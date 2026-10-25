"""The preset strip at 210 g: part 1's stand sliced 5 more ways (probe/slice_cells.sh), each against the 210 g phone at
the settled pose; writes out/probe/0.22.0/strip-p210.json. python3 probe/strip.py"""
import json, os, sys
LAB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, LAB); sys.path.insert(0, os.path.join(LAB, 'tests')); sys.path.insert(0, os.path.join(LAB, 'probe'))
from tip import model as M
from stl_tools import read_stl
import analyse as AN
root = os.path.join(LAB, 'out', 'probe', '0.22.0')
n = json.load(open(os.path.join(root, 'numbers.json'), encoding='utf-8'))['lip15-p210']
st = read_stl(os.path.join(root, 'lip15-p190', 'stand.stl'))
out = {}
for k in ('speed', '3walls', '20pct', 'gyroid', '3w20g', '100pct'):
    s = json.load(open(os.path.join(root, 'lip15-p190', f'slice-{k}.json'), encoding='utf-8'))
    com = AN.gcode_back_to_model(s['part_centre_from_gcode'], st)
    r = M.margin_row(s['part_g_from_gcode'], com, 210.0, n['phone_pose_settled'], n['footprint'], n['tipping_edge'])
    out[k] = {'grams': s['part_g_from_gcode'], 'time': s['time'], 'com_y': round(com[1], 2), 'margin_210g_mm': round(r['margin_mm'], 2)}
json.dump(out, open(os.path.join(root, 'strip-p210.json'), 'w'), indent=1)
for k, v in out.items(): print(k, v)
