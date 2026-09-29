"""An independent reading of connector presets and shape transforms in the OOXML."""
import math

from pptx.oxml.ns import qn


def drawn_path(prst, adj, x, y, w, h, rot=0, flip_v=False, flip_h=False):
    """The polyline PowerPoint draws for a connector: preset path, then flips, then rotation
    about the box centre (DrawingML semantics, written independently of the converter)."""
    a = [v / 100000 for v in adj]
    local = {
        "straightConnector1": [(0, 0), (w, h)],
        "bentConnector2": [(0, 0), (w, 0), (w, h)],
        "bentConnector3": [(0, 0), (w * a[0], 0), (w * a[0], h), (w, h)] if a else None,
        "bentConnector4": [(0, 0), (w * a[0], 0), (w * a[0], h * a[1]), (w, h * a[1]), (w, h)] if len(a) > 1 else None,
        "bentConnector5": [(0, 0), (w * a[0], 0), (w * a[0], h * a[1]), (w * a[2], h * a[1]),
                           (w * a[2], h), (w, h)] if len(a) > 2 else None,
    }[prst]
    t = math.radians(rot / 60000)
    out = []
    for px, py in local:
        if flip_h:
            px = w - px
        if flip_v:
            py = h - py
        dx, dy = px - w / 2, py - h / 2
        out.append((x + w / 2 + dx * math.cos(t) - dy * math.sin(t),
                    y + h / 2 + dx * math.sin(t) + dy * math.cos(t)))
    return out



def xfrm(el):
    x = el.find(f".//{qn('a:xfrm')}")
    off, ext = x.find(qn("a:off")), x.find(qn("a:ext"))
    return (int(off.get("x")), int(off.get("y")), int(ext.get("cx")), int(ext.get("cy")),
            int(x.get("rot", 0)), x.get("flipV") == "1", x.get("flipH") == "1")
