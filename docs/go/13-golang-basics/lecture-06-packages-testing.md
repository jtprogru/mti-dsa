# Лекция 6. Пакеты, модули и тестирование

## Пакеты — единица организации кода

Каждый Go-файл начинается с объявления пакета:

```go
package mathx
```

Все файлы в одной директории должны принадлежать **одному пакету** (исключение — `_test.go` файлы, см. ниже). Имя пакета и имя директории обычно совпадают, но это не обязательное правило (хотя нарушать его — плохая идея).

Пакет — это **минимальная единица компиляции и переиспользования**. Импортируется он по пути от корня модуля:

```go
import "github.com/jtprogru/myapp/mathx"
```

### Экспортированные и приватные имена

В Go нет ключевых слов `public`/`private`. Видимость определяется регистром первой буквы имени:

- **С большой буквы** — экспортированное, доступно из других пакетов.
- **С маленькой** — приватное, видно только внутри текущего пакета.

```go
package mathx

func Sum(a, b int) int { return a + b }  // экспортирована
func mul(a, b int) int { return a * b }  // приватная
```

Это касается всего: функций, типов, полей структур, методов, констант, переменных.

```go
type User struct {
    ID       int    // экспортируется
    Name     string // экспортируется
    password string // приватное, не сериализуется в JSON и т. д.
}
```

### `init` — функция инициализации пакета

```go
package db

var conn *sql.DB

func init() {
    var err error
    conn, err = sql.Open("postgres", os.Getenv("DATABASE_URL"))
    if err != nil {
        log.Fatal(err)
    }
}
```

`init()` вызывается **автоматически** при первом импорте пакета, до `main`. У одного пакета может быть несколько `init` (даже в разных файлах) — порядок вызова в пределах пакета определяется порядком файлов в `go build`, но между пакетами — порядком зависимостей.

Старайтесь обходиться без `init`: глобальное состояние, скрытые побочные эффекты, неудобство тестирования. Лучший паттерн — явная функция-конструктор и DI.

### `_` — импорт ради побочного эффекта

```go
import _ "github.com/lib/pq"   // регистрирует драйвер в database/sql
```

Импорт с `_` означает: «выполни `init()` пакета, но не используй его символы». Применяется в основном для регистрации драйверов БД, кодеков и подобных «плагинов».

## Структура большого проекта

Соглашения уровня [golang-standards/project-layout](https://github.com/golang-standards/project-layout):

```text
myapp/
├── go.mod
├── go.sum
├── README.md
├── cmd/
│   ├── server/
│   │   └── main.go          # бинарник: ./bin/server
│   └── cli/
│       └── main.go          # бинарник: ./bin/cli
├── internal/                 # пакеты, доступные ТОЛЬКО внутри myapp
│   ├── config/
│   │   └── config.go
│   ├── handler/
│   │   ├── user.go
│   │   └── user_test.go
│   └── storage/
│       ├── interface.go
│       └── postgres/
│           └── postgres.go
├── pkg/                      # пакеты, разрешённые к импорту ИЗВНЕ (опционально)
│   └── client/
│       └── client.go
└── api/
    └── openapi.yaml
```

### `internal/` — это синтаксис компилятора

Если путь импорта содержит сегмент `internal`, то такой пакет разрешён к импорту **только** из пакетов с общим родителем `internal/`:

- `myapp/internal/handler` — можно импортировать из `myapp/cmd/server` ✅
- `myapp/internal/handler` — нельзя импортировать из `otherapp/cmd/server` ❌

Это лучший способ скрыть внутреннюю реализацию и зафиксировать публичный API в `pkg/`.

### `cmd/` для нескольких бинарников

Если проект собирает несколько бинарников (CLI, сервер, миграции), кладите каждый в свою поддиректорию `cmd/<name>/main.go`. Сборка тогда — `go build -o bin/server ./cmd/server`.

Если бинарник один — `main.go` можно держать прямо в корне модуля.

## Модули (`go mod`)

### Создание

```bash
go mod init github.com/jtprogru/myapp
```

Появляется файл `go.mod`:

```text
module github.com/jtprogru/myapp

go 1.23
```

### Добавление зависимостей

```bash
go get github.com/stretchr/testify@latest
go get github.com/spf13/cobra@v1.8.0
```

После этого `go.mod` пополняется блоком `require`, а файл `go.sum` — контрольными суммами загруженных версий.

```text
require (
    github.com/spf13/cobra v1.8.0
    github.com/stretchr/testify v1.9.0
)
```

`go.sum` нужно **коммитить в git** — он гарантирует, что у вас и у всех остальных собирается одна и та же версия. Это аналог `uv.lock`/`poetry.lock` в Python.

### Команды для зависимостей

```bash
go get -u ./...           # обновить все зависимости до последних минорных версий
go mod tidy               # синхронизировать go.mod/go.sum с реальным импортом в коде
go mod download           # скачать все зависимости в локальный кэш
go mod vendor             # сложить копии всех зависимостей в ./vendor/ (опционально)
go list -m -u all         # показать, какие зависимости можно обновить
```

`go mod tidy` запускайте перед каждым коммитом: он добавит недостающие зависимости и удалит «мёртвые», которые уже не используются.

### Версионирование

Go modules используют **семантическое версионирование** + специальные правила для мажорных версий 2+:

```text
github.com/foo/bar v1.2.3
github.com/foo/bar/v2 v2.0.1        // для мажор-2 путь содержит /v2
```

Pre-release и devel-версии используют псевдо-теги вида `v0.0.0-20240101120000-abc123def456`.

### `replace` — подмена зависимости

Удобно для локальной разработки или временного форка:

```text
replace github.com/foo/bar => ../bar
replace github.com/foo/bar => github.com/myorg/bar v1.2.3-fix
```

## Тестирование

В Go тесты — часть стандартной библиотеки, а не отдельный фреймворк.

### Базовый тест

Тесты живут рядом с кодом в файлах с суффиксом `_test.go`:

```text
mathx/
├── mathx.go
└── mathx_test.go
```

```go
// mathx.go
package mathx

func Sum(a, b int) int { return a + b }
```

```go
// mathx_test.go
package mathx

import "testing"

func TestSum(t *testing.T) {
    got := Sum(2, 3)
    want := 5
    if got != want {
        t.Errorf("Sum(2, 3) = %d, want %d", got, want)
    }
}
```

Запуск:

```bash
go test                  # тесты в текущем пакете
go test ./...            # все тесты во всём модуле
go test -v               # подробный вывод
go test -run TestSum     # только тесты, чьё имя матчит regex
go test -cover           # покрытие в процентах
go test -race ./...      # с детектором гонок (важно для конкурентного кода)
```

### `t.Error` vs `t.Fatal`

- `t.Error`, `t.Errorf` — пометить тест как проваленный, **продолжить** выполнение.
- `t.Fatal`, `t.Fatalf` — пометить и **немедленно** остановить тест (через `runtime.Goexit`, defer'ы выполнятся).

Используйте `Fatal`, если дальнейшие проверки бессмысленны без текущей.

### Табличные тесты (table-driven tests)

Идиома Go — описывать кейсы списком, потом итерироваться:

```go
func TestSum(t *testing.T) {
    cases := []struct {
        name    string
        a, b    int
        want    int
    }{
        {"positive", 2, 3, 5},
        {"zero", 0, 0, 0},
        {"negative", -1, -1, -2},
        {"overflow_safe", 100, 200, 300},
    }
    for _, tc := range cases {
        t.Run(tc.name, func(t *testing.T) {
            got := Sum(tc.a, tc.b)
            if got != tc.want {
                t.Errorf("Sum(%d, %d) = %d, want %d", tc.a, tc.b, got, tc.want)
            }
        })
    }
}
```

`t.Run(name, func)` создаёт подтест с отдельным именем. Удобно:

- в выводе видно, какой именно кейс упал;
- можно запустить только нужный: `go test -run TestSum/zero`;
- подтесты могут быть параллельными (см. ниже).

### Параллельные тесты

```go
func TestSum(t *testing.T) {
    cases := []struct{ a, b, want int }{ /* ... */ }
    for _, tc := range cases {
        t.Run(fmt.Sprintf("%d+%d", tc.a, tc.b), func(t *testing.T) {
            t.Parallel()   // помечаем подтест как параллельный
            got := Sum(tc.a, tc.b)
            if got != tc.want {
                t.Errorf("got=%d want=%d", got, tc.want)
            }
        })
    }
}
```

Все подтесты с `t.Parallel()` запускаются конкурентно (ограничено `-parallel N`). Полезно, когда тестов много и они независимы.

### Setup/teardown через `t.Cleanup` и helper

```go
func TestWithFile(t *testing.T) {
    f, err := os.CreateTemp("", "test_*.txt")
    if err != nil {
        t.Fatal(err)
    }
    t.Cleanup(func() {
        f.Close()
        os.Remove(f.Name())
    })
    // ... используем f ...
}
```

`t.Cleanup` — аналог Python `pytest` fixture с teardown. Выполнится при завершении теста (успешном или провальном).

### Бенчмарки

```go
func BenchmarkSum(b *testing.B) {
    for i := 0; i < b.N; i++ {
        _ = Sum(1, 2)
    }
}
```

Запуск:

```bash
go test -bench=. -benchmem
```

Подробно про бенчмарки и профилирование — в последней лекции темы 14.

### Fuzz-тестирование (Go 1.18+)

```go
func FuzzSum(f *testing.F) {
    f.Add(1, 2)
    f.Fuzz(func(t *testing.T, a, b int) {
        got := Sum(a, b)
        if got != a+b {
            t.Errorf("Sum(%d, %d) = %d", a, b, got)
        }
    })
}
```

```bash
go test -fuzz=FuzzSum
```

Раннер сам подбирает «странные» входные данные (большие, отрицательные, граничные) и ищет падения. В стандартной библиотеке так нашли несколько багов парсеров.

### Внешний и внутренний тестовый пакет

Можно тестировать как **изнутри** пакета (видны приватные имена), так и **снаружи** (только публичный API):

```go
// mathx_test.go — внутренний пакет
package mathx
// видит mathx.mul и т. п.
```

```go
// mathx_external_test.go — внешний пакет
package mathx_test
import "github.com/.../mathx"
// видит только mathx.Sum
```

Оба варианта живут в одной директории. Внешний полезен для проверки, что публичный API достаточен и не требует костылей.

## Покрытие

```bash
go test -coverprofile=cover.out ./...
go tool cover -html=cover.out -o cover.html
open cover.html
```

В индустрии 70–80% покрытия — нормальный ориентир, но цифра сама по себе ничего не говорит. Гораздо важнее покрытие «горячих» путей.

## Сторонние библиотеки для тестов

Стандартный `testing` достаточен, но многие команды используют:

- [testify](https://github.com/stretchr/testify) — `assert.Equal`, `require.NoError`, моки;
- [gomock](https://github.com/uber-go/mock) (`mockgen`) — генерация моков по интерфейсам;
- [testcontainers-go](https://github.com/testcontainers/testcontainers-go) — поднимать настоящий Postgres/Redis в Docker для интеграционных тестов.

## Параллель с Python

| Python                                            | Go                                                 |
|---------------------------------------------------|-----------------------------------------------------|
| модуль = файл                                     | пакет = директория                                  |
| `__init__.py`, `from x import y`                  | `package x` + `import "module/x"`                   |
| `from x import _y` — приватное по соглашению      | приватное по регистру (компилятор forces)           |
| `pyproject.toml` + `uv.lock`                      | `go.mod` + `go.sum`                                 |
| `pytest`                                           | `go test`                                            |
| `@pytest.mark.parametrize`                        | подтесты `t.Run` + табличные тесты                  |
| фикстуры (`@pytest.fixture`)                      | `t.Cleanup`, helper-функции                         |
| `unittest.TestCase`                               | `func TestXxx(t *testing.T)`                        |
| `pytest --cov`                                    | `go test -cover -coverprofile=...`                  |
| `hypothesis`                                       | `func FuzzXxx(f *testing.F)`                         |

## Итог

Пакет — единица организации (директория = пакет). Видимость по регистру первой буквы. Модуль (`go.mod`) — единица версионирования и зависимостей; `go.sum` коммитится. Тесты — встроенный пакет `testing`, идиома — табличные тесты + `t.Run`. Покрытие, бенчмарки, fuzz — всё «из коробки», без отдельных фреймворков. На этом основы Go заканчиваются — в теме 14 мы перейдём к конкурентности, контексту, HTTP, БД и профилированию.
