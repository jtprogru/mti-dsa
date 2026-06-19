import pytest

from labs.lab10 import (
    LogEntry,
    LogStats,
    _print_counter,
    aggregate,
    analyze_file,
    demo_parse_one,
    demo_sample,
    latency_percentiles,
    main,
    menu,
    parse_line,
    parse_log,
    percentile,
    read_lines,
    top_n,
)


def feed_input(monkeypatch, values):
    """Подменяет input() последовательностью значений."""
    inputs = iter(values)
    monkeypatch.setattr("builtins.input", lambda _="": next(inputs))


class TestParseLine:
    @pytest.mark.parametrize(
        "line, expected",
        [
            (
                "10.0.0.1 GET /api/users 200 12.5",
                LogEntry("10.0.0.1", "GET", "/api/users", 200, 12.5),
            ),
            (
                "192.168.1.10 POST /login 500 130.0",
                LogEntry("192.168.1.10", "POST", "/login", 500, 130.0),
            ),
            # целочисленная латентность парсится как float
            (
                "10.0.0.2 DELETE /api/users/42 204 3",
                LogEntry("10.0.0.2", "DELETE", "/api/users/42", 204, 3.0),
            ),
            # ведущие/хвостовые пробелы допустимы
            (
                "  10.0.0.3 GET /health 200 1.0  ",
                LogEntry("10.0.0.3", "GET", "/health", 200, 1.0),
            ),
        ],
    )
    def test_valid_lines(self, line, expected):
        assert parse_line(line) == expected

    @pytest.mark.parametrize(
        "line",
        [
            "",  # пустая строка
            "просто текст без полей",
            "10.0.0.1 GET /api/users 200",  # нет латентности
            "10.0.0.1 GET /api/users abc 12.5",  # статус не число
            "10.0.0.1 GET /api/users 20 12.5",  # статус не трёхзначный
            "10.0.0.1 GET /api/users 200 fast",  # латентность не число
        ],
    )
    def test_broken_lines_return_none(self, line):
        assert parse_line(line) is None

    def test_status_is_int(self):
        entry = parse_line("10.0.0.1 GET /x 200 5.0")
        assert isinstance(entry.status, int)

    def test_latency_is_float(self):
        entry = parse_line("10.0.0.1 GET /x 200 5")
        assert isinstance(entry.latency, float)


class TestParseLogStreaming:
    def test_skips_broken_lines(self):
        lines = [
            "10.0.0.1 GET /a 200 1.0",
            "битая строка",
            "10.0.0.2 GET /b 404 2.0",
        ]
        entries = list(parse_log(lines))
        assert len(entries) == 2
        assert [e.path for e in entries] == ["/a", "/b"]

    def test_is_lazy_generator(self):
        # parse_log не материализует вход: возвращает итератор, который тянет
        # строки по одной. Источник тоже генератор — если бы parse_log делал
        # list(source), это бы проявилось, но главное — тип результата ленивый.
        import collections.abc as abc

        gen = parse_log(x for x in [])
        assert isinstance(gen, abc.Iterator)

    def test_consumes_source_lazily(self):
        # Источник-генератор, который считает, сколько строк у него запросили.
        consumed = {"n": 0}

        def source():
            for line in ["10.0.0.1 GET /a 200 1.0", "10.0.0.2 GET /b 200 2.0"]:
                consumed["n"] += 1
                yield line

        it = parse_log(source())
        # пока ничего не запросили — источник не тронут
        assert consumed["n"] == 0
        first = next(it)
        # запросили одну запись — прочитана ровно одна строка источника
        assert first.path == "/a"
        assert consumed["n"] == 1

    def test_reads_from_file(self, tmp_path):
        log = tmp_path / "access.log"
        log.write_text(
            "10.0.0.1 GET /a 200 1.0\nмусор\n10.0.0.2 GET /b 500 2.0\n",
            encoding="utf-8",
        )
        entries = list(parse_log(str(log)))
        assert [e.status for e in entries] == [200, 500]


class TestReadLines:
    def test_strips_newlines(self):
        assert list(read_lines(["a\n", "b\n", "c"])) == ["a", "b", "c"]

    def test_reads_file(self, tmp_path):
        f = tmp_path / "f.txt"
        f.write_text("x\ny\n", encoding="utf-8")
        assert list(read_lines(str(f))) == ["x", "y"]


# Известный набор строк с заранее посчитанными агрегатами.
KNOWN_LINES = [
    "10.0.0.1 GET /api/users 200 10.0",
    "10.0.0.1 GET /api/users 200 20.0",
    "10.0.0.2 POST /api/login 500 30.0",
    "10.0.0.2 GET /api/users 404 40.0",
    "10.0.0.3 GET /health 200 50.0",
]


class TestAggregate:
    def test_total_counts_only_valid(self):
        lines = KNOWN_LINES + ["битая", ""]
        assert aggregate(lines).total == 5

    @pytest.mark.parametrize(
        "field, expected",
        [
            ("by_status", {200: 3, 500: 1, 404: 1}),
            ("by_ip", {"10.0.0.1": 2, "10.0.0.2": 2, "10.0.0.3": 1}),
            (
                "by_path",
                {"/api/users": 3, "/api/login": 1, "/health": 1},
            ),
        ],
    )
    def test_counters(self, field, expected):
        stats = aggregate(KNOWN_LINES)
        assert getattr(stats, field) == expected

    def test_collects_latencies(self):
        stats = aggregate(KNOWN_LINES)
        assert stats.latencies == [10.0, 20.0, 30.0, 40.0, 50.0]

    def test_empty_source(self):
        stats = aggregate([])
        assert stats.total == 0
        assert stats.by_status == {}
        assert stats.latencies == []


class TestLogStatsAdd:
    def test_add_accumulates(self):
        stats = LogStats()
        stats.add(LogEntry("ip1", "GET", "/a", 200, 1.0))
        stats.add(LogEntry("ip1", "GET", "/a", 500, 2.0))
        assert stats.total == 2
        assert stats.by_ip == {"ip1": 2}
        assert stats.by_status == {200: 1, 500: 1}
        assert stats.by_path == {"/a": 2}
        assert stats.latencies == [1.0, 2.0]


class TestTopN:
    def test_orders_by_count_desc(self):
        counter = {"a": 1, "b": 5, "c": 3}
        assert top_n(counter, 3) == [("b", 5), ("c", 3), ("a", 1)]

    def test_limits_results(self):
        counter = {"a": 1, "b": 5, "c": 3}
        assert top_n(counter, 1) == [("b", 5)]

    def test_ties_broken_by_key(self):
        counter = {"b": 2, "a": 2, "c": 1}
        assert top_n(counter, 2) == [("a", 2), ("b", 2)]


class TestPercentile:
    @pytest.mark.parametrize(
        "p, expected",
        [
            (50, 50),
            (95, 95),
            (99, 99),
            (100, 100),
            (1, 1),
        ],
    )
    def test_one_to_hundred(self, p, expected):
        # nearest-rank: rank = ceil(p/100 * 100) = p, элемент == p
        assert percentile(list(range(1, 101)), p) == expected

    @pytest.mark.parametrize(
        "p, expected",
        [
            (50, 5),  # rank = ceil(0.50*10) = 5 -> 5
            (95, 10),  # rank = ceil(0.95*10) = 10 -> 10
            (99, 10),  # rank = ceil(0.99*10) = 10 -> 10
            (10, 1),  # rank = ceil(0.10*10) = 1 -> 1
            (100, 10),
        ],
    )
    def test_one_to_ten(self, p, expected):
        assert percentile(list(range(1, 11)), p) == expected

    def test_unsorted_input_is_sorted(self):
        # тот же набор, но в обратном порядке — результат не зависит от порядка
        assert percentile([100 - i for i in range(100)], 95) == 95

    def test_does_not_mutate_input(self):
        data = [3, 1, 2]
        percentile(data, 50)
        assert data == [3, 1, 2]

    def test_single_value(self):
        assert percentile([42.0], 50) == 42.0
        assert percentile([42.0], 99) == 42.0

    @pytest.mark.parametrize("p", [0, -5])
    def test_low_percentile_returns_min(self, p):
        assert percentile([5, 1, 9, 3], p) == 1

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            percentile([], 50)


class TestLatencyPercentiles:
    def test_known_set(self):
        result = latency_percentiles(list(range(1, 101)))
        assert result == {"p50": 50, "p95": 95, "p99": 99}

    def test_empty_returns_zeros(self):
        assert latency_percentiles([]) == {"p50": 0.0, "p95": 0.0, "p99": 0.0}


class TestLogEntryDunder:
    def test_eq_with_other_type_is_false(self):
        entry = LogEntry("10.0.0.1", "GET", "/", 200, 1.0)
        # __eq__ возвращает NotImplemented -> Python трактует как неравенство
        assert entry != "не LogEntry"
        assert (entry == 123) is False

    def test_repr_contains_fields(self):
        entry = LogEntry("10.0.0.1", "GET", "/api", 200, 1.5)
        text = repr(entry)
        assert text.startswith("LogEntry(ip='10.0.0.1'")
        assert "status=200" in text


class TestPrintCounter:
    def test_prints_top_keys(self, capsys):
        _print_counter("Заголовок", {"a": 5, "b": 3, "c": 1}, limit=2)
        out = capsys.readouterr().out
        assert "Заголовок:" in out
        assert "a: 5" in out
        assert "b: 3" in out
        assert "c: 1" not in out


class TestDemos:
    def test_demo_sample(self, capsys):
        demo_sample()
        out = capsys.readouterr().out
        assert "Обработано валидных записей" in out
        assert "Перцентили латентности" in out

    def test_demo_parse_one(self, capsys):
        demo_parse_one()
        out = capsys.readouterr().out
        assert "Валидная строка" in out
        assert "Битая строка" in out


class TestAnalyzeFile:
    def test_reads_and_aggregates(self, tmp_path, monkeypatch, capsys):
        path = tmp_path / "access.log"
        path.write_text(
            "10.0.0.1 GET /api 200 12.5\n10.0.0.2 POST /login 500 40.0\n",
            encoding="utf-8",
        )
        feed_input(monkeypatch, [str(path)])
        analyze_file()
        out = capsys.readouterr().out
        assert "Обработано валидных записей: 2" in out
        assert "Перцентили латентности" in out

    def test_no_valid_lines(self, tmp_path, monkeypatch, capsys):
        path = tmp_path / "empty.log"
        path.write_text("совсем не лог\n", encoding="utf-8")
        feed_input(monkeypatch, [str(path)])
        analyze_file()
        assert "не нашлось ни одной валидной строки" in capsys.readouterr().out

    def test_oserror_on_directory(self, tmp_path, monkeypatch, capsys):
        feed_input(monkeypatch, [str(tmp_path)])
        analyze_file()
        assert "Не удалось прочитать файл" in capsys.readouterr().out


class TestMenu:
    def test_all_options_then_exit(self, tmp_path, monkeypatch, capsys):
        path = tmp_path / "access.log"
        path.write_text("10.0.0.1 GET /api 200 12.5\n", encoding="utf-8")
        feed_input(monkeypatch, ["1", "2", "3", str(path), "x", "0"])
        menu()
        out = capsys.readouterr().out
        assert "Обработано валидных записей" in out
        assert "Неизвестный пункт меню" in out
        assert "Выход." in out

    def test_exit_immediately(self, monkeypatch, capsys):
        feed_input(monkeypatch, ["0"])
        menu()
        assert "Выход." in capsys.readouterr().out

    def test_main_delegates_to_menu(self, monkeypatch, capsys):
        feed_input(monkeypatch, ["0"])
        main()
        assert "Выход." in capsys.readouterr().out
