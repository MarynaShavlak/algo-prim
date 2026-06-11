"""Приклад 1 — основний граф ``A–F`` (той самий, що в проєкті про Флойда–Воршала).

Відтворює весь покроковий розбір із README: сам граф, кадр ``[граф | черга]``
після кожної події (старт + 5 знятих ребер), зведену сітку еволюції та
підсумковий рисунок МОД із відкинутим ребром. Усі рисунки зберігаються в
``docs/images/``.

Запуск:  ``python examples/01_graph_abcdef.py``      (українською → docs/images/)
         ``python examples/01_graph_abcdef.py en``   (англійською → docs/images/en/)
"""

# _common ПЕРШИМ: налаштовує Agg, sys.path і мову до імпорту matplotlib.pyplot
from _common import print_saved_location, report_mst, save_figure
from _graphs import ABCDEF

from prim_mst.core import build_graph, mst_weight, prim_mst, prim_mst_steps  # noqa: E402
from prim_mst.i18n import t  # noqa: E402
from prim_mst.visualization import (  # noqa: E402
    configure_style,
    draw_evolution,
    draw_graph,
    draw_mst_result,
    format_weight,
    show_step,
)

# --- дані прикладу: граф A–F (єдине джерело — examples/_graphs.py) -----------
EXAMPLE = ABCDEF


def main() -> None:
    configure_style()
    edges, pos, n = EXAMPLE.edges, EXAMPLE.positions, EXAMPLE.n
    graph = build_graph(edges)

    # 1) сам граф (нейтральний, без стану алгоритму)
    save_figure(draw_graph(edges, pos, figsize=(7, 5)), "graph_abcdef.png")

    # 2) алгоритм із журналом подій (старт явно з A — як list(graph.nodes())[0])
    mst, events = prim_mst_steps(graph, start="A")
    print(t("Готово: журнал містить {n} подій (старт + по одній на кожне зняте ребро).").format(
        n=len(events)))
    print()

    # 3) кадр [граф | черга] після кожної події (+ текстовий підсумок у консоль)
    for event in events:
        fig = show_step(event, edges, pos, n)
        save_figure(fig, f"step_abcdef_{event['step']}.png")
        print()

    # 4) зведена сітка еволюції
    save_figure(draw_evolution(events, edges, pos,
                               t("Еволюція МОД: дерево росте ребро за ребром (граф A–F)"),
                               ncols=3),
                "evolution_abcdef.png")

    # 5) підсумковий рисунок: МОД + відкинуте ребро
    save_figure(draw_mst_result(edges, events[-1]["mst_edges"], pos), "mst_abcdef.png")

    # 6) підсумок у консоль (формат базової реалізації + вага + відкинуті ребра)
    report_mst(mst, EXAMPLE)

    # 7) звірка: інструментована версія == базова == networkx
    import networkx as nx  # noqa: E402  (локальний імпорт лише для звірки)
    base = prim_mst(graph)
    reference = nx.minimum_spanning_tree(graph)
    assert mst_weight(base) == mst_weight(mst) == reference.size(weight="weight")
    print()
    print(t("Звірка: базова реалізація і networkx дають ту саму вагу МОД ({total}) ✓").format(
        total=format_weight(mst_weight(mst))))

    print_saved_location()


if __name__ == "__main__":
    main()
