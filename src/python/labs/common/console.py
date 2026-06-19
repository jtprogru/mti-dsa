"""Чтение ввода с клавиатуры с повтором при ошибке.

Во многих лабораторных меню нужно одно и то же: попросить число, а при вводе
мусора — вежливо повторить запрос. Чтобы не копировать этот цикл в каждую
работу, он собран здесь.

Поведение задаётся параметром `default`:

- `default is None` — обязательный ввод: пустая строка считается неверной и
  запрос повторяется (так вели себя меню в lab04/05/07/08);
- `default` задан — пустой ввод (просто Enter) возвращает значение по умолчанию
  (так вели себя меню в lab09/11).
"""


def read_int(prompt: str, default: int | None = None) -> int:
    """Читает целое число, повторяя запрос при неверном вводе.

    При заданном `default` пустой ввод возвращает значение по умолчанию.
    """
    while True:
        raw = input(prompt).strip()
        if raw == "" and default is not None:
            return default
        try:
            return int(raw)
        except ValueError:
            print("Это не целое число, попробуйте снова.")


def read_float(prompt: str, default: float | None = None) -> float:
    """Читает число с плавающей точкой, повторяя запрос при неверном вводе.

    При заданном `default` пустой ввод возвращает значение по умолчанию.
    """
    while True:
        raw = input(prompt).strip()
        if raw == "" and default is not None:
            return default
        try:
            return float(raw)
        except ValueError:
            print("Это не число, попробуйте снова.")


__all__ = ["read_int", "read_float"]
