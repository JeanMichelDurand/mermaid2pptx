"""The command line: `mermaid2pptx FILE`, and the batch conversion behind the Windows dialog."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __doc__ as _doc, __version__
from .convert import convert
from .errors import MermaidError
from .flowchart.parser import DIRECTIONS
from .options import AUTHOR_ENV, SLIDE_SIZES, TEMPLATE_ENV, Options, palette
from .source import extract_blocks


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="mermaid2pptx", description=_doc.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="Mermaid file (.mmd, or .md with ```mermaid blocks); '-' = stdin")
    ap.add_argument("-o", "--output", help="output .pptx (default: input name with .pptx)")
    ap.add_argument("--block", type=int, default=1, help="which ```mermaid block of a Markdown file (1-based)")
    ap.add_argument("--direction", choices=sorted(DIRECTIONS), help="override the diagram direction")
    ap.add_argument("--font-size", type=float, default=12.0, help="node text size in pt before fitting (12)")
    ap.add_argument("--font", help="font name (default: the theme font, so a paste adopts the target deck's)")
    ap.add_argument("--render", choices=("mermaid", "bpmn"), default="mermaid",
                    help="flowcharts: mermaid (default) draws the flowchart's own shapes; "
                         "bpmn draws tasks, gateways, events and swim lanes like a BPMN process")
    ap.add_argument("--no-events", action="store_true",
                    help="bpmn: don't add the start and end events the diagram lacks")
    ap.add_argument("--no-lanes", action="store_true",
                    help="bpmn: draw top-level subgraphs as groups, never as swim lanes")
    ap.add_argument("--color", default="purple",
                    help="box colours: purple (default), slate, theme (the target deck's "
                         "theme colours) or #RRGGBB")
    ap.add_argument("--author", help=f"document author (default: ${AUTHOR_ENV}, else empty)")
    ap.add_argument("--template", metavar="DECK",
                    help=".pptx or .potx whose theme (colours, fonts) and slide size the deck takes, so "
                         f"--color theme shows its colours (default: ${TEMPLATE_ENV}, else python-pptx's blank deck)")
    ap.add_argument("--aspect", choices=sorted(SLIDE_SIZES), default="16:9",
                    help="slide shape (16:9), without --template")
    ap.add_argument("--no-fit", action="store_true",
                    help="keep the natural size and size the slide to the diagram instead of shrinking it")
    ap.add_argument("--no-group", action="store_true", help="leave the shapes ungrouped on the slide")
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = ap.parse_args(argv)

    try:
        if args.input == "-":
            sys.stdin.reconfigure(encoding="utf-8-sig")      # the Windows console code page is not UTF-8
            src = sys.stdin.read()
        else:
            src = Path(args.input).read_text(encoding="utf-8-sig")   # tolerate Notepad's BOM
    except OSError as exc:
        print(f"error: cannot read {args.input}: {exc.strerror}", file=sys.stderr)
        return 1
    except UnicodeDecodeError:
        print(f"error: {args.input} is not UTF-8: save it as UTF-8 and try again", file=sys.stderr)
        return 1
    blocks = extract_blocks(src)
    if not 1 <= args.block <= len(blocks):
        ap.error(f"--block {args.block}: the input has {len(blocks)} mermaid block(s)")
    out = Path(args.output) if args.output else \
        (Path("diagram.pptx") if args.input == "-" else Path(args.input).with_suffix(".pptx"))
    try:
        palette(args.color)
    except ValueError as exc:
        ap.error(f"--color: {exc}")
    opts = Options(font_size=args.font_size, font=args.font, color=args.color, render=args.render,
                   events=not args.no_events, lanes=not args.no_lanes, author=args.author, group=not args.no_group,
                   fit=not args.no_fit, aspect=args.aspect, direction=args.direction, template=args.template)
    try:
        prs, d, _ = convert(blocks[args.block - 1], opts)
    except MermaidError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    try:
        prs.save(out)
    except OSError as exc:
        hint = " (is it open in PowerPoint?)" if isinstance(exc, PermissionError) else ""
        print(f"error: cannot write {out}: {exc.strerror}{hint}", file=sys.stderr)
        return 1
    for w in d.warnings:
        print(f"warning: {w}", file=sys.stderr)
    print(f"{out}: {d.summary()}")
    return 0


def convert_files(paths: list[str]) -> tuple[bool, str]:
    """Convert each file with the default options, as `mermaid2pptx FILE` would.

    Returns whether every file converted, and everything the conversions printed (results,
    warnings, errors), for a message box.
    """
    import contextlib
    import io
    ok, report = True, io.StringIO()
    for path in paths:
        with contextlib.redirect_stdout(report), contextlib.redirect_stderr(report):
            try:
                code = main([path])
            except SystemExit as exc:                    # argparse errors
                code = exc.code
            except Exception as exc:                     # a bug: say so rather than vanish
                print(f"error: {path}: unexpected {exc!r}. Please report it with the file.")
                code = 1
        ok = ok and code == 0
    return ok, report.getvalue().strip()
