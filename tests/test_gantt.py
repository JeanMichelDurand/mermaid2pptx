"""Gantt charts: dates, the parser's resolution of starts and ends, layout and the written deck."""
from datetime import datetime

import pytest

import mermaid2pptx as m2p
from mermaid2pptx.gantt import layout, parse
from mermaid2pptx.gantt.dates import Calendar, date_parser, strftime, ticks

SRC = """gantt
    title Plan
    dateFormat YYYY-MM-DD
    axisFormat %d %b
    excludes weekends
    section Prepare
    Write the brief   :done, brief, 2026-03-02, 3d
    Review it         :active, review, after brief, 2d
    section Deliver
    Build             :crit, build, 2026-03-09, 1w
    Test              :2d
    Go live           :milestone, live, after build, 0d
    Handover          :handover, 2026-03-09, until live
"""


def d(s):
    return datetime.fromisoformat(s)


def test_date_formats():
    assert date_parser("YYYY-MM-DD")("2026-03-02") == d("2026-03-02")
    assert date_parser("DD/MM/YYYY HH:mm")("05/03/2026 14:30") == d("2026-03-05T14:30")
    assert date_parser("D MMM YY")("5 Mar 26") == d("2026-03-05")
    assert date_parser("YYYY-MM-DD")("2026-03-05T08:00") == d("2026-03-05T08:00")     # ISO fallback
    assert date_parser("YYYY-MM-DD")("tomorrow") is None
    assert strftime(d("2026-03-05T14:07"), "%a %e %B %Y, %H:%M %%") == "Thu 5 March 2026, 14:07 %"


def test_durations_skip_excluded_days():
    cal = Calendar(["weekends", "2026-03-10"], [])
    assert cal.add(d("2026-03-05"), "2d") == d("2026-03-09")      # Thu, Fri; the weekend pushes the end
    assert cal.add(d("2026-03-09"), "2d") == d("2026-03-12")      # Mon, (Tue excluded), Wed
    assert Calendar([], []).add(d("2026-03-05"), "36h") == d("2026-03-06T12:00")
    assert Calendar([], []).add(d("2026-01-31"), "1M") == d("2026-02-28")


def test_ticks():
    week = ticks(d("2026-03-04"), d("2026-04-20"))
    assert all(t.weekday() == 0 for t in week) and len(week) <= 12        # Mondays
    assert ticks(d("2026-03-04T10:00"), d("2026-03-14"))[0] == d("2026-03-05")   # daily, at midnight
    assert [t.hour for t in ticks(d("2026-03-04T10:00"), d("2026-03-06"))][:3] == [12, 18, 0]   # every 6 hours
    months = ticks(d("2026-01-15"), d("2026-12-01"), "1month")
    assert [t.month for t in months] == list(range(2, 13)) and all(t.day == 1 for t in months)


def test_parse_resolves_every_date():
    g = parse(SRC)
    t = {x.id: x for x in g.tasks}
    assert g.sections == ["Prepare", "Deliver"] and g.title == "Plan"
    assert (t["brief"].start, t["brief"].end) == (d("2026-03-02"), d("2026-03-05"))
    assert t["review"].start == t["brief"].end and t["review"].end == d("2026-03-09")    # over the weekend
    assert t["build"].tags == {"crit"}
    test = g.tasks[3]
    assert test.name == "Test" and test.start == t["build"].end                          # follows the previous
    assert t["live"].milestone and t["live"].start == t["build"].end
    assert t["handover"].end == t["live"].start                                          # until
    assert g.summary() == "2 sections, 5 tasks, 1 milestone"
    assert g.excluded and all(a.weekday() == 5 for a, _ in g.excluded)


@pytest.mark.parametrize("src, msg", [
    ("gantt\nsection A", "no tasks"),
    ("gantt\nA :3d", "first task needs a start"),
    ("gantt\nA :a, 2026-01-01, 2d\nB :after zz, 1d", "unknown task id"),
    ("gantt\nA :a, after b, 1d\nB :b, after a, 1d", "loop"),
    ("gantt\nA :a, 2026-01-01, soon", "cannot read the end"),
    ("gantt\nthis is not a task", "not a Gantt statement"),
])
def test_errors(src, msg):
    with pytest.raises(m2p.MermaidError, match=msg):
        parse(src)


def test_layout():
    g = parse(SRC)
    lay = layout(g)
    bars = {b.task.id: b for b in lay.bars}
    rows = [b.box.cy for b in lay.bars]
    assert rows == sorted(rows) and len(set(rows)) == len(rows)            # one row per task, in order
    assert bars["review"].box.x == pytest.approx(bars["brief"].box.x + bars["brief"].box.w)
    assert bars["live"].box.w == bars["live"].box.h                         # a diamond
    for b in lay.bars:                                                      # every task inside its section band
        (band,) = [bd for s, bd, _, _ in lay.sections if s == b.task.section]
        assert band.y <= b.box.y and b.box.y + b.box.h <= band.y + band.h
        if not b.inside:                                                    # a name beside its bar never covers it
            assert b.label.x >= b.box.x + b.box.w - 0.01 or b.label.x + b.label.w <= b.box.x + 0.01
    xs = [x for x, _ in lay.ticks]
    assert xs == sorted(xs) and [s for _, s in lay.ticks][0].endswith("Mar")
    assert min(b.box.x for b in lay.bars) >= 0 and lay.width > 0 and lay.height > 0


@pytest.mark.parametrize("color", ["purple", "slate", "theme", "#00A0B0"])
def test_deck(color):
    prs, g, _ = m2p.convert(SRC, m2p.Options(color=color))
    (grp,) = prs.slides[0].shapes
    names = [s.name for s in grp.shapes]
    assert [n for n in names if n.startswith(("task ", "milestone "))] == [f"{'milestone' if t.milestone else 'task'} "
                                                                             f"{t.id}" for t in g.tasks]
    assert names.index("section Prepare") < names.index("task brief")       # bands behind the bars
    assert sum(n.startswith("grid ") for n in names) == sum(n.startswith("tick ") for n in names) > 0
