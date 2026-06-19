"""Самописный аналог встроенной range — ленивый объект-последовательность.

Встроенная range намеренно не используется — это часть учебного задания.
Здесь воспроизведены её ключевые свойства: O(1) на len, индексацию и проверку
вхождения целого числа, ленивая итерация без материализации списка, срезы,
возвращающие новый range, и согласованные __eq__/__hash__.

Подробный разбор того, как устроена настоящая range в CPython и почему наша
реализация повторяет именно эти решения, — на странице документации common.
"""

from collections.abc import Sequence


class CustomRange(Sequence):
    """Ленивая последовательность целых чисел — аналог встроенной range.

    Поддерживает обе формы вызова: CustomRange(stop) и
    CustomRange(start, stop[, step]). Хранит только start/stop/step и
    предвычисленную длину, а конкретные элементы вычисляет арифметически по
    запросу — поэтому не зависит от размера диапазона по памяти.
    """

    def __init__(self, start: int, stop: int | None = None, step: int = 1) -> None:
        if stop is None:  # форма CustomRange(stop)
            start, stop = 0, start
        if step == 0:
            raise ValueError("CustomRange() arg 3 must not be zero")

        self.start = start
        self.stop = stop
        self.step = step

        # Длина считается один раз по формуле и кешируется — отсюда O(1) на len.
        if step > 0:
            raw = (stop - start + step - 1) // step
        else:
            raw = (start - stop - step - 1) // (-step)
        self._length = raw if raw > 0 else 0  # без встроенного max

    def __len__(self) -> int:
        return self._length

    def __getitem__(self, index: int | slice) -> "int | CustomRange":
        # Срез строит новый CustomRange с пересчитанными границами, не копируя данные.
        if isinstance(index, slice):
            start, stop, step = index.indices(self._length)
            return CustomRange(
                self.start + start * self.step,
                self.start + stop * self.step,
                self.step * step,
            )
        if index < 0:  # нормализация отрицательного индекса
            index += self._length
        if not 0 <= index < self._length:
            raise IndexError("CustomRange object index out of range")
        return self.start + index * self.step  # i-й элемент — чистая арифметика, O(1)

    def __iter__(self):
        # Ленивая итерация: значение наращивается на шаг, список не строится.
        value = self.start
        count = 0
        while count < self._length:
            yield value
            value += self.step
            count += 1

    def __reversed__(self):
        value = self.start + (self._length - 1) * self.step
        count = 0
        while count < self._length:
            yield value
            value -= self.step
            count += 1

    def __contains__(self, x: object) -> bool:
        # Для целого — проверка арифметикой за O(1); иначе откат к перебору.
        if not isinstance(x, int):
            for v in self:
                if v == x:
                    return True
            return False
        if self._length == 0:
            return False
        if self.step > 0:
            in_bounds = self.start <= x < self.stop
        else:
            in_bounds = self.stop < x <= self.start
        return in_bounds and (x - self.start) % self.step == 0

    def index(self, value: object, start: int = 0, stop: int | None = None) -> int:
        # Позиция элемента — тоже арифметика, без перебора, если значение целое.
        if value in self:
            return (value - self.start) // self.step
        raise ValueError(f"{value!r} is not in range")

    def count(self, value: object) -> int:
        return 1 if value in self else 0

    def __eq__(self, other: object) -> bool:
        # Равенство — по порождаемой последовательности, а не по сырым параметрам:
        # CustomRange(0, 3, 2) == CustomRange(0, 4, 2), т.к. оба дают [0, 2].
        if not isinstance(other, CustomRange):
            return NotImplemented
        if self._length != other._length:
            return False
        if self._length == 0:
            return True
        if self.start != other.start:
            return False
        if self._length == 1:
            return True
        return self.step == other.step

    def __hash__(self) -> int:
        # Хеш согласован с __eq__: незначимые поля обнуляются, чтобы равные
        # диапазоны имели равный хеш.
        if self._length == 0:
            return hash((0, None, None))
        if self._length == 1:
            return hash((1, self.start, None))
        return hash((self._length, self.start, self.step))

    def __repr__(self) -> str:
        if self.step == 1:
            return f"CustomRange({self.start}, {self.stop})"
        return f"CustomRange({self.start}, {self.stop}, {self.step})"


# Удобный псевдоним в стиле встроенной range (строчными буквами).
custom_range = CustomRange


__all__ = ["CustomRange", "custom_range"]
