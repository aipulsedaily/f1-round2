"""halo_assembly - FIA halo, its aero fairing, three machined mounts, T-cam pod.

Layout (car-local metres, +X forward, +Y left, +Z up, tyre contact z = 0)
-----------------------------------------------------------------------
    hoop        titanium tube, 45 mm OD, anchored low behind each shoulder at
                (-0.075, +-0.335, 0.690), arcing forward/up to (0.890, 0, 0.860)
    pillar      titanium, (0.905, 0, 0.606) up to the hoop front point
    fairing     three carbon mouldings that clad the hoop (front piece across
                the nose, one per rear leg) plus a deeper blade on the pillar.
                Each moulding is a real shell: outer skin, inner skin, and a
                moulded collar at each end that seals onto the bare tube, so the
                titanium reads at the joints and at both rear legs. Every
                section is sized to enclose tube + seal gap + laminate (see
                _enclose), which is what keeps the skin outside the tube and the
                bore inside the skin.

                Each moulding is built as four laminate strips, parted at the
                leading edge, the trailing edge and the two parting-line
                grooves. They share their boundary vertices, so the skin is
                continuous; splitting them lets each strip carry its own weave
                frame when the carbon material needs one (_align_weave).
    mounts      front clevis foot on the bulkhead crown + two shoulder feet,
                all machined titanium on conforming pads with visible bolts
    pod         T-camera on the roll-hoop crown behind the halo, on a saddle
                plate that follows the airbox ridge
    fin         GPS/telemetry blade aft of the pod

Everything that touches the monocoque is sampled off spec.BODY_STATIONS via a
local, unsnapped copy of body_surface_point (spec's own helper quantises frac
to 1/64, which turns a conforming pad into a staircase), and buried a few mm so
a slightly different skin still cannot leave a bracket floating.
"""

import math

from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

import common as C
import spec as S

NAME = "halo_assembly"
P = NAME + "_"
TAU = math.pi * 2.0


# --------------------------------------------------------------------------- #
# hoop centreline
#
# Authored as a half (front centre -> rear tip -> a short tail that plunges into
# the shoulder bracket), then mirrored.  Mirroring the control points instead of
# fitting a closed curve is what guarantees the tangent at the centre is purely
# lateral, so the pillar meets a genuinely smooth apex.
# --------------------------------------------------------------------------- #

HOOP_HALF = [
    (0.8900, 0.0000, 0.8600),
    (0.8800, 0.0520, 0.8595),
    (0.8520, 0.1040, 0.8572),
    (0.8060, 0.1560, 0.8540),
    (0.7420, 0.2060, 0.8500),
    (0.6600, 0.2520, 0.8452),
    (0.5600, 0.2920, 0.8385),
    (0.4460, 0.3220, 0.8292),
    (0.3220, 0.3430, 0.8162),
    (0.1960, 0.3520, 0.7990),
    (0.0700, 0.3530, 0.7760),
    (-0.0120, 0.3490, 0.7520),
    (-0.0520, 0.3430, 0.7200),
    (-0.0750, 0.3350, 0.6900),      # the anchor point in the brief
    (-0.0768, 0.3255, 0.6790),
    (-0.0782, 0.3175, 0.6690),
    (-0.0790, 0.3140, 0.6645),
    (-0.0807, 0.3067, 0.6551),      # buried in the shoulder bracket socket
]

TUBE_R = 0.0225                     # 45 mm OD titanium section
PATH_N = 380                        # arc-uniform samples over the whole hoop

# fairing spans, arc length from the front centre (metres)
FAIR_FRONT_S = 0.575
FAIR_REAR_S0 = 0.640
FAIR_REAR_S1 = 1.044

PILLAR_FOOT_Z = 0.6060
PILLAR_X = 0.9050

WALL = 0.0026                       # fairing laminate
SEAM_XC = 0.345                     # parting line, fraction of chord
GAP = 0.0012                        # moulding-to-tube seal clearance


# --------------------------------------------------------------------------- #
# small mesh utilities (kept inside the module - common.py is frozen)
# --------------------------------------------------------------------------- #

class Acc:
    """Vert/face accumulator so a whole family of fasteners is one object."""

    def __init__(self):
        self.v = []
        self.f = []

    def add(self, verts, faces, xf=None):
        o = len(self.v)
        if xf is None:
            self.v.extend(tuple(p) for p in verts)
        else:
            self.v.extend(tuple(xf @ Vector(p)) for p in verts)
        self.f.extend(tuple(i + o for i in fc) for fc in faces)
        return o


def _basis(origin, zax, xhint=(1.0, 0.0, 0.0)):
    z = Vector(zax).normalized()
    x = Vector(xhint)
    x = x - z * x.dot(z)
    if x.length < 1e-7:
        x = Vector((0.0, 0.0, 1.0))
        x = x - z * x.dot(z)
        if x.length < 1e-7:
            x = Vector((0.0, 1.0, 0.0))
            x = x - z * x.dot(z)
    x.normalize()
    y = z.cross(x)
    return Matrix(((x.x, y.x, z.x, origin[0]),
                   (x.y, y.y, z.y, origin[1]),
                   (x.z, y.z, z.z, origin[2]),
                   (0.0, 0.0, 0.0, 1.0)))


def _ring_faces(base, n, rows, wrap=True, close=False):
    """Quad faces for a stack of `rows` rings of `n` verts each."""
    f = []
    span = n if wrap else n - 1
    for i in range(rows - 1):
        a, b = base + i * n, base + (i + 1) * n
        for k in range(span):
            k2 = (k + 1) % n
            f.append((a + k, a + k2, b + k2, b + k))
    if close and rows > 2:
        a, b = base + (rows - 1) * n, base
        for k in range(span):
            k2 = (k + 1) % n
            f.append((a + k, a + k2, b + k2, b + k))
    return f


def _flat(rings):
    return [tuple(v) for r in rings for v in r]


def _fan(verts, faces, base, n, flip=False):
    """Close a NON-planar ring with a centroid fan.

    An n-gon over a ring that is not flat (a pod nose sitting on the airbox
    ridge, a fin root following the skin) tessellates into spikes - harmless in
    a beauty render until anything reads the mesh, and instantly visible under
    --wire as slivers shooting off the part. A fan is well behaved.
    """
    ring = verts[base:base + n]
    cx = sum(v[0] for v in ring) / n
    cy = sum(v[1] for v in ring) / n
    cz = sum(v[2] for v in ring) / n
    c = len(verts)
    verts.append((cx, cy, cz))
    for k in range(n):
        k2 = (k + 1) % n
        faces.append((c, base + k2, base + k) if flip else (c, base + k, base + k2))
    return c


def _obj(name, verts, faces, coll, mat, smooth=True, auto=34.0):
    ob = C.new_obj(P + name, verts, faces, coll=coll, smooth=smooth)
    C.merge_doubles(ob, 1e-6)
    if auto is not None:
        C.shade_auto_smooth(ob, auto)
    S.assign(ob, mat)
    return ob


def _pca_axis(pairs):
    """Dominant axis of an area-weighted normal cloud [(area, normal), ...].

    The top eigenvector of sum(area * n n^T) - found by power iteration, since
    mathutils has no eigensolver. For a fan of normals this lands on the middle
    of the fan, which is exactly where the weave projection axis wants to be.
    """
    m = [[0.0] * 3 for _ in range(3)]
    for a, n in pairs:
        for i in range(3):
            for j in range(3):
                m[i][j] += a * n[i] * n[j]
    v = Vector((0.317, 0.523, 0.791))
    for _ in range(32):
        w = Vector(tuple(sum(m[i][j] * v[j] for j in range(3)) for i in range(3)))
        if w.length < 1e-14:
            return Vector((0.0, 0.0, 1.0))
        v = w.normalized()
    return v


def _face_normals(ob):
    return [(p.area, Vector(p.normal)) for p in ob.data.polygons if p.area > 1e-12]


def _weave_axis(pairs, t=0.35):
    """Projection axis that leaves the least streaked area.

    A surface streaks where its normal is perpendicular to the axis (the twill
    is constant along it), so this minimises the area with |n . a| < t: a
    coarse sweep of the hemisphere from the PCA axis, then hill-climbing.
    Sub-sampled to keep a full part rebuild under a second of this.
    """
    if not pairs:
        return Vector((0.0, 0.0, 1.0))
    if len(pairs) > 640:
        pairs = pairs[::len(pairs) // 640 + 1]

    def cost(a):
        return sum(ar for ar, n in pairs if abs(n.dot(a)) < t)

    best_a = _pca_axis(pairs)
    best = cost(best_a)
    for i in range(1, 18):
        st, ct = math.sin(math.pi * i / 18.0), math.cos(math.pi * i / 18.0)
        for j in range(36):
            a = Vector((st * math.cos(TAU * j / 36.0),
                        st * math.sin(TAU * j / 36.0), ct))
            c = cost(a)
            if c < best:
                best, best_a = c, a
    for step in (0.20, 0.08, 0.03):
        moved = True
        while moved:
            moved = False
            for d in ((step, 0, 0), (-step, 0, 0), (0, step, 0),
                      (0, -step, 0), (0, 0, step), (0, 0, -step)):
                a = (best_a + Vector(d)).normalized()
                c = cost(a)
                if c < best - 1e-12:
                    best, best_a, moved = c, a, True
    return best_a


_TRIPLANAR = None


def _weave_is_triplanar():
    """Does the shared carbon material project its twill on all three planes?

    Read-only introspection of the frozen material, and it decides whether the
    geometry-side workaround below is wanted at all:

      * single projection  - the twill is constant along object z, so every
        object needs its own frame or it streaks (R2-D1).
      * triplanar          - the blend weights come from the WORLD normal while
        the projections are in OBJECT space, so the two only line up while the
        object frame IS world. Rotating an object would now pick the wrong
        projection for a face and re-introduce the smear.

    So: rotate only when rotating is the fix.
    """
    global _TRIPLANAR
    if _TRIPLANAR is None:
        nt = S.mat("CarbonFibre").node_tree
        _TRIPLANAR = sum(1 for n in nt.nodes
                         if n.bl_idname == "ShaderNodeTexWave") > 2
    return _TRIPLANAR


def _align_weave(ob, axis=None):
    """Spin the mesh into a local frame that suits the carbon weave, and put
    the rotation on the object so nothing moves in world space.

    A single-projection weave maps its twill from OBJECT coordinates with bands
    in local x and y, so the pattern is CONSTANT along local z. Any face whose
    normal is perpendicular to local z is therefore stretched into vertical
    corduroy instead of a 2x2 twill (R2-D1: 32 % of the front moulding, 87 % of
    the crown vanes). The material is frozen, so the object's own frame is the
    only lever: point local z down the dominant normal of this piece. For a
    doubly curved hoop one frame is not enough - the moulding is split into
    laminate strips first, each of which gets its own.
    """
    if _weave_is_triplanar():
        return ob
    a = Vector(axis) if axis is not None else _weave_axis(_face_normals(ob))
    if a.length < 1e-9:
        return ob
    R = _basis((0.0, 0.0, 0.0), a.normalized())
    ob.data.transform(R.inverted())
    ob.matrix_world = R
    return ob


def _frames(pts):
    """Parallel-transported (tangent, normal, binormal) along a polyline."""
    n = len(pts)
    tg = []
    for i in range(n):
        if i == 0:
            t = pts[1] - pts[0]
        elif i == n - 1:
            t = pts[-1] - pts[-2]
        else:
            t = pts[i + 1] - pts[i - 1]
        tg.append(t.normalized())
    ref = Vector((0.0, 0.0, 1.0))
    if abs(tg[0].dot(ref)) > 0.9:
        ref = Vector((1.0, 0.0, 0.0))
    nr = (ref - tg[0] * ref.dot(tg[0])).normalized()
    nrm, bin_ = [], []
    for t in tg:
        nr = (nr - t * nr.dot(t))
        if nr.length < 1e-8:
            nr = Vector((0.0, 0.0, 1.0)) - t * t.z
        nr.normalize()
        nrm.append(nr.copy())
        bin_.append(t.cross(nr).normalized())
    return tg, nrm, bin_


def _resample(pts, n):
    d = [0.0]
    for i in range(1, len(pts)):
        d.append(d[-1] + (pts[i] - pts[i - 1]).length)
    total = d[-1]
    out, j = [], 0
    for i in range(n):
        s = total * i / (n - 1)
        while j < len(d) - 2 and d[j + 1] < s:
            j += 1
        seg = max(d[j + 1] - d[j], 1e-12)
        out.append(pts[j].lerp(pts[j + 1], (s - d[j]) / seg))
    return out, total


def _sweep_circle(pts, r_of_i, seg=32, cap=True):
    tg, nr, bn = _frames(pts)
    rings = []
    for i, p in enumerate(pts):
        r = r_of_i(i)
        rings.append([p + nr[i] * (math.cos(TAU * k / seg) * r)
                      + bn[i] * (math.sin(TAU * k / seg) * r) for k in range(seg)])
    verts = _flat(rings)
    faces = _ring_faces(0, seg, len(rings))
    if cap:
        faces.append(tuple(range(seg))[::-1])
        s = (len(rings) - 1) * seg
        faces.append(tuple(range(s, s + seg)))
    return verts, faces


# --------------------------------------------------------------------------- #
# monocoque skin sampling (local, unsnapped)
# --------------------------------------------------------------------------- #

_PROF = {}


def _profile(x):
    k = round(x, 4)
    p = _PROF.get(k)
    if p is None:
        p = C.catmull_rom(S.station_half(S.station_at(k)), 401)
        _PROF[k] = p
    return p


def _skin(x, frac):
    p = _profile(x)
    f = min(max(frac, 0.0), 1.0) * 400.0
    i = min(int(f), 399)
    t = f - i
    a, b = p[i], p[i + 1]
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def _skin_pt(x, frac, side=1.0):
    y, z = _skin(x, frac)
    return Vector((x, y * side, z))


def _skin_n(x, frac, side=1.0):
    d = 0.0025
    a = _skin_pt(x + d, frac, side)
    b = _skin_pt(x - d, frac, side)
    c = _skin_pt(x, min(frac + 0.004, 1.0), side)
    e = _skin_pt(x, max(frac - 0.004, 0.0), side)
    n = (a - b).cross(c - e)
    if n.length < 1e-9:
        return Vector((0.0, 0.0, 1.0))
    n.normalize()
    if n.z < 0.0:
        n = -n
    return n


def _skin_z_of_y(x, y, fmin=0.78):
    """Top-surface height at (x, y) - only valid above the widest station."""
    p = _profile(x)
    ay = abs(y)
    i0 = int(fmin * 400)
    for i in range(len(p) - 1, i0, -1):
        y1, z1 = p[i]
        y0, z0 = p[i - 1]
        if (y1 - ay) * (y0 - ay) <= 0.0 and abs(y0 - y1) > 1e-9:
            t = (ay - y1) / (y0 - y1)
            return z1 + (z0 - z1) * t
    return p[-1][1]


def _crown_n(x, y):
    d = 0.004
    a = Vector((x + d, y, _skin_z_of_y(x + d, y)))
    b = Vector((x - d, y, _skin_z_of_y(x - d, y)))
    c = Vector((x, y + d, _skin_z_of_y(x, y + d)))
    e = Vector((x, y - d, _skin_z_of_y(x, y - d)))
    n = (a - b).cross(c - e)
    if n.length < 1e-9:
        return Vector((0.0, 0.0, 1.0))
    n.normalize()
    return -n if n.z < 0.0 else n


def _slab(rows_p, rows_n, up, down):
    """Closed slab from a grid of surface points + normals."""
    nr, nc = len(rows_p), len(rows_p[0])
    top = [[rows_p[i][j] + rows_n[i][j] * up for j in range(nc)] for i in range(nr)]
    bot = [[rows_p[i][j] - rows_n[i][j] * down for j in range(nc)] for i in range(nr)]
    verts = _flat(top) + _flat(bot)
    off = nr * nc
    faces = []
    for i in range(nr - 1):
        for j in range(nc - 1):
            a = i * nc + j
            faces.append((a, a + 1, a + nc + 1, a + nc))
            b = off + a
            faces.append((b + nc, b + nc + 1, b + 1, b))
    for j in range(nc - 1):
        a = j
        faces.append((a + 1, a, off + a, off + a + 1))
        a = (nr - 1) * nc + j
        faces.append((a, a + 1, off + a + 1, off + a))
    for i in range(nr - 1):
        a = i * nc
        faces.append((a, a + nc, off + a + nc, off + a))
        a = i * nc + nc - 1
        faces.append((a + nc, a, off + a, off + a + nc))
    return verts, faces


def _span(a, b, n, edge=0.055):
    """Parameter list with a tight pair of rings at each end.

    The close pair is what lets a pad carry a real machined step around its
    perimeter: a 4 mm drop across 3 mm of surface reads as a milled land, the
    same drop across a 7 mm grid cell only reads as a soft slump.
    """
    fr = [0.0, edge * 0.45, edge]
    for i in range(1, n - 1):
        fr.append(edge + (1.0 - 2.0 * edge) * i / (n - 1.0))
    fr += [1.0 - edge, 1.0 - edge * 0.45, 1.0]
    return [C.lerp(a, b, t) for t in fr]


def _stepped_slab(rp, rn, up_hi, up_lo, down):
    nr, nc = len(rp), len(rp[0])

    def up(i, j):
        return up_lo if (i < 2 or i > nr - 3 or j < 2 or j > nc - 3) else up_hi

    top = [[rp[i][j] + rn[i][j] * up(i, j) for j in range(nc)] for i in range(nr)]
    bot = [[rp[i][j] - rn[i][j] * down for j in range(nc)] for i in range(nr)]
    verts = _flat(top) + _flat(bot)
    off = nr * nc
    faces = []
    for i in range(nr - 1):
        for j in range(nc - 1):
            a = i * nc + j
            faces.append((a, a + 1, a + nc + 1, a + nc))
            b = off + a
            faces.append((b + nc, b + nc + 1, b + 1, b))
    for j in range(nc - 1):
        a = j
        faces.append((a + 1, a, off + a, off + a + 1))
        a = (nr - 1) * nc + j
        faces.append((a, a + 1, off + a + 1, off + a))
    for i in range(nr - 1):
        a = i * nc
        faces.append((a, a + nc, off + a + nc, off + a))
        a = i * nc + nc - 1
        faces.append((a + nc, a, off + a, off + a + nc))
    return verts, faces


def _spotface(acc, origin, zax, r=0.0108, h=0.0020, seg=36):
    """Machined seat under a bolt head.

    R2-D9: the first version stopped at the counterbore rim, leaving two open
    rings (1008 open-boundary edges across the part). Closing the profile back
    down the bore makes each seat a real machined ring - closed, manifold, and
    still hidden under its bolt head.
    """
    rows = [_circ(r * 0.42, 0.0, seg), _circ(r, 0.0, seg),
            _circ(r, h - 0.0006, seg), _circ(r - 0.0007, h, seg),
            _circ(r * 0.42, h, seg)]
    v = _flat(rows)
    f = _ring_faces(0, seg, len(rows), close=True)
    acc.add(v, f, _basis(origin, zax))


# --------------------------------------------------------------------------- #
# fasteners
# --------------------------------------------------------------------------- #

def _hex_r(theta, ri):
    a = (theta + math.pi / 6.0) % (math.pi / 3.0) - math.pi / 6.0
    return ri / math.cos(a)


def _circ(r, z, seg):
    return [(r * math.cos(TAU * k / seg), r * math.sin(TAU * k / seg), z)
            for k in range(seg)]


def _hexring(ri, z, seg, grow=0.0):
    out = []
    for k in range(seg):
        t = TAU * k / seg
        r = _hex_r(t, ri) + grow
        out.append((r * math.cos(t), r * math.sin(t), z))
    return out


def _cap_screw(acc, origin, zax, xhint=(1, 0, 0), d=0.008, hd=0.0132, hh=0.0072,
               shank=0.014, washer=0.0, seg=48, sock=0.62):
    """Hex-socket cap screw, seating face at the origin, axis +z."""
    ri = hd * 0.30                      # socket across-flats / 2
    sd = hh * sock
    rings = [
        _hexring(ri, hh - sd, seg),
        _hexring(ri, hh - 0.0007, seg),
        _hexring(ri, hh, seg, grow=0.0005),
        _circ(hd * 0.5 - 0.0006, hh, seg),
        _circ(hd * 0.5, hh - 0.0007, seg),
        _circ(hd * 0.5, 0.0007, seg),
        _circ(hd * 0.5 - 0.0006, 0.0, seg),
        _circ(d * 0.5 + 0.0005, 0.0, seg),
        _circ(d * 0.5, -0.0005, seg),
        _circ(d * 0.5, -shank + 0.0006, seg),
        _circ(d * 0.5 - 0.0006, -shank, seg),
    ]
    verts = _flat(rings)
    faces = _ring_faces(0, seg, len(rings))
    faces.append(tuple(range(seg)))                       # socket floor
    s = (len(rings) - 1) * seg
    faces.append(tuple(range(s, s + seg))[::-1])          # shank end
    acc.add(verts, faces, _basis(origin, zax, xhint))

    if washer > 0.0:
        _washer(acc, origin, zax, xhint, ro=hd * 0.62, rw=d * 0.55, t=washer,
                seg=seg)


def _washer(acc, origin, zax, xhint=(1, 0, 0), ro=0.0109, rw=0.0057, t=0.0016,
            seg=48):
    """Plain washer, seating face at the origin, body BELOW it (-z)."""
    wr = [
        _circ(rw, 0.0, seg), _circ(ro - 0.0004, 0.0, seg),
        _circ(ro, -0.0004, seg), _circ(ro, -t + 0.0004, seg),
        _circ(ro - 0.0004, -t, seg), _circ(rw, -t, seg),
    ]
    acc.add(_flat(wr), _ring_faces(0, seg, len(wr), close=True),
            _basis(origin, zax, xhint))


def _flush_screw(acc, origin, zax, xhint=(1, 0, 0), hd=0.0104, seg=36):
    """Countersunk socket screw in a parting line, seating face at the origin.

    R2-D7: the ring stack used to run +0.0004 DOWN to -0.0022 and was capped at
    the top, so the hex recess opened into the panel and the visible face was a
    plain closed dome - 68 fasteners rendering as blank 10 mm blisters. The
    stack now starts at the socket floor and climbs: hex walls -> broken mouth
    -> flat head top -> countersink cone -> shank. The drive faces the camera.
    """
    # Depth budget: these sit in a 2.6 mm laminate over a 1.2 mm seal gap, so
    # nothing may reach more than ~3.8 mm below the seat or the shank spears the
    # titanium tube underneath (it did: 1308 tri pairs against HoopTube).
    ri = hd * 0.26
    top = 0.0006
    rings = [
        _hexring(ri * 0.52, -0.0018, seg),               # socket floor
        _hexring(ri, -0.0014, seg),                      # floor fillet
        _hexring(ri, top - 0.0004, seg),                 # socket wall
        _hexring(ri + 0.0004, top, seg),                 # broken mouth
        _circ(hd * 0.5 - 0.0006, top, seg),              # flat head face
        _circ(hd * 0.5, top - 0.0005, seg),              # head OD, edge broken
        _circ(hd * 0.34, -0.0022, seg),                  # 90 deg countersink
        _circ(hd * 0.24, -0.0034, seg),                  # shank into the panel
    ]
    verts = _flat(rings)
    faces = _ring_faces(0, seg, len(rings))
    faces.append(tuple(range(seg))[::-1])                # socket floor cap
    s = (len(rings) - 1) * seg
    faces.append(tuple(range(s, s + seg)))               # shank end
    acc.add(verts, faces, _basis(origin, zax, xhint))


def _hex_nut(acc, origin, zax, xhint=(1, 0, 0), af=0.0125, h=0.0062, bore=0.0072,
             seg=48):
    ri = af * 0.5
    rings = [
        _circ(bore * 0.5, 0.0, seg),
        _hexring(ri - 0.0006, 0.0, seg),
        _hexring(ri, 0.0006, seg),
        _hexring(ri, h - 0.0006, seg),
        _hexring(ri - 0.0006, h, seg),
        _circ(bore * 0.5, h, seg),
        _circ(bore * 0.5, 0.0, seg),
    ]
    verts = _flat(rings)
    faces = _ring_faces(0, seg, len(rings))
    acc.add(verts, faces, _basis(origin, zax, xhint))


# --------------------------------------------------------------------------- #
# fairing section
# --------------------------------------------------------------------------- #

def _naca(xc):
    xc = min(max(xc, 0.0), 1.0)
    return (0.2969 * math.sqrt(xc) - 0.1260 * xc - 0.3516 * xc * xc
            + 0.2843 * xc ** 3 - 0.1015 * xc ** 4)


_NMAX = _naca(0.30)


def _tear(chord, ht, nose=0.0290, cut=0.99, n_surf=30, te_pts=5,
          groove=None, gd=0.0009):
    """Closed teardrop: a aft along the chord, b across. Index 0 is the LE.

    `groove` inserts a real parting-line notch at that chord fraction on both
    surfaces - four extra points with ~70 deg walls, so auto-smooth keeps the
    edge crisp instead of blurring a shallow dent away.

    Returns (points, seam, te_index). seam is (upper0, upper1, lower0, lower1)
    - the four groove-floor indices - and te_index is the middle of the
    trailing-edge closure. Those five indices are where the moulding is parted
    into laminate strips.
    """
    def yy(xc):
        return ht * _naca(xc) / _NMAX

    # The leading edge sits a fixed distance ahead of the tube axis whatever the
    # chord: that is what keeps a short-chord section from swallowing the tube.
    x0 = min(max(nose / chord, 0.16), 0.49)

    base = [cut * 0.5 * (1.0 - math.cos(math.pi * i / n_surf))
            for i in range(n_surf + 1)]
    xs, dep = [], []
    for i, xc in enumerate(base):
        if groove is not None and i > 0 and base[i - 1] < groove <= xc:
            # The notch is inserted at the first base point PAST the groove, so
            # the cosine-spaced point just before it can easily sit inside the
            # notch's own span - the loop then ran forwards, back, forwards, and
            # crossed itself at every single station (that is where all of this
            # part's self-intersecting fairing faces came from). Swallow any
            # base point the notch covers and keep the chordwise run monotone.
            lo = groove - 0.0060
            while xs and xs[-1] >= lo - 1e-9:
                xs.pop()
                dep.pop()
            for dx, dd in ((-0.0060, 0.0), (-0.0038, 1.0),
                           (0.0038, 1.0), (0.0060, 0.0)):
                xs.append(groove + dx)
                dep.append(dd)
        if xs and xc <= xs[-1] + 1e-9:
            continue
        xs.append(xc)
        dep.append(0.0)

    pts = [(chord * (xc - x0), yy(xc) - dep[i] * gd) for i, xc in enumerate(xs)]
    nu = len(xs)
    a_te, y_te = pts[-1]
    for j in range(1, te_pts + 1):
        th = math.pi * j / (te_pts + 1)
        pts.append((a_te + y_te * 0.62 * math.sin(th), y_te * math.cos(th)))
    for i in range(len(xs) - 2, 0, -1):
        pts.append((chord * (xs[i] - x0), -(yy(xs[i]) - dep[i] * gd)))

    seam = None
    if groove is not None:
        deep = [i for i, d in enumerate(dep) if d > 0.5]
        if len(deep) == 2:
            lo0 = nu + te_pts + (nu - 2 - deep[1])
            lo1 = nu + te_pts + (nu - 2 - deep[0])
            seam = (deep[0], deep[1], lo0, lo1)
    return pts, seam, nu + (te_pts - 1) // 2


def _enclose(sec, core_r, extra, k=0.0025):
    """Push the loop out until it clears `core_r(dir) + extra` everywhere.

    R2-D2/D4: the section table alone decided whether the moulding was big
    enough for the tube inside it, and over both rear legs and the bottom of
    the pillar blade it was not - the skin ran INSIDE the tube by up to
    0.74 mm (3.95 mm on the pillar). This is the guarantee: whatever the table
    says, the outer skin cannot come closer to the axis than the thing it
    clads plus gap plus laminate. Smooth max, so where the table is already
    generous (everywhere it should be) the aerofoil is untouched.
    """
    out = []
    for (a, b) in sec:
        r = math.hypot(a, b)
        if r < 1e-9:
            out.append((core_r(1.0, 0.0) + extra, 0.0))
            continue
        rm = core_r(a / r, b / r) + extra
        rr = 0.5 * (r + rm + math.sqrt((r - rm) ** 2 + k * k)) - 0.5 * k
        out.append((a * rr / r, b * rr / r))
    return out


def _sup_r(ca, cb, rx, ry, nx):
    """Radius of |x/rx|^nx + |y/ry|^nx = 1 along the unit direction (ca, cb)."""
    t = (abs(ca) / rx) ** nx + (abs(cb) / ry) ** nx
    return t ** (-1.0 / nx)


def _inner(sec, wall, core_r, gap):
    """Inner skin of the moulding.

    Two things a plain inward offset gets wrong. (1) It crosses itself wherever
    the section is thinner than 2 x wall - everything aft of ~95 % chord - which
    leaves inverted faces inside the laminate and degenerate walls at the TE, so
    the wall thins into a real closeout instead. (2) A radial clamp on its own
    (the R1 behaviour) lets the clamped inner skin end up OUTSIDE the outer skin
    when the section is too small, which is precisely how the black seal came to
    poke through the carbon as a crescent; the outer loop is now guaranteed
    bigger by _enclose, and the clamp here only ever keeps the bore off the tube.
    """
    n = len(sec)
    out = []
    for i in range(n):
        p = Vector((sec[i][0], sec[i][1], 0.0))
        a = Vector((sec[(i - 1) % n][0], sec[(i - 1) % n][1], 0.0))
        b = Vector((sec[(i + 1) % n][0], sec[(i + 1) % n][1], 0.0))
        e0 = (p - a)
        e1 = (b - p)
        nn = Vector((e0.y, -e0.x, 0.0)).normalized() + Vector((e1.y, -e1.x, 0.0)).normalized()
        if nn.length < 1e-9:
            nn = Vector((e1.y, -e1.x, 0.0))
        nn.normalize()
        if nn.dot(p) < 0.0:
            nn = -nn
        w = wall
        if p.x > 0.0:                       # aft of the axis: watch the closeout
            w = min(wall, max(0.0006, abs(p.y) - 0.0005))
        q = p - nn * w
        if abs(p.y) > 0.0006 and q.y * p.y < 0.0:
            q.y = math.copysign(0.0002, p.y)
        r = math.hypot(q.x, q.y)
        rmin = core_r(q.x / r, q.y / r) + gap if r > 1e-9 else core_r(1.0, 0.0) + gap
        if r < rmin:
            q = q.normalized() * rmin if r > 1e-9 else Vector((rmin, 0.0, 0.0))
        out.append((q.x, q.y))
    return out


def _collar(sec, r):
    out = []
    for a, b in sec:
        v = Vector((a, b, 0.0))
        if v.length < 1e-9:
            v = Vector((1.0, 0.0, 0.0))
        v = v.normalized() * r
        out.append((v.x, v.y))
    return out


def _chord_axes(t):
    """Section axes: ex downstream along the chord, ey across."""
    dn = Vector((-1.0, 0.0, 0.0))
    a = dn - t * dn.dot(t)
    wa = a.length
    up = Vector((0.0, 0.0, 1.0))
    u = up - t * up.dot(t)
    if u.length < 1e-7:
        u = Vector((0.0, 0.0, 1.0))
    u.normalize()
    w = min(1.0, wa) ** 2
    ex = (a.normalized() * w + u * (1.0 - w)) if wa > 1e-7 else u
    ex = ex - t * ex.dot(t)
    if ex.length < 1e-8:
        ex = u
    ex.normalize()
    return ex, t.cross(ex).normalized()


# (arc from the apex, chord, half-thickness).
#
# R2-D2: the old table ran the chord down to 61.8 mm over the rear legs. A
# 45 mm tube whose axis sits at nose/chord = 47 % of a 62 mm chord cannot fit
# inside that section - the skin passed inside the tube at 47 of 66 leg
# stations. The minimum chord for a 45 mm tube 29 mm behind the leading edge,
# with 1.2 mm of seal gap and a 2.6 mm laminate, is about 82 mm; the table
# keeps 1.5-2.5 mm of margin on that everywhere, and _enclose enforces it.
_CH = [(0.00, 0.0900, 0.0290), (0.22, 0.0890, 0.0289), (0.42, 0.0870, 0.0287),
       (0.60, 0.0855, 0.0285), (0.80, 0.0845, 0.0284), (0.95, 0.0842, 0.0284),
       (1.10, 0.0850, 0.0285)]


def _fair_sec(s):
    s = abs(s)
    if s <= _CH[0][0]:
        return _CH[0][1], _CH[0][2]
    for i in range(len(_CH) - 1):
        a, b = _CH[i], _CH[i + 1]
        if a[0] <= s <= b[0]:
            t = C.smoothstep((s - a[0]) / (b[0] - a[0]))
            return C.lerp(a[1], b[1], t), C.lerp(a[2], b[2], t)
    return _CH[-1][1], _CH[-1][2]


def _tube_r(s):
    # R2-D3: the tail used to swell to 25.2 mm over its last 100 mm. That was
    # invisible while the socket was a hole in a plate, but the pedestal now
    # carries a real 46 mm bore and an upset end would burst straight through
    # its wall. The section is constant; the ferrule does the swaging.
    return TUBE_R


# --------------------------------------------------------------------------- #
# hoop geometry
# --------------------------------------------------------------------------- #

def _hoop_path():
    ctrl = [Vector((x, -y, z)) for (x, y, z) in reversed(HOOP_HALF[1:])]
    ctrl += [Vector((x, y, z)) for (x, y, z) in HOOP_HALF]
    dense = [Vector(p) for p in C.catmull_rom([tuple(v) for v in ctrl], 1600)]
    pts, total = _resample(dense, PATH_N)
    tg, nr, bn = _frames(pts)
    half = total * 0.5
    arc = [total * i / (PATH_N - 1) - half for i in range(PATH_N)]   # signed, 0 = apex
    return pts, tg, nr, bn, arc, total


def _hoop_tube(coll, pts, tg, nr, bn, arc, seg=64):
    rings = []
    for i, p in enumerate(pts):
        r = _tube_r(arc[i])
        rings.append([p + nr[i] * (math.cos(TAU * k / seg) * r)
                      + bn[i] * (math.sin(TAU * k / seg) * r) for k in range(seg)])
    verts = _flat(rings)
    faces = _ring_faces(0, seg, len(rings))
    faces.append(tuple(range(seg))[::-1])
    s = (len(rings) - 1) * seg
    faces.append(tuple(range(s, s + seg)))
    ob = _obj("HoopTube", verts, faces, coll, "Titanium", auto=52.0)
    C.add_bevel(ob, 0.0008, 2, angle=34.0)       # R2-D9: raw 90 deg end rims
    return ob, (verts, faces)


def _strips(n, seam, te_i):
    """Section index ranges for the four laminate strips of a moulding.

    Parted at the leading edge, at the trailing-edge closure, and at the floor
    of each parting-line groove - i.e. at the four places a real moulding is
    already broken. Ranges are inclusive and share their end columns, so the
    outer skin is continuous across a joint: the only thing that changes is
    which frame the weave is projected from.
    """
    u0, u1, l0, l1 = seam
    return (("Nu", list(range(0, u1 + 1))),
            ("Au", list(range(u1, te_i + 1))),
            ("Al", list(range(te_i, l0 + 1))),
            ("Nl", list(range(l0, n)) + [0]))


def _strip_obj(name, rings_o, rings_i, cols, coll, mat, bevel=0.0005):
    """One closed laminate strip: outer skin, inner skin, two walls, two ends."""
    m, L = len(rings_o), len(cols)
    verts = [tuple(rings_o[j][k]) for j in range(m) for k in cols]
    verts += [tuple(rings_i[j][k]) for j in range(m) for k in cols]
    bi = m * L
    faces = []
    for j in range(m - 1):
        for c in range(L - 1):
            a = j * L + c
            faces.append((a, a + 1, a + L + 1, a + L))
            b = bi + a
            faces.append((b + L, b + L + 1, b + 1, b))
    for j in range(m - 1):                       # side walls at both edges
        a, b = j * L, bi + j * L
        faces.append((a, a + L, b + L, b))
        a, b = j * L + L - 1, bi + j * L + L - 1
        faces.append((a + L, a, b, b + L))
    for c in range(L - 1):                       # moulded ends
        faces.append((c, bi + c, bi + c + 1, c + 1))
        a = (m - 1) * L + c
        faces.append((a + 1, bi + a + 1, bi + a, a))
    ob = _obj(name, verts, faces, coll, mat, auto=50.0)
    if bevel:
        C.add_bevel(ob, bevel, 2, angle=42.0)
    _align_weave(ob, _weave_axis(_skin_normals(rings_o, cols)))
    return ob, verts, faces


def _skin_normals(rings, cols):
    """(area, normal) for the OUTER skin quads only - the visible surface.

    Taking them over the whole closed strip would cancel to nothing; the weave
    frame has to follow the side you can see.
    """
    out = []
    for j in range(len(rings) - 1):
        for c in range(len(cols) - 1):
            a = rings[j][cols[c]]
            b = rings[j][cols[c + 1]]
            cc = rings[j + 1][cols[c + 1]]
            d = rings[j + 1][cols[c]]
            nv = (cc - a).cross(d - b)
            if nv.length > 1e-12:
                out.append((nv.length * 0.5, nv.normalized()))
    return out


def _fairing_piece(name, i0, i1, pts, tg, arc, coll, screws, seg_screw=0.115,
                   n_surf=30, halves=None):
    """One carbon moulding around the hoop, in four laminate strips.

    Outer skin + inner skin + a moulded collar at each extremity that closes
    down onto the bare tube, so no raw laminate edge is ever visible and the
    shell cannot float off the tube it clads.

    R2-D2: the ends used to blend to a 62 x 27 mm teardrop, whose minimum
    radius (21.8 mm) is INSIDE the 22.5 mm tube. That inverted the shell over
    12 of 73 section points - a razor-thin end with the seal ring showing
    through it as a black crescent, and a constant-radius cylindrical band down
    each rear leg where the clamped inner skin became the outermost surface.
    They now blend to a true collar: outer skin at tube + gap + wall, inner
    skin at tube + gap, so the end face is a real 2.6 mm annulus of laminate.
    """
    rings_o, rings_i = [], []
    seam_pts = []
    n_sec = seam = te_i = None
    for j in range(i0, i1 + 1):
        p, t = pts[j], tg[j]
        ex, ey = _chord_axes(t)
        s = arc[j]
        d_end = min(abs(arc[j] - arc[i0]), abs(arc[i1] - arc[j]))
        c0, h0 = _fair_sec(s)
        sec, seam, te_i = _tear(c0, h0, groove=SEAM_XC, n_surf=n_surf)
        rt = _tube_r(s)
        core = lambda ca, cb, _r=rt: _r
        sec = _enclose(sec, core, GAP + WALL)
        inn = _inner(sec, WALL, core, GAP)
        wcol = 1.0 - C.smoothstep(d_end / 0.026)
        if wcol > 0.0:
            co, ci = _collar(sec, rt + GAP + WALL), _collar(sec, rt + GAP)
            sec = [(C.lerp(a[0], b[0], wcol), C.lerp(a[1], b[1], wcol))
                   for a, b in zip(sec, co)]
            inn = [(C.lerp(a[0], b[0], wcol), C.lerp(a[1], b[1], wcol))
                   for a, b in zip(inn, ci)]
        if n_sec is None:
            n_sec = len(sec)
        rings_o.append([p + ex * a + ey * b for (a, b) in sec])
        rings_i.append([p + ex * a + ey * b for (a, b) in inn])
        if seam is not None and d_end > 0.045:
            nrm_u = (ex * (sec[seam[0]][0] + sec[seam[1]][0])
                     + ey * (sec[seam[0]][1] + sec[seam[1]][1])) * 0.5
            nrm_l = (ex * (sec[seam[2]][0] + sec[seam[3]][0])
                     + ey * (sec[seam[2]][1] + sec[seam[3]][1])) * 0.5
            seam_pts.append((s, p + nrm_u, nrm_u.normalized(),
                             p + nrm_l, nrm_l.normalized()))

    # The 1.15 m front moulding sweeps through more than 60 deg of section
    # rotation, which no single weave frame can follow (R2-D1: 25 % of the nose
    # quadrant still streaked with one frame per strip). It is parted on the car
    # centreline - under the halo camera, where a two-piece moulding would join
    # anyway - and each half is stripped separately. The halves share their
    # centre ring exactly, so the skin is continuous across the joint.
    m = len(rings_o)
    spans = ([("", 0, m - 1)] if halves is None else
             [(halves[0], 0, (m - 1) // 2), (halves[1], (m - 1) // 2, m - 1)])
    made, allv, allf = [], [], []
    for stag, j0, j1 in spans:
        so, si = rings_o[j0:j1 + 1], rings_i[j0:j1 + 1]
        for tag, cols in _strips(n_sec, seam, te_i):
            ob, v, f = _strip_obj(name + stag + tag, so, si, cols, coll,
                                  "CarbonFibre")
            made.append(ob)
            off = len(allv)
            allv += v
            allf += [tuple(i + off for i in fc) for fc in f]

    ends = ((pts[i0], tg[i0], 1.0, _tube_r(arc[i0])),
            (pts[i1], tg[i1], -1.0, _tube_r(arc[i1])))

    # flush fasteners down the parting line, both sides
    last = -1e9
    for (s, pu, nu, pl, nl) in seam_pts:
        if abs(s - last) < seg_screw:
            continue
        last = s
        # Seat them on the panel, not on the floor of the 0.9 mm groove they
        # straddle - otherwise the head is 0.1 mm BELOW the surrounding skin and
        # only a crescent of it shows.
        _flush_screw(screws, pu + nu * 0.0011, nu)
        _flush_screw(screws, pl + nl * 0.0011, nl)
    return made, (allv, allf), ends


def _seal(acc, p, tdir, into, rt, seg=40):
    ex = Vector((1.0, 0.0, 0.0))
    ex = (ex - tdir * ex.dot(tdir))
    if ex.length < 1e-6:
        ex = Vector((0.0, 0.0, 1.0)) - tdir * tdir.z
    ex.normalize()
    ey = tdir.cross(ex)
    c0 = p + tdir * (into * 0.0045)
    rows = []
    # R2-D2: the seal used to be fatter (rt + 1.9 mm) than the moulding's own
    # bore, so it showed through the carbon. It now lives inside the collar with
    # 0.2 mm to spare and only its lip is visible in the joint.
    for (r, off) in ((rt + 0.0002, -0.0050), (rt + 0.0010, -0.0040),
                     (rt + 0.0010, 0.0040), (rt + 0.0002, 0.0050)):
        c = c0 + tdir * off
        rows.append([c + ex * (r * math.cos(TAU * k / seg))
                     + ey * (r * math.sin(TAU * k / seg)) for k in range(seg)])
    acc.add(_flat(rows), _ring_faces(0, seg, 4, close=True))


def _crown_vane(coll, x0, y0, bvh, tag):
    """Turning vane moulded onto the crown of the nose fairing.

    D7: the first attempt built it in the section frame, but a third of the way
    round the hoop that frame's +b is already pointing outboard, so the vane
    grew sideways out of the flank as a sail. Vanes stand up in world Z with the
    chord in world X, and the root is dropped onto the moulding by ray cast.
    """
    up = Vector((0.0, 0.0, 1.0))

    def surf(dx):
        loc, _n, _i, _d = bvh.ray_cast(Vector((x0 + dx, y0, 0.980)), -up, 0.16)
        return loc.z if loc is not None else None

    z_mid = surf(0.0)
    if z_mid is None:
        return None
    sta = [(0.0000, 0.0250, -0.0270, 0.00225),
           (0.0060, 0.0224, -0.0250, 0.00205),
           (0.0112, 0.0174, -0.0214, 0.00170),
           (0.0152, 0.0104, -0.0164, 0.00125),
           (0.0176, 0.0024, -0.0090, 0.00065)]
    dense = C.catmull_rom(sta, 16)
    rows, n = [], None
    for (h, le, te, th) in dense:
        c = le - te
        nose = 0.32 * c
        sec, _sm, _ti = _tear(c, th, nose=nose, cut=0.982, n_surf=11, te_pts=3)
        n = len(sec)
        w = min(1.0, h / 0.0090)
        row = []
        for (a_s, b_s) in sec:
            dx = le - (nose + a_s)
            zs = surf(dx)
            if zs is None:
                zs = z_mid
            row.append((x0 + dx, y0 + b_s,
                        C.lerp(zs, z_mid, w) + h - 0.0016))
        rows.append(row)
    verts = _flat(rows)
    faces = _ring_faces(0, n, len(rows))
    faces.append(tuple(range(n))[::-1])
    _fan(verts, faces, (len(rows) - 1) * n, n)
    ob = _obj("CrownVane" + tag, verts, faces, coll, "CarbonMatte", auto=46.0)
    C.add_bevel(ob, 0.0004, 2, angle=40.0)       # R2-D9: razor trailing edge
    _align_weave(ob)                             # R2-D1: 87 % streaked
    return ob


def _sup_ring(cx, cy, z, rx, ry, n, seg):
    out = []
    e = 2.0 / n
    for k in range(seg):
        t = TAU * k / seg
        ct, st = math.cos(t), math.sin(t)
        out.append((cx + rx * math.copysign(abs(ct) ** e, ct),
                    cy + ry * math.copysign(abs(st) ** e, st), z))
    return out


def _bvh(verts, faces):
    return BVHTree.FromPolygons([tuple(v) for v in verts],
                                [list(f) for f in faces], all_triangles=False)


def _hit_up(bvh, x, y, z0, dz=0.30):
    loc, _n, _i, _d = bvh.ray_cast(Vector((x, y, z0)), Vector((0.0, 0.0, 1.0)), dz)
    return None if loc is None else loc.z


# --------------------------------------------------------------------------- #
# front pillar
# --------------------------------------------------------------------------- #

# z, half-width, half-thickness, superellipse exponent.
#
# R2-D6: the blade used to reach 21.2 mm half-thickness at z = 0.664, while the
# clevis it sits in is only 10.6 mm half-open - so the foot of the pillar was
# buried 1 cm inside both ears (99 tri pairs a side once the mirrored prism was
# fixed), which is what speckles the clevis inner face. The blade now stays
# inside the fork all the way to the top of the arch (z = 0.6638) and only
# flares to round above it.
PILLAR_STA = [
    (0.6060, 0.0250, 0.0090, 5.0),
    (0.6100, 0.0253, 0.0091, 5.0),
    (0.6400, 0.0251, 0.0093, 4.6),
    (0.6580, 0.0249, 0.0095, 4.0),
    (0.6660, 0.0248, 0.0098, 3.4),
    (0.6740, 0.0246, 0.0150, 2.6),
    (0.6820, 0.0245, 0.0212, 2.1),
    (0.7000, 0.0244, 0.0244, 2.0),
    (0.7600, 0.0233, 0.0233, 2.0),
    (0.8200, 0.0216, 0.0216, 2.0),
    (0.8480, 0.0208, 0.0208, 2.0),
]


def _pillar_x(z):
    t = min(max((z - PILLAR_FOOT_Z) / 0.254, 0.0), 1.0)
    return PILLAR_X - 0.015 * (t ** 1.35)


def _pillar_tube(coll, bvh_tube, seg=64):
    rows = []
    zs = [s[0] for s in PILLAR_STA]
    dense = C.catmull_rom([(s[0], s[1], s[2], s[3]) for s in PILLAR_STA], 34)
    for (z, rx, ry, n) in dense:
        rows.append(_sup_ring(_pillar_x(z), 0.0, z, rx, ry, n, seg))
    # top ring rides up onto the hoop tube so the joint is a weld, not a gap
    top = []
    for (x, y, z) in rows[-1]:
        h = _hit_up(bvh_tube, x, y, 0.800)
        top.append((x, y, (h + 0.0012) if h is not None else z + 0.012))
    rows.append(top)
    verts = _flat(rows)
    faces = _ring_faces(0, seg, len(rows))
    faces.append(tuple(range(seg))[::-1])
    _fan(verts, faces, (len(rows) - 1) * seg, seg)
    ob = _obj("PillarTube", verts, faces, coll, "Titanium", auto=48.0)
    C.add_bevel(ob, 0.0008, 2, angle=34.0)       # R2-D9
    return ob


PIL_FAIR = [(0.6780, 0.1240, 0.0300), (0.7200, 0.1200, 0.0298),
            (0.7700, 0.1130, 0.0292), (0.8150, 0.1010, 0.0282),
            (0.8460, 0.0920, 0.0272)]


_PIL_DENSE = None


def _pillar_core(z):
    """(rx, ry, exponent) of the pillar tube's own section at height z."""
    global _PIL_DENSE
    if _PIL_DENSE is None:
        _PIL_DENSE = C.catmull_rom([(s[0], s[1], s[2], s[3])
                                    for s in PILLAR_STA], 121)
    d = _PIL_DENSE
    if z <= d[0][0]:
        return d[0][1], d[0][2], d[0][3]
    if z >= d[-1][0]:
        return d[-1][1], d[-1][2], d[-1][3]
    for i in range(len(d) - 1):
        if d[i][0] <= z <= d[i + 1][0]:
            t = (z - d[i][0]) / max(d[i + 1][0] - d[i][0], 1e-9)
            return (C.lerp(d[i][1], d[i + 1][1], t),
                    C.lerp(d[i][2], d[i + 1][2], t),
                    C.lerp(d[i][3], d[i + 1][3], t))
    return d[-1][1], d[-1][2], d[-1][3]


def _pillar_fairing(coll, bvh_fair, screws, n_surf=26):
    """Deeper blade cladding the front pillar, in four laminate strips.

    R2-D4: the lower termination blended to a 62 x 26.4 mm teardrop whose
    minimum radius is 20.65 mm, against a pillar section 24.6 mm across - a
    3.95 mm breach, so the radially clamped inner skin became the outermost
    surface and the bottom 17 mm of the blade carried a lumpy cylindrical bulge
    instead of an aerofoil, with the tube itself through the skin. The blade is
    now clad against the pillar's REAL superellipse section (it is a 50 x 18 mm
    blade down at the clevis, not a 49 mm circle), and the bottom blends to a
    collar of that shape plus gap plus laminate.
    """
    dense = C.catmull_rom(PIL_FAIR, 30)
    ztop = dense[-1][0]
    top_sec, seam, te_i = _tear(dense[-1][1], dense[-1][2], nose=0.0335,
                                groove=SEAM_XC, n_surf=n_surf)
    n = len(top_sec)
    # per-column ceiling: where does this column meet the hoop moulding? Cast
    # from where the top ring actually ends up - a collar round the pillar tube,
    # not the full-chord section - or the rays for the nose and tail columns
    # miss the moulding entirely.
    rx, ry, nx = _pillar_core(ztop)
    top_ring = _core_offset(top_sec,
                            lambda ca, cb: _sup_r(ca, cb, rx, ry, nx),
                            GAP + WALL)
    ceil, hits = [], []
    for (a, b) in top_ring:
        h = _hit_up(bvh_fair, _pillar_x(ztop) - a, b, 0.800)
        ceil.append((h - 0.0016) if h is not None else None)
        if h is not None:
            hits.append(h - 0.0016)
    fb = min(hits) if hits else ztop + 0.006
    ceil = [fb if c is None else c for c in ceil]

    rings_o, rings_i = [], []
    seam_pts = []
    m = len(dense)
    for j, (z, c, h) in enumerate(dense):
        sec, seam, te_i = _tear(c, h, nose=0.0335, groove=SEAM_XC,
                                n_surf=n_surf)
        rx, ry, nx = _pillar_core(z)
        core = lambda ca, cb, _a=rx, _b=ry, _n=nx: _sup_r(ca, cb, _a, _b, _n)
        sec = _enclose(sec, core, GAP + WALL)
        inn = _inner(sec, WALL, core, GAP)
        # Collar both ends. The foot one is the visible moulded end; the top one
        # matters just as much, because the blade's top ring is cut off against
        # the underside of the hoop moulding by ray cast - if the blade is still
        # at full 92 mm chord there, its nose and tail hang outside the moulding
        # they are supposed to die into and the ray misses, leaving horns and a
        # notch at the apex (visible from below in /tmp/ha_a_V12_apexunder.png).
        # A 49 mm collar round the pillar tube tucks entirely inside it.
        wcol = 1.0 - C.smoothstep(min(j, m - 1 - j) / 3.4)
        if wcol > 0.0:
            co = _core_offset(sec, core, GAP + WALL)
            ci = _core_offset(sec, core, GAP)
            sec = [(C.lerp(p[0], q[0], wcol), C.lerp(p[1], q[1], wcol))
                   for p, q in zip(sec, co)]
            inn = [(C.lerp(p[0], q[0], wcol), C.lerp(p[1], q[1], wcol))
                   for p, q in zip(inn, ci)]
        t = j / (m - 1.0)
        ro, ri = [], []
        for k in range(n):
            zz = C.lerp(dense[0][0], ceil[k], t)
            ro.append(Vector((_pillar_x(z) - sec[k][0], sec[k][1], zz)))
            ri.append(Vector((_pillar_x(z) - inn[k][0], inn[k][1], zz)))
        rings_o.append(ro)
        rings_i.append(ri)
        if seam is not None and 0.02 < t < 0.98:
            for pair in ((seam[0], seam[1]), (seam[2], seam[3])):
                px = 0.5 * (ro[pair[0]][0] + ro[pair[1]][0])
                py = 0.5 * (ro[pair[0]][1] + ro[pair[1]][1])
                pz = 0.5 * (ro[pair[0]][2] + ro[pair[1]][2])
                seam_pts.append((z, Vector((px, py, pz)),
                                 Vector((0.0, 1.0 if py > 0 else -1.0, 0.0))))

    made = []
    for tag, cols in _strips(n, seam, te_i):
        ob, _v, _f = _strip_obj("PillarFairing" + tag, rings_o, rings_i, cols,
                                coll, "CarbonFibre")
        made.append(ob)

    last = {1: -9.0, -1: -9.0}
    for (z, p, nv) in seam_pts:
        side = 1 if nv.y > 0 else -1
        if abs(z - last[side]) < 0.055:
            continue
        last[side] = z
        _flush_screw(screws, p + nv * 0.0011, nv, xhint=(0, 0, 1))
    return made


def _core_offset(sec, core_r, extra):
    """The clad object's own outline plus `extra`, sampled in sec's directions.

    A moulded end that seals onto a 50 x 18 mm blade has to follow that blade,
    not a circle drawn round it - that was the other half of R2-D4.
    """
    out = []
    for (a, b) in sec:
        r = math.hypot(a, b)
        if r < 1e-9:
            out.append((core_r(1.0, 0.0) + extra, 0.0))
            continue
        rr = core_r(a / r, b / r) + extra
        out.append((a * rr / r, b * rr / r))
    return out


# --------------------------------------------------------------------------- #
# mounting feet
# --------------------------------------------------------------------------- #

def _prism(profile, y0, y1, chamf=0.0009):
    """Closed prism from a 2D (x, z) loop, extruded along y with broken edges.

    R2-D6: the chamfer rings were [y0, y0+c, y1-c, y1] regardless of direction,
    so on every mirrored (y1 < y0) prism the second ring stepped BACK past the
    cap and folded an inverted lip - FrontEarR came out 12.0 mm thick against
    10.6 mm on the left, and the lip bit into the pillar tube. Step along the
    extrusion, whichever way it runs.
    """
    n = len(profile)
    sg = 1.0 if y1 >= y0 else -1.0
    ys = [y0, y0 + sg * chamf, y1 - sg * chamf, y1]
    sc = [1.0 - chamf / 0.030, 1.0, 1.0, 1.0 - chamf / 0.030]
    cx = sum(p[0] for p in profile) / n
    cz = sum(p[1] for p in profile) / n
    rings = []
    for y, s in zip(ys, sc):
        rings.append([(cx + (p[0] - cx) * s, y, cz + (p[1] - cz) * s)
                      for p in profile])
    verts = _flat(rings)
    faces = _ring_faces(0, n, len(rings))
    faces.append(tuple(range(n))[::-1])
    b = (len(rings) - 1) * n
    faces.append(tuple(range(b, b + n)))
    return verts, faces


def _front_foot(coll, screws, ti):
    made = []
    xs = _span(0.8460, 0.9660, 15)
    ys = _span(-0.0575, 0.0575, 13)
    rp = [[Vector((x, y, _skin_z_of_y(x, y))) for y in ys] for x in xs]
    rn = [[_crown_n(x, y) for y in ys] for x in xs]
    v, f = _stepped_slab(rp, rn, 0.0102, 0.0058, 0.0060)
    pad = _obj("FrontPad", v, f, coll, "Titanium", auto=30.0)
    C.add_bevel(pad, 0.0011, 3, angle=30.0)
    made.append(pad)

    for bx in (0.8620, 0.9500):
        for by in (-0.0410, 0.0410):
            z = _skin_z_of_y(bx, by) + 0.0102
            nv = _crown_n(bx, by)
            _spotface(ti, (bx, by, z), nv, r=0.0110, h=0.0022)
            _cap_screw(screws, (bx, by, z + 0.0022), nv, xhint=(1, 0, 0),
                       d=0.0080, hd=0.0134, hh=0.0074, shank=0.024, washer=0.0014)

    # clevis ears
    prof = [(0.8740, 0.5940), (0.9360, 0.5940), (0.9360, 0.6340)]
    for i in range(1, 44):                       # R2-D8: 22 facets on a 31 mm
        a = math.pi * i / 44.0                   # arch read as a polygon rim
        prof.append((0.9050 + 0.0310 * math.cos(a), 0.6340 + 0.0298 * math.sin(a)))
    prof.append((0.8740, 0.6340))
    for side in (1, -1):
        v, f = _prism(prof, side * 0.0106, side * 0.0212)
        ear = _obj(f"FrontEar{'L' if side > 0 else 'R'}", v, f, coll, "Titanium",
                   auto=30.0)
        C.add_bevel(ear, 0.0013, 3, angle=30.0)
        made.append(ear)
        pk = []
        for i in range(64):                      # R2-D8: 28 read as a polygon
            a = TAU * i / 64.0
            pk.append((0.9050 + 0.0205 * math.cos(a), 0.6330 + 0.0178 * math.sin(a)))
        v, f = _prism(pk, side * 0.0212, side * 0.0226, chamf=0.0004)
        boss = _obj(f"FrontEarBoss{'L' if side > 0 else 'R'}", v, f, coll,
                    "Titanium", auto=30.0)
        C.add_bevel(boss, 0.0008, 2, angle=30.0)
        made.append(boss)

    # R2-D5: the joint is 0.0226 half-thickness of boss on each side. The screw
    # seats on TOP of its washer (the washer is drawn below the origin, so the
    # old origin buried it inside the boss), the nut seats on its own washer on
    # the far face instead of hanging 2.6 mm off in space, the shank is long
    # enough to run right through the nut, and the bore is 0.8 mm bigger than
    # the shank so the two cylinders cannot z-fight inside the nut.
    y_face, w_t = 0.0226, 0.0016
    _washer(screws, (0.9050, y_face + w_t, 0.6340), (0, 1, 0), ro=0.0176 * 0.62,
            rw=0.0104 * 0.55, t=w_t)
    _cap_screw(screws, (0.9050, y_face + w_t, 0.6340), (0, 1, 0), xhint=(1, 0, 0),
               d=0.0104, hd=0.0176, hh=0.0098, shank=0.0590, washer=0.0)
    _washer(screws, (0.9050, -(y_face + w_t), 0.6340), (0, -1, 0),
            ro=0.0176 * 0.62, rw=0.0104 * 0.55, t=w_t)
    _hex_nut(screws, (0.9050, -(y_face + w_t), 0.6340), (0, -1, 0),
             xhint=(1, 0, 0), af=0.0168, h=0.0082, bore=0.0112)
    return made


def _rear_foot(coll, screws, ti, side, tail_pts):
    made = []
    sg = 1.0 if side > 0 else -1.0
    tag = "L" if side > 0 else "R"
    xs = _span(-0.1450, -0.0180, 13)
    fr = _span(0.6930, 0.7790, 9)
    rp = [[_skin_pt(x, ff, sg) for ff in fr] for x in xs]
    rn = [[_skin_n(x, ff, sg) for ff in fr] for x in xs]
    v, f = _stepped_slab(rp, rn, 0.0094, 0.0052, 0.0055)
    pad = _obj(f"RearPad{tag}", v, f, coll, "Titanium", auto=30.0)
    C.add_bevel(pad, 0.0011, 3, angle=30.0)
    made.append(pad)

    for bx, bf in ((-0.1345, 0.7000), (-0.1345, 0.7720),
                   (-0.0255, 0.7000), (-0.0255, 0.7720)):
        p = _skin_pt(bx, bf, sg)
        nv = _skin_n(bx, bf, sg)
        _spotface(ti, p + nv * 0.0094, nv, r=0.0106, h=0.0020)
        _cap_screw(screws, p + nv * 0.0114, nv, xhint=(1, 0, 0),
                   d=0.0080, hd=0.0134, hh=0.0074, shank=0.024, washer=0.0014)

    # Pedestal: a machined block on the pad that sockets the tube tail.
    pc = _skin_pt(-0.0800, 0.7340, sg)
    pn = _skin_n(-0.0800, 0.7340, sg)
    ax = Vector((1.0, 0.0, 0.0))
    ax = (ax - pn * ax.dot(pn)).normalized()
    ay = pn.cross(ax)
    seg = 56
    b_c = pc + pn * 0.0092
    base = []
    for k in range(seg):
        t = TAU * k / seg
        ct, st = math.cos(t), math.sin(t)
        e = 2.0 / 4.4
        base.append(ax * (0.0432 * math.copysign(abs(ct) ** e, ct))
                    + ay * (0.0304 * math.copysign(abs(st) ** e, st)))

    # R2-D3a: the top ring was framed off tdir, which points DOWN the tail -
    # 165 deg from the pad normal pn - so ey = tdir x ex came out as -ay and the
    # loft ran the two rings in OPPOSITE rotational senses. Every intermediate
    # row therefore swept through the axis: that is the V-shaped sail across the
    # pedestal flank, not a lofting subtlety. Frame the top off tup (up out of
    # the socket) so both rings are indexed the same way round.
    a1 = Vector(tail_pts[-1])                      # buried end of the tube
    tup = (Vector(tail_pts[-2]) - a1).normalized()  # up along the tail
    ex = (ax - tup * ax.dot(tup)).normalized()
    ey = tup.cross(ex)
    # R2-D3c: the top plane used to land 3.24 mm BELOW the end of the tube, so
    # the bore opened onto fresh air. Put it 16 mm up the tail instead - the
    # tube now runs through the face and bottoms out inside the socket.
    t_c = a1 + tup * 0.0135
    r_bore = TUBE_R + 0.0005
    ring = [(math.cos(TAU * k / seg), math.sin(TAU * k / seg)) for k in range(seg)]
    top = [ex * (0.0304 * c) + ey * (0.0304 * s) for (c, s) in ring]

    rows = [[b_c + p for p in base]]
    for (fp, fs) in ((0.155, 0.000), (0.205, 0.075), (0.400, 0.320),
                     (0.600, 0.640), (0.760, 0.880), (0.865, 1.000),
                     (1.000, 1.000)):
        c = b_c.lerp(t_c, fp)
        rows.append([c + base[k].lerp(top[k], fs) for k in range(seg)])
    # R2-D3b: the bore used to be the mesh boundary - 56 open edges, a
    # zero-thickness rim with the inside of the block on show. Break the rim and
    # sink a real 20 mm socket with a floor under it.
    for (r, dz) in ((r_bore + 0.0011, 0.0000), (r_bore, -0.0013),
                    (r_bore, -0.0195), (r_bore - 0.0030, -0.0208)):
        c = t_c + tup * dz
        rows.append([c + ex * (r * cs) + ey * (r * sn) for (cs, sn) in ring])
    verts = _flat(rows)
    faces = _ring_faces(0, seg, len(rows))
    faces.append(tuple(range(seg))[::-1])
    _fan(verts, faces, (len(rows) - 1) * seg, seg, flip=True)   # socket floor
    ped = _obj(f"RearPedestal{tag}", verts, faces, coll, "Titanium", auto=36.0)
    C.add_bevel(ped, 0.0012, 3, angle=34.0)
    made.append(ped)

    # machined ferrule swaged onto the tube just above the socket
    sc = t_c + tup * 0.0215
    st_rows = []
    for (r, off) in ((TUBE_R + 0.0006, -0.0080), (0.0262, -0.0070),
                     (0.0272, -0.0046), (0.0272, 0.0046),
                     (0.0262, 0.0070), (TUBE_R + 0.0006, 0.0080)):
        c = sc + tup * off
        st_rows.append([c + ex * (r * math.cos(TAU * k / seg))
                        + ey * (r * math.sin(TAU * k / seg)) for k in range(seg)])
    verts = _flat(st_rows)
    faces = _ring_faces(0, seg, len(st_rows), close=True)
    fer = _obj(f"RearFerrule{tag}", verts, faces, coll, "Titanium", auto=40.0)
    C.add_bevel(fer, 0.0006, 2, angle=34.0)      # R2-D9: raw swage rims
    made.append(fer)
    return made


# --------------------------------------------------------------------------- #
# T-camera pod, aerial fin, halo camera and its loom
# --------------------------------------------------------------------------- #

POD_STA = [
    (-0.3180, 0.0300, 0.0525, 0.0345),
    (-0.3400, 0.0327, 0.0560, 0.0380),
    (-0.3750, 0.0341, 0.0572, 0.0392),
    (-0.4200, 0.0331, 0.0562, 0.0382),
    (-0.4700, 0.0296, 0.0522, 0.0350),
    (-0.5200, 0.0236, 0.0462, 0.0300),
    (-0.5600, 0.0156, 0.0384, 0.0242),
    (-0.5850, 0.0090, 0.0310, 0.0192),
]

_WALL_F = [0.09, 0.17, 0.23, 0.245, 0.265, 0.28, 0.40, 0.55, 0.70, 0.85]
_WALL_D = [0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0]
POD_NT = 21
POD_NB = 21


def _pod_w(x):
    xs = [st[0] for st in POD_STA]
    ws = [st[1] for st in POD_STA]
    if x >= xs[0]:
        return ws[0]
    if x <= xs[-1]:
        return ws[-1]
    for i in range(len(xs) - 1):
        if xs[i] >= x >= xs[i + 1]:
            return C.lerp(ws[i], ws[i + 1], (xs[i] - x) / (xs[i] - xs[i + 1]))
    return ws[-1]


def _pod_section(x, w, htop, hsh, keel=0.0045, notch=0.0011):
    zc = _skin_z_of_y(x, 0.0)
    top = []
    for i in range(POD_NT):
        y = w * math.cos(math.pi * i / (POD_NT - 1.0))
        top.append((x, y, zc + htop - (htop - hsh) * (abs(y) / max(w, 1e-6)) ** 2.0))
    bot = []
    for i in range(POD_NB):
        y = -w + 2.0 * w * i / (POD_NB - 1.0)
        bot.append((x, y, _skin_z_of_y(x, y) + keel))
    out = list(top)
    # left wall (y = -w) top -> bottom, then bottom row, then right wall up
    def wall(y, ztop, zbot):
        col = []
        for f, d in zip(_WALL_F, _WALL_D):
            col.append((x, y - math.copysign(d * notch, y), C.lerp(ztop, zbot, f)))
        return col
    out += wall(-w, top[-1][2], bot[0][2])
    out += bot
    out += list(reversed(wall(w, top[0][2], bot[-1][2])))
    return out


def _pod(coll, screws):
    made = []
    dense = C.catmull_rom(POD_STA, 46)
    secs = [_pod_section(*st) for st in dense]
    n = len(secs[0])

    def shrink(sec, x, f):
        cy = 0.0
        cz = sum(p[2] for p in sec) / len(sec)
        return [(x, C.lerp(p[1], cy, f), C.lerp(p[2], cz, f)) for p in sec]

    rows = []
    for dx, f in ((0.0104, 0.56), (0.0096, 0.36), (0.0074, 0.19),
                  (0.0040, 0.065)):
        rows.append(shrink(secs[0], dense[0][0] + dx, f))
    rows += secs
    for dx, f in ((0.0038, 0.10), (0.0068, 0.30), (0.0086, 0.58), (0.0094, 0.82)):
        rows.append(shrink(secs[-1], dense[-1][0] - dx, f))

    verts = _flat(rows)
    faces = _ring_faces(0, n, len(rows))
    _fan(verts, faces, 0, n, flip=True)
    _fan(verts, faces, (len(rows) - 1) * n, n)
    bvh_pod = _bvh(verts, faces)
    pod = _obj("PodShell", verts, faces, coll, "CarbonFibre", auto=44.0)
    C.add_bevel(pod, 0.0032, 3, angle=26.0)
    _align_weave(pod)
    made.append(pod)

    # saddle plate under it, conforming to the airbox ridge
    xs = _span(-0.3060, -0.5960, 15)
    rp, rn = [], []
    for x in xs:
        end = min(C.smoothstep((x - xs[-1]) / 0.030),
                  C.smoothstep((xs[0] - x) / 0.026))
        w = _pod_w(x) * C.lerp(0.34, 1.0, end) + 0.0072 * C.lerp(0.45, 1.0, end)
        ys = _span(-w, w, 9)
        rp.append([Vector((x, y, _skin_z_of_y(x, y))) for y in ys])
        rn.append([_crown_n(x, y) for y in ys])
    v, f = _stepped_slab(rp, rn, 0.0052, 0.0030, 0.0060)
    plate = _obj("PodSaddle", v, f, coll, "CarbonMatte", auto=30.0)
    C.add_bevel(plate, 0.0012, 3, angle=30.0)
    made.append(plate)

    # flush screws down the pod parting line
    i_notch = POD_NT + 3
    for j in range(4, len(secs) - 6, 8):
        for k in (i_notch, n - 1 - 3):
            p = secs[j][k]
            nv = Vector((0.0, 1.0 if p[1] > 0 else -1.0, -0.25)).normalized()
            _flush_screw(screws, Vector(p) + nv * 0.0004, nv, xhint=(1, 0, 0),
                         hd=0.0080)
    # saddle plate screws
    for sx in (-0.3320, -0.4300, -0.5220):
        for sy in (-(_pod_w(sx) + 0.0034), _pod_w(sx) + 0.0034):
            p = Vector((sx, sy, _skin_z_of_y(sx, sy) + 0.0050))
            _flush_screw(screws, p, _crown_n(sx, sy), xhint=(1, 0, 0), hd=0.0086)

    # service hatch on each flank - the flank is a 250 mm run of otherwise
    # unbroken laminate, which is exactly the "flat face bigger than 15 mm" the
    # brief calls a defect
    for sgn, tg2 in ((1.0, "L"), (-1.0, "R")):
        hp = _pod_hatch(coll, bvh_pod, sgn, tg2, screws)
        if hp is not None:
            made.append(hp)

    # camera barrel out of the pod nose
    xn = dense[0][0] + 0.0100
    zc = _skin_z_of_y(xn, 0.0) + 0.0310
    ax = Vector((0.9986, 0.0, -0.0523))
    seg = 44
    prof = [(0.0000, -0.0140), (0.0166, -0.0140), (0.0166, 0.0075),
            (0.0158, 0.0098), (0.0140, 0.0112), (0.0129, 0.0112),
            (0.0129, 0.0022), (0.0104, 0.0000), (0.0040, -0.0022)]
    rows = [[(r * math.cos(TAU * k / seg), r * math.sin(TAU * k / seg), z)
             for k in range(seg)] for (r, z) in prof]
    v = _flat(rows)
    f = _ring_faces(0, seg, len(rows))
    f.append(tuple(range(seg))[::-1])
    b = (len(rows) - 1) * seg
    f.append(tuple(range(b, b + seg)))
    m = _basis((xn - 0.0020, 0.0, zc), ax, (0, 0, 1))
    barrel = _obj("PodCamBarrel", [tuple(m @ Vector(p)) for p in v], f, coll,
                  "Titanium", auto=36.0)
    C.add_bevel(barrel, 0.0005, 2, angle=34.0)   # R2-D9
    made.append(barrel)

    lens = []
    for i in range(7):
        t = i / 6.0
        r = 0.0126 * math.cos(t * math.radians(62.0))
        z = 0.0038 + 0.0026 * math.sin(t * math.radians(62.0))
        lens.append([(r * math.cos(TAU * k / seg), r * math.sin(TAU * k / seg), z)
                     for k in range(seg)])
    v = _flat(lens)
    f = _ring_faces(0, seg, len(lens))
    f.append(tuple(range(seg))[::-1])
    b = (len(lens) - 1) * seg
    f.append(tuple(range(b, b + seg)))
    gl = _obj("PodCamLens", [tuple(m @ Vector(p)) for p in v], f, coll,
              "DisplayGlass", auto=60.0)
    made.append(gl)

    # sun hood over the lens
    hood = [math.radians(C.lerp(-74.0, 74.0, i / 12.0)) for i in range(13)]
    nh = len(hood)
    rows = []
    for (r, z) in ((0.0164, 0.0050), (0.0192, 0.0074), (0.0192, 0.0168),
                   (0.0166, 0.0158)):
        rows.append([(r * math.cos(a), r * math.sin(a), z) for a in hood])
    v = _flat(rows)
    f = _ring_faces(0, nh, 4, wrap=False)
    f += [(3 * nh + k, 3 * nh + k + 1, k + 1, k) for k in range(nh - 1)]
    f.append((0, nh, 2 * nh, 3 * nh))
    f.append((3 * nh + nh - 1, 2 * nh + nh - 1, nh + nh - 1, nh - 1))
    hd = _obj("PodCamHood", [tuple(m @ Vector(p)) for p in v], f, coll,
              "MatteBlack", auto=40.0)
    C.add_bevel(hd, 0.0004, 2, angle=34.0)       # R2-D9
    made.append(hd)
    return made


def _pod_hatch(coll, bvh, sgn, tag, screws, seg=44):
    """Raised service cover moulded onto the pod flank."""
    xc, zc = -0.4020, _skin_z_of_y(-0.4020, 0.0) + 0.0140
    ra, rb = 0.0380, 0.0158
    ydir = Vector((0.0, -sgn, 0.0))

    def land(u, sc):
        t = TAU * u
        e = 2.0 / 3.2
        x = xc + ra * sc * math.copysign(abs(math.cos(t)) ** e, math.cos(t))
        z = zc + rb * sc * math.copysign(abs(math.sin(t)) ** e, math.sin(t))
        loc, _nrm, _i, _d = bvh.ray_cast(Vector((x, sgn * 0.20, z)), ydir, 0.30)
        return loc, Vector((0.0, sgn, 0.0))

    # R2-D9/R2 open shells: the land ring used to be the mesh boundary (44 open
    # edges a side). Sink a second copy of it 1 mm INTO the pod flank and fan it
    # shut, so the cover is a closed solid whose closing face is buried.
    rows = []
    for (sc, h) in ((1.000, -0.0010), (1.000, 0.0000), (0.982, 0.0040),
                    (0.880, 0.0047), (0.620, 0.0049)):
        row = []
        for k in range(seg):
            loc, nrm = land(k / seg, sc)
            if loc is None:
                return None
            row.append(tuple(loc + nrm * h))
        rows.append(row)
    verts = _flat(rows)
    faces = _ring_faces(0, seg, len(rows))
    _fan(verts, faces, 0, seg, flip=True)
    _fan(verts, faces, (len(rows) - 1) * seg, seg)
    ob = _obj("PodHatch" + tag, verts, faces, coll, "CarbonFibre", auto=40.0)
    C.add_bevel(ob, 0.0006, 2, angle=34.0)
    dome = [[Vector(p) for p in r] for r in rows[1:]]
    _align_weave(ob, _weave_axis(_skin_normals(dome, list(range(seg)) + [0])))
    for u in (0.08, 0.42, 0.58, 0.92):
        loc, nrm = land(u, 0.80)
        if loc is not None:
            _flush_screw(screws, loc + nrm * 0.0049, nrm, xhint=(1, 0, 0),
                         hd=0.0068)
    return ob


def _fin(coll, screws, ti):
    """GPS / telemetry blade aft of the pod."""
    made = []
    xs = _span(-0.6120, -0.7060, 9)
    ys = _span(-0.0148, 0.0148, 5)
    rp = [[Vector((x, y, _skin_z_of_y(x, y))) for y in ys] for x in xs]
    rn = [[_crown_n(x, y) for y in ys] for x in xs]
    v, f = _stepped_slab(rp, rn, 0.0052, 0.0028, 0.0050)
    base = _obj("FinBase", v, f, coll, "Titanium", auto=30.0)
    C.add_bevel(base, 0.0009, 3, angle=30.0)
    made.append(base)

    sta = [(0.0000, -0.6205, -0.6985, 0.0060),
           (0.0130, -0.6262, -0.6980, 0.0057),
           (0.0270, -0.6372, -0.6966, 0.0051),
           (0.0390, -0.6508, -0.6942, 0.0044),
           (0.0480, -0.6648, -0.6906, 0.0034),
           (0.0532, -0.6762, -0.6868, 0.0021)]
    dense = C.catmull_rom(sta, 24)
    rows, n = [], None
    for (h, le, te, t) in dense:
        c = le - te
        sec, _sm, _ti = _tear(c, t, nose=0.30 * c, cut=0.985, n_surf=18, te_pts=4)
        n = len(sec)
        xa = le - 0.30 * c
        row = []
        for (a, b) in sec:
            x = xa - a
            zc = _skin_z_of_y(x, 0.0) + 0.0046 + h
            zk = _skin_z_of_y(x, b) + 0.0046
            row.append((x, b, C.lerp(zk, zc, min(1.0, h / 0.0090))))
        rows.append(row)
    tip = rows[-1]
    cx = sum(p[0] for p in tip) / n
    cz = sum(p[2] for p in tip) / n
    for (fs, dz) in ((0.42, 0.0016), (0.78, 0.0026)):
        rows.append([(C.lerp(p[0], cx, fs), p[1] * (1.0 - fs),
                      C.lerp(p[2], cz, fs * 0.5) + dz) for p in tip])
    verts = _flat(rows)
    faces = _ring_faces(0, n, len(rows))
    _fan(verts, faces, 0, n, flip=True)
    _fan(verts, faces, (len(rows) - 1) * n, n)
    blade = _obj("FinBlade", verts, faces, coll, "MatteBlack", auto=52.0)
    C.add_bevel(blade, 0.0004, 2, angle=40.0)    # R2-D9
    made.append(blade)

    for sx in (-0.6250, -0.6930):
        p = Vector((sx, 0.0, _skin_z_of_y(sx, 0.0) + 0.0052))
        nv = _crown_n(sx, 0.0)
        _spotface(ti, p, nv, r=0.0062, h=0.0012)
        _flush_screw(screws, p + nv * 0.0012, nv, xhint=(1, 0, 0), hd=0.0072)
    return made


def _hit(bvh, origin, dirv, dist=0.60):
    loc, _n, _i, _d = bvh.ray_cast(Vector(origin), Vector(dirv).normalized(), dist)
    return loc


def _halo_cam(coll, screws, bvh_fair):
    """Forward-facing camera on the crown of the front moulding, plus its loom."""
    made = []
    xs = [0.9160, 0.9080, 0.8960, 0.8820, 0.8680, 0.8560, 0.8470, 0.8420]
    tops = [0.9060, 0.9098, 0.9112, 0.9108, 0.9086, 0.9050, 0.9010, 0.8975]
    hw = [0.0092, 0.0130, 0.0160, 0.0172, 0.0170, 0.0158, 0.0136, 0.0106]
    rows = []
    seg = 26
    for x, zt, w in zip(xs, tops, hw):
        h = _hit(bvh_fair, (x, 0.0, 0.960), (0, 0, -1), 0.14)
        zb = (h.z - 0.0020) if h is not None else 0.8860
        row = []
        for k in range(seg):
            t = TAU * k / seg
            e = 2.0 / 3.4
            y = w * math.copysign(abs(math.cos(t)) ** e, math.cos(t))
            zc = 0.5 * (zt + zb)
            zh = 0.5 * (zt - zb)
            z = zc + zh * math.copysign(abs(math.sin(t)) ** e, math.sin(t))
            row.append((x, y, z))
        rows.append(row)
    verts = _flat(rows)
    faces = _ring_faces(0, seg, len(rows))
    faces.append(tuple(range(seg))[::-1])
    b = (len(rows) - 1) * seg
    faces.append(tuple(range(b, b + seg)))
    body = _obj("HaloCamBody", verts, faces, coll, "MatteBlack", auto=40.0)
    C.add_bevel(body, 0.0014, 3, angle=26.0)
    made.append(body)

    seg2 = 36
    m = _basis((0.9145, 0.0, 0.8992), (0.9945, 0.0, 0.1045), (0, 0, 1))
    prof = [(0.0000, -0.0060), (0.0088, -0.0060), (0.0088, 0.0034),
            (0.0080, 0.0046), (0.0064, 0.0046), (0.0064, 0.0006),
            (0.0030, -0.0010)]
    rows = [[(r * math.cos(TAU * k / seg2), r * math.sin(TAU * k / seg2), z)
             for k in range(seg2)] for (r, z) in prof]
    v = _flat(rows)
    f = _ring_faces(0, seg2, len(rows))
    f.append(tuple(range(seg2))[::-1])
    b = (len(rows) - 1) * seg2
    f.append(tuple(range(b, b + seg2)))
    hb = _obj("HaloCamBarrel", [tuple(m @ Vector(p)) for p in v], f, coll,
              "Titanium", auto=36.0)
    C.add_bevel(hb, 0.0004, 2, angle=34.0)       # R2-D9
    made.append(hb)
    lens = []
    for i in range(6):
        t = i / 5.0
        r = 0.0062 * math.cos(t * math.radians(60.0))
        z = 0.0018 + 0.0014 * math.sin(t * math.radians(60.0))
        lens.append([(r * math.cos(TAU * k / seg2), r * math.sin(TAU * k / seg2), z)
                     for k in range(seg2)])
    v = _flat(lens)
    f = _ring_faces(0, seg2, len(lens))
    f.append(tuple(range(seg2))[::-1])
    b = (len(lens) - 1) * seg2
    f.append(tuple(range(b, b + seg2)))
    made.append(_obj("HaloCamLens", [tuple(m @ Vector(p)) for p in v], f, coll,
                     "DisplayGlass", auto=60.0))

    for sx in (0.9020, 0.8560):
        h = _hit(bvh_fair, (sx, 0.0, 0.960), (0, 0, -1), 0.14)
        if h is None:
            continue
        _flush_screw(screws, Vector((sx, 0.0130, h.z + 0.0060)),
                     Vector((0.0, 0.42, 1.0)), xhint=(1, 0, 0), hd=0.0072)
        _flush_screw(screws, Vector((sx, -0.0130, h.z + 0.0060)),
                     Vector((0.0, -0.42, 1.0)), xhint=(1, 0, 0), hd=0.0072)
    return made


def _loom(coll, bvh_all):
    """Camera loom down the back of the pillar moulding into a grommet."""
    made = []
    zs = [0.8940, 0.8840, 0.8700, 0.8560, 0.8400, 0.8200, 0.8000, 0.7800,
          0.7620, 0.7480, 0.7390]
    pts = []
    for z in zs:
        h = _hit(bvh_all, (0.700, 0.0135, z), (1, 0, 0), 0.30)
        x = (h.x - 0.0056) if h is not None else 0.8300
        pts.append(Vector((x, 0.0135, z)))
    pts[0] = Vector((0.8480, 0.0135, 0.8960))
    dense = [Vector(p) for p in C.catmull_rom([tuple(p) for p in pts], 60)]
    v, f = _sweep_circle(dense, lambda i: 0.0036, seg=18)
    made.append(_obj("Loom", v, f, coll, "MatteBlack", auto=40.0))

    # grommet where it enters the moulding
    p0 = dense[-1]
    d = (dense[-1] - dense[-5]).normalized()
    seg = 28
    # R2 open shells: the profile used to stop at the far rim, leaving 56 open
    # edges; closing the loop back to the mouth gives it a real 3.9 mm bore
    # (0.3 mm clear of the loom, so the two cylinders cannot z-fight).
    prof = [(0.0039, 0.0), (0.0088, -0.0060), (0.0104, -0.0120),
            (0.0104, -0.0150), (0.0039, -0.0150)]
    rows = []
    for (r, off) in prof:
        c = p0 + d * (-off)
        ex = Vector((0.0, 1.0, 0.0))
        ex = (ex - d * ex.dot(d)).normalized()
        ey = d.cross(ex)
        rows.append([c + ex * (r * math.cos(TAU * k / seg))
                     + ey * (r * math.sin(TAU * k / seg)) for k in range(seg)])
    v = _flat(rows)
    f = _ring_faces(0, seg, len(rows), close=True)
    gr = _obj("LoomGrommet", v, f, coll, "MatteBlack", auto=40.0)
    C.add_bevel(gr, 0.0004, 2, angle=34.0)
    made.append(gr)

    # P-clip halfway down
    pc = dense[26]
    d2 = (dense[28] - dense[24]).normalized()
    ex = Vector((0.0, 1.0, 0.0))
    ex = (ex - d2 * ex.dot(d2)).normalized()
    ey = d2.cross(ex)
    rows = []
    for (r, off) in ((0.0040, -0.0035), (0.0058, -0.0035),
                     (0.0058, 0.0035), (0.0040, 0.0035)):
        c = pc + d2 * off
        rows.append([c + ex * (r * math.cos(TAU * k / seg))
                     + ey * (r * math.sin(TAU * k / seg)) for k in range(seg)])
    v = _flat(rows)
    f = _ring_faces(0, seg, 4, close=True)
    lc = _obj("LoomClip", v, f, coll, "Titanium", auto=40.0)
    C.add_bevel(lc, 0.0004, 2, angle=34.0)       # R2-D9
    made.append(lc)
    return made


# --------------------------------------------------------------------------- #
# entry point
# --------------------------------------------------------------------------- #

def build(coll, ctx=None):
    made = []
    screws = Acc()
    ti = Acc()

    pts, tg, nr, bn, arc, total = _hoop_path()
    tube, tube_mesh = _hoop_tube(coll, pts, tg, nr, bn, arc)
    made.append(tube)

    def idx_of(s):
        lo, hi = 0, PATH_N - 1
        best, bi = 1e9, 0
        for i in range(PATH_N):
            d = abs(arc[i] - s)
            if d < best:
                best, bi = d, i
        return bi

    fr0, fr1 = idx_of(-FAIR_FRONT_S), idx_of(FAIR_FRONT_S)
    front, front_mesh, ends = _fairing_piece("FairingFront", fr0, fr1, pts, tg,
                                             arc, coll, screws, halves=("R", "L"))
    made += front
    all_ends = list(ends)
    for tag, s0, s1 in (("L", FAIR_REAR_S0, FAIR_REAR_S1),
                        ("R", -FAIR_REAR_S1, -FAIR_REAR_S0)):
        obs, _m, e2 = _fairing_piece("FairingRear" + tag, idx_of(s0), idx_of(s1),
                                     pts, tg, arc, coll, screws, seg_screw=0.135)
        made += obs
        all_ends += list(e2)

    bvh_tube = _bvh(*tube_mesh)
    bvh_front = _bvh(*front_mesh)
    made.append(_pillar_tube(coll, bvh_tube))
    pf = _pillar_fairing(coll, bvh_front, screws)
    made += pf

    made += _front_foot(coll, screws, ti)
    tailL = [Vector(HOOP_HALF[-2]), Vector(HOOP_HALF[-1])]
    tailR = [Vector((p.x, -p.y, p.z)) for p in tailL]
    made += _rear_foot(coll, screws, ti, 1, tailL)
    made += _rear_foot(coll, screws, ti, -1, tailR)

    seals = Acc()
    for (pe, te, into, rt) in all_ends:
        _seal(seals, pe, te, into, rt)
    sl = _obj("Seals", seals.v, seals.f, coll, "MatteBlack", auto=40.0)
    C.add_bevel(sl, 0.0004, 2, angle=34.0)       # R2-D9
    made.append(sl)
    for tag, sv in (("L", 0.130), ("R", -0.130)):
        j = idx_of(sv)
        vn = _crown_vane(coll, pts[j].x, pts[j].y, bvh_front, tag)
        if vn is not None:
            made.append(vn)

    made += _pod(coll, screws)
    made += _fin(coll, screws, ti)
    made += _halo_cam(coll, screws, bvh_front)

    allv = list(front_mesh[0])
    allf = list(front_mesh[1])
    for strip in pf:
        pmw = strip.matrix_world
        off = len(allv)
        allv += [tuple(pmw @ v.co) for v in strip.data.vertices]
        allf += [tuple(i + off for i in p.vertices) for p in strip.data.polygons]
    made += _loom(coll, _bvh(allv, allf))

    made.append(_obj("Fasteners", screws.v, screws.f, coll, "SteelFastener",
                     auto=30.0))
    made.append(_obj("MountDetail", ti.v, ti.f, coll, "Titanium", auto=30.0))
    return made
