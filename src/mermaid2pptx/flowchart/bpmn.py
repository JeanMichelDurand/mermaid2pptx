"""Reading a flowchart as a simplified BPMN process (`--render bpmn`)."""
from __future__ import annotations

import re

from .model import Diagram, Edge, Node


_DATA = {"cylinder", "parallelogram", "parallelogram_alt"}     # data store, data object: kept
_USER = re.compile(r"^\s*[\U0001F464\U0001F465]\uFE0F?\s*")    # 👤 👥


def _take_icon(text: str) -> tuple[str, str | None]:
    m = _USER.match(text)
    return (text[m.end():], "user") if m else (text, None)


def to_bpmn(d: Diagram, events: bool = True, lanes: bool = True) -> Diagram:
    """Read the flowchart as a simplified BPMN process (in place, and returned).

    `{decision}` -> exclusive gateway. `((circle))`, `(((double circle)))` and `([stadium])`
    -> events: start without incoming flow, end without outgoing flow (a double circle is
    always an end), intermediate otherwise (a stadium in mid-flow stays a task).
    `[[subroutine]]` -> call activity. Database and parallelogram shapes are kept. Every other
    shape -> task. With `events`, a process with no start (end) event gets one before each
    source (after each sink). A leading 👤 in a text becomes a user icon. With `lanes`, when
    every node sits in one of two or more top-level subgraphs, those are drawn as lanes.
    """
    for n in d.nodes.values():
        n.text, n.icon = _take_icon(n.text)
    for sg in d.subgraphs.values():
        sg.title, sg.icon = _take_icon(sg.title)
    tops = [s for s, sg in d.subgraphs.items() if sg.parent is None]
    if lanes and len(tops) >= 2 and all(d.path(n)[:1] for n in d.nodes):
        d.lanes = tops
    flows = [e for e in d.edges if e.line != "invisible" and e.src != e.dst]
    has_in, has_out = {e.dst for e in flows}, {e.src for e in flows}
    for n in d.nodes.values():
        sh, i, o = n.shape, n.id in has_in, n.id in has_out
        if sh == "diamond":
            n.shape = "gateway"
        elif sh == "doublecircle" or (sh in ("circle", "stadium") and i and not o):
            n.shape = "end"
        elif sh in ("circle", "stadium") and not i:
            n.shape = "start"
        elif sh == "circle":
            n.shape = "intermediate"
        elif sh == "subroutine":
            n.shape = "call"
        elif sh not in _DATA:
            n.shape = "task"
    if not events:
        return d
    kinds = {n.shape for n in d.nodes.values()}
    steps = [n for n in d.nodes.values() if n.shape in ("task", "call", "gateway")]
    sources = [] if "start" in kinds else [n for n in steps if n.id not in has_in and n.id in has_out]
    sinks = [] if "end" in kinds else [n for n in steps if n.id in has_in and n.id not in has_out]

    def fresh(base):
        while base in d.nodes or base in new:
            base += "_"
        return base

    new: dict[str, Node] = {}
    starts, ends, e_in, e_out = {}, {}, [], []
    for n in sources:
        k = fresh(f"start_{n.id}")
        starts[k] = new[k] = Node(k, "", "start", cluster=n.cluster)
        e_in.append(Edge(k, n.id))
    for n in sinks:
        k = fresh(f"end_{n.id}")
        ends[k] = new[k] = Node(k, "", "end", cluster=n.cluster)
        e_out.append(Edge(n.id, k))
    d.nodes = {**d.nodes, **starts, **ends}        # after the author's nodes: same cycle breaking
    d.edges = d.edges + e_in + e_out
    return d
