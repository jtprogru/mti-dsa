# Лекция 3. Коллекции: списки, кортежи, словари, множества

В этой лекции — четыре главных «контейнерных» типа Python и их аналоги в Go: списки (`list`), кортежи (`tuple`), словари (`dict`) и множества (`set`).

## Обзор

| Тип Python | Изменяемость | Упорядоченность | Литерал | Аналог в Go |
|------------|--------------|------------------|---------|-------------|
| `list` | изменяемый | упорядоченный | `[1, 2, 3]` | slice (`[]int`) |
| `tuple` | неизменяемый | упорядоченный | `(1, 2, 3)` | array (фикс. размер) или struct |
| `dict` | изменяемый | упорядоченный (с 3.7) | `{"k": "v"}` | map (`map[string]int`) |
| `set` | изменяемый | неупорядоченный | `{1, 2}` | `map[T]struct{}` (идиома) |
| `frozenset` | неизменяемый | неупорядоченный | `frozenset({1, 2})` | — |

## Списки (`list`)

Список — **изменяемая упорядоченная** коллекция произвольных объектов. По сути — динамический массив.

### Создание

```python
# Литерал
empty = []
nums = [1, 2, 3]
mixed = [1, "two", [3, 4], None]

# Через функцию list()
chars = list("hello")        # ['h', 'e', 'l', 'l', 'o']
nums = list(range(5))        # [0, 1, 2, 3, 4]
```

### Генераторы списков (list comprehensions)

Декларативный способ построить список:

```python
# квадраты чисел
squares = [x * x for x in range(10)]

# С фильтрацией
evens = [x for x in range(20) if x % 2 == 0]

# С преобразованием
words = ["hello", "world"]
shouts = [w.upper() + "!" for w in words]

# Вложенный (декартово произведение)
pairs = [(x, y) for x in range(3) for y in range(3)]

# Двумерная матрица
matrix = [[0] * 5 for _ in range(3)]   # 3×5 нулей
```

В Go генераторов нет — пишут циклы:

```go
squares := make([]int, 0, 10)
for x := 0; x < 10; x++ {
    squares = append(squares, x*x)
}
```

### Индексация и срезы

```python
nums = [10, 20, 30, 40, 50]

nums[0]         # 10 — первый
nums[-1]        # 50 — последний
nums[1:3]       # [20, 30] — срез
nums[:3]        # [10, 20, 30] — начало
nums[2:]        # [30, 40, 50] — хвост
nums[::2]       # [10, 30, 50] — с шагом 2
nums[::-1]      # [50, 40, 30, 20, 10] — реверс
```

Срез возвращает **новый список** (копию).

В Go slice'ы тоже поддерживают срезы, но возвращают **окно** в тот же массив (не копию):

```go
nums := []int{10, 20, 30, 40, 50}

a := nums[1:3]      // []int{20, 30}
a[0] = 999          // nums[1] == 999 — изменили оригинал!
```

Чтобы получить независимую копию в Go — нужен `copy` или `append`:

```go
a := append([]int{}, nums[1:3]...)
// или
b := slices.Clone(nums[1:3])  // Go 1.21+
```

### Методы списка

```python
nums = [1, 2, 3]

nums.append(4)              # [1, 2, 3, 4]
nums.extend([5, 6])         # [1, 2, 3, 4, 5, 6]
nums.insert(0, 0)           # [0, 1, 2, 3, 4, 5, 6]
nums.remove(3)              # [0, 1, 2, 4, 5, 6]  — удалить первое значение
val = nums.pop()            # val=6, nums=[0, 1, 2, 4, 5]
val = nums.pop(0)           # val=0, nums=[1, 2, 4, 5]
nums.index(4)               # 2 — позиция значения
nums.count(2)               # 1 — сколько раз встречается
nums.reverse()              # перевернуть на месте
nums.sort()                 # отсортировать на месте
nums.sort(reverse=True)     # по убыванию
copy = nums.copy()          # копия (можно и nums[:])
nums.clear()                # очистить
```

Сортировка с ключом:

```python
words = ["abc", "a", "ab"]
words.sort(key=len)         # по длине: ['a', 'ab', 'abc']
words.sort(key=str.lower)   # case-insensitive

# Функция sorted() возвращает НОВЫЙ список, не меняя оригинал
result = sorted(words, key=len)
```

В Go:

```go
import "slices"   // Go 1.21+

s := []int{3, 1, 2}
slices.Sort(s)              // [1, 2, 3]
slices.SortFunc(s, func(a, b int) int { return b - a })  // по убыванию

words := []string{"abc", "a", "ab"}
slices.SortFunc(words, func(a, b string) int { return len(a) - len(b) })
```

### Изменяющие vs возвращающие методы

Важно отличать:

- **Меняют список** (возвращают `None`): `sort`, `reverse`, `append`, `extend`, `insert`, `remove`, `clear`.
- **Возвращают новый объект**: `sorted()`, `reversed()`, срезы.

```python
nums = [3, 1, 2]

# Плохо — забыли, что sort() меняет на месте
result = nums.sort()        # result is None!

# Правильно
nums.sort()                 # nums = [1, 2, 3]
# или
result = sorted(nums)       # новый список
```

## Кортежи (`tuple`)

Кортеж — **неизменяемая упорядоченная** коллекция.

### Зачем нужны кортежи

- защита от случайного изменения;
- меньше памяти, чем у списка;
- быстрее при итерации;
- можно использовать как **ключ словаря** или элемент **множества** (списки нельзя — они не хэшируемы).

### Создание

```python
empty = ()
one = (42,)                  # запятая обязательна!
without_parens = 1, 2, 3     # тоже кортеж
nums = (1, 2, 3)

# Из итерируемого
chars = tuple("hi")          # ('h', 'i')
```

> `(42)` — это **не** кортеж, а просто число `42` в скобках. Чтобы получить кортеж из одного элемента, нужна запятая: `(42,)`.

### Распаковка (unpacking)

Самая частая операция с кортежами — распаковка:

```python
point = (1.5, 2.5)
x, y = point

# Возврат нескольких значений из функции — это кортеж
def minmax(values):
    return min(values), max(values)

low, high = minmax([3, 1, 4, 1, 5])

# Расширенная распаковка
first, *rest = [1, 2, 3, 4]      # first=1, rest=[2, 3, 4]
first, *middle, last = [1, 2, 3, 4, 5]  # first=1, middle=[2, 3, 4], last=5
```

В Go кортежей нет, но multiple return — есть:

```go
func minmax(values []int) (int, int) {
    return slices.Min(values), slices.Max(values)
}

low, high := minmax([]int{3, 1, 4, 1, 5})
```

Для именованного кортежа в Python используют `dataclass` или `NamedTuple`:

```python
from typing import NamedTuple

class Point(NamedTuple):
    x: float
    y: float

p = Point(1.5, 2.5)
print(p.x, p.y)
print(p[0], p[1])    # ещё и по индексу работает

# Эквивалент через collections.namedtuple
from collections import namedtuple
Point2 = namedtuple("Point2", "x y")
```

В Go аналог — `struct`:

```go
type Point struct {
    X, Y float64
}

p := Point{X: 1.5, Y: 2.5}
fmt.Println(p.X, p.Y)
```

## Словари (`dict`)

Словарь — **изменяемая** коллекция пар «ключ → значение» с быстрым доступом по ключу (хэш-таблица).

### Создание

```python
empty = {}
colors = {"red": "красный", "green": "зелёный"}

# Через функцию
colors = dict(red="красный", green="зелёный")
colors = dict([("red", "красный"), ("green", "зелёный")])

# fromkeys — все ключи с одним значением
nums = dict.fromkeys(["a", "b", "c"], 0)   # {"a": 0, "b": 0, "c": 0}

# Словарь-генератор (comprehension)
squares = {n: n * n for n in range(5)}     # {0:0, 1:1, 2:4, 3:9, 4:16}
```

С Python 3.7 порядок ключей в словаре **гарантированно** соответствует порядку вставки.

### Доступ и изменение

```python
colors = {"red": "красный", "green": "зелёный"}

colors["red"]               # "красный"
colors["blue"]              # KeyError!
colors["blue"] = "синий"    # добавление
colors["red"] = "ярко-красный"  # перезапись

# Безопасный доступ — get()
colors.get("blue")           # None если нет
colors.get("blue", "?")      # "?" если нет

# Проверка наличия — in
if "red" in colors:
    print(colors["red"])
```

### Удаление

```python
del colors["red"]            # KeyError если нет
val = colors.pop("red")      # val=значение, KeyError если нет
val = colors.pop("red", None)  # без исключения
colors.clear()
```

### Перебор

```python
for key in colors:           # перебор ключей
    print(key, colors[key])

for key, value in colors.items():
    print(key, "→", value)

for value in colors.values():
    print(value)
```

### Слияние

```python
a = {"x": 1, "y": 2}
b = {"y": 3, "z": 4}

# update — изменяет на месте
a.update(b)                  # a = {"x": 1, "y": 3, "z": 4}

# | — оператор слияния (3.9+) — возвращает новый
merged = a | b               # новый словарь

# Распаковка — тоже создаёт новый
merged = {**a, **b}
```

### `setdefault`

Установить значение, если ключа нет:

```python
counts = {}
for word in ["a", "b", "a", "c", "a", "b"]:
    counts.setdefault(word, 0)
    counts[word] += 1
# {"a": 3, "b": 2, "c": 1}
```

Часто проще `collections.Counter`:

```python
from collections import Counter
counts = Counter(["a", "b", "a", "c", "a", "b"])
# Counter({'a': 3, 'b': 2, 'c': 1})
```

### `defaultdict`

Автоматически создаёт ключ с дефолтным значением:

```python
from collections import defaultdict

groups = defaultdict(list)
for name, group in [("Аня", "А"), ("Боря", "Б"), ("Вася", "А")]:
    groups[group].append(name)
# defaultdict(<class 'list'>, {'А': ['Аня', 'Вася'], 'Б': ['Боря']})
```

### Словари в Go: `map`

```go
colors := map[string]string{
    "red":   "красный",
    "green": "зелёный",
}

colors["blue"] = "синий"     // добавление
v := colors["red"]           // "красный"

// Проверка наличия (важно: при отсутствии возвращается "zero value")
v, ok := colors["yellow"]
if ok {
    fmt.Println(v)
} else {
    fmt.Println("нет ключа")
}

// Удаление
delete(colors, "red")

// Перебор (порядок СЛУЧАЕН — намеренно, чтобы вы на него не закладывались)
for k, v := range colors {
    fmt.Println(k, v)
}
```

## Множества (`set`)

Множество — **неупорядоченная** коллекция **уникальных** хэшируемых элементов.

### Создание

```python
empty = set()                # ВАЖНО: {} — это пустой словарь!
nums = {1, 2, 3}
chars = set("hello")         # {'h', 'e', 'l', 'o'}
unique = set([1, 2, 2, 3, 3, 3])   # {1, 2, 3}

# Генератор множеств
squares = {x * x for x in range(-3, 4)}   # {0, 1, 4, 9}
```

### Применения

**Удаление дубликатов:**

```python
words = ["hello", "world", "hello", "python"]
unique_words = list(set(words))
```

**Быстрая проверка членства** (`in` за `O(1)` вместо `O(n)` для списка):

```python
valid_codes = {"OK", "PENDING", "ERROR"}
if status in valid_codes:
    ...
```

**Математические операции:**

```python
a = {1, 2, 3, 4}
b = {3, 4, 5, 6}

a | b     # {1, 2, 3, 4, 5, 6} — объединение
a & b     # {3, 4}             — пересечение
a - b     # {1, 2}              — разность
a ^ b     # {1, 2, 5, 6}        — симметричная разность

a <= b    # False — подмножество?
a < b     # False — строгое подмножество?
a.isdisjoint({7, 8})  # True — не пересекаются?
```

### Методы

```python
s = {1, 2, 3}
s.add(4)              # {1, 2, 3, 4}
s.discard(2)          # {1, 3, 4} — не падает если нет
s.remove(3)           # KeyError если нет
s.pop()               # удалить и вернуть произвольный
s.clear()
```

### `frozenset`

Неизменяемое множество — можно использовать как ключ словаря:

```python
fs = frozenset([1, 2, 3])
fs.add(4)             # AttributeError — неизменяемо

# Можно как ключ словаря
permissions = {
    frozenset(["read"]): "viewer",
    frozenset(["read", "write"]): "editor",
}
```

### Множества в Go

Отдельного типа нет. Идиома — `map[T]struct{}`:

```go
seen := map[string]struct{}{}
seen["hello"] = struct{}{}
seen["world"] = struct{}{}

if _, ok := seen["hello"]; ok {
    fmt.Println("найдено")
}

delete(seen, "hello")
```

`struct{}` занимает ноль байт — идеальный тип-«пустышка». Альтернатива — `map[T]bool` (чуть проще читать, но 1 байт на значение).

В Go 1.21+ появились утилиты в `slices` (а в будущем — generic `set` в стандартной библиотеке предлагается, но пока нет).

## Когда что выбирать

| Задача | Выбор |
|--------|-------|
| Упорядоченный список с изменением | `list` (Py) / `slice` (Go) |
| Фиксированный набор полей разных типов | `tuple` (Py) или `NamedTuple`/`dataclass` / `struct` (Go) |
| Быстрый поиск по уникальному ключу | `dict` (Py) / `map` (Go) |
| Проверка членства / устранение дубликатов | `set` (Py) / `map[T]struct{}` (Go) |
| Подсчёт частот | `Counter` (Py) / самописная агрегация в `map[T]int` (Go) |
| Слово → список | `defaultdict(list)` (Py) / `map[string][]T` (Go) |

## Подводные камни

### Неявное копирование изменяемых типов

```python
default = []
def append_to(value, lst=default):   # ОПАСНО — список общий между вызовами!
    lst.append(value)
    return lst

append_to(1)   # [1]
append_to(2)   # [1, 2]  ← НЕ [2]
```

Правильно:

```python
def append_to(value, lst=None):
    if lst is None:
        lst = []
    lst.append(value)
    return lst
```

### Изменение списка во время перебора

```python
nums = [1, 2, 3, 4]
for n in nums:
    if n % 2 == 0:
        nums.remove(n)    # БАГ — пропустит элементы
```

Правильно — создайте копию или новый список:

```python
nums = [n for n in nums if n % 2 != 0]
```

### Хэшируемость

В `dict` ключами и в `set` элементами могут быть только **хэшируемые** значения. Хэшируемые — все неизменяемые встроенные типы (`int`, `str`, `tuple`, `frozenset`). Не хэшируемые — `list`, `dict`, `set`.

```python
d = {}
d[(1, 2)] = "ok"      # tuple — хэшируемый
d[[1, 2]] = "bad"     # TypeError: unhashable type: 'list'
```

### Поверхностная vs глубокая копия

```python
import copy

original = [[1, 2], [3, 4]]
shallow = original.copy()           # копирует внешний список, вложенные общие
shallow[0].append(99)
print(original)   # [[1, 2, 99], [3, 4]]  ← изменили оригинал

deep = copy.deepcopy(original)      # независимая копия
deep[0].append(100)
print(original)   # [[1, 2, 99], [3, 4]] — не изменён
```

В Go то же самое — `copy()` для slice копирует только верхний уровень.

## Сравнение Python ↔ Go: коллекции

| Аспект | Python | Go |
|--------|--------|-----|
| Список | `list` (`[1, 2]`) | `[]int{1, 2}` |
| Срезы возвращают | копию | окно |
| Сортировка | `list.sort()` / `sorted()` | `slices.Sort()` (1.21+) |
| Кортеж | `(1, 2, 3)` | array `[3]int{...}` или struct |
| Множественный возврат | tuple | нативно |
| Словарь | `dict` | `map` |
| Перебор — порядок | сохраняется (с 3.7) | случайный (специально) |
| Проверка ключа | `key in d`, `d.get(k)` | `v, ok := d[k]` |
| Множество | `set` (`{1, 2}`) | `map[T]struct{}` |
| Comprehensions | да | нет (только циклы) |

---

## Контрольные вопросы

- Почему `(1)` не кортеж, а `(1,)` — кортеж?
- Что произойдёт, если изменить срез слайса в Go и почему это поведение отличается от Python?
- В чём разница между `list.sort()` и `sorted(list)`? Что вернёт каждая?
- Какие типы могут быть ключами словаря и почему?
- Зачем нужен `setdefault`, и чем `defaultdict(list)` от него отличается?
- Почему `set()` пустое, а `{}` — это пустой словарь?
- Какие операции над множествами есть и как они называются в математике?
- Чем `frozenset` отличается от `set` и где это пригождается?
- Почему в Go перебор `map` даёт случайный порядок?
- Чем `shallow copy` отличается от `deep copy`, в каких случаях это критично?
