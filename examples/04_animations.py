"""Приклад 4 — GIF/MP4-анімації для README.

Показує АЛГОРИТМ У РУСІ там, де статичний кадр поступається. Статичні рисунки
(``.png``) генерують приклади 00–03; тут — лише анімації.

1. ``evolution_abcdef`` / ``evolution_abcdefg`` — дерево росте ребро за
   ребром: кадр ``[граф | черга]`` після кожної події журналу (зелене дерево
   більшає, у черзі видно нові та застарілі ребра);
2. ``cut_steps_abcdef`` — властивість розрізу в русі: перед кожним кроком
   видно розріз «дерево S проти решти» і те, що Прим бере САМЕ найдешевше
   ребро через розріз;
3. ``cable_plans_abcdef`` — аналогія з кабельною мережею: усі траси → якесь
   дерево → мінімальне дерево.

Запуск:  ``python examples/04_animations.py``      (uk → docs/images/)
         ``python examples/04_animations.py en``   (en → docs/images/en/)
"""

# _common ПЕРШИМ: налаштовує Agg, sys.path і мову до імпорту matplotlib.pyplot
from _common import GraphExample, print_saved_location, save_anim
from _graphs import ABCDEF, ABCDEFG, cable_plans

from prim_mst.core import build_graph, prim_mst_steps  # noqa: E402
from prim_mst.i18n import t  # noqa: E402
from prim_mst.visualization import (  # noqa: E402
    configure_style,
    draw_cable_plan,
    draw_cut,
    draw_mst_result,
    draw_prim_step,
    format_weight,
)

# Графи ABCDEF / ABCDEFG беремо з examples/_graphs.py (єдине джерело правди).
# Збереження кадрів робить save_anim із _common: GIF завжди + MP4 за наявності
# ffmpeg, у теку поточної мови (docs/images або docs/images/en). Параметр name —
# базове ім'я файлу БЕЗ розширення.


def animate_evolution(example: GraphExample, name: str, figsize=(11.5, 5.2)) -> None:
    """GIF/MP4: кадр ``[граф | черга]`` після кожної події журналу.

    Прийняті ребра тримаємо на екрані довше, застарілі — теж помітно (це
    головний навчальний момент), стартовий кадр коротше, фінальний — із
    додатковою затримкою перед зацикленням.
    """
    edges, pos, n = example.edges, example.positions, example.n
    _, events = prim_mst_steps(build_graph(edges), start="A")
    figures, durations = [], []
    for event in events:
        figures.append(draw_prim_step(event, edges, pos, n, figsize=figsize))
        if event["kind"] == "init":
            durations.append(1600)
        elif event["kind"] == "add":
            durations.append(2200)
        else:
            durations.append(1900)
    durations[-1] += 1400
    save_anim(figures, name, durations)
    print(t("  {name}: {n} кадрів").format(name=name, n=len(figures)))


def animate_cut(example: GraphExample, name: str, figsize=(7.6, 5.4)) -> None:
    """GIF/MP4: властивість розрізу перед кожним кроком Прима.

    Для кожного прийнятого ребра показуємо стан ДО кроку: дерево ``S``
    (зелене), решта вершин (сірі), усі ребра через розріз (сині пунктирні) і
    найдешевше з них (зелене суцільне) — саме його й бере алгоритм. Фінальний
    кадр — готове МОД.
    """
    edges, pos = example.edges, example.positions
    _, events = prim_mst_steps(build_graph(edges), start="A")
    figures, durations = [], []
    for prev, event in zip(events, events[1:]):
        if event["kind"] != "add":
            continue
        fig = draw_cut(
            edges, pos, prev["visited"], tree_edges=prev["mst_edges"], shade=False,
            figsize=figsize,
            title=t("Крок {i}: найдешевше ребро через розріз → у МОД").format(
                i=event["step"]))
        figures.append(fig)
        durations.append(2400)
    figures.append(draw_mst_result(edges, events[-1]["mst_edges"], pos,
                                   figsize=figsize))
    durations.append(3000)
    save_anim(figures, name, durations)
    print(t("  {name}: {n} кадрів").format(name=name, n=len(figures)))


def animate_cable(name: str) -> None:
    """GIF/MP4: аналогія з кабельною мережею — три плани по черзі."""
    edges, pos = ABCDEF.edges, ABCDEF.positions
    title = t("Як з'єднати всі міста найдешевше?")
    figures = [draw_cable_plan(edges, pos, plan, title) for plan in cable_plans()]
    durations = [1700, 2100, 2800]
    save_anim(figures, name, durations)
    print(t("  {name}: {n} кадрів").format(name=name, n=len(figures)))


def main() -> None:
    configure_style()
    print(t("Генерую GIF-анімації…"))

    # імена — БЕЗ розширення: save_anim сам додасть .gif (+ .mp4 за наявності ffmpeg)
    # 1) еволюція дерева: [граф | черга] подія за подією
    animate_evolution(ABCDEF, "evolution_abcdef")
    animate_evolution(ABCDEFG, "evolution_abcdefg")

    # 2) властивість розрізу в русі (основний граф A–F)
    animate_cut(ABCDEF, "cut_steps_abcdef")

    # 3) аналогія з кабельною мережею
    animate_cable("cable_plans_abcdef")

    print_saved_location()


if __name__ == "__main__":
    main()
