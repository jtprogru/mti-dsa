"""
Задания:

1. Реализовать потоковую (построчную) обработку лог-файла через генераторы,
   чтобы НЕ держать весь файл в памяти. Источником может быть путь к файлу
   или любая итерируемая последовательность строк (список, генератор, поток).
2. Распарсить строку access-лога в структуру LogEntry
   (ip, метод, путь, статус, латентность). Битые строки пропускать, не падая.
3. Агрегировать поля: счётчики обращений по статусам, по IP и по эндпоинтам
   (путям). Счётчики строим руками на dict — Counter не используем, чтобы было
   видно сам механизм агрегации (предмет лабы — потоковость и агрегация).
4. Считать перцентили латентности p50 / p95 / p99 РУКАМИ: метод nearest-rank
   (ближайший ранг) по ISO/ГОСТ: сортируем латентности и берём элемент с
   номером rank = ceil(p/100 * N) (нумерация с 1). statistics НЕ используем.
5. В меню (main) продемонстрировать разбор встроенного примера лог-строк:
   парсинг, агрегаты и перцентили латентности.

Формат лог-строки (упрощённый access-лог, поля через пробел):
    <ip> <method> <path> <status> <latency_ms>
Пример:
    10.0.0.1 GET /api/users 200 12.5

Метод перцентиля зафиксирован: **nearest-rank**, rank = ceil(p/100 * N),
индексация результата с 1 (см. percentile() и docs/lab10.md).
"""

import re
from collections.abc import Iterable, Iterator

# Регэксп строки лога: 5 полей через пробелы. Латентность — целое или дробное.
# Группы именованные, чтобы парсер читался как «достаём поле по имени».
_LOG_RE = re.compile(
    r"^\s*"
    r"(?P<ip>\S+)\s+"
    r"(?P<method>\S+)\s+"
    r"(?P<path>\S+)\s+"
    r"(?P<status>\d{3})\s+"
    r"(?P<latency>\d+(?:\.\d+)?)"
    r"\s*$"
)


# --- Задание 2: структура записи лога ---------------------------------------


class LogEntry:
    """Одна разобранная строка access-лога.

    Простой контейнер из пяти полей. Намеренно не dataclass — чтобы поведение
    (__eq__, __repr__) было видно явно, в стиле остальных лаб.
    """

    __slots__ = ("ip", "method", "path", "status", "latency")

    def __init__(self, ip: str, method: str, path: str, status: int, latency: float) -> None:
        self.ip = ip
        self.method = method
        self.path = path
        self.status = status
        self.latency = latency

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, LogEntry):
            return NotImplemented
        return (
            self.ip == other.ip
            and self.method == other.method
            and self.path == other.path
            and self.status == other.status
            and self.latency == other.latency
        )

    def __repr__(self) -> str:
        return (
            f"LogEntry(ip={self.ip!r}, method={self.method!r}, path={self.path!r}, "
            f"status={self.status}, latency={self.latency})"
        )


def parse_line(line: str) -> LogEntry | None:
    """Парсит одну строку лога в LogEntry.

    Возвращает LogEntry для валидной строки и None — для битой (не подошла под
    формат). None вместо исключения выбран сознательно: в реальном логе всегда
    есть мусорные строки, и из-за одной не должен падать весь разбор.
    """
    match = _LOG_RE.match(line)
    if match is None:
        return None
    return LogEntry(
        ip=match.group("ip"),
        method=match.group("method"),
        path=match.group("path"),
        status=int(match.group("status")),
        latency=float(match.group("latency")),
    )


# --- Задание 1: потоковый источник строк и записей --------------------------


def read_lines(source: str | Iterable[str]) -> Iterator[str]:
    """Лениво отдаёт строки источника по одной (потоково).

    Источник — либо путь к файлу (str), либо уже готовая итерируемая
    последовательность строк (список, генератор, файловый объект). В случае
    файла он открывается и читается построчно: в каждый момент в памяти лежит
    одна строка, а не весь файл. Перевод строки справа обрезается.

    Это генератор — пока его не итерируют, файл не читается и память не растёт.
    """
    if isinstance(source, str):
        with open(source, encoding="utf-8") as fh:
            for line in fh:
                yield line.rstrip("\n")
    else:
        for line in source:
            yield line.rstrip("\n")


def parse_log(source: str | Iterable[str]) -> Iterator[LogEntry]:
    """Потоково парсит источник, отдавая только валидные LogEntry.

    Генератор поверх read_lines: читает строку — парсит — отдаёт (или
    пропускает битую). Весь конвейер ленивый, поэтому обрабатывать можно лог
    любого размера, не загружая его целиком.
    """
    for line in read_lines(source):
        entry = parse_line(line)
        if entry is not None:
            yield entry


# --- Задание 3: агрегация счётчиков -----------------------------------------


def _bump(counter: dict, key) -> None:
    """Увеличить счётчик ключа в dict на 1 (механика Counter руками)."""
    if key in counter:
        counter[key] += 1
    else:
        counter[key] = 1


class LogStats:
    """Аккумулятор агрегатов одного прохода по логу.

    Заполняется потоково методом add() по одной записи за раз, поэтому не
    требует материализации всех записей. Хранит:
      - счётчики по статусам / IP / путям (dict ключ -> количество);
      - список латентностей (нужен для перцентилей — их без всех значений
        не посчитать);
      - общее число обработанных записей.
    """

    def __init__(self) -> None:
        self.by_status: dict[int, int] = {}
        self.by_ip: dict[str, int] = {}
        self.by_path: dict[str, int] = {}
        self.latencies: list[float] = []
        self.total: int = 0

    def add(self, entry: LogEntry) -> None:
        """Учесть одну запись во всех агрегатах."""
        _bump(self.by_status, entry.status)
        _bump(self.by_ip, entry.ip)
        _bump(self.by_path, entry.path)
        self.latencies.append(entry.latency)
        self.total += 1


def aggregate(source: str | Iterable[str]) -> LogStats:
    """Один потоковый проход по источнику со сбором всех агрегатов.

    Источник проходится один раз через генератор parse_log: записи не
    складываются в общий список, каждая сразу учитывается в LogStats.
    """
    stats = LogStats()
    for entry in parse_log(source):
        stats.add(entry)
    return stats


def top_n(counter: dict, n: int = 3) -> list[tuple]:
    """Top-N ключей счётчика по убыванию количества (ties — по ключу).

    Удобно для «топ эндпоинтов» / «топ IP». Сортируем пары (ключ, количество):
    сначала по количеству убыванию, затем по ключу по возрастанию для
    стабильного, воспроизводимого порядка.
    """
    pairs = list(counter.items())
    pairs.sort(key=lambda kv: (-kv[1], str(kv[0])))
    return pairs[:n]


# --- Задание 4: перцентили латентности (вручную) ----------------------------


def percentile(values: list[float], p: float) -> float:
    """Перцентиль методом nearest-rank (ближайший ранг). statistics НЕ используем.

    Алгоритм:
      1. Отсортировать значения по возрастанию (копию, вход не мутируем).
      2. Посчитать ранг rank = ceil(p/100 * N), нумерация элементов с 1.
      3. Вернуть элемент под этим рангом (индекс rank-1 в 0-нумерации).

    Граничные случаи: p<=0 -> минимум, p>=100 -> максимум. Пустой вход — ошибка
    (перцентиль пустого множества не определён).

    Метод nearest-rank выбран осознанно: он не интерполирует, всегда возвращает
    РЕАЛЬНОЕ наблюдаемое значение из выборки и даёт детерминированный результат
    (важно для тестов). Например, для [1..100] p95 == 95, p99 == 99, p50 == 50.
    """
    if not values:
        raise ValueError("percentile() от пустой последовательности не определён")
    ordered = sorted(values)
    n = len(ordered)
    if p <= 0:
        return ordered[0]
    if p >= 100:
        return ordered[n - 1]
    # ceil(p/100 * n) без math.ceil: целочисленное деление с округлением вверх.
    # rank в диапазоне [1, n]; индекс — rank-1.
    scaled = p * n  # = (p/100 * n) * 100, делим на 100 ниже
    rank = (scaled + 99) // 100  # ceil(scaled/100)
    rank = int(rank)
    if rank < 1:
        rank = 1
    if rank > n:
        rank = n
    return ordered[rank - 1]


def latency_percentiles(values: list[float]) -> dict[str, float]:
    """Считает сразу p50 / p95 / p99 латентности. Пустой вход -> нули."""
    if not values:
        return {"p50": 0.0, "p95": 0.0, "p99": 0.0}
    return {
        "p50": percentile(values, 50),
        "p95": percentile(values, 95),
        "p99": percentile(values, 99),
    }


# --- Задание 5: встроенный пример и меню ------------------------------------


SAMPLE_LOG: list[str] = [
    "10.0.0.1 GET /api/users 200 12.5",
    "10.0.0.2 GET /api/users 200 8.0",
    "10.0.0.1 POST /api/login 200 45.2",
    "10.0.0.3 GET /api/orders 500 130.0",
    "10.0.0.1 GET /api/users 404 5.0",
    "битая строка которую парсер должен пропустить",
    "10.0.0.2 GET /api/orders 200 22.0",
    "10.0.0.4 DELETE /api/users/42 204 3.5",
    "10.0.0.3 GET /api/orders 500 210.0",
    "10.0.0.1 GET /health 200 1.0",
]


def _print_counter(title: str, counter: dict, limit: int = 5) -> None:
    """Печатает top-`limit` ключей счётчика."""
    print(f"\n{title}:")
    for key, count in top_n(counter, limit):
        print(f"  {key}: {count}")


def demo_sample() -> None:
    """Полный разбор встроенного примера лог-строк: агрегаты + перцентили."""
    print("\nРазбор встроенного примера лог-строк (одна строка — битая):")
    stats = aggregate(SAMPLE_LOG)
    print(f"Обработано валидных записей: {stats.total}")

    _print_counter("Обращения по статусам", stats.by_status)
    _print_counter("Топ IP", stats.by_ip)
    _print_counter("Топ эндпоинтов", stats.by_path)

    pct = latency_percentiles(stats.latencies)
    print("\nПерцентили латентности (мс), метод nearest-rank:")
    print(f"  p50 = {pct['p50']}")
    print(f"  p95 = {pct['p95']}")
    print(f"  p99 = {pct['p99']}")


def demo_parse_one() -> None:
    """Показывает разбор одной валидной и одной битой строки."""
    good = "10.0.0.7 GET /api/ping 200 7.5"
    bad = "не лог, а просто текст"
    print(f"\nВалидная строка: {good!r}")
    print(f"  -> {parse_line(good)}")
    print(f"\nБитая строка:    {bad!r}")
    print(f"  -> {parse_line(bad)} (None — строка пропускается при разборе)")


def analyze_file() -> None:
    """Читает путь к файлу с клавиатуры и потоково разбирает его."""
    path = input("Путь к лог-файлу: ").strip()
    try:
        stats = aggregate(path)
    except OSError as exc:
        print(f"Не удалось прочитать файл: {exc}")
        return
    if stats.total == 0:
        print("В файле не нашлось ни одной валидной строки лога.")
        return
    print(f"Обработано валидных записей: {stats.total}")
    _print_counter("Обращения по статусам", stats.by_status)
    _print_counter("Топ IP", stats.by_ip)
    _print_counter("Топ эндпоинтов", stats.by_path)
    pct = latency_percentiles(stats.latencies)
    print("\nПерцентили латентности (мс), метод nearest-rank:")
    print(f"  p50={pct['p50']}  p95={pct['p95']}  p99={pct['p99']}")


def menu() -> None:
    while True:
        print("\n" + "=" * 40)
        print("Меню (разбор логов):")
        print("  1. Разобрать встроенный пример (агрегаты + перцентили)")
        print("  2. Показать парсинг одной строки (валидной и битой)")
        print("  3. Разобрать лог-файл по пути")
        print("  0. Выход")

        choice = input("Выберите пункт: ").strip()

        if choice == "0":
            print("Выход.")
            return
        if choice == "1":
            demo_sample()
        elif choice == "2":
            demo_parse_one()
        elif choice == "3":
            analyze_file()
        else:
            print("Неизвестный пункт меню, попробуйте снова.")


def main() -> None:
    menu()


if __name__ == "__main__":
    main()
