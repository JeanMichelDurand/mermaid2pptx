# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/).

## [Unreleased]

## [1.1.0] - 2026-09-29

### Changed

- **Flowcharts are drawn with their own Mermaid shapes by default.** The BPMN reading (gateways,
  events, swim lanes, added start and end events) is now opt-in: `--render bpmn`. To keep the
  1.0 output, add `--render bpmn` to your commands.
- The code is a package (`src/mermaid2pptx/`, one folder per diagram type) instead of one
  file, with no file over 500 lines; `CONTRIBUTING.md` has the map. `python -m mermaid2pptx`
  works, and `import mermaid2pptx` keeps `convert`, `Options` and `MermaidError`.
- The summary line counts in the singular when there is one: `1 edge`.

### Added

- A browser version, published on GitHub Pages: https://jeanmicheldurand.github.io/mermaid2pptx/. It runs the converter
  in the page with Pyodide, for users who cannot install or run programs.
- Signing of the Windows executable through SignPath, enabled once the project is approved
  (`CODE_SIGNING.md`).

## [1.0.1] - 2026-09-29

### Changed

- The Windows executable, double-clicked, opens a file dialog instead of printing the command-line
  usage; with files dropped on it, it converts them. Either way, the result or the error shows in
  a message box that offers to open the slides, and no console window stays behind. From a
  command prompt it behaves as before.

### Fixed

- A missing or unreadable input file, an input not saved as UTF-8, or an output that cannot be
  written (for instance still open in PowerPoint) now prints a one-line `error:` message and exits
  with status 1, instead of a Python traceback.

## [1.0.0] - 2026-09-29

### Added

- Converts a Mermaid `flowchart` / `graph` into native PowerPoint shapes on one slide: autoshapes
  for nodes, elbow connectors glued to their connection sites, text boxes for labels.
- Layered layout with orthogonal routing; jogs between two layers get separate tracks.
- BPMN render (default): gateways, start/intermediate/end events, call activities, swim lanes
  from top-level subgraphs, user icon from a leading 👤. `--render mermaid` keeps the flowchart's
  own shapes.
- `classDef`, `class`, `:::`, `style` and `linkStyle` colours and strokes.
- Colour palettes `purple` (default), `slate`, `theme`, or any `#RRGGBB`.
- Markdown input (`--block N`), stdin input, `--direction`, `--aspect`, `--no-fit`, `--no-group`.
- Document author from `--author` or `MERMAID2PPTX_AUTHOR`.
- Standalone executables for Windows, Linux and macOS, and a PyPI package.

[Unreleased]: ../../compare/v1.0.2...HEAD
[1.0.2]: ../../compare/v1.0.1...v1.0.2
[1.0.1]: ../../compare/v1.0.0...v1.0.1
[1.0.0]: ../../releases/tag/v1.0.0
