"""Общие вспомогательные функции, переиспользуемые в нескольких лабораторных.

Чтобы не дублировать один и тот же код в каждой работе, базовые helper'ы
собраны в этом локальном пакете и разложены по логическим модулям:

- arrays — операции над массивами (array_length, generate_array, print_array);
- ranges — самописный аналог range (custom_range).

Импорты можно делать как из пакета (`from labs.common import array_length`),
так и из конкретного модуля (`from labs.common.arrays import array_length`).
Встроенные функции (len, range, ...) намеренно не используются — это часть
учебного задания.
"""

from labs.common.arrays import array_length, generate_array, print_array
from labs.common.ranges import custom_range

__all__ = ["array_length", "generate_array", "print_array", "custom_range"]
