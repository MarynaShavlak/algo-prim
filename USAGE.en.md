# Quick start

[🇺🇦 Українська](USAGE.md)  ·  **🇬🇧 English**

> Part of the documentation of [“Prim's Algorithm: a step-by-step walkthrough”](README.en.md). This page covers installation and running the examples and tests. For the repository layout see [PROJECT_STRUCTURE.en.md](PROJECT_STRUCTURE.en.md).

> **Python ≥ 3.8 required.** The code uses `from __future__ import annotations`, so it runs on 3.8+ (developed and tested on 3.12).

```bash
# 1. Dependencies
pip install -r requirements.txt
# or install the package in development mode:
pip install -e .
# (optional) MP4 videos of the animations without root — ships ffmpeg via imageio-ffmpeg:
pip install -e ".[video]"

# 2. Reproduce all figures and console outputs (in Ukrainian → docs/images/)
python examples/00_cable_analogy.py           # cable-network analogy + the cut property
python examples/01_graph_abcdef.py            # the main graph A–F (step-by-step walkthrough)
python examples/02_lazy_deletion_abcdefg.py   # graph A–G: lazy deletion in action
python examples/03_disconnected.py            # the limitation: a disconnected graph
python examples/04_animations.py              # GIF+MP4 animations (evolution, cut, cables)
python examples/05_code_walkthrough.py        # code ↔ graph ↔ queue panels

# 3. The same in English (→ docs/images/en/) — add the `en` argument:
python examples/01_graph_abcdef.py en
python examples/04_animations.py en
```

Together the six scripts generate **29 static figures** (`.png`), **6 GIF animations** (`.gif`) and **6 MP4 videos** (`.mp4`) in [`docs/images/`](docs/images) and print the console outputs; with the `en` argument the same media in English land in [`docs/images/en/`](docs/images/en). They finish in seconds (the animations take up to a minute). **MP4s** are encoded only when `ffmpeg` is available (system-wide or from `imageio-ffmpeg`); without it the GIFs are still built — the run never fails.

Verify the correctness of the algorithm (the results are cross-checked against the reference implementation in `networkx`):

```bash
python tests/test_core.py     # core correctness (needs networkx only)
python tests/test_smoke.py    # smoke: rendering, GIF and i18n do not crash (matplotlib, pillow)
# or both via pytest (pip install -e ".[dev]"):
pytest
```

The `test_core.py` suite covers the MST-weight match with `networkx.minimum_spanning_tree` (both teaching graphs + a series of random connected graphs), the spanning-tree properties, the internal consistency of the instrumented version's event journal, the lazy/eager agreement, and the behaviour on a disconnected graph (the basic implementation crashes, `prim_msf` builds an honest forest). The `test_smoke.py` suite checks that every drawing function and the GIF builder run without errors, and that **every Cyrillic label has an English translation** (the `missing_translations` audit).

Minimal use as a library:

```python
from prim_mst import build_graph, prim_mst, mst_weight

graph = build_graph([("A", "B", 3), ("B", "C", 1), ("A", "C", 5)])
mst = prim_mst(graph)          # a networkx.Graph with the MST edges
print(mst_weight(mst))         # 4
```
