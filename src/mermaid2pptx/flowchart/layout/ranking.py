"""Phase 1: node and label sizes, then layers (ranks), after breaking the cycles."""
from __future__ import annotations

from dataclasses import dataclass

from ...text import text_width, wrap
from ..model import Diagram
from ..shapes import OUTSIDE, node_size
from .model import ICON_EM, OUTSIDE_GAP, OUTSIDE_WRAP_EM, WRAP_EM


@dataclass
class Measures:
    lines: dict[str, list[str]]             # node text, wrapped
    sizes: dict[str, tuple[float, float]]   # node box (w, h)
    cores: dict[str, float]                 # symbol side of a node whose text sits outside it
    label_lines: list[list[str]]            # per edge
    label_size: list[tuple[float, float]]


@dataclass
class Ranking:
    rank: dict[str, int]
    loops: set[int]          # self-loops (edge indices)
    reversed_: set[int]      # back edges: reversed to break the cycles


def measure(d: Diagram, fs: float) -> Measures:
    lfs = 0.85 * fs                                 # edge-label font
    vertical = d.direction in ("TB", "BT")
    ids = list(d.nodes)
    lines = {n: wrap(d.nodes[n].text, fs, WRAP_EM * fs) for n in ids}
    sizes = {n: node_size(d.nodes[n].shape, lines[n], fs) for n in ids}
    cores: dict[str, float] = {}
    for n in ids:           # symbol + its text on the -cross side, mirrored so the symbol is centred
        if (em := OUTSIDE.get(d.nodes[n].shape)) is None:
            continue
        core = cores[n] = em * fs
        lines[n] = wrap(d.nodes[n].text, fs, OUTSIDE_WRAP_EM * fs) if d.nodes[n].text else []
        tw = max((text_width(ln, fs) + 0.3 * fs for ln in lines[n]), default=0.0)
        th = len(lines[n]) * fs * 1.2
        gap = OUTSIDE_GAP * fs if lines[n] else 0.0
        sizes[n] = (core + 2 * (tw + gap), max(core, th)) if vertical else (max(core, tw), core + 2 * (th + gap))
    for n in ids:           # a user icon in the top-left corner: widen both sides, text stays centred
        if d.nodes[n].icon and n not in cores:
            w, h = sizes[n]
            sizes[n] = (w + 2 * (ICON_EM + 0.3) * fs, max(h, (ICON_EM + 0.8) * fs))
    label_lines = [wrap(e.text, lfs, 0.8 * WRAP_EM * fs) if e.text else [] for e in d.edges]
    label_size = [(max(text_width(ln, lfs) for ln in ll) + 0.5 * lfs, len(ll) * lfs * 1.2 + 0.3 * lfs)
                  if ll else (0.0, 0.0) for ll in label_lines]
    return Measures(lines, sizes, cores, label_lines, label_size)


def rank_nodes(d: Diagram) -> Ranking:
    """Longest-path ranks, sources pulled down to their children. A depth-first search in
    declaration order reverses the edges that close a cycle: the one written last."""
    ids = list(d.nodes)
    edges = d.edges
    loops = {i for i, e in enumerate(edges) if e.src == e.dst}
    out_adj: dict[str, list[int]] = {n: [] for n in ids}
    for i, e in enumerate(edges):
        if i not in loops:
            out_adj[e.src].append(i)
    reversed_: set[int] = set()
    state: dict[str, int] = {}
    for root in ids:
        if root in state:
            continue
        state[root] = 1
        stack = [(root, iter(out_adj[root]))]
        while stack:
            n, it = stack[-1]
            for i in it:
                v = edges[i].dst
                if state.get(v) == 1:
                    reversed_.add(i)
                elif v not in state:
                    state[v] = 1
                    stack.append((v, iter(out_adj[v])))
                    break
            else:
                state[n] = 2
                stack.pop()

    def minlen(i):          # a labelled edge spans two ranks: its label gets a slot of its own
        e = edges[i]
        return max(e.minlen, 2) if e.text and i not in reversed_ else e.minlen

    succ: dict[str, list[tuple[str, int]]] = {n: [] for n in ids}
    pred: dict[str, list[tuple[str, int]]] = {n: [] for n in ids}
    for i, e in enumerate(edges):
        if i in loops:
            continue
        u, v = (e.dst, e.src) if i in reversed_ else (e.src, e.dst)
        succ[u].append((v, minlen(i)))
        pred[v].append((u, minlen(i)))
    remaining = {n: len(pred[n]) for n in ids}
    topo = [n for n in ids if not remaining[n]]
    for n in topo:
        for v, _ in succ[n]:
            remaining[v] -= 1
            if not remaining[v]:
                topo.append(v)
    rank = {n: 0 for n in ids}
    for n in topo:
        for v, ml in succ[n]:
            rank[v] = max(rank[v], rank[n] + ml)
    for n in reversed(topo):
        if not pred[n] and succ[n]:
            rank[n] = min(rank[v] - ml for v, ml in succ[n])
    low = min(rank.values(), default=0)
    return Ranking({n: r - low for n, r in rank.items()}, loops, reversed_)
