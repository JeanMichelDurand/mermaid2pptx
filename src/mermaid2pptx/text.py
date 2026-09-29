"""Label text: Mermaid markup to plain lines, and a width estimate to size boxes without a font."""
import html
import re


def clean_text(text: str) -> str:
    """Mermaid label -> plain text with '\\n' line breaks."""
    t = text.strip()
    if len(t) >= 2 and t[0] == t[-1] == '"':
        t = t[1:-1]
    if len(t) >= 2 and t[0] == t[-1] == "`":            # markdown string
        t = t[1:-1].replace("**", "").replace("__", "")
    t = re.sub(r"<br\s*/?>", "\n", t, flags=re.I)
    t = re.sub(r"#(\w+);", lambda m: f"&#{m[1]};" if m[1].isdigit() else f"&{m[1]};", t)
    t = html.unescape(t)
    t = re.sub(r"</?[a-zA-Z][^>]*>", "", t)
    t = re.sub(r"\bfa[bsr]?:fa-[\w-]+\s*", "", t)         # font-awesome icons
    return "\n".join(line.strip() for line in t.split("\n")).strip()


def _char_em(ch: str) -> float:
    if ch in "il.,:;'|!`":
        return 0.28
    if ch in "fjrtI()[]{}- /\\\"":
        return 0.38
    if ch in "mwMW@%":
        return 0.88
    if ord(ch) > 0x2E80:
        return 1.0
    if ch.isupper():
        return 0.66
    if ch.isdigit():
        return 0.56
    return 0.54


def text_width(line: str, size: float) -> float:
    return sum(_char_em(c) for c in line) * size


def wrap(text: str, size: float, max_width: float) -> list[str]:
    lines = []
    for para in text.split("\n"):
        cur = ""
        for word in para.split(" "):
            cand = f"{cur} {word}" if cur else word
            if cur and text_width(cand, size) > max_width:
                lines.append(cur)
                cur = word
            else:
                cur = cand
        lines.append(cur)
    return lines
