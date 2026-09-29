"""Sequence diagrams (`sequenceDiagram`): parse, lay out, draw."""
from __future__ import annotations

from pptx import Presentation

from ..options import Options
from .layout import SequenceLayout, layout
from .model import Sequence
from .parser import parse
from .render import render

__all__ = ["Sequence", "SequenceLayout", "convert", "layout", "parse", "render"]


def convert(src: str, opts: Options) -> tuple[Presentation, Sequence, SequenceLayout]:
    s = parse(src)
    lay = layout(s, opts.font_size)
    return render(s, lay, opts), s, lay
