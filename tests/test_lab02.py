import pytest

from labs.lab02 import BinaryTree, LinkedList, Queue, main


class TestMain:
    def test_runs_and_prints(self, capsys):
        main()
        output = capsys.readouterr().out
        assert "Связанный список" in output
        assert "Очередь" in output
        assert "дерево" in output.lower()


# custom_range живёт в labs/common и тестируется в tests/test_common.py.

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


# ─── LinkedList ──────────────────────────────────────────────────────────────


class TestLinkedList:
    def test_empty_list_has_no_head(self):
        assert LinkedList().head is None

    def test_add_single_node(self):
        ll = LinkedList()
        ll.add(42)
        assert ll.head.value == 42
        assert ll.head.next is None

    def test_add_preserves_order(self):
        ll = LinkedList()
        for v in [10, 20, 30]:
            ll.add(v)
        assert list_values(ll) == [10, 20, 30]

    def test_add_seven_nodes(self):
        ll = LinkedList()
        for v in [10, 20, 30, 40, 50, 60, 70]:
            ll.add(v)
        assert list_values(ll) == [10, 20, 30, 40, 50, 60, 70]

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

    def test_remove_tail(self):
        ll = LinkedList()
        for v in [1, 2, 3]:
            ll.add(v)
        ll.remove(3)
        assert list_values(ll) == [1, 2]

    def test_remove_only_first_occurrence(self):
        ll = LinkedList()
        for v in [5, 5, 5]:
            ll.add(v)
        ll.remove(5)
        assert list_values(ll) == [5, 5]

    def test_remove_nonexistent_does_not_raise(self):
        ll = LinkedList()
        ll.add(1)
        ll.remove(99)
        assert list_values(ll) == [1]

    def test_remove_from_empty_does_not_raise(self):
        ll = LinkedList()
        ll.remove(1)
        assert ll.head is None

    def test_print_list_output(self, capsys):
        ll = LinkedList()
        for v in [10, 20, 30]:
            ll.add(v)
        ll.print_list()
        lines = capsys.readouterr().out.strip().splitlines()
        assert lines == ["10", "20", "30"]

    def test_print_empty_list_prints_nothing(self, capsys):
        LinkedList().print_list()
        assert capsys.readouterr().out == ""


# ─── Queue ───────────────────────────────────────────────────────────────────


class TestQueue:
    def test_new_queue_is_empty(self):
        assert Queue().is_empty()

    def test_enqueue_makes_non_empty(self):
        q = Queue()
        q.enqueue(1)
        assert not q.is_empty()

    def test_peek_returns_front(self):
        q = Queue()
        q.enqueue(10)
        q.enqueue(20)
        assert q.peek() == 10

    def test_peek_does_not_remove(self):
        q = Queue()
        q.enqueue(1)
        q.peek()
        assert not q.is_empty()

    def test_dequeue_returns_front(self):
        q = Queue()
        q.enqueue(10)
        q.enqueue(20)
        assert q.dequeue() == 10

    def test_dequeue_removes_element(self):
        q = Queue()
        q.enqueue(1)
        q.dequeue()
        assert q.is_empty()

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


# ─── BinaryTree ──────────────────────────────────────────────────────────────


class TestBinaryTree:
    def test_new_tree_has_no_root(self):
        assert BinaryTree().root is None

    def test_add_root(self):
        bt = BinaryTree()
        bt.add(50)
        assert bt.root.value == 50

    def test_smaller_goes_left(self):
        bt = BinaryTree()
        bt.add(50)
        bt.add(30)
        assert bt.root.left.value == 30

    def test_larger_goes_right(self):
        bt = BinaryTree()
        bt.add(50)
        bt.add(70)
        assert bt.root.right.value == 70

    def test_bst_property_inorder_sorted(self):
        bt = BinaryTree()
        for v in [50, 30, 70, 20, 40, 60, 80]:
            bt.add(v)
        assert inorder(bt.root) == [20, 30, 40, 50, 60, 70, 80]

    def test_all_values_present_in_output(self, capsys):
        bt = BinaryTree()
        values = [50, 30, 70, 20, 40, 60, 80]
        for v in values:
            bt.add(v)
        bt.print_tree()
        output = capsys.readouterr().out
        for v in values:
            assert str(v) in output

    def test_print_empty_tree(self, capsys):
        BinaryTree().print_tree()
        assert "пуст" in capsys.readouterr().out

    def test_single_node_tree(self):
        bt = BinaryTree()
        bt.add(42)
        assert bt.root.left is None
        assert bt.root.right is None

    def test_equal_value_goes_right(self):
        bt = BinaryTree()
        bt.add(50)
        bt.add(50)
        assert bt.root.right.value == 50
