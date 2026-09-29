"""Every Python file stays short enough to read in one sitting (CONTRIBUTING.md)."""
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
MAX_LINES = 500
FILES = sorted(p for d in ("src", "tests") for p in (ROOT / d).rglob("*.py")) + [ROOT / "install.py"]


@pytest.mark.parametrize("path", FILES, ids=lambda p: str(p.relative_to(ROOT)))
def test_file_is_at_most_500_lines(path):
    n = len(path.read_text(encoding="utf-8").splitlines())
    assert n <= MAX_LINES, f"{path.name} has {n} lines: split it by responsibility"
