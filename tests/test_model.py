"""tip/model.py: the margin table for a stand + phone, from measured inputs (the stand's mass and balance point, the
phone's pose and mass, the stand's footprint and its tipping edge). Hand-checkable cases."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from tip import model as M  # noqa: E402

RECT = [(0, 3), (80, 3), (80, 57), (0, 57)]   # footprint, the tipping edge along y = 3
EDGE = ((0, 3), (80, 3))


def test_margin_row_is_the_seesaw_sum_against_the_edge():
    # stand 100 g at y=30, phone 100 g at y=-10: combined y=10, 7 mm inside y=3
    row = M.margin_row(stand_g=100, stand_com=(40, 30, 10), phone_g=100, phone_com=(40, -10, 70),
                       footprint=RECT, edge=EDGE)
    assert row['combined_g'] == 200
    assert row['combined_com'][1] == pytest.approx(10.0)
    assert row['margin_mm'] == pytest.approx(7.0)
    assert row['stands'] is True
    assert row['tip_deg'] == pytest.approx(M.P.tip_angle_deg(7.0, 40.0))


def test_a_lighter_stand_lets_the_phone_pull_the_balance_point_past_the_edge():
    heavy = M.margin_row(156, (40, 31.9, 14), 190, (40, -8.5, 79), RECT, EDGE)
    light = M.margin_row(43, (40, 30.0, 15), 190, (40, -8.5, 79), RECT, EDGE)
    assert heavy['stands'] and not light['stands']
    assert light['margin_mm'] < 0 < heavy['margin_mm']


def test_band_spans_every_combination_and_reports_min_and_max():
    stands = {'solid': (156, (40, 31.9, 14)), 'sliced': (43, (40, 30.0, 15))}
    phones = {'flush': (40, -6.4, 80), 'settled': (40, -8.5, 79)}
    band = M.band(stands, {190: phones}, RECT, EDGE, along=(0.0, -0.38, 0.92), shift_mm=5.0)
    b = band[190]
    # 2 stands x 2 poses x 3 shifts (-5, 0, +5) = 12 rows
    assert len(b['rows']) == 12
    assert b['min_mm'] <= b['max_mm']
    assert {r['stand'] for r in b['rows']} == {'solid', 'sliced'}
    by = M.summary_by_stand(b)
    assert by['solid']['min_mm'] > 0 > by['sliced']['max_mm']


def test_hook_variant_from_the_band():
    assert M.hook_variant(sliced_min=-5.0, sliced_max=-2.0, solid_min=4.0) == 'A'
    assert M.hook_variant(sliced_min=-1.0, sliced_max=1.5, solid_min=4.0) == 'B'
    assert M.hook_variant(sliced_min=0.5, sliced_max=3.0, solid_min=8.0) == 'C'
