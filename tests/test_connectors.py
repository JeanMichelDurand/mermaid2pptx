"""Connector geometry, checked against an independent reading of the OOXML presets."""
import random

import pytest

from mermaid2pptx.slide.connectors import connector_geometry, simplify
from ooxml import drawn_path


def _random_route(rng, n):
    pts, (x, y) = [(0.0, 0.0)], (0.0, 0.0)
    axis = rng.choice((0, 1))
    for _ in range(n):
        step = rng.choice((-1, 1)) * rng.uniform(5, 100)
        x, y = (x + step, y) if axis == 0 else (x, y + step)
        pts.append((x, y))
        axis = 1 - axis
    return pts


@pytest.mark.parametrize("n", [1, 2, 3, 4, 5])
def test_connector_geometry_draws_the_route(n):
    rng = random.Random(n)
    for _ in range(300):
        pts = _random_route(rng, n)
        g = connector_geometry(pts)
        drawn = simplify(drawn_path(g["prst"], g["adj"], g["x"], g["y"], g["w"], g["h"], g["rot"], g["flipV"]))
        assert len(drawn) == len(pts)
        for p, q in zip(drawn, pts):     # 0.1pt: the minimum box extent of a bent connector
            assert p == pytest.approx(q, abs=0.11), (pts, g)


def test_connector_geometry_degenerate_width():
    """A back edge between two sites at the same x: the box gets a 0.1pt minimum width."""
    pts = [(100, 200), (130, 200), (130, 50), (100, 50)]
    g = connector_geometry(pts)
    drawn = drawn_path(g["prst"], g["adj"], g["x"], g["y"], g["w"], g["h"], g["rot"], g["flipV"])
    assert drawn[0] == pytest.approx(pts[0], abs=0.01)
    assert drawn[-1] == pytest.approx(pts[-1], abs=0.11)
    assert max(p[0] for p in drawn) == pytest.approx(130, abs=0.01)


def test_simplify():
    assert simplify([(0, 0), (0, 0), (0, 5), (0, 10), (3, 10)]) == [(0, 0), (0, 10), (3, 10)]
