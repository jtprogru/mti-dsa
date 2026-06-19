"""Общие вспомогательные функции, переиспользуемые в нескольких лабораторных.

Чтобы не дублировать один и тот же код в каждой работе, базовые helper'ы
собраны в этом локальном пакете и разложены по логическим модулям:

- arrays — операции над массивами (array_length, generate_array, print_array);
- ranges — самописный аналог range: ленивый CustomRange и псевдоним custom_range;
- console — чтение ввода с клавиатуры с повтором при ошибке (read_int, read_float).

Импорты можно делать как из пакета (`from labs.common import array_length`),
так и из конкретного модуля (`from labs.common.arrays import array_length`).
Встроенные функции (len, range, ...) намеренно не используются — это часть
учебного задания.
"""

from labs.common.arrays import array_length, generate_array, print_array
from labs.common.console import read_float, read_int
from labs.common.ranges import CustomRange, custom_range

__all__ = [
    "array_length",
    "generate_array",
    "print_array",
    "CustomRange",
    "custom_range",
    "read_int",
    "read_float",
]
