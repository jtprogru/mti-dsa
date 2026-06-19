# Лекция 2. Строки и рекурсия

Эта лекция — о двух важных темах, которые понадобятся дальше:

- **строки** — практически в каждой задаче приходится что-то форматировать, разбирать ввод, собирать вывод;
- **рекурсия** — мощный приём для задач, где данные сами рекурсивно определены (деревья, графы, бинарный поиск).

## Строки в Python: ключевые методы

Строки в Python — **неизменяемые** (immutable). Все методы возвращают новую строку, не меняя исходную.

```python
s = "  Hello, World!  "
print(s.strip())   # "Hello, World!"
print(s)           # "  Hello, World!  " — оригинал не изменился
```

### Регистр и пробелы

| Метод | Действие | Пример |
|-------|----------|--------|
| `lower()` | в нижний регистр | `"АБВ".lower()` → `"абв"` |
| `upper()` | в верхний регистр | `"абв".upper()` → `"АБВ"` |
| `capitalize()` | первая буква заглавная | `"вася".capitalize()` → `"Вася"` |
| `title()` | каждое слово с заглавной | `"hello world".title()` → `"Hello World"` |
| `swapcase()` | поменять регистр | `"Hi".swapcase()` → `"hI"` |
| `strip([chars])` | срезать пробелы (или заданные символы) с краёв | `"  ab  ".strip()` → `"ab"` |
| `lstrip` / `rstrip` | то же, только слева/справа | |
| `center(w, fill)` | выровнять по центру | `"1".center(5, "*")` → `"**1**"` |
| `ljust` / `rjust` | выровнять влево/вправо | `"7".rjust(3, "0")` → `"007"` |
| `zfill(w)` | дополнить нулями слева | `"42".zfill(5)` → `"00042"` |

### Поиск и проверки

| Метод | Действие |
|-------|----------|
| `find(sub)` | индекс первого вхождения (или `-1`) |
| `rfind(sub)` | то же, но с конца |
| `index(sub)` | как `find`, но при отсутствии — `ValueError` |
| `count(sub)` | сколько раз встречается |
| `startswith(p)` / `endswith(p)` | начинается/заканчивается на `p` |
| `in` (оператор) | есть ли подстрока: `"abc" in s` |
| `isalpha`, `isdigit`, `isalnum`, `isspace`, `isupper`, `islower`, `isnumeric` | проверки символов |

Если нужно просто узнать, есть ли подстрока — пишите `if "abc" in s:`. `find` нужен только если важна позиция.

### Разбиение и склейка

```python
"1,2,,3,".split(",")     # ['1', '2', '', '3', '']
"hello world".split()    # ['hello', 'world'] — по пробелам
"a/b/c/d".rsplit("/", 1) # ['a/b/c', 'd'] — с конца, не более 1 раза

"-".join(["1", "2", "3"])     # "1-2-3"
"-".join(map(str, [1, 2, 3])) # "1-2-3"

"first line\nsecond\nthird".splitlines()
# ['first line', 'second', 'third']
```

### Замена

```python
"hello world".replace("world", "Python")
# "hello Python"

"a-b-c-d".replace("-", "_", 2)
# "a_b_c-d" — заменили только первые 2
```

### Кодировки

```python
"кот cat".encode()              # b'\xd0\xba\xd0\xbe\xd1\x82 cat'
"кот cat".encode("ascii")       # UnicodeEncodeError
"кот cat".encode("ascii", "ignore")   # b' cat'
"кот cat".encode("ascii", "replace")  # b'??? cat'

b"\xd0\xba\xd0\xbe\xd1\x82".decode()  # "кот"
```

В Python 3 `str` — это всегда Unicode. `bytes` — это «сырые» байты. Между ними переход — через `encode()` / `decode()`.

## Форматирование строк

Способов три, в порядке от современного к устаревшему:

1. **f-strings** (Python 3.6+) — **предпочтительно**;
2. `str.format()`;
3. `%`-форматирование.

### f-strings

```python
name = "Вася"
age = 23

print(f"{name} is {age} years old")
# Вася is 23 years old

# Выражения:
print(f"{age * 2 + 1}")  # 47

# Форматные спецификации:
pi = 3.14159265
print(f"{pi:.2f}")       # 3.14
print(f"{pi:10.2f}")     # "      3.14" (ширина 10)
print(f"{pi:<10.2f}|")   # "3.14      |"
print(f"{pi:>10.2f}|")   # "      3.14|"
print(f"{pi:^10.2f}|")   # "   3.14   |"

# Числа:
print(f"{1_234_567:,}")  # "1,234,567"
print(f"{255:08b}")      # "11111111" (бинарный, ширина 8)
print(f"{255:08x}")      # "000000ff" (hex)

# Отладочный вывод (Python 3.8+):
x = 42
print(f"{x=}")            # "x=42"
print(f"{name=}, {age=}") # "name='Вася', age=23"
```

### `str.format()`

```python
"{} {} {}".format("a", "b", "c")            # "a b c"
"{2} {0} {1}".format("a", "b", "c")         # "c a b"
"{name} = {value}".format(name="x", value=42)  # "x = 42"

# Доступ к атрибутам и индексам:
data = {"name": "Аня", "age": 30}
"{d[name]}, {d[age]}".format(d=data)  # "Аня, 30"

# Те же форматные спецификации:
"{:.2f}".format(3.14159)  # "3.14"
```

### `%`-форматирование

```python
"%s %d" % ("number", 5)   # "number 5"
"%d%%" % 100              # "100%"
```

Устарело. Встречается в логирующих библиотеках для отложенного форматирования (`logger.info("got %d items", n)`).

### Строки в Go

В Go форматирование делается пакетом `fmt`:

```go
name := "Вася"
age := 23

fmt.Printf("%s is %d years old\n", name, age)
// Вася is 23 years old

s := fmt.Sprintf("%s = %d", name, age)
// "Вася = 23"

// Числа
fmt.Printf("%.2f\n", 3.14159)  // 3.14
fmt.Printf("%08b\n", 255)      // 11111111
fmt.Printf("%08x\n", 255)      // 000000ff
```

Основные глаголы (verbs):

| Verb | Назначение |
|------|------------|
| `%v` | значение в формате по умолчанию |
| `%+v` | то же, но для структур — с именами полей |
| `%#v` | Go-синтаксис представления |
| `%s` | строка |
| `%q` | строка в кавычках |
| `%d` | целое десятичное |
| `%b`, `%o`, `%x` | двоичное, восьмеричное, шестнадцатеричное |
| `%f` | вещественное |
| `%e`, `%g` | экспоненциальное / автоматический выбор |
| `%t` | bool |
| `%T` | тип значения |

Пакет `strings` содержит аналоги методов:

```go
strings.ToLower("АБВ")              // "абв"
strings.Contains("hello", "ell")    // true
strings.HasPrefix("hello", "he")    // true
strings.Split("a,b,,c", ",")        // []string{"a", "b", "", "c"}
strings.Join([]string{"1","2"}, "-") // "1-2"
strings.Replace("a-b-c", "-", "_", 1) // "a_b-c"
strings.ReplaceAll("a-b-c", "-", "_") // "a_b_c"
strings.TrimSpace("  ab  ")         // "ab"
```

Сравнение:

| Что делаем | Python | Go |
|------------|--------|-----|
| Подстрока | `"ab" in s` | `strings.Contains(s, "ab")` |
| Разбить | `s.split(",")` | `strings.Split(s, ",")` |
| Склеить | `",".join(parts)` | `strings.Join(parts, ",")` |
| Заменить всё | `s.replace("a", "b")` | `strings.ReplaceAll(s, "a", "b")` |
| Форматирование | f-string | `fmt.Sprintf` |
| Декодировать байты | `b.decode("utf-8")` | `string(b)` (если UTF-8) |

## Рекурсия

**Рекурсивная функция** — функция, которая вызывает сама себя.

### Прямая и косвенная рекурсия

```python
def a():
    a()  # прямая рекурсия


def b():
    c()


def c():
    b()  # b и c — взаимно рекурсивные (косвенная)
```

### Когда рекурсия уместна

Рекурсия естественна там, где **данные сами рекурсивно определены**:

- деревья (DOM, AST, файловая система);
- графы (поиск в глубину);
- алгоритмы «разделяй и властвуй» (бинарный поиск, merge sort, быстрая сортировка);
- математические определения (факториал, числа Фибоначчи, разбор выражений).

Если задача имеет очевидное **итерационное** решение — обычно лучше итерация: она быстрее и не рискует переполнить стек.

### Правило хорошего тона: база рекурсии

В любой рекурсивной функции должен быть **нерекурсивный выход** (база). Иначе — бесконечная рекурсия и переполнение стека.

### Классика: факториал

=== "Python"

    ```python
    def factorial(n: int) -> int:
        if n < 0:
            raise ValueError("отрицательный аргумент")
        if n in (0, 1):       # база
            return 1
        return n * factorial(n - 1)
    ```

=== "Go"

    ```go
    func Factorial(n int) int {
        if n < 0 {
            panic("отрицательный аргумент")
        }
        if n <= 1 {
            return 1
        }
        return n * Factorial(n-1)
    }
    ```

### Подвох: числа Фибоначчи

```python
def fib(n: int) -> int:
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)
```

Работает, но **экспоненциально медленно**: `fib(40)` уже считается несколько секунд, потому что одни и те же значения пересчитываются заново миллионы раз.

Лечится мемоизацией:

```python
from functools import cache


@cache
def fib(n: int) -> int:
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)


print(fib(100))  # мгновенно
```

Или итеративной версией:

```python
def fib(n: int) -> int:
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a
```

### Бинарный (двоичный) поиск

Поиск элемента в **отсортированном** массиве.

=== "Python"

    ```python
    def binary_search(arr: list[int], target: int) -> int:
        """Вернуть индекс target или -1."""

        def search(lo: int, hi: int) -> int:
            if lo > hi:
                return -1
            mid = (lo + hi) // 2
            if arr[mid] == target:
                return mid
            if arr[mid] < target:
                return search(mid + 1, hi)
            return search(lo, mid - 1)

        return search(0, len(arr) - 1)
    ```

=== "Go"

    ```go
    func BinarySearch(arr []int, target int) int {
        var search func(lo, hi int) int
        search = func(lo, hi int) int {
            if lo > hi {
                return -1
            }
            mid := (lo + hi) / 2
            switch {
            case arr[mid] == target:
                return mid
            case arr[mid] < target:
                return search(mid+1, hi)
            default:
                return search(lo, mid-1)
            }
        }
        return search(0, len(arr)-1)
    }
    ```

В стандартной библиотеке Python для этого есть модуль `bisect`, а в Go — `sort.SearchInts`:

```python
import bisect

i = bisect.bisect_left(arr, target)
if i < len(arr) and arr[i] == target:
    ...  # нашли
```

```go
i := sort.SearchInts(arr, target)
if i < len(arr) && arr[i] == target {
    // нашли
}
```

### Обход дерева (структуры каталогов)

Рекурсивно вывести все файлы в директории:

=== "Python"

    ```python
    from pathlib import Path


    def walk(path: Path) -> None:
        for entry in path.iterdir():
            if entry.is_file():
                print(entry)
            elif entry.is_dir():
                walk(entry)


    walk(Path("."))
    ```

    А лучше — встроенный `Path.rglob` / `os.walk`:

    ```python
    for file in Path(".").rglob("*"):
        if file.is_file():
            print(file)
    ```

=== "Go"

    ```go
    import (
        "fmt"
        "io/fs"
        "path/filepath"
    )

    func main() {
        _ = filepath.WalkDir(".", func(path string, d fs.DirEntry, err error) error {
            if err != nil {
                return err
            }
            if !d.IsDir() {
                fmt.Println(path)
            }
            return nil
        })
    }
    ```

## Хвостовая рекурсия и предел стека

В Python **нет** оптимизации хвостовой рекурсии — глубина рекурсии ограничена (`sys.getrecursionlimit()`, по умолчанию 1000):

```python
import sys
sys.setrecursionlimit(10_000)  # можно повысить, но не лечит причину
```

Если рекурсия глубокая (тысячи уровней) — переписывайте на итерацию. Особенно это касается обработки данных: пройти по списку из 100 000 элементов рекурсивно — стек обвалится.

В Go ситуация лучше: горутины имеют **растущий** стек (начальный размер ~8 КБ, может расти до сотен МБ). Но хвостовой оптимизации тоже нет — рекурсия глубиной в миллион тоже сломается.

## Деревья

Изучение рекурсии тесно связано с **деревьями** — структурой данных, где у каждого узла есть набор потомков. Деревья используются как:

- модель сложных данных (XML/HTML/JSON);
- инструмент алгоритмов (деревья поиска, кучи, индексы БД);
- структуры обработки (AST в компиляторах).

Простейшее бинарное дерево:

```python
from dataclasses import dataclass


@dataclass
class Node:
    value: int
    left: "Node | None" = None
    right: "Node | None" = None


def in_order(node: Node | None) -> None:
    if node is None:
        return
    in_order(node.left)
    print(node.value)
    in_order(node.right)
```

Аналогично в Go:

```go
type Node struct {
    Value int
    Left  *Node
    Right *Node
}

func InOrder(n *Node) {
    if n == nil {
        return
    }
    InOrder(n.Left)
    fmt.Println(n.Value)
    InOrder(n.Right)
}
```

Видно: рекурсивный обход дерева — короткий и элегантный. Итеративный аналог (через явный стек) — гораздо многословнее.

---

## Контрольные вопросы

- Чем `str.find()` отличается от `str.index()`? Когда какой использовать?
- Почему строки в Python неизменяемы? Чем это удобно?
- Какие три способа форматирования строк есть в Python? Какой современный?
- Что выведет `f"{x=}"` для `x = 42`?
- Как преобразовать `bytes` в `str`, какие тут опасности?
- Что обязательно должно быть в каждой рекурсивной функции, иначе будет переполнение стека?
- Почему наивная рекурсивная `fib(n)` работает экспоненциально медленно? Как ускорить?
- В каких задачах рекурсия — естественный выбор, а в каких — лучше итерация?
- Чем поиск в `bisect` (Python) или `sort.SearchInts` (Go) лучше рукописного бинарного поиска?
- Есть ли в Python и Go оптимизация хвостовой рекурсии и что это значит на практике?
