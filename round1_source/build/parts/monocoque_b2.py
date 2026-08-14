"""monocoque_b2 - the central body, built as a PANEL ASSEMBLY.

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

The COCKPIT COAMING is not made of grid cells at all (D-MB37). Its bead band is
cut out of the raster 34 mm outboard of the outline and rebuilt as one
structured annulus of 57 true parallel curves of the aperture, 0.43 mm apart, so
the bead height is an analytic smootherstep of the real distance from the rim
and of nothing else. The outermost ring of the annulus IS the raster's hole
boundary, so the join is a plain quad band on bare, bead-free skin.

Measured departure from spec.body_surface_point, tools/devcheck.py, 21 894
samples (267 stations x 41 fracs x 2 sides):
    max_outside_apertures  0.0087 m   (tolerance 0.015, 58 % of budget)
    violations_outside     0
Left/right disagreement over the last 160 mm of the tail is 0.00 mm at every
station and frac sampled - it was 8.95 mm, see D-MB39.
Inside the cockpit aperture 466 sample points fall in open air because the
reference surface there describes the closed trough this module was asked to
replace with a real hole.

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
    D-MB37  THE crystalline band, for real this time. The coaming bead was a
            height field indexed by grid cell - a discrete harmonic solved over
            a Manhattan dilation of the rim - so it was not a function of
            position: at a true 8-12 mm outboard of the outline it ranged from
            0.004 mm to 5.128 mm, because 11 cells of dilation is 13 mm of band
            where the rows are 1.2 mm and 46 mm where they are 4.2 mm.
            Neighbouring vertices differed by 0.16 mm across a 3.8 mm cell - a
            4.8 degree normal flip, alternating in sign, one cell wide. Rebuilt
            as a structured offset annulus (section 5b)
    D-MB38  the aperture outlines were uniform-parameter Catmull-Rom through
            control points 100 mm apart on the flank and 2 mm apart at the tips.
            That overshoots: a 15.6 mm convex radius against a 146 mm concave
            one at the widest point of the cockpit, and worse the finer you
            sampled it. Centripetal parameterisation, arclength delivery, and a
            fairing pass that keeps every radius larger than the lip built on it
    D-MB39  a panel line sits a fixed number of millimetres from its anchor
            knot; at the tail that is wider than the whole half section, so the
            column evaluated outboard of the panel while keeping its place in
            the column order and the monotone guard collapsed everything beyond
            it. 11 mm off the reference surface on the left of the tail against
            5 mm on the right. Metric columns are now bracketed by their plain
            neighbours. The arclength that sizes a column run also wrapped at
            psi = 0, so the underpan and the nose were built five times denser
            on one side than the other
    D-MB40  the tail cap opened with a ring 0.4 mm FORWARD of the tail fairing's
            last row - a collar standing proud of the panel it closes
    D-MB41  the sidepod inlet was an 84 mm blind sack lined in MatteBlack that
            necked to 56 % of its mouth in the last 6 mm; nothing in it could
            catch a photon
    D-MB42  rows 20 microns apart and coincident feature columns left ribbons of
            zero-area quads whose zero normals seed spurious sharp edges
    D-MB43  the sidepod and lower flank ran their two panel edges together to
            exactly the same psi at the trailing station - a knife edge, and 287
            non-manifold edges
    D-MB44  the reference surface still carries the C0 kinks where D-MB13 clamps
            its faired stations back into the tolerance tube. A 4.2 mm raster
            smears them; the annulus resolves them, and the rim normal turned 24
            degrees in one 1.9 mm step and threw the 5.8 mm bead sideways. The
            bead DIRECTION is faired; the points are not moved

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

NAME = "monocoque_b2"
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
                 f=0.0, anchorf=None):
        self.kind = kind
        self.psi = psi
        self.anchor = anchor
        self.ds = ds
        self.lo = lo
        self.hi = hi
        self.f = f
        self.anchorf = anchorf
        self.blo = self.bhi = None      # bracketing columns, see _bracket
        self.bk = self.bn = 0

    def eval_psi(self, x, pf):
        if self.kind == "p":
            return self.psi
        if self.kind == "s":
            a = self.anchorf(x) if self.anchorf is not None else self.anchor
            p = psi_of_sring(pf, sring(pf, a) + self.ds)
            # D-MB39: a panel line sits a FIXED NUMBER OF MILLIMETRES from its
            # anchor knot, but a panel's half section shrinks toward the tail
            # until 60 mm is more than the whole width of it. The column then
            # evaluates past the panel's outboard edge while still holding its
            # place in the column ORDER, and build_panel's monotone guard drags
            # every column outboard of it onto the same parameter - the whole
            # outer half of a station collapses to one chord. That is what put
            # the underpan 11 mm off the reference surface on the left of the
            # tail against 5 mm on the right (the mirror line's columns were
            # silently dropped by the arclength wrap, so only one side had it).
            # Every metric column is now bracketed by its neighbouring plain
            # columns and can never cross one.
            if self.blo is not None and self.bhi is not None:
                a2 = self.blo.eval_psi(x, pf)
                b2 = self.bhi.eval_psi(x, pf)
                if b2 > a2:
                    e = (b2 - a2) / (2.0 * (self.bn + 1))
                    p = min(max(p, a2 + (self.bk + 1) * e),
                            b2 - (self.bn - self.bk) * e)
            return p
        a, b = self.lo(x), self.hi(x)
        return a + (b - a) * self.f


def _arc_between(pf, a, b):
    """Arclength along the section between two psi values, the short way.

    D-MB39: this used |sring(b) - sring(a)|, and sring wraps at psi = 0, so an
    interval that straddles the belly centre - which is exactly what the
    underpan and the nose cone are made of - measured the arclength the LONG way
    round the whole section. Three metres instead of a quarter of one, so the
    column count hit its 160 cap and one half of those panels was built five
    times denser than the other. Same skin, but a different mesh left and right,
    and a lot of polygons for nothing.
    """
    d = abs(sring(pf, b) - sring(pf, a))
    return min(d, 2.0 * pf.half - d)


def _bracket(cols):
    """Tell every metric column which plain columns it must stay between."""
    n = len(cols)
    i = 0
    while i < n:
        if cols[i].kind != "s":
            i += 1
            continue
        j = i
        while j < n and cols[j].kind == "s":
            j += 1
        lo = cols[i - 1] if i > 0 else None
        hi = cols[j] if j < n else None
        for k in range(j - i):
            c = cols[i + k]
            c.blo, c.bhi, c.bk, c.bn = lo, hi, k, j - i
        i = j
    return cols


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

    fill = []
    for a, b in zip(knots, knots[1:]):
        amax = 0.0
        for x in xr:
            amax = max(amax, _arc_between(prof(x), a, b))
        n = min(max(2, int(math.ceil(amax / step))), 160)
        for i in range(n):
            fill.append(Col("p", psi=a + (b - a) * i / n))
    fill.append(Col("p", psi=ps_hi))

    ref = xs[len(xs) // 2]
    pfr = prof(ref)
    keep = []
    for c in fcols:
        p = c.eval_psi(ref, pfr)
        if ps_lo - 1e-9 <= p <= ps_hi + 1e-9:
            keep.append((p, sring(pfr, p), c))
    keep.sort(key=lambda t: t[0])
    # D-MB42: two features whose columns land on the same arclength (a chine's
    # flank sample against a panel line's ramp, say) left a pair of columns
    # microns apart and a full-height ribbon of zero-area quads down the panel.
    ded = []
    for t in keep:
        if ded and abs(t[1] - ded[-1][1]) < 6.0e-5:
            continue
        ded.append(t)
    keep = ded
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
    return _bracket(cols)


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
    return _bracket(out)


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
    # D-MB42: the guard used to be 12 microns. Two panel lines whose ramp rows
    # nearly coincide, or a dense band whose end lands next to a plain row, then
    # left rows 20 microns apart - a whole station of 0.02 x 4 mm slivers whose
    # normals are numerical noise, and shade_auto_smooth reads those as sharp
    # edges. 60 microns is still a quarter of a groove wall, so nothing that
    # carries a feature is lost.
    out = [xs[0]]
    for v in xs[1:]:
        if v - out[-1] > 6.0e-5:
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
    bmesh.ops.dissolve_degenerate(bm, dist=2.0e-5, edges=bm.edges)
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


def closed_spline(pts, n, alpha=0.5):
    """Periodic CENTRIPETAL Catmull-Rom through a closed list of 2-tuples,
    delivered evenly spaced by arclength.

    D-MB38: this used the uniform-parameter form, one output sample per control
    interval regardless of how long that interval was. The cockpit outline's
    control points run 100 mm apart along the flank and 2 mm apart at the tips -
    a fifty-fold spacing change - and uniform Catmull-Rom through data like that
    overshoots hard. Measured on the shipped outline it put a 15.6 mm convex
    radius against a 146 mm concave one at x = -0.10, right at the widest point
    of the aperture: an S-kink in the coaming rim, and it got worse the finer
    you sampled (at 1200 samples, R = 4.0 mm convex against 15.2 mm concave).
    Centripetal parameterisation is the standard cure - it provably cannot cusp
    or self-intersect between control points - and arclength delivery means one
    output segment is one output segment wherever you are on the loop, which is
    what the offset march and the rim resampler both assume.
    """
    m = len(pts)
    if m < 3:
        return [tuple(p) for p in pts]
    tk = [0.0] * (m + 3)
    for i in range(m + 3):
        a = pts[(i - 1) % m]
        b = pts[i % m]
        d = math.hypot(b[0] - a[0], b[1] - a[1])
        tk[i] = tk[i - 1] + (d ** alpha if d > 1e-12 else 1e-6) if i else 0.0

    def seg_pt(i, u):
        """u in [0,1] across the span from pts[i] to pts[i+1]."""
        p0, p1 = pts[(i - 1) % m], pts[i % m]
        p2, p3 = pts[(i + 1) % m], pts[(i + 2) % m]
        t0, t1, t2, t3 = tk[i], tk[i + 1], tk[i + 2], tk[i + 3]
        t = t1 + (t2 - t1) * u
        out = []
        for k in range(2):
            a1 = ((t1 - t) * p0[k] + (t - t0) * p1[k]) / max(t1 - t0, 1e-12)
            a2 = ((t2 - t) * p1[k] + (t - t1) * p2[k]) / max(t2 - t1, 1e-12)
            a3 = ((t3 - t) * p2[k] + (t - t2) * p3[k]) / max(t3 - t2, 1e-12)
            b1 = ((t2 - t) * a1 + (t - t0) * a2) / max(t2 - t0, 1e-12)
            b2 = ((t3 - t) * a2 + (t - t1) * a3) / max(t3 - t1, 1e-12)
            out.append(((t2 - t) * b1 + (t - t1) * b2) / max(t2 - t1, 1e-12))
        return (out[0], out[1])

    over = max(6, int(math.ceil(4.0 * n / m)))
    fine = []
    for i in range(m):
        for j in range(over):
            fine.append(seg_pt(i, j / float(over)))
    # even delivery by arclength
    q = len(fine)
    acc = [0.0] * (q + 1)
    for i in range(q):
        a, b = fine[i], fine[(i + 1) % q]
        acc[i + 1] = acc[i] + math.hypot(b[0] - a[0], b[1] - a[1])
    L = acc[q]
    out = []
    j = 0
    for i in range(n):
        sv = L * i / float(n)
        while j < q - 1 and acc[j + 1] < sv:
            j += 1
        dl = acc[j + 1] - acc[j]
        u = 0.0 if dl < 1e-12 else (sv - acc[j]) / dl
        a, b = fine[j], fine[(j + 1) % q]
        out.append((a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u))
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


def _resample_ring(ring_pos, curve, even=0.0, smooth=None):
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
    for _ in range(RING_SMOOTH if smooth is None else int(smooth)):
        dl = [0.5 * dl[k] + 0.25 * (dl[k - 1] + dl[(k + 1) % n])
              for k in range(n)]
    # D-MB37c: the correspondence is allowed to follow the raster boundary only
    # so far. That boundary is a staircase whose vertex density per millimetre
    # of arc changes fourfold where the row pitch changes, and a ring that
    # follows it exactly arrives on the outline with 0.2 mm spacing in places -
    # which is finer than the offset step and folds the quads. `even` mixes in a
    # uniform spacing, so no part of the ring can ever be tighter than
    # (1 - even) of the mean however the raster underneath it is distributed.
    if even > 0.0:
        avg = L / n
        dl = [avg * even + (1.0 - even) * v for v in dl]
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


def _cells_inside(rows, srs, nr, nc, loop, edge):
    """The set of grid cells whose four corners all fall inside a closed
    (x, crest-relative arclength) loop."""
    bands = _row_bands(rows, loop)
    ins = []
    for i in range(nr):
        b = bands[i]
        if b is None or i < edge or i > nr - 1 - edge:
            ins.append(None)
            continue
        lo, hi = b
        row = srs[i]
        ins.append([lo < row[j] < hi for j in range(nc)])
    out = set()
    for i in range(nr - 1):
        a, b = ins[i], ins[i + 1]
        if a is None or b is None:
            continue
        for j in range(edge, nc - 1 - edge):
            if a[j] and a[j + 1] and b[j] and b[j + 1]:
                out.add((i, j))
    return out


# =========================================================================== #
# 5b.  the coaming annulus                                                    #
# =========================================================================== #
#
# D-MB37 - the real cause of the "crystalline band" that D-MB25, D-MB30 and
# D-MB33 all failed to kill.
#
# The coaming bead used to be a height field indexed by GRID CELL: _harmonic
# dilated the rim ring R times with a 4-neighbourhood and solved a discrete
# Laplace problem over that set, and the bead was `bead * smootherstep(w)` with
# w the solution. A dilation of a raster staircase in index space is not a
# distance in metres, so the bead height was not a function of position at all.
# Measured on the shipped module, at a true 8-12 mm outboard of the cockpit
# outline the bead ranged from 0.004 mm to 5.128 mm - a five millimetre spread
# at ONE distance - because rows are 1.2 mm at the aperture tips and 4.2 mm
# along its sides, so eleven cells of dilation is 13 mm of band in one place and
# 46 mm in another. Neighbouring vertices differed by up to 0.16 mm across a
# 3.8 mm cell: a 4.8 degree facet-to-facet normal flip, alternating in sign,
# one cell wide. That is exactly the chain of bright/dark shards, and no amount
# of smoothing iterations or auto-smooth angle can fix a height field that is
# not single-valued in space.
#
# The band is now not a band of grid cells at all. Everything within the bead's
# reach is CUT OUT of the raster and rebuilt as one continuous structured
# annulus: rings of true parallel curves of the aperture outline, so the ring
# index IS the distance from the rim, and the bead is an analytic function of it
# alone. Radially it is sampled at ~0.5 mm, well under the width of the gloss
# highlight, and the profile is a smootherstep so height, slope and curvature
# all land on zero at the outer edge - the deck cannot see where the band ends.
# The outermost ring of the annulus is the raster's own hole boundary, so the
# join is a plain quad band on bare, bead-free skin; the staircase survives
# there as topology only, which is invisible.


def _offset_family(loop, w, m, relax=0.12):
    """Outward parallel curves of a closed loop in (x, arclength) space.

    Marches the loop outward along its own normal in m equal steps. A light
    tangential Laplacian each step keeps the points spread where the outline
    turns tightly (the fore and aft tips of the cockpit have a ~90 mm radius,
    against a 24 mm march) without measurably shrinking the ring - the outline
    is already a smooth spline, so there is no high frequency for it to eat.
    Index correspondence with the seed loop is preserved, so the family is a
    regular quad grid.
    """
    n = len(loop)
    sgn = 1.0 if _signed_area(loop) > 0.0 else -1.0
    cur = [(p[0], p[1]) for p in loop]
    out = [list(cur)]
    step = float(w) / max(1, m)
    a1 = 1.0 - 2.0 * relax
    for _ in range(max(1, m)):
        adv = []
        for k in range(n):
            a = cur[k - 1]
            b = cur[(k + 1) % n]
            tx, ty = b[0] - a[0], b[1] - a[1]
            ln = math.hypot(tx, ty) or 1.0
            adv.append((cur[k][0] + sgn * (ty / ln) * step,
                        cur[k][1] - sgn * (tx / ln) * step))
        cur = [(a1 * adv[k][0] + relax * (adv[k - 1][0] + adv[(k + 1) % n][0]),
                a1 * adv[k][1] + relax * (adv[k - 1][1] + adv[(k + 1) % n][1]))
               for k in range(n)]
        out.append(list(cur))
    return out


def _fair_outline(loop, passes, rmin=0.0):
    """Low-pass a closed outline in the surface metric and re-space it evenly.

    D-MB38: an aperture outline is not free to carry any radius it likes. A
    13.4 mm deep rolled lip built round a corner whose radius is 8 mm has to
    turn the lip inside out, and the fan of back-to-back faces that results is
    the same failure as D-MB34's 0.2 mm slivers on the inlet. The cockpit
    outline had an 8.4 mm convex radius at x = -0.100 - not from the design,
    from spline ripple - so every outline is faired until nothing on it is
    tighter than the deepest thing built off it.
    """
    n = len(loop)
    if n < 8 or passes <= 0:
        return list(loop)
    cur = [(p[0], p[1]) for p in loop]
    for _ in range(int(passes)):
        cur = [(0.5 * cur[k][0] + 0.25 * (cur[k - 1][0] + cur[(k + 1) % n][0]),
                0.5 * cur[k][1] + 0.25 * (cur[k - 1][1] + cur[(k + 1) % n][1]))
               for k in range(n)]
    acc = [0.0] * (n + 1)
    for k in range(n):
        a, b = cur[k], cur[(k + 1) % n]
        acc[k + 1] = acc[k] + math.hypot(b[0] - a[0], b[1] - a[1])
    L = acc[n]
    out = []
    j = 0
    for i in range(n):
        sv = L * i / float(n)
        while j < n - 1 and acc[j + 1] < sv:
            j += 1
        dl = acc[j + 1] - acc[j]
        t = 0.0 if dl < 1e-12 else (sv - acc[j]) / dl
        a, b = cur[j], cur[(j + 1) % n]
        out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    if rmin > 0.0:
        worst = 0.0
        for k in range(n):
            a, b, c = out[k - 1], out[k], out[(k + 1) % n]
            t1 = (b[0] - a[0], b[1] - a[1])
            t2 = (c[0] - b[0], c[1] - b[1])
            cr = t1[0] * t2[1] - t1[1] * t2[0]
            dd = (math.hypot(*t1) * math.hypot(*t2)
                  * math.hypot(c[0] - a[0], c[1] - a[1]))
            if dd > 1e-15:
                worst = max(worst, abs(2.0 * cr / dd))
        if worst * rmin > 1.0:
            print(f"!! outline still turns at R={1000.0/worst:.1f} mm "
                  f"(wanted >= {rmin*1000:.0f} mm)")
    return out


def _bead_shape(v):
    """Bead height factor at normalised outboard distance v in [0, 1].

    smootherstep(1 - v): 1 at the rim with a flat crown for the lip to roll off,
    and 0 at the outer edge with zero slope AND zero curvature, so the annulus
    meets the untouched deck with nothing for a highlight to catch on."""
    t = 1.0 - min(max(v, 0.0), 1.0)
    return t * t * t * (10.0 + t * (6.0 * t - 15.0))


def _feat_shape(v):
    """Relief features (chines, panel lines) fade out into the coaming rather
    than being chopped off at the band edge - D-MB23, kept."""
    t = min(max(v, 0.0), 1.0)
    return t * t * t * (10.0 + t * (6.0 * t - 15.0))


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


# =========================================================================== #
# 6.  the panel builder
# =========================================================================== #

def build_panel(name, coll, rows, cols, mats, thick=T_SKIN, feats=(), cross=(),
                holes=(), mat_lip=1, mat_throat=None, angle=38.0,
                flange=FLANGE, roll_seg=6, close_ring=False, shrink=None,
                tip=None):
    nr, nc = len(rows), len(cols)
    grid = []
    psis = []
    for x in rows:
        pf = prof(x)
        fr = []
        for ft in feats:
            rc = ft.row(x, pf)
            if rc is not None:
                fr.append((ft.apply, rc))
        line = []
        prev = -1e9
        for c in cols:
            p = c.eval_psi(x, pf)
            if p <= prev + 1e-6:
                p = prev + 1e-6
            prev = p
            line.append(p)
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

    # Every distinct x asks _Prof for a fresh 561-point section - about 110 kB
    # each - and the annulus wants a different x at every one of its ~70 000
    # vertices, which is several gigabytes of section cache on a box with 11 GB.
    # Annulus points are therefore evaluated on a 0.4 mm ladder of stations and
    # interpolated between them. The body's lengthwise curvature over 0.4 mm is
    # about 2e-8 m of sagitta, four orders below anything that can shade.
    ANN_DX = 0.0004

    def ann_pt(xv, dv, fscale):
        q = xv / ANN_DX
        i0 = math.floor(q)
        t = q - i0
        a = full_pt(i0 * ANN_DX, dv, fscale)
        if t < 1e-9:
            return a
        b = full_pt((i0 + 1) * ANN_DX, dv, fscale)
        return (a[0] + (b[0] - a[0]) * t,
                a[1] + (b[1] - a[1]) * t,
                a[2] + (b[2] - a[2]) * t)

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
    anns = []
    warp = {}
    beads = {}
    edge = 3
    for hole in holes:
        curve = [(cx, sring(prof(cx), cp) - prof(cx).half)
                 for (cx, cp) in hole["curve"]]
        if hole.get("fair"):
            curve = _fair_outline(curve, hole["fair"], hole.get("rmin", 0.0))
        # D-MB37: a hole with `annulus` set has its whole bead band cut out of
        # the raster and rebuilt as a structured offset grid. The cut reaches
        # `annulus` metres of true surface distance outboard of the outline plus
        # `ann_margin` of clear, bead-free skin for the join, so the raster hole
        # boundary is guaranteed to sit outside the last analytic ring.
        aw = float(hole.get("annulus", 0.0) or 0.0)
        hdead = ring = None
        for attempt in (aw, 0.0):
            cut = curve
            if attempt > 0.0:
                cut = _offset_family(
                    curve, attempt + float(hole.get("ann_margin", 0.010)),
                    14)[-1]
            hd = _clean_dead(_cells_inside(rows, srs, nr, nc, cut, edge))
            rg = _dead_ring(hd)
            # two apertures whose cuts collide would each try to own the same
            # cells and the loser would be left with a floating rim
            if rg is not None and len(rg) >= 24 and not (dead & hd):
                hdead, ring, aw = hd, rg, attempt
                break
            if attempt > 0.0:
                print(f"!! {name}: annulus cut unusable - falling back")
        if ring is None:
            continue
        dead |= hdead

        if aw > 0.0:
            # D-MB37b: which end of the annulus carries the raster boundary's
            # vertex distribution matters. Laying it on the OUTLINE and letting
            # the family grow out to meet a boundary 34 mm further away
            # compresses the rim by the ratio of the two arclengths - about 2:1
            # where the outline turns at 36 mm radius - so a 2 mm rim spacing
            # became 0.3 mm and folded the lip built off it into back-to-back
            # slivers at x = -0.098. The correspondence is taken at the OUTER
            # ring instead, where it is a 1.17:1 stretch, and carried inward
            # along the family's own march lines. All quads, nothing to stitch.
            nseg = int(hole.get("ann_rings", 48))
            fam0 = _offset_family(curve, aw, nseg)
            outer = fam0[nseg]
            pos0 = [(rows[i], srs[i][j]) for (i, j) in ring]
            snap = _resample_ring(pos0, outer,
                                  even=float(hole.get("ann_even", 0.0)),
                                  smooth=int(hole.get("ann_smooth", 320)))
            mo = len(outer)
            oacc = [0.0] * (mo + 1)
            for k in range(mo):
                p2, q2 = outer[k], outer[(k + 1) % mo]
                oacc[k + 1] = oacc[k] + math.hypot(q2[0] - p2[0],
                                                   q2[1] - p2[1])
            uu = []
            for q in snap:                 # recover the fractional march index
                best, bu = 1e18, 0.0
                for k in range(mo):
                    ax, asv = outer[k]
                    ex = outer[(k + 1) % mo][0] - ax
                    es = outer[(k + 1) % mo][1] - asv
                    l2 = ex * ex + es * es
                    t = 0.0 if l2 < 1e-16 else max(0.0, min(
                        1.0, ((q.x - ax) * ex + (q.y - asv) * es) / l2))
                    dd = (ax + ex * t - q.x) ** 2 + (asv + es * t - q.y) ** 2
                    if dd < best:
                        best, bu = dd, k + t
                uu.append(bu)
            fam = []
            for m in range(nseg + 1):
                rg = fam0[m]
                row = []
                for u in uu:
                    k = int(u) % mo
                    t = u - int(u)
                    a2, b2 = rg[k], rg[(k + 1) % mo]
                    row.append((a2[0] + (b2[0] - a2[0]) * t,
                                a2[1] + (b2[1] - a2[1]) * t))
                fam.append(row)
            anns.append(dict(hole=hole, ring=ring, fam=fam,
                             bead=hole.get("bead", 0.0)))
            continue

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
            if abs(bead) > 1e-9:
                beads[k] = beads.get(k, 0.0) + bead * v[2]
        rims.append((hole, ring, rimf, bead))

    # apply the accumulated parameter-space warp once, so two apertures whose
    # blend bands touch add up instead of overwriting one another
    rimset = set()
    for (_h, ring, _f, _b) in rims:
        rimset.update(ring)
    for ((i, j), (dx, dsv, gw)) in warp.items():
        if (i, j) in rimset:
            continue
        grid[i][j] = full_pt(rows[i] + dx, srs[i][j] + dsv,
                             max(0.0, 1.0 - gw))
    # D-MB33: this loop used to read each vertex's normal off the grid it was
    # writing to, so whether a vertex saw its neighbours beaded or not depended
    # on dict iteration order. A 6 mm bead applied along a normal computed from
    # a half-updated neighbourhood throws vertices sideways by millimetres, and
    # THAT is what shattered the coaming into a crystalline band - not the rim
    # snap, which had already been cleaned up twice by then. Gather, then apply.
    bpts = []
    for ((i, j), bv) in beads.items():
        if (i, j) in rimset or abs(bv) < 1e-7:
            continue
        nn0 = _grid_n(grid, i, j, nr, nc, close_ring)
        bpts.append((i, j, tuple(Vector(grid[i][j]) + nn0 * bv)))
    for (i, j, p) in bpts:
        grid[i][j] = p
    for (_h, ring, rimf, bead) in rims:
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

    # ---- D-MB37: the coaming annulus ------------------------------------- #
    # One structured surface from the rim out to the raster's hole boundary.
    # Ring m sits at a TRUE m/M of the band width outboard of the outline, so
    # the bead is bead * smootherstep(1 - m/M) - a function of position and of
    # nothing else. Normals are gathered off the un-beaded base grid and only
    # then applied (the D-MB33 lesson), so no vertex can see a half-displaced
    # neighbour.
    rim_specs = []
    _pfr = prof(rows[ii])
    _ur, _sdr = psi_us(psis[ii][jj])
    _yr, _zr, _nyr, _nzr = _pfr.at(_ur)
    out_ref = Vector((0.0, _sdr * _nyr, _nzr))
    ann_flip = refn.dot(out_ref) < 0.0
    for spec in anns:
        fam = spec["fam"]
        aring = spec["ring"]
        bead = spec["bead"]
        nseg = len(fam) - 1
        an = len(fam[0])
        base = []
        for m in range(nseg + 1):
            fs = _feat_shape(m / float(nseg))
            base.append([ann_pt(p[0], p[1], fs) for p in fam[m]])

        votes = 0
        for k in range(0, an, max(1, an // 64)):
            du = Vector(base[0][(k + 1) % an]) - Vector(base[0][k - 1])
            dv = Vector(base[1][k]) - Vector(base[0][k])
            nn = du.cross(dv)
            pf2 = prof(round(fam[0][k][0] / ANN_DX) * ANN_DX)
            u2, sd2 = psi_us(psi_of_sring(pf2, pf2.half + fam[0][k][1]))
            _y2, _z2, ny2, nz2 = pf2.at(u2)
            votes += 1 if nn.dot(Vector((0.0, sd2 * ny2, nz2))) >= 0.0 else -1
        sgn = 1.0 if votes >= 0 else -1.0

        nrm = []
        for m in range(nseg + 1):
            hi_r = base[min(m + 1, nseg)]
            lo_r = base[max(m - 1, 0)]
            row = []
            for k in range(an):
                du = Vector(base[m][(k + 1) % an]) - Vector(base[m][k - 1])
                dv = Vector(hi_r[k]) - Vector(lo_r[k])
                nn = du.cross(dv) * sgn
                row.append(nn.normalized() if nn.length > 1e-12
                           else Vector((0.0, 0.0, 1.0)))
            nrm.append(row)
        # D-MB44: the bead is a 5.8 mm displacement, so the DIRECTION it is
        # applied in matters as much as the height. The reference surface still
        # carries the C0 kinks left where D-MB13's fairing clamps its station
        # curves back into their tolerance tube; on a 4.2 mm raster those are
        # smeared away, but the annulus samples at 0.43 mm and resolves them -
        # the rim normal turned 24 degrees in one 1.9 mm step at x = -0.100 and
        # threw the rim 2.4 mm sideways, which folded the coaming lip built off
        # it into back-to-back slivers. The bead direction is smoothed round and
        # across the band. The base points are untouched, so the skin stays
        # exactly where the contract puts it; only the direction is faired.
        for _ in range(9):
            for m in range(nseg + 1):
                row = nrm[m]
                nrm[m] = [(row[k] * 2.0 + row[k - 1] + row[(k + 1) % an])
                          for k in range(an)]
            for m in range(nseg + 1):
                a2 = nrm[max(m - 1, 0)]
                b2 = nrm[min(m + 1, nseg)]
                nrm[m] = [(nrm[m][k] * 2.0 + a2[k] + b2[k]).normalized()
                          if (nrm[m][k] * 2.0 + a2[k] + b2[k]).length > 1e-12
                          else Vector((0.0, 0.0, 1.0)) for k in range(an)]

        aidx = []
        for m in range(nseg + 1):
            h = bead * _bead_shape(m / float(nseg))
            aidx.append([vid(Vector(base[m][k]) + nrm[m][k] * h)
                         for k in range(an)])
        aidx.append([idx[k] for k in aring])     # bare raster hole boundary
        rev = (sgn < 0.0) != ann_flip
        for m in range(nseg + 1):
            for k in range(an):
                k2 = (k + 1) % an
                q = (aidx[m][k], aidx[m][k2], aidx[m + 1][k2], aidx[m + 1][k])
                faces.append(q[::-1] if rev else q)
                mids.append(0)

        basis = []
        for k in range(an):
            p = Vector(verts[aidx[0][k]])
            nn = nrm[0][k]
            ee = Vector(base[1][k]) - Vector(base[0][k])
            ee -= nn * ee.dot(nn)
            if ee.length < 1e-12:
                ee = Vector((1.0, 0.0, 0.0))
            basis.append((p, ee.normalized(), nn))
        rim_specs.append((spec["hole"], list(aidx[0]), basis))

    def edge_loop(loop, dirs, t, seg, fl, mid=0):
        n = len(loop)
        prev = [idx[k] for k in loop]
        r = t * 0.5
        rings = []
        for sgi in range(1, seg + 1):
            th = math.pi * sgi / seg
            cur = []
            for k, key in enumerate(loop):
                base = Vector(grid[key[0]][key[1]])
                e, nn = dirs[k]
                cur.append(vid(base + e * (r * math.sin(th))
                               - nn * (r - r * math.cos(th))))
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
        if not close_ring:
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
        edge_loop(loop, [dir_for(k) for k in loop], thick, roll_seg, flange)

    mth = mat_lip if mat_throat is None else mat_throat
    for (hole, ring, rimf, _bd) in rims:
        rim_specs.append((hole, [idx[k] for k in ring],
                          [(Vector(grid[k[0]][k[1]]), rimf[k][1], rimf[k][0])
                           for k in ring]))
    for (hole, prev0, basis) in rim_specs:
        if not hole.get("lip"):
            continue
        n = len(basis)
        nsum = Vector((0, 0, 0))
        for (_p, _e, nn) in basis:
            nsum += nn
        prev = list(prev0)
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

        cap_ax = -nsum.normalized() if nsum.length > 1e-9 else Vector((0, 0, -1))
        th = hole.get("throat")
        if th:
            # D-MB05: a duct mouth on a curved flank is a saddle, not a planar
            # loop. Scaling that rim about its centroid folded consecutive rings
            # through each other - the pinwheel of black petals in the sidepod
            # inlet. The throat now flattens the section onto the duct plane as
            # it goes back, which is what a real moulded duct does anyway.
            ax = th.get("axis")
            ax = cap_ax if ax is None else Vector(ax).normalized()
            cap_ax = ax
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
                bridge(cur, mth, prev)
                prev = cur

        if hole.get("cap", True):
            cc = Vector((0, 0, 0))
            for vi in prev:
                cc += Vector(verts[vi])
            cc /= len(prev)
            # D-MB41: a flat disc across the back of a duct is a hole in the
            # render. Pushing its centre back turns it into a shallow cone whose
            # walls are lit at different angles, which is what tells the eye
            # there is a volume behind the lip.
            cc = cc + cap_ax * float(hole.get("cap_depth", 0.0))
            ci = vid(cc)
            for k in range(n):
                k2 = (k + 1) % n
                tri = (prev[k], prev[k2], ci)
                faces.append(tri if flip else tri[::-1])
                mids.append(mth)

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


# D-MB43: both of these ran their panel's two edges together to EXACTLY the
# same psi at the panel's trailing station - a knife edge, which no laminate has
# and no mesh survives. Every column in that row lands on one parameter, the
# monotone guard spaces them a micron apart, and the result is a few hundred
# zero-area quads sharing edges: 287 of the part's 415 non-manifold edges were
# in the two sidepods for this reason. The edges now stop a few millimetres
# apart, which is also how the panel is actually made.
EDGE_MIN = 0.004


def sp_hi(x):
    return max(min(cover_lo(x), PK[5]), PK[2] + EDGE_MIN)


def sp_hi_r(x):
    return 2.0 - sp_hi(x)


def lf_hi(x):
    return max(min(PK[2], cover_lo(x)), PK[1] + EDGE_MIN)


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


# D-MB37: 320 segments round a 2.3 m outline is a 7.2 mm chord, and where the
# lens closes to a ~90 mm radius at its fore and aft tips that is a 4.7 degree
# kink in the rim every seven millimetres - visible faceting on the crown of the
# coaming bead itself, quite apart from the band behind it. The outline is a
# spline; sample it at the scale the rim is actually built to.
CK_SEG = 1200


def cockpit_curve():
    return _y_curve(COCKPIT, CK_SEG)


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
    # D-MB32 put 1.2 mm rows at all four aperture tips so a 4.2 mm raster could
    # follow an outline that turns 6 mm of half width per millimetre of x.
    # D-MB37 took the cockpit's coaming out of the raster altogether: its cut now
    # runs 34 mm outboard, where the outline is blunt, so the cockpit's two sets
    # of fine rows only make its hole boundary long and unevenly spaced - which
    # is what the annulus's tangential layout is inherited from. They are gone;
    # the airbox, still cut by the raster, keeps its own.
    tm_rows = make_rows(X_TUB_R + hx, X_SP_LE - hx,
                        dense=[(-0.44, 0.82, 0.0042),
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
                    throat=coam_throat, cap=True, blend=11,
                    # D-MB37: the coaming's bead band is not made of grid cells
                    # any more. 24 mm of it is cut out and rebuilt as 56 true
                    # offset rings of the outline (0.43 mm apart), so the bead
                    # is an analytic function of distance from the rim. 24 mm
                    # is as wide as the band can be and still leave the deck
                    # between the coaming and the airbox mouth intact - the two
                    # outlines are only 48 mm apart at the centreline.
                    annulus=0.024, ann_margin=0.010, ann_rings=56,
                    ann_step=0.0018,
                    fair=40, rmin=0.024),
               dict(curve=ab, bead=0.0009, lip=ab_lip,
                    throat=ab_throat, cap=True, blend=10)],
        mat_lip=1, mat_throat=2))
    made.extend(build_cell(coll))

    # ---- 4. sidepod bodywork -------------------------------------------- #
    inl_lip = [(0.0008, 0.0020), (0.0026, 0.0028), (0.0050, 0.0024),
               (0.0066, 0.0006), (0.0072, -0.0026), (0.0070, -0.0072)]
    # D-MB41: the inlet was a 84 mm blind sack that necked to 56 % of its mouth
    # in the last 6 mm, lined in MatteBlack. Nothing in there could catch a
    # photon, so behind a correctly rolled lip sat a flat black hole - the least
    # resolved aperture on the part. The duct now runs 150 mm back at close to
    # full area, so the key actually reaches the far wall, it is lined in
    # CarbonMatte like a real duct, and the back of it is a radiator face canted
    # 20 degrees to the mouth so it lights unevenly and reads as depth rather
    # than as a hole. It stays inboard of the sidepod part's own inner wall.
    inl_throat = dict(steps=[(0.014, 0.990, 0.30), (0.034, 0.975, 0.70),
                             (0.058, 0.958, 0.94), (0.084, 0.944, 1.00),
                             (0.110, 0.930, 1.00), (0.132, 0.918, 1.00),
                             (0.150, 0.905, 1.00)])
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
            ["LiveryPaint", "CarbonFibre", "CarbonMatte"], thick=T_SKIN,
            feats=sp_cr + sp_ln, cross=sp_x,
            holes=[dict(curve=icv, bead=0.0018, lip=inl_lip,
                        throat=inl_throat, cap=True, cap_depth=0.052,
                        blend=10)],
            mat_lip=1, mat_throat=2))

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
    up_ln = [LongLine(0.0, 0.060, -2.30, 1.95),
             LongLine(0.0, -0.060, -2.30, 1.95)]
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
    # D-MB40: the cap used to open with an extra full-section ring 0.4 mm
    # FORWARD of X_TAIL, so it stood proud of the tail fairing's own last row
    # and the joint read as a bulge with a shading step where it should read as
    # a closure. The collar is gone - the cap now starts exactly on the last
    # station - and its profile leaves that station along the body's own taper
    # instead of leaving it parallel, so the two surfaces are tangent and the
    # closure is flush. Its rings are also clustered toward the tip.
    ncap = 108
    CAPL = 0.015
    pf = prof(X_TAIL)
    cz = 0.5 * (pf.z[0] + pf.z[-1])
    base_ring = [spt(X_TAIL, 2.0 * i / ncap) for i in range(ncap)]
    _h0, _h1 = pf.half, prof(X_TAIL + 0.030).half
    taper = min(0.85, max(0.0, (_h1 - _h0) / max(_h1, 1e-6) * (CAPL / 0.030)))
    rings = []
    NC = 13
    for k in range(NC):
        t = math.sin(0.5 * math.pi * k / (NC - 1.0))
        x = X_TAIL - CAPL * t
        sc = ((1.0 - taper * t) * math.sqrt(max(0.0, 1.0 - t * t))
              * 0.998 + 0.002)
        rings.append([(x, p[1] * sc, cz + (p[2] - cz) * sc)
                      for p in base_ring])
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
    # stride keeps the surround fastener count at 16 whatever CK_SEG is
    for (cv, off, every, rr) in ((ck, 0.0560, CK_SEG // 16, 0.0058),
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

    return made
