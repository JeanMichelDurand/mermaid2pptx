"""Flowcharts (`flowchart` / `graph`): parse, optionally read as BPMN, lay out, draw."""
from __future__ import annotations

from pptx import Presentation

from ..options import Options
from .bpmn import to_bpmn
from .layout import Layout, layout
from .model import Diagram
from .parser import DIRECTIONS, parse
from .render import render

__all__ = ["DIRECTIONS", "Diagram", "Layout", "convert", "layout", "parse", "render", "to_bpmn"]


def convert(src: str, opts: Options) -> tuple[Presentation, Diagram, Layout]:
    d = parse(src)
    if opts.direction:
        d.direction = DIRECTIONS[opts.direction.upper()]
    if opts.render == "bpmn":
        to_bpmn(d, opts.events, opts.lanes)
    lay = layout(d, opts.font_size)
    return render(d, lay, opts), d, lay
