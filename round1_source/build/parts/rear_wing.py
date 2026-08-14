"""rear_wing - the complete rear wing assembly at the tail of the car.

Contract: +X forward (nose x=+3.000), +Y car LEFT, +Z up, tyre contact z=0.
Span 1.050 m (outer faces of the endplates at |y| = 0.525), top of the
assembly at z = spec.REAR_WING_TOP_Z, flap trailing edge at x = -2.630.

Assembly
--------
    mainplane      lofted aerofoil, spooned centre section, rolled tips
    DRS flap       separate element on 6 real hinge brackets, open slot gap
    DRS pod        centreline actuator fairing + pushrod + rod-end to the flap
    endplates      through-cut louvre stack with formed vanes, rolled outer
                   edge, bonded doublers, rivet lines
    pylons         swan-neck, from the engine cover deck onto the mainplane's
                   UPPER surface, bolted top flanges
    beam wing      two elements, endplate to endplate, below the main wing
    rain light     rear-facing LED panel in a housing on a stalk under the
                   beam wing centre
    gurney         full-span tab on the flap TE, stepped taller at the tips

Nothing here bakes in spec.GROUND.
"""

import math

import bpy
from mathutils import Vector

import common as C
import spec as S

NAME = "rear_wing"
P = "RW_"

# --------------------------------------------------------------------------- #
# principal geometry
# --------------------------------------------------------------------------- #

EP_MID = 0.5115         # endplate mid surface
EP_T = 0.0130           # laminate thickness
EP_INNER = EP_MID - 0.5 * EP_T          # 0.5050
EP_OUTER = EP_MID + 0.5 * EP_T          # 0.5180
EP_ROLL = 0.0070        # outboard roll -> outer skin reaches 0.5250 = span/2

Y_TIP = EP_INNER + 0.0030               # elements bury 3 mm into the plate
TE_HALF = 0.0006        # 1.2 mm blunt trailing edge

TOP_Z = S.REAR_WING_TOP_Z               # 0.950
TE_X = S.REAR_WING_TE_X                 # -2.630

N_CHORD = 112           # aerofoil samples per surface
N_SPAN = 241            # spanwise stations, main elements

# Element keys: centre (y=0) and tip (|y|=Y_TIP).
#   lex/lez  leading edge, chord, inc (deg, TE up), cam (negative = inverted),
#   th       thickness ratio
MAIN = dict(
    c=dict(lex=-2.2210, lez=0.7530, chord=0.3000, inc=17.0, cam=-0.058, th=0.104),
    t=dict(lex=-2.2320, lez=0.7760, chord=0.2760, inc=14.5, cam=-0.050, th=0.098),
)
FLAP = dict(
    c=dict(lex=-2.4988, lez=0.8570, chord=0.1500, inc=29.0, cam=-0.060, th=0.090),
    t=dict(lex=-2.4901, lez=0.8614, chord=0.1400, inc=26.0, cam=-0.052, th=0.086),
)
BEAM1 = dict(
    c=dict(lex=-2.2850, lez=0.3900, chord=0.1500, inc=16.0, cam=-0.062, th=0.100),
    t=dict(lex=-2.3150, lez=0.4560, chord=0.1400, inc=14.0, cam=-0.054, th=0.096),
)
BEAM2 = dict(
    c=dict(lex=-2.4210, lez=0.4440, chord=0.1050, inc=30.0, cam=-0.070, th=0.092),
    t=dict(lex=-2.4450, lez=0.5000, chord=0.0990, inc=27.0, cam=-0.062, th=0.088),
)

Y_BEAM_TIP = EP_INNER + 0.0025

# endplate outline, front -> rear, as (x, z_bottom) and (x, z_top) controls
_EPB_CTRL = [(-2.1900, 0.6520), (-2.1920, 0.6060), (-2.1955, 0.5560),
             (-2.2010, 0.5120), (-2.2120, 0.4790), (-2.2350, 0.4570),
             (-2.2800, 0.4400), (-2.3600, 0.4260), (-2.4500, 0.4160),
             (-2.5400, 0.4110), (-2.6000, 0.4180), (-2.6420, 0.4520),
             (-2.6720, 0.5150)]
# NB the rolled band bulges 6.5 mm past the mid surface, so the TOP EDGE of
# the mid surface sits at 0.9436 and the finished outer edge lands exactly on
# spec.REAR_WING_TOP_Z = 0.950. Measured, not assumed.
_EPT_CTRL = [(-2.1900, 0.7036), (-2.1920, 0.7496), (-2.1955, 0.7996),
             (-2.2010, 0.8396), (-2.2120, 0.8666), (-2.2350, 0.8856),
             (-2.2800, 0.9016), (-2.3600, 0.9216), (-2.4500, 0.9356),
             (-2.5400, 0.9426), (-2.6000, 0.9436), (-2.6420, 0.9416),
             (-2.6720, 0.9216)]

EP_X_F = _EPB_CTRL[0][0]
EP_X_R = _EPB_CTRL[-1][0]

# Louvre stack. The window sits in the free area between the mainplane's
# upper skin and the endplate top edge; the slots run PARALLEL to the top edge
# (they are specified as offsets below it in TOP_OFFS, not as absolute z), so
# they stay a constant 13.5 mm tall instead of tapering into slivers.
LOUVRE_X = (-2.4600, -2.3400)


# --------------------------------------------------------------------------- #
# local maths helpers (spec.py / common.py are frozen - nothing goes back there)
# --------------------------------------------------------------------------- #

def _curve_fn(ctrl, samples=900):
    """Monotone-in-x lookup through a Catmull-Rom spline of (x, z) controls.

    Controls run front (large x) -> rear (small x), so the table is decreasing.
    """
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


_ZB = _curve_fn(_EPB_CTRL)
_ZT = _curve_fn(_EPT_CTRL)


def _naca_t(s):
    return (0.2969 * math.sqrt(s) - 0.1260 * s - 0.3516 * s * s
            + 0.2843 * s ** 3 - 0.1036 * s ** 4)


def _airfoil(chord, thick, camber, n=N_CHORD):
    """Closed inverted-aerofoil loop in (u aft along chord, v normal).

    Cosine chordwise spacing so the leading-edge radius does not facet in a
    reflection, and a real rounded trailing edge instead of a knife.
    """
    up, lo = [], []
    for i in range(n + 1):
        s = 0.5 - 0.5 * math.cos(math.pi * i / n)
        u = chord * s
        yc = camber * chord * 4.0 * s * (1.0 - s)
        yt = 5.0 * thick * chord * _naca_t(s) + TE_HALF * s * s
        up.append((u, yc + yt))
        lo.append((u, yc - yt))
    ring = list(up)
    for ang in (50.0, 25.0, 0.0, -25.0, -50.0):
        r = math.radians(ang)
        ring.append((chord + TE_HALF * math.cos(r), TE_HALF * math.sin(r)))
    ring.append(lo[n])
    ring.extend(reversed(lo[1:n]))
    return ring


def _frame(n):
    n = Vector(n).normalized()
    a = Vector((0.0, 0.0, 1.0)) if abs(n.z) < 0.9 else Vector((1.0, 0.0, 0.0))
    t = n.cross(a).normalized()
    return t, n.cross(t).normalized(), n


def _reframe(ob):
    """Store a Y-facing panel in a frame whose local XY lies in the panel.

    The shared CarbonFibre weave is driven by OBJECT coordinates and only
    varies in local X and Y. A panel whose normal is +/-Y has constant local Y,
    so the 2x2 twill degenerates into vertical fluting - a pleated curtain, not
    carbon. Rotating the stored mesh puts the plies in the panel, which is what
    a laminator does anyway.
    """
    me = ob.data
    for v in me.vertices:
        x, y, z = v.co
        v.co = (x, z, -y)
    me.update()
    ob.rotation_euler = (math.pi * 0.5, 0.0, 0.0)
    return ob


# --------------------------------------------------------------------------- #
# aerofoil elements
# --------------------------------------------------------------------------- #

def _key(e, a, k, k0=0.30):
    """Blend the centre key into the tip key. `a` is |y| / Y_TIP."""
    return C.lerp(e["c"][k], e["t"][k], C.smoothstep((a - k0) / (1.0 - k0)))


def _tip_roll(a):
    """Extra upward kick over the last 55 mm of span - the 2022 tip roll-up
    where the element merges into the endplate."""
    return 0.0080 * C.smoothstep((a - 0.880) / 0.120) ** 2


def _elem_params(e, y, y_tip, roll=True):
    a = min(1.0, abs(y) / y_tip)
    lez = _key(e, a, "lez") + (_tip_roll(a) if roll else 0.0)
    return (_key(e, a, "lex"), lez, _key(e, a, "chord"),
            math.radians(_key(e, a, "inc")), _key(e, a, "cam"), _key(e, a, "th"))


def _elem_ring(e, y, y_tip=Y_TIP, roll=True, shrink=0.0):
    lex, lez, ch, inc, cam, th = _elem_params(e, y, y_tip, roll)
    ca, sa = math.cos(inc), math.sin(inc)
    cx, cz = lex - 0.5 * ch * ca, lez + 0.5 * ch * sa
    out = []
    for (u, v) in _airfoil(ch, th, cam):
        x = lex - (u * ca - v * sa)
        z = lez + (u * sa + v * ca)
        if shrink:
            x, z = C.lerp(x, cx, shrink), C.lerp(z, cz, shrink)
        out.append((x, y, z))
    return out


def _elem_pt(e, y, s, upper=True, y_tip=Y_TIP, roll=True):
    """Point + in-plane normal on an element skin at span y, chord fraction s."""
    lex, lez, ch, inc, cam, th = _elem_params(e, y, y_tip, roll)
    ca, sa = math.cos(inc), math.sin(inc)

    def surf(ss):
        u = ch * ss
        yc = cam * ch * 4.0 * ss * (1.0 - ss)
        yt = 5.0 * th * ch * _naca_t(max(ss, 1e-6)) + TE_HALF * ss * ss
        v = (yc + yt) if upper else (yc - yt)
        return (lex - (u * ca - v * sa), lez + (u * sa + v * ca))

    h = 2.5e-3
    x0, z0 = surf(max(0.0, s - h))
    x1, z1 = surf(min(1.0, s + h))
    tx, tz = x1 - x0, z1 - z0
    L = math.hypot(tx, tz) or 1.0
    n = Vector((-tz / L, 0.0, tx / L))
    if (n.z > 0.0) != upper:
        n = -n
    x, z = surf(s)
    return Vector((x, y, z)), n


def _span_stations(n, y_tip):
    """Cosine-clustered span stations: dense at the tips where the roll-up and
    the endplate junction are, and dense at the centre where the pod sits."""
    out = []
    for i in range(n):
        t = i / (n - 1)
        # cosine in [-1, 1] then a mild centre re-cluster
        c = -math.cos(math.pi * t)
        c = 0.82 * c + 0.18 * (c ** 3)
        out.append(c * y_tip)
    return out


def _loft_element(name, e, coll, y_tip=Y_TIP, n_span=N_SPAN, roll=True,
                  mat="CarbonFibre", smooth=38.0):
    ys = _span_stations(n_span, y_tip)
    rings = [_elem_ring(e, y, y_tip, roll) for y in ys]
    v, f = C.loft(rings, closed=True, cap_start=True, cap_end=True)
    ob = C.new_obj(name, v, f, coll=coll, smooth=True)
    C.merge_doubles(ob, 1e-6)
    C.shade_auto_smooth(ob, smooth)
    S.assign(ob, mat)
    return ob


# --------------------------------------------------------------------------- #
# hardware primitives
# --------------------------------------------------------------------------- #

def _hex_r(r, t):
    ap = r * math.cos(math.pi / 6.0)
    return ap / math.cos((t % (math.pi / 3.0)) - math.pi / 6.0)


def _screw_geo(centre, normal, r_head=0.0038, h_head=0.0029, r_sock=0.0021,
               d_sock=0.0018, seg=22):
    """Socket-head cap screw: chamfered head with a real hex recess."""
    t, b, n = _frame(normal)
    o = Vector(centre)
    ch = min(0.0008, h_head * 0.30)

    def ring(rad_fn, h):
        out = []
        for i in range(seg):
            a = C.TAU * i / seg
            r = rad_fn(a)
            out.append(tuple(o + t * (r * math.cos(a)) + b * (r * math.sin(a))
                             + n * h))
        return out

    circ = lambda rr: (lambda a: rr)
    hexr = lambda rr: (lambda a: _hex_r(rr, a))
    rings = [
        ring(circ(r_head * 0.93), -0.0006),
        ring(circ(r_head), 0.0004),
        ring(circ(r_head), h_head - ch),
        ring(circ(r_head - ch), h_head),
        ring(hexr(r_sock), h_head),
        ring(hexr(r_sock), h_head - d_sock + 0.0004),
        ring(hexr(r_sock * 0.70), h_head - d_sock),
    ]
    return C.loft(rings, closed=True, cap_start=True, cap_end=True)


def _rivet_geo(centre, normal, r=0.0021, h=0.0010, seg=14):
    """Domed rivet head - the bond-line detail on a laminate joint."""
    t, b, n = _frame(normal)
    o = Vector(centre)
    rings = []
    for k in range(5):
        ph = 0.5 * math.pi * k / 4.0
        rr, hh = r * math.cos(ph * 0.90), h * math.sin(ph)
        rings.append([tuple(o + t * (rr * math.cos(C.TAU * i / seg))
                            + b * (rr * math.sin(C.TAU * i / seg))
                            + n * (hh - 0.0004)) for i in range(seg)])
    # cap_end matters: the top ring still has radius 0.156 * r, so leaving it
    # open punched a 0.33 mm hole in the apex of all 182 rivet domes and made
    # them the only open shells in the part.
    return C.loft(rings, closed=True, cap_start=True, cap_end=True)


def _merge_geo(name, coll, geos, coll_mat="SteelFastener", smooth=32.0):
    """One mesh out of many (verts, faces) pairs - keeps the object count sane
    when a part carries 200 fasteners."""
    verts, faces = [], []
    for (v, f) in geos:
        base = len(verts)
        verts.extend(v)
        faces.extend(tuple(i + base for i in fc) for fc in f)
    ob = C.new_obj(name, verts, faces, coll=coll, smooth=True)
    C.merge_doubles(ob, 1e-6)
    C.shade_auto_smooth(ob, smooth)
    S.assign(ob, coll_mat)
    return ob


def _prism(name, coll, outline, origin, ax, ay, depth, mat="Titanium",
           bevel=0.0010, bseg=3, smooth=32.0):
    """Extrude a closed 2D outline along a third axis. outline is [(u, v)]."""
    o, ax, ay = Vector(origin), Vector(ax), Vector(ay)
    n = ax.cross(ay).normalized()
    rings = [[tuple(o + ax * u + ay * v + n * d) for (u, v) in outline]
             for d in (0.0, depth)]
    v, f = C.loft(rings, closed=True, cap_start=True, cap_end=True)
    ob = C.new_obj(name, v, f, coll=coll, smooth=False)
    C.merge_doubles(ob, 1e-6)
    if bevel:
        C.add_bevel(ob, width=bevel, segments=bseg, angle=25.0)
    C.shade_auto_smooth(ob, smooth)
    S.assign(ob, mat)
    return ob


def _rounded_rect(hx, hz, rc, arc=7, straight=5):
    """CCW outline of a rounded rectangle in local (du, dv)."""
    rc = max(1e-4, min(rc, hx * 0.95, hz * 0.95))
    ax, az = hx - rc, hz - rc
    corners = ((ax, az, 0.0), (-ax, az, 90.0), (-ax, -az, 180.0), (ax, -az, 270.0))
    out = []
    for k, (cx, cz, s0) in enumerate(corners):
        for i in range(arc):
            a = math.radians(s0 + 90.0 * i / arc)
            out.append((cx + rc * math.cos(a), cz + rc * math.sin(a)))
        a = math.radians(s0 + 90.0)
        px, pz = cx + rc * math.cos(a), cz + rc * math.sin(a)
        qcx, qcz, qs = corners[(k + 1) % 4]
        qa = math.radians(qs)
        qx, qz = qcx + rc * math.cos(qa), qcz + rc * math.sin(qa)
        for i in range(straight):
            t = i / straight
            out.append((C.lerp(px, qx, t), C.lerp(pz, qz, t)))
    return out


def _tube(name, coll, path, radius, coll_mat="Titanium", seg=18, caps=True,
          smooth=40.0):
    """Parallel-transport sweep of a circle along a polyline."""
    pts = [Vector(p) for p in path]
    tans = []
    for i in range(len(pts)):
        if i == 0:
            t = pts[1] - pts[0]
        elif i == len(pts) - 1:
            t = pts[-1] - pts[-2]
        else:
            t = pts[i + 1] - pts[i - 1]
        tans.append(t.normalized())
    ref = Vector((0.0, 0.0, 1.0))
    if abs(tans[0].dot(ref)) > 0.94:
        ref = Vector((0.0, 1.0, 0.0))
    nrm = (ref - tans[0] * ref.dot(tans[0])).normalized()
    rings = []
    for i, (p, t) in enumerate(zip(pts, tans)):
        if i:
            nrm = (nrm - t * nrm.dot(t)).normalized()
        bn = t.cross(nrm).normalized()
        r = radius(i / (len(pts) - 1)) if callable(radius) else radius
        rings.append([tuple(p + nrm * (r * math.cos(C.TAU * k / seg))
                            + bn * (r * math.sin(C.TAU * k / seg)))
                      for k in range(seg)])
    v, f = C.loft(rings, closed=True, cap_start=caps, cap_end=caps)
    ob = C.new_obj(name, v, f, coll=coll, smooth=True)
    C.merge_doubles(ob, 1e-6)
    C.shade_auto_smooth(ob, smooth)
    S.assign(ob, coll_mat)
    return ob


# --------------------------------------------------------------------------- #
# generic twin-skin shell with real through-holes
# --------------------------------------------------------------------------- #

def _shell_from_grid(name, coll, grid, nrm, thick, holes=(), band_seg=4,
                     mat="CarbonFibre", smooth=34.0, hole_rim=None,
                     hole_band_seg=6):
    """Two skins offset +-thick/2 from a mid-surface grid, closed by a rounded
    band around the outer boundary AND around every hole.

    grid   : grid[i][j] mid-surface points, i = columns, j = rows
    nrm    : constant offset direction (the panel's thickness axis)
    holes  : list of (i0, i1, j0, j1) - cells [i0,i1) x [j0,j1) are removed,
             so grid rows j0/j1 and columns i0/i1 form the slot rim.
    hole_rim : IN-PLANE radius of the rim band around a hole. Defaults to
             thick/2, which is a full half-round roll - and that is exactly
             what sealed the louvres shut (D-rw-R2-01). A hole only stays open
             if 2 * hole_rim is comfortably less than the slot's own height,
             so a slot cut in a thick laminate wants a small break radius, not
             a full roll. The band stays a half-ELLIPSE: it still spans the
             whole thickness normal to the panel (it has to, to join the two
             skins), it just does not eat the hole in-plane.

    Built by hand rather than with a solidify modifier because a modifier
    cannot open a hole, and a boolean would wreck the quad flow that keeps the
    reflection on a 13 mm laminate edge clean.
    """
    ni, nj = len(grid), len(grid[0])
    nrm = Vector(nrm).normalized()
    h = 0.5 * thick

    def inside_hole(i, j):
        for (i0, i1, j0, j1) in holes:
            if i0 <= i < i1 and j0 <= j < j1:
                return True
        return False

    cells = [(i, j) for i in range(ni - 1) for j in range(nj - 1)
             if not inside_hole(i, j)]
    used = set()
    for (i, j) in cells:
        used.update(((i, j), (i + 1, j), (i, j + 1), (i + 1, j + 1)))

    verts, faces = [], []
    idx = {}
    for (i, j) in sorted(used):
        p = Vector(grid[i][j])
        idx[(1, i, j)] = len(verts)
        verts.append(tuple(p + nrm * h))
        idx[(-1, i, j)] = len(verts)
        verts.append(tuple(p - nrm * h))
    for (i, j) in cells:
        a, b = idx[(1, i, j)], idx[(1, i + 1, j)]
        c, d = idx[(1, i + 1, j + 1)], idx[(1, i, j + 1)]
        faces.append((a, b, c, d))
        a, b = idx[(-1, i, j)], idx[(-1, i + 1, j)]
        c, d = idx[(-1, i + 1, j + 1)], idx[(-1, i, j + 1)]
        faces.append((a, d, c, b))

    def out_dir(i, j, ni_, nj_, i0, i1, j0, j1, into):
        """In-surface direction from (i, j) toward the free space.

        D-rw-12: this used to be `this point minus the neighbouring column`.
        Where the endplate's leading edge is near vertical, adjacent columns
        are 1.5 mm apart in x but their rows differ by 30 mm in z, so that
        vector pointed almost straight DOWN the edge instead of out of it, the
        rim band folded through itself and the leading edge grew a white
        faceted shard. Take the normal to the BOUNDARY CURVE instead - it does
        not care how skewed the interior quads are.
        """
        d = Vector((0.0, 0.0, 0.0))

        def edge_normal(t, inward):
            e = nrm.cross(Vector(t))
            if e.length < 1e-9:
                return None
            e.normalize()
            return -e if e.dot(Vector(inward)) > 0.0 else e

        here = Vector(grid[i][j])
        if i == i0 or i == i1:
            ja, jb = max(j - 1, j0), min(j + 1, j1)
            t = Vector(grid[i][jb]) - Vector(grid[i][ja])
            step = 1 if i == i0 else -1
            inward = Vector(grid[min(max(i + step, 0), ni_ - 1)][j]) - here
            e = edge_normal(t, inward)
            if e is not None:
                d += e
        if j == j0 or j == j1:
            ia, ib = max(i - 1, i0), min(i + 1, i1)
            t = Vector(grid[ib][j]) - Vector(grid[ia][j])
            step = 1 if j == j0 else -1
            inward = Vector(grid[i][min(max(j + step, 0), nj_ - 1)]) - here
            e = edge_normal(t, inward)
            if e is not None:
                d += e
        if into:
            d = -d
        return d.normalized() if d.length > 1e-9 else Vector((1.0, 0.0, 0.0))

    def band(loop, into, r_in=None, seg=None):
        """loop: ordered [(i, j)] boundary; bridge outer skin -> inner skin."""
        r_in = h if r_in is None else r_in
        seg = band_seg if seg is None else seg
        rings = []
        for k in range(seg + 1):
            ph = math.pi * k / seg
            ring = []
            for (i, j, i0, i1, j0, j1) in loop:
                p = Vector(grid[i][j])
                e = out_dir(i, j, ni, nj, i0, i1, j0, j1, into)
                ring.append(tuple(p + e * (r_in * math.sin(ph))
                                  + nrm * (h * math.cos(ph))))
            rings.append(ring)
        base = len(verts)
        n = len(loop)
        for r in rings:
            verts.extend(r)
        for k in range(seg):
            a, b = base + k * n, base + (k + 1) * n
            for m in range(n):
                m2 = (m + 1) % n
                faces.append((a + m, a + m2, b + m2, b + m))
        # ring 0 and ring band_seg are coincident with the two skins by
        # construction (sin 0 = 0, cos 0 = 1), so the merge pass welds them.
        # Emitting explicit weld quads here would only add degenerate faces.

    def rect_loop(i0, i1, j0, j1):
        lp = []
        for i in range(i0, i1):
            lp.append((i, j0, i0, i1, j0, j1))
        for j in range(j0, j1):
            lp.append((i1, j, i0, i1, j0, j1))
        for i in range(i1, i0, -1):
            lp.append((i, j1, i0, i1, j0, j1))
        for j in range(j1, j0, -1):
            lp.append((i0, j, i0, i1, j0, j1))
        return lp

    band(rect_loop(0, ni - 1, 0, nj - 1), into=False)
    for (i0, i1, j0, j1) in holes:
        band(rect_loop(i0, i1, j0, j1), into=True, r_in=hole_rim,
             seg=hole_band_seg)

    ob = C.new_obj(name, verts, faces, coll=coll, smooth=True)
    C.merge_doubles(ob, 1e-6)
    C.shade_auto_smooth(ob, smooth)
    S.assign(ob, mat)
    return ob


# --------------------------------------------------------------------------- #
# endplate
# --------------------------------------------------------------------------- #

TOP_OFFS = [0.0000, 0.0055, 0.0110,
            0.0155, 0.0290,          # louvre 1
            0.0345, 0.0480,          # louvre 2
            0.0535, 0.0670,          # louvre 3
            0.0760, 0.0920, 0.1120, 0.1380]
N_LOW = 26                  # rows below the louvre block
H_REF = 0.460               # reference plate height for the un-anchored rows
NJ = N_LOW + len(TOP_OFFS)

# D-rw-R2-01. The slot is bounded by two grid rows and the rim band rolls INTO
# it from both. With an 11 mm slot and a full 6.5 mm roll the two rolls met in
# the middle and welded the louvre shut - the plate measured solid on a ray
# cast straight through it. A slot has to be taller than twice its own break
# radius to survive: 13.5 mm of slot minus 2 x 1.5 mm of rim leaves a 10.5 mm
# clear opening, which is what the ray probe now reports.
LOUVRE_SLOT_H = 0.0135      # every slot, by construction of TOP_OFFS
EP_HOLE_RIM = 0.0015        # in-plane break radius on a cut edge


def _ep_roll(x, z):
    """Outboard roll of the laminate near the top and trailing edges."""
    d = min(_ZT(x) - z, x - EP_X_R)
    return EP_ROLL * C.smoothstep((0.016 - d) / 0.016)


def _ep_mid_y(x, z, side):
    return side * (EP_MID + _ep_roll(x, z))


def _ep_cols():
    """Column x list, clustered at the ends and snapped to the louvre window."""
    xs = []
    n = 196
    for i in range(n):
        t = i / (n - 1)
        t = 0.5 - 0.5 * math.cos(math.pi * t)
        t = 0.72 * t + 0.28 * (i / (n - 1))
        xs.append(C.lerp(EP_X_F, EP_X_R, t))
    for xv in LOUVRE_X:
        xs.extend([xv, xv - 0.0022, xv + 0.0022])
    xs = sorted(set(round(v, 6) for v in xs), reverse=True)
    out = [xs[0]]
    for v in xs[1:]:
        if out[-1] - v > 0.0009:
            out.append(v)
    return out


def _ep_rows(x):
    """Row w-values (0 = bottom edge, 1 = top edge) for one column."""
    zb, zt = _ZB(x), _ZT(x)
    h = max(zt - zb, 1e-4)
    g = (C.smoothstep((x - (LOUVRE_X[0] - 0.055)) / 0.045)
         * C.smoothstep(((LOUVRE_X[1] + 0.055) - x) / 0.045))
    top = []
    for o in TOP_OFFS:
        wa = 1.0 - o / h
        wf = 1.0 - o / H_REF
        w = C.lerp(wf, wa, g)
        if top and w > top[-1] - 0.004:
            w = top[-1] - 0.004
        top.append(w)
    w_last = max(top[-1], 0.30)
    low = []
    for j in range(N_LOW):
        t = j / N_LOW
        t = 0.5 - 0.5 * math.cos(math.pi * t)
        t = 0.62 * t + 0.38 * (j / N_LOW)
        low.append(w_last * t)
    return low + list(reversed(top))


def _ep_grid(side):
    xs = _ep_cols()
    grid = []
    for x in xs:
        zb, zt = _ZB(x), _ZT(x)
        col = []
        for w in _ep_rows(x):
            z = zb + (zt - zb) * w
            col.append(Vector((x, _ep_mid_y(x, z, side), z)))
        grid.append(col)
    return xs, grid


def _louvre_holes(xs):
    def col_of(xv):
        return min(range(len(xs)), key=lambda i: abs(xs[i] - xv))
    i0, i1 = col_of(LOUVRE_X[0]), col_of(LOUVRE_X[1])
    i0, i1 = min(i0, i1), max(i0, i1)
    holes = []
    for k in (3, 5, 7):
        j_top = N_LOW + (len(TOP_OFFS) - 1 - k)
        j_bot = j_top - 1
        holes.append((i0, i1, j_bot, j_top))
    return holes, i0, i1


def _ep_face_pt(x, z, side, face=1.0):
    """Point on the endplate's outer (face=+1) / inner (face=-1) skin."""
    return Vector((x, _ep_mid_y(x, z, side) + side * face * 0.5 * EP_T, z))


def _louvre_vane(name, coll, side, k_top, k_bot, nx=34, nq=7):
    """The formed scoop that fills a louvre slot.

    A louvre is not a hole - it is material hinged along the slot's lower edge
    and pushed outboard, so it is welded to the plate along that edge and at
    both ends. Modelled that way it can never read as a floating tab.

    D-rw-R2-01: the vane used to rise 1.06 x the slot height, i.e. it capped
    the slot off completely, so even once the plate is genuinely cut there is
    nothing to see. It now stops at 0.78 of the slot, leaving ~1.5 mm of
    totally unobstructed slot above its top edge; at 25 deg of elevation the
    sight line clears the standing edge and drops straight into the opening.
    """
    x0, x1 = LOUVRE_X
    o_t, o_b = TOP_OFFS[k_top], TOP_OFFS[k_bot]
    hs = o_b - o_t
    rows = []
    for iq in range(nq):
        q = iq / (nq - 1)
        dz = hs * 0.78 * q
        dy = 0.0058 * (q ** 1.5)
        row = []
        for ix in range(nx):
            t = ix / (nx - 1)
            x = C.lerp(x0, x1, t)
            # both ends curl back onto the plate over the last 6 mm
            fade = (C.smoothstep((x - x0) / 0.0065)
                    * C.smoothstep((x1 - x) / 0.0065))
            zb = _ZT(x) - o_b
            p = _ep_face_pt(x, zb + dz, side, 1.0)
            row.append((p.x, p.y + side * dy * fade, p.z))
        rows.append(row)
    v, f = C.grid_surface(rows)
    ob = C.new_obj(name, v, f, coll=coll, smooth=True)
    m = C.add_solidify(ob, thickness=0.0016, offset=0.0)
    m.use_even_offset = False
    m.use_rim = True
    C.add_bevel(ob, width=0.0004, segments=2, angle=30.0)
    C.shade_auto_smooth(ob, 40.0)
    S.assign(ob, "CarbonFibre")
    return _reframe(ob)


def _ep_pad(name, coll, side, xc, zc, hx, hz, tilt=0.0, proud=0.0024,
            face=1.0, mat="CarbonMatte", rc=None):
    """Bonded doubler on an endplate face - a three-ring loft over an explicit
    rounded-rect outline, so it gets a real machined chamfer and no rim
    topology at all."""
    ca, sa = math.cos(math.radians(tilt)), math.sin(math.radians(tilt))
    rc = min(hx, hz) * 0.45 if rc is None else rc
    ch = min(0.0008, proud * 0.34)
    ndir = Vector((0.0, side * face, 0.0))

    def place(dx, dz, hgt):
        x = xc + dx * ca - dz * sa
        z = zc + dx * sa + dz * ca
        return tuple(_ep_face_pt(x, z, side, face) + ndir * hgt)

    out = _rounded_rect(hx, hz, rc)
    inn = [(math.copysign(max(0.0, abs(dx) - ch), dx),
            math.copysign(max(0.0, abs(dz) - ch), dz)) for (dx, dz) in out]
    rings = [[place(dx, dz, -0.0006) for (dx, dz) in out],
             [place(dx, dz, proud - ch) for (dx, dz) in out],
             [place(dx, dz, proud) for (dx, dz) in inn]]
    v, f = C.loft(rings, closed=True, cap_start=True, cap_end=True)
    ob = C.new_obj(name, v, f, coll=coll, smooth=True)
    C.merge_doubles(ob, 1e-6)
    C.shade_auto_smooth(ob, 30.0)
    S.assign(ob, mat)
    return ob


def _ep_strip(name, coll, side, path, hw, proud=0.0022, face=1.0,
              mat="CarbonMatte"):
    """Raised stiffener strip following an (x, z) path on an endplate face.

    The lower half of an endplate is otherwise 0.2 m of blank laminate, which
    is exactly the "flat untextured face" the brief calls a defect.
    """
    ch = min(0.0007, proud * 0.34)
    ndir = Vector((0.0, side * face, 0.0))
    n = len(path)

    def edges(shrink):
        left, right = [], []
        for i in range(n):
            ax, az = path[max(i - 1, 0)]
            bx, bz = path[min(i + 1, n - 1)]
            tx, tz = bx - ax, bz - az
            L = math.hypot(tx, tz) or 1.0
            nx, nz = -tz / L, tx / L
            w = hw - shrink
            end = C.smoothstep(min(i, n - 1 - i) / max(0.10 * n, 1.0))
            x, z = path[i]
            left.append((x + nx * w * end, z + nz * w * end))
            right.append((x - nx * w * end, z - nz * w * end))
        return left + list(reversed(right))

    def ring(shrink, hgt):
        return [tuple(_ep_face_pt(x, z, side, face) + ndir * hgt)
                for (x, z) in edges(shrink)]

    rings = [ring(0.0, -0.0006), ring(0.0, proud - ch), ring(ch, proud)]
    v, f = C.loft(rings, closed=True, cap_start=True, cap_end=True)
    ob = C.new_obj(name, v, f, coll=coll, smooth=True)
    C.merge_doubles(ob, 1e-6)
    C.shade_auto_smooth(ob, 30.0)
    S.assign(ob, mat)
    return ob


def _elem_joint_line(e, side, y_tip, n=13, s0=0.10, s1=0.93, roll=True):
    """(x, z) samples along an element's chord line at the endplate face -
    where a real bolt/rivet row follows the joint."""
    y = (EP_INNER - 0.001) * side
    out = []
    for i in range(n):
        s = C.lerp(s0, s1, i / (n - 1))
        pu, _ = _elem_pt(e, y, s, True, y_tip, roll)
        pl, _ = _elem_pt(e, y, s, False, y_tip, roll)
        out.append((0.5 * (pu.x + pl.x), 0.5 * (pu.z + pl.z)))
    return out


def _root_fillet(name, coll, e, side, y_tip, r=0.0038, nphi=6, roll=True,
                 n_ring=None):
    """Quarter-round bond fillet where an element enters the endplate face.

    Without it the element meets the plate at a raw 90 degree intersection,
    which is the loudest tell of an untouched CAD boolean.
    """
    y_face = EP_INNER * side
    ring = _elem_ring(e, (EP_INNER - r * 0.45) * side, y_tip, roll)
    if n_ring:
        ring = [ring[i] for i in range(0, len(ring), max(1, len(ring) // n_ring))]
    pts = [(p[0], p[2]) for p in ring]
    n = len(pts)
    area = sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1]
               for i in range(n))
    sgn = 1.0 if area > 0.0 else -1.0
    nrm = []
    for i in range(n):
        ax, az = pts[(i - 1) % n]
        bx, bz = pts[(i + 1) % n]
        tx, tz = bx - ax, bz - az
        L = math.hypot(tx, tz) or 1.0
        nrm.append((sgn * tz / L, -sgn * tx / L))
    rows = []
    for k in range(nphi):
        phi = 0.5 * math.pi * k / (nphi - 1)
        off, dy = r * math.cos(phi), -r * math.sin(phi) * side
        rows.append([(pts[i][0] + nrm[i][0] * off, y_face + dy,
                      pts[i][1] + nrm[i][1] * off) for i in range(n)])
    v, f = C.loft(rows, closed=True, cap_start=False, cap_end=False)
    ob = C.new_obj(name, v, f, coll=coll, smooth=True)
    m = C.add_solidify(ob, thickness=0.0014, offset=0.0)
    m.use_even_offset = False
    C.shade_auto_smooth(ob, 44.0)
    S.assign(ob, "CarbonFibre")
    return ob


def _build_endplate(coll, side):
    tag = "L" if side > 0 else "R"
    made = []
    xs, grid = _ep_grid(side)
    holes, i0, i1 = _louvre_holes(xs)
    ob = _shell_from_grid(f"{P}Endplate_{tag}", coll, grid, (0.0, side, 0.0),
                          EP_T, holes=holes, band_seg=4, mat="CarbonFibre",
                          smooth=30.0, hole_rim=EP_HOLE_RIM, hole_band_seg=6)
    made.append(_reframe(ob))

    for n_, (kt, kb) in enumerate(((3, 4), (5, 6), (7, 8))):
        made.append(_louvre_vane(f"{P}Louvre{n_}_{tag}", coll, side, kt, kb))

    # bonded doublers over each element joint, on the outer face
    pads = [("Main", -2.3900, 0.8110, 0.0700, 0.0225, -12.0),
            ("Flap", -2.5560, 0.8950, 0.0400, 0.0180, -22.0),
            ("Beam", -2.3760, 0.4640, 0.0550, 0.0200, -13.0)]
    for (nm, xc, zc, hx, hz, tilt) in pads:
        made.append(_ep_pad(f"{P}Pad{nm}_{tag}", coll, side, xc, zc, hx, hz,
                            tilt=tilt))

    # lower stiffener rib - and a row of rivets down it
    rib = [(x, _ZB(x) + 0.0235) for x in
           [C.lerp(-2.2450, -2.6150, i / 26.0) for i in range(27)]]
    made.append(_ep_strip(f"{P}RibLo_{tag}", coll, side, rib, 0.0090))
    rib2 = [(x, _ZT(x) - 0.0195) for x in
            [C.lerp(-2.4900, -2.6300, i / 12.0) for i in range(13)]]
    made.append(_ep_strip(f"{P}RibHi_{tag}", coll, side, rib2, 0.0070))

    # INNER face: bonded stiffeners + a doubler at the beam joint. Without
    # them the inboard side of the plate is 0.45 x 0.50 m of blank laminate -
    # the single largest featureless face on the part.
    for nm, xr in (("A", -2.3400), ("B", -2.5150)):
        z0 = _ZB(xr) + 0.0280
        z1 = _ZT(xr) - 0.1450
        vr = [(xr, C.lerp(z0, z1, i / 10.0)) for i in range(11)]
        made.append(_ep_strip(f"{P}RibIn{nm}_{tag}", coll, side, vr, 0.0068,
                              proud=0.0020, face=-1.0))
    ribin = [(x, _ZB(x) + 0.0215) for x in
             [C.lerp(-2.2600, -2.6050, i / 22.0) for i in range(23)]]
    made.append(_ep_strip(f"{P}RibLoIn_{tag}", coll, side, ribin, 0.0075,
                          proud=0.0020, face=-1.0))
    made.append(_ep_pad(f"{P}PadBeamIn_{tag}", coll, side, -2.3760, 0.4640,
                        0.0550, 0.0200, tilt=-13.0, face=-1.0))

    # fastener rows following the element joints, both faces
    screws, rivets = [], []
    joints = ((MAIN, Y_TIP, 11, True), (FLAP, Y_TIP, 7, True),
              (BEAM1, Y_BEAM_TIP, 6, False), (BEAM2, Y_BEAM_TIP, 5, False))
    for (e, ytip, n, rl) in joints:
        line = _elem_joint_line(e, side, ytip, n=n, roll=rl)
        for k, (x, z) in enumerate(line):
            p = _ep_face_pt(x, z, side, 1.0)
            nd = (0.0, side, 0.0)
            if k in (0, n - 1) or (n > 8 and k == n // 2):
                screws.append(_screw_geo(p, nd, r_head=0.0040, h_head=0.0030))
            else:
                rivets.append(_rivet_geo(p, nd))
            pi = _ep_face_pt(x, z, side, -1.0)
            rivets.append(_rivet_geo(pi, (0.0, -side, 0.0), r=0.0018, h=0.0008))
    # rivet border around the louvre panel
    xl0, xl1 = LOUVRE_X[0] - 0.012, LOUVRE_X[1] + 0.012
    for i in range(9):
        x = C.lerp(xl0, xl1, i / 8)
        for o in (TOP_OFFS[2] - 0.0050, TOP_OFFS[8] + 0.0085):
            rivets.append(_rivet_geo(_ep_face_pt(x, _ZT(x) - o, side, 1.0),
                                     (0.0, side, 0.0), r=0.0016, h=0.0007))
    for i in range(10):
        x = C.lerp(-2.2600, -2.6000, i / 9.0)
        rivets.append(_rivet_geo(_ep_face_pt(x, _ZB(x) + 0.0235, side, 1.0),
                                 (0.0, side, 0.0), r=0.0017, h=0.0007))
    for xr in (-2.3400, -2.5150):
        z0, z1 = _ZB(xr) + 0.0330, _ZT(xr) - 0.1500
        for i in range(7):
            rivets.append(_rivet_geo(
                _ep_face_pt(xr, C.lerp(z0, z1, i / 6.0), side, -1.0),
                (0.0, -side, 0.0), r=0.0016, h=0.0006))
    made.append(_merge_geo(f"{P}EPScrews_{tag}", coll, screws, "SteelFastener"))
    made.append(_merge_geo(f"{P}EPRivets_{tag}", coll, rivets, "Titanium", 46.0))
    return made


# --------------------------------------------------------------------------- #
# carbon blades from a 2D profile (pylons, brackets, stalks)
# --------------------------------------------------------------------------- #

def _poly_area(pts):
    n = len(pts)
    return 0.5 * sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1]
                     for i in range(n))


def _offset_outline(pts, dists):
    """Shrink a closed 2D outline inward by a per-point distance (bisectors)."""
    n = len(pts)
    sgn = 1.0 if _poly_area(pts) > 0.0 else -1.0
    out = []
    for i in range(n):
        px, pz = pts[(i - 1) % n]
        cx, cz = pts[i]
        nx, nz = pts[(i + 1) % n]
        b = Vector((0.0, 0.0))
        for (ax, az, bx, bz) in ((px, pz, cx, cz), (cx, cz, nx, nz)):
            ex, ez = bx - ax, bz - az
            L = math.hypot(ex, ez) or 1.0
            b += Vector((-sgn * ez / L, sgn * ex / L))    # inward normal
        if b.length < 1e-9:
            b = Vector((0.0, 1.0))
        b.normalize()
        # bisector shortening: keep the perpendicular offset equal to `d`
        ex, ez = nx - cx, nz - cz
        L = math.hypot(ex, ez) or 1.0
        nrm = Vector((-sgn * ez / L, sgn * ex / L))
        k = max(0.42, b.dot(nrm))
        d = dists[i] if isinstance(dists, (list, tuple)) else dists
        out.append((cx + b.x * d / k, cz + b.y * d / k))
    return out


def _blade(name, coll, outline, y_c, thick, radii=None, mat="CarbonFibre",
           smooth=36.0, nphi=7, y_scale=1.0):
    """Extrude a closed (x, z) outline along Y into a plate with rolled edges.

    `radii` is the edge radius at each outline point, so a pylon can carry a
    fat 11 mm leading edge and a 3 mm trailing edge on the same blade instead
    of the uniform round a bevel modifier would give.
    """
    R = 0.5 * thick
    if radii is None:
        radii = [R] * len(outline)
    rings = []
    for k in range(nphi):
        ph = math.pi * k / (nphi - 1)
        ins = [r * (1.0 - math.sin(ph)) for r in radii]
        pts = _offset_outline(outline, ins)
        yy = y_c + R * math.cos(ph) * y_scale
        rings.append([(x, yy, z) for (x, z) in pts])
    v, f = C.loft(rings, closed=True, cap_start=True, cap_end=True)
    ob = C.new_obj(name, v, f, coll=coll, smooth=True)
    C.merge_doubles(ob, 1e-5)
    C.shade_auto_smooth(ob, smooth)
    S.assign(ob, mat)
    return ob


def _radii_by_x(outline, r_front, r_rear):
    """Edge radius from chordwise position: fat rolled leading edge, thin
    trailing edge. A constant radius turns every strut into a round bar, and a
    round bar wrapped in a 5 mm twill reads as threaded rod (D-rw-08)."""
    xs = [q[0] for q in outline]
    x0, x1 = min(xs), max(xs)
    d = max(x1 - x0, 1e-6)
    return [C.lerp(r_rear, r_front, C.smoothstep((x - x0) / d)) for x in xs]


def _body_z(x, y):
    """z of the monocoque skin at (x, y) on its upper half - so the pylon feet
    land on the body instead of guessing a height."""
    best, bz = 1e9, 0.0
    for i in range(140):
        frac = 0.55 + 0.45 * i / 139.0
        yy, zz = S.body_surface_point(x, frac)
        d = abs(yy - abs(y))
        if d < best:
            best, bz = d, zz
    return bz


# --------------------------------------------------------------------------- #
# swan-neck pylons
# --------------------------------------------------------------------------- #

PYLON_Y = 0.0885
PYLON_T = 0.0172


def _contour_offset(e, y, idxs, gaps, y_tip=Y_TIP, roll=True):
    """Offset a run of an element's section contour outward by `gaps`.

    Used for the swan neck's inner edge: it must wrap the mainplane's leading
    edge with a real, visible slot, which is the whole point of a swan neck -
    the wing's suction surface stays untouched.
    """
    ring = _elem_ring(e, y, y_tip, roll)
    pts = [(q[0], q[2]) for q in ring]
    n = len(pts)
    area = sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1]
               for i in range(n))
    sgn = 1.0 if area > 0.0 else -1.0
    out = []
    for k, i in enumerate(idxs):
        ax, az = pts[(i - 1) % n]
        bx, bz = pts[(i + 1) % n]
        tx, tz = bx - ax, bz - az
        L = math.hypot(tx, tz) or 1.0
        nx, nz = sgn * tz / L, -sgn * tx / L
        g = gaps[k]
        out.append((pts[i][0] + nx * g, pts[i][1] + nz * g))
    return out


def _le_wrap_idx(s_up=0.100, s_lo=0.125):
    """Contour indices from the upper surface, round the LE, to the lower."""
    n = N_CHORD
    i_up = max(1, int(round(n * math.acos(1.0 - 2.0 * s_up) / math.pi)))
    i_lo = max(1, int(round(n * math.acos(1.0 - 2.0 * s_lo) / math.pi)))
    return list(range(i_up, -1, -1)) + [2 * n + 6 - k for k in range(1, i_lo + 1)]


def _pylon_outline():
    """Closed (x, z) loop: up the front edge, over the crown, down onto the
    mainplane's UPPER skin, forward along the bonded foot, then round the
    leading edge with a 6-13 mm slot and back down to the engine cover."""
    x_a, x_e = -2.0300, -2.1520
    z_a = _body_z(x_a, PYLON_Y) - 0.018
    z_e = _body_z(x_e, PYLON_Y) - 0.018

    front = C.catmull_rom(
        [(x_a, z_a), (-2.0555, z_a + 0.060), (-2.0850, 0.4880),
         (-2.1130, 0.5900), (-2.1400, 0.6850), (-2.1700, 0.7620),
         (-2.2010, 0.8140), (-2.2260, 0.8360), (-2.2450, 0.8398)], 30)
    crown = C.catmull_rom(
        [(-2.2450, 0.8398), (-2.2750, 0.8370), (-2.3050, 0.8280),
         (-2.3280, 0.8140), (-2.3395, 0.7990), (-2.3405, 0.7900)], 14)[1:]

    foot = []
    for i in range(14):
        ss = C.lerp(0.400, 0.112, i / 13.0)
        q, nn = _elem_pt(MAIN, PYLON_Y, ss, True)
        q = q - nn * (0.0032 * C.smoothstep((ss - 0.128) / 0.055))
        foot.append((q.x, q.z))

    idxs = _le_wrap_idx()
    m = len(idxs)
    gaps = []
    for k in range(m):
        t = k / (m - 1.0)
        gaps.append(C.smoothstep(t / 0.28)
                    * (0.0060 + 0.0078 * C.smoothstep((t - 0.55) / 0.45)))
    wrap = _contour_offset(MAIN, PYLON_Y, idxs, gaps)

    tail = C.catmull_rom(
        [wrap[-1], (-2.2540, 0.7060), (-2.2330, 0.6320), (-2.2050, 0.5420),
         (-2.1800, 0.4520), (x_e, z_e)], 22)[1:]
    return front + crown + foot + wrap + tail, len(front), len(crown)


def _build_pylons(coll):
    made = []
    outline, n_front, n_crown = _pylon_outline()
    n = len(outline)
    radii = []
    for i in range(n):
        # the fat rolled edge belongs to the FRONT edge and the crown only; the
        # foot, the leading-edge wrap and the aft edge are all trailing edges
        u = (i - n_front) / float(max(n_crown, 1))
        r = C.lerp(0.0086, 0.0026, C.smoothstep(u))
        radii.append(min(r, 0.5 * PYLON_T))
    for side in (1, -1):
        tag = "L" if side > 0 else "R"
        ob = _blade(f"{P}Pylon_{tag}", coll, outline, side * PYLON_Y, PYLON_T,
                    radii=radii, mat="CarbonFibre", smooth=32.0, nphi=9)
        made.append(_reframe(ob))

        # bolted foot flange on the mainplane's upper skin
        screws = []
        for s in (0.150, 0.225, 0.300):
            p, nd = _elem_pt(MAIN, side * PYLON_Y, s, True)
            for dy in (-0.0168, 0.0168):
                q = p + Vector((0.0, dy, 0.0)) + nd * 0.0004
                screws.append(_screw_geo(q, nd, r_head=0.0042, h_head=0.0031))
        made.append(_merge_geo(f"{P}PylonBolts_{tag}", coll, screws))

        # machined root flange where the blade enters the engine cover deck
        feet = []
        for nm, xr in (("F", -2.0480), ("R", -2.1360)):
            zz = _body_z(xr, PYLON_Y) + 0.004
            made.append(_prism(
                f"{P}PylonFoot{nm}_{tag}", coll,
                _rounded_rect(0.0250, 0.0105, 0.0045),
                (xr, side * PYLON_Y + 0.0175, zz), (1.0, 0.0, 0.0),
                (0.0, 0.0, 1.0), 0.0350, mat="Titanium", bevel=0.0012))
            for dy in (-0.0132, 0.0132):
                feet.append(_screw_geo((xr, side * PYLON_Y + dy, zz + 0.0100),
                                       (0.0, 0.0, 1.0), r_head=0.0036,
                                       h_head=0.0026))
        made.append(_merge_geo(f"{P}PylonFootBolts_{tag}", coll, feet))
    return made


# --------------------------------------------------------------------------- #
# DRS hinge line: mainplane bracket + flap clevis tabs + pin
# --------------------------------------------------------------------------- #

HINGE_Y = (0.1150, 0.2850, 0.4550)
PIVOT = (-2.5195, 0.8508)       # in the open slot gap, 8.8 mm below the flap


def _arc_outline(anchor, piv, R, n_arc=26):
    """anchor: material-side points (ordered). Wrap the long way round a pivot
    circle of radius R so the result is a simple polygon: a lug on a stalk."""
    px, pz = piv
    a0 = math.atan2(anchor[-1][1] - pz, anchor[-1][0] - px)
    a1 = math.atan2(anchor[0][1] - pz, anchor[0][0] - px)
    while a1 > a0:
        a1 -= C.TAU
    arc = [(px + R * math.cos(C.lerp(a0, a1, i / (n_arc - 1))),
            pz + R * math.sin(C.lerp(a0, a1, i / (n_arc - 1))))
           for i in range(n_arc)]
    return list(anchor) + arc


def _wrap_arc(p_from, p_to, piv, R, n=24):
    """Arc round `piv` covering everything the stalk does not - so the lug end
    of a bracket is a real circular boss."""
    a0 = math.atan2(p_from[1] - piv[1], p_from[0] - piv[0])
    a1 = math.atan2(p_to[1] - piv[1], p_to[0] - piv[0])
    while a1 > a0:
        a1 -= C.TAU
    return [(piv[0] + R * math.cos(C.lerp(a0, a1, i / (n - 1))),
             piv[1] + R * math.sin(C.lerp(a0, a1, i / (n - 1))))
            for i in range(n)]


def _hinge(coll, y, tag):
    made = []
    R = 0.0064
    foot, top, bolts = [], [], []
    for i in range(11):
        u = i / 10.0
        ss = C.lerp(0.690, 0.975, u)
        p, n = _elem_pt(MAIN, y, ss, True)
        pl, _ = _elem_pt(MAIN, y, ss, False)
        # The blade EMERGES from the wing instead of balancing on it with a
        # knife edge (D-rw-04) - but a FLAT 4 mm was the wrong way to do it.
        # The section runs out to 3.0 mm at ss=0.975, so 4 mm punched the foot
        # clean through the suction surface and left a teardrop of titanium
        # hanging under the wing at all six stations (D-rw-R2-03). Bury a
        # fraction of the LOCAL section thickness instead, so the foot is
        # always inside the skin no matter how thin the tail gets.
        th = (p - pl).length
        q = p - n * min(0.0040, 0.34 * th)
        foot.append((q.x, q.z))
        ht = 0.0042 + 0.0230 * C.smoothstep(u ** 0.85)
        t = p + n * ht
        top.append((t.x, t.z))
    for ss in (0.745, 0.895):
        p, n = _elem_pt(MAIN, y, ss, True)
        for dy in (-0.0102, 0.0102):
            bolts.append(_screw_geo(p + Vector((0.0, dy, 0.0)) + n * 0.0003, n,
                                    r_head=0.0033, h_head=0.0024,
                                    r_sock=0.0018, d_sock=0.0015))
    out = foot + _wrap_arc(foot[-1], top[-1], PIVOT, R) + top[::-1]
    rad = [0.0026] * len(out)
    ob = _blade(f"{P}Hinge_{tag}", coll, out, y, 0.0075, radii=rad,
                mat="Titanium", smooth=30.0, nphi=7)
    made.append(ob)
    made.append(_merge_geo(f"{P}HingeBolts_{tag}", coll, bolts))

    # D-rw-09: with the skin line 25 mm long and the eye only 2.4 mm clear of
    # the flap, the lug came out as a crescent with two knife points. A short
    # skin line, buried 4 mm into the flap, gives a solid clevis lug.
    tab = []
    for i in range(8):
        ss = C.lerp(0.075, 0.215, i / 7)
        q, nn = _elem_pt(FLAP, y, ss, False)
        q = q - nn * 0.0042
        tab.append((q.x, q.z))
    # aft -> forward so _arc_outline wraps the LONG way and the lug actually
    # encloses the pin. Listed forward -> aft it took the 85 deg short arc and
    # the "clevis" came out as a crescent floating above the pivot (D-rw-10).
    tab.reverse()
    out2 = _arc_outline(tab, PIVOT, 0.0058)
    rad2 = [0.0018] * len(out2)
    for dy in (-0.0062, 0.0062):
        ob = _blade(f"{P}HingeTab{'A' if dy < 0 else 'B'}_{tag}", coll, out2,
                    y + dy, 0.0042, radii=rad2, mat="Titanium", smooth=30.0,
                    nphi=6)
        made.append(ob)

    made.append(_tube(f"{P}HingePin_{tag}", coll,
                      [(PIVOT[0], y - 0.0128, PIVOT[1]),
                       (PIVOT[0], y - 0.0090, PIVOT[1]),
                       (PIVOT[0], y + 0.0090, PIVOT[1]),
                       (PIVOT[0], y + 0.0128, PIVOT[1])],
                      lambda t: 0.0029 if 0.2 < t < 0.8 else 0.0036,
                      coll_mat="SteelFastener", seg=20))
    return made


# --------------------------------------------------------------------------- #
# DRS actuator pod on the centreline
# --------------------------------------------------------------------------- #

def _main_upper_z(x):
    """z of the mainplane's upper skin at the centre section (constant in y for
    |y| < 0.30 * Y_TIP, which is where the pod and its fillet live)."""
    best, bz = 1e9, 0.0
    for i in range(400):
        s = i / 399.0
        p, _ = _elem_pt(MAIN, 0.0, s, True)
        d = abs(p.x - x)
        if d < best:
            best, bz = d, p.z
    return bz


def _pod_ring(x, w, h, n_se=30, n_fil=6, n_base=4):
    """Half superellipse standing on the wing skin, flaring into a bond fillet
    at both feet so the pod is moulded onto the wing, not dropped on it.

    Fixed point count at every station - a variable-length ring is what makes
    C.loft raise, and worse, a silently twisted surface if it does not.
    """
    zs = _main_upper_z(x)
    e = 2.0 / 2.7
    th0 = 0.16
    fo = 0.0018 + 0.075 * w                     # fillet reach outboard
    pb = (w * abs(math.cos(th0)) ** e, h * abs(math.sin(th0)) ** e)
    pa = (w + fo, -0.0013)
    pc = (w + 0.30 * fo, 0.0004)

    def bez(t):
        u = 1.0 - t
        return (u * u * pa[0] + 2 * u * t * pc[0] + t * t * pb[0],
                u * u * pa[1] + 2 * u * t * pc[1] + t * t * pb[1])

    fil = [bez(i / (n_fil - 1)) for i in range(n_fil)]
    se = []
    for i in range(n_se):
        th = C.lerp(th0, math.pi - th0, i / (n_se - 1))
        ct, st = math.cos(th), math.sin(th)
        se.append((w * math.copysign(abs(ct) ** e, ct), h * abs(st) ** e))
    prof = fil + se[1:-1] + [(-q[0], q[1]) for q in reversed(fil)]
    prof += [(C.lerp(-(w + fo), w + fo, i / float(n_base + 1)), -0.0013)
             for i in range(1, n_base + 1)]
    return [(x, dy, zs + dn) for (dy, dn) in prof]


# D-rw-R2-02. The pod used to run all the way back to the mainplane's trailing
# edge (x = -2.5079) and was still 36 mm tall there, while the flap's LOWER
# skin dips to z = 0.8555 right above it - so the dome ploughed 3.8 mm into the
# flap and its flat tail cap died inside the leading-edge underside. The flap's
# forward-most point is x = -2.4988, so the pod is now boat-tailed to close at
# x = -2.4966, ahead of the flap, and the actuator rod does the reaching.
POD_KEYS = [(-2.3950, 0.0120, 0.0175), (-2.4120, 0.0210, 0.0290),
            (-2.4300, 0.0268, 0.0368), (-2.4460, 0.0300, 0.0424),
            (-2.4600, 0.0302, 0.0436), (-2.4720, 0.0288, 0.0410),
            (-2.4820, 0.0254, 0.0342), (-2.4900, 0.0206, 0.0252),
            (-2.4950, 0.0164, 0.0186)]
POD_CTRL = C.catmull_rom(POD_KEYS, 34)

# Actuator rod centreline: out of the pod's tail, UNDER the flap's leading
# edge, up to the rod-end in the clevis. Every station is checked against the
# flap's lower skin - the rod used to be routed straight through it.
PUSHROD_PATH = [(-2.4870, 0.0, 0.8470), (-2.4930, 0.0, 0.8468),
                (-2.4990, 0.0, 0.8470), (-2.5080, 0.0, 0.8478),
                (-2.5180, 0.0, 0.8494), (-2.5290, 0.0, 0.8516),
                (-2.5405, 0.0, 0.8548)]
ROD_TIP = (-2.5405, 0.8548)


def _pushrod_r(t):
    """Fat spherical-bearing boss at the pod exit and at the rod end, slim
    shaft between - a stepped rod, not a length of dowel."""
    return (0.0031
            + 0.0019 * (1.0 - C.smoothstep(t / 0.22))
            + 0.0016 * C.smoothstep((t - 0.80) / 0.20))


def _pod_wh(x):
    """(half width, height) of the pod at station x."""
    xs = [c[0] for c in POD_CTRL]
    if x >= xs[0]:
        return POD_CTRL[0][1], POD_CTRL[0][2]
    if x <= xs[-1]:
        return POD_CTRL[-1][1], POD_CTRL[-1][2]
    for i in range(len(xs) - 1):
        if xs[i] >= x >= xs[i + 1]:
            t = (xs[i] - x) / (xs[i] - xs[i + 1] or 1.0)
            return (C.lerp(POD_CTRL[i][1], POD_CTRL[i + 1][1], t),
                    C.lerp(POD_CTRL[i][2], POD_CTRL[i + 1][2], t))
    return POD_CTRL[-1][1], POD_CTRL[-1][2]


def _pod_z(x, dy):
    w, h = _pod_wh(x)
    e = 2.0 / 2.7
    q = min(1.0, abs(dy) / max(w, 1e-6))
    ct = q ** (1.0 / e)
    st = math.sqrt(max(0.0, 1.0 - ct * ct))
    return _main_upper_z(x) + h * (st ** e)


def _pod_surf(x, dy):
    """Point + outward normal on the pod skin - so a hatch or a screw lands ON
    the dome instead of hovering over it (D-rw-03)."""
    d = 6e-4
    zc = _pod_z(x, dy)
    dzdy = (_pod_z(x, dy + d) - _pod_z(x, dy - d)) / (2 * d)
    dzdx = (_pod_z(x + d, dy) - _pod_z(x - d, dy)) / (2 * d)
    n = Vector((-dzdx, -dzdy, 1.0)).normalized()
    return Vector((x, dy, zc)), n


def _pod_pad(name, coll, xc, hx, hy, proud=0.0022, mat="CarbonMatte"):
    """Access hatch that follows the pod's dome."""
    ch = 0.0007
    out = _rounded_rect(hx, hy, min(hx, hy) * 0.42)
    inn = [(math.copysign(max(0.0, abs(a) - ch), a),
            math.copysign(max(0.0, abs(b) - ch), b)) for (a, b) in out]

    def place(pts, hgt):
        row = []
        for (dx, dy) in pts:
            p, n = _pod_surf(xc + dx, dy)
            row.append(tuple(p + n * hgt))
        return row

    rings = [place(out, -0.0008), place(out, proud - ch), place(inn, proud)]
    v, f = C.loft(rings, closed=True, cap_start=True, cap_end=True)
    ob = C.new_obj(name, v, f, coll=coll, smooth=True)
    C.merge_doubles(ob, 1e-6)
    C.shade_auto_smooth(ob, 30.0)
    S.assign(ob, mat)
    return ob


def _build_pod(coll):
    made = []
    ctrl = POD_CTRL
    rings = [_pod_ring(x, w, h) for (x, w, h) in ctrl]
    nose = _pod_ring(ctrl[0][0] + 0.0068, 0.0022, 0.0042)
    tail = _pod_ring(ctrl[-1][0] - 0.0016, 0.0120, 0.0144)
    v, f = C.loft([nose] + rings + [tail], closed=True,
                  cap_start=True, cap_end=True)
    ob = C.new_obj(f"{P}DRSPod", v, f, coll=coll, smooth=True)
    C.merge_doubles(ob, 1e-6)
    C.shade_auto_smooth(ob, 34.0)
    S.assign(ob, "CarbonFibre")
    made.append(ob)

    # access hatch on the crown + its four cap screws, all on the dome
    made.append(_pod_pad(f"{P}PodHatch", coll, -2.4560, 0.0235, 0.0150))
    scr = []
    for (dx, dy) in ((0.0182, 0.0098), (-0.0182, 0.0098),
                     (0.0182, -0.0098), (-0.0182, -0.0098)):
        q, n = _pod_surf(-2.4560 + dx, dy)
        scr.append(_screw_geo(q + n * 0.0020, n, r_head=0.0030, h_head=0.0022,
                              r_sock=0.0017, d_sock=0.0014))
    made.append(_merge_geo(f"{P}PodScrews", coll, scr))

    # actuator pushrod: pod tail -> clevis lever under the flap.
    # The lever's skin line is BURIED 3.5 mm into the flap (the section is
    # 12-13 mm thick over ss 0.15..0.36) so the tabs grow out of the flap
    # instead of kissing it tangentially, and the lug radius now clears the
    # rod-end boss rather than being smaller than it.
    lever = []
    for i in range(7):
        s = C.lerp(0.150, 0.360, i / 6)
        p, nn = _elem_pt(FLAP, 0.0, s, False)
        p = p - nn * 0.0035
        lever.append((p.x, p.z))
    lever.reverse()
    tip = ROD_TIP
    out = _arc_outline(lever, tip, 0.0074)
    for dy in (-0.0074, 0.0074):
        made.append(_blade(f"{P}PodLever{'A' if dy < 0 else 'B'}", coll, out,
                           dy, 0.0038, radii=[0.0016] * len(out),
                           mat="Titanium", smooth=30.0, nphi=6))
    made.append(_tube(f"{P}PushRod", coll, PUSHROD_PATH, _pushrod_r,
                      coll_mat="Titanium", seg=20))
    made.append(_tube(f"{P}PushPin", coll,
                      [(tip[0], -0.0112, tip[1]), (tip[0], 0.0112, tip[1])],
                      0.0026, coll_mat="SteelFastener", seg=16))
    return made


# --------------------------------------------------------------------------- #
# gurney flap on the flap trailing edge
# --------------------------------------------------------------------------- #

def _gurney_h(a):
    """8 mm inboard, stepping to 12.5 mm over the outer 170 mm - the tip gurney."""
    return 0.0070 + 0.0045 * C.smoothstep((a - 0.655) / 0.055)


def _build_gurney(coll):
    ys = _span_stations(193, Y_TIP)
    t = 0.0023
    rings = []
    for y in ys:
        lex, lez, ch, inc, cam, th = _elem_params(FLAP, y, Y_TIP, True)
        ca, sa = math.cos(inc), math.sin(inc)
        eu = Vector((-ca, 0.0, sa))          # aft along the chord
        ev = Vector((sa, 0.0, ca))           # normal, pressure side up
        te = Vector((lex, y, lez)) + eu * ch
        hgt = _gurney_h(min(1.0, abs(y) / Y_TIP))
        prof = [(TE_HALF, 0.0), (TE_HALF, hgt - 0.0009)]
        for k in range(5):
            aa = math.radians(90.0 * k / 4.0)
            prof.append((TE_HALF - 0.0009 + 0.0009 * math.cos(aa),
                         hgt - 0.0009 + 0.0009 * math.sin(aa)))
        prof += [(TE_HALF - t, hgt - 0.0009), (TE_HALF - t, 0.0),
                 (TE_HALF - t, -0.0016), (TE_HALF, -0.0016)]
        rings.append([tuple(te + eu * u + ev * v) for (u, v) in prof])
    v, f = C.loft(rings, closed=True, cap_start=True, cap_end=True)
    ob = C.new_obj(f"{P}Gurney", v, f, coll=coll, smooth=True)
    C.merge_doubles(ob, 1e-6)
    C.shade_auto_smooth(ob, 32.0)
    # D-rw-11: a 7 mm tab seen edge-on carries barely one 5 mm twill cell, and
    # the shared weave bump aliases across it into a zipper. A gurney is a
    # painted/bonded tab, not exposed weave - MatteBlack kills the artefact.
    S.assign(ob, "MatteBlack")
    return [ob]


# --------------------------------------------------------------------------- #
# beam wing, its centre struts and the rain light
# --------------------------------------------------------------------------- #

def _build_beam(coll):
    made = [
        _loft_element(f"{P}Beam1", BEAM1, coll, y_tip=Y_BEAM_TIP, n_span=161,
                      roll=False),
        _loft_element(f"{P}Beam2", BEAM2, coll, y_tip=Y_BEAM_TIP, n_span=161,
                      roll=False),
    ]
    # two struts from the engine-cover deck up to the beam wing's lower skin
    for side in (1, -1):
        tag = "L" if side > 0 else "R"
        yv = side * 0.0520
        top = []
        for i in range(11):
            ss = C.lerp(0.070, 0.520, i / 10)
            q, _ = _elem_pt(BEAM1, yv, ss, False, Y_BEAM_TIP, False)
            top.append((q.x, q.z))
        # D-rw-07: the base used to sample the body at each corner's own x. The
        # tail cone collapses so fast there that the aft corner landed at
        # z=0.178 and the "strut" grew into a 230 mm fin. One level base, taken
        # where the deck actually is, keeps it a 140 mm pillar.
        x_aft, x_fwd = top[-1][0] - 0.006, top[0][0] + 0.008
        z_base = _body_z(0.5 * (x_aft + x_fwd), abs(yv)) - 0.015
        out = top + [(x_aft, z_base + 0.026), (x_aft, z_base),
                     (x_fwd, z_base), (x_fwd, z_base + 0.024)]
        rad = _radii_by_x(out, 0.0070, 0.0024)
        made.append(_reframe(_blade(f"{P}BeamStrut_{tag}", coll, out, yv,
                                    0.0140, radii=rad, mat="CarbonFibre",
                                    smooth=32.0, nphi=9)))
    return made


def _build_rainlight(coll):
    made = []
    xc, zc = -2.4880, 0.3520
    # stalk hanging off the beam wing's lower skin at the centreline
    top = []
    for i in range(9):
        s = C.lerp(0.140, 0.780, i / 8)
        p, _ = _elem_pt(BEAM2, 0.0, s, False, Y_BEAM_TIP, False)
        top.append((p.x, p.z))
    out = top + [(top[-1][0] + 0.004, zc + 0.016), (xc + 0.020, zc + 0.014),
                 (xc + 0.026, zc + 0.028)]
    made.append(_reframe(_blade(f"{P}RainStalk", coll, out, 0.0, 0.0132,
                                radii=_radii_by_x(out, 0.0064, 0.0024),
                                mat="CarbonFibre", smooth=32.0, nphi=9)))

    # housing: a rounded box facing aft, with a bezel and a lens
    body = _rounded_rect(0.0300, 0.0225, 0.0075)
    made.append(_prism(f"{P}RainHousing", coll, body,
                       (xc + 0.0240, 0.0, zc), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0),
                       -0.0400, mat="CarbonFibre", bevel=0.0022, bseg=4))
    bez = _rounded_rect(0.0262, 0.0188, 0.0060)
    made.append(_prism(f"{P}RainBezel", coll, bez,
                       (xc - 0.0154, 0.0, zc), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0),
                       -0.0026, mat="MatteBlack", bevel=0.0009))
    lens = _rounded_rect(0.0228, 0.0156, 0.0050)
    rings = []
    for k in range(4):
        t = k / 3.0
        sc = 1.0 - 0.10 * t * t
        rings.append([(xc - 0.0180 - 0.0026 * math.sin(t * math.pi * 0.5),
                       u * sc, zc + v * sc) for (u, v) in lens])
    v, f = C.loft(rings, closed=True, cap_start=True, cap_end=True)
    ob = C.new_obj(f"{P}RainLens", v, f, coll=coll, smooth=True)
    C.merge_doubles(ob, 1e-6)
    C.shade_auto_smooth(ob, 40.0)
    S.assign(ob, "AnodisedRed")
    made.append(ob)

    scr = [_screw_geo((xc - 0.0160, dy, zc + dz), (-1.0, 0.0, 0.0),
                      r_head=0.0030, h_head=0.0022, r_sock=0.0017,
                      d_sock=0.0014)
           for (dy, dz) in ((0.0272, 0.0110), (-0.0272, 0.0110),
                            (0.0272, -0.0110), (-0.0272, -0.0110))]
    made.append(_merge_geo(f"{P}RainScrews", coll, scr))
    return made


# --------------------------------------------------------------------------- #
# assembly
# --------------------------------------------------------------------------- #

def build(coll, ctx=None):
    made = []

    made.append(_loft_element(f"{P}Mainplane", MAIN, coll))
    made.append(_loft_element(f"{P}Flap", FLAP, coll, n_span=161))
    made += _build_gurney(coll)
    made += _build_beam(coll)
    made += _build_pod(coll)
    made += _build_rainlight(coll)
    made += _build_pylons(coll)

    for y in HINGE_Y:
        for side in (1, -1):
            made += _hinge(coll, side * y, f"{'L' if side > 0 else 'R'}"
                           f"{int(round(y * 1000))}")

    for side in (1, -1):
        tag = "L" if side > 0 else "R"
        made += _build_endplate(coll, side)
        for (nm, e, ytip, rl) in (("Main", MAIN, Y_TIP, True),
                                  ("Flap", FLAP, Y_TIP, True),
                                  ("Beam1", BEAM1, Y_BEAM_TIP, False),
                                  ("Beam2", BEAM2, Y_BEAM_TIP, False)):
            made.append(_root_fillet(f"{P}Fillet{nm}_{tag}", coll, e, side,
                                     ytip, roll=rl))
    return made
