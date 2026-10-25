"""The printed stand's mass and balance point from the slicer's G-code (tip/gcode_mass.py): every extruding move lays a
bead of filament; its mass is the filament length pushed (E, relative or absolute) times the filament's cross-section
times the density, placed at the move's midpoint. Proven on hand-made G-code before it reads a real file."""
import math
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from tip import gcode_mass as G  # noqa: E402

AREA = math.pi * (1.75 / 2) ** 2  # mm2 of 1.75 mm filament


def test_two_beads_relative_e():
    g = """M83
G1 Z0.2 F600
G1 X0 Y0
G1 X10 Y0 E1.0
G1 X10 Y10 E3.0
"""
    r = G.mass_and_centre(g, density=1.24, diameter=1.75)
    assert r['filament_mm'] == pytest.approx(4.0)
    assert r['mass_g'] == pytest.approx(4.0 * AREA * 1.24 / 1000)
    # bead 1 midpoint (5, 0), weight 1; bead 2 midpoint (10, 5), weight 3
    assert r['centre'][0] == pytest.approx((5 * 1 + 10 * 3) / 4)
    assert r['centre'][1] == pytest.approx((0 * 1 + 5 * 3) / 4)
    assert r['centre'][2] == pytest.approx(0.2)


def test_absolute_e_and_retractions_and_travel():
    g = """M82
G92 E0
G1 Z0.4
G1 X0 Y0
G1 X10 Y0 E2.0
G1 E1.2 ; retract, no bead
G0 X20 Y20 ; travel
G1 E2.0 ; unretract, no bead
G1 X20 Y30 E4.0
"""
    r = G.mass_and_centre(g, density=1.0, diameter=1.75)
    assert r['filament_mm'] == pytest.approx(4.0)
    assert r['centre'][0] == pytest.approx((5 * 2 + 20 * 2) / 4)
    assert r['centre'][1] == pytest.approx((0 * 2 + 25 * 2) / 4)
    assert r['centre'][2] == pytest.approx(0.4)


def test_skips_the_purge_line_before_the_first_layer_marker_when_asked():
    g = """M83
G1 Z0.2
G1 X0 Y-3
G1 X60 Y-3 E5 ; purge
;LAYER_CHANGE
;Z:0.2
G1 X0 Y0
G1 X10 Y0 E1.0
"""
    all_ = G.mass_and_centre(g, density=1.0, diameter=1.75)
    part = G.mass_and_centre(g, density=1.0, diameter=1.75, from_first_layer=True)
    assert all_['filament_mm'] == pytest.approx(6.0)
    assert part['filament_mm'] == pytest.approx(1.0)
    assert part['centre'][1] == pytest.approx(0.0)


def test_an_arc_bead_sits_at_the_arc_centroid():
    # a counter-clockwise quarter circle (G3) of radius 10 about (0, 0), from (10, 0) to (0, 10): the centroid of the
    # curve is r sin(h)/h from the centre along the bisector, h = half the sweep
    g = """M83
G1 Z0.2
G1 X10 Y0
G3 X0 Y10 I-10 J0 E2.0
"""
    r = G.mass_and_centre(g, density=1.0, diameter=1.75)
    d = 10 * math.sin(math.pi / 4) / (math.pi / 4)
    assert r['filament_mm'] == pytest.approx(2.0)
    assert r['centre'][0] == pytest.approx(d * math.cos(math.pi / 4))
    assert r['centre'][1] == pytest.approx(d * math.sin(math.pi / 4))
    assert r['arcs'] == 1


def test_a_clockwise_arc_goes_the_other_way_round():
    # G2 from (10, 0) to (0, 10) about (0, 0) is the long way: three quarters, clockwise, through (0, -10) and (-10, 0)
    g = """M83
G1 Z0.2
G1 X10 Y0
G2 X0 Y10 I-10 J0 E2.0
"""
    r = G.mass_and_centre(g, density=1.0, diameter=1.75)
    h = 3 * math.pi / 4
    d = 10 * math.sin(h) / h
    # bisector of the clockwise sweep from 0 deg to -270 deg is -135 deg
    assert r['centre'][0] == pytest.approx(d * math.cos(-3 * math.pi / 4))
    assert r['centre'][1] == pytest.approx(d * math.sin(-3 * math.pi / 4))
