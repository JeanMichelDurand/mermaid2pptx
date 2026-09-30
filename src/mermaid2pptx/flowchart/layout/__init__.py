"""Flowchart layout: a small layered (Sugiyama-style) engine with orthogonal routing.

Every edge is a straight line or an elbow connector whose segments are horizontal/vertical,
with horizontal jogs spread on separate tracks between two layers so they never sit on top of
each other. The phases, one module each:

    ranking    sizes, cycle breaking, layers
    graph      the layered graph: dummy nodes for long edges, label slots
    ordering   order within each layer (fewest crossings)
    placement  cross coordinates
    lanes      swim lanes side by side
    routing    back edges, tracks, rank coordinates, routes
"""
from __future__ import annotations

from dataclasses import replace

from ...geometry import Box
from ..model import Diagram, ancestors
from .graph import LayerGraph
from .lanes import lane_boxes, shift_lanes
from .model import ICON_EM, OUTSIDE_GAP, Layout, Route
from .ordering import order_layers
from .placement import place_nodes
from .ranking import measure, rank_nodes
from .routing import Frame, back_edge_sides, route_edges, side_runs

__all__ = ["ICON_EM", "OUTSIDE_GAP", "Layout", "Route", "layout"]


def layout(d: Diagram, font_size: float = 12.0) -> Layout:
    fs = font_size
    m = measure(d, fs)
    rk = rank_nodes(d)
    through: set[int] = set()        # back edges threaded through the layers
    while True:
        g = LayerGraph(d, fs, m, rk, through)
        order_layers(g)
        place_nodes(g)
        back_side, blocked = back_edge_sides(g)
        if not blocked:
            break
        # no room round the outside: lay out again with them threaded through the layers like
        # forward edges (dummy slots reserved), drawn upwards
        through |= blocked
    side_c = side_runs(g, back_side)
    bands = shift_lanes(g, back_side, side_c) if g.lane_ix else []
    f = Frame(g)
    routes = route_edges(g, f, back_side, side_c)
    clusters, cl_boxes = _clusters(g, f.boxes, routes)
    lanes = lane_boxes(g, bands, f.boxes, cl_boxes, routes) if bands else []
    return _normalised(Layout(f.boxes, m.lines, routes, clusters, 0.0, 0.0, fs, lanes))


def _clusters(g: LayerGraph, boxes: dict[str, Box], routes: list[Route]):
    """Subgraph boxes (lanes aside), innermost first so parents can wrap them; drawn outermost first."""
    d, pad = g.d, g.pad
    cl_boxes: dict[str, Box] = {}
    order = sorted((s for s in d.subgraphs if s not in g.lane_ix), key=lambda s: -len(ancestors(d, s)))
    for sid in order:
        parts = [boxes[n] for n in g.ids if d.nodes[n].cluster == sid]
        parts += [cl_boxes[s] for s in d.subgraphs if d.subgraphs[s].parent == sid and s in cl_boxes]
        parts += [r.label for r in routes if r.label and sid in g.paths[r.edge.src]
                  and sid in g.paths[r.edge.dst] and r.edge.src != r.edge.dst]
        if not parts:
            continue
        x0 = min(b.x for b in parts) - pad
        y0 = min(b.y for b in parts) - pad - g.title_h
        x1 = max(b.x + b.w for b in parts) + pad
        y1 = max(b.y + b.h for b in parts) + pad
        cl_boxes[sid] = Box(x0, y0, x1 - x0, y1 - y0)
    drawn = sorted(cl_boxes, key=lambda s: (len(ancestors(d, s)), -cl_boxes[s].w * cl_boxes[s].h))
    return [(s, cl_boxes[s], [d.subgraphs[s].title]) for s in drawn], cl_boxes


def _normalised(lay: Layout) -> Layout:
    """The same layout moved so its bounding box starts at (0, 0), with its width and height."""
    xs, ys = [], []
    for b in list(lay.boxes.values()) + [b for _, b, _ in lay.clusters] + [r.label for r in lay.routes if r.label] + \
            [b for _, body, header, _ in lay.lanes for b in (body, header)]:
        xs += [b.x, b.x + b.w]
        ys += [b.y, b.y + b.h]
    for r in lay.routes:
        xs += [p[0] for p in r.points]
        ys += [p[1] for p in r.points]
    x0, y0 = (min(xs), min(ys)) if xs else (0.0, 0.0)
    width, height = ((max(xs) - x0), (max(ys) - y0)) if xs else (0.0, 0.0)

    def shift(b):
        return replace(b, x=b.x - x0, y=b.y - y0) if b else None

    for r in lay.routes:
        r.points = [(x - x0, y - y0) for x, y in r.points]
        r.label = shift(r.label)
    return Layout({n: shift(b) for n, b in lay.boxes.items()}, lay.lines, lay.routes,
                  [(s, shift(b), t) for s, b, t in lay.clusters], width, height, lay.font_size,
                  [(s, shift(b), shift(h), t) for s, b, h, t in lay.lanes])
