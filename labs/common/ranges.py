"""Самописный аналог встроенной range.

Встроенная range намеренно не используется — это часть учебного задания.
"""


def custom_range(start: int, stop: int | None = None, step: int = 1) -> list[int]:
    """Самописный аналог встроенной range — возвращает список целых чисел.

    Поддерживает обе формы вызова: custom_range(stop) и
    custom_range(start, stop[, step]). Встроенная range не используется.
    """
    if stop is None:
        start, stop = 0, start
    if step == 0:
        raise ValueError("step не может быть равен нулю.")
    result: list[int] = []
    current = start
    if step > 0:
        while current < stop:
            result.append(current)
            current += step
    else:
        while current > stop:
            result.append(current)
            current += step
    return result


__all__ = ["custom_range"]
