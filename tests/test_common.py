import pytest

from labs.common import array_length, custom_range, generate_array, print_array


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
    def test_single_arg_matches_builtin(self):
        assert custom_range(5) == list(range(5))

    def test_single_arg_zero_is_empty(self):
        assert custom_range(0) == []

    def test_start_stop(self):
        assert custom_range(2, 7) == list(range(2, 7))

    def test_start_stop_step(self):
        assert custom_range(1, 10, 2) == list(range(1, 10, 2))

    def test_negative_step(self):
        assert custom_range(10, 0, -1) == list(range(10, 0, -1))

    def test_negative_step_with_step_size(self):
        assert custom_range(10, 0, -3) == list(range(10, 0, -3))

    def test_empty_when_start_ge_stop(self):
        assert custom_range(5, 5) == []
        assert custom_range(7, 3) == []

    def test_empty_when_negative_step_wrong_direction(self):
        assert custom_range(0, 5, -1) == []

    def test_returns_list(self):
        assert isinstance(custom_range(3), list)

    def test_zero_step_raises(self):
        with pytest.raises(ValueError):
            custom_range(0, 5, 0)
