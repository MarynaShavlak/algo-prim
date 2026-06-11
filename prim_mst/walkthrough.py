# -*- coding: utf-8 -*-
"""Покрокова візуалізація «код ↔ граф» для алгоритму Прима.

Кожен крок — це рядок із трьох панелей: **ліворуч фрагмент коду з підсвіченими
активними рядками**, по центру — **граф** (дерево, що росте), праворуч —
**черга з пріоритетами** саме на цьому кроці. Колір рядка коду кодує гілку,
що спрацювала: 🟨 рядок виконується зараз, 🟩 гілка «прийняти» (вершина нова —
ребро йде в МОД), 🟥 гілка «пропустити» (ребро застаріле).

Три незалежні блоки + композитор:

* **журнал** (:func:`build_steps`) — переганяє журнал подій
  :func:`prim_mst.core.prim_mst_steps` у список **незмінних знімків** із мапою
  підсвічування та готовими аргументами обох панелей стану; знає алгоритм,
  нічого не малює;
* **кодова панель** (:func:`draw_code_panel`) — малює :data:`CODE` і підсвічує
  рядки за мапою ``{індекс: колір}`` зі знімка; нічого не знає про алгоритм;
* **панелі стану** — повторно використовуємо
  :func:`prim_mst.visualization.draw_graph_state` та
  :func:`prim_mst.visualization.draw_queue_panel`;
* **композитор** (:func:`render_code_step`, :func:`draw_code_walkthrough_grid`) —
  складає панелі в одну фігуру / у високу сітку.

Кожне зняте з черги ребро дає **два знімки**: «heappop — перевіряємо вершину»
(інтрига) та «гілка спрацювала» (розв'язка). Статична сітка показує лише
розв'язки (:func:`pick_illustrative`), повна анімація — обидва.

Двомовність: увесь видимий текст через :func:`prim_mst.i18n.t`; кольори —
зі :mod:`prim_mst.style`.
"""

from __future__ import annotations

from typing import Dict, Hashable, List, Optional, Sequence, Tuple

import matplotlib.pyplot as plt
from matplotlib.patches import Patch, Rectangle

from .core import build_graph, prim_mst_steps
from .i18n import t
from .style import (
    GREEN_TXT,
    HL_ACTIVE,
    HL_ADD,
    HL_SKIP,
    PATH_COLOR,
    TEXT_DARK,
    TEXT_FORMULA,
)
from .visualization import (
    draw_graph_state,
    draw_queue_panel,
    format_weight,
)

__all__ = [
    "CODE",
    "build_steps",
    "pick_illustrative",
    "draw_code_panel",
    "render_code_step",
    "draw_code_walkthrough_grid",
    "code_legend_handles",
]


# ---------------------------------------------------------------------------
# «Код як дані»: один елемент списку = один рядок коду. Індекси СТАБІЛЬНІ — саме
# на них посилається мапа підсвічування `hl`. Дослівно повторює серце
# `core.prim_mst` (nbrs(v) — скорочення для graph.edges(nbunch=[v]), щоб рядки
# вміщалися на панелі).
# ---------------------------------------------------------------------------
CODE: List[str] = [
    "mst, visited = nx.Graph(), {start}",         # 0  init: дерево = одна вершина
    "edges = []                      # купа",     # 1  init: порожня черга
    "for v, w in nbrs(start):",                   # 2  init: ребра старту…
    "    heappush(edges, (w, start, v))",         # 3  …ідуть у чергу
    "",                                           # 4
    "while visited != set(graph.nodes()):",       # 5  ← поки в дереві не всі вершини
    "    weight, u, v = heappop(edges)",          # 6  ← найлегше ребро з черги
    "    if v not in visited:",                   # 7  ← перевірка (гілка)
    "        visited.add(v)",                     # 8  ← гілка «прийняти»
    "        mst.add_edge(u, v, weight=weight)",  # 9  ← гілка «прийняти»
    "        for x, w in nbrs(v):",               # 10 ← нові ребра з v…
    "            if x not in visited:",           # 11
    "                heappush(edges, (w, v, x))", # 12 …ідуть у чергу
    "    # else: ребро застаріле — пропускаємо",  # 13 ← гілка «пропустити»
]

# Семантичні набори рядків для `hl` (значення — кольори зі style.py):
_HL_INIT = {0: HL_ACTIVE, 1: HL_ACTIVE, 2: HL_ACTIVE, 3: HL_ACTIVE}
_HL_TEST = {6: HL_ACTIVE, 7: HL_ACTIVE}                  # зняли ребро й перевіряємо
_HL_ACCEPT = {6: HL_ACTIVE, 7: HL_ACTIVE,
              8: HL_ADD, 9: HL_ADD, 10: HL_ADD, 11: HL_ADD, 12: HL_ADD}
_HL_SKIP = {6: HL_ACTIVE, 7: HL_ACTIVE, 13: HL_SKIP}
_HL_DONE = {5: HL_ACTIVE}                                # умова циклу стала хибною


# ---------------------------------------------------------------------------
# Блок 1 — журнал кроків (знімки НЕЗМІННІ: складаємо з копій подій core)
# ---------------------------------------------------------------------------
def build_steps(
    edge_list: Sequence[Tuple[Hashable, Hashable, float]],
    start: Optional[Hashable] = None,
) -> List[Dict]:
    """Журнал знімків «код ↔ граф ↔ черга» для покрокових панелей.

    Кожне зняте з черги ребро розгортається у два знімки: ``test`` (heappop,
    рішення ще не ухвалене — ребро помаранчеве, верхній рядок черги жовтий) і
    ``add``/``skip`` (гілка спрацювала). На початку — ``init``, наприкінці —
    ``final``. Знімок містить готові аргументи для
    :func:`visualization.draw_graph_state` (``graph_args``) та
    :func:`visualization.draw_queue_panel` (``queue_args``).
    """
    graph = build_graph(list(edge_list))
    n_nodes = graph.number_of_nodes()
    _, events = prim_mst_steps(graph, start=start)

    init = events[0]
    steps: List[Dict] = [{
        "kind": "init",
        "hl": dict(_HL_INIT),
        "title": t("Старт: {s}").format(s=init["start"]),
        "caption": t("дерево = {{{s}}}; у черзі — ребра з {s}").format(s=init["start"]),
        "graph_args": dict(visited=init["visited"], tree_edges=init["mst_edges"],
                           fringe=list(init["queue"])),
        "queue_args": dict(queue=init["queue"], visited=init["visited"],
                           total=init["total"], pushed=init["pushed"],
                           list_label=t("у чергу покладено ребра з {s}:").format(
                               s=init["start"])),
    }]

    for prev, event in zip(events, events[1:]):
        w, u, v = event["edge"]
        edge_txt = f"({format_weight(w)}, {u}, {v})"

        # 1) heappop: рішення ще не ухвалене — стан ДО події, ребро «у фокусі»
        steps.append({
            "kind": "test",
            "hl": dict(_HL_TEST),
            "title": t("Крок {i}: heappop").format(i=event["step"]),
            "caption": t("heappop → {edge}: чи є {v} у visited?").format(
                edge=edge_txt, v=v),
            "graph_args": dict(visited=prev["visited"], tree_edges=prev["mst_edges"],
                               fringe=[e for e in prev["queue"]
                                       if e[2] not in prev["visited"]],
                               popped=event["edge"], popped_ok=None),
            "queue_args": dict(queue=prev["queue"], visited=prev["visited"],
                               total=prev["total"], highlight_top=True),
        })

        # 2) гілка спрацювала — стан ПІСЛЯ події
        if event["kind"] == "add":
            kind, hl = "add", dict(_HL_ACCEPT)
            title = t("Крок {i}: + {u}–{v} ({w})").format(
                i=event["step"], u=u, v=v, w=format_weight(w))
            caption = t("{edge}: {v} ще немає у visited → ребро прийнято в МОД ✔").format(
                edge=edge_txt, v=v)
        else:
            kind, hl = "skip", dict(_HL_SKIP)
            title = t("Крок {i}: пропуск").format(i=event["step"])
            caption = t("{edge}: {v} уже у visited → ребро застаріле, пропуск ✗").format(
                edge=edge_txt, v=v)
        steps.append({
            "kind": kind,
            "hl": hl,
            "title": title,
            "caption": caption,
            "graph_args": dict(visited=event["visited"], tree_edges=event["mst_edges"],
                               fringe=[e for e in event["queue"]
                                       if e[2] not in event["visited"]],
                               popped=event["edge"], popped_ok=(kind == "add"),
                               just_added=(v if kind == "add" else None)),
            "queue_args": dict(queue=event["queue"], visited=event["visited"],
                               total=event["total"], popped=event["edge"],
                               verdict=kind, pushed=event["pushed"]),
        })

    last = events[-1]
    steps.append({
        "kind": "final",
        "hl": dict(_HL_DONE),
        "title": t("Готово: вага {total}").format(total=format_weight(last["total"])),
        "caption": t("усі вершини в дереві → умова while хибна; вага МОД = {total}").format(
            total=format_weight(last["total"])),
        "graph_args": dict(visited=last["visited"], tree_edges=last["mst_edges"],
                           fringe=[e for e in last["queue"]
                                   if e[2] not in last["visited"]]),
        "queue_args": dict(queue=last["queue"], visited=last["visited"],
                           total=last["total"],
                           list_label=t("у черзі лишилось (уже не знадобиться):")),
    })

    # кожна подія дала рівно два знімки + init + final
    assert len(steps) == 2 * (len(events) - 1) + 2, "журнал не збігається з подіями"
    return steps


def pick_illustrative(steps: List[Dict]) -> List[Dict]:
    """Зріз журналу для СТАТИЧНОЇ сітки: лише розв'язки, без кадрів heappop.

    Кадри ``test`` («інтрига» перед перевіркою) важливі в анімації, але в
    статичній сітці вони подвоювали б кожен рядок. Лишаємо ``init``, усі
    ``add``/``skip`` та ``final``.
    """
    return [s for s in steps if s["kind"] != "test"]


# ---------------------------------------------------------------------------
# Блок 2 — кодова панель (ліворуч)
# ---------------------------------------------------------------------------
def draw_code_panel(ax, highlights: Dict[int, str], code: Sequence[str] = CODE,
                    *, fontsize: float = 9.6) -> None:
    """Малює ``code`` на осі ``ax`` і підсвічує рядки за мапою ``highlights``.

    :param highlights: ``{індекс_рядка: колір_заливки}`` зі знімка журналу.
    Рендер **чистий**: та сама мапа → та сама картинка, без знання про алгоритм.
    Кожен рядок проганяється через :func:`t` (коментарі перекладуться, чистий
    код — лишиться незмінним обома мовами).
    """
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    nlines = len(code)
    line_h = 1.0 / nlines
    for i, line in enumerate(code):
        y = 1.0 - (i + 0.5) * line_h
        if i in highlights:
            ax.add_patch(Rectangle((0, y - line_h * 0.46), 1, line_h * 0.92,
                                   facecolor=highlights[i], edgecolor="none", zorder=0))
        ax.text(0.02, y, t(line), family="monospace", fontsize=fontsize,
                va="center", ha="left", color=TEXT_DARK, zorder=2)


def code_legend_handles() -> List[Patch]:
    """Хендли легенди підсвічування коду (для ``fig.legend``)."""
    return [
        Patch(facecolor=HL_ACTIVE, edgecolor="none", label=t("активний рядок")),
        Patch(facecolor=HL_ADD, edgecolor="none", label=t("прийнято (ребро в МОД)")),
        Patch(facecolor=HL_SKIP, edgecolor="none", label=t("пропуск (застаріле ребро)")),
    ]


def _caption_color(kind: str) -> str:
    """Колір підпису-вердикту за типом кроку."""
    if kind in ("add", "final"):
        return GREEN_TXT
    if kind == "skip":
        return PATH_COLOR
    return TEXT_FORMULA


# ---------------------------------------------------------------------------
# Композитор — одна фігура на крок (анімація) + повна сітка (статика)
# ---------------------------------------------------------------------------
def render_code_step(
    step: Dict,
    edge_list: Sequence[Tuple[Hashable, Hashable, float]],
    pos: Dict[Hashable, Tuple[float, float]],
    n_nodes: int,
    *,
    figsize: Tuple[float, float] = (12.8, 4.5),
    code: Sequence[str] = CODE,
):
    """Один крок → одна фігура ``[код | граф | черга]`` (кадр для анімації).

    :returns: об'єкт ``Figure``.
    """
    fig, (axc, axg, axq) = plt.subplots(
        1, 3, figsize=figsize, gridspec_kw={"width_ratios": [1.12, 1.5, 0.95]})
    draw_code_panel(axc, step["hl"], code)
    draw_graph_state(axg, list(edge_list), pos, node_size=560, weight_fs=9.5,
                     **step["graph_args"])
    axg.set_title(step["title"], fontsize=11.5)
    draw_queue_panel(axq, n_nodes=n_nodes, **step["queue_args"])
    if step.get("caption"):
        fig.text(0.5, 0.022, step["caption"], ha="center", va="bottom",
                 fontsize=10, family="monospace", color=_caption_color(step["kind"]))
    fig.subplots_adjust(left=0.02, right=0.98, top=0.92, bottom=0.11, wspace=0.07)
    return fig


def draw_code_walkthrough_grid(
    steps: List[Dict],
    edge_list: Sequence[Tuple[Hashable, Hashable, float]],
    pos: Dict[Hashable, Tuple[float, float]],
    n_nodes: int,
    suptitle: str,
    *,
    code: Sequence[str] = CODE,
    row_h: float = 4.0,
    width: float = 12.8,
    legend: bool = True,
):
    """Усі ``steps`` у ОДНІЙ високій сітці: рядок = ``[код | граф | черга]``.

    :param steps: журнал (повний або зріз :func:`pick_illustrative`).
    :returns: об'єкт ``Figure``.
    """
    nrow = len(steps)
    fig, axes = plt.subplots(nrow, 3, figsize=(width, row_h * nrow),
                             gridspec_kw={"width_ratios": [1.12, 1.5, 0.95]})
    if nrow == 1:
        axes = [axes]
    for r, step in enumerate(steps):
        axc, axg, axq = axes[r]
        draw_code_panel(axc, step["hl"], code)
        draw_graph_state(axg, list(edge_list), pos, node_size=560, weight_fs=9.5,
                         **step["graph_args"])
        axg.set_title(step["title"], fontsize=11.5)
        draw_queue_panel(axq, n_nodes=n_nodes, **step["queue_args"])
        if step.get("caption"):
            axg.text(0.5, -0.07, step["caption"], transform=axg.transAxes,
                     ha="center", va="top", fontsize=9, family="monospace",
                     color=_caption_color(step["kind"]), clip_on=False)

    fig.suptitle(suptitle, fontsize=14, fontweight="bold")
    bottom = 0.035 if legend else 0.01
    if legend:
        fig.legend(handles=code_legend_handles(), loc="lower center", ncol=3,
                   frameon=False, fontsize=10, bbox_to_anchor=(0.5, 0.002))
    fig.tight_layout(rect=(0, bottom, 1, 0.985), h_pad=4.5)
    return fig
