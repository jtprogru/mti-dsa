# Лекция 3. Ошибки, исключения и декораторы

В любой нетривиальной программе могут возникать ошибки. Причины разные: программист допустил опечатку в синтаксисе языка; пользователь ввёл не те данные; внешний сервис упал; файл удалили во время чтения. Способ, которым язык программирования сообщает об ошибке и позволяет её обработать, во многом определяет стиль кода.

В этой лекции:

- разберём, как устроена обработка ошибок в Python (`try/except/finally`, `raise`, собственные классы исключений, `assert`);
- посмотрим на принципиально другой подход в Go — ошибки как значения, `errors.Is/As`, `panic/recover`;
- познакомимся с декораторами Python и аналогичным паттерном middleware в Go;
- применим декораторы к практическим задачам — логирование ошибок и retry.

## Синтаксические ошибки vs исключения

Если в коде есть нарушение синтаксиса языка, интерпретатор Python не сможет даже начать выполнение и сразу укажет на место:

```text
File "<stdin>", line 1
    1a = 10
    ^
SyntaxError: invalid syntax
```

`SyntaxError` — это всё-таки **ошибка**: программа не запустилась. Всё остальное, что возникает во время выполнения, в Python называют **исключениями** (exceptions). В других языках употребляют термин «семантические ошибки», но в Python принято говорить об исключениях.

> **Traceback** — обратная трассировка вызовов, которую Python печатает при необработанном исключении. Читается снизу вверх: внизу сама ошибка, выше — путь вызовов, который привёл к ней. По трассировке быстрее всего находят место поломки.

Типичные встроенные исключения:

| Исключение | Когда возникает |
|------------|-----------------|
| `NameError` | Использована необъявленная переменная. |
| `ValueError` | Значение не соответствует ожидаемому типу/диапазону: `int("Hi")`. |
| `TypeError` | Операция между несовместимыми типами: `8 + "3"`. |
| `ZeroDivisionError` | Деление на ноль. |
| `KeyError` / `IndexError` | Нет такого ключа в словаре / индекса в списке. |
| `FileNotFoundError` | Открытие несуществующего файла. |
| `AttributeError` | Обращение к несуществующему атрибуту объекта. |

Полная иерархия — в [документации Python](https://docs.python.org/3/library/exceptions.html). Все исключения наследуются от `BaseException` (а пользовательские — от `Exception`).

## Перехват исключений: `try/except`

Когда ошибки могут возникнуть из-за внешнего мира (ввод пользователя, файл, сеть) — их нужно обрабатывать, а не давать программе падать.

```python
try:
    n = int(input("Введите целое число: "))
except ValueError:
    print("Вы ввели не целое число")
else:
    print(f"Вы ввели число {n}")
```

Логика:

- блок `try` — то, что *может* выбросить исключение;
- `except <Класс>:` — обработчик конкретного типа исключения;
- `else` — выполнится, если в `try` исключений *не было*;
- `finally` — выполнится в любом случае (типичное применение — закрыть ресурс).

Несколько типов исключений можно объединить:

```python
try:
    a = float(input("Делимое: "))
    b = float(input("Делитель: "))
    print(f"Частное: {a / b:.2f}")
except (ValueError, ZeroDivisionError) as exc:
    print(f"Не получилось: {exc}")
```

Конструкция `as exc` сохраняет объект исключения — у него обычно есть атрибуты и понятный `__str__`.

### Чего НЕ делать

```python
# Плохо: ловим всё подряд и проглатываем.
try:
    do_something()
except:        # ловит даже KeyboardInterrupt, SystemExit
    pass
```

«Голый» `except:` (или `except Exception: pass`) — антипаттерн. Он:

1. Маскирует баги.
2. Делает программу неотлаживаемой.
3. Перехватывает даже `KeyboardInterrupt` — программа перестаёт реагировать на `Ctrl+C`.

Правильно — ловить **конкретные** типы исключений, а необработанные — пробрасывать дальше.

## Возбуждение исключений: `raise`

```python
def sqrt(x: float) -> float:
    if x < 0:
        raise ValueError(f"Отрицательное число: {x}")
    return x ** 0.5
```

Если хочется поймать, что-то залогировать и пробросить дальше — используется `raise` без аргументов:

```python
try:
    do_something()
except DatabaseError:
    logger.exception("Сохранение упало")
    raise
```

Сохраняется и оригинальный traceback, и место повторной выдачи.

### Цепочка исключений

```python
try:
    parse(data)
except ValueError as exc:
    raise ParseError("Не удалось распарсить вход") from exc
```

`raise … from exc` сохраняет цепочку: в traceback видно и исходную, и обёрнутую ошибку.

## Собственные классы исключений

Когда встроенных классов не хватает по смыслу — заводят свои, наследуя от `Exception` (или подходящего подкласса).

```python
class ShortInputError(Exception):
    def __init__(self, length: int, atleast: int) -> None:
        super().__init__(
            f"Длина введённой строки {length}, ожидалось минимум {atleast}"
        )
        self.length = length
        self.atleast = atleast


try:
    text = input("Введите что-нибудь: ")
    if len(text) < 3:
        raise ShortInputError(len(text), 3)
except ShortInputError as exc:
    print(exc)
    print(f"Не хватает {exc.atleast - exc.length} символов")
```

Хороший стиль:

- в больших проектах вводят базовый класс — `class AppError(Exception): ...` — и наследуют все доменные исключения от него (`UserNotFound(AppError)`, `PaymentDeclined(AppError)`). Это позволяет одним `except AppError` ловить весь домен и пропускать чужие.
- сообщение пишут в `super().__init__(...)`.
- дополнительные поля (`length`, `atleast`) — для программной обработки.

## `assert`

`assert` проверяет инвариант: если условие ложно — возбуждается `AssertionError`.

```python
def average(values: list[float]) -> float:
    assert values, "average: пустой список"
    return sum(values) / len(values)
```

Важные особенности:

- `assert` предназначен только для **проверки внутренних инвариантов** программы — ситуаций, которые не должны возникать, если код правильный;
- **не** для валидации пользовательского ввода — для этого используйте `if` + `raise ValueError(...)`;
- при запуске Python с флагом `-O` (`python -O script.py`) все `assert` пропускаются — нельзя полагаться на побочные эффекты внутри `assert`.

## Контекстные менеджеры — альтернатива `try/finally`

Часто `finally` нужен, чтобы закрыть ресурс. В Python для этого есть оператор `with`:

```python
# Вместо try/finally
with open("data.txt", encoding="utf-8") as f:
    data = f.read()
# Файл закрыт автоматически, даже если внутри было исключение.
```

`with` работает с любым объектом, реализующим протокол контекстного менеджера (`__enter__` / `__exit__`).

## Обработка ошибок в Go

В Go нет исключений в привычном смысле. Ошибка — это **значение типа `error`**, которое функция возвращает наравне с обычным результатом.

```go
package main

import (
    "fmt"
    "strconv"
)

func main() {
    n, err := strconv.Atoi("123abc")
    if err != nil {
        fmt.Println("не удалось распарсить:", err)
        return
    }
    fmt.Println("число:", n)
}
```

Идиоматический паттерн — проверка `if err != nil` сразу после вызова. Это многословно, но делает поток ошибок видимым в коде.

### Создание ошибок

```go
import (
    "errors"
    "fmt"
)

var ErrNotFound = errors.New("not found")

func find(id int) (string, error) {
    if id == 0 {
        return "", ErrNotFound
    }
    if id < 0 {
        return "", fmt.Errorf("отрицательный id: %d", id)
    }
    return "ok", nil
}
```

- `errors.New("...")` — для статических ошибок.
- `fmt.Errorf("...: %v", x)` — форматирование (как `printf`).
- `fmt.Errorf("...: %w", err)` — **оборачивание** ошибки, чтобы сохранить цепочку (аналог `raise ... from exc`).

### `errors.Is` и `errors.As`

Чтобы проверить, не была ли ошибка обёрнута в другую — используют `errors.Is` (сравнение по значению) и `errors.As` (приведение к конкретному типу):

```go
import "errors"

if errors.Is(err, ErrNotFound) {
    // err — это ErrNotFound, даже если она была обёрнута через %w
}

var pathErr *os.PathError
if errors.As(err, &pathErr) {
    fmt.Println("проблема с путём:", pathErr.Path)
}
```

### Кастомные типы ошибок

```go
type ValidationError struct {
    Field   string
    Message string
}

func (e *ValidationError) Error() string {
    return fmt.Sprintf("%s: %s", e.Field, e.Message)
}
```

Любой тип, реализующий метод `Error() string`, удовлетворяет интерфейсу `error`.

### `panic` и `recover` — аналог исключений

Для **исключительных** ситуаций (не для штатной обработки!) в Go есть `panic`. Если не перехвачен — программа завершается с trace stack. Перехватывают через `defer` + `recover`:

```go
func safe() {
    defer func() {
        if r := recover(); r != nil {
            fmt.Println("восстановились после паники:", r)
        }
    }()

    panic("что-то пошло не так")
}
```

В нормальном Go-коде `panic` практически не используется напрямую. Допустимые случаи: невосстановимые баги программиста, инициализация, граница между языками (CGO).

## Сравнение Python ↔ Go

| Аспект | Python | Go |
|--------|--------|-----|
| Базовая модель | Исключения (выбрасываются вверх по стеку) | Возвращаемые значения типа `error` |
| Перехват | `try/except` | `if err != nil` |
| Цепочка | `raise X from y` | `fmt.Errorf("...: %w", err)` |
| Проверка типа | `except SpecificError` / `isinstance` | `errors.Is`, `errors.As` |
| «Очистить ресурс» | `finally`, `with` | `defer` |
| Внутренние инварианты | `assert` | `panic` (в крайнем случае) |
| Иерархия | Глубокое наследование от `Exception` | Плоская: интерфейс `error` |

Подходы — диаметрально разные:

- **Python**: ошибки распространяются «вверх» автоматически, обработать их можно как близко к источнику, так и на самом верху.
- **Go**: каждая функция явно решает, что делать с ошибкой; пропустить её сложно.

В обоих языках критично логировать контекст: что именно пошло не так, при каких входных данных.

## Декораторы в Python

Декоратор — функция, которая принимает другую функцию и возвращает новую функцию, обычно «обёрнутую» дополнительным поведением. Это применение паттерна **Decorator** из «банды четырёх», для которого в Python есть синтаксический сахар `@decorator`.

### Функции — объекты первого класса

Чтобы декораторы были понятны, нужно вспомнить три факта о функциях в Python:

```python
def shout(word: str = "да") -> str:
    return word.capitalize() + "!"


# 1. Функцию можно присвоить переменной.
scream = shout
print(scream())  # Да!

# 2. Функцию можно определить внутри другой функции.
def talk() -> None:
    def whisper(word: str = "да") -> str:
        return word.lower() + "..."
    print(whisper())


# 3. Функцию можно вернуть из другой функции и передать как аргумент.
def get_talk(mode: str = "shout"):
    def shout_inner() -> str: return "Да!"
    def whisper_inner() -> str: return "да..."
    return shout_inner if mode == "shout" else whisper_inner


talk_fn = get_talk("whisper")
print(talk_fn())  # да...
```

### Минимальный декоратор

```python
def my_decorator(fn):
    def wrapper():
        print("До вызова")
        result = fn()
        print("После вызова")
        return result
    return wrapper


@my_decorator
def hello() -> None:
    print("Привет")


hello()
# До вызова
# Привет
# После вызова
```

Запись `@my_decorator` над `hello` эквивалентна:

```python
hello = my_decorator(hello)
```

### Передача аргументов и `*args, **kwargs`

Декоратор не знает заранее сигнатуру декорируемой функции, поэтому wrapper обычно принимает `*args, **kwargs`:

```python
def trace(fn):
    def wrapper(*args, **kwargs):
        print(f"-> {fn.__name__}{args} {kwargs}")
        result = fn(*args, **kwargs)
        print(f"<- {fn.__name__} = {result!r}")
        return result
    return wrapper


@trace
def add(a: int, b: int) -> int:
    return a + b


add(2, 3)
# -> add(2, 3) {}
# <- add = 5
```

### `functools.wraps`

После применения декоратора `wrapper` подменяет оригинальную функцию — теряются её имя, docstring и аннотации. Чтобы их сохранить, оборачивают wrapper в `functools.wraps`:

```python
from functools import wraps


def trace(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        print(f"-> {fn.__name__}")
        return fn(*args, **kwargs)
    return wrapper
```

Без `wraps` сломаются `help()`, отладчик, любая интроспекция.

### Декораторы с параметрами

Если декоратору самому нужны параметры — добавляется ещё один уровень функций:

```python
def repeat(times: int):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            for _ in range(times):
                fn(*args, **kwargs)
        return wrapper
    return decorator


@repeat(times=3)
def hi() -> None:
    print("Привет!")


hi()
# Привет!
# Привет!
# Привет!
```

`@repeat(times=3)` — это вызов `repeat(3)`, который возвращает декоратор; этот декоратор уже применяется к `hi`.

### Стандартные декораторы из `functools`

- **`functools.cache`** — мемоизация без ограничения.
- **`functools.lru_cache(maxsize=…)`** — мемоизация с ограничением.
- **`functools.singledispatch`** — диспетчеризация по типу первого аргумента.
- **`functools.wraps`** — сохранение метаданных (см. выше).

```python
from functools import cache


@cache
def fib(n: int) -> int:
    return n if n < 2 else fib(n - 1) + fib(n - 2)
```

## Практика: логирование исключений и retry

### Логирование исключений

Чтобы не писать `try/except` в каждой функции:

```python
import logging
from functools import wraps

log = logging.getLogger(__name__)


def log_errors(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception:
            log.exception("Ошибка в %s", fn.__name__)
            raise
    return wrapper


@log_errors
def divide(a: float, b: float) -> float:
    return a / b


divide(1, 0)  # запишет traceback в лог и пробросит ZeroDivisionError
```

`log.exception(...)` — это `log.error` + автоматически добавленный traceback.

### Повторные попытки (retry)

```python
import time
from functools import wraps


def retry(tries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Повторяет вызов функции при исключении."""
    if tries < 1 or delay < 0 or backoff < 1:
        raise ValueError("плохие параметры retry")

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            current_delay = delay
            attempts_left = tries
            while True:
                try:
                    return fn(*args, **kwargs)
                except Exception:
                    attempts_left -= 1
                    if attempts_left <= 0:
                        raise
                    time.sleep(current_delay)
                    current_delay *= backoff
        return wrapper
    return decorator


@retry(tries=3, delay=0.5)
def fetch_data() -> dict:
    ...
```

В мире готовых библиотек этот паттерн уже реализован — `tenacity` (Python), `cenkalti/backoff` (Go).

## Аналоги декораторов в Go: middleware

В Go нет синтаксиса декораторов, но идея «обернуть функцию ещё одной функцией» прекрасно выражается явно. Самое популярное применение — middleware для HTTP-обработчиков.

```go
package main

import (
    "log"
    "net/http"
    "time"
)

type Middleware func(http.Handler) http.Handler

func Logging(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        start := time.Now()
        next.ServeHTTP(w, r)
        log.Printf("%s %s — %s", r.Method, r.URL.Path, time.Since(start))
    })
}

func Recover(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        defer func() {
            if rec := recover(); rec != nil {
                log.Printf("panic: %v", rec)
                http.Error(w, "internal error", http.StatusInternalServerError)
            }
        }()
        next.ServeHTTP(w, r)
    })
}

func chain(h http.Handler, mws ...Middleware) http.Handler {
    for i := len(mws) - 1; i >= 0; i-- {
        h = mws[i](h)
    }
    return h
}

func main() {
    mux := http.NewServeMux()
    mux.HandleFunc("/hello", func(w http.ResponseWriter, r *http.Request) {
        _, _ = w.Write([]byte("hello\n"))
    })

    handler := chain(mux, Logging, Recover)
    _ = http.ListenAndServe(":8080", handler)
}
```

Логика та же, что у декораторов Python: внешняя функция (`Logging`, `Recover`) принимает «обёрнутую» функцию и возвращает новую с дополнительным поведением. Только без сахара `@` — обёртку накладывают вызовом.

Аналогичный «retry» в Go обычно реализуют как helper-функцию или вспомогательный тип, например:

```go
import (
    "math"
    "time"
)

func Retry(tries int, delay time.Duration, fn func() error) error {
    var err error
    for i := 0; i < tries; i++ {
        if err = fn(); err == nil {
            return nil
        }
        time.Sleep(delay * time.Duration(math.Pow(2, float64(i))))
    }
    return err
}
```

---

## Контрольные вопросы

- В чём разница между `SyntaxError` и обычным исключением?
- Когда стоит использовать `try/except/else/finally`, а когда — `with`?
- Почему `except:` без указания типа — антипаттерн?
- Чем `raise ... from exc` отличается от просто `raise`?
- Для каких задач используется `assert` и почему его не стоит ставить на пользовательский ввод?
- Как в Go отличить «определённую» ошибку (`ErrNotFound`) от любой другой?
- Что такое `panic`/`recover` и когда их допустимо применять?
- Что делает декоратор без `functools.wraps` и почему это плохо?
- Как написать декоратор, который сам принимает параметры?
- Чем middleware в Go концептуально похож на декоратор в Python?
