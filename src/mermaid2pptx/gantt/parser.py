"""Gantt text -> Gantt: settings, sections and tasks, with every date resolved.

A task is `Name : [tags,] [id,] [start,] end`: tags among done/active/crit/milestone; start a
date or `after id1 id2` (the latest of their ends), else the previous task's end; end a date, a
duration (`3d`, `1w`, `12h`) or `until id` (that task's start).
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta

from ..errors import MermaidError
from ..source import statement_lines
from ..text import clean_text
from .dates import DAYS, Calendar, date_parser, is_duration
from .model import Gantt, Task

_TAGS = ("done", "active", "crit", "milestone")
_IGNORED = ("todaymarker", "topaxis", "click", "acctitle", "accdescr", "displaymode")


def parse(src: str) -> Gantt:
    lines = statement_lines(src)
    if not lines or lines[0].split()[0].lower() != "gantt":
        raise MermaidError("not a Gantt chart")
    g = Gantt()
    date_format, excludes, includes, inclusive = "YYYY-MM-DD", [], [], False
    raw: list[tuple[str, str, list[str], str]] = []      # name, section, fields, the line
    section = ""
    for st in lines[1:]:
        word, _, rest = st.partition(" ")
        low = word.lower().rstrip(":")
        rest = rest.strip()
        if low == "title":
            g.title = clean_text(rest)
        elif low == "dateformat":
            date_format = rest
        elif low == "axisformat":
            g.axis_format = rest
        elif low == "tickinterval":
            g.tick_interval = rest
        elif low == "excludes":
            excludes += [x for x in re.split(r"[,\s]+", rest) if x]
        elif low == "includes":
            includes += [x for x in re.split(r"[,\s]+", rest) if x]
        elif low == "weekday" and rest.capitalize() in DAYS:
            g.week_start = DAYS.index(rest.capitalize())
        elif low == "inclusiveenddates":
            inclusive = True
        elif low == "section":
            section = clean_text(rest)
            g.sections.append(section)
        elif low.startswith(_IGNORED):
            continue
        elif ":" in st:
            name, _, meta = st.partition(":")
            raw.append((clean_text(name), section, [f.strip() for f in meta.split(",")], st))
        else:
            raise MermaidError(f"not a Gantt statement: {st}")
    if not raw:
        raise MermaidError("the chart has no tasks")
    if any(not s for _, s, _, _ in raw) and "" not in g.sections:
        g.sections.insert(0, "")                        # tasks before the first section
    parse_date = date_parser(date_format)
    inc = [d.date() for d in (parse_date(x) for x in includes) if d]
    cal = Calendar(excludes, inc)
    g.tasks = _resolve(raw, parse_date, cal, inclusive)
    g.excluded = _excluded_runs(g, cal)
    return g


def _resolve(raw, parse_date, cal: Calendar, inclusive: bool) -> list[Task]:
    specs = []
    for k, (name, section, fields, st) in enumerate(raw):
        tags = set()
        while fields and fields[0].lower() in _TAGS:
            tags.add(fields.pop(0).lower())
        if len(fields) == 3:
            tid, start, end = fields
        elif len(fields) == 2:
            tid, (start, end) = "", fields
        elif len(fields) == 1:
            tid, start, end = "", "", fields[0]
        else:
            raise MermaidError(f"a task has a start and an end at most, in: {st}")
        if tid and (is_duration(tid) or parse_date(tid)):   # `id, 3d` was read as start, end
            raise MermaidError(f"task id {tid!r} looks like a date, in: {st}")
        specs.append(dict(name=name, section=section, id=tid or f"task{k + 1}", start=start, end=end,
                          tags=tags, line=st))
    by_id = {s["id"]: s for s in specs}
    done: dict[str, Task] = {}

    def task(k: int, seen=()) -> Task:
        s = specs[k]
        if s["id"] in done:
            return done[s["id"]]
        if s["id"] in seen:
            raise MermaidError(f"tasks depend on each other in a loop, at {s['id']!r}")
        seen = (*seen, s["id"])

        def ref(tid):
            if tid not in by_id:
                raise MermaidError(f"unknown task id {tid!r} in: {s['line']}")
            return task(specs.index(by_id[tid]), seen)

        if s["start"].lower().startswith("after "):
            start = max(ref(t).end for t in s["start"][6:].split())
        elif s["start"]:
            start = parse_date(s["start"])
            if start is None:
                raise MermaidError(f"cannot read the date {s['start']!r} in: {s['line']}")
        elif k:
            start = task(k - 1, seen).end
        else:
            raise MermaidError(f"the first task needs a start date, in: {s['line']}")
        end_text = s["end"]
        if end_text.lower().startswith("until "):
            end = min(ref(t).start for t in end_text[6:].split())
        elif is_duration(end_text):
            end = cal.add(start, end_text)
        elif (end := parse_date(end_text)) is not None:
            end += timedelta(days=1) if inclusive else timedelta(0)
        else:
            raise MermaidError(f"cannot read the end {end_text!r} (a date, `3d` or `until id`) in: {s['line']}")
        t = done[s["id"]] = Task(s["name"], s["id"], s["section"], start, max(end, start), s["tags"])
        return t

    return [task(k) for k in range(len(specs))]


def _excluded_runs(g: Gantt, cal: Calendar) -> list[tuple[datetime, datetime]]:
    """Runs of excluded days inside the chart, to shade."""
    if not cal:
        return []
    t0 = min(t.start for t in g.tasks).replace(hour=0, minute=0, second=0, microsecond=0)
    t1 = max(t.end for t in g.tasks)
    runs, d = [], t0
    while d < t1 and len(runs) < 200:
        if cal.excluded(d.date()):
            end = d
            while cal.excluded(end.date()):
                end += timedelta(days=1)
            runs.append((d, min(end, t1)))
            d = end
        d += timedelta(days=1)
    return runs
