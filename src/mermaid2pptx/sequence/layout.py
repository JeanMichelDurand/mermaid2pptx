"""Sequence layout: columns spaced so every label fits, then one pass down the page.

Columns: each participant's lifeline x. Neighbours keep their boxes apart, and every message,
self-message and note asks for room between two columns (`x_j - x_i >= need`); the
constraints are met left to right by pushing the later columns. Rows: each event moves a
cursor down the page and leaves its geometry behind.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..geometry import Box
from ..text import text_width, wrap
from .model import Activation, Divider, End, Fragment, Message, Note, Sequence

# spacing, in em of the font size
COL_GAP, BOX_PAD, MIN_W, LABEL_PAD, SELF_W, SELF_H, ACT_W = 2.0, 1.0, 5.0, 1.0, 2.2, 1.6, 0.9
NOTE_WRAP, NOTE_PAD, BLOCK_PAD, TAB_H, NUM = 14, 0.5, 0.8, 1.5, 1.3
LABEL = 0.85                    # message and note text, relative to the participants' text


@dataclass
class MessageGeom:
    message: Message
    points: list[tuple[float, float]]
    label: Box | None
    lines: list[str]
    number: Box | None = None       # autonumber badge
    index: int = 0


@dataclass
class BlockGeom:
    kind: str
    lines: list[str]
    box: Box
    tab: Box                        # the kind, top-left
    label: Box | None               # the condition, beside the tab
    dividers: list[tuple[float, list[str], Box | None]] = field(default_factory=list)   # y, text, where


@dataclass
class SequenceLayout:
    heads: dict[str, tuple[Box, Box]]              # participant -> top box, bottom box
    lines: dict[str, list[str]]
    lifelines: dict[str, tuple[float, float, float]]   # x, top y, bottom y
    messages: list[MessageGeom]
    activations: list[tuple[str, Box]]
    notes: list[tuple[Box, list[str]]]
    blocks: list[BlockGeom]                        # outermost first
    rects: list[tuple[Box, str]]                   # rect blocks: box, colour
    groups: list[tuple[Box, list[str], str | None]]
    title: tuple[Box, list[str]] | None
    width: float
    height: float
    font_size: float


def _columns(s: Sequence, ids: list[str], widths: dict[str, float], fs: float) -> dict[str, float]:
    lfs = LABEL * fs
    col = {p: i for i, p in enumerate(ids)}
    need: list[tuple[int, int, float]] = []
    for a, b in zip(ids, ids[1:]):
        need.append((col[a], col[b], (widths[a] + widths[b]) / 2 + COL_GAP * fs))
    for e in s.events:
        if isinstance(e, Message):
            lw = max((text_width(ln, lfs) for ln in wrap(e.text, lfs, 1e9)), default=0.0)
            i, j = sorted((col[e.src], col[e.dst]))
            if i != j:
                need.append((i, j, lw + 2 * LABEL_PAD * fs + ACT_W * fs))
            elif i + 1 < len(ids):
                need.append((i, i + 1, SELF_W * fs + lw + LABEL_PAD * fs + widths[ids[i + 1]] / 2))
        elif isinstance(e, Note):
            nw = _note_width(e, fs)
            i, j = sorted(col[a] for a in e.actors[:2]) if len(e.actors) > 1 else (col[e.actors[0]],) * 2
            if e.position == "right" and i + 1 < len(ids):
                need.append((i, i + 1, ACT_W * fs + nw + LABEL_PAD * fs + widths[ids[i + 1]] / 2))
            elif e.position == "left" and i > 0:
                need.append((i - 1, i, ACT_W * fs + nw + LABEL_PAD * fs + widths[ids[i - 1]] / 2))
            elif e.position == "over" and i != j:
                need.append((i, j, nw - 2 * NOTE_PAD * fs))
            elif e.position == "over":
                for a, b in ((i - 1, i), (i, i + 1)):
                    if 0 <= a and b < len(ids):
                        need.append((a, b, nw / 2 + LABEL_PAD * fs + widths[ids[a if a != i else b]] / 2))
    xs = [0.0] * len(ids)
    for i, j, n in sorted(need, key=lambda c: (c[1], c[0])):
        if xs[j] - xs[i] < n:
            shift = n - (xs[j] - xs[i])
            for k in range(j, len(ids)):
                xs[k] += shift
    return {p: xs[col[p]] for p in ids}


def _note_width(n: Note, fs: float) -> float:
    lfs = LABEL * fs
    return max((text_width(ln, lfs) for ln in wrap(n.text, lfs, NOTE_WRAP * fs)), default=0.0) + 2 * NOTE_PAD * fs


def layout(s: Sequence, font_size: float = 12.0) -> SequenceLayout:
    fs = font_size
    lfs = LABEL * fs
    ids = list(s.participants)
    lines = {p: wrap(s.participants[p].label, fs, 12 * fs) for p in ids}
    widths = {p: max(max((text_width(ln, fs) for ln in lines[p]), default=0.0) + 2 * BOX_PAD * fs, MIN_W * fs)
              for p in ids}
    head_h = max((len(lines[p]) * 1.2 * fs + 1.1 * fs for p in ids), default=2.4 * fs)
    head_h += max((2.4 * fs for p in ids if s.participants[p].kind == "actor"), default=0.0)   # the figure
    x = _columns(s, ids, widths, fs)
    top = 0.0
    title = None
    if s.title:
        tl = wrap(s.title, 1.2 * fs, 1e9)
        title = (Box(0, 0, 0, len(tl) * 1.44 * fs), tl)       # centred once the width is known
        top = title[0].h + 0.8 * fs
    if s.groups:
        top += 1.6 * fs                                       # the box labels sit above the heads
    heads_top = top
    y = top + head_h + 1.2 * fs

    messages: list[MessageGeom] = []
    notes: list[tuple[Box, list[str]]] = []
    activations: list[tuple[str, Box]] = []
    active: dict[str, list[float]] = {p: [] for p in ids}          # start y of each open bar
    open_blocks: list[dict] = []
    blocks: list[BlockGeom] = []
    rects: list[tuple[Box, str]] = []
    last_y = y
    number = 0

    def edge(p, towards):
        """Where a message leaves or reaches `p`'s lifeline, on the side facing `towards`."""
        depth = len(active[p])
        if not depth:
            return x[p]
        return x[p] + (1 if towards > x[p] else -1) * ACT_W * fs / 2 + (depth - 1) * ACT_W * fs / 2

    def extend(lo, hi):
        for b in open_blocks:
            b["lo"], b["hi"] = min(b["lo"], lo), max(b["hi"], hi)

    def close_bar(p, at):
        start = active[p].pop()
        depth = len(active[p])
        cx = x[p] + depth * ACT_W * fs / 2
        activations.append((p, Box(cx - ACT_W * fs / 2, start, ACT_W * fs, max(at - start, 0.6 * fs))))

    for e in s.events:
        if isinstance(e, Message):
            ll = wrap(e.text, lfs, 1e9) if e.text else []
            lh = len(ll) * 1.2 * lfs
            y += lh + 0.4 * fs
            if e.activate:
                active[e.dst].append(y)
            lw = max((text_width(ln, lfs) for ln in ll), default=0.0) + 0.4 * fs
            if e.src == e.dst:
                x0 = edge(e.src, x[e.src] + 1)
                pts = [(x0, y), (x0 + SELF_W * fs, y), (x0 + SELF_W * fs, y + SELF_H * fs), (x0, y + SELF_H * fs)]
                label = Box(x0 + 0.3 * fs, y - lh - 0.2 * fs, lw, lh) if ll else None
                extend(x[e.src] - ACT_W * fs, x0 + max(SELF_W * fs, lw + 0.3 * fs))
                bottom = y + SELF_H * fs
            else:
                x0, x1 = edge(e.src, x[e.dst]), edge(e.dst, x[e.src])
                pts = [(x0, y), (x1, y)]
                label = Box((x0 + x1) / 2 - lw / 2, y - lh - 0.2 * fs, lw, lh) if ll else None
                extend(min(x[e.src], x[e.dst]) - ACT_W * fs, max(x[e.src], x[e.dst]) + ACT_W * fs)   # bars inside
                bottom = y
            g = MessageGeom(e, pts, label, ll)
            if s.autonumber:
                number += 1
                d = NUM * fs
                g.index, g.number = number, Box(pts[0][0] - d / 2, y - d / 2, d, d)
            messages.append(g)
            last_y = y
            if e.deactivate and active[e.src]:
                close_bar(e.src, bottom)
            y = bottom + 1.0 * fs
        elif isinstance(e, Activation):
            if e.on:
                active[e.actor].append(last_y)
            elif active[e.actor]:
                close_bar(e.actor, last_y)
        elif isinstance(e, Note):
            nl = wrap(e.text, lfs, NOTE_WRAP * fs)
            nw, nh = _note_width(e, fs), len(nl) * 1.2 * lfs + 2 * NOTE_PAD * fs
            a = e.actors[0]
            if e.position == "right":
                nx = x[a] + ACT_W * fs
            elif e.position == "left":
                nx = x[a] - ACT_W * fs - nw
            else:
                lo, hi = min(x[p] for p in e.actors), max(x[p] for p in e.actors)
                nw = max(nw, hi - lo + 2 * NOTE_PAD * fs)
                nx = (lo + hi) / 2 - nw / 2
            y += 0.3 * fs
            notes.append((Box(nx, y, nw, nh), nl))
            extend(nx, nx + nw)
            y += nh + 0.8 * fs
        elif isinstance(e, Fragment):
            y += 0.3 * fs
            open_blocks.append({"e": e, "top": y, "lo": float("inf"), "hi": float("-inf"), "dividers": []})
            y += TAB_H * fs + 0.6 * fs
        elif isinstance(e, Divider):
            open_blocks[-1]["dividers"].append((y, wrap(f"[{e.label}]", lfs, 1e9) if e.label else []))
            y += TAB_H * fs
        elif isinstance(e, End):
            box = _close_block(open_blocks.pop(), y + 0.3 * fs, fs, x, blocks, rects)
            extend(box.x, box.x + box.w)                      # the enclosing blocks wrap this one
            y += 0.9 * fs
    y_end = y + 0.4 * fs
    for p in ids:
        while active[p]:
            close_bar(p, y_end - 0.4 * fs)

    heads = {}
    for p in ids:
        w, h = widths[p], head_h
        heads[p] = (Box(x[p] - w / 2, heads_top, w, h), Box(x[p] - w / 2, y_end, w, h))
    lifelines = {p: (x[p], heads_top + head_h, y_end) for p in ids}
    groups = []
    for g in s.groups:
        if not g.members:
            continue
        lo = min(heads[p][0].x for p in g.members) - 0.6 * fs
        hi = max(heads[p][0].x + heads[p][0].w for p in g.members) + 0.6 * fs
        groups.append((Box(lo, heads_top - 1.6 * fs, hi - lo, y_end + head_h - heads_top + 2.2 * fs),
                       [g.label] if g.label else [], g.color))
    blocks.sort(key=lambda b: b.box.w * b.box.h, reverse=True)       # outermost first
    lay = SequenceLayout(heads, lines, lifelines, messages, activations, notes, blocks, rects, groups, title,
                         0.0, 0.0, fs)
    return _normalised(lay)


def _close_block(b: dict, bottom: float, fs: float, x: dict[str, float], blocks: list, rects: list) -> Box:
    """The block's geometry, added to `blocks` (or `rects`); returns its box."""
    e = b["e"]
    lfs = LABEL * fs
    if b["lo"] == float("inf"):                       # nothing inside: span every lifeline
        b["lo"], b["hi"] = min(x.values()), max(x.values())
    lo, hi = b["lo"] - BLOCK_PAD * fs, b["hi"] + BLOCK_PAD * fs
    tab_w = text_width(e.kind, lfs) + 1.2 * fs
    label = wrap(f"[{e.label}]", lfs, 1e9) if e.label else []
    lw = max((text_width(ln, lfs) for ln in label), default=0.0) + 0.4 * fs
    hi = max(hi, lo + tab_w + (lw + 0.4 * fs if label else 0.0))
    for _, dl in b["dividers"]:
        hi = max(hi, lo + max((text_width(ln, lfs) for ln in dl), default=0.0) + 1.2 * fs)
    box = Box(lo, b["top"], hi - lo, bottom - b["top"])
    if e.kind == "rect":
        rects.append((box, e.color or "EEEEEE"))
        return box
    tab = Box(lo, b["top"], tab_w, TAB_H * fs)
    lab = Box(lo + tab_w + 0.3 * fs, b["top"], lw, TAB_H * fs) if label else None
    dividers = []
    for dy, dl in b["dividers"]:
        dw = max((text_width(ln, lfs) for ln in dl), default=0.0) + 0.4 * fs
        dividers.append((dy, dl, Box(lo + (hi - lo) / 2 - dw / 2, dy + 0.1 * fs, dw, TAB_H * fs - 0.2 * fs)
                         if dl else None))
    blocks.append(BlockGeom(e.kind, label, box, tab, lab, dividers))
    return box


def _normalised(lay: SequenceLayout) -> SequenceLayout:
    boxes = [b for pair in lay.heads.values() for b in pair] + [b for _, b in lay.activations] + \
        [b for b, _ in lay.notes] + [b.box for b in lay.blocks] + [b for b, _ in lay.rects] + \
        [b for b, _, _ in lay.groups] + [b for m in lay.messages for b in (m.label, m.number) if b]
    xs = [v for b in boxes for v in (b.x, b.x + b.w)] + [p[0] for m in lay.messages for p in m.points]
    ys = [v for b in boxes for v in (b.y, b.y + b.h)]
    x0, x1, y0 = min(xs), max(xs), min(ys + [0.0])
    if lay.title:                                   # centred over the diagram
        tb, tl = lay.title
        tw = max(text_width(ln, 1.2 * lay.font_size) for ln in tl) + lay.font_size
        cx = (x0 + x1) / 2
        lay.title = (Box(cx - tw / 2, 0.0, tw, tb.h), tl)
        x0, x1 = min(x0, cx - tw / 2), max(x1, cx + tw / 2)
    width, height = x1 - x0, max(ys) - y0

    def mv(b: Box | None) -> Box | None:
        return Box(b.x - x0, b.y - y0, b.w, b.h) if b else None

    return SequenceLayout(
        {p: (mv(a), mv(b)) for p, (a, b) in lay.heads.items()}, lay.lines,
        {p: (lx - x0, t - y0, u - y0) for p, (lx, t, u) in lay.lifelines.items()},
        [MessageGeom(m.message, [(px - x0, py - y0) for px, py in m.points], mv(m.label), m.lines, mv(m.number),
                     m.index) for m in lay.messages],
        [(p, mv(b)) for p, b in lay.activations], [(mv(b), t) for b, t in lay.notes],
        [BlockGeom(b.kind, b.lines, mv(b.box), mv(b.tab), mv(b.label),
                   [(dy - y0, dl, mv(db)) for dy, dl, db in b.dividers]) for b in lay.blocks],
        [(mv(b), c) for b, c in lay.rects], [(mv(b), t, c) for b, t, c in lay.groups],
        (mv(lay.title[0]), lay.title[1]) if lay.title else None, width, height, lay.font_size)
