"""THE PROBE (no AI, $0): part 1's phone stand with a phone-sized block in its slot, in SolidCraft 0.22.0, over MCP,
behind the logging proxy (every request/reply in <cell>/transcript.jsonl, which the video's tool-call panels cite).
The same run_cell() scores Claude's designs (claude-run/score.py): it only reads a design, it never trusts a reply.

    docker run --rm -v <lab>:/work -v <lab>/out/probe/0.22.0:/lab/out -w /work solidcraft-tipping-lab:0.22.0 \
        python3 probe/probe.py CELL [CELL ...]

A cell = (a design file, optional named sizes to set, a phone block). Per cell: open a copy of the design, set the
named sizes, give every stand body built-in PLA (1.24 g/cm3; the stand = every body not named like a phone, so a phone
body Claude added to measure is left out), read the slot sketch, place a phone block at the settled pose (tip/physics.py
slot_pose: it leans on the slot's sharp top edge and slides into the play), give it a material that makes its grams,
check SolidCraft finds no overlap, read mass + balance point both ways (component.properties: reads the materials;
inspect.center_of_mass: uniform density), export the stand and the block as STL, save, write cell.json. Slicing and the
margin table happen after, outside SolidCraft (probe/slice_cells.sh, probe/analyse.py)."""
import datetime
import json
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
PHONES = {  # name: (length, width, grams); thickness = the design's phone_thickness (bare 9) unless a cell sets it
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
    for lip in (15, 30, 35, 40):   # a slot sized for a phone in a case (12 mm), with the bare phone in it: the most lean
        c[f'lip{lip}-p190-caseoff'] = dict(front_lip=float(lip), phone_thickness=12.0, block_thickness=9.0, phone='p190')
        c[f'lip{lip}-p250-caseoff'] = dict(front_lip=float(lip), phone_thickness=12.0, block_thickness=9.0, phone='p250')
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


def is_phone_body(b):
    return 'phone' in b['name'].lower() and b['name'].lower() != 'phonestand'


def run_cell(name, spec, design=DESIGN, out_root=OUT):
    d = os.path.join(out_root, name)
    os.makedirs(d, exist_ok=True)
    L, W, g = PHONES[spec['phone']]
    res = {'cell': name, 'spec': spec, 'design_in': os.path.basename(design), 'phone_g': g,
           'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')}
    shutil.copy(design, os.path.join(d, 'design.solidcraft'))
    s = Session(os.path.join(d, 'transcript.jsonl'))
    try:
        res['open'] = s.call('open', {'path': f'{d}/design.solidcraft'})
        for pname in ('front_lip', 'phone_thickness'):
            if pname in spec:
                res[f'set_{pname}'] = s.call('set_parameter', {'name': pname, 'value': spec[pname]})
        plist = s.ex('parameters.list', {})
        params = {p['name']: p['value'] for p in plist.get('parameters', [])} if isinstance(plist, dict) else {}
        res['parameters'] = params
        T = float(spec.get('block_thickness', spec.get('phone_thickness', params.get('phone_thickness', 9.0))))
        res['phone_block_mm'] = [L, W, T]
        allb = s.call('measure', {})['bodies']
        res['bodies_all'] = [b['name'] for b in allb]
        res['stand_bodies'] = [b['name'] for b in allb if not is_phone_body(b)]
        res['assign_pla'] = s.ex('material.assign', {'bodies': res['stand_bodies'], 'material': 'PLA'})
        stand = [b for b in s.call('measure', {})['bodies'] if b['name'] in res['stand_bodies']]
        mass = sum(b['mass_g'] for b in stand)
        com = [sum(b['mass_g'] * b['center_of_mass'][i] for b in stand) / mass for i in range(3)]
        lo = [min(b['bbox']['min'][i] for b in stand) for i in range(3)]
        hi = [max(b['bbox']['max'][i] for b in stand) for i in range(3)]
        res['stand_solid'] = {'mass_g': mass, 'com': com, 'volume_mm3': sum(b['volume_mm3'] for b in stand),
                              'bbox': {'min': lo, 'max': hi}, 'material': 'PLA', 'density': 1.24}
        sk = s.ex('sketch.inspect', {'sketch': 'SlotProfile'})
        if not isinstance(sk, dict) or 'points' not in sk:
            res['error'] = 'no SlotProfile sketch: score by hand'
            raise RuntimeError(res['error'])
        F, C, E = slot_from_sketch(sk, hi[2])
        res['slot'] = {'front_floor': F, 'back_floor': C, 'front_top_edge': E}
        poses = {k: P.slot_pose(F, C, E, T, L, lean=k) for k in ('flush', 'settled')}
        res['poses'] = poses
        pose = poses['settled']
        x0 = (lo[0] + hi[0]) / 2 - W / 2
        tilt_from_vertical = 90.0 - pose['axis_deg']
        fy, fz = pose['bottom_corners_yz'][0]           # bottom-front corner
        res['phone_box'] = s.call('batch', {'commands': [
            {'command': 'solid.box', 'params': {'length': W, 'width': T, 'height': L, 'corner': [x0, 0, 0],
                                                'body_name': 'LabPhone'}},
            {'command': 'solid.move', 'params': {'bodies': ['LabPhone'], 'axis': [1, 0, 0],
                                                 'angle': f'{tilt_from_vertical} deg'}},
            {'command': 'solid.move', 'params': {'bodies': ['LabPhone'], 'translate': [0, fy, fz]}},
        ]})
        mat = f'Lab phone block {int(g)} g'
        res['phone_material'] = s.ex('material.create', {'name': mat, 'density_g_cm3': g / (L * W * T / 1000.0)})
        s.ex('material.assign', {'bodies': ['LabPhone'], 'material': mat})
        res['interference'] = s.ex('inspect.interference', {'bodies': res['stand_bodies'] + ['LabPhone']})
        props = s.ex('component.properties', {})
        mine = [x for x in props['bodies'] if x['name'] in res['stand_bodies'] + ['LabPhone']]
        pb = [x for x in mine if x['name'] == 'LabPhone'][0]
        res['phone_solidcraft'] = {'mass_g': pb['mass_g'], 'com': pb['center_of_mass'], 'bbox': pb['bbox']}
        mt = sum(x['mass_g'] for x in mine)
        res['combined_solidcraft'] = {'mass_g': mt, 'com': [sum(x['mass_g'] * x['center_of_mass'][i] for x in mine) / mt
                                                            for i in range(3)]}
        res['uniform_com'] = s.ex('inspect.center_of_mass', {'bodies': res['stand_bodies'] + ['LabPhone']})
        s.call('export', {'path': f'{d}/stand.stl', 'bodies': res['stand_bodies']})
        s.call('export', {'path': f'{d}/phone.stl', 'bodies': ['LabPhone']})
        res['save'] = s.call('save', {'path': f'{d}/design.solidcraft'})
        res['ok'] = True
    except Hang as e:
        res['ok'] = False
        res['HANG'] = str(e)
    except Exception as e:  # recorded, not hidden
        res['ok'] = False
        res.setdefault('error', repr(e))
    finally:
        s.close()
    save(d, 'cell.json', res)
    inter = res.get('interference')
    print(json.dumps({'cell': res['cell'], 'ok': res.get('ok'), 'error': res.get('error'),
                      'stand_g': round(res.get('stand_solid', {}).get('mass_g', float('nan')), 2),
                      'overlaps': inter.get('count') if isinstance(inter, dict) else None,
                      'combined_com': res.get('combined_solidcraft', {}).get('com')}), flush=True)
    return res


if __name__ == '__main__':
    all_cells = cells()
    names = sys.argv[1:] or list(all_cells)
    for n in names:
        run_cell(n, all_cells[n])
