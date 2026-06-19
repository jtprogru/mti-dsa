"""
Задания:

1. Реализовать ориентированный граф через список смежности (adjacency list):
   хранить вершины и исходящие из каждой рёбра. Поддержать добавление вершины,
   добавление ребра (с автоматическим созданием концевых вершин) и получение
   соседей вершины.
2. Реализовать обход в ширину (BFS) — вернуть порядок посещения вершин по
   «уровням» от стартовой (на очереди).
3. Реализовать обход в глубину (DFS) — вернуть порядок посещения вершин,
   уходя вглубь по первому непосещённому соседу (на стеке / рекурсии).
4. Реализовать обнаружение цикла в ориентированном графе (через раскраску
   вершин: белая / серая / чёрная).
5. Реализовать топологическую сортировку (порядок с учётом зависимостей) —
   алгоритм Кана через степени входа (in-degree). Для графа с циклом
   топосортировка невозможна — корректно сигнализировать исключением.
6. В меню продемонстрировать всё на примере графа зависимостей сервисов
   (порядок запуска): обходы, проверка на цикл и топологический порядок старта.
"""

from labs.common import array_length

# --- Задание 1: ориентированный граф на списке смежности --------------------


class DirectedGraph:
    """Ориентированный граф, хранящийся списком смежности (adjacency list).

    Для каждой вершины храним список её исходящих соседей: ребро A -> B
    означает «A зависит от того, что B уже на месте» либо «из A можно попасть
    в B» — смысл задаёт прикладная задача. В терминах зависимостей сервисов
    ребро `app -> db` читается как «app зависит от db».

    Хранилище — обычный dict `{вершина: [соседи...]}`. Сам dict здесь не
    предмет лабораторной (в lab05 хеш-таблица писалась руками); здесь предмет —
    алгоритмы на графе, поэтому dict используется как готовый контейнер.

    Особенности:
      - порядок вставки вершин и рёбер сохраняется (важно для детерминированных
        обходов и стабильного топологического порядка);
      - параллельные (дублирующие) рёбра не добавляются повторно;
      - петли (A -> A) допускаются и являются простейшим циклом.
    """

    def __init__(self) -> None:
        # {вершина: список исходящих соседей}; порядок вставки сохраняется
        self._adjacency: dict = {}

    def add_vertex(self, vertex) -> None:
        """Добавить изолированную вершину (без рёбер). Идемпотентно."""
        if vertex not in self._adjacency:
            self._adjacency[vertex] = []

    def add_edge(self, src, dst) -> None:
        """Добавить ребро src -> dst, создав отсутствующие вершины.

        Дублирующее ребро игнорируется, чтобы список соседей не разрастался
        одинаковыми записями (на корректность обходов это не влияет, но
        искажало бы степени и засоряло вывод).
        """
        self.add_vertex(src)
        self.add_vertex(dst)
        neighbors = self._adjacency[src]
        for existing in neighbors:
            if existing == dst:
                return  # параллельное ребро — не дублируем
        neighbors.append(dst)

    def neighbors(self, vertex) -> list:
        """Список исходящих соседей вершины (копия, чтобы её нельзя было портить)."""
        if vertex not in self._adjacency:
            raise KeyError(f"Вершины {vertex!r} нет в графе.")
        return list(self._adjacency[vertex])

    def vertices(self) -> list:
        """Все вершины графа в порядке добавления."""
        result: list = []
        for vertex in self._adjacency:
            result.append(vertex)
        return result

    def has_vertex(self, vertex) -> bool:
        """Есть ли вершина в графе."""
        return vertex in self._adjacency

    def __len__(self) -> int:
        """Число вершин."""
        return array_length(self.vertices())

    def print_graph(self) -> None:
        """Печатает список смежности: `вершина -> сосед1, сосед2, ...`."""
        print("DirectedGraph (список смежности):")
        for vertex in self._adjacency:
            neighbors = self._adjacency[vertex]
            if array_length(neighbors) == 0:
                print(f"  {vertex} -> (нет рёбер)")
            else:
                print(f"  {vertex} -> " + ", ".join(str(n) for n in neighbors))


# --- Задание 2: обход в ширину (BFS) ----------------------------------------


def bfs(graph: DirectedGraph, start) -> list:
    """Обход в ширину от вершины start. Возвращает порядок посещения.

    BFS идёт «волнами»: сначала стартовая вершина, потом все её соседи, потом
    соседи соседей и так далее. Реализован на очереди (FIFO): берём вершину из
    головы, помечаем посещённой, её ещё не посещённых соседей кладём в хвост.

    Соседи перебираются в порядке добавления рёбер — обход детерминирован.
    """
    if not graph.has_vertex(start):
        raise KeyError(f"Вершины {start!r} нет в графе.")

    order: list = []
    visited: set = set()
    queue: list = [start]  # очередь вершин; голова — индекс head
    visited.add(start)
    head = 0  # «указатель головы» вместо pop(0) — чтобы не сдвигать список

    while head < array_length(queue):
        current = queue[head]
        head += 1
        order.append(current)
        for neighbor in graph.neighbors(current):
            if neighbor not in visited:
                visited.add(neighbor)  # помечаем при постановке в очередь
                queue.append(neighbor)
    return order


# --- Задание 3: обход в глубину (DFS) ---------------------------------------


def dfs(graph: DirectedGraph, start) -> list:
    """Обход в глубину от вершины start. Возвращает порядок посещения.

    DFS уходит как можно глубже по первому непосещённому соседу, и только
    упёршись в тупик — откатывается назад. Реализован на явном стеке (LIFO),
    чтобы не зависеть от лимита рекурсии Python на больших графах.

    Чтобы порядок совпадал с естественной рекурсией (соседи берутся слева
    направо), кладём соседей в стек в обратном порядке: тогда первый сосед
    окажется на вершине стека и будет обработан первым.
    """
    if not graph.has_vertex(start):
        raise KeyError(f"Вершины {start!r} нет в графе.")

    order: list = []
    visited: set = set()
    stack: list = [start]

    while array_length(stack) > 0:
        current = stack.pop()  # снимаем с вершины стека
        if current in visited:
            continue  # вершина уже обработана через другой путь
        visited.add(current)
        order.append(current)
        neighbors = graph.neighbors(current)
        # кладём соседей в обратном порядке — первый сосед обработается первым
        i = array_length(neighbors) - 1
        while i >= 0:
            neighbor = neighbors[i]
            if neighbor not in visited:
                stack.append(neighbor)
            i -= 1
    return order


# --- Задание 4: обнаружение цикла -------------------------------------------

# Цвета вершин при поиске цикла (классическая «трёхцветная» раскраска DFS):
#   _WHITE — вершина ещё не посещалась;
#   _GRAY  — вершина в текущем стеке рекурсии (обрабатывается прямо сейчас);
#   _BLACK — вершина и всё её поддерево полностью обработаны.
# Ребро в СЕРУЮ вершину — это «back edge», то есть цикл.
_WHITE = 0
_GRAY = 1
_BLACK = 2


def has_cycle(graph: DirectedGraph) -> bool:
    """Есть ли в ориентированном графе цикл.

    Используем обход в глубину с раскраской вершин. Если по ходу DFS мы
    наткнулись на ребро в СЕРУЮ вершину (ту, что сейчас в стеке рекурсии), —
    значит, нашли обратное ребро (back edge), а оно замыкает цикл.

    Запускаем DFS из каждой ещё белой вершины: граф может быть несвязным.
    Обход на явном стеке (а не рекурсии), чтобы выдержать большие графы.
    """
    color: dict = {}
    for vertex in graph.vertices():
        color[vertex] = _WHITE

    for root in graph.vertices():
        if color[root] != _WHITE:
            continue
        # на стеке храним пары (вершина, индекс следующего соседа для разбора)
        stack: list = [[root, 0]]
        color[root] = _GRAY
        while array_length(stack) > 0:
            frame = stack[array_length(stack) - 1]  # вершина стека
            vertex = frame[0]
            idx = frame[1]
            neighbors = graph.neighbors(vertex)
            if idx < array_length(neighbors):
                frame[1] = idx + 1  # сдвигаем указатель соседа для этой вершины
                neighbor = neighbors[idx]
                if color[neighbor] == _GRAY:
                    return True  # ребро в серую вершину — цикл
                if color[neighbor] == _WHITE:
                    color[neighbor] = _GRAY
                    stack.append([neighbor, 0])
            else:
                color[vertex] = _BLACK  # все соседи разобраны — вершина закрыта
                stack.pop()
    return False


# --- Задание 5: топологическая сортировка (алгоритм Кана) -------------------


class CycleError(Exception):
    """Топологическая сортировка невозможна: в графе есть цикл."""


def topological_sort(graph: DirectedGraph) -> list:
    """Топологический порядок вершин (алгоритм Кана через степени входа).

    Возвращает такой порядок, в котором для каждого ребра src -> dst вершина
    src идёт РАНЬШЕ dst. В терминах зависимостей: если `app -> db` значит «app
    зависит от db», то в обратном порядке (db перед app) получаем порядок
    запуска — см. `startup_order`.

    Алгоритм Кана:
      1. Считаем in-degree (число входящих рёбер) для каждой вершины.
      2. Кладём в очередь все вершины с in-degree == 0 (ни от кого не зависят).
      3. Снимаем вершину из очереди, добавляем в результат, у всех её соседей
         уменьшаем in-degree; если он стал 0 — кладём соседа в очередь.
      4. Если в результат попали не все вершины — остался цикл (его вершины
         так и не получили нулевую степень) -> CycleError.

    Порядок добавления вершин/рёбер сохраняется, поэтому при нескольких
    допустимых порядках результат детерминирован.
    """
    in_degree: dict = {}
    for vertex in graph.vertices():
        in_degree[vertex] = 0
    for vertex in graph.vertices():
        for neighbor in graph.neighbors(vertex):
            in_degree[neighbor] = in_degree[neighbor] + 1

    # очередь вершин с нулевой входной степенью (в порядке добавления вершин)
    queue: list = []
    for vertex in graph.vertices():
        if in_degree[vertex] == 0:
            queue.append(vertex)

    order: list = []
    head = 0
    while head < array_length(queue):
        current = queue[head]
        head += 1
        order.append(current)
        for neighbor in graph.neighbors(current):
            in_degree[neighbor] = in_degree[neighbor] - 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if array_length(order) != array_length(graph.vertices()):
        # не все вершины «развязались» — значит, есть цикл
        raise CycleError(
            "Топологическая сортировка невозможна: в графе есть цикл "
            "(циклическая зависимость)."
        )
    return order


def startup_order(graph: DirectedGraph) -> list:
    """Порядок запуска сервисов, если ребро A -> B значит «A зависит от B».

    Топологическая сортировка даёт «зависимый раньше зависимости», а запускать
    надо наоборот — сперва то, от чего зависят. Поэтому разворачиваем результат
    `topological_sort`. При цикле прокидываем CycleError наверх.
    """
    order = topological_sort(graph)
    reversed_order: list = []
    i = array_length(order) - 1
    while i >= 0:
        reversed_order.append(order[i])
        i -= 1
    return reversed_order


# --- Задание 6: меню и демонстрация на графе зависимостей сервисов -----------


def build_services_graph() -> DirectedGraph:
    """Пример графа зависимостей сервисов (ребро A -> B: «A зависит от B»).

    Топология типичного веб-стека:
        web      -> api
        api      -> db, cache
        worker   -> db, queue
        db, cache, queue — базовые сервисы без зависимостей.

    Граф ацикличен (DAG), поэтому для него существует корректный порядок старта.
    """
    graph = DirectedGraph()
    graph.add_edge("web", "api")
    graph.add_edge("api", "db")
    graph.add_edge("api", "cache")
    graph.add_edge("worker", "db")
    graph.add_edge("worker", "queue")
    # базовые сервисы как изолированные «листья» уже созданы add_edge,
    # но добавим явно для наглядности (идемпотентно)
    graph.add_vertex("db")
    graph.add_vertex("cache")
    graph.add_vertex("queue")
    return graph


def build_cyclic_graph() -> DirectedGraph:
    """Пример графа с циклической зависимостью: a -> b -> c -> a.

    Такой граф нельзя топологически отсортировать — для него `topological_sort`
    бросает CycleError, а `has_cycle` возвращает True.
    """
    graph = DirectedGraph()
    graph.add_edge("a", "b")
    graph.add_edge("b", "c")
    graph.add_edge("c", "a")  # замыкаем цикл
    return graph


def demo_services() -> None:
    """Демонстрация на графе зависимостей сервисов: обходы и порядок старта."""
    graph = build_services_graph()
    print()
    graph.print_graph()
    print("\nBFS от 'web':", bfs(graph, "web"))
    print("DFS от 'web':", dfs(graph, "web"))
    print("Есть цикл?", "да" if has_cycle(graph) else "нет")
    print("Топологический порядок (зависимый раньше зависимости):")
    print("  ", topological_sort(graph))
    print("Порядок ЗАПУСКА сервисов (сначала зависимости):")
    print("  ", startup_order(graph))


def demo_cycle() -> None:
    """Демонстрация графа с циклом: обнаружение и реакция топосортировки."""
    graph = build_cyclic_graph()
    print()
    graph.print_graph()
    print("\nЕсть цикл?", "да" if has_cycle(graph) else "нет")
    try:
        topological_sort(graph)
    except CycleError as exc:
        print("topological_sort ->", exc)


def menu() -> None:
    graph = build_services_graph()

    while True:
        print("\n" + "=" * 40)
        print("Меню (графы):")
        print("  1. Показать граф (список смежности)")
        print("  2. Добавить вершину")
        print("  3. Добавить ребро (зависимость A -> B)")
        print("  4. BFS от вершины")
        print("  5. DFS от вершины")
        print("  6. Проверить граф на цикл")
        print("  7. Топологическая сортировка")
        print("  8. Порядок запуска сервисов (startup order)")
        print("  9. Демонстрация на графе сервисов")
        print("  10. Демонстрация графа с циклом")
        print("  0. Выход")

        choice = input("Выберите пункт: ").strip()

        if choice == "0":
            print("Выход.")
            return
        if choice == "1":
            graph.print_graph()
        elif choice == "2":
            vertex = input("Имя вершины: ").strip()
            graph.add_vertex(vertex)
            print(f"Добавлена вершина: {vertex}")
        elif choice == "3":
            src = input("Откуда (зависит): ").strip()
            dst = input("Куда (зависимость): ").strip()
            graph.add_edge(src, dst)
            print(f"Добавлено ребро: {src} -> {dst}")
        elif choice == "4":
            start = input("Стартовая вершина: ").strip()
            if graph.has_vertex(start):
                print("BFS:", bfs(graph, start))
            else:
                print(f"Вершины {start!r} нет в графе.")
        elif choice == "5":
            start = input("Стартовая вершина: ").strip()
            if graph.has_vertex(start):
                print("DFS:", dfs(graph, start))
            else:
                print(f"Вершины {start!r} нет в графе.")
        elif choice == "6":
            print("Цикл:", "найден" if has_cycle(graph) else "не найден")
        elif choice == "7":
            try:
                print("Топологический порядок:", topological_sort(graph))
            except CycleError as exc:
                print(exc)
        elif choice == "8":
            try:
                print("Порядок запуска:", startup_order(graph))
            except CycleError as exc:
                print(exc)
        elif choice == "9":
            demo_services()
        elif choice == "10":
            demo_cycle()
        else:
            print("Неизвестный пункт меню, попробуйте снова.")


def main() -> None:
    menu()


if __name__ == "__main__":
    main()
