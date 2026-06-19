# lab02 — связный список, очередь, дерево

## Содержание

- [Node — узел односвязного списка](#node--узел-односвязного-списка)
- [LinkedList — односвязный список](#linkedlist--односвязный-список)
- [Queue — очередь](#queue--очередь)
- [TreeNode — узел бинарного дерева](#treenode--узел-бинарного-дерева)
- [BinaryTree — бинарное дерево поиска (BST)](#binarytree--бинарное-дерево-поиска-bst)
- [Визуализация дерева (`print_tree`)](#визуализация-дерева-print_tree)

---

## Node — узел односвязного списка

Базовый «кирпичик» связных структур. Хранит **значение** и **ссылку на следующий** узел.

```python
class Node:
    def __init__(self, value: int) -> None:
        self.value: int = value          # полезные данные
        self.next: "Node | None" = None  # ссылка на следующий узел (или None)
```

- `next = None` означает «следующего нет» — это **конец списка**.
- В строковой аннотации `"Node | None"` тип в кавычках, потому что класс `Node` ещё не «дообъявлен» в момент написания (forward reference).

Несколько узлов, связанных через `next`, образуют цепочку:
```
head → [10|•] → [20|•] → [30|None]
```

## LinkedList — односвязный список

**Связный список** — последовательность узлов, где каждый знает только о следующем. В отличие от массива, элементы **не лежат подряд в памяти**, доступ по индексу невозможен — только перебором от головы.

Класс хранит лишь `head` (голову). Всё остальное достижимо через `.next`.

```python
class LinkedList:
    def __init__(self) -> None:
        self.head: Node | None = None    # первый узел; None = список пуст
```

### `add(value)` — добавить в конец

Идём до последнего узла (у которого `next is None`) и прицепляем новый.

```python
    def add(self, value: int) -> None:
        new_node = Node(value)
        if self.head is None:        # список пуст — новый узел становится головой
            self.head = new_node
            return
        current = self.head
        while current.next is not None:   # доходим до последнего узла
            current = current.next
        current.next = new_node           # прицепляем в конец
```

- **Сложность:** O(n) — нужно дойти до конца (нет хранения «хвоста»).

### `remove(value)` — удалить первый узел с этим значением

Главная идея удаления в связном списке: **«перепрыгнуть» через узел**, переставив ссылку `next` у предыдущего узла.

```python
    def remove(self, value: int) -> None:
        if self.head is None:            # пустой список — ничего не делаем
            return
        if self.head.value == value:     # удаляем голову — особый случай
            self.head = self.head.next
            return
        current = self.head
        while current.next is not None:
            if current.next.value == value:
                current.next = current.next.next   # «перепрыгиваем» через узел
                return
            current = current.next
```

- Узел не удаляется явно — на него просто **никто больше не ссылается**, и сборщик мусора Python освобождает память.
- Удаляется только **первое** вхождение значения.
- **Сложность:** O(n).

Схема `current.next = current.next.next`:
```
до:    [A] → [B] → [C]          (удаляем B)
              ↑ current.next
после: [A] ─────→ [C]           (B больше недостижим)
```

### `print_list()` — печать всех значений

```python
    def print_list(self) -> None:
        current = self.head
        while current is not None:    # пока узлы не кончились
            print(current.value)
            current = current.next    # шаг к следующему
```

Это **типовой шаблон обхода** связного списка: `current = head`, цикл `while current is not None`, в конце `current = current.next`.

## Queue — очередь

**Очередь (queue)** — структура по принципу **FIFO** (First In, First Out, «первым пришёл — первым ушёл»). Как очередь в магазине: добавляем в хвост, обслуживаем с головы.

Реализована на связном списке с **двумя указателями**: `_head` (откуда извлекаем) и `_tail` (куда добавляем). Хранение хвоста делает добавление O(1).

```python
class Queue:
    def __init__(self) -> None:
        self._head: Node | None = None  # front — откуда извлекаем (dequeue)
        self._tail: Node | None = None  # back  — куда добавляем (enqueue)

    def is_empty(self) -> bool:
        return self._head is None
```

### `enqueue(value)` — добавить в хвост

```python
    def enqueue(self, value: int) -> None:
        new_node = Node(value)
        if self._tail is None:        # очередь пуста: новый узел и голова, и хвост
            self._head = new_node
            self._tail = new_node
            return
        self._tail.next = new_node    # прицепляем за текущим хвостом
        self._tail = new_node         # новый узел становится хвостом
```

- **Сложность:** O(1) — именно ради этого хранится `_tail`.

### `dequeue()` — извлечь из головы

```python
    def dequeue(self) -> int:
        if self.is_empty():
            raise IndexError("Очередь пуста, невозможно извлечь элемент.")
        value = self._head.value
        self._head = self._head.next   # голова сдвигается на следующий
        if self._head is None:         # очередь опустела — обнуляем и хвост
            self._tail = None
        return value
```

- **Тонкий момент:** если после извлечения голова стала `None`, нужно обнулить и `_tail`, иначе он будет указывать на «висячий» удалённый узел.
- **Сложность:** O(1).

### `peek()` и `print_queue()`

```python
    def peek(self) -> int:             # посмотреть первый, не извлекая
        if self.is_empty():
            raise IndexError("Очередь пуста, невозможно получить значение.")
        return self._head.value

    def print_queue(self) -> None:     # печать от головы к хвосту
        if self.is_empty():
            print("Очередь пуста.")
            return
        current = self._head
        while current is not None:
            print(current.value)
            current = current.next
```

**Стек vs очередь** — главное различие:

| | Стек (LIFO) | Очередь (FIFO) |
|---|---|---|
| Добавление | на вершину | в хвост |
| Извлечение | с вершины (последний) | с головы (первый) |
| Аналогия | стопка тарелок | очередь людей |
| Применение | отмена, DFS, рекурсия | задачи по порядку, BFS, буферы |

## TreeNode — узел бинарного дерева

В отличие от `Node` (одна ссылка `next`), узел дерева имеет **две** ссылки — на левого и правого потомка.

```python
class TreeNode:
    def __init__(self, value: int) -> None:
        self.value: int = value
        self.left: "TreeNode | None" = None   # левый потомок
        self.right: "TreeNode | None" = None  # правый потомок
```

## BinaryTree — бинарное дерево поиска (BST)

**Бинарное дерево поиска (Binary Search Tree)** — дерево, где для каждого узла:

- все значения в **левом** поддереве **меньше** значения узла;
- все значения в **правом** поддереве **больше или равны**.

Это свойство (BST-инвариант) позволяет искать, как в бинарном поиске: на каждом шаге отбрасываем половину дерева.

```python
class BinaryTree:
    def __init__(self) -> None:
        self.root: TreeNode | None = None    # корень дерева
```

### `add(value)` — вставка с сохранением порядка

Спускаемся от корня: меньше — идём влево, иначе — вправо, пока не найдём пустое место.

```python
    def add(self, value: int) -> None:
        new_node = TreeNode(value)
        if self.root is None:        # пустое дерево — новый узел становится корнем
            self.root = new_node
            return
        current = self.root
        while True:
            if value < current.value:        # меньше — налево
                if current.left is None:
                    current.left = new_node   # нашли пустое место
                    return
                current = current.left
            else:                            # больше или равно — направо
                if current.right is None:
                    current.right = new_node
                    return
                current = current.right
```

- **Сложность:** O(h), где h — высота дерева. Для сбалансированного дерева h ≈ log₂(n), для «вырожденного» (отсортированный ввод) h = n.

**Пример.** Вставляем `[50, 30, 70, 20, 40, 60, 80]`:
```
        50
       /  \
     30    70
    / \   /  \
  20  40 60  80
```
`30 < 50` → влево, `70 > 50` → вправо и т.д. Получается аккуратное дерево, потому что значения поданы в удачном порядке.

**Проблема порядка ввода.** Если вставлять уже отсортированные данные `[20, 30, 40, 50, ...]`, дерево «выродится» в список (каждый следующий больше → всегда вправо), и поиск станет O(n):
```
20
  \
   30
     \
      40
        \
         50
```
Решение этой проблемы — в [lab02_random.md](lab02_random.md) (метод `build_balanced`).

### Обходы дерева

Хотя в коде явный обход спрятан внутри визуализации, важно знать три классических обхода в глубину:

- **in-order** (лево → корень → право): для BST даёт значения **по возрастанию**.
- **pre-order** (корень → лево → право): для копирования/сериализации дерева.
- **post-order** (лево → право → корень): для удаления/освобождения дерева.

In-order рекурсивно:
```python
def in_order(node):
    if node is None:
        return
    in_order(node.left)
    print(node.value)        # для дерева выше выведет: 20 30 40 50 60 70 80
    in_order(node.right)
```

## Визуализация дерева (`print_tree`)

Рисует дерево сверху вниз с ветками `/` и `\`. Алгоритм в два этапа.

### Этап 1: `_collect_positions` — присвоить координаты

Рекурсивный **in-order обход** присваивает каждому узлу пару `(x, depth)`:

- `x` — порядковый номер при in-order обходе (горизонтальная позиция);
- `depth` — глубина узла (вертикальная позиция).

Поскольку in-order для BST идёт слева направо по возрастанию, узлы естественным образом раскладываются по горизонтали без наложений.

```python
    def _collect_positions(self, node, depth, counter, positions) -> None:
        if node is None:
            return
        self._collect_positions(node.left, depth + 1, counter, positions)   # сначала левое
        positions[node] = (counter[0], depth)   # (номер in-order, глубина)
        counter[0] += 1                          # счётчик в списке — чтобы менялся «по ссылке»
        self._collect_positions(node.right, depth + 1, counter, positions)  # потом правое
```

- **`counter` — это список из одного числа `[0]`**, а не просто `int`. Хитрость: целые числа в Python неизменяемы и передаются «по значению», а список — изменяемый объект, поэтому `counter[0] += 1` виден во всех рекурсивных вызовах. Это способ сделать общий «сквозной» счётчик через рекурсию.

### Этап 2: `print_tree` — нарисовать сетку символов

```python
    def print_tree(self) -> None:
        if self.root is None:
            print("Дерево пусто.")
            return

        positions: dict[TreeNode, tuple[int, int]] = {}
        self._collect_positions(self.root, 0, [0], positions)

        step = 4   # горизонтальный шаг между соседними узлами in-order
        margin = max(len(str(n.value)) for n in positions)   # запас под широкие числа
        height = max(depth for _, depth in positions.values()) + 1

        def center(n: TreeNode) -> int:
            x, _ = positions[n]
            return x * step + margin     # X-координата центра узла на экране

        rows = height * 2 - 1            # между уровнями узлов — строка под ветки
        width = max(center(n) for n in positions) + margin + 1
        grid = [[" "] * width for _ in custom_range(rows)]   # «холст» из пробелов

        for node, (_, depth) in positions.items():
            label = str(node.value)
            row = depth * 2              # узлы — на чётных строках
            col = center(node)
            start = col - (len(label) - 1) // 2   # центрируем подпись
            for i, ch in enumerate(label):
                grid[row][start + i] = ch         # «впечатываем» число в холст

            branch_row = row + 1         # нечётная строка под узлом — для веток
            if node.left is not None:
                grid[branch_row][(col + center(node.left)) // 2] = "/"
            if node.right is not None:
                grid[branch_row][(col + center(node.right)) // 2] = "\\"

        for line in grid:
            print("".join(line).rstrip())   # rstrip — убираем хвостовые пробелы
```

**Как это работает по шагам:**

1. Каждому узлу уже известны `(x, depth)`. Экранный X-центр = `x * step + margin`.
2. Узлы рисуются на **чётных** строках (`depth * 2`), ветки `/` `\` — на **нечётных** строках между ними.
3. `grid` — двумерный список символов («холст»), изначально весь из пробелов.
4. Каждая цифра числа «впечатывается» в нужную клетку.
5. Ветка ставится посередине между X-центром родителя и потомка.
6. `rstrip()` убирает лишние пробелы справа в каждой строке.

Результат:
```
        50
       /  \
     30    70
    / \   /  \
  20  40 60  80
```

Этот код **общий для lab02 и lab02_random**. Самописный `custom_range` (вместо запрещённого `range`) берётся из общего пакета — см. [common](common.md).

---

## Где это в проде

Эти три структуры — фундамент, на котором стоят системы, которые инженер эксплуатирует:

- **Связный список.** Список свободных блоков в аллокаторах памяти, цепочки бакетов в hash map ([lab05](lab05.md)), двусвязный список «свежести» в LRU-кэше ([lab08](lab08.md)), intrusive-списки в ядре Linux (`list_head`). Везде, где элементы часто вставляют и удаляют в середине, а доступ по индексу не нужен.
- **Очередь (FIFO).** Очереди задач у worker-пулов, буферизация входящих запросов, очереди сообщений (Kafka, RabbitMQ, SQS — концептуально это та же FIFO с гарантиями доставки). Канал в Go (`chan`) — по сути потокобезопасная очередь. Тот же FIFO — в обходе графа в ширину ([lab06](lab06.md)).
- **Дерево поиска (BST).** Прямое развитие идеи — **B-tree / B+-tree**, на которых построены индексы БД (PostgreSQL, MySQL): тот же принцип «меньше — влево, больше — вправо», но узел хранит не одно значение, а целую страницу диска, чтобы минимизировать обращения к медленному носителю. Упорядоченное хранение по ключу (`std::map` в C++, `sortedcontainers` в Python) и иерархии вроде дерева каталогов ФС — тоже отсюда.

---

## Параллельная реализация на Go

Связный список, очередь и BST реализованы на Go в пакете [`src/golang/dsa/lab02`](https://github.com/jtprogru/dsa-for-ops/tree/main/src/golang/dsa/lab02). ASCII-визуализация дерева заменена методом-обходом `InOrder()` (для BST он даёт значения по возрастанию — это удобно тестировать). Ниже — вставка в дерево поиска: меньшие значения уходят влево, остальные (`>=`) — вправо.

=== "Python"

    ```python
    def add(self, value: int) -> None:
        new_node = TreeNode(value)
        if self.root is None:
            self.root = new_node
            return
        current = self.root
        while True:
            if value < current.value:
                if current.left is None:
                    current.left = new_node
                    return
                current = current.left
            else:
                if current.right is None:
                    current.right = new_node
                    return
                current = current.right
    ```

=== "Go"

    ```go
    func (t *BinaryTree) Add(value int) {
        node := &TreeNode{Value: value}
        if t.Root == nil {
            t.Root = node
            return
        }
        current := t.Root
        for {
            if value < current.Value {
                if current.Left == nil {
                    current.Left = node
                    return
                }
                current = current.Left
            } else {
                if current.Right == nil {
                    current.Right = node
                    return
                }
                current = current.Right
            }
        }
    }
    ```
