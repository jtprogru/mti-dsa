from labs.lab04 import (
    array_length,
    binary_search,
    binary_search_sorted,
    build_sorted_sequence,
    generate_array,
    insert_sorted,
    linear_all_indices,
    linear_contains,
    linear_count,
    linear_first_index,
    main,
    menu,
    print_array,
    read_sorted_sequence,
)


def feed_input(monkeypatch, values):
    """Подменяет input() последовательностью значений."""
    inputs = iter(values)
    monkeypatch.setattr("builtins.input", lambda _="": next(inputs))


class TestGenerateArray:
    def test_correct_size(self):
        assert len(generate_array(10)) == 10

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


class TestLinearContains:
    def test_present(self):
        assert linear_contains([5, 1, 9, 3], 9) is True

    def test_absent(self):
        assert linear_contains([5, 1, 9, 3], 7) is False

    def test_empty(self):
        assert linear_contains([], 1) is False

    def test_first_element(self):
        assert linear_contains([42, 1, 2], 42) is True

    def test_last_element(self):
        assert linear_contains([1, 2, 42], 42) is True


class TestLinearFirstIndex:
    def test_first_occurrence(self):
        assert linear_first_index([5, 1, 5, 3], 5) == 0

    def test_in_middle(self):
        assert linear_first_index([9, 8, 1, 7], 1) == 2

    def test_absent_returns_minus_one(self):
        assert linear_first_index([1, 2, 3], 9) == -1

    def test_empty_returns_minus_one(self):
        assert linear_first_index([], 1) == -1


class TestLinearAllIndices:
    def test_multiple_occurrences(self):
        assert linear_all_indices([5, 1, 5, 3, 5], 5) == [0, 2, 4]

    def test_single_occurrence(self):
        assert linear_all_indices([9, 8, 1], 1) == [2]

    def test_absent_returns_minus_one(self):
        assert linear_all_indices([1, 2, 3], 9) == -1

    def test_empty_returns_minus_one(self):
        assert linear_all_indices([], 1) == -1


class TestLinearCount:
    def test_multiple_occurrences(self):
        assert linear_count([5, 1, 5, 3, 5], 5) == 3

    def test_single_occurrence(self):
        assert linear_count([9, 8, 1], 1) == 1

    def test_absent_returns_zero(self):
        assert linear_count([1, 2, 3], 9) == 0

    def test_empty_returns_zero(self):
        assert linear_count([], 1) == 0


class TestBinarySearch:
    def test_found_in_middle(self):
        assert binary_search([1, 2, 3, 4, 5], 3) == 2

    def test_found_at_start(self):
        assert binary_search([1, 2, 3, 4, 5], 1) == 0

    def test_found_at_end(self):
        assert binary_search([1, 2, 3, 4, 5], 5) == 4

    def test_absent_returns_minus_one(self):
        assert binary_search([1, 2, 3, 4, 5], 6) == -1

    def test_absent_in_gap(self):
        assert binary_search([1, 3, 5, 7], 4) == -1

    def test_empty_returns_minus_one(self):
        assert binary_search([], 1) == -1

    def test_single_element_present(self):
        assert binary_search([42], 42) == 0

    def test_single_element_absent(self):
        assert binary_search([42], 7) == -1

    def test_matches_index_on_random(self):
        arr = sorted(generate_array(50))
        target = arr[len(arr) // 2]
        idx = binary_search(arr, target)
        assert arr[idx] == target


class TestBinarySearchSorted:
    def test_sorts_then_finds(self):
        idx, sorted_arr = binary_search_sorted([5, 2, 9, 1, 7], 9)
        assert sorted_arr == [1, 2, 5, 7, 9]
        assert sorted_arr[idx] == 9

    def test_absent(self):
        idx, sorted_arr = binary_search_sorted([5, 2, 9, 1, 7], 3)
        assert idx == -1
        assert sorted_arr == [1, 2, 5, 7, 9]

    def test_does_not_mutate_input(self):
        original = [3, 1, 2]
        binary_search_sorted(original, 2)
        assert original == [3, 1, 2]


class TestInsertSorted:
    def test_into_empty(self):
        assert insert_sorted([], 5) == [5]

    def test_at_start(self):
        assert insert_sorted([2, 4, 6], 1) == [1, 2, 4, 6]

    def test_in_middle(self):
        assert insert_sorted([1, 2, 6], 4) == [1, 2, 4, 6]

    def test_at_end(self):
        assert insert_sorted([1, 2, 3], 9) == [1, 2, 3, 9]

    def test_duplicate(self):
        assert insert_sorted([1, 2, 2, 3], 2) == [1, 2, 2, 2, 3]

    def test_does_not_mutate_input(self):
        original = [1, 3, 5]
        insert_sorted(original, 4)
        assert original == [1, 3, 5]


class TestBuildSortedSequence:
    def test_unsorted_input(self):
        assert build_sorted_sequence([5, 2, 9, 1, 7]) == [1, 2, 5, 7, 9]

    def test_already_sorted(self):
        assert build_sorted_sequence([1, 2, 3]) == [1, 2, 3]

    def test_reverse_sorted(self):
        assert build_sorted_sequence([4, 3, 2, 1]) == [1, 2, 3, 4]

    def test_with_duplicates(self):
        assert build_sorted_sequence([3, 1, 3, 1, 2]) == [1, 1, 2, 3, 3]

    def test_empty(self):
        assert build_sorted_sequence([]) == []

    def test_matches_builtin_on_random(self):
        arr = generate_array(50)
        assert build_sorted_sequence(arr) == sorted(arr)


class TestArrayLength:
    def test_empty(self):
        assert array_length([]) == 0

    def test_non_empty(self):
        assert array_length([1, 2, 3]) == 3

    def test_single(self):
        assert array_length([42]) == 1


class TestReadSortedSequence:
    def test_sorts_input(self, monkeypatch):
        inputs = iter(["5", "2", "9", "1", "7"])
        monkeypatch.setattr("builtins.input", lambda _="": next(inputs))
        assert read_sorted_sequence(5) == [1, 2, 5, 7, 9]

    def test_already_sorted_input(self, monkeypatch):
        inputs = iter(["1", "2", "3"])
        monkeypatch.setattr("builtins.input", lambda _="": next(inputs))
        assert read_sorted_sequence(3) == [1, 2, 3]

    def test_with_duplicates(self, monkeypatch):
        inputs = iter(["3", "1", "3", "2"])
        monkeypatch.setattr("builtins.input", lambda _="": next(inputs))
        assert read_sorted_sequence(4) == [1, 2, 3, 3]

    def test_invalid_input_is_retried(self, monkeypatch, capsys):
        # "foo" не считается за число и не уменьшает счётчик оставшихся
        inputs = iter(["foo", "2", "1"])
        monkeypatch.setattr("builtins.input", lambda _="": next(inputs))
        assert read_sorted_sequence(2) == [1, 2]
        assert "Это не целое число" in capsys.readouterr().out

    def test_shows_running_sequence(self, monkeypatch, capsys):
        inputs = iter(["3", "1", "2"])
        monkeypatch.setattr("builtins.input", lambda _="": next(inputs))
        read_sorted_sequence(3)
        output = capsys.readouterr().out
        # после каждого ввода печатается текущее отсортированное состояние
        assert "[3]" in output
        assert "[1, 3]" in output
        assert "[1, 2, 3]" in output

    def test_default_count_consumes_ten(self, monkeypatch):
        inputs = iter([str(v) for v in range(10, 0, -1)])
        monkeypatch.setattr("builtins.input", lambda _="": next(inputs))
        assert read_sorted_sequence() == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]


class TestMenu:
    def test_all_options_then_exit(self, monkeypatch, capsys):
        feed_input(
            monkeypatch,
            [
                # сначала делаем массив детерминированным: [1..10]
                "3",
                "1",
                "2",
                "3",
                "4",
                "5",
                "6",
                "7",
                "8",
                "9",
                "10",
                "1",
                "5",  # поиск перебором + искомое число
                "2",
                "5",  # бинарный поиск: элемент найден
                "2",
                "99",  # бинарный поиск: элемент не найден
                "4",
                "5",  # поиск во введённой: найден
                "4",
                "99",  # поиск во введённой: не найден
                "5",  # новый массив
                "x",  # неизвестный пункт
                "0",  # выход
            ],
        )
        menu()
        output = capsys.readouterr().out
        assert "Итоговая отсортированная последовательность" in output
        assert "Содержится" in output
        assert "Элемент найден на индексе" in output
        assert "Элемент не найден" in output
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
