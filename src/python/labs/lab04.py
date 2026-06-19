"""
Задания:

1. Создать целочисленный массив (10 чисел), заполнить его случайными числами,
   реализовать функцию print_array для вывода массива на экран.
2. Реализовать поиск простым перебором в созданном массиве. Функции должны
   возвращать:
     - true/false (есть ли элемент);
     - индекс первого вхождения / -1;
     - индексы всех вхождений / -1;
     - количество вхождений / 0.
3. Реализовать алгоритм бинарного поиска в целочисленном массиве. Для сортировки
   использовать один из реализованных ранее алгоритмов сортировки (вставками).
4. Ввести с клавиатуры 10 чисел. Введённые числа формируют отсортированную
   последовательность. Для формирования использовать алгоритм сортировки
   вставками.
5. Реализовать алгоритм бинарного поиска в полученном отсортированном массиве.
"""

from labs.common import array_length, generate_array, print_array, read_int
from labs.lab03 import insertion_sort

# --- Задание 2: поиск простым перебором ------------------------------------


def linear_contains(arr: list[int], target: int) -> bool:
    """Есть ли элемент в массиве. Возвращает True/False."""
    i = 0
    while i < array_length(arr):
        if arr[i] == target:
            return True
        i += 1
    return False


def linear_first_index(arr: list[int], target: int) -> int:
    """Индекс первого вхождения элемента или -1, если его нет."""
    i = 0
    while i < array_length(arr):
        if arr[i] == target:
            return i
        i += 1
    return -1


def linear_all_indices(arr: list[int], target: int) -> list[int] | int:
    """Индексы всех вхождений элемента. Если ни одного — возвращает -1."""
    indices: list[int] = []
    i = 0
    while i < array_length(arr):
        if arr[i] == target:
            indices.append(i)
        i += 1
    if not indices:
        return -1
    return indices


def linear_count(arr: list[int], target: int) -> int:
    """Количество вхождений элемента. Если ни одного — возвращает 0."""
    count = 0
    i = 0
    while i < array_length(arr):
        if arr[i] == target:
            count += 1
        i += 1
    return count


# --- Задание 3 и 5: бинарный поиск -----------------------------------------


def binary_search(arr: list[int], target: int) -> int:
    """Бинарный поиск в **отсортированном** массиве.

    Возвращает индекс одного из вхождений элемента или -1, если его нет.
    На каждом шаге сравниваем середину диапазона с искомым и отбрасываем
    половину, в которой элемента точно нет.
    """
    low = 0
    high = array_length(arr) - 1
    while low <= high:
        mid = (low + high) // 2
        if arr[mid] == target:
            return mid
        if arr[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    return -1


def binary_search_sorted(arr: list[int], target: int) -> tuple[int, list[int]]:
    """Сортирует массив вставками и выполняет в нём бинарный поиск.

    Возвращает (индекс в отсортированном массиве или -1, отсортированный массив).
    Входной массив не мутируется — сортировка возвращает новый список.
    """
    sorted_arr, _ = insertion_sort(arr)
    return binary_search(sorted_arr, target), sorted_arr


# --- Задание 4: формирование отсортированной последовательности -------------


def insert_sorted(sorted_arr: list[int], value: int) -> list[int]:
    """Вставляет value в уже отсортированный массив, сохраняя порядок.

    Это один шаг сортировки вставками: ищем место для value и сдвигаем
    больши́е элементы вправо. Возвращает новый список.
    """
    result = list(sorted_arr)
    result.append(value)
    j = array_length(result) - 2
    while j >= 0 and result[j] > value:
        result[j + 1] = result[j]
        result[j] = value
        j -= 1
    return result


def build_sorted_sequence(values: list[int]) -> list[int]:
    """Строит отсортированную последовательность, добавляя элементы по одному.

    Каждый новый элемент вставляется в нужное место уже отсортированной части
    (сортировка вставками «на лету»).
    """
    result: list[int] = []
    i = 0
    while i < array_length(values):
        result = insert_sorted(result, values[i])
        i += 1
    return result


def read_sorted_sequence(count: int = 10) -> list[int]:
    """Читает count чисел с клавиатуры и формирует отсортированную последовательность.

    После каждого ввода показывает текущее состояние последовательности, чтобы
    было видно, как сортировка вставками поддерживает порядок.
    """
    sequence: list[int] = []
    i = 0
    while i < count:
        raw = input(f"Введите число {i + 1} из {count}: ").strip()
        try:
            value = int(raw)
        except ValueError:
            print("Это не целое число, попробуйте снова.")
            continue
        sequence = insert_sorted(sequence, value)
        print("Текущая отсортированная последовательность:", sequence)
        i += 1
    return sequence


def menu() -> None:
    arr = generate_array(10)
    print("Сгенерирован массив из 10 случайных чисел:")
    print_array(arr)

    while True:
        print("\n" + "=" * 40)
        print("Меню:")
        print("  1. Поиск простым перебором (все варианты)")
        print("  2. Бинарный поиск (с сортировкой вставками)")
        print("  3. Ввести 10 чисел с клавиатуры (отсортированная вставками)")
        print("  4. Бинарный поиск во введённой последовательности")
        print("  5. Сгенерировать новый массив")
        print("  0. Выход")

        choice = input("Выберите пункт: ").strip()

        if choice == "0":
            print("Выход.")
            return
        if choice == "1":
            target = read_int("Какое число ищем? ")
            print(f"\nМассив: {arr}")
            print(f"Содержится:           {linear_contains(arr, target)}")
            print(f"Первое вхождение:     {linear_first_index(arr, target)}")
            print(f"Все вхождения:        {linear_all_indices(arr, target)}")
            print(f"Количество вхождений: {linear_count(arr, target)}")
        elif choice == "2":
            target = read_int("Какое число ищем? ")
            idx, sorted_arr = binary_search_sorted(arr, target)
            print(f"\nОтсортированный массив: {sorted_arr}")
            if idx == -1:
                print("Элемент не найден.")
            else:
                print(f"Элемент найден на индексе {idx} (в отсортированном массиве).")
        elif choice == "3":
            sequence = read_sorted_sequence(10)
            print("\nИтоговая отсортированная последовательность:")
            print_array(sequence)
            arr = sequence
            print("Эта последовательность стала текущим массивом.")
        elif choice == "4":
            target = read_int("Какое число ищем? ")
            idx = binary_search(arr, target)
            if idx == -1:
                print("Элемент не найден. (Для пункта 4 массив должен быть отсортирован — см. пункт 3.)")
            else:
                print(f"Элемент найден на индексе {idx}.")
        elif choice == "5":
            arr = generate_array(10)
            print("Сгенерирован новый массив:")
            print_array(arr)
        else:
            print("Неизвестный пункт меню, попробуйте снова.")


def main() -> None:
    menu()


if __name__ == "__main__":
    main()
