"""Phase 3: the order of the nodes in each layer, by barycentre sweeps, with the members of a
subgraph kept contiguous and lanes in declaration order."""
from __future__ import annotations

from .graph import LayerGraph


def crossings(g: LayerGraph) -> int:
    total = 0
    for layer in g.layers[:-1]:
        segs = [(g.pos[a], g.pos[b]) for a in layer for b in g.down[a]]
        total += sum(1 for x in range(len(segs)) for y in range(x + 1, len(segs))
                     if (segs[x][0] - segs[y][0]) * (segs[x][1] - segs[y][1]) < 0)
    return total


def _sort_layer(g: LayerGraph, layer: list, neigh) -> list:
    pos, ln = g.pos, g.ln
    bary = {k: (sum(pos[n] for n in neigh[k]) / len(neigh[k]) if neigh[k] else float(pos[k]))
            for k in layer}
    depth = max((len(ln[k].path) for k in layer), default=0)
    means = {}
    for k in layer:
        p = ln[k].path
        for lvl in range(len(p)):
            means.setdefault(p[:lvl + 1], []).append(bary[k])

    def key(k):         # lane, then each enclosing subgraph's mean barycentre, then the node's own
        p = ln[k].path
        out = [(g.lane_of(k), "")]
        for lvl in range(depth):
            if len(p) > lvl:
                sg = p[:lvl + 1]
                out.append((sum(means[sg]) / len(means[sg]), "/".join(sg)))
            else:
                out.append((bary[k], ""))
        out.append((bary[k], str(pos[k])))
        return out

    return sorted(layer, key=key)


def order_layers(g: LayerGraph, sweeps: int = 24):
    """Alternate down and up sweeps; keeps the order with the fewest crossings."""
    best, best_layers = crossings(g), [list(la) for la in g.layers]
    for it in range(sweeps):
        rng = range(1, g.n_ranks) if it % 2 == 0 else range(g.n_ranks - 2, -1, -1)
        for r in rng:
            g.layers[r] = _sort_layer(g, g.layers[r], g.up if it % 2 == 0 else g.down)
            g.pos.update({k: i for i, k in enumerate(g.layers[r])})
        cur = crossings(g)
        if cur < best:
            best, best_layers = cur, [list(la) for la in g.layers]
    g.layers = best_layers
    g.pos = {k: i for layer in g.layers for i, k in enumerate(layer)}
