# Лекция 5. Методы и интерфейсы

## Методы

Метод в Go — это функция с особым параметром-«получателем» (receiver) перед именем:

```go
type Rectangle struct {
    Width, Height float64
}

func (r Rectangle) Area() float64 {
    return r.Width * r.Height
}

r := Rectangle{Width: 3, Height: 4}
fmt.Println(r.Area())   // 12
```

Запись `(r Rectangle)` — это receiver. Внутри метода `r` — это копия структуры (по значению).

### Value receiver vs pointer receiver

```go
// получатель по значению — метод работает с КОПИЕЙ
func (r Rectangle) Scale(k float64) {
    r.Width *= k
    r.Height *= k
}

// получатель по указателю — метод видит/меняет ОРИГИНАЛ
func (r *Rectangle) ScaleInPlace(k float64) {
    r.Width *= k
    r.Height *= k
}

r := Rectangle{3, 4}
r.Scale(2)         // ничего не изменилось
fmt.Println(r)     // {3 4}
r.ScaleInPlace(2)  // Go автоматически возьмёт &r
fmt.Println(r)     // {6 8}
```

### Когда что использовать

**Pointer receiver:**

1. Метод должен изменить состояние.
2. Структура «тяжёлая» — копировать дорого.
3. Структура содержит мьютекс, файл-дескриптор и т. п. — копировать нельзя.

**Value receiver:**

1. Тип маленький и иммутабельный (примитивы, точки, цвета).
2. Структура должна семантически быть значением (например, `time.Time`).

**Правило согласованности.** Если у типа есть хоть один метод с pointer receiver — обычно делают все методы pointer receiver. Иначе путаница: одни методы изменяют состояние, другие нет.

### Методы на любых типах

Можно объявить методы не только на структурах, а на любом типе, объявленном в этом же пакете:

```go
type Status int

const (
    StatusPending Status = iota
    StatusActive
    StatusBanned
)

func (s Status) String() string {
    return [...]string{"pending", "active", "banned"}[s]
}
```

Этим часто пользуются: своим именем оборачивают `int`, `string`, `[]byte` — и навешивают на них поведение.

Что нельзя — добавить метод к чужому типу. Например, написать `func (s string) Reverse() string` запрещено, потому что `string` объявлен в пакете `builtin`. Это намеренно: предотвращает «monkey patching».

## Интерфейсы

Интерфейс — это **набор сигнатур методов**. Любой тип, который реализует все эти методы, **автоматически** удовлетворяет интерфейсу. Не нужно писать `implements` или `extends`.

```go
type Shape interface {
    Area() float64
    Perimeter() float64
}

type Circle struct {
    Radius float64
}

func (c Circle) Area() float64      { return math.Pi * c.Radius * c.Radius }
func (c Circle) Perimeter() float64 { return 2 * math.Pi * c.Radius }

func describe(s Shape) {
    fmt.Printf("площадь=%.2f, периметр=%.2f\n", s.Area(), s.Perimeter())
}

describe(Circle{Radius: 5})
```

`Circle` нигде не указывает, что «реализует» `Shape`. Это **structural typing** — компилятор просто проверяет, что у переданного значения есть нужные методы.

Этот подход напоминает Python `typing.Protocol` (PEP 544) и противоположен Java/C#, где надо явно писать `implements`.

### Несколько реализаций

```go
type Rectangle struct{ W, H float64 }
func (r Rectangle) Area() float64      { return r.W * r.H }
func (r Rectangle) Perimeter() float64 { return 2 * (r.W + r.H) }

shapes := []Shape{
    Circle{Radius: 5},
    Rectangle{W: 3, H: 4},
}
for _, s := range shapes {
    describe(s)
}
```

### Пустой интерфейс / `any`

Интерфейс без методов — `interface{}`. С Go 1.18 для него есть синоним `any`. Удовлетворить ему может **любой** тип.

```go
var x any = 42
x = "hello"
x = []int{1, 2, 3}
```

Это аналог Python `Any` или `object`. Использование `any` подавляет типобезопасность — берегите его на крайний случай (универсальные контейнеры, параметры логгера, передача через границы пакетов).

С появлением дженериков многие случаи `any` теперь решаются типобезопасно (см. ниже).

### Type assertion и type switch

Из значения интерфейса можно «достать» конкретный тип:

```go
var i any = "hello"

s := i.(string)         // panic, если внутри не string
s, ok := i.(string)     // safe-форма с comma-ok

if v, ok := i.(int); ok {
    fmt.Println("int:", v)
}
```

Когда нужно различить несколько типов — `type switch`:

```go
func describe(i any) string {
    switch v := i.(type) {
    case int:
        return fmt.Sprintf("int=%d", v)
    case string:
        return fmt.Sprintf("string=%q", v)
    case []int:
        return fmt.Sprintf("[]int len=%d", len(v))
    case nil:
        return "nil"
    default:
        return fmt.Sprintf("unknown %T", v)
    }
}
```

Конструкция `v := i.(type)` работает только внутри `switch`.

## Композиция интерфейсов

Один интерфейс может встраивать другие:

```go
type Reader interface {
    Read(p []byte) (n int, err error)
}

type Writer interface {
    Write(p []byte) (n int, err error)
}

type ReadWriter interface {
    Reader
    Writer
}
```

Это базовая идиома стандартной библиотеки. Всё, что умеет читать и писать, автоматически удовлетворяет `io.ReadWriter`.

## Каноничные интерфейсы стандартной библиотеки

Запомните их — они везде:

### `error`

```go
type error interface {
    Error() string
}
```

Уже обсуждали в лекции 3.

### `fmt.Stringer`

```go
type Stringer interface {
    String() string
}
```

Если тип реализует `String()`, его форматирование `%v`, `%s` и `fmt.Println` использует этот метод.

```go
type Distance float64

func (d Distance) String() string {
    return fmt.Sprintf("%.2f км", float64(d))
}

fmt.Println(Distance(3.14159))   // 3.14 км
```

### `io.Reader` и `io.Writer`

```go
type Reader interface {
    Read(p []byte) (n int, err error)
}

type Writer interface {
    Write(p []byte) (n int, err error)
}
```

Файлы, сетевые соединения, буферы (`bytes.Buffer`), архивы — всё это `Reader`/`Writer`. Благодаря этому одни и те же функции (`io.Copy`, `bufio.NewScanner`, `json.NewDecoder`) работают и с файлами, и с сетью, и с памятью.

### `sort.Interface` (устарел, но полезен для понимания)

```go
type Interface interface {
    Len() int
    Less(i, j int) bool
    Swap(i, j int)
}
```

Раньше — единственный способ сортировки кастомных коллекций. Сейчас — `slices.SortFunc` (Go 1.21+), но интерфейс всё ещё используется в legacy-коде.

## `nil` интерфейс — известная ловушка

Интерфейс внутри — это пара `(тип, значение)`. Интерфейс равен `nil`, только если **и тип, и значение `nil`**.

```go
var p *MyError = nil   // p — nil-указатель
var e error = p        // e — НЕ nil (тип внутри = *MyError, значение = nil)

if e == nil {
    fmt.Println("чисто")
} else {
    fmt.Println("грязно")   // напечатает это
}
```

Это **самый частый WTF-момент** для новичков. Решение: возвращайте `nil` напрямую, а не «nil-указатель типизированной ошибки»:

```go
func do() error {
    if ok {
        return nil   // ОК
    }
    return &MyError{}
}
```

## Дженерики (с Go 1.18)

До 1.18 дженериков не было — приходилось писать одно и то же для каждого типа или использовать `any` и type assertions. В 1.18 их наконец добавили.

```go
func Max[T cmp.Ordered](a, b T) T {
    if a > b {
        return a
    }
    return b
}

Max(3, 5)        // int
Max(3.14, 2.71)  // float64
Max("a", "b")    // string
```

`[T cmp.Ordered]` — параметр типа с **ограничением** (constraint). `cmp.Ordered` — встроенное ограничение (Go 1.21+): любой упорядочиваемый тип (числа, строки).

### Пользовательские ограничения

```go
type Number interface {
    int | int64 | float64
}

func Sum[T Number](nums []T) T {
    var total T
    for _, n := range nums {
        total += n
    }
    return total
}
```

Здесь `int | int64 | float64` — type union, новая форма интерфейса для дженериков.

### Дженерики и интерфейсы

В большинстве случаев интерфейсы остаются удобнее (поведенческая абстракция), а дженерики уместны для контейнеров и алгоритмов на разных типах данных (одна реализация для `int`/`float64`/`string`). Хорошее правило: «если в коде есть `interface{}` + type assertion — может, нужен дженерик».

## Параллель с Python

| Python                                       | Go                                              |
|----------------------------------------------|--------------------------------------------------|
| `class C: def m(self): ...`                  | `func (c *C) M() { ... }`                       |
| `@abstractmethod` / `Protocol`               | интерфейс (структурно — как Protocol)           |
| `isinstance(x, T)`                           | type assertion `x.(T)`                          |
| `match x: case int(): ...`                   | `switch v := x.(type) { case int: ... }`        |
| наследование классов                         | embedding структур + интерфейсов                |
| дак-тайпинг                                  | structural typing (статический эквивалент)      |
| `T = TypeVar("T")` + generic                 | `[T any]` (Go 1.18+)                            |
| `Any`                                        | `any` (синоним `interface{}`)                   |
| `__str__`                                    | `String() string` (интерфейс `fmt.Stringer`)    |

## Итог

Метод в Go — функция с receiver. Value receiver работает с копией, pointer receiver — с оригиналом; внутри типа методы согласуют. Интерфейс — набор методов; реализация автоматическая (structural typing). Канонические `error`, `fmt.Stringer`, `io.Reader`/`io.Writer`. Дженерики с 1.18 закрывают то, что раньше делали через `any`. В последней лекции темы — пакеты и тестирование.
