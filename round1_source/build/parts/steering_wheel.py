"""Modern F1 steering wheel - hero close-up asset.

Built in a wheel-local frame and placed with one matrix, so every object shares
the same object-space (the carbon weave runs continuously across the shell,
panels and paddles instead of jumping at every part boundary).

Local frame
-----------
    local +x   across the wheel, toward the driver's left  (world -Y)
    local +y   up the wheel face                           (world  X*sin, Z*cos)
    local +z   out of the face, toward the driver          (world -X*cos, Z*sin)

Hub centre sits at world (0.50, 0, 0.50), face tilted back 22 deg.
Wheel is 280 mm across, 200 mm tall, shell 16 mm thick.
"""

import math

from mathutils import Matrix, Vector

import common as C
import spec as S

NAME = "steering_wheel"
PFX = "SW_"

CENTRE = (0.50, 0.0, 0.50)
TILT_DEG = 22.0
TAU = math.pi * 2.0

# z planes of the shell (local)
Z_FACE = 0.0075          # front skin at the rim
Z_BACK = -0.0075
RIM_R = 0.0024           # rim quarter-round
PANEL_Z = 0.0091         # top of the lower control plate - controls sit here


def _matrix():
    t = math.radians(TILT_DEG)
    c, s = math.cos(t), math.sin(t)
    return Matrix(((0.0, s, -c, CENTRE[0]),
                   (-1.0, 0.0, 0.0, CENTRE[1]),
                   (0.0, c, s, CENTRE[2]),
                   (0.0, 0.0, 0.0, 1.0)))


MW = _matrix()


# --------------------------------------------------------------------------- #
# small geometry helpers (kept inside this module on purpose)
# --------------------------------------------------------------------------- #

def _mk(name, verts, faces, coll, mat, smooth=34.0, mw=None, weld=2e-5):
    ob = C.new_obj(PFX + name, verts, faces, coll=coll, smooth=True)
    if weld:
        C.merge_doubles(ob, weld)
    C.shade_auto_smooth(ob, smooth)
    S.assign(ob, mat)
    ob.matrix_world = MW if mw is None else mw
    return ob


def _loft_obj(name, rings, coll, mat, closed=True, caps=True, smooth=34.0,
              mw=None):
    v, f = C.loft(rings, closed=closed, cap_start=caps, cap_end=caps)
    return _mk(name, v, f, coll, mat, smooth=smooth, mw=mw)


def _norm2(v):
    l = math.hypot(v[0], v[1])
    return (v[0] / l, v[1] / l) if l > 1e-12 else (0.0, 0.0)


def _signed_area(poly):
    a = 0.0
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        a += x0 * y1 - x1 * y0
    return 0.5 * a


def _ccw(poly):
    return poly if _signed_area(poly) > 0.0 else poly[::-1]


def _poly_offset(poly, d):
    """Offset a closed CCW polygon inward by d (metres)."""
    poly = _ccw(poly)
    n = len(poly)
    out = []
    for i in range(n):
        x0, y0 = poly[i - 1]
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        n1 = _norm2((-(y1 - y0), x1 - x0))
        n2 = _norm2((-(y2 - y1), x2 - x1))
        bx, by = n1[0] + n2[0], n1[1] + n2[1]
        bl = math.hypot(bx, by)
        if bl < 1e-9:
            out.append((x1, y1))
            continue
        bx, by = bx / bl, by / bl
        cosv = bx * n1[0] + by * n1[1]
        k = d / max(cosv, 0.30)
        out.append((x1 + bx * k, y1 + by * k))
    return out


def _poly_scale(poly, s, c):
    return [(c[0] + (p[0] - c[0]) * s, c[1] + (p[1] - c[1]) * s) for p in poly]


def _centroid(poly):
    a = 0.0
    cx = cy = 0.0
    n = len(poly)
    for i in range(n):
        x0, y0 = poly[i]
        x1, y1 = poly[(i + 1) % n]
        cr = x0 * y1 - x1 * y0
        a += cr
        cx += (x0 + x1) * cr
        cy += (y0 + y1) * cr
    a *= 0.5
    if abs(a) < 1e-12:
        return (0.0, 0.0)
    return (cx / (6.0 * a), cy / (6.0 * a))


def _ring(poly, z):
    return [(p[0], p[1], z) for p in poly]


def _circle(cx, cy, r, z, seg):
    """One ring of a solid of revolution about +z.

    Deliberately a single helper: hand-written rings elsewhere in this file
    once used mismatched divisors for cos and sin (cos(TAU*j/28) with
    sin(TAU*j/36)), which is not a circle at all but a self-crossing Lissajous
    figure. Everything that wants a circle now goes through here.
    """
    return [(cx + r * math.cos(TAU * i / seg),
             cy + r * math.sin(TAU * i / seg), z) for i in range(seg)]


def _mirror_half(half, samples=150):
    pts = C.catmull_rom(half, samples)
    pts[0] = (0.0, pts[0][1])
    pts[-1] = (0.0, pts[-1][1])
    out = [tuple(p) for p in pts]
    out += [(-p[0], p[1]) for p in reversed(pts[1:-1])]
    return out


def _rr(w, h, r, ca=8, nx=None, ny=None, cx=0.0, cy=0.0, seg=0.004):
    """Rounded rectangle outline, CCW, deterministic point count."""
    hw, hh = w * 0.5, h * 0.5
    r = min(r, hw * 0.999, hh * 0.999)
    lx, ly = 2.0 * (hw - r), 2.0 * (hh - r)
    if nx is None:
        nx = max(1, int(round(lx / seg)))
    if ny is None:
        ny = max(1, int(round(ly / seg)))
    pts = []
    for i in range(ny):
        pts.append((hw, -(hh - r) + ly * i / ny))
    for i in range(ca):
        a = 0.5 * math.pi * i / ca
        pts.append((hw - r + r * math.cos(a), hh - r + r * math.sin(a)))
    for i in range(nx):
        pts.append((hw - r - lx * i / nx, hh))
    for i in range(ca):
        a = 0.5 * math.pi * (1.0 + i / ca)
        pts.append((-(hw - r) + r * math.cos(a), hh - r + r * math.sin(a)))
    for i in range(ny):
        pts.append((-hw, (hh - r) - ly * i / ny))
    for i in range(ca):
        a = 0.5 * math.pi * (2.0 + i / ca)
        pts.append((-(hw - r) + r * math.cos(a), -(hh - r) + r * math.sin(a)))
    for i in range(nx):
        pts.append((-(hw - r) + lx * i / nx, -hh))
    for i in range(ca):
        a = 0.5 * math.pi * (3.0 + i / ca)
        pts.append((hw - r + r * math.cos(a), -(hh - r) + r * math.sin(a)))
    return [(p[0] + cx, p[1] + cy) for p in pts]


def _slab(name, poly, z0, z1, r, coll, mat, steps=3, smooth=34.0):
    """Closed slab from a 2D outline with a quarter-round rim on both faces."""
    poly = _ccw(poly)
    rings = []
    for k in range(steps + 1):
        a = 0.5 * math.pi * k / steps
        rings.append(_ring(_poly_offset(poly, r * (1.0 - math.sin(a))),
                           z0 + r * (1.0 - math.cos(a))))
    for k in range(steps, -1, -1):
        a = 0.5 * math.pi * k / steps
        rings.append(_ring(_poly_offset(poly, r * (1.0 - math.sin(a))),
                           z1 - r * (1.0 - math.cos(a))))
    return _loft_obj(name, rings, coll, mat, caps=True, smooth=smooth)


def _tube(name, profile, coll, mat, segments=64, at=(0.0, 0.0), smooth=34.0,
          mw=None, twist=0.0):
    """Solid of revolution about local +z. profile = [(r, z), ...].

    A profile that starts and ends at r=0 makes a closed solid; one that
    returns to its first point makes a closed torus-like ring.
    """
    rings = []
    for (r, z) in profile:
        ring = []
        for i in range(segments):
            t = TAU * i / segments + twist
            ring.append((at[0] + r * math.cos(t), at[1] + r * math.sin(t), z))
        rings.append(ring)
    v, f = C.loft(rings, closed=True, cap_start=False, cap_end=False)
    return _mk(name, v, f, coll, mat, smooth=smooth, mw=mw, weld=1.5e-5)


def _knurled(name, profile, coll, mat, at=(0.0, 0.0), teeth=44, amp=0.00035,
             per_tooth=4, smooth=30.0, twist=0.0):
    """Revolve with a triangular knurl. profile = [(r, z, knurl_factor)].

    `twist` rotates the finished shape rigidly about the axis (radians). It
    exists so a MATING knurl can be clocked against a part that is not ours:
    the knurl phase is still evaluated on the untwisted angle, so the tooth
    count and shape are untouched and only the clock position moves.
    """
    seg = teeth * per_tooth
    rings = []
    for (r, z, kf) in profile:
        ring = []
        for i in range(seg):
            t0 = TAU * i / seg
            f = (t0 * teeth / TAU) % 1.0
            tri = 1.0 - abs(2.0 * f - 1.0)
            rr = r + amp * kf * (tri - 0.5)
            t = t0 + twist
            ring.append((at[0] + rr * math.cos(t), at[1] + rr * math.sin(t), z))
        rings.append(ring)
    v, f = C.loft(rings, closed=True, cap_start=False, cap_end=False)
    return _mk(name, v, f, coll, mat, smooth=smooth, weld=1.0e-5)


def _box_pts(x0, x1, y0, y1, z0, z1):
    v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
         (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
         (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return v, f


# DisplayEmit is a dot-matrix built from two SAW band textures on the OBJECT
# coordinate: rows band along object Z with a 2.0944 mm pitch, columns along
# object Y with a 3.4906 mm pitch, and the lit dot is where both saws are high.
# A screen therefore has to be authored in the object YZ plane. These helpers
# rotate the wheel-local XY screen plane into it, and optionally shrink a group
# so it samples a single phase (a segment that is uniformly lit or uniformly
# dark, instead of a gradient across it).
EM_ROWS = 1.0 / (150.0 * 20.0 / TAU)      # 2.0944 mm - object Z
EM_COLS = 1.0 / (90.0 * 20.0 / TAU)       # 3.4906 mm - object Y
EM_PERM = Matrix(((0.0, 1.0, 0.0, 0.0),
                  (0.0, 0.0, 1.0, 0.0),
                  (1.0, 0.0, 0.0, 0.0),
                  (0.0, 0.0, 0.0, 1.0)))
EM_LIT = (0.62 * EM_COLS, 0.95 * EM_ROWS)   # both saws high  -> lit segment
EM_DARK = (0.62 * EM_COLS, 0.10 * EM_ROWS)  # row saw low     -> dark segment


def _emit(name, boxes, cen, coll, k=1.0, ph=(0.0, 0.0), smooth=60.0):
    """Emissive geometry mapped into DisplayEmit's YZ dot grid.

    k=1 leaves the dot matrix at its native 3.5 x 2.1 mm pitch (a screen full
    of pixels); a large k shrinks the group into one dot phase so the whole
    group reads as a single lit or unlit segment.
    """
    v, f = _merge_meshes(boxes)
    nv = [((p[2] - cen[2]) / k,
           (p[0] - cen[0]) / k + ph[0],
           (p[1] - cen[1]) / k + ph[1]) for p in v]
    mw = (MW @ Matrix.Translation(Vector(cen)) @ EM_PERM
          @ Matrix.Diagonal(Vector((k, k, k, 1.0)))
          @ Matrix.Translation(Vector((0.0, -ph[0], -ph[1]))))
    # weld in the shrunk local space: the LED dies are revolves with poles, and
    # unwelded poles leave non-manifold zero-length edges behind
    return _mk(name, nv, f, coll, "DisplayEmit", smooth=smooth, mw=mw,
               weld=max(1e-9, 2e-5 / k))


def _merge_meshes(parts):
    """parts = [(verts, faces), ...] -> single (verts, faces)."""
    V, F = [], []
    for v, f in parts:
        o = len(V)
        V.extend(v)
        F.extend([tuple(i + o for i in face) for face in f])
    return V, F


def _rot2(p, ang, c=(0.0, 0.0)):
    ca, sa = math.cos(ang), math.sin(ang)
    dx, dy = p[0] - c[0], p[1] - c[1]
    return (c[0] + dx * ca - dy * sa, c[1] + dx * sa + dy * ca)


def _bar(cx, cy, ang, l, w, z0, z1):
    """Rotated rectangular bar (a tick mark / mask bar) as (verts, faces)."""
    pts = [(-l * 0.5, -w * 0.5), (l * 0.5, -w * 0.5),
           (l * 0.5, w * 0.5), (-l * 0.5, w * 0.5)]
    pts = [_rot2(p, ang) for p in pts]
    pts = [(p[0] + cx, p[1] + cy) for p in pts]
    v = [(p[0], p[1], z0) for p in pts] + [(p[0], p[1], z1) for p in pts]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
         (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return v, f


def _hex_screw(cx, cy, z_top, r_head=0.0034, seg=24, depth=0.0011,
               head_h=0.0018, dn=1.0):
    """Countersunk cap screw with a real hex socket. Returns (verts, faces).

    dn = -1 drives the screw the other way (heads on the back of the wheel).
    """
    rs = r_head * 0.56          # socket across-flats-ish
    head_h = head_h * dn
    depth = depth * dn
    zc = z_top - 0.0004 * dn    # chamfer plane
    circ = lambda r, z: [(cx + r * math.cos(TAU * i / seg),
                          cy + r * math.sin(TAU * i / seg), z)
                         for i in range(seg)]

    def hexr(r, z):
        out = []
        for i in range(seg):
            t = TAU * i / seg
            k = (t % (TAU / 6.0)) - TAU / 12.0
            rr = r / math.cos(k)
            out.append((cx + rr * math.cos(t), cy + rr * math.sin(t), z))
        return out

    rings = [circ(r_head * 0.86, z_top - head_h),      # buried shank
             circ(r_head, z_top - head_h + 0.0004 * dn),
             circ(r_head, zc),
             circ(r_head - 0.0004, z_top),
             hexr(rs, z_top),
             hexr(rs, z_top - depth),
             hexr(rs * 0.12, z_top - depth - 0.0002 * dn)]
    v, f = C.loft(rings, closed=True, cap_start=True, cap_end=True)
    return v, f


# --------------------------------------------------------------------------- #
# shell
# --------------------------------------------------------------------------- #

SHELL_HALF = [
    (0.0000, -0.0620),
    (0.0180, -0.0642),
    (0.0330, -0.0722),
    (0.0452, -0.0862),
    (0.0560, -0.0952),
    (0.0700, -0.0982),
    (0.0900, -0.0958),
    (0.1090, -0.0868),
    (0.1250, -0.0700),
    (0.1345, -0.0480),
    (0.1390, -0.0220),
    (0.1400, 0.0100),
    (0.1370, 0.0420),
    (0.1300, 0.0660),
    (0.1180, 0.0830),
    (0.0990, 0.0940),
    (0.0740, 0.0990),
    (0.0400, 0.1000),
    (0.0000, 0.1005),
]


def shell_poly(samples=150):
    return _mirror_half(SHELL_HALF, samples)


def _shell(coll):
    poly = shell_poly()
    cen = _centroid(poly)
    inner = _poly_offset(poly, RIM_R)

    rings = []
    face_s = [0.06, 0.16, 0.27, 0.39, 0.51, 0.63, 0.75, 0.87, 1.0]
    for s in face_s:
        z = Z_FACE + 0.0006 * (1.0 - s * s)
        rings.append(_ring(_poly_scale(inner, s, cen), z))
    # front rim quarter round
    for k in range(1, 4):
        a = 0.5 * math.pi * k / 3.0
        rings.append(_ring(_poly_offset(poly, RIM_R * (1.0 - math.sin(a))),
                           Z_FACE - RIM_R * (1.0 - math.cos(a))))
    rings.append(_ring(poly, Z_BACK + RIM_R))
    for k in range(2, -1, -1):
        a = 0.5 * math.pi * k / 3.0
        rings.append(_ring(_poly_offset(poly, RIM_R * (1.0 - math.sin(a))),
                           Z_BACK + RIM_R * (1.0 - math.cos(a))))
    for s in reversed(face_s):
        z = Z_BACK - 0.0012 * (1.0 - s * s)
        rings.append(_ring(_poly_scale(inner, s, cen), z))

    ob = _loft_obj("Shell", rings, coll, "CarbonFibre", caps=True, smooth=26.0)
    return [ob]


# --------------------------------------------------------------------------- #
# grips
# --------------------------------------------------------------------------- #

GRIP_T0, GRIP_T1 = 0.0, 1.0
GROOVES = (0.255, 0.415, 0.575, 0.735)


def _grip_station(t):
    y = 0.0560 - 0.1330 * t
    xc = 0.1058 + 0.0088 * math.sin(math.pi * min(1.0, t * 1.05)) - 0.0060 * t
    tap = (1.0 - 0.955 * ((2.0 * t - 1.0) ** 6)) ** 0.42
    hw = 0.0182 * tap
    tap2 = (1.0 - 0.975 * ((2.0 * t - 1.0) ** 8)) ** 0.45
    h = 0.0348 * tap2
    return y, xc, hw, h


def _grip_base(t, u):
    """Un-displaced section point (x, z) at station t, arc parameter u."""
    _y, xc, hw, h = _grip_station(t)
    arch = (1.0 - abs(2.0 * u - 1.0) ** 3.0) ** (1.0 / 3.0)
    return (xc + hw * (1.0 - 2.0 * u), 0.0069 + h * arch)


def _grip_offset(t, u):
    """Inward displacement (metres) at (t, u): finger relief + thumb dish +
    the moulded dimple pattern of the rubber."""
    g = 0.0
    for gt in GROOVES:
        g += math.exp(-((t - gt) / 0.0300) ** 2)
    g = min(g, 1.0)
    win_g = math.exp(-((u - 0.240) / 0.300) ** 2)
    th = math.exp(-((t - 0.150) / 0.0640) ** 2)
    win_t = math.exp(-((u - 0.890) / 0.150) ** 2)
    dim = (math.sin(TAU * u * 13.0) * math.sin(TAU * t * 26.0))
    fade = min(1.0, min(u, 1.0 - u) / 0.10) * min(1.0, min(t, 1.0 - t) / 0.06)
    return (0.0031 * g * win_g + 0.0042 * th * win_t
            - 0.00020 * dim * fade)


def _grip_rings(side, nt=188, na=126, nb=22):
    rings = []
    du = 0.5 / na
    for i in range(nt + 1):
        t = i / nt
        y, xc, hw, h = _grip_station(t)
        pts = []
        for j in range(na + 1):
            u = j / na
            p = _grip_base(t, u)
            a = _grip_base(t, max(0.0, u - du))
            b = _grip_base(t, min(1.0, u + du))
            tx, tz = b[0] - a[0], b[1] - a[1]
            tl = math.hypot(tx, tz) or 1.0
            nx, nz = tz / tl, -tx / tl        # outward normal
            d = _grip_offset(t, u)
            z = p[1] - nz * d
            pts.append((side * (p[0] - nx * d), y, max(0.0069, z)))
        for j in range(1, nb):
            u = 1.0 - j / nb
            x = xc + hw * (1.0 - 2.0 * u)
            pts.append((side * x, y, 0.0069))
        rings.append(pts if side > 0 else pts[::-1])
    return rings


def _grips(coll):
    obs = []
    for side, tag in ((1, "L"), (-1, "R")):
        rings = _grip_rings(side)
        ob = _loft_obj("Grip" + tag, rings, coll, "SuedeGrip", caps=True,
                       smooth=42.0)
        obs.append(ob)

        # mount plate under the grip so it is visibly bolted on, not floating
        foot = []
        for i in range(0, 85, 4):
            t = i / 84.0
            y, xc, hw, _h = _grip_station(t)
            foot.append((side * (xc + hw + 0.0028), y))
        for i in range(84, -1, -4):
            t = i / 84.0
            y, xc, hw, _h = _grip_station(t)
            foot.append((side * (xc - hw - 0.0028), y))
        if side < 0:
            foot = foot[::-1]
        plate = C.catmull_rom(foot + [foot[0]], 120)
        obs.append(_slab("GripPlate" + tag, plate, Z_FACE - 0.0004, Z_FACE + 0.0016,
                         0.0007, coll, "CarbonMatte", steps=2))

        scr = []
        for t in (0.055, 0.335, 0.655, 0.945):
            y, xc, hw, _h = _grip_station(t)
            scr.append(_hex_screw(side * (xc + hw + 0.0021), y, Z_FACE + 0.0028,
                                  r_head=0.0027, seg=22, depth=0.0011,
                                  head_h=0.0022))
            scr.append(_hex_screw(side * (xc - hw - 0.0021), y, Z_FACE + 0.0028,
                                  r_head=0.0027, seg=22, depth=0.0011,
                                  head_h=0.0022))
        v, f = _merge_meshes(scr)
        obs.append(_mk("GripScrews" + tag, v, f, coll, "SteelFastener",
                       smooth=32.0))
    return obs


# --------------------------------------------------------------------------- #
# display
# --------------------------------------------------------------------------- #

DISP_CX, DISP_CY = 0.0, 0.0390
DISP_W, DISP_H = 0.1360, 0.0620          # bezel outer
LCD_W, LCD_H = 0.1180, 0.0480            # visible screen


def _display(coll):
    obs = []
    ca, nx, ny = 8, 26, 8
    outer = _rr(DISP_W, DISP_H, 0.0085, ca, nx, ny, DISP_CX, DISP_CY)
    inner = _rr(LCD_W + 0.0055, LCD_H + 0.0055, 0.0045, ca, nx, ny,
                DISP_CX, DISP_CY)

    # bezel: a frame lofted between the outer and the inner opening
    z0, z1 = Z_FACE - 0.0006, Z_FACE + 0.0094
    rings = []
    rings.append(_ring(_poly_offset(outer, 0.0016), z0))
    rings.append(_ring(outer, z0 + 0.0016))
    rings.append(_ring(outer, z1 - 0.0022))
    rings.append(_ring(_poly_offset(outer, 0.0010), z1 - 0.0006))
    rings.append(_ring(_poly_offset(outer, 0.0022), z1))
    rings.append(_ring(_poly_offset(inner, -0.0012), z1))
    rings.append(_ring(inner, z1 - 0.0016))
    rings.append(_ring(inner, z1 - 0.0044))            # glass ledge
    rings.append(_ring(_poly_offset(inner, -0.0022), z1 - 0.0052))
    rings.append(_ring(_poly_offset(inner, -0.0022), z0))
    obs.append(_loft_obj("DispBezel", rings, coll, "CarbonFibre", caps=False,
                         smooth=30.0))

    # bezel fasteners
    scr = []
    for (sx, sy) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        scr.append(_hex_screw(DISP_CX + sx * (DISP_W * 0.5 - 0.0042),
                              DISP_CY + sy * (DISP_H * 0.5 - 0.0042),
                              z1 + 0.0011, r_head=0.0029, seg=22,
                              depth=0.0012, head_h=0.0023))
    v, f = _merge_meshes(scr)
    obs.append(_mk("DispScrews", v, f, coll, "SteelFastener", smooth=32.0))

    # dark LCD substrate - the lit segments are separate raised geometry
    zs = z1 - 0.0074
    face = _rr(LCD_W + 0.0044, LCD_H + 0.0044, 0.0040, 6, 18, 6,
               DISP_CX, DISP_CY)
    obs.append(_slab("DispFace", face, zs - 0.0018, zs + 0.0004, 0.0005, coll,
                     "MatteBlack", steps=2, smooth=40.0))

    x0, x1 = DISP_CX - LCD_W * 0.5, DISP_CX + LCD_W * 0.5
    y0, y1 = DISP_CY - LCD_H * 0.5, DISP_CY + LCD_H * 0.5
    zb0, zb1 = zs + 0.0004, zs + 0.0009
    lit, off, data, chrome = [], [], [], []

    # --- rev bar: 15 segments across the top, 11 lit -----------------------
    n = 15
    pitch = (x1 - x0 - 0.0020) / n
    for i in range(n):
        xx = x0 + 0.0010 + i * pitch
        b = _box_pts(xx + 0.0006, xx + pitch - 0.0006, y1 - 0.0092,
                     y1 - 0.0016, zb0, zb1)
        (lit if i < 11 else off).append(b)

    # --- 7-segment gear digit, reading "5" ---------------------------------
    gx, gy, gw, gh, gt = DISP_CX - 0.0362, DISP_CY - 0.0034, 0.0086, 0.0128, 0.0026
    segs = {
        "a": _box_pts(gx - gw + gt * 0.8, gx + gw - gt * 0.8, gy + gh - gt, gy + gh, zb0, zb1),
        "g": _box_pts(gx - gw + gt * 0.8, gx + gw - gt * 0.8, gy - gt * 0.5, gy + gt * 0.5, zb0, zb1),
        "d": _box_pts(gx - gw + gt * 0.8, gx + gw - gt * 0.8, gy - gh, gy - gh + gt, zb0, zb1),
        "f": _box_pts(gx - gw, gx - gw + gt, gy + gt * 0.8, gy + gh - gt * 0.8, zb0, zb1),
        "b": _box_pts(gx + gw - gt, gx + gw, gy + gt * 0.8, gy + gh - gt * 0.8, zb0, zb1),
        "e": _box_pts(gx - gw, gx - gw + gt, gy - gh + gt * 0.8, gy - gt * 0.8, zb0, zb1),
        "c": _box_pts(gx + gw - gt, gx + gw, gy - gh + gt * 0.8, gy - gt * 0.8, zb0, zb1),
    }
    for k, m in segs.items():
        (lit if k in ("a", "f", "g", "c", "d") else off).append(m)

    # --- centre field: lap / delta pseudo-text ------------------------------
    for r in range(2):
        for c in range(7):
            xx = DISP_CX - 0.0230 + c * 0.0058
            yy = DISP_CY + 0.0062 - r * 0.0092
            data.append(_box_pts(xx, xx + 0.0042, yy, yy + 0.0062, zb0, zb1))

    # --- right field: three data rows ---------------------------------------
    for r in range(3):
        for c in range(6):
            xx = DISP_CX + 0.0230 + c * 0.0050
            yy = DISP_CY + 0.0074 - r * 0.0072
            data.append(_box_pts(xx, xx + 0.0036, yy, yy + 0.0046, zb0, zb1))

    # --- bottom status strip ------------------------------------------------
    for c in range(9):
        xx = x0 + 0.0040 + c * 0.0120
        data.append(_box_pts(xx, xx + 0.0086, y0 + 0.0022, y0 + 0.0056,
                             zb0, zb1))

    # thin chrome field dividers so the layout reads as panels
    for xx in (DISP_CX - 0.0262, DISP_CX + 0.0206):
        chrome.append(_box_pts(xx, xx + 0.0006, y0 + 0.0068, y1 - 0.0106,
                               zb0, zb1 + 0.0002))
    chrome.append(_box_pts(x0 + 0.0020, x1 - 0.0020, y0 + 0.0062,
                           y0 + 0.0068, zb0, zb1 + 0.0002))
    v, f = _merge_meshes(chrome)
    obs.append(_mk("DispTrim", v, f, coll, "Titanium", smooth=40.0))

    cen = (DISP_CX, DISP_CY, zs)
    obs.append(_emit("DispLit", lit, cen, coll, k=220.0, ph=EM_LIT))
    obs.append(_emit("DispOff", off, cen, coll, k=220.0, ph=EM_DARK))
    obs.append(_emit("DispData", data, cen, coll, k=1.0))

    # cover glass, recessed below the bezel lip
    glass = _rr(LCD_W + 0.0070, LCD_H + 0.0070, 0.0045, 6, 18, 6,
                DISP_CX, DISP_CY)
    obs.append(_slab("DispGlass", glass, z1 - 0.0044, z1 - 0.0030, 0.0004,
                     coll, "DisplayGlass", steps=2, smooth=50.0))
    return obs


# --------------------------------------------------------------------------- #
# marshalling / rev LED strip
# --------------------------------------------------------------------------- #

LED_N = 16
LED_X0 = -0.0810
LED_PITCH = 0.0108


def _led_y(x):
    return 0.0855 - 0.0080 * (x / 0.086) ** 2


def _sweep_x(name, xs, section, coll, mat, smooth=34.0):
    rings = []
    for x in xs:
        yc = _led_y(x)
        rings.append([(x, yc + dy, z) for (dy, z) in section])
    return _loft_obj(name, rings, coll, mat, caps=True, smooth=smooth)


def _leds(coll):
    obs = []
    xs = [-0.0885 + 0.1770 * i / 52.0 for i in range(53)]

    carrier = [(-0.0078, 0.0064), (0.0078, 0.0064), (0.0078, 0.0098),
               (0.0064, 0.0106), (-0.0064, 0.0106), (-0.0078, 0.0098)]
    obs.append(_sweep_x("LedCarrier", xs, carrier, coll, "MatteBlack",
                        smooth=30.0))


    hood = [(0.0080, 0.0062), (0.0128, 0.0062), (0.0128, 0.0140),
            (0.0108, 0.0174), (0.0082, 0.0174), (0.0056, 0.0148),
            (0.0056, 0.0114), (0.0080, 0.0092)]
    obs.append(_sweep_x("LedHood", xs, hood, coll, "CarbonFibre", smooth=30.0))

    lip = [(-0.0128, 0.0062), (-0.0080, 0.0062), (-0.0080, 0.0122),
           (-0.0094, 0.0136), (-0.0116, 0.0136), (-0.0128, 0.0122)]
    obs.append(_sweep_x("LedLip", xs, lip, coll, "CarbonFibre", smooth=30.0))

    # individual lenses + reflector cups
    lens = []
    cups = []
    for i in range(LED_N):
        x = LED_X0 + i * LED_PITCH
        y = _led_y(x)
        prof = []
        for k in range(9):
            a = 0.5 * math.pi * k / 8.0
            prof.append((0.0040 * math.cos(a), 0.0104 + 0.0029 * math.sin(a)))
        prof = [(0.0, 0.01145), (0.0018, 0.01125), (0.0032, 0.01070),
                (0.0040, 0.01020)] + prof
        rings = []
        for (r, z) in prof:
            rings.append(_circle(x, y, r, z, 36))
        lens.append(C.loft(rings, closed=True, cap_start=False, cap_end=False))
        cprof = [(0.0039, 0.0100), (0.0050, 0.0103), (0.0051, 0.0113),
                 (0.0046, 0.0115), (0.0042, 0.0107), (0.0039, 0.0100)]
        rings = []
        for (r, z) in cprof:
            rings.append(_circle(x, y, r, z, 32))
        cups.append(C.loft(rings, closed=True, cap_start=False, cap_end=False))
    v, f = _merge_meshes(lens)
    obs.append(_mk("LedLenses", v, f, coll, "DisplayGlass", smooth=40.0,
                   weld=1e-5))
    v, f = _merge_meshes(cups)
    obs.append(_mk("LedCups", v, f, coll, "Titanium", smooth=34.0, weld=1e-5))

    # the dies themselves: 11 lit, 5 dark - a rev bar caught part way up
    die_lit, die_off = [], []
    for i in range(LED_N):
        x = LED_X0 + i * LED_PITCH
        y = _led_y(x)
        rings = []
        for (r, z) in ((0.0, 0.01055), (0.0022, 0.01055), (0.0026, 0.01072),
                       (0.0021, 0.01088), (0.0, 0.01094)):
            rings.append(_circle(x, y, r, z, 28))
        m = C.loft(rings, closed=True, cap_start=False, cap_end=False)
        (die_lit if i < 11 else die_off).append(m)
    cen = (0.0, 0.0820, 0.0104)
    obs.append(_emit("LedLit", die_lit, cen, coll, k=420.0, ph=EM_LIT))
    obs.append(_emit("LedOff", die_off, cen, coll, k=420.0, ph=EM_DARK))
    return obs


# --------------------------------------------------------------------------- #
# controls
# --------------------------------------------------------------------------- #

def _ring_mesh(profile, cx, cy, seg=48):
    rings = []
    for (r, z) in profile:
        rings.append([(cx + r * math.cos(TAU * i / seg),
                       cy + r * math.sin(TAU * i / seg), z)
                      for i in range(seg)])
    return C.loft(rings, closed=True, cap_start=False, cap_end=False)


def _knurl_mesh(profile, cx, cy, teeth, amp):
    seg = teeth * 5
    rings = []
    for (r, z, kf) in profile:
        ring = []
        for i in range(seg):
            t = TAU * i / seg
            fr = (t * teeth / TAU) % 1.0
            tri = 1.0 - abs(2.0 * fr - 1.0)
            rr = r + amp * kf * (tri - 0.5)
            ring.append((cx + rr * math.cos(t), cy + rr * math.sin(t), z))
        rings.append(ring)
    return C.loft(rings, closed=True, cap_start=False, cap_end=False)


def _button(cx, cy, r, bz, proud=0.0012, seg=44):
    """(collar_mesh, cap_mesh, cap_top_z) for one push button."""
    ri, ro = r + 0.0007, r + 0.0032
    col = [(ri, bz - 0.0004), (ro, bz - 0.0004), (ro, bz + 0.0026),
           (ro - 0.0006, bz + 0.0033), (ri + 0.0005, bz + 0.0033),
           (ri, bz + 0.0026), (ri, bz - 0.0004)]
    top = bz + 0.0033 + proud
    cap = [(0.0, bz + 0.0011), (r * 0.5, bz + 0.0007), (r - 0.0005,
           bz + 0.0004), (r, bz + 0.0011),
           (r, top - 0.0010), (r - 0.0005, top - 0.0002),
           (r - 0.0014, top), (r * 0.55, top - 0.0002),
           (0.0, top - 0.0005)]
    return (_ring_mesh(col, cx, cy, seg), _ring_mesh(cap, cx, cy, seg), top)


def _rotary(cx, cy, r_base, lw, bz, teeth=40, marks=12, ang0=0.0):
    """Returns dict of meshes for one rotary dial."""
    r_knob = r_base - lw - 0.0013
    ring = [(r_base - lw, bz - 0.0004), (r_base, bz - 0.0004),
            (r_base, bz + 0.0011), (r_base - 0.0005, bz + 0.0016),
            (r_base - lw + 0.0004, bz + 0.0016), (r_base - lw, bz + 0.0011),
            (r_base - lw, bz - 0.0004)]
    legend = _ring_mesh(ring, cx, cy, 80)

    tick = []
    for i in range(marks * 2):
        a = ang0 + TAU * i / (marks * 2)
        major = (i % 2 == 0)
        index = (i == 0)
        l1 = r_base - 0.0009
        l0 = r_base - lw + (0.0007 if major else lw * 0.46)
        rm = 0.5 * (l0 + l1)
        tick.append(_bar(cx + rm * math.cos(a), cy + rm * math.sin(a), a,
                         l1 - l0, 0.0012 if index else (0.0008 if major
                                                        else 0.0005),
                         bz + 0.0013, bz + 0.0018))
    ticks = _merge_meshes(tick)

    nut = [(r_knob - 0.0004, bz + 0.0013), (r_knob + 0.0016, bz + 0.0013),
           (r_knob + 0.0016, bz + 0.0028), (r_knob + 0.0010, bz + 0.0033),
           (r_knob - 0.0004, bz + 0.0033), (r_knob - 0.0004, bz + 0.0013)]
    collar = _ring_mesh(nut, cx, cy, 64)

    ztop = bz + 0.0033 + (0.0086 if lw > 0.0060 else 0.0072)
    kp = [(0.0, bz + 0.0026, 0.0),
          (r_knob - 0.0008, bz + 0.0026, 0.0),
          (r_knob, bz + 0.0034, 0.4),
          (r_knob, bz + 0.0046, 1.0),
          (r_knob, ztop - 0.0022, 1.0),
          (r_knob, ztop - 0.0014, 0.4),
          (r_knob - 0.0009, ztop - 0.0004, 0.0),
          (r_knob - 0.0022, ztop, 0.0),            # flat top rim
          (r_knob - 0.0042, ztop, 0.0),
          (r_knob - 0.0052, ztop - 0.0009, 0.0),   # step into the dish
          (r_knob * 0.44, ztop - 0.0013, 0.0),
          (0.0042, ztop - 0.0011, 0.0),
          (0.0035, ztop + 0.0005, 0.0),            # centre boss
          (0.0026, ztop + 0.0010, 0.0),
          (0.0, ztop + 0.0012, 0.0)]
    knob = _knurl_mesh(kp, cx, cy, teeth, 0.00060)

    pa = ang0 + math.pi * 0.5
    ptr = _merge_meshes([
        _bar(cx + (r_knob * 0.56) * math.cos(pa),
             cy + (r_knob * 0.56) * math.sin(pa), pa,
             r_knob * 0.78, 0.0013, ztop - 0.0014, ztop + 0.0004),
        _bar(cx + (r_knob * 0.56) * math.cos(pa + math.pi),
             cy + (r_knob * 0.56) * math.sin(pa + math.pi), pa,
             r_knob * 0.40, 0.0007, ztop - 0.0014, ztop - 0.0006)])
    return legend, ticks, collar, knob, ptr


def _toggle(cx, cy, bz, tilt=0.38, tdir=1.0):
    """Hex-nut based toggle switch: (nut, lever) meshes."""
    hexp = [(0.0, bz - 0.0004), (0.0058, bz - 0.0004), (0.0058, bz + 0.0028),
            (0.0050, bz + 0.0035), (0.0, bz + 0.0035)]
    rings = []
    for (r, z) in hexp:
        rings.append([(cx + (r / math.cos(((TAU * i / 24) % (TAU / 6.0))
                                          - TAU / 12.0)) * math.cos(TAU * i / 24),
                       cy + (r / math.cos(((TAU * i / 24) % (TAU / 6.0))
                                          - TAU / 12.0)) * math.sin(TAU * i / 24),
                       z) if r > 1e-6 else (cx, cy, z)
                      for i in range(24)])
    nut = C.loft(rings, closed=True, cap_start=False, cap_end=False)

    boss = _ring_mesh([(0.0, bz + 0.0032), (0.0036, bz + 0.0032),
                       (0.0036, bz + 0.0044), (0.0029, bz + 0.0049),
                       (0.0, bz + 0.0049)], cx, cy, 28)

    p0 = Vector((cx, cy, bz + 0.0040))
    d = Vector((0.0, math.sin(tilt) * tdir, math.cos(tilt)))
    p1 = p0 + d * 0.0122
    lever = _rod_mesh(p0, p1, 0.0019, 0.0011, seg=22)
    ball = _rod_mesh(p1 - d * 0.0016, p1 - d * 0.0002, 0.0020, 0.0020, seg=22)
    return _merge_meshes([nut, boss]), _merge_meshes([lever, ball])


def _rod_mesh(p0, p1, r0, r1, seg=20, caps=5):
    p0, p1 = Vector(p0), Vector(p1)
    ax = p1 - p0
    L = ax.length
    if L < 1e-9:
        return ([], [])
    ax = ax / L
    ref = Vector((1.0, 0.0, 0.0))
    if abs(ax.dot(ref)) > 0.9:
        ref = Vector((0.0, 1.0, 0.0))
    u = ax.cross(ref).normalized()
    v = ax.cross(u)
    stations = []
    for k in range(caps + 1):
        a = -0.5 * math.pi + 0.5 * math.pi * k / caps
        stations.append((r0 * math.sin(a), r0 * math.cos(a)))
    stations.append((L, r1))
    for k in range(1, caps + 1):
        a = 0.5 * math.pi * k / caps
        stations.append((L + r1 * math.sin(a), r1 * math.cos(a)))
    rings = []
    for (s, r) in stations:
        c = p0 + ax * s
        rings.append([tuple(c + (u * math.cos(TAU * i / seg)
                                 + v * math.sin(TAU * i / seg)) * r)
                      for i in range(seg)])
    return C.loft(rings, closed=True, cap_start=False, cap_end=False)


# Control plate extents. PLATE_Y1 was 0.0060 with ROW_A_Y at 0.0000: the row A
# collars (9.45 mm outer radius) then overhung the plate's top edge by 3.4 mm
# with open air under the crescent, and the four inner ones drove into the
# display bezel skirt (which starts at y = 0.0080). The row now sits low enough,
# and the plate reaches high enough, that every collar lands wholly on the
# plate with clearance to the bezel.
PLATE_Y0, PLATE_Y1 = -0.0845, 0.0074
ROW_A_Y = -0.0028
ROW_A_R = 0.0060
ROW_B_Y = -0.0245
ROT_Y = -0.0590


def _emit_disc(name, cx, cy, z, r, coll):
    """Backlit insert under a translucent button cap."""
    seg = 28
    v = [(cx, cy, z)]
    for i in range(seg):
        v.append((cx + r * math.cos(TAU * i / seg),
                  cy + r * math.sin(TAU * i / seg), z))
    f = [(0, 1 + i, 1 + (i + 1) % seg) for i in range(seg)]
    return _emit(name, [(v, f)], (cx, cy, z), coll, k=90.0, ph=EM_LIT)


def _controls(coll):
    obs = []
    bz = PANEL_Z

    plate = _rr(0.1630, PLATE_Y1 - PLATE_Y0, 0.0120, 8, 30, 16,
                0.0, 0.5 * (PLATE_Y0 + PLATE_Y1))
    obs.append(_slab("Panel", plate, Z_FACE - 0.0004, PANEL_Z, 0.0009, coll,
                     "CarbonMatte", steps=2))
    scr = []
    # top pair sits between rows A and B: at the old corner position they were
    # 8.0 mm from the outer row A button centres, i.e. 4.2 mm inside its collar.
    for sx in (-1, 1):
        scr.append(_hex_screw(sx * 0.0770, -0.0135, PANEL_Z + 0.0012,
                              r_head=0.0028, seg=22, depth=0.0012,
                              head_h=0.0023))
        scr.append(_hex_screw(sx * 0.0745, 0.5 * (PLATE_Y0 + PLATE_Y1) - 0.0390,
                              PANEL_Z + 0.0012, r_head=0.0028, seg=22,
                              depth=0.0012, head_h=0.0023))
    scr.append(_hex_screw(0.0, PLATE_Y1 - 0.0038, PANEL_Z + 0.0012,
                          r_head=0.0028, seg=22, depth=0.0012, head_h=0.0023))
    scr.append(_hex_screw(0.0, PLATE_Y0 + 0.0038, PANEL_Z + 0.0012,
                          r_head=0.0028, seg=22, depth=0.0012, head_h=0.0023))
    v, f = _merge_meshes(scr)
    obs.append(_mk("PanelScrews", v, f, coll, "SteelFastener", smooth=32.0))

    collars, marks, legends = [], [], []
    caps = {"AnodisedRed": [], "AnodisedGold": [], "MatteBlack": [],
            "Titanium": [], "DisplayGlass": []}
    lit = []

    # row A - six 12.5 mm buttons
    row_a = [(-0.0665, "MatteBlack", -0.0006), (-0.0400, "AnodisedRed", 0.0012),
             (-0.0135, "MatteBlack", 0.0012), (0.0135, "AnodisedGold", 0.0012),
             (0.0400, "DisplayGlass", 0.0012), (0.0665, "MatteBlack", -0.0006)]
    for (x, m, pr) in row_a:
        col, cap, top = _button(x, ROW_A_Y, ROW_A_R, bz, proud=pr, seg=56)
        collars.append(col)
        caps[m].append(cap)
        if m == "DisplayGlass":
            lit.append((x, ROW_A_Y, bz + 0.0012, ROW_A_R - 0.0004))

    # row B - four 15 mm buttons + two toggles
    row_b = [(-0.0440, "MatteBlack", 0.0014), (-0.0155, "DisplayGlass", 0.0014),
             (0.0155, "AnodisedRed", 0.0014), (0.0440, "MatteBlack", 0.0014)]
    for (x, m, pr) in row_b:
        col, cap, top = _button(x, ROW_B_Y, 0.0075, bz, proud=pr, seg=64)
        collars.append(col)
        caps[m].append(cap)
        if m == "DisplayGlass":
            lit.append((x, ROW_B_Y, bz + 0.0012, 0.0068))

    tg = []
    for (x, tdir) in ((-0.0690, 1.0), (0.0690, -1.0)):
        nut, lever = _toggle(x, ROW_B_Y, bz, tdir=tdir)
        tg.append(nut)
        caps["MatteBlack"].append(lever)
    collars.extend(tg)

    # side buttons flanking the display - 10 mm
    for (x, y, m) in ((-0.0778, 0.0250, "AnodisedGold"),
                      (-0.0778, 0.0560, "MatteBlack"),
                      (0.0778, 0.0250, "DisplayGlass"),
                      (0.0778, 0.0560, "MatteBlack")):
        col, cap, top = _button(x, y, 0.0050, Z_FACE, proud=0.0010, seg=44)
        collars.append(col)
        caps[m].append(cap)
        if m == "DisplayGlass":
            lit.append((x, y, Z_FACE + 0.0012, 0.0044))

    # rotaries
    for (x, y, rb, lw, teeth, marks_n, a0) in (
            (-0.0505, ROT_Y, 0.0215, 0.0072, 46, 12, 0.35),
            (0.0505, ROT_Y, 0.0215, 0.0072, 46, 12, -0.9),
            (0.0000, -0.0560, 0.0155, 0.0055, 34, 8, 0.0)):
        legend, ticks, collar, knob, ptr = _rotary(x, y, rb, lw, bz,
                                                   teeth=teeth, marks=marks_n,
                                                   ang0=a0)
        legends.append(legend)
        marks.append(ticks)
        marks.append(ptr)
        collars.append(collar)
        caps["MatteBlack"].append(knob)

    v, f = _merge_meshes(collars)
    obs.append(_mk("Collars", v, f, coll, "Titanium", smooth=30.0, weld=1e-5))
    v, f = _merge_meshes(legends)
    obs.append(_mk("Legends", v, f, coll, "CarbonMatte", smooth=30.0, weld=1e-5))
    v, f = _merge_meshes(marks)
    obs.append(_mk("Marks", v, f, coll, "Titanium", smooth=40.0, weld=1e-5))
    for m, parts in caps.items():
        if not parts:
            continue
        v, f = _merge_meshes(parts)
        obs.append(_mk("Caps" + m, v, f, coll, m, smooth=30.0, weld=1e-5))
    for i, (x, y, z, r) in enumerate(lit):
        obs.append(_emit_disc("Lit%d" % i, x, y, z, r, coll))
    return obs


# --------------------------------------------------------------------------- #
# paddles
# --------------------------------------------------------------------------- #

def _blade_section(x_in, x_out, z0, curl, th, nu=32, nc=6):
    """Curved blade cross-section in the local (x, z) plane, closed loop."""
    cen = []
    for i in range(nu + 1):
        u = i / nu
        x = x_in + (x_out - x_in) * u
        z = z0 - curl * (u ** 1.7)
        cen.append((x, z))
    nrm = []
    for i in range(nu + 1):
        a = cen[max(0, i - 1)]
        b = cen[min(nu, i + 1)]
        tx, tz = b[0] - a[0], b[1] - a[1]
        l = math.hypot(tx, tz) or 1.0
        nrm.append((-tz / l, tx / l))
    h = th * 0.5
    loop = [(cen[i][0] + nrm[i][0] * h, cen[i][1] + nrm[i][1] * h)
            for i in range(nu + 1)]
    # rounded outer end
    ax, az = cen[nu]
    a0 = math.atan2(nrm[nu][1], nrm[nu][0])
    tx, tz = cen[nu][0] - cen[nu - 1][0], cen[nu][1] - cen[nu - 1][1]
    tl = math.hypot(tx, tz) or 1.0
    for k in range(1, nc):
        a = a0 - math.pi * k / nc
        loop.append((ax + h * math.cos(a) * 1.0, az + h * math.sin(a)))
    loop += [(cen[i][0] - nrm[i][0] * h, cen[i][1] - nrm[i][1] * h)
             for i in range(nu, -1, -1)]
    ax, az = cen[0]
    a0 = math.atan2(-nrm[0][1], -nrm[0][0])
    for k in range(1, nc):
        a = a0 - math.pi * k / nc
        loop.append((ax + h * math.cos(a), az + h * math.sin(a)))
    return loop


def _paddle(name, side, coll, y0, y1, x_in0, x_in1, x_out0, x_out1,
            z0, z1, curl0, curl1, th, ns=40, mat="CarbonFibre"):
    rings = []
    for i in range(ns + 1):
        s = i / ns
        e = min(1.0, min(s, 1.0 - s) / 0.045)          # end chamfer
        k = 0.55 + 0.45 * e
        xi = C.lerp(x_in0, x_in1, s)
        xo = C.lerp(x_out0, x_out1, s)
        xm = 0.5 * (xi + xo)
        xi = xm + (xi - xm) * (0.90 + 0.10 * e)
        xo = xm + (xo - xm) * (0.90 + 0.10 * e)
        sec = _blade_section(xi, xo, C.lerp(z0, z1, s), C.lerp(curl0, curl1, s),
                             th * k)
        y = C.lerp(y0, y1, s)
        rings.append([(side * x, y, z) for (x, z) in sec][::side])
    return _loft_obj(name, rings, coll, mat, caps=True, smooth=32.0)


# Clutch paddle hinge line. It used to run along y = +0.0040 at x = 0.014..0.039,
# which is straight through the quick-release hub (HubPlate reaches r = 0.0482,
# QRBody r = 0.0362) while the blade itself started 11.5 mm away at y = -0.0075 -
# so the blade both floated off its own pivot and was buried in the hub. The
# whole group now lives outboard and below the hub: every part of it is at
# r > 0.050 from the hub axis, and the blade end is swallowed by the boss.
CL_PIV_Y = -0.0310       # spindle axis (local y)
CL_PIV_Z = -0.0186       # spindle axis (local z)
CL_LUG_X = (0.0505, 0.0690)
CL_LUG_Z = -0.0188       # lug bottom: stops short of the blade, which hangs
                         # 3.2 mm below the spindle so the lugs never pierce it


def _paddles(coll):
    obs = []
    py, pz = CL_PIV_Y, CL_PIV_Z
    for side, tag in ((1, "L"), (-1, "R")):
        sh = _paddle("Shift" + tag, side, coll,
                     0.0455, -0.0430,
                     0.0470, 0.0585, 0.1035, 0.0905,
                     -0.0240, -0.0268, 0.0150, 0.0122, 0.0040, ns=72)
        C.add_bevel(sh, width=0.0006, segments=2, angle=32.0)
        obs.append(sh)
        cl = _paddle("Clutch" + tag, side, coll,
                     py - 0.0015, -0.0690,
                     0.0490, 0.0530, 0.0810, 0.0740,
                     pz - 0.0032, pz - 0.0020, 0.0046, 0.0036, 0.0032, ns=46)
        C.add_bevel(cl, width=0.0005, segments=2, angle=32.0)
        obs.append(cl)

        # pivot bosses wrapped round the spindles - the blades visibly hinge
        boss = []
        boss.append(_rod_mesh(Vector((side * 0.0405, 0.0470, -0.0252)),
                              Vector((side * 0.0575, 0.0470, -0.0252)),
                              0.0072, 0.0072, seg=28))
        boss.append(_rod_mesh(Vector((side * 0.0550, py, pz)),
                              Vector((side * 0.0645, py, pz)),
                              0.0050, 0.0050, seg=24))
        v, f = _merge_meshes(boss)
        ob = _mk("PadBoss" + tag, v, f, coll, "CarbonFibre", smooth=34.0)
        obs.append(ob)

        # brackets bolted to the back skin
        br = []
        for bx in (0.0350, 0.0630):
            x0, x1 = sorted((side * (bx - 0.0055), side * (bx + 0.0055)))
            br.append(_box_pts(x0, x1, 0.0432, 0.0508, -0.0272, -0.0082))
        x0, x1 = sorted((side * 0.0330, side * 0.0650))
        br.append(_box_pts(x0, x1, 0.0446, 0.0500, -0.0180, -0.0082))
        for bx in CL_LUG_X:
            x0, x1 = sorted((side * (bx - 0.0045), side * (bx + 0.0045)))
            br.append(_box_pts(x0, x1, py - 0.0086, py + 0.0090,
                               CL_LUG_Z, -0.0082))
        x0, x1 = sorted((side * 0.0485, side * 0.0710))
        br.append(_box_pts(x0, x1, py - 0.0027, py + 0.0027, -0.0140, -0.0082))
        v, f = _merge_meshes(br)
        ob = _mk("PadBracket" + tag, v, f, coll, "CarbonMatte", smooth=34.0)
        C.add_bevel(ob, width=0.0010, segments=2, angle=32.0)
        obs.append(ob)

        rods = [_rod_mesh(Vector((side * 0.0338, 0.0470, -0.0252)),
                          Vector((side * 0.0642, 0.0470, -0.0252)),
                          0.0029, 0.0029, seg=22),
                _rod_mesh(Vector((side * 0.0485, py, pz)),
                          Vector((side * 0.0710, py, pz)),
                          0.0023, 0.0023, seg=20)]
        # return-spring can (shift only - there is no room beside the clutch
        # blade for one that is actually attached to something)
        rods.append(_rod_mesh(Vector((side * 0.0625, 0.0470, -0.0252)),
                              Vector((side * 0.0625, 0.0330, -0.0252)),
                              0.0038, 0.0032, seg=20))
        v, f = _merge_meshes(rods)
        obs.append(_mk("PadPivot" + tag, v, f, coll, "SteelFastener",
                       smooth=32.0))

        scr = []
        for (bx, by) in ((0.0380, 0.0455), (0.0590, 0.0455)):
            scr.append(_hex_screw(side * bx, by, -0.0270, r_head=0.0026,
                                  seg=18, depth=0.0010, head_h=0.0020,
                                  dn=-1.0))
        for bx in CL_LUG_X:
            scr.append(_hex_screw(side * bx, py + 0.0056, CL_LUG_Z - 0.0008,
                                  r_head=0.0026, seg=18, depth=0.0010,
                                  head_h=0.0020, dn=-1.0))
        v, f = _merge_meshes(scr)
        obs.append(_mk("PadScrews" + tag, v, f, coll, "SteelFastener",
                       smooth=32.0))
    return obs


# --------------------------------------------------------------------------- #
# quick-release hub
# --------------------------------------------------------------------------- #

HUB_SCR_A = 0.39         # phase of the 8-off hub plate screw circle

# Half a tooth of the 15-off QR spline (24 deg pitch), which is what it takes to
# drop our tooth tips into CI_column's socket grooves instead of onto its flanks.
SPL_CLOCK = math.radians(6.0)

# The joint contract with cockpit_interior, in wheel-local z (negative = forward,
# towards the dash). Anything on the column side has to agree with these:
#   z = -0.0500   column socket mouth / rear end face      (s = +50.000 mm)
#   z = -0.0502   QR body seating face, 0.2 mm inside it   (s = +50.200 mm)
#   z = -0.0652   spline nose, 15.2 mm into the bore       (s = +65.200 mm)
# In car-local world that puts the socket mouth on the QR axis at
#   (0.546359, 0.0, 0.481270)  -> (0.546359, 0.0, 0.821270) assembled.


def _hub(coll):
    obs = []
    plate = [(0.0000, -0.0087), (0.0240, -0.0085), (0.0420, -0.0081),
             (0.0468, -0.0083), (0.0482, -0.0094), (0.0482, -0.0138),
             (0.0466, -0.0152), (0.0420, -0.0160), (0.0380, -0.0166),
             (0.0372, -0.0180), (0.0355, -0.0188), (0.0000, -0.0188)]
    obs.append(_tube("HubPlate", plate, coll, "CarbonMatte", segments=128))

    # The QR body's nose used to stop dead at local z = -0.0480 on a bare
    # 19.0 mm stub, which put its front face 2.000 mm AXIALLY short of the
    # column's socket mouth (CI_column ends at local z = -0.0500, measured
    # s = +50.000 mm along the QR axis from the hub centre) and 2.973 mm from
    # the nearest column surface, so the male spline crossed an open slot with
    # nothing round it. The 24.0 mm land now runs on to a seating face at
    # z = -0.0502, 0.2 mm INSIDE the socket mouth: the face lands on the
    # socket's rear annulus (r 21.2..25.2 mm) over r 21.2..23.6 mm and the land
    # itself stays inside the socket's 25.2 mm rim, so the engagement is real
    # but never breaks a visible surface. It also buries the 2.2 mm of spline
    # that used to stand proud of the body.
    body = [(0.0000, -0.0179), (0.0120, -0.0181), (0.0260, -0.0184),
            (0.0352, -0.0186), (0.0362, -0.0196),
            (0.0362, -0.0232), (0.0350, -0.0244), (0.0300, -0.0250),
            (0.0296, -0.0262), (0.0300, -0.0356), (0.0290, -0.0368),
            (0.0244, -0.0372), (0.0240, -0.0384), (0.0240, -0.0470),
            (0.0238, -0.0478), (0.0238, -0.0498), (0.0236, -0.0502),
            (0.0000, -0.0502)]
    obs.append(_tube("QRBody", body, coll, "Titanium", segments=128))

    collar = [(0.0300, -0.0264, 0.0), (0.0344, -0.0272, 0.4),
              (0.0348, -0.0282, 1.0), (0.0348, -0.0334, 1.0),
              (0.0344, -0.0346, 0.4), (0.0300, -0.0352, 0.0),
              (0.0300, -0.0264, 0.0)]
    obs.append(_knurled("QRCollar", collar, coll, "AnodisedRed", teeth=54,
                        amp=0.0011, per_tooth=4, smooth=26.0))

    # Male QR spline. It was 1.0 mm undersize on radius and a quarter of a tooth
    # out of clock, so it hung in the middle of CI_column's bore with 1.225 mm
    # of air all round and ZERO triangles in common - the whole wheel was
    # mechanically floating on the column.
    #
    # The bore, ray-swept round the clock in this same frame, is
    #     r_bore(t) = 21.2 + 1.3 * (0.5 + 0.5 cos(15 (t - 18 deg)))  mm
    # i.e. 15 grooves peaking at 22.5 mm on t = 18 + 24k deg and 15 crests
    # bottoming at 21.2 mm on t = 6 + 24k deg. Untwisted, _knurled puts our
    # tooth TIPS on t = 12 + 24k deg - dead on the flanks, meshing nothing - so
    # SPL_CLOCK rotates them by +6 deg onto the grooves.
    #
    # Radii are then set for a real spline fit rather than a press: tips
    # 23.0 mm bite 0.5 mm into the 22.5 mm grooves, roots 20.4 mm clear the
    # 21.2 mm crests by 0.8 mm. All of it is inside the socket or inside the
    # QR body nose, so nothing here is on a visible surface.
    spl = [(0.0000, -0.0478, 0.0), (0.0205, -0.0478, 0.0),
           (0.0217, -0.0490, 0.6), (0.0217, -0.0630, 1.0),
           (0.0207, -0.0646, 0.4), (0.0175, -0.0652, 0.0),
           (0.0074, -0.0652, 0.0), (0.0062, -0.0640, 0.0),
           (0.0062, -0.0572, 0.0), (0.0000, -0.0566, 0.0)]
    obs.append(_knurled("QRSpline", spl, coll, "Titanium", teeth=15,
                        amp=0.0026, per_tooth=6, smooth=26.0,
                        twist=SPL_CLOCK))

    # Drive pins. They used to sit at r = 0.0272, entirely swallowed by the
    # HubPlate / QRBody / collar - 99% of their vertices tested inside hub
    # solids. They now stand on a bolt circle outboard of the QR body (r 0.0362)
    # and the collar (r 0.0354) and project back past the collar, where they
    # actually read. The half-pitch offset from the hub screws' own circle
    # (TAU*i/8 + HUB_SCR_A) is the maximum available angular clearance for a
    # 6-on-8 arrangement.
    pins = []
    for i in range(6):
        a = TAU * i / 6.0 + HUB_SCR_A + math.pi / 24.0
        cx, cy = 0.0400 * math.cos(a), 0.0400 * math.sin(a)
        # z0 is set so the domed root ends at -0.0137, below the moulded ribs
        # on the back skin (which reach -0.0129) but still 2.6 mm inside the
        # hub plate, whose rear face sits at about -0.0163 at this radius.
        pins.append(_rod_mesh(Vector((cx, cy, -0.0165)),
                              Vector((cx, cy, -0.0320)), 0.0028, 0.0025,
                              seg=20))
    v, f = _merge_meshes(pins)
    obs.append(_mk("QRPins", v, f, coll, "SteelFastener", smooth=32.0))

    scr = []
    for i in range(8):
        a = TAU * i / 8.0 + HUB_SCR_A
        scr.append(_hex_screw(0.0432 * math.cos(a), 0.0432 * math.sin(a),
                              -0.0172, r_head=0.0031, seg=22, depth=0.0012,
                              head_h=0.0022, dn=-1.0))
    v, f = _merge_meshes(scr)
    obs.append(_mk("HubScrews", v, f, coll, "SteelFastener", smooth=32.0))
    return obs


# --------------------------------------------------------------------------- #
# back structure + loom boot
# --------------------------------------------------------------------------- #

def _sweep_path(name, path, radii, coll, mat, seg=32, smooth=32.0):
    rings = []
    n = len(path)
    for i in range(n):
        p = Vector(path[i])
        a = Vector(path[min(n - 1, i + 1)]) - Vector(path[max(0, i - 1)])
        if a.length < 1e-9:
            a = Vector((0.0, 0.0, 1.0))
        a.normalize()
        ref = Vector((1.0, 0.0, 0.0))
        if abs(a.dot(ref)) > 0.9:
            ref = Vector((0.0, 1.0, 0.0))
        u = a.cross(ref).normalized()
        v = a.cross(u)
        r = radii[i]
        rings.append([tuple(p + (u * math.cos(TAU * k / seg)
                                 + v * math.sin(TAU * k / seg)) * r)
                      for k in range(seg)])
    return _loft_obj(name, rings, coll, mat, caps=True, smooth=smooth)


# moulded stiffening ribs on the back skin. Shared with the screw placer: a
# screw dropped onto a rib would be swallowed by it (the rib stands 2.6 mm
# proud of the back plate), so the placer walks along the bolt line to the
# nearest clear spot instead.
RIB_BARS = ((-0.055, -0.030, 1.15, 0.095),
            (0.055, -0.030, -1.15, 0.095),
            (-0.062, 0.036, -0.55, 0.082),
            (0.062, 0.036, 0.55, 0.082),
            (0.0, -0.070, 0.0, 0.108))
RIB_HW = 0.0045
BP_REAR = Z_BACK - 0.0028          # back plate outer face
LOOM = (0.0230, -0.0620, -0.0448)  # connector block half-width, y0, y1


def _clear_of_ribs(px, py, clear):
    """True if a fastener of radius `clear` at (px, py) lands on bare plate."""
    for (bx, by, ang, ln) in RIB_BARS:
        dx, dy = px - bx, py - by
        ca, sa = math.cos(ang), math.sin(ang)
        u = dx * ca + dy * sa
        v = -dx * sa + dy * ca
        if abs(u) <= ln * 0.5 + clear and abs(v) <= RIB_HW + clear:
            return False
    if (abs(px) <= LOOM[0] + clear
            and LOOM[1] - clear <= py <= LOOM[2] + clear):
        return False
    return True


def _back(coll):
    obs = []
    poly = shell_poly()
    cen = _centroid(poly)
    plate = _poly_scale(poly, 0.855, cen)
    obs.append(_slab("BackPlate", plate, BP_REAR, Z_BACK - 0.0008,
                     0.0009, coll, "CarbonMatte", steps=2))
    # Screws bite INTO the plate: head face 0.8 mm proud of the outer face at
    # BP_REAR, shank buried 1.3 mm in the 2 mm laminate. (They used to be
    # driven at Z_BACK - 0.0115, which left every head hanging 6.6 mm behind
    # the plate in open air.)
    scr = []
    edge = _poly_offset(plate, 0.0055)
    ne = len(edge)
    step = max(1, ne // 13)
    used = []
    for k in range(0, ne, step):
        pick = None
        for d in range(0, step // 2):
            for i in (k + d, k - d):
                p = edge[i % ne]
                if _clear_of_ribs(p[0], p[1], 0.0036):
                    pick = p
                    break
            if pick is not None:
                break
        if pick is None:
            continue
        if any((pick[0] - q[0]) ** 2 + (pick[1] - q[1]) ** 2 < 0.0150 ** 2
               for q in used):
            continue
        used.append(pick)
        scr.append(_hex_screw(pick[0], pick[1], BP_REAR - 0.0008, r_head=0.0028,
                              seg=20, depth=0.0011, head_h=0.0021, dn=-1.0))
    v, f = _merge_meshes(scr)
    obs.append(_mk("BackScrews", v, f, coll, "SteelFastener", smooth=32.0))

    ribs = []
    for (bx, by, ang, ln) in RIB_BARS:
        ribs.append(_bar(bx, by, ang, ln, 2.0 * RIB_HW,
                         Z_BACK - 0.0044, Z_BACK - 0.0028))
        ribs.append(_bar(bx, by, ang, ln - 0.010, 0.0056,
                         Z_BACK - 0.0054, Z_BACK - 0.0044))
    v, f = _merge_meshes(ribs)
    ob = _mk("BackRibs", v, f, coll, "CarbonMatte", smooth=34.0)
    C.add_bevel(ob, width=0.0009, segments=2, angle=32.0)
    obs.append(ob)

    # loom connector block on the lower back skin
    con = [_box_pts(-LOOM[0], LOOM[0], LOOM[1], LOOM[2],
                    Z_BACK - 0.0108, Z_BACK - 0.0030),
           _box_pts(-0.0196, 0.0196, -0.0604, -0.0464,
                    Z_BACK - 0.0126, Z_BACK - 0.0100)]
    v, f = _merge_meshes(con)
    ob = _mk("LoomBlock", v, f, coll, "MatteBlack", smooth=34.0)
    C.add_bevel(ob, width=0.0011, segments=2, angle=32.0)
    obs.append(ob)
    pins = []
    for i in range(8):
        px = -0.0154 + i * 0.0044
        pins.append(_rod_mesh(Vector((px, -0.0534, Z_BACK - 0.0122)),
                              Vector((px, -0.0534, Z_BACK - 0.0146)),
                              0.0012, 0.0012, seg=12))
    v, f = _merge_meshes(pins)
    obs.append(_mk("LoomPins", v, f, coll, "SteelFastener", smooth=32.0))

    # loom boot
    n = 34
    path, radii = [], []
    for i in range(n):
        t = i / (n - 1.0)
        y = -0.0510 - 0.0500 * t
        z = -0.0086 - 0.0240 * t - 0.0090 * t * t
        path.append((0.0, y, z))
        base = C.lerp(0.0118, 0.0082, t)
        corr = 0.0016 * math.sin(TAU * 5.5 * t - 0.6) if t > 0.16 else 0.0
        radii.append(base + corr)
    obs.append(_sweep_path("LoomBoot", path, radii, coll, "MatteBlack",
                           seg=40, smooth=44.0))

    # hose clamp: a short band swept on the boot's own path
    i0, i1 = 3, 7
    obs.append(_sweep_path("LoomClamp", path[i0:i1],
                           [radii[i] + 0.0013 for i in range(i0, i1)],
                           coll, "SteelFastener", seg=40, smooth=30.0))

    cab = []
    p0 = Vector(path[-1])
    for (dx, rr) in ((-0.0034, 0.0026), (0.0034, 0.0030), (0.0000, 0.0022)):
        cab.append(_rod_mesh(p0 + Vector((dx, 0.0030, 0.0020)),
                             p0 + Vector((dx * 1.6, -0.0180, -0.0130)),
                             rr, rr, seg=16))
    v, f = _merge_meshes(cab)
    obs.append(_mk("LoomCables", v, f, coll, "MatteBlack", smooth=44.0))

    # cable ties round the bundle
    ties = []
    for (t, rr) in ((0.30, 0.0062), (0.66, 0.0056)):
        c = p0 + Vector((0.0, -0.0180 * t + 0.0030 * (1 - t),
                         -0.0130 * t + 0.0020 * (1 - t)))
        ties.append(_rod_mesh(c + Vector((-0.0075, 0.0, 0.0)),
                              c + Vector((0.0075, 0.0, 0.0)),
                              rr, rr, seg=18, caps=2))
    v, f = _merge_meshes(ties)
    ob = _mk("LoomTies", v, f, coll, "MatteBlack", smooth=40.0)
    obs.append(ob)
    return obs


# --------------------------------------------------------------------------- #

def _plates(coll):
    """Machined data plates in the empty top corners of the face."""
    obs = []
    base, ins, riv = [], [], []
    for sx in (-1, 1):
        cx, cy = sx * 0.1040, 0.0735
        pl = _rr(0.0262, 0.0122, 0.0024, 5, 5, 3, cx, cy)
        base.append((pl, cx, cy))
        ins.append(_bar(cx, cy + 0.0020, 0.0, 0.0180, 0.0026,
                        Z_FACE + 0.0014, Z_FACE + 0.0018))
        for i in range(4):
            ins.append(_bar(cx - 0.0072 + i * 0.0048, cy - 0.0028, 0.0,
                            0.0032, 0.0012, Z_FACE + 0.0014, Z_FACE + 0.0017))
        for dx in (-0.0106, 0.0106):
            riv.append(_hex_screw(cx + dx, cy, Z_FACE + 0.0026,
                                  r_head=0.0022, seg=16, depth=0.0008,
                                  head_h=0.0018))
    for i, (pl, cx, cy) in enumerate(base):
        obs.append(_slab("Plate%d" % i, pl, Z_FACE - 0.0004, Z_FACE + 0.0014,
                         0.0006, coll, "CarbonMatte", steps=2))
    v, f = _merge_meshes(ins)
    obs.append(_mk("PlateEtch", v, f, coll, "Titanium", smooth=40.0))
    v, f = _merge_meshes(riv)
    obs.append(_mk("PlateRivets", v, f, coll, "SteelFastener", smooth=32.0))
    return obs


def build(coll, ctx=None):
    objs = []
    objs += _shell(coll)
    objs += _back(coll)
    objs += _grips(coll)
    objs += _display(coll)
    objs += _leds(coll)
    objs += _controls(coll)
    objs += _plates(coll)
    objs += _paddles(coll)
    objs += _hub(coll)
    return objs
