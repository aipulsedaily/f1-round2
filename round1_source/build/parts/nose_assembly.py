"""nose_assembly - the nose cone on the monocoque nose, x = +3.000 (FIA crash
structure tip) back to x = +1.900 (the chassis joint face).

Everything here is welded to the contract surface. Every point is the same
Catmull-Rom curve `spec.body_surface_point()` samples - evaluated at arbitrary
parameter instead of that helper's 65 discrete steps, so seams can be 1.9 mm
wide - then pushed out along the section normal by OFF = 3 mm, which is what
makes the cone read as a bonded structure sitting ON the monocoque skin instead
of z-fighting with it. `_selfcheck()` asserts the two agree to < 1e-9 m.

What is modelled
----------------
  * crash-structure tip: an elliptical rolled edge (15 mm along x, 5.0 mm in,
    4.0 mm down) into a slightly domed blunt face measuring 154 x 123 mm at the
    rim - the flattened bluff end the brief asks for, not a bulbous toe. The
    face is a square-topology disc patch, NOT a triangle fan, so there is no
    pole singularity exactly where the eye lands.
  * two forward-facing camera pods, each on a swept carbon fin whose footprint
    conforms to the skin: lens barrel, glass, index band, parting line, aft
    connector, fasteners.
  * a five-probe pitot rake on the crown: mast, cross bar, hollow probes with
    real chamfered bores.
  * the nose/chassis joint collar and its ring of spot-faced socket-cap screws.
  * the front bulkhead access panel, proud in a seating recess, with six
    quarter-turn (Dzus) fasteners in titanium receptacle rings.
  * underside pylon seats: a milled pocket in the belly either side, centred on
    y = +-0.048 at every station, with a titanium mating plate bonded into it
    presenting a TRUE flat at z = 0.2248 - 0.3 mm clear of the flat crown of
    front_wing's pylon flange - and four threaded inserts on its bolt pattern,
    bore threads modelled as real helical geometry.
  * panel seams as real recessed geometry (1.9 x 1.05 mm troughs): two
    longitudinal runs per side, two transverse section joints.
  * flush static ports, and a crown fillet that turns the spec section's 150 deg
    spine into a ~75 mm radius instead of a knife edge.

Defects found by rendering, and what fixed them (details at each site)
---------------------------------------------------------------------
  D-na-01  blunt face folded on itself - the tip roll was a normal offset and
           29 mm exceeds the belly chine's radius. Now an anisotropic shrink.
  D-na-02  collar looked banded between bolts. I blamed the 9:1 ring-density
           jump and rebased it (330 samples, worth keeping) - but re-rendering
           the same 9x crop showed the banding unchanged, so the diagnosis was
           wrong: it is the shared weave foreshortening, same root cause as
           D-na-06/11. Still present on the collar at grazing angles.
  D-na-03  camera mount read as a ribbon on an oval sticker. Now a swept fin
           whose footprint conforms to the skin; the separate pad is gone.
  D-na-04  cable boot ended in mid air once the fin head moved inside the pod.
           Replaced with an aft connector that is attached by construction.
  D-na-05  outer pitot probes' root bosses stood proud of the tapered cross bar
           as flat cylinder ends. Bar thickened to swallow them.
  D-na-06  cone interior: the shared weave foreshortens into 0.6 mm corduroy at
           grazing angles. Deep interior is matte black, laminate edge carbon.
  D-na-07  static ports were 24 mm chrome washers with a 44-segment polygonal
           brim. Now 18 mm, 0.5 mm proud, 64 segments.
  D-na-08  crossing seams summed depth and pitted at the junction. Deepest one
           wins instead.
  D-na-09  fin fore/aft runouts tapered to a razor. Boxier footprint.
  D-na-10  mast/bar/pod faceted along their superellipse corners - too few
           section samples under a 36 deg smooth threshold. Denser + 60 deg.

Round 2 - defects an independent reviewer proved by rendering and measuring
---------------------------------------------------------------------------
  D-na-12  blunt face measured 104 x 81 mm against a briefed ~150 x 130, and the
           last 38 mm of the cone ran up to 26 mm INSIDE the contract surface.
           Elliptical roll, no pinch: 154 x 123 mm, never more than 1.0 mm
           inside. (_shell_stations)
  D-na-13  the pylon boss skewed 42 mm sideways along its own length because its
           footprint was frozen in one station's arc coordinate, and its face
           followed the skin down instead of holding the mating plane, so
           front_wing's flange speared 4.5 mm into it. Now a milled pocket in
           the shell plus a plate on a true flat. (_feature_off, _build_boss)
  D-na-15  the threaded inserts were a non-monotone lathe profile capped through
           their own shank: negative volume, 288 self-intersections, and a blank
           disc in the render. Rebuilt as a closed section, pole to pole, with a
           real helical bore thread. (_gen_insert)
  D-na-17  pitot probe roots left chisel slivers on the cross bar and hung below
           and past it. The bar is resized so every root fits strictly inside
           its local section, and roots start 6 mm aft of the bar's centreline.
  D-na-19  connection audit rank 1: the joint collar ran straight through all
           six front-suspension chassis brackets. suspension_front bolts three
           pads per corner at x = 1.905 / 1.955 / 1.975 - dead inside the
           collar band - and the band stood +7.81 mm proud of the nominal
           station surface against a bracket boss reaching +10.0 mm, so the
           weave crossed the titanium 1.6 mm below its top face and left a hard
           intersection curve mid-plate. The band is now relieved (cut clear,
           square ends capped, bolts in the cut dropped) round each pickup, and
           NOSE_Shell carries a machined relief pocket under each footprint
           whose floor is 2.0 mm below the pad's own seating face, so nothing
           in this module reaches the height of a bracket any more. The pads'
           10-12 mm bite into the monocoque skin is correct seating and is
           untouched. See PICKUPS / _relief_* / _collar_cuts.
  D-na-18  the collar's weave ribbing. NOT fixed - see _build_collar. The
           geometry-side fix the reviewer suggested (re-author the flanks in a
           rotated frame) was built and rendered against the same crops and made
           it worse, and the material reads Object coordinates only, so UVs
           cannot help either. Reverted; reported open.

Coordinate contract: +X forward, +Y car left, +Z up, tyre contact z = 0.
"""

import math

import bmesh
import bpy
from mathutils import Vector

import common as C
import spec as S

NAME = "nose_assembly"
P = "NOSE_"
TAU = math.pi * 2.0

# --------------------------------------------------------------------------- #
# principal dimensions
# --------------------------------------------------------------------------- #

X_AFT = 1.9000              # chassis joint face
X_TIP = 3.0000              # crash-structure apex (spec.NOSE_TIP_X)
OFF = 0.0030                # shell stands this far proud of the spec skin
WALL = 0.0088               # laminate thickness seen at the joint face
AFT_R = 0.0018              # broken edge at the joint face
X_IN_END = 2.0600           # front bulkhead, seen inside the cone

# Crash-structure tip. D-na-12: a 23 mm circular roll plus a 6 mm pinch ate the
# blunt face down to 104 x 81 mm (brief: ~150 x 130) and pulled the last 38 mm of
# the cone up to 26 mm INSIDE spec.body_surface_point, which the assembled
# monocoque's own tip would then punch straight through. The roll is now an
# ellipse: it runs 15 mm in x but only pulls in 5.0 mm laterally / 4.0 mm
# vertically, so the face keeps the briefed size and the shell never falls more
# than 2 mm inside the contract surface.
TIP_DOME = 0.0012           # dome height of the blunt face
X_RIM = X_TIP - TIP_DOME    # 2.99880 - where the blunt face starts
TIP_RX = 0.0150             # roll run along x
TIP_DY = 0.0050             # roll pull-in, lateral
TIP_DZ = 0.0040             # roll pull-in, vertical
X_ROLL0 = X_RIM - TIP_RX    # 2.98380 - where the roll starts

CROWN_A = 0.0026            # crown fillet drop (< OFF: never sinks into the body)
CROWN_X0, CROWN_X1 = 1.9015, 1.9900   # faded out under the joint collar

# recessed panel seams
SEAM_W, SEAM_D = 0.00095, 0.00105     # half width / depth, metres
TS_W, TS_D = 0.00115, 0.00120
LSEAM_V = (0.300, 0.795)              # profile parameter of each longitudinal run
LSEAM_WIN = (1.9860, 2.0300, 2.9300, 2.9540)
TSEAM_X = (2.4200, 2.9560)

# front bulkhead access panel, in (x, arc-from-crown) metres
PAN_XC, PAN_HX = 2.1850, 0.1330
PAN_HS, PAN_R = 0.0570, 0.0250
PAN_GAP = 0.0024            # plate edge -> recess wall
PAN_REC_D, PAN_REC_W = 0.0014, 0.0018
PAN_T = 0.0030              # plate thickness

# joint collar
COL_BOLT_X = 1.9330
COL_BOLT_PITCH = 0.0430
COL_SPOT_R, COL_SPOT_W, COL_SPOT_D = 0.0072, 0.0026, 0.0011

# Front-suspension inboard pickups. D-na-19: suspension_front bolts three
# chassis pads per corner into exactly this station range and all three land on
# the joint collar - the audit measured the collar standing +7.81 mm proud of
# the nominal station surface at the upper-forward pad, i.e. 3.2 mm proud of the
# monocoque's own skin and 1.6 mm below the top of the pad's machined boss, so
# the band ran straight through six titanium brackets.
#
# Each pad is a squircle footprint laid out in (station, profile frac) about its
# anchor - hx along x, harc of skin arc across - in the SAME ring parameter this
# module uses, so the footprint maps to a rounded rectangle of those half sizes
# in (x, arc) with the four extremes touching and 11 mm of slack at the corners.
# Copied rather than imported: suspension_front is frozen, and a build-time
# import of a sibling part would make this module's geometry depend on module
# load order.
#       (station x, half length, profile frac, half arc)
PICKUPS = ((1.9550, 0.0480, 0.7810, 0.0350),      # upper wishbone, fwd leg
           (1.9050, 0.0470, 0.4380, 0.0310),      # steering rack exit
           (1.9750, 0.0480, 0.2190, 0.0350))      # lower wishbone, fwd leg
REL_R = 0.0240              # footprint corner radius
REL_CLR = 0.0025            # flat pocket floor runs this far past the footprint
# 8 mm of wall renders as a soft dent in the paint where the pocket is not
# covered by the monocoque skin - a 2.8 mm dip spread over 8 mm reads as damage,
# not as hardware. 5 mm turns the same dip into a moulded step you can point at.
REL_WALL = 0.0050           # blended pocket wall
REL_Z = 0.0002              # pocket floor, offset from the nominal surface
COL_CLR = 0.0100            # collar band stops this far short of a footprint
COL_MINSEG = 0.0450         # a leftover band shorter than this goes too

# camera pods
CAM_ROOT_X, CAM_ROOT_S = 2.6640, 0.1130
CAM_POD_X0, CAM_POD_X1 = 2.7100, 2.8320
CAM_Y, CAM_Z = 0.1560, 0.3560
CAM_HW, CAM_HH, CAM_SQ = 0.0212, 0.0194, 3.1

# pitot rake
PIT_BASE_X = 2.5850

# Front wing pylon interface. front_wing.py's FW_PylonFlange_L/R is an aerofoil
# saddle spanning x 2.858..2.968, y = 48 +- 19 mm, whose crown ring - the face it
# bolts up with - is a flat at z = 0.2245, with its four cap screws on
# (2.950, 0), (2.908, +-0.009), (2.883, 0).
#
# D-na-13: the nose belly at y = 48 mm runs z = 0.2177 at x = 2.858 up to 0.2269
# at x = 2.990, i.e. the flange's mating plane is up to 6.8 mm INSIDE the skin at
# the aft end of its own footprint. A pad laid on the skin therefore cannot
# present that plane: the old boss smin'd its way down the skin to 0.2190 and the
# flange speared 4.5 mm into it. The seat is now a real machined pocket - the
# shell is relieved up to a flat floor at PYL_FACE_Z + PAD_T over the footprint,
# and the titanium plate bonded into it presents the mating plane exactly.
PYL_Y = 0.0480
PYL_FACE_Z = 0.2248         # mating face: 0.3 mm clear of the flange crown
PYL_BOLTS = ((2.9500, 0.0), (2.9080, 0.0090), (2.9080, -0.0090), (2.8830, 0.0))
PAD_X0, PAD_X1 = 2.8480, 2.9820
PAD_XC, PAD_HX = 0.5 * (PAD_X0 + PAD_X1), 0.5 * (PAD_X1 - PAD_X0)
PAD_HS = 0.0250             # nominal footprint half width in y
PAD_R = 0.0080              # footprint corner radius
PAD_T = 0.0026              # plate thickness -> pocket floor
PAD_CLR = 0.0024            # keep the footprint this far inboard of the chine
PAD_EDGE = 0.0006           # plate inset beyond the pocket wall
POCKET_Z = PYL_FACE_Z + PAD_T

V_BASE = 216                # base ring samples before feature clustering


# --------------------------------------------------------------------------- #
# profile evaluation - the curve spec.body_surface_point() samples
# --------------------------------------------------------------------------- #

_CTRL = {}
_ARC = {}


def _ctrl(x):
    k = round(x, 6)
    c = _CTRL.get(k)
    if c is None:
        c = S.station_half(S.station_at(min(max(k, -2.47), 3.0)))
        _CTRL[k] = c
    return c


def _cr(pts_ctrl, u):
    """common.catmull_rom's curve, evaluated at arbitrary u in [0, 1]."""
    pts = [pts_ctrl[0]] + list(pts_ctrl) + [pts_ctrl[-1]]
    segs = len(pts) - 3
    u = 0.0 if u < 0.0 else (1.0 if u > 1.0 else u)
    f = u * segs
    seg = min(int(f), segs - 1)
    t = f - seg
    p0, p1, p2, p3 = pts[seg], pts[seg + 1], pts[seg + 2], pts[seg + 3]
    t2 = t * t
    t3 = t2 * t
    return (0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t
                   + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2
                   + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3),
            0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t
                   + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2
                   + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3))


def _sect(x, v):
    """Section point at station x, ring parameter v in [0, 2).

    v = 0 belly centreline, v = 1 crown centreline, v > 1 mirrors to the car's
    right. For v <= 1 this is exactly spec.body_surface_point(x, v).
    """
    v %= 2.0
    if v <= 1.0:
        return _cr(_ctrl(x), v)
    y, z = _cr(_ctrl(x), 2.0 - v)
    return (-y, z)


def _norm2(x, v, h=2.0e-4):
    a = _sect(x, v - h)
    b = _sect(x, v + h)
    ty, tz = b[0] - a[0], b[1] - a[1]
    d = math.hypot(ty, tz) or 1.0
    return (tz / d, -ty / d)


def _norm3(x, v):
    """Outward 3D normal of the section-swept surface at (x, v)."""
    ny, nz = _norm2(x, v)
    h = 0.0020
    a = _sect(x - h, v)
    b = _sect(x + h, v)
    tx = Vector((2.0 * h, b[0] - a[0], b[1] - a[1]))
    hv = 2.0e-4
    c = _sect(x, v - hv)
    d = _sect(x, v + hv)
    tv = Vector((0.0, d[0] - c[0], d[1] - c[1]))
    n = tv.cross(tx)
    if n.length < 1e-9:
        return (0.0, ny, nz)
    n.normalize()
    if n.y * ny + n.z * nz < 0.0:
        n = -n
    return tuple(n)


def _crown_alpha(x):
    """Half angle (rad) of the spec section's centreline spine at station x."""
    a = _sect(x, 1.0 - 1.5e-3)
    b = _sect(x, 1.0)
    return math.atan2(b[1] - a[1], max(a[0] - b[0], 1e-9))


def _arc_table(x, n=321):
    """(vs, signed arc from crown) at station x; +arc is the car's left flank."""
    k = round(x, 3)
    t = _ARC.get(k)
    if t is not None:
        return t
    vs = [2.0 * i / (n - 1) for i in range(n)]
    pts = [_sect(k, v) for v in vs]
    cum = [0.0]
    for i in range(1, n):
        cum.append(cum[-1] + math.dist(pts[i], pts[i - 1]))
    icr = (n - 1) // 2                       # v = 1.0 exactly (n is odd)
    t = (vs, [cum[icr] - c for c in cum])
    _ARC[k] = t
    return t


def _v_at_arc(x, s):
    """Ring parameter at signed arc s from the crown."""
    vs, ss = _arc_table(x)
    if s >= ss[0]:
        return vs[0]
    if s <= ss[-1]:
        return vs[-1]
    lo, hi = 0, len(ss) - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if ss[mid] > s:
            lo = mid
        else:
            hi = mid
    d = ss[lo] - ss[hi]
    t = 0.0 if abs(d) < 1e-12 else (ss[lo] - s) / d
    return vs[lo] + (vs[hi] - vs[lo]) * t


def _arc_at_v(x, v):
    vs, ss = _arc_table(x)
    f = (v % 2.0) / 2.0 * (len(vs) - 1)
    i = min(int(f), len(vs) - 2)
    return ss[i] + (ss[i + 1] - ss[i]) * (f - i)


def _v_of_y(x, y):
    """Ring parameter whose section point has this y (belly half only)."""
    lo, hi = (0.0, 0.60) if y >= 0.0 else (1.40, 2.00)
    for _ in range(44):
        mid = 0.5 * (lo + hi)
        if _sect(x, mid)[0] < y:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


# --------------------------------------------------------------------------- #
# small maths helpers
# --------------------------------------------------------------------------- #

def _ss(t):
    t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
    return t * t * (3.0 - 2.0 * t)


def _win(x, x0, x1, x2, x3):
    return _ss((x - x0) / max(x1 - x0, 1e-9)) * _ss((x3 - x) / max(x3 - x2, 1e-9))


def _smin(a, b, k):
    """Polynomial smooth minimum - numerically safe, unlike the exp() form."""
    h = max(0.0, min(1.0, 0.5 + 0.5 * (b - a) / k))
    return b * (1.0 - h) + a * h - k * h * (1.0 - h)


def _groove(d, w, depth):
    """Recessed seam cross-section: flat floor, C1 walls, zero outside +-w."""
    u = abs(d) / w
    if u >= 1.0:
        return 0.0
    if u <= 0.55:
        return -depth
    return -depth * (0.5 + 0.5 * math.cos(math.pi * (u - 0.55) / 0.45))


def _rrect(dx, dy, hx, hy, r):
    """Signed distance to a rounded rectangle (negative inside)."""
    qx = abs(dx) - (hx - r)
    qy = abs(dy) - (hy - r)
    return (math.hypot(max(qx, 0.0), max(qy, 0.0))
            + min(max(qx, qy), 0.0) - r)


def _crown_delta(x, s):
    """Circular fillet rounding off the spec section's centreline spine.

    The mirrored half profile meets itself at 2*alpha (alpha ~ 14.5 deg at the
    tip) - a real crease. A tangent circular arc of radius r drops the apex by
    A = r*(sec(alpha) - 1) and spans |s| < r*sin(alpha), so the radius follows
    from the drop we are willing to pay. Faded out under the joint collar, so
    the part still meets whatever spine the monocoque behind it carries.
    """
    fade = _ss((x - CROWN_X0) / (CROWN_X1 - CROWN_X0))
    if fade <= 0.0:
        return 0.0
    a = _crown_alpha(x)
    amp = CROWN_A * fade
    r = amp / max(1.0 / max(math.cos(a), 1e-6) - 1.0, 1e-6)
    d = r * math.sin(a)
    if abs(s) >= d:
        return 0.0
    return -amp - r + math.sqrt(max(r * r - s * s, 0.0)) + math.tan(a) * abs(s)


# --------------------------------------------------------------------------- #
# relief pockets round the front-suspension pickups (D-na-19)
# --------------------------------------------------------------------------- #

_PKDS = {}


def _pk_ds(x, f):
    """Skin arc per unit profile frac at (x, f) - suspension_front's _dsdf.

    That module sizes each pad's frac half extent as harc / dsdf sampled over
    +-0.010 frac. Sampling the same span here means the footprint below is the
    footprint the pad is actually built on, not a near miss: the ring parameter
    is shared, so with the same dsdf the two agree to the width of a line.
    """
    k = (round(x, 5), round(f, 5))
    d = _PKDS.get(k)
    if d is None:
        f0, f1 = max(0.0, f - 0.010), min(1.0, f + 0.010)
        d = abs(_arc_at_v(x, f1) - _arc_at_v(x, f0)) / (f1 - f0)
        _PKDS[k] = d
    return d


def _relief_sd(x, v):
    """Signed distance to the nearest pickup footprint, metres, neg = inside."""
    vv = v if v <= 1.0 else 2.0 - v         # both flanks carry the same corner
    d = 1.0
    for (x0, hx, f0, harc) in PICKUPS:
        d = min(d, _rrect(x - x0, (vv - f0) * _pk_ds(x0, f0), hx, harc, REL_R))
    return d


def _relief_w(x, v):
    """Pocket weight: 1 over the footprint + REL_CLR, 0 a wall width outside."""
    return _ss((REL_CLR + REL_WALL - _relief_sd(x, v)) / REL_WALL)


def _relief_fix(o):
    """Squash the joint-face laminate rings into the pocket.

    The aft face is a stack of FIXED offsets running from the inner wall out to
    OFF - AFT_R. Left alone inside a pocket its outer edge stands a millimetre
    proud of the floor and rings each pad with a lip; clamped to the floor the
    outer rings collapse onto each other and shade as zero-area slivers. Scaling
    the whole stack about the inner wall until its outer edge lands exactly on
    the floor keeps every ring ordered, distinct and below the pad.
    """
    return -WALL + (o + WALL) * ((REL_Z + WALL) / (OFF - AFT_R + WALL))


_CUTS = None


def _collar_cuts():
    """Profile-frac intervals where the joint collar band is relieved.

    One interval per pickup, its footprint widened by COL_CLR so the band ends
    clear of the bracket rather than kissing it, then merged: the rack exit and
    the lower-forward pad sit 36 mm apart and the stub of band left between them
    would be half as long as the band is wide, which reads as debris rather than
    as hardware.
    """
    global _CUTS
    if _CUTS is None:
        iv = []
        for (x0, hx, f0, harc) in PICKUPS:
            h = (harc + COL_CLR) / _pk_ds(x0, f0)
            iv.append([f0 - h, f0 + h])
        iv.sort()
        out = [iv[0]]
        for lo, hi in iv[1:]:
            gap = _arc_at_v(COL_BOLT_X, out[-1][1]) - _arc_at_v(COL_BOLT_X, lo)
            if gap < COL_MINSEG:
                out[-1][1] = max(out[-1][1], hi)
            else:
                out.append([lo, hi])
        _CUTS = tuple((a, b) for a, b in out)
    return _CUTS


def _collar_keep(v):
    vv = v if v <= 1.0 else 2.0 - v
    return not any(lo <= vv <= hi for (lo, hi) in _collar_cuts())


# --------------------------------------------------------------------------- #
# ring / station sampling
# --------------------------------------------------------------------------- #

def _cluster(a, b, n, bumps, periodic=False, mind=None):
    """Monotone sample list over [a, b] with extra density inside each bump."""
    if periodic:
        vals = [a + (b - a) * i / n for i in range(n)]
    else:
        vals = [a + (b - a) * i / (n - 1) for i in range(n)]
    for (c, hw, m) in bumps:
        for i in range(m):
            v = c - hw + 2.0 * hw * i / (m - 1)
            if periodic:
                v = a + ((v - a) % (b - a))
            vals.append(v)
    vals = sorted(v for v in vals if a - 1e-12 <= v <= b + 1e-12)
    if mind is None:
        mind = (b - a) * 1.0e-4
    out = []
    for v in vals:
        if out and v - out[-1] < mind:
            continue
        out.append(v)
    if periodic and out and (b - out[-1]) < mind:
        out.pop()
    return out


def _make_vs():
    """Ring parameters. The count is forced to a multiple of 4 so the blunt-face
    disc patch (4*(K-1) boundary points) welds vertex-for-vertex to the rim."""
    bumps = [(1.0, 0.036, 27)]
    for f in LSEAM_V:
        bumps.append((f, 0.0075, 15))
        bumps.append((2.0 - f, 0.0075, 15))
    for sgn in (1.0, -1.0):
        v = _v_at_arc(PAN_XC, sgn * (PAN_HS + PAN_GAP))
        bumps.append((v, 0.0090, 17))
    # Pylon seat pocket walls. The wall turns through ~135 deg over its own
    # width, so it needs about five ring samples across or the facets break the
    # 40 deg smooth threshold irregularly and the rim renders as crumpled foil.
    # The constant-y edge also maps to a v that drifts along the pad, so each
    # edge gets a bump spanning its whole v range.
    for sgn in (1.0, -1.0):
        for out in (-1.0, 1.0):
            vv = []
            for x in (PAD_X0, PAD_XC, PAD_X1):
                y = PYL_Y + out * _pad_hs(x)
                v = _v_of_y(x, y * sgn)
                vv.append(v)
            c = 0.5 * (min(vv) + max(vv))
            hw = 0.5 * (max(vv) - min(vv)) + 0.0050
            # size the bump by ARC, not by v: v is the Catmull-Rom parameter, and
            # over the belly segment it stretches to ~440 mm per unit against a
            # ring average of 225, so a v-uniform bump lands 1.8 mm apart exactly
            # where the wall needs 0.55.
            arc = abs(_arc_at_v(PAD_XC, c + hw) - _arc_at_v(PAD_XC, c - hw))
            bumps.append((c, hw, max(9, int(round(arc / 0.00055)))))
    # Pickup relief pockets (D-na-19). Each wall drops 2.8 mm over its 5 mm
    # width, turning through ~100 deg, so it wants six samples across; at the
    # base ring pitch of 5.7 mm it would get one. The walls sit at a CONSTANT
    # frac - the pad footprint is laid out in frac, not in arc - so unlike the
    # pylon seat these bumps do not have to be widened for drift.
    for (x0, hx, f0, harc) in PICKUPS:
        ds = _pk_ds(x0, f0)
        hw = (0.5 * REL_WALL + 0.0020) / ds
        for sgn in (1.0, -1.0):
            for out in (-1.0, 1.0):
                c = f0 + out * (harc + REL_CLR + 0.5 * REL_WALL) / ds
                if sgn < 0.0:
                    c = 2.0 - c
                bumps.append((c, hw, max(7, int(round(2.0 * hw * ds / 0.0010)))))
    vs = _cluster(0.0, 2.0, V_BASE, bumps, periodic=True, mind=2.0e-4)
    while len(vs) % 4:
        gaps = [(vs[(i + 1) % len(vs)] - vs[i]) % 2.0 for i in range(len(vs))]
        i = max(range(len(vs)), key=lambda k: gaps[k])
        vs.append((vs[i] + gaps[i] * 0.5) % 2.0)
        vs.sort()
    return vs


def _make_xs():
    bumps = [(TSEAM_X[0], 0.0024, 13), (TSEAM_X[1], 0.0024, 13),
             (PAN_XC - PAN_HX - PAN_GAP, 0.0038, 11),
             (PAN_XC + PAN_HX + PAN_GAP, 0.0038, 11),
             (PAD_X0, 0.0050, 17), (PAD_X1, 0.0050, 17),   # seat pocket walls
             # The pocket's long walls run along x and their y position tapers
             # with the chine, so at the base 9 mm station pitch the wall foot
             # jumped ~1 mm per station and the rim rendered as a crumpled zigzag.
             # 3.5 mm stations across the whole seat keep it a straight line.
             (PAD_XC, PAD_HX + 0.0050, 41),
             (X_ROLL0, 0.0080, 9)]                         # roll tangency
    for (x0, hx, f0, harc) in PICKUPS:                     # pickup pocket walls
        for out in (-1.0, 1.0):
            bumps.append((x0 + out * (hx + REL_CLR + 0.5 * REL_WALL),
                          0.5 * REL_WALL + 0.0020, 9))
    return _cluster(X_AFT + AFT_R, X_ROLL0, 116, bumps, mind=4.0e-4)


_VS = None
_ICROWN = 0
_ISEAM = ()


def _prepare():
    global _VS, _ICROWN, _ISEAM
    if _VS is not None:
        return
    _VS = _make_vs()
    _ICROWN = min(range(len(_VS)), key=lambda i: abs(_VS[i] - 1.0))
    idx = []
    for f in LSEAM_V:
        for v in (f, 2.0 - f):
            idx.append(min(range(len(_VS)), key=lambda i: abs(_VS[i] - v)))
    _ISEAM = tuple(idx)


class _Sta:
    """One station: section points, normals and arc coordinate along the ring."""

    __slots__ = ("x", "p", "n", "s")

    def __init__(self, x, vs, icrown=None):
        self.x = x
        self.p = [_sect(x, v) for v in vs]
        self.n = [_norm2(x, v) for v in vs]
        cum = [0.0]
        for i in range(1, len(vs)):
            cum.append(cum[-1] + math.dist(self.p[i], self.p[i - 1]))
        if icrown is None:
            icrown = min(range(len(vs)), key=lambda i: abs(vs[i] - 1.0))
        c0 = cum[icrown]
        self.s = [c0 - c for c in cum]


def _feature_off(sta, j, xr):
    """Seam / recess relief at (station, ring index). Metres, negative = inward."""
    s = sta.s[j]
    off = _crown_delta(sta.x, s)

    # D-na-08: grooves used to sum. Where a transverse seam crosses a
    # longitudinal one that made a 2.25 mm pit at the junction - visible as a
    # dark blob at 9x. Panel lines do not get deeper where they meet, so take
    # the deepest single groove instead.
    g = 0.0
    w = _win(xr, *LSEAM_WIN)
    if w > 0.002:
        for js in _ISEAM:
            d = s - sta.s[js]
            if abs(d) < SEAM_W:
                g = min(g, w * _groove(d, SEAM_W, SEAM_D))
    for xs in TSEAM_X:
        if abs(xr - xs) < TS_W:
            g = min(g, _groove(xr - xs, TS_W, TS_D))

    # D-na-13: pylon seat pocket. The mating plane the front wing bolts to lies
    # ABOVE the belly skin over the aft half of the flange footprint, so the seat
    # has to be milled INTO the cone, not laid on it. Drive the surface up to a
    # flat floor at POCKET_Z: solving z + nz*(OFF + off) = POCKET_Z for off keeps
    # the floor a true plane whatever the section is doing underneath.
    y, z = sta.p[j]
    ny, nz = sta.n[j]
    pk = 0.0
    if nz < -0.25 and PAD_X0 - 0.009 < xr < PAD_X1 + 0.009:
        d = _pad_sd(xr, abs(y))
        if d < 0.0:
            znat = z + nz * OFF
            if znat < POCKET_Z:
                w2 = _ss(-d / _pocket_w(xr))
                pk = w2 * (POCKET_Z - znat) / nz
                g *= 1.0 - w2       # a panel line does not cross a machined seat
    off += g + pk

    sd = _rrect(xr - PAN_XC, s, PAN_HX + PAN_GAP, PAN_HS + PAN_GAP, PAN_R)
    if sd < 0.0:
        off -= PAN_REC_D * _ss(-sd / PAN_REC_W)
    return off


def _pad_hs(x):
    """Pylon seat half width (in y) at station x.

    Clamped so the footprint stays PAD_CLR inboard of the belly chine: the
    section shrinks fast toward the tip (bw = 78 mm at x = 2.852, 64 mm at
    2.980) and a constant-width pad climbs onto the chine, which is what made
    the old boss stand clear of the belly in side elevation.
    """
    lim = S.station_at(x)[1] - PYL_Y - PAD_CLR
    return max(0.004, _smin(PAD_HS, lim, 0.0025))


def _pad_sd(x, ay):
    """Signed distance to the pylon seat footprint (ay = |y|), negative inside."""
    return _rrect(x - PAD_XC, ay - PYL_Y, PAD_HX, _pad_hs(x), PAD_R)


_PDEPTH = {}


def _pocket_depth(x):
    """How far the seat floor stands above the natural skin at the seat centre."""
    k = round(x, 5)
    d = _PDEPTH.get(k)
    if d is None:
        z = _conform_pt(k, _arc_at_v(k, _v_of_y(k, PYL_Y)), 0.0)[2]
        d = max(0.0, POCKET_Z - z)
        _PDEPTH[k] = d
    return d


def _pocket_w(x):
    """Width of the seat's blended wall at station x.

    The wall turns through 2*atan(1.5*depth/width) across its own width. The
    seat is 10.3 mm deep at the aft end and 1.5 mm at the front, so a constant
    width either leaves the deep end as a stack of 60 deg facets - which the
    40 deg smooth threshold then marks sharp in an irregular dotted pattern, and
    THAT is what made the rim render as crumpled foil - or eats the whole plate
    at the shallow end. Tying the width to the local depth holds every facet
    under the threshold with a wall no wider than it has to be.
    """
    return min(0.0085, max(0.0025, 0.80 * _pocket_depth(x)))


def _shrink_ring(ring, dy, dz):
    """Pull a section ring in by (dy, dz) metres - about its centroid.

    D-na-01: doing this as a normal offset (the obvious way, and what the roll
    used to do) self-intersects the moment d exceeds the local convex radius.
    The belly chine near the tip is a ~10 mm radius and the roll asked for 29 mm,
    so the offset swallowtailed and the blunt face grew a visible fold with a
    ragged black self-intersection line straight down the middle of it. A scale
    about the centroid can never fold, and scaling y and z independently keeps
    the roll exactly circular at the four extreme points, which is where the
    silhouette is read.
    """
    n = len(ring)
    cy = sum(p[1] for p in ring) / n
    cz = sum(p[2] for p in ring) / n
    w = max(abs(p[1] - cy) for p in ring)
    h = max(abs(p[2] - cz) for p in ring)
    sy = max(0.02, 1.0 - dy / max(w, 1e-6))
    sz = max(0.02, 1.0 - dz / max(h, 1e-6))
    return [(p[0], cy + (p[1] - cy) * sy, cz + (p[2] - cz) * sz) for p in ring]


# --------------------------------------------------------------------------- #
# mesh assembly helpers
# --------------------------------------------------------------------------- #

def _obj(name, verts, faces, coll, mats, fmat=None, smooth=35.0, merge=1e-5):
    ob = C.new_obj(name, verts, faces, coll=coll, smooth=True)
    me = ob.data
    if fmat is not None and len(me.polygons) == len(fmat):
        for i, p in enumerate(me.polygons):
            p.material_index = fmat[i]
    elif fmat is not None:
        print(f"!! {name}: fmat {len(fmat)} != polys {len(me.polygons)}")
    if merge:
        C.merge_doubles(ob, merge)
    for m in mats:
        C.assign(ob, S.mat(m), slot=len(ob.data.materials))
    if smooth is not None:
        C.shade_auto_smooth(ob, smooth)
    return ob


def _cut_holes(ob, cutter_verts, cutter_faces, coll, name):
    """DIFFERENCE `ob` with a throwaway solid, and bake the result in.

    A structured grid cannot carry a clean circular hole, and without real holes
    the plate is solid behind every insert - which is exactly why the inserts
    used to render as blank discs: their bores were drilled into a face the
    plate's own skin then covered up. The cut is applied at build time and the
    cutter deleted, so nothing extra survives into the scene.
    """
    cut = C.new_obj(name, cutter_verts, cutter_faces, coll=coll, smooth=False)
    # Both operands have to be in the view layer or the depsgraph evaluates the
    # object unmodified and the cut silently does nothing.
    sc = bpy.context.scene.collection
    borrowed = [o for o in (ob, cut) if o.name not in sc.objects]
    for o in borrowed:
        sc.objects.link(o)
    m = ob.modifiers.new("HoleCut", "BOOLEAN")
    m.operation = "DIFFERENCE"
    m.solver = "EXACT"
    m.object = cut
    bpy.context.view_layer.update()
    deps = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(deps),
                                         depsgraph=deps)
    old = ob.data
    ob.modifiers.remove(m)
    for o in borrowed:
        if o is not cut:
            sc.objects.unlink(o)
    if len(me.polygons) == len(old.polygons):
        print(f"!! {ob.name}: boolean cut produced no change")
    ob.data = me
    cutdata = cut.data
    me.name = old.name
    if old.users == 0:
        bpy.data.meshes.remove(old)
    bpy.data.objects.remove(cut, do_unlink=True)
    if cutdata.users == 0:          # keep repeat builds from leaking datablocks
        bpy.data.meshes.remove(cutdata)
    # EXACT leaves a handful of zero-area slivers along the cut. They shade as
    # speckle at hero zoom, so dissolve them out.
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=9.0e-5)
    bmesh.ops.dissolve_degenerate(bm, dist=9.0e-5, edges=bm.edges)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    me.update()
    return ob


def _emit(V, F, verts, faces):
    o = len(V)
    V.extend(verts)
    F.extend([tuple(o + i for i in f) for f in faces])


def _bridge(faces, a, b, n, fmat=None, mi=0):
    for j in range(n):
        j2 = (j + 1) % n
        faces.append((a + j, a + j2, b + j2, b + j))
        if fmat is not None:
            fmat.append(mi)


def _frame(origin, axis, ref=(0.0, 0.0, 1.0)):
    ez = Vector(axis).normalized()
    r = Vector(ref)
    if abs(r.dot(ez)) > 0.94:
        r = Vector((1.0, 0.0, 0.0))
        if abs(r.dot(ez)) > 0.94:
            r = Vector((0.0, 1.0, 0.0))
    ex = (r - ez * r.dot(ez)).normalized()
    return Vector(origin), ex, ez.cross(ex), ez


def _hex_r(t, r):
    """Radius of a hexagon (across-flats r) at polar angle t."""
    a = (t + math.pi / 6.0) % (math.pi / 3.0) - math.pi / 6.0
    return r / math.cos(a)


def _gen_lathe(fr, prof, seg=48, close_ends=True):
    """Solid of revolution about the frame's z axis.

    prof entries are (radius, height) or (radius, height, "hex"). radius 0 emits
    a single pole vertex and a triangle fan, so there are never degenerate quads.
    """
    o, ex, ey, ez = fr
    V, F = [], []
    rings = []
    for e in prof:
        r, h = e[0], e[1]
        hexy = len(e) > 2 and e[2] == "hex"
        if r < 1e-7:
            rings.append(("pole", len(V)))
            V.append(tuple(o + ez * h))
            continue
        base = len(V)
        for i in range(seg):
            t = TAU * i / seg
            rr = _hex_r(t, r) if hexy else r
            V.append(tuple(o + ex * (rr * math.cos(t))
                           + ey * (rr * math.sin(t)) + ez * h))
        rings.append(("ring", base))
    for k in range(len(rings) - 1):
        (ka, a), (kb, b) = rings[k], rings[k + 1]
        if ka == "pole" and kb == "ring":
            for i in range(seg):
                F.append((a, b + (i + 1) % seg, b + i))
        elif ka == "ring" and kb == "pole":
            for i in range(seg):
                F.append((a + i, a + (i + 1) % seg, b))
        elif ka == "ring" and kb == "ring":
            for i in range(seg):
                i2 = (i + 1) % seg
                F.append((a + i, a + i2, b + i2, b + i))
    if close_ends:
        if rings[0][0] == "ring":
            F.append(tuple(range(rings[0][1], rings[0][1] + seg))[::-1])
        if rings[-1][0] == "ring":
            F.append(tuple(range(rings[-1][1], rings[-1][1] + seg)))
    return V, F


def _tri(u):
    return 1.0 - abs(2.0 * u - 1.0)


def _gen_insert(fr, seg=28, r_out=0.0074, h_top=0.0132, r_maj=0.0035,
                r_min=0.0029, pitch=0.0010, h0=0.0036, h1=0.0110,
                r_cb=0.0047, h_cb=0.0030):
    """Bonded threaded insert: flanged sleeve with a real helical bore thread.

    D-na-15 (was): _gen_lathe was handed a profile that ended
    (0.0074, -0.0009) -> (0.0074, +0.0016) - it turned round and ran back up the
    OUTSIDE at constant radius - and close_ends then capped that with an n-gon
    at h = +0.0016 which sliced straight through the r = 0.0034 shank. Signed
    volume came out negative (-5.0e-7 m3) with 288 self-intersecting triangle
    pairs per side, and from below the insert rendered as a plain flat disc.
    This profile is a single closed cross-section, pole to pole, so there is
    nothing to cap and nothing to self-intersect; the bore carries a 1.0 mm
    pitch thread as actual geometry.

    The 9.4 mm counterbore is not decoration: front_wing's pylon cap screws are
    built head-UP off the flange crown (head r = 4.0 mm reaching z = 0.2271,
    i.e. 2.3 mm above this plate's mating face), so without a clearance recess
    every one of them would bury itself in the plate.
    """
    o, ex, ey, ez = fr
    V, F = [], []
    rings = []

    def add_ring(rfun, h):
        base = len(V)
        for i in range(seg):
            t = TAU * i / seg
            r = rfun(t)
            V.append(tuple(o + ex * (r * math.cos(t))
                           + ey * (r * math.sin(t)) + ez * h))
        rings.append(("ring", base))

    def add_pole(h):
        rings.append(("pole", len(V)))
        V.append(tuple(o + ez * h))

    def const(r):
        return lambda _t: r

    add_pole(h_top)                       # closed top, buried in the plate
    add_ring(const(r_out), h_top)
    add_ring(const(r_out), 0.0020)        # sleeve wall
    add_ring(const(r_out - 0.0006), 0.0006)
    add_ring(const(r_out - 0.0010), 0.0000)   # broken rim at the mating face
    add_ring(const(r_cb + 0.0006), 0.0000)    # annular face
    add_ring(const(r_cb), 0.0006)             # counterbore lead-in
    add_ring(const(r_cb), h_cb)               # counterbore wall
    add_ring(const(0.0040), h_cb + 0.0006)    # counterbore floor
    add_ring(const(0.0038), h0)           # bore lead-in chamfer
    n = max(8, int(round((h1 - h0) / 0.00035)))
    for k in range(n + 1):
        h = h0 + (h1 - h0) * k / n
        add_ring(lambda t, h=h: r_maj - (r_maj - r_min)
                 * _tri(((h - pitch * t / TAU) / pitch) % 1.0), h)
    add_ring(const(r_min), h1 + 0.0009)   # blind bottom of the bore
    add_pole(h1 + 0.0022)

    for k in range(len(rings) - 1):
        (ka, a), (kb, b) = rings[k], rings[k + 1]
        if ka == "pole":
            for i in range(seg):
                F.append((a, b + (i + 1) % seg, b + i))
        elif kb == "pole":
            for i in range(seg):
                F.append((a + i, a + (i + 1) % seg, b))
        else:
            for i in range(seg):
                i2 = (i + 1) % seg
                F.append((a + i, a + i2, b + i2, b + i))
    return V, F


def _gen_screw(fr, r_head=0.0045, h_head=0.0030, r_sock=0.0023, d_sock=0.0018,
               seg=32, sink=0.0022):
    """Socket-cap screw: chamfered head with a real hex socket in it."""
    prof = [(0.0, -sink), (r_head, -sink), (r_head, h_head - 0.0006),
            (r_head - 0.0005, h_head), (r_sock + 0.0004, h_head),
            (r_sock, h_head - 0.0003, "hex"),
            (r_sock, h_head - d_sock, "hex"), (0.0, h_head - d_sock)]
    return _gen_lathe(fr, prof, seg=seg, close_ends=False)


# --------------------------------------------------------------------------- #
# square-topology disc patch (no pole, no fan)
# --------------------------------------------------------------------------- #

def _square_border(K):
    b = []
    for i in range(K - 1):
        b.append((i, 0))
    for j in range(K - 1):
        b.append((K - 1, j))
    for i in range(K - 1, 0, -1):
        b.append((i, K - 1))
    for j in range(K - 1, 0, -1):
        b.append((0, j))
    return b


def _square_u(a, b):
    """Fractional position (0..1) around the unit square, in the same order and
    from the same origin as _square_border()."""
    if abs(a) >= abs(b):
        d = (2.0 + (b + 1.0)) if a > 0.0 else (6.0 + (1.0 - b))
    else:
        d = (4.0 + (1.0 - a)) if b > 0.0 else (a + 1.0)
    return (d / 8.0) % 1.0


def _disc_patch(loop, K):
    """Map a closed 2D loop of 4*(K-1) points onto a K x K grid.

    Concentric-square mapping: grid ring m becomes the loop scaled about its
    centroid by rho = m/(K-1), and position around that ring is the loop's own
    index parameter. So (a) boundary cell k is exactly loop[k] - the patch welds
    vertex-for-vertex to whatever ring it caps - (b) cell aspect stays sane all
    the way in, unlike the elliptical map which crushes the four corner cells to
    slivers, and (c) there is no pole at all.

    Returns (grid, rho), both K x K.
    """
    n = len(loop)
    assert n == 4 * (K - 1), (n, K)
    cx = sum(p[0] for p in loop) / n
    cy = sum(p[1] for p in loop) / n
    border = {ij: k for k, ij in enumerate(_square_border(K))}
    grid = [[None] * K for _ in range(K)]
    rho = [[0.0] * K for _ in range(K)]
    for i in range(K):
        for j in range(K):
            if (i, j) in border:
                grid[i][j] = loop[border[(i, j)]]
                rho[i][j] = 1.0
                continue
            a = -1.0 + 2.0 * i / (K - 1)
            b = -1.0 + 2.0 * j / (K - 1)
            r = max(abs(a), abs(b))
            if r < 1e-12:
                grid[i][j] = (cx, cy)
                continue
            t = _square_u(a / r, b / r) * n
            k = int(t) % n
            f = t - int(t)
            p0, p1 = loop[k], loop[(k + 1) % n]
            px = p0[0] + (p1[0] - p0[0]) * f
            py = p0[1] + (p1[1] - p0[1]) * f
            grid[i][j] = (cx + r * (px - cx), cy + r * (py - cy))
            rho[i][j] = r
    return grid, rho


def _patch_faces(idx):
    K = len(idx)
    return [(idx[i][j], idx[i + 1][j], idx[i + 1][j + 1], idx[i][j + 1])
            for i in range(K - 1) for j in range(K - 1)]


# --------------------------------------------------------------------------- #
# the shell
# --------------------------------------------------------------------------- #

def _shell_stations():
    """Ordered ring specs: bulkhead -> liner -> joint face -> skin -> tip."""
    st = []
    for f in (0.055, 0.22, 0.46, 0.70, 0.88, 1.0):     # dished front bulkhead
        st.append(dict(xs=X_IN_END, xa=X_IN_END + 0.0105 * (1.0 - f * f),
                       mode="fix", off=-WALL, scale=f, mi=2))
    n = 9
    for i in range(1, n + 1):                          # inner laminate wall
        x = X_IN_END + (1.9008 - X_IN_END) * (i / n)
        st.append(dict(xs=x, xa=x, mode="fix", off=-WALL, mi=2))
    st.append(dict(xs=X_AFT, xa=X_AFT, mode="fix", off=-WALL + 0.0008, mi=2))
    for o in (-0.0062, -0.0040, -0.0018, 0.0000, OFF - AFT_R):   # joint face
        st.append(dict(xs=X_AFT, xa=X_AFT, mode="fix", off=o,
                       mi=1 if o <= 0.0 else 0))
    for i in range(4, 0, -1):                          # rolled edge onto the skin
        th = 0.5 * math.pi * i / 5.0
        x = X_AFT + AFT_R * (1.0 - math.sin(th))
        st.append(dict(xs=x, xa=x, mode="surf",
                       d=-AFT_R * (1.0 - math.cos(th)), mi=0))
    for x in _make_xs():                               # the skin
        st.append(dict(xs=x, xa=x, mode="surf", d=0.0, mi=0))
    for i in range(1, 27):                             # roll into the blunt face
        th = 0.5 * math.pi * i / 26.0
        x = X_ROLL0 + TIP_RX * math.sin(th)
        c = 1.0 - math.cos(th)
        st.append(dict(xs=min(x, X_TIP), xa=x, mode="surf", d=0.0, mi=0,
                       shrink=(TIP_DY * c, TIP_DZ * c)))
    return st


def _build_shell(coll):
    _prepare()
    vs = _VS
    n = len(vs)
    verts, faces, fmat = [], [], []
    bases = []
    for st in _shell_stations():
        sta = _Sta(st["xs"], vs, _ICROWN)
        ring = []
        for j in range(n):
            y, z = sta.p[j]
            ny, nz = sta.n[j]
            if st["mode"] == "fix":
                o = st["off"]
            else:
                o = OFF + st["d"] + _feature_off(sta, j, st["xa"])
            # D-na-19: relief pocket round each front-suspension pickup. Driving
            # the surface to a fixed offset from the nominal station surface -
            # rather than subtracting a depth - means the floor is the same
            # machined plane whatever seam, roll or fillet passes underneath it.
            w = _relief_w(st["xa"], vs[j])
            if w > 0.0:
                tgt = _relief_fix(o) if st["mode"] == "fix" else REL_Z
                o += w * (tgt - o)
            ring.append((st["xa"], y + ny * o, z + nz * o))
        f = st.get("scale")
        if f is not None:
            cy = sum(p[1] for p in ring) / n
            cz = sum(p[2] for p in ring) / n
            ring = [(p[0], cy + f * (p[1] - cy), cz + f * (p[2] - cz))
                    for p in ring]
        sh = st.get("shrink")
        if sh is not None and (sh[0] > 0.0 or sh[1] > 0.0):
            ring = _shrink_ring(ring, sh[0], sh[1])
        base = len(verts)
        verts.extend(ring)
        if bases:
            _bridge(faces, bases[-1], base, n, fmat, st["mi"])
        bases.append(base)
    # cap the bulkhead's small centre ring with a fan (deep inside, never seen)
    ci = len(verts)
    verts.append((sum(verts[k][0] for k in range(n)) / n,
                  sum(verts[k][1] for k in range(n)) / n,
                  sum(verts[k][2] for k in range(n)) / n))
    for k in range(n):
        faces.append((ci, (k + 1) % n, k))
        fmat.append(1)

    # blunt face: square-topology disc patch welded to the rim ring
    rim = bases[-1]
    K = n // 4 + 1
    loop = [(verts[rim + k][1], verts[rim + k][2]) for k in range(n)]
    grid, rho = _disc_patch(loop, K)
    border = {ij: k for k, ij in enumerate(_square_border(K))}
    idx = [[0] * K for _ in range(K)]
    for i in range(K):
        for j in range(K):
            if (i, j) in border:
                idx[i][j] = rim + border[(i, j)]
            else:
                y, z = grid[i][j]
                idx[i][j] = len(verts)
                verts.append((X_RIM + TIP_DOME * (1.0 - rho[i][j] ** 2), y, z))
    for f in _patch_faces(idx):
        faces.append(f)
        fmat.append(0)

    # D-na-06: the whole inside was CarbonMatte, and at the grazing angles you
    # actually see a cavity from, the shared weave texture foreshortens into a
    # 0.6 mm moire that reads as corduroy. The laminate edge round the joint
    # face still wants to be carbon - it is seen square-on - but the deep
    # interior is matte black, which is what an unpainted cone bore looks like
    # anyway.
    ob = _obj(P + "Shell", verts, faces, coll,
              ("LiveryPaint", "CarbonMatte", "MatteBlack"),
              fmat=fmat, smooth=40.0, merge=None)
    return [ob]


# --------------------------------------------------------------------------- #
# conformal fittings that sit on the skin
# --------------------------------------------------------------------------- #

def _conform_pt(x, s, off):
    """Point off metres out from the shell surface at (station x, arc s)."""
    v = _v_at_arc(x, s)
    y, z = _sect(x, v)
    ny, nz = _norm2(x, v)
    tot = OFF + off + _crown_delta(x, s)
    return (x, y + ny * tot, z + nz * tot)


def _conform_ring(xc, sc, prof, seg=48, rx=1.0, ry=1.0):
    """Lathe-like fitting wrapped onto the shell surface.

    prof = [(radius, offset)]; radius runs along the skin, offset along the
    surface normal relative to the shell's outer surface.
    """
    V, F = [], []
    rings = []
    for (r, o) in prof:
        if r < 1e-7:
            rings.append(("pole", len(V)))
            V.append(_conform_pt(xc, sc, o))
            continue
        base = len(V)
        for i in range(seg):
            t = TAU * i / seg
            V.append(_conform_pt(xc + r * rx * math.cos(t),
                                 sc + r * ry * math.sin(t), o))
        rings.append(("ring", base))
    for k in range(len(rings) - 1):
        (ka, a), (kb, b) = rings[k], rings[k + 1]
        if ka == "pole":
            for i in range(seg):
                F.append((a, b + (i + 1) % seg, b + i))
        elif kb == "pole":
            for i in range(seg):
                F.append((a + i, a + (i + 1) % seg, b))
        else:
            for i in range(seg):
                i2 = (i + 1) % seg
                F.append((a + i, a + i2, b + i2, b + i))
    # Close whichever end ring is not a pole. These fittings are seated below
    # the skin they sit on, so the cap is buried - but leaving it off left an
    # open boundary loop in a hero asset, which is a light leak waiting to
    # happen the moment anything moves.
    for (k, rev) in ((0, True), (len(rings) - 1, False)):
        kind, b = rings[k]
        if kind != "ring":
            continue
        cap = tuple(range(b, b + seg))
        F.append(cap[::-1] if rev else cap)
    return V, F


def _rrect_loop(hx, hy, r, n):
    """CCW rounded-rectangle loop of exactly n points, centred on the origin."""
    ax, ay = hx - r, hy - r
    q = 0.5 * math.pi * r
    per = 4.0 * (ax + ay) + 4.0 * q
    out = []
    for i in range(n):
        d = per * i / n
        if d < 2 * ax:
            out.append((-ax + d, -hy))
            continue
        d -= 2 * ax
        if d < q:
            t = d / r
            out.append((ax + r * math.sin(t), -ay - r * math.cos(t)))
            continue
        d -= q
        if d < 2 * ay:
            out.append((hx, -ay + d))
            continue
        d -= 2 * ay
        if d < q:
            t = d / r
            out.append((ax + r * math.cos(t), ay + r * math.sin(t)))
            continue
        d -= q
        if d < 2 * ax:
            out.append((ax - d, hy))
            continue
        d -= 2 * ax
        if d < q:
            t = d / r
            out.append((-ax - r * math.sin(t), ay + r * math.cos(t)))
            continue
        d -= q
        if d < 2 * ay:
            out.append((-hx, ay - d))
            continue
        d -= 2 * ay
        t = d / r
        out.append((-ax - r * math.cos(t), -ay - r * math.sin(t)))
    return out


# --------------------------------------------------------------------------- #
# nose / chassis joint collar and its fastener ring
# --------------------------------------------------------------------------- #

COL_LOOP = [(1.98000, -0.00170), (1.97600, -0.00020), (1.97100, 0.00110),
            (1.96400, 0.00300), (1.95800, 0.00450), (1.95200, 0.00512),
            (1.94600, 0.00532), (1.94100, 0.00538), (1.93750, 0.00540),
            (1.93450, 0.00541), (1.93150, 0.00541), (1.92850, 0.00540),
            (1.92500, 0.00539), (1.92000, 0.00538), (1.91200, 0.00520),
            (1.90600, 0.00450), (1.90200, 0.00330), (1.90050, 0.00210),
            (1.90050, -0.00120), (1.93000, -0.00200), (1.96500, -0.00200),
            (1.98000, -0.00170)]


def _collar_bolts():
    _vs, ss = _arc_table(COL_BOLT_X)
    half = ss[0]
    n = max(20, int(round(2.0 * half / COL_BOLT_PITCH)))
    if n % 2:
        n += 1
    return [half - (i + 0.5) * (2.0 * half) / n for i in range(n)]


def _fan_cap(verts, faces, idx, outward):
    """Close a profile ring with a centroid fan, wound to face `outward`."""
    m = len(idx)
    c = [sum(verts[i][k] for i in idx) / m for k in range(3)]
    ci = len(verts)
    verts.append(tuple(c))
    nx = ny = nz = 0.0
    for k in range(m):
        p, q = verts[idx[k]], verts[idx[(k + 1) % m]]
        nx += (p[1] - q[1]) * (p[2] + q[2])
        ny += (p[2] - q[2]) * (p[0] + q[0])
        nz += (p[0] - q[0]) * (p[1] + q[1])
    flip = (nx * outward[0] + ny * outward[1] + nz * outward[2]) < 0.0
    for k in range(m):
        a, b = idx[k], idx[(k + 1) % m]
        faces.append((ci, b, a) if flip else (ci, a, b))


def _build_collar(coll):
    # D-na-19: drop any bolt whose spot-face would hang over a relief cut. The
    # head is 8.8 mm across, so a bolt sitting exactly on the cut would lose
    # half its seat and stand on air.
    bolts = [s for s in _collar_bolts()
             if all(_collar_keep(_v_at_arc(COL_BOLT_X, s + d))
                    for d in (-0.0062, 0.0, 0.0062))]
    vb = [_v_at_arc(COL_BOLT_X, s) for s in bolts]
    # D-na-02: base 150 next to 21-sample bolt clusters put a 9:1 jump in ring
    # density round the collar, and the shading banded visibly between the
    # bolts. 330 base samples brings the ratio to about 3:1 and it disappears.
    vs = _cluster(0.0, 2.0, 330, [(v, 0.0150, 19) for v in vb],
                  periodic=True, mind=2.0e-4)
    n = len(vs)
    spot = COL_SPOT_R + COL_SPOT_W

    # D-na-19: the band is relieved round each of the six forward suspension
    # pickups. COL_LOOP's last entry repeats its first, so the profile is the
    # 21 distinct entries closed cyclically - the old build bridged 22 rings and
    # left a degenerate strip for merge_doubles to eat, which is fine for a
    # closed band but leaves nothing to cap a cut end with.
    keep = [_collar_keep(v) for v in vs]
    loop = COL_LOOP[:-1]
    m = len(loop)

    verts, faces = [], []
    bases = []
    for (xr, o0) in loop:
        sta = _Sta(xr, vs)
        ring = []
        for j in range(n):
            y, z = sta.p[j]
            ny, nz = sta.n[j]
            o = OFF + o0 + _crown_delta(xr, sta.s[j])
            if o0 > 0.0050:
                for bs in bolts:
                    d = math.hypot(xr - COL_BOLT_X, sta.s[j] - bs)
                    if d < spot:
                        o -= COL_SPOT_D * _ss((spot - d) / COL_SPOT_W)
                        break
            ring.append((xr, y + ny * o, z + nz * o))
        base = len(verts)
        verts.extend(ring)
        bases.append(base)
    for k in range(m):
        a, b = bases[k], bases[(k + 1) % m]
        for j in range(n):
            j2 = (j + 1) % n
            if keep[j] and keep[j2]:
                faces.append((a + j, a + j2, b + j2, b + j))
    for j in range(n):
        j2 = (j + 1) % n
        if keep[j] == keep[j2]:
            continue
        live, dead = (j, j2) if keep[j] else (j2, j)
        p, q = verts[bases[0] + live], verts[bases[0] + dead]
        _fan_cap(verts, faces, [bases[k] + live for k in range(m)],
                 (p[0] - q[0], p[1] - q[1], p[2] - q[2]))

    # D-na-02/18: the shared CarbonFibre weave is a 2D pattern in OBJECT x/y
    # extruded along object z - it has no z dependence at all - so on a surface
    # that runs parallel to that extrusion the weave stretches and reads as
    # ribbing. The obvious geometry-side answer is to re-author the flanks in a
    # frame turned 90 deg about X so the pattern lies in world x/z, which is the
    # flank's own plane. I built that (split at the section's 45 deg diagonals,
    # flanks rotated) and rendered the identical crops: it made the collar WORSE
    # - a_weave/a_collar in na_shots show a coarser, more strongly shaded
    # vertical rib than the un-rotated b_weave/b_collar - because the overlaid
    # wave pair does not behave like the simple 2D product the anisotropy
    # argument assumes. Reverted, and left honest: on a closed ring section no
    # single object frame can win, and the material reads Object coordinates
    # only (no UV input anywhere in s03_materials.carbon_fibre), so geometry
    # cannot fix it either. See the round-2 report.
    ob = _obj(P + "Collar", verts, faces, coll, ("CarbonFibre",), smooth=34.0)
    made = [ob]

    V, F = [], []
    for (bs, bv) in zip(bolts, vb):
        p = _conform_pt(COL_BOLT_X, bs, 0.00541 - COL_SPOT_D)
        fr = _frame(p, _norm3(COL_BOLT_X, bv), (1.0, 0.0, 0.0))
        _emit(V, F, *_gen_screw(fr, r_head=0.0044, h_head=0.0026, r_sock=0.0021,
                                d_sock=0.0015, seg=30, sink=0.0018))
    made.append(_obj(P + "CollarBolts", V, F, coll, ("Titanium",), smooth=28.0))
    return made


# --------------------------------------------------------------------------- #
# front bulkhead access panel
# --------------------------------------------------------------------------- #

def _build_panel(coll):
    K = 61
    nb = 4 * (K - 1)
    loop = _rrect_loop(PAN_HX, PAN_HS, PAN_R, nb)
    grid, _rho = _disc_patch(loop, K)
    top_off = PAN_T - PAN_REC_D
    bot_off = -PAN_REC_D + 0.0002

    verts, faces = [], []
    top = [[0] * K for _ in range(K)]
    bot = [[0] * K for _ in range(K)]
    for i in range(K):
        for j in range(K):
            dx, ds = grid[i][j]
            top[i][j] = len(verts)
            verts.append(_conform_pt(PAN_XC + dx, ds, top_off))
            bot[i][j] = len(verts)
            verts.append(_conform_pt(PAN_XC + dx, ds, bot_off))
    faces += _patch_faces(top)
    faces += [f[::-1] for f in _patch_faces(bot)]
    sb = _square_border(K)
    for k in range(nb):
        i0, j0 = sb[k]
        i1, j1 = sb[(k + 1) % nb]
        faces.append((top[i0][j0], bot[i0][j0], bot[i1][j1], top[i1][j1]))
    ob = _obj(P + "Panel", verts, faces, coll, ("CarbonFibre",), smooth=36.0)
    C.add_bevel(ob, width=0.0007, segments=3, angle=34.0)
    made = [ob]

    seats = ((-0.1010, -0.0410), (-0.1010, 0.0410), (0.0, -0.0455),
             (0.0, 0.0455), (0.1010, -0.0410), (0.1010, 0.0410))
    RV, RF = [], []
    HV, HF = [], []
    for (dx, ds) in seats:
        x = PAN_XC + dx
        b = top_off
        prof = [(0.0000, b + 0.0004), (0.0062, b + 0.0004), (0.0066, b + 0.0012),
                (0.0082, b + 0.0016), (0.0094, b + 0.0014), (0.0098, b + 0.0006),
                (0.0100, b - 0.0016)]
        _emit(RV, RF, *_conform_ring(x, ds, prof, seg=44))
        _emit(HV, HF, *_dzus_head(x, ds, b + 0.0006))
    made.append(_obj(P + "PanelRings", RV, RF, coll, ("Titanium",), smooth=30.0))
    made.append(_obj(P + "PanelFasteners", HV, HF, coll, ("SteelFastener",),
                     smooth=32.0))
    return made


def _dzus_head(xc, sc, off, r=0.0060, K=25):
    """Slotted quarter-turn head as a disc patch - the slot is real geometry."""
    nb = 4 * (K - 1)
    loop = [(r * math.cos(TAU * i / nb), r * math.sin(TAU * i / nb))
            for i in range(nb)]
    grid, rho = _disc_patch(loop, K)
    V, F = [], []
    top = [[0] * K for _ in range(K)]
    for i in range(K):
        for j in range(K):
            dx, ds = grid[i][j]
            o = off + 0.0005 * (1.0 - rho[i][j] ** 2)
            if abs(ds) < 0.0013 and rho[i][j] < 0.90:
                o -= 0.0013 * _ss((0.0013 - abs(ds)) / 0.0005)
            top[i][j] = len(V)
            V.append(_conform_pt(xc + dx, sc + ds, o))
    F += _patch_faces(top)
    sb = _square_border(K)
    base = len(V)
    for k in range(nb):
        i0, j0 = sb[k]
        dx, ds = grid[i0][j0]
        V.append(_conform_pt(xc + dx, sc + ds, off - 0.0018))
    for k in range(nb):
        i0, j0 = sb[k]
        i1, j1 = sb[(k + 1) % nb]
        F.append((top[i0][j0], base + k, base + (k + 1) % nb, top[i1][j1]))
    return V, F


# --------------------------------------------------------------------------- #
# camera pods
# --------------------------------------------------------------------------- #

def _pod_ring(x, y0, z0, hw, hh, n=44, sq=CAM_SQ, grow=0.0):
    ring = []
    e = 2.0 / sq
    for i in range(n):
        t = TAU * i / n
        ct, st = math.cos(t), math.sin(t)
        ring.append((x,
                     y0 + (hw + grow) * math.copysign(abs(ct) ** e, ct),
                     z0 + (hh + grow) * math.copysign(abs(st) ** e, st)))
    return ring


def _pod_surf(x, y0, z0, hw, hh, t, sq=CAM_SQ):
    """Surface point and outward normal on the pod section at polar param t."""
    e = 2.0 / sq
    ct, st = math.cos(t), math.sin(t)
    y = hw * math.copysign(abs(ct) ** e, ct)
    z = hh * math.copysign(abs(st) ** e, st)
    d = 1e-3
    ct2, st2 = math.cos(t + d), math.sin(t + d)
    y2 = hw * math.copysign(abs(ct2) ** e, ct2)
    z2 = hh * math.copysign(abs(st2) ** e, st2)
    ty, tz = y2 - y, z2 - z
    L = math.hypot(ty, tz) or 1.0
    return (x, y0 + y, z0 + z), (0.0, tz / L, -ty / L)


def _build_camera(coll, side):
    tag = "L" if side > 0 else "R"
    made = []
    sroot = CAM_ROOT_S * side
    y0 = CAM_Y * side
    z0 = CAM_Z
    tip = Vector((2.7480, y0 - 0.0100 * side, z0 - 0.0090))

    # Mount: a swept fin fairing. D-na-03: this started life as a constant
    # section swept from the skin to the pod plus a separate elliptical pad, and
    # it read as a twisted ribbon glued to a sticker - the pad rim was a hard
    # ellipse lying on the paint and the blade was 6:1 in plan. A fin is the
    # honest shape: morph a long narrow footprint that CONFORMS to the skin into
    # the small section that plugs into the pod. Every intermediate ring is a
    # convex blend of two convex curves, so it cannot fold, the root runs out
    # into the surface by itself, and no separate pad is needed.
    rings = []
    nseg, m = 30, 56
    # D-na-09: an elliptical footprint (n=2.2) tapered the fore and aft runouts
    # to a razor edge lying on the paint. A rounded-rectangle footprint (n=3.2)
    # keeps real width right out to the ends, so the fairing runs out as a ramp
    # a machinist would recognise instead of a blade.
    e_root, e_tip = 2.0 / 3.2, 2.0 / 2.6
    A, B = 0.0540, 0.0150                     # footprint half length / half width
    ch1, th1 = 0.0210, 0.0092                 # section where it enters the pod
    foot, head = [], []
    for i in range(m):
        t = TAU * i / m
        ct, st = math.cos(t), math.sin(t)
        # -B*side: arc s grows AWAY from the crown, so "up" on the skin is -s on
        # the left and +s on the right. Getting this backwards twists the fin.
        foot.append(_conform_pt(
            CAM_ROOT_X + A * math.copysign(abs(ct) ** e_root, ct),
            sroot - B * side * math.copysign(abs(st) ** e_root, st), -0.0026))
        head.append((tip.x + ch1 * math.copysign(abs(ct) ** e_tip, ct), tip.y,
                     tip.z + th1 * math.copysign(abs(st) ** e_tip, st)))
    for k in range(nseg + 1):
        b = 1.0 - (1.0 - k / nseg) ** 1.7      # steep off the skin, soft into pod
        rings.append([(C.lerp(f[0], h[0], b), C.lerp(f[1], h[1], b),
                       C.lerp(f[2], h[2], b)) for f, h in zip(foot, head)])
    v, f = C.loft(rings, closed=True, cap_start=True, cap_end=True)
    made.append(_obj(P + "CamStalk_" + tag, v, f, coll, ("CarbonFibre",),
                     smooth=60.0))

    # pod body
    prof_x = ((CAM_POD_X1, 0.30), (CAM_POD_X1 - 0.0016, 0.62),
              (CAM_POD_X1 - 0.0042, 0.84), (CAM_POD_X1 - 0.0080, 0.96),
              (CAM_POD_X1 - 0.0150, 1.00), (2.7600, 1.00), (2.7300, 0.99),
              (CAM_POD_X0 + 0.0130, 0.97), (CAM_POD_X0 + 0.0055, 0.90),
              (CAM_POD_X0 + 0.0016, 0.72), (CAM_POD_X0, 0.40))
    rings = [_pod_ring(x, y0, z0, CAM_HW * s, CAM_HH * s) for (x, s) in prof_x]
    v, f = C.loft(rings, closed=True, cap_start=True, cap_end=True)
    ob = _obj(P + "CamPod_" + tag, v, f, coll, ("MatteBlack",), smooth=56.0)
    C.add_bevel(ob, width=0.0006, segments=2, angle=36.0)
    made.append(ob)

    # lens barrel, glass
    fr = _frame((CAM_POD_X1 - 0.0025, y0, z0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0))
    v, f = _gen_lathe(fr, [(0.0000, -0.0060), (0.0148, -0.0060),
                           (0.0150, 0.0022), (0.0146, 0.0044),
                           (0.0132, 0.0052), (0.0128, 0.0056),
                           (0.0104, 0.0056), (0.0100, 0.0038),
                           (0.0099, 0.0012), (0.0000, 0.0012)], seg=52)
    made.append(_obj(P + "CamBarrel_" + tag, v, f, coll, ("Titanium",),
                     smooth=28.0))
    fr2 = _frame((CAM_POD_X1 - 0.0025, y0, z0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0))
    v, f = _gen_lathe(fr2, [(0.0000, 0.0016), (0.0092, 0.0016),
                            (0.0096, 0.0024), (0.0092, 0.0032),
                            (0.0000, 0.0036)], seg=52)
    made.append(_obj(P + "CamGlass_" + tag, v, f, coll, ("DisplayGlass",),
                     smooth=24.0))

    # red index band - a flush inlay, not a rubber belt strapped round the pod
    band = []
    for (x, g) in ((2.7862, -0.0009), (2.7856, 0.0001), (2.7850, 0.0003),
                   (2.7770, 0.0003), (2.7764, 0.0001), (2.7758, -0.0009)):
        band.append(_pod_ring(x, y0, z0, CAM_HW, CAM_HH, grow=g))
    v, f = C.loft(band, closed=True, cap_start=True, cap_end=True)
    made.append(_obj(P + "CamBand_" + tag, v, f, coll, ("AnodisedRed",),
                     smooth=50.0))

    # body / end-cap parting line, so the pod is not one blank slab
    # The band's two end rings stand 0.2 mm proud so the parting line reads as a
    # pair of raised lips. Left open they were two exposed boundary loops - a
    # hairline crack right round the pod at 10x - so each end now runs back
    # inside the skin and is capped there.
    split = []
    for (x, g) in ((2.7352, -0.0010), (2.7350, 0.0002), (2.7344, -0.0007),
                   (2.7326, -0.0007), (2.7320, 0.0002), (2.7318, -0.0010)):
        split.append(_pod_ring(x, y0, z0, CAM_HW, CAM_HH, grow=g))
    v, f = C.loft(split, closed=True, cap_start=True, cap_end=True)
    made.append(_obj(P + "CamSplit_" + tag, v, f, coll, ("MatteBlack",),
                     smooth=26.0))

    # pod fasteners, on the surface, normal to it
    V, F = [], []
    for (bx, t) in ((2.7180, 0.62), (2.7180, -0.62), (2.8180, 0.62),
                    (2.8180, -0.62)):
        sc = 1.0
        for k in range(len(prof_x) - 1):
            if prof_x[k][0] >= bx >= prof_x[k + 1][0]:
                u = (prof_x[k][0] - bx) / (prof_x[k][0] - prof_x[k + 1][0])
                sc = C.lerp(prof_x[k][1], prof_x[k + 1][1], u)
                break
        ang = t if side > 0 else math.pi - t
        p, nn = _pod_surf(bx, y0, z0, CAM_HW * sc, CAM_HH * sc, ang)
        _emit(V, F, *_gen_screw(_frame(p, nn, (1.0, 0.0, 0.0)), r_head=0.0027,
                                h_head=0.0015, r_sock=0.0012, d_sock=0.0009,
                                seg=22, sink=0.0016))
    made.append(_obj(P + "CamScrews_" + tag, V, F, coll, ("SteelFastener",),
                     smooth=28.0))

    # D-na-04: this used to be a cable boot bridging the pod to the stalk head.
    # Once the mount became a fin the head sits INSIDE the pod, so the boot had
    # nowhere to land and rendered as a tube stub hanging in mid air under the
    # pod. A connector on the pod's aft face is attached by construction.
    fr4 = _frame((CAM_POD_X0 + 0.0040, y0, z0 - 0.0020), (-1.0, 0.0, 0.0),
                 (0.0, 0.0, 1.0))
    v, f = _gen_lathe(fr4, [(0.0000, -0.0080), (0.0092, -0.0080),
                            (0.0092, 0.0042), (0.0078, 0.0058),
                            (0.0078, 0.0128), (0.0058, 0.0146),
                            (0.0058, 0.0202), (0.0046, 0.0214),
                            (0.0000, 0.0214)], seg=28)
    made.append(_obj(P + "CamConn_" + tag, v, f, coll, ("MatteBlack",),
                     smooth=30.0))
    return made


# --------------------------------------------------------------------------- #
# pitot rake
# --------------------------------------------------------------------------- #

def _build_pitot(coll):
    made = []
    x0 = PIT_BASE_X
    prof = [(0.0000, -0.0010), (0.0130, -0.0010), (0.0190, 0.0010),
            (0.0225, 0.0016), (0.0243, 0.0009), (0.0252, -0.0018)]
    v, f = _conform_ring(x0, 0.0, prof, seg=64, rx=1.30, ry=0.78)
    made.append(_obj(P + "PitotBase", v, f, coll, ("CarbonFibre",), smooth=30.0))

    base = _conform_pt(x0, 0.0, 0.0014)
    top_z = base[2] + 0.0560
    rings = []
    n, m = 26, 64
    e = 2.0 / 2.7
    for k in range(n + 1):
        w = k / n
        z = base[2] - 0.0080 + (top_z - base[2] + 0.0080) * w
        xc = base[0] - 0.0040 * w * w
        fl = 1.0 + 0.55 * max(0.0, 1.0 - max(0.0, w - 0.05) / 0.30) ** 2
        # D-na-16: at 0.0170 the mast's top ring poked 0.4 mm out through the
        # bar's leading edge - a razor sliver right at the junction. The top of
        # the mast now sits 1.5 mm inside the bar's section all round.
        ch = C.lerp(0.0205, 0.0150, _ss(w)) * (1.0 + 0.28 * (fl - 1.0))
        th = C.lerp(0.0050, 0.0042, _ss(w)) * fl
        ring = []
        for i in range(m):
            t = TAU * i / m
            ct, st = math.cos(t), math.sin(t)
            ring.append((xc + ch * math.copysign(abs(ct) ** e, ct),
                         th * math.copysign(abs(st) ** e, st), z))
        rings.append(ring)
    v, f = C.loft(rings, closed=True, cap_start=True, cap_end=True)
    # D-na-11: even at 64 samples per section the mast still striped, so it was
    # never faceting - it is the shared weave, which has no Z dependence and so
    # degenerates into corduroy on anything tall and slim. Painted matte black
    # is both plausible for an instrumentation mast and free of the artefact.
    made.append(_obj(P + "PitotMast", v, f, coll, ("MatteBlack",), smooth=62.0))

    # D-na-05/17: the cross bar tapered to 70 % at the tips and the probes' root
    # bosses were 1.34 x the tube laid on TOP of it, so each root left a
    # razor-thin chisel sliver of its own aft cap lying proud of the bar's aft
    # face, and the outer bosses hung 1.6 mm below the bar and 0.9 mm past its
    # end cap. Every boss is now sized to fit strictly INSIDE the bar's local
    # section (root radius + |dz| + 1 mm <= half height) and starts 6 mm aft of
    # the bar's own centreline, so what you see is a fillet-flared boss emerging
    # from the bar's nose - no cap, no sliver, nothing hanging past anything.
    # The bar is 35 x 17.6 mm, spans +-55 mm and rolls into a domed end.
    bar = []
    e2 = 2.0 / 2.6
    bx = base[0] - 0.0048
    zbar = top_z - 0.0016
    BAR_A, BAR_B = 0.0175, 0.0088
    stations = [(-0.0552, 0.26), (-0.0544, 0.46), (-0.0530, 0.66),
                (-0.0510, 0.80), (-0.0480, 0.88), (-0.0400, 0.925),
                (-0.0290, 0.955), (-0.0150, 0.985), (0.0, 1.0)]
    stations += [(-y, s) for (y, s) in reversed(stations[:-1])]
    for (y, sc) in stations:
        ring = []
        for i in range(48):
            t = TAU * i / 48
            ct, st = math.cos(t), math.sin(t)
            ring.append((bx + BAR_A * sc * math.copysign(abs(ct) ** e2, ct),
                         y,
                         zbar + BAR_B * sc * math.copysign(abs(st) ** e2, st)))
        bar.append(ring)
    v, f = C.loft(bar, closed=True, cap_start=True, cap_end=True)
    made.append(_obj(P + "PitotBar", v, f, coll, ("MatteBlack",), smooth=62.0))

    V, F = [], []
    #        y        ro      ri      L       dz       rb (root boss)
    tubes = ((0.0000, 0.0050, 0.0031, 0.1460, 0.0014, 0.0056),
             (0.0290, 0.0040, 0.0025, 0.1200, 0.0005, 0.0050),
             (-0.0290, 0.0040, 0.0025, 0.1200, 0.0005, 0.0050),
             (0.0470, 0.0032, 0.0019, 0.0980, -0.0010, 0.0042),
             (-0.0470, 0.0032, 0.0019, 0.0980, -0.0010, 0.0042))
    for (y, ro, ri, L, dz, rb) in tubes:
        fr = _frame((bx, y, zbar + dz), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0))
        prof = [(0.0000, -0.0060), (rb, -0.0060), (rb, 0.0086),
                (rb * 0.86, 0.0122), (ro * 1.10, 0.0158), (ro, 0.0192),
                (ro, L - 0.0034), (ro * 0.92, L), (ri + 0.0005, L),
                (ri, L - 0.0019), (ri, L - 0.0195), (0.0000, L - 0.0205)]
        _emit(V, F, *_gen_lathe(fr, prof, seg=40))
    made.append(_obj(P + "PitotProbes", V, F, coll, ("Titanium",), smooth=26.0))

    V, F = [], []
    for (dx, ds) in ((-0.0148, 0.0136), (-0.0148, -0.0136),
                     (0.0172, 0.0112), (0.0172, -0.0112)):
        x = x0 + dx
        p = _conform_pt(x, ds, 0.0007)
        fr = _frame(p, _norm3(x, _v_at_arc(x, ds)), (1.0, 0.0, 0.0))
        _emit(V, F, *_gen_screw(fr, r_head=0.0030, h_head=0.0017, r_sock=0.0014,
                                d_sock=0.0010, seg=22, sink=0.0016))
    made.append(_obj(P + "PitotScrews", V, F, coll, ("SteelFastener",),
                     smooth=28.0))
    return made


# --------------------------------------------------------------------------- #
# underside pylon mounting bosses
# --------------------------------------------------------------------------- #

def _build_boss(coll, side):
    """Titanium mating plate bonded into the milled pylon seat.

    D-na-14 (was): the footprint was laid out in a constant arc-from-crown
    coordinate sampled once at x = 2.940. The section shrinks fast toward the
    tip, so the pad skewed 42 mm sideways along its own length - outboard edge
    10 mm past the belly chine at the aft end, inboard edge 7 mm off the car
    centreline at the front, the two sides converging in a V. Every point is now
    laid out in real y about PYL_Y, with the half width clamped inboard of the
    chine, so the plate is where the docstring always claimed it was.
    """
    tag = "L" if side > 0 else "R"
    hx = PAD_HX - 0.0085 - PAD_EDGE       # clear of the widest wall
    hs0 = PAD_HS - 0.0025 - PAD_EDGE      # normalising reference for the grid
    K = 41
    nb = 4 * (K - 1)
    grid, _rho = _disc_patch(_rrect_loop(hx, hs0, PAD_R - 0.0012, nb), K)
    sb = _square_border(K)
    ztop = POCKET_Z + 0.0030          # buried in the shell above the pocket floor

    verts, faces = [], []
    top = [[0] * K for _ in range(K)]
    bot = [[0] * K for _ in range(K)]
    for i in range(K):
        for j in range(K):
            dx, ds = grid[i][j]
            x = PAD_XC + dx
            hs = _pad_hs(x) - _pocket_w(x) - PAD_EDGE
            dy = ds * (hs / hs0)                       # taper with the chine
            zb = PYL_FACE_Z
            # machined relief: a blank 128 x 43 mm slab is exactly the "flat
            # untextured face" the brief calls a defect, and a real mating plate
            # is relieved anyway. Land round the rim, land round every insert,
            # 0.9 mm pocket between them - relief moves AWAY from the flange, so
            # the joint still closes on metal.
            a = _rrect(dx, dy, hx - 0.0090, max(0.0030, hs - 0.0075), 0.0055)
            for (bx, by) in PYL_BOLTS:
                a = max(a, 0.0100 - math.hypot(x - bx, dy - by))
            if a < 0.0:
                zb += 0.0009 * _ss(-a / 0.0022)
            y = (PYL_Y + dy) * side
            top[i][j] = len(verts)
            verts.append((x, y, ztop))
            bot[i][j] = len(verts)
            verts.append((x, y, zb))
    faces += [f[::-1] for f in _patch_faces(top)]
    faces += _patch_faces(bot)
    for k in range(nb):
        i0, j0 = sb[k]
        i1, j1 = sb[(k + 1) % nb]
        faces.append((top[i1][j1], bot[i1][j1], bot[i0][j0], top[i0][j0]))
    ob = _obj(P + "PylonBoss_" + tag, verts, faces, coll, ("Titanium",),
              smooth=32.0, merge=None)
    # Real holes for the inserts. Without them the plate is solid behind every
    # insert: the bore, the counterbore and the thread all end up drilled into a
    # face the plate itself then covers, which is exactly why the inserts used
    # to render as blank discs. It also gives front_wing's cap screws - which it
    # builds head-UP off the flange crown, reaching z = 0.2271 - somewhere to go.
    CV, CF = [], []
    for (bx, by) in PYL_BOLTS:
        fr = _frame((bx, (PYL_Y + by) * side, 0.0), (0.0, 0.0, 1.0),
                    (1.0, 0.0, 0.0))
        _emit(CV, CF, *_gen_lathe(fr, [(0.0076, 0.2180), (0.0076, 0.2420)],
                                  seg=48))
    _cut_holes(ob, CV, CF, coll, P + "_cut_" + tag)
    C.shade_auto_smooth(ob, 32.0)
    C.add_bevel(ob, width=0.0006, segments=2, angle=30.0)
    made = [ob]

    V, F = [], []
    for (bx, by) in PYL_BOLTS:
        fr = _frame((bx, (PYL_Y + by) * side, PYL_FACE_Z), (0.0, 0.0, 1.0),
                    (1.0, 0.0, 0.0))
        _emit(V, F, *_gen_insert(fr))
    made.append(_obj(P + "PylonInserts_" + tag, V, F, coll, ("SteelFastener",),
                     smooth=28.0))
    return made


# --------------------------------------------------------------------------- #
# flush static ports
# --------------------------------------------------------------------------- #

def _build_ports(coll, side):
    tag = "L" if side > 0 else "R"
    # D-na-07: these were 24 mm discs with a 2.3 mm thick rim and 44 segments -
    # at 10x they read as chrome plumbing washers with a visibly polygonal brim.
    # A real static port is ~18 mm, sits half a millimetre proud, and has a
    # 4 mm hole.
    prof = [(0.0000, -0.0026), (0.0019, -0.0026), (0.0021, -0.0002),
            (0.0028, 0.0004), (0.0076, 0.0005), (0.0086, 0.0002),
            (0.0090, -0.0016)]
    V, F = [], []
    for (x, v) in ((2.5200, 0.700), (2.3050, 0.632)):
        s = _arc_at_v(x, v if side > 0 else 2.0 - v)
        _emit(V, F, *_conform_ring(x, s, prof, seg=64))
    return [_obj(P + "StaticPorts_" + tag, V, F, coll, ("Titanium",),
                 smooth=30.0)]


# --------------------------------------------------------------------------- #

def _selfcheck():
    """Max distance between this module's surface and spec.body_surface_point."""
    worst = 0.0
    for x in (1.95, 2.20, 2.55, 2.80, 2.97):
        for i in range(65):
            worst = max(worst, math.dist(S.body_surface_point(x, i / 64.0),
                                         _sect(x, i / 64.0)))
    return worst


def build(coll, ctx=None):
    _prepare()
    made = []
    made += _build_shell(coll)
    made += _build_collar(coll)
    made += _build_panel(coll)
    made += _build_pitot(coll)
    for side in (1, -1):
        made += _build_camera(coll, side)
        made += _build_boss(coll, side)
        made += _build_ports(coll, side)
    return made
