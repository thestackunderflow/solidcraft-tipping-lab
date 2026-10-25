"""slicer/resolve_preset.py: a stock PrusaSlicer preset, resolved from the vendor bundle's inherits chain into one flat
config (parents left to right, later parents win, the preset's own keys win last)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'slicer'))
import resolve_preset as R  # noqa: E402

INI = """[vendor]
name = Test

[print:*common*]
layer_height = 0.2
perimeters = 3
fill_density = 20%

[print:*fast*]
perimeters = 2
top_solid_layers = 5

[print:0.20mm BASE]
inherits = *common*
fill_pattern = grid

[print:0.20mm SPEED]
inherits = 0.20mm BASE; *fast*
fill_density = 15%
compatible_printers_condition = printer_model=="X"

[filament:PLA]
filament_density = 1.24
"""


def test_inherits_chain_later_parents_and_own_keys_win():
    secs = R.parse(INI)
    p = R.resolve(secs, 'print', '0.20mm SPEED')
    assert p['layer_height'] == '0.2'
    assert p['perimeters'] == '2'          # *fast* (later parent) beats *common*
    assert p['fill_density'] == '15%'      # own key beats the parents
    assert p['fill_pattern'] == 'grid'
    assert p['top_solid_layers'] == '5'
    assert 'inherits' not in p and 'compatible_printers_condition' not in p


def test_flat_config_has_every_key_once():
    secs = R.parse(INI)
    text = R.flat_config(secs, print_name='0.20mm SPEED', filament_name='PLA', printer_name=None)
    lines = [l for l in text.splitlines() if l and not l.startswith('#')]
    keys = [l.split(' = ', 1)[0] for l in lines]
    assert len(keys) == len(set(keys))
    assert 'filament_density = 1.24' in lines and 'perimeters = 2' in lines
