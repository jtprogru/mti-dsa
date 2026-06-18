"""
Задания (вариант со случайными данными):

1. Связанный список заполняется случайными значениями.
2. Очередь на основе связанного списка заполняется случайными значениями.
3. Бинарное дерево строится так, чтобы его форма НЕ зависела от
   последовательности вводимых значений:
     - сначала печатаем дерево, построенное вставкой в случайном порядке
       (форма зависит от порядка ввода);
     - затем — дерево, построенное из тех же значений, но отсортированных
       и вставленных «серединой вперёд» (сбалансированное, форма одинакова
       при любом исходном порядке).
"""

import random

from labs.common import custom_range


class Node:
    def __init__(self, value: int) -> None:
        self.value: int = value
        self.next: "Node | None" = None


class LinkedList:
    def __init__(self) -> None:
        self.head: Node | None = None

    def add(self, value: int) -> None:
        new_node = Node(value)
        if self.head is None:
            self.head = new_node
            return
        current = self.head
        while current.next is not None:
            current = current.next
        current.next = new_node

    def remove(self, value: int) -> None:
        if self.head is None:
            return
        if self.head.value == value:
            self.head = self.head.next
            return
        current = self.head
        while current.next is not None:
            if current.next.value == value:
                current.next = current.next.next
                return
            current = current.next

    def print_list(self) -> None:
        current = self.head
        while current is not None:
            print(current.value)
            current = current.next


class Queue:
    def __init__(self) -> None:
        self._head: Node | None = None  # front — откуда извлекаем
        self._tail: Node | None = None  # back  — куда добавляем

    def is_empty(self) -> bool:
        return self._head is None

    def enqueue(self, value: int) -> None:
        new_node = Node(value)
        if self._tail is None:
            self._head = new_node
            self._tail = new_node
            return
        self._tail.next = new_node
        self._tail = new_node

    def dequeue(self) -> int:
        if self.is_empty():
            raise IndexError("Очередь пуста, невозможно извлечь элемент.")
        value = self._head.value
        self._head = self._head.next
        if self._head is None:
            self._tail = None
        return value

    def peek(self) -> int:
        if self.is_empty():
            raise IndexError("Очередь пуста, невозможно получить значение.")
        return self._head.value

    def print_queue(self) -> None:
        if self.is_empty():
            print("Очередь пуста.")
            return
        current = self._head
        while current is not None:
            print(current.value)
            current = current.next


class TreeNode:
    def __init__(self, value: int) -> None:
        self.value: int = value
        self.left: "TreeNode | None" = None
        self.right: "TreeNode | None" = None


class BinaryTree:
    def __init__(self) -> None:
        self.root: TreeNode | None = None

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

    def build_balanced(self, values: list[int]) -> None:
        """Строит сбалансированное дерево из значений.

        Значения сортируются, затем серединой массива выбирается корень и
        рекурсивно вставляются левая и правая половины. Результат не зависит
        от исходного порядка values.
        """
        ordered = sorted(values)

        def insert_middle(lo: int, hi: int) -> None:
            if lo > hi:
                return
            mid = (lo + hi) // 2
            self.add(ordered[mid])
            insert_middle(lo, mid - 1)
            insert_middle(mid + 1, hi)

        insert_middle(0, len(ordered) - 1)

    def _collect_positions(
        self,
        node: "TreeNode | None",
        depth: int,
        counter: list[int],
        positions: "dict[TreeNode, tuple[int, int]]",
    ) -> None:
        if node is None:
            return
        self._collect_positions(node.left, depth + 1, counter, positions)
        positions[node] = (counter[0], depth)  # (порядковый номер in-order, глубина)
        counter[0] += 1
        self._collect_positions(node.right, depth + 1, counter, positions)

    def print_tree(self) -> None:
        if self.root is None:
            print("Дерево пусто.")
            return

        positions: dict[TreeNode, tuple[int, int]] = {}
        self._collect_positions(self.root, 0, [0], positions)

        step = 4  # горизонтальный шаг между соседними узлами in-order-обхода
        margin = max(len(str(n.value)) for n in positions)
        height = max(depth for _, depth in positions.values()) + 1

        def center(n: TreeNode) -> int:
            x, _ = positions[n]
            return x * step + margin

        rows = height * 2 - 1
        width = max(center(n) for n in positions) + margin + 1
        grid = [[" "] * width for _ in custom_range(rows)]

        for node, (_, depth) in positions.items():
            label = str(node.value)
            row = depth * 2
            col = center(node)
            start = col - (len(label) - 1) // 2
            for i, ch in enumerate(label):
                grid[row][start + i] = ch

            branch_row = row + 1
            if node.left is not None:
                grid[branch_row][(col + center(node.left)) // 2] = "/"
            if node.right is not None:
                grid[branch_row][(col + center(node.right)) // 2] = "\\"

        for line in grid:
            print("".join(line).rstrip())


def main() -> None:
    # Связанный список
    print("=" * 30)
    print("Связанный список (случайные значения):")
    list_values = random.sample(custom_range(1, 100), 7)
    print("Сгенерировано:", list_values)
    ll = LinkedList()
    for v in list_values:
        ll.add(v)
    ll.print_list()
    victim = random.choice(list_values)
    print(f"Удаляем случайный узел ({victim}):")
    ll.remove(victim)
    ll.print_list()

    # Очередь
    print("=" * 30)
    print("Очередь (случайные значения):")
    queue_values = random.sample(custom_range(1, 100), 4)
    print("Сгенерировано:", queue_values)
    q = Queue()
    print("Пустая?", q.is_empty())
    for v in queue_values:
        q.enqueue(v)
    print("После заполнения — пустая?", q.is_empty())
    print("Первый элемент (peek):", q.peek())
    print("Содержимое очереди:")
    q.print_queue()
    print("Извлечено (dequeue):", q.dequeue())
    print("Новый первый:", q.peek())

    # Бинарное дерево
    print("=" * 30)
    tree_values = random.sample(custom_range(1, 100), 7)
    print("Случайные значения для дерева:", tree_values)

    print("-" * 30)
    print("До сортировки (вставка в случайном порядке — форма зависит от ввода):")
    bt_raw = BinaryTree()
    for v in tree_values:
        bt_raw.add(v)
    bt_raw.print_tree()

    print("-" * 30)
    print("После сортировки (сбалансированное — форма не зависит от ввода):")
    bt_balanced = BinaryTree()
    bt_balanced.build_balanced(tree_values)
    bt_balanced.print_tree()
    print("=" * 30)


if __name__ == "__main__":
    main()
