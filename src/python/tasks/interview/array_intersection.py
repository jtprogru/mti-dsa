"""Задача (intersection of two arrays): даны два массива `nums1` и `nums2`.

Найти: их пересечение с учётом кратности — каждый элемент входит в ответ
столько раз, сколько он встречается в обоих массивах. Порядок любой.

Пример:
    [1, 2, 2, 1], [2, 2] -> [2, 2]
    [4, 9, 5], [9, 4, 9, 8, 4] -> [4, 9]

Закрепляет: lab05 (хеш-таблица). Считаем частоты элементов меньшего массива
в словаре, затем «вычёркиваем» их, проходя по большему. Это классический
ответ на follow-up «а если один массив огромный» — в память грузим меньший.
Сложность: O(n + m) время, O(min(n, m)) память.
"""


def array_intersection(nums1: list[int], nums2: list[int]) -> list[int]:
    # В словарь кладём меньший массив — экономим память.
    if len(nums1) > len(nums2):
        nums1, nums2 = nums2, nums1

    counts: dict[int, int] = {}
    for num in nums1:
        counts[num] = counts.get(num, 0) + 1

    result: list[int] = []
    for num in nums2:
        if counts.get(num, 0) > 0:
            result.append(num)
            counts[num] -= 1
    return result
