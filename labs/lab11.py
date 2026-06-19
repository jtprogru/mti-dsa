"""
Задания:

1. Реализовать собственную полиномиальную хеш-функцию для строк (без встроенного
   hash) — она понадобится и кольцу, и bloom-фильтру. Показать, что обычное
   распределение ключей по нодам через `hash(key) % N` при изменении числа нод N
   ребалансит почти все ключи.
2. Реализовать consistent hashing — хеш-кольцо: ноды раскладываются по кольцу
   значений хеша, а ключ обслуживает первая нода по часовой стрелке. Поддержать
   add_node / remove_node / get_node(key). Сравнить долю «переехавших» ключей
   при добавлении ноды с наивным `hash % N`.
3. Добавить виртуальные ноды (replicas): одна физическая нода представлена на
   кольце несколькими точками. Это выравнивает нагрузку и уменьшает перекос при
   добавлении/удалении нод.
4. Реализовать bloom filter «с нуля»: битовый массив (на списке int) и k хеш-функций
   (одна базовая хеш-функция с разными «солями»). Поддержать add(item) и
   contains(item). Показать ключевое свойство: ложноотрицательных НЕТ (всё
   добавленное гарантированно contains==True), но возможны ложноположительные.
5. В меню продемонстрировать: ребаланс `hash % N` против кольца при добавлении
   ноды, влияние виртуальных нод на равномерность, накопление ложноположительных
   срабатываний bloom-фильтра.
"""

from labs.common import array_length

# --- Задание 1: хеш-функция -------------------------------------------------

# Маска 64 бита: держим хеш в фиксированном беззнаковом диапазоне [0, 2^64).
# Без неё полиномиальный хеш рос бы неограниченно (в Python int безразмерный),
# а нам нужно «кольцо» конечного размера и стабильная раскладка по битам.
_MASK64 = (1 << 64) - 1


def hash_str(key: str, salt: int = 0) -> int:
    """Полиномиальный хеш строки по схеме Горнера, база 31, в кольце 2^64.

    `salt` подмешивается в начальное состояние — так из одной функции получаем
    «семейство» независимых хешей (нужно для k хеш-функций bloom-фильтра и для
    разнесения виртуальных нод на кольце). Дублируем функцию внутри lab11, чтобы
    не зависеть от приватного кода lab05.
    """
    h = (salt * 0x9E3779B1 + 1) & _MASK64  # затравка зависит от соли
    for ch in key:
        h = (h * 31 + ord(ch)) & _MASK64
    # Финальное перемешивание (avalanche, как в splitmix64): без него короткие
    # строки дают мелкие хеши, кучкующиеся в начале 64-битного диапазона, и на
    # кольце все ключи свалились бы на одну ноду. Перемешивание «размазывает»
    # даже близкие хеши по всему пространству [0, 2^64).
    h = (h ^ (h >> 30)) & _MASK64
    h = (h * 0xBF58476D1CE4E5B9) & _MASK64
    h = (h ^ (h >> 27)) & _MASK64
    h = (h * 0x94D049BB133111EB) & _MASK64
    h = (h ^ (h >> 31)) & _MASK64
    return h


def hash_key(key, salt: int = 0) -> int:
    """Хеш произвольного ключа: int и str приводим к строке и хешируем единообразно."""
    return hash_str(str(key), salt)


# --- Задание 1 (демо-контраст): наивное распределение hash % N --------------


def naive_node(key, num_nodes: int) -> int:
    """Наивное шардирование: номер ноды как остаток хеша по числу нод.

    Это та самая схема `hash(key) % N`, которая ломается при изменении N:
    меняется делитель — меняется остаток почти у всех ключей.
    """
    if num_nodes <= 0:
        raise ValueError("num_nodes должно быть положительным.")
    return hash_key(key) % num_nodes


def naive_rebalanced_fraction(keys: list, num_nodes: int) -> float:
    """Доля ключей, сменивших ноду при росте числа нод N -> N+1 в схеме hash % N.

    Для каждого ключа сравниваем naive_node(key, N) и naive_node(key, N+1).
    Возвращает долю «переехавших» (обычно близка к 1 — почти всё ребалансится).
    """
    total = array_length(keys)
    if total == 0:
        return 0.0
    moved = 0
    for key in keys:
        if naive_node(key, num_nodes) != naive_node(key, num_nodes + 1):
            moved += 1
    return moved / total


# --- Задания 2-3: consistent hashing (хеш-кольцо + виртуальные ноды) ---------


class ConsistentHashRing:
    """Хеш-кольцо: ноды и ключи отображаются в одно пространство хешей [0, 2^64).

    Ключ обслуживает первая нода по часовой стрелке от позиции ключа на кольце
    (а если ключ «правее» всех точек — кольцо замыкается на первую точку).

    Виртуальные ноды (replicas): каждая физическая нода представлена на кольце
    `replicas` точками (солим имя ноды номером реплики). Чем больше реплик, тем
    равномернее ключи распределяются между нодами и тем меньше перекос при
    добавлении/удалении ноды.

    Внутреннее устройство:
      _ring  — отсортированный по позиции список пар [position, node_name];
               держим его всегда в порядке возрастания, чтобы get_node делал
               бинарный поиск первой точки >= hash(key).
    """

    def __init__(self, replicas: int = 100) -> None:
        if replicas <= 0:
            raise ValueError("replicas должно быть положительным.")
        self._replicas: int = replicas
        # _ring — список [position, node]; поддерживаем отсортированным по position.
        self._ring: list[list] = []
        self._nodes: list = []  # имена физических нод (для статистики/печати)

    def _vnode_position(self, node, replica: int) -> int:
        """Позиция виртуальной ноды на кольце: хеш имени ноды с солью-номером реплики."""
        return hash_key(f"{node}#{replica}", salt=replica)

    def _insort(self, position: int, node) -> None:
        """Вставить точку, сохранив сортировку _ring по position (вставка в нужное место)."""
        lo = 0
        hi = array_length(self._ring)
        while lo < hi:
            mid = (lo + hi) // 2
            if self._ring[mid][0] < position:
                lo = mid + 1
            else:
                hi = mid
        self._ring.insert(lo, [position, node])

    def add_node(self, node) -> None:
        """Добавить физическую ноду — это `replicas` точек на кольце."""
        for n in self._nodes:
            if n == node:
                return  # нода уже есть — не дублируем
        self._nodes.append(node)
        replica = 0
        while replica < self._replicas:
            self._insort(self._vnode_position(node, replica), node)
            replica += 1

    def remove_node(self, node) -> bool:
        """Удалить физическую ноду со всеми её виртуальными точками. True, если была."""
        found = False
        i = 0
        while i < array_length(self._nodes):
            if self._nodes[i] == node:
                self._nodes.pop(i)
                found = True
                break
            i += 1
        if not found:
            return False
        # выкидываем все точки этой ноды (фильтрация чужих обратно в _ring)
        kept: list[list] = []
        for point in self._ring:
            if point[1] != node:
                kept.append(point)
        self._ring = kept
        return True

    def get_node(self, key):
        """Нода, отвечающая за ключ: первая точка по часовой стрелке (>= hash(key)).

        Если хеш ключа больше всех позиций на кольце — замыкаемся на первую точку
        (кольцо «по часовой стрелке» уходит за максимум и возвращается к минимуму).
        Поиск — бинарный по отсортированному _ring, O(log V).
        """
        size = array_length(self._ring)
        if size == 0:
            raise ValueError("Кольцо пустое: сначала добавьте ноды.")
        h = hash_key(key)
        # бинарный поиск первой точки с position >= h
        lo = 0
        hi = size
        while lo < hi:
            mid = (lo + hi) // 2
            if self._ring[mid][0] < h:
                lo = mid + 1
            else:
                hi = mid
        if lo == size:
            lo = 0  # замыкание кольца
        return self._ring[lo][1]

    def distribution(self, keys: list) -> dict:
        """Сколько ключей попадает на каждую физическую ноду (для оценки равномерности)."""
        counts: dict = {}
        for node in self._nodes:
            counts[node] = 0
        for key in keys:
            node = self.get_node(key)
            counts[node] += 1
        return counts

    def nodes(self) -> list:
        """Список физических нод на кольце."""
        return list(self._nodes)

    def __len__(self) -> int:
        """Число точек на кольце (физические ноды * replicas)."""
        return array_length(self._ring)


def ring_rebalanced_fraction(keys: list, nodes: list, new_node, replicas: int = 100) -> float:
    """Доля ключей, сменивших ноду на кольце при добавлении одной ноды.

    Сравниваем get_node ДО и ПОСЛЕ add_node(new_node) на одном наборе ключей.
    На кольце переезжает лишь малая доля (≈ 1/(N+1)) — переезжают только ключи
    того сегмента, который «отрезала» новая нода, а не все ключи как в hash % N.
    """
    before = ConsistentHashRing(replicas=replicas)
    for node in nodes:
        before.add_node(node)

    after = ConsistentHashRing(replicas=replicas)
    for node in nodes:
        after.add_node(node)
    after.add_node(new_node)

    total = array_length(keys)
    if total == 0:
        return 0.0
    moved = 0
    for key in keys:
        if before.get_node(key) != after.get_node(key):
            moved += 1
    return moved / total


# --- Задание 4: bloom filter ------------------------------------------------


class BloomFilter:
    """Вероятностная структура «принадлежит ли элемент множеству».

    Гарантии:
      - НЕТ ложноотрицательных: если элемент добавляли, contains вернёт True всегда;
      - возможны ложноположительные: contains может вернуть True для элемента,
        которого не добавляли (его биты случайно «закрыли» другие элементы).

    Устройство: битовый массив на `size` бит и `num_hashes` (k) хеш-функций.
    Биты пакуем в список целых по 64 бита (битовый массив реализуем руками, без
    bytearray/set). add ставит k бит, contains проверяет, что все k бит стоят.
    """

    _WORD_BITS = 64  # бит в одном «слове» (элементе списка)

    def __init__(self, size: int = 1024, num_hashes: int = 3) -> None:
        if size <= 0:
            raise ValueError("size должно быть положительным.")
        if num_hashes <= 0:
            raise ValueError("num_hashes должно быть положительным.")
        self._size: int = size
        self._k: int = num_hashes
        self._count: int = 0  # сколько раз вызывали add (для оценки заполнения)
        # битовый массив: список слов по 64 бита, изначально все нули
        words = (size + self._WORD_BITS - 1) // self._WORD_BITS
        self._bits: list[int] = []
        i = 0
        while i < words:
            self._bits.append(0)
            i += 1

    def _positions(self, item) -> list:
        """k позиций бит для элемента: одна хеш-функция с k разными солями."""
        positions: list = []
        salt = 0
        while salt < self._k:
            positions.append(hash_key(item, salt=salt) % self._size)
            salt += 1
        return positions

    def _set_bit(self, pos: int) -> None:
        """Поставить бит pos в битовом массиве."""
        word = pos // self._WORD_BITS
        offset = pos % self._WORD_BITS
        self._bits[word] |= (1 << offset)

    def _get_bit(self, pos: int) -> bool:
        """Стоит ли бит pos."""
        word = pos // self._WORD_BITS
        offset = pos % self._WORD_BITS
        return (self._bits[word] >> offset) & 1 == 1

    def add(self, item) -> None:
        """Добавить элемент: выставить все k его бит."""
        for pos in self._positions(item):
            self._set_bit(pos)
        self._count += 1

    def contains(self, item) -> bool:
        """Вероятностная проверка принадлежности.

        True — элемент, ВОЗМОЖНО, есть (может быть ложноположительным).
        False — элемента ТОЧНО нет (ложноотрицательных не бывает).
        """
        for pos in self._positions(item):
            if not self._get_bit(pos):
                return False  # хотя бы один бит не стоит -> элемента точно не добавляли
        return True

    def estimated_false_positive_rate(self) -> float:
        """Оценка вероятности ложноположительного: (1 - e^(-k*n/m))^k.

        m = size (бит), n = число добавленных элементов, k = число хеш-функций.
        Считаем e^x руками рядом, чтобы не тянуть math (в духе «без магии»).
        """
        if self._count == 0:
            return 0.0
        x = -(self._k * self._count) / self._size
        e_x = _exp(x)
        base = 1.0 - e_x
        # возведение в степень k натуральным числом
        result = 1.0
        i = 0
        while i < self._k:
            result *= base
            i += 1
        return result

    def fill_ratio(self) -> float:
        """Доля установленных бит — насколько фильтр «забит»."""
        set_bits = 0
        word = 0
        while word < array_length(self._bits):
            value = self._bits[word]
            while value:
                set_bits += value & 1
                value >>= 1
            word += 1
        return set_bits / self._size

    def __len__(self) -> int:
        """Сколько раз вызывали add."""
        return self._count


def _exp(x: float) -> float:
    """Экспонента e^x рядом Тейлора (без math) — для оценки FPR bloom-фильтра."""
    term = 1.0
    result = 1.0
    n = 1
    while n < 50:
        term *= x / n
        result += term
        n += 1
    return result


# --- Задание 5: меню и демонстрации -----------------------------------------


def _read_int(prompt: str, default: int) -> int:
    """Читает целое число; пустой ввод -> default; при ошибке повторяет запрос."""
    while True:
        raw = input(prompt).strip()
        if raw == "":
            return default
        try:
            return int(raw)
        except ValueError:
            print("Это не целое число, попробуйте снова.")


def _sample_keys(count: int) -> list:
    """Набор строковых ключей вида key-0..key-(count-1) для демонстраций."""
    keys: list = []
    i = 0
    while i < count:
        keys.append(f"key-{i}")
        i += 1
    return keys


def demo_naive_vs_ring() -> None:
    """Показывает, почему hash % N ребалансит почти всё, а кольцо — малую долю.

    Берём большой набор ключей и 4 ноды. Добавляем 5-ю ноду и считаем долю
    ключей, сменивших ноду, в обеих схемах.
    """
    keys = _sample_keys(10000)
    nodes = ["node-A", "node-B", "node-C", "node-D"]
    new_node = "node-E"

    naive = naive_rebalanced_fraction(keys, num_nodes=array_length(nodes))
    ring = ring_rebalanced_fraction(keys, nodes, new_node, replicas=100)

    print("\nДобавляем 5-ю ноду к 4 (набор 10000 ключей):")
    print(f"  hash % N        : переехало {naive * 100:.1f}% ключей")
    print(f"  consistent ring : переехало {ring * 100:.1f}% ключей")
    print(
        "\nИтог: hash % N меняет делитель -> остаток меняется почти у всех ключей; "
        "на кольце новая нода забирает только свой сегмент (≈ 1/(N+1))."
    )


def demo_virtual_nodes() -> None:
    """Показывает влияние числа виртуальных нод на равномерность раскладки ключей."""
    keys = _sample_keys(10000)
    nodes = ["node-A", "node-B", "node-C", "node-D"]

    for replicas in (1, 10, 100):
        ring = ConsistentHashRing(replicas=replicas)
        for node in nodes:
            ring.add_node(node)
        dist = ring.distribution(keys)
        counts = [dist[node] for node in nodes]
        smallest = counts[0]
        largest = counts[0]
        for c in counts:
            if c < smallest:
                smallest = c
            if c > largest:
                largest = c
        skew = (largest - smallest) / (array_length(keys) / array_length(nodes))
        print(f"\nreplicas={replicas:>3}: {dist}")
        print(f"  перекос (max-min относительно идеала): {skew * 100:.1f}%")
    print("\nИтог: чем больше виртуальных нод, тем ровнее ключи раскладываются по нодам.")


def demo_bloom() -> None:
    """Показывает: ложноотрицательных нет, ложноположительные накапливаются."""
    bloom = BloomFilter(size=1024, num_hashes=3)
    added = _sample_keys(200)
    for item in added:
        bloom.add(item)

    # ложноотрицательных не бывает: всё добавленное обязано находиться
    all_found = True
    for item in added:
        if not bloom.contains(item):
            all_found = False
    print(f"\nДобавлено {array_length(added)} элементов в фильтр (size=1024, k=3).")
    print(f"  все добавленные находятся (нет ложноотрицательных): {all_found}")

    # проверяем элементы, которых НЕ добавляли — часть может ложно сработать
    probes = _sample_keys(10000)
    false_positives = 0
    checked = 0
    for item in probes:
        # берём только те, что точно не добавляли
        if item not in added:
            checked += 1
            if bloom.contains(item):
                false_positives += 1
    rate = false_positives / checked if checked else 0.0
    print(f"  ложноположительных среди {checked} чужих: {false_positives} ({rate * 100:.2f}%)")
    print(f"  оценка FPR по формуле: {bloom.estimated_false_positive_rate() * 100:.2f}%")
    print(f"  заполнение битового массива: {bloom.fill_ratio() * 100:.1f}%")
    print(
        "\nИтог: False = элемента ТОЧНО нет; True = ВОЗМОЖНО есть. Чем больше "
        "элементов, тем выше доля ложноположительных."
    )


def menu() -> None:
    while True:
        print("\n" + "=" * 40)
        print("Меню (consistent hashing и bloom filter):")
        print("  1. hash % N против кольца при добавлении ноды")
        print("  2. Влияние виртуальных нод на равномерность")
        print("  3. Bloom filter: ложноотрицательные и ложноположительные")
        print("  4. Своё кольцо: разложить ключи по нодам")
        print("  5. Свой bloom filter: добавить и проверить элемент")
        print("  0. Выход")

        choice = input("Выберите пункт: ").strip()

        if choice == "0":
            print("Выход.")
            return
        if choice == "1":
            demo_naive_vs_ring()
        elif choice == "2":
            demo_virtual_nodes()
        elif choice == "3":
            demo_bloom()
        elif choice == "4":
            replicas = _read_int("Виртуальных нод на физическую (Enter=100): ", 100)
            num_nodes = _read_int("Сколько нод (Enter=4): ", 4)
            num_keys = _read_int("Сколько ключей разложить (Enter=10000): ", 10000)
            ring = ConsistentHashRing(replicas=replicas)
            i = 0
            while i < num_nodes:
                ring.add_node(f"node-{i}")
                i += 1
            dist = ring.distribution(_sample_keys(num_keys))
            print("Раскладка ключей по нодам:")
            for node in ring.nodes():
                print(f"  {node}: {dist[node]}")
        elif choice == "5":
            size = _read_int("Размер битового массива (Enter=1024): ", 1024)
            k = _read_int("Число хеш-функций k (Enter=3): ", 3)
            bloom = BloomFilter(size=size, num_hashes=k)
            print("Вводите элементы для добавления, пустая строка — закончить.")
            while True:
                item = input("  add: ").strip()
                if item == "":
                    break
                bloom.add(item)
            query = input("Проверить элемент (contains): ").strip()
            result = bloom.contains(query)
            verdict = "ВОЗМОЖНО есть" if result else "ТОЧНО нет"
            print(f"  contains({query!r}) = {result} -> {verdict}")
        else:
            print("Неизвестный пункт меню, попробуйте снова.")


def main() -> None:
    menu()


if __name__ == "__main__":
    main()
