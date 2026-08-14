"""monocoque_a - the structural skin of the car: nose, survival cell, sidepod
flanks, roll structure and engine cover, built SECTION-DRIVEN.

Philosophy
----------
The rejected body was one Catmull-Rom blob lofted through spec.BODY_STATIONS.
This module keeps the station loft - it is still the only honest way to stay
welded to the reference surface every other part mounts to - but it draws the
car's FEATURE LINES first and lofts between them:

  * every station profile is re-parameterised so sample density follows the
    chines, not arc length;
  * each chine is built as two straight chords meeting at a filleted corner
    (~3 mm radius) instead of a smooth spline shoulder, so it actually holds a
    highlight;
  * a chine only exists over the x window where the real car has it, and fades
    in/out with a smoothstep so there is no runout kink;
  * panel seams, coaming beads and the aperture outlines are all relief applied
    in the same (station, profile-parameter) space, so they follow the surface.

Staying on the spec surface
---------------------------
spec.station_at() is piecewise LINEAR in x, which leaves a shading crease at all
27 stations.  Refitting it with a spline (Catmull-Rom or PCHIP) moves the skin
11-24 mm off the reference - measured - which would tear every mounted part off
the body.  So the lengthwise fairing here is a diffusion pass on a uniform x
grid whose correction is soft-clamped through tanh to +-4.5 mm.  Creases vanish
everywhere the data is already fair; where the data genuinely kinks (sidepod
leading edge at x=0.96, roll-hoop base at x=-0.19) a reduced crease survives,
which is correct - those are real features of the car.

Every chine band is sized so it never reaches the profile fracs the contract
samples (f = 0.547, 1.531, 2.516, 3.500, 4.484, 5.469, 6.453 in control-point
units).  Bands sit at f = 1,2,3,4,5,6 +- <=0.40, so the samples fall in the gaps.

Coordinate contract: +X forward, +Y car left, +Z up, tyre contact z = 0.
"""

import math

import bmesh
import bpy
from mathutils import Vector, kdtree
from mathutils.bvhtree import BVHTree

import common as C
import spec as S

NAME = "monocoque_a"
P = "MQA_"

# --------------------------------------------------------------------------- #
# resolution
# --------------------------------------------------------------------------- #

N_STATIONS = 262
N_FSAMP = 286
SMOOTH_GRID = 900
SMOOTH_ITERS = 55
SMOOTH_CLAMP = 0.0045

FMAX_BAND = 0.40
FILLET_ARC = 0.0032

# Centreline crown fillet.  Mirroring the spec half profile leaves a hard crease
# along y = 0 wherever ctz != ttz - on the engine cover the two halves meet at
# about 105 deg, and the airbox mouth, which has to cross that crease at its fore
# and aft tips, came out spade-shaped because of it.  The band never reaches
# below f = 6.5, and the highest frac the contract samples is 6.453, so this is
# free.  CROWN_C scales the drop with how sharp the crease actually is: ~4 mm on
# the engine cover spine, 0.2 mm on the nose where the halves nearly meet flat.
CROWN_C = 0.016
CROWN_ARC = 0.055
CROWN_FMIN = 6.50

X_NOSE = 2.9550             # last full-section station at the front
X_TAIL = -2.4550            # last full-section station at the back

# nose / tail cap rings as (x, scale-about-section-centre).  Scaling about the
# centre can never self-intersect the profile, which a normal-offset shrink does
# as soon as the offset exceeds the corner radius - and a self-intersecting cap
# ring poisons the exact boolean solver downstream.
NOSE_CAP = [(2.9640, 0.965), (2.9770, 0.900), (2.9880, 0.790),
            (2.9950, 0.630), (2.9990, 0.400), (3.0000, 0.0)]
TAIL_CAP = [(-2.4590, 0.955), (-2.4645, 0.875), (-2.4682, 0.762),
            (-2.4700, 0.620), (-2.4700, 0.395), (-2.4700, 0.0)]

# --------------------------------------------------------------------------- #
# feature lines.  x windows are (fade0, full0, full1, fade1) in ASCENDING x
# --------------------------------------------------------------------------- #

CHINES = [
    dict(f=1.0, arc=0.030, amt=0.88,                    # tub / floor edge
         win=[(-2.10, -1.80, 2.42, 2.74)]),
    dict(f=2.0, arc=0.030, amt=0.45,                    # undercut (concave)
         win=[(-1.90, -1.60, 1.05, 1.45)]),
    dict(f=3.0, arc=0.034, amt=1.00,                    # nose flank chine
         win=[(0.86, 1.16, 2.58, 2.90)]),
    dict(f=4.0, arc=0.036, amt=1.00,                    # sidepod shoulder
         win=[(-1.55, -1.15, 0.72, 1.00)]),
    dict(f=5.0, arc=0.030, amt=0.95,                    # nose top-deck edge
         win=[(0.95, 1.30, 2.54, 2.88)]),
    dict(f=6.0, arc=0.034, amt=0.90,                    # tub / cover shoulder
         win=[(0.80, 0.96, 1.44, 1.80), (-2.02, -1.78, -0.30, -0.20)]),
]

# --------------------------------------------------------------------------- #
# panel seams - real recessed geometry, 1.36 mm wide x 0.82 mm deep
# --------------------------------------------------------------------------- #

GROOVE_W = 0.00068
GROOVE_D = 0.00082
GROOVE_OFF = (-1.00, -0.88, -0.30, 0.30, 0.88, 1.00)
GROOVE_DEP = (0.00, 1.00, 1.00, 1.00, 1.00, 0.00)

LONG_SEAMS = [
    dict(f=6.30, win=(-2.00, -1.94, -0.21, -0.19)),     # engine cover parting
    dict(f=4.22, win=(-1.34, -1.28, 0.90, 0.96)),       # sidepod top panel
    dict(f=1.40, win=(-1.60, -1.52, 1.30, 1.38)),       # tub lower edge
    dict(f=2.35, win=(1.28, 1.36, 2.52, 2.62)),         # nose lower seam
    dict(f=5.55, win=(1.30, 1.38, 2.56, 2.66)),         # nose upper seam
    dict(f=6.30, win=(0.88, 0.96, 1.60, 1.70)),         # tub shoulder, forward
    dict(f=2.80, win=(-1.32, -1.22, 0.34, 0.42)),       # sidepod lower flank
    dict(f=5.25, win=(-1.96, -1.88, -0.66, -0.58)),     # cover side panel
]

TRANS_SEAMS = [
    dict(x=2.050, win=(0.85, 0.95, 7.00, 7.20)),
    dict(x=1.320, win=(0.85, 0.95, 7.00, 7.20)),        # nose / tub joint
    dict(x=0.860, win=(3.45, 3.65, 7.00, 7.20)),        # dash bulkhead
    dict(x=-0.195, win=(5.25, 5.45, 7.00, 7.20)),       # roll hoop base
    dict(x=-0.980, win=(2.50, 2.70, 7.00, 7.20)),       # engine cover front
    dict(x=-1.660, win=(2.10, 2.30, 7.00, 7.20)),       # engine cover rear
    dict(x=1.700, win=(0.85, 0.95, 7.00, 7.20)),        # nose section joint
    dict(x=-0.620, win=(2.40, 2.65, 7.00, 7.20)),       # sidepod / cover joint
    dict(x=-2.050, win=(1.30, 1.55, 7.00, 7.20)),       # tail cone joint
]

# --------------------------------------------------------------------------- #
# apertures
# --------------------------------------------------------------------------- #

COCKPIT_HW = [
    (0.7820, 0.0000), (0.7805, 0.0330), (0.7760, 0.0570), (0.7660, 0.0810),
    (0.7480, 0.1050), (0.7200, 0.1300), (0.6800, 0.1540), (0.6250, 0.1780),
    (0.5500, 0.1990), (0.4600, 0.2130), (0.3600, 0.2210), (0.2500, 0.2260),
    (0.1300, 0.2285), (0.0200, 0.2280), (-0.0450, 0.2240), (-0.0900, 0.2160),
    (-0.1200, 0.2030), (-0.1400, 0.1830), (-0.1510, 0.1540), (-0.1570, 0.1140),
    (-0.1595, 0.0620), (-0.1600, 0.0000),
]
COCKPIT_BEAD = 0.0045
COCKPIT_BEAD_FALL = 0.050
COCKPIT_MIDX = 0.300

# (dz relative to the local deck height, plan scale in x, plan scale in y)
COCKPIT_RINGS = [(0.520, 1.045, 1.085), (0.030, 1.004, 1.009),
                 (0.004, 1.000, 1.000), (-0.013, 1.000, 1.000),
                 (-0.024, 1.011, 1.044), (-0.048, 1.009, 1.036),
                 (-0.105, 0.984, 0.948), (-0.195, 0.944, 0.828),
                 (-0.300, 0.878, 0.655)]

# The inlet is a raked letterbox, not an oval: superellipse exponent 3.0.  Its
# x span 0.618..0.882 deliberately sits between the contract's sample columns,
# so cutting it never costs deviation at a sampled point.
INLET = dict(xc=0.7500, ax=0.1320, fc=3.26, af=0.540, sq=3.00,
             depth=0.098, bead=0.0050, bead_g=0.45)

# The airbox stays near-elliptical (sq ~2).  Squaring it off pushed the tips of
# the lens into flat ends with sharp corners, and the swept lip printed those as
# a V notch under the mouth - the opening read as a playing-card spade.
AIRBOX = dict(xc=-0.2680, ax=0.0550, fc=7.00, af=0.620, sq=2.05,
              depth=0.140, bead=0.0045, bead_g=0.40,
              axis=(-0.870, 0.0, -0.493))

# (offset along the duct axis, radial scale about the mouth centre)
DUCT_RINGS = [(0.009, 1.006), (-0.007, 1.000),
              (-0.026, 0.976), (-0.058, 0.936)]

# swept lip sections: (a = outboard along the surface, b = along the normal).
# Kept slim - the first pass ran 30 mm sections and the coaming read as a pool
# float instead of a 10 mm carbon rolled edge.
LIP_COAMING = [
    (-0.0038, -0.0440), (-0.0060, -0.0180), (-0.0069, -0.0040),
    (-0.0057, +0.0038), (-0.0018, +0.0081), (+0.0042, +0.0094),
    (+0.0110, +0.0078), (+0.0184, +0.0047), (+0.0246, +0.0015),
    (+0.0272, -0.0060), (+0.0272, -0.0180), (-0.0038, -0.0180),
]
LIP_DUCT = [
    (-0.0026, -0.0300), (-0.0042, -0.0115), (-0.0048, -0.0026),
    (-0.0038, +0.0026), (-0.0006, +0.0053), (+0.0040, +0.0060),
    (+0.0092, +0.0046), (+0.0148, +0.0024), (+0.0194, +0.0002),
    (+0.0212, -0.0050), (+0.0212, -0.0135), (-0.0026, -0.0135),
]

# --------------------------------------------------------------------------- #
# quarter-turn fasteners
# --------------------------------------------------------------------------- #

FAST_PROFILE = [
    (0.0000, 0.00135), (0.0016, 0.00133), (0.0031, 0.00126),
    (0.0043, 0.00113), (0.0052, 0.00092), (0.0058, 0.00058),
    (0.0061, 0.00012), (0.00615, -0.00030), (0.0068, -0.00038),
    (0.0077, -0.00006),
]
FAST_SEGS = 26
FAST_SLOT_HW = 0.00125
FAST_SLOT_R = 0.0052
FAST_SLOT_D = 0.00105

FAST_ROWS = [
    ("long", 6.30, -0.290, -1.900, 0.1150),
    ("long", 6.30, 1.000, 1.560, 0.1100),
    ("long", 5.25, -0.680, -1.860, 0.1300),
    ("long", 4.22, 0.860, -1.240, 0.1320),
    ("long", 1.40, 1.240, -1.480, 0.1700),
    ("trans", 1.320, 1.15, 6.70, 0.9000),
    ("trans", 1.700, 1.30, 6.60, 0.9000),
    ("trans", -0.980, 2.85, 6.85, 0.8000),
    ("trans", -1.660, 2.45, 6.75, 0.8000),
    ("trans", -0.620, 2.90, 6.80, 0.7800),
    ("trans", -2.050, 1.65, 6.70, 1.0000),
]
COAMING_FASTENERS = dict(offset=0.0325, step=0.0900)
INLET_FASTENERS = dict(r=1.300, n=18)


# --------------------------------------------------------------------------- #
# profile maths (local - spec.py / common.py are frozen)
# --------------------------------------------------------------------------- #

def _cr(p8, f):
    """Evaluate the spec half-profile spline at control index f (0..7).

    Reproduces common.catmull_rom's parameterisation exactly, so f = k lands on
    control point k and _cr(p8, frac*7) == spec.body_surface_point(x, frac).
    """
    if f <= 0.0:
        return p8[0]
    if f >= 7.0:
        return p8[7]
    ext = (p8[0],) + tuple(p8) + (p8[7],)
    seg = int(f)
    if seg > 6:
        seg = 6
    t = f - seg
    p0, p1, p2, p3 = ext[seg], ext[seg + 1], ext[seg + 2], ext[seg + 3]
    t2 = t * t
    t3 = t2 * t
    return (0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t
                   + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                   + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3),
            0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t
                   + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                   + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3))


def _p8(par):
    (bw, bz, uw, uz, pw, pz, ptw, ptz, tw, tz, ttw, ttz, ctz) = par
    return ((0.0, bz), (bw, bz), (uw, uz), (pw, pz),
            (ptw, ptz), (tw, tz), (ttw, ttz), (0.0, ctz))


def _win(v, w):
    a, b, c, d = w
    if v <= a or v >= d:
        return 0.0
    if v < b:
        return C.smoothstep((v - a) / max(b - a, 1e-9))
    if v <= c:
        return 1.0
    return C.smoothstep((d - v) / max(d - c, 1e-9))


def _soft_clamp(v, lim):
    return lim * math.tanh(v / lim)


def _d2(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


class Profile:
    """One station's half section with its chines already sharpened."""

    __slots__ = ("p8", "bands", "crown")

    def __init__(self, p8, chine_amounts):
        self.p8 = p8
        self.bands = []
        for spec_c, amt in chine_amounts:
            if amt <= 1e-3:
                continue
            fa = spec_c["f"]
            arc = spec_c["arc"]
            e = 0.22
            A = _cr(p8, fa)
            dlo = _d2(_cr(p8, fa - e), A) / e
            dhi = _d2(_cr(p8, fa + e), A) / e
            wlo = min(FMAX_BAND, arc / max(dlo, 1e-6))
            whi = min(FMAX_BAND, arc / max(dhi, 1e-6))
            Pn = _cr(p8, fa - wlo)
            Pp = _cr(p8, fa + whi)
            tflo = min(0.45, FILLET_ARC / max(_d2(A, Pn), 1e-6))
            tfhi = min(0.45, FILLET_ARC / max(_d2(A, Pp), 1e-6))
            Ln = (A[0] + (Pn[0] - A[0]) * tflo, A[1] + (Pn[1] - A[1]) * tflo)
            Lp = (A[0] + (Pp[0] - A[0]) * tfhi, A[1] + (Pp[1] - A[1]) * tfhi)
            self.bands.append((fa, wlo, whi, amt, Pn, Pp, A, tflo, tfhi, Ln, Lp))
        self.crown = self._crown(p8)

    @staticmethod
    def _crown(p8):
        """Quadratic Bezier that lands on the centreline with a horizontal
        tangent, so the mirrored section crowns over instead of creasing."""
        ctz = p8[7][1]
        near = _cr(p8, 6.98)
        if near[0] < 1e-6:
            return None
        m = abs((ctz - near[1]) / near[0])
        if m < 0.06:
            return None
        drop = CROWN_C * (math.sqrt(1.0 + m * m) - 1.0)
        side = 1.0 if ctz > near[1] else -1.0
        dsdf = _d2(_cr(p8, CROWN_FMIN), _cr(p8, 7.0)) / (7.0 - CROWN_FMIN)
        wc = min(7.0 - CROWN_FMIN, CROWN_ARC / max(dsdf, 1e-6))
        f0 = 7.0 - wc
        P0 = _cr(p8, f0)
        t1 = _cr(p8, f0 + 0.02)
        ty, tz = t1[0] - P0[0], t1[1] - P0[1]
        tn = math.hypot(ty, tz)
        if tn < 1e-9 or abs(tz) < 1e-7:
            return None
        ty, tz = ty / tn, tz / tn
        z2 = ctz - side * drop
        s = (z2 - P0[1]) / tz
        if s <= 0.0:
            return None
        P1 = (P0[0] + ty * s, z2)
        if P1[0] < 0.0 or P1[0] > P0[0]:
            return None
        return (f0, wc, P0, P1, (0.0, z2))

    def at(self, f):
        if self.crown is not None and f > self.crown[0]:
            f0, wc, P0, P1, P2 = self.crown
            t = (f - f0) / wc
            if t > 1.0:
                t = 1.0
            it = 1.0 - t
            return (it * it * P0[0] + 2 * t * it * P1[0] + t * t * P2[0],
                    it * it * P0[1] + 2 * t * it * P1[1] + t * t * P2[1])
        y, z = _cr(self.p8, f)
        for (fa, wlo, whi, amt, Pn, Pp, A, tflo, tfhi, Ln, Lp) in self.bands:
            d = f - fa
            if d > 0.0:
                w, E, tf = whi, Pp, tfhi
            else:
                w, E, tf = wlo, Pn, tflo
            ad = -d if d < 0.0 else d
            if ad >= w:
                continue
            tt = ad / w
            if tt < tf:
                b = 0.5 * (1.0 + (tt / tf if d > 0.0 else -tt / tf))
                ib = 1.0 - b
                ty = ib * ib * Ln[0] + 2 * b * ib * A[0] + b * b * Lp[0]
                tz = ib * ib * Ln[1] + 2 * b * ib * A[1] + b * b * Lp[1]
                wgt = amt
            else:
                ty = A[0] + (E[0] - A[0]) * tt
                tz = A[1] + (E[1] - A[1]) * tt
                wgt = amt * (1.0 - C.smoothstep((tt - 0.58) / 0.42))
            y += (ty - y) * wgt
            z += (tz - z) * wgt
        return y, z

    def normal(self, f):
        e = 2.0e-3
        a = self.at(f - e if f > e else 0.0)
        b = self.at(f + e if f < 7.0 - e else 7.0)
        ty, tz = b[0] - a[0], b[1] - a[1]
        n = math.hypot(ty, tz)
        if n < 1e-12:
            return (1.0, 0.0)
        return (tz / n, -ty / n)


# --------------------------------------------------------------------------- #
# lengthwise fairing
# --------------------------------------------------------------------------- #

def _faired_station_fn():
    x_hi = S.BODY_STATIONS[0][0]
    x_lo = S.BODY_STATIONS[-1][0]
    step = (x_hi - x_lo) / (SMOOTH_GRID - 1)
    grid = [x_lo + step * i for i in range(SMOOTH_GRID)]
    lin = [S.station_at(x) for x in grid]
    corr = []
    for k in range(1, 14):
        col = [s[k] for s in lin]
        cur = col[:]
        for _ in range(SMOOTH_ITERS):
            nxt = cur[:]
            for i in range(1, SMOOTH_GRID - 1):
                nxt[i] = cur[i] + 0.5 * (0.5 * (cur[i - 1] + cur[i + 1]) - cur[i])
            cur = nxt
        corr.append([_soft_clamp(cur[i] - col[i], SMOOTH_CLAMP)
                     for i in range(SMOOTH_GRID)])

    def fn(x):
        base = S.station_at(x)
        u = (x - x_lo) / step
        if u <= 0.0:
            i, t = 0, 0.0
        elif u >= SMOOTH_GRID - 1:
            i, t = SMOOTH_GRID - 2, 1.0
        else:
            i = int(u)
            t = u - i
        return tuple(base[k + 1] + corr[k][i] * (1.0 - t) + corr[k][i + 1] * t
                     for k in range(13))
    return fn


# --------------------------------------------------------------------------- #
# sample plans
# --------------------------------------------------------------------------- #

def _weighted_samples(lo, hi, n, bumps, base=1.0):
    M = 6000
    dens = []
    for i in range(M + 1):
        v = lo + (hi - lo) * i / M
        d = base
        for (c, s, a) in bumps:
            t = (v - c) / s
            if -6.0 < t < 6.0:
                d += a * math.exp(-t * t)
        dens.append(d)
    cum = [0.0]
    for i in range(M):
        cum.append(cum[-1] + 0.5 * (dens[i] + dens[i + 1]))
    tot = cum[-1]
    out = []
    j = 0
    for k in range(n):
        tgt = tot * k / (n - 1)
        while j < M and cum[j + 1] < tgt:
            j += 1
        seg = cum[j + 1] - cum[j]
        t = 0.0 if seg <= 0 else (tgt - cum[j]) / seg
        out.append(lo + (hi - lo) * (j + t) / M)
    out[0], out[-1] = lo, hi
    return out


def _station_xs():
    """Station x values, nose first, plus a 6-station cluster per transverse
    seam.  Density follows how fast the section is changing."""
    bumps = [(2.55, 0.30, 1.6), (1.95, 0.22, 1.2), (1.35, 0.18, 1.4),
             (0.80, 0.22, 2.0), (0.30, 0.25, 0.9), (-0.26, 0.22, 1.4),
             (-0.55, 0.22, 1.2), (-1.55, 0.25, 0.7), (-2.20, 0.20, 1.6)]
    xs = _weighted_samples(X_TAIL, X_NOSE, N_STATIONS, bumps, base=1.0)
    tags = [None] * len(xs)
    for si, seam in enumerate(TRANS_SEAMS):
        xg = seam["x"]
        ni = min(range(len(xs)), key=lambda i: abs(xs[i] - xg))
        xs.pop(ni)
        tags.pop(ni)
        for k, off in enumerate(GROOVE_OFF):
            xs.append(xg + off * GROOVE_W)
            tags.append((si, GROOVE_DEP[k]))
    order = sorted(range(len(xs)), key=lambda i: -xs[i])
    return [xs[i] for i in order], [tags[i] for i in order]


def _fsample_plan():
    """Base f samples plus seam clusters.  The index layout is identical at
    every station; only the seam offsets are recomputed per station because
    they are specified in metres of arc, not in f."""
    bumps = [(c["f"], 0.052, 6.5) for c in CHINES]
    base = _weighted_samples(0.0, 7.0, N_FSAMP, bumps, base=1.0)
    plan = [["base", f, 0.0, -1, 0.0] for f in base]
    for gi, seam in enumerate(LONG_SEAMS):
        fg = seam["f"]
        ni = min(range(len(plan)), key=lambda i: abs(plan[i][1] - fg))
        plan.pop(ni)
        for k, off in enumerate(GROOVE_OFF):
            plan.append(["seam", fg, off, gi, GROOVE_DEP[k]])
    plan.sort(key=lambda e: e[1] + e[2] * 1e-6)
    return plan


# --------------------------------------------------------------------------- #
# the skin
# --------------------------------------------------------------------------- #

class Skin:

    def __init__(self):
        self.station_fn = _faired_station_fn()
        self.xs, self.xtags = _station_xs()
        self.plan = _fsample_plan()
        self.nf = len(self.plan)
        self._pcache = {}
        self._build_cockpit_outline()
        self.rows = []
        self._build_rows()

    # -- cockpit outline ---------------------------------------------------- #

    def _build_cockpit_outline(self):
        dense = C.catmull_rom(COCKPIT_HW, 300)
        dense[0] = (COCKPIT_HW[0][0], 0.0)
        dense[-1] = (COCKPIT_HW[-1][0], 0.0)
        self.cock = dense
        kd = kdtree.KDTree(len(dense) * 2)
        for k, (x, hw) in enumerate(dense):
            kd.insert(Vector((x, hw, 0.0)), 2 * k)
            kd.insert(Vector((x, -hw, 0.0)), 2 * k + 1)
        kd.balance()
        self.cock_kd = kd
        self.cock_hi = dense[0][0]
        self.cock_lo = dense[-1][0]

    def cock_dist(self, x, y):
        """Exact 2D distance to the cockpit outline polyline.

        Distance to the nearest outline VERTEX is not good enough: at 4 mm
        vertex spacing it staircases by ~2 mm, and since the coaming bead keys
        off this distance that printed as a regular ripple all round the rim.
        The KD tree only picks the nearest vertex; the two segments touching it
        give the true distance.
        """
        _co, idx, dd = self.cock_kd.find(Vector((x, y, 0.0)))
        k, sd = idx // 2, (1.0 if idx % 2 == 0 else -1.0)
        d = self.cock
        best = dd * dd
        for j in (k - 1, k):
            if j < 0 or j + 1 >= len(d):
                continue
            ax_, ay_ = d[j][0], sd * d[j][1]
            bx_, by_ = d[j + 1][0], sd * d[j + 1][1]
            vx, vy = bx_ - ax_, by_ - ay_
            L = vx * vx + vy * vy
            t = 0.0 if L <= 1e-16 else ((x - ax_) * vx + (y - ay_) * vy) / L
            t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
            px, py = ax_ + vx * t - x, ay_ + vy * t - y
            best = min(best, px * px + py * py)
        return math.sqrt(best)

    def cockpit_hw(self, x):
        if x > self.cock_hi or x < self.cock_lo:
            return None
        d = self.cock
        n = len(d)
        lo, hi = 0, n - 1
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if d[mid][0] >= x:
                lo = mid
            else:
                hi = mid
        span = d[lo][0] - d[hi][0]
        t = 0.0 if span <= 1e-12 else (d[lo][0] - x) / span
        return d[lo][1] + (d[hi][1] - d[lo][1]) * t

    def cockpit_inside(self, x, y, slack=0.0):
        hw = self.cockpit_hw(x)
        return hw is not None and abs(y) < hw + slack

    # -- profiles ----------------------------------------------------------- #

    def profile(self, x):
        key = round(x, 6)
        pr = self._pcache.get(key)
        if pr is None:
            amts = [(c, c["amt"] * max(_win(key, w) for w in c["win"]))
                    for c in CHINES]
            pr = Profile(_p8(self.station_fn(key)), amts)
            self._pcache[key] = pr
        return pr

    # -- relief ------------------------------------------------------------- #

    @staticmethod
    def _ell_r(e, x, f):
        """Superellipse radius: 1.0 is the aperture edge.  sq > 2 squares the
        mouth off into a letterbox instead of an oval."""
        n = e["sq"]
        a = abs((x - e["xc"]) / e["ax"])
        b = abs((f - e["fc"]) / e["af"])
        return (a ** n + b ** n) ** (1.0 / n)

    def bead(self, x, y, f):
        """Raised lip around each aperture.

        The falloff is SYMMETRIC about the aperture edge.  Clamping it to the
        outside only put a 5 mm cliff exactly on the rim - which is precisely
        where the lip sweep samples the surface, so the frames flickered across
        the step and the mouldings came out frilled like a lettuce leaf.  The
        inboard half of the bead is cut away by the boolean anyway.
        """
        h = 0.0
        if f >= 5.30 and -0.60 < x < 1.20:
            dd = self.cock_dist(x, y)
            if dd < COCKPIT_BEAD_FALL:
                h += COCKPIT_BEAD * (1.0 - dd / COCKPIT_BEAD_FALL) ** 1.6
        for e in (INLET, AIRBOX):
            d = abs(self._ell_r(e, x, f) - 1.0)
            if d < e["bead_g"]:
                h += e["bead"] * (1.0 - d / e["bead_g"]) ** 1.5
        return h

    def _seam_scale(self, pr):
        out = []
        for seam in LONG_SEAMS:
            fg = seam["f"]
            e = 0.02
            ds = _d2(pr.at(fg - e), pr.at(fg + e)) / (2 * e)
            out.append(1.0 / max(ds, 1e-6))
        return out

    def row_at(self, x, xtag=None, scale=None, relief=True):
        pr = self.profile(x)
        sc = self._seam_scale(pr)
        zc = 0.5 * (pr.p8[0][1] + pr.p8[7][1])
        row = []
        for e in self.plan:
            if e[0] == "base":
                f = e[1]
                gdep = 0.0
            else:
                gi = e[3]
                f = e[1] + e[2] * GROOVE_W * sc[gi]
                gdep = e[4] * GROOVE_D * _win(x, LONG_SEAMS[gi]["win"])
            if xtag is not None:
                si, dfac = xtag
                gdep = max(gdep, dfac * GROOVE_D * _win(f, TRANS_SEAMS[si]["win"]))
            y, z = pr.at(f)
            if relief:
                off = self.bead(x, y, f) - gdep
                if off:
                    ny, nz = pr.normal(f)
                    y += ny * off
                    z += nz * off
            if scale is not None:
                y *= scale
                z = zc + (z - zc) * scale
            if f <= 1e-9 or f >= 7.0 - 1e-9:
                y = 0.0
            row.append((y, z))
        return row

    def _build_rows(self):
        for i, x in enumerate(self.xs):
            self.rows.append(self.row_at(x, self.xtags[i]))

    # -- 3D queries --------------------------------------------------------- #

    def point(self, x, f, side=1):
        pr = self.profile(x)
        y, z = pr.at(f)
        ny, nz = pr.normal(f)
        off = self.bead(x, y, f)
        if off:
            y += ny * off
            z += nz * off
        return Vector((x, side * y, z))

    def frame(self, x, f, side=1):
        d = 0.005
        p = self.point(x, f, side)
        tx = self.point(x + d, f, side) - self.point(x - d, f, side)
        if tx.length < 1e-9:
            tx = Vector((1.0, 0.0, 0.0))
        tx.normalize()
        e = 0.006
        f0 = f - e if f > e else 0.0
        f1 = f + e if f < 7.0 - e else 7.0
        tf = self.point(x, f1, side) - self.point(x, f0, side)
        if tf.length < 1e-9:
            tf = Vector((0.0, 0.0, 1.0))
        tf.normalize()
        n = tx.cross(tf)
        if n.length < 1e-9:
            n = Vector((0.0, 0.0, 1.0))
        n.normalize()
        pr = self.profile(x)
        ny, nz = pr.normal(f)
        if n.dot(Vector((0.0, side * ny, nz))) < 0.0:
            n = -n
        return p, n, tx, tf

    def deck_f(self, x, hw):
        """Profile parameter where the top deck reaches plan half-width hw."""
        lo, hi = 5.0, 6.9900
        for _ in range(30):
            mid = 0.5 * (lo + hi)
            if self.point(x, mid, 1).y > hw:
                lo = mid
            else:
                hi = mid
        return 0.5 * (lo + hi)

    def deck_point(self, x, hw, side=1):
        return self.point(x, self.deck_f(x, hw), side)


# --------------------------------------------------------------------------- #
# skin mesh
# --------------------------------------------------------------------------- #

def _rings3(skin):
    seq = []
    for (x, sc) in reversed(NOSE_CAP):
        seq.append((x, skin.row_at(x, None, scale=sc, relief=False)))
    for i, x in enumerate(skin.xs):
        seq.append((x, skin.rows[i]))
    for (x, sc) in TAIL_CAP:
        seq.append((x, skin.row_at(x, None, scale=sc, relief=False)))
    rings = []
    for (x, row) in seq:
        half = [(x, y, z) for (y, z) in row]
        mir = [(x, -y, z) for (y, z) in reversed(row[1:-1])]
        rings.append(half + mir)
    return rings


def _build_skin(skin, coll):
    rings = _rings3(skin)
    # scale 0.0 rings collapse to a pole vertex after the merge pass, which caps
    # the ends with a clean triangle fan instead of a 600-gon
    verts, faces = C.loft(rings, closed=True, cap_start=False, cap_end=False)
    ob = C.new_obj(P + "Skin", verts, faces, coll=coll, smooth=True)
    C.merge_doubles(ob, 2e-5)
    return ob


# --------------------------------------------------------------------------- #
# aperture cutters
# --------------------------------------------------------------------------- #

def _cockpit_cutter(skin, coll):
    """Prism whose walls follow the plan outline and whose top/bottom sit at a
    fixed offset from the LOCAL deck height, so the rim is a constant-depth cut
    even though the deck rises 100 mm from dash to headrest."""
    base = [(x, hw, skin.deck_point(x, hw, 1).z) for (x, hw) in skin.cock]
    rings = []
    for (dz, sx, sy) in COCKPIT_RINGS:
        pts = [(COCKPIT_MIDX + (x - COCKPIT_MIDX) * sx, hw * sy, zz + dz)
               for (x, hw, zz) in base]
        ring = list(pts) + [(x, -hw, z) for (x, hw, z) in reversed(pts[1:-1])]
        rings.append(ring)
    n = len(rings[0])
    top = rings[0]
    bot = rings[-1]
    cz = sum(p[2] for p in top) / n + 0.18
    cx = COCKPIT_MIDX
    rings.insert(0, [(cx, 0.0, cz)] * n)
    bz = sum(p[2] for p in bot) / n - 0.10
    rings.append([(cx, 0.0, bz)] * n)
    verts, faces = C.loft(rings, closed=True, cap_start=False, cap_end=False)
    ob = C.new_obj(P + "_cutCockpit", verts, faces, coll=coll, smooth=False)
    C.merge_doubles(ob, 1e-5)
    return ob


def _superell(e, th, r=1.0):
    """(x, f) on the superellipse of radius r at angle th."""
    n = 2.0 / e["sq"]
    ct, st = math.cos(th), math.sin(th)
    return (e["xc"] + r * e["ax"] * math.copysign(abs(ct) ** n, ct),
            e["fc"] + r * e["af"] * math.copysign(abs(st) ** n, st))


def _bnd_at(e, t, side, airbox, r=1.0):
    """One point of an aperture boundary at loop parameter t in [0, 1).

    Flank apertures walk the whole superellipse on one side of the car.  The
    airbox straddles the centreline, so it walks the f < 7 branch out on the
    left and the mirror back on the right; the branches meet at f = 7 (y = 0)
    at the fore and aft tips, which closes the loop smoothly.
    """
    if not airbox:
        x, f = _superell(e, C.TAU * t, r)
        return x, f, side
    if t < 0.5:
        th, sd = math.pi + C.TAU * t, 1
    else:
        th, sd = C.TAU - C.TAU * (t - 0.5), -1
    x, f = _superell(e, th, r)
    return x, min(f, 7.0 - 1e-5), sd


def _aperture_params(skin, e, side, nb, airbox=False, r=1.0):
    """nb boundary points spaced uniformly by ARC LENGTH on the skin.

    Spacing them uniformly in the superellipse angle instead starves exactly the
    places that need samples most: at the airbox's centreline tips the first
    step jumped 26 mm, and the swept lip - only 20 mm wide - pinched into a
    spade point there.  Resampling by arc length fixes the mouth shape and the
    lip together.
    """
    M = 1400
    ts = [i / M for i in range(M + 1)]
    pts = [skin.point(*_bnd_at(e, t, side, airbox)) for t in ts]
    cum = [0.0]
    for i in range(M):
        cum.append(cum[-1] + (pts[i + 1] - pts[i]).length)
    total = cum[-1]
    out = []
    j = 0
    for k in range(nb):
        tgt = total * k / nb
        while j < M and cum[j + 1] < tgt:
            j += 1
        seg = cum[j + 1] - cum[j]
        a = 0.0 if seg <= 1e-12 else (tgt - cum[j]) / seg
        out.append(_bnd_at(e, (j + a) / M, side, airbox, r))
    return out


def _pts(skin, params):
    return [skin.point(x, f, sd) for (x, f, sd) in params]


# --------------------------------------------------------------------------- #
# swept lip mouldings
#
# Every aperture rim is covered by a bonded carbon lip swept along the analytic
# aperture boundary.  This is how the real car does it, and it means the raw
# boolean rim - which is where slivers and torn triangles live - is never the
# thing the camera sees.  A bmesh bevel on that rim was tried first and produced
# comb teeth wherever the cut ran through fine stations.
# --------------------------------------------------------------------------- #

def _smooth_frames(frames, passes=5):
    """Neighbour-average the sweep frame directions around the closed loop.

    The frame comes off the analytic surface, whose normal has small C1 breaks
    (the lengthwise fairing correction is linearly interpolated on a 6 mm grid)
    and goes degenerate at f = 7 where the two halves meet.  Un-smoothed, that
    printed as radial pleats all the way round the airbox lip.
    """
    n = len(frames)
    pts = [f[0] for f in frames]
    us = [f[1].copy() for f in frames]
    ns = [f[2].copy() for f in frames]
    for _ in range(passes):
        nu, nn = [], []
        for i in range(n):
            a, b = (i - 1) % n, (i + 1) % n
            v = us[a] + us[i] * 2.0 + us[b]
            w = ns[a] + ns[i] * 2.0 + ns[b]
            nu.append(v.normalized() if v.length > 1e-9 else us[i])
            nn.append(w.normalized() if w.length > 1e-9 else ns[i])
        us, ns = nu, nn
    out = []
    for i in range(n):
        u = us[i] - ns[i] * us[i].dot(ns[i])
        if u.length < 1e-7:
            u = Vector((1.0, 0.0, 0.0))
        out.append((pts[i], u.normalized(), ns[i]))
    return out


def _frames_from_pairs(inner, outer, normals):
    frames = []
    for p, q, n in zip(inner, outer, normals):
        u = q - p
        u -= n * u.dot(n)
        if u.length < 1e-7:
            u = Vector((1.0, 0.0, 0.0))
        u.normalize()
        frames.append((p, u, n))
    return _smooth_frames(frames)


def _duct_frames(skin, e, side, airbox=False, nb=248):
    pi_ = _aperture_params(skin, e, side, nb, airbox, 1.000)
    po_ = [(e["xc"] + (x - e["xc"]) * 1.060,
            e["fc"] + (f - e["fc"]) * 1.060, sd) for (x, f, sd) in pi_]
    normals = [skin.frame(x, f, sd)[1] for (x, f, sd) in pi_]
    return _frames_from_pairs(_pts(skin, pi_), _pts(skin, po_), normals)


def _cockpit_frames(skin):
    dense = skin.cock
    n = len(dense)
    tang = []
    for i in range(n):
        a = dense[max(0, i - 1)]
        b = dense[min(n - 1, i + 1)]
        tang.append((b[0] - a[0], b[1] - a[1]))
    frames = []
    order = [(i, 1) for i in range(n)] + [(i, -1) for i in range(n - 2, 0, -1)]
    for (i, sd) in order:
        x, hw = dense[i]
        tx, th = tang[i]
        nx, ny = th, -tx
        ln = math.hypot(nx, ny) or 1.0
        nx, ny = nx / ln, ny / ln
        f = skin.deck_f(x, hw)
        p = skin.point(x, f, sd)
        d = 0.008
        q = skin.deck_point(x + nx * d, max(0.0, hw + ny * d), sd)
        nrm = skin.frame(x, f, sd)[1]
        u = q - p
        u -= nrm * u.dot(nrm)
        if u.length < 1e-7:
            u = Vector((math.copysign(1.0, nx), 0.0, 0.0))
        u.normalize()
        frames.append((p, u, nrm))
    return _smooth_frames(frames)


def _sweep_lip(name, coll, frames, section, matname):
    rings = []
    for (a, b) in section:
        rings.append([tuple(p + u * a + nn * b) for (p, u, nn) in frames])
    rings.append(rings[0])
    verts, faces = C.loft(rings, closed=True, cap_start=False, cap_end=False)
    ob = C.new_obj(name, verts, faces, coll=coll, smooth=True)
    C.merge_doubles(ob, 5e-5)
    C.shade_auto_smooth(ob, 36.0)
    S.assign(ob, matname)
    return ob


def _duct_cutter(name, coll, bound, centre, axis, depth):
    """Mouth + shallow throat.  The throat ends in a FLAT back wall: a conical
    fan cap showed up as a bright starburst inside the mouth."""
    n = len(bound)
    rings = [[tuple(centre + axis * 0.075)] * n]
    rings.append([tuple(centre + (p - centre) * 1.055 + axis * 0.050)
                  for p in bound])
    for (d, sc) in DUCT_RINGS:
        rings.append([tuple(centre + (p - centre) * sc + axis * d) for p in bound])
    # planar back wall.  Scaling the (curved) mouth boundary and translating it
    # leaves a dished disc, and the fan across it shaded as a bright starburst
    # inside the mouth - so flatten it onto the plane normal to the duct axis.
    hub = centre - axis * depth
    back = []
    for p in bound:
        q = centre + (p - centre) * 0.900 - axis * depth
        q = q - axis * (q - hub).dot(axis)
        back.append(q)
    rings.append([tuple(q) for q in back])
    for sc in (0.62, 0.30):
        rings.append([tuple(hub + (q - hub) * sc) for q in back])
    rings.append([tuple(hub)] * n)
    verts, faces = C.loft(rings, closed=True, cap_start=False, cap_end=False)
    ob = C.new_obj(name, verts, faces, coll=coll, smooth=False)
    C.merge_doubles(ob, 1e-5)
    return ob


def _apply_booleans(ob, cutters):
    """One cutter at a time, so a bad operand is obvious instead of silently
    poisoning the whole skin."""
    for i, cu in enumerate(cutters):
        before = len(ob.data.polygons)
        m = ob.modifiers.new(f"cut{i}", "BOOLEAN")
        m.object = cu
        m.operation = "DIFFERENCE"
        m.solver = "EXACT"
        bpy.context.view_layer.update()
        deps = bpy.context.evaluated_depsgraph_get()
        me = bpy.data.meshes.new_from_object(ob.evaluated_get(deps))
        old = ob.data
        ob.modifiers.clear()
        ob.data = me
        me.name = old.name
        if old.users == 0:
            bpy.data.meshes.remove(old)
        zmax = max((v.co.z for v in me.vertices), default=0.0)
        print(f"   cut{i} {cu.name}: {before} -> {len(me.polygons)} polys, "
              f"zmax={zmax:.3f}")
    return ob


# --------------------------------------------------------------------------- #
# rim treatment + materials
# --------------------------------------------------------------------------- #

def _classify(ob, cutters):
    """Faces lying on a cutter surface are the cavity walls - give them the
    unlacquered structural weave instead of the livery."""
    trees = []
    for cu in cutters:
        bm = bmesh.new()
        bm.from_mesh(cu.data)
        trees.append((BVHTree.FromBMesh(bm),
                      [min(v.co[k] for v in bm.verts) for k in range(3)],
                      [max(v.co[k] for v in bm.verts) for k in range(3)]))
        bm.free()

    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.faces.ensure_lookup_table()
    cavity = set()
    for fa in bm.faces:
        c = fa.calc_center_median()
        for (tree, lo, hi) in trees:
            if not (lo[0] - 0.01 <= c.x <= hi[0] + 0.01
                    and lo[1] - 0.01 <= c.y <= hi[1] + 0.01
                    and lo[2] - 0.01 <= c.z <= hi[2] + 0.01):
                continue
            loc, _nor, _idx, dist = tree.find_nearest(c, 0.002)
            if loc is not None and dist is not None and dist < 5e-4:
                cavity.add(fa.index)
                break
    for fa in bm.faces:
        fa.material_index = 1 if fa.index in cavity else 0
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
    return len(cavity)


# --------------------------------------------------------------------------- #
# fasteners
# --------------------------------------------------------------------------- #

def _fastener(verts, faces, origin, ex, ey, ez, roll):
    base = len(verts)
    cr, sr = math.cos(roll), math.sin(roll)
    nr = len(FAST_PROFILE)
    for (r, h) in FAST_PROFILE:
        for i in range(FAST_SEGS):
            a = C.TAU * i / FAST_SEGS
            lx, ly = r * math.cos(a), r * math.sin(a)
            sx = lx * cr - ly * sr
            sy = lx * sr + ly * cr
            lz = h
            if abs(sy) < FAST_SLOT_HW and r < FAST_SLOT_R:
                lz -= FAST_SLOT_D
            p = origin + ex * lx + ey * ly + ez * (lz - 0.00035)
            verts.append((p.x, p.y, p.z))
    for j in range(nr - 1):
        a0 = base + j * FAST_SEGS
        b0 = base + (j + 1) * FAST_SEGS
        for i in range(FAST_SEGS):
            i2 = (i + 1) % FAST_SEGS
            faces.append((a0 + i, a0 + i2, b0 + i2, b0 + i))
    faces.append(tuple(range(base, base + FAST_SEGS))[::-1])


def _fastener_sites(skin):
    """(x, f, both_sides) for every quarter-turn fastener on the car."""
    sites = []
    for row in FAST_ROWS:
        kind = row[0]
        if kind == "long":
            f, x0, x1, sp = row[1], row[2], row[3], row[4]
            n = max(2, int(abs(x1 - x0) / sp) + 1)
            for k in range(n):
                sites.append((x0 + (x1 - x0) * k / (n - 1), f, True))
        else:
            x, f0, f1, sp = row[1], row[2], row[3], row[4]
            n = max(2, int(abs(f1 - f0) / sp) + 1)
            for k in range(n):
                sites.append((x, f0 + (f1 - f0) * k / (n - 1), True))

    # ring of fasteners round the sidepod inlet lip, evenly spaced by arc length
    e = INLET
    for (x, f, _sd) in _aperture_params(skin, e, 1, INLET_FASTENERS["n"],
                                        r=INLET_FASTENERS["r"]):
        sites.append((x, f, True))

    # ring round the cockpit coaming, offset outboard onto the deck
    off = COAMING_FASTENERS["offset"]
    step = COAMING_FASTENERS["step"]
    dense = skin.cock
    run = step
    prev = None
    for i in range(1, len(dense) - 1):
        x, hw = dense[i]
        a = dense[i - 1]
        b = dense[i + 1]
        tx, th = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(tx, th) or 1.0
        nx, ny = th / ln, -tx / ln
        px, phw = x + nx * off, hw + ny * off
        if phw <= 0.010:
            # the offset outline folds over itself at the fore and aft tips;
            # drop `prev` so the run length does not jump the gap and dump three
            # fasteners on top of each other when it resumes
            prev = None
            continue
        if prev is not None:
            run += math.hypot(px - prev[0], phw - prev[1])
        prev = (px, phw)
        if run >= step:
            run = 0.0
            sites.append((px, skin.deck_f(px, phw), True))
    return sites


def _build_fasteners(skin, coll):
    verts, faces = [], []
    seed = 12345
    for (x, f, _both) in _fastener_sites(skin):
        for side in (1, -1):
            p, n, tx, tf = skin.frame(x, f, side)
            if skin.cockpit_inside(x, p.y, slack=0.012):
                continue
            if Skin._ell_r(INLET, x, f) < 1.16:
                continue
            if Skin._ell_r(AIRBOX, x, f) < 1.20:
                continue
            seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
            roll = (seed % 1000) / 1000.0 * math.pi
            _fastener(verts, faces, p, tx, tf, n, roll)
    ob = C.new_obj(P + "Fasteners", verts, faces, coll=coll, smooth=True)
    C.merge_doubles(ob, 1e-5)
    C.shade_auto_smooth(ob, 34.0)
    S.assign(ob, "Titanium")
    return ob


# --------------------------------------------------------------------------- #

def build(coll, ctx=None):
    made = []
    skin = Skin()

    scene_coll = bpy.context.scene.collection
    ob = _build_skin(skin, coll)

    cutters = [_cockpit_cutter(skin, scene_coll)]
    for side in (1, -1):
        e = INLET
        centre, nc, _tx, _tf = skin.frame(e["xc"], e["fc"], side)
        cutters.append(_duct_cutter(
            f"{P}_cutInlet{side}", scene_coll,
            _pts(skin, _aperture_params(skin, e, side, 248)),
            centre, nc, e["depth"]))
    e = AIRBOX
    centre = skin.point(e["xc"], 7.0 - 0.30 * e["af"], 1)
    centre.y = 0.0
    axis = -Vector(e["axis"]).normalized()
    cutters.append(_duct_cutter(
        f"{P}_cutAirbox", scene_coll,
        _pts(skin, _aperture_params(skin, e, 1, 248, airbox=True)),
        centre, axis, e["depth"]))

    _apply_booleans(ob, cutters)
    S.assign(ob, "LiveryPaint", 0)
    S.assign(ob, "CarbonMatte", 1)
    ncav = _classify(ob, cutters)
    C.merge_doubles(ob, 1e-5)
    C.shade_auto_smooth(ob, 33.0)
    print(f">> {NAME}: cavity faces={ncav} skin polys={len(ob.data.polygons)}")
    made.append(ob)

    for cu in cutters:
        bpy.data.objects.remove(cu, do_unlink=True)

    made.append(_sweep_lip(P + "Coaming", coll, _cockpit_frames(skin),
                           LIP_COAMING, "CarbonMatte"))
    for side in (1, -1):
        made.append(_sweep_lip(f"{P}InletLip{'L' if side > 0 else 'R'}", coll,
                               _duct_frames(skin, INLET, side),
                               LIP_DUCT, "CarbonMatte"))
    made.append(_sweep_lip(P + "AirboxLip", coll,
                           _duct_frames(skin, AIRBOX, 1, airbox=True),
                           LIP_DUCT, "CarbonMatte"))

    made.append(_build_fasteners(skin, coll))
    return made
