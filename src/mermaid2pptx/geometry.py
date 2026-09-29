"""A box on the page, in points, y down: what every layout produces."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Box:
    x: float
    y: float
    w: float
    h: float
    core: float = 0.0       # flowchart: side of the drawn symbol when its text sits outside it

    @property
    def cx(self):
        return self.x + self.w / 2

    @property
    def cy(self):
        return self.y + self.h / 2
