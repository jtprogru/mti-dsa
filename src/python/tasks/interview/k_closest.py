"""Задача (k ближайших к элементу): дан отсортированный массив `a`, индекс
`idx` и число `k`.

Найти: `k` элементов массива, ближайших по значению к `a[idx]` (сам
`a[idx]` в ответ не входит). Порядок результата — по возрастанию.

Пример:
    a = [10, 15, 20, 50, 55, 78, 91], idx = 2, k = 3 -> [10, 15, 50]
    (вокруг 20 ближайшие: 15, 10, 50)

Закрепляет: lab04 (поиск, два указателя от точки). От `idx` расходимся
влево и вправо, на каждом шаге беря соседа, который ближе по значению.
Опора на отсортированность даёт O(k) после того, как позиция уже известна.
Сложность: O(k log k) время (из-за финальной сортировки k элементов).
"""


def k_closest(a: list[int], idx: int, k: int) -> list[int]:
    pivot = a[idx]
    left = idx - 1
    right = idx + 1
    result: list[int] = []

    while k > 0 and (left >= 0 or right < len(a)):
        if left < 0:
            result.append(a[right])
            right += 1
        elif right >= len(a):
            result.append(a[left])
            left -= 1
        elif pivot - a[left] <= a[right] - pivot:
            result.append(a[left])
            left -= 1
        else:
            result.append(a[right])
            right += 1
        k -= 1

    return sorted(result)
