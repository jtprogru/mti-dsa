import pytest

from labs.lab09 import (
    LeakyBucket,
    RingBuffer,
    SlidingWindowCounter,
    SlidingWindowLog,
    TokenBucket,
    _read_float,
    _read_int,
    demo_burst,
    demo_steady,
    main,
    menu,
)


def feed_input(monkeypatch, values):
    """Подменяет input() последовательностью значений."""
    inputs = iter(values)
    monkeypatch.setattr("builtins.input", lambda _="": next(inputs))


class TestRingBuffer:
    def test_invalid_capacity_raises(self):
        with pytest.raises(ValueError):
            RingBuffer(0)

    def test_push_and_to_list(self):
        rb = RingBuffer(3)
        rb.push("a")
        rb.push("b")
        assert rb.to_list() == ["a", "b"]
        assert len(rb) == 2
        assert rb.is_full() is False

    def test_fills_up(self):
        rb = RingBuffer(3)
        rb.push(1)
        rb.push(2)
        rb.push(3)
        assert rb.is_full() is True
        assert rb.to_list() == [1, 2, 3]

    def test_overwrite_oldest_on_overflow(self):
        # Перезапись по кругу: 4-й элемент затирает самый старый (1).
        rb = RingBuffer(3)
        for v in (1, 2, 3, 4):
            rb.push(v)
        assert rb.to_list() == [2, 3, 4]
        assert len(rb) == 3

    def test_overwrite_wraps_multiple_times(self):
        rb = RingBuffer(3)
        for v in (1, 2, 3, 4, 5, 6, 7):
            rb.push(v)
        # последние три элемента, порядок от старого к новому
        assert rb.to_list() == [5, 6, 7]

    def test_pop_is_fifo(self):
        rb = RingBuffer(3)
        rb.push(1)
        rb.push(2)
        assert rb.pop() == 1
        assert rb.pop() == 2
        assert rb.pop() is None  # пусто
        assert rb.is_empty() is True

    def test_peek_oldest(self):
        rb = RingBuffer(2)
        assert rb.peek_oldest() is None
        rb.push(10)
        rb.push(20)
        assert rb.peek_oldest() == 10
        rb.push(30)  # затирает 10
        assert rb.peek_oldest() == 20


class TestTokenBucket:
    def test_invalid_params_raise(self):
        with pytest.raises(ValueError):
            TokenBucket(capacity=0, rate=1)
        with pytest.raises(ValueError):
            TokenBucket(capacity=5, rate=0)

    def test_initial_burst_up_to_capacity(self):
        # Стартуем с полным ведром: 5 запросов в момент 0 проходят, 6-й — нет.
        tb = TokenBucket(capacity=5, rate=1, start=0.0)
        results = [tb.allow(0.0) for _ in range(6)]
        assert results == [True, True, True, True, True, False]

    def test_refill_over_time(self):
        # Опустошаем ведро, ждём 2 секунды (rate=1) -> 2 токена восстановились.
        tb = TokenBucket(capacity=5, rate=1, start=0.0)
        for _ in range(5):
            tb.allow(0.0)
        assert tb.allow(0.0) is False  # ведро пусто
        assert tb.allow(2.0) is True  # за 2 сек накапало 2 токена
        assert tb.allow(2.0) is True
        assert tb.allow(2.0) is False

    def test_refill_capped_at_capacity(self):
        # Долгая пауза не копит токены сверх capacity.
        tb = TokenBucket(capacity=3, rate=1, start=0.0)
        assert tb.available_tokens(1000.0) == 3

    @pytest.mark.parametrize(
        "rate,wait,expected_extra",
        [
            (2.0, 1.0, 2),  # 2 токена/сек * 1 сек = 2
            (0.5, 2.0, 1),  # 0.5 токена/сек * 2 сек = 1
            (1.0, 3.0, 3),
        ],
    )
    def test_refill_rate_parametrized(self, rate, wait, expected_extra):
        tb = TokenBucket(capacity=10, rate=rate, start=0.0)
        # выпиваем всё
        while tb.allow(0.0):
            pass
        # после ожидания должно стать ровно expected_extra токенов
        allowed = 0
        while tb.allow(wait):
            allowed += 1
        assert allowed == expected_extra

    def test_time_going_backwards_is_ignored(self):
        tb = TokenBucket(capacity=5, rate=1, start=10.0)
        tb.allow(10.0)
        # «назад во времени» не должно доливать токены
        before = tb.available_tokens(5.0)
        assert before == tb.available_tokens(5.0)

    def test_cost_greater_than_one(self):
        tb = TokenBucket(capacity=5, rate=1, start=0.0)
        assert tb.allow(0.0, cost=3) is True
        assert tb.allow(0.0, cost=3) is False  # осталось 2 токена


class TestLeakyBucket:
    def test_invalid_params_raise(self):
        with pytest.raises(ValueError):
            LeakyBucket(capacity=0, rate=1)
        with pytest.raises(ValueError):
            LeakyBucket(capacity=5, rate=0)

    def test_fills_to_capacity_then_overflows(self):
        # Пустое ведро вмещает capacity запросов в момент 0, следующий — overflow.
        lb = LeakyBucket(capacity=3, rate=1, start=0.0)
        results = [lb.allow(0.0) for _ in range(4)]
        assert results == [True, True, True, False]

    def test_leaks_over_time(self):
        # Заполняем, ждём 2 секунды (rate=1) -> вытекло 2 -> снова есть место.
        lb = LeakyBucket(capacity=3, rate=1, start=0.0)
        for _ in range(3):
            lb.allow(0.0)
        assert lb.allow(0.0) is False  # полно
        assert lb.allow(2.0) is True  # вытекло 2, место появилось
        assert lb.allow(2.0) is True
        assert lb.allow(2.0) is False

    def test_water_never_negative(self):
        lb = LeakyBucket(capacity=3, rate=1, start=0.0)
        lb.allow(0.0)
        # после долгой паузы вода полностью вытекла (не уходит в минус)
        assert lb.water_level(1000.0) == 0.0

    @pytest.mark.parametrize(
        "rate,wait,drained",
        [
            (1.0, 1.0, 1),
            (2.0, 1.0, 2),
            (1.0, 5.0, 5),
        ],
    )
    def test_drain_rate_parametrized(self, rate, wait, drained):
        capacity = 5
        lb = LeakyBucket(capacity=capacity, rate=rate, start=0.0)
        while lb.allow(0.0):
            pass
        # после ожидания вытекло min(drained, capacity), столько мест освободилось
        freed = 0
        while lb.allow(wait):
            freed += 1
        assert freed == min(drained, capacity)


class TestSlidingWindowLog:
    def test_invalid_params_raise(self):
        with pytest.raises(ValueError):
            SlidingWindowLog(limit=0, window_size=10)
        with pytest.raises(ValueError):
            SlidingWindowLog(limit=5, window_size=0)

    def test_limit_within_window(self):
        # 3 запроса в окне 10с проходят, 4-й — нет.
        sw = SlidingWindowLog(limit=3, window_size=10)
        assert sw.allow(0.0) is True
        assert sw.allow(1.0) is True
        assert sw.allow(2.0) is True
        assert sw.allow(3.0) is False

    def test_window_slides_and_frees_slots(self):
        sw = SlidingWindowLog(limit=2, window_size=10)
        assert sw.allow(0.0) is True
        assert sw.allow(5.0) is True
        assert sw.allow(6.0) is False  # окно (−4, 6] содержит оба запроса
        # в момент 11 запрос t=0 выпал из окна (11−10=1, 0 <= 1) -> освободилось место
        assert sw.allow(11.0) is True

    def test_window_boundary_exclusive_left(self):
        # Граница окна левая исключающая: запрос ровно на boundary выкидывается.
        sw = SlidingWindowLog(limit=1, window_size=10)
        assert sw.allow(0.0) is True
        # в момент 10: boundary = 0, отметка 0 <= 0 -> выпала, место есть
        assert sw.allow(10.0) is True

    def test_count_reflects_eviction(self):
        sw = SlidingWindowLog(limit=5, window_size=10)
        sw.allow(0.0)
        sw.allow(1.0)
        sw.allow(2.0)
        assert sw.count(2.0) == 3
        # к моменту 11.5 граница = 1.5: отметки 0 и 1 выпали, осталась только 2
        assert sw.count(11.5) == 1


class TestSlidingWindowCounter:
    def test_invalid_params_raise(self):
        with pytest.raises(ValueError):
            SlidingWindowCounter(limit=0, window_size=10)
        with pytest.raises(ValueError):
            SlidingWindowCounter(limit=5, window_size=0)

    def test_limit_within_single_window(self):
        sw = SlidingWindowCounter(limit=3, window_size=10, start=0.0)
        assert sw.allow(0.0) is True
        assert sw.allow(1.0) is True
        assert sw.allow(2.0) is True
        assert sw.allow(3.0) is False

    def test_counter_resets_after_full_window_gap(self):
        # Проскок через несколько окон обнуляет и текущий, и предыдущий счётчики.
        sw = SlidingWindowCounter(limit=2, window_size=10, start=0.0)
        sw.allow(0.0)
        sw.allow(1.0)
        assert sw.allow(2.0) is False
        # окно 0 -> окно 5 (далеко): всё обнулилось
        assert sw.allow(100.0) is True
        assert sw.allow(101.0) is True

    def test_weighted_estimate_at_boundary(self):
        # Окно 10, limit 10. Заполним предыдущее окно 10 запросами в [0,10).
        sw = SlidingWindowCounter(limit=10, window_size=10, start=0.0)
        for t in range(10):
            assert sw.allow(float(t)) is True
        # в момент 15 мы на 50% в новом окне: оценка = 10*0.5 + 0 = 5 < 10 -> можно
        assert sw.estimated_count(15.0) == pytest.approx(5.0)
        assert sw.allow(15.0) is True

    def test_estimate_decreases_as_window_advances(self):
        sw = SlidingWindowCounter(limit=100, window_size=10, start=0.0)
        for t in range(8):
            sw.allow(float(t))
        e_early = sw.estimated_count(11.0)  # почти всё предыдущее окно ещё в счёт
        e_late = sw.estimated_count(19.0)  # почти выехали из предыдущего окна
        assert e_early > e_late


class TestReadHelpers:
    def test_read_int_default_on_empty(self, monkeypatch):
        monkeypatch.setattr("builtins.input", lambda _="": "")
        assert _read_int("p", 7) == 7

    def test_read_int_valid(self, monkeypatch):
        monkeypatch.setattr("builtins.input", lambda _="": "42")
        assert _read_int("p", 7) == 42

    def test_read_int_retries(self, monkeypatch, capsys):
        feed_input(monkeypatch, ["x", "9"])
        assert _read_int("p", 0) == 9
        assert "Это не целое число" in capsys.readouterr().out

    def test_read_float_default_on_empty(self, monkeypatch):
        monkeypatch.setattr("builtins.input", lambda _="": "")
        assert _read_float("p", 1.5) == 1.5

    def test_read_float_valid(self, monkeypatch):
        monkeypatch.setattr("builtins.input", lambda _="": "2.5")
        assert _read_float("p", 1.0) == 2.5


class TestDemos:
    def test_demo_burst(self, capsys):
        demo_burst()
        out = capsys.readouterr().out
        assert "token bucket" in out
        assert "leaky bucket" in out
        assert "sliding window log" in out
        assert "sliding window counter" in out

    def test_demo_steady(self, capsys):
        demo_steady()
        out = capsys.readouterr().out
        assert "token bucket" in out
        assert "Равномерный поток" in out


class TestMenu:
    def test_all_options_then_exit(self, monkeypatch, capsys):
        feed_input(
            monkeypatch,
            [
                "1", "5", "1", "5", "10",  # задать параметры
                "2",                        # token bucket
                "3",                        # leaky bucket
                "4",                        # sliding window log
                "5",                        # sliding window counter
                "6",                        # burst
                "7",                        # steady
                "z",                        # неизвестный пункт
                "0",                        # выход
            ],
        )
        menu()
        out = capsys.readouterr().out
        assert "Параметры обновлены" in out
        assert "Неизвестный пункт" in out
        assert "Выход" in out

    def test_exit_immediately(self, monkeypatch, capsys):
        feed_input(monkeypatch, ["0"])
        menu()
        assert "Выход" in capsys.readouterr().out

    def test_main_delegates_to_menu(self, monkeypatch, capsys):
        feed_input(monkeypatch, ["0"])
        main()
        assert "Выход" in capsys.readouterr().out
