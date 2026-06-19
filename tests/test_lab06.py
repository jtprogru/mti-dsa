import pytest

from labs.lab06 import (
    CycleError,
    DirectedGraph,
    bfs,
    build_cyclic_graph,
    build_services_graph,
    demo_cycle,
    demo_services,
    dfs,
    has_cycle,
    main,
    menu,
    startup_order,
    topological_sort,
)


def feed_input(monkeypatch, values):
    """Подменяет input() последовательностью значений."""
    inputs = iter(values)
    monkeypatch.setattr("builtins.input", lambda _="": next(inputs))


# ─── helpers ─────────────────────────────────────────────────────────────────


def make_graph(edges) -> DirectedGraph:
    """Граф из списка рёбер [(src, dst), ...] в заданном порядке."""
    graph = DirectedGraph()
    for src, dst in edges:
        graph.add_edge(src, dst)
    return graph


def is_valid_topo_order(graph: DirectedGraph, order: list) -> bool:
    """Проверяет, что для каждого ребра src -> dst src идёт раньше dst."""
    position = {vertex: i for i, vertex in enumerate(order)}
    if set(position) != set(graph.vertices()):
        return False  # не все вершины попали в порядок
    for src in graph.vertices():
        for dst in graph.neighbors(src):
            if position[src] >= position[dst]:
                return False
    return True


# Известный граф для детерминированных обходов:
#   1 -> 2, 1 -> 3
#   2 -> 4
#   3 -> 4
# Соседи перебираются в порядке добавления рёбер.
KNOWN_EDGES = [(1, 2), (1, 3), (2, 4), (3, 4)]


# ─── DirectedGraph ───────────────────────────────────────────────────────────


class TestDirectedGraph:
    def test_new_graph_is_empty(self):
        assert len(DirectedGraph()) == 0

    def test_add_vertex(self):
        graph = DirectedGraph()
        graph.add_vertex("a")
        assert graph.has_vertex("a")
        assert graph.vertices() == ["a"]

    def test_add_vertex_is_idempotent(self):
        graph = DirectedGraph()
        graph.add_vertex("a")
        graph.add_vertex("a")
        assert graph.vertices() == ["a"]

    def test_add_edge_creates_endpoints(self):
        graph = DirectedGraph()
        graph.add_edge("a", "b")
        assert graph.has_vertex("a")
        assert graph.has_vertex("b")

    def test_add_edge_preserves_order(self):
        graph = make_graph([("a", "b"), ("a", "c")])
        assert graph.neighbors("a") == ["b", "c"]

    def test_duplicate_edge_ignored(self):
        graph = make_graph([("a", "b"), ("a", "b")])
        assert graph.neighbors("a") == ["b"]

    def test_neighbors_returns_copy(self):
        graph = make_graph([("a", "b")])
        graph.neighbors("a").append("hacked")
        assert graph.neighbors("a") == ["b"]

    def test_neighbors_missing_vertex_raises(self):
        with pytest.raises(KeyError):
            DirectedGraph().neighbors("nope")

    def test_vertices_insertion_order(self):
        graph = make_graph([("x", "y"), ("z", "x")])
        assert graph.vertices() == ["x", "y", "z"]

    def test_len_counts_vertices(self):
        graph = make_graph(KNOWN_EDGES)
        assert len(graph) == 4

    def test_print_graph_output(self, capsys):
        graph = make_graph([("a", "b")])
        graph.print_graph()
        out = capsys.readouterr().out
        assert "a -> b" in out
        assert "нет рёбер" in out  # b изолирована


# ─── BFS ─────────────────────────────────────────────────────────────────────


class TestBFS:
    def test_known_graph_order(self):
        graph = make_graph(KNOWN_EDGES)
        assert bfs(graph, 1) == [1, 2, 3, 4]

    def test_single_vertex(self):
        graph = DirectedGraph()
        graph.add_vertex("solo")
        assert bfs(graph, "solo") == ["solo"]

    def test_visits_each_vertex_once(self):
        # ромб: 1->2, 1->3, 2->4, 3->4 — вершина 4 не должна повториться
        graph = make_graph(KNOWN_EDGES)
        order = bfs(graph, 1)
        assert len(order) == len(set(order))

    def test_does_not_follow_unreachable(self):
        graph = make_graph([(1, 2), (3, 4)])  # две компоненты
        assert bfs(graph, 1) == [1, 2]

    def test_cycle_terminates(self):
        graph = make_graph([(1, 2), (2, 3), (3, 1)])
        assert bfs(graph, 1) == [1, 2, 3]

    def test_missing_start_raises(self):
        with pytest.raises(KeyError):
            bfs(make_graph(KNOWN_EDGES), 99)


# ─── DFS ─────────────────────────────────────────────────────────────────────


class TestDFS:
    def test_known_graph_order(self):
        # 1 -> [2,3]; уходим вглубь: 1,2,4 (тупик), назад к 3 (4 уже посещена)
        graph = make_graph(KNOWN_EDGES)
        assert dfs(graph, 1) == [1, 2, 4, 3]

    def test_single_vertex(self):
        graph = DirectedGraph()
        graph.add_vertex("solo")
        assert dfs(graph, "solo") == ["solo"]

    def test_visits_each_vertex_once(self):
        graph = make_graph(KNOWN_EDGES)
        order = dfs(graph, 1)
        assert len(order) == len(set(order))

    def test_does_not_follow_unreachable(self):
        graph = make_graph([(1, 2), (3, 4)])
        assert dfs(graph, 1) == [1, 2]

    def test_cycle_terminates(self):
        graph = make_graph([(1, 2), (2, 3), (3, 1)])
        assert dfs(graph, 1) == [1, 2, 3]

    def test_vertex_pushed_twice_is_visited_once(self):
        # Ромб: вершину 3 в стек кладут оба родителя (1 и 2) до её посещения.
        # Когда дубликат всплывает из стека повторно, DFS должен его пропустить.
        graph = make_graph([(1, 2), (1, 3), (2, 3)])
        order = dfs(graph, 1)
        assert order == [1, 2, 3]
        assert len(order) == len(set(order))

    def test_missing_start_raises(self):
        with pytest.raises(KeyError):
            dfs(make_graph(KNOWN_EDGES), 99)

    def test_bfs_and_dfs_cover_same_reachable_set(self):
        graph = make_graph(KNOWN_EDGES)
        assert set(bfs(graph, 1)) == set(dfs(graph, 1))


# ─── обнаружение цикла ───────────────────────────────────────────────────────


class TestHasCycle:
    @pytest.mark.parametrize(
        "edges, expected",
        [
            ([(1, 2), (2, 3), (3, 4)], False),  # простая цепочка
            (KNOWN_EDGES, False),  # ромб (DAG)
            ([(1, 2), (2, 3), (3, 1)], True),  # цикл из трёх
            ([(1, 1)], True),  # петля
            ([(1, 2), (3, 4)], False),  # две ацикличные компоненты
            ([(1, 2), (2, 3), (4, 5), (5, 4)], True),  # цикл в одной из компонент
        ],
    )
    def test_cycle_detection(self, edges, expected):
        assert has_cycle(make_graph(edges)) is expected

    def test_empty_graph_has_no_cycle(self):
        assert has_cycle(DirectedGraph()) is False

    def test_services_graph_is_acyclic(self):
        assert has_cycle(build_services_graph()) is False

    def test_cyclic_graph_helper_has_cycle(self):
        assert has_cycle(build_cyclic_graph()) is True


# ─── топологическая сортировка ───────────────────────────────────────────────


class TestTopologicalSort:
    @pytest.mark.parametrize(
        "edges",
        [
            [(1, 2), (2, 3), (3, 4)],
            KNOWN_EDGES,
            [("web", "api"), ("api", "db"), ("api", "cache")],
            [(1, 2), (1, 3), (1, 4)],
        ],
    )
    def test_produces_valid_order(self, edges):
        graph = make_graph(edges)
        order = topological_sort(graph)
        assert is_valid_topo_order(graph, order)

    def test_chain_exact_order(self):
        graph = make_graph([(1, 2), (2, 3), (3, 4)])
        assert topological_sort(graph) == [1, 2, 3, 4]

    def test_includes_all_vertices(self):
        graph = make_graph(KNOWN_EDGES)
        assert set(topological_sort(graph)) == {1, 2, 3, 4}

    def test_isolated_vertices_included(self):
        graph = DirectedGraph()
        graph.add_vertex("lonely")
        graph.add_edge("a", "b")
        assert set(topological_sort(graph)) == {"lonely", "a", "b"}

    @pytest.mark.parametrize(
        "edges",
        [
            [(1, 2), (2, 3), (3, 1)],  # цикл из трёх
            [(1, 1)],  # петля
            [(1, 2), (2, 3), (4, 5), (5, 4)],  # цикл в части графа
        ],
    )
    def test_cycle_raises(self, edges):
        with pytest.raises(CycleError):
            topological_sort(make_graph(edges))

    def test_services_graph_valid(self):
        graph = build_services_graph()
        assert is_valid_topo_order(graph, topological_sort(graph))


# ─── порядок запуска сервисов ────────────────────────────────────────────────


class TestStartupOrder:
    def test_dependency_starts_before_dependent(self):
        # app -> db значит «app зависит от db»: db должен стартовать раньше app
        graph = make_graph([("app", "db")])
        order = startup_order(graph)
        assert order.index("db") < order.index("app")

    def test_services_graph_dependencies_first(self):
        graph = build_services_graph()
        order = startup_order(graph)
        # базовые сервисы — раньше тех, кто от них зависит
        assert order.index("db") < order.index("api")
        assert order.index("cache") < order.index("api")
        assert order.index("api") < order.index("web")
        assert order.index("db") < order.index("worker")
        assert order.index("queue") < order.index("worker")

    def test_includes_all_vertices(self):
        graph = build_services_graph()
        assert set(startup_order(graph)) == set(graph.vertices())

    def test_cycle_raises(self):
        with pytest.raises(CycleError):
            startup_order(build_cyclic_graph())


class TestDemos:
    def test_demo_services(self, capsys):
        demo_services()
        out = capsys.readouterr().out
        assert "BFS от 'web'" in out
        assert "Топологический порядок" in out

    def test_demo_cycle(self, capsys):
        demo_cycle()
        out = capsys.readouterr().out
        assert "Есть цикл? да" in out
        assert "topological_sort ->" in out


class TestMenu:
    def test_all_options_then_exit(self, monkeypatch, capsys):
        feed_input(
            monkeypatch,
            [
                "1",  # показать граф
                "2",
                "newnode",  # добавить вершину
                "3",
                "newnode",
                "db",  # добавить ребро
                "4",
                "web",  # BFS от существующей
                "4",
                "missing",  # BFS от несуществующей
                "5",
                "web",  # DFS от существующей
                "5",
                "missing",  # DFS от несуществующей
                "6",  # проверить на цикл
                "7",  # топосортировка
                "8",  # порядок запуска
                "9",  # демо сервисов
                "10",  # демо цикла
                "z",  # неизвестный пункт
                "0",  # выход
            ],
        )
        menu()
        out = capsys.readouterr().out
        assert "Добавлена вершина: newnode" in out
        assert "Добавлено ребро: newnode -> db" in out
        assert "Вершины 'missing' нет в графе." in out
        assert "Неизвестный пункт меню" in out
        assert "Выход." in out

    def test_cycle_then_topo_and_startup_report_error(self, monkeypatch, capsys):
        # Через меню замыкаем цикл (cyc1 -> cyc2 -> cyc1), затем просим
        # топосортировку (7) и порядок запуска (8): оба ловят CycleError.
        feed_input(
            monkeypatch,
            [
                "3",
                "cyc1",
                "cyc2",  # ребро cyc1 -> cyc2
                "3",
                "cyc2",
                "cyc1",  # ребро cyc2 -> cyc1 (замыкаем цикл)
                "7",  # топосортировка -> CycleError
                "8",  # порядок запуска -> CycleError
                "0",  # выход
            ],
        )
        menu()
        out = capsys.readouterr().out
        assert out.count("цикл") >= 2  # сообщение об ошибке напечатано в пунктах 7 и 8
        assert "Выход." in out

    def test_exit_immediately(self, monkeypatch, capsys):
        feed_input(monkeypatch, ["0"])
        menu()
        assert "Выход." in capsys.readouterr().out

    def test_main_delegates_to_menu(self, monkeypatch, capsys):
        feed_input(monkeypatch, ["0"])
        main()
        assert "Выход." in capsys.readouterr().out
