"""
Задания:

1. Работа с файлами через контекстные менеджеры (with): записать список строк
   в файл и прочитать его обратно. Файл всегда корректно закрывается, даже если
   внутри блока возникнет исключение.
2. Аргументы командной строки на argparse: разобрать argv в объект настроек и
   выполнить работу, вернув КОД ВОЗВРАТА процесса (0 — успех, ненулевой — ошибка),
   как это делает любая утилита в Unix.
3. Исключения как часть контракта функции: собственный класс ConfigError и
   разбор простого key=value-конфига, который явно сообщает об ошибках формата,
   а не падает с непонятным трейсбеком.
4. Генераторы и итераторы (зацепка — CustomRange из labs/common/ranges.py):
   ленивое построчное чтение файла и фильтрующий генератор, который не держит
   весь файл в памяти. Плюс ленивая числовая последовательность поверх
   CustomRange.
5. В меню (main) продемонстрировать всё перечисленное на временных файлах во
   временной папке, не засоряя репозиторий.

Все функции чистые и тестируемые: файловый ввод-вывод идёт через явные пути,
argparse разобран через parse_args(argv) (а не sys.argv напрямую), а работа
утилиты вынесена в run(args), возвращающий int. Меню в main() — только
демонстрация и интерактив.
"""

import argparse
import tempfile
from collections.abc import Iterator
from pathlib import Path

from labs.common import array_length, custom_range, generate_array, print_array

# --- Задание 3: собственное исключение --------------------------------------


class ConfigError(Exception):
    """Ошибка разбора конфигурационной строки или файла.

    Своё исключение (а не голый ValueError) делает контракт функции явным:
    вызывающий код ловит именно ConfigError и понимает, что речь о КОНФИГЕ, а не
    о случайной ошибке где-то в недрах. В атрибутах храним номер строки и саму
    строку — этого достаточно, чтобы показать пользователю, где он ошибся.
    """

    def __init__(self, message: str, line_no: int | None = None, line: str | None = None) -> None:
        self.line_no = line_no
        self.line = line
        if line_no is not None:
            message = f"строка {line_no}: {message}"
        super().__init__(message)


# --- Задание 1: работа с файлами через контекстные менеджеры ----------------


def write_lines(path: str | Path, lines: list[str]) -> int:
    """Записать строки в файл (по одной на строку). Возвращает число строк.

    Открытие через `with` гарантирует, что файл закроется и буфер сбросится на
    диск даже при исключении внутри блока — поэтому ручной close() не нужен.
    """
    count = 0
    with open(path, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")
            count += 1
    return count


def read_lines(path: str | Path) -> list[str]:
    """Прочитать файл целиком в список строк без завершающих переводов строки.

    Подходит для небольших файлов: читаем всё в память. Для больших файлов есть
    ленивый iter_lines (задание 4), который не материализует список.
    """
    result: list[str] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            result.append(line.rstrip("\n"))
    return result


# --- Задание 4: генераторы и итераторы --------------------------------------


def iter_lines(path: str | Path) -> Iterator[str]:
    """Ленивый генератор строк файла: отдаёт по одной, не держа файл в памяти.

    Это генераторная функция: тело не выполняется при вызове — только при
    итерации (for / next). Файл закрывается, когда генератор исчерпан или
    закрыт, благодаря `with` вокруг yield.
    """
    with open(path, encoding="utf-8") as f:
        for line in f:
            yield line.rstrip("\n")


def filter_lines(lines: Iterator[str] | list[str], needle: str) -> Iterator[str]:
    """Фильтрующий генератор: пропускает только строки, содержащие needle.

    Принимает любой итерируемый источник (список или генератор iter_lines),
    поэтому фильтр можно навесить прямо на потоковое чтение файла, не загружая
    его целиком. Это «ленивый grep».
    """
    for line in lines:
        if needle in line:
            yield line


def even_squares(stop: int) -> Iterator[int]:
    """Ленивая последовательность квадратов чётных чисел [0, stop) поверх CustomRange.

    Демонстрирует, как самописный CustomRange из labs.common ведёт себя как
    обычный range в генераторном выражении: ничего не материализуется, пока не
    начнётся итерация.
    """
    for n in custom_range(stop):
        if n % 2 == 0:
            yield n * n


# --- Задание 3: разбор конфига (исключение как часть контракта) -------------


def parse_config_line(line: str, line_no: int | None = None) -> tuple[str, str] | None:
    """Разобрать одну строку конфига `key = value`. Контракт:

    - пустая строка или комментарий (`#`) -> None (строку пропускаем);
    - корректная `key=value` -> (key, value) с обрезанными пробелами;
    - всё остальное (нет `=`, пустой ключ) -> ConfigError.

    line_no попадает в текст ошибки, чтобы пользователь нашёл проблемную строку.
    """
    stripped = line.strip()
    if stripped == "" or stripped.startswith("#"):
        return None
    if "=" not in stripped:
        raise ConfigError("ожидается формат key=value", line_no, line)
    key, _, value = stripped.partition("=")
    key = key.strip()
    value = value.strip()
    if key == "":
        raise ConfigError("пустой ключ", line_no, line)
    return key, value


def parse_config(text: str) -> dict[str, str]:
    """Разобрать многострочный конфиг в словарь. Бросает ConfigError при ошибке.

    Нумерация строк начинается с 1 — как в редакторах, чтобы ошибку было удобно
    сопоставить с файлом.
    """
    config: dict[str, str] = {}
    line_no = 1
    for line in text.splitlines():
        pair = parse_config_line(line, line_no)
        if pair is not None:
            config[pair[0]] = pair[1]
        line_no += 1
    return config


def load_config(path: str | Path) -> dict[str, str]:
    """Прочитать и разобрать конфиг из файла.

    Файл читается через контекстный менеджер; разбор — через parse_config, так
    что ConfigError указывает на конкретную строку файла.
    """
    with open(path, encoding="utf-8") as f:
        return parse_config(f.read())


# --- Задание 2: argparse + код возврата процесса ----------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Разобрать argv в Namespace. Принимает список аргументов (а не sys.argv).

    Явный argv делает функцию тестируемой: в тесте передаём список строк, а не
    патчим sys.argv. argparse сам бросит SystemExit при `--help` или неверных
    аргументах — это стандартное поведение CLI.
    """
    parser = argparse.ArgumentParser(
        prog="lab00",
        description="Учебная CLI-утилита: считает строки файла или ищет в нём подстроку.",
    )
    parser.add_argument("path", help="путь к текстовому файлу")
    parser.add_argument(
        "-c",
        "--count",
        action="store_true",
        help="вывести число строк в файле",
    )
    parser.add_argument(
        "-g",
        "--grep",
        metavar="ПОДСТРОКА",
        help="вывести строки, содержащие подстроку",
    )
    return parser.parse_args(argv)


def run(args: argparse.Namespace) -> int:
    """Выполнить работу по разобранным аргументам. Возвращает КОД ВОЗВРАТА.

    Контракт по кодам возврата (как у обычной Unix-утилиты):
      0 — успех;
      1 — файл не найден / не читается;
      2 — конфликт аргументов (не задано, что делать).

    Ошибки печатаются как сообщения, а не как трейсбек — так ведёт себя утилита,
    а не библиотека.
    """
    if not args.count and args.grep is None:
        print("Нужно указать --count или --grep ПОДСТРОКА.")
        return 2

    path = Path(args.path)
    try:
        # Потоковое чтение: фильтр и счётчик идут поверх ленивого iter_lines.
        if args.grep is not None:
            found = 0
            for line in filter_lines(iter_lines(path), args.grep):
                print(line)
                found += 1
            if args.count:
                print(f"Найдено строк: {found}")
        else:
            total = 0
            for _ in iter_lines(path):
                total += 1
            print(f"Всего строк: {total}")
    except FileNotFoundError:
        print(f"Файл не найден: {path}")
        return 1
    except OSError as exc:
        print(f"Не удалось прочитать файл {path}: {exc}")
        return 1
    return 0


def main_cli(argv: list[str] | None = None) -> int:
    """Точка входа CLI: разобрать argv и выполнить run. Возвращает код возврата.

    Именно это значение нужно передать в sys.exit(...), чтобы код возврата
    утилиты дошёл до оболочки.
    """
    args = parse_args(argv)
    return run(args)


# --- Задание 5: меню и демонстрация -----------------------------------------


def _demo_files(work_dir: Path) -> None:
    """Демонстрация заданий 1 и 4 на временном файле."""
    sample = work_dir / "sample.txt"
    lines = ["alpha ok", "beta error", "gamma ok", "delta error", "epsilon ok"]
    written = write_lines(sample, lines)
    print(f"Записано строк в {sample.name}: {written}")

    print("\nЧтение целиком (read_lines):")
    for line in read_lines(sample):
        print(f"  {line}")

    print("\nЛенивое потоковое чтение (iter_lines) + фильтр 'ok':")
    for line in filter_lines(iter_lines(sample), "ok"):
        print(f"  {line}")


def _demo_config(work_dir: Path) -> None:
    """Демонстрация задания 3: успешный разбор и обработка ConfigError."""
    good = work_dir / "good.conf"
    write_lines(good, ["# демо-конфиг", "host = localhost", "port = 8080", "", "debug=true"])
    print("\nРазбор корректного конфига:")
    for key, value in load_config(good).items():
        print(f"  {key} -> {value}")

    print("\nРазбор битого конфига (ловим ConfigError):")
    try:
        parse_config("host = localhost\nport 8080\n")
    except ConfigError as exc:
        print(f"  поймали ошибку: {exc}")


def _demo_generators() -> None:
    """Демонстрация задания 4: ленивая последовательность поверх CustomRange."""
    squares = list(even_squares(10))
    print("\nКвадраты чётных чисел из [0, 10) (even_squares поверх CustomRange):")
    print(f"  {squares}")
    arr = generate_array(5)
    print("\nСлучайный массив (generate_array из common):")
    print_array(arr)
    print(f"  длина (array_length): {array_length(arr)}")


def _demo_cli(work_dir: Path) -> None:
    """Демонстрация задания 2: parse_args + run на временном файле."""
    sample = work_dir / "cli.txt"
    write_lines(sample, ["error: disk full", "info: ok", "error: timeout"])

    print("\nЭмуляция вызова `lab00 cli.txt --count`:")
    code = run(parse_args([str(sample), "--count"]))
    print(f"  код возврата: {code}")

    print("\nЭмуляция вызова `lab00 cli.txt --grep error`:")
    code = run(parse_args([str(sample), "--grep", "error"]))
    print(f"  код возврата: {code}")

    print("\nЭмуляция вызова на несуществующий файл (ожидаем код 1):")
    code = run(parse_args([str(work_dir / "nope.txt"), "--count"]))
    print(f"  код возврата: {code}")


def menu() -> None:
    # Все демонстрации работают во временной папке, чтобы не оставлять мусор.
    with tempfile.TemporaryDirectory() as tmp:
        work_dir = Path(tmp)

        while True:
            print("\n" + "=" * 40)
            print("Меню (Python для эксплуатации):")
            print("  1. Файлы: запись и чтение (with, iter_lines + фильтр)")
            print("  2. Конфиг: разбор key=value и обработка ConfigError")
            print("  3. Генераторы: even_squares поверх CustomRange")
            print("  4. CLI: parse_args + run и коды возврата")
            print("  0. Выход")

            choice = input("Выберите пункт: ").strip()

            if choice == "0":
                print("Выход.")
                return
            if choice == "1":
                _demo_files(work_dir)
            elif choice == "2":
                _demo_config(work_dir)
            elif choice == "3":
                _demo_generators()
            elif choice == "4":
                _demo_cli(work_dir)
            else:
                print("Неизвестный пункт меню, попробуйте снова.")


def main() -> None:
    menu()


if __name__ == "__main__":
    main()
