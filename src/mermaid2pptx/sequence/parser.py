"""Sequence diagram text -> Sequence: participants, messages, notes, activations and blocks."""
from __future__ import annotations

import re

from ..errors import MermaidError
from ..source import statement_lines
from ..styles import parse_color
from ..text import clean_text
from .model import Activation, Divider, End, Fragment, Group, Message, Note, Participant, Sequence

_ARROW = r"<<-->>|<<->>|-->>|->>|--x|-x|--\)|-\)|-->|->"
_MESSAGE = re.compile(rf"(?P<src>.+?)\s*(?P<arrow>{_ARROW})\s*(?P<act>[+-])?\s*(?P<dst>[^:]+?)\s*(?::(?P<text>.*))?")
_PARTICIPANT = re.compile(r"(?:create\s+)?(?P<kind>participant|actor)\s+(?P<id>[^\s@]+)(?:@\{.*\})?"
                          r"(?:\s+as\s+(?P<label>.+))?", re.I)
_NOTE = re.compile(r"note\s+(?P<pos>left of|right of|over)\s+(?P<who>[^:]+?)\s*:(?P<text>.*)", re.I)
_BLOCKS = ("loop", "alt", "opt", "par", "critical", "break", "rect")
_DIVIDERS = {"else": "alt", "and": "par", "option": "critical"}
_IGNORED = ("acctitle", "accdescr", "links", "link", "properties", "details")


def _arrow(arrow: str) -> dict:
    dotted = arrow.lstrip("<").startswith("--")
    head = {">>": "arrow", "x": "cross", ")": "open"}.get(arrow[-2:] if arrow.endswith(">>") else arrow[-1], "none")
    return dict(line="dotted" if dotted else "solid", end=head, start="arrow" if arrow.startswith("<<") else "none")


class _Parser:
    def __init__(self):
        self.s = Sequence()
        self.stack: list[str] = []          # open blocks and boxes, innermost last
        self.group: Group | None = None

    def parse(self, src: str) -> Sequence:
        lines = statement_lines(src)
        if not lines or lines[0].split()[0].lower() != "sequencediagram":
            raise MermaidError("not a sequence diagram")
        for st in lines[1:]:
            try:
                self.statement(st)
            except MermaidError as exc:
                raise MermaidError(f"{exc} in: {st}") from None
        if self.stack:
            raise MermaidError(f"'{self.stack[-1]}' is missing its 'end'")
        if not self.s.participants:
            raise MermaidError("the diagram has no participants")
        return self.s

    def statement(self, st: str):
        word = st.split(None, 1)[0].lower().rstrip(":")
        rest = st[len(word):].strip().lstrip(":").strip() if " " in st or ":" in st else ""
        s = self.s
        if word == "title":
            s.title = clean_text(rest)
        elif word == "autonumber":
            s.autonumber = rest.lower() != "off"
        elif word in ("activate", "deactivate"):
            s.events.append(Activation(self.touch(rest).id, word == "activate"))
        elif word == "destroy":
            s.warnings.append(f"'destroy {rest}' ignored: the participant is drawn to the end")
        elif word.startswith(_IGNORED):
            return
        elif word == "box":
            self.box(rest)
        elif word in _BLOCKS:
            color = parse_color(rest) if word == "rect" else None
            s.events.append(Fragment(word, "" if word == "rect" else clean_text(rest), color))
            self.stack.append(word)
        elif word in _DIVIDERS:
            if not self.stack or self.stack[-1] in ("box", "rect"):
                raise MermaidError(f"'{word}' outside a block")
            s.events.append(Divider(word, clean_text(rest)))
        elif word == "end" and not rest:
            if not self.stack:
                raise MermaidError("'end' without a block")
            if self.stack.pop() == "box":
                self.group = None
            else:
                s.events.append(End())
        elif m := _PARTICIPANT.fullmatch(st):
            p = self.touch(m["id"])
            p.kind = m["kind"].lower()
            if m["label"]:
                p.label = clean_text(m["label"])
        elif m := _NOTE.fullmatch(st):
            who = [self.touch(a.strip()).id for a in m["who"].split(",")]
            s.events.append(Note(m["pos"].split()[0].lower(), who, clean_text(m["text"])))
        elif m := _MESSAGE.fullmatch(st):
            a, b = self.touch(m["src"].strip()), self.touch(m["dst"].strip())
            s.events.append(Message(a.id, b.id, clean_text(m["text"] or ""), **_arrow(m["arrow"]),
                                    activate=m["act"] == "+", deactivate=m["act"] == "-"))
        else:
            raise MermaidError("not a sequence diagram statement")

    def box(self, rest: str):
        color, label = None, rest
        if m := re.match(r"(rgba?\([^)]*\)|#\w+|\w+)\s*(.*)", rest):
            if m[1].lower() == "transparent":
                label = m[2]
            elif (c := parse_color(m[1])) is not None:
                color, label = c, m[2]
        self.group = Group(clean_text(label), color)
        self.s.groups.append(self.group)
        self.stack.append("box")

    def touch(self, pid: str) -> Participant:
        if not pid:
            raise MermaidError("missing participant")
        p = self.s.participants.get(pid)
        if p is None:
            p = self.s.participants[pid] = Participant(pid, pid)
            if self.group is not None:
                self.group.members.append(pid)
        return p


def parse(src: str) -> Sequence:
    return _Parser().parse(src)
