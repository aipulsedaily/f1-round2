"""suspension_rear - both rear corners, gearbox pickups to upright.

What is here
------------
Per corner (RL / RR), authored on the LEFT and mirrored with a determinant-+1
transform so no object ever carries negative scale:

  * upper and lower wishbones - two aerofoil-faired carbon legs joined by a
    moulded web near the outboard end, so each pair reads as one wishbone with
    a narrow outboard base and a wide gearbox-side base.
  * toe link and pushrod, same construction.
  * every link end is a real rod end: a swaged race with a spherical seat, a
    barrel ball visible through the race opening, a rolled thread on the shank
    and an anodised jam nut. Inboard ends get the clevis, through-bolt and
    nyloc as well.
  * gearbox-side pickup brackets: a machined pad that CONFORMS to the body
    skin - every grid point, top AND underside, resampled off the real station
    profile and then bedded 1.4 mm into it, so there is no daylight anywhere
    round the joint - four cap screws, a web, two clevis cheeks.
  * pushrod rocker: a two-plate bellcrank on a torsion-bar boss, with the ARB
    drop link on its second arm, the ARB blade and its casing seal boot.
  * driveshaft: inboard tripod housing, both convoluted CV boots with band
    clamps, and the outboard joint running through the upright bore into
    brake_assembly's hub. It is ONE continuous shaft: the bar telescopes 30 mm
    into the tripod housing at one end and 30 mm into the outboard CV at the
    other, and the CV's spigot is an interference fit in the 36 mm hub bore.

Interfaces this module is built against
---------------------------------------
brake_assembly owns the upright, and therefore the outboard pickups. Its
LUGS_REAR table puts fore/aft clevis pairs on a common pin axis, so each
wishbone gets a wide outboard base:

    upper  r=0.108  th=70/110 deg  ax=-0.024      pin +X
    lower  r=0.104  th=250/290     ax=-0.020      pin +X
    toe    r=0.100  th=200         ax=-0.036      pin +Z

ax is measured OUTBOARD from the hub face at
(-1.80, +-(REAR_TYRE_Y - UPRIGHT_Y_INSET), TYRE_R). Its clevis cheeks start
13.2 mm from the pin centre, so a rod end has to be under 26 mm wide; its ball
is an 18.4 mm barrel, so the ball here (a 30 mm sphere truncated flat at
+-11.2 mm, i.e. 23.2 mm wide) completely encloses it and no two surfaces ever
end up coincident. The outboard through-bolt drawn here is likewise smaller
than theirs and lives entirely inside it.

The brake drum's inboard bulkhead sits at ax = -0.115 and only passes a leg
through a 20 deg x 64 mm slot centred on each lug. Every leg therefore leaves
the upright RADIALLY as a bare 28 mm shank and only opens into its aerofoil
fairing once it is clear of the duct.
"""

import math

import bpy
from mathutils import Matrix, Vector

import common as C
import spec as S

NAME = "suspension_rear"
TAU = math.pi * 2.0

# --------------------------------------------------------------------------- #
# hard points (LEFT corner, world metres)
# --------------------------------------------------------------------------- #

HUB_X = S.REAR_AXLE                              # -1.800
HUB_Y = S.REAR_TYRE_Y - S.UPRIGHT_Y_INSET        #  0.7125
HUB_Z = S.TYRE_R                                 #  0.360
BULK_AX = -0.115                                 # brake-duct bulkhead plane


def _lug(deg, r, ax):
    """A point in the corner-local cylindrical frame brake_assembly uses."""
    th = math.radians(deg)
    return Vector((HUB_X + r * math.cos(th), HUB_Y + ax, HUB_Z + r * math.sin(th)))


UF = _lug(70.0, 0.108, -0.024)      # upper wishbone, front leg
UR = _lug(110.0, 0.108, -0.024)     # upper wishbone, rear leg
LF = _lug(290.0, 0.104, -0.020)     # lower wishbone, front leg
LR = _lug(250.0, 0.104, -0.020)     # lower wishbone, rear leg
TO = _lug(200.0, 0.100, -0.036)     # toe link

# where each leg crosses the duct bulkhead - dead centre of its slot
W_UF = _lug(70.0, 0.104, BULK_AX)
W_UR = _lug(110.0, 0.104, BULK_AX)
W_LF = _lug(290.0, 0.100, BULK_AX)
W_LR = _lug(250.0, 0.100, BULK_AX)
W_TO = _lug(200.0, 0.104, BULK_AX)

# Gearbox-side hard points are NOT free-typed coordinates: each one is a
# station x, a height z on the skin and a stand-off along the skin's own
# outward normal. That is what guarantees the bracket pad lands on the body and
# the clevis never sinks into it, whatever the section shape does.
#   (x, z_on_skin, normal_stand_off)
PICKS = {
    "uf": (-1.890, 0.402, 0.040),
    "ur": (-2.150, 0.300, 0.042),
    "lf": (-1.900, 0.232, 0.042),
    "lr": (-2.095, 0.208, 0.046),
    "to": (-2.215, 0.230, 0.040),
    "rk": (-1.980, 0.395, 0.038),
}

ROCK_PAD_Z = 0.358        # rocker pedestal pad, well below the pivot

ROCK_HALF = 0.018                           # plate inner face offset in x
ROCK_T = 0.0110                             # plate thickness

ARB_X = -2.055
ARB_Z = 0.300
ARB_TIP_X = -2.020
ARB_TIP_Z = 0.245
ARB_STAND = 0.030                           # blade plane, off the skin

SHAFT_X = HUB_X
SHAFT_Z = HUB_Z

PUSH_FOOT_Y = 0.520
PUSH_FOOT_RISE = 0.030   # pushrod clevis sits ON TOP of the wishbone leg

# --------------------------------------------------------------------------- #
# rod-end / fastener dimensions
# --------------------------------------------------------------------------- #

# The race opening has to show the ball - a rod end whose bore reads as a black
# dot is the classic tell of a modelled-not-engineered joint. Widening the ball
# to 30 mm and holding the race to 23.2 mm (still inside brake_assembly's
# 26.4 mm clevis gap) opens the bore to 20 mm, i.e. half the race OD, which is
# what a real spherical bearing looks like.
BALL_R = 0.0150       # bearing ball sphere radius
BALL_H = 0.0112       # ball truncated flat at this half height
SEAT_R = 0.0154       # spherical seat in the race
EYE_R = 0.0202        # race outside radius
EYE_W = 0.0232        # race width
NECK_R = 0.0104
THR_R = 0.0092
THR_H0 = 0.0205
THR_H1 = 0.0462
JAM_AF = 0.0258
JAM_H = 0.0120
JAM_H0 = 0.0332
SOCK_R = 0.0140       # arm end socket the shank screws into
SOCK_H = 0.0455       # pin centre -> socket face, at k=1
TOE_K = 0.86          # rod-end scale on the toe link (smaller hardware)

BOLT_R = 0.0052       # brake_assembly's through-bolt shank
CHEEK_IN = 0.0128     # clevis cheek inner face, from the pin centre
CHEEK_T = 0.0056


# --------------------------------------------------------------------------- #
# mesh accumulator
# --------------------------------------------------------------------------- #

class _M:
    __slots__ = ("v", "f")

    def __init__(self):
        self.v = []
        self.f = []

    def ring(self, pts):
        i0 = len(self.v)
        self.v.extend((float(p[0]), float(p[1]), float(p[2])) for p in pts)
        return list(range(i0, len(self.v)))

    def bridge(self, A, B, closed=True):
        n = len(A)
        for i in range(n if closed else n - 1):
            j = (i + 1) % n
            self.f.append((A[i], A[j], B[j], B[i]))

    def tube(self, rings, closed=True, cap0=True, cap1=True, loop=False):
        idx = [self.ring(r) for r in rings]
        pairs = list(zip(idx, idx[1:]))
        if loop:
            pairs.append((idx[-1], idx[0]))
        for a, b in pairs:
            if len(a) == 1 and len(b) == 1:
                continue
            if len(a) == 1:
                for i in range(len(b)):
                    self.f.append((a[0], b[i], b[(i + 1) % len(b)]))
            elif len(b) == 1:
                for i in range(len(a)):
                    self.f.append((a[i], a[(i + 1) % len(a)], b[0]))
            else:
                self.bridge(a, b, closed)
        if not loop:
            if cap0 and len(idx[0]) > 2:
                self.f.append(tuple(reversed(idx[0])))
            if cap1 and len(idx[-1]) > 2:
                self.f.append(tuple(idx[-1]))
        return idx


def _hint(axis):
    """A reference direction guaranteed not to be parallel to `axis`."""
    a = Vector(axis).normalized()
    return (0.0, 0.0, 1.0) if abs(a.x) > 0.7 else (1.0, 0.0, 0.0)


def _basis(zdir, xhint=(1.0, 0.0, 0.0)):
    z = Vector(zdir)
    if z.length < 1e-12:
        z = Vector((0.0, 0.0, 1.0))
    z = z.normalized()
    x = Vector(xhint)
    x = x - z * x.dot(z)
    if x.length < 1e-7:
        for cand in ((0.0, 0.0, 1.0), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0)):
            x = Vector(cand) - z * Vector(cand).dot(z)
            if x.length > 1e-6:
                break
    x.normalize()
    return x, z.cross(x), z


def _spin(m, origin, axis, prof, n=44, xhint=None, cap0=True, cap1=True,
          loop=False, rfn=None):
    """Solid of revolution from a (radius, height) profile about `axis`.

    rfn(i_profile, theta) -> extra radius, for lobed or splined surfaces.
    A zero-radius profile point becomes a single pole vertex and a triangle
    fan, so caps never carry degenerate quads.
    """
    ex, ey, ez = _basis(axis, xhint or _hint(axis))
    o = Vector(origin)
    rings = []
    for k, (r, h) in enumerate(prof):
        c = o + ez * h
        # A ring is a pole only if it is zero radius AFTER rfn - otherwise a
        # lobed/hex ring written as (0, h) would collapse to n coincident
        # vertices, which tube() then bridges into a degenerate disc.
        flat = (rfn is None or
                max(abs(rfn(k, TAU * i / 12.0)) for i in range(12)) < 1e-9)
        if abs(r) < 1e-7 and flat:
            rings.append([c])
            continue
        ring = []
        for i in range(n):
            t = TAU * i / n
            rr = r + (rfn(k, t) if rfn else 0.0)
            ring.append(c + ex * (rr * math.cos(t)) + ey * (rr * math.sin(t)))
        rings.append(ring)
    return m.tube(rings, closed=True, cap0=cap0, cap1=cap1, loop=loop)


# --------------------------------------------------------------------------- #
# 2-D sections
# --------------------------------------------------------------------------- #

def _foil(chord, t_ratio, le=0.32, te_half=0.0009, nh=22, narc=3):
    """Closed symmetric NACA-style section, CCW, origin at `le` fraction chord.

    +u is forward. The trailing edge is blunted with a real radius: a razor
    edge shades as a black line and aliases badly at 4K.
    """
    def half(s):
        s = max(s, 0.0)
        return 5.0 * t_ratio * chord * (0.2969 * math.sqrt(s) - 0.1260 * s
                                        - 0.3516 * s * s + 0.2843 * s ** 3
                                        - 0.1036 * s ** 4)

    pts = []
    for i in range(nh + 1):
        s = 0.5 * (1.0 - math.cos(math.pi * i / nh))
        pts.append((chord * (le - s), half(s) + te_half * s))
    ute = chord * (le - 1.0)
    for k in range(1, narc + 1):
        b = math.pi * k / (narc + 1)
        pts.append((ute - te_half * math.sin(b), te_half * math.cos(b)))
    for i in range(nh, 0, -1):
        s = 0.5 * (1.0 - math.cos(math.pi * i / nh))
        pts.append((chord * (le - s), -(half(s) + te_half * s)))
    return pts


def _match_circle(pts, r):
    """Circle sampled at the same normalised arc-length stations as `pts`, so
    lerping between the two morphs a fairing into a round shank without any
    point sliding along the surface."""
    n = len(pts)
    d = [0.0]
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        d.append(d[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    tot = d[-1] or 1.0
    return [(r * math.cos(TAU * d[i] / tot), r * math.sin(TAU * d[i] / tot))
            for i in range(n)]


def _lerp2(a, b, t):
    return [(p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)
            for p, q in zip(a, b)]


def _offset2d(pts, d):
    n = len(pts)
    out = []
    for i in range(n):
        a, b = pts[(i - 1) % n], pts[(i + 1) % n]
        tx, ty = b[0] - a[0], b[1] - a[1]
        L = math.hypot(tx, ty) or 1.0
        out.append((pts[i][0] + ty / L * d, pts[i][1] - tx / L * d))
    return out


def _sec_half(pts, u):
    """Half height of a closed 2-D section at chord station u (0.0 outside it).

    This is what lets the moulded web leave each leg at the leg's OWN local
    thickness instead of at some nominal fraction of it.
    """
    best = 0.0
    n = len(pts)
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        if (a[0] - u) * (b[0] - u) <= 0.0 and abs(b[0] - a[0]) > 1e-12:
            t = (u - a[0]) / (b[0] - a[0])
            best = max(best, abs(a[1] + (b[1] - a[1]) * t))
    return best


def _arm_section(chord, thick, r0, r1, b0=(0.055, 0.30), b1=(0.72, 0.955),
                 nh=22, u_off=0.0):
    """Section function for a faired link: socket -> aerofoil -> socket.

    u_off slides the FAIRING (not the structural axis, and not the round end
    sockets) fore or aft. The two legs of a wishbone sit only ~70 mm apart at
    the upright, so with both fairings centred their trailing and leading edges
    end up 1 mm apart and the pair reads as one stamped plank. Biasing the front
    leg's fairing forward and the rear leg's aft opens a real 33 mm slot between
    them, which is exactly what the real parts do.
    """
    def f(t):
        t = min(max(t, 0.0), 1.0)
        k = 0.80 + 0.20 * math.sin(math.pi * t) ** 0.55
        foil = _foil(chord * k, thick / chord, nh=nh)
        rr = r0 + (r1 - r0) * t
        circ = _match_circle(foil, rr)
        blend = min(C.smoothstep((t - b0[0]) / (b0[1] - b0[0])),
                    C.smoothstep((b1[1] - t) / (b1[1] - b1[0])))
        sec = _lerp2(circ, foil, blend)
        if u_off:
            d = u_off * blend
            sec = [(u + d, v) for (u, v) in sec]
        return sec
    return f


def _sweep(m, path, sect_fn, chord_hint=(1.0, 0.0, 0.0), cap0=True, cap1=True):
    n = len(path)
    rings = []
    for i, p in enumerate(path):
        if i == 0:
            tg = Vector(path[1]) - Vector(path[0])
        elif i == n - 1:
            tg = Vector(path[-1]) - Vector(path[-2])
        else:
            tg = Vector(path[i + 1]) - Vector(path[i - 1])
        eu, ev, _ = _basis(tg, chord_hint)
        rings.append([Vector(p) + eu * u + ev * v
                      for (u, v) in sect_fn(i / (n - 1))])
    return m.tube(rings, closed=True, cap0=cap0, cap1=cap1)


def _bez(p0, p1, p2, p3, n):
    out = []
    for i in range(n):
        u = i / (n - 1)
        w = 1.0 - u
        out.append(Vector(p0) * (w ** 3) + Vector(p1) * (3 * w * w * u)
                   + Vector(p2) * (3 * w * u * u) + Vector(p3) * (u ** 3))
    return out


def _shank_dir(v, pin):
    """Direction a rod-end shank can actually point.

    A rod end's rolled thread is perpendicular to its ball bore, so it can only
    ever leave the joint in the plane normal to the pin. _rod_end enforces that
    by projecting whatever direction it is handed; ANY other consumer of the
    same joint has to use this identical projection or the two drift apart.
    """
    a = Vector(pin).normalized()
    v = Vector(v)
    v = v - a * v.dot(a)
    return v.normalized() if v.length > 1e-9 else Vector((0.0, 1.0, 0.0))


def _leg_path(tip, wp, inb, n=38, k0=0.30, k1=0.36, sock=SOCK_H,
              pin=(1.0, 0.0, 0.0)):
    """Rod-end face -> duct slot (dead straight, so the slot is always
    cleared) -> smooth bezier to the gearbox-side rod-end face.

    D: both socket faces used to be placed `sock` along the RAW line to the duct
    waypoint while the rod end they screw onto was built along that line
    PROJECTED perpendicular to its pin (see _shank_dir). The two agree only when
    the leg already leaves the joint square to the pin. The inboard end of a
    rear leg does not: 33.8 deg out on the upper rear, 32.3 on the lower rear,
    which parked the socket face 25 mm off the shank axis and left it measuring
    4.74 / 3.67 mm clear of the rod end it is supposed to be screwed into. The
    front legs only got away with it (15.8 / 20.1 deg, 12-16 mm off axis)
    because a 28 mm socket bore is still wide enough to swallow the shank.
    Both ends are now placed on - and arrive along - the rod end's own axis, so
    the shank enters the socket square whatever the leg's plan-view sweep does.

    `sock` must be scaled with the rod end's own k: the toe link runs k=0.86
    hardware whose thread ends 6.4 mm short of the k=1 socket depth, which is
    the whole of that link's 5.24 / 5.66 mm shortfall at the two ends.
    """
    d0 = _shank_dir(Vector(wp) - Vector(tip), pin)
    p0 = Vector(tip) + d0 * sock
    d1 = _shank_dir(Vector(wp) - Vector(inb), pin)
    p3 = Vector(inb) + d1 * sock
    L = (p3 - Vector(wp)).length
    curve = _bez(Vector(wp), Vector(wp) + d0 * (k0 * L), p3 + d1 * (k1 * L),
                 p3, n)
    ns = 4
    lead = [p0 + (Vector(wp) - p0) * (i / ns) for i in range(ns)]
    return lead + curve, d0, d1


# --------------------------------------------------------------------------- #
# fasteners
# --------------------------------------------------------------------------- #

def _hexnut(m, origin, axis, af, h, xhint=None, n=48, bore=0.0, ch=None):
    """Hex nut with the real double chamfer: the flats keep full height, the
    six corners get cut back by a cone at each face."""
    xhint = xhint or _hint(axis)
    # A hex whose flats fall inside its own bore renders as a self-intersecting
    # black sunburst - it cost one whole cycle to find on the rocker pivot, so
    # the size is clamped here rather than trusted at every call site.
    af = max(af, bore * 2.4)
    ch = ch if ch is not None else af * 0.10
    rmax = af / math.sqrt(3.0)
    rflat = af * 0.5

    def hexr(t):
        a = ((t + math.pi / 6.0) % (math.pi / 3.0)) - math.pi / 6.0
        return rflat / math.cos(a)

    ex, ey, ez = _basis(axis, xhint)
    o = Vector(origin)
    rings = []
    for z in (0.0, ch * 0.42, ch, h - ch, h - ch * 0.42, h):
        dz = min(z, h - z)
        cap = rflat * 1.005 + (rmax - rflat * 1.005) * min(dz / ch, 1.0)
        ring = []
        for i in range(n):
            t = TAU * i / n
            r = min(hexr(t), cap)
            ring.append(o + ez * z + ex * (r * math.cos(t))
                        + ey * (r * math.sin(t)))
        rings.append(ring)
    if bore <= 0.0:
        m.tube(rings, cap0=True, cap1=True)
        return
    idx = m.tube(rings, cap0=False, cap1=False)
    inner = []
    for z in (0.0, h):
        inner.append([o + ez * z + ex * (bore * math.cos(TAU * i / n))
                      + ey * (bore * math.sin(TAU * i / n)) for i in range(n)])
    i0 = m.ring(inner[0])
    i1 = m.ring(inner[1])
    m.bridge(i0, idx[0])
    m.bridge(idx[-1], i1)
    m.bridge(i1, i0)


def _hex_rfn(scales, af):
    """Extra-radius function that turns the listed profile rings into a hex.

    The profile itself carries the across-flats radius; this only adds the
    corner rise, so a hex ring and a round ring can live in ONE solid of
    revolution. n must be a multiple of 12 for the corners and the flat
    midpoints to land on samples.
    """
    rf = af * 0.5

    def f(k, t):
        sc = scales.get(k, 0.0)
        if not sc:
            return 0.0
        a = ((t + math.pi / 6.0) % (math.pi / 3.0)) - math.pi / 6.0
        return rf * sc * (1.0 / math.cos(a) - 1.0)
    return f


def _socket_prof(af, depth, face_h, into, k0):
    """Profile points + hex ring scales for a broached hex socket.

    `into` is +1 when the material lies at greater h than the face plane at
    `face_h`. The points come back ordered so they splice straight onto the
    head's own profile - BEFORE it when into > 0, AFTER it when into < 0 - so
    the head and its socket are one unbroken surface of revolution.

    D: the old _hex_socket() built its mouth ring as (z=0, scale=0), i.e. n
    COINCIDENT vertices, which tube() bridged into a solid disc that capped the
    socket and landed exactly coplanar with the head's own end cap. Every
    fastener in the part therefore rendered as a blank domed pin with a
    z-fighting scratch, and it was the sole source of the module's 3240
    boundary edges per corner. Splicing the recess into the head profile makes
    the mouth a real hole and keeps the shell closed.
    """
    rf = af * 0.5
    s = 1.0 if into > 0 else -1.0
    pts = [(0.0, face_h + s * (depth + rf * 0.34)),
           (rf * 0.58, face_h + s * depth),
           (rf, face_h + s * depth * 0.84),
           (rf, face_h + s * depth * 0.12),
           (rf * 1.12, face_h)]
    sc = [0.0, 0.58, 1.0, 1.0, 1.12]
    if into < 0:
        pts.reverse()
        sc.reverse()
    return pts, {k0 + i: v for i, v in enumerate(sc) if v}


def _thread(m, origin, axis, r, h0, h1, pitch=0.0018, depth=0.00085, n=32,
            xhint=None, rows_per=6, lead=0.0014):
    """A real helical V-thread. The triangular phase term is periodic in theta,
    so the surface closes on itself with no seam and no doubled vertices."""
    xhint = xhint or _hint(axis)
    rows = max(8, int(round((h1 - h0) / pitch * rows_per)))
    ex, ey, ez = _basis(axis, xhint)
    o = Vector(origin)

    def prof(u):
        v = 2.0 * abs(((u + 0.5) % 1.0) - 0.5)
        return min(max((v - 0.16) / 0.68, 0.0), 1.0)

    rings = [[o + ez * h0]]
    for k in range(rows + 1):
        h = h0 + (h1 - h0) * k / rows
        taper = min(1.0, (h - h0) / lead, (h1 - h) / lead)
        taper = max(taper, 0.0)
        ring = []
        for i in range(n):
            t = TAU * i / n
            rr = (r - depth * prof(h / pitch - t / TAU)
                  - depth * 1.2 * (1.0 - taper))
            ring.append(o + ez * h + ex * (rr * math.cos(t))
                        + ey * (rr * math.sin(t)))
        rings.append(ring)
    rings.append([o + ez * h1])
    m.tube(rings, cap0=False, cap1=False)


def _cap_screw(m, origin, axis, r_sh=0.0030, length=0.010, head_r=0.0050,
               head_h=0.0042, n=36, xhint=None):
    """Socket-head cap screw, head and broached hex in one closed shell."""
    xhint = xhint or _hint(axis)
    ch = head_r * 0.11
    af = head_r * 1.06
    prof = [(0.0, -length), (r_sh, -length), (r_sh, 0.0), (head_r - ch, 0.0),
            (head_r, ch), (head_r, head_h - ch), (head_r - ch, head_h)]
    sp, hk = _socket_prof(af, head_h * 0.62, head_h, -1, len(prof))
    _spin(m, origin, axis, prof + sp, n=n, xhint=xhint, cap0=False, cap1=False,
          rfn=_hex_rfn(hk, af))


def _fork_bolt(m, centre, axis, inner, outer, r=BOLT_R, hr=0.0110, hh=0.0062,
               n=36):
    """Through bolt spanning a fork: head one side, nyloc the other."""
    c = Vector(centre)
    a = Vector(axis).normalized()
    xh = _hint(axis)
    ch = hr * 0.10
    af = hr * 1.12
    sp, hk = _socket_prof(af, hh * 0.55, -outer - hh, 1, 0)
    prof = sp + [(hr - ch, -outer - hh), (hr, -outer - hh + ch),
                 (hr, -outer - 0.0010), (hr - 0.0006, -outer),
                 (r, -outer + 0.0006), (r, outer + 0.0086),
                 (r - 0.0005, outer + 0.0092)]
    _spin(m, c, a, prof, n=n, xhint=xh, cap0=True, cap1=True,
          rfn=_hex_rfn(hk, af))
    # The nyloc bears on the fork face, 0.2 mm proud of coplanar so the two
    # annuli cannot fight. It used to be parked 1.0 mm clear of it - a nut
    # floating on nothing - and the shank is lengthened to keep two threads
    # showing past it.
    _hexnut(m, c + a * (outer - 0.0002), a, 0.0168, 0.0070, xhint=xh,
            bore=r + 0.0002, n=42)
    return inner


# --------------------------------------------------------------------------- #
# plates with a bore (clevis cheeks, rocker arms, ARB blade)
# --------------------------------------------------------------------------- #

def _capsule_outline(c0, r0, c1, r1, n_arc=22):
    dx, dy = c1[0] - c0[0], c1[1] - c0[1]
    L = math.hypot(dx, dy)
    if L < 1e-6 or L + min(r0, r1) <= abs(r0 - r1) + 1e-9:
        c, r = (c0, r0) if r0 >= r1 else (c1, r1)
        m = 4 * n_arc
        return [(c[0] + r * math.cos(TAU * i / m),
                 c[1] + r * math.sin(TAU * i / m)) for i in range(m)]
    al = math.atan2(dy, dx)
    be = math.acos(max(-1.0, min(1.0, (r0 - r1) / L)))
    pts = []
    for i in range(n_arc + 1):
        a = (al + be) + (TAU - 2 * be) * i / n_arc
        pts.append((c0[0] + r0 * math.cos(a), c0[1] + r0 * math.sin(a)))
    for i in range(n_arc + 1):
        a = (al - be) + (2 * be) * i / n_arc
        pts.append((c1[0] + r1 * math.cos(a), c1[1] + r1 * math.sin(a)))
    return pts


def _ray_out(poly, ang):
    ux, uy = math.cos(ang), math.sin(ang)
    n = len(poly)
    best = 1e9
    for i in range(n):
        ax, ay = poly[i]
        bx, by = poly[(i + 1) % n]
        ex, ey = bx - ax, by - ay
        det = -ux * ey + ex * uy
        if abs(det) < 1e-13:
            continue
        t = (-ax * ey + ex * ay) / det
        s = (ux * ay - uy * ax) / det
        if t > 1e-6 and -1e-9 <= s <= 1.0 + 1e-9:
            best = min(best, t)
    return best if best < 1e8 else 0.01


def _resample(poly, n):
    """Resample a closed polygon at n equal ARC-LENGTH stations."""
    m = len(poly)
    cum = [0.0]
    for i in range(m):
        a, b = poly[i], poly[(i + 1) % m]
        cum.append(cum[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    tot = cum[-1]
    out, j = [], 0
    for i in range(n):
        s = tot * i / n
        while j < m - 1 and cum[j + 1] < s:
            j += 1
        seg = (cum[j + 1] - cum[j]) or 1.0
        u = (s - cum[j]) / seg
        a, b = poly[j], poly[(j + 1) % m]
        out.append((a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u))
    return out


def _plate(m, hole_c, hole_r, r_head, base_c, r_base, axis, t0, t1,
           ch=0.0011, n=40, xhint=None, lobes=()):
    """A chamfered plate with a bore, swept from t0 to t1 along `axis`.

    The outline is the union of a capsule from the bore out to `base_c` and one
    per extra (point, radius) in `lobes` - a two-lobe plate is how a bellcrank
    is actually made, and it is the only way to avoid two separate plates
    laying coplanar faces on top of each other round a shared hub.

    D: the outline used to be sampled on n uniform ANGULAR rays from the bore,
    which crowded samples where the outline is closest and starved the far base
    arc (at n=40 a 21 mm arc got ~10 samples, 0.26 mm sagitta - a visibly
    straight-edged silhouette at the 400 mm hero distance), and the chamfer was
    a constant RADIAL inset, so its band pinched to nothing along the capsule
    flanks. The outline is now resampled by arc length and the chamfer is inset
    along the outline's own normal, so it is a constant band the whole way
    round.
    """
    xhint = xhint or _hint(axis)
    ex, ey, ez = _basis(axis, xhint)
    o = Vector(hole_c)

    caps = [(Vector(base_c), r_base)] + [(Vector(p), r) for (p, r) in lobes]
    polys = []
    for (bc, rb) in caps:
        d = bc - o
        polys.append(_capsule_outline((0.0, 0.0), r_head,
                                      (d.dot(ex), d.dot(ey)), rb, n_arc=40))
    if len(polys) == 1:
        dense = polys[0]
    else:
        # union of capsules that all contain the bore centre -> star shaped
        # about it, so a max over per-lobe ray casts IS the union boundary
        nr = 1440
        dense = []
        for i in range(nr):
            a = TAU * i / nr
            rr = max(_ray_out(p, a) for p in polys)
            dense.append((rr * math.cos(a), rr * math.sin(a)))

    P = _resample(dense, n)
    cb = ch * 0.85
    inner = hole_r + cb + 0.0004
    lo, hi = min(t0, t1), max(t0, t1)

    Q = []
    for i in range(n):
        a, b, c = P[(i - 1) % n], P[i], P[(i + 1) % n]
        tx, ty = c[0] - a[0], c[1] - a[1]
        L = math.hypot(tx, ty) or 1.0
        cross = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
        if cross < 0.0:
            # concave (the crotch between two lobes): a normal inset folds over
            # itself there, so pull straight back towards the bore instead
            rr = math.hypot(b[0], b[1]) or 1.0
            q = (b[0] * (1.0 - ch / rr), b[1] * (1.0 - ch / rr))
        else:
            q = (b[0] - ty / L * ch, b[1] + tx / L * ch)
        rq = math.hypot(q[0], q[1])
        rb = math.hypot(b[0], b[1]) or 1.0
        if rq < inner:
            q = (b[0] * inner / rb, b[1] * inner / rb)
        Q.append(q)

    def ring(pts, h):
        return [o + ez * h + ex * p[0] + ey * p[1] for p in pts]

    def bore(r, h):
        out = []
        for i in range(n):
            a = math.atan2(P[i][1], P[i][0])
            out.append(o + ez * h + ex * (r * math.cos(a))
                       + ey * (r * math.sin(a)))
        return out

    rings = [
        bore(hole_r, lo + cb),
        bore(hole_r + cb, lo),
        ring(Q, lo),
        ring(P, lo + ch),
        ring(P, hi - ch),
        ring(Q, hi),
        bore(hole_r + cb, hi),
        bore(hole_r, hi - cb),
    ]
    m.tube(rings, cap0=False, cap1=False, loop=True)


# --------------------------------------------------------------------------- #
# rod ends
# --------------------------------------------------------------------------- #

def _rod_end(mb, mn, centre, pin_axis, shank_dir, k=1.0, n=40, thread=True,
             pin_bolt=False):
    """Race + ball + threaded shank + jam nut, all in world space."""
    c = Vector(centre)
    pa = Vector(pin_axis).normalized()
    sd = _shank_dir(shank_dir, pa)

    seat, er, ew = SEAT_R * k, EYE_R * k, EYE_W * k
    ch = 0.0011 * k
    half = ew * 0.5
    ropen = math.sqrt(max(seat * seat - half * half, 1e-8))

    # Race: spherical seat, a swage groove round the OD and a real chamfer at
    # each bore mouth - that chamfer is what puts a dark ring between race and
    # ball instead of letting the two read as one lump of metal.
    mch = 0.0011 * k                      # bore-mouth chamfer
    hs = half - mch
    prof = [(math.sqrt(max(seat * seat - hs * hs, 1e-9)) + mch, -half)]
    steps = 12
    for i in range(steps + 1):
        h = -hs + 2.0 * hs * i / steps
        prof.append((math.sqrt(max(seat * seat - h * h, 1e-9)), h))
    g = 0.0010 * k
    prof += [(math.sqrt(max(seat * seat - hs * hs, 1e-9)) + mch, half),
             (er * 0.70, half), (er - ch, half),
             (er, half - ch), (er, half - ch - 0.0018 * k),
             (er - g, half - ch - 0.0030 * k),
             (er - g, -(half - ch - 0.0030 * k)),
             (er, -(half - ch - 0.0018 * k)), (er, -(half - ch)),
             (er - ch, -half), (er * 0.70, -half)]
    _spin(mb, c, pa, prof, n=n, xhint=sd, loop=True)

    # Ball: sphere truncated flat, big enough to swallow the upright's own ball,
    # and BORED for the bolt. A solid ball reads as a blank plug; the bore is
    # what makes it read as a spherical bearing.
    br, bh = BALL_R * k, BALL_H * k
    bore = BOLT_R * k + 0.0006
    fr = math.sqrt(max(br * br - bh * bh, 1e-9))
    a0 = math.asin(bh / br)
    bc = 0.0007 * k
    bp = [(bore + bc, -bh), (fr - bc, -bh), (fr, -bh + bc)]
    for i in range(1, 22):
        a = -a0 + 2.0 * a0 * i / 22
        bp.append((br * math.cos(a), br * math.sin(a)))
    bp += [(fr, bh - bc), (fr - bc, bh), (bore + bc, bh), (bore, bh - bc),
           (bore, -bh + bc)]
    _spin(mb, c, pa, bp, n=n, xhint=sd, loop=True)

    # neck: starts outside the seat sphere and inside the race, so its cap is
    # never visible through the bore and never clips the ball
    h0 = seat + 0.0008 * k
    neck = [(0.0, h0), (NECK_R * k, h0), (NECK_R * k, er + 0.0012 * k),
            (THR_R * k + 0.0006 * k, THR_H0 * k)]
    _spin(mb, c, sd, neck, n=n, xhint=pa)
    if thread:
        _thread(mb, c, sd, THR_R * k, THR_H0 * k, THR_H1 * k, n=30, xhint=pa,
                pitch=0.0018 * k, depth=0.00085 * k)
    else:
        _spin(mb, c, sd, [(0.0, THR_H0 * k), (THR_R * k, THR_H0 * k),
                          (THR_R * k, THR_H1 * k), (0.0, THR_H1 * k)],
              n=n, xhint=pa)
    _hexnut(mn, c + sd * (JAM_H0 * k), sd, JAM_AF * k, JAM_H * k, xhint=pa,
            bore=THR_R * k - 0.0003, n=48)
    if pin_bolt:
        # Outboard joints are bolted up by brake_assembly's clevis, whose bolt
        # is r=5.2 mm with a head/nut 9.6 mm at |h| 17.2..23.0 mm. This one is
        # deliberately drawn smaller and shorter so it lives entirely INSIDE
        # that bolt in the assembled car - no coincident faces, no z-fighting -
        # while still closing the joint when this part is rendered alone.
        r = 0.0048 * k
        hr, hh = 0.0090 * k, 0.0044 * k
        o = 0.0180 * k
        af = hr * 1.12
        sp, hk = _socket_prof(af, hh * 0.55, 0.0, 1, 0)
        _spin(mb, c - pa * (o + hh), pa,
              sp + [(hr - hr * 0.10, 0.0), (hr, hr * 0.10),
                    (hr, hh - 0.0008 * k),
                    (hr - 0.0008 * k, hh), (r, hh),
                    (r, hh + 2.0 * o - 0.0008 * k),
                    (r + 0.0006 * k, hh + 2.0 * o),
                    (hr - 0.0008 * k, hh + 2.0 * o),
                    (hr, hh + 2.0 * o + 0.0008 * k), (hr, hh + 2.0 * o + hh),
                    (0.0, hh + 2.0 * o + hh)], n=36, xhint=sd,
              rfn=_hex_rfn(hk, af))


def _clevis(mb, mf, centre, pin_axis, base_c, k=1.0, n=40, r_base=0.021):
    """Two cheeks plus the through bolt: the gearbox-side half of a joint."""
    c = Vector(centre)
    pa = Vector(pin_axis).normalized()
    inn, t = CHEEK_IN * k, CHEEK_T * k
    for s in (-1.0, 1.0):
        _plate(mb, c, BOLT_R * k + 0.0003, 0.0148 * k, base_c, r_base,
               pa * s, inn, inn + t, ch=0.0010, n=n)
    _fork_bolt(mf, c, pa, inn, inn + t, r=BOLT_R * k, hr=0.0110 * k,
               hh=0.0062 * k)


# --------------------------------------------------------------------------- #
# body skin sampling - so every bracket really sits on the car
# --------------------------------------------------------------------------- #

_SKIN = {}


def _skin_poly(x):
    key = round(x, 4)
    r = _SKIN.get(key)
    if r is None:
        pts = C.catmull_rom(S.station_half(S.station_at(x)), 161)
        cum = [0.0]
        for i in range(1, len(pts)):
            cum.append(cum[-1] + math.hypot(pts[i][0] - pts[i - 1][0],
                                            pts[i][1] - pts[i - 1][1]))
        r = (pts, cum)
        _SKIN[key] = r
    return r


def _skin_l(x, z):
    """Arc length along the half section at which the skin is at height z."""
    pts, cum = _skin_poly(x)
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        if abs(b[1] - a[1]) > 1e-9 and (a[1] - z) * (b[1] - z) <= 0.0:
            return cum[i] + (cum[i + 1] - cum[i]) * (z - a[1]) / (b[1] - a[1])
    return cum[-1] * 0.5


def _skin_pt(x, l):
    pts, cum = _skin_poly(x)
    l = min(max(l, 0.0), cum[-1])
    lo, hi = 0, len(cum) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if cum[mid] <= l:
            lo = mid
        else:
            hi = mid
    seg = (cum[hi] - cum[lo]) or 1.0
    u = (l - cum[lo]) / seg
    y = pts[lo][0] + (pts[hi][0] - pts[lo][0]) * u
    z = pts[lo][1] + (pts[hi][1] - pts[lo][1]) * u
    ty, tz = pts[hi][0] - pts[lo][0], pts[hi][1] - pts[lo][1]
    L = math.hypot(ty, tz) or 1.0
    return Vector((x, y, z)), Vector((0.0, tz / L, -ty / L))


def _skin_at(x, z):
    return _skin_pt(x, _skin_l(x, z))


_PICK_CACHE = {}


def _pick(key):
    """(pin point, pad centre height) for one gearbox-side pickup."""
    if key not in _PICK_CACHE:
        x, z, off = PICKS[key]
        p, n = _skin_at(x, z)
        _PICK_CACHE[key] = (p + n * off, z)
    return _PICK_CACHE[key]


def _arb_points():
    """ARB bar root, blade plane and blade tip, all referenced off the skin."""
    root, _n = _skin_at(ARB_X, ARB_Z)
    tip_sk, tn = _skin_at(ARB_TIP_X, ARB_TIP_Z)
    y1 = tip_sk.y + ARB_STAND / max(tn.y, 0.35)
    return (Vector((ARB_X, root.y, ARB_Z)), y1,
            Vector((ARB_TIP_X, y1, ARB_TIP_Z)))


# --------------------------------------------------------------------------- #
# gearbox-side bracket
# --------------------------------------------------------------------------- #

def _rrect_outline(a, b, fil, nc=8):
    pts = []
    for (cx, cy, a0) in ((a - fil, b - fil, 0.0), (-(a - fil), b - fil, 90.0),
                         (-(a - fil), -(b - fil), 180.0),
                         (a - fil, -(b - fil), 270.0)):
        for k in range(nc + 1):
            ang = math.radians(a0 + 90.0 * k / nc)
            pts.append((cx + fil * math.cos(ang), cy + fil * math.sin(ang)))
    return pts


def _pad(mb, mf, x0, z0, lx, lt, thick=0.0114, lift=-0.0014, bolt=(0.62, 0.60)):
    """A machined pad that follows the body skin in BOTH directions.

    Every grid point is resampled off the real station profile, so the pad is
    genuinely curved. The top is not a plain slab - it carries a 2.4 mm skim
    pocket inside a rim, and each of the four screws sits on its own spotfaced
    boss, so no face of it is a bare plate bigger than about 25 mm.

    D: `lift` used to be +1.3 mm, so every pad hovered 1.3 mm clear of the skin
    it is bonded to and showed an open shadow slot right round its 86x64 mm
    footprint in the assembled car. It is now NEGATIVE: the pad is bedded 1.4 mm
    into the skin, which is both what a bonded pad does and the only way to
    guarantee no daylight whatever the station curvature does between grid
    points. The underside was also a single flat cap0 n-gon spanning a curved
    5756 mm^2 footprint - it is now a resampled fan that follows the same skin.
    """
    outline = _rrect_outline(lx * 0.5, lt * 0.5, min(lx, lt) * 0.24)
    ch = 0.0013
    top = lift + thick
    pocket = top - 0.0024

    def place(a, b, off):
        p, nn = _skin_pt(x0 + a, _skin_l(x0 + a, z0) + b)
        return p + nn * off

    inner = [(u * 0.93, v * 0.93) for (u, v) in outline]
    rings = [[place(0.0, 0.0, lift)],
             [place(u * 0.42, v * 0.42, lift) for (u, v) in outline],
             [place(u * 0.80, v * 0.80, lift) for (u, v) in outline],
             [place(u, v, lift) for (u, v) in outline],
             [place(u, v, top - ch) for (u, v) in outline],
             [place(u, v, top) for (u, v) in inner],
             [place(u * 0.80, v * 0.80, top) for (u, v) in inner],
             [place(u * 0.74, v * 0.74, pocket) for (u, v) in inner],
             [place(u * 0.40, v * 0.40, pocket) for (u, v) in inner],
             [place(0.0, 0.0, pocket)]]
    mb.tube(rings, cap0=False, cap1=False)

    for sa in (-1.0, 1.0):
        for sb in (-1.0, 1.0):
            a, b = sa * bolt[0] * lx * 0.5, sb * bolt[1] * lt * 0.5
            p, nn = _skin_pt(x0 + a, _skin_l(x0 + a, z0) + b)
            o = p + nn * pocket
            _spin(mb, o, nn, [(0.0, 0.0), (0.0086, 0.0), (0.0086, 0.0026),
                              (0.0078, 0.0034), (0.0, 0.0034)],
                  n=26, xhint=(1, 0, 0), cap0=False)
            _cap_screw(mf, o + nn * 0.0034, nn, xhint=(1, 0, 0))
    return place(0.0, 0.0, top)


def _bracket(mb, mf, pin_c, pin_axis, lx=0.086, lt=0.064, k=1.0, r_base=0.022,
             pad_z=None):
    """Pad + web + clevis cheeks carrying one inboard pickup.

    The cheek capsule's base circle is placed r_base + 4.0 mm off the skin, so
    its lowest point lands 4 mm INSIDE the 11.4 mm pad it grows out of - deep
    enough that cheek and pad read as one casting, shallow enough that no lug
    plate ever dives through the bodywork.
    """
    pin_c = Vector(pin_c)
    z0 = pin_c.z if pad_z is None else pad_z
    p0, n0 = _skin_at(pin_c.x, z0)
    _pad(mb, mf, pin_c.x, z0, lx, lt)
    base = p0 + n0 * (r_base + 0.0040)
    _clevis(mb, mf, pin_c, pin_axis, base, k=k, r_base=r_base)
    stem = pin_c - base
    if stem.length > 0.020:
        tip = base + stem * 0.58
        # r_base must not exceed the base's own stand-off, or the web's base
        # arc dives through the pad and out the back of the bodywork.
        _plate(mb, tip, 0.0040, 0.0135, base, min(0.0210, r_base - 0.0016),
               Vector(pin_axis), -0.0044, 0.0044, ch=0.0009, n=36)
    return base


# --------------------------------------------------------------------------- #
# the corner
# --------------------------------------------------------------------------- #

def _corner(tag, coll, mirror):
    carb, rods, nuts = _M(), _M(), _M()
    brak, fast, shaf = _M(), _M(), _M()
    boot, clmp = _M(), _M()

    X = Vector((1.0, 0.0, 0.0))
    Y = Vector((0.0, 1.0, 0.0))
    Z = Vector((0.0, 0.0, 1.0))

    # ---- wishbones ------------------------------------------------------- #
    legs = {}
    # k0 shapes how fast a leg turns off its radial exit from the duct. The
    # upper rear leg uses a tighter value so it swings aft early and leaves a
    # real channel for the pushrod to climb through between the two upper legs.
    for key, tip, wp, chord, thick, k0, uo in (
            ("uf", UF, W_UF, 0.062, 0.0175, 0.30, 0.015),
            ("ur", UR, W_UR, 0.062, 0.0175, 0.18, -0.015),
            ("lf", LF, W_LF, 0.068, 0.0192, 0.30, 0.017),
            ("lr", LR, W_LR, 0.068, 0.0192, 0.30, -0.017)):
        inb, padz = _pick(key)
        path, d0, d1 = _leg_path(tip, wp, inb, k0=k0, pin=X)
        sect = _arm_section(chord, thick, SOCK_R, SOCK_R, u_off=uo)
        _sweep(carb, path, sect)
        legs[key] = (path, d0, d1, sect)
        _rod_end(rods, nuts, tip, X, d0, pin_bolt=True)
        _rod_end(rods, nuts, inb, X, d1)
        _bracket(brak, fast, inb, X, pad_z=padz)

    # Moulded web joining each pair of legs near the outboard base.
    #
    # A plain lens between the two legs left a hard crease where it cut the leg
    # fairings and read as a stamped paddle. The web's half height at every
    # chord station is now the ENVELOPE of the two leg sections there, floored
    # by a waist that runs out at both ends, so the web surface is always
    # inside the leg it emerges from and crosses it tangentially. These are
    # still separate shells - nothing is booleaned - but the step is gone.
    WEB_SPAN = 0.15
    for a, b in (("uf", "ur"), ("lf", "lr")):
        pa, pb = legs[a][0], legs[b][0]
        sa, sb = legs[a][3], legs[b][3]
        nweb, nu, rings, prev = 26, 40, [], None
        for i in range(nweb):
            t = i / (nweb - 1)
            j = t * WEB_SPAN * (len(pa) - 1)
            j0 = min(int(j), len(pa) - 2)
            jf = j - j0
            A = pa[j0] + (pa[j0 + 1] - pa[j0]) * jf
            B = pb[j0] + (pb[j0 + 1] - pb[j0]) * jf
            mid = (A + B) * 0.5
            tg = (pa[j0 + 1] + pb[j0 + 1]) * 0.5 - mid if prev is None else mid - prev
            prev = mid
            eu = B - A
            hw = eu.length * 0.5
            eu = eu.normalized()
            tg = (tg - eu * tg.dot(eu)).normalized()
            ev = tg.cross(eu)
            u_par = j / (len(pa) - 1)
            pta, ptb = sa(u_par), sb(u_par)
            thick = max(max(abs(v) for (_u, v) in pta),
                        max(abs(v) for (_u, v) in ptb))
            # run out at BOTH ends: the outboard end used to be cut off square
            runo = C.smoothstep(t / 0.13)
            runi = C.smoothstep((1.0 - t) / 0.34)
            waist = 0.0008 + (0.34 * thick - 0.0008) * runo * runi
            ring = []
            for q in range(nu):
                ang = TAU * q / nu
                cu = math.cos(ang)
                # Envelope of BOTH leg sections at this chord station, so the
                # web leaves each leg at exactly that leg's local half
                # thickness. D: it used to leave at a flat 0.5x the leg's MAX
                # thickness, which near the trailing edge - where the web
                # actually emerges - is a 4 mm step, and the union read as a
                # hard straight crease with a stamped paddle behind it.
                env = max(_sec_half(pta, -hw * (cu + 1.0)),
                          _sec_half(ptb, hw * (1.0 - cu)), waist)
                ring.append(mid + eu * (hw * cu) + ev * (env * math.sin(ang)))
            rings.append(ring)
        carb.tube(rings, cap0=True, cap1=True)

    # ---- toe link -------------------------------------------------------- #
    i_to, to_padz = _pick("to")
    # sock scales with TOE_K: this link's rod ends are 0.86 scale, so their
    # thread stops 6.4 mm short of where a k=1 socket face would sit.
    path, d0, d1 = _leg_path(TO, W_TO, i_to, k0=0.32, k1=0.34,
                             sock=SOCK_H * TOE_K, pin=Z)
    _sweep(carb, path, _arm_section(0.046, 0.0140, 0.0122, 0.0122))
    _rod_end(rods, nuts, TO, Z, d0, k=TOE_K, pin_bolt=True)
    _rod_end(rods, nuts, i_to, Z, d1, k=TOE_K)
    _bracket(brak, fast, i_to, Z, lx=0.076, lt=0.060, k=TOE_K, r_base=0.019,
             pad_z=to_padz)

    # ---- rocker ---------------------------------------------------------- #
    ROCK_P, rock_padz = _pick("rk")
    # arms spread ~67 deg apart: at 41 deg the two capsule outlines merged
    # into one leaf shape and the bellcrank stopped reading as a bellcrank
    ROCK_A = ROCK_P + Vector((0.0, 0.078, 0.046))
    ROCK_B = ROCK_P + Vector((0.0, 0.098, -0.072))
    # The bellcrank is ONE plate per side carrying both arms, bored at the
    # pivot. D: it used to be two separate capsule plates, each with a 51 mm
    # base circle centred on the same pivot and swept between the same two
    # heights - so a 51 mm disc of doubled, exactly coplanar faces z-fought on
    # every face, which is most of why the pivot read as a stack of washers.
    for s in (-1.0, 1.0):
        t0 = s * ROCK_HALF
        t1 = s * (ROCK_HALF + ROCK_T)
        _plate(brak, ROCK_P, 0.0138, 0.0276, ROCK_A, 0.0158, X, t0, t1,
               ch=0.0016, n=96, lobes=[(ROCK_B, 0.0158)])
        for hole in (ROCK_A, ROCK_B):
            # Spotfaced bearing seat, sunk 0.4 mm INTO the arm so its own base
            # annulus is buried in the plate instead of laid exactly on the
            # plate's face, where the two fought.
            _spin(brak, hole + X * (t1 - s * 0.0004), X * s,
                  [(BOLT_R + 0.0004, 0.0), (0.0148, 0.0), (0.0148, 0.0028),
                   (0.0136, 0.0036), (BOLT_R + 0.0004, 0.0036)],
                  n=36, xhint=(0, 0, 1), loop=True)
        # Hub collar: a bored bearing carrier standing 4.4 mm proud of the arm.
        # D: this was _spin(ROCK_P + X*t0, X, ...) - a SIGNED origin with an
        # UNSIGNED axis - so on the s=-1 side it grew the wrong way, from
        # -18 mm to -7 mm, straight over the torsion boss, and the -X plate got
        # no collar at all. Its two end discs were also exactly coplanar with
        # the plate faces. It now starts 0.4 mm inside the plate (so the inner
        # end is buried) and is an annulus, not a capped puck.
        _spin(brak, ROCK_P + X * (t0 + s * 0.0004), X * s,
              [(0.0212, 0.0), (0.0262, 0.0), (0.0268, 0.0014),
               (0.0268, 0.0136), (0.0262, 0.0150), (0.0212, 0.0150)],
              n=48, xhint=(0, 0, 1), loop=True)
    # Torsion-bar boss spanning the two plates. It used to be 50 mm across,
    # which swallowed the 60 mm rocker hub and left the arms reading as two
    # fins on a drum; at 41 mm the hub, its circlip groove and the splined
    # collar all read as separate machined features.
    # It runs 1 mm INTO each plate so its end discs are buried rather than
    # sitting exactly on the plates' inner faces.
    _spin(brak, ROCK_P - X * 0.0190, X,
          [(0.0, 0.0), (0.0198, 0.0), (0.0206, 0.0010), (0.0206, 0.0078),
           (0.0186, 0.0090), (0.0186, 0.0120), (0.0206, 0.0132),
           (0.0206, 0.0248), (0.0186, 0.0260), (0.0186, 0.0290),
           (0.0206, 0.0302), (0.0206, 0.0370), (0.0198, 0.0380),
           (0.0, 0.0380)], n=48, xhint=(0, 0, 1))
    # Pivot shaft: head hard against one pedestal spotface, nut against the
    # other. D: the nut was 23 mm across flats on a 26.8 mm bore - the hex fell
    # INSIDE its own hole and the self-intersection rendered as a black
    # serrated sunburst round the pivot. A nut has to be at least ~2.4x bore.
    sp, hk = _socket_prof(0.0172, 0.0036, 0.0, 1, 0)
    _spin(rods, ROCK_P - X * 0.0498, X,
          sp + [(0.0142, 0.0), (0.0158, 0.0016), (0.0158, 0.0058),
                (0.0132, 0.0066), (0.0132, 0.1074), (0.0, 0.1080)],
          n=48, xhint=(0, 0, 1), rfn=_hex_rfn(hk, 0.0172))
    _hexnut(fast, ROCK_P + X * 0.0440, X, 0.0360, 0.0110, xhint=(0, 0, 1),
            bore=0.0136, n=48)

    # pivot pedestal: two cheeks outboard of the rocker plates onto a pad
    # The pad sits well below the pivot on the flank, not directly under it:
    # a pedestal only 12 mm tall made two 46 mm discs that swallowed the whole
    # rocker hub. Dropping the pad 37 mm down the skin gives a 50 mm tapered
    # pedestal that reads as a bearing carrier bolted to the casing.
    p_sk, n_sk = _skin_at(ROCK_P.x, ROCK_PAD_Z)
    _pad(brak, fast, ROCK_P.x, ROCK_PAD_Z, 0.066, 0.058)
    ped_base = p_sk + n_sk * (0.0270 + 0.0040)
    for s in (-1.0, 1.0):
        _plate(brak, ROCK_P, 0.0135, 0.0180, ped_base, 0.0270, X * s,
               0.0344, 0.0416, ch=0.0013, n=72)
        # sunk 0.4 mm so the seat's own base annulus is inside the cheek
        _spin(brak, ROCK_P + X * (s * 0.0412), X * s,
              [(0.0136, 0.0), (0.0172, 0.0), (0.0172, 0.0022),
               (0.0160, 0.0030), (0.0136, 0.0030)],
              n=36, xhint=(0, 0, 1), loop=True)

    # ---- pushrod --------------------------------------------------------- #
    lrp = legs["lr"][0]
    fi = next((i for i, p in enumerate(lrp) if p.y <= PUSH_FOOT_Y), 6)
    fi = max(3, min(fi, len(lrp) - 4))
    fpt = lrp[fi]
    ftan = (lrp[fi + 1] - lrp[fi - 1]).normalized()
    foot = fpt + Vector((0.0, 0.0, PUSH_FOOT_RISE))
    pdir = (ROCK_A - foot).normalized()
    p0 = foot + pdir * SOCK_H
    p1 = ROCK_A - pdir * SOCK_H
    npp = 28
    _sweep(carb, [p0 + (p1 - p0) * (i / (npp - 1)) for i in range(npp)],
           _arm_section(0.048, 0.0182, SOCK_R, SOCK_R, b0=(0.06, 0.30),
                        b1=(0.70, 0.94)))
    _rod_end(rods, nuts, foot, X, pdir)
    _rod_end(rods, nuts, ROCK_A, X, -pdir)
    # bearing on the spotface seat, not sunk 3.2 mm inside it
    _fork_bolt(fast, ROCK_A, X, ROCK_HALF, ROCK_HALF + ROCK_T + 0.0032)

    # pushrod foot: saddle clamp round the lower wishbone leg, then cheeks
    sect = legs["lr"][3]
    eu, ev, _ = _basis(ftan, (1, 0, 0))
    rings = []
    for dj in (-2, -1, 0, 1, 2):
        idx = max(0, min(len(lrp) - 1, fi + dj))
        t = idx / (len(lrp) - 1)
        grow = 0.0036 * (1.0 - 0.58 * (abs(dj) / 2.0) ** 2)
        pts = _offset2d(sect(t), grow)
        rings.append([lrp[idx] + eu * u + ev * v for (u, v) in pts])
    brak.tube(rings, cap0=True, cap1=True)
    for s in (-1.0, 1.0):
        _plate(brak, foot, 0.0148, 0.0208, fpt, 0.0235, X * s,
               CHEEK_IN, CHEEK_IN + CHEEK_T, ch=0.0011, n=40)
    _fork_bolt(fast, foot, X, CHEEK_IN, CHEEK_IN + CHEEK_T)
    for s in (-1.0, 1.0):   # clamp screws through the saddle, heads underneath
        o = fpt + eu * (s * 0.030) - ev * 0.014
        _cap_screw(fast, o, -ev, r_sh=0.0026, length=0.020,
                   head_r=0.0044, head_h=0.0038, xhint=tuple(eu))

    # ---- ARB blade, seal boot, drop link --------------------------------- #
    arb_root, arb_y1, ARB_TIP = _arb_points()
    arb_end = Vector((ARB_X, arb_y1, ARB_Z))
    barL = arb_y1 - arb_root.y
    _spin(brak, arb_root - Y * 0.040, Y,
          [(0.0, 0.0), (0.0140, 0.0), (0.0140, 0.040 + barL * 0.42),
           (0.0128, 0.040 + barL * 0.52), (0.0128, 0.040 + barL),
           (0.0110, 0.040 + barL + 0.0026), (0.0, 0.040 + barL + 0.0026)],
          n=40, xhint=(1, 0, 0))
    # Rubber gaiter where the bar leaves the casing: a flat bolting flange, then
    # three convolutions, then a swaged collar on the bar.
    #
    # D: the four flange screws used to sit at r=23.6 mm, h=+2.6 mm with an
    # 8 mm shank running +Y - straight through the first convolution (h
    # 5.2-10.4 mm at r 21.2-27.2 mm; 989 overlapping triangle pairs), with the
    # heads buried at h=-0.4 mm on the casing side where nothing could see
    # them. The flange is now a real 6 mm-wide land at r 27-33 mm OUTSIDE the
    # convolution envelope, and the screws stand on it, heads out.
    FLG = 0.0300
    gp = [(0.0146, 0.0)]
    for (r, h) in ((0.0340, 0.0000), (0.0344, 0.0008), (0.0344, 0.0026),
                   (0.0340, 0.0034), (0.0256, 0.0034), (0.0250, 0.0056),
                   (0.0206, 0.0080), (0.0244, 0.0112), (0.0192, 0.0136),
                   (0.0232, 0.0168), (0.0180, 0.0192), (0.0214, 0.0220),
                   (0.0168, 0.0244), (0.0166, 0.0270), (0.0166, 0.0300),
                   (0.0146, 0.0300)):
        gp.append((r, h))
    _spin(boot, arb_root - Y * 0.0010, Y, gp, n=44, xhint=(1, 0, 0), loop=True)
    _spin(clmp, arb_root - Y * 0.0010, Y,
          [(0.0169, 0.0268), (0.0186, 0.0274), (0.0186, 0.0294),
           (0.0169, 0.0300)], n=36, xhint=(1, 0, 0), loop=True)
    for i in range(4):
        a = TAU * (i + 0.5) / 4.0
        o = arb_root - Y * 0.0010 + Vector((FLG * math.cos(a), 0.0034,
                                           FLG * math.sin(a)))
        _cap_screw(fast, o, Y, r_sh=0.0024, length=0.009, head_r=0.0038,
                   head_h=0.0032, xhint=(1, 0, 0))
    _plate(brak, ARB_TIP, 0.0062, 0.0136, arb_end, 0.0210, Y,
           -0.0062, 0.0062, ch=0.0010, n=64)
    # Blade root clamp. D: this was a bare 42 x 16 mm cylinder of EXACTLY the
    # blade plate's own 21.0 mm base radius, so the two cylindrical surfaces
    # were identical over a 10.4 mm band and z-fought as lens-shaped bright
    # patches on the blade face; both its end faces were flat and unbroken. It
    # is now 25 mm radius - larger than anything it grips - chamfered into the
    # blade at the inboard end and domed at the outboard end.
    _spin(brak, arb_end - Y * 0.0092, Y,
          [(0.0, 0.0), (0.0150, 0.0), (0.0212, 0.0022), (0.0244, 0.0044),
           (0.0250, 0.0058), (0.0250, 0.0126), (0.0244, 0.0142),
           (0.0224, 0.0164), (0.0180, 0.0180), (0.0104, 0.0190),
           (0.0, 0.0194)], n=44, xhint=(1, 0, 0))

    dl_dir = (ROCK_B - ARB_TIP).normalized()
    dlL = (ROCK_B - ARB_TIP).length
    a0 = ARB_TIP + dl_dir * 0.0210
    _spin(brak, a0, dl_dir,
          [(0.0, 0.0), (0.0104, 0.0), (0.0104, 0.0028), (0.0084, 0.0060),
           (0.0084, dlL - 0.0210 - SOCK_H * 0.70),
           (0.0104, dlL - 0.0210 - SOCK_H * 0.70 + 0.0032),
           (0.0104, dlL - 0.0210 - SOCK_H * 0.62),
           (0.0, dlL - 0.0210 - SOCK_H * 0.62)], n=32, xhint=(1, 0, 0))
    _rod_end(rods, nuts, ROCK_B, X, -dl_dir, k=0.80)
    _fork_bolt(fast, ROCK_B, X, ROCK_HALF, ROCK_HALF + ROCK_T + 0.0032)
    for s in (-1.0, 1.0):
        _plate(brak, ARB_TIP, 0.0044, 0.0116, a0 + dl_dir * 0.010, 0.0104,
               Y * s, 0.0086, 0.0086 + 0.0046, ch=0.0009, n=32)
    _fork_bolt(fast, ARB_TIP, Y, 0.0086, 0.0132, r=0.0042, hr=0.0088,
               hh=0.0050)

    # ---- driveshaft ------------------------------------------------------ #
    org = Vector((SHAFT_X, 0.0, SHAFT_Z))

    def lobe(k, t):
        return 0.0034 * math.cos(3.0 * t) if 2 <= k <= 6 else 0.0

    # Inboard tripod housing. It was a bare 105 mm drum - the single largest
    # untextured face in the part - so it now carries a bolted output flange, a
    # spigot register, a snap-ring groove and a machined step under the boot.
    _spin(shaf, org, Y,
          [(0.0, 0.1540), (0.0300, 0.1540), (0.0300, 0.1610), (0.0560, 0.1610),
           (0.0574, 0.1626), (0.0574, 0.1712), (0.0560, 0.1728),
           (0.0492, 0.1740), (0.0492, 0.1782), (0.0510, 0.1800)],
          n=52, xhint=(1, 0, 0))
    _spin(shaf, org, Y,
          [(0.0, 0.176), (0.0480, 0.176), (0.0512, 0.180), (0.0528, 0.192),
           (0.0528, 0.2085), (0.0498, 0.2100), (0.0498, 0.2160),
           (0.0528, 0.2175), (0.0528, 0.236), (0.0512, 0.248),
           (0.0480, 0.256), (0.0424, 0.2620), (0.0400, 0.2640),
           (0.0400, 0.2800), (0.0384, 0.2820), (0.0310, 0.2840)],
          n=52, xhint=(1, 0, 0), rfn=lobe)
    for i in range(6):
        a = TAU * (i + 0.5) / 6.0
        o = org + Y * 0.1540 + Vector((0.0432 * math.cos(a), 0.0,
                                       0.0432 * math.sin(a)))
        _spin(shaf, o, -Y, [(0.0, -0.0070), (0.0088, -0.0070), (0.0088, 0.0),
                            (0.0, 0.0)], n=22, xhint=(1, 0, 0), cap0=False)
        _cap_screw(fast, o - Y * 0.0070, -Y, r_sh=0.0034, length=0.010,
                   head_r=0.0058, head_h=0.0046, xhint=(1, 0, 0))
    # Shaft, with a rolled shoulder beside each boot seat so the small end of a
    # gaiter is retained instead of just resting on plain bar. D: the two
    # 60 mm support cones that used to sit here poked out through the boot
    # valleys (1758 overlapping triangle pairs) and the boots sealed on nothing.
    #
    # D: the bar used to STOP at y=0.524 while the outboard CV started at
    # y=0.574, so the driveshaft was two disconnected islands with exactly
    # 50.00 mm of air between them, bridged by nothing but the rubber gaiter -
    # the largest single break on the car. It now runs to y=0.604, i.e. 30 mm
    # inside the CV's inboard face, which is the same telescopic engagement the
    # inboard tripod already had (shaft 0.254 into a housing that closes at
    # 0.284). It stays under the gaiter's 0.0186 bore the whole way.
    _spin(shaf, org, Y,
          [(0.0, 0.254), (0.0194, 0.256), (0.0194, 0.300), (0.0182, 0.306),
           (0.0182, 0.4040), (0.0208, 0.4080), (0.0208, 0.4140),
           (0.0182, 0.4180), (0.0182, 0.4560), (0.0208, 0.4600),
           (0.0208, 0.4660), (0.0182, 0.4700), (0.0182, 0.5100),
           (0.0194, 0.5140), (0.0194, 0.5220), (0.0182, 0.5254),
           (0.0182, 0.5980), (0.0166, 0.6040), (0.0, 0.6040)],
          n=40, xhint=(1, 0, 0))
    # Outboard joint. It runs through the upright bore into the hub on the
    # assembled car, but on its own it was a 120 mm bare cone, so it gets the
    # same treatment as the inboard end: a splined stub, a circlip groove and a
    # broken corner.
    #
    # D: that stub used to dead-end with a cap at y=0.700, 27.5 mm short of the
    # hub spigot face at y=0.7275 - its nearest neighbour of any kind was the
    # upright bore wall, 3.76 mm away radially, so the driveshaft drove nothing
    # and the rear wheels hung off the hub bearing alone. It now necks down past
    # the upright bore (r 0.0310, ends y=0.7425) and runs on to y=0.7640 as an
    # 0.0184 spigot inside brake_assembly's 0.0180 hub bore - 36.5 mm of
    # engagement at the same 0.4 mm interference that module uses for its own
    # bell-on-hub fit, and still 56 mm clear of the wheel nut at y=0.8205.
    # rfn indexes PROFILE ROWS, so lengthening the tip moved the splined land
    # from rows 2/3 to rows 7/8 - it is still the r=0.0262 band at y 0.676-0.698.
    def spline(kk, t):
        return 0.0006 * (0.5 + 0.5 * math.cos(30.0 * t)) if kk in (7, 8) else 0.0
    _spin(shaf, org, Y,
          [(0.0, 0.7640), (0.0168, 0.7640), (0.0184, 0.7606),
           (0.0184, 0.7286), (0.0196, 0.7256), (0.0244, 0.7160),
           (0.0244, 0.7000), (0.0262, 0.6980),
           (0.0262, 0.6760), (0.0244, 0.6740), (0.0272, 0.6700),
           (0.0272, 0.6620), (0.0500, 0.6520), (0.0540, 0.6400),
           (0.0540, 0.6262), (0.0512, 0.6248), (0.0512, 0.6188),
           (0.0540, 0.6174), (0.0540, 0.6040), (0.0500, 0.5960),
           (0.0400, 0.5930), (0.0400, 0.5780), (0.0384, 0.5760),
           (0.0310, 0.5740)], n=52, xhint=(1, 0, 0), rfn=spline)
    # tell-tale screws over each tripod roller bore
    for a in (0.0, TAU / 3.0, 2.0 * TAU / 3.0):
        n = Vector((math.cos(a), -0.26, math.sin(a))).normalized()
        o = org + Y * 0.1880 + Vector((0.0524 * math.cos(a), 0.0,
                                       0.0524 * math.sin(a)))
        _spin(shaf, o, n, [(0.0, 0.0), (0.0074, 0.0), (0.0074, 0.0024),
                           (0.0, 0.0024)], n=20, xhint=(0, 1, 0), cap0=False)
        _cap_screw(fast, o + n * 0.0024, n, r_sh=0.0026, length=0.008,
                   head_r=0.0044, head_h=0.0036, xhint=(0, 1, 0))

    BORE_A, BORE_B = 0.0404, 0.0186        # bores that seal on the two seats
    WALL_A, WALL_B = 0.0072, 0.0056        # bead thickness at each end
    OUT_A, OUT_B = BORE_A + WALL_A, BORE_B + WALL_B
    GRV = 0.0011                           # rolled clamp groove depth

    def make_boot(ya, yb, cy_a, cy_b, lip_a=0.0140, lip_b=0.0140, nconv=8,
                  amp=0.0100, nseg=44):
        """A moulded CV gaiter: a clamped sealing bead on a real seat at each
        end, `nconv` rounded convolutions between them and a plain return wall
        inside, i.e. a closed shell with a bore, not an open sleeve.

        D: the old boot was capped at each end by a solid flat n-gon - a
        95.6 mm black disc round the tripod neck (7161 mm^2, exposed as a 15 mm
        annulus) and a 27.6 mm lid over a 19.4 mm shaft - so it sealed onto
        nothing. Its folds were 28.3 mm deep on a 15-17 mm pitch, nearly twice
        as deep as long, and abs(w)**0.62 flattened every crest into a disc
        edge: a stack of records. It also stepped ~1.1 mm at s=0.10 and 0.90
        where the convoluted region started and stopped. Folds are now 10 mm on
        a 13.9 mm pitch, pure cosine, and the envelope goes to zero at both
        beads so the surface is continuous.
        """
        d = 1.0 if yb > ya else -1.0
        H = abs(yb - ya)
        sa, sb = lip_a / H, 1.0 - lip_b / H
        ga, gb = abs(cy_a - ya) / H, abs(cy_b - ya) / H

        def rad(s):
            if s <= sa:
                r = OUT_A
            elif s >= sb:
                r = OUT_B
            else:
                u = (s - sa) / (sb - sa)
                r = OUT_A + (OUT_B - OUT_A) * C.smoothstep(u)
                env = min(C.smoothstep(u / 0.10),
                          C.smoothstep((1.0 - u) / 0.10))
                r += amp * env * 0.5 * (1.0 - math.cos(TAU * nconv * u))
            # flat-bottomed clamp groove, wider than the band it carries, so
            # the strap clears the rubber over its whole width
            for g in (ga, gb):
                dz = abs(s - g) * H
                if dz <= 0.0058:
                    r -= GRV
                elif dz < 0.0080:
                    r -= GRV * 0.5 * (1.0 + math.cos(math.pi * (dz - 0.0058)
                                                     / 0.0022))
            return r

        ns = 15 * nconv + 34
        prof = [(BORE_A, 0.0), (rad(0.0) - 0.0016, 0.0),
                (rad(0.0016 / H), 0.0016)]
        for i in range(1, ns):
            s = 0.0016 / H + (1.0 - 0.0016 / H) * i / (ns - 1)
            prof.append((rad(s), H * s))
        prof += [(OUT_B - 0.0014, H), (BORE_B, H), (BORE_B, H - lip_b * 0.8)]
        for i in range(1, 4):
            u = i / 4.0
            prof.append((BORE_B + (BORE_A - BORE_B) * u,
                         (H - lip_b * 0.8) + (lip_a - H + lip_b * 0.8) * u))
        prof.append((BORE_A, lip_a))
        _spin(boot, org + Y * ya, Y * d, prof, n=nseg, xhint=(1, 0, 0),
              loop=True)

    make_boot(0.2650, 0.4040, 0.2720, 0.3970)
    make_boot(0.5930, 0.4700, 0.5860, 0.4770, nconv=7)

    def clamp(y, r, w=0.0050):
        """Worm-drive band clamp: an open annular STRAP sitting in the rolled
        groove of a boot bead.

        D: _spin(cap0=True, cap1=True) on a 4-point ring profile appended a
        full n-gon disc at each end, so every clamp was a solid 95.6 mm puck -
        the largest flat faces in the whole part - and its inner radius was set
        exactly equal to the boot radius at that station, so the two surfaces
        were coincident (2021 overlapping triangle pairs, clamps reading as
        loose washers slid onto the boot).
        """
        _spin(clmp, org, Y, [(r, y - w), (r + 0.0021, y - w + 0.0011),
                             (r + 0.0021, y + w - 0.0011), (r, y + w)],
              n=44, xhint=(1, 0, 0), loop=True)
        ex, ey, ez = _basis(Y, (1, 0, 0))
        c = org + ez * y + ex * (r + 0.0021)
        rings = []
        for du in (-0.0062, 0.0062):
            rings.append([c + ez * du + ex * (0.0028 * a) + ey * (0.0042 * b)
                          for (a, b) in ((-0.2, -1), (1, -1), (1, 1), (-0.2, 1))])
        clmp.tube(rings, cap0=True, cap1=True)

    clamp(0.2720, OUT_A - GRV + 0.0002)
    clamp(0.3970, OUT_B - GRV + 0.0002)
    clamp(0.5860, OUT_A - GRV + 0.0002)
    clamp(0.4770, OUT_B - GRV + 0.0002)

    # ------------------------------------------------------------------ #
    origin = Vector((-1.95, 0.42, 0.34))
    ex = Vector((0.32, -0.95, 0.0)).normalized()
    ez = Vector((0.0, 0.0, 1.0))
    made = []
    for (sfx, m, matname, auto) in (
            ("Arms", carb, "CarbonFibre", 34.0),
            ("RodEnds", rods, "SteelFastener", 32.0),
            ("JamNuts", nuts, "AnodisedRed", 34.0),
            ("Brackets", brak, "Titanium", 34.0),
            ("Fasteners", fast, "SteelFastener", 32.0),
            ("Driveshaft", shaf, "Titanium", 32.0),
            ("Boots", boot, "MatteBlack", 44.0),
            ("Clamps", clmp, "SteelFastener", 32.0)):
        if not m.f:
            continue
        made.append(_emit(f"{NAME}_{tag}_{sfx}", m, matname, coll, origin,
                          ex, ez, mirror, auto=auto))
    return made


def _emit(name, m, matname, coll, origin, ex, ez, mirror, auto=32.0):
    """Store verts in a part-local frame (local X down the arms, local Z on the
    fairing normal) so the shared carbon weave lies IN the broad faces instead
    of being extruded along them into stripes."""
    ex = Vector(ex).normalized()
    ez = Vector(ez)
    ez = (ez - ex * ez.dot(ex)).normalized()
    ey = ez.cross(ex)
    R = Matrix((ex, ey, ez)).transposed()
    o = Vector(origin)
    verts = []
    for p in m.v:
        q = Vector(p) - o
        verts.append((q.dot(ex), q.dot(ey), q.dot(ez)))
    faces = m.f
    if mirror:
        verts = [(v[0], -v[1], v[2]) for v in verts]
        faces = [tuple(reversed(f)) for f in faces]
        D = Matrix.Diagonal((1.0, -1.0, 1.0))
        mat = (Matrix.Translation(Vector((o.x, -o.y, o.z)))
               @ (D @ R @ D).to_4x4())
    else:
        mat = Matrix.Translation(o) @ R.to_4x4()
    ob = C.new_obj(name, verts, faces, coll=coll, smooth=True, auto_smooth=auto)
    ob.matrix_world = mat
    S.assign(ob, matname)
    return ob


def build(coll, ctx=None):
    made = []
    made += _corner("RL", coll, False)
    made += _corner("RR", coll, True)
    return made
