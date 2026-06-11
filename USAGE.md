# Швидкий старт

**🇺🇦 Українська**  ·  [🇬🇧 English](USAGE.en.md)

> Частина документації проєкту [«Алгоритм Прима: покроковий розбір»](README.md). Тут — команди встановлення, запуску прикладів і тестів. Структуру репозиторію див. у [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md).

> **Потрібен Python ≥ 3.8.** Код використовує `from __future__ import annotations`, тож працює на 3.8+ (розробляється й тестується на 3.12).

```bash
# 1. Залежності
pip install -r requirements.txt
# або встановити пакет у режимі розробки:
pip install -e .
# (опційно) MP4-відео анімацій без root — додає ffmpeg із пакета imageio-ffmpeg:
pip install -e ".[video]"

# 2. Відтворити всі рисунки й текстові виводи (українською → docs/images/)
python examples/00_cable_analogy.py           # аналогія з кабельною мережею + розріз
python examples/01_graph_abcdef.py            # основний граф A–F (покроковий розбір)
python examples/02_lazy_deletion_abcdefg.py   # граф A–G: ліниве видалення в дії
python examples/03_disconnected.py            # обмеження: незв'язний граф
python examples/04_animations.py              # анімації GIF+MP4 (еволюція, розріз, кабелі)
python examples/05_code_walkthrough.py        # панелі «код ↔ граф ↔ черга»

# 3. Те саме англійською (→ docs/images/en/) — додайте аргумент `en`:
python examples/01_graph_abcdef.py en
python examples/04_animations.py en
```

Шість скриптів разом генерують **29 статичних рисунків** (`.png`), **6 GIF-анімацій** (`.gif`) і **6 MP4-відео** (`.mp4`) у [`docs/images/`](docs/images) та друкують текстові виводи в консоль; з аргументом `en` ті самі медіа англійською потрапляють у [`docs/images/en/`](docs/images/en). Виконуються за кілька секунд (анімації — до хвилини). **MP4** кодуються лише за наявності `ffmpeg` (системного або з `imageio-ffmpeg`); без нього збираються самі GIF — збірка не падає.

Перевірити коректність алгоритму (результати звірено з еталонною реалізацією `networkx`):

```bash
python tests/test_core.py     # коректність ядра (потрібен лише networkx)
python tests/test_smoke.py    # smoke: рендер, GIF та i18n не падають (matplotlib, pillow)
# або обидва через pytest (pip install -e ".[dev]"):
pytest
```

Тести `test_core.py` покривають збіг ваги МОД із `networkx.minimum_spanning_tree` (обидва навчальні графи + серія випадкових зв'язних графів), властивості остовного дерева, узгодженість журналу подій інструментованої версії, збіг eager- і lazy-версій та поведінку на незв'язному графі (базова реалізація аварійно зупиняється, `prim_msf` будує чесний ліс). Smoke-тести `test_smoke.py` перевіряють, що всі функції малювання і збірка GIF виконуються без помилок, а **всі кириличні підписи мають англійський переклад** (аудит `missing_translations`).

Мінімальне використання як бібліотеки:

```python
from prim_mst import build_graph, prim_mst, mst_weight

graph = build_graph([("A", "B", 3), ("B", "C", 1), ("A", "C", 5)])
mst = prim_mst(graph)          # networkx.Graph з ребрами МОД
print(mst_weight(mst))         # 4
```
