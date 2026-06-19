"""Задача (contains duplicate): дан список чисел.

Найти: вернуть True, если в списке есть хотя бы один повтор, иначе False.

Пример:
    [0, 1, 2, 3, 3, 5] -> True
    [0, 1, 2, 3]       -> False

Закрепляет: lab05 (хеш-таблица). Множество «уже виденных» значений — это
та же хеш-таблица: проверка `in` за O(1) превращает наивный двойной цикл
O(n^2) в один проход.
Сложность: O(n) время, O(n) память.
"""


def contains_duplicate(nums: list[int]) -> bool:
    seen: set[int] = set()
    for num in nums:
        if num in seen:
            return True
        seen.add(num)
    return False
