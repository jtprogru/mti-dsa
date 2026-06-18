import pytest

from labs.lab01 import Stack, calculate_total_sum, custom_max, custom_max_index, generate_array, main, print_array


class TestMain:
    def test_runs_and_prints(self, capsys):
        main()
        output = capsys.readouterr().out
        assert "Максимум" in output
        assert "Вершина стека" in output


class TestCustomMax:
    def test_positive_numbers(self):
        assert custom_max([1, 5, 3, 9, 2]) == 9

    def test_negative_numbers(self):
        assert custom_max([-3, -1, -7, -2]) == -1

    def test_mixed_numbers(self):
        assert custom_max([98, 88, 74, 89, 87, 11, 15, 91, -5, 78]) == 98

    def test_single_element(self):
        assert custom_max([42]) == 42

    def test_all_equal(self):
        assert custom_max([5, 5, 5]) == 5

    def test_empty_array_raises(self):
        with pytest.raises(ValueError):
            custom_max([])


class TestCalculateTotalSum:
    def test_positive_numbers(self):
        assert calculate_total_sum([1, 2, 3, 4]) == 10

    def test_negative_numbers(self):
        assert calculate_total_sum([-1, -2, -3]) == -6

    def test_mixed_numbers(self):
        assert calculate_total_sum([98, 88, 74, 89, 87, 11, 15, 91, -5, 78]) == 626

    def test_empty_array(self):
        assert calculate_total_sum([]) == 0

    def test_single_element(self):
        assert calculate_total_sum([7]) == 7

    def test_zeros(self):
        assert calculate_total_sum([0, 0, 0]) == 0


class TestGenerateArray:
    def test_correct_size(self):
        arr = generate_array(10)
        assert len(arr) == 10

    def test_values_in_range(self):
        arr = generate_array(100)
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


class TestCustomMaxIndex:
    def test_max_at_end(self):
        assert custom_max_index([1, 2, 3, 9]) == 3

    def test_max_at_start(self):
        assert custom_max_index([9, 2, 3, 1]) == 0

    def test_max_in_middle(self):
        assert custom_max_index([1, 9, 3, 2]) == 1

    def test_negative_numbers(self):
        assert custom_max_index([-5, -1, -3]) == 1

    def test_single_element(self):
        assert custom_max_index([42]) == 0

    def test_first_occurrence_when_equal(self):
        assert custom_max_index([5, 5, 5]) == 0

    def test_empty_array_raises(self):
        with pytest.raises(ValueError):
            custom_max_index([])


class TestStack:
    def test_new_stack_is_empty(self):
        assert Stack().is_empty()

    def test_push_makes_non_empty(self):
        s = Stack()
        s.push(1)
        assert not s.is_empty()

    def test_peek_returns_last_pushed(self):
        s = Stack()
        s.push(10)
        s.push(20)
        assert s.peek() == 20

    def test_peek_does_not_remove(self):
        s = Stack()
        s.push(5)
        s.peek()
        assert not s.is_empty()

    def test_pop_returns_last_pushed(self):
        s = Stack()
        s.push(1)
        s.push(2)
        assert s.pop() == 2

    def test_pop_removes_element(self):
        s = Stack()
        s.push(1)
        s.pop()
        assert s.is_empty()

    def test_lifo_order(self):
        s = Stack()
        for v in [1, 2, 3]:
            s.push(v)
        assert [s.pop(), s.pop(), s.pop()] == [3, 2, 1]

    def test_pop_empty_raises(self):
        with pytest.raises(IndexError):
            Stack().pop()

    def test_peek_empty_raises(self):
        with pytest.raises(IndexError):
            Stack().peek()

    def test_print_stack_order(self, capsys):
        s = Stack()
        for v in [1, 2, 3]:
            s.push(v)
        s.print_stack()
        lines = capsys.readouterr().out.strip().splitlines()
        assert lines == ["3", "2", "1"]

    def test_print_stack_does_not_remove(self, capsys):
        s = Stack()
        s.push(42)
        s.print_stack()
        assert not s.is_empty()

    def test_print_empty_stack(self, capsys):
        Stack().print_stack()
        assert "пуст" in capsys.readouterr().out
