"""THE PROBE (no AI, $0): part 1's phone stand with a phone-sized block in its slot, in SolidCraft 0.22.0, over MCP,
behind the logging proxy (every request/reply in <cell>/transcript.jsonl, which the video's tool-call panels cite).

    docker run --rm -v <lab>:/work -v <lab>/out/probe/0.22.0:/lab/out -w /work solidcraft-tipping-lab:0.22.0 \
        python3 probe/probe.py CELL [CELL ...]

A cell = (front_lip, phone_thickness, phone block length x width x thickness, phone grams). Per cell:
  open part 1's design (a copy), set the named sizes, give the stand built-in PLA (1.24 g/cm3), read the slot sketch,
  place the phone block at the settled pose (tip/physics.py slot_pose: it leans on the slot's sharp top edge and slides
  into the play), give it a material that makes its grams, check SolidCraft finds no overlap, ask for mass + balance
  point both ways (component.properties: reads the materials; inspect.center_of_mass: uniform density), export the
  stand and the phone as STL, save the design, and write pose.json + props.json. Slicing and the margin table happen
  after, outside SolidCraft (slicer/slice.sh, probe/analyse.py)."""
import datetime
import json
import math
import os
import shutil
import sys

LAB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.join(LAB, 'tests'))
sys.path.insert(0, LAB)
from mcp_client import Hang, McpClient, SERVER_CMD  # noqa: E402
from tip import physics as P  # noqa: E402

OUT = '/lab/out'
PROXY = os.path.join(LAB, 'proxy', 'mcp_log_proxy.py')
DESIGN = os.path.join(LAB, 'data', 'part1-stand.solidcraft')
PHONES = {  # name: (length, width, grams); thickness = phone_thickness (bare 9, cased 12)
    'p165': (150.0, 72.0, 165.0), 'p190': (150.0, 72.0, 190.0), 'p210': (150.0, 72.0, 210.0),
    'p250': (163.0, 78.0, 250.0),
}


def cells():
    c = {}
    for k in PHONES:
        c[f'lip15-{k}'] = dict(front_lip=15.0, phone_thickness=9.0, phone=k)
    for lip in (20, 25, 30, 35, 40, 45):
        c[f'lip{lip}-p250'] = dict(front_lip=float(lip), phone_thickness=9.0, phone='p250')
        c[f'lip{lip}-p190'] = dict(front_lip=float(lip), phone_thickness=9.0, phone='p190')
    for lip in (15, 30, 35, 40, 45):
        c[f'lip{lip}-p250-case'] = dict(front_lip=float(lip), phone_thickness=12.0, phone='p250')
    return c


class Session:
    def __init__(self, transcript):
        self.c = McpClient(['python3', PROXY, '--log', transcript, '--watchdog', '180', '--'] + SERVER_CMD, timeout_s=240)
        self.c.start()

    def call(self, name, args):
        r = self.c.call_tool(name, args)
        t = '\n'.join(b['text'] for b in r.get('content', []) if b.get('type') == 'text')
        try:
            return json.loads(t)
        except json.JSONDecodeError:
            return t

    def ex(self, command, params):
        return self.call('execute', {'command': command, 'params': params})

    def close(self):
        self.c.close()


def save(d, name, obj):
    with open(os.path.join(d, name), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(obj, f, indent=1, ensure_ascii=False, default=str)
        f.write('\n')


def slot_from_sketch(sk, top_z):
    pts = {p['id']: p['world'] for p in sk['points']}
    F = (pts['l1.start'][1], pts['l1.start'][2])        # floor, front-wall end
    C = (pts['l1.end'][1], pts['l1.end'][2])            # floor, back-wall end
    up = (pts['l3.end'][1], pts['l3.end'][2])           # front wall, upper end (above the top: cut off by it)
    t = (top_z - F[1]) / (up[1] - F[1])
    E = (F[0] + t * (up[0] - F[0]), top_z)              # the front wall's sharp top edge
    return F, C, E


def run_cell(name, spec):
    d = os.path.join(OUT, name)
    os.makedirs(d, exist_ok=True)
    L, W, g = PHONES[spec['phone']]
    T = spec['phone_thickness']
    res = {'cell': name, 'spec': spec, 'phone_block_mm': [L, W, T], 'phone_g': g,
           'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')}
    shutil.copy(DESIGN, os.path.join(d, 'design.solidcraft'))
    s = Session(os.path.join(d, 'transcript.jsonl'))
    try:
        res['open'] = s.call('open', {'path': f'{OUT}/{name}/design.solidcraft'})
        for pname in ('front_lip', 'phone_thickness'):
            if pname in spec:
                res[f'set_{pname}'] = s.call('set_parameter', {'name': pname, 'value': spec[pname]})
        res['assign_pla'] = s.ex('material.assign', {'bodies': ['PhoneStand'], 'material': 'PLA'})
        m = s.call('measure', {'body': 'PhoneStand'})
        b = m['bodies'][0]
        res['stand_solid'] = {'mass_g': b['mass_g'], 'com': b['center_of_mass'], 'volume_mm3': b['volume_mm3'],
                              'bbox': b['bbox'], 'material': b['material'], 'density': b['density_g_cm3']}
        top_z = b['bbox']['max'][2]
        sk = s.ex('sketch.inspect', {'sketch': 'SlotProfile'})
        F, C, E = slot_from_sketch(sk, top_z)
        res['slot'] = {'front_floor': F, 'back_floor': C, 'front_top_edge': E}
        poses = {k: P.slot_pose(F, C, E, T, L, lean=k) for k in ('flush', 'settled')}
        res['poses'] = poses
        pose = poses['settled']
        x0 = (b['bbox']['min'][0] + b['bbox']['max'][0]) / 2 - W / 2
        tilt_from_vertical = 90.0 - pose['axis_deg']
        fy, fz = pose['bottom_corners_yz'][0]           # bottom-front corner
        res['phone_box'] = s.call('batch', {'commands': [
            {'command': 'solid.box', 'params': {'length': W, 'width': T, 'height': L, 'corner': [x0, 0, 0],
                                                'body_name': 'Phone'}},
            {'command': 'solid.move', 'params': {'bodies': ['Phone'], 'axis': [1, 0, 0],
                                                 'angle': f'{tilt_from_vertical} deg'}},
            {'command': 'solid.move', 'params': {'bodies': ['Phone'], 'translate': [0, fy, fz]}},
        ]})
        vol_cm3 = L * W * T / 1000.0
        mat = f'Phone block {int(g)} g'
        res['phone_material'] = s.ex('material.create', {'name': mat, 'density_g_cm3': g / vol_cm3})
        s.ex('material.assign', {'bodies': ['Phone'], 'material': mat})
        res['interference'] = s.ex('inspect.interference', {'bodies': ['PhoneStand', 'Phone']})
        props = s.ex('component.properties', {})
        res['combined_solidcraft'] = {'mass_g': props['total']['mass_g'], 'com': props['total']['center_of_mass']}
        pb = [x for x in props['bodies'] if x['name'] == 'Phone'][0]
        res['phone_solidcraft'] = {'mass_g': pb['mass_g'], 'com': pb['center_of_mass'], 'bbox': pb['bbox']}
        res['uniform_com'] = s.ex('inspect.center_of_mass', {})
        s.call('export', {'path': f'{OUT}/{name}/stand.stl', 'bodies': ['PhoneStand']})
        s.call('export', {'path': f'{OUT}/{name}/phone.stl', 'bodies': ['Phone']})
        res['save'] = s.call('save', {'path': f'{OUT}/{name}/design.solidcraft'})
        res['ok'] = True
    except Hang as e:
        res['HANG'] = str(e)
    except Exception as e:  # recorded, not hidden
        res['ok'] = False
        res['error'] = repr(e)
    finally:
        s.close()
    save(d, 'cell.json', res)
    keep = ('cell', 'ok', 'error')
    print(json.dumps({k: res.get(k) for k in keep} | {
        'stand_g': round(res.get('stand_solid', {}).get('mass_g', float('nan')), 2),
        'overlaps': (res.get('interference') or {}).get('count') if isinstance(res.get('interference'), dict) else None,
        'combined_com': res.get('combined_solidcraft', {}).get('com')}), flush=True)
    return res


if __name__ == '__main__':
    all_cells = cells()
    names = sys.argv[1:] or list(all_cells)
    for n in names:
        run_cell(n, all_cells[n])
