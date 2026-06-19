# common — общие утилиты

Базовые helper'ы, которые повторяются из лабораторной в лабораторную, вынесены в локальный пакет `labs/common` — чтобы не дублировать один и тот же код. Лабы импортируют их напрямую:

```python
from labs.common import array_length, generate_array, print_array, custom_range
```

Импортировать можно как из пакета (`from labs.common import array_length`), так и из конкретного модуля (`from labs.common.arrays import array_length`). Встроенные функции (`len`, `range`, …) внутри этих helper'ов **намеренно не используются** — это часть учебного задания.

Пакет разложен на два модуля:

| Модуль | Что внутри |
|--------|------------|
| `labs.common.arrays` | `array_length`, `generate_array`, `print_array` |
| `labs.common.ranges` | `CustomRange` (класс) и псевдоним `custom_range` |

## `arrays` — операции над массивом

### `array_length(arr)` — длина без `len()`

Проходим по всем элементам и считаем их — «ручная» замена `len()`.

```python
def array_length(arr: list) -> int:
    count = 0
    for _ in arr:      # перебираем элементы, само значение не нужно
        count += 1
    return count
```

- **Сложность:** O(n) — один проход.
- В реальном коде так писать не нужно: есть `len()` за O(1). Здесь — учебная цель.

### `generate_array(size)` — заполнение случайными числами

```python
def generate_array(size: int) -> list[int]:
    result = []
    i = 0
    while i < size:
        result.append(random.randint(1, 100))  # случайное число 1..100 включительно
        i += 1
    return result
```

- `random.randint(a, b)` возвращает целое в диапазоне **[a, b]** (обе границы включены).
- Цикл `while` с ручным счётчиком вместо `for i in range(size)` — снова из-за запрета встроенных функций.

### `print_array(arr)` — вывод по индексу

Задание требует обращаться к элементам **по индексу**, а не перебором значений.

```python
def print_array(arr: list[int]) -> None:
    i = 0
    while i < array_length(arr):
        print(f"[{i}] = {arr[i]}")   # arr[i] — доступ по индексу
        i += 1
```

Вывод:
```
[0] = 42
[1] = 7
[2] = 99
```

## `ranges` — самописный `range`

`CustomRange` — это **ленивый аналог встроенной `range`**, а не просто функция, возвращающая список. Он хранит только `start`/`stop`/`step` и предвычисленную длину, а каждый элемент вычисляет арифметически по запросу. `custom_range` — строчный псевдоним этого же класса (`custom_range = CustomRange`), чтобы вызовы выглядели как у встроенной `range`.

```python
from labs.common import CustomRange, custom_range
list(custom_range(0, 10, 2))   # [0, 2, 4, 6, 8]
```

### Как устроена настоящая `range` в CPython

Чтобы понять, что именно мы воспроизводим, полезно знать внутреннее устройство оригинала. `range` — это C-объект `rangeobject` (`Objects/rangeobject.c`):

```c
typedef struct {
    PyObject_HEAD
    PyObject *start;
    PyObject *stop;
    PyObject *step;
    PyObject *length;   // предвычисленная длина
} rangeobject;
```

Поля хранятся как `PyObject*` (а не как `long`), поэтому `range(10**100)` работает — границы лежат в виде Python-`int` неограниченной точности. Ключевые механики:

- **Длина** считается один раз при создании по формуле `(stop - start + step - 1) // step` (с зеркальным вариантом для отрицательного шага) и кешируется. Поэтому `len(r)` — чтение поля, **O(1)**.
- **Индексация** `r[i]` — чистая арифметика `start + i * step` с нормализацией отрицательного индекса через длину. Никакого перебора, **O(1)**.
- **Объект сам ничего не итерирует** — для прохода создаётся отдельный итератор, наращивающий значение на шаг. Список в памяти не строится.
- **`x in r`** для **целого** `x` проверяется арифметически: лежит ли `x` в границах и делится ли `(x - start)` нацело на `step` → **O(1)**. Для нецелого `x` (`float`, строка, объект) CPython откатывается к линейному перебору со сравнением `==` → **O(n)**.
- **Срез** `r[a:b:c]` строит новый `range` с пересчитанными границами — данные не копируются.
- **Равенство** сравнивает диапазоны по **порождаемой последовательности**, а не по сырым параметрам: `range(0, 3, 2) == range(0, 4, 2)`, потому что оба дают `[0, 2]`. Хеш согласован с этим.

### `CustomRange` — наша реализация

`CustomRange` повторяет все эти свойства. Он наследуется от `collections.abc.Sequence` — благодаря этому становится «настоящей» последовательностью и работает как drop-in там, где нужен sequence-протокол (например, `random.sample(custom_range(1, 100), 7)` в лабах). Встроенные `range`/`max` внутри намеренно не используются.

#### Конструктор и длина

```python
class CustomRange(Sequence):
    def __init__(self, start, stop=None, step=1):
        if stop is None:                      # форма CustomRange(stop)
            start, stop = 0, start
        if step == 0:
            raise ValueError("CustomRange() arg 3 must not be zero")
        self.start, self.stop, self.step = start, stop, step
        if step > 0:
            raw = (stop - start + step - 1) // step
        else:
            raw = (start - stop - step - 1) // (-step)
        self._length = raw if raw > 0 else 0   # без встроенного max
```

- `stop is None` → единственный аргумент трактуется как верхняя граница, старт сдвигается на 0 — как у `range`.
- `step == 0` запрещён (иначе бесконечный цикл) → `ValueError`.
- Длина вычисляется **один раз** той же формулой, что в CPython, и кешируется в `_length`. `len()` потом — O(1).

#### Индексация и срез — O(1)

```python
    def __getitem__(self, index):
        if isinstance(index, slice):                 # срез → новый CustomRange
            start, stop, step = index.indices(self._length)
            return CustomRange(
                self.start + start * self.step,
                self.start + stop * self.step,
                self.step * step,
            )
        if index < 0:
            index += self._length                    # нормализация отрицательного
        if not 0 <= index < self._length:
            raise IndexError("CustomRange object index out of range")
        return self.start + index * self.step         # i-й элемент — арифметика
```

`r[i]` — это `start + i * step`, без перебора. Срез не копирует элементы, а строит новый `CustomRange` с пересчитанными границами.

#### Ленивая итерация

```python
    def __iter__(self):
        value = self.start
        count = 0
        while count < self._length:
            yield value
            value += self.step
            count += 1
```

Значение наращивается на шаг в генераторе — список в памяти не материализуется. Поэтому `custom_range(10**18)` создаётся мгновенно. `__reversed__` устроен симметрично (идём от последнего элемента вниз).

#### Проверка вхождения — O(1) для целых

```python
    def __contains__(self, x):
        if not isinstance(x, int):
            return any(v == x for v in self)         # медленный путь, O(n)
        if self._length == 0:
            return False
        if self.step > 0:
            in_bounds = self.start <= x < self.stop
        else:
            in_bounds = self.stop < x <= self.start
        return in_bounds and (x - self.start) % self.step == 0
```

Тот же приём, что в CPython: для целого — проверка границ и делимости за O(1); для нецелого — откат к перебору. `index()` и `count()` опираются на ту же арифметику.

#### Равенство и хеш — по последовательности

```python
    def __eq__(self, other):
        if not isinstance(other, CustomRange):
            return NotImplemented
        if self._length != other._length:
            return False
        if self._length == 0:
            return True
        if self.start != other.start:
            return False
        if self._length == 1:
            return True
        return self.step == other.step
```

Два диапазона равны, если порождают одну и ту же последовательность, даже при разных параметрах: `CustomRange(0, 3, 2) == CustomRange(0, 4, 2)` (оба дают `[0, 2]`). `__hash__` обнуляет незначимые поля (для пустого и одноэлементного диапазона `step`/`start` не влияют), чтобы равные объекты имели равный хеш — иначе они вели бы себя некорректно в `set`/`dict`.

### Свойства и отличия от оригинала

| Операция | `CustomRange` | Сложность |
|----------|---------------|-----------|
| `len(r)` | чтение `_length` | O(1) |
| `r[i]` | `start + i * step` | O(1) |
| `x in r` (целое) | арифметика | O(1) |
| `x in r` (нецелое) | перебор | O(n) |
| итерация | генератор, без списка | O(n), O(1) память |
| `r[a:b:c]` | новый `CustomRange` | O(1) |

Главное упрощение против CPython: всё на Python-`int` (что бесплатно даёт неограниченную точность), нет разделения на быстрый/общий итераторы и нет поддержки `__index__` для объектов, маскирующихся под `int`.

Используется в [lab02](lab02.md) и [lab02_random](lab02_random.md) при построении «холста» для визуализации дерева (`for _ in custom_range(rows)`) и как популяция для `random.sample`.

## Где это в проде

Сами по себе `array_length` и `print_array` — учебные заглушки встроенных функций, но `CustomRange` иллюстрирует приём, без которого не обходится ни один эксплуатационный скрипт, — **ленивые вычисления**:

- **Ленивая итерация = константная память на любом объёме.** `CustomRange` не материализует список, а вычисляет элементы на ходу — поэтому `custom_range(10**18)` создаётся мгновенно. Тот же принцип у генераторов Python и итераторов/каналов Go: читать гигабайтный лог построчно ([lab10](lab10.md)), а не грузить его в память целиком; стримить ответ HTTP, а не собирать в буфер. Разница между `range` и list — ровно об этом.
- **Sequence-протокол.** Наследование от `collections.abc.Sequence` даёт объекту индексацию, срезы и `in` «бесплатно» — пример того, как стандартные интерфейсы (в духе `io.Reader` в Go) позволяют своим типам работать с чужим кодом без переделок.
