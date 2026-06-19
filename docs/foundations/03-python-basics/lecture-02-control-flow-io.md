# Лекция 2. Управляющие конструкции и ввод-вывод

В этой лекции — три классических темы:

- **условия** (`if`/`elif`/`else`);
- **циклы** (`while`, `for`) — с особенностями Python и Go;
- **ввод-вывод** — простейший консольный ввод и форматированный вывод.

## Условные конструкции

### Python: `if` / `elif` / `else`

```python
n = int(input("Введите число: "))

if n > 0:
    print("положительное")
elif n < 0:
    print("отрицательное")
else:
    print("ноль")
```

Условие — любое выражение, которое будет приведено к bool. Скобки вокруг условия **не нужны** (в Go тоже):

```python
if x > 0 and x < 100:
    ...
```

### Однострочная форма

```python
if x > 0: print(x)   # допустимо, но плохой стиль
```

PEP 8 не рекомендует — лучше развёрнутая запись.

### Тернарный оператор

```python
status = "положительное" if x > 0 else "не положительное"
```

В Go тернарного оператора **нет** — пишут полный `if`:

```go
status := "не положительное"
if x > 0 {
    status = "положительное"
}
```

### `match` (Python 3.10+)

Structural pattern matching — мощнее обычного `switch`:

```python
def describe(point: tuple) -> str:
    match point:
        case (0, 0):
            return "Origin"
        case (x, 0):
            return f"X-axis at {x}"
        case (0, y):
            return f"Y-axis at {y}"
        case (x, y):
            return f"Point at ({x}, {y})"
        case _:
            return "Not a point"
```

### Go: `if` и `switch`

```go
if n > 0 {
    fmt.Println("положительное")
} else if n < 0 {
    fmt.Println("отрицательное")
} else {
    fmt.Println("ноль")
}
```

Особенность Go — **инициализация** прямо в `if`:

```go
if err := doSomething(); err != nil {
    return err
}
// err недоступна здесь — её scope только if
```

Это идиоматический Go-паттерн для проверки ошибок.

`switch` без `break` после каждого `case`:

```go
switch n {
case 0:
    fmt.Println("ноль")
case 1, 2, 3:
    fmt.Println("малое число")
default:
    fmt.Println("большое число")
}
```

Можно использовать как полноценную замену длинной цепочки `if/elif`:

```go
switch {
case n > 100:
    fmt.Println("большое")
case n > 10:
    fmt.Println("среднее")
default:
    fmt.Println("малое")
}
```

## Циклы

### Цикл `while` (только Python)

```python
i = 5
while i < 15:
    print(i)
    i += 2
```

Программист сам управляет условием. Применяется, когда количество итераций заранее не известно (например, чтение до EOF, ожидание события).

В Go отдельного `while` нет — используют `for`:

```go
i := 5
for i < 15 {
    fmt.Println(i)
    i += 2
}
```

И «бесконечный цикл»:

```go
for {
    // ...
    if condition {
        break
    }
}
```

### Цикл `for` в Python

В Python `for` — это **перебор элементов итерируемого объекта**, а не цикл со счётчиком как в C/Pascal/Go:

```python
for char in "hello":
    print(char, end=" ")
# h e l l o

for item in [10, 20, 30]:
    print(item)

for key in {"name": "Аня", "age": 30}:
    print(key)
```

Если нужны и индекс, и элемент — `enumerate`:

```python
for i, char in enumerate("abc"):
    print(i, char)
# 0 a
# 1 b
# 2 c
```

Если нужно перебирать **два списка одновременно** — `zip`:

```python
names = ["Аня", "Боря"]
ages = [25, 30]

for name, age in zip(names, ages):
    print(name, age)
```

### Функция `range`

Для цикла со счётчиком (как в C/Pascal) используется `range`:

```python
range(5)             # 0, 1, 2, 3, 4
range(1, 5)          # 1, 2, 3, 4
range(2, 10, 2)      # 2, 4, 6, 8
range(5, 0, -1)      # 5, 4, 3, 2, 1
```

`range` возвращает специальный итерируемый объект, **не список**. Это эффективно по памяти — числа генерируются по одному:

```python
type(range(100))   # <class 'range'>
list(range(5))     # [0, 1, 2, 3, 4] — если нужен список
```

Типичные шаблоны:

```python
# 5 раз сделать что-то
for _ in range(5):
    print("hello")

# Обойти список с индексами
for i in range(len(items)):
    items[i] *= 2

# Лучше: используйте enumerate
for i, x in enumerate(items):
    items[i] = x * 2
```

### Цикл `for` в Go

В Go `for` — единственный цикл, у него три формы:

**1. Классический C-style:**

```go
for i := 0; i < 10; i++ {
    fmt.Println(i)
}
```

**2. while-style:**

```go
for i < 10 {
    i++
}
```

**3. Бесконечный:**

```go
for {
    // нужно break
}
```

**Перебор коллекций — `range`:**

```go
nums := []int{10, 20, 30}

for i, v := range nums {
    fmt.Println(i, v)
}

// Только индекс
for i := range nums {
    fmt.Println(i)
}

// Только значение (индекс игнорируем)
for _, v := range nums {
    fmt.Println(v)
}

// Перебор map
m := map[string]int{"a": 1, "b": 2}
for k, v := range m {
    fmt.Println(k, v)
}
```

`range` по строке выдаёт **руны** (Unicode code points), а не байты — про это в [лекции 4](lecture-04-encodings-bytes.md).

### `break` и `continue`

В обоих языках одинаково:

- `break` — досрочно прервать цикл;
- `continue` — пропустить остаток тела и начать следующую итерацию.

```python
for i in "hello world":
    if i == "o":
        continue        # пропускаем 'o'
    if i == "l" and ...:
        break          # выйти полностью
    print(i, end="")
```

В Go дополнительно есть **метки** для break/continue из вложенных циклов:

```go
outer:
for i := 0; i < 5; i++ {
    for j := 0; j < 5; j++ {
        if i*j > 6 {
            break outer  // выйти из внешнего цикла
        }
    }
}
```

### Цикл `else` в Python

Особенность Python: у `for` и `while` может быть `else`, который выполняется, если цикл закончился **естественным образом** (без `break`):

```python
for i in "hello world":
    if i == "a":
        print("найдена буква 'a'")
        break
else:
    print("буквы 'a' нет")
# Выведет: буквы 'a' нет
```

Это пригодится в задачах поиска: «нашли или дошли до конца, не найдя».

В Go аналога нет — пишут флаг:

```go
found := false
for _, ch := range "hello world" {
    if ch == 'a' {
        found = true
        break
    }
}
if !found {
    fmt.Println("буквы 'a' нет")
}
```

### Вложенные циклы

Классический пример — таблица умножения:

=== "Python"

    ```python
    for i in range(1, 10):
        for j in range(1, 10):
            print(f"{i*j:4d}", end="")
        print()
    ```

=== "Go"

    ```go
    for i := 1; i < 10; i++ {
        for j := 1; j < 10; j++ {
            fmt.Printf("%4d", i*j)
        }
        fmt.Println()
    }
    ```

## Случайные числа

Часто нужны для тестов и игровой логики.

=== "Python"

    ```python
    import random

    random.randint(1, 100)        # целое 1..100 (включительно)
    random.random()               # float [0, 1)
    random.uniform(0.0, 5.0)      # float [0, 5]
    random.choice(["a", "b", "c"]) # случайный элемент
    random.shuffle(my_list)        # перемешать на месте

    # Воспроизводимость — фиксируем seed
    random.seed(42)
    ```

=== "Go"

    ```go
    import (
        "math/rand"
        "time"
    )

    func main() {
        // С Go 1.20+ глобальный rand автоматически seeded
        n := rand.Intn(100)           // 0..99
        f := rand.Float64()           // [0, 1)

        // Свой источник со своим seed (детерминированно)
        r := rand.New(rand.NewSource(42))
        r.Intn(100)

        // С Go 1.20+ также есть math/rand/v2 — новый API
    }
    ```

> Для криптографии используйте `secrets` в Python и `crypto/rand` в Go — `random`/`math/rand` **не** криптографически стойкие.

## Ввод-вывод: основы

### Вывод: `print()`

```python
print(42)
print(2.5, "Hello", [1, 2])    # несколько аргументов — через пробел
```

Параметры:

- `sep` — разделитель между аргументами (по умолчанию пробел);
- `end` — что добавить в конец (по умолчанию `\n`);
- `file` — куда выводить (по умолчанию `sys.stdout`);
- `flush` — принудительно сбросить буфер.

```python
print("a", "b", "c", sep="-")      # a-b-c
print("без перевода", end="")
print("дополнительный отступ", end="\n\n")

import sys
print("в stderr", file=sys.stderr)

# Запись в файл
with open("out.txt", "w") as f:
    print("в файл", file=f)
```

### Форматирование вывода

Подробно про форматирование строк — в [лекции 2 темы 4](../04-procedures-and-files/lecture-02-strings-recursion.md). Краткое напоминание:

```python
name = "Аня"
age = 30
pi = 3.14159

# f-strings — современный способ
print(f"{name} is {age}")
print(f"{pi:.2f}")           # 3.14
print(f"{pi:10.2f}")         # "      3.14"
print(f"{42:08b}")           # "00101010" — двоичный
print(f"{name=}")            # name='Аня' — отладочный

# str.format()
print("{} is {}".format(name, age))
print("{0} {1} {0}".format("a", "b"))   # a b a

# %-форматирование (старое, в логгерах)
print("%s is %d" % (name, age))
```

### Вывод в Go

`fmt`-пакет:

```go
fmt.Println("a", "b", "c")        // вывод с пробелами + \n
fmt.Print("без \\n")
fmt.Printf("%s is %d\n", name, age)

// В строку
s := fmt.Sprintf("%s = %.2f", name, pi)

// В stderr
fmt.Fprintln(os.Stderr, "ошибка")

// В файл
f, _ := os.Create("out.txt")
defer f.Close()
fmt.Fprintln(f, "в файл")
```

Основные verb'ы:

| Verb | Что выводит |
|------|-------------|
| `%v` | значение по умолчанию |
| `%+v` | то же, для структур — с именами полей |
| `%#v` | Go-литерал |
| `%T` | тип значения |
| `%s` | строка |
| `%q` | строка в кавычках |
| `%d` | int (десятичный) |
| `%b`, `%o`, `%x`, `%X` | int в других системах |
| `%f`, `%e`, `%g` | float |
| `%t` | bool |
| `%p` | указатель |

### Ввод: `input()`

```python
name = input("Ваше имя: ")   # выводит подсказку, ждёт ввод, возвращает строку
print(f"Привет, {name}!")
```

Главное правило: `input()` **всегда** возвращает строку. Если нужно число:

```python
age = int(input("Возраст: "))      # с возможностью ValueError
price = float(input("Цена: "))
```

С обработкой ошибок:

```python
try:
    n = int(input("Введите число: "))
except ValueError:
    print("это не число")
    n = 0
```

### Ввод в Go

`fmt.Scan`, `fmt.Scanln`, `fmt.Scanf`:

```go
var name string
fmt.Print("Имя: ")
fmt.Scanln(&name)

var age int
fmt.Print("Возраст: ")
_, err := fmt.Scanln(&age)
if err != nil {
    fmt.Println("это не число")
}
```

Для многострочного ввода — `bufio.Scanner`:

```go
scanner := bufio.NewScanner(os.Stdin)
for scanner.Scan() {
    line := scanner.Text()
    fmt.Println("got:", line)
}
```

## Стандартные потоки

Программа работает с тремя потоками:

| Поток | Python | Go |
|-------|--------|-----|
| Стандартный ввод (stdin) | `sys.stdin` | `os.Stdin` |
| Стандартный вывод (stdout) | `sys.stdout` | `os.Stdout` |
| Стандартный вывод ошибок (stderr) | `sys.stderr` | `os.Stderr` |

В Python:

```python
import sys

text = sys.stdin.read()       # аналог input(), всё сразу
for line in sys.stdin:        # построчно (до Ctrl+D)
    print(line.strip())

print("error!", file=sys.stderr)
```

В Go:

```go
import (
    "bufio"
    "fmt"
    "io"
    "os"
)

func main() {
    data, _ := io.ReadAll(os.Stdin)  // весь stdin
    fmt.Println(string(data))

    scanner := bufio.NewScanner(os.Stdin)
    for scanner.Scan() {
        fmt.Println(scanner.Text())
    }

    fmt.Fprintln(os.Stderr, "error!")
}
```

## Пример: интерактивный калькулятор

Решает простейшую задачу со скидкой:

=== "Python"

    ```python
    qty = int(input("Сколько апельсинов? "))
    price = float(input("Цена одного апельсина: "))

    total = qty * price
    if qty >= 10:
        total *= 0.9    # скидка 10%
        print(f"Скидка 10%! Итого: {total:.2f} руб")
    else:
        print(f"Итого: {total:.2f} руб")
    ```

=== "Go"

    ```go
    package main

    import "fmt"

    func main() {
        var qty int
        var price float64

        fmt.Print("Сколько апельсинов? ")
        fmt.Scanln(&qty)

        fmt.Print("Цена одного апельсина: ")
        fmt.Scanln(&price)

        total := float64(qty) * price
        if qty >= 10 {
            total *= 0.9
            fmt.Printf("Скидка 10%%! Итого: %.2f руб\n", total)
        } else {
            fmt.Printf("Итого: %.2f руб\n", total)
        }
    }
    ```

## Сравнение Python ↔ Go: управляющие конструкции

| Аспект | Python | Go |
|--------|--------|-----|
| `if` | `if cond:` + отступ | `if cond { ... }` |
| Тернарный | `a if cond else b` | нет |
| Инициализация в `if` | walrus `:=` | `if x := f(); x > 0 { ... }` |
| `switch` | `match` (3.10+) | `switch` (часто без break) |
| `while` | есть | нет (через `for cond`) |
| `for` | по итерируемому | три формы: C-style, while-style, range |
| Цикл со счётчиком | `for i in range(n)` | `for i := 0; i < n; i++` |
| Цикл `else` | есть | нет |
| Метки break/continue | нет | есть |
| Случайные числа | `random` | `math/rand` (или v2) |
| Stdin построчно | `for line in sys.stdin` | `bufio.NewScanner(os.Stdin)` |

---

## Контрольные вопросы

- Чем `for` в Python отличается от `for` в C/Pascal/Go? Почему так сделано?
- Что такое `range` и почему `range(1_000_000)` не «расходует» миллион ячеек памяти?
- Когда применять `for ... else`, а когда — флаг?
- Что выведет `print("a", "b", "c", sep="-", end="!")`?
- Почему `input()` всегда возвращает строку, и как получить число?
- Чем `if err := doSomething(); err != nil` лучше отдельного `err := doSomething(); if err != nil` в Go?
- Что вернёт `random.randint(1, 100)` — может ли это быть 100?
- Чем `math/rand` отличается от `crypto/rand` в Go?
- Почему в Go нет тернарного оператора (`a ? b : c`), и как это компенсируется?
- Что делает `enumerate(items)` и в чём преимущество перед `range(len(items))`?
