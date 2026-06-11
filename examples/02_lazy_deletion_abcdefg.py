"""Приклад 2 — граф ``A–G`` з лекції: «ліниве видалення» у дії.

Це той самий граф, на якому демонструвалася базова реалізація. Він цікавий
тим, що на ньому черга накопичує **застарілі** ребра: на кроках 6–8 алгоритм
тричі поспіль знімає ребро, обидва кінці якого вже в дереві, і просто
пропускає його (рядок ``if v not in visited``). Усі рисунки зберігаються в
``docs/images/``.

Запуск:  ``python examples/02_lazy_deletion_abcdefg.py``      (uk → docs/images/)
         ``python examples/02_lazy_deletion_abcdefg.py en``   (en → docs/images/en/)
"""

# _common ПЕРШИМ: налаштовує Agg, sys.path і мову до імпорту matplotlib.pyplot
from _common import print_saved_location, report_mst, save_figure
from _graphs import ABCDEFG

from prim_mst.core import build_graph, prim_mst_steps  # noqa: E402
from prim_mst.i18n import t  # noqa: E402
from prim_mst.visualization import (  # noqa: E402
    configure_style,
    draw_evolution,
    draw_graph,
    draw_mst_result,
    show_step,
)

# --- дані прикладу: граф A–G (єдине джерело — examples/_graphs.py) -----------
EXAMPLE = ABCDEFG


def main() -> None:
    configure_style()
    edges, pos, n = EXAMPLE.edges, EXAMPLE.positions, EXAMPLE.n
    graph = build_graph(edges)

    # 1) сам граф
    save_figure(draw_graph(edges, pos, figsize=(7.6, 5.4)), "graph_abcdefg.png")

    # 2) алгоритм із журналом (старт явно з A — як list(graph.nodes())[0])
    mst, events = prim_mst_steps(graph, start="A")
    skips = [e for e in events if e["kind"] == "skip"]
    print(t("Готово: {n} подій, із них {k} — застарілі ребра (ліниве видалення).").format(
        n=len(events), k=len(skips)))
    print()

    # 3) кадр [граф | черга] після кожної події (+ текстовий підсумок у консоль)
    for event in events:
        fig = show_step(event, edges, pos, n)
        save_figure(fig, f"step_abcdefg_{event['step']}.png")
        print()

    # 4) зведена сітка еволюції
    save_figure(draw_evolution(events, edges, pos,
                               t("Еволюція МОД на графі A–G: три застарілі ребра поспіль"),
                               ncols=4),
                "evolution_abcdefg.png")

    # 5) підсумковий рисунок: МОД + відкинуті ребра
    save_figure(draw_mst_result(edges, events[-1]["mst_edges"], pos,
                                figsize=(7.6, 5.4)),
                "mst_abcdefg.png")

    # 6) підсумок у консоль
    report_mst(mst, EXAMPLE)

    print_saved_location()


if __name__ == "__main__":
    main()
