"""The layout's result (Layout, Route), its working node (LNode), spacing and small numeric helpers."""
from __future__ import annotations

from dataclasses import dataclass, field

from ...geometry import Box
from ..model import Edge


@dataclass
class Route:
    edge: Edge
    points: list[tuple[float, float]]   # screen points, orthogonal polyline
    src_site: int | None                # PowerPoint connection-site index, None = not glued
    dst_site: int | None
    label: Box | None = None
    label_lines: list[str] = field(default_factory=list)


@dataclass
class Layout:
    boxes: dict[str, Box]
    lines: dict[str, list[str]]
    routes: list[Route]
    clusters: list[tuple[str, Box, list[str]]]   # outermost first
    width: float
    height: float
    font_size: float
    lanes: list[tuple[str, Box, Box, list[str]]] = field(default_factory=list)   # id, body, header, title


@dataclass
class LNode:
    key: object          # node id, or ("d", edge index, k) for a dummy
    rs: float            # extent along the rank axis
    cs: float            # extent along the cross axis
    real: bool
    path: tuple
    rank: int
    label: bool = False
    c: float = 0.0


# spacing, in em of the font size
NODESEP, RANKSEP, DUMMYSEP, TRACK, PAD, BACKSEP, LOOP, WRAP_EM = 2.4, 2.9, 0.9, 0.6, 0.9, 1.2, 1.0, 14
OUTSIDE_WRAP_EM, OUTSIDE_GAP, ICON_EM = 9, 0.4, 0.9
OUT = {"TB": "b", "BT": "t", "LR": "r", "RL": "l"}
IN = {"TB": "t", "BT": "b", "LR": "l", "RL": "r"}
SIDE = {"TB": "r", "BT": "r", "LR": "b", "RL": "b"}          # the +cross side
SIDE_NEG = {"TB": "l", "BT": "l", "LR": "t", "RL": "t"}


def median(vals: list[float]) -> float:
    v = sorted(vals)
    n = len(v)
    return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2


def pav(targets: list[float], weights: list[float]) -> list[float]:
    """Weighted isotonic regression (pool adjacent violators): closest non-decreasing fit."""
    blocks: list[list[float]] = []
    for t, w in zip(targets, weights):
        blocks.append([t, w, 1])
        while len(blocks) > 1 and blocks[-2][0] > blocks[-1][0]:
            v2, w2, n2 = blocks.pop()
            v1, w1, n1 = blocks.pop()
            blocks.append([(v1 * w1 + v2 * w2) / (w1 + w2), w1 + w2, n1 + n2])
    out: list[float] = []
    for v, _, n in blocks:
        out += [v] * int(n)
    return out


def common(a: tuple, b: tuple) -> int:
    n = 0
    while n < min(len(a), len(b)) and a[n] == b[n]:
        n += 1
    return n
