"""Sequence diagrams: parser, layout and the written deck."""
import pytest

import mermaid2pptx as m2p
from mermaid2pptx import cli
from mermaid2pptx.sequence import layout, parse
from mermaid2pptx.sequence.model import Activation, Divider, End, Fragment, Note

SRC = """sequenceDiagram
    title Order
    autonumber
    actor C as Customer
    box rgb(240, 240, 255) Shop
    participant W as Web shop
    participant S as Stock
    end
    C->>+W: Order<br>two items
    W->>S: Reserve
    S-->>W: Reserved
    Note right of S: Kept 15 minutes
    alt paid
        W->>W: Confirm
    else card refused
        W--xC: Payment failed
    end
    W-->>-C: Receipt
    Note over C,W: Done
"""


def test_parse():
    s = parse(SRC)
    assert s.title == "Order" and s.autonumber
    assert [(p.id, p.label, p.kind) for p in s.participants.values()] == [
        ("C", "Customer", "actor"), ("W", "Web shop", "participant"), ("S", "Stock", "participant")]
    assert s.groups[0].label == "Shop" and s.groups[0].members == ["W", "S"] and s.groups[0].color == "F0F0FF"
    kinds = [type(e).__name__ for e in s.events]
    assert kinds == ["Message", "Message", "Message", "Note", "Fragment", "Message", "Divider", "Message", "End",
                     "Message", "Note"]
    first = s.events[0]
    assert (first.text, first.activate, first.end) == ("Order\ntwo items", True, "arrow")
    assert s.summary() == "3 participants, 6 messages, 2 notes"


@pytest.mark.parametrize("arrow, line, end, start", [
    ("->", "solid", "none", "none"), ("-->", "dotted", "none", "none"), ("->>", "solid", "arrow", "none"),
    ("-->>", "dotted", "arrow", "none"), ("-x", "solid", "cross", "none"), ("--x", "dotted", "cross", "none"),
    ("-)", "solid", "open", "none"), ("--)", "dotted", "open", "none"), ("<<->>", "solid", "arrow", "arrow"),
    ("<<-->>", "dotted", "arrow", "arrow"),
])
def test_arrows(arrow, line, end, start):
    (m,) = parse(f"sequenceDiagram\nWeb-App{arrow}DB: q").events
    assert (m.src, m.dst, m.line, m.end, m.start) == ("Web-App", "DB", line, end, start)


def test_statements():
    s = parse("sequenceDiagram\nA->>B: hi\nactivate B\nloop daily\nB->>A: x\nend\ndeactivate B\n"
              "par one\nA-)B: a\nand two\nA-)B: b\nend\nrect rgb(200, 220, 255)\nA->B: c\nend\nNote left of A: n")
    assert isinstance(s.events[1], Activation) and s.events[1].on
    assert isinstance(s.events[2], Fragment) and s.events[2].label == "daily"
    assert isinstance(s.events[8], Divider) and s.events[8].kind == "and"
    rect = next(e for e in s.events if isinstance(e, Fragment) and e.kind == "rect")
    assert rect.color == "C8DCFF"
    assert sum(isinstance(e, End) for e in s.events) == 3
    assert isinstance(s.events[-1], Note) and s.events[-1].position == "left"


@pytest.mark.parametrize("src, msg", [
    ("sequenceDiagram\nloop x\nA->>B: y", "missing its 'end'"),
    ("sequenceDiagram\nend", "without a block"),
    ("sequenceDiagram\nelse x", "outside a block"),
    ("sequenceDiagram\nwhat is this", "not a sequence diagram statement"),
    ("sequenceDiagram\n", "no participants"),
])
def test_errors(src, msg):
    with pytest.raises(m2p.MermaidError, match=msg):
        parse(src)


def test_layout():
    s = parse(SRC)
    lay = layout(s)
    xs = {p: lay.lifelines[p][0] for p in s.participants}
    assert xs["C"] < xs["W"] < xs["S"]                                  # declaration order
    tops = [lay.heads[p][0] for p in s.participants]
    for a, b in zip(tops, tops[1:]):
        assert a.x + a.w < b.x                                          # heads never overlap
    ys = [m.points[0][1] for m in lay.messages]
    assert ys == sorted(ys) and len(set(ys)) == len(ys)                 # one row each, top to bottom
    for m in lay.messages:
        if m.label and m.message.src != m.message.dst:                  # the label fits between its ends
            lo, hi = sorted(p[0] for p in m.points)
            assert lo - 0.01 <= m.label.x and m.label.x + m.label.w <= hi + 0.01
    self_msg = next(m for m in lay.messages if m.message.src == m.message.dst)
    assert len(self_msg.points) == 4
    assert [m.index for m in lay.messages] == [1, 2, 3, 4, 5, 6]        # autonumber
    (alt,) = lay.blocks
    for m in lay.messages[3:5]:                                         # inside the alt block
        assert alt.box.y < m.points[0][1] < alt.box.y + alt.box.h
    assert len(alt.dividers) == 1
    (bar,) = [b for p, b in lay.activations if p == "W"]
    assert bar.y == pytest.approx(lay.messages[0].points[0][1])         # from the `+` message...
    assert bar.y + bar.h == pytest.approx(lay.messages[-1].points[0][1])    # ...to the `-` one
    (group, _, color) = lay.groups[0]
    assert group.x < lay.heads["W"][0].x and lay.heads["S"][0].x + lay.heads["S"][0].w < group.x + group.w
    assert lay.width > 0 and lay.height > 0 and min(b.x for b, _ in lay.heads.values()) >= 0


def test_deck(tmp_path):
    prs, s, _ = m2p.convert(SRC)
    out = tmp_path / "seq.pptx"
    prs.save(out)
    (grp,) = m2p.convert(SRC)[0].slides[0].shapes
    names = [sh.name for sh in grp.shapes]
    assert names.count("participant W top") == 1 and names.count("participant W bottom") == 1
    assert "actor C top" in names and names.count("actor icon C") == 4       # head and shoulders, twice
    assert sum(n.startswith("message ") for n in names) == 6
    assert names.index("box") < names.index("participant W top")             # the box band behind
    lifeline = next(sh for sh in grp.shapes if sh.name == "lifeline W")
    ids = {sh.shape_id: sh.name for sh in grp.shapes}
    st = lifeline._element.find(".//{*}stCxn")
    end = lifeline._element.find(".//{*}endCxn")
    assert ids[int(st.get("id"))] == "participant W top" and ids[int(end.get("id"))] == "participant W bottom"


def test_cli(tmp_path, capsys):
    f = tmp_path / "s.mmd"
    f.write_text("sequenceDiagram\nAlice->>Bob: Hi\nBob-->>Alice: Hello", encoding="utf-8")
    assert cli.main([str(f)]) == 0
    assert "2 participants, 2 messages, 0 notes" in capsys.readouterr().out
