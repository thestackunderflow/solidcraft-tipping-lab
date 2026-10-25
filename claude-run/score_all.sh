#!/usr/bin/env bash
# Score every run: behaviour from the logs, then each saved design re-opened in SolidCraft (the run's folder mounted as
# /lab/out so the server may read it), the stand sliced with the stock SPEED preset, and the margin table.
#   bash claude-run/score_all.sh
set -euo pipefail
cd "$(dirname "$0")/.."
LAB="$(pwd -W 2>/dev/null || pwd)"
python claude-run/score.py behaviour > /dev/null
for d in out/runs/*-*; do
  [ -d "$d" ] || continue
  if [ -f "$d/work/stand.solidcraft" ] && [ ! -f "$d/score/score-p210/cell.json" ]; then
    MSYS_NO_PATHCONV=1 timeout 600 docker run --rm -v "$LAB:/work" -v "$LAB/$d:/lab/out" -w /work solidcraft-tipping-lab:0.22.0 \
      python3 claude-run/score.py design /lab/out > "$d/score-design.log" 2>&1 || true
  fi
  if [ -f "$d/score/score-p210/stand.stl" ] && [ ! -f "$d/score/score-p210/slice-speed.json" ]; then
    bash slicer/slice.sh "$d/score/score-p210/stand.stl" "$d/score/score-p210" slice-speed > /dev/null || true
  fi
done
MSYS_NO_PATHCONV=1 docker run --rm -v "$LAB:/work" -w /work solidcraft-tipping-lab:0.22.0 python3 claude-run/score.py table
