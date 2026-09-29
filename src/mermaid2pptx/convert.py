"""One Mermaid diagram -> a one-slide deck, whatever its type."""
from __future__ import annotations

from pptx import Presentation

from . import flowchart
from .options import Options
from .source import diagram_kind

_CONVERTERS = {"flowchart": flowchart.convert}


def convert(src: str, opts: Options | None = None) -> tuple[Presentation, object, object]:
    """(deck, parsed diagram, layout). Every diagram has `warnings` and a `summary()`."""
    opts = opts or Options()
    return _CONVERTERS[diagram_kind(src)](src, opts)
