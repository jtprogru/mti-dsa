# Лекция 3. Функции, ошибки и `panic`/`recover`

## Объявление функций

```go
func add(a, b int) int {
    return a + b
}
```

Синтаксис: `func имя(параметры) тип-результата { ... }`. Если несколько параметров одного типа идут подряд — тип можно указать один раз: `func add(a, b int)` вместо `func add(a int, b int)`.

### Несколько возвращаемых значений

В отличие от Python, где функция возвращает кортеж и его можно распаковать, в Go это встроенная фича языка:

```go
func divmod(a, b int) (int, int) {
    return a / b, a % b
}

q, r := divmod(17, 5)
fmt.Println(q, r)  // 3 2
```

Один из возвращаемых параметров можно игнорировать через `_`:

```go
q, _ := divmod(17, 5)
```

### Именованные возвращаемые значения

Можно дать имена возвращаемым значениям прямо в сигнатуре. Тогда они объявляются как переменные внутри функции, и `return` без аргументов («naked return») возвращает их текущие значения:

```go
func divide(a, b float64) (result float64, err error) {
    if b == 0 {
        err = errors.New("division by zero")
        return
    }
    result = a / b
    return
}
```

Это удобно для документирования (видно, что значит каждый результат) и для коротких функций. Для длинных — naked return делают код хуже читаемым, лучше писать `return result, err` явно.

### Variadic-функции

```go
func sum(nums ...int) int {
    total := 0
    for _, n := range nums {
        total += n
    }
    return total
}

fmt.Println(sum(1, 2, 3))      // 6
fmt.Println(sum(1, 2, 3, 4, 5)) // 15

// Раскрыть срез в variadic-аргументы
nums := []int{1, 2, 3}
fmt.Println(sum(nums...))  // 6
```

Это аналог Python `*args`. Аналога `**kwargs` (именованных параметров) в Go нет — для этого используют структуру или паттерн functional options (см. ниже).

### Functional options — идиоматичный паттерн

Поскольку именованных аргументов нет, при большом числе опциональных параметров в Go применяют паттерн functional options:

```go
type Server struct {
    host    string
    port    int
    timeout time.Duration
    tls     bool
}

type Option func(*Server)

func WithPort(p int) Option           { return func(s *Server) { s.port = p } }
func WithTimeout(d time.Duration) Option { return func(s *Server) { s.timeout = d } }
func WithTLS() Option                  { return func(s *Server) { s.tls = true } }

func NewServer(host string, opts ...Option) *Server {
    s := &Server{host: host, port: 8080, timeout: 30 * time.Second}
    for _, opt := range opts {
        opt(s)
    }
    return s
}

srv := NewServer("0.0.0.0", WithPort(443), WithTLS(), WithTimeout(60*time.Second))
```

Так устроены конструкторы во многих популярных библиотеках Go (`grpc`, `zap`, `viper`).

## Функции — first-class values

Функцию можно сохранить в переменную, передать в другую функцию, вернуть из функции.

```go
func apply(f func(int) int, x int) int {
    return f(x)
}

double := func(x int) int { return x * 2 }
fmt.Println(apply(double, 21))  // 42
```

### Замыкания

Функция-литерал захватывает переменные окружающей области видимости по ссылке:

```go
func counter() func() int {
    n := 0
    return func() int {
        n++
        return n
    }
}

next := counter()
fmt.Println(next(), next(), next())  // 1 2 3
```

Каждый вызов `counter()` создаёт новую переменную `n` и новое замыкание.

### Известная ловушка: захват переменной цикла

До Go 1.22 переменная цикла переиспользовалась — все горутины/замыкания видели одно и то же значение:

```go
// До Go 1.22 — БАГ
for i := 0; i < 3; i++ {
    go func() {
        fmt.Println(i)  // часто напечатает 3, 3, 3
    }()
}
```

В Go 1.22 семантику изменили: теперь на каждой итерации создаётся новая переменная (как в Python). Но если ваш проект на старом Go (`go 1.21` в `go.mod`) — пишите явно:

```go
for i := 0; i < 3; i++ {
    i := i  // создаём локальную копию
    go func() {
        fmt.Println(i)
    }()
}
```

## Ошибки как значения

В Go нет исключений в привычном смысле. Ошибки — это **обычные значения**, которые функция возвращает наряду с результатом. По соглашению — последним возвращаемым значением.

```go
func readConfig(path string) (Config, error) {
    data, err := os.ReadFile(path)
    if err != nil {
        return Config{}, fmt.Errorf("read config: %w", err)
    }
    var cfg Config
    if err := json.Unmarshal(data, &cfg); err != nil {
        return Config{}, fmt.Errorf("parse config: %w", err)
    }
    return cfg, nil
}
```

Вызывающая сторона обязательно проверяет `err`:

```go
cfg, err := readConfig("app.yaml")
if err != nil {
    log.Fatal(err)
}
```

Идиома `if err != nil { return ... }` встречается чуть ли не на каждой пятой строке Go-кода. Это считается особенностью языка («Go is verbose»). В обмен вы получаете явный поток ошибок — невозможно «пропустить» исключение, как это бывает в Python.

### Тип `error`

`error` — это встроенный интерфейс:

```go
type error interface {
    Error() string
}
```

Любой тип, у которого есть метод `Error() string`, удовлетворяет `error`. Подробнее про интерфейсы — лекция 5.

### Создание ошибок

Простейший способ — пакет `errors`:

```go
import "errors"

err := errors.New("something went wrong")
```

С форматированием — `fmt.Errorf`:

```go
err := fmt.Errorf("read file %s: %w", path, originalErr)
```

Глагол `%w` — особенный: он **оборачивает** другую ошибку, сохраняя её внутри новой. После этого можно проверить корневую причину через `errors.Is`/`errors.As`.

### Sentinel errors

Часто библиотеки предоставляют заранее объявленные значения ошибок, по которым можно проверять конкретные ситуации:

```go
// в стандартной библиотеке
var ErrNotExist = errors.New("file does not exist")

// в нашем коде
if errors.Is(err, os.ErrNotExist) {
    // файл не существует — создаём
}
```

`errors.Is` рекурсивно разворачивает обёртки и сравнивает с целевым значением. Это правильный способ — никогда не сравнивайте через `==` или по тексту ошибки.

### Custom error types

Когда нужно передать в ошибке структурированные данные:

```go
type ValidationError struct {
    Field   string
    Message string
}

func (e *ValidationError) Error() string {
    return fmt.Sprintf("validation: %s: %s", e.Field, e.Message)
}

// использование
err := &ValidationError{Field: "email", Message: "invalid format"}

// проверка типа
var ve *ValidationError
if errors.As(err, &ve) {
    fmt.Println("плохое поле:", ve.Field)
}
```

`errors.As` — аналог `errors.Is`, но не для конкретного значения, а для типа. Если в цепочке обёрток найдётся ошибка нужного типа, она присваивается в `&ve`.

### Sentinel vs typed — что выбрать

- Если состояние можно описать константой и больше нечего вкладывать — sentinel (`var ErrNotFound = errors.New("not found")`).
- Если нужны данные внутри (поле, код, контекст) — отдельный тип.

И **не возвращайте `error` как deepcopy строки** — не пишите `func() string` вместо `func() error`. Это сразу ломает все механизмы оборачивания и проверки.

## `panic` и `recover`

`panic` — механизм для **исключительных, неожиданных** ситуаций, аналог исключений. Когда вызывается `panic(value)`, текущая функция немедленно прекращает выполнение, выполняются все её `defer`, потом то же происходит в вызвавшей функции и так до самого `main`, после чего программа аварийно завершается с выводом stack trace.

```go
func divide(a, b int) int {
    if b == 0 {
        panic("division by zero")
    }
    return a / b
}
```

`recover` — единственный способ перехватить `panic`. Работает только внутри `defer`:

```go
func safeDivide(a, b int) (result int, err error) {
    defer func() {
        if r := recover(); r != nil {
            err = fmt.Errorf("recovered: %v", r)
        }
    }()
    return divide(a, b), nil
}
```

### Когда использовать `panic`

**Почти никогда** в обычной бизнес-логике. Идиома Go — возвращать `error`. `panic` уместен:

1. **Программные ошибки**, которые нельзя обработать (нарушение инварианта, обращение по nil-указателю). В стандартной библиотеке так делают, например, `regexp.MustCompile` — паникует, если регулярка некорректна.
2. **На границе библиотеки** — паника изнутри ловится `recover` на верхнем уровне и превращается в `error` (так делают многие парсеры).
3. **В тестах** — `t.Fatal` под капотом использует `runtime.Goexit`, но `panic("not implemented")` — нормальный способ пометить заглушку.

Помните: паника пересекает границы горутин (см. тему 14), и неперехваченная паника в горутине рушит всю программу.

## `defer` для cleanup и неявных эффектов

Уже видели в прошлой лекции. Ещё несколько идиом:

```go
// Освобождение мьютекса
mu.Lock()
defer mu.Unlock()

// Закрытие HTTP-тела ответа
resp, err := http.Get(url)
if err != nil {
    return err
}
defer resp.Body.Close()

// Логирование времени выполнения
defer func(start time.Time) {
    log.Printf("operation took %v", time.Since(start))
}(time.Now())
```

В последнем примере обратите внимание: `time.Now()` вычисляется **сразу** (когда выполняется строка с `defer`), а функция вызовется в конце.

## Параллель с Python

| Python                                                | Go                                                       |
|-------------------------------------------------------|----------------------------------------------------------|
| `def f(a, b): return a, b`                            | `func f(a, b int) (int, int) { return a, b }`            |
| `*args`                                               | `nums ...int`                                            |
| `**kwargs`                                            | functional options или структура с полями                |
| `def f(x=10):`                                        | нет (только functional options или nil-проверка)         |
| `try: ... except SpecificError as e: ...`             | `if err != nil { ... if errors.As(err, &ve) { ... } }`   |
| `raise CustomException("msg")`                        | `return &CustomError{Msg: "msg"}`                        |
| `raise OneError() from other`                         | `fmt.Errorf("...: %w", other)`                           |
| `try: ... finally: ...`                               | `defer ...`                                              |
| исключения как поток управления                       | ошибки как значения                                      |
| `lambda x: x * 2`                                     | `func(x int) int { return x * 2 }` (нет короткого лямбда-синтаксиса) |
| замыкания и lexical scoping                           | то же самое                                              |

## Итог

Функции — first-class, поддерживают несколько возвращаемых значений, variadic-параметры и замыкания. Ошибки — обычные значения, проверяются явно через `if err != nil`. Оборачивание — `%w` + `errors.Is`/`errors.As`. `panic`/`recover` — для исключительных ситуаций, не для бизнес-логики. В следующей лекции — массивы, срезы, карты и структуры.
