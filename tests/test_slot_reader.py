"""probe.slot_from_sketch: the slot's floor corners and the top edge the phone leans on, read from the design's
SlotProfile sketch whichever way the slot leans (a run may flip back_angle to 110 deg, so the phone leans on the
other wall). Also score.behaviour reads parameters.change in its {name, expression} form."""
import math
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'probe'))
sys.path.insert(0, os.path.join(HERE, '..', 'claude-run'))
import probe as PR  # noqa: E402


def sketch(F, C, angle_deg, depth=25.0):
    a = math.radians(angle_deg)
    ax = (-math.cos(a), math.sin(a))
    up_f = (F[0] + depth * ax[0], F[1] + depth * ax[1])
    up_c = (C[0] + depth * ax[0], C[1] + depth * ax[1])
    w = lambda p: [60.0, p[0], p[1]]  # noqa: E731
    return {'points': [{'id': 'l1.start', 'world': w(F)}, {'id': 'l1.end', 'world': w(C)},
                       {'id': 'l2.end', 'world': w(up_c)}, {'id': 'l3.end', 'world': w(up_f)}]}


def test_part1_slot_leans_on_the_front_wall():
    F, C = (15.0, 8.0), (24.396926, 11.420201)
    lf, lc, e = PR.slot_from_sketch(sketch(F, C, 70.0), 30.0)
    assert lf == pytest.approx(F) and lc == pytest.approx(C)
    assert e[0] == pytest.approx(15.0 - 22.0 / math.tan(math.radians(70)), abs=1e-6) and e[1] == 30.0


def test_flipped_slot_leans_on_the_other_wall():
    # back_angle 110: the slot leans toward +y; the floor runs down toward +y; the phone rests on the +y wall
    F, C = (15.0, 11.42), (24.397, 8.0)
    lf, lc, e = PR.slot_from_sketch(sketch(F, C, 110.0), 30.0)
    assert lf == pytest.approx(C) and lc == pytest.approx(F)
    assert e[0] > C[0] and e[1] == 30.0


def test_behaviour_reads_parameters_change_name_expression():
    import json
    import tempfile
    import score as S
    p = os.path.join(tempfile.mkdtemp(), 'transcript.jsonl')
    with open(p, 'w', encoding='utf-8') as f:
        f.write(json.dumps({'dir': 'client->server', 'msg': {'id': 1, 'method': 'tools/call', 'params': {
            'name': 'batch', 'arguments': {'commands': [
                {'command': 'parameters.change', 'params': {'name': 'back_angle', 'expression': '110 deg'}}]}}}}) + '\n')
    assert S.behaviour(p)['changed_parameters'] == {'back_angle': '110 deg'}
