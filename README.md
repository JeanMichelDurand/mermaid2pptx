# mermaid2pptx

[![tests](https://github.com/JeanMichelDurand/mermaid2pptx/actions/workflows/ci.yml/badge.svg)](https://github.com/JeanMichelDurand/mermaid2pptx/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/mermaid2pptx)](https://pypi.org/project/mermaid2pptx/)
[![Python](https://img.shields.io/pypi/pyversions/mermaid2pptx)](https://pypi.org/project/mermaid2pptx/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](https://github.com/JeanMichelDurand/mermaid2pptx/blob/main/LICENSE)

Turns a Mermaid **flowchart**, **sequence diagram** or **Gantt chart** into native PowerPoint
shapes on a single slide, ready to copy into an existing deck: real autoshapes and connectors
glued to them, not a picture. A flowchart can also be read as a simplified **BPMN** process and
drawn like one (`--render bpmn`).

One dependency (`python-pptx`). Runs on Windows, Linux and macOS, or in the browser.
PowerPoint is only needed to open the result.

## Before / after

A front-office incident process with three swim lanes
([`examples/incident_lanes.mmd`](https://github.com/JeanMichelDurand/mermaid2pptx/blob/main/examples/incident_lanes.mmd)):

| Mermaid | PowerPoint (`mermaid2pptx --render bpmn incident_lanes.mmd`) |
|---|---|
| <img src="https://raw.githubusercontent.com/JeanMichelDurand/mermaid2pptx/main/docs/img/incident_lanes.before.png" width="300" alt="Mermaid rendering: three stacked subgraphs"> | <img src="https://raw.githubusercontent.com/JeanMichelDurand/mermaid2pptx/main/docs/img/incident_lanes.after.png" width="560" alt="PowerPoint slide: three BPMN swim lanes with glued connectors"> |

A leave request, with a database, a data object and a loop back
([`examples/flowchart.mmd`](https://github.com/JeanMichelDurand/mermaid2pptx/blob/main/examples/flowchart.mmd)):

| Mermaid | PowerPoint (`mermaid2pptx flowchart.mmd`) |
|---|---|
| <img src="https://raw.githubusercontent.com/JeanMichelDurand/mermaid2pptx/main/docs/img/flowchart.before.png" width="380" alt="Mermaid rendering of the leave request flowchart"> | <img src="https://raw.githubusercontent.com/JeanMichelDurand/mermaid2pptx/main/docs/img/flowchart.after.png" width="440" alt="PowerPoint slide: the same shapes, with elbow connectors"> |

The same leave request as a sequence diagram
([`examples/sequence.mmd`](https://github.com/JeanMichelDurand/mermaid2pptx/blob/main/examples/sequence.mmd)):

| Mermaid | PowerPoint (`mermaid2pptx sequence.mmd`) |
|---|---|
| <img src="https://raw.githubusercontent.com/JeanMichelDurand/mermaid2pptx/main/docs/img/sequence.before.png" width="380" alt="Mermaid rendering of the sequence diagram"> | <img src="https://raw.githubusercontent.com/JeanMichelDurand/mermaid2pptx/main/docs/img/sequence.after.png" width="440" alt="PowerPoint slide: participants, lifelines, messages, activation bars, notes and blocks"> |

A new employee's onboarding plan
([`examples/gantt.mmd`](https://github.com/JeanMichelDurand/mermaid2pptx/blob/main/examples/gantt.mmd)):

| Mermaid | PowerPoint (`mermaid2pptx gantt.mmd`) |
|---|---|
| <img src="https://raw.githubusercontent.com/JeanMichelDurand/mermaid2pptx/main/docs/img/gantt.before.png" width="380" alt="Mermaid rendering of the Gantt chart"> | <img src="https://raw.githubusercontent.com/JeanMichelDurand/mermaid2pptx/main/docs/img/gantt.after.png" width="440" alt="PowerPoint slide: sections, bars, milestones and a weekly axis"> |

Every box, diamond and arrow on the right is a native, editable PowerPoint object: move a flowchart
box and its connectors follow. `docs/screenshots.sh` regenerates these images.

## Install

### Option 0: nothing to install, in your browser

Open **[the web version](https://jeanmicheldurand.github.io/mermaid2pptx/)**, paste or drop your `.mmd` file, and click *Convert to
PowerPoint*. It runs the same converter inside the page (Python compiled for the browser, with
[Pyodide](https://pyodide.org)): your diagram never leaves your computer, and no admin rights,
Python or executable are needed. This is the way to go on a locked-down work PC, where Windows
*Smart App Control* or IT policies block unsigned programs.

### Option 1: download the executable (no Python, no admin rights)

Take the file for your system from the [latest release](https://github.com/JeanMichelDurand/mermaid2pptx/releases/latest):

| System | File |
|---|---|
| Windows | `mermaid2pptx-windows-x86_64.exe` |
| Linux | `mermaid2pptx-linux-x86_64` |
| macOS (Apple silicon) | `mermaid2pptx-macos-arm64` |

Nothing to install: put it in any folder you can write to.

- **Windows.** Double-click `mermaid2pptx-windows-x86_64.exe` and choose one or more `.mmd` files,
  or drag the files onto it. Each `.pptx` is written next to its `.mmd`, and a message offers to
  open them in PowerPoint. The first run may show "Windows protected your PC", because the file
  is not signed yet: *More info* → *Run anyway*. With *Smart App Control* on (Windows 11), an
  unsigned program cannot be run at all: use the browser version above. See the
  [code signing policy](https://github.com/JeanMichelDurand/mermaid2pptx/blob/main/CODE_SIGNING.md). From a command prompt, it is the
  command line below.
- **Linux / macOS.** `chmod +x mermaid2pptx-*` once. On macOS, the first run is blocked as
  "unidentified developer": `xattr -d com.apple.quarantine mermaid2pptx-macos-arm64`.

### Option 2: with Python 3.10+

```sh
pipx install mermaid2pptx          # or: uv tool install mermaid2pptx
```

This puts a `mermaid2pptx` command on your PATH.

### Option 3: from a copy of this folder

```sh
python3 install.py          # Windows: py install.py
```

This creates `.venv/` in this folder, installs the converter into it and writes a launcher:
`mermaid2pptx.bat` on Windows, `mermaid2pptx` (a shell script) on Linux and macOS. Nothing is
installed globally. The folder holds no `.bat` file until then, so it can be sent by mail: mail
filters block batch files, even inside a zip.

## Use

```sh
mermaid2pptx diagram.mmd                       # -> diagram.pptx
mermaid2pptx notes.md --block 2 -o flow.pptx   # 2nd ```mermaid block of a Markdown file
cat diagram.mmd | mermaid2pptx - -o flow.pptx
```

(`mermaid2pptx.bat` or `./mermaid2pptx` with option 3, the downloaded file's name with option 1.)
Open the `.pptx`, click the diagram (it is one group), copy, and paste it into your slide.
Input files are read as UTF-8 (with or without BOM).

## What you get

- **Your template, or none.** By default the file is python-pptx's built-in blank deck: one
  slide, blank layout, no placeholders. With `--template DECK` (or the `MERMAID2PPTX_TEMPLATE`
  environment variable, which the Windows dialog also reads) it is that `.pptx` or `.potx`
  emptied of its slides: its theme colours and fonts, its slide size (`--aspect` is ignored),
  and the layout with the fewest placeholders, any left over removed. `--color theme` then
  shows the template's colours in the file itself, not only once pasted. Shapes carry no theme style reference, so a paste brings no stray
  shadows or colours with it. The text uses the theme font unless `--font` is given, so it
  takes on the target deck's font when pasted with "Use destination theme".
- **Real, editable objects.** Every node is an autoshape (rectangle, decision, terminator, database…)
  with its own text. Every edge is a connector **glued** to a connection site of both of its nodes:
  move a node and PowerPoint re-routes its edges. Labels are text boxes.
- **Aligned lines.** Edges are orthogonal: straight, or elbows with 90° bends. The converter
  computes each connector's rotation, flip and adjust values so the drawn path matches the
  computed route exactly, and each end sits on its connection site.
  When several edges bend in the same gap between two layers, each gets its own track, so no
  two edges share a line. Straight edges are also drawn as elbow connectors, so they stay
  orthogonal when a node is moved.
- **Author.** The file's author and "last modified by" are `--author`, else the
  `MERMAID2PPTX_AUTHOR` environment variable, else empty. The built-in deck's own metadata is
  cleared. PowerPoint writes your own name into "last modified by" if you save the file again.
- **Fits the slide.** A large diagram is scaled down to fit (16:9 by default), fonts included.
  `--no-fit` keeps the natural size and sizes the slide to the diagram instead.

## Options

| Option | Effect |
|---|---|
| `-o FILE` | output path (default: the input name with `.pptx`) |
| `--block N` | the Nth ```` ```mermaid ```` block of a Markdown file |
| `--direction TB\|BT\|LR\|RL` | flowcharts: override the diagram's direction |
| `--font-size PT` | text size before fitting (12) |
| `--font NAME` | fixed font instead of the theme font |
| `--render mermaid\|bpmn` | Flowcharts. `mermaid` (default): the flowchart's own shapes. `bpmn`: drawn like a BPMN process, see below |
| `--no-events` | `bpmn`: don't add the start and end events the diagram lacks |
| `--no-lanes` | `bpmn`: draw top-level subgraphs as groups, never as lanes |
| `--color NAME\|#RRGGBB` | box colours. `purple` (default): `#5236AB` with white text. `slate`: light grey boxes. `theme`: theme colours (background 1, accent 1, text 1), so the paste recolours with the target deck, and the file shows the `--template` deck's. `#RRGGBB`: boxes in that colour, with black or white text for contrast |
| `--author NAME` | document author (default: `$MERMAID2PPTX_AUTHOR`, else empty) |
| `--template DECK` | `.pptx` or `.potx` whose theme and slide size the file takes (default: `$MERMAID2PPTX_TEMPLATE`, else none; `""` = none) |
| `--aspect 16:9\|4:3` | slide shape, without a template |
| `--no-fit` | natural size; the slide grows to fit the diagram |
| `--no-group` | shapes left ungrouped |
| `--version` | print the version |

## BPMN render (`--render bpmn`)

The input is a plain Mermaid flowchart used as a simplified BPMN process. It is drawn this way:

| Mermaid | BPMN element | Drawn as |
|---|---|---|
| `{decision}` | exclusive gateway | small diamond, its text beside it (left in TB/BT, above in LR/RL) |
| `((circle))`, `([stadium])` with no incoming flow | start event | thin circle, text beside it |
| `((circle))`, `([stadium])` with no outgoing flow, `(((double circle)))` | end event | thick circle |
| `((circle))` in mid-flow | intermediate event | double circle |
| `[[subroutine]]` | call activity | rounded box, thick border |
| `[(database)]`, `[/parallelogram/]` | data store, data object | unchanged |
| any other shape | task | rounded box |
| top-level `subgraph`s holding every node | lanes | adjacent bands with a header strip |
| any other `subgraph` | group | dash-dot box, title top-left |
| `👤` at the start of a text | user task / user lane | a user icon in the box's top-left corner, or before the lane title |

**Lanes.** When there are two or more top-level subgraphs and every node sits in one of them,
they become swim lanes, in the order they are declared: columns with the header at the top
in TD/BT, rows with the header on the left in LR/RL. A flow between lanes crosses over; a loop
that stays in one lane goes round inside that lane. See `examples/incident_lanes.mmd`.

If the diagram has no start event, one is added before each node without an incoming flow. If
it has no end event, one is added after each node without an outgoing flow (`--no-events` to
turn this off). The diagram's direction is kept; BPMN is usually drawn left to right,
`--direction LR` does that.

## Flowchart syntax covered

- `flowchart` / `graph`, directions `TB TD BT LR RL`. Front matter, `%%` comments, `;` statement separators and ```` ``` ```` fences are all accepted.
- Node shapes: `[rect]` `(round)` `([stadium])` `[[subroutine]]` `[(database)]` `((circle))`
  `(((double circle)))` `{diamond}` `{{hexagon}}` `[/parallelogram/]` `[\alt\]` `[/trapezoid\]`
  `[\alt trapezoid/]` `>flag]`; `"quoted text"`, `<br>`, `#quot;`-style entities, markdown strings.
- Edges: `-->` `---` `-.->` `==>` `~~~` (invisible, still used for the layout) `<-->` `--o` `--x`. Each extra dash
  adds a rank (`--->`). Labels as `-->|text|` or `-- text -->`; chains `A --> B --> C`, and `&` groups.
- `subgraph id [Title] … end`, nested; an edge to a subgraph id is attached to a member node
  (with a warning).
- `classDef`, `class`, `:::class`, `style` (on nodes and subgraphs), `linkStyle`: `fill`, `stroke`,
  `stroke-width`, `stroke-dasharray` (`0` = solid), `color`. A `classDef` fill or stroke wins over
  `--color`; other CSS (`rx`, `ry`, …) is ignored.

Not covered: the v11 `A@{ shape: … }` syntax, `click`, and per-subgraph `direction` (ignored). An
`x` end marker is drawn as a diamond, because PowerPoint has no cross arrowhead.

## Sequence diagrams

- `participant` and `actor` (a figure over the name), with `as` aliases; participants met in a
  message are added in order. Each is drawn at the top and again at the bottom, joined by a dashed
  lifeline glued to both boxes.
- Messages `->` `-->` `->>` `-->>` `-x` `--x` `-)` `--)` `<<->>` `<<-->>` (solid or dotted, with
  an arrow, an open arrow, a cross or nothing), to another participant or to oneself (a loop).
- Activation bars: `+`/`-` on a message, or `activate` / `deactivate`; nested bars step right.
- `Note left of | right of | over A[,B]`, drawn as folded-corner notes.
- Blocks `loop`, `alt`/`else`, `opt`, `par`/`and`, `critical`/`option`, `break`, nested;
  `rect rgb(…)` as a coloured background; `box Colour Label … end` around participants.
- `autonumber` (a numbered badge at the start of each message) and `title`.

Not covered: `create`/`destroy` (the participant is drawn from top to bottom, with a warning for
`destroy`), `links`, and the v11 participant types (`@{ "type": … }`, drawn as participants).

## Gantt charts

- `title`, `dateFormat` (dayjs tokens: `YYYY-MM-DD` by default, `DD/MM/YYYY HH:mm`, `D MMM YY`…),
  `axisFormat` (`%d %b`, `%Y-%m-%d` by default, `%H:%M`…), `tickInterval` (`1week`, `1month`…),
  `weekday`, `section`.
- Tasks `Name : [done|active|crit|milestone,] [id,] [start,] end`, where start is a date or
  `after id1 id2`, and end is a date, a duration (`3d`, `2w`, `12h`, `30m`, `1M`) or `until id`.
  Without a start, a task follows the one before it.
- `excludes weekends`, day names or dates (and `includes` exceptions): durations skip those days,
  which are shaded on the chart. `inclusiveEndDates`.
- One row per task; sections as alternating bands with their name on the left; the task's name on
  its bar when it fits, beside it otherwise. Done, active and critical tasks have their own colours
  in every palette.

Not covered: `click`, `todayMarker` (a slide has no "today"), `displayMode compact`, and dependency
arrows (Mermaid draws none either).

## Layout, in short

Flowcharts use a layered (Sugiyama-style) layout, implemented in `src/mermaid2pptx/flowchart/layout/`:

1. Break cycles (the edge written last closes the cycle).
2. Rank nodes by longest path. An edge with a label spans two ranks, so its label gets its own slot.
3. Order each layer with barycentre sweeps, keeping each subgraph's members together.
4. Place nodes along the cross axis with a median pull and a weighted isotonic fit (pool adjacent violators), then straighten long edges and 1-to-1 links.
5. Route every edge orthogonally, with jogs spread over tracks.

A back edge (one that closes a cycle) goes round the outside of the layers when both of its nodes are
outermost in their layer. Otherwise the layout runs again with that edge threaded through reserved slots.

**Known limits.** A group narrower than its title, entered from its title side, can have an edge
cross the title.  In LR/RL, an edge entering a subgraph that spans several ranks can
graze the subgraph's title. A route with more than 5 segments cannot be a connector preset; it
becomes an unglued polyline (not seen on the examples). Text widths are estimated, not
measured: a very wide font can wrap one more line than planned.

## Tests

```sh
python3 install.py dev             # Windows: py install.py dev
.venv/bin/python -m pytest         # Windows: .venv\Scripts\python.exe -m pytest
```

GitHub Actions runs them on Windows, Linux and macOS, with Python 3.10 and 3.13, on every push.

The tests cover the three parsers, and a check that each connector's geometry draws its route: the
path is rebuilt from the XML (preset path, then flip, then rotation) independently of the
converter. On every example in `examples/` in every direction, they also check that nodes never
overlap, that routes stay orthogonal and never cross a node, and that each connector end, as
drawn, lands on the connection site it is glued to.

The connection-site indices in `flowchart/shapes.py` were measured in PowerPoint through COM
(`ConnectionSiteCount` / `BeginConnect`), and the examples were checked by rendering them in
PowerPoint and moving a node to confirm the glue holds.

## Contributing

Bug reports (with the Mermaid input) and pull requests are welcome: see
[CONTRIBUTING.md](https://github.com/JeanMichelDurand/mermaid2pptx/blob/main/CONTRIBUTING.md) and the [Code of Conduct](https://github.com/JeanMichelDurand/mermaid2pptx/blob/main/CODE_OF_CONDUCT.md).

## Releasing

Bump `__version__` in `src/mermaid2pptx/__init__.py` and merge it into `main`, then tag that merged
commit: `git switch main && git pull && git tag v1.2.3 && git push origin v1.2.3`. The workflow stops
at once if the tag and `__version__` differ (a tag on a commit that still has the old version).
The `release` workflow runs the tests, builds one standalone executable per system with
PyInstaller, runs each on an example, attaches them to a GitHub release, and publishes the
package to PyPI. Record the changes in [CHANGELOG.md](https://github.com/JeanMichelDurand/mermaid2pptx/blob/main/CHANGELOG.md) first.

## License

MIT, see [LICENSE](https://github.com/JeanMichelDurand/mermaid2pptx/blob/main/LICENSE). The software is provided "as is", without warranty of any kind,
express or implied. The authors are not liable for any claim, damage or other liability arising
from its use. Check the generated slides before you rely on them.
