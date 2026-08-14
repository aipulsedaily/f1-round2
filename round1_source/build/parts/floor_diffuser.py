"""Complete 2022-spec underfloor: venturi tunnels, fences, plank, diffuser.

Coordinate contract: +X forward, +Y car left, +Z up, tyre contact at z = 0.
Nothing here bakes in S.GROUND.

What is in the box
------------------
    * one lofted floor shell, x = +1.550 -> S.DIFFUSER_EXIT_X, half width 0.855,
      underside reference plane at S.FLOOR_Z. The underside carries two venturi
      tunnels (inlet mouth -> throat at x ~ +0.85 -> expansion -> diffuser),
      a rolled outer rim and a rolled leading edge lip.
    * 4 floor fences per side hanging off the swept leading edge, varying depth,
      leaning outboard, rounded bottom edges.
    * floor edge wing running the outer rim, hooked section with a rolled lip
      and a slow spanwise wave, fading back into the rim at both ends.
    * 3 tyre-wake deflectors per side on the outer floor ahead of the rear tyre.
    * plank on the centreline, underside at S.PLANK_Z, with milled skid
      pockets, 8 titanium skid blocks, 3 wear-measurement holes and 86 real
      countersunk fasteners (conical seats booleaned into the plank and into
      the skids, hex sockets in the heads).
    * diffuser: steep upsweep from x = -1.45, central keel, 8 separator vanes
      with raked leading edges running the full depth of the expansion.
    * bonded joint straps down the tunnel roofs and the diffuser, each with a
      row of flush titanium fasteners; two more fastener rows off the straps.

Everything is authored from one analytic underside height field, so fences,
vanes and fasteners sit exactly on the surface instead of floating near it.
"""

import math

import bpy
from mathutils import Vector

import common as C
import spec as S

NAME = "floor_diffuser"
P = "FD_"

# --------------------------------------------------------------------------- #
# principal geometry
# --------------------------------------------------------------------------- #

X_LE = 1.5500                    # floor leading edge
X_EXIT = S.DIFFUSER_EXIT_X       # -2.2300
Z_REF = S.FLOOR_Z                # 0.0500 - underside reference plane
Z_PLANK = S.PLANK_Z              # 0.0400 - plank underside

Y_IN = 0.1500                    # flat centre strip half width (plank land)
T_RIM = 0.0160                   # laminate thickness at the outer rim

# D-fd-R2-03: the plank/skid is the ride-height datum and the wear reference,
# so it has to be the lowest thing on the car. Nothing else in this module may
# hang below this plane. (Skid faces sit at 0.0389, i.e. 1.1 mm proud of the
# plank underside, so plank -> skid stays the bottom two layers.)
Z_LOW = Z_PLANK + 0.0006         # 0.0406

PLANK_HW = 0.1500
PLANK_XF = 1.4000
PLANK_XR = -1.4400
PLANK_TOP = 0.0506               # 0.6 mm into the floor: bonded, no z-fight

N_FLAT = 12                      # ring samples across the flat centre strip
N_ARCH = 110                     # ring samples across one tunnel
N_ROLL = 14                      # samples around the rolled rim

FENCE_MAT = "CarbonMatte"


# --------------------------------------------------------------------------- #
# curve helpers (spec.py / common.py are frozen, so these live here)
# --------------------------------------------------------------------------- #

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


def _curve(ctrl, smooth=24, samples=1600):
    """PCHIP, then binomial-smoothed into a LUT.

    PCHIP is only C1: the curvature step at each knot shows up as a faint band
    in a specular reflection even when the silhouette looks perfect. Smoothing
    the sampled curve removes the step without letting the shape wander.
    """
    f = _pchip(ctrl)
    xs = sorted(p[0] for p in ctrl)
    x0, x1 = xs[0], xs[-1]
    vals = [f(x0 + (x1 - x0) * i / (samples - 1)) for i in range(samples)]
    for _ in range(smooth):
        prev = vals[:]
        for i in range(1, samples - 1):
            vals[i] = 0.25 * prev[i - 1] + 0.5 * prev[i] + 0.25 * prev[i + 1]
    dx = (x1 - x0) / (samples - 1)

    def g(x):
        if x <= x0:
            return vals[0]
        if x >= x1:
            return vals[-1]
        t = (x - x0) / dx
        i = int(t)
        u = t - i
        return vals[i] * (1.0 - u) + vals[i + 1] * u
    return g


# floor half width -------------------------------------------------------- #
W = _curve([(1.5500, 0.5200), (1.5000, 0.5580), (1.4400, 0.6060), (1.3600, 0.6720),
            (1.2800, 0.7340), (1.2000, 0.7880), (1.1200, 0.8260), (1.0400, 0.8480),
            (0.9600, 0.8540), (0.7000, 0.8550), (0.3000, 0.8550), (-0.1000, 0.8550),
            (-0.5000, 0.8550), (-0.8000, 0.8520), (-1.0000, 0.8380), (-1.1200, 0.8060),
            (-1.2400, 0.7480), (-1.3600, 0.6800), (-1.4600, 0.6220), (-1.5600, 0.5880),
            (-1.7000, 0.5680), (-1.9000, 0.5600), (-2.1000, 0.5520), (-2.2300, 0.5450)])

# centreline underside (diffuser roof on the centreline) ------------------- #
ZK = _curve([(1.5500, 0.0500), (0.8000, 0.0500), (0.0000, 0.0500), (-0.8000, 0.0500),
             (-1.2000, 0.0500), (-1.3600, 0.0506), (-1.4500, 0.0530), (-1.5400, 0.0640),
             (-1.6400, 0.0830), (-1.7600, 0.1120), (-1.8800, 0.1460), (-2.0000, 0.1850),
             (-2.1000, 0.2250), (-2.1700, 0.2590), (-2.2300, 0.2900)])

# tunnel roof peak height ------------------------------------------------- #
ZT = _curve([(1.5500, 0.1520), (1.4400, 0.1410), (1.3000, 0.1290), (1.1500, 0.1190),
             (1.0000, 0.1130), (0.8500, 0.1100), (0.6000, 0.1150), (0.3000, 0.1250),
             (0.0000, 0.1380), (-0.4000, 0.1580), (-0.8000, 0.1800), (-1.1000, 0.2000),
             (-1.3500, 0.2210), (-1.5000, 0.2440), (-1.7000, 0.2770), (-1.9000, 0.3030),
             (-2.1000, 0.3210), (-2.2300, 0.3300)])

# outer rim underside ------------------------------------------------------ #
ZE = _curve([(1.5500, 0.0545), (1.3000, 0.0525), (1.0000, 0.0518), (0.4000, 0.0515),
             (-0.2000, 0.0515), (-0.8000, 0.0530), (-1.1000, 0.0565), (-1.3000, 0.0645),
             (-1.5000, 0.0790), (-1.7000, 0.0955), (-1.9000, 0.1090), (-2.1000, 0.1195),
             (-2.2300, 0.1250)])

# position of the tunnel roof peak, as a fraction across the tunnel -------- #
FPK = _curve([(1.5500, 0.420), (1.2000, 0.470), (0.6000, 0.510), (0.0000, 0.520),
              (-0.6000, 0.515), (-1.2000, 0.495), (-1.7000, 0.460), (-2.2300, 0.420)])

# laminate thickness scale - rolls the LE lip closed and thins the exit TE - #
KT = _curve([(1.5500, 0.090), (1.5420, 0.300), (1.5280, 0.660), (1.5100, 0.900),
             (1.4800, 1.000), (0.0000, 1.000), (-1.6000, 1.000), (-1.9000, 0.900),
             (-2.0800, 0.600), (-2.1800, 0.340), (-2.2300, 0.185)],
            smooth=6, samples=2400)

# laminate thickness across the section (f = 0 centre .. 1 rim) ------------ #
TSEC = _pchip([(0.00, 0.0106), (0.18, 0.0140), (0.40, 0.0182), (0.72, 0.0180),
               (1.00, T_RIM)])


# --------------------------------------------------------------------------- #
# the underside height field
# --------------------------------------------------------------------------- #

def _arch(f, fp):
    """Tunnel cross-section shape: 0 at the keel land, 1 at the roof peak,
    0 again at the rim, tangent-continuous at all three."""
    if f <= 0.0 or f >= 1.0:
        return 0.0
    if f <= fp:
        return C.smoothstep((f / fp) ** 0.85)
    return 1.0 - C.smoothstep(((f - fp) / (1.0 - fp)) ** 1.18)


class _St:
    """Cached station constants - the ring builder hits these ~250 times."""

    __slots__ = ("x", "w", "zk", "zt", "ze", "fp", "k", "r", "b")

    def __init__(self, x):
        x = min(X_LE, max(X_EXIT, x))
        self.x = x
        self.w = W(x)
        self.zk = ZK(x)
        self.zt = ZT(x)
        self.ze = ZE(x)
        self.fp = FPK(x)
        self.k = KT(x)
        self.r = 0.5 * T_RIM * self.k          # rolled rim radius
        self.b = self.w - self.r               # y where the rim roll starts


def _frac(st, y):
    if y <= Y_IN:
        return 0.0
    if y >= st.b:
        return 1.0
    return (y - Y_IN) / (st.b - Y_IN)


def _prof(st, y):
    """(z_under, z_top) of the shell at station st, |y| <= st.b."""
    y = abs(y)
    f = _frac(st, y)
    if f <= 0.0:
        zu = st.zk
    elif f >= 1.0:
        zu = st.ze
    else:
        base = C.lerp(st.zk, st.ze, f)
        zu = base + _arch(f, st.fp) * (st.zt - base)
    t = TSEC(f)
    # the k taper pulls both skins toward the mid surface, closing the LE lip
    # and thinning the diffuser trailing edge without moving the mid surface.
    half = 0.5 * t * (1.0 - st.k)
    return zu + half, zu + t - half


def _skin(st, y):
    """(z_under, z_top) of the real shell at station st for ANY |y|.

    Outboard of st.b the shell is the rolled rim - a half circle of radius
    st.r centred on the mid surface - not the flat profile _prof extrapolates
    there. Plates whose bonded root reaches past st.b (fence 2 does) need the
    true surface or the clamp below is computed against a skin that is not
    where the mesh actually is.
    """
    y = abs(y)
    if y <= st.b:
        return _prof(st, y)
    zu_b, zt_b = _prof(st, st.b)
    zc = 0.5 * (zu_b + zt_b)
    rr = max(0.5 * (zt_b - zu_b), 1e-5)
    d = min(y - st.b, rr)
    e = math.sqrt(max(0.0, rr * rr - d * d))
    return zc - e, zc + e


def _root_top(st, yc, rise, margin=0.0006):
    """Callable dy -> world z for a bonded plate root at station st.

    D-fd-R2-02: the plate root used to be a flat horizontal strip `rise` above
    the underside at the plate centreline. In the diffuser the KT taper thins
    the laminate to 2.0-3.4 mm while the underside still falls ~0.9 mm per mm
    of y, so a 14 mm wide flared root could not possibly stay inside it: the
    keel and every vane came out through the UPPER skin (measured +1.0 to
    +8.7 mm) as a sawtooth of slivers on top of the diffuser. Following the
    surface across the plate's own footprint keeps the root buried at every y
    while still touching the underside everywhere, so it neither pokes through
    nor floats.
    """
    def f(dy):
        zu, zt = _skin(st, yc + dy)
        gap = max(zt - zu, 3e-4)
        return min(zu + rise, zt - min(margin, 0.30 * gap))
    return f


def _under_z(x, y):
    return _prof(_St(x), y)[0]


def _under_normal(x, y, h=0.0016):
    """Outward (downward) unit normal of the underside height field."""
    zx = (_under_z(x + h, y) - _under_z(x - h, y)) / (2.0 * h)
    zy = (_under_z(x, y + h) - _under_z(x, y - h)) / (2.0 * h)
    n = Vector((zx, zy, -1.0))
    n.normalize()
    return n


def _le_x(y):
    """x of the swept leading edge at half width y (bisection on W)."""
    if y <= W(X_LE):
        return X_LE
    lo, hi = 0.95, X_LE
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        if W(mid) > y:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


# --------------------------------------------------------------------------- #
# mesh accumulation
# --------------------------------------------------------------------------- #

class _Acc:
    def __init__(self):
        self.v = []
        self.f = []

    def add(self, verts, faces):
        n = len(self.v)
        self.v.extend(tuple(p) for p in verts)
        self.f.extend(tuple(i + n for i in fc) for fc in faces)
        return n

    def add_mirrored(self, verts, faces):
        self.add([(p[0], -p[1], p[2]) for p in verts],
                 [tuple(reversed(fc)) for fc in faces])

    def emit(self, name, coll, mat, auto=35.0, smooth=True, merge=None):
        ob = C.new_obj(name, self.v, self.f, coll=coll, smooth=smooth)
        if merge:
            C.merge_doubles(ob, merge)
        C.shade_auto_smooth(ob, auto)
        S.assign(ob, mat)
        return ob


def _ring_pts(cx, cy, r, n, z, spin=0.0):
    return [(cx + r * math.cos(spin + C.TAU * i / n),
             cy + r * math.sin(spin + C.TAU * i / n), z) for i in range(n)]


def _hex_ring(n_side=4):
    """Unit hexagon perimeter sampled into 6*n_side points."""
    out = []
    for c in range(6):
        a0 = C.TAU * c / 6.0
        a1 = C.TAU * (c + 1) / 6.0
        p0 = (math.cos(a0), math.sin(a0))
        p1 = (math.cos(a1), math.sin(a1))
        for i in range(n_side):
            t = i / n_side
            out.append((C.lerp(p0[0], p1[0], t), C.lerp(p0[1], p1[1], t)))
    return out


_HEX24 = _hex_ring(4)


def _bridge(a0, b0, n, closed=True):
    """Quads between two equal-length vertex index runs."""
    out = []
    span = n if closed else n - 1
    for j in range(span):
        j2 = (j + 1) % n
        out.append((a0 + j, a0 + j2, b0 + j2, b0 + j))
    return out


# --------------------------------------------------------------------------- #
# the floor shell
# --------------------------------------------------------------------------- #

def _station_xs():
    segs = [(X_LE, 1.5000, 14), (1.5000, 1.3000, 18), (1.3000, 1.0000, 20),
            (1.0000, 0.2000, 34), (0.2000, -0.6000, 34), (-0.6000, -1.2000, 26),
            (-1.2000, -1.4500, 14), (-1.4500, -1.9000, 44), (-1.9000, -2.1600, 26),
            (-2.1600, X_EXIT, 9)]
    xs = []
    for (x0, x1, n) in segs:
        for i in range(n):
            xs.append(x0 + (x1 - x0) * i / n)
    xs.append(X_EXIT)
    return xs


def _section_ys(st):
    """y samples across one half of the underside, cosine-clustered so the
    inner tunnel wall and the rim - the two high-curvature zones - get the
    tight spacing instead of the flat middle."""
    ys = [Y_IN * i / (N_FLAT - 1) for i in range(N_FLAT)]
    span = st.b - Y_IN
    for i in range(1, N_ARCH + 1):
        f = 0.5 - 0.5 * math.cos(math.pi * i / N_ARCH)
        ys.append(Y_IN + span * f)
    return ys


def _shell_ring(st):
    """Closed YZ ring: underside outboard, around the rolled rim, top skin
    back inboard, then mirrored. Underside and top share y samples so the end
    caps can be a clean quad bridge instead of a self-overlapping n-gon."""
    ys = _section_ys(st)
    nu = len(ys)
    prof = [_prof(st, y) for y in ys]
    half = [(ys[i], prof[i][0]) for i in range(nu)]

    zu_b, zt_b = prof[-1]
    zc = 0.5 * (zu_b + zt_b)
    rr = max(0.5 * (zt_b - zu_b), 1e-5)
    for i in range(1, N_ROLL):
        a = -0.5 * math.pi + math.pi * i / N_ROLL
        half.append((st.b + rr * math.cos(a), zc + rr * math.sin(a)))

    for i in range(nu - 1, -1, -1):
        half.append((ys[i], prof[i][1]))

    ring = [(st.x, y, z) for (y, z) in half]
    ring += [(st.x, -y, z) for (y, z) in reversed(half[1:-1])]
    return ring, nu


def _cap_faces(base, h_len, nu, nri):
    """Caps for one shell end ring. `base` is the ring's first vertex index."""
    full = 2 * h_len - 2

    def idx(h, side):
        if side == 0 or h == 0 or h == h_len - 1:
            return base + h
        return base + full - h

    faces = []
    for side in (0, 1):
        top = h_len - 1                       # half index of the top at y=0
        for i in range(nu - 1):
            a = idx(i, side)
            b = idx(i + 1, side)
            c = idx(top - (i + 1), side)
            d = idx(top - i, side)
            faces.append((a, b, c, d) if side == 0 else (d, c, b, a))
        rim = [idx(nu - 1 + j, side) for j in range(nri + 2)]
        faces.append(tuple(rim) if side == 0 else tuple(reversed(rim)))
    return faces


def _build_shell(coll):
    xs = _station_xs()
    rings = []
    nu = nri = 0
    for x in xs:
        st = _St(x)
        ring, nu = _shell_ring(st)
        nri = N_ROLL - 1
        rings.append(ring)

    verts, faces = C.loft(rings, closed=True, cap_start=False, cap_end=False)
    h_len = 2 * nu + nri
    faces += _cap_faces(0, h_len, nu, nri)
    faces += _cap_faces((len(rings) - 1) * len(rings[0]), h_len, nu, nri)

    ob = C.new_obj(P + "Shell", verts, faces, coll=coll, smooth=True)
    C.merge_doubles(ob, 1e-6)
    C.shade_auto_smooth(ob, 46.0)
    S.assign(ob, "CarbonMatte")
    return ob


# --------------------------------------------------------------------------- #
# swept plate primitive - fences, diffuser vanes, keel
# --------------------------------------------------------------------------- #

def _plate_ring(x, yc, z_top, z_bot, t, lean=0.0, top=None, n_side=16,
                n_round=14, fillet=0.0038, fh=0.0130):
    """Closed section of a vertical plate: bonded root (buried in the floor),
    rounded bottom edge, optional outboard lean.

    `fillet` flares the plate where it meets the floor. A plate that meets a
    laminate at a knife-sharp 90 deg join reads as a card pushed into the
    surface; the real thing is bonded with a radiused fillet.

    `top` is an optional callable dy -> world z (see _root_top) giving where
    the root sits at the local y offset. Without it the root is a flat
    horizontal strip, which is only safe on a floor that is flat across the
    plate's own width. The widest point of the flare is exactly at the root,
    so the flat version puts its two root corners up to 8.7 mm off the surface
    the plate is supposed to be bonded to.
    """
    # a plate can never be thicker than the depth it has to fit its bottom
    # round into - thin it instead of pushing the bottom edge through the floor
    t = max(6e-5, min(t, (z_top - z_bot) / 2.4))
    fillet = min(fillet, 1.4 * t)
    tl = math.tan(lean)
    zr = z_bot + t
    w0 = t + fillet                       # the root is the widest section
    ztc = top(0.0) if top else z_top      # lean datum

    def rootz(dy):
        """Root z at plate-local offset dy, solved WITH the lean shift.

        A leaning plate does not meet the floor at yc + dy: the root is
        displaced by (ztc - z_root) * tan(lean), and on one side that moves it
        back to where the diffuser roof is lower. Sampling the skin at the
        nominal offset left that corner ~1.1 mm proud. Three fixed-point steps
        converge to well under a micron.
        """
        if top is None:
            return z_top
        z = top(dy)
        for _ in range(3):
            z = top(dy + (ztc - z) * tl)
        return z

    ztp = rootz(w0)                        # +y flare corner
    ztm = rootz(-w0)                       # -y flare corner
    # the two closure points sit only t/3 off the centreline, but at the
    # diffuser exit the roof falls 1.3 mm per mm of y - enough on its own to
    # push a centreline-sampled root out through a 4 mm laminate.
    ztq = rootz(t / 3.0)
    ztr = rootz(-t / 3.0)

    def pt(y, z):
        return (x, yc + y + (ztc - z) * tl, z)

    def wall(sign, za):
        out = []
        for i in range(n_side):
            z = C.lerp(za, zr, (i / (n_side - 1)) ** 1.55)
            u = (za - z) / fh
            w = t + fillet * max(0.0, 1.0 - u) ** 1.7 if u < 1.0 else t
            out.append(pt(sign * w, z))
        return out

    pts = wall(1.0, ztp)
    for i in range(1, n_round):
        a = -math.pi * i / n_round
        pts.append(pt(t * math.cos(a), zr + t * math.sin(a)))
    pts += list(reversed(wall(-1.0, ztm)))
    pts.append(pt(-t / 3.0, ztr))
    pts.append(pt(t / 3.0, ztq))
    return pts


def _sweep_plate(stations):
    """stations: list of (x, yc, z_top, z_bot, t, lean[, top])."""
    rings = [_plate_ring(*s) for s in stations]
    return C.loft(rings, closed=True, cap_start=True, cap_end=True)


# --------------------------------------------------------------------------- #
# floor fences
# --------------------------------------------------------------------------- #

# y at the leading edge, run length, outboard drift, bottom z at the front,
# bottom z growth, lean (deg), thickness
#
# D-fd-R2-03: zb0/zb1 used to run 0.0120..0.0300, i.e. the fences hung as much
# as 28 mm BELOW the plank underside - with the tyres on the ground the car
# would have been standing on its fences. Every value is re-datumed +29 mm so
# the deepest fence bottoms out at Z_LOW, and _build_fences clamps as well.
FENCES = [
    dict(y0=0.2850, length=0.4300, drift=0.0450, zb0=0.0485, zb1=0.0590,
         lean=7.0, t=0.0046, xoff=0.0360),
    dict(y0=0.4450, length=0.4600, drift=0.0620, zb0=0.0450, zb1=0.0575,
         lean=10.0, t=0.0044, xoff=0.0400),
    dict(y0=0.6050, length=0.4200, drift=0.0560, zb0=0.0425, zb1=0.0545,
         lean=13.0, t=0.0042, xoff=0.0120),
    dict(y0=0.7600, length=0.3300, drift=0.0380, zb0=0.0410, zb1=0.0525,
         lean=16.0, t=0.0040, xoff=0.0100),
]


def _build_fences(coll):
    acc = _Acc()
    for spec in FENCES:
        xf = _le_x(spec["y0"]) - spec["xoff"]
        xr = xf - spec["length"]
        n = 54
        stations = []
        for i in range(n):
            s = i / (n - 1)
            x = C.lerp(xf, xr, s)
            yc = spec["y0"] + spec["drift"] * s ** 1.25
            st = _St(x)
            tf = _root_top(st, yc, 0.0035)
            z_top = tf(0.0)
            zb = C.lerp(spec["zb0"], spec["zb1"], C.smoothstep(s))
            # D-fd-04: fading the last 30 % of the depth into the floor drew a
            # long tapered claw. A real fence keeps its depth and stops at a
            # defined vertical trailing edge; only the last few mm round off.
            if s > 0.93:
                zb = C.lerp(zb, zb + 0.0075, (s - 0.93) / 0.07)
            # never below the plank datum, and never so shallow that the plate
            # degenerates - fence 3 lives right out on the rim where the floor
            # underside is only ~16 mm clear of the plank plane.
            zb = max(Z_LOW, min(zb, z_top - 0.0075))
            # round the leading and trailing edges in plan
            taper = min(1.0, (s / 0.050) ** 0.5 if s < 0.050 else 1.0)
            taper = min(taper, 1.0 if s < 0.955 else
                        max(0.30, ((1.0 - s) / 0.045) ** 0.6))
            t = max(0.0007, spec["t"] * taper)
            stations.append((x, yc, z_top, zb, t,
                             math.radians(spec["lean"]), tf))
        v, f = _sweep_plate(stations)
        acc.add(v, f)
        acc.add_mirrored(v, f)
    return acc.emit(P + "Fences", coll, FENCE_MAT, auto=42.0, merge=1e-6)


# --------------------------------------------------------------------------- #
# diffuser vanes + central keel
# --------------------------------------------------------------------------- #

# small tyre-wake deflectors on the outer floor just ahead of the rear tyre
WAKE_FINS = [
    dict(x0=-0.9200, length=0.1350, f=0.930, depth=0.0300, lean=21.0, t=0.0032),
    dict(x0=-1.0800, length=0.1250, f=0.925, depth=0.0270, lean=24.0, t=0.0031),
    dict(x0=-1.2300, length=0.1100, f=0.920, depth=0.0235, lean=27.0, t=0.0029),
]


def _build_wake_fins(coll):
    acc = _Acc()
    for spec in WAKE_FINS:
        n = 26
        stations = []
        for i in range(n):
            s = i / (n - 1)
            x = spec["x0"] - spec["length"] * s
            st = _St(x)
            yc = Y_IN + spec["f"] * (st.b - Y_IN)
            tf = _root_top(st, yc, 0.0030)
            z_top = tf(0.0)
            # raked front, square trailing edge
            d = spec["depth"] * (0.30 + 0.70 * C.smoothstep(min(1.0, s / 0.42)))
            # D-fd-R2-03: out at f ~ 0.92 the floor underside is only ~26 mm
            # above the plank plane, so the full 30 mm rake reached 2.8 mm
            # below the ride-height datum.
            z_bot = max(z_top - d, Z_LOW)
            t = spec["t"]
            if s < 0.10:
                t *= max(0.30, (s / 0.10) ** 0.5)
            elif s > 0.94:
                t *= max(0.32, ((1.0 - s) / 0.06) ** 0.6)
            stations.append((x, yc, z_top, z_bot, t,
                             math.radians(spec["lean"]), tf))
        v, f = _sweep_plate(stations)
        acc.add(v, f)
        acc.add_mirrored(v, f)
    return acc.emit(P + "WakeFins", coll, "CarbonFibre", auto=40.0, merge=1e-6)


VANES = [
    dict(y0=0.1700, x0=-1.3950, drift=0.0300, zb0=0.0512, zb1=0.0930,
         lean=3.0, t=0.0038),
    dict(y0=0.2800, x0=-1.4050, drift=0.0420, zb0=0.0530, zb1=0.0975,
         lean=5.0, t=0.0038),
    dict(y0=0.3850, x0=-1.3900, drift=0.0480, zb0=0.0560, zb1=0.1020,
         lean=8.0, t=0.0036),
    dict(y0=0.4700, x0=-1.3400, drift=0.0400, zb0=0.0625, zb1=0.1075,
         lean=11.0, t=0.0034),
]

# --------------------------------------------------------------------------- #
# suspension clearance slots through the vanes
# --------------------------------------------------------------------------- #

# D-fd-R3-01: the rear wishbone legs and the toe link cross the diffuser tunnel
# between y = 0.25 and y = 0.46 at z = 0.202..0.266 - straight through
# separator vanes 0, 1 and 2 (measured 1471 arm/vane intersecting triangle
# pairs, 135 more than the round before because suspension_rear dropped its
# arms ~10 mm).
#
# A vane cannot be moved out of the way. Its root IS the tunnel roof, so
# lowering it unbonds the vane and opens a slot into the floor; its bottom edge
# is already 100-140 mm BELOW the arms, so deepening it only adds plate to the
# arm's path; and the crossings are spread over 400 mm of a 830 mm vane, so it
# cannot be shortened either. What a real floor does where a link has to pass
# through a fence is cut a passage and close the laminate round it. These are
# those passages: one window per crossing, the laminate continuous above,
# below, fore and aft of every one.
#
# Each entry is a MEASURED arm envelope in the vane's own plane - BVH
# nearest-surface plus a parity inside test against suspension_rear_RL_Arms,
# sampled on a 2 mm grid across the full plate thickness - and the cut is that
# box grown by SLOT_CLEAR with SLOT_R corners. `pierce` marks the one crossing
# where the leg leaves the tunnel THROUGH the roof: there the vane's root is
# inside the arm, so the window has to run past the root instead of stopping
# SLOT_LAND short of it.
SLOT_CLEAR = 0.0050              # laminate-to-arm gap the window is cut for
SLOT_LAND = 0.0100               # min plate left between window and vane root
SLOT_R = 0.0080                  # window corner radius

VANE_SLOTS = (
    # toe link, just ahead of its inboard rod end
    dict(v=0, x=(-2.2010, -2.1690), z=(0.2240, 0.2480)),
    # rear leg + pushrod: two crossings 16 mm apart in z, cut as ONE window -
    # separate ones would leave a 6 mm sliver of plate between them
    dict(v=1, x=(-2.1290, -2.0530), z=(0.2020, 0.2660)),
    # front leg
    dict(v=1, x=(-1.9130, -1.8790), z=(0.2060, 0.2360)),
    # rear leg, running nearly parallel to the roof out here
    dict(v=2, x=(-2.0720, -1.9560), z=(0.2320, 0.2560)),
    # ... and climbing out through it: the arm's upper surface is at 0.283,
    # 4 mm ABOVE the top of the vane's own root flare, so over these 58 mm
    # there is no laminate to leave. Overlaps the window above so the two cut
    # as one opening rather than leaving a 4 mm rib between them.
    dict(v=2, x=(-2.0360, -1.9780), z=(0.2500, 0.2830), pierce=True),
    # front leg
    dict(v=2, x=(-1.8940, -1.8060), z=(0.2300, 0.2540)),
)


def _vane_root_z(spec, x):
    """z of the vane's bonded root (its top) at station x."""
    return _root_top(_St(x), _vane_yc(spec, x), 0.0035)(0.0)


def _slot_outline(x0, x1, z0, z1, r, n=7):
    """Closed rounded-rectangle outline in the (x, z) plane."""
    r = max(1e-4, min(r, 0.5 * min(x1 - x0, z1 - z0) - 1e-4))
    out = []
    for (cx, cz, a0) in ((x1 - r, z1 - r, 0.00), (x0 + r, z1 - r, 0.25),
                         (x0 + r, z0 + r, 0.50), (x1 - r, z0 + r, 0.75)):
        for i in range(n + 1):
            a = C.TAU * (a0 + 0.25 * i / n)
            out.append((cx + r * math.cos(a), cz + r * math.sin(a)))
    return out


def _slot_cutter(acc, spec, x0, x1, z0, z1, half_y=0.0300):
    """Prism that punches one window through a vane, and through its mirror.

    Swept along y, centred on the plate itself: a leaning plate is displaced
    (root - z) * tan(lean) from its own centreline at the window's height, and
    half_y (30 mm) then covers the drift across the window while still leaving
    at least 45 mm to the next vane, so no cutter touches a vane it is not for.
    """
    xm, zm = 0.5 * (x0 + x1), 0.5 * (z0 + z1)
    yp = (_vane_yc(spec, xm)
          + (_vane_root_z(spec, xm) - zm) * math.tan(math.radians(spec["lean"])))
    ring = _slot_outline(x0, x1, z0, z1, SLOT_R)
    v, f = C.loft([[(x, yp - half_y, z) for (x, z) in ring],
                   [(x, yp + half_y, z) for (x, z) in ring]],
                  closed=True, cap_start=True, cap_end=True)
    acc.add(v, f)
    acc.add_mirrored(v, f)


def _build_vane_slots(ob, coll):
    """Cut every VANE_SLOTS window out of the emitted vane mesh.

    Two passes, because a pierce window deliberately overlaps the window above
    it: handing the exact solver ONE cutter that intersects itself made it
    subtract the whole of vane 2 (measured - all 3627 verts of the vane and
    every triangle of it gone from the result) instead of cutting two
    openings. Each pass therefore carries only disjoint solids.
    """
    for pierce in (False, True):
        cut = _Acc()
        for slot in VANE_SLOTS:
            if bool(slot.get("pierce")) != pierce:
                continue
            spec = VANES[slot["v"]]
            (xa, xb), (za, zb) = slot["x"], slot["z"]
            x0, x1 = xa - SLOT_CLEAR, xb + SLOT_CLEAR
            roofs = [_vane_root_z(spec, C.lerp(x0, x1, i / 8.0))
                     for i in range(9)]
            if pierce:
                # right through the root and 12 mm past it, so no sliver of the
                # flared root is left standing inside the arm
                z_top = max(zb + SLOT_CLEAR, max(roofs) + 0.0120)
            else:
                # never take the window closer than SLOT_LAND to the root: out
                # at vane 2 the leg runs only 13 mm under the roof, and a full
                # 5 mm clearance there would leave an 8 mm ribbon of laminate
                # carrying a 126 mm window.
                z_top = min(zb + SLOT_CLEAR, min(roofs) - SLOT_LAND)
            _slot_cutter(cut, spec, x0, x1, za - SLOT_CLEAR, z_top)
        if cut.f:
            _apply_boolean(ob, cut, coll,
                           "vaneslot_pierce" if pierce else "vaneslot")
    return ob


def _build_vanes(coll):
    acc = _Acc()
    for spec in VANES:
        x0, x1 = spec["x0"], X_EXIT + 0.0020
        n = 76
        stations = []
        for i in range(n):
            s = i / (n - 1)
            x = C.lerp(x0, x1, s)
            yc = spec["y0"] + spec["drift"] * s ** 1.4
            st = _St(x)
            tf = _root_top(st, yc, 0.0035)
            z_top = tf(0.0)
            zb = C.lerp(spec["zb0"], spec["zb1"], s ** 0.85)
            # raked leading edge: the vane grows out of the diffuser roof over
            # its first ~220 mm instead of appearing as a 150 mm deep slab
            zb = max(zb, z_top - C.lerp(0.014, 0.420,
                                        C.smoothstep(min(1.0, s / 0.28))))
            taper = 1.0
            if s < 0.05:
                taper = max(0.20, (s / 0.05) ** 0.5)
            elif s > 0.985:
                taper = max(0.30, ((1.0 - s) / 0.015) ** 0.5)
            t = max(0.0008, spec["t"] * taper)
            stations.append((x, yc, z_top, zb, t,
                             math.radians(spec["lean"]), tf))
        v, f = _sweep_plate(stations)
        acc.add(v, f)
        acc.add_mirrored(v, f)

    # central keel
    n = 72
    stations = []
    for i in range(n):
        s = i / (n - 1)
        x = C.lerp(-1.4450, X_EXIT + 0.0020, s)
        st = _St(x)
        tf = _root_top(st, 0.0, 0.0040)
        z_top = tf(0.0)
        zb = C.lerp(0.0415, 0.1060, s ** 0.80)
        zb = max(zb, z_top - C.lerp(0.016, 0.300,
                                    C.smoothstep(min(1.0, s / 0.30))))
        t = C.lerp(0.0130, 0.0100, s)
        if s < 0.05:
            t *= max(0.22, (s / 0.05) ** 0.5)
        elif s > 0.985:
            t *= max(0.35, ((1.0 - s) / 0.015) ** 0.5)
        stations.append((x, 0.0, z_top, zb, t, 0.0, tf))
    v, f = _sweep_plate(stations)
    acc.add(v, f)

    ob = C.new_obj(P + "DiffuserVanes", acc.v, acc.f, coll=coll, smooth=True)
    C.merge_doubles(ob, 1e-6)
    _build_vane_slots(ob, coll)
    C.merge_doubles(ob, 1e-6)
    C.shade_auto_smooth(ob, 42.0)
    S.assign(ob, "CarbonMatte")
    return ob


# --------------------------------------------------------------------------- #
# floor edge wing
# --------------------------------------------------------------------------- #

EW_XF = 1.0250
EW_XR = -1.3050
_EW_CAMBER_RAW = [(-0.0240, 0.0072), (-0.0140, 0.0050), (-0.0055, 0.0020),
                  (0.0025, -0.0028), (0.0105, -0.0092), (0.0180, -0.0150),
                  (0.0250, -0.0188), (0.0300, -0.0180), (0.0316, -0.0130),
                  (0.0296, -0.0072), (0.0236, -0.0038)]

# D-fd-R2-03: the hook bottomed out 21 mm under the floor rim, which put the
# edge wing 9.7 mm BELOW the plank underside - the ride-height datum. The
# floor rim itself sits only 11.5 mm above that plane, so the hook has to be
# shallower. Scaling the section vertically about its root keeps the shape,
# keeps the root buried exactly where it was in the rim laminate, and lifts
# the lowest point clear of the plank.
EW_ZK = 0.560
_EW_ZROOT = _EW_CAMBER_RAW[0][1]
EW_CAMBER = [(dy, _EW_ZROOT + (dz - _EW_ZROOT) * EW_ZK)
             for (dy, dz) in _EW_CAMBER_RAW]


def _plate_loop(cam, hw, tip_round=6):
    """Closed section loop from a camber polyline, thickness 2*hw, rounded tip."""
    n = len(cam)
    nrm = []
    for i in range(n):
        a = cam[max(0, i - 1)]
        b = cam[min(n - 1, i + 1)]
        d = Vector((b[0] - a[0], b[1] - a[1]))
        if d.length < 1e-9:
            d = Vector((1.0, 0.0))
        d.normalize()
        nrm.append((-d[1], d[0]))
    up = [(cam[i][0] + hw * nrm[i][0], cam[i][1] + hw * nrm[i][1])
          for i in range(n)]
    dn = [(cam[i][0] - hw * nrm[i][0], cam[i][1] - hw * nrm[i][1])
          for i in range(n)]
    loop = list(up)
    tx, ty = cam[-1]
    a0 = math.atan2(nrm[-1][1], nrm[-1][0])
    for i in range(1, tip_round):
        a = a0 - math.pi * i / tip_round
        loop.append((tx + hw * math.cos(a), ty + hw * math.sin(a)))
    loop += list(reversed(dn))
    return loop


def _build_edge_wing(coll):
    acc = _Acc()
    n = 208
    rings = []
    for i in range(n):
        s = i / (n - 1)
        x = C.lerp(EW_XF, EW_XR, s)
        st = _St(x)
        fade = 1.0
        if s < 0.090:
            fade = 0.02 + 0.98 * C.smoothstep(s / 0.090)
        elif s > 0.910:
            fade = 0.02 + 0.98 * C.smoothstep((1.0 - s) / 0.090)
        # slow spanwise wave in the lip, ~0.31 m period - the real thing is
        # never a perfectly straight extrusion
        wav = 1.0 + 0.050 * math.sin(x * (2.0 * math.pi / 0.310) + 0.7)
        # D-fd-02: fading the whole section about the rim left a 5 mm hook
        # dangling in mid air at each end. Fade toward the root point instead,
        # so the wing melts back into the floor rim it grows out of.
        root = EW_CAMBER[0]
        cam = [(root[0] + (dy * wav - root[0]) * fade,
                root[1] + (dz - root[1]) * fade)
               for (dy, dz) in C.catmull_rom(EW_CAMBER, 26)]
        loop = _plate_loop(cam, 0.0022 * (0.45 + 0.55 * fade))
        y0 = st.w
        z0 = st.ze + 0.5 * TSEC(1.0) * (1.0 - st.k)
        rings.append([(x, y0 + dy, z0 + dz) for (dy, dz) in loop])
    v, f = C.loft(rings, closed=True, cap_start=True, cap_end=True)
    acc.add(v, f)
    acc.add_mirrored(v, f)
    return acc.emit(P + "EdgeWing", coll, "CarbonFibre", auto=40.0, merge=1e-6)


# --------------------------------------------------------------------------- #
# fasteners
# --------------------------------------------------------------------------- #

def _frame(n, spin):
    n = Vector(n).normalized()
    ref = Vector((1.0, 0.0, 0.0))
    if abs(n.dot(ref)) > 0.9:
        ref = Vector((0.0, 1.0, 0.0))
    t = (ref - n * ref.dot(n)).normalized()
    b = n.cross(t)
    ca, sa = math.cos(spin), math.sin(spin)
    return t * ca + b * sa, -t * sa + b * ca, n


def _csk_fastener(acc, origin, normal, spin, r_head=0.0056, r_sock=0.0021,
                  d_head=0.0042, d_sock=0.0026, r_shank=0.0031,
                  shank=0.0110, seg=28):
    """Countersunk cap screw seated flush in a conical seat.

    Local +Z is the outward normal; the material lies at local z < 0, so the
    head face sits 0.2 mm below the surface, the cone runs deeper and the shank
    disappears into the part.
    """
    o = Vector(origin)
    u, v, w = _frame(normal, spin)

    def pt(lx, ly, lz):
        p = o + u * lx + v * ly + w * lz
        return (p.x, p.y, p.z)

    verts, faces = [], []

    def ring(pts):
        i0 = len(verts)
        verts.extend(pts)
        return i0

    circ = [(math.cos(C.TAU * i / seg), math.sin(C.TAU * i / seg))
            for i in range(seg)]
    hexs = _HEX24 if seg == 24 else circ

    r0 = ring([pt(r_head * c, r_head * s, -0.0002) for (c, s) in circ])
    r1 = ring([pt(r_sock * c, r_sock * s, -0.0002) for (c, s) in hexs])
    r2 = ring([pt(r_sock * c, r_sock * s, -0.0002 - d_sock) for (c, s) in hexs])
    r3 = ring([pt(r_shank * c, r_shank * s, -d_head) for (c, s) in circ])
    r4 = ring([pt(r_shank * c, r_shank * s, -shank) for (c, s) in circ])

    faces += _bridge(r0, r1, seg)              # flat head face
    faces += _bridge(r1, r2, seg)              # socket wall
    faces.append(tuple(range(r2, r2 + seg)))   # socket floor
    faces += _bridge(r0, r3, seg)              # countersink cone
    faces += _bridge(r3, r4, seg)              # shank
    faces.append(tuple(range(r4, r4 + seg)))
    acc.add(verts, faces)


def _strap(acc, spec, xa, xb, n=118, hw=0.0132, h=0.0021, ch=0.0038):
    """Bonded joint strap lying on the floor underside.

    A real underfloor is several bonded panels: the joints show as a proud
    strap with a fastener row down it. Without them the tunnel roof is a
    featureless half metre of carbon.
    """
    rings = []
    for i in range(n):
        x = C.lerp(xa, xb, i / (n - 1))
        st = _St(x)
        y = _strap_y(spec, x, st)
        nrm = _under_normal(x, y)
        end = 1.0
        s = i / (n - 1)
        if s < 0.03:
            end = s / 0.03
        elif s > 0.97:
            end = (1.0 - s) / 0.03
        lift = h * (0.15 + 0.85 * C.smoothstep(end))

        def onsurf(dy, up=0.0):
            zz = _under_z(x, y + dy)
            return (x + nrm.x * up, y + dy + nrm.y * up, zz + nrm.z * up)

        rings.append([onsurf(-hw), onsurf(-hw + ch, lift),
                      onsurf(hw - ch, lift), onsurf(hw)])
    v, fc = C.loft(rings, closed=True, cap_start=True, cap_end=True)
    acc.add(v, fc)
    return v, fc


def _flush_rivet(acc, x, y, spin, r=0.0042, lift=0.0, seg=24):
    """Flush titanium fastener that conforms to the curved floor surface: the
    base ring is sampled ON the surface, everything above is offset along the
    local normal, so there is neither a gap nor a sunk rim."""
    z = _under_z(x, y)
    n = _under_normal(x, y)
    u, v, w = _frame(n, spin)
    o = Vector((x, y, z))

    verts, faces = [], []
    rise = lift

    def ring_at(rad, lift, shape):
        i0 = len(verts)
        for (c, s) in shape:
            p = o + u * (rad * c) + v * (rad * s)
            zz = _under_z(p.x, p.y)
            base = Vector((p.x, p.y, zz))
            q = base + w * (lift + rise)
            verts.append((q.x, q.y, q.z))
        return i0

    circ = [(math.cos(C.TAU * i / seg), math.sin(C.TAU * i / seg))
            for i in range(seg)]
    r0 = ring_at(r, 0.00012, circ)
    r1 = ring_at(r * 0.955, 0.00065, circ)
    r2 = ring_at(r * 0.780, 0.00085, circ)
    r3 = ring_at(r * 0.330, 0.00085, _HEX24)
    r4 = ring_at(r * 0.330, 0.00030, _HEX24)
    faces += _bridge(r0, r1, seg)
    faces += _bridge(r1, r2, seg)
    faces += _bridge(r2, r3, seg)
    faces += _bridge(r3, r4, seg)
    faces.append(tuple(range(r4, r4 + seg)))
    faces.append(tuple(range(r0 + seg - 1, r0 - 1, -1)))
    acc.add(verts, faces)


def _spin(i):
    return (i * 2.399963) % C.TAU


def _vane_yc(spec, x):
    """Centreline y of a diffuser vane at station x (clamped to its run)."""
    x0, x1 = spec["x0"], X_EXIT + 0.0020
    s = min(1.0, max(0.0, (x - x0) / (x1 - x0)))
    return spec["y0"] + spec["drift"] * s ** 1.4


def _diffuser_channel_y(x):
    """Mid-channel between diffuser vanes 0 and 1.

    D-fd-R2-01: this strap used to run at a constant fraction (f = 0.400) of
    the local half width. The floor plan narrows toward the exit while the
    vanes drift outboard, so the two crossed at x = -1.82 and from there back
    the 26.4 mm strap band and its whole flush-rivet row ran straight THROUGH
    vane 1 (1098 strap and 243 rivet triangle pairs intersecting it). Tracking
    the vanes instead keeps the strap in the channel it is meant to be in, with
    ~55 mm of clear floor either side of it all the way to the trailing edge.
    """
    return 0.5 * (_vane_yc(VANES[0], x) + _vane_yc(VANES[1], x))


STRAPS = [dict(f=0.155, xa=1.3050, xb=-1.2000),
          dict(f=0.855, xa=1.1200, xb=-1.1800),
          dict(yfun=_diffuser_channel_y, xa=-1.3000, xb=-2.1700)]


def _strap_y(spec, x, st):
    yf = spec.get("yfun")
    return yf(x) if yf is not None else Y_IN + spec["f"] * (st.b - Y_IN)


def _build_straps(coll):
    acc = _Acc()
    for spec in STRAPS:
        v, fc = _strap(acc, spec, spec["xa"], spec["xb"])
        acc.add_mirrored(v, fc)
    return acc.emit(P + "JointStraps", coll, "CarbonMatte", auto=34.0)


def _build_floor_rivets(coll):
    acc = _Acc()
    idx = 0
    for spec in STRAPS:
        xa, xb = spec["xa"], spec["xb"]
        pitch = 0.0960
        n = max(2, int(round((xa - xb) / pitch)))
        for i in range(n + 1):
            x = xa - (xa - xb) * i / n
            if i == 0 or i == n:
                x += 0.0130 * (1 if i == 0 else -1)
            st = _St(x)
            y = _strap_y(spec, x, st)
            _flush_rivet(acc, x, y, _spin(idx), lift=0.0021)
            idx += 1
    # sparser rows off the straps: outer floor and the tunnel roof crown
    for (f, xa, xb, pitch) in ((0.965, 0.980, -1.120, 0.1450),
                               (0.560, 1.150, -1.150, 0.1900)):
        n = int(round((xa - xb) / pitch))
        for i in range(n + 1):
            x = xa - (xa - xb) * i / n
            st = _St(x)
            y = Y_IN + f * (st.b - Y_IN)
            _flush_rivet(acc, x, y, _spin(idx), r=0.0034)
            idx += 1
    v, fc = list(acc.v), list(acc.f)
    acc.add_mirrored(v, fc)
    ob = acc.emit(P + "FloorRivets", coll, "Titanium", auto=32.0)
    C.add_bevel(ob, width=0.00016, segments=2, angle=32.0)
    return ob


# --------------------------------------------------------------------------- #
# plank, skid blocks, countersunk fasteners
# --------------------------------------------------------------------------- #

SKID_X = (1.1200, 0.2800, -0.6000, -1.2800)
SKID_Y = 0.0860
SKID_HX = 0.0650
SKID_HY = 0.0340
SKID_TOP = 0.0480
SKID_BOT = 0.0389
WEAR_X = (0.9800, -0.1000, -1.1500)
WEAR_R = 0.0250


def _prism(acc, x0, x1, y0, y1, z0, z1):
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
         (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    acc.add(v, f)


def _revolve_solid(acc, profile, cx, cy, seg=28):
    """profile: list of (r, z) starting and ending at r = 0."""
    verts, faces = [], []
    rings = []
    for (r, z) in profile:
        if r <= 1e-6:
            verts.append((cx, cy, z))
            rings.append((len(verts) - 1, True))
        else:
            i0 = len(verts)
            for i in range(seg):
                a = C.TAU * i / seg
                verts.append((cx + r * math.cos(a), cy + r * math.sin(a), z))
            rings.append((i0, False))
    for k in range(len(rings) - 1):
        (a, pa), (b, pb) = rings[k], rings[k + 1]
        if pa and pb:
            continue
        if pa:
            for j in range(seg):
                faces.append((a, b + j, b + (j + 1) % seg))
        elif pb:
            for j in range(seg):
                faces.append((b, a + (j + 1) % seg, a + j))
        else:
            faces += _bridge(a, b, seg)
    acc.add(verts, faces)


def _fastener_sites():
    """(x, y) of every countersunk fastener in the plank."""
    sites = []
    n = 21
    for i in range(n):
        x = C.lerp(1.3400, -1.3800, i / (n - 1))
        sites.append((x, 0.1315))
        sites.append((x, -0.1315))
    m = 14
    for i in range(m):
        x = C.lerp(1.2800, -1.3200, i / (m - 1))
        sites.append((x, 0.0380))
        sites.append((x, -0.0380))
    return sites


def _skid_bolt_sites():
    """Bolts that hold the titanium skids into the plank. They seat in the
    skid's own face, not the plank's - putting them at plank level buried the
    heads inside the block (D-fd-03)."""
    sites = []
    for sx in SKID_X:
        for sy in (SKID_Y, -SKID_Y):
            sites.append((sx - 0.0430, sy))
            sites.append((sx + 0.0430, sy))
    return sites


def _apply_boolean(ob, cutter_acc, coll, tag):
    """Difference `cutter_acc` out of `ob` and bake the result into its mesh."""
    cutter = C.new_obj(P + "_cut_" + tag, cutter_acc.v, cutter_acc.f,
                       coll=coll, smooth=False)
    try:
        m = ob.modifiers.new("csk", "BOOLEAN")
        m.object = cutter
        m.operation = "DIFFERENCE"
        m.solver = "EXACT"
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
        ob.modifiers.remove(m)
        old = ob.data
        ob.data = me
        if old.users == 0:
            bpy.data.meshes.remove(old)
    except Exception as exc:                      # pragma: no cover
        print(f"!! {NAME}: {tag} boolean failed ({exc}) - left plain")
        for mod in list(ob.modifiers):
            ob.modifiers.remove(mod)
    finally:
        cd = cutter.data
        bpy.data.objects.remove(cutter, do_unlink=True)
        if cd.users == 0:
            bpy.data.meshes.remove(cd)
    return ob


def _csk_seat(cut, fx, fy, z_face, r_top=0.0058, r_hole=0.0032, depth=0.0044,
              thru=0.0120, seg=28):
    _revolve_solid(cut, [(0.0, z_face - 0.0020),
                         (r_top, z_face - 0.0020),
                         (r_top, z_face + 0.0001),
                         (r_hole, z_face + depth),
                         (r_hole, z_face + thru),
                         (0.0, z_face + thru)], fx, fy, seg=seg)


def _build_plank(coll):
    made = []

    # --- slab ------------------------------------------------------------- #
    acc = _Acc()
    _prism(acc, PLANK_XR, PLANK_XF, -PLANK_HW, PLANK_HW, Z_PLANK, PLANK_TOP)
    ob = C.new_obj(P + "Plank", acc.v, acc.f, coll=coll, smooth=False)

    # --- cutter: skid pockets, wear holes, countersinks -------------------- #
    cut = _Acc()
    for sx in SKID_X:
        for sy in (SKID_Y, -SKID_Y):
            _prism(cut, sx - SKID_HX - 0.0005, sx + SKID_HX + 0.0005,
                   sy - SKID_HY - 0.0005, sy + SKID_HY + 0.0005,
                   Z_PLANK - 0.0030, SKID_TOP + 0.0002)
    for wx in WEAR_X:
        _revolve_solid(cut, [(0.0, Z_PLANK - 0.0030),
                             (WEAR_R, Z_PLANK - 0.0030),
                             (WEAR_R, Z_PLANK + 0.0012),
                             (WEAR_R - 0.0012, Z_PLANK + 0.0024),
                             (WEAR_R - 0.0012, PLANK_TOP + 0.0030),
                             (0.0, PLANK_TOP + 0.0030)], wx, 0.0, seg=40)
    for (fx, fy) in _fastener_sites():
        _csk_seat(cut, fx, fy, Z_PLANK, thru=PLANK_TOP + 0.0020 - Z_PLANK)
    _apply_boolean(ob, cut, coll, "plank")

    C.merge_doubles(ob, 1e-6)
    C.shade_auto_smooth(ob, 24.0)
    S.assign(ob, "CarbonCeramic")
    C.add_bevel(ob, width=0.0011, segments=2, angle=28.0)
    made.append(ob)

    # --- titanium skid blocks --------------------------------------------- #
    acc = _Acc()
    for sx in SKID_X:
        for sy in (SKID_Y, -SKID_Y):
            _prism(acc, sx - SKID_HX, sx + SKID_HX, sy - SKID_HY, sy + SKID_HY,
                   SKID_BOT, SKID_TOP)
    sk = C.new_obj(P + "Skids", acc.v, acc.f, coll=coll, smooth=False)
    cut = _Acc()
    for (fx, fy) in _skid_bolt_sites():
        _csk_seat(cut, fx, fy, SKID_BOT, r_top=0.0048, r_hole=0.0026,
                  depth=0.0036, thru=0.0140, seg=24)
    _apply_boolean(sk, cut, coll, "skid")
    C.merge_doubles(sk, 1e-6)
    C.shade_auto_smooth(sk, 26.0)
    S.assign(sk, "Titanium")
    C.add_bevel(sk, width=0.0016, segments=3, angle=30.0)
    made.append(sk)

    # --- countersunk heads ------------------------------------------------- #
    acc = _Acc()
    for i, (fx, fy) in enumerate(_fastener_sites()):
        _csk_fastener(acc, (fx, fy, Z_PLANK), (0.0, 0.0, -1.0), _spin(i))
    for i, (fx, fy) in enumerate(_skid_bolt_sites()):
        _csk_fastener(acc, (fx, fy, SKID_BOT), (0.0, 0.0, -1.0), _spin(i + 7),
                      r_head=0.0046, r_sock=0.0018, d_head=0.0035,
                      d_sock=0.0022, r_shank=0.0026, shank=0.0140)
    fs = acc.emit(P + "PlankBolts", coll, "SteelFastener", auto=30.0)
    C.add_bevel(fs, width=0.00018, segments=2, angle=30.0)
    made.append(fs)
    return made


# --------------------------------------------------------------------------- #

def build(coll, ctx=None):
    made = []
    made.append(_build_shell(coll))
    made.append(_build_fences(coll))
    made.append(_build_vanes(coll))
    made.append(_build_edge_wing(coll))
    made.append(_build_wake_fins(coll))
    made.append(_build_straps(coll))
    made.append(_build_floor_rivets(coll))
    made += _build_plank(coll)
    return made
