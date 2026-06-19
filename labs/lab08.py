"""
Задания:

1. Реализовать узел двусвязного списка руками: поля key, value и две ссылки
   (prev — на предыдущий, next — на следующий узел). Двусвязность нужна, чтобы
   уметь вырезать любой узел из середины за O(1), зная только сам узел.
2. Реализовать LRU-кэш (Least Recently Used) с фиксированной ёмкостью capacity:
   хеш-таблица (здесь допустим встроенный dict — само хранилище не предмет
   лабы, в отличие от lab05) хранит key -> узел, а двусвязный список держит
   порядок использования (от most recently used к least recently used).
3. Операция get(key): вернуть значение за O(1) и пометить ключ как недавно
   использованный — переместить его узел в «голову» списка.
4. Операция put(key, value): вставить/обновить за O(1), переместить узел в
   «голову»; при переполнении вытеснить «хвост» — наименее недавно
   использованный (LRU) ключ.
5. В меню (main) продемонстрировать вытеснение: завести кэш малой ёмкости и
   показать, как обращения к ключам меняют порядок и кого вытесняет переполнение.

Идея заимствует хеш-таблицу из lab05 (быстрый доступ по ключу) и двусвязный
список из lab02 (порядок), соединяя их в одну структуру: dict даёт O(1) поиск
узла, список — O(1) изменение порядка и вытеснение.
"""

# --- Задание 1: узел двусвязного списка -------------------------------------


class Node:
    """Узел двусвязного списка LRU-кэша.

    Хранит пару (key, value) и две ссылки на соседей. Ключ нужен прямо в узле,
    чтобы при вытеснении «хвоста» знать, какой ключ удалить из хеш-таблицы.
    """

    def __init__(self, key=None, value=None) -> None:
        self.key = key
        self.value = value
        self.prev: "Node | None" = None
        self.next: "Node | None" = None


# --- Задание 2-4: LRU-кэш ----------------------------------------------------


class LRUCache:
    """LRU-кэш с вытеснением наименее недавно использованного элемента.

    Внутреннее устройство:
      * _store — хеш-таблица key -> Node (даёт O(1) поиск узла по ключу);
      * двусвязный список с двумя «часовыми» (sentinel) узлами _head и _tail,
        между которыми лежат реальные узлы. Порядок в списке = порядок
        использования: сразу за _head — most recently used (MRU), перед
        _tail — least recently used (LRU).

    Часовые узлы избавляют от проверок на None при вставке/удалении с краёв:
    у любого реального узла всегда есть и prev, и next.

    Все операции (get/put) — O(1): поиск через dict, перецепление ссылок в
    списке — за константу.
    """

    def __init__(self, capacity: int) -> None:
        if capacity < 1:
            raise ValueError("capacity должен быть положительным (>= 1).")
        self._capacity: int = capacity
        self._store: dict = {}  # key -> Node
        # Часовые: _head <-> ... реальные узлы ... <-> _tail
        self._head: Node = Node()  # перед самым свежим (MRU)
        self._tail: Node = Node()  # после самого старого (LRU)
        self._head.next = self._tail
        self._tail.prev = self._head

    # --- внутренние операции над списком (по одному перецеплению ссылок) -----

    def _remove(self, node: Node) -> None:
        """Вырезать узел из списка за O(1) (двусвязность даёт доступ к соседям)."""
        node.prev.next = node.next
        node.next.prev = node.prev

    def _add_front(self, node: Node) -> None:
        """Вставить узел сразу за _head — он становится most recently used."""
        node.prev = self._head
        node.next = self._head.next
        self._head.next.prev = node
        self._head.next = node

    def _move_to_front(self, node: Node) -> None:
        """Пометить узел как недавно использованный: вырезать и вставить в голову."""
        self._remove(node)
        self._add_front(node)

    # --- публичный API -------------------------------------------------------

    def get(self, key, default=None):
        """Вернуть значение по ключу и освежить его (MRU). Иначе — default.

        Любое обращение к ключу считается использованием, поэтому узел
        перемещается в голову списка.
        """
        node = self._store.get(key)
        if node is None:
            return default
        self._move_to_front(node)
        return node.value

    def put(self, key, value) -> None:
        """Вставить/обновить пару за O(1). При переполнении вытеснить LRU.

        Если ключ уже есть — обновляем значение и освежаем узел. Если ключа
        нет — создаём узел, кладём в голову; и, если ёмкость превышена,
        вытесняем «хвост» (наименее недавно использованный ключ).
        """
        node = self._store.get(key)
        if node is not None:
            node.value = value
            self._move_to_front(node)
            return

        new_node = Node(key, value)
        self._store[key] = new_node
        self._add_front(new_node)

        if len(self._store) > self._capacity:
            self._evict()

    def _evict(self) -> None:
        """Вытеснить наименее недавно использованный узел (перед _tail)."""
        lru = self._tail.prev
        self._remove(lru)
        del self._store[lru.key]

    # --- интроспекция (для меню/тестов/демонстрации) -------------------------

    def contains(self, key) -> bool:
        """Есть ли ключ в кэше (без изменения порядка использования)."""
        return key in self._store

    def peek(self, key, default=None):
        """Подсмотреть значение, НЕ освежая ключ (порядок не меняется)."""
        node = self._store.get(key)
        if node is None:
            return default
        return node.value

    def keys_mru_to_lru(self) -> list:
        """Ключи в порядке использования: от самого свежего (MRU) к самому старому (LRU)."""
        result: list = []
        current = self._head.next
        while current is not self._tail:
            result.append(current.key)
            current = current.next
        return result

    def __len__(self) -> int:
        return len(self._store)

    def __contains__(self, key) -> bool:
        return key in self._store

    def print_cache(self) -> None:
        """Печатает содержимое кэша в порядке MRU -> LRU (кого вытеснят последним/первым)."""
        order = self.keys_mru_to_lru()
        print(
            f"LRUCache: size={len(self)}, capacity={self._capacity}  "
            f"(MRU слева, LRU справа — вытесняется крайний справа)"
        )
        if not order:
            print("  <пусто>")
            return
        parts = []
        for key in order:
            parts.append(f"{key}={self.peek(key)}")
        print("  " + " <- ".join(parts))


# --- Задание 5: меню и демонстрация вытеснения ------------------------------


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


def demo_eviction() -> None:
    """Наглядно показывает, как LRU-кэш меняет порядок и кого вытесняет.

    Сценарий на кэше ёмкости 2:
      put(1) put(2)  -> в кэше [2, 1] (2 свежее)
      get(1)         -> 1 освежается, порядок [1, 2]
      put(3)         -> переполнение: вытесняется LRU = 2, в кэше [3, 1]
      get(2)         -> промах (2 уже вытеснен)
      put(4)         -> вытесняется LRU = 1, в кэше [4, 3]
    """
    print("\nLRU-кэш ёмкости 2. Следим за порядком MRU -> LRU.\n")
    cache = LRUCache(capacity=2)

    cache.put(1, "a")
    cache.put(2, "b")
    print("После put(1) put(2):")
    cache.print_cache()

    print("\nget(1) ->", cache.get(1), "(ключ 1 освежён, стал MRU)")
    cache.print_cache()

    cache.put(3, "c")
    print("\nput(3): переполнение, вытесняется LRU (ключ 2):")
    cache.print_cache()

    print("\nget(2) ->", cache.get(2, "<промах>"), "(ключ 2 уже вытеснен)")

    cache.put(4, "d")
    print("\nput(4): снова переполнение, вытесняется LRU (ключ 1):")
    cache.print_cache()

    print(
        "\nИтог: вытесняется не «самый старый по вставке», а наименее недавно "
        "использованный. Обращение get/put переводит ключ в MRU и отодвигает "
        "его момент вытеснения."
    )


def menu() -> None:
    capacity = 3
    cache = LRUCache(capacity=capacity)

    while True:
        print("\n" + "=" * 40)
        print(f"Меню (LRU-кэш, capacity={capacity}):")
        print("  1. put — добавить/обновить пару ключ=значение")
        print("  2. get — получить значение по ключу (освежает ключ)")
        print("  3. peek — подсмотреть значение, НЕ освежая порядок")
        print("  4. Напечатать кэш (порядок MRU -> LRU)")
        print("  5. Демонстрация вытеснения (LRU)")
        print("  6. Пересоздать кэш с новой ёмкостью")
        print("  0. Выход")

        choice = input("Выберите пункт: ").strip()

        if choice == "0":
            print("Выход.")
            return
        if choice == "1":
            key = _read_key("Ключ (число или строка): ")
            value = _read_key("Значение: ")
            cache.put(key, value)
            print(f"put({key}={value}). Текущий порядок:")
            cache.print_cache()
        elif choice == "2":
            key = _read_key("Ключ для get: ")
            print(f"  get({key}) -> {cache.get(key, '<промах>')}")
            cache.print_cache()
        elif choice == "3":
            key = _read_key("Ключ для peek: ")
            print(f"  peek({key}) -> {cache.peek(key, '<нет>')} (порядок не изменён)")
        elif choice == "4":
            cache.print_cache()
        elif choice == "5":
            demo_eviction()
        elif choice == "6":
            capacity = _read_int("Новая ёмкость (>= 1): ")
            if capacity < 1:
                print("Ёмкость должна быть >= 1, оставляю прежний кэш.")
                capacity = len(cache._store) or 1
                continue
            cache = LRUCache(capacity=capacity)
            print(f"Создан новый пустой кэш ёмкости {capacity}.")
        else:
            print("Неизвестный пункт меню, попробуйте снова.")


def main() -> None:
    menu()


if __name__ == "__main__":
    main()
