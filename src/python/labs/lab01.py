"""
Задания:

1. Реализовать целочисленный массив из 10 элементов, заполнить его случайными числами, вывести на экран
2. Реализовать функцию для вывода массива на экран. При реализации использовать обращение к элементам массива по индексу.
3. Реализовать функцию нахождения максимального элемента массива. Функция возвращает значение максимального элемента. Встроенные функции не использовать.
4. Реализовать функцию нахождения максимального элемента массива. Функция возвращает индекс максимального элемента массива. Встроенные функции не использовать.
5. Реалиовать функцию подсчета суммы элементов массива. Функция возвращает значение суммы. Встроенные функции не использовать.
6. Реализовать стек на основе массива. Реализацию делать в виде класса.
7. Реализовать методы добавления узла, извлечения узла, получение значения узла, проверка на пустоту
8. Реализовать метод распечатки стека (от вершины до начала). При этом элементы не извлекаются.
"""

from labs.common import array_length, generate_array, print_array


def custom_max_index(arr: list[int]) -> int:
    if not arr:
        raise ValueError("Массив пуст, невозможно найти максимальный элемент.")
    m = arr[0]
    idx = 0
    x = 1
    while x < array_length(arr):
        if arr[x] > m:
            m = arr[x]
            idx = x
        x += 1
    return idx


def custom_max(arr: list[int]) -> int:
    if not arr:
        raise ValueError("Массив пуст, невозможно найти максимальный элемент.")
    m = arr[0]
    for x in arr[1:]:
        if x > m:
            m = x
    return m


def calculate_total_sum(arr: list[int]) -> int:
    total = 0
    for x in arr:
        total += x
    return total


class Stack:
    def __init__(self) -> None:
        self._data: list = []

    def is_empty(self) -> bool:
        return array_length(self._data) == 0

    def push(self, value) -> None:
        self._data.append(value)

    def pop(self):
        if self.is_empty():
            raise IndexError("Стек пуст, невозможно извлечь элемент.")
        return self._data.pop()

    def peek(self):
        if self.is_empty():
            raise IndexError("Стек пуст, невозможно получить вершину.")
        return self._data[array_length(self._data) - 1]

    def print_stack(self) -> None:
        if self.is_empty():
            print("Стек пуст.")
            return
        i = array_length(self._data) - 1
        while i >= 0:
            print(self._data[i])
            i -= 1


def main() -> None:
    arr = generate_array(10)
    print("=" * 30)
    print("Массив по индексам:")
    print_array(arr)
    print(f"Максимум:  {custom_max(arr)}")
    print(f"Индекс:    {custom_max_index(arr)}")
    print(f"Сумма:     {calculate_total_sum(arr)}")
    print("=" * 30)

    stack = Stack()
    print("Стек пуст?", stack.is_empty())
    for val in arr:
        stack.push(val)
    print("После заполнения — стек пуст?", stack.is_empty())
    print("Вершина стека:", stack.peek())
    print("Содержимое стека (от вершины):")
    stack.print_stack()
    print("Извлечено:", stack.pop())
    print("Новая вершина:", stack.peek())
    print("=" * 30)


if __name__ == "__main__":
    main()
