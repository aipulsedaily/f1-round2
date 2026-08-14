"""2022+ four-element front wing, 2.000 m span, LE at x = +3.020.

Coordinate contract: +X forward, +Y car left, +Z up, tyre contact at z = 0.
Everything here is authored in car-local metres. Nothing bakes in GROUND.

Assembly
--------
    4 lofted aerofoil elements, real slot gaps (13-20 mm), 1 mm blunt TE
    endplates at |y| = 1.000 with an outboard curl on the top-rear quarter
    footplate / undercut along the bottom of each endplate
    4 vertical strakes per side under the mainplane, outermost on the EP face
    2 cascade winglets per side cantilevered off the endplate inner face
    2 under-nose pylons with bolted top flanges
    flap adjuster boss + tab, gurney on the top flap, cap screws everywhere
"""

import math

import bpy
from mathutils import Vector

import common as C
import spec as S

NAME = "front_wing"
P = "FW_"

# --------------------------------------------------------------------------- #
# principal geometry
# --------------------------------------------------------------------------- #

EP_T = 0.0130           # endplate laminate thickness (real, ray-measured)
EP_MID = 0.9815         # endplate mid-surface at the uncambered station
EP_CURL = 0.01220       # outboard curl -> outer face peaks at y = 1.00000
EP_LIP = 0.0068         # outboard footplate roll along the bottom edge
EP_BOW = 0.0046         # outboard camber of the mid panel (D-fw-13)
EP_R = 0.0055           # rolled radius on the laminate rim - see _ep_shell
EP_BURY = 0.0030        # how far element roots bury into the laminate
EP_X_F = 3.0150
EP_X_R = 2.3380

# There is deliberately no Y_TIP constant any more. The laminate face is a
# curved surface, not the plane EP_MID -/+ EP_T/2, so a single tip station
# cannot bury every element in it - see _tip_y and _ep_face_y (D-fw-15/17).

TE_HALF = 0.0005        # 1 mm trailing edge

N_CHORD = 104           # aerofoil samples per surface
N_SPAN = 281            # spanwise stations per element

# lex, lez, chord, inc(deg, TE up), camber(negative = inverted), thickness ratio
ELEMS = [
    dict(tag="Main",
         c=dict(lex=3.0200, lez=0.0720, chord=0.2350, inc=2.0, cam=-0.020, th=0.108),
         m=dict(lex=3.0195, lez=0.0780, chord=0.3200, inc=7.0, cam=-0.050, th=0.098),
         o=dict(lex=3.0120, lez=0.0800, chord=0.3450, inc=7.5, cam=-0.058, th=0.092)),
    dict(tag="Flap1",
         c=dict(lex=2.8300, lez=0.0990, chord=0.1500, inc=5.0, cam=-0.030, th=0.098),
         m=dict(lex=2.7780, lez=0.1331, chord=0.2120, inc=14.0, cam=-0.070, th=0.088),
         o=dict(lex=2.7700, lez=0.1369, chord=0.2220, inc=15.0, cam=-0.078, th=0.084)),
    dict(tag="Flap2",
         c=dict(lex=2.7200, lez=0.1281, chord=0.1300, inc=8.0, cam=-0.035, th=0.094),
         m=dict(lex=2.6340, lez=0.1962, chord=0.1760, inc=18.5, cam=-0.078, th=0.084),
         o=dict(lex=2.6250, lez=0.2053, chord=0.1850, inc=19.5, cam=-0.088, th=0.080)),
    dict(tag="Flap3",
         c=dict(lex=2.6300, lez=0.1597, chord=0.1150, inc=11.0, cam=-0.040, th=0.090),
         m=dict(lex=2.5060, lez=0.2645, chord=0.1500, inc=22.0, cam=-0.086, th=0.080),
         o=dict(lex=2.4950, lez=0.2793, chord=0.1580, inc=23.0, cam=-0.098, th=0.076)),
]

# endplate outline, front -> rear
_ZB_CTRL = [(3.0150, 0.0730), (2.9900, 0.0470), (2.9600, 0.0315), (2.9000, 0.0220),
            (2.8000, 0.0192), (2.6900, 0.0192), (2.6000, 0.0238), (2.5300, 0.0375),
            (2.4650, 0.0790), (2.4000, 0.1440), (2.3380, 0.2060)]
_ZT_CTRL = [(3.0150, 0.0870), (2.9900, 0.1040), (2.9600, 0.1265), (2.9000, 0.1670),
            (2.8000, 0.2200), (2.6900, 0.2680), (2.6000, 0.2985), (2.5300, 0.3245),
            (2.4650, 0.3430), (2.4000, 0.3575), (2.3380, 0.3645)]


# --------------------------------------------------------------------------- #
# small maths helpers (kept local - spec.py / common.py are frozen)
# --------------------------------------------------------------------------- #

def _curve_fn(ctrl, samples=800):
    """Monotone-in-x lookup through a Catmull-Rom spline of (x, z) controls."""
    pts = C.catmull_rom(ctrl, samples)
    xs = [p[0] for p in pts]
    zs = [p[1] for p in pts]

    def f(x):
        if x >= xs[0]:
            return zs[0]
        if x <= xs[-1]:
            return zs[-1]
        lo, hi = 0, len(xs) - 1
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if xs[mid] >= x:
                lo = mid
            else:
                hi = mid
        dx = xs[lo] - xs[hi]
        t = 0.0 if abs(dx) < 1e-12 else (xs[lo] - x) / dx
        return zs[lo] + (zs[hi] - zs[lo]) * t
    return f


_ZB = _curve_fn(_ZB_CTRL)
_ZT = _curve_fn(_ZT_CTRL)


def _resample_closed(pts, n):
    """Even arc-length resample of a closed 2-D polyline."""
    m = len(pts)
    acc = [0.0]
    for i in range(m):
        a, b = pts[i], pts[(i + 1) % m]
        acc.append(acc[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
    total = acc[-1]
    out, j = [], 0
    for k in range(n):
        t = total * k / n
        while j < m and acc[j + 1] < t:
            j += 1
        seg = acc[j + 1] - acc[j]
        f = 0.0 if seg < 1e-12 else (t - acc[j]) / seg
        a, b = pts[j], pts[(j + 1) % m]
        out.append((C.lerp(a[0], b[0], f), C.lerp(a[1], b[1], f)))
    return out


def _naca_t(s):
    return (0.2969 * math.sqrt(s) - 0.1260 * s - 0.3516 * s * s
            + 0.2843 * s ** 3 - 0.1036 * s ** 4)


def _airfoil(chord, thick, camber, n=N_CHORD):
    """Closed inverted-aerofoil loop in (u along chord, v normal).

    Cosine chordwise spacing keeps the leading-edge radius smooth enough that
    reflections do not facet. The trailing edge is a 1 mm round, not a knife.
    """
    up, lo = [], []
    for i in range(n + 1):
        s = 0.5 - 0.5 * math.cos(math.pi * i / n)
        u = chord * s
        yc = camber * chord * 4.0 * s * (1.0 - s)
        yt = 5.0 * thick * chord * _naca_t(s) + TE_HALF * s * s
        up.append((u, yc + yt))
        lo.append((u, yc - yt))
    ring = list(up)                                   # LE .. upper TE
    for ang in (45.0, 0.0, -45.0):                    # TE round-over
        r = math.radians(ang)
        ring.append((chord + TE_HALF * math.cos(r), TE_HALF * math.sin(r)))
    ring.append(lo[n])                                # lower TE
    ring.extend(reversed(lo[1:n]))                    # lower surface back to LE
    return ring


def _key(e, a, k):
    """Blend centre -> mid -> tip keys. Twist/chord wash out to the neutral
    centre section; the outer half keeps growing."""
    t1 = C.smoothstep((a - 0.115) / 0.245)
    t2 = C.smoothstep((a - 0.430) / 0.470)
    c, m, o = e["c"][k], e["m"][k], e["o"][k]
    return C.lerp(c, m, t1) + (o - m) * t2


def _elem_params(e, y):
    a = abs(y)
    return (_key(e, a, "lex"), _key(e, a, "lez"), _key(e, a, "chord"),
            math.radians(_key(e, a, "inc")), _key(e, a, "cam"), _key(e, a, "th"))


def _elem_ring(e, y, n=N_CHORD):
    lex, lez, ch, inc, cam, th = _elem_params(e, y)
    ca, sa = math.cos(inc), math.sin(inc)
    return [(lex - (u * ca - v * sa), y, lez + (u * sa + v * ca))
            for (u, v) in _airfoil(ch, th, cam, n)]


def _elem_surf(e, y, x, upper=True, n=260):
    """(z, inc) of the element's upper/lower skin at station y, abscissa x."""
    lex, lez, ch, inc, cam, th = _elem_params(e, y)
    ca, sa = math.cos(inc), math.sin(inc)
    best = None
    for i in range(n + 1):
        s = i / n
        u = ch * s
        yc = cam * ch * 4.0 * s * (1.0 - s)
        yt = 5.0 * th * ch * _naca_t(s) + TE_HALF * s * s
        v = (yc + yt) if upper else (yc - yt)
        px = lex - (u * ca - v * sa)
        pz = lez + (u * sa + v * ca)
        d = abs(px - x)
        if best is None or d < best[0]:
            best = (d, pz)
    return best[1], inc


def _reframe(ob):
    """Re-express a mesh in a local frame rotated +90 deg about X.

    D-fw-12: the shared CarbonFibre weave is driven by object coordinates and
    only varies in the object's local X and Y. On a part whose skin faces +/-Y
    - pylons, endplates, strakes, fences - that collapses the 2x2 twill into
    vertical fluting that reads as a pleated curtain, not carbon. Storing those
    meshes in a frame where local XY lies in the panel restores a real weave
    and is what a laminator would do anyway: plies follow the panel.
    """
    me = ob.data
    for v in me.vertices:
        x, y, z = v.co
        v.co = (x, z, -y)
    me.update()
    ob.rotation_euler = (math.pi * 0.5, 0.0, 0.0)
    return ob


def _frame(n):
    n = Vector(n).normalized()
    a = Vector((0.0, 0.0, 1.0)) if abs(n.z) < 0.9 else Vector((1.0, 0.0, 0.0))
    t = n.cross(a).normalized()
    return t, n.cross(t).normalized(), n


def _sheet(name, rows, coll, thick, mat="CarbonFibre", bevel=0.0016, bseg=3,
           offset=0.0, smooth=42.0):
    v, f = C.grid_surface(rows)
    ob = C.new_obj(name, v, f, coll=coll, smooth=True)
    m = C.add_solidify(ob, thickness=thick, offset=offset)
    # D-fw-05: even-offset divides by the vertex/face normal dot, and on a
    # nearly-flat sheet with a shallow rim it produced 1.4 m spikes out of a
    # 2.6 mm pad. These sheets are near-developable; plain offset is correct.
    m.use_even_offset = False
    # D-fw-14: thickness_clamp is Blender's "Offset Clamp" - it silently limits
    # the extrusion to the SHORTEST adjacent edge, per vertex. On these swept
    # grids the shortest edge is a fraction of a millimetre, so a declared 4.2 mm
    # strake came out 2.5 mm and a 5.0 mm footplate came out 2.9 mm. Nothing here
    # is offset far enough to self-intersect, so the clamp buys nothing and costs
    # every declared plate thickness. Off.
    m.thickness_clamp = 0.0
    m.use_rim = True
    if bevel:
        C.add_bevel(ob, width=bevel, segments=bseg, angle=32.0)
    C.shade_auto_smooth(ob, smooth)
    S.assign(ob, mat)
    return ob


def _frame_box(name, coll, origin, t, b, n, ht, hb, h0, h1, mat="Titanium",
               bevel=0.0012, bseg=3):
    o, t, b, n = Vector(origin), Vector(t), Vector(b), Vector(n)
    verts = []
    for sh in (h0, h1):
        for (st, sb) in ((-ht, -hb), (ht, -hb), (ht, hb), (-ht, hb)):
            verts.append(tuple(o + t * st + b * sb + n * sh))
    faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
             (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    ob = C.new_obj(name, verts, faces, coll=coll, smooth=False)
    C.add_bevel(ob, width=bevel, segments=bseg, angle=25.0)
    C.shade_auto_smooth(ob, 34.0)
    S.assign(ob, mat)
    return ob


def _hex_r(r, t):
    ap = r * math.cos(math.pi / 6.0)
    return ap / math.cos((t % (math.pi / 3.0)) - math.pi / 6.0)


def _cap_screw(name, coll, centre, normal, r_head=0.0045, h_head=0.0034,
               r_sock=0.0025, d_sock=0.0021, seg=24, mat="SteelFastener"):
    """Socket-head cap screw: chamfered head with a real hex recess."""
    t, b, n = _frame(normal)
    o = Vector(centre)
    ch = min(0.0009, h_head * 0.30)

    def ring(rad_fn, h):
        out = []
        for i in range(seg):
            a = C.TAU * i / seg
            r = rad_fn(a)
            out.append(tuple(o + t * (r * math.cos(a)) + b * (r * math.sin(a)) + n * h))
        return out

    circ = lambda rr: (lambda a: rr)
    hexr = lambda rr: (lambda a: _hex_r(rr, a))
    rings = [
        ring(circ(r_head * 0.94), -0.0006),
        ring(circ(r_head), 0.0004),
        ring(circ(r_head), h_head - ch),
        ring(circ(r_head - ch), h_head),
        ring(hexr(r_sock), h_head),
        ring(hexr(r_sock), h_head - d_sock + 0.0004),
        ring(hexr(r_sock * 0.72), h_head - d_sock),
    ]
    v, f = C.loft(rings, closed=True, cap_start=True, cap_end=True)
    ob = C.new_obj(name, v, f, coll=coll, smooth=True)
    C.merge_doubles(ob, 1e-6)
    C.shade_auto_smooth(ob, 30.0)
    S.assign(ob, mat)
    return ob


# --------------------------------------------------------------------------- #
# endplate surface
# --------------------------------------------------------------------------- #

def _ep_lip(x, v):
    """Outboard roll along the bottom of the plate - the tyre-wake footplate
    lip. It also stops the lower half of the outer face being 200 mm of blank
    laminate (D-fw-11)."""
    fx = C.smoothstep((x - 2.500) / 0.180) * C.smoothstep((2.965 - x) / 0.140)
    gv = C.smoothstep((0.170 - v) / 0.170)
    return EP_LIP * fx * gv


def _ep_bow(x, v):
    """Outboard camber of the panel between the footplate roll and the curl.

    D-fw-13: with y held at EP_MID everywhere between the lip and the curl, the
    plate carried a 600 x 100 mm dead-flat panel per face - measured, 68 % of
    its area had a face normal within 0.5 deg of +/-Y, i.e. zero curvature. It
    reads as a grey paddle and breaks spec.py's flat-face rule.
    A real endplate is cambered outboard and the camber grows rearward where the
    plate is working the tyre wake. The Gaussian term is a shallow fore-aft
    swage so the panel carries a moving highlight instead of one flat value.
    """
    v = min(1.0, max(0.0, v))
    a = EP_BOW * (0.34 + 0.66 * C.smoothstep((2.960 - x) / 0.430))
    swage = math.exp(-((v - 0.420) / 0.085) ** 2) * C.smoothstep((2.930 - x) / 0.220)
    return a * math.sin(math.pi * v) ** 1.35 - 0.0012 * swage


def _ep_point(x, v, side):
    zb, zt = _ZB(x), _ZT(x)
    fx = C.smoothstep((2.780 - x) / 0.320)
    gv = C.smoothstep((v - 0.760) / 0.240)
    z = zb + (zt - zb) * v - 0.0140 * fx * gv ** 3
    y = (EP_MID + EP_CURL * fx * gv + _ep_lip(x, v) + _ep_bow(x, v)) * side
    return (x, y, z)


def _ep_v_of_z(x, z):
    """Invert the endplate surface: which v puts the point at height z?

    Pads and rivets must be laid out in real (x, z) space - a constant-v band
    follows the tapering outline and renders as a curved sliver, which read as
    a scratch rather than a bonded doubler (D-fw-01).
    """
    lo, hi = 0.0, 1.0
    for _ in range(30):
        mid = 0.5 * (lo + hi)
        if _ep_point(x, mid, 1)[2] < z:
            lo = mid
        else:
            hi = mid
    return min(0.985, max(0.015, 0.5 * (lo + hi)))


def _rounded_rect(hx, hz, rc, arc=9, straight=7):
    """CCW outline of a rounded rectangle in local (dx, dz)."""
    rc = max(1e-4, min(rc, hx * 0.92, hz * 0.92))
    ax, az = hx - rc, hz - rc
    corners = ((ax, az, 0.0), (-ax, az, 90.0), (-ax, -az, 180.0), (ax, -az, 270.0))
    out = []
    for k, (cx, cz, s) in enumerate(corners):
        for i in range(arc):
            a = math.radians(s + 90.0 * i / arc)
            out.append((cx + rc * math.cos(a), cz + rc * math.sin(a)))
        a = math.radians(s + 90.0)
        px, pz = cx + rc * math.cos(a), cz + rc * math.sin(a)
        qcx, qcz, qs = corners[(k + 1) % 4]
        qa = math.radians(qs)
        qx, qz = qcx + rc * math.cos(qa), qcz + rc * math.sin(qa)
        for i in range(straight):
            t = i / straight
            out.append((C.lerp(px, qx, t), C.lerp(pz, qz, t)))
    return out


def _ep_pad(name, coll, xc, zc, hx, hz, tilt_deg, side, coll_mat="CarbonFibre",
            proud=0.0026, face=1, rc=None):
    """Bonded doubler on an endplate face (face 1 = outer, -1 = inner).

    D-fw-08: the first version swept a squircle-mapped grid and the boundary
    came out as a pointed lens with a solidify rim that beveled into notches.
    A three-ring loft over an explicit rounded-rect outline gives a clean
    machined pad with a real chamfer and no rim topology at all.
    """
    ca, sa = math.cos(math.radians(tilt_deg)), math.sin(math.radians(tilt_deg))
    rc = min(hx, hz) * 0.62 if rc is None else rc
    ch = min(0.0009, proud * 0.34)
    nc = _ep_normal(xc, _ep_v_of_z(xc, zc), side) * float(face)

    def place(dx, dz, h):
        x = xc + dx * ca - dz * sa
        z = zc + dx * sa + dz * ca
        p = Vector(_ep_point(x, _ep_v_of_z(x, z), side))
        return tuple(p + nc * (EP_T * 0.5 + h))

    out = _rounded_rect(hx, hz, rc)
    inn = [(math.copysign(max(0.0, abs(dx) - ch), dx),
            math.copysign(max(0.0, abs(dz) - ch), dz)) for (dx, dz) in out]
    rings = [[place(dx, dz, -0.0007) for (dx, dz) in out],
             [place(dx, dz, proud - ch) for (dx, dz) in out],
             [place(dx, dz, proud) for (dx, dz) in inn]]
    v, f = C.loft(rings, closed=True, cap_start=True, cap_end=True)
    ob = C.new_obj(name, v, f, coll=coll, smooth=True)
    C.merge_doubles(ob, 1e-6)
    C.shade_auto_smooth(ob, 30.0)
    S.assign(ob, coll_mat)
    return ob


def _root_fillet(name, coll, e, side, nphi=6):
    """Concave bond fillet where an element enters the endplate face.

    Without it the element meets the plate at a raw 90 deg intersection, which
    is the single loudest tell of an untouched CAD boolean (D-fw-06).

    Three things were wrong with the first version and all three were visible:
      * it was built on the nominal y = 0.9750 plane, 5 mm inboard of where the
        laminate face really is, so it floated with zero overlap on anything;
      * the quarter-round bulged AWAY from the corner - that is a bead, not a
        fillet, a fillet is concave;
      * a 104-sample cosine outline solidified 1.6 mm and beveled 0.6 mm put
        ~1900 sub-0.1 mm2 faces on each of Fillet2/3.
    Now: a closed solid ring swept along a 41-sample outline, each station
    landing on the measured face y for its own (x, z), 0.7 mm inside the
    laminate and 0.4 mm inside the element so the bond is real.
    """
    ring = _elem_ring(e, 0.9500, 41)
    pts = [(p[0], p[2]) for p in ring]
    ch = _key(e, 0.9500, "chord")
    r = max(0.0030, min(0.0055, 0.018 * ch))
    n = len(pts)
    area = sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1]
               for i in range(n))
    sgn = 1.0 if area > 0.0 else -1.0
    nrm, yf = [], []
    for i in range(n):
        ax, az = pts[(i - 1) % n]
        bx, bz = pts[(i + 1) % n]
        tx, tz = bx - ax, bz - az
        L = math.hypot(tx, tz) or 1.0
        nrm.append((sgn * tz / L, -sgn * tx / L))
        yf.append(_ep_face_y(pts[i][0], pts[i][1], 1, -1))

    into_ep, into_el = 0.0007, -0.0004
    prof = [(r, into_ep)]
    for k in range(nphi):                                  # concave quarter round
        a = math.radians(90.0 + 90.0 * k / (nphi - 1))
        prof.append((r + r * math.cos(a), -r + r * math.sin(a)))
    prof += [(into_el, -r), (into_el, into_ep)]

    rows = []
    for (s, d) in prof + [prof[0]]:
        rows.append([(pts[i][0] + nrm[i][0] * s, (yf[i] + d) * side,
                      pts[i][1] + nrm[i][1] * s) for i in range(n)])
    v, f = C.loft(rows, closed=True, cap_start=False, cap_end=False)
    ob = C.new_obj(name, v, f, coll=coll, smooth=True)
    C.merge_doubles(ob, 1e-6)
    C.shade_auto_smooth(ob, 46.0)
    S.assign(ob, "CarbonFibre")
    return ob


def _ep_normal(x, v, side, h=2e-4):
    a = Vector(_ep_point(min(EP_X_F, x + h), v, side))
    b = Vector(_ep_point(max(EP_X_R, x - h), v, side))
    c = Vector(_ep_point(x, min(1.0, v + 0.002), side))
    d = Vector(_ep_point(x, max(0.0, v - 0.002), side))
    n = (a - b).cross(c - d)
    if n.length < 1e-12:
        return Vector((0.0, float(side), 0.0))
    n.normalize()
    if n.y * side < 0.0:
        n = -n
    return n


def _ep_face(x, v, side, face=1):
    """Point on the real laminate face (face +1 = outboard, -1 = inboard)."""
    return (Vector(_ep_point(x, v, side))
            + _ep_normal(x, v, side) * (face * EP_T * 0.5))


def _ep_face_y(x, z, side=1, face=-1):
    """|y| of the laminate face at height z, station x.

    Everything that bonds to the plate has to be placed against THIS, not
    against a nominal EP_MID -/+ EP_T/2 plane: the face carries the
    footplate lip, the panel camber and the outboard curl, so it wanders
    over 12 mm across the plate (D-fw-15).
    """
    return abs(_ep_face(x, _ep_v_of_z(x, z), side, face).y)


def _ep_roll(d, r):
    """Half-thickness at distance d from the plate outline: flat land in the
    middle, quarter-round rolling into the rim over the last r."""
    h = EP_T * 0.5
    if d >= r:
        return h
    d = max(0.0, d)
    return h - r + math.sqrt(max(0.0, r * r - (r - d) * (r - d)))


def _ep_shell(name, coll, side, nx=130, ninner=60, r=EP_R, rim_rows=3):
    """Closed 13 mm laminate shell, built - not extruded.

    D-fw-14/16: solidify's offset clamp collapsed this plate to 1.0-2.7 mm and
    the 3.4 mm bevel that was meant to round the rim folded into 111 zero-area
    slivers. Both go away if the shell is authored directly: two offset face
    sheets at +/- EP_T/2, a quarter-round roll of radius r into the outline and
    a rim band joining them. Thickness is then exactly 13.00 mm everywhere by
    construction, the rim is G1-continuous with both faces without a bevel
    modifier, and every detail placed at _ep_point + n*(EP_T*0.5 + h) lands
    exactly h proud of the real face.

    r is 5.5 of the 6.5 mm half-thickness on purpose. The shared CarbonFibre
    weave is driven by OBJECT coordinates and only varies in local X and Y, so
    any surface standing perpendicular to the panel - which is exactly what a
    flat rim land is - collapses the twill into stripes (the same D-fw-12 trap
    that made the panels look pleated). Rolling almost the whole 13 mm edge
    leaves a 2 mm land and lets the weave wrap round the rim like it does on
    the pylon nose.
    """
    def graded(length, rr, n):
        """Stations 0..length with six extra inside each rolled rim."""
        arc = [rr * (1.0 - math.cos(math.radians(a)))
               for a in (0.0, 15.0, 30.0, 45.0, 60.0, 75.0)]
        mid = [rr + (length - 2.0 * rr) * k / n for k in range(n + 1)]
        return arc + mid + [length - a for a in reversed(arc)]

    L = EP_X_F - EP_X_R
    xs = graded(L, r, nx)
    cols = []
    for dx0 in xs:
        x = EP_X_F - dx0
        dx = min(dx0, L - dx0)
        z0 = _ep_point(x, 0.0, side)[2]
        z1 = _ep_point(x, 1.0, side)[2]
        H = max(1e-5, z1 - z0)
        rr = min(r, 0.30 * H)
        col = []
        for d in graded(H, rr, ninner):
            v = min(1.0, max(0.0, d / H))
            p = Vector(_ep_point(x, v, side))
            n = _ep_normal(x, v, side)
            col.append((p, n, _ep_roll(min(dx, d, H - d), rr)))
        cols.append(col)

    nx, nv = len(cols), len(cols[0])
    verts, faces = [], []
    out0 = 0
    for col in cols:
        for (p, n, d) in col:
            verts.append(tuple(p + n * d))
    in0 = len(verts)
    for col in cols:
        for (p, n, d) in col:
            verts.append(tuple(p - n * d))

    def oi(i, j):
        return out0 + i * nv + j

    def ii(i, j):
        return in0 + i * nv + j

    for i in range(nx - 1):
        for j in range(nv - 1):
            faces.append((oi(i, j), oi(i, j + 1), oi(i + 1, j + 1), oi(i + 1, j)))
            faces.append((ii(i, j), ii(i + 1, j), ii(i + 1, j + 1), ii(i, j + 1)))

    loop = ([(i, 0) for i in range(nx)]
            + [(nx - 1, j) for j in range(1, nv)]
            + [(i, nv - 1) for i in range(nx - 2, -1, -1)]
            + [(0, j) for j in range(nv - 2, 0, -1)])
    band = []
    for m in range(1, rim_rows):
        t = 1.0 - 2.0 * m / rim_rows
        row = []
        for (i, j) in loop:
            p, n, d = cols[i][j]
            row.append(len(verts))
            verts.append(tuple(p + n * (d * t)))
        band.append(row)
    rings = [[oi(i, j) for (i, j) in loop]] + band + [[ii(i, j) for (i, j) in loop]]
    for a, b in zip(rings, rings[1:]):
        for k in range(len(loop)):
            k2 = (k + 1) % len(loop)
            faces.append((a[k], a[k2], b[k2], b[k]))

    ob = C.new_obj(name, verts, faces, coll=coll, smooth=True)
    C.merge_doubles(ob, 1e-6)
    C.shade_auto_smooth(ob, 44.0)
    S.assign(ob, "CarbonFibre")
    return _reframe(ob)


# --------------------------------------------------------------------------- #
# builders
# --------------------------------------------------------------------------- #

_TIP_CACHE = {}


def _tip_y(e):
    """Outermost loft station for an element: EP_BURY past the REAL inner face.

    D-fw-17: one global Y_TIP of 0.9780 was picked 3 mm inboard of the nominal
    face. The real face is not a plane - it carries the curl and the panel
    camber - so on the top flap it sits 8 mm further outboard, and every
    element stopped short, leaving an open slot round its root with the flat
    212-vertex loft cap staring out of it. Each element now solves its own tip
    against the face its own root outline actually meets, which also keeps the
    tip 10 mm clear of the outer face so nothing punches through.
    """
    tag = e["tag"]
    if tag not in _TIP_CACHE:
        ring = _elem_ring(e, 0.9500, 30)
        _TIP_CACHE[tag] = max(_ep_face_y(p[0], p[2], 1, -1) for p in ring) + EP_BURY
    return _TIP_CACHE[tag]


def _build_elements(coll):
    made = []
    for e in ELEMS:
        yt = _tip_y(e)
        ys = [-yt + 2.0 * yt * i / (N_SPAN - 1) for i in range(N_SPAN)]
        rings = [_elem_ring(e, y) for y in ys]
        v, f = C.loft(rings, closed=True, cap_start=True, cap_end=True)
        ob = C.new_obj(P + "El_" + e["tag"], v, f, coll=coll, smooth=True)
        C.shade_auto_smooth(ob, 58.0)
        S.assign(ob, "CarbonFibre")
        made.append(ob)
    return made


def _build_endplate(coll, side):
    tag = "L" if side > 0 else "R"
    made = [_ep_shell(P + "Endplate_" + tag, coll, side)]

    # Team accent on the outer face. D-fw-18: the old band was laid out in v,
    # so it tapered from 8 mm at the rear to 0.8 mm over the nose and read as a
    # red wire; and at v = 0.913..0.968 it sat in the deepest part of the curl,
    # where a proud ribbon is the widest thing on the car. Now it is a constant
    # 22 mm livery band in real z, 13.5 mm under the top edge, standing 0.6 mm
    # proud so the plate itself stays the widest surface. The band is placed so
    # that solidify puts its back face 0.2 mm INSIDE the laminate: land it at
    # exactly 0.0 and the two surfaces are coincident over 0.13 m2, which is a
    # ray-tie waiting to speckle.
    arows = []
    na, nb = 104, 6
    for i in range(na):
        x = C.lerp(2.9550, 2.3540, i / (na - 1.0))
        z0 = _ep_point(x, 1.0, side)[2] - 0.0135
        row = []
        for j in range(nb):
            z = z0 - 0.0220 * j / (nb - 1.0)
            v = _ep_v_of_z(x, z)
            row.append(tuple(_ep_face(x, v, side, 1)
                             + _ep_normal(x, v, side) * 0.0002))
        arows.append(row)
    made.append(_reframe(_sheet(P + "Accent_" + tag, arows, coll, 0.0008,
                                "AnodisedRed", bevel=0.0, smooth=40.0)))

    # element attachment doublers + through bolts, laid along each element's
    # chord line so they read as machined pads rather than curved slivers
    pads = [(2.8600, 0.1070, 0.0580, 0.0185, -9.0),
            (2.6650, 0.1655, 0.0400, 0.0165, -15.0),
            (2.5380, 0.2340, 0.0360, 0.0155, -19.5),
            (2.4700, 0.2900, 0.0280, 0.0135, -23.0)]
    for k, (xc, zc, hx, hz, tilt) in enumerate(pads):
        made.append(_reframe(_ep_pad(f"{P}Pad{k}_{tag}", coll, xc, zc, hx, hz,
                                     tilt, side)))
        ca, sa = math.cos(math.radians(tilt)), math.sin(math.radians(tilt))
        for f in (-0.62, 0.62):
            bx, bz = xc + hx * f * ca, zc + hx * f * sa
            bv = _ep_v_of_z(bx, bz)
            n = _ep_normal(bx, bv, side)
            c = Vector(_ep_point(bx, bv, side)) + n * (EP_T * 0.5 + 0.0026)
            made.append(_cap_screw(f"{P}Bolt{k}{'a' if f < 0 else 'b'}_{tag}",
                                   coll, c, n, r_head=0.0048, h_head=0.0034))

    # bonded fillets where each element enters the inner face
    for k, e in enumerate(ELEMS):
        made.append(_root_fillet(f"{P}Fillet{k}_{tag}", coll, e, side))

    # FIA / build data plate low on the inner face, four small rivets
    made.append(_reframe(_ep_pad(f"{P}DataPlate_{tag}", coll, 2.4300, 0.1750,
                                 0.0270, 0.0110, -14.0, side,
                                 coll_mat="Titanium", proud=0.0014, face=-1,
                                 rc=0.0035)))
    for dxp, dzp in ((-0.0210, -0.0065), (0.0210, -0.0118),
                     (-0.0210, 0.0065), (0.0210, 0.0012)):
        rx, rz = 2.4300 + dxp, 0.1750 + dzp
        rv = _ep_v_of_z(rx, rz)
        nn = _ep_normal(rx, rv, side)
        cc = Vector(_ep_point(rx, rv, side)) - nn * (EP_T * 0.5 + 0.0014)
        made.append(_cap_screw(f"{P}DPRivet{dxp:+.3f}{dzp:+.4f}_{tag}", coll,
                               cc, -nn, r_head=0.0020, h_head=0.0010,
                               r_sock=0.0010, d_sock=0.0005, seg=14,
                               mat="SteelFastener"))

    # bond rivets along the footplate laminate joint, outer face
    for k in range(8):
        t = k / 7.0
        rx = C.lerp(2.9200, 2.5400, t)
        rz = _ZB(rx) + 0.0105
        rv = _ep_v_of_z(rx, rz)
        nn = _ep_normal(rx, rv, side)
        cc = Vector(_ep_point(rx, rv, side)) + nn * (EP_T * 0.5)
        made.append(_cap_screw(f"{P}FPRivet{k}_{tag}", coll, cc, nn,
                               r_head=0.0026, h_head=0.0012, r_sock=0.0013,
                               d_sock=0.0006, seg=16, mat="Titanium"))

    # flush rivet line down the inner face along the trailing edge
    for k in range(9):
        t = k / 8.0
        rx = C.lerp(2.3760, 2.3640, t)
        rz = C.lerp(0.2260, 0.3340, t)
        rv = _ep_v_of_z(rx, rz)
        n = -_ep_normal(rx, rv, side)
        c = Vector(_ep_point(rx, rv, side)) - _ep_normal(rx, rv, side) * (EP_T * 0.5)
        made.append(_cap_screw(f"{P}Rivet{k}_{tag}", coll, c, n, r_head=0.0032,
                               h_head=0.0014, r_sock=0.0016, d_sock=0.0008,
                               seg=18, mat="Titanium"))
    return made


def _build_footplate(coll, side):
    tag = "L" if side > 0 else "R"
    amp = _curve_fn([(2.9700, 0.06), (2.9200, 0.42), (2.8400, 0.80),
                     (2.7400, 1.00), (2.6400, 0.96), (2.5600, 0.74),
                     (2.5000, 0.38), (2.4600, 0.10)])
    sec = C.catmull_rom([(0.0000, 0.0000), (0.0075, 0.0035), (0.0150, 0.0090),
                         (0.0250, 0.0148), (0.0380, 0.0186), (0.0520, 0.0205),
                         (0.0640, 0.0212)], 17)
    rows = []
    for i in range(96):
        x = C.lerp(2.9700, 2.4600, i / 95.0)
        # a floor of 0.02 shrank the 64 mm section to 1.3 mm at the ends, i.e.
        # 0.08 mm sample spacing and a rash of sub-0.01 mm2 faces
        a = max(0.11, amp(x))
        zb = _ZB(x) + 0.0012
        # root bonded 3 mm inside the measured inner face, not 2 mm inside a
        # nominal plane that the laminate never occupied (D-fw-15)
        y0 = _ep_face_y(x, zb + 0.0060, side, -1) + 0.0030
        rows.append([(x, (y0 - dy * a) * side, zb + dz * a)
                     for (dy, dz) in sec])
    return [_sheet(P + "Footplate_" + tag, rows, coll, 0.0050, "CarbonFibre",
                   bevel=0.0012, bseg=2, smooth=40.0)]


def _build_strakes(coll, side):
    tag = "L" if side > 0 else "R"
    made = []
    main = ELEMS[0]
    specs = [(None, 0.000), (0.9050, 0.020), (0.8450, 0.018), (0.7880, 0.015)]
    zbot = _curve_fn([(2.9900, 0.0320), (2.9200, 0.0272), (2.8600, 0.0262),
                      (2.8000, 0.0292), (2.7850, 0.0340)])
    for k, (y0, sweep) in enumerate(specs):
        rows = []
        for i in range(46):
            u = i / 45.0
            x = C.lerp(2.9860, 2.7900, u)
            y = 0.9745 if y0 is None else (y0 + sweep * u ** 1.6)
            ztop, _ = _elem_surf(main, y, x, upper=False)
            ztop += 0.0045                      # bury into the mainplane
            # D-fw-10: square-cut ends read as an unfinished offcut. Wash the
            # fence height out over the first and last 12 % of the chord.
            taper = 0.55 + 0.45 * C.smoothstep(min(u, 1.0 - u) / 0.12)
            zb = ztop - (ztop - zbot(x)) * taper
            col = []
            for j in range(16):
                w = j / 15.0
                z = C.lerp(ztop, zb, w)
                # the outermost fence is bonded to the plate, so its outer skin
                # has to ride the laminate face rather than sit on one plane
                # 4.2 mm short of it (D-fw-15)
                yy = (_ep_face_y(x, z, side, -1) - 0.0013) if y0 is None else y
                col.append((x, yy * side, z))
            rows.append(col)
        made.append(_reframe(_sheet(f"{P}Strake{k}_{tag}", rows, coll, 0.0042,
                                    "CarbonFibre", bevel=0.0013, bseg=3,
                                    smooth=38.0)))
    return made


def _mini_wing(name, coll, le0, le1, ch0, ch1, inc0, inc1, cam, th, y0, y1,
               nst=34, mat="CarbonFibre"):
    rings = []
    for i in range(nst):
        t = i / (nst - 1)
        y = C.lerp(y0, y1, t)
        lex, lez = C.lerp(le0[0], le1[0], t), C.lerp(le0[1], le1[1], t)
        ch = C.lerp(ch0, ch1, t)
        inc = math.radians(C.lerp(inc0, inc1, t))
        ca, sa = math.cos(inc), math.sin(inc)
        rings.append([(lex - (u * ca - v * sa), y, lez + (u * sa + v * ca))
                      for (u, v) in _airfoil(ch, th, cam, 56)])
    v, f = C.loft(rings, closed=True, cap_start=True, cap_end=True)
    ob = C.new_obj(name, v, f, coll=coll, smooth=True)
    C.shade_auto_smooth(ob, 58.0)
    S.assign(ob, mat)
    return ob


def _build_cascades(coll, side):
    tag = "L" if side > 0 else "R"
    made = []
    # D-fw-09: the two winglets used to stop at 0.856 and 0.888 while the fin
    # sat at 0.862-0.872, so one speared it and the other floated 16 mm short.
    # Both now die 1 mm inside the fin's laminate.
    y_fin = 0.8650
    y_tip = (y_fin + 0.0010) * side
    cfg = [((2.7150, 0.2225), (2.7060, 0.2170), 0.0920, 0.0820, 20.0, 16.0),
           ((2.6200, 0.2620), (2.6120, 0.2570), 0.0720, 0.0640, 24.0, 20.0)]
    for k, (leA, leB, cA, cB, iA, iB) in enumerate(cfg):
        # these root high on the plate, inside the curl, so the root station is
        # solved against the measured face like the elements are (D-fw-15)
        ca, sa = math.cos(math.radians(iA)), math.sin(math.radians(iA))
        foot = [(leA[0] - (u * ca - v * sa), leA[1] + (u * sa + v * ca))
                for (u, v) in _airfoil(cA, 0.135, -0.070, 20)]
        root = (max(_ep_face_y(px, pz, 1, -1) for (px, pz) in foot) + 0.0020) * side
        made.append(_mini_wing(f"{P}Cascade{k}_{tag}", coll, leA, leB, cA, cB,
                               iA, iB, -0.070, 0.135, root, y_tip))
    # compact cascade endplate tying the two winglet tips together - raked
    # front edge and a rolled top so it is not a rectangle of cardboard
    ft = _curve_fn([(2.7460, 0.2430), (2.7000, 0.2650), (2.6400, 0.2840),
                    (2.5800, 0.2965), (2.5340, 0.3020)])
    fb = _curve_fn([(2.7460, 0.2205), (2.7000, 0.2120), (2.6400, 0.2240),
                    (2.5800, 0.2415), (2.5340, 0.2560)])
    fin = []
    for i in range(38):
        u = i / 37.0
        x = C.lerp(2.7460, 2.5340, u)
        fin.append([(x, y_fin * side, C.lerp(ft(x), fb(x), j / 13.0))
                    for j in range(14)])
    made.append(_reframe(_sheet(P + "CascadeFin_" + tag, fin, coll, 0.0038,
                                "CarbonFibre", bevel=0.0012, bseg=3,
                                smooth=38.0)))
    return made


def _build_adjusters(coll, side):
    tag = "L" if side > 0 else "R"
    made = []
    # big adjuster boss on the endplate outer face at the top-flap joint
    n = _ep_normal(2.5000, 0.740, side)
    c = Vector(_ep_point(2.5000, 0.740, side)) + n * (EP_T * 0.5)
    made.append(_cap_screw(P + "AdjBoss_" + tag, coll, c, n, r_head=0.0135,
                           h_head=0.0040, r_sock=0.0058, d_sock=0.0030,
                           seg=36, mat="Titanium"))
    # tab bracket standing on the top flap, just inboard of the endplate
    # one low-profile clevis on the top flap, sized like real hardware rather
    # than the pair of Lego blocks the first pass produced (D-fw-07)
    e3 = ELEMS[3]
    xb, yb = 2.4670, 0.9260
    z, inc = _elem_surf(e3, yb, xb, upper=True)
    t = Vector((-math.cos(inc), 0.0, math.sin(inc)))
    b = Vector((0.0, 1.0, 0.0))
    nrm = Vector((math.sin(inc), 0.0, math.cos(inc)))
    o = Vector((xb, yb * side, z))
    made.append(_frame_box(P + "AdjTab_" + tag, coll, o, t, b, nrm,
                           0.0082, 0.0034, -0.0035, 0.0072, "Titanium",
                           bevel=0.0010))
    made.append(_cap_screw(P + "AdjScrew_" + tag, coll, o + nrm * 0.0072, nrm,
                           r_head=0.0030, h_head=0.0022, r_sock=0.0016,
                           d_sock=0.0013, mat="AnodisedRed"))
    return made


def _build_gurney(coll, side):
    tag = "L" if side > 0 else "R"
    e3 = ELEMS[3]
    rows = []
    m = 96
    for i in range(m):
        a = C.lerp(0.3000, _tip_y(e3), i / (m - 1))
        y = a * side
        lex, lez, ch, inc, cam, th = _elem_params(e3, a)
        ca, sa = math.cos(inc), math.sin(inc)
        s = 0.982
        u = ch * s
        yc = cam * ch * 4.0 * s * (1.0 - s)
        yt = 5.0 * th * ch * _naca_t(s) + TE_HALF * s * s
        v = yc + yt
        px = lex - (u * ca - v * sa)
        pz = lez + (u * sa + v * ca)
        nx_, nz_ = sa, ca
        h = 0.0062 * C.smoothstep((a - 0.340) / 0.160)
        col = []
        for j in range(5):
            d = C.lerp(-0.0045, h, j / 4.0)
            col.append((px + nx_ * d, y, pz + nz_ * d))
        rows.append(col)
    return [_sheet(P + "Gurney_" + tag, rows, coll, 0.0016, "CarbonFibre",
                   bevel=0.0005, bseg=2, smooth=38.0)]


def _build_pylon(coll, side):
    tag = "L" if side > 0 else "R"
    made = []
    main = ELEMS[0]
    y0 = 0.0480 * side
    z_top = 0.2185
    nz, nu = 44, 44

    def plan(w, grow=0.0):
        """(le_x, chord, half-width scale) of the pylon section at height frac w."""
        lex = C.lerp(2.9950, 2.9680, w)
        ch = C.lerp(0.1260, 0.1000, w)
        thr = C.lerp(0.270, 0.230, w)
        # flared root fairing: the section swells into the mainplane instead of
        # cutting it at a hard line (D-fw-04)
        flare = 1.0 + 0.85 * max(0.0, 1.0 - w / 0.16) ** 2
        return lex, ch * (1.0 + 0.14 * (flare - 1.0)) + grow, thr, flare

    def section(w, grow=0.0, wid=0.0):
        lex, ch, thr, flare = plan(w, grow)
        ring = []
        for i in range(2 * nu):
            if i <= nu:
                s = 0.5 - 0.5 * math.cos(math.pi * i / nu)
                sgn = 1.0
            else:
                s = 0.5 - 0.5 * math.cos(math.pi * (2 * nu - i) / nu)
                sgn = -1.0
            hw = (5.0 * thr * ch * _naca_t(s) + 0.0005 * s * s) * flare + wid
            ring.append((lex - ch * s, sgn * hw))
        return ring

    rings = []
    for k in range(nz):
        w = (k / (nz - 1)) ** 0.85
        ring = []
        for (x, hw) in section(w):
            y = y0 + hw * side
            zl, _ = _elem_surf(main, abs(y), x, upper=True)
            zl -= 0.0055
            # a *1.15 ramp saturated seven rings early and left the top of
            # the pylon as a stack of near-coincident rings - 103 sub-0.01 mm2
            # faces and a flat mushroom shelf under the flange
            ring.append((x, y, C.lerp(zl, z_top, C.smoothstep(w))))
        rings.append(ring)
    v, f = C.loft(rings, closed=True, cap_start=True, cap_end=True)
    ob = C.new_obj(P + "Pylon_" + tag, v, f, coll=coll, smooth=True)
    C.merge_doubles(ob, 1e-6)
    C.shade_auto_smooth(ob, 46.0)
    S.assign(ob, "CarbonFibre")
    made.append(_reframe(ob))

    # Mounting flange: follows the pylon plan offset outboard, so it reads as a
    # machined saddle rather than a T-bar cap (D-fw-03).
    # D-fw-19: it was a bare 4-ring loft with NO bevel modifier at all - every
    # edge of a machined titanium saddle was mathematically sharp, both flare
    # steps and both cap rims, and spec.py says break every edge a machinist
    # would. A bevel modifier is the wrong tool here: on a 44-station aerofoil
    # outline whose nose samples are 0.25 mm apart it left 134 sub-0.01 mm2
    # corner patches whatever width it was given. So the chamfers are rings:
    # the outline is resampled to an even 4 mm pitch and each step carries its
    # own break, which is exactly how the part would be turned anyway.
    frings = []
    for (zz, grow, wid) in ((0.2138, 0.0000, 0.0000),   # buried in the pylon
                            (0.2151, 0.0080, 0.0048),   # flare
                            (0.2158, 0.0090, 0.0055),   # break
                            (0.2216, 0.0098, 0.0060),   # side wall
                            (0.2226, 0.0100, 0.0062),
                            (0.2234, 0.0092, 0.0054),   # break under the face
                            (0.2239, 0.0088, 0.0050),   # top face
                            (0.2245, 0.0072, 0.0036)):  # crown, rim broken
        frings.append([(x, y0 + hw * side, zz)
                       for (x, hw) in _resample_closed(section(1.0, grow, wid), 56)])
    v, f = C.loft(frings, closed=True, cap_start=True, cap_end=True)
    fl = C.new_obj(P + "PylonFlange_" + tag, v, f, coll=coll, smooth=True)
    C.merge_doubles(fl, 1e-6)
    C.shade_auto_smooth(fl, 30.0)
    S.assign(fl, "Titanium")
    made.append(fl)

    for j, (bx, by) in enumerate(((2.9500, 0.0), (2.9080, 0.0090),
                                  (2.9080, -0.0090), (2.8830, 0.0))):
        made.append(_cap_screw(
            f"{P}PylonBolt{j}_{tag}", coll,
            Vector((bx, y0 + by * side, 0.2245)), (0.0, 0.0, 1.0),
            r_head=0.0040, h_head=0.0026, r_sock=0.0021, d_sock=0.0016))
    return made


# --------------------------------------------------------------------------- #

def build(coll, ctx=None):
    made = []
    made += _build_elements(coll)
    for side in (1, -1):
        made += _build_endplate(coll, side)
        made += _build_footplate(coll, side)
        made += _build_strakes(coll, side)
        made += _build_cascades(coll, side)
        made += _build_adjusters(coll, side)
        made += _build_gurney(coll, side)
        made += _build_pylon(coll, side)
    return made
