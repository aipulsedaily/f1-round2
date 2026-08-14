"""suspension_front - both front suspension corners, hero close-up detail.

Layout (LEFT corner authored, RIGHT mirrored about y=0)
------------------------------------------------------
Outboard everything hangs off the upright pickups that `brake_assembly`
publishes as LUGS_FRONT: five lugs on a hub at

    (S.FRONT_AXLE, +-(S.FRONT_TYRE_Y - S.UPRIGHT_Y_INSET), S.TYRE_R)

two upper, two lower, one steering-arm.  That module also cuts pass-through
slots in the brake-drum bulkhead at +-10 deg of each lug angle and 86..150 mm
radius, so every leg leaves its rod end running very nearly straight inboard
and only turns for the chassis once it is clear of the drum - that is the
"knee" in each leg path, not a stylistic choice.

Inboard everything lands on the monocoque skin through spec.body_surface_point,
via a locally interpolated copy (`_skin`) because spec's own helper snaps frac
to 1/64 and a bracket pad sampled through it comes out as a staircase.  Pads
bury 7 mm into the nominal skin: monocoque_a fairs the stations lengthwise
with a +-4.5 mm clamp, so a pad that only kissed the nominal surface could end
up floating.

Per corner
    upper wishbone   two aerofoil-faired legs on the two upper lugs
    lower wishbone   ditto on the lower lugs, plus the pushrod pickup gusset
    pushrod          lower-wishbone leg -> rocker, ~34 deg
    track rod        steering lug -> rack exit with a bellows gaiter
    12 rod ends      ball, race, jam nut, cut thread, bolt, washers, nuts
    5 chassis pads   conforming, bolted, with clevis ears
    rocker + damper  on a pedestal saddling the chassis top shoulder

Outboard fastener hardware is deliberately built a few percent under
brake_assembly's own ball/bolt at the same lug, so in the assembled car it
hides inside that geometry instead of z-fighting with it, while the part still
renders complete on its own.
"""

import math

import bpy
from mathutils import Vector

import common as C
import spec as S

NAME = "suspension_front"
TAU = math.pi * 2.0


# --------------------------------------------------------------------------- #
# upright pickups - taken live from brake_assembly when it imports
# --------------------------------------------------------------------------- #

# (deg about the axle, radius, offset along the axle (+ = outboard), pin axis)
LUGS_FALLBACK = ((68.0, 0.108, -0.022, (1.0, 0.0, 0.0)),
                 (112.0, 0.108, -0.022, (1.0, 0.0, 0.0)),
                 (292.0, 0.103, -0.018, (1.0, 0.0, 0.0)),
                 (248.0, 0.103, -0.018, (1.0, 0.0, 0.0)),
                 (346.0, 0.100, -0.034, (0.0, 0.0, 1.0)))


def _lugs():
    try:
        import importlib
        ba = importlib.import_module("brake_assembly")
        lugs = getattr(ba, "LUGS_FRONT", None)
        if lugs and len(lugs) == 5:
            return tuple(lugs)
    except Exception:
        pass
    return LUGS_FALLBACK


HUB = Vector((S.FRONT_AXLE, S.FRONT_TYRE_Y - S.UPRIGHT_Y_INSET, S.TYRE_R))
DRUM_BULKHEAD_Y = HUB.y - 0.085      # brake_assembly _drum_profile ax0, front


def _lug_point(entry):
    deg, r, ax, pin = entry
    th = math.radians(deg)
    return (Vector((HUB.x + r * math.cos(th), HUB.y + ax, HUB.z + r * math.sin(th))),
            Vector(pin).normalized())


# --------------------------------------------------------------------------- #
# chassis anchors - (station x, profile frac) on the monocoque half section
# --------------------------------------------------------------------------- #

UP_F_ANCHOR = (1.955, 0.7810)        # upper wishbone, forward leg
UP_R_ANCHOR = (1.520, 0.5470)        # upper wishbone, rear leg
LO_F_ANCHOR = (1.975, 0.2190)        # lower wishbone, forward leg
LO_R_ANCHOR = (1.500, 0.2190)        # lower wishbone, rear leg
TR_ANCHOR = (1.905, 0.4380)          # steering rack exit
ROCKER_ANCHOR = (1.588, 0.8250)      # rocker pedestal saddle
DAMPER_ANCHOR = (1.688, 0.8750)      # damper front foot

STANDOFF = 0.0500                    # joint centre above the nominal skin
PAD_SINK = 0.0070                    # pad inner face below the nominal skin

KNEE_Y = 0.6540                      # leg turns for the chassis only once clear
KNEE_G = 0.30                        # of the drum bulkhead at 0.6775

# rod-end hardware stack, distance from the ball centre along the leg
J_NECK0, J_NECK1 = 0.0090, 0.0285    # rod-end body neck
J_THR0, J_THR1 = 0.0268, 0.0620      # cut thread
J_JAM0, J_JAM1 = 0.0452, 0.0530      # jam nut
J_SOCK0, J_SOCK1 = 0.0562, 0.0985    # bonded socket over the fairing
J_FAIR = 0.0840                      # fairing end cap

BALL_R = 0.00920
RACE_BORE = 0.00945
RACE_R = 0.01580
RACE_W = 0.00620

# through-bolt stack, measured from the ball centre along the pin
B_WASH0, B_WASH1 = 0.00790, 0.00920
B_EAR0, B_EAR1 = 0.00950, 0.01670
B_NUT0 = 0.01700
B_NUT_H = 0.00600
B_HEAD_H = 0.00720
B_SHANK = 0.00485
B_WASH_R = 0.01060


# --------------------------------------------------------------------------- #
# small maths
# --------------------------------------------------------------------------- #

def _basis(w, xhint=(1.0, 0.0, 0.0)):
    w = Vector(w).normalized()
    u = Vector(xhint)
    u = u - w * u.dot(w)
    if u.length < 1e-7:
        u = Vector((0.0, 0.0, 1.0))
        u = u - w * u.dot(w)
        if u.length < 1e-7:
            u = Vector((0.0, 1.0, 0.0))
            u = u - w * u.dot(w)
    u.normalize()
    return u, w.cross(u), w


def _poly_r(theta, sides, rc, rot=0.0):
    """Radius of a regular polygon (circumradius rc) at angle theta."""
    step = TAU / sides
    a = (theta - rot) % step
    return rc * math.cos(step * 0.5) / math.cos(a - step * 0.5)


def _sell(ha, hb, e, n):
    """Superellipse ring: e=1 ellipse, e<1 boxy."""
    out = []
    for i in range(n):
        t = TAU * i / n
        ct, st = math.cos(t), math.sin(t)
        out.append((ha * math.copysign(abs(ct) ** e, ct),
                    hb * math.copysign(abs(st) ** e, st)))
    return out


def _afoil(tc, nu=30, nte=9, u_te=0.965):
    """Closed (u, v) contour, LE -> upper -> TE -> lower.

    v is normalised so the full thickness is 1.0: multiply u by chord and v by
    thickness.  tc = thickness/chord, used only to keep the trailing-edge cap
    round in real space rather than in parameter space.
    """
    def yt(u):
        u = max(0.0, min(1.0, u))
        return 5.0 * (0.2969 * math.sqrt(u) - 0.1260 * u - 0.3516 * u * u
                      + 0.2843 * u ** 3 - 0.1015 * u ** 4)

    us = [0.5 * (1.0 - math.cos(math.pi * i / (nu - 1))) * u_te for i in range(nu)]
    up = [(u, yt(u)) for u in us]
    vte = yt(u_te)
    cap = []
    for k in range(1, nte - 1):
        ph = math.pi * k / (nte - 1)
        cap.append((u_te + vte * tc * math.sin(ph), vte * math.cos(ph)))
    lo = [(u, -yt(u)) for u in reversed(us[1:-1])]
    return up + cap + lo


def _to_circle(pts, ca, r, t):
    """Blend a star-shaped 2D contour towards a circle of radius r about ca."""
    if t <= 0.0:
        return list(pts)
    out = []
    for (a, b) in pts:
        ang = math.atan2(b, a - ca)
        ta, tb = ca + r * math.cos(ang), r * math.sin(ang)
        out.append((a + (ta - a) * t, b + (tb - b) * t))
    return out


# --------------------------------------------------------------------------- #
# skin sampling - smooth in frac, unlike spec's 1/64-snapped helper
# --------------------------------------------------------------------------- #

_SKIN_CACHE = {}
_SKIN_NS = 401


def _skin_curve(x):
    key = round(x, 5)
    c = _SKIN_CACHE.get(key)
    if c is None:
        c = C.catmull_rom(S.station_half(S.station_at(x)), _SKIN_NS)
        _SKIN_CACHE[key] = c
    return c


def _skin_yz(x, frac):
    c = _skin_curve(x)
    f = max(0.0, min(1.0, frac)) * (_SKIN_NS - 1)
    i = min(int(f), _SKIN_NS - 2)
    t = f - i
    (y0, z0), (y1, z1) = c[i], c[i + 1]
    return (y0 + (y1 - y0) * t, z0 + (z1 - z0) * t)


def _skin(x, frac):
    """Point on the monocoque half section plus its outward unit normal."""
    y, z = _skin_yz(x, frac)
    d = 0.012
    y0, z0 = _skin_yz(x, max(0.0, frac - d))
    y1, z1 = _skin_yz(x, min(1.0, frac + d))
    ty, tz = y1 - y0, z1 - z0
    L = math.hypot(ty, tz) or 1.0
    return Vector((x, y, z)), Vector((0.0, tz / L, -ty / L))


def _anchor(a, out=STANDOFF):
    p, n = _skin(a[0], a[1])
    return p + n * out


# --------------------------------------------------------------------------- #
# mesh accumulator
# --------------------------------------------------------------------------- #

class _M:
    def __init__(self):
        self.v = []
        self.f = []

    def ring(self, pts):
        i0 = len(self.v)
        for p in pts:
            self.v.append((float(p[0]), float(p[1]), float(p[2])))
        return list(range(i0, len(self.v)))

    def bridge(self, a, b, closed=True):
        n = len(a)
        span = n if closed else n - 1
        for j in range(span):
            k = (j + 1) % n
            self.f.append((a[j], a[k], b[k], b[j]))

    def loft(self, rings, closed=True, cap0=False, cap1=False):
        idx = [self.ring(r) for r in rings]
        for i in range(len(idx) - 1):
            self.bridge(idx[i], idx[i + 1], closed)
        if cap0:
            self.f.append(tuple(reversed(idx[0])))
        if cap1:
            self.f.append(tuple(idx[-1]))
        return idx

    # ---- solids ---------------------------------------------------------- #

    def spin(self, origin, axis, profile, n=40, xhint=(1.0, 0.0, 0.0),
             loop=False, cap0=None, cap1=None):
        """Revolve a (radius, height) profile about `axis` through `origin`."""
        o = Vector(origin)
        u, v, w = _basis(axis, xhint)
        cs = [(math.cos(TAU * i / n), math.sin(TAU * i / n)) for i in range(n)]
        rings = []
        for (r, h) in profile:
            base = o + w * h
            rings.append([base + u * (r * c) + v * (r * s) for (c, s) in cs])
        if loop:
            cap0 = cap1 = False
        if cap0 is None:
            cap0 = profile[0][0] > 1e-6
        if cap1 is None:
            cap1 = profile[-1][0] > 1e-6
        self.loft(rings, closed=True, cap0=cap0, cap1=cap1)

    def prism(self, poly, org, ea, eb, h0, h1, ew, ch=0.0012):
        """Extrude a closed 2D polygon (in the ea/eb plane) along ew."""
        org, ea, eb, ew = Vector(org), Vector(ea), Vector(eb), Vector(ew)
        cx = sum(p[0] for p in poly) / len(poly)
        cy = sum(p[1] for p in poly) / len(poly)
        rad = sum(math.hypot(p[0] - cx, p[1] - cy) for p in poly) / len(poly)
        k = max(0.0, 1.0 - ch / max(rad, 1e-5))

        def ring(scale, h):
            return [org + ea * (cx + (p[0] - cx) * scale) +
                    eb * (cy + (p[1] - cy) * scale) + ew * h for p in poly]

        self.loft([ring(k, h0), ring(1.0, h0 + ch),
                   ring(1.0, h1 - ch), ring(k, h1)],
                  closed=True, cap0=True, cap1=True)

    def thread(self, origin, axis, r_crest, depth, length, pitch,
               n=26, per_pitch=4, xhint=(1.0, 0.0, 0.0)):
        """A real helical cut thread: the crest is a helix, not stacked rings."""
        o = Vector(origin)
        u, v, w = _basis(axis, xhint)
        nr = max(6, int(round(length / pitch * per_pitch)))
        cs = [(math.cos(TAU * i / n), math.sin(TAU * i / n)) for i in range(n)]
        rings = []
        for j in range(nr + 1):
            h = length * j / nr
            base = o + w * h
            ring = []
            for i, (c, s) in enumerate(cs):
                p = ((h - pitch * i / n) / pitch) % 1.0
                cut = min(1.0, max(0.0, (abs(2.0 * p - 1.0) - 0.16) / 0.68))
                e = min(1.0, j / 2.0, (nr - j) / 2.0)      # run-out at both ends
                r = r_crest - depth * (cut * e + (1.0 - e) * 0.5)
                ring.append(base + u * (r * c) + v * (r * s))
            rings.append(ring)
        self.loft(rings, closed=True, cap0=True, cap1=True)

    def hexnut(self, origin, axis, af, height, bore, n=36,
               xhint=(1.0, 0.0, 0.0), rot=0.0, sides=6):
        """Hex nut / bolt head with the usual conical corner chamfers."""
        rc = af / (2.0 * math.cos(math.pi / sides))
        rf = af * 0.5
        ch = rc - rf
        o = Vector(origin)
        u, v, w = _basis(axis, xhint)
        h2 = height * 0.5

        def ring(h, cap_r):
            out = []
            for i in range(n):
                t = TAU * i / n
                r = _poly_r(t, sides, rc, rot)
                if cap_r is not None:
                    r = min(r, cap_r)
                out.append(o + w * h + u * (r * math.cos(t)) + v * (r * math.sin(t)))
            return out

        def circ(h, r):
            return [o + w * h + u * (r * math.cos(TAU * i / n))
                    + v * (r * math.sin(TAU * i / n)) for i in range(n)]

        body = [ring(-h2, rf), ring(-h2 + ch, None),
                ring(h2 - ch, None), ring(h2, rf)]
        if bore > 1e-5:
            rings = [circ(-h2, bore)] + body + [circ(h2, bore), circ(-h2, bore)]
            self.loft(rings, closed=True, cap0=False, cap1=False)
        else:
            self.loft(body, closed=True, cap0=True, cap1=True)

    def washer(self, origin, axis, r_out, r_in, h0, h1, n=32, xhint=(1, 0, 0)):
        ch = 0.00035
        self.spin(origin, axis,
                  [(r_in, h0), (r_out - ch, h0), (r_out, h0 + ch),
                   (r_out, h1 - ch), (r_out - ch, h1), (r_in, h1), (r_in, h0)],
                  n=n, xhint=xhint, loop=True)


def _emit(m, name, matname, sy, coll, auto=34.0):
    if sy > 0:
        verts, faces = m.v, m.f
    else:
        verts = [(x, -y, z) for (x, y, z) in m.v]
        faces = [tuple(reversed(f)) for f in m.f]
    ob = C.new_obj(name, verts, faces, coll=coll, smooth=True)
    C.merge_doubles(ob, 2e-5)
    C.shade_auto_smooth(ob, auto)
    S.assign(ob, matname)
    return ob


# --------------------------------------------------------------------------- #
# paths
# --------------------------------------------------------------------------- #

def _leg_path(p_out, p_in, knee_y=KNEE_Y, g=KNEE_G, samples=180):
    """Rod-end centre to rod-end centre, with the outboard knee."""
    p_out, p_in = Vector(p_out), Vector(p_in)
    d = p_in - p_out
    if knee_y is None or abs(d.y) < 1e-6:
        return [p_out + d * (i / (samples - 1.0)) for i in range(samples)]
    fy = (knee_y - p_out.y) / d.y
    knee = Vector((p_out.x + d.x * fy * g, knee_y, p_out.z + d.z * fy * g))
    raw = C.catmull_rom([tuple(p_out), tuple(knee), tuple(p_in)], samples)
    return [Vector(p) for p in raw]


def _arclen(pts):
    cum = [0.0]
    for i in range(1, len(pts)):
        cum.append(cum[-1] + (pts[i] - pts[i - 1]).length)
    return cum


def _at(pts, cum, d):
    d = max(0.0, min(cum[-1], d))
    lo, hi = 0, len(cum) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if cum[mid] <= d:
            lo = mid
        else:
            hi = mid
    span = cum[hi] - cum[lo]
    t = 0.0 if span < 1e-12 else (d - cum[lo]) / span
    return pts[lo] + (pts[hi] - pts[lo]) * t


def _tan(pts, cum, d):
    e = 0.005
    a = _at(pts, cum, max(0.0, d - e))
    b = _at(pts, cum, min(cum[-1], d + e))
    return (b - a).normalized()


def _frame(tangent, alpha=0.0):
    """Chord axis (pointing aft) and thickness axis for a streamwise fairing."""
    t = Vector(tangent).normalized()
    ec = Vector((-1.0, 0.0, 0.0))
    ec = ec - t * ec.dot(t)
    if ec.length < 1e-6:
        ec = Vector((0.0, 0.0, -1.0))
        ec = ec - t * ec.dot(t)
    ec.normalize()
    en = ec.cross(t).normalized()
    if alpha:
        ca, sa = math.cos(alpha), math.sin(alpha)
        ec, en = ec * ca + en * sa, en * ca - ec * sa
    return ec, en


# --------------------------------------------------------------------------- #
# aerofoil fairing + bonded end socket
# --------------------------------------------------------------------------- #

# a bonded clamshell fairing carries a fine moulding seam along its leading
# edge; without it an 85 mm blank blade behaves as one flat mirror
_LE_BEAD = {0: 0.00042, 1: 0.00024, 2: 0.00009, -1: 0.00024, -2: 0.00009}


def _grow(pts, ca, amount):
    if not amount:
        return pts
    out = []
    for (a, b) in pts:
        da, db = a - ca, b
        L = math.hypot(da, db) or 1.0
        out.append((a + da / L * amount, b + db / L * amount))
    return out


def _ring_from_sect(qc, ec, en, chord, thick, morph=0.0, r_circ=0.0,
                    grow=0.0, bead=False):
    contour = _afoil(thick / max(chord, 1e-6))
    ca = 0.17 * chord
    pts = [((u - 0.25) * chord, v * thick) for (u, v) in contour]
    if morph > 0.0:
        pts = _to_circle(pts, ca, r_circ, morph)
    elif bead:
        n = len(pts)
        out = list(pts)
        for key, amt in _LE_BEAD.items():
            i = key % n
            a, b = pts[i]
            da, db = a - ca, b
            L = math.hypot(da, db) or 1.0
            out[i] = (a + da / L * amt, b + db / L * amt)
        pts = out
    pts = _grow(pts, ca, grow)
    return [qc + ec * a + en * b for (a, b) in pts]


def _fairing(m, pts, cum, d0, d1, sect, alpha, nring=34):
    rings = []
    for i in range(nring):
        s = i / (nring - 1.0)
        d = d0 + (d1 - d0) * s
        chord, thick = sect(d)
        qc = _at(pts, cum, d)
        ec, en = _frame(_tan(pts, cum, d), alpha)
        rings.append(_ring_from_sect(qc, ec, en, chord, thick, bead=True))
    m.loft(rings, closed=True, cap0=True, cap1=True)


def _socket(m, pts, cum, d_near, d_far, sect, alpha, r_sock=0.0113, nring=11):
    """Bonded titanium end socket: fairing section morphing to a round spigot.

    Over the length that overlaps the fairing the socket keeps the fairing's
    own section and only stands 1.1 mm proud of it - morphing towards the
    circle inside the overlap pulled the trailing edge *under* the carbon and
    the two surfaces z-fought, which showed as torn stripes in the weave.
    """
    sgn = 1.0 if d_near > d_far else -1.0
    c_n, t_n = sect(d_near)
    lip = 0.00110
    steps = [(d_far, 0.0, 0.00014), (d_far, 0.0, lip)]
    for i in range(1, nring + 1):
        s = i / float(nring)
        d = d_far + (d_near - d_far) * s
        tm = C.smoothstep(max(0.0, s - 0.32) / 0.62)
        steps.append((d, tm, lip * (1.0 - 0.90 * tm)))
    steps.append((d_near + sgn * 0.0030, 1.0, 0.0))
    steps.append((d_near + sgn * 0.0043, 1.0, -0.0013))

    rings = []
    for (d, t, g) in steps:
        chord, thick = sect(d)
        if t >= 1.0:
            chord, thick = c_n, t_n
        qc = _at(pts, cum, d)
        ec, en = _frame(_tan(pts, cum, d), alpha)
        rings.append(_ring_from_sect(qc, ec, en, chord, thick,
                                     morph=t, r_circ=r_sock, grow=g))
    m.loft(rings, closed=True, cap0=True, cap1=True)


# --------------------------------------------------------------------------- #
# rod-end joint
# --------------------------------------------------------------------------- #

def _pin_bolt(mst, centre, pin, k=1.0, hint=(1.0, 0.0, 0.0), thread_stub=True):
    """Washers, shank, head and nut clamping a rod end into a clevis."""
    centre, pin = Vector(centre), Vector(pin).normalized()
    for sgn in (-1.0, 1.0):
        mst.washer(centre + pin * (sgn * B_WASH0 * k), pin * sgn,
                   B_WASH_R * k, 0.00510 * k, 0.0, (B_WASH1 - B_WASH0) * k,
                   n=32, xhint=hint)
    half = (B_NUT0 + B_NUT_H) * k
    mst.spin(centre - pin * half, pin,
             [(B_SHANK * k, 0.0), (B_SHANK * k, 2.0 * half)],
             n=26, xhint=hint, cap0=False, cap1=False)
    # hex head one side, nut the other
    mst.hexnut(centre + pin * ((B_NUT0 + B_HEAD_H * 0.5) * k), pin,
               0.01560 * k, B_HEAD_H * k, 0.00515 * k, n=36, xhint=hint)
    mst.hexnut(centre - pin * ((B_NUT0 + B_NUT_H * 0.5) * k), pin,
               0.01440 * k, B_NUT_H * k, 0.00515 * k, n=36, xhint=hint)
    mst.spin(centre + pin * ((B_NUT0 + B_HEAD_H) * k), pin,
             [(0.0, 0.0), (B_SHANK * k, 0.0)], n=26, xhint=hint)
    if thread_stub:
        mst.thread(centre - pin * ((B_NUT0 + B_NUT_H) * k + 0.0043 * k), -pin,
                   B_SHANK * k, 0.00075 * k, 0.0043 * k, 0.0013 * k,
                   n=24, per_pitch=4, xhint=hint)
    else:
        mst.spin(centre - pin * ((B_NUT0 + B_NUT_H) * k), pin,
                 [(0.0, 0.0), (B_SHANK * k, 0.0)], n=26, xhint=hint)


def _ball_and_race(mti, mst, centre, pin, hint, k=1.0, shrink=1.0):
    br = BALL_R * k * shrink
    bore = 0.00500 * k
    hh = math.sqrt(max(br * br - bore * bore, 1e-9))
    th = math.asin(min(1.0, bore / br))
    prof = [(bore, -hh)]
    NB = 16
    for i in range(NB + 1):
        a = -(math.pi * 0.5 - th) + (math.pi - 2.0 * th) * i / NB
        prof.append((br * math.cos(a), br * math.sin(a)))
    prof.append((bore, hh))
    prof.append((bore, -hh))
    mst.spin(centre, pin, prof, n=36, xhint=hint, loop=True)

    ch = 0.00100 * k
    lip = 0.00110 * k
    rb, rr, rw = RACE_BORE * k, RACE_R * k, RACE_W * k
    mti.spin(centre, pin,
             [(rb, -rw), (rb + lip, -rw - lip * 0.55),
              (rr - ch, -rw - lip * 0.55), (rr, -rw - lip * 0.55 + ch),
              (rr, rw + lip * 0.55 - ch), (rr - ch, rw + lip * 0.55),
              (rb + lip, rw + lip * 0.55), (rb, rw), (rb, -rw)],
             n=40, xhint=hint, loop=True)


def _rod_end(mti, mst, mrd, centre, pin, out_dir, k=1.0, upright=False):
    """Ball, race, neck, thread, jam nut and through-bolt at one joint.

    `out_dir` points from the ball centre along the leg, away from the joint.
    """
    centre = Vector(centre)
    pin = Vector(pin).normalized()
    od = Vector(out_dir).normalized()
    hint = od - pin * od.dot(pin)
    if hint.length < 1e-6:
        hint = Vector((0.0, 0.0, 1.0))
    hint = hint.normalized()

    _ball_and_race(mti, mst, centre, pin, hint, k=k,
                   shrink=0.9946 if upright else 1.0)

    # ---- neck: race -> round shank ---------------------------------------- #
    necks = []
    NN = 8
    u, v, w = _basis(od, pin)
    for i in range(NN):
        s = i / (NN - 1.0)
        d = (J_NECK0 + (J_NECK1 - J_NECK0) * s) * k
        ha = (0.0068 + (0.0081 - 0.0068) * s) * k
        hb = (0.0154 + (0.0081 - 0.0154) * s) * k
        e = 0.56 + 0.44 * C.smoothstep(s)
        base = centre + od * d
        necks.append([base + u * a + v * b for (a, b) in _sell(ha, hb, e, 36)])
    mti.loft(necks, closed=True, cap0=True, cap1=True)

    # ---- cut thread, jam nut ---------------------------------------------- #
    mst.thread(centre + od * (J_THR0 * k), od, 0.00800 * k, 0.00105 * k,
               (J_THR1 - J_THR0) * k, 0.00150 * k, n=26, per_pitch=4, xhint=pin)
    mrd.hexnut(centre + od * ((J_JAM0 + J_JAM1) * 0.5 * k), od,
               0.01920 * k, (J_JAM1 - J_JAM0) * k, 0.00815 * k, n=36, xhint=pin)

    # ---- through bolt ------------------------------------------------------ #
    if upright:
        # deliberately tucked inside brake_assembly's own bolt at this lug
        hs = 0.0226
        mst.spin(centre - pin * hs, pin,
                 [(0.0, 0.0), (0.0086, 0.0), (0.0091, 0.0006), (0.0091, 0.0044),
                  (0.0086, 0.0050), (0.0048, 0.0050), (0.0048, 2 * hs - 0.0050),
                  (0.0086, 2 * hs - 0.0050), (0.0091, 2 * hs - 0.0044),
                  (0.0091, 2 * hs - 0.0006), (0.0086, 2 * hs), (0.0, 2 * hs)],
                 n=32, xhint=hint)
        mst.spin(centre - pin * (hs - 0.0002), pin,
                 [(0.0, 0.0), (0.0040, 0.0), (0.0040, 0.0028), (0.0, 0.0028)],
                 n=6, xhint=hint)
    else:
        _pin_bolt(mst, centre, pin, k=k, hint=hint)


# --------------------------------------------------------------------------- #
# chassis brackets
# --------------------------------------------------------------------------- #

def _map_uv(t, k=0.62, e=0.55):
    """Unit square -> rounded rectangle (squircle) at parameter angle t."""
    c, s = math.cos(t), math.sin(t)
    u = math.copysign(abs(c) ** e, c)
    v = math.copysign(abs(s) ** e, s)
    return (u * math.sqrt(max(0.0, 1.0 - k * v * v)),
            v * math.sqrt(max(0.0, 1.0 - k * u * u)))


def _pad_outline(n=68):
    return [_map_uv(TAU * i / n) for i in range(n)]


def _dsdf(x, f):
    """Arc length of the half section per unit frac, near frac f."""
    d = 0.010
    f0, f1 = max(0.0, f - d), min(1.0, f + d)
    y0, z0 = _skin_yz(x, f0)
    y1, z1 = _skin_yz(x, f1)
    return math.hypot(y1 - y0, z1 - z0) / max(f1 - f0, 1e-9)


def _pad_frac(ax, harc):
    """frac half-extent that spans `harc` metres of skin at this anchor."""
    return harc / max(_dsdf(ax[0], ax[1]), 1e-6)


PAD_FLANGE = 0.0092                  # rim thickness
PAD_BOSS = 0.0170                    # raised centre the ears stand on


def _pad(m, ax, hx, harc, t_flange=PAD_FLANGE, t_boss=PAD_BOSS,
         sink=PAD_SINK, n=68):
    """Conforming bracket pad, bonded and bolted to the monocoque skin.

    Two levels: a thin bolted flange and a raised machined boss carrying the
    clevis ears, so the visible face is never one big blank curved slab.
    """
    x0, f0 = ax
    hf = _pad_frac(ax, harc)
    outline = _pad_outline(n)
    ch = 0.0013
    a_p, a_n = _skin(x0, f0)

    def ring(scale, off, flat=False):
        pts = []
        for (u, v) in outline:
            p, nn = _skin(x0 + hx * u * scale, f0 + hf * v * scale)
            if flat:
                # the boss the clevis ears bolt to is a machined FLAT face, not
                # a skin-parallel offset: a flat ear foot meeting a curved boss
                # intersects at a grazing angle and combs badly under zoom
                d = p - a_p
                pts.append(a_p + a_n * off + (d - a_n * d.dot(a_n)))
            else:
                pts.append(p + nn * off)
        return pts

    b = -sink
    T1, T2 = t_flange - sink, t_boss - sink
    m.loft([ring(0.0, b), ring(0.36, b), ring(0.68, b), ring(0.90, b),
            ring(0.975, b), ring(1.0, b + ch), ring(1.0, T1 - ch),
            ring(0.975, T1), ring(0.930, T1), ring(0.900, T1 + ch),
            ring(0.900, T2 - ch * 1.4, flat=True),
            ring(0.860, T2, flat=True), ring(0.52, T2, flat=True),
            ring(0.0, T2, flat=True)],
           closed=True, cap0=False, cap1=False)
    return hf


# bolt spots are (parameter angle deg, radial fraction of the outline) so they
# always land on the flange band, whatever the pad's aspect ratio
DEF_SPOTS = ((25.0, 0.70), (155.0, 0.70), (205.0, 0.70), (335.0, 0.70))


def _pad_bolts(mst, ax, hx, harc, thick=PAD_FLANGE, spots=DEF_SPOTS):
    x0, f0 = ax
    hf = _pad_frac(ax, harc)
    for (ang, rad) in spots:
        u, v = _map_uv(math.radians(ang))
        u, v = u * rad, v * rad
        p, nn = _skin(x0 + hx * u, f0 + hf * v)
        base = p + nn * (thick - PAD_SINK)
        mst.washer(base, nn, 0.00680, 0.00300, -0.00030, 0.00110, n=28)
        mst.hexnut(base + nn * 0.00130, nn, 0.00920, 0.00370, 0.0, n=36)


def _ear_outline(rb=0.0150, hgt=0.0390, fw=0.0225, na=26, base=-0.0060):
    pts = [(-fw, base), (-fw * 0.93, base + 0.0115), (-fw * 0.78, base + 0.0210)]
    a0, a1 = math.radians(232.0), math.radians(-52.0)
    for i in range(na + 1):
        a = a0 + (a1 - a0) * i / na
        pts.append((rb * math.cos(a), hgt + rb * math.sin(a)))
    pts += [(fw * 0.78, base + 0.0210), (fw * 0.93, base + 0.0115), (fw, base)]
    return pts


def _fork(m, org, ea, eb, pin, hgt, rb=0.0150, fw=0.0195, k=1.0, ch=0.0011,
          axoff=0.0, base=-0.0155):
    """Two clevis ears straddling a joint `hgt` above `org`.

    `axoff` is the joint's offset along the pin from `org`: without it the ear
    gap is centred on the pad rather than on the ball, and the near ear eats
    into the rod-end race.
    """
    poly = _ear_outline(rb=rb, hgt=hgt, fw=fw, base=base)
    centre = Vector(org) + Vector(eb) * hgt + Vector(pin) * axoff
    step = 0.0021
    for sgn in (-1.0, 1.0):
        i0, i1 = B_EAR0 * k, B_EAR1 * k - step
        a, b = ((axoff + i0, axoff + i1) if sgn > 0 else
                (axoff - i1, axoff - i0))
        m.prism(poly, org, ea, eb, a, b, pin, ch=ch)
        # raised bearing boss the washer and nut actually land on: without it
        # the ear is a 30 x 45 mm blank plate
        # start 0.8 mm inside the plate: a boss base disc exactly on the
        # plate's cap plane is two coplanar faces and combs under zoom
        m.spin(centre + Vector(pin) * (sgn * (i1 - 0.0008)), Vector(pin) * sgn,
               [(0.0, 0.0), (rb - 0.0013, 0.0),
                (rb - 0.0013, step - 0.0001), (rb - 0.0021, step + 0.0008)],
               n=40, xhint=eb)


def _stand(org, target, pin):
    """(ea, eb, height, axial offset) for a fork standing at `org`."""
    pin = Vector(pin).normalized()
    v = Vector(target) - Vector(org)
    axoff = v.dot(pin)
    vp = v - pin * axoff
    hgt = vp.length
    eb = vp / hgt if hgt > 1e-9 else Vector((0.0, 0.0, 1.0))
    return eb.cross(pin).normalized(), eb, hgt, axoff


def _clevis(mti, mst, ax, pin, hx=0.044, harc=0.034, standoff=STANDOFF,
            spots=DEF_SPOTS, k=1.0, fw=0.0195):
    """Pad + two clevis ears + pad fasteners; returns the joint centre."""
    p, nn = _skin(ax[0], ax[1])
    centre = p + nn * standoff
    pin = Vector(pin).normalized()
    org = p + nn * (PAD_BOSS - PAD_SINK)
    ea, eb, hgt, axoff = _stand(org, centre, pin)

    _pad(mti, ax, hx, harc)
    _pad_bolts(mst, ax, hx, harc, spots=spots)
    _fork(mti, org, ea, eb, pin, hgt, rb=0.0150 * k, fw=fw, k=k, axoff=axoff)
    return centre


# --------------------------------------------------------------------------- #
# one link
# --------------------------------------------------------------------------- #

def _sect_fn(d0, d1, c_end, c_mid, t_end, t_mid, ramp=0.245):
    """Chord/thickness along a link.

    A sin(pi*s) bulge turns the arm into a pointed lens; a real faired wishbone
    holds its chord over most of the span and only necks down over the last
    ~15% into the end socket.
    """
    span = max(d1 - d0, 1e-6)

    def sect(d):
        s = max(0.0, min(1.0, (d - d0) / span))
        w = C.smoothstep(min(s, 1.0 - s) / ramp)
        g = 0.945 + 0.11 * s                    # a touch wider inboard
        return (c_end + (c_mid * g - c_end) * w,
                t_end + (t_mid * (0.97 + 0.06 * s) - t_end) * w)
    return sect


def _leg(mcf, mti, mst, mrd, p_out, pin_out, p_in, pin_in, alpha,
         c_mid, t_mid, c_end=0.0300, t_end=0.0212, nring=44, k=1.0,
         knee_y=KNEE_Y, upright_out=True, report=None, tag=""):
    """One faired suspension link, rod end to rod end."""
    pts = _leg_path(p_out, p_in, knee_y=knee_y)
    cum = _arclen(pts)
    L = cum[-1]
    d0, d1 = J_FAIR * k, L - J_FAIR * k
    sect = _sect_fn(d0, d1, c_end, c_mid, t_end, t_mid)

    _fairing(mcf, pts, cum, d0, d1, sect, alpha, nring=nring)
    _socket(mti, pts, cum, J_SOCK0 * k, J_SOCK1 * k, sect, alpha,
            r_sock=0.0113 * k)
    _socket(mti, pts, cum, L - J_SOCK0 * k, L - J_SOCK1 * k, sect, alpha,
            r_sock=0.0113 * k)
    _rod_end(mti, mst, mrd, p_out, pin_out, _tan(pts, cum, 0.0), k=k,
             upright=upright_out)
    _rod_end(mti, mst, mrd, p_in, pin_in, -_tan(pts, cum, L), k=k,
             upright=False)
    if report is not None:
        report.append((tag, pts, cum))
    return pts, cum


def _pushrod_gusset(mti, mst, leg_pts, leg_cum, d, foot, pin):
    """Clamp collar on the wishbone leg carrying the pushrod clevis."""
    o = _at(leg_pts, leg_cum, d)
    t = _tan(leg_pts, leg_cum, d)
    foot, pin = Vector(foot), Vector(pin).normalized()
    u, v, w = _basis(t, pin)

    mti.spin(o - t * 0.0190, t,
             [(0.0118, 0.0), (0.0143, 0.0), (0.0147, 0.0016), (0.0147, 0.0330),
              (0.0143, 0.0346), (0.0118, 0.0346), (0.0118, 0.0)],
             n=40, xhint=pin, loop=True)
    for dd in (-0.0110, 0.0080):
        pos = o + t * dd
        for sgn in (-1.0, 1.0):
            mst.hexnut(pos + u * (sgn * 0.0158), u * sgn, 0.0094, 0.0038,
                       0.0027, n=30, xhint=t)
        mst.spin(pos - u * 0.0180, u, [(0.0027, 0.0), (0.0027, 0.0360)],
                 n=20, xhint=t, cap0=False, cap1=False)

    ea, eb, hgt, axoff = _stand(o, foot, pin)
    _fork(mti, o, ea, eb, pin, hgt, rb=0.0148, fw=0.0138, axoff=axoff,
          base=-0.0165)


# --------------------------------------------------------------------------- #
# rocker + damper
# --------------------------------------------------------------------------- #

def _rocker(mti, mst, mrd, mbk, piv, axis, ph, pd):
    piv, ph, pd = Vector(piv), Vector(ph), Vector(pd)
    axis = Vector(axis).normalized()

    # ---- pedestal saddle --------------------------------------------------- #
    RPX, RPA = 0.078, 0.060
    _pad(mti, ROCKER_ANCHOR, RPX, RPA, t_flange=0.0104, t_boss=0.0200)
    _pad_bolts(mst, ROCKER_ANCHOR, RPX, RPA, thick=0.0104,
               spots=((0.0, 0.74), (180.0, 0.74), (90.0, 0.74), (270.0, 0.74),
                      (36.0, 0.86), (144.0, 0.86), (216.0, 0.86), (324.0, 0.86)))
    p, nn = _skin(*ROCKER_ANCHOR)
    org = p + nn * (0.0200 - PAD_SINK)
    ea, eb, hgt, axoff = _stand(org, piv, axis)
    cheek = _ear_outline(rb=0.0215, hgt=hgt, fw=0.0300, base=-0.0190)
    for sgn in (-1.0, 1.0):
        a, b = ((axoff + 0.0250, axoff + 0.0346) if sgn > 0 else
                (axoff - 0.0346, axoff - 0.0250))
        mti.prism(cheek, org, ea, eb, a, b, axis, ch=0.0013)
        mti.spin(piv + axis * (sgn * 0.0338), axis * sgn,
                 [(0.0, 0.0), (0.0198, 0.0), (0.0198, 0.0026), (0.0189, 0.0034)],
                 n=40, xhint=eb)

    # ---- pivot pin: solid, socket head one side, castle nut the other ----- #
    mst.spin(piv - axis * 0.0344, axis,
             [(0.0, 0.0), (0.0110, 0.0), (0.0110, 0.0688), (0.0, 0.0688)],
             n=32, xhint=(1, 0, 0))
    mst.hexnut(piv - axis * 0.0382, axis, 0.0290, 0.0076, 0.0, n=36,
               xhint=(1, 0, 0))
    mst.hexnut(piv + axis * 0.0374, axis, 0.0262, 0.0060, 0.0113, n=36,
               xhint=(1, 0, 0))
    mst.spin(piv + axis * 0.0404, axis, [(0.0, 0.0), (0.0112, 0.0)],
             n=32, xhint=(1, 0, 0))
    mst.spin(piv - axis * 0.0421, axis,
             [(0.0, 0.0), (0.0058, 0.0), (0.0058, 0.0030), (0.0, 0.0030)],
             n=6, xhint=(1, 0, 0))

    # ---- rocker body ------------------------------------------------------- #
    mti.spin(piv, axis,
             [(0.0114, -0.0230), (0.0223, -0.0230), (0.0235, -0.0218),
              (0.0235, 0.0218), (0.0223, 0.0230), (0.0114, 0.0230),
              (0.0114, -0.0230)],
             n=44, xhint=(ph - piv), loop=True)

    def web(a, b, ha0, ha1, ht0, ht1, nw=10, slot=None):
        """Rocker arm between two bosses.

        With `slot` the arm is two parallel machined plates with a gap down the
        middle instead of one solid slab - a 35 x 60 mm blank titanium face was
        the biggest featureless area on the part, and a real bellcrank is open
        between its cheeks anyway.
        """
        a, b = Vector(a), Vector(b)
        d = b - a
        L = d.length
        d = d / L
        e2 = axis.cross(d).normalized()
        plates = ((None,),) if slot is None else (-1.0, 1.0)
        for sgn in plates:
            rings = []
            for i in range(nw):
                s = i / (nw - 1.0)
                c = a + d * (L * s)
                ha = ha0 + (ha1 - ha0) * s
                ht = ht0 + (ht1 - ht0) * s
                if slot is None:
                    sec = _sell(ha, ht, 0.45, 28)
                    rings.append([c + e2 * p0 + axis * p1 for (p0, p1) in sec])
                else:
                    g = slot[0] + (slot[1] - slot[0]) * s
                    half = 0.5 * (ht - g)
                    off = sgn * (g + half)
                    sec = _sell(ha, half, 0.45, 28)
                    rings.append([c + e2 * p0 + axis * (off + p1)
                                  for (p0, p1) in sec])
            mti.loft(rings, closed=True, cap0=True, cap1=True)

    for tip in (ph, pd):
        d = (tip - piv).normalized()
        knuckle = tip - d * 0.0300
        web(piv, knuckle, 0.0215, 0.0134, 0.0210, 0.0167,
            slot=(0.0044, 0.0095))
        e2 = axis.cross(d).normalized()
        _fork(mti, knuckle, e2, d, axis, 0.0300, rb=0.0158, fw=0.0134,
              base=-0.0150)
    web(ph, pd, 0.0092, 0.0092, 0.0058, 0.0058, nw=8)

    # ---- damper ------------------------------------------------------------ #
    dp, dn = _skin(*DAMPER_ANCHOR)
    foot = dp + dn * 0.0520
    _pad(mti, DAMPER_ANCHOR, 0.047, 0.033, t_flange=0.0090, t_boss=0.0160)
    _pad_bolts(mst, DAMPER_ANCHOR, 0.047, 0.033, thick=0.0090,
               spots=((25.0, 0.70), (155.0, 0.70), (205.0, 0.70), (335.0, 0.70)))
    org2 = dp + dn * (0.0160 - PAD_SINK)
    ea2, eb2, hg2, ax2 = _stand(org2, foot, axis)
    _fork(mti, org2, ea2, eb2, axis, hg2, rb=0.0146, fw=0.0180, axoff=ax2)

    dax = (foot - pd).normalized()          # rocker eye -> chassis foot
    L = (foot - pd).length
    _ball_and_race(mti, mst, foot, axis, dax)
    _pin_bolt(mst, foot, axis, hint=dax)
    _ball_and_race(mti, mst, pd, axis, -dax)
    _pin_bolt(mst, pd, axis, hint=-dax)

    # body sits on the chassis foot, shaft runs up to the rocker
    mti.spin(foot, -dax,
             [(0.0, 0.0142), (0.0138, 0.0142), (0.0142, 0.0150),
              (0.0142, 0.0210), (0.0196, 0.0228), (0.0200, 0.0240),
              (0.0200, 0.0640), (0.0196, 0.0652), (0.0154, 0.0660),
              (0.0154, 0.0716), (0.0136, 0.0732), (0.0136, 0.0768),
              (0.0074, 0.0768)],
             n=44, xhint=(0, 0, 1))
    mrd.spin(foot - dax * 0.0250, -dax,
             [(0.0202, 0.0), (0.0208, 0.0010), (0.0208, 0.0116),
              (0.0202, 0.0126), (0.0202, 0.0)],
             n=44, xhint=(0, 0, 1), loop=True)

    # shaft and bellows run from the body up to the rocker eye
    shaft_l = max(0.006, L - 0.0760 - 0.0128)
    mst.spin(foot - dax * 0.0760, -dax, [(0.0062, 0.0), (0.0062, shaft_l)],
             n=26, xhint=(0, 0, 1), cap0=False, cap1=False)
    nb = 6
    span = max(0.006, shaft_l - 0.0125)
    prof = [(0.0068, 0.0)]
    for i in range(nb):
        h = span * (i + 0.5) / nb
        prof.append((0.0102, h))
        prof.append((0.0076, h + span / (2.0 * nb)))
    prof.append((0.0069, span))
    mbk.spin(foot - dax * 0.0782, -dax, prof, n=32, xhint=(0, 0, 1))

    # piggyback reservoir with its adjuster, so the body is not a blank tube
    perp = dn - dax * dn.dot(dax)
    perp = perp.normalized() if perp.length > 1e-6 else axis
    side = dax.cross(perp).normalized()
    res_a = foot - dax * 0.0250 + side * 0.0332      # reservoir, foot end
    mti.spin(res_a, -dax,
             [(0.0, 0.0), (0.0086, 0.0), (0.0090, 0.0005), (0.0090, 0.0424),
              (0.0086, 0.0430), (0.0, 0.0430)], n=32, xhint=perp)
    mti.spin(foot - dax * 0.0330 + side * 0.0150, side,
             [(0.0060, 0.0), (0.0060, 0.0190)], n=24, xhint=dax,
             cap0=False, cap1=False)
    mrd.spin(res_a - dax * 0.0428, -dax,
             [(0.0, 0.0), (0.0088, 0.0), (0.0092, 0.0005), (0.0092, 0.0056),
              (0.0088, 0.0061), (0.0, 0.0061)], n=32, xhint=perp)
    mrd.hexnut(res_a + dax * 0.0028, dax, 0.0122, 0.0052, 0.0, n=36, xhint=perp)


# --------------------------------------------------------------------------- #
# corner build
# --------------------------------------------------------------------------- #

def _corner(coll, sy):
    tag = "FL" if sy > 0 else "FR"
    lugs = _lugs()
    mcf, mti, mst, mrd, mbk = _M(), _M(), _M(), _M(), _M()

    p_uf, pin_uf = _lug_point(lugs[0])
    p_ur, pin_ur = _lug_point(lugs[1])
    p_lf, pin_lf = _lug_point(lugs[2])
    p_lr, pin_lr = _lug_point(lugs[3])
    p_st, pin_st = _lug_point(lugs[4])

    a_uf, a_ur = _anchor(UP_F_ANCHOR), _anchor(UP_R_ANCHOR)
    a_lf, a_lr = _anchor(LO_F_ANCHOR), _anchor(LO_R_ANCHOR)
    a_tr = _anchor(TR_ANCHOR)
    up_axis = (a_uf - a_ur).normalized()
    lo_axis = (a_lf - a_lr).normalized()
    diag = []

    # ---- upper wishbone ---------------------------------------------------- #
    _clevis(mti, mst, UP_F_ANCHOR, up_axis, hx=0.048, harc=0.035)
    _clevis(mti, mst, UP_R_ANCHOR, up_axis, hx=0.050, harc=0.034)
    _leg(mcf, mti, mst, mrd, p_uf, pin_uf, a_uf, up_axis, math.radians(2.6),
         0.0840, 0.0248, report=diag, tag="upper-front")
    _leg(mcf, mti, mst, mrd, p_ur, pin_ur, a_ur, up_axis, math.radians(2.6),
         0.0840, 0.0248, report=diag, tag="upper-rear")

    # ---- lower wishbone ---------------------------------------------------- #
    _clevis(mti, mst, LO_F_ANCHOR, lo_axis, hx=0.048, harc=0.035)
    _clevis(mti, mst, LO_R_ANCHOR, lo_axis, hx=0.050, harc=0.034)
    _leg(mcf, mti, mst, mrd, p_lf, pin_lf, a_lf, lo_axis, math.radians(-2.2),
         0.0880, 0.0258, report=diag, tag="lower-front")
    lr_pts, lr_cum = _leg(mcf, mti, mst, mrd, p_lr, pin_lr, a_lr, lo_axis,
                          math.radians(-2.2), 0.0880, 0.0258,
                          report=diag, tag="lower-rear")

    # ---- rocker geometry --------------------------------------------------- #
    rp, rn = _skin(*ROCKER_ANCHOR)
    piv = rp + rn * 0.0740
    arm = Vector((0.460, 0.790, -0.130)).normalized()
    ph = piv + arm * 0.1160
    r_axis = (Vector((1.0, 0.0, 0.0)) - arm * arm.x).normalized()
    e2 = r_axis.cross(arm).normalized()
    pd = piv + 0.0980 * (math.cos(math.radians(192.0)) * arm
                         + math.sin(math.radians(192.0)) * e2)

    # ---- pushrod ----------------------------------------------------------- #
    # the pickup sits inboard of the end socket, on bare carbon, and the ball
    # hangs from the saddle's boss rather than off the leg's centreline
    d_gus = 0.0745
    gus_o = _at(lr_pts, lr_cum, d_gus)
    foot = gus_o + Vector((0.0350, 0.0, -0.0330))
    push_dir = (ph - foot).normalized()
    push_pin = Vector((0.0, 1.0, 0.0)).cross(push_dir).normalized()
    _pushrod_gusset(mti, mst, lr_pts, lr_cum, d_gus, foot, push_pin)
    _leg(mcf, mti, mst, mrd, foot, push_pin, ph, r_axis, 0.0,
         0.0720, 0.0262, knee_y=None, nring=38, upright_out=False,
         report=diag, tag="pushrod")

    # ---- track rod --------------------------------------------------------- #
    ktr = 0.86
    _leg(mcf, mti, mst, mrd, p_st, pin_st, a_tr, Vector((0.0, 0.0, 1.0)),
         math.radians(1.6), 0.0520, 0.0196, c_end=0.0250, t_end=0.0178,
         nring=36, k=ktr, report=diag, tag="track-rod")
    _clevis(mti, mst, TR_ANCHOR, Vector((0.0, 0.0, 1.0)), hx=0.047, harc=0.031,
            k=ktr, fw=0.0168)
    pT, nT = _skin(*TR_ANCHOR)
    gdir = (a_tr - pT).normalized()
    gprof = [(0.0192, 0.0)]
    for i in range(6):
        gprof.append((0.0178 - 0.0016 * i, 0.0038 + 0.0044 * i))
        gprof.append((0.0138 - 0.0014 * i, 0.0058 + 0.0044 * i))
    mbk.spin(pT + nT * 0.0045, gdir, gprof, n=32, cap0=True, cap1=True)

    # ---- rocker + damper --------------------------------------------------- #
    _rocker(mti, mst, mrd, mbk, piv, r_axis, ph, pd)

    made = [
        _emit(mcf, f"{NAME}_{tag}_Arms", "CarbonFibre", sy, coll, auto=42.0),
        _emit(mti, f"{NAME}_{tag}_Fittings", "Titanium", sy, coll, auto=32.0),
        _emit(mst, f"{NAME}_{tag}_Fasteners", "SteelFastener", sy, coll, auto=30.0),
        _emit(mrd, f"{NAME}_{tag}_Adjusters", "AnodisedRed", sy, coll, auto=30.0),
        _emit(mbk, f"{NAME}_{tag}_Seals", "MatteBlack", sy, coll, auto=36.0),
    ]
    if sy > 0:
        _report(diag, piv, ph, pd, foot, (mcf, mti, mst, mrd, mbk))
    return made


def _report(diag, piv, ph, pd, foot, meshes=()):
    """Clearance diagnostics printed into the preview log."""
    print(">> suspension_front geometry")
    ys = [v[1] for m in meshes for v in m.v]
    if ys:
        print(f"   left corner y span {min(ys):+.4f} .. {max(ys):+.4f} "
              f"(min |y| must stay clear of the mirror plane)")
    print(f"   piv={tuple(round(v, 4) for v in piv)} "
          f"ph={tuple(round(v, 4) for v in ph)} "
          f"pd={tuple(round(v, 4) for v in pd)} "
          f"foot={tuple(round(v, 4) for v in foot)}")
    for (tag, pts, cum) in diag:
        ys = [p.y for p in pts]
        hit = None
        for i in range(len(pts) - 1):
            if (pts[i].y - DRUM_BULKHEAD_Y) * (pts[i + 1].y - DRUM_BULKHEAD_Y) <= 0:
                hit = pts[i]
                break
        extra = ""
        if hit is not None:
            fx, up = hit.x - HUB.x, hit.z - HUB.z
            extra = (f"  bulkhead deg={math.degrees(math.atan2(up, fx)) % 360:7.2f}"
                     f" r={math.hypot(fx, up):.4f}")
        print(f"   {tag:12s} len={cum[-1]:.4f} y {max(ys):.4f}->{min(ys):.4f}{extra}")
    for i in range(len(diag)):
        for j in range(i + 1, len(diag)):
            a, b = diag[i][1], diag[j][1]
            best = 1e9
            for pa in a[::5]:
                for pb in b[::5]:
                    d = (pa - pb).length
                    if d < best:
                        best = d
            if best < 0.070:
                print(f"   MIN {diag[i][0]:12s} <-> {diag[j][0]:12s} {best:.4f}")


# --------------------------------------------------------------------------- #

def build(coll, ctx=None):
    made = []
    for sy in (1.0, -1.0):
        made.extend(_corner(coll, sy))
    return made
