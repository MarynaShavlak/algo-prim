"""Приклад 0 — аналогія з кабельною мережею та властивість розрізу.

Ілюстрації для розділу «Інтуїція» README: що взагалі таке мінімальне остовне
дерево (з'єднати всі міста найдешевше) і чому жадібний вибір Прима безпечний
(властивість розрізу). Усі рисунки зберігаються в ``docs/images/``.

Запуск:  ``python examples/00_cable_analogy.py``      (українською → docs/images/)
         ``python examples/00_cable_analogy.py en``   (англійською → docs/images/en/)
"""

# _common ПЕРШИМ: налаштовує Agg, sys.path і мову до імпорту matplotlib.pyplot
from _common import print_saved_location, save_figure
from _graphs import ABCDEF, cable_plans

from prim_mst.i18n import t  # noqa: E402
from prim_mst.visualization import (  # noqa: E402
    configure_style,
    draw_cable_plans,
    draw_cut,
    draw_graph,
)


def main() -> None:
    configure_style()
    edges, pos = ABCDEF.edges, ABCDEF.positions

    # 1) карта «міст і можливих трас» — той самий граф A–F, але мовою аналогії
    save_figure(draw_graph(edges, pos, title=t("Міста та можливі траси кабелю (вартість прокладання)")),
                "cable_map_abcdef.png")

    # 2) три плани поряд: усі траси → якесь дерево → мінімальне дерево
    save_figure(draw_cable_plans(edges, pos, cable_plans(),
                                 t("Як з'єднати всі міста найдешевше?")),
                "cable_plans_abcdef.png")

    # 3) властивість розрізу: дерево {A, B, C} проти решти вершин
    save_figure(draw_cut(edges, pos, {"A", "B", "C"},
                         tree_edges=[("A", "B", 3), ("B", "C", 1)]),
                "cut_property_abcdef.png")

    print(t("Збережено 3 рисунки: аналогія з кабельною мережею + властивість розрізу."))
    print_saved_location()


if __name__ == "__main__":
    main()
