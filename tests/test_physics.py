"""The tipping maths (tip/physics.py), proven on cases a hand can check before it touches the stand.

Rule (OpenStax University Physics 1, 12.1): a body on a table stands while the line straight down from its centre of
mass lands inside its support area, and tips once it lands outside. The margin is the signed distance from that point
to the nearest edge of the support area (positive = inside); the tip angle is how far the stand can be leaned over
that edge before it falls: atan(margin / height of the centre of mass)."""
import math
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from tip import physics as P  # noqa: E402


def test_combined_centre_of_mass_is_the_weighted_average():
    # a seesaw: 2 kg at x=0 and 1 kg at x=3 balance at x=1
    m, c = P.combine([(2.0, (0, 0, 0)), (1.0, (3, 0, 0))])
    assert m == 3.0
    assert np.allclose(c, (1, 0, 0))


def test_margin_inside_a_rectangle_is_the_distance_to_the_nearest_edge():
    rect = [(0, 0), (10, 0), (10, 4), (0, 4)]
    assert P.margin((5, 1), rect) == pytest.approx(1.0)
    assert P.margin((9.5, 2), rect) == pytest.approx(0.5)


def test_margin_outside_is_negative():
    rect = [(0, 0), (10, 0), (10, 4), (0, 4)]
    assert P.margin((5, -2), rect) == pytest.approx(-2.0)
    assert P.margin((12, 2), rect) == pytest.approx(-2.0)


def test_margin_toward_one_edge_only():
    rect = [(0, 0), (10, 0), (10, 4), (0, 4)]
    # the y = 0 edge only (the stand's front edge), even when another edge is nearer
    assert P.edge_margin((9.5, 2), rect, edge=((0, 0), (10, 0))) == pytest.approx(2.0)


def test_tip_angle():
    assert P.tip_angle_deg(1.0, 1.0) == pytest.approx(45.0)
    assert P.tip_angle_deg(-1.0, 1.0) == pytest.approx(-45.0)
    assert P.tip_angle_deg(0.0, 50.0) == pytest.approx(0.0)


def test_support_polygon_is_the_hull_of_the_points_touching_the_table():
    # a box from z=0 with a rounded front-bottom edge: only the points at z=0 touch the table
    pts = np.array([[0, 3, 0], [10, 3, 0], [10, 8, 0], [0, 8, 0], [0, 0, 3], [10, 0, 3], [5, 5, 0]], dtype=float)
    hull = P.support_polygon(pts, tol=1e-6)
    xs = sorted({round(x, 6) for x, _ in hull})
    ys = sorted({round(y, 6) for _, y in hull})
    assert xs == [0.0, 10.0] and ys == [3.0, 8.0]
    assert len(hull) == 4


def test_phone_pose_in_the_slot_puts_its_middle_up_the_slot_axis():
    # floor centre at (y=0, z=0), axis 90 deg (straight up): a 150 mm phone's middle is 75 mm up
    c = P.phone_centre(floor_centre=(0.0, 0.0), axis_deg=90.0, length=150.0, x=0.0)
    assert np.allclose(c, (0, 0, 75))
    # 70 deg from horizontal, leaning toward -y
    c = P.phone_centre(floor_centre=(10.0, 5.0), axis_deg=70.0, length=150.0, x=1.0, toward=-1)
    assert c[0] == 1.0
    assert c[1] == pytest.approx(10 - 75 * math.cos(math.radians(70)))
    assert c[2] == pytest.approx(5 + 75 * math.sin(math.radians(70)))
