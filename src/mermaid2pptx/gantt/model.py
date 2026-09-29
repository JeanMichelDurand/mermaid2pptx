"""A parsed Gantt chart: sections of tasks with resolved start and end dates."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from ..text import count


@dataclass
class Task:
    name: str
    id: str
    section: str
    start: datetime
    end: datetime
    tags: set[str] = field(default_factory=set)       # done, active, crit, milestone

    @property
    def milestone(self) -> bool:
        return "milestone" in self.tags


@dataclass
class Gantt:
    title: str = ""
    sections: list[str] = field(default_factory=list)
    tasks: list[Task] = field(default_factory=list)
    axis_format: str = "%Y-%m-%d"
    tick_interval: str | None = None
    week_start: int = 0                                # Monday
    excluded: list[tuple[datetime, datetime]] = field(default_factory=list)   # runs of excluded days
    warnings: list[str] = field(default_factory=list)

    def summary(self) -> str:
        milestones = sum(t.milestone for t in self.tasks)
        named = sum(1 for s in self.sections if s)          # "" holds the tasks before any section
        return ", ".join((count(named, "section"), count(len(self.tasks) - milestones, "task"),
                          count(milestones, "milestone")))
