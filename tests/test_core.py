"""Тести коректності алгоритму Прима.

Покривають те, про що йдеться в README:

* збіг ваги МОД з еталонною реалізацією ``networkx.minimum_spanning_tree``
  (на обох навчальних графах і на серії випадкових зв'язних графів);
* властивості остовного дерева: ``n − 1`` ребер, зв'язність, усі вершини;
* інструментована версія (:func:`prim_mst_steps`) повторює базову дія в дію,
  а її журнал подій внутрішньо узгоджений (черга відсортована, дерево росте
  по одній вершині, застарілі ребра нічого не змінюють);
* поведінку на незв'язному графі: базова версія аварійно зупиняється,
  eager-версія повертає лише компоненту старту, ліс (:func:`prim_msf`) чесний.

Запуск::

    pytest                       # якщо встановлено pytest
    python tests/test_core.py    # без pytest (вбудований раннер)
"""

from __future__ import annotations

import os
import random
import sys

import networkx as nx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prim_mst import (  # noqa: E402
    build_graph,
    mst_weight,
    prim_msf,
    prim_mst,
    prim_mst_eager,
    prim_mst_steps,
)

# --- Граф A–F: той самий, що в проєкті про Флойда–Воршала (неорієнтований) --
ABCDEF_EDGES = [("A", "B", 3), ("B", "C", 1), ("C", "D", 7),
                ("C", "F", 2), ("D", "E", 2), ("E", "F", 3)]
# --- Граф A–G із демонстрації базової реалізації ----------------------------
ABCDEFG_EDGES = [("A", "B", 7), ("A", "D", 5), ("B", "C", 8), ("B", "D", 9),
                 ("B", "E", 7), ("C", "E", 5), ("D", "E", 15), ("D", "F", 6),
                 ("E", "F", 8), ("E", "G", 9), ("F", "G", 11)]
# --- Незв'язний граф: два «острови» -----------------------------------------
ISLANDS_EDGES = [("M", "N", 2), ("N", "O", 4), ("M", "O", 7), ("P", "Q", 3)]


def _undirected_edge_set(tree):
    """Ребра дерева як множина (порядок кінців не важливий)."""
    return {frozenset((u, v)) for u, v in tree.edges()}


def _random_connected_graph(seed: int, n: int = 12, extra: int = 14) -> "nx.Graph":
    """Випадковий зв'язний граф: остовний ланцюг + випадкові додаткові ребра."""
    rng = random.Random(seed)
    g = nx.Graph()
    nodes = [f"v{i}" for i in range(n)]
    order = nodes[:]
    rng.shuffle(order)
    for a, b in zip(order, order[1:]):           # ланцюг гарантує зв'язність
        g.add_edge(a, b, weight=rng.randint(1, 20))
    added = 0
    while added < extra:
        u, v = rng.sample(nodes, 2)
        if not g.has_edge(u, v):
            g.add_edge(u, v, weight=rng.randint(1, 20))
            added += 1
    return g


def test_abcdef_weight_matches_networkx():
    g = build_graph(ABCDEF_EDGES)
    mst = prim_mst(g)
    assert mst_weight(mst) == 11
    assert mst_weight(mst) == nx.minimum_spanning_tree(g).size(weight="weight")


def test_abcdef_known_tree():
    """На графі A–F МОД єдине: відкинутим має бути саме ребро C–D (7)."""
    g = build_graph(ABCDEF_EDGES)
    mst = prim_mst(g)
    assert _undirected_edge_set(mst) == {
        frozenset(p) for p in [("A", "B"), ("B", "C"), ("C", "F"), ("E", "F"), ("D", "E")]
    }
    assert not mst.has_edge("C", "D")


def test_abcdefg_weight_matches_networkx():
    g = build_graph(ABCDEFG_EDGES)
    mst = prim_mst(g)
    assert mst_weight(mst) == 39
    assert mst_weight(mst) == nx.minimum_spanning_tree(g).size(weight="weight")


def test_mst_is_spanning_tree():
    """У МОД рівно n − 1 ребро, воно зв'язне й охоплює всі вершини."""
    for edges in (ABCDEF_EDGES, ABCDEFG_EDGES):
        g = build_graph(edges)
        mst = prim_mst(g)
        assert mst.number_of_edges() == g.number_of_nodes() - 1
        assert set(mst.nodes()) == set(g.nodes())
        assert nx.is_connected(mst)
        assert nx.is_tree(mst)


def test_steps_match_base_implementation():
    """Інструментована версія будує точно те саме дерево, що й базова."""
    for edges in (ABCDEF_EDGES, ABCDEFG_EDGES):
        g = build_graph(edges)
        base = prim_mst(g)
        steps_tree, _ = prim_mst_steps(g)   # старт за замовчуванням — як у базової
        assert _undirected_edge_set(base) == _undirected_edge_set(steps_tree)


def test_events_journal_consistency():
    """Журнал подій внутрішньо узгоджений (це на ньому стоять усі візуалізації)."""
    g = build_graph(ABCDEFG_EDGES)
    mst, events = prim_mst_steps(g, start="A")

    assert events[0]["kind"] == "init"
    assert events[0]["visited"] == {"A"}
    adds = [e for e in events if e["kind"] == "add"]
    skips = [e for e in events if e["kind"] == "skip"]
    assert len(adds) == g.number_of_nodes() - 1   # рівно n − 1 прийнятих ребер
    assert len(skips) == 3                        # на A–G — рівно три застарілі

    for prev, event in zip(events, events[1:]):
        # черга у знімку відсортована за пріоритетом — верхнє ребро і знімається
        assert event["queue"] == sorted(event["queue"])
        assert event["edge"] == prev["queue"][0]
        if event["kind"] == "add":
            # дерево виросло рівно на одну вершину — кінець прийнятого ребра
            assert event["visited"] - prev["visited"] == {event["edge"][2]}
            assert len(event["mst_edges"]) == len(prev["mst_edges"]) + 1
            assert event["total"] == prev["total"] + event["edge"][0]
        else:
            # застаріле ребро: дерево й вага без змін, нічого не надіслано в чергу
            assert event["visited"] == prev["visited"]
            assert event["mst_edges"] == prev["mst_edges"]
            assert event["pushed"] == []

    # підсумок журналу збігається з повернутим деревом
    assert {frozenset((u, v)) for u, v, _ in events[-1]["mst_edges"]} == \
        _undirected_edge_set(mst)
    assert events[-1]["total"] == mst_weight(mst)


def test_eager_matches_lazy():
    """Жадібна (eager) версія дає ту саму вагу МОД, що й лінива."""
    for edges in (ABCDEF_EDGES, ABCDEFG_EDGES):
        g = build_graph(edges)
        assert mst_weight(prim_mst_eager(g)) == mst_weight(prim_mst(g))


def test_random_graphs_match_networkx():
    """Серія випадкових зв'язних графів: вага МОД збігається з networkx."""
    for seed in range(8):
        g = _random_connected_graph(seed)
        expected = nx.minimum_spanning_tree(g).size(weight="weight")
        assert mst_weight(prim_mst(g)) == expected
        assert mst_weight(prim_mst_eager(g)) == expected
        tree, events = prim_mst_steps(g)
        assert mst_weight(tree) == expected
        assert events[-1]["total"] == expected


def test_disconnected_base_raises():
    """Базова реалізація на незв'язному графі аварійно зупиняється.

    Черга порожніє (компонента старту вичерпана), а умова
    ``visited != set(graph.nodes())`` усе ще істинна — ``heappop`` падає з
    ``IndexError``. Саме це обмеження розібрано в прикладі 03 і README.
    """
    g = build_graph(ISLANDS_EDGES)
    raised = False
    try:
        prim_mst(g)
    except IndexError:
        raised = True
    assert raised, "очікували IndexError на незв'язному графі"


def test_disconnected_eager_returns_start_component():
    """Eager-версія мовчки повертає дерево лише компоненти старту."""
    g = build_graph(ISLANDS_EDGES)
    tree = prim_mst_eager(g, start="M")
    assert set(tree.nodes()) == {"M", "N", "O"}
    assert mst_weight(tree) == 6          # M–N (2) + N–O (4); M–O (7) відкинуто


def test_prim_msf_spanning_forest():
    """Мінімальний остовний ліс: окреме МОД у кожній компоненті + ізольовані вершини."""
    g = build_graph(ISLANDS_EDGES)
    g.add_node("Z")                       # ізольована вершина без ребер
    forest = prim_msf(g)
    assert set(forest.nodes()) == set(g.nodes())
    assert mst_weight(forest) == 9        # {M,N,O}: 2+4  +  {P,Q}: 3
    assert forest.number_of_edges() == 3
    assert forest.degree("Z") == 0
    # ліс мінімальний: збігається з networkx (який теж будує ліс)
    assert mst_weight(forest) == nx.minimum_spanning_tree(g).size(weight="weight")


def test_single_vertex_graph():
    """Виродженний випадок: одна вершина — жодного ребра, журнал з одного запису."""
    g = nx.Graph()
    g.add_node("X")
    assert prim_mst(g).number_of_edges() == 0
    tree, events = prim_mst_steps(g)
    assert tree.number_of_edges() == 0
    assert len(events) == 1 and events[0]["kind"] == "init"
    assert mst_weight(prim_mst_eager(g)) == 0


def test_build_graph_and_weight():
    g = build_graph([("A", "B", 3), ("B", "C", 1)])
    assert g.number_of_nodes() == 3
    assert g["A"]["B"]["weight"] == 3
    assert mst_weight(g) == 4             # для дерева вага = сума всіх ребер


def _run_without_pytest():
    """Мінімальний раннер на випадок, якщо pytest не встановлено."""
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failures = 0
    for test in tests:
        try:
            test()
            print(f"PASS  {test.__name__}")
        except AssertionError as exc:
            failures += 1
            print(f"FAIL  {test.__name__}: {exc}")
    print(f"\n{len(tests) - failures}/{len(tests)} тестів пройдено")
    return failures


if __name__ == "__main__":
    sys.exit(1 if _run_without_pytest() else 0)
