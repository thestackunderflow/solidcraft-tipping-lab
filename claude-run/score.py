"""Score every agent run in out/runs/<arm>-<n>/ (tipping lab). Two halves, neither trusts Claude's chat text:

1. behaviour(): what Claude asked SolidCraft, from the logging proxy's JSON-RPC rows: weighed with materials or not,
   used the uniform-density tool, added a phone body, which named sizes it changed, failed calls.
2. the design: the run's saved design is re-opened by probe.run_cell() (inside the lab image; a 210 g phone block at
   the settled pose, the stand in PLA), sliced with the stock SPEED preset, and probe/analyse.py's margin table is
   computed. Pass = the stand still stands with the 210 g phone AS SLICED (central margin > 0); also reported: the band,
   the solid margin, and whether the phone's own balance point sits over the footprint (the viewer's own criterion).

    python3 claude-run/score.py behaviour            (host or image: writes out/runs/BEHAVIOUR.json)
    python3 claude-run/score.py design RUN_DIR       (inside the image: re-opens the design -> RUN_DIR/score/<cell>)
    python3 claude-run/score.py table                (after slicing: out/runs/SCORES.json)"""
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.join(HERE, '..')
WEIGH = {'component.properties', 'occurrence.properties'}
MATERIAL = {'material.assign', 'material.create'}


def _rows(p):
    with open(p, encoding='utf-8') as f:
        return [json.loads(l) for l in f if l.strip()]


def _commands(name, args):
    if name == 'batch':
        return [c for c in args.get('commands', []) if isinstance(c, dict)]
    if name == 'execute':
        return [{'command': args.get('command'), 'params': args.get('params') or {}}]
    return [{'command': name, 'params': args}]


def behaviour(transcript):
    rows = _rows(transcript)
    calls, replies = {}, {}
    for r in rows:
        m = r.get('msg') or {}
        if r.get('dir') == 'client->server' and m.get('method') == 'tools/call':
            calls[m['id']] = m['params']
        elif r.get('dir') == 'server->client' and 'id' in m and 'result' in m:
            replies[m['id']] = m['result']
    cmds, failed, errors = [], 0, []
    for i, p in calls.items():
        cmds += _commands(p['name'], p.get('arguments') or {})
        res = replies.get(i) or {}
        t = '\n'.join(c.get('text', '') for c in res.get('content', []) if c.get('type') == 'text')
        try:
            body = json.loads(t)
        except (json.JSONDecodeError, TypeError):
            body = t
        if res.get('isError') or (isinstance(body, dict) and body.get('ok') is False):
            failed += 1
            errors.append((body.get('failed') or {}).get('error') if isinstance(body, dict) else str(body)[:200])
    names = [c.get('command') for c in cmds]
    used_material = any(n in MATERIAL for n in names)
    weighed = any(n in WEIGH for n in names) or (used_material and 'measure' in names)
    phone = False
    changed = {}
    for c in cmds:
        p = c.get('params') or {}
        n = c.get('command')
        if n and n.startswith('solid.') and 'phone' in json.dumps(p).lower():
            phone = True
        if n == 'set_parameter' and 'name' in p:
            changed[p['name']] = p.get('value', p.get('expression'))
        if n == 'parameters.change' and 'name' in p:
            changed[p['name']] = p.get('expression', p.get('value'))
        if n == 'parameters.change':
            ch = p.get('changes') or {}
            if isinstance(ch, dict):
                changed.update(ch)
            elif isinstance(ch, list):
                for x in ch:
                    if isinstance(x, dict) and 'name' in x:
                        changed[x['name']] = x.get('value', x.get('expression'))
    return {'tool_calls': len(calls), 'commands': names, 'failed_calls': failed, 'failed_errors': errors,
            'weighed_with_materials': bool(weighed), 'used_uniform_com': 'inspect.center_of_mass' in names,
            'added_phone_body': phone, 'changed_parameters': changed}


def all_behaviour():
    out = []
    for d in sorted(glob.glob(os.path.join(LAB, 'out', 'runs', '*-*'))):
        if not os.path.isdir(d) or not os.path.exists(os.path.join(d, 'transcript.jsonl')):
            continue
        b = behaviour(os.path.join(d, 'transcript.jsonl'))
        try:
            o = json.load(open(os.path.join(d, 'claude-output.json'), encoding='utf-8'))
        except (OSError, json.JSONDecodeError):
            o = {}
        b.update({'run': os.path.basename(d), 'cost_usd': o.get('total_cost_usd'), 'turns': o.get('num_turns'),
                  'final_answer': (o.get('result') or '')[:2000],
                  'saved_design': os.path.exists(os.path.join(d, 'work', 'stand.solidcraft')),
                  'exported_stl': os.path.exists(os.path.join(d, 'work', 'stand.stl'))})
        out.append(b)
    with open(os.path.join(LAB, 'out', 'runs', 'BEHAVIOUR.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, indent=1)
    return out


def design(run_dir):
    sys.path.insert(0, os.path.join(LAB, 'probe'))
    sys.path.insert(0, LAB)
    import probe as PR
    src = os.path.join(run_dir, 'work', 'stand.solidcraft')
    return PR.run_cell('score-p210', {'phone': 'p210'}, design=src, out_root=os.path.join(run_dir, 'score'))


def table():
    sys.path.insert(0, os.path.join(LAB, 'probe'))
    sys.path.insert(0, LAB)
    import analyse as AN
    beh = {b['run']: b for b in json.load(open(os.path.join(LAB, 'out', 'runs', 'BEHAVIOUR.json'), encoding='utf-8'))}
    rows = []
    for run, b in beh.items():
        cdir = os.path.join(LAB, 'out', 'runs', run, 'score', 'score-p210')
        g = None
        if os.path.exists(os.path.join(cdir, 'slice-speed.json')):
            g = AN.cell_numbers(cdir)
        row = {'run': run, 'cost_usd': b['cost_usd'], 'changed': b['changed_parameters'],
               'weighed_with_materials': b['weighed_with_materials'], 'used_uniform_com': b['used_uniform_com'],
               'added_phone_body': b['added_phone_body'], 'failed_calls': b['failed_calls']}
        if g and g.get('ok'):
            fp = g['footprint']
            ys = [y for _, y in fp]
            own_over = min(ys) <= g['phone_pose_settled'][1] <= max(ys)
            row.update({'stand_g_solid': round(g['stand_solid_solidcraft']['mass_g'], 2),
                        'stand_g_sliced': g['stand_sliced']['part_g'],
                        'margin_solid_mm': round(g['central']['solid']['margin_mm'], 2),
                        'margin_sliced_mm': round(g['central']['sliced']['margin_mm'], 2),
                        'band_sliced_mm': [round(g['band']['by_stand']['sliced']['min_mm'], 2),
                                           round(g['band']['by_stand']['sliced']['max_mm'], 2)],
                        'phone_own_point_over_footprint': bool(own_over),
                        'stands_as_sliced': bool(g['central']['sliced']['margin_mm'] > 0),
                        'overlaps': g['interference_count']})
        else:
            row.update({'scored': 'by hand', 'why': (g or {}).get('error', 'no scored design')})
        rows.append(row)
    with open(os.path.join(LAB, 'out', 'runs', 'SCORES.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump({'runs': rows}, f, indent=1)
    for r in rows:
        print(json.dumps(r))
    return rows


if __name__ == '__main__':
    what = sys.argv[1]
    if what == 'behaviour':
        for b in all_behaviour():
            print(json.dumps({k: b[k] for k in ('run', 'cost_usd', 'weighed_with_materials', 'used_uniform_com',
                                                'added_phone_body', 'changed_parameters', 'failed_calls')}))
    elif what == 'design':
        design(sys.argv[2])
    elif what == 'table':
        table()
