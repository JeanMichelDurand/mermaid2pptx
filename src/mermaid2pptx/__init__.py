"""Convert a Mermaid flowchart, sequence diagram or Gantt chart into native, editable PowerPoint
shapes on one blank slide.

    mermaid2pptx diagram.mmd -o diagram.pptx
    mermaid2pptx notes.md --block 2                    # 2nd ```mermaid block
    cat diagram.mmd | mermaid2pptx - -o diagram.pptx

The deck is python-pptx's built-in blank presentation unless --template names a .pptx or .potx,
whose theme (colours, fonts) and slide size it then takes: open it, click the diagram (a single
group) and paste it into any slide. Nodes are autoshapes;
edges are connectors glued to the nodes' connection sites, so they follow a node you move.

Flowcharts are laid out by a small layered (Sugiyama-style) engine with orthogonal routing
(flowchart/layout). With --render bpmn a flowchart is read as a simplified BPMN process:
decisions become gateways, circles and stadiums events, other boxes tasks, with missing
start/end events added, top-level subgraphs drawn as swim lanes and a leading 👤 as a user
icon (flowchart/bpmn.py). Boxes are purple unless --color says otherwise.
See README.md for the syntax covered and the known limits.
"""
from .convert import convert
from .errors import MermaidError
from .options import AUTHOR_ENV, PALETTES, TEMPLATE_ENV, Options, palette
from .source import extract_blocks

__version__ = "1.1.1"
__all__ = ["AUTHOR_ENV", "PALETTES", "TEMPLATE_ENV", "MermaidError", "Options", "convert", "extract_blocks",
           "palette", "__version__"]
