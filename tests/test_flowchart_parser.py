"""Flowchart parser: shapes, edges, chains, subgraphs, styles, errors, Markdown blocks."""

import pytest

import mermaid2pptx as m2p
from mermaid2pptx.flowchart import parse
from mermaid2pptx.styles import parse_color
from mermaid2pptx.text import clean_text


# -- parser ----------------------------------------------------------------------------------

def test_shapes_and_labels():
    d = parse("""flowchart LR
        a[rect] --> b(round) --> c([stadium]) --> d[[sub]] --> e[(db)] --> f((circle))
        f --> g{diamond} --> h{{hex}} --> i[/para/] --> j[\\alt\\] --> k[/trap\\] --> l[\\trap alt/]
        l --> m>flag] --> n(((double))) --> o["quoted [brackets] text"]""")
    assert d.direction == "LR"
    shapes = {n.id: n.shape for n in d.nodes.values()}
    assert shapes == {"a": "rect", "b": "round", "c": "stadium", "d": "subroutine", "e": "cylinder",
                      "f": "circle", "g": "diamond", "h": "hexagon", "i": "parallelogram",
                      "j": "parallelogram_alt", "k": "trapezoid", "l": "trapezoid_alt", "m": "flag",
                      "n": "doublecircle", "o": "rect"}
    assert d.nodes["o"].text == "quoted [brackets] text"
    assert len(d.edges) == 14


def test_edge_kinds():
    d = parse("""graph TD
        A --> B
        A --- C
        A -.-> D
        A ==> E
        A ~~~ F
        A <--> G
        A --o H
        A --x I
        A ---> J
        A -- yes --> K
        A -->|no| L
        A -. maybe .-> M
        A == sure ==> N""")
    e = {x.dst: x for x in d.edges}
    assert (e["B"].line, e["B"].end, e["B"].minlen) == ("solid", "arrow", 1)
    assert (e["C"].end, e["C"].minlen) == ("none", 1)
    assert e["D"].line == "dotted" and e["E"].line == "thick" and e["F"].line == "invisible"
    assert (e["G"].start, e["G"].end) == ("arrow", "arrow")
    assert e["H"].end == "circle" and e["I"].end == "cross"
    assert e["J"].minlen == 2
    assert [e[k].text for k in "KLMN"] == ["yes", "no", "maybe", "sure"]
    assert e["M"].line == "dotted" and e["N"].line == "thick"


def test_chains_groups_and_statements():
    d = parse("""---
title: ignored
---
```mermaid
flowchart TB
    %% a comment
    A & B --> C & D; C --> E
```""")
    assert [(e.src, e.dst) for e in d.edges] == [("A", "C"), ("A", "D"), ("B", "C"), ("B", "D"), ("C", "E")]


def test_subgraphs_and_styles():
    d = parse("""flowchart TB
        subgraph outer [Outer box]
            A --> B
            subgraph inner
                C
            end
        end
        B --> C --> D:::hot
        classDef hot fill:#f96,stroke:#333,stroke-width:3px
        classDef default fill:#eee
        class A hot
        style B fill:#00ff00,color:white
        style outer fill:#fafafa
        linkStyle 0 stroke:#ff0000,stroke-width:2px""")
    assert d.path("A") == ("outer",) and d.path("C") == ("outer", "inner") and d.path("D") == ()
    assert d.subgraphs["outer"].title == "Outer box" and d.subgraphs["outer"].style["fill"] == "#fafafa"
    assert d.node_style(d.nodes["D"])["fill"] == "#f96"
    assert d.node_style(d.nodes["A"])["fill"] == "#f96"
    assert d.node_style(d.nodes["C"])["fill"] == "#eee"
    assert parse_color(d.node_style(d.nodes["B"])["color"]) == "FFFFFF"
    assert d.edges[0].style["stroke"] == "#ff0000"


def test_edge_to_subgraph_attaches_to_a_member():
    d = parse("""flowchart LR
        X --> grp
        subgraph grp
            A --> B
        end""")
    assert "grp" not in d.nodes
    assert (d.edges[0].src, d.edges[0].dst) == ("X", "A")
    assert d.warnings


def test_text_cleanup_and_colors():
    assert clean_text('"a<br>b<br/>c #quot;q#quot; &amp; #35;"') == 'a\nb\nc "q" & #'
    assert clean_text('"`**bold** md`"') == "bold md"
    assert parse_color("#abc") == "AABBCC"
    assert parse_color("rgb(255, 0, 16)") == "FF0010"
    assert parse_color("nonsense") is None


@pytest.mark.parametrize("src, msg", [
    ("sequenceDiagram\n A->>B: hi", "only 'flowchart'"),
    ("flowchart TD\n subgraph x\n A", "missing its 'end'"),
    ("flowchart TD\n A[oops --> B", "unclosed shape"),
    ("", "empty"),
])
def test_errors(src, msg):
    with pytest.raises(m2p.MermaidError, match=msg):
        parse(src)


def test_markdown_blocks():
    md = "text\n```mermaid\ngraph TD\nA-->B\n```\nmore\n```mermaid\ngraph LR\nC-->D\n```\n"
    blocks = m2p.extract_blocks(md)
    assert len(blocks) == 2 and "C-->D" in blocks[1]
    assert m2p.extract_blocks("graph TD\nA-->B") == ["graph TD\nA-->B"]
