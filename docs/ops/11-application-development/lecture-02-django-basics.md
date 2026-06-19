# Лекция 2. Django — основы фреймворка

## Зачем нам ещё один фреймворк

В теме 10 мы видели `http.server` — стандартный модуль для базового HTTP, и трогали `requests` для клиента. На этом фундаменте можно построить веб-приложение, но придётся писать руками: маршрутизацию, шаблоны, формы, сессии, ORM, миграции, аутентификацию. Веб-фреймворки делают эту работу за вас.

В Python два «больших» фреймворка:

- **Django** (2005 г., Adrian Holovaty, Simon Willison) — «батарейки включены». ORM, админка, шаблоны, формы, миграции, авторизация — всё из коробки. Хорош для CRUD-приложений, контентных сайтов, админ-панелей.
- **Flask** (2010 г., Armin Ronacher) — минималистичный микрофреймворк. Маршрутизация + шаблоны, остальное собираете из библиотек. Хорош, когда нужно лёгкое решение или нестандартная архитектура.
- **FastAPI** (2018 г., Sebastián Ramírez) — современная альтернатива для API: async, type hints как контракт, автогенерация OpenAPI.

В курсе разбираем Django: он покрывает максимум тем за минимум кода и до сих пор остаётся одним из самых востребованных навыков на рынке Python.

Текущая стабильная версия — **Django 5.x** (LTS — 4.2 и 5.2). В примерах используем синтаксис 5.x; различия с 4.x минимальны, но `path()` с конвертерами и async views — это уже стандарт.

## Установка и старт проекта

```bash
mkdir myblog && cd myblog
uv init --bare
uv add 'django>=5,<6'
```

`uv add` записывает зависимость в `pyproject.toml` и фиксирует версию в `uv.lock`. Никакие виртуальные окружения вручную создавать не нужно — `uv` всё делает сам.

Создание проекта:

```bash
uv run django-admin startproject blog .
```

Точка в конце важна — она просит положить структуру в текущую директорию, а не создавать ещё одну. Получаем:

```text
myblog/
├── manage.py             # CLI-обёртка над django-admin для текущего проекта
├── blog/
│   ├── __init__.py
│   ├── settings.py       # конфигурация
│   ├── urls.py           # глобальный роутер
│   ├── wsgi.py           # production-точка входа (WSGI)
│   ├── asgi.py           # production-точка входа (ASGI, для async)
└── pyproject.toml
```

Запуск:

```bash
uv run python manage.py migrate    # применить миграции встроенных приложений
uv run python manage.py runserver
```

По умолчанию — `http://127.0.0.1:8000`. Откройте в браузере — увидите стандартную welcome-страницу.

## Проекты и приложения

В Django есть два уровня:

- **Project** — корневой контейнер (наш `myblog/blog/`). Один на репозиторий. Содержит общую конфигурацию.
- **App** — отдельное переиспользуемое приложение (новости, блог, авторизация, аналитика). Проект подключает несколько app'ов.

```bash
uv run python manage.py startapp posts
```

Структура нового приложения:

```text
posts/
├── __init__.py
├── admin.py        # регистрация моделей в админке
├── apps.py         # конфигурация приложения
├── migrations/
│   └── __init__.py
├── models.py       # модели данных
├── tests.py        # тесты
└── views.py        # обработчики запросов
```

Чтобы Django увидел приложение, добавьте его в `INSTALLED_APPS` в `blog/settings.py`:

```python
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "posts",   # ← наше приложение
]
```

## MVT — паттерн Django

Классический MVC адаптирован у Django как **MVT — Model–View–Template**:

- **Model** — описание данных (что хранится в БД).
- **View** — функция (или класс), которая обрабатывает HTTP-запрос и возвращает ответ.
- **Template** — HTML-шаблон, который рендерится во view с подставленными данными.

Маршруты (URL configuration) Django называют отдельно — это не часть MVT, но критически важная третья деталь.

## Модели

```python
# posts/models.py
from django.db import models
from django.contrib.auth.models import User


class Post(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    body = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posts")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["-created_at"])]

    def __str__(self) -> str:
        return self.title
```

Что произошло:

1. `Post` — Python-класс, унаследованный от `models.Model`. Django по нему построит таблицу `posts_post` в БД.
2. Поля — атрибуты класса. `CharField`, `TextField`, `BooleanField`, `DateTimeField` — типы Django. Они же отвечают за валидацию форм.
3. `ForeignKey` — связь «многие-к-одному». `on_delete=CASCADE` — удалить пост при удалении автора. Альтернативы: `SET_NULL`, `PROTECT`, `RESTRICT`.
4. `auto_now_add=True` — записать момент создания и больше никогда не менять. `auto_now=True` — обновлять при каждом `save()`.
5. `Meta` — мета-настройки: порядок по умолчанию, индексы, имя таблицы.
6. `__str__` — нужен, чтобы записи красиво отображались в админке и логах.

## Миграции

Django сравнивает текущий код моделей с историей миграций и автогенерирует diff:

```bash
uv run python manage.py makemigrations posts
# Migrations for 'posts':
#   posts/migrations/0001_initial.py
#     - Create model Post

uv run python manage.py migrate
# Operations to perform:
#   Apply all migrations: admin, auth, contenttypes, posts, sessions
# Running migrations:
#   Applying posts.0001_initial... OK
```

Миграции — обычные Python-файлы в `posts/migrations/`. Их **коммитят в git**: это история эволюции схемы БД. Никогда не редактируйте применённую миграцию руками — создавайте новую.

Если миграция уехала с ошибкой в schema, есть `python manage.py migrate posts 0001` для отката до конкретной версии и `python manage.py squashmigrations posts 0001 0010` для слияния старых миграций.

## ORM — основные запросы

ORM (Object-Relational Mapper) скрывает SQL. Каждая модель получает менеджер `objects`:

```python
# Создание
post = Post.objects.create(title="Hello", slug="hello", body="...", author=user)

# Чтение одной записи
post = Post.objects.get(slug="hello")            # один — иначе DoesNotExist
post = Post.objects.filter(slug="hello").first() # один или None

# Чтение списка
posts = Post.objects.filter(published=True)              # WHERE published = True
posts = Post.objects.filter(title__icontains="django")    # WHERE title ILIKE '%django%'
posts = Post.objects.exclude(author__username="spam")     # NOT IN
posts = Post.objects.order_by("-created_at")[:10]         # LIMIT 10

# Связи — обращение через ORM, не вручную через id
post.author.email                  # JOIN posts → auth_user
user.posts.filter(published=True)  # related_name="posts" на ForeignKey

# Обновление
post.title = "New title"
post.save()
Post.objects.filter(author=user).update(published=True)   # bulk

# Удаление
post.delete()
Post.objects.filter(published=False).delete()             # bulk
```

QuerySet ленив — БД не дёргается, пока вы не итерируете, не возьмёте срез, не вызовете `.first()`/`.exists()`/`.count()`. Это позволяет цепочно фильтровать без лишних запросов.

### N+1 — главный анти-паттерн ORM

```python
# ПЛОХО — отдельный запрос на каждого автора
for post in Post.objects.all():
    print(post.author.email)

# ХОРОШО — один JOIN
for post in Post.objects.select_related("author"):
    print(post.author.email)
```

`select_related` — для `ForeignKey`/`OneToOne` (JOIN). `prefetch_related` — для `ManyToMany`/обратных связей (отдельный второй запрос + сборка в Python). Без них на сотне постов получите 101 запрос. На тысяче — 1001.

## Маршруты (URLconf)

`blog/urls.py` — корневой роутер. Подключает роутеры приложений:

```python
# blog/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("posts/", include("posts.urls")),
]
```

```python
# posts/urls.py
from django.urls import path
from . import views

app_name = "posts"  # пространство имён для reverse()

urlpatterns = [
    path("", views.post_list, name="list"),
    path("<slug:slug>/", views.post_detail, name="detail"),
    path("create/", views.post_create, name="create"),
]
```

Конвертеры в `<...>` — `str`, `int`, `slug`, `uuid`, `path` — Django сам парсит сегмент пути и подаёт в view нужный тип.

## Views (функции)

```python
# posts/views.py
from django.shortcuts import render, get_object_or_404, redirect
from .models import Post
from .forms import PostForm


def post_list(request):
    posts = Post.objects.filter(published=True).select_related("author")
    return render(request, "posts/list.html", {"posts": posts})


def post_detail(request, slug: str):
    post = get_object_or_404(Post, slug=slug, published=True)
    return render(request, "posts/detail.html", {"post": post})


def post_create(request):
    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect("posts:detail", slug=post.slug)
    else:
        form = PostForm()
    return render(request, "posts/form.html", {"form": form})
```

- `request` — объект запроса (HTTP-метод, GET/POST/cookies/файлы/пользователь).
- `get_object_or_404` — найти или вернуть 404. Удобнее, чем ловить `DoesNotExist`.
- `render(request, template, context)` — рендерит шаблон со значениями.
- `redirect("posts:detail", slug=...)` — HTTP-редирект; `posts:detail` разворачивается в URL.

### Class-based views (CBV)

Альтернатива функциям — классы с готовыми сценариями:

```python
from django.views.generic import ListView, DetailView


class PostListView(ListView):
    model = Post
    template_name = "posts/list.html"
    context_object_name = "posts"
    paginate_by = 20

    def get_queryset(self):
        return super().get_queryset().filter(published=True).select_related("author")
```

CBV полезны для CRUD: `CreateView`, `UpdateView`, `DeleteView`, `DetailView`, `ListView`. Они задают «скелет», вы переопределяете методы. Минус — труднее читать поток (магия наследования), плюс — мало кода.

В реальных проектах часто пишут смесь: простые экраны на функциях, типовые CRUD на CBV.

## Шаблоны

Шаблоны живут в `posts/templates/posts/` (двойной `posts/` — чтобы избежать конфликта имён с шаблонами других приложений):

```html
{# posts/templates/posts/base.html — общий каркас #}
<!doctype html>
<html lang="ru">
<head>
    <meta charset="utf-8">
    <title>{% block title %}Блог{% endblock %}</title>
</head>
<body>
    <header>
        <a href="{% url 'posts:list' %}">Посты</a>
        {% if user.is_authenticated %}
            <span>Привет, {{ user.username }}</span>
        {% else %}
            <a href="{% url 'admin:login' %}">Войти</a>
        {% endif %}
    </header>
    <main>{% block content %}{% endblock %}</main>
</body>
</html>
```

```html
{# posts/templates/posts/list.html #}
{% extends "posts/base.html" %}
{% block title %}Все посты{% endblock %}
{% block content %}
    <h1>Все посты</h1>
    <ul>
        {% for post in posts %}
            <li>
                <a href="{% url 'posts:detail' slug=post.slug %}">{{ post.title }}</a>
                <small>от {{ post.author.username }} · {{ post.created_at|date:"d.m.Y" }}</small>
            </li>
        {% empty %}
            <li>Пока ничего не опубликовано.</li>
        {% endfor %}
    </ul>
{% endblock %}
```

Базовые конструкции:

- `{{ var }}` — вывод переменной (с автоэкранированием HTML — защита от XSS).
- `{% if %}`/`{% for %}`/`{% url %}`/`{% block %}`/`{% extends %}`/`{% include %}` — теги.
- `{{ var|filter:arg }}` — фильтр (`date`, `length`, `truncatechars`, `default`, `safe`, `linebreaks`).

Шаблоны Django — намеренно слабый язык. Если хочется бизнес-логики в шаблоне — это сигнал, что её надо перенести во view.

Альтернатива — **Jinja2** (синтаксис похож на Django, но мощнее: можно вызывать любой Python). Подключается через `django.template.backends.jinja2.Jinja2` — в типовом учебном проекте берите встроенный Django Templates.

## Админка — даром

Зарегистрируйте модель в `posts/admin.py`:

```python
from django.contrib import admin
from .models import Post


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "created_at", "published")
    list_filter = ("published", "author")
    search_fields = ("title", "body")
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "created_at"
```

Создайте суперпользователя:

```bash
uv run python manage.py createsuperuser
```

Откройте `http://127.0.0.1:8000/admin/` — у вас полноценная CRUD-админка с фильтрами, поиском и пагинацией. Для прототипов, внутренних инструментов и MVP это часто всё, что нужно.

## Конфигурация и переменные окружения

`settings.py` не должен содержать секретов. Распространённый паттерн — читать через `os.environ` или библиотеку `django-environ`:

```python
# settings.py
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
DEBUG = os.environ.get("DJANGO_DEBUG", "0") == "1"
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost").split(",")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}
```

В продакшене — PostgreSQL вместо SQLite, `DEBUG=False`, `SECRET_KEY` из секретного хранилища, статика отдаётся через `nginx`/`whitenoise`.

## Команда `shell` для интерактивной отладки

```bash
uv run python manage.py shell
>>> from posts.models import Post
>>> Post.objects.count()
3
>>> Post.objects.filter(published=True).values_list("title", flat=True)
<QuerySet ['Hello', 'Django basics']>
```

Внутри — обычный Python REPL с предустановленным окружением Django. Удобно проверять запросы, не дёргая HTTP.

`uv run python manage.py shell -i ipython` — для IPython c подсветкой и историей (нужно `uv add --dev ipython`).

## Параллель с Go

Django — толстый «батарейки-включены» подход. В Go-сообществе принято собирать стек из мелких пакетов: `net/http` + ORM (`ent`, `gorm`) + миграции (`goose`/`migrate`) + шаблоны (`html/template`) + CLI (`cobra`). Цена — больше кода и решений; плюс — выше прозрачность и контроль.

| Django                                  | Go                                            |
|-----------------------------------------|------------------------------------------------|
| `path()` + `views.py`                   | `mux.HandleFunc("GET /...", handler)` (Go 1.22+) |
| ORM (`Post.objects.filter`)             | `database/sql` + ручной SQL или `gorm`/`ent`   |
| `makemigrations` + `migrate`            | `goose`/`migrate`/`atlas`                      |
| Django Templates                        | `html/template`                                |
| Django Admin                            | нет аналога «из коробки»                       |
| `django.contrib.auth`                   | `golang.org/x/crypto/bcrypt` + сессии руками   |
| `manage.py shell`                       | нет REPL — пишите CLI-команды через `cobra`    |

## Что почитать

- [Официальная документация Django](https://docs.djangoproject.com/) — лучшая в индустрии. Начните с туториала «Polls app» (7 частей).
- [Two Scoops of Django](https://www.feldroy.com/books/two-scoops-of-django-3-x) — каноническая книга по best practices.
- [Django for Beginners](https://djangoforbeginners.com/) Will Vincent — для новичков.

## Итог

Django — фреймворк с «батарейками». MVT-паттерн: модели → миграции → ORM, маршруты → views → шаблоны, готовая админка через `admin.py`. `manage.py` — основной CLI-инструмент. Зависимости через `uv add 'django>=5,<6'`. В следующей лекции — формы, сигналы и REST API через DRF.
