import pytest

from labs.lab08 import (
    LRUCache,
    Node,
    _parse_key,
    _read_int,
    demo_eviction,
    main,
    menu,
)


def feed_input(monkeypatch, values):
    """Подменяет input() последовательностью значений."""
    inputs = iter(values)
    monkeypatch.setattr("builtins.input", lambda _="": next(inputs))


class TestNode:
    def test_fields_default_none(self):
        n = Node()
        assert n.key is None
        assert n.value is None
        assert n.prev is None
        assert n.next is None

    def test_fields_set(self):
        n = Node("k", 42)
        assert n.key == "k"
        assert n.value == 42


class TestLRUCacheBasics:
    def test_invalid_capacity_raises(self):
        with pytest.raises(ValueError):
            LRUCache(0)
        with pytest.raises(ValueError):
            LRUCache(-1)

    def test_put_and_get(self):
        cache = LRUCache(2)
        cache.put("a", 1)
        assert cache.get("a") == 1

    def test_get_missing_returns_default(self):
        cache = LRUCache(2)
        assert cache.get("nope") is None
        assert cache.get("nope", -1) == -1

    def test_update_existing_value(self):
        cache = LRUCache(2)
        cache.put("a", 1)
        cache.put("a", 2)
        assert cache.get("a") == 2
        assert len(cache) == 1  # обновление не добавляет новый элемент

    def test_contains_and_dunder_contains(self):
        cache = LRUCache(2)
        cache.put("a", 1)
        assert cache.contains("a") is True
        assert cache.contains("b") is False
        assert ("a" in cache) is True
        assert ("b" in cache) is False

    def test_len(self):
        cache = LRUCache(3)
        assert len(cache) == 0
        cache.put(1, 1)
        cache.put(2, 2)
        assert len(cache) == 2

    def test_capacity_never_exceeded(self):
        cache = LRUCache(2)
        for i in range(5):
            cache.put(i, i)
        assert len(cache) == 2


class TestPeek:
    def test_peek_returns_value_without_refresh(self):
        # peek не должен менять порядок использования
        cache = LRUCache(2)
        cache.put(1, "a")
        cache.put(2, "b")  # порядок MRU->LRU: [2, 1]
        assert cache.peek(1) == "a"
        # 1 НЕ освежён -> при put(3) вытесняется именно 1 (он LRU)
        cache.put(3, "c")
        assert cache.contains(1) is False
        assert cache.contains(2) is True
        assert cache.contains(3) is True

    def test_peek_missing_returns_default(self):
        cache = LRUCache(2)
        assert cache.peek("x") is None
        assert cache.peek("x", "<нет>") == "<нет>"


class TestEvictionOrder:
    def test_evicts_least_recently_used_on_insert(self):
        cache = LRUCache(2)
        cache.put(1, "a")
        cache.put(2, "b")
        cache.put(3, "c")  # переполнение -> вытесняется 1 (LRU)
        assert cache.contains(1) is False
        assert cache.get(2) == "b"
        assert cache.get(3) == "c"

    def test_get_refreshes_and_changes_victim(self):
        cache = LRUCache(2)
        cache.put(1, "a")
        cache.put(2, "b")
        assert cache.get(1) == "a"  # 1 освежён -> теперь LRU это 2
        cache.put(3, "c")  # вытесняется 2, а не 1
        assert cache.contains(2) is False
        assert cache.contains(1) is True
        assert cache.contains(3) is True

    def test_update_refreshes_victim(self):
        cache = LRUCache(2)
        cache.put(1, "a")
        cache.put(2, "b")
        cache.put(1, "z")  # обновление освежает 1 -> LRU становится 2
        cache.put(3, "c")  # вытесняется 2
        assert cache.contains(2) is False
        assert cache.get(1) == "z"
        assert cache.contains(3) is True

    def test_full_sequence_survivors(self):
        # классический сценарий LRU из учебников
        cache = LRUCache(2)
        cache.put(1, 1)
        cache.put(2, 2)
        assert cache.get(1) == 1   # порядок [1, 2]
        cache.put(3, 3)            # вытесняет 2
        assert cache.get(2) is None
        cache.put(4, 4)            # вытесняет 1
        assert cache.get(1) is None
        assert cache.get(3) == 3
        assert cache.get(4) == 4

    @pytest.mark.parametrize(
        "ops, expected_keys_mru_to_lru",
        [
            # каждая операция: ("put", k, v) или ("get", k)
            ([("put", 1, "a"), ("put", 2, "b")], [2, 1]),
            ([("put", 1, "a"), ("put", 2, "b"), ("get", 1)], [1, 2]),
            (
                [("put", 1, "a"), ("put", 2, "b"), ("put", 3, "c")],
                [3, 2],  # 1 вытеснен
            ),
            (
                [("put", 1, "a"), ("put", 2, "b"), ("get", 1), ("put", 3, "c")],
                [3, 1],  # 2 вытеснен, 1 был освежён
            ),
        ],
    )
    def test_order_after_operations(self, ops, expected_keys_mru_to_lru):
        cache = LRUCache(2)
        for op in ops:
            if op[0] == "put":
                cache.put(op[1], op[2])
            else:
                cache.get(op[1])
        assert cache.keys_mru_to_lru() == expected_keys_mru_to_lru


class TestCapacityOne:
    def test_single_slot_replaces(self):
        cache = LRUCache(1)
        cache.put("a", 1)
        assert cache.get("a") == 1
        cache.put("b", 2)  # вытесняет a
        assert cache.contains("a") is False
        assert cache.get("b") == 2
        assert len(cache) == 1

    def test_single_slot_update_same_key(self):
        cache = LRUCache(1)
        cache.put("a", 1)
        cache.put("a", 2)
        assert cache.get("a") == 2
        assert len(cache) == 1


class TestKeysOrder:
    def test_keys_empty(self):
        cache = LRUCache(2)
        assert cache.keys_mru_to_lru() == []

    def test_keys_mru_first(self):
        cache = LRUCache(3)
        cache.put(1, 1)
        cache.put(2, 2)
        cache.put(3, 3)
        # последний вставленный — самый свежий (MRU) — идёт первым
        assert cache.keys_mru_to_lru() == [3, 2, 1]


class TestPrintCache:
    def test_print_non_empty(self, capsys):
        cache = LRUCache(2)
        cache.put(1, "x")
        cache.put(2, "y")
        cache.print_cache()
        out = capsys.readouterr().out
        assert "LRUCache" in out
        assert "2=y" in out
        assert "1=x" in out

    def test_print_empty(self, capsys):
        cache = LRUCache(2)
        cache.print_cache()
        assert "<пусто>" in capsys.readouterr().out


class TestParseKey:
    @pytest.mark.parametrize(
        "raw, expected",
        [("42", 42), ("-5", -5), ("hello", "hello"), ("0", 0)],
    )
    def test_parse(self, raw, expected):
        assert _parse_key(raw) == expected


class TestReadInt:
    def test_valid(self, monkeypatch):
        monkeypatch.setattr("builtins.input", lambda _="": "7")
        assert _read_int("p") == 7

    def test_retries_until_valid(self, monkeypatch, capsys):
        feed_input(monkeypatch, ["abc", "9"])
        assert _read_int("p") == 9
        assert "Это не целое число" in capsys.readouterr().out


class TestDemo:
    def test_demo_eviction(self, capsys):
        demo_eviction()
        out = capsys.readouterr().out
        assert "LRU" in out
        assert "вытесняется" in out
        assert "<промах>" in out  # get(2) после вытеснения


class TestMenu:
    def test_all_options_then_exit(self, monkeypatch, capsys):
        feed_input(
            monkeypatch,
            [
                "1", "a", "1",   # put a=1
                "2", "a",         # get a
                "3", "a",         # peek a
                "4",              # печать
                "5",              # демонстрация вытеснения
                "6", "2",         # пересоздать кэш ёмкости 2
                "x",              # неизвестный пункт
                "0",              # выход
            ],
        )
        menu()
        out = capsys.readouterr().out
        assert "put(a=1)" in out
        assert "Создан новый пустой кэш" in out
        assert "Неизвестный пункт" in out
        assert "Выход" in out

    def test_exit_immediately(self, monkeypatch, capsys):
        feed_input(monkeypatch, ["0"])
        menu()
        assert "Выход" in capsys.readouterr().out

    def test_main_delegates_to_menu(self, monkeypatch, capsys):
        feed_input(monkeypatch, ["0"])
        main()
        assert "Выход" in capsys.readouterr().out
