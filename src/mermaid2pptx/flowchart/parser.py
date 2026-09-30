"""Flowchart text -> Diagram: shapes, edge kinds, chains, subgraphs, classes and styles."""
from __future__ import annotations

import re

from ..errors import MermaidError
from ..source import statement_lines
from ..styles import parse_style
from ..text import clean_text
from .model import Diagram, Edge, Node, Subgraph, ancestors


DIRECTIONS = {"TB": "TB", "TD": "TB", "BT": "BT", "LR": "LR", "RL": "RL",
              "V": "TB", "^": "BT", ">": "LR", "<": "RL"}

_ID = re.compile(r"\w+(?:[-.]\w+)*")
# opener -> [(closer, shape)], longest openers first
_OPENERS = [
    ("(((", [(")))", "doublecircle")]),
    ("((", [("))", "circle")]),
    ("([", [("])", "stadium")]),
    ("[[", [("]]", "subroutine")]),
    ("[(", [(")]", "cylinder")]),
    ("{{", [("}}", "hexagon")]),
    ("[/", [("/]", "parallelogram"), ("\\]", "trapezoid")]),
    ("[\\", [("\\]", "parallelogram_alt"), ("/]", "trapezoid_alt")]),
    ("(", [(")", "round")]),
    ("[", [("]", "rect")]),
    ("{", [("}", "diamond")]),
    (">", [("]", "flag")]),
]
# `A -- text --> B`, `A -. text .-> B`, `A == text ==> B`
_EDGE_TEXT = re.compile(
    r"(?P<l><|[ox](?=[-=]))?(?P<open>--|-\.|==)(?![->.=]|[ox]\s)\s*(?P<text>\S.*?)\s*"
    r"(?P<close>-{2,}[>ox]?|\.+-[>ox]?|={2,}[>ox]?)(?=\s|$|[\w\"])")
# `-->`, `---`, `-.->`, `==>`, `~~~`, `<-->`, `--o`, `--x`, `--->` (longer = more ranks)
_EDGE = re.compile(r"(?P<l><|[ox](?=[-=]))?(?P<body>-{2,}|-\.+-|={2,}|~{3,})(?P<r>>|[ox](?=\s|$))?")
_PIPE = re.compile(r"\s*\|(?P<text>[^|]*)\|")
_MARKERS = {"": "none", None: "none", ">": "arrow", "<": "arrow", "o": "circle", "x": "cross"}


def _split_statements(line: str) -> list[str]:
    """Split on ';' outside quotes and brackets."""
    out, cur, depth, quote = [], [], 0, False
    for ch in line:
        if ch == '"':
            quote = not quote
        elif not quote and ch in "([{":
            depth += 1
        elif not quote and ch in ")]}":
            depth = max(0, depth - 1)
        elif ch == ";" and not quote and depth == 0:
            out.append("".join(cur))
            cur = []
            continue
        cur.append(ch)
    out.append("".join(cur))
    return [s.strip() for s in out if s.strip()]


class _Parser:
    def __init__(self):
        self.d = Diagram()
        self.stack: list[str] = []
        self.explicit: set[str] = set()       # ids given a label or shape somewhere
        self.sg_counter = 0

    # -- statements -------------------------------------------------------------------------
    def parse(self, src: str) -> Diagram:
        stmts = [s for ln in statement_lines(src) for s in _split_statements(ln)]
        if not stmts:
            raise MermaidError("empty diagram")
        m = re.fullmatch(r"(flowchart|graph)(?:\s+(\S+))?", stmts[0], re.I)
        if not m:
            kind = stmts[0].split()[0]
            raise MermaidError(f"only 'flowchart'/'graph' diagrams are supported, not {kind!r}")
        if m[2]:
            if m[2].upper() not in DIRECTIONS:
                raise MermaidError(f"unknown direction {m[2]!r}")
            self.d.direction = DIRECTIONS[m[2].upper()]
        for st in stmts[1:]:
            try:
                self.statement(st)
            except MermaidError as exc:
                raise MermaidError(f"{exc} in: {st}") from None
        if self.stack:
            raise MermaidError(f"subgraph {self.stack[-1]!r} is missing its 'end'")
        self.resolve_subgraph_endpoints()
        return self.d

    def statement(self, st: str):
        word = st.split(None, 1)[0]
        low = word.lower()
        rest = st[len(word):].strip()
        if low == "subgraph":
            self.subgraph(rest)
        elif low == "end" and not rest:
            if not self.stack:
                raise MermaidError("'end' without subgraph")
            self.stack.pop()
        elif low == "direction" or low in ("click", "call", "href") or low.startswith(("acctitle", "accdescr")):
            return
        elif low == "classdef":
            names, _, spec = rest.partition(" ")
            for name in names.split(","):
                self.d.class_defs.setdefault(name.strip(), {}).update(parse_style(spec))
        elif low == "class":
            ids, _, cls = rest.rpartition(" ")
            for nid in ids.split(","):
                self.touch(nid.strip()).classes.append(cls.strip())
        elif low == "style":
            nid, _, spec = rest.partition(" ")
            target = self.d.subgraphs.get(nid) or self.touch(nid.strip())
            target.style.update(parse_style(spec))
        elif low == "linkstyle":
            which, _, spec = rest.partition(" ")
            idx = range(len(self.d.edges)) if which == "default" else \
                [int(i) for i in which.split(",") if i.strip().isdigit()]
            for i in idx:
                if i < len(self.d.edges):
                    self.d.edges[i].style.update(parse_style(spec))
        else:
            self.chain(st)

    def subgraph(self, rest: str):
        if m := re.fullmatch(r"(\w[\w.-]*)\s*\[(.*)\]", rest):
            sid, title = m[1], clean_text(m[2])
        elif rest.startswith('"'):
            self.sg_counter += 1
            sid, title = f"subGraph{self.sg_counter}", clean_text(rest)
        elif rest and " " not in rest:
            sid = title = rest
        else:
            self.sg_counter += 1
            sid, title = (rest if rest else f"subGraph{self.sg_counter}"), clean_text(rest)
        self.d.subgraphs[sid] = Subgraph(sid, title, self.stack[-1] if self.stack else None)
        self.stack.append(sid)

    # -- chains: A[x] --> B & C -->|y| D ----------------------------------------------------
    def chain(self, st: str):
        i = 0
        group, i = self.group(st, i)
        while True:
            i = _skip_ws(st, i)
            if i >= len(st):
                return
            edge, i = self.edge(st, i)
            i = _skip_ws(st, i)
            nxt, i = self.group(st, i)
            for a in group:
                for b in nxt:
                    self.d.edges.append(Edge(a, b, edge["text"], edge["line"], edge["start"],
                                             edge["end"], edge["minlen"]))
            group = nxt

    def group(self, st: str, i: int) -> tuple[list[str], int]:
        ids = []
        while True:
            nid, i = self.node(st, _skip_ws(st, i))
            ids.append(nid)
            j = _skip_ws(st, i)
            if j < len(st) and st[j] == "&":
                i = j + 1
                continue
            return ids, i

    def node(self, st: str, i: int) -> tuple[str, int]:
        m = _ID.match(st, i)
        if not m:
            raise MermaidError(f"expected a node id at {st[i:i + 20]!r}")
        nid, i = m[0], m.end()
        text = shape = None
        for opener, closers in _OPENERS:
            if not st.startswith(opener, i):
                continue
            j = i + len(opener)
            if j < len(st) and st[j] == '"':
                q = st.find('"', j + 1)
                if q < 0:
                    raise MermaidError("unterminated string")
                text, k = st[j + 1:q], q + 1
                hits = [(k, c, s) for c, s in closers if st.startswith(c, k)]
            else:
                hits = sorted((st.find(c, j), c, s) for c, s in closers if st.find(c, j) >= 0)
                if hits:
                    text = st[j:hits[0][0]]
            if not hits:
                raise MermaidError(f"unclosed shape {opener!r} for node {nid!r}")
            k, closer, shape = hits[0]
            i = k + len(closer)
            break
        classes = []
        while st.startswith(":::", i):
            m = _ID.match(st, i + 3)
            if not m:
                break
            classes.append(m[0])
            i = m.end()
        node = self.touch(nid)
        if text is not None:
            node.text = clean_text(text)
            self.explicit.add(nid)
        if shape:
            node.shape = shape
            self.explicit.add(nid)
        node.classes += classes
        return nid, i

    def edge(self, st: str, i: int) -> tuple[dict, int]:
        if m := _EDGE_TEXT.match(st, i):
            close = m["close"]
            head = close[-1] if close[-1] in ">ox" else ""
            body = close[:-1] if head else close
            text, kind = clean_text(m["text"]), m["open"]
            end = m.end()
        elif m := _EDGE.match(st, i):
            head, body, kind, text, end = m["r"] or "", m["body"], m["body"], "", m.end()
        else:
            raise MermaidError(f"expected an edge at {st[i:i + 20]!r}")
        if p := _PIPE.match(st, end):
            text, end = clean_text(p["text"]), p.end()
        left = m["l"] or ""
        if "." in kind:
            line, minlen = "dotted", body.count(".")
        elif kind.startswith("~"):
            line, minlen = "invisible", 1
        else:           # `-->`/`==>` is 1 rank, `---`/`===` too; each extra dash adds one
            line = "thick" if kind.startswith("=") else "solid"
            minlen = len(body) - (1 if head or (left and m.re is _EDGE) else 2)
        return dict(text=text, line=line, start=_MARKERS[left], end=_MARKERS[head],
                    minlen=max(1, minlen)), end

    # -- nodes ------------------------------------------------------------------------------
    def touch(self, nid: str) -> Node:
        node = self.d.nodes.get(nid)
        if node is None:
            node = self.d.nodes[nid] = Node(nid, nid)
        if self.stack and node.cluster is None and nid not in self.d.subgraphs:
            node.cluster = self.stack[-1]
        return node

    def resolve_subgraph_endpoints(self):
        """`A --> subgraphId`: mermaid draws to the cluster; we attach to its first/last node."""
        d = self.d
        for sid in d.subgraphs:
            if sid in d.nodes and sid not in self.explicit:
                del d.nodes[sid]

        def members(sid):
            subs = {s for s in d.subgraphs if s == sid or sid in ancestors(d, s)}
            return [n for n, node in d.nodes.items() if node.cluster in subs]

        kept = []
        for e in d.edges:
            ok = True
            for attr, pick in (("src", -1), ("dst", 0)):
                sid = getattr(e, attr)
                if sid in d.subgraphs and sid not in d.nodes:
                    ms = members(sid)
                    if not ms:
                        d.warnings.append(f"edge to empty subgraph {sid!r} dropped")
                        ok = False
                        break
                    setattr(e, attr, ms[pick])
                    d.warnings.append(f"edge to subgraph {sid!r} attached to node {ms[pick]!r}")
            if ok:
                kept.append(e)
        d.edges = kept



def _skip_ws(s: str, i: int) -> int:
    while i < len(s) and s[i].isspace():
        i += 1
    return i


def parse(src: str) -> Diagram:
    return _Parser().parse(src)
