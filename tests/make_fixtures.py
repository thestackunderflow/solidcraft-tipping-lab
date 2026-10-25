"""Writes the two integration-test shapes: a 20 mm cube and an L (two boxes joined), whose balance points are known by
hand. probe/slice_fixtures.sh slices them at 100% infill; tests/test_gcode_integration.py checks the G-code numbers."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stl_tools import box_tris, write_stl  # noqa: E402

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fixtures')
os.makedirs(D, exist_ok=True)
write_stl(os.path.join(D, 'cube20.stl'), box_tris((0, 0, 0), (20, 20, 20)))
# an L lying flat: a 40 x 10 x 10 bar plus a 10 x 30 x 10 leg at its left end (no overlap): one solid
write_stl(os.path.join(D, 'ell.stl'), np.concatenate([box_tris((0, 0, 0), (40, 10, 10)), box_tris((0, 10, 0), (10, 40, 10))]))
print('ok')
