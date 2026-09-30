"""Diagrams shared by the tests."""
from pathlib import Path

import pytest

from mermaid2pptx.flowchart import parse, to_bpmn

ALL_EXAMPLES = sorted((Path(__file__).parent.parent / "examples").glob("*.mmd"))
EXAMPLES = [p for p in ALL_EXAMPLES if p.read_text(encoding="utf-8").lstrip().startswith(("flowchart", "graph"))]


def examples():
    for path in EXAMPLES:
        for direction in ("TB", "BT", "LR", "RL"):
            for render in ("bpmn", "mermaid"):
                yield pytest.param(path, direction, render, id=f"{path.stem}-{direction}-{render}")


def diagram(path, direction, render):
    d = parse(path.read_text())
    d.direction = direction
    return to_bpmn(d) if render == "bpmn" else d


LANES_SRC = """graph TD
    subgraph U["👤 Client"]
        S(( )) --> A["👤 Demande"]
    end
    subgraph T[Outil]
        B{Type ?}
        subgraph N[Nested]
            C[Ticket]
        end
    end
    subgraph P[Support]
        D[Traitement] --> E(( ))
        D --> D
    end
    A --> B
    B -->|incident| C
    B -->|demande| D
    C --> D
    D --> A
"""
