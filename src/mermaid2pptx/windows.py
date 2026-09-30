"""The Windows executable started from Explorer: a file dialog and message boxes, no console."""
from __future__ import annotations

import os
import sys
from pathlib import Path

from .cli import convert_files


def started_from_explorer() -> bool:
    """The Windows executable was double-clicked, or had files dropped on it.

    From Explorer, the only processes attached to the console are the executable's own two (a
    one-file build runs under its bootloader); from a shell, the shell is attached as well.
    """
    if sys.platform != "win32" or not getattr(sys, "frozen", False):
        return False
    import ctypes
    attached = ctypes.windll.kernel32.GetConsoleProcessList((ctypes.c_uint * 4)(), 4)
    return 0 < attached <= 2 and sys.stdin is not None and sys.stdin.isatty()   # not in CI, not piped


def explorer_ui(paths: list[str]) -> int:
    """No console for Explorer users: a file dialog when double-clicked, message boxes for results."""
    import ctypes
    from tkinter import Tk, filedialog, messagebox
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)     # SW_HIDE
    root = Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    if not paths:
        paths = list(filedialog.askopenfilenames(
            parent=root, title="mermaid2pptx: choose the Mermaid files to convert",
            filetypes=[("Mermaid or Markdown", "*.mmd *.mermaid *.md *.txt"), ("All files", "*.*")]))
        if not paths:
            return 0
    ok, report = convert_files(paths)
    if not ok:
        messagebox.showerror("mermaid2pptx", report, parent=root)
        return 1
    if messagebox.askyesno("mermaid2pptx", f"{report}\n\nOpen in PowerPoint now?", parent=root):
        for path in paths:
            os.startfile(Path(path).with_suffix(".pptx"))
    return 0
