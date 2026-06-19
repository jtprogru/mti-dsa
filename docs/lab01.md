# lab01 — массив и стек

Учебное ограничение лабораторной: **не использовать встроенные функции** (`len`, `range`, `max`, `sum`). Поэтому даже длина массива считается вручную.

## Содержание

- [Функции над массивом](#функции-над-массивом)
  - [`array_length`](#array_lengtharr--длина-без-len)
  - [`generate_array`](#generate_arraysize--заполнение-случайными-числами)
  - [`print_array`](#print_arrayarr--вывод-по-индексу)
  - [`custom_max`](#custom_maxarr--максимум-значение)
  - [`custom_max_index`](#custom_max_indexarr--максимум-индекс)
  - [`calculate_total_sum`](#calculate_total_sumarr--сумма-без-sum)
- [Класс Stack](#класс-stack)

---

## Функции над массивом

> `array_length`, `generate_array` и `print_array` переиспользуются и в следующих лабораторных, поэтому вынесены в общий пакет `labs/common` (`from labs.common import ...`) — подробнее на странице [common](common.md). Ниже они разобраны в контексте lab01.

### `array_length(arr)` — длина без `len()`

Проходим по всем элементам и считаем их. Это «ручная» замена `len()`.

```python
def array_length(arr: list) -> int:
    count = 0
    for _ in arr:      # перебираем элементы, само значение не нужно
        count += 1
    return count
```

- **Идея:** счётчик увеличивается на каждой итерации.
- **Сложность:** O(n) — один проход.
- В реальном коде так писать не нужно: есть `len()` за O(1). Здесь — учебная цель.

### `generate_array(size)` — заполнение случайными числами

```python
import random

def generate_array(size: int) -> list[int]:
    result = []
    i = 0
    while i < size:
        result.append(random.randint(1, 100))  # случайное число 1..100 включительно
        i += 1
    return result
```

- `random.randint(a, b)` возвращает целое в диапазоне **[a, b]** (обе границы включены).
- Цикл `while` с ручным счётчиком вместо `for i in range(size)` — опять же из-за запрета встроенных функций.

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

### `custom_max(arr)` — максимум (значение)

Классический алгоритм поиска максимума: берём первый элемент за «текущий максимум» и сравниваем с остальными.

```python
def custom_max(arr: list[int]) -> int:
    if not arr:                       # защита от пустого массива
        raise ValueError("Массив пуст, невозможно найти максимальный элемент.")
    m = arr[0]                        # предполагаем, что первый — максимальный
    for x in arr[1:]:                 # сравниваем с остальными
        if x > m:
            m = x                     # нашли больше — обновляем
    return m
```

- **Инвариант:** после обработки k элементов `m` равен максимуму среди них.
- **Сложность:** O(n).
- `if not arr` — пустой список считается «ложным», поэтому это проверка на пустоту.

### `custom_max_index(arr)` — максимум (индекс)

То же самое, но запоминаем ещё и **позицию** максимума.

```python
def custom_max_index(arr: list[int]) -> int:
    if not arr:
        raise ValueError("Массив пуст, невозможно найти максимальный элемент.")
    m = arr[0]      # текущий максимум (значение)
    idx = 0         # индекс текущего максимума
    x = 1
    while x < array_length(arr):
        if arr[x] > m:
            m = arr[x]
            idx = x     # запоминаем позицию
        x += 1
    return idx
```

- Возвращает индекс **первого** вхождения максимума (строгое `>`, не `>=`).
- **Сложность:** O(n).

### `calculate_total_sum(arr)` — сумма без `sum()`

```python
def calculate_total_sum(arr: list[int]) -> int:
    total = 0
    for x in arr:
        total += x
    return total
```

- Аккумулятор `total` накапливает сумму. **Сложность:** O(n).

---

## Класс Stack

**Стек (stack)** — структура данных по принципу **LIFO** (Last In, First Out, «последним пришёл — первым ушёл»). Как стопка тарелок: кладём и берём сверху.

Здесь стек реализован поверх обычного списка (массива). «Вершина» стека — это **конец** списка, потому что добавление/удаление в конце списка работает за O(1).

```python
class Stack:
    def __init__(self) -> None:
        self._data: list = []          # внутреннее хранилище

    def is_empty(self) -> bool:
        return array_length(self._data) == 0

    def push(self, value) -> None:     # добавить на вершину
        self._data.append(value)

    def pop(self):                     # снять с вершины и вернуть
        if self.is_empty():
            raise IndexError("Стек пуст, невозможно извлечь элемент.")
        return self._data.pop()

    def peek(self):                    # посмотреть вершину, не снимая
        if self.is_empty():
            raise IndexError("Стек пуст, невозможно получить вершину.")
        return self._data[array_length(self._data) - 1]   # последний элемент

    def print_stack(self) -> None:     # печать от вершины к началу
        if self.is_empty():
            print("Стек пуст.")
            return
        i = array_length(self._data) - 1   # с конца
        while i >= 0:
            print(self._data[i])
            i -= 1
```

**Ключевые операции:**

| Метод       | Что делает                          | Сложность |
|-------------|-------------------------------------|-----------|
| `push(v)`   | добавить элемент на вершину         | O(1)      |
| `pop()`     | снять и вернуть верхний элемент     | O(1)      |
| `peek()`    | вернуть вершину, **не снимая**      | O(1)      |
| `is_empty()`| проверка на пустоту                 | O(1)*     |
| `print_stack()` | печать сверху вниз              | O(n)      |

\* `is_empty` использует `array_length` (O(n)) только из-за учебного запрета на `len`.

**Разница `pop` и `peek`:** `pop` удаляет элемент, `peek` — только подсматривает.

Пример использования:
```python
stack = Stack()
stack.push(10)
stack.push(20)
stack.push(30)
print(stack.peek())   # 30 (вершина, не снята)
print(stack.pop())    # 30 (снята)
print(stack.peek())   # 20 (новая вершина)
```

**Где применяется стек:** отмена действий (Ctrl+Z), проверка скобок, вызовы функций (call stack), обход графа в глубину (DFS).

---

## Где это в проде

Массив и стек — настолько базовые, что в проде они везде «под капотом»:

- **Массив (непрерывная память).** Слайс в Go (`[]byte`), список в Python, буферы ввода-вывода — это всё массив: доступ по индексу за O(1) и расположение элементов подряд, которое любит кэш процессора (последовательное чтение префетчится, случайные прыжки по памяти — нет). Кольцевые буферы метрик и логов, на которых стоит [lab09](lab09.md) (rate limiting), — тоже массив.
- **Стек вызовов (call stack).** Каждый вызов функции кладёт на стек фрейм с локальными переменными и адресом возврата; `panic` в Go и traceback в Python — это распечатка стека сверху вниз. Переполнение стека (`stack overflow`) — бесконечная рекурсия, упёршаяся в его лимит. Тот же LIFO — в откате действий (undo), сопоставлении скобок/тегов в парсерах и линтерах, обходе графа в глубину ([lab06](lab06.md)).

---

## Параллельная реализация на Go

Те же структуры реализованы на Go в пакете [`src/golang/dsa/lab01`](https://github.com/jtprogru/dsa-for-ops/tree/main/src/golang/dsa/lab01) (с table-driven тестами в `lab01_test.go`). Отличия от Python: вместо исключений — возврат `error`, а стек обобщён через дженерики (`Stack[T any]`).

=== "Python"

    ```python
    class Stack:
        def __init__(self) -> None:
            self._data: list = []

        def is_empty(self) -> bool:
            return array_length(self._data) == 0

        def push(self, value) -> None:
            self._data.append(value)

        def pop(self):
            if self.is_empty():
                raise IndexError("Стек пуст.")
            return self._data.pop()

        def peek(self):
            if self.is_empty():
                raise IndexError("Стек пуст.")
            return self._data[array_length(self._data) - 1]
    ```

=== "Go"

    ```go
    type Stack[T any] struct {
        data []T
    }

    func (s *Stack[T]) IsEmpty() bool {
        return ArrayLength(s.data) == 0
    }

    func (s *Stack[T]) Push(value T) {
        s.data = append(s.data, value)
    }

    func (s *Stack[T]) Pop() (T, error) {
        var zero T
        if s.IsEmpty() {
            return zero, ErrEmpty
        }
        last := ArrayLength(s.data) - 1
        value := s.data[last]
        s.data = s.data[:last]
        return value, nil
    }

    func (s *Stack[T]) Peek() (T, error) {
        var zero T
        if s.IsEmpty() {
            return zero, ErrEmpty
        }
        return s.data[ArrayLength(s.data)-1], nil
    }
    ```
