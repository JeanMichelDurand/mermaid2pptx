# Contributing

Thanks for helping. Bug reports with the Mermaid input that fails are the most useful
contribution of all: use the [bug report form](https://github.com/JeanMichelDurand/mermaid2pptx/issues/new/choose).

## Set up

```sh
python3 install.py dev          # Windows: py install.py dev
.venv/bin/python -m pytest      # Windows: .venv\Scripts\python.exe -m pytest
```

The linter is [ruff](https://docs.astral.sh/ruff/), configured in `pyproject.toml`:
`pipx run ruff check .` (or `uvx ruff check .`).

## Conventions

- **One dependency, short files.** The converter needs only `python-pptx`; please open an issue
  before adding another. No Python file goes over 500 lines (`tests/test_code_size.py` fails if one
  does): when a file grows, split it by responsibility, following the map below.
- **A new layout case comes with an example.** Add a `.mmd` file to `examples/`: the tests check every
  example in every direction (no overlapping nodes, orthogonal routes that never cross a node,
  connectors glued to their sites), so it is covered from then on.
- **Connection sites are measured, not guessed.** The indices in `SHAPES` were read from PowerPoint
  (`ConnectionSiteCount` / `BeginConnect`). A new shape needs the same measurement.
- **User-visible changes** get a line under `[Unreleased]` in `CHANGELOG.md`.

## Code map

```
src/mermaid2pptx/
  cli.py, windows.py      command line; the Windows file dialog and message boxes
  convert.py, source.py   one diagram in, one deck out; which diagram type a text is
  options.py, styles.py   options and palettes; CSS-like colours and styles
  text.py, geometry.py    label wrapping and width estimates; Box
  slide/                  python-pptx helpers every diagram type draws with (deck, shapes, connectors)
  flowchart/              model, parser, bpmn (the BPMN reading), shapes, render
    layout/               ranking -> graph -> ordering -> placement -> lanes -> routing
tests/                    one file per area; ooxml.py reads connectors back independently
```

A diagram type is a folder with the same steps: `parser.py` (text -> model), a layout (model ->
boxes and routes in points) and `render.py` (layout -> shapes on a `slide.deck.Canvas`), joined by
its `convert()` and registered in `convert.py` and `source.py`.

## Pull requests

Fork, branch, and open a pull request against `main`. The `tests` workflow (ruff, then pytest on
Windows, Linux and macOS) must be green before it can be merged.

By contributing, you agree that your work is released under the [MIT license](LICENSE), and to
follow the [Code of Conduct](CODE_OF_CONDUCT.md).
