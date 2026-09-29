"""Conversion options and colour palettes, shared by every diagram type."""
from __future__ import annotations

from dataclasses import dataclass

from pptx.enum.dml import MSO_THEME_COLOR

from .styles import contrast, parse_color

# node_*: boxes; accent: event outlines; text: labels outside the boxes
PALETTES = {
    "purple": {
        "node_fill": "5236AB", "node_line": "3A2680", "node_text": "FFFFFF", "accent": "5236AB",
        "text": "200A58", "edge": "200A58", "cluster_fill": "F2F1F9", "cluster_line": "A8A0D6",
        "cluster_text": "200A58", "label_fill": "FFFFFF",
    },
    "slate": {
        "node_fill": "F1F5F9", "node_line": "64748B", "node_text": "0F172A", "accent": "64748B",
        "text": "0F172A", "edge": "475569", "cluster_fill": "F8FAFC", "cluster_line": "94A3B8",
        "cluster_text": "334155", "label_fill": "FFFFFF",
    },
    "theme": {  # recolours with the deck it is pasted into
        "node_fill": MSO_THEME_COLOR.BACKGROUND_1, "node_line": MSO_THEME_COLOR.ACCENT_1,
        "node_text": MSO_THEME_COLOR.TEXT_1, "accent": MSO_THEME_COLOR.ACCENT_1,
        "text": MSO_THEME_COLOR.TEXT_1, "edge": MSO_THEME_COLOR.TEXT_1,
        "cluster_fill": MSO_THEME_COLOR.BACKGROUND_2, "cluster_line": MSO_THEME_COLOR.TEXT_2,
        "cluster_text": MSO_THEME_COLOR.TEXT_2, "label_fill": MSO_THEME_COLOR.BACKGROUND_1,
    },
}
AUTHOR_ENV = "MERMAID2PPTX_AUTHOR"      # default document author, when --author is not given


def palette(color: str) -> dict:
    """A named palette (PALETTES), or the slate one with boxes in the colour `#RRGGBB`."""
    if color.lower() in PALETTES:
        return PALETTES[color.lower()]
    rgb = parse_color(color)
    if rgb is None:
        raise ValueError(f"unknown colour {color!r}: use {', '.join(PALETTES)} or #RRGGBB")
    dark = "".join(f"{int(int(rgb[k:k + 2], 16) * 0.7):02X}" for k in (0, 2, 4))
    return {**PALETTES["slate"], "node_fill": rgb, "node_line": dark, "node_text": contrast(rgb), "accent": rgb}


SLIDE_SIZES = {"16:9": (960.0, 540.0), "4:3": (720.0, 540.0)}
MARGIN = 24.0


@dataclass
class Options:
    font_size: float = 12.0
    font: str | None = None
    color: str = "purple"               # a PALETTES name or #RRGGBB
    render: str = "bpmn"                # bpmn | mermaid
    events: bool = True                 # bpmn: add missing start/end events
    lanes: bool = True                  # bpmn: top-level subgraphs as swim lanes
    author: str | None = None           # None: $MERMAID2PPTX_AUTHOR, else empty
    group: bool = True
    fit: bool = True
    aspect: str = "16:9"
    direction: str | None = None
