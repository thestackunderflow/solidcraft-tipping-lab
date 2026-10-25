# SolidCraft tipping lab: will the part 1 phone stand tip over?

The lab behind "SolidCraft + Claude: Will This Phone Stand Tip? Center of Mass" (SolidCraft for Beginners #7, The Stack
Underflow). A viewer asked about the phone stand from part 1: put a phone in that slot, won't it tip over? And could
Claude figure it out? The lab puts a phone-sized block in the stand's slot in SolidCraft, weighs the stand both as the
design file sees it (solid plastic) and as a slicer would print it, and works out where the shared balance point lands.
Everything runs in Docker on SolidCraft 0.22.0. Tested 25 Oct 2026. Nothing was printed: every print weight and time is
the slicer's estimate.

## The idea in one line
Think of a seesaw. The stand sits on one side of its back edge, the phone hangs out on the other. The stand wins only if
its weight times its distance beats the phone's. Slicing a part (walls plus a thin infill) makes it much lighter than
the solid design file, so the same stand can stand on screen and tip in real life.

## What it found
The phone is a 150 x 72 x 9 mm block of 210 g unless a row says otherwise.
- **The stand, three ways** (weight and balance point y, mm): SolidCraft, solid PLA 1.24 g/cm³: 155.8 g at 31.94; the
  lab's own STL maths: 155.8 g at 31.94; the slicer at 100% infill: 156.0 g at 31.93. Sliced with PrusaSlicer 2.9.2's
  stock "0.20mm SPEED @MK4S 0.4" preset (2 walls, 15% grid, Prusament PLA): **42.7 g at 30.04, about a quarter.**
- **Solid, it stands; sliced, it tips.** With the solid stand the shared balance point is 5.7 mm inside the back edge.
  Sliced: (42.7 x 30.0 + 210 x -8.5) / 252.7 = -2.0, and the tipping edge is at y = 3.0, so it is 5.0 mm past the edge.
  Every phone we tried, 165 to 250 g, tips as sliced (the best case is still 0.42 mm past).
- **More plastic barely helps.** 3 walls: 47.0 g, 4.6 mm past. 20% infill: 48.9 g, 4.2 past. 3 walls + 20% gyroid:
  52.3 g, 3.9 past. 50% infill: 88.7 g (1 h 54 min) just stands (0.3 mm to spare). 100%: 156.0 g, 3 h 14 min, 5.7 mm.
- **SolidCraft has two balance-point tools.** `inspect.center_of_mass` treats every body as the same weight (y 14.3 for
  stand plus phone); `component.properties` reads the materials (y 8.7). 5.6 mm apart: ask the right one.
- **The fix: one named size from part 1**, `front_lip` 15 to 40 mm (more base in front of the slot). Sliced, the 210 g
  phone now has 15.8 mm to spare, at least 5.1 mm in the worst case we tried (phones 165 to 250 g, with and without a
  case), using the same 42.6 g of plastic. At 35 mm the worst case is only 0.85 mm.
- **Claude Code** (claude-sonnet-5-5, Claude Code 2.1.310), 6 fresh tries, $0.79 at API prices. 3 tries got the viewer's
  own words ("center the phone's center of mass over the middle of the base"), 3 got only "make sure it doesn't tip when
  printed with the 0.20mm SPEED preset". All 6 flipped the slot's lean (`back_angle` 70 to 110 degrees). None put a phone
  into SolidCraft or weighed the sliced print (one guessed "roughly 30 g"). We re-opened and re-sliced every design: all
  6 stand with a 210 g phone, but 2 of the 3 "make sure it doesn't tip" designs leave the slot's mouth 4.4 mm wide for
  a 9 mm phone, so the phone does not fit. Passes: 4 of 6 (the viewer's words 3 of 3, with a longer base,
  55 to 62 g sliced; "make sure" 1 of 3).
- These are static numbers: a phone sitting still. Tapping the screen pushes it toward the edge it tips over.

Where each number lives: `out/probe/0.22.0/numbers.json` (every cell: weights, balance points, margins),
`out/probe/analyse-0.22.0.txt` (the margin table), `out/probe/0.22.0/strip-p210.json` (the infill rows),
`out/runs/SCORES.json` and `out/runs/BEHAVIOUR.json` (Claude's 6 runs, re-scored), `video/frames/runs-drawings.json`
(the 4.36 mm slot opening).

## Run the lab
You need Docker. Nothing is installed on your computer.
```
docker build -t solidcraft-tipping-lab:0.22.0 .
docker run --rm -v "$PWD:/work" -w /work solidcraft-tipping-lab:0.22.0 python3 -m pytest -q tests/
docker run --rm -v "$PWD:/work" -v "$PWD/out/probe/0.22.0:/lab/out" -w /work solidcraft-tipping-lab:0.22.0 python3 probe/probe.py lip15-p210 lip40-p210
docker run --rm -v "$PWD:/work" -w /work solidcraft-tipping-lab:0.22.0 python3 probe/analyse.py out/probe/0.22.0
```
The build downloads the SolidCraft 0.22.0 Linux release and checks it against the release's SHA256SUMS.txt. The tests
run offline (the G-code tests use small sliced fixtures in `tests/fixtures/`). The probe needs no AI and no money.

Slicing (`slicer/slice.sh`, `probe/slice_cells.sh`) runs PrusaSlicer 2.9.2 in a separate container image that is not
part of this repo (the scripts call it `habs-slicer:0.2`; any image with `prusa-slicer` 2.9.2 and its bundled profiles at
`/usr/share/PrusaSlicer/profiles` works). The sliced G-code we used is already in `out/`, so `analyse.py` works without it.

To run Claude yourself: `bash claude-run/run.sh viewer|outcome RUN_ID`, then `bash claude-run/score_all.sh` (needs
Claude Code and an API key; each run is capped at $1.50 and a shared budget file is checked first; see the top of
`run.sh`).

## Layout
- `data/part1-stand.solidcraft` (and `.stl`): part 1's phone stand, the starting design.
- `tip/physics.py`: the seesaw sum, the support area, the margin to the tipping edge, the tip angle, and where the phone
  settles in the slot. `tip/gcode_mass.py`: the print's weight and balance point from the G-code (arcs included).
  `tip/model.py`: the margin table.
- `probe/`: the no-AI probe (`probe.py`: one cell = a design, named sizes, a phone), `slice_cells.sh`, `strip.py` (the
  infill rows), `analyse.py` (the table), `explore.py` (the two balance-point tools).
- `slicer/`: `slice.sh` and `resolve_preset.py` (the stock presets read from the vendor bundle), `slice_report.py`.
- `claude-run/`: `run.sh` (one sealed run), `score.py` and `score_all.sh` (re-open, re-slice, score), `budget.py`.
- `proxy/mcp_log_proxy.py`: logs every request and reply between Claude Code and SolidCraft to `transcript.jsonl`.
- `out/probe/0.22.0/lipL-pG[-case|-caseoff]/`: one folder per probe cell (front lip L mm, phone G grams), with the
  design, STLs, G-code and the MCP log. `out/runs/`: Claude's 6 runs. `out/*.log`: red (failing first) and green tests.
- `tests/`: the tests. `video/`: the drawings and cards used in the video, made from the lab's numbers.

## Licence
Apache-2.0 (`LICENSE`). Not affiliated with SolidCraft, Prusa Research or Anthropic. Narration of the video:
AI-generated voice.
