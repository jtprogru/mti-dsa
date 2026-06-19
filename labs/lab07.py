"""
Задания:

1. Реализовать бинарную кучу НА МАССИВЕ руками: просеивание вверх (sift_up) и
   вниз (sift_down), операции push / pop / peek. Потомки элемента с индексом i
   лежат на 2i+1 и 2i+2, родитель — на (i-1)//2. Встроенный heapq не используем
   — в этом и смысл лабы: видно, как куча устроена внутри.
2. Поддержать обе разновидности — min-куча (сверху минимум) и max-куча (сверху
   максимум). Реализовано одним классом BinaryHeap с параметром-компаратором.
3. Построить приоритетную очередь поверх кучи: элемент + числовой приоритет.
   Очередь отдаёт элемент с наибольшим (или наименьшим) приоритетом.
4. Решить задачу top-K: найти K самых больших / самых тяжёлых элементов БЕЗ
   полной сортировки массива — через кучу размера K за O(n log K).
5. Меню для демонстрации: построить кучу из массива, push/pop, heapsort,
   приоритетная очередь, top-K.
"""

from labs.common import array_length, generate_array

# --- Задание 1-2: бинарная куча на массиве ----------------------------------

# Куча хранится в обычном массиве (list). Для элемента с индексом i:
#   родитель  -> (i - 1) // 2
#   левый сын -> 2 * i + 1
#   правый    -> 2 * i + 2
# Никаких ссылок и узлов — дерево «закодировано» индексами, поэтому куча очень
# компактна по памяти. Свойство кучи (heap property): родитель не нарушает
# порядок относительно обоих потомков (для min-кучи родитель <= потомков).


class BinaryHeap:
    """Бинарная min/max-куча на массиве, реализованная вручную.

    Разновидность задаётся параметром kind:
      "min" — на вершине минимальный элемент (min-куча);
      "max" — на вершине максимальный элемент (max-куча).

    Внутри всё работает через один компаратор _higher(a, b): «должен ли a
    стоять ВЫШЕ b в куче». Для min-кучи выше тот, кто меньше; для max-кучи —
    кто больше. Это позволяет не дублировать sift_up / sift_down под два случая.

    Сложности:
      push / pop — O(log n) (просеивание по высоте дерева);
      peek       — O(1);
      build (из массива) — O(n) (просеивание снизу вверх).
    """

    def __init__(self, kind: str = "min", data: list | None = None) -> None:
        if kind not in ("min", "max"):
            raise ValueError("kind должен быть 'min' или 'max'.")
        self._kind: str = kind
        self._data: list = []
        if data:
            self._build(data)

    def _higher(self, a, b) -> bool:
        """True, если a должен стоять выше b в куче.

        min-куча: выше меньший элемент (a < b).
        max-куча: выше больший элемент (a > b).
        """
        if self._kind == "min":
            return a < b
        return a > b

    def _sift_up(self, i: int) -> None:
        """Просеивание вверх: поднимаем элемент i, пока он «выше» родителя.

        Используется после push: новый элемент кладём в конец и поднимаем до
        его законного места. Высота дерева log n — отсюда O(log n).
        """
        while i > 0:
            parent = (i - 1) // 2
            if self._higher(self._data[i], self._data[parent]):
                self._data[i], self._data[parent] = self._data[parent], self._data[i]
                i = parent
            else:
                break

    def _sift_down(self, i: int) -> None:
        """Просеивание вниз: опускаем элемент i к «более высокому» из потомков.

        Используется после pop: на вершину кладём последний элемент и опускаем
        его, пока он нарушает свойство кучи. На каждом шаге выбираем потомка,
        который должен стоять выше (минимум для min-кучи, максимум для max).
        """
        n = array_length(self._data)
        while True:
            left = 2 * i + 1
            right = 2 * i + 2
            best = i  # кандидат на «самый высокий» среди i и его потомков
            if left < n and self._higher(self._data[left], self._data[best]):
                best = left
            if right < n and self._higher(self._data[right], self._data[best]):
                best = right
            if best == i:
                break  # свойство кучи восстановлено
            self._data[i], self._data[best] = self._data[best], self._data[i]
            i = best

    def _build(self, data: list) -> None:
        """Построить кучу из готового массива за O(n) (heapify).

        Просеиваем вниз все внутренние узлы, начиная с последнего родителя и
        двигаясь к корню. Это дешевле, чем n раз вызвать push (O(n log n)).
        """
        self._data = list(data)
        n = array_length(self._data)
        i = n // 2 - 1  # индекс последнего узла, у которого есть хотя бы один потомок
        while i >= 0:
            self._sift_down(i)
            i -= 1

    def push(self, value) -> None:
        """Добавить элемент: кладём в конец и просеиваем вверх. O(log n)."""
        self._data.append(value)
        self._sift_up(array_length(self._data) - 1)

    def pop(self):
        """Извлечь вершину (минимум или максимум). O(log n).

        Меняем вершину с последним элементом, отрезаем вершину с конца и
        просеиваем вниз новый корень.
        """
        n = array_length(self._data)
        if n == 0:
            raise IndexError("pop из пустой кучи.")
        top = self._data[0]
        last = self._data.pop()  # снимаем последний элемент
        if array_length(self._data) > 0:
            self._data[0] = last  # ставим его на вершину
            self._sift_down(0)
        return top

    def peek(self):
        """Посмотреть вершину, не извлекая её. O(1)."""
        if array_length(self._data) == 0:
            raise IndexError("peek из пустой кучи.")
        return self._data[0]

    def is_empty(self) -> bool:
        return array_length(self._data) == 0

    def as_list(self) -> list:
        """Копия внутреннего массива (для отладки и тестов структуры)."""
        return list(self._data)

    def __len__(self) -> int:
        return array_length(self._data)


# --- Задание 1-2: heapsort (демонстрация инварианта) ------------------------


def heap_sort(arr: list, reverse: bool = False) -> list:
    """Сортировка кучей: build за O(n), затем n раз pop за O(log n) -> O(n log n).

    Последовательные pop из min-кучи дают возрастающий порядок (из max-кучи —
    убывающий). Это прямое доказательство того, что куча отдаёт элементы в
    отсортированном порядке. Вход не мутируется.
    """
    kind = "max" if reverse else "min"
    heap = BinaryHeap(kind=kind, data=arr)
    result: list = []
    while not heap.is_empty():
        result.append(heap.pop())
    return result


# --- Задание 3: приоритетная очередь поверх кучи ----------------------------


class PriorityQueue:
    """Приоритетная очередь поверх BinaryHeap: хранит пары (приоритет, элемент).

    Параметр order:
      "max" — первым выходит элемент с НАИБОЛЬШИМ приоритетом (по умолчанию;
              это привычная семантика «самое срочное вперёд»);
      "min" — первым выходит элемент с наименьшим приоритетом.

    Чтобы не сравнивать сами элементы (они могут быть несравнимы между собой),
    в кучу кладём кортеж (priority, tie, item), где tie — производный от счётчика
    вставок tie-breaker: при равных приоритетах сравнение уходит на него, очередь
    остаётся FIFO-стабильной, а сам item никогда не участвует в сравнении.

    Тонкость: для FIFO нужно, чтобы при равных приоритетах ВЫШЕ стоял раньше
    вставленный элемент. В min-куче выше меньший кортеж, поэтому tie = +seq
    (меньший seq = раньше). В max-куче выше больший кортеж, поэтому tie = -seq
    (меньший seq даёт больший -seq, то есть тоже выходит первым).
    """

    def __init__(self, order: str = "max") -> None:
        if order not in ("min", "max"):
            raise ValueError("order должен быть 'min' или 'max'.")
        # Куча сравнивает кортежи (priority, tie, item) лексикографически.
        # Для очереди по максимуму приоритета нужна max-куча по первому полю.
        self._order: str = order
        self._heap = BinaryHeap(kind=order)
        self._seq: int = 0

    def push(self, item, priority) -> None:
        """Добавить элемент с приоритетом. O(log n)."""
        # tie-breaker инвертируется для max-кучи, чтобы FIFO сохранялся в обоих режимах
        tie = -self._seq if self._order == "max" else self._seq
        self._heap.push((priority, tie, item))
        self._seq += 1

    def pop(self):
        """Извлечь элемент с экстремальным приоритетом. Возвращает item. O(log n)."""
        if self._heap.is_empty():
            raise IndexError("pop из пустой очереди.")
        _, _, item = self._heap.pop()
        return item

    def peek(self):
        """Посмотреть следующий элемент, не извлекая. O(1)."""
        if self._heap.is_empty():
            raise IndexError("peek из пустой очереди.")
        return self._heap.peek()[2]

    def is_empty(self) -> bool:
        return self._heap.is_empty()

    def __len__(self) -> int:
        return array_length(self._heap.as_list())


# --- Задание 4: top-K без полной сортировки ---------------------------------


def top_k_largest(arr: list, k: int) -> list:
    """K самых больших элементов БЕЗ полной сортировки массива.

    Идея: держим min-кучу размера не больше K. Идём по массиву один раз:
      - пока в куче меньше K элементов — просто кладём;
      - дальше сравниваем элемент с вершиной (текущим минимумом среди лидеров):
        если он больше — выкидываем минимум и кладём новый.
    В итоге в куче остаются ровно K наибольших. Сложность O(n log K) и память
    O(K) — выгодно, когда K << n (например, top-10 самых медленных из миллиона
    запросов): полная сортировка стоила бы O(n log n) и O(n) памяти.

    Возвращает K элементов, отсортированных по убыванию. Если k >= len(arr) —
    возвращает все элементы (тоже по убыванию). При k <= 0 — пустой список.
    """
    if k <= 0:
        return []
    heap = BinaryHeap(kind="min")
    for value in arr:
        if array_length(heap.as_list()) < k:
            heap.push(value)
        elif value > heap.peek():
            # новый элемент больше слабейшего из лидеров — заменяем
            heap.pop()
            heap.push(value)
    # в куче — K наибольших (или все, если их меньше K); отдаём по убыванию
    collected: list = []
    while not heap.is_empty():
        collected.append(heap.pop())
    collected.reverse()  # pop из min-кучи даёт возрастание -> разворачиваем
    return collected


def top_k_smallest(arr: list, k: int) -> list:
    """K самых маленьких элементов без полной сортировки. Зеркало top_k_largest.

    Держим max-куча размера K: на вершине — самый большой из текущих кандидатов
    на «маленькие». Если очередной элемент меньше вершины, он вытесняет её.
    Возвращает K элементов по возрастанию. O(n log K), память O(K).
    """
    if k <= 0:
        return []
    heap = BinaryHeap(kind="max")
    for value in arr:
        if array_length(heap.as_list()) < k:
            heap.push(value)
        elif value < heap.peek():
            heap.pop()
            heap.push(value)
    collected: list = []
    while not heap.is_empty():
        collected.append(heap.pop())
    collected.reverse()  # pop из max-кучи даёт убывание -> разворачиваем
    return collected


# --- Задание 5: меню и демонстрация -----------------------------------------


def _read_int(prompt: str) -> int:
    """Читает целое число, повторяя запрос при неверном вводе."""
    while True:
        raw = input(prompt).strip()
        try:
            return int(raw)
        except ValueError:
            print("Это не целое число, попробуйте снова.")


def demo_heap(arr: list) -> None:
    """Строит min- и max-кучу из массива, показывает вершины и heapsort."""
    print("Исходный массив:", arr)
    min_heap = BinaryHeap(kind="min", data=arr)
    max_heap = BinaryHeap(kind="max", data=arr)
    print("min-куча (массив):", min_heap.as_list(), "-> вершина (минимум):", min_heap.peek())
    print("max-куча (массив):", max_heap.as_list(), "-> вершина (максимум):", max_heap.peek())
    print("heapsort по возрастанию:", heap_sort(arr))
    print("heapsort по убыванию:  ", heap_sort(arr, reverse=True))


def demo_priority_queue() -> None:
    """Демонстрирует приоритетную очередь как планировщик задач."""
    pq = PriorityQueue(order="max")
    tasks = [
        ("backup", 1),
        ("deploy-hotfix", 10),
        ("rotate-logs", 3),
        ("scale-up", 8),
    ]
    print("Кладём задачи (имя, приоритет):", tasks)
    for name, prio in tasks:
        pq.push(name, prio)
    print("Порядок выполнения (по убыванию приоритета):")
    while not pq.is_empty():
        print("  ->", pq.pop())


def demo_top_k(arr: list, k: int) -> None:
    """Показывает top-K без полной сортировки."""
    print("Массив:", arr)
    print(f"top-{k} наибольших:", top_k_largest(arr, k))
    print(f"top-{k} наименьших:", top_k_smallest(arr, k))


def menu() -> None:
    arr = generate_array(10)
    print("Сгенерирован массив из 10 случайных чисел:")
    print(arr)

    while True:
        print("\n" + "=" * 40)
        print("Меню (куча и top-K):")
        print("  1. Построить кучи и heapsort")
        print("  2. Приоритетная очередь (планировщик задач)")
        print("  3. top-K наибольших / наименьших")
        print("  4. Push элемент в min-кучу и показать вершину")
        print("  5. Сгенерировать новый массив")
        print("  0. Выход")

        choice = input("Выберите пункт: ").strip()

        if choice == "0":
            print("Выход.")
            return
        if choice == "1":
            print()
            demo_heap(arr)
        elif choice == "2":
            print()
            demo_priority_queue()
        elif choice == "3":
            k = _read_int("Сколько элементов в top-K: ")
            print()
            demo_top_k(arr, k)
        elif choice == "4":
            value = _read_int("Значение для вставки: ")
            heap = BinaryHeap(kind="min", data=arr)
            heap.push(value)
            print("Куча после push:", heap.as_list(), "-> вершина:", heap.peek())
        elif choice == "5":
            arr = generate_array(10)
            print("Сгенерирован новый массив:")
            print(arr)
        else:
            print("Неизвестный пункт меню, попробуйте снова.")


def main() -> None:
    menu()


if __name__ == "__main__":
    main()
