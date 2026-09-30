# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Fixed

- **The Theme colours had no theme to show.** The file was always built on python-pptx's
  Office deck, so `--color theme` showed Office blue until pasted, with no way to give it your
  deck's theme. `--template DECK` (a `.pptx` or `.potx`, or the `MERMAID2PPTX_TEMPLATE`
  environment variable, read by the Windows executable's dialog too) builds the file on that
  deck: its theme colours and fonts, its slide size, none of its slides. The browser version
  has a "Template" picker, and choosing one selects the Theme colours.

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

- **Sequence diagrams** (`sequenceDiagram`): participants and actors, dashed lifelines glued to
  the participant boxes (drawn again at the bottom), every Mermaid arrow (`->>`, `-->>`, `-x`,
  `-)`, `<<->>`…), messages to oneself, activation bars (`+`/`-`, `activate`), notes,
  `loop`/`alt`/`opt`/`par`/`critical`/`break` blocks, `rect` backgrounds, `box` groups,
  `autonumber` and `title`. Example: `examples/sequence.mmd`.
- **Gantt charts** (`gantt`): sections as bands, a time axis with automatic ticks (or
  `tickInterval`), `dateFormat` and `axisFormat`, tasks by date, duration, `after` and `until`,
  `done`/`active`/`crit` bars and milestones, `excludes weekends` (and days, dates) with the
  excluded days shaded. Example: `examples/gantt.mmd`.

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

[Unreleased]: ../../compare/v1.1.0...HEAD
[1.1.0]: ../../compare/v1.0.1...v1.1.0
[1.0.1]: ../../compare/v1.0.0...v1.0.1
[1.0.0]: ../../releases/tag/v1.0.0
