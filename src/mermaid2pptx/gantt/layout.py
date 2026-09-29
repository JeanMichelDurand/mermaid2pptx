"""Gantt layout: one row per task, sections as bands down the left, time along x."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ..geometry import Box
from ..text import text_width, wrap
from .dates import strftime, ticks
from .model import Gantt, Task

# in em of the font size
CHART_W, ROW_H, BAR_H, SECTION_WRAP, TICK_GAP, LABEL = 52.0, 2.0, 1.4, 10.0, 1.0, 0.85


@dataclass
class Bar:
    task: Task
    box: Box                        # the bar, or the diamond of a milestone
    label: Box
    inside: bool                    # the name sits on the bar (else beside it)


@dataclass
class GanttLayout:
    title: tuple[Box, list[str]] | None
    sections: list[tuple[str, Box, Box, list[str]]]     # name, band, label column, wrapped name
    bars: list[Bar]
    ticks: list[tuple[float, str]]                      # x, label
    tick_label_w: float
    grid: tuple[float, float]                           # top and bottom y of the grid lines
    axis_y: float
    shaded: list[Box]                                   # excluded days
    width: float
    height: float
    font_size: float


def layout(g: Gantt, font_size: float = 12.0) -> GanttLayout:
    fs = font_size
    lfs = LABEL * fs
    t0 = min(t.start for t in g.tasks)
    t1 = max(t.end for t in g.tasks)
    if t1 <= t0:
        t1 = t0.replace(hour=23, minute=59)
    tick_dates = ticks(t0, t1, g.tick_interval, g.week_start)
    labels = [strftime(d, g.axis_format) for d in tick_dates]
    tick_w = max((text_width(s, lfs) for s in labels), default=0.0) + TICK_GAP * fs
    names = {s: wrap(s, fs, SECTION_WRAP * fs) if s else [] for s in g.sections}
    col_w = max((max(text_width(ln, fs) for ln in ls) for ls in names.values() if ls), default=0.0)
    col_w = col_w + 1.6 * fs if col_w else 0.0
    chart_w = max(CHART_W * fs, len(tick_dates) * tick_w)
    x0 = col_w

    def x(d: datetime) -> float:
        return x0 + (d - t0).total_seconds() / (t1 - t0).total_seconds() * chart_w

    top = 0.0
    title = None
    if g.title:
        tl = wrap(g.title, 1.2 * fs, 1e9)
        tw = max(text_width(ln, 1.2 * fs) for ln in tl) + fs
        title = (Box(x0 + chart_w / 2 - tw / 2, 0.0, tw, len(tl) * 1.44 * fs), tl)
        top = title[0].h + 0.8 * fs
    y = top
    sections, bars = [], []
    row_h, bar_h = ROW_H * fs, BAR_H * fs
    for s in g.sections:
        rows = [t for t in g.tasks if t.section == s]
        if not rows:
            continue
        band_h = max(len(rows) * row_h, len(names[s]) * 1.2 * fs + 0.8 * fs)
        sections.append((s, Box(0.0, y, col_w + chart_w, band_h), Box(0.0, y, col_w, band_h), names[s]))
        ry = y + (band_h - len(rows) * row_h) / 2
        for t in rows:
            cy = ry + row_h / 2
            name_w = text_width(t.name, lfs) + 0.8 * fs
            if t.milestone:
                mx = x(t.start + (t.end - t.start) / 2)
                box = Box(mx - bar_h / 2, cy - bar_h / 2, bar_h, bar_h)
                inside = False
            else:
                bx0, bx1 = x(t.start), max(x(t.end), x(t.start) + 0.3 * fs)
                box = Box(bx0, cy - bar_h / 2, bx1 - bx0, bar_h)
                inside = name_w <= box.w
            if inside:
                label = Box(box.x, box.y, box.w, box.h)
            elif box.x + box.w + 0.3 * fs + name_w <= x0 + chart_w or box.x - name_w - 0.3 * fs < x0:
                label = Box(box.x + box.w + 0.3 * fs, box.y, name_w, box.h)      # right of the bar
            else:
                label = Box(box.x - 0.3 * fs - name_w, box.y, name_w, box.h)     # left, near the end
            bars.append(Bar(t, box, label, inside))
            ry += row_h
        y += band_h
    grid = (top, y)
    tick_pos = [(x(d), s) for d, s in zip(tick_dates, labels)]
    shaded = [Box(x(a), top, x(b) - x(a), y - top) for a, b in g.excluded]
    xs = [0.0, x0 + chart_w] + [b.label.x for b in bars] + [b.label.x + b.label.w for b in bars] + \
        [p - tick_w / 2 for p, _ in tick_pos] + [p + tick_w / 2 for p, _ in tick_pos]
    if title:
        xs += [title[0].x, title[0].x + title[0].w]
    left = min(xs)
    height = y + 0.3 * fs + 1.4 * lfs
    return _shifted(GanttLayout(title, sections, bars, tick_pos, tick_w, grid, y, shaded, max(xs) - left, height, fs),
                    left)


def _shifted(lay: GanttLayout, dx: float) -> GanttLayout:
    """Moves everything right by -dx, so the leftmost thing is at x = 0."""
    def mv(b: Box) -> Box:
        return Box(b.x - dx, b.y, b.w, b.h)

    if not dx:
        return lay
    lay.title = (mv(lay.title[0]), lay.title[1]) if lay.title else None
    lay.sections = [(s, mv(band), mv(col), n) for s, band, col, n in lay.sections]
    lay.bars = [Bar(b.task, mv(b.box), mv(b.label), b.inside) for b in lay.bars]
    lay.ticks = [(x - dx, s) for x, s in lay.ticks]
    lay.shaded = [mv(b) for b in lay.shaded]
    return lay
