"""Навчальна реалізація та візуалізація алгоритму Прима (МОД).

Пакет розділено на модулі:

* :mod:`prim_mst.core` — сам алгоритм (``prim_mst``, ``prim_mst_steps``,
  ``prim_mst_eager``), мінімальний остовний ліс та утиліти;
* :mod:`prim_mst.visualization` — функції малювання графів, кроків і панелі
  черги з пріоритетами (потребують ``matplotlib`` і ``networkx``);
* :mod:`prim_mst.walkthrough` — покрокова візуалізація «код ↔ граф» з
  підсвічуванням активних рядків коду (потребує ``matplotlib``);
* :mod:`prim_mst.animation` — збірка анімацій GIF (Pillow) + MP4 (ffmpeg).

``core`` та ``i18n`` не тягнуть ``matplotlib``, тож ``import prim_mst``
лишається легким; модулі малювання імпортують явно
(``from prim_mst.visualization import …`` / ``… .walkthrough import …``).

Приклад::

    from prim_mst import build_graph, prim_mst, mst_weight

    graph = build_graph([("A", "B", 3), ("B", "C", 1), ("A", "C", 5)])
    mst = prim_mst(graph)
    print(mst_weight(mst))   # 4
"""

from .core import (
    build_graph,
    mst_weight,
    prim_msf,
    prim_mst,
    prim_mst_eager,
    prim_mst_steps,
)
from .i18n import get_lang, set_lang, t

__all__ = [
    "build_graph",
    "prim_mst",
    "prim_mst_steps",
    "prim_mst_eager",
    "prim_msf",
    "mst_weight",
    # двомовні підписи (uk/en) — без важких залежностей, тож безпечно тут
    "t",
    "set_lang",
    "get_lang",
]

# Єдине джерело правди для версії пакета: pyproject.toml читає його звідси через
# [tool.setuptools.dynamic] version = { attr = "prim_mst.__version__" }.
__version__ = "1.0.0"
