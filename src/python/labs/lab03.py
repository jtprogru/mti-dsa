"""
Задания:

1. Создать целочисленный массив (10 чисел), заполнить его случайными числами,
   реализовать функцию print_array для вывода массива на экран, функцию
   get_min_element для поиска минимального элемента массива. Вывести на экран
   массив и минимальный элемент.
2. Реализовать алгоритм сортировки выбором.
3. Реализовать сортировку выбором с использованием функции поиска минимального
   элемента. Для этого функцию нужно изменить так, чтобы она возвращала индекс
   минимального элемента (get_index_min_element).
4. Реализовать алгоритм сортировки вставками.
5. Реализовать алгоритм пузырьковой сортировки.
6. Реализовать счётчик для подсчёта перестановок элементов для трёх алгоритмов
   сортировки.
7. Сравнить количество перестановок для разных алгоритмов. Сделать вывод об
   эффективности того или иного алгоритма.
8. Реализовать меню для вывода данных на экран. Каждый пункт меню — отдельный
   вид сортировки. Отдельный пункт — сравнить все алгоритмы по количеству
   перестановок.
"""

from labs.common import array_length, generate_array, print_array


def get_min_element(arr: list[int]) -> int:
    if not arr:
        raise ValueError("Массив пуст, невозможно найти минимальный элемент.")
    m = arr[0]
    x = 1
    while x < array_length(arr):
        if arr[x] < m:
            m = arr[x]
        x += 1
    return m


def get_index_min_element(arr: list[int], start: int = 0) -> int:
    """Возвращает индекс минимального элемента, начиная с позиции start.

    Параметр start позволяет переиспользовать функцию в сортировке выбором:
    на каждом шаге ищется минимум в ещё не отсортированном хвосте массива.
    """
    if not arr:
        raise ValueError("Массив пуст, невозможно найти минимальный элемент.")
    idx = start
    x = start + 1
    while x < array_length(arr):
        if arr[x] < arr[idx]:
            idx = x
        x += 1
    return idx


def selection_sort(arr: list[int]) -> tuple[list[int], int]:
    """Сортировка выбором. Возвращает (отсортированный массив, число перестановок).

    На каждом шаге ищем минимум в неотсортированном хвосте и меняем его местами
    с первым элементом этого хвоста.
    """
    result = list(arr)
    swaps = 0
    n = array_length(result)
    i = 0
    while i < n - 1:
        min_idx = i
        j = i + 1
        while j < n:
            if result[j] < result[min_idx]:
                min_idx = j
            j += 1
        if min_idx != i:
            result[i], result[min_idx] = result[min_idx], result[i]
            swaps += 1
        i += 1
    return result, swaps


def selection_sort_with_min(arr: list[int]) -> tuple[list[int], int]:
    """Сортировка выбором, использующая get_index_min_element.

    Логически эквивалентна selection_sort, но поиск минимума вынесен в отдельную
    функцию (задание 3).
    """
    result = list(arr)
    swaps = 0
    n = array_length(result)
    i = 0
    while i < n - 1:
        min_idx = get_index_min_element(result, i)
        if min_idx != i:
            result[i], result[min_idx] = result[min_idx], result[i]
            swaps += 1
        i += 1
    return result, swaps


def insertion_sort(arr: list[int]) -> tuple[list[int], int]:
    """Сортировка вставками. Возвращает (отсортированный массив, число перестановок).

    Перестановкой считается каждый сдвиг элемента вправо при поиске места для
    вставки текущего значения.
    """
    result = list(arr)
    swaps = 0
    n = array_length(result)
    i = 1
    while i < n:
        key = result[i]
        j = i - 1
        while j >= 0 and result[j] > key:
            result[j + 1] = result[j]
            swaps += 1
            j -= 1
        result[j + 1] = key
        i += 1
    return result, swaps


def bubble_sort(arr: list[int]) -> tuple[list[int], int]:
    """Пузырьковая сортировка. Возвращает (отсортированный массив, число перестановок).

    Соседние элементы сравниваются и меняются местами; после каждого прохода
    очередной максимум «всплывает» в конец. Цикл прерывается, если за проход не
    было ни одной перестановки.
    """
    result = list(arr)
    swaps = 0
    n = array_length(result)
    i = 0
    while i < n - 1:
        swapped = False
        j = 0
        while j < n - i - 1:
            if result[j] > result[j + 1]:
                result[j], result[j + 1] = result[j + 1], result[j]
                swaps += 1
                swapped = True
            j += 1
        if not swapped:
            break
        i += 1
    return result, swaps


def quick_sort(arr: list[int]) -> tuple[list[int], int]:
    """Быстрая сортировка. Возвращает (отсортированный массив, число перестановок).

    «Разделяй и властвуй»: за один проход (схема Ломуто) массив разбивается на
    «меньше опорного» и «больше опорного», опорный ставится на своё место, затем
    обе половины сортируются рекурсивно. Перестановкой считается обмен внутри
    разбиения. Средняя сложность O(n·log n), худшая — O(n²).
    """
    result = list(arr)

    def partition(low: int, high: int) -> tuple[int, int]:
        pivot = result[high]
        swaps = 0
        i = low - 1
        j = low
        while j < high:
            if result[j] <= pivot:
                i += 1
                if i != j:
                    result[i], result[j] = result[j], result[i]
                    swaps += 1
            j += 1
        if i + 1 != high:
            result[i + 1], result[high] = result[high], result[i + 1]
            swaps += 1
        return i + 1, swaps

    def sort(low: int, high: int) -> int:
        if low >= high:
            return 0
        pivot_idx, swaps = partition(low, high)
        swaps += sort(low, pivot_idx - 1)
        swaps += sort(pivot_idx + 1, high)
        return swaps

    total_swaps = sort(0, array_length(result) - 1)
    return result, total_swaps


def compare_swaps(arr: list[int]) -> dict[str, int]:
    """Считает число перестановок для всех алгоритмов на одном массиве."""
    return {
        "Сортировка выбором": selection_sort(arr)[1],
        "Сортировка вставками": insertion_sort(arr)[1],
        "Пузырьковая сортировка": bubble_sort(arr)[1],
        "Быстрая сортировка": quick_sort(arr)[1],
    }


def print_comparison(arr: list[int]) -> None:
    print("Сравнение количества перестановок на одном массиве:")
    print("Исходный массив:", arr)
    results = compare_swaps(arr)
    for name, swaps in results.items():
        print(f"  {name:<24} — перестановок: {swaps}")

    best = min(results, key=results.__getitem__)
    print(f"\nМеньше всего перестановок у алгоритма «{best}».")
    print(
        "Вывод: сортировка выбором всегда делает не больше n-1 перестановок, но\n"
        "выполняет максимум сравнений. Вставки и пузырёк зависят от исходного\n"
        "порядка: на почти отсортированных данных они выигрывают, на обратно\n"
        "отсортированных — проигрывают. Эти три алгоритма имеют сложность O(n²).\n"
        "Быстрая сортировка — «разделяй и властвуй» со средней сложностью\n"
        "O(n·log n) и худшей O(n²); на больших массивах она вне конкуренции."
    )


def menu() -> None:
    arr = generate_array(10)
    print("Сгенерирован массив из 10 случайных чисел:")
    print_array(arr)
    print(f"Минимальный элемент: {get_min_element(arr)}")

    options = {
        "1": ("Сортировка выбором", selection_sort),
        "2": ("Сортировка выбором (через поиск минимума)", selection_sort_with_min),
        "3": ("Сортировка вставками", insertion_sort),
        "4": ("Пузырьковая сортировка", bubble_sort),
        "5": ("Быстрая сортировка", quick_sort),
    }

    while True:
        print("\n" + "=" * 40)
        print("Меню:")
        for key, (name, _) in options.items():
            print(f"  {key}. {name}")
        print("  6. Сравнить все алгоритмы по перестановкам")
        print("  7. Сгенерировать новый массив")
        print("  0. Выход")

        choice = input("Выберите пункт: ").strip()

        if choice == "0":
            print("Выход.")
            return
        if choice in options:
            name, func = options[choice]
            sorted_arr, swaps = func(arr)
            print(f"\n{name}:")
            print("Исходный:        ", arr)
            print("Отсортированный: ", sorted_arr)
            print("Перестановок:    ", swaps)
        elif choice == "6":
            print()
            print_comparison(arr)
        elif choice == "7":
            arr = generate_array(10)
            print("Сгенерирован новый массив:")
            print_array(arr)
            print(f"Минимальный элемент: {get_min_element(arr)}")
        else:
            print("Неизвестный пункт меню, попробуйте снова.")


def main() -> None:
    menu()


if __name__ == "__main__":
    main()
