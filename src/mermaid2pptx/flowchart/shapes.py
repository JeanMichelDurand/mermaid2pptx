"""Mermaid shape -> PowerPoint preset, connection sites and the box size its text needs.

Site indices measured in PowerPoint (ConnectionSiteCount / BeginConnect); fx, fy are the
site position as a fraction of the box. A callable fraction depends on the box (w, h).
"""
from __future__ import annotations

from pptx.enum.shapes import MSO_SHAPE

from ..geometry import Box
from ..text import text_width

_RECT4 = {"t": (0, .5, 0), "l": (1, 0, .5), "b": (2, .5, 1), "r": (3, 1, .5)}
_OVAL8 = {"t": (0, .5, 0), "l": (2, 0, .5), "b": (4, .5, 1), "r": (6, 1, .5)}
SHAPES = {
    "rect": (MSO_SHAPE.RECTANGLE, _RECT4, False),
    "round": (MSO_SHAPE.ROUNDED_RECTANGLE, _RECT4, False),
    "stadium": (MSO_SHAPE.FLOWCHART_TERMINATOR, _RECT4, False),
    "subroutine": (MSO_SHAPE.FLOWCHART_PREDEFINED_PROCESS, _RECT4, False),
    "diamond": (MSO_SHAPE.FLOWCHART_DECISION, _RECT4, False),
    "hexagon": (MSO_SHAPE.FLOWCHART_PREPARATION, _RECT4, False),
    "circle": (MSO_SHAPE.OVAL, _OVAL8, False),
    "doublecircle": (MSO_SHAPE.OVAL, _OVAL8, False),
    "cylinder": (MSO_SHAPE.FLOWCHART_MAGNETIC_DISK,
                 {"t": (1, .5, 0), "l": (2, 0, .5), "b": (3, .5, 1), "r": (4, 1, .5)}, False),
    "parallelogram": (MSO_SHAPE.FLOWCHART_DATA,
                      {"t": (1, .5, 0), "l": (2, .1, .5), "b": (4, .5, 1), "r": (5, .9, .5)}, False),
    "parallelogram_alt": (MSO_SHAPE.FLOWCHART_DATA,
                          {"t": (1, .5, 0), "l": (5, .1, .5), "b": (4, .5, 1), "r": (2, .9, .5)}, True),
    "trapezoid": (MSO_SHAPE.TRAPEZOID,
                  {"t": (0, .5, 0), "l": (1, lambda w, h: .125 * min(w, h) / w, .5),
                   "b": (2, .5, 1), "r": (3, lambda w, h: 1 - .125 * min(w, h) / w, .5)}, False),
    "trapezoid_alt": (MSO_SHAPE.FLOWCHART_MANUAL_OPERATION,
                      {"t": (0, .5, 0), "l": (1, .1, .5), "b": (2, .5, 1), "r": (3, .9, .5)}, False),
    "flag": (MSO_SHAPE.PENTAGON,
             {"t": (0, lambda w, h: (w - .5 * min(w, h)) / 2 / w, 0), "l": (1, 0, .5),
              "b": (2, lambda w, h: (w - .5 * min(w, h)) / 2 / w, 1), "r": (3, 1, .5)}, False),
    # BPMN render (see to_bpmn)
    "task": (MSO_SHAPE.ROUNDED_RECTANGLE, _RECT4, False),
    "call": (MSO_SHAPE.ROUNDED_RECTANGLE, _RECT4, False),
    "gateway": (MSO_SHAPE.FLOWCHART_DECISION, _RECT4, False),
    "start": (MSO_SHAPE.OVAL, _OVAL8, False),
    "end": (MSO_SHAPE.OVAL, _OVAL8, False),
    "intermediate": (MSO_SHAPE.OVAL, _OVAL8, False),
}
# BPMN gateways and events: a fixed-size symbol (side in em) with its text outside, beside it
OUTSIDE = {"gateway": 2.6, "start": 2.0, "end": 2.0, "intermediate": 2.0}


def site(shape: str, side: str, box: Box) -> tuple[int, float, float]:
    """Connection site on `side` of a node: (PowerPoint site index, x, y)."""
    idx, fx, fy = SHAPES[shape][1][side]
    if box.core:            # the symbol is a square centred in a box that also holds its text
        box = Box(box.cx - box.core / 2, box.cy - box.core / 2, box.core, box.core)
    fx = fx(box.w, box.h) if callable(fx) else fx
    return idx, box.x + fx * box.w, box.y + fy * box.h


def node_size(shape: str, lines: list[str], fs: float) -> tuple[float, float]:
    """Box (w, h) in points that leaves the text inside the preset's own text area."""
    tw = max((text_width(ln, fs) for ln in lines), default=0.0)
    th = len(lines) * fs * 1.2
    px, py = 0.8 * fs, 0.55 * fs
    w, h = tw + 2 * px, th + 2 * py
    if shape == "diamond":
        w, h = 2 * tw + 2 * px, 2 * th + py
        w = max(w, 1.4 * h)
    elif shape in ("circle", "doublecircle"):
        w = h = max(tw, th) / 0.72 + px
    elif shape == "stadium":
        w += 0.7 * h
    elif shape in ("hexagon", "parallelogram", "parallelogram_alt"):
        w = w / 0.62
    elif shape in ("trapezoid", "trapezoid_alt"):
        w += 0.6 * h
    elif shape == "subroutine":
        w = w / 0.78
    elif shape == "cylinder":
        h = th / 0.5 + py
    elif shape == "flag":
        w += 0.55 * h
    return max(w, 3.5 * fs), max(h, 2.4 * fs)
