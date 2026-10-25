"""End to end: real PrusaSlicer 2.9.2 G-code (stock SPEED preset, but 100% rectilinear infill so the print is solid) of
two shapes whose balance points are known by hand, read by tip/gcode_mass.py (arcs included) via slicer/slice.sh.
The fixtures (tests/fixtures/*-100.json) come from tests/make_fixtures.py + slicer/slice.sh; the G-code is centred at
(125, 105) by the slicer's --center, i.e. the shape's bounding-box centre moves there."""
import json
import os

import pytest

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fixtures')


def load(n):
    return json.load(open(os.path.join(D, f'{n}-100.json'), encoding='utf-8'))


def test_solid_cube_balance_point_is_its_centre_and_mass_is_its_volume():
    r = load('cube20')
    x, y, z = r['part_centre_from_gcode']
    assert x == pytest.approx(125.0, abs=0.1) and y == pytest.approx(105.0, abs=0.1)
    assert z == pytest.approx(10.0, abs=0.2)                    # layers are 0.2 mm: the bead heights quantise z
    assert r['part_g_from_gcode'] == pytest.approx(8.0 * 1.24, rel=0.01)
    assert r['settings']['print_settings_id'] == '0.20mm SPEED @MK4S 0.4'


def test_l_shape_balance_point_is_off_centre_by_the_hand_sum():
    # bar 40 x 10 x 10 at (20, 5) + leg 10 x 30 x 10 at (5, 25): balance point (13.571, 13.571); bbox centre (20, 20)
    r = load('ell')
    bx = (20 * 4000 + 5 * 3000) / 7000
    by = (5 * 4000 + 25 * 3000) / 7000
    x, y, _ = r['part_centre_from_gcode']
    assert x == pytest.approx(125.0 + bx - 20.0, abs=0.1)
    assert y == pytest.approx(105.0 + by - 20.0, abs=0.1)
    assert r['part_g_from_gcode'] == pytest.approx(7.0 * 1.24, rel=0.01)
