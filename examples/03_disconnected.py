"""Приклад 3 — обмеження Прима: незв'язний граф.

Остовне дерево існує лише у **зв'язного** графа. Цей приклад показує, що
станеться, якщо забути про це:

* базова реалізація ``prim_mst`` аварійно зупиняється (``IndexError``: черга
  спорожніла, а недосяжні вершини так і не потрапили в дерево);
* ``prim_mst_eager`` «тихо» повертає дерево лише однієї компоненти —
  результат виглядає правдоподібно, але остовним деревом не є;
* чесний вихід — перевірити ``nx.is_connected`` перед запуском або будувати
  **мінімальний остовний ліс** (``prim_msf``): окреме МОД у кожній компоненті.

Запуск:  ``python examples/03_disconnected.py``      (uk → docs/images/)
         ``python examples/03_disconnected.py en``   (en → docs/images/en/)
"""

# _common ПЕРШИМ: налаштовує Agg, sys.path і мову до імпорту matplotlib.pyplot
from _common import print_saved_location, save_figure
from _graphs import ISLANDS

import networkx as nx  # noqa: E402

from prim_mst.core import (  # noqa: E402
    build_graph,
    mst_weight,
    prim_msf,
    prim_mst,
    prim_mst_eager,
)
from prim_mst.i18n import t  # noqa: E402
from prim_mst.visualization import (  # noqa: E402
    configure_style,
    draw_graph,
    draw_mst_result,
    format_weight,
)

# --- дані прикладу: два «острови» (єдине джерело — examples/_graphs.py) ------
EXAMPLE = ISLANDS


def main() -> None:
    configure_style()
    edges, pos = EXAMPLE.edges, EXAMPLE.positions
    graph = build_graph(edges)

    # 1) сам граф: дві компоненти зв'язності
    save_figure(draw_graph(edges, pos, title=t("Незв'язний граф: два «острови»"),
                           figsize=(7, 4.6)),
                "graph_islands.png")

    # 2) чесна перевірка перед запуском
    print(t("Чи зв'язний граф? nx.is_connected → {flag}").format(
        flag=nx.is_connected(graph)))
    components = [sorted(c) for c in nx.connected_components(graph)]
    print(t("Компоненти зв'язності: {comps}").format(
        comps="; ".join("{" + ", ".join(map(str, c)) + "}" for c in components)))
    print()

    # 3) що буде, якщо запустити базову реалізацію попри все
    print(t("Запускаємо базову реалізацію prim_mst на незв'язному графі…"))
    try:
        prim_mst(graph)
        print(t("  (несподівано: помилки не сталося)"))
    except IndexError:
        start_component = next(c for c in nx.connected_components(graph) if "M" in c)
        unreachable = sorted(set(graph.nodes()) - start_component)
        print(t("  💥 IndexError: heappop із порожньої черги."))
        print(t("  Дерево охопило компоненту старту, а вершини {missing} недосяжні —").format(
            missing=", ".join(map(str, unreachable))))
        print(t("  умова `visited != set(graph.nodes())` ніколи не стане хибною."))
    print()

    # 4) eager-версія не падає, але повертає дерево ЛИШЕ компоненти старту
    partial = prim_mst_eager(graph, start="M")
    print(t("prim_mst_eager(start=M) повертає дерево лише компоненти {{M, N, O}}: вага {w}.").format(
        w=format_weight(mst_weight(partial))))
    print(t("Це НЕ остовне дерево всього графа — частину вершин втрачено мовчки!"))
    print()

    # 5) чесний результат для незв'язного графа — мінімальний остовний ліс
    forest = prim_msf(graph)
    print(t("Мінімальний остовний ліс (prim_msf): {k} ребра, вага {w}.").format(
        k=forest.number_of_edges(), w=format_weight(mst_weight(forest))))
    forest_edges = [(u, v, d["weight"]) for u, v, d in forest.edges(data=True)]
    save_figure(draw_mst_result(edges, forest_edges, pos,
                                title=t("Мінімальний остовний ліс (вага {w})").format(
                                    w=format_weight(mst_weight(forest))),
                                figsize=(7, 4.6)),
                "msf_islands.png")

    print_saved_location()


if __name__ == "__main__":
    main()
