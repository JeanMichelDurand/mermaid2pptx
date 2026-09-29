#!/usr/bin/env bash
# Regenerates the README's before/after images (docs/img/) from examples/.
#   docs/screenshots.sh [EXAMPLE ...]        default: every example the README shows
# Runs under WSL with a Windows host: "before" is the Mermaid diagram rendered by headless Edge
# (mermaid.js from jsDelivr), "after" is the converted slide exported to PNG by PowerPoint (COM).
# Both are cropped to their content by Pillow. Needs `python3 install.py dev` already run, and Pillow.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
PY=${PY:-python3}
EDGE="/mnt/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"
NAMES=("$@"); [ ${#NAMES[@]} -gt 0 ] || NAMES=(incident_lanes flowchart sequence gantt)
declare -A OPTS=([incident_lanes]="--render bpmn")      # converter options, per example
OUT="$ROOT/docs/img"; mkdir -p "$OUT"

# PowerPoint and Edge cannot reliably use \\wsl.localhost paths: stage under the Windows %TEMP%.
WIN_TMP=$(powershell.exe -NoProfile -Command '[IO.Path]::GetTempPath()' | tr -d '\r')
STAGE=$(wslpath -u "$WIN_TMP")mermaid2pptx_shots
mkdir -p "$STAGE"
WIN_STAGE=$(wslpath -w "$STAGE")

for name in "${NAMES[@]}"; do
  src="$ROOT/examples/$name.mmd"
  # before: mermaid.js in headless Edge
  $PY - "$src" "$STAGE/$name.html" <<'EOF'
import html, sys
from pathlib import Path
src = Path(sys.argv[1]).read_text(encoding="utf-8")
Path(sys.argv[2]).write_text(f"""<!doctype html><meta charset="utf-8">
<body style="margin:0;background:#fff"><pre class="mermaid">{html.escape(src)}</pre>
<script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
<script>mermaid.initialize({{startOnLoad: true, theme: "default"}});</script>""", encoding="utf-8")
EOF
  "$EDGE" --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=2 \
    --window-size=1400,2400 --virtual-time-budget=15000 \
    --screenshot="$WIN_STAGE\\$name.before.png" "file:///$(wslpath -m "$STAGE/$name.html")" 2>/dev/null
  # after: the converted slide, exported by PowerPoint
  # shellcheck disable=SC2086
  "$ROOT/.venv/bin/python" -m mermaid2pptx ${OPTS[$name]:-} "$src" -o "$STAGE/$name.pptx" >/dev/null
  powershell.exe -NoProfile -NonInteractive -Command "
    \$ErrorActionPreference = 'Stop'
    \$app = New-Object -ComObject PowerPoint.Application
    try {
      \$pres = \$app.Presentations.Open('$WIN_STAGE\\$name.pptx', -1, 0, 0)
      \$pres.Slides.Item(1).Export('$WIN_STAGE\\$name.after.png', 'PNG', 1920, 1080)
      \$pres.Close()
    } finally { \$app.Quit(); [Runtime.InteropServices.Marshal]::ReleaseComObject(\$app) | Out-Null }
  "
  for side in before after; do
    $PY - "$STAGE/$name.$side.png" "$OUT/$name.$side.png" <<'EOF'
import sys
from PIL import Image, ImageChops
im = Image.open(sys.argv[1]).convert("RGB")
box = ImageChops.difference(im, Image.new("RGB", im.size, "white")).getbbox()
pad = 24
im = im.crop((max(box[0] - pad, 0), max(box[1] - pad, 0),
              min(box[2] + pad, im.width), min(box[3] + pad, im.height)))
im.thumbnail((1200, 1200))
im.save(sys.argv[2], optimize=True)
EOF
  done
  echo "$name: $(ls "$OUT"/$name.*.png | xargs -n1 basename | tr '\n' ' ')"
done
rm -rf "$STAGE"
