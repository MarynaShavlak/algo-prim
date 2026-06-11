# -*- coding: utf-8 -*-
"""Двомовні підписи для візуалізацій (uk за замовчуванням / en).

Замість важкої інфраструктури ``gettext``/``.po`` тут застосовано прийом
**«вихідний рядок — це і є ключ»**: ключем у словнику перекладів виступає сам
український рядок. Наслідки:

* **Мова за замовчуванням лишається байт-у-байт незмінною.** Коли ``LANG == "uk"``,
  :func:`t` повертає аргумент *без жодного пошуку* — український вивід (і всі
  раніше згенеровані рисунки) ідентичні тим, що були б і без i18n узагалі.
* **Відсутній переклад «деградує» безпечно** до вихідного рядка (``_EN.get(s, s)``):
  забули перекласти — отримаєте український підпис, а не ``KeyError`` чи ``"???"``.
* **Нуль інфраструктури** — один Python-файл, жодних білд-кроків.

Оркестратор (скрипти ``examples/``) перемикає мову через :func:`set_lang`
(``"en"`` із аргументів CLI) і кладе рисунки в ``docs/images/en/``. Той самий код
малювання, той самий білдер — змінюється лише глобальний ``LANG``, і всі виклики
:func:`t` всередині повертають переклад. Жодна функція-фігура не знає про мову.

Правила вживання у коді фігур:

* обгортайте **шаблон**, а не результат: ``t("…{x}…").format(x=v)``, ніколи
  ``t(f"…{v}…")`` — інакше ключ щоразу інакший і переклад не знайдеться;
* ключ у :data:`_EN` має збігатися з рядком у коді **символ-у-символ**, включно з
  пробілами, переносами ``\\n``, тире (``–`` en-dash ≠ ``-`` дефіс), стрілками
  (``→``) та позначками ``✓``/``✗``;
* суто формульні/символьні рядки (без жодного українського слова — напр.
  ``"(2, C, F)"``) у словник НЕ заносимо: :func:`t` поверне їх незмінними, а
  виглядають вони однаково обома мовами.
"""

from __future__ import annotations

import re
from typing import Dict, Set

#: Мова за замовчуванням (= вихідна мова рядків-ключів у коді).
LANG = "uk"

#: Будь-яка кирилична літера — ознака «це український рядок, а не формула/символи».
_CYRILLIC = re.compile(r"[Ѐ-ӿ]")

#: Аудит повноти перекладу: рядки з кирилицею, які в режимі ``en`` НЕ знайшлися в
#: :data:`_EN` (тобто лишилися б українськими). Наповнюється на льоту в :func:`t`;
#: має бути порожнім після повного прогону ``en`` — це й перевіряють тести/збірка.
missing_translations: Set[str] = set()


def set_lang(lang: str) -> None:
    """Встановити мову підписів: ``"uk"`` (типово) або ``"en"``."""
    global LANG
    assert lang in ("uk", "en"), lang
    LANG = lang


def get_lang() -> str:
    """Повернути поточну мову підписів (``"uk"`` або ``"en"``)."""
    return LANG


def t(s: str) -> str:
    """Повернути підпис мовою :data:`LANG` (ключ — вихідний український рядок).

    Для ``LANG == "uk"`` повертає ``s`` без змін (нульовий ризик регресій); для
    ``"en"`` — переклад із :data:`_EN`, а якщо його немає — безпечно сам ``s``.
    Якщо в режимі ``en`` рядок містить кирилицю, але перекладу немає, він
    запам'ятовується в :data:`missing_translations` (мовчазний аудит — не падаємо,
    лише фіксуємо «забутий» ключ).
    """
    if LANG == "uk":
        return s                # мова за замовчуванням: жодного пошуку, байт-у-байт
    out = _EN.get(s)
    if out is None:
        if _CYRILLIC.search(s):
            missing_translations.add(s)   # забутий/неточний ключ — фіксуємо для аудиту
        return s                # відсутній ключ -> безпечно повертаємо вихідний рядок
    return out


# ---------------------------------------------------------------------------
# Словник перекладів (uk -> en).
#
# Згруповано за місцем появи. Шаблони з {плейсхолдерами} перекладені цілком — у
# коді їх викликають як t(шаблон).format(...). НЕ перейменовуйте плейсхолдери:
# їхні імена мусять збігатися з тими, що у виклику .format().
# ---------------------------------------------------------------------------
_EN: Dict[str, str] = {
    # --- visualization.draw_graph (типовий заголовок графа) -------------------
    "Неорієнтований зважений граф": "Undirected weighted graph",

    # --- visualization.draw_queue_panel (панель черги з пріоритетами) ---------
    "Черга з пріоритетами": "Priority queue",
    "(вага, звідки, куди)": "(weight, from, to)",
    "щойно знято (heappop):": "just popped (heappop):",
    "✔ {v} нова → ребро йде в МОД": "✔ {v} is new → the edge joins the MST",
    "✗ {v} вже в дереві → пропускаємо": "✗ {v} already in the tree → skipped",
    "у черзі лишилось:": "left in the queue:",
    "у черзі:": "in the queue:",
    "у чергу покладено ребра з {s}:": "edges of {s} pushed to the queue:",
    "— порожня —": "— empty —",
    "← heappop зніме це": "← heappop takes this",
    "ціль уже в дереві": "target already in tree",
    "← нове": "← new",
    "… і ще {n}": "… and {n} more",
    "вгорі — найменша вага (зніметься першим)":
        "smallest weight on top (popped first)",
    "у дереві: {k}/{n} вершин · вага МОД: {total}":
        "in the tree: {k}/{n} vertices · MST weight: {total}",

    # --- visualization.step_title (заголовки кадру кроку) ---------------------
    "Старт: дерево росте з вершини {s}": "Start: the tree grows from vertex {s}",
    "Крок {i}: ребро {u}–{v} ({w}) → у МОД":
        "Step {i}: edge {u}–{v} ({w}) → into the MST",
    "Крок {i}: ребро ({w}, {u}, {v}) застаріле — пропускаємо":
        "Step {i}: edge ({w}, {u}, {v}) is stale — skipped",

    # --- visualization.draw_evolution ------------------------------------------
    "Старт: {s}": "Start: {s}",
    "у черзі: {q}": "in the queue: {q}",
    "Крок {i}: + {u}–{v} ({w})": "Step {i}: + {u}–{v} ({w})",
    "вага дерева: {total}": "tree weight: {total}",
    "Крок {i}: ✗ ({w}, {u}, {v})": "Step {i}: ✗ ({w}, {u}, {v})",
    "застаріле — {v} вже в дереві": "stale — {v} already in the tree",

    # --- visualization.draw_mst_result ------------------------------------------
    "Мінімальне остовне дерево (вага {total})":
        "Minimum spanning tree (weight {total})",
    "пунктиром — ребра, що не ввійшли до МОД (разом {w})":
        "dashed — edges left out of the MST (total {w})",

    # --- visualization.draw_cut (властивість розрізу) ---------------------------
    "Розріз: дерево S проти решти вершин":
        "The cut: tree S vs. the remaining vertices",
    "через розріз: {best} ✓ найдешевше — його і бере Прим":
        "across the cut: {best} ✓ the cheapest — exactly what Prim takes",
    ";  дорожчі: {others}": ";  pricier: {others}",
    "вершини дерева (S)": "tree vertices (S)",
    "ще не в дереві": "not in the tree yet",
    "найдешевше ребро розрізу": "cheapest edge of the cut",
    "інші ребра розрізу": "other edges of the cut",

    # --- visualization.step_summary (текстовий підсумок кроку) ------------------
    "Старт: початкова вершина {s}": "Start: initial vertex {s}",
    "Дерево = {{{s}}}. До черги покладено ребра з {s}: {q}":
        "Tree = {{{s}}}. Edges of {s} pushed to the queue: {q}",
    "Крок {i}: знято з черги ребро ({w}, {u}, {v})":
        "Step {i}: popped edge ({w}, {u}, {v}) from the queue",
    "{v} ще НЕ в дереві → приймаємо: {v} приєднується ребром {u}–{v} ({w}).":
        "{v} is NOT in the tree yet → accept: {v} joins via edge {u}–{v} ({w}).",
    "  Дерево: {nodes}   ·   ребер у МОД: {k}/{m}   ·   вага: {total}":
        "  Tree: {nodes}   ·   MST edges: {k}/{m}   ·   weight: {total}",
    "  До черги додано ребра з {v}: {q}":
        "  Edges of {v} pushed to the queue: {q}",
    "  Нових ребер немає: усі сусіди {v} вже в дереві.":
        "  No new edges: every neighbour of {v} is already in the tree.",
    "{v} ВЖЕ в дереві → ребро застаріле («ліниве видалення»), пропускаємо.":
        "{v} is ALREADY in the tree → the edge is stale (“lazy deletion”), skipped.",
    "  Дерево без змін: {nodes}   ·   вага: {total}":
        "  Tree unchanged: {nodes}   ·   weight: {total}",
    "  Черга тепер: {q}": "  Queue now: {q}",

    # --- walkthrough.py: кириличні рядки кодової панелі (CODE) ------------------
    "edges = []                      # купа":
        "edges = []                      # heap",
    "    # else: ребро застаріле — пропускаємо":
        "    # else: stale edge — skip it",

    # --- walkthrough.py: заголовки/підписи знімків ------------------------------
    "дерево = {{{s}}}; у черзі — ребра з {s}":
        "tree = {{{s}}}; the queue holds the edges of {s}",
    "Крок {i}: heappop": "Step {i}: heappop",
    "heappop → {edge}: чи є {v} у visited?":
        "heappop → {edge}: is {v} in visited?",
    "{edge}: {v} ще немає у visited → ребро прийнято в МОД ✔":
        "{edge}: {v} not in visited yet → edge accepted into the MST ✔",
    "Крок {i}: пропуск": "Step {i}: skip",
    "{edge}: {v} уже у visited → ребро застаріле, пропуск ✗":
        "{edge}: {v} already in visited → stale edge, skipped ✗",
    "Готово: вага {total}": "Done: weight {total}",
    "усі вершини в дереві → умова while хибна; вага МОД = {total}":
        "all vertices in the tree → the while condition is false; MST weight = {total}",
    "у черзі лишилось (уже не знадобиться):":
        "left in the queue (never needed):",
    # легенда підсвічування коду
    "активний рядок": "active line",
    "прийнято (ребро в МОД)": "accepted (edge into the MST)",
    "пропуск (застаріле ребро)": "skip (stale edge)",

    # --- _common.report_mst (підсумок у консоль) --------------------------------
    "Вага МОД: {total}   (ребер: {k} із {m} можливих)":
        "MST weight: {total}   (edges: {k} of {m} possible)",
    "Не ввійшли до МОД: {edges}": "Left out of the MST: {edges}",
    "\nРисунки збережено у: {path}": "\nFigures saved to: {path}",

    # --- examples/_graphs.cable_plans -------------------------------------------
    "прокласти всі 6 трас: 18 — цикли, зайві витрати":
        "lay all 6 routes: 18 — cycles, wasted money",
    "дерево (без циклів), але не найдешевше: 15":
        "a tree (no cycles), but not the cheapest one: 15",
    "мінімальне остовне дерево: 11 ✓": "the minimum spanning tree: 11 ✓",

    # --- examples/00_cable_analogy ------------------------------------------------
    "Міста та можливі траси кабелю (вартість прокладання)":
        "Cities and possible cable routes (cost to lay)",
    "Як з'єднати всі міста найдешевше?":
        "What is the cheapest way to connect all the cities?",
    "Збережено 3 рисунки: аналогія з кабельною мережею + властивість розрізу.":
        "Saved 3 figures: the cable-network analogy + the cut property.",

    # --- examples/01_graph_abcdef ---------------------------------------------
    "Готово: журнал містить {n} подій (старт + по одній на кожне зняте ребро).":
        "Done: the journal holds {n} events (start + one per popped edge).",
    "Еволюція МОД: дерево росте ребро за ребром (граф A–F)":
        "MST evolution: the tree grows edge by edge (graph A–F)",
    "Звірка: базова реалізація і networkx дають ту саму вагу МОД ({total}) ✓":
        "Cross-check: the basic implementation and networkx agree on the MST weight ({total}) ✓",

    # --- examples/02_lazy_deletion_abcdefg -------------------------------------
    "Готово: {n} подій, із них {k} — застарілі ребра (ліниве видалення).":
        "Done: {n} events, {k} of them are stale edges (lazy deletion).",
    "Еволюція МОД на графі A–G: три застарілі ребра поспіль":
        "MST evolution on graph A–G: three stale edges in a row",

    # --- examples/03_disconnected -----------------------------------------------
    "Незв'язний граф: два «острови»": "A disconnected graph: two “islands”",
    "Чи зв'язний граф? nx.is_connected → {flag}":
        "Is the graph connected? nx.is_connected → {flag}",
    "Компоненти зв'язності: {comps}": "Connected components: {comps}",
    "Запускаємо базову реалізацію prim_mst на незв'язному графі…":
        "Running the basic prim_mst on a disconnected graph…",
    "  (несподівано: помилки не сталося)": "  (unexpectedly, no error occurred)",
    "  💥 IndexError: heappop із порожньої черги.":
        "  💥 IndexError: heappop from an empty queue.",
    "  Дерево охопило компоненту старту, а вершини {missing} недосяжні —":
        "  The tree covered the start component, while vertices {missing} are unreachable —",
    "  умова `visited != set(graph.nodes())` ніколи не стане хибною.":
        "  so the condition `visited != set(graph.nodes())` never becomes false.",
    "prim_mst_eager(start=M) повертає дерево лише компоненти {{M, N, O}}: вага {w}.":
        "prim_mst_eager(start=M) returns the tree of component {{M, N, O}} only: weight {w}.",
    "Це НЕ остовне дерево всього графа — частину вершин втрачено мовчки!":
        "This is NOT a spanning tree of the whole graph — some vertices were silently lost!",
    "Мінімальний остовний ліс (prim_msf): {k} ребра, вага {w}.":
        "Minimum spanning forest (prim_msf): {k} edges, weight {w}.",
    "Мінімальний остовний ліс (вага {w})": "Minimum spanning forest (weight {w})",

    # --- examples/04_animations -----------------------------------------------
    "Генерую GIF-анімації…": "Generating GIF animations…",
    "  {name}: {n} кадрів": "  {name}: {n} frames",
    "Крок {i}: найдешевше ребро через розріз → у МОД":
        "Step {i}: the cheapest edge across the cut → into the MST",

    # --- examples/05_code_walkthrough ------------------------------------------
    "Генерую покрокові панелі «код ↔ граф ↔ черга»…":
        "Generating step-by-step code ↔ graph ↔ queue panels…",
    "Код ↔ граф ↔ черга: по одному рядку на кожне зняте ребро":
        "Code ↔ graph ↔ queue: one row per popped edge",
    "  {name}: сітка, {n} рядків": "  {name}: grid, {n} rows",
    "  {name}: анімація, {n} кадрів": "  {name}: animation, {n} frames",

    # --- animation.save_animation (діагностика MP4, рідкісні шляхи) ------------
    "  ({name} пропущено — ffmpeg недоступний; pip install imageio-ffmpeg для відео)":
        "  ({name} skipped — ffmpeg unavailable; pip install imageio-ffmpeg for video)",
    "  ({name} пропущено: {err})": "  ({name} skipped: {err})",
}
