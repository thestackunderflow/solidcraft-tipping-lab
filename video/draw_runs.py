"""Pictures of two of Claude's designs (python3 video/draw_runs.py): outcome-1 (back_angle 110, slot_floor 8: the slot's
top is partly roofed, the phone block cuts into it, red) and outcome-3 (slot_floor 12: it fits)."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import draw as D
R = os.path.join(D.LAB, 'out', 'runs')
made = [D.side_run(os.path.join(R, 'outcome-1', 'score', 'score-p210', 'cell.json'), 'run-outcome1-roof', 110.0, 8.0),
        D.side_run(os.path.join(R, 'outcome-3', 'score', 'score-p210', 'cell.json'), 'run-outcome3-fits', 110.0, 12.0),
        D.side_run(os.path.join(R, 'outcome-1', 'score', 'score-p210', 'cell.json'), 'run-outcome1-mouth', 110.0, 8.0,
                   w=960, h=720, y0=12.0, z0=14.0, scale=32.0),
        D.side_run(os.path.join(R, 'outcome-3', 'score', 'score-p210', 'cell.json'), 'run-outcome3-mouth', 110.0, 12.0,
                   w=960, h=720, y0=12.0, z0=14.0, scale=32.0),
        {'part1_opening_mm': round(D.opening_at_top(70.0, 8.0), 2)}]
json.dump(made, open(os.path.join(D.OUT, 'runs-drawings.json'), 'w'), indent=1)
print(made)
