# Лекция 3. Django — формы, сигналы и REST API

В прошлой лекции собрали базовый блог: модели, миграции, views, шаблоны и админка. Теперь — что делать, когда есть пользовательский ввод, нужно реагировать на изменения в БД и отдавать данные не в HTML, а в JSON для фронтенда или мобильного клиента.

## Формы

В Django формы — это полноценная абстракция, которая делает три вещи:

1. **Рендерит** поля как HTML;
2. **Валидирует** входные данные;
3. **Очищает** их в типизированный `cleaned_data`.

### ModelForm — авто-форма по модели

```python
# posts/forms.py
from django import forms
from .models import Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["title", "slug", "body", "published"]
        widgets = {
            "body": forms.Textarea(attrs={"rows": 10}),
        }

    def clean_slug(self):
        slug = self.cleaned_data["slug"]
        if slug.startswith("admin"):
            raise forms.ValidationError("Slug не может начинаться с 'admin'.")
        return slug
```

Использование во view (видели в прошлой лекции):

```python
def post_create(request):
    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)   # не сохранять, добавим author
            post.author = request.user
            post.save()
            return redirect("posts:detail", slug=post.slug)
    else:
        form = PostForm()
    return render(request, "posts/form.html", {"form": form})
```

### Шаблон с формой

```html
{# posts/templates/posts/form.html #}
{% extends "posts/base.html" %}
{% block content %}
    <h1>Новый пост</h1>
    <form method="post">
        {% csrf_token %}
        {{ form.as_p }}
        <button type="submit">Опубликовать</button>
    </form>
{% endblock %}
```

`{% csrf_token %}` — обязательный токен против CSRF-атак. Без него Django вернёт 403. Аналог проверки в любом современном фреймворке. AJAX-запросы должны слать токен в заголовке `X-CSRFToken`.

`{{ form.as_p }}` рендерит все поля внутри `<p>...</p>`. Альтернативы: `as_table`, `as_ul`, ручной рендер по полям:

```html
<div class="field">
    {{ form.title.label_tag }}
    {{ form.title }}
    {% if form.title.errors %}<div class="error">{{ form.title.errors }}</div>{% endif %}
</div>
```

### Не-моделевая форма

Когда форма не привязана к модели (поиск, контакты, фильтры):

```python
class ContactForm(forms.Form):
    email = forms.EmailField()
    subject = forms.CharField(max_length=200)
    message = forms.CharField(widget=forms.Textarea)
    agree = forms.BooleanField(label="Согласен с обработкой данных")
```

`is_valid()`, `cleaned_data`, `clean_<field>` работают точно так же.

## Сигналы

Сигналы — это паттерн Observer внутри Django. Когда происходит событие (сохранение модели, удаление, миграция), Django **рассылает** сигнал, и все подписчики реагируют.

### Готовые сигналы моделей

```python
# posts/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils.text import slugify

from .models import Post


@receiver(post_save, sender=Post)
def fill_slug(sender, instance: Post, created: bool, **kwargs):
    if created and not instance.slug:
        instance.slug = slugify(instance.title)
        instance.save(update_fields=["slug"])


@receiver(post_delete, sender=Post)
def log_deletion(sender, instance: Post, **kwargs):
    print(f"Пост '{instance.title}' удалён")
```

Подключение в `apps.py`:

```python
class PostsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "posts"

    def ready(self):
        from . import signals   # noqa: F401  — регистрирует обработчики
```

### Когда сигналы — это плохо

Сигналы создают «магию на расстоянии»: код в `models.py` не показывает, что после `save()` что-то ещё произойдёт. На больших проектах это превращается в кошмар отладки.

Альтернативы:

- **Метод модели** (`def save(self, *args, **kwargs): ... super().save(...)`) — явно и видно.
- **Сервисная функция** (`services.create_post(...)`) — собирает все шаги: сохранить, отправить email, обновить кеш. Тоже явно.

Сигналы оправданы, когда:

- Подписчик в другом приложении, и вы не хотите импортную зависимость;
- Нужна реакция на стандартные события Django, которые вы не контролируете (`user_logged_in`, `request_started`).

Для всего остального — явные сервисы лучше.

## Аутентификация и сессии

Из коробки Django даёт:

- Модель `User` (`username`, `email`, `password` (хешированный), `is_staff`, `is_superuser`);
- Views для login/logout/password reset (`django.contrib.auth.urls`);
- Middleware, который кладёт `request.user` в каждый запрос;
- Декораторы `@login_required`, `@permission_required`, `@user_passes_test`.

```python
# blog/urls.py
urlpatterns = [
    path("accounts/", include("django.contrib.auth.urls")),
    # ...
]
```

Эти строки регистрируют `/accounts/login/`, `/accounts/logout/`, `/accounts/password_reset/` и т. д. Шаблоны положите в `templates/registration/login.html` — Django найдёт их сам.

```python
# views.py
from django.contrib.auth.decorators import login_required

@login_required
def post_create(request):
    ...
```

Анонимный пользователь будет перенаправлен на `LOGIN_URL` (по умолчанию `/accounts/login/`).

### Кастомная User-модель

**Сразу** при старте проекта подменяйте `User` на свою модель — иначе потом будет очень больно мигрировать:

```python
# accounts/models.py
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    email = models.EmailField(unique=True)
    bio = models.TextField(blank=True)
```

```python
# settings.py
AUTH_USER_MODEL = "accounts.User"
```

Получить модель в коде:

```python
from django.contrib.auth import get_user_model
User = get_user_model()
```

Никогда не импортируйте `from django.contrib.auth.models import User` напрямую — это сломается при кастомной модели.

## REST API через Django REST framework

Для отдачи данных в JSON Django сам ничего особого не умеет. Стандарт индустрии — пакет **Django REST framework (DRF)**.

```bash
uv add djangorestframework
```

```python
# settings.py
INSTALLED_APPS = [
    # ...
    "rest_framework",
]
```

### Сериализатор

Сериализатор — это «форма для API»: описывает, как модель превращается в JSON и обратно.

```python
# posts/serializers.py
from rest_framework import serializers
from .models import Post


class PostSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Post
        fields = ["id", "title", "slug", "body", "author", "created_at", "published"]
        read_only_fields = ["id", "author", "created_at"]
```

### ViewSet и роутер

```python
# posts/api.py
from rest_framework import viewsets, permissions
from .models import Post
from .serializers import PostSerializer


class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.select_related("author").filter(published=True)
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_field = "slug"

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
```

```python
# posts/urls.py
from rest_framework.routers import DefaultRouter
from . import api

router = DefaultRouter()
router.register("posts", api.PostViewSet, basename="post")

urlpatterns = [
    # ...
    path("api/", include(router.urls)),
]
```

Готово — у вас есть полноценный REST API:

| Метод | URL                    | Что делает              |
|-------|------------------------|--------------------------|
| GET   | `/api/posts/`          | список (с пагинацией)    |
| POST  | `/api/posts/`          | создать                  |
| GET   | `/api/posts/{slug}/`   | один пост                |
| PUT   | `/api/posts/{slug}/`   | полное обновление        |
| PATCH | `/api/posts/{slug}/`   | частичное обновление     |
| DELETE| `/api/posts/{slug}/`   | удалить                  |

DRF сам делает: пагинацию, фильтрацию, валидацию, разрешения, отрисовку браузерной DRF-консоли (на dev — очень удобно).

### Permissions

Готовые классы: `AllowAny`, `IsAuthenticated`, `IsAdminUser`, `IsAuthenticatedOrReadOnly`. Кастомные — наследуете от `BasePermission`:

```python
class IsAuthorOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author_id == request.user.id
```

### Аутентификация

По умолчанию DRF принимает сессионную и базовую auth. Для SPA/мобильного клиента — JWT через [`djangorestframework-simplejwt`](https://django-rest-framework-simplejwt.readthedocs.io/):

```bash
uv add djangorestframework-simplejwt
```

```python
# settings.py
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
}
```

```python
# urls.py
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path("api/token/", TokenObtainPairView.as_view()),
    path("api/token/refresh/", TokenRefreshView.as_view()),
]
```

После этого клиент логинится `POST /api/token/` с username/password, получает `{access, refresh}`, шлёт `Authorization: Bearer <access>` в дальнейших запросах.

## Тесты

Django поставляет свой `TestCase`, основанный на стандартном `unittest`:

```python
# posts/tests.py
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Post

User = get_user_model()


class PostListTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("alice", password="x")
        cls.post = Post.objects.create(
            title="Hello", slug="hello", body="Body", author=cls.user, published=True
        )

    def test_list_view_renders_published_posts(self):
        response = self.client.get(reverse("posts:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Hello")

    def test_unpublished_post_404(self):
        self.post.published = False
        self.post.save()
        response = self.client.get(reverse("posts:detail", kwargs={"slug": "hello"}))
        self.assertEqual(response.status_code, 404)
```

`TestCase` оборачивает каждый тест в транзакцию и откатывает её — БД в начале каждого теста чистая. `setUpTestData` (vs `setUp`) выполняется один раз на весь класс — быстрее.

Запуск — через стандартный `manage.py`:

```bash
uv run python manage.py test posts
```

Или через `pytest` + плагин `pytest-django` — удобнее, особенно если уже используете pytest в других проектах (см. [тему 12](../12-code-quality-and-testing/lecture-01-testing.md)).

## Что почитать дальше

- [Django REST framework docs](https://www.django-rest-framework.org/) — глубокий tutorial.
- [Django Packages](https://djangopackages.org/) — каталог стороннего: `django-allauth` (соц-логины), `django-extensions` (доп. команды), `django-debug-toolbar` (профилировка запросов).
- [django-stubs](https://github.com/typeddjango/django-stubs) — type hints для Django (даёт нормальный автокомплит и `mypy`).

## Параллель с Go

Если будете писать API на Go — нет монолита уровня Django, собираете стек:

| Django                                  | Go                                            |
|-----------------------------------------|------------------------------------------------|
| `forms.ModelForm` + `is_valid()`         | `go-playground/validator` + ручной mapping      |
| Сигналы (`post_save`)                    | Event bus вручную или библиотека вроде `watermill` |
| `django.contrib.auth`                    | `golang-jwt/jwt` + сессии в Redis              |
| DRF `ModelViewSet`                       | `chi` / `gin` + ручные handlers + `sqlc` или `gorm` |
| `manage.py test`                         | `go test ./...`                                 |

## Итог

Формы для пользовательского ввода (`ModelForm` для CRUD, базовый `Form` для всего остального). Сигналы — мощный, но опасный инструмент: предпочитайте явные сервисы. Аутентификация `django.contrib.auth` готова из коробки; для SPA — JWT через `simplejwt`. REST API — на DRF: сериализаторы + `ModelViewSet` + роутер. Тесты — встроенный `TestCase` или `pytest-django`. В последней лекции — как из этого всего собрать standalone-бинарник.
