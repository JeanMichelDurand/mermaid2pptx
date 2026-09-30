"""Finding the diagram in a text: Markdown blocks, front matter, comments, the diagram type."""
from __future__ import annotations

import re

from .errors import MermaidError

# first word of a diagram -> its type
KINDS = {"flowchart": "flowchart", "graph": "flowchart", "sequencediagram": "sequence", "gantt": "gantt"}


def extract_blocks(src: str) -> list[str]:
    """The ```mermaid blocks of a Markdown text, or the text itself if it has none."""
    blocks = re.findall(r"^\s*(?:```|~~~)\s*mermaid[^\n]*\n(.*?)^\s*(?:```|~~~)", src, re.M | re.S)
    return blocks or [src]


def statement_lines(src: str) -> list[str]:
    """The diagram's lines, stripped: no fences, YAML front matter, blank lines or %% comments."""
    lines = src.replace("\r\n", "\n").split("\n")
    lines = [ln for ln in lines if not ln.strip().startswith(("```", "~~~"))]
    while lines and not lines[0].strip():
        lines.pop(0)
    if lines and lines[0].strip() == "---":                  # YAML front matter
        end = next((i for i, ln in enumerate(lines[1:], 1) if ln.strip() == "---"), 0)
        lines = lines[end + 1:]
    return [ln.strip() for ln in lines if ln.strip() and not ln.strip().startswith("%%")]


def diagram_kind(src: str) -> str:
    """'flowchart', 'sequence' or 'gantt', from the diagram's first word."""
    lines = statement_lines(src)
    if not lines:
        raise MermaidError("empty diagram")
    word = lines[0].split()[0]
    kind = KINDS.get(word.lower())
    if kind is None:
        raise MermaidError(f"unsupported diagram type {word!r}: this converter reads flowchart (graph), "
                           "sequenceDiagram and gantt")
    return kind
