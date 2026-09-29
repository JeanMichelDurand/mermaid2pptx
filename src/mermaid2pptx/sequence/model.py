"""A parsed sequence diagram: participants, and the events down the page in order."""
from __future__ import annotations

from dataclasses import dataclass, field

from ..text import count


@dataclass
class Participant:
    id: str
    label: str
    kind: str = "participant"           # participant | actor


@dataclass
class Message:
    src: str
    dst: str
    text: str = ""
    line: str = "solid"                 # solid | dotted
    start: str = "none"                 # marker at src: none | arrow
    end: str = "arrow"                  # marker at dst: none | arrow | open | cross
    activate: bool = False              # `+`: activates the receiver
    deactivate: bool = False            # `-`: deactivates the sender


@dataclass
class Note:
    position: str                       # left | right | over
    actors: list[str]
    text: str


@dataclass
class Activation:
    actor: str
    on: bool


@dataclass
class Fragment:
    """Opens a block: loop, alt, opt, par, critical, break, or rect (a coloured background)."""
    kind: str
    label: str
    color: str | None = None            # rect: RRGGBB


@dataclass
class Divider:
    """`else`, `and` or `option`: a new section of the open block."""
    kind: str
    label: str


@dataclass
class End:
    pass


@dataclass
class Group:
    """`box`: participants drawn on one coloured band."""
    label: str
    color: str | None
    members: list[str] = field(default_factory=list)


@dataclass
class Sequence:
    title: str = ""
    participants: dict[str, Participant] = field(default_factory=dict)
    events: list = field(default_factory=list)
    groups: list[Group] = field(default_factory=list)
    autonumber: bool = False
    warnings: list[str] = field(default_factory=list)

    def summary(self) -> str:
        messages = sum(isinstance(e, Message) for e in self.events)
        notes = sum(isinstance(e, Note) for e in self.events)
        return ", ".join((count(len(self.participants), "participant"), count(messages, "message"),
                          count(notes, "note")))
