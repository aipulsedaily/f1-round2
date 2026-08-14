"""monocoque_c - the structural skin of the car, built as a subdivision cage.

Philosophy: SUBDIVISION CAGE.
----------------------------
Nothing here is a dense loft. A deliberately structured control cage is built in
(x, u) parameter space - u walks the 7-point half section from belly centre (0)
to centre top (1), exactly the parameterisation `spec.body_surface_point` uses -
and then Catmull-Clark subdivision turns it into the finished skin.

What the cage buys us:

  * class-A-ish fairing for free.  The cage rows are placed on a *smoothed*
    station curve (Catmull-Rom through spec.BODY_STATIONS, soft-clamped so it
    never wanders more than 5 mm from the piecewise-linear reference that
    `spec.station_at` defines), so the piecewise-linear kinks the raw station
    table has at every station are gone without the surface drifting off spec.

  * genuinely sharp chines.  A chine is NOT a crease bolted onto a smooth
    surface - the *section* is given a real corner at the control point and the
    cage carries two support columns 5 mm and 16 mm either side of it, so the
    limit surface turns through the corner in well under a millimetre.  Fade the
    corner weight along x and the chine runs in and out the way a moulded
    carbon edge does.

  * panel lines that are real recessed geometry.  Three cage loops 0.7 mm apart
    with the middle one pushed ~1.0 mm down the normal, all three creased, give
    a 1.4 x 1.0 mm trench whose depth survives subdivision exactly (an uncreased
    cage groove that size gets averaged away to about a third of its depth).
    The two trench walls - and only the walls - carry MatteBlack, because a
    symmetric groove in a 0.028-roughness clearcoat reflects almost exactly like
    the panel around it and the seam simply disappears.

  * apertures cut into the CAGE, before subdividing.  The cockpit, the two
    sidepod inlets and the airbox mouth are holes in the control mesh whose
    border is extruded inwards and down; subdivision then rolls the lip for us
    and the wall thickness is real geometry, not a zero-thickness shell edge.

Where the cage fights back (all measured in renders, all fixed here):
    - a cell-masked aperture leaves a one-cell staircase; the inlet border is
      snapped onto its analytic superellipse (_sp_project).
    - closing the tube on an n-gon makes a valence-140 pole whose ripple
      rendered as a 50 mm radial star at the nose tip; the cap ring is now
      4.5 % of section and approached down a scale ladder (_tip_rows).
    - a seam whose run-out lands between two ordinary cage rows ramps 1 mm of
      depth over 30 mm and that shallow dish flares; every transverse seam now
      either wraps the whole ring or dies into a longitudinal one 0.7 mm away.
    - per-interval smoothstep on the cockpit rim table forced zero slope at
      every node and scalloped the coaming; it is a spline now.

Coordinate contract: +X forward (nose tip x = +3.000, tail x = -2.470), +Y car
left, +Z up, tyre contact z = 0.  Metres.  Nothing bakes in spec.GROUND.

Measured max deviation from `spec.body_surface_point` over the 15 x 7 x 2
reference grid: 0.0044 m outside apertures (0.0908 m at the three frac = 0.92
samples that fall inside the cockpit opening, which is cut away by design).
"""

import math

import bmesh
import bpy
from mathutils import Vector

import common as C
import spec as S

NAME = "monocoque_c"
P = "MCQ_"

SUBD = 2                    # Catmull-Clark levels baked into the mesh
U6 = 6.0 / 7.0              # parameter of the tub-shoulder control point

MAT_SKIN, MAT_CARBON, MAT_DARK, MAT_LIP = 0, 1, 2, 3


# --------------------------------------------------------------------------- #
# reference surface
# --------------------------------------------------------------------------- #

_DENSE = None


def _dense():
    """spec.BODY_STATIONS resampled as a Catmull-Rom in x (4001 samples).

    The station table is only C0 in x - `spec.station_at` lerps between rows, so
    the raw surface has a transverse kink at all 27 stations.  Those kinks show
    as ripples in a 0.028-roughness clearcoat, which is exactly the "lumpy
    section transition" failure.  Smoothing in x fixes them, but the smoothed
    curve overshoots the linear reference by up to 14 mm at the sidepod leading
    edge, so `_station` soft-clamps the difference (tanh) to 5 mm per component.
    """
    global _DENSE
    if _DENSE is None:
        _DENSE = C.catmull_rom(S.BODY_STATIONS, 4001)
    return _DENSE


_SCACHE = {}
_CAP = 0.0050


def _station(x):
    key = round(x, 7)
    st = _SCACHE.get(key)
    if st is not None:
        return st
    d = _dense()
    if x >= d[0][0]:
        sm = d[0]
    elif x <= d[-1][0]:
        sm = d[-1]
    else:
        lo, hi = 0, len(d) - 1
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if d[mid][0] >= x:
                lo = mid
            else:
                hi = mid
        t = (d[lo][0] - x) / (d[lo][0] - d[hi][0])
        sm = tuple(C.lerp(d[lo][k], d[hi][k], t) for k in range(14))
    lin = S.station_at(x)
    st = tuple(lin[k] + _CAP * math.tanh((sm[k] - lin[k]) / _CAP) for k in range(14))
    _SCACHE[key] = st
    return st


def _cr(pts, u):
    """Catmull-Rom on the 8-point half section, identical parameterisation to
    common.catmull_rom (so u = i/64 reproduces body_surface_point(x, i/64))."""
    p = [pts[0]] + list(pts) + [pts[-1]]
    segs = len(p) - 3
    f = u * segs
    if f <= 0.0:
        seg, t = 0, 0.0
    elif f >= segs:
        seg, t = segs - 1, 1.0
    else:
        seg = int(f)
        t = f - seg
    p0, p1, p2, p3 = p[seg], p[seg + 1], p[seg + 2], p[seg + 3]
    t2 = t * t
    t3 = t2 * t
    return (0.5 * (2 * p1[0] + (-p0[0] + p2[0]) * t
                   + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                   + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3),
            0.5 * (2 * p1[1] + (-p0[1] + p2[1]) * t
                   + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                   + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3))


# --------------------------------------------------------------------------- #
# feature lines
# --------------------------------------------------------------------------- #
# weight 0 = leave the smooth Catmull-Rom section alone,
# weight 1 = the section turns a real corner at that control point.
#   1 belly edge   2 undercut waist   3 max width   4 sidepod shoulder
#   6 tub shoulder / cockpit surround
CHINE = {
    1: ((3.00, 0.10), (2.30, 0.34), (1.50, 0.58), (0.60, 0.74), (-0.60, 0.74),
        (-1.40, 0.52), (-2.10, 0.18), (-2.47, 0.00)),
    2: ((3.00, 0.08), (2.30, 0.28), (1.40, 0.50), (0.70, 0.68), (-0.80, 0.68),
        (-1.50, 0.46), (-2.10, 0.16), (-2.47, 0.00)),
    3: ((3.00, 0.25), (2.72, 0.72), (2.20, 0.90), (1.60, 0.90), (1.10, 0.82),
        (0.93, 0.58), (0.87, 0.08), (0.62, 0.08), (0.50, 0.55), (0.28, 0.86),
        (-0.60, 0.88), (-1.20, 0.80), (-1.80, 0.50), (-2.25, 0.16), (-2.47, 0.00)),
    4: ((3.00, 0.18), (2.50, 0.52), (1.60, 0.70), (0.95, 0.80), (0.42, 0.92),
        (-0.70, 0.92), (-1.30, 0.78), (-1.90, 0.42), (-2.30, 0.12), (-2.47, 0.00)),
    6: ((3.00, 0.00), (2.20, 0.12), (1.45, 0.50), (0.95, 0.80), (0.10, 0.86),
        (-0.09, 0.72), (-0.16, 0.30), (-0.30, 0.06), (-2.47, 0.00)),
}

CHINE_WIN = 0.020           # corner blend window, metres of section arc
SUP_INNER = 0.0052          # inner support column, metres of arc off the corner
SUP_OUTER = 0.0165          # outer support column


def _tab(tab, x):
    if x >= tab[0][0]:
        return tab[0][1]
    if x <= tab[-1][0]:
        return tab[-1][1]
    for (x0, v0), (x1, v1) in zip(tab, tab[1:]):
        if x1 <= x <= x0:
            return C.lerp(v0, v1, (x0 - x) / (x0 - x1))
    return tab[-1][1]


class _Row(object):
    """Everything needed to evaluate one station's half section."""

    __slots__ = ("x", "ctrl", "feat", "spine", "seg", "zc")

    def __init__(self, x):
        self.x = x
        c = S.station_half(_station(x))
        self.ctrl = c
        self.zc = 0.5 * (c[0][1] + c[7][1])
        self.seg = [math.hypot(c[k + 1][0] - c[k][0], c[k + 1][1] - c[k][1])
                    for k in range(7)]

        self.feat = {}
        for k, tab in CHINE.items():
            w = _tab(tab, x)
            la, lb = self.seg[k - 1], self.seg[k]
            if w <= 0.004 or la < 1e-6 or lb < 1e-6:
                continue
            cp = c[k]
            din = ((cp[0] - c[k - 1][0]) / la, (cp[1] - c[k - 1][1]) / la)
            dout = ((c[k + 1][0] - cp[0]) / lb, (c[k + 1][1] - cp[1]) / lb)
            win = min(CHINE_WIN, 0.42 * la, 0.42 * lb)
            self.feat[k] = (cp, din, dout, w, win, k / 7.0)

        # crown / spine rounding.  spec's section arrives at the centreline with
        # a non-zero lateral tangent, so mirroring it gives a razor ridge down
        # the whole spine.  Fillet it with a fixed apex drop.
        self.spine = None
        v = c[7]
        gy, gz = c[6][0] - v[0], c[6][1] - v[1]
        gl = math.hypot(gy, gz)
        if gl > 1e-5:
            gy, gz = gy / gl, gz / gl
            if abs(gz) > 0.055 and gy > 0.25:
                drop = 0.0130
                lt = drop * abs(gz) / max(1e-4, 1.0 - gy)
                lt = max(0.006, min(lt, 0.45 * gl))
                r = lt * gy / abs(gz)
                d = r / gy
                o = (0.0, v[1] + math.copysign(d, gz))
                self.spine = (v, lt, r, o)

    def pt(self, u):
        y, z = _cr(self.ctrl, u)
        for cp, din, dout, w, win, uf in self.feat.values():
            dy, dz = y - cp[0], z - cp[1]
            s = math.hypot(dy, dz)
            if s >= win or s < 1e-9:
                continue
            if u < uf:
                qy, qz = cp[0] - din[0] * s, cp[1] - din[1] * s
            else:
                qy, qz = cp[0] + dout[0] * s, cp[1] + dout[1] * s
            t = s / win
            b = w * (1.0 - t * t * (3.0 - 2.0 * t))
            y += (qy - y) * b
            z += (qz - z) * b
        sp = self.spine
        if sp is not None:
            v, lt, r, o = sp
            s = math.hypot(y - v[0], z - v[1])
            if s < lt:
                dy, dz = y - o[0], z - o[1]
                dl = math.hypot(dy, dz)
                if dl > 1e-9:
                    t = s / lt
                    b = 1.0 - t * t * (3.0 - 2.0 * t)
                    ty, tz = o[0] + dy / dl * r, o[1] + dz / dl * r
                    y += (ty - y) * b
                    z += (tz - z) * b
        return y, z


_ROWS = {}


def _row(x):
    k = round(x, 7)
    r = _ROWS.get(k)
    if r is None:
        r = _Row(x)
        _ROWS[k] = r
    return r


# --------------------------------------------------------------------------- #
# nose / tail tip rounding
# --------------------------------------------------------------------------- #

TIP_F0, TIP_F1 = 2.9560, 3.0000
TIP_R0, TIP_R1 = -2.4430, -2.4700


TIP_FLOOR = 0.045
# scale ladder for the rounded nose / tail caps.  The tube closes on an n-gon
# whose centre becomes a valence-140 extraordinary vertex; the only way to keep
# its ripple sub-millimetre is to make that cap tiny AND approach it with rows
# spaced like the scale ladder rather than like the rest of the body.
TIP_SCALES = (0.20, 0.30, 0.42, 0.54, 0.66, 0.77, 0.88, 0.955, 0.993)


def _tip_scale(x):
    if x >= TIP_F0:
        t = min(1.0, (x - TIP_F0) / (TIP_F1 - TIP_F0))
        return max(TIP_FLOOR, math.sqrt(max(0.0, 1.0 - t * t)))
    if x <= TIP_R0:
        t = min(1.0, (TIP_R0 - x) / (TIP_R0 - TIP_R1))
        return max(TIP_FLOOR, math.sqrt(max(0.0, 1.0 - t * t)))
    return 1.0


def _tip_rows():
    out = []
    for sc in TIP_SCALES:
        t = math.sqrt(max(0.0, 1.0 - sc * sc))
        out.append(TIP_F0 + t * (TIP_F1 - TIP_F0))
        out.append(TIP_R0 - t * (TIP_R0 - TIP_R1))
    return out


def _P(x, u):
    r = _row(x)
    y, z = r.pt(u)
    s = _tip_scale(x)
    if s < 1.0:
        y *= s
        z = r.zc + (z - r.zc) * s
    return Vector((x, y, z))


def _frame(x, u):
    """(position, outward normal, +u tangent, +x tangent) on the +y half."""
    hu = 0.0035
    hx = 0.0030
    p = _P(x, u)
    du = _P(x, min(1.0, u + hu)) - _P(x, max(0.0, u - hu))
    dx = _P(x + hx, u) - _P(x - hx, u)
    if du.length < 1e-9:
        du = Vector((0.0, -1.0, 0.0))
    if dx.length < 1e-9:
        dx = Vector((1.0, 0.0, 0.0))
    n = dx.cross(du)
    if n.length < 1e-9:
        n = Vector((0.0, 1.0, 0.0))
    n.normalize()
    axis = Vector((x, 0.0, _row(x).zc))
    if n.dot(p - axis) < 0.0:
        n = -n
    return p, n, du.normalized(), dx.normalized()


# --------------------------------------------------------------------------- #
# panel-line seams
# --------------------------------------------------------------------------- #
# longitudinal: (segment, local fraction, x_from, x_to, depth, run-out)
LONG_SEAM = {
    "G1": dict(seg=4, f=0.30, x0=0.9050, x1=-1.5200, d=0.00102),  # sidepod top
    "G2": dict(seg=2, f=0.30, x0=0.9050, x1=-1.5200, d=0.00100),  # under the inlet
    "G3": dict(seg=5, f=0.70, x0=0.9050, x1=-0.6150, d=0.00098),  # cockpit surround
    "G4": dict(seg=3, f=0.30, x0=2.4000, x1=1.6600, d=0.00096),   # nose flank
    "G5": dict(seg=4, f=0.70, x0=-0.7000, x1=-1.0800, d=0.00098),  # hatch lower
    "G6": dict(seg=5, f=0.30, x0=-0.7000, x1=-1.0800, d=0.00098),  # hatch upper
}
HATCH_U0, HATCH_U1 = (4 + 0.70) / 7.0, (5 + 0.30) / 7.0
# transverse: x, active u window, depth.  A window that stops mid-panel makes
# the trench ramp out over one whole cage cell (~30 mm) and that shallow dish
# flares in the clearcoat, so every transverse seam either wraps the full ring
# or dies into a longitudinal trench 0.7 mm away.
TRANS_SEAM = {
    "T5": dict(x=2.4000, u0=-1.0, u1=2.0, d=0.00096),
    "T1": dict(x=1.6600, u0=-1.0, u1=2.0, d=0.00108),
    "T2": dict(x=0.9050, u0=-1.0, u1=2.0, d=0.00104),
    "T3": dict(x=-0.6150, u0=-1.0, u1=2.0, d=0.00108),
    "T4": dict(x=-1.5200, u0=-1.0, u1=2.0, d=0.00108),
    "T6": dict(x=-0.7000, u0=HATCH_U0 - 0.0002, u1=HATCH_U1 + 0.0002, d=0.00098),
    "T7": dict(x=-1.0800, u0=HATCH_U0 - 0.0002, u1=HATCH_U1 + 0.0002, d=0.00098),
}
SEAM_HALF = 0.00070         # half width of a seam trench
LONG_RUNOUT = 0.00060       # metres of x
TRANS_RUNOUT = 0.00030      # parameter u


def _ramp(v, lo, hi):
    if hi <= lo:
        return 1.0
    return max(0.0, min(1.0, (v - lo) / (hi - lo)))


def _long_active(g, x):
    a, b = g["x1"], g["x0"]
    return (_ramp(x, a, a + LONG_RUNOUT)
            * _ramp(-x, -b, -b + LONG_RUNOUT))


def _trans_active(t, u):
    return (_ramp(u, t["u0"], t["u0"] + TRANS_RUNOUT)
            * _ramp(-u, -t["u1"], -t["u1"] + TRANS_RUNOUT))


# --------------------------------------------------------------------------- #
# apertures
# --------------------------------------------------------------------------- #

COCKPIT_RIM = [
    (0.7800, 0.0460), (0.7500, 0.0940), (0.7150, 0.1250), (0.6700, 0.1520),
    (0.6100, 0.1790), (0.5300, 0.2020), (0.4400, 0.2170), (0.3400, 0.2240),
    (0.2200, 0.2270), (0.0900, 0.2255), (-0.0200, 0.2170), (-0.0560, 0.2075),
    (-0.0880, 0.1915), (-0.1120, 0.1705), (-0.1300, 0.1430),
]
AIRBOX_RIM = [
    (-0.1880, 0.0440), (-0.2000, 0.0790), (-0.2140, 0.0985), (-0.2300, 0.1070),
    (-0.2460, 0.1040), (-0.2600, 0.0880), (-0.2700, 0.0460),
]
CK_X0, CK_X1 = 0.7800, -0.1300
AB_X0, AB_X1 = -0.1880, -0.2700
CK_LEAD, CK_TRAIL = 0.9050, -0.4400       # where the boundary column rejoins u6

SP_X0, SP_X1 = 0.8460, 0.6150             # sidepod inlet, x extent
SP_UC, SP_LU = 0.4380, 0.0810             # mouth centre / half height in u
SP_N = 3.5                                # superellipse exponent (letterbox)
SP_XC = 0.5 * (SP_X0 + SP_X1)
SP_LX = 0.5 * (SP_X0 - SP_X1)


def _sp_inside(x, u):
    return ((abs(x - SP_XC) / SP_LX) ** SP_N
            + (abs(u - SP_UC) / SP_LU) ** SP_N) <= 1.0


def _sp_project(x, u):
    """Radially snap a staircase border vertex onto the analytic mouth outline.

    Masking cage cells against the outline leaves a one-cell staircase, and at
    cage resolution that is a 15 mm sawtooth the lip roll cannot hide.  Pulling
    every border vertex onto the true superellipse costs at most half a cell of
    shear in the neighbouring quads and buys a genuinely fair mouth.
    """
    th = math.atan2((u - SP_UC) / SP_LU, (x - SP_XC) / SP_LX)
    e = 2.0 / SP_N
    c, s = math.cos(th), math.sin(th)
    return (SP_XC + SP_LX * math.copysign(abs(c) ** e, c),
            SP_UC + SP_LU * math.copysign(abs(s) ** e, s))

U_MIN_GAP = 0.0062          # boundary column never collapses onto the u6 chine


_TABD = {}


def _tab_pts(tbl, x):
    """Catmull-Rom through a (x, value) table.

    This started as per-interval smoothstep, which forces zero slope at every
    table node - the cockpit rim came out visibly scalloped, one bump per row
    of the table.  A spline through the same points is fair.
    """
    key = id(tbl)
    d = _TABD.get(key)
    if d is None:
        d = C.catmull_rom(list(tbl), 800)
        _TABD[key] = d
    if x >= d[0][0]:
        return d[0][1]
    if x <= d[-1][0]:
        return d[-1][1]
    lo, hi = 0, len(d) - 1
    while hi - lo > 1:
        m = (lo + hi) // 2
        if d[m][0] >= x:
            lo = m
        else:
            hi = m
    t = (d[lo][0] - x) / max(1e-12, d[lo][0] - d[hi][0])
    return C.lerp(d[lo][1], d[hi][1], t)


def _open_hw(x):
    """Half width (y) of the top aperture boundary, and whether it is open."""
    if x > CK_LEAD or x < CK_TRAIL:
        return None, 0.0
    if CK_X0 >= x >= CK_X1:
        return _tab_pts(COCKPIT_RIM, x), 1.0
    if AB_X0 >= x >= AB_X1:
        return _tab_pts(AIRBOX_RIM, x), 1.0
    if x > CK_X0:                                   # deck ahead of the cockpit
        t = _smooth(_ramp(-x, -CK_LEAD, -CK_X0))
        return C.lerp(_shoulder_hw(CK_LEAD), 0.0460, t), 0.0
    if CK_X1 > x > AB_X0:                           # roll-hoop bulkhead
        t = _smooth(_ramp(-x, -CK_X1, -AB_X0))
        return C.lerp(COCKPIT_RIM[-1][1], AIRBOX_RIM[0][1], t), 0.0
    t = _smooth(_ramp(-x, -AB_X1, -CK_TRAIL))       # behind the airbox
    return C.lerp(AIRBOX_RIM[-1][1], _shoulder_hw(CK_TRAIL), t), 0.0


def _smooth(t):
    return t * t * (3.0 - 2.0 * t)


def _shoulder_hw(x):
    return S.station_half(_station(x))[6][0]


def _boundary_u(x):
    """u of the top aperture boundary column at station x (>= U6 + gap)."""
    hw, openw = _open_hw(x)
    r = _row(x)
    if hw is None:
        return U6 + U_MIN_GAP, 0.0
    lo, hi = U6, 0.99920
    y_lo = r.pt(lo)[0]
    if hw >= y_lo:
        return U6 + U_MIN_GAP, openw
    for _ in range(34):
        mid = 0.5 * (lo + hi)
        if r.pt(mid)[0] > hw:
            lo = mid
        else:
            hi = mid
    return max(U6 + U_MIN_GAP, 0.5 * (lo + hi)), openw


# --------------------------------------------------------------------------- #
# the control cage: columns
# --------------------------------------------------------------------------- #
# Every segment of the 7-piece half section gets:
#   two support columns hugging each end control point (so a chine there turns
#   in < 1 mm), and three interior columns, one of which is exactly the
#   parameter `spec.body_surface_point` samples for that segment.
_MIDF = [0.546875, 0.531250, 0.515625, 0.500000, 0.484375, 0.468750, 0.453125]
DECK_T = (0.18, 0.36, 0.54, 0.72, 0.86)


def _seg_fracs(seg):
    inner = [0.30, _MIDF[seg], 0.70]
    out = []
    for f in inner:
        gid = None
        for k, g in LONG_SEAM.items():
            if g["seg"] == seg and abs(g["f"] - f) < 1e-6:
                gid = k
        if gid is None:
            out.append(("u", f, None))
        else:
            out.append(("s", f, (gid, -1)))
            out.append(("s", f, (gid, 0)))
            out.append(("s", f, (gid, 1)))
    return out


def _columns():
    """Column descriptors, belly centre -> centre top.

    kind 'k' control point, 'p' plain, 's' seam member, 'd' cockpit deck,
    'b' aperture boundary.
    """
    cols = []
    for seg in range(7):
        cols.append(dict(kind="k", k=seg, seg=seg, f=0.0))
        if seg == 6:
            # the deck band that carries the cockpit / airbox coaming: fillers
            # plus the aperture boundary column itself, all of them riding on
            # the boundary parameter so the rim can sweep without a staircase.
            for t in DECK_T:
                cols.append(dict(kind="d", t=t))
            cols.append(dict(kind="b"))
        if seg == 0:
            lo = [dict(kind="p", seg=seg, f=0.10, sup=None),
                  dict(kind="p", seg=seg, f=0.20, sup=None)]
        else:
            lo = [dict(kind="p", seg=seg, f=None, sup=("lo", 0)),
                  dict(kind="p", seg=seg, f=None, sup=("lo", 1))]
        if seg == 6:
            hi = [dict(kind="p", seg=seg, f=0.80, sup=None),
                  dict(kind="p", seg=seg, f=0.90, sup=None)]
        else:
            hi = [dict(kind="p", seg=seg, f=None, sup=("hi", 1)),
                  dict(kind="p", seg=seg, f=None, sup=("hi", 0))]
        cols.extend(lo)
        for _kind, f, seam in _seg_fracs(seg):
            cols.append(dict(kind="s" if seam else "p", seg=seg, f=f, seam=seam,
                             sup=None))
        cols.extend(hi)
    cols.append(dict(kind="k", k=7, seg=6, f=1.0))
    for i, c in enumerate(cols):
        c["i"] = i
    return cols


COLS = _columns()
NCH = len(COLS)
M = 2 * NCH - 2
J_BOUND = next(c["i"] for c in COLS if c["kind"] == "b")
J_U6 = next(c["i"] for c in COLS if c["kind"] == "k" and c["k"] == 6)


def _nominal_u(c):
    if c["kind"] == "k":
        return c["k"] / 7.0
    if c["kind"] == "d":
        return U6 + 1e-4
    if c["kind"] == "b":
        return U6 + 2e-4
    if c.get("sup"):
        end, idx = c["sup"]
        f = (0.04, 0.13)[idx] if end == "lo" else 1.0 - (0.04, 0.13)[idx]
        return (c["seg"] + f) / 7.0
    return (c["seg"] + c["f"]) / 7.0


NOM_U = [_nominal_u(c) for c in COLS]


def _row_u(x):
    """Actual u for every column at station x (monotonically increasing)."""
    r = _row(x)
    ub, openw = _boundary_u(x)
    us = [0.0] * NCH
    for c in COLS:
        i = c["i"]
        kind = c["kind"]
        if kind == "k":
            us[i] = c["k"] / 7.0
        elif kind == "d":
            us[i] = U6 + (ub - U6) * c["t"]
        elif kind == "b":
            us[i] = ub
        elif c.get("sup"):
            seg = c["seg"]
            end, idx = c["sup"]
            arc = SUP_INNER if idx == 0 else SUP_OUTER
            sl = max(1e-5, r.seg[seg])
            fr = min(0.11 if idx == 0 else 0.27, arc / sl)
            us[i] = (seg + (fr if end == "lo" else 1.0 - fr)) / 7.0
        else:
            seg = c["seg"]
            f = c["f"]
            if c["kind"] == "s":
                gid, side = c["seam"]
                sl = max(1e-5, r.seg[seg])
                du = SEAM_HALF / sl / 7.0
                f = f + side * du * 7.0
            us[i] = (seg + f) / 7.0
    # segment 6 columns are squeezed above the aperture boundary
    for c in COLS:
        i = c["i"]
        if c["kind"] in ("d", "b", "k"):
            continue
        if c["seg"] != 6:
            continue
        t = (NOM_U[i] - U6) / (1.0 - U6)
        us[i] = ub + (1.0 - ub) * t
    us[NCH - 1] = 1.0
    for i in range(1, NCH):                      # safety: keep strictly sorted
        if us[i] <= us[i - 1] + 2e-5:
            us[i] = us[i - 1] + 2e-5
    us[NCH - 1] = min(1.0, us[NCH - 1])
    return us, ub, openw


# --------------------------------------------------------------------------- #
# the control cage: rows
# --------------------------------------------------------------------------- #

def _step(x):
    if x > 2.870:
        return 0.0220
    if x > 2.300:
        return 0.0420
    if x > 1.750:
        return 0.0540
    if x > 1.020:
        return 0.0620
    if x > 0.880:
        return 0.0340
    if x > 0.590:
        return 0.0165          # sidepod inlet mouth needs a fine outline
    if x > 0.420:
        return 0.0290
    if x > 0.020:
        return 0.0380
    if x > -0.090:
        return 0.0250
    if x > -0.330:
        return 0.0135          # roll hoop rises 400 mm in 240 mm of x
    if x > -0.470:
        return 0.0230
    if x > -0.720:
        return 0.0340
    if x > -1.450:
        return 0.0600
    if x > -2.020:
        return 0.0520
    if x > -2.300:
        return 0.0350
    return 0.0200


def _rows():
    xs = [3.0000]
    x = 3.0000
    while x > -2.4700:
        x -= _step(x)
        if x < -2.4700:
            break
        xs.append(x)
    xs.append(-2.4700)

    forced = [CK_X0, CK_X1, AB_X0, AB_X1, SP_X0, SP_X1, CK_LEAD, CK_TRAIL,
              TIP_F0, TIP_R0] + _tip_rows()
    for t in TRANS_SEAM.values():
        forced += [t["x"] - SEAM_HALF, t["x"], t["x"] + SEAM_HALF]
    for g in LONG_SEAM.values():
        forced += [g["x0"], g["x1"]]
    forced = sorted(set(round(v, 6) for v in forced))
    keep = [v for v in xs if all(abs(v - f) > 0.0048 for f in forced)
            and TIP_R0 - 0.0005 < v < TIP_F0 + 0.0005]
    xs = sorted(set(round(v, 6) for v in keep) | set(forced), reverse=True)
    return xs


# --------------------------------------------------------------------------- #
# seam depth field
# --------------------------------------------------------------------------- #

def _seam_offset(x, i_seam_row, col, u_act, seam_rows):
    """Inward normal offset (negative) plus seam membership for one cage vertex.

    Returns (offset, long_activity, trans_activity, long_gid)."""
    off = 0.0
    cl = 0.0
    ct = 0.0
    lgid = None
    c = col
    if c["kind"] == "s":
        gid, side = c["seam"]
        g = LONG_SEAM[gid]
        a = _long_active(g, x)
        if a > 0.0:
            cl = a
            lgid = gid
            if side == 0:
                off = min(off, -g["d"] * a)
    tid = seam_rows.get(i_seam_row)
    if tid is not None:
        gid, side = tid
        t = TRANS_SEAM[gid]
        a = _trans_active(t, u_act)
        if a > 0.0:
            ct = a
            if side == 0:
                off = min(off, -t["d"] * a)
    return off, cl, ct, lgid


# --------------------------------------------------------------------------- #
# build
# --------------------------------------------------------------------------- #

def _hole_loop(cells, ncols):
    """Trace the border of a set of deleted cage cells.

    cells: set of (row, col) quads that were removed.  Returns the border as an
    ordered [(row, col, (di, dj))] ring, where (di, dj) is the inward direction
    expressed in grid-index steps - summed from the border edges meeting at that
    vertex, so a diagonal staircase corner gets a diagonal inward vector and the
    lip never folds back over surviving skin.
    """
    out_edge = {}
    for (i, j) in cells:
        jn = (j + 1) % ncols
        jp = (j - 1) % ncols
        for a, b, inw, nb in (((i, j), (i, jn), (1, 0), (i - 1, j)),
                              ((i, jn), (i + 1, jn), (0, -1), (i, jn)),
                              ((i + 1, jn), (i + 1, j), (-1, 0), (i + 1, j)),
                              ((i + 1, j), (i, j), (0, 1), (i, jp))):
            if nb not in cells:
                if a in out_edge:
                    raise RuntimeError("aperture pinches at %r" % (a,))
                out_edge[a] = (b, inw)
    if not out_edge:
        return []
    start = min(out_edge)
    loop, v = [], start
    while True:
        loop.append(v)
        v = out_edge[v][0]
        if v == start:
            break
        if len(loop) > len(out_edge) + 2:
            raise RuntimeError("aperture border did not close")
    if len(loop) != len(out_edge):
        raise RuntimeError("aperture border is not a single ring")
    ring = []
    n = len(loop)
    for k, v in enumerate(loop):
        a = out_edge[v][1]
        b = out_edge[loop[(k - 1) % n]][1]
        ring.append((v[0], v[1], (a[0] + b[0], a[1] + b[1])))
    return ring


def _band_rings(loop, prof):
    """loop: [(pos, n, inward)]; prof: [(along inward, along -n)] offsets."""
    rings = []
    for a_in, a_n in prof:
        rings.append([p + inw * a_in + n * a_n for (p, n, inw) in loop])
    return rings


CK_FLOOR = [(0.780, 0.400), (0.620, 0.330), (0.450, 0.272), (0.300, 0.238),
            (0.100, 0.222), (-0.060, 0.232), (-0.185, 0.310)]


def _ck_floor(x):
    return _tab_pts(CK_FLOOR, x)


def _build_skin(coll):
    xs = _rows()
    nrow = len(xs)

    seam_rows = {}
    for gid, t in TRANS_SEAM.items():
        for side, xv in ((-1, t["x"] + SEAM_HALF), (0, t["x"]), (1, t["x"] - SEAM_HALF)):
            for i, x in enumerate(xs):
                if abs(x - xv) < 1e-6:
                    seam_rows[i] = (gid, side)

    verts = []
    faces = []
    fmat = []
    creases = {}
    grid = [[0] * M for _ in range(nrow)]
    lgid = [[None] * NCH for _ in range(nrow)]
    tval = [[0.0] * NCH for _ in range(nrow)]

    row_u = []
    row_ub = []
    row_open = []
    for x in xs:
        us, ub, ow = _row_u(x)
        row_u.append(us)
        row_ub.append(ub)
        row_open.append(ow)

    # ---- vertices -------------------------------------------------------- #
    for i, x in enumerate(xs):
        us = row_u[i]
        pos_half = []
        cl_half = [0.0] * NCH
        ct_half = [0.0] * NCH
        for c in COLS:
            j = c["i"]
            u = us[j]
            off, cl, ct, lg = _seam_offset(x, i, c, u, seam_rows)
            cl_half[j] = cl
            ct_half[j] = ct
            lgid[i][j] = lg if cl > 0.5 else None
            tval[i][j] = ct
            if off != 0.0:
                p, n, _tu, _tx = _frame(x, u)
                p = p + n * off
            else:
                p = _P(x, u)
            pos_half.append(p)
        for j in range(M):
            hh = j if j < NCH else 2 * NCH - 2 - j
            sy = 1.0 if j < NCH else -1.0
            p = pos_half[hh]
            grid[i][j] = len(verts)
            verts.append((p.x, sy * p.y, p.z))
        # creases: along-x edges for longitudinal seams
        if i > 0:
            for j in range(M):
                hh = j if j < NCH else 2 * NCH - 2 - j
                v = min(cl_half[hh], 1.0)
                if v > 0.02:
                    creases[(grid[i - 1][j], grid[i][j])] = v
        # creases: around-ring edges for transverse seams
        if i in seam_rows:
            for j in range(M):
                hh0 = j if j < NCH else 2 * NCH - 2 - j
                j2 = (j + 1) % M
                hh1 = j2 if j2 < NCH else 2 * NCH - 2 - j2
                v = min(ct_half[hh0], ct_half[hh1], 1.0)
                if v > 0.02:
                    creases[(grid[i][j], grid[i][j2])] = v

    # ---- aperture masks -------------------------------------------------- #
    def top_open(i):
        return row_open[i] > 0.5

    # The inlet mouth is a superellipse in (x, u); cage cells whose centre falls
    # inside it are removed and the resulting staircase border is then snapped
    # back onto the analytic outline (see _sp_project).
    side0 = set()
    for i in range(nrow - 1):
        xm = 0.5 * (xs[i] + xs[i + 1])
        if not (SP_X1 - 0.02 <= xm <= SP_X0 + 0.02):
            continue
        for j in range(1, NCH - 1):
            um = 0.25 * (row_u[i][j] + row_u[i][j + 1]
                         + row_u[i + 1][j] + row_u[i + 1][j + 1])
            if _sp_inside(xm, um):
                side0.add((i, j))
    # regularise: no diagonal-only contacts, no one-cell spurs
    for _ in range(3):
        for (i, j) in list(side0):
            nb = sum(1 for c in ((i - 1, j), (i + 1, j), (i, j - 1), (i, j + 1))
                     if c in side0)
            if nb <= 1:
                side0.discard((i, j))
        add = set()
        for (i, j) in side0:
            for c in ((i - 1, j), (i + 1, j), (i, j - 1), (i, j + 1)):
                nb = sum(1 for d in ((c[0] - 1, c[1]), (c[0] + 1, c[1]),
                                     (c[0], c[1] - 1), (c[0], c[1] + 1))
                         if d in side0)
                if nb >= 3:
                    add.add(c)
        side0 |= add
    side1 = set((i, M - 1 - j) for (i, j) in side0)
    sp_sides = [side0, side1] if len(side0) > 8 else []
    sp_cells = side0 | side1

    sp_rings = []
    proj = {}
    for cells in sp_sides:
        ring = _hole_loop(cells, M)
        sp_rings.append(ring)
        for (i, j, _d) in ring:
            hh = j if j < NCH else 2 * NCH - 2 - j
            sy = 1.0 if j < NCH else -1.0
            xq, uq = _sp_project(xs[i], row_u[i][hh])
            proj[(i, j)] = (xq, uq)
            p = _P(xq, uq)
            verts[grid[i][j]] = (p.x, sy * p.y, p.z)

    def face_skipped(i, j):
        if top_open(i) and top_open(i + 1):
            if J_BOUND <= j <= M - J_BOUND - 1:
                return True
        return (i, j) in sp_cells

    # ---- faces ----------------------------------------------------------- #
    for i in range(nrow - 1):
        for j in range(M):
            if face_skipped(i, j):
                continue
            j2 = (j + 1) % M
            faces.append((grid[i][j], grid[i][j2], grid[i + 1][j2], grid[i + 1][j]))
            hh = j if j < NCH else 2 * NCH - 2 - j
            h2 = j2 if j2 < NCH else 2 * NCH - 2 - j2
            # A trench wall - and ONLY a trench wall - is painted matte black:
            # a symmetric 1 mm groove in gloss paint reflects almost exactly
            # like the panel around it and the seam disappears, while a real
            # gap shows the dark structure underneath.  The test is strict
            # (both ends of the quad inside the same trench) so the run-out
            # ramp never gets painted.
            dark = lgid[i][hh] is not None and lgid[i][hh] == lgid[i][h2]
            if not dark:
                ta, tb = seam_rows.get(i), seam_rows.get(i + 1)
                if ta is not None and tb is not None and ta[0] == tb[0]:
                    dark = min(tval[i][hh], tval[i][h2],
                               tval[i + 1][hh], tval[i + 1][h2]) > 0.5
            fmat.append(MAT_DARK if dark
                        else (MAT_CARBON if NOM_U[hh] < 0.128 else MAT_SKIN))

    # nose and tail caps
    faces.append(tuple(grid[0][j] for j in range(M)))
    fmat.append(MAT_SKIN)
    faces.append(tuple(grid[nrow - 1][j] for j in range(M - 1, -1, -1)))
    fmat.append(MAT_SKIN)

    # ---- aperture lips --------------------------------------------------- #
    # Every aperture is a rectangle in cage index space.  Its border ring is
    # walked once, each border vertex gets an outward normal and an "inward"
    # direction lying in the tangent plane, and the lip / throat is a set of
    # rings offset along those two axes.  Subdivision then rolls the lip.
    def rim(ring):
        ids, loop = [], []
        for (i, j, (di, dj)) in ring:
            jj = j % M
            ids.append(grid[i][jj])
            hh = jj if jj < NCH else 2 * NCH - 2 - jj
            sy = 1.0 if jj < NCH else -1.0
            xq, uq = proj.get((i, jj), (xs[i], row_u[i][hh]))
            p, n, tu, tx = _frame(xq, uq)
            mir = (lambda v: Vector((v.x, sy * v.y, v.z)))
            p, n, tu, tx = mir(p), mir(n), mir(tu), mir(tx)
            # +i steps toward the tail, +j steps toward the centreline on the
            # +y half and away from it once the ring has wrapped
            h = (-tx) * di + (tu if jj < NCH else -tu) * dj
            if h.length < 1e-9:
                h = tu
            loop.append([p, n, h.normalized()])
        cnt = len(loop)
        out = []
        for k in range(cnt):
            a = loop[(k - 1) % cnt][0]
            b = loop[(k + 1) % cnt][0]
            p, n, h = loop[k]
            t = b - a
            t = t - n * t.dot(n)
            if t.length < 1e-9:
                t = h.cross(n)
            t.normalize()
            inw = n.cross(t)
            if inw.dot(h) < 0.0:
                inw = -inw
            if inw.length < 1e-9:
                inw = h
            out.append((p, n, inw.normalized()))
        return ids, out

    def lip(ids, loop, prof, mats):
        base = len(verts)
        rings = _band_rings(loop, prof)
        for ring in rings:
            for p in ring:
                verts.append((p.x, p.y, p.z))
        n = len(loop)
        for k in range(n):
            k2 = (k + 1) % n
            faces.append((ids[k], ids[k2], base + k2, base + k))
            fmat.append(MAT_LIP)
        for r in range(len(rings) - 1):
            a, b = base + r * n, base + (r + 1) * n
            for k in range(n):
                k2 = (k + 1) % n
                faces.append((a + k, a + k2, b + k2, b + k))
                fmat.append(mats[min(r, len(mats) - 1)])
        return base + (len(rings) - 1) * n, n, rings[-1]

    def extend(prev_base, n, rings):
        pb = prev_base
        for ring in rings:
            nb = len(verts)
            for p in ring:
                verts.append((p.x, p.y, p.z))
            for k in range(n):
                k2 = (k + 1) % n
                faces.append((pb + k, pb + k2, nb + k2, nb + k))
                fmat.append(MAT_DARK)
            pb = nb
        faces.append(tuple(range(pb, pb + n)))
        fmat.append(MAT_DARK)

    # --- top aperture: cockpit and airbox --- #
    ck_rows = [i for i, x in enumerate(xs) if CK_X0 + 1e-6 >= x >= CK_X1 - 1e-6]
    ab_rows = [i for i, x in enumerate(xs) if AB_X0 + 1e-6 >= x >= AB_X1 - 1e-6]

    COAM = [(0.0042, 0.0016), (0.0094, -0.0036), (0.0122, -0.0138)]
    for rows_, is_ck in ((ck_rows, True), (ab_rows, False)):
        if len(rows_) < 2:
            continue
        cells = set()
        for i in range(rows_[0], rows_[-1]):
            for j in range(J_BOUND, M - J_BOUND):
                cells.add((i, j))
        ids, loop = rim(_hole_loop(cells, M))
        pb, n, last = lip(ids, loop, COAM, [MAT_LIP, MAT_DARK])
        if is_ck:
            xc = 0.30
            more = []
            # shrink the survival-cell shell down in stages; the final n-gon cap
            # has to be small or Catmull-Clark fans it into visible radial
            # creases across the whole cockpit floor.
            # The survival-cell blanking shell.  The last two rings are at a
            # CONSTANT z so the n-gon that closes the floor is planar - a
            # non-planar cap fans into radial creases that were clearly
            # visible through the cockpit opening from above.
            for fx, fy, dz, zoff in ((0.992, 0.976, 0.060, None),
                                     (0.978, 0.945, 0.140, 0.150),
                                     (0.950, 0.890, 0.240, 0.062),
                                     (0.880, 0.740, 0.330, 0.006),
                                     (0.760, 0.520, None, 0.2160),
                                     (0.720, 0.470, None, 0.2100)):
                ring = []
                for p in last:
                    zf = _ck_floor(p.x)
                    if dz is None:
                        z = zoff
                    else:
                        z = p.z - dz if zoff is None else max(zf + zoff, p.z - dz)
                    ring.append(Vector((xc + (p.x - xc) * fx, p.y * fy, z)))
                more.append(ring)
        else:
            more = []
            for a_in, a_n in ((0.0055, -0.030), (0.0050, -0.060)):
                more.append([last[k] + loop[k][2] * a_in + loop[k][1] * a_n
                             for k in range(n)])
            # close the airbox throat on a plane of constant x so the n-gon
            # cap stays planar and does not fan
            prev = more[-1]
            cy = sum(q.y for q in prev) / n
            cz = sum(q.z for q in prev) / n
            xb = min(q.x for q in prev) - 0.016
            more.append([Vector((xb, cy + (q.y - cy) * 0.80,
                                 cz + (q.z - cz) * 0.80)) for q in prev])
        extend(pb, n, more)

    # --- sidepod inlets --- #
    SPP = [(0.0050, 0.0015), (0.0108, -0.0042), (0.0136, -0.0170)]
    for ring in sp_rings:
        ids, loop = rim(ring)
        pb, n_, last = lip(ids, loop, SPP, [MAT_LIP, MAT_DARK])
        more = []
        for a_in, a_n in ((0.0034, -0.032), (-0.0030, -0.048)):
            more.append([last[k] + loop[k][2] * a_in + loop[k][1] * a_n
                         for k in range(n_)])
        extend(pb, n_, more)

    ob = C.new_obj(P + "Skin", verts, faces, coll=coll, smooth=True)
    me = ob.data
    for k, idx in enumerate(fmat):
        if k < len(me.polygons):
            me.polygons[k].material_index = idx

    for nm in ("LiveryPaint", "CarbonMatte", "MatteBlack", "CarbonFibre"):
        me.materials.append(S.mat(nm))

    # creases
    if creases:
        emap = {}
        for e in me.edges:
            a, b = e.vertices
            emap[(a, b)] = e.index
            emap[(b, a)] = e.index
        attr = me.attributes.get("crease_edge")
        if attr is None:
            attr = me.attributes.new("crease_edge", "FLOAT", "EDGE")
        data = attr.data
        for (a, b), v in creases.items():
            ei = emap.get((a, b))
            if ei is not None:
                data[ei].value = max(data[ei].value, min(1.0, v))

    C.merge_doubles(ob, 1e-6)

    # cage vertices stranded inside an aperture carry no faces; drop them so
    # the cage stays a clean manifold
    bm = bmesh.new()
    bm.from_mesh(me)
    loose = [v for v in bm.verts if not v.link_faces]
    if loose:
        bmesh.ops.delete(bm, geom=loose, context="VERTS")
        bm.to_mesh(me)
    bm.free()
    me.update()

    m = ob.modifiers.new("Subdivision", "SUBSURF")
    m.levels = SUBD
    m.render_levels = SUBD
    m.use_creases = True
    m.boundary_smooth = "PRESERVE_CORNERS"
    bpy.context.view_layer.update()
    deps = bpy.context.evaluated_depsgraph_get()
    baked = bpy.data.meshes.new_from_object(ob.evaluated_get(deps))
    ob.modifiers.clear()
    old = ob.data
    ob.data = baked
    baked.name = P + "SkinMesh"
    if old.users == 0:
        bpy.data.meshes.remove(old)
    C.shade_auto_smooth(ob, 46.0)
    return ob


# --------------------------------------------------------------------------- #
# quarter-turn fasteners
# --------------------------------------------------------------------------- #

FAST_R_OUT = 0.0093
FAST_R_REC = 0.0086
FAST_R_FLR = 0.0066
FAST_R_HEAD = 0.0060
FAST_SEG = 28


def _fastener(px, u, roll, verts, faces, fmat):
    p, n, tu, _tx = _frame(px, u)
    e1 = tu.normalized()
    e2 = n.cross(e1).normalized()
    ca, sa = math.cos(roll), math.sin(roll)
    a1 = e1 * ca + e2 * sa
    a2 = -e1 * sa + e2 * ca

    def circle(r, dz):
        out = []
        for i in range(FAST_SEG):
            t = C.TAU * i / FAST_SEG
            out.append(p + a1 * (r * math.cos(t)) + a2 * (r * math.sin(t)) + n * dz)
        return out

    def slot(hl, hw, dz, nexp=5.0):
        out = []
        for i in range(FAST_SEG):
            t = C.TAU * i / FAST_SEG
            ct, st = math.cos(t), math.sin(t)
            e = 2.0 / nexp
            y = hl * math.copysign(abs(ct) ** e, ct)
            z = hw * math.copysign(abs(st) ** e, st)
            out.append(p + a1 * y + a2 * z + n * dz)
        return out

    rings = [circle(FAST_R_OUT, -0.0020),
             circle(FAST_R_OUT, 0.00030),
             circle(FAST_R_REC, -0.00090),
             circle(FAST_R_FLR, -0.00100),
             circle(FAST_R_HEAD, -0.00042),
             slot(0.0053, 0.00105, -0.00042),
             slot(0.0046, 0.00078, -0.00170)]
    band_mat = (1, 1, 1, 0, 0, 1)
    base = len(verts)
    for ring in rings:
        for q in ring:
            verts.append((q.x, q.y, q.z))
    n_ = FAST_SEG
    for r in range(len(rings) - 1):
        a, b = base + r * n_, base + (r + 1) * n_
        for k in range(n_):
            k2 = (k + 1) % n_
            faces.append((a + k, a + k2, b + k2, b + k))
            fmat.append(band_mat[r])
    faces.append(tuple(range(base, base + n_))[::-1])
    fmat.append(1)
    last = base + (len(rings) - 1) * n_
    faces.append(tuple(range(last, last + n_)))
    fmat.append(1)


def _frange(a, b, step):
    out = []
    v = a
    while v <= b + 1e-9:
        out.append(v)
        v += step
    return out


def _build_fasteners(coll):
    verts, faces, fmat = [], [], []
    rows = []
    # along transverse seams (u positions), offset onto the removable panel
    for xf, u0, u1, nu in ((1.6280, 0.16, 0.86, 7),
                           (0.8700, 0.32, 0.83, 6),
                           (-0.5820, 0.30, 0.84, 7),
                           (-1.4870, 0.26, 0.84, 6)):
        for i in range(nu):
            u = u0 + (u1 - u0) * i / (nu - 1)
            rows.append((xf, u, math.pi * 0.5))
    # along the sidepod upper seam
    g = LONG_SEAM["G1"]
    useam = (g["seg"] + g["f"]) / 7.0
    for x in _frange(-1.40, 0.80, 0.1625):
        rows.append((x, useam + 0.0185, 0.0))
    for xh in _frange(-1.045, -0.700, 0.0863):
        rows.append((xh, HATCH_U0 + 0.0135, 0.0))
        rows.append((xh, HATCH_U1 - 0.0135, 0.0))
    g2 = LONG_SEAM["G3"]
    u3 = (g2["seg"] + g2["f"]) / 7.0
    for x in _frange(-0.55, 0.86, 0.1760):
        rows.append((x, u3 - 0.0175, 0.0))

    for (x, u, roll) in rows:
        for sy in (1, -1):
            v0, f0 = len(verts), len(faces)
            _fastener(x, u, roll, verts, faces, fmat)
            if sy < 0:
                for k in range(v0, len(verts)):
                    vx, vy, vz = verts[k]
                    verts[k] = (vx, -vy, vz)
                for fi in range(f0, len(faces)):
                    faces[fi] = tuple(reversed(faces[fi]))

    ob = C.new_obj(P + "Fasteners", verts, faces, coll=coll, smooth=True)
    me = ob.data
    for k, idx in enumerate(fmat):
        if k < len(me.polygons):
            me.polygons[k].material_index = idx
    for nm in ("Titanium", "MatteBlack"):
        me.materials.append(S.mat(nm))
    C.shade_auto_smooth(ob, 24.0)
    return ob


# --------------------------------------------------------------------------- #

def build(coll, ctx=None):
    _ROWS.clear()
    _SCACHE.clear()
    objs = [_build_skin(coll)]
    objs.append(_build_fasteners(coll))
    return objs
