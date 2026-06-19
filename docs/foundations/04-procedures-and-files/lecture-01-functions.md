# Лекция 1. Подпрограммы: функции и область видимости

До этого мы программировали в основном «линейно»: пишем команды одну за другой, изредка ветвимся и зацикливаемся. Это нормально для коротких скриптов, но для проектов сложнее «hello world» уже не годится — человеку очень сложно держать в голове сотни строк линейного кода.

Чтобы упростить работу, **обособленные или повторяющиеся части программы** выделяют в **подпрограммы**.

> **Подпрограмма** — функционально независимая часть программы. Структура подпрограммы такая же, как у программы в целом: у неё есть имя, входные параметры, тело и (обычно) возвращаемое значение.

Подпрограммы решают три задачи:

- избавляют от необходимости повторять одни и те же куски кода;
- улучшают структуру программы — основная функция становится похожа на «оглавление»;
- упрощают сопровождение: правишь подпрограмму один раз, а изменение видно везде, где она вызывается.

Хорошие поводы выделить код в отдельную подпрограмму:

- вы написали один и тот же кусок кода более одного раза;
- внутри логики «слишком много мелочей», заслоняющих смысл;
- алгоритм сложный и его хочется отладить и протестировать отдельно;
- этот код, скорее всего, понадобится в других программах.

В Python подпрограммы — это **функции** (`def` или `lambda`). В Go — тоже **функции** (`func`). И там и там — это объекты первого класса: их можно присваивать переменным, передавать в аргументах, возвращать из других функций.

## Функция в Python: базовый синтаксис

Определение функции начинается с ключевого слова `def`:

```python
def add(x: int, y: int) -> int:
    """Сложить два числа и вернуть результат."""
    return x + y


print(add(2, 3))    # 5
print(add("ab", "cd"))  # "abcd" — Python не проверяет типы в рантайме
```

- `def` — служебное слово.
- `add` — имя функции (snake_case по PEP 8).
- `(x: int, y: int)` — список параметров с аннотациями типов.
- `-> int` — тип возвращаемого значения.
- `"""..."""` — строка документации (docstring).
- `return` — возврат значения; если его нет, функция возвращает `None`.

Функция в Go:

```go
func Add(x, y int) int {
    return x + y
}

func main() {
    fmt.Println(Add(2, 3)) // 5
}
```

В Go типы обязательны и проверяются компилятором. Имена с заглавной буквы (`Add`) — экспортируются из пакета (видны другим пакетам), с маленькой — приватные.

## Аргументы функции

При определении функции параметры называют **формальными**. При вызове — переданные значения называются **фактическими**.

### Позиционные и именованные аргументы

=== "Python"

    ```python
    def person(name: str, age: int) -> None:
        print(f"{name} is {age} years old")


    person("John", 23)                    # позиционно
    person(name="John", age=23)           # по имени
    person(age=23, name="John")           # порядок неважен при именах
    ```

=== "Go"

    ```go
    func Person(name string, age int) {
        fmt.Printf("%s is %d years old\n", name, age)
    }

    func main() {
        Person("John", 23) // в Go только позиционно
    }
    ```

В Go именованных параметров **нет**. Если их хочется — заводят структуру:

```go
type PersonOpts struct {
    Name string
    Age  int
}

func Person(opts PersonOpts) {
    fmt.Printf("%s is %d years old\n", opts.Name, opts.Age)
}

Person(PersonOpts{Name: "John", Age: 23})
```

### Значения по умолчанию

В Python:

```python
def space(planet_name: str, center: str = "Star") -> None:
    print(f"{planet_name} is orbiting a {center}")


space("Mars")                # Mars is orbiting a Star
space("Mars", "Black Hole")  # Mars is orbiting a Black Hole
```

В Go значений по умолчанию **нет**. Эмулируют либо перегрузкой через переменное число аргументов, либо через структуру опций (паттерн **functional options**):

```go
type SpaceOption func(*spaceConfig)

type spaceConfig struct {
    center string
}

func WithCenter(c string) SpaceOption {
    return func(cfg *spaceConfig) { cfg.center = c }
}

func Space(planet string, opts ...SpaceOption) {
    cfg := spaceConfig{center: "Star"}
    for _, opt := range opts {
        opt(&cfg)
    }
    fmt.Printf("%s is orbiting a %s\n", planet, cfg.center)
}

Space("Mars")
Space("Mars", WithCenter("Black Hole"))
```

### Переменное число аргументов

=== "Python"

    ```python
    def func(*args: int, **kwargs: str) -> None:
        print("args:", args)
        print("kwargs:", kwargs)


    func(1, 2, 3, a="x", b="y")
    # args: (1, 2, 3)
    # kwargs: {'a': 'x', 'b': 'y'}
    ```

=== "Go"

    ```go
    func Sum(values ...int) int {
        total := 0
        for _, v := range values {
            total += v
        }
        return total
    }

    Sum()          // 0
    Sum(1, 2, 3)   // 6
    Sum([]int{1, 2, 3}...) // развернуть слайс
    ```

В Python `*args` — кортеж позиционных, `**kwargs` — словарь именованных. В Go вариативный параметр всегда последний, и внутри функции это обычный slice.

### Опасная ловушка: изменяемый default

```python
# ПЛОХО — список-default создаётся один раз на функцию,
# а не при каждом вызове
def append_to(value, lst=[]):
    lst.append(value)
    return lst


print(append_to(1))  # [1]
print(append_to(2))  # [1, 2]  ← неожиданно!
```

Правильно:

```python
def append_to(value, lst=None):
    if lst is None:
        lst = []
    lst.append(value)
    return lst
```

В Go проблемы нет — значения по умолчанию не поддерживаются.

## Аннотации типов

В Python со версии 3.5 можно записывать типы аргументов и возвращаемых значений:

```python
from collections.abc import Iterable


def stats(values: Iterable[float]) -> tuple[float, float]:
    """Среднее и медиана списка чисел."""
    items = sorted(values)
    n = len(items)
    mean = sum(items) / n
    median = items[n // 2] if n % 2 else (items[n // 2 - 1] + items[n // 2]) / 2
    return mean, median
```

**Что важно:** Python в рантайме типы **не проверяет**. Они нужны для:

- читаемости кода (IDE/ревьюеру сразу понятно, что ожидается);
- автокомплита и подсказок в редакторе;
- статической проверки утилитами `mypy`, `pyright`, `ruff`.

Хороший стиль для современного Python (3.10+):

- встроенные типы вместо `typing.List` и `typing.Dict`: `list[int]`, `dict[str, int]`;
- союзы через `|`: `int | None` вместо `Optional[int]`;
- `from collections.abc import Iterable, Mapping, Sequence` для абстракций.

В Go типы — часть синтаксиса. Альтернативного «опционального» режима нет.

## Документирование (docstrings)

PEP 257 рекомендует:

- для каждой публичной функции — docstring;
- начинается с краткого предложения в повелительном наклонении;
- грамотный язык, законченные предложения.

```python
def k_nearest_neighbors(dataframe: pd.DataFrame, k: int = 5) -> pd.DataFrame:
    """Найти k ближайших соседей для каждой строки.

    Возвращает DataFrame, где для каждой исходной строки добавлены
    индексы её k ближайших соседей по евклидовой метрике.

    Args:
        dataframe: исходный набор данных.
        k: количество соседей. По умолчанию 5.

    Returns:
        Расширенный DataFrame.
    """
```

В Go комментарий в виде `// FunctionName ...` сразу над функцией становится её документацией (см. `go doc` и `pkg.go.dev`):

```go
// Sum returns the sum of integer values.
// Returns 0 when no arguments are passed.
func Sum(values ...int) int {
    ...
}
```

## Область видимости (scope)

Каждое имя — переменная, функция, импорт — существует в какой-то **области видимости**. Если обратиться к имени вне его области, будет ошибка (`NameError` в Python, ошибка компиляции в Go).

### Python: LEGB

В Python работает правило поиска имён **LEGB**:

1. **L**ocal — внутри текущей функции;
2. **E**nclosing — внутри охватывающих функций (для замыканий);
3. **G**lobal — на уровне модуля;
4. **B**uilt-in — встроенные имена (`print`, `len`, ...).

```python
name = "Tom"             # глобально


def say_hi() -> None:
    print("Hello", name)  # читает глобальную


def say_bye() -> None:
    name = "Bob"          # локальная, скрывает глобальную
    print("Good bye", name)


say_hi()   # Hello Tom
say_bye()  # Good bye Bob
print(name)  # Tom — глобальная не изменилась
```

### `global` и `nonlocal`

Если внутри функции нужно **изменить** глобальную переменную (а не создать локальную), её помечают `global`:

```python
counter = 0


def inc() -> None:
    global counter
    counter += 1
```

Для замыкания (изменения переменной из охватывающей функции, не глобальной) — `nonlocal`:

```python
def make_counter():
    count = 0

    def inc() -> int:
        nonlocal count
        count += 1
        return count

    return inc


c = make_counter()
print(c())  # 1
print(c())  # 2
```

### Неочевидный момент

```python
x = 10


def foo():
    print(x)   # UnboundLocalError!
    x += 1
```

Python видит `x += 1` — присваивание внутри функции, значит `x` считается локальной *на всём протяжении функции*. К моменту `print(x)` локальная ещё не определена. Лечится `global x` или `nonlocal x`.

### Глобальные переменные — это плохо

Глобальные переменные:

- усложняют тестирование (тесты влияют друг на друга);
- затрудняют рефакторинг (любая функция может что-то изменить);
- ломают многопоточность (race conditions).

Допустимо хранить в глобальной области только **константы**:

```python
PI = 3.14159
MAX_RETRIES = 5
```

Общее состояние модулей лучше держать в отдельном `config.py` и обращаться через `config.x`.

### Scope в Go

Go проще: scope определяется **блоком** `{ ... }`. Внутри блока видны все имена, объявленные раньше; вне блока — нет.

```go
package main

import "fmt"

var counter = 0 // package-level (≈ глобальная)

func inc() {
    counter++ // прямо работает
}

func main() {
    x := 10
    if x > 5 {
        y := 20      // видна только в if
        fmt.Println(x, y)
    }
    // fmt.Println(y) // ошибка компиляции: y undefined
}
```

Имена с заглавной буквы экспортируются из пакета, с маленькой — приватные.

## Анонимные функции и замыкания

### Python: `lambda`

`lambda` — однострочная анонимная функция. Полезна там, где нужна короткая функция-аргумент:

```python
add = lambda x, y: x + y
print(add(2, 3))  # 5

# Типичный сценарий: ключ сортировки
people = [("Аня", 30), ("Боря", 25)]
people.sort(key=lambda p: p[1])
```

Ограничения: только одно выражение, без statement'ов. Для всего сложнее — обычный `def`.

### Замыкания

```python
def adder(n: int):
    def add(x: int) -> int:
        return x + n
    return add


inc = adder(1)
add5 = adder(5)
print(inc(10))   # 11
print(add5(10))  # 15
```

`add` «помнит» внешнее `n` после возврата `adder` — это и есть замыкание.

### Go: анонимные функции

```go
add := func(x, y int) int { return x + y }
fmt.Println(add(2, 3)) // 5

// Замыкание
adder := func(n int) func(int) int {
    return func(x int) int { return x + n }
}

inc := adder(1)
fmt.Println(inc(10)) // 11
```

В Go анонимная функция — обычное выражение, можно сразу вызвать:

```go
result := func(x int) int { return x * 2 }(21)
fmt.Println(result) // 42
```

## Передача по ссылке или по значению

В C/Pascal параметры по умолчанию передаются **по значению** — создаётся копия. Если нужно изменить переменную вызывающего — передают указатель (по ссылке).

### Python: всё передаётся по ссылке на объект

Точнее — всё передаётся **по значению ссылки на объект**. Поведение зависит от **изменяемости объекта**:

- **неизменяемые** (`int`, `float`, `str`, `tuple`, `frozenset`) — внутри функции «выглядят» как переданные по значению; присваивание создаёт новый объект;
- **изменяемые** (`list`, `dict`, `set`) — функция видит тот же объект и может его изменить.

```python
def append_value(items: list[int]) -> None:
    items.append(99)


a = [1, 2, 3]
append_value(a)
print(a)  # [1, 2, 3, 99]  ← внешний список изменился
```

Лечится копией:

```python
new_items = items[:]            # копия списка
new_items = list(items)         # тоже копия
new_items = items.copy()        # тоже
import copy
new_items = copy.deepcopy(items)  # глубокая копия
```

### Go: всё передаётся по значению

В Go аргументы всегда копируются. Если нужно изменить переменную вызывающего — передают **указатель**:

```go
func increment(x int) {
    x++ // ничего не меняет снаружи
}

func incrementPtr(x *int) {
    *x++
}

n := 1
increment(n)
fmt.Println(n) // 1

incrementPtr(&n)
fmt.Println(n) // 2
```

Слайсы, мапы и каналы в Go — типы со ссылочной семантикой: копируется «дескриптор», но содержимое разделяется:

```go
func appendValue(items []int) {
    items = append(items, 99)  // ВНИМАНИЕ: может создать новый слайс
}

func mutateFirst(items []int) {
    items[0] = 99  // меняет элемент исходного массива
}
```

## Несколько возвращаемых значений

В Python — кортеж:

```python
def divmod_(a: int, b: int) -> tuple[int, int]:
    return a // b, a % b


q, r = divmod_(10, 3)
```

В Go — нативная поддержка multiple return, и это **идиоматический** способ возвращать ошибки:

```go
func DivMod(a, b int) (int, int) {
    return a / b, a % b
}

func ParseConfig(path string) (Config, error) {
    ...
}

cfg, err := ParseConfig("config.toml")
if err != nil {
    return err
}
```

## Что делает функцию «хорошей»

«Хорошая» функция (компиляция рекомендаций Боба Мартина и community):

- **внятно названа** — снаружи понятно, что делает;
- **одна ответственность** — делает одно дело;
- **возвращает значение** — даже `True/False` лучше, чем `None`;
- **короткая** — около 50 строк максимум;
- **идемпотентная** — при одинаковых аргументах возвращает одинаковый результат;
- **чистая** (если возможно) — без побочных эффектов.

### Один принцип ответственности

```python
# ПЛОХО — функция делает два дела
def calculate_and_print_stats(values: list[float]) -> None:
    total = sum(values)
    mean = statistics.mean(values)
    median = statistics.median(values)
    print(f"SUM:    {total}")
    print(f"MEAN:   {mean}")
    print(f"MEDIAN: {median}")


# ХОРОШО — отделили вычисление от вывода
def stats(values: list[float]) -> dict[str, float]:
    return {
        "sum": sum(values),
        "mean": statistics.mean(values),
        "median": statistics.median(values),
    }


def print_stats(values: dict[str, float]) -> None:
    for key, value in values.items():
        print(f"{key.upper():<8} {value}")
```

Слово «and» в имени функции — почти всегда признак нарушения SRP.

### Идемпотентность и чистота

```python
# Чистая функция — нет побочных эффектов, только вход/выход
def add_three(n: int) -> int:
    return n + 3


# Идемпотентная, но не чистая — есть побочный эффект (print)
def add_three_log(n: int) -> int:
    print(f"adding 3 to {n}")
    return n + 3


# Не идемпотентная — зависит от ввода/состояния
def add_three_input() -> int:
    return int(input("число: ")) + 3
```

Чем больше функций чистые/идемпотентные — тем проще их тестировать (никаких моков, никакой подготовки окружения).

## Сравнение Python ↔ Go

| Аспект | Python | Go |
|--------|--------|-----|
| Объявление | `def name(...) -> Type:` | `func Name(...) Type` |
| Анонимные | `lambda x: x` (однострочная) | `func(x int) int { return x }` |
| Default-параметры | да | нет (используют functional options) |
| `*args` / `**kwargs` | да | `variadic ...T`, именованных нет |
| Несколько возвращаемых | через tuple | нативно |
| Идиома ошибок | исключения | `(value, error)` |
| Аннотации типов | опциональны (`mypy`/`pyright`) | обязательны |
| Глобальное состояние | можно, но не нужно | пакет-уровень доступен в пакете |
| Замыкания | поддерживаются | поддерживаются |

---

## Контрольные вопросы

- Чем формальные параметры отличаются от фактических?
- Что такое `*args` и `**kwargs` в Python и какие у Go аналоги?
- Почему изменяемый default-аргумент (`def f(x=[]):`) — это ловушка?
- В чём разница между ключевыми словами `global` и `nonlocal`?
- Почему `print(x); x += 1` внутри функции с глобальной `x` приводит к `UnboundLocalError`?
- В Python всё передаётся «по ссылке» или «по значению»? Почему ответ — «зависит»?
- Как в Go реализовать functional options и зачем это нужно?
- Что такое идемпотентная и чистая функция? Чем чистая отличается от идемпотентной?
- Какие признаки нарушения принципа единственной ответственности у функции?
- Что произойдёт, если функция в Go не вернёт значение, объявленное в её сигнатуре?
