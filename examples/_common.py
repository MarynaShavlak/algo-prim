"""Спільні утиліти для прикладів (``examples/``).

Щоб кожен приклад не повторював той самий boilerplate (перемикання matplotlib
на ``Agg``, додавання кореня репозиторію в ``sys.path``, обчислення шляху до
``docs/images`` та однаковісінькі функції збереження фігур і друку шляхів),
усе зведено в одне місце.

Імпортуйте цей модуль ПЕРШИМ у прикладі — він налаштовує ``Agg`` до того, як
буде імпортовано ``matplotlib.pyplot``.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from typing import Dict, Hashable, List, Tuple

import matplotlib

matplotlib.use("Agg")  # зберігаємо у файли без графічного дисплея

# корінь репозиторію в sys.path — дозволяє запуск без `pip install -e .`
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from prim_mst.animation import save_animation as _save_animation  # noqa: E402
from prim_mst.core import mst_weight  # noqa: E402
from prim_mst.i18n import missing_translations, set_lang, t  # noqa: E402
from prim_mst.style import FIGURE_DPI  # noqa: E402
from prim_mst.visualization import format_weight, print_mst_edges  # noqa: E402

# --- вибір мови підписів із аргументів CLI ---------------------------------
# Передайте "en" аргументом (``python examples/01_graph_abcdef.py en``), щоб
# малювати англійською. Імпортуйте _common ПЕРШИМ: тут одразу перемикається мова
# t() і маршрут теки виводу, тож усі подальші виклики малювання знають мову.
LANG: str = "en" if "en" in sys.argv[1:] else "uk"
set_lang(LANG)

#: Тека, куди приклади зберігають усі рисунки (англійською → у підтеку ``en/``).
IMG_DIR = (
    os.path.join(_ROOT, "docs", "images", "en") if LANG == "en"
    else os.path.join(_ROOT, "docs", "images")
)
os.makedirs(IMG_DIR, exist_ok=True)


@dataclass(frozen=True)
class GraphExample:
    """Дані одного прикладу: список ребер та координати вершин.

    :param edges: ребра ``(u, v, вага)`` неорієнтованого графа.
    :param positions: координати вершин ``{вершина: (x, y)}`` для малювання.
    """

    edges: List[Tuple[Hashable, Hashable, float]]
    positions: Dict[Hashable, Tuple[float, float]] = field(default_factory=dict)

    @property
    def nodes(self) -> List[Hashable]:
        """Вершини у порядку першої появи в ребрах."""
        seen: List[Hashable] = []
        for u, v, _ in self.edges:
            for node in (u, v):
                if node not in seen:
                    seen.append(node)
        return seen

    @property
    def n(self) -> int:
        """Кількість вершин."""
        return len(self.nodes)


def save_figure(fig, name: str) -> None:
    """Зберігає фігуру у :data:`IMG_DIR` під іменем ``name``."""
    fig.savefig(os.path.join(IMG_DIR, name), bbox_inches="tight", dpi=FIGURE_DPI)


def save_anim(figures, basename: str, durations, **kwargs):
    """Зберігає анімацію у :data:`IMG_DIR`: GIF завжди + MP4 за наявності ffmpeg.

    :param figures: список фігур-кадрів (будуть закриті під час рендера).
    :param basename: ім'я файлу БЕЗ розширення — ``.gif`` і ``.mp4`` додаються самі.
    :param durations: тривалість кадру(ів) у мс (число або послідовність).
    :returns: шлях до MP4, якщо його записано, інакше ``None`` (GIF є завжди).
    """
    gif = os.path.join(IMG_DIR, basename + ".gif")
    mp4 = os.path.join(IMG_DIR, basename + ".mp4")
    return _save_animation(figures, gif, durations, mp4_path=mp4, **kwargs)


def report_mst(mst, example: GraphExample) -> None:
    """Друкує підсумок: ребра МОД (як у базовій реалізації), вагу та відкинуті ребра."""
    print_mst_edges(mst)
    total = mst_weight(mst)
    print(t("Вага МОД: {total}   (ребер: {k} із {m} можливих)").format(
        total=format_weight(total), k=mst.number_of_edges(), m=len(example.edges)))
    rejected = [(u, v, w) for u, v, w in example.edges if not mst.has_edge(u, v)]
    if rejected:
        skipped = ", ".join(
            t("{u}–{v} ({w})").format(u=u, v=v, w=format_weight(w)) for u, v, w in rejected)
        print(t("Не ввійшли до МОД: {edges}").format(edges=skipped))


def print_saved_location() -> None:
    """Друкує підсумкове повідомлення про теку зі збереженими рисунками.

    В англійському режимі заразом звітує аудит i18n: якщо якийсь кириличний
    підпис не знайшов перекладу, він потрапив у ``missing_translations`` — про
    це попереджаємо (рисунок вийшов із українським текстом).
    """
    print(t("\nРисунки збережено у: {path}").format(path=IMG_DIR))
    if LANG == "en" and missing_translations:
        print("WARNING: missing EN translations for:")
        for s in sorted(missing_translations):
            print("  -", repr(s))
