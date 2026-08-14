"""_wt_before - PRE-FIX snapshot of wheel_tyre for before/after crops.

Not assembled (underscore-prefixed modules are skipped by s08_assemble).

wheel_tyre - one front + one rear F1 wheel/tyre corner, mirrored to 4 corners.

Authoring frame (LOCAL, per wheel object)
-----------------------------------------
The mesh is built with the AXLE along local +Z, exactly as `s03_materials.
tyre_rubber` expects ("the tyre mesh is built around +Z and then rotated onto
the axle, so in OBJECT space the axle is still Z: radius = |xy|, sidewall =
large |z|").  Local +Z is the OUTBOARD face.

The object is then placed with

    left  corner :  rotation_euler = (-90 deg, 0, 0)        -> +Z -> car +Y
    right corner :  rotation_euler = (-90 deg, 0, 180 deg)  -> +Z -> car -Y

Both are proper rotations (no negative scale), so normals and the object-space
texture lookups stay identical, and the two sides share mesh data.  Under both
rotations local +Y maps to world -Z, i.e. LOCAL +Y IS DOWN - which is why the
contact patch is flattened towards local +Y.

Loaded vs unloaded radius
-------------------------
S.TYRE_R (0.360) is the LOADED rolling radius: hub at z = 0.360, contact plane
at z = 0.  A tyre that is a perfect circle of radius 0.360 is the classic CG
tell, so the carcass is moulded at 361.8 mm and the bottom 2 mm is squashed
flat against z = 0, with the sidewall bulging outboard beside the patch.  The
tread therefore still touches z = 0 exactly; the moulded (unloaded) diameter is
723.6 mm rather than 720.0 mm.
"""

import math
import os

import bpy
from mathutils import Vector

import common as C
import spec as S

NAME = "wheel_tyre"
TAU = math.pi * 2.0

# --------------------------------------------------------------------------- #
# principal dimensions
# --------------------------------------------------------------------------- #

R_LOADED = S.TYRE_R                 # 0.360, hub height / contact radius
R_MOULD = R_LOADED + 0.0018         # unloaded tread radius
R_BEAD = S.RIM_R                    # 0.2286  tyre bore
R_SEAT = S.RIM_INNER_R              # 0.2296  rim bead seat (1 mm proud, D046)
R_FLANGE = 0.2436                   # rim flange tip
R_MAXW = 0.2975                     # radius at which the tyre is widest
R_BAND0, R_BAND1 = 0.3005, 0.3225   # compound band (matches TyreRubber ramp)

TYRE_SEG = 208
RIM_SEG = 160
COVER_SEG = 176

PATCH_HALF = math.radians(11.0)     # angular reach of the contact deformation

# Carcass half-width inset from the spec half section.  With the shoulder built
# the right way round the compound-band relief (+0.90 mm along the normal, and
# the normal is axial where the band starts) is the widest feature on the tyre,
# not the mould flash - so the carcass is pulled in far enough that the CREST of
# that relief, hw + 0.0009, lands 0.2 mm inside the spec half section and the car
# stays under the 2.000 m regulation width.
HW_INSET = 0.0011


# --------------------------------------------------------------------------- #
# hub-referenced stations  (D-R3-03 / D-R3-12)
# --------------------------------------------------------------------------- #
# Everything else in this file is referenced to the rim flange face
# zf = hw - 0.010, which MOVES with the tyre section width: the front flange is
# at local z 0.1425, the rear at 0.1925.  The brake corner is referenced to the
# hub origin instead, which sits at car y = tyre_y - S.UPRIGHT_Y_INSET, so a
# brake feature at hub station `ax` always lands at
#
#     local z = ax - S.UPRIGHT_Y_INSET
#
# on EVERY corner, front and rear alike (tyre_y cancels).  Anything in this
# module that has to mate with the brake assembly must be written in this frame,
# not in zf, or the front and rear corners land in different places.  These are
# the stations wheel_tyre mates with:
HUB_Z = -S.UPRIGHT_Y_INSET                  # -0.0850  hub origin plane
BELL_FACE_Z = HUB_Z + 0.0684                # -0.0166  disc-bell OUTBOARD drive
BELL_FACE_R = (0.0470, 0.0648)              #          face, an annulus
HUB_BOSS_TH = math.radians(30.0)            #          hub's own 6 drive bosses
HUB_FLANGE_Z = HUB_Z + 0.0900               # +0.0050  hub flange underside
HUB_NUT_Z = HUB_Z + 0.1380                  # +0.0530  hub nut end cap, r 0.0140
UPRIGHT_FACE_Z = HUB_Z + 0.0300             # -0.0550  outboard end face of the
#                                                      STATIC upright - nothing
#                                                      that rotates with the
#                                                      wheel may cross it


# --------------------------------------------------------------------------- #
# tiny maths helpers (kept local - nothing here belongs in common.py)
# --------------------------------------------------------------------------- #

def _hash(i, j, k):
    n = (i * 73856093) ^ (j * 19349663) ^ (k * 83492791)
    n = ((n ^ (n >> 13)) * 1274126177) & 0x7FFFFFFF
    return (((n ^ (n >> 16)) & 0xFFFF) / 65535.0) - 0.5


def _vnoise(p, scale):
    """Smooth value noise, continuous everywhere (no seams on a closed loft)."""
    x, y, z = p[0] * scale, p[1] * scale, p[2] * scale
    i, j, k = math.floor(x), math.floor(y), math.floor(z)
    fx, fy, fz = x - i, y - j, z - k
    ux = fx * fx * (3.0 - 2.0 * fx)
    uy = fy * fy * (3.0 - 2.0 * fy)
    uz = fz * fz * (3.0 - 2.0 * fz)
    out = 0.0
    for dk in (0, 1):
        wk = uz if dk else 1.0 - uz
        for dj in (0, 1):
            wj = uy if dj else 1.0 - uy
            for di in (0, 1):
                wi = ux if di else 1.0 - ux
                out += wi * wj * wk * _hash(i + di, j + dj, k + dk)
    return out


def _mix(a, b, t):
    return a + (b - a) * t


def _sstep(e0, e1, x):
    if e1 == e0:
        return 0.0 if x < e0 else 1.0
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3.0 - 2.0 * t)


def _add(V, F, verts, faces):
    b = len(V)
    V.extend(verts)
    F.extend([tuple(i + b for i in f) for f in faces])


def _obj(name, V, F, coll, mat, angle=32.0, merge=None):
    ob = C.new_obj(name, V, F, coll=coll, smooth=True)
    if merge:
        C.merge_doubles(ob, merge)
    C.shade_auto_smooth(ob, angle)
    S.assign(ob, mat)
    return ob


def _lathe(profile, segs, wrap_profile=True, warp=None):
    """Revolve a (r, z) polyline about +Z.  `warp(x, y, z, ip, iseg)` may return
    a replacement (x, y, z).  Returns (verts, faces)."""
    n = len(profile)
    V = []
    for ip, (r, z) in enumerate(profile):
        for i in range(segs):
            t = TAU * i / segs
            x, y = r * math.cos(t), r * math.sin(t)
            if warp is not None:
                x, y, z2 = warp(x, y, z, ip, i)
                V.append((x, y, z2))
            else:
                V.append((x, y, z))
    F = []
    last = n if wrap_profile else n - 1
    for ip in range(last):
        a = (ip % n) * segs
        b = ((ip + 1) % n) * segs
        for i in range(segs):
            j = (i + 1) % segs
            F.append((a + i, a + j, b + j, b + i))
    return V, F


def _arc_pts(cx, cz, rad, a0, a1, n):
    return [(cx + rad * math.cos(_mix(a0, a1, i / (n - 1.0))),
             cz + rad * math.sin(_mix(a0, a1, i / (n - 1.0)))) for i in range(n)]


# --------------------------------------------------------------------------- #
# tyre section
# --------------------------------------------------------------------------- #

def _tyre_half(hw_spec):
    """Half section, (r, z) from the tread centreline out to the bead heel.

    hw_spec  tyre half section width from the spec.  The moulded carcass stops
             HW_INSET short of it so the crest of the compound-band relief -
             the widest feature on the flank - stays inside the 2.000 m
             regulation width.
    """
    hw = hw_spec - HW_INSET
    z_flange = hw_spec - 0.010          # rim flange outer face
    z_t = 0.815 * hw                    # edge of the flat tread
    crown = 0.0016                      # tread crown, centre proud of the edge
    out = []

    # --- tread: broad and near flat, gently crowned ------------------------- #
    # ~7 mm section pitch: the 405 mm rear tread was 13 rings = 13.7 mm bands,
    # which is a flat untextured span at hero distance (D-R2-02b).
    nt = max(13, int(z_t / 0.0070) + 2)
    for i in range(nt):
        z = z_t * i / (nt - 1.0)
        out.append((R_MOULD - crown * (z / z_t) ** 2, z))

    # --- shoulder: superellipse, p > 2 gives a DEFINED shoulder ------------- #
    r1, r2 = R_MOULD - crown, R_MAXW
    dr, dz = r1 - r2, hw - z_t
    p = 2.35

    def sh(t):
        # t = 0 -> (tread edge r, z_t);  t = 1 -> (R_MAXW, hw = widest point).
        # D-R2-01: this used to return `hw - dz * b`, which put the tread edge
        # at the WIDEST z and threw the shoulder backwards, cutting a 28-37 mm
        # deep annular gutter between tread and sidewall.
        u = t * math.pi * 0.5
        a = max(math.cos(u), 0.0) ** (2.0 / p)
        b = max(math.sin(u), 0.0) ** (2.0 / p)
        return (r2 + dr * a, z_t + dz * b)

    def t_of_r(r):
        a = min(max((r - r2) / dr, 0.0), 1.0)
        return math.acos(min(1.0, a ** (p * 0.5))) / (math.pi * 0.5)

    ts = [i / 33.0 for i in range(34)]
    # extra samples so the compound band step is crisp, not a ramp
    for rr in (R_BAND0 - 0.0016, R_BAND0 - 0.0006, R_BAND0, R_BAND0 + 0.0010,
               R_BAND1 - 0.0010, R_BAND1, R_BAND1 + 0.0006, R_BAND1 + 0.0016):
        ts.append(t_of_r(rr))
    ts = sorted(set(round(t, 6) for t in ts if 0.0 < t < 1.0))
    for t in ts:
        r, z = sh(t)
        if r >= R_MAXW + 0.0013:        # stop before the parting-line ridge
            out.append((r, z))

    # --- mould parting flash at the widest point ---------------------------- #
    for dr_, dzz in ((0.0013, 0.0), (0.0007, 0.00034), (0.0, 0.00040),
                     (-0.0007, 0.00034), (-0.0013, 0.0)):
        out.append((R_MAXW + dr_, hw + dzz))

    # --- lower sidewall: convex bulge, tucking under the flange ------------- #
    low = [(R_MAXW - 0.0013, hw), (R_MAXW - 0.0075, hw - 0.0004),
           (R_MAXW - 0.0155, hw - 0.0012), (R_MAXW - 0.0255, hw - 0.0026),
           (R_MAXW - 0.0355, hw - 0.0046), (R_MAXW - 0.0445, hw - 0.0070)]
    out.extend(C.catmull_rom(low, 17))
    # moulded rim-protector rib just above the bead
    out.extend([(0.2489, hw - 0.00755), (0.2482, hw - 0.00728),
                (0.2474, hw - 0.00715), (0.2466, hw - 0.00734),
                (0.2459, hw - 0.00800), (0.2454, hw - 0.00890)])
    out.extend(C.catmull_rom(
        [(0.2454, hw - 0.00890), (0.2444, hw - 0.0104), (0.2436, hw - 0.0120),
         (0.2430, hw - 0.0132)], 5))

    # --- bead: deliberately buried ~1 mm inside the rim flange -------------- #
    out.extend([(0.2400, z_flange - 0.0079), (0.2350, z_flange - 0.0122),
                (0.2296, z_flange - 0.0152), (R_BEAD, z_flange - 0.0172),
                (R_BEAD, z_flange - 0.0280)])
    return out


def _band_relief(half):
    """Raise the compound band 0.55 mm along the surface normal.

    The step edges land 1.6 mm outside the TyreRubber colour ramp, so the dark
    red sits on the flat top of the relief instead of straddling its chamfer.
    """
    out = list(half)
    n = len(half)
    for i in range(1, n - 1):
        r, z = half[i]
        h = (_sstep(R_BAND0 - 0.0016, R_BAND0, r)
             * (1.0 - _sstep(R_BAND1, R_BAND1 + 0.0016, r)))
        if h <= 0.0:
            continue
        r0, z0 = half[i - 1]
        r1, z1 = half[i + 1]
        dr, dz = r1 - r0, z1 - z0
        L = math.hypot(dr, dz) or 1.0
        nx, nz = dz / L, -dr / L        # outward normal of the section
        out[i] = (r + nx * 0.00090 * h, z + nz * 0.00090 * h)
    return out


def _tyre_profile(hw):
    """Closed (r, z) section loop of the whole tyre."""
    half = _band_relief(_tyre_half(hw))
    bore_z = half[-1][1]
    loop = list(half)
    loop.append((R_BEAD, bore_z * 0.45))
    loop.append((R_BEAD, 0.0))
    loop.append((R_BEAD, -bore_z * 0.45))
    loop.extend([(r, -z) for (r, z) in reversed(half)][:-1])
    return loop


# --------------------------------------------------------------------------- #
# contact patch deformation - applied to the tyre AND everything glued to it
# --------------------------------------------------------------------------- #

def _squash(x, y, z):
    """Flatten the bottom of the tyre onto local y = R_LOADED (world z = 0)."""
    rho = math.hypot(x, y)
    if rho < 0.2400 or y <= 0.0:
        return x, y, z
    phi = math.acos(max(-1.0, min(1.0, y / rho)))     # angle off straight down
    if phi > PATCH_HALF * 2.2:
        return x, y, z

    w = _sstep(0.2700, 0.3300, rho)
    if w > 0.0:
        limit = R_LOADED / math.cos(min(phi, 1.2))
        e = rho - limit
        k = 0.0004
        # soft max(0, e): stays >= e so the tread never crosses z = 0, and
        # rounds the shoulder of the patch instead of creasing it
        pull = 0.5 * (e + math.sqrt(e * e + k * k)) * w
        if pull > 0.0:
            s = (rho - pull) / rho
            x, y = x * s, y * s

    # sidewall squeezes outboard beside the patch
    g = max(0.0, 1.0 - (phi / (PATCH_HALF * 1.9)) ** 2) ** 1.6
    if g > 0.0 and abs(z) > 0.060:
        rr = (rho - 0.2880) / 0.0340
        z += math.copysign(0.0014 * g * math.exp(-rr * rr), z)
    return x, y, z


def _tread_edge_z(hw_spec):
    return 0.815 * (hw_spec - HW_INSET)


def _zsquish(ob, k):
    """Compress the MESH along the axle by k and give the OBJECT scale 1/k.

    World geometry is unchanged, but object-space |z| - which is what
    s03_materials.tyre_rubber uses to split tread from sidewall, with a fixed
    0.082..0.104 m ramp - is remapped so that the split lands exactly on the
    shoulder of THIS tyre.  Without it the 405 mm rear tread carries a matte
    stripe down its middle and glossy bands either side, which reads as dirt.
    """
    me = ob.data
    for v in me.vertices:
        v.co.z *= k
    me.update()
    ob.scale = (1.0, 1.0, 1.0 / k)
    return ob


def _tyre_mesh(name, hw, coll):
    prof = _tyre_profile(hw)
    npt = len(prof)

    def warp(x, y, z, ip, iseg):
        r, z0 = prof[ip]
        # moulded surface noise: a real tyre is never a perfect surface of
        # revolution.  Amplitude stays under 0.12 mm so it only shows up in
        # grazing reflections, which is exactly where a CG tyre gives itself up.
        if r > 0.2450:
            # 45 mm wavelength: anything finer aliases against the 224 segments
            # and turns into blotches.  The fine pebble is the material's bump.
            amp = 0.00008 if abs(z0) < 0.735 * hw else 0.00013
            nz = _vnoise((x, y, z), 22.0)
            s = 1.0 + (nz * amp) / r
            x, y = x * s, y * s
            z = z + nz * amp * (1.0 if z0 > 0 else -1.0) * 0.35
        return _squash(x, y, z)

    V, F = _lathe(prof, TYRE_SEG, wrap_profile=True, warp=warp)
    ob = _obj(name, V, F, coll, "TyreRubber", angle=26.0, merge=6e-5)
    return ob, prof


# --------------------------------------------------------------------------- #
# sidewall surface lookup + conformed relief (lettering, vent pips)
# --------------------------------------------------------------------------- #

def _sidewall_fn(prof, hw, upper=False):
    """z(r) and a surface frame on the OUTBOARD flank.

    upper=False -> the flank below the widest point (r 0.229 .. R_MAXW)
    upper=True  -> the shoulder above it (r R_MAXW .. tread edge)
    """
    if upper:
        branch = [(r, z) for (r, z) in prof if z > 0.30 * hw and r >= R_MAXW]
    else:
        branch = [(r, z) for (r, z) in prof
                  if z > 0.30 * hw and 0.2290 <= r <= R_MAXW + 1e-9]
    branch.sort()
    rs = [p[0] for p in branch]
    zs = [p[1] for p in branch]

    def z_at(r):
        r = min(max(r, rs[0]), rs[-1])
        lo, hi = 0, len(rs) - 1
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if rs[mid] <= r:
                lo = mid
            else:
                hi = mid
        span = rs[hi] - rs[lo]
        t = 0.0 if span <= 0 else (r - rs[lo]) / span
        return _mix(zs[lo], zs[hi], t)

    def frame(r, th):
        """Point + outward unit normal on the sidewall at (r, theta)."""
        d = 0.0008
        slope = (z_at(r + d) - z_at(r - d)) / (2.0 * d)
        L = math.hypot(1.0, slope)
        c, s = math.cos(th), math.sin(th)
        p = Vector((r * c, r * s, z_at(r)))
        nrm = Vector((-slope * c / L, -slope * s / L, 1.0 / L))
        return p, nrm

    return z_at, frame


def _extrude_outline(outline, frame, height, chamfer, planar_top=False):
    """outline: [(theta, r), ...] closed loop.  Build a raised pad conformed to
    the surface, with a chamfered top edge so no edge is perfectly sharp.

    The base ring is sunk 0.3 mm below the surface so the pad is a closed
    manifold that is unambiguously attached (no coincident faces, no floating).
    """
    clean = []
    for p in outline:
        if not clean or abs(p[0] - clean[-1][0]) > 1e-9 or abs(p[1] - clean[-1][1]) > 1e-9:
            clean.append(p)
    if len(clean) > 1 and abs(clean[0][0] - clean[-1][0]) < 1e-9 \
            and abs(clean[0][1] - clean[-1][1]) < 1e-9:
        clean.pop()
    outline = clean
    n = len(outline)
    cth = sum(o[0] for o in outline) / n
    cr = sum(o[1] for o in outline) / n
    # local (arc, radial) coordinates + a true inward edge normal per point, so
    # the chamfer is a real offset curve and does not pinch at the corners
    loc = [((th - cth) * cr, r - cr) for (th, r) in outline]
    inw = []
    for i in range(n):
        ax, ay = loc[i - 1]
        bx, by = loc[(i + 1) % n]
        tx, ty = bx - ax, by - ay
        L = math.hypot(tx, ty) or 1.0
        nx, ny = ty / L, -tx / L
        if nx * loc[i][0] + ny * loc[i][1] > 0.0:
            nx, ny = -nx, -ny
        inw.append((nx, ny))
    rings = []
    for (fh, ins) in ((-0.35, 0.0), (0.62, 0.0), (1.0, chamfer)):
        ring = []
        for i in range(n):
            arc = loc[i][0] + inw[i][0] * ins
            dr = loc[i][1] + inw[i][1] * ins
            p, nrm = frame(cr + dr, cth + arc / cr)
            ring.append(tuple(p + nrm * (height * fh)))
        rings.append(ring)
    if planar_top:
        # A machined boss on a shallow cone is a FLAT milled plateau.  Snapping
        # the top ring to one plane also makes its fan cap exactly planar - a
        # conformed cap shows shading creases at the corners otherwise.
        zt = sum(v[2] for v in rings[2]) / n
        rings[2] = [(x, y, zt) for (x, y, _z) in rings[2]]
    V = [v for ring in rings for v in ring]
    F = []
    for k in range(2):
        a, b = k * n, (k + 1) * n
        for i in range(n):
            j = (i + 1) % n
            F.append((a + i, a + j, b + j, b + i))
    F.append(tuple(range(2 * n, 3 * n)))
    F.append(tuple(range(n))[::-1])
    return V, F


def _mirror_z(V, F):
    return ([(x, y, -z) for (x, y, z) in V], [tuple(reversed(f)) for f in F])


def _squash_verts(V):
    return [_squash(*v) for v in V]


GLYPHS = {
    " ": [],
    "A": [(0.02, 0, 0.31, 1), (0.31, 1, 0.60, 0), (0.13, 0.36, 0.49, 0.36)],
    "P": [(0.08, 0, 0.08, 1), (0.08, 1, 0.44, 1), (0.44, 1, 0.44, 0.54),
          (0.44, 0.54, 0.08, 0.54)],
    "E": [(0.09, 0, 0.09, 1), (0.09, 1, 0.53, 1), (0.09, 0.52, 0.45, 0.52),
          (0.09, 0, 0.53, 0)],
    "X": [(0.04, 0, 0.58, 1), (0.58, 0, 0.04, 1)],
    "R": [(0.08, 0, 0.08, 1), (0.08, 1, 0.44, 1), (0.44, 1, 0.44, 0.54),
          (0.44, 0.54, 0.08, 0.54), (0.24, 0.54, 0.54, 0)],
    "S": [(0.52, 0.90, 0.34, 1.0), (0.34, 1.0, 0.12, 0.92), (0.12, 0.92, 0.14, 0.66),
          (0.14, 0.66, 0.44, 0.52), (0.44, 0.52, 0.52, 0.30),
          (0.52, 0.30, 0.34, 0.02), (0.34, 0.02, 0.10, 0.12)],
    "O": [(0.10, 0.24, 0.10, 0.76), (0.52, 0.24, 0.52, 0.76),
          (0.10, 0.76, 0.21, 1.0), (0.21, 1.0, 0.41, 1.0), (0.41, 1.0, 0.52, 0.76),
          (0.10, 0.24, 0.21, 0.0), (0.21, 0.0, 0.41, 0.0), (0.41, 0.0, 0.52, 0.24)],
    "0": [(0.10, 0.24, 0.10, 0.76), (0.52, 0.24, 0.52, 0.76),
          (0.10, 0.76, 0.21, 1.0), (0.21, 1.0, 0.41, 1.0), (0.41, 1.0, 0.52, 0.76),
          (0.10, 0.24, 0.21, 0.0), (0.21, 0.0, 0.41, 0.0), (0.41, 0.0, 0.52, 0.24)],
    "1": [(0.31, 0, 0.31, 1), (0.15, 0.80, 0.31, 1.0), (0.14, 0, 0.48, 0)],
    "3": [(0.09, 0.93, 0.40, 1.0), (0.40, 1.0, 0.52, 0.78), (0.52, 0.78, 0.28, 0.55),
          (0.28, 0.55, 0.54, 0.31), (0.54, 0.31, 0.40, 0.02), (0.40, 0.02, 0.08, 0.09)],
    "5": [(0.53, 1.0, 0.13, 1.0), (0.13, 1.0, 0.11, 0.57), (0.11, 0.57, 0.38, 0.61),
          (0.38, 0.61, 0.54, 0.38), (0.54, 0.38, 0.44, 0.05), (0.44, 0.05, 0.08, 0.11)],
    "6": [(0.50, 0.92, 0.25, 1.0), (0.25, 1.0, 0.09, 0.62), (0.09, 0.62, 0.09, 0.24),
          (0.09, 0.24, 0.29, 0.0), (0.29, 0.0, 0.49, 0.11), (0.49, 0.11, 0.52, 0.34),
          (0.52, 0.34, 0.30, 0.50), (0.30, 0.50, 0.10, 0.44)],
    "7": [(0.06, 1, 0.56, 1), (0.56, 1, 0.24, 0)],
    "8": [(0.13, 0.57, 0.13, 0.86), (0.49, 0.57, 0.49, 0.86), (0.13, 0.86, 0.31, 1.0),
          (0.31, 1.0, 0.49, 0.86), (0.13, 0.57, 0.31, 0.45), (0.31, 0.45, 0.49, 0.57),
          (0.10, 0.45, 0.10, 0.16), (0.52, 0.45, 0.52, 0.16), (0.10, 0.16, 0.31, 0.0),
          (0.31, 0.0, 0.52, 0.16), (0.10, 0.45, 0.31, 0.45), (0.31, 0.45, 0.52, 0.45)],
    "C": [(0.52, 0.80, 0.42, 0.96), (0.42, 0.96, 0.24, 1.0), (0.24, 1.0, 0.11, 0.76),
          (0.11, 0.76, 0.11, 0.24), (0.11, 0.24, 0.24, 0.0), (0.24, 0.0, 0.42, 0.04),
          (0.42, 0.04, 0.52, 0.20)],
    "2": [(0.09, 0.86, 0.26, 1.0), (0.26, 1.0, 0.46, 0.94), (0.46, 0.94, 0.50, 0.70),
          (0.50, 0.70, 0.08, 0.02), (0.08, 0.02, 0.55, 0.02)],
    "F": [(0.09, 0, 0.09, 1), (0.09, 1, 0.53, 1), (0.09, 0.52, 0.45, 0.52)],
    "L": [(0.11, 1, 0.11, 0), (0.11, 0, 0.53, 0)],
    "J": [(0.20, 1.0, 0.54, 1.0), (0.44, 1.0, 0.44, 0.22),
          (0.44, 0.22, 0.30, 0.04), (0.30, 0.04, 0.13, 0.13)],
    "4": [(0.44, 0, 0.44, 1), (0.44, 1, 0.06, 0.30), (0.06, 0.30, 0.56, 0.30)],
    "/": [(0.04, -0.05, 0.56, 1.0)],
    "-": [(0.08, 0.50, 0.54, 0.50)],
    ".": [(0.26, 0.02, 0.32, 0.02)],
}
ADVANCE = {" ": 0.42, "/": 0.62, "-": 0.62, ".": 0.36, "1": 0.60}


def _text_strokes(text, th0, r_base, size, stroke_w, dirn=-1.0):
    """Stroke capsules for `text`, returned as closed (theta, r) outlines."""
    widths = [ADVANCE.get(ch, 0.68) for ch in text]
    total = sum(widths) + 0.12 * (len(text) - 1)
    u = -0.5 * total * size
    out = []
    for ch, w in zip(text, widths):
        for (x0, y0, x1, y1) in GLYPHS.get(ch, []):
            pts = _capsule(u + x0 * size, y0 * size,
                           u + x1 * size, y1 * size, stroke_w)
            out.append([(th0 + dirn * px / r_base, r_base + py) for (px, py) in pts])
        u += (w + 0.12) * size
    return out


def _capsule(x0, y0, x1, y1, w, n=7):
    """Rounded stroke outline in glyph space, returned CCW."""
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1e-9
    ux, uy = dx / L, dy / L
    px, py = -uy, ux
    rad = w * 0.5
    pts = []
    for i in range(n):
        a = math.pi * (i / (n - 1.0)) - math.pi * 0.5
        ca, sa = math.cos(a), math.sin(a)
        pts.append((x1 + (ux * ca + px * sa) * rad, y1 + (uy * ca + py * sa) * rad))
    for i in range(n):
        a = math.pi * (i / (n - 1.0)) + math.pi * 0.5
        ca, sa = math.cos(a), math.sin(a)
        pts.append((x0 + (ux * ca + px * sa) * rad, y0 + (uy * ca + py * sa) * rad))
    return pts


# --------------------------------------------------------------------------- #
# sidewall lettering + mould vent pips
# --------------------------------------------------------------------------- #

WORDMARK = [(math.radians(a), "APEX") for a in (2.0, 152.0, 254.0)]
SIZEMARK = [(math.radians(a), "305/670-R18") for a in (42.0, 205.0)]


def _lettering(name, prof, hw, coll):
    _z, frame = _sidewall_fn(prof, hw)
    V, F = [], []
    jobs = ([(th, txt, 0.2600, 0.0140, 0.0027, 0.00085) for th, txt in WORDMARK]
            + [(th, txt, 0.2600, 0.0078, 0.0017, 0.00060) for th, txt in SIZEMARK]
            + [(math.radians(a), "C3", 0.2790, 0.0110, 0.0021, 0.00075)
               for a in (78.0, 318.0)]
            + [(math.radians(a), t, 0.2512, 0.0056, 0.0013, 0.00045)
               for a, t in ((100.0, "0417-24"), (186.0, "APEX-F1"),
                            (300.0, "PRESS-18"))])
    for th, txt, r_base, size, sw, h in jobs:
        for outline in _text_strokes(txt, th, r_base, size, sw):
            v, f = _extrude_outline(outline, frame, h, 0.00030)
            _add(V, F, _squash_verts(v), f)
    # inboard flank carries the wordmark only
    Vi, Fi = [], []
    for th, txt in WORDMARK:
        # dirn flips because the whole set is about to be mirrored in z: the
        # inboard flank must still read correctly when seen from inboard.
        for outline in _text_strokes(txt, th + 0.34, 0.2600, 0.0140, 0.0027,
                                     dirn=1.0):
            v, f = _extrude_outline(outline, frame, 0.00085, 0.00030)
            _add(Vi, Fi, _squash_verts(v), f)
    Vi, Fi = _mirror_z(Vi, Fi)
    _add(V, F, Vi, Fi)
    return _obj(name, V, F, coll, "MatteBlack", angle=38.0)


def _vent_pips(name, prof, hw, coll):
    """Small round mould vent pips - the rubber that squeezed into the mould's
    air bleeds.  Real ones are ragged: some full length, some torn short."""
    _zl, frame_lo = _sidewall_fn(prof, hw, upper=False)
    _zu, frame_hi = _sidewall_fn(prof, hw, upper=True)
    V, F = [], []
    seg = 8
    rows = ((0.3390, frame_hi, 26, 0.31), (0.3268, frame_hi, 24, 1.11),
            (0.3120, frame_hi, 22, 1.97), (0.2905, frame_lo, 22, 0.44),
            (0.2740, frame_lo, 20, 0.74), (0.2560, frame_lo, 18, 2.51))
    for (rr, frame, count, phase), side in ((r, s) for s in (1.0, -1.0)
                                            for r in rows):
        for k in range(count):
            th = phase + (0.0 if side > 0 else 0.31) + TAU * k / count
            jit = _hash(int(rr * 1e4), k, 7 if side > 0 else 11)
            if jit < -0.42:
                continue                       # torn off in the mould
            p, nrm = frame(rr + 0.0018 * jit, th + 0.05 * jit)
            if side < 0:                       # same pips on the inboard flank
                p = Vector((p.x, p.y, -p.z))
                nrm = Vector((nrm.x, nrm.y, -nrm.z))
            length = 0.0016 + 0.0015 * jit
            t1 = Vector((-math.sin(th), math.cos(th), 0.0))
            t1 = (t1 - nrm * t1.dot(nrm)).normalized()
            t2 = nrm.cross(t1)
            tilt = t1 * (0.35 * jit) + t2 * (0.28 * _hash(k, 3, int(rr * 1e4)))
            axis = (nrm + tilt).normalized()
            ring_r = (0.00072, 0.00069, 0.00060, 0.00034)
            ring_h = (-0.0004, 0.42, 0.78, 1.0)
            base = len(V)
            for ir, (rad, hf) in enumerate(zip(ring_r, ring_h)):
                hh = hf if ir == 0 else hf * length
                cen = p + axis * hh
                for i in range(seg):
                    a = TAU * i / seg
                    q = cen + t1 * (rad * math.cos(a)) + t2 * (rad * math.sin(a))
                    V.append(_squash(q.x, q.y, q.z))
            for ir in range(3):
                a, b = base + ir * seg, base + (ir + 1) * seg
                for i in range(seg):
                    j = (i + 1) % seg
                    F.append((a + i, a + j, b + j, b + i))
            F.append(tuple(range(base + 3 * seg, base + 4 * seg)))
            F.append(tuple(range(base, base + seg))[::-1])
    return _obj(name, V, F, coll, "TyreRubber", angle=44.0)


# --------------------------------------------------------------------------- #
# rim barrel - full 18 in barrel with bead seats, humps and J flanges
# --------------------------------------------------------------------------- #

def _barrel_half(zf):
    """(r, z) from the centre of the well outboard, then back along the inside."""
    w0 = zf - 0.0800
    outer = [(0.1960, 0.0), (0.1960, w0), (0.1988, zf - 0.0757),
             (0.2075, zf - 0.0663), (0.2205, zf - 0.0560),
             (0.2268, zf - 0.0492), (0.2292, zf - 0.0452),
             (0.2286, zf - 0.0410), (0.2274, zf - 0.0388)]
    seat = [(0.2274, zf - 0.0388), (0.2282, zf - 0.0300),
            (0.2290, zf - 0.0212), (0.2296, zf - 0.0140)]
    fill = C.catmull_rom([(0.2296, zf - 0.0140), (0.2330, zf - 0.0118),
                          (0.2380, zf - 0.0086), (0.2412, zf - 0.0058),
                          (R_FLANGE, zf - 0.0030)], 9)
    tip = _arc_pts(R_FLANGE - 0.0030, zf - 0.0030, 0.0030, 0.0, math.pi * 0.5, 7)
    face = [(0.2380, zf), (0.2320, zf), (0.2255, zf), (0.2205, zf), (0.2180, zf)]
    inner = [(0.2166, zf - 0.0012), (0.2160, zf - 0.0060),
             (0.2186, zf - 0.0150), (0.2205, zf - 0.0300),
             (0.2200, zf - 0.0430), (0.2168, zf - 0.0524),
             (0.2060, zf - 0.0620), (0.1948, zf - 0.0730),
             (0.1908, zf - 0.0790), (0.1905, 0.0)]
    return outer + seat[1:] + list(fill)[1:] + tip[1:] + face + inner


def _rim_barrel(name, zf, coll):
    half = _barrel_half(zf)
    loop = half + [(r, -z) for (r, z) in reversed(half)][1:-1]
    V, F = _lathe(loop, RIM_SEG, wrap_profile=True)
    return _obj(name, V, F, coll, "WheelRim", angle=26.0, merge=8e-5)


# --------------------------------------------------------------------------- #
# wheel centre - dished spider, ribbed on the inboard face, hub register
# --------------------------------------------------------------------------- #

def _wheel_centre(name, zf, coll):
    front = [(0.2225, zf - 0.0060), (0.2100, zf - 0.0132), (0.1900, zf - 0.0232),
             (0.1600, zf - 0.0322), (0.1250, zf - 0.0382), (0.0950, zf - 0.0402),
             (0.0760, zf - 0.0392), (0.0640, zf - 0.0330), (0.0570, zf - 0.0230),
             (0.0540, zf - 0.0140), (0.0532, zf - 0.0088), (0.0500, zf - 0.0082),
             (0.0400, zf - 0.0082), (0.0334, zf - 0.0082), (0.0320, zf - 0.0100),
             (0.0320, zf - 0.0170)]
    bore = [(0.0320, 0.0), (0.0320, -0.0700), (0.0322, -0.0836), (0.0342, -0.0850)]
    hub = [(0.0450, -0.0850), (0.0464, -0.0841), (0.0478, -0.0839),
           (0.0592, -0.0839), (0.0606, -0.0841), (0.0620, -0.0850),
           (0.0820, -0.0850), (0.0888, -0.0850),
           (0.0900, -0.0838), (0.0900, -0.0806), (0.0884, -0.0794),
           (0.0800, -0.0790), (0.0784, -0.0770)]
    back = [(0.0780, -0.0600), (0.0780, -0.0200), (0.0790, zf - 0.0640),
            (0.0900, zf - 0.0576), (0.1150, zf - 0.0542), (0.1500, zf - 0.0500),
            (0.1850, zf - 0.0420), (0.2080, zf - 0.0300), (0.2190, zf - 0.0200),
            (0.2225, zf - 0.0140)]
    loop = front + bore + hub + back
    ribw = ([0.0] * len(front) + [0.0] * len(bore) + [0.0] * len(hub)
            + [0.15, 0.7, 1.0, 1.0, 1.0, 1.0, 0.8, 0.35, 0.1, 0.0])

    def warp(x, y, z, ip, iseg):
        w = ribw[ip]
        if w > 0.0:
            th = TAU * iseg / RIM_SEG
            lobe = _sstep(0.30, 0.86, 0.5 + 0.5 * math.cos(6.0 * th))
            z -= 0.0052 * w * lobe
        return x, y, z

    V, F = _lathe(loop, RIM_SEG, wrap_profile=True, warp=warp)
    return _obj(name, V, F, coll, "WheelRim", angle=28.0, merge=8e-5)


# --------------------------------------------------------------------------- #
# machined aero cover - broad flat annulus, ONE step up to the centre boss
# --------------------------------------------------------------------------- #

def _cover_face_z(zf, r):
    """Outboard face of the cover: shallow 2 deg cone, one step, boss."""
    z_out = zf + 0.0010
    r_out, r_step = 0.2415, 0.0980
    if r >= r_step:
        return z_out + (r_out - r) * 0.0200
    z_ring = z_out + (r_out - r_step) * 0.0200 + 0.0055
    if r >= 0.0950:
        t = _sstep(0.0950, r_step, r)
        return _mix(z_ring, z_out + (r_out - r_step) * 0.0200, t)
    return z_ring


# ONE witness groove, and it sits out at the rim where the face is parted from
# the edge chamfer.  The inner two (r = 107.5 and 70 mm) were adding concentric
# rings to the hub area and fighting the "broad flat annulus" brief (D-R2-04).
COVER_GROOVES = ((0.2330, 0.0019, 0.00085),)

# Turned finish: the cover is faced off on a lathe, so the whole disc carries a
# fine concentric tool trace.  4.4 mm pitch / 28 um deep is a real finish, and
# it is what keeps a 96 mm-wide annulus from being a bald untextured face now
# that the six proud pads are gone.
TURN_PITCH = 0.0044
TURN_AMP = 0.000028


def _cover_groove(r):
    """Turned witness groove - a machined face is never one bald surface."""
    d = 0.0
    for (rg, w, dep) in COVER_GROOVES:
        t = (r - rg) / w
        if abs(t) < 1.0:
            d += dep * (1.0 - t * t) ** 0.7
    return d


def _cover_turn(r):
    return TURN_AMP * math.sin(TAU * r / TURN_PITCH)


def _cover(name, zf, coll):
    zr = _cover_face_z(zf, 0.0)
    # 4 rings per turning period - fewer and the tool trace aliases into beat
    # patterns instead of reading as a machined finish.
    step = TURN_PITCH * 0.25
    radii = [0.0560 + step * i
             for i in range(int((0.2402 - 0.0560) / step) + 1)]
    radii += [_mix(0.0942, 0.0996, i / 8.0) for i in range(9)]
    radii += [0.2380, 0.2402]
    for (rg, w, _d) in COVER_GROOVES:       # explicit samples across the groove
        radii += [rg + w * f for f in (-1.02, -0.72, -0.42, -0.16, 0.0,
                                       0.16, 0.42, 0.72, 1.02)]
    radii = sorted(set(round(v, 6) for v in radii if 0.0555 < v < 0.2405))
    face = [(r, _cover_face_z(zf, r) - _cover_groove(r) + _cover_turn(r))
            for r in radii]
    edge = _arc_pts(0.2402, zf + 0.0007, 0.0014, math.pi * 0.5, -math.pi * 0.5, 7)
    back = [(0.2380, zf - 0.0004), (0.2260, zf - 0.0004), (0.2180, zf - 0.0006),
            (0.2050, zf - 0.0030), (0.1800, zf - 0.0052), (0.1500, zf - 0.0040),
            (0.1200, zf - 0.0018), (0.1000, zf + 0.0002), (0.0800, zf + 0.0026),
            (0.0650, zf + 0.0046), (0.0575, zf + 0.0053)]
    lip = [(0.0552, zr - 0.0034), (0.0540, zr - 0.0022), (0.0535, zr - 0.0010)]
    inner_top = [(0.0540, zr - 0.0002), (0.0552, zr)]
    loop = face + list(edge)[1:] + back + lip + inner_top
    V, F = _lathe(loop, COVER_SEG, wrap_profile=True)
    return _obj(name, V, F, coll, "WheelRim", angle=24.0, merge=8e-5)


def _cover_frame(zf):
    def frame(r, th):
        d = 0.0006
        slope = (_cover_face_z(zf, r + d) - _cover_face_z(zf, r - d)) / (2.0 * d)
        L = math.hypot(1.0, slope)
        c, s = math.cos(th), math.sin(th)
        return (Vector((r * c, r * s, _cover_face_z(zf, r))),
                Vector((-slope * c / L, -slope * s / L, 1.0 / L)))
    return frame


def _cover_pads(name, zf, coll):
    """Stamped marking on the cover annulus + the valve boss.

    D-R2-04: this used to carry six 4.5 mm-proud rounded-rect pads at +/-15 deg
    covering half the annulus, which read as a six-spoke wheel face.  The brief
    asks for a broad FLAT annulus with one step to the centre boss, so the pads
    are gone; the annulus now gets its interest from the turned finish in
    _cover_turn, the marking below and the ring of cap screws.
    """
    frame = _cover_frame(zf)
    V, F = [], []
    for th, txt, rb, size, sw in ((math.radians(44.9), "13.7J X 18", 0.2135,
                                   0.0068, 0.0013),
                                  (math.radians(224.9), "FL-004", 0.2135,
                                   0.0068, 0.0013)):
        for outline in _text_strokes(txt, th, rb, size, sw):
            v, f = _extrude_outline(outline, frame, 0.00045, 0.00016)
            _add(V, F, v, f)
    boss = [(VALVE_TH + math.cos(TAU * i / 24.0) * 0.0082 / VALVE_R,
             VALVE_R + math.sin(TAU * i / 24.0) * 0.0082) for i in range(24)]
    v, f = _extrude_outline(boss, frame, 0.0022, 0.0008, planar_top=True)
    _add(V, F, v, f)
    return _obj(name, V, F, coll, "WheelRim", angle=24.0)


# --------------------------------------------------------------------------- #
# fasteners: socket head cap screws, centre-lock nut + clip, pegs, valve
# --------------------------------------------------------------------------- #

def _screw(V, F, origin, axis, t1, t2, head_r=0.0029, head_h=0.0026,
           sock_af=0.0015, sock_d=0.0017, seg=18):
    """Socket head cap screw with a real hexagon socket sunk into the head.

    seg is a multiple of 6 so the hexagon corners land on ring vertices and
    every bridge is a clean quad (no T junctions around the socket).
    """
    o, ax = Vector(origin), Vector(axis).normalized()

    def circ(rad, h):
        return [o + ax * h + t1 * (rad * math.cos(TAU * i / seg))
                + t2 * (rad * math.sin(TAU * i / seg)) for i in range(seg)]

    def hexr(af, h, shrink=1.0):
        out = []
        for i in range(seg):
            a = TAU * i / seg
            k = math.fmod(a + math.pi / 6.0, math.pi / 3.0) - math.pi / 6.0
            rad = af / math.cos(k) * shrink
            out.append(o + ax * h + t1 * (rad * math.cos(a)) + t2 * (rad * math.sin(a)))
        return out

    base = len(V)
    rings = [circ(head_r * 0.80, -0.0030), circ(head_r * 0.80, -0.0012),
             circ(head_r, -0.0006), circ(head_r, head_h - 0.0006),
             circ(head_r - 0.0005, head_h), hexr(sock_af, head_h),
             hexr(sock_af, head_h - sock_d, 0.985),
             hexr(sock_af * 0.55, head_h - sock_d - 0.0004, 0.985)]
    for r in rings:
        V.extend(tuple(p) for p in r)
    V.append(tuple(o + ax * (head_h - sock_d - 0.0006)))
    V.append(tuple(o + ax * (-0.0030)))
    apex, foot = base + 8 * seg, base + 8 * seg + 1
    for k in range(7):
        a, b = base + k * seg, base + (k + 1) * seg
        for i in range(seg):
            j = (i + 1) % seg
            F.append((a + i, a + j, b + j, b + i))
    last = base + 7 * seg
    for i in range(seg):
        F.append((last + i, apex, last + (i + 1) % seg))
        F.append((base + i, base + (i + 1) % seg, foot))


def _cover_screws(name, zf, coll):
    frame = _cover_frame(zf)
    V, F = [], []
    for k in range(12):
        th = TAU * k / 12.0 + math.radians(7.5)
        p, nrm = frame(0.2262, th)
        t1 = Vector((-math.sin(th), math.cos(th), 0.0))
        t1 = (t1 - nrm * t1.dot(nrm)).normalized()
        _screw(V, F, p, nrm, t1, nrm.cross(t1))
    return _obj(name, V, F, coll, "SteelFastener", angle=30.0)


CLIP_R = 0.0300                     # pitch radius of the retention clip
CLIP_GROOVE = 0.0019                # radius of the semicircular face groove


def _centre_lock(zf, coll, prefix):
    """Centre-lock nut, its wire retention clip and the axle stub end."""
    seat = zf - 0.0082
    objs = []

    # ---- centre-lock nut: raised drive boss, clip groove in the OUTBOARD face,
    # hex skirt.  D-R2-05: the clip used to sit in a groove turned into the SIDE
    # of the nut, between a 37.2 mm collar above it and a 39.0 mm collar below,
    # so from outboard it was completely buried and only its two bent tails
    # showed - two stray metal shards on the hex.  The groove is now a
    # semicircular channel in the face itself, at r = 30 mm, well inside the
    # 53.5 mm cover aperture, so the whole ring reads.
    z_f = seat + 0.0142                  # outboard annular face of the nut
    V, F = [], []
    face_pts = ([(0.0165, seat + 0.0002), (0.0165, seat + 0.0150),
                 (0.0173, seat + 0.0164), (0.0188, seat + 0.0170),
                 (0.0224, seat + 0.0170), (0.0248, seat + 0.0170),
                 (0.0257, seat + 0.0166), (0.0262, seat + 0.0158),
                 (0.0262, seat + 0.0148), (0.0268, seat + 0.0143),
                 (0.0276, z_f)]
                + _arc_pts(CLIP_R, z_f, CLIP_GROOVE, math.pi, TAU, 13)
                + [(0.0332, z_f), (0.0346, z_f), (0.0358, z_f)])
    skirt = [(0.0370, seat + 0.0128), (0.0378, seat + 0.0116),
             (0.0384, seat + 0.0100), (0.0390, seat + 0.0084),
             (0.0390, seat + 0.0038), (0.0404, seat + 0.0022),
             (0.0412, seat + 0.0002)]
    prof = face_pts + skirt
    # hex blends in down the skirt; the last two entries are the base ring the
    # _lathe call appends below.
    hexf = ([0.0] * len(face_pts) + [0.25, 0.5, 0.8, 1.0, 1.0, 0.6, 0.75]
            + [0.75, 0.0])

    def hexwarp(x, y, z, ip, iseg):
        f = hexf[ip]
        if f <= 0.0:
            return x, y, z
        th = TAU * iseg / 96.0
        a = math.fmod(th + math.pi / 6.0, math.pi / 3.0) - math.pi / 6.0
        s = _mix(1.0, (1.0 / math.cos(a)) * 0.985, f)
        return x * s, y * s, z

    V, F = _lathe(prof + [(0.0412, seat - 0.0016), (0.0165, seat - 0.0016)],
                  96, wrap_profile=True, warp=hexwarp)
    objs.append(_obj(prefix + "_Nut", V, F, coll, "SteelFastener",
                     angle=26.0, merge=8e-5))

    # ---- wire retention clip, half sunk in that face groove ---------------- #
    # wire_r 1.6 < CLIP_GROOVE 1.9 and the wire axis sits 0.2 mm below the face,
    # so the wire circle is strictly inside the groove circle (0.1 mm clearance,
    # no coincident faces) while 1.4 mm of it stands proud of the face.
    #
    # The two tails LIFT before they sweep out.  While the wire is directly over
    # the groove (|rr - CLIP_R| <= 0.0003) it can be at any height without
    # touching the nut, but the moment it moves outboard of the groove mouth its
    # underside has to be clear of the face - otherwise the tails saw straight
    # through it (80 overlapping triangle pairs in the first cut of this fix).
    V, F = [], []
    wire_r, ring_r = 0.0016, CLIP_R
    n_a, n_w = 144, 10
    span = math.radians(316.0)
    bend_w = 0.40                       # rad of ring given over to each tail
    for i in range(n_a):
        t = i / (n_a - 1.0)
        a = -span * 0.5 + span * t
        bend = min(1.0, max(0.0, (abs(a) - span * 0.5 + bend_w) / bend_w)) ** 1.6
        s = min(1.0, bend / 0.42)
        lift = 0.0040 * s * s * (3.0 - 2.0 * s)     # clears the face by 2.2 mm
        q = max(0.0, (bend - 0.42) / 0.58)
        rr = ring_r + 0.0055 * q ** 1.25
        cen = Vector((rr * math.cos(a), rr * math.sin(a),
                      z_f - 0.0002 + lift + 0.0014 * q))
        rad = Vector((math.cos(a), math.sin(a), 0.0))
        for j in range(n_w):
            b = TAU * j / n_w
            V.append(tuple(cen + rad * (wire_r * math.cos(b))
                           + Vector((0, 0, wire_r * math.sin(b)))))
    for i in range(n_a - 1):
        a, b = i * n_w, (i + 1) * n_w
        for j in range(n_w):
            k = (j + 1) % n_w
            F.append((a + j, a + k, b + k, b + j))
    F.append(tuple(range(n_w))[::-1])
    F.append(tuple(range((n_a - 1) * n_w, n_a * n_w)))
    objs.append(_obj(prefix + "_NutClip", V, F, coll, "SteelFastener", angle=40.0))

    # ---- axle stub end inside the nut bore -------------------------------- #
    stub = [(0.0000, seat - 0.0090), (0.0110, seat - 0.0090), (0.0140, seat - 0.0060),
            (0.0142, seat + 0.0122), (0.0130, seat + 0.0144), (0.0090, seat + 0.0150),
            (0.0000, seat + 0.0150)]
    V, F = _lathe(stub, 64, wrap_profile=False)
    objs.append(_obj(prefix + "_AxleEnd", V, F, coll, "Titanium",
                     angle=30.0, merge=8e-5))
    return objs


def _drive_pegs(name, coll):
    """Six drive pegs on the hub register, engaging the upright."""
    V, F = [], []
    seg = 30
    for k in range(6):
        th = TAU * k / 6.0 + math.radians(30.0)
        cx, cy = 0.0720 * math.cos(th), 0.0720 * math.sin(th)
        prof = [(0.0000, -0.0836), (0.0056, -0.0840), (0.0066, -0.0850),
                (0.0068, -0.0866), (0.0068, -0.1000), (0.0066, -0.1016),
                (0.0060, -0.1029), (0.0050, -0.1039), (0.0036, -0.1045),
                (0.0019, -0.1048), (0.0000, -0.1049)]
        v, f = _lathe(prof, seg, wrap_profile=False)
        _add(V, F, [(x + cx, y + cy, z) for (x, y, z) in v], f)
    ob = _obj(name, V, F, coll, "SteelFastener", angle=30.0, merge=8e-5)
    return ob


VALVE_TH = math.radians(105.0)      # in the gap between two cover pads
VALVE_R = 0.2170


def _valve(zf, coll, prefix):
    frame = _cover_frame(zf)
    p, nrm = frame(VALVE_R, VALVE_TH)
    rad = Vector((math.cos(VALVE_TH), math.sin(VALVE_TH), 0.0))
    axis = (nrm + rad * 0.46).normalized()
    t1 = axis.cross(Vector((0, 0, 1.0)))
    if t1.length < 1e-6:
        t1 = Vector((1.0, 0, 0))
    t1.normalize()
    t2 = axis.cross(t1)
    objs = []
    for (nm, mat, rings) in (
        (prefix + "_ValveStem", "SteelFastener",
         [(0.0068, -0.0030), (0.0068, 0.0010), (0.0050, 0.0018), (0.0050, 0.0042),
          (0.0042, 0.0047), (0.0042, 0.0058)]),
        (prefix + "_ValveCap", "AnodisedRed",
         [(0.0021, 0.0038), (0.0052, 0.0042), (0.0060, 0.0050), (0.0060, 0.0072),
          (0.0052, 0.0081), (0.0023, 0.0085)]),
    ):
        V, F = [], []
        seg = 24
        for (rr, hh) in rings:
            for i in range(seg):
                a = TAU * i / seg
                q = p + axis * hh + t1 * (rr * math.cos(a)) + t2 * (rr * math.sin(a))
                V.append(tuple(q))
        for ir in range(len(rings) - 1):
            a, b = ir * seg, (ir + 1) * seg
            for i in range(seg):
                j = (i + 1) % seg
                F.append((a + i, a + j, b + j, b + i))
        F.append(tuple(range(seg))[::-1])
        F.append(tuple(range((len(rings) - 1) * seg, len(rings) * seg)))
        objs.append(_obj(nm, V, F, coll, mat, angle=32.0, merge=8e-5))
    return objs


# --------------------------------------------------------------------------- #
# assembly
# --------------------------------------------------------------------------- #

def _corner(prefix, hw, coll):
    """One complete corner, authored with the axle on local +Z (+Z outboard)."""
    zf = hw - 0.010                      # rim flange outer face
    tyre, prof = _tyre_mesh(prefix + "_Tyre", hw, coll)
    k = 0.104 / (_tread_edge_z(hw) + 0.002)
    objs = [_zsquish(tyre, k),
            _zsquish(_lettering(prefix + "_Lettering", prof, hw, coll), k),
            _zsquish(_vent_pips(prefix + "_VentPips", prof, hw, coll), k),
            _rim_barrel(prefix + "_RimBarrel", zf, coll),
            _wheel_centre(prefix + "_WheelCentre", zf, coll),
            _cover(prefix + "_AeroCover", zf, coll),
            _cover_pads(prefix + "_CoverPads", zf, coll),
            _cover_screws(prefix + "_CoverScrews", zf, coll),
            _drive_pegs(prefix + "_DrivePegs", coll)]
    objs += _centre_lock(zf, coll, prefix)
    objs += _valve(zf, coll, prefix)
    return objs


def _place(ob, x, y, right):
    ob.rotation_mode = "XYZ"
    ob.location = (x, y, S.TYRE_R)
    ob.rotation_euler = (-math.pi * 0.5, 0.0, math.pi if right else 0.0)
    return ob                            # NB: never touches ob.scale


def _mirror_instances(src_objs, tag, x, y, coll):
    """Same meshes, rotated 180 deg about X so the outboard face still points
    outboard.  A proper rotation, so normals and object-space textures hold."""
    out = []
    for src in src_objs:
        name = src.name.replace("_" + tag + "_", "_" + tag[0] + "R_", 1)
        old = bpy.data.objects.get(name)
        if old is not None:
            bpy.data.objects.remove(old, do_unlink=True)
        ob = bpy.data.objects.new(name, src.data)
        coll.objects.link(ob)
        ob.scale = src.scale
        _place(ob, x, y, right=True)
        out.append(ob)
    return out


def build(coll, ctx=None):
    # WT_ONLY=FL/RL restricts the build to a single corner.  Preview-only
    # convenience: unset (the default, and what the car build uses) returns all
    # four corners.
    only = os.environ.get("WT_ONLY", "").upper()
    objs = []
    for tag, x, y, hw in (("FL", S.FRONT_AXLE, S.FRONT_TYRE_Y, S.FRONT_TYRE_HW),
                          ("RL", S.REAR_AXLE, S.REAR_TYRE_Y, S.REAR_TYRE_HW)):
        if only and only != tag:
            continue
        left = _corner("%s_%s" % (NAME, tag), hw, coll)
        for ob in left:
            _place(ob, x, y, right=False)
        objs += left
        if not only:
            objs += _mirror_instances(left, tag, x, -y, coll)
    return objs
