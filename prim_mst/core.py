"""Реалізації алгоритму Прима (мінімальне остовне дерево, МОД).

Модуль містить три рівні реалізації — від базової «з конспекту» до
навчально-інструментованої:

* :func:`prim_mst` — базова реалізація з лекції: черга з пріоритетами
  ``heapq`` + «ліниве видалення» застарілих ребер. Саме її код розібрано
  в README рядок за рядком.
* :func:`prim_mst_steps` — та сама логіка крок у крок, але повертає ще й
  **журнал подій**: що зняли з черги, прийняли чи пропустили ребро, що
  додалося до черги і який стан дерева/черги після кожного кроку. Саме її
  використовують навчальні візуалізації.
* :func:`prim_mst_eager` — бонусна «жадібна» (eager) версія: для кожної
  вершини поза деревом тримаємо лише НАЙКРАЩЕ відоме ребро (decrease-key),
  тож черга ніколи не містить дублікатів.

Допоміжні утиліти: :func:`build_graph` (граф зі списку ребер),
:func:`mst_weight` (сумарна вага), :func:`prim_msf` (мінімальний остовний
ліс для незв'язних графів).

Алгоритм Прима працює з **неорієнтованим зваженим зв'язним** графом
``networkx.Graph``. На незв'язному графі базова реалізація аварійно
зупиняється (черга порожніє, а вершини лишаються) — це обмеження докладно
розібрано в ``examples/03_disconnected.py`` і README.
"""

from __future__ import annotations

from heapq import heappop, heappush
from typing import Dict, Hashable, List, Optional, Tuple

import networkx as nx

#: Елемент черги з пріоритетами: ``(вага, звідки, куди)``. Кортежі порівнюються
#: лексикографічно — спершу вага, за рівності ваги імена вершин, — тому порядок
#: зняття з черги повністю детермінований.
QueueEdge = Tuple[float, Hashable, Hashable]
#: Один запис журналу подій :func:`prim_mst_steps` (див. докстрінг функції).
Event = Dict[str, object]


def build_graph(edge_list: List[Tuple[Hashable, Hashable, float]]) -> "nx.Graph":
    """Будує неорієнтований зважений граф зі списку ребер ``(u, v, вага)``.

    Зручний місток між «єдиним джерелом правди» прикладів
    (``examples/_graphs.py``) і ``networkx.Graph``, який очікує алгоритм.
    """
    graph = nx.Graph()
    for u, v, weight in edge_list:
        graph.add_edge(u, v, weight=weight)
    return graph


def prim_mst(graph):
    """Базова реалізація алгоритму Прима (ліниве видалення).

    Код навмисно збережено у вигляді «з конспекту» — саме він розібраний у
    README рядок за рядком. Очікує **зв'язний** неорієнтований зважений граф;
    повертає його мінімальне остовне дерево як новий ``networkx.Graph``.

    Складність: :math:`O(E \\log E)` часу (кожне ребро може двічі потрапити
    до черги) та :math:`O(E)` пам'яті на чергу.
    """
    # Створення порожнього МОД
    mst = nx.Graph()

    # Відвідані вершини, починаючи з випадкової початкової вершини
    visited = {list(graph.nodes())[0]}

    # Черга з пріоритетами для ребер, яка ініціалізується ребрами початкової вершини
    edges = []
    for _, v, weight in graph.edges(data='weight', nbunch=visited):
        heappush(edges, (weight, _, v))

    # Поки в МОД не всі вершини
    while visited != set(graph.nodes()):
        # Вибираємо ребро з найменшою вагою, що з'єднує дерево з новою вершиною
        weight, u, v = heappop(edges)
        if v not in visited:
            # Додаємо нову вершину до МОД
            visited.add(v)
            mst.add_edge(u, v, weight=weight)
            # Додаємо всі ребра з нової вершини до черги з пріоритетами
            for _, new_v, new_weight in graph.edges(data='weight', nbunch=[v]):
                if new_v not in visited:
                    heappush(edges, (new_weight, v, new_v))

    return mst


def prim_mst_steps(graph, start: Optional[Hashable] = None) -> Tuple["nx.Graph", List[Event]]:
    """Інструментована версія Прима для покрокового розбору.

    Повторює :func:`prim_mst` **дія в дію** (та сама черга, той самий порядок
    зняття і додавання ребер), але після кожної події кладе у журнал знімок
    стану. Додатково дозволяє явно задати початкову вершину ``start``.

    :returns: кортеж ``(mst, events)``, де ``events`` — список подій:

        * перша подія має ``kind="init"`` — старт алгоритму;
        * далі по одній події на кожне зняте з черги ребро:
          ``kind="add"`` (вершина нова — ребро прийнято до МОД) або
          ``kind="skip"`` (вершина вже в дереві — ребро застаріле).

        Кожна подія — словник із ключами:

        * ``kind`` — ``"init"`` / ``"add"`` / ``"skip"``;
        * ``step`` — номер кроку (``0`` для ``init``);
        * ``start`` — початкова вершина;
        * ``edge`` — зняте з черги ребро ``(вага, u, v)`` (``None`` для ``init``);
        * ``pushed`` — список ребер, щойно доданих до черги;
        * ``visited`` — множина вершин дерева ПІСЛЯ події (копія);
        * ``mst_edges`` — ребра МОД ``(u, v, вага)`` у порядку додавання (копія);
        * ``queue`` — вміст черги ПІСЛЯ події, відсортований за пріоритетом
          (саме в цьому порядку ребра зніматимуться далі);
        * ``total`` — поточна сумарна вага дерева.

    Складність та сама, що й у базовій версії, плюс :math:`O(E \\log E)` на
    знімки черги (їх сортуємо для читомості).
    """
    mst = nx.Graph()
    if start is None:
        start = list(graph.nodes())[0]
    visited = {start}
    mst_edges: List[Tuple[Hashable, Hashable, float]] = []
    total = 0.0

    edges: List[QueueEdge] = []
    pushed: List[QueueEdge] = []
    for _, v, weight in graph.edges(data="weight", nbunch=[start]):
        heappush(edges, (weight, _, v))
        pushed.append((weight, _, v))

    def snapshot(kind: str, step: int, edge: Optional[QueueEdge]) -> Event:
        return {
            "kind": kind,
            "step": step,
            "start": start,
            "edge": edge,
            "pushed": list(pushed),
            "visited": set(visited),
            "mst_edges": list(mst_edges),
            "queue": sorted(edges),
            "total": total,
        }

    events: List[Event] = [snapshot("init", 0, None)]

    step = 0
    while visited != set(graph.nodes()):
        weight, u, v = heappop(edges)
        step += 1
        pushed = []
        if v not in visited:
            visited.add(v)
            mst.add_edge(u, v, weight=weight)
            mst_edges.append((u, v, weight))
            total += weight
            for _, new_v, new_weight in graph.edges(data="weight", nbunch=[v]):
                if new_v not in visited:
                    heappush(edges, (new_weight, v, new_v))
                    pushed.append((new_weight, v, new_v))
            events.append(snapshot("add", step, (weight, u, v)))
        else:
            events.append(snapshot("skip", step, (weight, u, v)))

    return mst, events


def prim_mst_eager(graph, start: Optional[Hashable] = None) -> "nx.Graph":
    """«Жадібна» (eager) версія Прима: черга без дублікатів.

    Замість того, щоб класти в чергу ВСІ ребра й ліниво пропускати застарілі,
    для кожної вершини ``v`` поза деревом тримаємо лише **найкраще** відоме
    ребро ``best[v] = (вага, u)``, яке з'єднує її з деревом, і оновлюємо його,
    коли знаходимо дешевше (semantics decrease-key). Пам'ять — :math:`O(V)`
    замість :math:`O(E)`.

    Ця версія не «вибухає» і на незв'язному графі: коли ``best`` порожніє,
    вона просто повертає дерево компоненти, в якій лежить ``start`` (порівняйте
    з :func:`prim_mst`, який у цьому випадку аварійно зупиняється).
    """
    mst = nx.Graph()
    if graph.number_of_nodes() == 0:
        return mst
    if start is None:
        start = list(graph.nodes())[0]
    mst.add_node(start)
    visited = {start}

    # best[v] = (вага, u): найдешевше відоме ребро, що з'єднує v із деревом
    best: Dict[Hashable, Tuple[float, Hashable]] = {}
    for _, v, weight in graph.edges(data="weight", nbunch=[start]):
        best[v] = (weight, start)

    while best:
        # детермінований вибір: найменша вага, за рівності — менша вершина
        v = min(best, key=lambda x: (best[x][0], str(x)))
        weight, u = best.pop(v)
        visited.add(v)
        mst.add_edge(u, v, weight=weight)
        for _, x, new_weight in graph.edges(data="weight", nbunch=[v]):
            if x not in visited and (x not in best or new_weight < best[x][0]):
                best[x] = (new_weight, v)  # decrease-key: знайшли дешевше ребро до x

    return mst


def prim_msf(graph) -> "nx.Graph":
    """Мінімальний остовний **ліс**: Прим окремо в кожній компоненті зв'язності.

    Остовного **дерева** в незв'язного графа не існує (між компонентами немає
    жодного ребра), але в кожній компоненті своє МОД є. Разом вони утворюють
    мінімальний остовний ліс — саме його повертає ця функція (зокрема й
    ізольовані вершини, як вершини без ребер).
    """
    forest = nx.Graph()
    forest.add_nodes_from(graph.nodes())
    for component in nx.connected_components(graph):
        if len(component) > 1:
            sub = graph.subgraph(component)
            tree, _ = prim_mst_steps(sub, start=min(component, key=str))
            forest.add_edges_from(tree.edges(data=True))
    return forest


def mst_weight(tree) -> float:
    """Сумарна вага ребер дерева (або лісу)."""
    return sum(weight for _, _, weight in tree.edges(data="weight"))
