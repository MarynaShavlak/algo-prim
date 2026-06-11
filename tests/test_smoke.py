"""Smoke-тести: візуалізація, збірка GIF та i18n виконуються без помилок.

На відміну від ``test_core.py`` (який перевіряє ЧИСЛА), ці тести не звіряють
«правильність картинки» — лише що кожна функція малювання повертає фігуру й не
кидає винятків, що ``save_gif`` збирає валідний GIF, що панелі «код ↔ граф»
будуються, а ВСІ кириличні підписи пакета мають англійський переклад
(аудит ``missing_translations``).

Потребують ``matplotlib``, ``networkx`` і ``pillow``.

Запуск::

    pytest
    python tests/test_smoke.py    # вбудований раннер, без pytest
"""

from __future__ import annotations

import io
import os
import sys
import tempfile
from contextlib import redirect_stdout

import matplotlib

matplotlib.use("Agg")  # без графічного дисплея — ДО імпорту pyplot

import matplotlib.pyplot as plt  # noqa: E402

# корінь репозиторію та examples/ у sys.path
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (_ROOT, os.path.join(_ROOT, "examples")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from prim_mst.animation import save_animation, save_gif  # noqa: E402
from prim_mst.core import build_graph, prim_mst_steps  # noqa: E402
from prim_mst.i18n import missing_translations, set_lang  # noqa: E402
from prim_mst.visualization import (  # noqa: E402
    configure_style,
    draw_cable_plans,
    draw_cut,
    draw_evolution,
    draw_graph,
    draw_mst_result,
    draw_prim_step,
    draw_queue_panel,
    queue_str,
    step_summary,
    step_title,
)

# Маленький граф із гарантованим застарілим ребром: B–C (3) знімається, коли
# C вже приєднано через A–C (2), — достатній для перевірки всіх гілок рендера.
_EDGES = [("A", "B", 1), ("A", "C", 2), ("B", "C", 3), ("C", "D", 4)]
_POS = {"A": (0.0, 1.0), "B": (1.2, 1.8), "C": (1.4, 0.2), "D": (2.6, 1.0)}
_N = 4


def _events():
    _, events = prim_mst_steps(build_graph(_EDGES), start="A")
    return events


def test_draw_functions_return_figures():
    """Кожна функція малювання відпрацьовує без винятків і дає фігуру."""
    configure_style()
    events = _events()
    kinds = [e["kind"] for e in events]
    assert "skip" in kinds, "приклад мусить містити застаріле ребро"

    figures = [
        draw_graph(_EDGES, _POS, title="t"),
        draw_evolution(events, _EDGES, _POS, "t", ncols=3),
        draw_mst_result(_EDGES, events[-1]["mst_edges"], _POS),
        draw_cut(_EDGES, _POS, {"A", "B"}, tree_edges=[("A", "B", 1)]),
        draw_cable_plans(_EDGES, _POS, [
            {"edges": list(_EDGES), "color": "#9E9E9E", "caption": "t"},
            {"edges": [("A", "B", 1)], "color": "#2E7D32", "caption": "t"},
        ], "t"),
    ]
    figures.extend(draw_prim_step(e, _EDGES, _POS, _N) for e in events)
    for fig in figures:
        assert fig is not None
        plt.close(fig)


def test_queue_panel_edge_cases():
    """Панель черги: порожня черга, верхній рядок у фокусі, згортання довгого хвоста."""
    fig, ax = plt.subplots()
    draw_queue_panel(ax, [], {"A"}, _N, 0)                      # порожня
    plt.close(fig)

    fig, ax = plt.subplots()
    long_queue = [(w, "A", f"v{w}") for w in range(1, 13)]      # 12 > max_rows
    draw_queue_panel(ax, long_queue, {"A"}, 13, 0, highlight_top=True)
    plt.close(fig)

    assert queue_str([]) != ""                                   # «— порожня —»


def test_save_gif_creates_valid_gif():
    """save_gif збирає багатокадровий GIF із кількох фігур."""
    from PIL import Image

    frames = []
    for i in range(3):
        fig, ax = plt.subplots(figsize=(2, 2))
        ax.plot([0, 1], [0, i + 1])   # кадри РІЗНІ, інакше GIF злив би їх в один
        ax.set_title(str(i))
        frames.append(fig)

    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "smoke.gif")
        save_gif(frames, out, [200, 200, 200])
        assert os.path.exists(out)
        with Image.open(out) as im:
            assert im.n_frames == 3
            assert im.info.get("loop") == 0


def test_save_gif_rejects_empty():
    """Порожній список кадрів має давати зрозумілий ValueError, а не падати глибше."""
    with tempfile.TemporaryDirectory() as d:
        raised = False
        try:
            save_gif([], os.path.join(d, "x.gif"), 100)
        except ValueError:
            raised = True
        assert raised, "save_gif мав кинути ValueError на порожньому списку"


def test_save_animation_writes_gif_and_maybe_mp4():
    """save_animation: GIF збирається ЗАВЖДИ; MP4 — лише якщо доступний ffmpeg."""
    from PIL import Image

    frames = []
    for i in range(3):
        fig, ax = plt.subplots(figsize=(2.5, 2))   # непарні пікселі — перевірка парного паддингу MP4
        ax.plot([0, 1], [0, i + 1])                # кадри різні, інакше відео «злило» б їх
        ax.set_title(str(i))
        frames.append(fig)

    with tempfile.TemporaryDirectory() as d:
        gif = os.path.join(d, "anim.gif")
        mp4 = os.path.join(d, "anim.mp4")
        result = save_animation(frames, gif, [200, 200, 200], mp4_path=mp4)

        assert os.path.exists(gif)                  # GIF — гарантований формат
        with Image.open(gif) as im:
            assert im.n_frames == 3
        # MP4 — best-effort: якщо ffmpeg є, save_animation повертає шлях і файл існує;
        # якщо немає — повертає None і GIF усе одно зібрано (білд не падає).
        if result is not None:
            assert result == mp4
            assert os.path.exists(mp4) and os.path.getsize(mp4) > 0


def test_walkthrough_builds_and_renders():
    """walkthrough «код ↔ граф ↔ черга»: журнал будується, обидва рівні рендеряться.

    ``build_steps`` містить внутрішній ``assert`` (журнал відповідає подіям
    алгоритму), тож цей тест заодно перевіряє і його.
    """
    from prim_mst.walkthrough import (  # noqa: E402
        build_steps,
        draw_code_walkthrough_grid,
        pick_illustrative,
        render_code_step,
    )

    steps = build_steps(_EDGES, start="A")
    kinds = {s["kind"] for s in steps}
    assert {"init", "test", "add", "skip", "final"} <= kinds
    assert any(s["hl"] for s in steps)          # десь є підсвічування рядків коду

    shown = pick_illustrative(steps)
    assert len(shown) < len(steps)              # кадри heappop у сітку не входять
    grid = draw_code_walkthrough_grid(shown, _EDGES, _POS, _N, "t")
    assert grid is not None
    plt.close(grid)
    frame = render_code_step(steps[1], _EDGES, _POS, _N)
    assert frame is not None
    plt.close(frame)


def test_step_summary_texts():
    """Текстові підсумки містять ключові пояснення для кожного типу події."""
    events = _events()
    init_txt = step_summary(events[0], _N)
    assert "Старт" in init_txt
    add_txt = step_summary(next(e for e in events if e["kind"] == "add"), _N)
    assert "приймаємо" in add_txt
    skip_txt = step_summary(next(e for e in events if e["kind"] == "skip"), _N)
    assert "застаріле" in skip_txt
    for e in events:
        assert step_title(e)


def test_report_mst_prints_base_format():
    """report_mst друкує ребра у форматі базової реалізації + вагу й відкинуті ребра."""
    from _common import GraphExample, report_mst  # noqa: E402
    from prim_mst.core import prim_mst  # noqa: E402

    example = GraphExample(edges=list(_EDGES), positions=dict(_POS))
    mst = prim_mst(build_graph(_EDGES))
    buf = io.StringIO()
    with redirect_stdout(buf):
        report_mst(mst, example)
    out = buf.getvalue()
    assert "Edges in the MST:" in out
    assert "Вага МОД" in out
    assert "B–C" in out                          # відкинуте ребро названо явно


def test_english_labels_complete():
    """Аудит i18n: ПОВНИЙ рендер у режимі en не лишає неперекладених підписів.

    Прогін на графі A–G покриває всі гілки підписів (нові/застарілі ребра,
    згортання черги, розріз, кабельні плани, панелі коду). Якщо якийсь
    кириличний рядок не знайшов перекладу, він опиниться в
    ``missing_translations`` — і тест назве його поіменно.
    """
    from _graphs import ABCDEFG, cable_plans  # noqa: E402
    from prim_mst.walkthrough import build_steps, render_code_step  # noqa: E402

    edges, pos, n = ABCDEFG.edges, ABCDEFG.positions, ABCDEFG.n
    set_lang("en")
    missing_translations.clear()
    try:
        _, events = prim_mst_steps(build_graph(edges), start="A")
        for e in events:
            step_summary(e, n)
            step_title(e)
            plt.close(draw_prim_step(e, edges, pos, n))
        plt.close(draw_evolution(events, edges, pos, "t"))
        plt.close(draw_mst_result(edges, events[-1]["mst_edges"], pos))
        plt.close(draw_cut(edges, pos, events[2]["visited"],
                           tree_edges=events[2]["mst_edges"], shade=False))
        plt.close(draw_cable_plans(ABCDEFG.edges, pos, cable_plans()[:1], "t"))
        plt.close(draw_graph(edges, pos))
        queue_str([])
        fig, ax = plt.subplots()
        draw_queue_panel(ax, [(w, "A", f"v{w}") for w in range(1, 13)],
                         {"A"}, 13, 0, highlight_top=True)
        plt.close(fig)
        for s in build_steps(edges, start="A"):
            plt.close(render_code_step(s, edges, pos, n))
        assert not missing_translations, \
            f"бракує перекладів: {sorted(missing_translations)}"
    finally:
        set_lang("uk")
        missing_translations.clear()


def _run_without_pytest():
    """Мінімальний раннер; на відміну від ядра, ловить БУДЬ-ЯКИЙ виняток."""
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failures = 0
    for test in tests:
        try:
            test()
            print(f"PASS  {test.__name__}")
        except Exception as exc:  # noqa: BLE001 — smoke: будь-яка помилка = провал
            failures += 1
            print(f"FAIL  {test.__name__}: {type(exc).__name__}: {exc}")
    print(f"\n{len(tests) - failures}/{len(tests)} smoke-тестів пройдено")
    return failures


if __name__ == "__main__":
    sys.exit(1 if _run_without_pytest() else 0)
