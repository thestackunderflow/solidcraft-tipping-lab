#!/usr/bin/env bash
# Slice an STL headlessly with PrusaSlicer 2.9.2 (image habs-slicer:0.2) using the BUNDLED stock presets, resolved from
# the vendor bundle by slicer/resolve_preset.py (the CLI can't load them by name without a datadir):
#   printer "Original Prusa MK4S 0.4 nozzle", print "0.20mm SPEED @MK4S 0.4", material "Prusament PLA @MK4S"
# (arc fitting ON, "emit_center", as in the preset: the G-code has G2/G3 arcs, which tip/gcode_mass.py counts), plus an optional settings strip (walls, infill %, pattern) for the sensitivity
# rows. Writes <out>/<name>.gcode + <name>.json (grams, time, the print's balance point from tip/gcode_mass.py).
#   bash slicer/slice.sh STL OUTDIR NAME [--perimeters N] [--fill-density P%] [--fill-pattern X]
set -euo pipefail
cd "$(dirname "$0")/.."
EXP="$(pwd -W 2>/dev/null || pwd)"
STL=$1; OUT=$2; NAME=$3; shift 3
mkdir -p "$OUT"
MSYS_NO_PATHCONV=1 docker run --rm -v "$EXP:/w" -w /w habs-slicer:0.2 sh -c "
  set -e
  python3 slicer/resolve_preset.py /usr/share/PrusaSlicer/profiles/PrusaResearch.ini '0.20mm SPEED @MK4S 0.4' \
    'Prusament PLA @MK4S' 'Original Prusa MK4S 0.4 nozzle' > '$OUT/$NAME-config.ini'
  prusa-slicer --load '$OUT/$NAME-config.ini' $* --center 125,105 --binary-gcode=0 \
    --export-gcode -o '$OUT/$NAME.gcode' '$STL' > '$OUT/$NAME-log.txt' 2>&1
  python3 -c \"
import json, re, sys
sys.path.insert(0, '.')
from tip.gcode_mass import mass_and_centre
g = open('$OUT/$NAME.gcode', encoding='utf-8', errors='replace').read()
foot = dict(re.findall(r'^; ([^=\n]+?) = (.+)$', g, re.M))
r = mass_and_centre(g, density=float(foot['filament_density']), diameter=float(foot['filament_diameter']), from_first_layer=True)
keys = ['print_settings_id', 'layer_height', 'perimeters', 'fill_density', 'fill_pattern', 'top_solid_layers',
        'bottom_solid_layers', 'filament_density', 'filament_diameter', 'arc_fitting', 'skirts', 'brim_width']
rep = {'stl': '$STL', 'settings': {k: foot.get(k) for k in keys},
       'slicer_total_g': float(foot['total filament used [g]']), 'time': foot.get('estimated printing time (normal mode)'),
       'part_g_from_gcode': round(r['mass_g'], 3), 'part_centre_from_gcode': [round(v, 3) for v in r['centre']],
       'note': 'part_* counts beads from the first ;LAYER_CHANGE on (the purge line before it is left out); the G-code is centred at 125,105'}
json.dump(rep, open('$OUT/$NAME.json', 'w'), indent=1)
print(json.dumps(rep))
\"
  prusa-slicer --help | head -1 >> '$OUT/$NAME-log.txt'
"
