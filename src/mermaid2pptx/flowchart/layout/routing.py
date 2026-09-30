"""Phase 5: edges. Back edges round the outside, tracks for the horizontal jogs between two
layers, the rank coordinate of each layer, then every edge's orthogonal route."""
from __future__ import annotations

from ...geometry import Box
from ..shapes import site
from .graph import LayerGraph
from .model import BACKSEP, IN, LOOP, OUT, RANKSEP, SIDE, SIDE_NEG, TRACK, Route


def back_edge_sides(g: LayerGraph) -> tuple[dict[int, int], set[int]]:
    """Back edges go round the outside of the layers, on the side (+1 or -1) where both of their
    nodes are outermost (with lanes: in their own lane, for an edge that stays in one lane).
    Returns those sides, and the back edges with no such side: they must be threaded through."""
    ln, edges, rank = g.ln, g.edges, g.rk.rank

    def outermost(n, sign):
        return all(not ln[k].real or g.lane_of(k) != g.lane_of(n) or (ln[k].c - ln[n].c) * sign <= 0
                   for k in g.layers[rank[n]])

    back_side: dict[int, int] = {}
    blocked = set()
    for i in g.rk.reversed_ - g.through:
        e = edges[i]
        sign = None if g.lane_of(e.src) != g.lane_of(e.dst) else \
            next((sg for sg in (1, -1) if outermost(e.src, sg) and outermost(e.dst, sg)), None)
        if sign is None:
            blocked.add(i)
        else:
            back_side[i] = sign
    return back_side, blocked


def side_runs(g: LayerGraph, back_side: dict[int, int]) -> dict[int, float]:
    """Cross coordinate of each back edge's run beside the layers; overlapping ones are stacked outwards."""
    ln, edges, rank, fs = g.ln, g.edges, g.rk.rank, g.fs
    side_c: dict[int, float] = {}
    runs: list[tuple[int, int, int, int, float]] = []
    for i in sorted(back_side, key=lambda i: abs(rank[edges[i].src] - rank[edges[i].dst])):
        e, sign = edges[i], back_side[i]
        lo, hi = sorted((rank[e.src], rank[e.dst]))

        def reach(k):       # how far a node and the subgraph boxes around it extend on that side
            depth = len(ln[k].path)
            titles = (depth - bool(g.lane_ix)) * g.title_h if not g.vertical and sign < 0 else 0.0
            return sign * ln[k].c + ln[k].cs / 2 + depth * g.pad + titles

        run = sign * (max(reach(k) for k in ln if lo <= ln[k].rank <= hi and g.lane_of(k) == g.lane_of(e.src))
                      + BACKSEP * fs)
        for a, b, sg, ls, lc in runs:
            if sg == sign and ls == g.lane_of(e.src) and a <= hi and lo <= b:
                run = sign * max(sign * run, sign * lc + BACKSEP * fs)
        lcs = g.rc(*g.m.label_size[i])[1] if e.text else 0.0
        side_c[i] = run + sign * lcs / 2
        runs.append((lo, hi, sign, g.lane_of(e.src), run + sign * lcs))
    return side_c


class Frame:
    """Tracks and rank coordinates: where each layer and each horizontal jog sits on the rank
    axis, and the node boxes on the page (before normalising to the origin)."""

    def __init__(self, g: LayerGraph):
        self.g = g
        ln, fs, rank = g.ln, g.fs, g.rk.rank
        self.snap = 0.15 * fs
        self._tracks()
        sg_ranks: dict[str, list[int]] = {}
        for n in g.ids:
            for sg in g.paths[n]:
                if sg not in g.lane_ix:       # a lane's title is in its header, not between layers
                    sg_ranks.setdefault(sg, []).append(rank[n])
        n_ranks = g.n_ranks
        self.layer_size = layer_size = [max((ln[k].rs for k in layer), default=0.0) for layer in g.layers]
        self.gaps = gaps = []
        for gap in range(n_ranks - 1):
            starts = sum(1 for rs in sg_ranks.values() if min(rs) == gap + 1)
            ends_ = sum(1 for rs in sg_ranks.values() if max(rs) == gap)
            extra = (starts + ends_) * g.pad
            if g.vertical:
                extra += g.title_h * (starts if g.direction == "TB" else ends_)
            gaps.append(max(RANKSEP * fs, (self.n_tracks[gap] + 1) * TRACK * fs) + extra)
        self.r_center = r_center = [layer_size[0] / 2] if n_ranks else []
        for gap in range(n_ranks - 1):
            r_center.append(r_center[-1] + layer_size[gap] / 2 + gaps[gap] + layer_size[gap + 1] / 2)
        self.r_max = (r_center[-1] + layer_size[-1] / 2) if n_ranks else 0.0
        self.boxes = {}
        for n in g.ids:
            w, h = g.m.sizes[n]
            x, y = self.to_screen(r_center[rank[n]], ln[n].c)
            self.boxes[n] = Box(x - w / 2, y - h / 2, w, h, g.m.cores.get(n, 0.0))

    def _tracks(self):
        """Horizontal jogs of different edges in one gap never share a line."""
        g, snap = self.g, self.snap
        ln = g.ln
        out_deg = {n: 0 for n in g.ids}
        in_deg = {n: 0 for n in g.ids}
        for keys in g.chains.values():
            out_deg[keys[0]] += 1
            in_deg[keys[-1]] += 1
        self.jogs = jogs = {}                  # edge -> [(gap, from_c, to_c, key)]
        intervals: dict[int, dict] = {}       # gap -> key -> [lo, hi]
        for i, keys in g.chains.items():
            cur = g.anchor(keys[0], keys[1])
            jogs[i] = []
            for j in range(1, len(keys)):
                a, b = keys[j - 1], keys[j]
                to = g.anchor(b, a)
                if abs(to - cur) <= snap:
                    continue
                if i in g.rk.reversed_:          # threaded back edge: its own track, never shared
                    key = ("e", i, j)
                elif ln[a].real and ln[b].real:
                    key = ("s", a) if out_deg[a] >= in_deg[b] else ("t", b)
                elif ln[a].real:
                    key = ("s", a)
                elif ln[b].real:
                    key = ("t", b)
                else:
                    key = ("e", i, j)
                gap = ln[a].rank
                jogs[i].append((gap, cur, to, key))
                iv = intervals.setdefault(gap, {}).setdefault(key, [min(cur, to), max(cur, to)])
                iv[0], iv[1] = min(iv[0], cur, to), max(iv[1], cur, to)
                cur = to
        self.track_of = {}
        self.n_tracks = [0] * g.n_ranks
        for gap, ivs in intervals.items():
            ends: list[float] = []
            for key, (lo, hi) in sorted(ivs.items(), key=lambda kv: kv[1][0]):
                t = next((t for t, e in enumerate(ends) if e < lo - 0.5 * g.fs), None)
                if t is None:
                    t = len(ends)
                    ends.append(hi)
                ends[t] = hi
                self.track_of[(gap, key)] = t
            self.n_tracks[gap] = len(ends)

    def track_r(self, gap, key):
        start = self.r_center[gap] + self.layer_size[gap] / 2
        return start + (self.track_of[(gap, key)] + 1) * self.gaps[gap] / (self.n_tracks[gap] + 1)

    def to_screen(self, r, c):
        return {"TB": (c, r), "BT": (c, self.r_max - r), "LR": (r, c), "RL": (self.r_max - r, c)}[self.g.direction]

    def to_abs(self, x, y):
        return {"TB": (y, x), "BT": (self.r_max - y, x), "LR": (x, y), "RL": (self.r_max - x, y)}[self.g.direction]

    def site_abs(self, n, side):
        """A node's connection site: (index, (rank, cross))."""
        idx, x, y = site(self.g.d.nodes[n].shape, side, self.boxes[n])
        return idx, self.to_abs(x, y)


def _labelled(route: Route, x, y, g: LayerGraph, i: int) -> Route:
    lw, lh = g.m.label_size[i]
    route.label, route.label_lines = Box(x - lw / 2, y - lh / 2, lw, lh), g.m.label_lines[i]
    return route


def route_edges(g: LayerGraph, f: Frame, back_side: dict[int, int], side_c: dict[int, float]) -> list[Route]:
    """Every edge's route, in the order the edges were written."""
    edges, direction, ln = g.edges, g.direction, g.ln
    routes: list[Route] = []
    for i, keys in g.chains.items():
        e = edges[i]
        si, (sr, sc) = f.site_abs(keys[0], OUT[direction])
        ti, (er, ec) = f.site_abs(keys[-1], IN[direction])
        pts = [(sr, sc)]
        for gap, frm, to, key in f.jogs[i]:
            tr = f.track_r(gap, key)
            pts += [(tr, frm), (tr, to)]
        pts.append((er, pts[-1][1] if abs(ec - pts[-1][1]) <= f.snap else ec))
        screen = [f.to_screen(r, c) for r, c in pts]
        route = Route(e, screen[::-1], ti, si) if i in g.rk.reversed_ else Route(e, screen, si, ti)
        lab = next((k for k in keys[1:-1] if ln[k].label), None)
        if lab is not None:
            x, y = f.to_screen(f.r_center[ln[lab].rank], ln[lab].c)
        elif e.text:        # a threaded back edge too short for a label slot: longest segment
            a, b = max(zip(screen, screen[1:]), key=lambda s: abs(s[0][0] - s[1][0]) + abs(s[0][1] - s[1][1]))
            x, y = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
        routes.append(_labelled(route, x, y, g, i) if e.text else route)

    # back edges: out of the side of the lower node, up a lane beside everything, into the
    # side of the upper one; lanes of overlapping back edges are stacked outwards
    for i, run in side_c.items():
        e, sign = edges[i], back_side[i]
        side = SIDE[direction] if sign > 0 else SIDE_NEG[direction]
        si, (sr, sc) = f.site_abs(e.src, side)
        ti, (er, ec) = f.site_abs(e.dst, side)
        route = Route(e, [f.to_screen(*p) for p in [(sr, sc), (sr, run), (er, run), (er, ec)]], si, ti)
        routes.append(_labelled(route, *f.to_screen((sr + er) / 2, run), g, i) if e.text else route)

    for i in sorted(g.rk.loops):
        e = edges[i]
        si, (sr, sc) = f.site_abs(e.src, SIDE[direction])
        ti, (er, ec) = f.site_abs(e.src, IN[direction])
        m = LOOP * g.fs
        top = er - m
        pts = [(sr, sc), (sr, sc + m), (top, sc + m), (top, ec), (er, ec)]
        route = Route(e, [f.to_screen(r, c) for r, c in pts], si, ti)
        if e.text:
            lh = g.rc(*g.m.label_size[i])[1]
            route = _labelled(route, *f.to_screen((sr + top) / 2, sc + m + lh / 2 + 0.2 * g.fs), g, i)
        routes.append(route)
    routes.sort(key=lambda r: edges.index(r.edge))
    return routes
