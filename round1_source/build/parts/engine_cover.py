"""engine_cover - the upper bodywork from behind the driver's head to the tail.

What this module owns
---------------------
Everything that sits ON the upper monocoque between x = +0.100 and x = -2.240:

    EC_shell        seven bolt-on skin panels with real 3.2 mm joints between
                    them, rolled 4.6 mm edges everywhere, apertures cut for the
                    airbox mouth and four louvre banks
    EC_seams        the bonded backing strips you see down every panel joint
    EC_bulkhead     the closing bulkhead behind the driver's headrest
    EC_hoop         principal roll structure: the surround band around the
                    airbox mouth, the crest fairing and its rear stays
    EC_tcam         onboard-camera pod on the roll-hoop crest
    EC_duct         airbox throat + vertical splitter + plenum, visible inside
    EC_fin          shark fin along the spine, x = -0.44 -> -2.10
    EC_pans         the sunken pans behind the four louvre banks
    EC_louvres      31 formed gill blades bridging those pans
    EC_tailduct     tail cooling-exit liner, heat-shield bulkhead, pipe struts
    EC_exhaust      72 mm titanium tailpipe seated in the tail cone
    EC_fixings      118 Dzus quarter-turn fasteners along the seams

Landing on the skin
-------------------
Nothing is guessed. The cover section at a station is built from
`spec.body_surface_point` samples between `frac_lo(x)` and the crown, then the
control polygon is MIRRORED about y = 0 before it is re-splined, which is what
kills the ridge the raw 7-point half profile leaves along the spine (its end
tangent is not horizontal, so a plain mirror would crease the crown).  Every
control point is then pushed 4.2 mm along its own 2-D surface normal - the
laminate thickness - so the cover sits ON the monocoque, never inside it.

`spec.station_at` is piecewise LINEAR in x, so it leaves a shading crease at all
27 station knots. Those are removed with a 15-tap Gaussian (sigma 30 mm) over
the CONTROL points, clamped so the smoothed section is never more than 4.8 mm
from the exact one; feature lines the data really has (the roll-hoop base)
survive, spurious creases do not.

Surface features are authored in (x, w) where w is arc length in METRES from
the crown along the section, so a 96 mm louvre bank is 96 mm on the skin at the
tail as well as at the roll hoop.  Aperture edges are exact, not stair-stepped:
grid nodes adjacent to a hole are Newton-projected onto the hole's own zero
level set before the surface is evaluated.

Coordinates: +X forward (nose x=+3.000), +Y car left, +Z up, contact plane z=0.
"""

import math

import bmesh
import bpy
from mathutils import Vector

import common as C
import spec as S

NAME = "engine_cover"
P = "EC_"

TAU = math.pi * 2.0

# --------------------------------------------------------------------------- #
# principal stations and panel breaks
# --------------------------------------------------------------------------- #

X_FWD = 0.100             # shoulder-rail front edge (beside the cockpit)
X_DECK_F = -0.176         # deck panel front edge (behind COCKPIT_REAR_X)
X_SEAM_M = -0.560         # mid transverse joint  (matches the livery break)
X_SEAM_T = -1.450         # cover / tail joint    (matches the livery break)
X_TAIL_E = -2.240         # cooling-exit lip

# D-EC03: H_PANEL has to exceed the fairing clamp, or at a station where the
# gaussian pulls the crown down by the full 4.8 mm the cover sinks INTO the
# monocoque.  Measured worst case was -0.6 mm at x = -0.259 (the roll-hoop
# knee).  Clamp tightened, laminate thickened; worst case is now +1.6 mm.
H_PANEL = 0.0058          # laminate proudness above the reference surface
T_SKIN = 0.0046           # panel thickness
GAP = 0.0032              # panel-to-panel joint
BACK_DROP = 0.0115        # backing strip below the outer skin

# airbox mouth (superellipse in (x, w), metres)
MO_XC, MO_XH = -0.2620, 0.0500
MO_WH, MO_N = 0.1240, 2.45
LIP_H = 0.0072            # raised intake lip at the mouth rim

# roll structure: the crest spine runs from behind the hoop band back to where
# the shark fin has grown tall enough to stand on its own.
X_CREST_F, X_CREST_R = -0.362, -0.665

# Shark fin.  D-EC22: the fin used to start at -0.400, i.e. inside the tall part
# of the crest fairing, and broke back OUT of it at a 4 deg angle over 80 mm -
# a knife-edged, torn-looking membrane at the roll hoop.  It now starts behind
# the camera pod and stands ON the crest (see _root_z), so the two surfaces
# always meet transversally.
X_FIN_F, X_FIN_R = -0.486, -2.100
FIN_BURY = 0.0060         # root skirt sunk into the skin, so it cannot float
FIN_FIL = 0.0115          # root cove radius
# How much horizontal run the skirt gets to make its FIN_BURY drop.  1.0 means
# 45 deg measured in relative height, which on a deck already falling at 36 deg
# is only a 24 deg geometric crossing - the root then renders as one soft bright
# bead with no edge in it, which is the symptom the fin-root defect described.
# 0.42 puts the runout at ~72 deg absolute, i.e. a 36 deg crossing.
FIN_RUNOUT = 0.42

# louvre banks: (xc, xh, from_seam, w_off, wh, n_super, n_blades)
# w_off is arc length in METRES, measured from the crown (from_seam = 0) or
# from the deck/shoulder joint (from_seam = 1).
BANKS = (
    (-0.9400, 0.1620, 1, 0.0950, 0.0440, 5.0, 7),   # bank A, shoulder panel
    (-1.7050, 0.1450, 0, 0.1250, 0.0400, 5.0, 7),   # bank B, tail panel
)
PLINTH_H = 0.0068
PLINTH_RAMP = 0.026
PAN_D = 0.0245

# tail
X_LINER_F = -1.9500
R_PIPE = 0.0360           # 72 mm tailpipe
T_PIPE = 0.0026
X_PIPE_TIP = -2.3350
Z_PIPE_TIP = 0.2460
# D-EC25: the pipe used to RISE towards the tail (0.238 -> 0.252), which drove
# its forward half straight through the cooling-duct floor - 2130 shared
# triangles, the floor 50 mm above the pipe bottom at x = -1.96 and a raw crease
# visible looking into the exit.  The duct floor is a chord between the cover's
# two lower edges and physically cannot be dropped below them, so the pipe is
# what has to move: it now falls aft the way a real exhaust does (turbine high,
# tailpipe low) and clears the floor by 8 mm at the bulkhead, 43 mm at the exit.
# Measured wall clearance all round the pipe afterwards: raising it too far left
# only 7.4 mm of duct above the pipe at the strut station and turned two of the
# three pipe struts into 8 mm stubs, so the whole pipe then came back down 6 mm.
Z_PIPE_FWD = 0.2960


def _key(x):
    return int(round(x * 100000.0))


# =========================================================================== #
# 1.  the reference surface
# =========================================================================== #

def _cr_point(p, t):
    """Catmull-Rom through control points `p` at continuous t in [0, 1].

    Same maths and parameterisation as common.catmull_rom, so evaluating
    S.station_half(S.station_at(x)) here reproduces S.body_surface_point(x, t)
    to within that function's 1/64 sampling quantisation.
    """
    pts = [p[0]] + list(p) + [p[-1]]
    segs = len(pts) - 3
    f = min(max(t, 0.0), 1.0) * segs
    seg = min(int(f), segs - 1)
    u = f - seg
    p0, p1, p2, p3 = pts[seg], pts[seg + 1], pts[seg + 2], pts[seg + 3]
    u2, u3 = u * u, u * u * u
    return (
        0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * u
               + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * u2
               + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * u3),
        0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * u
               + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * u2
               + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * u3),
    )


_SM_SIG = 0.030
_SM_CLAMP = 0.0042

# D-EC12: the fairing used to be a 15-tap gaussian evaluated at the query point,
# taps 10 mm apart.  S.station_at is piecewise LINEAR, so convolving it with a
# DISCRETE kernel gives a result that is still piecewise linear - with a slope
# break every 10 mm instead of every station.  That is invisible in silhouette
# and very visible in a specular reflection: the tail panel showed a regular
# transverse ripple.  The fairing is now done ONCE onto a uniform 3.5 mm table
# and read back with Catmull-Rom, so the surface is smooth between stations and
# only the genuine feature lines (roll-hoop knee) keep a crease.
_TAB_X0, _TAB_X1, _TAB_DX = 0.400, -2.520, 0.0035
_TAB_N = int(round((_TAB_X0 - _TAB_X1) / _TAB_DX)) + 1
_ctrl_tab = None


def _build_ctrl_tab():
    global _ctrl_tab
    exact = [S.station_half(S.station_at(_TAB_X0 - _TAB_DX * i))
             for i in range(_TAB_N)]
    sig = _SM_SIG / _TAB_DX
    rad = int(math.ceil(3.0 * sig))
    ker = [math.exp(-0.5 * (k / sig) ** 2) for k in range(-rad, rad + 1)]
    ks = sum(ker)
    ker = [v / ks for v in ker]
    out = []
    for i in range(_TAB_N):
        lo, hi = i - rad, i + rad
        pts = []
        for c in range(8):
            sy = sz = 0.0
            for j in range(lo, hi + 1):
                w = ker[j - lo]
                m = 0 if j < 0 else (_TAB_N - 1 if j >= _TAB_N else j)
                p = exact[m][c]
                sy += w * p[0]
                sz += w * p[1]
            ey, ez = exact[i][c]
            dy, dz = sy - ey, sz - ez
            d = math.hypot(dy, dz)
            if d > 1e-9:
                # smooth (tanh) clamp: a hard clamp puts a kink of its own at
                # the point where it starts to bind
                f = _SM_CLAMP * math.tanh(d / _SM_CLAMP) / d
                sy, sz = ey + dy * f, ez + dz * f
            pts.append((sy, sz))
        pts[0] = (0.0, pts[0][1])
        pts[7] = (0.0, pts[7][1])
        out.append(pts)
    _ctrl_tab = out


def _ctrl(x):
    """8-point half profile at x, read from the faired table with Catmull-Rom."""
    if _ctrl_tab is None:
        _build_ctrl_tab()
    t = (_TAB_X0 - x) / _TAB_DX
    t = min(max(t, 0.0), _TAB_N - 1.0)
    i = min(int(t), _TAB_N - 2)
    u = t - i
    i0 = max(i - 1, 0)
    i3 = min(i + 2, _TAB_N - 1)
    a, b, c, d = _ctrl_tab[i0], _ctrl_tab[i], _ctrl_tab[i + 1], _ctrl_tab[i3]
    u2, u3 = u * u, u * u * u
    out = []
    for k in range(8):
        row = []
        for j in (0, 1):
            p0, p1, p2, p3 = a[k][j], b[k][j], c[k][j], d[k][j]
            row.append(0.5 * ((2 * p1) + (-p0 + p2) * u
                              + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u2
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * u3))
        out.append((row[0], row[1]))
    out[0] = (0.0, out[0][1])
    out[7] = (0.0, out[7][1])
    return out


def _body(x, f):
    return _cr_point(_ctrl(x), f)


# --------------------------------------------------------------------------- #
# lower boundary of the cover, as a fraction of the body's half profile
# --------------------------------------------------------------------------- #

def _mk_table(pairs, n=520, passes=26):
    """Monotone-safe faired lookup: dense linear resample + binomial smoothing."""
    xs = [p[0] for p in pairs]
    x0, x1 = xs[0], xs[-1]
    vals = []
    for i in range(n):
        x = x0 + (x1 - x0) * i / (n - 1)
        for k in range(len(pairs) - 1):
            a, b = pairs[k], pairs[k + 1]
            if (a[0] - x) * (b[0] - x) <= 0.0 and a[0] != b[0]:
                t = (x - a[0]) / (b[0] - a[0])
                vals.append(C.lerp(a[1], b[1], t))
                break
        else:
            vals.append(pairs[-1][1] if abs(x - x1) < abs(x - x0) else pairs[0][1])
    for _ in range(passes):
        nv = list(vals)
        for i in range(1, n - 1):
            nv[i] = 0.25 * vals[i - 1] + 0.5 * vals[i] + 0.25 * vals[i + 1]
        vals = nv
    return (x0, x1, vals)


def _tab(tab, x):
    x0, x1, vals = tab
    n = len(vals)
    t = (x - x0) / (x1 - x0)
    t = min(max(t, 0.0), 1.0) * (n - 1)
    i = min(int(t), n - 2)
    return C.lerp(vals[i], vals[i + 1], t - i)


_FLO = _mk_table([(0.300, 0.7250), (0.100, 0.7210), (-0.176, 0.7090),
                  (-0.400, 0.7020), (-0.800, 0.6900), (-1.200, 0.6640),
                  (-1.600, 0.6100), (-1.950, 0.4700), (-2.240, 0.3100),
                  (-2.400, 0.2900)])

# the longitudinal deck / shoulder joint is specified as a body half-profile
# FRACTION, so it tracks the tub-shoulder chine down the whole car instead of
# wandering off it wherever the section changes character.
_FSEAM = _mk_table([(0.300, 0.8880), (0.100, 0.8840), (-0.200, 0.8720),
                    (-0.560, 0.8580), (-1.000, 0.8500), (-1.450, 0.8400),
                    (-1.900, 0.8150), (-2.400, 0.7900)])


def _frac_lo(x):
    return _tab(_FLO, x)


_qs_cache = {}


def _qsplit(x):
    k = _key(x)
    got = _qs_cache.get(k)
    if got is None:
        got = _q_of_frac(x, _tab(_FSEAM, x))
        _qs_cache[k] = got
    return got


# =========================================================================== #
# 2.  the cover's own section
# =========================================================================== #

_GS = (0.0, 0.155, 0.320, 0.500, 0.685, 0.855, 1.0)

_sec_cache = {}


def _cover_ctrl(x):
    """Symmetric 13-point control polygon for the cover section at x.

    Mirroring the half profile about y = 0 BEFORE re-splining is what makes the
    crown a smooth dome: the mirrored neighbours give the apex a horizontal
    tangent, where the raw spec half profile ends with dz/df = 0.07-0.14 and
    would leave a ridge down the whole spine.
    """
    k = _key(x)
    got = _sec_cache.get(k)
    if got is not None:
        return got
    fl = _frac_lo(x)
    half = [_body(x, fl + (1.0 - fl) * g) for g in _GS]
    full = half + [(-y, z) for (y, z) in reversed(half[:-1])]
    n = len(full)
    out = []
    for i in range(n):
        a = full[max(0, i - 1)]
        b = full[min(n - 1, i + 1)]
        ty, tz = b[0] - a[0], b[1] - a[1]
        L = math.hypot(ty, tz) or 1.0
        ny, nz = tz / L, -ty / L
        out.append((full[i][0] + ny * H_PANEL, full[i][1] + nz * H_PANEL))
    _sec_cache[k] = out
    return out


_QN = 160
_arc_cache = {}


def _qmap(x):
    """(A, total): A[k] is normalised arc from the crown at spline index k/_QN.

    D-EC02: q used to be the raw spline parameter.  The cover's control points
    are NOT evenly spaced in arc - over the cockpit trough at x = +0.10 half the
    section's arc lives in a quarter of the parameter - so a joint line placed
    at "q = 0.62" landed 40 mm from the lower edge at one station and 210 mm at
    another, and the front shoulder rails came out as 35 mm knife edges.  q is
    now normalised ARC from the crown, so w = q * arc is metres on the skin.
    """
    k = _key(x)
    got = _arc_cache.get(k)
    if got is not None:
        return got
    ctrl = _cover_ctrl(x)
    pts = [_cr_point(ctrl, 0.5 * (1.0 - i / _QN)) for i in range(_QN + 1)]
    cum = [0.0]
    for i in range(1, _QN + 1):
        cum.append(cum[-1] + math.hypot(pts[i][0] - pts[i - 1][0],
                                        pts[i][1] - pts[i - 1][1]))
    total = cum[-1] or 1.0
    got = ([c / total for c in cum], total)
    _arc_cache[k] = got
    return got


def _arc(x):
    """Arc length in metres from the crown to the lower edge (q = 0 -> 1)."""
    return _qmap(x)[1]


def _s_of_q(x, q):
    """Spline index fraction (0 crown, 1 lower edge) for arc fraction q."""
    A = _qmap(x)[0]
    q = min(max(q, 0.0), 1.0)
    lo, hi = 0, _QN
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if A[mid] <= q:
            lo = mid
        else:
            hi = mid
    d = A[hi] - A[lo]
    t = 0.0 if d < 1e-12 else (q - A[lo]) / d
    return (lo + t) / _QN


def _q_of_s(x, s):
    A = _qmap(x)[0]
    f = min(max(s, 0.0), 1.0) * _QN
    k = min(int(f), _QN - 1)
    return C.lerp(A[k], A[k + 1], f - k)


def _sect(x, q):
    """3-D point on the cover skin.  q = 0 crown, q = +1 left lower edge,
    measured as normalised arc length along the section."""
    qq = min(max(q, -1.0), 1.0)
    s = _s_of_q(x, abs(qq))
    v = 0.5 - 0.5 * s if qq >= 0.0 else 0.5 + 0.5 * s
    y, z = _cr_point(_cover_ctrl(x), v)
    return Vector((x, y, z))


def _q_of_w(x, w):
    return w / max(_arc(x), 1e-6)


def _q_of_frac(x, f):
    """q of the point at body half-profile fraction `f` - lets a joint line
    follow a real feature of the monocoque instead of a parameter value."""
    fl = _frac_lo(x)
    g = min(max((f - fl) / max(1e-6, 1.0 - fl), 0.0), 1.0)
    idx = len(_GS) - 1.0
    for i in range(len(_GS) - 1):
        if _GS[i] <= g <= _GS[i + 1]:
            idx = i + (g - _GS[i]) / (_GS[i + 1] - _GS[i])
            break
    return _q_of_s(x, 1.0 - 2.0 * (idx / 12.0))


def _frame(x, q):
    """(P, N, Tx, Tq) - point, outward unit normal, unit surface tangents."""
    p = _sect(x, q)
    dq, dx = 0.0030, 0.0022
    tq = _sect(x, min(1.0, q + dq)) - _sect(x, max(-1.0, q - dq))
    tx = _sect(x + dx, q) - _sect(x - dx, q)
    n = tx.cross(tq)
    if n.length < 1e-9:
        n = Vector((0.0, 0.0, 1.0))
    n.normalize()
    if tx.length > 1e-9:
        tx = tx.normalized()
    if tq.length > 1e-9:
        tq = tq.normalized()
    return p, n, tx, tq


def _at(x, q, h=0.0):
    p, n, _tx, _tq = _frame(x, q)
    return p + n * h


# =========================================================================== #
# 3.  feature algebra in (x, w) - w is arc length in metres from the crown
# =========================================================================== #

def _sd_super(x, q, xc, xh, wc, wh, n=2.6, sym=False):
    """Signed distance (metres) to a superellipse in (x, w).

    D-EC08: this used to return (r - 1) * min(xh, wh).  For the airbox mouth
    xh = 50 mm and wh = 124 mm, so the "distance" was under-reported 2.5x along
    w: the raised intake lip, whose width is driven off this number, came out
    28 mm deep at the front of the mouth and 70 mm deep at its sides, and read
    as a lumpy organic bulge instead of a moulded rim.  Dividing by |grad| gives
    a first-order true distance, which is near-exact close to the boundary -
    exactly where every offset feature lives.
    """
    w = q * _arc(x)
    if sym:
        w = abs(w)
    a = abs((x - xc) / xh)
    b = abs((w - wc) / wh)
    s = a ** n + b ** n
    if s < 1e-10:
        return -min(xh, wh)
    r = s ** (1.0 / n)
    c = s ** (1.0 / n - 1.0)
    gx = c * (a ** (n - 1.0)) / xh
    gw = c * (b ** (n - 1.0)) / wh
    g = math.hypot(gx, gw)
    if g < 1e-9:
        return (r - 1.0) * min(xh, wh)
    return (r - 1.0) / g


def _outline(xc, xh, wc, wh, n, npts, sign=1.0):
    """(x, q) samples around a superellipse boundary, CCW in (x, w)."""
    e = 2.0 / n
    out = []
    for i in range(npts):
        t = TAU * i / npts
        ct, st = math.cos(t), math.sin(t)
        xn = math.copysign(abs(ct) ** e, ct)
        wn = math.copysign(abs(st) ** e, st)
        x = xc + xh * xn
        w = sign * (wc + wh * wn)
        out.append((x, _q_of_w(x, w)))
    return out


def _mouth_sd(x, q):
    return _sd_super(x, q, MO_XC, MO_XH, 0.0, MO_WH, MO_N)


_bwc = {}


def _bank_wc(bank):
    """Arc distance from the crown to a louvre bank's centreline, metres."""
    got = _bwc.get(bank)
    if got is None:
        xc, _xh, from_seam, off, _wh, _ns, _nb = bank
        base = _qsplit(xc) * _arc(xc) if from_seam else 0.0
        got = base + off
        _bwc[bank] = got
    return got


def _bank_sd(x, q, bank):
    xc, xh, _fs, _off, wh, ns, _nb = bank
    return _sd_super(x, q, xc, xh, _bank_wc(bank), wh, ns, sym=True)


def _pad(d, height, ramp):
    if d >= ramp:
        return 0.0
    if d <= 0.0:
        return height
    return height * C.smoothstep(1.0 - d / ramp)


def _hfun(x, q):
    """Local relief on the skin: intake lip and the four louvre plinths."""
    h = 0.0
    d = _mouth_sd(x, q)
    if d < 0.075:
        h += LIP_H * math.exp(-(max(d, 0.0) / 0.026) ** 2)
    for bank in BANKS:
        if abs(x - bank[0]) < bank[1] + 0.09:
            h += _pad(_bank_sd(x, q, bank), PLINTH_H, PLINTH_RAMP)
    return h


def _front_sd(x, q):
    """Raked forward cut on the shoulder rails: the joint runs 52 mm further
    forward at the lower edge than at the deck seam, the way a cover's front
    edge follows the cockpit coaming."""
    qs = _qsplit(x)
    t = min(1.0, max(0.0, (abs(q) - qs) / max(1e-6, 1.0 - qs)))
    return (X_FWD + 0.052 * C.smoothstep(t)) - x


# --------------------------------------------------------------------------- #
# what a spine-mounted part actually lands on
# --------------------------------------------------------------------------- #

_DECK_N = 30
_DECK_W = 0.058           # arc from the crown that the table covers
_deck_cache = {}


def _deck_tab(x):
    """(|y|, z, w) samples walking outboard from the crown, relief included.

    D-EC21: the fin used to be built on a FLAT bottom line at "crown - 3 mm".
    The deck falls 6.9 mm at 20 mm off the spine and 18.5 mm at 40 mm, so the
    outer corners of every flared root section stood on nothing - a continuous
    see-through slot down both sides of the fin for its whole 1.7 m.  Anything
    that lands on the spine now asks this table where the skin actually is
    instead of assuming the deck is flat there.
    """
    k = _key(x)
    got = _deck_cache.get(k)
    if got is None:
        ys, zs, ws = [], [], []
        for i in range(_DECK_N + 1):
            w = _DECK_W * i / _DECK_N
            q = _q_of_w(x, w)
            p = _at(x, q, _hfun(x, q))
            ys.append(abs(p.y))
            zs.append(p.z)
            ws.append(w)
        got = (ys, zs, ws)
        _deck_cache[k] = got
    return got


def _deck_lookup(x, y, col):
    tab = _deck_tab(x)
    ys, vals = tab[0], tab[col]
    a = abs(y)
    if a <= ys[0]:
        return vals[0]
    for i in range(len(ys) - 1):
        if ys[i] <= a <= ys[i + 1]:
            d = ys[i + 1] - ys[i]
            t = 0.0 if d < 1e-12 else (a - ys[i]) / d
            return C.lerp(vals[i], vals[i + 1], t)
    return vals[-1]


def _deck_z(x, y):
    """z of the outer skin (local relief included) at (x, y), near the spine."""
    return _deck_lookup(x, y, 1)


def _deck_w(x, y):
    """Arc length from the crown to the skin point at (x, y)."""
    return _deck_lookup(x, y, 2)


def _crest_h(x, w):
    """Height of the roll-hoop crest fairing above the skin at arc w.

    Reproduces exactly what _hoop() lofts, so anything standing on the crest
    stands on the surface that is really there rather than on a guessed offset.
    """
    if x > X_CREST_F or x < X_CREST_R:
        return 0.0
    u = (X_CREST_F - x) / (X_CREST_F - X_CREST_R)
    hw = C.lerp(0.1080, 0.0300, C.smoothstep(u ** 0.72))
    hgt = 0.0128 * (1.0 - u) ** 1.25 + 0.0026 * (1.0 - u * 0.7)
    s = min(1.0, abs(w) / max(hw, 1e-6))
    bump = (1.0 - s * s) ** 0.42
    return hgt * bump - 0.0024 * (1.0 - bump)


def _root_z(x, y):
    """Top of whatever a spine-mounted part lands on at (x, y): the skin, plus
    the crest fairing wherever the crest exists."""
    return _deck_z(x, y) + max(0.0, _crest_h(x, _deck_w(x, y)))


# =========================================================================== #
# 4.  mesh accumulation
# =========================================================================== #

class Acc:
    __slots__ = ("v", "f", "m")

    def __init__(self):
        self.v = []
        self.f = []
        self.m = []

    def vert(self, p):
        self.v.append((float(p[0]), float(p[1]), float(p[2])))
        return len(self.v) - 1

    def face(self, idx, mat=0):
        self.f.append(tuple(idx))
        self.m.append(mat)

    def loft(self, rings, mat=0, closed=True, cap_start=False, cap_end=False):
        b = len(self.v)
        n = len(rings[0])
        for r in rings:
            if len(r) != n:
                raise ValueError("ring length mismatch")
            for p in r:
                self.vert(p)
        span = n if closed else n - 1
        for i in range(len(rings) - 1):
            a0, b0 = b + i * n, b + (i + 1) * n
            for j in range(span):
                j2 = (j + 1) % n
                self.face((a0 + j, a0 + j2, b0 + j2, b0 + j), mat)
        if cap_start:
            self.face(tuple(range(b, b + n))[::-1], mat)
        if cap_end:
            s = b + (len(rings) - 1) * n
            self.face(tuple(range(s, s + n)), mat)
        return b

    def grid(self, rows, mat=0):
        b = len(self.v)
        n = len(rows[0])
        for r in rows:
            for p in r:
                self.vert(p)
        for i in range(len(rows) - 1):
            a0, b0 = b + i * n, b + (i + 1) * n
            for j in range(n - 1):
                self.face((a0 + j, a0 + j + 1, b0 + j + 1, b0 + j), mat)
        return b


def _emit(name, acc, coll, matnames, smooth=32.0, bevel=None):
    ob = C.new_obj(name, acc.v, acc.f, coll=coll, smooth=True)
    for i, mn in enumerate(matnames):
        C.assign(ob, S.mat(mn), slot=i)
    me = ob.data
    if len(me.polygons) == len(acc.m):
        for poly, mi in zip(me.polygons, acc.m):
            poly.material_index = min(mi, len(matnames) - 1)
    else:
        print(f"!! {name}: face count changed "
              f"({len(me.polygons)} != {len(acc.m)}), materials collapsed")
    if smooth is not None:
        C.shade_auto_smooth(ob, smooth)
    if bevel is not None:
        C.add_bevel(ob, width=bevel[0], segments=bevel[1], angle=bevel[2])
    return ob


# =========================================================================== #
# 5.  the panel shell builder
# =========================================================================== #

def _newton_snap(x, q, sdf, dx_cell, dq_cell):
    """Project (x, q) onto sdf = 0.  Movement clamped to 3/4 of a cell."""
    x0, q0 = x, q
    ex, eq = 3.0e-4, 1.5e-3
    for _ in range(7):
        s = sdf(x, q)
        if abs(s) < 2.0e-5:
            break
        gx = (sdf(x + ex, q) - sdf(x - ex, q)) / (2.0 * ex)
        gq = (sdf(x, q + eq) - sdf(x, q - eq)) / (2.0 * eq)
        g2 = gx * gx + gq * gq
        if g2 < 1e-12:
            break
        x -= s * gx / g2
        q -= s * gq / g2
    lx = 0.78 * dx_cell
    lq = 0.78 * dq_cell
    x = min(max(x, x0 - lx), x0 + lx)
    q = min(max(q, q0 - lq), q0 + lq)
    return x, q


def _panel(acc, x0, x1, qlo, qhi, stepx=0.0062, stepq=0.0062,
           holes=(), hfun=None, t=T_SKIN, m_out=0, m_in=1, rim_seg=3):
    """One closed, rolled-edge bodywork panel.

    qlo/qhi are floats or callables of x, so a joint line can sweep across the
    section.  `holes` are signed-distance callables; grid nodes on a hole
    boundary are projected onto the exact zero level set, so an aperture edge is
    a smooth curve rather than a 6 mm staircase.
    """
    fq0 = qlo if callable(qlo) else (lambda _x, _v=qlo: _v)
    fq1 = qhi if callable(qhi) else (lambda _x, _v=qhi: _v)
    hf = hfun or (lambda _x, _q: 0.0)

    nx = max(2, int(round(abs(x1 - x0) / stepx)))
    xm = 0.5 * (x0 + x1)
    arc = _arc(xm) * abs(fq1(xm) - fq0(xm))
    nq = max(2, int(round(arc / stepq)))

    xs = [x0 + (x1 - x0) * i / nx for i in range(nx + 1)]
    par = [[(xs[i], C.lerp(fq0(xs[i]), fq1(xs[i]), j / nq)) for j in range(nq + 1)]
           for i in range(nx + 1)]

    def sd(x, q):
        if not holes:
            return 1.0
        return min(h(x, q) for h in holes)

    # ---- which quads survive ------------------------------------------- #
    present = [[True] * nq for _ in range(nx)]
    if holes:
        for i in range(nx):
            for j in range(nq):
                cx = 0.25 * (par[i][j][0] + par[i + 1][j][0]
                             + par[i][j + 1][0] + par[i + 1][j + 1][0])
                cq = 0.25 * (par[i][j][1] + par[i + 1][j][1]
                             + par[i][j + 1][1] + par[i + 1][j + 1][1])
                present[i][j] = sd(cx, cq) > 0.0

    def quad(i, j):
        if 0 <= i < nx and 0 <= j < nq:
            return present[i][j]
        return False

    used = [[False] * (nq + 1) for _ in range(nx + 1)]
    holeadj = [[False] * (nq + 1) for _ in range(nx + 1)]
    for i in range(nx + 1):
        for j in range(nq + 1):
            u = False
            a = False
            for di in (-1, 0):
                for dj in (-1, 0):
                    ii, jj = i + di, j + dj
                    if 0 <= ii < nx and 0 <= jj < nq:
                        if present[ii][jj]:
                            u = True
                        else:
                            a = True
            used[i][j] = u
            holeadj[i][j] = a
    if holes:
        dxc = abs(x1 - x0) / nx
        for i in range(nx + 1):
            for j in range(nq + 1):
                if used[i][j] and holeadj[i][j]:
                    x, q = par[i][j]
                    dqc = abs(fq1(xs[i]) - fq0(xs[i])) / nq
                    par[i][j] = _newton_snap(x, q, sd, dxc, dqc)

    # ---- geometry -------------------------------------------------------- #
    Pn = [[None] * (nq + 1) for _ in range(nx + 1)]
    for i in range(nx + 1):
        for j in range(nq + 1):
            if not used[i][j]:
                continue
            x, q = par[i][j]
            p, n, tx, tq = _frame(x, q)
            h = hf(x, q)
            Pn[i][j] = (p, n, tx, tq, h)

    outer = {}
    inner = {}

    def vout(i, j):
        k = (i, j)
        got = outer.get(k)
        if got is None:
            p, n, _tx, _tq, h = Pn[i][j]
            got = acc.vert(p + n * h)
            outer[k] = got
        return got

    def vin(i, j):
        k = (i, j)
        got = inner.get(k)
        if got is None:
            p, n, _tx, _tq, h = Pn[i][j]
            got = acc.vert(p + n * (h - t))
            inner[k] = got
        return got

    for i in range(nx):
        for j in range(nq):
            if not present[i][j]:
                continue
            a, b, c, d = (i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)
            acc.face((vout(*a), vout(*b), vout(*c), vout(*d)), m_out)
            acc.face((vin(*d), vin(*c), vin(*b), vin(*a)), m_in)

    # ---- rolled rim ------------------------------------------------------ #
    bedges = []
    wacc = {}

    def push(node, wvec):
        cur = wacc.get(node)
        if cur is None:
            wacc[node] = wvec.copy()
        else:
            cur += wvec

    for i in range(nx + 1):
        for j in range(nq):
            # edge (i,j)-(i,j+1): quads (i-1,j) and (i,j)
            l, r = quad(i - 1, j), quad(i, j)
            if l == r:
                continue
            a, b = (i, j), (i, j + 1)
            bedges.append((a, b))
            for nd in (a, b):
                tx = Pn[nd[0]][nd[1]][2]
                push(nd, -tx if r else tx)
    for i in range(nx):
        for j in range(nq + 1):
            # edge (i,j)-(i+1,j): quads (i,j-1) and (i,j)
            l, r = quad(i, j - 1), quad(i, j)
            if l == r:
                continue
            a, b = (i, j), (i + 1, j)
            bedges.append((a, b))
            for nd in (a, b):
                tq = Pn[nd[0]][nd[1]][3]
                push(nd, -tq if r else tq)

    r = 0.5 * t
    rings = {}
    for nd, wv in wacc.items():
        p, n, _tx, _tq, h = Pn[nd[0]][nd[1]]
        w = wv - n * wv.dot(n)
        if w.length < 1e-7:
            w = _tq.copy()
        w.normalize()
        mid = p + n * (h - r)
        ring = [vout(*nd)]
        for k in range(1, rim_seg + 1):
            th = math.pi * k / (rim_seg + 1)
            ring.append(acc.vert(mid + n * (r * math.cos(th))
                                 + w * (r * math.sin(th))))
        ring.append(vin(*nd))
        rings[nd] = ring
    for a, b in bedges:
        ra, rb = rings[a], rings[b]
        for k in range(rim_seg + 1):
            acc.face((ra[k], rb[k], rb[k + 1], ra[k + 1]), m_out)
    return nx, nq


# =========================================================================== #
# 6.  fasteners - Dzus quarter-turn, explicit chamfers, no booleans
# =========================================================================== #

def _fastener(acc, org, n, tx, ty, m_body=0, m_head=0, ang=0.0, seg=22):
    """Flanged Dzus stud: rolled washer, barrel, two D pads across a 3.2 mm slot."""
    ca, sa = math.cos(ang), math.sin(ang)
    ex = tx * ca + ty * sa
    ey = -tx * sa + ty * ca

    def pt(r, a, z):
        return org + ex * (r * math.cos(a)) + ey * (r * math.sin(a)) + n * z

    # washer: closed profile revolved
    prof = [(0.00455, 0.0000), (0.00720, 0.0000), (0.00720, 0.00062),
            (0.00655, 0.00120), (0.00500, 0.00120), (0.00455, 0.00082)]
    rings = []
    for (rr, zz) in prof:
        rings.append([pt(rr, TAU * i / seg, zz) for i in range(seg)])
    b = len(acc.v)
    for ring in rings:
        for p in ring:
            acc.vert(p)
    npr = len(prof)
    for i in range(npr):
        i2 = (i + 1) % npr
        for j in range(seg):
            j2 = (j + 1) % seg
            acc.face((b + i * seg + j, b + i * seg + j2,
                      b + i2 * seg + j2, b + i2 * seg + j), m_body)

    # barrel up to the slot floor.  D-EC01: the profile used to end at r = 0,
    # which produced `seg` zero-area quads per stud - 352 faces silently dropped
    # by mesh.validate(), which then shifted every material index.  The floor is
    # now two real annuli and one triangle fan.
    bp = [(0.00450, 0.00050), (0.00450, 0.00142), (0.00398, 0.00165),
          (0.00230, 0.00165)]
    rings = [[pt(rr, TAU * i / seg, zz) for i in range(seg)] for (rr, zz) in bp]
    base = acc.loft(rings, m_head, closed=True)
    last = base + (len(bp) - 1) * seg
    cidx = acc.vert(org + n * 0.00165)
    for j in range(seg):
        acc.face((last + j, last + (j + 1) % seg, cidx), m_head)

    # two D pads either side of the slot
    half = 0.00160
    rad = 0.00445
    a0 = math.asin(half / rad)
    for sgn in (1.0, -1.0):
        arc = []
        na = 13
        for i in range(na):
            a = a0 + (math.pi - 2.0 * a0) * i / (na - 1)
            arc.append((rad * math.cos(a), sgn * rad * math.sin(a)))
        prof_rings = []
        for (zz, shr) in ((0.00150, 1.0), (0.00286, 1.0), (0.00318, 0.86)):
            ring = []
            for (u, v) in arc:
                cy = sgn * half
                uu = u * shr
                vv = cy + (v - cy) * shr
                ring.append(org + ex * uu + ey * vv + n * zz)
            prof_rings.append(ring)
        acc.loft(prof_rings, m_head, closed=True, cap_start=True, cap_end=True)


# =========================================================================== #
# 7.  build
# =========================================================================== #

def _q_deck(x, sgn):
    return sgn * (_qsplit(x) - 0.5 * GAP / _arc(x))


def _q_shoulder(x, sgn):
    return sgn * (_qsplit(x) + 0.5 * GAP / _arc(x))


def _shell(coll):
    acc = Acc()
    hg = 0.5 * GAP

    holes_mouth = [_mouth_sd]
    holes_a = [lambda x, q: _bank_sd(x, q, BANKS[0])]
    holes_b = [lambda x, q: _bank_sd(x, q, BANKS[1])]

    # deck, front (carries the airbox mouth)
    _panel(acc, X_DECK_F, X_SEAM_M + hg,
           lambda x: _q_deck(x, -1.0), lambda x: _q_deck(x, 1.0),
           stepx=0.0056, stepq=0.0056, holes=holes_mouth, hfun=_hfun)
    # deck, rear
    _panel(acc, X_SEAM_M - hg, X_SEAM_T + hg,
           lambda x: _q_deck(x, -1.0), lambda x: _q_deck(x, 1.0),
           stepx=0.0068, stepq=0.0068, hfun=_hfun)
    # shoulders
    for sgn in (1.0, -1.0):
        _panel(acc, X_FWD + 0.058, X_SEAM_M + hg,
               lambda x, s=sgn: _q_shoulder(x, s), lambda x, s=sgn: s * 1.0,
               stepx=0.0064, stepq=0.0060, holes=[_front_sd], hfun=_hfun)
        _panel(acc, X_SEAM_M - hg, X_SEAM_T + hg,
               lambda x, s=sgn: _q_shoulder(x, s), lambda x, s=sgn: s * 1.0,
               stepx=0.0058, stepq=0.0055, holes=holes_a, hfun=_hfun)
    # tail
    _panel(acc, X_SEAM_T - hg, X_TAIL_E, -1.0, 1.0,
           stepx=0.0060, stepq=0.0058, holes=holes_b, hfun=_hfun)

    return _emit(P + "shell", acc, coll, ["LiveryPaint", "CarbonMatte"],
                 smooth=34.0)


def _seams(coll):
    """Bonded backing strips seen down every panel joint."""
    acc = Acc()
    hb = lambda _x, _q: -BACK_DROP
    for xs in (X_SEAM_M, X_SEAM_T):
        _panel(acc, xs + 0.017, xs - 0.017, -0.995, 0.995,
               stepx=0.0060, stepq=0.0075, hfun=hb, t=0.0030, rim_seg=2,
               m_out=0, m_in=0)
    for sgn in (1.0, -1.0):
        _panel(acc, X_FWD, X_SEAM_T,
               lambda x, s=sgn: s * (_qsplit(x) - 0.017 / _arc(x)),
               lambda x, s=sgn: s * (_qsplit(x) + 0.017 / _arc(x)),
               stepx=0.0075, stepq=0.0065, hfun=hb, t=0.0030, rim_seg=2,
               m_out=0, m_in=0)
    return _emit(P + "seams", acc, coll, ["CarbonMatte"], smooth=30.0)


def _bulkhead(coll):
    """Closing bulkhead behind the driver's headrest: a dished carbon panel
    that hangs off the deck panel's front edge, so the cover is not an open
    tube when you look at it from ahead."""
    acc = Acc()
    x = X_DECK_F
    nq = 64
    front, back = [], []
    for k in range(8):
        u = k / 7.0
        drop = 0.082 * u ** 0.86
        xx = x + 0.030 * C.smoothstep(u)          # dishes rearward as it drops
        fr, bk = [], []
        for j in range(nq + 1):
            q = C.lerp(_q_deck(xx, -1.0), _q_deck(xx, 1.0), j / nq)
            p, n, _tx, _tq = _frame(xx, q)
            base = p + n * (-T_SKIN - 0.0010) - Vector((0.0, 0.0, drop))
            fr.append(base)
            bk.append(base - Vector((0.0035, 0.0, 0.0)))
        front.append(fr)
        back.append(bk)
    acc.grid(front, 0)
    acc.grid([list(reversed(r)) for r in back], 0)
    # close the four edges so it is a solid slab, not a sheet
    for pair, flip in (((front[0], back[0]), False),
                       ((front[-1], back[-1]), True)):
        a, b = pair
        base = len(acc.v)
        for i in range(nq + 1):
            acc.vert(a[i])
            acc.vert(b[i])
        for i in range(nq):
            f = (base + 2 * i, base + 2 * i + 1, base + 2 * i + 3, base + 2 * i + 2)
            acc.face(f[::-1] if flip else f, 0)
    for j, flip in ((0, True), (nq, False)):
        base = len(acc.v)
        for k in range(8):
            acc.vert(front[k][j])
            acc.vert(back[k][j])
        for k in range(7):
            f = (base + 2 * k, base + 2 * k + 1, base + 2 * k + 3, base + 2 * k + 2)
            acc.face(f[::-1] if flip else f, 0)
    return _emit(P + "bulkhead", acc, coll, ["CarbonMatte"], smooth=32.0)


# --------------------------------------------------------------------------- #
# airbox: throat, splitter, plenum
# --------------------------------------------------------------------------- #

def _duct(coll):
    acc = Acc()
    NP = 72
    lip = _outline(MO_XC, MO_XH, 0.0, MO_WH, MO_N, NP)

    # target plenum ring: rounded rect at x = X_PL, diving below the crown
    X_PL = -0.545
    Z_PL = 0.735
    HW, HH, NN = 0.0885, 0.0530, 3.2
    # D-EC10: the plenum ring was built with theta measured from +y while the
    # mouth outline measures it from +x, so the loft twisted the duct through 90
    # degrees - the mouth's lower lip ended up feeding the plenum's left wall and
    # the throat read as a nonsense fold.  phi = theta - 90 pairs the mouth's
    # low front edge with the plenum floor, which is where the air actually goes.
    tgt = []
    for i in range(NP):
        t = TAU * i / NP
        ct, st = math.cos(t), math.sin(t)
        e = 2.0 / NN
        tgt.append(Vector((X_PL,
                           HW * math.copysign(abs(st) ** e, st),
                           Z_PL - HH * math.copysign(abs(ct) ** e, ct))))

    K = 16
    rings = []
    for k in range(K + 1):
        u = k / K
        s = C.smoothstep(u ** 0.82)
        ring = []
        for i in range(NP):
            x, q = lip[i]
            p, n, _tx, _tq = _frame(x, q)
            start = p + n * (_hfun(x, q) - T_SKIN - 0.0008)
            # first pull straight in along the normal, then morph to the plenum
            pull = n * (-0.020 * C.smoothstep(min(1.0, u * 2.4)))
            ring.append(start.lerp(tgt[i], s) + pull * (1.0 - s))
        rings.append(ring)
    # lacquered throat, matte deeper in: the value break is what makes the
    # tunnel read as depth instead of a flat black hole.
    acc.loft(rings[:8], 3, closed=True)
    acc.loft(rings[7:], 0, closed=True)

    # four stiffening beads down the throat - their highlights describe the bore
    for i0 in (NP // 8, 3 * NP // 8, 5 * NP // 8, 7 * NP // 8):
        rows = []
        for k in range(1, 10):
            ring = rings[k]
            ctr = Vector((0.0, 0.0, 0.0))
            for p in ring:
                ctr += p
            ctr /= NP
            p = ring[i0]
            d = (ring[(i0 + 1) % NP] - ring[(i0 - 1) % NP])
            if d.length < 1e-9:
                continue
            d.normalize()
            inw = (ctr - p)
            inw -= d * inw.dot(d)
            if inw.length < 1e-9:
                continue
            inw.normalize()
            hh = 0.0034 * min(1.0, (10.0 - k) / 4.0)
            ww = 0.0055
            rows.append([p - d * ww,
                         p - d * ww * 0.55 + inw * hh * 0.62,
                         p + inw * hh,
                         p + d * ww * 0.55 + inw * hh * 0.62,
                         p + d * ww])
        if len(rows) > 1:
            acc.loft(rows, 3, closed=False)

    # plenum floor / far wall - deliberately dark, you only see darkness in there
    b = len(acc.v)
    for p in rings[-1]:
        acc.vert(p)
    cidx = acc.vert(Vector((X_PL - 0.055, 0.0, Z_PL - 0.004)))
    for i in range(NP):
        acc.face((b + i, b + (i + 1) % NP, cidx), 1)

    # Flow dividers.  D-EC15: one lonely centre blade left the throat reading as
    # a black hole with a white sliver in it.  Three vanes give the tunnel three
    # lit leading edges at any camera angle, which is what makes a duct read as
    # a duct - and multi-vane dividers are what is actually in there.
    # D-EC18: the vanes were Titanium.  A metal with nothing to reflect inside a
    # dark plenum renders as pure black with a sandy roughness-noise crawl over
    # it; lacquered carbon keeps a diffuse term and a clean lit edge.
    for (yc, xs0, xs1, THK, hs, mt) in ((0.0000, -0.2270, -0.5180, 0.0042, 1.00, 3),
                                        (0.0480, -0.2360, -0.4560, 0.0031, 0.78, 3),
                                        (-0.0480, -0.2360, -0.4560, 0.0031, 0.78, 3)):
        NS = 24
        NV = 9

        def vring(x, th, hscale):
            tt = C.smoothstep(min(1.0, max(0.0, (x - xs0) / (xs1 - xs0))) ** 0.82)
            ptop = _at(x, 0.0, _hfun(x, 0.0) - T_SKIN - 0.0020)
            zt = C.lerp(ptop.z, Z_PL + HH - 0.0035, tt)
            zb = C.lerp(ptop.z - 0.052, Z_PL - HH + 0.0035, tt)
            zm = 0.5 * (zt + zb)
            zt = zm + (zt - zm) * hscale
            zb = zm + (zb - zm) * hscale
            xx = C.lerp(ptop.x, X_PL, tt)
            r = []
            for k in range(NV):
                r.append(Vector((xx, yc + th * 0.5,
                                 C.lerp(zt, zb, k / (NV - 1)))))
            for k in range(NV):
                r.append(Vector((xx, yc - th * 0.5,
                                 C.lerp(zt, zb, 1.0 - k / (NV - 1)))))
            return r

        rows = []
        for j in (2, 1):                       # rounded leading edge
            rows.append(vring(xs0 + 0.010 * j,
                              THK * 0.42 * math.sqrt(max(0.0, 1.0 - (j / 2.4) ** 2)),
                              hs))
        for i in range(NS + 1):
            u = i / NS
            rows.append(vring(C.lerp(xs0, xs1, u),
                              THK * (1.0 - 0.35 * u) * (0.42 if i == 0 else 1.0),
                              hs))
        acc.loft(rows, mt, closed=True, cap_start=True, cap_end=True)
    return _emit(P + "duct", acc, coll,
                 ["CarbonMatte", "MatteBlack", "Titanium", "CarbonFibre"],
                 smooth=30.0)


# --------------------------------------------------------------------------- #
# roll structure
# --------------------------------------------------------------------------- #

def _hoop(coll):
    acc = Acc()
    NP = 96
    # surround band: a swept rounded section following the mouth outline,
    # offset outboard of the lip
    inner = _outline(MO_XC, MO_XH + 0.0105, 0.0, MO_WH + 0.0110, 2.5, NP)
    outer = _outline(MO_XC, MO_XH + 0.0530, 0.0, MO_WH + 0.0525, 2.8, NP)

    # D-EC07 / D-EC11: a sin() crest made the band a fat doughnut round the
    # mouth, and both feet feathered onto the deck at +0.6 mm.  A surface that
    # approaches another asymptotically has no edge - where it "ends" is decided
    # by sub-millimetre shading, and the band's outline rendered as a scalloped,
    # wobbling curve.  It is now a flat-topped rail whose feet are BURIED
    # 2.6 mm in the deck, so the visible outline is a clean transversal
    # intersection instead of a tangency.
    band_h = ((0.00, -0.0026), (0.075, 0.0036), (0.165, 0.0114),
              (0.245, 0.0122), (0.755, 0.0122), (0.835, 0.0114),
              (0.925, 0.0036), (1.00, -0.0026))

    def bh(u):
        for i in range(len(band_h) - 1):
            a, b = band_h[i], band_h[i + 1]
            if a[0] <= u <= b[0]:
                return C.lerp(a[1], b[1], C.smoothstep((u - a[0]) / (b[0] - a[0])))
        return band_h[-1][1]

    NS = 19
    rows = []
    for k in range(NS):
        u = k / (NS - 1)
        row = []
        for i in range(NP):
            xi, qi = inner[i]
            xo, qo = outer[i]
            x = C.lerp(xi, xo, u)
            q = C.lerp(qi, qo, u)
            row.append(_at(x, q, _hfun(x, q) + bh(u)))
        rows.append(row)
    acc.loft(rows, 0, closed=True)

    # D-EC09: the roll structure used to end in two 230 mm knife-edged blades
    # standing on the deck; from above they read as a pair of needles.  A real
    # cover carries the hoop's rear load into a moulded spine that runs back and
    # becomes the fin root, which is what this is - and it also gives the fin
    # somewhere to be born instead of a floating point.
    NC = 54
    crows, crows2 = [], []
    NK = 17
    for k in range(NK):
        u = k / (NK - 1.0)
        x = C.lerp(X_CREST_F, X_CREST_R, u)
        hw = C.lerp(0.1080, 0.0300, C.smoothstep(u ** 0.72))
        hgt = 0.0128 * (1.0 - u) ** 1.25 + 0.0026 * (1.0 - u * 0.7)
        row, row2 = [], []
        for i in range(NC + 1):
            v = i / NC
            q = _q_of_w(x, hw * (2.0 * v - 1.0))
            bump = (1.0 - (2.0 * v - 1.0) ** 2) ** 0.42
            # same tangency trap as the band: bury the spine's edges
            row.append(_at(x, q, _hfun(x, q) + hgt * bump - 0.0024 * (1.0 - bump)))
            row2.append(_at(x, q, _hfun(x, q) - 0.0040))
        crows.append(row)
        crows2.append(row2)
    acc.grid(crows, 2)
    acc.grid([list(reversed(r)) for r in crows2], 2)
    for j, flip in ((0, False), (NC, True)):
        b0 = len(acc.v)
        for k in range(NK):
            acc.vert(crows[k][j])
            acc.vert(crows2[k][j])
        for k in range(NK - 1):
            f = (b0 + 2 * k, b0 + 2 * k + 1, b0 + 2 * k + 3, b0 + 2 * k + 2)
            acc.face(f[::-1] if flip else f, 2)
    for k, flip in ((0, True), (NK - 1, False)):
        b2 = len(acc.v)
        for i in range(NC + 1):
            acc.vert(crows[k][i])
            acc.vert(crows2[k][i])
        for i in range(NC):
            f = (b2 + 2 * i, b2 + 2 * i + 1, b2 + 2 * i + 3, b2 + 2 * i + 2)
            acc.face(f[::-1] if flip else f, 2)

    return _emit(P + "hoop", acc, coll,
                 ["CarbonFibre", "CarbonMatte", "CarbonFibre"], smooth=30.0,
                 bevel=(0.0016, 2, 42.0))


def _tcam(coll):
    """Onboard camera pod on the roll-hoop crest.

    D-EC28: this used to be a 537-poly featureless blob - a tapered carbon
    "thumb" with a grey sphere shoved into its side, no housing, no bezel, no
    mount and a hard unfilleted interpenetration where the lens met the body -
    sitting dead centre of the airbox hero shot and 44 mm above ROLL_HOOP_TOP_Z.
    It is now a real pod: a foot flange buried 2.6 mm in the crest so it cannot
    float or feather onto it, a short pylon, a moulded housing, a lens boss that
    grows out of a raised pad instead of stabbing through the shell, a machined
    bezel and a recessed dark element.  Its top is 15 mm lower than before.
    """
    acc = Acc()
    CX = -0.4300
    zref = max(_root_z(CX + 0.056 * (i / 8.0 - 0.5), 0.0)
               for i in range(9)) + 0.0020

    NA, NL, NG = 48, 32, 24

    def sq(a, b, z, e=5.0):
        r = []
        for i in range(NA):
            t = TAU * i / NA
            ct, st = math.cos(t), math.sin(t)
            p = 2.0 / e
            r.append(Vector((CX + a * math.copysign(abs(ct) ** p, ct),
                             b * math.copysign(abs(st) ** p, st), z)))
        return r

    def circ(c, u, v, r, n):
        return [c + u * (r * math.cos(TAU * i / n))
                + v * (r * math.sin(TAU * i / n)) for i in range(n)]

    def band(rings, mats, cap_start=False, cap_end=False):
        """Loft with a material per BAND, so a bezel and a lens can live in one
        watertight shell instead of three shells with coincident open rims."""
        b0 = len(acc.v)
        n = len(rings[0])
        for rg in rings:
            for p in rg:
                acc.vert(p)
        for i in range(len(rings) - 1):
            a0, c0 = b0 + i * n, b0 + (i + 1) * n
            for j in range(n):
                j2 = (j + 1) % n
                acc.face((a0 + j, a0 + j2, c0 + j2, c0 + j), mats[i])
        if cap_start:
            acc.face(tuple(range(b0, b0 + n))[::-1], mats[0])
        if cap_end:
            s = b0 + (len(rings) - 1) * n
            acc.face(tuple(range(s, s + n)), mats[-1])

    # foot flange -> pylon -> housing, one closed shell
    prof = ((0.0300, 0.0228, None), (0.0300, 0.0228, 0.0000),
            (0.0288, 0.0218, 0.0022), (0.0186, 0.0130, 0.0038),
            (0.0186, 0.0130, 0.0074), (0.0252, 0.0176, 0.0092),
            (0.0264, 0.0186, 0.0110), (0.0264, 0.0186, 0.0272),
            (0.0252, 0.0176, 0.0292), (0.0206, 0.0138, 0.0308),
            (0.0104, 0.0064, 0.0318))
    rings = []
    for (a, b, dz) in prof:
        rg = sq(a, b, 0.0 if dz is None else zref + dz)
        if dz is None:               # base ring rides the crest, buried 2.6 mm
            rg = [Vector((p.x, p.y, _root_z(p.x, p.y) - 0.0026)) for p in rg]
        rings.append(rg)
    band(rings, [0] * (len(rings) - 1), cap_start=True, cap_end=True)

    # lens: pad -> barrel -> bezel -> recessed element, one closed shell
    zl = zref + 0.0186
    ey, ez = Vector((0.0, 1.0, 0.0)), Vector((0.0, 0.0, 1.0))
    lens = ((-0.4110, 0.0112, 0), (-0.4024, 0.0112, 0), (-0.4004, 0.0096, 0),
            (-0.3930, 0.0096, 2), (-0.3914, 0.0116, 2), (-0.3872, 0.0116, 2),
            (-0.3856, 0.0100, 1), (-0.3878, 0.0086, 1), (-0.3902, 0.0078, 1))
    band([circ(Vector((xx, 0.0, zl)), ey, ez, rr, NL) for (xx, rr, _m) in lens],
         [m for (_x, _r, m) in lens[:-1]], cap_start=True, cap_end=True)

    # cable gland out of the left flank
    gz = zref + 0.0140
    ex = Vector((1.0, 0.0, 0.0))
    gl = ((-0.0130, 0.0056), (-0.0208, 0.0056), (-0.0222, 0.0064),
          (-0.0240, 0.0058))
    band([circ(Vector((CX - 0.0082, yy, gz)), ex, ez, rr, NG) for (yy, rr) in gl],
         [1] * (len(gl) - 1), cap_start=True, cap_end=True)

    # smooth=22 keeps the housing's own corner rings creased; at 30 deg the
    # auto-smooth ran straight over them and the pod rendered as a soft pillow
    # rather than a moulded box.
    return _emit(P + "tcam", acc, coll,
                 ["CarbonFibre", "MatteBlack", "Titanium"],
                 smooth=22.0, bevel=(0.0007, 2, 34.0))


# --------------------------------------------------------------------------- #
# shark fin
# --------------------------------------------------------------------------- #

# D-EC04: the first fin height table grew monotonically to 217 mm at the tail,
# which - because the cover crown falls 520 mm over the same run - rendered as a
# rectangular billboard hanging off the back of the car.  Real fins taper. The
# top line now descends steadily and the last 250 mm runs the fin out to a
# 28 mm stub, so the trailing edge is a raked runout, not a slab.
# D-EC22: the table is now height above _root_z - i.e. above the crest fairing
# wherever the crest exists - so the fin can never be inside it.
_FIN_TOP = _mk_table([(-0.486, 0.0085), (-0.510, 0.0122), (-0.540, 0.0182),
                      (-0.575, 0.0258), (-0.620, 0.0352), (-0.665, 0.0440),
                      (-0.800, 0.0630), (-1.000, 0.0850), (-1.250, 0.1050),
                      (-1.500, 0.1180), (-1.700, 0.1240), (-1.850, 0.1185),
                      (-1.960, 0.0965), (-2.040, 0.0600), (-2.100, 0.0280)],
                     passes=10)
_FIN_THK = _mk_table([(-0.486, 0.0168), (-0.560, 0.0146), (-0.900, 0.0122),
                      (-1.400, 0.0102), (-1.800, 0.0085), (-2.100, 0.0072)],
                     passes=14)

_FIN_NF = 6               # cove points per side
_FIN_NZ = 13              # flank points per side
_FIN_NC = 6               # tip-radius points per side
_FIN_NB = 15              # points along the buried underside
_K45 = 1.0 - math.sqrt(0.5)


def _fin_geo(x, shrink=1.0, hscale=1.0):
    """(wb, rt, rf, ya, yb, zf0, zc, zt) - the fin section's key dimensions."""
    wb = max(0.0018, _tab(_FIN_THK, x) * shrink)
    z0 = _root_z(x, 0.0)
    zt = z0 + max(0.0035, _tab(_FIN_TOP, x) * hscale)
    rt = min(0.0034 * shrink, 0.34 * max(zt - z0, 1e-4), 0.95 * wb)
    zc = zt - rt
    zsw = _root_z(x, wb)
    rf = min(FIN_FIL * shrink, 0.80 * max(zc - zsw, 1e-4))
    ya = wb + rf * _K45                       # cove -> runout knuckle
    # Runout: a short steep facet from the end of the cove down THROUGH the skin.
    # Solving it against absolute z instead put the buried corner 54 mm off the
    # spine on a deck that already falls at 36 deg; FIN_RUNOUT sets how steep it
    # is relative to that drop, which is what controls the crossing angle and
    # therefore whether the root has a visible edge at all.
    yb = ya + FIN_RUNOUT * (rf * _K45 + FIN_BURY)
    return wb, rt, rf, ya, yb, zsw + rf, zc, zt


def _fin_foot(x):
    """Half-width of the fin's root skirt at x; 0 where there is no fin."""
    if x > X_FIN_F + 0.015 or x < X_FIN_R - 0.010:
        return 0.0
    return _fin_geo(min(max(x, X_FIN_R), X_FIN_F))[4]


def _fin_ring(x, shrink=1.0, hscale=1.0):
    """Closed (y, z) section of the fin at station x.

    D-EC21: the underside IS the deck now, sunk FIN_BURY into it, so the root is
    in contact at every station instead of hanging off a flat chord; and the
    cove finishes on a steep runout that cuts THROUGH the skin at 33-45 deg
    rather than feathering onto it, so the root has a readable edge instead of a
    sub-millimetre tangency (the same trap D-EC07 fixed on the hoop band).
    """
    wb, rt, rf, ya, yb, zf0, zc, zt = _fin_geo(x, shrink, hscale)
    side = [(yb, _root_z(x, yb) - FIN_BURY),
            (ya, _root_z(x, ya) + rf * _K45)]
    for i in range(1, _FIN_NF + 1):                    # cove, 225 -> 180 deg
        ph = math.pi * (1.25 - 0.25 * i / _FIN_NF)
        yy = wb + rf * (1.0 + math.cos(ph))
        side.append((yy, _root_z(x, yy) + rf * (1.0 + math.sin(ph))))
    for k in range(1, _FIN_NZ + 1):                    # flank
        u = k / _FIN_NZ
        side.append((wb + (rt - wb) * u ** 0.72, C.lerp(zf0, zc, u)))
    for k in range(1, _FIN_NC):                        # tip radius
        th = 0.5 * math.pi * k / _FIN_NC
        side.append((rt * math.cos(th), zc + rt * math.sin(th)))

    ring = [Vector((x, yy, zz)) for (yy, zz) in side]
    ring.append(Vector((x, 0.0, zt)))
    ring.extend(Vector((x, -yy, zz)) for (yy, zz) in reversed(side))
    for i in range(1, _FIN_NB + 1):                    # buried underside
        yy = -yb + 2.0 * yb * i / (_FIN_NB + 1)
        ring.append(Vector((x, yy, _root_z(x, yy) - FIN_BURY)))
    return ring


def _fin(coll):
    acc = Acc()
    rings = []
    # rounded leading edge: thickness AND height run out over the last 13 mm,
    # so the nose is a small rounded shoulder standing on the crest instead of
    # a full-height blade erupting out of it.
    for (dx, sh, hs) in ((0.0130, 0.15, 0.30), (0.0082, 0.42, 0.60),
                         (0.0036, 0.75, 0.86)):
        rings.append(_fin_ring(X_FIN_F + dx, shrink=sh, hscale=hs))
    N = 148
    for i in range(N + 1):
        u = i / N
        rings.append(_fin_ring(C.lerp(X_FIN_F, X_FIN_R, u ** 1.02)))
    # thin trailing edge
    for k, sh in enumerate((0.55, 0.20)):
        rings.append(_fin_ring(X_FIN_R - 0.0035 * (k + 1), shrink=sh))
    acc.loft(rings, 0, closed=True, cap_start=True, cap_end=True)
    # D-EC05: LiveryPaint keys its white centre stripe off |y| < 0.020, and a
    # fin IS a 12 mm blade on y = 0, so the whole thing rendered as a white
    # sail.  Bare lacquered carbon is what half the grid runs anyway.
    return _emit(P + "fin", acc, coll, ["CarbonFibre"], smooth=36.0)


# --------------------------------------------------------------------------- #
# louvre banks
# --------------------------------------------------------------------------- #

def _pans(coll):
    acc = Acc()
    for bank in BANKS:
        xc, xh, _fs, _off, wh, ns, _nb = bank
        wc = _bank_wc(bank)
        for sgn in (1.0, -1.0):
            NP = 84
            out = _outline(xc, xh, wc, wh, ns, NP, sign=sgn)
            rings = []
            for k in range(6):
                u = k / 5.0
                shr = 1.0 - 0.085 * u ** 1.3
                ring = []
                for (x, q) in out:
                    w = abs(q) * _arc(x)
                    x2 = xc + (x - xc) * shr
                    w2 = sgn * (wc + (w - wc) * shr)
                    q2 = _q_of_w(x2, w2)
                    hh = _hfun(x2, q2)
                    ring.append(_at(x2, q2, hh - T_SKIN - 0.0006
                                    - (PAN_D - T_SKIN) * C.smoothstep(u)))
                rings.append(ring)
            acc.loft(rings, 0, closed=True, cap_end=True)
    return _emit(P + "pans", acc, coll, ["MatteBlack"], smooth=28.0)


def _louvres(coll):
    acc = Acc()
    made = 0
    for bank in BANKS:
        xc, xh, _fs, _off, wh, ns, nb = bank
        wc = _bank_wc(bank)
        # D-EC14: the blade was a fixed 11 mm wide while the pitch worked out at
        # 7.5 mm, so consecutive blades OVERLAPPED and the "louvres" were a
        # closed lid over the aperture - no slot, no visible duct, the exact
        # defect the brief calls out.  Width is now derived from the pitch.
        # D-EC24: and the blades used to span only 0.86 of the aperture, leaving
        # an UNLOUVRED 6 mm slot at BOTH w-extremes of every bank - about twice
        # the inter-blade gap and 300 mm long, so each bank read as missing its
        # outer gills.  The pitch now divides the FULL aperture, which puts both
        # end margins at half a gap: the even rhythm a real gill panel has.
        pitch = 2.0 * wh / nb
        bwid = pitch * 0.56
        lift = pitch * 0.55
        for sgn in (1.0, -1.0):
            for k in range(nb):
                wk = wc - wh + pitch * (k + 0.5)

                def _hx(w):
                    """aperture half-length in x at arc position w."""
                    wnp = min(1.0, abs(w - wc) / wh)
                    return xh * max(0.0, 1.0 - wnp ** ns) ** (1.0 / ns)

                if min(_hx(wk - 0.5 * bwid), _hx(wk + 0.5 * bwid)) < 0.012:
                    continue
                made += 1
                NXS, NSS = 22, 7
                rings = []
                for i in range(NXS + 1):
                    # cosine spacing clusters rings at the ends, where the blade
                    # has to dive into the panel in ~12 mm
                    t = 0.5 - 0.5 * math.cos(math.pi * i / NXS)
                    ef = C.smoothstep(min(1.0, min(t, 1.0 - t) / 0.045))
                    ring = []
                    top = []
                    for m in range(NSS):
                        s = m / (NSS - 1)
                        # D-EC23: s used to run OUTBOARD -> INBOARD, so every
                        # blade's raised edge faced the crown, i.e. away from
                        # any camera that can see the bank at all.  Each blade
                        # then roofed the slot behind it and the bank rendered
                        # as a solid ribbed pad: measured 4.8-8.0% of the pan
                        # visible from the two hero angles.  The blade now rises
                        # OUTBOARD, so the open side of every slot faces the way
                        # the panel does and the camera looks straight in.
                        w = wk - 0.5 * bwid + bwid * s
                        # Each END of the blade follows the APERTURE's own curved
                        # boundary.  A rectangular blade whose length was taken at
                        # its centreline over-ran the aperture by 20 mm at the
                        # outer edge of the outermost gill once the blades were
                        # spread across the full opening - a 7 mm proud spur lying
                        # on the panel - and fell 20 mm short at the other edge.
                        xx = xc + (_hx(w) + 0.0035) * (1.0 - 2.0 * t)
                        q = _q_of_w(xx, sgn * w)
                        lf = (lift * C.smoothstep(s) + 0.0026) * ef - 0.0030
                        top.append((xx, q, _hfun(xx, q) + lf))
                    for (xx, q, h) in top:
                        ring.append(_at(xx, q, h))
                    for (xx, q, h) in reversed(top):
                        ring.append(_at(xx, q, h - 0.0013))
                    rings.append(ring)
                acc.loft(rings, 0, closed=True, cap_start=True, cap_end=True)
    print(f">> {P}louvres blades={made}")
    # D-EC17: CarbonMatte maps a 5 mm twill in object space.  On an 8.5 mm wide
    # slat that is two weave repeats across the blade, and at close range the
    # bank rendered as a stack of knurled rods.  Gill slats are moulded black
    # composite on the real car anyway.
    return _emit(P + "louvres", acc, coll, ["MatteBlack"], smooth=30.0,
                 bevel=(0.0006, 2, 45.0))


# --------------------------------------------------------------------------- #
# tail cooling exit + exhaust
# --------------------------------------------------------------------------- #

def _pipe_axis(x):
    u = (x - X_LINER_F) / (X_PIPE_TIP - X_LINER_F)
    return Vector((x, 0.0, C.lerp(Z_PIPE_FWD, Z_PIPE_TIP, u)))


def _liner_ring(x, gap, nq=54):
    """Closed duct section inside the shell at station x.

    D-EC16: the floor used to be a straight chord meeting the side walls at a
    hard corner - from behind it read as a folded sheet of paper.  The chord is
    now blended into the walls over the last 22% of the span with a cosine, so
    the section closes with a radius like a moulded duct.
    """
    pts = []
    for i in range(nq + 1):
        q = -1.0 + 2.0 * i / nq
        p, n, _tx, _tq = _frame(x, q)
        pts.append(p - n * gap)
    zf = 0.5 * (pts[0].z + pts[-1].z) - 0.010
    floor = []
    NF = 20
    for i in range(1, NF):
        t = i / NF
        y = C.lerp(pts[0].y, pts[-1].y, t)
        e = min(t, 1.0 - t) / 0.22
        blend = 0.5 - 0.5 * math.cos(math.pi * min(1.0, e))
        z = C.lerp(0.5 * (pts[0].z + pts[-1].z), zf - 0.005, blend)
        floor.append(Vector((x, y, z)))
    # D-EC29: `pts + floor` walked -y -> crown -> +y and then -y -> +y AGAIN, so
    # the section was a self-crossing bowtie: edge 54-55 and the closing edge
    # 73-0 crossed, and the "floor" was two ribbons slung diagonally across the
    # duct rather than one closed profile.  Verified with a segment-intersection
    # test on the section at x = -2.150 (1 crossing pair before, 0 after).  The
    # floor has to be traversed back the way it came.
    return pts + list(reversed(floor))


def _tailduct(coll):
    """Returns (liner, fittings).

    D-EC13: the liner was a single-sided loft.  Seen from below-behind - which
    is exactly where a rear three-quarter hero shot looks - its floor read as a
    zero-thickness sheet with a razor edge.  It is now its own object carrying a
    solidify, so the duct has a real 3.4 mm wall and a rolled exit lip.
    """
    lin = Acc()
    acc = Acc()
    K = 15
    rings = []
    for k in range(K + 1):
        u = k / K
        x = C.lerp(X_TAIL_E, X_LINER_F, u)
        gap = C.lerp(0.0195, 0.0460, C.smoothstep(u))
        rings.append(_liner_ring(x, gap))
    lin.loft(rings, 0, closed=True)

    # annular heat-shield bulkhead at the forward end, around the tailpipe
    n = len(rings[-1])
    ax = _pipe_axis(X_LINER_F)
    bulk = [rings[-1]]
    for k in range(4):
        u = (k + 1) / 4.0
        r = R_PIPE + 0.0075
        ring = []
        for i in range(n):
            src = rings[-1][i]
            ang = math.atan2(src.z - ax.z, src.y - ax.y)
            tgt = Vector((X_LINER_F - 0.010 * u, ax.y + r * math.cos(ang),
                          ax.z + r * math.sin(ang)))
            ring.append(src.lerp(tgt, C.smoothstep(u)))
        bulk.append(ring)
    acc.loft(bulk, 1, closed=True)

    # three struts holding the pipe, right at the mouth where they are seen
    xs0, xs1 = -2.2005, -2.2385
    ax0 = _pipe_axis(0.5 * (xs0 + xs1))
    xr = 0.5 * (xs0 + xs1)
    ref = _liner_ring(xr, C.lerp(0.0195, 0.0460,
                                 C.smoothstep((xr - X_TAIL_E)
                                              / (X_LINER_F - X_TAIL_E))))
    # D-EC25 follow-on: with the pipe sitting higher in the duct the space above
    # it is only 13 mm, so a strut aimed anywhere between 45 and 135 deg is a
    # stub.  Wall distance was mapped every 15 deg round the pipe at this exact
    # station; the trio now goes where there is room - two lateral (50.7 mm) and
    # one straight down to the floor (43.2 mm).
    n_strut = 0
    for ang in (0.0, math.pi, math.pi * 1.50):
        d = Vector((0.0, math.cos(ang), math.sin(ang)))
        inner = ax0 + d * (R_PIPE - 0.0010)
        wall, best = None, -1.0
        for r in ref:
            v = r - ax0
            v.x = 0.0
            if v.length < 1e-6:
                continue
            c = v.normalized().dot(d)
            if c > best:
                best, wall = c, r
        if wall is None or best < 0.88:
            continue
        n_strut += 1
        outerp = Vector((ax0.x, wall.y, wall.z)) + d * 0.004
        # D-EC20: the strut section used to be offset along +/- X - the same
        # axis the loft ran along - so the "solid" was a ribbon lying in its own
        # sweep plane: 18 zero-area faces and a strut you could not actually see
        # in the duct.  Thickness now goes along d x X, i.e. tangentially, and
        # the loft runs radially from the pipe to the liner wall.
        tang = Vector((0.0, math.sin(ang), -math.cos(ang)))
        NT, NC = 8, 9
        srings = []
        for m in range(NT + 1):
            t = m / NT
            base = inner.lerp(outerp, t)
            th = 0.0034 * (0.62 + 0.38 * math.sin(math.pi * t) ** 0.5)
            ring = []
            for sgn2 in (1.0, -1.0):
                for k in range(NC):
                    u = k / (NC - 1) if sgn2 > 0 else 1.0 - k / (NC - 1)
                    xx = C.lerp(xs0, xs1, u)
                    w = th * math.sqrt(max(0.16, 1.0 - 0.84 * (2.0 * u - 1.0) ** 2))
                    ring.append(Vector((xx, base.y, base.z)) + tang * (sgn2 * w))
            srings.append(ring)
        acc.loft(srings, 2, closed=True, cap_start=True, cap_end=True)
    print(f">> {P}tailduct struts={n_strut}")

    ob_lin = _emit(P + "tailliner", lin, coll, ["CarbonMatte"], smooth=30.0)
    m = C.add_solidify(ob_lin, thickness=0.0034, offset=0.0)
    m.use_rim = True
    C.add_bevel(ob_lin, width=0.0011, segments=2, angle=45.0)
    ob_fit = _emit(P + "tailfittings", acc, coll,
                   ["CarbonMatte", "AnodisedGold", "Titanium"], smooth=30.0)
    return [ob_lin, ob_fit]


def _exhaust(coll):
    acc = Acc()
    NA = 64
    xs = [X_LINER_F + (X_PIPE_TIP - X_LINER_F) * (i / 22) for i in range(23)]

    def ring(x, r, dz=0.0):
        a = _pipe_axis(x)
        return [Vector((x, r * math.cos(TAU * i / NA),
                        a.z + dz + r * math.sin(TAU * i / NA))) for i in range(NA)]

    outer = [ring(x, R_PIPE) for x in xs]
    # tip: chamfer over then back down the bore
    tipx = X_PIPE_TIP
    outer.append(ring(tipx + 0.0006, R_PIPE))
    outer.append(ring(tipx + 0.0002, R_PIPE - 0.0008))
    # cap_start closes the pipe's buried forward end; without it there is a
    # 72 mm hole looking forward out of the duct from a low rear angle
    acc.loft(outer, 0, closed=True, cap_start=True)
    bore = [ring(tipx + 0.0002, R_PIPE - T_PIPE)]
    for i in range(1, 12):
        bore.append(ring(C.lerp(tipx, X_LINER_F + 0.02, i / 11.0),
                         R_PIPE - T_PIPE))
    acc.loft([outer[-1]] + bore, 1, closed=True)
    # dark plug deep inside
    b = len(acc.v)
    for p in bore[-1]:
        acc.vert(p)
    ci = acc.vert(_pipe_axis(X_LINER_F + 0.02))
    for i in range(NA):
        acc.face((b + i, b + (i + 1) % NA, ci), 1)

    # Heat-shield clamp band with two lugs.  D-EC26: this used to be a plain
    # loft with cap_start AND cap_end, which welded two SOLID 36.5 mm AnodisedGold
    # discs right across the 33.4 mm bore, 49 mm inside the tip - rendered down
    # the pipe the tailpipe was a blind gold-bottomed cup and the 405 mm of real
    # bore behind it was dead geometry.  It is now a closed REVOLVED profile: a
    # genuine annular band with a bore through it, gripping the pipe (r just
    # inside R_PIPE) instead of floating 0.5 mm off it.
    bx0, bx1 = -2.2660, -2.2860
    bprof = ((bx0, R_PIPE - 0.0004), (bx0 - 0.0018, R_PIPE + 0.0042),
             (bx1 + 0.0018, R_PIPE + 0.0042), (bx1, R_PIPE - 0.0004))
    bb = len(acc.v)
    for (x, r) in bprof:
        for p in ring(x, r):
            acc.vert(p)
    npr = len(bprof)
    for i in range(npr):
        i2 = (i + 1) % npr
        for j in range(NA):
            j2 = (j + 1) % NA
            acc.face((bb + i * NA + j, bb + i * NA + j2,
                      bb + i2 * NA + j2, bb + i2 * NA + j), 2)
    for sgn in (1.0, -1.0):
        a = _pipe_axis(0.5 * (bx0 + bx1))
        y0 = sgn * (R_PIPE + 0.0035)
        lug = []
        for x in (bx0 - 0.0012, bx1 + 0.0012):
            r0 = []
            for (dy, dz) in ((0.0, -0.0060), (0.0, 0.0060),
                             (sgn * 0.0105, 0.0042), (sgn * 0.0105, -0.0042)):
                r0.append(Vector((x, y0 + dy, a.z + dz)))
            lug.append(r0)
        acc.loft(lug, 2, closed=True, cap_start=True, cap_end=True)
    return _emit(P + "exhaust", acc, coll,
                 ["Titanium", "MatteBlack", "AnodisedGold"], smooth=26.0)


# --------------------------------------------------------------------------- #
# fasteners
# --------------------------------------------------------------------------- #

_FIX_REFUSED = []          # (x, q, w, fin_foot) of every stud place() rejected


def _fixings(coll):
    acc = Acc()
    del _FIX_REFUSED[:]
    n_made = 0
    n_skip = 0

    def place(x, q, extra=0.0, mat=0, ang=0.0):
        # D-EC06: the washer's underside is a flat annulus and the panel is
        # curved, so seating it exactly on the surface z-fought over a 14 mm
        # disc.  Sink it 0.5 mm - more than the 0.13 mm sagitta across the head.
        # D-EC27: and check what is actually UNDERNEATH.  14 of 176 studs used
        # to be wrong because placement was never validated: some hung over the
        # cockpit opening where the deck panel has not started yet, one floated
        # 3.1 mm over the hoop band on the crest, and seven were swallowed whole
        # by the crest fairing, the camera pod or the fin.  Every stud now
        # (a) is refused if it lands in the fin's footprint and (b) rides on the
        # crest fairing when it is standing on one.
        nonlocal n_made, n_skip
        p, n, tx, tq = _frame(x, q)
        w = abs(q) * _arc(x)
        foot = _fin_foot(x)
        if foot > 0.0 and w < foot + 0.0085:
            n_skip += 1
            _FIX_REFUSED.append((round(x, 4), round(q, 4), round(w, 4),
                                 round(foot, 4)))
            return
        ch = max(0.0, _crest_h(x, w))
        _fastener(acc, p + n * (_hfun(x, q) + ch + extra - 0.0005), n, tx, tq,
                  m_body=mat, m_head=mat, ang=ang)
        n_made += 1

    # Deck / shoulder longitudinal joints.  The DECK panel only starts at
    # X_DECK_F, so forward of that the joint has nothing under its inboard side
    # but the open cockpit; only the shoulder-side stud of the pair exists there.
    x = X_FWD - 0.030
    while x > X_SEAM_T + 0.030:
        for sgn in (1.0, -1.0):
            off = 0.0215 / _arc(x)
            place(x, sgn * (_qsplit(x) + off), 0.0002, 0, ang=0.7 * x)
            if x < X_DECK_F - 0.012:
                place(x, sgn * (_qsplit(x) - off), 0.0002, 0, ang=-0.5 * x)
        x -= 0.118
    # Transverse joints - a row of studs each side of the gap.  The q = 0 pair
    # used to sit on the spine, i.e. inside the fin (25 mm of blade over them at
    # X_SEAM_M, 110 mm at X_SEAM_T); the row now starts clear of both the fin
    # skirt and the crest fairing's edge.
    for xs in (X_SEAM_M, X_SEAM_T):
        for side in (1.0, -1.0):
            xx = xs + side * 0.0230
            for qq in (0.150, 0.290, 0.430, 0.580, 0.780, 0.910):
                place(xx, qq, 0.0002, 0, ang=1.1 * qq)
                place(xx, -qq, 0.0002, 0, ang=-1.1 * qq)
    # lower edge of the shoulder/tail panels
    x = X_FWD - 0.055
    while x > X_TAIL_E + 0.055:
        for sgn in (1.0, -1.0):
            place(x, sgn * (1.0 - 0.0180 / _arc(x)), 0.0002, 0, ang=0.9 * x)
        x -= 0.135
    # round the louvre plinths
    for bank in BANKS:
        xc, xh, _fs, _off, wh, ns, _nb = bank
        wc = _bank_wc(bank)
        for sgn in (1.0, -1.0):
            pts = _outline(xc, xh + 0.0205, wc, wh + 0.0205, ns, 10, sign=sgn)
            for (px, pq) in pts:
                place(px, pq, 0.0002, 1, ang=2.0 * px)
    # Roll-hoop crest.  This used to be a single row ON the spine with a guessed
    # 14.2 mm lift: the front stud stood 3.1 mm clear of the hoop band, two were
    # buried 20-39 mm inside the camera pod and three inside the crest itself.
    # It is now a pair either side of the spine at a fixed arc offset, seated on
    # the crest surface by place()'s _crest_h term, clear of the pod (37 mm) and
    # of the fin's leading edge.
    for i in range(5):
        xx = C.lerp(-0.384, -0.516, i / 4.0)
        for sgn in (1.0, -1.0):
            place(xx, sgn * _q_of_w(xx, 0.0425), 0.0002, 1, ang=1.7 * xx)
    print(f">> {P}fixings n={n_made} refused={n_skip}")
    return _emit(P + "fixings", acc, coll, ["SteelFastener", "AnodisedRed"],
                 smooth=28.0)


# =========================================================================== #
# 8.  entry point
# =========================================================================== #

def _diag():
    print(">> engine_cover diagnostics")
    worst = 0.0
    for x in (0.100, -0.176, -0.259, -0.360, -0.560, -0.940, -1.450,
              -1.705, -2.100, -2.240):
        a = _arc(x)
        crown = _sect(x, 0.0)
        low = _sect(x, 1.0)
        seam = _qsplit(x)
        d = crown.z - S.body_top_z(x)
        worst = min(worst, d) if worst else d
        print(f"   x={x:+.3f} arc={a:.4f} crown-body={1000*d:+.2f}mm "
              f"low=({low.y:.4f},{low.z:.4f}) seam q={seam:.3f} "
              f"w={seam*a:.3f} below_seam={(1.0-seam)*a:.3f}")
    print(f"   worst crown clearance over the body: {1000*worst:+.2f} mm")
    for bank in BANKS:
        xc, xh, _fs, _off, wh, ns, nb = bank
        wc = _bank_wc(bank)
        a = _arc(xc)
        print(f"   bank xc={xc} w=[{wc-wh:.3f},{wc+wh:.3f}] of arc {a:.3f} "
              f"seam_w={_qsplit(xc)*a:.3f} len={2*xh:.3f} n={nb} "
              f"plinth=[{wc-wh-0.030:.3f},{wc+wh+0.030:.3f}]")
    print(f"   mouth q half = {_q_of_w(MO_XC, MO_WH):.3f}, "
          f"width={2*MO_WH:.3f} m, x=[{MO_XC+MO_XH:.3f},{MO_XC-MO_XH:.3f}]")
    tip = _sect(X_TAIL_E, 0.0)
    lowt = _sect(X_TAIL_E, 1.0)
    print(f"   tail opening z=[{lowt.z:.4f},{tip.z:.4f}] halfw={lowt.y:.4f} "
          f"pipe z=[{Z_PIPE_TIP-R_PIPE:.4f},{Z_PIPE_TIP+R_PIPE:.4f}]")


def build(coll, ctx=None):
    _sec_cache.clear()
    _arc_cache.clear()
    _qs_cache.clear()
    _bwc.clear()
    _deck_cache.clear()
    _diag()
    made = []
    made.append(_shell(coll))
    made.append(_seams(coll))
    bh = _bulkhead(coll)
    if bh:
        made.append(bh)
    made.append(_duct(coll))
    made.append(_hoop(coll))
    made.append(_tcam(coll))
    made.append(_fin(coll))
    made.append(_pans(coll))
    made.append(_louvres(coll))
    made.extend(_tailduct(coll))
    made.append(_exhaust(coll))
    made.append(_fixings(coll))
    return made
