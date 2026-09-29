"""Phase 2: the layered graph the later phases work on.

Real nodes plus a chain of dummy nodes for every edge spanning several layers (one of them
the edge's label slot), in "rank" (along the flow) and "cross" coordinates, so one code path
serves the four directions. The cross coordinate `c` of each node is what ordering and
placement compute.
"""
from __future__ import annotations

from ...geometry import Box
from ..model import Diagram
from ..shapes import site
from .model import DUMMYSEP, IN, NODESEP, OUT, PAD, LNode, common
from .ranking import Measures, Ranking


class LayerGraph:
    def __init__(self, d: Diagram, fs: float, m: Measures, rk: Ranking, through: set[int]):
        """`through`: back edges threaded through the layers like forward edges (drawn upwards)
        instead of going round the outside."""
        self.d, self.fs, self.m, self.rk, self.through = d, fs, m, rk, through
        self.direction = d.direction
        self.vertical = d.direction in ("TB", "BT")            # rank axis is screen y
        self.ids = ids = list(d.nodes)
        self.edges = edges = d.edges
        self.lane_ix = {sg: i for i, sg in enumerate(d.lanes)}
        self.title_h = fs * 1.5
        self.pad = PAD * fs
        rank, reversed_ = rk.rank, rk.reversed_

        self.paths = paths = {n: d.path(n) for n in ids}
        self.ln = ln = {}
        for n in ids:
            rs, cs = self.rc(*m.sizes[n])
            ln[n] = LNode(n, rs, cs, True, paths[n], rank[n])
        self.chains = chains = {}           # edge -> [upper node, dummies..., lower node]
        for i, e in enumerate(edges):
            if i in rk.loops or (i in reversed_ and i not in through):
                continue
            u, v = (e.dst, e.src) if i in reversed_ else (e.src, e.dst)
            span = rank[v] - rank[u]
            shared = paths[u][:common(paths[u], paths[v])]
            if self.lane_ix and not shared:      # a flow between lanes runs in the lower node's lane
                shared = paths[v][:1]
            keys = [u]
            for k in range(1, span):
                is_label = bool(e.text) and k == span // 2
                rs, cs = self.rc(*m.label_size[i]) if is_label else (0.0, 0.0)
                key = ("d", i, k)
                ln[key] = LNode(key, rs, cs, False, shared, rank[u] + k, is_label)
                keys.append(key)
            keys.append(v)
            chains[i] = keys
        self.down = {k: [] for k in ln}
        self.up = {k: [] for k in ln}
        for keys in chains.values():
            for a, b in zip(keys, keys[1:]):
                self.down[a].append(b)
                self.up[b].append(a)

        self.n_ranks = max((x.rank for x in ln.values()), default=0) + 1
        layers: list[list] = [[] for _ in range(self.n_ranks)]
        seen: set = set()
        for root in [n for n in ids if not self.up[n]] + ids:     # DFS gives the initial order
            stack = [root]
            while stack:
                k = stack.pop()
                if k in seen:
                    continue
                seen.add(k)
                layers[ln[k].rank].append(k)
                stack.extend(reversed(self.down[k]))
        self.layers = [sorted(layer, key=self.lane_of) for layer in layers]      # lanes in declaration order
        self.pos = {k: i for layer in self.layers for i, k in enumerate(layer)}
        self.offsets: list[list[float]] = []

    def rc(self, w, h):
        """Screen (w, h) -> (extent along the rank axis, along the cross axis)."""
        return (h, w) if self.vertical else (w, h)

    def lane_of(self, k) -> int:
        return self.lane_ix[self.ln[k].path[0]] if self.lane_ix else 0

    def sep(self, a, b) -> float:
        """Least distance between the centres of `a` and `b`, neighbours in a layer."""
        na, nb = self.ln[a], self.ln[b]
        solid = (na.real or na.label) and (nb.real or nb.label)
        s = (na.cs + nb.cs) / 2 + (NODESEP if solid else DUMMYSEP) * self.fs
        c = common(na.path, nb.path)
        s += ((len(na.path) - c) + (len(nb.path) - c)) * self.pad
        if not self.vertical:                               # cluster titles sit above, on the c axis
            s += (len(nb.path) - c) * self.title_h
        return s

    def c_off(self, n, side):
        """The out/in site of a node may be off-centre on the cross axis (flag shape)."""
        w, h = self.m.sizes[n]
        _, x, y = site(self.d.nodes[n].shape, side, Box(-w / 2, -h / 2, w, h, self.m.cores.get(n, 0.0)))
        return x if self.vertical else y

    def anchor(self, k, other):
        """Cross coordinate an edge leaves/enters `k` from, seen from neighbour `other`."""
        node = self.ln[k]
        if not node.real:
            return node.c
        return node.c + self.c_off(k, OUT[self.direction] if self.ln[other].rank > node.rank else IN[self.direction])

    def try_move(self, k, c) -> bool:
        """Move `k` to cross coordinate `c` if its layer neighbours leave room."""
        ln = self.ln
        layer, p = self.layers[ln[k].rank], self.pos[k]
        if p > 0 and c - ln[layer[p - 1]].c < self.sep(layer[p - 1], k) - 0.01:
            return False
        if p + 1 < len(layer) and ln[layer[p + 1]].c - c < self.sep(k, layer[p + 1]) - 0.01:
            return False
        ln[k].c = c
        return True
