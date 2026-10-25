#!/usr/bin/env bash
# Slice every probe cell's stand.stl with the stock preset (slicer/slice.sh), then the sensitivity strip for part 1's
# stand (lip15-p190): 3 walls, 20% infill, gyroid, and a 100% infill method check (G-code vs CAD).
#   bash probe/slice_cells.sh out/probe/0.22.0
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT=$1
for d in "$ROOT"/*; do
  if [ -f "$d/stand.stl" ] && [ ! -f "$d/slice-speed.json" ]; then
    bash slicer/slice.sh "$d/stand.stl" "$d" slice-speed > /dev/null
  fi
done
S="$ROOT/lip15-p190"
[ -f "$S/slice-3walls.json" ] || bash slicer/slice.sh "$S/stand.stl" "$S" slice-3walls --perimeters 3 > /dev/null
[ -f "$S/slice-20pct.json" ] || bash slicer/slice.sh "$S/stand.stl" "$S" slice-20pct --fill-density 20% > /dev/null
[ -f "$S/slice-gyroid.json" ] || bash slicer/slice.sh "$S/stand.stl" "$S" slice-gyroid --fill-pattern gyroid > /dev/null
[ -f "$S/slice-3w20g.json" ] || bash slicer/slice.sh "$S/stand.stl" "$S" slice-3w20g --perimeters 3 --fill-density 20% --fill-pattern gyroid > /dev/null
[ -f "$S/slice-100pct.json" ] || bash slicer/slice.sh "$S/stand.stl" "$S" slice-100pct --fill-density 100% --fill-pattern rectilinear > /dev/null
[ -f "$S/slice-50pct.json" ] || bash slicer/slice.sh "$S/stand.stl" "$S" slice-50pct --fill-density 50% > /dev/null
[ -f "$S/slice-60pct.json" ] || bash slicer/slice.sh "$S/stand.stl" "$S" slice-60pct --fill-density 60% > /dev/null
echo "sliced: $(ls "$ROOT"/*/slice-speed.json | wc -l) cells"
