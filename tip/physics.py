"""Tipping maths for a stand on a table (static only: no tap, no cable pull).

A body stands while the line straight down from its centre of mass lands inside its support area (the convex hull of
the points touching the table), and tips once it lands outside (OpenStax University Physics 1, 12.1). Distances in mm,
masses in g, angles in degrees; y is front-to-back, z is up."""
import math

import numpy as np


def combine(parts):
    """[(mass, (x, y, z)), ...] -> (total mass, combined centre of mass): the seesaw sum."""
    m = sum(float(p[0]) for p in parts)
    c = sum(float(p[0]) * np.asarray(p[1], dtype=float) for p in parts) / m
    return m, c


def _hull(points):
    """Andrew's monotone chain, counter-clockwise, no repeated last point."""
    pts = sorted({(round(float(x), 9), round(float(y), 9)) for x, y in points})
    if len(pts) < 3:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def support_polygon(points, tol=1e-4):
    """The (x, y) hull of the points at the lowest z (within tol): what touches the table."""
    p = np.asarray(points, dtype=float).reshape(-1, 3)
    z0 = p[:, 2].min()
    return _hull(p[np.abs(p[:, 2] - z0) <= tol][:, :2])


def _signed_edge_distance(pt, a, b, inside_sign):
    (ax, ay), (bx, by), (px, py) = a, b, pt
    ex, ey = bx - ax, by - ay
    n = math.hypot(ex, ey)
    return inside_sign * ((ex * (py - ay) - ey * (px - ax)) / n)


def margin(pt, polygon):
    """Signed distance from pt to the polygon's nearest edge: + inside, - outside (convex polygon)."""
    poly = _hull(polygon)
    d = [_signed_edge_distance(pt, poly[i], poly[(i + 1) % len(poly)], 1.0) for i in range(len(poly))]
    inside = all(x >= -1e-12 for x in d)
    if inside:
        return min(d)
    # outside: the distance to the polygon (as a negative number)
    best = math.inf
    for i in range(len(poly)):
        (ax, ay), (bx, by) = poly[i], poly[(i + 1) % len(poly)]
        ex, ey = bx - ax, by - ay
        t = max(0.0, min(1.0, ((pt[0] - ax) * ex + (pt[1] - ay) * ey) / (ex * ex + ey * ey)))
        best = min(best, math.hypot(pt[0] - (ax + t * ex), pt[1] - (ay + t * ey)))
    return -best


def edge_margin(pt, polygon, edge):
    """Signed distance from pt to one named edge's line, + on the polygon's side of it (the stand's front edge)."""
    poly = _hull(polygon)
    cx = sum(p[0] for p in poly) / len(poly)
    cy = sum(p[1] for p in poly) / len(poly)
    a, b = edge
    s = 1.0 if _signed_edge_distance((cx, cy), a, b, 1.0) >= 0 else -1.0
    return _signed_edge_distance(pt, a, b, s)


def tip_angle_deg(margin_mm, height_mm):
    """How far the stand can be leaned over the edge before it falls: atan(margin / height of the centre of mass)."""
    return math.degrees(math.atan2(margin_mm, height_mm))


def phone_centre(floor_centre, axis_deg, length, x, toward=1):
    """The middle of a phone standing on the slot floor along the slot axis: floor_centre is (y, z) of the floor's
    middle, axis_deg the axis angle from the table, toward = -1 when the slot leans toward -y."""
    y0, z0 = floor_centre
    a = math.radians(axis_deg)
    return np.array([float(x), y0 + toward * (length / 2) * math.cos(a), z0 + (length / 2) * math.sin(a)])


def _unit(v):
    v = np.asarray(v, dtype=float)
    return v / np.linalg.norm(v)


def slot_pose(front_floor, back_floor, front_top, thickness, length, lean='settled', max_tilt_deg=15.0, step_deg=0.01,
              force_tilt=False):
    """The phone standing in a slot, in the slot's (y, z) section.

    The slot: a floor from front_floor to back_floor, walls perpendicular to it, front_top = the front wall's top edge.
    The phone (thickness x length) stands on the floor and leans on front_top with its front face. In the slot's own
    frame (X across from the front wall to the back wall, Y up the slot axis) it may tilt forward by theta into the
    slot's play. For each theta it sits as low as the floor and the walls allow (sliding down its contact).
    lean='flush': theta = 0, flat against the front wall. lean='settled': the theta with the lowest middle, which is
    where gravity takes a phone with no friction at its foot (static, no tap). Returns the axis angle from the table,
    the tilt, the phone's middle and its bottom corners in world (y, z). force_tilt=True returns the pose at
    max_tilt_deg (or the last one that fits): for tests and the worst-case band."""
    F, C, E = (np.asarray(p, dtype=float) for p in (front_floor, back_floor, front_top))
    ux = _unit(C - F)                       # across the slot, front -> back
    uy = np.array([-ux[1], ux[0]])          # up the slot axis
    if np.dot(uy, E - F) < 0:
        uy = -uy
    W = float(np.linalg.norm(C - F))
    H = float(np.dot(E - F, uy))
    t, L = float(thickness), float(length)

    def local(theta):
        st, ct = math.sin(theta), math.cos(theta)
        d = np.array([-st, ct])             # up the phone (top toward the front wall)
        nf = np.array([-ct, -st])           # out of its front face
        kf = float(np.dot(nf, [0.0, H]))    # the front face passes the top edge
        kb = kf - t
        lo, hi = -math.inf, math.inf
        for k in (kf, kb):
            # corner = s d + k nf ; Y >= 0 (floor) ; 0 <= X <= W (walls)
            cy, ky = d[1], k * nf[1]
            lo = max(lo, -ky / cy)
            cx, kx = d[0], k * nf[0]
            if abs(cx) < 1e-15:
                if not (-1e-9 <= kx <= W + 1e-9):
                    return None
            else:
                a1, a2 = (0.0 - kx) / cx, (W - kx) / cx   # X >= 0 and X <= W
                lo_x, hi_x = (a2, a1) if cx < 0 else (a1, a2)
                lo, hi = max(lo, lo_x), min(hi, hi_x)
        if lo > hi + 1e-9:
            return None
        s = lo
        centre = (s + L / 2) * d + (kf - t / 2) * nf
        corners = [s * d + kf * nf, s * d + kb * nf]
        return theta, centre, corners

    def world(res):
        theta, c, corners = res
        to_w = lambda q: F + q[0] * ux + q[1] * uy
        axis = to_w(np.array([-math.sin(theta), math.cos(theta)])) - F
        return {'tilt_deg': math.degrees(theta),
                'axis_deg': math.degrees(math.atan2(axis[1], abs(axis[0]))) if abs(axis[0]) > 1e-12 else 90.0,
                'centre_yz': [float(v) for v in to_w(c)],
                'bottom_corners_yz': [[float(v) for v in to_w(q)] for q in corners]}

    flush = local(0.0)
    if lean == 'flush':
        return world(flush)
    best = flush
    th = 0.0
    while th < math.radians(max_tilt_deg):
        th += math.radians(step_deg)
        r = local(th)
        if r is None:
            break
        if force_tilt:
            best = r
            continue
        if (F + r[1][0] * ux + r[1][1] * uy)[1] < (F + best[1][0] * ux + best[1][1] * uy)[1]:
            best = r
    return world(best)
