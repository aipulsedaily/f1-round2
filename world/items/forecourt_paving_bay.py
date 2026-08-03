#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
forecourt_paving_bay.py -- per-item hero campaign, item ``forecourt_paving_bay``
(zone ``showroom_breach``, wave 1, build order 24, HERO, 1400 instances).

WHAT THIS IS
============
The showroom forecourt: large-format PRECAST concrete flags, 1500 x 1000 mm,
laid to the building's grid on a mortar/sand bed, each one an individual slab
with its own laying level, its own warp, its own arris, its own chips and its
own history.  Not a scored plane.  The joints are modelled SLOTS with walls, a
jointing bed that has washed out by its own amount along every metre, detritus,
moss and weeds; the trench reinstatements are real asphalt panels with a sawn
edge and a bitumen overband; and the flags the pavers CUT on site have a
different edge from the flags that came out of the mould.

THIS IS NOT THE PADDOCK APRON.  ``paddock_paving_bay`` is cast-in-situ concrete:
one continuous pour, saw kerfs cut into it the next morning, a broom finish, a
wheel-track polish.  This is a different trade with different tools.  Precast
flags arrive finished, get bedded one at a time, rock when the bed is short,
lip against each other at 2-4 mm, spall at the corners when a wheel loads an
unsupported edge, and are cut with a disc when they meet the building or the
road.  Every one of those is a different geometric signature, and none of the
code, the fields or the materials here are shared with that module.

THE ARITHMETIC THAT SETS THE DETAIL FLOOR
-----------------------------------------
    manifest: nearest_camera_m = 1.7, lens_at_closest_mm = 35, HERO,
              onscreen_px_4k = 2160 over px_measured_dimension_m = 1.0

    px_per_m = (3840 * 35 / 36) / 1.7 = 2196.1 px/m   ->   1 px = 0.4554 mm

which is the closest any ground surface in this film is filmed.  On the 4K
master, at the contract sun (elevation 12.4706 deg, shadow ratio 4.5222):

    a 5.0 mm cast arris chamfer       11.0 px, and throws 22.6 mm = 49.6 px
                                      of shadow into the joint
    a 12 mm joint slot                26.4 px wide, and at 14 mm deep it is
                                      fully occluded -- a real black line with
                                      a lit north wall, not a painted one
    a 3.0 mm flag-to-flag lip          6.6 px, throws 13.6 mm = 29.8 px
    a 6 mm exposed aggregate grain    13.2 px  -- individually visible
    a 14 mm coarse stone              30.7 px, throws 63 mm = 139 px
    a 2.5 mm grain of washed-out       5.5 px, throws 11 mm = 25 px
      jointing grit
    a 0.8 mm matrix erosion            1.8 px, throws 3.6 mm = 7.9 px
    a 2 mm arris chip                  4.4 px
    0.85 mm mesh pitch (near field)    1.9 px  -- the geometry floor
    0.25 mm saw-blade score            0.55 px -- BELOW the pixel: this one
                                      layer is a bump, and it is the only
                                      thing on this item that is

Everything above 1 px in that table exists as MESH.  At a 12.5 deg sun the read
of any pavement is the shadow its relief throws, and a bump map throws none.

THE PUBLIC INTERFACE  (this item is a FOUNDATION -- 3 items depend on it)
========================================================================
Dependants named in the manifest: ``concrete_spall_debris`` (400 pieces that
skitter across this surface), ``glass_shard_fan_settled`` (a 40 m fan that
lands on it and must still be there in Beat 6), ``forecourt_bollard`` (6, at
world X = 19.5).  None of them can ask questions, so:

--- 1. WHERE THE SURFACE IS ------------------------------------------------

    surface_z(x, y)        -> z of the flag top at any WORLD point, metres.
    flag_top_z(x, y)       -> (z, flag_index or -1) same thing, with identity.

    This is the level a straightedge reads: flag datum + bed settlement + rock
    + warp.  It does NOT include the finish relief (-0.9..+1.4 mm of aggregate
    and matrix) or the chips, because anything RESTING on the flag bridges
    those.  A shard, a spall fragment, a bollard base plate sits on this.

    In the joints it returns the JOINT BED level instead -- the surface a
    fragment that fell into the joint actually comes to rest on.  Use
    ``on_flag(x, y)`` to tell which of the two you got.

    C.world_ground_z(x, y) returns APRON_Z = 0.000 exactly over this whole
    region.  THIS MODULE IS THE MESH UNDER THAT NUMBER and it is not flat.
    Measured bounds against that datum, over the whole 1 000+ flag field, are
    reported by verify() and asserted here as hard limits:

        FLAG_TOP_MAX_M = +0.0035   never higher, so build_architecture's
                                   MARK_Z = 0.0075 thermoplastic still has
                                   4.0 mm of air over the proudest flag corner
        FLAG_TOP_MIN_M = -0.0090   never lower

    A module that keeps calling C.world_ground_z is within +3.5 / -9.0 mm of
    this concrete.  A module that calls surface_z is exact.

--- 2. THE JOINTS ----------------------------------------------------------

    joint_segments(flags) -> [Joint, ...]   every joint in the field:

        p0, p1      world endpoints of the joint CENTRELINE
        axis        'x' or 'y' -- the direction the joint runs
        kind        'formed' (both edges came out of the mould) or
                    'sawn'   (at least one edge was cut on site)
        width_m     clear width at the top, 7..22 mm
        arris_z0/1  flag top z either side at each end (they differ: flags lip)
        bed_z       z of the JOINTING BED -- the level a seed germinates on
                    and a 3 mm glass chip comes to rest on.  6..30 mm below
                    the arris, and it varies ALONG the joint:
                    ``joint_bed_z(joint, t)``
        weeded      True on the 18 % the manifest declares colonised
        overband    True where a trench reinstatement's bitumen covers it
        left/right  flag indices either side

    FORECOURT JOINT COLONISATION IS BUILT BY THIS MODULE.  ``weeded`` marks the
    joints that ALREADY CARRY a plant emitted from here.  A dependant adding
    vegetation must place on ``weeded == False`` joints or it will grow a
    second plant through the first one.

--- 3. LETTING SOMETHING INTO THE PAVING -----------------------------------

    reserve_circle(x, y, r, kind)    a cored socket: the flags are recessed to
    reserve_rect(x0, x1, y0, y1)     SOCKET_FLOOR_M with a sawn wall and a
                                     grout collar, so a bollard drops into a
                                     real pocket instead of z-fighting a slab
                                     that is still there.  Call BEFORE build().

    BOLLARD_SOCKETS   the 6 sockets this module builds by default, at the
                      contract's FORECOURT_BOLLARD_X = 19.5, y = +-9.0, +-10.8,
                      +-12.6.  ``forecourt_bollard`` should read this list
                      rather than invent positions; if it wants others it calls
                      reserve_circle() first and passes replace=True.
    SOCKET_R_M        0.180   cored radius
    SOCKET_FLOOR_M   -0.045   pocket floor below datum
    COLLAR_TOP_M     -0.004   grout collar top, i.e. 4 mm below the arris

--- 4. THE LAYING PLAN -----------------------------------------------------

    flag_layout(rect, seed) -> [Flag, ...]     deterministic.  Same seed, same
                                               flags, forever -- a dependant
                                               can recompute the plan without
                                               this module having emitted
                                               anything.

    SET OUT FROM THE BUILDING, CUT AT THE BOUNDARY, which is what a paving gang
    actually does and what makes the grid legible:

        the x course lines are  x = 15.000 - k * 1.500   (15.000 is
                                C.ACCESS_GLASS_X, the breach plane, so the
                                first course butts the sill dead on)
        the y course lines are  y = j * 1.000            (0.000 is the
                                building centreline)

    Westward that divides the 42.0 m to the forecourt edge into 28 whole
    courses exactly.  Eastward it leaves 0.500 m at x = 25.5..26.0, and that
    strip is CUT -- 44 sawn slivers along the outer edge.  The pavilion
    (C R1_SHELL) and the access ribbon (|y| <= 6.3 for x >= 15) are cut out the
    same way, and every cut face carries the sawn edge treatment.  That is
    where the manifest's first variation axis, "saw-cut vs formed joint", comes
    from: it is the construction sequence, not a coin flip.

--- 5. WHAT A DEPENDANT NEEDS TO KNOW ABOUT THE MATERIAL -------------------

    bake_flag_attrs(mesh, **overrides)   writes all 8 vertex attributes this
                                         module's materials read, so a
                                         dependant emitting geometry INTO
                                         mat_flag() does not get a surface
                                         that silently reads zero.
    ATTRS = ('agg','aggid','wear','soil','damp','stain','stype','arr')

THE FOUR DECLARED VARIATION AXES, AND WHERE EACH ONE LIVES
==========================================================
  saw-cut vs formed joint   Joint.kind, and it is GEOMETRY: a formed edge has a
                            5 mm cast chamfer with a mould radius and a mould
                            line 22 mm down the face; a sawn edge is square to
                            0.6 mm, shows the aggregate cut through in section,
                            chips 2.4x more often, and its face carries the
                            blade's score.  MEASURED over the built field:
                            188 of 2 032 joints (9.25 %) are sawn -- at the
                            road, at the building, around every reinstatement,
                            and around the 48 flags (4.7 %) that have been
                            lifted and replaced with one cut from stock.  That
                            last source is what puts a sawn joint in the MIDDLE
                            of the field where the lens is, not only at its
                            edge.
  weed colonisation ~18 %   Joint.weeded, and it is GEOMETRY: 4 species, every
                            tuft generated from its own seed, growing from the
                            bed level inside the slot so the slot walls occlude
                            them correctly.  MEASURED 17.91 % (364 of 2 032),
                            and it is not scattered evenly: the probability is
                            driven by damp, joint width and traffic, so the
                            colonists cluster along the shade line and the
                            frontage instead of dotting the field like confetti.
  2.4 % reinstated asphalt  five trench reinstatements laid out as a real
                            staircase along the joint grid, asphalt panel +
                            sawn flag edges + a 55 mm bitumen overband.
                            MEASURED 25 of 1 050 cells = 2.381 %.
  stain                     seven independent stain systems (_stain_fields):
                            iron, oil, rubber, algae/biofilm, efflorescence,
                            rain-shed patina, and the GHOST of the seven pieces
                            of forecourt furniture that stood in one place long
                            enough to leave a pale disc, a dirt rim and four
                            rust points (FURNITURE_MARKS).  Each has its own
                            spatial law; none of them is a noise multiplied by
                            a colour.

WHAT THE ASSEMBLY MUST DELETE BEFORE THIS ITEM IS LINKED IN
===========================================================
``build_architecture`` still builds the class-level forecourt as
``ARCH_Paving_Forecourt``: a 1.5 x 1.0 m grid of FLAT QUADS at Z_BAY = 0.000
with a 0..2.5 mm random offset, plus its sub-base prism.  THIS MODULE REPLACES
THE BAYS AND ONLY THE BAYS.  Linking both gives a coplanar pair over 1 445 m2 at
a 0-3.5 mm offset -- the exact z-fight class the assembly review has already
found twice -- so the assembly must, in this order:

  1. delete the bay faces of ``ARCH_Paving_Forecourt`` (material
     ``A_ForecourtSlab``, the polygons at z ~ 0.000);
  2. KEEP its sub-base prism (-0.30..-0.012) and its formation slab under the
     pavilion (R1_FORMATION_Z), which this module does not build;
  3. keep its granite edge band and slot drain at the forecourt perimeter,
     which this module deliberately stops short of;
  4. link this collection and pass build()'s ``bedding=False`` if the
     architecture sub-base is present, so the two beds do not overlap.

THE 300 mm THE CONTRACT LEAVES TO NOBODY
=========================================
``apron_platform_mask`` subtracts the ribbon plus C.ACCESS_RIBBON_SAW_M, so
architecture's paving stops at |y| = 6.300 for x >= 15; ``in_access_ribbon`` at
margin 0 puts the road's own surface at |y| = 6.000.  MEASURED, both, over the
whole forecourt.  ``world_ground_z`` hands the 300 mm between them to
OWNER_APRON and nothing builds it.  This module fills it as the sawn edge strip
it physically is (see ``_edge_joints``), everywhere between -4 and -16 mm, and
stops 12 mm clear of the road.  IF ``tools/placement_gate.py`` COUNTS THAT STRIP
AS ROAD CORRIDOR, this item is an edge-definer there and should be held to the
true half-width (6.000), not to the courtesy margin -- or build() should be
called with ``ribbon_strip=False`` and the contract defect fixed at its source.

WHAT IS INSTANCED AND WHAT IS NOT, HONESTLY
===========================================
Flags within ``explicit_r`` of the lens are individual unique meshes at a pitch
that resolves 2 px at their own distance.  Beyond it they come from LIBRARIES
of unique flag meshes, one library per cut size, every member generated from
its own seed -- a different warp, a different arris, different chips, a
different crack, different stains.  The report carries the repeat factor, and
verify() prints it per bucket.  Transform randomisation is NOT counted as
variation anywhere in this module.
"""

import argparse
import json
import math
import os
import sys
import time

import numpy as np

try:
    import bpy
    from mathutils import Vector, Matrix
except Exception:                                    # pragma: no cover
    bpy = None

# --------------------------------------------------------------------------- paths
_HERE = os.path.dirname(os.path.abspath(__file__))
_WORLD = os.path.dirname(_HERE)
_ROOT = os.path.dirname(_WORLD)
for _p in (_WORLD, os.path.join(_ROOT, "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import world_contract as C                                            # noqa: E402

ITEM = "forecourt_paving_bay"
PFX = "FCP_"                       # every object this module emits
LIBPFX = "FCPL_"                   # library source meshes (never linked to the scene)
COLL_NAME = "W_Item_ForecourtPavingBay"
LIB_COLL_NAME = "W_Item_ForecourtPavingBay_Library"
SEED = 24601

# ------------------------------------------------------------- the filmed spec
NEAREST_CAMERA_M = 1.7             # manifest, DERIVED from the camera corridor
LENS_AT_CLOSEST_MM = 35.0
SENSOR_MM = 36.0
RES_X_4K = 3840
RES_Y_4K = 2160
PX_PER_M = (RES_X_4K * LENS_AT_CLOSEST_MM / SENSOR_MM) / NEAREST_CAMERA_M   # 2196.1
MM_PER_PX = 1000.0 / PX_PER_M                                              # 0.4554
GATE_LIMIT_PX = 6.0                # hero limit on the 10th-percentile edge
DECLARED_INSTANCES = 1400

# =============================================================================
# 1.  THE LAYING PLAN -- every number is a real paving dimension
# =============================================================================
# Forecourt extents: build_architecture's, from the contract, in WORLD metres.
_FC = dict(C.FORECOURT_WORLD)
X0 = _FC["cx"] - _FC["hx"]          # -27.0
X1 = _FC["cx"] + _FC["hx"]          # +26.0
Y0 = _FC["cy"] - _FC["hy"]          # -22.0
Y1 = _FC["cy"] + _FC["hy"]          # +22.0

SETOUT_X = C.ACCESS_GLASS_X         # 15.000 -- the breach plane IS a course line
SETOUT_Y = 0.0                      # the building centreline
CELL_W = 1.500                      # course width, world x
CELL_H = 1.000                      # flag length, world y
JOINT_NOM_M = 0.012                 # nominal joint, and build_architecture's
JOINT_SD_M = 0.0016                 # laying tolerance on the joint width
JOINT_MIN_M = 0.007
JOINT_MAX_M = 0.024
FLAG_T_M = 0.075                    # 75 mm precast flag, a real catalogue depth
SOFFIT_M = -0.045                   # how far down the modelled skirt goes.  The
                                    # bedding covers everything below -0.030, so
                                    # 45 mm is 15 mm of margin, not 75 mm of
                                    # geometry nobody can see.

# LEVELS.  A flag bed is screeded to +-3 mm and the flags lip against each other.
FLAG_TOP_MAX_M = +0.0035            # HARD CEILING -- 4.0 mm under MARK_Z
FLAG_TOP_MIN_M = -0.0090
LEVEL_SD_M = 0.0016                 # bed level scatter, per flag
ROCK_MAX_M = 0.0021                 # a flag on a short bed sits proud on one corner
WARP_MAX_M = 0.0024                 # precast flags dish/hog across the diagonal
BASIN_DEPTH_M = 0.0055              # settlement basins, where water stands
LIP_TARGET_M = 0.0030               # the lip the frame is designed to show

# ARRIS.
CHAMFER_W_M = 0.0050                # cast arris chamfer, 5 mm at 45 deg
CHAMFER_SAWN_M = 0.0006             # a sawn edge is square: 0.6 mm arris break
CHIP_ZONE_M = 0.016                 # how far in from the edge chipping reaches
CHIP_PROB_FORMED = 0.16             # per 18 mm arris cell
CHIP_PROB_SAWN = 0.38               # a sawn edge is unarmoured and chips more
CORNER_SPALL_P = 0.13

# JOINT BED.
BED_MIN_M = -0.030                  # deepest a washed-out joint gets
BED_MAX_M = -0.005                  # a freshly re-sanded joint
BED_COARSE_M = -0.014               # the far-field bedding sheet's nominal top
GRAIN_MAX_M = 0.0031                # jointing grit relief

# TRENCH REINSTATEMENT.
OVERBAND_W_M = 0.055                # bitumen overband over the reinstatement joint
OVERBAND_H_M = 0.0030               # and how proud it stands
ASPH_TOP_M = -0.0035                # reinstatements are always laid low

# SOCKETS (the interface forecourt_bollard builds on).
SOCKET_R_M = 0.180
SOCKET_FLOOR_M = -0.045
COLLAR_TOP_M = -0.004
COLLAR_W_M = 0.055
BOLLARD_LINE_X = C.FORECOURT_BOLLARD_X                      # 19.5, from the contract
BOLLARD_SOCKETS = [(BOLLARD_LINE_X, y) for y in
                   (-12.6, -10.8, -9.0, 9.0, 10.8, 12.6)]

# FAMILIES.  A precast forecourt is specified as a palette, not one flag.
#   blast  shot-blasted grey, fine exposed aggregate      the field
#   hone   honed charcoal, aggregate cut dead flat        the banding courses
#   agg    washed exposed-aggregate, 4-9 mm stone         the accent courses
FAM_BLAST, FAM_HONE, FAM_AGG = 0, 1, 2
FAM_NAME = {FAM_BLAST: "blast", FAM_HONE: "hone", FAM_AGG: "agg"}

# THE BANDING PLAN.  Charcoal honed courses at a 7-course rhythm off the
# building line, with an exposed-aggregate course beside each -- so the frame
# has designed structure in it and not just noise.
BAND_PERIOD = 7
BAND_HONE_PHASE = 3
BAND_AGG_PHASE = 4

CUT_KEEP_MIN_M2 = 0.055             # a sliver smaller than this is not laid;
                                    # the paver fills it with mortar instead

# WHAT STOOD HERE.  The manifest's fourth variation axis is "stain", and the
# strongest stain on any forecourt is not a drip or a spill -- it is the GHOST
# of something that stood in one place for years.  Under it the concrete never
# weathered, so it is paler than everything around it; at its rim the dirt piled
# against the obstruction; and where its feet were, the steel rusted into the
# slab.  A clean disc with a dirty rim and four rust points is read instantly
# and correctly by anyone who has ever looked at a pavement.
#   (x, y, radius, feet, foot_radius)   WORLD metres
FURNITURE_MARKS = [
    (15.95, 13.15, 0.285, 4, 0.230),    # a planter, beside the north frontage
    (18.40, 8.60, 0.215, 3, 0.170),     # an A-frame sign by the road mouth
    (16.10, -9.35, 0.330, 4, 0.265),    # the twin planter on the south side
    (21.30, 12.10, 0.190, 0, 0.0),      # a bin that has been moved
    (-8.60, 14.20, 0.260, 4, 0.205),    # a cycle stand on the west apron
    (-19.20, -6.40, 0.300, 3, 0.240),   # a gas bottle cage behind the building
    (12.40, 16.80, 0.175, 0, 0.0),      # a cone that lived here one winter
]

# The keep-outs, in WORLD metres.  Both are rectangles over the forecourt.
R1_SHELL = (-15.250, 15.000, -11.250, 11.250)        # build_architecture's measured
R1_JOINT_M = 0.012                                   # construction joint at the shell
RIBBON_SAW_M = C.ACCESS_RIBBON_SAW_M                 # 0.30
RIBBON_HALF_W = 6.0                                  # MEASURED above, not assumed
RIBBON_KEEPOUT = (SETOUT_X, X1 + 1.0,
                  -(RIBBON_HALF_W + RIBBON_SAW_M), RIBBON_HALF_W + RIBBON_SAW_M)
# Whether to fill the contract's orphan 300 mm between the road surface at
# |y| = 6.000 and architecture's paving line at |y| = 6.300.  See the module
# header: build(ribbon_strip=False) turns it off and leaves the hole open.
RIBBON_STRIP = True

# ------------------------------------------------------- the macro shot's frame
# Declared here rather than with the test scene because build() needs them: the
# mesh pitch is chosen against the FRUSTUM, not against a radius.
VIEW_AZ_DEG = -26.0        # 32 deg off the sun's bearing: the light rakes ACROSS
CAM_PITCH_DEG = 58.0       # and the flag grid runs diagonally through the frame
TEST_CENTRE = (18.6, 9.4)  # east forecourt, outside the ribbon's sawn edge

# ------------------------------------------------------------------ LOD bands
EXPLICIT_R_M = 9.0                  # unique meshes inside this radius
FIELD_R_M = 34.0                    # instanced flags out to here
RIBBON_R_M = 3.4                    # fine joint ribbons inside this radius
RIBBON_R2_M = 8.0                   # coarse joint ribbons out to here
WEED_EXPLICIT_R_M = 4.2
LIB_PITCH_M = 0.009
VERT_BUDGET = 9_000_000


def lod_pitch(d):
    """Mesh pitch in metres for a flag whose centre is `d` from the lens.

    The near band is 0.85 mm = 1.87 px on the 4K master at 1.7 m, so the finest
    thing the mesh can express is about two pixels across.  That is the honest
    floor for this item: a 6 mm aggregate grain gets 7 samples, a 5 mm chamfer
    gets 6 (10 with the edge grading), a 2 mm chip gets 2.  Below it -- the
    0.25 mm blade score, the 0.15 mm matrix pitting -- is where the bump layer
    starts, and nothing above 1 px is left to a bump.
    """
    if d <= 2.6:
        return 0.00085
    if d <= 4.2:
        return 0.00170
    if d <= 7.0:
        return 0.00340
    return 0.00680


# =============================================================================
# 2.  DETERMINISTIC NOISE -- written here, shared with nothing
# =============================================================================
_U32 = np.uint32


def _mix(h):
    # the wraparound IS the hash; numpy's overflow warning is noise here
    with np.errstate(over="ignore"):
        h = np.asarray(h, _U32)
        h ^= h >> _U32(16)
        h = (h * _U32(0x7feb352d)).astype(_U32)
        h ^= h >> _U32(15)
        h = (h * _U32(0x846ca68b)).astype(_U32)
        h ^= h >> _U32(16)
    return h


def _ih_raw(*keys):
    with np.errstate(over="ignore"):
        h = _U32(0x9e3779b9)
        for k in keys:
            h = _mix(h ^ np.asarray(k, np.int64).astype(_U32) * _U32(0x85ebca6b))
    return h


def _ih(*keys):
    """Integer hash of any number of integer-ish keys -> uint32 array."""
    return _ih_raw(*keys)


def h01(*keys):
    """-> float in [0, 1).  Scalars in, scalar out; arrays in, array out."""
    v = _ih(*keys).astype(np.float64) * (1.0 / 4294967296.0)
    return float(v) if v.ndim == 0 else v


def _sstep(e0, e1, x):
    d = np.asarray(e1, np.float64) - np.asarray(e0, np.float64)
    d = np.where(np.abs(d) < 1e-12, 1e-12, d)
    t = np.clip((np.asarray(x, np.float64) - e0) / d, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def _smax(a, b, k):
    """Smooth maximum -- rounded transitions where two surfaces meet."""
    h = np.clip(0.5 + 0.5 * (a - b) / k, 0.0, 1.0)
    return a * h + b * (1.0 - h) + k * h * (1.0 - h)


def vn2(X, Y, seed, cell=1.0):
    """Value noise, C1, on a square lattice of side `cell`."""
    x = np.asarray(X, np.float64) / cell
    y = np.asarray(Y, np.float64) / cell
    ix = np.floor(x).astype(np.int64)
    iy = np.floor(y).astype(np.int64)
    fx = x - ix
    fy = y - iy
    ux = fx * fx * (3.0 - 2.0 * fx)
    uy = fy * fy * (3.0 - 2.0 * fy)
    a = h01(ix, iy, seed)
    b = h01(ix + 1, iy, seed)
    c = h01(ix, iy + 1, seed)
    d = h01(ix + 1, iy + 1, seed)
    return (a * (1 - ux) * (1 - uy) + b * ux * (1 - uy)
            + c * (1 - ux) * uy + d * ux * uy)


def fbm2(X, Y, seed, cell=1.0, oct=4, lac=2.07, gain=0.5):
    tot = np.zeros(np.shape(X), np.float64)
    amp = 1.0
    nrm = 0.0
    cl = float(cell)
    for o in range(oct):
        tot += amp * vn2(X, Y, seed + 977 * o, cl)
        nrm += amp
        amp *= gain
        cl /= lac
    return tot / max(nrm, 1e-9)


def worley(X, Y, seed, cell=0.006, jitter=0.85):
    """F1 distance and the winning cell's hash.

    -> (f1, cid, dx, dy) where f1 is in metres, cid in [0,1) identifies the
    cell (this is what carries an aggregate grain's identity into the shader),
    and dx, dy point from the sample to the winning site.
    """
    x = np.asarray(X, np.float64) / cell
    y = np.asarray(Y, np.float64) / cell
    ix = np.floor(x).astype(np.int64)
    iy = np.floor(y).astype(np.int64)
    best = np.full(np.shape(x), 1e9)
    cid = np.zeros(np.shape(x))
    bdx = np.zeros(np.shape(x))
    bdy = np.zeros(np.shape(x))
    for oy in (-1, 0, 1):
        for ox in (-1, 0, 1):
            gx = ix + ox
            gy = iy + oy
            hx = h01(gx, gy, seed, 1)
            hy = h01(gx, gy, seed, 2)
            px = gx + 0.5 + (hx - 0.5) * jitter
            py = gy + 0.5 + (hy - 0.5) * jitter
            dx = px - x
            dy = py - y
            d = dx * dx + dy * dy
            m = d < best
            best = np.where(m, d, best)
            cid = np.where(m, h01(gx, gy, seed, 3), cid)
            bdx = np.where(m, dx, bdx)
            bdy = np.where(m, dy, bdy)
    return np.sqrt(best) * cell, cid, bdx * cell, bdy * cell


def _graded_axis(a0, a1, pitch, edge_zone, edge_pitch):
    """Samples from a0 to a1, fine within `edge_zone` of either end.

    The chamfer, the chips and the sawn arris all live in the outer 16 mm of a
    flag, and sampling them at the interior pitch would round a 5 mm chamfer
    off into a 5 mm fillet.  Grading costs 40 extra samples per axis.
    """
    L = float(a1 - a0)
    if L <= edge_pitch * 3:
        return np.array([a0, a1], np.float64)
    n = max(64, int(L / max(edge_pitch, 1e-5)) + 1)
    t = np.linspace(0.0, L, n)
    e = np.minimum(t, L - t)
    p = edge_pitch + (pitch - edge_pitch) * _sstep(0.0, edge_zone, e)
    inv = 1.0 / p
    s = np.concatenate([[0.0], np.cumsum(0.5 * (inv[1:] + inv[:-1]) * np.diff(t))])
    m = max(2, int(round(s[-1])))
    xs = np.interp(np.linspace(0.0, s[-1], m + 1), s, t)
    xs[0] = 0.0
    xs[-1] = L
    return a0 + xs


# =============================================================================
# 3.  THE FLAG, THE PLAN, AND THE CUTS
# =============================================================================
class Flag(object):
    """One laid unit.  Everything about it is decided here, once, from `seed`."""
    __slots__ = ("idx", "i", "j", "x0", "x1", "y0", "y1", "w", "h",
                 "cx", "cy", "sawn", "fam", "level", "tx", "ty", "warp",
                 "rock", "rockc", "seed", "chip", "chipsz", "crack", "crackp",
                 "agg_cell", "agg_h", "erode", "expose", "age", "kind",
                 "agg2_cell", "agg2_h", "expose2", "tone", "shed",
                 "wear", "damp", "alg", "eff", "rust", "oil", "rub", "soil",
                 "n_verts", "mesh_name", "src", "bucket", "cut", "trench", "cutm",
                 "repl")

    def __init__(self, **kw):
        for k in self.__slots__:
            setattr(self, k, kw.get(k, 0))

    @property
    def area(self):
        return self.w * self.h

    def __repr__(self):
        return ("<Flag %d (%d,%d) %.3fx%.3f %s%s>"
                % (self.idx, self.i, self.j, self.w, self.h,
                   FAM_NAME.get(self.fam, "?"),
                   " cut" if self.cut else ""))


# --- reservations and trenches, both registered BEFORE build() --------------
_RESERVE = []          # list of dicts: circle or rect keep-outs inside the paving
_TRENCH = []           # list of trench dicts, in CELL coordinates


def reserve_circle(x, y, r=SOCKET_R_M, kind="socket", floor=SOCKET_FLOOR_M):
    """Core a socket through the paving at world (x, y).  -> the record."""
    rec = dict(shape="circle", x=float(x), y=float(y), r=float(r),
               kind=str(kind), floor=float(floor))
    _RESERVE.append(rec)
    return rec


def reserve_rect(x0, x1, y0, y1, kind="chamber", floor=SOCKET_FLOOR_M):
    rec = dict(shape="rect", x0=float(x0), x1=float(x1), y0=float(y0),
               y1=float(y1), kind=str(kind), floor=float(floor))
    _RESERVE.append(rec)
    return rec


def clear_reservations():
    del _RESERVE[:]


def default_reservations(replace=False):
    """The 6 bollard sockets at the contract's FORECOURT_BOLLARD_X."""
    if replace:
        clear_reservations()
    if not any(r.get("kind") == "socket" for r in _RESERVE):
        for (x, y) in BOLLARD_SOCKETS:
            reserve_circle(x, y, SOCKET_R_M, "socket")
    return [r for r in _RESERVE if r["kind"] == "socket"]


# THE TRENCH REINSTATEMENTS.  2.4 % of the field, per the manifest.  Four real
# jobs, each a staircase along the joint grid because that is what happens when
# a gang lifts flags to get at a duct: they lift WHOLE flags and cut only where
# the excavation runs past one.  `i` counts courses east from the glass plane,
# `j` counts flags north from the building centreline.
TRENCHES = [
    # a power/comms duct run from the road mouth up the north flank of the glass
    dict(name="duct_north", cells=[(1, j) for j in range(7, 14)]
                                  + [(2, 13), (3, 13), (4, 13)],
         age=0.18, sunk=0.0035),
    # the same job's spur, one course further out, cut short at a chamber
    dict(name="duct_spur", cells=[(2, 7), (2, 8), (3, 8)],
         age=0.30, sunk=0.0022),
    # and the chamber it was cut short at
    dict(name="chamber_ne", cells=[(4, 12), (5, 12)], age=0.45, sunk=0.0031),
    # a water repair on the west forecourt: a square dig around a valve
    # RELOCATED, and the placement gate is why.  At (-11,-3) this dig sat at
    # world x -1.5..1.5, y -3..-1 -- which is INSIDE the pavilion (R1_SHELL),
    # i.e. an asphalt trench across the showroom floor, and 0.595 m inside the
    # car's driven path.  It is now in the west forecourt strip beyond the back
    # wall, where a water main actually runs.  `_cell_is_paved` below stops the
    # same mistake being made again by hand.
    dict(name="valve_west", cells=[(-24, -3), (-24, -2), (-23, -3), (-23, -2)],
         age=0.62, sunk=0.0048),
    # an older gas main crossing the north apron -- weathered grey, not black
    dict(name="gas_north", cells=[(i, 14) for i in range(-13, -3)],
         age=0.88, sunk=0.0060),
]


def _cell_is_paved(i, j):
    """True where this module actually lays something.

    A trench is dug through PAVING.  A trench declared over the pavilion floor
    or the access road is not a reinstatement, it is an asphalt patch on
    somebody else's surface -- which is exactly what the placement gate found,
    0.595 m inside the car's driven path.  Every trench cell is now tested
    against the same clip the flags use.
    """
    for (p, _m) in _clip_cell(cell_bounds(i, j)):
        if (p[1] - p[0]) * (p[3] - p[2]) >= CUT_KEEP_MIN_M2:
            return True
    return False


def _trench_cells():
    out = {}
    for t in TRENCHES:
        keep = []
        for c in t["cells"]:
            if _cell_is_paved(int(c[0]), int(c[1])):
                keep.append(tuple(c))
                out[tuple(c)] = t
            else:
                print(">> trench %s: cell %s is not paved (pavilion, ribbon or "
                      "outside the forecourt) -- NOT dug" % (t["name"], tuple(c)))
        t["_paved_cells"] = keep
    return out


# --- the cell grid ----------------------------------------------------------
def cell_bounds(i, j):
    """World rectangle of course i, flag j (the CELL, joints included)."""
    return (SETOUT_X + i * CELL_W, SETOUT_X + (i + 1) * CELL_W,
            SETOUT_Y + j * CELL_H, SETOUT_Y + (j + 1) * CELL_H)


def cell_index(x, y):
    return (int(math.floor((x - SETOUT_X) / CELL_W)),
            int(math.floor((y - SETOUT_Y) / CELL_H)))


def _keepouts():
    """Every rectangle the paving is cut around, WORLD metres."""
    sx0, sx1, sy0, sy1 = R1_SHELL
    # three sides carry the 12 mm construction joint; the +x face is the breach
    # plane and the contract pins every consumer to 15.000 with no allowance.
    shell = (sx0 - R1_JOINT_M, sx1, sy0 - R1_JOINT_M, sy1 + R1_JOINT_M)
    return [("shell", shell), ("ribbon", RIBBON_KEEPOUT)]


def _sub_rects(rect, ko):
    """`rect` minus axis-aligned rectangle `ko` -> list of clear rectangles.

    A guillotine split, which is exactly how a paver cuts a flag around an
    obstruction: never an L, always straight cuts, and the offcut that is too
    small to bed is not laid.
    """
    x0, x1, y0, y1 = rect
    kx0, kx1, ky0, ky1 = ko
    if kx1 <= x0 or kx0 >= x1 or ky1 <= y0 or ky0 >= y1:
        return [rect]
    out = []
    if kx0 > x0:
        out.append((x0, kx0, y0, y1))
    if kx1 < x1:
        out.append((kx1, x1, y0, y1))
    mx0, mx1 = max(x0, kx0), min(x1, kx1)
    if mx1 > mx0:
        if ky0 > y0:
            out.append((mx0, mx1, y0, ky0))
        if ky1 < y1:
            out.append((mx0, mx1, ky1, y1))
    return out


def _clip_cell(rect):
    """-> [(rect, sawn_mask), ...].  sawn_mask bits: 1 -x, 2 +x, 4 -y, 8 +y."""
    pieces = [rect]
    for _n, ko in _keepouts():
        nxt = []
        for p in pieces:
            nxt.extend(_sub_rects(p, ko))
        pieces = nxt
    # the forecourt boundary itself
    nxt = []
    for (x0, x1, y0, y1) in pieces:
        cx0, cx1 = max(x0, X0), min(x1, X1)
        cy0, cy1 = max(y0, Y0), min(y1, Y1)
        if cx1 - cx0 > 1e-6 and cy1 - cy0 > 1e-6:
            nxt.append((cx0, cx1, cy0, cy1))
    out = []
    for p in nxt:
        if (p[1] - p[0]) * (p[3] - p[2]) < CUT_KEEP_MIN_M2:
            continue
        m = 0
        if p[0] > rect[0] + 1e-6:
            m |= 1
        if p[1] < rect[1] - 1e-6:
            m |= 2
        if p[2] > rect[2] + 1e-6:
            m |= 4
        if p[3] < rect[3] - 1e-6:
            m |= 8
        out.append((p, m))
    return out


# --- the large-scale fields the whole forecourt shares ----------------------
def wear_field(X, Y, seed=SEED):
    """Pedestrian polish.  Highest at the showroom frontage, decaying outward.

    A forecourt is not a road: the wear pattern is FEET, and feet come out of
    the doors and fan.  Plus one service-vehicle track across the north apron
    where the delivery truck backs in, which is a different, harder polish.
    """
    X = np.asarray(X, np.float64)
    Y = np.asarray(Y, np.float64)
    d_door = np.sqrt((X - 15.0) ** 2 + (Y - 0.0) ** 2)
    ped = np.exp(-np.maximum(d_door - 4.0, 0.0) / 9.0)
    # the fan is not symmetric: the entrance sits north of centre
    ped *= 0.55 + 0.45 * _sstep(-7.0, 6.0, Y)
    # a service track, an arc across the north apron to the loading door
    tx = -6.0 + 9.0 * np.cos((Y - 15.0) / 7.0)
    trk = np.exp(-((X - tx) / 1.35) ** 2) * _sstep(9.0, 12.0, Y)
    lane = np.exp(-((np.abs(Y) - 7.4) / 1.5) ** 2) * _sstep(15.0, 17.0, X)
    w = np.clip(ped * 0.85 + trk * 0.75 + lane * 0.55, 0.0, 1.0)
    return np.clip(w * (0.72 + 0.55 * fbm2(X, Y, seed + 41, 2.6, 4)), 0.0, 1.0)


def basin_field(X, Y, seed=SEED):
    """Settlement basins: where the sub-base consolidated and water stands.

    -> 0..1.  These are the only large-scale departure from the datum plane in
    this module, they are bounded by BASIN_DEPTH_M, and they are what makes the
    damp, the algae and the efflorescence sit somewhere instead of everywhere.
    """
    X = np.asarray(X, np.float64)
    Y = np.asarray(Y, np.float64)
    b = fbm2(X + 311.0, Y - 97.0, seed + 613, 7.5, 3)
    b = _sstep(0.58, 0.90, b)
    # a real one over the backfilled duct run, which always settles
    b = np.maximum(b, 0.85 * np.exp(-((X - 17.2) / 1.1) ** 2)
                   * _sstep(6.0, 8.0, Y) * _sstep(15.0, 13.5, Y))
    return np.clip(b, 0.0, 1.0)


def damp_field(X, Y, seed=SEED):
    """Where the surface stays wet: basins, the north shade line, the drip line
    under the facade, and the lee of the wall the sun never reaches."""
    X = np.asarray(X, np.float64)
    Y = np.asarray(Y, np.float64)
    d = basin_field(X, Y, seed) * 0.9
    # the pavilion's own shadow at a 12.47 deg sun bearing -58 deg lies to the
    # north-west of the shell: this is where biofilm survives the afternoon
    shade = _sstep(11.0, 13.6, Y) * _sstep(16.4, 14.0, X)
    d = np.maximum(d, 0.62 * shade)
    # the facade drip line, 0.35 m off the glass -- and it stops where the
    # BUILDING stops (R1_SHELL |y| <= 11.25), because rain only sheds off a wall
    # that is there.  Running it the full 22 m put a damp stripe down the open
    # forecourt where there is nothing overhead to shed it.
    d = np.maximum(d, 0.70 * np.exp(-((X - 15.35) / 0.26) ** 2)
                   * _sstep(6.2, 6.9, np.abs(Y))
                   * _sstep(11.75, 11.15, np.abs(Y)))
    return np.clip(d * (0.62 + 0.60 * fbm2(X, Y, seed + 77, 1.7, 4)), 0.0, 1.0)


def _flag_kind(i, j, seed):
    """Which precast family this course belongs to -- the banding plan."""
    ph = (i - BAND_HONE_PHASE) % BAND_PERIOD
    if ph == 0:
        return FAM_HONE
    if ph == (BAND_AGG_PHASE - BAND_HONE_PHASE) % BAND_PERIOD:
        return FAM_AGG
    # 3 % of the field is a REPLACEMENT flag from a later batch: right size,
    # wrong shade, sharper arris, and always beside something that broke.
    return FAM_BLAST


def flag_layout(rect=None, seed=SEED):
    """The whole laying plan, deterministically.  -> [Flag, ...]"""
    rect = rect or (X0, X1, Y0, Y1)
    rx0, rx1, ry0, ry1 = rect
    i0 = int(math.floor((rx0 - SETOUT_X) / CELL_W))
    i1 = int(math.ceil((rx1 - SETOUT_X) / CELL_W))
    j0 = int(math.floor((ry0 - SETOUT_Y) / CELL_H))
    j1 = int(math.ceil((ry1 - SETOUT_Y) / CELL_H))
    tc = _trench_cells()
    flags = []
    n = 0
    for i in range(i0, i1):
        for j in range(j0, j1):
            cell = cell_bounds(i, j)
            if cell[1] <= rx0 or cell[0] >= rx1 or cell[3] <= ry0 or cell[2] >= ry1:
                continue
            trench = tc.get((i, j))
            for (p, cutmask) in _clip_cell(cell):
                jw = _joint_w(i, j, seed)
                # the flag is the clear rectangle less the joint on every side
                # that has a neighbour; a cut side butts the obstruction with a
                # 3 mm sawn gap instead of a bedded joint
                x0 = p[0] + (0.003 if (cutmask & 1) else jw[0] * 0.5)
                x1 = p[1] - (0.003 if (cutmask & 2) else jw[1] * 0.5)
                y0 = p[2] + (0.003 if (cutmask & 4) else jw[2] * 0.5)
                y1 = p[3] - (0.003 if (cutmask & 8) else jw[3] * 0.5)
                w, h = x1 - x0, y1 - y0
                if w < 0.06 or h < 0.06 or w * h < CUT_KEEP_MIN_M2:
                    continue
                fs = int(h01(i, j, len(flags), seed, 7) * 2e9)
                f = Flag(idx=n, i=i, j=j, x0=x0, x1=x1, y0=y0, y1=y1,
                         w=w, h=h, cx=0.5 * (x0 + x1), cy=0.5 * (y0 + y1),
                         sawn=cutmask, cutm=cutmask, seed=fs,
                         cut=bool(cutmask),
                         trench=trench["name"] if trench else "")
                _decide_flag(f, seed)
                flags.append(f)
                n += 1
    _level_flags(flags, seed)
    return flags


def _joint_w(i, j, seed):
    """The four joint widths around cell (i, j).  Shared by both neighbours:
    the width on the -x side of cell i IS the width on the +x side of cell
    i-1, computed from the JOINT's identity, not the flag's."""
    def jw(kind, a, b):
        g = h01(kind, a, b, seed, 55)
        v = JOINT_NOM_M + (g - 0.5) * 2.0 * JOINT_SD_M * 1.9
        return float(np.clip(v, JOINT_MIN_M, JOINT_MAX_M))
    return (jw(0, i, j), jw(0, i + 1, j), jw(1, i, j), jw(1, i, j + 1))


def _decide_flag(f, seed):
    """Every per-flag scalar.  This is the variation, and it is all geometric
    except the last six, which are the stains."""
    s = f.seed
    r = lambda k: h01(s, k)                                          # noqa: E731
    f.fam = _flag_kind(f.i, f.j, seed)
    # a replacement flag: right size, later batch
    if r(3) < 0.030:
        f.fam = FAM_BLAST
        f.age = 0.08 + 0.14 * r(5)
    else:
        f.age = 0.30 + 0.70 * r(7)
    f.kind = FAM_NAME[f.fam]
    if f.fam == FAM_AGG:
        f.agg_cell = 0.0042 + 0.0034 * r(11)          # 4.2 .. 7.6 mm stone
        f.agg_h = 0.00110 + 0.00095 * r(13)           # 1.10 .. 2.05 mm proud
        f.erode = 0.00055 + 0.00045 * r(17)
        f.expose = 0.52 + 0.26 * r(19)
    elif f.fam == FAM_HONE:
        f.agg_cell = 0.0030 + 0.0022 * r(11)
        f.agg_h = 0.00012 + 0.00016 * r(13)           # cut dead flat
        f.erode = 0.00008 + 0.00010 * r(17)
        f.expose = 0.80 + 0.18 * r(19)                # every stone is cut open
    else:
        # MEASURED AGAINST THE FIRST MACRO: at 0.42-0.76 mm of relief a
        # shot-blasted flag rendered as flat grey at 0.46 mm/px, while the
        # exposed-aggregate flag beside it read perfectly.  A real blasted
        # finish loses 0.6-1.2 mm of matrix and stands the fine aggregate proud
        # of it; the shadow that throws at a 12.5 deg sun is 3-5 mm, or 7-11 px.
        f.agg_cell = 0.0024 + 0.0022 * r(11)          # 2.4 .. 4.6 mm
        f.agg_h = 0.00058 + 0.00042 * r(13)           # 0.58 .. 1.00 mm
        f.erode = 0.00042 + 0.00034 * r(17)
        f.expose = 0.42 + 0.26 * r(19)
    # THE COARSE FRACTION.  A concrete paving flag is not made of one grain
    # size: it is a GRADED mix, and the blast or the wash exposes the odd 10-18
    # mm stone standing well proud of the fine matrix.  Without it the surface
    # renders as a perfectly even sandpaper over 1.5 m -- which is what the
    # second macro showed, and it is the difference between concrete and a
    # texture.  At 0.4554 mm/px a 14 mm stone is 31 px across and throws 63 mm
    # = 138 px of shadow at the contract sun.
    f.agg2_cell = 0.0095 + 0.0090 * r(81)          # 9.5 .. 18.5 mm spacing
    f.agg2_h = (0.0022 if f.fam == FAM_AGG else 0.0011) * (0.6 + 0.8 * r(83))
    f.expose2 = (0.34 if f.fam == FAM_AGG else 0.17) * (0.5 + 1.1 * r(85))
    if f.fam == FAM_HONE:
        f.agg2_h = 0.00016 * (0.6 + 0.8 * r(83))   # cut flat with the rest
        f.expose2 = 0.55
    # the flag's own shade: precast comes off a pallet, and two pallets poured a
    # fortnight apart are never the same grey
    f.tone = 0.86 + 0.30 * r(87)
    # and which way the rain runs off it, which is where the dirt stays
    f.shed = r(89) * 2.0 * math.pi
    f.warp = (r(23) - 0.42) * 2.0 * WARP_MAX_M
    f.tx = (r(29) - 0.5) * 2.0 * 0.0011 / max(f.w, 0.4)
    f.ty = (r(31) - 0.5) * 2.0 * 0.0011 / max(f.h, 0.4)
    f.rock = ROCK_MAX_M * max(0.0, r(37) * 1.55 - 0.62)
    f.rockc = int(r(41) * 4.0) & 3
    f.chip = (CHIP_PROB_SAWN if f.sawn else CHIP_PROB_FORMED) * (0.55 + 0.95 * r(43))
    f.chipsz = 0.0032 + 0.0075 * r(47)
    f.crack = (r(53) < (0.055 + 0.10 * (1.0 if f.sawn else 0.0)))
    f.crackp = r(59)
    # A REPLACEMENT.  5.5 % of a forecourt this age has been lifted and re-laid
    # -- a delivery lorry cracked a flag, the replacement was cut from a slab in
    # the yard, and it went back in with one or two SAWN edges, a sharper arris
    # and a shade the rest of the field lost fifteen years ago.  This is the
    # second source of the manifest's first variation axis, and unlike the field
    # boundary it puts sawn joints in the MIDDLE of the paving where the lens is.
    f.repl = (not f.cut) and (r(67) < 0.055)
    if f.repl:
        bits = (1, 2, 4, 8)
        for t in range(1 + int(r(69) * 2.0)):
            f.sawn |= bits[int(r(73 + t) * 4.0) & 3]
        f.age = 0.04 + 0.22 * r(77)
        f.crack = False
    return f


def _level_flags(flags, seed):
    """Bed levels, with the lip between neighbours held to a laying tolerance.

    A flag field is not random z per flag: the bed is screeded, so neighbours
    are correlated, and what the eye reads is the LIP at the joint.  A smooth
    bed field carries the correlation; a per-flag scatter carries the tolerance;
    and the result is clamped so nothing ever breaks FLAG_TOP_MAX_M.
    """
    if not flags:
        return
    cx = np.array([f.cx for f in flags])
    cy = np.array([f.cy for f in flags])
    bed = (fbm2(cx, cy, seed + 101, 6.5, 4) - 0.5) * 0.0034
    bas = basin_field(cx, cy, seed)
    scat = np.array([(h01(f.seed, 71) - 0.5) for f in flags]) * 2.0 * LEVEL_SD_M
    lev = bed + scat - bas * BASIN_DEPTH_M
    # a reinstatement is not a flag: its level is the asphalt's, always low
    tby = {t["name"]: t for t in TRENCHES}
    for k, f in enumerate(flags):
        if f.trench:
            lev[k] = ASPH_TOP_M - 0.5 * tby[f.trench]["sunk"]
    # THE CEILING IS MEASURED, NOT ESTIMATED.  The first version clamped against
    # warp + rock and missed the tilt term, and the field came out 1.07 mm over
    # FLAG_TOP_MAX_M -- which would have put a flag corner 1.07 mm inside
    # build_architecture's thermoplastic.  So evaluate the real surface at the
    # four corners and the centre of every flag and clamp on what it says.
    for k, f in enumerate(flags):
        f.level = float(lev[k])
    for _pass in range(2):
        for f in flags:
            zs = [_flag_plane_z(f, f.cx + ux * f.w * 0.5, f.cy + uy * f.h * 0.5)
                  for (ux, uy) in ((-1, -1), (1, -1), (1, 1), (-1, 1), (0, 0))]
            hi_, lo_ = max(zs), min(zs)
            if hi_ > FLAG_TOP_MAX_M:
                f.level -= (hi_ - FLAG_TOP_MAX_M)
            elif lo_ < FLAG_TOP_MIN_M:
                f.level += (FLAG_TOP_MIN_M - lo_)
    return flags


# =============================================================================
# 4.  THE JOINT MODEL  -- what the dependants place into
# =============================================================================
class Joint(object):
    __slots__ = ("idx", "p0", "p1", "axis", "kind", "width_m", "arris_z0",
                 "arris_z1", "bed_z", "wash", "weeded", "species", "overband",
                 "left", "right", "seed", "moss")

    def __init__(self, **kw):
        for k in self.__slots__:
            setattr(self, k, kw.get(k, 0))

    @property
    def length(self):
        return math.hypot(self.p1[0] - self.p0[0], self.p1[1] - self.p0[1])

    def __repr__(self):
        return ("<Joint %d %s %s %.0fmm %.2fm%s>"
                % (self.idx, self.axis, self.kind, self.width_m * 1000,
                   self.length, " WEED" if self.weeded else ""))


def joint_bed_z(j, t):
    """Jointing-bed level at parameter t in [0, 1] along joint `j`.

    THE NUMBER A SEED GERMINATES ON and a 3 mm glass chip comes to rest on.
    The bed is not flat: rain scours it at the low end, a boot presses it at
    the high end, and re-sanding after a repair leaves one metre in ten full.
    """
    t = np.clip(np.asarray(t, np.float64), 0.0, 1.0)
    L = max(j.length, 1e-6)
    # arris_z0/z1 are the LEFT and RIGHT flag tops, not two ends of one edge:
    # the bed is referenced to their mean and the difference between them is the
    # LIP, which is what the eye actually reads at a 12.5 deg sun.
    arr = 0.5 * (j.arris_z0 + j.arris_z1)
    w = j.wash * (0.55 + 0.45 * vn2(t * L, np.full_like(t, float(j.idx)),
                                    j.seed + 5, 0.42))
    w = w + 0.22 * j.wash * vn2(t * L, np.full_like(t, float(j.idx)),
                                j.seed + 9, 0.11)
    z = arr - np.clip(w, 0.004, 0.030)
    return z if z.ndim else float(z)


def joint_segments(flags, seed=SEED):
    """Every joint in the field.  Two flags that share a cell boundary make one.

    The joint's identity is the CELL BOUNDARY, not either flag, so both
    neighbours agree about its width, its kind and its bed without either of
    them having to know the other exists.
    """
    by_cell = {}
    for f in flags:
        by_cell.setdefault((f.i, f.j), []).append(f)
    tc = _trench_cells()
    joints = []
    n = 0
    for (i, j), fs in sorted(by_cell.items()):
        for axis, di, dj in (("y", 1, 0), ("x", 0, 1)):
            nb = by_cell.get((i + di, j + dj))
            if not nb:
                continue
            a = max(fs, key=lambda f: f.area)
            b = max(nb, key=lambda f: f.area)
            if axis == "y":
                jx = SETOUT_X + (i + 1) * CELL_W
                ov0 = max(a.y0, b.y0)
                ov1 = min(a.y1, b.y1)
                if ov1 - ov0 < 0.05:
                    continue
                p0, p1 = (jx, ov0), (jx, ov1)
                gap = b.x0 - a.x1
                if not (JOINT_MIN_M * 0.5 <= gap <= 0.034):
                    continue          # not a joint: a cut has opened the field
                sawn = bool(a.sawn & 2) or bool(b.sawn & 1)
            else:
                jy = SETOUT_Y + (j + 1) * CELL_H
                ov0 = max(a.x0, b.x0)
                ov1 = min(a.x1, b.x1)
                if ov1 - ov0 < 0.05:
                    continue
                p0, p1 = (ov0, jy), (ov1, jy)
                gap = b.y0 - a.y1
                if not (JOINT_MIN_M * 0.5 <= gap <= 0.034):
                    continue
                sawn = bool(a.sawn & 8) or bool(b.sawn & 4)
            ta, tb = tc.get((i, j)), tc.get((i + di, j + dj))
            if ta is not None and tb is not None:
                continue            # inside the reinstatement there is no joint
            if (ta is None) != (tb is None):
                sawn = True                      # the trench edge was cut
            js = int(h01(i, j, 13 if axis == "y" else 29, seed, 3) * 2e9)
            r = lambda k: h01(js, k)                                  # noqa: E731
            # 18 % colonised, but not uniformly: a joint colonises where it is
            # damp, out of the traffic, and wide.  That is why the weeds cluster
            # along the shade line instead of dotting the field like confetti.
            mx, my = 0.5 * (p0[0] + p1[0]), 0.5 * (p0[1] + p1[1])
            dmp = float(damp_field(np.array([mx]), np.array([my]), seed)[0])
            wr = float(wear_field(np.array([mx]), np.array([my]), seed)[0])
            # A BROOM DOES NOT REACH BEHIND A PLANTER.  Wherever a piece of
            # forecourt furniture has stood, the 300 mm of joint in its lee is
            # never swept and never walked on, and that is where the colonists
            # are in every real forecourt.  It is also 7 places in this field
            # where a plant, a stain and a joint are guaranteed to be in the
            # same square metre -- which is what a macro has to show.
            lee = 0.0
            for (gx, gy, gr, _nf, _fr) in FURNITURE_MARKS:
                if math.hypot(mx - gx, my - gy) < gr + 0.42:
                    lee = 1.0
                    break
            p_weed = np.clip(0.048 + 0.63 * dmp + 0.40 * _sstep(0.012, 0.020, gap)
                             - 0.40 * wr + 0.42 * lee, 0.0, 0.94)
            weeded = (r(11) < p_weed) and not (ta or tb)
            joints.append(Joint(
                idx=n, p0=p0, p1=p1, axis=axis,
                kind="sawn" if sawn else "formed",
                width_m=float(max(gap, 0.004)),
                arris_z0=float(a.level + a.warp * 0.4),
                arris_z1=float(b.level + b.warp * 0.4),
                wash=float(0.006 + 0.021 * r(13) ** 1.5 + 0.006 * dmp),
                weeded=bool(weeded),
                species=int(r(17) * 4) & 3,
                moss=bool(r(19) < (0.10 + 0.55 * dmp)),
                overband=bool((ta is None) != (tb is None)),
                left=a.idx, right=b.idx, seed=js))
            n += 1
    joints.extend(_edge_joints(flags, n, seed))
    return joints


def _edge_joints(flags, n0, seed=SEED):
    """The joints where the paving meets something that is not paving.

    TWO OF THEM MATTER AND ONE OF THEM IS A HOLE IN THE CONTRACT.

    * THE RIBBON.  `apron_platform_mask` subtracts the access ribbon plus
      C.ACCESS_RIBBON_SAW_M = 0.300, so architecture's paving stops at
      |y| = 6.300; `in_access_ribbon` at margin 0 says the road's own surface
      ends at |y| = 6.000.  MEASURED: 6.000 and 6.300 exactly, over the whole
      forecourt.  That leaves a 300 mm strip which `world_ground_z` hands to
      OWNER_APRON and which nothing actually builds -- an open trench 11 m long
      on both sides of the road the car drives out on, 1.7 m from the lens.
      This module fills it, as what it physically is: the SAWN EDGE STRIP where
      a flag field is cut to an asphalt road, grit-filled, bitumen-sealed at the
      flag arris, and everywhere BELOW the datum (-4 to -16 mm).  It stops
      12 mm clear of the road surface, so it cannot overlap SURF_AccessRoad.
      Pass ribbon_strip=False to build() to leave the contract's hole open.

    * THE BUILDING.  A 12 mm construction joint at the pavilion shell, sealed,
      swept, and never colonised -- which is why the weeds in this forecourt
      stop dead at the facade instead of ringing it.
    """
    out = []
    n = n0
    sx0, sx1, sy0, sy1 = R1_SHELL
    for f in flags:
        if f.trench or not f.cutm:
            continue
        for bit, axis, (ex, ey), (tx_, ty_) in (
                (1, "x", (f.x0, f.cy), (-1, 0)), (2, "x", (f.x1, f.cy), (1, 0)),
                (4, "y", (f.cx, f.y0), (0, -1)), (8, "y", (f.cx, f.y1), (0, 1))):
            if not (f.cutm & bit):
                continue
            probe = (ex + tx_ * 0.02, ey + ty_ * 0.02)
            kind = None
            if (RIBBON_KEEPOUT[0] <= probe[0] <= RIBBON_KEEPOUT[1]
                    and RIBBON_KEEPOUT[2] <= probe[1] <= RIBBON_KEEPOUT[3]):
                kind = "ribbon"
            elif (sx0 - R1_JOINT_M <= probe[0] <= sx1
                  and sy0 - R1_JOINT_M <= probe[1] <= sy1 + R1_JOINT_M):
                kind = "shell"
            if kind is None:
                continue
            if kind == "ribbon":
                if not RIBBON_STRIP:
                    continue
                outer = math.copysign(RIBBON_HALF_W + 0.012, ey if ty_ else ex)
                if axis == "y":
                    w = abs(f.y1 if ty_ > 0 else f.y0) - abs(outer)
                    c = 0.5 * ((f.y1 if ty_ > 0 else f.y0) + outer)
                    p0, p1 = (f.x0, c), (f.x1, c)
                    a0 = _flag_plane_z(f, f.x0, f.y1 if ty_ > 0 else f.y0)
                    a1 = _flag_plane_z(f, f.x1, f.y1 if ty_ > 0 else f.y0)
                else:
                    continue
                w = abs(w)
                if not (0.05 < w < 0.45):
                    continue
                over = True
            else:
                w = R1_JOINT_M
                if axis == "y":
                    c = (f.y1 + w * 0.5) if ty_ > 0 else (f.y0 - w * 0.5)
                    p0, p1 = (f.x0, c), (f.x1, c)
                    a0 = _flag_plane_z(f, f.x0, f.y1 if ty_ > 0 else f.y0)
                    a1 = _flag_plane_z(f, f.x1, f.y1 if ty_ > 0 else f.y0)
                else:
                    c = (f.x1 + w * 0.5) if tx_ > 0 else (f.x0 - w * 0.5)
                    p0, p1 = (c, f.y0), (c, f.y1)
                    a0 = _flag_plane_z(f, f.x1 if tx_ > 0 else f.x0, f.y0)
                    a1 = _flag_plane_z(f, f.x1 if tx_ > 0 else f.x0, f.y1)
                over = False
            js = int(h01(f.idx, bit, seed, 131) * 2e9)
            dmp = float(damp_field(np.array([0.5 * (p0[0] + p1[0])]),
                                   np.array([0.5 * (p0[1] + p1[1])]), seed)[0])
            out.append(Joint(
                idx=n, p0=p0, p1=p1, axis=axis, kind="sawn", width_m=float(w),
                arris_z0=float(a0), arris_z1=float(a1),
                wash=float(0.005 + 0.012 * h01(js, 3) + 0.006 * dmp),
                weeded=bool(kind == "ribbon" and h01(js, 5) < 0.42),
                species=int(h01(js, 7) * 4) & 3,
                moss=bool(kind == "ribbon" and h01(js, 9) < 0.5),
                overband=over, left=f.idx, right=-1, seed=js))
            n += 1
    return out


# =============================================================================
# 5.  THE SURFACE QUERY  -- surface_z / flag_top_z / on_flag
# =============================================================================
_IDX = {"flags": None, "grid": None, "seed": None}


def _index(flags, seed=SEED):
    g = {}
    for f in flags:
        g.setdefault((f.i, f.j), []).append(f)
    _IDX["flags"] = flags
    _IDX["grid"] = g
    _IDX["seed"] = seed
    return g


def _ensure_index(seed=SEED):
    if _IDX["grid"] is None or _IDX["seed"] != seed:
        _index(flag_layout(seed=seed), seed)
    return _IDX["grid"]


def flag_at(x, y, seed=SEED):
    """-> the Flag whose FOOTPRINT contains (x, y), or None if in a joint."""
    g = _ensure_index(seed)
    for f in g.get(cell_index(x, y), ()):
        if f.x0 <= x <= f.x1 and f.y0 <= y <= f.y1:
            return f
    return None


def on_flag(x, y, seed=SEED):
    return flag_at(x, y, seed) is not None


def _flag_plane_z(f, x, y):
    """The straightedge level of flag f at (x, y) -- datum + tilt + rock + warp,
    WITHOUT the finish relief, because a thing resting on the flag bridges it."""
    u = x - f.cx
    v = y - f.cy
    hw = max(f.w * 0.5, 1e-6)
    hh = max(f.h * 0.5, 1e-6)
    un, vn_ = u / hw, v / hh
    warp = f.warp * (un * un + vn_ * vn_ - 0.66) * 0.75
    cs = ((-1, -1), (1, -1), (1, 1), (-1, 1))[f.rockc]
    rock = f.rock * max(0.0, 0.5 * (1.0 + un * cs[0])) * max(0.0, 0.5 * (1.0 + vn_ * cs[1]))
    return f.level + f.tx * u + f.ty * v + warp + rock


def flag_top_z(x, y, seed=SEED):
    """-> (z, flag_index).  In a joint, z is the JOINT BED and the index is -1.

    THIS IS THE FUNCTION A DEPENDANT SITS ON.  `concrete_spall_debris`,
    `glass_shard_fan_settled` and `forecourt_bollard` all resolve their z here
    rather than assuming C.APRON_Z, and that is the difference between a shard
    lying on the concrete and a shard 3 mm inside it.
    """
    f = flag_at(x, y, seed)
    if f is not None:
        return float(_flag_plane_z(f, x, y)), f.idx
    # a joint: interpolate between the two nearest flag planes and drop to bed
    g = _ensure_index(seed)
    i, j = cell_index(x, y)
    best, bz = 1e9, 0.0
    for ii in (i - 1, i, i + 1):
        for jj in (j - 1, j, j + 1):
            for f in g.get((ii, jj), ()):
                dx = max(f.x0 - x, 0.0, x - f.x1)
                dy = max(f.y0 - y, 0.0, y - f.y1)
                d = math.hypot(dx, dy)
                if d < best:
                    best = d
                    bz = _flag_plane_z(f, min(max(x, f.x0), f.x1),
                                       min(max(y, f.y0), f.y1))
    if best > 0.5:
        return float(C.APRON_Z), -1
    return float(bz - 0.012 - 0.008 * h01(i, j, 991)), -1


def surface_z(x, y, seed=SEED):
    return flag_top_z(x, y, seed)[0]


def nearest_joint(x, y, seed=SEED, joints=None):
    """-> (Joint, t, distance_m).  What a fragment slides into."""
    js = joints if joints is not None else joint_segments(
        _IDX["flags"] or flag_layout(seed=seed), seed)
    best, bj, bt = 1e9, None, 0.0
    for j in js:
        ax, ay = j.p0
        bx, by = j.p1
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 < 1e-12 else np.clip(((x - ax) * dx + (y - ay) * dy) / L2, 0, 1)
        px, py = ax + dx * t, ay + dy * t
        d = math.hypot(x - px, y - py)
        if d < best:
            best, bj, bt = d, j, float(t)
    return bj, bt, best


# =============================================================================
# 6.  THE MESH EMITTER  -- one graded grid, a quad mask, and real walls
# =============================================================================
ATTRS = ("agg", "aggid", "wear", "soil", "damp", "stain", "stype", "arr")

# The wall rows.  Dense at the top because only the top 14 mm of a flag's side
# is ever out of the bedding: the rest exists so the solid is closed, not so it
# can be looked at.
WALL_ROWS = (0.0025, 0.0060, 0.0110, 0.0190, 0.0310, 0.0450)


def _emit_grid(name, X, Y, Z, attrs, keep=None, skirt_depth=None,
               mat=0, smooth=True, wall_mat=None, wall_jitter=0.00022,
               seed=0):
    """Grid -> bpy Mesh, with walls wherever the quad mask has a boundary.

    The same routine builds a flag (mask all true, so the wall is the flag's
    four sides), an asphalt reinstatement (mask = the staircase of lifted
    cells, so the wall is the sawn trench edge) and a joint ribbon (no wall at
    all).  One code path, so a boundary is a boundary everywhere.
    """
    nx, ny = X.shape
    nv = nx * ny
    co = np.empty((nv, 3), np.float32)
    co[:, 0] = X.ravel()
    co[:, 1] = Y.ravel()
    co[:, 2] = Z.ravel()
    at = {k: np.asarray(attrs[k], np.float32).ravel().copy() for k in ATTRS}

    K = np.ones((nx - 1, ny - 1), bool) if keep is None else np.asarray(keep, bool)
    ii, jj = np.meshgrid(np.arange(nx - 1), np.arange(ny - 1), indexing="ij")
    k00 = ii * ny + jj
    quads = np.stack([k00, k00 + ny, k00 + ny + 1, k00 + 1], -1)[K].astype(np.int32)
    if quads.size == 0:
        return None
    fmat = np.full(len(quads), int(mat), np.int32)
    fsm = np.full(len(quads), bool(smooth), bool)

    if skirt_depth is not None:
        P = np.zeros((nx + 1, ny + 1), bool)
        P[1:-1, 1:-1] = K
        pairs = []
        # -x, +x, -y, +y.  The order of (a, b) is chosen so that (a->b) x (-z)
        # points OUT of the solid; see the note in the module header.
        sel = K & ~P[0:-2, 1:-1]
        a = (ii * ny + jj)[sel]
        b = (ii * ny + jj + 1)[sel]
        pairs.append((a, b))
        sel = K & ~P[2:, 1:-1]
        a = ((ii + 1) * ny + jj + 1)[sel]
        b = ((ii + 1) * ny + jj)[sel]
        pairs.append((a, b))
        sel = K & ~P[1:-1, 0:-2]
        a = ((ii + 1) * ny + jj)[sel]
        b = (ii * ny + jj)[sel]
        pairs.append((a, b))
        sel = K & ~P[1:-1, 2:]
        a = (ii * ny + jj + 1)[sel]
        b = ((ii + 1) * ny + jj + 1)[sel]
        pairs.append((a, b))
        A = np.concatenate([p[0] for p in pairs]).astype(np.int64)
        B = np.concatenate([p[1] for p in pairs]).astype(np.int64)
        ne = len(A)
        if ne:
            rows = np.asarray(WALL_ROWS, np.float64)
            rows = rows[rows < skirt_depth * 0.999]
            rows = np.concatenate([rows, [skirt_depth]])
            nr = len(rows)
            blocks = []
            for r_i, d in enumerate(rows):
                for src in (A, B):
                    c = co[src].astype(np.float64).copy()
                    jx = (h01(src, r_i, seed, 1) - 0.5) * 2.0 * wall_jitter
                    jy = (h01(src, r_i, seed, 2) - 0.5) * 2.0 * wall_jitter
                    c[:, 0] += jx * (1.0 - r_i / nr)
                    c[:, 1] += jy * (1.0 - r_i / nr)
                    c[:, 2] -= d
                    blocks.append(c.astype(np.float32))
            wco = np.concatenate(blocks, 0)
            base = nv
            idxA = base + np.arange(nr)[:, None] * (2 * ne) + np.arange(ne)[None, :]
            idxB = idxA + ne
            wq = []
            prevA, prevB = A, B
            for r_i in range(nr):
                wq.append(np.stack([prevA, prevB, idxB[r_i], idxA[r_i]], -1))
                prevA, prevB = idxA[r_i], idxB[r_i]
            wq = np.concatenate(wq, 0).astype(np.int32)
            co = np.concatenate([co, wco], 0)
            for k in ATTRS:
                v = at[k]
                rep = [v]
                for _r in range(nr):
                    rep.append(v[A])
                    rep.append(v[B])
                at[k] = np.concatenate(rep)
            # the wall IS the arris face: sign carries sawn (-) vs cast (+)
            sgn = np.sign(at["arr"][A])
            sgn = np.where(sgn == 0, 1.0, sgn)
            off = nv
            for _r in range(nr):
                at["arr"][off:off + ne] = sgn
                at["arr"][off + ne:off + 2 * ne] = sgn
                off += 2 * ne
            quads = np.concatenate([quads, wq], 0)
            fmat = np.concatenate(
                [fmat, np.full(len(wq), int(mat if wall_mat is None else wall_mat),
                               np.int32)])
            fsm = np.concatenate([fsm, np.zeros(len(wq), bool)])

    # DROP THE LOOSE VERTICES.  A masked grid keeps its full nx*ny vertex array
    # and only filters the QUADS, so every hole leaves its vertices behind with
    # nothing attached to them.  They render as nothing and they weigh nothing --
    # and then tools/placement_gate.py, which measures VERTICES, reported the
    # bedding sheet 1.598 m inside the car's driven path at three points where
    # the sheet has no faces at all.  An invisible vertex in a keep-out volume
    # is still a finding, and a finding nobody can see in a render is the worst
    # kind: it is either ignored or "fixed" by weakening the gate.
    used = np.unique(quads.ravel())
    if len(used) < len(co):
        remap = np.full(len(co), -1, np.int64)
        remap[used] = np.arange(len(used), dtype=np.int64)
        quads = remap[quads].astype(np.int32)
        co = co[used]
        for k in ATTRS:
            at[k] = at[k][used]

    me = bpy.data.meshes.new(name)
    npo = len(quads)
    me.vertices.add(len(co))
    me.vertices.foreach_set("co", np.ascontiguousarray(co, np.float32).ravel())
    me.loops.add(npo * 4)
    me.loops.foreach_set("vertex_index", np.ascontiguousarray(quads, np.int32).ravel())
    me.polygons.add(npo)
    me.polygons.foreach_set("loop_start", np.arange(npo, dtype=np.int32) * 4)
    me.update()
    me.validate(verbose=False)
    me.polygons.foreach_set("material_index", np.ascontiguousarray(fmat, np.int32))
    me.polygons.foreach_set("use_smooth", np.ascontiguousarray(fsm, bool))
    for k in ATTRS:
        a = me.attributes.new(k, "FLOAT", "POINT")
        a.data.foreach_set("value", np.ascontiguousarray(at[k], np.float32))
    return me


def bake_flag_attrs(me, **over):
    """Write every attribute mat_flag() reads onto an arbitrary mesh.

    A dependant that emits geometry into these materials and skips this gets a
    surface where `agg` reads 0 everywhere -- pure matrix, no stone -- and
    nobody traces the flat grey back to here.
    """
    n = len(me.vertices)
    d = dict(agg=0.25, aggid=0.5, wear=0.2, soil=0.4, damp=0.15,
             stain=0.0, stype=0.0, arr=0.0)
    d.update(over)
    for k in ATTRS:
        v = d[k]
        arr = (np.full(n, float(v), np.float32) if np.isscalar(v)
               else np.asarray(v, np.float32))
        a = me.attributes.get(k) or me.attributes.new(k, "FLOAT", "POINT")
        a.data.foreach_set("value", np.ascontiguousarray(arr))
    return me


# =============================================================================
# 7.  THE FLAG'S OWN SURFACE  -- relief, arris, chips, crack, socket
# =============================================================================
def _stain_fields(f, WX, WY, U, V, de, seed):
    """Six independent stain systems, each with its own spatial law.

    They are separate because they DO different things to light: iron is a
    matte plume that follows water, oil is a glossy patch that follows a
    parked car, rubber is a satin arc that follows a steered wheel, biofilm is
    a green-black film that follows damp, efflorescence is a white bloom that
    follows a joint, and patina is the general dirt everything gets.
    """
    s = f.seed
    r = lambda k: h01(s, k)                                          # noqa: E731
    damp = damp_field(WX, WY, seed)
    wear = wear_field(WX, WY, seed)

    # ---- iron: a run from something that rusted and drained across the flag
    rust = np.zeros_like(U)
    if r(101) < 0.11:
        ox = (r(103) - 0.5) * f.w
        oy = (r(105) - 0.5) * f.h
        ang = r(107) * 2 * math.pi
        dx = (U - ox) * math.cos(ang) + (V - oy) * math.sin(ang)
        dy = -(U - ox) * math.sin(ang) + (V - oy) * math.cos(ang)
        plume = np.exp(-((dy / (0.020 + 0.10 * np.clip(dx, 0, None))) ** 2))
        rust = np.clip(plume * _sstep(-0.02, 0.05, dx)
                       * (0.45 + 0.75 * fbm2(WX, WY, seed + 211, 0.09, 4)),
                       0.0, 1.0) * (0.5 + 0.5 * r(109))
    # ---- oil: where a car stood.  A drip cluster, not a blob.
    oil = np.zeros_like(U)
    if r(113) < 0.085 and abs(f.cy) > 6.0:
        ox = (r(115) - 0.5) * f.w * 0.8
        oy = (r(117) - 0.5) * f.h * 0.8
        d = np.hypot(U - ox, V - oy)
        oil = np.clip(np.exp(-(d / (0.035 + 0.11 * r(119))) ** 1.6)
                      * (0.5 + 0.9 * fbm2(WX * 3, WY * 3, seed + 223, 0.05, 3)),
                      0.0, 1.0)
    # ---- rubber: a scuff arc where a car was steered on the spot
    rub = np.zeros_like(U)
    dcx, dcy = 16.6, 7.9
    rr = np.hypot(WX - dcx, np.abs(WY) - dcy)
    band = np.exp(-((rr - 1.35) / 0.16) ** 2) + 0.7 * np.exp(-((rr - 2.10) / 0.13) ** 2)
    rub = np.clip(band * (0.35 + 0.85 * fbm2(WX * 2, WY * 2, seed + 227, 0.16, 4)),
                  0.0, 1.0)
    # ---- biofilm / algae: damp, and it creeps OUT of the joints
    edge_creep = np.exp(-np.maximum(de, 0.0) / 0.045)
    alg = np.clip(damp * (0.35 + 0.85 * edge_creep)
                  * (0.35 + 0.95 * fbm2(WX, WY, seed + 229, 0.22, 4))
                  * (1.0 - 0.55 * wear), 0.0, 1.0)
    # ---- efflorescence: lime carried to the surface, blooming at the joint
    eff = np.clip((0.25 + 0.75 * damp) * edge_creep
                  * _sstep(0.35, 0.85, fbm2(WX, WY, seed + 233, 0.13, 3))
                  * (0.30 + 0.90 * r(131)), 0.0, 1.0)
    # ---- the ghost of what stood here ------------------------------------
    ghost_clean = np.zeros_like(U)
    ghost_ring = np.zeros_like(U)
    for (mx, my, mr, nfeet, fr) in FURNITURE_MARKS:
        if abs(mx - f.cx) > f.w * 0.5 + mr + 0.12:
            continue
        if abs(my - f.cy) > f.h * 0.5 + mr + 0.12:
            continue
        dd = np.hypot(WX - mx, WY - my)
        rj = mr * (1.0 + 0.07 * (fbm2(WX * 9, WY * 9, seed + 251, 0.09, 3) - 0.5))
        ghost_clean = np.maximum(ghost_clean, _sstep(rj + 0.012, rj - 0.012, dd))
        ghost_ring = np.maximum(ghost_ring, np.exp(-((dd - rj) / 0.045) ** 2))
        for k in range(nfeet):
            a0 = 2 * math.pi * k / max(nfeet, 1) + 0.4
            fd = np.hypot(WX - (mx + math.cos(a0) * fr),
                          WY - (my + math.sin(a0) * fr))
            rust = np.maximum(rust, 0.85 * np.exp(-(fd / 0.030) ** 1.5)
                              * (0.55 + 0.65 * fbm2(WX * 6, WY * 6,
                                                    seed + 253, 0.04, 3)))
    rust = np.maximum(rust, 0.45 * ghost_ring
                      * fbm2(WX * 4, WY * 4, seed + 257, 0.07, 3))

    # ---- patina: age, shelter, and how long since anyone jet-washed it
    pat = np.clip(0.22 + 0.55 * f.age
                  + 0.45 * (fbm2(WX, WY, seed + 239, 0.55, 4) - 0.5)
                  + 0.30 * damp - 0.35 * wear, 0.0, 1.0)
    # RAIN DOES NOT LEAVE A FLAG EVENLY DIRTY.  It runs to the low corner, so
    # the uphill half stays soiled and the run-off track is washed clean, and a
    # dark margin builds along the arris where the water finally stands.  Three
    # lines, and they are what stops 1.5 m of flag reading as one tone.
    sx, sy = math.cos(f.shed), math.sin(f.shed)
    run = _sstep(-0.45, 0.55, (U * sx + V * sy) / max(0.5 * (f.w + f.h), 0.2))
    pat = np.clip(pat * (0.72 + 0.46 * run)
                  + 0.34 * np.exp(-np.maximum(de, 0.0) / 0.055)
                  * (0.5 + 0.7 * fbm2(WX * 2, WY * 2, seed + 241, 0.06, 3)),
                  0.0, 1.0)

    # under the thing that stood here the surface never weathered; against it
    # the dirt banked up.  Both, and the flag's own pallet shade on top.
    pat = np.clip(pat * (1.0 - 0.78 * ghost_clean) + 0.58 * ghost_ring, 0.0, 1.0)
    alg = np.clip(alg * (1.0 - 0.85 * ghost_clean), 0.0, 1.0)
    soil = np.clip((pat * 0.82 + alg * 0.45 + eff * 0.10) * f.tone, 0.0, 1.0)
    # one hot channel + a selector, because these three never coexist
    stain = np.maximum.reduce([rust, oil, rub])
    stype = np.where(rust >= np.maximum(oil, rub), 0.5,
                     np.where(oil >= rub, 0.0, 1.0))
    return dict(soil=soil.astype(np.float32),
                damp=np.clip(damp * 0.8 + eff * 0.35, 0, 1).astype(np.float32),
                stain=stain.astype(np.float32),
                stype=stype.astype(np.float32),
                wear=wear.astype(np.float32))


def _flag_fields(f, pitch, seed=SEED, fine=True):
    """-> (X, Y, Z, attrs) in LOCAL coordinates about the flag centre."""
    # The interior pitch already puts 6 samples across a 5 mm chamfer, so the
    # edge refinement is modest on purpose: a 2.1x density step over 12 mm was
    # itself visible as a band.  0.62x over 20 mm is not.
    epitch = float(np.clip(pitch * 0.62, 0.00055, 0.0024))
    ezone = float(np.clip(pitch * 24.0, 0.016, 0.042))
    us = _graded_axis(-f.w * 0.5, f.w * 0.5, pitch, ezone, epitch)
    vs = _graded_axis(-f.h * 0.5, f.h * 0.5, pitch, ezone, epitch)
    U, V = np.meshgrid(us, vs, indexing="ij")
    WX = f.cx + U
    WY = f.cy + V

    hw, hh = f.w * 0.5, f.h * 0.5
    d_mx = U + hw
    d_px = hw - U
    d_my = V + hh
    d_py = hh - V
    de = np.minimum(np.minimum(d_mx, d_px), np.minimum(d_my, d_py))

    # ---- 1. the flag as a bedded solid -----------------------------------
    un = U / max(hw, 1e-6)
    vn_ = V / max(hh, 1e-6)
    warp = f.warp * (un * un + vn_ * vn_ - 0.66) * 0.75
    cs = ((-1, -1), (1, -1), (1, 1), (-1, 1))[f.rockc]
    rock = f.rock * np.clip(0.5 * (1 + un * cs[0]), 0, 1) * np.clip(0.5 * (1 + vn_ * cs[1]), 0, 1)
    Z = f.level + f.tx * U + f.ty * V + warp + rock

    # ---- 2. the finish: aggregate and matrix ------------------------------
    off = (h01(f.seed, 301) * 90.0, h01(f.seed, 303) * 90.0)
    # THE MESH GRID AND THE STONE LATTICE MUST NOT SHARE AN AXIS.  Both were
    # world-aligned, so the sampling beat against the cell spacing and left a
    # faint diagonal crosshatch across the flag -- visible in the 2x peep, in
    # the corner where the graded axis changes density in BOTH directions at
    # once.  A per-flag rotation of the aggregate lattice removes the resonance
    # entirely and costs two multiplies; it is also what a real mould does,
    # since nothing about a concrete mix knows which way the flag was cast.
    ra = h01(f.seed, 305) * math.pi
    ca_, sa_ = math.cos(ra), math.sin(ra)
    RU = U * ca_ - V * sa_
    RV = U * sa_ + V * ca_
    f1, cid, _dx, _dy = worley(RU + off[0], RV + off[1], f.seed + 7,
                               cell=f.agg_cell, jitter=0.92)
    # `aggid` USED TO BE THE CELL'S HASH and it was wrong in a way only a 4x
    # peep showed: a hash is not interpolable.  Baked per vertex it blends
    # linearly between two neighbouring cells, and through a CONSTANT colour
    # ramp that sweep runs the WHOLE palette -- flint, quartz, basalt, granite
    # -- inside the 0.85 mm between two samples, at every cell boundary in the
    # field.  Averaged over a pixel that is grey mush, which is exactly what the
    # surface peep showed.  So the attribute now carries the stone's LIGHTNESS,
    # which is a physical quantity that interpolates correctly: a blend between
    # a dark flint and a pale quartz is a mid grey, and the ramp is LINEAR.
    e2 = (cid * 37.0) % 1.0
    e3 = (cid * 91.0) % 1.0
    e4 = (cid * 613.0) % 1.0
    lit = (cid * 149.0) % 1.0
    # A CRUSHED AGGREGATE IS NOT A FIELD OF IDENTICAL DOMES.  The first macro
    # read as pebbledash because every grain was the same size and the same
    # rounded profile.  Real stone in a blasted or washed face is graded (a
    # 3:1 spread of sizes) and ANGULAR (a flat-topped fragment with a sharp
    # shoulder), so the size spread is widened and the profile exponent is
    # randomised per grain: e5 near 0.35 is a flat chip, near 1.5 a river pebble.
    e5 = (cid * 271.0) % 1.0
    rad = f.agg_cell * (0.17 + 0.46 * e3)
    shp = 0.35 + 1.15 * e5
    t = np.clip(1.0 - (f1 / rad) ** (1.4 + 1.6 * e5), 0.0, 1.0) ** shp
    exposed = (e2 < f.expose).astype(np.float64)
    smask = t * exposed
    stone = f.agg_h * (0.45 + 0.85 * e4) * smask
    # ---- 2b. the coarse fraction ------------------------------------------
    rb = h01(f.seed, 307) * math.pi
    cb_, sb_ = math.cos(rb), math.sin(rb)
    f2, cid2, _dx2, _dy2 = worley(U * cb_ - V * sb_ + 70.0 + off[0],
                                  U * sb_ + V * cb_ + 70.0 + off[1],
                                  f.seed + 31, cell=f.agg2_cell, jitter=0.95)
    g2 = (cid2 * 17.0) % 1.0
    g3 = (cid2 * 89.0) % 1.0
    rad2 = f.agg2_cell * (0.16 + 0.26 * g3)
    t2 = np.clip(1.0 - (f2 / rad2) ** (1.5 + 1.2 * g3), 0.0, 1.0) ** (0.4 + 0.9 * g3)
    smask2 = t2 * (g2 < f.expose2).astype(np.float64)
    stone2 = f.agg2_h * (0.5 + 0.8 * ((cid2 * 331.0) % 1.0)) * smask2
    Z += np.maximum(stone, stone2) - f.erode * (1.0 - np.maximum(smask, smask2))
    # the coarse stone owns the colour where it is the one on top
    lit2 = (cid2 * 197.0) % 1.0
    win2 = smask2 > smask
    lit = np.where(win2, lit2, lit)
    smask = np.maximum(smask, smask2)
    Z += (fbm2(U * 1.0, V * 1.0, f.seed + 13, 0.0018, 2) - 0.5) * 0.00024
    del t2, f2, g2, g3, rad2, win2

    # ---- 3. the arris.  A CAST edge and a SAWN edge are different objects. --
    cw = np.array([CHAMFER_SAWN_M if (f.sawn & 1) else CHAMFER_W_M,
                   CHAMFER_SAWN_M if (f.sawn & 2) else CHAMFER_W_M,
                   CHAMFER_SAWN_M if (f.sawn & 4) else CHAMFER_W_M,
                   CHAMFER_SAWN_M if (f.sawn & 8) else CHAMFER_W_M])
    # a mould chamfer wobbles by +-0.4 mm along its length; a disc cut does not
    wob = 1.0 + 0.09 * (fbm2(WX * 4.0, WY * 4.0, f.seed + 17, 0.10, 3) - 0.5) * 2.0
    drop = np.maximum.reduce([
        np.maximum(cw[0] * wob - d_mx, 0.0), np.maximum(cw[1] * wob - d_px, 0.0),
        np.maximum(cw[2] * wob - d_my, 0.0), np.maximum(cw[3] * wob - d_py, 0.0)])
    Z -= drop
    # the cast chamfer has a mould radius at its top break; the sawn one is
    # square, and that 0.7 mm difference is 1.5 px and reads
    if not f.sawn:
        Z -= 0.0007 * np.exp(-((de - CHAMFER_W_M) / 0.0016) ** 2)

    # ---- 4. chips and corner spalls ---------------------------------------
    if fine:
        f1c, cidc, _a, _b = worley(RU + 40.0, RV + 40.0, f.seed + 23,
                                   cell=0.018, jitter=1.0)
        c2 = (cidc * 53.0) % 1.0
        rc = f.chipsz * (0.35 + 1.30 * c2)
        prof = np.clip(1.0 - (f1c / np.maximum(rc, 1e-5)) ** 1.35, 0.0, 1.0)
        gate = np.exp(-(np.maximum(de, 0.0) / CHIP_ZONE_M) ** 1.7)
        chip = (cidc < f.chip).astype(np.float64) * prof * gate * rc * 0.52
        Z -= chip
        for ci, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
            if h01(f.seed, 401 + ci) >= CORNER_SPALL_P:
                continue
            rr = 0.014 + 0.032 * h01(f.seed, 411 + ci)
            d = np.hypot(U - sx * hw, V - sy * hh)
            Z -= (rr * 0.34) * np.clip(1.0 - (d / rr) ** 1.6, 0.0, 1.0) ** 0.8

    # ---- 5. the crack ------------------------------------------------------
    if f.crack:
        ang = f.crackp * math.pi
        ca, sa = math.cos(ang), math.sin(ang)
        o = (f.crackp - 0.5) * 0.5 * min(f.w, f.h)
        sd = U * ca + V * sa - o
        sd = sd + 0.0055 * (fbm2(U * 6, V * 6, f.seed + 29, 0.06, 4) - 0.5) * 2.0
        wd = 0.0009 + 0.0018 * h01(f.seed, 61)
        Z -= (0.0035 + 0.0040 * h01(f.seed, 63)) * np.exp(-(sd / wd) ** 2)
        Z += 0.00042 * np.tanh(sd / 0.010)          # the two halves have parted

    # ---- 6. reservations: a cored socket with a grout collar --------------
    for rec in _RESERVE:
        if rec["shape"] == "circle":
            d = np.hypot(WX - rec["x"], WY - rec["y"])
            if float(d.min()) > rec["r"] + COLLAR_W_M + 0.02:
                continue
            rj = rec["r"] * (1.0 + 0.014 * (fbm2(WX * 20, WY * 20,
                                                 f.seed + 71, 0.05, 3) - 0.5))
            k = _sstep(rj + 0.0025, rj - 0.0025, d)
            collar = _sstep(rj + COLLAR_W_M, rj + 0.001, d) * (1.0 - k)
            Z = Z * (1.0 - k) + rec["floor"] * k
            Z = Z * (1.0 - collar) + (COLLAR_TOP_M + 0.0009 * (fbm2(
                WX * 30, WY * 30, f.seed + 73, 0.02, 3) - 0.5)) * collar
        else:
            inx = (WX > rec["x0"]) & (WX < rec["x1"])
            iny = (WY > rec["y0"]) & (WY < rec["y1"])
            k = (inx & iny).astype(np.float64)
            if k.max() > 0:
                Z = Z * (1 - k) + rec["floor"] * k

    # ---- 7. the attributes -------------------------------------------------
    st = _stain_fields(f, WX, WY, U, V, de, seed)
    arrmask = np.exp(-(np.maximum(de, 0.0) / 0.0038) ** 1.5)
    sawn_any = 1.0 if f.sawn else 0.0
    near_sawn = np.zeros_like(U)
    if f.sawn & 1:
        near_sawn = np.maximum(near_sawn, np.exp(-(d_mx / 0.008) ** 1.4))
    if f.sawn & 2:
        near_sawn = np.maximum(near_sawn, np.exp(-(d_px / 0.008) ** 1.4))
    if f.sawn & 4:
        near_sawn = np.maximum(near_sawn, np.exp(-(d_my / 0.008) ** 1.4))
    if f.sawn & 8:
        near_sawn = np.maximum(near_sawn, np.exp(-(d_py / 0.008) ** 1.4))
    arr = np.where(near_sawn > 0.5 * arrmask, -arrmask, arrmask)
    attrs = dict(
        agg=smask.astype(np.float32),
        aggid=lit.astype(np.float32),
        wear=st["wear"],
        soil=np.clip(st["soil"] + 0.16 * arrmask, 0, 1).astype(np.float32),
        damp=st["damp"],
        stain=st["stain"],
        stype=st["stype"],
        arr=arr.astype(np.float32))
    del sawn_any
    return U, V, Z, attrs


def flag_mesh(f, pitch, name=None, fine=True, seed=SEED):
    U, V, Z, attrs = _flag_fields(f, pitch, seed, fine)
    me = _emit_grid(name or ("%sF%06d" % (LIBPFX, f.idx)), U, V, Z, attrs,
                    keep=None, skirt_depth=abs(SOFFIT_M), mat=0, smooth=True,
                    seed=f.seed)
    f.n_verts = len(me.vertices)
    f.mesh_name = me.name
    return me


# =============================================================================
# 8.  THE JOINT ITSELF  -- a slot with a bed in it, not a dark line
# =============================================================================
def joint_ribbon_mesh(j, along, across, name, seed=SEED):
    """The jointing bed inside one slot, plus 7 mm tucked under each flag.

    The visible part is 12 mm wide -- 26 px on the 4K master -- so it is
    sampled at 0.8 mm across: 15 samples over the slot.  What is in there is
    kiln-dried sand that has washed to its own depth along every 100 mm, the
    grit that washed with it, and the humus a plant made.
    """
    L = j.length
    if L < 0.04:
        return None
    half = j.width_m * 0.5 + 0.007
    ts = np.arange(0.0, L + along * 0.5, along)
    ss = _graded_axis(-half, half, across, 0.004, min(across, 0.0006))
    T, S = np.meshgrid(ts, ss, indexing="ij")
    tt = T / max(L, 1e-9)
    bed = joint_bed_z(j, tt)
    # grit: individual grains, 0.6-2.2 mm, which is 1.3-4.8 px
    g1, gid, _a, _b = worley(T, S, j.seed + 3, cell=0.0022, jitter=1.0)
    gr = np.clip(1.0 - (g1 / (0.0011 * (0.5 + (gid * 17.0) % 1.0))) ** 2, 0, 1) ** 0.6
    z = bed + GRAIN_MAX_M * gr * (0.35 + 0.75 * ((gid * 7.0) % 1.0))
    z += (fbm2(T * 3, S * 3, j.seed + 5, 0.010, 3) - 0.5) * 0.0016
    # UNDER THE FLAG the bed rises to meet the underside of the chamfer, so the
    # slot is closed without the fill ever breaking the surface.
    #
    # The first version raised it to a level computed from the WHOLE ribbon
    # (max(bed) + 4 mm = +3.5 mm), which is above the top of most of the field:
    # under a flag bedded at -6.0 mm the jointing sand stood 9.5 mm PROUD of the
    # concrete, as a ridge down both sides of every joint.  The target has to be
    # the LOCAL arris on the side being tucked, minus the depth of that side's
    # chamfer, or the fill climbs out of the joint wherever a flag has settled.
    below = 0.0072 if j.kind == "formed" else 0.0038
    zside = np.where(S < 0.0, j.arris_z0, j.arris_z1) - below
    tuck = _sstep(j.width_m * 0.5, j.width_m * 0.5 + 0.006, np.abs(S))
    z = z * (1 - tuck) + zside * tuck
    if j.weeded:
        # a colonised joint has a humus mound: the plant built its own soil
        m = np.exp(-((tt - (0.25 + 0.5 * h01(j.seed, 31))) / 0.18) ** 2)
        z += m * (0.004 + 0.006 * h01(j.seed, 33)) * np.exp(-(S / 0.006) ** 2)
    if j.overband:
        # bitumen poured over the reinstatement joint: proud, wrinkled, glossy
        z = np.maximum(z, OVERBAND_H_M * np.exp(-(S / (OVERBAND_W_M * 0.5)) ** 4)
                       + 0.0004 * (fbm2(T * 8, S * 8, j.seed + 7, 0.02, 3) - 0.5))
    if j.axis == "y":
        X = np.full_like(T, j.p0[0]) + S
        Y = j.p0[1] + T
    else:
        X = j.p0[0] + T
        Y = np.full_like(T, j.p0[1]) + S
    cx, cy = 0.5 * (j.p0[0] + j.p1[0]), 0.5 * (j.p0[1] + j.p1[1])
    dmp = float(damp_field(np.array([cx]), np.array([cy]), seed)[0])
    n = T.size
    attrs = dict(
        agg=(gr * 0.7).astype(np.float32),
        aggid=gid.astype(np.float32),
        wear=np.full(n, 0.10, np.float32).reshape(T.shape),
        soil=np.clip(0.55 + 0.35 * dmp + 0.3 * (fbm2(X, Y, seed + 5, 0.08, 3) - 0.5),
                     0, 1).astype(np.float32),
        damp=np.full_like(T, np.clip(0.35 + 0.6 * dmp, 0, 1)).astype(np.float32),
        stain=np.zeros_like(T, np.float32),
        stype=np.zeros_like(T, np.float32),
        arr=np.zeros_like(T, np.float32))
    mat = 1 if not j.overband else 2
    return _emit_grid(name, X - cx, Y - cy, z, attrs, keep=None,
                      skirt_depth=None, mat=mat, smooth=True, seed=j.seed), (cx, cy)


def bedding_sheet(rect, coll, seed=SEED, tile=8.0, pitch=0.055,
                  suppress=None):
    """The bed under everything.  Coarse, and only ever seen in the far joints.

    Inside `suppress` (the radius where fine joint ribbons exist) it is dropped
    24 mm so it can never fight them; it is invisible there in any case,
    because the ribbons and the flags cover it completely.
    """
    out = []
    x0, x1, y0, y1 = rect
    nx = max(1, int(math.ceil((x1 - x0) / tile)))
    ny = max(1, int(math.ceil((y1 - y0) / tile)))
    for a in range(nx):
        for b in range(ny):
            ax0 = x0 + a * tile
            ax1 = min(x1, ax0 + tile)
            ay0 = y0 + b * tile
            ay1 = min(y1, ay0 + tile)
            xs = np.arange(ax0, ax1 + pitch * 0.5, pitch)
            ys = np.arange(ay0, ay1 + pitch * 0.5, pitch)
            if len(xs) < 2 or len(ys) < 2:
                continue
            X, Y = np.meshgrid(xs, ys, indexing="ij")
            # THE BED STOPS WHERE THE PAVING STOPS.  The first version swept a
            # continuous sheet over the whole build rect, which put 14 mm of
            # bedding sand under the access road and under the showroom floor --
            # 1.598 m inside the car's driven path on the placement gate, three
            # tiles over.  Neither surface is bedded by this trade.
            qx = 0.5 * (X[:-1, :-1] + X[1:, 1:])
            qy = 0.5 * (Y[:-1, :-1] + Y[1:, 1:])
            keep = np.ones(qx.shape, bool)
            for _n, (kx0, kx1, ky0, ky1) in _keepouts():
                keep &= ~((qx > kx0) & (qx < kx1) & (qy > ky0) & (qy < ky1))
            if not keep.any():
                continue
            z = (BED_COARSE_M + (fbm2(X, Y, seed + 811, 0.35, 4) - 0.5) * 0.006)
            if suppress:
                sx, sy, sr = suppress
                d = np.hypot(X - sx, Y - sy)
                z -= 0.024 * _sstep(sr + 1.2, sr - 0.4, d)
            n = X.size
            attrs = dict(agg=np.full_like(X, 0.35, np.float32),
                         aggid=(fbm2(X, Y, seed + 813, 0.02, 2)).astype(np.float32),
                         wear=np.zeros_like(X, np.float32),
                         soil=np.full_like(X, 0.62, np.float32),
                         damp=np.full_like(X, 0.35, np.float32),
                         stain=np.zeros_like(X, np.float32),
                         stype=np.zeros_like(X, np.float32),
                         arr=np.zeros_like(X, np.float32))
            del n
            cx, cy = 0.5 * (ax0 + ax1), 0.5 * (ay0 + ay1)
            me = _emit_grid("%sBed_%02d_%02d" % (PFX, a, b), X - cx, Y - cy, z,
                            attrs, keep=keep, skirt_depth=0.06, mat=1,
                            smooth=True, seed=seed + a * 31 + b)
            if me is None:
                continue
            ob = bpy.data.objects.new(me.name, me)
            ob.location = (cx, cy, 0.0)
            coll.objects.link(ob)
            out.append(ob)
    return out


# =============================================================================
# 9.  THE TRENCH REINSTATEMENTS  -- 2.4 % of the field, and a different trade
# =============================================================================
def _cell_dist(i, j, anchor):
    cb = cell_bounds(i, j)
    dx = max(cb[0] - anchor[0], 0.0, anchor[0] - cb[1])
    dy = max(cb[2] - anchor[1], 0.0, anchor[1] - cb[3])
    return math.hypot(dx, dy)


def trench_meshes(t, coll, pitch_near, anchor, seed=SEED, seen=None):
    """One asphalt reinstatement, built in DISTANCE BANDS.

    A reinstatement is not "a black quad".  It is 20 mm of binder rolled into a
    hole by a machine that cannot get within 150 mm of the edge, so it is always
    low in the middle, always coarse and proud at the cut, always a different
    black from the road, and always overbanded because the cut leaks.

    WHY BANDS.  The first version meshed each trench's whole bounding box at the
    pitch its nearest cell deserved: 9.0 M triangles for four reinstatements, of
    which the lens could see about 40 000.  The cells are therefore partitioned
    by their own distance from the lens and each band is its own panel.  The
    band boundary is a cell boundary, i.e. a construction joint between two
    pours -- which is what a reinstatement that was opened twice actually has.
    """
    objs = []
    cells_all = t.get("_paved_cells") or [c for c in t["cells"]
                                          if _cell_is_paved(int(c[0]), int(c[1]))]
    if not cells_all:
        return objs
    bands = {}
    for (i, j) in cells_all:
        d = _cell_dist(i, j, anchor)
        vis = True if seen is None else bool(seen(i, j))
        k = 0 if (vis and d < 2.9) else (1 if d < 6.5 else (2 if d < 15.0 else 3))
        bands.setdefault(k, []).append((i, j))
    pitches = (max(pitch_near, 0.0011), 0.004, 0.010, 0.024)
    for k, cells in sorted(bands.items()):
        pitch = pitches[k]
        # a hard cap, because a reinstatement that happens to sit under the lens
        # would otherwise mesh 2 M quads per square metre and spend the whole
        # budget on asphalt the frame cannot see
        area = sum(CELL_W * CELL_H for _c in cells)
        if area / (pitch * pitch) > 1.2e6:
            pitch = math.sqrt(area / 1.2e6)
        xs_ = [SETOUT_X + i * CELL_W for (i, _j) in cells]
        ys_ = [SETOUT_Y + j * CELL_H for (_i, j) in cells]
        bx0, bx1 = min(xs_), max(xs_) + CELL_W
        by0, by1 = min(ys_), max(ys_) + CELL_H
        xs = np.arange(bx0, bx1 + pitch * 0.5, pitch)
        ys = np.arange(by0, by1 + pitch * 0.5, pitch)
        if len(xs) < 3 or len(ys) < 3:
            continue
        X, Y = np.meshgrid(xs, ys, indexing="ij")
        qx = 0.5 * (X[:-1, :-1] + X[1:, 1:])
        qy = 0.5 * (Y[:-1, :-1] + Y[1:, 1:])
        keep = np.zeros(qx.shape, bool)
        for (i, j) in cells:
            cb = cell_bounds(i, j)
            keep |= ((qx > cb[0] + 0.0015) & (qx < cb[1] - 0.0015)
                     & (qy > cb[2] + 0.0015) & (qy < cb[3] - 0.0015))
        if not keep.any():
            continue
        # distance in from the CUT, which is what the roller law is written on
        inner = np.zeros(X.shape)
        for (i, j) in cells_all:
            cb = cell_bounds(i, j)
            inner = np.maximum(inner, np.minimum.reduce([
                X - cb[0], cb[1] - X, Y - cb[2], cb[3] - Y]))
        age = t["age"]
        sunk = t["sunk"]
        z = (ASPH_TOP_M - sunk * _sstep(0.0, 0.55, inner)
             + 0.0016 * (fbm2(X, Y, seed + 907, 0.6, 4) - 0.5))
        c1, cid, _a, _b = worley(X, Y, seed + 911, cell=0.0092, jitter=0.95)
        cr = 0.0040 + 0.0016 * ((cid * 23.0) % 1.0)
        ch = np.clip(1.0 - (c1 / cr) ** 2, 0, 1) ** 0.55
        prod = 0.0010 + 0.0022 * _sstep(0.30, 0.03, inner) + 0.0009 * age
        z += ch * prod * (0.4 + 0.9 * ((cid * 131.0) % 1.0))
        z -= 0.0007 * (1.0 - ch) * (0.4 + 0.9 * age)
        cx, cy = 0.5 * (bx0 + bx1), 0.5 * (by0 + by1)
        attrs = dict(
            agg=ch.astype(np.float32), aggid=cid.astype(np.float32),
            wear=np.clip(wear_field(X, Y, seed) * (0.6 + 0.6 * age), 0, 1
                         ).astype(np.float32),
            soil=np.clip(0.25 + 0.65 * age
                         + 0.3 * (fbm2(X, Y, seed + 913, 0.25, 3) - 0.5),
                         0, 1).astype(np.float32),
            damp=damp_field(X, Y, seed).astype(np.float32),
            stain=np.zeros_like(X, np.float32), stype=np.zeros_like(X, np.float32),
            arr=np.zeros_like(X, np.float32))
        me = _emit_grid("%sAsph_%s_%d" % (PFX, t["name"], k), X - cx, Y - cy, z,
                        attrs, keep=keep, skirt_depth=0.030, mat=3, smooth=True,
                        seed=seed + 17 + k)
        if me is None:
            continue
        ob = bpy.data.objects.new(me.name, me)
        ob.location = (cx, cy, 0.0)
        coll.objects.link(ob)
        objs.append(ob)
    return objs


# =============================================================================
# 10.  THE COLONISTS  -- four species, every plant generated from its own seed
# =============================================================================
def _blade(px, py, pz, az, seed, L, w0, kind=0):
    """One grass blade: a folded strip that arcs over under its own weight.

    Two quads per segment with a raised crease, because a blade seen at 0.45 mm
    per pixel is a V in section, and a flat ribbon reads as plastic.
    """
    r = lambda k: h01(seed, k)                                       # noqa: E731
    n = 8 + int(r(1) * 4)
    lean = 0.30 + 0.62 * r(3)
    curl = 0.7 + 1.5 * r(5)
    twist = (r(7) - 0.5) * 1.4
    V = []
    Q = []
    A = []
    prev = None
    for s in range(n + 1):
        t = s / float(n)
        arc = lean * (t ** curl)
        h = L * t * (1.0 - 0.42 * arc)
        rad = L * arc * 0.85
        ang = az + twist * t
        cx = px + math.cos(ang) * rad
        cy = py + math.sin(ang) * rad
        cz = pz + h
        wid = w0 * (1.0 - t) ** 0.75 + 0.00012
        nx_, ny_ = -math.sin(ang), math.cos(ang)
        crease = wid * 0.30 * (1.0 - t * 0.4)
        a = (cx - nx_ * wid, cy - ny_ * wid, cz)
        b = (cx, cy, cz + crease)
        c = (cx + nx_ * wid, cy + ny_ * wid, cz)
        base = len(V)
        V.extend([a, b, c])
        A.extend([t, t, t])
        if prev is not None:
            Q.append((prev, prev + 1, base + 1, base))
            Q.append((prev + 1, prev + 2, base + 2, base + 1))
        prev = base
    return V, Q, A


def _leaf(px, py, pz, az, seed, L, W):
    """A prostrate rosette leaf.

    THE FIRST VERSION RENDERED A SUCCULENT.  Five smooth 90 mm ellipses with a
    pale tip is a houseplant, not a plantain in a paving joint -- the peep at
    0.11 mm/px showed fat fleshy paddles with no edge and no rib.  A real
    pavement rosette leaf is 20-45 mm, has a SERRATED margin, a raised MIDRIB
    that makes it fold along its length, and it lies down and curls at the tip
    under its own weight.  All three are geometry, and at 0.4554 mm/px a 1.5 mm
    tooth on the margin is 3.3 px -- visible, and the thing that stops the
    silhouette reading as an ellipse.
    """
    r = lambda k: h01(seed, k)                                       # noqa: E731
    nu, nv = 13, 6
    V, Q, A = [], [], []
    tilt = 0.07 + 0.22 * r(1)
    teeth = 4 + int(r(2) * 5)
    tdep = 0.10 + 0.22 * r(3)
    rib = 0.10 + 0.14 * r(4)
    curl = 0.55 + 1.10 * r(5)
    for iu in range(nu + 1):
        u = iu / float(nu)
        marg = 1.0 - tdep * (0.5 + 0.5 * math.cos(u * teeth * 2.0 * math.pi))
        for iv in range(nv + 1):
            v = (iv / float(nv)) * 2.0 - 1.0
            wid = (W * math.sin(math.pi * min(u, 0.999) ** 0.55) * marg
                   * (1.0 - 0.10 * abs(v)))
            rr = L * u
            cx = px + math.cos(az) * rr - math.sin(az) * v * wid
            cy = py + math.sin(az) * rr + math.cos(az) * v * wid
            # the midrib holds the centre up and the margins fall away from it
            fold = rib * wid * (1.0 - abs(v) ** 1.5) - rib * wid * 0.35
            droop = L * tilt * math.sin(math.pi * u ** curl)
            cz = pz + droop + fold + 0.0004 * math.cos(v * 4.7 + u * 9.0)
            V.append((cx, cy, cz))
            A.append(u)
    for iu in range(nu):
        for iv in range(nv):
            k = iu * (nv + 1) + iv
            Q.append((k, k + nv + 1, k + nv + 2, k + 1))
    return V, Q, A


def weed_tuft(kind, seed, scale=1.0):
    """-> (verts, quads, t_attr).  Local, z from 0 up, origin at the bed."""
    r = lambda k: h01(seed, k)                                       # noqa: E731
    V, Q, A = [], [], []

    def add(v, q, a):
        b = len(V)
        V.extend(v)
        A.extend(a)
        Q.extend([(x + b, y + b, z + b, w + b) for (x, y, z, w) in q])

    if kind == 0:                       # annual meadow grass, the joint classic
        n = 9 + int(r(11) * 14)
        for k in range(n):
            az = r(20 + k) * 2 * math.pi
            L = (0.030 + 0.085 * r(60 + k) ** 1.4) * scale
            add(*_blade((r(90 + k) - 0.5) * 0.010, (r(120 + k) - 0.5) * 0.010,
                        0.0, az, seed * 7 + k, L, 0.00105 + 0.0007 * r(150 + k)))
    elif kind == 1:                     # moss cushion
        R = (0.022 + 0.055 * r(11)) * scale
        p = max(0.0016, R / 26.0)
        xs = np.arange(-R, R + p, p)
        X, Y = np.meshgrid(xs, xs, indexing="ij")
        d = np.hypot(X, Y) / R
        z = (0.004 + 0.012 * r(13)) * np.clip(1 - d ** 2, 0, 1) ** 0.62
        z += (fbm2(X, Y, seed + 3, 0.008, 4) - 0.5) * 0.0035 * np.clip(1 - d, 0, 1)
        z += (fbm2(X, Y, seed + 5, 0.0022, 2) - 0.5) * 0.0016 * np.clip(1 - d, 0, 1)
        z = np.where(d > 1.0, -0.004, z)
        nx = len(xs)
        for a in range(nx):
            for b in range(nx):
                V.append((float(X[a, b]), float(Y[a, b]), float(z[a, b])))
                A.append(float(np.clip(1.0 - d[a, b], 0, 1)))
        for a in range(nx - 1):
            for b in range(nx - 1):
                if d[a, b] > 1.05 and d[a + 1, b + 1] > 1.05:
                    continue
                k = a * nx + b
                Q.append((k, k + nx, k + nx + 1, k + 1))
        for k in range(26 + int(r(17) * 40)):     # the shoots on top
            aa = r(200 + k) * 2 * math.pi
            rr = R * 0.92 * math.sqrt(r(240 + k))
            add(*_blade(math.cos(aa) * rr, math.sin(aa) * rr,
                        float(0.010 * (1 - (rr / R) ** 2)), r(280 + k) * 6.28,
                        seed * 13 + k, 0.004 + 0.006 * r(320 + k), 0.00035))
    elif kind == 2:                     # procumbent pearlwort: a prostrate mat
        for k in range(14 + int(r(11) * 16)):
            aa = r(30 + k) * 2 * math.pi
            rr = (0.004 + 0.030 * r(70 + k)) * scale
            add(*_blade(math.cos(aa) * rr, math.sin(aa) * rr, 0.0,
                        aa + (r(110 + k) - 0.5), seed * 17 + k,
                        0.006 + 0.016 * r(160 + k), 0.00055))
    else:                               # a plantain / dandelion rosette
        n = 9 + int(r(11) * 6)
        for k in range(n):
            az = (k / float(n)) * 2 * math.pi + (r(30 + k) - 0.5) * 0.9
            # graded: the outer whorl is old and long, the centre is new and
            # short, which is what makes a rosette read as a rosette
            g = (k / float(n - 1)) if n > 1 else 0.0
            L = (0.016 + 0.030 * (1.0 - g) + 0.014 * r(70 + k)) * scale
            add(*_leaf(0.0, 0.0, 0.0, az, seed * 19 + k, L, L * 0.20))
        for k in range(1 + int(r(13) * 3)):       # and a seed stalk
            add(*_blade(0.0, 0.0, 0.0, r(90 + k) * 6.28, seed * 23 + k,
                        0.045 + 0.070 * r(130 + k), 0.00060))
    return V, Q, A


def grit_grain(seed, size):
    """One washed-out grain of jointing grit, lying on the flag.

    WHY THIS EXISTS.  Rain does not leave a paved joint alone: it lifts the
    kiln-dried sand out of the slot and fans it across the flag downhill of it,
    and after one winter there is a scatter of 1-4 mm grit along every joint.
    At 0.4554 mm per pixel a 2.5 mm grain is 5.5 px with a 25 px shadow at the
    contract sun, which makes it one of the strongest "this is a real surface"
    signals available in this frame -- and it costs 28 quads.

    Angular, not spherical: this is crushed rock, and a sphere reads as caviar.
    """
    r = lambda k: h01(seed, k)                                       # noqa: E731
    nu, nv = 7, 4
    V, Q = [], []
    for iu in range(nu):
        au = 2 * math.pi * iu / nu
        for iv in range(nv + 1):
            av = math.pi * (iv / float(nv)) - math.pi * 0.5
            rad = size * (0.55 + 0.75 * r(iu * 11 + iv * 3 + 7))
            V.append((math.cos(av) * math.cos(au) * rad,
                      math.cos(av) * math.sin(au) * rad,
                      math.sin(av) * rad * (0.42 + 0.30 * r(iu + 41))))
    for iu in range(nu):
        for iv in range(nv):
            a = iu * (nv + 1) + iv
            b = ((iu + 1) % nu) * (nv + 1) + iv
            Q.append((a, b, b + 1, a + 1))
    zmin = min(v[2] for v in V)
    V = [(x, y, z - zmin) for (x, y, z) in V]
    me = bpy.data.meshes.new("%sGrit_%06d" % (LIBPFX, seed % 999999))
    co = np.asarray(V, np.float32)
    quads = np.asarray(Q, np.int32)
    me.vertices.add(len(co))
    me.vertices.foreach_set("co", co.ravel())
    me.loops.add(len(quads) * 4)
    me.loops.foreach_set("vertex_index", quads.ravel())
    me.polygons.add(len(quads))
    me.polygons.foreach_set("loop_start", np.arange(len(quads), dtype=np.int32) * 4)
    me.update()
    me.validate(verbose=False)
    me.polygons.foreach_set("use_smooth", np.zeros(len(quads), bool))
    bake_flag_attrs(me, agg=0.85, aggid=float(r(3)), wear=0.05,
                    soil=float(0.35 + 0.5 * r(5)), damp=float(0.3 * r(7)))
    return me


def weed_object(kind, seed, name, scale=1.0):
    V, Q, A = weed_tuft(kind, seed, scale)
    if not Q:
        return None
    me = bpy.data.meshes.new(name)
    co = np.asarray(V, np.float32)
    quads = np.asarray(Q, np.int32)
    me.vertices.add(len(co))
    me.vertices.foreach_set("co", co.ravel())
    me.loops.add(len(quads) * 4)
    me.loops.foreach_set("vertex_index", quads.ravel())
    me.polygons.add(len(quads))
    me.polygons.foreach_set("loop_start", np.arange(len(quads), dtype=np.int32) * 4)
    me.update()
    me.validate(verbose=False)
    me.polygons.foreach_set("use_smooth", np.ones(len(quads), bool))
    a = me.attributes.new("t", "FLOAT", "POINT")
    a.data.foreach_set("value", np.ascontiguousarray(np.asarray(A, np.float32)))
    a = me.attributes.new("sp", "FLOAT", "POINT")
    a.data.foreach_set("value", np.full(len(co), kind / 3.0, np.float32))
    return me


# =============================================================================
# 11.  MATERIALS  -- procedural, layered, and TexCoord->Object EVERYWHERE
# =============================================================================
# At |P| ~ 1000 m a Geometry->Position driven procedural loses all precision and
# blotches; that is what wrecked the first world pass.  The forecourt sits at
# |P| < 40 m, so it would arguably survive -- and it still does not do it,
# because the flags in the far field are INSTANCED and a position-driven shader
# would make every instance of one source identical AND world-locked at once.
# Object space + baked attributes + Object Info Random is the combination that
# is both precise and per-instance unique.
def _srgb(hexstr):
    v = [int(hexstr[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    return tuple((c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
                 for c in v) + (1.0,)


class _MB(object):
    """Tiny node-graph builder: keeps the material code readable."""

    def __init__(self, name):
        m = bpy.data.materials.get(name)
        if m is None:
            m = bpy.data.materials.new(name)
        m.use_nodes = True
        self.m = m
        self.nt = m.node_tree
        self.nt.nodes.clear()
        self.x = 0
        self.mat = m

    def n(self, t, x=None, y=0, **kw):
        nd = self.nt.nodes.new(t)
        self.x += 190 if x is None else 0
        nd.location = (self.x if x is None else x, y)
        for k, v in kw.items():
            setattr(nd, k, v)
        return nd

    def link(self, a, ao, b, bi):
        self.nt.links.new(a.outputs[ao], b.inputs[bi])

    def attr(self, name, y=0):
        a = self.n("ShaderNodeAttribute", x=-1500, y=y)
        a.attribute_name = name
        return a

    def objco(self, y=0):
        t = self.n("ShaderNodeTexCoord", x=-1700, y=y)
        return t

    def noise(self, co, scale, detail=6.0, rough=0.55, w=None, y=0, dist=0.0):
        nd = self.n("ShaderNodeTexNoise", x=-1200, y=y)
        nd.noise_dimensions = "4D"
        nd.inputs["Scale"].default_value = scale
        nd.inputs["Detail"].default_value = detail
        nd.inputs["Roughness"].default_value = rough
        if "Distortion" in nd.inputs:
            nd.inputs["Distortion"].default_value = dist
        self.link(co, "Object", nd, "Vector")
        if w is not None:
            self.link(w[0], w[1], nd, "W")
        return nd

    def vor(self, co, scale, y=0, feature="F1", w=None):
        nd = self.n("ShaderNodeTexVoronoi", x=-1200, y=y)
        nd.voronoi_dimensions = "4D"
        nd.feature = feature
        nd.inputs["Scale"].default_value = scale
        self.link(co, "Object", nd, "Vector")
        if w is not None:
            self.link(w[0], w[1], nd, "W")
        return nd

    def ramp(self, src, so, stops, y=0):
        r = self.n("ShaderNodeValToRGB", y=y)
        e = r.color_ramp.elements
        while len(e) > 1:
            e.remove(e[-1])
        e[0].position = stops[0][0]
        e[0].color = stops[0][1]
        for (p, c) in stops[1:]:
            el = e.new(p)
            el.color = c
        self.link(src, so, r, "Fac")
        return r

    def mix(self, fac, fo, a, ao, b, bo, y=0, blend="MIX"):
        n = self.n("ShaderNodeMix", y=y)
        n.data_type = "RGBA"
        n.blend_type = blend
        if isinstance(fac, (int, float)):
            n.inputs["Factor"].default_value = float(fac)
        else:
            self.link(fac, fo, n, "Factor")
        if isinstance(a, tuple):
            n.inputs[6].default_value = a
        else:
            self.nt.links.new(a.outputs[ao], n.inputs[6])
        if isinstance(b, tuple):
            n.inputs[7].default_value = b
        else:
            self.nt.links.new(b.outputs[bo], n.inputs[7])
        return n

    def math(self, op, a, ao, b=None, bo=None, y=0, clamp=False):
        n = self.n("ShaderNodeMath", y=y)
        n.operation = op
        n.use_clamp = clamp
        if isinstance(a, (int, float)):
            n.inputs[0].default_value = float(a)
        else:
            self.nt.links.new(a.outputs[ao], n.inputs[0])
        if b is not None:
            if isinstance(b, (int, float)):
                n.inputs[1].default_value = float(b)
            else:
                self.nt.links.new(b.outputs[bo], n.inputs[1])
        return n


# The palette.  Invented, physical, and consistent across the three families.
# Cement is a COOL grey and the contract sun is warm (1.000, 0.716, 0.387 at
# 12.47 deg elevation).  A warm matrix under a warm key reads as sandstone, so
# the pigment is held slightly blue of neutral and the light does the warming.
COL_MATRIX = _srgb("b0aeab")        # cement matrix, shot-blasted
COL_MATRIX_D = _srgb("87867f")      # matrix in the shade of its own texture
COL_GRANITE = _srgb("a49a92")       # pink-grey granite
COL_FLINT = _srgb("55524d")         # dark flint
COL_QUARTZ = _srgb("d7d2c6")        # white quartz
COL_BASALT = _srgb("3f423f")        # basalt
COL_HONE = _srgb("55565a")          # charcoal honed body
COL_HONE_S = _srgb("7d8085")        # its cut aggregate
COL_RUST = _srgb("8a4a24")
COL_OIL = _srgb("2a2622")
COL_RUBBER = _srgb("3a3835")
COL_ALGAE = _srgb("4a5137")
COL_EFF = _srgb("e6e4dc")
COL_SAND = _srgb("a89a80")
COL_GRIT = _srgb("77706a")
COL_BITUMEN = _srgb("232224")
COL_ASPH = _srgb("3b3a38")
COL_CHIP = _srgb("6e6a63")
COL_LEAF = _srgb("5c6f34")
COL_LEAF_DRY = _srgb("8a7c46")
COL_MOSS = _srgb("47632c")


def _flag_material(name, fam):
    """One precast family.  Nine texture layers, and every one of them is doing
    a different job that can be named:

      1 aggregate colour by baked cell id      which stone this grain is
      2 matrix colour variation                the cement is not one grey
      3 batch shift by Object Info Random      no two instances share a shade
      4 large-scale mould variation            the flag has a face, not a tone
      5 wear polish                            traffic cuts the stone flat
      6 stain: iron / oil / rubber             three different reflectances
      7 biofilm + efflorescence                the damp story
      8 sub-mm matrix pitting (BUMP)           below the geometry floor
      9 saw-blade score on sawn faces (BUMP)   0.25 mm = 0.55 px, the only
                                               feature on this item legitimately
                                               left to a bump map
    """
    b = _MB(name)
    co = b.objco()
    oi = b.n("ShaderNodeObjectInfo", x=-1700, y=-600)
    a_agg = b.attr("agg", y=520)
    a_id = b.attr("aggid", y=380)
    a_wear = b.attr("wear", y=240)
    a_soil = b.attr("soil", y=100)
    a_damp = b.attr("damp", y=-40)
    a_stain = b.attr("stain", y=-180)
    a_stype = b.attr("stype", y=-320)
    a_arr = b.attr("arr", y=-460)

    # ---- 1. which stone -----------------------------------------------------
    if fam == FAM_HONE:
        stones = [(0.00, _srgb("34363a")), (0.24, _srgb("4c4e52")),
                  (0.50, COL_HONE_S), (0.74, _srgb("8f9298")),
                  (1.00, _srgb("b0b2b8"))]
        body = COL_HONE
        body_d = _srgb("3f4044")
    else:
        stones = [(0.00, _srgb("2c2f2d")), (0.18, COL_BASALT),
                  (0.36, COL_FLINT), (0.55, _srgb("7d7468")),
                  (0.72, COL_GRANITE), (0.88, _srgb("cdc4b2")),
                  (1.00, _srgb("e3ded2"))]
        body = COL_MATRIX
        body_d = COL_MATRIX_D
    ramp_stone = b.ramp(a_id, "Fac", stones, y=380)
    ramp_stone.color_ramp.interpolation = "LINEAR"

    # ---- 2. the matrix, which is not one grey -------------------------------
    n_mat = b.noise(co, 320.0, detail=6.0, rough=0.62, w=(oi, "Random"), y=200)
    mat_col = b.mix(n_mat, "Fac", body, None, body_d, None, y=200)

    # ---- 3. + 4. batch shade and the flag's own face ------------------------
    # THE FLAG'S OWN GREY.  Two pallets of precast poured a fortnight apart are
    # never the same colour, and a forecourt of 1 027 flags all at one value is
    # the single most synthetic thing a paving render can do.  The scale is 0.9
    # (a 1.1 m wavelength against a 1.5 m flag), so this reads as ONE FLAG'S
    # TONE with a gradient across it rather than as blotching -- and its W is
    # Object Info Random, so no two instances of one library mesh share it.
    n_face = b.noise(co, 0.9, detail=5.0, rough=0.5, w=(oi, "Random"), y=60,
                     dist=0.35)
    face = b.ramp(n_face, "Fac", [(0.22, (0.80, 0.80, 0.81, 1)),
                                  (0.50, (1.0, 1.0, 1.0, 1)),
                                  (0.80, (1.16, 1.15, 1.12, 1))], y=60)
    base = b.mix(a_agg, "Fac", mat_col, "Result", ramp_stone, "Color", y=300)
    base = b.mix(1.0, None, base, "Result", face, "Color", y=300,
                 blend="MULTIPLY")

    # ---- 5. polish: traffic cuts the proud stone flat and darkens the matrix -
    pol = b.math("MULTIPLY", a_wear, "Fac", 0.85, None, y=-100)
    base2 = b.mix(pol, "Value", base, "Result", (0.80, 0.79, 0.77, 1), None,
                  y=-100, blend="MULTIPLY")

    # ---- 6. the three stains ------------------------------------------------
    n_st = b.noise(co, 42.0, detail=6.0, rough=0.6, w=(oi, "Random"), y=-260)
    st_amt = b.math("MULTIPLY", a_stain, "Fac", n_st, "Fac", y=-260, clamp=True)
    st_amt = b.math("POWER", st_amt, "Value", 0.75, None, y=-300, clamp=True)
    st_col = b.ramp(a_stype, "Fac", [(0.00, COL_OIL), (0.34, COL_OIL),
                                     (0.42, COL_RUST), (0.62, COL_RUST),
                                     (0.72, COL_RUBBER), (1.00, COL_RUBBER)],
                    y=-260)
    c_st = b.mix(st_amt, "Value", base2, "Result", st_col, "Color", y=-260)

    # ---- 7. biofilm and efflorescence ---------------------------------------
    n_alg = b.noise(co, 12.0, detail=7.0, rough=0.58, w=(oi, "Random"), y=-420,
                    dist=0.6)
    alg_m = b.math("MULTIPLY", a_damp, "Fac", n_alg, "Fac", y=-420, clamp=True)
    alg_m = b.math("MULTIPLY", alg_m, "Value", 0.85, None, y=-460, clamp=True)
    c_alg = b.mix(alg_m, "Value", c_st, "Result", COL_ALGAE, None, y=-420)
    # EFFLORESCENCE IS A BLOOM, NOT A WASH.  The first version multiplied `damp`
    # by a Voronoi's Distance output and clamped -- and Distance is a metric in
    # texture units, not a 0..1 mask, so anywhere damp x distance exceeded 1 the
    # clamp pinned the mask at 1.0 and the flag rendered as SOLID WHITE LIME.
    # In the first macro that was half the frame.  A ramp turns the metric into
    # a mask with a floor and a ceiling, and the bloom is capped at 0.55 because
    # lime carried to a surface stains it, it does not paint it.
    n_eff = b.vor(co, 26.0, y=-560, feature="SMOOTH_F1", w=(oi, "Random"))
    eff_r = b.ramp(n_eff, "Distance", [(0.28, (0.0, 0.0, 0.0, 1)),
                                       (0.62, (1.0, 1.0, 1.0, 1))], y=-560)
    eff_n = b.noise(co, 7.5, detail=6.0, rough=0.6, w=(oi, "Random"), y=-620)
    eff_m = b.math("MULTIPLY", eff_r, "Color", eff_n, "Fac", y=-600, clamp=True)
    eff_m = b.math("MULTIPLY", eff_m, "Value", a_damp, "Fac", y=-620, clamp=True)
    eff_m = b.math("MULTIPLY", eff_m, "Value", 0.55, None, y=-640, clamp=True)
    c_eff = b.mix(eff_m, "Value", c_alg, "Result", COL_EFF, None, y=-560)

    # ---- soil / patina ------------------------------------------------------
    n_soil = b.noise(co, 5.5, detail=8.0, rough=0.62, w=(oi, "Random"), y=-700)
    soil_m = b.math("MULTIPLY", a_soil, "Fac", n_soil, "Fac", y=-700, clamp=True)
    # 0.55 read as a haze at 1.7 m.  Dirt on a fifteen-year-old forecourt is not
    # a haze; it is the difference between the flag under the planter and the
    # flag beside it, and it has to carry that far.
    soil_m = b.math("MULTIPLY", soil_m, "Value", 0.72, None, y=-740, clamp=True)
    c_soil = b.mix(soil_m, "Value", c_eff, "Result", _srgb("6f6a60"), None, y=-700)

    # ---- the arris: cast edges catch light, sawn edges show cut stone -------
    # A CAST ARRIS AND A SAWN ARRIS ARE DIFFERENT SURFACES, not one edge mask.
    # The mould face is laitance-rich -- finer, paler, almost no exposed stone.
    # The disc cut is the opposite: it slices every grain open, so the sawn band
    # is the HIGHEST-contrast aggregate anywhere on the flag.  At 0.46 mm per
    # pixel a 5 mm chamfer is 11 px of it, and the difference reads.
    arr_abs = b.math("ABSOLUTE", a_arr, "Fac", y=-860)
    sawn_sel = b.math("LESS_THAN", a_arr, "Fac", -0.02, None, y=-900)
    cast_sel = b.math("GREATER_THAN", a_arr, "Fac", 0.02, None, y=-860)
    cast_m = b.math("MULTIPLY", cast_sel, "Value", arr_abs, "Value", y=-870)
    cast_m = b.math("MULTIPLY", cast_m, "Value", 0.22, None, y=-880, clamp=True)
    c_cast = b.mix(cast_m, "Value", c_soil, "Result",
                   _srgb("c6c2b8") if fam != FAM_HONE else _srgb("6d6e73"),
                   None, y=-860)
    sawn_face = b.math("MULTIPLY", sawn_sel, "Value", arr_abs, "Value", y=-940)
    col = b.mix(sawn_face, "Value", c_cast, "Result", ramp_stone, "Color",
                y=-980)

    # ---- roughness ----------------------------------------------------------
    n_rgh = b.noise(co, 90.0, detail=6.0, rough=0.55, w=(oi, "Random"), y=-1100)
    rg = b.ramp(n_rgh, "Fac", [(0.25, (0.60, 0.60, 0.60, 1)),
                               (0.75, (0.86, 0.86, 0.86, 1))], y=-1100)
    rg_w = b.mix(a_wear, "Fac", rg, "Color", (0.34, 0.34, 0.34, 1), None, y=-1140)
    rg_d = b.mix(alg_m, "Value", rg_w, "Result", (0.42, 0.42, 0.42, 1), None,
                 y=-1180)
    rg_s = b.mix(st_amt, "Value", rg_d, "Result", (0.26, 0.26, 0.26, 1), None,
                 y=-1220)

    # ---- 8. + 9. the bump layers -------------------------------------------
    n_pit = b.noise(co, 1500.0, detail=5.0, rough=0.55, w=(oi, "Random"), y=-1340)
    bump1 = b.n("ShaderNodeBump", y=-1340)
    bump1.inputs["Strength"].default_value = 0.55 if fam != FAM_HONE else 0.12
    bump1.inputs["Distance"].default_value = 0.00028
    b.link(n_pit, "Fac", bump1, "Height")
    w_saw = b.n("ShaderNodeTexWave", x=-1200, y=-1500)
    w_saw.wave_type = "RINGS"
    w_saw.inputs["Scale"].default_value = 3.5
    w_saw.inputs["Distortion"].default_value = 1.5
    w_saw.inputs["Detail"].default_value = 2.0
    b.link(co, "Object", w_saw, "Vector")
    saw_h = b.math("MULTIPLY", w_saw, "Fac", sawn_face, "Value", y=-1500)
    bump2 = b.n("ShaderNodeBump", y=-1500)
    bump2.inputs["Strength"].default_value = 0.45
    bump2.inputs["Distance"].default_value = 0.00026
    b.link(saw_h, "Value", bump2, "Height")
    b.link(bump1, "Normal", bump2, "Normal")
    bev = b.n("ShaderNodeBevel", y=-1620)
    bev.samples = 6
    bev.inputs["Radius"].default_value = 0.0006
    b.link(bump2, "Normal", bev, "Normal")

    bsdf = b.n("ShaderNodeBsdfPrincipled", x=520, y=0)
    out = b.n("ShaderNodeOutputMaterial", x=820, y=0)
    b.link(col, "Result", bsdf, "Base Color")
    b.link(rg_s, "Result", bsdf, "Roughness")
    b.link(bev, "Normal", bsdf, "Normal")
    bsdf.inputs["Specular IOR Level"].default_value = 0.42
    if "Coat Weight" in bsdf.inputs:
        bsdf.inputs["Coat Weight"].default_value = 0.0
    b.link(bsdf, "BSDF", out, "Surface")
    return b.m


def mat_flag(fam=FAM_BLAST):
    return _flag_material("FCP_Flag_%s" % FAM_NAME[fam], fam)


def mat_joint():
    """Kiln-dried sand, silt, grit and the humus a plant made."""
    b = _MB("FCP_JointFill")
    co = b.objco()
    oi = b.n("ShaderNodeObjectInfo", x=-1700, y=-600)
    a_agg = b.attr("agg", y=400)
    a_id = b.attr("aggid", y=260)
    a_soil = b.attr("soil", y=120)
    a_damp = b.attr("damp", y=-20)
    grit = b.ramp(a_id, "Fac", [(0.0, COL_GRIT), (0.3, _srgb("8b8177")),
                                (0.55, _srgb("5f5b55")), (0.8, _srgb("9d937f")),
                                (1.0, _srgb("6b6559"))], y=260)
    grit.color_ramp.interpolation = "CONSTANT"
    # A JOINT LIT ONLY BY SKY RENDERS BLUE, and it should -- but a real one also
    # gets a bounce off two concrete walls 12 mm apart, so the fill is paler and
    # warmer than the pure sky tint the first peep showed.
    n_s = b.noise(co, 55.0, detail=7.0, rough=0.6, w=(oi, "Random"), y=120)
    sand = b.mix(n_s, "Fac", _srgb("bdae90"), None, COL_SAND, None, y=120)
    base = b.mix(a_agg, "Fac", sand, "Result", grit, "Color", y=200)
    n_d = b.noise(co, 9.0, detail=8.0, rough=0.6, w=(oi, "Random"), y=-140)
    dirt = b.math("MULTIPLY", a_soil, "Fac", n_d, "Fac", y=-140, clamp=True)
    c1 = b.mix(dirt, "Value", base, "Result", _srgb("4a453c"), None, y=-140)
    wet = b.math("MULTIPLY", a_damp, "Fac", 0.8, None, y=-260, clamp=True)
    c2 = b.mix(wet, "Value", c1, "Result", _srgb("36322b"), None, y=-260)
    # same defect, same fix: Distance through a ramp before it is used as a mask
    n_alg = b.vor(co, 34.0, y=-380, feature="SMOOTH_F1", w=(oi, "Random"))
    alg_r = b.ramp(n_alg, "Distance", [(0.22, (0.0, 0.0, 0.0, 1)),
                                       (0.58, (1.0, 1.0, 1.0, 1))], y=-380)
    algm = b.math("MULTIPLY", a_damp, "Fac", alg_r, "Color", y=-400, clamp=True)
    algm = b.math("MULTIPLY", algm, "Value", 0.80, None, y=-420, clamp=True)
    c3 = b.mix(algm, "Value", c2, "Result", COL_ALGAE, None, y=-380)
    n_r = b.noise(co, 180.0, detail=5.0, rough=0.5, w=(oi, "Random"), y=-500)
    rg = b.ramp(n_r, "Fac", [(0.2, (0.78, 0.78, 0.78, 1)),
                             (0.85, (0.97, 0.97, 0.97, 1))], y=-500)
    rgw = b.mix(wet, "Value", rg, "Color", (0.40, 0.40, 0.40, 1), None, y=-540)
    n_b = b.noise(co, 900.0, detail=5.0, rough=0.55, w=(oi, "Random"), y=-660)
    bump = b.n("ShaderNodeBump", y=-660)
    bump.inputs["Strength"].default_value = 0.5
    bump.inputs["Distance"].default_value = 0.0004
    b.link(n_b, "Fac", bump, "Height")
    bsdf = b.n("ShaderNodeBsdfPrincipled", x=520)
    out = b.n("ShaderNodeOutputMaterial", x=820)
    b.link(c3, "Result", bsdf, "Base Color")
    b.link(rgw, "Result", bsdf, "Roughness")
    b.link(bump, "Normal", bsdf, "Normal")
    b.link(bsdf, "BSDF", out, "Surface")
    return b.m


def mat_overband():
    b = _MB("FCP_Overband")
    co = b.objco()
    oi = b.n("ShaderNodeObjectInfo", x=-1700, y=-600)
    a_soil = b.attr("soil", y=200)
    n1 = b.noise(co, 60.0, detail=7.0, rough=0.6, w=(oi, "Random"), y=200)
    base = b.mix(n1, "Fac", COL_BITUMEN, None, _srgb("343133"), None, y=200)
    n2 = b.noise(co, 8.0, detail=6.0, rough=0.5, w=(oi, "Random"), y=40)
    dust = b.math("MULTIPLY", a_soil, "Fac", n2, "Fac", y=40, clamp=True)
    c = b.mix(dust, "Value", base, "Result", _srgb("6d675c"), None, y=40)
    n3 = b.noise(co, 220.0, detail=6.0, rough=0.55, w=(oi, "Random"), y=-120)
    rg = b.ramp(n3, "Fac", [(0.2, (0.22, 0.22, 0.22, 1)),
                            (0.8, (0.55, 0.55, 0.55, 1))], y=-120)
    n4 = b.noise(co, 340.0, detail=6.0, rough=0.6, w=(oi, "Random"), y=-260)
    bump = b.n("ShaderNodeBump", y=-260)
    bump.inputs["Strength"].default_value = 0.6
    bump.inputs["Distance"].default_value = 0.0009
    b.link(n4, "Fac", bump, "Height")
    bsdf = b.n("ShaderNodeBsdfPrincipled", x=520)
    out = b.n("ShaderNodeOutputMaterial", x=820)
    b.link(c, "Result", bsdf, "Base Color")
    b.link(rg, "Color", bsdf, "Roughness")
    b.link(bump, "Normal", bsdf, "Normal")
    b.link(bsdf, "BSDF", out, "Surface")
    return b.m


def mat_asphalt():
    """A trench reinstatement: not the road's asphalt and not the same black."""
    b = _MB("FCP_Reinstatement")
    co = b.objco()
    oi = b.n("ShaderNodeObjectInfo", x=-1700, y=-600)
    a_agg = b.attr("agg", y=380)
    a_id = b.attr("aggid", y=240)
    a_soil = b.attr("soil", y=100)
    a_wear = b.attr("wear", y=-40)
    a_damp = b.attr("damp", y=-180)
    chip = b.ramp(a_id, "Fac", [(0.0, COL_CHIP), (0.3, _srgb("857c70")),
                                (0.55, _srgb("4f4b46")), (0.8, _srgb("9c9184")),
                                (1.0, _srgb("5c574f"))], y=240)
    chip.color_ramp.interpolation = "CONSTANT"
    n1 = b.noise(co, 70.0, detail=7.0, rough=0.6, w=(oi, "Random"), y=100)
    bind = b.mix(n1, "Fac", COL_ASPH, None, _srgb("2b2a29"), None, y=100)
    base = b.mix(a_agg, "Fac", bind, "Result", chip, "Color", y=180)
    n2 = b.noise(co, 3.5, detail=7.0, rough=0.6, w=(oi, "Random"), y=-60)
    grey = b.math("MULTIPLY", a_soil, "Fac", n2, "Fac", y=-60, clamp=True)
    c1 = b.mix(grey, "Value", base, "Result", _srgb("7a746a"), None, y=-60)
    c2 = b.mix(a_wear, "Fac", c1, "Result", _srgb("46443f"), None, y=-200)
    n3 = b.noise(co, 150.0, detail=6.0, rough=0.55, w=(oi, "Random"), y=-340)
    rg = b.ramp(n3, "Fac", [(0.2, (0.45, 0.45, 0.45, 1)),
                            (0.8, (0.82, 0.82, 0.82, 1))], y=-340)
    rgw = b.mix(a_damp, "Fac", rg, "Color", (0.34, 0.34, 0.34, 1), None, y=-380)
    n4 = b.noise(co, 1100.0, detail=5.0, rough=0.5, w=(oi, "Random"), y=-500)
    bump = b.n("ShaderNodeBump", y=-500)
    bump.inputs["Strength"].default_value = 0.4
    bump.inputs["Distance"].default_value = 0.0003
    b.link(n4, "Fac", bump, "Height")
    bev = b.n("ShaderNodeBevel", y=-560)
    bev.samples = 4
    bev.inputs["Radius"].default_value = 0.0005
    b.link(bump, "Normal", bev, "Normal")
    bsdf = b.n("ShaderNodeBsdfPrincipled", x=520)
    out = b.n("ShaderNodeOutputMaterial", x=820)
    b.link(c2, "Result", bsdf, "Base Color")
    b.link(rgw, "Result", bsdf, "Roughness")
    b.link(bev, "Normal", bsdf, "Normal")
    b.link(bsdf, "BSDF", out, "Surface")
    return b.m


def mat_plant():
    """Leaf and moss in one shader, selected by the `sp` attribute.

    Translucent, because a 0.15 mm blade at a 12.5 deg sun is lit from behind
    for most of the shot and an opaque leaf there reads as green plastic.
    """
    b = _MB("FCP_Colonist")
    co = b.objco()
    oi = b.n("ShaderNodeObjectInfo", x=-1700, y=-600)
    a_t = b.attr("t", y=300)
    a_sp = b.attr("sp", y=160)
    # every plant its own green: Object Info Random shifts the whole species
    # band, so a joint with four colonists in it does not have four of one plant
    n1 = b.noise(co, 26.0, detail=6.0, rough=0.6, w=(oi, "Random"), y=160)
    hue = b.ramp(oi, "Random", [(0.00, _srgb("5f6b30")), (0.34, _srgb("4e6335")),
                                (0.62, _srgb("6a7a3a")), (1.00, _srgb("55622c"))],
                 y=220)
    grn = b.mix(n1, "Fac", hue, "Color", _srgb("7a8a4c"), None, y=160)
    mossc = b.mix(n1, "Fac", COL_MOSS, None, _srgb("6a7d38"), None, y=60)
    body = b.mix(a_sp, "Fac", grn, "Result", mossc, "Result", y=200)
    # THE PALE TIP WAS DOING TOO MUCH.  A weed does dry from the tip, but the
    # first ramp turned the last 15 % of every leaf bone-white and the peep
    # showed five highlights instead of five leaves.
    tip = b.ramp(a_t, "Fac", [(0.62, (1.0, 1.0, 1.0, 1)),
                              (0.90, (0.94, 0.92, 0.74, 1)),
                              (1.00, (0.84, 0.78, 0.56, 1))], y=-60)
    c = b.mix(1.0, None, body, "Result", tip, "Color", y=-60, blend="MULTIPLY")
    dry = b.noise(co, 3.0, detail=5.0, rough=0.5, w=(oi, "Random"), y=-200)
    drym = b.math("POWER", dry, "Fac", 2.4, None, y=-200, clamp=True)
    c2 = b.mix(drym, "Value", c, "Result", COL_LEAF_DRY, None, y=-200)
    vein = b.n("ShaderNodeTexWave", x=-1200, y=-340)
    vein.wave_type = "BANDS"
    vein.inputs["Scale"].default_value = 190.0
    vein.inputs["Distortion"].default_value = 3.0
    b.link(co, "Object", vein, "Vector")
    bump = b.n("ShaderNodeBump", y=-340)
    bump.inputs["Strength"].default_value = 0.30
    bump.inputs["Distance"].default_value = 0.00025
    b.link(vein, "Fac", bump, "Height")
    bsdf = b.n("ShaderNodeBsdfPrincipled", x=520)
    out = b.n("ShaderNodeOutputMaterial", x=820)
    b.link(c2, "Result", bsdf, "Base Color")
    b.link(bump, "Normal", bsdf, "Normal")
    bsdf.inputs["Roughness"].default_value = 0.42
    for nm, v in (("Subsurface Weight", 0.35), ("Subsurface Scale", 0.004)):
        if nm in bsdf.inputs:
            bsdf.inputs[nm].default_value = v
    if "Subsurface Radius" in bsdf.inputs:
        bsdf.inputs["Subsurface Radius"].default_value = (0.006, 0.010, 0.003)
    b.link(bsdf, "BSDF", out, "Surface")
    b.m.use_backface_culling = False
    return b.m


_MATS = {}


def materials():
    if not _MATS:
        _MATS["flag_blast"] = mat_flag(FAM_BLAST)
        _MATS["flag_hone"] = mat_flag(FAM_HONE)
        _MATS["flag_agg"] = mat_flag(FAM_AGG)
        _MATS["joint"] = mat_joint()
        _MATS["overband"] = mat_overband()
        _MATS["asphalt"] = mat_asphalt()
        _MATS["plant"] = mat_plant()
    return _MATS


def _slots(me, names):
    m = materials()
    for n in names:
        me.materials.append(m[n])
    return me


# =============================================================================
# 12.  BUILD  -- the explicit near field, the libraries, the instancers
# =============================================================================
def _collection(name, parent=None, link=True):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
    if link:
        par = parent or bpy.context.scene.collection
        if c.name not in par.children:
            par.children.link(c)
    return c


def _clear():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for me in list(bpy.data.meshes):
        bpy.data.meshes.remove(me)
    for ng in list(bpy.data.node_groups):
        bpy.data.node_groups.remove(ng)
    for cl in list(bpy.data.collections):
        bpy.data.collections.remove(cl)
    _MATS.clear()


def _fam_slot(f):
    return {FAM_BLAST: "flag_blast", FAM_HONE: "flag_hone",
            FAM_AGG: "flag_agg"}[f.fam]


def _flag_object(f, coll, pitch, name=None, fine=True, seed=SEED, link=True):
    me = flag_mesh(f, pitch, name=name, fine=fine, seed=seed)
    _slots(me, [_fam_slot(f), "joint", "overband", "asphalt"])
    ob = bpy.data.objects.new(me.name, me)
    ob.location = (float(f.cx), float(f.cy), 0.0)
    if link:
        coll.objects.link(ob)
    return ob


def _pick_instancer(name, library, n_src, seed, flip=True, spin=False):
    """Instance-on-points, picking a DIFFERENT SOURCE MESH per point.

    `Pick Instance` + a random index into a collection of unique meshes is the
    only arrangement that scores > 1 on the gate's `distinct_sources`, and it
    is the only one that is true: a rotated copy of one flag is one flag.
    The 180 deg flip below sits ON TOP of that, never instead of it.
    """
    ng = bpy.data.node_groups.new(name, "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT",
                            socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT",
                            socket_type="NodeSocketGeometry")
    gi = ng.nodes.new("NodeGroupInput"); gi.location = (-800, 0)
    go = ng.nodes.new("NodeGroupOutput"); go.location = (800, 0)
    ci = ng.nodes.new("GeometryNodeCollectionInfo"); ci.location = (-800, -260)
    ci.inputs["Collection"].default_value = library
    ci.inputs["Separate Children"].default_value = True
    ci.inputs["Reset Children"].default_value = True
    iop = ng.nodes.new("GeometryNodeInstanceOnPoints"); iop.location = (300, 0)
    iop.inputs["Pick Instance"].default_value = True
    ridx = ng.nodes.new("FunctionNodeRandomValue"); ridx.location = (-400, -520)
    ridx.data_type = "INT"
    for s in ridx.inputs:
        if not s.enabled:
            continue
        if s.name == "Min":
            s.default_value = 0
        elif s.name == "Max":
            s.default_value = max(0, n_src - 1)
        elif s.name == "Seed":
            s.default_value = int(seed) % 30000
    ng.links.new(gi.outputs[0], iop.inputs["Points"])
    ng.links.new(ci.outputs["Instances"], iop.inputs["Instance"])
    for s in ridx.outputs:
        if s.enabled:
            ng.links.new(s, iop.inputs["Instance Index"])
            break
    if flip or spin:
        rr = ng.nodes.new("FunctionNodeRandomValue"); rr.location = (-620, -820)
        rr.data_type = "FLOAT"
        for s in rr.inputs:
            if not s.enabled:
                continue
            if s.name == "Min":
                s.default_value = 0.0
            elif s.name == "Max":
                s.default_value = 1.0
            elif s.name == "Seed":
                s.default_value = (int(seed) + 811) % 30000
        src = None
        for s in rr.outputs:
            if s.enabled:
                src = s
                break
        if spin:
            mul = ng.nodes.new("ShaderNodeMath"); mul.location = (-380, -820)
            mul.operation = "MULTIPLY"
            mul.inputs[1].default_value = 2.0 * math.pi
            ng.links.new(src, mul.inputs[0])
            last = mul
        else:
            gt = ng.nodes.new("ShaderNodeMath"); gt.location = (-420, -820)
            gt.operation = "GREATER_THAN"
            gt.inputs[1].default_value = 0.5
            ng.links.new(src, gt.inputs[0])
            mul = ng.nodes.new("ShaderNodeMath"); mul.location = (-240, -820)
            mul.operation = "MULTIPLY"
            mul.inputs[1].default_value = math.pi
            ng.links.new(gt.outputs[0], mul.inputs[0])
            last = mul
        cxyz = ng.nodes.new("ShaderNodeCombineXYZ"); cxyz.location = (-60, -820)
        ng.links.new(last.outputs[0], cxyz.inputs["Z"])
        ng.links.new(cxyz.outputs[0], iop.inputs["Rotation"])
    ng.links.new(iop.outputs["Instances"], go.inputs[0])
    return ng


def _points_object(name, pts, coll):
    me = bpy.data.meshes.new(name)
    me.from_pydata([(float(a), float(b), float(c)) for (a, b, c) in pts], [], [])
    me.update()
    ob = bpy.data.objects.new(me.name, me)
    coll.objects.link(ob)
    return ob


def _synth_flag(proto, key, k, seed):
    """A LIBRARY flag is not a copy of a placed one.

    It shares only what the bucket forces it to share -- its footprint, because
    a 1.488 m flag in a 1.238 m slot leaves a 250 mm hole in the forecourt --
    and generates its own family, warp, rock, arris, chips, crack, aggregate,
    age and stains from its own seed.  That is what makes it a library and not
    "one flag spammed 1 000 times".
    """
    f = Flag(**{s: getattr(proto, s) for s in Flag.__slots__})
    f.seed = int(h01(key[0] * 1e4, key[1] * 1e4, k, seed, 97) * 2e9)
    f.idx = 900000 + k
    f.level = 0.0
    f.cx = 0.0
    f.cy = 0.0
    r = lambda t: h01(f.seed, t)                                     # noqa: E731
    f.i = int(r(2) * 40) - 20
    f.j = int(r(4) * 40) - 20
    _decide_flag(f, seed)
    # the large-scale fields cannot follow an instance, so a library flag samples
    # them at a plausible point of its own and the per-instance shade comes from
    # Object Info Random in the shader.  Documented, bounded, and only ever used
    # beyond EXPLICIT_R_M where a 9 mm mesh is already the limit.
    f.cx = 15.0 + (r(6) - 0.5) * 30.0
    f.cy = (r(8) - 0.5) * 30.0
    f.trench = ""
    return f


def _frame_footprint(az_deg=VIEW_AZ_DEG, pitch_deg=CAM_PITCH_DEG,
                     lens=LENS_AT_CLOSEST_MM, h=NEAREST_CAMERA_M):
    """-> (near_d, far_d, half_angle_rad, ux, uy) of the ground the lens sees."""
    vhalf = math.degrees(math.atan(0.5 * SENSOR_MM * RES_Y_4K / RES_X_4K / lens))
    hhalf = math.atan(0.5 * SENSOR_MM / lens)
    near_d = h / math.tan(math.radians(pitch_deg + vhalf))
    far_d = h / math.tan(math.radians(pitch_deg - vhalf))
    a = math.radians(az_deg)
    return near_d, far_d, hhalf, math.cos(a), math.sin(a), \
        h / math.tan(math.radians(pitch_deg))


def build(anchor_world=None, quality="hero", seed=SEED, coll_name=COLL_NAME,
          rect=None, explicit_r=EXPLICIT_R_M, field_r=FIELD_R_M,
          lib_per_bucket=None, bedding=True, weeds=True, sockets=True,
          stats=None, vert_budget=VERT_BUDGET, view_az_deg=VIEW_AZ_DEG,
          ribbon_strip=True):
    """Emit the forecourt.  -> stats dict.

    `anchor_world` is THE LENS.  Flags near it are individual unique meshes at
    a pitch that resolves ~2 px at their own distance; flags beyond
    `explicit_r` come from libraries of unique flag meshes.  The report carries
    the repeat factor rather than hiding it.
    """
    t0 = time.time()
    global RIBBON_STRIP
    RIBBON_STRIP = bool(ribbon_strip)
    draft = (quality == "draft")
    coll = _collection(coll_name)
    libcoll = _collection(LIB_COLL_NAME, link=False)
    materials()
    if sockets:
        default_reservations()
    if lib_per_bucket is None:
        lib_per_bucket = 3 if draft else 14
    if draft:
        explicit_r = min(explicit_r, 3.2)
        field_r = min(field_r, 16.0)
        vert_budget = 900_000

    ax, ay = (anchor_world[0], anchor_world[1]) if anchor_world else (17.5, 8.0)
    az = anchor_world[2] if (anchor_world and len(anchor_world) > 2) else NEAREST_CAMERA_M
    if rect is None:
        rect = (max(X0, ax - field_r), min(X1, ax + field_r),
                max(Y0, ay - field_r), min(Y1, ay + field_r))

    flags = flag_layout(rect, seed)
    _index(flags, seed)
    joints = joint_segments(flags, seed)
    laid = [f for f in flags if not f.trench]
    print(">> layout: %d cells laid over %.0f m2 (mean %.3f m2), %d joints, "
          "%d sawn (%.1f %%), %d weeded (%.1f %%)"
          % (len(laid), sum(f.area for f in laid),
             sum(f.area for f in laid) / max(len(laid), 1), len(joints),
             sum(1 for j in joints if j.kind == "sawn"),
             100.0 * sum(1 for j in joints if j.kind == "sawn") / max(len(joints), 1),
             sum(1 for j in joints if j.weeded),
             100.0 * sum(1 for j in joints if j.weeded) / max(len(joints), 1)))

    # ---- 1. near / far ------------------------------------------------------
    # THE BUDGET GOES WHERE THE LENS LOOKS.  At 1.7 m on a 35 mm lens the frame
    # covers ground from 0.48 to 1.90 m out and about 2.1 m across -- 3 m2, or
    # two flags and a bit.  Spending 0.85 mm on the 180 flags inside a 9 m
    # radius would cost 400 M vertices to put 99 % of them off camera.  So the
    # pitch is chosen against the FRUSTUM: in-frame flags get the hero pitch,
    # everything else gets a pitch that is honest for a bounce and a shadow.
    n_d, f_d, hh, ux, uy, aim_d = _frame_footprint(view_az_deg)
    ox = ax + ux * 0.0
    oy = ay + uy * 0.0

    def _seen(cx, cy, w=1.5, margin=0.45):
        dx, dy = cx - ox, cy - oy
        sd = dx * ux + dy * uy
        td = abs(-dx * uy + dy * ux)
        if sd < n_d - margin - w or sd > f_d + margin:
            return False
        return td <= sd * math.tan(hh) + margin + w * 0.5

    def in_frame(f, margin=0.45):
        return _seen(f.cx, f.cy, f.w, margin)

    def in_frame_cell(i, j):
        cb = cell_bounds(i, j)
        return _seen(0.5 * (cb[0] + cb[1]), 0.5 * (cb[2] + cb[3]), CELL_W)

    near, far = [], []
    for f in laid:
        d = math.sqrt((f.cx - ax) ** 2 + (f.cy - ay) ** 2 + az * az)
        (near if d <= explicit_r else far).append((d, f))

    objs = []
    verts = 0
    dropped = []
    n_hero = 0
    for d, f in sorted(near, key=lambda t: t[0]):
        p = lod_pitch(d) if in_frame(f) else max(lod_pitch(d) * 4.0, 0.0055)
        n_hero += 1 if p <= 0.0009 else 0
        est = int((f.w / p + 4) * (f.h / p + 4) * 1.3)
        if verts + est > vert_budget:
            dropped.append((d, f))
            continue
        ob = _flag_object(f, coll, p, name="%sFlag_%05d" % (PFX, f.idx),
                          fine=True, seed=seed)
        objs.append(ob)
        verts += len(ob.data.vertices)
    if dropped:
        print(">> vertex budget: %d of %d near flags pushed to the instanced band"
              % (len(dropped), len(near)))
        far.extend(dropped)
        near = [t for t in near if t not in dropped]
    print(">> explicit near field: %d flags, %d verts, %d of them at the hero "
          "pitch (%.2f mm = %.2f px at %.2f m)"
          % (len(objs), verts, n_hero, 1000 * lod_pitch(0.0),
             lod_pitch(0.0) * PX_PER_M, NEAREST_CAMERA_M))

    # ---- 2. the libraries ---------------------------------------------------
    buckets = {}
    for d, f in far:
        buckets.setdefault((round(f.w, 3), round(f.h, 3)), []).append(f)
    libs = {}
    lib_n = 0
    explicit_far = []
    for key, members in sorted(buckets.items()):
        if len(members) < 3:
            explicit_far.extend(members)
            continue
        n = min(lib_per_bucket, max(3, len(members)))
        cl = _collection("%s_%d_%d" % (LIB_COLL_NAME, int(key[0] * 1000),
                                       int(key[1] * 1000)), link=False)
        if cl.name not in libcoll.children:
            libcoll.children.link(cl)
        srcs = []
        for k in range(n):
            lf = _synth_flag(members[0], key, lib_n, seed)
            me = flag_mesh(lf, LIB_PITCH_M,
                           name="%sB%d_%d_%02d" % (LIBPFX, int(key[0] * 1000),
                                                   int(key[1] * 1000), k),
                           fine=True, seed=seed)
            _slots(me, [_fam_slot(lf), "joint", "overband", "asphalt"])
            ob = bpy.data.objects.new(me.name, me)
            ob.hide_render = True
            cl.objects.link(ob)
            srcs.append(ob)
            lib_n += 1
        libs[key] = (cl, srcs)
    for f in explicit_far:
        ob = _flag_object(f, coll, 0.018, name="%sFlagX_%05d" % (PFX, f.idx),
                          fine=False, seed=seed)
        objs.append(ob)

    # ---- 3. the instancers --------------------------------------------------
    inst_objs = []
    n_inst = 0
    for key, members in sorted(buckets.items()):
        if key not in libs:
            continue
        cl, srcs = libs[key]
        ob = _points_object("%sField_%d_%d" % (PFX, int(key[0] * 1000),
                                               int(key[1] * 1000)),
                            [(f.cx, f.cy, f.level) for f in members], coll)
        ng = _pick_instancer(ob.name + "_GN", cl, len(srcs),
                             seed + int(key[0] * 977) + int(key[1] * 131),
                             flip=True)
        md = ob.modifiers.new("paving", "NODES")
        md.node_group = ng
        ob["instances"] = len(members)
        ob["library_sources"] = len(srcs)
        inst_objs.append(ob)
        n_inst += len(members)
    print(">> instanced field: %d flags from %d buckets, %d unique source meshes "
          "at %.1f mm (repeat %.1fx), %d far flags built explicitly"
          % (n_inst, len(libs), lib_n, LIB_PITCH_M * 1000,
             n_inst / max(lib_n, 1), len(explicit_far)))

    # ---- 4. the joints ------------------------------------------------------
    jobjs = []
    for j in joints:
        mid = (0.5 * (j.p0[0] + j.p1[0]), 0.5 * (j.p0[1] + j.p1[1]))
        d = math.hypot(mid[0] - ax, mid[1] - ay)
        if d > RIBBON_R2_M:
            continue
        dx, dy = mid[0] - ox, mid[1] - oy
        sd = dx * ux + dy * uy
        td = abs(-dx * uy + dy * ux)
        seen = (n_d - 0.6 <= sd <= f_d + 0.9) and td <= sd * math.tan(hh) + 0.6
        fine = seen and d <= RIBBON_R_M
        r = joint_ribbon_mesh(j, 0.0022 if fine else 0.007,
                              0.00075 if fine else 0.0022,
                              "%sJoint_%05d" % (PFX, j.idx), seed)
        if r is None:
            continue
        me, (cx, cy) = r
        if me is None:
            continue
        _slots(me, ["flag_blast", "joint", "overband", "asphalt"])
        ob = bpy.data.objects.new(me.name, me)
        ob.location = (cx, cy, 0.0)
        coll.objects.link(ob)
        jobjs.append(ob)

    # ---- 5. the reinstatements ---------------------------------------------
    tobjs = []
    for t in TRENCHES:
        for ob in trench_meshes(t, coll, 0.0013, (ax, ay), seed,
                                seen=lambda i, j: in_frame_cell(i, j)):
            _slots(ob.data, ["flag_blast", "joint", "overband", "asphalt"])
            tobjs.append(ob)

    # ---- 6. the colonists ---------------------------------------------------
    wobjs = []
    n_weed = 0
    if weeds:
        wlib = _collection(LIB_COLL_NAME + "_Weeds", link=False)
        if wlib.name not in libcoll.children:
            libcoll.children.link(wlib)
        nsrc = 12 if draft else 52
        wsrc = []
        for k in range(nsrc):
            kind = k % 4
            me = weed_object(kind, int(h01(seed, 1201 + k) * 2e9),
                             "%sW%d_%02d" % (LIBPFX, kind, k),
                             0.65 + 0.85 * h01(seed, 1301 + k))
            if me is None:
                continue
            me.materials.append(materials()["plant"])
            ob = bpy.data.objects.new(me.name, me)
            ob.hide_render = True
            wlib.objects.link(ob)
            wsrc.append(ob)
        pts = []
        for j in joints:
            if not j.weeded:
                continue
            L = j.length
            n = max(1, int(L / (0.16 + 0.5 * h01(j.seed, 41))))
            for k in range(n):
                t = (k + 0.35 + 0.3 * h01(j.seed, 61 + k)) / n
                px = j.p0[0] + (j.p1[0] - j.p0[0]) * t
                py = j.p0[1] + (j.p1[1] - j.p0[1]) * t
                pz = float(joint_bed_z(j, t)) + 0.0015
                d = math.hypot(px - ax, py - ay)
                if d <= WEED_EXPLICIT_R_M:
                    kind = (j.species + k) & 3
                    me = weed_object(kind, int(h01(j.seed, 71 + k) * 2e9),
                                     "%sWeed_%05d_%d" % (PFX, j.idx, k),
                                     0.7 + 0.8 * h01(j.seed, 81 + k))
                    if me is None:
                        continue
                    me.materials.append(materials()["plant"])
                    ob = bpy.data.objects.new(me.name, me)
                    ob.location = (px, py, pz)
                    ob.rotation_euler = (0.0, 0.0,
                                         h01(j.seed, 91 + k) * 2 * math.pi)
                    coll.objects.link(ob)
                    wobjs.append(ob)
                else:
                    pts.append((px, py, pz))
                n_weed += 1
        if pts and wsrc:
            ob = _points_object("%sWeedField" % PFX, pts, coll)
            ng = _pick_instancer(ob.name + "_GN", wlib, len(wsrc), seed + 7717,
                                 flip=False, spin=True)
            md = ob.modifiers.new("colonists", "NODES")
            md.node_group = ng
            ob["instances"] = len(pts)
            ob["library_sources"] = len(wsrc)
            inst_objs.append(ob)

    # ---- 6b. the grit the rain washed out of the joints ---------------------
    gobjs = []
    n_grit = 0
    glib = _collection(LIB_COLL_NAME + "_Grit", link=False)
    if glib.name not in libcoll.children:
        libcoll.children.link(glib)
    gsrc = []
    for k in range(8 if draft else 28):
        me = grit_grain(int(h01(seed, 2201 + k) * 2e9),
                        0.00055 + 0.0016 * h01(seed, 2301 + k))
        me.materials.append(materials()["joint"])
        ob = bpy.data.objects.new(me.name, me)
        glib.objects.link(ob)
        gsrc.append(ob)
    gpts = []
    for j in joints:
        mid = (0.5 * (j.p0[0] + j.p1[0]), 0.5 * (j.p0[1] + j.p1[1]))
        if math.hypot(mid[0] - ax, mid[1] - ay) > RIBBON_R2_M:
            continue
        L = j.length
        n = int(L * (34.0 if _seen(mid[0], mid[1], 0.4, 0.9) else 9.0))
        for k in range(n):
            t = h01(j.seed, 3001 + k)
            side = 1.0 if h01(j.seed, 3301 + k) > 0.5 else -1.0
            # the fan is one-sided and decays: this is a wash, not a sprinkle
            off = side * (j.width_m * 0.5 + 0.002
                          + 0.075 * h01(j.seed, 3601 + k) ** 2.2)
            px_ = j.p0[0] + (j.p1[0] - j.p0[0]) * t
            py_ = j.p0[1] + (j.p1[1] - j.p0[1]) * t
            if j.axis == "y":
                px_ += off
            else:
                py_ += off
            z, fi = flag_top_z(px_, py_, seed)
            gpts.append((px_, py_, z + 0.0004))
            n_grit += 1
    if gpts and gsrc:
        ob = _points_object("%sGritField" % PFX, gpts, coll)
        ng = _pick_instancer(ob.name + "_GN", glib, len(gsrc), seed + 4421,
                             flip=False, spin=True)
        md = ob.modifiers.new("grit", "NODES")
        md.node_group = ng
        ob["instances"] = len(gpts)
        ob["library_sources"] = len(gsrc)
        inst_objs.append(ob)
        gobjs.append(ob)

    # ---- 7. the bed ---------------------------------------------------------
    bobjs = []
    if bedding:
        bobjs = bedding_sheet(rect, coll, seed, tile=12.0, pitch=0.110,
                              suppress=(ax, ay, RIBBON_R2_M))

    st = dict(
        cells=len(flags), flags_laid=len(laid), flags_explicit=len(objs),
        flags_instanced=n_inst, library_meshes=lib_n, libraries=len(libs),
        library_pitch_mm=round(LIB_PITCH_M * 1000, 2),
        repeat_factor=round(n_inst / max(lib_n, 1), 2),
        joints=len(joints),
        joints_sawn=sum(1 for j in joints if j.kind == "sawn"),
        joints_weeded=sum(1 for j in joints if j.weeded),
        joint_ribbons=len(jobjs), reinstatements=len(tobjs),
        reinstated_cells=sum(1 for f in flags if f.trench),
        colonists=n_weed, colonists_explicit=len(wobjs), grit=n_grit,
        grit_sources=len(gsrc),
        ribbon_strip=bool(ribbon_strip),
        bed_tiles=len(bobjs), sockets=len([r for r in _RESERVE
                                           if r["kind"] == "socket"]),
        near_verts=verts,
        objects=len(objs) + len(inst_objs) + len(jobjs) + len(tobjs)
        + len(wobjs) + len(bobjs),
        seconds=round(time.time() - t0, 1))
    if stats is not None:
        stats.update(st)
    print(">> build: %s" % json.dumps(st))
    return st


# =============================================================================
# 13.  THE TEST SCENE  -- the contract sun, and the manifest's own 1.7 m / 35 mm
# =============================================================================


def apply_contract_sky():
    """Force the Sky Texture onto the CONTRACT's atmosphere.

    Must run after any procedural_world(), including the one inside
    save_clean(): that helper writes `dust_density` (which does not exist in
    this Blender; it is `aerosol_density`) and a sun_rotation that is the
    bearing rather than the contract's SKY_SUN_ROTATION_DEG.
    """
    w = bpy.context.scene.world
    if not (w and w.use_nodes):
        return 0
    n = 0
    for nd in w.node_tree.nodes:
        if nd.type != "TEX_SKY":
            continue
        for attr, val in (("sun_disc", C.SKY_SUN_DISC), ("sun_intensity", 1.0),
                          ("air_density", C.SKY_AIR),
                          ("aerosol_density", C.SKY_AEROSOL),
                          ("ozone_density", C.SKY_OZONE),
                          ("altitude", C.SKY_ALTITUDE),
                          ("sun_elevation", math.radians(C.SUN_ELEV_DEG)),
                          ("sun_rotation", math.radians(C.SKY_SUN_ROTATION_DEG)),
                          ("sun_size", math.radians(C.SUN_ANGULAR_DIAM_DEG))):
            if hasattr(nd, attr):
                setattr(nd, attr, val)
        n += 1
        print(">> sky: air %.2f aerosol %.2f ozone %.2f elev %.3f deg disc %s"
              % (nd.air_density, nd.aerosol_density, nd.ozone_density,
                 math.degrees(nd.sun_elevation), nd.sun_disc))
    return n


def contract_sun(scene):
    import fix_audit_blend as FAB
    FAB.procedural_world()
    apply_contract_sky()
    lt = bpy.data.lights.new(PFX + "Sun", "SUN")
    lt.energy = C.SUN_ENERGY
    lt.color = C.SUN_COLOR
    lt.angle = math.radians(C.SUN_ANGULAR_DIAM_DEG)
    ob = bpy.data.objects.new(PFX + "Sun", lt)
    d = Vector(C.SUN_DIR).normalized()
    ob.rotation_mode = "QUATERNION"
    ob.rotation_quaternion = Vector((0.0, 0.0, 1.0)).rotation_difference(d)
    scene.collection.objects.link(ob)
    print(">> sun: elev %.4f deg  bearing %.4f deg  energy %.3f  shadow ratio "
          "%.4f  -> a 3.0 mm lip throws %.1f mm = %.1f px"
          % (C.SUN_ELEV_DEG, C.SUN_BEARING_DEG, C.SUN_ENERGY, C.SUN_SHADOW_RATIO,
             3.0 * C.SUN_SHADOW_RATIO, 3.0 * C.SUN_SHADOW_RATIO * PX_PER_M / 1000))
    return ob


def camera_pose(target, az_deg=VIEW_AZ_DEG, pitch_deg=CAM_PITCH_DEG,
                lens=LENS_AT_CLOSEST_MM, near_m=NEAREST_CAMERA_M):
    """The lens EXACTLY `near_m` from the paving.

    WHICH DISTANCE 1.7 m IS.  The manifest derives nearest_camera_m as the
    minimum over the whole camera corridor.  This item is a continuous ground
    plane, so the closest point of it is always the one directly under the
    lens, and "1.7 m from the forecourt" therefore means THE CAMERA FLIES AT
    1.7 m.  Solving instead for the bottom edge of the frame would put the lens
    lower than the film ever gets -- a harder test than the specified one,
    which is not the same thing as the specified test.
    """
    vhalf = math.degrees(math.atan(0.5 * SENSOR_MM * RES_Y_4K / RES_X_4K / lens))
    hhalf = math.degrees(math.atan(0.5 * SENSOR_MM / lens))
    bot = pitch_deg + vhalf
    top = pitch_deg - vhalf
    h = near_m
    near_d = h / math.tan(math.radians(bot))
    aim_d = h / math.tan(math.radians(pitch_deg))
    far_d = h / math.tan(math.radians(top))
    a = math.radians(az_deg)
    cam = Vector((target[0] - math.cos(a) * aim_d,
                  target[1] - math.sin(a) * aim_d, h))
    tgt = Vector((target[0], target[1], target[2] if len(target) > 2 else 0.0))
    rel = (az_deg - C.SUN_BEARING_DEG) % 360.0
    print(">> camera: %.0f mm, axis %.1f deg down, azimuth %.1f deg "
          "(%.1f deg off the sun -> raking cross light)"
          % (lens, pitch_deg, az_deg, rel))
    print(">>   height %.4f m (= the manifest's %.3f m).  ground in frame "
          "%.3f .. %.3f m out; frame %.2f x %.2f m at the centre"
          % (h, near_m, near_d, far_d,
             2 * math.hypot(aim_d, h) * math.tan(math.radians(hhalf)),
             far_d - near_d))
    for lbl, dd in (("nadir  (the manifest's 1.700 m)", h),
                    ("frame bottom", math.hypot(near_d, h)),
                    ("frame centre", math.hypot(aim_d, h)),
                    ("frame top", math.hypot(far_d, h))):
        print(">>   px/m at %-34s %6.3f m -> %7.1f px/m  (1 px = %.4f mm)"
              % (lbl, dd, RES_X_4K * lens / SENSOR_MM / dd,
                 1000.0 * SENSOR_MM * dd / (RES_X_4K * lens)))
    return cam, tgt, (near_d, aim_d, far_d, hhalf)


def macro_camera(scene, target, name="CAM_FCP_Macro"):
    cam_p, tgt, _g = camera_pose(target)
    cd = bpy.data.cameras.new(name)
    cd.lens = LENS_AT_CLOSEST_MM
    cd.sensor_width = SENSOR_MM
    cd.clip_start = 0.01
    cd.clip_end = 800.0
    cam = bpy.data.objects.new(name, cd)
    scene.collection.objects.link(cam)
    fwd = (tgt - cam_p).normalized()
    right = fwd.cross(Vector((0.0, 0.0, 1.0)))
    if right.length < 1e-6:
        right = Vector((1.0, 0.0, 0.0))
    right.normalize()
    up = right.cross(fwd).normalized()
    M = Matrix((right, up, -fwd)).transposed().to_4x4()
    cam.matrix_world = Matrix.Translation(cam_p) @ M
    scene.camera = cam
    return cam


def measure_nearest(cam):
    """Distance from the lens to the nearest FCP_ vertex ACTUALLY BUILT.

    A claim about the filmed distance that is not this number is a claim about
    the intent, not the artefact (R2-017).
    """
    deps = bpy.context.evaluated_depsgraph_get()
    cp = np.array(cam.matrix_world.translation)
    best, who = 1e9, ""
    for ob in bpy.context.scene.objects:
        if ob.type != "MESH" or not ob.name.startswith(PFX):
            continue
        oe = ob.evaluated_get(deps)
        me = oe.to_mesh()
        if me is None or not len(me.vertices):
            continue
        co = np.empty(len(me.vertices) * 3, np.float32)
        me.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        M = np.array(ob.matrix_world.to_4x4())
        co = co @ M[:3, :3].T + M[:3, 3]
        d = float(np.linalg.norm(co - cp, axis=1).min())
        if d < best:
            best, who = d, ob.name
        oe.to_mesh_clear()
    print(">> nearest %s vertex to the lens: %.4f m (%s) -- manifest %.3f m"
          % (PFX, best, who, NEAREST_CAMERA_M))
    return best


def choose_test_target(seed=SEED, centre=TEST_CENTRE, span=15.0,
                       search=(15.0, 26.0, -22.0, 22.0)):
    """Pick the patch the macro is shot on, and say why.

    The manifest names four variation axes.  A macro that lands on plain
    concrete proves none of them, and "it is in the code" is not evidence --
    that is exactly R2-017.  So the frame is CHOSEN: score every candidate on
    what falls inside the ground quad the lens ACTUALLY covers at 1.7 m on a
    35 mm lens, not inside a radius that can be satisfied off-camera.
    """
    rect = search or (centre[0] - span, centre[0] + span,
                      centre[1] - span, centre[1] + span)
    flags = flag_layout(rect, seed)
    _index(flags, seed)
    joints = joint_segments(flags, seed)
    _c, _t, (near_d, aim_d, far_d, hhalf) = camera_pose((centre[0], centre[1], 0.0))
    a = math.radians(VIEW_AZ_DEG)
    ux, uy = math.cos(a), math.sin(a)
    px_, py_ = -uy, ux

    def in_frame(cx, cy, x, y):
        """Is (x, y) inside the ground quad of a frame aimed at (cx, cy)?"""
        ox = cx - ux * aim_d
        oy = cy - uy * aim_d
        dx, dy = x - ox, y - oy
        s = dx * ux + dy * uy
        t = dx * px_ + dy * py_
        if s < near_d or s > far_d:
            return False
        return abs(t) <= s * math.tan(math.radians(hhalf))

    cands = []
    for f in flags:
        if f.trench or f.cx < 15.4 or abs(f.cy) < 6.5:
            continue
        n_sawn = n_form = n_weed = n_over = 0
        lip = 0.0
        for j in joints:
            mx = 0.5 * (j.p0[0] + j.p1[0])
            my = 0.5 * (j.p0[1] + j.p1[1])
            if not in_frame(f.cx, f.cy, mx, my):
                continue
            if j.kind == "sawn":
                n_sawn += 1
            else:
                n_form += 1
            n_weed += 1 if j.weeded else 0
            n_over += 1 if j.overband else 0
            lip = max(lip, abs(j.arris_z0 - j.arris_z1))
        fam = set()
        crack = 0
        repl = 0
        for g in flags:
            if not in_frame(f.cx, f.cy, g.cx, g.cy):
                continue
            fam.add(g.fam)
            crack += 1 if g.crack else 0
            repl += 1 if g.repl else 0
        wx = np.array([f.cx]); wy = np.array([f.cy])
        rub = float(np.exp(-((np.hypot(f.cx - 16.6, abs(f.cy) - 7.9) - 1.35)
                             / 0.16) ** 2))
        ghost = 0.0
        for (mx, my, mr, _nf, _fr) in FURNITURE_MARKS:
            if in_frame(f.cx, f.cy, mx, my):
                ghost = max(ghost, 1.0)
        dmp = float(damp_field(wx, wy, seed)[0])
        sc = (2.4 * min(n_sawn, 2) / 2.0 + 1.4 * min(n_form, 3) / 3.0
              + 2.4 * min(n_weed, 2) / 2.0 + 1.6 * min(n_over, 1)
              + 1.5 * min(lip / LIP_TARGET_M, 1.0) + 1.3 * min(len(fam), 3) / 3.0
              + 0.9 * min(crack, 2) / 2.0 + 0.9 * min(repl, 2) / 2.0
              + 0.8 * rub + 0.7 * dmp + 1.0 * min(f.area / 1.4, 1.0)
              + 1.7 * ghost)
        cands.append((sc, f, dict(
            score=round(sc, 3), flag=f.idx, family=FAM_NAME[f.fam],
            xy=[round(f.cx, 3), round(f.cy, 3)],
            flag_m2=round(f.area, 3),
            sawn_joints_in_frame=n_sawn, formed_joints_in_frame=n_form,
            weeded_joints_in_frame=n_weed, overband_in_frame=n_over,
            max_lip_mm=round(lip * 1000, 2), families_in_frame=len(fam),
            cracked_flags=crack, replacement_flags=repl,
            rubber=round(rub, 3), damp=round(dmp, 3),
            furniture_ghost_in_frame=int(ghost))))

    # THE FRAME MUST CONTAIN THE AXES, NOT THE NEIGHBOURHOOD.  A macro shot on
    # plain concrete proves nothing the manifest asked for, so the axes are
    # REQUIREMENTS first and a score second -- scored on what falls inside the
    # ground quad the lens actually covers, never inside a radius that can be
    # satisfied off-camera.
    #
    # WHY "N OF SIX" AND NOT A FIXED SET.  The first version demanded a sawn
    # joint AND a formed joint AND a colonised joint AND a full flag, all at
    # once.  Then the weed rate was corrected from 23.8 % to the manifest's
    # 18 % -- and that conjunction went from four candidates to ONE, which was
    # a flag with a 0.77 mm lip, no reinstatement, no stain and nothing else to
    # look at.  A requirement that collapses when an unrelated number is
    # corrected is not measuring the frame, it is measuring luck.  Counting how
    # many of the six features are present degrades gracefully instead.
    FEATURES = (
        ("sawn joint", lambda w: w["sawn_joints_in_frame"] > 0),
        ("formed joint", lambda w: w["formed_joints_in_frame"] > 0),
        ("colonised joint", lambda w: w["weeded_joints_in_frame"] > 0),
        ("reinstatement overband", lambda w: w["overband_in_frame"] > 0),
        ("furniture ghost stain", lambda w: w["furniture_ghost_in_frame"] > 0),
        ("a lip over 2.0 mm", lambda w: w["max_lip_mm"] >= 2.0),
    )
    for _sc, _f, w in cands:
        w["features"] = [n for (n, t) in FEATURES if t(w)]
        w["n_features"] = len(w["features"])
    best, bsc, why = None, -1.0, {}
    for need in (6, 5, 4, 3, 2, 1, 0):
        ok = [c for c in cands
              if c[2]["n_features"] >= need and (c[2]["flag_m2"] > 1.2 or need < 3)]
        if ok:
            bsc, best, why = max(ok, key=lambda c: c[0])
            why["tier"] = "%d of 6 declared features in frame" % need
            why["candidates_at_tier"] = len(ok)
            if need < 6:
                print(">> macro target: no frame carried more than %d of the 6 "
                      "features; taking the best of %d" % (need, len(ok)))
            break
    print(">> macro target chosen from %d candidates: %s"
          % (len(flags), json.dumps(why)))
    return best, why


def _save(out):
    import fix_audit_blend as FAB
    FAB.save_clean(out)
    apply_contract_sky()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out),
                                relative_remap=False, compress=True)
    left = [i.filepath for i in bpy.data.images if i.source == "FILE"]
    if left:
        raise SystemExit("REFUSING: external images survived the save: %s" % left)
    return out


def build_test_scene(quality="hero", out=None, seed=SEED, field_r=FIELD_R_M):
    scene = bpy.context.scene
    _clear()
    tf, why = choose_test_target(seed)
    target = ((tf.cx, tf.cy, 0.0) if tf is not None
              else (TEST_CENTRE[0], TEST_CENTRE[1], 0.0))
    cam_p, _t, _g = camera_pose(target)
    stats = build(anchor_world=(cam_p.x, cam_p.y, cam_p.z), quality=quality,
                  seed=seed, field_r=field_r)
    stats["macro_target"] = why
    contract_sun(scene)
    cam = macro_camera(scene, target)
    stats["camera_nearest_m"] = round(measure_nearest(cam), 4)
    scene.render.engine = "CYCLES"
    scene.render.resolution_x = RES_X_4K
    scene.render.resolution_y = RES_Y_4K
    scene.render.film_transparent = False
    scene.view_settings.view_transform = C.VIEW_TRANSFORM
    scene.view_settings.look = C.VIEW_LOOK
    scene.view_settings.exposure = C.REFERENCE_EXPOSURE_EXTERIOR
    try:
        scene.cycles.max_bounces = 8
        scene.cycles.diffuse_bounces = 4
        scene.cycles.glossy_bounces = 4
        scene.cycles.transmission_bounces = 4
        scene.cycles.use_adaptive_sampling = True
        scene.cycles.adaptive_threshold = 0.005
        scene.cycles.use_denoising = True
    except Exception as e:
        print("   (cycles settings: %s)" % e)
    if out:
        _save(out)
        stats["blend"] = out
        stats["blend_mb"] = round(os.path.getsize(out) / 1048576.0, 1)
        print(">> saved %s (%.1f MB)" % (out, stats["blend_mb"]))
    return stats


# =============================================================================
# 14.  SELF-MEASUREMENT  -- the things item_gate structurally cannot check
# =============================================================================
def verify(seed=SEED, out=None):
    """Measure the ARTEFACT.  Every number is a physical quantity (R2-017)."""
    rep = {"item": ITEM, "seed": seed}
    flags = flag_layout(seed=seed)
    _index(flags, seed)
    joints = joint_segments(flags, seed)
    laid = [f for f in flags if not f.trench]
    rep["cells"] = len(flags)
    rep["flags_laid"] = len(laid)
    rep["area_m2"] = round(sum(f.area for f in laid), 1)
    rep["mean_flag_m2"] = round(sum(f.area for f in laid) / max(len(laid), 1), 4)
    rep["cut_flags"] = sum(1 for f in laid if f.cut)
    rep["cut_pct"] = round(100.0 * rep["cut_flags"] / max(len(laid), 1), 2)

    # ---- 1. does the built concrete stay inside the declared plane? --------
    tops, lows = [], []
    for f in laid:
        for (ux, uy) in ((-1, -1), (1, -1), (1, 1), (-1, 1), (0, 0)):
            z = _flag_plane_z(f, f.cx + ux * f.w * 0.5, f.cy + uy * f.h * 0.5)
            tops.append(z)
            lows.append(z)
    rep["flag_top_max_mm"] = round(max(tops) * 1000, 3)
    rep["flag_top_min_mm"] = round(min(lows) * 1000, 3)
    rep["ceiling_ok"] = bool(max(tops) <= FLAG_TOP_MAX_M + 1e-9)
    rep["clear_of_MARK_Z_mm"] = round((0.0075 - max(tops)) * 1000, 3)

    # ---- 2. the lip between neighbours, which is what the eye reads --------
    lips = [abs(j.arris_z0 - j.arris_z1) for j in joints]
    if lips:
        lips_s = sorted(lips)
        rep["lip_mm"] = dict(
            p50=round(lips_s[len(lips_s) // 2] * 1000, 3),
            p90=round(lips_s[int(len(lips_s) * 0.9)] * 1000, 3),
            max=round(lips_s[-1] * 1000, 3),
            px_at_1p7m=round(lips_s[int(len(lips_s) * 0.9)] * PX_PER_M, 2),
            shadow_px_p90=round(lips_s[int(len(lips_s) * 0.9)]
                                * C.SUN_SHADOW_RATIO * PX_PER_M, 1))

    # ---- 3. the declared variation axes, COUNTED not claimed ---------------
    jw = [j.width_m for j in joints if j.right >= 0]
    je = [j.width_m for j in joints if j.right < 0]
    rep["axes"] = dict(
        joints=len(joints),
        sawn_joints=sum(1 for j in joints if j.kind == "sawn"),
        sawn_pct=round(100.0 * sum(1 for j in joints if j.kind == "sawn")
                       / max(len(joints), 1), 2),
        weeded_joints=sum(1 for j in joints if j.weeded),
        weeded_pct=round(100.0 * sum(1 for j in joints if j.weeded)
                         / max(len(joints), 1), 2),
        weeded_target_pct=18.0,
        reinstated_cells=sum(1 for f in flags if f.trench),
        reinstated_pct=round(100.0 * sum(1 for f in flags if f.trench)
                             / max(len(flags), 1), 3),
        reinstated_target_pct=2.4,
        overband_joints=sum(1 for j in joints if j.overband),
        families={FAM_NAME[k]: sum(1 for f in laid if f.fam == k)
                  for k in (FAM_BLAST, FAM_HONE, FAM_AGG)},
        cracked_flags=sum(1 for f in laid if f.crack),
        replacement_flags=sum(1 for f in laid if f.repl),
        # field joints and edge strips are different objects, and averaging them
        # together is what produced a "271 mm joint" in the first report
        joint_width_mm=dict(
            min=round(min(jw) * 1000, 2), mean=round(float(np.mean(jw)) * 1000, 2),
            max=round(max(jw) * 1000, 2)) if jw else {},
        edge_strip_mm=dict(
            n=len(je), min=round(min(je) * 1000, 1),
            max=round(max(je) * 1000, 1)) if je else {})

    # ---- 4. does surface_z agree with the contract's datum? ----------------
    rng = np.random.default_rng(7)
    xs = rng.uniform(15.6, 25.4, 900)
    ys = rng.uniform(6.6, 21.4, 900)
    dz = []
    for x, y in zip(xs, ys):
        z, fi = flag_top_z(float(x), float(y), seed)
        if fi >= 0:
            dz.append(z - C.APRON_Z)
    if dz:
        rep["vs_world_ground_z_mm"] = dict(
            n=len(dz), min=round(min(dz) * 1000, 3), max=round(max(dz) * 1000, 3),
            mean=round(float(np.mean(dz)) * 1000, 3))

    # ---- 5. the joint bed, which is what a dependant drops things onto -----
    beds = [float(joint_bed_z(j, 0.5)) - 0.5 * (j.arris_z0 + j.arris_z1)
            for j in joints]
    if beds:
        rep["joint_depth_mm"] = dict(min=round(-max(beds) * 1000, 2),
                                     mean=round(-float(np.mean(beds)) * 1000, 2),
                                     max=round(-min(beds) * 1000, 2))
    rep["sockets"] = [dict(x=r["x"], y=r["y"], r=r["r"])
                      for r in _RESERVE if r.get("shape") == "circle"]
    if out:
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        json.dump(rep, open(out, "w"), indent=1)
    print(">> verify: %s" % json.dumps(rep, indent=1))
    return rep


def dump_interface(out, seed=SEED):
    """Write the interface the three dependants build on, as data.

    `concrete_spall_debris`, `glass_shard_fan_settled` and `forecourt_bollard`
    all need the same three things and none of them can ask for them: WHERE THE
    SURFACE IS, WHERE THE JOINTS ARE, and WHERE THE SOCKETS ARE.  Importing this
    module gives them the exact functions; this file gives them the answers
    without a Blender at all, and it is generated from the same `flag_layout`
    the build calls, so it cannot drift from what was emitted.
    """
    flags = flag_layout(seed=seed)
    _index(flags, seed)
    joints = joint_segments(flags, seed)
    d = dict(
        item=ITEM, seed=seed, generated_by=os.path.basename(__file__),
        frame="WORLD metres; z = 0.000 is C.APRON_Z",
        how_to_use=dict(
            surface_z="the flag top a thing RESTS on; use it, never APRON_Z",
            joint_bed_z="the level a fragment that fell into a joint sits on",
            weeded="True = this module already grew a plant here; do not add one",
            sockets="forecourt_bollard should use these, or call reserve_circle "
                    "BEFORE build() and use its own"),
        constants=dict(
            cell_w=CELL_W, cell_h=CELL_H, setout_x=SETOUT_X, setout_y=SETOUT_Y,
            joint_nom_m=JOINT_NOM_M, flag_t_m=FLAG_T_M, soffit_m=SOFFIT_M,
            flag_top_max_m=FLAG_TOP_MAX_M, flag_top_min_m=FLAG_TOP_MIN_M,
            chamfer_w_m=CHAMFER_W_M, chamfer_sawn_m=CHAMFER_SAWN_M,
            socket_r_m=SOCKET_R_M, socket_floor_m=SOCKET_FLOOR_M,
            collar_top_m=COLLAR_TOP_M, collar_w_m=COLLAR_W_M,
            overband_w_m=OVERBAND_W_M, overband_h_m=OVERBAND_H_M,
            bollard_line_x=BOLLARD_LINE_X,
            forecourt_rect=[X0, X1, Y0, Y1],
            ribbon_half_w=RIBBON_HALF_W, ribbon_saw_m=RIBBON_SAW_M,
            r1_shell=list(R1_SHELL), attrs=list(ATTRS),
            px_per_m_at_1p7m=round(PX_PER_M, 1)),
        sockets=[dict(x=r["x"], y=r["y"], r=r["r"], floor=r["floor"],
                      collar_top=COLLAR_TOP_M, kind=r["kind"])
                 for r in _RESERVE if r.get("shape") == "circle"],
        trenches=[dict(name=t["name"], cells=[list(c) for c in t["cells"]],
                       age=t["age"], sunk=t["sunk"],
                       top_z=round(ASPH_TOP_M - 0.5 * t["sunk"], 5))
                  for t in TRENCHES],
        flags=[dict(i=f.i, j=f.j, x0=round(f.x0, 4), x1=round(f.x1, 4),
                    y0=round(f.y0, 4), y1=round(f.y1, 4),
                    z=round(f.level, 5), fam=FAM_NAME[f.fam],
                    sawn=f.sawn, cut=int(bool(f.cut)), repl=int(bool(f.repl)),
                    crack=int(bool(f.crack)), trench=f.trench)
               for f in flags],
        joints=[dict(p0=[round(j.p0[0], 4), round(j.p0[1], 4)],
                     p1=[round(j.p1[0], 4), round(j.p1[1], 4)],
                     axis=j.axis, kind=j.kind, w=round(j.width_m, 4),
                     zl=round(j.arris_z0, 5), zr=round(j.arris_z1, 5),
                     bed=round(float(joint_bed_z(j, 0.5)), 5),
                     weeded=int(j.weeded), overband=int(j.overband))
                for j in joints])
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    json.dump(d, open(out, "w"))
    print(">> interface: %s  (%d flags, %d joints, %d sockets, %.1f kB)"
          % (out, len(d["flags"]), len(d["joints"]), len(d["sockets"]),
             os.path.getsize(out) / 1024.0))
    return d


def measure_scene():
    """Post-build measurement of what is actually in the blend."""
    deps = bpy.context.evaluated_depsgraph_get()
    tris = 0
    verts = 0
    for ob in bpy.context.scene.objects:
        if ob.type != "MESH" or not ob.name.startswith(PFX):
            continue
        oe = ob.evaluated_get(deps)
        me = oe.to_mesh()
        if me is None:
            continue
        verts += len(me.vertices)
        for p in me.polygons:
            tris += max(len(p.vertices) - 2, 1)
        oe.to_mesh_clear()
    from collections import Counter
    srcs = Counter()
    n = 0
    for inst in deps.object_instances:
        if not inst.is_instance:
            continue
        ob = inst.object
        if ob is None or ob.type != "MESH":
            continue
        n += 1
        srcs[ob.data.name if ob.data else ob.name] += 1
    lib_tris = 0
    for me in bpy.data.meshes:
        if me.name.startswith(LIBPFX):
            for p in me.polygons:
                lib_tris += max(len(p.vertices) - 2, 1)
    out = dict(explicit_tris=tris, explicit_verts=verts,
               realized_instances=n, distinct_sources=len(srcs),
               top_source_share=(round(srcs.most_common(1)[0][1] / n, 4)
                                 if n else None),
               library_tris=lib_tris,
               total_traced_tris=tris + sum(
                   cnt * sum(max(len(p.vertices) - 2, 1)
                             for p in bpy.data.meshes[nm].polygons)
                   for nm, cnt in srcs.items() if nm in bpy.data.meshes))
    print(">> scene: %s" % json.dumps(out))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="test",
                    choices=("test", "build", "verify", "interface"))
    ap.add_argument("--out", default=None)
    ap.add_argument("--quality", default="hero")
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--field-r", type=float, default=FIELD_R_M)
    ap.add_argument("--report", default=None)
    argv = sys.argv
    a = ap.parse_args(argv[argv.index("--") + 1:] if "--" in argv else [])
    if a.mode == "verify":
        verify(a.seed, a.report)
        return
    if a.mode == "interface":
        default_reservations()
        dump_interface(a.out or os.path.join(
            _HERE, "forecourt_paving_bay_interface.json"), a.seed)
        return
    if a.mode == "build":
        st = build(quality=a.quality, seed=a.seed)
    else:
        st = build_test_scene(a.quality, a.out, a.seed, a.field_r)
        st["scene"] = measure_scene()
        st["verify"] = verify(a.seed)
    if a.report:
        os.makedirs(os.path.dirname(os.path.abspath(a.report)), exist_ok=True)
        json.dump(st, open(a.report, "w"), indent=1)


if __name__ == "__main__":
    main()
