"""FROZEN round-1 copy of barge_boards, kept only so the before/after
renders of the round-2 defect list use identical cameras.  Not developed.
"""
"""barge_boards - the turning-vane / deflector cluster between the front wheels
and the sidepod inlets, both sides.

Contents (left side authored, mirrored in-mesh)
-----------------------------------------------
    BB_Footplate    the bargeboard footplate: a rolled carbon shelf that hugs
                    the floor 6 mm clear of it, with an upturned outer lip and
                    a serrated ("shark tooth") outer edge over its rear third.
    BB_Deflector    the main vertical deflector, x = 1.470 -> 0.870.  A moulded
                    4.8 mm panel that leans outboard, carries a soft chine at
                    45 % height and rolls its top edge outboard through up to
                    96 deg on a 36 mm radius - the curl.  Three vertical
                    stiffening beads and one recessed two-piece moulding joint
                    are moulded into the surface, and three delta vortex
                    strakes stand on the outboard face under the curl.
    BB_Slat         the forward slat: a second, shorter vertical element ahead
                    of and inboard of the deflector leading edge, standing on
                    the same footplate, with a ~30 mm leading-edge slot gap.
    BB_Vanes        5 horizontal turning vanes of decreasing chord (375 -> 201
                    mm) stacked over 190 mm of height.  Each is a cambered
                    5 mm plate with a moulded 30 %-chord stiffener rib and a
                    serrated trailing edge, swept forward and drooping
                    outboard, rooted on the chassis flank and bonded into the
                    deflector's inboard face at the tip.  The staggered leading
                    edges leave four 43-52 mm slot gaps.  Each vane carries a
                    17 mm chordwise flow fence at a staggered span station.
    BB_RootStrips   the 5 chassis mounting strips the vane roots grow out of -
                    curved carbon strips lying on the monocoque flank.
    BB_UnderVanes   the under-chassis turning vanes: a belly pad bonded to the
                    tub underside ahead of the floor leading edge, with 3
                    S-section fins hanging below it.
    BB_Struts       2 titanium tie struts, chassis flank -> deflector, each on
                    twin-lug clevises with spherical rod ends.
    BB_Fasteners    50 socket-head fasteners with real hexagonal sockets, and
                    8 hex nuts.
    BB_Rivets       312 flush rivet domes.
    BB_Spacers      anodised spacer collars under the footplate fasteners and
                    the rod-end bearing balls.

Landing on the neighbours
-------------------------
Nothing here is guessed.  `_FTOP` is the floor's top surface measured by
raycasting `parts/floor_diffuser` on a 50 mm grid over x = 0.60 .. 1.55,
y = 0.20 .. 0.85; it is read back with a Catmull-Rom bicubic so the footplate
underside is C1 and does not crease.  The monocoque flank and belly come from
`spec.BODY_STATIONS` through the same Catmull-Rom that `spec.body_surface_point`
samples, but at 481 points instead of 65, so the mounting strips do not
stair-step.  Measured agreement with parts/monocoque_b over the flank band
z = 0.10 .. 0.45, x = 0.90 .. 1.55 is 0.7 - 4.4 mm (worst at z ~ 0.35, where that
module's shoulder sits outboard of the contract), so every part that touches
the body is held 2.1 - 7.4 mm proud of the reference skin: it lands ON the car,
it never grows out of the inside of it.

Brackets are placed on the real TANGENT PLANE of whatever they land on
(`_surf_frame`), not on a (0, ny, nz) frame - the deflector's leading edge
sweeps at dY/dx = -0.60, so a 36 mm bracket on a naive frame punches straight
through the 4.8 mm panel.

Measured bounds, both sides, 268 k evaluated polygons in 10 objects:
    x  0.870 .. 1.730     y  |0.060| .. 0.753     z  0.060 .. 0.507

Clearances, all MEASURED over every vertex of the finished mesh, not asserted:
    nearest approach to the floor's outer rim, in plan:  +10.4 mm (the curled
                             top edge at x = 1.335, 0.37 m above the floor)
    nearest approach to the floor's top surface:  the six footplate bolt shanks
                             enter the laminate by up to 1.5 mm - they are
                             bolts into floor inserts.  Nothing else on the
                             part comes within 6 mm of the floor.
    footplate underside      6.0 mm above the measured floor top, everywhere
    lowest vane surface      >= 41 mm above the footplate
    under-chassis fins       z >= 0.060, above the floor underside (0.050) and
                             the plank (0.040); tops <= 0.144, clear of
                             suspension_front (min z 0.135 at y > 0.05)
    forward slat             x <= 1.505, clear of suspension_front (min x 1.526)
    deflector trailing edge  x >= 0.870, 88 mm ahead of the sidepod (x 0.958)
    rear tie strut           chassis boss at x = 1.000, clear of the sidepod
                             inlet surround (which reaches x = 0.965)

Coordinate contract: +X forward, +Y car left, +Z up, tyre contact z = 0.
"""

import math

import bpy
from mathutils import Vector

import common as C
import spec as S

NAME = "_bb_before"
P = "BB_"

TAU = math.pi * 2.0


# =========================================================================== #
# 0.  small maths helpers (spec.py / common.py are frozen, so these live here)
# =========================================================================== #

def _pchip(ctrl):
    """Monotone cubic Hermite through control points - no spline overshoot."""
    pts = sorted(ctrl)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    n = len(xs)
    h = [xs[i + 1] - xs[i] for i in range(n - 1)]
    d = [(ys[i + 1] - ys[i]) / h[i] for i in range(n - 1)]
    m = [0.0] * n
    m[0], m[-1] = d[0], d[-1]
    for i in range(1, n - 1):
        if d[i - 1] * d[i] <= 0.0:
            m[i] = 0.0
        else:
            w1 = 2.0 * h[i] + h[i - 1]
            w2 = h[i] + 2.0 * h[i - 1]
            m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])

    def f(x):
        if x <= xs[0]:
            return ys[0]
        if x >= xs[-1]:
            return ys[-1]
        lo, hi = 0, n - 1
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if xs[mid] <= x:
                lo = mid
            else:
                hi = mid
        hh = h[lo]
        t = (x - xs[lo]) / hh
        t2, t3 = t * t, t * t * t
        return (ys[lo] * (2 * t3 - 3 * t2 + 1) + hh * m[lo] * (t3 - 2 * t2 + t)
                + ys[hi] * (-2 * t3 + 3 * t2) + hh * m[hi] * (t3 - t2))
    return f


def _ss(t):
    return C.smoothstep(t)


def _cr1(p0, p1, p2, p3, t):
    t2, t3 = t * t, t * t * t
    return 0.5 * ((2.0 * p1) + (-p0 + p2) * t
                  + (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * t2
                  + (-p0 + 3.0 * p1 - 3.0 * p2 + p3) * t3)


def _norms2(path):
    """Right-hand unit normals for an open 2D polyline."""
    n = len(path)
    out = []
    for i in range(n):
        if i == 0:
            tx = path[1][0] - path[0][0]
            ty = path[1][1] - path[0][1]
        elif i == n - 1:
            tx = path[-1][0] - path[-2][0]
            ty = path[-1][1] - path[-2][1]
        else:
            tx = path[i + 1][0] - path[i - 1][0]
            ty = path[i + 1][1] - path[i - 1][1]
        L = math.hypot(tx, ty) or 1.0
        out.append((ty / L, -tx / L))
    return out


def _plate_loop(path, ht, nc=6):
    """Closed section loop for a plate of half-thickness `ht` whose mid-surface
    is the open 2D polyline `path`, with semicircular rolled ends.

    ht may be 0 - the loop then collapses onto `path`, which is exactly what is
    wanted for the last station of a rolled leading edge: after a
    remove-doubles the surface closes over itself with no cap facet at all.
    """
    nrm = _norms2(path)
    n = len(path)
    a = [(path[i][0] + nrm[i][0] * ht, path[i][1] + nrm[i][1] * ht)
         for i in range(n)]
    b = [(path[i][0] - nrm[i][0] * ht, path[i][1] - nrm[i][1] * ht)
         for i in range(n)]

    tx = path[-1][0] - path[-2][0]
    ty = path[-1][1] - path[-2][1]
    L = math.hypot(tx, ty) or 1.0
    tx, ty = tx / L, ty / L
    nx, ny = nrm[-1]
    cap_e = []
    for k in range(1, nc):
        ang = math.pi * k / nc
        ca, sa = math.cos(ang), math.sin(ang)
        cap_e.append((path[-1][0] + ht * (ca * nx + sa * tx),
                      path[-1][1] + ht * (ca * ny + sa * ty)))

    tx = path[1][0] - path[0][0]
    ty = path[1][1] - path[0][1]
    L = math.hypot(tx, ty) or 1.0
    tx, ty = tx / L, ty / L
    nx, ny = nrm[0]
    cap_s = []
    for k in range(1, nc):
        ang = math.pi * k / nc
        ca, sa = math.cos(ang), math.sin(ang)
        cap_s.append((path[0][0] - ht * (ca * nx + sa * tx),
                      path[0][1] - ht * (ca * ny + sa * ty)))

    return a + cap_e + b[::-1] + cap_s


def _roll_stations(x_hi, x_lo, n_core, roll, nr=6):
    """(x, thickness_scale) stations for a panel lofted along x whose two ends
    roll shut over radius `roll`."""
    st = []
    for k in range(nr + 1):
        ph = (math.pi * 0.5) * (k / nr)
        st.append((x_hi - roll * (1.0 - math.cos(ph)), math.sin(ph)))
    xa, xb = x_hi - roll, x_lo + roll
    for i in range(1, n_core + 1):
        st.append((xa + (xb - xa) * (i / n_core), 1.0))
    for k in range(nr - 1, -1, -1):
        ph = (math.pi * 0.5) * (k / nr)
        st.append((x_lo + roll * (1.0 - math.cos(ph)), math.sin(ph)))
    return st


class _Acc:
    """Vertex/face accumulator - one emitted object per material group."""

    def __init__(self):
        self.v = []
        self.f = []

    def add(self, verts, faces):
        o = len(self.v)
        self.v.extend((float(p[0]), float(p[1]), float(p[2])) for p in verts)
        self.f.extend(tuple(i + o for i in fc) for fc in faces)

    def loft(self, rings, closed=True, cap_start=True, cap_end=True):
        v, f = C.loft(rings, closed=closed, cap_start=cap_start,
                      cap_end=cap_end)
        self.add(v, f)

    def mirror(self):
        """Mirror everything accumulated so far about the y = 0 plane."""
        nv, nf = len(self.v), len(self.f)
        self.v.extend((x, -y, z) for (x, y, z) in self.v[:nv])
        self.f.extend(tuple(i + nv for i in reversed(fc)) for fc in self.f[:nf])

    def emit(self, name, coll, mat, auto=38.0, merge=1.0e-5):
        ob = C.new_obj(name, self.v, self.f, coll=coll, smooth=True)
        if merge:
            C.merge_doubles(ob, merge)
        if auto is not None:
            C.shade_auto_smooth(ob, auto)
        S.assign(ob, mat)
        return ob


def _frame(n, spin=0.0):
    n = Vector(n).normalized()
    ref = Vector((0.0, 0.0, 1.0))
    if abs(n.dot(ref)) > 0.92:
        ref = Vector((1.0, 0.0, 0.0))
    t = (ref - n * ref.dot(n)).normalized()
    b = n.cross(t)
    if spin:
        cs, sn = math.cos(spin), math.sin(spin)
        t, b = t * cs + b * sn, b * cs - t * sn
    return t, b


def _hex_r(r, ang):
    """Radius of a regular hexagon of inscribed radius r at polar angle ang."""
    a = (ang + math.pi / 6.0) % (math.pi / 3.0) - math.pi / 6.0
    return r / math.cos(a)


def _revolve_solid(acc, profile, p, n, seg=24, spin=0.0):
    """profile: [(radius, height_along_n, is_hex)] - closed solid of revolution
    about the axis through p along n."""
    t, b = _frame(n, spin)
    p = Vector(p)
    nv = Vector(n).normalized()
    rings = []
    for entry in profile:
        r, h = entry[0], entry[1]
        hexf = entry[2] if len(entry) > 2 else False
        base = p + nv * h
        ring = []
        for i in range(seg):
            a = TAU * i / seg
            rr = _hex_r(r, a) if hexf else r
            ring.append(tuple(base + t * (rr * math.cos(a))
                              + b * (rr * math.sin(a))))
        rings.append(ring)
    acc.loft(rings, closed=True, cap_start=False, cap_end=False)


def _tube(acc, p0, p1, rprof, seg=20, cap=True):
    """Tapered tube from p0 to p1. rprof: [(t, r)] with t in 0..1."""
    p0, p1 = Vector(p0), Vector(p1)
    axis = p1 - p0
    t, b = _frame(axis, 0.0)
    rings = []
    for (s, r) in rprof:
        c = p0 + axis * s
        rings.append([tuple(c + t * (r * math.cos(TAU * i / seg))
                            + b * (r * math.sin(TAU * i / seg)))
                      for i in range(seg)])
    acc.loft(rings, closed=True, cap_start=cap, cap_end=cap)


# --------------------------------------------------------------------------- #
# fasteners
# --------------------------------------------------------------------------- #

def _bolt(acc, p, n, rh=0.0046, spin=0.0, seg=24, shank=0.011):
    """Flush socket-head fastener with a real hexagonal socket.

    Head top sits 0.6 mm proud, the countersink cone runs 4 mm down to the
    shank, and the 2.4 mm hex socket is 2.8 mm deep with a chamfered mouth.
    """
    rs = rh * 0.44
    prof = [
        (0.0, -shank),
        (rh * 0.52, -shank),
        (rh * 0.52, -shank + 0.0008),
        (rh * 0.55, -0.0040),
        (rh, 0.0006),
        (rh - 0.00035, 0.00095),
        (rs + 0.00055, 0.00095),
        (rs, 0.00055, True),
        (rs, -0.0022, True),
        (rs - 0.0006, -0.0026, True),
        (0.0, -0.0026),
    ]
    _revolve_solid(acc, prof, p, n, seg=seg, spin=spin)


def _prism(acc, poly, origin, e, u, v, thick, cham=0.0006):
    """Closed 2D polygon `poly` (in the u/v plane) extruded along `e` with both
    faces chamfered, so no edge of the lug is left dead sharp."""
    cu = sum(p[0] for p in poly) / len(poly)
    cv = sum(p[1] for p in poly) / len(poly)
    h = thick * 0.5
    k = 1.0 - cham / max(0.004, thick)
    rings = []
    for (off, sc) in ((-h, k), (-h + cham, 1.0), (h - cham, 1.0), (h, k)):
        ring = []
        for (pu, pv) in poly:
            uu = cu + (pu - cu) * sc
            vv = cv + (pv - cv) * sc
            ring.append(tuple(Vector(origin) + e * off + u * uu + v * vv))
        rings.append(ring)
    acc.loft(rings, closed=True, cap_start=True, cap_end=True)


def _rivet(acc, p, n, r=0.0026, seg=14):
    prof = [(0.0, -0.0024), (r * 0.8, -0.0024), (r, -0.0006),
            (r, 0.00015), (r * 0.86, 0.00055), (r * 0.55, 0.00085),
            (0.0, 0.00095)]
    _revolve_solid(acc, prof, p, n, seg=seg)


# =========================================================================== #
# 1.  the neighbours: measured floor top, monocoque flank and belly
# =========================================================================== #

# Floor top surface, raycast from parts/floor_diffuser on 2026-07-25.
# rows = x (descending), cols = y.  None where the floor is not there.
_FT_X = [1.55, 1.50, 1.45, 1.40, 1.35, 1.30, 1.25, 1.20, 1.15, 1.10,
         1.05, 1.00, 0.95, 0.90, 0.85, 0.80, 0.75, 0.70, 0.65, 0.60]
_FT_Y = [0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65,
         0.70, 0.75, 0.80, 0.85]
_FT_RAW = [
    [.0909, .1376, .1616, .1552, .1294, .0936, .0662, None, None, None, None, None, None, None],
    [.0905, .1329, .1615, .1626, .1461, .1165, .0852, .0697, None, None, None, None, None, None],
    [.0852, .1217, .1512, .1600, .1522, .1315, .1034, .0782, None, None, None, None, None, None],
    [.0808, .1119, .1401, .1548, .1533, .1407, .1189, .0936, .0737, None, None, None, None, None],
    [.0773, .1039, .1299, .1474, .1509, .1447, .1294, .1080, .0859, .0708, None, None, None, None],
    [.0747, .0976, .1211, .1393, .1470, .1450, .1353, .1187, .0985, .0797, .0690, None, None, None],
    [.0727, .0927, .1139, .1318, .1419, .1431, .1375, .1254, .1084, .0899, .0746, .0679, None, None],
    [.0712, .0889, .1080, .1252, .1366, .1400, .1374, .1287, .1150, .0983, .0820, .0706, None, None],
    [.0701, .0861, .1037, .1200, .1319, .1370, .1360, .1299, .1187, .1040, .0882, .0748, .0682, None],
    [.0694, .0841, .1005, .1161, .1281, .1341, .1344, .1299, .1206, .1074, .0924, .0785, .0694, None],
    [.0688, .0826, .0981, .1131, .1249, .1315, .1326, .1293, .1213, .1093, .0951, .0812, .0709, None],
    [.0684, .0817, .0966, .1111, .1228, .1295, .1311, .1284, .1211, .1098, .0961, .0823, .0717, .0651],
    [.0682, .0810, .0954, .1096, .1211, .1279, .1298, .1274, .1205, .1096, .0962, .0826, .0719, .0667],
    [.0680, .0805, .0946, .1084, .1198, .1266, .1287, .1265, .1199, .1092, .0960, .0826, .0719, .0669],
    [.0679, .0802, .0941, .1078, .1191, .1260, .1282, .1263, .1198, .1093, .0961, .0826, .0719, .0669],
    [.0679, .0801, .0940, .1077, .1191, .1261, .1285, .1267, .1203, .1098, .0965, .0829, .0720, .0670],
    [.0679, .0802, .0942, .1080, .1196, .1267, .1293, .1277, .1213, .1106, .0971, .0832, .0721, .0670],
    [.0679, .0804, .0945, .1086, .1203, .1277, .1305, .1289, .1225, .1117, .0979, .0836, .0722, .0670],
    [.0680, .0807, .0950, .1093, .1213, .1289, .1318, .1303, .1239, .1128, .0987, .0840, .0723, .0669],
    [.0681, .0809, .0955, .1100, .1222, .1300, .1331, .1316, .1252, .1139, .0994, .0844, .0724, .0669],
]


def _fill_grid():
    """Ascending-x grid with the off-floor cells continued at the rim height so
    the bicubic never sees a hole."""
    g = []
    for row in reversed(_FT_RAW):
        r = []
        last = 0.0690
        for v in row:
            if v is None:
                r.append(last)
            else:
                r.append(v)
                last = v
        g.append(r)
    return g


_FT = _fill_grid()
_FT_XA = list(reversed(_FT_X))


def _ftop(x, y):
    """Floor top surface z, Catmull-Rom bicubic over the measured grid."""
    xs, ys, g = _FT_XA, _FT_Y, _FT
    nx, ny = len(xs), len(ys)
    if x <= xs[0]:
        i, u = 0, 0.0
    elif x >= xs[-1]:
        i, u = nx - 2, 1.0
    else:
        i = int((x - xs[0]) / 0.05)
        i = max(0, min(nx - 2, i))
        u = (x - xs[i]) / (xs[i + 1] - xs[i])
    if y <= ys[0]:
        j, w = 0, 0.0
    elif y >= ys[-1]:
        j, w = ny - 2, 1.0
    else:
        j = int((y - ys[0]) / 0.05)
        j = max(0, min(ny - 2, j))
        w = (y - ys[j]) / (ys[j + 1] - ys[j])

    def gv(a, b):
        return g[max(0, min(nx - 1, a))][max(0, min(ny - 1, b))]

    col = []
    for k in range(-1, 3):
        col.append(_cr1(gv(i + k, j - 1), gv(i + k, j),
                        gv(i + k, j + 1), gv(i + k, j + 2), w))
    return _cr1(col[0], col[1], col[2], col[3], u)


_PROF_CACHE = {}


def _prof(x):
    """481-point half section at station x - the same Catmull-Rom that
    spec.body_surface_point samples, densified so it does not stair-step."""
    key = round(x * 2000.0)
    p = _PROF_CACHE.get(key)
    if p is None:
        half = S.station_half(S.station_at(key / 2000.0))
        p = C.catmull_rom(half, 481)
        _PROF_CACHE[key] = p
    return p


def _flank(x, z):
    """(y, ny, nz) on the monocoque flank at station x, height z.

    The flank branch (profile index 62 .. 380) is monotone in z at every station
    in this module's x window, so the inversion is a plain bracket search.
    """
    pts = _prof(x)
    lo, hi = 62, 380
    if z <= pts[lo][1]:
        i = lo
        t = 0.0
    elif z >= pts[hi][1]:
        i = hi - 1
        t = 1.0
    else:
        i = lo
        for k in range(lo, hi):
            if pts[k][1] <= z <= pts[k + 1][1]:
                i = k
                break
        dz = pts[i + 1][1] - pts[i][1]
        t = (z - pts[i][1]) / dz if dz > 1e-9 else 0.0
    y = pts[i][0] + (pts[i + 1][0] - pts[i][0]) * t
    a = pts[max(lo, i - 3)]
    b = pts[min(hi, i + 4)]
    ty, tz = b[0] - a[0], b[1] - a[1]
    L = math.hypot(ty, tz) or 1.0
    return y, tz / L, -ty / L


def _belly(x, y):
    """(z, ny, nz) on the tub belly at station x, half width y.  Normal points
    away from the body (downwards)."""
    pts = _prof(x)
    lo, hi = 0, 90
    if y <= pts[lo][0]:
        i, t = lo, 0.0
    elif y >= pts[hi][0]:
        i, t = hi - 1, 1.0
    else:
        i = lo
        for k in range(lo, hi):
            if pts[k][0] <= y <= pts[k + 1][0]:
                i = k
                break
        dy = pts[i + 1][0] - pts[i][0]
        t = (y - pts[i][0]) / dy if dy > 1e-9 else 0.0
    z = pts[i][1] + (pts[i + 1][1] - pts[i][1]) * t
    a = pts[max(lo, i - 3)]
    b = pts[min(hi, i + 4)]
    ty, tz = b[0] - a[0], b[1] - a[1]
    L = math.hypot(ty, tz) or 1.0
    return z, tz / L, -ty / L


# =========================================================================== #
# 2.  principal geometry of the cluster
# =========================================================================== #

D_XLE, D_XTE = 1.470, 0.870          # main deflector chord
F_XLE, F_XTE = 1.512, 0.870          # footplate
S_XLE, S_XTE = 1.505, 1.395          # forward slat
S_OFF = 0.034                        # slat base, inboard of the deflector base

# base line of the deflector / footplate centre, y at the footplate
# D-bb-13: with the base line 12 mm further out the curled top edge crossed
# the floor's own outer rim by 3.9 mm in plan at x = 1.362, where the floor is
# still narrowing.  Pulled in so the whole cluster stays inboard of the rim.
D_Y0 = _pchip([(0.870, 0.638), (0.900, 0.642), (0.960, 0.647), (1.040, 0.649),
               (1.120, 0.645), (1.200, 0.634), (1.280, 0.614), (1.360, 0.578),
               (1.420, 0.542), (1.470, 0.508), (1.512, 0.496)])

# top edge of the deflector (the highest point of the curl)
D_ZT = _pchip([(0.870, 0.398), (0.900, 0.428), (0.960, 0.465), (1.040, 0.492),
               (1.120, 0.505), (1.200, 0.505), (1.280, 0.492), (1.360, 0.450),
               (1.420, 0.396), (1.470, 0.330)])

# how much of the 96 deg curl is present at each station
D_CURL = _pchip([(0.870, 0.34), (0.960, 0.70), (1.060, 0.95), (1.180, 1.00),
                 (1.280, 0.92), (1.360, 0.68), (1.420, 0.40), (1.470, 0.08)])

D_HT = 0.0024          # half laminate thickness (4.8 mm panel)
D_ROLL = 0.0019        # LE / TE roll radius
D_RCURL = 0.036        # curl radius
D_TH0 = 3.0            # lean at the foot, deg
D_TH1 = 13.0           # lean where the curl starts, deg
D_ACURL = 96.0         # full curl sweep, deg
D_NL = 54              # spine samples below the curl
D_NC = 18              # spine samples in the curl

FP_GAP = 0.0060        # footplate underside above the floor
FP_T = 0.0070          # footplate laminate
FP_MID = FP_GAP + FP_T * 0.5
D_ZFOOT = FP_GAP + 0.0025   # deflector foot sinks 4.5 mm into the footplate

# Relief moulded into the deflector, as (x, gaussian half width, height).
# Positive = proud stiffening bead, negative = recessed panel-joint groove.
# D-bb-03: at 1.7 mm over a 13 mm half width the beads were invisible even at
# 6x zoom - the panel read as one dead sheet.  Narrower and taller now, and a
# real two-piece moulding joint runs down the panel at x = 1.238.
D_BEADS = [(1.338, 0.0092, 0.0026), (1.152, 0.0092, 0.0026),
           (0.978, 0.0088, 0.0022), (1.238, 0.0026, -0.0014)]
D_VG = [(1.330, 1.268, 0.0125), (1.246, 1.184, 0.0135),
        (1.162, 1.100, 0.0125)]   # outboard vortex fins: x front, x rear, h


def _chine(t):
    """Tilt blend along the deflector section: a soft feature line at 45 %."""
    return 0.30 * _ss(t / 0.32) + 0.70 * _ss((t - 0.40) / 0.14)


def _defl_spine_raw(x, y0, zt, curl):
    zb = _ftop(x, y0) + D_ZFOOT
    th0 = math.radians(D_TH0)
    th1 = math.radians(D_TH1)
    A = math.radians(D_ACURL) * max(0.0, min(1.0, curl))
    th2 = th1 + A
    gain = D_RCURL * ((1.0 - math.sin(th1)) if th2 > math.pi * 0.5
                      else (math.sin(th2) - math.sin(th1)))
    zc = zt - gain
    H = max(0.02, zc - zb)
    pts = [(y0, zb)]
    dy = 0.0
    for i in range(1, D_NL + 1):
        ang = th0 + (th1 - th0) * _chine((i - 0.5) / D_NL)
        dy += math.tan(ang) * (H / D_NL)
        pts.append((y0 + dy, zb + H * (i / D_NL)))
    cy, cz = pts[-1]
    for k in range(1, D_NC + 1):
        th = th1 + A * (k / D_NC)
        pts.append((cy + D_RCURL * (math.cos(th1) - math.cos(th)),
                    cz + D_RCURL * (math.sin(th) - math.sin(th1))))
    return pts


_SPINE_CACHE = {}


def _defl_spine(x):
    key = round(x * 2000.0)
    sp = _SPINE_CACHE.get(key)
    if sp is None:
        xx = key / 2000.0
        sp = _defl_spine_raw(xx, D_Y0(xx), D_ZT(xx), D_CURL(xx))
        # stiffening beads: push the mid-surface out along its own normal
        amp = 0.0
        for (bx, bw, bh) in D_BEADS:
            amp += bh * math.exp(-((xx - bx) / bw) ** 2)
        if abs(amp) > 1e-6:
            nrm = _norms2(sp)
            n = len(sp)
            out = []
            for i, (py, pz) in enumerate(sp):
                t = i / (n - 1.0)
                # D-bb-07: a short fade let the bead stop dead just under the
                # curl, which read as a gouge in the panel.  Long fades now.
                f = _ss((t - 0.05) / 0.20) * (1.0 - _ss((t - 0.50) / 0.26))
                out.append((py + nrm[i][0] * amp * f,
                            pz + nrm[i][1] * amp * f))
            sp = out
        _SPINE_CACHE[key] = sp
    return sp


def _defl_at(x, z):
    """(mid_y, ny, nz) on the deflector's mid-surface at station x, height z."""
    sp = _defl_spine(x)
    nrm = _norms2(sp)
    if z <= sp[0][1]:
        return sp[0][0], nrm[0][0], nrm[0][1]
    for i in range(len(sp) - 1):
        z0, z1 = sp[i][1], sp[i + 1][1]
        if z0 <= z <= z1:
            t = (z - z0) / (z1 - z0) if z1 > z0 else 0.0
            return (sp[i][0] + (sp[i + 1][0] - sp[i][0]) * t,
                    nrm[i][0] + (nrm[i + 1][0] - nrm[i][0]) * t,
                    nrm[i][1] + (nrm[i + 1][1] - nrm[i][1]) * t)
    return sp[-1][0], nrm[-1][0], nrm[-1][1]


def _defl_mid_y(x, z):
    """y of the deflector's mid-surface at station x and height z."""
    return _defl_at(x, z)[0]


# --------------------------------------------------------------------------- #
# the five horizontal turning vanes
# --------------------------------------------------------------------------- #

# chord-normalised mean line: strongly cambered, trailing edge 6.8 % down
_VMEAN = [(0.000, 0.0000), (0.030, -0.0016), (0.080, -0.0038),
          (0.150, -0.0072), (0.250, -0.0128), (0.360, -0.0198),
          (0.480, -0.0282), (0.600, -0.0376), (0.720, -0.0472),
          (0.840, -0.0570), (0.930, -0.0640), (1.000, -0.0685)]

VANES = [
    dict(z=0.218, xle=1.395, chord=0.375, drop=0.033, sweep=0.030, dch=0.012,
         serr=(9, 0.0052), fence=0.545),
    dict(z=0.270, xle=1.358, chord=0.330, drop=0.031, sweep=0.028, dch=0.011,
         serr=(8, 0.0046), fence=0.420),
    dict(z=0.319, xle=1.321, chord=0.286, drop=0.029, sweep=0.026, dch=0.010,
         serr=(7, 0.0040), fence=0.500),
    dict(z=0.365, xle=1.284, chord=0.243, drop=0.027, sweep=0.024, dch=0.009,
         serr=(6, 0.0034), fence=0.600),
    dict(z=0.408, xle=1.247, chord=0.201, drop=0.025, sweep=0.022, dch=0.008,
         serr=(5, 0.0028), fence=0.455),
]
V_HT = 0.0025
V_NSPAN = 72
V_NCH = 34

# under-chassis turning vanes
U_XF, U_XR = 1.730, 1.548
U_FIN_Y = (0.072, 0.117, 0.162)

# tie struts: (chassis x, chassis z, deflector x, deflector z)
# D-bb-02: the rear strut's chassis boss was at x = 0.950; parts/sidepod's
# inlet surround reaches x = 0.965 at that height, so it moved 50 mm forward.
STRUTS = [(1.372, 0.330, 1.376, 0.352),
          (1.000, 0.396, 1.002, 0.412)]


# =========================================================================== #
# 3.  builders
# =========================================================================== #

def _build_footplate(acc_plate, acc_bolt, acc_rivet, acc_trim):
    win_f = _pchip([(0.870, 0.020), (1.100, 0.020), (1.250, 0.024),
                    (1.330, 0.036), (1.420, 0.046), (1.512, 0.044)])
    wout_f = _pchip([(0.870, 0.046), (0.960, 0.052), (1.100, 0.058),
                     (1.250, 0.052), (1.360, 0.040), (1.440, 0.028),
                     (1.512, 0.017)])

    def tooth(x):
        if x > 1.090 or x < 0.868:
            return 0.0
        fr = ((1.090 - x) / 0.0442) % 1.0
        f = 1.0 - abs(2.0 * fr - 1.0)
        fade = _ss((1.090 - x) / 0.030) * _ss((x - 0.868) / 0.022)
        return 0.0125 * f * fade

    nw = 24
    stations = _roll_stations(F_XLE, F_XTE, 176, 0.0032, nr=5)
    rings = []
    for (x, ks) in stations:
        yc = D_Y0(x)
        y0 = yc - win_f(x)
        y1 = yc + wout_f(x) + tooth(x)
        path = []
        for i in range(nw + 1):
            s = i / nw
            y = y0 + (y1 - y0) * s
            path.append((y, _ftop(x, y) + FP_MID))
        # upturned outer lip
        ye, ze = path[-1]
        gy = ye - path[-2][0]
        gz = ze - path[-2][1]
        gl = math.hypot(gy, gz) or 1.0
        gy, gz = gy / gl, gz / gl
        for (dl, du) in ((0.0055, 0.0018), (0.0090, 0.0055),
                         (0.0098, 0.0096), (0.0086, 0.0131)):
            path.append((ye + gy * dl, ze + gz * dl + du))
        rings.append([(x, py, pz)
                      for (py, pz) in _plate_loop(path, FP_T * 0.5 * ks, nc=6)])
    acc_plate.loft(rings, closed=True, cap_start=False, cap_end=False)

    # spacers + fasteners tying the footplate down to the floor edge
    for x in (1.462, 1.352, 1.238, 1.124, 1.010, 0.906):
        y = D_Y0(x) + 0.030
        zf = _ftop(x, y)
        dz_dx = (_ftop(x + 0.004, y) - _ftop(x - 0.004, y)) / 0.008
        dz_dy = (_ftop(x, y + 0.004) - _ftop(x, y - 0.004)) / 0.008
        nrm = Vector((-dz_dx, -dz_dy, 1.0)).normalized()
        # D-bb-12: a spacer stood on a vertical axis with a flat foot cut 3.3 mm
        # into the floor on its inboard side - the floor's shoulder falls at
        # ~0.33 there.  It stands on the floor's own tangent plane now and its
        # foot beds a uniform 0.3 mm, which is a bonded joint, not a clash.
        H = FP_GAP / max(0.85, nrm.z)
        _revolve_solid(acc_trim,
                       [(0.0, -0.0003), (0.0086, -0.0003), (0.0086, 0.0002),
                        (0.0092, 0.0008), (0.0092, H - 0.0010),
                        (0.0086, H - 0.0004), (0.0086, H + 0.0006),
                        (0.0, H + 0.0006)],
                       (x, y, zf), tuple(nrm), seg=26)
        _bolt(acc_bolt, (x, y, _ftop(x, y) + FP_GAP + FP_T), tuple(nrm),
              rh=0.0050, spin=0.31 * x, shank=0.013)

    # flush rivets down the deflector root joint, both faces
    for i in range(15):
        x = 1.440 - i * 0.0385
        y0 = D_Y0(x)
        zb = _ftop(x, y0) + FP_GAP + FP_T + 0.0038
        for sgn in (1.0, -1.0):
            _rivet(acc_rivet, (x, y0 + sgn * (D_HT + 0.0002), zb),
                   (0.0, sgn, 0.06), r=0.0021)


def _build_deflector(acc):
    stations = _roll_stations(D_XLE, D_XTE, 152, D_ROLL, nr=6)
    rings = []
    for (x, ks) in stations:
        sp = _defl_spine(x)
        rings.append([(x, py, pz)
                      for (py, pz) in _plate_loop(sp, D_HT * ks, nc=6)])
    acc.loft(rings, closed=True, cap_start=False, cap_end=False)


_S_ZT = _pchip([(1.395, 0.354), (1.430, 0.334), (1.470, 0.303),
                (1.505, 0.268)])


def _slat_spine(x):
    y0 = D_Y0(x) - S_OFF
    zt = _S_ZT(x)
    zb = _ftop(x, y0) + D_ZFOOT
    th0, th1 = math.radians(4.0), math.radians(11.0)
    A = math.radians(44.0)
    R = 0.026
    gain = R * (math.sin(th1 + A) - math.sin(th1))
    zc = zt - gain
    H = max(0.02, zc - zb)
    n = 30
    pts = [(y0, zb)]
    dy = 0.0
    for i in range(1, n + 1):
        ang = th0 + (th1 - th0) * _ss((i - 0.5) / n)
        dy += math.tan(ang) * (H / n)
        pts.append((y0 + dy, zb + H * (i / n)))
    cy, cz = pts[-1]
    for k in range(1, 11):
        th = th1 + A * (k / 10.0)
        pts.append((cy + R * (math.cos(th1) - math.cos(th)),
                    cz + R * (math.sin(th) - math.sin(th1))))
    return pts


def _build_slat(acc):
    stations = _roll_stations(S_XLE, S_XTE, 58, 0.0018, nr=5)
    rings = []
    for (x, ks) in stations:
        rings.append([(x, py, pz)
                      for (py, pz) in _plate_loop(_slat_spine(x),
                                                  0.0022 * ks, nc=6)])
    acc.loft(rings, closed=True, cap_start=False, cap_end=False)


def _vane_serr(v, u):
    """Sawtooth added to the chord: a serrated trailing edge, faded out over
    the last 9 % of span at each end so root and tip stay clean."""
    n, amp = v["serr"]
    fr = (u * n) % 1.0
    fade = _ss(u / 0.09) * (1.0 - _ss((u - 0.91) / 0.09))
    return amp * (1.0 - abs(2.0 * fr - 1.0)) * fade


def _vane_y(v, u, px, pz):
    yr = _flank(px, pz)[0] + 0.0030
    yt = _defl_mid_y(px, pz) - 0.0015
    return yr + (yt - yr) * u


def _vane_section(v, u):
    """Chordwise mid-line of one vane at spanwise parameter u, in (x, z)."""
    xle = v["xle"] + v["sweep"] * u
    ch = v["chord"] + v["dch"] * u + _vane_serr(v, u)
    z0 = v["z"] - v["drop"] * (u ** 1.4)
    tw = math.radians(-2.6 * u)
    ct, st = math.cos(tw), math.sin(tw)
    path = []
    for (c, h) in _VMEAN:
        dx = -c * ch
        # moulded spanwise stiffener rib at 30 % chord: 1.15 mm proud on both
        # faces, so the vane is not one dead sheet edge to edge
        dz = h * ch + 0.00115 * math.exp(-((c - 0.30) / 0.075) ** 2)
        # twist about the quarter chord
        px = -0.25 * ch + (dx + 0.25 * ch) * ct - dz * st
        pz = (dx + 0.25 * ch) * st + dz * ct
        path.append((xle + px, z0 + pz))
    return C.catmull_rom(path, V_NCH)


def _build_vanes(acc):
    for v in VANES:
        rings = []
        for j in range(V_NSPAN + 1):
            u = j / V_NSPAN
            mid = _vane_section(v, u)
            swell = (1.0 + 1.05 * (1.0 - _ss(u / 0.075))
                     + 0.85 * _ss((u - 0.925) / 0.075))
            loop = _plate_loop(mid, V_HT * swell, nc=5)
            rings.append([(px, _vane_y(v, u, px, pz), pz)
                          for (px, pz) in loop])
        acc.loft(rings, closed=True, cap_start=True, cap_end=True)
        if v["fence"] is not None:
            _build_vane_fence(acc, v, v["fence"])


def _vane_chord_x(v, uf, s):
    """(x, z) at chord fraction s of one vane's mid-line at spanwise uf."""
    mid = C.catmull_rom(_vane_section(v, uf), 200)
    i = max(0, min(199, int(round(s * 199))))
    return mid[i]


def _build_vane_fence(acc, v, uf):
    """Chordwise flow fence standing on a vane's upper surface.

    D-bb-05: built with a sin() thickness taper the fence's leading and
    trailing edges collapsed to knife slivers that read as torn foil.  It is
    lofted on proper roll stations now, so both ends close on a 1.3 mm radius.
    """
    mid = C.catmull_rom(_vane_section(v, uf), 200)
    x_hi, x_lo = mid[8][0], mid[176][0]
    rings = []
    for (x, ks) in _roll_stations(x_hi, x_lo, 62, 0.0013, nr=5):
        s = (x_hi - x) / (x_hi - x_lo)
        pz = None
        for i in range(len(mid) - 1):
            if mid[i][0] >= x >= mid[i + 1][0]:
                dx = mid[i][0] - mid[i + 1][0]
                t = (mid[i][0] - x) / dx if dx > 1e-9 else 0.0
                pz = mid[i][1] + (mid[i + 1][1] - mid[i][1]) * t
                break
        if pz is None:
            pz = mid[0][1] if x > mid[0][0] else mid[-1][1]
        y = _vane_y(v, uf, x, pz)
        # D-bb-09: an 11 mm fence read as a scratch on the panel behind it.
        h = 0.0175 * (0.32 + 0.68 * math.sin(math.pi * min(1.0, 0.10 + s)))
        lean = 0.0072 * (s ** 1.25)
        path = [(y, pz - 0.0019),
                (y + lean * 0.24, pz + h * 0.36),
                (y + lean * 0.62, pz + h * 0.72),
                (y + lean, pz + h)]
        rings.append([(x, py, pzz)
                      for (py, pzz) in _plate_loop(path, 0.0016 * ks, nc=5)])
    acc.loft(rings, closed=True, cap_start=False, cap_end=False)


def _build_defl_trim(acc_fin, acc_rivet):
    """Outboard vortex strakes and the rivet row beside the moulded panel joint.

    D-bb-06: the strakes were lofted with a sin() thickness taper and a
    3-point section; both ends finished as curled slivers.  Roll stations and
    a 5-point section now give a proper delta strake with a rolled top edge.
    """
    for (xa, xb, hmax) in D_VG:
        rings = []
        for (x, ks) in _roll_stations(xa, xb, 40, 0.0015, nr=5):
            s = max(0.0, min(1.0, (xa - x) / (xa - xb)))
            zf = D_ZT(x) - 0.098
            my, ny, nz = _defl_at(x, zf)
            h = hmax * (0.10 + 0.90 * (1.0 - s) ** 0.75)
            path = [(my - ny * 0.0013, zf - nz * 0.0013)]
            for k in (0.28, 0.58, 0.82, 1.0):
                lean = 0.0022 * (k ** 1.4)
                path.append((my + ny * (h * k) + lean,
                             zf + nz * (h * k) + 0.0016 * k))
            rings.append([(x, py, pz)
                          for (py, pz) in _plate_loop(path, 0.0017 * ks, nc=5)])
        acc_fin.loft(rings, closed=True, cap_start=False, cap_end=False)

    xr = 1.2205
    zb = _ftop(xr, D_Y0(xr)) + D_ZFOOT
    zt = D_ZT(xr) - 0.052
    for i in range(10):
        z = zb + 0.052 + (zt - zb - 0.052) * (i / 9.0)
        my, ny, nz = _defl_at(xr, z)
        _rivet(acc_rivet, (xr, my + ny * (D_HT + 0.0002),
                           z + nz * (D_HT + 0.0002)), (0.0, ny, nz), r=0.0020)


def _build_root_strips(acc_strip, acc_bolt, acc_rivet):
    for v in VANES:
        x_hi = v["xle"] + 0.019
        x_lo = v["xle"] - v["chord"] - 0.015
        stations = _roll_stations(x_hi, x_lo, 42, 0.0026, nr=5)
        rings = []
        for (x, ks) in stations:
            u = max(0.0, min(1.0, (v["xle"] - x) / v["chord"]))
            zc = _vane_z_at(v, x)
            hz = 0.0225 - 0.0035 * u
            path = []
            n = 15
            for i in range(n + 1):
                z = zc - hz + 2.0 * hz * (i / n)
                y, _ny, _nz = _flank(x, z)
                path.append((y + 0.0046, z))
            rings.append([(x, py, pz)
                          for (py, pz) in _plate_loop(path, 0.0025 * ks, nc=5)])
        acc_strip.loft(rings, closed=True, cap_start=False, cap_end=False)

        # 3 fasteners per strip, alternating above / below the vane root
        for k, (fx, dz) in enumerate(((0.17, 0.0135), (0.50, -0.0135),
                                      (0.83, 0.0135))):
            x = v["xle"] - v["chord"] * fx
            z = _vane_z_at(v, x) + dz
            y, ny, nz = _flank(x, z)
            _bolt(acc_bolt, (x, y + 0.0074, z), (0.0, ny, nz),
                  rh=0.0044, spin=0.7 * k + x, shank=0.012)
        # rivet rows along both long edges of the strip
        for i in range(7):
            fx = 0.06 + 0.147 * i
            x = v["xle"] - v["chord"] * fx
            for sgn in (1.0, -1.0):
                z = _vane_z_at(v, x) + sgn * 0.0185
                y, ny, nz = _flank(x, z)
                _rivet(acc_rivet, (x, y + 0.0073, z), (0.0, ny, nz), r=0.0021)


def _vane_z_at(v, x):
    """z of a vane's root mean line at station x (used to place its strip)."""
    mid = _vane_section(v, 0.0)
    if x >= mid[0][0]:
        return mid[0][1]
    if x <= mid[-1][0]:
        return mid[-1][1]
    for i in range(len(mid) - 1):
        if mid[i][0] >= x >= mid[i + 1][0]:
            dx = mid[i][0] - mid[i + 1][0]
            t = (mid[i][0] - x) / dx if dx > 1e-9 else 0.0
            return mid[i][1] + (mid[i + 1][1] - mid[i][1]) * t
    return mid[-1][1]


_U_Y0 = _pchip([(1.548, 0.030), (1.620, 0.038), (1.690, 0.052),
                (1.730, 0.064)])
_U_Y1 = _pchip([(1.548, 0.206), (1.620, 0.200), (1.690, 0.188),
                (1.730, 0.178)])


def _build_under(acc_vane, acc_rivet):
    # belly pad - swept planform, wider where the tunnel inlets are fed
    stations = _roll_stations(U_XF, U_XR, 62, 0.0028, nr=6)
    rings = []
    ny_pad = 32
    for (x, ks) in stations:
        ya, yb_ = _U_Y0(x), _U_Y1(x)
        path = []
        for i in range(ny_pad + 1):
            y = ya + (yb_ - ya) * (i / ny_pad)
            z, ny, nz = _belly(x, y)
            # two shallow moulded strakes across the pad
            o = 0.0035 + 0.0016 * (math.exp(-((y - 0.096) / 0.0075) ** 2)
                                   + math.exp(-((y - 0.140) / 0.0075) ** 2))
            path.append((y + ny * o, z + nz * o))
        rings.append([(x, py, pz)
                      for (py, pz) in _plate_loop(path, 0.0025 * ks, nc=5)])
    acc_vane.loft(rings, closed=True, cap_start=False, cap_end=False)

    # three curved fins hanging under it
    for k, yb in enumerate(U_FIN_Y):
        x_hi, x_lo = U_XF - 0.012, U_XR + 0.010
        stations = _roll_stations(x_hi, x_lo, 64, 0.0020, nr=6)
        rings = []
        nseg = 18
        for (x, ks) in stations:
            s = (x_hi - x) / (x_hi - x_lo)
            # D-bb-01: sizing the fins by depth put their tips at z = 0.040 -
            # level with the plank and 10 mm BELOW the floor underside.  Drive
            # the bottom edge from an absolute z instead, so the fins always
            # finish in clean air above the floor's leading-edge lip.
            z_bot = 0.0668 - 0.0052 * _ss(s)
            z0, ny, nz = _belly(x, yb)
            depth = max(0.012, ((z0 + nz * 0.0035) - z_bot) / max(0.2, -nz))
            base = (yb + ny * 0.0035, z0 + nz * 0.0035)
            path = []
            for i in range(nseg + 1):
                t = i / nseg
                d = depth * t
                # S-curved in section: these are turning vanes, so they bow
                # outboard and hook back, not flat planks
                lean = (0.020 * math.sin(math.pi * t ** 0.85)
                        - 0.009 * (t ** 2.4)) * (0.40 + 0.60 * s)
                path.append((base[0] + ny * d + lean, base[1] + nz * d))
            rings.append([(x, py, pz)
                          for (py, pz) in _plate_loop(path, 0.0021 * ks, nc=5)])
        acc_vane.loft(rings, closed=True, cap_start=False, cap_end=False)

        for i in range(4):
            x = x_hi - 0.020 - i * 0.043
            for sgn in (1.0, -1.0):
                y = yb + sgn * 0.0048
                z, ny, nz = _belly(x, y)
                _rivet(acc_rivet, (x, y + ny * 0.0059, z + nz * 0.0059),
                       (0.0, ny, nz), r=0.0019)

    # perimeter rivets on the pad
    for i in range(11):
        x = U_XF - 0.014 - i * 0.0152
        for y in (_U_Y0(x) + 0.008, _U_Y1(x) - 0.008):
            z, ny, nz = _belly(x, y)
            _rivet(acc_rivet, (x, y + ny * 0.0059, z + nz * 0.0059),
                   (0.0, ny, nz), r=0.0020)


def _surf_frame(fy, x, z, d=0.005):
    """Tangent-plane frame of a surface y = fy(x, z): (point, outward normal,
    chordwise tangent).

    D-bb-10: the strut clevises were placed on a rigid (0, ny, nz) frame.  Over
    the deflector's swept leading edge dY/dx reaches -0.60, so a bracket 18 mm
    long punched 11 mm straight through the 4.8 mm panel.  Landing brackets on
    the real tangent plane cuts the worst-case departure over their whole
    footprint to 0.11 mm, which is second-order curvature only.
    """
    p = Vector((x, fy(x, z), z))
    tx = Vector((2.0 * d, fy(x + d, z) - fy(x - d, z), 0.0)).normalized()
    tz = Vector((0.0, fy(x, z + d) - fy(x, z - d), 2.0 * d)).normalized()
    n = tz.cross(tx).normalized()
    tx = (tx - n * tx.dot(n)).normalized()
    return p, n, tx


def _build_struts(acc_strut, acc_bolt, acc_trim):
    for (cx, cz, dx, dz) in STRUTS:
        pc0, nc, ac = _surf_frame(lambda a, b: _flank(a, b)[0], cx, cz)
        pc = pc0 + nc * 0.0014
        pd0, nd_out, ad = _surf_frame(_defl_mid_y, dx, dz)
        nd = -nd_out
        pd = pd0 + nd * 0.0026

        piv_c = pc + nc * 0.0255
        piv_d = pd + nd * 0.0245
        axis = (piv_d - piv_c).normalized()

        # D-bb-08: the tube ended open at the pivot with a 9.8 mm mouth that the
        # eye could not cover, so each rod end had a black hole in it.  The
        # shank is now narrower than the eye is wide and is capped inside the
        # spherical bearing.
        rr = 0.0058
        rprof = []
        for i in range(37):
            t = i / 36.0
            e = min(t, 1.0 - t)
            if e < 0.030:
                r = 0.0067
            else:
                r = 0.0067 + (rr - 0.0067) * _ss((e - 0.030) / 0.070)
            rprof.append((t, r))
        _tube(acc_strut, piv_c, piv_d, rprof, seg=32, cap=True)

        _rod_end(acc_strut, acc_bolt, acc_trim, pc, nc, ac, 0.0255)
        _rod_end(acc_strut, acc_bolt, acc_trim, pd, nd, ad, 0.0245)


# Outline of a clevis lug in (in-plane tangent, surface normal) space.
# D-bb-11: the base ran 2.5 mm BELOW the pad origin, which left only 0.5 mm of
# margin inside a 4.8 mm panel - the four corners of the two lugs punched
# through the deflector's outboard face as bright slivers.  The base now sits
# 1.0 mm ABOVE the origin and the origin itself is set 0.2 mm proud of the
# panel's inboard face, so the lugs never reach the mid-surface.
_LUG = [(-0.0182, 0.0010), (-0.0170, 0.0048), (-0.0138, 0.0110),
        (-0.0104, 0.0170)]


def _rod_end(acc, acc_bolt, acc_trim, p, n, a, hpiv):
    """Twin-lug clevis with a spherical rod end - what a real tie strut lands
    on.  D-bb-04 replaced a flat 29 mm disc that read as a plain cylinder end.

    `a` must be an IN-PLANE tangent of the surface (see _surf_frame): the lug's
    long axis follows it, so a long bracket stays on a swept panel.
    """
    p = Vector(p)
    n = Vector(n).normalized()
    a = Vector(a) - n * Vector(a).dot(n)
    if a.length < 1e-6:
        a = Vector((1.0, 0.0, 0.0))
    a = a.normalized()
    e = n.cross(a).normalized()
    piv = Vector(p) + n * hpiv

    # machined pad the clevis stands on
    _revolve_solid(acc, [(0.0, -0.0018), (0.0138, -0.0018), (0.0150, -0.0004),
                         (0.0150, 0.0032), (0.0138, 0.0046), (0.0092, 0.0052),
                         (0.0, 0.0052)],
                   tuple(p), tuple(n), seg=32)

    poly = list(_LUG)
    rp = 0.0128
    for k in range(17):
        ang = math.radians(196.0 - 212.0 * k / 16.0)
        poly.append((rp * math.cos(ang), hpiv + rp * math.sin(ang)))
    poly += [(0.0104, 0.0170), (0.0138, 0.0110), (0.0170, 0.0048),
             (0.0182, 0.0010)]
    for side in (-1.0, 1.0):
        _prism(acc, poly, tuple(p + e * (side * 0.0108)), e, a, n,
               0.0038, cham=0.0007)

    # spherical bearing + its eye
    _revolve_solid(acc, [(0.0074, -0.0070), (0.0108, -0.0070), (0.0115, -0.0062),
                         (0.0115, 0.0062), (0.0108, 0.0070), (0.0074, 0.0070),
                         (0.0068, 0.0062), (0.0068, -0.0062), (0.0074, -0.0070)],
                   tuple(piv), tuple(e), seg=32)
    ball = []
    for k in range(17):
        ang = math.radians(-90.0 + 180.0 * k / 16.0)
        ball.append((0.0072 * math.cos(ang), 0.0072 * math.sin(ang)))
    _revolve_solid(acc_trim, ball, tuple(piv), tuple(e), seg=32)

    _bolt(acc_bolt, tuple(piv + e * 0.0133), tuple(e), rh=0.0052,
          spin=1.7 * p.x, shank=0.028)
    _revolve_solid(acc_bolt, [(0.0, -0.0034), (0.0050, -0.0034, True),
                              (0.0050, 0.0028, True), (0.0044, 0.0034),
                              (0.0, 0.0034)],
                   tuple(piv - e * 0.0161), tuple(-e), seg=24)


# =========================================================================== #
# 4.  entry point
# =========================================================================== #

def build(coll, ctx=None):
    _SPINE_CACHE.clear()
    _PROF_CACHE.clear()

    plate = _Acc()
    defl = _Acc()
    slat = _Acc()
    vanes = _Acc()
    strips = _Acc()
    under = _Acc()
    strut = _Acc()
    bolts = _Acc()
    rivets = _Acc()
    trim = _Acc()

    _build_footplate(plate, bolts, rivets, trim)
    _build_deflector(defl)
    _build_defl_trim(defl, rivets)
    _build_slat(slat)
    _build_vanes(vanes)
    _build_root_strips(strips, bolts, rivets)
    _build_under(under, rivets)
    _build_struts(strut, bolts, trim)

    for a in (plate, defl, slat, vanes, strips, under, strut, bolts,
              rivets, trim):
        a.mirror()

    made = [
        plate.emit(P + "Footplate", coll, "CarbonMatte", auto=40.0),
        defl.emit(P + "Deflector", coll, "CarbonFibre", auto=42.0),
        slat.emit(P + "Slat", coll, "CarbonFibre", auto=42.0),
        vanes.emit(P + "Vanes", coll, "CarbonFibre", auto=42.0),
        strips.emit(P + "RootStrips", coll, "CarbonMatte", auto=40.0),
        under.emit(P + "UnderVanes", coll, "CarbonMatte", auto=40.0),
        strut.emit(P + "Struts", coll, "Titanium", auto=34.0),
        bolts.emit(P + "Fasteners", coll, "SteelFastener", auto=30.0),
        rivets.emit(P + "Rivets", coll, "Titanium", auto=32.0),
        trim.emit(P + "Spacers", coll, "AnodisedRed", auto=32.0),
    ]
    return made
