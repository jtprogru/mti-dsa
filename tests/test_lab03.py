import pytest

from labs.lab03 import (
    bubble_sort,
    compare_swaps,
    generate_array,
    get_index_min_element,
    get_min_element,
    insertion_sort,
    main,
    menu,
    print_array,
    print_comparison,
    quick_sort,
    selection_sort,
    selection_sort_with_min,
)


def feed_input(monkeypatch, values):
    """Подменяет input() последовательностью значений."""
    inputs = iter(values)
    monkeypatch.setattr("builtins.input", lambda _="": next(inputs))


SORTERS = [
    selection_sort,
    selection_sort_with_min,
    insertion_sort,
    bubble_sort,
    quick_sort,
]


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


class TestGetMinElement:
    def test_positive_numbers(self):
        assert get_min_element([5, 1, 9, 3]) == 1

    def test_negative_numbers(self):
        assert get_min_element([-3, -1, -7, -2]) == -7

    def test_min_at_end(self):
        assert get_min_element([9, 8, 7, 1]) == 1

    def test_single_element(self):
        assert get_min_element([42]) == 42

    def test_all_equal(self):
        assert get_min_element([5, 5, 5]) == 5

    def test_empty_array_raises(self):
        with pytest.raises(ValueError):
            get_min_element([])


class TestGetIndexMinElement:
    def test_min_at_start(self):
        assert get_index_min_element([1, 2, 3]) == 0

    def test_min_at_end(self):
        assert get_index_min_element([9, 8, 1]) == 2

    def test_min_in_middle(self):
        assert get_index_min_element([9, 1, 3]) == 1

    def test_first_occurrence_when_equal(self):
        assert get_index_min_element([5, 5, 5]) == 0

    def test_start_offset_skips_prefix(self):
        # минимум всего массива (1) на индексе 0, но ищем с позиции 1
        assert get_index_min_element([1, 7, 2, 9], 1) == 2

    def test_empty_array_raises(self):
        with pytest.raises(ValueError):
            get_index_min_element([])


class TestSorters:
    @pytest.mark.parametrize("sorter", SORTERS)
    def test_sorts_unsorted(self, sorter):
        result, _ = sorter([5, 2, 9, 1, 7])
        assert result == [1, 2, 5, 7, 9]

    @pytest.mark.parametrize("sorter", SORTERS)
    def test_does_not_mutate_input(self, sorter):
        original = [3, 1, 2]
        sorter(original)
        assert original == [3, 1, 2]

    @pytest.mark.parametrize("sorter", SORTERS)
    def test_already_sorted(self, sorter):
        result, _ = sorter([1, 2, 3, 4])
        assert result == [1, 2, 3, 4]

    @pytest.mark.parametrize("sorter", SORTERS)
    def test_reverse_sorted(self, sorter):
        result, _ = sorter([4, 3, 2, 1])
        assert result == [1, 2, 3, 4]

    @pytest.mark.parametrize("sorter", SORTERS)
    def test_single_element(self, sorter):
        result, swaps = sorter([42])
        assert result == [42]
        assert swaps == 0

    @pytest.mark.parametrize("sorter", SORTERS)
    def test_empty(self, sorter):
        result, swaps = sorter([])
        assert result == []
        assert swaps == 0

    @pytest.mark.parametrize("sorter", SORTERS)
    def test_with_duplicates(self, sorter):
        result, _ = sorter([3, 1, 3, 1, 2])
        assert result == [1, 1, 2, 3, 3]

    @pytest.mark.parametrize("sorter", SORTERS)
    def test_matches_builtin_on_random(self, sorter):
        arr = generate_array(50)
        result, _ = sorter(arr)
        assert result == sorted(arr)


class TestSwapCounters:
    def test_already_sorted_no_swaps(self):
        for sorter in SORTERS:
            _, swaps = sorter([1, 2, 3, 4, 5])
            assert swaps == 0

    def test_selection_variants_match(self):
        arr = generate_array(30)
        assert selection_sort(arr)[1] == selection_sort_with_min(arr)[1]

    def test_selection_swaps_bounded_by_n_minus_1(self):
        arr = [5, 4, 3, 2, 1]
        _, swaps = selection_sort(arr)
        assert swaps <= len(arr) - 1

    def test_bubble_reverse_sorted_max_swaps(self):
        # для обратно отсортированного массива пузырёк делает n*(n-1)/2 перестановок
        arr = [5, 4, 3, 2, 1]
        _, swaps = bubble_sort(arr)
        assert swaps == 10

    def test_quick_sort_no_swaps_when_sorted(self):
        # уже отсортированный массив (схема Ломуто, опорный — последний):
        # ни один обмен не нужен
        _, swaps = quick_sort([1, 2, 3, 4, 5])
        assert swaps == 0

    def test_quick_sort_swaps_are_nonnegative(self):
        _, swaps = quick_sort([3, 1, 2, 5, 4])
        assert swaps >= 0


class TestCompareSwaps:
    def test_keys_present(self):
        result = compare_swaps([3, 1, 2])
        assert set(result) == {
            "Сортировка выбором",
            "Сортировка вставками",
            "Пузырьковая сортировка",
            "Быстрая сортировка",
        }

    def test_values_are_ints(self):
        result = compare_swaps(generate_array(10))
        assert all(isinstance(v, int) for v in result.values())

    def test_print_comparison_outputs_best(self, capsys):
        print_comparison([3, 1, 2])
        output = capsys.readouterr().out
        assert "Вывод" in output
        assert "перестановок" in output


class TestMenu:
    def test_all_options_then_exit(self, monkeypatch, capsys):
        # 1-5 — сортировки, 6 — сравнение, 7 — новый массив, x — неизвестный, 0 — выход
        feed_input(monkeypatch, ["1", "2", "3", "4", "5", "6", "7", "x", "0"])
        menu()
        output = capsys.readouterr().out
        assert "Сортировка выбором" in output
        assert "Быстрая сортировка" in output
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
