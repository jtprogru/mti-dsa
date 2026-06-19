import pytest

from labs.lab00 import (
    ConfigError,
    _demo_cli,
    _demo_config,
    _demo_files,
    _demo_generators,
    even_squares,
    filter_lines,
    iter_lines,
    load_config,
    main,
    main_cli,
    menu,
    parse_args,
    parse_config,
    parse_config_line,
    read_lines,
    run,
    write_lines,
)


def feed_input(monkeypatch, values):
    """Подменяет input() последовательностью значений."""
    inputs = iter(values)
    monkeypatch.setattr("builtins.input", lambda _="": next(inputs))


# --- Задание 1: файлы через контекстные менеджеры ---------------------------


class TestWriteAndReadLines:
    def test_write_returns_count(self, tmp_path):
        path = tmp_path / "out.txt"
        assert write_lines(path, ["a", "b", "c"]) == 3

    def test_round_trip(self, tmp_path):
        path = tmp_path / "out.txt"
        write_lines(path, ["alpha", "beta", "gamma"])
        assert read_lines(path) == ["alpha", "beta", "gamma"]

    def test_write_empty_creates_empty_file(self, tmp_path):
        path = tmp_path / "empty.txt"
        assert write_lines(path, []) == 0
        assert read_lines(path) == []

    def test_read_strips_only_trailing_newline(self, tmp_path):
        path = tmp_path / "spaces.txt"
        write_lines(path, ["  padded  ", "tab\tinside"])
        assert read_lines(path) == ["  padded  ", "tab\tinside"]

    def test_read_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            read_lines(tmp_path / "nope.txt")


# --- Задание 4: генераторы и итераторы --------------------------------------


class TestIterLines:
    def test_yields_each_line(self, tmp_path):
        path = tmp_path / "data.txt"
        write_lines(path, ["one", "two", "three"])
        assert list(iter_lines(path)) == ["one", "two", "three"]

    def test_is_lazy_generator(self, tmp_path):
        path = tmp_path / "data.txt"
        write_lines(path, ["x", "y"])
        gen = iter_lines(path)
        # генератор отдаёт по одному элементу
        assert next(gen) == "x"
        assert next(gen) == "y"
        with pytest.raises(StopIteration):
            next(gen)

    def test_empty_file_yields_nothing(self, tmp_path):
        path = tmp_path / "empty.txt"
        write_lines(path, [])
        assert list(iter_lines(path)) == []


class TestFilterLines:
    @pytest.mark.parametrize(
        "lines, needle, expected",
        [
            (["foo ok", "bar error", "baz ok"], "ok", ["foo ok", "baz ok"]),
            (["a", "b", "c"], "z", []),
            (["error 1", "error 2"], "error", ["error 1", "error 2"]),
            ([], "x", []),
        ],
    )
    def test_filters(self, lines, needle, expected):
        assert list(filter_lines(lines, needle)) == expected

    def test_works_over_iter_lines(self, tmp_path):
        path = tmp_path / "log.txt"
        write_lines(path, ["info ok", "warn err", "debug ok"])
        assert list(filter_lines(iter_lines(path), "ok")) == ["info ok", "debug ok"]


class TestEvenSquares:
    @pytest.mark.parametrize(
        "stop, expected",
        [
            (10, [0, 4, 16, 36, 64]),
            (1, [0]),
            (0, []),
            (2, [0]),
            (5, [0, 4, 16]),
        ],
    )
    def test_values(self, stop, expected):
        assert list(even_squares(stop)) == expected

    def test_returns_generator(self):
        gen = even_squares(6)
        assert next(gen) == 0
        assert next(gen) == 4


# --- Задание 3: исключения как часть контракта ------------------------------


class TestParseConfigLine:
    @pytest.mark.parametrize(
        "line, expected",
        [
            ("host = localhost", ("host", "localhost")),
            ("port=8080", ("port", "8080")),
            ("  key  =  value  ", ("key", "value")),
            ("flag=", ("flag", "")),
            ("url = http://a=b", ("url", "http://a=b")),
        ],
    )
    def test_valid_pairs(self, line, expected):
        assert parse_config_line(line) == expected

    @pytest.mark.parametrize("line", ["", "   ", "# comment", "  # spaced comment"])
    def test_skipped_lines_return_none(self, line):
        assert parse_config_line(line) is None

    def test_no_equals_raises(self):
        with pytest.raises(ConfigError):
            parse_config_line("host localhost")

    def test_empty_key_raises(self):
        with pytest.raises(ConfigError):
            parse_config_line("= value")

    def test_error_carries_line_number(self):
        with pytest.raises(ConfigError) as exc_info:
            parse_config_line("broken", line_no=7)
        assert exc_info.value.line_no == 7
        assert "7" in str(exc_info.value)


class TestParseConfig:
    def test_parses_multiple_keys(self):
        text = "host = localhost\nport = 8080\n"
        assert parse_config(text) == {"host": "localhost", "port": "8080"}

    def test_skips_comments_and_blanks(self):
        text = "# header\n\nhost = a\n\n# mid\nport = b\n"
        assert parse_config(text) == {"host": "a", "port": "b"}

    def test_later_key_overrides_earlier(self):
        assert parse_config("x = 1\nx = 2\n") == {"x": "2"}

    def test_empty_text_gives_empty_dict(self):
        assert parse_config("") == {}

    def test_raises_with_correct_line_number(self):
        text = "ok = 1\nbroken line\n"
        with pytest.raises(ConfigError) as exc_info:
            parse_config(text)
        assert exc_info.value.line_no == 2


class TestLoadConfig:
    def test_loads_from_file(self, tmp_path):
        path = tmp_path / "app.conf"
        write_lines(path, ["# config", "host = localhost", "port = 9090"])
        assert load_config(path) == {"host": "localhost", "port": "9090"}

    def test_raises_config_error_from_file(self, tmp_path):
        path = tmp_path / "bad.conf"
        write_lines(path, ["host = localhost", "no equals here"])
        with pytest.raises(ConfigError):
            load_config(path)

    def test_missing_file_raises_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_config(tmp_path / "missing.conf")


# --- Задание 2: argparse parse_args + run -----------------------------------


class TestParseArgs:
    def test_path_and_count(self):
        args = parse_args(["file.txt", "--count"])
        assert args.path == "file.txt"
        assert args.count is True
        assert args.grep is None

    def test_grep_value(self):
        args = parse_args(["file.txt", "--grep", "error"])
        assert args.grep == "error"
        assert args.count is False

    def test_short_flags(self):
        args = parse_args(["file.txt", "-c", "-g", "warn"])
        assert args.count is True
        assert args.grep == "warn"

    def test_missing_path_exits(self):
        with pytest.raises(SystemExit):
            parse_args([])

    def test_help_exits(self):
        with pytest.raises(SystemExit):
            parse_args(["--help"])


class TestRun:
    def test_count_returns_zero(self, tmp_path, capsys):
        path = tmp_path / "data.txt"
        write_lines(path, ["a", "b", "c"])
        code = run(parse_args([str(path), "--count"]))
        assert code == 0
        assert "Всего строк: 3" in capsys.readouterr().out

    def test_grep_prints_matches(self, tmp_path, capsys):
        path = tmp_path / "log.txt"
        write_lines(path, ["error one", "ok", "error two"])
        code = run(parse_args([str(path), "--grep", "error"]))
        assert code == 0
        out = capsys.readouterr().out
        assert "error one" in out
        assert "error two" in out
        assert "ok\n" not in out

    def test_grep_with_count(self, tmp_path, capsys):
        path = tmp_path / "log.txt"
        write_lines(path, ["error one", "ok", "error two"])
        run(parse_args([str(path), "--grep", "error", "--count"]))
        assert "Найдено строк: 2" in capsys.readouterr().out

    def test_missing_file_returns_one(self, tmp_path, capsys):
        code = run(parse_args([str(tmp_path / "nope.txt"), "--count"]))
        assert code == 1
        assert "Файл не найден" in capsys.readouterr().out

    def test_no_action_returns_two(self, tmp_path, capsys):
        path = tmp_path / "data.txt"
        write_lines(path, ["a"])
        code = run(parse_args([str(path)]))
        assert code == 2
        assert "--count" in capsys.readouterr().out


class TestMainCli:
    def test_returns_run_exit_code_success(self, tmp_path):
        path = tmp_path / "data.txt"
        write_lines(path, ["x", "y"])
        assert main_cli([str(path), "--count"]) == 0

    def test_returns_error_code_on_missing_file(self, tmp_path):
        assert main_cli([str(tmp_path / "nope.txt"), "--count"]) == 1

    def test_returns_two_without_action(self, tmp_path):
        path = tmp_path / "data.txt"
        write_lines(path, ["x"])
        assert main_cli([str(path)]) == 2


class TestRunOSError:
    def test_directory_path_returns_one(self, tmp_path, capsys):
        # Передаём директорию вместо файла -> IsADirectoryError (подкласс OSError).
        assert run(parse_args([str(tmp_path), "--count"])) == 1
        assert "Не удалось прочитать файл" in capsys.readouterr().out


class TestDemos:
    def test_demo_files(self, tmp_path, capsys):
        _demo_files(tmp_path)
        out = capsys.readouterr().out
        assert "Записано строк" in out
        assert "Ленивое потоковое чтение" in out

    def test_demo_config(self, tmp_path, capsys):
        _demo_config(tmp_path)
        out = capsys.readouterr().out
        assert "host -> localhost" in out
        assert "поймали ошибку" in out

    def test_demo_generators(self, capsys):
        _demo_generators()
        out = capsys.readouterr().out
        assert "Квадраты чётных чисел" in out
        assert "Случайный массив" in out

    def test_demo_cli(self, tmp_path, capsys):
        _demo_cli(tmp_path)
        out = capsys.readouterr().out
        assert "код возврата: 0" in out
        assert "код возврата: 1" in out


class TestMenu:
    def test_all_options_then_exit(self, monkeypatch, capsys):
        feed_input(monkeypatch, ["1", "2", "3", "4", "x", "0"])
        menu()
        out = capsys.readouterr().out
        assert "Записано строк" in out
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
