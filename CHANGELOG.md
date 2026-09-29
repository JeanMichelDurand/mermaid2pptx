# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/).

## [Unreleased]

## [1.0.1] - 2026-09-29

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

[Unreleased]: ../../compare/v1.0.1...HEAD
[1.0.1]: ../../compare/v1.0.0...v1.0.1
[1.0.0]: ../../releases/tag/v1.0.0
