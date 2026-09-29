"""Dates for Gantt charts: Mermaid's `dateFormat` (dayjs tokens), durations, excluded days,
axis ticks and `axisFormat` (d3 / strftime directives, English names on every OS)."""
from __future__ import annotations

import calendar
import re
from datetime import date, datetime, timedelta

MONTHS = [calendar.month_name[i] for i in range(1, 13)]
DAYS = [calendar.day_name[i] for i in range(7)]          # Monday first, like date.weekday()

# dayjs parse tokens, longest first
_TOKENS = [("YYYY", r"(?P<Y>\d{4})"), ("YY", r"(?P<y>\d{2})"), ("MMMM", r"(?P<B>[A-Za-z]+)"),
           ("MMM", r"(?P<b>[A-Za-z]{3})"), ("MM", r"(?P<M>\d{2})"), ("M", r"(?P<M>\d{1,2})"),
           ("DD", r"(?P<D>\d{2})"), ("Do", r"(?P<D>\d{1,2})(?:st|nd|rd|th)"), ("D", r"(?P<D>\d{1,2})"),
           ("HH", r"(?P<H>\d{2})"), ("H", r"(?P<H>\d{1,2})"), ("mm", r"(?P<m>\d{2})"), ("m", r"(?P<m>\d{1,2})"),
           ("ss", r"(?P<s>\d{2})"), ("s", r"(?P<s>\d{1,2})"), ("X", r"(?P<X>\d+(?:\.\d+)?)"), ("x", r"(?P<x>\d+)")]
_UNITS = {"ms": timedelta(milliseconds=1), "s": timedelta(seconds=1), "m": timedelta(minutes=1),
          "h": timedelta(hours=1), "d": timedelta(days=1), "w": timedelta(weeks=1)}
_DURATION = re.compile(r"(\d+(?:\.\d+)?)\s*(ms|s|m|h|d|w|M|y)")


def date_parser(fmt: str):
    """A function reading a date written in the dayjs format `fmt`; None when it does not match."""
    pattern, i = "", 0
    while i < len(fmt):
        tok = next((t for t in _TOKENS if fmt.startswith(t[0], i)), None)
        if tok and f"(?P<{tok[1][4]}>" not in pattern:
            pattern += tok[1]
            i += len(tok[0])
        else:
            pattern += re.escape(fmt[i])
            i += 1
    rx = re.compile(pattern)

    def parse(text: str) -> datetime | None:
        m = rx.fullmatch(text.strip())
        if not m:
            try:                            # Mermaid falls back on the browser's own reading
                return datetime.fromisoformat(text.strip())
            except ValueError:
                return None
        g = m.groupdict()
        if g.get("X"):
            return datetime.fromtimestamp(float(g["X"]))
        if g.get("x"):
            return datetime.fromtimestamp(int(g["x"]) / 1000)
        year = int(g["Y"]) if g.get("Y") else 2000 + int(g["y"]) if g.get("y") else 1970
        month = int(g["M"]) if g.get("M") else _month(g.get("B") or g.get("b")) if (g.get("B") or g.get("b")) else 1
        try:
            return datetime(year, month, int(g.get("D") or 1), int(g.get("H") or 0), int(g.get("m") or 0),
                            int(g.get("s") or 0))
        except ValueError:
            return None
    return parse


def _month(name: str) -> int:
    return next((i + 1 for i, m in enumerate(MONTHS) if m.lower().startswith(name.lower()[:3])), 1)


def is_duration(text: str) -> bool:
    return _DURATION.fullmatch(text.strip()) is not None


class Calendar:
    """Working days: `excludes weekends`, `excludes friday, 2024-12-25`, and `includes` exceptions."""

    def __init__(self, excludes: list[str], includes: list[date], weekend: tuple[int, int] = (5, 6)):
        self.days: set[int] = set()
        self.dates: set[date] = set()
        self.includes = set(includes)
        for item in excludes:
            low = item.strip().lower()
            if low == "weekends":
                self.days |= set(weekend)
            elif low.capitalize() in DAYS:
                self.days.add(DAYS.index(low.capitalize()))
            elif (d := date_parser("YYYY-MM-DD")(item)) is not None:
                self.dates.add(d.date())

    def excluded(self, d: date) -> bool:
        return d not in self.includes and (d.weekday() in self.days or d in self.dates)

    def __bool__(self):
        return bool(self.days or self.dates)

    def add(self, start: datetime, text: str) -> datetime:
        """`start` + the duration `text`; a duration in days or weeks skips the excluded days."""
        n, unit = _DURATION.fullmatch(text.strip()).groups()
        n = float(n)
        if unit == "M":
            return _add_months(start, int(n))
        if unit == "y":
            return _add_months(start, 12 * int(n))
        if unit in ("d", "w") and self:
            days, end = n * (7 if unit == "w" else 1), start
            while days > 0:
                if not self.excluded(end.date()):
                    days -= 1
                end += timedelta(days=1)
            while self.excluded(end.date()) and end > start:         # never end on an excluded day
                end += timedelta(days=1)
            return end
        return start + n * _UNITS[unit]


def _add_months(d: datetime, n: int) -> datetime:
    y, m = divmod(d.month - 1 + n, 12)
    year, month = d.year + y, m + 1
    return d.replace(year=year, month=month, day=min(d.day, calendar.monthrange(year, month)[1]))


# tick intervals, finest first: (count, unit)
_STEPS = [(1, "hour"), (3, "hour"), (6, "hour"), (12, "hour"), (1, "day"), (2, "day"), (1, "week"), (2, "week"),
          (1, "month"), (3, "month"), (6, "month"), (1, "year"), (5, "year")]
_TICK = re.compile(r"(\d+)\s*(millisecond|second|minute|hour|day|week|month|year)s?")


def ticks(t0: datetime, t1: datetime, interval: str | None = None, week_start: int = 0,
          most: int = 12) -> list[datetime]:
    """Tick dates in [t0, t1]: every `interval` (`1week`, Mermaid's tickInterval) or the finest step
    giving at most `most` ticks. Days start at midnight, weeks on `week_start`, months on the 1st."""
    span = (t1 - t0).total_seconds()
    if interval and (m := _TICK.fullmatch(interval.strip())):
        step = (int(m[1]), m[2])
    else:
        rough = {"hour": 3600, "day": 86400, "week": 7 * 86400, "month": 30.4 * 86400, "year": 365.25 * 86400}
        step = next((s for s in _STEPS if span / (s[0] * rough[s[1]]) <= most), _STEPS[-1])
    n, unit = step
    t = t0.replace(microsecond=0)
    if unit in ("day", "week", "month", "year"):
        t = t.replace(hour=0, minute=0, second=0)
    if unit == "week":
        t -= timedelta(days=(t.weekday() - week_start) % 7)
    elif unit == "month":
        t = t.replace(day=1)
    elif unit == "year":
        t = t.replace(month=1, day=1)
    elif unit == "hour":                     # every 6 hours: 00:00, 06:00, 12:00...
        t = t.replace(hour=t.hour - t.hour % n, minute=0, second=0)
    out = []
    while t <= t1 and len(out) < 500:
        if t >= t0:
            out.append(t)
        if unit in ("month", "year"):
            t = _add_months(t, n * (12 if unit == "year" else 1))
        else:
            t += n * {"millisecond": timedelta(milliseconds=1), "second": timedelta(seconds=1),
                      "minute": timedelta(minutes=1), "hour": timedelta(hours=1), "day": timedelta(days=1),
                      "week": timedelta(weeks=1)}[unit]
    return out


def strftime(d: datetime, fmt: str) -> str:
    """d3-style `axisFormat`: %Y %y %m %d %e %b %B %a %A %H %I %M %S %p %j %U %W %%, English names."""
    def one(m):
        c = m[1]
        return {
            "Y": f"{d.year}", "y": f"{d.year % 100:02d}", "m": f"{d.month:02d}", "d": f"{d.day:02d}",
            "e": f"{d.day:>2}".strip(), "b": MONTHS[d.month - 1][:3], "B": MONTHS[d.month - 1],
            "a": DAYS[d.weekday()][:3], "A": DAYS[d.weekday()], "H": f"{d.hour:02d}",
            "I": f"{(d.hour - 1) % 12 + 1:02d}", "M": f"{d.minute:02d}", "S": f"{d.second:02d}",
            "p": "AM" if d.hour < 12 else "PM", "j": f"{d.timetuple().tm_yday:03d}",
            "U": d.strftime("%U"), "W": d.strftime("%W"), "%": "%",
        }.get(c, m[0])
    return re.sub(r"%-?([a-zA-Z%])", one, fmt)
