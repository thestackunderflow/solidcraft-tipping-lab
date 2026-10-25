"""The margin table from the probe cells (no AI, $0), run after probe/probe.py and probe/slice_cells.sh:

    docker run --rm -v <lab>:/work -w /work solidcraft-tipping-lab:0.22.0 python3 probe/analyse.py out/probe/0.22.0

Per cell: the stand as solid (SolidCraft's component.properties, cross-checked by the lab's own STL maths), the stand as
sliced (the G-code's grams and balance point, translated back from the slicer's --center), the phone at both poses
(flush, settled) with its own balance point shifted -5/0/+5 mm along its length, the footprint from the stand STL's
bottom, the tipping edge = the footprint edge nearest the phone. Writes <dir>/numbers.json and prints a summary."""
import json
import math
import os
import sys

import numpy as np

LAB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.join(LAB, 'tests'))
sys.path.insert(0, LAB)
from stl_tools import bottom_points, centre_of_mass, read_stl, volume, watertight, bodies  # noqa: E402
from tip import model as M  # noqa: E402
from tip import physics as P  # noqa: E402

PLA = 1.24


def gcode_back_to_model(centre, stl_tris, at=(125.0, 105.0)):
    p = np.asarray(stl_tris, dtype=float).reshape(-1, 3)
    cx = (p[:, 0].min() + p[:, 0].max()) / 2
    cy = (p[:, 1].min() + p[:, 1].max()) / 2
    return [centre[0] - (at[0] - cx), centre[1] - (at[1] - cy), centre[2]]


def tipping_edge(poly, phone_y):
    """The footprint edge the phone leans over: the edge whose line is nearest the phone's balance point in y."""
    hull = P._hull(poly)
    best = None
    for i in range(len(hull)):
        a, b = hull[i], hull[(i + 1) % len(hull)]
        if abs(a[1] - b[1]) < 1e-6:   # an edge along x (front or back)
            d = abs(a[1] - phone_y)
            if best is None or d < best[0]:
                best = (d, (a, b))
    return best[1]


def cell_numbers(cdir, slice_name='speed'):
    c = json.load(open(os.path.join(cdir, 'cell.json'), encoding='utf-8'))
    if not c.get('ok'):
        return {'cell': c['cell'], 'ok': False, 'error': c.get('error')}
    st = read_stl(os.path.join(cdir, 'stand.stl'))
    ph = read_stl(os.path.join(cdir, 'phone.stl'))
    sl = json.load(open(os.path.join(cdir, f'slice-{slice_name}.json'), encoding='utf-8'))
    poly = P.support_polygon(bottom_points(st))
    pose = c['poses']['settled']
    xmid = float(np.mean(read_stl(os.path.join(cdir, 'stand.stl')).reshape(-1, 3)[:, 0][[0]])) if False else \
        (c['stand_solid']['bbox']['min'][0] + c['stand_solid']['bbox']['max'][0]) / 2
    phone_g = c['phone_g']
    poses = {k: [xmid, v['centre_yz'][0], v['centre_yz'][1]] for k, v in c['poses'].items()}
    edge = tipping_edge(poly, poses['settled'][1])
    a = math.radians(pose['axis_deg'])
    sgn = -1.0 if poses['settled'][1] < c['slot']['front_floor'][0] else 1.0
    along = [0.0, sgn * math.cos(a), math.sin(a)]
    sl_com = gcode_back_to_model(sl['part_centre_from_gcode'], st)
    stands = {'solid': (c['stand_solid']['mass_g'], c['stand_solid']['com']),
              'sliced': (sl['part_g_from_gcode'], sl_com)}
    b = M.band(stands, {phone_g: poses}, poly, edge, along=along, shift_mm=5.0)[phone_g]
    by = M.summary_by_stand(b)
    central = {s: M.margin_row(stands[s][0], stands[s][1], phone_g, poses['settled'], poly, edge)
               for s in stands}
    return {
        'cell': c['cell'], 'ok': True, 'spec': c['spec'], 'phone_g': phone_g, 'phone_block_mm': c['phone_block_mm'],
        'stand_solid_solidcraft': c['stand_solid'],
        'stand_solid_stl': {'volume_mm3': volume(st), 'com': [float(v) for v in centre_of_mass(st)],
                            'mass_g_at_1.24': volume(st) * PLA / 1000, 'watertight': watertight(st),
                            'bodies': bodies(st)},
        'stand_sliced': {'part_g': sl['part_g_from_gcode'], 'slicer_total_g': sl['slicer_total_g'],
                         'com': sl_com, 'time': sl['time'], 'settings': sl['settings']},
        'phone_stl_com': [float(v) for v in centre_of_mass(ph)], 'phone_pose_settled': poses['settled'],
        'phone_pose_flush': poses['flush'], 'tilt_deg': pose['tilt_deg'], 'axis_deg': pose['axis_deg'],
        'footprint': poly, 'tipping_edge': edge,
        'interference_count': (c.get('interference') or {}).get('count'),
        'combined_solidcraft': c['combined_solidcraft'], 'uniform_com': c['uniform_com'].get('center'),
        'central': central, 'band': {'min_mm': b['min_mm'], 'max_mm': b['max_mm'], 'by_stand': by},
    }


if __name__ == '__main__':
    root = sys.argv[1]
    rows = {}
    for name in sorted(os.listdir(root)):
        d = os.path.join(root, name)
        if os.path.isfile(os.path.join(d, 'cell.json')) and os.path.isfile(os.path.join(d, 'slice-speed.json')):
            rows[name] = cell_numbers(d)
    with open(os.path.join(root, 'numbers.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(rows, f, indent=1)
        f.write('\n')
    for n, r in rows.items():
        if not r.get('ok'):
            print(n, 'FAILED', r.get('error'))
            continue
        cs, cl = r['central']['solid'], r['central']['sliced']
        bs = r['band']['by_stand']
        print(f"{n:22s} stand {r['stand_solid_solidcraft']['mass_g']:.1f} g solid / {r['stand_sliced']['part_g']:.1f} g sliced "
              f"| margin solid {cs['margin_mm']:+.2f} ({bs['solid']['min_mm']:+.2f}..{bs['solid']['max_mm']:+.2f}) "
              f"sliced {cl['margin_mm']:+.2f} ({bs['sliced']['min_mm']:+.2f}..{bs['sliced']['max_mm']:+.2f}) "
              f"| overlaps {r['interference_count']}")
