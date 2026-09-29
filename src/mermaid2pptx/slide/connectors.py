"""Connectors: an orthogonal route -> a bentConnector preset glued to its shapes' sites."""
from __future__ import annotations

from lxml import etree
from pptx.enum.shapes import MSO_CONNECTOR
from pptx.oxml.ns import qn

from .deck import EMU_PER_PT
from .shapes import strip_style

_ROT = {(1, 0): 0, (0, 1): 5400000, (-1, 0): 10800000, (0, -1): 16200000}
# a straight edge is a flat elbow (bentConnector3 of height 0): it stays orthogonal when
# PowerPoint re-routes it after a node is moved, where a straightConnector1 turns diagonal
_PRESET = {1: "bentConnector3", 2: "bentConnector2", 3: "bentConnector3",
           4: "bentConnector4", 5: "bentConnector5"}


def simplify(points: list[tuple[float, float]], eps: float = 0.01) -> list[tuple[float, float]]:
    """Drop zero-length segments and merge collinear ones."""
    out: list[tuple[float, float]] = []
    for p in points:
        if out and abs(p[0] - out[-1][0]) < eps and abs(p[1] - out[-1][1]) < eps:
            continue
        if len(out) >= 2:
            a, b = out[-2], out[-1]
            if (abs(a[0] - b[0]) < eps and abs(b[0] - p[0]) < eps) or \
               (abs(a[1] - b[1]) < eps and abs(b[1] - p[1]) < eps):
                out[-1] = p
                continue
        out.append(p)
    return out


def connector_geometry(points: list[tuple[float, float]], min_extent: float = 0.1) -> dict:
    """Preset, rotation, flip, box and adjust values of a connector drawing `points`.

    `points` is an orthogonal polyline (1 to 5 segments). A bentConnectorN draws, in its own
    box, (0,0) -> (x1,0) -> (x1,y2) -> (x3,y2) ... -> (w,h), the first segment along +x;
    `rot` (a multiple of 90 degrees) turns +x onto the first segment's direction and `flipV`
    puts the end on the right side, so the drawn path is exactly `points`.
    """
    n = len(points) - 1
    if not 1 <= n <= 5:
        raise ValueError(f"a connector draws 1 to 5 segments, not {n}")
    (sx, sy), (ex, ey) = points[0], points[-1]
    dx, dy = points[1][0] - sx, points[1][1] - sy
    first = (1 if dx > 0 else -1, 0) if abs(dx) >= abs(dy) else (0, 1 if dy > 0 else -1)
    a = (ex - sx) * first[0] + (ey - sy) * first[1]
    ux = first if a >= 0 or n == 1 else (-first[0], -first[1])
    uy_rot = (-ux[1], ux[0])                         # where the rotation sends local +y
    b = (ex - sx) * uy_rot[0] + (ey - sy) * uy_rot[1]
    flip = b < 0
    uy = (-uy_rot[0], -uy_rot[1]) if flip else uy_rot
    w, h = abs(a), abs(b)
    if n > 1:
        w, h = max(w, min_extent), max(h, min_extent)
    local = [((x - sx) * ux[0] + (y - sy) * ux[1], (x - sx) * uy[0] + (y - sy) * uy[1])
             for x, y in points]
    adj = [round(100000 * (local[k][0] / w if k % 2 else local[k][1] / h)) for k in range(1, n - 1)] \
        if n > 1 else [50000]
    cx = sx + ux[0] * w / 2 + uy[0] * h / 2
    cy = sy + ux[1] * w / 2 + uy[1] * h / 2
    return dict(prst=_PRESET[n], rot=_ROT[ux], flipV=flip, x=cx - w / 2, y=cy - h / 2, w=w, h=h, adj=adj)


def add_path(shapes, pts: list[tuple[float, float]], start: tuple[int, int | None],
             end: tuple[int, int | None]):
    """A connector drawing the orthogonal polyline `pts` (slide points), glued at `start` and
    `end` = (shape id, site index or None); an unglued freeform past a preset's 5 segments."""
    if len(pts) - 1 <= 5:
        cx = shapes.add_connector(MSO_CONNECTOR.STRAIGHT, 0, 0, 1, 1)
        strip_style(cx)
        _set_connector_xml(cx, connector_geometry(pts), start, end)
        return cx
    fb = shapes.build_freeform(round(pts[0][0] * EMU_PER_PT), round(pts[0][1] * EMU_PER_PT), scale=1.0)
    fb.add_line_segments([(round(x * EMU_PER_PT), round(y * EMU_PER_PT)) for x, y in pts[1:]], close=False)
    cx = fb.convert_to_shape()
    strip_style(cx)
    cx.fill.background()
    return cx


def _set_connector_xml(cx, g: dict, start: tuple[int, int | None], end: tuple[int, int | None]):
    el = cx._element
    sp_pr = el.find(qn("p:spPr"))
    xfrm = sp_pr.find(qn("a:xfrm"))
    for attr in ("rot", "flipH", "flipV"):
        xfrm.attrib.pop(attr, None)
    if g["rot"]:
        xfrm.set("rot", str(g["rot"]))
    if g["flipV"]:
        xfrm.set("flipV", "1")
    xfrm.find(qn("a:off")).set("x", str(round(g["x"] * EMU_PER_PT)))
    xfrm.find(qn("a:off")).set("y", str(round(g["y"] * EMU_PER_PT)))
    xfrm.find(qn("a:ext")).set("cx", str(round(g["w"] * EMU_PER_PT)))
    xfrm.find(qn("a:ext")).set("cy", str(round(g["h"] * EMU_PER_PT)))
    geom = sp_pr.find(qn("a:prstGeom"))
    geom.set("prst", g["prst"])
    av = geom.find(qn("a:avLst"))
    if av is None:
        av = etree.SubElement(geom, qn("a:avLst"))
    for child in list(av):
        av.remove(child)
    for k, v in enumerate(g["adj"], 1):
        etree.SubElement(av, qn("a:gd"), name=f"adj{k}", fmla=f"val {v}")
    c_nv = el.find(qn("p:nvCxnSpPr")).find(qn("p:cNvCxnSpPr"))
    for tag, (shape_id, idx) in (("a:stCxn", start), ("a:endCxn", end)):
        if idx is not None:
            etree.SubElement(c_nv, qn(tag), id=str(shape_id), idx=str(idx))
