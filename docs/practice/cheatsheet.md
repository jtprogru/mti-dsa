# Шпаргалка

Краткий справочник по типам данных и области видимости в Python с параллелями в Go. Для подробного изучения — соответствующие лекции.

## Типы данных в Python

| Тип | Категория | Изменяемость | Литерал |
|------|-----------|--------------|---------|
| `None` | специальный | — | `None` |
| `bool` | логический | неизменяемый | `True`, `False` |
| `int` | число | неизменяемый | `42`, `0b101`, `0x1F` |
| `float` | число с плавающей точкой | неизменяемый | `3.14`, `1e-3` |
| `complex` | комплексное число | неизменяемый | `1 + 2j` |
| `str` | строка (Unicode) | **неизменяемый** | `"hello"`, `'hi'`, `"""..."""` |
| `bytes` | байтовая строка | **неизменяемый** | `b"\x00"` |
| `bytearray` | массив байт | изменяемый | `bytearray(b"...")` |
| `memoryview` | окно в байты без копирования | — | `memoryview(b)` |
| `list` | список произвольных объектов | изменяемый | `[1, 2, 3]` |
| `tuple` | **неизменяемый** список | неизменяемый | `(1, 2, 3)` |
| `range` | диапазон чисел | неизменяемый | `range(5)` |
| `set` | множество уникальных | изменяемый | `{1, 2, 3}` |
| `frozenset` | **неизменяемое** множество | неизменяемый | `frozenset({1, 2})` |
| `dict` | словарь / хэш-таблица / JSON-подобный | изменяемый | `{"k": "v"}` |

Подробно — [Тема 3, Лекция 1](../foundations/03-python-basics/lecture-01-syntax-types.md) и [Лекция 3](../foundations/03-python-basics/lecture-03-collections.md).

### Аналоги в Go

| Python | Go |
|--------|-----|
| `None` | `nil` (только для указателей/слайсов/мап/каналов/функций/интерфейсов) |
| `bool` | `bool` |
| `int` | `int8`, `int16`, `int32`, `int64`, `int` (платформо-зависимый) |
| `float` | `float32`, `float64` |
| `complex` | `complex64`, `complex128` |
| `str` | `string` (UTF-8 байты) |
| `bytes` / `bytearray` | `[]byte` |
| `list` | slice (`[]T`) |
| `tuple` | array (`[N]T`) или `struct` |
| `set` | `map[T]struct{}` (идиома) |
| `dict` | `map[K]V` |

## Область видимости в Python (LEGB)

Python ищет имена в **четырёх** областях в таком порядке:

1. **Local (L)** — внутри текущей функции (`def`).
2. **Enclosing (E)** — в охватывающей функции (для замыканий).
3. **Global (G)** — на уровне модуля (за пределами всех `def`).
4. **Built-in (B)** — встроенные имена (`print`, `len`, `max`, ...).

### Модификаторы

- `global x` — внутри функции **изменить** глобальную переменную (а не создать локальную).
- `nonlocal x` — внутри вложенной функции **изменить** переменную из охватывающей функции.

```python
counter = 0  # G

def make_counter():
    count = 0  # E (для inc)

    def inc() -> int:
        nonlocal count  # ссылается на E, а не L
        count += 1
        return count

    return inc


def reset():
    global counter  # ссылается на G
    counter = 0
```

Подробно — [Тема 4, Лекция 1](../foundations/04-procedures-and-files/lecture-01-functions.md).

### Scope в Go

Go проще:

- Scope определяется блоком `{ ... }`.
- Имена с заглавной буквы экспортируются из пакета, с маленькой — приватны.
- `package`-level переменные — аналог глобальных, доступны во всём пакете.

## Быстрые рецепты Python

### Распаковка

```python
a, b, c = 1, 2, 3
a, b = b, a                       # swap

first, *rest = [1, 2, 3, 4]       # first=1, rest=[2,3,4]
head, *body, tail = [1, 2, 3, 4]  # head=1, body=[2,3], tail=4
```

### F-strings (Python 3.6+)

```python
name, n = "Аня", 42

f"{name=}"          # "name='Аня'" (отладка, 3.8+)
f"{n:08b}"          # "00101010"
f"{n:08x}"          # "0000002a"
f"{3.14159:.2f}"    # "3.14"
f"{1_000_000:,}"    # "1,000,000"
```

### Списочные/словарные/множественные comprehensions

```python
squares = [x * x for x in range(10)]
even = [x for x in range(20) if x % 2 == 0]
matrix = [[0] * 5 for _ in range(3)]

inv = {v: k for k, v in d.items()}
chars = {c for c in "hello" if c not in "aeiou"}
```

### Безопасный доступ

```python
d.get("key", default)           # без KeyError
d.setdefault("key", default)    # создать если нет

# Counter / defaultdict
from collections import Counter, defaultdict
Counter(["a", "b", "a"])        # Counter({'a': 2, 'b': 1})
groups = defaultdict(list)
groups["fruits"].append("apple")
```

### Контекстные менеджеры

```python
with open("data.txt", encoding="utf-8") as f:
    data = f.read()

# Несколько сразу
with open("in.txt") as fi, open("out.txt", "w") as fo:
    fo.write(fi.read())
```

### Типичные «питоничные» оптимизации

```python
# Перебор с индексом
for i, item in enumerate(items):
    ...

# Параллельный перебор
for a, b in zip(list_a, list_b):
    ...

# Условный возврат
value = a if condition else b

# Цепочка сравнений (только Python)
if 0 < x < 100:
    ...

# Walrus (3.8+)
if (n := len(data)) > 100:
    print(f"много: {n}")
```

## Что нельзя в Python

- ⛔ `null` — есть `None`.
- ⛔ `++` / `--` — есть `+= 1` / `-= 1`.
- ⛔ Объявление типа без значения (`int x;` в стиле C) — все переменные сразу со значением.
- ⛔ Изменить `str`, `tuple`, `bytes`, `frozenset` — они неизменяемые.
- ⛔ Использовать `list`, `dict`, `set` как ключ словаря — они не хэшируемы.
- ⛔ `switch/case` (но есть `match/case` с Python 3.10+).
- ⛔ Тернарный `cond ? a : b` — есть `a if cond else b`.

## Когда использовать что

| Задача | Рекомендация |
|--------|--------------|
| Список с возможностью изменения | `list` |
| Фиксированный набор разнотипных полей | `tuple` или `dataclass` / `NamedTuple` |
| Быстрый поиск по уникальному ключу | `dict` |
| Проверка членства, устранение дубликатов | `set` |
| Подсчёт частот | `Counter` |
| Группировка | `defaultdict(list)` |
| Финансовые расчёты | `Decimal`, **не** `float` |
| Кэширование функции | `@functools.cache` или `@lru_cache(maxsize=...)` |
| Чтение конфигов | TOML (`tomllib`) или YAML (`pyyaml`), **не** `pickle` |
| Сериализация для других языков | JSON, **не** `pickle` |
