"""Базовые операции над массивами без встроенных функций.

Длина, генерация и печать массива реализованы вручную (без len) — это часть
учебного задания.
"""

import random


def array_length(arr: list) -> int:
    """Длина массива без встроенной len: просто считаем элементы."""
    count = 0
    for _ in arr:
        count += 1
    return count


def generate_array(size: int) -> list[int]:
    """Массив из size случайных целых чисел в диапазоне [1, 100]."""
    result = []
    i = 0
    while i < size:
        result.append(random.randint(1, 100))
        i += 1
    return result


def print_array(arr: list[int]) -> None:
    """Печатает массив по индексам в формате `[i] = значение`."""
    i = 0
    while i < array_length(arr):
        print(f"[{i}] = {arr[i]}")
        i += 1


__all__ = ["array_length", "generate_array", "print_array"]
