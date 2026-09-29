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

- **One file, one dependency, on purpose.** Everything lives in `mermaid2pptx.py` and needs only
  `python-pptx`, so the tool can be copied or mailed as a single script. Please don't split it into
  a package or add a dependency; open an issue first if you think it has to change.
- **A new layout case comes with an example.** Add a `.mmd` file to `examples/`: the tests check every
  example in every direction (no overlapping nodes, orthogonal routes that never cross a node,
  connectors glued to their sites), so it is covered from then on.
- **Connection sites are measured, not guessed.** The indices in `SHAPES` were read from PowerPoint
  (`ConnectionSiteCount` / `BeginConnect`). A new shape needs the same measurement.
- **User-visible changes** get a line under `[Unreleased]` in `CHANGELOG.md`.

## Pull requests

Fork, branch, and open a pull request against `main`. The `tests` workflow (ruff, then pytest on
Windows, Linux and macOS) must be green before it can be merged.

By contributing, you agree that your work is released under the [MIT license](LICENSE), and to
follow the [Code of Conduct](CODE_OF_CONDUCT.md).
