import pytest

from labs.lab07 import (
    BinaryHeap,
    PriorityQueue,
    heap_sort,
    main,
    menu,
    top_k_largest,
    top_k_smallest,
)


def feed_input(monkeypatch, values):
    """Подменяет input() последовательностью значений."""
    inputs = iter(values)
    monkeypatch.setattr("builtins.input", lambda _="": next(inputs))


def is_valid_heap(data: list, kind: str) -> bool:
    """Проверяет свойство кучи напрямую по массиву (родитель vs потомки)."""
    n = len(data)
    for i in range(n):
        for child in (2 * i + 1, 2 * i + 2):
            if child < n:
                if kind == "min" and data[i] > data[child]:
                    return False
                if kind == "max" and data[i] < data[child]:
                    return False
    return True


DATASETS = [
    [5, 2, 9, 1, 7, 3, 8],
    [3, 1, 2],
    [42],
    [10, 10, 10, 5, 5],
    [9, 8, 7, 6, 5, 4, 3, 2, 1],
    [1, 2, 3, 4, 5, 6, 7, 8, 9],
    [-3, -1, -7, 4, 0, 2],
]


class TestHeapProperty:
    @pytest.mark.parametrize("data", DATASETS)
    @pytest.mark.parametrize("kind", ["min", "max"])
    def test_build_satisfies_heap_property(self, data, kind):
        heap = BinaryHeap(kind=kind, data=data)
        assert is_valid_heap(heap.as_list(), kind)

    @pytest.mark.parametrize("data", DATASETS)
    @pytest.mark.parametrize("kind", ["min", "max"])
    def test_push_keeps_heap_property(self, data, kind):
        heap = BinaryHeap(kind=kind)
        for value in data:
            heap.push(value)
            assert is_valid_heap(heap.as_list(), kind)

    @pytest.mark.parametrize("data", DATASETS)
    @pytest.mark.parametrize("kind", ["min", "max"])
    def test_pop_keeps_heap_property(self, data, kind):
        heap = BinaryHeap(kind=kind, data=data)
        while len(heap) > 0:
            heap.pop()
            assert is_valid_heap(heap.as_list(), kind)

    @pytest.mark.parametrize("data", DATASETS)
    def test_min_heap_peek_is_minimum(self, data):
        heap = BinaryHeap(kind="min", data=data)
        assert heap.peek() == min(data)

    @pytest.mark.parametrize("data", DATASETS)
    def test_max_heap_peek_is_maximum(self, data):
        heap = BinaryHeap(kind="max", data=data)
        assert heap.peek() == max(data)

    def test_invalid_kind_raises(self):
        with pytest.raises(ValueError):
            BinaryHeap(kind="weird")

    def test_pop_empty_raises(self):
        with pytest.raises(IndexError):
            BinaryHeap(kind="min").pop()

    def test_peek_empty_raises(self):
        with pytest.raises(IndexError):
            BinaryHeap(kind="min").peek()

    def test_does_not_mutate_input(self):
        original = [3, 1, 2]
        BinaryHeap(kind="min", data=original)
        assert original == [3, 1, 2]


class TestOrderedExtraction:
    @pytest.mark.parametrize("data", DATASETS)
    def test_min_heap_pops_ascending(self, data):
        heap = BinaryHeap(kind="min", data=data)
        out = [heap.pop() for _ in range(len(data))]
        assert out == sorted(data)

    @pytest.mark.parametrize("data", DATASETS)
    def test_max_heap_pops_descending(self, data):
        heap = BinaryHeap(kind="max", data=data)
        out = [heap.pop() for _ in range(len(data))]
        assert out == sorted(data, reverse=True)

    @pytest.mark.parametrize("data", DATASETS)
    def test_heap_sort_ascending(self, data):
        assert heap_sort(data) == sorted(data)

    @pytest.mark.parametrize("data", DATASETS)
    def test_heap_sort_descending(self, data):
        assert heap_sort(data, reverse=True) == sorted(data, reverse=True)

    def test_heap_sort_does_not_mutate_input(self):
        original = [3, 1, 2]
        heap_sort(original)
        assert original == [3, 1, 2]


class TestPriorityQueue:
    def test_max_order_pops_highest_priority_first(self):
        pq = PriorityQueue(order="max")
        pq.push("low", 1)
        pq.push("high", 10)
        pq.push("mid", 5)
        assert pq.pop() == "high"
        assert pq.pop() == "mid"
        assert pq.pop() == "low"

    def test_min_order_pops_lowest_priority_first(self):
        pq = PriorityQueue(order="min")
        pq.push("low", 1)
        pq.push("high", 10)
        pq.push("mid", 5)
        assert pq.pop() == "low"
        assert pq.pop() == "mid"
        assert pq.pop() == "high"

    def test_stable_fifo_on_equal_priority(self):
        # при равных приоритетах порядок вставки сохраняется (tie-breaker seq)
        pq = PriorityQueue(order="max")
        pq.push("first", 5)
        pq.push("second", 5)
        pq.push("third", 5)
        assert [pq.pop(), pq.pop(), pq.pop()] == ["first", "second", "third"]

    def test_peek_does_not_remove(self):
        pq = PriorityQueue(order="max")
        pq.push("a", 1)
        pq.push("b", 2)
        assert pq.peek() == "b"
        assert len(pq) == 2

    def test_items_are_not_compared(self):
        # элементы несравнимы между собой (dict), но приоритеты различны —
        # очередь не должна падать, сравнивая item
        pq = PriorityQueue(order="max")
        pq.push({"task": "a"}, 1)
        pq.push({"task": "b"}, 2)
        assert pq.pop() == {"task": "b"}

    def test_invalid_order_raises(self):
        with pytest.raises(ValueError):
            PriorityQueue(order="weird")

    def test_pop_empty_raises(self):
        with pytest.raises(IndexError):
            PriorityQueue().pop()

    def test_peek_empty_raises(self):
        with pytest.raises(IndexError):
            PriorityQueue().peek()


class TestTopK:
    @pytest.mark.parametrize(
        "data, k, expected",
        [
            ([5, 2, 9, 1, 7, 3, 8], 3, [9, 8, 7]),
            ([5, 2, 9, 1, 7, 3, 8], 1, [9]),
            ([10, 10, 10, 5, 5], 2, [10, 10]),
            ([-3, -1, -7, 4, 0, 2], 3, [4, 2, 0]),
        ],
    )
    def test_top_k_largest_known(self, data, k, expected):
        assert top_k_largest(data, k) == expected

    @pytest.mark.parametrize(
        "data, k, expected",
        [
            ([5, 2, 9, 1, 7, 3, 8], 3, [1, 2, 3]),
            ([5, 2, 9, 1, 7, 3, 8], 1, [1]),
            ([10, 10, 10, 5, 5], 2, [5, 5]),
            ([-3, -1, -7, 4, 0, 2], 3, [-7, -3, -1]),
        ],
    )
    def test_top_k_smallest_known(self, data, k, expected):
        assert top_k_smallest(data, k) == expected

    @pytest.mark.parametrize("data", DATASETS)
    def test_largest_matches_sorted(self, data):
        k = 3
        assert top_k_largest(data, k) == sorted(data, reverse=True)[:k]

    @pytest.mark.parametrize("data", DATASETS)
    def test_smallest_matches_sorted(self, data):
        k = 3
        assert top_k_smallest(data, k) == sorted(data)[:k]

    @pytest.mark.parametrize("data", DATASETS)
    def test_k_greater_than_len_returns_all_largest(self, data):
        k = len(data) + 5
        assert top_k_largest(data, k) == sorted(data, reverse=True)

    @pytest.mark.parametrize("data", DATASETS)
    def test_k_equal_len_returns_all(self, data):
        k = len(data)
        assert top_k_largest(data, k) == sorted(data, reverse=True)
        assert top_k_smallest(data, k) == sorted(data)

    @pytest.mark.parametrize("k", [0, -1, -10])
    def test_k_non_positive_returns_empty(self, k):
        assert top_k_largest([5, 2, 9, 1], k) == []
        assert top_k_smallest([5, 2, 9, 1], k) == []

    def test_empty_array(self):
        assert top_k_largest([], 3) == []
        assert top_k_smallest([], 3) == []


class TestMenu:
    def test_all_options_then_exit(self, monkeypatch, capsys):
        # 1 — кучи, 2 — очередь, 3+k — top-K, 4+value — push, 5 — новый массив,
        # x — неизвестный пункт, 0 — выход
        feed_input(monkeypatch, ["1", "2", "3", "3", "4", "42", "5", "x", "0"])
        menu()
        output = capsys.readouterr().out
        assert "heapsort" in output
        assert "Порядок выполнения" in output
        assert "Неизвестный пункт" in output
        assert "Выход" in output

    def test_exit_immediately(self, monkeypatch, capsys):
        feed_input(monkeypatch, ["0"])
        menu()
        assert "Выход" in capsys.readouterr().out

    def test_main_delegates_to_menu(self, monkeypatch, capsys):
        feed_input(monkeypatch, ["0"])
        main()
        assert "Выход" in capsys.readouterr().out
