"""Phase 4: cross coordinates. Packed layers, then median alignment with neighbours (isotonic
fit, so the order holds), dummy chains straightened, 1-to-1 links put in line."""
from __future__ import annotations

from .graph import LayerGraph
from .model import median, pav


def _place_layer(g: LayerGraph, r: int, neigh):
    ln, layer = g.ln, g.layers[r]
    targets, weights = [], []
    for k in layer:
        ns = neigh[k]
        if ns:
            want = median([g.anchor(n, k) for n in ns])
            if ln[k].real:
                want -= g.anchor(k, ns[0]) - ln[k].c
            targets.append(want)
        else:
            targets.append(ln[k].c)
        weights.append(1.0 if ln[k].real else 4.0)
    ys = pav([t - o for t, o in zip(targets, g.offsets[r])], weights)
    for k, y, o in zip(layer, ys, g.offsets[r]):
        ln[k].c = y + o


def place_nodes(g: LayerGraph, sweeps: int = 10):
    ln = g.ln
    g.offsets = []
    for layer in g.layers:
        off = [0.0]
        for a, b in zip(layer, layer[1:]):
            off.append(off[-1] + g.sep(a, b))
        g.offsets.append(off)
        for k, o in zip(layer, off):
            ln[k].c = o

    for it in range(sweeps):
        if it % 2 == 0:
            for r in range(1, g.n_ranks):
                _place_layer(g, r, g.up)
        else:
            for r in range(g.n_ranks - 2, -1, -1):
                _place_layer(g, r, g.down)

    # straighten dummy chains: one lane, ideally in line with the source or the target
    for keys in g.chains.values():
        dummies = keys[1:-1]
        if not dummies:
            continue
        for lane in (g.anchor(keys[-1], keys[-2]), g.anchor(keys[0], keys[1]), median([ln[k].c for k in dummies])):
            old = [ln[k].c for k in dummies]
            if all(g.try_move(k, lane) for k in dummies):
                break
            for k, c in zip(dummies, old):
                ln[k].c = c

    # 1-to-1 links between real nodes: put the pair in line when there is room
    for rng, nb, back in ((range(1, g.n_ranks), g.up, g.down), (range(g.n_ranks - 2, -1, -1), g.down, g.up)):
        for r in rng:
            for k in g.layers[r]:
                if ln[k].real and len(nb[k]) == 1 and len(back[nb[k][0]]) == 1 and ln[nb[k][0]].real:
                    o = nb[k][0]
                    g.try_move(k, ln[k].c + g.anchor(o, k) - g.anchor(k, o))
