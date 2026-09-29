"""CSS-like Mermaid styles (`style`, `classDef`, `linkStyle`) and colours."""
import re

_NAMED_COLORS = {
    "white": "FFFFFF", "black": "000000", "red": "FF0000", "green": "008000", "blue": "0000FF",
    "yellow": "FFFF00", "orange": "FFA500", "purple": "800080", "gray": "808080", "grey": "808080",
    "lightgray": "D3D3D3", "lightgrey": "D3D3D3", "darkgray": "A9A9A9", "pink": "FFC0CB",
    "lightblue": "ADD8E6", "lightgreen": "90EE90", "navy": "000080", "teal": "008080",
}


def parse_color(value: str) -> str | None:
    v = value.strip().lower()
    if m := re.fullmatch(r"#([0-9a-f]{3})", v):
        return "".join(c * 2 for c in m[1]).upper()
    if m := re.fullmatch(r"#([0-9a-f]{6})([0-9a-f]{2})?", v):
        return m[1].upper()
    if m := re.fullmatch(r"rgba?\((\d+)\s*,\s*(\d+)\s*,\s*(\d+).*\)", v):
        return "".join(f"{min(int(x), 255):02X}" for x in m.groups())
    return _NAMED_COLORS.get(v)


def parse_style(spec: str) -> dict[str, str]:
    out = {}
    for part in re.split(r",(?![^(]*\))", spec):
        if ":" in part:
            k, v = part.split(":", 1)
            out[k.strip().lower()] = v.strip().rstrip(";")
    return out


def contrast(rgb: str) -> str:
    r, g, b = (int(rgb[k:k + 2], 16) for k in (0, 2, 4))
    return "0F172A" if 0.299 * r + 0.587 * g + 0.114 * b > 150 else "FFFFFF"


def dashed(style: dict[str, str]) -> bool:
    """stroke-dasharray with a non-zero dash (`0` and `none` mean a solid line)."""
    return bool(re.search(r"[1-9]", style.get("stroke-dasharray", "")))


def px_to_pt(v: str) -> float | None:
    m = re.match(r"([\d.]+)\s*(px|pt)?", v)
    if not m:
        return None
    return float(m[1]) * (0.75 if (m[2] or "px") == "px" else 1.0)
