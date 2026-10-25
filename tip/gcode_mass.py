"""Mass and balance point of a print from its G-code: every extruding G0/G1 move lays a bead whose mass is the filament
length pushed times the filament's cross-section times its density, placed at the move's midpoint. Retractions
(E without XY motion) and travel moves lay nothing. Arcs (G2/G3) are refused: the lab slices with arc fitting off.

    python3 -m tip.gcode_mass FILE.gcode [density] [diameter]   -> JSON"""
import json
import math
import re
import sys

WORD = re.compile(r'([A-Z])([-+]?\d*\.?\d+)')


def mass_and_centre(text, density=1.24, diameter=1.75, from_first_layer=False):
    area = math.pi * (diameter / 2) ** 2
    rel = False
    x = y = z = 0.0
    e = 0.0
    total = 0.0
    sx = sy = sz = 0.0
    started = not from_first_layer
    for raw in text.splitlines():
        line = raw.split(';', 1)[0].strip()
        if raw.startswith(';LAYER_CHANGE'):
            started = True
        if not line:
            continue
        cmd = line.split()[0]
        if cmd == 'M83':
            rel = True
            continue
        if cmd == 'M82':
            rel = False
            continue
        if cmd in ('G2', 'G3'):
            raise ValueError('arc moves (G2/G3) are not handled: slice with arc fitting off')
        w = dict((k, float(v)) for k, v in WORD.findall(line[len(cmd):]))
        if cmd == 'G92':
            if 'E' in w:
                e = w['E']
            continue
        if cmd not in ('G0', 'G1'):
            continue
        nx, ny, nz = w.get('X', x), w.get('Y', y), w.get('Z', z)
        de = 0.0
        if 'E' in w:
            de = w['E'] if rel else w['E'] - e
            e = e + w['E'] if rel else w['E']
        moved = (nx != x) or (ny != y)
        if de > 0 and moved and started:
            total += de
            sx += de * (x + nx) / 2
            sy += de * (y + ny) / 2
            sz += de * nz
        x, y, z = nx, ny, nz
    if total == 0:
        return {'filament_mm': 0.0, 'mass_g': 0.0, 'centre': None}
    return {'filament_mm': total, 'mass_g': total * area * density / 1000.0,
            'centre': [sx / total, sy / total, sz / total]}


if __name__ == '__main__':
    d = float(sys.argv[2]) if len(sys.argv) > 2 else 1.24
    dia = float(sys.argv[3]) if len(sys.argv) > 3 else 1.75
    r = mass_and_centre(open(sys.argv[1], encoding='utf-8', errors='replace').read(), d, dia, from_first_layer=True)
    print(json.dumps(r, indent=1))
