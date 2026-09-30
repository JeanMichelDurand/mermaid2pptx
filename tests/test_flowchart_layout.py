"""Layout invariants on every example in every direction, and swim lanes."""

import pytest

from mermaid2pptx.flowchart import layout, parse, to_bpmn
from samples import LANES_SRC, diagram, examples


@pytest.mark.parametrize("path, direction, render", list(examples()))
def test_layout_invariants(path, direction, render):
    d = diagram(path, direction, render)
    lay = layout(d)
    boxes = list(lay.boxes.items())
    for i, (a, ba) in enumerate(boxes):                 # nodes never overlap
        for b, bb in boxes[i + 1:]:
            assert ba.x + ba.w <= bb.x + 0.01 or bb.x + bb.w <= ba.x + 0.01 or \
                ba.y + ba.h <= bb.y + 0.01 or bb.y + bb.h <= ba.y + 0.01, (a, b)
    for r in lay.routes:
        pts = r.points
        for p, q in zip(pts, pts[1:]):                  # orthogonal
            assert abs(p[0] - q[0]) < 0.01 or abs(p[1] - q[1]) < 0.01, (r.edge, pts)
        if r.edge.src == r.edge.dst:
            continue
        segments = list(zip(pts, pts[1:]))
        for n, b in lay.boxes.items():                  # never through a node
            for k, (p, q) in enumerate(segments):
                # the end segments may cut the bounding box corner of their own node to reach
                # an inset site (parallelogram, trapezoid)
                if (k == 0 and n == r.edge.src) or (k == len(segments) - 1 and n == r.edge.dst):
                    continue
                x0, x1, y0, y1 = min(p[0], q[0]), max(p[0], q[0]), min(p[1], q[1]), max(p[1], q[1])
                inside = x1 > b.x + 0.5 and x0 < b.x + b.w - 0.5 and y1 > b.y + 0.5 and y0 < b.y + b.h - 0.5
                assert not inside, (r.edge.src, r.edge.dst, "crosses", n)



@pytest.mark.parametrize("direction", ["TB", "BT", "LR", "RL"])
def test_lanes(direction):
    d = to_bpmn(parse(LANES_SRC))
    d.direction = direction
    assert d.lanes == ["U", "T", "P"]
    lay = layout(d)
    vertical = direction in ("TB", "BT")
    lanes = {sid: body for sid, body, _, _ in lay.lanes}
    spans = [(b.x, b.x + b.w) if vertical else (b.y, b.y + b.h) for b in lanes.values()]
    for (_, a1), (b0, _) in zip(spans, spans[1:]):     # adjacent, in declaration order
        assert b0 == pytest.approx(a1)
    for n, box in lay.boxes.items():                    # each node inside its own lane
        body = lanes[d.path(n)[0]]
        assert body.x - 0.01 <= box.x and box.x + box.w <= body.x + body.w + 0.01, n
        assert body.y - 0.01 <= box.y and box.y + box.h <= body.y + body.h + 0.01, n
    headers = [h for _, _, h, _ in lay.lanes]
    assert all((h.y + h.h if vertical else h.x + h.w) == pytest.approx(
        lanes["U"].y if vertical else lanes["U"].x) for h in headers)   # headers before the flow
    assert [c[0] for c in lay.clusters] == ["N"]        # a nested subgraph stays a group
