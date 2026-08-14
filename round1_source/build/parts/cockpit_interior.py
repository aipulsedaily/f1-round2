"""cockpit_interior - everything inside the cockpit opening.

What this module owns
---------------------
    CI_liner        cockpit tray lining the survival-cell throat: dished floor
                    tray, tub walls, rolled coaming lip that tucks under the
                    monocoque's own cockpit surround
    CI_sip          side impact panels bonded to the tub walls: stiffener ribs,
                    honeycomb doubler, a bolted access hatch, rivet rows
    CI_seat         moulded carbon seat shell - dished pan, hip and shoulder
                    bolsters, rolled edge, harness slot bosses, lift handles
    CI_seatpad      ribbed foam inserts (pan + back) and the leg-trough pad
    CI_headrest     rear head restraint: helmet cradle, grommeted vent bores
    CI_sidehead     FIA side head protection wedges on the coaming, Dzus fixed
    CI_dash         dash bulkhead with a rolled footwell aperture, switch
                    panel, master switch, extinguisher T-handle, connectors
    CI_column       steering column stub on the steering wheel's own axis:
                    bearing carrier, gaiter, QR collar and a FEMALE 15-spline
                    socket that steering_wheel.py's male QR plugs into
    CI_footwell     footwell tunnel forward of the dash bulkhead
    CI_pedals       pedal box: rails, plate, brake + throttle, master cylinders
    CI_harness_web  six-point webbing with modelled warp ribs and weft float
    CI_harness_hw   3-bar adjusters, bar tacks, anchor plates, eye bolts and
                    the central rotary buckle
    CI_lines        drink line, radio lead (coiled), wiring loom, P-clips
    CI_seal         rubber bulb seal capping the coaming lip
    CI_fixings      cap screws, rivets and Dzus quarter-turns

Coordinates
-----------
Car-local throughout, identity object transforms, so every object-space
procedural (the weave in CarbonMatte, the nap in SuedeGrip) runs continuously
across the whole assembly instead of restarting at each object boundary.

Landing inside the tub - MEASURED 2026-07-25 against the CURRENT monocoque_b
---------------------------------------------------------------------------
monocoque_b cuts the cockpit with the outline in ``APERTURE`` (same table) and
pulls a THROAT down from it.  Ray-casting the built monocoque today:

    survival-cell floor      MB_cell_floor top skin, z = 0.3949, |y| <= 0.134
    cell stringers/fixings   stand up to z = 0.4292 at |y| 0.121-0.137
    tub floor skin           MB_chassis_cockpit,     z = 0.3704
    wall half width @ x=0.20 z=0.60 -> 0.2061 | 0.56 -> 0.2021 | 0.50 -> 0.1908
                             z=0.46 -> 0.1761 | 0.44 -> 0.1704 | 0.43 -> 0.1676
    centreline walls         rear x=-0.161 @ z=0.60, -0.078 @ z=0.44
                             front x=+0.766 @ z=0.58, +0.654 @ z=0.405

The older landing in this file (a 0.4601 flat cap) is what monocoque_b used to
have; it does not any more, and the tray floor was left hanging 77 mm above the
real one.  ``Z_FLOOR`` is now 0.4030 - 8 mm over MB_cell_floor - and ``KTAB``
is refitted station by station so the lining stays 5.5 mm inboard of the
ray-cast wall at every depth, including the shelf it now steps over the cell
stringers with.  Measured result: CI x monocoque_b triangle overlaps fell from
1118 to 494, and all 494 are the footwell tunnel passing through the front
cockpit bulkhead in a 42 mm band at x 0.654-0.696, entirely inside the
bodywork.  monocoque_b models no opening there, and a footwell has to go
somewhere; nothing else in the part touches the monocoque at all.
"""

import math

import bmesh
import bpy
from mathutils import Vector

import common as C
import spec as S

NAME = "cockpit_interior"
P = "CI_"

TAU = math.pi * 2.0


# =========================================================================== #
# 0.  accumulator + primitive helpers
# =========================================================================== #

class _Acc:
    """Vert/face/material-index accumulator, one object per _Acc."""

    def __init__(self):
        self.v = []
        self.f = []
        self.m = []

    def add(self, verts, faces, mat=0):
        b = len(self.v)
        self.v.extend(tuple(p) for p in verts)
        for fc in faces:
            self.f.append(tuple(b + i for i in fc))
            self.m.append(mat)
        return b

    def loft(self, rings, mat=0, closed=True, cap_start=False, cap_end=False):
        n = len(rings[0])
        for r in rings:
            if len(r) != n:
                raise ValueError(f"ring length mismatch {len(r)} != {n}")
        b = len(self.v)
        for r in rings:
            self.v.extend(tuple(p) for p in r)
        span = n if closed else n - 1
        for i in range(len(rings) - 1):
            a0, b0 = b + i * n, b + (i + 1) * n
            for j in range(span):
                j2 = (j + 1) % n
                self.f.append((a0 + j, a0 + j2, b0 + j2, b0 + j))
                self.m.append(mat)
        if cap_start:
            self.f.append(tuple(range(b, b + n))[::-1])
            self.m.append(mat)
        if cap_end:
            s = b + (len(rings) - 1) * n
            self.f.append(tuple(range(s, s + n)))
            self.m.append(mat)
        return b

    def grid(self, rows, mat=0, wrap=False):
        n = len(rows[0])
        b = len(self.v)
        for r in rows:
            self.v.extend(tuple(p) for p in r)
        span = n if wrap else n - 1
        for i in range(len(rows) - 1):
            a0, b0 = b + i * n, b + (i + 1) * n
            for j in range(span):
                j2 = (j + 1) % n
                self.f.append((a0 + j, a0 + j2, b0 + j2, b0 + j))
                self.m.append(mat)
        return b


def _cut_and_weld(ob, coll, cut, extra, smooth=32.0):
    """Difference `cut` out of `ob`, then weld `extra` into the result.

    The operand handed to the solver is a single closed manifold shell (the
    bosses, beams and handles are held back in `extra` precisely so it is), the
    modifier is evaluated and baked here, and the cutter object is deleted - so
    the finished part carries no modifier, no helper object and no boolean
    surprises at render time.
    """
    if not cut.v:
        return ob
    cob = C.new_obj(ob.name + "_cutter", cut.v, cut.f, coll=coll, smooth=False)
    m = ob.modifiers.new("open", "BOOLEAN")
    m.operation = "DIFFERENCE"
    m.solver = "EXACT"
    m.object = cob
    bpy.context.view_layer.update()
    deps = bpy.context.evaluated_depsgraph_get()
    new = bpy.data.meshes.new_from_object(ob.evaluated_get(deps))
    old = ob.data
    ob.modifiers.clear()
    ob.data = new
    bpy.data.meshes.remove(old)
    new.name = ob.name
    cme = cob.data
    bpy.data.objects.remove(cob, do_unlink=True)
    # do_unlink drops the object but leaves its mesh datablock orphaned, which
    # is how a "harmless" helper leaks two meshes per build call.
    if cme is not None and cme.users == 0:
        bpy.data.meshes.remove(cme)

    if extra is not None and extra.v:
        tmp = bpy.data.meshes.new(ob.name + "_extra")
        tmp.from_pydata([tuple(p) for p in extra.v], [], extra.f)
        tmp.validate(verbose=False)
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bm.from_mesh(tmp)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(ob.data)
        bm.free()
        bpy.data.meshes.remove(tmp)
        C.merge_doubles(ob, 2.5e-5)
    for p in ob.data.polygons:
        p.use_smooth = True
    C.shade_auto_smooth(ob, smooth)
    return ob


def _emit(name, acc, coll, mats, smooth=32.0, weld=2.5e-5):
    ob = C.new_obj(name, acc.v, acc.f, coll=coll, smooth=True)
    if weld:
        C.merge_doubles(ob, weld)
    me = ob.data
    for i, mname in enumerate(mats):
        S.assign(ob, mname, slot=i)
    if len(mats) > 1 and len(me.polygons) == len(acc.m):
        for poly, mi in zip(me.polygons, acc.m):
            poly.material_index = min(mi, len(mats) - 1)
    C.shade_auto_smooth(ob, smooth)
    return ob


def _v(p):
    return Vector((float(p[0]), float(p[1]), float(p[2])))


def _basis(nrm, ref=(1.0, 0.0, 0.0)):
    n = _v(nrm).normalized()
    r = _v(ref)
    if abs(r.dot(n)) > 0.92:
        r = Vector((0.0, 0.0, 1.0)) if abs(n.z) < 0.92 else Vector((0.0, 1.0, 0.0))
    u = (r - n * r.dot(n)).normalized()
    return u, n.cross(u).normalized(), n


def _hexr(across_flats):
    a0 = math.pi / 6.0

    def f(a):
        t = (a + a0) % (math.pi / 3.0) - a0
        return 0.5 * across_flats / math.cos(t)
    return f


def _slotr(half_len, half_wid, k=6.0):
    """Radius function of a rounded slot (stadium-ish superellipse)."""
    def f(a):
        cx = abs(math.cos(a)) / half_len
        cy = abs(math.sin(a)) / half_wid
        return (cx ** k + cy ** k) ** (-1.0 / k)
    return f


def _shape(acc, pos, nrm, rings, seg=32, ref=(1.0, 0.0, 0.0), mat=0):
    """Solid of revolution (radius may be a function of angle) at pos/nrm."""
    u, w, n = _basis(nrm, ref)
    p = _v(pos)
    out = []
    for (rf, h) in rings:
        ring = []
        for i in range(seg):
            a = TAU * i / seg
            r = rf(a) if callable(rf) else rf
            q = p + u * (r * math.cos(a)) + w * (r * math.sin(a)) + n * h
            ring.append((q.x, q.y, q.z))
        out.append(ring)
    acc.loft(out, mat=mat, closed=True)
    return out


# ---- fasteners ------------------------------------------------------------ #

def _cap_screw(acc, pos, nrm, r=0.0040, h=0.0030, mat=0, seg=24, sink=0.0014,
               ref=(1.0, 0.0, 0.0)):
    sr = r * 0.55
    sd = h * 0.60
    c = min(0.00045, r * 0.14)
    hx = _hexr(2.0 * sr)
    rings = [(0.0, -sink), (r, -sink), (r, h - c), (r - c, h),
             (hx, h), (hx, h - sd), (0.0, h - sd)]
    _shape(acc, pos, nrm, rings, seg=seg, mat=mat, ref=ref)


def _rivet(acc, pos, nrm, r=0.0020, mat=0, seg=13, ref=(1.0, 0.0, 0.0)):
    rings = [(0.0, -0.0013), (r, -0.0013), (r, 0.0), (r * 0.96, 0.00045),
             (r * 0.80, 0.00098), (r * 0.47, 0.00142), (0.0, 0.00158)]
    _shape(acc, pos, nrm, rings, seg=seg, mat=mat, ref=ref)


def _dzus(acc, pos, nrm, tan, r=0.0058, mat=0, seg=30):
    """Quarter-turn button: buried flange, flat head, real recessed drive slot."""
    slot = _slotr(r * 0.74, 0.00105)
    rings = [(0.0, -0.0022), (r * 1.28, -0.0022), (r * 1.28, -0.0011),
             (r * 1.06, -0.0004), (r, 0.0), (r, 0.0011),
             (r - 0.0004, 0.0015), (slot, 0.0015), (slot, 0.0006),
             (0.0, 0.0004)]
    _shape(acc, pos, nrm, rings, seg=seg, mat=mat, ref=tan)


def _eye_bolt(acc, pos, nrm, up, r=0.0055, mat=0):
    """Harness anchor: shouldered boss with a real rolled eye above it, so the
    strap has something to pass through instead of ending in mid-air."""
    rings = [(0.0, 0.0), (r * 1.9, 0.0), (r * 1.9, 0.0032), (r * 1.55, 0.0042),
             (r * 1.1, 0.0048), (r * 1.1, 0.0086), (r * 1.0, 0.0098),
             (0.0, 0.0098)]
    _shape(acc, pos, nrm, rings, seg=22, mat=mat, ref=up)
    n = _v(nrm).normalized()
    u, w, _n3 = _basis(nrm, up)
    c = _v(pos) + n * 0.0158
    ring = []
    for i in range(28):
        a = TAU * i / 28.0
        ring.append(c + u * (0.0086 * math.cos(a)) + w * (0.0086 * math.sin(a)))
    ring.append(ring[0])
    _tube(acc, ring, 0.0028, seg=10, mat=mat, caps=False, up=tuple(n))
    _tube(acc, [_v(pos) + n * 0.0086, c - u * 0.0055], 0.0028, seg=10, mat=mat)


# ---- sweeps --------------------------------------------------------------- #

def _frames(path, up=(0.0, 0.0, 1.0)):
    pv = [_v(p) for p in path]
    n = len(pv)
    tg = []
    for i in range(n):
        if i == 0:
            t = pv[1] - pv[0]
        elif i == n - 1:
            t = pv[-1] - pv[-2]
        else:
            t = pv[i + 1] - pv[i - 1]
        if t.length < 1e-9:
            t = Vector((1.0, 0.0, 0.0))
        tg.append(t.normalized())
    u0 = _v(up)
    if abs(u0.dot(tg[0])) > 0.95:
        u0 = Vector((1.0, 0.0, 0.0)) if abs(tg[0].x) < 0.9 else Vector((0.0, 1.0, 0.0))
    nn = [(u0 - tg[0] * u0.dot(tg[0])).normalized()]
    for i in range(1, n):
        w = nn[-1] - tg[i] * nn[-1].dot(tg[i])
        if w.length < 1e-9:
            w = tg[i].cross(Vector((0.0, 0.0, 1.0)))
        nn.append(w.normalized())
    bb = [tg[i].cross(nn[i]).normalized() for i in range(n)]
    return pv, tg, nn, bb


def _tube(acc, path, r, seg=14, mat=0, caps=True, up=(0.0, 0.0, 1.0)):
    pv, _tg, nn, bb = _frames(path, up)
    rings = []
    m = len(pv)
    for i, p in enumerate(pv):
        t = i / max(1, m - 1)
        rr = r(t) if callable(r) else r
        ring = []
        for k in range(seg):
            a = TAU * k / seg
            q = p + nn[i] * (rr * math.cos(a)) + bb[i] * (rr * math.sin(a))
            ring.append((q.x, q.y, q.z))
        rings.append(ring)
    acc.loft(rings, mat=mat, closed=True, cap_start=caps, cap_end=caps)
    return rings


def _shell_rings(sections, edge=3, er=0.0009):
    """sections: list of (top_pts, bot_pts) - equal-length Vector lists.

    Returns closed rings: top surface, rounded right edge, bottom surface
    reversed, rounded left edge.  Used for every strap, pad and bonded panel in
    this module so they all get a real rolled edge instead of a knife edge.
    """
    rings = []
    for top, bot in sections:
        ring = list(top)
        c = (top[-1] + bot[-1]) * 0.5
        ax = (top[-1] - bot[-1]) * 0.5
        d = top[-1] - top[-2]
        if ax.length > 1e-9:
            an = ax.normalized()
            d = d - an * d.dot(an)
        d = d.normalized() * er if d.length > 1e-9 else Vector((0, 0, 0))
        for k in range(1, edge + 1):
            th = math.pi * k / (edge + 1)
            ring.append(c + ax * math.cos(th) + d * math.sin(th))
        ring.extend(reversed(bot))
        c2 = (top[0] + bot[0]) * 0.5
        ax2 = (top[0] - bot[0]) * 0.5
        d2 = top[0] - top[1]
        if ax2.length > 1e-9:
            an2 = ax2.normalized()
            d2 = d2 - an2 * d2.dot(an2)
        d2 = d2.normalized() * er if d2.length > 1e-9 else Vector((0, 0, 0))
        for k in range(1, edge + 1):
            th = math.pi * (edge + 1 - k) / (edge + 1)
            ring.append(c2 + ax2 * math.cos(th) + d2 * math.sin(th))
        rings.append([(p.x, p.y, p.z) for p in ring])
    return rings


def _tab1(tab, u):
    if u <= tab[0][0]:
        return tab[0][1]
    if u >= tab[-1][0]:
        return tab[-1][1]
    for i in range(len(tab) - 1):
        if tab[i][0] <= u <= tab[i + 1][0]:
            t = (u - tab[i][0]) / (tab[i + 1][0] - tab[i][0])
            return C.lerp(tab[i][1], tab[i + 1][1], t)
    return tab[-1][1]


# =========================================================================== #
# 1.  the cockpit aperture and the throat measured off monocoque_b
# =========================================================================== #

APERTURE = [
    (0.780, 0.000), (0.766, 0.048), (0.726, 0.100), (0.664, 0.146),
    (0.588, 0.178), (0.482, 0.201), (0.362, 0.212), (0.242, 0.217),
    (0.122, 0.217), (0.022, 0.212), (-0.052, 0.199), (-0.102, 0.179),
    (-0.134, 0.145), (-0.156, 0.098), (-0.166, 0.040), (-0.168, 0.000),
]

AP_XC = 0.3060            # aperture centroid the throat scales about
Z_FLOOR = 0.4030          # tray floor: 8.1 mm over MB_cell_floor's 0.3949 cap
RIM_DROP = 0.0055         # tuck the lining under the monocoque coaming

# depth parameter v -> (z fraction, half width scale, length scale).
#
# D-CI23: refitted 2026-07-25 against the CURRENT monocoque_b.  Its cockpit no
# longer bottoms out at z=0.4601 - MB_cell_floor caps the throat at 0.3949 and
# the survival-cell stringers/fixings stand up to 0.4292 at |y| 0.121-0.137.
# Every entry below is (min over 40 stations of the ray-cast wall - 5.5 mm) /
# aperture half width at the same station, then a monotone-decreasing envelope
# so the funnel never bulges back out.  The step between v=0.845 and v=0.875 is
# the real shelf over the cell stringers, not a modelling artefact.
KTAB_EZ = [(0.000, 0.000), (0.060, 0.060), (0.120, 0.120), (0.200, 0.200),
           (0.280, 0.280), (0.360, 0.360), (0.440, 0.440), (0.520, 0.520),
           (0.600, 0.600), (0.680, 0.680), (0.740, 0.740), (0.800, 0.800),
           (0.845, 0.845), (0.875, 0.875), (0.900, 0.900), (0.940, 0.940),
           (1.000, 1.000)]
KTAB_KY = [(0.000, 0.9067), (0.060, 0.8917), (0.120, 0.8801), (0.200, 0.8616),
           (0.280, 0.8407), (0.360, 0.8176), (0.440, 0.7930), (0.520, 0.7554),
           (0.600, 0.7040), (0.680, 0.7040), (0.740, 0.7040), (0.800, 0.7040),
           (0.845, 0.7040), (0.875, 0.5090), (0.900, 0.4960), (0.940, 0.4890),
           (1.000, 0.4830)]
KTAB_KX = [(0.000, 0.9500), (0.060, 0.9500), (0.120, 0.9500), (0.200, 0.9500),
           (0.280, 0.9500), (0.360, 0.9500), (0.440, 0.9500), (0.520, 0.9400),
           (0.600, 0.9220), (0.680, 0.8900), (0.740, 0.8300), (0.800, 0.7900),
           (0.845, 0.7500), (0.875, 0.7400), (0.900, 0.7340), (0.940, 0.7280),
           (1.000, 0.7200)]
# extra rear pull-in (see _ky_at), fitted the same way
KTAB_TR = [(0.000, 0.000), (0.520, 0.000), (0.680, 0.040), (0.800, 0.060),
           (0.875, 0.000), (1.000, 0.000)]

X_DASH_B = 0.6300         # dash bulkhead rear face (tray front)
X_DASH_F = 0.6440
X_FOOT_F = 1.0900         # footwell tunnel front bulkhead
SKIN_T = 0.0055           # CI_liner solidify thickness (grows INBOARD)


def _ez(v):
    return _tab1(KTAB_EZ, v)


def _ky(v):
    return _tab1(KTAB_KY, v)


def _kx(v):
    return _tab1(KTAB_KX, v)


def _skin_z(x, y):
    """z of the body's upper skin at station x, |y| - walks the same 7-point
    half section spec.body_surface_point samples."""
    half = S.station_half(S.station_at(x))
    pts = C.catmull_rom(half, 220)
    y = abs(y)
    for i in range(len(pts) - 1, 0, -1):
        y0, z0 = pts[i]
        y1, z1 = pts[i - 1]
        if i == len(pts) - 1 and y <= y0 + 1e-9:
            return z0
        if (y0 - y) * (y1 - y) <= 0.0 and abs(y1 - y0) > 1e-9:
            t = (y - y0) / (y1 - y0)
            return z0 + (z1 - z0) * t
    return pts[-1][1]


_AP_S = C.catmull_rom(APERTURE, 200)
_AP_X = [p[0] for p in _AP_S]


def _ap_hw(x):
    if x >= _AP_X[0] or x <= _AP_X[-1]:
        return 0.0
    lo, hi = 0, len(_AP_X) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if _AP_X[mid] >= x:
            lo = mid
        else:
            hi = mid
    t = (_AP_X[lo] - x) / max(_AP_X[lo] - _AP_X[hi], 1e-9)
    return max(0.0, C.lerp(_AP_S[lo][1], _AP_S[hi][1], t))


_RIMZ_CACHE = {}


def _rim_z(x):
    """z of the aperture edge at station x, already dropped under the coaming."""
    key = round(x, 5)
    hit = _RIMZ_CACHE.get(key)
    if hit is not None:
        return hit
    hw = max(_ap_hw(x), 0.0045)
    z = _skin_z(x, hw) - RIM_DROP
    _RIMZ_CACHE[key] = z
    return z


def _ky_at(xr, v):
    """Half-width scale with an extra rear pull-in.

    D-CI13: monocoque_b's throat closes in faster behind the driver than a
    uniform scale of the aperture does - at (x=-0.045, z=0.495) the measured
    wall is at y=0.152 while a uniform 0.848 scale put the lining at 0.155,
    3.5 mm THROUGH it.  This tapers the rear of the funnel with depth."""
    k = _ky(v)
    if xr < 0.0200:
        k *= 1.0 - _tab1(KTAB_TR, v) * min(1.0, (0.0200 - xr) / 0.1880)
    return k


def _funnel_pt(xr, v):
    """Point on the tray wall.  xr is the station of the rim point it hangs
    from, v the depth parameter (0 rim, 1 floor edge).  Returns (x, y, z)."""
    kx, e = _kx(v), _ez(v)
    x = AP_XC + (xr - AP_XC) * kx
    y = _ap_hw(xr) * _ky_at(xr, v)
    z = C.lerp(_rim_z(xr), Z_FLOOR, e)
    return x, y, z


def _wall_yz(x, v):
    """(y, z) of the wall at station x and depth v - inverts the length scale."""
    kx = _kx(v)
    xr = AP_XC + (x - AP_XC) / kx
    return (_ap_hw(xr) * _ky_at(xr, v),
            C.lerp(_rim_z(xr), Z_FLOOR, _ez(v)))


def _mkvs():
    """Depth samples, bunched through the stringer shelf at v 0.84-0.95 so the
    step resolves as a shelf instead of a 40 mm chamfer."""
    out = [i / 30.0 * 0.82 for i in range(31)]
    out += [0.845, 0.858, 0.868, 0.876, 0.884, 0.895, 0.910, 0.930, 0.952,
            0.972, 0.988, 1.000]
    return sorted(set(round(v, 5) for v in out))


VS = _mkvs()


def _liner_half(x, samples=40):
    """Inner half section (y, z) at station x: floor centre -> rim."""
    y1, _z1 = _wall_yz(x, 1.0)
    ctl = [(0.0, Z_FLOOR), (0.42 * y1, Z_FLOOR + 0.0012),
           (0.80 * y1, Z_FLOOR + 0.0006)]
    for v in reversed(VS):
        y, z = _wall_yz(x, v)
        ctl.append((y, z))
    return C.catmull_rom(ctl, samples)


def _normals2(pts):
    """Outward 2D normals of a (y, z) polyline (outward = away from the tub
    interior: -z under the floor, +y outboard of the wall)."""
    n = len(pts)
    out = []
    for i in range(n):
        if i == 0:
            dy, dz = pts[1][0] - pts[0][0], pts[1][1] - pts[0][1]
        elif i == n - 1:
            dy, dz = pts[-1][0] - pts[-2][0], pts[-1][1] - pts[-2][1]
        else:
            dy, dz = pts[i + 1][0] - pts[i - 1][0], pts[i + 1][1] - pts[i - 1][1]
        l = math.hypot(dy, dz)
        out.append((0.0, -1.0) if l < 1e-12 else (dz / l, -dy / l))
    return out


def _wall_pt(x, s):
    """Point + inward normal on the tray wall, s in 0..1 along the half
    section (0 = floor centre, 1 = rim).  Positive y side."""
    inner = _liner_half(x)
    nrm = _normals2(inner)
    f = s * (len(inner) - 1)
    i = min(max(int(f), 0), len(inner) - 2)
    t = f - i
    y = C.lerp(inner[i][0], inner[i + 1][0], t)
    z = C.lerp(inner[i][1], inner[i + 1][1], t)
    ny = C.lerp(nrm[i][0], nrm[i + 1][0], t)
    nz = C.lerp(nrm[i][1], nrm[i + 1][1], t)
    l = math.hypot(ny, nz) or 1.0
    return Vector((x, y, z)), Vector((0.0, -ny / l, -nz / l))


def _wall_s_at_z(x, z):
    inner = _liner_half(x)
    for i in range(len(inner) - 1, 0, -1):
        z0, z1 = inner[i][1], inner[i - 1][1]
        if (z0 - z) * (z1 - z) <= 0.0 and abs(z1 - z0) > 1e-9:
            t = (z - z0) / (z1 - z0)
            return (i - t) / (len(inner) - 1)
    return 1.0


def _rim_top(x):
    """(y, z) of the lining's top edge at station x."""
    return _wall_yz(x, 0.0)


# =========================================================================== #
# 2.  the tray lining
# =========================================================================== #

def _tray_loop(v, n_side=112):
    """Closed section loop at depth v, running front tip -> left -> rear tip ->
    right -> back.  Truncated at the dash bulkhead."""
    kx = _kx(v)
    xr_front = AP_XC + (X_DASH_B - AP_XC) / kx
    xr_front = min(xr_front, 0.7780)
    xr_rear = -0.1670
    left = []
    for i in range(n_side):
        t = i / (n_side - 1.0)
        # bunch samples toward both tips where curvature is high
        t = 0.72 * t + 0.28 * (0.5 - 0.5 * math.cos(math.pi * t))
        xr = C.lerp(xr_front, xr_rear, t)
        x, y, z = _funnel_pt(xr, v)
        left.append((x, y, z))
    right = [(x, -y, z) for (x, y, z) in reversed(left[1:-1])]
    return left + right


def _build_liner(acc, fix):
    rings = [_tray_loop(v) for v in VS]
    # flat floor tray inside the v=1 loop
    base = _tray_loop(1.0)
    for s in (0.80, 0.58, 0.34, 0.12):
        rings.append([(AP_XC + (x - AP_XC) * s, y * s, Z_FLOOR)
                      for (x, y, z) in base])
    n = len(rings[0])
    acc.loft(rings, mat=0, closed=True, cap_end=True)
    _ = n

    # ---- floor detail: seat rails, drains, doublers ---------------------- #
    # The liner is solidified 5.5 mm INBOARD (measured: a ray down the tray at
    # x=0.20 crosses the shell at Z_FLOOR and Z_FLOOR+0.0055), so anything laid
    # on the floor has to start from Z_FLOOR + SKIN or it is buried.
    for sgn in (1, -1):
        rows_t, rows_b = [], []
        for i in range(40):
            x = C.lerp(0.0100, 0.4400, i / 39.0)
            yc = sgn * 0.0800
            zb = Z_FLOOR + SKIN_T
            rows_t.append([Vector((x, yc - 0.0165, zb + 0.0100)),
                           Vector((x, yc - 0.0120, zb + 0.0118)),
                           Vector((x, yc + 0.0120, zb + 0.0118)),
                           Vector((x, yc + 0.0165, zb + 0.0100))])
            rows_b.append([Vector((x, yc - 0.0165, zb)),
                           Vector((x, yc - 0.0120, zb)),
                           Vector((x, yc + 0.0120, zb)),
                           Vector((x, yc + 0.0165, zb))])
        acc.loft(_shell_rings([(rows_t[i], rows_b[i]) for i in range(40)],
                              edge=2, er=0.0016),
                 mat=0, closed=True, cap_start=True, cap_end=True)
        for k in range(6):
            x = C.lerp(0.0320, 0.4180, k / 5.0)
            _cap_screw(fix, (x, sgn * 0.0800, Z_FLOOR + SKIN_T + 0.0130),
                       (0, 0, 1), r=0.0042, h=0.0030, mat=0)

    for k in range(3):
        x = C.lerp(0.0700, 0.3900, k / 2.0)
        _shape(acc, (x, 0.0, Z_FLOOR + SKIN_T), (0, 0, 1),
               [(0.0182, -0.0030), (0.0182, -0.0012), (0.0166, -0.0002),
                (0.0146, 0.0004), (0.0131, 0.0002), (0.0126, -0.0004),
                (0.0126, -0.0034), (0.0, -0.0040)], seg=26, mat=0)


SIP_Z0 = 0.4620           # bottom of the side impact panels: clear of the
#                           stringer shelf the tray now steps over at z~0.433


def _build_sip(acc, fix):
    """Side impact panels bonded to the tray walls."""
    for sgn in (1, -1):
        xs = [C.lerp(-0.0700, 0.5400, i / 55.0) for i in range(56)]
        sec = []
        for xi, x in enumerate(xs):
            s0 = _wall_s_at_z(x, SIP_Z0)
            s1 = _wall_s_at_z(x, _rim_top(x)[1] - 0.0180)
            tx = xi / (len(xs) - 1.0)
            top, bot = [], []
            n = 34
            for j in range(n):
                s = C.lerp(s0, s1, j / (n - 1.0))
                p, nn = _wall_pt(x, s)
                p = Vector((p.x, sgn * p.y, p.z))
                nn = Vector((nn.x, sgn * nn.y, nn.z))
                u = j / (n - 1.0)
                rib = 0.0
                for rc in (0.215, 0.500, 0.775):
                    d = (u - rc) / 0.060
                    if abs(d) < 1.0:
                        rib += 0.0052 * (0.5 + 0.5 * math.cos(math.pi * d))
                for xc in (0.085, 0.235, 0.905):
                    d = (tx - xc) / 0.022
                    if abs(d) < 1.0:
                        rib += 0.0040 * (0.5 + 0.5 * math.cos(math.pi * d))
                if u > 0.880:
                    rib += 0.0036 * min(1.0, (u - 0.880) / 0.045)
                fall = min(1.0, min(u, 1.0 - u) / 0.055)
                th = (0.0032 + rib) * (0.30 + 0.70 * fall)
                top.append(p + nn * (0.0009 + th))
                bot.append(p + nn * 0.0006)
            sec.append((top, bot))
        acc.loft(_shell_rings(sec, edge=3, er=0.0011), mat=0,
                 closed=True, cap_start=True, cap_end=True)

        # bolted access hatch
        hx0, hx1 = 0.2900, 0.4500
        hs0, hs1 = 0.50, 0.78
        sec = []
        nx = 20
        for i in range(nx):
            x = C.lerp(hx0, hx1, i / (nx - 1.0))
            top, bot = [], []
            n = 14
            for j in range(n):
                s = C.lerp(hs0, hs1, j / (n - 1.0))
                p, nn = _wall_pt(x, s)
                p = Vector((p.x, sgn * p.y, p.z))
                nn = Vector((nn.x, sgn * nn.y, nn.z))
                u, w = i / (nx - 1.0), j / (n - 1.0)
                fall = min(1.0, min(u, 1.0 - u) / 0.09) * min(1.0, min(w, 1.0 - w) / 0.12)
                top.append(p + nn * (0.0050 + 0.0026 * fall))
                bot.append(p + nn * 0.0046)
            sec.append((top, bot))
        acc.loft(_shell_rings(sec, edge=3, er=0.0010), mat=0,
                 closed=True, cap_start=True, cap_end=True)
        for i in range(4):
            for j in range(2):
                x = C.lerp(hx0 + 0.014, hx1 - 0.014, i / 3.0)
                s = C.lerp(hs0 + 0.035, hs1 - 0.035, float(j))
                p, nn = _wall_pt(x, s)
                p = Vector((p.x, sgn * p.y, p.z))
                nn = Vector((nn.x, sgn * nn.y, nn.z))
                _dzus(fix, p + nn * 0.0072, nn, Vector((1.0, 0.0, 0.0)),
                      r=0.0054, mat=0)

        for s_ in (0.0, 1.0):
            for k in range(22):
                x = C.lerp(-0.0620, 0.5320, k / 21.0)
                s0 = _wall_s_at_z(x, SIP_Z0)
                s1 = _wall_s_at_z(x, _rim_top(x)[1] - 0.0180)
                s = C.lerp(s0 + 0.020, s1 - 0.018, s_)
                p, nn = _wall_pt(x, s)
                p = Vector((p.x, sgn * p.y, p.z))
                nn = Vector((nn.x, sgn * nn.y, nn.z))
                _rivet(fix, p + nn * 0.0042, nn, r=0.0018, mat=1)


def _build_seal(acc):
    """Rubber bulb seal capping the lining's top edge."""
    xs = [C.lerp(-0.1620, X_DASH_B - 0.004, i / 179.0) for i in range(180)]
    for sgn in (1, -1):
        rings = []
        for i, x in enumerate(xs):
            y, z = _rim_top(x)
            ends = min(1.0, min(i, len(xs) - 1 - i) / 5.0)
            r1 = 0.0052 * (0.30 + 0.70 * ends)
            r2 = 0.0044 * (0.30 + 0.70 * ends)
            ring = []
            for k in range(14):
                a = TAU * k / 14.0
                ring.append((x, sgn * (y - 0.0040) + r1 * math.cos(a),
                             z + 0.0004 + r2 * math.sin(a)))
            rings.append(ring)
        acc.loft(rings, mat=0, closed=True, cap_start=True, cap_end=True)


def _build_coaming_fix(fix):
    """Rivet row on the wall just under the coaming."""
    n = 40
    for sgn in (1, -1):
        for k in range(n):
            x = C.lerp(-0.1350, 0.5900, k / (n - 1.0))
            s = _wall_s_at_z(x, _rim_top(x)[1] - 0.0135)
            p, nn = _wall_pt(x, s)
            p = Vector((p.x, sgn * p.y, p.z))
            nn = Vector((nn.x, sgn * nn.y, nn.z))
            _rivet(fix, p + nn * 0.0006, nn, r=0.0018, mat=1)


# =========================================================================== #
# 3.  seat shell + ribbed padding
# =========================================================================== #

SPINE = [
    (0.5300, 0.5065), (0.4650, 0.4968), (0.4000, 0.4908), (0.3250, 0.4874),
    (0.2500, 0.4868), (0.1800, 0.4892), (0.1200, 0.4962), (0.0750, 0.5080),
    (0.0380, 0.5248), (0.0050, 0.5448), (-0.0250, 0.5660), (-0.0500, 0.5872),
    (-0.0700, 0.6052), (-0.0830, 0.6180),
]

SEAT_W = [(0.00, 0.1330), (0.10, 0.1500), (0.22, 0.1625), (0.34, 0.1705),
          (0.46, 0.1735), (0.58, 0.1710), (0.70, 0.1630), (0.80, 0.1520),
          (0.90, 0.1390), (0.96, 0.1280), (1.00, 0.1180)]
SEAT_B = [(0.00, 0.0180), (0.12, 0.0330), (0.26, 0.0500), (0.38, 0.0580),
          (0.50, 0.0540), (0.62, 0.0440), (0.72, 0.0400), (0.84, 0.0510),
          (0.94, 0.0480), (1.00, 0.0320)]
SEAT_D = [(0.00, 0.0090), (0.20, 0.0135), (0.42, 0.0150), (0.60, 0.0118),
          (0.80, 0.0092), (1.00, 0.0075)]
SHELL_T = 0.0062

_SP = C.catmull_rom(SPINE, 180)
_ARC = [0.0]
for _k in range(1, len(_SP)):
    _ARC.append(_ARC[-1] + math.hypot(_SP[_k][0] - _SP[_k - 1][0],
                                      _SP[_k][1] - _SP[_k - 1][1]))


def _spine_frame(u):
    f = u * (len(_SP) - 1)
    i = min(int(f), len(_SP) - 2)
    t = f - i
    x = C.lerp(_SP[i][0], _SP[i + 1][0], t)
    z = C.lerp(_SP[i][1], _SP[i + 1][1], t)
    i0 = max(0, i - 2)
    i1 = min(len(_SP) - 1, i + 3)
    dx = _SP[i1][0] - _SP[i0][0]
    dz = _SP[i1][1] - _SP[i0][1]
    l = math.hypot(dx, dz) or 1.0
    dx, dz = dx / l, dz / l
    return Vector((x, 0.0, z)), Vector((dx, 0.0, dz)), Vector((dz, 0.0, -dx))


def _spine_arc(u):
    f = u * (len(_SP) - 1)
    i = min(int(f), len(_SP) - 2)
    return C.lerp(_ARC[i], _ARC[i + 1], f - i)


def _spine_u_at_x(x):
    """u where the seat spine crosses station x (spine x decreases with u)."""
    for i in range(len(_SP) - 1):
        x0, x1 = _SP[i][0], _SP[i + 1][0]
        if (x0 - x) * (x1 - x) <= 0.0 and abs(x0 - x1) > 1e-12:
            return (i + (x0 - x) / (x0 - x1)) / (len(_SP) - 1)
    return 0.0


# ---- front cut: the seat has to stop BEHIND the steering wheel -------------
#
# D-CI34.  MEASURED off the built steering_wheel.py (every SW_ vertex, car-local):
#     the wheel occupies x 0.4398..0.5669, |y| <= 0.1401, z 0.4069..0.5964.
# It is a 22 deg raked disc whose bottom rim reaches z=0.4069 - 1.6 mm off the
# tray floor skin - at x=0.469, so there is no room under it and none over it:
# anything the seat puts in x > 0.44 at pan height is inside the wheel.  The pan
# used to start at x=0.5300 (SPINE[0]) with the pad on top of it, i.e. a
# horizontal sheet driven through the wheel's own centreline (overlaps ran
# wheel-local b -0.026..+0.028 across the full a = +-0.140 width).  Both are now
# cut at X_SEAT_F, the pad keeping its original 0.030 setback behind the shell.
X_WHEEL_AFT = 0.4398      # rearmost vertex of the whole built steering wheel
X_SEAT_F = 0.4335         # seat shell nose: 6.3 mm aft of it
U_SEAT_F = _spine_u_at_x(X_SEAT_F)
U_PAD_F = U_SEAT_F + 0.030


def _seat_w(u):
    return _tab1(SEAT_W, u)


def _bol_ramp(t):
    """Bolster rise: flat middle, smooth climb, rolled crest."""
    if t <= 0.50:
        return 0.0
    s = min(1.0, (t - 0.50) / 0.50)
    return (s * s * (3.0 - 2.0 * s)) * (1.0 - 0.20 * s ** 6)


def _seat_prof(u):
    w = _seat_w(u)
    b = _tab1(SEAT_B, u)
    d = _tab1(SEAT_D, u)
    return [(0.000 * w, -d),
            (0.240 * w, -d * 0.86),
            (0.460 * w, -d * 0.34),
            (0.620 * w, b * _bol_ramp(0.62) + 0.0006),
            (0.760 * w, b * _bol_ramp(0.76)),
            (0.870 * w, b * _bol_ramp(0.87)),
            (0.950 * w, b * _bol_ramp(0.95)),
            (1.000 * w, b * _bol_ramp(1.00))]


_SEC_CACHE = {}


def _seat_section(u, nv):
    key = (round(u, 5), nv)
    hit = _SEC_CACHE.get(key)
    if hit is not None:
        return hit
    half = C.catmull_rom(_seat_prof(u), (nv + 1) // 2)
    full = [(-p[0], p[1]) for p in reversed(half[1:])] + list(half)
    n = len(full)
    nrm = []
    for i in range(n):
        if i == 0:
            dv, dh = full[1][0] - full[0][0], full[1][1] - full[0][1]
        elif i == n - 1:
            dv, dh = full[-1][0] - full[-2][0], full[-1][1] - full[-2][1]
        else:
            dv, dh = full[i + 1][0] - full[i - 1][0], full[i + 1][1] - full[i - 1][1]
        l = math.hypot(dv, dh) or 1.0
        nrm.append((-dh / l, dv / l))
    _SEC_CACHE[key] = (full, nrm)
    return full, nrm


def _seat_pt(u, q, off=0.0, nv=61):
    full, nrm = _seat_section(u, nv)
    f = (q * 0.5 + 0.5) * (len(full) - 1)
    i = min(max(int(f), 0), len(full) - 2)
    t = f - i
    v = C.lerp(full[i][0], full[i + 1][0], t)
    h = C.lerp(full[i][1], full[i + 1][1], t)
    nv2 = C.lerp(nrm[i][0], nrm[i + 1][0], t)
    nh2 = C.lerp(nrm[i][1], nrm[i + 1][1], t)
    l = math.hypot(nv2, nh2) or 1.0
    p, _t3, n3 = _spine_frame(u)
    return p + Vector((0.0, 1.0, 0.0)) * (v + off * nv2 / l) + n3 * (h + off * nh2 / l)


def _seat_nrm(u, q, nv=61):
    full, nrm = _seat_section(u, nv)
    f = (q * 0.5 + 0.5) * (len(full) - 1)
    i = min(max(int(f), 0), len(full) - 2)
    t = f - i
    nv2 = C.lerp(nrm[i][0], nrm[i + 1][0], t)
    nh2 = C.lerp(nrm[i][1], nrm[i + 1][1], t)
    l = math.hypot(nv2, nh2) or 1.0
    _p, _t3, n3 = _spine_frame(u)
    return (Vector((0.0, 1.0, 0.0)) * (nv2 / l) + n3 * (nh2 / l)).normalized()


# (u, q, half_len, half_wid, tangent) of the four harness slots.
U_SHOULDER = 0.790        # shoulder slot station: low enough that the strap
#                           can run down BEHIND the shell to the rear anchor
#                           without entering the head restraint (bottom 0.593)
U_SUBMARINE = 0.320
HARNESS_SLOTS = [
    (U_SHOULDER, +0.40, 0.0290, 0.0082, (0.0, 1.0, 0.0)),
    (U_SHOULDER, -0.40, 0.0290, 0.0082, (0.0, 1.0, 0.0)),
    (U_SUBMARINE, +0.26, 0.0250, 0.0078, (1.0, 0.0, 0.0)),
    (U_SUBMARINE, -0.26, 0.0250, 0.0078, (1.0, 0.0, 0.0)),
]
SLOT_CB = 0.0055          # counterbore radial step
SLOT_CBD = 0.0030         # counterbore depth


def _slot_frame(u, q):
    return _seat_pt(u, q, off=0.0002), _seat_nrm(u, q)


def _slot_cutter(cut, pos, nrm, tan, hl, hw):
    """Stepped prism: a counterbore for the grommet flange, then the slot
    proper, driven right through the shell so the hole is a real hole."""
    fo = _slotr(hl + SLOT_CB, hw + SLOT_CB, k=4.0)
    fi = _slotr(hl, hw, k=4.0)
    # +h runs OUTWARD along the seat's own normal, so the counterbore is at
    # -SLOT_CBD and the slot proper carries on to -0.040, well past the 6.2 mm
    # shell.  Getting this sign wrong cuts the whole slot at counterbore
    # diameter and leaves the boss standing in mid-air.
    _shape(cut, pos, nrm,
           [(0.0, 0.0120), (fo, 0.0120), (fo, -SLOT_CBD), (fi, -SLOT_CBD),
            (fi, -0.0400), (0.0, -0.0400)], seg=48, ref=tan)


def _slot_boss(acc, pos, nrm, tan, hl, hw, mat=0):
    """Bonded slot grommet: a CLOSED ring section (first ring == last ring, so
    no open boundary anywhere) seated in the counterbore, rolled over the hole
    edge and lining the bore.  Nothing here reaches outside the cut volume, so
    the boss never interpenetrates the shell it lines."""
    fL = _slotr(hl - 0.0006, hw - 0.0006, k=4.0)
    fI = _slotr(hl - 0.0022, hw - 0.0022, k=4.0)
    fO = _slotr(hl + SLOT_CB - 0.0006, hw + SLOT_CB - 0.0006, k=4.0)
    fM = _slotr(hl + 0.0034, hw + 0.0034, k=4.0)
    fN = _slotr(hl + 0.0008, hw + 0.0008, k=4.0)
    d = SLOT_CBD - 0.0004
    rings = [(fI, 0.0046), (fI, -0.0150), (fL, -0.0164), (fL, -d), (fO, -d),
             (fO, 0.0030), (fM, 0.0054), (fN, 0.0062), (fI, 0.0046)]
    _shape(acc, pos, nrm, rings, seg=48, mat=mat, ref=tan)


def _build_seat(acc, extra, cut, fix):
    nu, nv = 116, 61
    # Every station aft of the cut keeps the u it always had, so trimming the
    # nose cannot shift a single section of the shoulders, the harness slots or
    # the rolled rear edge - only the front cap is new.
    us = [U_SEAT_F] + [i / (nu - 1.0) for i in range(nu)
                       if i / (nu - 1.0) > U_SEAT_F + 0.0045]
    sec = []
    for u in us:
        p, _t, n = _spine_frame(u)
        yv = Vector((0.0, 1.0, 0.0))
        full, nrm = _seat_section(u, nv)
        top, bot = [], []
        for j in range(len(full)):
            v, h = full[j]
            nv2, nh2 = nrm[j]
            top.append(p + yv * v + n * h)
            bot.append(p + yv * (v - SHELL_T * nv2) + n * (h - SHELL_T * nh2))
        sec.append((top, bot))
    acc.loft(_shell_rings(sec, edge=4, er=0.0028), mat=0,
             closed=True, cap_start=True, cap_end=True)

    # D-CI24: the tray floor is now 77 mm lower, so four 10 mm pillars would
    # have read as stilts over an empty bathtub.  Two moulded longitudinal
    # beams stand on the floor rails and carry the pan instead.
    for sgn in (1, -1):
        n_b = 30
        rows_t, rows_b = [], []
        zb = Z_FLOOR + SKIN_T + 0.0121
        u_b0 = max(0.115, U_SEAT_F + 0.008)
        for i in range(n_b):
            u = C.lerp(u_b0, 0.665, i / (n_b - 1.0))
            p = _seat_pt(u, sgn * 0.36, off=-SHELL_T)
            yc = sgn * min(abs(p.y), 0.0800)
            ends = min(1.0, min(i, n_b - 1 - i) / 2.5)
            w = 0.0128 * (0.52 + 0.48 * ends)
            zt = max(zb + 0.004, p.z + 0.0012)
            rows_t.append([Vector((p.x, yc - w, zt)),
                           Vector((p.x, yc + w, zt))])
            rows_b.append([Vector((p.x, yc - w, zb)),
                           Vector((p.x, yc + w, zb))])
        extra.loft(_shell_rings([(rows_t[i], rows_b[i]) for i in range(n_b)],
                                edge=3, er=0.0022),
                   mat=0, closed=True, cap_start=True, cap_end=True)
        for k in range(4):
            u = C.lerp(max(0.155, u_b0 + 0.030), 0.625, k / 3.0)
            p = _seat_pt(u, sgn * 0.36, off=-SHELL_T)
            _cap_screw(fix, (p.x, sgn * min(abs(p.y), 0.0800), zb - 0.0026),
                       (0, 0, -1), r=0.0040, h=0.0028, mat=0)

    for (u, q, hl, hw, tan) in HARNESS_SLOTS:
        pos, nn = _slot_frame(u, q)
        _slot_cutter(cut, pos, nn, Vector(tan), hl, hw)
        _slot_boss(extra, pos, nn, Vector(tan), hl, hw, mat=0)

    for sgn in (1, -1):
        u, q = 0.920, sgn * 0.80
        p0 = _seat_pt(u, q)
        p1 = _seat_pt(u - 0.050, q)
        nn = _seat_nrm(u, q)
        _tube(extra, [p0, (p0 + p1) * 0.5 + nn * 0.0195, p1], 0.0030,
              seg=10, mat=0)


def _build_seat_pads(acc):
    for (u0, u1, pitch, qmax) in ((0.030, 0.400, 0.0520, 0.80),
                                  (0.475, 0.968, 0.0540, 0.78)):
        arc_len = _spine_arc(u1) - _spine_arc(u0)
        nu = max(38, int(arc_len / 0.0028))
        # same trick as the shell: only the nose station is new (D-CI34)
        ucut = max(u0, U_PAD_F)
        us = [ucut] + [C.lerp(u0, u1, i / (nu - 1.0)) for i in range(nu)
                       if C.lerp(u0, u1, i / (nu - 1.0)) > ucut + 0.0035]
        nv = 69
        sec = []
        for i, u in enumerate(us):
            rib = 0.5 - 0.5 * math.cos(TAU * _spine_arc(u) / pitch)
            ends = min(1.0, min(i, len(us) - 1 - i) / (len(us) * 0.085))
            top, bot = [], []
            for j in range(nv):
                q = C.lerp(-qmax, qmax, j / (nv - 1.0))
                base = _seat_pt(u, q, off=0.0010)
                nn = _seat_nrm(u, q)
                t = abs(q) / qmax
                side = 1.0 - 0.62 * max(0.0, (t - 0.70) / 0.30) ** 1.3
                # D-CI22: at 7x the insert was still one 300 mm smooth black
                # face.  Quilt channels plus a perforation dimple grid, both
                # sampled at >=3 points per period so they survive shading.
                qv = q * _seat_w(u) * qmax
                arcv = _spine_arc(u)
                quilt = (0.0026
                         * (0.5 - 0.5 * math.cos(TAU * arcv / 0.0235))
                         * (0.5 - 0.5 * math.cos(TAU * qv / 0.0240)))
                perf = (0.0009
                        * (0.5 - 0.5 * math.cos(TAU * arcv / 0.0118))
                        * (0.5 - 0.5 * math.cos(TAU * qv / 0.0120)))
                pad = ((0.0250 - 0.0034 * rib - quilt - perf) * side
                       * (0.22 + 0.78 * ends))
                top.append(base + nn * pad)
                bot.append(base)
            sec.append((top, bot))
        acc.loft(_shell_rings(sec, edge=4, er=0.0030), mat=0,
                 closed=True, cap_start=True, cap_end=True)


def _build_leg_pad(acc, fix):
    """Padded leg trough covering the tray floor forward of the seat pan."""
    x0, x1 = 0.5340, X_DASH_B - 0.016
    nu, nv = 44, 62
    sec = []
    for i in range(nu):
        t = i / (nu - 1.0)
        x = C.lerp(x0, x1, t)
        y1, _z1 = _wall_yz(x, 1.0)
        hw = max(0.045, y1 * 0.90)
        ends = min(1.0, min(t, 1.0 - t) / 0.10)
        top, bot = [], []
        for j in range(nv):
            q = C.lerp(-1.0, 1.0, j / (nv - 1.0))
            y = q * hw
            ch = 0.0
            for cc in (-0.46, 0.46):
                d = (q - cc) / 0.30
                if abs(d) < 1.0:
                    ch -= 0.0034 * (0.5 + 0.5 * math.cos(math.pi * d))
            crest = 0.0048 * max(0.0, 1.0 - (abs(q) / 0.17) ** 2)
            side = 1.0 - 0.55 * max(0.0, (abs(q) - 0.80) / 0.20) ** 1.2
            quilt = (0.0022 * (0.5 - 0.5 * math.cos(TAU * x / 0.0240))
                     * (0.5 - 0.5 * math.cos(TAU * y / 0.0245))
                     + 0.0008 * (0.5 - 0.5 * math.cos(TAU * x / 0.0120))
                     * (0.5 - 0.5 * math.cos(TAU * y / 0.0122)))
            pad = (0.0150 + ch + crest - quilt) * side * (0.25 + 0.75 * ends)
            top.append(Vector((x, y, Z_FLOOR + SKIN_T + max(0.0020, pad))))
            bot.append(Vector((x, y, Z_FLOOR + SKIN_T)))
        sec.append((top, bot))
    acc.loft(_shell_rings(sec, edge=3, er=0.0024), mat=0,
             closed=True, cap_start=True, cap_end=True)
    for i in range(2):
        for sgn in (1, -1):
            x = C.lerp(x0 + 0.020, x1 - 0.020, float(i))
            y1, _z1 = _wall_yz(x, 1.0)
            _cap_screw(fix, (x, sgn * y1 * 0.66, Z_FLOOR + SKIN_T + 0.0044),
                       (0, 0, 1), r=0.0038, h=0.0026, mat=0)


# =========================================================================== #
# 4.  head restraint + FIA side head protection
# =========================================================================== #

HR_X_BACK = -0.1400
HR_TOP = 0.7220
HR_BOT = 0.5930
HR_W = 0.1580
HR_CZ = 0.6640


def _hr_front(y, z):
    ty = min(1.0, abs(y) / HR_W)
    tz = (z - HR_CZ) / 0.0900
    cy = 1.0 - math.sqrt(max(0.0, 1.0 - ty * ty))
    cz = 1.0 - math.sqrt(max(0.0, 1.0 - min(1.0, tz * tz)))
    return -0.0480 + 0.0520 * cy + 0.0270 * cz


_VW = [i / 32.0 for i in range(33)]
_RW_Y = [0.006 + 0.011 * i for i in range(17)]
_RW_GRID = None


def _rear_wall_x_raw(y):
    """(z, x) polyline down the tray's rear wall at half width |y|."""
    zs, xs = [], []
    ay = abs(y)
    for v in _VW:
        kx = _kx(v)
        target = ay / max(_ky_at(-0.05, v), 1e-6)
        lo, hi = -0.1680, 0.1150
        if _ap_hw(hi) <= target:
            xr = hi
        else:
            for _ in range(24):
                mid = 0.5 * (lo + hi)
                if _ap_hw(mid) < target:
                    lo = mid
                else:
                    hi = mid
            xr = 0.5 * (lo + hi)
        xs.append(AP_XC + (xr - AP_XC) * kx)
        zs.append(C.lerp(_rim_z(xr), Z_FLOOR, _ez(v)))
    return zs, xs


def _rear_wall_x(y, z):
    """x of the tray's rear wall at (|y|, z), so parts can sit against it."""
    global _RW_GRID
    if _RW_GRID is None:
        _RW_GRID = [_rear_wall_x_raw(yy) for yy in _RW_Y]
    ay = min(max(abs(y), _RW_Y[0]), _RW_Y[-1])
    f = (ay - _RW_Y[0]) / (_RW_Y[1] - _RW_Y[0])
    i = min(int(f), len(_RW_Y) - 2)
    t = f - i

    def at(k):
        zs, xs = _RW_GRID[k]
        if z >= zs[0]:
            return xs[0]
        if z <= zs[-1]:
            return xs[-1]
        for j in range(len(zs) - 1):
            if zs[j] >= z >= zs[j + 1]:
                s = (zs[j] - z) / max(zs[j] - zs[j + 1], 1e-9)
                return xs[j] + (xs[j + 1] - xs[j]) * s
        return xs[-1]
    return C.lerp(at(i), at(i + 1), t)


def _hr_back(y, z):
    """Rear face of the head restraint.

    D-CI10: this used to be a fixed formula in y alone; below the coaming it
    put the pad up to 100 mm behind the tray's rear wall, so the bottom of the
    headrest hung through the back of the cockpit.  It now follows the wall.
    """
    ay = abs(y)
    base = (HR_X_BACK if ay <= 0.055 else
            HR_X_BACK + 0.0880 * ((ay - 0.055) / (HR_W - 0.055)) ** 1.6)
    if z < 0.6440:
        base = max(base, _rear_wall_x(y, z) + 0.0105)
    return base


def _hr_hw(z):
    t = (z - HR_BOT) / (HR_TOP - HR_BOT)
    return HR_W * (0.90 + 0.24 * math.sin(math.pi * min(1.0, max(0.0, t))) - 0.13 * t)


# (y, z) of the eight vent bores.  All eight are clear of the transverse cover
# seam at z=0.656 and of the fore-aft crown seam at y=0, so the boolean that
# opens them never has to cut through another shell.
HR_VENTS = [(0.032, 0.698), (-0.032, 0.698), (0.092, 0.698), (-0.092, 0.698),
            (0.058, 0.660), (-0.058, 0.660), (0.118, 0.660), (-0.118, 0.660)]
HR_SEAM_Z = 0.6270
VENT_R = 0.0125           # clear bore
VENT_CB = 0.0175          # counterbore that seats the grommet flange


def _build_headrest(acc, extra, cut, fix):
    nz, ny = 62, 58
    rings = []
    for i in range(nz):
        t = i / (nz - 1.0)
        z = C.lerp(HR_BOT, HR_TOP, t)
        edge = min(1.0, min(t, 1.0 - t) / 0.085)
        shrink = 0.0120 * (1.0 - math.sqrt(max(0.0, edge)))
        hw = max(0.006, _hr_hw(z) - shrink)
        ring = []
        for j in range(ny):
            y = -hw + 2.0 * hw * j / (ny - 1.0)
            dim = 0.00085 * (0.5 - 0.5 * math.cos(TAU * y / 0.0240)) \
                * (0.5 - 0.5 * math.cos(TAU * z / 0.0235))
            ring.append((_hr_front(y, z) + shrink * 0.5 + dim, y, z))
        for j in range(ny - 2, 0, -1):
            y = -hw + 2.0 * hw * j / (ny - 1.0)
            ring.append((_hr_back(y, z) - shrink * 0.5, y, z))
        rings.append(ring)
    acc.loft(rings, mat=0, closed=True, cap_start=True, cap_end=True)

    # moulded cover seam right round the pad
    seam = []
    zs = HR_SEAM_Z
    for i in range(58):
        t = i / 57.0
        y = C.lerp(-_hr_hw(zs) * 0.94, _hr_hw(zs) * 0.94, t)
        seam.append(Vector((_hr_front(y, zs) - 0.0016, y, zs)))
    for i in range(1, 57):
        t = 1.0 - i / 57.0
        y = C.lerp(-_hr_hw(zs) * 0.94, _hr_hw(zs) * 0.94, t)
        seam.append(Vector((_hr_back(y, zs) + 0.0016, y, zs)))
    seam.append(seam[0])
    _tube(acc, seam, 0.0016, seg=8, mat=0, caps=False)
    # bonded plaque, below the cover seam and clear of the vent field
    _plate(acc, (_hr_front(0.0, 0.6090) + 0.0009, 0.0, 0.6090),
           (1.0, 0.0, 0.16), (0, 1, 0), 0.0250, 0.0086, 0.0050, 0.0014, mat=0)
    # fore-aft cover seam over the crown
    crown = []
    for i in range(30):
        t = i / 29.0
        z = C.lerp(0.6220, HR_TOP - 0.0035, t)
        crown.append(Vector((_hr_front(0.0, z) - 0.0014, 0.0, z)))
    for i in range(1, 24):
        t = i / 23.0
        z = C.lerp(HR_TOP - 0.0035, 0.6220, t)
        crown.append(Vector((_hr_back(0.0, z) + 0.0014, 0.0, z)))
    _tube(acc, crown, 0.0014, seg=8, mat=0, caps=True)
    # D-CI25: these were a bore solid dropped INTO the pad while the pad's own
    # face stayed shut, so every one rendered as a crescent moulding around a
    # solid disc of foam.  The pad is now actually cut (stepped cutter below,
    # applied as a boolean at build time) and a closed grommet ring is welded
    # into the counterbore afterwards.
    for (yy, zz) in HR_VENTS:
        xf = _hr_front(yy, zz)
        n = (-1.0, 0.0, 0.0)
        _shape(cut, (xf, yy, zz), n,
               [(0.0, -0.0090), (VENT_CB, -0.0090), (VENT_CB, 0.0020),
                (VENT_R, 0.0020), (VENT_R, 0.0230), (0.0, 0.0230)],
               seg=40, mat=0)
        _shape(extra, (xf, yy, zz), n,
               [(0.0118, 0.0016), (0.0171, 0.0016), (0.0171, -0.0020),
                (0.0158, -0.0040), (0.0134, -0.0048), (0.0118, -0.0038),
                (0.0115, -0.0014), (0.0115, 0.0104), (0.0118, 0.0116),
                (0.0121, 0.0104), (0.0121, 0.0016), (0.0118, 0.0016)],
               seg=40, mat=0)

    for (yy, zz) in ((0.082, 0.690), (-0.082, 0.690), (0.100, 0.648),
                     (-0.100, 0.648)):
        xb = _hr_back(yy, zz)
        _cap_screw(fix, (xb - 0.0008, yy, zz), (-1.0, 0.0, 0.0),
                   r=0.0060, h=0.0040, mat=0)
    # webbing pull tabs
    for sgn in (1, -1):
        a = Vector((_hr_front(sgn * 0.126, 0.7040) + 0.003, sgn * 0.126, 0.7040))
        pts = [a, a + Vector((0.019, sgn * 0.006, 0.0085)),
               a + Vector((0.030, sgn * 0.002, -0.0050)),
               a + Vector((0.016, sgn * -0.004, -0.0130))]
        sm = [Vector(q) for q in C.catmull_rom([tuple(q) for q in pts], 22)]
        sec = []
        for i, q in enumerate(sm):
            e = min(1.0, min(i, len(sm) - 1 - i) / 2.0)
            sd = Vector((0.0, 1.0, 0.0))
            up = Vector((0.42, 0.0, 0.91)).normalized()
            hwid = 0.0090 * (0.5 + 0.5 * e)
            sec.append(([q + sd * hwid + up * 0.0009, q - sd * hwid + up * 0.0009],
                        [q + sd * hwid - up * 0.0009, q - sd * hwid - up * 0.0009]))
        acc.loft(_shell_rings(sec, edge=2, er=0.0008), mat=0,
                 closed=True, cap_start=True, cap_end=True)


def _build_side_head(acc, fix):
    """Two padded wedges on the coaming, each on a bolted carbon base."""
    for sgn in (1, -1):
        xs = [C.lerp(-0.0620, 0.1900, i / 31.0) for i in range(32)]
        sec = []
        for i, x in enumerate(xs):
            t = i / (len(xs) - 1.0)
            yt, zt = _rim_top(x)
            y_out = sgn * (yt - 0.0040)
            y_in = sgn * (yt - 0.0560 - 0.0110 * math.sin(math.pi * t))
            ztop = zt + 0.0780 * (0.35 + 0.65 * math.sin(math.pi * min(1.0, t * 1.25)))
            ends = min(1.0, min(t, 1.0 - t) / 0.10)
            n = 16
            top, bot = [], []
            for j in range(n):
                s = j / (n - 1.0)
                y = C.lerp(y_in, y_out, s)
                zb = C.lerp(zt + 0.0035, zt - 0.0035, s)
                zc = C.lerp(ztop, zt + 0.0110, s ** 1.7)
                top.append(Vector((x, y, C.lerp(zb, zc, ends))))
                bot.append(Vector((x, y, zb - 0.0032)))
            sec.append((top, bot))
        acc.loft(_shell_rings(sec, edge=3, er=0.0030), mat=0,
                 closed=True, cap_start=True, cap_end=True)
        seam = []
        for i, x in enumerate(xs):
            t = i / (len(xs) - 1.0)
            yt, zt = _rim_top(x)
            ends = min(1.0, min(t, 1.0 - t) / 0.10)
            y = sgn * (yt - 0.0300 - 0.0055 * math.sin(math.pi * t))
            ztop = zt + 0.0780 * (0.35 + 0.65 * math.sin(math.pi * min(1.0, t * 1.25)))
            seam.append(Vector((x, y, C.lerp(zt + 0.0035, ztop * 0.985, ends))))
        _tube(acc, seam, 0.0014, seg=8, mat=0, caps=True)
        for k in range(4):
            x = C.lerp(-0.0400, 0.1650, k / 3.0)
            yt, zt = _rim_top(x)
            _dzus(fix, (x, sgn * (yt - 0.0180), zt + 0.0030), (0.0, 0.0, 1.0),
                  (1.0, 0.0, 0.0), r=0.0058, mat=0)


# =========================================================================== #
# 5.  dash bulkhead, steering column stub, footwell tunnel, pedals
# =========================================================================== #

DASH_T = X_DASH_F - X_DASH_B
# Footwell aperture: a scaled-down copy of the tunnel mouth (FOOT[0]) so the
# tunnel's own rim is always hidden behind the panel and the driver looks
# straight down the tunnel through the hole.
HOLE_CZ = 0.5040
HOLE_HW = 0.0840
HOLE_HH = 0.0250
HOLE_K = 3.4

# ---- steering column -------------------------------------------------------
# MEASURED off the built steering_wheel.py, not guessed.  Its MW places the
# wheel centre at (0.50, 0, 0.50) with a 22 deg rake, so the QR axis runs
# (0.92718, 0, -0.37461) forwards; the male QR spline (r 0.0192 + 2.6 mm teeth)
# occupies wheel-local z -0.0478..-0.0652, i.e. world (0.5443,0,0.4821) to
# (0.5605,0,0.4756).  The column therefore has to arrive on THAT axis and
# present a female socket, and it crosses the dash plane at z=0.4475 - which is
# only possible now the tray floor sits at 0.403 instead of 0.472.
COL_C = (0.5000, 0.0, 0.5000)
COL_FWD = (0.927184, 0.0, -0.374607)     # unit, wheel -> dash
COL_END_L = 0.0500        # wheel-local depth of the column's end face
COL_SOCK_R = 0.0212       # socket bore root radius (wheel spline max 0.0205)

# ===== JOINT CONTRACT with steering_wheel.py - DO NOT MOVE THESE ============
# D-CI35.  Audit ranks 7 and 8 (SW_QRBody front face 2.973 mm off this socket's
# end face; SW_QRSpline floating 1.225 mm inside this bore) were closed from the
# WHEEL side, against the numbers below, and steering_wheel.py now states the
# same three stations back at us.  Shrinking this bore or shifting COL_END_L
# "to close the gap" would double-fix it and drive the wheel's hub through the
# socket, so both values are frozen.  Measured with the pair built in one file:
#
#   socket mouth / end face   wheel-local z = -0.0500   (s = 50.000 mm)
#                             car-local (0.546359, 0.0, 0.481270)
#                             assembled  (0.546359, 0.0, 0.821270)
#   mouth end annulus         r 21.2 .. 25.2 mm
#   bore, swept round the QR axis in _shape's own frame:
#                             r(t) = 21.2 + 1.3 * (0.5 + 0.5 cos(15 (t - 18 deg))) mm
#                             15 crests at 21.2 mm on t = 6 + 24k deg
#                             15 grooves at 22.5 mm on t = 18 + 24k deg
#   bore depth                wheel-local z -0.0500 .. -0.0662 (16.2 mm)
#
#   -> SW_QRBody seats its 24.0 mm land on a face at z = -0.0502, 0.2 mm inside
#      the mouth: nearest surface 0.200 mm, 742 overlapping triangles.
#   -> SW_QRSpline tips 23.0 mm bite 0.5 mm into the 22.5 mm grooves, clocked
#      +6 deg: nearest surface 0.015 mm, 179 overlapping triangles, 15.2 mm of
#      engagement.
# ===========================================================================


def _col_pt(local_z):
    """World point on the steering axis at wheel-local z (negative = forwards)."""
    return Vector(COL_C) - Vector(COL_FWD) * local_z


COL_Z_DASH = (Vector(COL_C) + Vector(COL_FWD)
              * ((X_DASH_B - COL_C[0]) / COL_FWD[0])).z


def _plate(acc, pos, nrm, tan, hw, hh, rad, t, mat=0, n=64, cham=0.0009):
    u, w, n3 = _basis(nrm, tan)
    p = _v(pos)
    k = 2.0 + 4.0 * (1.0 - min(1.0, rad / max(hw, hh)))

    def mkring(sx, sy, h):
        ring = []
        for i in range(n):
            a = TAU * i / n
            ca, sa = math.cos(a), math.sin(a)
            rr = ((abs(ca) / max(sx, 1e-5)) ** k + (abs(sa) / max(sy, 1e-5)) ** k) ** (-1.0 / k)
            q = p + u * (rr * ca) + w * (rr * sa) + n3 * h
            ring.append((q.x, q.y, q.z))
        return ring

    r0 = mkring(hw, hh, 0.0)
    r1 = mkring(hw, hh, t - cham)
    r2 = mkring(hw - cham, hh - cham, t)
    acc.loft([r0, r1, r2], mat=mat, closed=True, cap_start=True, cap_end=True)


def _resample_by_angle(loop, cx, cy, n):
    """Star-shaped resample of a closed (y, z) loop at n uniform angles.

    D-CI26: this used to fall back to a hard-coded r=0.05 whenever a ray found
    no intersection, and _dash_loops then called it with a centre 36 mm ABOVE
    the footwell slot, so 77 of 128 samples took the fallback and the 'slot'
    came out as a 136 x 74 mm blob with a perfect 50 mm arc on top.  A missing
    intersection now means the centre is not inside the loop, which is a bug in
    the caller, so say so instead of inventing a radius.
    """
    m = len(loop)
    out = []
    for i in range(n):
        a = TAU * i / n
        dx, dy = math.cos(a), math.sin(a)
        best = None
        for k in range(m):
            y0, z0 = loop[k]
            y1, z1 = loop[(k + 1) % m]
            ey, ez = y1 - y0, z1 - z0
            den = dx * ez - dy * ey
            if abs(den) < 1e-12:
                continue
            t = ((y0 - cx) * ez - (z0 - cy) * ey) / den
            if t <= 1e-9:
                continue
            s = (dx * (z0 - cy) - dy * (y0 - cx)) / (-den)
            if -1e-6 <= s <= 1.0 + 1e-6 and (best is None or t < best):
                best = t
        if best is None:
            raise ValueError(
                f"_resample_by_angle: centre ({cx:.4f}, {cy:.4f}) is not "
                f"inside the loop - no hit at {math.degrees(a):.1f} deg")
        out.append((cx + dx * best, cy + dy * best))
    return out


def _hole_loop(n, cz=None, hw=None, hh=None):
    """The footwell aperture, sampled at n uniform angles about its OWN centre.

    Both this and the panel outline run angle 0..TAU in the same direction from
    the same y=0 start, so lofting outline[i] -> hole[i] gives a clean web.
    """
    cz = HOLE_CZ if cz is None else cz
    hw = HOLE_HW if hw is None else hw
    hh = HOLE_HH if hh is None else hh
    out = []
    for i in range(n):
        a = TAU * i / n
        ca, sa = math.cos(a), math.sin(a)
        rad = ((abs(ca) / hw) ** HOLE_K
               + (abs(sa) / hh) ** HOLE_K) ** (-1.0 / HOLE_K)
        out.append((rad * ca, HOLE_CZ + rad * sa))
    return out


def _dash_loops(n=128):
    inner = _liner_half(X_DASH_F + 0.004)
    loop = [(-p[0], p[1]) for p in reversed(inner[1:])] + list(inner)
    top = loop[-1]
    loop = loop + [(C.lerp(top[0], -top[0], k / 9.0), top[1]) for k in range(1, 9)]
    loop = [(p[0] * 0.988, p[1] - 0.0004) for p in loop]
    # Resample the outline about the HOLE's centre so the two loops share a
    # star centre and the web between them cannot fold back on itself.
    outer = _resample_by_angle(loop, 0.0, HOLE_CZ, n)
    return outer, _hole_loop(n), HOLE_CZ


def _build_dash(acc, fix):
    outer, hole, cz = _dash_loops()
    x = X_DASH_F
    zt = _rim_top(X_DASH_B)[1]

    def ring(l2, dx, sc=None):
        if sc is None:
            return [(x + dx, p[0], p[1]) for p in l2]
        return [(x + dx, (p[0]) * sc, HOLE_CZ + (p[1] - HOLE_CZ) * sc) for p in l2]

    o_f, o_b = ring(outer, 0.0), ring(outer, -DASH_T)
    h_f, h_b = ring(hole, 0.0), ring(hole, -DASH_T)
    h_r1 = ring(hole, -DASH_T - 0.0045, 1.032)
    h_r2 = ring(hole, -DASH_T - 0.0095, 1.062)
    acc.loft([o_f, h_f], mat=0, closed=True)
    acc.loft([o_b, h_b], mat=0, closed=True)
    acc.loft([o_f, o_b], mat=0, closed=True)
    acc.loft([h_f, h_b, h_r1, h_r2], mat=0, closed=True)

    # ---- dash furniture ------------------------------------------------- #
    # D-CI27: every one of these used to be built at x >= X_DASH_F + 2.6 mm
    # with a +X normal, i.e. on the face that points into the footwell tunnel
    # and the nose.  The driver sits at x < 0.63 and looks at the REAR face, so
    # they now sit at X_DASH_B - d with a -X normal.  xb/nb below are the only
    # two things that decide it; nothing here may use `x` (= X_DASH_F) again.
    xb = X_DASH_B
    nb = (-1.0, 0.0, 0.0)
    # D-CI12: the panel is short, so the switchgear rides the flanks; it now
    # also has to clear the footwell aperture (z 0.473..0.525 at |y|<0.086).
    zsw = min(zt - 0.0230, HOLE_CZ + HOLE_HH + 0.0300)
    zpl = min(zt - 0.0330, HOLE_CZ + HOLE_HH + 0.0180)
    for sgn in (1, -1):
        _plate(acc, (xb - 0.0026, sgn * 0.0940, zpl),
               nb, (0, 1, 0), 0.0250, 0.0125, 0.0055, 0.0050, mat=0)
        for k in range(3):
            _shape(acc, (xb - 0.0072,
                         sgn * 0.0940 + C.lerp(-0.0140, 0.0140, k / 2.0), zpl),
                   nb,
                   [(0.0, 0.0), (0.0056, 0.0), (0.0056, 0.0042),
                    (0.0046, 0.0052), (0.0046, 0.0084), (0.0036, 0.0094),
                    (0.0, 0.0094)], seg=16, mat=1)
    # master switch (car's left) and extinguisher T-handle (car's right)
    _shape(acc, (xb - 0.0072, -0.0430, zsw), nb,
           [(0.0, 0.0), (0.0104, 0.0), (0.0104, 0.0034), (0.0092, 0.0044),
            (0.0092, 0.0080), (0.0076, 0.0094), (0.0, 0.0096)], seg=22, mat=2)
    hy, hz = 0.0430, zsw
    _shape(acc, (xb - 0.0026, hy, hz), nb,
           [(0.0, 0.0), (0.0108, 0.0), (0.0108, 0.0038), (0.0088, 0.0050),
            (0.0088, 0.0074), (0.0, 0.0074)], seg=20, mat=2)
    _tube(acc, [Vector((xb - 0.0074, hy, hz)), Vector((xb - 0.0245, hy, hz))],
          0.0032, seg=12, mat=2)
    _tube(acc, [Vector((xb - 0.0240, hy - 0.0135, hz)),
                Vector((xb - 0.0240, hy + 0.0135, hz))], 0.0040, seg=12, mat=2)
    # loom connectors low on the flanks, beside the column bearing carrier
    for sgn in (1, -1):
        _plate(acc, (xb - 0.0026, sgn * 0.0550, COL_Z_DASH + 0.0085),
               nb, (0, 1, 0), 0.0145, 0.0110, 0.0070, 0.0020, mat=1)
    # D-CI09: the perimeter screws used to sit on a fixed ellipse about the
    # panel centre; at the bottom that put them 21 mm BELOW the tray floor,
    # hanging in space under the bulkhead.  They now ride the panel's own
    # outline, inset 9 mm.
    for k in range(14):
        i = int(round(k * len(outer) / 14.0)) % len(outer)
        py, pz = outer[i]
        d = math.hypot(py, pz - cz) or 1.0
        f = max(0.0, 1.0 - 0.0090 / d)
        _cap_screw(fix, (xb - 0.0028, py * f, cz + (pz - cz) * f), nb,
                   r=0.0038, h=0.0026, mat=0)


def _angled_boss(acc, base_p, base_n, tip_p, tip_n, r0, r1, steps=7, seg=32,
                 mat=0):
    """Loft from a ring lying flat on one plane to a ring square to another.

    The column axis is raked 22 deg, so a disc perpendicular to it can never sit
    flush on the vertical dash face - it either floats on one edge or buries the
    other in the laminate.  This grows the carrier's base out of the panel
    instead."""
    bn = _v(base_n).normalized()
    tn = _v(tip_n).normalized()
    rings = []
    for i in range(steps + 1):
        t = i / steps
        n = (bn * (1.0 - t) + tn * t).normalized()
        c = _v(base_p) * (1.0 - t) + _v(tip_p) * t
        r = C.lerp(r0, r1, t)
        u, w, _n3 = _basis(n, (0.0, 1.0, 0.0))
        rings.append([tuple(c + u * (r * math.cos(TAU * k / seg))
                            + w * (r * math.sin(TAU * k / seg)))
                      for k in range(seg)])
    acc.loft(rings, mat=mat, closed=True)
    return rings


def _build_column(acc, fix):
    """Column stub on the steering wheel's own axis, ending in a female QR
    socket that the wheel's male spline plugs into.

    D-CI28: the old stub ran from (0.630, 0.532) to (0.556, 0.500) - DESCENDING
    towards the driver at -23 deg - and finished in a 20 mm MALE spline.  The
    wheel's QR is a 38.4 mm male spline on an axis RISING at +22 deg towards the
    driver, so the two could never mate: 45 deg apart and 25 mm out in z.
    """
    p_bulk = _col_pt((X_DASH_B - COL_C[0]) / -COL_FWD[0])
    p_end = _col_pt(-COL_END_L)
    ax = (p_end - p_bulk).normalized()
    L = (p_end - p_bulk).length

    u, w, _n = _basis(ax)
    # Bearing carrier, flange seated ON the bulkhead's rear face (h=0 is exactly
    # X_DASH_B): the panel is solid at the column's height, so a carrier that
    # started 5.5 mm forward would have buried its flange inside the laminate.
    h0 = 0.0130
    _angled_boss(acc, (X_DASH_B - 0.0004, 0.0, COL_Z_DASH), (-1.0, 0.0, 0.0),
                 p_bulk + ax * h0, ax, 0.0300, 0.0238, mat=0)
    _shape(acc, p_bulk + ax * h0, ax,
           [(0.0, 0.0), (0.0238, 0.0), (0.0238, 0.0046), (0.0216, 0.0058),
            (0.0176, 0.0058), (0.0176, 0.0140), (0.0156, 0.0152),
            (0.0128, 0.0152), (0.0128, 0.0)], seg=32, mat=0)
    for k in range(6):
        a = TAU * k / 6.0 + 0.26
        _cap_screw(fix, p_bulk + ax * (h0 + 0.0002) + u * (0.0202 * math.cos(a))
                   + w * (0.0202 * math.sin(a)), ax, r=0.0032, h=0.0022, mat=0)
    # rubber gaiter over the bearing
    rings = []
    for i in range(23):
        t = i / 22.0
        h = 0.0292 + t * 0.0166
        rr = 0.0128 + 0.0038 * (0.5 - 0.5 * math.cos(TAU * t * 3.0))
        rings.append([tuple(p_bulk + ax * h + u * (rr * math.cos(TAU * k / 26.0))
                            + w * (rr * math.sin(TAU * k / 26.0)))
                      for k in range(26)])
    acc.loft(rings, mat=1, closed=True)
    # shaft with a machined step
    _shape(acc, p_bulk + ax * 0.0400, ax,
           [(0.0, 0.0), (0.0118, 0.0), (0.0118, 0.0090), (0.0104, 0.0102),
            (0.0104, 0.0170), (0.0, 0.0170)], seg=24, mat=0)
    # quick-release collar with six drive pins
    hcol = 0.0570
    _shape(acc, p_bulk + ax * hcol, ax,
           [(0.0, 0.0), (0.0206, 0.0), (0.0206, 0.0116), (0.0184, 0.0128),
            (0.0104, 0.0128), (0.0104, 0.0)], seg=30, mat=2)
    base = p_bulk + ax * (hcol + 0.0128)

    # female QR socket: 15 internal splines, bore root 21.2 mm radius so the
    # wheel's 20.5 mm crest slides in with 0.7 mm of clearance.
    def spl(a):
        return COL_SOCK_R + 0.0013 * (0.5 + 0.5 * math.cos(a * 15.0))
    hs = L - (hcol + 0.0128)
    _shape(acc, base, ax,
           [(0.0, 0.0), (0.0180, 0.0), (0.0268, 0.0042), (0.0268, hs - 0.0022),
            (0.0252, hs), (spl, hs), (spl, 0.0042), (0.0, 0.0022)],
           seg=90, mat=0)


# D-CI29: the tunnel used to dive from z=0.498 at the mouth to a 0.284 centre
# by x=1.03, which drove its whole lower half through MB_chassis_cockpit's tub
# floor (z=0.3704) and through MB_cell_bulkhead - 818 face pairs.  Ray-casting
# the built monocoque_b for the largest inscribed superellipse at each station
# shows the free interior forward of the front bulkhead is centred near z=0.44
# and is 0.27-0.34 half width; the tunnel now stays inside that corridor and is
# wider and flatter, which is also what a real footwell looks like.
FOOT = [
    (0.6465, 0.0000, 0.5040, 0.0900, 0.0290),
    (0.7000, 0.0000, 0.4980, 0.0930, 0.0320),
    (0.7600, 0.0000, 0.4830, 0.1010, 0.0410),
    (0.8000, 0.0000, 0.4650, 0.1400, 0.0700),
    (0.8700, 0.0000, 0.4450, 0.1850, 0.0930),
    (0.9600, 0.0000, 0.4350, 0.2050, 0.0980),
    (1.0700, 0.0000, 0.4250, 0.2000, 0.0930),
]
FOOT_K = 2.6


def _foot_at(t):
    """(centre, half width, half height) along the footwell tunnel."""
    n = len(FOOT) - 1
    f = t * n
    i = min(int(f), n - 1)
    s = f - i
    a, b = FOOT[i], FOOT[i + 1]
    return (Vector((C.lerp(a[0], b[0], s), 0.0, C.lerp(a[2], b[2], s))),
            C.lerp(a[3], b[3], s), C.lerp(a[4], b[4], s))


def _foot_t_at_x(x):
    """Invert the station table: x -> t."""
    n = len(FOOT) - 1
    if x <= FOOT[0][0]:
        return 0.0
    if x >= FOOT[-1][0]:
        return 1.0
    for i in range(n):
        if FOOT[i][0] <= x <= FOOT[i + 1][0]:
            s = (x - FOOT[i][0]) / (FOOT[i + 1][0] - FOOT[i][0])
            return (i + s) / n
    return 1.0


def _foot_sec_at_x(x):
    c, hw, hh = _foot_at(_foot_t_at_x(x))
    return c.z, hw, hh


def _foot_dz(x, y):
    """Half height of the tunnel at station x and offset y (0 outside)."""
    cz, hw, hh = _foot_sec_at_x(x)
    t = min(1.0, abs(y) / hw)
    return hh * max(0.0, 1.0 - t ** FOOT_K) ** (1.0 / FOOT_K)


def _foot_lo(x, y):
    """z of the tunnel's inner floor at (x, y)."""
    cz, _hw, _hh = _foot_sec_at_x(x)
    return cz - _foot_dz(x, y)


def _build_footwell(acc, fix):
    rings = []
    n = 46
    for i in range(n):
        t = i / (n - 1.0)
        c, hw, hh = _foot_at(t)
        k = 3.4 if t < 0.08 else 2.6
        ring = []
        for j in range(64):
            a = TAU * j / 64.0
            ca, sa = math.cos(a), math.sin(a)
            rad = ((abs(ca) / hw) ** k + (abs(sa) / hh) ** k) ** (-1.0 / k)
            ring.append((c.x, rad * ca, c.z + rad * sa))
        rings.append(ring)
    c, _hw, _hh = _foot_at(1.0)
    last = rings[n - 1]
    for s in (0.985, 0.930, 0.780, 0.480):
        rings.append([(c.x + 0.0095 * (1.0 - s) / 0.52, y * s, c.z + (z - c.z) * s)
                      for (_x, y, z) in last])
    acc.loft(rings, mat=0, closed=True, cap_end=True)

    def _foot_rad(hw, hh, a, k=2.6):
        ca, sa = math.cos(a), math.sin(a)
        return ((abs(ca) / hw) ** k + (abs(sa) / hh) ** k) ** (-1.0 / k)

    # hoop frames
    for t in (0.56, 0.74, 0.90):
        c, hw, hh = _foot_at(t)
        rings2 = []
        for dx, gr in ((-0.0070, 1.000), (-0.0040, 1.026), (0.0040, 1.026),
                       (0.0070, 1.000)):
            ring = []
            for j in range(64):
                a = TAU * j / 64.0
                r = _foot_rad(hw, hh, a)
                ring.append((c.x + dx, r * math.cos(a) * gr,
                             c.z + r * math.sin(a) * gr))
            rings2.append(ring)
        acc.loft(rings2, mat=0, closed=True)
        for k in range(8):
            a = TAU * k / 8.0 + 0.4
            r = _foot_rad(hw, hh, a) * 1.026
            nn = Vector((0.0, -math.cos(a), -math.sin(a))).normalized()
            _rivet(fix, Vector((c.x, r * math.cos(a), c.z + r * math.sin(a)))
                   + nn * 0.0004, nn, r=0.0018, mat=1)

    # longitudinal stringers - four bonded top-hat sections down the tunnel
    for a0 in (0.62, math.pi - 0.62, math.pi + 0.62, -0.62):
        rows_t, rows_b = [], []
        for i in range(26):
            t = 0.46 + 0.50 * i / 25.0
            c, hw, hh = _foot_at(t)
            ends = min(1.0, min(i, 25 - i) / 3.0)
            row_t, row_b = [], []
            for da in (-0.075, -0.048, 0.048, 0.075):
                a = a0 + da
                r = _foot_rad(hw, hh, a)
                nn = Vector((0.0, math.cos(a), math.sin(a))).normalized()
                base = Vector((c.x, r * math.cos(a), c.z + r * math.sin(a)))
                lift = 0.0036 if abs(da) < 0.06 else 0.0006
                row_t.append(base + nn * (lift * (0.25 + 0.75 * ends)))
                row_b.append(base - nn * 0.0004)
            rows_t.append(row_t)
            rows_b.append(row_b)
        acc.loft(_shell_rings([(rows_t[i], rows_b[i]) for i in range(26)],
                              edge=2, er=0.0010),
                 mat=0, closed=True, cap_start=True, cap_end=True)

    # inspection panel on the tunnel roof
    rows_t, rows_b = [], []
    for i in range(14):
        t = 0.56 + 0.28 * i / 13.0
        c, hw, hh = _foot_at(t)
        et = min(1.0, min(i, 13 - i) / 2.0)
        row_t, row_b = [], []
        for j in range(10):
            a = math.pi * 0.5 + C.lerp(-0.52, 0.52, j / 9.0)
            ej = min(1.0, min(j, 9 - j) / 1.6)
            r = _foot_rad(hw, hh, a)
            nn = Vector((0.0, math.cos(a), math.sin(a))).normalized()
            base = Vector((c.x, r * math.cos(a), c.z + r * math.sin(a)))
            row_t.append(base + nn * (0.0010 + 0.0028 * min(et, ej)))
            row_b.append(base + nn * 0.0006)
        rows_t.append(row_t)
        rows_b.append(row_b)
    acc.loft(_shell_rings([(rows_t[i], rows_b[i]) for i in range(14)],
                          edge=2, er=0.0011),
             mat=0, closed=True, cap_start=True, cap_end=True)
    for i in range(4):
        for j in (0, 1):
            t = 0.575 + 0.25 * i / 3.0
            c, hw, hh = _foot_at(t)
            a = math.pi * 0.5 + (-0.44 if j == 0 else 0.44)
            r = _foot_rad(hw, hh, a)
            nn = Vector((0.0, math.cos(a), math.sin(a))).normalized()
            _dzus(fix, Vector((c.x, r * math.cos(a), c.z + r * math.sin(a)))
                  + nn * 0.0044, nn, Vector((1.0, 0.0, 0.0)), r=0.0050, mat=0)


PED_X0, PED_X1 = 0.8700, 1.0600      # pedal rail span
PED_RAIL_Y = 0.0720
PED_RAIL_W = 0.0105


def _ped_plate_z():
    """Top of the pedal-box mounting plate.

    D-CI30: the box used to be pinned to a hard-coded zf=0.183, which put 212
    of its 6472 vertices OUTSIDE the tunnel - the deepest 57 mm below the belly,
    in free air.  It now stands on the tunnel's own inner floor: the rails sit
    1.5 mm above _foot_lo() at their outboard edge and the plate rides on top.
    """
    zb = max(_foot_lo(PED_X0, PED_RAIL_Y + PED_RAIL_W),
             _foot_lo(PED_X0, PED_RAIL_Y - PED_RAIL_W))
    return zb + 0.0015 + 0.0250


def _build_pedals(acc, fix):
    x0, x1 = PED_X0, PED_X1
    zp = _ped_plate_z()

    # wedge rails: bottom on the tunnel floor, top flat at the plate
    for sgn in (1, -1):
        yy = sgn * PED_RAIL_Y
        w = PED_RAIL_W
        n = 16
        rows_t, rows_b = [], []
        for i in range(n):
            x = C.lerp(x0, x1, i / (n - 1.0))
            zb = max(_foot_lo(x, abs(yy) + w),
                     _foot_lo(x, abs(yy) - w)) + 0.0015
            rows_t.append([Vector((x, yy - w, zp)), Vector((x, yy + w, zp))])
            rows_b.append([Vector((x, yy - w, zb)), Vector((x, yy + w, zb))])
        acc.loft(_shell_rings([(rows_t[i], rows_b[i]) for i in range(n)],
                              edge=2, er=0.0020),
                 mat=0, closed=True, cap_start=True, cap_end=True)

    nx, ny = 14, 10
    sec = []
    for i in range(nx):
        x = C.lerp(x0 + 0.020, x1 - 0.015, i / (nx - 1.0))
        top, bot = [], []
        for j in range(ny):
            y = C.lerp(-0.0900, 0.0900, j / (ny - 1.0))
            top.append(Vector((x, y, zp + 0.0055)))
            bot.append(Vector((x, y, zp)))
        sec.append((top, bot))
    acc.loft(_shell_rings(sec, edge=2, er=0.0020), mat=0,
             closed=True, cap_start=True, cap_end=True)
    for i in range(4):
        for sgn in (1, -1):
            _cap_screw(fix, (C.lerp(x0 + 0.040, x1 - 0.035, i / 3.0),
                             sgn * PED_RAIL_Y, zp + 0.0057), (0, 0, 1),
                       r=0.0040, h=0.0028, mat=0)

    for (sgn, fw, fh) in ((1, 0.0400, 0.0400), (-1, 0.0320, 0.0330)):
        yc = sgn * 0.0500
        piv = Vector((1.0250, yc, zp + 0.0150))
        top = Vector((0.9680, yc, piv.z + 0.1072))
        _tube(acc, [piv, piv.lerp(top, 0.5), top], 0.0084, seg=16, mat=0)
        _shape(acc, piv + Vector((0, -0.0170, 0)), (0, 1, 0),
               [(0.0, 0.0), (0.0155, 0.0), (0.0155, 0.0070), (0.0118, 0.0082),
                (0.0118, 0.0258), (0.0155, 0.0270), (0.0155, 0.0340),
                (0.0, 0.0340)], seg=22, mat=0)
        _cap_screw(fix, piv + Vector((0, 0.0184, 0)), (0, 1, 0), r=0.0055,
                   h=0.0036, mat=0)

        d = (top - piv).normalized()
        face_n = Vector((-d.z, 0.0, d.x)).normalized()
        nu, nv2 = 48, 18
        sec = []
        for i in range(nu):
            t = i / (nu - 1.0)
            arc = C.lerp(0.028, 0.028 + 2.0 * fh, t)
            c = piv + d * arc
            ends = min(1.0, min(t, 1.0 - t) / 0.055)
            top_r, bot_r = [], []
            for j in range(nv2):
                s = j / (nv2 - 1.0)
                q = c + Vector((0.0, C.lerp(-fw, fw, s), 0.0))
                serr = 0.0009 * (0.5 - 0.5 * math.cos(TAU * arc / 0.0075))
                side = min(1.0, min(s, 1.0 - s) / 0.10)
                top_r.append(q + face_n * (0.0078 + (0.0034 + serr)
                                           * (0.25 + 0.75 * min(ends, side))))
                bot_r.append(q + face_n * 0.0072)
            sec.append((top_r, bot_r))
        acc.loft(_shell_rings(sec, edge=3, er=0.0017), mat=0,
                 closed=True, cap_start=True, cap_end=True)

        mc = Vector((1.0780, yc, piv.z + 0.0330))
        _shape(acc, mc, (-1, 0, 0),
               [(0.0, 0.0), (0.0185, 0.0), (0.0185, 0.0055), (0.0150, 0.0066),
                (0.0150, 0.0500), (0.0122, 0.0516), (0.0122, 0.0575),
                (0.0, 0.0575)], seg=26, mat=1)
        nose = mc - Vector((0.0575, 0.0, 0.0))
        rodp = piv + d * 0.0720
        _tube(acc, [rodp, rodp.lerp(nose, 0.55), nose], 0.0040, seg=12, mat=1)
        _shape(acc, nose + Vector((0.0085, 0.0, 0.0)), (-1, 0, 0),
               [(0.0, 0.0), (0.0082, 0.0), (0.0082, 0.0060), (0.0068, 0.0072),
                (0.0, 0.0072)], seg=14, mat=1)
        res = mc - Vector((0.0280, 0.0, 0.0)) + Vector((0.0, 0.0, 0.0260))
        _shape(acc, res, (0, 0, 1),
               [(0.0, 0.0), (0.0100, 0.0), (0.0114, 0.0050), (0.0114, 0.0290),
                (0.0092, 0.0312), (0.0054, 0.0320), (0.0054, 0.0356),
                (0.0, 0.0356)], seg=20, mat=1)
        _tube(acc, [res, res + Vector((0.0055, sgn * 0.0045, -0.0120)),
                    mc - Vector((0.0215, 0.0, 0.0)) + Vector((0.0, 0.0, 0.0055))],
              0.0030, seg=10, mat=1)
        spr = []
        for k in range(40):
            tt = k / 39.0
            b = piv + d * C.lerp(0.020, 0.058, tt)
            spr.append(b + Vector((0.0, sgn * 0.0210, 0.0))
                       + face_n * (0.0054 * math.cos(TAU * 5.0 * tt))
                       + Vector((0.0, 0.0054 * math.sin(TAU * 5.0 * tt), 0.0)))
        _tube(acc, spr, 0.0010, seg=8, mat=1)

    sec = []
    for i in range(8):
        x = C.lerp(0.9800, 1.0400, i / 7.0)
        top, bot = [], []
        for j in range(8):
            y = C.lerp(-0.0165, 0.0165, j / 7.0)
            top.append(Vector((x, y, zp + 0.0090)))
            bot.append(Vector((x, y, zp + 0.0055)))
        sec.append((top, bot))
    acc.loft(_shell_rings(sec, edge=2, er=0.0014), mat=1,
             closed=True, cap_start=True, cap_end=True)

    # Self-check: every pedal-box vertex must lie inside the tunnel's own
    # superellipse.  This is the exact test the reviewer failed the part on, so
    # the build refuses to emit geometry that would fail it again.
    worst, at = 0.0, None
    for (px, py, pz) in acc.v:
        cz, hw, hh = _foot_sec_at_x(px)
        if not (FOOT[0][0] <= px <= FOOT[-1][0]):
            continue
        f = (abs(py) / hw) ** FOOT_K + (abs(pz - cz) / hh) ** FOOT_K
        if f > worst:
            worst, at = f, (px, py, pz)
    if worst > 1.0:
        raise ValueError(f"pedal box breaks out of the footwell tunnel: "
                         f"f={worst:.3f} at {at}")


# =========================================================================== #
# 6.  six-point harness
# =========================================================================== #

WEB_T = 0.0016


def _webbing(acc, ctrl, half_w, mat=0, pu=0.0092, pv=0.0030,
             aw=0.00021, af=0.00009, nv=None, step=0.0030):
    """Ribbon with modelled warp ribs, weft float and selvedge edges.

    ctrl: list of (x, y, z, nx, ny, nz).  The normal is splined with the
    centreline so the strap twists smoothly instead of flipping.
    """
    pts = C.catmull_rom(ctrl, 24)
    L = 0.0
    for i in range(1, len(pts)):
        L += math.dist(pts[i][:3], pts[i - 1][:3])
    pts = C.catmull_rom(ctrl, max(24, int(L / step)))
    if nv is None:
        nv = min(62, max(18, int(2.0 * (half_w - 0.0011) / (pv / 3.0))))

    pv_list = [Vector(p[:3]) for p in pts]
    nv_list = [(Vector(p[3:6]).normalized() if Vector(p[3:6]).length > 1e-9
                else Vector((0, 0, 1))) for p in pts]

    sec = []
    arc = 0.0
    er = 0.0011
    a = half_w - er
    for i in range(len(pv_list)):
        if i > 0:
            arc += (pv_list[i] - pv_list[i - 1]).length
        if i == 0:
            t = pv_list[1] - pv_list[0]
        elif i == len(pv_list) - 1:
            t = pv_list[-1] - pv_list[-2]
        else:
            t = pv_list[i + 1] - pv_list[i - 1]
        t = t.normalized()
        n = nv_list[i] - t * nv_list[i].dot(t)
        n = n.normalized() if n.length > 1e-9 else Vector((0, 0, 1))
        s = t.cross(n).normalized()
        ends = min(1.0, min(i, len(pv_list) - 1 - i) / 3.0)
        top, bot = [], []
        for j in range(nv):
            v = -a + 2.0 * a * j / (nv - 1.0)
            warp = aw * (0.5 - 0.5 * math.cos(TAU * v / pv))
            weft = af * math.cos(TAU * arc / pu + math.pi * v / pv)
            selv = 0.00022 if abs(v) > a - 0.0032 else 0.0
            crown = 0.00010 * (1.0 - (v / a) ** 2)
            h = (WEB_T * 0.5 + warp + weft + selv + crown) * (0.35 + 0.65 * ends)
            q = pv_list[i] + s * v
            top.append(q + n * h)
            bot.append(q - n * (WEB_T * 0.5 * (0.35 + 0.65 * ends)))
        sec.append((top, bot))
    acc.loft(_shell_rings(sec, edge=3, er=er), mat=mat,
             closed=True, cap_start=True, cap_end=True)


def _adjuster(acc, pos, nrm, wdir, half_w, mat=0):
    """Three-bar ladder-lock slider, aligned to the strap it grips."""
    u, w, _n = _basis(nrm, wdir)
    p = _v(pos)
    hw = half_w + 0.0052
    hl = 0.0195
    rr = 0.0025

    def frame_path(sx, sy):
        pts = []
        for i in range(45):
            a = TAU * i / 44.0
            ca, sa = math.cos(a), math.sin(a)
            rad = ((abs(ca) / sx) ** 5.0 + (abs(sa) / sy) ** 5.0) ** (-0.2)
            pts.append(p + u * (rad * ca) + w * (rad * sa))
        return pts

    _tube(acc, frame_path(hw, hl), rr, seg=12, mat=mat, caps=False)
    for dy in (-0.0064, 0.0064):
        _tube(acc, [p + u * (-hw + 0.0015) + w * dy,
                    p + u * (hw - 0.0015) + w * dy], rr * 0.86, seg=12,
              mat=mat, caps=True)


def _bartack(acc, pos, nrm, wdir, half_w, mat=0):
    u = _v(wdir).normalized()
    n = _v(nrm).normalized()
    t = u.cross(n).normalized()
    p = _v(pos)
    for k in range(7):
        v = C.lerp(-half_w * 0.80, half_w * 0.80, k / 6.0)
        _tube(acc, [p + u * v - t * 0.0055 + n * 0.0004,
                    p + u * v + t * 0.0055 + n * 0.0004],
              0.00045, seg=7, mat=mat, caps=True)


def _anchor_plate(acc, fix, pos, nrm, tan, mat=0):
    _plate(acc, pos, nrm, tan, 0.0265, 0.0170, 0.0110, 0.0038, mat=mat)
    u, _w, _n = _basis(nrm, tan)
    for k in (-1, 1):
        _cap_screw(fix, _v(pos) + u * (0.0185 * k) + _v(nrm).normalized() * 0.0040,
                   nrm, r=0.0042, h=0.0030, mat=0)


def _buckle(acc, pos, nrm, tan, angles, mat_metal=1, mat_red=2):
    """Central rotary buckle.

    D-CI16: the six tongue plates used to sit on fixed 60 deg spacing while the
    straps arrived at completely different angles, so at 7x zoom they read as
    little white slivers of paper poking out from under the body with no strap
    attached.  The tongues are now placed on the angles the webbing actually
    arrives from, and each one is long enough to be seen entering the body.
    """
    u, w, n = _basis(nrm, tan)
    p = _v(pos)
    R = 0.0300
    _shape(acc, p, n, [(0.0, -0.0092), (R * 0.86, -0.0092), (R, -0.0060),
                       (R, 0.0052), (R * 0.94, 0.0078), (R * 0.60, 0.0082),
                       (R * 0.60, 0.0094), (0.0, 0.0094)], seg=56,
           mat=mat_metal, ref=tan)
    for a in angles:
        d = u * math.cos(a) + w * math.sin(a)
        sd = d.cross(n)
        sec = []
        for i in range(8):
            q = p + d * C.lerp(R - 0.0105, R + 0.0012, i / 7.0)
            e = min(1.0, min(i, 7 - i) / 1.4)
            hwid = 0.0072 * (0.55 + 0.45 * e)
            th = 0.0021 * (0.45 + 0.55 * e)
            top = [q + sd * C.lerp(-hwid, hwid, j / 5.0) + n * th
                   for j in range(6)]
            bot = [q + sd * C.lerp(-hwid, hwid, j / 5.0) - n * th
                   for j in range(6)]
            sec.append((top, bot))
        acc.loft(_shell_rings(sec, edge=2, er=0.0009), mat=mat_metal,
                 closed=True, cap_start=True, cap_end=True)

    def knurl(a):
        return 0.0238 + 0.00030 * math.cos(a * 44.0)
    _shape(acc, p + n * 0.0084, n,
           [(0.0, 0.0), (0.0238, 0.0), (knurl, 0.0011), (knurl, 0.0080),
            (0.0222, 0.0095), (0.0170, 0.0102), (0.0, 0.0104)],
           seg=88, mat=mat_metal, ref=tan)
    # release indicator: a proud anodised disc on the cap
    _shape(acc, p + n * 0.0186, n,
           [(0.0, 0.0), (0.0176, 0.0), (0.0176, 0.0014), (0.0158, 0.0023),
            (0.0, 0.0025)], seg=44, mat=mat_red, ref=tan)
    for k in range(2):
        a = math.pi * k
        d = u * math.cos(a) + w * math.sin(a)
        sd = d.cross(n)
        sec = []
        for i in range(8):
            q = p + n * 0.0211 + d * C.lerp(0.0022, 0.0132, i / 7.0)
            hwid = C.lerp(0.0028, 0.0011, i / 7.0)
            sec.append(([q + sd * hwid + n * 0.0013, q - sd * hwid + n * 0.0013],
                        [q + sd * hwid, q - sd * hwid]))
        acc.loft(_shell_rings(sec, edge=2, er=0.0006), mat=mat_red,
                 closed=True, cap_start=True, cap_end=True)


def _build_harness(web, hw, fix):
    ub = 0.245
    n_b = _seat_nrm(ub, 0.0)
    b_pos = _seat_pt(ub, 0.0, off=0.0010 + 0.0250 + 0.0108)
    b_tan = Vector((1.0, 0.0, 0.0))
    A_SH, A_LAP, A_SUB = 0.60, 0.30, 0.92
    _buckle(hw, b_pos, n_b, b_tan,
            [math.pi * a for a in (A_SH, -A_SH, A_LAP, -A_LAP, A_SUB, -A_SUB)])

    def bn(a, r=0.0400):
        u, w, _n = _basis(n_b, b_tan)
        return b_pos + (u * math.cos(a) + w * math.sin(a)) * r - n_b * 0.0026

    def tail(a):
        """Last two control points: over the tongue, then dead under the
        buckle body where the end cap can never be seen."""
        return [tuple(bn(a, 0.0330) + n_b * 0.0044) + tuple(n_b),
                tuple(bn(a, 0.0090) - n_b * 0.0052) + tuple(n_b)]

    def sp(u, q, off):
        return tuple(_seat_pt(u, q, off=off)) + tuple(_seat_nrm(u, q))

    # ---- rear shoulder anchors on the tray's REAR wall --------------------- #
    # D-CI11: these used to be planted on a guessed plane 17 mm outside the
    # rear wall.  They now ride _rear_wall_x, and (D-CI31) the shoulder straps
    # actually terminate on them instead of stopping in mid-air.
    anchors = {}
    for sgn in (1, -1):
        yy, zz = sgn * 0.0850, 0.5220
        # _rear_wall_x is the MODELLED wall; the liner's 5.5 mm skin grows
        # inboard from it, and the plate's own corners sit 5.5 mm behind its
        # centre, so the plate has to stand 12 mm proud or it cuts the wall.
        pa = Vector((_rear_wall_x(yy, zz) + SKIN_T, yy, zz))
        d = Vector((1.0, 0.0, 0.34)).normalized()
        _anchor_plate(hw, fix, pa + d * 0.0062, d, Vector((0.0, 1.0, 0.0)))
        _eye_bolt(hw, pa + d * 0.0096, d, Vector((0.0, 1.0, 0.0)), r=0.0046,
                  mat=1)
        anchors[sgn] = (pa, d)

    # ---- shoulder straps -------------------------------------------------- #
    # D-CI31: both straps used to stop 48 mm past the slot boss, 9 mm off the
    # shell, with a visible cut end cap that was then buried inside the head
    # restraint (340 face pairs).  Each one now threads its slot - which is a
    # real hole since D-CI32 - runs down behind the shell and dies inside its
    # rear anchor plate, where no cap can be seen.
    for sgn in (1, -1):
        u_slot, q_slot = U_SHOULDER, sgn * 0.40
        pa, da = anchors[sgn]
        a_end = math.pi * (A_SH if sgn > 0 else -A_SH)
        ctrl = [
            tuple(pa + da * 0.0090) + tuple(da),
            tuple(pa + da * 0.0256) + tuple(da),
            sp(u_slot - 0.030, q_slot, -0.0250),
            sp(u_slot, q_slot, -0.0115),
            sp(u_slot, q_slot, 0.0050),
            sp(0.720, sgn * 0.395, 0.0290),
            sp(0.620, sgn * 0.375, 0.0288),
            sp(0.490, sgn * 0.330, 0.0295),
            sp(0.370, sgn * 0.250, 0.0300),
        ] + tail(a_end)
        _webbing(web, ctrl, 0.0235, mat=0)
        pb2 = _seat_pt(0.660, sgn * 0.385, off=0.0286)
        na = _seat_nrm(0.660, sgn * 0.385)
        ta = (_seat_pt(0.620, sgn * 0.380, off=0.0286) -
              _seat_pt(0.700, sgn * 0.390, off=0.0286)).normalized()
        _adjuster(hw, pb2, na, ta.cross(na).normalized(), 0.0235, mat=1)
        pb = _seat_pt(0.560, sgn * 0.352, off=0.0300)
        nb2 = _seat_nrm(0.560, sgn * 0.352)
        tb = (_seat_pt(0.520, sgn * 0.340, off=0.0300) -
              _seat_pt(0.600, sgn * 0.362, off=0.0300)).normalized()
        _bartack(hw, pb, nb2, tb.cross(nb2).normalized(), 0.0235, mat=1)

    # ---- lap straps ------------------------------------------------------- #
    for sgn in (1, -1):
        xa = 0.1200
        pw, nw = _wall_pt(xa, _wall_s_at_z(xa, 0.5180))
        pw = Vector((pw.x, sgn * pw.y, pw.z))
        nw = Vector((nw.x, sgn * nw.y, nw.z))
        _anchor_plate(hw, fix, pw + nw * 0.0016, nw, Vector((1.0, 0.0, 0.0)))
        _eye_bolt(hw, pw + nw * 0.0052, nw, Vector((0.0, 0.0, 1.0)), r=0.0050,
                  mat=1)
        a_end = math.pi * (A_LAP if sgn > 0 else -A_LAP)
        mid_n = (nw * 0.62 + Vector((0.0, 0.0, 0.78))).normalized()
        ctrl = [
            tuple(pw + nw * 0.0172) + tuple(nw),
            tuple(pw + nw * 0.0300 + Vector((0.014, 0.0, 0.004))) + tuple(mid_n),
            sp(0.410, sgn * 0.900, 0.0130),
            sp(0.340, sgn * 0.630, 0.0290),
            sp(0.282, sgn * 0.330, 0.0312),
        ] + tail(a_end)
        _webbing(web, ctrl, 0.0225, mat=0)
        pa = pw + nw * 0.0312 + Vector((0.018, 0.0, 0.005))
        ta = (Vector(ctrl[2][:3]) - Vector(ctrl[0][:3])).normalized()
        _adjuster(hw, pa, mid_n, ta.cross(mid_n).normalized(), 0.0225, mat=1)

    # ---- anti-submarine straps -------------------------------------------- #
    for sgn in (1, -1):
        u0, q0 = U_SUBMARINE, sgn * 0.26
        a_end = math.pi * (A_SUB if sgn > 0 else -A_SUB)
        # threads its slot too: the tail dies in the void under the pan, which
        # the seat itself hides from every camera angle
        ctrl = [
            sp(u0, q0, -0.0400),
            sp(u0, q0, -0.0130),
            sp(u0, q0, 0.0055),
            sp(u0 + 0.030, q0 * 0.92, 0.0230),
        ] + tail(a_end)
        _webbing(web, ctrl, 0.0195, mat=0)
        _bartack(hw, _seat_pt(u0 + 0.019, q0, off=0.0155),
                 _seat_nrm(u0 + 0.019, q0), Vector((0.0, 1.0, 0.0)), 0.0195,
                 mat=1)


# =========================================================================== #
# 7.  drink line, radio lead, wiring loom
# =========================================================================== #

def _p_clip(acc, fix, pos, nrm, tan, r=0.0038, mat=1):
    u, _w, n = _basis(nrm, tan)
    p = _v(pos)
    pts = [p + n * ((r + 0.0011) * math.cos(math.pi * 0.16 + TAU * 0.84 * i / 21.0))
           + u * ((r + 0.0011) * math.sin(math.pi * 0.16 + TAU * 0.84 * i / 21.0))
           for i in range(22)]
    _tube(acc, pts, 0.0010, seg=8, mat=mat, caps=True)
    _cap_screw(fix, p - n * (r + 0.0026), -n, r=0.0032, h=0.0022, mat=0)


def _build_lines(acc, fix):
    # drink line, car's right
    path = []
    for i in range(8):
        t = i / 7.0
        x = C.lerp(0.4600, -0.0400, t)
        z = C.lerp(0.5240, 0.5860, t ** 1.25)
        p, n = _wall_pt(x, _wall_s_at_z(x, z))
        path.append(Vector((p.x, -p.y, p.z)) + Vector((n.x, -n.y, n.z)) * 0.0138)
    path.append(Vector((-0.0760, -0.1120, 0.6220)))
    path.append(Vector((-0.0840, -0.1050, 0.6450)))
    sm = [Vector(q) for q in C.catmull_rom([tuple(p) for p in path], 80)]
    _tube(acc, sm, 0.0028, seg=12, mat=1)
    for k in (0.16, 0.46, 0.74):
        i = int(k * (len(sm) - 1))
        p = sm[i]
        _pw, n = _wall_pt(p.x, _wall_s_at_z(p.x, p.z))
        n = Vector((n.x, -n.y, n.z))
        _p_clip(acc, fix, p, n, Vector((1.0, 0.0, 0.0)), r=0.0028)
    end = sm[-1]
    d = (end - sm[-6]).normalized()
    _shape(acc, end - d * 0.0165, d,
           [(0.0, 0.0), (0.0058, 0.0), (0.0058, 0.0056), (0.0078, 0.0064),
            (0.0078, 0.0152), (0.0058, 0.0164), (0.0058, 0.0230),
            (0.0, 0.0230)], seg=18, mat=2)

    # coiled radio lead, car's left
    a0p, a0n = _wall_pt(0.2600, _wall_s_at_z(0.2600, 0.5100))
    a0 = a0p + a0n * 0.0300
    a1 = Vector((-0.0430, 0.0930, 0.6020))
    axis = a1 - a0
    ln = axis.length
    ad = axis.normalized()
    e1, e2, _e3 = _basis(ad)
    ns = int(220 * ln / 0.28) + 60
    coil = []
    for i in range(ns):
        t = i / (ns - 1.0)
        amp = 0.0122 * math.sin(math.pi * min(1.0, max(0.0, (t - 0.10) / 0.80))) ** 0.5
        a = TAU * 4.5 * t
        coil.append(a0 + ad * (ln * t) + e1 * (amp * math.cos(a))
                    + e2 * (amp * math.sin(a)))
    _tube(acc, [a0 - ad * 0.026] + coil + [a1 + ad * 0.020], 0.0022, seg=10,
          mat=1)
    _shape(acc, a0 - ad * 0.026, -ad,
           [(0.0, 0.0), (0.0068, 0.0), (0.0068, 0.0068), (0.0086, 0.0078),
            (0.0086, 0.0168), (0.0068, 0.0180), (0.0, 0.0182)], seg=18, mat=2)
    _shape(acc, a1 + ad * 0.020, ad,
           [(0.0, 0.0), (0.0064, 0.0), (0.0064, 0.0056), (0.0082, 0.0066),
            (0.0082, 0.0146), (0.0064, 0.0158), (0.0, 0.0160)], seg=18, mat=2)


def _build_loom(acc, fix):
    for sgn in (1, -1):
        path = []
        for i in range(9):
            t = i / 8.0
            x = C.lerp(0.5700, -0.1000, t)
            z = C.lerp(0.5480, 0.5560, t) + 0.016 * math.sin(math.pi * t)
            p, nn = _wall_pt(x, _wall_s_at_z(x, z))
            p = Vector((p.x, sgn * p.y, p.z))
            nn = Vector((nn.x, sgn * nn.y, nn.z))
            path.append(p + nn * 0.0148)
        sm = [Vector(q) for q in C.catmull_rom([tuple(p) for p in path], 70)]
        _tube(acc, sm, 0.0080, seg=14, mat=0)
        for k in (0.12, 0.36, 0.60, 0.86):
            i = int(k * (len(sm) - 1))
            p = sm[i]
            _pw, nn = _wall_pt(p.x, _wall_s_at_z(p.x, p.z))
            nn = Vector((nn.x, sgn * nn.y, nn.z))
            _p_clip(acc, fix, p, nn, Vector((1.0, 0.0, 0.0)), r=0.0080, mat=1)
        for k in (0.26, 0.70):
            i = int(k * (len(sm) - 1))
            p = sm[i]
            _pw, nn = _wall_pt(p.x, _wall_s_at_z(p.x, p.z))
            nn = Vector((nn.x, sgn * nn.y, nn.z))
            d = (nn * 0.55 + Vector((0.0, 0.0, -0.83))).normalized()
            _tube(acc, [p, p + d * 0.024,
                        p + d * 0.044 + Vector((0.010, 0, -0.008))],
                  0.0036, seg=10, mat=0)
            _shape(acc, p + d * 0.0055, d,
                   [(0.0, 0.0), (0.0066, 0.0), (0.0066, 0.0100),
                    (0.0044, 0.0124), (0.0, 0.0126)], seg=14, mat=1)


# =========================================================================== #
# build
# =========================================================================== #

def build(coll, ctx=None):
    objs = []
    fix = _Acc()
    hw = _Acc()

    acc = _Acc()
    _build_liner(acc, fix)
    ob = _emit(P + "liner", acc, coll, ["CarbonMatte"], smooth=34.0)
    C.add_solidify(ob, thickness=0.0055, offset=-1.0)
    C.add_bevel(ob, width=0.0011, segments=2, angle=42.0)
    objs.append(ob)

    acc = _Acc()
    _build_sip(acc, fix)
    objs.append(_emit(P + "sip", acc, coll, ["CarbonMatte"], smooth=32.0))

    acc, extra, cut = _Acc(), _Acc(), _Acc()
    _build_seat(acc, extra, cut, fix)
    ob = _emit(P + "seat", acc, coll, ["CarbonMatte"], smooth=36.0)
    _cut_and_weld(ob, coll, cut, extra, smooth=36.0)
    objs.append(ob)

    acc = _Acc()
    _build_seat_pads(acc)
    _build_leg_pad(acc, fix)
    objs.append(_emit(P + "seatpad", acc, coll, ["SuedeGrip"], smooth=40.0))

    acc, extra, cut = _Acc(), _Acc(), _Acc()
    _build_headrest(acc, extra, cut, fix)
    ob = _emit(P + "headrest", acc, coll, ["SuedeGrip"], smooth=34.0)
    _cut_and_weld(ob, coll, cut, extra, smooth=34.0)
    objs.append(ob)

    acc = _Acc()
    _build_side_head(acc, fix)
    objs.append(_emit(P + "sidehead", acc, coll, ["SuedeGrip"], smooth=34.0))

    acc = _Acc()
    _build_dash(acc, fix)
    objs.append(_emit(P + "dash", acc, coll,
                      ["CarbonMatte", "MatteBlack", "AnodisedRed"], smooth=32.0))

    acc = _Acc()
    _build_column(acc, fix)
    objs.append(_emit(P + "column", acc, coll,
                      ["Titanium", "MatteBlack", "AnodisedRed"], smooth=34.0))

    acc = _Acc()
    _build_footwell(acc, fix)
    objs.append(_emit(P + "footwell", acc, coll, ["CarbonMatte"], smooth=34.0))

    acc = _Acc()
    _build_pedals(acc, fix)
    objs.append(_emit(P + "pedals", acc, coll,
                      ["CarbonMatte", "Titanium"], smooth=34.0))

    web = _Acc()
    _build_harness(web, hw, fix)
    objs.append(_emit(P + "harness_web", web, coll, ["SuedeGrip"], smooth=44.0))
    objs.append(_emit(P + "harness_hw", hw, coll,
                      ["CarbonMatte", "SteelFastener", "AnodisedRed"],
                      smooth=32.0))

    acc = _Acc()
    _build_lines(acc, fix)
    _build_loom(acc, fix)
    objs.append(_emit(P + "lines", acc, coll,
                      ["MatteBlack", "MatteBlack", "SteelFastener"], smooth=36.0))

    acc = _Acc()
    _build_seal(acc)
    objs.append(_emit(P + "seal", acc, coll, ["MatteBlack"], smooth=40.0))

    _build_coaming_fix(fix)
    objs.append(_emit(P + "fixings", fix, coll,
                      ["SteelFastener", "MatteBlack"], smooth=28.0))

    return objs


# =========================================================================== #
# DEFECTS - found by rendering, fixed, and confirmed by re-rendering the SAME
# view or crop.  Every entry below was measured or seen, not assumed.
# =========================================================================== #
#
# D-CI01  The whole interior was built as a real 0.50 m deep survival cell with
#         its floor at z=0.118.  Ray-casting the built monocoque_b showed its
#         cockpit throat bottoms out in a CAPPED floor at z=0.4601 with side
#         walls at 0.2067/0.2017/0.1887/0.1684 half-width (z=0.610/0.550/0.490/
#         0.470 at x=+0.20).  340 mm of this part ran straight through it.
#         Rebuilt as a tray fitted inside the measured throat (KTAB).
#         Confirmed: tools/pv.sh r3_c / r3_top, and the clearance table below.
# D-CI02  Seat was 0.19 half-width in a 0.227 tub with 45 mm of air under it -
#         the cockpit read as an empty bathtub.  Seat widened to fill the tray,
#         pan extended forward, leg-trough pad added.  Confirmed: r2_c.
# D-CI03  Seat bolsters used a smoothstep starting at t=0.60, which printed a
#         crease and a sheet-metal "wing" at the shoulders.  Replaced by an
#         explicit 8-point section with a rolled crest (_seat_prof).
# D-CI04  _plate() collapsed its top ring to 2 % scale, leaving a 64-gon
#         micro-pole in the middle of every plate.  Flat n-gon caps instead.
# D-CI05  3-bar adjusters were oriented off a fixed axis and sat at ~60 deg to
#         the strap they grip.  They now take the strap's own width vector.
# D-CI06  Pedal faces sat 4.2 mm off the arm centreline, i.e. buried inside an
#         8.8 mm radius tube - the whole pedal face was invisible.
# D-CI07  Head-restraint vent bores were built with the profile inverted: each
#         one was a 3 mm domed BOSS, not a hole.  Now 19 mm grommeted bores.
#         Confirmed: z2 crop at 7x.
# D-CI09  Dash perimeter screws rode a fixed ellipse and ended up 21 mm below
#         the tray floor, hanging in space.  They now ride the panel outline.
# D-CI10  _hr_back() was a function of y alone; below the coaming it put the
#         pad up to 100 mm behind the tray's rear wall.  It now follows the
#         wall (_rear_wall_x).  Measured: -99.6 mm -> +6.7 mm.
# D-CI11  Rear shoulder anchors were planted on a guessed plane, 17 mm outside
#         the rear wall.  They now ride the wall via _wall_pt.
# D-CI12  The dash panel is only 115 mm tall.  A centred switch strip plus a
#         43 mm doubler ring round the column overran the top edge and the
#         footwell mouth.  Switchgear moved to the flanks, doubler deleted.
# D-CI13  A uniform scale of the aperture closes in slower than the real throat
#         behind the driver: at (x=-0.045, z=0.495) the lining sat 3.5 mm
#         THROUGH the measured wall.  _ky_at() adds a depth-weighted rear taper.
# D-CI14  The coiled radio lead swung 14.5 mm about an axis only 9 mm off the
#         wall, so half of every turn was outside the tub (-12.8 mm).
# D-CI15  At 7x the foam inserts were one featureless 300 mm black face.
#         Quilt + perforation relief and the SuedeGrip nap.  Confirmed: z6 8x.
# D-CI16/19  Buckle tongues sat on fixed 60 deg spacing while the straps
#         arrived at other angles, and stuck 12.5 mm clear of the body - at 7x
#         they read as jagged white slivers of paper.  Tongues now sit on the
#         actual strap angles and barely clear the slot mouth.
# D-CI17  Head restraint and side head pads were the two largest untextured
#         surfaces left.  Suede nap, moulded cover seams, bonded plaque,
#         webbing pull tabs (they were bent wire before).  Confirmed: z2 7x.
# D-CI18/21  Recessing the red release indicator into the knurled cap buried it
#         twice over - the buckle rendered as a plain chrome pill.  It is now a
#         proud chamfered disc with the arrows on top.  Confirmed: z1d 7x.
# D-CI20  The crown of the head restraint was still one smooth 180 x 130 mm
#         face; moulded dimple relief plus a fore-aft cover seam.
# D-CI22  Strap tails ended in mid-air over the seat pad with visible cut caps.
#         They now die under the buckle body where the cap cannot be seen.
#         Confirmed: z1d 7x, same crop as z1.
#
#
# ---- round 2 (2026-07-25) -------------------------------------------------
# Every one of these was measured against the CURRENTLY built monocoque_b and
# steering_wheel, fixed, and re-measured / re-rendered on the SAME pinned
# camera (tools/pv.sh --centre 0.47 0 0.47 --radius 0.70).
#
# D-CI23  The header's "MEASURED" landing was stale.  monocoque_b's cockpit no
#         longer caps at z=0.4601: MB_cell_floor tops out at 0.3949 and the
#         cell stringers/fixings at 0.4292.  Z_FLOOR 0.4720 -> 0.4030, and
#         KTAB refitted from 40 stations x 17 depths of ray-cast wall.  CI x
#         monocoque_b overlaps 1118 -> 494.
# D-CI24  With the floor 69 mm lower the four 10 mm seat pillars would have been
#         stilts over an empty tub; replaced by two moulded subframe beams that
#         stand on the floor rails.
# D-CI25  Head-restraint vent bores were STILL not holes (D-CI07 recurring): a
#         bore solid pushed into a pad whose face was never opened, so each one
#         rendered as a crescent moulding round a solid disc.  The pad is now
#         cut by a real boolean at build time (stepped cutter -> 12.5 mm bore in
#         a 17.5 mm counterbore) and a closed grommet ring is welded in after.
#         Ray down every bore: no hit at the face, first hit 23 mm inside.
# D-CI26  _dash_loops resampled the footwell slot about cz=0.5245, 36 mm ABOVE
#         it, so 77 of 128 samples took _resample_by_angle's hard-coded r=0.05
#         fallback and the "156 x 30 slot" came out as a 136 x 74 blob with a
#         50 mm arc on top, while the designed slot stayed SOLID.  The hole is
#         now generated at its own centre and the fallback raises instead of
#         inventing a radius.  Ray +x at z=0.504: passes through from y=0 to
#         y=0.083 and is stopped at 0.090.
# D-CI27  All dash furniture (2 switch plates + 6 buttons, master switch,
#         extinguisher T-handle, 2 loom connectors, 14 perimeter screws) was
#         built on the FORWARD face pointing into the footwell; from outside the
#         car you saw the whole switchgear array.  It is now on X_DASH_B with a
#         -X normal, where the driver is.  Confirmed: V3 before/after.
# D-CI28  The column could not mate with the wheel: it descended at -23 deg to a
#         20 mm MALE spline while steering_wheel's QR is a 38.4 mm male spline
#         on an axis rising at +22 deg.  The column is now built on the wheel's
#         own axis through (0.50,0,0.50) and ends in a 15-tooth FEMALE socket.
#         Measured: 15.2 mm of spline engagement, 0 overlapping triangles.
# D-CI29  The footwell tunnel dived to z=0.284 and drove its lower half through
#         the tub floor and the cell bulkhead.  Re-routed through the corridor
#         found by inscribing superellipses in ray-cast free space; wider and
#         flatter, and the only monocoque contact left is the 42 mm bulkhead
#         pass-through at x 0.654-0.696.
# D-CI30  212 of 6472 pedal-box vertices hung OUT of the tunnel, the worst 57 mm
#         below the belly in free air.  The box now stands on _foot_lo(), the
#         tunnel's own inner floor, and build() refuses to emit it otherwise.
#         Measured: 0 vertices outside, worst superellipse f = 0.963.
# D-CI31  Both shoulder straps stopped in mid-air 48 mm past the boss with a cut
#         end cap buried in the head restraint (340 face pairs).  They now
#         thread the slot, run down behind the shell and die inside the rear
#         anchor plates.  CI_headrest x CI_harness_web: 340 -> 0.
# D-CI32  The four harness slots were fake - 5 mm blind pockets in raised bosses
#         that also left 352 open boundary edges.  The shell is now boolean-cut
#         and the boss is a closed ring seated in a counterbore.  48-ray grid
#         per slot: 0/48 clear before, 48/48 and 43/48 clear after; CI_seat
#         non-manifold edges 352 -> 0.
# D-CI33  The column's splined end was buried 6.5 mm in the leg-trough pad.
#         CI_seatpad x CI_column: 104 -> 0.
#
#
# ---- round 3 (2026-07-25, connection audit) --------------------------------
#
# D-CI34  Audit rank 2, hero-visible: the seat and its foam were driven straight
#         THROUGH the steering wheel.  SPINE[0] put the pan's nose at x=0.5300,
#         z=0.5065 - 30 mm forward of the wheel centre and 6 mm above it - so the
#         pan and the 25 mm insert on top of it crossed the wheel as a horizontal
#         sheet at wheel-local b -0.026..+0.028 over the FULL a = +-0.140 width:
#         the pad sliced the left grip, buried the lower button row and hid the
#         whole rotary array in top-down and high front-quarter.
#         Measured before (both modules built in one file, BVHTree.overlap):
#             SW_Shell x CI_seat 2118 | x CI_seatpad 1667 | SW_GripL/R x CI_seat
#             890 each | x CI_seatpad 864 each | SW_HubPlate x CI_seat 447 ...
#             17257 triangle pairs over 42 SW_/CI_ object pairs.
#         Every SW_ vertex, car-local: the wheel occupies x 0.4398..0.5669,
#         |y| <= 0.1401, z 0.4069..0.5964.  It is a raked disc whose bottom rim
#         is 1.6 mm off the tray floor skin at x=0.469 and whose top is at
#         x=0.530 - there is no room over it, none under it, and lowering the
#         seat cannot help, so the pan has to stop BEHIND it.  Shell and pan
#         insert are now cut at X_SEAT_F=0.4335 via _spine_u_at_x (U_SEAT_F,
#         U_PAD_F); the insert keeps its original 0.030 setback and every station
#         aft of the cut keeps the u it always had, so nothing but the nose moved.
#         Measured after: CI_seat max x 0.5323 -> 0.4351 (4.7 mm clear of the
#         wheel), SW_ x CI_seat 0 pairs, SW_ x CI_seatpad 0 pairs, and the
#         unrelated CI x CI counts are unchanged (headrest x seat 1044 -> 1044,
#         seat x sip 750 -> 750, liner x seat 720 -> 720).
#         Confirmed by render on a pinned camera, before/after: top-down
#         az0/el84 and front-quarter az34/el38 at centre (0.44,0,0.50).
# D-CI35  Audit ranks 7/8 (the QR joint) were closed from the steering_wheel
#         side against this file's existing socket - see the JOINT CONTRACT
#         above.  Re-measured here, not assumed: SW_QRBody x CI_column
#         2.973 mm -> 0.200 mm with 742 overlapping triangles, SW_QRSpline x
#         CI_column 1.225 mm -> 0.015 mm with 179.  Nothing in CI_column changed
#         and nothing in it may change without re-clocking the wheel's spline.
#
# Final measured state (build/parts + monocoque_b + steering_wheel in one file):
#     CI x monocoque_b        494 pairs, all CI_footwell x MB_chassis_cockpit
#                             in x 0.654-0.696 (bulkhead pass-through, hidden)
#     CI x steering_wheel     10 object pairs, and only two kinds left:
#                             (a) the QR mate - SW_QRBody 742 + SW_QRSpline 179
#                                 tri pairs into CI_column, which IS the joint
#                                 (0.200 / 0.015 mm, D-CI35), and
#                             (b) 1676 pairs into CI_liner + 391 into CI_sip
#                                 where the wheel's own lower rim, grips and
#                                 loom sit outboard/below the tub.  NOT a lining
#                                 fit: rays at x 0.44-0.52 put the liner wall at
#                                 |y| 0.131-0.139 and SW_Shell at 0.133-0.140,
#                                 1-3 mm outboard of it, while MB_chassis_cockpit
#                                 is 25 mm further out again - and in the
#                                 assembled car the same wheel already cuts
#                                 MB_cell_floor (158+164+256+61 pairs) and
#                                 MB_cell_stringer (84).  Widening the tray here
#                                 would only move the interference onto the
#                                 monocoque; it needs the wheel raised or the
#                                 rim narrowed, so it is left flagged.
#     CI_seat / CI_seatpad x steering_wheel  0 pairs (was 17257 / 42 obj pairs)
#     CI_pedals x CI_footwell 0 | CI_dash x CI_footwell 0 | CI_dash x CI_column 0
#     CI_seatpad x CI_column  0 | CI_headrest x CI_harness_web 0
# Build is idempotent (15 objects / 15 meshes after 1, 2 and 3 calls).
