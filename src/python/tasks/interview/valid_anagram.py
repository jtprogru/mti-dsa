"""Задача (valid anagram): даны две строки `s` и `t`.

Найти: вернуть True, если `t` — анаграмма `s` (тот же набор букв в другом
порядке), иначе False.

Пример:
    "anagram", "nagaram" -> True
    "rat", "car"         -> False

Закрепляет: lab05 (хеш-таблица). Сравниваем не отсортированные строки
(O(n log n)), а частотные словари букв (O(n)). Если у двух строк совпадают
счётчики по каждому символу — это анаграммы.
Сложность: O(n) время, O(k) память (k — размер алфавита).
"""


def _char_counts(s: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for ch in s:
        counts[ch] = counts.get(ch, 0) + 1
    return counts


def is_anagram(s: str, t: str) -> bool:
    if len(s) != len(t):
        return False
    return _char_counts(s) == _char_counts(t)
