"""A parsed flowchart: nodes, edges, subgraphs and their styles."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Node:
    id: str
    text: str
    shape: str = "rect"
    classes: list[str] = field(default_factory=list)
    style: dict[str, str] = field(default_factory=dict)
    cluster: str | None = None          # innermost subgraph id
    icon: str | None = None             # bpmn: "user" (a leading 👤 in the text)


@dataclass
class Edge:
    src: str
    dst: str
    text: str = ""
    line: str = "solid"                 # solid | dotted | thick | invisible
    start: str = "none"                 # marker at src: none | arrow | circle | cross
    end: str = "arrow"                  # marker at dst
    minlen: int = 1
    style: dict[str, str] = field(default_factory=dict)


@dataclass
class Subgraph:
    id: str
    title: str
    parent: str | None
    style: dict[str, str] = field(default_factory=dict)
    icon: str | None = None


@dataclass
class Diagram:
    direction: str = "TB"
    nodes: dict[str, Node] = field(default_factory=dict)
    edges: list[Edge] = field(default_factory=list)
    subgraphs: dict[str, Subgraph] = field(default_factory=dict)
    class_defs: dict[str, dict[str, str]] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    lanes: list[str] = field(default_factory=list)      # bpmn: top-level subgraphs drawn as lanes

    def path(self, node_id: str) -> tuple[str, ...]:
        """Subgraph ids enclosing the node, outermost first."""
        out, sg = [], self.nodes[node_id].cluster
        while sg:
            out.append(sg)
            sg = self.subgraphs[sg].parent
        return tuple(reversed(out))

    def summary(self) -> str:
        return f"{len(self.nodes)} nodes, {len(self.edges)} edges, {len(self.subgraphs)} subgraphs"

    def node_style(self, node: Node) -> dict[str, str]:
        style = dict(self.class_defs.get("default", {}))
        for cls in node.classes:
            style.update(self.class_defs.get(cls, {}))
        style.update(node.style)
        return style


def ancestors(d: Diagram, sid: str) -> list[str]:
    """Subgraph ids enclosing subgraph `sid`, innermost first."""
    out, p = [], d.subgraphs[sid].parent
    while p:
        out.append(p)
        p = d.subgraphs[p].parent
    return out
