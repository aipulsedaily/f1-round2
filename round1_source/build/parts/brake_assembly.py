"""brake_assembly - the four brake corner assemblies.

Each corner is authored in a right-handed CORNER-LOCAL frame

    p = (fx, ax, up)      fx = +X world (forward)
                          ax = OUTBOARD along the axle
                          up = +Z world

with the origin on the hub face centre, i.e. world
(+-1.80, +-(tyre_y - S.UPRIGHT_Y_INSET), S.TYRE_R).  The right-hand corners
reuse the same authoring code with ax mirrored and the winding reversed, so no
object carries a negative scale.

Each object picks its own local frame (see `_make` / `_frame_axes`) because the
shared materials read Object coordinates and the carbon weave is a 2-D pattern
extruded along local Z: whichever surface CONTAINS local Z has no texture
gradient across it and smears into stripes.  "axle" puts local +Z on the axle,
which is what CarbonCeramic's ring grain and the flat inboard bulkhead want;
"fore" puts local +Z on car-forward; ("radial", th) puts local +Z out along the
radius at th, which is what one arc panel of the duct barrel needs - no single
rigid frame can serve a whole cylinder, which is why the barrel is laid up as
four bonded arc panels.

Preview conveniences, both off by default and irrelevant to a normal build:
    BRAKE_CORNERS=FL,RR   build only these corners
    BRAKE_SKIP=drum,scoop drop objects whose name suffix matches, so a render
                          can look straight at the internals
"""

import math
import os

import bpy
from mathutils import Matrix, Vector

import common as C
import spec as S

NAME = "brake_assembly"
TAU = math.pi * 2.0

# --------------------------------------------------------------------------- #
# principal dimensions (metres, corner-local)
# --------------------------------------------------------------------------- #

DISC_R = S.BRAKE_DISC_R            # 0.140  -> 280 mm carbon disc
DISC_T = S.BRAKE_DISC_T            # 0.032
DISC_AX = 0.055                    # disc centre plane, outboard of the hub face
PLATE_T = 0.0102                   # one friction plate
BORE_R = 0.0755                    # disc bore
SLOT_N = 12                        # drive slots in the bore
SLOT_D = 0.0042

DISC_A_OUT = DISC_AX + 0.5 * DISC_T           # 0.0710
DISC_A_IN = DISC_AX - 0.5 * DISC_T            # 0.0390
PLATE_O = (DISC_A_OUT - PLATE_T, DISC_A_OUT)  # outboard plate (ax_in, ax_out)
PLATE_I = (DISC_A_IN, DISC_A_IN + PLATE_T)    # inboard plate

CAL_TH0, CAL_TH1 = math.radians(118.0), math.radians(194.0)
CAL_AX_O = (0.090, 0.110)          # outboard caliper leg, ax span
CAL_AX_I = (0.000, 0.020)          # inboard caliper leg
PAD_T = 0.0035                     # friction thickness
PAD_BK = 0.0040                    # backing plate
PAD_GAP = 0.0004                   # running clearance disc <-> pad
PIN_R = 0.1465                     # pad retaining pin radius (clears the disc)

DRUM_R = 0.2030
MOUTH_TH = math.radians(15.0)    # exactly 6 drum cells each side of dead ahead
MOUTH_A0, MOUTH_A1 = -0.010, 0.066


# --------------------------------------------------------------------------- #
# small maths helpers
# --------------------------------------------------------------------------- #

def _cyl(r, th, ax):
    """cylindrical about the axle -> authoring (fx, ax, up)."""
    return (r * math.cos(th), ax, r * math.sin(th))


def _basis(zdir, xhint=(1.0, 0.0, 0.0)):
    z = Vector(zdir).normalized()
    x = Vector(xhint)
    x = x - z * x.dot(z)
    if x.length < 1e-7:
        x = Vector((0.0, 0.0, 1.0))
        x = x - z * x.dot(z)
    x.normalize()
    return x, z.cross(x), z


def _rrect(a, b, fil, nq=3):
    """closed CCW rounded rectangle, half extents a/b, corner radius fil."""
    f = max(1e-6, min(fil, a * 0.95, b * 0.95))
    out = []
    for (cx, cy, a0) in ((a - f, b - f, 0.0), (-(a - f), b - f, 90.0),
                         (-(a - f), -(b - f), 180.0), (a - f, -(b - f), 270.0)):
        for k in range(nq + 1):
            ang = math.radians(a0 + 90.0 * k / nq)
            out.append((cx + f * math.cos(ang), cy + f * math.sin(ang)))
    return out


def _rrect_loop(a, b, fil, nc=5, ns=7):
    """rounded rectangle sampled with the straight runs subdivided too."""
    f = max(1e-5, min(fil, a * 0.9, b * 0.9))
    quads = ((a - f, b - f, 0.0), (-(a - f), b - f, 90.0),
             (-(a - f), -(b - f), 180.0), (a - f, -(b - f), 270.0))
    pts = []
    for qi, (cx, cy, a0) in enumerate(quads):
        for k in range(nc + 1):
            ang = math.radians(a0 + 90.0 * k / nc)
            pts.append((cx + f * math.cos(ang), cy + f * math.sin(ang)))
        nx, ny, na = quads[(qi + 1) % 4]
        p0 = pts[-1]
        p1 = (nx + f * math.cos(math.radians(na)),
              ny + f * math.sin(math.radians(na)))
        for j in range(1, ns):
            t = j / ns
            pts.append((C.lerp(p0[0], p1[0], t), C.lerp(p0[1], p1[1], t)))
    return pts


def _out_normal(p, core):
    """outward normal of a rounded rect whose straight core is +-core."""
    cx = max(-core[0], min(core[0], p[0]))
    cy = max(-core[1], min(core[1], p[1]))
    dx, dy = p[0] - cx, p[1] - cy
    ln = math.hypot(dx, dy)
    if ln < 1e-9:
        return (1.0, 0.0)
    return (dx / ln, dy / ln)


def _slot_notch(th, n=SLOT_N, width=0.34, soft=0.11):
    """1 inside one of n bore drive slots, 0 outside, corners smoothed."""
    ph = (th * n / TAU) % 1.0
    d = abs(ph - 0.5)
    e0, e1 = width * 0.5, width * 0.5 + soft
    return 1.0 - C.smoothstep((d - e0) / (e1 - e0))


class _P2:
    """2-D path builder for lathe profiles, in (r, ax)."""

    def __init__(self, p):
        self.pts = [(float(p[0]), float(p[1]))]

    def line(self, p, n=1):
        a = self.pts[-1]
        for i in range(1, n + 1):
            t = i / n
            self.pts.append((C.lerp(a[0], p[0], t), C.lerp(a[1], p[1], t)))
        return self

    def arc(self, c, r, a0, a1, n=4):
        for i in range(1, n + 1):
            a = math.radians(C.lerp(a0, a1, i / n))
            self.pts.append((c[0] + r * math.cos(a), c[1] + r * math.sin(a)))
        return self


# --------------------------------------------------------------------------- #
# mesh accumulator
# --------------------------------------------------------------------------- #

class _Mesh:
    def __init__(self):
        self.v = []
        self.f = []

    def vert(self, p):
        self.v.append((float(p[0]), float(p[1]), float(p[2])))
        return len(self.v) - 1

    def ring(self, pts):
        return [self.vert(p) for p in pts]

    def face(self, idx):
        idx = tuple(idx)
        if len(idx) >= 3 and len(set(idx)) == len(idx):
            self.f.append(idx)

    def quad(self, a, b, c, d):
        """emits a quad, or the triangle left when one edge collapses."""
        idx = (a, b, c, d)
        out = [v for k, v in enumerate(idx) if v != idx[k - 1]]
        if len(out) >= 3 and len(set(out)) == len(out):
            self.f.append(tuple(out))

    def bridge(self, ra, rb, closed=True):
        n = len(ra)
        cnt = n if closed else n - 1
        for i in range(cnt):
            j = (i + 1) % n
            self.quad(ra[i], ra[j], rb[j], rb[i])

    def loft(self, rings, closed=True, cap0=False, cap1=False, wrap=False):
        for i in range(len(rings) - 1):
            self.bridge(rings[i], rings[i + 1], closed)
        if wrap:
            self.bridge(rings[-1], rings[0], closed)
            return
        if cap0:
            self.face(list(reversed(rings[0])))
        if cap1:
            self.face(list(rings[-1]))

    # -- revolve about the axle --------------------------------------------
    def lathe(self, profile, n=96, wrap=True, cap0=False, cap1=False):
        rings = []
        for (r, ax) in profile:
            rings.append([self.vert(_cyl(r, TAU * i / n, ax)) for i in range(n)])
        self.loft(rings, closed=True, cap0=cap0, cap1=cap1, wrap=wrap)
        return rings

    # -- revolve about an arbitrary axis -----------------------------------
    def spin(self, org, zdir, profile, n=24, xhint=(1.0, 0.0, 0.0),
             cap0=True, cap1=True, wrap=False):
        x, y, z = _basis(zdir, xhint)
        o = Vector(org)
        rings = []
        for (r, h) in profile:
            if r < 1e-6:
                p = self.vert(o + z * h)
                rings.append([p] * n)
            else:
                rings.append([self.vert(o + z * h
                                        + x * (r * math.cos(TAU * i / n))
                                        + y * (r * math.sin(TAU * i / n)))
                              for i in range(n)])
        self.loft(rings, closed=True, cap0=cap0, cap1=cap1, wrap=wrap)
        return rings

    # -- swept beam along a 3-D path ---------------------------------------
    def beam(self, path, sect, cap0=True, cap1=True, up=(0.0, 0.0, 1.0)):
        pts = [Vector(p) for p in path]
        n = len(pts)
        tans = []
        for i in range(n):
            if i == 0:
                t = pts[1] - pts[0]
            elif i == n - 1:
                t = pts[-1] - pts[-2]
            else:
                t = pts[i + 1] - pts[i - 1]
            tans.append(t.normalized())
        x0, y0, _z0 = _basis(tans[0], up)
        frames = [(x0, y0)]
        for i in range(1, n):
            px, py = frames[-1]
            z = tans[i]
            x = px - z * px.dot(z)
            if x.length < 1e-7:
                x = py - z * py.dot(z)
            x.normalize()
            frames.append((x, z.cross(x)))
        rings = []
        for i in range(n):
            x, y = frames[i]
            rings.append([self.vert(pts[i] + x * u + y * v)
                          for (u, v) in sect(i, i / max(1, n - 1))])
        self.loft(rings, closed=True, cap0=cap0, cap1=cap1)
        return rings

    # -- arc beam: closed (r, ax) section swept round the axle --------------
    def arc_beam(self, th0, th1, n, sect, cap0=True, cap1=True):
        rings = []
        for i in range(n + 1):
            t = i / n
            th = C.lerp(th0, th1, t)
            rings.append(self.ring([_cyl(r, th, ax) for (r, ax) in sect(t, th)]))
        self.loft(rings, closed=True, cap0=cap0, cap1=cap1)
        return rings

    # -- parametric sheet with punched holes --------------------------------
    def sheet(self, P, nu, nv, wrap_u=True, wrap_v=False, holes=None, skip=None,
              chamfer=0.0006, nsign=1.0, lip=1.32):
        """P(iu, iv) -> point. holes: {(bu, bv): radius} over 2x2 fine blocks."""
        nuv = nu if wrap_u else nu + 1
        nvv = nv if wrap_v else nv + 1
        grid = [[self.vert(P(iu, iv)) for iv in range(nvv)] for iu in range(nuv)]
        holes = dict(holes or {})
        covered = set()
        for (bu, bv) in holes:
            for du in range(2):
                for dv in range(2):
                    covered.add(((2 * bu + du) % nuv, (2 * bv + dv) % nvv))
        for iu in range(nu):
            iu2 = (iu + 1) % nuv
            for iv in range(nv):
                iv2 = (iv + 1) % nvv
                if (iu, iv) in covered:
                    continue
                if skip is not None and skip(iu, iv):
                    continue
                self.quad(grid[iu][iv], grid[iu2][iv],
                          grid[iu2][iv2], grid[iu][iv2])
        off = ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (1, 2), (0, 2), (0, 1))
        rings = {}
        for (bu, bv), spec in holes.items():
            hr, sides = spec if isinstance(spec, tuple) else (spec, 8)
            u0, v0 = 2 * bu, 2 * bv
            bidx = [grid[(u0 + du) % nuv][(v0 + dv) % nvv] for (du, dv) in off]
            ctr = Vector(self.v[grid[(u0 + 1) % nuv][(v0 + 1) % nvv]])
            pu = Vector(self.v[grid[(u0 + 2) % nuv][(v0 + 1) % nvv]]) - \
                Vector(self.v[grid[u0 % nuv][(v0 + 1) % nvv]])
            pv = Vector(self.v[grid[(u0 + 1) % nuv][(v0 + 2) % nvv]]) - \
                Vector(self.v[grid[(u0 + 1) % nuv][v0 % nvv]])
            nrm = pu.cross(pv)
            if nrm.length < 1e-12:
                continue
            nrm.normalize()
            nrm = nrm * nsign
            dirs = []
            for k in range(8):
                d = Vector(self.v[bidx[k]]) - ctr
                d = d - nrm * d.dot(nrm)
                if d.length < 1e-9:
                    d = Vector((1.0, 0.0, 0.0))
                dirs.append(d.normalized())
            if sides >= 16:
                fine = []
                for k in range(8):
                    fine.append(dirs[k])
                    mid = dirs[k] + dirs[(k + 1) % 8]
                    fine.append(mid.normalized() if mid.length > 1e-9 else dirs[k])
                dirs = fine
            n = len(dirs)
            rim = [self.vert(ctr + d * (hr * lip)) for d in dirs]
            inner = [self.vert(ctr + d * hr - nrm * chamfer) for d in dirs]
            step = n // 8
            for k in range(8):
                k2 = (k + 1) % 8
                self.quad(bidx[k], bidx[k2], rim[(k * step + 1) % n], rim[k * step])
                for j in range(1, step):
                    self.face((bidx[k2], rim[(k * step + j + 1) % n],
                               rim[(k * step + j) % n]))
            for j in range(n):
                j2 = (j + 1) % n
                self.quad(rim[j], rim[j2], inner[j2], inner[j])
            rings[(bu, bv)] = (inner, ctr, nrm)
        return grid, rings

    def blind(self, hole, depth, taper=0.90, n_ring=1):
        """close a punched hole off as a flat-bottomed drilling."""
        idx, ctr, nrm = hole
        prev = idx
        for j in range(1, n_ring + 1):
            t = j / n_ring
            ring = []
            for k in range(len(idx)):
                d = Vector(self.v[idx[k]]) - ctr
                d = d - nrm * d.dot(nrm)
                ring.append(self.vert(ctr + d * C.lerp(1.0, taper, t)
                                      - nrm * (depth * t)))
            self.bridge(prev, ring, closed=True)
            prev = ring
        self.face(list(prev))

    def through(self, ha, hb):
        """stitch two punched holes on opposite faces into one bore."""
        p8 = (6, 5, 4, 3, 2, 1, 0, 7)
        a, b = ha[0], hb[0]
        n = len(a)
        if n == 8:
            perm = p8
        else:
            perm = [0] * 16
            for k in range(8):
                perm[2 * k] = 2 * p8[k]
                perm[2 * k + 1] = 2 * p8[(k + 1) % 8] + 1
        for k in range(n):
            k2 = (k + 1) % n
            self.quad(a[k], a[k2], b[perm[k2]], b[perm[k]])


# --------------------------------------------------------------------------- #
# object creation
# --------------------------------------------------------------------------- #

def _frame_axes(frame):
    """Local (x, y, z) axes of an object frame, expressed as WORLD directions.

    The shared carbon weave is a 2-D pattern extruded along the object's local
    Z, so a surface that CONTAINS local Z has no texture gradient across it and
    smears into stripes.  Picking the frame per object is how that is avoided.
    """
    if frame == "fore":                       # local +Z = car-forward
        return (0.0, 1.0, 0.0), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0)
    if isinstance(frame, tuple):              # ("radial", th): +Z = the panel's
        th = frame[1]                         # own mean radius about the axle
        return ((0.0, 1.0, 0.0),
                (-math.sin(th), 0.0, math.cos(th)),
                (math.cos(th), 0.0, math.sin(th)))
    return (-1.0, 0.0, 0.0), (0.0, 0.0, 1.0), (0.0, 1.0, 0.0)   # "axle"


def _make(m, name, matname, hub, side, auto=32.0, smooth=True, frame="axle"):
    """frame picks the object-local axes, which is what Object-space textures
    ride on.  "axle": local +Z is the axle - CarbonCeramic's ring grain then
    runs round the disc.  "fore": local +Z is car-forward.  ("radial", th):
    local +Z points out along the radius at th, which is what one arc panel of
    the duct barrel needs for its weave to stay a weave (D_R2)."""
    ex, ey, ez = _frame_axes(frame)
    verts = []
    for p in m.v:
        w = (p[0], side * p[1], p[2])
        verts.append((w[0] * ex[0] + w[1] * ex[1] + w[2] * ex[2],
                      w[0] * ey[0] + w[1] * ey[1] + w[2] * ey[2],
                      w[0] * ez[0] + w[1] * ez[1] + w[2] * ez[2]))
    rot = Matrix(((ex[0], ey[0], ez[0]),
                  (ex[1], ey[1], ez[1]),
                  (ex[2], ey[2], ez[2]))).to_4x4()
    faces = [tuple(reversed(f)) for f in m.f] if side < 0 else list(m.f)
    ob = C.new_obj(name, verts, faces, coll=COLL, smooth=smooth, auto_smooth=auto)
    ob.matrix_world = Matrix.Translation(Vector(hub)) @ rot
    S.assign(ob, matname)
    return ob


# --------------------------------------------------------------------------- #
# 1. the disc
# --------------------------------------------------------------------------- #

def _plate_profile(ax_in, ax_out, na=20):
    """Closed cross-section of one friction plate as (base_r, notch_w, ax)."""
    r_id = BORE_R + 0.0010
    r_fo = DISC_R - 0.0022
    ch = 0.0012
    pts = []

    def nw(s):
        return 1.0 - C.smoothstep((s - 0.05) / 0.09)

    # A: outer face, bore -> OD              indices 0 .. na
    for i in range(na + 1):
        s = i / na
        pts.append((C.lerp(r_id, r_fo, s), nw(s), ax_out))
    # B: OD chamfer                          na+1, na+2
    for k in (1, 2):
        a = math.radians(90.0 * k / 2.0)
        pts.append((r_fo + (DISC_R - r_fo) * math.sin(a), 0.0,
                    ax_out - ch * (1.0 - math.cos(a))))
    # C: OD band  na+3 .. na+6.  Four cells, not six: a 2.6 mm radial hole
    # needs a block at least 2.6 mm tall, and six cells over a 7.8 mm band
    # gives blocks of 2.6 mm that the hole rim overruns.
    a0, a1 = ax_out - ch, ax_in + ch
    for k in range(1, 5):
        pts.append((DISC_R, 0.0, C.lerp(a0, a1, k / 4.0)))
    # D: OD chamfer back                     na+7, na+8
    for k in (1, 2):
        a = math.radians(90.0 * k / 2.0)
        pts.append((DISC_R - (DISC_R - r_fo) * (1.0 - math.cos(a)), 0.0,
                    ax_in + ch * (1.0 - math.sin(a))))
    # E: inner face, OD -> bore              na+11 .. 2na+10
    for i in range(1, na + 1):
        pts.append((C.lerp(r_fo, r_id, i / na), nw(i / na), ax_in))
    # F: bore band                           2na+11 .. 2na+15
    b0, b1 = ax_in + 0.0010, ax_out - 0.0010
    pts.append((BORE_R, 1.0, b0))
    for k in (1, 2, 3):
        pts.append((BORE_R, 1.0, C.lerp(b0, b1, k / 4.0)))
    pts.append((BORE_R, 1.0, b1))
    return pts


def _disc(hub, side):
    m = _Mesh()
    nu = 176
    na = 18
    for (ax_in, ax_out) in (PLATE_O, PLATE_I):
        prof = _plate_profile(ax_in, ax_out, na)
        nv = len(prof)

        def P(iu, iv, prof=prof, nv=nv):
            th = TAU * iu / nu
            base, w, ax = prof[iv % nv]
            return _cyl(base - w * SLOT_D * _slot_notch(th), th, ax)

        holes = {}
        pairs = []
        # the inner-face block mirroring outer-face block b (see the section
        # layout in _plate_profile) is na + 3 - b
        for (blk, phase, hr) in ((1, 0, 0.0020), (3, 1, 0.0022),
                                 (5, 0, 0.0024), (7, 1, 0.0024)):
            for col in range(phase, nu // 2, 2):
                holes[(col, blk)] = (hr, 16)
                holes[(col, na + 3 - blk)] = (hr, 16)
                pairs.append(((col, blk), (col, na + 3 - blk)))
        # radial drilling round the OD, staggered over the band's two blocks
        od = []
        od_blk = (na + 2) // 2
        for col in range(nu // 2):
            key = (col, od_blk + (col % 2))
            holes[key] = (0.0013, 16)
            od.append(key)

        _g, rings = m.sheet(P, nu, nv, wrap_u=True, wrap_v=True, holes=holes,
                            chamfer=0.00055, nsign=1.0, lip=1.30)
        for (a, b) in pairs:
            if a in rings and b in rings:
                m.through(rings[a], rings[b])
        for k in od:
            if k in rings:
                m.blind(rings[k], 0.010, taper=0.86, n_ring=2)
    return _make(m, f"{NAME}_{TAG}_Disc", "CarbonCeramic", hub, side, auto=26.0)


def _disc_vanes(hub, side):
    m = _Mesh()
    n = 36
    r0, r1 = 0.0812, DISC_R - 0.0016
    a0, a1 = PLATE_I[1] - 0.0010, PLATE_O[0] + 0.0010
    for i in range(n):
        th0 = TAU * i / n
        rings = []
        ns = 7
        for k in range(ns):
            t = k / (ns - 1)
            r = C.lerp(r0, r1, t)
            th = th0 + math.radians(9.0) * (t ** 1.4)
            dth = C.lerp(0.0016, 0.0011, t) / r
            sec = [_cyl(r, th + du, 0.5 * (a0 + a1) + dv)
                   for (du, dv) in _rrect(dth, 0.5 * (a1 - a0), 0.0004, nq=2)]
            rings.append(m.ring(sec))
        m.loft(rings, closed=True, cap0=True, cap1=True)
    return _make(m, f"{NAME}_{TAG}_DiscVanes", "CarbonCeramic", hub, side, auto=34.0)


# --------------------------------------------------------------------------- #
# 2. bell, hub, wheel nut
# --------------------------------------------------------------------------- #

def _bell(hub, side):
    """Disc bell, bolted to the hub's own bell flange.

    D_R2: this used to start its bore at r 0.0330 against a 0.0300 hub OD - a
    3 mm annular gap and ZERO Bell<->Hub contact - while its r 0.0440 wall and
    inner flange sat 11 mm INSIDE the non-rotating upright (597 tri pairs).  The
    disc carrier had no load path to the wheel and was mechanically attached to
    the one part that must never turn.  The whole inner end now lives outboard
    of the upright's ax=0.0300 end face, its 0.0296 bore is an interference fit
    on the 0.0300 hub shaft, and its flange face beds into the hub flange.
    """
    m = _Mesh()
    prof = (_P2((0.0296, 0.0362))
            .line((0.0472, 0.0362), 2)
            .line((0.0530, 0.0396), 1)
            .line((0.0605, 0.0448), 2)
            .line((0.0648, 0.0500), 2)
            .line((0.0680, 0.0562), 2)
            .line((0.0680, 0.0640), 2)
            .line((0.0648, 0.0684), 1)
            .line((0.0470, 0.0684), 2)
            .line((0.0440, 0.0640), 1)
            .line((0.0440, 0.0414), 3)
            .line((0.0296, 0.0414), 2))
    pts = prof.pts
    nu = 72
    nv = len(pts)

    def P(iu, iv):
        r, ax = pts[iv % nv]
        return _cyl(r, TAU * iu / nu, ax)

    # 12 bell bolts on a 74 mm PCD, drilled into the OUTBOARD face of the
    # flange (rows 18-20) so they are seen through the disc bore and land in
    # the hub flange behind them.  nsign is -1 here because this profile loop
    # runs CCW in (r, ax): with +1 the "blind drillings" were extruded the
    # wrong way and stood proud as 6 mm pegs that fouled the disc bore.
    holes = {(i * 3 + 1, 9): (0.0022, 16) for i in range(12)}
    _g, rings = m.sheet(P, nu, nv, wrap_u=True, wrap_v=True, holes=holes,
                        chamfer=0.0004, nsign=-1.0, lip=1.30)
    for k, h in rings.items():
        m.blind(h, 0.0038, taper=0.94, n_ring=1)

    # 12 drive tangs engaging the disc bore slots
    for i in range(SLOT_N):
        th = TAU * (i + 0.5) / SLOT_N
        rings2 = []
        for ax in (DISC_A_IN - 0.0030, DISC_A_OUT + 0.0030):
            sec = [_cyl(0.0648 + dv, th + du, ax)
                   for (du, dv) in _rrect(0.0040 / 0.0648, 0.0062, 0.0012, nq=2)]
            rings2.append(m.ring(sec))
        m.loft(rings2, closed=True, cap0=True, cap1=True)
    return _make(m, f"{NAME}_{TAG}_Bell", "Titanium", hub, side, auto=30.0)


def _hub(hub, side):
    m = _Mesh()
    # the flange at ax 0.0330-0.0364 is what the disc bell bolts to; it is
    # 3 mm clear of the upright's ax=0.0300 end face and 0.6 mm narrower than
    # the bell flange it carries, so no two faces are ever coincident.
    prof = (_P2((0.0180, 0.0150))
            .line((0.0300, 0.0150), 2)
            .line((0.0300, 0.0330), 1)
            .line((0.0466, 0.0330), 2)
            .line((0.0466, 0.0364), 1)
            .line((0.0300, 0.0364), 2)
            .line((0.0300, 0.0430), 1)
            .line((0.0268, 0.0462), 1)
            .line((0.0268, 0.0870), 3)
            .line((0.0300, 0.0900), 1)
            .line((0.0560, 0.0900), 3)
            .line((0.0560, 0.0962), 1)
            .line((0.0300, 0.0990), 3)
            .line((0.0300, 0.1080), 1)
            .line((0.0180, 0.1080), 2)
            .line((0.0180, 0.0150), 6))
    m.lathe(prof.pts[:-1], n=64, wrap=True)
    for i in range(6):
        th = TAU * i / 6.0 + math.radians(30.0)
        o = Vector(_cyl(0.0455, th, 0.0930))
        m.spin(o, (0.0, 1.0, 0.0),
               ((0.0000, -0.0060), (0.0072, -0.0060), (0.0072, 0.0176),
                (0.0056, 0.0196), (0.0000, 0.0196)), n=18)
    return _make(m, f"{NAME}_{TAG}_Hub", "Titanium", hub, side, auto=30.0)


def _wheel_nut(hub, side):
    m = _Mesh()
    m.spin(Vector((0.0, 0.1080, 0.0)), (0.0, 1.0, 0.0),
           ((0.0000, 0.0000), (0.0345, 0.0000), (0.0365, 0.0022),
            (0.0365, 0.0230), (0.0345, 0.0252), (0.0180, 0.0252),
            (0.0180, 0.0296), (0.0140, 0.0300), (0.0000, 0.0300)), n=48)
    for i in range(12):
        th = TAU * i / 12.0
        rings = []
        for ax in (0.1088, 0.1320):
            sec = [_cyl(0.0362 + dv, th + du, ax)
                   for (du, dv) in _rrect(0.0058 / 0.0362, 0.0026, 0.0007, nq=2)]
            rings.append(m.ring(sec))
        m.loft(rings, closed=True, cap0=True, cap1=True)
    return _make(m, f"{NAME}_{TAG}_Nut", "AnodisedRed", hub, side, auto=30.0)


# --------------------------------------------------------------------------- #
# 3. upright
# --------------------------------------------------------------------------- #

#  deg,   r,     ax,    pin axis
LUGS_FRONT = ((68.0, 0.108, -0.022, (1.0, 0.0, 0.0)),
              (112.0, 0.108, -0.022, (1.0, 0.0, 0.0)),
              (292.0, 0.103, -0.018, (1.0, 0.0, 0.0)),
              (248.0, 0.103, -0.018, (1.0, 0.0, 0.0)),
              (346.0, 0.100, -0.034, (0.0, 0.0, 1.0)))
LUGS_REAR = ((70.0, 0.108, -0.024, (1.0, 0.0, 0.0)),
             (110.0, 0.108, -0.024, (1.0, 0.0, 0.0)),
             (290.0, 0.104, -0.020, (1.0, 0.0, 0.0)),
             (250.0, 0.104, -0.020, (1.0, 0.0, 0.0)),
             (200.0, 0.100, -0.036, (0.0, 0.0, 1.0)))


def _upright(hub, side, rear):
    m = _Mesh()
    prof = (_P2((0.0310, -0.0480))
            .line((0.0560, -0.0480), 2)
            .line((0.0600, -0.0440), 1)
            .line((0.0600, 0.0090), 2)
            .line((0.0530, 0.0160), 1)
            .line((0.0530, 0.0300), 1)
            .line((0.0310, 0.0300), 2)
            .line((0.0310, -0.0480), 4))
    m.lathe(prof.pts[:-1], n=64, wrap=True)

    def arm_sect(w0, w1, h0, h1):
        def f(i, t):
            return _rrect(C.lerp(w0, w1, t), C.lerp(h0, h1, t), 0.0034, nq=3)
        return f

    for (deg, rr, ax, pin) in (LUGS_REAR if rear else LUGS_FRONT):
        th = math.radians(deg)
        base = Vector(_cyl(0.0530, th, ax + 0.004))
        tip = Vector(_cyl(rr, th, ax))
        path = [base + (tip - base) * t for t in (0.0, 0.35, 0.7, 1.0)]
        m.beam(path, arm_sect(0.0170, 0.0092, 0.0210, 0.0125), up=(0.0, 1.0, 0.0))
        axis = Vector(pin).normalized()
        for sgn in (-1.0, 1.0):
            o = tip + axis * (sgn * 0.0132)
            # closed section swept with wrap=True: cap0/cap1=False on a profile
            # whose first and last point coincide left 40 unwelded boundary
            # edges per boss (400 non-manifold edges on the upright).
            m.spin(o, axis * sgn,
                   ((0.0055, 0.0000), (0.0125, 0.0000), (0.0128, 0.0009),
                    (0.0128, 0.0044), (0.0125, 0.0053), (0.0055, 0.0053)),
                   n=20, wrap=True, xhint=(0.0, 1.0, 0.0))
        # rod-end ball + through bolt
        m.spin(tip, axis, ((0.0000, -0.0092), (0.0072, -0.0092),
                           (0.0092, -0.0060), (0.0092, 0.0060),
                           (0.0072, 0.0092), (0.0000, 0.0092)), n=20,
               xhint=(0.0, 1.0, 0.0))
        m.spin(tip - axis * 0.0230, axis,
               ((0.0000, 0.0000), (0.0092, 0.0000), (0.0096, 0.0016),
                (0.0096, 0.0044), (0.0052, 0.0058), (0.0052, 0.0402),
                (0.0096, 0.0416), (0.0096, 0.0444), (0.0092, 0.0460),
                (0.0000, 0.0460)), n=20, xhint=(0.0, 1.0, 0.0))

    # caliper mounting arms
    for th in (CAL_TH0, CAL_TH1):
        base = Vector(_cyl(0.0560, th, 0.006))
        tip = Vector(_cyl(0.1710, th, -0.006))
        path = [base + (tip - base) * t for t in (0.0, 0.3, 0.62, 0.86, 1.0)]
        m.beam(path, arm_sect(0.0150, 0.0105, 0.0230, 0.0150), up=(0.0, 1.0, 0.0))
        m.spin(tip, (0.0, 1.0, 0.0),
               ((0.0000, -0.0020), (0.0132, -0.0020), (0.0136, -0.0008),
                (0.0136, 0.0058), (0.0000, 0.0058)), n=20)
    return _make(m, f"{NAME}_{TAG}_Upright", "Titanium", hub, side, auto=32.0)


# --------------------------------------------------------------------------- #
# 4. caliper, pistons, pads
# --------------------------------------------------------------------------- #

PISTON_TH = (math.radians(131.0), math.radians(156.0), math.radians(181.0))
PISTON_R = 0.1180
PISTON_RAD = (0.0150, 0.0165, 0.0150)
BRIDGE_TH = (CAL_TH0 + math.radians(3.5), math.radians(156.0),
             CAL_TH1 - math.radians(3.5))


def _boss(th):
    v = 0.0
    for pt in PISTON_TH:
        d = (th - pt) / math.radians(13.0)
        v = max(v, math.exp(-d * d * 2.2))
    return v


def _caliper(hub, side):
    m = _Mesh()
    n_th = 76
    for (a_lo, a_hi) in (CAL_AX_O, CAL_AX_I):
        outboard = a_lo > 0.05

        def sect(t, th, a_lo=a_lo, a_hi=a_hi, outboard=outboard):
            b = _boss(th)
            end = min(1.0, min(t, 1.0 - t) / 0.06)
            r_lo = C.lerp(0.1105, 0.0955, b) + 0.010 * (1.0 - end)
            r_hi = C.lerp(0.1755, 0.1865, max(b, 1.0 - end))
            rc, rh = 0.5 * (r_lo + r_hi), 0.5 * (r_hi - r_lo)
            thick = 0.5 * (a_hi - a_lo) + 0.0026 * b
            ac = 0.5 * (a_lo + a_hi) + (0.0026 * b if outboard else -0.0026 * b)
            return [(rc + du, ac + dv)
                    for (du, dv) in _rrect(rh, thick, 0.0035, nq=3)]

        m.arc_beam(CAL_TH0, CAL_TH1, n_th, sect)

    # three bridges over the disc, with a machined channel down the crown so
    # they do not read as plain slabs
    for (thb, wid) in zip(BRIDGE_TH, (math.radians(4.6), math.radians(4.0),
                                      math.radians(4.6))):
        h = 0.0088
        sec2 = ((-wid, -h + 0.0016), (-wid + 0.0016 / 0.18, -h),
                (wid - 0.0016 / 0.18, -h), (wid, -h + 0.0016),
                (wid, h - 0.0030), (wid - 0.0022 / 0.18, h),
                (wid * 0.42, h), (wid * 0.34, h - 0.0026),
                (-wid * 0.34, h - 0.0026), (-wid * 0.42, h),
                (-wid + 0.0022 / 0.18, h), (-wid, h - 0.0030))
        rings = []
        for ax in (CAL_AX_I[0] - 0.0006, CAL_AX_O[1] + 0.0006):
            rings.append(m.ring([_cyl(0.1790 + dv, thb + du, ax)
                                 for (du, dv) in sec2]))
        m.loft(rings, closed=True, cap0=True, cap1=True)

    # piston bosses: seated on the leg's *bulged* outer face so they stand
    # proud as full circles instead of being sliced into crescents
    for k, th in enumerate(PISTON_TH):
        pr = PISTON_RAD[k]
        for (a, sgn) in ((CAL_AX_O[1] + 0.0052, 1.0), (CAL_AX_I[0] - 0.0052, -1.0)):
            o = Vector(_cyl(PISTON_R, th, a))
            m.spin(o, (0.0, sgn, 0.0),
                   ((0.0000, -0.0070), (pr + 0.0062, -0.0070),
                    (pr + 0.0062, 0.0030), (pr + 0.0044, 0.0050),
                    (pr - 0.0030, 0.0050), (pr - 0.0044, 0.0034),
                    (0.0000, 0.0034)), n=32)
            # bore end plug with a hex socket recess
            m.spin(o, (0.0, sgn, 0.0),
                   ((0.0000, 0.0026), (pr - 0.0064, 0.0026),
                    (pr - 0.0064, 0.0044), (pr - 0.0082, 0.0056),
                    (0.0038, 0.0056), (0.0034, 0.0040), (0.0000, 0.0040)), n=24)
    # radial machining ribs in the scallops between the bosses
    for th in (math.radians(143.5), math.radians(168.5)):
        for (a, sgn) in ((CAL_AX_O[1], 1.0), (CAL_AX_I[0], -1.0)):
            rings = []
            for i in range(5):
                t = i / 4.0
                r = C.lerp(0.1130, 0.1720, t)
                hh = 0.0030 * math.sin(math.pi * min(1.0, 0.15 + 0.85 * t))
                sec = [_cyl(r, th + du, a + sgn * (dv + hh - 0.0026))
                       for (du, dv) in _rrect(0.0042 / r, 0.0030, 0.0009, nq=2)]
                rings.append(m.ring(sec))
            m.loft(rings, closed=True, cap0=True, cap1=True)
    # bleed nipples
    for (a, sgn) in ((CAL_AX_O[1], 1.0), (CAL_AX_I[0], -1.0)):
        o = Vector(_cyl(0.1700, CAL_TH1 - math.radians(8.0), a))
        m.spin(o, (0.0, sgn, 0.0),
               ((0.0000, -0.0010), (0.0058, -0.0010), (0.0058, 0.0060),
                (0.0034, 0.0068), (0.0034, 0.0126), (0.0024, 0.0138),
                (0.0000, 0.0138)), n=14)
    # mounting ears reaching inboard onto the upright arms
    for th in (CAL_TH0, CAL_TH1):
        rings = []
        for ax in (-0.0062, CAL_AX_I[0] + 0.0080):
            sec = [_cyl(0.1710 + dv, th + du, ax)
                   for (du, dv) in _rrect(math.radians(5.2), 0.0136, 0.0030, nq=3)]
            rings.append(m.ring(sec))
        m.loft(rings, closed=True, cap0=True, cap1=True)
        m.spin(Vector(_cyl(0.1710, th, -0.0062)), (0.0, -1.0, 0.0),
               ((0.0000, -0.0012), (0.0088, -0.0012), (0.0092, 0.0000),
                (0.0092, 0.0056), (0.0088, 0.0068), (0.0000, 0.0068)), n=14)
    return _make(m, f"{NAME}_{TAG}_Caliper", "WheelRim", hub, side, auto=30.0)


def _pistons(hub, side):
    m = _Mesh()
    pad_o = PLATE_O[1] + PAD_GAP + PAD_T + PAD_BK
    pad_i = PLATE_I[0] - PAD_GAP - PAD_T - PAD_BK
    for k, th in enumerate(PISTON_TH):
        pr = PISTON_RAD[k]
        for (a_body, a_pad, sgn) in ((CAL_AX_O[0], pad_o, 1.0),
                                     (CAL_AX_I[1], pad_i, -1.0)):
            o = Vector(_cyl(PISTON_R, th, a_body))
            h = abs(a_body - a_pad) - 0.0003
            m.spin(o, (0.0, -sgn, 0.0),
                   ((0.0000, -0.0070), (pr, -0.0070), (pr, h - 0.0018),
                    (pr - 0.0018, h), (0.0000, h)), n=26)
            # dust seal: a closed ring section, not an open ribbon (the open
            # version left 52 boundary edges per piston)
            m.spin(o, (0.0, -sgn, 0.0),
                   ((pr + 0.0003, 0.0008), (pr + 0.0019, 0.0019),
                    (pr + 0.0019, 0.0034), (pr + 0.0003, 0.0045)),
                   n=26, wrap=True)
    return _make(m, f"{NAME}_{TAG}_Pistons", "SteelFastener", hub, side, auto=30.0)


def _pads(hub, side):
    mb, mf = _Mesh(), _Mesh()
    t0 = CAL_TH0 - math.radians(2.5)
    t1 = CAL_TH1 + math.radians(2.5)
    n = 34
    faces = ((PLATE_O[1] + PAD_GAP + PAD_T, PLATE_O[1] + PAD_GAP + PAD_T + PAD_BK, 1.0),
             (PLATE_I[0] - PAD_GAP - PAD_T - PAD_BK, PLATE_I[0] - PAD_GAP - PAD_T, -1.0))
    for (a0, a1, sgn) in faces:
        # the disc-facing side carries the full footprint, the piston side is
        # rebated - a plain slab reads as white plastic under a hard key light
        ad, ap = (a0, a1) if sgn > 0 else (a1, a0)
        st = 0.0009 * (1.0 if ap > ad else -1.0)

        def bsect(t, th, ad=ad, ap=ap, st=st):
            end = min(1.0, min(t, 1.0 - t) / 0.05)
            rlo = 0.0955 + 0.004 * (1.0 - end)
            rhi = 0.1375 - 0.003 * (1.0 - end)
            reb = 0.0042
            m1 = ad + st * 1.6
            m2 = ad + st * 2.6
            return [(rlo + 0.0006, ad), (rhi - 0.0006, ad),
                    (rhi, ad + st * 0.7), (rhi, m1), (rhi - reb, m2),
                    (rhi - reb, ap - st * 0.7), (rhi - reb - 0.0008, ap),
                    (rlo + reb + 0.0008, ap), (rlo + reb, ap - st * 0.7),
                    (rlo + reb, m2), (rlo, m1), (rlo, ad + st * 0.7)]
        mb.arc_beam(t0, t1, n, bsect)
        for th in (t0 + math.radians(4.6), t1 - math.radians(4.6)):
            rings = []
            for ax in (min(a0, a1) + 0.0004, max(a0, a1) - 0.0004):
                sec = [_cyl(PIN_R + dv, th + du, ax)
                       for (du, dv) in _rrect(math.radians(3.1), 0.0088, 0.0022, nq=3)]
                rings.append(mb.ring(sec))
            mb.loft(rings, closed=True, cap0=True, cap1=True)
        # D_R2 (critical): `a1` put the INBOARD friction block at 0.0316-0.0351,
        # i.e. wholly inside its own backing plate (0.0311-0.0351) - that pad had
        # no lining at all, its bare steel faced the disc 3.9 mm away, and the two
        # +ax faces were exactly coplanar so MatteBlack and SteelFastener
        # z-fought across the whole 66 cm2 face.  The friction block has to sit
        # OUTBOARD of the inboard backing plate, mirroring the outboard pad:
        # both then leave exactly PAD_GAP to their disc face.
        fa = (a0 - PAD_T) if sgn > 0 else (a1 + PAD_T)

        def fsect(t, th, fa=fa, sgn=sgn):
            end = min(1.0, min(t, 1.0 - t) / 0.05)
            rlo = 0.0968 + 0.005 * (1.0 - end)
            rhi = 0.1368 - 0.004 * (1.0 - end)
            return [(0.5 * (rlo + rhi) + du, fa + sgn * 0.5 * PAD_T + dv)
                    for (du, dv) in _rrect(0.5 * (rhi - rlo), 0.5 * PAD_T,
                                           0.0008, nq=2)]
        # split into two blocks so the pad carries a real relief slot
        gap = math.radians(1.6)
        tm = 0.5 * (t0 + t1)
        mf.arc_beam(t0, tm - gap, n // 2, fsect)
        mf.arc_beam(tm + gap, t1, n // 2, fsect)
    for th in (t0 + math.radians(4.6), t1 - math.radians(4.6)):
        mb.spin(Vector(_cyl(PIN_R, th, CAL_AX_I[0] - 0.008)), (0.0, 1.0, 0.0),
                ((0.0000, 0.0000), (0.0032, 0.0000), (0.0032, 0.1225),
                 (0.0062, 0.1225), (0.0062, 0.1258), (0.0000, 0.1258)), n=16)
    # Anti-rattle pad spring: a bowed leaf trapped over the radially outer edge
    # of each backing plate.  D_R2: the old version fed an (angular, radial)
    # section into a circumferential sweep, so du was the sweep direction - the
    # "leaf" was a 12 mm radial fin of ZERO axial thickness swept along its own
    # 2.8 mm width, and being at r 0.121-0.133 it cut clean through all six
    # pistons (593 tri pairs).  du is now the radial half-THICKNESS and dv the
    # axial half-width, and the leaf rides at r 0.1371-0.1417: outside the
    # pistons' reach (max r 0.1345) and inside the retaining pins (r 0.1433),
    # touching the pad's own 0.1375 rim at both ends where it is clipped on.
    for (a0, a1, sgn) in faces:
        ad = a0 if sgn > 0 else a1
        st = 0.0009 * sgn
        rings = []
        ns = 30
        for i in range(ns + 1):
            t = i / ns
            th = C.lerp(t0 + math.radians(9.0), t1 - math.radians(9.0), t)
            u = min(1.0, max(0.0, (t - 0.06) / 0.88))
            lift = 0.0034 * math.sin(math.pi * u) ** 0.55
            rings.append(mb.ring([
                _cyl(0.1378 + lift + du, th, ad + st * 1.15 + dv)
                for (du, dv) in _rrect(0.0006, 0.0022, 0.0004, nq=2)]))
        mb.loft(rings, closed=True, cap0=True, cap1=True)
    return (_make(mb, f"{NAME}_{TAG}_PadPlate", "SteelFastener", hub, side, auto=30.0),
            _make(mf, f"{NAME}_{TAG}_PadFriction", "MatteBlack", hub, side, auto=30.0))


def _heat_shield(hub, side):
    m = _Mesh()
    r_sh = 0.1893

    def sect(t, th):
        # D_R2: the ends used to be "curled down over the caliper" by dropping
        # 15 mm of radius - but the caliper's arc_beam flares back OUT to
        # r_hi = 0.1865 at exactly those angles and the upright's caliper-arm
        # boss reaches 0.1846, so the curl drove the foil straight through both
        # (182 Upright + end-of-caliper tri pairs).  Nothing may go below the
        # 0.1880 inner skin.  Taper the ends in WIDTH instead - it reads as a
        # wrapped foil end and cannot foul anything - and lift them a whisker.
        e = C.smoothstep((abs(t - 0.5) * 2.0 - 0.74) / 0.26)
        return [(r_sh + 0.0008 * e + dv, 0.0550 + du)
                for (du, dv) in _rrect(0.0645 - 0.0210 * e, 0.0013, 0.0011, nq=3)]

    m.arc_beam(CAL_TH0 - math.radians(5.0), CAL_TH1 + math.radians(5.0), 48, sect)
    # Standoff tabs down onto the caliper bridges.  They start at 0.1856, not
    # 0.1770: the upright's caliper-arm end boss reaches r 0.1846 at ax
    # -0.008..0.000 and the old tabs speared it (66 tri pairs).  0.1856 still
    # bites 2.2 mm into the bridge crown at 0.1878, which is the joint.
    for thb in BRIDGE_TH:
        for ax in (-0.0028, 0.1128):
            rings = []
            for r in (0.1856, r_sh + 0.0010):
                sec = [_cyl(r, thb + du, ax + dv)
                       for (du, dv) in _rrect(math.radians(2.4), 0.0050, 0.0008, nq=2)]
                rings.append(m.ring(sec))
            m.loft(rings, closed=True, cap0=True, cap1=True)
        # rivet through each tab
        for ax in (-0.0028, 0.1128):
            m.spin(Vector(_cyl(r_sh + 0.0004, thb, ax)),
                   Vector(_cyl(1.0, thb, 0.0)),
                   ((0.0000, 0.0000), (0.0022, 0.0000), (0.0024, 0.0005),
                    (0.0024, 0.0014), (0.0016, 0.0020), (0.0000, 0.0020)),
                   n=10, xhint=(0.0, 1.0, 0.0))
    return _make(m, f"{NAME}_{TAG}_Shield", "AnodisedGold", hub, side, auto=40.0)


# --------------------------------------------------------------------------- #
# 5. brake line
# --------------------------------------------------------------------------- #

def _hose(m, path, r0, n=40, braid=0.00040, pitch=0.0115, nb=9, samples=88):
    # D_R2: n=24 around nb=9 braid lobes is 2.7 samples per lobe, so the
    # displaced braid aliased into a knotted, lumpy rope with an irregular
    # silhouette.  n >= 4*nb is the floor for a stainless braid to read as one.
    pts = C.catmull_rom([tuple(p) for p in path], samples)
    P = [Vector(p) for p in pts]
    tans = []
    for i in range(len(P)):
        if i == 0:
            t = P[1] - P[0]
        elif i == len(P) - 1:
            t = P[-1] - P[-2]
        else:
            t = P[i + 1] - P[i - 1]
        tans.append(t.normalized())
    x, y, _z = _basis(tans[0], (0.0, 1.0, 0.0))
    frames = [(x, y)]
    s = [0.0]
    for i in range(1, len(P)):
        px, py = frames[-1]
        z = tans[i]
        xx = px - z * px.dot(z)
        if xx.length < 1e-7:
            xx = py - z * py.dot(z)
        xx.normalize()
        frames.append((xx, z.cross(xx)))
        s.append(s[-1] + (P[i] - P[i - 1]).length)
    rings = []
    for i in range(len(P)):
        xx, yy = frames[i]
        ring = []
        for k in range(n):
            a = TAU * k / n
            ph = TAU * s[i] / pitch
            f = max(math.cos(nb * a + ph), math.cos(nb * a - ph))
            r = r0 + braid * f
            if i < 2 or i > len(P) - 3:
                r = r0
            ring.append(m.vert(P[i] + xx * (r * math.cos(a))
                               + yy * (r * math.sin(a))))
        rings.append(ring)
    m.loft(rings, closed=True, cap0=True, cap1=True)


def _crimp(m, ctr, zdir, r, l0, l1, flats=12):
    x, y, z = _basis(zdir, (0.0, 1.0, 0.0))
    o = Vector(ctr)
    rings = []
    for (rr, h) in ((r * 0.80, l0), (r, l0 + 0.0018), (r, l1 - 0.0018),
                    (r * 0.80, l1)):
        ring = []
        for i in range(flats * 3):
            a = TAU * i / (flats * 3)
            k = rr * (1.0 - 0.06 * (0.5 + 0.5 * math.cos(flats * a)))
            ring.append(m.vert(o + z * h + x * (k * math.cos(a))
                               + y * (k * math.sin(a))))
        rings.append(ring)
    m.loft(rings, closed=True, cap0=True, cap1=True)


def _brake_line(hub, side, rear):
    m, mf = _Mesh(), _Mesh()
    pts, ax0, _ax1 = _drum_profile(rear)
    # D_R2: the banjo used to sit at 156 deg, dead under the middle heat-shield
    # standoff tab, which speared it (26 tri pairs).  175 deg is clear of all
    # three tabs, of both machining ribs and of the bleed nipple.
    thb = math.radians(175.0)
    p0 = Vector(_cyl(0.1690, thb, -0.0105))
    p1 = Vector(_cyl(0.1600, thb + math.radians(13.0), -0.0330))
    p2 = Vector(_cyl(0.1400, math.radians(194.0), -0.0600))
    # D_R2: the hose used to cross the inboard bulkhead through solid carbon at
    # ~190 deg / r 0.125 (143 tri pairs) while its dedicated pass-through slot
    # sat empty beside it.  Aim it AT the slot: after cell quantisation the hole
    # is th 197.5-210.0 deg, r 0.090-0.130, so cross it at 204.5 deg / r 0.105.
    ax_b = _bulk_ax(pts, 0.1080)[0]
    p3 = Vector(_cyl(0.1080, math.radians(204.0), ax_b + 0.0140))
    p4 = Vector(_cyl(0.0990, math.radians(206.0), ax_b - 0.0320))
    _hose(m, (p0, p1, p2, p3, p4), 0.0038)
    _crimp(mf, p0, (p1 - p0).normalized(), 0.0064, -0.0030, 0.0180)
    _crimp(mf, p4, (p4 - p3).normalized(), 0.0064, -0.0200, 0.0010)
    # banjo body on the inboard caliper leg
    mf.spin(Vector(_cyl(0.1690, thb, 0.0010)), (0.0, -1.0, 0.0),
            ((0.0000, -0.0050), (0.0106, -0.0050), (0.0106, 0.0062),
             (0.0074, 0.0062), (0.0074, 0.0116), (0.0000, 0.0116)), n=18)
    # crossover pipe, tucked between the caliper crown and the heat shield
    # (r 0.1875 max against the shield's inner skin at 0.1880)
    q0 = Vector(_cyl(0.1815, math.radians(142.0), CAL_AX_I[0] + 0.004))
    q1 = Vector(_cyl(0.1845, math.radians(142.0), 0.0550))
    q2 = Vector(_cyl(0.1815, math.radians(142.0), CAL_AX_O[1] - 0.004))
    _hose(m, (q0, q1, q2), 0.0030, n=36, braid=0.00028, pitch=0.0085, samples=44)
    for (pp, dd) in ((q0, (0.0, -1.0, 0.0)), (q2, (0.0, 1.0, 0.0))):
        mf.spin(Vector(pp), dd,
                ((0.0000, -0.0110), (0.0056, -0.0110), (0.0056, -0.0026),
                 (0.0042, -0.0016), (0.0042, 0.0044), (0.0000, 0.0044)), n=16)
    return (_make(m, f"{NAME}_{TAG}_Line", "SteelFastener", hub, side, auto=44.0),
            _make(mf, f"{NAME}_{TAG}_LineFittings", "AnodisedRed", hub, side, auto=30.0))


# --------------------------------------------------------------------------- #
# 6. drum / duct enclosure
# --------------------------------------------------------------------------- #

OUT_SLOTS = tuple((math.radians(128.0 + k * 20.0 - 6.0),
                   math.radians(128.0 + k * 20.0 + 6.0)) for k in range(4))
OUT_AX = (0.006, 0.076)
def _bulk_slots(lugs):
    """pass-throughs in the inboard bulkhead, lined up with the upright's own
    wishbone pickups so a leg can actually reach them."""
    out = []
    for (deg, rr, _ax, _pin) in lugs:
        out.append((math.radians(deg - 10.0), math.radians(deg + 10.0),
                    0.086, 0.150))
    out.append((math.radians(198.0), math.radians(211.0), 0.086, 0.122))
    return tuple(out)


BULK_SLOTS_F = _bulk_slots(LUGS_FRONT)
BULK_SLOTS_R = _bulk_slots(LUGS_REAR)


def _drum_profile(rear):
    ax0 = -0.115 if rear else -0.085
    ax1 = 0.165 if rear else 0.145
    R = DRUM_R
    p = (_P2((0.0660, ax0 + 0.0140))
         .line((0.0900, ax0 + 0.0080), 1)
         .line((0.1300, ax0 + 0.0020), 2)
         .line((0.1860, ax0), 2)
         .arc((0.1860, ax0 + 0.0170), 0.0170, -90.0, 0.0, 4)
         .line((R, ax0 + 0.0470), 2)
         .line((R + 0.0035, ax0 + 0.0530), 1)
         .line((R + 0.0035, ax0 + 0.0700), 1)
         .line((R, ax0 + 0.0760), 1)
         .line((R, ax1 - 0.0620), 6)
         .line((R + 0.0028, ax1 - 0.0560), 1)
         .line((R + 0.0028, ax1 - 0.0230), 2)
         .line((R, ax1 - 0.0170), 1)
         .line((R, ax1 - 0.0060), 1)
         .arc((0.1955, ax1 - 0.0060), 0.0075, 0.0, 90.0, 3)
         .line((0.1880, ax1 - 0.0020), 1)
         .line((0.1855, ax1 - 0.0130), 1))
    return p.pts, ax0, ax1


def _bulge(th, r, ax, amp=0.0060):
    """gentle swelling of the barrel around the inlet, so the bolt-on scoop
    fairs into the drum instead of standing on a bare cylinder."""
    if r < DRUM_R - 0.010:
        return 0.0
    dth = math.atan2(math.sin(th), math.cos(th))
    if abs(dth) > math.radians(52.0):
        return 0.0
    da = max(abs(dth) * DRUM_R - MOUTH_TH * DRUM_R, 0.0)
    db = 0.0
    if ax < MOUTH_A0:
        db = MOUTH_A0 - ax
    elif ax > MOUTH_A1:
        db = ax - MOUTH_A1
    return amp * math.exp(-(math.hypot(da, db) / 0.034) ** 2)


def _ribs(th, r, ax, ax0, ax1):
    """raised circumferential stiffening beads, faded out where the bonded
    inlet scoop sits so a bead never runs under the scoop flange."""
    if r < DRUM_R - 0.004:
        return 0.0
    dth = abs(math.atan2(math.sin(th), math.cos(th)))
    fade = C.smoothstep((dth - math.radians(26.0)) / math.radians(16.0))
    if fade <= 0.001:
        return 0.0
    v = 0.0
    for a in (ax0 + 0.098, ax1 - 0.086):
        d = (ax - a) / 0.0034
        v = max(v, 0.0017 * math.exp(-d * d))
    return v * fade


DRUM_NU = 144
IV_JOINT = 7           # profile index where the bulkhead panel laps the barrel
SHELL_T = 0.0032

# The barrel is laid up as BARREL_SEG bonded arc panels rather than one tube.
# D_R2: the weave is a 2-D pattern extruded along the object's local Z, so on a
# full cylinder about the axle there is no rigid frame that keeps it a weave -
# with local Z along car-forward the top and bottom flanks contained Z and
# rendered as fine parallel corduroy, and that barrel is the biggest surface in
# the part.  One frame per panel, each with local Z along its own mean radius,
# fixes it.  Panels overlap by BARREL_LAP columns; the trailing panel laps OVER
# the next, whose leading edge tucks BARREL_TUCK under it, so no two skins are
# ever coincident.
BARREL_SEG = 4
BARREL_LAP = 3
BARREL_TUCK = 0.0008


def _barrel_r(pts, ax):
    """Authored barrel radius at an axial station.

    The shell offsets SHELL_T OUTWARD from this, so anything bonded to the
    outside of the drum has to be seated on _barrel_r(...) + SHELL_T or it is
    swallowed by the skin (measured: skin outer = authored + 0.0032 exactly).
    """
    best = None
    for i in range(len(pts) - 1):
        (r0, a0), (r1, a1) = pts[i], pts[i + 1]
        if r0 < DRUM_R - 0.004 or r1 < DRUM_R - 0.004:
            continue
        if min(a0, a1) - 1e-9 <= ax <= max(a0, a1) + 1e-9:
            t = 0.0 if abs(a1 - a0) < 1e-9 else (ax - a0) / (a1 - a0)
            v = C.lerp(r0, r1, t)
            best = v if best is None else max(best, v)
    return DRUM_R if best is None else best


def _bulk_ax(pts, r):
    """(authored ax, outer-skin ax) of the inboard bulkhead at radius r.

    The bulkhead is a shallow cone, so its skin is SHELL_T along the profile
    NORMAL, not along the axle: at r 0.0790 that is 3.3 mm of ax, not 3.2.
    Getting this wrong is what buried the inner rivet ring completely.
    """
    for i in range(IV_JOINT + 2):
        (r0, a0), (r1, a1) = pts[i], pts[i + 1]
        if r1 > r0 and r0 - 1e-9 <= r <= r1 + 1e-9:
            t = (r - r0) / (r1 - r0)
            ax = C.lerp(a0, a1, t)
            return ax, ax - SHELL_T * math.hypot(r1 - r0, a1 - a0) / (r1 - r0)
    return pts[0][1], pts[0][1] - SHELL_T


def _prof_normal(pts, i):
    """outward unit normal of the (r, ax) profile at sample i."""
    a = pts[max(0, i - 1)]
    b = pts[min(len(pts) - 1, i + 1)]
    tr, ta = b[0] - a[0], b[1] - a[1]
    ln = math.hypot(tr, ta) or 1.0
    return (ta / ln, -tr / ln)


def _drum_panel(hub, side, rear, iv0, iv1, tag, frame, lap=False, useg=None):
    """One bonded panel of the duct enclosure.

    The barrel, its four arc panels and the inboard bulkhead are separate
    objects on purpose: the shared carbon weave is a 2-D pattern extruded along
    the object's local Z, so one frame cannot serve a cylinder about the axle
    and a disc normal to it at once - whichever surface contains local Z smears
    into stripes.  Splitting at real lap joints lets each panel take the frame
    that suits it.  `useg` = (first column, column count, lap columns).
    """
    m = _Mesh()
    pts, ax0, ax1 = _drum_profile(rear)
    nvp = iv1 - iv0
    iu0, nus, nlap = (0, DRUM_NU, 0) if useg is None else useg

    def P(iu, iv):
        g = iv0 + iv
        th = TAU * (iu0 + iu) / DRUM_NU
        r, ax = pts[g]
        r += _bulge(th, r, ax) + _ribs(th, r, ax, ax0, ax1)
        if nlap and iu < 2 * nlap:
            # tuck under the neighbour, ramping out over twice the overlap so
            # the two skins never come within 0.4 mm of coincident inside it
            r -= BARREL_TUCK * (1.0 - iu / (2.0 * nlap))
        if lap:
            # tuck the barrel's inboard end one skin under the bulkhead flange
            f = 0.0
            if g <= IV_JOINT + 2:
                f = 1.0
            elif g <= IV_JOINT + 5:
                f = (IV_JOINT + 5 - g) / 3.0
            if f > 0.0:
                # 0.5 mm bond line: the bulkhead's skin laps outside the
                # barrel's here, and coincident faces would z-fight
                nr, nax = _prof_normal(pts, g)
                r -= nr * 0.0005 * f
                ax -= nax * 0.0005 * f
        return _cyl(r, th, ax)

    nv_all = len(pts) - 1
    iv_mouth = [i for i in range(nv_all) if pts[i][0] > DRUM_R - 0.004
                and MOUTH_A0 <= 0.5 * (pts[i][1] + pts[i + 1][1]) <= MOUTH_A1]
    iv_out = [i for i in range(nv_all) if pts[i][0] > DRUM_R - 0.004
              and OUT_AX[0] <= 0.5 * (pts[i][1] + pts[i + 1][1]) <= OUT_AX[1]]
    iv_bulk = [i for i in range(nv_all) if pts[i][1] < ax0 + 0.010]
    slots = BULK_SLOTS_R if rear else BULK_SLOTS_F

    def skip(iu, iv):
        g = iv0 + iv
        th = (TAU * (iu0 + iu + 0.5) / DRUM_NU) % TAU
        thn = math.atan2(math.sin(th), math.cos(th))
        if g in iv_mouth and abs(thn) <= MOUTH_TH:
            return True
        if g in iv_out:
            for (a, b) in OUT_SLOTS:
                if a <= th <= b:
                    return True
        if g in iv_bulk:
            rm = 0.5 * (pts[g][0] + pts[g + 1][0])
            for (a, b, r0, r1) in slots:
                if a <= th <= b and r0 <= rm <= r1:
                    return True
        return False

    m.sheet(P, nus, nvp, wrap_u=(useg is None), skip=skip, nsign=-1.0)
    ob = _make(m, f"{NAME}_{TAG}_{tag}", "CarbonMatte", hub, side, auto=34.0,
               frame=frame)
    sol = ob.modifiers.new("Shell", "SOLIDIFY")
    sol.thickness = SHELL_T
    sol.offset = 1.0
    sol.use_even_offset = True
    sol.use_rim = True
    C.add_bevel(ob, width=0.0008, segments=2, angle=34.0)
    return ob


def _drum(hub, side, rear):
    """The barrel, as BARREL_SEG bonded arc panels (see BARREL_SEG above)."""
    pts, _a0, _a1 = _drum_profile(rear)
    span = DRUM_NU // BARREL_SEG
    out = []
    for k in range(BARREL_SEG):
        iu0 = k * span - span // 2
        th_c = TAU * (iu0 + 0.5 * span) / DRUM_NU
        out.append(_drum_panel(hub, side, rear, IV_JOINT, len(pts) - 1,
                               "Drum" if k == 0 else f"Drum{k}",
                               ("radial", th_c), lap=True,
                               useg=(iu0, span + BARREL_LAP, BARREL_LAP)))
    return out


def _drum_bulk(hub, side, rear):
    return _drum_panel(hub, side, rear, 0, IV_JOINT + 2, "DrumBulk", "axle")


def _mouth_bounds(rear):
    """the ax range the mouth cut actually lands on, in profile points."""
    pts, ax0, ax1 = _drum_profile(rear)
    nv = len(pts) - 1
    ivs = [i for i in range(nv) if pts[i][0] > DRUM_R - 0.004
           and MOUTH_A0 <= 0.5 * (pts[i][1] + pts[i + 1][1]) <= MOUTH_A1]
    return pts[ivs[0]][1], pts[ivs[-1] + 1][1]


def _scoop(hub, side, rear):
    """The bolt-on inlet scoop: a raised collar round the mouth with a rolled
    lip, plus its bonding flange and rivets."""
    m = _Mesh()
    a_lo, a_hi = _mouth_bounds(rear)
    am, ah = 0.5 * (a_lo + a_hi), 0.5 * (a_hi - a_lo)
    sh = MOUTH_TH * DRUM_R          # half width of the mouth as arc length
    fil = 0.0130
    pts, _a0, _a1 = _drum_profile(rear)
    per = _rrect_loop(sh + 0.0040, ah + 0.0040, fil, nc=5, ns=7)
    core = (sh + 0.0040 - fil, ah + 0.0040 - fil)
    # Cross-section of the collar in (outward-in-plane, radial), with w = 0 on
    # the OUTER skin.  D_R2: the collar used to be seated on the authored
    # (pre-Solidify) surface, so the shell's 3.2 mm outward offset swallowed the
    # whole bonding flange and all 24 of its rivets - the mouth read as a plain
    # raised bezel with no fasteners at all.  The flange now lies ON the skin.
    sec = ((0.0000, -0.0060), (0.0000, 0.0000), (0.0002, 0.0064),
           (0.0013, 0.0108), (0.0036, 0.0131), (0.0072, 0.0133),
           (0.0100, 0.0116), (0.0117, 0.0076), (0.0128, 0.0026),
           (0.0178, 0.0016), (0.0250, 0.0012), (0.0250, -0.0060))

    def skin(th, ax):
        return (_barrel_r(pts, ax) + SHELL_T
                + _bulge(th, DRUM_R, ax, amp=0.0060))

    def place(s, t, u, w):
        n = _out_normal((s, t), core)
        th = (s + n[0] * u) / DRUM_R
        ax = am + t + n[1] * u
        return _cyl(skin(th, ax) + w, th, ax)

    rings = [[m.vert(place(s, t, u, w)) for (u, w) in sec] for (s, t) in per]
    m.loft(rings, closed=True, wrap=True)
    # rivets round the bonding flange, seated 0.4 mm into it
    for i in range(0, len(per), 2):
        s, t = per[i]
        n = _out_normal((s, t), core)
        th = (s + n[0] * 0.0208) / DRUM_R
        ax = am + t + n[1] * 0.0208
        o = Vector(_cyl(skin(th, ax) + 0.0004, th, ax))
        m.spin(o, Vector(_cyl(1.0, th, 0.0)),
               ((0.0000, 0.0000), (0.0022, 0.0000), (0.0024, 0.0005),
                (0.0024, 0.0013), (0.0017, 0.0019), (0.0000, 0.0019)), n=10,
               xhint=(0.0, 1.0, 0.0))
    return _make(m, f"{NAME}_{TAG}_Scoop", "CarbonFibre", hub, side, auto=36.0,
                 frame="fore")


def _drum_vanes(hub, side, rear):
    m = _Mesh()
    a_lo, a_hi = _mouth_bounds(rear)
    am = 0.5 * (a_lo + a_hi)
    ah = 0.5 * (a_hi - a_lo) + 0.004
    for k in (-1, 0, 1):
        th0 = math.radians(8.5 * k)
        rings = []
        ns = 9
        for i in range(ns):
            t = i / (ns - 1)
            r = C.lerp(DRUM_R + 0.0060, 0.1460, t)
            th = th0 + math.radians(26.0) * (t ** 1.6)
            hw = 0.0009 + 0.0013 * math.sin(math.pi * min(1.0, 0.10 + t))
            sec = [_cyl(r, th + du, am + dv)
                   for (du, dv) in _rrect(hw / r, ah, 0.0005, nq=2)]
            rings.append(m.ring(sec))
        m.loft(rings, closed=True, cap0=True, cap1=True)
    # circumferential splitter, set deeper so the mouth is not a flat grille
    rings = []
    for i in range(7):
        t = i / 6.0
        r = C.lerp(DRUM_R - 0.0020, 0.1500, t)
        sec = [_cyl(r, du, am + dv)
               for (du, dv) in _rrect(MOUTH_TH + math.radians(1.6), 0.0015,
                                      0.0006, nq=2)]
        rings.append(m.ring(sec))
    m.loft(rings, closed=True, cap0=True, cap1=True)
    # louvre deflectors over the outlet slots
    for (a, b) in OUT_SLOTS:
        rings = []
        for i in range(5):
            t = i / 4.0
            r = DRUM_R + 0.0004 + 0.0075 * math.sin(math.pi * 0.5 * t)
            ax = C.lerp(OUT_AX[1] - 0.001, OUT_AX[1] + 0.011, t)
            sec = [_cyl(r + dv, 0.5 * (a + b) + du, ax + dv * 0.0)
                   for (du, dv) in _rrect(0.5 * (b - a) + math.radians(0.6),
                                          0.0012, 0.0005, nq=2)]
            rings.append(m.ring(sec))
        m.loft(rings, closed=True, cap0=True, cap1=True)
    return _make(m, f"{NAME}_{TAG}_DuctVanes", "CarbonMatte", hub, side, auto=34.0,
                 frame="fore")


# --------------------------------------------------------------------------- #
# 6b. duct mounts - the load path from the shroud to the upright
#
# D_R13: the whole eight-object shroud floated 18.44 mm (front) / 18.86 mm
# (rear) clear of the upright with NOTHING carrying it - measured worst-case,
# both directions.  It hung off the wishbone rod ends piercing its bulkhead and
# (at the rear) a 0.01 mm touch on the ROTATING rim barrel.  A brake duct is
# bolted to the upright, so three titanium brackets now run from a saddle
# clamped on the upright's 60 mm flank, inboard past the disc, to a pad bolted
# through the inboard bulkhead.  Angles are chosen so a saddle never lands on a
# wishbone pickup boss, a caliper mounting arm or the brake-line pass-through,
# and so the strut clears the rear driveshaft CV cup (r <= 54 mm) - measured
# 12.65 mm at its worst, with the saddle bolt tips 15.93 mm off the same cup.
# --------------------------------------------------------------------------- #

# Angles measured against the assembled corner, not chosen by eye: the only
# bands where NO suspension member crosses the r 65-90 mm annulus the pads need,
# on the front AND the rear, are 0-50, 130-180 and 300-320 deg.  270 deg (the
# obvious "bottom" pick) put a pad corner 0.59 mm off a rear lower wishbone arm.
MOUNT_TH = (30.0, 150.0, 310.0)     # bracket angles, corner-local
MOUNT_FOOT_R = 0.0600               # upright outer flank radius
MOUNT_BED = 0.0006                  # bracket bedded into the seat it clamps
MOUNT_FOOT_AX = -0.0335             # saddle centre on the flank
MOUNT_SADDLE_T = 0.0120             # saddle thickness at its crown
MOUNT_SADDLE_A = 0.0125             # saddle axial half length at its crown
MOUNT_SADDLE_TH = math.radians(17.0)
MOUNT_BOLT_TH = math.radians(12.0)  # saddle bolts, either side of the strut
MOUNT_BOLT_AX = -0.0395             # clear of the wishbone arm roots (>= -33 mm)
MOUNT_ROOT_R = 0.0654               # strut root, flush with the saddle crown
MOUNT_ROOT_AX = -0.0400
MOUNT_PAD_R = 0.0790                # pad centre radius on the bulkhead cone
MOUNT_PAD_T = 0.0070


def _polar(r, th, ax, c=0.0):
    """corner-local point at (r, th, ax), offset c along the circumference."""
    return Vector((r * math.cos(th) - c * math.sin(th), ax,
                   r * math.sin(th) + c * math.cos(th)))


def _mount_taper(t):
    """saddle section factor along its arc - thick at the crown, thinned at the
    tips so the foot reads as a machined saddle and not a length of pipe."""
    return 1.0 - 0.42 * (abs(t - 0.5) * 2.0) ** 2.6


def _mount_saddle_r(t):
    """outer radius of the saddle at arc parameter t (0..1)."""
    return (MOUNT_FOOT_R - MOUNT_BED
            + MOUNT_SADDLE_T * (0.42 + 0.58 * _mount_taper(t)))


def _mount_cone(rear):
    """The pad seat on the inboard bulkhead: its (r, ax), and the unit tangent
    and OUTWARD unit normal of the bulkhead cone there, in the (r, ax) plane.
    The bulkhead is a shallow cone, so a pad normal to the axle would land on
    one edge - the pad and its bolt both ride this normal instead."""
    pts, _a0, _a1 = _drum_profile(rear)
    a_lo = _bulk_ax(pts, MOUNT_PAD_R - 0.004)[0]
    a_hi = _bulk_ax(pts, MOUNT_PAD_R + 0.004)[0]
    ax = _bulk_ax(pts, MOUNT_PAD_R)[0]
    tr, ta = 0.008, a_hi - a_lo
    ln = math.hypot(tr, ta)
    tr, ta = tr / ln, ta / ln
    return ax, (tr, ta), (ta, -tr)


def _mount_basis(th, rear):
    """(pad centre, circumferential, cone tangent, cone outward normal)."""
    pad_ax, (tr, ta), (nr, na) = _mount_cone(rear)
    er = Vector((math.cos(th), 0.0, math.sin(th)))
    eax = Vector((0.0, 1.0, 0.0))
    ec = Vector((-math.sin(th), 0.0, math.cos(th)))
    return (_polar(MOUNT_PAD_R, th, pad_ax), ec, er * tr + eax * ta,
            er * nr + eax * na)


def _cap_bolt(m, org, zdir, head_r, head_h, shank_r, depth, n=18,
              xhint=(0.0, 1.0, 0.0)):
    """Socket cap-head bolt seated at `org`: the head stands `head_h` proud
    along -zdir, the shank is driven `depth` along +zdir into what is below.
    The socket is a real hexagon, not a turned recess - at 400 mm these read as
    the difference between a bolt and a bump."""
    x, y, z = _basis(zdir, xhint)
    o = Vector(org)
    sr, sd = head_r * 0.58, head_h * 0.62

    def ring(rad, h, hexa=False):
        out = []
        for i in range(n):
            a = TAU * i / n
            rr = (rad / math.cos((a % (math.pi / 3.0)) - math.pi / 6.0)
                  if hexa else rad)
            out.append(m.vert(o + z * h + x * (rr * math.cos(a))
                              + y * (rr * math.sin(a))))
        return out

    soc1 = ring(sr * 0.94, -head_h + sd, hexa=True)
    soc0 = ring(sr, -head_h, hexa=True)
    top = ring(head_r * 0.93, -head_h)
    crown = ring(head_r, -head_h * 0.72)
    seat = ring(head_r, 0.0)
    shank = ring(shank_r, 0.0)
    tip = ring(shank_r, depth - shank_r * 0.30)
    tipc = ring(shank_r * 0.72, depth)
    m.face(list(soc1))
    for (a, b) in ((soc1, soc0), (soc0, top), (top, crown), (crown, seat),
                   (seat, shank), (shank, tip), (tip, tipc)):
        m.bridge(a, b)
    m.face(list(reversed(tipc)))


def _duct_mount(hub, side, rear):
    """Three brackets tying the duct shroud to the upright: a saddle clamped on
    the flank, a tapered strut running inboard past the disc, and a pad that
    beds into the inboard bulkhead and is bolted through it."""
    m = _Mesh()
    for deg in MOUNT_TH:
        th = math.radians(deg)
        r_in = MOUNT_FOOT_R - MOUNT_BED

        def sect(t, _th, r_in=r_in):
            e = _mount_taper(t)
            r_out = _mount_saddle_r(t)
            rc = 0.5 * (r_in + r_out)
            return [(rc + dr, MOUNT_FOOT_AX + dax)
                    for (dr, dax) in _rrect(0.5 * (r_out - r_in),
                                            MOUNT_SADDLE_A * (0.55 + 0.45 * e),
                                            0.0024, nq=3)]

        m.arc_beam(th - MOUNT_SADDLE_TH, th + MOUNT_SADDLE_TH, 16, sect)

        pc, ec, et, en = _mount_basis(th, rear)
        # strut: root buried in the saddle, tip buried in the pad
        tip = pc - en * 0.0022
        r_tip = math.hypot(tip.x, tip.z)
        ns = 9
        path = []
        for i in range(ns):
            t = i / (ns - 1)
            s = t * t * (3.0 - 2.0 * t)
            path.append(_polar(C.lerp(MOUNT_ROOT_R, r_tip, s), th,
                               C.lerp(MOUNT_ROOT_AX, tip.y, t)))

        def asect(_i, t):
            # a blade, not a rod: wide at the saddle where the bending moment
            # is, narrowed to the pad.  Depth stays inside the saddle crown so
            # the root fairs into the foot instead of standing proud of it.
            return _rrect(C.lerp(0.0095, 0.0055, t), C.lerp(0.0060, 0.0044, t),
                          0.0016, nq=3)

        m.beam(path, asect, up=tuple(_polar(0.0, th, 0.0, 1.0)))

        # pad: seated MOUNT_BED into the bulkhead skin, tapered away from it.
        # Radial half extent stops at r 88 mm: the bulkhead's wishbone
        # pass-throughs open at r 90 mm (row 0 of the cone, rm 78 mm, is never
        # cut) so the pad always lands on unbroken carbon.
        per = _rrect(0.0125, 0.0090, 0.0034, nq=3)
        rings = []
        for (off, sc) in ((MOUNT_BED, 1.0), (-0.0022, 0.99), (-MOUNT_PAD_T, 0.84)):
            rings.append(m.ring([pc + en * off + ec * (u * sc) + et * (v * sc)
                                 for (u, v) in per]))
        m.loft(rings, closed=True, cap0=True, cap1=True)
    ob = _make(m, f"{NAME}_{TAG}_DuctMount", "Titanium", hub, side, auto=32.0)
    C.add_bevel(ob, width=0.0007, segments=2, angle=36.0)
    return ob


def _mount_fasteners(m, rear):
    """What actually makes the mounts a load path: two cap screws per bracket
    driven 13 mm into the upright body, and one through the bulkhead skin into
    each pad."""
    for deg in MOUNT_TH:
        th = math.radians(deg)
        for sgn in (-1.0, 1.0):
            tb = th + sgn * MOUNT_BOLT_TH
            r_out = _mount_saddle_r(0.5 + 0.5 * MOUNT_BOLT_TH / MOUNT_SADDLE_TH)
            _cap_bolt(m, _polar(r_out, tb, MOUNT_BOLT_AX),
                      -Vector((math.cos(tb), 0.0, math.sin(tb))),
                      0.0045, 0.0032, 0.0030, 0.0225, xhint=(0.0, 1.0, 0.0))
        pc, ec, _et, en = _mount_basis(th, rear)
        _cap_bolt(m, pc + en * SHELL_T, -en, 0.0048, 0.0034, 0.0032,
                  SHELL_T + 0.0052, xhint=tuple(ec))


def _drum_fasteners(hub, side, rear):
    m = _Mesh()
    pts, ax0, ax1 = _drum_profile(rear)
    # rivets round the bulkhead: the lap joint ring and the hub boss ring
    slots = BULK_SLOTS_R if rear else BULK_SLOTS_F
    # D_R2: every one of these rivets was placed against the AUTHORED surface,
    # not the skin the Solidify actually produces, so the inner bulkhead ring
    # was buried outright, the outer ring showed 0.4 mm of a 1.7 mm dome and the
    # barrel rings showed 0.5 mm of a 3.0 mm dome - they read as drilled holes.
    # _bulk_ax / _barrel_r return the real skin, and each dome is now seated
    # 0.3-0.4 mm into it and stands proud by the rest.
    for (n, rr, off) in ((18, 0.1735, 0.30), (10, 0.0790, 0.15)):
        for i in range(n):
            th = TAU * (i + off) / n
            blocked = False
            for (a, b, r0, r1) in slots:
                if a - 0.05 <= th <= b + 0.05 and r0 - 0.012 <= rr <= r1 + 0.012:
                    blocked = True
            # D_R13: no rivet where a duct-mount pad lands - the mount bolt is
            # the fastener in that part of the ring, and a 2.3 mm dome 4 mm from
            # a 9.6 mm cap head would foul it.
            if abs(rr - MOUNT_PAD_R) < 0.012:
                for deg in MOUNT_TH:
                    d = th - math.radians(deg)
                    if abs(math.atan2(math.sin(d), math.cos(d))) < math.radians(12.0):
                        blocked = True
            if blocked:
                continue
            o = Vector(_cyl(rr, th, _bulk_ax(pts, rr)[1] + 0.0003))
            m.spin(o, (0.0, -1.0, 0.0),
                   ((0.0000, 0.0000), (0.0021, 0.0000), (0.0023, 0.0004),
                    (0.0023, 0.0012), (0.0015, 0.0017), (0.0000, 0.0017)),
                   n=12, xhint=(1.0, 0.0, 0.0))
    for (n, axf) in ((18, ax0 + 0.0615), (14, ax1 - 0.0395)):
        for i in range(n):
            th = TAU * (i + 0.35) / n
            if abs(math.atan2(math.sin(th), math.cos(th))) < math.radians(27.0):
                continue                     # keep clear of the scoop flange
            rf = (_barrel_r(pts, axf) + SHELL_T
                  + _bulge(th, DRUM_R, axf, amp=0.0060) - 0.0004)
            o = Vector(_cyl(rf, th, axf))
            m.spin(o, Vector(_cyl(1.0, th, 0.0)),
                   ((0.0000, 0.0000), (0.0038, 0.0000), (0.0042, 0.0006),
                    (0.0042, 0.0022), (0.0030, 0.0030), (0.0012, 0.0030),
                    (0.0012, 0.0018), (0.0000, 0.0018)), n=14,
                   xhint=(0.0, 1.0, 0.0))
    _mount_fasteners(m, rear)
    return _make(m, f"{NAME}_{TAG}_DrumFast", "SteelFastener", hub, side, auto=30.0)


# --------------------------------------------------------------------------- #
# assembly
# --------------------------------------------------------------------------- #

TAG = "FL"
COLL = None

CORNERS = (
    ("FL", S.FRONT_AXLE, S.FRONT_TYRE_Y - S.UPRIGHT_Y_INSET, 1, False),
    ("FR", S.FRONT_AXLE, -(S.FRONT_TYRE_Y - S.UPRIGHT_Y_INSET), -1, False),
    ("RL", S.REAR_AXLE, S.REAR_TYRE_Y - S.UPRIGHT_Y_INSET, 1, True),
    ("RR", S.REAR_AXLE, -(S.REAR_TYRE_Y - S.UPRIGHT_Y_INSET), -1, True),
)


def build(coll, ctx=None):
    global TAG, COLL
    COLL = coll
    want = os.environ.get("BRAKE_CORNERS")
    want = set(w.strip().upper() for w in want.split(",")) if want else None
    drop = os.environ.get("BRAKE_SKIP", "")
    drop = set(w.strip().lower() for w in drop.split(",") if w.strip())
    out = []
    for (tag, x, y, side, rear) in CORNERS:
        if want and tag not in want:
            continue
        TAG = tag
        hub = (x, y, S.TYRE_R)
        made = []
        made.append(_disc(hub, side))
        made.append(_disc_vanes(hub, side))
        made.append(_bell(hub, side))
        made.append(_hub(hub, side))
        made.append(_wheel_nut(hub, side))
        made.append(_upright(hub, side, rear))
        made.append(_caliper(hub, side))
        made.append(_pistons(hub, side))
        made += list(_pads(hub, side))
        made.append(_heat_shield(hub, side))
        made += list(_brake_line(hub, side, rear))
        made += list(_drum(hub, side, rear))
        made.append(_drum_bulk(hub, side, rear))
        made.append(_duct_mount(hub, side, rear))
        made.append(_scoop(hub, side, rear))
        made.append(_drum_vanes(hub, side, rear))
        made.append(_drum_fasteners(hub, side, rear))
        for ob in made:
            # BRAKE_SKIP is a preview aid only: it lets a render look straight
            # at the internals without the duct enclosure in the way.  The
            # trailing digits are stripped so "drum" still names all four arc
            # panels of the barrel without also catching DrumBulk/DrumFast.
            base = ob.name.split("_")[-1].lower()
            if drop and (base in drop or base.rstrip("0123456789") in drop):
                bpy.data.objects.remove(ob, do_unlink=True)
            else:
                out.append(ob)
    return out
