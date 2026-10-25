"""Our drawings for the video, from lab numbers only (no AI, no repainting); words go on later (video/make_cards.sh).

    docker run --rm -v <lab>:/work -w /work solidcraft-tipping-lab:0.22.0 python3 video/draw.py

Side views are seen from the user's seat's left (the user sits on the +y side, the long end of the base; the phone
leans away, toward -y), drawn to scale from part 1's slot sketch and the probe cells (out/probe/0.22.0/numbers.json):
  side-<cell>-<stand>.png   the stand's middle section (grey), the phone block (dark), the stand's dot, the phone's dot,
                            the shared dot, a line straight down, the footprint bar and the tipping edge
  phone-alone.png           the phone in the slot with only its own dot: the line lands past the edge
  honeycomb.png             one real layer of the sliced stand (G-code, z = 15 mm): walls dark, infill light
  ruler-*.png               the ruler on a finger, with and without the coin
Every PNG is written by a tiny zlib PNG writer (numpy only)."""
import json
import math
import os
import struct
import sys
import zlib

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.join(HERE, '..')
sys.path.insert(0, LAB)
OUT = os.path.join(HERE, 'frames')
NUM = json.load(open(os.path.join(LAB, 'out', 'probe', '0.22.0', 'numbers.json'), encoding='utf-8'))

BG = (236, 239, 244)
STAND = (176, 186, 200)
STAND_EDGE = (100, 116, 139)
PHONE = (71, 85, 105)
TABLE = (148, 163, 184)
INK = (31, 41, 55)
RED = (183, 28, 28)
GREEN = (27, 94, 32)
BLUE = (29, 78, 216)
AMBER = (180, 83, 9)
WALL = (51, 65, 85)
INFILL = (203, 213, 225)


def png(path, img):
    h, w, _ = img.shape
    raw = b''.join(b'\x00' + img[y].astype(np.uint8).tobytes() for y in range(h))

    def chunk(t, d):
        c = struct.pack('>I', len(d)) + t + d
        return c + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    with open(path, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)) +
                chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))


class Canvas:
    """World (y, z) in mm -> pixels; y grows to the right, z up."""

    def __init__(self, w, h, y0, z0, scale):
        self.img = np.zeros((h, w, 3), dtype=np.uint8)
        self.img[:] = BG
        self.w, self.h, self.y0, self.z0, self.s = w, h, y0, z0, scale
        yy, zz = np.meshgrid(np.arange(w), np.arange(h))
        self.Y = self.y0 + (yy + 0.5) / self.s
        self.Z = self.z0 + (h - zz - 0.5) / self.s

    def px(self, y, z):
        return (y - self.y0) * self.s, self.h - (z - self.z0) * self.s

    def fill_mask(self, mask, col):
        self.img[mask] = col

    def poly_mask(self, pts):
        pts = np.asarray(pts, dtype=float)
        inside = np.zeros(self.Y.shape, dtype=bool)
        n = len(pts)
        for i in range(n):
            (ya, za), (yb, zb) = pts[i], pts[(i + 1) % n]
            cond = ((za > self.Z) != (zb > self.Z))
            with np.errstate(divide='ignore', invalid='ignore'):
                ycross = ya + (self.Z - za) * (yb - ya) / (zb - za)
            inside ^= cond & (self.Y < ycross)
        return inside

    def line(self, a, b, col, width_mm):
        (ya, za), (yb, zb) = a, b
        dy, dz = yb - ya, zb - za
        L2 = dy * dy + dz * dz
        t = np.clip(((self.Y - ya) * dy + (self.Z - za) * dz) / L2, 0, 1) if L2 > 0 else 0
        d = np.hypot(self.Y - (ya + t * dy), self.Z - (za + t * dz))
        self.img[d <= width_mm / 2] = col

    def dashed(self, a, b, col, width_mm, dash=3.0):
        (ya, za), (yb, zb) = a, b
        L = math.hypot(yb - ya, zb - za)
        n = int(L // (2 * dash)) + 1
        for i in range(n):
            t0, t1 = (2 * i * dash) / L, min(1.0, (2 * i + 1) * dash / L)
            if t0 >= 1:
                break
            self.line((ya + t0 * (yb - ya), za + t0 * (zb - za)), (ya + t1 * (yb - ya), za + t1 * (zb - za)), col, width_mm)

    def dot(self, c, r_mm, col, ring=None):
        d = np.hypot(self.Y - c[0], self.Z - c[1])
        if ring:
            self.img[d <= r_mm + ring[1]] = ring[0]
        self.img[d <= r_mm] = col


def stand_profile(front_lip=15.0, angle=70.0, slot_w=10.0, floor=8.0, depth=60.0, height=30.0, r=3.0, slot_len=25.0):
    """The stand's middle section, from part 1's named sizes (sketch SlotProfile): a 60 x 30 rectangle with 3 mm
    rounds, minus the slot: floor from (front_lip, floor) along the floor direction slot_w, walls 25 mm up the axis."""
    a = math.radians(angle)
    ax = np.array([-math.cos(a), math.sin(a)])       # up the slot (leans toward -y, the short end)
    fl = np.array([math.sin(a), math.cos(a)])        # along the floor, front -> back
    F = np.array([front_lip, floor])
    C = F + slot_w * fl
    return F, C, [F, C, C + slot_len * ax, F + slot_len * ax]


def stand_mask(cv, front_lip=15.0, angle=70.0, floor=8.0):
    F, C, slot = stand_profile(front_lip, angle, 10.0, floor)
    Y, Z = cv.Y, cv.Z
    r = 3.0
    box = (Y >= 0) & (Y <= 60) & (Z >= 0) & (Z <= 30)
    for cy, cz in ((r, r), (60 - r, r), (r, 30 - r), (60 - r, 30 - r)):
        corner = (np.abs(Y - cy) > 0) & (((Y < r) if cy == r else (Y > 60 - r)) & ((Z < r) if cz == r else (Z > 30 - r)))
        box &= ~(corner & (np.hypot(Y - cy, Z - cz) > r))
    return box & ~cv.poly_mask(slot)


def phone_rect(cell):
    n = NUM[cell]
    L, W, T = n['phone_block_mm']
    a = math.radians(n['axis_deg'])
    d = np.array([-math.cos(a), math.sin(a)])
    nf = np.array([-math.sin(a), -math.cos(a)])
    c = np.array(n['phone_pose_settled'][1:])
    hl, ht = L / 2, T / 2
    return [c - hl * d - ht * nf, c - hl * d + ht * nf, c + hl * d + ht * nf, c + hl * d - ht * nf]


def side(cell, stand, name, front_lip=15.0, phone=True, dots=('stand', 'phone', 'shared'), w=900, h=1300, bracket=False):
    n = NUM[cell]
    cv = Canvas(w, h, -40.0, -8.0, 7.5)
    cv.fill_mask(cv.Z < 0, (226, 232, 240))
    cv.line((-40, 0), (80, 0), TABLE, 0.6)
    cv.fill_mask(stand_mask(cv, front_lip), STAND)
    if phone:
        cv.fill_mask(cv.poly_mask(phone_rect(cell)), PHONE)
    edge_y = n['tipping_edge'][0][1]
    far_y = max(y for _, y in n['footprint'])
    cv.line((edge_y, -1.6), (far_y, -1.6), BLUE, 1.6)                 # the footprint, under the table line
    cv.line((edge_y, -4.5), (edge_y, 1.0), BLUE, 0.6)                 # the tipping edge mark
    s = n['stand_sliced'] if stand == 'sliced' else n['stand_solid_solidcraft']
    sc = s['com']
    pc = n['phone_pose_settled']
    g = n['central'][stand]['combined_com']
    if 'standline' in dots:
        cv.dashed((sc[1], sc[2]), (sc[1], 0.0), GREEN, 0.7)
    if bracket:
        cv.line((edge_y, -5.0), (front_lip, -5.0), AMBER, 1.0)
        cv.line((edge_y, -6.5), (edge_y, -3.5), AMBER, 0.8)
        cv.line((front_lip, -6.5), (front_lip, -3.5), AMBER, 0.8)
    if 'stand' in dots or 'standline' in dots:
        cv.dot((sc[1], sc[2]), 1.6, AMBER, ring=((255, 255, 255), 0.5))
    if 'phone' in dots:
        cv.dot((pc[1], pc[2]), 1.6, (255, 255, 255), ring=(INK, 0.5))
        if 'shared' not in dots:
            cv.dashed((pc[1], pc[2]), (pc[1], 0.0), RED, 0.6)
    if 'shared' in dots:
        ok = n['central'][stand]['margin_mm'] > 0
        col = GREEN if ok else RED
        cv.dashed((g[1], g[2]), (g[1], 0.0), col, 0.7)
        cv.dot((g[1], g[2]), 2.4, col, ring=((255, 255, 255), 0.6))
        cv.dot((g[1], 0.0), 1.0, col)
    os.makedirs(OUT, exist_ok=True)
    png(os.path.join(OUT, name + '.png'), cv.img)
    return {'name': name, 'cell': cell, 'stand': stand, 'margin_mm': n['central'][stand]['margin_mm'],
            'edge_y': edge_y, 'shared_yz': [g[1], g[2]], 'phone_yz': [pc[1], pc[2]], 'scale_px_per_mm': cv.s,
            'origin_mm': [cv.y0, cv.z0], 'size_px': [w, h]}


def honeycomb(gcode, z=15.0, name='honeycomb', w=1200, h=900):
    """One layer of the real G-code, seen from above: walls (perimeters) dark, infill light."""
    import re
    lines = open(gcode, encoding='utf-8', errors='replace').read().splitlines()
    zc, typ, x, y, segs = None, '', 0.0, 0.0, []
    for L in lines:
        if L.startswith(';Z:'):
            zc = float(L[3:])
        if L.startswith(';TYPE:'):
            typ = L[6:]
        m = re.match(r'G[0123] ', L)
        if not m:
            continue
        wd = dict((k, float(v)) for k, v in re.findall(r'([XYEIJ])([-+]?\d*\.?\d+)', L))
        nx, ny = wd.get('X', x), wd.get('Y', y)
        if zc is not None and abs(zc - z) < 0.05 and wd.get('E', 0) > 0 and (nx, ny) != (x, y):
            segs.append((typ, x, y, nx, ny))
        x, y = nx, ny
    xs = [s[1] for s in segs] + [s[3] for s in segs]
    ys = [s[2] for s in segs] + [s[4] for s in segs]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    sc = min(w / (max(xs) - min(xs) + 8), h / (max(ys) - min(ys) + 8))
    cv = Canvas(w, h, -w / 2 / sc, -h / 2 / sc, sc)
    cv.img[:] = (255, 255, 255)
    for t, x0, y0, x1, y1 in segs:
        col = WALL if 'perimeter' in t.lower() else INFILL
        if col == INFILL:
            cv.line((x0 - cx, y0 - cy), (x1 - cx, y1 - cy), col, 0.45)
    for t, x0, y0, x1, y1 in segs:
        if 'perimeter' in t.lower():
            cv.line((x0 - cx, y0 - cy), (x1 - cx, y1 - cy), WALL, 0.45)
    png(os.path.join(OUT, name + '.png'), cv.img)
    return {'name': name, 'z': z, 'segments': len(segs)}


def ruler(name, coin=None, w=1200, h=600):
    cv = Canvas(w, h, -160.0, -60.0, 4.0)
    L = 300.0
    bal = 0.0 if coin is None else (coin * 10.0) / (30.0 + 10.0)      # ruler 30 g at 0, coin 10 g at `coin`
    cv.fill_mask(cv.poly_mask([(-L / 2, 0), (L / 2, 0), (L / 2, 8), (-L / 2, 8)]), (250, 204, 21))
    for i in range(-15, 16):
        cv.line((i * 10.0, 8), (i * 10.0, 4.5 if i % 5 else 2.5), INK, 0.6)
    if coin is not None:
        cv.fill_mask(cv.poly_mask([(coin - 12, 8), (coin + 12, 8), (coin + 12, 12), (coin - 12, 12)]), (148, 163, 184))
    cv.fill_mask(cv.poly_mask([(bal - 6, -55), (bal + 6, -55), (bal + 5, -2), (bal - 5, -2)]), (234, 179, 8) if False else (253, 186, 116))
    cv.dot((bal, 4.0), 3.0, RED, ring=((255, 255, 255), 0.8))
    png(os.path.join(OUT, name + '.png'), cv.img)
    return {'name': name, 'balance_mm': bal}


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    made = [
        side('lip15-p210', 'solid', 'side-p210-solid'),
        side('lip15-p210', 'sliced', 'side-p210-sliced'),
        side('lip15-p210', 'sliced', 'phone-alone', dots=('phone',)),
        side('lip15-p210', 'solid', 'stand-and-phone-dots', dots=('stand', 'phone')),
        side('lip40-p210', 'sliced', 'side-fix-p210-sliced', front_lip=40.0) if 'lip40-p210' in NUM else
        side('lip40-p250', 'sliced', 'side-fix-p250-sliced', front_lip=40.0),
        honeycomb(os.path.join(LAB, 'out', 'probe', '0.22.0', 'lip15-p210', 'slice-speed.gcode')),
        ruler('ruler-plain'), ruler('ruler-coin', coin=120.0),
        side('lip15-p210', 'solid', 'stand-only', phone=False, dots=('standline',)),
        side('lip15-p210', 'sliced', 'fix-before', dots=('phone', 'shared'), bracket=True),
        side('lip40-p210', 'sliced', 'fix-after', front_lip=40.0, dots=('phone', 'shared'), bracket=True),
    ]
    json.dump(made, open(os.path.join(OUT, 'drawings.json'), 'w', encoding='utf-8'), indent=1)
    for m in made:
        print(m)


def opening_at_top(angle, floor, front_lip=15.0, slot_w=10.0, slot_len=25.0, top=30.0):
    """The slot's opening on the top face, measured across the slot (perpendicular to its axis), for part 1's sketch
    with back_angle `angle`: the slot polygon clipped at z = top. Returns mm (0 if the slot doesn't reach the top)."""
    F, C, slot = stand_profile(front_lip, angle, slot_w, floor, slot_len=slot_len)
    pts = []
    n = len(slot)
    for i in range(n):
        a, b = slot[i], slot[(i + 1) % n]
        if (a[1] - top) * (b[1] - top) < 0:
            t = (top - a[1]) / (b[1] - a[1])
            pts.append(a + t * (b - a))
    if len(pts) < 2:
        return 0.0
    ys = sorted(p[0] for p in pts)
    return (ys[-1] - ys[0]) * math.sin(math.radians(angle))


def side_run(cell_json, name, angle, floor, w=900, h=1300, y0=-10.0, z0=-8.0, scale=7.5, shared=None, shared_ok=True):
    """A run's design (part 1 slot with the run's back_angle / slot_floor), the 210 g block at our settled pose, and
    where the block would cut into the stand in red: the phone doesn't fit."""
    c = json.load(open(cell_json, encoding='utf-8'))
    p = c['poses']['settled']
    L, W, T = c['phone_block_mm']
    a = math.radians(p['axis_deg'])
    sgn = 1.0 if p['centre_yz'][0] > c['slot']['front_floor'][0] else -1.0
    d = np.array([sgn * math.cos(a), math.sin(a)])
    nf = np.array([-d[1], d[0]])
    cc = np.array(p['centre_yz'])
    rect = [cc - L / 2 * d - T / 2 * nf, cc - L / 2 * d + T / 2 * nf, cc + L / 2 * d + T / 2 * nf, cc + L / 2 * d - T / 2 * nf]
    cv = Canvas(w, h, y0, z0, scale)
    cv.fill_mask(cv.Z < 0, (226, 232, 240))
    F, C, slot = stand_profile(15.0, angle, 10.0, floor)
    Y, Z = cv.Y, cv.Z
    box = (Y >= 0) & (Y <= 60) & (Z >= 0) & (Z <= 30)
    st = stand_mask(cv, 15.0, angle, floor)
    ph = cv.poly_mask(rect)
    cv.fill_mask(st, STAND)
    cv.fill_mask(ph & ~st, PHONE)
    cv.fill_mask(ph & st, RED)
    if shared is not None:
        col = GREEN if shared_ok else RED
        cv.line((3.0, -1.6), (57.0, -1.6), BLUE, 1.6)
        cv.dashed((shared[0], shared[1]), (shared[0], 0.0), col, 0.7)
        cv.dot((shared[0], shared[1]), 2.4, col, ring=((255, 255, 255), 0.6))
        cv.dot((cc[0], cc[1]), 1.6, (255, 255, 255), ring=(INK, 0.5))
    png(os.path.join(OUT, name + '.png'), cv.img)
    return {'name': name, 'opening_mm': round(opening_at_top(angle, floor), 2), 'overlap_px': int((ph & st).sum())}
