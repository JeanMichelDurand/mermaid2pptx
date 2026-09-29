"""Swim lanes (`--render bpmn`, top-level subgraphs): side-by-side bands across the whole diagram."""
from __future__ import annotations

from ...geometry import Box
from ...text import text_width, wrap
from .graph import LayerGraph
from .model import ICON_EM, LOOP, WRAP_EM, Route


def shift_lanes(g: LayerGraph, back_side: dict[int, int], side_c: dict[int, float]) -> list[tuple[str, float, float]]:
    """Shift each lane as a whole so their bands sit side by side, in order. Moves the nodes'
    and back edges' cross coordinates; returns each lane's band (id, low, high)."""
    ln, edges, fs, pad = g.ln, g.edges, g.fs, g.pad
    ext: dict[int, list[float]] = {}
    for k, node in ln.items():
        m = len(node.path) * pad
        lo_hi = ext.setdefault(g.lane_of(k), [node.c - node.cs / 2 - m, node.c + node.cs / 2 + m])
        lo_hi[0] = min(lo_hi[0], node.c - node.cs / 2 - m)
        lo_hi[1] = max(lo_hi[1], node.c + node.cs / 2 + m)
    for i, c in side_c.items():
        sign, (lw, lh) = back_side[i], g.m.label_size[i]
        reach_ = c + sign * (g.rc(lw, lh)[1] / 2 + pad)
        lo_hi = ext[g.lane_of(edges[i].src)]
        lo_hi[0], lo_hi[1] = min(lo_hi[0], reach_), max(lo_hi[1], reach_)
    for i in g.rk.loops:
        n = edges[i].src
        extra = LOOP * fs + (g.rc(*g.m.label_size[i])[1] + 0.2 * fs if edges[i].text else 0.0) + pad
        ext[g.lane_of(n)][1] = max(ext[g.lane_of(n)][1], ln[n].c + ln[n].cs / 2 + extra)
    bands: list[tuple[str, float, float]] = []
    delta, end = {}, 0.0
    for sg, ix in g.lane_ix.items():
        lo, hi = ext.get(ix, [end, end])
        title = g.d.subgraphs[sg]
        want = min(text_width(title.title, fs) + (ICON_EM + 0.4) * fs * bool(title.icon),
                   WRAP_EM * fs) + 2 * pad
        if hi - lo < want:
            lo, hi = (lo + hi - want) / 2, (lo + hi + want) / 2
        delta[ix] = end - lo
        bands.append((sg, end, end + hi - lo))
        end += hi - lo
    for k in ln:
        ln[k].c += delta[g.lane_of(k)]
    for i in side_c:
        side_c[i] += delta[g.lane_of(edges[i].src)]
    return bands


def lane_boxes(g: LayerGraph, bands, boxes: dict[str, Box], cl_boxes: dict[str, Box],
               routes: list[Route]) -> list[tuple[str, Box, Box, list[str]]]:
    """One band each across the whole diagram, a header strip at the start of the flow:
    (lane id, body, header, title lines)."""
    fs, pad, vertical = g.fs, g.pad, g.vertical
    allb = list(boxes.values()) + list(cl_boxes.values()) + [r.label for r in routes if r.label]
    pts = [p for r in routes for p in r.points]
    # extent along the rank axis (screen y when vertical, x otherwise)
    r0 = min([b.y if vertical else b.x for b in allb] + [p[1] if vertical else p[0] for p in pts]) - pad
    r1 = max([b.y + b.h if vertical else b.x + b.w for b in allb]
             + [p[1] if vertical else p[0] for p in pts]) + pad
    titles = {}
    for sg, lo, hi in bands:
        icon = (ICON_EM + 0.4) * fs if g.d.subgraphs[sg].icon else 0.0
        titles[sg] = wrap(g.d.subgraphs[sg].title, fs, max(hi - lo - pad - icon, 3 * fs))
    head = max(len(t) for t in titles.values()) * fs * 1.2 + 0.8 * fs
    out = []
    for sg, lo, hi in bands:
        if vertical:
            body, header = Box(lo, r0, hi - lo, r1 - r0), Box(lo, r0 - head, hi - lo, head)
        else:
            body, header = Box(r0, lo, r1 - r0, hi - lo), Box(r0 - head, lo, head, hi - lo)
        out.append((sg, body, header, titles[sg]))
    return out
