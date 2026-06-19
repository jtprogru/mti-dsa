import pytest

from labs.lab05 import (
    HashMapChaining,
    HashMapOpenAddr,
    _parse_key,
    demo_collisions,
    demo_resize,
    hash_int,
    hash_key,
    hash_str,
    main,
    menu,
)


def feed_input(monkeypatch, values):
    """Подменяет input() последовательностью значений."""
    inputs = iter(values)
    monkeypatch.setattr("builtins.input", lambda _="": next(inputs))


class TestHashFunctions:
    def test_hash_int_positive(self):
        assert hash_int(42) == 42

    def test_hash_int_zero(self):
        assert hash_int(0) == 0

    def test_hash_int_negative(self):
        assert hash_int(-7) == 7

    def test_hash_str_deterministic(self):
        assert hash_str("abc") == hash_str("abc")

    def test_hash_str_empty(self):
        assert hash_str("") == 0

    def test_hash_str_known_value(self):
        # h = ord('a')*31 + ord('b') = 97*31 + 98 = 3105
        assert hash_str("ab") == 97 * 31 + 98

    def test_hash_str_different_strings_differ(self):
        assert hash_str("abc") != hash_str("acb")

    def test_hash_key_dispatch_int(self):
        assert hash_key(15) == hash_int(15)

    def test_hash_key_dispatch_str(self):
        assert hash_key("key") == hash_str("key")

    def test_hash_key_unsupported_type_raises(self):
        with pytest.raises(TypeError):
            hash_key(3.14)


class TestHashMapChaining:
    def test_put_and_get(self):
        m = HashMapChaining()
        m.put("a", 1)
        assert m.get("a") == 1

    def test_get_missing_returns_default(self):
        m = HashMapChaining()
        assert m.get("nope") is None
        assert m.get("nope", -1) == -1

    def test_update_existing_key(self):
        m = HashMapChaining()
        m.put("a", 1)
        m.put("a", 2)
        assert m.get("a") == 2
        assert len(m) == 1

    def test_contains(self):
        m = HashMapChaining()
        m.put("a", 1)
        assert m.contains("a") is True
        assert m.contains("b") is False

    def test_delete_present(self):
        m = HashMapChaining()
        m.put("a", 1)
        assert m.delete("a") is True
        assert m.contains("a") is False
        assert len(m) == 0

    def test_delete_absent(self):
        m = HashMapChaining()
        assert m.delete("a") is False

    def test_delete_second_in_bucket(self):
        # 1 и 9 коллизируют в один бакет; удаляем не первый, а второй элемент
        m = HashMapChaining(capacity=8)
        m.put(1, "a")
        m.put(9, "b")
        assert m.delete(9) is True
        assert m.get(1) == "a"
        assert m.contains(9) is False

    def test_collision_keeps_both_keys(self):
        # 1, 9, 17 при capacity=8 дают один индекс
        m = HashMapChaining(capacity=8)
        m.put(1, "a")
        m.put(9, "b")
        m.put(17, "c")
        assert m.get(1) == "a"
        assert m.get(9) == "b"
        assert m.get(17) == "c"
        assert m.collisions == 2  # 9 и 17 легли в занятый бакет

    def test_load_factor(self):
        m = HashMapChaining(capacity=8)
        m.put(1, 1)
        m.put(2, 2)
        assert m.load_factor() == 2 / 8

    def test_autoresize_keeps_all_keys(self):
        m = HashMapChaining(capacity=8)
        i = 0
        while i < 7:  # 7/8 > 0.75 -> rehash
            m.put(i, i * 10)
            i += 1
        assert m._capacity == 16
        i = 0
        while i < 7:
            assert m.get(i) == i * 10
            i += 1

    def test_keys_and_items(self):
        m = HashMapChaining()
        m.put("a", 1)
        m.put("b", 2)
        assert sorted(m.keys()) == ["a", "b"]
        assert sorted(m.items()) == [("a", 1), ("b", 2)]

    def test_print_map(self, capsys):
        m = HashMapChaining(capacity=8)
        m.put(1, "x")
        m.put(9, "y")  # коллизия с 1
        m.print_map()
        out = capsys.readouterr().out
        assert "HashMapChaining" in out
        assert "1=x" in out
        assert "9=y" in out


class TestHashMapOpenAddr:
    def test_invalid_probe_raises(self):
        with pytest.raises(ValueError):
            HashMapOpenAddr(probe="quadratic")

    @pytest.mark.parametrize("probe", ["linear", "double"])
    def test_put_and_get(self, probe):
        m = HashMapOpenAddr(probe=probe)
        m.put("a", 1)
        assert m.get("a") == 1

    @pytest.mark.parametrize("probe", ["linear", "double"])
    def test_get_missing_returns_default(self, probe):
        m = HashMapOpenAddr(probe=probe)
        assert m.get("nope") is None
        assert m.get("nope", -1) == -1

    @pytest.mark.parametrize("probe", ["linear", "double"])
    def test_update_existing_key(self, probe):
        m = HashMapOpenAddr(probe=probe)
        m.put("a", 1)
        m.put("a", 2)
        assert m.get("a") == 2
        assert len(m) == 1

    @pytest.mark.parametrize("probe", ["linear", "double"])
    def test_collision_keeps_both_keys(self, probe):
        m = HashMapOpenAddr(capacity=8, probe=probe)
        m.put(1, "a")
        m.put(9, "b")  # коллизия с 1
        m.put(17, "c")  # коллизия с 1
        assert m.get(1) == "a"
        assert m.get(9) == "b"
        assert m.get(17) == "c"
        assert m.collisions > 0

    def test_contains(self):
        m = HashMapOpenAddr()
        m.put("a", 1)
        assert m.contains("a") is True
        assert m.contains("b") is False

    def test_delete_present(self):
        m = HashMapOpenAddr()
        m.put("a", 1)
        assert m.delete("a") is True
        assert m.contains("a") is False
        assert len(m) == 0

    def test_delete_absent(self):
        m = HashMapOpenAddr()
        assert m.delete("a") is False

    def test_tombstone_keeps_later_key_findable(self):
        # Ключевой тест: удаление через надгробие не должно «прятать» 9.
        m = HashMapOpenAddr(capacity=8, probe="linear")
        m.put(1, "a")
        m.put(9, "b")  # коллизия -> следующий слот
        assert m.delete(1) is True  # на месте 1 теперь надгробие
        assert m.get(9) == "b"  # 9 всё ещё находится сквозь надгробие
        assert m._tombstones == 1

    def test_tombstone_slot_is_reused(self):
        m = HashMapOpenAddr(capacity=8, probe="linear")
        m.put(1, "a")
        m.put(9, "b")
        m.delete(1)  # надгробие на домашнем слоте ключей 1/9/17
        m.put(17, "c")  # проба пройдёт надгробие и переиспользует его
        assert m.get(17) == "c"
        assert m._tombstones == 0

    def test_autoresize_drops_tombstones(self):
        m = HashMapOpenAddr(capacity=8, probe="linear")
        m.put(1, "a")
        m.delete(1)  # одно надгробие
        # доводим до порога 0.5 -> resize, надгробия отбрасываются
        m.put(2, "b")
        m.put(3, "c")
        m.put(4, "d")
        assert m._capacity == 16
        assert m._tombstones == 0
        assert m.get(2) == "b"
        assert m.get(3) == "c"
        assert m.get(4) == "d"

    def test_load_factor(self):
        m = HashMapOpenAddr(capacity=8)
        m.put(1, 1)
        assert m.load_factor() == 1 / 8

    def test_keys_and_items(self):
        m = HashMapOpenAddr()
        m.put("a", 1)
        m.put("b", 2)
        assert sorted(m.keys()) == ["a", "b"]
        assert sorted(m.items()) == [("a", 1), ("b", 2)]

    def test_print_map_shows_value_empty_and_deleted(self, capsys):
        m = HashMapOpenAddr(capacity=8, probe="linear")
        m.put(1, "x")
        m.put(9, "y")
        m.delete(1)  # надгробие
        m.print_map()
        out = capsys.readouterr().out
        assert "HashMapOpenAddr(linear)" in out
        assert "9=y" in out
        assert "<deleted>" in out
        assert "[0] ." in out  # пустой слот


class TestParseKey:
    def test_int(self):
        assert _parse_key("42") == 42

    def test_negative_int(self):
        assert _parse_key("-5") == -5

    def test_string(self):
        assert _parse_key("hello") == "hello"


class TestDemos:
    def test_demo_collisions(self, capsys):
        demo_collisions()
        out = capsys.readouterr().out
        assert "коллизия" in out
        assert "HashMapChaining" in out
        assert "HashMapOpenAddr(linear)" in out
        assert "HashMapOpenAddr(double)" in out

    def test_demo_resize(self, capsys):
        demo_resize()
        out = capsys.readouterr().out
        assert "capacity вырос" in out
        assert "rehash" in out


class TestMenu:
    def test_all_options_then_exit(self, monkeypatch, capsys):
        feed_input(
            monkeypatch,
            [
                "1",
                "5",
                "50",  # добавить пару 5=50
                "2",
                "5",  # получить по ключу
                "3",
                "5",  # удалить ключ
                "4",  # напечатать таблицы
                "5",  # демонстрация коллизий
                "6",  # демонстрация resize
                "x",  # неизвестный пункт
                "0",  # выход
            ],
        )
        menu()
        out = capsys.readouterr().out
        assert "Добавлено: 5=50" in out
        assert "удалён" in out
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
