"""Задача (rotate array): дан массив `nums` и неотрицательное `k`.

Найти: циклически сдвинуть массив вправо на `k` шагов, изменяя его на месте.

Пример:
    [1, 2, 3, 4, 5, 6, 7], k = 3 -> [5, 6, 7, 1, 2, 3, 4]

Закрепляет: lab01 (массив, in-place). Сдвиг на `k` эквивалентен сдвигу на
`k % n` (полный круг ничего не меняет). Делаем разворот in-place в три
приёма: весь массив, затем первые `k` и оставшиеся — без доп. массива.
Сложность: O(n) время, O(1) доп. память.
"""


def _reverse(nums: list[int], left: int, right: int) -> None:
    while left < right:
        nums[left], nums[right] = nums[right], nums[left]
        left += 1
        right -= 1


def rotate(nums: list[int], k: int) -> None:
    n = len(nums)
    if n == 0:
        return
    k %= n
    _reverse(nums, 0, n - 1)  # развернули весь массив
    _reverse(nums, 0, k - 1)  # вернули порядок в первой части
    _reverse(nums, k, n - 1)  # и во второй
