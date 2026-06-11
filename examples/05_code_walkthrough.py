"""Приклад 5 — покрокова візуалізація «код ↔ граф ↔ черга».

Кожен крок = рядок із трьох панелей: ліворуч код алгоритму з **підсвіченими
активними рядками** (колір показує, яка гілка ``if`` спрацювала), по центру —
**граф** (дерево, що росте), праворуч — **черга з пріоритетами** саме на цьому
кроці. Логіку див. у ``prim_mst/walkthrough.py``.

Для кожного навчального графа (A–F, A–G) генеруємо два артефакти:

* **статичну сітку** (``code_steps_*.png``) — лише «розв'язки» (init + кожна
  гілка add/skip + підсумок);
* **повну анімацію** (``code_walk_*.gif`` + ``.mp4``) — з проміжними кадрами
  «heappop: перевіряємо вершину».

Запуск:  ``python examples/05_code_walkthrough.py``      (uk → docs/images/)
         ``python examples/05_code_walkthrough.py en``   (en → docs/images/en/)
"""

# _common ПЕРШИМ: налаштовує Agg, sys.path і мову до імпорту matplotlib.pyplot
from _common import GraphExample, print_saved_location, save_anim, save_figure
from _graphs import ABCDEF, ABCDEFG

import matplotlib.pyplot as plt  # noqa: E402

from prim_mst.i18n import t  # noqa: E402
from prim_mst.visualization import configure_style  # noqa: E402
from prim_mst.walkthrough import (  # noqa: E402
    build_steps,
    draw_code_walkthrough_grid,
    pick_illustrative,
    render_code_step,
)

# Тривалість кадру анімації за типом кроку (мс): «розв'язки» тримаємо довше,
# проміжні кадри heappop — коротше (вони лише створюють інтригу).
_DUR = {"init": 1700, "test": 1000, "add": 2100, "skip": 1900, "final": 3000}


def make_walkthrough(example: GraphExample, grid_name: str, anim_name: str) -> None:
    """Статична сітка «розв'язок» + повна анімація для одного графа."""
    edges, pos, n = example.edges, example.positions, example.n
    steps = build_steps(edges, start="A")

    # 1) статична сітка: init + кожна гілка add/skip + підсумок
    shown = pick_illustrative(steps)
    grid = draw_code_walkthrough_grid(
        shown, edges, pos, n, t("Код ↔ граф ↔ черга: по одному рядку на кожне зняте ребро"))
    save_figure(grid, grid_name + ".png")
    plt.close(grid)
    print(t("  {name}: сітка, {n} рядків").format(name=grid_name, n=len(shown)))

    # 2) повна анімація (із кадрами «heappop: перевіряємо вершину»)
    figures = [render_code_step(s, edges, pos, n) for s in steps]
    durations = [_DUR.get(s["kind"], 800) for s in steps]
    save_anim(figures, anim_name, durations)
    print(t("  {name}: анімація, {n} кадрів").format(name=anim_name, n=len(figures)))


def main() -> None:
    configure_style()
    print(t("Генерую покрокові панелі «код ↔ граф ↔ черга»…"))

    # імена — БЕЗ розширення (save_figure додає .png; save_anim — .gif/.mp4)
    make_walkthrough(ABCDEF, "code_steps_abcdef", "code_walk_abcdef")
    make_walkthrough(ABCDEFG, "code_steps_abcdefg", "code_walk_abcdefg")

    print_saved_location()


if __name__ == "__main__":
    main()
