"""monocoque_b - the central body, built as a PANEL ASSEMBLY.

Philosophy
----------
A race car body is not one lofted skin. It is a set of separately moulded
panels - nose cone, chassis top, cockpit section, sidepod bodywork, lower
flanks, underpan, engine cover, tail fairing - each with its own laminate
thickness, each rolled over at its edges, each separated from its neighbour by
a real gap with a bonded backing strip visible behind it. The apertures here
are panel boundaries with rolled coamings and throats, not holes punched into a
blob afterwards.

Everything rides on the frozen reference surface in spec.BODY_STATIONS.
Lengthwise, the 13 station curves are resampled at 2 mm and FAIRED inside a
tolerance tube around the contract's own piecewise-linear polyline (D-MB13), so
curvature is spread over the whole length instead of being piled into a fillet
at each knot; the clamp back into the tube after every smoothing pass is what
keeps the skin provably on the contract. Across the section it is exactly the
contract's Catmull-Rom, with the top ~40 mm blended into a horizontal arrival at
the centreline so the mirrored surface has a radiused spine instead of a 70
degree crease (D-MB16). Apertures are cut by testing which grid cells fall
inside the outline and walking the boundary of that region (D-MB18), so a rim
vertex never travels more than about one cell and the skin around it is not
dragged into darts.

Measured departure from spec.body_surface_point, tools/devcheck.py at its
current 21 894-sample density (267 stations x 41 fracs x 2 sides):
    max_outside_apertures  0.0087 m   (tolerance 0.015, 58 % of budget)
    violations_outside     0
Left/right disagreement, measured as the difference in nearest-surface distance
between the two sides over a 41-frac sweep, is at most 0.010 mm anywhere in the
tail (it was 8.95 mm before D-MB38/39/40).
Inside the cockpit aperture six sample points (x = 0.6 / 0.3 / 0.0 at frac 0.92,
both sides) fall in open air because the reference surface there describes the
closed trough this module was asked to replace with a real hole.

Panels
------
    nose cone           x  2.000 .. 3.000   closed, blunt crash tip
    chassis fwd         x  0.960 .. 2.000
    chassis + cockpit   x -0.440 .. 0.960   cockpit + airbox apertures
    sidepod L/R         x -1.340 .. 0.960   inlet aperture
    lower flank L/R     x -1.712 .. 0.960
    underpan            x -2.455 .. 2.000
    engine cover        x -1.450 ..-0.440
    tail fairing        x -2.455 ..-1.450   + tail cap
plus the survival cell inside the cockpit aperture (ribbed tub floor, front and
rear bulkheads, side stringers), one merged Dzus quarter-turn object and one
merged backing-strip object. Every panel is the same 5.8 mm laminate so the
rolled edges match across every joint.

Defect log (each found in a render, fixed, re-rendered to confirm)
-----------------------------------------------------------------
    D-MB01  aperture outlines wound opposite to the index ring -> every lip
            tore into crossed quads (the "bird" on the roll hoop)
    D-MB02  throat extruded along fanning per-vertex normals -> self-intersect
    D-MB03  cockpit hole box reached row 0 of its panel -> torn black wedges
    D-MB04  snap/relax done in 3-D -> dented the skin off the spec surface
    D-MB05  throat scaled about the centroid of a saddle rim -> pinwheel
    D-MB06  rim frame read off dead grid neighbours -> shredded coaming
    D-MB07  Chebyshev relax wedges -> dart folded into the sidepod shoulder
    D-MB08  chassis/cover break sat on the steep roll-hoop face -> 15 mm gash
    D-MB09  0.9 x 0.75 mm panel lines were invisible
    D-MB10  nose closed with a fan off a 39 %-of-section ring -> flat disc tip
    D-MB11  cockpit coaming read as a painted outline, not a moulded rim
    D-MB12  airbox lip stood proud of the skyline as a duck bill
    D-MB13  curvature piled at the station knots -> low-frequency quilt on the
            deck; faired inside a tolerance tube instead
    D-MB14  min-step sweep from one corner -> cusp in the cockpit rim outline
    D-MB15  same sweep -> stair-step corrugation down the throat wall
    D-MB16  mirrored Catmull-Rom end tangent -> 70 deg crease down the spine
    D-MB17  harmonic blend decayed linearly -> dart at the edge of the band
    D-MB18  rectangular hole box -> 150 mm corner snaps, source of the darts
    D-MB19  rim outward direction taken from the snap vector, now from the
            outline normal
    D-MB20  airbox authored in plan -> knife point that tore the crown skyline
    D-MB21  cockpit was a rim, a throat and a lid; now a real survival cell
    D-MB22  chines faded in and out inside their own panel -> folds at joints
    D-MB23  blend band re-placed vertices on the bare surface, deleting the
            chine running through it -> hard step at the band edge
    D-MB24  fixed-psi feature columns crossed the moving panel columns and
            collapsed 59 % of a row -> 25 mm dent, left/right asymmetric
    D-MB25  rim pulled only 55 % onto its correspondence -> crystalline shards
            right around the coaming
    D-MB26  aperture arclength measured absolutely, not from the crest -> the
            outline drifted off the centreline as the section shrank
    D-MB27  surround fasteners sat under the coaming bead, half sunk
    D-MB28  the cell pan kept full flange height where it is 50 mm wide, so the
            two flanges folded through each other
    D-MB29  blending two monotone parameterisations still bunched the rim -
            eleven vertices inside four millimetres; now done in delta space
    D-MB30  bead scaled by smootherstep(w)/w, which peaks at 1.20 -> a 1.2 mm
            ring ridge three cells outboard of every rim
    D-MB31  4 300 zero-area quads per panel from collapsed feature columns;
            their zero normals were seeding spurious sharp edges along a chine
    D-MB32  a 4.2 mm raster cannot follow an outline that turns 6 mm of half
            width per mm of x; the four aperture tips get 1.2 mm rows
    D-MB33  the bead loop read each vertex's normal off the grid it was writing
            to, so the result depended on dict order - THE crystalline band
    D-MB34  sidepod inlet closed to a point at its fore end -> 0.2 mm slivers
    D-MB35  inlet's lower edge ran down the middle of the max-width chine
    D-MB36  rolled edges and return flanges were painted; past the crown of the
            roll they are now bare laminate, which is what a panel gap shows
    D-MB37  THE coaming shard band, and why D-MB25/30/33 never fixed it. The
            blend band was a harmonic field on the GRID INDEX - R cells wide,
            dropping a fixed amount per cell - on a grid whose cells run
            0.03 .. 5.96 mm. The same per-cell drop of a 5.8 mm bead therefore
            landed on cells differing 13x in metres, so the bead's flank slope
            alternated between 7 and 52 degrees from one cell to the next.
            Measured on the deck grid, adjacent faces disagreed by 15-25 deg on
            average through the band against 0.26 deg on the skin beside it.
            The weight is now the true distance in METRES from the outline and
            the bead's direction comes off the reference surface instead of off
            the grid. Same measurement after the fix: 0.9 - 4.6 deg.
    D-MB38  the underpan's floor lines were pinned 60 mm from the centreline on
            a belly that runs from 304 mm of half section to 30 mm, so past
            x = -2.36 their columns were outside the panel altogether
    D-MB39  psi_of_sring answers in [0, 2], so on a panel written as [-1/7, 1/7]
            every right-hand feature column came back as ~1.97 and was silently
            dropped - and the same wrap made make_cols size that half of the
            panel at the 160-column cap instead of 41
    D-MB40  the monotone guard was a forward sweep, so ONE out-of-order column
            dragged every column behind it onto the same parameter: the 10.7 mm
            dent in the tail belly, and the mechanism behind D-MB24 too. Fixed
            psi and fixed-fraction columns are now immovable and only metric
            columns are clamped, into the gap between them
    D-MB41  the tail cap opened with a duplicate ring 0.4 mm forward of X_TAIL,
            so it stood proud of the two panels it closes against
    D-MB42  slivers with no short edge survive dissolve_degenerate; they are now
            collapsed by AREA, and the rolled border is deduplicated below the
            weld distance so a panel corner cannot weld into a 3-face edge.
            415 non-manifold edges -> 16, 265 near-degenerate faces -> 30
    D-MB43  the sidepod inlet was six matte-black rings behind a good lip - an
            unlit void. Lacquered carbon walls, finer rings, and a lit step in
            front of a matte core.

Coordinates: +X forward (tip x=+3.000), +Y car left, +Z up, contact plane z=0.
"""

import math

import bmesh
import bpy
from mathutils import Vector

import common as C
import spec as S

try:                                    # Blender ships numpy; keep a fallback
    import numpy as _np
except Exception:                       # pragma: no cover
    _np = None

NAME = "monocoque_b"
P = "MB_"

DENS = 1.0                # global mesh density knob; 1.0 ships
ROW_STEP = 0.0055
COL_STEP = 0.0042

# --------------------------------------------------------------------------- #
# principal panel breaks
# --------------------------------------------------------------------------- #

X_TIP = 3.000
X_NOSE_J = 2.000          # nose cone / chassis joint (matches the livery line)
X_SP_LE = 0.960           # front edge of the sidepod bodywork
X_TUB_R = -0.440          # chassis rear edge / engine cover front edge
# D-MB08: the chassis/cover break used to sit at x=-0.222, half way up the
# roll-hoop front face where dz/dx is nearly 2. A 7 mm gap in x opens a 15 mm
# gash along the surface there and the joint read as a torn hole. The survival
# cell carries the roll hoop and the airbox on a real car anyway, so the break
# moved behind the crown where the deck is almost flat.
X_SP_TE = -1.340          # sidepod bodywork trailing edge
X_COVER_J = -1.450        # engine cover / tail fairing joint
X_TAIL = -2.455           # start of the tail closing cap

GAP = 0.0018              # panel-to-panel gap
T_SKIN = 0.0058
FLANGE = 0.013            # return flange behind every rolled edge

# D-MB45: a CLOSED butt joint - the nose cone to the chassis. See the defect log.
# The two skins stop SEAM_HX either side of the joint station and their lips roll
# outward by SEAM_R > SEAM_HX, so the lips MEET on the joint plane 1.3 mm under
# the skin. What is left outside is a 1.8 mm shut line with a bottom to it, not a
# 7.6 mm dish over a hole. SEAM_R carries margin because the lip rolls along the
# SURFACE, not along x: where the section is steeply tapered only its x-component
# closes the gap.
SEAM_HX = GAP * 0.5
SEAM_R = 0.0013

PK = [k / 7.0 for k in range(8)]
# 0 belly centre | 1 belly edge | 2 undercut waist | 3 max width
# 4 sidepod shoulder | 5 tub side | 6 tub shoulder | 7 centre top


# =========================================================================== #
# 1.  lengthwise interpolation: tolerance-tube faired station curves
# =========================================================================== #

_XK = [s[0] for s in S.BODY_STATIONS][::-1]
_VK = [list(s[1:]) for s in S.BODY_STATIONS][::-1]
_NK = len(_XK)
_NC = 13


def _smoother(t):
    if t <= 0.0:
        return 0.0
    if t >= 1.0:
        return 1.0
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)


# D-MB13: the previous scheme interpolated linearly between stations with a
# solved C2 corner fillet at each knot. It measured 2.0 mm off the contract, but
# every scrap of its curvature lived in a short window either side of a knot and
# the spans in between were dead flat. Under gloss that reads as a QUILT - 220 mm
# flat panels separated by soft ridges - and the highlight terminator visibly
# wobbles as it crosses each one. That was the one thing the losing module did
# better, and it is fixed here by fairing instead of filleting.
#
# Each of the 13 station curves is now resampled at 2 mm and faired inside a
# tolerance tube around the contract's own piecewise-linear polyline: a wide box
# blur, then a hard clamp back into the tube, repeated. The clamp is what makes
# it safe - the result provably cannot leave the tube, so the surface stays on
# the contract - while the blur spreads the curvature over the whole length.
# The tube closes to zero at the nose tip and the tail so those land exactly.
# A plain C2 cubic spline through the stations was tried first and rings badly:
# it overshoots the roll-hoop data by 57 mm at x = -0.014.
FAIR_DX = 0.0020
FAIR_TOL = 0.0052         # tube half width, metres
FAIR_END = 0.060          # taper the tube shut over this much at each end
FAIR_BOX = 13             # box-blur half width in samples (54 mm kernel)
FAIR_ITER = 300

_TN = int(round((_XK[-1] - _XK[0]) / FAIR_DX)) + 1
_TSTEP = (_XK[-1] - _XK[0]) / (_TN - 1)
_TX = [_XK[0] + i * _TSTEP for i in range(_TN)]


def _lin_table():
    out = [[0.0] * _NC for _ in range(_TN)]
    j = 0
    for i, x in enumerate(_TX):
        while j < _NK - 2 and _XK[j + 1] < x:
            j += 1
        h = _XK[j + 1] - _XK[j]
        t = 0.0 if h <= 0.0 else min(max((x - _XK[j]) / h, 0.0), 1.0)
        row = out[i]
        a, b = _VK[j], _VK[j + 1]
        for k in range(_NC):
            row[k] = a[k] + (b[k] - a[k]) * t
    return out


def _tol_vector():
    x0, x1 = _TX[0], _TX[-1]
    return [FAIR_TOL * _smoother(min(x - x0, x1 - x) / FAIR_END) for x in _TX]


def _box_np(a, w):
    k = 2 * w + 1
    pad = _np.concatenate((_np.repeat(a[:, :1], w, 1), a,
                           _np.repeat(a[:, -1:], w, 1)), 1)
    c = _np.cumsum(pad, axis=1)
    c = _np.concatenate((_np.zeros((a.shape[0], 1)), c), 1)
    return (c[:, k:] - c[:, :-k]) / k


def _box_py(rows, w):
    n = len(rows)
    k = 2 * w + 1
    out = [[0.0] * _NC for _ in range(n)]
    for c in range(_NC):
        acc = rows[0][c] * (w + 1)
        for i in range(1, w):
            acc += rows[min(i, n - 1)][c]
        for i in range(n):
            acc += rows[min(i + w, n - 1)][c]
            acc -= rows[max(i - w - 1, 0)][c]
            out[i][c] = acc / k
    return out


def _fair_table():
    lin = _lin_table()
    tol = _tol_vector()
    if _np is not None:
        a = _np.asarray(lin, dtype=_np.float64).T.copy()
        base = _np.asarray(lin, dtype=_np.float64).T
        tv = _np.asarray(tol, dtype=_np.float64)[None, :]
        lo, hi = base - tv, base + tv
        for _ in range(FAIR_ITER):
            a = _box_np(_box_np(_box_np(a, FAIR_BOX), FAIR_BOX), FAIR_BOX)
            _np.clip(a, lo, hi, out=a)
        return [tuple(r) for r in a.T.tolist()]
    cur = [list(r) for r in lin]
    for _ in range(60):
        cur = _box_py(_box_py(cur, FAIR_BOX), FAIR_BOX)
        for i in range(_TN):
            t = tol[i]
            b = lin[i]
            r = cur[i]
            for c in range(_NC):
                r[c] = min(max(r[c], b[c] - t), b[c] + t)
    return [tuple(r) for r in cur]


_TB = _fair_table()


def _station13(x):
    f = (x - _TX[0]) / _TSTEP
    if f <= 0.0:
        return list(_TB[0])
    if f >= _TN - 1:
        return list(_TB[-1])
    i = int(f)
    t = f - i
    b = _TB[i]
    c = _TB[i + 1]
    a = _TB[i - 1] if i > 0 else b
    d = _TB[i + 2] if i + 2 < _TN else c
    t2 = t * t
    t3 = t2 * t
    return [0.5 * (2.0 * b[k] + (c[k] - a[k]) * t
                   + (2.0 * a[k] - 5.0 * b[k] + 4.0 * c[k] - d[k]) * t2
                   + (3.0 * b[k] - a[k] - 3.0 * c[k] + d[k]) * t3)
            for k in range(_NC)]


# =========================================================================== #
# 2.  section profile - the exact spec half section, sampled dense
# =========================================================================== #

NP = 7 * 80 + 1
_KI = [80 * k for k in range(8)]

# D-MB16: the contract's half section is a Catmull-Rom that arrives at the top
# centre travelling along the chord from the tub shoulder - 35 degrees above
# horizontal over the engine cover. Mirrored about y = 0 that is a 70 degree
# included crease running the whole length of the spine, and it shows in the
# plan view as a razor highlight down the centreline. The last stretch of the
# half section is blended into a cubic that arrives at the crest horizontally,
# so the mirrored surface is smooth there and the spine becomes a real radius.
# The apex itself never moves, so spec.body_top_z is untouched; the blend is
# C2 at its forward end and its length is solved to cap the departure.
CREST_MAX = 0.0038
CREST_SR_MIN = 0.014
CREST_SR_MAX = 0.052


def _round_crest(y, z):
    """Blend the top of a half section into a horizontal arrival at y = 0."""
    n = len(y)
    s = [0.0] * n
    for i in range(1, n):
        s[i] = s[i - 1] + math.hypot(y[i] - y[i - 1], z[i] - z[i - 1])
    tot = s[-1]
    if tot < 1e-6:
        return
    dy = y[n - 1] - y[n - 9]
    dz = z[n - 1] - z[n - 9]
    if -dy < 1e-9:
        return
    th = abs(math.atan2(dz, -dy))
    sr = CREST_MAX / (0.20 * max(th, 0.02))
    sr = min(max(sr, CREST_SR_MIN), CREST_SR_MAX, 0.30 * tot)
    for _try in range(3):
        s0 = tot - sr
        ia = 0
        for i in range(n - 1, -1, -1):
            if s[i] <= s0:
                ia = i
                break
        if ia >= n - 4:
            return
        ay, az = y[ia], z[ia]
        ty = y[min(ia + 4, n - 1)] - y[max(ia - 4, 0)]
        tz = z[min(ia + 4, n - 1)] - z[max(ia - 4, 0)]
        tm = math.hypot(ty, tz)
        if tm < 1e-12:
            return
        ty /= tm
        tz /= tm
        by, bz = 0.0, z[n - 1]
        ch = math.hypot(ay - by, az - bz)
        m0y, m0z = ty * ch, tz * ch
        m1y, m1z = -ch, 0.0
        worst = 0.0
        buf = []
        for i in range(ia, n):
            u = min(1.0, max(0.0, (s[i] - s[ia]) / (tot - s[ia])))
            u2 = u * u
            u3 = u2 * u
            h00 = 2.0 * u3 - 3.0 * u2 + 1.0
            h10 = u3 - 2.0 * u2 + u
            h01 = -2.0 * u3 + 3.0 * u2
            h11 = u3 - u2
            hy = h00 * ay + h10 * m0y + h01 * by + h11 * m1y
            hz = h00 * az + h10 * m0z + h01 * bz + h11 * m1z
            w = _smoother(u)
            ny = y[i] + w * (hy - y[i])
            nz = z[i] + w * (hz - z[i])
            worst = max(worst, math.hypot(ny - y[i], nz - z[i]))
            buf.append((i, ny, nz))
        if worst <= CREST_MAX * 1.08 or sr <= CREST_SR_MIN + 1e-6:
            for (i, ny, nz) in buf:
                y[i] = ny
                z[i] = nz
            return
        sr = max(CREST_SR_MIN, sr * max(0.45, CREST_MAX / worst))


class _Prof(object):

    def __init__(self, x):
        v = _station13(x)
        ctrl = [(0.0, v[1]), (v[0], v[1]), (v[2], v[3]), (v[4], v[5]),
                (v[6], v[7]), (v[8], v[9]), (v[10], v[11]), (0.0, v[12])]
        pts = C.catmull_rom(ctrl, NP)
        self.y = [p[0] for p in pts]
        self.z = [p[1] for p in pts]
        self.y[0] = 0.0
        self.y[-1] = 0.0
        _round_crest(self.y, self.z)
        self.y[-1] = 0.0
        s = [0.0] * NP
        for i in range(1, NP):
            s[i] = s[i - 1] + math.hypot(self.y[i] - self.y[i - 1],
                                         self.z[i] - self.z[i - 1])
        self.s = s
        self.half = s[-1]
        self.ks = [s[i] for i in _KI]
        ny = [0.0] * NP
        nz = [0.0] * NP
        for i in range(NP):
            a = max(0, i - 1)
            b = min(NP - 1, i + 1)
            ty = self.y[b] - self.y[a]
            tz = self.z[b] - self.z[a]
            m = math.hypot(ty, tz) or 1.0
            ny[i] = tz / m
            nz[i] = -ty / m
        self.ny = ny
        self.nz = nz

    def at(self, u):
        f = min(max(u, 0.0), 1.0) * (NP - 1)
        i = int(f)
        if i >= NP - 1:
            i = NP - 2
        t = f - i
        y = self.y[i] + (self.y[i + 1] - self.y[i]) * t
        z = self.z[i] + (self.z[i + 1] - self.z[i]) * t
        ny = self.ny[i] + (self.ny[i + 1] - self.ny[i]) * t
        nz = self.nz[i] + (self.nz[i + 1] - self.nz[i]) * t
        m = math.hypot(ny, nz) or 1.0
        return y, z, ny / m, nz / m

    def s_at(self, u):
        f = min(max(u, 0.0), 1.0) * (NP - 1)
        i = int(f)
        if i >= NP - 1:
            i = NP - 2
        return self.s[i] + (self.s[i + 1] - self.s[i]) * (f - i)

    def u_at_s(self, sv):
        if sv <= 0.0:
            return 0.0
        if sv >= self.half:
            return 1.0
        lo, hi = 0, NP - 1
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if self.s[mid] <= sv:
                lo = mid
            else:
                hi = mid
        d = self.s[lo + 1] - self.s[lo]
        t = 0.0 if d < 1e-12 else (sv - self.s[lo]) / d
        return (lo + t) / (NP - 1)

    def u_at_y(self, yv, u0, u1):
        lo = int(u0 * (NP - 1))
        hi = int(u1 * (NP - 1))
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if self.y[mid] >= yv:
                lo = mid
            else:
                hi = mid
        d = self.y[lo] - self.y[lo + 1]
        t = 0.0 if abs(d) < 1e-12 else (self.y[lo] - yv) / d
        return (lo + min(max(t, 0.0), 1.0)) / (NP - 1)

    def u_at_z(self, zv, u0, u1):
        lo = int(u0 * (NP - 1))
        hi = int(u1 * (NP - 1))
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if self.z[mid] <= zv:
                lo = mid
            else:
                hi = mid
        d = self.z[lo + 1] - self.z[lo]
        t = 0.0 if abs(d) < 1e-12 else (zv - self.z[lo]) / d
        return (lo + min(max(t, 0.0), 1.0)) / (NP - 1)


_PC = {}


def prof(x):
    k = int(round(x * 1e5))
    p = _PC.get(k)
    if p is None:
        p = _Prof(k * 1e-5)
        _PC[k] = p
    return p


def psi_us(psi):
    t = psi % 2.0
    return (t, 1.0) if t <= 1.0 else (2.0 - t, -1.0)


def sring(pf, psi):
    u, sd = psi_us(psi)
    return pf.s_at(u) if sd > 0 else 2.0 * pf.half - pf.s_at(u)


def psi_of_sring(pf, sv):
    sv = sv % (2.0 * pf.half)
    if sv <= pf.half:
        return pf.u_at_s(sv)
    return 2.0 - pf.u_at_s(2.0 * pf.half - sv)


def spt(x, psi, off=0.0):
    pf = prof(x)
    u, sd = psi_us(psi)
    y, z, ny, nz = pf.at(u)
    return (x, sd * (y + off * ny), z + off * nz)


def psi_shift(pf, psi, dm):
    return psi_of_sring(pf, sring(pf, psi) + dm)


# =========================================================================== #
# 3.  relief features
# =========================================================================== #

class Crease(object):
    """A hard chine.

    Normal displacement is sag*(1 - |d|/w)^2 - exactly the departure of a
    tangent line from a circular arc - so the flanks leave the reference
    surface tangentially and the only sharp thing is the tip, which is itself
    rounded to a 1.6 mm radius. Included break angle is a constant ~20 deg.
    """

    SAG_RATIO = 0.088
    TIP_R = 0.0016

    def __init__(self, psi, x0, x1, fade=0.11, wmax=0.032, scale=1.0):
        self.psi = psi
        self.x0, self.x1 = min(x0, x1), max(x0, x1)
        self.fade = fade
        self.wmax = wmax
        self.scale = scale
        self.psif = None

    def window(self, pf):
        u, _sd = psi_us(self.psi)
        k = min(max(int(round(u * 7.0)), 0), 7)
        prev = pf.ks[k] - pf.ks[k - 1] if k > 0 else 1.0
        nxt = pf.ks[k + 1] - pf.ks[k] if k < 7 else 1.0
        return min(self.wmax, 0.34 * min(prev, nxt))

    def amp(self, x):
        return (_smoother((x - self.x0) / self.fade)
                * _smoother((self.x1 - x) / self.fade) * self.scale)

    def row(self, x, pf):
        a = self.amp(x)
        if a <= 1e-6:
            return None
        w = self.window(pf)
        p = self.psif(x) if self.psif is not None else self.psi
        return (a * self.SAG_RATIO * w, w, sring(pf, p))

    @staticmethod
    def apply(rc, sp):
        sag, w, base = rc
        d = sp - base
        ad = math.sqrt(d * d + Crease.TIP_R * Crease.TIP_R) - Crease.TIP_R
        if ad >= w:
            return 0.0
        f = 1.0 - ad / w
        return sag * f * f

    def ds_list(self):
        fr = [0.026, 0.062, 0.108, 0.170, 0.262, 0.400, 0.590, 0.810, 1.0]
        out = [0.0]
        for f in fr:
            out.append(f)
            out.append(-f)
        return sorted(out)


class _Groove(object):
    """1.3 mm wide, 1.0 mm deep, 0.24 mm walls.

    D-MB09: at 0.9 x 0.75 mm with 0.28 mm ramps the seams were a whisper - the
    tub hatch outline read as a faint sheen change rather than a line. Widened
    to the top of the brief's range and given near-vertical walls so the groove
    holds a shadow at a grazing angle."""

    def __init__(self, hw=0.00065, depth=0.00098, wall=0.00024):
        self.hw = hw
        self.depth = depth
        self.wall = wall

    def value(self, d):
        a = abs(d)
        if a <= self.hw:
            return -self.depth
        if a >= self.hw + self.wall:
            return 0.0
        return -self.depth * (1.0 - (a - self.hw) / self.wall)

    def offsets(self):
        h, w = self.hw, self.wall
        return [-h - w - 0.0004, -h - w, -h - w * 0.5, -h, 0.0,
                h, h + w * 0.5, h + w, h + w + 0.0004]


GRV = _Groove()


class LongLine(object):
    """Fore-aft recessed panel line at a metric offset from a profile knot."""

    def __init__(self, psi, ds0, x0, x1, fade=0.030, g=GRV):
        self.psi = psi
        self.ds0 = ds0
        self.x0, self.x1 = min(x0, x1), max(x0, x1)
        self.fade = fade
        self.g = g
        self.psif = None

    def row(self, x, pf):
        a = (_smoother((x - self.x0) / self.fade)
             * _smoother((self.x1 - x) / self.fade))
        if a <= 1e-6:
            return None
        p = self.psif(x) if self.psif is not None else self.psi
        return (a, sring(pf, p) + self.ds0, self.g)

    @staticmethod
    def apply(rc, sp):
        a, base, g = rc
        return a * g.value(sp - base)

    def ds_list(self):
        return [self.ds0 + d for d in self.g.offsets()]


class CrossLine(object):
    """Recessed panel line running around the section at a fixed x."""

    def __init__(self, x, ps0, ps1, fade=0.025, g=GRV):
        self.x = x
        self.ps0, self.ps1 = ps0, ps1
        self.fade = fade
        self.g = g

    def off(self, x, psi):
        a = (_smoother((psi - self.ps0) / self.fade)
             * _smoother((self.ps1 - psi) / self.fade))
        if a <= 1e-6:
            return 0.0
        return a * self.g.value(x - self.x)

    def rows(self):
        return [self.x + d for d in self.g.offsets()]


# =========================================================================== #
# 4.  column and row layout
# =========================================================================== #

class Col(object):
    """A grid column. 'p' sits at a fixed psi; 's' at a metric arclength from
    an anchor knot (so a 0.9 mm groove stays 0.9 mm at every station); 'm'
    floats at a fixed fraction between two moving panel edges."""

    def __init__(self, kind, psi=0.0, anchor=0.0, ds=0.0, lo=None, hi=None,
                 f=0.0, anchorf=None, sub2=False):
        self.kind = kind
        self.psi = psi
        self.anchor = anchor
        self.ds = ds
        self.lo = lo
        self.hi = hi
        self.f = f
        self.anchorf = anchorf
        # D-MB39: psi_of_sring always answers in [0, 2]. A panel that straddles
        # the belly centreline is written as [-1/7, +1/7], so an 's' column on
        # its RIGHT half comes back as ~1.97 and compares as if it were on the
        # far side of the whole ring. Panels in that representation set sub2 and
        # get the answer in their own half-open convention.
        self.sub2 = sub2

    def eval_psi(self, x, pf):
        if self.kind == "p":
            return self.psi
        if self.kind == "s":
            a = self.anchorf(x) if self.anchorf is not None else self.anchor
            p = psi_of_sring(pf, sring(pf, a) + self.ds)
            return p - 2.0 if (self.sub2 and p > 1.0) else p
        a, b = self.lo(x), self.hi(x)
        return a + (b - a) * self.f


def make_cols(ps_lo, ps_hi, xs, feats=(), step=None, drop_last=False):
    """Ordered columns spanning [ps_lo, ps_hi] of the ring."""
    step = (step or COL_STEP) / max(DENS, 1e-3)
    xr = xs[::max(1, len(xs) // 9)] + [xs[-1]]
    fcols = []
    for ft in feats:
        if isinstance(ft, Crease):
            w = max(ft.window(prof(x)) for x in xr)
            dss = [f * w * 1.04 for f in ft.ds_list()]
        else:
            dss = ft.ds_list()
        for d in dss:
            fcols.append(Col("s", anchor=ft.psi, ds=d,
                             anchorf=getattr(ft, "psif", None)))

    knots = [ps_lo, ps_hi]
    for k in range(8):
        for pv in (PK[k], 2.0 - PK[k]):
            if ps_lo - 1e-9 <= pv <= ps_hi + 1e-9:
                knots.append(pv)
    knots = sorted(set(round(v, 9) for v in knots))

    # D-MB39: a panel that straddles the belly centreline is written with a
    # NEGATIVE lower psi, and sring() answers modulo the whole ring, so the span
    # of the interval [-1/7, 0] came back as the long way round - 2.23 m instead
    # of 0.17 m. The underpan therefore got 160 columns (the hard cap) on its
    # right half and 41 on its left: a 4x left/right density difference baked
    # into the one panel that is supposed to be perfectly mirror-symmetric.
    sub2 = ps_lo < -1e-9
    fill = []
    for a, b in zip(knots, knots[1:]):
        amax = 0.0
        for x in xr:
            pf = prof(x)
            d = abs(sring(pf, b) - sring(pf, a))
            amax = max(amax, min(d, 2.0 * pf.half - d))
        n = min(max(2, int(math.ceil(amax / step))), 160)
        for i in range(n):
            fill.append(Col("p", psi=a + (b - a) * i / n))
    fill.append(Col("p", psi=ps_hi))

    ref = xs[len(xs) // 2]
    pfr = prof(ref)
    keep = []
    for c in fcols:
        c.sub2 = sub2
        p = c.eval_psi(ref, pfr)
        if ps_lo - 1e-9 <= p <= ps_hi + 1e-9:
            keep.append((p, sring(pfr, p), c))
    keep.sort(key=lambda t: t[0])
    guard = 0.55 * step
    out = []
    for c in fill:
        sv = sring(pfr, c.psi)
        if all(abs(sv - k[1]) >= guard for k in keep):
            out.append((c.psi, c))
    out.extend([(k[0], k[2]) for k in keep])
    out.sort(key=lambda t: t[0])
    cols = [c for _p, c in out]
    if drop_last and len(cols) > 2 and abs(cols[-1].psi - ps_hi) < 1e-9:
        cols = cols[:-1]
    return cols


def mfeats(feats, lo, hi, xref):
    """Re-anchor relief features onto a pair of moving panel edges.

    D-MB24: a panel whose psi range changes with x - the sidepod tapers to
    nothing at x = -1.34, the engine cover flares 2.6x on its way to the tail -
    carried its chines and panel lines at FIXED psi while its grid columns moved
    with the edges. Past the point where the two disagree the feature columns
    cross the moving ones, and build_panel's monotone guard then collapsed up to
    59 % of a row into a single parameter: the surface between two surviving
    columns became one long chord and dented 25 mm off the reference. Because
    the guard only ever pushes forward, the collapse was worse on one side than
    the other, which is why the flank came out visibly left/right asymmetric.
    A feature on a moving panel now moves with it, so nothing can cross.
    """
    a0, b0 = lo(xref), hi(xref)
    span = b0 - a0
    for ft in feats:
        f = (ft.psi - a0) / span
        ft.psif = (lambda fr: (lambda x: lo(x) + (hi(x) - lo(x)) * fr))(f)
    return feats


def to_moving(cols, lo, hi, xref):
    """Re-anchor fixed-psi columns onto a pair of moving panel edges."""
    a0, b0 = lo(xref), hi(xref)
    out = []
    for c in cols:
        if c.kind == "p":
            out.append(Col("m", lo=lo, hi=hi, f=(c.psi - a0) / (b0 - a0),
                           psi=c.psi))
        else:
            out.append(c)
    return out


def _order_cols(raw, anch, eps=1.0e-6):
    """Make a row's column parameters strictly increasing WITHOUT cascading.

    D-MB40: the old guard was a single forward sweep - `if p <= prev: p = prev`.
    One column out of order therefore poisoned every column behind it, all the
    way to the edge of the panel. That is the mechanism behind D-MB24 and behind
    the tail asymmetry: a metric feature column at a fixed offset from an anchor
    drifts outboard as the section shrinks, and at the tail the underpan's floor
    line evaluated to psi 0.208 on a panel that ends at 0.143, so the sweep
    dragged the outer three quarters of the belly onto that one parameter. The
    surface between the two surviving columns became a single chord and dented
    10.7 mm off the reference. It only showed on the LEFT because the right
    line's columns were being dropped by the psi wrap (D-MB39), which turned a
    symmetric fault into an 8.95 mm left/right disagreement.

    A fixed-psi or fixed-fraction column cannot cross anything - those two kinds
    define the panel and are treated as immovable. Only the metric columns are
    clamped, and only into the gap between the two immovable ones on either side
    of them, so a feature that has wandered off the end of its own panel costs a
    sliver quad instead of a quarter of the panel. Where a feature has wandered
    that far it has always faded to zero amplitude anyway - it is precisely
    because the section got too small to hold the offset that it wandered.
    """
    n = len(raw)
    out = list(raw)
    prev = -1.0e18
    for i in range(n):
        if anch[i]:
            if out[i] <= prev + eps:
                out[i] = prev + eps
            prev = out[i]
    i = 0
    while i < n:
        if anch[i]:
            i += 1
            continue
        j = i
        while j < n and not anch[j]:
            j += 1
        lo = out[i - 1] if i > 0 else out[j] - 1.0 if j < n else 0.0
        hi = out[j] if j < n else lo + 1.0
        m = j - i
        p2 = lo
        for k in range(m):
            v = min(max(out[i + k], p2 + eps), hi - eps * (m - k))
            if v <= p2:
                v = p2 + eps
            out[i + k] = v
            p2 = v
        i = j
    return out


def make_rows(x0, x1, step=None, extra=(), dense=(), lines=()):
    step = (step or ROW_STEP) / max(DENS, 1e-3)
    n = max(2, int(math.ceil(abs(x1 - x0) / step)))
    xs = [x0 + (x1 - x0) * i / n for i in range(n + 1)]
    for e in extra:
        if min(x0, x1) < e < max(x0, x1):
            xs.append(e)
    for ln in lines:
        for v in ln.rows():
            if min(x0, x1) < v < max(x0, x1):
                xs.append(v)
    for (a, b, st) in dense:
        a2, b2 = max(min(x0, x1), min(a, b)), min(max(x0, x1), max(a, b))
        if b2 <= a2:
            continue
        m = int(math.ceil((b2 - a2) / (st / max(DENS, 1e-3))))
        for i in range(m + 1):
            xs.append(a2 + (b2 - a2) * i / m)
    xs = sorted(set(round(v, 7) for v in xs))
    out = [xs[0]]
    for v in xs[1:]:
        if v - out[-1] > 1.2e-5:
            out.append(v)
    return out


# =========================================================================== #
# 5.  mesh helpers
# =========================================================================== #

def _mk(name, verts, faces, coll, mats, mids=None, angle=38.0, ref=None):
    if name in bpy.data.objects:
        old = bpy.data.objects[name]
        od = old.data
        bpy.data.objects.remove(old, do_unlink=True)
        if od and od.users == 0 and isinstance(od, bpy.types.Mesh):
            bpy.data.meshes.remove(od)
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], [tuple(f) for f in faces])
    me.validate(verbose=False)
    me.update()

    bm = bmesh.new()
    bm.from_mesh(me)
    # D-MB31: wherever a feature column and a plain column happened to coincide
    # at some station, build_panel's monotone guard pushed one onto the other and
    # left a quad with two pairs of identical corners - 4 300 of them on the
    # cockpit panel, 8 000 on each sidepod. They render as nothing, but a
    # zero-area face has a zero normal, and shade_auto_smooth compares face
    # normals to decide which edges are sharp: every one of them was seeding a
    # spurious hard edge along a chine. Material indices are set in bmesh so the
    # weld below is free to change the face count.
    if mids is not None and len(mats) > 1 and len(mids) == len(bm.faces):
        bm.faces.ensure_lookup_table()
        for f, m in zip(bm.faces, mids):
            f.material_index = m
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if ref is not None:
        rp, rn = Vector(ref[0]), Vector(ref[1])
        best, bd = None, 1e18
        for f in bm.faces:
            d = (f.calc_center_median() - rp).length_squared
            if d < bd:
                bd, best = d, f
        if best is not None and best.normal.dot(rn) < 0.0:
            bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=3.0e-5)
    # D-MB42: dissolve_degenerate only collapses edges SHORTER than dist, and a
    # sliver 4 mm long and a micron wide has no short edge - it survives with an
    # area of 1e-11 m2 and a normal that is pure round-off. Those are what seed
    # spurious sharp edges (D-MB31 again, from the other direction). The narrow
    # ones are now collapsed by area: take the shortest edge of every face under
    # a square micron and collapse it, twice, which is enough to converge. The
    # 60 um dissolve is still less than half the 120 um gap between the columns
    # that build a groove wall, so no authored feature can be eaten.
    bmesh.ops.dissolve_degenerate(bm, dist=6.0e-5, edges=bm.edges)
    for _ in range(2):
        bm.faces.ensure_lookup_table()
        kill = set()
        for f in bm.faces:
            if f.calc_area() >= 8.0e-9:
                continue
            e0, l0 = None, 1e18
            for e in f.edges:
                el = e.calc_length()
                if el < l0:
                    e0, l0 = e, el
            if e0 is not None:
                kill.add(e0)
        if not kill:
            break
        bmesh.ops.collapse(bm, edges=list(kill), uvs=False)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1.0e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    me.update()

    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    for i, mn in enumerate(mats):
        C.assign(ob, S.mat(mn), slot=i)
    C.shade_auto_smooth(ob, angle)
    return ob


def _grid_n(grid, i, j, nr, nc, wrap=False):
    a = grid[min(i + 1, nr - 1)][j]
    b = grid[max(i - 1, 0)][j]
    if wrap:
        c = grid[i][(j + 1) % nc]
        d = grid[i][(j - 1) % nc]
    else:
        c = grid[i][min(j + 1, nc - 1)]
        d = grid[i][max(j - 1, 0)]
    n = (Vector(c) - Vector(d)).cross(Vector(a) - Vector(b))
    if n.length < 1e-12:
        return Vector((0.0, 0.0, 1.0))
    return n.normalized()


def closed_spline(pts, n):
    """Periodic Catmull-Rom through a closed list of 2-tuples."""
    m = len(pts)
    out = []
    for i in range(n):
        f = m * i / float(n)
        seg = int(f)
        t = f - seg
        p0 = pts[(seg - 1) % m]
        p1 = pts[seg % m]
        p2 = pts[(seg + 1) % m]
        p3 = pts[(seg + 2) % m]
        t2, t3 = t * t, t * t * t
        out.append(tuple(
            0.5 * ((2 * p1[k]) + (-p0[k] + p2[k]) * t
                   + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t2
                   + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t3)
            for k in range(2)))
    return out


def _signed_area(pts):
    a = 0.0
    n = len(pts)
    for k in range(n):
        p = pts[k]
        q = pts[(k + 1) % n]
        a += p[0] * q[1] - q[0] * p[1]
    return 0.5 * a


def _curve_frame(curve):
    """Cumulative arclength table + O(1) evaluator for a closed 2-D polyline."""
    m = len(curve)
    acc = [0.0] * (m + 1)
    for k in range(m):
        a = curve[k]
        b = curve[(k + 1) % m]
        acc[k + 1] = acc[k] + math.hypot(b[0] - a[0], b[1] - a[1])
    L = acc[m]

    def at(sv):
        sv %= L
        lo, hi = 0, m
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if acc[mid] <= sv:
                lo = mid
            else:
                hi = mid
        dl = acc[lo + 1] - acc[lo]
        t = 0.0 if dl < 1e-12 else (sv - acc[lo]) / dl
        a = curve[lo]
        b = curve[(lo + 1) % m]
        return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)

    return acc, L, at


RING_SMOOTH = 30


def _resample_ring(ring_pos, curve):
    """Lay a hole's boundary ring evenly along its aperture outline.

    D-MB14/D-MB15: the first version snapped each ring vertex to its nearest
    point on the outline, unwrapped the arclengths, forced them monotone with a
    minimum step by sweeping FORWARD from index 0, and relaxed only the interior
    of that sweep. Both operations single out whichever vertex the walk happened
    to start at, so the rim outline kinked into a cusp there, the plan view came
    out very slightly non-mirrored, and the uneven spacing the min-step sweep
    left behind extruded into visible stair-steps down the throat wall.

    D-MB25/D-MB29: the second version parameterised the ring by its own
    arclength and pulled it toward the nearest-point correspondence. Both are
    monotone on their own, but a weighted blend of two monotone sequences can
    still bunch, and it did - eleven rim vertices inside four millimetres beside
    the cockpit, which is what shattered the coaming into shards.

    This works in DELTA space, which cannot bunch by construction. The spacing
    between consecutive nearest-point arclengths is floored, smoothed right
    around the closed loop, and renormalised to the outline's length, then
    integrated back up. Smoothing a set of positive numbers leaves them
    positive, so the result is strictly increasing however jagged the raster
    boundary underneath it was: the staircase noise is averaged away (even
    spacing for the throat) while the large-scale correspondence survives (small
    displacement, no dragged skin). The final rotation is set by the circular
    mean of the residuals, so nothing distinguishes one vertex from another and
    a mirror-symmetric ring gives a mirror-symmetric rim.
    """
    n = len(ring_pos)
    if _signed_area(curve) * _signed_area(ring_pos) < 0.0:
        curve = list(curve)[::-1]
    acc, L, at = _curve_frame(curve)
    m = len(curve)

    near = [0.0] * n
    for k in range(n):
        px, py = ring_pos[k][0], ring_pos[k][1]
        bs, bd = 0.0, 1e18
        for q in range(m):
            ax, ay = curve[q]
            bx, by = curve[(q + 1) % m]
            ex, ey = bx - ax, by - ay
            l2 = ex * ex + ey * ey
            t = 0.0 if l2 < 1e-14 else max(0.0, min(1.0, ((px - ax) * ex
                                                          + (py - ay) * ey) / l2))
            qx, qy = ax + ex * t, ay + ey * t
            dd = (qx - px) ** 2 + (qy - py) ** 2
            if dd < bd:
                bd = dd
                bs = acc[q] + math.sqrt(l2) * t
        near[k] = bs

    # spacing between consecutive nearest points, wrapped into (-L/2, L/2]
    dl = [0.0] * n
    for k in range(n):
        v = near[(k + 1) % n] - near[k]
        v -= L * round(v / L)
        dl[k] = v
    floor = 0.12 * L / n
    dl = [max(v, floor) for v in dl]
    for _ in range(RING_SMOOTH):
        dl = [0.5 * dl[k] + 0.25 * (dl[k - 1] + dl[(k + 1) % n])
              for k in range(n)]
    sc = L / (sum(dl) or 1.0)
    dl = [v * sc for v in dl]

    run = [0.0] * n
    for k in range(1, n):
        run[k] = run[k - 1] + dl[k - 1]
    cs = sn = 0.0
    tau = 2.0 * math.pi
    for k in range(n):
        a = tau * (near[k] - run[k]) / L
        cs += math.cos(a)
        sn += math.sin(a)
    s0 = 0.0 if (cs == 0.0 and sn == 0.0) else L * math.atan2(sn, cs) / tau
    return [Vector((p[0], p[1], 0.0)) for p in (at(run[k] + s0)
                                                for k in range(n))]


def _row_bands(rows, curve):
    """[s_lo, s_hi] the outline spans at every row station (None if clear)."""
    m = len(curve)
    out = []
    for x in rows:
        lo, hi = 1e18, -1e18
        for k in range(m):
            ax, asv = curve[k]
            bx, bsv = curve[(k + 1) % m]
            if (ax - x) * (bx - x) > 0.0:
                continue
            if abs(bx - ax) < 1e-12:
                lo = min(lo, asv, bsv)
                hi = max(hi, asv, bsv)
                continue
            t = (x - ax) / (bx - ax)
            sv = asv + (bsv - asv) * t
            lo = min(lo, sv)
            hi = max(hi, sv)
        out.append(None if hi <= lo else (lo, hi))
    return out


def _clean_dead(dead):
    """Make a raster region safe to walk: no spurs, no one-cell notches, no
    diagonal pinch points, one component only."""
    if not dead:
        return dead
    for _ in range(3):
        drop = set()
        for (i, j) in dead:
            k = 0
            for nb in ((i - 1, j), (i + 1, j), (i, j - 1), (i, j + 1)):
                if nb in dead:
                    k += 1
            if k <= 1:
                drop.add((i, j))
        if not drop:
            break
        dead -= drop
    for _ in range(4):
        add = set()
        for (i, j) in dead:
            for nb in ((i - 1, j), (i + 1, j), (i, j - 1), (i, j + 1)):
                if nb in dead or nb in add:
                    continue
                a, b = nb
                k = 0
                for n2 in ((a - 1, b), (a + 1, b), (a, b - 1), (a, b + 1)):
                    if n2 in dead:
                        k += 1
                if k >= 3:
                    add.add(nb)
        if not add:
            break
        dead |= add
    for _ in range(8):
        add = set()
        for (i, j) in dead:
            for (di, dj) in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
                if (i + di, j + dj) in dead and (i + di, j) not in dead \
                        and (i, j + dj) not in dead:
                    add.add((i + di, j))
        if not add:
            break
        dead |= add
    seen = set()
    best = set()
    for cell in dead:
        if cell in seen:
            continue
        stack = [cell]
        seen.add(cell)
        comp = []
        while stack:
            (i, j) = stack.pop()
            comp.append((i, j))
            for nb in ((i - 1, j), (i + 1, j), (i, j - 1), (i, j + 1)):
                if nb in dead and nb not in seen:
                    seen.add(nb)
                    stack.append(nb)
        if len(comp) > len(best):
            best = set(comp)
    return best


def _dead_ring(dead):
    """Ordered boundary loop of a set of dead faces, or None if it is not one
    simple loop."""
    nxt = {}
    for (i, j) in dead:
        for (a, b, nb) in (((i, j), (i, j + 1), (i - 1, j)),
                           ((i, j + 1), (i + 1, j + 1), (i, j + 1)),
                           ((i + 1, j + 1), (i + 1, j), (i + 1, j)),
                           ((i + 1, j), (i, j), (i, j - 1))):
            if nb not in dead:
                if a in nxt:
                    return None            # pinch point - not a simple loop
                nxt[a] = b
    if len(nxt) < 8:
        return None
    start = min(nxt)
    loop = [start]
    cur = nxt[start]
    while cur != start:
        loop.append(cur)
        cur = nxt.get(cur)
        if cur is None or len(loop) > len(nxt):
            return None
    if len(loop) != len(nxt):
        return None
    if _signed_area(loop) > 0.0:
        loop.reverse()
    return loop


def _harmonic(nr, nc, dead, rim, R):
    """Smooth extension of a rim displacement field over a band of width R.

    Solves a discrete Laplace problem: the rim carries (dx, ds, 1), the outer
    edge of the band carries zero, everything between is harmonic. The weight
    channel then drives a C1 falloff (see D-MB17) so the band cannot leave a
    crease where it meets untouched skin.
    """
    if not rim:
        return {}
    ri = [k[0] for k in rim]
    rj = [k[1] for k in rim]
    di = [k[0] for k in dead] or ri
    dj = [k[1] for k in dead] or rj
    ra = max(0, min(min(ri), min(di)) - R - 1)
    rb = min(nr - 1, max(max(ri), max(di) + 1) + R + 1)
    ca = max(0, min(min(rj), min(dj)) - R - 1)
    cb = min(nc - 1, max(max(rj), max(dj) + 1) + R + 1)
    H = rb - ra + 1
    W = cb - ca + 1
    if H < 3 or W < 3:
        return {}

    if _np is None:
        return {}

    fixed = _np.zeros((H, W), dtype=bool)
    live = _np.ones((H, W), dtype=bool)
    val = _np.zeros((H, W, 3), dtype=_np.float64)
    for (i, j) in dead:                       # a dead face kills its 4 corners
        for (a, b) in ((i, j), (i, j + 1), (i + 1, j), (i + 1, j + 1)):
            if ra <= a <= rb and ca <= b <= cb:
                live[a - ra, b - ca] = False
    for (k, v) in rim.items():
        i, j = k
        if ra <= i <= rb and ca <= j <= cb:
            live[i - ra, j - ca] = True
            fixed[i - ra, j - ca] = True
            val[i - ra, j - ca] = (v[0], v[1], 1.0)

    # dilate the rim R cells to find the band; everything outside stays zero
    band = _np.zeros((H, W), dtype=bool)
    band[fixed] = True
    for _ in range(R):
        nb = band.copy()
        nb[1:, :] |= band[:-1, :]
        nb[:-1, :] |= band[1:, :]
        nb[:, 1:] |= band[:, :-1]
        nb[:, :-1] |= band[:, 1:]
        band = nb
    band &= live
    free = band & ~fixed
    if not free.any():
        return {}

    cnt = _np.zeros((H, W), dtype=_np.float64)
    lv = live.astype(_np.float64)
    cnt[1:, :] += lv[:-1, :]
    cnt[:-1, :] += lv[1:, :]
    cnt[:, 1:] += lv[:, :-1]
    cnt[:, :-1] += lv[:, 1:]
    cnt = _np.maximum(cnt, 1.0)
    lm = lv[:, :, None]
    fm = free[:, :, None]
    it = int(min(900, max(60, 5 * R * R)))
    acc = _np.zeros_like(val)
    for _ in range(it):
        vm = val * lm
        acc[:] = 0.0
        acc[1:, :] += vm[:-1, :]
        acc[:-1, :] += vm[1:, :]
        acc[:, 1:] += vm[:, :-1]
        acc[:, :-1] += vm[:, 1:]
        acc /= cnt[:, :, None]
        val = _np.where(fm, acc, val)

    out = {}
    idx = _np.argwhere(free)
    for (a, b) in idx:
        w = val[a, b, 2]
        if w <= 1e-4:
            continue
        # D-MB17: a harmonic field decays LINEARLY into the untouched skin, so
        # its gradient jumps at the outer edge of the band and folds a dart into
        # the reflection - the triangular wedge that survived beside the cockpit
        # coaming. Scaling by smootherstep(w)/w leaves the rim untouched (w = 1)
        # and lands on zero with zero slope and zero curvature at the far edge.
        g = w * w * (10.0 + w * (6.0 * w - 15.0))
        # g = smootherstep(w)/w peaks at 1.20, so scaling the coaming BEAD by it
        # put a 1.2 mm ring ridge three cells outboard of the rim. The bead uses
        # smootherstep(w) itself, which is bounded by 1 (D-MB30).
        out[(int(a) + ra, int(b) + ca)] = (val[a, b, 0] * g,
                                           val[a, b, 1] * g, w * g)
    return out


def _band_weight(rows, srs, nr, nc, curve, bands, W, deadv):
    """Blend weight around an aperture: 1 on the outline, 0 W METRES outboard.

    D-MB37 - THE cause of the coaming shard band, and the reason D-MB25, D-MB30
    and D-MB33 all failed to remove it. Those three passes each fixed something
    real (rim correspondence, bead scaling, evaluation order) but none of them
    touched the thing that was actually wrong: the blend band was a discrete
    harmonic field on the GRID INDEX, R *cells* wide, decaying by a fixed amount
    per cell.

    This grid is deliberately non-uniform. A groove wall puts columns 0.24 mm
    apart, a chine's flank columns are unevenly spread across its width, and the
    aperture tips carry 1.2 mm rows (D-MB32) that do not align with the 4.2 mm
    ones, leaving 0.3 mm slivers where the two rasters beat against each other.
    Measured inside the cockpit band: the column step runs 0.09 .. 4.0 mm and the
    row step 0.03 .. 5.96 mm, a 13x spread.

    A weight that drops the same amount per index step therefore drops at a
    wildly different rate per MILLIMETRE from one cell to the next, and a 5.8 mm
    coaming bead riding on it turns that into a flank whose slope alternates
    between 7 and 52 degrees cell by cell (measured: mean 18 deg, p95 52 deg).
    That is a chain of facets exactly one cell long and one cell wide running
    along the outboard side of the bead - which is precisely what a gloss
    highlight cannot carry, and precisely what the verifier photographed.

    The weight is now the true distance in metres from the aperture outline,
    measured in the surface's own (x, arclength) chart, so the bead's flank has
    the same slope everywhere regardless of how the grid happens to be resolved
    underneath it. The band also stops pinching to a third of its width at the
    four aperture tips, which is where the shards were worst.
    """
    if not curve or W <= 1e-9:
        return {}
    cx = [p[0] for p in curve]
    cd = [p[1] for p in curve]
    x0, x1 = min(cx) - W, max(cx) + W
    d0, d1 = min(cd) - W, max(cd) + W

    keys = []
    pts = []
    for i in range(nr):
        x = rows[i]
        if x < x0 or x > x1:
            continue
        bd = bands[i]
        row = srs[i]
        for j in range(nc):
            dv = row[j]
            if dv < d0 or dv > d1:
                continue
            if bd is not None and bd[0] < dv < bd[1]:
                continue                       # inside the hole
            if (i, j) in deadv:
                continue
            keys.append((i, j))
            pts.append((x, dv))
    if not keys:
        return {}

    if _np is not None:
        P = _np.asarray(pts, dtype=_np.float64)
        A = _np.asarray(curve, dtype=_np.float64)
        E = _np.roll(A, -1, axis=0) - A
        L2 = _np.maximum((E * E).sum(1), 1e-18)
        best = _np.empty(len(P))
        for s in range(0, len(P), 2048):
            Q = P[s:s + 2048]
            t = ((Q[:, None, 0] - A[None, :, 0]) * E[None, :, 0]
                 + (Q[:, None, 1] - A[None, :, 1]) * E[None, :, 1]) / L2[None, :]
            _np.clip(t, 0.0, 1.0, out=t)
            ex = A[None, :, 0] + E[None, :, 0] * t - Q[:, None, 0]
            ey = A[None, :, 1] + E[None, :, 1] * t - Q[:, None, 1]
            best[s:s + 2048] = _np.sqrt((ex * ex + ey * ey).min(1))
        dists = best
    else:                                      # pragma: no cover
        dists = []
        m = len(curve)
        for (px, pd) in pts:
            bd2 = 1e18
            for q in range(m):
                ax, ad = curve[q]
                bx, bdd = curve[(q + 1) % m]
                ex, ed = bx - ax, bdd - ad
                l2 = ex * ex + ed * ed
                t = 0.0 if l2 < 1e-14 else max(0.0, min(
                    1.0, ((px - ax) * ex + (pd - ad) * ed) / l2))
                qx, qd = ax + ex * t - px, ad + ed * t - pd
                bd2 = min(bd2, qx * qx + qd * qd)
            dists.append(math.sqrt(bd2))

    out = {}
    for (k, dd) in zip(keys, dists):
        t = float(dd) / W
        if t >= 1.0:
            continue
        out[k] = _smoother(1.0 - t)
    return out


# =========================================================================== #
# 6.  the panel builder
# =========================================================================== #

def build_panel(name, coll, rows, cols, mats, thick=T_SKIN, feats=(), cross=(),
                holes=(), mat_lip=1, mat_throat=None, angle=38.0,
                flange=FLANGE, roll_seg=6, close_ring=False, shrink=None,
                tip=None, seam_rows=(), seam_r=SEAM_R):
    nr, nc = len(rows), len(cols)
    # D-MB40: which columns are load-bearing for the panel's own extent. A 'p'
    # column sits at a fixed psi and an 'm' column at a fixed fraction between
    # the panel's two edges: both are monotone by construction and neither can
    # ever cross anything. Only the metric ('s') feature columns move relative
    # to them, so only they are allowed to be clamped. See _order_cols.
    anch = [c.kind != "s" for c in cols]
    grid = []
    psis = []
    for x in rows:
        pf = prof(x)
        fr = []
        for ft in feats:
            rc = ft.row(x, pf)
            if rc is not None:
                fr.append((ft.apply, rc))
        line = _order_cols([c.eval_psi(x, pf) for c in cols], anch)
        psis.append(line)
        rw = []
        for p in line:
            sp = sring(pf, p)
            off = 0.0
            for (fn, rc) in fr:
                off += fn(rc, sp)
            for cl in cross:
                off += cl.off(x, p)
            u, sd = psi_us(p)
            y, z, ny, nz = pf.at(u)
            rw.append((x, sd * (y + off * ny), z + off * nz))
        if shrink is not None:
            sc = shrink(x)
            if abs(sc - 1.0) > 1e-9:
                cz = 0.5 * (pf.z[0] + pf.z[-1])
                rw = [(px, py * sc, cz + (pz - cz) * sc) for (px, py, pz) in rw]
        grid.append(rw)

    # D-MB26: aperture work runs in CREST-RELATIVE arclength d = s - half(x),
    # not absolute ring arclength. `half` shrinks as the section shrinks, so an
    # absolute s meant one thing at the front of an aperture and another at the
    # back: the outline drifted a couple of millimetres to one side of the
    # centreline and the fastener ring round the coaming came out non-mirrored.
    # d is measured from the crest, which is common to every station.
    srs = [[sring(prof(rows[i]), psis[i][j]) - prof(rows[i]).half
            for j in range(nc)] for i in range(nr)]

    def place(xv, dv):
        pf2 = prof(xv)
        return spt(xv, psi_of_sring(pf2, pf2.half + dv))

    def surf_n(xv, dv, h=0.0016):
        """Outward unit normal of the REFERENCE SURFACE at (x, arclength).

        D-MB37: the bead used to be pushed along a normal differenced off the
        vertex's four grid neighbours. In the blend band those neighbours are
        0.03 mm away in one direction and 5.9 mm in the other, so the direction
        was as resolution-dependent as the magnitude was, and it wobbled cell to
        cell with it. Differentiating the spec surface at the vertex's own
        parameter cannot be fooled by how the grid is refined. This is the same
        frame the rim itself already uses (D-MB06).
        """
        a = Vector(place(xv + h, dv)) - Vector(place(xv - h, dv))
        b = Vector(place(xv, dv + h)) - Vector(place(xv, dv - h))
        n = b.cross(a)
        pf2 = prof(xv)
        u2, sd2 = psi_us(psi_of_sring(pf2, pf2.half + dv))
        _y, _z, ny2, nz2 = pf2.at(u2)
        ref2 = Vector((0.0, sd2 * ny2, nz2))
        if n.length < 1e-12:
            return ref2
        n.normalize()
        return -n if n.dot(ref2) < 0.0 else n

    _fcache = {}

    def full_pt(xv, dv, fscale):
        """Surface point at (x, arclength) WITH the relief features re-evaluated.

        D-MB23: every vertex the blend band touched used to be re-placed on the
        bare reference surface, which silently deleted the chine or panel line
        running through it. A chine crossing the edge of the band therefore
        stepped by its full sag in one quad - a hard little wedge exactly where
        the darts were reported. The features are re-evaluated at the warped
        parameter and faded out toward the rim, so they run into the coaming
        instead of being chopped off at the band boundary.
        """
        pf2 = prof(xv)
        sv = pf2.half + dv
        p = psi_of_sring(pf2, sv)
        off = 0.0
        if fscale > 1e-4 and (feats or cross):
            key = int(round(xv * 1e5))
            fr2 = _fcache.get(key)
            if fr2 is None:
                fr2 = []
                for ft in feats:
                    rc = ft.row(xv, pf2)
                    if rc is not None:
                        fr2.append((ft.apply, rc))
                _fcache[key] = fr2
            for (fn, rc) in fr2:
                off += fn(rc, sv)
            for cl in cross:
                off += cl.off(xv, p)
            off *= fscale
        u, sd = psi_us(p)
        y, z, ny, nz = pf2.at(u)
        return (xv, sd * (y + off * ny), z + off * nz)

    # D-MB18: the hole used to be a RECTANGLE of grid cells whose boundary ring
    # was then snapped onto the aperture outline. Circumscribing a 950 x 400 mm
    # lens with a rectangle leaves 150 mm of empty corner, so the four corner
    # vertices had to travel 150 mm to reach the outline and the skin around
    # them was dragged with them - the origin of every dart, cusp and pleat
    # anyone has ever found beside a coaming. The dead cells are now exactly the
    # cells INSIDE the outline (tested per row against the outline's own
    # s-band), the ring is the boundary loop of that region, and no rim vertex
    # ever moves more than about one cell to land on the outline. The blend that
    # follows therefore carries millimetres, not decimetres.
    dead = set()
    rims = []
    warp = {}
    beads = {}
    edge = 3
    for hole in holes:
        curve = [(cx, sring(prof(cx), cp) - prof(cx).half)
                 for (cx, cp) in hole["curve"]]
        bands = _row_bands(rows, curve)
        ins = []
        for i in range(nr):
            b = bands[i]
            if b is None or i < edge or i > nr - 1 - edge:
                ins.append(None)
                continue
            lo, hi = b
            row = srs[i]
            ins.append([lo < row[j] < hi for j in range(nc)])
        hdead = set()
        for i in range(nr - 1):
            a, b = ins[i], ins[i + 1]
            if a is None or b is None:
                continue
            for j in range(edge, nc - 1 - edge):
                if a[j] and a[j + 1] and b[j] and b[j + 1]:
                    hdead.add((i, j))
        hdead = _clean_dead(hdead)
        ring = _dead_ring(hdead)
        if ring is None or len(ring) < 24:
            continue
        dead |= hdead

        pos = [(rows[i], srs[i][j]) for (i, j) in ring]
        new = _resample_ring(pos, curve)
        nrg = len(new)
        cxm = sum(q.x for q in new) / nrg
        csm = sum(q.y for q in new) / nrg
        rim = {}
        rimf = {}
        # D-MB06: the ring's own frame was read off the grid, whose inboard
        # neighbours are the DEAD vertices still sitting where the hole is - so
        # every lip normal near a corner was junk and the coaming shredded into
        # shards. The rim frame is now differentiated straight off the spec
        # surface at the snapped parameter, which cannot be fooled.
        # D-MB19: the rim's outward direction used to be read off the vector the
        # snap had just moved the vertex along. That only worked because the old
        # rectangular ring always moved outward by a huge amount; now that a rim
        # vertex moves barely a millimetre, that vector is noise and the coaming
        # would roll the wrong way at random. It is taken from the OUTLINE
        # instead - the 2-D loop normal, signed away from the aperture centroid.
        h = 0.0016
        for k in range(nrg):
            key = ring[k]
            p0 = pos[k]
            q = new[k]
            grid[key[0]][key[1]] = place(q.x, q.y)
            rim[key] = (q.x - p0[0], q.y - p0[1])
            dx = Vector(place(q.x + h, q.y)) - Vector(place(q.x - h, q.y))
            ds = Vector(place(q.x, q.y + h)) - Vector(place(q.x, q.y - h))
            nn = ds.cross(dx)
            pf2 = prof(q.x)
            u2, sd2 = psi_us(psi_of_sring(pf2, pf2.half + q.y))
            _y, _z, ny2, nz2 = pf2.at(u2)
            ref2 = Vector((0.0, sd2 * ny2, nz2))
            if nn.length < 1e-12:
                nn = ref2.copy()
            nn.normalize()
            if nn.dot(ref2) < 0.0:
                nn = -nn
            a2 = new[(k - 1) % nrg]
            b2 = new[(k + 1) % nrg]
            tx, ts = b2.x - a2.x, b2.y - a2.y
            ox, os_ = ts, -tx
            if ox * (q.x - cxm) + os_ * (q.y - csm) < 0.0:
                ox, os_ = -ox, -os_
            om = math.hypot(ox, os_) or 1.0
            ee = dx * (ox / om) + ds * (os_ / om)
            ee -= nn * ee.dot(nn)
            if ee.length < 1e-12:
                ee = Vector((1.0, 0.0, 0.0))
            rimf[key] = (nn, ee.normalized())

        R = int(hole.get("blend", 9))
        bead = hole.get("bead", 0.0)
        field = _harmonic(nr, nc, hdead, rim, R)
        for (k, v) in field.items():
            a = warp.get(k)
            warp[k] = (v[0], v[1], v[2]) if a is None else \
                (a[0] + v[0], a[1] + v[1], min(1.0, a[2] + v[2]))
        rims.append((hole, ring, rimf, bead, curve, bands, R))

    rimset = set()
    for r in rims:
        rimset.update(r[1])
    deadv = set()
    for (i, j) in dead:
        deadv.add((i, j))
        deadv.add((i, j + 1))
        deadv.add((i + 1, j))
        deadv.add((i + 1, j + 1))
    deadv -= rimset

    # D-MB37: the bead and the feature fade are driven by a METRIC weight -
    # distance in metres from the outline - not by the harmonic field's index
    # count. See _band_weight. The harmonic field still carries the rim's own
    # displacement (dx, ds) into the skin, which is what it is good at and which
    # measurably contributes nothing to the faceting; only the two things that
    # ride on a 5.8 mm normal displacement moved onto the metric weight.
    mws = {}
    for (hole, _rg, _rf, bead, curve, bands, R) in rims:
        bw = hole.get("beadw", R * COL_STEP)
        for (k, wv) in _band_weight(rows, srs, nr, nc, curve, bands,
                                    bw, deadv).items():
            mws[k] = min(1.0, mws.get(k, 0.0) + wv)
            if abs(bead) > 1e-9:
                beads[k] = beads.get(k, 0.0) + bead * wv

    # apply the accumulated parameter-space warp once, so two apertures whose
    # blend bands touch add up instead of overwriting one another
    for (i, j) in set(warp) | set(mws):
        if (i, j) in rimset:
            continue
        wv = warp.get((i, j))
        dx = 0.0 if wv is None else wv[0]
        dsv = 0.0 if wv is None else wv[1]
        grid[i][j] = full_pt(rows[i] + dx, srs[i][j] + dsv,
                             max(0.0, 1.0 - mws.get((i, j), 0.0)))
    # D-MB33: this loop used to read each vertex's normal off the grid it was
    # writing to, so whether a vertex saw its neighbours beaded or not depended
    # on dict iteration order. Gather, then apply. D-MB37 went further and took
    # the direction off the reference surface instead of off the grid at all.
    bpts = []
    for ((i, j), bv) in beads.items():
        if (i, j) in rimset or abs(bv) < 1e-7:
            continue
        nn0 = surf_n(rows[i], srs[i][j])
        bpts.append((i, j, tuple(Vector(grid[i][j]) + nn0 * bv)))
    for (i, j, p) in bpts:
        grid[i][j] = p
    for (_h, ring, rimf, bead, _cv, _bd, _R) in rims:
        if abs(bead) < 1e-9:
            continue
        for key in ring:
            nn0 = rimf[key][0]
            grid[key[0]][key[1]] = tuple(Vector(grid[key[0]][key[1]])
                                         + nn0 * bead)

    verts = []
    faces = []
    mids = []
    idx = {}

    def vid(p):
        verts.append(tuple(p))
        return len(verts) - 1

    for i in range(nr):
        for j in range(nc):
            idx[(i, j)] = vid(grid[i][j])

    ii, jj = nr // 2, nc // 3
    a = Vector(grid[ii][jj])
    b = Vector(grid[ii][jj + 1])
    c = Vector(grid[ii + 1][jj + 1])
    refn = _grid_n(grid, ii, jj, nr, nc, close_ring)
    flip = (b - a).cross(c - a).dot(refn) < 0.0

    cspan = nc if close_ring else nc - 1
    for i in range(nr - 1):
        for j in range(cspan):
            if (i, j) in dead:
                continue
            j2 = (j + 1) % nc
            q = (idx[(i, j)], idx[(i, j2)], idx[(i + 1, j2)], idx[(i + 1, j)])
            faces.append(q[::-1] if flip else q)
            mids.append(0)

    def dedup_loop(loop):
        """Drop border vertices that are closer together than the weld distance.

        D-MB42: a rolled edge builds a chain of `seg + 1` new vertices per border
        vertex. Where two neighbouring border vertices sit a micron apart - the
        panel corners, where a column pair has been squeezed together - their two
        chains coincide, remove_doubles welds them, and the quads that used to
        span them become edges with three faces on them. Deduplicating the border
        below the weld distance removes the cause instead of the symptom; the
        vertices dropped here are exactly the ones remove_doubles was going to
        merge anyway.
        """
        out = []
        for k in loop:
            p = Vector(grid[k[0]][k[1]])
            if out and (p - Vector(grid[out[-1][0]][out[-1][1]])).length < 4.0e-5:
                continue
            out.append(k)
        while len(out) > 8 and (Vector(grid[out[0][0]][out[0][1]])
                                - Vector(grid[out[-1][0]][out[-1][1]])
                                ).length < 4.0e-5:
            out.pop()
        return out if len(out) > 8 else loop

    seamset = set(seam_rows)

    def edge_loop(loop, dirs, t, seg, fl, mid=0):
        n = len(loop)
        prev = [idx[k] for k in loop]
        r = t * 0.5
        half = max(1, seg // 2)

        def prof_std(sgi):
            """Free edge: a plain semicircular rollover of radius t/2. Widest
            point t/2 outboard AND t/2 under the skin."""
            th = math.pi * sgi / seg
            return r * math.sin(th), r * (1.0 - math.cos(th))

        def prof_seam(sgi):
            """D-MB45 - the lip of a CLOSED butt joint. A quarter round of
            radius seam_r takes the skin over the edge, then the wall tucks
            back in to the panel's own inner surface. The widest point is only
            seam_r under the skin instead of t/2, which is what lets the two
            lips of a joint meet with a 1.8 mm shut line above them instead of
            a 7.6 mm dish. The return keeps the two panels apart below the
            contact, so they touch on one ring and nowhere else."""
            if sgi <= half:
                th = 0.5 * math.pi * sgi / half
                return seam_r * math.sin(th), seam_r * (1.0 - math.cos(th))
            u = (sgi - half) / float(seg - half)
            return seam_r * (1.0 - _smoother(u)), seam_r + (t - seam_r) * u

        seam = [key[0] in seamset for key in loop]
        rings = []
        for sgi in range(1, seg + 1):
            std = prof_std(sgi)
            sm = prof_seam(sgi)
            cur = []
            for k, key in enumerate(loop):
                base = Vector(grid[key[0]][key[1]])
                e, nn = dirs[k]
                ov, dv = sm if seam[k] else std
                cur.append(vid(base + e * ov - nn * dv))
            rings.append(cur)
        last = []
        for k, key in enumerate(loop):
            base = Vector(grid[key[0]][key[1]])
            e, nn = dirs[k]
            last.append(vid(base - nn * t - e * fl))
        rings.append(last)
        # D-MB36: the whole rolled edge and its return flange were painted. On a
        # real car the paint stops on the outside of the roll and what you see
        # down a 1.8 mm panel gap is bare laminate. Past the crown of the roll
        # the faces take the panel's second material slot.
        cut = max(1, seg // 2)
        for (ri, cur) in enumerate(rings):
            m = mid if ri < cut else min(1, len(mats) - 1)
            for k in range(n):
                k2 = (k + 1) % n
                q = (prev[k], prev[k2], cur[k2], cur[k])
                faces.append(q[::-1] if flip else q)
                mids.append(m)
            prev = cur

    def dir_for(key, force=None):
        i, j = key
        n = _grid_n(grid, min(max(i, 1), nr - 2),
                    j if close_ring else min(max(j, 1), nc - 2),
                    nr, nc, close_ring)
        acc = Vector((0, 0, 0))
        if i == 0:
            acc += Vector(grid[0][j]) - Vector(grid[1][j])
        if i == nr - 1:
            acc += Vector(grid[nr - 1][j]) - Vector(grid[nr - 2][j])
        # D-MB45: at a panel CORNER this used to add the fore-aft and the
        # outboard directions together and roll the lip off at 45 deg. On a
        # seam row that halves the lip's reach along x - measured 1.16 mm of
        # residual gap at the two corners where chassis_fwd meets the underpan,
        # against 0.00 everywhere else - so a seam lip always rolls square
        # across its own joint.
        if not close_ring and i not in seamset:
            if j == 0:
                acc += Vector(grid[i][0]) - Vector(grid[i][1])
            if j == nc - 1:
                acc += Vector(grid[i][nc - 1]) - Vector(grid[i][nc - 2])
        if force is not None:
            acc = Vector(force)
        acc -= n * acc.dot(n)
        if acc.length < 1e-9:
            acc = Vector((1.0, 0.0, 0.0))
        return acc.normalized(), n

    if close_ring:
        lps = [[(0, j) for j in range(nc)]]
        if tip is None:
            lps.append([(nr - 1, j) for j in range(nc)])
        for lp in lps:
            lp = dedup_loop(lp)
            edge_loop(lp, [dir_for(k) for k in lp], thick, roll_seg, flange)
        if tip is not None:
            ti = vid(Vector(tip))
            for j in range(nc):
                j2 = (j + 1) % nc
                tri = (idx[(nr - 1, j)], idx[(nr - 1, j2)], ti)
                faces.append(tri[::-1] if flip else tri)
                mids.append(0)
    else:
        loop = [(0, j) for j in range(nc)]
        loop += [(i, nc - 1) for i in range(1, nr)]
        loop += [(nr - 1, j) for j in range(nc - 2, -1, -1)]
        loop += [(i, 0) for i in range(nr - 2, 0, -1)]
        loop = dedup_loop(loop)
        edge_loop(loop, [dir_for(k) for k in loop], thick, roll_seg, flange)

    mth = mat_lip if mat_throat is None else mat_throat
    for (hole, ring, rimf, _bd, _cv, _bn, _R) in rims:
        if not hole.get("lip"):
            continue
        n = len(ring)
        basis = []
        nsum = Vector((0, 0, 0))
        for key in ring:
            p = Vector(grid[key[0]][key[1]])
            nn, e = rimf[key]
            basis.append((p, e, nn))
            nsum += nn
        prev = [idx[k] for k in ring]
        pos = [b[0] for b in basis]

        def bridge(cur, mid, prev=None):
            for k in range(n):
                k2 = (k + 1) % n
                q = (prev[k], prev[k2], cur[k2], cur[k])
                faces.append(q if flip else q[::-1])
                mids.append(mid)

        for (dt, dn) in hole["lip"]:
            cur = [vid(p - e * dt + nn * dn) for (p, e, nn) in basis]
            bridge(cur, mat_lip, prev)
            prev = cur
            pos = [Vector(verts[v]) for v in cur]

        th = hole.get("throat")
        if th:
            # D-MB05: a duct mouth on a curved flank is a saddle, not a planar
            # loop. Scaling that rim about its centroid folded consecutive rings
            # through each other - the pinwheel of black petals in the sidepod
            # inlet. The throat now flattens the section onto the duct plane as
            # it goes back, which is what a real moulded duct does anyway.
            ax = th.get("axis")
            ax = -nsum.normalized() if ax is None else Vector(ax).normalized()
            tc = Vector((0, 0, 0))
            for q in pos:
                tc += q
            tc /= len(pos)
            for step in th["steps"]:
                d, sc = step[0], step[1]
                b = step[2] if len(step) > 2 else 1.0
                scx = step[3] if len(step) > 3 else None
                cur = []
                for q in pos:
                    r = q - tc
                    r = r - ax * (r.dot(ax) * b)
                    if scx is None:
                        r = r * sc
                    else:
                        r = Vector((r.x * scx, r.y * sc, r.z * sc))
                    cur.append(vid(tc + r + ax * d))
                bridge(cur, step[4] if len(step) > 4 else mth, prev)
                prev = cur

        if hole.get("cap", True):
            cc = Vector((0, 0, 0))
            for vi in prev:
                cc += Vector(verts[vi])
            cc /= len(prev)
            ci = vid(cc)
            mcap = hole.get("mat_cap", mth)
            for k in range(n):
                k2 = (k + 1) % n
                tri = (prev[k], prev[k2], ci)
                faces.append(tri if flip else tri[::-1])
                mids.append(mcap)

    return _mk(name, verts, faces, coll, mats, mids, angle=angle,
               ref=(grid[ii][jj], refn))


# =========================================================================== #
# 7.  panel plan helpers
# =========================================================================== #

def cover_lo(x):
    """Lower edge of the engine cover / tail fairing, as a psi."""
    if x >= -1.10:
        return PK[5]
    if x >= -1.34:
        return PK[5] + (PK[2] - PK[5]) * _smoother((-1.10 - x) / 0.24)
    if x >= -1.72:
        return PK[2] + (PK[1] - PK[2]) * _smoother((-1.34 - x) / 0.38)
    return PK[1]


def cover_hi(x):
    return 2.0 - cover_lo(x)


def sp_hi(x):
    return min(cover_lo(x), PK[5])


def sp_hi_r(x):
    return 2.0 - sp_hi(x)


def lf_hi(x):
    return min(PK[2], cover_lo(x))


def lf_hi_r(x):
    return 2.0 - lf_hi(x)


# =========================================================================== #
# 8.  aperture outlines
# =========================================================================== #

COCKPIT = [
    (0.780, 0.000), (0.766, 0.048), (0.726, 0.100), (0.664, 0.146),
    (0.588, 0.178), (0.482, 0.201), (0.362, 0.212), (0.242, 0.217),
    (0.122, 0.217), (0.022, 0.212), (-0.052, 0.199), (-0.102, 0.179),
    (-0.134, 0.145), (-0.156, 0.098), (-0.166, 0.040), (-0.168, 0.000),
]

# D-MB20: the airbox used to be a plan-view table whose fore end went from
# y = 0 to y = 41 mm in 4 mm of x. On a face sloping at 49 degrees that is a
# knife point, and the rolled lip built off it collapsed into the blade-and-notch
# that tore the roll-hoop skyline. The mouth is now generated as a superellipse
# in the SURFACE metric of the crown - arclength forward-aft along the crest,
# arclength outboard from it - so every part of the outline including the fore
# tip carries a real radius, and the whole thing sits clear of the crown.
AB_XF = -0.2160           # fore (lower) edge of the mouth
AB_XA = -0.3230           # aft (upper) edge - the crown itself is at -0.360
AB_HALF = 0.1180          # half width, arclength outboard of the crest
AB_N = 2.35               # superellipse exponent: 2 = ellipse, higher = boxier
AB_TAPER = 0.90           # width scale at the aft end
AB_SEG = 216

# a letterbox, not an eye: long in x, shallow in z, on the swept sidepod front
# D-MB34: the mouth's forward end used to close to a point - zl = zu at
# x = 0.862 - and the rolled lip built round that cusp collapsed into a fan of
# 0.2 mm slivers, a ragged line right on the duct's leading edge. A real duct
# lip has a radius; the fore end now stands 15 mm open.
INLET = [
    (0.8585, 0.4090, 0.4250), (0.8480, 0.3980, 0.4400),
    (0.8200, 0.3890, 0.4520), (0.7760, 0.3920, 0.4560),
    (0.7260, 0.3950, 0.4600), (0.6820, 0.3970, 0.4640),
    (0.6520, 0.3990, 0.4660), (0.6320, 0.4120, 0.4560),
]


def _y_curve(tab, n=260):
    left = []
    for (x, hw) in tab:
        if hw <= 1e-6:
            left.append((x, 1.0))
        else:
            left.append((x, prof(x).u_at_y(hw, PK[5], 1.0)))
    right = []
    for (x, hw) in reversed(tab[1:-1]):
        right.append((x, 2.0 - prof(x).u_at_y(hw, PK[5], 1.0)))
    return closed_spline(left + right, n)


def cockpit_curve():
    return _y_curve(COCKPIT, 320)


_CRESTX = None


def _crest_table():
    """Cumulative arclength along the y = 0 crown line, x = -0.10 .. -0.44."""
    global _CRESTX
    if _CRESTX is None:
        xs = [-0.100 - 0.0010 * i for i in range(341)]
        acc = [0.0]
        for i in range(1, len(xs)):
            z0 = prof(xs[i - 1]).z[-1]
            z1 = prof(xs[i]).z[-1]
            acc.append(acc[-1] + math.hypot(xs[i] - xs[i - 1], z1 - z0))
        _CRESTX = (xs, acc)
    return _CRESTX


def _crest_arc(x):
    xs, acc = _crest_table()
    f = (-0.100 - x) / 0.0010
    if f <= 0.0:
        return acc[0]
    if f >= len(xs) - 1:
        return acc[-1]
    i = int(f)
    return acc[i] + (acc[i + 1] - acc[i]) * (f - i)


def _crest_x(a):
    xs, acc = _crest_table()
    if a <= acc[0]:
        return xs[0]
    if a >= acc[-1]:
        return xs[-1]
    lo, hi = 0, len(acc) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if acc[mid] <= a:
            lo = mid
        else:
            hi = mid
    d = acc[lo + 1] - acc[lo]
    t = 0.0 if d < 1e-12 else (a - acc[lo]) / d
    return xs[lo] + (xs[lo + 1] - xs[lo]) * t


def airbox_curve():
    af = _crest_arc(AB_XF)
    aa = _crest_arc(AB_XA)
    ac = 0.5 * (af + aa)
    ah = 0.5 * (aa - af)
    e = 2.0 / AB_N
    loop = []
    for i in range(AB_SEG):
        t = C.TAU * i / AB_SEG
        ct, st = math.cos(t), math.sin(t)
        fx = math.copysign(abs(ct) ** e, ct)
        fy = math.copysign(abs(st) ** e, st)
        a = ac + ah * fx
        x = _crest_x(a)
        pf = prof(x)
        w = AB_HALF * (1.0 + (AB_TAPER - 1.0) * max(0.0, fx))
        d = abs(fy) * w
        u = pf.u_at_s(max(0.0, pf.half - d))
        loop.append((x, u if fy >= 0.0 else 2.0 - u))
    return loop


def inlet_curve(side=1.0, n=200):
    top, bot = [], []
    for (x, zl, zu) in INLET:
        pf = prof(x)
        pu = pf.u_at_z(zu, PK[2], PK[5])
        pl = pf.u_at_z(zl, PK[2], PK[5])
        top.append((x, pu if side > 0 else 2.0 - pu))
        bot.append((x, pl if side > 0 else 2.0 - pl))
    loop = top + bot[::-1][1:-1]
    if side < 0:
        loop = loop[::-1]
    return closed_spline(loop, n)


# =========================================================================== #
# 9.  hardware
# =========================================================================== #

def _dzus(verts, faces, mids, mid, pos, nrm, tan, r=0.0064, rise=0.0009,
          seg=40):
    """A quarter-turn Dzus button: chamfered outer flange, flat head, and a
    real recessed drive slot straight across it."""
    b1 = tan.normalized()
    b2 = nrm.cross(b1).normalized()
    base = len(verts)
    shape = [(r * 1.38, -0.0002), (r * 1.24, 0.0001), (r * 1.09, rise * 0.42),
             (r * 1.00, rise), (r * 0.90, rise * 1.04), (r * 0.72, rise * 1.05),
             (r * 0.44, rise * 1.03), (r * 0.20, rise * 1.02),
             (0.0, rise * 1.02)]
    s_hw = 0.00105
    s_r = r * 0.98
    s_d = 0.00075
    for (rr, hh) in shape:
        for i in range(seg):
            a = 2.0 * math.pi * i / seg
            ca, sa = math.cos(a), math.sin(a)
            dep = s_d if (rr <= s_r and abs(rr * sa) <= s_hw) else 0.0
            verts.append(tuple(pos + b1 * (rr * ca) + b2 * (rr * sa)
                               + nrm * (hh - dep)))
    for k in range(len(shape) - 1):
        a = base + k * seg
        b = base + (k + 1) * seg
        for i in range(seg):
            i2 = (i + 1) % seg
            faces.append((a + i, a + i2, b + i2, b + i))
            mids.append(mid)
    return base


def outline_offset(curve, d):
    """Offset a closed (x, psi) outline outward by d in the surface metric."""
    pts = [(cx, sring(prof(cx), cp) - prof(cx).half) for (cx, cp) in curve]
    m = len(pts)
    cx0 = sum(p[0] for p in pts) / m
    cs0 = sum(p[1] for p in pts) / m
    out = []
    for k in range(m):
        a = pts[(k - 1) % m]
        b = pts[(k + 1) % m]
        ox, os_ = b[1] - a[1], a[0] - b[0]
        if ox * (pts[k][0] - cx0) + os_ * (pts[k][1] - cs0) < 0.0:
            ox, os_ = -ox, -os_
        mm = math.hypot(ox, os_) or 1.0
        nx = pts[k][0] + d * ox / mm
        nd = pts[k][1] + d * os_ / mm
        pfn = prof(nx)
        out.append((nx, psi_of_sring(pfn, pfn.half + nd)))
    return out


def build_fasteners(coll, spots):
    verts, faces, mids = [], [], []
    for sp in spots:
        x, psi, along_x = sp[0], sp[1], sp[2]
        rad = sp[3] if len(sp) > 3 else 0.0064
        lift = sp[4] if len(sp) > 4 else 0.0003
        p = Vector(spt(x, psi))
        t1 = Vector(spt(x + 0.004, psi)) - p
        t2 = Vector(spt(x, psi + 0.004)) - p
        n = t1.cross(t2)
        if n.length < 1e-12:
            continue
        n.normalize()
        if n.dot(p - Vector((x, 0.0, 0.35))) < 0.0:
            n = -n
        tan = t1 if along_x else t2
        tan = tan - n * tan.dot(n)
        if tan.length < 1e-9:
            continue
        _dzus(verts, faces, mids, 0, p + n * lift, n, tan, r=rad)
    if not verts:
        return None
    return _mk(P + "fasteners", verts, faces, coll, ["SteelFastener"], mids,
               angle=32.0)


# =========================================================================== #
# 9b.  the survival cell inside the cockpit aperture
# =========================================================================== #

# D-MB21: the cockpit read as a black hole with a lid on it - a rim, a throat
# and a flat cap, nothing you could call structure. The throat now carries on
# down past where the cockpit-lining part picks it up (that part's tray floor
# sits at z = 0.4720, so everything here stays below z = 0.4601 and cannot foul
# it) into a real survival cell: a ribbed tub floor with rolled-up sides and
# side stringers, a front bulkhead under the dash and a rear bulkhead behind the
# headrest. In isolation you now see a cell; in the assembly the lining covers
# it exactly as it did before.
AP_XC = 0.3060
CELL_Z = 0.3920
CELL_KX = 0.868
CELL_KY = 0.520
CELL_XF = 0.6960
CELL_XR = -0.1080
CELL_BH_F = 0.6480        # front bulkhead station
CELL_BH_R = -0.0640       # rear bulkhead station
CELL_TOP = 0.4540         # top of the bulkheads - 6 mm under the lining floor

# half section of the pan, across: (v, dz). v = 1 is the edge of the flat.
CELL_SEC = [(0.000, 0.0000), (0.150, -0.0007), (0.320, -0.0018),
            (0.480, -0.0028), (0.640, -0.0033), (0.780, -0.0034),
            (0.880, -0.0029), (0.955, -0.0016), (1.000, 0.0000),
            (1.036, 0.0015), (1.063, 0.0048), (1.079, 0.0096),
            (1.087, 0.0154), (1.091, 0.0220), (1.095, 0.0284),
            (1.117, 0.0326), (1.143, 0.0344), (1.169, 0.0334),
            (1.187, 0.0300)]

_CKS = None


def _ck_hw(x):
    """Plan half width of the cockpit aperture at station x."""
    global _CKS
    if _CKS is None:
        _CKS = C.catmull_rom(COCKPIT, 260)
    pts = _CKS
    if x >= pts[0][0] or x <= pts[-1][0]:
        return 0.0
    lo, hi = 0, len(pts) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if pts[mid][0] >= x:
            lo = mid
        else:
            hi = mid
    d = pts[lo][0] - pts[hi][0]
    t = 0.0 if abs(d) < 1e-12 else (pts[lo][0] - x) / d
    return max(0.0, pts[lo][1] + (pts[hi][1] - pts[lo][1]) * t)


def _cell_hw(x):
    """Half width of the cell floor at its own station x."""
    xr = AP_XC + (x - AP_XC) / CELL_KX
    return max(0.042, _ck_hw(xr) * CELL_KY)


def _cell_taper(x):
    """D-MB28: the pan's rolled-up sides and stringer flange kept full height
    right to the ends, where the pan is only 50 mm wide - the two flanges folded
    through each other. The flange now lies down over the last 90 mm."""
    return (_smoother((x - CELL_XR) / 0.090)
            * _smoother((CELL_XF - x) / 0.090))


def _bump(t, w):
    if abs(t) >= w:
        return 0.0
    return 0.5 * (1.0 + math.cos(math.pi * t / w))


CELL_RIB_V = (0.395, 0.775)
CELL_RIB_X = (0.545, 0.320, 0.086, -0.148)


def _cell_z(x, v):
    a = abs(v)
    t = _tab_sec(a)
    z = CELL_Z + (t * _cell_taper(x) if t > 0.0 else t)
    if a <= 1.0:
        # D-MB37: at 6.2 mm tall on 0.115-wide windows the floor ribs stepped
        # ~40 deg per quad where a longitudinal crossed a transverse one and the
        # crossings read faceted. Lower, wider, and sampled by more rows.
        for vr in CELL_RIB_V:
            z += 0.0050 * _bump(a - vr, 0.150)
        for xr in CELL_RIB_X:
            z += 0.0044 * _bump(x - xr, 0.042) * (1.0 - 0.55 * a * a)
    return z


def _tab_sec(a):
    tab = CELL_SEC
    if a <= tab[0][0]:
        return tab[0][1]
    if a >= tab[-1][0]:
        return tab[-1][1]
    for i in range(len(tab) - 1):
        if tab[i][0] <= a <= tab[i + 1][0]:
            t = (a - tab[i][0]) / (tab[i + 1][0] - tab[i][0])
            return C.lerp(tab[i][1], tab[i + 1][1], t)
    return tab[-1][1]


def build_cell(coll):
    made = []
    vmax = CELL_SEC[-1][0]
    half = C.catmull_rom([(p[0], p[0]) for p in CELL_SEC], 46)
    vs = [p[0] for p in half]
    vs[0] = 0.0
    cols = [-v for v in reversed(vs[1:])] + vs
    nx = 196
    rows = []
    for i in range(nx + 1):
        x = CELL_XF + (CELL_XR - CELL_XF) * i / nx
        hw = _cell_hw(x)
        row = []
        for v in cols:
            row.append((x, v * hw, _cell_z(x, v)))
        rows.append(row)
    v, f = C.grid_surface(rows)
    pan = _mk(P + "cell_floor", v, f, coll, ["CarbonFibre"], [0] * len(f),
              angle=34.0)
    C.add_solidify(pan, 0.0058, offset=0.0)
    made.append(pan)

    # ---- bulkheads --------------------------------------------------------- #
    bv, bf, bm = [], [], []
    fix = []
    for (bx, sgn) in ((CELL_BH_F, 1.0), (CELL_BH_R, -1.0)):
        hw = _cell_hw(bx)
        nz = 26
        nw = 34
        base = len(bv)
        for k in range(nz + 1):
            t = k / nz
            z = C.lerp(_cell_z(bx, 0.0) + 0.0010, CELL_TOP, t)
            # the bulkhead bows away from the cockpit and flares at the top
            bow = 0.026 * math.sin(math.pi * t) * sgn
            wid = hw * (1.0 + 0.115 * t)
            for q in range(nw + 1):
                u = -1.0 + 2.0 * q / nw
                bv.append((bx + bow * (1.0 - 0.55 * u * u),
                           u * wid,
                           z + 0.0042 * (1.0 - u * u) * (1.0 - t)))
        for k in range(nz):
            for q in range(nw):
                a = base + k * (nw + 1) + q
                b = a + nw + 1
                bf.append((a, a + 1, b + 1, b))
                bm.append(0)
        for q in range(6):
            u = -0.80 + 1.60 * q / 5.0
            wid = hw * 1.115
            fix.append(((bx + 0.026 * sgn, u * wid, CELL_TOP - 0.0075),
                        (0.0, 0.0, 1.0), (1.0, 0.0, 0.0)))
    if bv:
        bh = _mk(P + "cell_bulkhead", bv, bf, coll, ["CarbonFibre"], bm,
                 angle=34.0)
        C.add_solidify(bh, 0.0060, offset=0.0)
        made.append(bh)

    # ---- longitudinal stringer caps on the pan flange ---------------------- #
    sv, sf, sm = [], [], []
    for side in (1.0, -1.0):
        rowsL = []
        n = 96
        for i in range(n + 1):
            x = CELL_XF - 0.012 + (CELL_XR + 0.012 - CELL_XF + 0.012) * i / n
            hw = _cell_hw(x)
            tp = _cell_taper(x)
            ring = []
            for (a, dz) in ((1.098, 0.0292), (1.126, 0.0338), (1.152, 0.0356),
                            (1.176, 0.0344), (1.192, 0.0308), (1.186, 0.0270),
                            (1.160, 0.0252), (1.128, 0.0258), (1.104, 0.0276)):
                ring.append((x, side * a * hw, CELL_Z + dz * tp))
            rowsL.append(ring)
        base = len(sv)
        vv, ff = C.loft(rowsL, closed=True, cap_start=True, cap_end=True)
        sv.extend(vv)
        for q in ff:
            sf.append(tuple(k + base for k in q))
            sm.append(0)
    if sv:
        made.append(_mk(P + "cell_stringer", sv, sf, coll, ["CarbonMatte"],
                        sm, angle=34.0))

    # ---- fixings ----------------------------------------------------------- #
    fv, ff2, fm = [], [], []
    for (pos, nrm, tan) in fix:
        _dzus(fv, ff2, fm, 0, Vector(pos), Vector(nrm), Vector(tan), r=0.0050,
              rise=0.0008, seg=32)
    for side in (1.0, -1.0):
        for i in range(7):
            x = CELL_XF - 0.028 - (CELL_XF - CELL_XR - 0.056) * i / 6.0
            hw = _cell_hw(x)
            _dzus(fv, ff2, fm, 0,
                  Vector((x, side * 1.152 * hw,
                          CELL_Z + 0.0358 * _cell_taper(x))),
                  Vector((0.0, 0.0, 1.0)), Vector((1.0, 0.0, 0.0)),
                  r=0.0048, rise=0.0008, seg=32)
    if fv:
        made.append(_mk(P + "cell_fixings", fv, ff2, coll, ["SteelFastener"],
                        fm, angle=32.0))
    return made


def build_backing(coll, strips):
    """Bonded backing strips 9 mm under every joint - what you actually see
    down a 1.8 mm panel gap on a real car."""
    verts, faces, mids = [], [], []
    for st in strips:
        rows = []
        if st[0] == "x":
            _, xv, p0, p1, hw = st
            n = max(10, int(abs(p1 - p0) / 0.010))
            for d in (-hw, hw):
                rows.append([spt(xv + d, p0 + (p1 - p0) * i / n, -0.009)
                             for i in range(n + 1)])
        else:
            _, psfn, x0, x1, hw = st
            n = max(10, int(abs(x1 - x0) / 0.012))
            for sgn in (-1.0, 1.0):
                row = []
                for i in range(n + 1):
                    x = x0 + (x1 - x0) * i / n
                    pf = prof(x)
                    row.append(spt(x, psi_shift(pf, psfn(x), sgn * hw), -0.009))
                rows.append(row)
        base = len(verts)
        v, f = C.grid_surface(rows)
        verts.extend(v)
        for q in f:
            faces.append(tuple(i + base for i in q))
            mids.append(0)
    if not verts:
        return None
    return _mk(P + "backing", verts, faces, coll, ["CarbonMatte"], mids,
               angle=30.0)


# =========================================================================== #
# 10.  build
# =========================================================================== #

def build(coll, ctx=None):
    made = []
    _PC.clear()
    hx = GAP * 0.5 + T_SKIN * 0.5

    def pair(psi, *a, **kw):
        return [Crease(psi, *a, **kw), Crease(2.0 - psi, *a, **kw)]

    # ---- 1. nose cone --------------------------------------------------- #
    nose_cr = pair(PK[3], 2.030, 2.952, wmax=0.026, scale=1.35) + \
        pair(PK[1], 2.060, 2.930, wmax=0.020, scale=0.85)
    nose_x = CrossLine(2.350, 0.02, 1.98, fade=0.06)
    nose_x2 = CrossLine(2.690, 0.02, 1.98, fade=0.06)
    # the last 16 mm rolls into a blunt crash-structure tip; the section is
    # scaled toward its own centre so the tip stays on the spec section right
    # up to where it closes
    # D-MB10: the tip closed with a fan off a ring still at 39 % of section, so
    # the crash structure ended in a visible flat disc. Rows are now clustered
    # by sin so the last ring is 5 % of section and the fan is ~8 mm across.
    TIPL = 0.017

    def nose_shrink(x):
        if x <= X_TIP - TIPL:
            return 1.0
        t = min(1.0, (x - (X_TIP - TIPL)) / TIPL)
        return math.sqrt(max(0.0, 1.0 - t * t))

    # D-MB45: the aft edge stops SEAM_HX forward of the joint station, not
    # hx = GAP/2 + T_SKIN/2 - the lip's own roll covers the rest and meets the
    # chassis lip on the joint plane.
    nose_rows = make_rows(X_NOSE_J + hx, X_TIP - TIPL, extra=[2.60, 2.64],
                          dense=[(2.90, X_TIP - TIPL, 0.0035)],
                          lines=[nose_x, nose_x2])
    NT = 24
    for k in range(1, NT):
        a = 0.5 * math.pi * k / NT
        nose_rows.append(X_TIP - TIPL * (1.0 - math.sin(a)))
    nose_rows = sorted(set(round(v, 7) for v in nose_rows))
    nose_cols = make_cols(0.0, 2.0, nose_rows, feats=nose_cr, step=0.0040,
                          drop_last=True)
    pft = prof(X_TIP - TIPL)
    made.append(build_panel(
        P + "nose", coll, nose_rows, nose_cols,
        ["LiveryPaint", "CarbonMatte"], thick=T_SKIN, feats=nose_cr,
        cross=[nose_x, nose_x2], close_ring=True, angle=40.0,
        shrink=nose_shrink,
        tip=(X_TIP, 0.0, 0.5 * (pft.z[0] + pft.z[-1]))))

    # ---- 2. chassis, forward section ------------------------------------ #
    # D-MB22: every chine used to fade in and out INSIDE the panel it lived on,
    # so the tub shoulder line appeared out of nothing at x = 0.975, ran 1.0 m
    # and vanished again - and on the panel behind it a second stub ran x = 0.80
    # to 0.948. Two feature lines pointing at each other across a joint with a
    # gap in between is exactly how you get a triangular fold in the reflection.
    # The shoulder and max-width chines are now single continuous lines whose
    # fades sit OUTSIDE the panels they cross, so the amplitude matches on both
    # sides of every joint and there is nothing left to dart.
    tf_cr = pair(PK[3], 0.700, 1.985, wmax=0.030, fade=0.10, scale=1.25) + \
        pair(PK[6], 0.700, 1.960, wmax=0.022, fade=0.10, scale=0.78) + \
        pair(PK[1], 0.760, 1.975, wmax=0.022, fade=0.10, scale=0.8)
    tf_ln = [LongLine(1.0, -0.104, 1.400, 1.700),
             LongLine(1.0, 0.104, 1.400, 1.700),
             LongLine(PK[6], 0.030, 1.010, 1.930),
             LongLine(2.0 - PK[6], -0.030, 1.010, 1.930)]
    tf_x = [CrossLine(1.400, 0.86, 1.14, fade=0.030),
            CrossLine(1.700, 0.86, 1.14, fade=0.030),
            CrossLine(1.150, PK[1] + 0.03, 2.0 - PK[1] - 0.03, fade=0.035)]
    tf_rows = make_rows(X_SP_LE + hx, X_NOSE_J - hx, lines=tf_x)
    tf_cols = make_cols(PK[1], 2.0 - PK[1], tf_rows, feats=tf_cr + tf_ln)
    made.append(build_panel(
        P + "chassis_fwd", coll, tf_rows, tf_cols,
        ["LiveryPaint", "CarbonMatte"], thick=T_SKIN, feats=tf_cr + tf_ln,
        cross=tf_x))

    # ---- 3. chassis, cockpit section ------------------------------------ #
    tm_cr = pair(PK[6], 0.700, 1.200, wmax=0.022, fade=0.10, scale=0.78) + \
        pair(PK[6], -0.620, -0.140, wmax=0.020, fade=0.11, scale=0.70)
    tm_x = [CrossLine(0.850, PK[5] + 0.02, 2.0 - PK[5] - 0.02, fade=0.030),
            CrossLine(-0.300, PK[5] + 0.02, 2.0 - PK[5] - 0.02, fade=0.030)]
    tm_ln = [LongLine(PK[5], 0.026, -0.410, 0.930),
             LongLine(2.0 - PK[5], -0.026, -0.410, 0.930)]
    # D-MB32: an aperture outline that turns 6 mm of half width per millimetre
    # of x - which is what a lens-shaped cockpit does at its tips - cannot be
    # tracked by a raster of 4.2 mm rows: the cut ends bluntly ten cells wide
    # while the outline runs on to a point, and the rim vertices that have to
    # bridge the difference fold the quads behind them. The four aperture tips
    # get 1.2 mm rows so the cut can follow the outline into the point.
    tm_rows = make_rows(X_TUB_R + hx, X_SP_LE - hx,
                        dense=[(-0.44, 0.82, 0.0042),
                               (0.740, 0.800, 0.0012),
                               (-0.200, -0.132, 0.0012),
                               (-0.238, -0.202, 0.0012),
                               (-0.340, -0.300, 0.0012)], lines=tm_x)
    tm_cols = make_cols(PK[5], 2.0 - PK[5], tm_rows, feats=tm_cr + tm_ln,
                        step=0.0038)
    ck = cockpit_curve()
    ab = airbox_curve()
    # D-MB12: a 2.2 mm bead plus a 3 mm lip rise on the mouth's forward tip -
    # which sits on the steepest part of the roll-hoop face - stood proud of the
    # skyline and read as a duck bill hanging off the crown. A real intake lip
    # is close to flush; the bead and the rise both came down.
    ab_lip = [(0.0009, 0.0011), (0.0028, 0.0015), (0.0052, 0.0011),
              (0.0070, 0.0000), (0.0078, -0.0034), (0.0076, -0.0090)]
    ab_throat = dict(axis=(-0.62, 0.0, -0.785),
                     steps=[(0.018, 0.980, 0.30), (0.044, 0.950, 0.70),
                            (0.078, 0.905, 0.94), (0.112, 0.862, 1.00),
                            (0.146, 0.822, 1.00), (0.172, 0.770, 1.00),
                            (0.186, 0.640, 1.00), (0.192, 0.380, 1.00)])
    # D-MB11: at a 4 mm bead and a 5 mm roll the coaming read as a painted
    # outline rather than a moulded rim. A real cockpit surround stands ~12 mm
    # proud of the deck, so the bead and the roll both grew.
    coam = [(0.0012, 0.0036), (0.0038, 0.0058), (0.0076, 0.0062),
            (0.0110, 0.0044), (0.0132, 0.0012), (0.0138, -0.0034),
            (0.0134, -0.0094)]
    # steps down to d = 0.138 are load-bearing: the cockpit-lining part measured
    # its funnel off them. Everything past that is the survival cell (D-MB21).
    coam_throat = dict(axis=(0.0, 0.0, -1.0),
                       steps=[(0.014, 1.000, 0.25), (0.040, 0.990, 0.60),
                              (0.072, 0.968, 0.88), (0.104, 0.938, 1.00),
                              (0.128, 0.900, 1.00), (0.138, 0.876, 1.00),
                              (0.160, 0.842, 1.00, 0.962),
                              (0.186, 0.808, 1.00, 0.940),
                              (0.208, 0.778, 1.00, 0.924),
                              (0.224, 0.744, 1.00, 0.913),
                              (0.236, 0.688, 1.00, 0.905),
                              (0.242, 0.596, 1.00, 0.900)])
    made.append(build_panel(
        P + "chassis_cockpit", coll, tm_rows, tm_cols,
        ["LiveryPaint", "CarbonFibre", "CarbonMatte"], thick=T_SKIN,
        feats=tm_cr + tm_ln, cross=tm_x,
        holes=[dict(curve=ck, bead=0.0058, lip=coam,
                    throat=coam_throat, cap=True, blend=11),
               dict(curve=ab, bead=0.0009, lip=ab_lip,
                    throat=ab_throat, cap=True, blend=10)],
        mat_lip=1, mat_throat=2))
    made.extend(build_cell(coll))

    # ---- 4. sidepod bodywork -------------------------------------------- #
    inl_lip = [(0.0008, 0.0020), (0.0026, 0.0028), (0.0050, 0.0024),
               (0.0066, 0.0006), (0.0072, -0.0026), (0.0070, -0.0072)]
    # D-MB43: the duct was six rings of MatteBlack closed with a MatteBlack fan.
    # Nothing in there could catch a highlight, so a correctly rolled lip framed
    # a flat unlit void and the aperture read as a hole cut in a card. A real
    # inlet shows a moulded carbon duct with a heat exchanger a little way down
    # it. The walls now take the panel's lacquered-carbon slot so they carry the
    # key light down the duct, the ring spacing is finer over the first 50 mm so
    # the wall reads as a curved surface instead of six facets, and a 4 mm step
    # at d = 0.074 puts a lit edge in front of the core - which stays matte black
    # (mat_cap) so there is still real depth behind it.
    inl_throat = dict(steps=[(0.008, 0.990, 0.22), (0.019, 0.974, 0.52),
                             (0.030, 0.955, 0.74), (0.041, 0.934, 0.90),
                             (0.052, 0.912, 0.98), (0.062, 0.890, 1.00),
                             (0.069, 0.868, 1.00), (0.0695, 0.800, 1.00),
                             (0.077, 0.782, 1.00), (0.084, 0.560, 1.00, None,
                                                    2)])
    for side, tag in ((1.0, "L"), (-1.0, "R")):
        lo = (lambda x: PK[2]) if side > 0 else (lambda x: 2.0 - PK[2])
        hi = sp_hi if side > 0 else sp_hi_r
        p2 = PK[2] if side > 0 else 2.0 - PK[2]
        p3 = PK[3] if side > 0 else 2.0 - PK[3]
        p4 = PK[4] if side > 0 else 2.0 - PK[4]
        pa = (p2 + 0.02) if side > 0 else (2.0 - PK[5] + 0.02)
        pb = (PK[5] - 0.02) if side > 0 else (p2 - 0.02)
        # D-MB35: the mouth's lower edge ran straight down the middle of the
        # max-width chine, so every rim quad along it had to reconcile a sharp
        # crease dying into a rolled lip - 460 slivers along the duct's floor.
        # The mouth now sits in the clear band between the two chines, and the
        # max-width chine runs forward from the tail and dies into the surround,
        # which is where it ends on a real car anyway.
        sp_cr = [Crease(p3, -1.430, 0.642, wmax=0.030, fade=0.11, scale=1.25),
                 Crease(p4, -1.430, 1.050, wmax=0.026, fade=0.11, scale=1.05)]
        sp_x = [CrossLine(-0.560, pa, pb, fade=0.030),
                CrossLine(0.120, pa, pb, fade=0.030),
                CrossLine(-1.040, pa, pb, fade=0.030)]
        sp_ln = [LongLine(p3, 0.052 * side, -1.260, 0.620),
                 LongLine(p4, -0.046 * side, -1.240, 0.820)]
        lo2, hi2 = (lo, hi) if side > 0 else (hi, lo)
        mfeats(sp_cr + sp_ln, lo2, hi2, 0.0)
        sp_rows = make_rows(X_SP_TE, X_SP_LE - hx, step=0.0058,
                            dense=[(0.580, 0.880, 0.0038),
                                   (0.615, 0.660, 0.0012),
                                   (0.840, 0.876, 0.0012)], lines=sp_x)
        a0, b0 = lo(0.0), hi(0.0)
        cols = make_cols(min(a0, b0), max(a0, b0), sp_rows,
                         feats=sp_cr + sp_ln, step=0.0040)
        cols = to_moving(cols, lo, hi, 0.0) if side > 0 else \
            to_moving(cols, hi, lo, 0.0)
        icv = inlet_curve(side)
        made.append(build_panel(
            P + "sidepod_" + tag, coll, sp_rows, cols,
            ["LiveryPaint", "CarbonFibre", "MatteBlack", "Titanium"],
            thick=T_SKIN,
            feats=sp_cr + sp_ln, cross=sp_x,
            holes=[dict(curve=icv, bead=0.0018, lip=inl_lip,
                        throat=inl_throat, cap=True, blend=10, mat_cap=3)],
            mat_lip=1, mat_throat=1))

    # ---- 5. lower flanks ------------------------------------------------- #
    for side, tag in ((1.0, "L"), (-1.0, "R")):
        lf_x = [CrossLine(0.200,
                          PK[1] + 0.014 if side > 0 else 2.0 - PK[2] + 0.014,
                          PK[2] - 0.014 if side > 0 else 2.0 - PK[1] - 0.014,
                          fade=0.020),
                CrossLine(-0.640,
                          PK[1] + 0.014 if side > 0 else 2.0 - PK[2] + 0.014,
                          PK[2] - 0.014 if side > 0 else 2.0 - PK[1] - 0.014,
                          fade=0.020)]
        lf_rows = make_rows(-1.712, X_SP_LE - hx, step=0.0075, lines=lf_x)
        lo = (lambda x: PK[1]) if side > 0 else (lambda x: 2.0 - PK[1])
        hi = lf_hi if side > 0 else lf_hi_r
        a0, b0 = lo(0.0), hi(0.0)
        cols = make_cols(min(a0, b0), max(a0, b0), lf_rows, step=0.0045)
        cols = to_moving(cols, lo, hi, 0.0) if side > 0 else \
            to_moving(cols, hi, lo, 0.0)
        made.append(build_panel(
            P + "lowerflank_" + tag, coll, lf_rows, cols,
            ["CarbonFibre", "CarbonMatte"], thick=T_SKIN, cross=lf_x))

    # ---- 6. underpan ----------------------------------------------------- #
    # D-MB38 - the tail asymmetry. The two floor lines were anchored at the
    # belly CENTRELINE with a fixed metric offset of 60 mm. The belly half
    # section is 304 mm of arclength at mid-car and 30 mm at x = -2.455, so a
    # column pinned 60 mm from the centre walks steadily outboard as a fraction
    # of the panel and, past x = -2.36, is outside the panel altogether: at
    # x = -2.435 it evaluates to psi 0.208 on a panel that ends at 0.143. The
    # monotone guard in build_panel then drags every column after it onto that
    # one parameter - the outer 3/4 of the belly collapsed into a single chord,
    # 10.7 mm off the reference surface. This is D-MB24 again, on the one panel
    # that never got the D-MB24 treatment. It showed up only on the LEFT because
    # the right-hand line's columns were being silently discarded by the psi
    # wrap fixed in D-MB39, which is what made it an 8.95 mm left/right
    # disagreement rather than a symmetric dent.
    #
    # The lines are now anchored at a fixed station on the section (0.197 of the
    # belly half, which is the 60 mm they already sat at where the floor is
    # widest) with a metric groove on top, so they track the floor's own plan
    # taper instead of running off the edge of it. Nothing can cross, on either
    # side, at any station.
    UP_LN = PK[1] * 0.197
    up_ln = [LongLine(UP_LN, 0.0, -2.30, 1.95),
             LongLine(-UP_LN, 0.0, -2.30, 1.95)]
    up_x = [CrossLine(0.600, -PK[1] + 0.012, PK[1] - 0.012, fade=0.020),
            CrossLine(-0.300, -PK[1] + 0.012, PK[1] - 0.012, fade=0.020),
            CrossLine(-1.200, -PK[1] + 0.012, PK[1] - 0.012, fade=0.020)]
    up_rows = make_rows(X_TAIL, X_NOSE_J - hx, step=0.012, lines=up_x)
    up_cols = make_cols(-PK[1], PK[1], up_rows, feats=up_ln, step=0.0075)
    made.append(build_panel(
        P + "underpan", coll, up_rows, up_cols,
        ["CarbonFibre", "CarbonMatte"], thick=T_SKIN, feats=up_ln,
        cross=up_x))

    # ---- 7. engine cover -------------------------------------------------- #
    ec_cr = [Crease(PK[6], -1.560, -0.300, wmax=0.022, fade=0.11, scale=0.70),
             Crease(2.0 - PK[6], -1.560, -0.300, wmax=0.022, fade=0.11,
                    scale=0.70),
             Crease(PK[4], -1.560, -0.780, wmax=0.026, fade=0.11, scale=0.8),
             Crease(2.0 - PK[4], -1.560, -0.780, wmax=0.026, fade=0.11,
                    scale=0.8)]
    ec_ln = [LongLine(1.0, 0.096, -1.420, -0.600),
             LongLine(1.0, -0.096, -1.420, -0.600)]
    ec_x = [CrossLine(-0.560, cover_lo(-0.56) + 0.02,
                      cover_hi(-0.56) - 0.02, fade=0.030)]
    mfeats(ec_cr + ec_ln, cover_lo, cover_hi, -0.8)
    ec_rows = make_rows(X_COVER_J + hx, X_TUB_R - hx, step=0.0052, lines=ec_x)
    a0, b0 = cover_lo(-0.8), cover_hi(-0.8)
    ec_cols = make_cols(a0, b0, ec_rows, feats=ec_cr + ec_ln, step=0.0042)
    ec_cols = to_moving(ec_cols, cover_lo, cover_hi, -0.8)
    made.append(build_panel(
        P + "engine_cover", coll, ec_rows, ec_cols,
        ["LiveryPaint", "CarbonFibre"], thick=T_SKIN,
        feats=ec_cr + ec_ln, cross=ec_x))

    # ---- 8. tail fairing -------------------------------------------------- #
    tl_cr = [Crease(PK[3], -2.340, -1.360, wmax=0.024, fade=0.11, scale=0.9),
             Crease(2.0 - PK[3], -2.340, -1.360, wmax=0.024, fade=0.11,
                    scale=0.9),
             Crease(PK[5], -2.300, -1.360, wmax=0.020, fade=0.11, scale=0.7),
             Crease(2.0 - PK[5], -2.300, -1.360, wmax=0.020, fade=0.11,
                    scale=0.7)]
    tl_x = [CrossLine(-1.980, cover_lo(-1.98) + 0.02,
                      cover_hi(-1.98) - 0.02, fade=0.030)]
    tl_ln = [LongLine(1.0, 0.062, -2.240, -1.480),
             LongLine(1.0, -0.062, -2.240, -1.480)]
    mfeats(tl_cr + tl_ln, cover_lo, cover_hi, -1.9)
    tl_rows = make_rows(X_TAIL, X_COVER_J - hx, step=0.0058, lines=tl_x)
    a0, b0 = cover_lo(-1.9), cover_hi(-1.9)
    tl_cols = make_cols(a0, b0, tl_rows, feats=tl_cr + tl_ln, step=0.0045)
    tl_cols = to_moving(tl_cols, cover_lo, cover_hi, -1.9)
    made.append(build_panel(
        P + "tail_fairing", coll, tl_rows, tl_cols,
        ["LiveryPaint", "CarbonMatte"], thick=T_SKIN,
        feats=tl_cr + tl_ln, cross=tl_x))

    # ---- 9. tail cap ------------------------------------------------------ #
    ncap = 108
    pf = prof(X_TAIL)
    cz = 0.5 * (pf.z[0] + pf.z[-1])
    base_ring = [spt(X_TAIL, 2.0 * i / ncap) for i in range(ncap)]
    rings = []
    for k in range(8):
        t = k / 7.0
        x = X_TAIL - 0.015 * t
        sc = math.sqrt(max(0.0, 1.0 - t * t)) * 0.998 + 0.002
        rings.append([(x, p[1] * sc, cz + (p[2] - cz) * sc)
                      for p in base_ring])
    # D-MB41: the cap used to open with an extra copy of the base ring shifted
    # 0.4 mm FORWARD of X_TAIL. Both the tail fairing and the underpan end their
    # last row exactly on X_TAIL, so that ring stood 0.4 mm proud of the two
    # panels it closes against and the joint read as a bulge with a shading step
    # instead of a flush closure. rings[0] below is already at X_TAIL at scale
    # 1.0 - i.e. exactly the panels' own last ring - so the duplicate was doing
    # nothing but making the step.
    v, f = C.loft(rings, closed=True, cap_start=True, cap_end=True)
    made.append(_mk(P + "tail_cap", v, f, coll, ["LiveryPaint"],
                    [0] * len(f), angle=40.0,
                    ref=(rings[1][ncap // 4],
                         (0.0, 1.0 if rings[1][ncap // 4][1] > 0 else -1.0, 0.0))))

    # ---- 10. fasteners ----------------------------------------------------- #
    spots = []
    for i in range(16):
        spots.append((X_NOSE_J - 0.030, 2.0 * (i + 0.5) / 16.0, False))
    for i in range(12):
        spots.append((X_SP_LE + 0.028,
                      PK[1] + (2.0 - 2.0 * PK[1]) * (i + 0.5) / 12.0, False))
    x = 0.870
    while x > -1.26:
        pf = prof(x)
        for s in (1.0, -1.0):
            pu = sp_hi(x) if s > 0 else sp_hi_r(x)
            spots.append((x, psi_shift(pf, pu, -0.021 * s), True))
            pl = PK[2] if s > 0 else 2.0 - PK[2]
            spots.append((x, psi_shift(pf, pl, 0.021 * s), True))
        x -= 0.152
    x = -0.520
    while x > -1.40:
        pf = prof(x)
        for s in (1.0, -1.0):
            pu = cover_lo(x) if s > 0 else cover_hi(x)
            spots.append((x, psi_shift(pf, pu, 0.021 * s), True))
        x -= 0.148
    for i in range(10):
        t = (i + 0.5) / 10.0
        spots.append((X_COVER_J - 0.030,
                      cover_lo(-1.48) + (cover_hi(-1.48) - cover_lo(-1.48)) * t,
                      False))
    for i in range(11):
        t = (i + 0.5) / 11.0
        spots.append((X_TUB_R - 0.032,
                      cover_lo(-0.47) + (cover_hi(-0.47) - cover_lo(-0.47)) * t,
                      False))
    # quarter-turns holding the deck panel down all round the cockpit surround
    # and the airbox mouth - the two removable panels nobody had fastened
    # D-MB27: the surround fasteners sat on the BARE reference surface while the
    # skin around a coaming is beaded up to 6 mm proud of it, so they were half
    # sunk into their own panel. They now sit outside the bead's reach, on the
    # deck-panel joint line where a real one would be.
    for (cv, off, every, rr) in ((ck, 0.0560, 20, 0.0058),
                                 (ab, 0.0300, 36, 0.0054)):
        for (fx, fp) in outline_offset(cv, off)[::every]:
            spots.append((fx, fp, True, rr, 0.0006))
    fob = build_fasteners(coll, spots)
    if fob:
        made.append(fob)

    # ---- 11. backing strips ------------------------------------------------ #
    strips = [
        ("x", X_NOSE_J, 0.002, 1.998, 0.020),
        ("x", X_SP_LE, PK[1], 2.0 - PK[1], 0.020),
        ("x", X_TUB_R, cover_lo(X_TUB_R), cover_hi(X_TUB_R), 0.020),
        ("x", X_COVER_J, cover_lo(-1.45), cover_hi(-1.45), 0.020),
        ("l", lambda x: PK[1], -2.35, 1.98, 0.018),
        ("l", lambda x: 2.0 - PK[1], -2.35, 1.98, 0.018),
        ("l", lambda x: PK[2], -1.33, 0.95, 0.018),
        ("l", lambda x: 2.0 - PK[2], -1.33, 0.95, 0.018),
        ("l", sp_hi, -1.33, 0.95, 0.018),
        ("l", sp_hi_r, -1.33, 0.95, 0.018),
        ("l", cover_lo, -1.71, -0.43, 0.018),
        ("l", cover_hi, -1.71, -0.43, 0.018),
    ]
    bob = build_backing(coll, strips)
    if bob:
        made.append(bob)

    # D-MB44: the section cache holds a 561-point _Prof for every distinct x
    # the build touched - and the aperture blend evaluates the surface at a
    # different x for every vertex in the band, so it ends up holding tens of
    # thousands of them, several hundred MB that nothing needs once the meshes
    # exist. Renders of this part were being OOM-killed on an 11 GB box.
    _PC.clear()
    return made
