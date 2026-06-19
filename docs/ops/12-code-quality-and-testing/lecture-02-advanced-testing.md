# Лекция 2. Продвинутое тестирование (Advanced Testing)

В [лекции 1](lecture-01-testing.md) разобрали unit-тесты в `unittest`, `pytest` и `go test`. На больших проектах одних unit-тестов мало:

- бизнес-логика зависит от **внешних систем** (БД, HTTP, очереди) — нужны интеграционные тесты;
- покрытие хорошо подобранными примерами обманчиво — нужно тестирование **свойств** (property-based);
- зависимости в коде нужно **подменять моками** — без них unit-тест становится интеграционным;
- качество кода в команде поддерживается **CI-метриками** — coverage gates, линтеры, type-checkers, security-сканеры.

Эта лекция — про вторую половину работы тестировщика-разработчика.

## Mock-объекты

**Mock (заглушка-обманка)** — объект, имитирующий поведение настоящей зависимости в тесте. Зачем:

- Изолировать тестируемый код от медленных/нестабильных зависимостей (БД, сеть).
- Проверять, что код *вызвал* нужный метод с нужными аргументами.
- Симулировать сценарии, которые трудно воспроизвести (отказ сети, истёкший токен).

### Терминология (по Мартину Фаулеру)

Часто всё называют «моками», но есть градации:

| Термин | Что делает |
|--------|-----------|
| **Dummy** | Объект-болванка, передаётся для аргумента, не используется. |
| **Stub** | Возвращает заранее заданные данные на вызовы. |
| **Spy** | Stub + записывает, как его вызывали. |
| **Mock** | Spy + ожидания: «должен быть вызван `save(...)` ровно один раз». |
| **Fake** | Упрощённая, но рабочая реализация (in-memory БД вместо настоящей). |

В быту это всё называют моками, но различия важны: библиотека `unittest.mock` даёт *моки и стабы*; `pytest-mock` — обёртку над ними; testcontainers — *фейки/реальные сервисы*.

### Python: `unittest.mock`

Встроен в стандартную библиотеку.

```python
# service.py
import httpx


def fetch_user(user_id: int) -> dict:
    response = httpx.get(f"https://api.example.com/users/{user_id}")
    response.raise_for_status()
    return response.json()


def send_welcome(user_id: int, mailer) -> None:
    user = fetch_user(user_id)
    mailer.send(user["email"], "Добро пожаловать!")
```

```python
# tests/test_service.py
from unittest.mock import Mock, patch

import service


@patch("service.httpx.get")
def test_fetch_user_calls_correct_url(mock_get):
    mock_get.return_value.json.return_value = {"id": 1, "email": "u@example.com"}
    mock_get.return_value.raise_for_status.return_value = None

    result = service.fetch_user(1)

    mock_get.assert_called_once_with("https://api.example.com/users/1")
    assert result == {"id": 1, "email": "u@example.com"}


def test_send_welcome_calls_mailer():
    mailer = Mock()
    with patch("service.fetch_user", return_value={"email": "u@example.com"}):
        service.send_welcome(42, mailer)

    mailer.send.assert_called_once_with("u@example.com", "Добро пожаловать!")
```

- `Mock()` создаёт объект с произвольным API — любой метод/атрибут «существует».
- `patch("module.symbol")` подменяет символ на время теста (контекстный менеджер или декоратор).
- `mock.assert_called_once_with(...)` — проверка ожидания.
- `mock.return_value` / `mock.side_effect` — что возвращать на вызовы.

**Важно:** `patch` подменяет символ **там, где он используется**, а не там, где определён. Если в `service.py` написано `from httpx import get`, патчить нужно `service.get`, а не `httpx.get`.

### Python: `pytest-mock`

```bash
uv add --dev pytest-mock
```

Тонкая обёртка над `unittest.mock` — добавляет фикстуру `mocker`:

```python
def test_send_welcome(mocker):
    mock_fetch = mocker.patch("service.fetch_user", return_value={"email": "u@x.com"})
    mailer = mocker.Mock()

    service.send_welcome(42, mailer)

    mock_fetch.assert_called_once_with(42)
    mailer.send.assert_called_once()
```

Главное преимущество — автоматическая отмена патча после теста, никаких `with patch(...)` пирамид.

### Go: интерфейсы как естественный мок

В Go моки не нужны для того, что в Python требует `patch`. Достаточно объявить интерфейс с нужным методом — и в тестах подсунуть свою реализацию:

```go
// service.go
type Mailer interface {
    Send(to, subject string) error
}

type UserFetcher interface {
    Fetch(id int) (User, error)
}

type Service struct {
    Mailer  Mailer
    Fetcher UserFetcher
}

func (s *Service) SendWelcome(userID int) error {
    user, err := s.Fetcher.Fetch(userID)
    if err != nil {
        return err
    }
    return s.Mailer.Send(user.Email, "Добро пожаловать!")
}
```

```go
// service_test.go
type fakeMailer struct {
    sentTo      string
    sentSubject string
}

func (f *fakeMailer) Send(to, subject string) error {
    f.sentTo = to
    f.sentSubject = subject
    return nil
}

type fakeFetcher struct{ user User }
func (f *fakeFetcher) Fetch(int) (User, error) { return f.user, nil }

func TestSendWelcome(t *testing.T) {
    mailer := &fakeMailer{}
    svc := &Service{
        Mailer:  mailer,
        Fetcher: &fakeFetcher{user: User{Email: "u@example.com"}},
    }

    if err := svc.SendWelcome(42); err != nil {
        t.Fatal(err)
    }

    if mailer.sentTo != "u@example.com" {
        t.Errorf("неожиданный получатель: %s", mailer.sentTo)
    }
}
```

Это — **fake** (по терминологии Фаулера): простая ручная реализация. Никаких метапрограммных трюков, интерфейс гарантирует совместимость на этапе компиляции.

### Go: `gomock` и `testify/mock`

Когда интерфейс большой и нужно много вариантов проверок — на помощь приходят кодогенераторы:

```bash
go install go.uber.org/mock/mockgen@latest
mockgen -source=service.go -destination=mocks/mailer.go -package=mocks
```

```go
// service_test.go
import "go.uber.org/mock/gomock"

func TestSendWelcome_gomock(t *testing.T) {
    ctrl := gomock.NewController(t)
    defer ctrl.Finish()

    mailer := mocks.NewMockMailer(ctrl)
    fetcher := mocks.NewMockUserFetcher(ctrl)

    fetcher.EXPECT().
        Fetch(42).
        Return(User{Email: "u@example.com"}, nil)

    mailer.EXPECT().
        Send("u@example.com", "Добро пожаловать!").
        Return(nil)

    svc := &Service{Mailer: mailer, Fetcher: fetcher}
    if err := svc.SendWelcome(42); err != nil {
        t.Fatal(err)
    }
}
```

`gomock` строго следит за порядком вызовов и аргументами. Альтернатива — [`testify/mock`](https://github.com/stretchr/testify) с runtime-проверками. Кодогенерация надёжнее.

> **Правило большого пальца.** Чем меньше моков — тем проще тест. Если в тесте 5 моков с десятью `EXPECT`, проблема не в тестах, а в архитектуре: слишком много зависимостей у одного компонента (нарушение SRP, [тема 6, лекция 3](../../foundations/06-oop-principles/lecture-03-solid.md)).

## Property-based testing

В примерах-тестах вы говорите: «при входе X должен быть выход Y». Property-based говорит другое: **«какое бы X ни было, для функции должно выполняться свойство P»** — а библиотека сама генерирует сотни случайных X и ищет контрпример.

Изобретено в Haskell-сообществе как [QuickCheck](https://hackage.haskell.org/package/QuickCheck) (Клаессен и Хьюз, 2000). Сейчас есть аналоги во всех языках.

### Когда полезно

- Алгоритмы с математическими инвариантами (сортировка, парсеры, сериализация).
- Поиск граничных случаев (пустые строки, отрицательные числа, Unicode).
- Регрессии: библиотека запоминает контрпример и пробует его при каждом запуске.

### Свойства, которые легко формулировать

1. **Round-trip:** `decode(encode(x)) == x`.
2. **Идемпотентность:** `f(f(x)) == f(x)` (например, `sorted(sorted(xs)) == sorted(xs)`).
3. **Коммутативность/ассоциативность:** `add(a, b) == add(b, a)`.
4. **Инвариант:** «после `sorted` длина массива не изменилась».
5. **Сравнение с эталоном:** оптимизированная реализация даёт тот же результат, что и наивная.

### Python: Hypothesis

```bash
uv add --dev hypothesis
```

```python
# test_sort.py
from hypothesis import given, strategies as st


def my_sort(xs: list[int]) -> list[int]:
    # тестируем самописную сортировку
    if len(xs) <= 1:
        return xs
    pivot = xs[0]
    less = [x for x in xs[1:] if x <= pivot]
    greater = [x for x in xs[1:] if x > pivot]
    return my_sort(less) + [pivot] + my_sort(greater)


@given(st.lists(st.integers()))
def test_sort_length_preserved(xs):
    assert len(my_sort(xs)) == len(xs)


@given(st.lists(st.integers()))
def test_sort_idempotent(xs):
    assert my_sort(my_sort(xs)) == my_sort(xs)


@given(st.lists(st.integers()))
def test_sort_matches_builtin(xs):
    assert my_sort(xs) == sorted(xs)
```

Hypothesis сгенерирует сотни списков (пустые, длинные, с повторами, с экстремальными числами) и проверит свойство. При падении — **сжимает** входные данные до минимального контрпримера:

```
Falsifying example: test_sort_matches_builtin(
    xs=[0, 0],  # минимальный контрпример
)
```

Расширенные генераторы:

```python
@given(
    st.text(min_size=1),
    st.dictionaries(st.text(), st.integers()),
    st.lists(st.integers(), min_size=1, max_size=100),
)
def test_complex(name, mapping, values):
    ...
```

`@settings(max_examples=1000, deadline=None)` — настройка количества попыток и таймаута. Сохранённые контрпримеры — в `.hypothesis/examples/`.

### Go: `testing/quick` и `rapid`

В стандартной библиотеке есть [`testing/quick`](https://pkg.go.dev/testing/quick), но он скудный — без shrinking, без сложных генераторов. На практике берут [`pgregory.net/rapid`](https://github.com/flyingmutant/rapid):

```bash
go get pgregory.net/rapid
```

```go
package mysort

import (
    "sort"
    "testing"

    "pgregory.net/rapid"
)

func MySort(xs []int) []int { /* ... */ }

func TestSortMatchesStdlib(t *testing.T) {
    rapid.Check(t, func(t *rapid.T) {
        xs := rapid.SliceOf(rapid.Int()).Draw(t, "xs")

        got := MySort(append([]int{}, xs...))
        want := append([]int{}, xs...)
        sort.Ints(want)

        if !equal(got, want) {
            t.Fatalf("mismatch:\n got=%v\nwant=%v", got, want)
        }
    })
}
```

`rapid.Check` сгенерирует сотни тестов, при падении — сожмёт вход до минимального примера и сохранит его в `testdata/rapid/`. Тот же контрпример будет проигран при следующем `go test`.

### Когда property-based не работает

- Свойство сложно сформулировать («интерфейс должен выглядеть красиво»).
- Запуск свойства долгий (тесты на БД с тысячью попыток — это часы).
- Невозможно отделить чистую логику от побочных эффектов.

Property-based **дополняет** unit-тесты, а не заменяет. Часто вместе с classическими примерами на конкретные граничные случаи.

## Интеграционные тесты

**Unit-тест** проверяет один компонент в изоляции — БД заменена моком, HTTP — стабом. **Интеграционный тест** проверяет связку компонентов вместе — с реальной БД, реальной очередью, реальным HTTP-клиентом. **E2E-тест** — всё приложение целиком, обычно с UI.

Граница условна, но цель ясна: убедиться, что компоненты *соединяются правильно* — то, чего unit-тесты по определению проверить не могут.

### Проблема: настоящая БД в тестах

Варианты:

| Подход | Плюсы | Минусы |
|--------|-------|--------|
| **In-memory БД** (SQLite в `:memory:`) | Быстро, без зависимостей. | Не та БД, что в проде — миграции могут не пройти. |
| **Отдельный инстанс на CI** | Производственный движок. | Setup, шаринг между тестами, конкуренция. |
| **Testcontainers** | Изоляция, актуальная версия. | Нужен Docker, медленнее старта. |
| **Shared dev БД** | Просто. | Хрупко, тесты ломают друг друга, нельзя параллелить. |

### Testcontainers

Идея: тест на старте запускает реальный сервис в Docker-контейнере, проверяет, останавливает. Производственный движок + изоляция.

#### Python

```bash
uv add --dev testcontainers[postgres]
```

```python
# tests/test_repo.py
import pytest
from sqlalchemy import create_engine, text
from testcontainers.postgres import PostgresContainer


@pytest.fixture(scope="session")
def postgres():
    with PostgresContainer("postgres:16") as pg:
        yield pg


@pytest.fixture
def engine(postgres):
    eng = create_engine(postgres.get_connection_url())
    with eng.begin() as conn:
        conn.execute(text("CREATE TABLE IF NOT EXISTS users (id INT, name TEXT)"))
    yield eng
    with eng.begin() as conn:
        conn.execute(text("DROP TABLE users"))


def test_insert_user(engine):
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO users VALUES (1, 'Alice')"))
        row = conn.execute(text("SELECT name FROM users WHERE id = 1")).first()
    assert row.name == "Alice"
```

`scope="session"` — контейнер один на всю сессию pytest. Между тестами очищаем данные (truncate, drop/recreate) или используем транзакции с откатом.

#### Go

```bash
go get github.com/testcontainers/testcontainers-go
go get github.com/testcontainers/testcontainers-go/modules/postgres
```

```go
package repo_test

import (
    "context"
    "database/sql"
    "testing"

    _ "github.com/lib/pq"
    "github.com/testcontainers/testcontainers-go"
    "github.com/testcontainers/testcontainers-go/modules/postgres"
    "github.com/testcontainers/testcontainers-go/wait"
)

func setupDB(t *testing.T) *sql.DB {
    t.Helper()
    ctx := context.Background()

    pg, err := postgres.Run(ctx, "postgres:16",
        postgres.WithDatabase("test"),
        postgres.WithUsername("test"),
        postgres.WithPassword("test"),
        testcontainers.WithWaitStrategy(
            wait.ForLog("database system is ready to accept connections").
                WithOccurrence(2),
        ),
    )
    if err != nil {
        t.Fatal(err)
    }
    t.Cleanup(func() { _ = pg.Terminate(ctx) })

    dsn, err := pg.ConnectionString(ctx, "sslmode=disable")
    if err != nil {
        t.Fatal(err)
    }
    db, err := sql.Open("postgres", dsn)
    if err != nil {
        t.Fatal(err)
    }
    return db
}

func TestInsertUser(t *testing.T) {
    db := setupDB(t)
    if _, err := db.Exec("CREATE TABLE users (id INT, name TEXT)"); err != nil {
        t.Fatal(err)
    }
    if _, err := db.Exec("INSERT INTO users VALUES (1, 'Alice')"); err != nil {
        t.Fatal(err)
    }

    var name string
    err := db.QueryRow("SELECT name FROM users WHERE id = 1").Scan(&name)
    if err != nil || name != "Alice" {
        t.Fatalf("got %q err %v", name, err)
    }
}
```

`t.Cleanup` гарантирует остановку контейнера, даже если тест упал. Запуск Postgres ~3-5 секунд — окупается за счёт реалистичности.

### Httptest и тесты HTTP-клиентов

Для серверных тестов в Go стандарт — `net/http/httptest`:

```go
func TestClient_FetchUser(t *testing.T) {
    server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        if r.URL.Path != "/users/42" {
            t.Errorf("wrong path: %s", r.URL.Path)
        }
        w.Header().Set("Content-Type", "application/json")
        w.Write([]byte(`{"id":42,"name":"Alice"}`))
    }))
    defer server.Close()

    client := NewClient(server.URL)
    user, err := client.FetchUser(42)
    if err != nil {
        t.Fatal(err)
    }
    if user.Name != "Alice" {
        t.Errorf("got %s", user.Name)
    }
}
```

В Python аналог — [`respx`](https://github.com/lundberg/respx) для `httpx` или [`responses`](https://github.com/getsentry/responses) для `requests`:

```python
import respx
import httpx


@respx.mock
def test_fetch_user():
    respx.get("https://api.example.com/users/42").mock(
        return_value=httpx.Response(200, json={"id": 42, "name": "Alice"})
    )

    user = service.fetch_user(42)
    assert user["name"] == "Alice"
```

### Изоляция тестов и параллелизм

Интеграционные тесты — самая дорогая категория. Чтобы они не превратились в часовой CI:

- **Параллелить там, где можно.** В Go — `t.Parallel()`. В pytest — `pytest-xdist`. Но **общий контейнер нельзя параллелить** — каждому тесту своя схема/база, или sequential.
- **Транзакции с откатом** вместо `truncate` — быстрее, изолированнее.
- **Разделять unit и integration** на отдельные таргеты CI. Unit — на каждый push; integration — на main и PR.
- **Помечать долгие тесты.** В pytest — `@pytest.mark.slow`; в Go — `if testing.Short() { t.Skip() }` и запускать `go test -short` локально.

## Качество кода в CI

Тесты — половина работы. Вторая половина — **статический анализ**, **типы**, **безопасность**, **gates** на покрытие.

### Линтеры и форматтеры

| Инструмент | Язык | Что делает |
|------------|------|-----------|
| **ruff** | Python | Линт + автоформат + сортировка импортов, быстрый (Rust). |
| **black** | Python | Форматтер. Постепенно вытесняется `ruff format`. |
| **mypy** / **pyright** | Python | Static type checking. |
| **golangci-lint** | Go | Метаагрегатор десятков линтеров (`gofmt`, `govet`, `staticcheck`, `errcheck`, ...). |
| **gofmt** / **goimports** | Go | Форматтер + сортировка импортов. |

Минимальный `pyproject.toml`:

```toml
[tool.ruff]
line-length = 100
target-version = "py314"

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "SIM", "RUF"]

[tool.mypy]
python_version = "3.14"
strict = true
```

Минимальный `.golangci.yml`:

```yaml
version: "2"
linters:
  default: standard
  enable:
    - errcheck
    - govet
    - staticcheck
    - revive
    - gosec
    - misspell
    - unparam
```

### Security-сканеры

| Инструмент | Язык | Назначение |
|------------|------|-----------|
| **bandit** | Python | Поиск known-bad паттернов (`eval`, hardcoded credentials, weak crypto). |
| **pip-audit** / **safety** | Python | Проверка зависимостей на CVE. |
| **gosec** | Go | Аналог bandit для Go (входит в `golangci-lint`). |
| **govulncheck** | Go | Официальный от команды Go: ищет CVE в зависимостях и реально вызываемом коде. |
| **trivy** | Любой | Сканер контейнерных образов и manifest-файлов. |

### Coverage gates

Покрытие кода — метрика, которой легко манипулировать. 100% coverage не гарантирует отсутствие багов, а низкое coverage гарантирует их присутствие. Разумное правило — **не давать упасть**:

```yaml
# .github/workflows/ci.yml
- name: Run tests with coverage
  run: pytest --cov=app --cov-report=xml --cov-fail-under=80

- name: Go coverage gate
  run: |
    go test -coverprofile=cov.out ./...
    pct=$(go tool cover -func=cov.out | tail -1 | awk '{print $3}' | tr -d '%')
    if (( $(echo "$pct < 70" | bc -l) )); then
      echo "coverage $pct% < 70%"; exit 1
    fi
```

Лучше: **diff coverage** — измерять покрытие только изменённого кода. Инструменты: `diff-cover` (Python), [`coverage`](https://github.com/codecov/codecov-action) от Codecov.

### Сборный CI-пайплайн

Пример `.github/workflows/ci.yml`:

```yaml
name: ci
on:
  pull_request:
  push:
    branches: [main]

jobs:
  python:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
      - run: uv sync --dev
      - run: uv run ruff check .
      - run: uv run ruff format --check .
      - run: uv run mypy .
      - run: uv run bandit -r src/
      - run: uv run pip-audit
      - run: uv run pytest --cov=src --cov-fail-under=80

  go:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: "1.23"
      - uses: golangci/golangci-lint-action@v6
      - run: go test -race -coverprofile=cov.out ./...
      - run: go run golang.org/x/vuln/cmd/govulncheck@latest ./...
```

Каждая стадия проверяет одно. Падение любой — блокирует merge. Это и есть «качество кода в команде» — машинно, не на словах.

### Pre-commit hooks

Чтобы линтеры запускались до коммита, а не падали в CI:

```bash
uv add --dev pre-commit
```

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.7.0
    hooks:
      - id: ruff
      - id: ruff-format

  - repo: https://github.com/golangci/golangci-lint
    rev: v2.0.0
    hooks:
      - id: golangci-lint
```

После `pre-commit install` хуки запускаются автоматически на `git commit`. Грязные коммиты в принципе не возникают.

## Что использовать когда

| Сценарий | Инструмент |
|----------|-----------|
| Проверка одной функции в изоляции | unit-тест с моком |
| Поиск граничных случаев в чистой логике | property-based |
| Тест с реальной БД | testcontainers |
| HTTP-клиент против моков сервера | httptest / respx |
| Запретить мёртвый код | линтер с unused-правилом |
| Запретить регрессию покрытия | coverage gate в CI |
| Запретить CVE | govulncheck / pip-audit |
| Запретить «грязные» коммиты | pre-commit + format на хуках |

Цель не «100% покрытие» и не «20 линтеров». Цель — **уверенность**, что изменение, прошедшее CI, не сломает прод. Каждая метрика должна работать на это, иначе её можно убрать.

## Что почитать дальше

- Martin Fowler. [*Mocks Aren't Stubs*](https://martinfowler.com/articles/mocksArentStubs.html) — классификация test doubles.
- *Hypothesis Documentation* — стратегии и shrinking.
- [Testcontainers docs](https://testcontainers.com/) — модули для Postgres, Kafka, Redis, MinIO.
- [Go Testing By Example](https://research.swtch.com/testing) — Russ Cox.

## Контрольные вопросы

- В чём отличие mock от stub? Когда стоит использовать fake?
- Почему в Go реже нужны моки, чем в Python?
- Что такое property-based testing? Какие свойства легко проверять?
- Что делает shrinking при падении property-based теста?
- В чём разница между unit-, интеграционным и E2E-тестом?
- Почему in-memory SQLite не всегда хороший выбор для интеграционных тестов?
- Зачем нужны testcontainers, если можно поставить Postgres локально?
- Что такое coverage gate и в чём ограничение «покрытия» как метрики?
- Какие инструменты используются для проверки безопасности зависимостей в Python и Go?
- В чём ценность pre-commit hooks по сравнению с CI?
