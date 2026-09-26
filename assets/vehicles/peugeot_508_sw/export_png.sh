#!/usr/bin/env bash
# Renders every 508_sw_*.svg to transparent PNGs (@1x = 480x160, @2x = 960x320).
# Needs a headless Chromium: set CHROME=/path/to/headless_shell (or chrome) if not on PATH.
set -euo pipefail
cd "$(dirname "$0")"
CHROME="${CHROME:-$(ls /opt/pw-browsers/chromium_headless_shell-*/*/headless_shell 2>/dev/null | head -1)}"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
mkdir -p png
for svg in 508_sw_*.svg; do
  name="${svg%.svg}"
  for s in 1 2; do
    w=$((480 * s)); h=$((160 * s))
    echo "<html><body style=\"margin:0;background:transparent\"><img src=\"file://$PWD/$svg\" style=\"width:${w}px;height:${h}px;display:block\"></body></html>" > "$TMP/p.html"
    "$CHROME" --no-sandbox --disable-gpu --hide-scrollbars --default-background-color=00000000 \
      --window-size=$w,$h --screenshot="png/${name}@${s}x.png" "file://$TMP/p.html" >/dev/null 2>&1
    echo "png/${name}@${s}x.png"
  done
done
