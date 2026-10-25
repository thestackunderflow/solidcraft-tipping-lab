"""claude-run/score.py, the behaviour half: what Claude asked SolidCraft, read from the logging proxy's JSON-RPC rows
(never from Claude's chat text): did it weigh things with materials (component.properties / occurrence.properties /
measure after material.assign or material.create), did it use the uniform-density tool, did it add a phone body, which
named sizes it changed. Proven on hand-made rows."""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'claude-run'))
import score as S  # noqa: E402


def rows_file(calls):
    p = os.path.join(tempfile.mkdtemp(), 'transcript.jsonl')
    with open(p, 'w', encoding='utf-8') as f:
        for i, (name, args, result) in enumerate(calls, start=1):
            f.write(json.dumps({'dir': 'client->server', 'msg': {'jsonrpc': '2.0', 'id': i, 'method': 'tools/call',
                                                               'params': {'name': name, 'arguments': args}}}) + '\n')
            f.write(json.dumps({'dir': 'server->client', 'msg': {'jsonrpc': '2.0', 'id': i, 'result': {
                'content': [{'type': 'text', 'text': json.dumps(result)}]}}}) + '\n')
    return p


def test_measured_with_materials():
    p = rows_file([
        ('execute', {'command': 'material.create', 'params': {'name': 'Phone', 'density_g_cm3': 2.0}}, {'ok': True}),
        ('batch', {'commands': [{'command': 'solid.box', 'params': {'length': 72, 'width': 9, 'height': 150,
                                                                    'body_name': 'Phone'}}]}, {'ok': True}),
        ('execute', {'command': 'component.properties', 'params': {}}, {'total': {}}),
        ('set_parameter', {'name': 'front_lip', 'value': 40}, {'ok': True}),
    ])
    b = S.behaviour(p)
    assert b['weighed_with_materials'] is True
    assert b['used_uniform_com'] is False
    assert b['added_phone_body'] is True
    assert b['changed_parameters'] == {'front_lip': 40}
    assert b['tool_calls'] == 4


def test_uniform_density_only_and_no_phone():
    p = rows_file([
        ('execute', {'command': 'inspect.center_of_mass', 'params': {}}, {'center': [0, 0, 0]}),
        ('execute', {'command': 'parameters.change', 'params': {'changes': {'stand_depth': '80'}}}, {'ok': True}),
    ])
    b = S.behaviour(p)
    assert b['weighed_with_materials'] is False
    assert b['used_uniform_com'] is True
    assert b['added_phone_body'] is False
    assert b['changed_parameters'] == {'stand_depth': '80'}


def test_failed_calls_are_counted():
    p = rows_file([('batch', {'commands': []}, {'ok': False, 'failed': {'error': 'boom'}})])
    b = S.behaviour(p)
    assert b['failed_calls'] == 1 and b['failed_errors'] == ['boom']
