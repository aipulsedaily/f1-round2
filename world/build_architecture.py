"""
build_architecture.py  —  CIRCUIT VITRINE, the built environment.

Owns:  pit building + garage row, start/finish gantry, pit wall + wall stands,
       grandstand blocks and their terraces, the paddock (concrete, buildings,
       service ground, transporter park), the pit-exit apron platform,
       La Passerelle footbridge and Le Pont de la Plongee.

DOES NOT OWN (world_contract v1.0.0):
  * the Beat-4 walled corridor and the pit-exit portal  -> build_barriers.
    ARCH_ApronCorridor is named in C.CORRIDOR_DELETE_NAMES and is GONE.
  * the transit / access ribbon driving surface and its markings
    -> build_surface.  Every paved bay here is cut to C.access_ribbon_polygon().
  * anything inside C.road_corridor_mask() except the pit-exit apron platform,
    which C.platform_owner() assigns to this module.

THE GROUND DATUM IS NOT OURS EITHER.  Nothing in this file computes a ground
height.  Every foot, plinth, post and slab is placed with

    z, owner = C.world_ground_z(x, y)          # world frame, metres

and embedded by C.BASE_EMBED_M.  The declared z = 0.000 platform (paddock, pit
lane, garage floors, pit-exit apron, showroom forecourt) is C.APRON_Z, and the
step between it and the graded road corridor is built as a real retaining edge
(ARCH_RetainEdge) rather than hidden or averaged.

Everything is authored in the CIRCUIT frame C (pit straight on y=0 running +x,
S/F line at the origin) and placed into the WORLD frame W by one matrix:

    W = Rz(+40 deg) * ( C - (-350, +72) ) + (15, 0)

...except the showroom forecourt, which is authored in WORLD metres because it
belongs to the round-1 pavilion (identity transform, floor centre at the world
origin) and is deliberately laid to the building's grid, not the circuit's.

Run headless:
    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup -P build_architecture.py
    ... -P build_architecture.py -- --render all      (test renders)
    ... -P build_architecture.py -- --verify          (gates only, no render)

build() is idempotent: it deletes the ARCH collection tree and its datablocks
before rebuilding.

NOTHING is instanced without a variation system.  See build_architecture.md.
"""

import bpy, bmesh, math, os, sys, json, random, colorsys
from mathutils import Vector, Matrix, Euler

import numpy as np

# --------------------------------------------------------------------------- #
#  THE CONTRACT  —  world_contract.py is authoritative over this file          #
# --------------------------------------------------------------------------- #
_WORLD_DIR = os.path.dirname(os.path.abspath(__file__))
if _WORLD_DIR not in sys.path:
    sys.path.insert(0, _WORLD_DIR)
import world_contract as WC                       # noqa: E402

CONTRACT_MIN = "1.0.0"
if WC.__version__ < CONTRACT_MIN:
    raise RuntimeError("world_contract %s < %s" % (WC.__version__, CONTRACT_MIN))

APRON_Z = WC.APRON_Z                  # 0.000  — the declared platform plane
EMBED = WC.BASE_EMBED_M               # 0.020  — minimum embedment into the datum
RIBBON_SAW_M = WC.ACCESS_RIBBON_SAW_M  # 0.30 — C.access_ribbon_polygon()'s default
                                      # LATERAL margin, the sawn edge strip
                                      # build_surface lays outside the declared
                                      # ribbon edge.  RULE 1, world_contract 1.2.0:
                                      # this was a private literal that happened to
                                      # match, which is DEFECT 4 exactly.  Same
                                      # value, so no bay moves.
TOL_SEAM = WC.TOL_SEAM_M              # 0.010
TOL_COPLANAR = WC.TOL_COPLANAR_M      # 0.030

# --------------------------------------------------------------------------- #
#  THE THREE MARGINS AT THE GLASS PLANE   (assembly defect #2)                  #
# --------------------------------------------------------------------------- #
# Three modules used three different numbers for the SAME boundary and the world
# came apart in the metre the car breaches the glass:
#
#   C.road_corridor_mask   ACCESS_CORRIDOR_MARGIN_M = 3.00 -> terrain cuts to x=12.00
#   this module            RIBBON_SAW_M             = 0.30 -> paving cuts to x=14.70
#   C.access_ribbon_polygon(0.30)                          -> the polygon's END CAPS
#                                                             carry NO margin, so it
#                                                             still starts at x=15.000
#
# and 1 276 of 7 467 sampled points over x 4..17, y +-14 had no usable ground:
# ~64 m2, of which x 14.700..15.000 was FULLY OPEN, 0.300 m x 12.75 m, showing this
# module's forecourt sub-base as an open coffered eggcrate with no top faces.
#
# THE RECONCILIATION, and which module does what:
#
#   * THE MARGIN IS LATERAL AND ONLY LATERAL.  world_contract 1.0.1 settled it:
#     `ACCESS_RIBBON_T_MIN` = 0.0 pins the ribbon's START CAP on the breach plane,
#     world x = 15.000, whatever margin a caller passes, "and the paving butts the
#     ribbon at the threshold".  Its docstring names this module explicitly — "a
#     module that keeps its own `-saw - t` term reopens the slot on its own side;
#     the contract cannot reach into it" — so the term is gone.  `RIBBON_T_MIN` is
#     read FROM the contract with the old behaviour as the fallback, so the number
#     is settled in one file for all three modules.
#
#   * TERRAIN'S 3.00 m IS NOT THE SAME KIND OF NUMBER.  It is how far terrain keeps
#     OFF the ribbon, not where any surface starts.  Between x 12.00 and x 15.00 the
#     contract's `world_ground_z` gives the ground to `build_architecture:paving`
#     (the declared showroom forecourt), and this module now builds every square
#     metre of it, closed, right up to x = 15.000: bays at z = 0.000 outside the
#     round-1 pavilion, and a closed formation slab at z = -0.100 under it (R1_*
#     below).  Nothing in the forecourt is an open box any more.
RIBBON_T_MIN = float(getattr(WC, "ACCESS_RIBBON_T_MIN", -RIBBON_SAW_M))

# --------------------------------------------------------------------------- #
#  THE TRACK / APRON JOINT   (assembly defect #3)                               #
# --------------------------------------------------------------------------- #
# SURF_Track's outer edge is C.verge_edge(s) exactly.  This module's apron bay grid
# ALSO started at C.verge_edge and then inset every bay 12 mm, so both meshes stopped
# at the same coordinate and the 12 mm between them fell 0.300 m to the sub-base: at a
# 12.47 deg sun, a black line down 220 m of the pit straight.  TWO SURFACES CANNOT BOTH
# STOP AT A SHARED COORDINATE AND HOPE.  build_surface laps — `SURF_ApronJoint` carries
# the asphalt edge outboard of verge_edge as a real recessed sealant joint, 50 mm wide,
# 5 mm deep, with a 1.6 mm lap at its outer end — and this module's slab now BEGINS on
# the outer end of that lap, so the joint is a lit, sealed groove owned by one module
# and there is no coordinate two meshes both stop at.  Same `getattr` expression as
# build_surface, so the two track each other.
APRON_JOINT_LAP_M = float(getattr(WC, "APRON_JOINT_LAP_M", 0.050))
APRON_JOINT_DEPTH_M = float(getattr(WC, "APRON_JOINT_DEPTH_M", 0.005))

# --------------------------------------------------------------------------- #
#  THE ROUND-1 PAVILION  —  MEASURED, not assumed                               #
# --------------------------------------------------------------------------- #
# /home/zany/opus5-car-render/f1_showroom.blend, world frame, identity transform:
#
#   Floor            x -15.000..15.000  y -11.000..11.000  z -0.060..0.000
#   Wall_BackX       x -15.250..-15.000 y -11.250..11.250  z  0.000..6.200
#   Wall_SideY       x -15.250..15.250  y  11.000..11.250  z  0.000..6.200
#   GW_Right_Glass   x  15.000 (plane)  y -10.962..10.962  z  0.110..6.090
#   GW_Front_Glass   y -11.000 (plane)  x -14.962..14.962  z  0.110..6.090
#
# so the finished floor inside the pavilion is round 1's and its TOP IS z = 0.000
# EXACTLY — the same plane as C.APRON_Z.  Laying forecourt bays there would be a
# 30 x 22 m coplanar z-fight in the frame the camera breaches the glass, which is
# why the bays are cut to the shell.  What was wrong was (a) the cut rectangle was
# invented (-19.15..15.05, +-13.15) and 4.15 m too big to the west and 2.15 m too big
# in y, leaving a genuinely unpaved ring OUTSIDE the building, and (b) inside it the
# sub-base was an open-topped box.  Both are fixed: the cut is now the measured shell,
# and under it a CLOSED formation slab is cast at R1_FORMATION_Z — 40 mm clear of the
# round-1 floor's soffit, 100 mm clear of its finished level, so it can never fight
# either, and the world build has continuous ground at the corridor mouth.
R1_SHELL = (-15.250, 15.000, -11.250, 11.250)     # plan of the pavilion shell
R1_WALL_RETURN = 0.250                            # Wall_SideY reaches x = +15.250,
                                                  # a 0.25 x 0.25 m return past the
                                                  # glass at each end of the +y
                                                  # wall.  NOT cut out: excluding
                                                  # it would open two 0.27 x 0.25 m
                                                  # holes at the mouth to avoid
                                                  # 0.13 m2 of wall-base contact,
                                                  # and a wall standing on a slab
                                                  # is what a wall does.
R1_FLOOR_TOP_Z = 0.000
R1_FLOOR_SOFFIT_Z = -0.060
R1_FORMATION_Z = -0.100                           # this module's slab under it
R1_JOINT_M = 0.012                                # construction joint at the shell

# --------------------------------------------------------------------------- #
#  FRAMES                                                                      #
# --------------------------------------------------------------------------- #
ROT_DEG   = WC.ROT_DEG                            # 40.0, RULE 1 (1.2.0)
PIVOT_C   = WC.PIVOT_DESIGN                       # (-350.0, 72.0)
PIVOT_W   = WC.PIVOT_WORLD                        # (15.0, 0.0)
_CR, _SR  = math.cos(math.radians(ROT_DEG)), math.sin(math.radians(ROT_DEG))

M_C2W = (Matrix.Translation((PIVOT_W[0], PIVOT_W[1], 0.0))
         @ Matrix.Rotation(math.radians(ROT_DEG), 4, 'Z')
         @ Matrix.Translation((-PIVOT_C[0], -PIVOT_C[1], 0.0)))
M_W2C = M_C2W.inverted()


def c2w(x, y, z=0.0):
    dx, dy = x - PIVOT_C[0], y - PIVOT_C[1]
    return (PIVOT_W[0] + dx * _CR - dy * _SR, dx * _SR + dy * _CR, z)


def w2c(x, y, z=0.0):
    dx, dy = x - PIVOT_W[0], y - PIVOT_W[1]
    return (PIVOT_C[0] + dx * _CR + dy * _SR, PIVOT_C[1] - dx * _SR + dy * _CR, z)


COLL_ROOT = "ARCH"
SUBCOLLS = ("ARCH_Paving", "ARCH_PitBuilding", "ARCH_Gantry", "ARCH_PitWall",
            "ARCH_Grandstands", "ARCH_Paddock", "ARCH_Ground", "ARCH_Bridges")


# --------------------------------------------------------------------------- #
#  GROUND  —  every height in this file comes from the contract, via here      #
# --------------------------------------------------------------------------- #
# The declared platform rectangles are the CONTRACT's, not the spec's, because
# the spec's rectangles overlap the circuit (see WORLD_CONTRACT.md S7).
PLAT_RECTS = dict(WC.APRON_REGIONS_CIRCUIT)   # pit_lane / garages / paddock / apron
FORECOURT = dict(WC.FORECOURT_WORLD)          # world metres, half sizes


def wgz(x, y):
    """C.world_ground_z on arrays.  -> (z, owner).  World frame."""
    return WC.world_ground_z(np.asarray(x, float), np.asarray(y, float))


def sit_w(x, y, default=APRON_Z):
    """Scalar world-frame ground height for standing one object on."""
    z, _ = WC.world_ground_z(float(x), float(y))
    return default if (z != z) else float(z)     # NaN -> terrain -> declared plane


def sit_c(cx, cy, default=APRON_Z):
    """Scalar ground height at a CIRCUIT-frame point."""
    wx, wy = c2w(cx, cy)[:2]
    return sit_w(wx, wy, default)


def _ribbon_edges(t):
    """Ribbon inboard/outboard laterals at route stations t (contract's own
    precomputed table, the one C.in_access_ribbon interpolates)."""
    return (np.interp(t, WC._RT, WC._RVIN), np.interp(t, WC._RT, WC._RVOUT))


def clear_c(cx, cy, ribbon_m=RIBBON_SAW_M, t_min=None):
    """Signed clearance, metres, for CIRCUIT-frame points (arrays).

    > 0  build_architecture may lay its z = 0.000 platform here.
    <= 0 the road programme owns it: inside C.platform_edge on either side of
         the lap, or inside the access ribbon plus its sawn edge strip.

    This is the ONE predicate the paving is cut against, and it is built from
    contract primitives only — no re-derivation of a width, an offset or an
    edge.  Verified against C.world_ground_z in verify_contract().

    `ribbon_m` is the LATERAL margin — the sawn edge strip — and it is the ONLY
    margin.  `t_min` is the ribbon's start cap, `C.ACCESS_RIBBON_T_MIN` = 0.0, the
    breach plane at world x = 15.000: the paving is cut ON it, not 0.30 m behind
    it, because behind it is the showroom floor and nothing else builds there.
    Keeping a `-ribbon_m - t` term here is what left the 0.300 m x 12.75 m open
    slot the assembly review measured at the Beat-3 -> Beat-4 hinge.
    """
    cx = np.atleast_1d(np.asarray(cx, float))
    cy = np.atleast_1d(np.asarray(cy, float))
    t_min = RIBBON_T_MIN if t_min is None else float(t_min)
    wx, wy = WC.circuit_to_world(cx, cy)
    s, u = WC.project(wx, wy)
    lim = np.where(u >= 0.0, WC.platform_edge(s, +1), WC.platform_edge(s, -1))
    d_lap = np.abs(u) - lim
    t, v = WC.access_project(wx, wy)
    lo, hi = _ribbon_edges(t)
    d_rib = np.maximum.reduce([lo - ribbon_m - v, v - (hi + ribbon_m),
                               t_min - t,
                               t - (WC.ACCESS_TOTAL + ribbon_m)])
    return np.minimum(d_lap, d_rib)


def _r1_shell_clearance(x, y):
    """Signed distance OUTSIDE the round-1 pavilion shell, WORLD frame, metres.

    > 0  outside the building: this module lays finished paving at z = 0.000.
    <= 0 inside it: round 1's `Floor` is the finished surface (top z = 0.000
         exactly), so this module lays only the closed formation slab at
         R1_FORMATION_Z and never a bay.

    THREE SIDES CARRY THE 12 mm CONSTRUCTION JOINT AND THE FOURTH DOES NOT.  The
    +x face IS the breach plane, `C.ACCESS_GLASS_X` = 15.000, and the contract
    pins every consumer's cut to it (`ACCESS_RIBBON_T_MIN`).  Growing the shell
    12 mm eastward there put the paving's east edge at 15.012 and left a 12-18 mm
    slot open to the terrain at world x 15.000..15.018 for 6.3 < |y| < 11.25 —
    measured by a 5 mm ray profile, i.e. the SAME defect on a smaller scale, in
    the same metre.  So the glass plane is a butt joint with no allowance at all.
    """
    x = np.atleast_1d(np.asarray(x, float))
    y = np.atleast_1d(np.asarray(y, float))
    x0, x1, y0, y1 = R1_SHELL
    j = R1_JOINT_M
    return np.maximum.reduce([x0 - j - x, x - x1, y0 - j - y, y - (y1 + j)])


def in_rect(cx, cy, rect, inset=0.0):
    x0, x1, y0, y1 = rect
    return ((cx >= x0 + inset) & (cx <= x1 - inset) &
            (cy >= y0 + inset) & (cy <= y1 - inset))


# --------------------------------------------------------------------------- #
#  CURVED-BOUNDARY POLYGON CUT                                                 #
# --------------------------------------------------------------------------- #
# The road corridor edge is a 3675 m curve and the access ribbon is an R150 arc.
# A paving bay that straddles either has to be SAWN to the curve — the contract's
# rule for finding #2 is "cut, do not offset", and a chord across a whole 5 m bay
# would be a 21 mm lie against a 10 mm seam tolerance.  So a straddling bay is
# recursively quartered until the leaf is <= LEAF_M across, and only then clipped
# by the linear crossing.  At R = 150 m the sagitta of a 0.75 m chord is 0.47 mm.
#
# Everything is evaluated BREADTH FIRST so each recursion level is one vectorised
# clearance call: C.world_ground_z is 39 us a point and there are ~10^5 of them.
LEAF_M = 0.75
MAX_SPLIT = 4


def cut_bays(bays, clearance, leaf=LEAF_M, max_split=MAX_SPLIT):
    """bays: [(x0, x1, y0, y1, payload), ...] axis-aligned in the circuit frame.

    Returns [(polygon, payload, whole), ...] keeping only the part where
    `clearance(cx, cy) > 0`.  `whole` is True if the bay was untouched.
    """
    out = []
    level = [(b, 0) for b in bays]
    while level:
        P = []
        for (x0, x1, y0, y1, _pl), _d in level:
            P += [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        if not P:
            break
        A = np.array(P)
        f = clearance(A[:, 0], A[:, 1])
        nxt = []
        for i, ((x0, x1, y0, y1, pl), d) in enumerate(level):
            v = f[4 * i:4 * i + 4]
            span = max(x1 - x0, y1 - y0)
            can_split = span > leaf and d < max_split
            if v.min() > 0.0:
                out.append(([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], pl, d == 0))
                continue
            if v.max() <= 0.0:
                # A CELL CAN HIDE A POSITIVE RIDGE BETWEEN FOUR NEGATIVE CORNERS,
                # and dropping it on the corner test alone is how a 3.0 m apron bay
                # with a 0.75 m feasible strip through its middle vanished, leaving
                # three 293 mm holes in the pit-exit apron at world (109.6..110.2,
                # +-0.2).  `clearance` is a signed distance in the same units as the
                # cell, so a cell whose BEST corner is further outside than the cell
                # is wide cannot contain an inside point; anything shallower than
                # that gets split and looked at properly.
                if not can_split or v.max() <= -span:
                    continue
                mx, my = 0.5 * (x0 + x1), 0.5 * (y0 + y1)
                nxt += [((x0, mx, y0, my, pl), d + 1), ((mx, x1, y0, my, pl), d + 1),
                        ((mx, x1, my, y1, pl), d + 1), ((x0, mx, my, y1, pl), d + 1)]
                continue
            if can_split:
                mx, my = 0.5 * (x0 + x1), 0.5 * (y0 + y1)
                nxt += [((x0, mx, y0, my, pl), d + 1), ((mx, x1, y0, my, pl), d + 1),
                        ((mx, x1, my, y1, pl), d + 1), ((x0, mx, my, y1, pl), d + 1)]
                continue
            poly = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
            keep = []
            for k in range(4):
                p, q = poly[k], poly[(k + 1) % 4]
                fp, fq = v[k], v[(k + 1) % 4]
                if fp > 0.0:
                    keep.append(p)
                if (fp > 0.0) != (fq > 0.0):
                    tt = fp / (fp - fq)
                    keep.append((p[0] + tt * (q[0] - p[0]),
                                 p[1] + tt * (q[1] - p[1])))
            if len(keep) >= 3:
                out.append((keep, pl, False))
        level = nxt
    return out


# --------------------------------------------------------------------------- #
#  RETAINING EDGE  —  the step between the graded corridor and the z=0 platform #
# --------------------------------------------------------------------------- #
# C.ground_z at the corridor rim is up to 0.51 m below C.APRON_Z (measured, see
# verify_contract).  The old build laid its slabs at 0.000 and simply stopped, so
# the paddock hung over the runoff.  A real paddock is RETAINED off the graded
# ground by a cast edge beam with a slot drain at its foot, and that is what this
# builds — welded to C.corridor_rim's own z so the two meshes share a line.
RETAIN_MIN_DROP = 0.010          # below this the edge degenerates to a flush kerb
RETAIN_TOE = 0.45                # how far the toe of the beam reaches outboard
TERRAIN_SKIRT = 0.90             # closed skirt where the platform abuts terrain,
                                 # whose height this module is not allowed to know

# --------------------------------------------------------------------------- #
#  SMALL MATHS / COLOUR HELPERS                                                #
# --------------------------------------------------------------------------- #


def srgb(hexstr):
    """'#rrggbb' -> linear rgba tuple (Blender vertex colours are linear)."""
    h = hexstr.lstrip('#')
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255.0
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (out[0], out[1], out[2], 1.0)


def jitter_col(rgba, rng, amt=0.05, val=0.06):
    """Per-instance hue/value wobble so no two painted things match exactly."""
    h, l, s = colorsys.rgb_to_hls(*rgba[:3])
    h = (h + rng.uniform(-amt, amt)) % 1.0
    l = max(0.0, min(1.0, l * (1.0 + rng.uniform(-val, val))))
    s = max(0.0, min(1.0, s * (1.0 + rng.uniform(-val, val))))
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return (r, g, b, 1.0)


def lerp(a, b, t):
    return a + (b - a) * t


def T(x, y, z=0.0):
    return Matrix.Translation((x, y, z))


def Rz(deg):
    return Matrix.Rotation(math.radians(deg), 4, 'Z')


def Ry(deg):
    return Matrix.Rotation(math.radians(deg), 4, 'Y')


def Rx(deg):
    return Matrix.Rotation(math.radians(deg), 4, 'X')


def S(x, y=None, z=None):
    y = x if y is None else y
    z = x if z is None else z
    m = Matrix.Identity(4)
    m[0][0], m[1][1], m[2][2] = x, y, z
    return m


# --------------------------------------------------------------------------- #
#  MESH BUILDER  (list based -> from_pydata; fast enough for ~2 M faces)        #
# --------------------------------------------------------------------------- #
class MB:
    __slots__ = ("name", "v", "f", "fm", "fc", "fs", "mats", "midx")

    def __init__(self, name):
        self.name = name
        self.v = []          # vertices
        self.f = []          # faces (index tuples)
        self.fm = []         # material index per face
        self.fc = []         # rgba per face (written to a CORNER colour attr)
        self.fs = []         # smooth flag per face
        self.mats = []
        self.midx = {}

    # -- material slots -----------------------------------------------------
    def m(self, name):
        i = self.midx.get(name)
        if i is None:
            i = len(self.mats)
            self.midx[name] = i
            self.mats.append(name)
        return i

    # -- raw ----------------------------------------------------------------
    def add(self, verts, faces, mat, col=(1, 1, 1, 1), smooth=False):
        base = len(self.v)
        mi = self.m(mat)
        self.v.extend(verts)
        for fa in faces:
            self.f.append(tuple(base + i for i in fa))
            self.fm.append(mi)
            self.fc.append(col)
            self.fs.append(smooth)

    def ngon(self, pts, mat, col=(1, 1, 1, 1), smooth=False):
        self.add(pts, [tuple(range(len(pts)))], mat, col, smooth)

    def quad(self, a, b, c, d, mat, col=(1, 1, 1, 1), smooth=False):
        self.add([a, b, c, d], [(0, 1, 2, 3)], mat, col, smooth)

    # -- box, axis aligned in the builder's own frame ------------------------
    def box(self, p0, p1, mat, col=(1, 1, 1, 1), skip=""):
        x0, y0, z0 = p0
        x1, y1, z1 = p1
        x0, x1 = min(x0, x1), max(x0, x1)
        y0, y1 = min(y0, y1), max(y0, y1)
        z0, z1 = min(z0, z1), max(z0, z1)
        V = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
             (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        F = {'zn': (0, 3, 2, 1), 'zp': (4, 5, 6, 7), 'yn': (0, 1, 5, 4),
             'yp': (3, 7, 6, 2), 'xn': (0, 4, 7, 3), 'xp': (1, 2, 6, 5)}
        faces = [f for k, f in F.items() if k not in skip]
        self.add(V, faces, mat, col)

    # -- box through an arbitrary matrix (centre at the matrix origin) -------
    def xbox(self, mat4, size, mat, col=(1, 1, 1, 1), skip=""):
        sx, sy, sz = (s * 0.5 for s in size)
        V = [Vector(p) for p in
             [(-sx, -sy, -sz), (sx, -sy, -sz), (sx, sy, -sz), (-sx, sy, -sz),
              (-sx, -sy, sz), (sx, -sy, sz), (sx, sy, sz), (-sx, sy, sz)]]
        V = [tuple(mat4 @ p) for p in V]
        F = {'zn': (0, 3, 2, 1), 'zp': (4, 5, 6, 7), 'yn': (0, 1, 5, 4),
             'yp': (3, 7, 6, 2), 'xn': (0, 4, 7, 3), 'xp': (1, 2, 6, 5)}
        self.add(V, [f for k, f in F.items() if k not in skip], mat, col)

    # -- vertical prism from a 2D outline ------------------------------------
    def prism(self, pts2, z0, z1, mat, col=(1, 1, 1, 1), top=True, bot=True,
              sides=True):
        n = len(pts2)
        V = [(p[0], p[1], z0) for p in pts2] + [(p[0], p[1], z1) for p in pts2]
        F = []
        if sides:
            for i in range(n):
                j = (i + 1) % n
                F.append((i, j, n + j, n + i))
        if bot:
            F.append(tuple(range(n - 1, -1, -1)))
        if top:
            F.append(tuple(range(n, 2 * n)))
        self.add(V, F, mat, col)

    # -- cylinder / tube between two points ----------------------------------
    def cyl(self, p0, p1, r, mat, col=(1, 1, 1, 1), n=12, caps=True, r1=None,
            smooth=True, twist=0.0):
        p0, p1 = Vector(p0), Vector(p1)
        r1 = r if r1 is None else r1
        d = p1 - p0
        L = d.length
        if L < 1e-9:
            return
        z = d / L
        up = Vector((0, 0, 1)) if abs(z.z) < 0.95 else Vector((1, 0, 0))
        x = z.cross(up).normalized()
        y = z.cross(x).normalized()
        ring0, ring1 = [], []
        for i in range(n):
            a = twist + 2 * math.pi * i / n
            ca, sa = math.cos(a), math.sin(a)
            ring0.append(tuple(p0 + x * (ca * r) + y * (sa * r)))
            ring1.append(tuple(p1 + x * (ca * r1) + y * (sa * r1)))
        V = ring0 + ring1
        F = [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
        self.add(V, F, mat, col, smooth=smooth)
        if caps:
            self.add(ring0, [tuple(range(n - 1, -1, -1))], mat, col)
            self.add(ring1, [tuple(range(n))], mat, col)

    # -- I / box section beam between two points ------------------------------
    def beam(self, p0, p1, w, h, mat, col=(1, 1, 1, 1)):
        p0, p1 = Vector(p0), Vector(p1)
        d = p1 - p0
        L = d.length
        if L < 1e-9:
            return
        z = d / L
        up = Vector((0, 0, 1)) if abs(z.z) < 0.95 else Vector((1, 0, 0))
        x = z.cross(up).normalized()
        y = x.cross(z).normalized()
        ring = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
        V = [tuple(p0 + x * a + y * b) for a, b in ring] + \
            [tuple(p1 + x * a + y * b) for a, b in ring]
        F = [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7),
             (3, 2, 1, 0), (4, 5, 6, 7)]
        self.add(V, F, mat, col)

    # -- surface of revolution (tyres, drums, dishes) -------------------------
    def revolve(self, prof, mat4, mat, col=(1, 1, 1, 1), n=20, smooth=True,
                tread=0.0):
        """prof = [(r, z), ...] in the local frame, revolved about local Z.
        `tread` alternates the radius per segment so a tyre reads as a tyre."""
        rings = []
        for i, (r, z) in enumerate(prof):
            ring = []
            for k in range(n):
                a = 2 * math.pi * k / n
                rr = r + (tread if (k % 2 and r > 0.05) else 0.0)
                ring.append(tuple(mat4 @ Vector((rr * math.cos(a),
                                                 rr * math.sin(a), z))))
            rings.append(ring)
        V = []
        F = []
        for i in range(len(prof)):
            V.extend(rings[i])
        for i in range(len(prof) - 1):
            for k in range(n):
                a0 = i * n + k
                a1 = i * n + (k + 1) % n
                b0 = (i + 1) * n + k
                b1 = (i + 1) * n + (k + 1) % n
                F.append((a0, a1, b1, b0))
        self.add(V, F, mat, col, smooth=smooth)

    def tyre(self, mat4, r_out=0.42, r_in=0.185, w=0.23, mat="A_Rubber",
             col=(1, 1, 1, 1), rim=None, n=20):
        h = w * 0.5
        prof = [(r_in, -h), (r_out - 0.07, -h), (r_out, -h + 0.06),
                (r_out, h - 0.06), (r_out - 0.07, h), (r_in, h)]
        self.revolve(prof, mat4, mat, col, n=n, tread=0.012)
        self.revolve([(r_in, -h), (r_in, h)], mat4, mat, col, n=n)
        if rim:
            self.revolve([(0.02, 0.0), (r_in + 0.01, -0.02),
                          (r_in + 0.01, 0.02), (0.02, 0.0)], mat4, rim[0],
                         rim[1], n=n)

    # -- text baked to geometry (Blender's bundled Bfont; nothing downloaded) -
    def text(self, body, mat4, size, mat, col=(1, 1, 1, 1), extrude=0.012,
             align='CENTER', spacing=1.0):
        cu = bpy.data.curves.new("_tmptxt", 'FONT')
        cu.body = body
        cu.size = size
        cu.extrude = extrude
        cu.align_x = align
        cu.align_y = 'CENTER'
        cu.space_character = spacing
        cu.resolution_u = 3
        ob = bpy.data.objects.new("_tmptxt", cu)
        bpy.context.scene.collection.objects.link(ob)
        dg = bpy.context.evaluated_depsgraph_get()
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        if me and len(me.polygons):
            verts = [tuple(mat4 @ v.co) for v in me.vertices]
            faces = [tuple(p.vertices) for p in me.polygons]
            self.add(verts, faces, mat, col)
        ev.to_mesh_clear()
        bpy.context.scene.collection.objects.unlink(ob)
        bpy.data.objects.remove(ob)
        bpy.data.curves.remove(cu)

    # -- realise --------------------------------------------------------------
    def build(self, coll, matrix=None, bevel=None, hide_render=False):
        if not self.f:
            return None
        me = bpy.data.meshes.new(self.name)
        me.from_pydata(self.v, [], self.f)
        me.validate(verbose=False)
        if len(me.polygons) == len(self.fm):
            me.polygons.foreach_set("material_index", self.fm)
            me.polygons.foreach_set("use_smooth", [bool(s) for s in self.fs])
            ca = me.color_attributes.new(name="Col", type='FLOAT_COLOR',
                                         domain='CORNER')
            flat = []
            for poly, col in zip(me.polygons, self.fc):
                flat.extend(col * poly.loop_total)
            ca.data.foreach_set("color", flat)
        ob = bpy.data.objects.new(self.name, me)
        for mn in self.mats:
            me.materials.append(MATS[mn])
        coll.objects.link(ob)
        ob.matrix_world = M_C2W if matrix is None else matrix
        if bevel:
            md = ob.modifiers.new("bev", 'BEVEL')
            md.width = bevel
            md.segments = 2
            md.limit_method = 'ANGLE'
            md.angle_limit = math.radians(35.0)
            md.use_clamp_overlap = True
            md.miter_outer = 'MITER_ARC'
        ob.hide_render = hide_render
        return ob


# --------------------------------------------------------------------------- #
#  MATERIALS                                                                   #
# --------------------------------------------------------------------------- #
MATS = {}


def _nd(nt, typ, loc=(0, 0), **kw):
    n = nt.nodes.new(typ)
    n.location = loc
    for k, v in kw.items():
        if hasattr(n, k):
            setattr(n, k, v)
        else:
            try:
                n.inputs[k.replace('_', ' ')].default_value = v
            except Exception:
                pass
    return n


# R2-072.  THIS USED TO BE `except Exception: pass`.
#
# Addressing by NAME is why R2-057/R2-070 -- a socket INSERTION sliding every
# index along -- cannot happen here.  A socket RENAME or REMOVAL was the case
# the bare `pass` did not cover: the write goes nowhere, forever, and unlike a
# miswired relief chain it leaves NO artefact signature. `socket_blend_scan`
# can see a bump that landed on `Thin Wall`; nothing can see a Roughness that
# was never written, because the socket keeps its default and a default is a
# legal value.
#
# Measured before changing -- `tools/socket_setter_census.py` builds this
# module's material family and watches every call: 76 calls, 0 dropped.  Not
# one call site here depends on a miss being tolerated, so a missing socket is
# a raise; a value the socket refuses is NOT the R2-057 family and stays
# non-fatal, but it stops being invisible.
class SocketGone(KeyError):
    """The named socket is not on this node, so a value was about to vanish."""


def _set(node, key, val):
    if key not in node.inputs:
        raise SocketGone(
            "%s has no input socket %r -- its sockets are %s. Blender resolves "
            "a socket string against the socket's identifier as well as its "
            "display name, so this is a socket that is genuinely gone, not a "
            "rename this lookup could have absorbed."
            % (node.bl_idname, key, [s.name for s in node.inputs]))
    try:
        node.inputs[key].default_value = val
    except Exception as exc:                                     # noqa: BLE001
        print("!! socket write REFUSED: %s.%r = %r -- %s: %s"
              % (node.bl_idname, key, val, type(exc).__name__, exc))


def _newmat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = _nd(nt, 'ShaderNodeOutputMaterial', (900, 0))
    bsdf = _nd(nt, 'ShaderNodeBsdfPrincipled', (600, 0))
    nt.links.new(bsdf.outputs[0], out.inputs[0])
    return m, nt, bsdf


def _noise(nt, loc, scale, detail=6.0, rough=0.55, dist=0.0, vec=None):
    n = _nd(nt, 'ShaderNodeTexNoise', loc)
    _set(n, 'Scale', scale)
    _set(n, 'Detail', detail)
    _set(n, 'Roughness', rough)
    _set(n, 'Distortion', dist)
    if vec is not None:
        nt.links.new(vec, n.inputs['Vector'])
    return n


def _ramp(nt, loc, stops):
    n = _nd(nt, 'ShaderNodeValToRGB', loc)
    el = n.color_ramp.elements
    while len(el) > len(stops):
        el.remove(el[-1])
    for i, (p, c) in enumerate(stops):
        if i >= len(el):
            el.new(p)
        el[i].position = p
        el[i].color = c
    return n


def _mix(nt, loc, a, b, fac, blend='MIX'):
    n = _nd(nt, 'ShaderNodeMix', loc)
    n.data_type = 'RGBA'
    n.blend_type = blend
    if isinstance(fac, float):
        n.inputs['Factor'].default_value = fac
    else:
        nt.links.new(fac, n.inputs['Factor'])
    for sock, val in ((6, a), (7, b)):
        if isinstance(val, tuple):
            n.inputs[sock].default_value = val
        else:
            nt.links.new(val, n.inputs[sock])
    return n


def _math(nt, loc, op, a, b=None, c=None, clamp=False):
    n = _nd(nt, 'ShaderNodeMath', loc)
    n.operation = op
    n.use_clamp = clamp
    for i, v in enumerate((a, b, c)):
        if v is None:
            continue
        if isinstance(v, (float, int)):
            n.inputs[i].default_value = float(v)
        else:
            nt.links.new(v, n.inputs[i])
    return n


def _objcoord(nt, loc=(-1400, 0)):
    tc = _nd(nt, 'ShaderNodeTexCoord', loc)
    return tc.outputs['Object']


def mat_generic(name, base, rough, metallic=0.0, bump_scale=60.0, bump_str=0.10,
                mottle_scale=3.5, mottle_amt=0.10, mottle_dark=0.45,
                rough_var=0.18, vcol=False, grime=0.0, grime_scale=0.9,
                emission=None, emit_str=1.0, alpha=1.0, ior=1.45, sheen=0.0):
    """One layered PBR recipe: base -> mottle -> grime -> roughness break-up
    -> micro bump.  vcol=True takes the base colour from the 'Col' attribute so
    a single material serves an entire family of differently coloured parts."""
    m, nt, b = _newmat(name)
    oc = _objcoord(nt)
    if vcol:
        ca = _nd(nt, 'ShaderNodeVertexColor', (-1100, 200))
        ca.layer_name = "Col"
        basecol = ca.outputs['Color']
    else:
        basecol = base
    mot = _noise(nt, (-1100, -100), mottle_scale, 8.0, 0.6, vec=oc)
    motr = _ramp(nt, (-900, -100), [(0.35, (1, 1, 1, 1)),
                                    (0.75, (mottle_dark,) * 3 + (1,))])
    nt.links.new(mot.outputs['Fac'], motr.inputs['Fac'])
    mixed = _mix(nt, (-650, 100), basecol, motr.outputs['Color'],
                 mottle_amt, 'MULTIPLY')
    col_out = mixed.outputs[2]
    if grime > 0.0:
        gn = _noise(nt, (-1100, -400), grime_scale, 10.0, 0.75, dist=1.5, vec=oc)
        gr = _ramp(nt, (-900, -400), [(0.45, (1, 1, 1, 1)), (0.72, (0, 0, 0, 1))])
        nt.links.new(gn.outputs['Fac'], gr.inputs['Fac'])
        gm = _math(nt, (-720, -400), 'MULTIPLY', gr.outputs['Color'], grime)
        gmix = _mix(nt, (-450, 100), col_out, (0.055, 0.05, 0.045, 1),
                    gm.outputs[0])
        col_out = gmix.outputs[2]
    nt.links.new(col_out, b.inputs['Base Color'])
    _set(b, 'Metallic', metallic)
    _set(b, 'IOR', ior)
    _set(b, 'Alpha', alpha)
    if alpha < 1.0:
        m.blend_method = 'BLEND' if hasattr(m, 'blend_method') else m.blend_method
    # roughness break-up
    rn = _noise(nt, (-1100, -700), mottle_scale * 2.3, 6.0, 0.5, vec=oc)
    rr = _math(nt, (-880, -700), 'MULTIPLY_ADD', rn.outputs['Fac'],
               rough_var, rough - rough_var * 0.5, clamp=True)
    nt.links.new(rr.outputs[0], b.inputs['Roughness'])
    # micro bump
    bn = _noise(nt, (-1100, -1000), bump_scale, 8.0, 0.62, vec=oc)
    bmp = _nd(nt, 'ShaderNodeBump', (-700, -1000))
    _set(bmp, 'Strength', bump_str)
    _set(bmp, 'Distance', 0.02)
    nt.links.new(bn.outputs['Fac'], bmp.inputs['Height'])
    nt.links.new(bmp.outputs['Normal'], b.inputs['Normal'])
    if sheen:
        _set(b, 'Sheen Weight', sheen)
    if emission is not None:
        if vcol:
            nt.links.new(basecol, b.inputs['Emission Color'])
        else:
            _set(b, 'Emission Color', emission)
        _set(b, 'Emission Strength', emit_str)
    MATS[name] = m
    return m


def mat_paving():
    """Cast-in-situ concrete bays.  A white-noise hash on floor(p/bay) gives a
    per-bay constant tone/roughness step that lines up with the modelled joints,
    plus rubber pick-up through the pit-lane working lane."""
    m, nt, b = _newmat("A_ConcSlab")
    oc = _objcoord(nt)
    sc = _nd(nt, 'ShaderNodeVectorMath', (-1250, 300))
    sc.operation = 'SCALE'
    nt.links.new(oc, sc.inputs[0])
    sc.inputs['Scale'].default_value = 1.0 / 5.0
    fl = _nd(nt, 'ShaderNodeVectorMath', (-1080, 300))
    fl.operation = 'FLOOR'
    nt.links.new(sc.outputs[0], fl.inputs[0])
    wn = _nd(nt, 'ShaderNodeTexWhiteNoise', (-920, 300))
    wn.noise_dimensions = '3D'
    nt.links.new(fl.outputs[0], wn.inputs['Vector'])
    bayramp = _ramp(nt, (-740, 300), [(0.0, srgb('#77746d')),
                                      (0.34, srgb('#948f85')),
                                      (0.62, srgb('#6f6d67')),
                                      (0.85, srgb('#a6a29a')),
                                      (1.0, srgb('#837f78'))])
    nt.links.new(wn.outputs['Value'], bayramp.inputs['Fac'])
    # aggregate + mottle
    agg = _noise(nt, (-1250, -60), 55.0, 10.0, 0.72, vec=oc)
    aggr = _ramp(nt, (-1060, -60), [(0.36, (0.60, 0.60, 0.60, 1)),
                                    (0.64, (1.12, 1.11, 1.08, 1))])
    nt.links.new(agg.outputs['Fac'], aggr.inputs['Fac'])
    c1 = _mix(nt, (-540, 200), bayramp.outputs['Color'], aggr.outputs['Color'],
              0.35, 'MULTIPLY')
    stain = _noise(nt, (-1250, -320), 0.55, 12.0, 0.78, dist=1.8, vec=oc)
    stainr = _ramp(nt, (-1060, -320), [(0.36, (1, 1, 1, 1)), (0.72, (0, 0, 0, 1))])
    nt.links.new(stain.outputs['Fac'], stainr.inputs['Fac'])
    c2 = _mix(nt, (-330, 200), c1.outputs[2], srgb('#33312c'),
              _math(nt, (-520, -320), 'MULTIPLY', stainr.outputs['Color'],
                    0.60).outputs[0])
    # large-scale patchiness: 25-40 m of apron reads a whole tone apart
    big = _noise(nt, (-1250, -180), 0.035, 4.0, 0.55, vec=oc)
    bigr = _ramp(nt, (-1060, -180), [(0.30, (0.68, 0.68, 0.67, 1)),
                                     (0.72, (1.06, 1.06, 1.05, 1))])
    nt.links.new(big.outputs['Fac'], bigr.inputs['Fac'])
    c2 = _mix(nt, (-230, 200), c2.outputs[2], bigr.outputs['Color'], 0.85,
              'MULTIPLY')
    # rubber pick-up in the pit lane working lane (circuit y 12..23)
    sep = _nd(nt, 'ShaderNodeSeparateXYZ', (-1250, -600))
    nt.links.new(oc, sep.inputs[0])
    mr = _nd(nt, 'ShaderNodeMapRange', (-1060, -600))
    mr.inputs['From Min'].default_value = 11.0
    mr.inputs['From Max'].default_value = 24.5
    mr.inputs['To Min'].default_value = 1.0
    mr.inputs['To Max'].default_value = 0.0
    mr.clamp = True
    nt.links.new(sep.outputs['Y'], mr.inputs['Value'])
    rn = _noise(nt, (-1060, -820), 2.2, 8.0, 0.7, vec=oc)
    rm = _math(nt, (-860, -700), 'MULTIPLY', mr.outputs[0], rn.outputs['Fac'])
    rm2 = _math(nt, (-700, -700), 'MULTIPLY', rm.outputs[0], 0.75, clamp=True)
    c3 = _mix(nt, (-120, 200), c2.outputs[2], srgb('#2b2a28'), rm2.outputs[0])
    nt.links.new(c3.outputs[2], b.inputs['Base Color'])
    rr = _math(nt, (-330, -520), 'MULTIPLY_ADD', agg.outputs['Fac'], 0.22, 0.55,
               clamp=True)
    nt.links.new(rr.outputs[0], b.inputs['Roughness'])
    bmp = _nd(nt, 'ShaderNodeBump', (-120, -520))
    _set(bmp, 'Strength', 0.22)
    _set(bmp, 'Distance', 0.01)
    nt.links.new(agg.outputs['Fac'], bmp.inputs['Height'])
    nt.links.new(bmp.outputs['Normal'], b.inputs['Normal'])
    MATS["A_ConcSlab"] = m
    return m


def mat_board():
    """Board-marked in-situ concrete for the Beat-4 corridor wall.  The camera
    flies within 5 m of this surface, so the 200 mm shutter boards, the tie
    holes, the pour lines and the rain streaks are all in the shader."""
    m, nt, b = _newmat("A_ConcBoard")
    oc = _objcoord(nt)
    sep = _nd(nt, 'ShaderNodeSeparateXYZ', (-1350, 0))
    nt.links.new(oc, sep.inputs[0])
    # 200 mm boards, with a per-board tone from a white-noise hash
    bd = _math(nt, (-1180, 60), 'MULTIPLY', sep.outputs['Z'], 1.0 / 0.20)
    fl = _math(nt, (-1030, 120), 'FLOOR', bd.outputs[0])
    wn = _nd(nt, 'ShaderNodeTexWhiteNoise', (-880, 120))
    wn.noise_dimensions = '1D'
    nt.links.new(fl.outputs[0], wn.inputs['W'])
    tone = _ramp(nt, (-700, 160), [(0.0, srgb('#7c7a74')), (0.5, srgb('#8f8d86')),
                                   (1.0, srgb('#75736d'))])
    nt.links.new(wn.outputs['Value'], tone.inputs['Fac'])
    fr = _math(nt, (-1030, -60), 'FRACT', bd.outputs[0])
    groove = _ramp(nt, (-880, -60), [(0.0, (0, 0, 0, 1)), (0.09, (1, 1, 1, 1)),
                                     (0.93, (1, 1, 1, 1)), (1.0, (0, 0, 0, 1))])
    nt.links.new(fr.outputs[0], groove.inputs['Fac'])
    grain = _noise(nt, (-1180, -320), 90.0, 10.0, 0.7, vec=oc)
    streak = _nd(nt, 'ShaderNodeMapping', (-1180, -560))
    streak.inputs['Scale'].default_value = (7.0, 7.0, 0.55)
    nt.links.new(oc, streak.inputs['Vector'])
    sn = _noise(nt, (-1000, -560), 2.2, 12.0, 0.8, dist=1.2,
                vec=streak.outputs[0])
    sr = _ramp(nt, (-820, -560), [(0.40, (1, 1, 1, 1)), (0.72, (0.30, 0.29, 0.27, 1))])
    nt.links.new(sn.outputs['Fac'], sr.inputs['Fac'])
    c1 = _mix(nt, (-520, 120), tone.outputs['Color'], sr.outputs['Color'], 0.62,
              'MULTIPLY')
    c2 = _mix(nt, (-330, 120), c1.outputs[2], (0.30, 0.29, 0.27, 1),
              _math(nt, (-520, -120), 'MULTIPLY',
                    _math(nt, (-680, -120), 'SUBTRACT', 1.0,
                          groove.outputs['Color']).outputs[0], 0.8).outputs[0])
    nt.links.new(c2.outputs[2], b.inputs['Base Color'])
    bmp = _nd(nt, 'ShaderNodeBump', (-140, -300))
    _set(bmp, 'Strength', 0.55)
    _set(bmp, 'Distance', 0.03)
    nt.links.new(groove.outputs['Color'], bmp.inputs['Height'])
    bmp2 = _nd(nt, 'ShaderNodeBump', (60, -300))
    _set(bmp2, 'Strength', 0.25)
    _set(bmp2, 'Distance', 0.01)
    nt.links.new(grain.outputs['Fac'], bmp2.inputs['Height'])
    nt.links.new(bmp.outputs['Normal'], bmp2.inputs['Normal'])
    nt.links.new(bmp2.outputs['Normal'], b.inputs['Normal'])
    rr = _math(nt, (-330, -700), 'MULTIPLY_ADD', sn.outputs['Fac'], 0.26, 0.60)
    nt.links.new(rr.outputs[0], b.inputs['Roughness'])
    MATS["A_ConcBoard"] = m
    return m


def mat_paint(name, col, wear=0.55, scale=1.6):
    """Road paint with broken edges: a noise mask drives a Transparent BSDF so
    the mark erodes instead of ending in a hard CG line."""
    m, nt, b = _newmat(name)
    oc = _objcoord(nt)
    _set(b, 'Base Color', col)
    _set(b, 'Roughness', 0.62)
    n = _noise(nt, (-900, -300), 22.0 * scale, 12.0, 0.7, dist=1.2, vec=oc)
    r = _ramp(nt, (-700, -300), [(max(0.0, wear - 0.16), (0, 0, 0, 1)),
                                 (min(1.0, wear + 0.10), (1, 1, 1, 1))])
    nt.links.new(n.outputs['Fac'], r.inputs['Fac'])
    tr = _nd(nt, 'ShaderNodeBsdfTransparent', (600, -260))
    mixsh = _nd(nt, 'ShaderNodeMixShader', (760, -80))
    nt.links.new(r.outputs['Color'], mixsh.inputs['Fac'])
    nt.links.new(tr.outputs[0], mixsh.inputs[1])
    nt.links.new(b.outputs[0], mixsh.inputs[2])
    out = nt.nodes['Material Output']
    nt.links.new(mixsh.outputs[0], out.inputs[0])
    n2 = _noise(nt, (-900, -620), 3.0, 8.0, 0.6, vec=oc)
    rr = _math(nt, (-700, -620), 'MULTIPLY_ADD', n2.outputs['Fac'], 0.25, 0.5)
    nt.links.new(rr.outputs[0], b.inputs['Roughness'])
    MATS[name] = m
    return m


def mat_roofseam():
    """Standing-seam aluminium deck: ribs at 0.60 m, weather streaks, per-panel
    tone.  Read from directly overhead in the Beat-6 climb, so the seam pitch
    and the gutter staining have to survive a 14 m stand-off."""
    m, nt, b = _newmat("A_RoofSeam")
    oc = _objcoord(nt)
    sep = _nd(nt, 'ShaderNodeSeparateXYZ', (-1200, 0))
    nt.links.new(oc, sep.inputs[0])
    w = _math(nt, (-1020, 0), 'MULTIPLY', sep.outputs['X'], 1.0 / 0.60)
    fr = _math(nt, (-880, 0), 'FRACT', w.outputs[0])
    rib = _ramp(nt, (-720, 0), [(0.0, (0, 0, 0, 1)), (0.10, (1, 1, 1, 1)),
                                (0.90, (1, 1, 1, 1)), (1.0, (0, 0, 0, 1))])
    nt.links.new(fr.outputs[0], rib.inputs['Fac'])
    bmp = _nd(nt, 'ShaderNodeBump', (-380, -200))
    _set(bmp, 'Strength', 0.75)
    _set(bmp, 'Distance', 0.06)
    nt.links.new(rib.outputs['Color'], bmp.inputs['Height'])
    nt.links.new(bmp.outputs['Normal'], b.inputs['Normal'])
    # per-panel tone: hash on floor(x / 0.60), the same grid as the ribs
    fl = _nd(nt, 'ShaderNodeMath', (-1020, 260))
    fl.operation = 'FLOOR'
    nt.links.new(w.outputs[0], fl.inputs[0])
    wn = _nd(nt, 'ShaderNodeTexWhiteNoise', (-860, 260))
    wn.noise_dimensions = '1D'
    nt.links.new(fl.outputs[0], wn.inputs['W'])
    ptone = _ramp(nt, (-700, 300), [(0.0, srgb('#6f7477')), (0.4, srgb('#848a8c')),
                                    (0.75, srgb('#767b7e')), (1.0, srgb('#8d9294'))])
    nt.links.new(wn.outputs['Value'], ptone.inputs['Fac'])
    # weathering runs down the fall (object +Y), squashed across the panels
    mp = _nd(nt, 'ShaderNodeMapping', (-1380, -420))
    mp.inputs['Scale'].default_value = (5.0, 0.35, 1.0)
    nt.links.new(oc, mp.inputs['Vector'])
    streak = _noise(nt, (-1200, -420), 1.4, 12.0, 0.82, dist=2.4,
                    vec=mp.outputs[0])
    sr = _ramp(nt, (-1000, -420), [(0.38, (1, 1, 1, 1)),
                                   (0.80, (0.30, 0.31, 0.30, 1))])
    nt.links.new(streak.outputs['Fac'], sr.inputs['Fac'])
    base = _mix(nt, (-600, 200), ptone.outputs['Color'], sr.outputs['Color'],
                0.85, 'MULTIPLY')
    nt.links.new(base.outputs[2], b.inputs['Base Color'])
    _set(b, 'Metallic', 0.30)
    rr = _math(nt, (-600, -600), 'MULTIPLY_ADD', streak.outputs['Fac'], 0.3, 0.46)
    nt.links.new(rr.outputs[0], b.inputs['Roughness'])
    MATS["A_RoofSeam"] = m
    return m


def mat_glass(name, tint, rough=0.03, alpha=0.16):
    m, nt, b = _newmat(name)
    oc = _objcoord(nt)
    _set(b, 'Base Color', tint)
    _set(b, 'Roughness', rough)
    _set(b, 'Transmission Weight', 1.0)
    _set(b, 'IOR', 1.52)
    dirt = _noise(nt, (-900, -300), 2.4, 10.0, 0.7, vec=oc)
    dr = _ramp(nt, (-700, -300), [(0.5, (0, 0, 0, 1)), (0.85, (0.55, 0.55, 0.55, 1))])
    nt.links.new(dirt.outputs['Fac'], dr.inputs['Fac'])
    rr = _math(nt, (-500, -300), 'MULTIPLY_ADD', dr.outputs['Color'], 0.5, rough)
    nt.links.new(rr.outputs[0], b.inputs['Roughness'])
    MATS[name] = m
    return m


def mat_mesh_screen(name, col, alpha=0.42):
    """Woven mesh cladding / debris screen: alpha-blended, not modelled wire."""
    m, nt, b = _newmat(name)
    _set(b, 'Base Color', col)
    _set(b, 'Roughness', 0.62)
    _set(b, 'Metallic', 0.55)
    _set(b, 'Alpha', alpha)
    m.use_backface_culling = False
    MATS[name] = m
    return m


def build_materials():
    for m in list(bpy.data.materials):
        if m.name.startswith("A_") and m.users == 0:
            bpy.data.materials.remove(m)
    MATS.clear()
    mat_paving()
    mat_roofseam()
    mat_board()
    mat_generic("A_ConcPrecast", srgb('#9d9a93'), 0.62, bump_scale=90,
                bump_str=0.12, mottle_scale=2.2, mottle_amt=0.22, grime=0.45,
                grime_scale=1.1)
    mat_generic("A_Asphalt", srgb('#3a3a3a'), 0.72, bump_scale=180,
                bump_str=0.3, mottle_scale=6.0, mottle_amt=0.18, grime=0.2)
    mat_generic("A_SteelGalv", srgb('#b9bcbd'), 0.38, metallic=0.92,
                bump_scale=35, bump_str=0.07, mottle_scale=9.0, mottle_amt=0.22,
                mottle_dark=0.62, grime=0.30, rough_var=0.30)
    mat_generic("A_SteelPaint", srgb('#8f9498'), 0.42, metallic=0.25,
                bump_scale=70, bump_str=0.05, mottle_scale=5.0, mottle_amt=0.10,
                vcol=True, grime=0.28)
    mat_generic("A_Alu", srgb('#87898b'), 0.30, metallic=0.95, bump_scale=40,
                bump_str=0.04, mottle_scale=8.0, mottle_amt=0.10, grime=0.12)
    mat_generic("A_Seat", srgb('#cccccc'), 0.48, vcol=True, bump_scale=120,
                bump_str=0.06, mottle_scale=14.0, mottle_amt=0.10, grime=0.22,
                grime_scale=2.4, rough_var=0.22)
    mat_generic("A_Fabric", srgb('#dddddd'), 0.78, vcol=True, bump_scale=220,
                bump_str=0.22, mottle_scale=8.0, mottle_amt=0.14, sheen=0.35,
                grime=0.25)
    mat_generic("A_Sign", srgb('#dddddd'), 0.30, vcol=True, bump_scale=60,
                bump_str=0.03, mottle_scale=4.0, mottle_amt=0.06, grime=0.18)
    mr = mat_generic("A_Rubber", srgb('#1a1a1d'), 0.86, bump_scale=140,
                     bump_str=0.35, mottle_scale=7.0, mottle_amt=0.18,
                     grime=0.15)
    for n in mr.node_tree.nodes:            # rubber is not a glossy dielectric
        if n.type == 'BSDF_PRINCIPLED':
            _set(n, 'Specular IOR Level', 0.22)
    mat_generic("A_Timber", srgb('#8a6f4e'), 0.66, bump_scale=90, bump_str=0.25,
                mottle_scale=1.2, mottle_amt=0.30, grime=0.3)
    mat_generic("A_Emit", srgb('#ffe9c8'), 0.5, vcol=True, emission=srgb('#ffe9c8'),
                emit_str=6.0, bump_scale=10, bump_str=0.0, mottle_amt=0.0)
    mat_generic("A_EmitStrong", srgb('#fff2dc'), 0.5, vcol=True,
                emission=srgb('#fff2dc'), emit_str=22.0, bump_scale=10,
                bump_str=0.0, mottle_amt=0.0)
    mat_generic("A_Tarmac", srgb('#2f2f31'), 0.74, bump_scale=200, bump_str=0.34,
                mottle_scale=4.0, mottle_amt=0.2, grime=0.25)
    mat_glass("A_Glass", srgb('#cdd8d6'), 0.03, 0.16)
    mat_glass("A_GlassTint", srgb('#7d8f94'), 0.06, 0.30)
    mat_glass("A_Rooflight", srgb('#e6ece9'), 0.42, 0.55)
    mat_generic("A_Spandrel", srgb('#585f63'), 0.34, metallic=0.35,
                bump_scale=50, bump_str=0.04, mottle_amt=0.10, grime=0.2)
    mat_mesh_screen("A_MeshScreen", srgb('#6a6f72'), 0.62)
    mat_mesh_screen("A_MeshDark", srgb('#33383a'), 0.55)
    mat_paint("A_PaintWhite", srgb('#e8e8e4'), 0.50)
    mat_paint("A_PaintWhiteWorn", srgb('#d6d6d0'), 0.72, scale=2.4)
    mat_paint("A_PaintYellow", srgb('#e0b21f'), 0.56)
    mat_paint("A_PaintRed", srgb('#a02620'), 0.58)
    mat_paint("A_PaintBlue", srgb('#1f4f8a'), 0.52)
    mat_generic("A_Soil", srgb('#3b3025'), 0.88, bump_scale=90, bump_str=0.5,
                mottle_scale=5.0, mottle_amt=0.3)


def mat_slab(name, cell, stops, rough=0.55, bump=0.22):
    """Second paving family (forecourt sawn slabs) - same hash trick, own grid."""
    m, nt, b = _newmat(name)
    oc = _objcoord(nt)
    sc = _nd(nt, 'ShaderNodeVectorMath', (-1250, 300))
    sc.operation = 'DIVIDE'
    nt.links.new(oc, sc.inputs[0])
    sc.inputs[1].default_value = (cell[0], cell[1], 1.0)
    fl = _nd(nt, 'ShaderNodeVectorMath', (-1080, 300))
    fl.operation = 'FLOOR'
    nt.links.new(sc.outputs[0], fl.inputs[0])
    wn = _nd(nt, 'ShaderNodeTexWhiteNoise', (-920, 300))
    wn.noise_dimensions = '3D'
    nt.links.new(fl.outputs[0], wn.inputs['Vector'])
    bayramp = _ramp(nt, (-740, 300), stops)
    nt.links.new(wn.outputs['Value'], bayramp.inputs['Fac'])
    agg = _noise(nt, (-1250, -60), 85.0, 10.0, 0.7, vec=oc)
    aggr = _ramp(nt, (-1060, -60), [(0.42, (0.82, 0.82, 0.82, 1)),
                                    (0.60, (1.05, 1.04, 1.02, 1))])
    nt.links.new(agg.outputs['Fac'], aggr.inputs['Fac'])
    c1 = _mix(nt, (-540, 200), bayramp.outputs['Color'], aggr.outputs['Color'],
              0.30, 'MULTIPLY')
    stain = _noise(nt, (-1250, -320), 0.8, 12.0, 0.8, dist=1.6, vec=oc)
    stainr = _ramp(nt, (-1060, -320), [(0.5, (1, 1, 1, 1)), (0.82, (0, 0, 0, 1))])
    nt.links.new(stain.outputs['Fac'], stainr.inputs['Fac'])
    c2 = _mix(nt, (-330, 200), c1.outputs[2], srgb('#4a4741'),
              _math(nt, (-520, -320), 'MULTIPLY', stainr.outputs['Color'],
                    0.42).outputs[0])
    big = _noise(nt, (-1250, -180), 0.05, 4.0, 0.55, vec=oc)
    bigr = _ramp(nt, (-1060, -180), [(0.30, (0.74, 0.74, 0.73, 1)),
                                     (0.72, (1.05, 1.05, 1.04, 1))])
    nt.links.new(big.outputs['Fac'], bigr.inputs['Fac'])
    c2 = _mix(nt, (-230, 200), c2.outputs[2], bigr.outputs['Color'], 0.85,
              'MULTIPLY')
    nt.links.new(c2.outputs[2], b.inputs['Base Color'])
    rr = _math(nt, (-330, -520), 'MULTIPLY_ADD', agg.outputs['Fac'], 0.18, rough)
    nt.links.new(rr.outputs[0], b.inputs['Roughness'])
    bmp = _nd(nt, 'ShaderNodeBump', (-120, -520))
    _set(bmp, 'Strength', bump)
    _set(bmp, 'Distance', 0.008)
    nt.links.new(agg.outputs['Fac'], bmp.inputs['Height'])
    nt.links.new(bmp.outputs['Normal'], b.inputs['Normal'])
    MATS[name] = m
    return m


def build_materials_extra():
    mat_slab("A_ForecourtSlab", (1.5, 1.0),
             [(0.0, srgb('#b6b2a8')), (0.4, srgb('#c2beb3')),
              (0.75, srgb('#aca79c')), (1.0, srgb('#c8c4ba'))], 0.42, 0.16)
    mat_slab("A_ConcApron", (5.0, 5.0),
             [(0.0, srgb('#7b7871')), (0.32, srgb('#8f8b83')),
              (0.62, srgb('#726f69')), (0.86, srgb('#9a968d')),
              (1.0, srgb('#84817a'))], 0.58, 0.26)
    # THE SEALANT IN THE SAWN JOINTS  (defect #48).  Hot-poured bitumen sealant:
    # dark, but NOT black — 0.055 albedo, which is a real polymer-modified sealant
    # and about a third of the concrete beside it.  It is what a joint is supposed
    # to show; the defect was showing 35 mm of sub-base instead.  Deliberately
    # rough and slightly mottled so it does not read as a drawn line.
    mat_generic("A_Sealant", (0.055, 0.055, 0.058, 1.0), 0.82, bump_scale=180,
                bump_str=0.22, mottle_scale=3.0, mottle_amt=0.30,
                mottle_dark=0.55, grime=0.30, rough_var=0.22)
    # --- ground-detail family.  Calibrated against C.lambert_radiance: an
    #     albedo-a horizontal lambertian patch must render at a/pi * (E_direct
    #     + E_sky) = a * 8.276 linear.  See verify_lighting().
    mat_generic("A_Weed", srgb('#3f4a24'), 0.86, vcol=True, bump_scale=260,
                bump_str=0.55, mottle_scale=22.0, mottle_amt=0.42,
                mottle_dark=0.30, grime=0.10, rough_var=0.28)
    mat_generic("A_Checker", srgb('#6e7173'), 0.46, metallic=0.85,
                bump_scale=95, bump_str=0.30, mottle_scale=11.0,
                mottle_amt=0.24, mottle_dark=0.55, grime=0.34, rough_var=0.26)
    mat_generic("A_Gravel", srgb('#6b665c'), 0.90, bump_scale=42, bump_str=0.85,
                mottle_scale=3.2, mottle_amt=0.34, mottle_dark=0.42, grime=0.18)
    mat_generic("A_Plastic", srgb('#c8c8c8'), 0.38, vcol=True, bump_scale=150,
                bump_str=0.06, mottle_scale=6.0, mottle_amt=0.10, grime=0.30,
                rough_var=0.22)
    mat_generic("A_RustSteel", srgb('#6b4a33'), 0.80, metallic=0.55,
                bump_scale=120, bump_str=0.30, mottle_scale=7.0,
                mottle_amt=0.45, mottle_dark=0.35, grime=0.45)
    mat_generic("A_Tarp", srgb('#8e9aa2'), 0.62, vcol=True, bump_scale=180,
                bump_str=0.18, mottle_scale=5.0, mottle_amt=0.16, sheen=0.25,
                grime=0.28)
    mat_generic("A_Leaf", srgb('#33501f'), 0.72, vcol=True, bump_scale=190,
                bump_str=0.35, mottle_scale=16.0, mottle_amt=0.34,
                mottle_dark=0.42, rough_var=0.24)
    mat_generic("A_Bark", srgb('#4a3f34'), 0.88, bump_scale=110, bump_str=0.55,
                mottle_scale=9.0, mottle_amt=0.34, grime=0.25)


# --------------------------------------------------------------------------- #
#  CONVEX POLYGON CLIPPING (paddock slabs are sawn against the forecourt edge)  #
# --------------------------------------------------------------------------- #
def clip_half(poly, a, b, c, keep_inside=True):
    """Clip convex poly (list of (x,y)) by the half plane a*x+b*y+c <= 0."""
    if not poly:
        return []
    out = []
    n = len(poly)
    sgn = 1.0 if keep_inside else -1.0
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        dp = sgn * (a * p[0] + b * p[1] + c)
        dq = sgn * (a * q[0] + b * q[1] + c)
        if dp <= 0.0:
            out.append(p)
        if (dp < 0.0) != (dq < 0.0) and abs(dq - dp) > 1e-12:
            t = dp / (dp - dq)
            out.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
    return out


def subtract_rect(poly, rect_edges):
    """poly minus a convex region defined by half planes -> list of fragments."""
    frags = []
    rest = poly
    for (a, b, c) in rect_edges:
        piece = clip_half(rest, a, b, c, keep_inside=False)
        if len(piece) >= 3:
            frags.append(piece)
        rest = clip_half(rest, a, b, c, keep_inside=True)
        if len(rest) < 3:
            return frags
    return frags


def rect_halfplanes(cx, cy, hx, hy, rot_deg):
    """Half planes (a,b,c) with a*x+b*y+c<=0 inside, for a rotated rectangle."""
    ca, sa = math.cos(math.radians(rot_deg)), math.sin(math.radians(rot_deg))
    ax = (ca, sa)
    ay = (-sa, ca)
    out = []
    for (v, h) in ((ax, hx), (ay, hy)):
        out.append((v[0], v[1], -(v[0] * cx + v[1] * cy) - h))
        out.append((-v[0], -v[1], (v[0] * cx + v[1] * cy) - h))
    return out


# --------------------------------------------------------------------------- #
#  1. PAVING  —  the declared z = 0.000 platform, cut to the contract          #
# --------------------------------------------------------------------------- #
# WHAT CHANGED, AND WHY (assembly review findings #2 and the S7 apron conflict):
#
#   * ARCH_Paving_Apron used to run from circuit y = 9.5 outward.  verge_edge on
#     the pit straight is 10.5, so it paved 1.0 m x 241 m of build_surface's own
#     painted verge at a 55-70 mm offset: a lit coplanar ledge down the whole
#     main straight.
#   * ARCH_Paving_Paddock, ARCH_Paving_Apron and ARCH_Markings all overlapped
#     SURF_AccessRoad across the whole of Beat 4 at 1.4-9.0 mm.  The winning
#     surface flipped six times in 116 m.
#   * Both slabs also ran past the declared rectangles into ground the terrain
#     module builds.
#
# All three are now one rule: a bay is laid only where clear_c() > 0 AND the bay
# is inside a contract rectangle, and a bay that straddles either boundary is
# recursively quartered and SAWN to the curve.  Nothing is offset, nothing is
# hidden, and there is exactly one surface at every point (verify_contract()).
JOINT = 0.011            # half of the 22 mm saw-cut joint
Z_BAY = 0.000            # the declared plane, exactly.  Bay-to-bay level
Z_JIT = 0.0025           # variation is a real 0-2.5 mm construction tolerance,
                         # not a z-fight dodge: nothing else is laid here.
MARK_Z = 0.0075          # thermoplastic, laid ON the slab: always >= 4.0 mm
                         # above the highest possible bay INCLUDING its stain
                         # offset (+1.0 mm) and level jitter (+2.5 mm), so at a
                         # 12.5 deg sun every painted edge draws its own shadow
                         # line instead of z-fighting with the concrete.  At
                         # 5.5 mm the gate still found 3 columns where a
                         # fresh-pour bay came within 2.0 mm of its own paint.
SUBSLAB = 0.34           # depth of the sub-base under the bays

# --------------------------------------------------------------------------- #
#  THE SUB-BASE IS A SLAB, NOT A BOX WITH NO LID   (assembly defect #2 and #3)  #
# --------------------------------------------------------------------------- #
# Every paved field's sub-base was `prism(..., top=False)` — an open coffered
# eggcrate on a 9 m grid.  Two consequences, both measured in the assembled world:
#
#   * every saw joint between bays was not a joint, it was a 300-326 mm VOID.  A
#     22 mm joint over a 326 mm drop renders pitch black at a 12.47 deg sun and
#     the ray-cast probe reports NO GROUND, which is what it is.
#   * where the bays are legitimately absent — under the round-1 pavilion — the
#     eggcrate itself is the visible surface.  That is what CAM_GLASS_GAP.png
#     shows: the corridor mouth, with this module's coffers open to the sky.
#
# So the sub-base is now a CLOSED slab in two layers, and the joint depth is a
# stated number rather than an accident:
#
#   SUB_BED_DZ    the bedding layer directly under the bays.  A bay sits at
#                 Z_BAY + 0..2.5 mm level jitter, -2 mm for a polished old bay and
#                 -4 mm more for a reinstated service cut, so the deepest bay top
#                 is -6 mm: a 24 mm bed leaves >= 18 mm of joint and never less
#                 than 10 mm of clearance over the manhole plates at -14 mm.
#   SUB_FORM_DZ   the formation under the drain and duct corridors, below the
#                 precast channel invert (-55 mm) and the duct box top (-48 mm),
#                 so the hardware still sits IN a trench instead of being buried.
SUB_BED_DZ = 0.024
SUB_FORM_DZ = 0.062


def _bay(mb, x0, x1, y0, y1, z, mat, col=(1, 1, 1, 1)):
    mb.quad((x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z), mat, col)


def _poly_area(p):
    a = 0.0
    for i in range(len(p)):
        q = p[(i + 1) % len(p)]
        a += p[i][0] * q[1] - q[0] * p[i][1]
    return abs(a) * 0.5


def _fc_clearance(cx, cy):
    """Signed distance OUTSIDE the showroom forecourt, in the circuit frame."""
    fx, fy = w2c(FORECOURT['cx'], FORECOURT['cy'])[:2]
    ca, sa = math.cos(math.radians(-ROT_DEG)), math.sin(math.radians(-ROT_DEG))
    dx = (cx - fx) * ca + (cy - fy) * sa
    dy = -(cx - fx) * sa + (cy - fy) * ca
    return np.maximum(np.abs(dx) - FORECOURT['hx'], np.abs(dy) - FORECOURT['hy'])


def _stain(rng, kind):
    """Per-bay tint.  Concrete in a paddock is never one colour: fresh pours,
    polished old bays, fuel shadows, rubber pick-up off the transporter ramps.

    AMPLITUDE MATTERS.  The shader already carries a per-bay tone step of its own
    (mat_paving hashes floor(p / bay), spanning about +-13 %), and the first
    aerial frame showed the two compounding into a chessboard across 44 000 m2
    of 5 x 6 m bays.  So the vertex-colour layer is half what it was: it is there
    to break the shader's regularity, not to compete with it."""
    r = rng.random()
    if kind == 'pit' and r < 0.10:
        return (0.78, 0.77, 0.76, 1), -0.001          # rubber + fuel shadow
    if r < 0.035:
        return (1.035, 1.035, 1.025, 1), +0.001       # fresh pour
    if r < 0.075:
        return (0.950, 0.945, 0.935, 1), -0.002       # old, polished
    if r < 0.105:
        return (0.970, 0.975, 0.985, 1), 0.0          # a bluer batch of cement
    return (1, 1, 1, 1), 0.0


def _y_intervals(y0, y1, bands):
    """[y0, y1] minus the drain / duct corridors, so a bay is never laid across
    one.  The covers used to sit 2.0 mm above the slab they overlapped, which is
    a z-fight in plan, not a lip."""
    out = [(y0, y1)]
    for (a, b) in bands:
        nxt = []
        for (c, d) in out:
            if b <= c or a >= d:
                nxt.append((c, d))
                continue
            if c < a:
                nxt.append((c, a))
            if b < d:
                nxt.append((b, d))
        out = nxt
    return [(a, b) for (a, b) in out if b - a > 0.15]


def _paving_region(mb, rng, rect, cw, ch, mat, tag, drains=(), ducts=(),
                   clearance=None, kind='paddock'):
    """One paved field, cut to the contract.

    Every bay is an individual quad with its own 22 mm joint and its own 0-4 mm
    level; roughly one in nine is not a plain bay at all (manhole, asphalt patch
    over a service cut, fresh pour, polished old bay, gully, duct cover), and
    every bay that meets the road corridor or the access ribbon is sawn to it.
    """
    x0, x1, y0, y1 = rect
    bands = [(d - 0.22, d + 0.22) for d in drains] + \
            [(d - w * 0.5 - 0.13, d + w * 0.5 + 0.13) for (d, w) in ducts]
    strips = _y_intervals(y0, y1, bands)
    nx = max(1, int(round((x1 - x0) / cw)))
    cw = (x1 - x0) / nx
    bays = []
    for (sy0, sy1) in strips:
      ny = max(1, int(round((sy1 - sy0) / ch)))
      chs = (sy1 - sy0) / ny
      for i in range(nx):
        for j in range(ny):
            bx0 = x0 + i * cw + JOINT
            bx1 = x0 + (i + 1) * cw - JOINT
            by0 = sy0 + j * chs + JOINT
            by1 = sy0 + (j + 1) * chs - JOINT
            col, dz = _stain(rng, kind)
            m = mat
            if rng.random() < 0.024:                  # reinstated service cut
                m, dz = "A_Asphalt", dz - 0.004
            bays.append((bx0, bx1, by0, by1,
                         (m, col, Z_BAY + rng.random() * Z_JIT + dz,
                          rng.random(), rng.random())))
    del strips
    frags = cut_bays(bays, clearance) if clearance is not None else \
        [([(b[0], b[2]), (b[1], b[2]), (b[1], b[3]), (b[0], b[3])], b[4], True)
         for b in bays]
    st = {'bays': 0, 'special': 0, 'sawn': 0, 'm2': 0.0}
    for poly, (m, col, z, r1, r2), whole in frags:
        area = _poly_area(poly)
        if area < 0.02:
            continue
        mb.add([(p[0], p[1], z) for p in poly], [tuple(range(len(poly)))], m, col)
        st['bays'] += 1
        st['m2'] += area
        if not whole:
            st['sawn'] += 1
        if m != mat or col != (1, 1, 1, 1):
            st['special'] += 1
        if not whole:
            continue
        bx0, by0 = poly[0]
        bx1, by1 = poly[2]
        # -- a manhole, a gully or a duct pit drops INTO the bay ---------------
        if r1 < 0.016:
            mx, my = (bx0 + bx1) * 0.5, (by0 + by1) * 0.5
            rr = 0.31 + 0.14 * r2
            if r2 < 0.5:
                ring = [(mx + rr * math.cos(k * math.pi / 8),
                         my + rr * math.sin(k * math.pi / 8)) for k in range(16)]
            else:
                ring = [(mx - rr, my - rr * 0.7), (mx + rr, my - rr * 0.7),
                        (mx + rr, my + rr * 0.7), (mx - rr, my + rr * 0.7)]
            mb.add([(p[0], p[1], z - 0.014) for p in ring],
                   [tuple(range(len(ring)))], "A_SteelGalv", (0.55, 0.55, 0.55, 1))
            for k in range(len(ring)):
                a, b = ring[k], ring[(k + 1) % len(ring)]
                mb.quad((a[0], a[1], z), (b[0], b[1], z),
                        (b[0], b[1], z - 0.014), (a[0], a[1], z - 0.014),
                        "A_ConcPrecast", (0.72, 0.72, 0.70, 1))
            st['special'] += 1
        # -- weeds and moss in the saw joint: the single cheapest thing that
        #    stops 44 000 m2 of concrete reading as a shader test card --------
        elif r1 < 0.20:
            wl = 0.25 + 1.9 * r2
            wx = bx0 + (bx1 - bx0 - wl) * ((r1 * 61.0) % 1.0)
            e = by0 - JOINT if (r2 < 0.5) else by1 + JOINT
            mb.quad((wx, e - 0.016, z - 0.003), (wx + wl, e - 0.016, z - 0.003),
                    (wx + wl, e + 0.016, z - 0.003), (wx, e + 0.016, z - 0.003),
                    "A_Weed", (0.7 + 0.6 * r1, 1.0, 0.6, 1))
    # -- sub-base, so the joints read as saw joints and the slab has a real,
    #    closed edge.  Cut to the SAME boundary as the bays: a single box across
    #    the whole rectangle put its top face at -0.014 right across the road
    #    corridor, which is 120 mm ABOVE C.ground_z there — a lit ledge under the
    #    pit wall for 375 m, and the thing that made the first contract gate fail.
    #
    #    TWO CLOSED LAYERS, and neither is `top=False` any more.  The FORMATION
    #    runs under the whole rectangle at -SUB_FORM_DZ, below the drain and duct
    #    inverts, so the trenched hardware still sits in a trench.  The BEDDING
    #    runs under the bay strips only, at -SUB_BED_DZ, so a 22 mm saw joint is
    #    22 mm wide and 18-30 mm deep instead of 22 mm wide and 326 mm deep.
    def _grid(ax0, ax1, ay0, ay1, cell=9.0):
        out = []
        ni = max(1, int(round((ax1 - ax0) / cell)))
        nj = max(1, int(round((ay1 - ay0) / cell)))
        for i in range(ni):
            for j in range(nj):
                out.append((ax0 + (ax1 - ax0) * i / ni,
                            ax0 + (ax1 - ax0) * (i + 1) / ni,
                            ay0 + (ay1 - ay0) * j / nj,
                            ay0 + (ay1 - ay0) * (j + 1) / nj, None))
        return out

    def _lay(cells, za, zb):
        for poly, _pl, _w in (cut_bays(cells, clearance, leaf=0.7, max_split=4)
                              if clearance is not None else
                              [([(b[0], b[2]), (b[1], b[2]), (b[1], b[3]),
                                 (b[0], b[3])], None, True) for b in cells]):
            if _poly_area(poly) < 0.02:
                continue
            mb.prism(poly, za, zb, mat, (0.62, 0.62, 0.61, 1))

    _lay(_grid(x0, x1, y0, y1), -SUBSLAB, -SUB_FORM_DZ)
    for (sy0, sy1) in _y_intervals(y0, y1, bands):
        _lay(_grid(x0, x1, sy0, sy1), -SUB_FORM_DZ + 0.004, -SUB_BED_DZ)
    # -- cast-in slot drains, on the real fall line ---------------------------
    # Built unit by unit and OWNERSHIP-TESTED per unit: a single box across the
    # region ran the drain channel and the cable duct straight over the access
    # ribbon at -26 mm and -20 mm, which is inside C.TOL_COPLANAR_M (30 mm).
    def _own1(a, b, c, d):
        return bool(_owned([(a, c), (b, c), (b, d), (a, d)], pad=0.05).all())

    # The precast unit is now the FULL WIDTH of the corridor the bays were cut
    # around (dy +- 0.22, not +- 0.17) and it runs the WHOLE length of the field,
    # not from x0 + 1.0 to x1 - 1.0.  Both were leaving a 0.44 m wide, 62 mm deep
    # open trench along the formation, which is the same open-joint defect the
    # sub-base cap exists to close, only 20x wider.
    for dy in drains:
        n = int((x1 - x0) / 1.0)
        for k in range(n):
            gx = x0 + k * 1.0
            if not _own1(gx, gx + 1.0, dy - 0.24, dy + 0.24):
                continue
            mb.box((gx, dy - 0.22, -0.30), (gx + 1.0, dy + 0.22, -0.055),
                   "A_ConcPrecast", (0.78, 0.78, 0.77, 1))
            sag = 0.004 if (k % 7) else 0.016      # one grating in seven sits low
            mb.box((gx + 0.02, dy - 0.145, -0.022 - sag),
                   (gx + 0.96, dy + 0.145, 0.001 - sag), "A_SteelGalv",
                   (0.62, 0.62, 0.60, 1))
            if k % 11 == 4:                        # a grating lifted and stacked
                mb.box((gx + 0.10, dy + 0.34, 0.009), (gx + 1.04, dy + 0.63,
                       0.034), "A_SteelGalv", (0.58, 0.58, 0.56, 1))
    # -- cast-in cable ducts with bolted checker-plate covers -----------------
    for (dy, w) in ducts:
        n = int((x1 - x0) / 1.22) + 1
        for k in range(n):
            gx = x0 + k * 1.22
            if not _own1(gx, gx + 1.22, dy - w * 0.5 - 0.14, dy + w * 0.5 + 0.14):
                continue
            mb.box((gx, dy - w * 0.5 - 0.13, -0.55),
                   (gx + 1.22, dy + w * 0.5 + 0.13, -0.048), "A_ConcPrecast",
                   (0.74, 0.74, 0.73, 1))
            lift = 0.0 if (k % 13) else 0.035      # one cover in thirteen is proud
            mb.box((gx + 0.02, dy - w * 0.5, -0.022 + lift),
                   (gx + 1.18, dy + w * 0.5, 0.004 + lift), "A_Checker",
                   (0.60 + 0.10 * ((k * 7) % 3) / 3.0, 0.60, 0.58, 1))
            for sy in (-w * 0.5 + 0.06, w * 0.5 - 0.06):
                for sx in (gx + 0.12, gx + 1.08):
                    mb.cyl((sx, dy + sy, 0.004 + lift), (sx, dy + sy, 0.016 + lift),
                           0.016, "A_SteelGalv", (0.5, 0.5, 0.5, 1), n=6)
    return st


# --------------------------------------------------------------------------- #
#  1b. THE RETAINING EDGE                                                      #
# --------------------------------------------------------------------------- #
def _retain_run(mb, rng, S, side, tag, stats):
    """Cast edge beam along the corridor rim, welded to C.corridor_rim's z.

    Geometry, stated once so it cannot drift: the TOP of the beam is exactly on
    C.platform_edge — which is where the paving is cut — so the beam and the slab
    share an edge instead of overlapping.  The face batters INTO the corridor
    (wider at the base, as a retaining wall must be), and the heel is deliberately
    30 mm BELOW the road programme's own ground at its own lateral, so it is
    buried rather than laid on top of somebody else's surface."""
    if len(S) < 2:
        return
    S = np.asarray(S, float)
    e = WC.platform_edge(S, side)
    P = WC.su_to_world(S, e * side)
    cx, cy = WC.world_to_circuit(P[:, 0], P[:, 1])
    wz_ = P[:, 2]
    # inboard (toward the track) unit normal, taken from the contract itself
    Q = WC.su_to_world(S, (e - 1.0) * side)
    qx, qy = WC.world_to_circuit(Q[:, 0], Q[:, 1])
    ix, iy = qx - cx, qy - cy
    il = np.hypot(ix, iy)
    il[il < 1e-9] = 1.0
    ix, iy = ix / il, iy / il
    # the road programme's ground 0.28 m inboard, which the heel must sit under
    zh = WC.ground_z(S, (e - 0.28) * side)
    drop = APRON_Z - wz_
    for i in range(len(S) - 1):
        a, b = i, i + 1
        d0, d1 = float(drop[a]), float(drop[b])
        t0, t1 = (cx[a], cy[a]), (cx[b], cy[b])
        z0, z1 = float(wz_[a]), float(wz_[b])
        if max(d0, d1) < RETAIN_MIN_DROP:
            continue                # flush: the sawn slab edge is the boundary
        tone = 0.86 + 0.10 * ((i * 5) % 4) / 4.0
        bt = 0.045                     # batter: the base leans into the corridor
        f0 = (t0[0] + ix[a] * bt, t0[1] + iy[a] * bt)
        f1 = (t1[0] + ix[b] * bt, t1[1] + iy[b] * bt)
        # exposed face: top ON the rim (= the paving cut), base battered inboard
        mb.add([(f0[0], f0[1], z0 - 0.32), (f1[0], f1[1], z1 - 0.32),
                (t1[0], t1[1], APRON_Z), (t0[0], t0[1], APRON_Z)],
               [(0, 1, 2, 3)], "A_ConcBoard", (tone, tone, tone * 0.99, 1))
        # heel, buried 30 mm under the road programme's own ground
        h0 = (t0[0] + ix[a] * RETAIN_TOE, t0[1] + iy[a] * RETAIN_TOE)
        h1 = (t1[0] + ix[b] * RETAIN_TOE, t1[1] + iy[b] * RETAIN_TOE)
        mb.add([(f0[0], f0[1], z0 - 0.32), (f1[0], f1[1], z1 - 0.32),
                (h1[0], h1[1], float(zh[b]) - 0.030),
                (h0[0], h0[1], float(zh[a]) - 0.030)],
               [(0, 1, 2, 3)], "A_ConcPrecast", (0.76, 0.76, 0.75, 1))
        stats['m'] += float(np.hypot(cx[b] - cx[a], cy[b] - cy[a]))
        # weep pipes and staining, every fourth panel
        if i % 4 == 1 and d0 > 0.09:
            mb.cyl((f0[0], f0[1], z0 + 0.10),
                   (f0[0] + ix[a] * 0.10, f0[1] + iy[a] * 0.10, z0 + 0.10),
                   0.036, "A_ConcBoard", (0.34, 0.33, 0.31, 1), n=8)
        # a bollard above the drop, where it is deep enough to fall off
        if d0 > 0.28 and i % 7 == 3:
            px, py = t0[0] - ix[a] * 0.40, t0[1] - iy[a] * 0.40
            h = 0.98 + rng.uniform(-0.05, 0.05)
            mb.cyl((px, py, APRON_Z - 0.05), (px, py, APRON_Z + h), 0.055,
                   "A_SteelGalv", (1, 1, 1, 1), n=8)
            mb.cyl((px, py, APRON_Z + h - 0.10), (px, py, APRON_Z + h),
                   0.062, "A_PaintYellow", (1, 1, 1, 1), n=8)


def _terrain_skirt(mb, rng, a, b, inward, tag):
    """Closed skirt + kerb where the platform abuts ground this module is not
    allowed to know the height of.  Runs TERRAIN_SKIRT below the deck, so the
    terrain module may weld anywhere in that band and the edge still reads as a
    kerb rather than as a floating slab."""
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    if L < 0.5:
        return
    ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    nxv, nyv = inward
    n = max(1, int(L / 2.4))
    for k in range(n):
        t0, t1 = k / n, (k + 1) / n
        p0 = (a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0)
        p1 = (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1)
        tone = 0.84 + 0.12 * ((k * 3) % 5) / 5.0
        mb.quad((p0[0], p0[1], -TERRAIN_SKIRT), (p1[0], p1[1], -TERRAIN_SKIRT),
                (p1[0], p1[1], APRON_Z + 0.11), (p0[0], p0[1], APRON_Z + 0.11),
                "A_ConcBoard", (tone, tone, tone * 0.99, 1))
        mb.quad((p0[0], p0[1], APRON_Z + 0.11), (p1[0], p1[1], APRON_Z + 0.11),
                (p1[0] + nxv * 0.16, p1[1] + nyv * 0.16, APRON_Z + 0.11),
                (p0[0] + nxv * 0.16, p0[1] + nyv * 0.16, APRON_Z + 0.11),
                "A_ConcPrecast", (0.80, 0.80, 0.79, 1))
        mb.quad((p0[0] + nxv * 0.16, p0[1] + nyv * 0.16, APRON_Z + 0.11),
                (p1[0] + nxv * 0.16, p1[1] + nyv * 0.16, APRON_Z + 0.11),
                (p1[0] + nxv * 0.16, p1[1] + nyv * 0.16, APRON_Z),
                (p0[0] + nxv * 0.16, p0[1] + nyv * 0.16, APRON_Z),
                "A_ConcPrecast", (0.74, 0.74, 0.73, 1))
        if k % 6 == 2:                       # a kerb unit knocked out of line
            mb.box((p0[0] - 0.05, p0[1] - 0.05, APRON_Z + 0.05),
                   (p0[0] + 0.05, p0[1] + 0.05, APRON_Z + 0.15),
                   "A_ConcPrecast", (0.70, 0.70, 0.69, 1))


# --------------------------------------------------------------------------- #
#  1c. THE PIT-EXIT APRON PLATFORM  (C.platform_owner -> this module)          #
# --------------------------------------------------------------------------- #
# spec S10.5 declares the pit-exit apron, the access road and the racing surface
# "one plane at z = 0.000", and spec S9 crowns the racing surface, which puts its
# edge at -0.12 m.  The contract resolves that inside ground_z as a real valley
# gutter: 132 mm of rise over 8.0 m at a 3.05 % cross-grade, landing on exactly
# 0.000 and staying there.  This builds the concrete that gutter is cast in, so
# every vertex comes from C.su_to_world and the datum cannot drift by a micron.
#
# ASSEMBLY DEFECT #3, and the three separate mistakes inside it:
#
#   (a) the bay grid's u origin was `verge_edge.min()` — which on the pit straight
#       IS verge_edge at every station, because half_width is a constant 8.000 over
#       S15 — and every bay was then inset 12 mm.  So the first column began at
#       u = 10.512 against SURF_Track's outer edge at u = 10.500 and the clearance
#       test `d_in = u - verge_edge` never fired.  The grid origin is now a bay and
#       a half INBOARD of the inner limit, so the first column ALWAYS straddles and
#       is ALWAYS sawn: the inset can no longer survive at the boundary.  That is
#       exactly how ARCH_Paving_Paddock behaves, which is why the paddock never had
#       this defect: its rectangle's edges are nowhere near its cut line.
#   (b) the inner limit is no longer `verge_edge` at all.  build_surface lays
#       SURF_ApronJoint from verge_edge outward as a 50 mm sealed asphalt joint
#       with a 1.6 mm lap at its outer end; this slab starts on the end of that lap
#       (APRON_JOINT_LAP_M), so the two modules meet at a declared joint instead of
#       at a shared coordinate they both stop on.
#   (c) the same 12 mm inset ran in s, opening the same joint across the apron's
#       two ends where it meets build_barriers' runoff.  The ends are now sawn on
#       C.apron_zone == 0.5, which is exactly where C.platform_owner hands the
#       surface over.
#
# and the sub-base is a CLOSED slab with a top face, APRON_SUB_CAP under the datum,
# so a joint anywhere in the field is a joint and not a shaft.
APRON_GRID_INSET = 4.5       # how far INBOARD of the inner limit the u grid starts,
                             # so the first column always straddles and is always
                             # sawn.  0.0 was the defect: on the pit straight
                             # verge_edge is a constant 8.000 + 2.500, so
                             # `verge_edge.min()` IS verge_edge at every station and
                             # the grid origin landed exactly on the cut line.
APRON_BAY_JOINT = 0.004      # half of the 8 mm sawn joint (was 12 mm, and open)
APRON_SUB_CAP = 0.035        # bedding under the bays, 35 mm under the datum
# DEFECT #48, v1.1.1.  The line above used to be the WHOLE story, and its own
# comment claimed "an 8 mm saw joint is 8 mm wide and 10 mm deep".  It is not: the
# bays are laid ON the datum and the only thing under them was this bedding, so
# every sawn joint in the pit-exit apron was an 8 mm slot falling 35 mm to the
# sub-base.  MEASURED on the assembled world, scanning u at 1 mm:
#
#     s = 3300 / 3340 / 3380   u 39.047-39.054   8 mm wide, 35.0 mm deep
#
# — one at every 3.0 m bay line, the whole length of the apron.  At the declared
# 12.47 deg sun `C.SUN_SHADOW_RATIO` = 4.5222, so a 35 mm step casts 158 mm of
# shadow and NO DIRECT SUN REACHES THE FLOOR OF AN 8 mm SLOT.  All that is left is
# the 41 % of the sky the slot can see, and `C.recess_relative_radiance(0.008,
# 0.035)` = 0.037 of the surface beside it.  That is the 3,390 pure-black pixels
# the review found in CAM_APRON_EDGE.png — not a missing bay, a joint detail.
#
# THE FIX IS THE ONE A REAL SLAB USES: the joint is SEALED.  A second, shallow cap
# runs under the whole bay field at the contract's own declared sealant invert, so
# what shows in the joint is sealant 5 mm down and not sub-base 35 mm down.  The
# deep bedding stays exactly as it was, doing the job it was added for (burying the
# perimeter under the neighbouring surface at more than TOL_COPLANAR_M).
APRON_SEAL_CAP = float(getattr(WC, "APRON_JOINT_DEPTH_M", 0.005))   # 5 mm
APRON_SEAL_OVERRUN = 0.030   # 30 mm past the bay cut.  `cut_bays` clips a leaf cell
                             # with a LINEAR crossing at a resolution of
                             # APRON_LEAF / 2**APRON_SPLIT = 11 mm, so without an
                             # overrun the seal can fall short of the bay edge by up
                             # to that much and the bedding shows through the sliver:
                             # MEASURED at 0 mm overrun, a 4 mm x 34.8 mm slot at
                             # s = 3403 reading 0.019 of the surface beside it.
                             # 30 mm covers the clipper's error with margin and is
                             # far too small to reach a neighbouring surface — the
                             # 62 cm inset the declared-rectangle check uses is 20x
                             # it, and `clr` already carries `C.platform_field`.
APRON_BED_OVERRUN = 0.150    # ... and the bedding runs 150 mm PAST the bay cut on
                             # every side.  Two reasons, both measured:
                             #   * inboard it reaches 100 mm inside verge_edge, so
                             #     the 50 mm the contract gives build_surface's
                             #     SURF_ApronJoint has concrete 35 mm under it
                             #     instead of a 300 mm shaft — the review's exact
                             #     u = 10.500..10.512 scan;
                             #   * `cut_bays` clips a leaf cell with a LINEAR
                             #     crossing, and `clr` is not linear where the R150
                             #     ribbon crosses the apron, so the bay edge can
                             #     miss the true boundary by a few centimetres.  It
                             #     did, twice in 9 000 columns, and both were 293 mm
                             #     holes.  The overrun is deeper than
                             #     C.TOL_COPLANAR_M (30 mm) so it is buried under
                             #     the neighbour rather than coplanar with it.


def apron_clearance(su_s, su_u):
    """Signed clearance in (s, u): inside the pit-exit apron platform is > 0.

    THE ONE PREDICATE for the apron, at module scope so `build_apron_platform`
    and `verify_contract` cannot ask the question two different ways — which is
    the whole failure mode this round of the review exists to fix.  The bays are
    a REGULAR 2.4 x 3.0 m grid in (s, u) and this saws them to the platform edge,
    to the ribbon, to the apron zone's own ends and to build_surface's declared
    apron joint, instead of stretching the bay count per station to fit.  The
    stretched version produced acute irregular n-gons whose per-bay tone step
    rendered as shattered concrete at a grazing 12.5 deg sun -- visible in the
    first arch_apron_rim frame.
    """
    su_s = np.atleast_1d(np.asarray(su_s, float))
    su_u = np.atleast_1d(np.asarray(su_u, float))
    wx, wy, _ = np.transpose(WC.su_to_world(su_s, su_u))
    t, v = WC.access_project(wx, wy)
    lo, hi = _ribbon_edges(t)
    # THE INBOARD SIDE IS MEASURED IN LAP COORDINATES, v1.1.1 (defect #47).
    # `_ribbon_edges` is in ROUTE coordinates, and over the merge arc the route
    # heading differs from the lap heading by up to 3.3 deg, so an edge clipped to
    # `verge_edge` at the ROUTE's station lands up to 0.44 m OUTBOARD of
    # `verge_edge` once it is re-projected onto the lap.  Subtracting a further
    # 0.30 m saw margin from that put this slab's inboard cut at u = 10.64 while
    # `SURF_Track` ends at 10.50 and `SURF_AccessRoad` really begins at 10.94 —
    # MEASURED as an 13-100 mm wide, 300 mm deep black slot at s = 3400-3420 by
    # the recess gate below.  `C.ribbon_edge_u` is the ribbon's edge IN LAP
    # COORDINATES, published by the contract; on the same `ground_z` the two
    # surfaces butt exactly and there is nothing to saw.  The saw margin is kept on
    # the OUTBOARD side and on the longitudinal caps, where the two really do meet
    # slab-to-strip.
    lo_u = np.asarray(WC.ribbon_edge_u(su_s, "in"), float)
    d_rib_in = np.where(np.isfinite(lo_u), lo_u - su_u, np.inf)
    d_rib = np.maximum.reduce([d_rib_in, v - (hi + RIBBON_SAW_M),
                               RIBBON_T_MIN - t,
                               t - (WC.ACCESS_TOTAL + RIBBON_SAW_M)])
    # THE OUTBOARD CUT HANDS OVER TO A BAY FIELD — WHERE THERE IS ONE, AND ONLY
    # THERE.  `clear_c` (which cuts `build_paving`'s bay fields) is positive
    # exactly where `|u| > platform_edge`, so `platform_edge` is the line at
    # which this slab stops and a bay field starts.  The two predicates tile the
    # plane at that line with no overlap and no gap — PROVIDED a bay field
    # actually covers the other side of it.
    #
    # `build_paving` tiles bays over the `pit_lane`, `garages` and `paddock`
    # rectangles.  IT DOES NOT TILE THE `apron` RECTANGLE.  So outboard of
    # `platform_edge` and inside `apron`, this cut handed the ground to nobody:
    # `world_ground_z` returns a finished height and names OWNER_APRON — i.e.
    # this module — and no module laid a face.
    #
    # MEASURED on assembly8 (contract 1.2.1), s 3360-3500 x u 10-42 at
    # 0.50 x 0.10 m, counting only samples where `world_ground_z` is NOT NaN:
    # 7 803 samples = 390.15 m2 of DECLARED ground with nothing built on it,
    # 389.30 m2 of it owned by `build_architecture:paving`.  383.05 m2 has
    # nothing at all under the ray — not even terrain, which R2-040 cut out of
    # the declared platform — so it is open to the sky.
    #
    # It went unseen because `probe_pitexit.seam_map` samples u 10.00..16.00 and
    # the gap runs from u 10.50 to u 40.40: only 24.40 m2 of it is inside that
    # window, and the map's own reported `u_range` maximum is 15.999..., its
    # window edge.  A window that stops INSIDE the thing it measures reports the
    # first slice of it as the whole.
    #
    # `_PIT_NOSE_X` is where the `pit_lane` and `apron` rectangles abut, and it
    # is derived from `PIT_WALL_X0`, which v1.1.1 moved 17.7 m west.  The bay
    # field's west end moved with it; this slab's outboard cut did not follow.
    # SCOPED TO THE `apron` RECTANGLE, AND THE FIRST VERSION OF THIS FIX WAS NOT.
    # Releasing the cut wherever `platform_field` is negative released it inside
    # EVERY declared rectangle, so the grid ran to u = 62.55 against a
    # `platform_edge` maximum of 40.56 and the slab grew 5 881.5 -> 6 421.2 m2,
    # spilling east of the pit wall where it is not the apron's ground at all.
    # The module's own gates caught it (test build `work/r2132/arch_fixed.blend`):
    # 9 BLACK recesses at 30.0 mm x 310.5 mm on the new outer edge at s 3490,
    # 3502 and 3514 -> 0.0157 of the surface beside them against a 0.10 bound,
    # and 2 coplanar samples 22 mm under another module on the Beat-4 route.
    # The extension belongs ONLY where the apron rectangle is the declared owner
    # and no bay field covers the far side of `platform_edge`.
    cx_c, cy_c = WC.world_to_circuit(wx, wy)
    handover = np.zeros(np.shape(cx_c), bool)
    for _nm in ("pit_lane", "garages", "paddock"):
        handover |= in_rect(cx_c, cy_c, PLAT_RECTS[_nm], inset=0.0)
    own_apron = in_rect(cx_c, cy_c, PLAT_RECTS["apron"], inset=0.0)
    d_out = np.where(own_apron & ~handover, np.inf,
                     WC.platform_edge(su_s, +1) - su_u)
    d_in = su_u - (WC.verge_edge(su_s) + APRON_JOINT_LAP_M)
    # C.platform_owner hands this surface over at apron_zone == 0.5 exactly
    d_ap = (WC.apron_zone(su_s, +1) - 0.5) * 40.0
    # ... AND THE DECLARED RECTANGLES, v1.1.1.  `apron_zone` is a smooth weight and
    # its 0.5 crossing is at circuit x = -503, which is 23 m WEST of the declared
    # apron rectangle's own x0 = -480.  The slab ran out there — 350 up-faces over
    # circuit x -487.95..-480.68 — and the module's "paving stays inside the
    # contract's declared rectangles" check could not see it, because it only looks
    # at faces within 50 mm of the plane and the bedding sits 53 mm down there.  A
    # shallower layer (the sealed joint, #48) made the same overrun visible.  So the
    # cut asks the contract where the platform IS, instead of inferring it from a
    # weight: `C.platform_field` is negative inside the declared rectangles.
    d_plat = -np.asarray(WC.platform_field(wx, wy), float)
    return np.minimum.reduce([d_rib, d_out, d_in, d_ap, d_plat])


def build_apron_platform(colls, rng, summary):
    mb = MB("ARCH_Paving_ApronPlatform")
    # THE GRID'S STATION RANGE IS DERIVED, NOT TYPED.  It used to be the literal
    # `3186.0, 3436.0`, and `keep = apron_zone > 0.5` then SILENTLY TRUNCATED the
    # slab wherever the contract's apron ran past 3436 — which is exactly what
    # happened when v1.1.1 moved the pit wall east and `apron_zone > 0.5` went with
    # it to s = 3470: 34 m of declared apron with no slab on it, and the module
    # reported success because its own predicate never saw the stations it was not
    # given.  A hard-coded window over a contract quantity is a defect waiting for
    # the contract to move.
    _aps = np.arange(3050.0, 3600.0, 0.5)
    _apk = np.nonzero(WC.apron_zone(_aps, +1) > 0.5)[0]
    S0 = float(_aps[_apk[0]]) - 9.6 if len(_apk) else 3186.0
    S1 = float(_aps[_apk[-1]]) + 9.6 if len(_apk) else 3436.0
    ds = 2.4
    S = np.arange(S0, S1 + ds, ds)
    keep = WC.apron_zone(S, +1) > 0.5
    if not keep.any():
        return []
    # one station of overlap either side, so the apron_zone == 0.5 crossing is
    # INSIDE the grid and gets sawn rather than landing on an inset bay edge
    idx = np.nonzero(keep)[0]
    lo_i = max(0, int(idx[0]) - 1)
    hi_i = min(len(S) - 1, int(idx[-1]) + 1)
    S = S[lo_i:hi_i + 1]
    n_s = len(S) - 1
    E = WC.verge_edge(S) + APRON_JOINT_LAP_M
    P = WC.platform_edge(S, +1)

    clr = apron_clearance
    # THE OUTBOARD GRID BOUND IS DERIVED FROM THE DECLARED PLATFORM, NOT FROM
    # `platform_edge`.  This was `float(P.max()) + 3.0`, which is the same
    # mistake as the hard-coded `3186.0, 3436.0` station window above, one axis
    # over: a grid sized to a contract quantity that is NOT the one the cut uses.
    # `apron_clearance` now runs outboard to the declared rectangle wherever no
    # bay field takes over, and a grid that stops at `max(platform_edge) + 3`
    # would silently truncate the slab at u ~ 23.9 while the declared apron runs
    # to u ~ 40.4 — leaving the module reporting success over ground it was never
    # given.  Ask the contract where its platform IS.
    # ... and the bound is the `apron` RECTANGLE, not `platform_field`, for the
    # reason written against `d_out` in `apron_clearance`: `platform_field` is
    # negative inside every declared rectangle, so sizing the grid by it sized it
    # to the paddock and ran to u = 62.55.
    _up = np.arange(float(E.min()) - APRON_GRID_INSET, 60.0, 0.5)
    _gs2, _gu2 = np.meshgrid(S, _up, indexing="ij")
    _w2 = WC.su_to_world(_gs2.ravel(), _gu2.ravel())
    _cx2, _cy2 = WC.world_to_circuit(_w2[:, 0], _w2[:, 1])
    _in2 = in_rect(_cx2, _cy2, PLAT_RECTS["apron"], inset=0.0)
    UMAX = max(float(P.max()), (float(_gu2.ravel()[_in2].max())
                                if _in2.any() else 0.0)) + 3.0
    UMIN = float(E.min()) - APRON_GRID_INSET   # a bay and a half in: see (a) above
    print("[apron] grid u %.2f .. %.2f  (platform_edge max %.2f; the declared "
          "platform reaches %.2f)" % (UMIN, UMAX, float(P.max()), UMAX - 3.0))
    nu = int(math.ceil((UMAX - UMIN) / 3.0))
    j2 = APRON_BAY_JOINT
    bays = []
    for i in range(n_s):
        a, b = float(S[i]), float(S[i + 1])
        for j in range(nu):
            ua = UMIN + j * 3.0
            ub = ua + 3.0
            col, dz = _stain(rng, 'apron')
            m = "A_ConcApron" if rng.random() > 0.03 else "A_Asphalt"
            bays.append((a + j2, b - j2, ua + j2, ub - j2,
                         (m, col, dz, rng.random())))
    # leaf 0.35 / 5 splits, NOT 0.9 / 3.  `cut_bays` tests a cell's four corners,
    # so a THIN POSITIVE RIDGE between two negative corners is invisible to it and
    # the whole cell is dropped.  There is exactly such a ridge here: past s = 3390
    # the R150 ribbon eats the apron from outboard while build_surface's joint lap
    # holds the inboard edge, and at s = 3398 the feasible strip is 0.75 m wide
    # against a 0.375 m leaf.  Measured, that dropped three 293 mm holes into the
    # apron at world (109.6..110.2, +-0.2) — found by the sweep above, not by eye.
    #
    # AND THE MINIMUM FRAGMENT AREA HAS TO FOLLOW THE LEAF.  It was a flat
    # 0.03 m2.  At leaf 0.35 / 5 splits a leaf is 0.093 x 0.075 m = 0.007 m2, so
    # every clipped fragment AND every whole leaf near the boundary fell under the
    # threshold and was thrown away: a 0.28 m wide strip of finished slab vanished
    # down the entire pit-exit apron edge, and the ray sweep still passed, because
    # the bedding underneath is only 35 mm down.  THE RENDER FOUND IT — a 46 mm
    # blue shadow trough down 220 m of the pit straight.  That is the whole reason
    # "the joint measures closed" is not the test.
    APRON_LEAF, APRON_SPLIT = 0.35, 5
    # 0.2 cm2, i.e. essentially nothing.  At 2 % of a leaf (24 cm2) a sliver up to
    # 33 mm wide could still be discarded AT THE JOINT LINE, which is a 33 mm wide
    # 35 mm deep groove in the one place in the world that must not have one.
    APRON_MIN_FRAG = 2e-5
    frags = cut_bays(bays, clr, leaf=APRON_LEAF, max_split=APRON_SPLIT)
    area = 0.0
    for poly, (m, col, dz, r1), whole in frags:
        if _poly_area(poly) < APRON_MIN_FRAG:
            continue
        SS = np.array([p[0] for p in poly])
        UU = np.array([p[1] for p in poly])
        pts = WC.su_to_world(SS, UU)
        pts[:, 2] += dz
        mb.add([tuple(p) for p in pts], [tuple(range(len(poly)))], m, col)
        area += _poly_area(poly)
        if r1 < 0.02:                       # a gully on the gutter invert
            sm = float(SS.mean())
            um = float(min(UU.mean(), 13.0))
            g = WC.su_to_world(np.array([sm]), np.array([um]))[0]
            mb.cyl((g[0], g[1], g[2] - 0.02), (g[0], g[1], g[2] - 0.05), 0.34,
                   "A_SteelGalv", (0.55, 0.55, 0.54, 1), n=12)
    # BEDDING: sawn to the same boundary as the bays and capped APRON_SUB_CAP
    # under the datum, so an 8 mm saw joint is 8 mm wide and 10 mm deep.  Before
    # this the ray fell 0.300 m through every one of them, and 12 mm of it ran the
    # whole 220 m of the pit-exit apron edge as a black line at a 12.47 deg sun.
    cap = []
    for i in range(n_s):
        a, b = float(S[i]), float(S[i + 1])
        for j in range(nu):
            cap.append((a, b, UMIN + j * 3.0, UMIN + (j + 1) * 3.0, None))
    cm2 = 0.0

    def clr_bed(su_s, su_u):
        return clr(su_s, su_u) + APRON_BED_OVERRUN

    for poly, _pl, _w in cut_bays(cap, clr_bed, leaf=APRON_LEAF,
                                  max_split=APRON_SPLIT):
        if _poly_area(poly) < APRON_MIN_FRAG:
            continue
        SS = np.array([p[0] for p in poly])
        UU = np.array([p[1] for p in poly])
        pts = WC.su_to_world(SS, UU)
        pts[:, 2] -= APRON_SUB_CAP
        mb.add([tuple(p) for p in pts], [tuple(range(len(poly)))],
               "A_ConcApron", (0.66, 0.66, 0.65, 1))
        cm2 += _poly_area(poly)

    # THE SEALED JOINT  (defect #48).  Everything above leaves the sawn joints
    # looking 35 mm down at the bedding, which at a 12.47 deg sun is a black line
    # at every bay edge.  This lays the sealant: the SAME cell grid, uncut by the
    # 4 mm bay inset so it spans every joint, at the contract's declared
    # `APRON_JOINT_DEPTH_M` invert.  What the camera sees in a joint is now
    # 8 mm wide and 5 mm deep -> C.recess_relative_radiance = 0.180, a grey line,
    # against 0.037 for the 35 mm slot it replaces.  It is BELOW the bays, so it
    # changes nothing anywhere the finished slab is present.
    sm2 = 0.0

    def clr_seal(su_s, su_u):
        return clr(su_s, su_u) + APRON_SEAL_OVERRUN

    for poly, _pl, _w in cut_bays(cap, clr_seal, leaf=APRON_LEAF,
                                  max_split=APRON_SPLIT):
        if _poly_area(poly) < APRON_MIN_FRAG:
            continue
        SS = np.array([p[0] for p in poly])
        UU = np.array([p[1] for p in poly])
        pts = WC.su_to_world(SS, UU)
        pts[:, 2] -= APRON_SEAL_CAP
        mb.add([tuple(p) for p in pts], [tuple(range(len(poly)))],
               "A_Sealant", (0.11, 0.11, 0.115, 1))
        sm2 += _poly_area(poly)
    summary['apron_seal_m2'] = round(sm2, 1)
    summary['apron_seal_cap_mm'] = round(1000 * APRON_SEAL_CAP, 2)

    # FORMATION: a closed slab under the whole sweep so no edge is a hole
    for i in range(n_s):
        a, b = S[i], S[i + 1]
        for (ua, ub) in ((float(E[i]) - APRON_JOINT_LAP_M, float(P[i])),):
            q = WC.su_to_world(np.array([a, b, b, a]),
                               np.array([ua, ua, ub, ub]))
            mb.add([(q[0][0], q[0][1], q[0][2] - 0.30),
                    (q[1][0], q[1][1], q[1][2] - 0.30),
                    (q[2][0], q[2][1], q[2][2] - 0.30),
                    (q[3][0], q[3][1], q[3][2] - 0.30)],
                   [(3, 2, 1, 0)], "A_ConcApron", (0.6, 0.6, 0.59, 1))
    summary['apron_platform_m2'] = round(area, 1)
    summary['apron_bedding_m2'] = round(cm2, 1)
    summary['apron_joint_lap_m'] = APRON_JOINT_LAP_M
    return [mb.build(colls['ARCH_Paving'], matrix=Matrix.Identity(4))]


# --------------------------------------------------------------------------- #
def build_paving(colls, rng, summary):
    objs = []
    stats = {'bays': 0, 'special': 0, 'sawn': 0, 'm2': 0.0}

    def acc(s):
        for k in stats:
            stats[k] += s[k]

    def clearance(cx, cy):
        return np.minimum(clear_c(cx, cy), _fc_clearance(cx, cy))

    # ---- paddock: the big field, 580 x 74.5 m ------------------------------
    mb = MB("ARCH_Paving_Paddock")
    acc(_paving_region(mb, rng, PLAT_RECTS['paddock'], 5.0, 6.0, "A_ConcSlab",
                       "paddock", drains=(58.0, 88.0), ducts=((45.6, 0.62),),
                       clearance=clearance, kind='paddock'))
    objs.append(mb.build(colls['ARCH_Paving']))

    # ---- pit lane: the contract's rect, sawn back off the pit-wall footing --
    mb = MB("ARCH_Paving_PitLane")
    acc(_paving_region(mb, rng, PLAT_RECTS['pit_lane'], 4.0, 3.0, "A_ConcSlab",
                       "pitlane", drains=(12.9,), ducts=((22.9, 0.50),),
                       clearance=clearance, kind='pit'))
    objs.append(mb.build(colls['ARCH_Paving']))

    # ---- the paddock face of the pit building sits on its own slab ---------
    mb = MB("ARCH_Paving_Garages")
    acc(_paving_region(mb, rng, PLAT_RECTS['garages'], 5.0, 5.667, "A_ConcSlab",
                       "garages", drains=(), ducts=(),
                       clearance=clearance, kind='pit'))
    objs.append(mb.build(colls['ARCH_Paving']))

    # ---- showroom forecourt, world-aligned sawn slabs ----------------------
    mb = MB("ARCH_Paving_Forecourt")
    fcx0 = FORECOURT['cx'] - FORECOURT['hx']
    fcx1 = FORECOURT['cx'] + FORECOURT['hx']
    fcy0 = FORECOURT['cy'] - FORECOURT['hy']
    fcy1 = FORECOURT['cy'] + FORECOURT['hy']
    # THE PAVILION FOOTPRINT IS MEASURED NOW.  It used to be an invented
    # (-19.15, 15.05, -13.15, 13.15) — 4.15 m too big to the west and 2.15 m too
    # big in y against the round-1 shell — which left an unpaved ring 4.15 m wide
    # along the back wall and 2.15 m wide down both flanks that nobody built, and
    # (with the terrain hole reaching x = 12.0) a genuinely open mouth at the
    # glass plane.  R1_SHELL/R1_RECTS are the measured plan; the bays stop 12 mm
    # off it as a construction joint and the formation slab runs on underneath.
    cw, ch = 1.5, 1.0
    nx = int(round((fcx1 - fcx0) / cw))
    ny = int(round((fcy1 - fcy0) / ch))
    bays = []
    for i in range(nx):
        for j in range(ny):
            bx0 = fcx0 + i * cw + 0.006
            bx1 = bx0 + cw - 0.012
            by0 = fcy0 + j * ch + 0.006
            by1 = by0 + ch - 0.012
            r = rng.random()
            col = (1, 1, 1, 1)
            if r < 0.05:
                col = (1.06, 1.05, 1.04, 1)
            elif r < 0.09:
                col = (0.90, 0.90, 0.89, 1)
            elif r < 0.115:
                col = (0.95, 0.96, 0.98, 1)
            bays.append((bx0, bx1, by0, by1,
                         ("A_ForecourtSlab", col, Z_BAY + rng.random() * 0.0025,
                          rng.random())))

    def fc_clear_w(x, y):
        """World-frame: the forecourt is laid to the building's grid."""
        cx, cy = WC.world_to_circuit(x, y)
        return clear_c(cx, cy)

    def fc_bay_clear(x, y):
        """... and a finished BAY also stops at the round-1 pavilion shell."""
        return np.minimum(fc_clear_w(x, y), _r1_shell_clearance(x, y))

    def fc_under_r1(x, y):
        """... while the formation slab is the part that runs UNDER it."""
        return np.minimum(fc_clear_w(x, y), -_r1_shell_clearance(x, y))

    nbay = 0
    for poly, (m, col, z, r1), whole in cut_bays(bays, fc_bay_clear, leaf=0.4,
                                                 max_split=3):
        if _poly_area(poly) < 0.01:
            continue
        mb.add([(p[0], p[1], z) for p in poly], [tuple(range(len(poly)))], m, col)
        nbay += 1
        if whole and r1 < 0.06:                # a granite sett band, one bay in 16
            mb.box((poly[0][0] + 0.05, poly[0][1] + 0.05, z),
                   (poly[2][0] - 0.05, poly[2][1] - 0.05, z + 0.004),
                   "A_ConcPrecast", (0.66, 0.66, 0.65, 1))
    # SUB-BASE.  Cut to the ribbon: an uncut box put its top at -0.010 across the
    # access ribbon, which is exactly the coplanar pair the Beat-4 scan line
    # caught (ARCH_Paving_Forecourt 10 mm under SURF_AccessRoad at world x 15+).
    #
    # CLOSED, in two levels, and this is the fix for the black slot at the glass
    # plane.  OUTSIDE the pavilion the bedding runs 12 mm under the bays, so the
    # 12 mm saw joints in a 1.5 x 1.0 m sett grid are 12 mm deep instead of
    # 290 mm.  UNDER the pavilion no bay is laid — round 1's `Floor` is the
    # finished surface and its top IS z = 0.000 — so what this module casts is the
    # FORMATION the floor sits on, at R1_FORMATION_Z = -0.100: 40 mm clear of that
    # floor's soffit, 100 mm clear of its finished level, closed on every side.
    # Before this, the corridor mouth showed 9 m coffers open to the sky.
    sb = []
    for i in range(int((fcx1 - fcx0) / 6.0) + 1):
        for j in range(int((fcy1 - fcy0) / 6.0) + 1):
            sb.append((fcx0 + i * 6.0, min(fcx1, fcx0 + (i + 1) * 6.0),
                       fcy0 + j * 6.0, min(fcy1, fcy0 + (j + 1) * 6.0), None))
    for poly, _pl, _w in cut_bays(sb, fc_bay_clear, leaf=0.5, max_split=4):
        if _poly_area(poly) < 0.02:
            continue
        mb.prism(poly, -0.30, -0.012, "A_ForecourtSlab", (0.62, 0.62, 0.61, 1))
    fm2 = 0.0
    for poly, _pl, _w in cut_bays(sb, fc_under_r1, leaf=0.5, max_split=4):
        a = _poly_area(poly)
        if a < 0.02:
            continue
        fm2 += a
        mb.prism(poly, -0.36, R1_FORMATION_Z, "A_ForecourtSlab",
                 (0.60, 0.60, 0.59, 1))
    summary['forecourt_formation_m2'] = round(fm2, 1)
    # granite edge band + slot drain around the forecourt, sawn to the ribbon
    band = []
    for (ax0, ax1, ay0, ay1) in ((fcx0 - 0.55, fcx0, fcy0 - 0.55, fcy1 + 0.55),
                                 (fcx1, fcx1 + 0.55, fcy0 - 0.55, fcy1 + 0.55),
                                 (fcx0, fcx1, fcy0 - 0.55, fcy0),
                                 (fcx0, fcx1, fcy1, fcy1 + 0.55)):
        nseg_ = max(1, int(math.ceil(max(ax1 - ax0, ay1 - ay0) / 1.1)))
        for q in range(nseg_):
            if (ax1 - ax0) >= (ay1 - ay0):
                band.append((ax0 + (ax1 - ax0) * q / nseg_,
                             ax0 + (ax1 - ax0) * (q + 1) / nseg_,
                             ay0, ay1, None))
            else:
                band.append((ax0, ax1, ay0 + (ay1 - ay0) * q / nseg_,
                             ay0 + (ay1 - ay0) * (q + 1) / nseg_, None))
    for poly, _pl, _w in cut_bays(band, fc_clear_w, leaf=0.4, max_split=3):
        if _poly_area(poly) < 0.01:
            continue
        mb.prism(poly, -0.28, 0.008, "A_ConcPrecast", (0.62, 0.62, 0.60, 1))
    # bollard line protecting the glass frontage (world x = +19.5)
    nb = 0
    for k in range(9):
        by = -18.0 + k * 4.5
        if abs(by) < 6.0:
            continue                      # the launch corridor stays clear
        if clear_c(*WC.world_to_circuit(19.5, by))[0] <= 0.35:
            continue                      # ... and so does the access ribbon
        zg = sit_w(19.5, by)
        h = 0.95 + rng.uniform(-0.06, 0.06)
        lean = rng.uniform(-1.2, 1.2)
        mb.cyl((19.5, by, zg - EMBED),
               (19.5 + math.sin(math.radians(lean)) * h, by, zg + h),
               0.09, "A_Alu", (1, 1, 1, 1), n=12)
        mb.cyl((19.5, by, zg + h - 0.06), (19.5, by, zg + h + 0.01), 0.10,
               "A_Alu", (1, 1, 1, 1), n=12)
        nb += 1
    objs.append(mb.build(colls['ARCH_Paving'], matrix=Matrix.Identity(4)))

    # ---- the retaining edge along every corridor rim we abut ---------------
    mb = MB("ARCH_RetainEdge")
    rs = {'m': 0.0}
    ss = np.arange(0.0, WC.LAP, 1.0)
    for side in (+1, -1):
        e = WC.platform_edge(ss, side)
        w = WC.su_to_world(ss, e * side)
        cx, cy = WC.world_to_circuit(w[:, 0], w[:, 1])
        # is the ground just OUTBOARD of the rim ours?
        eo = e + 0.30
        wo = WC.su_to_world(ss, eo * side)
        ox, oy = WC.world_to_circuit(wo[:, 0], wo[:, 1])
        own = np.zeros(len(ss), bool)
        for rect in PLAT_RECTS.values():
            own |= in_rect(ox, oy, rect)
        own &= _fc_clearance(ox, oy) > 0.0
        # DEFECT #46, SECOND OBJECT — and the worse of the two.  The corridor rim
        # CROSSES the Beat-4 transit lane: C.platform_edge(s, +1) runs 30.92 m at
        # s = 3400 and 12.28 m at s = 3429 while the car crosses those same
        # stations at u = 26.0 and 15.9, so from s ~= 3405 east the rim lies
        # INBOARD of the driven route.  This edge beam stood 1.198 m inside the
        # car's swept volume at world (138.431, 27.140) with the car at 203 km/h —
        # deeper than ARCH_PitWall's 1.067 m.  `_fc_clearance` (the showroom
        # forecourt) was the ONLY keep-out this loop applied; nothing knew about
        # the transit lane.  The contract states it now, once, for every module
        # that stands something on a rim.
        own &= np.asarray(WC.rim_buildable(ss, side), bool)
        run = []
        for i, ok in enumerate(own):
            if ok:
                run.append(ss[i])
            elif len(run) > 2:
                _retain_run(mb, rng, run, side, "rim", rs)
                run = []
            else:
                run = []
        if len(run) > 2:
            _retain_run(mb, rng, run, side, "rim", rs)
    # ---- and the closed skirt where the platform abuts terrain -------------
    px0, px1, py0, py1 = PLAT_RECTS['paddock']
    ax0, ax1, ay0, ay1 = PLAT_RECTS['apron']
    for (a, b, inward) in (((px0, py0), (px0, py1), (1.0, 0.0)),
                           ((px0, py1), (px1, py1), (0.0, -1.0)),
                           ((px1, py1), (px1, py0 + 0.5), (-1.0, 0.0)),
                           ((ax0, ay0 + 12.0), (ax0, ay1), (1.0, 0.0))):
        _terrain_skirt(mb, rng, a, b, inward, "plat")
    objs.append(mb.build(colls['ARCH_Paving']))
    summary['retain_edge_m'] = round(rs['m'], 1)

    summary['paving_bays'] = stats['bays'] + nbay
    summary['paving_sawn'] = stats['sawn']
    summary['paving_special'] = stats['special']
    summary['paving_m2'] = round(stats['m2'], 1)
    summary['forecourt_bollards'] = nb
    return [o for o in objs if o]

# --------------------------------------------------------------------------- #
#  2. GROUND MARKINGS                                                          #
# --------------------------------------------------------------------------- #
# Every marking is broken into <= SEG_M pieces and each piece is tested against
# the contract before it is laid.  build_surface owns the markings on the racing
# surface, on the painted verge and on the access ribbon; the old build painted
# give-way triangles at circuit y = 8.4 (inside verge_edge = 10.5) and painted
# the transit route's own chevrons and PIT EXIT legend straight onto
# SURF_AccessRoad.  Both are gone.  _owned() is why they cannot come back.
SEG_M = 3.5
_MARK_DROPPED = [0]


def _owned(pts, pad=0.12, forecourt=True):
    """True for each (x, y) circuit-frame point architecture may paint."""
    A = np.asarray(pts, float).reshape(-1, 2)
    ok = clear_c(A[:, 0], A[:, 1]) > pad
    if forecourt:
        ok &= _fc_clearance(A[:, 0], A[:, 1]) > pad
    inr = np.zeros(len(A), bool)
    for rect in PLAT_RECTS.values():
        inr |= in_rect(A[:, 0], A[:, 1], rect, inset=pad)
    return ok & inr


def _stripe(mb, x0, x1, y0, y1, mat, z=MARK_Z, col=(1, 1, 1, 1)):
    """Segmented painted stripe.  A segment is laid only if all FOUR of its
    corners are architecture's ground — testing the centre alone let 334 faces
    through onto build_barriers' runoff platform in the first contract gate."""
    L = max(x1 - x0, y1 - y0)
    n = max(1, int(math.ceil(L / SEG_M)))
    along_x = (x1 - x0) >= (y1 - y0)
    segs = []
    for k in range(n):
        t0, t1 = k / n, (k + 1) / n
        if along_x:
            segs.append((x0 + (x1 - x0) * t0, x0 + (x1 - x0) * t1, y0, y1))
        else:
            segs.append((x0, x1, y0 + (y1 - y0) * t0, y0 + (y1 - y0) * t1))
    pts = []
    for (a, b, c, d) in segs:
        pts += [(a, c), (b, c), (b, d), (a, d)]
    ok = _owned(pts).reshape(-1, 4).all(axis=1)
    for (a, b, c, d), o in zip(segs, ok):
        if not o:
            _MARK_DROPPED[0] += 1
            continue
        _bay(mb, a, b, c, d, z, mat, col)


def _hatch(mb, x0, x1, y0, y1, mat, pitch=1.4, wide=0.45, ang=45.0, z=MARK_Z):
    """Diagonal hatched box, clipped to the box - used for keep-clear zones."""
    t = math.tan(math.radians(ang))
    span = (x1 - x0) + (y1 - y0) * t
    n = int(span / pitch) + 2
    polys = []
    for k in range(n):
        bx = x0 - (y1 - y0) * t + k * pitch
        poly = [(bx, y0), (bx + wide, y0), (bx + wide + (y1 - y0) * t, y1),
                (bx + (y1 - y0) * t, y1)]
        for (a, b, c) in ((-1, 0, x0), (1, 0, -x1)):
            poly = clip_half(poly, a, b, c, True)
        if len(poly) >= 3:
            polys.append(poly)
    if not polys:
        return
    keep = []
    pts = []
    for q in polys:
        pts += list(q)
        keep.append(len(q))
    ok = _owned(pts)
    i = 0
    for poly, k in zip(polys, keep):
        good = bool(ok[i:i + k].all())
        i += k
        if not good:
            _MARK_DROPPED[0] += 1
            continue
        mb.add([(p[0], p[1], z) for p in poly], [tuple(range(len(poly)))], mat)


def _legend(mb, body, x, y, rotz, size, mat, col=(1, 1, 1, 1), z=MARK_Z):
    """Painted text, laid only if the whole glyph box is architecture's ground."""
    r = size * (0.75 * len(body) + 1.0)
    box = [(x + dx, y + dy) for dx in (-r, 0.0, r) for dy in (-r, 0.0, r)]
    if not _owned(box, pad=0.05).all():
        _MARK_DROPPED[0] += 1
        return
    mb.text(body, T(x, y, z) @ Rz(rotz), size, mat, col, extrude=0.0)


def build_markings(colls, rng, garages, summary):
    mb = MB("ARCH_Markings")
    _MARK_DROPPED[0] = 0
    W, WW, Y, R, B = ("A_PaintWhite", "A_PaintWhiteWorn", "A_PaintYellow",
                      "A_PaintRed", "A_PaintBlue")
    PLX0, PLX1, PLY0, PLY1 = PLAT_RECTS['pit_lane']       # -245..130, 11.5..23.5
    # --- pit lane -----------------------------------------------------------
    # fast lane / working lane divider, broken where the boxes are
    _stripe(mb, -240.0, 128.0, 15.28, 15.43, W)
    _stripe(mb, -240.0, 128.0, 15.55, 15.70, W)
    # speed limit control lines
    for x, mat in ((-236.0, W), (118.0, W)):
        _stripe(mb, x, x + 0.30, 12.4, 23.3, mat)
    _legend(mb, "80", -228.0, 19.4, -90, 3.4, Y)
    _legend(mb, "PIT LANE LIMIT", -215.0, 19.4, -90, 1.5, WW)
    _legend(mb, "END LIMIT", 124.0, 19.4, -90, 1.5, WW)
    # the pit wall edge line: yellow, hard against the footing, worn through
    for k in range(int((PLX1 - PLX0) / 6.0)):
        px = PLX0 + k * 6.0
        if rng.random() < 0.13:
            continue                                # scrubbed off by traffic
        _stripe(mb, px + 0.2, px + 5.8, 12.30, 12.44,
                Y if rng.random() > 0.35 else WW)
    # per garage: pit box, bay number, and a different state of wear each
    for g in garages:
        bx, bw, num, name = g['x'], g['dw'], g['num'], g['team']
        mat = W if g['box_wear'] < 0.5 else WW
        x0, x1 = bx - bw * 0.5 - 0.6, bx + bw * 0.5 + 0.6
        for (a, b) in ((12.75, 12.90), (15.95, 16.10)):
            _stripe(mb, x0, x1, a, b, mat)
        for a in (x0, x1 - 0.15):
            _stripe(mb, a, a + 0.15, 12.75, 16.10, mat)
        _legend(mb, str(num), bx, 14.4, -90, 1.9, mat)
        if g['tidy'] > 0.55:
            _legend(mb, name, bx, 17.2, -90, 0.85, WW)
        if g['tidy'] < 0.35:      # working-lane cross hatch, untidy boxes only
            _hatch(mb, bx - bw * 0.4, bx + bw * 0.4, 16.4, 17.6, Y, 1.2, 0.35)
        # equipment footprint outlines: where the gun trolleys and jacks live
        if g['tidy'] > 0.4:
            for j, (ox, oy, ow, oh) in enumerate(((-2.6, 17.9, 1.5, 0.9),
                                                  (2.4, 17.9, 1.5, 0.9),
                                                  (0.0, 19.6, 2.4, 1.1))):
                if (j + num) % 3 == 0:
                    continue
                for (a, b, c, d) in ((bx + ox - ow / 2, bx + ox + ow / 2,
                                      oy - oh / 2, oy - oh / 2 + 0.08),
                                     (bx + ox - ow / 2, bx + ox + ow / 2,
                                      oy + oh / 2 - 0.08, oy + oh / 2),
                                     (bx + ox - ow / 2, bx + ox - ow / 2 + 0.08,
                                      oy - oh / 2, oy + oh / 2),
                                     (bx + ox + ow / 2 - 0.08, bx + ox + ow / 2,
                                      oy - oh / 2, oy + oh / 2)):
                    _stripe(mb, a, b, c, d, Y if j == 2 else WW)
    # walkway along the garage frontage
    _stripe(mb, -243.0, 74.0, 22.75, 22.90, Y)
    _hatch(mb, -243.0, 74.0, 22.90, 23.45, Y, 2.2, 0.5, 60.0)
    # pedestrian crossings from the wall stands to the garages
    for cx0 in (-196.0, -72.0, 52.0):
        for k in range(7):
            _stripe(mb, cx0 + k * 0.85, cx0 + k * 0.85 + 0.48, 12.9, 15.1, W)
    # pit entry (east) and pit exit (west) blends
    _hatch(mb, 96.0, 128.0, 12.4, 15.2, R, 2.0, 0.6, 55.0)
    _stripe(mb, -244.0, -150.0, 12.55, 12.73, B)
    _legend(mb, "PIT EXIT", -200.0, 13.6, -90, 1.6, B)
    _legend(mb, "SORTIE", -186.0, 13.6, -90, 1.1, B)
    # --- pit-exit apron: the keep-clear the marshals stand behind -----------
    _hatch(mb, -330.0, -318.0, 30.0, 42.0, Y, 2.0, 0.5, 40.0)
    _hatch(mb, -300.0, -288.0, 26.0, 38.0, Y, 2.0, 0.5, 40.0)
    # --- paddock ------------------------------------------------------------
    # transporter parking bays, numbered, two banks with different bay sizes
    for bank, (by0, by1, bw, n0) in enumerate(((93.0, 111.0, 4.2, 1),
                                               (62.0, 74.0, 3.6, 21))):
        nbank = 28 if bank == 0 else 18
        for k in range(nbank):
            bx = -300.0 + k * bw
            if bank == 1 and -155.0 < bx < 70.0:
                continue                       # hospitality units stand here
            m = W if rng.random() > 0.25 else WW
            _stripe(mb, bx, bx + 0.14, by0, by1, m)
            if k % 3 == 0:
                _legend(mb, str(n0 + k), bx + bw * 0.5, by0 + 1.4, -90, 0.9, m)
        _stripe(mb, -300.0, -300.0 + bw * nbank, by1 - 0.14, by1, W)
    # the paddock service road: edge lines, centre dashes, arrows, roundels
    # The service road is a CAMBERED ASPHALT OVERLAY, not the platform: its
    # crown is +70 mm and its channel +6 mm.  Painting its markings at the
    # platform's MARK_Z put them 0.5 mm under their own road at the kerb line.
    RY, RHW = SERVICE_RD_Y, SERVICE_RD_HW
    mbp, mb = mb, MB("ARCH_RoadMarkings")     # laid on the road, not the platform
    def _rz(y):
        return APRON_Z + 0.078 - 0.016 * abs(y - RY) + 0.0035
    for sgn in (-1, 1):
        yy = RY + sgn * 4.0
        _stripe(mb, -430.0, 92.0, yy - 0.07, yy + 0.07, W, z=_rz(yy))
    for k in range(int(522.0 / 8.0)):
        dx = -430.0 + k * 8.0
        _stripe(mb, dx, dx + 3.4, RY - 0.06, RY + 0.06,
                W if (k % 5) else WW, z=_rz(RY))
    for k, ax in enumerate((-380.0, -250.0, -120.0, 10.0)):
        for j in range(9):                      # a painted direction arrow
            wdt = 0.30 + 0.16 * j
            _stripe(mb, ax + j * 0.28, ax + j * 0.28 + 0.24,
                    RY + 2.0 - wdt, RY + 2.0 + wdt, WW, z=_rz(RY + 2.0))
        _legend(mb, "20", ax + 6.0, RY + 2.0, 0, 1.7, WW, z=_rz(RY + 2.0))
    road_obj = mb.build(colls['ARCH_Paving'])
    mb = mbp
    # fire lane + pedestrian route
    _hatch(mb, -300.0, 60.0, 88.6, 90.4, R, 3.0, 0.7, 65.0)
    _stripe(mb, -300.0, 60.0, 88.4, 88.6, W)
    _stripe(mb, -300.0, 60.0, 90.4, 90.6, W)
    _legend(mb, "FIRE LANE  KEEP CLEAR", -180.0, 89.5, 0, 1.25, R)
    _legend(mb, "FIRE LANE  KEEP CLEAR", -40.0, 89.5, 0, 1.25, R)
    # hospitality frontage: a painted apron edge and unit numbers
    for i, x0 in enumerate((-155.0, -118.0, -72.0, -28.0, 18.0)):
        _stripe(mb, x0, x0 + 30.0, 64.6, 64.74, WW)
        _legend(mb, "UNIT %d" % (i + 1), x0 + 15.0, 63.4, 0, 1.0, WW)
    # helipad by the medical centre
    hx, hy = -178.0, 100.0
    ring = []
    for k in range(48):
        a0 = 2 * math.pi * k / 48
        a1 = 2 * math.pi * (k + 1) / 48
        r0, r1 = 8.4, 9.0
        ring.append([(hx + r0 * math.cos(a0), hy + r0 * math.sin(a0)),
                     (hx + r1 * math.cos(a0), hy + r1 * math.sin(a0)),
                     (hx + r1 * math.cos(a1), hy + r1 * math.sin(a1)),
                     (hx + r0 * math.cos(a1), hy + r0 * math.sin(a1))])
    cen = [(sum(p[0] for p in q) / 4.0, sum(p[1] for p in q) / 4.0) for q in ring]
    for q, o in zip(ring, _owned(cen)):
        if o:
            mb.add([(p[0], p[1], MARK_Z) for p in q], [(0, 1, 2, 3)], W)
    _legend(mb, "H", hx, hy, 0, 7.0, W)
    summary['marking_faces'] = len(mb.f)
    summary['marking_dropped'] = _MARK_DROPPED[0]
    return [o for o in (mb.build(colls['ARCH_Paving']), road_obj) if o]




# --------------------------------------------------------------------------- #
#  2b. PADDOCK GROUND  —  the ground-level pass the aerial was missing         #
# --------------------------------------------------------------------------- #
# 44 000 m2 of concrete with nothing standing on it reads as a toy block from
# 240 m.  What makes a paddock read as a paddock is not the buildings; it is the
# stuff that lives between them: the service road and its kerbs, the hardcore
# compound, the fence lines, the cable ramps, the skips, the road cases, the
# light masts, the water tanks and the twenty other things that are only there
# because a race is happening.  All of it is generated, none of it is one asset
# spammed: every family below draws its dimensions, colour, wear, lean and
# contents from its own seeded stream, and every foot is placed on
# C.world_ground_z.
#
# KEEP-OUTS are the buildings and marked zones this module has already committed
# to, in the circuit frame.  Anything placed here is rejected against them AND
# against the contract (clear_c), so a bin can never end up on the racing surface
# or in the access ribbon.
KEEPOUT = [
    (-247.0,   77.0,  21.5,  42.5),      # pit building + its frontage
    (-154.0,  -88.0,  41.0,  64.0),      # media centre
    (-209.0, -168.0,  44.0,  66.0),      # medical centre
    (-159.0,   66.0,  63.0,  89.0),      # hospitality row
    (   6.0,   64.0,  89.0, 114.0),      # paddock club marquee
    (-248.0, -203.0,  95.0, 109.0),      # service compound
    (-303.0, -178.0,  90.0, 113.0),      # transporter bank 0
    (-298.0, -228.0,  57.0,  77.0),      # transporter bank 1
    (-470.0,  100.0,  75.4,  84.6),      # service road
    (-303.0,   62.0,  87.9,  91.1),      # fire lane
    (-190.0, -166.0,  88.0, 112.0),      # helipad
]
SERVICE_RD_Y = 80.0
SERVICE_RD_HW = 4.0


def _free(cx, cy, pad=0.6):
    """True where a loose object may stand: architecture's ground, clear of the
    contract's road programme AND of everything this module has committed to."""
    A = np.stack([np.asarray(cx, float).ravel(), np.asarray(cy, float).ravel()], 1)
    ok = _owned(A, pad=pad)
    for (x0, x1, y0, y1) in KEEPOUT:
        ok &= ~((A[:, 0] > x0 - pad) & (A[:, 0] < x1 + pad) &
                (A[:, 1] > y0 - pad) & (A[:, 1] < y1 + pad))
    return ok


def _scatter(rng, rect, n, pad=0.9, tries=14):
    """n accepted circuit-frame points inside `rect`, spread by rejection."""
    x0, x1, y0, y1 = rect
    out = []
    for _ in range(tries):
        if len(out) >= n:
            break
        m = (n - len(out)) * 6
        px = np.array([rng.uniform(x0, x1) for _ in range(m)])
        py = np.array([rng.uniform(y0, y1) for _ in range(m)])
        ok = _free(px, py, pad)
        for i in range(m):
            if not ok[i]:
                continue
            if any((px[i] - a) ** 2 + (py[i] - b) ** 2 < (pad * 2.4) ** 2
                   for a, b in out):
                continue
            out.append((float(px[i]), float(py[i])))
            if len(out) >= n:
                break
    return out


# ------------------------------------------------------------------ furniture
def _skip(mb, rng, x, y, ang):
    """Builder's skip.  Length, taper, contents and dent pattern all vary."""
    L = rng.uniform(3.0, 4.4)
    W = rng.uniform(1.65, 1.95)
    H = rng.uniform(1.05, 1.42)
    tap = rng.uniform(0.22, 0.48)
    col = jitter_col(srgb(rng.choice(('#8a4a1c', '#2f5f3a', '#5a5f66',
                                      '#7a2a24', '#1f4460'))), rng, 0.02, 0.18)
    m0 = T(x, y, 0.0) @ Rz(ang)
    base = [(-L / 2, -W / 2), (L / 2, -W / 2), (L / 2, W / 2), (-L / 2, W / 2)]
    top = [(-L / 2 - tap, -W / 2 - 0.06), (L / 2 + tap, -W / 2 - 0.06),
           (L / 2 + tap, W / 2 + 0.06), (-L / 2 - tap, W / 2 + 0.06)]
    V = [tuple(m0 @ Vector((p[0], p[1], 0.18))) for p in base] + \
        [tuple(m0 @ Vector((p[0], p[1], 0.18 + H))) for p in top]
    mb.add(V, [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)],
           "A_RustSteel", col)
    mb.add(V, [(0, 3, 2, 1)], "A_RustSteel", (col[0] * .6, col[1] * .6, col[2] * .6, 1))
    for k in range(3):                     # rolled top rail + rubbing strips
        mb.xbox(m0 @ T(0, 0, 0.30 + k * (H - 0.12) / 3.0),
                (L + 0.02 + tap * k * 0.5, W + 0.10, 0.055), "A_RustSteel",
                (col[0] * .85, col[1] * .85, col[2] * .85, 1))
    for sx in (-1, 1):                     # lifting lugs and wheels
        mb.xbox(m0 @ T(sx * L * 0.30, 0, 0.14), (0.10, W + 0.16, 0.22),
                "A_SteelPaint", srgb('#3b3f43'))
        mb.cyl(tuple(m0 @ Vector((sx * L * 0.36, -W / 2 - 0.04, 0.11))),
               tuple(m0 @ Vector((sx * L * 0.36, -W / 2 - 0.14, 0.11))), 0.11,
               "A_Rubber", (1, 1, 1, 1), n=10)
    fill = rng.random()
    if fill > 0.3:                          # contents, heaped above the rim
        for k in range(rng.randint(5, 16)):
            mm = m0 @ T(rng.uniform(-L / 2 + 0.4, L / 2 - 0.4),
                        rng.uniform(-W / 2 + 0.3, W / 2 - 0.3),
                        0.18 + H * rng.uniform(0.55, 1.05)) \
                @ Rz(rng.uniform(0, 180)) @ Ry(rng.uniform(-40, 40))
            mat, cc = rng.choice((("A_Timber", (1, 1, 1, 1)),
                                  ("A_Plastic", jitter_col(srgb('#b8bcbf'), rng,
                                                           0.05, 0.3)),
                                  ("A_ConcPrecast", (0.85, 0.85, 0.84, 1)),
                                  ("A_Tarp", jitter_col(srgb('#4a5a66'), rng,
                                                        0.04, 0.25))))
            mb.xbox(mm, (rng.uniform(0.3, 1.1), rng.uniform(0.2, 0.7),
                         rng.uniform(0.08, 0.4)), mat, cc)


def _roadcase(mb, rng, x, y, ang, z0=0.0):
    """Flight case.  Height, hardware count, lid state and livery all vary."""
    L = rng.uniform(0.75, 1.45)
    W = rng.uniform(0.55, 0.85)
    H = rng.uniform(0.55, 1.15)
    m0 = T(x, y, z0) @ Rz(ang)
    body = jitter_col(srgb(rng.choice(('#1b1d20', '#20323f', '#2c2620',
                                       '#3a3f43'))), rng, 0.02, 0.15)
    mb.xbox(m0 @ T(0, 0, 0.055 + H / 2), (L, W, H), "A_Plastic", body)
    for sz in (0.055, 0.055 + H):          # extruded edge trim
        mb.xbox(m0 @ T(0, 0, sz), (L + 0.03, W + 0.03, 0.045), "A_Alu",
                (0.72, 0.72, 0.72, 1))
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.cyl(tuple(m0 @ Vector((sx * (L / 2 - 0.09), sy * (W / 2 - 0.09),
                                      0.055))),
                   tuple(m0 @ Vector((sx * (L / 2 - 0.09), sy * (W / 2 - 0.09),
                                      0.0))), 0.052, "A_Plastic",
                   (0.12, 0.12, 0.13, 1), n=8)
            mb.xbox(m0 @ T(sx * (L / 2 - 0.10), sy * (W / 2 - 0.10),
                           0.055 + H), (0.11, 0.11, 0.05), "A_Alu",
                    (0.7, 0.7, 0.7, 1))
    if rng.random() < 0.55:                # a stencilled team panel
        mb.xbox(m0 @ T(0, W / 2 + 0.005, 0.055 + H * 0.62),
                (L * 0.7, 0.012, H * 0.28), "A_Sign",
                jitter_col(srgb(TEAMS[rng.randrange(14)][1]), rng, 0.02, 0.15))
    return H + 0.055


def _bin_(mb, rng, x, y, ang):
    """Wheelie bin.  Four sizes, lid open or shut, always slightly out of line."""
    W = rng.choice((0.58, 0.66, 0.74, 0.94))
    D = W * rng.uniform(0.72, 0.90)
    H = W * rng.uniform(1.45, 1.75)
    m0 = T(x, y, 0.0) @ Rz(ang) @ Rx(rng.uniform(-1.5, 1.5))
    col = jitter_col(srgb(rng.choice(('#20402a', '#1f3a58', '#5a1f22',
                                      '#3a3d40', '#6a5a1c'))), rng, 0.02, 0.18)
    mb.xbox(m0 @ T(0, 0, 0.09 + H / 2), (W, D, H), "A_Plastic", col)
    lid = rng.random() < 0.28
    if lid:
        mb.xbox(m0 @ T(0, -D * 0.62, 0.09 + H + 0.30) @ Rx(-72),
                (W + 0.02, D + 0.02, 0.06), "A_Plastic", col)
    else:
        mb.xbox(m0 @ T(0, 0, 0.09 + H + 0.03), (W + 0.02, D + 0.02, 0.06),
                "A_Plastic", col)
    for sx in (-1, 1):
        mb.cyl(tuple(m0 @ Vector((sx * (W / 2 - 0.07), D * 0.34, 0.09))),
               tuple(m0 @ Vector((sx * (W / 2 - 0.07), D * 0.34, 0.0))), 0.085,
               "A_Rubber", (1, 1, 1, 1), n=10)


def _pallet_stack(mb, rng, x, y, ang):
    n = rng.randint(2, 9)
    m0 = T(x, y, 0.0) @ Rz(ang)
    for k in range(n):
        z = k * 0.145
        dx = rng.uniform(-0.05, 0.05)
        dy = rng.uniform(-0.05, 0.05)
        da = rng.uniform(-4.0, 4.0)
        mm = m0 @ T(dx, dy, z) @ Rz(da)
        for j in range(3):                 # bearers
            mb.xbox(mm @ T(0, -0.4 + j * 0.4, 0.035), (1.2, 0.10, 0.07),
                    "A_Timber", jitter_col(srgb('#9c7f57'), rng, 0.02, 0.18))
        for j in range(5):                 # deck boards
            mb.xbox(mm @ T(-0.5 + j * 0.25, 0, 0.105), (0.11, 0.8, 0.018),
                    "A_Timber", jitter_col(srgb('#a88b62'), rng, 0.02, 0.2))
    if rng.random() < 0.35:                # shrink-wrapped load on top
        mb.xbox(m0 @ T(0, 0, n * 0.145 + 0.32), (1.1, 0.75, 0.62), "A_Tarp",
                jitter_col(srgb('#9fb0b8'), rng, 0.03, 0.2))


def _gascage(mb, rng, x, y, ang):
    m0 = T(x, y, 0.0) @ Rz(ang)
    W, D, H = rng.uniform(1.5, 2.4), rng.uniform(0.9, 1.3), 1.85
    for (a, b, c, d) in ((-W / 2, -D / 2, W / 2, -D / 2), (-W / 2, D / 2, W / 2, D / 2),
                         (-W / 2, -D / 2, -W / 2, D / 2), (W / 2, -D / 2, W / 2, D / 2)):
        p0 = m0 @ Vector((a, b, 0.02))
        p1 = m0 @ Vector((c, d, 0.02))
        mb.add([tuple(p0), tuple(p1), tuple(p1 + Vector((0, 0, H))),
                tuple(p0 + Vector((0, 0, H)))], [(0, 1, 2, 3)], "A_MeshScreen",
               (1, 1, 1, 1))
        for pp in (p0, p1):
            mb.cyl(tuple(pp), tuple(pp + Vector((0, 0, H))), 0.035, "A_SteelGalv",
                   (1, 1, 1, 1), n=6)
    nb = int(W / 0.31)
    for k in range(nb):
        for j in range(2):
            if rng.random() < 0.22:
                continue
            cc = srgb(rng.choice(('#2b4a7a', '#7a2a24', '#2a5a32', '#6a6a2a',
                                 '#54585c')))
            cx = -W / 2 + 0.16 + k * 0.31
            cy = -D / 2 + 0.28 + j * (D - 0.56)
            mb.cyl(tuple(m0 @ Vector((cx, cy, 0.02))),
                   tuple(m0 @ Vector((cx, cy, 1.32))), 0.145, "A_SteelPaint",
                   cc, n=12)
            mb.cyl(tuple(m0 @ Vector((cx, cy, 1.32))),
                   tuple(m0 @ Vector((cx, cy, 1.46))), 0.055, "A_Alu",
                   (0.7, 0.7, 0.7, 1), n=8)
    mb.xbox(m0 @ T(0, 0, H + 0.05), (W + 0.1, D + 0.1, 0.06), "A_RoofSeam",
            (1, 1, 1, 1))


def _watertank(mb, rng, x, y):
    r = rng.uniform(0.85, 1.45)
    h = rng.uniform(1.6, 2.6)
    m0 = T(x, y, 0.0)
    mb.cyl((x, y, 0.06), (x, y, 0.06 + h), r, "A_Plastic",
           jitter_col(srgb('#3a4a52'), rng, 0.02, 0.18), n=18)
    mb.cyl((x, y, 0.06 + h), (x, y, 0.10 + h), r * 0.98, "A_Plastic",
           jitter_col(srgb('#2f3d44'), rng, 0.02, 0.18), n=18)
    mb.cyl((x, y, 0.10 + h), (x, y, 0.20 + h), r * 0.22, "A_Plastic",
           (0.4, 0.4, 0.4, 1), n=10)
    for k in range(3):                     # bands
        mb.cyl((x, y, 0.4 + k * h * 0.30), (x, y, 0.44 + k * h * 0.30), r + 0.02,
               "A_SteelGalv", (0.7, 0.7, 0.7, 1), n=18)
    mb.box((x - r - 0.1, y - r - 0.1, 0.0), (x + r + 0.1, y + r + 0.1, 0.06),
           "A_Timber", (0.8, 0.8, 0.78, 1))


def _genset(mb, rng, x, y, ang):
    L, W, H = rng.uniform(2.2, 4.6), rng.uniform(1.1, 1.6), rng.uniform(1.4, 2.2)
    m0 = T(x, y, 0.0) @ Rz(ang)
    col = jitter_col(srgb(rng.choice(('#c8b41c', '#d0d3d6', '#2f5f8a',
                                      '#8a9096'))), rng, 0.02, 0.15)
    mb.xbox(m0 @ T(0, 0, 0.16 + H / 2), (L, W, H), "A_SteelPaint", col)
    mb.xbox(m0 @ T(0, 0, 0.08), (L + 0.12, W + 0.12, 0.16), "A_SteelPaint",
            srgb('#33363a'))
    for k in range(int(L / 0.22)):         # louvre bank
        mb.xbox(m0 @ T(-L / 2 + 0.14 + k * 0.22, W / 2 + 0.01,
                       0.16 + H * 0.62), (0.13, 0.02, H * 0.42), "A_Alu",
                (0.62, 0.62, 0.62, 1))
    mb.cyl(tuple(m0 @ Vector((L / 2 - 0.3, 0, 0.16 + H))),
           tuple(m0 @ Vector((L / 2 - 0.3, 0, 0.16 + H + rng.uniform(0.4, 0.9)))),
           0.075, "A_RustSteel", (1, 1, 1, 1), n=10)
    if rng.random() < 0.6:                 # cable tails on the ground
        for k in range(rng.randint(2, 5)):
            a = rng.uniform(0, 360)
            r0 = rng.uniform(1.2, 3.4)
            p0 = m0 @ Vector((-L / 2 - 0.1, rng.uniform(-W / 3, W / 3), 0.18))
            p1 = Vector((float(p0.x) + math.cos(math.radians(a)) * r0,
                         float(p0.y) + math.sin(math.radians(a)) * r0, 0.03))
            mb.cyl(tuple(p0), tuple(p1), rng.uniform(0.018, 0.036), "A_Rubber",
                   (1, 1, 1, 1), n=6)


def _cablereel(mb, rng, x, y, ang):
    r = rng.uniform(0.45, 0.95)
    w = rng.uniform(0.35, 0.7)
    m0 = T(x, y, r) @ Rz(ang) @ Rx(90)
    if rng.random() < 0.45:                # laid flat
        m0 = T(x, y, w * 0.5) @ Rz(ang)
    for sz in (-w / 2, w / 2):
        mb.revolve([(0.06, sz), (r, sz), (r, sz + 0.04 * (1 if sz < 0 else -1)),
                    (0.06, sz + 0.04 * (1 if sz < 0 else -1))], m0, "A_Timber",
                   jitter_col(srgb('#8f7550'), rng, 0.02, 0.2), n=16)
    mb.revolve([(r * 0.55, -w / 2 + 0.04), (r * 0.55, w / 2 - 0.04)], m0,
               "A_Rubber", (1, 1, 1, 1), n=16)


def _cone(mb, rng, x, y):
    h = rng.choice((0.45, 0.5, 0.75, 0.75, 1.0))
    lean = rng.uniform(0, 7.0) if rng.random() < 0.25 else 0.0
    m0 = T(x, y, 0.0) @ Rz(rng.uniform(0, 360)) @ Ry(lean)
    mb.xbox(m0 @ T(0, 0, 0.015), (h * 0.62, h * 0.62, 0.03), "A_Plastic",
            srgb('#8a2c14'))
    mb.revolve([(h * 0.30, 0.03), (h * 0.10, h * 0.62), (0.035, h)], m0,
               "A_Plastic", jitter_col(srgb('#c8471c'), rng, 0.015, 0.18), n=12)
    for k in range(2 if h > 0.6 else 1):
        zz = h * (0.40 + 0.22 * k)
        rr = h * 0.30 - (h * 0.20) * (zz / h)
        mb.revolve([(rr + 0.004, zz), (rr + 0.004, zz + h * 0.11)], m0,
                   "A_Sign", srgb('#e8e6df'), n=12)


def _jersey(mb, rng, a, b, seg=2.0):
    """A run of concrete jersey barriers: each unit is placed, not extruded."""
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    n = max(1, int(L / seg))
    for k in range(n):
        t = (k + 0.5) / n
        cx = a[0] + (b[0] - a[0]) * t
        cy = a[1] + (b[1] - a[1]) * t
        ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
        m0 = T(cx, cy, 0.0) @ Rz(ang + rng.uniform(-1.2, 1.2))
        h = rng.uniform(0.80, 0.92)
        tone = 0.86 + rng.uniform(-0.08, 0.10)
        prof = [(-0.30, 0.0), (0.30, 0.0), (0.30, 0.08), (0.12, 0.28),
                (0.075, h), (-0.075, h), (-0.12, 0.28), (-0.30, 0.08)]
        Lu = seg * 0.97
        V = [tuple(m0 @ Vector((-Lu / 2, p[0], p[1]))) for p in prof] + \
            [tuple(m0 @ Vector((Lu / 2, p[0], p[1]))) for p in prof]
        np_ = len(prof)
        F = [(i, (i + 1) % np_, np_ + (i + 1) % np_, np_ + i) for i in range(np_)]
        F.append(tuple(range(np_ - 1, -1, -1)))
        F.append(tuple(range(np_, 2 * np_)))
        mb.add(V, F, "A_ConcPrecast", (tone, tone, tone * 0.99, 1))
        if rng.random() < 0.30:
            mb.xbox(m0 @ T(0, -0.13, h * 0.62), (Lu * 0.7, 0.02, 0.22), "A_Sign",
                    jitter_col(srgb(BRANDS[k % len(BRANDS)][1]), rng, 0.02, 0.12))


def _heras(mb, rng, a, b, banner=0.35, h=2.05):
    """Temporary mesh fencing on cast feet.  Every panel leans differently and
    one in twelve is missing, which is what a real fence line looks like."""
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    n = max(1, int(L / 3.45))
    for k in range(n):
        t0, t1 = k / n, (k + 1) / n
        p0 = (a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0)
        p1 = (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1)
        if rng.random() < 0.045:
            continue                        # a panel taken away for access
        lean = rng.uniform(-2.6, 2.6)
        ux, uy = (p1[0] - p0[0]) / max(1e-6, math.hypot(p1[0] - p0[0],
                                                        p1[1] - p0[1])), 0.0
        nx, ny = -(p1[1] - p0[1]), (p1[0] - p0[0])
        nl = math.hypot(nx, ny) or 1.0
        nx, ny = nx / nl, ny / nl
        dx, dy = nx * math.tan(math.radians(lean)) * h, ny * math.tan(
            math.radians(lean)) * h
        mb.add([(p0[0], p0[1], 0.09), (p1[0], p1[1], 0.09),
                (p1[0] + dx, p1[1] + dy, h), (p0[0] + dx, p0[1] + dy, h)],
               [(0, 1, 2, 3)], "A_MeshScreen", (1, 1, 1, 1))
        for pp in (p0, p1):
            mb.cyl((pp[0], pp[1], 0.09),
                   (pp[0] + dx, pp[1] + dy, h + 0.04), 0.021, "A_SteelGalv",
                   (1, 1, 1, 1), n=6)
            # cast foot
            mb.xbox(T(pp[0], pp[1], 0.045) @ Rz(math.degrees(
                math.atan2(p1[1] - p0[1], p1[0] - p0[0]))),
                (0.30, 0.70, 0.09), "A_ConcPrecast",
                (0.80 + rng.uniform(-0.06, 0.06), 0.80, 0.79, 1))
        mb.cyl((p0[0] + dx, p0[1] + dy, h + 0.02), (p1[0] + dx, p1[1] + dy,
               h + 0.02), 0.021, "A_SteelGalv", (1, 1, 1, 1), n=6)
        if rng.random() < banner:
            nm, c1, c2 = BRANDS[(k * 7) % len(BRANDS)]
            sag = rng.uniform(0.02, 0.11)
            mb.add([(p0[0], p0[1], 0.42), (p1[0], p1[1], 0.42 - sag),
                    (p1[0] + dx * 0.8, p1[1] + dy * 0.8, h - 0.18 - sag),
                    (p0[0] + dx * 0.8, p0[1] + dy * 0.8, h - 0.18)],
                   [(0, 1, 2, 3)], "A_Sign", jitter_col(srgb(c1), rng, 0.015, 0.10))


def _lightmast(mb, rng, x, y, z0):
    h = rng.choice((11.5, 13.0, 14.5, 16.0)) + rng.uniform(-0.4, 0.4)
    nb = rng.randint(3, 6)
    mb.box((x - 0.55, y - 0.55, z0 - 0.10), (x + 0.55, y + 0.55, z0 + 0.42),
           "A_ConcPrecast", (0.86, 0.86, 0.85, 1))
    mb.cyl((x, y, z0 + 0.42), (x, y, z0 + h), 0.16, "A_SteelGalv",
           (1, 1, 1, 1), n=12, r1=0.10)
    for k in range(4):
        mb.cyl((x - 0.10, y, z0 + 1.0 + k * 0.9), (x + 0.10, y, z0 + 1.0 + k * 0.9),
               0.016, "A_SteelGalv", (1, 1, 1, 1), n=5)
    mb.box((x - 0.7, y - 0.20, z0 + h - 0.30), (x + 0.7, y + 0.20, z0 + h - 0.16),
           "A_SteelGalv", (0.66, 0.66, 0.66, 1))
    for k in range(nb):
        ax = x - 0.6 + 1.2 * (k + 0.5) / nb
        m = T(ax, y, z0 + h - 0.02) @ Rz(rng.uniform(-14, 14)) @ Rx(38.0)
        mb.xbox(m, (0.52, 0.62, 0.13), "A_Alu", (0.72, 0.72, 0.72, 1))
        mb.xbox(m @ T(0, 0, -0.075), (0.46, 0.56, 0.02), "A_Emit",
                (0.02, 0.02, 0.02, 1))
    if rng.random() < 0.5:                 # a small enclosure at the base
        mb.box((x + 0.6, y - 0.35, z0), (x + 1.0, y + 0.35, z0 + 0.95),
               "A_SteelPaint", srgb('#8d9399'))


def _fingerpost(mb, rng, x, y, z0, labels):
    h = rng.uniform(2.6, 3.2)
    mb.cyl((x, y, z0 - EMBED), (x, y, z0 + h), 0.055, "A_SteelGalv",
           (1, 1, 1, 1), n=10)
    a0 = rng.uniform(0, 360)
    for i, (txt, col) in enumerate(labels):
        zz = z0 + h - 0.28 - i * 0.30
        ang = a0 + i * rng.uniform(55, 140) * rng.choice((-1.0, 1.0))
        m = T(x, y, zz) @ Rz(ang)
        w = 0.30 + 0.145 * len(txt)          # sized to the legend, not guessed
        mb.xbox(m @ T(w * 0.5 + 0.06, 0, 0), (w, 0.028, 0.24), "A_Sign", col)
        for sy in (-1, 1):                   # legend on BOTH faces, light on dark
            # Rz(180) @ Rx(90) applies Rx first: normal +Z -> -Y -> +Y and the
            # reading direction +X -> -X, which is the +Y face.  The opposite
            # mapping renders the far side mirrored -- "TIXE TIP" in the first
            # arch_apron_rim frame.
            mb.text(txt, m @ T(w * 0.5 + 0.06, sy * 0.017, 0) @ Rz(90 + 90 * sy)
                    @ Rx(90), 0.115, "A_Sign", srgb('#f2f4f5'), extrude=0.003)
        mb.xbox(m @ T(w + 0.06, 0, 0), (0.10, 0.030, 0.26), "A_Sign",
                (col[0] * 0.55, col[1] * 0.55, col[2] * 0.55, 1))


def _firepoint(mb, rng, x, y, z0):
    mb.box((x - 0.42, y - 0.30, z0 - EMBED), (x + 0.42, y + 0.30, z0 + 0.10),
           "A_ConcPrecast", (0.84, 0.84, 0.83, 1))
    for sx in (-0.34, 0.34):
        mb.cyl((x + sx, y, z0 + 0.10), (x + sx, y, z0 + 1.55), 0.032,
               "A_SteelGalv", (1, 1, 1, 1), n=6)
    mb.box((x - 0.44, y - 0.24, z0 + 0.18), (x + 0.44, y + 0.24, z0 + 1.02),
           "A_SteelPaint", srgb('#8f1d16'))
    for k in range(rng.randint(1, 3)):
        cx = x - 0.24 + k * 0.26
        mb.cyl((cx, y, z0 + 0.24), (cx, y, z0 + 0.86), 0.075, "A_SteelPaint",
               srgb('#a02a1c'), n=12)
        mb.cyl((cx, y, z0 + 0.86), (cx, y, z0 + 0.98), 0.028, "A_Alu",
               (0.7, 0.7, 0.7, 1), n=8)
    mb.box((x - 0.30, y - 0.03, z0 + 1.08), (x + 0.30, y + 0.03, z0 + 1.52),
           "A_Sign", srgb('#9c2118'))
    mb.text("FIRE POINT", T(x, y - 0.04, z0 + 1.30) @ Rx(90), 0.10, "A_Sign",
            srgb('#f0eee8'), extrude=0.004)


def _shrub(mb, rng, x, y, z0, r_max=0.9):
    """A procedural shrub.

    The first version scattered 5-11 leaves of 0.10-0.26 m per stem over the
    whole crown volume, and at eye level in the paddock that rendered as green
    cards floating on sticks -- visible in the first contract-lit
    arch_paddock_eye frame.  A shrub is not sparse: it is a dense shell of small
    leaves on a branching skeleton.  So this builds

        3-6 primary stems, each with 2-4 secondary twigs,
        a FOLDED leaf (two triangles about a mid-rib, 12-22 deg of dihedral) so
        it catches light on one half and not the other,
        leaves 45-95 mm long, 30-70 of them per twig cluster,
        positioned on an ellipsoidal crown shell with a radial jitter, so the
        silhouette is a bush and not a cloud.

    Never the same twice, and never an imported asset."""
    nst = rng.randint(3, 6)
    h = rng.uniform(0.55, 1.35) * (r_max / 0.9)
    base = jitter_col(srgb(rng.choice(('#33501f', '#3c5a26', '#2b4a22',
                                       '#47591f', '#405c2a'))), rng, 0.02, 0.12)
    crown_r = r_max * rng.uniform(0.75, 1.0)
    for st in range(nst):
        a = rng.uniform(0, 2 * math.pi)
        rr = rng.uniform(0.0, r_max * 0.25)
        sx, sy = x + math.cos(a) * rr, y + math.sin(a) * rr
        lean = rng.uniform(0.25, 0.6)
        tipx = sx + math.cos(a) * crown_r * lean
        tipy = sy + math.sin(a) * crown_r * lean
        tipz = z0 + h * rng.uniform(0.55, 0.85)
        mb.cyl((sx, sy, z0 - 0.03), (tipx, tipy, tipz),
               rng.uniform(0.011, 0.022), "A_Bark", (1, 1, 1, 1), n=5,
               r1=rng.uniform(0.005, 0.010))
        for tw in range(rng.randint(2, 4)):
            t = rng.uniform(0.45, 1.0)
            bx = sx + (tipx - sx) * t
            by = sy + (tipy - sy) * t
            bz = z0 + (tipz - z0) * t
            ea = a + rng.uniform(-1.5, 1.5)
            el = crown_r * rng.uniform(0.25, 0.55)
            ex = bx + math.cos(ea) * el
            ey = by + math.sin(ea) * el
            ez = bz + rng.uniform(-0.05, 0.28) * h
            mb.cyl((bx, by, bz), (ex, ey, ez), rng.uniform(0.005, 0.010),
                   "A_Bark", (1, 1, 1, 1), n=4)
            nl = rng.randint(9, 18)
            for k in range(nl):
                u = rng.uniform(0.15, 1.12)
                px = bx + (ex - bx) * u + rng.uniform(-0.06, 0.06) * r_max
                py = by + (ey - by) * u + rng.uniform(-0.06, 0.06) * r_max
                pz = bz + (ez - bz) * u + rng.uniform(-0.05, 0.05) * h
                # keep the crown an ellipsoid, not a cloud
                dx, dy, dz = px - x, py - y, pz - (z0 + h * 0.55)
                q = (dx * dx + dy * dy) / max(1e-6, crown_r ** 2) + \
                    (dz * dz) / max(1e-6, (h * 0.62) ** 2)
                if q > 1.15:
                    f = 1.0 / math.sqrt(q / 1.15)
                    px, py, pz = x + dx * f, y + dy * f, z0 + h * 0.55 + dz * f
                L = rng.uniform(0.045, 0.095) * (r_max / 0.9 + 0.4)
                Wl = L * rng.uniform(0.42, 0.72)
                m = T(px, py, pz) @ Rz(rng.uniform(0, 360)) \
                    @ Ry(rng.uniform(-80, 80)) @ Rx(rng.uniform(-40, 40))
                fold = math.radians(rng.uniform(12, 22))
                c = jitter_col(base, rng, 0.025, 0.20)
                tipv = Vector((L, 0.0, 0.0))
                mid = Vector((0.0, 0.0, 0.0))
                for sgn in (-1, 1):
                    e0 = Vector((L * 0.42, sgn * Wl * 0.5,
                                 -math.sin(fold) * Wl * 0.5))
                    mb.add([tuple(m @ mid), tuple(m @ e0), tuple(m @ tipv)],
                           [(0, 1, 2)], "A_Leaf", c)


def _planter(mb, rng, x, y, z0, L, W):
    h = rng.uniform(0.52, 0.78)
    tone = 0.84 + rng.uniform(-0.06, 0.08)
    mb.box((x - L / 2, y - W / 2, z0 - EMBED), (x + L / 2, y + W / 2, z0 + h),
           "A_ConcPrecast", (tone, tone, tone * 0.99, 1))
    mb.box((x - L / 2 + 0.11, y - W / 2 + 0.11, z0 + h - 0.16),
           (x + L / 2 - 0.11, y + W / 2 - 0.11, z0 + h - 0.10), "A_Soil",
           (1, 1, 1, 1))
    n = max(1, int(L * W * rng.uniform(0.7, 1.5)))
    for k in range(n):
        _shrub(mb, rng, x + rng.uniform(-L / 2 + 0.3, L / 2 - 0.3),
               y + rng.uniform(-W / 2 + 0.25, W / 2 - 0.25), z0 + h - 0.12,
               r_max=min(W * 0.42, 0.95))


# --------------------------------------------------------------------------- #
def build_paddock_ground(colls, rng, summary):
    """The service ground: road, compound, fences, plant, furniture, lighting."""
    objs = []
    counts = {}

    # ---- 1. the service road: asphalt, kerbed, cambered, sawn to the contract
    mb = MB("ARCH_Ground_ServiceRoad")
    RY, HW = SERVICE_RD_Y, SERVICE_RD_HW
    bays = []
    for k in range(int(522.0 / 2.6)):
        bx0 = -430.0 + k * 2.6
        bays.append((bx0 + 0.02, bx0 + 2.58, RY - HW, RY + HW,
                     (rng.random(), rng.random())))

    def rd_clear(cx, cy):
        return np.minimum(clear_c(cx, cy), _fc_clearance(cx, cy))

    nseg = 0
    for poly, (r1, r2), whole in cut_bays(bays, rd_clear, leaf=0.6, max_split=3):
        if _poly_area(poly) < 0.05:
            continue
        # 1.6 % camber, laid ON the platform: the crown is +78 mm and the
        # channel +14 mm, so the asphalt is an overlay on the concrete, never
        # dips below the declared plane, and never comes within TOL of the
        # concrete's own 0-3.5 mm bay level at the kerb line
        pts = [(p[0], p[1], APRON_Z + 0.078 - 0.016 * abs(p[1] - RY))
               for p in poly]
        mb.add(pts, [tuple(range(len(poly)))], "A_Asphalt",
               (0.92 + 0.16 * r1, 0.94, 0.96, 1))
        del pts
        nseg += 1
        if r1 < 0.05 and whole:            # a reinstated trench, darker + sunk
            mb.quad((poly[0][0], RY - HW + 0.3, APRON_Z + 0.020),
                    (poly[1][0], RY - HW + 0.3, APRON_Z + 0.020),
                    (poly[1][0], RY + HW - 0.3, APRON_Z + 0.020),
                    (poly[0][0], RY + HW - 0.3, APRON_Z + 0.020),
                    "A_Asphalt", (0.62, 0.62, 0.64, 1))
    # kerbs both sides, unit by unit, with dropped crossings
    for sgn in (-1, 1):
        yy = RY + sgn * (HW + 0.075)
        k = 0
        px = -430.0
        while px < 92.0:
            L = rng.choice((0.9, 0.9, 1.2))
            drop = (k % 37) in (0, 1, 2)
            if _owned([(px + L * 0.5, yy)], pad=0.05)[0]:
                top = APRON_Z + (0.020 if drop else 0.125)
                tone = 0.82 + rng.uniform(-0.06, 0.09)
                mb.box((px, yy - 0.075, APRON_Z - 0.30),
                       (px + L - 0.01, yy + 0.075, top), "A_ConcPrecast",
                       (tone, tone, tone * 0.99, 1))
                if not drop and (k % 11) == 5:      # a gully behind the kerb
                    # RECESSED 14 mm.  Flush with the platform it sat exactly on
                    # the concrete's own bay plane -- 2 of the 3 cross-object
                    # coplanar columns the gate reported.
                    mb.box((px + 0.06, yy + sgn * 0.10, APRON_Z - 0.09),
                           (px + L - 0.06, yy + sgn * 0.42, APRON_Z - 0.014),
                           "A_SteelGalv", (0.6, 0.6, 0.58, 1))
            px += L
            k += 1
    # heavy rubber cable ramps across the road
    for k in range(7):
        rx = -400.0 + k * 72.0 + rng.uniform(-12, 12)
        if not _owned([(rx, RY)], pad=0.4)[0]:
            continue
        w = rng.uniform(0.55, 0.95)
        for j in range(int(2 * HW / 0.6)):
            yy = RY - HW + j * 0.6
            mb.add([(rx - w / 2, yy, APRON_Z + 0.02),
                    (rx + w / 2, yy, APRON_Z + 0.02),
                    (rx + w / 2, yy + 0.56, APRON_Z + 0.02),
                    (rx - w / 2, yy + 0.56, APRON_Z + 0.02)],
                   [(0, 1, 2, 3)], "A_Rubber", (1, 1, 1, 1))
            mb.add([(rx - w / 2, yy, APRON_Z + 0.02),
                    (rx - w / 2 + 0.12, yy, APRON_Z + 0.075),
                    (rx + w / 2 - 0.12, yy, APRON_Z + 0.075),
                    (rx + w / 2, yy, APRON_Z + 0.02)], [(0, 1, 2, 3)],
                   "A_Rubber", (1, 1, 1, 1))
            mb.add([(rx - w / 2 + 0.12, yy, APRON_Z + 0.075),
                    (rx + w / 2 - 0.12, yy, APRON_Z + 0.075),
                    (rx + w / 2 - 0.12, yy + 0.56, APRON_Z + 0.075),
                    (rx - w / 2 + 0.12, yy + 0.56, APRON_Z + 0.075)],
                   [(0, 1, 2, 3)], "A_Rubber",
                   (1.4, 1.2, 0.2, 1) if j % 2 else (1, 1, 1, 1))
    objs.append(mb.build(colls['ARCH_Ground']))
    counts['road_segments'] = nseg

    # ---- 2. the plant compound: crushed hardcore, fenced, full of kit -------
    mb = MB("ARCH_Ground_Compound")
    CX0, CX1, CY0, CY1 = -470.0, -400.0, 86.0, 112.0
    bays = []
    for i in range(int((CX1 - CX0) / 3.0)):
        for j in range(int((CY1 - CY0) / 3.0)):
            bays.append((CX0 + i * 3.0, CX0 + (i + 1) * 3.0,
                         CY0 + j * 3.0, CY0 + (j + 1) * 3.0, rng.random()))
    for poly, r1, whole in cut_bays(bays, _owned_clear, leaf=0.8, max_split=2):
        if _poly_area(poly) < 0.05:
            continue
        mb.add([(p[0], p[1], APRON_Z + 0.045 + 0.012 * math.sin(p[0] * 0.7)
                 + 0.010 * math.cos(p[1] * 0.9)) for p in poly],
               [tuple(range(len(poly)))], "A_Gravel",
               (0.88 + 0.24 * r1, 0.92, 0.94, 1))
    # loose stones on the surface, individually placed
    st = _scatter(rng, (CX0 + 1, CX1 - 1, CY0 + 1, CY1 - 1), 260, pad=0.05)
    for (sx, sy) in st:
        r = rng.uniform(0.035, 0.11)
        m = T(sx, sy, APRON_Z + 0.05 + r * 0.4) @ Rz(rng.uniform(0, 360)) \
            @ Rx(rng.uniform(0, 180))
        mb.xbox(m, (r * 2.2, r * 1.7, r * 1.2), "A_Gravel",
                (0.8 + rng.uniform(0, 0.5), 0.9, 0.95, 1))
    _heras(mb, rng, (CX0, CY0), (CX1, CY0), banner=0.12)
    _heras(mb, rng, (CX1, CY0), (CX1, CY1), banner=0.12)
    _heras(mb, rng, (CX0, CY1), (CX1, CY1), banner=0.12)
    for (sx, sy) in _scatter(rng, (CX0 + 3, CX1 - 3, CY0 + 3, CY1 - 3), 9, pad=2.6):
        f = rng.random()
        if f < 0.30:
            _genset(mb, rng, sx, sy, rng.uniform(0, 360))
        elif f < 0.50:
            _watertank(mb, rng, sx, sy)
        elif f < 0.68:
            _gascage(mb, rng, sx, sy, rng.uniform(0, 360))
        elif f < 0.85:
            _skip(mb, rng, sx, sy, rng.uniform(0, 360))
        else:
            _pallet_stack(mb, rng, sx, sy, rng.uniform(0, 360))
    objs.append(mb.build(colls['ARCH_Ground'], bevel=0.008))

    # ---- 3. loose furniture right across the paddock -----------------------
    mb = MB("ARCH_Ground_Furniture")
    zones = [(-430.0, -310.0, 42.0, 62.0), (-300.0, -160.0, 42.0, 58.0),
             (-150.0, 60.0, 42.0, 60.0), (-430.0, -200.0, 96.0, 113.0),
             (-160.0, 60.0, 92.0, 113.0), (-460.0, -320.0, 62.0, 76.0),
             (-260.0, 60.0, 76.0, 88.0), (-430.0, -260.0, 76.0, 88.0)]
    nfurn = 0
    for zi, zone in enumerate(zones):
        gr = random.Random(51000 + zi * 191)
        for (sx, sy) in _scatter(gr, zone, 26, pad=1.5):
            f = gr.random()
            a = gr.uniform(0, 360)
            if f < 0.15:
                _skip(mb, gr, sx, sy, a)
            elif f < 0.31:
                n = gr.randint(1, 4)
                for q in range(n):
                    _bin_(mb, gr, sx + q * 0.82 + gr.uniform(-0.05, 0.05),
                          sy + gr.uniform(-0.12, 0.12), a + gr.uniform(-8, 8))
            elif f < 0.50:
                z0 = 0.0
                for q in range(gr.randint(1, 3)):
                    z0 += _roadcase(mb, gr, sx + gr.uniform(-0.08, 0.08),
                                    sy + gr.uniform(-0.08, 0.08),
                                    a + gr.uniform(-6, 6), z0) + 0.006
            elif f < 0.62:
                _pallet_stack(mb, gr, sx, sy, a)
            elif f < 0.71:
                _gascage(mb, gr, sx, sy, a)
            elif f < 0.79:
                _cablereel(mb, gr, sx, sy, a)
            elif f < 0.86:
                _watertank(mb, gr, sx, sy)
            elif f < 0.93:
                _genset(mb, gr, sx, sy, a)
            else:
                for q in range(gr.randint(3, 9)):     # a cone line
                    _cone(mb, gr, sx + q * gr.uniform(1.4, 2.4),
                          sy + gr.uniform(-0.25, 0.25))
            nfurn += 1
    objs.append(mb.build(colls['ARCH_Ground'], bevel=0.006))
    counts['furniture_groups'] = nfurn

    # ---- 4. fence lines, gates, lighting, signage --------------------------
    mb = MB("ARCH_Ground_Fences")
    px0, px1, py0, py1 = PLAT_RECTS['paddock']
    gr = random.Random(6100)
    # perimeter, INSIDE the declared rectangle so no post stands on terrain
    for (a, b) in (((px0 + 0.7, py1 - 0.7), (px1 - 0.7, py1 - 0.7)),
                   ((px0 + 0.7, py0 + 0.7), (px0 + 0.7, py1 - 0.7)),
                   ((px1 - 0.7, py0 + 0.7), (px1 - 0.7, py1 - 0.7))):
        _heras(mb, gr, a, b, banner=0.30, h=2.45)
    # internal zoning: the transporter park and the hospitality frontage
    _heras(mb, gr, (-306.0, 90.4), (-176.0, 90.4), banner=0.42)
    _heras(mb, gr, (-160.0, 62.4), (62.0, 62.4), banner=0.46)
    _heras(mb, gr, (-472.0, 62.0), (-472.0, 88.0), banner=0.15)
    # light masts on the compound and along the service road
    nm = 0
    for (sx, sy) in [(-476.0, 84.0), (-440.0, 62.0), (-412.0, 92.0),
                     (-336.0, 86.5), (-268.0, 73.5), (-208.0, 86.5),
                     (-140.0, 73.5), (-74.0, 86.5), (-8.0, 73.5),
                     (58.0, 86.5), (92.0, 62.0), (-424.0, 45.5),
                     (-292.0, 45.5), (-96.0, 45.5), (44.0, 45.5),
                     (-402.0, 59.5), (-232.0, 59.5), (-166.0, 112.5),
                     (-58.0, 112.5), (78.0, 96.0)]:
        if not _free(np.array([sx]), np.array([sy]), 1.2)[0]:
            continue
        _lightmast(mb, gr, sx, sy, sit_c(sx, sy))
        nm += 1
    # finger posts and fire points where the routes cross
    LBL = [("PADDOCK", srgb('#e8e6df')), ("PIT LANE", srgb('#e0b21f')),
           ("MEDIA", srgb('#7fb2c8')), ("MEDICAL", srgb('#1e8a4a')),
           ("HOSPITALITY", srgb('#c9a227')), ("PARKING", srgb('#cfd2d5')),
           ("PIT EXIT", srgb('#1f4f8a')), ("ASSEMBLY", srgb('#a02620'))]
    nsg = 0
    for (sx, sy) in [(-462.0, 74.2), (-398.0, 74.2), (-306.0, 85.8),
                     (-232.0, 74.2), (-158.0, 85.8), (-84.0, 74.2),
                     (-10.0, 85.8), (64.0, 74.2), (-352.0, 43.5),
                     (-198.0, 92.5), (-46.0, 92.5), (-118.0, 60.0),
                     (26.0, 60.0), (-262.0, 44.5), (86.0, 74.2)]:
        if not _free(np.array([sx]), np.array([sy]), 1.0)[0]:
            continue
        k = gr.randrange(len(LBL))
        _fingerpost(mb, gr, sx, sy, sit_c(sx, sy),
                    [LBL[(k + i) % len(LBL)] for i in range(gr.randint(2, 4))])
        nsg += 1
    nfp = 0
    for (sx, sy) in [(-412.0, 73.6), (-268.0, 73.6), (-124.0, 73.6),
                     (20.0, 73.6), (-340.0, 86.4), (-52.0, 86.4),
                     (-448.0, 60.0), (-196.0, 44.0), (58.0, 44.0),
                     (-296.0, 113.2), (-64.0, 113.2)]:
        if not _free(np.array([sx]), np.array([sy]), 0.9)[0]:
            continue
        _firepoint(mb, gr, sx, sy, sit_c(sx, sy))
        nfp += 1
    counts['fire_points'] = nfp
    # jersey barrier runs protecting the crossings and the unit frontage
    _jersey(mb, gr, (-160.0, 60.6), (-120.0, 60.6))
    _jersey(mb, gr, (-70.0, 60.6), (-30.0, 60.6))
    _jersey(mb, gr, (16.0, 60.6), (60.0, 60.6))
    objs.append(mb.build(colls['ARCH_Ground'], bevel=0.006))
    counts['light_masts'] = nm
    counts['finger_posts'] = nsg

    # ---- 5. hospitality frontage: raised decks, tables, parasols ------------
    # The single biggest change to the aerial read.  Five 30 m unit frontages of
    # bare grey concrete become five occupied terraces, each with its own deck
    # size, board direction, board tone, furniture mix and parasol state.
    mb = MB("ARCH_Ground_Decks")
    ndeck = ntab = 0
    for i, (x0, x1) in enumerate(((-155.0, -126.0), (-118.0, -84.0),
                                  (-72.0, -40.0), (-28.0, 6.0), (18.0, 62.0))):
        gr = random.Random(7300 + i * 71)
        dy1 = 65.6
        dy0 = dy1 - gr.uniform(5.0, 8.5)
        dz = APRON_Z + gr.uniform(0.14, 0.30)
        bw = gr.choice((0.12, 0.145, 0.17))
        along_x = gr.random() < 0.6
        n = int(((dy1 - dy0) if along_x else (x1 - x0)) / (bw + 0.008))
        for k in range(n):
            tone = jitter_col(srgb(gr.choice(('#a4855c', '#8f7350', '#b09468',
                                              '#6f5b40'))), gr, 0.015, 0.16)
            if along_x:
                yy = dy0 + k * (bw + 0.008)
                mb.box((x0, yy, dz - 0.05), (x1, yy + bw, dz), "A_Timber", tone)
            else:
                xx = x0 + k * (bw + 0.008)
                mb.box((xx, dy0, dz - 0.05), (xx + bw, dy1, dz), "A_Timber", tone)
        mb.box((x0 - 0.06, dy0 - 0.06, APRON_Z - EMBED),
               (x1 + 0.06, dy1 + 0.06, dz - 0.082), "A_SteelPaint", srgb('#3d4247'))
        for k in range(int((x1 - x0) / 1.6)):        # a step down to the concrete
            sx = x0 + k * 1.6
            mb.box((sx, dy0 - 0.55, APRON_Z), (sx + 1.4, dy0 - 0.06, dz - 0.10),
                   "A_Timber", jitter_col(srgb('#9c8058'), gr, 0.01, 0.12))
        ndeck += 1
        for (tx, ty) in _scatter(gr, (x0 + 1.6, x1 - 1.6, dy0 + 1.4, dy1 - 1.4),
                                 gr.randint(4, 8), pad=1.5):
            kind = gr.random()
            if kind < 0.62:
                r = gr.uniform(0.42, 0.62)
                mb.cyl((tx, ty, dz), (tx, ty, dz + 0.70), 0.055, "A_Alu",
                       (1, 1, 1, 1), n=8)
                mb.cyl((tx, ty, dz + 0.70), (tx, ty, dz + 0.745), r, "A_Timber",
                       jitter_col(srgb('#c4b294'), gr, 0.01, 0.10), n=16)
                for c in range(gr.randint(2, 5)):
                    a = gr.uniform(0, 2 * math.pi)
                    cx_ = tx + math.cos(a) * (r + 0.42)
                    cy_ = ty + math.sin(a) * (r + 0.42)
                    m = T(cx_, cy_, dz) @ Rz(math.degrees(a) + 180
                                             + gr.uniform(-25, 25))
                    cc = jitter_col(srgb(gr.choice(('#2c3238', '#7d5a3a',
                                                    '#c8c2b4'))), gr, 0.02, 0.18)
                    mb.xbox(m @ T(0, 0, 0.44), (0.42, 0.42, 0.05), "A_Plastic", cc)
                    mb.xbox(m @ T(0, 0.19, 0.66), (0.42, 0.05, 0.42), "A_Plastic", cc)
                    for sx2 in (-0.17, 0.17):
                        for sy2 in (-0.17, 0.17):
                            mb.cyl((cx_ + sx2, cy_ + sy2, dz),
                                   (cx_ + sx2, cy_ + sy2, dz + 0.42), 0.016,
                                   "A_Alu", (1, 1, 1, 1), n=5)
                    ntab += 1
                if gr.random() < 0.55:               # parasol, open or furled
                    mb.cyl((tx, ty, dz), (tx, ty, dz + 2.35), 0.035, "A_Alu",
                           (1, 1, 1, 1), n=8)
                    fc = jitter_col(srgb('#ded8c8'), gr, 0.015, 0.10)
                    if gr.random() < 0.6:
                        for q in range(8):
                            a0 = 2 * math.pi * q / 8
                            a1 = 2 * math.pi * (q + 1) / 8
                            rr = gr.uniform(1.05, 1.45)
                            mb.add([(tx, ty, dz + 2.35),
                                    (tx + rr * math.cos(a0),
                                     ty + rr * math.sin(a0), dz + 1.92),
                                    (tx + rr * math.cos(a1),
                                     ty + rr * math.sin(a1), dz + 1.92)],
                                   [(0, 1, 2)], "A_Fabric", fc)
                    else:
                        mb.cyl((tx, ty, dz + 0.55), (tx, ty, dz + 2.30), 0.11,
                               "A_Fabric", fc, n=10)
            elif kind < 0.82:
                _planter(mb, gr, tx, ty, dz, gr.uniform(1.0, 1.8),
                         gr.uniform(0.7, 1.1))
            else:
                mb.box((tx - 0.7, ty - 0.35, dz), (tx + 0.7, ty + 0.35, dz + 0.95),
                       "A_Timber", jitter_col(srgb('#8f7350'), gr, 0.01, 0.12))
                mb.box((tx - 0.74, ty - 0.39, dz + 0.95),
                       (tx + 0.74, ty + 0.39, dz + 1.00), "A_Alu",
                       (0.78, 0.78, 0.78, 1))
    objs.append(mb.build(colls['ARCH_Ground'], bevel=0.005))
    counts['decks'] = ndeck
    counts['deck_seats'] = ntab

    # ---- 6. planting: concrete planters with generated shrubs ---------------
    mb = MB("ARCH_Ground_Planting")
    gr = random.Random(6200)
    npl = 0
    for (sx, sy) in _scatter(gr, (-460.0, 90.0, 64.0, 76.0), 22, pad=3.2) + \
                    _scatter(gr, (-460.0, 90.0, 42.0, 52.0), 16, pad=3.2) + \
                    _scatter(gr, (-300.0, 60.0, 92.0, 112.0), 14, pad=3.6):
        L = gr.choice((2.4, 3.2, 4.0, 5.4))
        _planter(mb, gr, sx, sy, sit_c(sx, sy), L, gr.uniform(1.1, 1.6))
        npl += 1
    objs.append(mb.build(colls['ARCH_Ground'], bevel=0.006))
    counts['planters'] = npl

    summary.update({('ground_' + k): v for k, v in counts.items()})
    return [o for o in objs if o]


def _owned_clear(cx, cy):
    return np.minimum(clear_c(cx, cy), _fc_clearance(cx, cy))


# --------------------------------------------------------------------------- #
#  3. PIT BUILDING  —  14 garages, none of them the same one twice             #
# --------------------------------------------------------------------------- #
# Fourteen fictional teams, A..N, so the row reads as a designed allocation
# rather than a random spray.  Each bay draws its door type, door state, door
# size, pier treatment, header/signage type, balcony dressing, roof plant and
# tidiness from its own seeded stream; the geometry of the door itself changes,
# not just its rotation.
TEAMS = [
    ("ALTHEA",    '#8e1d24', '#e8dfd0'), ("BOREAL",  '#5f9fd0', '#f2f6f8'),
    ("CORVUS",    '#141416', '#c8a24a'), ("DELMAR",  '#16305c', '#e2651a'),
    ("ESTIVAL",   '#c8ab74', '#4a3a28'), ("FULGOR",  '#e3bb14', '#2b2d31'),
    ("GRISAILLE", '#6d6f74', '#c02a78'), ("HALCYON", '#127f7a', '#f4f7f6'),
    ("IRIDIA",    '#5b3f9a', '#b9bec4'), ("JUNIPER", '#2f6b3a', '#efe6cd'),
    ("KESTREL",   '#1d3a2a', '#d8641c'), ("LUMEN",   '#e9edf0', '#17a8c4'),
    ("MERIDIAN",  '#22306e', '#f0f2f5'), ("NOCTIS",  '#2a2c2e', '#9ed61f'),
]
BAY_W = [21.0, 22.0, 20.5, 21.5, 23.0, 20.0, 21.0, 22.5,
         20.5, 21.0, 22.0, 20.5, 20.5, 20.0]          # sums to 296.0
CORE_W = [6.0, 5.0, 5.0, 8.0]                          # W, mid1, mid2, E  = 24
PB_Y0, PB_Y1 = 23.5, 40.5     # garage front / paddock face
PB_X0, PB_X1 = -245.0, 75.0
PB_Z_GF = 6.40                # underside of the first-floor slab
PB_Z_L1 = 10.40               # head of the level-1 glazing
PB_Z_RF = 10.90               # roof deck
PB_Z_PT = 12.00               # parapet top  (spec: roof z = +12.0)
CANOPY_Y = 19.80              # cantilever edge over the pit lane
L1_FACE_Y = 21.20


def garage_specs(rng):
    """One dict per garage bay.  Everything a later builder needs to make that
    bay unlike its neighbours."""
    out = []
    x = PB_X0 + CORE_W[0]
    order = [4, 5, 5]
    bi = 0
    for gi, n in enumerate(order):
        for k in range(n):
            w = BAY_W[bi]
            team, c1, c2 = TEAMS[bi]
            dw = round(rng.uniform(6.2, 8.4), 2)
            g = dict(
                num=bi + 1, team=team, x=x + w * 0.5, w=w, dw=dw,
                dh=round(rng.uniform(4.35, 4.95), 2),
                doff=round(rng.uniform(-1.1, 1.1), 2),
                dtype=('roller', 'sectional', 'concertina', 'overhead',
                       'roller', 'sectional')[bi % 6] if rng.random() < 0.75
                      else rng.choice(('roller', 'sectional', 'concertina',
                                       'overhead')),
                state=rng.choice(('closed', 'closed', 'part', 'open', 'open',
                                  'part', 'closed')),
                pier=rng.choice(('render', 'ribbed', 'block', 'slot')),
                header=rng.choice(('lightbox', 'cutletter', 'banner', 'plain')),
                col1=srgb(c1), col2=srgb(c2),
                tidy=rng.random(), box_wear=rng.random(),
                balcony=rng.choice(('glass', 'rail', 'mesh', 'glass')),
                bal_dress=rng.random(),
                roof=rng.random(), lit=rng.random() < 0.72,
                interior=rng.randint(0, 3), seed=rng.randint(0, 1 << 20),
            )
            out.append(g)
            x += w
            bi += 1
        if gi < 3:
            x += CORE_W[gi + 1]
    return out


def _door(mb, g, rng):
    """Five door families; the closed/part/open state changes the geometry."""
    x, dw, dh = g['x'] + g['doff'], g['dw'], g['dh']
    y = PB_Y0 + 0.04
    c = jitter_col(g['col2'], rng, 0.01, 0.10)
    frac = {'closed': 0.0, 'part': rng.uniform(0.30, 0.72), 'open': 1.0}[g['state']]
    z0 = 0.02 + (dh - 0.15) * frac
    # reveal / frame
    mb.box((x - dw / 2 - 0.16, PB_Y0 - 0.02, 0.0),
           (x - dw / 2, y + 0.30, dh + 0.18), "A_Alu", (0.8, 0.8, 0.8, 1))
    mb.box((x + dw / 2, PB_Y0 - 0.02, 0.0),
           (x + dw / 2 + 0.16, y + 0.30, dh + 0.18), "A_Alu", (0.8, 0.8, 0.8, 1))
    mb.box((x - dw / 2 - 0.16, PB_Y0 - 0.02, dh + 0.02),
           (x + dw / 2 + 0.16, y + 0.30, dh + 0.18), "A_Alu", (0.8, 0.8, 0.8, 1))
    t = g['dtype']
    if t == 'roller':
        if frac < 0.98:
            n = max(1, int((dh - z0) / 0.14))
            for k in range(n):
                zz = z0 + k * 0.14
                mb.box((x - dw / 2, y, zz), (x + dw / 2, y + 0.05, zz + 0.126),
                       "A_SteelPaint", c)
        if frac > 0.02:                      # the coil sits under the head
            mb.cyl((x - dw / 2 + 0.05, y + 0.22, dh - 0.32),
                   (x + dw / 2 - 0.05, y + 0.22, dh - 0.32),
                   0.16 + 0.12 * frac, "A_SteelPaint", c, n=14)
    elif t == 'sectional':
        panels = 4
        ph = (dh - 0.06) / panels
        for k in range(panels):
            zz = 0.02 + k * ph
            if zz + ph * 0.5 < z0:
                continue
            zz2 = zz + ph - 0.02
            if frac > 0.02:                  # panels stack up under the ceiling
                zz = dh + 0.05 + k * 0.10
                zz2 = zz + 0.08
                mb.box((x - dw / 2, y + 0.10 + k * 0.02, zz),
                       (x + dw / 2, y + 0.16 + k * 0.02, zz2), "A_SteelPaint", c)
                continue
            mb.box((x - dw / 2, y, zz), (x + dw / 2, y + 0.07, zz2),
                   "A_SteelPaint", c)
            if k == panels - 2:              # vision strip
                mb.box((x - dw / 2 + 0.5, y - 0.005, zz + 0.10),
                       (x + dw / 2 - 0.5, y + 0.075, zz2 - 0.10),
                       "A_GlassTint", (1, 1, 1, 1))
    elif t == 'concertina':
        leaves = 6
        lw = dw / leaves
        for k in range(leaves):
            if frac > 0.5:                   # folded back against the reveal
                fx = x - dw / 2 + (0.10 * k if k < leaves / 2 else
                                   dw - 0.10 * (leaves - k))
                mb.box((fx, y, 0.02), (fx + 0.09, y + lw * 0.85, dh),
                       "A_SteelPaint", c)
            else:
                lx = x - dw / 2 + k * lw
                sw = 0.06 * math.sin(k * 1.7)
                mb.box((lx + 0.02, y + sw, 0.02 + (dh - 0.1) * frac),
                       (lx + lw - 0.02, y + 0.06 + sw, dh), "A_SteelPaint", c)
    else:                                     # overhead single leaf
        if frac < 0.98:
            ang = 78.0 * frac
            m = T(x, y + 0.05, dh) @ Rx(-ang) @ T(0, 0, -(dh - 0.04) * 0.5)
            mb.xbox(m, (dw, 0.08, dh - 0.04), "A_SteelPaint", c)
            for k in range(3):
                mm = T(x, y + 0.09, dh) @ Rx(-ang) @ T(0, 0, -(dh - 0.04) * 0.5)
                mb.xbox(mm @ T(0, 0, -dh * 0.3 + k * dh * 0.3),
                        (dw - 0.2, 0.05, 0.10), "A_SteelPaint",
                        (c[0] * 0.8, c[1] * 0.8, c[2] * 0.8, 1))
        else:
            mb.box((x - dw / 2, y + 0.4, dh + 0.10),
                   (x + dw / 2, y + 2.6, dh + 0.20), "A_SteelPaint", c)
    return frac


def _interior(mb, g, rng, frac):
    """Only cut when the door is open enough to see in; four layouts, each with
    its own equipment wall, and one bay that is simply dark and empty."""
    x, dw = g['x'] + g['doff'], g['dw']
    d0, d1 = PB_Y0 + 0.05, PB_Y0 + 15.5
    w0, w1 = g['x'] - g['w'] / 2 + 0.45, g['x'] + g['w'] / 2 - 0.45
    mb.box((w0, d0, 0.012), (w1, d1, 0.02), "A_ConcSlab", (0.86, 0.86, 0.85, 1))
    mb.box((w0, d1, 0.0), (w1, d1 + 0.25, 5.6), "A_ConcPrecast", (0.9, 0.9, 0.9, 1))
    mb.box((w0 - 0.25, d0, 0.0), (w0, d1, 5.6), "A_ConcPrecast", (0.88, 0.88, 0.88, 1))
    mb.box((w1, d0, 0.0), (w1 + 0.25, d1, 5.6), "A_ConcPrecast", (0.88, 0.88, 0.88, 1))
    mb.box((w0, d0, 5.6), (w1, d1, 5.75), "A_SteelPaint", (0.28, 0.28, 0.29, 1))
    lay = g['interior']
    lit = g['lit']
    if lit:
        for k in range(5):
            yy = d0 + 1.6 + k * 2.7
            mb.box((x - dw * 0.42, yy, 5.42), (x + dw * 0.42, yy + 0.34, 5.56),
                   "A_EmitStrong", srgb('#fff2dc'))
    else:
        for k in range(2):
            yy = d0 + 3.0 + k * 6.0
            mb.box((x - dw * 0.3, yy, 5.42), (x + dw * 0.3, yy + 0.30, 5.56),
                   "A_Emit", (0.02, 0.02, 0.02, 1))
    if lay == 3:
        return                                     # stripped bay, nothing in it
    # tool wall
    side = -1 if lay % 2 == 0 else 1
    wx = (w0 + 0.3) if side < 0 else (w1 - 0.3)
    for k in range(6):
        yy = d0 + 1.2 + k * 2.1
        h = rng.uniform(1.6, 2.3)
        mb.box((wx - 0.55, yy, 0.02), (wx + 0.55, yy + 1.9, h), "A_SteelPaint",
               jitter_col(g['col1'], rng, 0.01, 0.12))
        mb.box((wx - 0.58, yy + 0.05, h - 0.06), (wx + 0.58, yy + 1.85, h),
               "A_Alu", (0.75, 0.75, 0.75, 1))
    # back-wall graphic in team colour
    mb.box((x - dw * 0.45, d1 - 0.02, 1.2), (x + dw * 0.45, d1 + 0.01, 3.6),
           "A_Sign", jitter_col(g['col1'], rng, 0.006, 0.05))
    mb.text(g['team'], T(x, d1 - 0.06, 2.4) @ Rx(90), 0.9, "A_Sign",
            jitter_col(g['col2'], rng, 0.01, 0.06), extrude=0.01)
    if lay == 0:
        for k in range(4):                          # wheel rack
            for s in range(2):
                mb.tyre(T(x + 0.6 + s * 0.9, d1 - 1.9, 0.40 + k * 0.74)
                        @ Rx(90) @ Rz(rng.uniform(0, 90)), r_out=0.36,
                        r_in=0.165, w=0.34, n=18,
                        rim=("A_Alu", (0.82, 0.82, 0.82, 1)))
            mb.box((x + 0.2, d1 - 2.3, 0.02 + k * 0.74),
                   (x + 1.9, d1 - 1.5, 0.06 + k * 0.74), "A_SteelGalv",
                   (0.62, 0.62, 0.62, 1))
    elif lay == 1:
        m = T(x - 1.4, d0 + 5.0, 0.5) @ Rz(rng.uniform(-8, 8))
        mb.xbox(m, (2.4, 0.9, 1.0), "A_SteelPaint", srgb('#b8bcc0'))   # bench
        mb.xbox(m @ T(0, 0, 0.56), (2.5, 1.0, 0.08), "A_Timber", (1, 1, 1, 1))
    else:
        for k in range(3):                          # stacked crates
            m = T(x + rng.uniform(-1.5, 1.5), d0 + 4.0 + k * 1.3,
                  0.35 + 0.7 * (k % 2)) @ Rz(rng.uniform(-12, 12))
            mb.xbox(m, (1.2, 0.8, 0.68), "A_SteelPaint",
                    jitter_col(g['col1'], rng, 0.02, 0.2))


def _header_sign(mb, g, rng):
    x, dw, dh = g['x'] + g['doff'], g['dw'], g['dh']
    y = PB_Y0
    z0 = dh + 0.30
    h = 1.15
    w = min(g['w'] - 1.6, dw + 3.6)
    kind = g['header']
    c1 = jitter_col(g['col1'], rng, 0.008, 0.06)
    c2 = jitter_col(g['col2'], rng, 0.008, 0.06)
    if kind == 'lightbox':
        mb.box((x - w / 2, y - 0.22, z0), (x + w / 2, y + 0.02, z0 + h),
               "A_Emit", (c2[0] * 0.9, c2[1] * 0.9, c2[2] * 0.9, 1))
        mb.box((x - w / 2 - 0.06, y - 0.30, z0 - 0.06),
               (x + w / 2 + 0.06, y - 0.20, z0 + h + 0.06), "A_Alu",
               (0.7, 0.7, 0.7, 1))
        if rng.random() < 0.18:              # one tube out at the near end
            mb.box((x - w / 2, y - 0.24, z0), (x - w / 2 + w * 0.28,
                   y - 0.19, z0 + h), "A_Sign", (0.05, 0.05, 0.05, 1))
        mb.text(g['team'], T(x, y - 0.34, z0 + h * 0.52) @ Rx(90), 0.62,
                "A_Sign", c1, extrude=0.02)
    elif kind == 'cutletter':
        mb.box((x - w / 2, y - 0.10, z0), (x + w / 2, y + 0.02, z0 + h),
               "A_Sign", c1)
        mb.text(g['team'], T(x, y - 0.16, z0 + h * 0.52) @ Rx(90), 0.66,
                "A_Alu", c2, extrude=0.05)
    elif kind == 'banner':
        sag = 0.10
        for k in range(8):                    # a fabric banner with real droop
            t0, t1 = k / 8.0, (k + 1) / 8.0
            xx0, xx1 = x - w / 2 + w * t0, x - w / 2 + w * t1
            s0 = math.sin(t0 * math.pi) * sag
            s1 = math.sin(t1 * math.pi) * sag
            mb.quad((xx0, y - 0.04 - s0, z0 - s0 * 0.5),
                    (xx1, y - 0.04 - s1, z0 - s1 * 0.5),
                    (xx1, y - 0.04 - s1, z0 + h - s1 * 0.5),
                    (xx0, y - 0.04 - s0, z0 + h - s0 * 0.5), "A_Fabric", c1)
        mb.text(g['team'], T(x, y - 0.22, z0 + h * 0.5) @ Rx(90), 0.60,
                "A_Sign", c2, extrude=0.004)
    else:
        mb.box((x - w / 2, y - 0.06, z0), (x + w / 2, y + 0.02, z0 + h),
               "A_Sign", c1)
        mb.text("%02d" % g['num'], T(x - w / 2 + 0.9, y - 0.10, z0 + h * 0.5)
                @ Rx(90), 0.80, "A_Sign", c2, extrude=0.02)
    # bay number repeated on the canopy fascia, always, so the row can be read
    mb.text("%02d" % g['num'], T(x, CANOPY_Y - 0.12, PB_Z_GF - 0.22) @ Rx(90),
            0.42, "A_Sign", srgb('#e9ecef'), extrude=0.006)


def _balcony_dress(mb, g, rng):
    x, w = g['x'], g['w']
    z = PB_Z_GF + 0.04
    kind = g['balcony']
    c1 = jitter_col(g['col1'], rng, 0.01, 0.08)
    if kind == 'glass':
        mb.box((x - w / 2 + 0.3, CANOPY_Y + 0.02, z + 0.05),
               (x + w / 2 - 0.3, CANOPY_Y + 0.08, z + 1.10), "A_GlassTint",
               (1, 1, 1, 1))
        for k in range(int(w / 2.4) + 1):
            mb.cyl((x - w / 2 + 0.3 + k * 2.4, CANOPY_Y + 0.05, z),
                   (x - w / 2 + 0.3 + k * 2.4, CANOPY_Y + 0.05, z + 1.15),
                   0.03, "A_Alu", (1, 1, 1, 1), n=8)
    elif kind == 'rail':
        for hh in (0.42, 0.78, 1.12):
            mb.cyl((x - w / 2 + 0.3, CANOPY_Y + 0.05, z + hh),
                   (x + w / 2 - 0.3, CANOPY_Y + 0.05, z + hh), 0.025,
                   "A_SteelGalv", (1, 1, 1, 1), n=8)
        for k in range(int(w / 1.9) + 1):
            mb.cyl((x - w / 2 + 0.3 + k * 1.9, CANOPY_Y + 0.05, z),
                   (x - w / 2 + 0.3 + k * 1.9, CANOPY_Y + 0.05, z + 1.15),
                   0.025, "A_SteelGalv", (1, 1, 1, 1), n=8)
    else:
        mb.box((x - w / 2 + 0.3, CANOPY_Y + 0.03, z),
               (x + w / 2 - 0.3, CANOPY_Y + 0.06, z + 1.12), "A_MeshScreen",
               (1, 1, 1, 1))
    d = g['bal_dress']
    if d > 0.62:                              # banner over the balustrade
        mb.box((x - w * 0.32, CANOPY_Y - 0.02, z - 0.62),
               (x + w * 0.32, CANOPY_Y + 0.01, z + 1.02), "A_Fabric", c1)
        mb.text(g['team'], T(x, CANOPY_Y - 0.06, z + 0.24) @ Rx(90), 0.46,
                "A_Sign", jitter_col(g['col2'], rng, 0.01, 0.05), extrude=0.004)
    if d > 0.35:                              # table, stools, parasol
        for k in range(rng.randint(1, 3)):
            mx = x + rng.uniform(-w * 0.3, w * 0.3)
            my = CANOPY_Y + rng.uniform(0.9, 1.6)
            mb.cyl((mx, my, z), (mx, my, z + 0.72), 0.05, "A_Alu", (1, 1, 1, 1), n=8)
            mb.cyl((mx, my, z + 0.72), (mx, my, z + 0.76), 0.42, "A_Sign",
                   srgb('#d8d5cf'), n=14)
            for s in range(rng.randint(0, 3)):
                a = rng.uniform(0, 6.28)
                sx, sy = mx + 0.85 * math.cos(a), my + 0.85 * math.sin(a)
                mb.cyl((sx, sy, z), (sx, sy, z + 0.44), 0.05, "A_Alu",
                       (1, 1, 1, 1), n=6)
                mb.cyl((sx, sy, z + 0.44), (sx, sy, z + 0.48), 0.20, "A_Sign",
                       jitter_col(c1, rng, 0.05, 0.2), n=10)
    if d > 0.80:
        px = x + rng.uniform(-2, 2)
        mb.cyl((px, CANOPY_Y + 1.2, z), (px, CANOPY_Y + 1.2, z + 2.3), 0.045,
               "A_Alu", (1, 1, 1, 1), n=8)
        for k in range(8):                    # a closed parasol, tied
            a0 = 2 * math.pi * k / 8
            mb.cyl((px, CANOPY_Y + 1.2, z + 2.3),
                   (px + 0.12 * math.cos(a0), CANOPY_Y + 1.2 + 0.12 * math.sin(a0),
                    z + 1.15), 0.035, "A_Fabric", c1, n=5)


def _pier(mb, g, rng, xa, xb):
    """The pier between two doors - four constructions, not four textures."""
    y0, y1 = PB_Y0 - 0.02, PB_Y0 + 0.55
    k = g['pier']
    if k == 'render':
        mb.box((xa, y0, 0.0), (xb, y1, PB_Z_GF - 0.4), "A_ConcPrecast",
               (0.98, 0.98, 0.97, 1))
    elif k == 'ribbed':
        mb.box((xa, y0 + 0.10, 0.0), (xb, y1, PB_Z_GF - 0.4), "A_ConcPrecast",
               (0.92, 0.92, 0.91, 1))
        n = max(1, int((xb - xa) / 0.30))
        for i in range(n):
            xx = xa + i * 0.30
            mb.box((xx + 0.04, y0, 0.0), (xx + 0.24, y0 + 0.12, PB_Z_GF - 0.4),
                   "A_Alu", (0.62, 0.63, 0.64, 1))
    elif k == 'block':
        rows = int((PB_Z_GF - 0.4) / 0.225)
        for r in range(rows):
            off = 0.11 if r % 2 else 0.0
            n = max(1, int((xb - xa) / 0.45))
            for i in range(n + 1):
                xx = xa + off + i * 0.45
                if xx > xb - 0.05:
                    continue
                mb.box((xx + 0.012, y0, r * 0.225 + 0.012),
                       (min(xx + 0.44, xb), y1, r * 0.225 + 0.213),
                       "A_ConcPrecast", (0.86 + 0.06 * ((i * 7 + r * 3) % 5) / 5.0,
                                         0.86, 0.85, 1))
    else:
        mb.box((xa, y0, 0.0), (xb, y1, PB_Z_GF - 0.4), "A_ConcPrecast",
               (0.95, 0.95, 0.94, 1))
        mb.box((xa + (xb - xa) * 0.4, y0 - 0.03, 1.2),
               (xa + (xb - xa) * 0.6, y0 + 0.06, PB_Z_GF - 1.1), "A_GlassTint",
               (1, 1, 1, 1))


def _core(mb, rng, xa, xb, tag):
    """Stair / services core.  Breaks the bay rhythm and carries the vertical
    circulation - three of them, each detailed differently."""
    y0, y1 = 21.9, PB_Y1
    top = PB_Z_PT + (0.7 if tag != 'E' else 1.9)
    mb.box((xa, y0, 0.0), (xb, y1, top), "A_ConcPrecast", (0.90, 0.90, 0.89, 1))
    # glazed stair slot on the pit-lane face
    mb.box((xa + 0.5, y0 - 0.06, 0.9), (xb - 0.5, y0 + 0.02, top - 1.4),
           "A_GlassTint", (1, 1, 1, 1))
    # the flights inside, visible through it
    n = int((top - 1.6) / 1.8)
    for k in range(n):
        z = 0.9 + k * 1.8
        d = 1 if k % 2 == 0 else -1
        mb.box((xa + 0.6, y0 + 0.10, z), (xb - 0.6, y0 + 1.9, z + 0.12),
               "A_SteelGalv", (0.7, 0.7, 0.7, 1))
        for s in range(9):
            mb.box((xa + 0.6 + (xb - xa - 1.2) * (s / 9.0 if d > 0 else 1 - s / 9.0),
                    y0 + 0.15, z + 0.12 + s * 0.19),
                   (xa + 0.6 + (xb - xa - 1.2) * ((s + 0.9) / 9.0 if d > 0 else
                                                  1 - (s + 0.9) / 9.0),
                    y0 + 1.85, z + 0.20 + s * 0.19), "A_SteelGalv",
                   (0.62, 0.62, 0.62, 1))
    # lift overrun / plant box, different on every core
    if tag == 'E':
        mb.box((xa + 1.0, y0 + 3.0, top), (xb - 1.0, y0 + 8.0, top + 2.4),
               "A_Alu", (0.8, 0.8, 0.8, 1))
        mb.cyl((xa + 2.0, y0 + 11.0, top), (xa + 2.0, y0 + 11.0, top + 9.0),
               0.14, "A_SteelGalv", (1, 1, 1, 1), n=10)
        for k in range(3):
            mb.cyl((xa + 2.0, y0 + 11.0, top + 3.0 + k * 2.4),
                   (xa + 2.0 + 0.9, y0 + 11.0, top + 3.6 + k * 2.4), 0.05,
                   "A_SteelGalv", (1, 1, 1, 1), n=6)
    else:
        mb.box((xa + 0.8, y0 + 4.0, top), (xb - 0.8, y0 + 7.5, top + 1.6),
               "A_ConcPrecast", (0.88, 0.88, 0.87, 1))


def _roof_plant(mb, rng, x0, x1):
    """Rooftop plant.  Every unit is drawn from a family with its own size,
    orientation, fin count and stain, and the density varies along the roof."""
    z = PB_Z_RF
    x = x0 + 2.0
    while x < x1 - 3.0:
        r = rng.random()
        if r < 0.34:                       # condenser bank, 1-3 units
            n = rng.randint(1, 3)
            for k in range(n):
                m = T(x + k * 1.5, 27.0 + rng.uniform(-1.5, 3.0), z + 0.55) \
                    @ Rz(rng.uniform(-6, 6))
                mb.xbox(m, (1.25, 1.15, 1.10), "A_SteelPaint", srgb('#9aa0a4'))
                for f in range(7):         # fins
                    mb.xbox(m @ T(0, 0, 0.56) @ T(-0.5 + f * 0.16, 0, 0),
                            (0.06, 1.0, 0.06), "A_Alu", (0.8, 0.8, 0.8, 1))
            x += 1.5 * n + rng.uniform(1.5, 5.0)
        elif r < 0.50:                     # AHU box on a plinth
            L = rng.uniform(3.0, 6.0)
            mb.box((x, 28.0, z), (x + L, 34.0, z + 0.25), "A_ConcPrecast",
                   (0.9, 0.9, 0.9, 1))
            m = T(x + L / 2, 31.0, z + 1.2) @ Rz(rng.uniform(-3, 3))
            mb.xbox(m, (L - 0.4, 2.6, 1.9), "A_SteelPaint", srgb('#b6bbbe'))
            for f in range(int(L / 0.8)):
                mb.xbox(m @ T(-L / 2 + 0.5 + f * 0.8, 1.32, 0), (0.6, 0.06, 1.5),
                        "A_Alu", (0.7, 0.7, 0.7, 1))
            x += L + rng.uniform(2.0, 6.0)
        elif r < 0.60:                     # satellite dish
            d = rng.uniform(0.9, 2.4)
            px, py = x + 1.5, 30.0 + rng.uniform(-2, 4)
            mb.cyl((px, py, z), (px, py, z + 0.6 + d * 0.4), 0.10, "A_SteelGalv",
                   (1, 1, 1, 1), n=8)
            m = T(px, py, z + 0.6 + d * 0.4) @ Rz(rng.uniform(-40, 40)) \
                @ Rx(rng.uniform(-55, -25))
            mb.cyl(tuple(m @ Vector((0, 0, 0))), tuple(m @ Vector((0, 0, 0.12))),
                   d * 0.5, "A_Sign", srgb('#e6e6e2'), n=20, r1=d * 0.5 * 0.94)
            x += 3.0 + rng.uniform(1.0, 5.0)
        elif r < 0.72:                     # cable tray run + supports
            L = rng.uniform(6.0, 18.0)
            yy = 25.4 + rng.uniform(0, 1.2)
            mb.box((x, yy, z + 0.42), (x + L, yy + 0.45, z + 0.50), "A_SteelGalv",
                   (0.66, 0.66, 0.66, 1))
            for k in range(int(L / 2.5) + 1):
                mb.box((x + k * 2.5, yy + 0.05, z), (x + k * 2.5 + 0.08,
                       yy + 0.13, z + 0.42), "A_SteelGalv", (0.6, 0.6, 0.6, 1))
            x += L + rng.uniform(1.0, 4.0)
        elif r < 0.80:                     # rooftop terrace deck + shades
            L = rng.uniform(8.0, 16.0)
            mb.box((x, 24.6, z + 0.02), (x + L, 32.0, z + 0.14), "A_Timber",
                   (1, 1, 1, 1))
            for k in range(int(L / 3.5)):
                px = x + 1.6 + k * 3.5
                mb.cyl((px, 25.4, z + 0.14), (px, 25.4, z + 2.5), 0.07, "A_Alu",
                       (1, 1, 1, 1), n=8)
                mb.cyl((px, 30.8, z + 0.14), (px, 30.8, z + 2.5), 0.07, "A_Alu",
                       (1, 1, 1, 1), n=8)
                if rng.random() < 0.7:
                    mb.box((px - 0.1, 25.3, z + 2.42), (px + 3.4, 30.9, z + 2.50),
                           "A_Fabric", jitter_col(srgb('#d9d5cb'), rng, 0.02, 0.1))
            x += L + rng.uniform(2.0, 5.0)
        elif r < 0.88:                     # TV camera platform
            px = x + 1.0
            mb.box((px, 23.9, z), (px + 2.2, 26.1, z + 0.9), "A_SteelGalv",
                   (0.7, 0.7, 0.7, 1))
            mb.box((px + 0.1, 24.0, z + 0.9), (px + 2.1, 26.0, z + 1.0),
                   "A_MeshDark", (1, 1, 1, 1))
            for cx, cy in ((px + 0.15, 24.05), (px + 2.05, 24.05),
                           (px + 0.15, 25.95), (px + 2.05, 25.95)):
                mb.cyl((cx, cy, z + 1.0), (cx, cy, z + 2.05), 0.03, "A_SteelGalv",
                       (1, 1, 1, 1), n=6)
            mb.cyl((px + 1.1, 25.0, z + 1.0), (px + 1.1, 25.0, z + 1.45), 0.09,
                   "A_SteelPaint", srgb('#1e1f21'), n=10)
            mb.xbox(T(px + 1.1, 24.75, z + 1.62) @ Rz(rng.uniform(-25, 25)),
                    (0.32, 0.75, 0.30), "A_SteelPaint", srgb('#232426'))
            x += 4.0 + rng.uniform(2.0, 8.0)
        else:
            x += rng.uniform(3.0, 9.0)


def _pit_equipment(mb, g, rng):
    """What is standing in front of the box.  Tidiness drives count AND
    alignment: a tidy box has three trolleys square to the wall, an untidy one
    has six things at angles with a hose across the floor."""
    tidy = g['tidy']
    x = g['x'] + g['doff']
    n = int(1 + (1.0 - tidy) * 6)
    c1 = g['col1']
    for k in range(n):
        kind = rng.random()
        ax = x + rng.uniform(-g['dw'] * 0.55, g['dw'] * 0.55)
        ay = 17.0 + rng.uniform(0.0, 4.2)
        rot = rng.uniform(-4, 4) if tidy > 0.6 else rng.uniform(-40, 40)
        m = T(ax, ay, 0.0) @ Rz(rot)
        if kind < 0.24:                     # roll cab, 3-6 drawers
            h = rng.uniform(0.9, 1.15)
            body = jitter_col(c1, rng, 0.02, 0.15)
            mb.xbox(m @ T(0, 0, h * 0.5 + 0.09), (0.72, 0.48, h), "A_SteelPaint",
                    body)
            nd = rng.randint(3, 6)
            dh = (h - 0.14) / nd
            for d in range(nd):
                dz = 0.16 + dh * (d + 0.5)
                mb.xbox(m @ T(0, -0.245, dz), (0.66, 0.022, dh - 0.025),
                        "A_SteelPaint", (body[0] * 0.72, body[1] * 0.72,
                                         body[2] * 0.72, 1))
                mb.xbox(m @ T(0, -0.262, dz), (0.24, 0.022, 0.024), "A_Alu",
                        (0.82, 0.82, 0.82, 1))
            mb.xbox(m @ T(0, 0, h + 0.11), (0.77, 0.53, 0.035), "A_SteelGalv",
                    (0.74, 0.74, 0.73, 1))
            mb.cyl(tuple(m @ Vector((-0.30, 0.28, h * 0.74))),
                   tuple(m @ Vector((0.30, 0.28, h * 0.74))), 0.018, "A_Alu",
                   (1, 1, 1, 1), n=6)
            for sx in (-0.28, 0.28):
                for sy in (-0.17, 0.17):
                    mb.cyl(tuple(m @ Vector((sx, sy - 0.03, 0.09))),
                           tuple(m @ Vector((sx, sy + 0.03, 0.09))), 0.09,
                           "A_Rubber", (1, 1, 1, 1), n=8)
        elif kind < 0.42:                   # tyre set, stacked
            nn = rng.randint(2, 4)
            for t in range(nn):
                mb.tyre(m @ T(0, 0, 0.18 + t * 0.32) @ Rz(rng.uniform(0, 90)),
                        r_out=0.36, r_in=0.165, w=0.30, n=18,
                        rim=("A_Alu", (0.8, 0.8, 0.8, 1)))
        elif kind < 0.56:                   # tyre blanket drum
            mb.cyl(tuple(m @ Vector((0, 0, 0.0))), tuple(m @ Vector((0, 0, 0.62))),
                   0.44, "A_Fabric", jitter_col(c1, rng, 0.02, 0.2), n=14)
        elif kind < 0.68:                   # gas bottle pair in a cage
            mb.xbox(m @ T(0, 0, 0.5), (0.7, 0.42, 1.0), "A_MeshDark", (1, 1, 1, 1))
            for sx in (-0.16, 0.16):
                mb.cyl(tuple(m @ Vector((sx, 0, 0.03))),
                       tuple(m @ Vector((sx, 0, 0.86))), 0.14, "A_SteelPaint",
                       rng.choice((srgb('#1c4f8c'), srgb('#8c1c1c'),
                                   srgb('#2f2f2f'))), n=12)
        elif kind < 0.80:                   # hose reel
            mb.cyl(tuple(m @ Vector((0, -0.12, 0.55))),
                   tuple(m @ Vector((0, 0.12, 0.55))), 0.34, "A_SteelPaint",
                   srgb('#d0d3d6'), n=16)
            mb.xbox(m @ T(0, 0, 0.22), (0.14, 0.5, 0.44), "A_SteelGalv",
                    (0.7, 0.7, 0.7, 1))
            if tidy < 0.4:                  # ... with the hose left out
                px, py = 0.0, 0.0
                for s in range(9):
                    nx = px + rng.uniform(0.3, 0.8)
                    ny = py + rng.uniform(-0.7, 0.7)
                    mb.cyl(tuple(m @ Vector((px, py - 0.4, 0.03))),
                           tuple(m @ Vector((nx, ny - 0.4, 0.03))), 0.028,
                           "A_Rubber", (1, 1, 1, 1), n=5)
                    px, py = nx, ny
        elif kind < 0.90:                   # folding chairs / bench
            for c in range(rng.randint(1, 3)):
                mm = m @ T(c * 0.62, 0, 0) @ Rz(rng.uniform(-25, 25))
                mb.xbox(mm @ T(0, 0, 0.44), (0.42, 0.42, 0.05), "A_SteelPaint",
                        jitter_col(c1, rng, 0.03, 0.2))
                mb.xbox(mm @ T(0, 0.19, 0.68), (0.42, 0.05, 0.42), "A_SteelPaint",
                        jitter_col(c1, rng, 0.03, 0.2))
                for sx in (-0.17, 0.17):
                    for sy in (-0.17, 0.17):
                        mb.cyl(tuple(mm @ Vector((sx, sy, 0.0))),
                               tuple(mm @ Vector((sx, sy, 0.44))), 0.016,
                               "A_Alu", (1, 1, 1, 1), n=5)
        else:                               # pallet + crate
            mb.xbox(m @ T(0, 0, 0.07), (1.2, 0.8, 0.14), "A_Timber", (1, 1, 1, 1))
            if rng.random() < 0.75:
                mb.xbox(m @ T(0, 0, 0.5) @ Rz(rng.uniform(-8, 8)),
                        (1.1, 0.72, 0.72), "A_SteelPaint",
                        jitter_col(c1, rng, 0.02, 0.2))


def build_pit_building(colls, rng, garages, summary):
    shell = MB("ARCH_PitBuilding_Shell")
    det = MB("ARCH_PitBuilding_Detail")
    # ---- ground slab, rear wall, flank walls -------------------------------
    shell.box((PB_X0, PB_Y0, -0.45), (PB_X1, PB_Y1, 0.012), "A_ConcPrecast",
              (0.82, 0.82, 0.81, 1))
    shell.box((PB_X0, PB_Y1 - 0.35, 0.0), (PB_X1, PB_Y1, PB_Z_RF),
              "A_ConcPrecast", (0.93, 0.93, 0.92, 1))
    shell.box((PB_X0, PB_Y0, 0.0), (PB_X0 + 0.35, PB_Y1, PB_Z_RF),
              "A_ConcPrecast", (0.93, 0.93, 0.92, 1))
    shell.box((PB_X1 - 0.35, PB_Y0, 0.0), (PB_X1, PB_Y1, PB_Z_RF),
              "A_ConcPrecast", (0.93, 0.93, 0.92, 1))
    # ---- first floor slab + pit-lane canopy --------------------------------
    shell.box((PB_X0, CANOPY_Y, PB_Z_GF - 0.40), (PB_X1, PB_Y1, PB_Z_GF),
              "A_ConcPrecast", (0.96, 0.96, 0.95, 1))
    shell.box((PB_X0, CANOPY_Y - 0.16, PB_Z_GF - 0.55), (PB_X1, CANOPY_Y,
              PB_Z_GF + 0.06), "A_Alu", (0.72, 0.73, 0.74, 1))   # fascia
    # ---- level 1: glazed hospitality band ----------------------------------
    shell.box((PB_X0, L1_FACE_Y, PB_Z_GF), (PB_X1, L1_FACE_Y + 0.12, PB_Z_L1),
              "A_Spandrel", (1, 1, 1, 1))
    x = PB_X0 + 0.4
    mull = 0
    while x < PB_X1 - 0.4:
        w = 2.1 + 0.55 * ((mull * 7) % 5) / 5.0        # mullion pitch wanders
        det.box((x, L1_FACE_Y - 0.05, PB_Z_GF + 0.10),
                (x + 0.10, L1_FACE_Y + 0.14, PB_Z_L1 - 0.10), "A_Alu",
                (0.75, 0.75, 0.75, 1))
        det.box((x + 0.10, L1_FACE_Y + 0.02, PB_Z_GF + 0.55),
                (x + w, L1_FACE_Y + 0.06, PB_Z_L1 - 0.45), "A_Glass",
                (1, 1, 1, 1))
        det.box((x + 0.10, L1_FACE_Y + 0.0, PB_Z_GF + 0.10),
                (x + w, L1_FACE_Y + 0.09, PB_Z_GF + 0.55), "A_Spandrel",
                (1, 1, 1, 1))
        x += w
        mull += 1
    shell.box((PB_X0, L1_FACE_Y - 0.10, PB_Z_L1), (PB_X1, PB_Y1, PB_Z_RF),
              "A_ConcPrecast", (0.95, 0.95, 0.94, 1))
    # ---- roof deck + parapet ----------------------------------------------
    shell.box((PB_X0, CANOPY_Y + 0.6, PB_Z_RF), (PB_X1, PB_Y1, PB_Z_RF + 0.06),
              "A_RoofSeam", (1, 1, 1, 1))
    for k in range(int((PB_X1 - PB_X0) / 0.60) + 1):     # standing seams
        sx = PB_X0 + k * 0.60
        shell.box((sx - 0.022, CANOPY_Y + 0.6, PB_Z_RF + 0.06),
                  (sx + 0.022, PB_Y1, PB_Z_RF + 0.115), "A_RoofSeam",
                  (0.86, 0.86, 0.87, 1))
    for k in range(4):                                   # sheet laps
        ly = CANOPY_Y + 1.4 + k * 5.0
        shell.box((PB_X0, ly - 0.04, PB_Z_RF + 0.060), (PB_X1, ly + 0.04,
                  PB_Z_RF + 0.064), "A_RoofSeam", (0.74, 0.74, 0.75, 1))
    shell.box((PB_X0, CANOPY_Y + 0.6, PB_Z_RF), (PB_X1, CANOPY_Y + 0.85, PB_Z_PT),
              "A_Alu", (0.78, 0.79, 0.80, 1))
    shell.box((PB_X0, PB_Y1 - 0.25, PB_Z_RF), (PB_X1, PB_Y1, PB_Z_PT),
              "A_Alu", (0.78, 0.79, 0.80, 1))
    # ---- cores -------------------------------------------------------------
    corexs = []
    x = PB_X0
    _core(shell, rng, x, x + CORE_W[0], 'W')
    corexs.append((x, x + CORE_W[0]))
    x += CORE_W[0]
    idx = 0
    for gi, n in enumerate((4, 5, 5)):
        for k in range(n):
            x += BAY_W[idx]
            idx += 1
        if gi < 2:
            _core(shell, rng, x, x + CORE_W[gi + 1], 'M%d' % gi)
            corexs.append((x, x + CORE_W[gi + 1]))
            x += CORE_W[gi + 1]
    _core(shell, rng, PB_X1 - CORE_W[3], PB_X1, 'E')
    corexs.append((PB_X1 - CORE_W[3], PB_X1))
    # ---- per bay ------------------------------------------------------------
    for i, g in enumerate(garages):
        gr = random.Random(g['seed'])
        xa = g['x'] - g['w'] / 2
        xb = g['x'] + g['w'] / 2
        dx0 = g['x'] + g['doff'] - g['dw'] / 2 - 0.16
        dx1 = g['x'] + g['doff'] + g['dw'] / 2 + 0.16
        _pier(shell, g, gr, xa, dx0)
        _pier(shell, g, gr, dx1, xb)
        shell.box((dx0, PB_Y0 - 0.02, g['dh'] + 0.18), (dx1, PB_Y0 + 0.55,
                  PB_Z_GF - 0.4), "A_ConcPrecast", (0.96, 0.96, 0.95, 1))
        frac = _door(det, g, gr)
        if frac > 0.25:
            _interior(det, g, gr, frac)
        _header_sign(det, g, gr)
        _balcony_dress(det, g, gr)
        _pit_equipment(det, g, gr)
        # soffit downlights under the canopy, a couple dark
        for k in range(int(g['w'] / 3.5)):
            lx = xa + 1.6 + k * 3.5
            on = gr.random() < 0.82
            det.box((lx - 0.28, 21.4, PB_Z_GF - 0.45), (lx + 0.28, 22.0,
                    PB_Z_GF - 0.40), "A_EmitStrong",
                    srgb('#fff0d8') if on else (0.02, 0.02, 0.02, 1))
    # ---- rear (paddock) face: truck doors, louvres, canopy -----------------
    for i, g in enumerate(garages):
        gr = random.Random(g['seed'] ^ 0x5A5A)
        w = min(5.2, g['w'] * 0.3)
        det.box((g['x'] - w / 2, PB_Y1 - 0.38, 0.02), (g['x'] + w / 2,
                PB_Y1 - 0.30, 4.7), "A_SteelPaint",
                jitter_col(g['col1'], gr, 0.01, 0.12))
        for k in range(int(4.7 / 0.22)):
            det.box((g['x'] - w / 2, PB_Y1 - 0.31, 0.05 + k * 0.22),
                    (g['x'] + w / 2, PB_Y1 - 0.28, 0.22 + k * 0.22), "A_Alu",
                    (0.6, 0.6, 0.6, 1))
        if gr.random() < 0.5:
            det.box((g['x'] - 4.0, PB_Y1 - 0.30, 5.4), (g['x'] + 4.0,
                    PB_Y1 - 0.24, 7.6), "A_MeshDark", (1, 1, 1, 1))
        det.text("%02d" % g['num'], T(g['x'], PB_Y1 + 0.02, 5.05) @ Rz(180)
                 @ Rx(90), 0.55, "A_Sign", srgb('#dfe3e6'), extrude=0.01)
    shell.box((PB_X0, PB_Y1, 4.9), (PB_X1, PB_Y1 + 3.2, 5.15), "A_Alu",
              (0.7, 0.71, 0.72, 1))
    for k in range(int((PB_X1 - PB_X0) / 12.0)):
        px = PB_X0 + 6.0 + k * 12.0
        shell.cyl((px, PB_Y1 + 3.0, 5.15), (px, PB_Y1 + 0.4, 7.2), 0.06,
                  "A_SteelGalv", (1, 1, 1, 1), n=8)
    # ---- roof plant, per stretch between cores -----------------------------
    for a, b in ((corexs[0][1], corexs[1][0]), (corexs[1][1], corexs[2][0]),
                 (corexs[2][1], corexs[3][0])):
        _roof_plant(det, rng, a, b)
    o1 = shell.build(colls['ARCH_PitBuilding'], bevel=0.020)
    o2 = det.build(colls['ARCH_PitBuilding'], bevel=0.006)
    summary['garages'] = len(garages)
    return [o1, o2]


def build_race_control(colls, rng, summary):
    """Race control / timing tower over the S/F, plus the podium terrace.
    Deliberately NOT the same architecture as the garages: canted glazing,
    an exposed frame and a different palette, so the S/F reads at a glance."""
    mb = MB("ARCH_RaceControl")
    x0, x1 = -6.0, 34.0
    y0, y1 = 23.6, PB_Y1
    lv = [PB_Z_PT, 15.6, 19.0, 22.4, 24.4]
    for i in range(len(lv) - 1):
        z0, z1 = lv[i], lv[i + 1]
        inset = 0.0 if i < 2 else 1.2
        mb.box((x0 + inset, y0 + 1.0, z0), (x1 - inset, y1, z0 + 0.35),
               "A_ConcPrecast", (0.92, 0.92, 0.91, 1))
        # canted glazed front, leaning out over the track by 10 degrees
        lean = 0.30 * (z1 - z0)
        mb.quad((x0 + inset, y0 + 1.0, z0 + 0.35), (x1 - inset, y0 + 1.0, z0 + 0.35),
                (x1 - inset, y0 + 1.0 - lean, z1), (x0 + inset, y0 + 1.0 - lean, z1),
                "A_Glass", (1, 1, 1, 1))
        n = int((x1 - x0 - 2 * inset) / 2.2)
        for k in range(n + 1):
            px = x0 + inset + k * (x1 - x0 - 2 * inset) / n
            mb.cyl((px, y0 + 1.0, z0 + 0.35), (px, y0 + 1.0 - lean, z1), 0.06,
                   "A_Alu", (1, 1, 1, 1), n=6)
        mb.box((x0 + inset, y1 - 0.3, z0), (x1 - inset, y1, z1), "A_ConcPrecast",
               (0.90, 0.90, 0.89, 1))
        for sx in (x0 + inset, x1 - inset - 0.3):
            mb.box((sx, y0 + 1.0 - lean, z0), (sx + 0.3, y1, z1), "A_ConcPrecast",
                   (0.90, 0.90, 0.89, 1))
        mb.box((x0 + inset + 0.3, y0 + 4.0, z0 + 0.35), (x1 - inset - 0.3,
               y1 - 0.3, z1 - 0.2), "A_Spandrel", (0.25, 0.25, 0.25, 1))
    top = lv[-1]
    mb.box((x0 + 1.2, y0 + 2.2, top), (x1 - 1.2, y1, top + 0.30), "A_ConcPrecast",
           (0.92, 0.92, 0.91, 1))
    # mast + aerials
    mb.cyl((x1 - 4.0, 33.0, top), (x1 - 4.0, 33.0, top + 6.0), 0.16,
           "A_SteelGalv", (1, 1, 1, 1), n=10)
    for k in range(4):
        mb.cyl((x1 - 4.0, 33.0, top + 1.6 + k * 1.1),
               (x1 - 4.0 + 1.1 * math.cos(k * 1.9), 33.0 + 1.1 * math.sin(k * 1.9),
                top + 2.0 + k * 1.1), 0.045, "A_SteelGalv", (1, 1, 1, 1), n=6)
    # timing lights bracket facing the line
    mb.box((x0 + 12.0, y0 + 0.2, 13.4), (x0 + 20.0, y0 + 1.0, 14.6), "A_Sign",
           srgb('#17191b'))
    for k in range(12):
        mb.box((x0 + 12.3 + k * 0.62, y0 + 0.10, 13.7),
               (x0 + 12.8 + k * 0.62, y0 + 0.22, 14.3), "A_Emit",
               srgb('#ff3a12') if k % 3 else srgb('#101010'))
    mb.text("RACE CONTROL", T(x0 + 20.0, y0 + 0.9, 21.0) @ Rx(90), 1.05,
            "A_Alu", srgb('#e8ebee'), extrude=0.05)
    # podium terrace on the pit-lane side at level 1
    mb.box((x0 - 12.0, CANOPY_Y - 0.2, PB_Z_GF + 0.04), (x0 - 1.0, L1_FACE_Y,
           PB_Z_GF + 0.10), "A_Timber", (1, 1, 1, 1))
    for k in range(9):
        mb.cyl((x0 - 11.6 + k * 1.3, CANOPY_Y + 0.06, PB_Z_GF + 0.10),
               (x0 - 11.6 + k * 1.3, CANOPY_Y + 0.06, PB_Z_GF + 1.20), 0.035,
               "A_Alu", (1, 1, 1, 1), n=8)
    mb.box((x0 - 12.0, CANOPY_Y + 0.02, PB_Z_GF + 1.16), (x0 - 1.0,
           CANOPY_Y + 0.10, PB_Z_GF + 1.24), "A_Alu", (1, 1, 1, 1))
    return [mb.build(colls['ARCH_PitBuilding'], bevel=0.015)]


# --------------------------------------------------------------------------- #
#  4. START / FINISH GANTRY   (spec 9: x=0, legs y=+/-11.0, soffit z=9.00)      #
# --------------------------------------------------------------------------- #
BRANDS = [
    ("VERSANT",  '#12385e', '#e9eef2'), ("OCTAL",     '#c8442a', '#fdf6e8'),
    ("CADENCE",  '#1d1f22', '#d8b03a'), ("SEPTIME",   '#0f6b52', '#eef6f2'),
    ("PALLAS",   '#5a2d6e', '#f0e9f4'), ("TERRA NOVA", '#7a5a24', '#f6efdf'),
    ("ZEPHYR",   '#0f7fa8', '#f2fbfe'), ("BRIAR",     '#4a5a2c', '#f0f3e6'),
    ("NOVEM",    '#a01d3c', '#ffeef2'), ("ORTHO",     '#2b2f33', '#9fd6e8'),
    ("LUMIERE",  '#d8a417', '#241d10'), ("MARQUE",    '#171a1d', '#e2e5e8'),
]


def _lattice(mb, p0, p1, w, mat, col, panel=1.7, chord=0.085, diag=0.045):
    """Square lattice mast/truss between two points - real members, not a box."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    L = d.length
    z = d / L
    up = Vector((0, 0, 1)) if abs(z.z) < 0.95 else Vector((1, 0, 0))
    ex = z.cross(up).normalized() * (w * 0.5)
    ey = z.cross(ex).normalized() * (w * 0.5)
    corners = [ex + ey, ex - ey, -ex - ey, -ex + ey]
    for c in corners:
        mb.cyl(tuple(p0 + c), tuple(p1 + c), chord, mat, col, n=8)
    n = max(1, int(round(L / panel)))
    for k in range(n + 1):
        t = k / n
        base = p0 + d * t
        for i in range(4):
            a = base + corners[i]
            b = base + corners[(i + 1) % 4]
            mb.cyl(tuple(a), tuple(b), diag, mat, col, n=6)
        if k < n:
            nxt = p0 + d * ((k + 1) / n)
            for i in range(4):
                a = base + corners[i]
                b = nxt + corners[(i + 1) % 4] if (k % 2 == 0) else \
                    nxt + corners[(i + 3) % 4]
                mb.cyl(tuple(a), tuple(b), diag, mat, col, n=6)


def build_gantry(colls, rng, summary):
    mb = MB("ARCH_Gantry")
    steel = srgb('#3c4145')
    soffit, topz = 9.00, 10.80
    # The legs stand at circuit y = +-11.0, which is OUTBOARD of verge_edge
    # (10.50) and INBOARD of C.platform_edge, i.e. on build_barriers' runoff
    # platform, whose z there is -0.138 and not 0.000.  Their pad caps follow it.
    for sy in (-11.0, 11.0):
        zg = min(sit_c(-1.2, sy), sit_c(1.2, sy))
        mb.box((-1.2, sy - 1.35, zg - 0.40), (1.2, sy + 1.35, zg + 0.45),
               "A_ConcPrecast", (0.88, 0.88, 0.87, 1))
        _lattice(mb, (0, sy, zg + 0.45), (0, sy, topz), 1.30, "A_SteelPaint",
                 steel, panel=1.55)
        # ladder + cable duct on the outboard face
        o = 0.95 * (1 if sy > 0 else -1)
        for k in range(int((topz - 0.9) / 0.30)):
            mb.cyl((-0.28, sy + o, 0.9 + k * 0.30), (0.28, sy + o, 0.9 + k * 0.30),
                   0.018, "A_SteelGalv", (1, 1, 1, 1), n=5)
        for sx in (-0.28, 0.28):
            mb.cyl((sx, sy + o, 0.6), (sx, sy + o, topz - 0.2), 0.028,
                   "A_SteelGalv", (1, 1, 1, 1), n=6)
        mb.box((-0.9, sy + o * 1.15, 0.5), (-0.55, sy + o * 1.35, 6.4),
               "A_SteelGalv", (0.62, 0.62, 0.62, 1))
        mb.box((-1.0, sy + o * 1.2, 1.1), (-0.45, sy + o * 1.55, 1.9),
               "A_SteelPaint", srgb('#8a9096'))     # junction box
        # photo-finish / timing head looking across the track
        mb.box((0.55, sy - 0.35 * (1 if sy > 0 else -1), 3.6),
               (1.05, sy + 0.35 * (1 if sy > 0 else -1), 4.3), "A_SteelPaint",
               srgb('#22252a'))
        mb.cyl((1.05, sy, 3.95), (1.35, sy, 3.95), 0.11, "A_Glass",
               (1, 1, 1, 1), n=12)
    # span truss: 4 chords + verticals + alternating diagonals
    for cz in (soffit + 0.10, topz - 0.10):
        for cx in (-0.95, 0.95):
            mb.cyl((cx, -11.0, cz), (cx, 11.0, cz), 0.095, "A_SteelPaint",
                   steel, n=8)
    nb = 14
    for k in range(nb + 1):
        yy = -11.0 + 22.0 * k / nb
        for cx in (-0.95, 0.95):
            mb.cyl((cx, yy, soffit + 0.10), (cx, yy, topz - 0.10), 0.05,
                   "A_SteelPaint", steel, n=6)
        for cz in (soffit + 0.10, topz - 0.10):
            mb.cyl((-0.95, yy, cz), (0.95, yy, cz), 0.05, "A_SteelPaint",
                   steel, n=6)
        if k < nb:
            y2 = -11.0 + 22.0 * (k + 1) / nb
            for cx in (-0.95, 0.95):
                a = (cx, yy, soffit + 0.10 if k % 2 == 0 else topz - 0.10)
                b = (cx, y2, topz - 0.10 if k % 2 == 0 else soffit + 0.10)
                mb.cyl(a, b, 0.042, "A_SteelPaint", steel, n=6)
    # walkway on top, mesh deck + handrail
    mb.box((-0.62, -11.2, topz - 0.08), (0.62, 11.2, topz - 0.02), "A_MeshDark",
           (1, 1, 1, 1))
    for sx in (-0.62, 0.62):
        for hh in (0.52, 1.05):
            mb.cyl((sx, -11.2, topz + hh), (sx, 11.2, topz + hh), 0.022,
                   "A_SteelGalv", (1, 1, 1, 1), n=6)
        for k in range(12):
            yy = -11.0 + k * 2.0
            mb.cyl((sx, yy, topz - 0.02), (sx, yy, topz + 1.10), 0.022,
                   "A_SteelGalv", (1, 1, 1, 1), n=6)
    # start light pods: five, hung under the soffit
    mb.box((-0.55, -5.2, soffit - 0.35), (0.55, 5.2, soffit - 0.10),
           "A_SteelPaint", srgb('#1b1d20'))
    for k in range(5):
        yy = -4.0 + k * 2.0
        mb.box((-0.42, yy - 0.44, soffit - 1.95), (0.42, yy + 0.44, soffit - 0.35),
               "A_SteelPaint", srgb('#141618'))
        for r in range(2):
            zz = soffit - 1.62 + r * 0.72
            mb.cyl((-0.43, yy, zz), (-0.50, yy, zz), 0.26, "A_Emit",
                   (0.015, 0.008, 0.008, 1), n=16)
            mb.cyl((-0.42, yy, zz), (-0.46, yy, zz), 0.30, "A_SteelPaint",
                   srgb('#0d0e10'), n=16)
    # repeater panel facing back up the pit lane
    mb.box((0.42, 6.4, soffit - 1.30), (0.60, 9.4, soffit - 0.30), "A_Sign",
           srgb('#101214'))
    for k in range(6):
        mb.box((0.60, 6.6 + k * 0.5, soffit - 1.05), (0.66, 6.95 + k * 0.5,
               soffit - 0.55), "A_Emit",
               srgb('#ffbb22') if k % 2 else (0.01, 0.01, 0.01, 1))
    # TV camera pods
    for yy, ang in ((-6.6, -18.0), (4.8, 12.0)):
        mb.cyl((0.0, yy, soffit - 0.10), (0.0, yy, soffit - 0.55), 0.07,
               "A_SteelGalv", (1, 1, 1, 1), n=8)
        m = T(0.0, yy, soffit - 0.78) @ Rz(ang) @ Rx(-8.0)
        mb.xbox(m, (0.34, 0.78, 0.34), "A_SteelPaint", srgb('#26292c'))
        mb.cyl(tuple(m @ Vector((0, -0.40, 0))), tuple(m @ Vector((0, -0.52, 0))),
               0.11, "A_Glass", (1, 1, 1, 1), n=12)
    # the banner: circuit name on the track face, START/FINISH on the pit face
    mb.box((-1.12, -11.0, soffit + 0.22), (-1.04, 11.0, topz - 0.22), "A_Sign",
           srgb('#101317'))
    mb.text("CIRCUIT VITRINE", T(-1.20, 0.6, soffit + 1.05) @ Rz(-90) @ Rx(90),
            0.80, "A_Sign", srgb('#eef1f4'), extrude=0.02)
    for k in range(22):                      # chequer band, two rows
        for r in range(2):
            if (k + r) % 2:
                continue
            mb.box((-1.20, -11.0 + k, soffit + 0.30 + r * 0.26),
                   (-1.16, -10.0 + k, soffit + 0.56 + r * 0.26), "A_Sign",
                   srgb('#eef1f4'))
    mb.box((1.04, -11.0, soffit + 0.22), (1.12, 11.0, topz - 0.22), "A_Sign",
           srgb('#141719'))
    mb.text("START / FINISH", T(1.20, 0.0, soffit + 1.05) @ Rz(90) @ Rx(90),
            0.80, "A_Sign", srgb('#e8ebef'), extrude=0.02)
    # two flags on the leg tops, cloth with a real fall
    for sy, phase in ((-11.0, 0.0), (11.0, 1.3)):
        mb.cyl((0, sy, topz), (0, sy, topz + 4.2), 0.055, "A_Alu", (1, 1, 1, 1),
               n=8)
        c = jitter_col(srgb('#c9ccd0'), rng, 0.02, 0.1)
        for k in range(10):
            t0, t1 = k / 10.0, (k + 1) / 10.0
            w0 = 1.9 * t0
            w1 = 1.9 * t1
            s0 = 0.28 * math.sin(t0 * 5.0 + phase)
            s1 = 0.28 * math.sin(t1 * 5.0 + phase)
            mb.quad((0.05 + w0, sy + s0, topz + 4.15 - 0.10 * t0),
                    (0.05 + w1, sy + s1, topz + 4.15 - 0.10 * t1),
                    (0.05 + w1, sy + s1, topz + 3.05 - 0.30 * t1),
                    (0.05 + w0, sy + s0, topz + 3.05 - 0.30 * t0), "A_Fabric", c)
    summary['gantry_soffit_z'] = soffit
    return [mb.build(colls['ARCH_Gantry'], bevel=0.010)]


# --------------------------------------------------------------------------- #
#  5. PIT WALL + PIT-WALL STANDS  (spec 10.7: y=+11.5, x=-245..+130, 1.2 m)     #
# --------------------------------------------------------------------------- #
def build_pit_wall(colls, rng, summary):
    """The pit wall is the CONTRACT's own barrier line on the left of the pit
    straight: C.barrier_offset(s, +1) is pinned to circuit y = +11.5 there and
    C.barrier_type() is B_CONCRETE, so this wall's TRACK FACE has to be on
    +11.5 exactly, not the 0.175 m inboard of it that it used to be.

    Its base follows C.ground_z, which along the wall line is -0.117..-0.146:
    the old wall started at z = 0.000 and hung 130 mm clear of the ground it is
    supposed to be cast into, over 375 m.  Its TOP stays level at +1.20 above
    the declared pit-lane deck, because a pit wall is set out from the pit lane
    — which is why it reads 1.33 m from the track and 1.20 m from the boxes."""
    mb = MB("ARCH_PitWall")
    y0, y1 = WC.PIT_WALL_Y, WC.PIT_WALL_Y + 0.35        # face ON the contract pin
    gaps = [(-1.9, 1.9), (96.0, 101.0)]     # gantry leg, pit entry
    # WEST END — DEFECT #46, AND IT IS THE CONTRACT'S NUMBER NOW, NOT THIS FILE'S.
    #
    # v1.0.x of this function had already found half of the defect by hand and
    # moved its own west end to a hard-coded circuit x = -228.0 with a 4.2 m
    # tapered nose.  It was not enough and it was not checked: the nose tapers in
    # HEIGHT ONLY, so its face is still on PIT_WALL_Y, and the placement gate
    # measured that nose 1.067 m inside the car's swept volume at world
    # (144.282, 29.425) with the car doing 207.0 km/h.
    #
    # The contract derives the station from `access_edges` now — the wall's nose
    # goes exactly where the pit-exit road's outboard edge comes inboard of
    # PIT_WALL_Y, s = 3447.71, circuit x = -227.29 — and publishes the terminal's
    # LENGTH and its LATERAL FLARE, because the nose is the thing that has to be
    # clear and a module that guessed either number would put it somewhere the
    # contract never checked.  See world_contract §10a.
    #
    #   nose face      PIT_WALL_Y + 0.60 = 12.10 at circuit x -227.29
    #   running face   PIT_WALL_Y        = 11.50 from circuit x -222.29
    #
    # MEASURED against telemetry.csv: worst car clearance over the whole wall span
    # is now +1.738 m (frame 141, s = 3449.84), and the wall face clears the
    # ribbon's outboard edge by at least 0.320 m for its whole 357 m.
    PIT_WALL_X0 = float(WC.PIT_WALL_X0)                  # -222.291
    TERM_L = float(WC.PIT_WALL_TERMINAL_M)               # 5.0
    TERM_F = float(WC.PIT_WALL_TERMINAL_FLARE_M)         # 0.60
    X_NOSE = PIT_WALL_X0 - TERM_L                        # -227.291 = the contract's
    x = PIT_WALL_X0
    unit = 0
    base_lo, base_hi = 9.9, -9.9
    zt0 = sit_c(X_NOSE, y0 + TERM_F) - EMBED
    NTERM = 7
    for k in range(NTERM):                   # flared terminal, cast in situ
        t0, t1 = k / float(NTERM), (k + 1) / float(NTERM)
        fy = TERM_F * (1.0 - t0)             # each unit set out on its west end,
        mb.box((X_NOSE + TERM_L * t0, y0 + fy, zt0),   # so the run reads as a
               (X_NOSE + TERM_L * t1 + 0.02, y1 + fy,  # stepped taper, which is
                0.18 + 1.02 * t1),                     # what precast terminal
               "A_ConcPrecast", (0.90 + 0.04 * (k % 3), 0.90, 0.89, 1))  # units are
    mb.box((X_NOSE - 0.40, y0 + TERM_F - 0.10, zt0 - 0.05),
           (X_NOSE + 0.60, y1 + TERM_F + 0.10, zt0 + 0.16), "A_ConcPrecast",
           (0.84, 0.84, 0.83, 1))
    for k in range(3):                       # chevron board on the nose
        mb.box((X_NOSE - 0.35, y0 + TERM_F - 0.06, 0.20 + k * 0.30),
               (X_NOSE + 0.15, y0 + TERM_F - 0.04, 0.44 + k * 0.30), "A_Sign",
               srgb('#e0b21f') if k % 2 else srgb('#1b1d20'))
    while x < 130.0:
        L = 3.0 if unit % 5 else 2.4         # every fifth unit is a short one
        xe = min(x + L, 130.0)
        skip = any(xe > g0 and x < g1 for g0, g1 in gaps)
        if not skip:
            zg = min(sit_c(x, y0), sit_c(xe, y0)) - EMBED
            base_lo, base_hi = min(base_lo, zg), max(base_hi, zg)
            h = 1.20 + rng.uniform(-0.012, 0.012)
            tilt = rng.uniform(-0.004, 0.004)
            mb.box((x + 0.02, y0 + tilt, zg), (xe - 0.02, y1 + tilt, h),
                   "A_ConcPrecast", (0.93 + rng.uniform(-0.05, 0.05), 0.93, 0.92, 1))
            mb.box((x + 0.0, y0 - 0.04 + tilt, h), (xe, y1 + 0.04 + tilt, h + 0.05),
                   "A_ConcPrecast", (0.86, 0.86, 0.85, 1))
        x = xe
        unit += 1
    summary['pit_wall_base_z'] = [round(base_lo, 4), round(base_hi, 4)]
    # return walls around the gantry leg and the pit entry
    for gx in (-1.9, 1.9, 96.0, 101.0):
        mb.box((gx - 0.18, y0, sit_c(gx, y0 + 0.9) - EMBED),
               (gx + 0.18, y0 + 1.9, 1.25),
               "A_ConcPrecast", (0.9, 0.9, 0.89, 1))
    # advertising panels on the track face - fictional brands, varied art,
    # varied wear, and three panels deliberately blank or peeling
    px = PIT_WALL_X0 + 1.0
    bi = 0
    while px < 128.0:
        w = rng.choice((6.0, 8.0, 8.0, 10.0, 12.0))
        if px + w > 128.0:
            break
        if any(px + w > g0 and px < g1 for g0, g1 in gaps):
            px += w
            continue
        name, c1, c2 = BRANDS[bi % len(BRANDS)]
        base = jitter_col(srgb(c1), rng, 0.012, 0.08)
        fg = srgb(c2)
        state = rng.random()
        mb.box((px + 0.12, y0 - 0.035, 0.16), (px + w - 0.12, y0, 1.10),
               "A_Sign", base if state > 0.12 else srgb('#8f9296'))
        if state > 0.12:
            mark = bi % 4
            if mark == 0:
                mb.box((px + 0.5, y0 - 0.05, 0.30), (px + 1.3, y0 - 0.036, 0.96),
                       "A_Sign", fg)
            elif mark == 1:
                mb.cyl((px + 0.95, y0 - 0.05, 0.63), (px + 0.95, y0 - 0.036, 0.63),
                       0.33, "A_Sign", fg, n=20)
            elif mark == 2:
                for k in range(3):
                    mb.box((px + 0.45 + k * 0.28, y0 - 0.05, 0.30 + k * 0.10),
                           (px + 0.65 + k * 0.28, y0 - 0.036, 0.96), "A_Sign", fg)
            mb.text(name, T(px + w * 0.58, y0 - 0.06, 0.63) @ Rx(90), 0.42,
                    "A_Sign", fg, extrude=0.004)
        if state < 0.06:                    # a corner peeled away
            mb.quad((px + w - 1.4, y0 - 0.04, 1.10), (px + w - 0.12, y0 - 0.04, 1.10),
                    (px + w - 0.12, y0 - 0.22, 0.72), (px + w - 1.1, y0 - 0.16, 0.86),
                    "A_Sign", srgb('#cfd2d5'))
        px += w
        bi += 1
    # ---- five pit-wall stands, no two alike --------------------------------
    picks = [1, 3, 6, 9, 12]
    for si, ti in enumerate(picks):
        team, c1, c2 = TEAMS[ti]
        gr = random.Random(9000 + si * 37)
        x0 = -196.0 + si * 62.0 + gr.uniform(-6, 6)
        L = gr.uniform(7.0, 10.5)
        tiers = gr.randint(1, 2)
        col = jitter_col(srgb(c1), gr, 0.01, 0.08)
        for t in range(tiers):
            zz = 1.30 + t * 0.62
            # the stands stand on the PIT LANE DECK, so their feet start at
            # C.platform_edge(+1) = 12.10, not at 11.9 where the ground is still
            # the road programme's and 135 mm lower than the deck
            yy0 = 12.25 + t * 1.15
            mb.box((x0, yy0, zz - 0.14), (x0 + L, yy0 + 1.25, zz), "A_MeshDark",
                   (1, 1, 1, 1))
            for k in range(int(L / 1.8) + 1):
                mb.cyl((x0 + 0.3 + k * 1.8, yy0 + 0.2, APRON_Z - EMBED),
                       (x0 + 0.3 + k * 1.8, yy0 + 0.2, zz - 0.14), 0.05,
                       "A_SteelGalv", (1, 1, 1, 1), n=8)
                mb.cyl((x0 + 0.3 + k * 1.8, yy0 + 1.05, APRON_Z - EMBED),
                       (x0 + 0.3 + k * 1.8, yy0 + 1.05, zz - 0.14), 0.05,
                       "A_SteelGalv", (1, 1, 1, 1), n=8)
            ns = int(L / 0.78)
            for k in range(ns):
                sx = x0 + 0.45 + k * 0.78
                if gr.random() < 0.18:
                    continue                 # gaps where nobody is sitting
                mb.xbox(T(sx, yy0 + 0.55, zz + 0.24) @ Rz(gr.uniform(-9, 9)),
                        (0.52, 0.50, 0.08), "A_Seat", col)
                mb.xbox(T(sx, yy0 + 0.80, zz + 0.50) @ Rz(gr.uniform(-9, 9)),
                        (0.52, 0.08, 0.46), "A_Seat", col)
                for lx in (-0.2, 0.2):
                    mb.cyl((sx + lx, yy0 + 0.55, zz), (sx + lx, yy0 + 0.55, zz + 0.20),
                           0.02, "A_Alu", (1, 1, 1, 1), n=5)
        # monitor bank
        nm = gr.randint(5, 11)
        for k in range(nm):
            mx = x0 + 0.6 + k * (L - 1.2) / max(1, nm - 1)
            on = gr.random() < 0.8
            mb.xbox(T(mx, 11.82, 1.98) @ Rx(-12), (0.44, 0.05, 0.30), "A_Emit",
                    srgb('#7fb4d8') if on else (0.01, 0.01, 0.012, 1))
            mb.xbox(T(mx, 11.86, 1.98) @ Rx(-12), (0.48, 0.05, 0.34),
                    "A_SteelPaint", srgb('#1b1d1f'))
        mb.box((x0, 11.78, 1.60), (x0 + L, 11.90, 1.72), "A_SteelGalv",
               (0.6, 0.6, 0.6, 1))
        # canopy: deployed / folded / none
        cst = gr.random()
        if cst < 0.45:
            mb.box((x0 - 0.2, 11.7, 2.95), (x0 + L + 0.2, 14.4, 3.05), "A_Fabric",
                   col)
            for k in (0.4, L - 0.4):
                mb.cyl((x0 + k, 14.2, 0.0), (x0 + k, 14.2, 2.98), 0.06, "A_Alu",
                       (1, 1, 1, 1), n=8)
            mb.text(team, T(x0 + L * 0.5, 11.66, 2.72) @ Rx(90), 0.34, "A_Sign",
                    srgb(c2), extrude=0.004)
        elif cst < 0.72:
            mb.cyl((x0 + 0.4, 14.2, 0.0), (x0 + 0.4, 14.2, 3.1), 0.06, "A_Alu",
                   (1, 1, 1, 1), n=8)
            mb.cyl((x0 + 0.4, 14.2, 3.1), (x0 + L - 0.4, 14.3, 2.55), 0.14,
                   "A_Fabric", col, n=10)     # rolled and lashed
        # ladder, cooler, cable spool - different set on each stand
        mb.box((x0 - 0.6, 12.2, 0.0), (x0 - 0.35, 13.4, 1.35), "A_SteelGalv",
               (0.65, 0.65, 0.65, 1))
        if gr.random() < 0.7:
            mb.xbox(T(x0 + gr.uniform(1, L - 1), 15.1, 0.28) @ Rz(gr.uniform(-30, 30)),
                    (0.9, 0.6, 0.56), "A_SteelPaint", jitter_col(srgb(c2), gr, 0.02, 0.2))
        if gr.random() < 0.6:
            sx = x0 + gr.uniform(0.5, L - 0.5)
            mb.cyl((sx, 15.8, 0.30), (sx, 16.3, 0.30), 0.30, "A_SteelPaint",
                   srgb('#3c4045'), n=14)
    summary['pit_wall_stands'] = len(picks)
    return [mb.build(colls['ARCH_PitWall'], bevel=0.008)]


# --------------------------------------------------------------------------- #
#  6. GRANDSTANDS  (spec 10.6/10.7: y=-34..-62, x=-420..+180, 14.0 m HARD CAP)  #
# --------------------------------------------------------------------------- #
# The Beat-6 camera passes 13.8 m above this roofline at circuit (-62,-53,27.8)
# and the Beat-6 hold ray to the wound crosses the band 29 m above it, so 14.0 m
# is a structural constraint, not a style choice.  Every block below is built to
# a computed top height and the whole collection is measured afterwards by
# verify_sightlines(); the build fails loudly if anything reaches 13.9 m.
GS_FRONT = -34.0
GS_BACK = -62.0
GS_CAP = 14.0

FONT57 = {
    'A': '.###./#...#/#...#/#####/#...#/#...#/#...#',
    'B': '####./#...#/####./#...#/#...#/#...#/####.',
    'C': '.###./#...#/#..../#..../#..../#...#/.###.',
    'D': '####./#...#/#...#/#...#/#...#/#...#/####.',
    'E': '#####/#..../#..../###../#..../#..../#####',
    'I': '#####/..#../..#../..#../..#../..#../#####',
    'N': '#...#/##..#/##..#/#.#.#/#..##/#..##/#...#',
    'O': '.###./#...#/#...#/#...#/#...#/#...#/.###.',
    'R': '####./#...#/#...#/####./#.#../#..#./#...#',
    'S': '.####/#..../#..../.###./....#/....#/####.',
    'T': '#####/..#../..#../..#../..#../..#../..#..',
    'U': '#...#/#...#/#...#/#...#/#...#/#...#/.###.',
    'V': '#...#/#...#/#...#/#...#/#...#/.#.#./..#..',
    ' ': '...../...../...../...../...../...../.....',
}

GS_BLOCKS = [
    dict(name='TRIBUNE OUEST', x0=-420.0, x1=-330.0, rows=20, tread=0.92,
         rise=0.345, roof='none', frame='concrete', pattern='letters',
         word='VITRINE', seat=0, base='#2c3e4c', accent='#d8dde0',
         aisle=11.0, voms=2),
    dict(name='TRIBUNE T15', x0=-318.0, x1=-214.0, rows=24, tread=0.86,
         rise=0.335, roof='rear', frame='steel', pattern='stripe', word='',
         seat=2, base='#1f4f6d', accent='#7fb2c8', aisle=9.5, voms=3),
    dict(name='VIRAGE OUEST', x0=-202.0, x1=-130.0, rows=18, tread=0.95,
         rise=0.355, roof='none', frame='tube', pattern='chequer', word='',
         seat=1, base='#3c4348', accent='#c9a227', aisle=12.0, voms=2),
    dict(name='TRIBUNE PRINCIPALE', x0=-118.0, x1=42.0, rows=22, tread=0.88,
         rise=0.335, roof='full', frame='steel', pattern='letters',
         word='CIRCUIT VITRINE', seat=0, base='#22282d', accent='#e2e6e9',
         aisle=10.0, voms=4),
    dict(name='TRIBUNE EST', x0=54.0, x1=126.0, rows=21, tread=0.90,
         rise=0.340, roof='rear', frame='concrete', pattern='gradient',
         word='', seat=2, base='#2e5b3a', accent='#7fa886', aisle=10.5, voms=2),
    dict(name='TRIBUNE TEMPORAIRE', x0=138.0, x1=180.0, rows=14, tread=0.82,
         rise=0.330, roof='none', frame='scaffold', pattern='speckle',
         word='', seat=3, base='#8a8f93', accent='#c8552a', aisle=14.0, voms=1),
]


def _seat_colour(blk, ci, ri, ncol, nrow, rng):
    base = srgb(blk['base'])
    acc = srgb(blk['accent'])
    p = blk['pattern']
    hit = False
    if p == 'letters':
        word = blk['word']
        px_w, px_h = 2, 2                      # one font pixel = 2 seats x 2 rows
        lw = 5 * px_w + 2 * px_w               # letter + spacing
        total = len(word) * lw
        c0 = (ncol - total) // 2
        r0 = max(1, (nrow - 7 * px_h) // 2)
        li = (ci - c0) // lw
        if 0 <= li < len(word) and (ci - c0) >= 0:
            lx = ((ci - c0) % lw) // px_w
            ly = (ri - r0) // px_h
            if 0 <= lx < 5 and 0 <= ly < 7:
                pat = FONT57.get(word[li], FONT57[' ']).split('/')
                if pat[6 - ly][lx] == '#':
                    hit = True
    elif p == 'stripe':
        hit = (ri // 3) % 2 == 0
    elif p == 'chequer':
        hit = ((ci // 4) + (ri // 4)) % 2 == 0
    elif p == 'gradient':
        hit = rng.random() < (ri / max(1, nrow - 1)) ** 1.6
    else:
        hit = rng.random() < 0.09
    c = acc if hit else base
    return jitter_col(c, rng, 0.010, 0.075)


def _seat(mb, m, kind, col, folded, rng):
    """Four seat archetypes; tip-up types fold at the rear hinge."""
    if kind == 3:                              # plank bench (temporary stand)
        mb.xbox(m @ T(0, 0.05, 0.42), (0.78, 0.30, 0.045), "A_Timber", col)
        return
    if kind == 0:                              # bucket with side wings
        if folded:
            mb.xbox(m @ T(0, 0.20, 0.60) @ Rx(-76), (0.44, 0.44, 0.05),
                    "A_Seat", col)
        else:
            mb.xbox(m @ T(0, 0, 0.42), (0.44, 0.44, 0.05), "A_Seat", col)
            mb.xbox(m @ T(0, -0.21, 0.45), (0.44, 0.06, 0.09), "A_Seat", col)
        mb.xbox(m @ T(0, 0.22, 0.62) @ Rx(-9), (0.44, 0.045, 0.40), "A_Seat", col)
        for sx in (-0.215, 0.215):
            mb.xbox(m @ T(sx, 0.10, 0.50), (0.04, 0.30, 0.16), "A_Seat", col)
    elif kind == 1:                            # flat pad, tubular frame
        mb.xbox(m @ T(0, 0, 0.40), (0.46, 0.40, 0.04), "A_Seat", col)
        mb.xbox(m @ T(0, 0.21, 0.58) @ Rx(-6), (0.46, 0.035, 0.32), "A_Seat", col)
    else:                                      # moulded shell, three facets
        if folded:
            mb.xbox(m @ T(0, 0.20, 0.60) @ Rx(-78), (0.45, 0.40, 0.055),
                    "A_Seat", col)
        else:
            mb.xbox(m @ T(0, -0.02, 0.41), (0.45, 0.34, 0.055), "A_Seat", col)
            mb.xbox(m @ T(0, 0.16, 0.44) @ Rx(20), (0.45, 0.14, 0.05), "A_Seat", col)
        mb.xbox(m @ T(0, 0.235, 0.58) @ Rx(-12), (0.45, 0.05, 0.34), "A_Seat", col)
        mb.xbox(m @ T(0, 0.20, 0.76) @ Rx(-24), (0.42, 0.05, 0.14), "A_Seat", col)
    for sx in (-0.17, 0.17):                   # standards
        mb.cyl(tuple(m @ Vector((sx, 0.16, 0.0))),
               tuple(m @ Vector((sx, 0.16, 0.44))), 0.018, "A_Alu",
               (0.55, 0.55, 0.55, 1), n=5)


def _grandstand_block(mb, blk, rng, summary):
    x0, x1 = blk['x0'], blk['x1']
    L = x1 - x0
    rows, tread, rise = blk['rows'], blk['tread'], blk['rise']
    front_deck = 2.40
    walk_d = 2.60                              # front walkway depth
    y_first = GS_FRONT - walk_d
    top_z = front_deck + rows * rise
    # ---- front fascia + advertising band -----------------------------------
    mb.box((x0, GS_FRONT - 0.35, -0.30), (x1, GS_FRONT, front_deck + 1.05),
           "A_ConcPrecast", (0.9, 0.9, 0.89, 1))
    px = x0 + 0.5
    bi = rng.randint(0, 11)
    while px < x1 - 6.0:
        w = rng.choice((9.0, 12.0, 12.0, 15.0))
        name, c1, c2 = BRANDS[bi % len(BRANDS)]
        mb.box((px, GS_FRONT, 0.75), (px + w - 0.3, GS_FRONT + 0.04, 2.05),
               "A_Sign", jitter_col(srgb(c1), rng, 0.01, 0.08))
        mb.text(name, T(px + w * 0.5, GS_FRONT + 0.10, 1.40) @ Rz(180) @ Rx(90),
                0.60, "A_Sign", srgb(c2), extrude=0.004)
        px += w
        bi += 1
    # ---- front walkway + rail ----------------------------------------------
    mb.box((x0, y_first, front_deck - 0.18), (x1, GS_FRONT, front_deck),
           "A_ConcPrecast", (0.95, 0.95, 0.94, 1))
    for hh in (0.50, 1.02):
        mb.cyl((x0, GS_FRONT - 0.12, front_deck + hh),
               (x1, GS_FRONT - 0.12, front_deck + hh), 0.024, "A_SteelGalv",
               (1, 1, 1, 1), n=6)
    for k in range(int(L / 2.2) + 1):
        mb.cyl((x0 + k * 2.2, GS_FRONT - 0.12, front_deck),
               (x0 + k * 2.2, GS_FRONT - 0.12, front_deck + 1.08), 0.024,
               "A_SteelGalv", (1, 1, 1, 1), n=6)
    # ---- aisles and vomitories --------------------------------------------
    naisle = max(1, int(round(L / blk['aisle'])))
    aisles = [x0 + (k + 0.5) * L / naisle for k in range(naisle)]
    aw = 1.25
    voms = [x0 + (k + 0.5) * L / blk['voms'] for k in range(blk['voms'])]
    vom_row = max(2, rows // 3)
    # ---- the rake: risers, treads, seats -----------------------------------
    seatn = 0
    for r in range(rows):
        yb = y_first - r * tread
        yf = yb - tread
        z0 = front_deck + r * rise
        z1 = z0 + rise
        mb.box((x0, yf, z0), (x1, yb, z0 + 0.16), "A_ConcPrecast",
               (0.93 + 0.04 * ((r * 5) % 3) / 3.0, 0.93, 0.92, 1))     # tread
        mb.box((x0, yf - 0.16, z0), (x1, yf, z1), "A_ConcPrecast",
               (0.90, 0.90, 0.89, 1))                                  # riser
        # seats between the aisles
        ncol = int(L / 0.50)
        for c in range(ncol):
            sx = x0 + 0.25 + c * 0.50
            if any(abs(sx - ax) < aw * 0.5 + 0.18 for ax in aisles):
                continue
            if r < vom_row + 2 and any(abs(sx - vx) < 1.5 for vx in voms) \
                    and r >= vom_row:
                continue
            col = _seat_colour(blk, c, r, ncol, rows, rng)
            folded = rng.random() < 0.22 and blk['seat'] in (0, 2)
            if rng.random() < 0.006:
                continue                        # a seat missing from the row
            # Rz(180): the rake runs toward -y, so the seats must face +y,
            # i.e. toward the track.  Without this every seat faces the back
            # wall - it was exactly that in the first test render.
            _seat(mb, T(sx, yb - tread * 0.42, z0 + 0.16) @ Rz(180),
                  blk['seat'], col, folded, rng)
            seatn += 1
    # aisle steps (two half-risers per row) + handrails
    for ax in aisles:
        for r in range(rows):
            yb = y_first - r * tread
            z0 = front_deck + r * rise
            for h in range(2):
                mb.box((ax - aw / 2, yb - tread * (h + 1) / 2, z0 + rise * h / 2),
                       (ax + aw / 2, yb - tread * h / 2, z0 + rise * (h + 1) / 2),
                       "A_ConcPrecast", (0.97, 0.97, 0.96, 1))
        for sx in (ax - aw / 2 - 0.06, ax + aw / 2 + 0.06):
            for r in range(0, rows - 1, 4):
                y_a = y_first - r * tread
                y_b = y_first - (r + 4) * tread
                z_a = front_deck + r * rise + 1.0
                z_b = front_deck + (r + 4) * rise + 1.0
                mb.cyl((sx, y_a, z_a), (sx, y_b, z_b), 0.024, "A_SteelGalv",
                       (1, 1, 1, 1), n=6)
                mb.cyl((sx, y_b, z_b - 1.0), (sx, y_b, z_b), 0.024,
                       "A_SteelGalv", (1, 1, 1, 1), n=6)
    # vomitory openings: hole in the deck, stair down, balustrade around
    for vx in voms:
        yb = y_first - vom_row * tread
        z0 = front_deck + vom_row * rise
        mb.box((vx - 1.5, yb - 2 * tread, z0 - 3.0), (vx + 1.5, yb, z0 - 2.85),
               "A_ConcPrecast", (0.88, 0.88, 0.87, 1))
        for s in range(9):
            mb.box((vx - 1.4, yb - 2 * tread + s * 0.26, z0 - 2.85 + s * 0.33),
                   (vx + 1.4, yb - 2 * tread + (s + 1) * 0.26,
                    z0 - 2.72 + s * 0.33), "A_ConcPrecast", (0.95, 0.95, 0.94, 1))
        for sx in (vx - 1.6, vx + 1.6):
            for hh in (0.55, 1.05):
                mb.cyl((sx, yb - 2 * tread, z0 + hh), (sx, yb + 0.2, z0 + hh),
                       0.024, "A_SteelGalv", (1, 1, 1, 1), n=6)
            mb.cyl((sx, yb + 0.2, z0), (sx, yb + 0.2, z0 + 1.08), 0.024,
                   "A_SteelGalv", (1, 1, 1, 1), n=6)
    # ---- undercroft structure ----------------------------------------------
    y_back = y_first - rows * tread
    frame = blk['frame']
    nb = max(2, int(L / 6.0))
    for k in range(nb + 1):
        bx = x0 + k * L / nb
        if frame == 'concrete':
            mb.beam((bx, GS_FRONT - 0.2, front_deck - 0.35),
                    (bx, y_back, top_z - 0.35), 0.42, 0.65, "A_ConcPrecast",
                    (0.86, 0.86, 0.85, 1))
            for cy, cz in ((GS_FRONT - 4.0, front_deck - 0.5),
                           ((GS_FRONT + y_back) * 0.5, (front_deck + top_z) * 0.5),
                           (y_back + 1.0, top_z - 0.6)):
                mb.box((bx - 0.28, cy - 0.28, 0.0), (bx + 0.28, cy + 0.28, cz),
                       "A_ConcPrecast", (0.88, 0.88, 0.87, 1))
        elif frame == 'steel':
            mb.beam((bx, GS_FRONT - 0.2, front_deck - 0.32),
                    (bx, y_back, top_z - 0.32), 0.30, 0.55, "A_SteelPaint",
                    srgb('#4a5054'))
            for cy in (GS_FRONT - 5.0, (GS_FRONT + y_back) * 0.5, y_back + 1.2):
                zt = front_deck + rise * (GS_FRONT - cy - walk_d) / tread - 0.5
                zt = max(1.2, min(top_z - 0.5, zt))
                mb.cyl((bx, cy, 0.0), (bx, cy, zt), 0.16, "A_SteelPaint",
                       srgb('#4a5054'), n=10)
            if k < nb:                                    # cross bracing
                bx2 = x0 + (k + 1) * L / nb
                cy = (GS_FRONT + y_back) * 0.5
                mb.cyl((bx, cy, 0.4), (bx2, cy, (front_deck + top_z) * 0.5 - 0.7),
                       0.055, "A_SteelPaint", srgb('#4a5054'), n=6)
                mb.cyl((bx2, cy, 0.4), (bx, cy, (front_deck + top_z) * 0.5 - 0.7),
                       0.055, "A_SteelPaint", srgb('#4a5054'), n=6)
        elif frame == 'tube':
            mb.beam((bx, GS_FRONT - 0.2, front_deck - 0.30),
                    (bx, y_back, top_z - 0.30), 0.26, 0.42, "A_SteelGalv",
                    (1, 1, 1, 1))
            for cy in (GS_FRONT - 6.0, y_back + 2.0):
                zt = front_deck + rise * (GS_FRONT - cy - walk_d) / tread - 0.45
                zt = max(1.2, min(top_z - 0.45, zt))
                mb.cyl((bx, cy, 0.0), (bx, cy, zt), 0.13, "A_SteelGalv",
                       (1, 1, 1, 1), n=10)
                mb.cyl((bx, cy, zt * 0.55), (bx, cy - 3.0, zt * 0.2), 0.07,
                       "A_SteelGalv", (1, 1, 1, 1), n=6)
        else:                                             # scaffold stand
            for cy in [GS_FRONT - 2.0 - j * 2.4 for j in range(int(
                    (GS_FRONT - y_back) / 2.4))]:
                zt = front_deck + rise * (GS_FRONT - cy - walk_d) / tread
                zt = max(0.8, min(top_z, zt))
                mb.cyl((bx, cy, 0.0), (bx, cy, zt), 0.049, "A_SteelGalv",
                       (1, 1, 1, 1), n=8)
                for lz in [1.0 + j * 2.0 for j in range(int(zt / 2.0))]:
                    mb.cyl((bx, cy, lz), (bx, cy - 2.4, lz), 0.049, "A_SteelGalv",
                           (1, 1, 1, 1), n=6)
                    if k < nb:
                        mb.cyl((bx, cy, lz), (x0 + (k + 1) * L / nb, cy, lz),
                               0.049, "A_SteelGalv", (1, 1, 1, 1), n=6)
    # rear wall / gallery
    mb.box((x0, y_back - 0.30, 0.0), (x1, y_back, top_z + 0.35),
           "A_ConcPrecast" if frame != 'scaffold' else "A_MeshScreen",
           (0.88, 0.88, 0.87, 1))
    for hh in (0.55, 1.10):
        mb.cyl((x0, y_back + 0.05, top_z + hh), (x1, y_back + 0.05, top_z + hh),
               0.024, "A_SteelGalv", (1, 1, 1, 1), n=6)
    rail_top = top_z + 1.10
    # ---- roof ---------------------------------------------------------------
    roof_top = 0.0
    if blk['roof'] != 'none':
        # fraction of the rake covered, measured back to front
        cover_front = y_back + (y_first - y_back) * (0.55 if blk['roof'] == 'rear'
                                                     else 0.95)
        soffit = top_z + 2.35
        depth = 1.05
        roof_top = soffit + depth + 0.22
        # hard cap: leave 0.75 m of headroom for seams, walkway and vent cowls
        if roof_top > GS_CAP - 0.75:
            over = roof_top - (GS_CAP - 0.75)
            soffit -= over
            roof_top = GS_CAP - 0.75
        ncol = max(2, int(L / 9.0))
        for k in range(ncol + 1):
            cx = x0 + k * L / ncol
            mb.cyl((cx, y_back - 0.1, 0.0), (cx, y_back - 0.1, soffit + depth),
                   0.19, "A_SteelPaint", srgb('#41474b'), n=12)
            # cantilever truss forward
            mb.cyl((cx, y_back - 0.1, soffit), (cx, cover_front, soffit + 0.35),
                   0.12, "A_SteelPaint", srgb('#41474b'), n=8)
            mb.cyl((cx, y_back - 0.1, soffit + depth), (cx, cover_front,
                   soffit + depth), 0.12, "A_SteelPaint", srgb('#41474b'), n=8)
            nd = max(2, int(abs(cover_front - y_back) / 2.2))
            for j in range(nd + 1):
                t0 = j / nd
                yy = y_back - 0.1 + (cover_front - y_back + 0.1) * t0
                zz = soffit + 0.35 * t0
                mb.cyl((cx, yy, zz), (cx, yy, soffit + depth), 0.06,
                       "A_SteelPaint", srgb('#41474b'), n=6)
                if j < nd:
                    t1 = (j + 1) / nd
                    y2 = y_back - 0.1 + (cover_front - y_back + 0.1) * t1
                    mb.cyl((cx, yy, zz), (cx, y2, soffit + depth), 0.045,
                           "A_SteelPaint", srgb('#41474b'), n=6)
            # back-stay to the rear wall foot
            mb.cyl((cx, y_back - 0.1, soffit + depth), (cx, y_back - 3.2, 0.0),
                   0.075, "A_SteelPaint", srgb('#41474b'), n=8)
        # purlins + standing-seam deck + gutter + fascia
        nd = max(2, int(abs(cover_front - y_back) / 1.6))
        for j in range(nd + 1):
            yy = y_back - 0.1 + (cover_front - y_back + 0.1) * (j / nd)
            mb.box((x0, yy - 0.06, soffit + depth), (x1, yy + 0.06,
                   soffit + depth + 0.16), "A_SteelGalv", (0.65, 0.65, 0.65, 1))
        mb.box((x0 - 0.3, cover_front, soffit + depth + 0.16),
               (x1 + 0.3, y_back + 0.4, soffit + depth + 0.22), "A_RoofSeam",
               (1, 1, 1, 1))
        # ---- the surface the Beat-6 camera flies 14 m above --------------
        # 600 mm standing seams as real ribs, 6 m sheet laps, a fall-arrest
        # walkway, vent cowls, outlets: nothing here is above +0.32 m.
        rz = soffit + depth + 0.22
        yA, yB = min(cover_front, y_back + 0.4), max(cover_front, y_back + 0.4)
        ns = int((x1 - x0 + 0.6) / 0.60)
        for k in range(ns + 1):
            sx = x0 - 0.3 + k * 0.60
            mb.box((sx - 0.022, yA, rz), (sx + 0.022, yB, rz + 0.058),
                   "A_RoofSeam", (0.86, 0.86, 0.87, 1))
            for j in range(int((yB - yA) / 1.6)):        # seam clips
                mb.box((sx - 0.055, yA + 0.8 + j * 1.6, rz + 0.030),
                       (sx + 0.055, yA + 0.92 + j * 1.6, rz + 0.052),
                       "A_SteelGalv", (0.7, 0.7, 0.7, 1))
        for k in range(rng.randint(2, 5)):               # replaced panels
            px = x0 + rng.uniform(2.0, max(2.1, (x1 - x0) - 6.0))
            py = yA + rng.uniform(0.0, (yB - yA) * 0.6)
            mb.box((px, py, rz + 0.002), (px + 0.56, py + rng.uniform(3.0, 7.0),
                   rz + 0.005), "A_RoofSeam", (1.12, 1.12, 1.13, 1))
        for k in range(int((yB - yA) / 6.0) + 1):        # sheet lap lines
            ly = yA + k * 6.0
            mb.box((x0 - 0.3, ly - 0.04, rz + 0.001), (x1 + 0.3, ly + 0.04,
                   rz + 0.004), "A_RoofSeam", (0.74, 0.74, 0.75, 1))
        wy = yA + (yB - yA) * 0.62
        mb.box((x0 + 1.0, wy - 0.45, rz + 0.06), (x1 - 1.0, wy + 0.45, rz + 0.10),
               "A_MeshDark", (1, 1, 1, 1))
        for k in range(int((x1 - x0) / 3.0)):
            mb.box((x0 + 1.4 + k * 3.0, wy - 0.50, rz + 0.02),
                   (x0 + 1.5 + k * 3.0, wy + 0.50, rz + 0.06), "A_SteelGalv",
                   (0.6, 0.6, 0.6, 1))
        for k in range(int((x1 - x0) / 14.0) + 1):       # vent cowls + outlets
            vx = x0 + 7.0 + k * 14.0
            if vx > x1 - 2.0:
                break
            vy = yA + (yB - yA) * (0.30 + 0.35 * ((k * 3) % 3) / 3.0)
            mb.cyl((vx, vy, rz), (vx, vy, rz + 0.20), 0.20, "A_SteelGalv",
                   (0.72, 0.72, 0.72, 1), n=12)
            mb.cyl((vx, vy, rz + 0.20), (vx, vy, rz + 0.30), 0.30, "A_SteelGalv",
                   (0.68, 0.68, 0.68, 1), n=12, r1=0.24)
            mb.cyl((vx + 3.0, yA + 0.9, rz - 0.02), (vx + 3.0, yA + 0.9, rz + 0.03),
                   0.16, "A_Alu", (0.6, 0.6, 0.6, 1), n=10)
        # translucent rooflight strips, two per block, different widths
        for j in range(2):
            yy = cover_front + (y_back - cover_front) * (0.30 + 0.32 * j)
            mb.box((x0 + 3.0, yy, soffit + depth + 0.20), (x1 - 3.0,
                   yy + 1.1 + 0.5 * j, soffit + depth + 0.26), "A_Rooflight",
                   (1, 1, 1, 1))
        # roof graphic - only ever seen from the Beat-6 crane-out, so it is
        # oriented to read from that camera (south of the stand, looking north)
        if blk['roof'] == 'full':
            gy = yA + (yB - yA) * 0.30
            # painted at pan level so the standing seams interrupt the paint,
            # which is how a real roof graphic reads from the air
            mb.text("CIRCUIT VITRINE", T((x0 + x1) * 0.5, gy, rz + 0.003),
                    4.2, "A_Sign", srgb('#3d4650'), extrude=0.0)
            mb.text("TRIBUNE PRINCIPALE",
                    T((x0 + x1) * 0.5, yA + (yB - yA) * 0.80, rz + 0.003),
                    2.1, "A_Sign", srgb('#3d4650'), extrude=0.0)
        mb.box((x0 - 0.3, cover_front - 0.42, soffit + depth - 0.10),
               (x1 + 0.3, cover_front, soffit + depth + 0.24), "A_Alu",
               (0.76, 0.77, 0.78, 1))
        mb.text(blk['name'], T((x0 + x1) * 0.5, cover_front + 0.06,
                soffit + depth + 0.05) @ Rz(180) @ Rx(90), 0.62, "A_Sign",
                srgb('#e6eaee'), extrude=0.01)
        # downlights and speakers hung UNDER the front chord (never above it)
        for k in range(int(L / 12.0) + 1):
            lx = x0 + 6.0 + k * 12.0
            if lx > x1 - 2.0:
                break
            mb.xbox(T(lx, cover_front + 0.9, soffit - 0.35) @ Rx(28),
                    (0.9, 0.34, 0.30), "A_SteelPaint", srgb('#2b2f33'))
            mb.xbox(T(lx, cover_front + 0.9, soffit - 0.52) @ Rx(28),
                    (0.84, 0.30, 0.06), "A_Emit", srgb('#151515'))
            if k % 2:
                mb.xbox(T(lx + 4.0, cover_front + 1.6, soffit - 0.30) @ Rx(20),
                        (0.42, 0.30, 0.52), "A_SteelPaint", srgb('#25282b'))
        # roof-edge gutter and downpipes at the rear columns
        mb.box((x0, y_back + 0.30, soffit + depth + 0.10),
               (x1, y_back + 0.55, soffit + depth + 0.26), "A_Alu",
               (0.7, 0.7, 0.7, 1))
        for k in range(ncol + 1):
            cx = x0 + k * L / ncol
            mb.cyl((cx + 0.28, y_back + 0.42, soffit + depth + 0.10),
                   (cx + 0.28, y_back + 0.42, 0.0), 0.075, "A_Alu",
                   (0.72, 0.72, 0.72, 1), n=8)
    top = max(rail_top, roof_top)
    summary.setdefault('gs_tops', {})[blk['name']] = round(top, 3)
    return seatn, top


def build_grandstands(colls, rng, summary):
    objs = []
    total_seats = 0
    hi = 0.0
    for bi, blk in enumerate(GS_BLOCKS):
        mb = MB("ARCH_Grandstand_%02d_%s" % (bi, blk['name'].split()[-1]))
        gr = random.Random(4200 + bi * 131)
        n, top = _grandstand_block(mb, blk, gr, summary)
        total_seats += n
        hi = max(hi, top)
        objs.append(mb.build(colls['ARCH_Grandstands']))
    # ---- stair / circulation towers in the gaps ----------------------------
    mb = MB("ARCH_Grandstand_Towers")
    gaps = []
    for i in range(len(GS_BLOCKS) - 1):
        gaps.append((GS_BLOCKS[i]['x1'], GS_BLOCKS[i + 1]['x0']))
    for gi, (ga, gb) in enumerate(gaps):
        gr = random.Random(7700 + gi * 53)
        cx = (ga + gb) * 0.5
        w = min(9.0, gb - ga - 1.0)
        h = gr.uniform(10.9, 12.3)
        y0 = GS_FRONT - 22.0
        y1 = y0 + 9.0
        for sx in (cx - w / 2, cx + w / 2):
            for sy in (y0, y1):
                mb.cyl((sx, sy, 0.0), (sx, sy, h + 0.9), 0.16, "A_SteelPaint",
                       srgb('#3f4549'), n=10)
        # switchback flights
        nfl = int(h / 1.85)
        for k in range(nfl):
            z = k * 1.85
            d = 1 if k % 2 == 0 else -1
            ya, yb = (y0 + 0.6, y1 - 0.6) if d > 0 else (y1 - 0.6, y0 + 0.6)
            for s in range(10):
                t0 = s / 10.0
                yy = ya + (yb - ya) * t0
                mb.box((cx - w / 2 + 0.4, yy - 0.18, z + 0.18 * s),
                       (cx + w / 2 - 0.4, yy + 0.18, z + 0.06 + 0.18 * s),
                       "A_SteelGalv", (0.66, 0.66, 0.66, 1))
            mb.box((cx - w / 2 + 0.3, (y0 if d < 0 else y1) - 1.4,
                    z + 1.79), (cx + w / 2 - 0.3, (y0 if d < 0 else y1) + 0.3,
                    z + 1.85), "A_MeshDark", (1, 1, 1, 1))
        # mesh cladding on the outer faces, and a light roof
        for sx0, sx1, sy0, sy1 in ((cx - w / 2, cx - w / 2 + 0.05, y0, y1),
                                   (cx + w / 2 - 0.05, cx + w / 2, y0, y1)):
            mb.box((sx0, sy0, 1.0), (sx1, sy1, h), "A_MeshScreen", (1, 1, 1, 1))
        mb.box((cx - w / 2 - 0.4, y0 - 0.4, h + 0.9), (cx + w / 2 + 0.4,
               y1 + 0.4, h + 1.02), "A_RoofSeam", (1, 1, 1, 1))
        mb.text("%d" % (gi + 2), T(cx, y0 - 0.45, h * 0.55) @ Rx(90), 1.6,
                "A_Sign", srgb('#e4e8ea'), extrude=0.02)
        hi = max(hi, h + 1.02)
        # ground-level concourse gate under the tower
        mb.box((cx - w / 2 - 0.5, y0 - 3.0, 0.0), (cx + w / 2 + 0.5, y0 - 2.7,
               3.0), "A_MeshScreen", (1, 1, 1, 1))
    objs.append(mb.build(colls['ARCH_Grandstands']))
    # ---- THE TERRACE  ------------------------------------------------------
    # The grandstand band is circuit y -34..-62, which is beyond
    # C.platform_edge(-1) = 25.0, so C.world_ground_z hands it to build_terrain
    # and returns NaN: this module is not allowed to know the height there and
    # must not guess it.  A grandstand does not sit on natural ground anyway — it
    # sits on a formed terrace.  So the terrace is built: deck at C.APRON_Z, a
    # battered retaining skirt TERRACE_DEPTH below it, CLOSED, and a service
    # apron front and rear.  Whatever build_terrain welds to on the outside, the
    # stand has a foot and the skirt reads as a retaining wall rather than as a
    # slab hanging in the air.  The extents are published in
    # build_architecture.md so terrain can cut to them.
    TERRACE_DEPTH = 1.85
    TX0, TX1 = -426.0, 186.0
    TY0, TY1 = GS_BACK - 7.0, GS_FRONT + 5.5
    mb = MB("ARCH_Grandstand_Terrace")
    gr = random.Random(9911)
    # THE GRID MUST COVER THE RECT.  `int((TY1 - TY0) / 5.0)` = 8 over a 40.5 m
    # band left a 0.5 m x 612 m strip (306 m2) along the terrace's front edge with
    # no deck at all — measured, 1.28 % of a 12 000-point sweep hit nothing.
    NTX = max(1, int(math.ceil((TX1 - TX0) / 6.0)))
    NTY = max(1, int(math.ceil((TY1 - TY0) / 5.0)))
    TCW = (TX1 - TX0) / NTX
    TCH = (TY1 - TY0) / NTY
    bays = []
    for i in range(NTX):
        for j in range(NTY):
            bays.append((TX0 + i * TCW + 0.012, TX0 + (i + 1) * TCW - 0.012,
                         TY0 + j * TCH + 0.012, TY0 + (j + 1) * TCH - 0.012,
                         (gr.random(), gr.random())))
    nb = 0
    for poly, (r1, r2), whole in cut_bays(bays, clear_c, leaf=1.0, max_split=3):
        if _poly_area(poly) < 0.05:
            continue
        col, dz = _stain(gr, 'apron')
        mb.add([(p[0], p[1], APRON_Z + dz + r2 * Z_JIT) for p in poly],
               [tuple(range(len(poly)))], "A_ConcApron", col)
        nb += 1
    # BEDDING under the deck, closed, 16 mm down.  The deck bays carry the same
    # 12 mm inset as every other field in this file, so without it each of the
    # 816 bays was ringed by a 24 mm slot straight through to the sky — the same
    # mechanism as assembly defect #3, over 25 700 m2 in the Beat-6 closing wide.
    tcap = []
    for i in range(NTX):
        for j in range(NTY):
            tcap.append((TX0 + i * TCW, TX0 + (i + 1) * TCW,
                         TY0 + j * TCH, TY0 + (j + 1) * TCH, None))
    for poly, _pl, _w in cut_bays(tcap, clear_c, leaf=1.0, max_split=3):
        if _poly_area(poly) < 0.05:
            continue
        mb.prism(poly, APRON_Z - 0.30, APRON_Z - 0.016, "A_ConcApron",
                 (0.64, 0.64, 0.63, 1))
    # the skirt: closed on all four sides, battered 0.35 m over its height
    for (a, b, nvx, nvy) in ((( TX0, TY0), ( TX1, TY0), 0.0, -1.0),
                             (( TX1, TY1), ( TX0, TY1), 0.0, 1.0),
                             (( TX0, TY1), ( TX0, TY0), -1.0, 0.0),
                             (( TX1, TY0), ( TX1, TY1), 1.0, 0.0)):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(1, int(L / 3.2))
        for k in range(n):
            t0, t1 = k / n, (k + 1) / n
            p0 = (a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0)
            p1 = (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1)
            bt = 0.35
            tone = 0.84 + 0.12 * ((k * 7) % 5) / 5.0
            mb.quad((p0[0] + nvx * bt, p0[1] + nvy * bt, APRON_Z - TERRACE_DEPTH),
                    (p1[0] + nvx * bt, p1[1] + nvy * bt, APRON_Z - TERRACE_DEPTH),
                    (p1[0], p1[1], APRON_Z + 0.02), (p0[0], p0[1], APRON_Z + 0.02),
                    "A_ConcBoard", (tone, tone, tone * 0.99, 1))
            if k % 5 == 2:                       # counterfort buttress
                mb.box((min(p0[0], p1[0]) - 0.2 + nvx * 0.05,
                        min(p0[1], p1[1]) - 0.2 + nvy * 0.05,
                        APRON_Z - TERRACE_DEPTH),
                       (min(p0[0], p1[0]) + 0.2 + nvx * (bt + 0.55),
                        min(p0[1], p1[1]) + 0.2 + nvy * (bt + 0.55),
                        APRON_Z - TERRACE_DEPTH * 0.35), "A_ConcBoard",
                       (tone * 0.96, tone * 0.96, tone, 1))
    # concourse: front and rear service aprons, kerbed
    for (fy0, fy1) in ((GS_FRONT - 0.35, GS_FRONT + 4.6),
                       (GS_BACK - 5.6, GS_BACK + 1.0)):
        mb.box((TX0 + 0.5, fy0, APRON_Z - 0.06), (TX1 - 0.5, fy1, APRON_Z + 0.012),
               "A_Asphalt", (0.96, 0.98, 1.0, 1))
    objs.append(mb.build(colls['ARCH_Grandstands']))
    summary['terrace_bays'] = nb
    summary['terrace_extent_circuit'] = [TX0, TX1, TY0, TY1]
    summary['terrace_depth_m'] = TERRACE_DEPTH
    summary['grandstand_seats'] = total_seats
    summary['grandstand_max_z'] = round(hi, 3)
    if hi > GS_CAP - 0.10:
        raise RuntimeError("grandstand height %.3f breaks the 14.0 m Beat-6 cap"
                           % hi)
    return objs


# --------------------------------------------------------------------------- #
#  7. THE BEAT-4 WALLED CORRIDOR  —  NOT OURS ANY MORE                         #
# --------------------------------------------------------------------------- #
# It was built TWICE, 0.5 m apart, in the corridor the camera flies at rooftop
# height: BR_Transit_* at offsets +8.0 / -7.0 running world x 18 -> 109.8, and
# ARCH_ApronCorridor at +8.5 / -7.5 running 27 -> 98.4.  The south wall was
# therefore half loose intersecting tyres sinking into a concrete plinth and half
# a properly belted stack.
#
# world_contract awards it to build_barriers (C.CORRIDOR_OWNER) — it is a
# retaining wall, a belted tyre stack, a debris fence and a portal, and every one
# of those is a build_barriers primitive with a per-unit variation model — and
# names ARCH_ApronCorridor in C.CORRIDOR_DELETE_NAMES.  So it is deleted, not
# shortened, and _assert_no_corridor() below makes the deletion permanent.
#
# The arithmetic in the old comment here was not wrong: at the old s = 90 the
# south wall really did land on the racing surface.  The contract reached the
# same wall by measurement and answered it better than this module did, by
# making the corridor ASYMMETRIC (north 6->96 = the spec-literal 90 m, south
# 6->90 = 84 m, both starting at world x = 21.0 to clear our bollard line at
# 19.5) instead of throwing away 20 m of the camera's walled run.
def _assert_no_corridor():
    for nm in WC.CORRIDOR_DELETE_NAMES:
        if nm in bpy.data.objects:
            raise RuntimeError(
                "%s exists: world_contract awards the Beat-4 corridor to %s"
                % (nm, WC.CORRIDOR_OWNER))


# --------------------------------------------------------------------------- #
#  8. PADDOCK BUILDINGS                                                        #
# --------------------------------------------------------------------------- #
def _modular_block(mb, rng, x0, x1, y0, y1, floors, fh, palette, roofkind,
                   glazing='strip', stairs='ext'):
    """A modular paddock unit.  Floor count, module stacking, cladding rhythm,
    balcony placement and roof plant are all arguments, so the five units in
    the paddock share a construction system and share no silhouette."""
    for f in range(floors):
        z0 = f * fh
        z1 = z0 + fh
        inset = 0.0 if f == 0 else rng.choice((0.0, 0.0, 1.2, 2.0))
        xa, xb = x0 + inset, x1 - inset
        mb.box((xa, y0, z0), (xb, y1, z0 + 0.22), "A_ConcPrecast",
               (0.9, 0.9, 0.89, 1))
        mb.box((xa, y0, z1 - 0.14), (xb, y1, z1), "A_Alu", (0.8, 0.8, 0.8, 1))
        # pale inner partition, so the glazing shows an interior instead of a
        # black void when the camera is above the paddock
        mb.box((xa + 1.6, y0 + 1.6, z0 + 0.22), (xb - 1.6, y1 - 1.6, z1 - 0.14),
               "A_Sign", srgb('#cfd2d0'))
        # four faces: alternating cladding panels and glazing
        for (ax, ay, bx, by, face) in ((xa, y0, xb, y0, 'S'), (xa, y1, xb, y1, 'N'),
                                       (xa, y0, xa, y1, 'W'), (xb, y0, xb, y1, 'E')):
            L = math.hypot(bx - ax, by - ay)
            if L < 0.5:
                continue
            n = max(2, int(L / 1.8))
            for k in range(n):
                t0, t1 = k / n, (k + 1) / n
                px0 = ax + (bx - ax) * t0
                py0 = ay + (by - ay) * t0
                px1 = ax + (bx - ax) * t1
                py1 = ay + (by - ay) * t1
                d = 0.06
                glass = (glazing == 'strip' and 0.15 < t0 < 0.85) or \
                        (glazing == 'chequer' and (k + f) % 2 == 0)
                mat = "A_Glass" if glass and face in 'SN' else "A_Sign"
                col = (1, 1, 1, 1) if mat == "A_Glass" else \
                    jitter_col(palette[(k + f) % len(palette)], rng, 0.006, 0.05)
                zz0 = z0 + 0.22 + (0.9 if not glass else 0.5)
                mb.box((min(px0, px1) - d, min(py0, py1) - d, zz0),
                       (max(px0, px1) + d, max(py0, py1) + d, z1 - 0.14),
                       mat, col)
                mb.box((min(px0, px1) - d, min(py0, py1) - d, z0 + 0.22),
                       (max(px0, px1) + d, max(py0, py1) + d, zz0),
                       "A_Spandrel", (1, 1, 1, 1))
        if f > 0 and inset > 0.5:            # the set-back becomes a terrace
            mb.box((x0, y0, z0 + 0.22), (x1, y1, z0 + 0.28), "A_Timber",
                   (1, 1, 1, 1))
            for k in range(int((x1 - x0) / 1.6) + 1):
                mb.cyl((x0 + k * 1.6, y0 + 0.1, z0 + 0.28),
                       (x0 + k * 1.6, y0 + 0.1, z0 + 1.35), 0.03, "A_Alu",
                       (1, 1, 1, 1), n=6)
            mb.box((x0, y0 + 0.05, z0 + 1.30), (x1, y0 + 0.15, z0 + 1.38),
                   "A_Alu", (1, 1, 1, 1))
    top = floors * fh
    if roofkind == 'plant':
        for k in range(rng.randint(2, 5)):
            m = T(rng.uniform(x0 + 2, x1 - 2), rng.uniform(y0 + 2, y1 - 2),
                  top + 0.55) @ Rz(rng.uniform(-15, 15))
            mb.xbox(m, (1.4, 1.2, 1.1), "A_SteelPaint", srgb('#9ba1a5'))
    elif roofkind == 'pv':
        for k in range(int((x1 - x0 - 2) / 2.2)):
            for j in range(int((y1 - y0 - 2) / 3.2)):
                m = T(x0 + 2.1 + k * 2.2, y0 + 2.4 + j * 3.2, top + 0.9) @ Rx(-22)
                mb.xbox(m, (2.0, 3.0, 0.06), "A_Spandrel", srgb('#101828'))
                mb.cyl((x0 + 2.1 + k * 2.2, y0 + 2.4 + j * 3.2 - 1.2, top),
                       (x0 + 2.1 + k * 2.2, y0 + 2.4 + j * 3.2 - 1.2, top + 0.55),
                       0.05, "A_Alu", (1, 1, 1, 1), n=6)
    elif roofkind == 'canopy':
        for k in range(int((x1 - x0) / 4.0) + 1):
            mb.cyl((x0 + k * 4.0, y0 + 1.0, top), (x0 + k * 4.0, y0 + 1.0,
                   top + 2.8), 0.08, "A_Alu", (1, 1, 1, 1), n=8)
            mb.cyl((x0 + k * 4.0, y1 - 1.0, top), (x0 + k * 4.0, y1 - 1.0,
                   top + 2.8), 0.08, "A_Alu", (1, 1, 1, 1), n=8)
        mb.box((x0 - 0.6, y0 + 0.6, top + 2.72), (x1 + 0.6, y1 - 0.6, top + 2.80),
               "A_Fabric", jitter_col(srgb('#e4e0d6'), rng, 0.02, 0.08))
    if stairs == 'ext':
        sx = x1 + 0.2
        for f in range(floors):
            z = f * fh
            for s in range(int(fh / 0.19)):
                mb.box((sx, y0 + 1.0 + s * 0.26, z + s * 0.19),
                       (sx + 1.4, y0 + 1.26 + s * 0.26, z + 0.06 + s * 0.19),
                       "A_SteelGalv", (0.66, 0.66, 0.66, 1))
            mb.box((sx, y0 + 0.6, z + fh - 0.06), (sx + 1.4, y0 + 1.0, z + fh),
                   "A_MeshDark", (1, 1, 1, 1))
        for hh in (0.55, 1.05):
            mb.cyl((sx + 1.45, y0 + 0.6, hh), (sx + 1.45, y0 + 1.0 + fh * 1.4,
                   floors * fh + hh), 0.024, "A_SteelGalv", (1, 1, 1, 1), n=6)


def _transporter(mb, rng, x, y, team, c1, c2, ang=0.0):
    """Team transporter, nose-in.  Trailer length, cab family, awning state,
    roof pods, side hatches and the tag-along van all vary per unit."""
    m0 = T(x, y, 0.0) @ Rz(ang)
    tl = rng.uniform(12.6, 14.6)
    tw, th = 2.55, 2.95
    deck = 1.28
    col = jitter_col(c1, rng, 0.008, 0.06)
    # trailer body + livery band + name
    mb.xbox(m0 @ T(0, tl * 0.5 + 1.9, deck + th * 0.5), (tw, tl, th),
            "A_SteelPaint", col)
    mb.xbox(m0 @ T(0, tl * 0.5 + 1.9, deck + th * 0.28), (tw + 0.03, tl * 0.98,
            th * 0.22), "A_Sign", jitter_col(c2, rng, 0.008, 0.06))
    for sx in (-1, 1):
        mb.text(team, m0 @ T(sx * (tw / 2 + 0.02), tl * 0.5 + 1.9,
                deck + th * 0.62) @ Rz(90 * sx) @ Rx(90), 0.72, "A_Sign",
                jitter_col(c2, rng, 0.01, 0.06), extrude=0.01)
    mb.xbox(m0 @ T(0, tl * 0.5 + 1.9, deck + th + 0.06), (tw * 0.94, tl * 0.98,
            0.12), "A_Alu", (0.72, 0.72, 0.72, 1))
    for k in range(rng.randint(1, 4)):     # roof pods / AC / cable drum
        mb.xbox(m0 @ T(rng.uniform(-0.7, 0.7), 3.0 + rng.uniform(0, tl - 2.0),
                deck + th + 0.35), (0.8, 1.1, 0.45), "A_Alu",
                (0.8, 0.8, 0.8, 1))
    # chassis + axles
    mb.xbox(m0 @ T(0, tl * 0.5 + 1.9, deck - 0.18), (tw * 0.8, tl, 0.28),
            "A_SteelPaint", srgb('#26282a'))
    for k in range(3):
        ay = 3.4 + k * 1.36
        for sx in (-1.02, 1.02):
            mb.tyre(m0 @ T(sx, ay, 0.52) @ Ry(90), r_out=0.52, r_in=0.26,
                    w=0.36, n=16, rim=("A_Alu", (0.72, 0.72, 0.72, 1)))
    # cab: two families
    cab_hi = rng.random() < 0.55
    ch = 2.75 if cab_hi else 2.35
    mb.xbox(m0 @ T(0, 1.0, 0.75 + ch * 0.5), (2.48, 2.5, ch), "A_SteelPaint", col)
    mb.xbox(m0 @ T(0, -0.20, 0.95 + ch * 0.55), (2.30, 0.16, ch * 0.42),
            "A_Glass", (1, 1, 1, 1))
    if cab_hi:
        mb.xbox(m0 @ T(0, 1.0, 0.75 + ch + 0.16), (2.2, 2.2, 0.30), "A_SteelPaint",
                jitter_col(c2, rng, 0.01, 0.1))
    for sx in (-1.35, 1.35):
        mb.xbox(m0 @ T(sx, 0.15, 1.9), (0.10, 0.22, 0.55), "A_SteelPaint",
                srgb('#1c1e20'))
        mb.cyl(tuple(m0 @ Vector((sx - 0.5, 1.9, 0.55))),
               tuple(m0 @ Vector((sx - 0.14, 1.9, 0.55))), 0.55, "A_Rubber",
               (1, 1, 1, 1), n=16)
    mb.xbox(m0 @ T(0, -0.35, 0.55), (2.4, 0.22, 0.34), "A_SteelPaint",
            srgb('#2a2c2e'))
    # awning: deployed / half / stowed
    aw = rng.random()
    side = rng.choice((-1, 1))
    if aw > 0.45:
        d = 4.6 if aw > 0.72 else 2.4
        mb.xbox(m0 @ T(side * (tw / 2 + d * 0.5), tl * 0.5 + 2.2, deck + th - 0.10),
                (d, tl * 0.82, 0.06), "A_Fabric", jitter_col(c2, rng, 0.02, 0.08))
        for k in range(3):
            py = 2.6 + k * (tl * 0.36)
            mb.cyl(tuple(m0 @ Vector((side * (tw / 2 + d), py, 0.0))),
                   tuple(m0 @ Vector((side * (tw / 2 + d), py, deck + th - 0.12))),
                   0.05, "A_Alu", (1, 1, 1, 1), n=8)
        if aw > 0.72:
            for k in range(rng.randint(2, 5)):
                mb.xbox(m0 @ T(side * (tw / 2 + rng.uniform(0.6, d - 0.6)),
                        2.8 + rng.uniform(0, tl * 0.7), 0.45)
                        @ Rz(rng.uniform(-30, 30)), (1.0, 0.7, 0.9),
                        "A_SteelPaint", jitter_col(c1, rng, 0.02, 0.2))
    else:
        mb.cyl(tuple(m0 @ Vector((side * (tw / 2 + 0.14), 2.4, deck + th - 0.18))),
               tuple(m0 @ Vector((side * (tw / 2 + 0.14), tl + 1.2,
                                  deck + th - 0.18))), 0.16, "A_Fabric",
               jitter_col(c2, rng, 0.02, 0.08), n=10)
    if rng.random() < 0.35:                # generator box on the ground
        mb.xbox(m0 @ T(-side * (tw / 2 + 1.2), tl * 0.5, 0.55)
                @ Rz(rng.uniform(-15, 15)), (1.6, 2.4, 1.1), "A_SteelPaint",
                srgb('#7d848a'))


def build_paddock(colls, rng, summary):
    mb = MB("ARCH_PaddockBuildings")
    # ---- media centre -------------------------------------------------------
    _modular_block(mb, random.Random(11), -150.0, -92.0, 44.0, 62.0, 2, 4.6,
                   [srgb('#c9ccd0'), srgb('#8d949a'), srgb('#e2e5e7')], 'pv',
                   glazing='strip')
    mb.text("CENTRE DE PRESSE", T(-121.0, 43.8, 6.9) @ Rx(90), 1.05, "A_Alu",
            srgb('#e6e9ec'), extrude=0.04)
    # ---- medical centre -----------------------------------------------------
    _modular_block(mb, random.Random(12), -205.0, -172.0, 47.0, 63.0, 1, 5.6,
                   [srgb('#e8eae9'), srgb('#cfd6d2')], 'plant', glazing='chequer',
                   stairs='none')
    mb.box((-214.0, 50.0, 0.0), (-205.0, 60.0, 0.25), "A_Asphalt", (1, 1, 1, 1))
    for k in range(3):
        mb.cyl((-213.0 + k * 4.0, 51.0, 0.25), (-213.0 + k * 4.0, 51.0, 4.2),
               0.10, "A_Alu", (1, 1, 1, 1), n=8)
        mb.cyl((-213.0 + k * 4.0, 59.0, 0.25), (-213.0 + k * 4.0, 59.0, 4.2),
               0.10, "A_Alu", (1, 1, 1, 1), n=8)
    mb.box((-214.5, 50.5, 4.18), (-204.5, 59.5, 4.30), "A_Alu", (0.8, 0.8, 0.8, 1))
    mb.box((-190.0, 46.6, 2.2), (-186.0, 47.0, 3.6), "A_Sign", srgb('#e8ebe9'))
    mb.box((-188.7, 46.5, 2.45), (-187.3, 46.9, 3.35), "A_Sign", srgb('#1e8a4a'))
    mb.box((-188.3, 46.5, 2.65), (-187.7, 46.9, 3.15), "A_Sign", srgb('#e8ebe9'))
    mb.text("MEDICAL", T(-178.0, 46.8, 3.2) @ Rx(90), 0.85, "A_Alu",
            srgb('#e6e9ec'), extrude=0.03)
    # ---- five hospitality units, one system, five silhouettes --------------
    specs = [(-155.0, -126.0, 3, 3.4, 'plant', 'strip', '#20344f'),
             (-118.0, -84.0, 2, 3.8, 'canopy', 'chequer', '#4a5a2e'),
             (-72.0, -40.0, 3, 3.2, 'pv', 'strip', '#5c3a24'),
             (-28.0, 6.0, 2, 4.2, 'canopy', 'strip', '#2f4f52'),
             (18.0, 62.0, 3, 3.3, 'plant', 'chequer', '#43324f')]
    for i, (x0, x1, fl, fh, rk, gl, base) in enumerate(specs):
        pal = [srgb(base), srgb('#d6d9dc'), jitter_col(srgb(base), rng, 0.04, 0.25)]
        _modular_block(mb, random.Random(300 + i * 17), x0, x1, 66.0,
                       66.0 + rng.uniform(14.0, 20.0), fl, fh, pal, rk, gl)
        mb.text(TEAMS[(i * 3) % 14][0], T((x0 + x1) * 0.5, 65.7, fl * fh - 1.2)
                @ Rx(90), 1.15, "A_Alu", srgb('#eceff2'), extrude=0.05)
    # ---- paddock club marquee ----------------------------------------------
    mx0, mx1, my0, my1 = 10.0, 60.0, 92.0, 112.0
    for k in range(6):
        px = mx0 + 3.0 + k * 8.8
        mb.cyl((px, (my0 + my1) * 0.5, 0.0), (px, (my0 + my1) * 0.5, 9.4), 0.16,
               "A_Alu", (1, 1, 1, 1), n=10)
    nseg = 14
    for k in range(nseg):
        t0, t1 = k / nseg, (k + 1) / nseg
        x_0 = mx0 + (mx1 - mx0) * t0
        x_1 = mx0 + (mx1 - mx0) * t1
        for sgn in (-1, 1):
            for j in range(5):
                s0, s1 = j / 5.0, (j + 1) / 5.0
                yy0 = (my0 + my1) * 0.5 + sgn * s0 * (my1 - my0) * 0.5
                yy1 = (my0 + my1) * 0.5 + sgn * s1 * (my1 - my0) * 0.5
                z0 = 9.4 - 5.2 * (s0 ** 1.7) - 0.35 * math.sin(t0 * 9.0)
                z1 = 9.4 - 5.2 * (s1 ** 1.7) - 0.35 * math.sin(t1 * 9.0)
                mb.quad((x_0, yy0, z0), (x_1, yy0, z0 - 0.02 * math.sin(t1 * 9)),
                        (x_1, yy1, z1 - 0.02 * math.sin(t1 * 9)), (x_0, yy1, z1),
                        "A_Fabric", srgb('#e9e6dd'))
    mb.box((mx0 - 0.4, my0 - 0.4, 0.0), (mx1 + 0.4, my0 + 0.1, 3.0), "A_Glass",
           (1, 1, 1, 1))
    mb.box((mx0 - 0.4, my1 - 0.1, 0.0), (mx1 + 0.4, my1 + 0.4, 3.0), "A_Glass",
           (1, 1, 1, 1))
    # ---- service compound ---------------------------------------------------
    for k in range(6):
        m = T(-238.0 + k * 5.2, 100.0 + rng.uniform(-2, 6), 1.35) \
            @ Rz(rng.uniform(-4, 4))
        mb.xbox(m, (4.4, 2.6, 2.7), "A_SteelPaint",
                jitter_col(srgb('#7f868c'), rng, 0.02, 0.2))
        for j in range(int(4.4 / 0.42)):
            mb.xbox(m @ T(-2.0 + j * 0.42, 1.32, 0), (0.30, 0.06, 2.2), "A_Alu",
                    (0.7, 0.7, 0.7, 1))
    for k in range(4):
        mb.cyl((-244.0, 104.0 + k * 4.2, 0.0), (-244.0, 104.0 + k * 4.2, 5.6),
               1.35, "A_Alu", (0.82, 0.82, 0.82, 1), n=20)
        mb.cyl((-244.0, 104.0 + k * 4.2, 5.6), (-244.0, 104.0 + k * 4.2, 6.0),
               1.42, "A_Alu", (0.78, 0.78, 0.78, 1), n=20)
    # ---- transporters, one per team, colours matched to the garages --------
    for i in range(14):
        team, c1, c2 = TEAMS[i]
        gr = random.Random(800 + i * 29)
        x = -296.0 + i * 8.1
        _transporter(mb, gr, x, 93.5, team, srgb(c1), srgb(c2),
                     ang=gr.uniform(-2.5, 2.5))
    for i in range(6):
        team, c1, c2 = TEAMS[(i * 2) % 14]
        gr = random.Random(880 + i * 31)
        _transporter(mb, gr, -294.0 + i * 8.4, 62.6, team, srgb(c1), srgb(c2),
                     ang=180.0 + gr.uniform(-2.5, 2.5))
    # ---- paddock perimeter fence + gates ------------------------------------
    def fence(ax, ay, bx, by, h=2.45, banner=True):
        L = math.hypot(bx - ax, by - ay)
        n = max(1, int(L / 3.0))
        for k in range(n):
            t0, t1 = k / n, (k + 1) / n
            p0 = (ax + (bx - ax) * t0, ay + (by - ay) * t0)
            p1 = (ax + (bx - ax) * t1, ay + (by - ay) * t1)
            mb.cyl((p0[0], p0[1], 0.0), (p0[0], p0[1], h), 0.045, "A_SteelGalv",
                   (1, 1, 1, 1), n=8)
            mb.add([(p0[0], p0[1], 0.15), (p1[0], p1[1], 0.15),
                    (p1[0], p1[1], h - 0.05), (p0[0], p0[1], h - 0.05)],
                   [(0, 1, 2, 3)], "A_MeshScreen", (1, 1, 1, 1))
            if banner and k % 3 == 1:
                nm, cc1, cc2 = BRANDS[(k * 5) % len(BRANDS)]
                mb.add([(p0[0], p0[1], 0.5), (p1[0], p1[1], 0.5),
                        (p1[0], p1[1], h - 0.35), (p0[0], p0[1], h - 0.35)],
                       [(0, 1, 2, 3)], "A_Sign", jitter_col(srgb(cc1), rng,
                                                            0.01, 0.08))
    fence(-486.0, 116.0, 104.0, 116.0)
    fence(-486.0, 40.5, -486.0, 116.0)
    fence(104.0, 116.0, 104.0, 41.0)
    summary['transporters'] = 20
    o1 = mb.build(colls['ARCH_Paddock'], bevel=0.010)

    # ---- showroom neighbours, authored in WORLD metres ----------------------
    mb = MB("ARCH_ShowroomSurrounds")
    gr = random.Random(555)
    # service yard west of the pavilion
    # x1 = -27.6 butts the forecourt's granite edge band at -27.55; it used to
    # run to -24.0 and overlap it, two surfaces 2 mm apart over 32 m
    mb.box((-42.0, -16.0, -0.30), (-27.6, 16.0, -0.004), "A_Asphalt",
           (1, 1, 1, 1))
    mb.box((-42.0, -16.0, -EMBED), (-41.6, 16.0, 2.6), "A_ConcPrecast",
           (0.9, 0.9, 0.89, 1))
    for k in range(4):
        mb.xbox(T(-38.0 + k * 3.4, 12.0 + gr.uniform(-1, 1), 1.35)
                @ Rz(gr.uniform(-6, 6)), (2.9, 2.3, 2.7), "A_SteelPaint",
                jitter_col(srgb('#8d9399'), gr, 0.02, 0.2))
    mb.box((-30.0, -14.0, 0.0), (-25.0, -6.0, 3.4), "A_MeshDark", (1, 1, 1, 1))
    # planters along the forecourt edge, five sizes, uneven spacing, PLANTED —
    # they were empty soil boxes, which is what a render looks like and not what
    # a forecourt looks like.  Every shrub is generated: 3-6 stems, its own
    # branch angles, its own leaf cloud, its own green.
    px = -24.0
    nfp = 0
    while px < 24.0:
        w = gr.choice((2.4, 3.2, 4.0, 5.2))
        if abs(px + w * 0.5) < 9.0:
            px += w + gr.uniform(1.2, 3.0)
            continue
        for sy in (-20.5, 20.5):
            # the forecourt is NOT one of the contract's circuit rectangles, so
            # _owned() rejects it outright: test the road programme directly
            if clear_c(*WC.world_to_circuit(px + w * 0.5, sy))[0] <= 1.2:
                continue
            zg = sit_w(px + w * 0.5, sy)
            mb.box((px, sy - 0.9, zg - EMBED), (px + w, sy + 0.9, zg + 0.62),
                   "A_ConcPrecast", (0.86 + gr.uniform(-0.04, 0.04), 0.86, 0.85, 1))
            mb.box((px + 0.12, sy - 0.78, zg + 0.50),
                   (px + w - 0.12, sy + 0.78, zg + 0.56), "A_Soil", (1, 1, 1, 1))
            for q in range(max(1, int(w * gr.uniform(0.6, 1.1)))):
                _shrub(mb, gr, px + gr.uniform(0.4, w - 0.4),
                       sy + gr.uniform(-0.55, 0.55), zg + 0.55, r_max=0.78)
            nfp += 1
        px += w + gr.uniform(1.2, 3.0)
    summary['forecourt_planters'] = nfp
    # three flagpoles, different heights, west of the glass
    for k, hh in enumerate((11.0, 12.6, 10.2)):
        fx, fy = -26.0, -14.0 + k * 14.0
        mb.cyl((fx, fy, 0.0), (fx, fy, hh), 0.075, "A_Alu", (1, 1, 1, 1), n=10)
        mb.cyl((fx, fy, 0.0), (fx, fy, 0.35), 0.28, "A_ConcPrecast",
               (0.85, 0.85, 0.84, 1), n=12)
        c = jitter_col(srgb('#d8dade'), gr, 0.03, 0.1)
        for j in range(8):
            t0, t1 = j / 8.0, (j + 1) / 8.0
            mb.quad((fx + 0.06 + 1.6 * t0, fy + 0.22 * math.sin(t0 * 5.5), hh - 0.3 - 0.1 * t0),
                    (fx + 0.06 + 1.6 * t1, fy + 0.22 * math.sin(t1 * 5.5), hh - 0.3 - 0.1 * t1),
                    (fx + 0.06 + 1.6 * t1, fy + 0.22 * math.sin(t1 * 5.5), hh - 1.4 - 0.25 * t1),
                    (fx + 0.06 + 1.6 * t0, fy + 0.22 * math.sin(t0 * 5.5), hh - 1.4 - 0.25 * t0),
                    "A_Fabric", c)
    o2 = mb.build(colls['ARCH_Paddock'], matrix=Matrix.Identity(4), bevel=0.010)
    return [o1, o2]


# --------------------------------------------------------------------------- #
#  9. BRIDGES  —  La Passerelle (circuit x=-450) and Le Pont de la Plongee      #
# --------------------------------------------------------------------------- #
def build_bridges(colls, rng, summary):
    mb = MB("ARCH_LaPasserelle")
    X = -450.0
    D = 4.0                                  # deck width along x
    y0, y1 = -24.0, 28.0
    soffit = 7.50
    deck = soffit + 0.42
    dep = 3.05                               # truss depth
    steel = srgb('#4c5257')
    # deck plate + walking surface
    mb.box((X - D / 2, y0, soffit), (X + D / 2, y1, deck), "A_ConcPrecast",
           (0.9, 0.9, 0.89, 1))
    for k in range(int((y1 - y0) / 1.2)):    # non-slip nosings, worn unevenly
        yy = y0 + k * 1.2
        mb.box((X - D / 2 + 0.2, yy, deck), (X + D / 2 - 0.2, yy + 0.06,
               deck + 0.012), "A_SteelGalv",
               (0.6 + 0.2 * ((k * 3) % 4) / 4.0, 0.6, 0.58, 1))
    # side trusses
    for sx in (X - D / 2, X + D / 2):
        for cz in (soffit + 0.05, soffit + dep):
            mb.cyl((sx, y0, cz), (sx, y1, cz), 0.13, "A_SteelPaint", steel, n=10)
        n = 20
        for k in range(n + 1):
            yy = y0 + (y1 - y0) * k / n
            mb.cyl((sx, yy, soffit + 0.05), (sx, yy, soffit + dep), 0.07,
                   "A_SteelPaint", steel, n=6)
            if k < n:
                y2 = y0 + (y1 - y0) * (k + 1) / n
                a = soffit + (0.05 if k % 2 == 0 else dep)
                b = soffit + (dep if k % 2 == 0 else 0.05)
                mb.cyl((sx, yy, a), (sx, y2, b), 0.055, "A_SteelPaint", steel, n=6)
        # mesh infill panels, three of them replaced by clear polycarbonate
        for k in range(int((y1 - y0) / 4.0)):
            yy = y0 + k * 4.0
            mat = "A_MeshScreen" if k % 5 != 3 else "A_GlassTint"
            mb.box((sx - 0.03, yy + 0.1, soffit + 0.6), (sx + 0.03, yy + 3.9,
                   soffit + dep - 0.15), mat, (1, 1, 1, 1))
    # top chords + a light roof
    for k in range(int((y1 - y0) / 2.6) + 1):
        yy = y0 + k * 2.6
        mb.cyl((X - D / 2, yy, soffit + dep), (X + D / 2, yy, soffit + dep + 0.55),
               0.05, "A_SteelPaint", steel, n=6)
    mb.box((X - D / 2 - 0.25, y0 - 0.3, soffit + dep + 0.52),
           (X + D / 2 + 0.25, y1 + 0.3, soffit + dep + 0.60), "A_RoofSeam",
           (1, 1, 1, 1))
    # end towers with switchback stairs and a lift shaft on the paddock side.
    # The south tower lands at circuit y = -24, which is INSIDE C.platform_edge
    # (25.0) on the right of the pit straight, i.e. on build_barriers' runoff
    # platform at z = -0.32.  The old towers started at z = 0.000 and floated.
    for ey, lift in ((y0, False), (y1, True)):
        sgn = -1 if ey < 0 else 1
        tx0, tx1 = X - D / 2 - 1.2, X + D / 2 + 1.2
        ty0, ty1 = ey + sgn * 0.0, ey + sgn * 8.0
        zt = min(sit_c(cx, cy) for cx in (tx0, tx1) for cy in (ty0, ty1)) - EMBED
        # a cast raft, so the tower has a foot whatever the neighbour built
        mb.box((tx0 - 0.55, min(ty0, ty1) - 0.55, zt - 0.55),
               (tx1 + 0.55, max(ty0, ty1) + 0.55, zt + 0.09), "A_ConcPrecast",
               (0.86, 0.86, 0.85, 1))
        for cx in (tx0, tx1):
            for cy in (ty0, ty1):
                mb.cyl((cx, cy, zt), (cx, cy, soffit + dep + 0.6), 0.15,
                       "A_SteelPaint", steel, n=10)
        for k in range(int(soffit / 1.9)):
            z = zt + 0.09 + k * 1.9
            d = 1 if k % 2 == 0 else -1
            ya = ty0 + sgn * (0.8 if d > 0 else 7.2)
            yb = ty0 + sgn * (7.2 if d > 0 else 0.8)
            for st in (tx0 + 0.30, tx1 - 0.30):     # stringers
                mb.beam((st, ya, z - 0.10), (st, yb, z + 1.80), 0.10, 0.34,
                        "A_SteelPaint", steel)
            for s in range(10):
                yy = ya + (yb - ya) * s / 10.0
                mb.box((tx0 + 0.35, yy - 0.2, z + 0.19 * s),
                       (tx1 - 0.35, yy + 0.2, z + 0.06 + 0.19 * s), "A_SteelGalv",
                       (0.66, 0.66, 0.66, 1))
            # half landing at the head of every flight
            mb.box((tx0 + 0.25, yb - sgn * 1.5, z + 1.84), (tx1 - 0.25,
                   yb + sgn * 0.35, z + 1.92), "A_MeshDark", (1, 1, 1, 1))
            mb.beam((tx0 + 0.25, yb + sgn * 0.3, z + 1.80),
                    (tx1 - 0.25, yb + sgn * 0.3, z + 1.80), 0.10, 0.30,
                    "A_SteelPaint", steel)
            for hh in (0.55, 1.08):                 # handrails up the flight
                mb.cyl((tx0 + 0.22, ya, z + hh), (tx0 + 0.22, yb, z + 1.9 + hh),
                       0.022, "A_SteelGalv", (1, 1, 1, 1), n=6)
                mb.cyl((tx1 - 0.22, ya, z + hh), (tx1 - 0.22, yb, z + 1.9 + hh),
                       0.022, "A_SteelGalv", (1, 1, 1, 1), n=6)
        for cx0, cx1 in ((tx0, tx0 + 0.05), (tx1 - 0.05, tx1)):
            mb.box((cx0, min(ty0, ty1), zt + 1.0), (cx1, max(ty0, ty1),
                   soffit + dep), "A_MeshScreen", (1, 1, 1, 1))
        mb.box((tx0, ty1 - sgn * 0.05, zt + 1.0), (tx1, ty1, soffit + dep),
               "A_MeshScreen", (1, 1, 1, 1))
        for cz in (zt + 1.0, soffit + dep):         # frame the cladding
            mb.beam((tx0, ty0, cz), (tx0, ty1, cz), 0.10, 0.16, "A_SteelPaint",
                    steel)
            mb.beam((tx1, ty0, cz), (tx1, ty1, cz), 0.10, 0.16, "A_SteelPaint",
                    steel)
            mb.beam((tx0, ty1, cz), (tx1, ty1, cz), 0.10, 0.16, "A_SteelPaint",
                    steel)
        if lift:
            mb.box((tx1 + 0.2, ty1 - sgn * 3.0, zt), (tx1 + 3.0, ty1, deck + 1.2),
                   "A_Spandrel", (1, 1, 1, 1))
            mb.box((tx1 + 0.24, ty1 - sgn * 2.6, zt + 1.0), (tx1 + 0.30,
                   ty1 - sgn * 0.4, deck - 0.4), "A_Glass", (1, 1, 1, 1))
        mb.box((tx0 - 0.4, min(ty0, ty1) - 0.4, deck + 1.4), (tx1 + 0.4,
               max(ty0, ty1) + 0.4, deck + 1.5), "A_RoofSeam", (1, 1, 1, 1))
    # R2-256.  THE TRUSS FACE IS NOT OURS TO LETTER, AND THIS IS WHY.
    #
    # A white 0.85 m run reading "PASSERELLE  2" used to be laid here, at
    # (X - D/2 - 0.1, 2.0, soffit + dep - 0.9) = (-452.100, 2.000, 9.650).
    # `build_dressing`'s family-5 fascia banner hangs on the SAME face at
    # (-452.055, 2.000, 8.920), 44.0 x 1.60 m -- 45 mm in front of it,
    # concentric, and wholly containing it.  Both were emitted; neither was
    # hidden; the delivered 4K frame 2972abcb3fa1.png shows gold CADENCE and
    # white PASSERELLE printed through each other and garbling into
    # "PASSERELICE".  Measured by `tools/text_overlap_gate.py`: 0.067 deg apart,
    # 8 mm of slab gap, 100 % of the smaller panel covered.
    #
    # THE BANNER WON, on ownership and not on taste.  `build_dressing.md`'s
    # inventory claims "bridge fascia banners | the two overpasses' own geometry,
    # read out of build_architecture.py | 4", and its "explicitly NOT mine" line
    # concedes to this module only "the S/F gantry and its lettering".  The
    # fascia is dressing's advertising surface; `docs/item_manifest.md` item 162
    # is `la_passerelle_banner`, "La Passerelle fascia banner".  Nothing in
    # circuit_spec or the manifest ever asked for a structural label there, and
    # the "2" numbered a series that does not exist -- there is one Passerelle
    # and one Pont de la Plongee, named, not numbered.  The banner is also
    # authored on BOTH faces of BOTH bridges while this label was on one face of
    # one bridge, so deleting the banner would have cost four units of brand
    # variety to keep one string that no document asks for.
    #
    # Do not put lettering back on this face.  Ask build_dressing for a banner.
    o1 = mb.build(colls['ARCH_Bridges'], bevel=0.010)

    # ---- Le Pont de la Plongee, s = 2410, soffit 6.80 above the road -------
    # Built in a local frame on the centreline at s = 2410, +y toward the LEFT of
    # travel.  The road level is C.elevation_c(2410), not a number copied out of
    # the PVI table; the abutment tops follow C.ground_z at their own lateral,
    # which on this side of the circuit is 0.35-0.55 m below the centreline
    # because the -1.6 % runoff platform has been falling for 15 m.
    PONT_S = 2410.0
    mb = MB("ARCH_PontPlongee")
    px_, py_, _pz, phdg, _pk = WC.centreline(PONT_S)
    hdg = math.degrees(phdg)
    zr = float(WC.elevation_c(PONT_S))
    soff = zr + 6.80
    half = 15.0
    dw = 6.0
    pont_ground = {}
    for sgn in (-1, 1):                      # abutments outside the runoff
        zab = float(WC.ground_z(PONT_S, sgn * half)) - EMBED
        pont_ground[sgn] = zab
        mb.box((-dw / 2 - 1.2, sgn * half - 2.2, zr - 6.0),
               (dw / 2 + 1.2, sgn * half + 3.0, soff), "A_ConcBoard",
               (0.9, 0.9, 0.89, 1))
        mb.box((-dw / 2 - 2.0, sgn * half - 3.0, zr - 6.0),
               (dw / 2 + 2.0, sgn * half + 4.0, zab + 0.10), "A_ConcPrecast",
               (0.85, 0.85, 0.84, 1))
        for k in range(5):                   # wing wall steps
            mb.box((-dw / 2 - 1.2 - k * 0.35, sgn * (half + 2.6 + k * 1.4),
                    zr - 4.0 + k * 0.9), (dw / 2 + 1.2 + k * 0.35,
                    sgn * (half + 4.0 + k * 1.4), soff - k * 1.1),
                   "A_ConcBoard", (0.88, 0.88, 0.87, 1))
    for sx in (-dw / 2, dw / 2):             # plate girders
        mb.box((sx - 0.14, -half, soff), (sx + 0.14, half, soff + 1.35),
               "A_SteelPaint", srgb('#39433f'))
        for k in range(15):
            yy = -half + 0.9 + k * 2.0
            mb.box((sx - 0.30, yy, soff + 0.1), (sx + 0.30, yy + 0.10,
                   soff + 1.25), "A_SteelPaint", srgb('#39433f'))
    mb.box((-dw / 2 - 0.35, -half, soff + 1.35), (dw / 2 + 0.35, half,
           soff + 1.62), "A_ConcPrecast", (0.92, 0.92, 0.91, 1))
    for k in range(9):                       # cross bracing under the deck
        yy = -half + 1.5 + k * 3.4
        mb.cyl((-dw / 2, yy, soff + 0.2), (dw / 2, yy + 1.4, soff + 1.2), 0.05,
               "A_SteelPaint", srgb('#39433f'), n=6)
        mb.cyl((dw / 2, yy, soff + 0.2), (-dw / 2, yy + 1.4, soff + 1.2), 0.05,
               "A_SteelPaint", srgb('#39433f'), n=6)
    for sx in (-dw / 2 - 0.3, dw / 2 + 0.3):  # parapet + fence
        mb.box((sx - 0.09, -half, soff + 1.62), (sx + 0.09, half, soff + 2.72),
               "A_ConcPrecast", (0.9, 0.9, 0.89, 1))
        mb.box((sx - 0.03, -half, soff + 2.72), (sx + 0.03, half, soff + 3.70),
               "A_MeshDark", (1, 1, 1, 1))
        for k in range(11):
            yy = -half + 1.5 + k * 3.0
            mb.cyl((sx, yy, soff + 2.6), (sx, yy, soff + 3.75), 0.04,
                   "A_SteelGalv", (1, 1, 1, 1), n=6)
    mb.box((-dw / 2 + 0.2, -half - 6.0, soff + 1.55), (dw / 2 - 0.2, half + 6.0,
           soff + 1.63), "A_Asphalt", (1, 1, 1, 1))
    m_pont = T(px_, py_, 0.0) @ Rz(hdg)
    o2 = mb.build(colls['ARCH_Bridges'], matrix=m_pont, bevel=0.010)
    summary['bridges'] = 2
    summary['pont_road_z'] = round(zr, 4)
    summary['pont_abutment_z'] = [round(pont_ground[-1], 4),
                                  round(pont_ground[+1], 4)]
    return [o1, o2]


# --------------------------------------------------------------------------- #
#  10. SIGHT-LINE VERIFICATION  (spec 10.6 asks for a scripted gate)            #
# --------------------------------------------------------------------------- #
HOLD_W = (594.19, 16.05, 140.0)
KEY0_W = (315.64, 89.61, 27.8)
WOUND_W = (15.0, 0.0, 2.85)
LINE_W = (329.396, 169.82, 0.60)
BEAT6_KEYS = [(-3.0, (129.84, 2.37, 2.8)), (-1.0, (255.52, 75.07, 14.8)),
              (0.0, (315.64, 89.61, 27.8)), (2.0, (425.14, 87.77, 62.1)),
              (4.0, (513.55, 61.43, 98.8)), (6.0, (572.69, 30.78, 128.0)),
              (8.0, (594.19, 16.05, 140.0))]


def _centreline_pt(s):
    """World point at station s, walked from the spec's element table."""
    try:
        with open("/home/zany/f1-round2/docs/circuit_spec.json") as fh:
            els = json.load(fh)['elements']
    except Exception:
        return None
    for e in els:
        s0 = e['s_start']
        L = e['length_m']
        if not (s0 <= s <= s0 + L):
            continue
        x, y = e['start_world']
        h = math.radians(e['heading_world_deg'])
        d = s - s0
        if e['type'] == 'S':
            return (x + d * math.cos(h), y + d * math.sin(h), 0.0)
        R = e['radius_m']
        sgn = 1.0 if e['turn_deg'] > 0 else -1.0
        cx = x - sgn * R * math.sin(h)
        cy = y + sgn * R * math.cos(h)
        th = math.atan2(y - cy, x - cx) + sgn * d / R
        return (cx + R * math.cos(th), cy + R * math.sin(th), 0.0)
    return None


def _ray(origin, target, back_off=1.0):
    """True if the segment is clear of ARCH geometry."""
    dg = bpy.context.evaluated_depsgraph_get()
    o = Vector(origin)
    t = Vector(target)
    d = t - o
    L = d.length
    if L < 1e-6:
        return True, None, 0.0
    dn = d / L
    hit, loc, nor, idx, obj, mtx = bpy.context.scene.ray_cast(
        dg, o, dn, distance=max(0.0, L - back_off))
    if hit:
        return False, obj.name if obj else "?", (Vector(loc) - o).length
    return True, None, L


def verify_sightlines(summary, verbose=True):
    fails = []
    checks = []
    # 1. hold -> the wound, centre and all four aperture corners
    ap = [WOUND_W, (15.0, -4.8, 0.30), (15.0, 4.8, 0.30),
          (15.0, -4.8, 5.60), (15.0, 4.8, 5.60)]
    for i, p in enumerate(ap):
        ok, who, d = _ray(HOLD_W, p, back_off=2.0)
        checks.append(("hold->wound[%d]" % i, ok, who, d))
        if not ok:
            fails.append("hold->wound[%d] blocked by %s at %.1f m" % (i, who, d))
    # 2. key0 -> the car crossing the line (and +/- 3 m of car length)
    for i, off in enumerate((-3.0, 0.0, 3.0)):
        p = (LINE_W[0] + off * math.cos(math.radians(40.0)),
             LINE_W[1] + off * math.sin(math.radians(40.0)), LINE_W[2])
        ok, who, d = _ray(KEY0_W, p, back_off=1.5)
        checks.append(("key0->car[%d]" % i, ok, who, d))
        if not ok:
            fails.append("key0->car[%d] blocked by %s at %.1f m" % (i, who, d))
    # 3. hold -> the car during the 3 s hold (601 / 701 / 815 m past the line)
    for s in (601.0, 701.0, 815.0):
        p = _centreline_pt(s)
        if p is None:
            continue
        p = (p[0], p[1], 0.6)
        ok, who, d = _ray(HOLD_W, p, back_off=2.0)
        checks.append(("hold->car@s%d" % s, ok, who, d))
        if not ok:
            fails.append("hold->car@s%.0f blocked by %s at %.1f m" % (s, who, d))
    # 4. the Beat-6 flight itself: a 6 m clearance sphere along the path
    dirs = []
    for a in range(8):
        for e in (-40, 0, 40):
            th = 2 * math.pi * a / 8
            ph = math.radians(e)
            dirs.append((math.cos(th) * math.cos(ph), math.sin(th) * math.cos(ph),
                         math.sin(ph)))
    dirs.append((0, 0, -1))
    dg = bpy.context.evaluated_depsgraph_get()
    worst = (1e9, None, None)
    for i in range(len(BEAT6_KEYS) - 1):
        (t0, p0), (t1, p1) = BEAT6_KEYS[i], BEAT6_KEYS[i + 1]
        for k in range(9):
            u = k / 8.0
            p = Vector((lerp(p0[0], p1[0], u), lerp(p0[1], p1[1], u),
                        lerp(p0[2], p1[2], u)))
            for d in dirs:
                hit, loc, nor, idx, obj, mtx = bpy.context.scene.ray_cast(
                    dg, p, Vector(d), distance=6.0)
                if hit:
                    dist = (Vector(loc) - p).length
                    if dist < worst[0]:
                        worst = (dist, obj.name if obj else "?",
                                 (round(p.x, 1), round(p.y, 1), round(p.z, 1)))
    checks.append(("beat6 path clearance", worst[0] > 5.99, worst[1], worst[0]))
    if worst[0] < 6.0:
        fails.append("Beat-6 camera path passes %.2f m from %s at %s"
                     % (worst[0], worst[1], worst[2]))
    # 5. the transit route stays clear for the car, on the CONTRACT's route and
    #    to the CONTRACT's ribbon half width, not to a private copy of either
    for i in range(60):
        t = i * WC.ACCESS_MERGE / 59.0
        px, py, hh = WC.access_route_point(t)
        vin, vout = WC.access_edges(np.array([t]))
        for lat in (float(vin[0]) + 0.6, 0.0, float(vout[0]) - 0.6):
            o = Vector((px - math.sin(hh) * lat, py + math.cos(hh) * lat,
                        WC.access_z(t, lat) + 0.35))
            hit, loc, nor, idx, obj, mtx = bpy.context.scene.ray_cast(
                dg, o, Vector((0, 0, 1)), distance=3.2)
            if hit:
                fails.append("transit route obstructed at t=%.0f v=%.1f by %s"
                             % (t, lat, obj.name if obj else "?"))
                break
    # 6. absolute height cap inside the grandstand band
    hi = 0.0
    who = None
    for ob in bpy.data.collections.get("ARCH_Grandstands").objects:
        for c in ob.bound_box:
            wp = ob.matrix_world @ Vector(c)
            cy = w2c(wp.x, wp.y)[1]
            if -63.0 < cy < -33.0 and wp.z > hi:
                hi = wp.z
                who = ob.name
    checks.append(("grandstand max z", hi <= 13.9, who, hi))
    if hi > 13.9:
        fails.append("grandstand band reaches z=%.2f (cap 14.0) in %s" % (hi, who))
    summary['sightline_checks'] = [(c[0], bool(c[1]), c[2],
                                    round(float(c[3]), 2)) for c in checks]
    summary['sightline_fails'] = fails
    if verbose:
        print("\n--- SIGHT-LINE GATE ---")
        for nm, ok, w, d in checks:
            print("  %-26s %s   %s %s" % (nm, "PASS" if ok else "FAIL",
                                          ("%.2f" % d), w or ""))
        for f in fails:
            print("  !! " + f)
        print("--- %s ---\n" % ("ALL CLEAR" if not fails else "%d FAILURES"
                                % len(fails)))
    return fails


# --------------------------------------------------------------------------- #
#  10b. THE CONTRACT GATE                                                       #
# --------------------------------------------------------------------------- #
# The assembly review's single lesson is that six agents each verified their own
# work in isolation and the assembled result was broken.  So this gate never asks
# "is my geometry self-consistent"; it asks C.world_ground_z who owns the ground
# under every vertex this module lays on it, and fails if the answer is anybody
# else.  Run by build(verify=True) and by  -- --verify .
GATE_SAMPLE = 300000          # face centres sampled per collection, at most
# Objects that ARE the ground surface, and so must agree with the contract datum
# to TOL_SEAM.  Everything else in these collections stands ON the platform (a
# kerb, a mast base, a skip, a gravel bed) and is only required not to appear on
# somebody else's ground.
GROUND_OBJS = ("ARCH_Paving_", "ARCH_Markings", "ARCH_Grandstand_Terrace")
CULL_BAND = 0.75              # z band about APRON_Z the cull pass considers
CULL_BURIED = 0.020           # an up-face this far under another module's ground
                              # is buried and harmless; above it, it is a defect


def embed_ground_contacts(summary, verbose=True):
    """Push every ground-contact vertex EMBED below the declared plane.

    MEASURED: a ray-cast sweep of 24 000 points over the whole precinct found
    370 samples where a building base, a fence foot, a skip or a crate had its
    underside at EXACTLY z = 0.000 against paving whose bays sit at 0.000-0.0025
    — coplanar surfaces at sub-millimetre separation, i.e. the same class of
    defect as the assembly review's finding #2, only inside one module.  In a
    ray tracer that renders as a shattered, faceted patch, which is exactly what
    the first contract-lit apron frame showed.

    Only vertices that belong to NO upward-facing face are moved, so a plate
    lying on the ground (a marking, a deck board) keeps its top where it is and
    only closed solids get 20 mm taller downward.  C.BASE_EMBED_M is the
    contract's own number for this, and it is what stops a 10 mm mesh tolerance
    opening a lit gap under anything at a 12.5 deg sun."""
    moved = 0
    for cn in ("ARCH_PitBuilding", "ARCH_Paddock", "ARCH_Ground",
               "ARCH_Grandstands", "ARCH_Gantry", "ARCH_PitWall",
               "ARCH_Bridges"):
        c = bpy.data.collections.get(cn)
        if not c:
            continue
        for ob in c.objects:
            me = ob.data
            if not isinstance(me, bpy.types.Mesh) or not len(me.polygons):
                continue
            m = np.array(ob.matrix_world).reshape(4, 4)
            zcol = m[2, :3]
            zoff = m[2, 3]
            nv = len(me.vertices)
            co = np.empty(nv * 3)
            me.vertices.foreach_get("co", co)
            co = co.reshape(-1, 3)
            wz = co @ zcol + zoff
            near = np.abs(wz - APRON_Z) < 0.004
            if not near.any():
                continue
            up = np.zeros(nv, bool)
            n = len(me.polygons)
            nor = np.empty(n * 3)
            me.polygons.foreach_get("normal", nor)
            nor = nor.reshape(-1, 3) @ m[:3, :3].T
            nl = np.linalg.norm(nor, axis=1)
            nl[nl < 1e-12] = 1.0
            for f, nz in zip(me.polygons, nor[:, 2] / nl):
                if nz > 0.20:
                    for v in f.vertices:
                        up[v] = True
            sel = np.nonzero(near & ~up)[0]
            if not len(sel):
                continue
            # move along the object's own local axis that maps to world -Z
            k = int(np.argmax(np.abs(zcol)))
            step = -EMBED / zcol[k]
            for v in sel:
                me.vertices[v].co[k] += step
            me.update()
            moved += len(sel)
    summary['embedded_verts'] = moved
    if verbose and moved:
        print("  embed_ground_contacts: %d vertices sunk %.0f mm" %
              (moved, 1000 * EMBED))
    return moved


def cull_unowned(summary, verbose=True):
    """Delete every upward-facing face this module put on another module's
    ground.  This is the contract's rule for finding #2 applied as a machine
    operation: CUT, DO NOT OFFSET.  It runs after the builders so no generator
    has to be individually trusted, and verify_contract() then measures that it
    worked."""
    import bmesh
    tot = 0
    for cn in ("ARCH_Paving", "ARCH_Ground", "ARCH_Grandstands"):
        c = bpy.data.collections.get(cn)
        if not c:
            continue
        for ob in list(c.objects):
            me = ob.data
            if not isinstance(me, bpy.types.Mesh) or not len(me.polygons):
                continue
            n = len(me.polygons)
            cen = np.empty(n * 3)
            nor = np.empty(n * 3)
            me.polygons.foreach_get("center", cen)
            me.polygons.foreach_get("normal", nor)
            m = np.array(ob.matrix_world).reshape(4, 4)
            W = cen.reshape(-1, 3) @ m[:3, :3].T + m[:3, 3]
            N = nor.reshape(-1, 3) @ m[:3, :3].T
            nl = np.linalg.norm(N, axis=1)
            nl[nl < 1e-12] = 1.0
            cand = np.nonzero(((N[:, 2] / nl) > 0.50) &
                              (np.abs(W[:, 2] - APRON_Z) < CULL_BAND))[0]
            if not len(cand):
                continue
            z, own = wgz(W[cand, 0], W[cand, 1])
            ostr = own.astype(str)
            alien = ~np.isin(ostr, [WC.OWNER_APRON, WC.OWNER_TERRAIN])
            proud = np.isfinite(z) & (W[cand, 2] > z - CULL_BURIED)
            kill = cand[alien & proud]
            if not len(kill):
                continue
            bm = bmesh.new()
            bm.from_mesh(me)
            bm.faces.ensure_lookup_table()
            ks = set(kill.tolist())
            bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index in ks],
                             context='FACES')
            bm.to_mesh(me)
            bm.free()
            me.update()
            tot += len(kill)
    summary['culled_faces'] = tot
    if verbose and tot:
        print("  cull_unowned: %d up-faces removed from another module's ground"
              % tot)
    return tot


# The paved surface itself and the paint on it.  A duct-cover bolt head, a
# lifted grating and a precast kerb are all legitimately proud of the slab; the
# SLAB is what has to agree with the contract, so the datum check is filtered by
# material rather than by fudging the hardware down until a gate passes.
PAVE_MATS = frozenset(("A_ConcSlab", "A_ConcApron", "A_ForecourtSlab",
                       "A_Sealant",
                       "A_Asphalt", "A_PaintWhite", "A_PaintWhiteWorn",
                       "A_PaintYellow", "A_PaintRed", "A_PaintBlue", "A_Weed"))


def _up_faces(names, z_lo=-0.70, z_hi=0.70, up=0.80):
    """World-space centres of UPWARD-FACING faces near the platform plane.

    Upward-facing is the test that matters: a vertical wall face 0.32 m below the
    datum is a retaining wall, but a horizontal face 0.32 m below the datum in the
    same place is a hole.  Returns (centres, names) so a failure can be named."""
    P, W, M = [], [], []
    for nm in names:
        c = bpy.data.collections.get(nm)
        if not c:
            continue
        for ob in c.objects:
            me = ob.data
            if not isinstance(me, bpy.types.Mesh) or not len(me.polygons):
                continue
            n = len(me.polygons)
            cen = np.empty(n * 3)
            nor = np.empty(n * 3)
            mi = np.empty(n, dtype=np.int32)
            me.polygons.foreach_get("center", cen)
            me.polygons.foreach_get("normal", nor)
            me.polygons.foreach_get("material_index", mi)
            slots = [(s.name if s else "") for s in me.materials]
            m = np.array(ob.matrix_world).reshape(4, 4)
            cen = cen.reshape(-1, 3) @ m[:3, :3].T + m[:3, 3]
            nor = nor.reshape(-1, 3) @ m[:3, :3].T
            nl = np.linalg.norm(nor, axis=1)
            nl[nl < 1e-12] = 1.0
            keep = ((nor[:, 2] / nl) > up) & (cen[:, 2] > z_lo) & (cen[:, 2] < z_hi)
            if keep.any():
                P.append(cen[keep])
                W += [ob.name] * int(keep.sum())
                M += [slots[i] if 0 <= i < len(slots) else ""
                      for i in mi[keep].tolist()]
    if not P:
        return np.zeros((0, 3)), [], []
    return np.vstack(P), W, M


def verify_contract(summary, verbose=True):
    """-> list of failures.  Every number here is measured against the contract."""
    fails, checks = [], []

    def chk(name, ok, detail=""):
        checks.append((name, bool(ok), detail))
        if not ok:
            fails.append("%s: %s" % (name, detail))

    chk("world_contract version", WC.__version__ >= CONTRACT_MIN, WC.__version__)
    # -- 1. the Beat-4 corridor is gone -------------------------------------
    live = [n for n in WC.CORRIDOR_DELETE_NAMES if n in bpy.data.objects]
    chk("C.CORRIDOR_DELETE_NAMES are deleted", not live,
        "owner=%s, still present: %s" % (WC.CORRIDOR_OWNER, live or "none"))

    # -- 2. every UPWARD-FACING surface we lay is on ground the contract gives
    #       us, and is on it to within TOL_SEAM ---------------------------------
    for coll in ("ARCH_Paving", "ARCH_Ground", "ARCH_Grandstands"):
        A, W, MM = _up_faces([coll], z_lo=APRON_Z - CULL_BAND,
                             z_hi=APRON_Z + CULL_BAND, up=0.50)
        if not len(A):
            continue
        if len(A) > GATE_SAMPLE:
            step = int(math.ceil(len(A) / GATE_SAMPLE))
            A, W, MM = A[::step], W[::step], MM[::step]
        z, own = wgz(A[:, 0], A[:, 1])
        ostr = own.astype(str)
        alien = ~np.isin(ostr, [WC.OWNER_APRON, WC.OWNER_TERRAIN])
        # buried under another module's ground is legal (footings, heels, kerb
        # roots); VISIBLE on it is the defect the review found six times over
        bad = alien & np.isfinite(z) & (A[:, 2] > z - CULL_BURIED)
        ex = sorted(set(("%s on %s" % (W[i], ostr[i]))
                        for i in np.nonzero(bad)[0][:400]))[:3]
        chk("%s shows no surface on another module's ground" % coll,
            not bad.any(),
            "%d / %d up-faces (%d buried, legal)%s"
            % (int(bad.sum()), len(A), int((alien & ~bad).sum()),
               ("  e.g. " + "; ".join(ex)) if ex else ""))
        # ... and the ground surfaces themselves are ON the datum
        # NOTHING PROUD is the rule that matters.  A recess is drainage — a slot
        # drain channel is 55 mm down and a gully 50 mm, by design.  A surface
        # ABOVE the datum is a lip the sun draws a shadow under and a coplanar
        # risk against the neighbour, so that side is held to TOL_SEAM + MARK_Z.
        isg = np.array([any(w.startswith(p) for p in GROUND_OBJS) and
                        (mm in PAVE_MATS) for w, mm in zip(W, MM)])
        good = isg & np.isfinite(z) & ~alien
        if good.any():
            d = A[good, 2] - z[good]
            lim = TOL_SEAM + MARK_Z
            far = np.nonzero(good)[0][d > lim]
            ex2 = ["%s @(%.1f,%.1f) +%.0fmm" % (W[i], A[i, 0], A[i, 1],
                                                1000 * (A[i, 2] - z[i]))
                   for i in far[:400][::max(1, len(far[:400]) // 3)]][:3]
            chk("%s ground surfaces are never proud of C.world_ground_z" % coll,
                float(d.max()) <= lim,
                "%d faces: max +%.1f mm (limit %.1f), deepest recess %.1f mm, "
                "p50 %+.1f mm, %d over%s"
                % (len(d), 1000 * d.max(), 1000 * lim, -1000 * d.min(),
                   1000 * np.median(d), len(far),
                   ("  e.g. " + ", ".join(ex2)) if ex2 else ""))

    # -- 2b. NO OPEN JOINT ANYWHERE ON A SURFACE WE OWN  (defects #2 and #3) ---
    # The gate above asks whether a face we built is in the right place.  This one
    # asks the opposite question, which is the one the assembly review actually
    # answered with a camera: STAND ON OUR GROUND AND CAST DOWN — is there
    # anything there, and how far down is it?  Both shipped defects were invisible
    # to a face-position test and obvious to this one:
    #
    #   * every saw joint in every field was a 300-326 mm shaft, because the
    #     sub-base was `top=False`;
    #   * the 12 mm strip at u = 10.500..10.512 down the whole pit-exit apron edge
    #     had nothing under it at all.
    #
    # DEPTH_LIM is the deepest a legitimate recess goes: the drain corridor
    # formation at SUB_FORM_DZ.  Anything deeper is a hole, and at a 12.47 deg sun
    # a hole is a black line.
    dgq = bpy.context.evaluated_depsgraph_get()

    def _drop(px, py, datum):
        """-> depth below `datum` of the first thing under (px, py); 9.99 if none."""
        out = np.empty(len(px))
        nm = [None] * len(px)
        for i in range(len(px)):
            hit, loc, _n, _idx, ob, _m = bpy.context.scene.ray_cast(
                dgq, Vector((float(px[i]), float(py[i]), 4.0)),
                Vector((0, 0, -1)), distance=8.0)
            if not hit or ob is None:
                out[i] = 9.99
            else:
                out[i] = float(datum[i]) - float(loc.z)
                nm[i] = ob.name
        return out, nm

    DEPTH_LIM = SUB_FORM_DZ + 0.004        # 66 mm
    rq = np.random.default_rng(4242)
    fields = []

    # (a) the pit-exit apron, tested with build_apron_platform's OWN predicate so
    #     the gate and the builder cannot disagree about where the slab is
    NA = 60000
    SA = rq.uniform(3196.0, 3429.0, NA)
    EA = WC.verge_edge(SA) + APRON_JOINT_LAP_M
    PA = WC.platform_edge(SA, +1)
    UA = EA + rq.random(NA) * np.maximum(PA - EA, 0.1)
    WA = WC.su_to_world(SA, UA)
    ka = apron_clearance(SA, UA) > 0.20
    sel = np.nonzero(ka)[0][:9000]
    fields.append(("pit-exit apron", WA[sel, 0], WA[sel, 1],
                   WC.ground_z(SA[sel], UA[sel])))

    # (b) the paddock / pit lane / garages / forecourt / terrace, in plan
    for nm_, rect, dr in (("paddock", PLAT_RECTS['paddock'],
                           ((58.0, 0.30), (88.0, 0.30), (45.6, 0.45))),
                          ("pit lane", PLAT_RECTS['pit_lane'],
                           ((12.9, 0.30), (22.9, 0.40))),
                          ("garages", PLAT_RECTS['garages'], ()),
                          ("terrace", (-426.0, 186.0, -69.0, -28.5), ())):
        cxq = rq.uniform(rect[0], rect[1], 40000)
        cyq = rq.uniform(rect[2], rect[3], 40000)
        wxq, wyq = WC.circuit_to_world(cxq, cyq)
        band = np.zeros(len(cxq), bool)
        for (dc, hw) in dr:
            band |= np.abs(cyq - dc) < hw
        okq = (clear_c(cxq, cyq) > 0.35) & ~band & \
            (_r1_shell_clearance(wxq, wyq) > 0.35)
        if nm_ != "terrace":
            okq &= _fc_clearance(cxq, cyq) > 0.35
        selq = np.nonzero(okq)[0][:6000]
        fields.append((nm_, wxq[selq], wyq[selq], np.zeros(len(selq))))

    # (c) the showroom forecourt and the corridor mouth, world-aligned
    fxq = rq.uniform(-27.0, 26.0, 40000)
    fyq = rq.uniform(-22.0, 22.0, 40000)
    ccx, ccy = WC.world_to_circuit(fxq, fyq)
    okq = (clear_c(ccx, ccy) > 0.20) & (_r1_shell_clearance(fxq, fyq) > 0.20)
    selq = np.nonzero(okq)[0][:6000]
    fields.append(("forecourt", fxq[selq], fyq[selq], np.zeros(len(selq))))
    okq = (clear_c(ccx, ccy) > 0.05) & (_r1_shell_clearance(fxq, fyq) < -0.05)
    selq = np.nonzero(okq)[0][:4000]
    fields.append(("under the round-1 pavilion", fxq[selq], fyq[selq],
                   np.full(len(selq), R1_FORMATION_Z)))

    # ... and a SECOND, stricter question, because the first one has a blind spot
    # this build fell into: if the finished slab goes missing but the bedding is
    # still there, every column lands 35 mm low and "no open joint" passes while
    # the frame shows a 46 mm shadow trough down 220 m of the pit straight.  So
    # also require that the thing a ray lands on is the FINISHED SURFACE almost
    # everywhere.  Only the saw joints may be low, and they are 8-24 mm of a
    # 2.4-6.0 m bay: 3 % is ten times the joint area and still caught a 0.28 m
    # strip on a 3.0 m bay (10 %) the moment it appeared.
    SURFACE_LOW = 0.020
    SURFACE_LOW_FRAC = 0.03
    worst_field = None
    for nm_, px, py, dat in fields:
        if not len(px):
            continue
        d, who = _drop(px, py, dat)
        bad = d > DEPTH_LIM
        exq = ["(%.1f, %.1f) %.0f mm %s" % (px[i], py[i], 1000 * d[i], who[i])
               for i in np.nonzero(bad)[0][:3]]
        chk("no open joint on the %s" % nm_, not bad.any(),
            "%d columns: %d deeper than %.0f mm, p99 %.1f mm, max %.1f mm%s"
            % (len(d), int(bad.sum()), 1000 * DEPTH_LIM,
               1000 * float(np.percentile(d, 99)), 1000 * float(d.max()),
               ("  e.g. " + "; ".join(exq)) if exq else ""))
        low = float((d > SURFACE_LOW).mean())
        chk("the %s shows its finished slab, not its bedding" % nm_,
            low <= SURFACE_LOW_FRAC,
            "%.2f %% of %d columns land >%.0f mm low (bound %.0f %%)"
            % (100 * low, len(d), 1000 * SURFACE_LOW, 100 * SURFACE_LOW_FRAC))
        if worst_field is None or float(d.max()) > worst_field[1]:
            worst_field = (nm_, float(d.max()))
    summary['open_joint_worst'] = worst_field

    # (c) THE APRON EDGE ITSELF, across the joint, at 1 mm.  This is the exact
    # scan the review ran at s = 3247 / 3305 / 3361 and got "the ray falls 0.300 m
    # to the sub-base" for u = 10.500..10.512.
    Sj = np.arange(3200.0, 3426.0, 1.0)
    OFFS = (0.001, 0.006, 0.012, 0.030, APRON_JOINT_LAP_M + 0.001,
            APRON_JOINT_LAP_M + 0.010, APRON_JOINT_LAP_M + 0.200)
    dmax = 0.0
    dwho = ""
    nj = 0
    for sj in Sj:
        Ej = float(WC.verge_edge(np.array([sj]))[0])
        # skip the stations where the R150 ribbon, not this module, owns the edge
        if apron_clearance(np.array([sj]),
                           np.array([Ej + APRON_JOINT_LAP_M + 0.30]))[0] <= 0.20:
            continue
        for du in OFFS:
            nj += 1
            p = WC.su_to_world(np.array([sj]), np.array([Ej + du]))[0]
            zg = float(WC.ground_z(np.array([sj]), np.array([Ej + du]))[0])
            hit, loc, _n, _i, ob, _m = bpy.context.scene.ray_cast(
                dgq, Vector((float(p[0]), float(p[1]), 4.0)),
                Vector((0, 0, -1)), distance=8.0)
            dd = 9.99 if (not hit or ob is None) else zg - float(loc.z)
            if dd > dmax:
                dmax, dwho = dd, "s=%.0f du=%.3f %s" % (
                    sj, du, ob.name if ob else "NOTHING")
    chk("the pit-exit apron edge is a joint, not a shaft",
        dmax <= DEPTH_LIM,
        "%d columns across u = verge_edge + 1..%.0f mm: deepest %.1f mm "
        "(limit %.0f)%s" % (nj, 1000 * OFFS[-1], 1000 * dmax, 1000 * DEPTH_LIM,
                            ("  worst " + dwho) if dwho else ""))
    summary['apron_edge_max_drop_mm'] = round(1000 * dmax, 1)

    # -- 2b-black. A DEPTH BOUND IS NOT A BLACKNESS BOUND  (defect #48) -------
    #
    # The two gates above PASSED the defect that shipped.  `DEPTH_LIM` is 66 mm and
    # the recess measured 34.2-34.5 mm; `SURFACE_LOW_FRAC` is 3 % and it was 0.66 %
    # of columns.  Both are honest numbers about the geometry, and both are
    # answering a question the frame does not ask.  What the frame showed was
    # **3,390 pixels below 0.02 luminance** in a scene whose track surface reads
    # 0.1729 — a black line 5 mm wide and 6.6 m long down the apron's outer edge,
    # ray-cast to ARCH_Paving_ApronPlatform's bedding at 34.24 mm mean below datum.
    #
    # THE SUN IS 12.47 deg UP.  `C.SUN_SHADOW_RATIO` = 4.5222, so a 34 mm step
    # casts 155 mm of shadow and NOTHING NARROWER THAN 155 mm GETS ANY DIRECT SUN
    # ON ITS FLOOR.  All that is left is the sky the slot can see through its own
    # mouth, which for a 5 mm x 34 mm slot is 7.25 % of the hemisphere.
    #
    # So this gate measures the RENDERED BRIGHTNESS OF THE FLOOR OF EVERY RECESS
    # it can find, as a fraction of the flat surface beside it, using
    # `C.recess_relative_radiance` — which is driven by the DECLARED SUN, so it
    # moves if build_sky moves.  It scans at 1 mm because the defect is 5 mm wide:
    # the 0.5 mm scan the review ran found it, the module's own 1 m sampling never
    # could, and every OFFS-based scan above steps in centimetres.
    #
    # ONLY CLOSED RECESSES COUNT.  A run that reaches the end of the scan span is
    # a STEP, not a slot — open to half the sky and correctly bright — so it is
    # excluded rather than reported as a 0.3 m deep black trench, which is what
    # the corridor rim would otherwise read as.
    RB_STEP = 0.001
    RB_SPAN = 0.30
    RB_MIN_DEPTH = 0.0015          # below this a "recess" is mesh tolerance
    rb_lines = []
    for sj in np.arange(3196.0, 3520.0, 3.0):
        Ej = float(WC.verge_edge(np.array([sj]))[0])
        Pj = float(WC.platform_edge(np.array([sj]), +1)[0])
        rb_lines.append(("apron inner edge", sj, Ej + APRON_JOINT_LAP_M))
        rb_lines.append(("apron outer edge", sj, Pj))
    rb_worst = (1.0, "")
    rb_black = []
    rb_recess = 0
    rb_hair = 0
    rb_hair_deep = 0.0
    for (lbl, sj, uc) in rb_lines:
        us = np.arange(uc - RB_SPAN, uc + RB_SPAN, RB_STEP)
        Wj = WC.su_to_world(np.full(us.shape, sj), us)
        zj = np.asarray(WC.ground_z(np.full(us.shape, sj), us), float)
        dd = np.empty(len(us))
        for i in range(len(us)):
            hit, loc, _n, _i, ob, _m = bpy.context.scene.ray_cast(
                dgq, Vector((float(Wj[i, 0]), float(Wj[i, 1]), 4.0)),
                Vector((0, 0, -1)), distance=8.0)
            dd[i] = (np.nan if (not hit or ob is None)
                     else float(zj[i]) - float(loc.z))
        bearing = math.degrees(WC.centreline(float(sj))[3])
        # A NO-HIT IS NOT A RECESS.  A ray that finds nothing at all is an
        # unbuilt-ground finding (#47) and it belongs to the gate above; treating
        # it as an infinitely deep slot makes this gate fail on any partial build
        # and, worse, buries the real recesses under 9.99 m of noise.
        j = 0
        while j < len(us):
            if not (dd[j] >= RB_MIN_DEPTH):
                j += 1
                continue
            k = j
            while k < len(us) and (dd[k] >= RB_MIN_DEPTH):
                k += 1
            # A ONE-SAMPLE RUN IS A HAIRLINE, NOT A MEASUREMENT.  Two abutting
            # meshes share an edge geometrically, not topologically, and a ray
            # aimed at that edge can miss both — which reads as a 1 mm slot as
            # deep as whatever is underneath.  So a run must be at least two
            # samples wide to be a recess; the hairlines are counted and their
            # worst depth reported so they are not silently dropped.  The defect
            # this gate exists for is 5 mm wide, five samples.
            if j > 0 and k < len(us) and (k - j) < 2:
                rb_hair += 1
                rb_hair_deep = max(rb_hair_deep, float(dd[j:k].max()))
            elif j > 0 and k < len(us):        # CLOSED both sides -> a slot
                w = (k - j) * RB_STEP
                dpt = float(dd[j:k].max())
                rb_recess += 1
                rr = float(WC.recess_relative_radiance(w, dpt, bearing))
                if rr < rb_worst[0]:
                    rb_worst = (rr, "%s s=%.0f u=%.3f  %.1f mm wide, %.1f mm deep"
                                % (lbl, sj, us[j], 1000 * w, 1000 * dpt))
                if rr < float(WC.TOL_RECESS_RADIANCE):
                    rb_black.append((rr, lbl, float(sj), float(us[j]), w, dpt))
            j = k
    rb_tail = ""
    if rb_hair:
        rb_tail += ("; %d one-sample hairlines skipped, deepest %.1f mm"
                    % (rb_hair, 1000 * rb_hair_deep))
    if rb_black:
        rb_tail += ("; %d BLACK, e.g. " % len(rb_black)
                    + "; ".join("%s s=%.0f %.1f mm x %.1f mm -> %.4f"
                                % (b[1], b[2], 1000 * b[4], 1000 * b[5], b[0])
                                for b in sorted(rb_black)[:3]))
    chk("no recess renders as a black line at the declared sun",
        not rb_black,
        "%d closed recesses scanned at %.0f mm over %d cross-sections; darkest "
        "%.4f of the surface beside it (bound %.2f) — %s%s"
        % (rb_recess, 1000 * RB_STEP, len(rb_lines), rb_worst[0],
           WC.TOL_RECESS_RADIANCE, rb_worst[1], rb_tail))
    summary['recess_hairlines'] = rb_hair
    summary['recess_worst_radiance'] = round(rb_worst[0], 4)
    summary['recess_black_count'] = len(rb_black)
    # THE GATE, TESTED AGAINST THE ARTEFACT ALREADY KNOWN TO BE BAD.  If this ever
    # says the shipped defect is acceptable, the check has stopped measuring.
    chk("... and the check calls the recess that SHIPPED black",
        bool(WC.recess_is_black(0.005, 0.03424))
        and not bool(WC.recess_is_black(0.008, 0.005)),
        "5.0 x 34.24 mm (the measured defect) -> %.4f; the sawn bay joints beside "
        "it, 8 x 5 mm -> %.4f; bound %.2f"
        % (WC.recess_relative_radiance(0.005, 0.03424),
           WC.recess_relative_radiance(0.008, 0.005), WC.TOL_RECESS_RADIANCE))

    # -- 2c. THE THREE MARGINS AT THE GLASS PLANE AGREE  (defect #2) ----------
    tmin_c = float(getattr(WC, "ACCESS_RIBBON_T_MIN", -RIBBON_SAW_M))
    chk("the ribbon start cap is the contract's, not ours",
        abs(RIBBON_T_MIN - tmin_c) < 1e-12,
        "C.ACCESS_RIBBON_T_MIN = %.3f, this module cuts at t >= %.3f"
        % (tmin_c, RIBBON_T_MIN))
    # measure the cut line on the route centreline by bisection, in world x
    xa, xb = WC.ACCESS_GLASS_X - 4.0, WC.ACCESS_GLASS_X + 4.0
    for _ in range(60):
        xm = 0.5 * (xa + xb)
        if clear_c(*WC.world_to_circuit(np.array([xm]), np.array([0.0])))[0] > 0:
            xa = xm
        else:
            xb = xm
    x_cut = 0.5 * (xa + xb)
    poly = WC.access_ribbon_polygon(RIBBON_SAW_M)
    x_poly = float(poly[:, 0].min())
    chk("the paving cut line IS the glass plane",
        abs(x_cut - WC.ACCESS_GLASS_X) < 0.002 and
        abs(x_poly - WC.ACCESS_GLASS_X) < 0.002,
        "paving cuts at x = %.4f, C.access_ribbon_polygon(%.2f) starts at "
        "x = %.4f, C.ACCESS_GLASS_X = %.3f, terrain's mask reaches x = %.3f"
        % (x_cut, RIBBON_SAW_M, x_poly, WC.ACCESS_GLASS_X,
           float(np.min(np.arange(WC.ACCESS_GLASS_X - 4.0, WC.ACCESS_GLASS_X,
                                  0.02)[WC.road_corridor_mask(
               np.arange(WC.ACCESS_GLASS_X - 4.0, WC.ACCESS_GLASS_X, 0.02),
               np.zeros(200))]) if WC.road_corridor_mask(
               np.arange(WC.ACCESS_GLASS_X - 4.0, WC.ACCESS_GLASS_X, 0.02),
               np.zeros(200)).any() else WC.ACCESS_GLASS_X)))
    summary['paving_cut_x'] = round(x_cut, 4)

    # -- 3. Beat 4: one surface at every point on the review's own scan line --
    X = np.arange(-5.0, 111.001, 0.25)
    Y = np.zeros_like(X)
    z, own = wgz(X, Y)
    flips = int((own[1:] != own[:-1]).sum())
    chk("Beat-4 scan line has one owner at a time", flips <= 4,
        "%d ownership changes over 116 m" % flips)
    # the real test: does OUR mesh actually appear anywhere it should not?
    dg = bpy.context.evaluated_depsgraph_get()
    coplanar = []
    for i in range(0, len(X), 2):
        if own[i] in (WC.OWNER_APRON,):
            continue
        hits = []
        zt = 6.0
        for _ in range(8):
            hit, loc, nor, idx, ob, mtx = bpy.context.scene.ray_cast(
                dg, Vector((float(X[i]), 0.0, zt)), Vector((0, 0, -1)),
                distance=zt + 4.0)
            if not hit or not ob:
                break
            hits.append((float(loc.z), ob.name))
            zt = float(loc.z) - 1e-4
            if zt < -3.0:
                break
        arch = [h for h in hits if h[1].startswith("ARCH")]
        if arch and abs(arch[0][0] - float(z[i])) < TOL_COPLANAR:
            coplanar.append((round(float(X[i]), 2), arch[0][1],
                             round(arch[0][0] - float(z[i]), 4)))
    chk("no ARCH mesh coplanar with another module on the Beat-4 route",
        not coplanar, "%d samples: %s" % (len(coplanar), coplanar[:4]))

    # -- 4. the declared platform rectangles are respected -------------------
    A, W, _MM = _up_faces(["ARCH_Paving"], z_lo=-0.05, z_hi=0.05)
    if len(A) > 150000:
        step = int(math.ceil(len(A) / 150000))
        A, W = A[::step], W[::step]
    cx, cy = WC.world_to_circuit(A[:, 0], A[:, 1])
    inr = _fc_clearance(cx, cy) <= 0.62
    for rect in PLAT_RECTS.values():
        inr |= in_rect(cx, cy, rect, inset=-0.62)
    ex = sorted(set(W[i] for i in np.nonzero(~inr)[0][:200]))[:3]
    chk("paving stays inside the contract's declared rectangles",
        float((~inr).mean()) < 1e-6,
        "%d of %d flat-plane up-faces outside%s"
        % (int((~inr).sum()), len(A), ("  e.g. " + ", ".join(ex)) if ex else ""))

    # -- 4b. NO TWO OF OUR OWN SURFACES MAY BE COPLANAR ----------------------
    # The contract's rule for finding #2 is "cut, do not offset", and it applies
    # inside a module as well as between two.  A ray-cast sweep of the whole
    # precinct collects every stack of ARCH surfaces under a sample point and
    # fails on any pair closer than TOL_SELF.  This is what found the six real
    # z-fights the first contract-lit frames rendered as shattered concrete:
    # building bases and fence feet with their underside at exactly z = 0.000,
    # cable-duct covers 2.0 mm above the slab they overlapped, deck boards
    # sharing a plane with their own sub-frame, and the service road's markings
    # laid at the platform's MARK_Z instead of on the road's own camber.
    TOL_SELF = 0.0025
    rs = np.random.default_rng(11)
    ns = 9000
    scx = rs.uniform(-500.0, 200.0, ns)
    scy = rs.uniform(-70.0, 120.0, ns)
    swx, swy = WC.circuit_to_world(scx, scy)
    self_pairs = {}
    self_where = {}
    # PER-OBJECT casting, not a step-down through the scene.  Stepping the ray
    # down past each hit CANNOT see two surfaces at the same z -- the next ray
    # starts below both -- which is precisely the case that renders as shattered
    # concrete.  Asking each object for its own first surface finds them.
    arch = [ob for cn in ("ARCH_Paving", "ARCH_Ground", "ARCH_Grandstands",
                          "ARCH_Paddock", "ARCH_PitBuilding", "ARCH_PitWall",
                          "ARCH_Gantry", "ARCH_Bridges")
            for ob in (bpy.data.collections.get(cn).objects
                       if bpy.data.collections.get(cn) else [])
            if isinstance(ob.data, bpy.types.Mesh) and len(ob.data.polygons)]
    inv = [ob.matrix_world.inverted() for ob in arch]
    down = Vector((0, 0, -1))
    for i in range(ns):
        stack = []
        for ob, mi in zip(arch, inv):
            o = mi @ Vector((float(swx[i]), float(swy[i]), 8.0))
            d = (mi.to_3x3() @ down).normalized()
            hit, loc, nor, idx = ob.ray_cast(o, d, distance=12.0)
            if hit:
                stack.append((float((ob.matrix_world @ loc).z), ob.name))
        stack.sort(key=lambda t: -t[0])
        for j in range(len(stack) - 1):
            if abs(stack[j][0] - stack[j + 1][0]) < TOL_SELF:
                k = (stack[j][1], stack[j + 1][1])
                self_pairs[k] = self_pairs.get(k, 0) + 1
                self_where.setdefault(k, []).append(
                    (round(float(scx[i]), 1), round(float(scy[i]), 1),
                     round(stack[j][0], 4)))
    cross = {k: v for k, v in self_pairs.items() if k[0] != k[1]}
    intra = {k: v for k, v in self_pairs.items() if k[0] == k[1]}
    # TWO DIFFERENT OBJECTS sharing a plane is the defect: they are placed
    # independently, they carry different materials, and the pair renders as the
    # shattered patch the first apron frame showed.  A single generated object's
    # own internal overlap (a moulded seat's pad against its own front lip, a
    # modular block's terrace against its own floor band) is bounded, always the
    # same material, and never visible -- so it is MEASURED and reported rather
    # than asserted away.
    cw = sorted(cross.items(), key=lambda kv: -kv[1])[:3]
    iw = sorted(intra.items(), key=lambda kv: -kv[1])[:3]
    chk("no two DIFFERENT ARCH objects are coplanar",
        sum(cross.values()) <= 0.0005 * ns,
        "%d of %d sampled columns (%.3f %%, bound 0.05 %%)%s"
        % (sum(cross.values()), ns, 100.0 * sum(cross.values()) / ns,
           ("  " + "; ".join("%s|%s x%d @%s" % (a, b, n, self_where[(a, b)][0])
                             for (a, b), n in cw)) if cw else ""))
    chk("intra-object coplanarity stays under 0.15 %",
        sum(intra.values()) <= 0.0015 * ns,
        "%d of %d (%.3f %%)%s" % (sum(intra.values()), ns,
        100.0 * sum(intra.values()) / ns,
        ("  worst: " + ", ".join("%s x%d" % (a, n) for (a, _b), n in iw))
        if iw else ""))

    # -- 5. the lighting the materials were calibrated against ---------------
    lr = WC.lambert_radiance(0.18)
    chk("lighting reference is the contract's", abs(sum(lr) / 3 - 1.4888) < 5e-4,
        "lambert_radiance(0.18) = (%.4f, %.4f, %.4f), sun %.3f W/m2 at "
        "(%.3f, %.3f, %.3f), AgX %+.3f"
        % (lr[0], lr[1], lr[2], WC.SUN_ENERGY, WC.SUN_COLOR[0], WC.SUN_COLOR[1],
           WC.SUN_COLOR[2], WC.REFERENCE_EXPOSURE_EXTERIOR))

    summary['contract_checks'] = [(c[0], c[1], c[2]) for c in checks]
    summary['contract_fails'] = fails
    if verbose:
        print("\n--- CONTRACT GATE  (world_contract %s) ---" % WC.__version__)
        for nm, ok, d in checks:
            print("  %-56s %s  %s" % (nm, "PASS" if ok else "FAIL", d))
        print("--- %s ---\n" % ("ALL CLEAR" if not fails
                                else "%d FAILURES" % len(fails)))
    return fails


# --------------------------------------------------------------------------- #
#  11. BUILD                                                                    #
# --------------------------------------------------------------------------- #
def _purge():
    root = bpy.data.collections.get(COLL_ROOT)
    if root:
        for c in list(root.children_recursive) + [root]:
            for ob in list(c.objects):
                me = ob.data
                bpy.data.objects.remove(ob, do_unlink=True)
                if isinstance(me, bpy.types.Mesh) and me.users == 0:
                    bpy.data.meshes.remove(me)
        for c in list(root.children_recursive):
            bpy.data.collections.remove(c)
        bpy.data.collections.remove(root)
    for m in list(bpy.data.meshes):
        if m.users == 0 and m.name.startswith("ARCH"):
            bpy.data.meshes.remove(m)
    for m in list(bpy.data.materials):
        if m.name.startswith("A_") and m.users == 0:
            bpy.data.materials.remove(m)


def _collections():
    root = bpy.data.collections.new(COLL_ROOT)
    bpy.context.scene.collection.children.link(root)
    out = {}
    for n in SUBCOLLS:
        c = bpy.data.collections.new(n)
        root.children.link(c)
        out[n] = c
    return out


def build(verify=True):
    """Build the whole trackside built environment.  Idempotent."""
    import time
    t0 = time.time()
    _purge()
    build_materials()
    build_materials_extra()
    colls = _collections()
    summary = {'module': 'build_architecture'}
    garages = garage_specs(random.Random(1234))
    objs = []
    objs += build_paving(colls, random.Random(2001), summary)
    objs += build_apron_platform(colls, random.Random(2011), summary)
    objs += build_markings(colls, random.Random(2002), garages, summary)
    objs += build_paddock_ground(colls, random.Random(2012), summary)
    objs += build_pit_building(colls, random.Random(2003), garages, summary)
    objs += build_race_control(colls, random.Random(2004), summary)
    objs += build_gantry(colls, random.Random(2005), summary)
    objs += build_pit_wall(colls, random.Random(2006), summary)
    objs += build_grandstands(colls, random.Random(2007), summary)
    objs += build_paddock(colls, random.Random(2009), summary)
    objs += build_bridges(colls, random.Random(2010), summary)
    objs = [o for o in objs if o]
    _assert_no_corridor()
    bpy.context.view_layer.update()
    cull_unowned(summary)
    embed_ground_contacts(summary)
    base_tris = 0
    for ob in objs:
        for p in ob.data.polygons:
            base_tris += max(0, p.loop_total - 2)
    # THE ONE THING THE WORLD BUILD CANNOT BUILD, STATED SO IT CANNOT BE MISSED.
    # The corridor mouth behind the glass plane is the round-1 pavilion's floor.
    # This module casts the formation that floor sits on and nothing else,
    # because the floor's finished level IS C.APRON_Z and two slabs at 0.000 in
    # the frame the car breaches the glass is exactly the coplanar defect this
    # whole round exists to close.
    summary['r1_floor_interface'] = {
        'floor_rect_world': [-15.0, 15.0, -11.0, 11.0],
        'floor_top_z': R1_FLOOR_TOP_Z, 'floor_soffit_z': R1_FLOOR_SOFFIT_Z,
        'arch_formation_z': R1_FORMATION_Z,
        'shell_rect_world': list(R1_SHELL),
        'source': 'opus5-car-render/f1_showroom.blend, objects Floor / Wall_*',
        'requires': 'the assembly must composite round-1 `Floor`; without it the '
                    'mouth reads as a 100 mm formation step -- ground, not a hole'}
    summary['objects'] = len(objs)
    summary['base_tris'] = base_tris
    summary['materials'] = len(MATS)
    summary['contract'] = WC.__version__
    summary['build_s'] = round(time.time() - t0, 1)
    root = bpy.data.collections.get(COLL_ROOT)
    if root:
        WC.stamp(root)                       # the .blend records its contract
    if verify:
        bpy.context.view_layer.update()
        summary['contract_fails'] = verify_contract(summary)
        summary['sightline_fails'] = verify_sightlines(summary)
    print(json.dumps({k: v for k, v in summary.items()
                      if k not in ('sightline_checks', 'contract_checks')},
                     indent=1))
    return summary


# --------------------------------------------------------------------------- #
#  12. TEST SCENE + RENDERS   (nothing here is part of build())                 #
# --------------------------------------------------------------------------- #SUN_DIR = Vector(WC.SUN_DIR).normalized()
RENDER_DIR = "/home/zany/f1-round2/render/world/architecture"


def _contract_proxies(showroom=True, r1floor=False):
    """The NEIGHBOURS, meshed from the contract, so a test render shows this
    module's geometry against the ground the other five have agreed to build —
    not against a flat plane of its own invention.

    None of this is part of build().  It exists so that 'verify against your
    neighbours' means something before the neighbours have shipped: the road
    corridor here is C.ground_z sampled on a (s, u) grid, and the terrain plate
    is deliberately drawn 0.20 m BELOW C.APRON_Z so that anywhere this module's
    platform is not properly retained shows up as a black slot.
    """
    # ---- the road corridor: build_surface + build_barriers, from the datum ---
    ds, du = 2.5, 1.6
    S = np.arange(0.0, WC.LAP, ds)
    mb = MB("PROXY_RoadCorridor")
    for side in (+1, -1):
        E = WC.platform_edge(S, side)
        V = WC.verge_edge(S)
        Hw = WC.half_width(S)
        AP = WC.apron_zone(S, side)
        for i in range(len(S) - 1):
            a, b = float(S[i]), float(S[i + 1])
            lim = float(max(E[i], E[i + 1]))
            # C.platform_owner hands the pit-exit apron to THIS module, so the
            # proxy must stop at verge_edge there.  Meshing it anyway put the
            # stand-in exactly coplanar with ARCH_Paving_ApronPlatform over
            # 5 800 m2 and rendered as shattered concrete in arch_apron_rim --
            # a scaffolding defect that looked exactly like a shipped one.
            if float(AP[i]) > 0.5:
                lim = float(max(V[i], V[i + 1]))
            nu = max(3, int(lim / du))
            for j in range(nu):
                ua = lim * j / nu
                ub = lim * (j + 1) / nu
                q = WC.su_to_world(np.array([a, b, b, a]),
                                   np.array([ua, ua, ub, ub]) * side)
                mid = 0.5 * (ua + ub)
                if mid <= float(Hw[i]):
                    m, c = "A_Tarmac", (1, 1, 1, 1)
                elif mid <= float(V[i]):
                    m, c = "A_Tarmac", (1.35, 1.35, 1.35, 1)
                else:
                    m, c = "A_Asphalt", (0.80, 0.82, 0.80, 1)
                mb.add([tuple(p) for p in q], [(0, 1, 2, 3)], m, c)
    mb.build(bpy.context.scene.collection, matrix=Matrix.Identity(4))
    # ---- the access ribbon: build_surface, from C.access_z ------------------
    mb = MB("PROXY_AccessRibbon")
    T = np.arange(0.0, WC.ACCESS_TOTAL, 2.0)
    for i in range(len(T) - 1):
        t0, t1 = float(T[i]), float(T[i + 1])
        vi0, vo0 = WC.access_edges(np.array([t0]))
        vi1, vo1 = WC.access_edges(np.array([t1]))
        nvv = 6
        for j in range(nvv):
            a0 = float(vi0[0]) + (float(vo0[0]) - float(vi0[0])) * j / nvv
            a1 = float(vi0[0]) + (float(vo0[0]) - float(vi0[0])) * (j + 1) / nvv
            b0 = float(vi1[0]) + (float(vo1[0]) - float(vi1[0])) * j / nvv
            b1 = float(vi1[0]) + (float(vo1[0]) - float(vi1[0])) * (j + 1) / nvv
            P = []
            for (tt, vv) in ((t0, a0), (t1, b0), (t1, b1), (t0, a1)):
                x, y, h = WC.access_route_point(tt)
                P.append((x - math.sin(h) * vv, y + math.cos(h) * vv,
                          WC.access_z(tt, vv)))
            mb.add(P, [(0, 1, 2, 3)], "A_Tarmac", (1.05, 1.05, 1.05, 1))
    mb.build(bpy.context.scene.collection, matrix=Matrix.Identity(4))
    # ---- build_surface's SURF_ApronJoint, from ITS published profile ---------
    # The asphalt-to-concrete joint at the pit-exit apron edge is build_surface's
    # geometry (see APRON_JOINT_LAP_M).  It is meshed here so the apron_edge probe
    # renders what the assembled world will show and not a 50 mm groove that only
    # exists because the neighbour is absent from the test scene.
    mb = MB("PROXY_ApronJoint")
    L, dJ = APRON_JOINT_LAP_M, APRON_JOINT_DEPTH_M
    prof = [(0.00 * L, 0.0), (0.16 * L, -dJ), (0.44 * L, -dJ),
            (0.64 * L, -0.32 * dJ), (1.00 * L, -0.32 * dJ)]
    Sj = np.arange(3186.0, 3436.0, 1.0)
    Sj = Sj[WC.apron_zone(Sj, +1) > 0.5]
    for i in range(len(Sj) - 1):
        a, b = float(Sj[i]), float(Sj[i + 1])
        for k in range(len(prof) - 1):
            (o0, z0), (o1, z1) = prof[k], prof[k + 1]
            q = WC.su_to_world(np.array([a, b, b, a]),
                               np.array([WC.verge_edge(np.array([a]))[0] + o0,
                                         WC.verge_edge(np.array([b]))[0] + o0,
                                         WC.verge_edge(np.array([b]))[0] + o1,
                                         WC.verge_edge(np.array([a]))[0] + o1]))
            mb.add([(q[0][0], q[0][1], q[0][2] + z0),
                    (q[1][0], q[1][1], q[1][2] + z0),
                    (q[2][0], q[2][1], q[2][2] + z1),
                    (q[3][0], q[3][1], q[3][2] + z1)],
                   [(0, 1, 2, 3)], "A_Asphalt", (0.55, 0.55, 0.55, 1))
    mb.build(bpy.context.scene.collection, matrix=Matrix.Identity(4))
    # ---- build_terrain's ground, deliberately 0.20 m low --------------------
    mb = MB("PROXY_Terrain")
    mb.box((-1400.0, -900.0, -6.0), (900.0, 1000.0, -0.20), "A_Soil",
           (0.72, 0.86, 0.52, 1))
    mb.build(bpy.context.scene.collection, matrix=Matrix.Identity(4))
    # ---- the round-1 pavilion, to ITS measured plan --------------------------
    # The shell is open on +x because by Beat 4 the glass is breached, and the
    # corridor-mouth probes have to be able to see the ground this module lays
    # behind the glass plane.  `r1floor` meshes round 1's own `Floor` (top z =
    # 0.000, soffit -0.060, x -15..15, y -11..11) so the mouth can be rendered
    # BOTH ways: without it, this module's formation slab is what you see and it
    # had better be closed; with it, the film's actual surface is what you see and
    # this module's slab had better be 100 mm under it and invisible.
    if showroom:
        mb = MB("PROXY_Showroom")
        # open on +x (breached) AND open on -z, so a downward probe inside the
        # shell reports the ground this module built and not the proxy's own lid.
        mb.box((R1_SHELL[0], R1_SHELL[2], 0.0), (R1_SHELL[1], R1_SHELL[3], 10.4),
               "A_ConcPrecast", (0.9, 0.9, 0.9, 1), skip="xpzn")
        mb.build(bpy.context.scene.collection, matrix=Matrix.Identity(4))
    if r1floor:
        mb = MB("PROXY_R1Floor")
        mb.box((-15.0, -11.0, R1_FLOOR_SOFFIT_Z), (15.0, 11.0, R1_FLOOR_TOP_Z),
               "A_ConcPrecast", (0.86, 0.86, 0.85, 1))
        mb.build(bpy.context.scene.collection, matrix=Matrix.Identity(4))
    # ---- the Beat-4 corridor walls, which are build_barriers' now -----------
    mb = MB("PROXY_TransitWalls")
    for side, top in ((+1, WC.TRANSIT_NORTH_TOP_Z), (-1, WC.TRANSIT_SOUTH_TOP_Z)):
        t0, t1 = WC.transit_wall_span(side)
        n = int((t1 - t0) / 2.0)
        for k in range(n):
            p0 = WC.transit_wall_point(t0 + (t1 - t0) * k / n, side)
            p1 = WC.transit_wall_point(t0 + (t1 - t0) * (k + 1) / n, side)
            mb.add([(p0[0], p0[1], p0[2] - 0.2), (p1[0], p1[1], p1[2] - 0.2),
                    (p1[0], p1[1], p1[2] + top), (p0[0], p0[1], p0[2] + top)],
                   [(0, 1, 2, 3)], "A_ConcBoard", (0.9, 0.9, 0.89, 1))
    mb.build(bpy.context.scene.collection, matrix=Matrix.Identity(4))


def _test_env(proxies=True, showroom=True, r1floor=False):
    """Sun, sky and exposure taken VERBATIM from the contract (S8).

    build_terrain.md S2.1 published a lighting rig that does not exist — sun
    120 W/m2 at (1.000, 0.735, 0.470), aerosol 1.45, ozone 1.80, direct:diffuse
    3.0:1, AgX -2.70 — and told everyone to adopt it.  build_sky shipped
    115.754 W/m2 at (1, 0.71632, 0.38712), aerosol 0.45, ozone 1.30, AgX -3.048,
    and the contract records those as the film's light.  Every render under
    render/world/architecture/ is lit by exactly these numbers, so the images are
    also a test of C.lambert_radiance."""
    sc = bpy.context.scene
    # --factory-startup ships a default Cube, Camera and Light.  They were being
    # saved into every test blend — a 2 m cube at the world origin, which is
    # inside the showroom — and the keep-out gate duly reported it as an object
    # in the car's path.  Scaffolding must not look like geometry.
    for ob in list(bpy.data.objects):
        if ob.name in ("Cube", "Light", "Camera") and not any(
                c.name.startswith(("ARCH", "PROXY")) for c in ob.users_collection):
            bpy.data.objects.remove(ob, do_unlink=True)
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'GPU'
    try:
        cp = bpy.context.preferences.addons['cycles'].preferences
        cp.compute_device_type = 'OPTIX'
        for d in cp.get_devices_for_type('OPTIX'):
            d.use = ('CPU' not in d.name.upper())
    except Exception as e:
        print("GPU setup:", e)
    w = bpy.data.worlds.new("ARCH_TESTWORLD")
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputWorld')
    bg = nt.nodes.new('ShaderNodeBackground')
    sky = nt.nodes.new('ShaderNodeTexSky')
    sky.sky_type = WC.SKY_MODEL              # MULTIPLE_SCATTERING in Blender 5.x
    sky.sun_elevation = math.radians(WC.SUN_ELEV_DEG)
    sky.sun_rotation = math.radians(WC.SKY_SUN_ROTATION_DEG)
    sky.sun_disc = WC.SKY_SUN_DISC
    # Blender 5.x: air_density / aerosol_density / ozone_density.  There is no
    # `dust_density` any more and no NISHITA enum -- both cost a build.
    for k, v in (('air_density', WC.SKY_AIR),
                 ('aerosol_density', WC.SKY_AEROSOL),
                 ('dust_density', WC.SKY_AEROSOL),
                 ('ozone_density', WC.SKY_OZONE),
                 ('altitude', WC.SKY_ALTITUDE),
                 ('sun_intensity', 1.0),
                 ('sun_size', math.radians(WC.SUN_ANGULAR_DIAM_DEG)),
                 # ground_albedo defaults to 0.3 and adds a bounce the GEOMETRY
                 # already provides.  Left at the default an albedo-0.18 card
                 # rendered 7.0/7.9/9.1 % over C.lambert_radiance(0.18); at 0.0
                 # it lands inside 1 %.  Measured, see build_architecture.md S9.
                 ('ground_albedo', 0.0)):
        if hasattr(sky, k):
            setattr(sky, k, v)
    # THE TEST RIG IS NOT build_sky.  build_sky reaches C.SKY_IRRADIANCE with a
    # low sky-node aerosol PLUS 1.1 km of explicit aerosol geometry; this
    # scaffolding has the node and not the geometry, so its sky comes out hot:
    # MEASURED, an albedo-0.18 lambertian card renders (1.7915, 1.5759, 1.4537)
    # against C.lambert_radiance(0.18) = (1.6744, 1.4600, 1.3321), i.e. +7.0 /
    # +7.9 / +9.1 %.  Subtracting the sun's own E_DIRECT_HORIZONTAL leaves a sky
    # of (6.27, 9.60, 15.69) W/m2 against the contract's (4.228, 7.577, 13.573),
    # whose means are 10.52 and 8.459.  So the background is scaled by
    # 8.459 / 10.52 = 0.804 and the frames are then exposure-correct at
    # C.REFERENCE_EXPOSURE_EXTERIOR.  The residual is TINT, not level, and it is
    # build_sky's aerosol layer -- see build_architecture.md S9.
    SKY_TEST_STRENGTH = 0.804
    bg.inputs['Strength'].default_value = WC.SKY_STRENGTH * SKY_TEST_STRENGTH
    nt.links.new(sky.outputs[0], bg.inputs[0])
    nt.links.new(bg.outputs[0], out.inputs[0])
    lt = bpy.data.lights.new("ARCH_SUN", 'SUN')
    lt.energy = WC.SUN_ENERGY
    lt.color = WC.SUN_COLOR
    lt.angle = math.radians(WC.SUN_ANGULAR_DIAM_DEG)
    ob = bpy.data.objects.new("ARCH_SUN", lt)
    sc.collection.objects.link(ob)
    # A Blender SUN emits along its local -Z, so local +Z must be C.SUN_DIR (the
    # direction TO the sun).  Negating it buries the sun below the horizon and
    # gives a shadowless sky-only render -- which is exactly what the first
    # contract-lit test frame showed.
    ob.rotation_euler = Vector(WC.SUN_DIR).to_track_quat('Z', 'Y').to_euler()
    sc.view_settings.view_transform = WC.VIEW_TRANSFORM
    try:
        sc.view_settings.look = WC.VIEW_LOOK
    except Exception:
        pass
    sc.view_settings.exposure = WC.REFERENCE_EXPOSURE_EXTERIOR
    if proxies:
        _contract_proxies(showroom=showroom, r1floor=r1floor)


def _cam(name, loc, aim, lens):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = 36.0
    ob = bpy.data.objects.new(name, cd)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    d = Vector(aim) - Vector(loc)
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return ob


# The camera set is deliberately SMALL.  The 5090 worker prewarms every camera in
# a .blend at load and 19 of them blew its readiness probe, so each render batch
# ships at most a handful.
CAMSETS = {
    # what the contract actually changed
    'beat4_route':   ((34.0, 0.0, 5.6), (128.0, 12.0, 1.4), 28.0),
    'beat4_low':     ((52.0, -3.2, 1.35), (150.0, 26.0, 1.2), 32.0),
    'apron_rim':     ((-268.0, 47.0, 3.2), (-236.0, 22.0, 0.2), 35.0),
    'pitlane':       ((-150.0, 17.5, 2.30), (30.0, 25.0, 5.0), 32.0),
    'pitwall_rim':   ((-70.0, 14.6, 1.05), (60.0, 12.6, 0.55), 40.0),
    # the ground-detail pass
    'paddock_eye':   ((-330.0, 70.0, 1.62), (-160.0, 84.0, 2.4), 35.0),
    'paddock_road':  ((-268.0, 88.5, 2.1), (-90.0, 78.0, 1.4), 30.0),
    'compound':      ((-390.0, 96.0, 3.4), (-455.0, 100.0, 1.2), 30.0),
    # the wide reads
    'aerial':        ((-330.0, -300.0, 240.0), (-120.0, 10.0, 6.0), 35.0),
    'aerial_pad':    ((-260.0, -60.0, 150.0), (-300.0, 80.0, 4.0), 40.0),
    'grandstand':    ((-58.0, -28.0, 21.0), (-66.0, -50.0, 5.0), 30.0),
    'passerelle':    ((-498.0, 1.5, 2.6), (-436.0, 3.0, 7.2), 30.0),
    'beat6_key0':    (None, None, 24.0),      # world-frame, from the beat sheet
    # --- the two assembly defects, framed so the answer is visual -------------
    # THE CORRIDOR MOUTH.  Low, inside the pavilion footprint, looking out along
    # the ribbon: the shot CAM_GLASS_GAP.png took, which showed this module's
    # forecourt sub-base as an open eggcrate behind a 0.300 m black slot.
    'glass_mouth':   ((7.5, 1.6, 0.95), (70.0, 6.0, 0.55), 30.0),
    # ... and the threshold itself, raked at the sun's own bearing so a joint 1 mm
    # wide draws whatever shadow it has.
    'glass_thresh':  ((11.2, -8.4, 0.42), (17.6, 7.5, -0.05), 42.0),
    # ... and CAM_GLASS_GAP.png's own framing: 0.30 m off the ground, 5 m back
    # from the breach plane, looking straight out through it.  That is the frame
    # that showed a 0.300 m black slot with this module's coffered sub-base
    # behind it, and it is the frame that has to show continuous ground now.
    'glass_gap':     ((10.0, 0.0, 0.30), (26.0, 1.0, 0.05), 35.0),
    # THE PIT-EXIT APRON EDGE.  Down 190 m of the joint, 1.10 m up, with the sun
    # 97 % across the joint at 12.47 deg: a 12 mm slot 300 mm deep is a black line
    # in this frame and a sealed 50 mm joint is a grey one.
    'apron_edge':    ((-31.9, -114.9, 1.10), (111.7, 1.5, 0.00), 50.0),
    'apron_joint':   ((-9.0, -102.9, 0.34), (35.3, -63.1, -0.12), 70.0),
    # ... and a macro on the joint itself: 8.4 m of it across the frame, the
    # camera 0.90 m up and 2.7 m inboard, so a 1 mm slot is 4 px wide at 4K.
    'apron_macro':   ((29.047, -64.970, 0.778), (36.879, -61.858, -0.122), 50.0),
}
WORLD_CAMS = {'beat4_route', 'beat4_low', 'beat6_key0',
              'glass_mouth', 'glass_thresh', 'apron_edge', 'apron_joint',
              'apron_macro', 'glass_gap'}


def _test_cams(which):
    cams = {}
    for nm in which:
        if nm not in CAMSETS:
            continue
        p, q, lens = CAMSETS[nm]
        if nm == 'beat6_key0':
            cams[nm] = _cam(nm, KEY0_W, LINE_W, lens)
            continue
        if nm in WORLD_CAMS:
            cams[nm] = _cam(nm, p, q, lens)
        else:
            cams[nm] = _cam(nm, c2w(p[0], p[1], p[2]), c2w(q[0], q[1], q[2]),
                            lens)
    return cams


def save_test_blend(which, path, proxies=True, showroom=True, r1floor=False):
    """Build + a small camera set + the contract's light, saved for the 5090."""
    _test_env(proxies=proxies, showroom=showroom, r1floor=r1floor)
    _test_cams(which)
    bpy.ops.wm.save_as_mainfile(filepath=path)
    print("saved", path, "cameras:", list(which))
    return path


def render_tests(which=('beat4_route', 'paddock_eye', 'aerial'),
                 res=(1280, 720), samples=64):
    os.makedirs(RENDER_DIR, exist_ok=True)
    _test_env()
    cams = _test_cams(which)
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 6
    sc.cycles.transmission_bounces = 4
    sc.render.film_transparent = False
    sc.render.image_settings.file_format = 'PNG'
    for nm in which:
        if nm not in cams:
            continue
        sc.camera = cams[nm]
        sc.render.filepath = os.path.join(RENDER_DIR, "arch_%s.png" % nm)
        print("rendering", nm)
        bpy.ops.render.render(write_still=True)
    return [os.path.join(RENDER_DIR, "arch_%s.png" % n) for n in which]

if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    s = build(verify=True)
    fails = (s.get('contract_fails') or []) + (s.get('sightline_fails') or [])
    if "--render" in argv:
        i = argv.index("--render")
        sel = argv[i + 1] if len(argv) > i + 1 else "beat4_route,paddock_eye,aerial"
        res = (1280, 720)
        samples = 64
        if "--res" in argv:
            res = tuple(int(v) for v in argv[argv.index("--res") + 1].split("x"))
        if "--samples" in argv:
            samples = int(argv[argv.index("--samples") + 1])
        render_tests(tuple(sel.split(",")), res, samples)
    if "--save" in argv:
        i = argv.index("--save")
        path = (argv[i + 1] if len(argv) > i + 1 and not argv[i + 1].startswith("-")
                else "/home/zany/f1-round2/world/architecture_test.blend")
        cams = ('beat4_route', 'paddock_eye', 'aerial')
        if "--cams" in argv:
            cams = tuple(argv[argv.index("--cams") + 1].split(","))
        save_test_blend(cams, path, proxies=("--noproxy" not in argv),
                        showroom=("--noshowroom" not in argv),
                        r1floor=("--r1floor" in argv))
    if fails:
        print("GATE FAILURES: %d" % len(fails))
        sys.exit(1)
