"""Задача (first unique character): дана строка `s` из строчных латинских букв.

Найти: индекс первого неповторяющегося символа; если такого нет — вернуть -1.

Пример:
    "leetcode"     -> 0
    "loveleetcode" -> 2
    "aabb"         -> -1

Закрепляет: lab05 (хеш-таблица). Два прохода: первый строит частотный
словарь, второй ищет первый символ с частотой 1. Подсчёт частот через
словарь — базовый приём, на котором стоят разбор логов и метрики.
Сложность: O(n) время, O(k) память (k — размер алфавита).
"""


def first_unique_char(s: str) -> int:
    frequency: dict[str, int] = {}
    for ch in s:
        frequency[ch] = frequency.get(ch, 0) + 1
    for i, ch in enumerate(s):
        if frequency[ch] == 1:
            return i
    return -1
