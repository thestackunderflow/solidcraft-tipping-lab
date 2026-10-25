"""Exploration ($0, no AI): what SolidCraft 0.22.0's material and mass-property commands return on part 1's stand.
    docker run --rm -v <lab>:/work -w /work solidcraft-tipping-lab:0.22.0 python3 probe/explore.py"""
import json
import os
import shutil
import sys

LAB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, os.path.join(LAB, 'tests'))
from mcp_client import McpClient  # noqa: E402

OUT = '/lab/out/explore'
os.makedirs(OUT, exist_ok=True)
shutil.copy(os.path.join(LAB, 'data', 'part1-stand.solidcraft'), os.path.join(OUT, 'stand.solidcraft'))


def call(m, name, args):
    r = m.call_tool(name, args)
    t = '\n'.join(b['text'] for b in r.get('content', []) if b.get('type') == 'text')
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        return t


def ex(m, command, params):
    return call(m, 'execute', {'command': command, 'params': params})


m = McpClient(['solidcraft-cli', 'mcp', '--allow-path', '/lab/out'])
m.start()
log = {}
log['open'] = call(m, 'open', {'path': f'{OUT}/stand.solidcraft'})
log['materials'] = ex(m, 'material.list', {})
log['create_pla'] = ex(m, 'material.create', {'name': 'PLA (1.24)', 'density_g_cm3': 1.24})
log['assign'] = ex(m, 'material.assign', {'bodies': ['PhoneStand'], 'material': 'PLA (1.24)'})
log['measure_pla'] = call(m, 'measure', {})
log['com'] = ex(m, 'inspect.center_of_mass', {})
log['props_root'] = ex(m, 'component.properties', {})
log['box'] = call(m, 'batch', {'commands': [{'command': 'solid.box', 'params': {
    'length': 72, 'width': 9, 'height': 150, 'corner': [64, -9, 0], 'body_name': 'Phone'}}]})
log['move'] = call(m, 'batch', {'commands': [{'command': 'solid.move', 'params': {
    'bodies': ['Phone'], 'axis': [1, 0, 0], 'angle': '20 deg'}}]})
log['create_phone'] = ex(m, 'material.create', {'name': 'Phone stand-in 190 g', 'density_g_cm3': 190 / 97.2})
log['assign_phone'] = ex(m, 'material.assign', {'bodies': ['Phone'], 'material': 'Phone stand-in 190 g'})
log['measure_both'] = call(m, 'measure', {})
log['com_both'] = ex(m, 'inspect.center_of_mass', {})
log['props_both'] = ex(m, 'component.properties', {})
m.close()
with open(f'{OUT}/explore.json', 'w', encoding='utf-8', newline='\n') as f:
    json.dump(log, f, indent=1, default=str)
for k, v in log.items():
    print('##', k, json.dumps(v, default=str)[:700])
