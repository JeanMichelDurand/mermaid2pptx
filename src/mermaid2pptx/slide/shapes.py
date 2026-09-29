"""Shape styling: colours, text, line ends, and the BPMN user icon."""
from __future__ import annotations

from lxml import etree
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Pt

from ..styles import parse_color

_MARKER_XML = {"arrow": "triangle", "circle": "oval", "cross": "diamond", "open": "arrow"}


def set_color(color_format, spec):
    """`spec` is 'RRGGBB' or an MSO_THEME_COLOR."""
    if isinstance(spec, str):
        color_format.rgb = RGBColor.from_string(spec)
    else:
        color_format.theme_color = spec


def set_fill(shape, css: str | None, default):
    """Solid fill: the CSS colour when it parses, else `default`."""
    shape.fill.solid()
    set_color(shape.fill.fore_color, (parse_color(css) if css else None) or default)


def strip_style(shape):
    """Drop the theme style reference: no inherited shadow, fill or font colour."""
    style = shape._element.find(qn("p:style"))
    if style is not None:
        shape._element.remove(style)


def write_text(tf, lines, size, color, font, bold=False, align=PP_ALIGN.CENTER):
    p = tf.paragraphs[0]
    p.alignment = align
    p.text = "\v".join(lines)
    for run in p.runs:
        run.font.size = Pt(size)
        run.font.bold = bold
        set_color(run.font.color, color)
        if font:
            run.font.name = font


def frame(tf, anchor=MSO_ANCHOR.MIDDLE, margin: float = 0.0, wrap: bool = False):
    """A text frame that neither resizes nor overflows its shape, with even margins (pt)."""
    tf.word_wrap, tf.auto_size, tf.vertical_anchor = wrap, MSO_AUTO_SIZE.NONE, anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = Pt(margin) if margin else 0


def style_line(line, width: float, color, dash=None, start: str = "none", end: str = "none"):
    """Width (pt), colour, dash style and the markers at both ends (none|arrow|open|circle|cross)."""
    line.width = Pt(width)
    set_color(line.color, color)
    if dash is not None:
        line.dash_style = dash
    ln = line._get_or_add_ln()
    for tag, marker in (("a:headEnd", start), ("a:tailEnd", end)):
        if marker != "none":
            etree.SubElement(ln, qn(tag), type=_MARKER_XML[marker], w="med", len="med")


def user_icon(cv, x, y, size, color, name):
    """BPMN user marker: a head over rounded shoulders, top-left corner at (x, y)."""
    for preset, (fx, fy, fw, fh) in ((MSO_SHAPE.OVAL, (.28, 0, .44, .44)),
                                     (MSO_SHAPE.ROUND_2_SAME_RECTANGLE, (.06, .5, .88, .5))):
        ic = cv.shapes.add_shape(preset, cv.X(x + fx * size), cv.Y(y + fy * size), cv.E(fw * size), cv.E(fh * size))
        strip_style(ic)
        ic.name = name
        if preset == MSO_SHAPE.ROUND_2_SAME_RECTANGLE:
            ic.adjustments[0] = 0.5
        ic.fill.solid()
        set_color(ic.fill.fore_color, color)
        ic.line.fill.background()
