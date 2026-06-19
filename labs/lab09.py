"""
Задания:

1. Реализовать кольцевой буфер (ring buffer) «руками»: фиксированный массив с
   указателями head/tail и счётчиком. Поддержать push (с перезаписью самого
   старого элемента при переполнении), последовательность элементов и подсчёт
   занятых ячеек. Это структура, на которой строится sliding window log.
2. Реализовать алгоритм Token Bucket (ведро с токенами): токены капают с
   постоянной скоростью до ёмкости ведра, запрос разрешается, если в ведре есть
   хотя бы один токен. Допускает короткие всплески (burst) до ёмкости ведра.
3. Реализовать алгоритм Leaky Bucket (дырявое ведро) как очередь фиксированного
   объёма, которая «вытекает» с постоянной скоростью. Сглаживает поток до
   равномерного и режет всплески.
4. Реализовать алгоритм Sliding Window Log: хранить времена последних запросов в
   кольцевом буфере и разрешать запрос, только если в окне длиной window_size
   меньше limit запросов. Точное окно без «скачка» на границе.
5. Реализовать алгоритм Sliding Window Counter: приближение скользящего окна
   через два фиксированных счётчика (текущее и предыдущее окно) с взвешиванием
   по доле времени — дёшево по памяти, без хранения каждого запроса.
6. Сделать алгоритмы детерминированно тестируемыми: «текущее время» не берётся
   из реального time/sleep, а передаётся в allow(now) явным параметром. Это
   позволяет в тестах «прокручивать» время вручную. В меню используем
   time.monotonic как часы по умолчанию.
7. Реализовать меню для демонстрации всех четырёх алгоритмов на потоке запросов.
"""

import time

from labs.common import array_length

# --- Задание 1: кольцевой буфер (ring buffer) -------------------------------


class RingBuffer:
    """Кольцевой буфер фиксированного размера на массиве с указателями.

    Массив создаётся один раз под capacity ячеек и не растёт. Два указателя:
      _head — индекс самого старого элемента (откуда читаем/вытесняем);
      _tail — индекс, куда ляжет следующий push.
    Оба двигаются по кругу через `% capacity`. Отдельный счётчик _count хранит
    число реально занятых ячеек (отличить «пусто» от «полно», когда head == tail).

    При переполнении (буфер полон, а пришёл новый push) самый старый элемент
    перезаписывается — head сдвигается вперёд. Это и нужно для sliding window:
    старые отметки времени должны уезжать.
    """

    def __init__(self, capacity: int) -> None:
        if capacity <= 0:
            raise ValueError("capacity кольцевого буфера должен быть > 0.")
        self._capacity: int = capacity
        # фиксированный массив: создаём один раз и больше не меняем размер
        self._data: list = []
        i = 0
        while i < capacity:
            self._data.append(None)
            i += 1
        self._head: int = 0  # индекс самого старого элемента
        self._tail: int = 0  # индекс под следующую запись
        self._count: int = 0  # сколько ячеек занято

    def push(self, value) -> None:
        """Положить элемент. Если буфер полон — перезаписать самый старый."""
        self._data[self._tail] = value
        self._tail = (self._tail + 1) % self._capacity
        if self._count == self._capacity:
            # буфер был полон: tail догнал head, самый старый элемент затёрт —
            # двигаем head, чтобы он указывал на новый «самый старый»
            self._head = (self._head + 1) % self._capacity
        else:
            self._count += 1

    def pop(self):
        """Извлечь и вернуть самый старый элемент (FIFO). None, если пусто."""
        if self._count == 0:
            return None
        value = self._data[self._head]
        self._data[self._head] = None
        self._head = (self._head + 1) % self._capacity
        self._count -= 1
        return value

    def peek_oldest(self):
        """Посмотреть самый старый элемент, не извлекая его. None, если пусто."""
        if self._count == 0:
            return None
        return self._data[self._head]

    def is_full(self) -> bool:
        """Все ячейки заняты."""
        return self._count == self._capacity

    def is_empty(self) -> bool:
        """Нет ни одного элемента."""
        return self._count == 0

    def to_list(self) -> list:
        """Содержимое от самого старого к самому новому (для тестов/печати)."""
        result: list = []
        i = 0
        idx = self._head
        while i < self._count:
            result.append(self._data[idx])
            idx = (idx + 1) % self._capacity
            i += 1
        return result

    def __len__(self) -> int:
        return self._count


# --- Задание 2: token bucket -------------------------------------------------


class TokenBucket:
    """Token Bucket: ведро ёмкости capacity, токены капают со скоростью rate/сек.

    Каждый разрешённый запрос «съедает» один токен. Токены пополняются непрерывно
    (rate штук в секунду) до потолка capacity. Если в ведре есть токен — запрос
    проходит и токен списывается, иначе запрос отклоняется.

    Особенность: ведро допускает всплеск (burst) — до capacity запросов подряд,
    пока накоплены токены. Время не берётся из реальных часов: метод allow(now)
    получает «текущее время» снаружи, что делает поведение детерминированным.
    """

    def __init__(self, capacity: float, rate: float, start: float = 0.0) -> None:
        if capacity <= 0:
            raise ValueError("capacity (ёмкость ведра) должна быть > 0.")
        if rate <= 0:
            raise ValueError("rate (скорость пополнения) должна быть > 0.")
        self._capacity: float = float(capacity)
        self._rate: float = float(rate)
        # стартуем с полным ведром — это даёт право на начальный всплеск
        self._tokens: float = float(capacity)
        self._last: float = start  # время последнего пополнения

    def _refill(self, now: float) -> None:
        """Долить токены за прошедшее время: rate * dt, но не выше capacity."""
        if now < self._last:
            # время не должно идти назад; защищаемся от рассинхрона часов
            return
        dt = now - self._last
        self._tokens = min(self._capacity, self._tokens + dt * self._rate)
        self._last = now

    def allow(self, now: float, cost: float = 1.0) -> bool:
        """Разрешить запрос в момент now. Списывает cost токенов, если хватает."""
        self._refill(now)
        if self._tokens >= cost:
            self._tokens -= cost
            return True
        return False

    def available_tokens(self, now: float) -> float:
        """Сколько токенов доступно к моменту now (с учётом пополнения)."""
        self._refill(now)
        return self._tokens


# --- Задание 3: leaky bucket -------------------------------------------------


class LeakyBucket:
    """Leaky Bucket: очередь объёма capacity, которая «вытекает» со скоростью rate.

    Метафора: ведро с дыркой в дне. Запросы «наливаются» в ведро, а вытекают
    равномерно — rate штук в секунду. Если к приходу запроса в ведре есть место
    (с учётом уже вытекшего объёма) — запрос принимается, иначе отклоняется
    (overflow). В отличие от token bucket, leaky bucket сглаживает поток до
    равномерного и НЕ пропускает резкий всплеск целиком.

    Уровень воды храним числом (_water). Перед каждым запросом «сливаем» то, что
    успело вытечь за dt: water -= rate * dt (не ниже нуля).
    """

    def __init__(self, capacity: float, rate: float, start: float = 0.0) -> None:
        if capacity <= 0:
            raise ValueError("capacity (объём ведра) должна быть > 0.")
        if rate <= 0:
            raise ValueError("rate (скорость утечки) должна быть > 0.")
        self._capacity: float = float(capacity)
        self._rate: float = float(rate)
        self._water: float = 0.0  # текущий уровень воды (стартуем с пустого ведра)
        self._last: float = start  # время последнего слива

    def _leak(self, now: float) -> None:
        """Слить воду, вытекшую за прошедшее время: rate * dt, но не ниже нуля."""
        if now < self._last:
            return
        dt = now - self._last
        self._water = max(0.0, self._water - dt * self._rate)
        self._last = now

    def allow(self, now: float, amount: float = 1.0) -> bool:
        """Разрешить запрос в момент now: налить amount, если ведро не переполнится."""
        self._leak(now)
        if self._water + amount <= self._capacity:
            self._water += amount
            return True
        return False

    def water_level(self, now: float) -> float:
        """Текущий уровень воды к моменту now (с учётом утечки)."""
        self._leak(now)
        return self._water


# --- Задание 4: sliding window log ------------------------------------------


class SlidingWindowLog:
    """Sliding Window Log: точное скользящее окно на кольцевом буфере времён.

    Храним отметки времени последних запросов. Запрос в момент now разрешается,
    если число запросов в окне (now - window_size, now] строго меньше limit.
    Старые отметки (вышедшие за левую границу окна) выкидываются.

    Кольцевой буфер на limit ячеек: больше limit отметок в окне всё равно жить
    не может (на limit+1-й запрос мы скажем «нет»), поэтому размера буфера хватает.
    Это самый точный алгоритм — без «скачка» на границе окна, но платит памятью
    (хранит каждый разрешённый запрос).
    """

    def __init__(self, limit: int, window_size: float) -> None:
        if limit <= 0:
            raise ValueError("limit должен быть > 0.")
        if window_size <= 0:
            raise ValueError("window_size должен быть > 0.")
        self._limit: int = limit
        self._window: float = float(window_size)
        # буфер ровно под limit живых отметок времени
        self._log: RingBuffer = RingBuffer(limit)

    def _evict_old(self, now: float) -> None:
        """Выбросить отметки, вышедшие за левую границу окна (now - window]."""
        boundary = now - self._window
        # самые старые отметки лежат в голове буфера; чистим, пока они «протухли»
        while not self._log.is_empty() and self._log.peek_oldest() <= boundary:
            self._log.pop()

    def allow(self, now: float) -> bool:
        """Разрешить запрос в момент now, если в окне меньше limit запросов."""
        self._evict_old(now)
        if array_length(self._log.to_list()) < self._limit:
            self._log.push(now)
            return True
        return False

    def count(self, now: float) -> int:
        """Сколько запросов в окне к моменту now (после очистки старых)."""
        self._evict_old(now)
        return array_length(self._log.to_list())


# --- Задание 5: sliding window counter --------------------------------------


class SlidingWindowCounter:
    """Sliding Window Counter: дешёвое приближение окна на двух счётчиках.

    Вместо хранения каждого запроса держим два счётчика — для текущего
    фиксированного окна и для предыдущего. Оценка нагрузки в скользящем окне:

        estimated = prev_count * (доля предыдущего окна, попавшая в скольжение)
                    + curr_count

    Доля предыдущего окна = (window_size - время, прошедшее в текущем окне) /
    window_size. Запрос разрешается, если estimated < limit. Память — O(1),
    точность ниже, чем у log (на границе возможна небольшая погрешность), но
    именно так считает rate limit nginx и многие API gateway.
    """

    def __init__(self, limit: int, window_size: float, start: float = 0.0) -> None:
        if limit <= 0:
            raise ValueError("limit должен быть > 0.")
        if window_size <= 0:
            raise ValueError("window_size должен быть > 0.")
        self._limit: int = limit
        self._window: float = float(window_size)
        # номер окна, в котором мы сейчас находимся (now // window)
        self._current_window: int = int(start // self._window)
        self._curr_count: int = 0  # счётчик текущего окна
        self._prev_count: int = 0  # счётчик предыдущего окна

    def _roll(self, now: float) -> None:
        """Перемотать окна, если now ушло в следующее (или дальше) окно."""
        window_index = int(now // self._window)
        if window_index == self._current_window:
            return
        if window_index == self._current_window + 1:
            # сдвинулись ровно на одно окно: текущее становится предыдущим
            self._prev_count = self._curr_count
        else:
            # проскочили сразу несколько окон — предыдущее окно уже неактуально
            self._prev_count = 0
        self._curr_count = 0
        self._current_window = window_index

    def _estimated(self, now: float) -> float:
        """Взвешенная оценка числа запросов в скользящем окне к моменту now."""
        elapsed_in_current = now - self._current_window * self._window
        prev_weight = (self._window - elapsed_in_current) / self._window
        if prev_weight < 0:
            prev_weight = 0.0
        return self._prev_count * prev_weight + self._curr_count

    def allow(self, now: float) -> bool:
        """Разрешить запрос в момент now, если оценка нагрузки меньше limit."""
        self._roll(now)
        if self._estimated(now) < self._limit:
            self._curr_count += 1
            return True
        return False

    def estimated_count(self, now: float) -> float:
        """Текущая взвешенная оценка нагрузки к моменту now."""
        self._roll(now)
        return self._estimated(now)


# --- Задание 7: меню и демонстрация -----------------------------------------


def _read_int(prompt: str, default: int) -> int:
    """Читает целое число; пустой ввод => default; повтор при неверном вводе."""
    while True:
        raw = input(prompt).strip()
        if raw == "":
            return default
        try:
            return int(raw)
        except ValueError:
            print("Это не целое число, попробуйте снова.")


def _read_float(prompt: str, default: float) -> float:
    """Читает число с плавающей точкой; пустой ввод => default."""
    while True:
        raw = input(prompt).strip()
        if raw == "":
            return default
        try:
            return float(raw)
        except ValueError:
            print("Это не число, попробуйте снова.")


def _build_limiters(capacity: float, rate: float, limit: int, window: float):
    """Собирает по одному экземпляру каждого алгоритма с общими часами от 0."""
    return [
        ("token bucket", TokenBucket(capacity=capacity, rate=rate, start=0.0)),
        ("leaky bucket", LeakyBucket(capacity=capacity, rate=rate, start=0.0)),
        ("sliding window log", SlidingWindowLog(limit=limit, window_size=window)),
        ("sliding window counter", SlidingWindowCounter(limit=limit, window_size=window, start=0.0)),
    ]


def demo_burst() -> None:
    """Показывает реакцию всех алгоритмов на всплеск: 10 запросов в момент t=0.

    Хорошо видно разницу: token bucket пропускает всплеск до ёмкости ведра,
    leaky bucket — тоже до объёма, а скользящие окна — до limit запросов.
    """
    print("\nВсплеск: 10 запросов одновременно в момент t=0.")
    print("Параметры: capacity/limit=5, rate=1/сек, окно=10 сек.\n")
    limiters = _build_limiters(capacity=5, rate=1, limit=5, window=10)
    for name, lim in limiters:
        allowed = 0
        i = 0
        while i < 10:
            if lim.allow(0.0):
                allowed += 1
            i += 1
        print(f"  {name:<24} пропущено {allowed} из 10")
    print("\nИтог: каждый алгоритм пропустил примерно «ёмкость» запросов и отбил остальные.")


def demo_steady() -> None:
    """Показывает восстановление: запрос раз в секунду в течение 8 секунд.

    При rate=1/сек равномерный поток проходит почти полностью — лимитеры
    успевают пополняться/вытекать между запросами.
    """
    print("\nРавномерный поток: по одному запросу каждую секунду, 8 секунд.")
    print("Параметры: capacity/limit=3, rate=1/сек, окно=3 сек.\n")
    limiters = _build_limiters(capacity=3, rate=1, limit=3, window=3)
    for name, lim in limiters:
        verdicts = []
        t = 0
        while t < 8:
            verdicts.append("+" if lim.allow(float(t)) else "-")
            t += 1
        print(f"  {name:<24} {' '.join(verdicts)}")
    print("\n(+ разрешён, - отклонён) Равномерный поток в пределах rate проходит стабильно.")


def menu() -> None:
    capacity = 5.0
    rate = 1.0
    limit = 5
    window = 10.0
    # в интерактиве за часы берём реальное монотонное время
    clock = time.monotonic

    while True:
        print("\n" + "=" * 40)
        print("Меню (rate limiting):")
        print(f"  Текущие параметры: capacity/limit={limit}, rate={rate}/сек, окно={window} сек")
        print("  1. Задать параметры (capacity, rate, limit, окно)")
        print("  2. Один запрос через token bucket (реальное время)")
        print("  3. Один запрос через leaky bucket (реальное время)")
        print("  4. Один запрос через sliding window log (реальное время)")
        print("  5. Один запрос через sliding window counter (реальное время)")
        print("  6. Демонстрация всплеска (burst, t=0)")
        print("  7. Демонстрация равномерного потока")
        print("  0. Выход")

        choice = input("Выберите пункт: ").strip()

        if choice == "0":
            print("Выход.")
            return
        if choice == "1":
            capacity = _read_float(f"capacity [{capacity}]: ", capacity)
            rate = _read_float(f"rate в секунду [{rate}]: ", rate)
            limit = _read_int(f"limit [{limit}]: ", limit)
            window = _read_float(f"окно в секундах [{window}]: ", window)
            print("Параметры обновлены.")
        elif choice in ("2", "3", "4", "5"):
            now = clock()
            if choice == "2":
                lim = TokenBucket(capacity=capacity, rate=rate, start=now)
            elif choice == "3":
                lim = LeakyBucket(capacity=capacity, rate=rate, start=now)
            elif choice == "4":
                lim = SlidingWindowLog(limit=limit, window_size=window)
            else:
                lim = SlidingWindowCounter(limit=limit, window_size=window, start=now)
            verdict = "разрешён" if lim.allow(now) else "отклонён"
            print(f"Запрос в момент now={now:.3f}: {verdict}")
        elif choice == "6":
            demo_burst()
        elif choice == "7":
            demo_steady()
        else:
            print("Неизвестный пункт меню, попробуйте снова.")


def main() -> None:
    menu()


if __name__ == "__main__":
    main()
