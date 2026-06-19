import math
import random

import pytest

from labs.lab02_random import BinaryTree, LinkedList, Queue, main

# ─── helpers ─────────────────────────────────────────────────────────────────


def list_values(ll: LinkedList) -> list[int]:
    values = []
    current = ll.head
    while current is not None:
        values.append(current.value)
        current = current.next
    return values


def queue_values(q: Queue) -> list[int]:
    values = []
    current = q._head
    while current is not None:
        values.append(current.value)
        current = current.next
    return values


def inorder(node) -> list[int]:
    if node is None:
        return []
    return inorder(node.left) + [node.value] + inorder(node.right)


def height(node) -> int:
    if node is None:
        return 0
    return 1 + max(height(node.left), height(node.right))


def shape(node):
    """Структурное представление дерева — для сравнения формы."""
    if node is None:
        return None
    return (node.value, shape(node.left), shape(node.right))


# custom_range живёт в labs/common и тестируется в tests/test_common.py.


# ─── LinkedList ──────────────────────────────────────────────────────────────


class TestLinkedList:
    def test_empty_list_has_no_head(self):
        assert LinkedList().head is None

    def test_add_preserves_order(self):
        ll = LinkedList()
        for v in [10, 20, 30]:
            ll.add(v)
        assert list_values(ll) == [10, 20, 30]

    def test_remove_head(self):
        ll = LinkedList()
        for v in [1, 2, 3]:
            ll.add(v)
        ll.remove(1)
        assert list_values(ll) == [2, 3]

    def test_remove_middle(self):
        ll = LinkedList()
        for v in [1, 2, 3]:
            ll.add(v)
        ll.remove(2)
        assert list_values(ll) == [1, 3]

    def test_remove_nonexistent_does_not_raise(self):
        ll = LinkedList()
        ll.add(1)
        ll.remove(99)
        assert list_values(ll) == [1]

    def test_remove_from_empty_does_not_raise(self):
        ll = LinkedList()
        ll.remove(1)
        assert ll.head is None

    def test_remove_tail(self):
        ll = LinkedList()
        for v in [1, 2, 3]:
            ll.add(v)
        ll.remove(3)
        assert list_values(ll) == [1, 2]

    def test_print_list_output(self, capsys):
        ll = LinkedList()
        for v in [10, 20, 30]:
            ll.add(v)
        ll.print_list()
        lines = capsys.readouterr().out.strip().splitlines()
        assert lines == ["10", "20", "30"]


# ─── Queue ───────────────────────────────────────────────────────────────────


class TestQueue:
    def test_new_queue_is_empty(self):
        assert Queue().is_empty()

    def test_peek_returns_front(self):
        q = Queue()
        q.enqueue(10)
        q.enqueue(20)
        assert q.peek() == 10

    def test_fifo_order(self):
        q = Queue()
        for v in [1, 2, 3]:
            q.enqueue(v)
        assert [q.dequeue(), q.dequeue(), q.dequeue()] == [1, 2, 3]

    def test_tail_updated_after_dequeue_to_empty(self):
        q = Queue()
        q.enqueue(1)
        q.dequeue()
        q.enqueue(2)
        assert q.peek() == 2

    def test_dequeue_empty_raises(self):
        with pytest.raises(IndexError):
            Queue().dequeue()

    def test_peek_empty_raises(self):
        with pytest.raises(IndexError):
            Queue().peek()

    def test_print_queue_order(self, capsys):
        q = Queue()
        for v in [10, 20, 30]:
            q.enqueue(v)
        q.print_queue()
        lines = capsys.readouterr().out.strip().splitlines()
        assert lines == ["10", "20", "30"]

    def test_print_empty_queue(self, capsys):
        Queue().print_queue()
        assert "пуст" in capsys.readouterr().out


# ─── BinaryTree (вставка по порядку) ──────────────────────────────────────────


class TestBinaryTreeAdd:
    def test_bst_property_inorder_sorted(self):
        bt = BinaryTree()
        for v in [50, 30, 70, 20, 40, 60, 80]:
            bt.add(v)
        assert inorder(bt.root) == [20, 30, 40, 50, 60, 70, 80]

    def test_smaller_goes_left_larger_goes_right(self):
        bt = BinaryTree()
        bt.add(50)
        bt.add(30)
        bt.add(70)
        assert bt.root.left.value == 30
        assert bt.root.right.value == 70

    def test_print_empty_tree(self, capsys):
        BinaryTree().print_tree()
        assert "пуст" in capsys.readouterr().out


# ─── BinaryTree.build_balanced ────────────────────────────────────────────────


class TestBuildBalanced:
    def test_inorder_still_sorted(self):
        bt = BinaryTree()
        bt.build_balanced([50, 30, 70, 20, 40, 60, 80])
        assert inorder(bt.root) == [20, 30, 40, 50, 60, 70, 80]

    def test_middle_element_is_root(self):
        bt = BinaryTree()
        bt.build_balanced([20, 30, 40, 50, 60, 70, 80])
        assert bt.root.value == 50  # середина отсортированного массива из 7

    def test_shape_independent_of_input_order(self):
        values = [20, 30, 40, 50, 60, 70, 80]
        reference = None
        for _ in range(20):
            shuffled = values[:]
            random.shuffle(shuffled)
            bt = BinaryTree()
            bt.build_balanced(shuffled)
            if reference is None:
                reference = shape(bt.root)
            else:
                assert shape(bt.root) == reference

    def test_height_is_minimal(self):
        # сбалансированное дерево из n узлов имеет высоту floor(log2(n)) + 1
        for n in [1, 2, 3, 7, 8, 15, 31, 50]:
            values = list(range(n))
            bt = BinaryTree()
            bt.build_balanced(values)
            assert height(bt.root) == math.floor(math.log2(n)) + 1

    def test_all_values_present(self):
        values = [5, 1, 9, 3, 7, 2, 8, 4, 6]
        bt = BinaryTree()
        bt.build_balanced(values)
        assert sorted(inorder(bt.root)) == sorted(values)

    def test_empty_values(self):
        bt = BinaryTree()
        bt.build_balanced([])
        assert bt.root is None

    def test_single_value(self):
        bt = BinaryTree()
        bt.build_balanced([42])
        assert bt.root.value == 42
        assert bt.root.left is None
        assert bt.root.right is None

    def test_all_values_in_print_output(self, capsys):
        values = [50, 30, 70, 20, 40, 60, 80]
        bt = BinaryTree()
        bt.build_balanced(values)
        bt.print_tree()
        output = capsys.readouterr().out
        for v in values:
            assert str(v) in output


class TestMain:
    def test_runs_and_prints(self, capsys):
        main()
        output = capsys.readouterr().out
        assert "Связанный список" in output
        assert "Очередь" in output
        assert "сбалансированное" in output.lower()
