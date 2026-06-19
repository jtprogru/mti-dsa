import random
from collections.abc import Sequence

import pytest

from labs.common import (
    CustomRange,
    array_length,
    custom_range,
    generate_array,
    print_array,
    read_float,
    read_int,
)


def feed_input(monkeypatch, values):
    """Подменяет input() последовательностью значений."""
    inputs = iter(values)
    monkeypatch.setattr("builtins.input", lambda _="": next(inputs))


class TestArrayLength:
    def test_empty(self):
        assert array_length([]) == 0

    def test_non_empty(self):
        assert array_length([1, 2, 3]) == 3

    def test_single(self):
        assert array_length([42]) == 1

    def test_counts_any_elements(self):
        assert array_length(["a", None, 3, 3]) == 4


class TestGenerateArray:
    def test_correct_size(self):
        assert array_length(generate_array(10)) == 10

    def test_zero_size_is_empty(self):
        assert generate_array(0) == []

    def test_values_in_range(self):
        arr = generate_array(200)
        assert all(1 <= x <= 100 for x in arr)

    def test_returns_list(self):
        assert isinstance(generate_array(5), list)


class TestPrintArray:
    def test_prints_each_element(self, capsys):
        print_array([10, 20, 30])
        output = capsys.readouterr().out
        assert "[0] = 10" in output
        assert "[1] = 20" in output
        assert "[2] = 30" in output

    def test_empty_array_prints_nothing(self, capsys):
        print_array([])
        assert capsys.readouterr().out == ""

    def test_line_count_matches_array(self, capsys):
        print_array([1, 2, 3, 4, 5])
        lines = capsys.readouterr().out.strip().splitlines()
        assert len(lines) == 5


class TestCustomRange:
    """custom_range — псевдоним класса CustomRange, поэтому тестируем оба имени."""

    def test_alias_is_class(self):
        assert custom_range is CustomRange

    def test_is_a_sequence(self):
        assert isinstance(custom_range(3), Sequence)

    # --- порождаемая последовательность совпадает со встроенной range ---

    @pytest.mark.parametrize(
        "args",
        [
            (5,),
            (0,),
            (2, 7),
            (1, 10, 2),
            (10, 0, -1),
            (10, 0, -3),
            (5, 5),  # пустой: start == stop
            (7, 3),  # пустой: start > stop при шаге +1
            (0, 5, -1),  # пустой: шаг «не в ту сторону»
            (-5, 5, 2),  # отрицательный старт
        ],
    )
    def test_matches_builtin_range(self, args):
        assert list(custom_range(*args)) == list(range(*args))

    def test_zero_step_raises(self):
        with pytest.raises(ValueError):
            custom_range(0, 5, 0)

    # --- длина ---

    def test_len(self):
        assert len(custom_range(5)) == 5
        assert len(custom_range(0, 100, 5)) == 20
        assert len(custom_range(5, 5)) == 0

    def test_bool(self):
        assert bool(custom_range(3)) is True
        assert bool(custom_range(0)) is False

    # --- индексация ---

    def test_getitem(self):
        r = custom_range(0, 100, 5)
        assert r[0] == 0
        assert r[3] == 15
        assert r[-1] == 95

    def test_getitem_out_of_range(self):
        r = custom_range(5)
        with pytest.raises(IndexError):
            _ = r[5]
        with pytest.raises(IndexError):
            _ = r[-6]

    def test_slice_returns_custom_range(self):
        r = custom_range(0, 100, 5)
        sliced = r[2:5]
        assert isinstance(sliced, CustomRange)
        assert list(sliced) == [10, 15, 20]

    def test_slice_matches_builtin(self):
        r = custom_range(0, 50, 3)
        assert list(r[1:8:2]) == list(range(0, 50, 3)[1:8:2])

    # --- вхождение / поиск ---

    def test_contains_int(self):
        r = custom_range(0, 100, 5)
        assert (50 in r) is True
        assert (51 in r) is False

    def test_contains_non_int_falls_back(self):
        r = custom_range(0, 5)
        assert (2.0 in r) is True  # медленный путь, но True
        assert (2.5 in r) is False
        assert ("x" in r) is False

    def test_contains_empty(self):
        assert (0 in custom_range(5, 5)) is False

    def test_contains_negative_step(self):
        r = custom_range(10, 0, -2)  # [10, 8, 6, 4, 2]
        assert (6 in r) is True
        assert (5 in r) is False  # вне шага
        assert (0 in r) is False  # за границей

    def test_index(self):
        r = custom_range(0, 100, 5)
        assert r.index(15) == 3

    def test_index_missing_raises(self):
        with pytest.raises(ValueError):
            custom_range(0, 100, 5).index(7)

    def test_count(self):
        r = custom_range(0, 100, 5)
        assert r.count(15) == 1
        assert r.count(7) == 0

    # --- реверс ---

    def test_reversed(self):
        r = custom_range(0, 100, 5)
        assert list(reversed(r)) == list(reversed(range(0, 100, 5)))

    # --- равенство и хеш по порождаемой последовательности ---

    def test_eq_by_sequence(self):
        assert custom_range(0, 3, 2) == custom_range(0, 4, 2)  # оба дают [0, 2]
        assert custom_range(5) == custom_range(0, 5)

    def test_eq_different(self):
        assert custom_range(5) != custom_range(6)
        assert custom_range(0, 5) != custom_range(0, 5, 2)

    def test_eq_same_length_different_start(self):
        assert custom_range(0, 5) != custom_range(1, 6)  # длина 5, старт 0 ≠ 1

    def test_eq_empty_ranges(self):
        assert custom_range(5, 5) == custom_range(3, 3)  # обе пусты → равны

    def test_eq_single_element_ignores_step(self):
        assert custom_range(0, 1) == custom_range(0, 1, 5)  # обе дают [0]

    def test_eq_other_type(self):
        assert custom_range(5) != [0, 1, 2, 3, 4]

    def test_hash_consistent_with_eq(self):
        assert hash(custom_range(0, 3, 2)) == hash(custom_range(0, 4, 2))
        assert custom_range(0, 3, 2) in {custom_range(0, 4, 2)}

    def test_hash_empty_and_single(self):
        assert hash(custom_range(5, 5)) == hash(custom_range(0, 0))
        assert hash(custom_range(0, 1)) == hash(custom_range(0, 1, 5))

    # --- repr ---

    def test_repr(self):
        assert repr(custom_range(5)) == "CustomRange(0, 5)"
        assert repr(custom_range(1, 10, 2)) == "CustomRange(1, 10, 2)"

    # --- атрибуты ---

    def test_attributes(self):
        r = custom_range(2, 20, 3)
        assert (r.start, r.stop, r.step) == (2, 20, 3)

    # --- работает как drop-in последовательность ---

    def test_works_with_random_sample(self):
        sample = random.sample(custom_range(1, 100), 7)
        assert len(sample) == 7
        assert all(1 <= x < 100 for x in sample)

    def test_lazy_does_not_materialize(self):
        # Огромный диапазон создаётся мгновенно — память под список не выделяется.
        r = custom_range(10**18)
        assert len(r) == 10**18
        assert r[10**17] == 10**17


class TestReadInt:
    def test_valid(self, monkeypatch):
        feed_input(monkeypatch, ["7"])
        assert read_int("p: ") == 7

    def test_negative(self, monkeypatch):
        feed_input(monkeypatch, ["-5"])
        assert read_int("p: ") == -5

    def test_retries_until_valid(self, monkeypatch, capsys):
        feed_input(monkeypatch, ["abc", "9"])
        assert read_int("p: ") == 9
        assert "Это не целое число" in capsys.readouterr().out

    def test_empty_without_default_retries(self, monkeypatch, capsys):
        # default не задан -> пустой ввод считается неверным и запрос повторяется
        feed_input(monkeypatch, ["", "4"])
        assert read_int("p: ") == 4
        assert "Это не целое число" in capsys.readouterr().out

    def test_empty_returns_default(self, monkeypatch):
        feed_input(monkeypatch, [""])
        assert read_int("p: ", default=42) == 42

    def test_value_overrides_default(self, monkeypatch):
        feed_input(monkeypatch, ["8"])
        assert read_int("p: ", default=42) == 8

    def test_retries_then_default_on_empty(self, monkeypatch, capsys):
        feed_input(monkeypatch, ["xx", ""])
        assert read_int("p: ", default=3) == 3
        assert "Это не целое число" in capsys.readouterr().out


class TestReadFloat:
    def test_valid(self, monkeypatch):
        feed_input(monkeypatch, ["3.14"])
        assert read_float("p: ") == 3.14

    def test_accepts_int_text(self, monkeypatch):
        feed_input(monkeypatch, ["5"])
        assert read_float("p: ") == 5.0

    def test_retries_until_valid(self, monkeypatch, capsys):
        feed_input(monkeypatch, ["nan?", "2.5"])
        assert read_float("p: ") == 2.5
        assert "Это не число" in capsys.readouterr().out

    def test_empty_without_default_retries(self, monkeypatch, capsys):
        feed_input(monkeypatch, ["", "1.5"])
        assert read_float("p: ") == 1.5
        assert "Это не число" in capsys.readouterr().out

    def test_empty_returns_default(self, monkeypatch):
        feed_input(monkeypatch, [""])
        assert read_float("p: ", default=2.71) == 2.71

    def test_value_overrides_default(self, monkeypatch):
        feed_input(monkeypatch, ["9.0"])
        assert read_float("p: ", default=2.71) == 9.0
