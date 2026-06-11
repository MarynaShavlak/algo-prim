"""Візуалізації для навчального розбору алгоритму Прима.

Алгоритм Прима «живе» у двох структурах одночасно: на **графі** (дерево, що
росте) і в **черзі з пріоритетами** (ребра-кандидати). Тому центральний кадр
розбору — це пара панелей ``[граф | черга]``, побудована з події журналу
:func:`prim_mst.core.prim_mst_steps`:

* :func:`draw_graph` — нейтральний зважений граф (без стану алгоритму);
* :func:`draw_graph_state` / :func:`draw_queue_panel` — складові панелі
  (малюють на переданих осях, із них збираються всі композиції);
* :func:`draw_prim_step` — головний кадр кроку: граф + черга поряд;
* :func:`draw_evolution` — зведена сітка станів після кожного кроку;
* :func:`draw_mst_result` — підсумок: МОД зеленим, відкинуті ребра пунктиром;
* :func:`draw_cut` — ілюстрація властивості розрізу (чому жадібний вибір
  безпечний);
* :func:`draw_cable_plans` / :func:`draw_cable_plan` — аналогія з кабельною
  мережею для розділу «Інтуїція»;
* :func:`step_summary` / :func:`show_step` — текстовий підсумок кроку + кадр.

Кольорова схема (єдина для всіх візуалізацій):

* 🟩 зелений — вершини/ребра, що ВЖЕ в МОД (дерево росте зеленим);
* 🟦 синій пунктир — ребра, що зараз лежать у черзі з пріоритетами;
* 🔴 червоний — ребро, щойно зняте з черги (суцільне = прийнято, пунктир
  з ✗ = застаріле, пропущено);
* 🟧 помаранчеве кільце — вершина, щойно додана на цьому кроці.
"""

from __future__ import annotations

from typing import Dict, FrozenSet, Hashable, Iterable, List, Optional, Sequence, Tuple

import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch, Patch, Rectangle

from .core import Event, QueueEdge, build_graph
from .i18n import t
from .style import (
    FIGURE_DPI,
    configure_style,
    BLUE_EDGE,
    CUT_EDGE,
    CUT_FILL,
    FRINGE_EDGE,
    GREEN_TXT,
    HEADER_TXT,
    MUTED_TXT,
    NEUTRAL_GRAY,
    NODE_IN,
    NODE_JUST_ADDED_EDGE,
    NODE_NEUTRAL,
    NODE_OUT,
    PATH_COLOR,
    POPPED_EDGE,
    QUEUE_BORDER,
    QUEUE_FILL,
    QUEUE_NEW_FILL,
    QUEUE_POP_FILL,
    QUEUE_STALE_FILL,
    QUEUE_STALE_TXT,
    REJECTED_EDGE,
    SUBLABEL_TXT,
    TEXT_DARK,
    TEXT_FORMULA,
    TREE_EDGE,
)

# :func:`configure_style` лишається доступною з цього модуля задля зручності
# (приклади імпортують її саме звідси), але визначена в :mod:`prim_mst.style`.

__all__ = [
    "configure_style",
    "format_weight",
    "queue_str",
    "draw_graph",
    "draw_graph_state",
    "draw_queue_panel",
    "draw_prim_step",
    "draw_evolution",
    "draw_mst_result",
    "draw_cut",
    "draw_cable_plans",
    "draw_cable_plan",
    "step_title",
    "step_summary",
    "show_step",
    "print_mst_edges",
]

EdgeList = List[Tuple[Hashable, Hashable, float]]
Positions = Dict[Hashable, Tuple[float, float]]


# ---------------------------------------------------------------------------
# Допоміжні форматувальники
# ---------------------------------------------------------------------------
def format_weight(w: float) -> str:
    """Форматує вагу ребра без зайвих нулів (``7`` замість ``7.0``)."""
    return f"{w:g}"


def _edge_str(edge: QueueEdge) -> str:
    """Запис елемента черги так, як він лежить у купі: ``(вага, звідки, куди)``."""
    w, u, v = edge
    return f"({format_weight(w)}, {u}, {v})"


def queue_str(queue: Sequence[QueueEdge]) -> str:
    """Уся черга одним рядком (у порядку пріоритету) або «— порожня —»."""
    if not queue:
        return t("— порожня —")
    return ", ".join(_edge_str(e) for e in queue)


def _ekey(u: Hashable, v: Hashable) -> FrozenSet:
    """Ключ неорієнтованого ребра: ``{u, v}`` (однаковий для обох напрямків)."""
    return frozenset((u, v))


# ---------------------------------------------------------------------------
# Панель графа (малює на переданій осі — з неї збираються всі композиції)
# ---------------------------------------------------------------------------
def draw_graph_state(
    ax,
    edge_list: EdgeList,
    pos: Positions,
    *,
    visited: Iterable[Hashable] = (),
    tree_edges: Sequence[Tuple[Hashable, Hashable, float]] = (),
    fringe: Sequence[QueueEdge] = (),
    popped: Optional[QueueEdge] = None,
    popped_ok: Optional[bool] = None,
    just_added: Optional[Hashable] = None,
    rejected: Sequence[Tuple[Hashable, Hashable, float]] = (),
    neutral_nodes: bool = False,
    node_size: int = 700,
    weight_fs: float = 10.5,
) -> None:
    """Малює граф у стані одного кроку Прима на осі ``ax``.

    :param visited: вершини, що вже в дереві (зелені).
    :param tree_edges: ребра МОД ``(u, v, вага)`` — зелені товсті.
    :param fringe: ребра, що лежать у черзі (сині пунктирні); очікує кортежі
        черги ``(вага, u, v)``.
    :param popped: ребро, щойно зняте з черги, — головний акцент кадру.
    :param popped_ok: ``True`` — прийнято (суцільне червоне), ``False`` —
        застаріле (червоний пунктир + ✗).
    :param just_added: вершина, додана на цьому кроці (помаранчеве кільце).
    :param rejected: ребра, що не ввійшли у МОД (бліді пунктирні) — для
        підсумкових рисунків.
    :param neutral_nodes: малювати всі вершини нейтральним синім (рисунки
        «просто граф», без стану алгоритму).
    """
    G = build_graph(edge_list)
    visited = set(visited)
    tree_keys = {_ekey(u, v) for u, v, _ in tree_edges}
    fringe_keys = {_ekey(u, v) for _, u, v in fringe}
    rejected_keys = {_ekey(u, v) for u, v, _ in rejected}
    popped_key = _ekey(popped[1], popped[2]) if popped is not None else None

    plain, tree, dashed_fringe, pale = [], [], [], []
    for u, v, _w in edge_list:
        key = _ekey(u, v)
        if key == popped_key:
            continue  # акцентне ребро малюємо окремо, поверх інших
        if key in tree_keys:
            tree.append((u, v))
        elif key in fringe_keys:
            dashed_fringe.append((u, v))
        elif key in rejected_keys:
            pale.append((u, v))
        else:
            plain.append((u, v))

    nx.draw_networkx_edges(G, pos, edgelist=plain, edge_color=NEUTRAL_GRAY,
                           width=1.5, ax=ax)
    nx.draw_networkx_edges(G, pos, edgelist=pale, edge_color=REJECTED_EDGE,
                           width=1.6, style="dashed", ax=ax)
    nx.draw_networkx_edges(G, pos, edgelist=dashed_fringe, edge_color=FRINGE_EDGE,
                           width=2.2, style="dashed", ax=ax)
    nx.draw_networkx_edges(G, pos, edgelist=tree, edge_color=TREE_EDGE,
                           width=3.4, ax=ax)
    if popped is not None:
        _, pu, pv = popped
        if popped_ok:
            nx.draw_networkx_edges(G, pos, edgelist=[(pu, pv)], edge_color=POPPED_EDGE,
                                   width=3.8, ax=ax)
        else:
            nx.draw_networkx_edges(G, pos, edgelist=[(pu, pv)], edge_color=POPPED_EDGE,
                                   width=2.6, style="dashed", ax=ax)
            # ✗ ставимо на 72 % довжини ребра, щоб не накласти на підпис ваги (він на середині)
            mx = pos[pu][0] + 0.72 * (pos[pv][0] - pos[pu][0])
            my = pos[pu][1] + 0.72 * (pos[pv][1] - pos[pu][1])
            ax.text(mx, my, "✗", ha="center", va="center", fontsize=17,
                    color=POPPED_EDGE, fontweight="bold", zorder=6)

    # вершини: у дереві / поза деревом / нейтральні; щойно додана — з кільцем
    if neutral_nodes:
        nx.draw_networkx_nodes(G, pos, node_color=NODE_NEUTRAL, node_size=node_size, ax=ax)
    else:
        in_tree = [n for n in G.nodes() if n in visited and n != just_added]
        out_tree = [n for n in G.nodes() if n not in visited]
        nx.draw_networkx_nodes(G, pos, nodelist=in_tree, node_color=NODE_IN,
                               node_size=node_size, ax=ax)
        nx.draw_networkx_nodes(G, pos, nodelist=out_tree, node_color=NODE_OUT,
                               node_size=node_size, ax=ax)
        if just_added is not None:
            nx.draw_networkx_nodes(G, pos, nodelist=[just_added], node_color=NODE_IN,
                                   node_size=node_size, edgecolors=NODE_JUST_ADDED_EDGE,
                                   linewidths=3.0, ax=ax)
    nx.draw_networkx_labels(G, pos, font_color="white", font_weight="bold", ax=ax)

    # підписи ваг: колір повторює клас ребра
    def _labels(pairs, color, bold=False):
        if not pairs:
            return
        labels = {(u, v): format_weight(G[u][v]["weight"]) for u, v in pairs}
        nx.draw_networkx_edge_labels(
            G, pos, edge_labels=labels, font_size=weight_fs, ax=ax, font_color=color,
            font_weight="bold" if bold else "normal",
            bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85),
        )

    _labels(plain, "#555")
    _labels(pale, MUTED_TXT)
    _labels(dashed_fringe, FRINGE_EDGE)
    _labels(tree, TREE_EDGE, bold=True)
    if popped is not None:
        _labels([(popped[1], popped[2])], POPPED_EDGE, bold=True)

    ax.margins(0.12)
    ax.axis("off")


def draw_graph(
    edge_list: EdgeList,
    pos: Positions,
    *,
    title: Optional[str] = None,
    figsize: Tuple[float, float] = (7, 5),
):
    """Малює нейтральний неорієнтований зважений граф (без стану алгоритму).

    :returns: об'єкт ``Figure``.
    """
    fig, ax = plt.subplots(figsize=figsize)
    draw_graph_state(ax, edge_list, pos, neutral_nodes=True)
    ax.set_title(t("Неорієнтований зважений граф") if title is None else title)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Панель черги з пріоритетами
# ---------------------------------------------------------------------------
def draw_queue_panel(
    ax,
    queue: Sequence[QueueEdge],
    visited: Iterable[Hashable],
    n_nodes: int,
    total: float,
    *,
    popped: Optional[QueueEdge] = None,
    verdict: Optional[str] = None,
    pushed: Sequence[QueueEdge] = (),
    highlight_top: bool = False,
    list_label: Optional[str] = None,
    max_rows: int = 9,
) -> None:
    """Малює стан черги з пріоритетами як вертикальний список на осі ``ax``.

    :param queue: вміст черги у порядку пріоритету (верхній рядок зніметься
        наступним ``heappop``).
    :param popped: ребро, щойно зняте з черги (окремий жовтий слот угорі).
    :param verdict: ``"add"`` (прийнято) або ``"skip"`` (застаріле) — підпис
        вердикту біля знятого ребра.
    :param pushed: ребра, додані на цьому кроці (зелена заливка рядків).
    :param highlight_top: підсвітити верхній рядок черги жовтим (кадр «зараз
        виконається heappop»).
    :param list_label: підпис над списком (типово «у черзі:»).
    :param max_rows: скільки рядків показувати; решта згортається у «… ще N».
    """
    visited = set(visited)
    pushed_set = set(pushed)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_title(t("Черга з пріоритетами"), fontsize=12, pad=22)
    ax.text(0.5, 1.012, t("(вага, звідки, куди)"), ha="center", va="bottom",
            transform=ax.transAxes, fontsize=8.5, color=MUTED_TXT)

    y = 0.965
    # --- слот щойно знятого ребра -----------------------------------------
    if popped is not None:
        ax.text(0.04, y, t("щойно знято (heappop):"), ha="left", va="center",
                fontsize=9, color=HEADER_TXT)
        y -= 0.055
        ax.add_patch(Rectangle((0.04, y - 0.027), 0.92, 0.054, facecolor=QUEUE_POP_FILL,
                               edgecolor=QUEUE_BORDER, linewidth=1, zorder=1))
        ax.text(0.10, y, _edge_str(popped), ha="left", va="center", fontsize=11.5,
                family="monospace", color=TEXT_DARK, zorder=2)
        y -= 0.055
        if verdict == "add":
            ax.text(0.07, y, t("✔ {v} нова → ребро йде в МОД").format(v=popped[2]),
                    ha="left", va="center", fontsize=9.5, color=GREEN_TXT, fontweight="bold")
        elif verdict == "skip":
            ax.text(0.07, y, t("✗ {v} вже в дереві → пропускаємо").format(v=popped[2]),
                    ha="left", va="center", fontsize=9.5, color=PATH_COLOR, fontweight="bold")
        y -= 0.052

    # --- список черги -------------------------------------------------------
    label = list_label if list_label is not None else (
        t("у черзі лишилось:") if popped is not None else t("у черзі:"))
    ax.text(0.04, y, label, ha="left", va="center", fontsize=9, color=HEADER_TXT)
    y -= 0.052

    if not queue:
        ax.text(0.10, y, t("— порожня —"), ha="left", va="center",
                fontsize=10.5, color=MUTED_TXT, style="italic")
        y -= 0.055
    else:
        shown = list(queue[:max_rows - 1]) if len(queue) > max_rows else list(queue)
        for idx, edge in enumerate(shown):
            stale = edge[2] in visited
            fresh = edge in pushed_set
            face = QUEUE_FILL
            if highlight_top and idx == 0:
                face = QUEUE_POP_FILL
            elif fresh:
                face = QUEUE_NEW_FILL
            elif stale:
                face = QUEUE_STALE_FILL
            ax.add_patch(Rectangle((0.04, y - 0.027), 0.92, 0.054, facecolor=face,
                                   edgecolor=QUEUE_BORDER, linewidth=1, zorder=1))
            ax.text(0.10, y, _edge_str(edge), ha="left", va="center", fontsize=11.5,
                    family="monospace", zorder=2,
                    color=QUEUE_STALE_TXT if stale else TEXT_DARK)
            if highlight_top and idx == 0:
                ax.text(0.93, y, t("← heappop зніме це"), ha="right", va="center",
                        fontsize=8, color=HEADER_TXT, style="italic", zorder=2)
            elif stale:
                ax.text(0.93, y, t("ціль уже в дереві"), ha="right", va="center",
                        fontsize=8, color=QUEUE_STALE_TXT, style="italic", zorder=2)
            elif fresh:
                ax.text(0.93, y, t("← нове"), ha="right", va="center",
                        fontsize=8, color=GREEN_TXT, zorder=2)
            y -= 0.062
        if len(queue) > max_rows:
            ax.text(0.10, y, t("… і ще {n}").format(n=len(queue) - len(shown)),
                    ha="left", va="center", fontsize=9.5, color=MUTED_TXT)
            y -= 0.055
        ax.text(0.04, y - 0.005, t("вгорі — найменша вага (зніметься першим)"),
                ha="left", va="center", fontsize=8, color=MUTED_TXT, style="italic")

    # --- підсумковий рядок стану дерева -------------------------------------
    ax.text(0.5, 0.025, t("у дереві: {k}/{n} вершин · вага МОД: {total}").format(
        k=len(visited), n=n_nodes, total=format_weight(total)),
        ha="center", va="center", fontsize=10, color=TEXT_FORMULA,
        transform=ax.transAxes)


# ---------------------------------------------------------------------------
# Головний кадр кроку: [граф | черга]
# ---------------------------------------------------------------------------
def step_title(event: Event) -> str:
    """Типовий заголовок кадру для події журналу."""
    kind = event["kind"]
    if kind == "init":
        return t("Старт: дерево росте з вершини {s}").format(s=event["start"])
    w, u, v = event["edge"]
    if kind == "add":
        return t("Крок {i}: ребро {u}–{v} ({w}) → у МОД").format(
            i=event["step"], u=u, v=v, w=format_weight(w))
    return t("Крок {i}: ребро ({w}, {u}, {v}) застаріле — пропускаємо").format(
        i=event["step"], u=u, v=v, w=format_weight(w))


def draw_prim_step(
    event: Event,
    edge_list: EdgeList,
    pos: Positions,
    n_nodes: int,
    *,
    title: Optional[str] = None,
    figsize: Tuple[float, float] = (11.5, 5.2),
):
    """Головний кадр одного кроку Прима: граф ліворуч, черга праворуч.

    :param event: подія журналу :func:`prim_mst.core.prim_mst_steps`.
    :returns: об'єкт ``Figure``.
    """
    kind = event["kind"]
    fig, (axg, axq) = plt.subplots(
        1, 2, figsize=figsize, gridspec_kw={"width_ratios": [1.55, 1]})

    fringe = [e for e in event["queue"] if e[2] not in event["visited"]]
    draw_graph_state(
        axg, edge_list, pos,
        visited=event["visited"],
        tree_edges=event["mst_edges"],
        fringe=fringe,
        popped=event["edge"],
        popped_ok=(kind == "add"),
        just_added=(event["edge"][2] if kind == "add" else None),
    )

    draw_queue_panel(
        axq, event["queue"], event["visited"], n_nodes, event["total"],
        popped=event["edge"],
        verdict=kind if event["edge"] is not None else None,
        pushed=event["pushed"],
        list_label=(t("у чергу покладено ребра з {s}:").format(s=event["start"])
                    if kind == "init" else None),
    )

    fig.suptitle(step_title(event) if title is None else title, fontsize=13.5)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    return fig


# ---------------------------------------------------------------------------
# Зведена сітка станів
# ---------------------------------------------------------------------------
def draw_evolution(
    events: List[Event],
    edge_list: EdgeList,
    pos: Positions,
    suptitle: str,
    ncols: int = 3,
):
    """Зведена сітка: стан графа після кожної події журналу.

    Деталі черги лишаються кадрам :func:`draw_prim_step`; тут — лише дерево,
    що росте, з коротким підписом під кожною панеллю.

    :returns: об'єкт ``Figure``.
    """
    count = len(events)
    nrows = (count + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(ncols * 3.7, nrows * 3.3))
    axes = axes.flatten() if hasattr(axes, "flatten") else [axes]

    for idx, event in enumerate(events):
        ax = axes[idx]
        kind = event["kind"]
        fringe = [e for e in event["queue"] if e[2] not in event["visited"]]
        draw_graph_state(
            ax, edge_list, pos,
            visited=event["visited"],
            tree_edges=event["mst_edges"],
            fringe=fringe,
            popped=event["edge"],
            popped_ok=(kind == "add"),
            just_added=(event["edge"][2] if kind == "add" else None),
            node_size=420, weight_fs=8.5,
        )
        if kind == "init":
            title = t("Старт: {s}").format(s=event["start"])
            caption = t("у черзі: {q}").format(q=queue_str(event["queue"]))
        elif kind == "add":
            w, u, v = event["edge"]
            title = t("Крок {i}: + {u}–{v} ({w})").format(
                i=event["step"], u=u, v=v, w=format_weight(w))
            caption = t("вага дерева: {total}").format(total=format_weight(event["total"]))
        else:
            w, u, v = event["edge"]
            title = t("Крок {i}: ✗ ({w}, {u}, {v})").format(
                i=event["step"], u=u, v=v, w=format_weight(w))
            caption = t("застаріле — {v} вже в дереві").format(v=v)
        ax.set_title(title, fontsize=10.5)
        ax.text(0.5, -0.02, caption, transform=ax.transAxes, ha="center", va="top",
                fontsize=8.5, color=SUBLABEL_TXT)

    for extra in range(count, len(axes)):
        axes[extra].axis("off")

    fig.suptitle(suptitle, fontsize=14)
    fig.tight_layout(rect=(0, 0, 1, 0.97), h_pad=2.4)
    return fig


# ---------------------------------------------------------------------------
# Підсумковий рисунок: МОД + відкинуті ребра
# ---------------------------------------------------------------------------
def draw_mst_result(
    edge_list: EdgeList,
    mst_edges: Sequence[Tuple[Hashable, Hashable, float]],
    pos: Positions,
    *,
    title: Optional[str] = None,
    figsize: Tuple[float, float] = (7, 5),
):
    """Підсумок: ребра МОД зелені, відкинуті — бліді пунктирні.

    :returns: об'єкт ``Figure``.
    """
    mst_keys = {_ekey(u, v) for u, v, _ in mst_edges}
    rejected = [(u, v, w) for u, v, w in edge_list if _ekey(u, v) not in mst_keys]
    nodes = {n for u, v, _ in edge_list for n in (u, v)}

    fig, ax = plt.subplots(figsize=figsize)
    draw_graph_state(ax, edge_list, pos, visited=nodes, tree_edges=mst_edges,
                     rejected=rejected)
    total = sum(w for _, _, w in mst_edges)
    skipped = sum(w for _, _, w in rejected)
    ax.set_title(t("Мінімальне остовне дерево (вага {total})").format(
        total=format_weight(total)) if title is None else title, fontsize=13)
    ax.text(0.5, -0.02, t("пунктиром — ребра, що не ввійшли до МОД (разом {w})").format(
        w=format_weight(skipped)),
        transform=ax.transAxes, ha="center", va="top", fontsize=9.5, color=SUBLABEL_TXT)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Властивість розрізу (чому жадібний вибір безпечний)
# ---------------------------------------------------------------------------
def draw_cut(
    edge_list: EdgeList,
    pos: Positions,
    S: Iterable[Hashable],
    *,
    tree_edges: Sequence[Tuple[Hashable, Hashable, float]] = (),
    title: Optional[str] = None,
    shade: bool = True,
    legend: bool = True,
    figsize: Tuple[float, float] = (7.6, 5.4),
):
    """Ілюстрація властивості розрізу: ``S`` проти решти вершин.

    Ребра, що перетинають розріз, — сині пунктирні; **найдешевше** з них —
    зелене суцільне (саме його безпечно додати до МОД). Якщо передано
    ``tree_edges``, ребра дерева всередині ``S`` теж зелені (тонші).

    :param shade: підкласти заокруглений фон під вершини ``S`` (вмикайте,
        коли жодна стороння вершина геометрично не потрапляє в цю рамку).
    :returns: об'єкт ``Figure``.
    """
    S = set(S)
    G = build_graph(edge_list)
    crossing = [(u, v, w) for u, v, w in edge_list if (u in S) != (v in S)]
    best = min(crossing, key=lambda e: (e[2], str(e[0]), str(e[1])))
    best_key = _ekey(best[0], best[1])
    crossing_keys = {_ekey(u, v) for u, v, _ in crossing}
    tree_keys = {_ekey(u, v) for u, v, _ in tree_edges}

    fig, ax = plt.subplots(figsize=figsize)

    if shade:
        xs = [pos[n][0] for n in S]
        ys = [pos[n][1] for n in S]
        pad = 0.42
        ax.add_patch(FancyBboxPatch(
            (min(xs) - pad, min(ys) - pad),
            (max(xs) - min(xs)) + 2 * pad, (max(ys) - min(ys)) + 2 * pad,
            boxstyle="round,pad=0.12", facecolor=CUT_FILL, edgecolor=CUT_EDGE,
            linewidth=1.6, linestyle="--", zorder=0))

    plain, cross, tree_in = [], [], []
    for u, v, _w in edge_list:
        key = _ekey(u, v)
        if key == best_key:
            continue
        if key in crossing_keys:
            cross.append((u, v))
        elif key in tree_keys:
            tree_in.append((u, v))
        else:
            plain.append((u, v))

    nx.draw_networkx_edges(G, pos, edgelist=plain, edge_color=NEUTRAL_GRAY, width=1.4, ax=ax)
    nx.draw_networkx_edges(G, pos, edgelist=tree_in, edge_color=TREE_EDGE, width=2.8, ax=ax)
    nx.draw_networkx_edges(G, pos, edgelist=cross, edge_color=FRINGE_EDGE,
                           width=2.4, style="dashed", ax=ax)
    nx.draw_networkx_edges(G, pos, edgelist=[(best[0], best[1])], edge_color=TREE_EDGE,
                           width=4.0, ax=ax)

    in_nodes = [n for n in G.nodes() if n in S]
    out_nodes = [n for n in G.nodes() if n not in S]
    nx.draw_networkx_nodes(G, pos, nodelist=in_nodes, node_color=NODE_IN, node_size=700, ax=ax)
    nx.draw_networkx_nodes(G, pos, nodelist=out_nodes, node_color=NODE_OUT, node_size=700, ax=ax)
    nx.draw_networkx_labels(G, pos, font_color="white", font_weight="bold", ax=ax)

    def _labels(pairs, color, bold=False):
        if not pairs:
            return
        labels = {(u, v): format_weight(G[u][v]["weight"]) for u, v in pairs}
        nx.draw_networkx_edge_labels(
            G, pos, edge_labels=labels, font_size=10.5, ax=ax, font_color=color,
            font_weight="bold" if bold else "normal",
            bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.85))

    _labels(plain, "#555")
    _labels(tree_in, TREE_EDGE)
    _labels(cross, FRINGE_EDGE, bold=True)
    _labels([(best[0], best[1])], TREE_EDGE, bold=True)

    others = ", ".join(_edge_str((w, u, v)) for u, v, w in sorted(
        crossing, key=lambda e: (e[2], str(e[0]), str(e[1]))) if _ekey(u, v) != best_key)
    caption = (t("через розріз: {best} ✓ найдешевше — його і бере Прим").format(
        best=_edge_str((best[2], best[0], best[1])))
        + ("" if not others else t(";  дорожчі: {others}").format(others=others)))
    ax.text(0.5, -0.02, caption, transform=ax.transAxes, ha="center", va="top",
            fontsize=9.5, color=TEXT_FORMULA)

    if legend:
        handles = [
            Patch(facecolor=NODE_IN, label=t("вершини дерева (S)")),
            Patch(facecolor=NODE_OUT, label=t("ще не в дереві")),
            Line2D([], [], color=TREE_EDGE, linewidth=3.2,
                   label=t("найдешевше ребро розрізу")),
            Line2D([], [], color=FRINGE_EDGE, linewidth=2.2, linestyle="--",
                   label=t("інші ребра розрізу")),
        ]
        ax.legend(handles=handles, loc="lower left", fontsize=8.5, frameon=True,
                  framealpha=0.92, borderpad=0.6)

    ax.margins(0.12)
    ax.axis("off")
    ax.set_title(t("Розріз: дерево S проти решти вершин") if title is None else title,
                 fontsize=13)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Аналогія з кабельною мережею (ілюстрації для розділу «Інтуїція»)
# ---------------------------------------------------------------------------
def _cable_panel(ax, edge_list: EdgeList, pos: Positions, chosen, color: str,
                 caption: str, weight_fs: float = 9.5) -> None:
    """Одна панель аналогії: обраний план кабелів кольоровим, решта трас — пунктиром."""
    G = build_graph(edge_list)
    chosen_keys = {_ekey(u, v) for u, v, _ in chosen}
    picked = [(u, v) for u, v, _ in edge_list if _ekey(u, v) in chosen_keys]
    rest = [(u, v) for u, v, _ in edge_list if _ekey(u, v) not in chosen_keys]

    nx.draw_networkx_edges(G, pos, edgelist=rest, edge_color=REJECTED_EDGE,
                           width=1.5, style="dashed", ax=ax)
    nx.draw_networkx_edges(G, pos, edgelist=picked, edge_color=color, width=3.2, ax=ax)
    nx.draw_networkx_nodes(G, pos, node_color=NODE_NEUTRAL, node_size=520, ax=ax)
    nx.draw_networkx_labels(G, pos, font_color="white", font_weight="bold",
                            font_size=10, ax=ax)

    labels_rest = {(u, v): format_weight(G[u][v]["weight"]) for u, v in rest}
    labels_pick = {(u, v): format_weight(G[u][v]["weight"]) for u, v in picked}
    common = dict(font_size=weight_fs, ax=ax,
                  bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.85))
    if labels_rest:
        nx.draw_networkx_edge_labels(G, pos, edge_labels=labels_rest,
                                     font_color=MUTED_TXT, **common)
    if labels_pick:
        nx.draw_networkx_edge_labels(G, pos, edge_labels=labels_pick,
                                     font_color=color, font_weight="bold", **common)

    ax.text(0.5, -0.03, caption, transform=ax.transAxes, ha="center", va="top",
            fontsize=10, color=HEADER_TXT, fontweight="bold")
    ax.margins(0.13)
    ax.axis("off")


def draw_cable_plans(
    edge_list: EdgeList,
    pos: Positions,
    plans: Sequence[Dict[str, object]],
    suptitle: str,
    figsize: Optional[Tuple[float, float]] = None,
):
    """Кілька планів прокладання кабелю поряд (панель на план).

    :param plans: список словників ``{"edges": [...], "color": str,
        "caption": str}`` — які траси обрано, яким кольором і з яким підписом.
    :returns: об'єкт ``Figure``.
    """
    n = len(plans)
    fig, axes = plt.subplots(1, n, figsize=figsize or (4.6 * n, 4.4))
    if n == 1:
        axes = [axes]
    for ax, plan in zip(axes, plans):
        _cable_panel(ax, edge_list, pos, plan["edges"], plan["color"], plan["caption"])
    fig.suptitle(suptitle, fontsize=13.5)
    fig.tight_layout(rect=(0, 0.02, 1, 0.95))
    return fig


def draw_cable_plan(
    edge_list: EdgeList,
    pos: Positions,
    plan: Dict[str, object],
    title: str,
    figsize: Tuple[float, float] = (5.8, 5.0),
):
    """Один план прокладання кабелю як окрема фігура — кадр для GIF-анімації.

    :returns: об'єкт ``Figure``.
    """
    fig, ax = plt.subplots(figsize=figsize)
    _cable_panel(ax, edge_list, pos, plan["edges"], plan["color"], plan["caption"])
    fig.suptitle(title, fontsize=12)
    fig.tight_layout(rect=(0, 0.02, 1, 0.93))
    return fig


# ---------------------------------------------------------------------------
# Текстовий підсумок кроку + кадр
# ---------------------------------------------------------------------------
def step_summary(event: Event, n_nodes: int) -> str:
    """Повертає текстовий підсумок однієї події журналу (що сталося і чому)."""
    bar = "=" * 60
    kind = event["kind"]
    visited_str = ", ".join(sorted(map(str, event["visited"])))

    if kind == "init":
        out = [bar, t("Старт: початкова вершина {s}").format(s=event["start"]), bar]
        out.append(t("Дерево = {{{s}}}. До черги покладено ребра з {s}: {q}").format(
            s=event["start"], q=queue_str(event["queue"])))
        return "\n".join(out)

    w, u, v = event["edge"]
    out = [bar,
           t("Крок {i}: знято з черги ребро ({w}, {u}, {v})").format(
               i=event["step"], w=format_weight(w), u=u, v=v),
           bar]
    if kind == "add":
        out.append(t("{v} ще НЕ в дереві → приймаємо: {v} приєднується ребром {u}–{v} ({w}).").format(
            u=u, v=v, w=format_weight(w)))
        out.append(t("  Дерево: {nodes}   ·   ребер у МОД: {k}/{m}   ·   вага: {total}").format(
            nodes=visited_str, k=len(event["mst_edges"]), m=n_nodes - 1,
            total=format_weight(event["total"])))
        if event["pushed"]:
            out.append(t("  До черги додано ребра з {v}: {q}").format(
                v=v, q=queue_str(event["pushed"])))
        else:
            out.append(t("  Нових ребер немає: усі сусіди {v} вже в дереві.").format(v=v))
    else:
        out.append(t("{v} ВЖЕ в дереві → ребро застаріле («ліниве видалення»), пропускаємо.").format(v=v))
        out.append(t("  Дерево без змін: {nodes}   ·   вага: {total}").format(
            nodes=visited_str, total=format_weight(event["total"])))
    out.append(t("  Черга тепер: {q}").format(q=queue_str(event["queue"])))
    return "\n".join(out)


def show_step(
    event: Event,
    edge_list: EdgeList,
    pos: Positions,
    n_nodes: int,
    save_path: Optional[str] = None,
):
    """Друкує текстовий підсумок події та малює кадр ``[граф | черга]``.

    :param save_path: якщо задано — зберігає кадр у файл.
    :returns: об'єкт ``Figure``.
    """
    print(step_summary(event, n_nodes))
    fig = draw_prim_step(event, edge_list, pos, n_nodes)
    if save_path:
        fig.savefig(save_path, bbox_inches="tight", dpi=FIGURE_DPI)
    return fig


def print_mst_edges(mst) -> None:
    """Друкує ребра МОД так само, як базова реалізація з конспекту."""
    print("Edges in the MST:")
    for edge in mst.edges(data=True):
        print(edge)
