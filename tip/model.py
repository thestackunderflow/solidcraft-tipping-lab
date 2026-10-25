"""The margin table: for a stand (mass + balance point) and a phone (mass + balance point in a given pose), where the
combined balance point lands against the stand's tipping edge. Every input comes from a lab measurement; nothing here
is estimated. Distances mm, masses g."""
import numpy as np

from tip import physics as P


def margin_row(stand_g, stand_com, phone_g, phone_com, footprint, edge):
    m, c = P.combine([(stand_g, stand_com), (phone_g, phone_com)])
    margin = P.edge_margin((c[0], c[1]), footprint, edge)
    return {'combined_g': float(m), 'combined_com': [float(v) for v in c], 'margin_mm': float(margin),
            'stands': bool(margin > 0), 'tip_deg': float(P.tip_angle_deg(margin, c[2]))}


def band(stands, phones_by_mass, footprint, edge, along, shift_mm=5.0):
    """stands: {name: (g, com)}; phones_by_mass: {g: {pose: com}}; along: the phone's axis (unit, world) for the
    'its balance point isn't at its middle' shift of -shift, 0, +shift mm. -> {g: {'rows', 'min_mm', 'max_mm'}}"""
    a = np.asarray(along, dtype=float)
    a = a / np.linalg.norm(a)
    out = {}
    for g, poses in phones_by_mass.items():
        rows = []
        for sname, (sg, scom) in stands.items():
            for pname, pcom in poses.items():
                for s in (-shift_mm, 0.0, shift_mm):
                    r = margin_row(sg, scom, g, np.asarray(pcom, dtype=float) + s * a, footprint, edge)
                    r.update({'stand': sname, 'pose': pname, 'phone_shift_mm': s})
                    rows.append(r)
        out[g] = {'rows': rows, 'min_mm': min(r['margin_mm'] for r in rows),
                  'max_mm': max(r['margin_mm'] for r in rows)}
    return out


def summary_by_stand(b):
    res = {}
    for r in b['rows']:
        d = res.setdefault(r['stand'], {'min_mm': float('inf'), 'max_mm': float('-inf')})
        d['min_mm'] = min(d['min_mm'], r['margin_mm'])
        d['max_mm'] = max(d['max_mm'], r['margin_mm'])
    return res


def hook_variant(sliced_min, sliced_max, solid_min):
    """PLAN rev 2 H4: A = the whole sliced band tips; B = it straddles zero; C = nothing tips as sliced."""
    if sliced_max < 0:
        return 'A'
    if sliced_min < 0:
        return 'B'
    return 'C'
