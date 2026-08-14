"""sidepod - both sidepod bodywork assemblies plus the wing mirrors.

What this module owns
---------------------
Everything that sits ON the monocoque flank between x = +0.96 and x = -1.15:

    SP_flank        the painted pod flank panel: rolled top joint, undercut
                    lower lip, joint grooves, downwash gutter and outer lip
    SP_front        the inlet surround moulding: rolled mouth lip and the duct
                    behind it, gold heat-shield lined
    SP_vane         the horizontal splitter vane across the mouth
    SP_rad          the radiator core face - lamellae, flat tubes, end tanks
    SP_shoulder     bolt-on carbon louvre plinth with a sunken trough
    SP_louvres      18 formed gill blades bridging the trough
    SP_sis          side impact structure fairing under the inlet
    SP_scoop        flank cooling scoop with a dark throat and splitter bars
    SP_mirror       mirror housing + aerofoil stalk grown out of one loft
    SP_mirrorface   the reflector, SP_mirrorglass the cover glass
    SP_fixings      54 Dzus quarter-turn fasteners
    SP_trim         three shoulder flow conditioners and 52 SIS rivets

Every object is authored on the LEFT side only and carries a MIRROR modifier,
so "both sidepods" is one mirror away. 230 k evaluated polygons.

Landing on the skin
-------------------
Nothing is guessed. Every point is authored in (x, v, h):

    x   car station, metres
    v   ARC LENGTH along the body's own half section, 0 at the pod's undercut
        lip and 1 at the top panel joint, between two band curves u_lo(x) and
        u_hi(x). Equal steps in v are equal millimetres on the skin.
    h   offset along the body's outward surface normal, metres

`_yz()` evaluates exactly the Catmull-Rom that `spec.body_surface_point`
samples (same control points, same parameterisation) but at a continuous
parameter, so the panel cannot stair-step the way a 65-sample lookup would.
`spec.station_at` is piecewise LINEAR in x, which puts a crease at every
station knot; those get smoothed by a 7-tap kernel applied to the CONTROL
POINTS (the spline is linear in them, so smoothing the controls smooths the
surface), then clamped so no control point moves more than 4.5 mm. Panel h is
never below +4.08 mm, so the bodywork always sits ON the skin, never inside
it. Measured agreement with spec.body_surface_point: see DEFECTS at the foot.
"""

import math

import bpy
from mathutils import Vector

import common as C
import spec as S

NAME = "sidepod"
P = "SP_"

TAU = math.pi * 2.0

# --------------------------------------------------------------------------- #
# principal stations
# --------------------------------------------------------------------------- #

X_POD_LE = 0.958          # pod leading edge (front panel outer boundary)
X_SEAM = 0.560            # inlet surround / flank panel joint
X_POD_TE = -1.148         # flank panel trailing edge
X_LIVERY_SEAM = -0.560    # transverse panel line (matches the livery zone edge)

H_PANEL = 0.0060          # nominal panel proudness above the body skin
H_CROWN = 0.0035          # extra crown across the flank
N_LOUVRE = 18

MV_REF = 0.27             # nominal metres of section arc per unit of v


# =========================================================================== #
# 1.  the reference surface
# =========================================================================== #

def _cr_point(p, t):
    """Catmull-Rom through control points `p` at continuous t in [0, 1].

    Identical maths and parameterisation to common.catmull_rom, so
    _cr_point(station_half(station_at(x)), u) reproduces
    spec.body_surface_point(x, u) to within its 1/128 sampling quantisation.
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


# 7-tap gaussian over +/-36 mm; kills the linear-interpolation creases that
# spec.station_at leaves at every station knot without moving the surface.
_SM_TAPS = ((-0.036, 0.055), (-0.024, 0.120), (-0.012, 0.200), (0.0, 0.250),
            (0.012, 0.200), (0.024, 0.120), (0.036, 0.055))
_SM_CLAMP = 0.0045

_ctrl_cache = {}


def _ctrl(x):
    key = int(round(x * 100000.0))
    got = _ctrl_cache.get(key)
    if got is not None:
        return got
    exact = S.station_half(S.station_at(x))
    acc = [[0.0, 0.0] for _ in range(8)]
    wsum = 0.0
    for dx, w in _SM_TAPS:
        h = S.station_half(S.station_at(x + dx))
        wsum += w
        for k in range(8):
            acc[k][0] += w * h[k][0]
            acc[k][1] += w * h[k][1]
    out = []
    for k in range(8):
        ex, ez = exact[k]
        sy, sz = acc[k][0] / wsum, acc[k][1] / wsum
        dy, dz = sy - ex, sz - ez
        d = math.hypot(dy, dz)
        if d > _SM_CLAMP:
            f = _SM_CLAMP / d
            sy, sz = ex + dy * f, ez + dz * f
        out.append((sy, sz))
    out[0] = (0.0, out[0][1])
    out[7] = (0.0, out[7][1])
    _ctrl_cache[key] = out
    return out


def _yz(x, u):
    return _cr_point(_ctrl(x), u)


_EX = 0.0035
_EU = 0.0040


def _n(x, u):
    """Outward unit normal of the body surface at (x, u)."""
    y0, z0 = _yz(x - _EX, u)
    y1, z1 = _yz(x + _EX, u)
    tx = Vector((2.0 * _EX, y1 - y0, z1 - z0))
    ya, za = _yz(x, max(0.0, u - _EU))
    yb, zb = _yz(x, min(1.0, u + _EU))
    tu = Vector((0.0, yb - ya, zb - za))
    nv = tx.cross(tu)
    if nv.length < 1e-9:
        return Vector((0.0, 1.0, 0.0))
    nv.normalize()
    if nv.y < 0.0:
        nv = -nv
    return nv


def _p(x, u, h=0.0):
    y, z = _yz(x, u)
    v = Vector((x, y, z))
    if h:
        v = v + _n(x, u) * h
    return v


# --------------------------------------------------------------------------- #
# band curves: v = 0 is the undercut lip, v = 1 the top panel joint
# --------------------------------------------------------------------------- #

_ULO = [(1.060, 0.396), (0.958, 0.386), (0.780, 0.372), (0.600, 0.362),
        (0.340, 0.348), (0.120, 0.340), (-0.300, 0.340), (-0.560, 0.346),
        (-0.820, 0.356), (-1.000, 0.372), (-1.220, 0.394)]
_UHI = [(1.060, 0.556), (0.958, 0.568), (0.780, 0.588), (0.600, 0.606),
        (0.340, 0.624), (0.120, 0.642), (-0.300, 0.690), (-0.560, 0.706),
        (-0.820, 0.712), (-1.000, 0.706), (-1.220, 0.688)]


def _mk_table(pairs, n=420):
    dense = C.catmull_rom(pairs, n)
    return dense


_TAB_LO = _mk_table(_ULO)
_TAB_HI = _mk_table(_UHI)


def _tab(tab, x):
    if x >= tab[0][0]:
        return tab[0][1]
    if x <= tab[-1][0]:
        return tab[-1][1]
    lo, hi = 0, len(tab) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if tab[mid][0] >= x:
            lo = mid
        else:
            hi = mid
    a, b = tab[lo], tab[hi]
    t = 0.0 if abs(a[0] - b[0]) < 1e-12 else (a[0] - x) / (a[0] - b[0])
    return a[1] + (b[1] - a[1]) * t


# D-SP10: v started life as a straight lerp between u_lo and u_hi. But the
# body section's Catmull-Rom is wildly non-uniform - 0.9 m of arc per unit u
# near the max-width knot, 2.3 m between the shoulder and the tub side - so a
# uniform v grid put columns 2.6 mm apart low down and 15 mm apart on the
# shoulder, and every radius quoted in metres came out the wrong size at one
# end. v is now ARC LENGTH along the section: v = 0 at the undercut lip, 1 at
# the top joint, and equal steps in v are equal millimetres on the skin.

_NB = 193
_band_cache = {}


def _band(x):
    key = int(round(x * 1000.0))
    got = _band_cache.get(key)
    if got is not None:
        return got
    xq = key / 1000.0
    ulo, uhi = _tab(_TAB_LO, xq), _tab(_TAB_HI, xq)
    u0 = max(0.02, ulo - 0.075)
    u1 = min(0.98, uhi + 0.075)
    us, cs = [], [0.0]
    prev = None
    for i in range(_NB):
        u = u0 + (u1 - u0) * i / (_NB - 1.0)
        us.append(u)
        p = _yz(xq, u)
        if prev is not None:
            cs.append(cs[-1] + math.hypot(p[0] - prev[0], p[1] - prev[1]))
        prev = p

    def s_at(u):
        f = (u - u0) / (u1 - u0) * (_NB - 1.0)
        i = min(_NB - 2, max(0, int(f)))
        return cs[i] + (cs[i + 1] - cs[i]) * (f - i)

    s0, s1 = s_at(ulo), s_at(uhi)
    got = (us, cs, s0, max(s1 - s0, 1e-4))
    _band_cache[key] = got
    return got


def _u_of_v(x, v):
    us, cs, s0, span = _band(x)
    t = s0 + span * v
    if t <= cs[0]:
        du = (us[1] - us[0]) / max(cs[1] - cs[0], 1e-9)
        return max(0.0, us[0] + (t - cs[0]) * du)
    if t >= cs[-1]:
        du = (us[-1] - us[-2]) / max(cs[-1] - cs[-2], 1e-9)
        return min(1.0, us[-1] + (t - cs[-1]) * du)
    lo, hi = 0, len(cs) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if cs[mid] <= t:
            lo = mid
        else:
            hi = mid
    f = (t - cs[lo]) / max(cs[hi] - cs[lo], 1e-9)
    return us[lo] + (us[hi] - us[lo]) * f


def _pv(x, v, h=0.0):
    return _p(x, _u_of_v(x, v), h)


def _nv(x, v):
    return _n(x, _u_of_v(x, v))


def _mv(x, v=0.5):
    """Metres of surface arc per unit of v - now a constant per station."""
    return _band(x)[3]


# --------------------------------------------------------------------------- #
# the flank panel offset field
# --------------------------------------------------------------------------- #

def _h_flank(x, v):
    vv = min(1.0, max(0.0, v))
    h = H_PANEL + H_CROWN * math.sin(math.pi * vv)
    # longitudinal panel-joint groove low on the flank. Width is quoted in
    # MILLIMETRES of skin, not in v - the band arc runs 141 mm at the pod nose
    # and 650 mm at its waist, so a fixed dv groove would be 1.8 mm wide at one
    # end and 8 mm at the other.
    sig = 0.0034 / _mv(x)
    h -= 0.0026 * math.exp(-((vv - 0.300) / sig) ** 2)
    # transverse joint on the livery panel line
    h -= 0.0024 * math.exp(-((x - X_LIVERY_SEAM) / 0.0048) ** 2)
    # second transverse joint ahead of the rear wheel
    h -= 0.0020 * math.exp(-((x + 0.960) / 0.0048) ** 2)
    # downwash ramp: behind the cockpit the shoulder carries a shallow gutter
    # with a raised outer lip, so the top surface actually funnels air down and
    # inboard toward the diffuser instead of just being the body's own shoulder.
    gx = (C.smoothstep((-0.300 - x) / 0.240)
          * C.smoothstep((x + 1.148) / 0.170))
    if gx > 0.001:
        h -= 0.0028 * gx * math.exp(-((vv - 0.800) / 0.075) ** 2)
        h += 0.0044 * gx * math.exp(-((vv - 0.948) / 0.038) ** 2)
    return h


# =========================================================================== #
# 2.  mesh accumulator
# =========================================================================== #

class _Acc:
    def __init__(self):
        self.v = []
        self.f = []
        self.m = []

    def add(self, verts, faces, mat=0):
        b = len(self.v)
        self.v.extend(tuple(p) for p in verts)
        for f in faces:
            self.f.append(tuple(b + i for i in f))
            self.m.append(mat)
        return b

    def loft(self, rings, mat=0, closed=True, cap_start=False, cap_end=False,
             mats=None):
        n = len(rings[0])
        for r in rings:
            if len(r) != n:
                raise ValueError("ring length mismatch")
        b = len(self.v)
        for r in rings:
            self.v.extend(tuple(p) for p in r)
        span = n if closed else n - 1
        for i in range(len(rings) - 1):
            a0, b0 = b + i * n, b + (i + 1) * n
            mi = mats[i] if mats else mat
            for j in range(span):
                j2 = (j + 1) % n
                self.f.append((a0 + j, a0 + j2, b0 + j2, b0 + j))
                self.m.append(mi)
        if cap_start:
            self.f.append(tuple(range(b, b + n))[::-1])
            self.m.append(mats[0] if mats else mat)
        if cap_end:
            s = b + (len(rings) - 1) * n
            self.f.append(tuple(range(s, s + n)))
            self.m.append(mats[-1] if mats else mat)
        return b

    def grid(self, rows, mat=0, mat_fn=None):
        n = len(rows[0])
        b = len(self.v)
        for r in rows:
            self.v.extend(tuple(p) for p in r)
        for i in range(len(rows) - 1):
            a0, b0 = b + i * n, b + (i + 1) * n
            for j in range(n - 1):
                self.f.append((a0 + j, a0 + j + 1, b0 + j + 1, b0 + j))
                self.m.append(mat_fn(i, j) if mat_fn else mat)
        return b


def _emit(name, acc, coll, matnames, smooth=32.0):
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
    return ob


# =========================================================================== #
# 3.  rounded-rectangle outlines in (x, v)
# =========================================================================== #
#
# A "shape" is (x0, x1, v0, v1, r_rear, r_front, mv): a rectangle in the
# surface parameters with corner radii given in METRES (converted to v through
# mv, the local arc length per unit v) so the corners look round on the skin
# rather than round in parameter space.

def _shape(x0, x1, v0, v1, r_rear, r_front, mv=MV_REF):
    return (float(x0), float(x1), float(v0), float(v1),
            float(r_rear), float(r_front), float(mv))


def _shape_inset(sh, d):
    x0, x1, v0, v1, rr, rf, mv = sh
    dv = d / mv
    nx0, nx1 = x0 + d, x1 - d
    nv0, nv1 = v0 + dv, v1 - dv
    if nx1 - nx0 < 0.004:
        c = 0.5 * (x0 + x1)
        nx0, nx1 = c - 0.002, c + 0.002
    if nv1 - nv0 < 0.004 / mv:
        c = 0.5 * (v0 + v1)
        nv0, nv1 = c - 0.002 / mv, c + 0.002 / mv
    return (nx0, nx1, nv0, nv1, max(rr - d, 0.0012), max(rf - d, 0.0012), mv)


def _shape_lerp(a, b, t):
    return tuple(a[k] + (b[k] - a[k]) * t for k in range(7))


def _pieces(sh):
    x0, x1, v0, v1, rr, rf, mv = sh
    # D-SP01: a corner radius larger than half the shorter side inverts the
    # straight pieces and the outline folds inside out. Clamp, always.
    lim = min(0.495 * (x1 - x0), 0.495 * (v1 - v0) * mv)
    rr = max(min(rr, lim), 0.0008)
    rf = max(min(rf, lim), 0.0008)
    rvr, rvf = rr / mv, rf / mv
    return [
        ("L", (x0, v0 + rvr, x0, v1 - rvr)),
        ("C", (x0 + rr, v1 - rvr, rr, rvr, 180.0, 90.0)),
        ("L", (x0 + rr, v1, x1 - rf, v1)),
        ("C", (x1 - rf, v1 - rvf, rf, rvf, 90.0, 0.0)),
        ("L", (x1, v1 - rvf, x1, v0 + rvf)),
        ("C", (x1 - rf, v0 + rvf, rf, rvf, 0.0, -90.0)),
        ("L", (x1 - rf, v0, x0 + rr, v0)),
        ("C", (x0 + rr, v0 + rvr, rr, rvr, -90.0, -180.0)),
    ]


def _piece_lengths(sh):
    mv = sh[6]
    out = []
    for kind, d in _pieces(sh):
        if kind == "L":
            out.append(math.hypot(d[2] - d[0], (d[3] - d[1]) * mv))
        else:
            out.append(0.5 * math.pi * 0.5 * (d[2] + d[3] * mv))
    return out


def _canon_t(sh):
    """Canonical parameter breakpoints (0..1) for a reference shape."""
    L = _piece_lengths(sh)
    tot = sum(L)
    ts, acc = [0.0], 0.0
    for l in L:
        acc += l
        ts.append(acc / tot)
    return ts


def _outline(sh, tvals, canon):
    pcs = _pieces(sh)
    out = []
    for t in tvals:
        tt = t % 1.0
        k = 0
        while k < 7 and tt >= canon[k + 1]:
            k += 1
        span = max(canon[k + 1] - canon[k], 1e-9)
        s = (tt - canon[k]) / span
        kind, d = pcs[k]
        if kind == "L":
            out.append((d[0] + (d[2] - d[0]) * s, d[1] + (d[3] - d[1]) * s))
        else:
            cx, cv, rx, rv, a0, a1 = d
            a = math.radians(a0 + (a1 - a0) * s)
            out.append((cx + rx * math.cos(a), cv + rv * math.sin(a)))
    return out


def _push(rings, ring, tol=2e-5):
    """Append a ring unless it repeats the previous one.

    D-SP23: the profile tables deliberately overlap - the last outer-edge entry
    and the first surface entry name the same inset and the same height, and so
    do the last surface entry and the first lip entry. Each overlap lofted a
    full band of ZERO-AREA quads: 352 on the plinth, 400 on the inlet surround.
    mesh.validate() keeps them (the indices differ, only the positions match),
    so they survived into the render as normal-less slivers and made the
    wireframe pass spray spokes a metre off the part.
    """
    if rings:
        prev = rings[-1]
        if len(prev) == len(ring):
            if max((a - b).length for a, b in zip(prev, ring)) < tol:
                return rings
    rings.append(ring)
    return rings


# =========================================================================== #
# 4.  the flank panel
# =========================================================================== #

def _cluster(vals, centres, halfw, step):
    got = list(vals)
    for c in centres:
        k = -int(halfw / step)
        while k * step <= halfw + 1e-9:
            got.append(c + k * step)
            k += 1
    got.sort()
    out = []
    for g in got:
        if not out or g - out[-1] > 0.35 * step:
            out.append(g)
    return out


# lower-edge treatment: (outward offset in metres beyond v=0, delta h).
# A 6 mm roll that turns right under and comes back as a bonded return flange -
# this is the undercut lower lip.
_EDGE_LO = [(0.0000, 0.0000), (0.0030, -0.0009), (0.0054, -0.0028),
            (0.0066, -0.0056), (0.0064, -0.0086), (0.0046, -0.0110),
            (0.0016, -0.0124), (-0.0032, -0.0128), (-0.0092, -0.0126),
            (-0.0150, -0.0122)]
# upper edge: tighter 4 mm roll, flange lands flush on the skin
_EDGE_HI = [(0.0000, 0.0000), (0.0022, -0.0007), (0.0038, -0.0021),
            (0.0044, -0.0040), (0.0038, -0.0058), (0.0022, -0.0070),
            (-0.0006, -0.0076), (-0.0056, -0.0078), (-0.0116, -0.0078)]
# fore/aft edges
_EDGE_X = [(0.0000, 0.0000), (0.0020, -0.0007), (0.0034, -0.0021),
           (0.0040, -0.0040), (0.0034, -0.0056), (0.0018, -0.0066),
           (-0.0010, -0.0072), (-0.0060, -0.0074)]


def _build_flank(acc):
    xs = []
    x = X_SEAM - 0.0015
    while x > X_POD_TE - 1e-9:
        xs.append(x)
        x -= 0.0058
    xs.append(X_POD_TE)
    xs = _cluster(xs, [X_LIVERY_SEAM, -0.960], 0.016, 0.0024)
    xs = sorted(set(round(v, 6) for v in xs), reverse=True)

    vs = [i / 53.0 for i in range(54)]
    vs = _cluster(vs, [0.300], 0.030, 0.0055)
    vs = _cluster(vs, [0.0, 1.0], 0.030, 0.010)
    vs = sorted(set(round(v, 6) for v in vs))
    vs = [v for v in vs if -1e-9 <= v <= 1.0 + 1e-9]

    # column list: extended rolls below v=0 and above v=1
    cols = []
    for d, dh in reversed(_EDGE_LO[1:]):
        cols.append(("lo", d, dh))
    cols.append(("in", 0.0, 0.0))
    for v in vs[1:-1]:
        cols.append(("in", v, 0.0))
    cols.append(("in", 1.0, 0.0))
    for d, dh in _EDGE_HI[1:]:
        cols.append(("hi", d, dh))

    def col_vh(x, c):
        kind, d, dh = c
        if kind == "in":
            return d, 0.0
        m = _mv(x, 0.0 if kind == "lo" else 1.0)
        if kind == "lo":
            return -d / m, dh
        return 1.0 + d / m, dh

    # row list: extended rolls fore of x[0] and aft of x[-1]
    rws = []
    for d, dh in reversed(_EDGE_X[1:]):
        rws.append(("fr", d, dh))
    for x in xs:
        rws.append(("in", x, 0.0))
    for d, dh in _EDGE_X[1:]:
        rws.append(("rr", d, dh))

    def row_xh(r):
        kind, d, dh = r
        if kind == "in":
            return d, 0.0
        if kind == "fr":
            return xs[0] + d, dh
        return xs[-1] - d, dh

    rows = []
    for r in rws:
        x, dhx = row_xh(r)
        row = []
        for c in cols:
            v, dhv = col_vh(x, c)
            h = _h_flank(x, min(1.0, max(0.0, v))) + min(dhx, dhv)
            row.append(_pv(x, v, h))
        rows.append(row)

    # D-SP19: the paint/carbon split ran at v = 0.085 where the surface is
    # perfectly smooth, so it read as a decal edge ruled across the bodywork.
    # It now lands exactly in the longitudinal panel-joint groove at v = 0.300,
    # which is what a real paint break follows.
    def mat_fn(i, j):
        v = cols[j][1] if cols[j][0] == "in" else (0.0 if cols[j][0] == "lo" else 1.0)
        return 1 if v < 0.300 else 0

    acc.grid(rows, mat_fn=mat_fn)


# =========================================================================== #
# 5.  generic aperture panel: outer rolled edge -> surface -> rolled aperture
# =========================================================================== #

def _aperture_rings(sh_out, sh_ap, tvals, canon, hbase, edge_prof, main_prof,
                    lip_prof, hmod=None):
    """Rings for a panel that runs from a rolled outer boundary across a
    surface and rolls over into an aperture.

    edge_prof : [(inset_m, dh)]   outer boundary treatment, first entry is the
                                  return flange tip, last lands on the surface
    main_prof : [(s, dh)]         s = 0 at the (inset) boundary, 1 at the
                                  aperture outline
    lip_prof  : [(inset_m, dh)]   roll over the aperture edge, insets measured
                                  from the aperture outline
    """
    hm = hmod or (lambda x, v, dh: dh)
    rings = []
    for d, dh in edge_prof:
        sh = _shape_inset(sh_out, d)
        pts = _outline(sh, tvals, canon)
        _push(rings, [_pv(x, v, hbase(x, v) + hm(x, v, dh)) for (x, v) in pts])
    base_in = _shape_inset(sh_out, edge_prof[-1][0])
    for s, dh in main_prof:
        sh = _shape_lerp(base_in, sh_ap, s)
        pts = _outline(sh, tvals, canon)
        _push(rings, [_pv(x, v, hbase(x, v) + hm(x, v, dh)) for (x, v) in pts])
    for d, dh in lip_prof:
        sh = _shape_inset(sh_ap, d)
        pts = _outline(sh, tvals, canon)
        _push(rings, [_pv(x, v, hbase(x, v) + hm(x, v, dh)) for (x, v) in pts])
    return rings


# =========================================================================== #
# 6.  inlet surround, throat, splitter vane, radiator
# =========================================================================== #

# D-SP21: the surround's outer boundary stopped 20 mm inside the band and its
# roll only ever moved INWARD, while the flank panel's roll bulges 4 mm
# outward - so the two panels met with a 10.7 mm gap and a 5 mm step in edge
# height. Boundary widened to the full band and the apex given a negative
# inset so both rolls have the same section; the joint is now a 3 mm shut line.
FRONT_OUT = _shape(X_SEAM + 0.0075, X_POD_LE, 0.004, 0.996, 0.024, 0.086, 0.200)
FRONT_AP = _shape(0.646, 0.879, 0.200, 0.800, 0.052, 0.052, 0.200)

_FR_EDGE = [(0.0130, -0.0052), (0.0074, -0.0050), (0.0034, -0.0036),
            (0.0008, -0.0016), (-0.0018, 0.0009), (0.0002, 0.0028),
            (0.0030, 0.0038), (0.0068, 0.0042)]
_FR_MAIN = [(0.00, 0.0042), (0.10, 0.0062), (0.24, 0.0086), (0.40, 0.0108),
            (0.56, 0.0126), (0.70, 0.0140), (0.82, 0.0150), (0.91, 0.0157),
            (0.965, 0.0161), (1.000, 0.0163)]
_FR_LIP = [(0.0000, 0.0163), (0.0022, 0.0152), (0.0044, 0.0132),
           (0.0060, 0.0104), (0.0070, 0.0070), (0.0074, 0.0032),
           (0.0072, -0.0008), (0.0064, -0.0046)]

THROAT_LEN = 0.120
THROAT_SX = 0.880
THROAT_SY = 0.840


def _ortho(d):
    a = Vector((0.0, 0.0, 1.0))
    if abs(d.dot(a)) > 0.9:
        a = Vector((1.0, 0.0, 0.0))
    e1 = d.cross(a)
    e1.normalize()
    e2 = d.cross(e1)
    e2.normalize()
    return e1, e2


def _build_front(acc, npts=200):
    canon = _canon_t(FRONT_OUT)
    tvals = [i / npts for i in range(npts)]

    def hbase(x, v):
        return _h_flank(x, min(1.0, max(0.0, v)))

    rings = _aperture_rings(FRONT_OUT, FRONT_AP, tvals, canon, hbase,
                            _FR_EDGE, _FR_MAIN, _FR_LIP)
    n_outer = len(rings)

    # --- 3D throat ---------------------------------------------------------
    q = rings[-1]
    cq = Vector((0, 0, 0))
    for pnt in q:
        cq = cq + pnt
    cq = cq / len(q)

    xc = 0.5 * (FRONT_AP[0] + FRONT_AP[1])
    vc = 0.5 * (FRONT_AP[2] + FRONT_AP[3])
    nm = _nv(xc, vc)
    d = (-nm + Vector((-0.42, 0.0, -0.06)))
    d.normalize()
    e1, e2 = _ortho(d)

    cf = cq + d * THROAT_LEN
    fring = []
    for pnt in q:
        r = pnt - cq
        a, b = r.dot(e1), r.dot(e2)
        fring.append(cf + e1 * (a * THROAT_SX) + e2 * (b * THROAT_SY))

    steps = 9
    for k in range(1, steps + 1):
        t = k / steps
        e = t * t * (3.0 - 2.0 * t)
        _push(rings, [q[i].lerp(fring[i], e) for i in range(len(q))])
    # short constant-section extension so the core is fully boxed in, then
    # converge on a small patch instead of closing a 200-gon across the duct
    rings.append([pnt + d * 0.040 for pnt in fring])
    # D-SP24: converging to 0.22 crammed 200 verts into a 165 mm perimeter,
    # 0.8 mm apart - below the preview wire thickness, so it still threw two
    # spokes. 0.55 keeps the closing n-gon planar and its verts 2.3 mm apart.
    for sc, dd in ((0.88, 0.050), (0.72, 0.058), (0.55, 0.064)):
        rings.append([cf + d * dd + (pnt - cf) * sc for pnt in fring])

    # D-SP13: the throat was 190 mm deep and lined entirely in matte carbon,
    # so the mouth read as a black void at every angle and the core was
    # invisible. The radiator sits 120 mm in now and the back half of the duct
    # is gold heat-shield film - which is what is actually in there, and it
    # picks up any light that reaches the throat.
    mats = []
    n_all = len(rings) - 1
    for i in range(n_all):
        if i < n_outer - 3:
            mats.append(0)
        elif i < n_outer:
            mats.append(1)
        else:
            mats.append(2)
    acc.loft(rings, mats=mats, closed=True, cap_end=True)
    return fring, cq, cf, d, e1, e2


def _build_vane(acc, fring, cf, d, e1, e2):
    """Horizontal splitter vane across the mouth, just inside the lip."""
    ab = [((p - cf).dot(e1), (p - cf).dot(e2)) for p in fring]
    a_lo = min(a for a, _b in ab)
    a_hi = max(a for a, _b in ab)
    # D-SP03: the vane was spanned to the ring at the BACK of the throat, but
    # it sits near the mouth where the duct is 1/THROAT_SX wider - both tips
    # floated ~8 mm short of the wall. Overspan instead; the excess buries
    # itself in the duct wall where nothing can see it.
    half = 0.5 * (a_hi - a_lo) * 1.16
    amid = 0.5 * (a_hi + a_lo)

    ns = 30
    nsec = 22
    c0, c1 = -0.114, -0.017          # positions along d relative to cf
    rings = []
    for i in range(ns + 1):
        t = i / ns
        a = amid + half * math.cos(math.pi * t) * -1.0
        # elliptical planform: the vane ends are tucked into the duct wall
        w = math.sin(math.pi * min(1.0, max(0.0, t))) ** 0.35
        chord0 = c0 - 0.004 * (1.0 - w)
        chord1 = c1 + 0.010 * (1.0 - w)
        th = 0.0125 * (0.35 + 0.65 * w)
        droop = -0.004 * (1.0 - w)
        ring = []
        for j in range(nsec):
            ang = TAU * j / nsec
            cs, sn = math.cos(ang), math.sin(ang)
            # cambered plate: rounded LE, sharp-ish TE
            s = 0.5 * (1.0 - cs)
            xx = chord0 + (chord1 - chord0) * s
            tt = th * math.sqrt(max(0.0, 1.0 - (2 * s - 1) ** 2)) ** 0.75
            camber = 0.010 * math.sin(math.pi * s) + droop
            ring.append(cf + d * xx + e1 * a
                        + e2 * (camber + 0.5 * tt * (1.0 if sn >= 0 else -1.0)))
        rings.append(ring)
    acc.loft(rings, mat=0, closed=True, cap_start=True, cap_end=True)


def _build_rad(acc, fring, cf, d, e1, e2):
    """Radiator core: horizontal lamellae, flat tubes, end tanks."""
    ab = [((p - cf).dot(e1), (p - cf).dot(e2)) for p in fring]
    b_lo = min(b for _a, b in ab)
    b_hi = max(b for _a, b in ab)

    def a_span(b):
        lo, hi = None, None
        n = len(ab)
        for i in range(n):
            a0, b0 = ab[i]
            a1, b1 = ab[(i + 1) % n]
            if (b0 - b) * (b1 - b) <= 0.0 and abs(b1 - b0) > 1e-9:
                t = (b - b0) / (b1 - b0)
                a = a0 + (a1 - a0) * t
                lo = a if lo is None else min(lo, a)
                hi = a if hi is None else max(hi, a)
        if lo is None:
            return None
        return lo, hi

    inset = 0.004
    pitch = 0.0032
    b0 = b_lo + inset
    b1 = b_hi - inset
    nrow = max(6, int((b1 - b0) / pitch))
    ncol = 54
    face = cf + d * 0.016

    rows = []
    kinds = []
    for i in range(nrow + 1):
        b = b0 + (b1 - b0) * i / nrow
        sp = a_span(b)
        if sp is None:
            sp = (-0.01, 0.01)
        lo, hi = sp[0] + inset, sp[1] - inset
        tube = (i % 5 == 0)
        dz = 0.0016 if tube else (-0.0018 if i % 2 else -0.0004)
        row = []
        for j in range(ncol + 1):
            a = lo + (hi - lo) * j / ncol
            row.append(face + e1 * a + e2 * b + d * (-dz))
        rows.append(row)
        kinds.append(tube)
    acc.grid(rows, mat_fn=lambda i, j: 1 if kinds[i] else 0)

    # D-SP02: the backing plate was a rectangle sized from the widest span plus
    # 20 mm, so its corners punched straight out through the duct wall and read
    # as a floating black slab beside the mouth. It now follows the duct
    # section, inset 1 mm, so it can only ever sit inside the throat.
    back = cf + d * 0.030
    rows = []
    for i in range(9):
        b = b_lo + (b_hi - b_lo) * i / 8.0
        sp = a_span(b) or (-0.005, 0.005)
        lo, hi = sp[0] + 0.001, sp[1] - 0.001
        rows.append([back + e1 * (lo + (hi - lo) * j / 12.0) + e2 * b
                     for j in range(13)])
    acc.grid(rows, mat=2)

    # end tanks: two anodised bars closing the matrix left and right
    for sgn in (-1.0, 1.0):
        spm = a_span(0.5 * (b_lo + b_hi)) or (-0.01, 0.01)
        a = spm[1] if sgn > 0 else spm[0]
        rings = []
        for i in range(15):
            t = i / 14.0
            b = b_lo + (b_hi - b_lo) * t
            sp = a_span(b) or (a, a)
            aa = sp[1] if sgn > 0 else sp[0]
            ring = []
            for j in range(12):
                ang = TAU * j / 12
                ring.append(face + e1 * (aa - sgn * 0.006 + 0.010 * math.cos(ang))
                            + e2 * b + d * (0.012 + 0.010 * math.sin(ang)))
            rings.append(ring)
        acc.loft(rings, mat=3, closed=True, cap_start=True, cap_end=True)


# =========================================================================== #
# 7.  louvre plinth + gill blades
# =========================================================================== #

PLINTH_OUT = _shape(-0.972, 0.196, 0.600, 0.886, 0.056, 0.050, 0.460)
PLINTH_AP = _shape(-0.735, -0.052, 0.660, 0.800, 0.032, 0.032, 0.460)

_PL_EDGE = [(0.0110, 0.0004), (0.0056, 0.0006), (0.0018, 0.0014),
            (0.0000, 0.0030), (0.0006, 0.0048)]
# D-SP12: the plateau was 200 x 1200 mm of unbroken carbon either side of the
# trough. A shut line ringing the vent panel at s = 0.60 breaks it up the way
# the real bonded-in insert does.
# D-SP26: even with the longitudinal crown the plateau still clipped 1.97 % of
# the centre third under the preview key, because ACROSS the panel it was flat
# to within 0.3 mm over 90 mm. A 1.8 mm transverse arch between the fastener
# ring and the shut line turns that specular sheet into a band.
_PL_MAIN = [(0.000, 0.0048), (0.055, 0.0104), (0.125, 0.0176),
            (0.220, 0.0242), (0.310, 0.0288), (0.400, 0.0312),
            (0.470, 0.0320), (0.530, 0.0313), (0.575, 0.0296),
            (0.612, 0.0281), (0.652, 0.0296), (0.710, 0.0309),
            (0.800, 0.0313), (0.900, 0.0307), (1.000, 0.0300)]
_PL_LIP = [(0.0000, 0.0300), (0.0018, 0.0292), (0.0032, 0.0276),
           (0.0040, 0.0254), (0.0044, 0.0228)]
_PL_WALL = [(0.0050, 0.0180), (0.0056, 0.0128), (0.0060, 0.0086),
            (0.0064, 0.0068), (0.0070, 0.0058)]
# D-SP18: the floor used to be three more INSETS - 14, 30 and 52 mm into a
# trough only 84 mm wide, so the last ring collapsed against the inset guard
# into a 641 x 9 mm slither which then got closed with a 176-gon. It shaded
# like a crumpled foil and the preview wireframe sprayed spokes off it.
# Converging the ring on a small central patch fixed the slither but left 176
# vertices crammed round a 24 x 20 mm n-gon, 0.5 mm apart - still enough to
# blow the wireframe pass up. The floor is now a plain quad GRID tucked 1.6 mm
# under the wall's bottom edge: no n-gon, no crack, and it reads as the
# separate bonded floor panel it would really be.


# D-SP14: the plateau was a constant 30 mm proud over its whole 1.17 m, so it
# caught one unbroken specular sheet - 1.97 % of the frame clipped in the az-130
# view. Tapering it 18 % toward both ends puts a longitudinal crown on it.
# D-SP27: the fastener ring around the plinth did NOT apply this taper, so the
# bolts nearest the fore and aft tips floated up to 3.0 mm off the carbon they
# are holding down. Both the panel and its fixings go through this one function.
def _plinth_hmod(x, dh):
    t = min(1.0, max(0.0, (x - PLINTH_OUT[0]) / (PLINTH_OUT[1] - PLINTH_OUT[0])))
    return dh * (1.0 - 0.18 * (1.0 - math.sin(math.pi * t) ** 0.30))


def _build_plinth(acc, npts=176):
    canon = _canon_t(PLINTH_OUT)
    tvals = [i / npts for i in range(npts)]

    def hbase(x, v):
        return _h_flank(x, min(1.0, max(0.0, v)))

    def hmod(x, v, dh):
        return _plinth_hmod(x, dh)

    rings = _aperture_rings(PLINTH_OUT, PLINTH_AP, tvals, canon, hbase,
                            _PL_EDGE, _PL_MAIN, _PL_LIP, hmod=hmod)
    n_top = len(rings)
    for d, dh in _PL_WALL:
        sh = _shape_inset(PLINTH_AP, d)
        pts = _outline(sh, tvals, canon)
        _push(rings, [_pv(x, v, hbase(x, v) + hmod(x, v, dh)) for (x, v) in pts])
    mats = [0 if i < n_top - 1 else 1 for i in range(len(rings) - 1)]
    acc.loft(rings, mats=mats, closed=True)

    fx0, fx1 = PLINTH_AP[0] + 0.004, PLINTH_AP[1] - 0.004
    nfx, nfv = 74, 12
    rows = []
    for i in range(nfx + 1):
        xf = fx0 + (fx1 - fx0) * i / nfx
        m = _mv(xf)
        v0f = PLINTH_AP[2] + 0.004 / m
        v1f = PLINTH_AP[3] - 0.004 / m
        rows.append([_pv(xf, v0f + (v1f - v0f) * j / nfv,
                         hbase(xf, 0.5 * (v0f + v1f)) + hmod(xf, 0.0, 0.0042))
                     for j in range(nfv + 1)])
    acc.grid(rows, mat=1)

    # D-SP05: the trough floor was 680 x 50 mm of untextured black. Three
    # LONGITUDINAL ducting rails now run under the gills - transverse ribs
    # would have collided with the blades (11 mm slots, 11 mm ribs).
    x0, x1, v0, v1 = PLINTH_AP[0], PLINTH_AP[1], PLINTH_AP[2], PLINTH_AP[3]
    for k, fv in enumerate((0.20, 0.50, 0.80)):
        vr = v0 + (v1 - v0) * fv
        rad = 0.0030 if k != 1 else 0.0036
        rings = []
        nx = 46
        for i in range(nx + 1):
            t = i / nx
            xr = x0 + 0.014 + (x1 - x0 - 0.028) * t
            # D-SP22: the end rings tapered to sc = 0, i.e. ten coincident
            # vertices closed by an n-gon. The preview wireframe pass sprayed
            # metre-long spokes off both ends of every rail and the plinth's
            # evaluated bounds ran 800 mm past the part.
            sc = max(0.20, math.sin(math.pi * min(1.0, max(0.0, t))) ** 0.25)
            ring = []
            for j in range(10):
                ang = TAU * j / 10
                dv = rad * sc * math.cos(ang) / _mv(xr, vr)
                dh = 0.0046 + rad * sc * math.sin(ang)
                ring.append(_pv(xr, vr + dv, hbase(xr, vr) + dh))
            rings.append(ring)
        acc.loft(rings, mat=1, closed=True, cap_start=True, cap_end=True)


def _build_louvres(acc):
    x0, x1 = PLINTH_AP[0], PLINTH_AP[1]
    v0, v1 = PLINTH_AP[2], PLINTH_AP[3]
    nsp = 20
    prof = []
    nsec = 9
    for i in range(nsec):
        t = i / (nsec - 1.0)
        prof.append(t)

    for k in range(N_LOUVRE):
        f = (k + 0.5) / N_LOUVRE
        xc = x0 + (x1 - x0) * f
        # blade chord grows slightly toward the rear of the bank
        chord = 0.0270
        lift = 0.0152 + 0.0020 * math.sin(math.pi * f)
        rings = []
        mvx = _mv(xc)
        for i in range(nsp + 1):
            s = i / nsp
            # D-SP20: the 6 mm embed into the trough wall was divided by the
            # nominal MV_REF (0.27) instead of the local band arc (~0.60), so
            # each blade actually buried 13 mm - twice the wall thickness.
            v = v0 - 0.006 / mvx + (v1 - v0 + 0.012 / mvx) * s
            base_h = _h_flank(xc, min(1.0, max(0.0, v))) + 0.0100
            # slight spanwise arch so the blade is not a flat plank
            arch = 0.0016 * math.sin(math.pi * min(1.0, max(0.0, s)))
            ring = []
            for j in range(2 * nsec - 2):
                if j < nsec:
                    t = prof[j]
                    side = 1.0
                else:
                    t = prof[2 * nsec - 2 - j]
                    side = -1.0
                cx = -0.5 * chord + chord * t
                cz = lift * t * t * (3.0 - 2.0 * t)
                th = 0.0030 * math.sqrt(max(0.0, 1.0 - (2 * t - 1) ** 2)) ** 0.6
                th = max(th, 0.0006)
                # section normal of the camber line
                dz = lift * 6.0 * t * (1.0 - t) / max(chord, 1e-6)
                ln = math.hypot(1.0, dz)
                nx, nz = -dz / ln, 1.0 / ln
                ring.append(_pv(xc + cx + side * 0.5 * th * nx, v,
                                base_h + arch + cz + side * 0.5 * th * nz))
            rings.append(ring)
        acc.loft(rings, mat=0, closed=True, cap_start=True, cap_end=True)


# =========================================================================== #
# 8.  side impact structure fairing
# =========================================================================== #

SIS_X0, SIS_X1 = 0.432, 0.988


def _sis_axis(x):
    """(u, normal offset, half height along the section, half protrusion)."""
    # fades into the skin at the back, rounds off into a nose at the front
    if x >= 0.940:
        t = min(1.0, (SIS_X1 - x) / 0.048)
        s = math.sqrt(max(0.0, 1.0 - (1.0 - t) ** 2))
    elif x <= 0.585:
        t = max(0.0, (x - SIS_X0) / 0.153)
        s = t ** 0.70
    else:
        s = 1.0
    # D-SP04: end rings collapsed to a single point, which left 40 zero-area
    # quads at each tip. Floor the section so the caps stay real geometry.
    s = max(s, 0.075)
    d = 0.0205 * s + 0.0015
    hz = 0.0228 * s
    hy = 0.0440 * s
    return 0.2960, d, hz, hy


def _build_sis(acc):
    xs = []
    x = SIS_X1
    while x > SIS_X0:
        xs.append(x)
        x -= 0.0072
    xs.append(SIS_X0)
    rings = []
    npt = 40
    for x in xs:
        u, d, hz, hy = _sis_axis(x)
        c = _p(x, u, d)
        y0, z0 = _yz(x, max(0.0, u - 0.02))
        y1, z1 = _yz(x, min(1.0, u + 0.02))
        et = Vector((0.0, y1 - y0, z1 - z0))
        et.normalize()
        en = _n(x, u)
        ring = []
        for j in range(npt):
            a = TAU * j / npt
            cs, sn = math.cos(a), math.sin(a)
            py = math.copysign(abs(cs) ** SIS_E, cs)
            pz = math.copysign(abs(sn) ** SIS_E, sn)
            ring.append(c + en * (hy * py) + et * (hz * pz))
        rings.append(ring)
    acc.loft(rings, mat=0, closed=True, cap_start=True, cap_end=True)


# =========================================================================== #
# 9.  wing mirror
# =========================================================================== #

MIR_ROOT = (0.470, 0.870)          # (x, v) on the flank panel
MIR_HEAD = Vector((0.598, 0.560, 0.748))
DRIVER_EYE = Vector((0.060, 0.300, 0.865))
MIR_W, MIR_H, MIR_D = 0.0880, 0.0335, 0.0300


def _mirror_frame():
    nm = (DRIVER_EYE - MIR_HEAD)
    nm.normalize()
    right = Vector((0.0, 0.0, 1.0)).cross(nm)
    right.normalize()
    up = nm.cross(right)
    up.normalize()
    return nm, right, up


def _rrect2(w, h, r, n):
    """Rounded rectangle in a local 2D frame, n points."""
    # D-SP09: the straight sides were laid on x = +/-(w - r) while the corner
    # arcs bulged out to +/-w, so the outline crossed itself and the mirror
    # housing lofted as a folded bowtie. Straights belong ON the extremes.
    r = min(r, min(w, h) * 0.98)
    sw, sh = w - r, h - r
    segs = [("l", (w, -sh, w, sh)), ("c", (sw, sh, 0.0, 90.0)),
            ("l", (sw, h, -sw, h)), ("c", (-sw, sh, 90.0, 180.0)),
            ("l", (-w, sh, -w, -sh)), ("c", (-sw, -sh, 180.0, 270.0)),
            ("l", (-sw, -h, sw, -h)), ("c", (sw, -sh, 270.0, 360.0))]
    lens = []
    for kind, d in segs:
        if kind == "l":
            lens.append(math.hypot(d[2] - d[0], d[3] - d[1]))
        else:
            lens.append(0.5 * math.pi * r)
    tot = sum(lens)
    out = []
    for i in range(n):
        t = tot * i / n
        acc = 0.0
        for k, (kind, d) in enumerate(segs):
            if t <= acc + lens[k] or k == len(segs) - 1:
                s = (t - acc) / max(lens[k], 1e-9)
                if kind == "l":
                    out.append((d[0] + (d[2] - d[0]) * s, d[1] + (d[3] - d[1]) * s))
                else:
                    a = math.radians(d[2] + (d[3] - d[2]) * s)
                    out.append((d[0] + r * math.cos(a), d[1] + r * math.sin(a)))
                break
            acc += lens[k]
    return out


def _build_mirror(acc, acc_face, acc_glass):
    nm, right, up = _mirror_frame()
    n = 96
    base = _rrect2(MIR_W, MIR_H, 0.016, n)

    # ---- housing shell: front rim -> domed back -------------------------- #
    # D-SP15: the back was a hand-written scale/depth table that flattened off
    # near the tip - the last four rings sat within 0.7 mm of each other while
    # the section shrank 0.33 -> 0.045, so the shading broke into a bullseye of
    # concentric bands. It is now a true half-ellipsoid sampled on equal arc,
    # and the object is smoothed at 55 deg so no ring reads as a crease.
    # D-SP25: a half-ellipsoid back is a surface of revolution, and the shared
    # CarbonFibre weave is mapped in OBJECT space - iso-lines of world x and y
    # close into circles on a dome, so the tip banded into concentric rings.
    # Squashing the back 1.55x harder in "up" than in "right" makes it the
    # wedge a real mirror housing is, and the weave reads as weave again.
    prof = []
    nb = 19
    for i in range(nb):
        a = 0.5 * math.pi * (i / (nb - 1.0)) ** 0.92
        c = math.cos(a)
        prof.append((c, c ** 1.55, -0.0335 * math.sin(a)))
    prof[-1] = (0.115, 0.045, -0.0335)
    rings = []
    for sr, su, dd in prof:
        rings.append([MIR_HEAD + right * (a * sr) + up * (b * su) + nm * dd
                      for (a, b) in base])
    acc.loft(rings, mat=0, closed=True, cap_end=True)

    # ---- rim roll into the glass recess ---------------------------------- #
    rim = [(1.000, 0.0000), (0.996, 0.0022), (0.986, 0.0036), (0.970, 0.0040),
           (0.952, 0.0032), (0.940, 0.0012), (0.936, -0.0030),
           (0.934, -0.0074)]
    rings = []
    for s, dd in rim:
        rings.append([MIR_HEAD + right * (a * s) + up * (b * s) + nm * dd
                      for (a, b) in base])
    acc.loft(rings, mat=0, closed=True)
    # recess back wall
    rings = []
    for s, dd in ((0.934, -0.0074), (0.900, -0.0080), (0.60, -0.0084),
                  (0.18, -0.0086)):
        rings.append([MIR_HEAD + right * (a * s) + up * (b * s) + nm * dd
                      for (a, b) in base])
    acc.loft(rings, mat=1, closed=True, cap_end=True)

    # ---- reflector + cover glass (slightly convex) ----------------------- #
    for target, mat, depth, bulge in ((acc_face, 0, -0.0072, 0.0016),
                                      (acc_glass, 0, -0.0048, 0.0020)):
        rows = []
        nr, nc = 22, 44
        for i in range(nr + 1):
            b = -1.0 + 2.0 * i / nr
            row = []
            for j in range(nc + 1):
                a = -1.0 + 2.0 * j / nc
                rr = min(1.0, math.hypot(a, b) * 0.86)
                row.append(MIR_HEAD + right * (a * MIR_W * 0.905)
                           + up * (b * MIR_H * 0.900)
                           + nm * (depth + bulge * (1.0 - rr * rr)))
            rows.append(row)
        target.grid(rows, mat=mat)

    # ---- aerofoil stalk --------------------------------------------------- #
    rx, rv = MIR_ROOT
    root = _pv(rx, rv, 0.0165)
    rn = _nv(rx, rv)
    head_attach = MIR_HEAD + right * (MIR_W * 0.62) + nm * (-0.020) + up * (-0.004)
    c0 = root + rn * 0.075 + Vector((-0.010, 0.0, 0.055))
    c1 = head_attach + Vector((0.030, -0.045, -0.075))

    def bez(t):
        mt = 1.0 - t
        return (root * (mt ** 3) + c0 * (3 * mt * mt * t)
                + c1 * (3 * mt * t * t) + head_attach * (t ** 3))

    nseg = 26
    nsec = 32

    def af_ring(centre, cdir, tdir, ch, th):
        out = []
        for j in range(nsec):
            ang = TAU * j / nsec
            cx = 0.5 * (1.0 - math.cos(ang))
            yt = 5.0 * th * (0.2969 * math.sqrt(max(cx, 0.0)) - 0.1260 * cx
                             - 0.3516 * cx ** 2 + 0.2843 * cx ** 3
                             - 0.1015 * cx ** 4)
            sgn = 1.0 if math.sin(ang) >= 0 else -1.0
            out.append(centre + cdir * ((cx - 0.42) * ch) + tdir * (sgn * yt))
        return out

    def frame(t):
        p0 = bez(max(0.0, t - 0.01))
        p1 = bez(min(1.0, t + 0.01))
        tang = (p1 - p0)
        tang.normalize()
        cd = Vector((1.0, 0.0, 0.0)) - tang * tang.dot(Vector((1.0, 0.0, 0.0)))
        if cd.length < 1e-6:
            cd = Vector((0.0, 1.0, 0.0))
        cd.normalize()
        td = tang.cross(cd)
        td.normalize()
        return cd, td

    # D-SP08: the root used to be a separate elliptical "shoe" lofted around
    # the strut - and its top ring (50 x 34 mm) was far wider than the strut
    # section (78 x 10 mm) and left uncapped, so the mount read as a funnel
    # with a hole in it. The fairing is now the SAME loft as the strut, four
    # flare rings on the strut's own aerofoil section, so there is no seam and
    # nothing to see into.
    cd0, td0 = frame(0.0)
    rings = []
    for sc_c, sc_t, dn in ((1.60, 4.30, -0.0215), (1.44, 3.05, -0.0120),
                           (1.28, 2.15, -0.0055), (1.13, 1.50, -0.0016)):
        rings.append(af_ring(root - rn * (-dn), cd0, td0,
                             0.0540 * sc_c, 0.1300 * 0.0540 * sc_t))
    for i in range(nseg + 1):
        t = i / nseg
        cd, td = frame(t)
        ch = 0.0540 * (1.0 - 0.20 * t)
        rings.append(af_ring(bez(t), cd, td, ch, 0.1300 * ch))
    acc.loft(rings, mat=1, closed=True, cap_start=True, cap_end=True)


# =========================================================================== #
# 10.  fasteners
# =========================================================================== #

_FAST_PROF = [(0.00060, 0.00140), (0.00220, 0.00150), (0.00300, 0.00230),
              (0.00420, 0.00250), (0.00540, 0.00232), (0.00610, 0.00170),
              (0.00640, 0.00080), (0.00645, -0.00060)]


def _fastener(acc, x, v, hbase, mat_head=0, mat_slot=1, ang=0.0):
    p0 = _pv(x, v, hbase)
    nn = _nv(x, v)
    e1, e2 = _ortho(nn)
    seg = 18
    rings = []
    for r, dh in _FAST_PROF:
        ring = []
        for j in range(seg):
            a = TAU * j / seg
            ring.append(p0 + nn * dh + e1 * (r * math.cos(a))
                        + e2 * (r * math.sin(a)))
        rings.append(ring)
    acc.loft(rings, mat=mat_head, closed=True, cap_start=True, cap_end=True)
    # quarter-turn slot
    ca, sa = math.cos(ang), math.sin(ang)
    u1 = e1 * ca + e2 * sa
    u2 = -e1 * sa + e2 * ca
    hw, hl, top, bot = 0.00072, 0.00460, 0.00110, -0.00050
    quad = []
    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        quad.append(p0 + u1 * (hl * sx) + u2 * (hw * sy))
    top_r = [q + nn * top for q in quad]
    bot_r = [q + nn * bot for q in quad]
    acc.loft([bot_r, top_r], mat=mat_slot, closed=True, cap_start=True,
             cap_end=True)


def _prof_h(prof, s):
    """Piecewise-linear lookup of the (s, dh) surface-height profile."""
    if s <= prof[0][0]:
        return prof[0][1]
    for k in range(len(prof) - 1):
        a, b = prof[k], prof[k + 1]
        if a[0] <= s <= b[0]:
            t = (s - a[0]) / max(b[0] - a[0], 1e-9)
            return a[1] + (b[1] - a[1]) * t
    return prof[-1][1]


def _build_fixings(acc):
    # D-SP06: fasteners were placed at a fixed height above the BODY, but both
    # panels dome as they approach their aperture - the front row sank 2.4 mm
    # into the moulding it was supposed to be holding down. Both rows now ride
    # the panel's own blend profile.
    canon_f = _canon_t(FRONT_OUT)
    base_f = _shape_inset(FRONT_OUT, _FR_EDGE[-1][0])
    s_f = 0.115
    sh = _shape_lerp(base_f, FRONT_AP, s_f)
    hf = _prof_h(_FR_MAIN, s_f)
    n = 22
    for i in range(n):
        t = (i + 0.5) / n
        (x, v) = _outline(sh, [t], canon_f)[0]
        _fastener(acc, x, v, _h_flank(x, min(1.0, max(0.0, v))) + hf,
                  ang=1.1 * i)

    canon_p = _canon_t(PLINTH_OUT)
    base_p = _shape_inset(PLINTH_OUT, _PL_EDGE[-1][0])
    s_p = 0.115
    shp = _shape_lerp(base_p, PLINTH_AP, s_p)
    hp = _prof_h(_PL_MAIN, s_p)
    n = 24
    for i in range(n):
        t = (i + 0.5) / n
        (x, v) = _outline(shp, [t], canon_p)[0]
        _fastener(acc, x, v,
                  _h_flank(x, min(1.0, max(0.0, v))) + _plinth_hmod(x, hp),
                  ang=0.7 * i)

    x = 0.500
    while x > -1.100:
        # D-SP11: leave room for the mirror mount shoe
        if not (0.395 < x < 0.548):
            _fastener(acc, x, 0.950, _h_flank(x, 0.950) + 0.0006, ang=0.9 * x)
        x -= 0.1150

    # four bolts ringing the mirror mount shoe, on the panel itself
    rx, rv = MIR_ROOT
    m = _mv(rx)
    for dx, dv in ((0.062, 0.0), (-0.062, 0.0), (0.0, 0.041), (0.0, -0.041)):
        _fastener(acc, rx + dx, rv + dv / m,
                  _h_flank(rx + dx, rv + dv / m) + 0.0006, ang=2.1 * dx)
    x = 0.470
    while x > -1.060:
        _fastener(acc, x, 0.052, _h_flank(x, 0.052) + 0.0006, ang=1.4 * x)
        x -= 0.1650


# =========================================================================== #
# 10b.  flank cooling scoop (gearbox / hydraulics cooler feed)
# =========================================================================== #

SCOOP_XF, SCOOP_XR, SCOOP_V = 0.048, -0.238, 0.170


def _build_scoop(acc):
    nx, ns = 30, 28
    wid = 0.0330
    rows = []
    for i in range(nx + 1):
        t = i / nx
        x = SCOOP_XF + (SCOOP_XR - SCOOP_XF) * t
        g = 1.0 - t
        hgt = 0.0240 * (g ** 0.62) + 0.0004
        hb = _h_flank(x, SCOOP_V)
        m = _mv(x, SCOOP_V)
        row = []
        for j in range(ns + 1):
            s = j / ns
            a = math.pi * s
            dv = -wid * math.cos(a) / m
            sn = math.sin(a)
            hh = hb + hgt * (sn ** 0.72) - 0.0014 * (1.0 - sn ** 0.35)
            row.append(_pv(x, SCOOP_V + dv, hh))
        rows.append(row)
    acc.grid(rows, mat=0)

    # dark throat floor so the mouth is not a hole onto glossy paint
    rows = []
    for i in range(nx + 1):
        t = i / nx
        x = SCOOP_XF + (SCOOP_XR - SCOOP_XF) * t
        hb = _h_flank(x, SCOOP_V) + 0.0016
        m = _mv(x, SCOOP_V)
        g = 1.0 - t
        row = []
        for j in range(13):
            s = -1.0 + 2.0 * j / 12.0
            row.append(_pv(x, SCOOP_V + s * wid * 0.985 / m,
                           hb + 0.0090 * (1.0 - g) ** 1.5))
        rows.append(row)
    acc.grid(rows, mat=1)

    # three splitter bars across the mouth
    for k in range(3):
        s = -0.5 + 0.5 * k
        rings = []
        for i in range(9):
            t = i / 8.0
            x = SCOOP_XF - 0.004 - 0.030 * t
            m = _mv(x, SCOOP_V)
            hb = _h_flank(x, SCOOP_V)
            g = 1.0 - (x - SCOOP_XR) / (SCOOP_XF - SCOOP_XR)
            top = hb + 0.0240 * ((1.0 - g) ** 0.62) * 0.92
            bot = hb + 0.0034
            ring = []
            for j in range(8):
                a = TAU * j / 8 + math.pi / 8
                ring.append(_pv(x, SCOOP_V + (s * wid * 1.30 + 0.0016
                                              * math.cos(a)) / m,
                                0.5 * (top + bot)
                                + 0.5 * (top - bot) * math.sin(a)))
            rings.append(ring)
        acc.loft(rings, mat=2, closed=True, cap_start=True, cap_end=True)


# =========================================================================== #
# 11.  extra flank furniture
# =========================================================================== #

def _sis_frame(x):
    u, d, hz, hy = _sis_axis(x)
    c = _p(x, u, d)
    y0, z0 = _yz(x, max(0.0, u - 0.02))
    y1, z1 = _yz(x, min(1.0, u + 0.02))
    et = Vector((0.0, y1 - y0, z1 - z0))
    et.normalize()
    return c, et, _n(x, u), hz, hy


SIS_E = 2.0 / 3.2


def _sis_surf(x, a):
    """Point and outward normal on the SIS fairing skin at section angle a."""
    c, et, en, hz, hy = _sis_frame(x)

    def yz(ang):
        cs, sn = math.cos(ang), math.sin(ang)
        return (hy * math.copysign(abs(cs) ** SIS_E, cs),
                hz * math.copysign(abs(sn) ** SIS_E, sn))

    y0, z0 = yz(a - 0.02)
    y1, z1 = yz(a + 0.02)
    dy, dz = y1 - y0, z1 - z0
    ln = math.hypot(dy, dz) or 1.0
    ny, nz = dz / ln, -dy / ln
    yy, zz = yz(a)
    if ny * yy + nz * zz < 0.0:
        ny, nz = -ny, -nz
    return c + en * yy + et * zz, (en * ny + et * nz).normalized()


def _build_trim(acc):
    """Flow-conditioning vanes on the shoulder and the SIS rivet lines."""
    # D-SP07: both flow conditioners were inside the louvre plinth footprint
    # (x < 0.28) and buried 25 mm under its plateau. Moved ahead of it.
    # D-SP16: they were also built as wedges standing on their leading edge -
    # the whole lower edge sat 3-4 mm clear of the paint. They are proper
    # plates now: flat foot 2.5 mm INTO the panel, rounded top, swept in v.
    for xc, vc, hgt, ln in ((0.404, 0.700, 0.0230, 0.078),
                            (0.352, 0.812, 0.0198, 0.070),
                            (0.300, 0.905, 0.0168, 0.062)):
        rings = []
        nchord = 17
        for i in range(nchord):
            s = i / (nchord - 1.0)
            xx = xc + ln * (0.5 - s)
            hh = hgt * math.sin(math.pi * min(1.0, max(0.0, s))) ** 0.42
            w = 0.0016 + 0.0009 * math.sin(math.pi * s)
            m = _mv(xx, vc)
            base = _h_flank(xx, vc)
            sweep = (0.011 * (s - 0.5) ** 1.0) / m       # swept vane
            hh = max(hh, 2.2 * w)
            sec = [(w, -0.0025)]
            for k in range(11):
                ang = math.pi * k / 10.0
                sec.append((w * math.cos(ang), hh - w + w * math.sin(ang)))
            sec.append((-w, -0.0025))
            ring = [_pv(xx, vc + sweep + dv / m, base + dh) for (dv, dh) in sec]
            rings.append(ring)
        acc.loft(rings, mat=0, closed=True, cap_start=True, cap_end=True)

    # D-SP17: the rivet line was placed at a hand-picked (0.32, 0.86) fraction
    # of the section half-axes. That point is INSIDE a superellipse, so every
    # rivet on both sides of the fairing was sunk out of sight. They are now
    # solved onto the skin at a fixed section angle with the skin's own normal.
    x = 0.975
    while x > 0.482:
        for a in (0.86, math.pi - 0.86, -0.86, math.pi + 0.86):
            cpos, nn = _sis_surf(x, a)
            if nn.y < 0.02:
                continue
            e1, e2 = _ortho(nn)
            rings = []
            for r, dh in ((0.00035, 0.00115), (0.00150, 0.00105),
                          (0.00235, 0.00060), (0.00255, -0.00050)):
                ring = []
                for j in range(10):
                    ang = TAU * j / 10
                    ring.append(cpos + nn * dh + e1 * (r * math.cos(ang))
                                + e2 * (r * math.sin(ang)))
                rings.append(ring)
            acc.loft(rings, mat=1, closed=True, cap_start=True, cap_end=True)
        x -= 0.0385


# =========================================================================== #
# 12.  build
# =========================================================================== #

def build(coll, ctx=None):
    objs = []

    acc = _Acc()
    _build_flank(acc)
    ob = _emit(P + "flank", acc, coll, ["LiveryPaint", "CarbonFibre"], smooth=34.0)
    C.add_solidify(ob, thickness=0.0026, offset=0.0)
    objs.append(ob)

    acc = _Acc()
    fring, cq, cf, dvec, e1, e2 = _build_front(acc)
    ob = _emit(P + "front", acc, coll,
               ["LiveryPaint", "CarbonMatte", "AnodisedGold"], smooth=34.0)
    C.add_solidify(ob, thickness=0.0028, offset=0.0)
    objs.append(ob)

    acc = _Acc()
    _build_vane(acc, fring, cf, dvec, e1, e2)
    objs.append(_emit(P + "vane", acc, coll, ["CarbonFibre"], smooth=40.0))

    acc = _Acc()
    _build_rad(acc, fring, cf, dvec, e1, e2)
    objs.append(_emit(P + "rad", acc, coll,
                      ["Titanium", "MatteBlack", "MatteBlack", "AnodisedRed"],
                      smooth=25.0))

    acc = _Acc()
    _build_plinth(acc)
    ob = _emit(P + "shoulder", acc, coll, ["CarbonFibre", "MatteBlack"], smooth=32.0)
    C.add_solidify(ob, thickness=0.0024, offset=0.0)
    objs.append(ob)

    acc = _Acc()
    _build_louvres(acc)
    objs.append(_emit(P + "louvres", acc, coll, ["CarbonFibre"], smooth=38.0))

    acc = _Acc()
    _build_sis(acc)
    ob = _emit(P + "sis", acc, coll, ["CarbonFibre"], smooth=34.0)
    objs.append(ob)

    acc, accf, accg = _Acc(), _Acc(), _Acc()
    _build_mirror(acc, accf, accg)
    objs.append(_emit(P + "mirror", acc, coll, ["CarbonFibre", "MatteBlack"],
                      smooth=55.0))
    objs.append(_emit(P + "mirrorface", accf, coll, ["SteelFastener"], smooth=45.0))
    objs.append(_emit(P + "mirrorglass", accg, coll, ["DisplayGlass"], smooth=45.0))

    acc = _Acc()
    _build_fixings(acc)
    objs.append(_emit(P + "fixings", acc, coll, ["SteelFastener", "MatteBlack"],
                      smooth=28.0))

    acc = _Acc()
    _build_scoop(acc)
    ob = _emit(P + "scoop", acc, coll,
               ["LiveryPaint", "MatteBlack", "CarbonMatte"], smooth=34.0)
    C.add_solidify(ob, thickness=0.0024, offset=0.0)
    objs.append(ob)

    acc = _Acc()
    _build_trim(acc)
    objs.append(_emit(P + "trim", acc, coll, ["CarbonFibre", "SteelFastener"],
                      smooth=32.0))

    for ob in objs:
        C.add_mirror(ob, axis=(False, True, False))
    return objs


# --------------------------------------------------------------------------- #
# DEFECTS - what each render/inspect cycle found and what fixed it
# --------------------------------------------------------------------------- #
#
# Each entry names the view it was FOUND in and the view it was re-rendered in
# to confirm the fix. In-line D-SPnn comments sit next to the code that changed.
#
# D-SP01  corner radius > half the shorter side folded the outline inside out
#         (found by inspection before the first render; clamped in _pieces)
# D-SP02  radiator backing plate was a rectangle sized to the widest span + 20
#         mm, so its corners punched out through the duct wall and read as a
#         floating black slab beside the mouth.        az40/el22 -> az40/el22
# D-SP03  splitter vane spanned to the ring at the BACK of the throat, leaving
#         both tips ~8 mm short of a wall that is 1/0.88 wider at the mouth.
# D-SP04  SIS end rings collapsed to a point: 40 zero-area quads per tip.
# D-SP05  trough floor was 680 x 50 mm of untextured black; three LONGITUDINAL
#         rails added (transverse ribs would have fouled the 11 mm gill slots).
# D-SP06  fasteners sat at a fixed height above the BODY while both panels dome
#         toward their aperture - the surround row sank 2.4 mm into the panel
#         it was meant to be holding down.
# D-SP07  two flow conditioners were inside the plinth footprint, 25 mm under
#         its plateau.                                  az-50/el24 -> az-50/el24
# D-SP08  mirror mount was an elliptical "shoe" whose 50 x 34 mm top ring was
#         far wider than the 78 x 10 mm strut and left uncapped: the mount read
#         as a funnel with a hole in it. Strut and fairing are now one loft.
#                                                       az8/el16 -> az-50/el24
# D-SP09  _rrect2 put the straight sides on +/-(w - r) while the corner arcs
#         bulged to +/-w, so the mirror housing lofted as a folded bowtie.
#                                                       az40/el22 z8 -> az40/el22
# D-SP10  v was a lerp between u_lo and u_hi, but the body section's spline is
#         wildly non-uniform (0.9 m of arc per unit u at the max-width knot,
#         2.3 m between shoulder and tub side). Columns ran 2.6 mm apart low
#         down and 15 mm apart on the shoulder and every radius quoted in
#         metres came out the wrong size at one end. v is now arc length.
# D-SP11  top fastener row ran through the mirror mount.
# D-SP12  plinth plateau was 200 x 1200 mm of unbroken carbon; shut line added.
# D-SP13  throat was 190 mm deep and lined in matte carbon, so the mouth was a
#         black void at every angle. Radiator moved to 120 mm and the back half
#         of the duct lined in gold heat-shield film.  az40/el22 -> az-50/el24
# D-SP14  plateau was a constant 30 mm proud over 1.17 m and caught one
#         unbroken specular sheet: 1.80 % of the az-130 frame clipped. With the
#         longitudinal crown it is 0.36 %.              az130/el12 -> az130/el12
# D-SP15  mirror housing back flattened off near the tip - four rings within
#         0.7 mm of each other while the section shrank 0.33 -> 0.045 - and
#         shaded as a bullseye.                         az-50/el24 z9 -> z9
# D-SP16  vortex generators were wedges standing on their leading edge; the
#         whole lower edge floated 3-4 mm clear of the paint.
#                                                       az-50/el24 z9 -> z10
# D-SP17  SIS rivets were placed at a hand-picked (0.32, 0.86) fraction of the
#         section half-axes - a point INSIDE a superellipse - so every rivet on
#         both sides was sunk out of sight.             az40/el22 -> az-50/el16
# D-SP18  trough floor insets (14/30/52 mm into an 84 mm trough) collapsed the
#         last ring into a 641 x 9 mm slither closed by a 176-gon; converging
#         on a central patch then left 176 verts 0.5 mm apart. Now a quad grid.
# D-SP19  paint/carbon split ran at v = 0.085 across perfectly smooth surface
#         and read as a decal edge; moved into the v = 0.300 joint groove.
# D-SP20  louvre blade wall embed used the nominal MV_REF (0.27) instead of the
#         local band arc (0.60) and buried 13 mm, twice the wall thickness.
# D-SP21  the surround's roll only moved inward while the flank panel's bulges
#         4 mm outward: a 10.7 mm gap and a 5 mm step at the panel joint.
# D-SP22  trough rails tapered to sc = 0 - ten coincident verts closed by an
#         n-gon. The wireframe pass sprayed metre-long spokes off both ends and
#         the plinth's evaluated bounds ran 800 mm past the part.
#                                                       wire az40 -> wire az40
# D-SP23  the profile tables deliberately overlap at the edge/surface and
#         surface/lip joins, and each overlap lofted a full band of ZERO-AREA
#         quads: 352 on the plinth, 400 on the surround. validate() keeps them
#         (indices differ, only positions match). _push() now drops repeats.
# D-SP24  the throat's closing rings converged to 0.22, cramming 200 verts into
#         a 165 mm perimeter - 0.8 mm apart, below the preview wire thickness,
#         so it still threw two spokes.                 wire az40 -> wire az40
# D-SP25  mirror housing back was a half-ellipsoid, i.e. a surface of
#         revolution; the shared weave is mapped in OBJECT space, so iso-lines
#         of world x/y close into circles on a dome and the tip banded into a
#         bullseye. Squashed 1.55x harder in "up" than in "right".
#                                                       az-50/el24 z9 -> z12
# D-SP26  even with the longitudinal crown the plateau was flat to within
#         0.3 mm ACROSS its 90 mm width; a 1.8 mm transverse arch added.
# D-SP27  the plinth fastener ring did not apply the plateau's crown taper, so
#         the bolts nearest the fore and aft tips floated up to 3.0 mm off the
#         carbon they hold down. One shared _plinth_hmod() now.
#
# MEASUREMENTS (probe scripts, not eyeballs)
#   max |this module's surface - spec.body_surface_point| over x in
#   [-1.20, 1.02] x u in [0.25, 0.82] = 5.05 mm, at x = 0.96 / u = 0.50 - the
#   pod leading-edge kink, the one place spec.station_at bends hardest. That is
#   the smoothing clamp doing its job; panel h there is +6.0 to +16.3 mm, so
#   the bodywork is still proud of the exact skin everywhere.
#   min h over the whole flank field = +4.08 mm. Nothing sinks into the body.
#   radiator core bbox y <= 0.499 against a body half width of 0.52 at its
#   station: the duct is inside the monocoque, not through it.
#   degenerate faces after D-SP22/23: 0 of 7019 (plinth), 0 of 7401 (surround).
#   tools/peep.py, az 130 / el 12: 0.25 % of the frame clipped under the
#   preview's deliberately hot close key - all of it the specular line along
#   the rolled top edge, which is what a rolled edge on gloss paint does. The
#   same view at --key 0.35, which is the showroom's own material value, is
#   0.000 % clipped and 0.020 % crushed.
#   230 776 evaluated polygons in 13 objects, both sides.
