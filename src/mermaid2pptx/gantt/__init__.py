"""Gantt charts (`gantt`): parse, lay out, draw."""
from __future__ import annotations

from pptx import Presentation

from ..options import Options
from .layout import GanttLayout, layout
from .model import Gantt
from .parser import parse
from .render import render

__all__ = ["Gantt", "GanttLayout", "convert", "layout", "parse", "render"]


def convert(src: str, opts: Options) -> tuple[Presentation, Gantt, GanttLayout]:
    g = parse(src)
    lay = layout(g, opts.font_size)
    return render(g, lay, opts), g, lay
