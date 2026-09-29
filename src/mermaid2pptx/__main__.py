"""`python -m mermaid2pptx`, and the entry point of the one-file executables."""
import sys

from mermaid2pptx.cli import main
from mermaid2pptx.windows import explorer_ui, started_from_explorer

if __name__ == "__main__":
    sys.exit(explorer_ui(sys.argv[1:]) if started_from_explorer() else main())
