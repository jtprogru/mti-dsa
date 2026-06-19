"""
Задания:

1. Реализовать собственную хеш-функцию для целочисленных и строковых ключей
   (без встроенного hash и dict). Показать, что хеш — это число, а индекс
   ячейки таблицы получается как hash(key) % capacity.
2. Реализовать хеш-таблицу методом цепочек (separate chaining): каждая ячейка —
   список пар (ключ, значение). Поддержать put / get / contains / delete.
3. Реализовать хеш-таблицу с открытой адресацией (open addressing): линейное
   пробирование и двойное хеширование. Корректно удалять элементы через
   «надгробие» (tombstone), чтобы не разрывать цепочку проб.
4. Считать число коллизий в обеих структурах и коэффициент заполнения
   (load factor). При превышении порога — расширять таблицу вдвое с полным
   перехешированием (rehash).
5. В меню продемонстрировать, что происходит при коллизии ключей: вставить
   ключи, попадающие в одну ячейку, и сравнить поведение метода цепочек,
   линейного пробирования и двойного хеширования. Показать срабатывание
   авторасширения.
"""

from labs.common import array_length

# --- Задание 1: хеш-функции -------------------------------------------------


def hash_int(key: int) -> int:
    """Хеш целого числа — само число (для отрицательных берём модуль)."""
    return key if key >= 0 else -key


def hash_str(key: str) -> int:
    """Полиномиальный хеш строки: h = s[0]*B^(n-1) + ... + s[n-1], база B = 31.

    База 31 — классический выбор: нечётное простое число, умножение на которое
    легко раскладывается процессором (31*h == (h << 5) - h). Накапливаем хеш
    схемой Горнера за один проход по символам.
    """
    h = 0
    for ch in key:
        h = h * 31 + ord(ch)
    return h


def hash_key(key) -> int:
    """Диспетчер хеширования: int -> hash_int, str -> hash_str.

    Для остальных типов бросает TypeError — таблица работает только с
    хешируемыми «вручную» ключами (числа и строки).
    """
    if isinstance(key, int):
        return hash_int(key)
    if isinstance(key, str):
        return hash_str(key)
    raise TypeError(
        f"Неподдерживаемый тип ключа: {type(key).__name__}. Ожидается int или str."
    )


# --- Задание 2: хеш-таблица методом цепочек ---------------------------------


class HashMapChaining:
    """Хеш-таблица с разрешением коллизий методом цепочек.

    Каждая ячейка (бакет) — список пар [ключ, значение]. При коллизии (два
    разных ключа дают один индекс) новая пара просто дописывается в список
    этого бакета, поэтому таблица никогда не «переполняется».

    Поля:
      collisions — счётчик коллизий: увеличивается, когда новый ключ попадает
                   в уже непустой бакет.
    """

    def __init__(self, capacity: int = 8) -> None:
        self._capacity: int = capacity
        self._size: int = 0
        self.collisions: int = 0
        self._max_load: float = 0.75
        self._buckets: list[list[list]] = []
        i = 0
        while i < capacity:
            self._buckets.append([])
            i += 1

    def _index(self, key) -> int:
        """Индекс бакета: свёртка хеша по размеру таблицы."""
        return hash_key(key) % self._capacity

    def put(self, key, value) -> None:
        """Вставить пару или обновить значение существующего ключа."""
        bucket = self._buckets[self._index(key)]
        for pair in bucket:
            if pair[0] == key:
                pair[1] = value  # обновление существующего ключа
                return
        if array_length(bucket) > 0:
            self.collisions += 1  # ключ лёг в уже занятый бакет — коллизия
        bucket.append([key, value])
        self._size += 1
        if self.load_factor() > self._max_load:
            self._resize(self._capacity * 2)

    def get(self, key, default=None):
        """Значение по ключу или default, если ключа нет."""
        for pair in self._buckets[self._index(key)]:
            if pair[0] == key:
                return pair[1]
        return default

    def contains(self, key) -> bool:
        """Есть ли ключ в таблице."""
        for pair in self._buckets[self._index(key)]:
            if pair[0] == key:
                return True
        return False

    def delete(self, key) -> bool:
        """Удалить ключ. Возвращает True, если ключ был найден и удалён."""
        bucket = self._buckets[self._index(key)]
        i = 0
        while i < array_length(bucket):
            if bucket[i][0] == key:
                bucket.pop(i)
                self._size -= 1
                return True
            i += 1
        return False

    def load_factor(self) -> float:
        """Коэффициент заполнения: число пар / число бакетов."""
        return self._size / self._capacity

    def _resize(self, new_capacity: int) -> None:
        """Расширить таблицу и заново разложить все пары (rehash)."""
        old_buckets = self._buckets
        self._capacity = new_capacity
        self._buckets = []
        self._size = 0
        self.collisions = 0
        i = 0
        while i < new_capacity:
            self._buckets.append([])
            i += 1
        for bucket in old_buckets:
            for pair in bucket:
                self.put(pair[0], pair[1])

    def keys(self) -> list:
        """Список всех ключей (порядок зависит от раскладки по бакетам)."""
        result: list = []
        for bucket in self._buckets:
            for pair in bucket:
                result.append(pair[0])
        return result

    def items(self) -> list:
        """Список всех пар (ключ, значение)."""
        result: list = []
        for bucket in self._buckets:
            for pair in bucket:
                result.append((pair[0], pair[1]))
        return result

    def print_map(self) -> None:
        """Печатает таблицу по бакетам — видно, где осели коллизии."""
        print(
            f"HashMapChaining: size={self._size}, capacity={self._capacity}, "
            f"load_factor={self.load_factor():.2f}, collisions={self.collisions}"
        )
        i = 0
        while i < self._capacity:
            bucket = self._buckets[i]
            if array_length(bucket) > 0:
                parts = []
                for pair in bucket:
                    parts.append(f"{pair[0]}={pair[1]}")
                print(f"  [{i}] " + " -> ".join(parts))
            i += 1

    def __len__(self) -> int:
        return self._size


# --- Задание 3: открытая адресация ------------------------------------------

# Сентинелы для слотов открытой адресации:
#   _EMPTY   — слот никогда не использовался (на нём поиск останавливается);
#   _DELETED — «надгробие» (tombstone): здесь был элемент, но его удалили.
#              Поиск проходит сквозь надгробие дальше, а вставка может его занять.
_EMPTY = object()
_DELETED = object()


class HashMapOpenAddr:
    """Хеш-таблица с открытой адресацией: все пары живут в одном массиве слотов.

    При коллизии элемент не уходит в список, а ищет другой свободный слот по
    последовательности проб. Поддержаны две стратегии (параметр probe):
      "linear" — линейное пробирование, шаг всегда 1 (idx, idx+1, idx+2, ...);
      "double" — двойное хеширование, шаг зависит от ключа (уменьшает
                 кластеризацию слотов).

    collisions — счётчик коллизий: увеличивается на каждый шаг пробы, который
    наткнулся на слот, занятый ДРУГИМ живым ключом.

    Замечание: capacity держим степенью двойки (8 -> 16 -> 32 ...). Тогда
    нечётный шаг двойного хеширования взаимно прост с capacity и проба обходит
    все слоты.
    """

    def __init__(self, capacity: int = 8, probe: str = "linear") -> None:
        if probe not in ("linear", "double"):
            raise ValueError("probe должен быть 'linear' или 'double'.")
        self._capacity: int = capacity
        self._probe: str = probe
        self._size: int = 0
        self._tombstones: int = 0
        self.collisions: int = 0
        self._max_load: float = 0.5
        self._slots: list = []
        i = 0
        while i < capacity:
            self._slots.append(_EMPTY)
            i += 1

    def _index(self, key) -> int:
        """Первичный индекс (домашний слот) ключа."""
        return hash_key(key) % self._capacity

    def _hash2(self, key) -> int:
        """Вторичный хеш для двойного хеширования (для шага пробы)."""
        return hash_key(key) // self._capacity + 1

    def _probe_step(self, key) -> int:
        """Шаг пробы. linear -> 1; double -> нечётный шаг, зависящий от ключа.

        Нечётный шаг (`... | 1`) гарантированно взаимно прост со степенью
        двойки, поэтому проба обойдёт все слоты и найдёт свободный.
        """
        if self._probe == "linear":
            return 1
        return (self._hash2(key) % self._capacity) | 1

    def put(self, key, value) -> None:
        """Вставить пару или обновить значение существующего ключа.

        Идём по слотам с шагом probe. Если встретили надгробие — запоминаем
        его как кандидата для вставки, но продолжаем искать: вдруг ключ уже
        лежит дальше и его нужно обновить, а не задублировать.
        """
        start = self._index(key)
        step = self._probe_step(key)
        first_tombstone = -1
        i = 0
        idx = start
        while self._slots[idx] is not _EMPTY:
            slot = self._slots[idx]
            if slot is _DELETED:
                if first_tombstone == -1:
                    first_tombstone = idx
            elif slot[0] == key:
                slot[1] = value  # обновление существующего ключа
                return
            else:
                self.collisions += 1  # слот занят чужим ключом — коллизия
            i += 1
            idx = (start + i * step) % self._capacity
        if first_tombstone != -1:
            self._slots[first_tombstone] = [key, value]  # переиспользуем надгробие
            self._tombstones -= 1
        else:
            self._slots[idx] = [key, value]
        self._size += 1
        self._maybe_resize()

    def _find_slot(self, key) -> int:
        """Индекс живого слота с ключом или -1. Сквозь надгробия идём дальше."""
        start = self._index(key)
        step = self._probe_step(key)
        i = 0
        idx = start
        while self._slots[idx] is not _EMPTY:
            slot = self._slots[idx]
            if slot is not _DELETED and slot[0] == key:
                return idx
            i += 1
            idx = (start + i * step) % self._capacity
        return -1

    def get(self, key, default=None):
        """Значение по ключу или default, если ключа нет."""
        idx = self._find_slot(key)
        if idx == -1:
            return default
        return self._slots[idx][1]

    def contains(self, key) -> bool:
        """Есть ли ключ в таблице."""
        return self._find_slot(key) != -1

    def delete(self, key) -> bool:
        """Удалить ключ, поставив надгробие. Возвращает True, если ключ был.

        Важно: нельзя просто очистить слот в _EMPTY — это разорвало бы цепочку
        проб, и get для ключей, вставленных «дальше» по цепочке, перестал бы
        их находить. Поэтому ставим _DELETED (надгробие): поиск идёт сквозь
        него, а вставка может занять его повторно.
        """
        idx = self._find_slot(key)
        if idx == -1:
            return False
        self._slots[idx] = _DELETED
        self._size -= 1
        self._tombstones += 1
        return True

    def load_factor(self) -> float:
        """Коэффициент заполнения по живым парам: size / capacity."""
        return self._size / self._capacity

    def _maybe_resize(self) -> None:
        """Расширить таблицу, если занятых слотов (пары + надгробия) слишком много.

        Учитываем и надгробия: иначе циклы вставок-удалений забили бы таблицу
        надгробиями и пробе негде было бы остановиться.
        """
        if (self._size + self._tombstones) / self._capacity >= self._max_load:
            self._resize(self._capacity * 2)

    def _resize(self, new_capacity: int) -> None:
        """Перехешировать в таблицу нового размера. Надгробия отбрасываются."""
        old_slots = self._slots
        self._capacity = new_capacity
        self._slots = []
        self._size = 0
        self._tombstones = 0
        self.collisions = 0
        i = 0
        while i < new_capacity:
            self._slots.append(_EMPTY)
            i += 1
        for slot in old_slots:
            if slot is not _EMPTY and slot is not _DELETED:
                self.put(slot[0], slot[1])

    def keys(self) -> list:
        """Список всех живых ключей."""
        result: list = []
        for slot in self._slots:
            if slot is not _EMPTY and slot is not _DELETED:
                result.append(slot[0])
        return result

    def items(self) -> list:
        """Список всех живых пар (ключ, значение)."""
        result: list = []
        for slot in self._slots:
            if slot is not _EMPTY and slot is not _DELETED:
                result.append((slot[0], slot[1]))
        return result

    def print_map(self) -> None:
        """Печатает таблицу по слотам: значение, пусто (.) или надгробие."""
        print(
            f"HashMapOpenAddr({self._probe}): size={self._size}, "
            f"capacity={self._capacity}, load_factor={self.load_factor():.2f}, "
            f"collisions={self.collisions}, tombstones={self._tombstones}"
        )
        i = 0
        while i < self._capacity:
            slot = self._slots[i]
            if slot is _EMPTY:
                label = "."
            elif slot is _DELETED:
                label = "<deleted>"
            else:
                label = f"{slot[0]}={slot[1]}"
            print(f"  [{i}] {label}")
            i += 1

    def __len__(self) -> int:
        return self._size


# --- Задание 5: меню и демонстрация коллизий --------------------------------


def _parse_key(raw: str):
    """Преобразует ввод в ключ: целое число, если это число, иначе строку."""
    try:
        return int(raw)
    except ValueError:
        return raw


def _read_key(prompt: str):
    """Читает ключ с клавиатуры (число или строка)."""
    return _parse_key(input(prompt).strip())


def _read_int(prompt: str) -> int:
    """Читает целое число, повторяя запрос при неверном вводе."""
    while True:
        raw = input(prompt).strip()
        try:
            return int(raw)
        except ValueError:
            print("Это не целое число, попробуйте снова.")


def demo_collisions() -> None:
    """Вставляет ключи, попадающие в один индекс, в три разные таблицы.

    Ключи 1, 9, 17 при capacity = 8 дают один и тот же индекс (1 % 8 == 9 % 8
    == 17 % 8 == 1) — это и есть коллизия. Сравниваем, как её разруливают
    цепочки, линейное пробирование и двойное хеширование.
    """
    keys = [1, 9, 17]
    print("\nКлючи", keys, "при capacity=8 все дают индекс 1 — коллизия.\n")

    chaining = HashMapChaining(capacity=8)
    linear = HashMapOpenAddr(capacity=8, probe="linear")
    double = HashMapOpenAddr(capacity=8, probe="double")

    for k in keys:
        chaining.put(k, k * 10)
        linear.put(k, k * 10)
        double.put(k, k * 10)

    chaining.print_map()
    print()
    linear.print_map()
    print()
    double.print_map()
    print(
        "\nИтог: цепочки складывают коллизии в список одного бакета; "
        "открытая адресация раскидывает их по другим слотам "
        "(линейная — подряд, двойное хеширование — с разным шагом)."
    )


def demo_resize() -> None:
    """Показывает авторасширение: вставляем пары, пока таблица не вырастет."""
    table = HashMapChaining(capacity=8)
    print("\nСтартовая capacity =", table._capacity, "(порог load_factor =", table._max_load, ")")
    i = 0
    while i < 8:
        before = table._capacity
        table.put(i, i)
        if table._capacity != before:
            print(f"  после вставки {i + 1}-й пары capacity вырос {before} -> {table._capacity} (rehash)")
        i += 1
    print("Итоговая таблица:")
    table.print_map()


def menu() -> None:
    chaining = HashMapChaining()
    linear = HashMapOpenAddr(probe="linear")
    double = HashMapOpenAddr(probe="double")
    maps = [("цепочки", chaining), ("линейная адресация", linear), ("двойное хеширование", double)]

    while True:
        print("\n" + "=" * 40)
        print("Меню (hash map):")
        print("  1. Добавить пару ключ=значение (во все три таблицы)")
        print("  2. Получить значение по ключу")
        print("  3. Удалить ключ")
        print("  4. Напечатать все три таблицы")
        print("  5. Демонстрация коллизий")
        print("  6. Демонстрация авторасширения (resize)")
        print("  0. Выход")

        choice = input("Выберите пункт: ").strip()

        if choice == "0":
            print("Выход.")
            return
        if choice == "1":
            key = _read_key("Ключ (число или строка): ")
            value = _read_key("Значение: ")
            for _, table in maps:
                table.put(key, value)
            print(f"Добавлено: {key}={value}")
        elif choice == "2":
            key = _read_key("Ключ для поиска: ")
            for name, table in maps:
                print(f"  {name}: {table.get(key, '<нет>')}")
        elif choice == "3":
            key = _read_key("Ключ для удаления: ")
            for name, table in maps:
                ok = table.delete(key)
                print(f"  {name}: {'удалён' if ok else 'не найден'}")
        elif choice == "4":
            for _, table in maps:
                print()
                table.print_map()
        elif choice == "5":
            demo_collisions()
        elif choice == "6":
            demo_resize()
        else:
            print("Неизвестный пункт меню, попробуйте снова.")


def main() -> None:
    menu()


if __name__ == "__main__":
    main()
