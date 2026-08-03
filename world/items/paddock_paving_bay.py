#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
paddock_paving_bay.py — CIRCUIT VITRINE, per-item hero campaign, item
``paddock_paving_bay`` (zone ``paddock``, wave 1, build order 129, HERO).

WHAT THIS IS, IN ONE SENTENCE
=============================
The paddock's cast-in-situ concrete apron built as **real geometry**: every bay
is its own slab with its own screed level, its own curl at the joints, its own
broom strokes, its own chipped arris and its own crack history — bedded on a
sub-base, separated by joints that are modelled slots with walls, sealant and
detritus, never a dark line painted on a flat plane.

THE ARITHMETIC THAT SETS THE DETAIL FLOOR
-----------------------------------------
    manifest: nearest_camera_m = 4.6, lens_at_closest_mm = 35, hero

    px_per_m = (3840 * 35 / 36) / 4.6 = 811.6 px/m   ->   1 px = 1.232 mm

So on the 4K master:

    an 8.0 mm saw kerf                      6.5 px wide
    a 3.0 mm chamfered arris                2.4 px, and at the contract sun
                                            (12.471 deg, shadow ratio 4.5222)
                                            it throws a 13.6 mm = 11 px shadow
    an 11-20 mm broom groove pitch          9-16 px — visible corduroy
    a 1.0 mm groove depth                   casts 4.5 mm = 3.7 px of shadow
    a 7 mm cement/sand matrix cell          5.7 px — the surface's tooth
    a 12 mm bay-to-bay level step           casts 54 mm = 44 px of shadow

Every one of those is geometry in this module.  Nothing in that list is a bump
map, because at a 12.47 deg sun the whole read of a pavement is the shadow its
relief throws, and a bump map throws none.

THE PUBLIC INTERFACE  (this item is a FOUNDATION — 5 items depend on it)
=======================================================================
Dependants named in the manifest: ``weed_joint_colonist`` (40 000 instances,
filmed at 1.7 m), ``moss_patch`` (3 000, 1.7 m), ``paddock_duct_cover`` (140),
``paddock_manhole_cover`` (120), ``paddock_slot_drain`` (80).  None of them can
ask questions, so everything they need is a function here.

--- 1. WHERE THE SURFACE IS -----------------------------------------------

    bay_top_z(x, y)      -> (z, bay_index) for any WORLD point on the apron.
                            This is the level a surveyor's staff reads on the
                            slab: bay datum + curl + screed wave + tilt.  It does
                            NOT include the broom groove (-0.4..-1.6 mm) or the
                            crazing (-0.3..-1.1 mm), because a thing standing on
                            the slab bridges those.  Anything laid ON the paving
                            (a marking, a cover frame, a bottle, a tyre) sits on
                            this.

    C.world_ground_z(x, y) returns APRON_Z = 0.000 exactly over this whole
    region.  THIS MODULE IS THE MESH UNDER THAT NUMBER, and it is not flat: bay
    tops run from BAY_TOP_MIN_M to BAY_TOP_MAX_M against that datum.  A module
    that keeps calling C.world_ground_z is never more than +5.6 mm below the
    concrete nor more than 12.0 mm above it.  A module that calls bay_top_z is
    exact.  Both bounds are MEASURED by ``verify()``, not asserted.

    BAY_TOP_MAX_M = +0.0056 is a HARD CEILING held deliberately below
    build_architecture's MARK_Z = 0.0075, so thermoplastic laid on this slab
    still has 1.9 mm of air under it at the worst bay in the world.

--- 2. THE JOINTS — what weed_joint_colonist and moss_patch need ------------

    joint_segments(bays) -> [Joint, ...]     every joint in the field, each with

        p0, p1        world-frame endpoints of the joint CENTRELINE, z at the
                      arris (i.e. the top of the slot)
        kind          'sawn' | 'formed' | 'isolation'
        width_m       clear width of the slot at the top
        arris_z0/z1   the slab top z at each end (they differ: bays step)
        bed_z         z of the DETRITUS SURFACE inside the slot — the level a
                      seed germinates on.  This is the number a weed's root
                      collar sits at, and it is 6..30 mm below the arris.
        sealed        True where a sealant bead fills the slot
        weeded        True on the 18 % of joints the manifest declares colonised
        moss          True where the joint is damp enough for moss
        left/right    bay indices either side

    A colonist placed at parameter t along the joint should read `bed_z` there
    (``joint_bed_z(joint, t)``) and grow from it.  The slot walls are real
    geometry, so a plant emerging from the slot is occluded by them correctly.

--- 3. LETTING SOMETHING INTO THE SLAB -------------------------------------

    reserve(polygon_world, kind)   registers an exclusion.  Bays are CUT TO THE
                                   POLYGON — not to its bounding box, which over
                                   -cut a world-aligned 0.72 m manhole by 1.9x in
                                   a frame rotated 40 deg — and a SAWN WALL is
                                   built from the cut boundary down to the same
                                   soffit as the outer skirt.  So
                                   paddock_manhole_cover / paddock_duct_cover /
                                   paddock_slot_drain drop into a real pocket
                                   with a real concrete face behind them instead
                                   of z-fighting a slab that is still there, or
                                   sitting over an aperture that shows the
                                   sub-base at a 12.47 deg sun.
                                   MEASURED: a 0.518 m2 request removes 5.25 %
                                   of a 9.546 m2 bay against a true 5.43 %, the
                                   difference being one cell of the graded grid.
                                   Call BEFORE build().

    RECESS_LIP_M = 0.004           how far below the surrounding arris the cover
                                   frame's seating shoulder sits.

--- 4. THE LAYOUT ----------------------------------------------------------

    bay_layout(rect_c, seed) -> [Bay, ...]   deterministic.  Same seed, same
                                             bays, forever — a dependant can
                                             recompute the layout without this
                                             module having emitted anything.

    The apron is laid in STRIPS the width of a paver pass, and that is what makes
    the joint grid legible:  longitudinal joints between strips are FORMED
    (tooled, tie-barred, 10 mm, sealed) and carry the level steps, because a
    strip is poured against a day-old neighbour.  Transverse joints inside a
    strip are SAWN (early-entry, 5 mm kerf) and carry almost no step, because
    they are cut into one continuous pour.  "sawn vs formed" — the manifest's
    first variation axis — is therefore not a coin flip per bay: it is the
    construction sequence, and it reads in the frame as two different families of
    line running at right angles.

    STRIP_W  = (2.85, 3.15, 3.45) m      paver pass widths
    BAY_L    = (2.55, 2.80, 3.05) m      saw spacing inside a strip
    NSTRIP   = 5                         passes in one repeat of the plan
    mean bay area = 3.15 * 2.80 = 8.82 m2, against the manifest's
    49 645 / 5 560 = 8.929 m2 (-1.2 %); MEASURED over a full 5 083-bay paddock
    layout by ``verify()`` at 8.900 m2.

    THE PLAN REPEATS EVERY FIVE PASSES, and the cell lengths are always one of
    the three canonical values rather than a jitter around them.  Both are
    forced by the instanced band: a library bay is dropped into a slot, so a
    2.60 m slab in a 2.72 m slot would leave a 120 mm hole in the apron, and a
    wheel track that stopped at a joint because the bay behind it came from a
    library would be the repeat showing.  Irregularity comes instead from the
    saw crew changing spacing at an obstruction — 13 % of bays, always to
    another canonical value.

--- 5. THE MATERIALS -------------------------------------------------------

    mat_concrete(), mat_sealant(), mat_detritus(), mat_asphalt(), mat_bed()
    all cached by name.  Every one reads ``TexCoord -> Object`` plus the baked
    vertex attributes in ``ATTRS``; ``Geometry -> Position`` appears nowhere in
    this file.  Per-bay decorrelation of the procedurals is done with
    ``Object Info -> Random``, NOT with world position, so a bay 480 m from the
    origin has exactly the precision of a bay at the origin.

    ATTRS = ('pol', 'oil', 'cav', 'arr', 'exp', 'age', 'fin', 'dmp')
    A dependant that emits geometry into these materials MUST write all eight;
    ``bake_attrs`` does it.  ``dmp`` is standing damp and it is what the biofilm
    layer keys off — a mesh that leaves it at 0 will read as a slab that has
    never been rained on.

--- 6. EMITTING -------------------------------------------------------------

    build(anchor=..., quality=...) -> dict
        Emits into collection ``W_Item_PaddockPavingBay``, object prefix
        ``PPB_``.  `anchor` is the LENS: bays near it are built as individual
        unique meshes at a pitch that resolves 2 px at their own distance; bays
        beyond ``EXPLICIT_R_M`` come from a library of unique bay meshes through
        a geometry-nodes instancer.  Library objects are prefixed ``PPBLIB_`` and
        live in a collection that is NOT linked to the scene, so they neither
        render as themselves nor pollute the item gate's edge statistics.

THE SEVEN LAWS, AND WHERE EACH ONE IS DISCHARGED
================================================
 1. procedural, by hand      no image node, no file, no library asset.  Every
                             stone, groove, chip and crack is generated here.
 2. no real brands           this item carries no lettering at all.
 3. car scale                the wheel-track polish lanes are set out on the
                             1.85 m track of the paddock transporters and the
                             2.005 m car width; the aisles clear both.
 4. z = 0 is one plane       the apron datum is C.APRON_Z = 0.000 and every bay
                             level is an offset from it, bounded in § 1.
 5. embed >= 20 mm           this item IS the ground.  Its own sub-base slab
                             runs to -0.340 m (C's SUBSLAB), and the visible bed
                             sits at BED_Z = -0.040 so a joint is never a void.
 6. recentre + TexCoord      every bay mesh is local to its own centre
                             (|P| < 1.8 m); the object matrix carries the 400 m
                             out to the paddock.
 7. chunk along s            a bay is <= 3.55 m; the bed is tiled at 40 m.

Run headless:

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P world/items/paddock_paving_bay.py -- --test-blend

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P world/items/paddock_paving_bay.py -- --test-blend --quality draft
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
import warnings

import bpy
import numpy as np
from mathutils import Matrix, Vector

# The hash below is splitmix64 and its wraparound is THE POINT; numpy 2 reports
# every wrap as a RuntimeWarning, which at 10^8 hashes per build is 400 MB of
# stderr for a defined operation.  Silenced by exact message so a REAL overflow
# somewhere else in this file still shows.
warnings.filterwarnings("ignore", category=RuntimeWarning,
                        message=r".*overflow encountered in scalar.*")

# --------------------------------------------------------------------------- paths
_HERE = os.path.dirname(os.path.abspath(__file__))          # .../world/items
_WORLD = os.path.dirname(_HERE)                             # .../world
_ROOT = os.path.dirname(_WORLD)                             # .../f1-round2
for _p in (_WORLD, _HERE, os.path.join(_ROOT, "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import world_contract as C                                  # noqa: E402
from build_surface import _G as G                           # noqa: E402
#   ^ build_surface's shader DSL, imported rather than copied: a second copy of
#     the project's node idiom is a second place for it to drift, and this
#     module's concrete has to sit beside M_Surf_Asphalt in the same frame.

COLL_NAME = "W_Item_PaddockPavingBay"
LIB_COLL_NAME = "W_Item_PaddockPavingBay_LIB"
PFX = "PPB_"
LIBPFX = "PPBLIB_"
MPFX = "M_PPB_"

ITEM_ID = "paddock_paving_bay"

# ---------------------------------------------------------------- filmed spec
# straight out of docs/item_manifest.json; do not guess what the manifest decided
NEAREST_CAMERA_M = 4.6
LENS_AT_CLOSEST_MM = 35.0
SENSOR_MM = 36.0
RES_X_4K = 3840
PX_PER_M = (RES_X_4K * LENS_AT_CLOSEST_MM / SENSOR_MM) / NEAREST_CAMERA_M   # 811.6
BAY_COUNT_WORLD = 5560
BAY_AREA_WORLD_M2 = 49645.0
BAY_MEAN_AREA_M2 = BAY_AREA_WORLD_M2 / BAY_COUNT_WORLD                      # 8.929

# =============================================================================
# 1.  THE CONSTRUCTION — every dimension is a real one
# =============================================================================
STRIP_W = (2.85, 3.15, 3.45)            # paver pass widths, m
BAY_L = (2.55, 2.80, 3.05)              # transverse saw spacing inside a strip
NSTRIP = 5                              # passes in one repeat of the laying plan
#   mean 3.15 x 2.80 = 8.820 m2  vs the manifest's 8.929 m2 (-1.2 %)
#
# WHY THE LAYING PLAN REPEATS.  A paver lays the same sequence of passes across a
# field, and this module needs it to: the wheel tracks that polish the slab are
# a function of where a bay sits ACROSS the strip, so a repeating plan is what
# lets a bay 40 m from the lens be an instance without its wheel track stopping
# dead at the joint.  Five passes is 15.4 m, which is also a believable aisle
# spacing for a paddock laid out for 16.5 m transporters.

SLAB_T = 0.180                          # nominal slab thickness
BED_Z = -0.040                          # visible sub-base surface in the joints
BED_PITCH = 0.30                        # the bed is only ever seen through a 5-10
                                        # mm slot: at 0.05 m it was 10.3 M verts
                                        # of geometry nobody can resolve, and its
                                        # relief belongs in mat_bed's bump
SKIRT_Z = -0.045                        # bay soffit: BELOW the bed, so no gap
SUBSLAB_Z = -0.340                      # C's SUBSLAB — formation, not modelled here

JOINT_SAWN_W = 0.0080                   # aged early-entry kerf, spalled open
                                        # 8 mm is 6.5 px at 812 px/m: a joint
                                        # has to be the strongest line in the
                                        # frame and at 5 mm it was 4 px of
                                        # nothing
JOINT_FORMED_W = 0.0120                 # tooled construction joint between strips
JOINT_ISOL_W = 0.0180                   # isolation joint at a structure
JOINT_SAWN_DEPTH = 0.045                # saw depth (D/4)

CHAMFER_SAWN_M = 0.0016                 # a saw cut has no chamfer, only the
                                        # micro-spall the blade leaves
CHAMFER_FORMED_R = 0.0060               # tooled quarter-round arris radius
CHAMFER_ISOL_R = 0.0080

# BAY LEVELS.  The manifest: "Bay-to-bay height variation must stay inside
# +/-15 mm - measured max is +14.8 mm today, and the tolerance is 15.5 mm."
# So the level field is CONSTRUCTED to a bounded step and then MEASURED; see
# `bay_levels` and `verify()`.  The ceiling is held below build_architecture's
# MARK_Z = 0.0075 so a marking laid on the slab never z-fights it.
LEVEL_STEP_CAP_M = 0.0148               # the manifest's measured max, held exactly
BAY_TOP_MAX_M = 0.0056
BAY_TOP_MIN_M = -0.0128
CURL_LEN_M = 0.34                       # how far in from a joint the slab curls
CURL_MAX_M = 0.0026

RECESS_LIP_M = 0.004                    # cover frame seating shoulder below arris

# WHEEL TRACKS.  Paddock transporters run a 1.85 m track; the car is 2.005 m wide
# and the aisles are set out to clear it.  Polish is where the rubber is.
TRACK_GAUGE_M = 1.85
TRACK_HALF_W = 0.16
AISLE_STRIP = 2                         # the aisle runs on the boundary between
                                        # pass 1 and pass 2 of each repeat

# THE FIVE VARIATION AXES, verbatim from the manifest, and the rate each is
# realised at.  These are not decoration: `verify()` counts them back out of the
# built layout and the gate report carries the counts.
FRAC_WEED_JOINTS = 0.18
FRAC_REINSTATE = 0.024

ATTRS = ("pol", "oil", "cav", "arr", "exp", "age", "fin", "dmp")

# LOD.  pitch(d) resolves TARGET_PX screen pixels at the distance the bay is
# actually filmed from.  2.0 px is half the 4 px the 5 mm kerf occupies, so the
# kerf is never the finest thing in the mesh.
TARGET_PX = 1.5
PITCH_MIN = 0.0015
PITCH_MAX = 0.034
EXPLICIT_R_M = 16.0                     # beyond this a bay is an instance
FIELD_R_M = 62.0                        # the whole test patch
VERT_BUDGET = 16_000_000                # explicit-field ceiling, so a careless
                                        # anchor cannot make a 40 GB blend
ALONG_CLASSES = 3                       # quantisation of the traffic field for
                                        # the instanced band's buckets
LIB_PITCH = PITCH_MAX                   # interior pitch of a library bay: 34 mm
                                        # is 5.8 px at the 22 m band edge, and a
                                        # bay interior at 22 m is sub-millimetre
                                        # relief.  The ARRIS does not coarsen
                                        # with it — _graded_axis holds the edge
                                        # zone at 6 mm however coarse the middle
                                        # is, so the chamfer and the chips still
                                        # exist on an instanced bay.

SEED = 20260729


# =============================================================================
# 2.  NUMERIC PLUMBING — hashes, noise, worley, all vectorised
# =============================================================================
_HK = (np.uint64(0x9E3779B97F4A7C15), np.uint64(0xC2B2AE3D27D4EB4F),
       np.uint64(0x165667B19E3779F9), np.uint64(0x27D4EB2F165667C5),
       np.uint64(0x85EBCA77C2B2AE63), np.uint64(0xD6E8FEB86659FD93))
_U32 = np.uint64(32)
_U29 = np.uint64(29)
_U31 = np.uint64(31)
_U11 = np.uint64(11)


def _h(*keys):
    """Deterministic 0..1 hash of integer arrays / scalars.  Vectorised.

    splitmix64's finaliser in unsigned arithmetic: it wraps silently instead of
    tripping numpy's signed-overflow warning on every call, and it decorrelates
    the low bits, which a plain multiply-shift does not.  The +2^40 bias makes
    negative lattice coordinates legal — cell (-3, -7) is a real cell.
    """
    n = np.uint64(0)
    for i, k in enumerate(keys):
        a = np.asarray(k)
        if a.dtype.kind == "f":
            a = np.floor(a)
        a = (a.astype(np.int64) + np.int64(1 << 40)).astype(np.uint64)
        n = n + a * _HK[i % 6]
    n = (n ^ (n >> _U29)) * np.uint64(0xBF58476D1CE4E5B9)
    n = (n ^ (n >> _U32)) * np.uint64(0x94D049BB133111EB)
    n = n ^ (n >> _U31)
    return (n >> _U11).astype(np.float64) / float(1 << 53)


def _vn2(x, y, seed):
    """Value noise, C1, on a unit lattice."""
    ix = np.floor(x); iy = np.floor(y)
    fx = x - ix; fy = y - iy
    ux = fx * fx * (3.0 - 2.0 * fx)
    uy = fy * fy * (3.0 - 2.0 * fy)
    a = _h(ix, iy, seed)
    b = _h(ix + 1, iy, seed)
    c = _h(ix, iy + 1, seed)
    d = _h(ix + 1, iy + 1, seed)
    return (a * (1 - ux) + b * ux) * (1 - uy) + (c * (1 - ux) + d * ux) * uy


def _fbm2(x, y, seed, oct=4, lac=2.03, gain=0.5):
    tot = np.zeros_like(np.asarray(x, float))
    amp = 1.0; norm = 0.0; f = 1.0
    for k in range(oct):
        tot = tot + amp * _vn2(x * f, y * f, seed + 131 * k)
        norm += amp
        amp *= gain
        f *= lac
    return tot / norm


def _worley(x, y, seed, jitter=1.0, want_id=False):
    """F1, F2 (and the winning cell's hash) on a unit lattice."""
    ix = np.floor(x); iy = np.floor(y)
    f1 = np.full(np.shape(x), 9.0)
    f2 = np.full(np.shape(x), 9.0)
    cid = np.zeros(np.shape(x))
    for dj in (-1, 0, 1):
        for di in (-1, 0, 1):
            cx = ix + di; cy = iy + dj
            hx = _h(cx, cy, seed)
            hy = _h(cx, cy, seed + 7717)
            px = cx + 0.5 + jitter * (hx - 0.5)
            py = cy + 0.5 + jitter * (hy - 0.5)
            d = np.sqrt((px - x) ** 2 + (py - y) ** 2)
            f2 = np.minimum(f2, np.maximum(f1, d))
            if want_id:
                win = d < f1
                cid = np.where(win, _h(cx, cy, seed + 33331), cid)
            f1 = np.minimum(f1, d)
    return (f1, f2, cid) if want_id else (f1, f2)


def _sstep(e0, e1, x):
    """Smoothstep with array-valued edges (an oil stain's radius is a field)."""
    d = np.asarray(e1, float) - np.asarray(e0, float)
    d = np.where(np.abs(d) < 1e-12, 1e-12, d)
    t = np.clip((np.asarray(x, float) - np.asarray(e0, float)) / d, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def _dist_polyline(X, Y, pts):
    """Min distance from every grid point to a polyline, and the signed side."""
    best = np.full(X.shape, 1e9)
    side = np.zeros(X.shape)
    for i in range(len(pts) - 1):
        ax, ay = pts[i]; bx, by = pts[i + 1]
        dx = bx - ax; dy = by - ay
        L2 = dx * dx + dy * dy
        if L2 < 1e-12:
            continue
        t = np.clip(((X - ax) * dx + (Y - ay) * dy) / L2, 0.0, 1.0)
        px = ax + t * dx; py = ay + t * dy
        d = np.sqrt((X - px) ** 2 + (Y - py) ** 2)
        cr = (X - ax) * dy - (Y - ay) * dx
        upd = d < best
        side = np.where(upd, np.sign(cr), side)
        best = np.where(upd, d, best)
    return best, side


def _srgb(hexstr):
    h = hexstr.lstrip("#")
    out = []
    for i in range(3):
        c = int(h[2 * i:2 * i + 2], 16) / 255.0
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (out[0], out[1], out[2], 1.0)


# =============================================================================
# 3.  THE CONDITION FIELDS — evaluated in the CIRCUIT frame, so they cross bays
# =============================================================================
# These are functions of position on the apron, not of the bay, because a wheel
# track, an oil spill and a damp shadow do not stop at a joint.  They are
# evaluated per VERTEX in float64 numpy at build time and BAKED, so the shader
# never has to know where in the world it is.

_PERIOD_CACHE = {}


def strip_period(seed=SEED):
    """-> (widths, cumulative, total, aisle_offset) of one repeat of the plan."""
    got = _PERIOD_CACHE.get(seed)
    if got:
        return got
    ws = [STRIP_W[int(_h(k, seed + 5) * len(STRIP_W)) % len(STRIP_W)]
          for k in range(NSTRIP)]
    cum = [0.0]
    for w in ws:
        cum.append(cum[-1] + w)
    got = (ws, cum, cum[-1], cum[AISLE_STRIP])
    _PERIOD_CACHE[seed] = got
    return got


def polish_across(cy, seed=SEED):
    """0..1 wheel-track polish as a function of circuit y ALONE.

    A 1.85 m transporter track polishes two 0.28 m bands either side of the
    aisle centreline, and the aisle is set out on the laying plan, so this is
    PERIODIC in the paving repeat.  That periodicity is not cosmetic: it is what
    makes an instanced bay 40 m out legal.  A track that stopped at a joint
    because the bay behind it came from a library would be the same class of
    defect as one tree spammed a hundred times — the repeat showing.
    """
    _ws, _cum, T, aisle = strip_period(seed)
    b = np.asarray(cy, float)
    dy = np.mod(b - aisle, T)
    out = np.zeros_like(dy)
    for s in (-0.5, 0.5):
        d = np.abs(np.mod(dy - s * TRACK_GAUGE_M + T * 0.5, T) - T * 0.5)
        out = np.maximum(out, 1.0 - _sstep(TRACK_HALF_W, TRACK_HALF_W + 0.15, d))
    return out


def polish_along(cx, cy, seed=SEED):
    """How hard THIS part of the aisle is driven.  Evaluated once per bay, at the
    bay centre, so it is constant inside a bay and therefore instanceable."""
    _ws, _cum, T, _a = strip_period(seed)
    a = np.asarray(cx, float)
    k = np.floor(np.asarray(cy, float) / T)
    use = 0.30 + 0.70 * _h(k, seed + 909)
    along = 0.45 + 0.55 * _fbm2(a / 23.0, k * 11.3, seed + 77, oct=3)
    return np.clip(use * along * 1.35, 0.0, 1.0)


def polish_field(cx, cy, seed=SEED):
    """The full field, for a caller that just wants the number at a point."""
    return np.clip(polish_across(cy, seed) * polish_along(cx, cy, seed), 0, 1)


def oil_field(cx, cy, seed=SEED):
    """0..1 absorbed oil / diesel, in clusters where the transporters stand."""
    a = np.asarray(cx, float); b = np.asarray(cy, float)
    # A SPILL IS NOT A DISC.  The first render came back with three perfect dark
    # circles on the apron, which is what an unwarped radial falloff always
    # gives.  The sample point is warped by two octaves at 0.9 and 3.1 c/m
    # BEFORE the distance is taken, so the outline is lobed and runs where the
    # slab falls, and the core is only ever a partial darkening.
    wx = a + 0.42 * (_fbm2(a * 0.9, b * 0.9, seed + 521, oct=4) - 0.5) * 2.0 \
        + 0.13 * (_fbm2(a * 3.1, b * 3.1, seed + 523, oct=3) - 0.5) * 2.0
    wy = b + 0.42 * (_fbm2(a * 0.9 + 31.0, b * 0.9, seed + 525, oct=4) - 0.5) * 2.0 \
        + 0.13 * (_fbm2(a * 3.1 + 17.0, b * 3.1, seed + 527, oct=3) - 0.5) * 2.0
    f1, _f2, cid = _worley(wx / 9.0, wy / 9.0, seed + 313, jitter=1.0,
                           want_id=True)
    live = (cid < 0.24).astype(np.float64)
    r = f1 * 9.0                                     # metres from the centre
    rad = 0.28 + 2.05 * np.clip(cid / 0.24, 0, 1)    # 0.28 .. 2.33 m
    core = (1.0 - _sstep(rad * 0.45, rad * 1.02, r)) * 0.80
    halo = (1.0 - _sstep(rad * 0.9, rad * 2.6, r)) * 0.26
    return np.clip(live * (core + halo), 0.0, 1.0)


def oil_local(X, Y, seed, amount):
    """A SELF-CONTAINED stain inside one bay, for the instanced band.

    KNOWN LIMIT, stated rather than hidden: a spill in the instanced band beyond
    EXPLICIT_R_M does not cross a joint, because the bay it is baked into does
    not know its neighbour.  A real spill sometimes does.  At 30 m a joint is
    0.6 px wide, so the tell is the stain's edge, not the joint; the explicit
    near field uses the continuous `oil_field` and has no such limit.
    """
    if amount <= 0.005:
        return np.zeros(X.shape)
    n = 1 + int(_h(seed, 3) * 2.9)
    out = np.zeros(X.shape)
    for i in range(n):
        ox = (_h(seed, 11 + i) - 0.5) * 1.4
        oy = (_h(seed, 21 + i) - 0.5) * 1.4
        rad = 0.22 + 1.20 * _h(seed, 31 + i)
        wx = X + 0.36 * rad * (_fbm2(X * 1.4 + seed % 37, Y * 1.4,
                                     seed + 541 + i, oct=4) - 0.5) * 2.0
        wy = Y + 0.36 * rad * (_fbm2(X * 1.4, Y * 1.4 + seed % 53,
                                     seed + 561 + i, oct=4) - 0.5) * 2.0
        r = np.sqrt((wx - ox) ** 2 + (wy - oy) ** 2)
        core = (1.0 - _sstep(rad * 0.45, rad * 1.02, r)) * 0.80
        out = np.maximum(out, core
                         + (1.0 - _sstep(rad * 0.9, rad * 2.6, r)) * 0.26)
    return np.clip(out * amount, 0.0, 1.0)


def damp_field(cx, cy, seed=SEED):
    """0..1 slow-drying damp: hollows, shaded strips, the lee of a building."""
    a = np.asarray(cx, float); b = np.asarray(cy, float)
    return np.clip(_fbm2(a / 7.5, b / 7.5, seed + 611, oct=4) * 1.3 - 0.28, 0, 1)


# =============================================================================
# 4.  THE LAYOUT
# =============================================================================
class Bay:
    """One cast bay.  Everything about it is decided here and nowhere else."""
    __slots__ = ("idx", "si", "bi", "x0", "x1", "y0", "y1", "cx", "cy",
                 "w", "h", "level", "seed", "fin", "age", "curl", "tx", "ty",
                 "dish", "broom_ang", "groove_p", "groove_d", "pass_w",
                 "craze", "crack", "reinst", "trowel", "popout",
                 "edge_kind", "polish", "oil", "n_verts", "mesh_name",
                 "sclass", "pa", "damp", "synth", "dy0")

    def __init__(self, **kw):
        for k in self.__slots__:
            setattr(self, k, kw.get(k))

    @property
    def area(self):
        return self.w * self.h

    def world_centre(self):
        wx, wy = C.circuit_to_world(self.cx, self.cy)
        return float(wx), float(wy)

    def __repr__(self):
        return ("<Bay %d strip %d  %.3f x %.3f m  level %+.1f mm  %s>"
                % (self.idx, self.si, self.w, self.h, self.level * 1000,
                   "reinstated" if self.reinst else "concrete"))


def _strip_plan(c0, c1, seed):
    """Paver passes across the apron, as a REPEATING plan anchored at cy = 0.

    Anchoring matters: two callers asking for overlapping rectangles must get the
    same strips, or a dependant's joint list and this module's mesh disagree by
    half a bay.
    """
    ws, cum, T, _a = strip_period(seed)
    k0 = int(math.floor(c0 / T)) - 1
    out = []
    y = k0 * T
    si = k0 * NSTRIP
    while y < c1:
        for m in range(NSTRIP):
            w = ws[m]
            if y + w > c0 and y < c1:
                out.append((y, y + w, si))
            y += w
            si += 1
    return out


X_ANCHOR = -620.0       # the setting-out peg the whole apron is walked from


def _bay_plan(d0, d1, si, seed):
    """Transverse saw spacing inside one strip.

    Constant per strip to within a tape length, because that is how a saw crew
    sets out: the spacing is chosen once for the pass and then walked.  Walked
    FROM A FIXED PEG at X_ANCHOR, not from the caller's rectangle — two callers
    asking for overlapping windows must get the same bays, or a dependant's
    joint list and this module's mesh disagree by half a bay.  The apron's
    circuit-x extents are -480 .. +130, so the peg is outside all of them.
    """
    base = BAY_L[int(_h(si, seed + 9) * len(BAY_L)) % len(BAY_L)]
    out = []
    t = X_ANCHOR
    j = 0
    while t < d1 and j < 40000:
        # THE CELL LENGTH IS ALWAYS ONE OF THE THREE CANONICAL VALUES, never a
        # continuous jitter around them.  A 4 % jitter looked like more variety
        # and is in fact a defect: a library bay is instanced into a slot, and a
        # 2.60 m slab dropped into a 2.72 m slot leaves a 120 mm hole in the
        # apron.  Irregularity instead comes from the crew adjusting the setting
        # out at an obstruction, which changes the spacing to ANOTHER canonical
        # value — 13 % of bays — so every footprint stays exactly instanceable.
        L = base
        if _h(si, j, seed + 15) < 0.13:
            L = BAY_L[int(_h(si, j, seed + 13) * len(BAY_L)) % len(BAY_L)]
        if t >= d0 and t + L <= d1:
            out.append((t, t + L, j))
        t += L
        j += 1
    return out


def bay_levels(bays, seed=SEED, cap=LEVEL_STEP_CAP_M):
    """Assign every bay its screed level, bounded so no edge-adjacent pair steps
    by more than `cap`.

    HOW A SLAB ACTUALLY GETS ITS LEVELS, which is why this is not iid noise:
      * along a strip the paver runs on rails, so the level drifts smoothly —
        neighbouring bays inside a strip are within about a millimetre;
      * across a strip the new pour meets a day-old edge, so the step lives on
        the LONGITUDINAL joint.  That is why the level steps in the render run
        in lines, the way they do on a real apron;
      * a handful of bays sit over a soft spot in the sub-base and have settled
        as a unit.

    Then it is RELAXED: any adjacent pair over `cap` is pulled together until
    none is.  The manifest's number is a tolerance that was held on site, and a
    site holds it by grinding the ones that were not.
    """
    if not bays:
        return
    idx = {(b.si, b.bi): b for b in bays}
    for b in bays:
        strip_off = (_h(b.si, seed + 21) - 0.5) * 0.0128             # +-6.4 mm
        drift = (_fbm2(b.cx / 17.0, b.si * 5.3, seed + 23, oct=3) - 0.5) * 0.0060
        settle = 0.0
        if _h(b.si, b.bi, seed + 29) < 0.045:                        # soft spot
            settle = -0.0035 - 0.0055 * _h(b.si, b.bi, seed + 31)
        micro = (_h(b.si, b.bi, seed + 37) - 0.5) * 0.0022
        b.level = strip_off + drift + settle + micro - 0.0022
    # --- relax until no edge-adjacent step exceeds the cap ------------------
    for _ in range(24):
        worst = 0.0
        for b in bays:
            for key in ((b.si, b.bi + 1), (b.si + 1, b.bi)):
                o = idx.get(key)
                if o is None:
                    continue
                d = b.level - o.level
                if abs(d) > cap:
                    worst = max(worst, abs(d))
                    k = (abs(d) - cap) * 0.5 * np.sign(d)
                    b.level -= k
                    o.level += k
        if worst == 0.0:
            break
    # --- clamp to the declared ceiling / floor -----------------------------
    hi = BAY_TOP_MAX_M - CURL_MAX_M
    lo = BAY_TOP_MIN_M + 0.0010
    for b in bays:
        b.level = float(min(max(b.level, lo), hi))


def bay_layout(rect_c, seed=SEED):
    """-> [Bay, ...] for the circuit-frame rectangle (x0, x1, y0, y1).

    DETERMINISTIC.  A dependant that wants to know where the joints are calls
    this with the same rect and seed and gets the same bays, without this module
    having emitted a single triangle.
    """
    x0, x1, y0, y1 = rect_c
    _ws, _cum, T, aisle = strip_period(seed)
    bays = []
    n = 0
    for (sy0, sy1, si) in _strip_plan(y0, y1, seed):
        if sy0 >= y1:
            break
        for (bx0, bx1, bi) in _bay_plan(x0, x1, si, seed):
            # THE SLAB IS SMALLER THAN THE CELL, and the difference IS the joint.
            # The first build laid bays edge to edge, which is a slab with no
            # joints at all — the one thing this item is made of.  The cell
            # bounds stay in x0..x1 (that is what bay_at and joint_segments
            # reason about); w, h are the concrete.
            w = (bx1 - bx0) - JOINT_SAWN_W
            h = (sy1 - sy0) - JOINT_FORMED_W
            if w < 0.5 or h < 0.5:
                continue
            cx = 0.5 * (bx0 + bx1)
            cy = 0.5 * (sy0 + sy1)
            bs = int(_h(si, bi, seed + 101) * 1e6)
            r = lambda k: float(_h(si, bi, seed + k))               # noqa: E731
            # finish: 0 = power-floated and burnished, 1 = heavy yard broom.
            # A paddock apron is a patchwork of both because it was laid by
            # different gangs on different days.  It is a STRIP property with a
            # per-bay wobble, because a gang finishes a pass before it moves on.
            fin = float(np.clip(0.42 + 0.72 * _h(si, seed + 201)
                                + 0.24 * (r(203) - 0.5), 0.30, 1.0))
            pa = float(polish_along(np.array([cx]), np.array([cy]), seed)[0])
            # the SUMMARY is the strongest polish anywhere on the bay, not the
            # value at its centre: a wheel track 0.28 m wide almost never runs
            # through a bay centre, so the centre value reported 0 wheel-track
            # bays over 5 137 bays that visibly have them.
            ys = np.linspace(sy0, sy1, 15)
            pol = float(polish_across(ys, seed).max() * pa)
            oil = float(oil_field(np.array([cx]), np.array([cy]), seed)[0])
            b = Bay(
                idx=n, si=si, bi=bi,
                x0=bx0, x1=bx1, y0=sy0, y1=sy1, cx=cx, cy=cy, w=w, h=h,
                level=0.0, seed=bs,
                fin=fin,
                age=float(0.12 + 0.88 * _h(si, bi, seed + 211)),
                curl=float(0.0006 + (CURL_MAX_M - 0.0006) * r(213) ** 1.4),
                tx=float((r(217) - 0.5) * 0.0016 / max(w, 0.6)),
                ty=float((r(219) - 0.5) * 0.0016 / max(h, 0.6)),
                dish=float((r(223) - 0.45) * 0.0016),
                # THE BROOM DOES NOT ALWAYS RUN THE SAME WAY, and on this
                # circuit that is not a cosmetic choice.  The strips run along
                # circuit x, i.e. world azimuth 40 deg; the contract sun bears
                # -58 deg, so light travels along 122 deg.  A groove broomed
                # ACROSS the strip lies at 130 deg — 8 deg off the light, which
                # casts no shadow at all and is why the first macro came back
                # with a flat slab.  A groove broomed ALONG the strip lies at
                # 40 deg, 82 deg across the light, and a 1.5 mm groove then
                # throws 6.8 mm = 5.5 px of shadow.  Real aprons are a patchwork
                # of both because they are finished pass by pass by different
                # gangs, so it is a per-STRIP choice — and the contrast between
                # a transverse-broomed bay and its longitudinal neighbour is one
                # of the best things in the frame.
                broom_ang=float(math.radians(
                    (0.0 if _h(si, seed + 261) < 0.55 else 90.0)
                    + (r(227) - 0.5) * 28.0)),
                groove_p=float(0.0112 + 0.0092 * r(229)),
                groove_d=float(0.00045 + 0.00095 * r(231)),
                pass_w=float(0.42 + 0.22 * r(233)),
                craze=float(max(0.0, r(237) * 1.7 - 0.28)),
                crack=(r(241) < 0.085),
                reinst=(r(243) < FRAC_REINSTATE),
                trowel=float(0.00016 + 0.00030 * r(247)),
                popout=float(max(0.0, r(251) * 1.6 - 0.32)),
                edge_kind=("formed", "sawn"),   # (long. across-strip, transverse)
                polish=pol, oil=oil, pa=pa,
                damp=float(damp_field(np.array([cx]), np.array([cy]), seed)[0]),
                sclass=si % NSTRIP, dy0=float(np.mod(sy0 - aisle, T)),
                synth=False,
                n_verts=0, mesh_name="",
            )
            bays.append(b)
            n += 1
    bay_levels(bays, seed)
    return bays


# --- the joint model --------------------------------------------------------
class Joint:
    __slots__ = ("p0", "p1", "kind", "width_m", "arris_z0", "arris_z1",
                 "bed_z", "sealed", "weeded", "moss", "left", "right", "idx")

    def __init__(self, **kw):
        for k in self.__slots__:
            setattr(self, k, kw.get(k))

    def length(self):
        return math.hypot(self.p1[0] - self.p0[0], self.p1[1] - self.p0[1])


def joint_bed_z(j, t):
    """z of the detritus surface at parameter t (0..1) along joint `j`.

    THE NUMBER A SEED GERMINATES ON.  weed_joint_colonist and moss_patch place
    their root collar here; the slot walls either side are real geometry, so a
    plant emerging from it is occluded correctly instead of floating on the slab.
    """
    return j.bed_z + (j.arris_z0 * (1 - t) + j.arris_z1 * t) * 0.0


def joint_segments(bays, seed=SEED):
    """Every joint in `bays`, in the WORLD frame.  See the docstring § 2."""
    by = {(b.si, b.bi): b for b in bays}
    out = []
    n = 0
    for b in bays:
        for key, kind in (((b.si, b.bi + 1), "sawn"), ((b.si + 1, b.bi), "formed")):
            o = by.get(key)
            if o is None:
                continue
            if kind == "sawn":                      # transverse, inside a strip
                cx = b.x1
                p0c, p1c = (cx, b.y0), (cx, b.y1)
                # the CLEAR width is exact, because the slabs are inset by half
                # of it each.  The variation a real joint shows at the top is
                # the arris spall, which is 2-26 mm and lives in the bay mesh.
                w = JOINT_SAWN_W
            else:                                   # longitudinal, strip to strip
                cy = b.y1
                p0c, p1c = (b.x0, cy), (b.x1, cy)
                w = JOINT_FORMED_W
            wx0, wy0 = C.circuit_to_world(p0c[0], p0c[1])
            wx1, wy1 = C.circuit_to_world(p1c[0], p1c[1])
            hi = max(b.level, o.level)
            # detritus level: a joint fills from the bottom over years
            fill = 0.009 + 0.021 * _h(b.idx, o.idx, seed + 307)
            weeded = _h(b.idx, o.idx, seed + 311) < FRAC_WEED_JOINTS
            if weeded:
                fill *= 0.62                        # a colonised joint is fuller
            out.append(Joint(
                p0=(float(wx0), float(wy0), hi), p1=(float(wx1), float(wy1), hi),
                kind=kind, width_m=float(w),
                arris_z0=float(b.level), arris_z1=float(o.level),
                bed_z=float(hi - fill),
                sealed=(kind == "formed" and _h(b.idx, seed + 313) > 0.22),
                weeded=bool(weeded),
                moss=bool(_h(b.idx, o.idx, seed + 317) < 0.11),
                left=b.idx, right=o.idx, idx=n))
            n += 1
    return out


# --- reservations (holes for the dependants' hardware) ----------------------
_RESERVED = []


def _poly_mask(X, Y, pts):
    """Point-in-polygon by crossing count.  Vectorised over the whole grid."""
    inside = np.zeros(X.shape, bool)
    n = len(pts)
    for i in range(n):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % n]
        dy = y1 - y0
        if abs(dy) < 1e-12:
            continue
        cond = (y0 > Y) != (y1 > Y)
        xint = x0 + (x1 - x0) * (Y - y0) / dy
        inside ^= (cond & (X < xint))
    return inside


def reserve(polygon_world, kind="cover", depth_m=RECESS_LIP_M):
    """Register an exclusion; bays are CUT to it.  See the docstring § 3.

    THE POLYGON, NOT ITS BOUNDING BOX.  The first version stored only the
    circuit-frame AABB, and the apron is laid in a frame rotated 40 deg from the
    world: a 0.72 m manhole square set out square to the world therefore removed
    1.9x the area it asked for.  Measured, not reasoned about — a 0.518 m2
    request cut 10.3 % of a 9.55 m2 bay instead of 5.4 %.  Every dependant here
    (paddock_manhole_cover, paddock_duct_cover, paddock_slot_drain) sets its
    hardware out square to something, and none of them can ask why the hole is
    bigger than the cover.
    """
    pc = [C.world_to_circuit(q[0], q[1]) for q in polygon_world]
    pts = [(float(a), float(b)) for a, b in pc]
    xs = [q[0] for q in pts]; ys = [q[1] for q in pts]
    _RESERVED.append(dict(kind=kind, depth=depth_m, pts=pts,
                          x0=min(xs), x1=max(xs), y0=min(ys), y1=max(ys)))
    return _RESERVED[-1]


def _reservation_mask(X, Y, bay):
    """Grid mask of everything reserved out of this bay (bay-local coords)."""
    if not _RESERVED:
        return None
    m = np.zeros(X.shape, bool)
    hit = False
    for r in _RESERVED:
        if (r["x1"] - bay.cx < -bay.w or r["x0"] - bay.cx > bay.w
                or r["y1"] - bay.cy < -bay.h or r["y0"] - bay.cy > bay.h):
            continue
        local = [(a - bay.cx, b - bay.cy) for (a, b) in r["pts"]]
        m |= _poly_mask(X, Y, local)
        hit = True
    return m if hit else None


# =============================================================================
# 5.  THE BAY MESH
# =============================================================================
def lod_pitch(dist_m):
    return float(np.clip(TARGET_PX * dist_m / (RES_X_4K * LENS_AT_CLOSEST_MM
                                               / SENSOR_MM),
                         PITCH_MIN, PITCH_MAX))


def _graded_axis(L, pitch, edge_zone, edge_pitch):
    """Vertex coordinates along one axis of a bay, DENSE AT THE ARRIS.

    The arris is where the detail is — the chamfer, the chips, the saw's
    micro-spall — and it is 2-14 mm wide.  A uniform 2.5 mm grid puts one vertex
    across a 3 mm chamfer and the chamfer becomes a bevel-shaped lie.  Grading
    the axis costs a few per cent of the vertex count and buys a resolved edge,
    which is also where the item gate's 10th-percentile edge length comes from.
    """
    if pitch <= edge_pitch * 1.02:
        n = max(2, int(round(L / pitch)))
        return np.linspace(-L * 0.5, L * 0.5, n + 1)
    pos = [0.0]
    t = 0.0
    guard = 0
    while t < L - 1e-9 and guard < 400000:
        guard += 1
        d = min(t, L - t)
        f = _sstep(0.0, edge_zone, d)
        step = edge_pitch + (pitch - edge_pitch) * float(f)
        t = min(t + step, L)
        pos.append(t)
    a = np.array(pos, float)
    a *= L / a[-1]
    return a - L * 0.5


def _broom(X, Y, bay, pol):
    """Yard-broom corduroy, with the things that make it read as a broom.

    A broom finish is not a sine wave.  The gang drags a 0.45-0.65 m head across
    the strip in overlapping passes; each pass sits at its own angle by a degree
    or two, the head wanders as the arm swings, bristles are missing and doubled,
    and the last 100 mm of a stroke fades as the operator lifts.  Every one of
    those is in here, because the regularity is what would give it away.
    """
    a = bay.broom_ang
    ca, sa = math.cos(a), math.sin(a)
    u = X * ca + Y * sa                       # ACROSS the grooves (circuit x)
    v = -X * sa + Y * ca                      # ALONG a stroke (circuit y)
    pw = bay.pass_w
    pid = np.floor(u / pw)                    # the gang advances along x
    pj = u / pw - pid
    # each pass at its own lateral registration and its own degree of skew
    u = (u + (_h(pid, bay.seed + 401) - 0.5) * bay.groove_p * 1.7
         + v * (_h(pid, bay.seed + 403) - 0.5) * 0.030)
    # the head wanders as the arm swings down the stroke
    u = u + 0.0013 * np.sin(v * 6.1 + _h(pid, bay.seed + 405) * 6.283)
    gp = bay.groove_p
    gi = np.floor(u / gp)
    gf = u / gp - gi
    hd = _h(gi, pid, bay.seed + 407)
    depth = bay.groove_d * (0.34 + 1.20 * hd)
    # each pass is leant on differently -- but softly, because the previous
    # amplitude drew the pass grid itself across the bay
    depth = depth * (0.78 + 0.44 * _h(pid, bay.seed + 411))
    # A wet clump of bristles ploughs deeper for 100-300 mm, then lets go; and
    # the head lifts over a high spot and a run of grooves is simply not there.
    # BOTH FIELDS ARE 2-D IN (u, v).  Keying them to the pass index made them
    # constant across a pass, so the render came back with hard-edged rectangles
    # of missing corduroy -- an artefact with a shape, not a broom.
    clump = _fbm2(u * 2.2, v * 4.5, bay.seed + 413, oct=3)
    depth = depth * (0.82 + 0.52 * clump)
    # A SKIP IS RARE.  At sstep(0.26, 0.54) more than half the bay lost its
    # corduroy and the render came back looking like a photocopy with banding.
    # sstep(0.44, 0.76) leaves about a sixth of the area lightened, and the
    # floor of 0.45 means the groove thins rather than vanishing.
    skip = _sstep(0.44, 0.76, _fbm2(u * 3.1, v * 3.1, bay.seed + 415, oct=4))
    depth = depth * (0.45 + 0.55 * skip)
    # a missing bristle leaves a flat, and its neighbour ploughs deeper
    miss = (_h(gi, pid, bay.seed + 409) < 0.075)
    nb = ((_h(gi - 1, pid, bay.seed + 409) < 0.075)
          | (_h(gi + 1, pid, bay.seed + 409) < 0.075))
    depth = np.where(miss, depth * 0.10, np.where(nb, depth * 1.45, depth))
    # the pass fades at the overlap with the one beside it
    fade = 0.62 + 0.38 * _sstep(0.0, 0.20, np.minimum(pj, 1.0 - pj))
    # ... and the stroke dies where the operator lifted, at the strip edge
    half = bay.h * 0.5
    lift = 0.55 + 0.45 * _sstep(0.0, 0.11, half - np.abs(v))
    prof = 0.5 * (1.0 + np.cos(np.pi * np.clip(np.abs(gf - 0.5) * 2.0 / 0.78,
                                               0.0, 1.0)))
    # the wheel tracks grind the ridges off
    return depth * prof * fade * lift * bay.fin * (1.0 - 0.86 * pol)


def _edge_chip(t, seed, prob, amp, cell):
    """1-D spall profile along one arris: extra chamfer width, in metres."""
    i = np.floor(t / cell)
    f = t / cell - i
    on = (_h(i, seed) < prob).astype(np.float64)
    ln = 0.22 + 0.90 * _h(i, seed + 1)
    prof = np.clip(1.0 - ((f - 0.5) / (0.5 * ln)) ** 2, 0.0, 1.0)
    # A SPALL IS A CONCHOIDAL FRACTURE, NOT A DRILLED HOLE.  A symmetric squared
    # bump under a shared exponent gave every chip the same round plan and the
    # render came back with a row of beads down each joint.  The exponent is now
    # per-chip (0.35 = a long feathered flake, 1.6 = a short deep bite) and the
    # edge of the break is roughened at 4 mm, which is 3 px at the filmed
    # distance -- the scale a fracture edge actually breaks at.
    prof = prof ** (0.35 + 1.25 * _h(i, seed + 3))
    prof = prof * (0.62 + 0.38 * _h(np.floor(t / 0.004), seed + 4))
    return on * amp * (0.25 + 0.85 * _h(i, seed + 2)) * prof


def _bay_fields(bay, X, Y, pitch, fine):
    """-> (Z_local, Zlow_local, attrs dict, mat_idx_field)

    Z is the top surface in the bay's OWN frame with z = 0 at the bay datum, so
    every material coordinate is |P| < 2 m and the object matrix carries the
    400 m out to the paddock.  Law 6.
    """
    w, h = bay.w, bay.h
    dxe = w * 0.5 - np.abs(X)
    dye = h * 0.5 - np.abs(Y)
    de = np.minimum(dxe, dye)
    cwx = bay.cx + X                       # circuit-frame position, float64
    cwy = bay.cy + Y

    if bay.synth:
        # A LIBRARY bay does not know where it will be dropped, so its fields
        # must depend only on things that survive instancing: its position
        # ACROSS the strip (which the repeating laying plan makes a constant of
        # its bucket) and its own seed.
        _ws, _cum, T, aisle = strip_period(SEED)
        cy_equiv = (aisle + bay.dy0 + JOINT_FORMED_W * 0.5
                    + (Y + bay.h * 0.5))
        pol = np.clip(polish_across(cy_equiv) * bay.pa, 0.0, 1.0)
        oil = oil_local(X, Y, bay.seed, bay.oil)
        dmp = np.full(X.shape, bay.damp)
    else:
        pol = np.clip(polish_across(cwy) * bay.pa, 0.0, 1.0)
        oil = oil_field(cwx, cwy)
        dmp = damp_field(cwx, cwy)

    # ---- low-frequency shape (this is what bay_top_z reports) -------------
    Zlo = bay.tx * X + bay.ty * Y
    ce = 1.0 - np.clip(de / CURL_LEN_M, 0.0, 1.0)
    Zlo = Zlo + bay.curl * ce ** 2
    cxr = 1.0 - np.clip(dxe / CURL_LEN_M, 0.0, 1.0)
    cyr = 1.0 - np.clip(dye / CURL_LEN_M, 0.0, 1.0)
    Zlo = Zlo + bay.curl * 0.55 * (cxr ** 2) * (cyr ** 2)
    Zlo = Zlo + (_fbm2(X / 0.85, Y / 0.85, bay.seed + 501, oct=3) - 0.5) * 0.0011
    Zlo = Zlo - bay.dish * (1.0 - (2 * X / w) ** 2) * (1.0 - (2 * Y / h) ** 2)

    Z = Zlo.copy()

    # ---- broom / burnish -------------------------------------------------
    if fine:
        Z = Z - _broom(X, Y, bay, pol)
        # power-float burnish rings on the low-fin bays
        r = np.sqrt((X - (bay.seed % 100) / 300.0) ** 2
                    + (Y + (bay.seed % 71) / 260.0) ** 2)
        Z = Z - bay.trowel * (1.0 - bay.fin) * (
            0.5 + 0.5 * np.sin(r * 96.0 + _fbm2(X * 3.1, Y * 3.1,
                                                bay.seed + 503, oct=2) * 9.0))
    # ---- map crazing -----------------------------------------------------
    # TWO CELL SCALES AND A PATCH MASK.  One Voronoi at one size tiles the
    # whole bay in an even honeycomb, which is what the third macro showed and
    # is not what map cracking looks like: it is patchy, it favours the drier
    # end of a bay, and its cells run 40 mm to 260 mm inside one patch.
    cell = 0.055 + 0.070 * _h(bay.seed, 5)
    f1, f2 = _worley(X / cell, Y / cell, bay.seed + 511, jitter=0.95)
    crk = 1.0 - _sstep(0.0, 0.060, f2 - f1)
    g1, g2 = _worley(X / (cell * 2.45), Y / (cell * 2.45), bay.seed + 517,
                     jitter=0.9)
    crk = np.maximum(crk, (1.0 - _sstep(0.0, 0.038, g2 - g1)) * 1.15)
    patch = _sstep(0.30, 0.66, _fbm2(X * 1.15, Y * 1.15, bay.seed + 519, oct=4))
    craze_amt = bay.craze * patch * (0.35 + 0.65 * _fbm2(X * 4.2, Y * 4.2,
                                                        bay.seed + 513, oct=3))
    if fine:
        Z = Z - craze_amt * crk * (0.00055 + 0.00125 * _h(bay.seed, 7))

    # ---- a through crack, on ~1 bay in 12 --------------------------------
    if bay.crack:
        # A SHRINKAGE CRACK IS NOT A ZIGZAG.  13 nodes over 2.8 m is a 220 mm
        # straight between kinks, which at 812 px/m is 180 px of ruled line.
        # 61 nodes and three octaves put the wander where the eye looks for it.
        s0 = _h(bay.seed, 11)
        pts = []
        n = 61
        tt = np.arange(n) / (n - 1.0)
        jj = np.full(n, float(bay.seed % 97))
        wob = ((_fbm2(tt * 3.3, jj, bay.seed + 521, oct=3) - 0.5) * h * 0.50
               + (_fbm2(tt * 13.0, jj, bay.seed + 523, oct=3) - 0.5) * h * 0.11
               + (_fbm2(tt * 47.0, jj, bay.seed + 525, oct=2) - 0.5) * h * 0.028)
        for i in range(n):
            px = -w * 0.5 + tt[i] * w
            py = (s0 - 0.5) * h * 0.62 + wob[i]
            pts.append((px, float(np.clip(py, -h * 0.47, h * 0.47))))
        d, side = _dist_polyline(X, Y, pts)
        hw = 0.0022 + 0.0026 * _h(bay.seed, 13)
        dep = 0.0016 + 0.0026 * _h(bay.seed, 17)
        Z = Z - dep * np.exp(-(d / hw) ** 2)
        Z = Z + side * (0.0004 + 0.0009 * _h(bay.seed, 19)) * \
            np.exp(-(d / 0.028) ** 2)

    # ---- THE MATRIX TOOTH ------------------------------------------------
    # An A/B against an UNDENOISED 2400-sample render settled this: the first
    # macro's concrete was soft not because the denoiser ate it and not because
    # the lens was wrong, but because between the 11 mm broom pitch (9 px) and
    # the 0.4-2.5 m mottle (hundreds of px) the surface carried NO CONTRAST AT
    # ALL, at any scale the eye reads as texture.  A bump map could not fix that:
    # the reinstatement's meshed aggregate in the same frame resolved perfectly,
    # which is the whole argument of the brief in one image.
    #
    # So the cement/sand matrix is meshed: 7 mm and 14 mm fbm at 0.10-0.30 mm.
    # 7 mm is 3.7 samples at the 1.87 mm pitch under the lens — the finest thing
    # that can exist here without aliasing, and 5.7 px on the 4K master.
    if fine:
        # oct=1 and oct=2, NOT 2 and 3.  At the 1.87 mm pitch under the lens a
        # 7 mm first octave is 3.7 samples; its second octave is 1.8, below
        # Nyquist, and the render came back with a directional moire that read
        # as a woven fabric.  An octave you cannot sample is not detail.
        Z = Z - (0.00016 + 0.00013 * _h(bay.seed, 41)) * \
            (_fbm2(X * 143.0, Y * 143.0, bay.seed + 541, oct=1) - 0.5) * 2.0
        Z = Z - (0.00024 + 0.00022 * _h(bay.seed, 43)) * \
            (_fbm2(X * 71.0, Y * 71.0, bay.seed + 543, oct=2) - 0.5) * 2.0
        # float chatter: the pan leaves 35 mm ripples along the pass
        Z = Z - bay.trowel * 1.6 * np.sin(
            (X * 0.94 + Y * 0.34) * 179.0
            + _fbm2(X * 6.0, Y * 6.0, bay.seed + 545, oct=3) * 7.0)
        # ---- blowholes: the poker missed, or the bleed water did not escape --
        bcell = 0.055
        bf1, _bf2, bid = _worley(X / bcell, Y / bcell, bay.seed + 547,
                                 jitter=1.0, want_id=True)
        # 20 % of 55 mm cells put a pit every 12 cm2 and the 1:1 crop came back
        # with measles.  A power-floated top gets far fewer than a formed face:
        # 12 % is about one pit per 25 cm2, which is what a slab that was
        # vibrated properly and floated once actually carries.
        live = (bid < 0.12).astype(np.float64)
        rr = bf1 * bcell
        rad = 0.0021 + 0.0026 * np.clip(bid / 0.12, 0, 1)
        dep = 0.0003 + 0.0010 * np.clip(bid / 0.12, 0, 1)
        Z = Z - live * dep * np.clip(1.0 - (rr / rad) ** 2, 0.0, 1.0)
        Z = Z + live * dep * 0.22 * np.clip(
            1.0 - ((rr - rad * 1.15) / (rad * 0.45)) ** 2, 0.0, 1.0)

    # ---- aggregate pop-outs where the laitance has gone ------------------
    pcell = 0.030
    pf1, _pf2, pid = _worley(X / pcell, Y / pcell, bay.seed + 531,
                             jitter=1.0, want_id=True)
    present = (pid < (0.05 + 0.30 * bay.popout + 0.22 * pol)).astype(np.float64)
    if fine:
        Z = Z + present * (0.00030 + 0.00095 * pid / 0.4) * \
            np.clip(1.0 - (pf1 / 0.40) ** 2, 0.0, 1.0)

    # ---- the arris: chamfer + spall, per edge, per joint family ----------
    drop = np.zeros(X.shape)
    edges = (("x-", dxe, Y, X < 0), ("x+", dxe, Y, X > 0),
             ("y-", dye, X, Y < 0), ("y+", dye, X, Y > 0))
    for k, (tag, d, along, sel) in enumerate(edges):
        transverse = tag.startswith("x")          # x edges are the SAWN joints
        es = bay.seed + 601 + 17 * k
        if transverse:
            base = CHAMFER_SAWN_M * (0.7 + 0.9 * _h(es, 3))
            chip = (_edge_chip(along + 30.0, es, 0.26, 0.0075, 0.032)
                    + _edge_chip(along + 70.0, es + 5, 0.075, 0.020, 0.115))
            cwid = base + chip
            dd = np.where(sel, d, 1e9)
            local = np.maximum(0.0, cwid - dd) * 0.92
        else:
            r = CHAMFER_FORMED_R * (0.82 + 0.36 * _h(es, 3))
            chip = (_edge_chip(along + 11.0, es, 0.19, 0.0095, 0.040)
                    + _edge_chip(along + 53.0, es + 5, 0.055, 0.026, 0.130))
            dd = np.where(sel, d, 1e9)
            fil = np.where(dd < r, r - np.sqrt(np.maximum(0.0, 2 * r * dd
                                                          - dd * dd)), 0.0)
            local = fil + np.maximum(0.0, chip - dd) * 0.80
        # the chip face is a fracture surface, not a plane
        rough = (_fbm2(X * 260.0, Y * 260.0, es + 9, oct=3) - 0.5) * 0.0016
        local = local + np.where(local > 1e-6, rough * np.clip(local / 0.004,
                                                              0, 1), 0.0)
        drop = np.maximum(drop, local)
    Z = Z - drop
    arr = np.clip(1.0 - de / 0.055, 0.0, 1.0)

    # ---- the reinstatement patch (2.4 % of bays) -------------------------
    midx = np.zeros(X.shape, np.int32)
    if bay.reinst:
        rs = bay.seed + 701
        full = _h(rs, 1) < 0.34
        if full:
            px0, px1 = -w * 0.5, w * 0.5
            py0, py1 = -h * 0.5, h * 0.5
        else:
            pw_ = w * (0.34 + 0.42 * _h(rs, 2))
            ph_ = h * (0.55 + 0.45 * _h(rs, 3))
            px0 = -w * 0.5 + (w - pw_) * _h(rs, 4); px1 = px0 + pw_
            py0 = -h * 0.5 + (h - ph_) * _h(rs, 5); py1 = py0 + ph_
        # the saw cut wanders — a trench is cut by hand off a chalk line
        wob = 0.006 * (_fbm2(Y * 5.0, np.full(Y.shape, rs % 53.0),
                             rs + 7, oct=3) - 0.5)
        inx = (X > px0 + wob) & (X < px1 + wob)
        iny = (Y > py0) & (Y < py1)
        m = inx & iny
        if m.any():
            sink = 0.0035 + 0.0060 * _h(rs, 9)
            # A GRADED MIX, not one sieve size.  A 14 mm cold-lay patch is
            # 14 / 10 / 6 / 4 mm stone in a bitumen mortar; a single 13 mm
            # Voronoi gave every chipping the same diameter and the render came
            # back as pebbledash render on a wall.
            ag1, ag2, agid = _worley(X / 0.019, Y / 0.019, rs + 11,
                                     jitter=1.0, want_id=True)
            agg = np.clip(1.0 - (ag1 / 0.42) ** 2, 0.0, 1.0) * \
                (0.00030 + 0.00135 * agid) * (agid < 0.46)
            bg1, _bg2, bgid = _worley(X / 0.0105, Y / 0.0105, rs + 17,
                                      jitter=1.0, want_id=True)
            agg = np.maximum(agg, np.clip(1.0 - (bg1 / 0.45) ** 2, 0.0, 1.0)
                             * (0.00018 + 0.00062 * bgid) * (bgid < 0.42))
            cg1, _cg2, cgid = _worley(X / 0.0058, Y / 0.0058, rs + 19,
                                      jitter=1.0, want_id=True)
            agg = np.maximum(agg, np.clip(1.0 - (cg1 / 0.48) ** 2, 0.0, 1.0)
                             * (0.00008 + 0.00026 * cgid) * (cgid < 0.50))
            rut = 0.0012 * pol * (1.0 - np.clip(np.abs(X - (px0 + px1) * 0.5)
                                                / max(w * 0.25, 0.2), 0, 1))
            az = (-sink + agg - rut
                  + (_fbm2(X * 9.0, Y * 9.0, rs + 13, oct=4) - 0.5) * 0.0022)
            Z = np.where(m, bay.tx * X + bay.ty * Y + az, Z)
            Zlo = np.where(m, bay.tx * X + bay.ty * Y - sink, Zlo)
            midx = np.where(m, 1, midx).astype(np.int32)
            # bitumen overband painted over the sawn edge
            band = (((np.abs(X - (px0 + wob)) < 0.030)
                     | (np.abs(X - (px1 + wob)) < 0.030)) & iny) | \
                   (((np.abs(Y - py0) < 0.030) | (np.abs(Y - py1) < 0.030)) & inx)
            Z = np.where(band, np.maximum(Z, Z + 0.0016), Z)
            midx = np.where(band, 2, midx).astype(np.int32)

    # ---- attributes -------------------------------------------------------
    cav = np.clip((Zlo - Z) / 0.0013, 0.0, 1.0)
    exp_ = np.clip(0.18 * _fbm2(X * 2.3, Y * 2.3, bay.seed + 801, oct=4) * 2.0
                   + 0.72 * pol + 0.55 * arr * bay.age, 0.0, 1.0)
    # damp: standing water finds the dish, the joints and the broom grooves,
    # and biofilm follows it.  Every paddock apron in the world is green-black
    # along the low side of its joints; the first two macros had none.
    dmp_l = np.clip(dmp * 0.55
                    + 0.55 * np.clip(-(Z - Zlo) / 0.0016, 0, 1)
                    + 0.50 * np.clip(1.0 - de / 0.18, 0, 1) ** 2
                    + 0.35 * np.clip(-(Zlo - Zlo.mean()) / 0.0016, 0, 1),
                    0.0, 1.0)
    attrs = {
        "dmp": dmp_l.astype(np.float32),
        "pol": pol.astype(np.float32),
        "oil": np.clip(oil + 0.30 * dmp * oil, 0, 1).astype(np.float32),
        "cav": cav.astype(np.float32),
        "arr": arr.astype(np.float32),
        "exp": exp_.astype(np.float32),
        "age": np.full(X.shape, bay.age, np.float32),
        "fin": np.full(X.shape, bay.fin, np.float32),
    }
    return Z, Zlo, attrs, midx


def bay_mesh(bay, pitch, name=None, fine=True):
    """Build the bay's mesh.  -> bpy Mesh, local to the bay centre."""
    epitch = float(np.clip(pitch * 0.48, 0.0011, 0.0060))
    ezone = float(np.clip(pitch * 20.0, 0.030, 0.075))
    xs = _graded_axis(bay.w, pitch, ezone, epitch)
    ys = _graded_axis(bay.h, pitch, ezone, epitch)
    nx, ny = len(xs), len(ys)
    X, Y = np.meshgrid(xs, ys, indexing="ij")

    Z, Zlo, attrs, midx = _bay_fields(bay, X, Y, pitch, fine)

    co = np.empty((nx * ny, 3), np.float32)
    co[:, 0] = X.ravel(); co[:, 1] = Y.ravel(); co[:, 2] = Z.ravel()

    # --- top quads, with the reserved holes dropped ------------------------
    ii, jj = np.meshgrid(np.arange(nx - 1), np.arange(ny - 1), indexing="ij")
    k = ii * ny + jj
    quads = np.stack([k, k + ny, k + ny + 1, k + 1], axis=-1).reshape(-1, 4)
    fmat = midx[:-1, :-1].reshape(-1).astype(np.int32)

    hole = _reservation_mask(X, Y, bay)
    hole_co = None
    hole_src = None
    hole_quads = None
    if hole is not None:
        hq = (hole[:-1, :-1] | hole[1:, :-1] | hole[1:, 1:] | hole[:-1, 1:])
        keep = ~hq.reshape(-1)
        quads = quads[keep]
        fmat = fmat[keep]
        # A HOLE NEEDS A WALL.  Deleting the quads left an aperture straight
        # through to the sub-base: at a 12.47 deg sun that is a lit slot under
        # every cover in the paddock, and the cover items cannot fix it because
        # the sawn face belongs to the slab, not to the lid.  The wall is built
        # from the boundary of the removed region, oriented so its normal faces
        # into the recess, and it goes down to the same soffit as the outer
        # skirt so a cover seated at RECESS_LIP_M has real concrete behind it.
        e_a, e_b = [], []
        vi = (np.arange(nx)[:, None] * ny + np.arange(ny)[None, :])
        dif = hq[:-1, :] != hq[1:, :]                     # boundary at column i+1
        ii, jj2 = np.nonzero(dif)
        left_removed = hq[ii, jj2]
        va = vi[ii + 1, jj2]; vb = vi[ii + 1, jj2 + 1]
        e_a.append(np.where(left_removed, vb, va))
        e_b.append(np.where(left_removed, va, vb))
        dif = hq[:, :-1] != hq[:, 1:]                     # boundary at row j+1
        ii, jj2 = np.nonzero(dif)
        low_removed = hq[ii, jj2]
        va = vi[ii, jj2 + 1]; vb = vi[ii + 1, jj2 + 1]
        e_a.append(np.where(low_removed, va, vb))
        e_b.append(np.where(low_removed, vb, va))
        ea = np.concatenate(e_a); eb = np.concatenate(e_b)
        if len(ea):
            ne = len(ea)
            top_a = co[ea]; top_b = co[eb]
            bot_a = top_a.copy(); bot_b = top_b.copy()
            bot_a[:, 2] = SKIRT_Z - bay.level
            bot_b[:, 2] = SKIRT_Z - bay.level
            hole_co = np.concatenate([top_a, bot_a, bot_b, top_b], axis=0)
            hole_src = np.concatenate([ea, ea, eb, eb])
            k0 = nx * ny
            hole_quads = np.stack([k0 + np.arange(ne),
                                   k0 + ne + np.arange(ne),
                                   k0 + 2 * ne + np.arange(ne),
                                   k0 + 3 * ne + np.arange(ne)],
                                  axis=-1).astype(np.int32)
            co = np.concatenate([co, hole_co.astype(np.float32)], axis=0)
            quads = np.concatenate([quads, hole_quads], axis=0)
            fmat = np.concatenate([fmat, np.full(ne, 3, np.int32)])

    # --- the skirt: the slab has a THICKNESS, and the joint has walls ------
    ring = []
    _n_hole = 0 if hole_src is None else len(hole_src)
    for i in range(nx):
        ring.append(i * ny + 0)
    for j in range(1, ny):
        ring.append((nx - 1) * ny + j)
    for i in range(nx - 2, -1, -1):
        ring.append(i * ny + (ny - 1))
    for j in range(ny - 2, 0, -1):
        ring.append(0 * ny + j)
    ring = np.array(ring, np.int32)
    nring = len(ring)
    base = co.shape[0]
    skirt_co = co[ring].copy()
    # the formwork face is not smooth: it carries the board marks and the
    # honeycombing a poker missed.  It is 5-40 mm of the frame at a joint.
    sx = skirt_co[:, 0].astype(np.float64)
    sy = skirt_co[:, 1].astype(np.float64)
    skirt_co[:, 2] = SKIRT_Z - bay.level
    co = np.concatenate([co, skirt_co], axis=0)
    # one intermediate ring so the joint wall carries relief
    mid_co = skirt_co.copy()
    mid_co[:, 2] = (-0.011 - 0.004 * _h(np.arange(nring), bay.seed + 901))
    mid_co[:, 0] = sx + (_fbm2(sx * 55.0, sy * 55.0, bay.seed + 903, oct=3)
                         - 0.5) * 0.0022 * np.sign(sx + 1e-9)
    mid_co[:, 1] = sy + (_fbm2(sx * 51.0, sy * 51.0, bay.seed + 905, oct=3)
                         - 0.5) * 0.0022 * np.sign(sy + 1e-9)
    mbase = base + nring
    co = np.concatenate([co, mid_co.astype(np.float32)], axis=0)

    a = ring
    b = np.roll(ring, -1)
    am = mbase + np.arange(nring)
    bm = mbase + np.roll(np.arange(nring), -1)
    ab = base + np.arange(nring)
    bb = base + np.roll(np.arange(nring), -1)
    w1 = np.stack([a, am, bm, b], axis=-1)
    w2 = np.stack([am, ab, bb, bm], axis=-1)
    skirt_quads = np.concatenate([w1, w2], axis=0).astype(np.int32)
    quads = np.concatenate([quads, skirt_quads], axis=0)
    fmat = np.concatenate([fmat, np.full(len(skirt_quads), 3, np.int32)])

    # --- extend the attributes over the skirt rings -----------------------
    for kx in ATTRS:
        v = attrs[kx].ravel()
        parts = [v]
        if hole_src is not None:
            parts.append(v[hole_src])
        parts += [v[ring], v[ring]]
        attrs[kx] = np.concatenate(parts)

    me = bpy.data.meshes.new(name or ("%sBay%06d" % (LIBPFX, bay.idx)))
    nv = co.shape[0]; npo = quads.shape[0]
    me.vertices.add(nv)
    me.vertices.foreach_set("co", np.ascontiguousarray(co, np.float32).ravel())
    me.loops.add(npo * 4)
    me.loops.foreach_set("vertex_index",
                         np.ascontiguousarray(quads, np.int32).ravel())
    me.polygons.add(npo)
    me.polygons.foreach_set("loop_start", np.arange(npo, dtype=np.int32) * 4)
    me.update()
    me.validate(verbose=False)
    me.polygons.foreach_set("material_index",
                            np.ascontiguousarray(fmat, np.int32))
    me.polygons.foreach_set("use_smooth", np.ones(npo, bool))
    for kx in ATTRS:
        at = me.attributes.new(kx, "FLOAT", "POINT")
        at.data.foreach_set("value", np.ascontiguousarray(attrs[kx], np.float32))
    bay.n_verts = nv
    bay.mesh_name = me.name
    return me


def bake_attrs(me, pol=0.0, oil=0.0, cav=0.0, arr=0.0, exp=0.35,
               age=0.5, fin=0.5, dmp=0.5):
    """Write all seven ATTRS onto an arbitrary mesh, for a dependant that emits
    geometry into these materials.  A missing attribute reads as 0 and the
    surface comes back wrong in a way nobody traces back to here."""
    n = len(me.vertices)
    vals = dict(pol=pol, oil=oil, cav=cav, arr=arr, exp=exp, age=age,
                fin=fin, dmp=dmp)
    for k in ATTRS:
        v = vals[k]
        arrv = np.full(n, float(v), np.float32) if np.isscalar(v) else \
            np.asarray(v, np.float32)
        at = me.attributes.get(k) or me.attributes.new(k, "FLOAT", "POINT")
        at.data.foreach_set("value", np.ascontiguousarray(arrv))
    return me


# --- the surface query the dependants use -----------------------------------
_BAY_INDEX = {"bays": [], "grid": None}


def _index_bays(bays):
    _BAY_INDEX["bays"] = bays
    _BAY_INDEX["grid"] = {}
    for b in bays:
        _BAY_INDEX["grid"][(int(math.floor(b.cx / 8.0)),
                            int(math.floor(b.cy / 8.0)))] = None
    _BAY_INDEX["cells"] = {}
    for b in bays:
        key = (int(math.floor(b.cx / 8.0)), int(math.floor(b.cy / 8.0)))
        _BAY_INDEX["cells"].setdefault(key, []).append(b)


def bay_at(x, y):
    """-> the Bay containing WORLD point (x, y), or None."""
    cx, cy = C.world_to_circuit(x, y)
    cx = float(cx); cy = float(cy)
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            key = (int(math.floor(cx / 8.0)) + di, int(math.floor(cy / 8.0)) + dj)
            for b in _BAY_INDEX.get("cells", {}).get(key, ()):
                if b.x0 <= cx <= b.x1 and b.y0 <= cy <= b.y1:
                    return b
    return None


def bay_top_z(x, y):
    """-> (z, bay_index) — the level a staff reads on the slab.  See § 1."""
    b = bay_at(x, y)
    if b is None:
        return C.APRON_Z, -1
    cx, cy = C.world_to_circuit(x, y)
    X = np.array([float(cx) - b.cx]); Y = np.array([float(cy) - b.cy])
    dxe = b.w * 0.5 - np.abs(X); dye = b.h * 0.5 - np.abs(Y)
    de = np.minimum(dxe, dye)
    z = b.tx * X + b.ty * Y
    ce = 1.0 - np.clip(de / CURL_LEN_M, 0.0, 1.0)
    z = z + b.curl * ce ** 2
    cxr = 1.0 - np.clip(dxe / CURL_LEN_M, 0.0, 1.0)
    cyr = 1.0 - np.clip(dye / CURL_LEN_M, 0.0, 1.0)
    z = z + b.curl * 0.55 * (cxr ** 2) * (cyr ** 2)
    z = z + (_fbm2(X / 0.85, Y / 0.85, b.seed + 501, oct=3) - 0.5) * 0.0011
    z = z - b.dish * (1.0 - (2 * X / b.w) ** 2) * (1.0 - (2 * Y / b.h) ** 2)
    return float(z[0]) + b.level, b.idx


# =============================================================================
# 6.  THE JOINT FURNITURE — sealant beads and detritus, as meshes
# =============================================================================
def _ribbon(pts_a, pts_b, name):
    """Two polylines -> a quad strip mesh (local coords)."""
    n = len(pts_a)
    co = np.concatenate([np.asarray(pts_a, np.float32),
                         np.asarray(pts_b, np.float32)], axis=0)
    i = np.arange(n - 1)
    quads = np.stack([i, i + 1, n + i + 1, n + i], axis=-1).astype(np.int32)
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(co))
    me.vertices.foreach_set("co", co.ravel())
    me.loops.add(len(quads) * 4)
    me.loops.foreach_set("vertex_index", quads.ravel())
    me.polygons.add(len(quads))
    me.polygons.foreach_set("loop_start",
                            np.arange(len(quads), dtype=np.int32) * 4)
    me.update(); me.validate(verbose=False)
    return me


def joint_furniture(joints, coll, anchor_c, seed=SEED, max_r=EXPLICIT_R_M):
    """Sealant beads and joint detritus, merged into a few chunk objects.

    THE JOINT IS THE LINE THE EYE FOLLOWS.  A 5 mm kerf at 812 px/m is 4 px
    wide, and what is inside those 4 px decides whether the pavement reads as
    cast or as printed: a sealant bead that has sagged and split, or forty years
    of grit compacted to within 8 mm of the arris with the odd chip of concrete
    sitting on it.
    """
    seal_v, seal_q, seal_n = [], [], 0
    grit_v, grit_q, grit_n = [], [], 0
    ax, ay = anchor_c
    used = 0
    for j in joints:
        p0 = np.array(j.p0[:2]); p1 = np.array(j.p1[:2])
        mid = 0.5 * (p0 + p1)
        cmx, cmy = C.world_to_circuit(mid[0], mid[1])
        if math.hypot(float(cmx) - ax, float(cmy) - ay) > max_r:
            continue
        used += 1
        L = j.length()
        n = max(6, int(L / 0.0035))
        t = np.linspace(0.0, 1.0, n)
        px = p0[0] + (p1[0] - p0[0]) * t
        py = p0[1] + (p1[1] - p0[1]) * t
        dx, dy = (p1 - p0) / max(L, 1e-9)
        nxv, nyv = -dy, dx
        arz = j.arris_z0 + (j.arris_z1 - j.arris_z0) * t
        i = np.arange(n - 1)
        s = t * L
        jj = np.full(n, float(j.idx % 97))

        def _strip(rows, store_v, store_q, base):
            """rows = [(offset_from_centre, z), ...] -> a quad strip."""
            V = [np.stack([px + nxv * o, py + nyv * o, z], axis=-1)
                 for (o, z) in rows]
            store_v.append(np.concatenate(V, axis=0))
            for k in range(len(rows) - 1):
                a0 = base + k * n
                b0 = base + (k + 1) * n
                store_q.append(np.stack([a0 + i, a0 + i + 1,
                                         b0 + i + 1, b0 + i], axis=-1))
            return base + len(rows) * n

        # --- detritus: compacted grit, DOMED, with individual grains ------
        # A flat ribbon 5 mm wide reads as a painted line at 812 px/m.  Three
        # rows give the fill a cross-section: it is packed hard against the slab
        # faces and stands slightly proud in the middle, which is what a joint
        # that has been swept and rained on for years actually looks like.
        hw = j.width_m * 0.5
        gz = j.bed_z + 0.0011 * (_fbm2(s * 42.0, jj, seed + 1101, oct=4) - 0.5) * 2
        gz = gz + 0.0008 * (_h(np.floor(s * 320.0), j.idx, seed + 1103) - 0.5)
        crown = 0.0009 + 0.0011 * _h(np.floor(s * 6.0), j.idx, seed + 1105)
        grit_n = _strip([(-hw * 0.98, gz - 0.0006),
                         (0.0, gz + crown),
                         (hw * 0.98, gz - 0.0006)], grit_v, grit_q, grit_n)
        # --- sealant: only on the formed joints that still have one -------
        if j.sealed:
            # a polysulphide bead sags to a concave meniscus, ages hard, and
            # splits: where it has, the split shows the detritus underneath.
            split = (_h(np.floor(s * 3.1), j.idx, seed + 1107) < 0.13)
            sag = 0.0022 + 0.0016 * _fbm2(s * 2.6, jj, seed + 1109, oct=3)
            edge_z = arz - 0.0006
            mid_z = np.where(split, j.bed_z + 0.0010, arz - sag)
            shw = hw * 0.97
            seal_n = _strip([(-shw, edge_z), (0.0, mid_z), (shw, edge_z)],
                            seal_v, seal_q, seal_n)
    out = []
    for tag, V, Q, mat in (("Grit", grit_v, grit_q, mat_detritus()),
                           ("Seal", seal_v, seal_q, mat_sealant())):
        if not V:
            continue
        co = np.concatenate(V, axis=0)
        qd = np.concatenate(Q, axis=0).astype(np.int32)
        centre = co.mean(axis=0)
        co = co - centre
        me = bpy.data.meshes.new(PFX + tag)
        me.vertices.add(len(co))
        me.vertices.foreach_set("co", np.ascontiguousarray(co, np.float32).ravel())
        me.loops.add(len(qd) * 4)
        me.loops.foreach_set("vertex_index", qd.ravel())
        me.polygons.add(len(qd))
        me.polygons.foreach_set("loop_start",
                                np.arange(len(qd), dtype=np.int32) * 4)
        me.update(); me.validate(verbose=False)
        me.polygons.foreach_set("use_smooth", np.ones(len(qd), bool))
        bake_attrs(me, arr=1.0, cav=1.0, exp=0.2, age=0.8, fin=0.0)
        me.materials.append(mat)
        ob = bpy.data.objects.new(PFX + tag, me)
        ob.location = (float(centre[0]), float(centre[1]), float(centre[2]))
        coll.objects.link(ob)
        out.append(ob)
    print(">> joint furniture: %d joints dressed, %d objects" % (used, len(out)))
    return out


def bed_tiles(rect_c, coll, seed=SEED, tile=40.0):
    """The sub-base seen through the joints.  A joint is never a void (R2 #48)."""
    x0, x1, y0, y1 = rect_c
    objs = []
    n = 0
    xt = np.arange(x0, x1, tile)
    yt = np.arange(y0, y1, tile)
    for tx in xt:
        for ty in yt:
            ex = min(tx + tile, x1); ey = min(ty + tile, y1)
            gx = np.arange(tx, ex + BED_PITCH, BED_PITCH)
            gy = np.arange(ty, ey + BED_PITCH, BED_PITCH)
            X, Y = np.meshgrid(gx, gy, indexing="ij")
            Z = BED_Z + (_fbm2(X * 3.4, Y * 3.4, seed + 1201, oct=4) - 0.5) * 0.0055
            f1, _f2 = _worley(X / 0.020, Y / 0.020, seed + 1203)
            Z = Z + np.clip(1.0 - (f1 / 0.42) ** 2, 0, 1) * 0.0022
            cxm, cym = 0.5 * (tx + ex), 0.5 * (ty + ey)
            wx, wy = C.circuit_to_world(X.ravel(), Y.ravel())
            wx0, wy0 = C.circuit_to_world(cxm, cym)
            # local frame = circuit axes, so TexCoord->Object stays axis-aligned
            co = np.stack([(X - cxm).ravel(), (Y - cym).ravel(), Z.ravel()],
                          axis=-1).astype(np.float32)
            nxq, nyq = X.shape[0], X.shape[1]
            ii, jj = np.meshgrid(np.arange(nxq - 1), np.arange(nyq - 1),
                                 indexing="ij")
            k = ii * nyq + jj
            quads = np.stack([k, k + nyq, k + nyq + 1, k + 1],
                             axis=-1).reshape(-1, 4).astype(np.int32)
            me = bpy.data.meshes.new("%sBed%02d" % (PFX, n))
            me.vertices.add(len(co))
            me.vertices.foreach_set("co", co.ravel())
            me.loops.add(len(quads) * 4)
            me.loops.foreach_set("vertex_index", quads.ravel())
            me.polygons.add(len(quads))
            me.polygons.foreach_set("loop_start",
                                    np.arange(len(quads), dtype=np.int32) * 4)
            me.update(); me.validate(verbose=False)
            me.polygons.foreach_set("use_smooth", np.ones(len(quads), bool))
            bake_attrs(me, arr=0.0, cav=1.0, exp=1.0, age=0.9, fin=0.0)
            me.materials.append(mat_bed())
            ob = bpy.data.objects.new(me.name, me)
            ob.location = (float(wx0), float(wy0), 0.0)
            ob.rotation_euler = (0.0, 0.0, math.radians(C.ROT_DEG))
            coll.objects.link(ob)
            objs.append(ob)
            n += 1
    return objs


# =============================================================================
# 7.  MATERIALS — all TexCoord->Object, all decorrelated by Object Info Random
# =============================================================================
def _mat(name):
    m = bpy.data.materials.get(name)
    if m:
        return m, None
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.node_tree.nodes.clear()
    return m, G(m.node_tree)


def _obj_space(g):
    """Object texture coordinate + a per-object decorrelation offset.

    LAW 6, and the reason the first pass blotched.  ``TexCoord -> Object`` gives
    a coordinate local to the bay, so |P| < 2 m however far the paddock is from
    the origin.  But every bay would then get the SAME noise, and 5 560 identical
    bays is the failure the user named.  ``Object Info -> Random`` is a per-object
    (and per-INSTANCE) scalar, so scaling it into a small offset decorrelates the
    procedurals without ever reintroducing a world position.
    """
    tc = g.n("ShaderNodeTexCoord")
    oi = g.n("ShaderNodeObjectInfo")
    r = oi.outputs["Random"]
    # 12 m, not 60.  The offset only has to decorrelate the LARGEST feature in
    # the graph (a 2.5 m rust plume), and Cycles evaluates the coordinate in
    # float: at 900 cycles/m a 61 m offset lands the sample at 55 000, where the
    # spacing between representable values is 4 um and the 1.1 mm noise starts
    # quantising.  12 m keeps every scaled coordinate under 11 000.
    off = g.comb(g.math("MULTIPLY", r, 12.7),
                 g.math("MULTIPLY", g.math("FRACT", g.math("MULTIPLY", r, 7.13)),
                        9.3),
                 g.math("MULTIPLY", g.math("FRACT", g.math("MULTIPLY", r, 3.71)),
                        6.1))
    return g.vadd(tc.outputs["Object"], off), tc.outputs["Object"], r


def _attr(g, name):
    a = g.n("ShaderNodeAttribute")
    a.attribute_name = name
    return a.outputs["Fac"]


def mat_concrete():
    """Cast-in-situ paddock concrete.

    WHY THIS FUNCTION WAS REWRITTEN, MEASURED RATHER THAN ARGUED
    ------------------------------------------------------------
    Version 5 of this material had twelve layers of history in it and the macro
    still came back reading as one flat cream sheet.  Guessing at amplitudes
    twice did not move it, so the BASE COLOUR ITSELF was rendered, through an
    Emission shader with a Standard view transform, and measured:

        mean 0.577   sd 0.0192   ->  a coefficient of variation of 3.3 %

    Three per cent.  The layers were all there and all doing almost nothing, and
    the reason is structural, not a matter of turning them up:

      * every mask was a noise pushed through a WIDE map-range window
        (0.30 .. 0.74), and a noise is mid-heavy, so every mask sat around 0.4
        with a small spread -- a grey mask, not a stencil;
      * every layer then MIXED TOWARD A COLOUR NEAR THE BASE, so each one pulled
        the result back to the mean that the one before it had just left.
        Twelve such layers do not compound, they AVERAGE.

    So the rules here now, and they are what the numbers demanded:

      1. MASKS ARE STENCILS.  Narrow windows (0.48 .. 0.68) so a mask is mostly
         0 with real 1s in it, and the layer lands somewhere rather than
         everywhere faintly.
      2. LAYERS MIX TOWARD COLOURS THAT ARE ACTUALLY DIFFERENT -- #35322b dirt
         against a #8a8880 cement is a factor of 3 in luminance, not 20 %.
      3. THE PER-BAY TONE IS A GAIN, NOT A MIX, AND IT IS APPLIED LAST.  A mix
         toward another grey can be undone by the next layer; a 0.72 .. 1.30
         multiply on the finished colour cannot, and bay-to-bay tone is the
         single strongest cue that this is 5 560 separate pours rather than one
         poured sheet.

    THE LAYERS, in cycles per metre against the bay's own object coordinate:

      matrix        265, 140   sand and cement, ungated -- the tooth
      aggregate     170        6 mm stone, revealed by `exp`
      grime         0.95, 4.2  what a season of paddock traffic leaves
      run-off       2.6 aniso  rain streaks down the fall of the bay
      pale patches  2.3        laitance that has not been walked off
      weathering    0.55       the metre-scale blotch of an old slab
      cavity dirt   38         everything the wind puts in a broom groove
      biofilm       5.5, 34    algae on the damp side of every joint
      rubber        4, 22      the driven bands, stretched along the track
      oil           16, 60     absorbed, as a multiply, never as a disc
      efflorescence 7          carbonate bloom at the arris
      rust          0.4        a chair left too close to the top
    """
    m, g = _mat(MPFX + "Concrete")
    if g is None:
        return m
    P, Pl, rnd = _obj_space(g)
    pol = _attr(g, "pol"); oil = _attr(g, "oil"); cav = _attr(g, "cav")
    arr = _attr(g, "arr"); exp_ = _attr(g, "exp"); age = _attr(g, "age")
    fin = _attr(g, "fin"); dmp = _attr(g, "dmp")

    def sharp(n, lo, hi):
        return g.mr(n, lo, hi, 0.0, 1.0)

    def mul(a, b):
        return g.math("MULTIPLY", a, b)

    # ---- the fields ------------------------------------------------------
    mo1, _ = g.noise(g.scale(P, 0.55), 1.0, detail=6.0, rough=0.62, dist=0.8)
    mo2, _ = g.noise(g.scale(P, 2.30), 1.0, detail=7.0, rough=0.58)
    rn, _ = g.noise(g.scale(P, 9.00), 1.0, detail=7.0, rough=0.60)
    gr1, _ = g.noise(g.scale(P, 0.95), 1.0, detail=6.0, rough=0.62, dist=0.9)
    gr2, _ = g.noise(g.scale(P, 4.20), 1.0, detail=7.0, rough=0.60)
    gr3, _ = g.noise(g.vmul(g.scale(P, 2.6), (1.0, 0.20, 1.0)), 1.0,
                     detail=7.0, rough=0.62)
    fine1, _ = g.noise(g.scale(P, 265.0), 1.0, detail=7.0, rough=0.62)
    fine2, _ = g.noise(g.scale(P, 140.0), 1.0, detail=7.0, rough=0.58)
    dgr, _ = g.noise(g.scale(P, 38.0), 1.0, detail=6.0, rough=0.62)
    al1, _ = g.noise(g.scale(P, 5.5), 1.0, detail=7.0, rough=0.62)
    al2, _ = g.noise(g.scale(P, 34.0), 1.0, detail=6.0, rough=0.58)
    rub1, _ = g.noise(g.vmul(g.scale(P, 4.0), (0.16, 1.0, 1.0)), 1.0,
                      detail=7.0, rough=0.62)
    rub2, _ = g.noise(g.vmul(g.scale(P, 22.0), (0.30, 1.0, 1.0)), 1.0,
                      detail=6.0, rough=0.55)
    oe1, _ = g.noise(g.scale(P, 16.0), 1.0, detail=7.0, rough=0.62)
    oe2, _ = g.noise(g.scale(P, 60.0), 1.0, detail=6.0, rough=0.58)
    ef, _ = g.noise(g.scale(P, 7.0), 1.0, detail=6.0, rough=0.55)
    ag = g.voro(g.scale(P, 170.0), 1.0, feature="SMOOTH_F1", rand=1.0, smooth=0.12)
    agv = g.mr(ag.outputs["Distance"], 0.0, 0.55, 0.0, 1.0)
    agid = g.voro(g.scale(P, 170.0), 1.0, feature="F1", rand=1.0)
    rv = g.voro(g.scale(P, 0.40), 1.0, feature="F1", rand=1.0)

    # ---- 0. one cement, with a batch HUE (the batch VALUE is the gain) ----
    base = g.mixc(g.mr(rnd, 0.15, 0.85, 0.0, 1.0),
                  g.rgb(*_srgb("#8d8b83")[:3]), g.rgb(*_srgb("#87867f")[:3]))

    # ---- 1. the matrix: sand and cement, on every square centimetre -------
    matrix = g.mixc(sharp(fine1, 0.36, 0.66),
                    g.rgb(*_srgb("#6d6a61")[:3]), g.rgb(*_srgb("#adaa9f")[:3]))
    matrix = g.mixc(mul(sharp(fine2, 0.40, 0.70), 0.55), matrix,
                    g.rgb(*_srgb("#7e7b71")[:3]))
    base = g.mixc(0.46, base, matrix)

    # ---- 2. the aggregate under the skin ---------------------------------
    aggc = g.mixc(agv, g.rgb(*_srgb("#6b665d")[:3]), g.rgb(*_srgb("#c6c0b1")[:3]))
    aggc = g.mixc(g.mr(agid.outputs["Color"], 0.0, 1.0, 0.0, 0.60), aggc,
                  g.rgb(*_srgb("#8d8272")[:3]))
    base = g.mixc(mul(exp_, 0.70), base, aggc)
    base = g.mixc(mul(sharp(agv, 0.20, 0.86), 0.16), base,
                  g.rgb(*_srgb("#787369")[:3]))

    # ---- 3. weathering, at the scale of a whole bay ----------------------
    base = g.mixc(mul(mul(sharp(mo1, 0.48, 0.70), age), 0.62), base,
                  g.rgb(*_srgb("#575249")[:3]))
    base = g.mixc(mul(mul(sharp(mo2, 0.54, 0.74), g.math("SUBTRACT", 1.0, pol)),
                      0.50), base, g.rgb(*_srgb("#bcbaaf")[:3]))
    base = g.mixc(mul(mul(sharp(rn, 0.52, 0.74), age), 0.42), base,
                  g.rgb(*_srgb("#645f55")[:3]))

    # ---- 4. grime and run-off --------------------------------------------
    grime = mul(sharp(gr1, 0.46, 0.68), sharp(gr2, 0.42, 0.68))
    base = g.mixc(mul(grime, 0.92), base, g.rgb(*_srgb("#35322b")[:3]))
    base = g.mixc(mul(sharp(gr3, 0.50, 0.70), 0.55), base,
                  g.rgb(*_srgb("#57534a")[:3]))

    # ---- 5. dirt in every hollow -----------------------------------------
    dirt = mul(cav, sharp(dgr, 0.40, 0.72))
    base = g.mixc(mul(dirt, 0.80), base, g.rgb(*_srgb("#2e2b25")[:3]))

    # ---- 6. biofilm on the damp side of the joints -----------------------
    alg = mul(g.math("POWER", dmp, 1.4),
              mul(sharp(al1, 0.46, 0.70), sharp(al2, 0.38, 0.72)))
    alg = mul(alg, g.math("SUBTRACT", 1.0, mul(pol, 0.85)))
    base = g.mixc(mul(alg, 1.0), base, g.rgb(*_srgb("#38402c")[:3]))
    base = g.mixc(mul(mul(alg, alg), 0.55), base, g.rgb(*_srgb("#1e2418")[:3]))

    # ---- 7. rubber on the driven bands -----------------------------------
    rub = mul(g.math("POWER", pol, 1.4),
              mul(sharp(rub1, 0.44, 0.72), sharp(rub2, 0.36, 0.74)))
    base = g.mixc(mul(rub, 0.85), base, g.rgb(*_srgb("#302e2b")[:3]))

    # ---- 8. oil, as a multiply -------------------------------------------
    oilm = g.mr(g.math("ADD", oil,
                       mul(g.math("SUBTRACT", oe1, 0.5), 0.55)),
                0.10, 0.58, 0.0, 1.0)
    oilm = mul(oilm, sharp(oe2, 0.20, 0.72))
    base = g.vmulc(base, g.mixc(oilm, g.rgb(1.0, 1.0, 1.0),
                                g.rgb(0.24, 0.21, 0.18)))
    halo = mul(g.mr(oil, 0.015, 0.20, 0.0, 1.0),
               g.math("SUBTRACT", 1.0, oilm))
    base = g.vmulc(base, g.mixc(halo, g.rgb(1.0, 1.0, 1.0),
                                g.rgb(0.70, 0.68, 0.65)))

    # ---- 9. efflorescence, 10. rust --------------------------------------
    eff = mul(g.math("POWER", arr, 1.7), sharp(ef, 0.52, 0.80))
    base = g.mixc(mul(eff, 0.40), base, g.rgb(*_srgb("#d6d4ca")[:3]))
    rustm = mul(g.mr(rv.outputs["Distance"], 0.02, 0.30, 1.0, 0.0),
                g.mr(rnd, 0.90, 0.97, 0.0, 1.0))
    base = g.mixc(mul(mul(rustm, sharp(rn, 0.40, 0.78)), 0.60), base,
                  g.rgb(*_srgb("#8a5b33")[:3]))

    # ---- 11. THE PER-BAY GAIN, LAST --------------------------------------
    gainf = g.mr(g.math("ADD", mul(rnd, 0.60), mul(age, 0.40)),
                 0.0, 1.0, 0.70, 1.32)
    base = g.vmulc(base, g.grey(gainf))

    # ---- micro relief ----------------------------------------------------
    grain, _ = g.noise(g.scale(P, 240.0), 1.0, detail=7.0, rough=0.62)
    pin, _ = g.noise(g.scale(P, 900.0), 1.0, detail=4.0, rough=0.60)
    ridge, _ = g.noise(g.vmul(g.scale(P, 30.0), (1.0, 0.07, 1.0)), 1.0,
                       detail=6.0, rough=0.50)
    hgt = g.math("ADD",
                 mul(g.math("SUBTRACT", grain, 0.5), 0.62),
                 g.math("ADD", mul(g.math("SUBTRACT", pin, 0.66), 0.45),
                        mul(g.math("SUBTRACT", ridge, 0.5),
                            mul(0.34, g.math("SUBTRACT", 1.0, fin)))))
    hgt = g.math("ADD", hgt, mul(g.math("SUBTRACT", agv, 0.5), mul(exp_, 0.6)))
    nrm = g.bump(hgt, strength=g.mr(pol, 0.0, 1.0, 1.05, 0.45), distance=0.0024)

    # ---- roughness -------------------------------------------------------
    rg1, _ = g.noise(g.scale(P, 14.0), 1.0, detail=6.0, rough=0.55)
    rg2, _ = g.noise(g.scale(P, 130.0), 1.0, detail=5.0, rough=0.55)
    rgh = g.mixf(sharp(rg1, 0.34, 0.72), 0.58, 0.94)
    rgh = g.mixf(sharp(rg2, 0.36, 0.70), rgh, g.math("ADD", rgh, 0.08))
    rgh = g.mixf(g.math("POWER", pol, 1.2), rgh, 0.36)
    rgh = g.mixf(mul(oilm, 0.92), rgh, 0.24)
    rgh = g.mixf(mul(dirt, 0.7), rgh, 0.95)
    rgh = g.mixf(mul(rub, 0.6), rgh, 0.52)
    rgh = g.mixf(mul(alg, 0.8), rgh, 0.96)
    rgh = g.mixf(g.math("SUBTRACT", 1.0, fin), rgh, mul(rgh, 0.58))

    bsdf = g.n("ShaderNodeBsdfPrincipled")
    g.set(bsdf.inputs["Base Color"], base)
    g.set(bsdf.inputs["Roughness"], rgh)
    g.set(bsdf.inputs["Normal"], nrm)
    if "Metallic" in bsdf.inputs:
        g.set(bsdf.inputs["Metallic"], 0.0)
    if "IOR" in bsdf.inputs:
        g.set(bsdf.inputs["IOR"], 1.486)
    if "Specular IOR Level" in bsdf.inputs:
        g.set(bsdf.inputs["Specular IOR Level"], g.mixf(oilm, 0.38, 0.58))
    out = g.n("ShaderNodeOutputMaterial")
    m.node_tree.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return m


def mat_sealant():
    """Polysulphide joint sealant: satin black-grey, dusty, split with age."""
    m, g = _mat(MPFX + "Sealant")
    if g is None:
        return m
    P, _Pl, rnd = _obj_space(g)
    n1, _ = g.noise(g.scale(P, 90.0), 1.0, detail=6.0, rough=0.60)
    n2, _ = g.noise(g.scale(P, 6.0), 1.0, detail=5.0, rough=0.55)
    crk = g.voro(g.scale(P, 90.0), 1.0, feature="DISTANCE_TO_EDGE", rand=1.0)
    ce = g.mr(crk.outputs["Distance"], 0.0, 0.07, 1.0, 0.0)
    base = g.mixc(g.mr(n2, 0.30, 0.75, 0.0, 1.0),
                  g.rgb(*_srgb("#1f1d1a")[:3]), g.rgb(*_srgb("#2e2b26")[:3]))
    base = g.mixc(g.math("MULTIPLY", ce, 0.75), base,
                  g.rgb(*_srgb("#16140f")[:3]))
    dust = g.mr(n1, 0.35, 0.85, 0.0, 1.0)
    base = g.mixc(g.math("MULTIPLY", dust, 0.30), base,
                  g.rgb(*_srgb("#544f46")[:3]))
    nrm = g.bump(g.math("ADD", g.math("MULTIPLY", n1, 0.45),
                        g.math("MULTIPLY", ce, -0.70)),
                 strength=0.6, distance=0.0010)
    bsdf = g.n("ShaderNodeBsdfPrincipled")
    g.set(bsdf.inputs["Base Color"], base)
    g.set(bsdf.inputs["Roughness"], g.mixf(dust, 0.50, 0.88))
    g.set(bsdf.inputs["Normal"], nrm)
    out = g.n("ShaderNodeOutputMaterial")
    m.node_tree.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return m


def mat_detritus():
    """What years put in a joint: grit, brick dust, tyre crumb, seed, sand."""
    m, g = _mat(MPFX + "Detritus")
    if g is None:
        return m
    P, _Pl, rnd = _obj_space(g)
    gr = g.voro(g.scale(P, 330.0), 1.0, feature="SMOOTH_F1", rand=1.0, smooth=0.10)
    gd = g.mr(gr.outputs["Distance"], 0.0, 0.55, 1.0, 0.0)
    gid = g.voro(g.scale(P, 330.0), 1.0, feature="F1", rand=1.0)
    col, _ = g.noise(g.scale(P, 22.0), 1.0, detail=7.0, rough=0.60)
    base = g.mixc(g.mr(col, 0.25, 0.80, 0.0, 1.0),
                  g.rgb(*_srgb("#282516")[:3]), g.rgb(*_srgb("#3b3527")[:3]))
    base = g.mixc(g.math("MULTIPLY", gd, 0.45), base,
                  g.rgb(*_srgb("#57503f")[:3]))
    base = g.mixc(g.mr(gid.outputs["Color"], 0.0, 1.0, 0.0, 0.40), base,
                  g.rgb(*_srgb("#7d7360")[:3]))
    org, _ = g.noise(g.scale(P, 5.0), 1.0, detail=6.0, rough=0.60)
    base = g.mixc(g.math("MULTIPLY", g.mr(org, 0.55, 0.90, 0.0, 1.0), 0.45),
                  base, g.rgb(*_srgb("#24230f")[:3]))
    nrm = g.bump(g.math("ADD", g.math("MULTIPLY", gd, 1.0),
                        g.math("MULTIPLY", col, 0.45)),
                 strength=1.0, distance=0.0020)
    bsdf = g.n("ShaderNodeBsdfPrincipled")
    g.set(bsdf.inputs["Base Color"], base)
    g.set(bsdf.inputs["Roughness"], g.mixf(gd, 0.96, 0.80))
    g.set(bsdf.inputs["Normal"], nrm)
    out = g.n("ShaderNodeOutputMaterial")
    m.node_tree.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return m


def mat_asphalt():
    """The reinstatement over a service cut: a blacker, coarser mix than the
    racing surface, laid cold and rolled by a wacker plate."""
    m, g = _mat(MPFX + "Reinstatement")
    if g is None:
        return m
    P, _Pl, rnd = _obj_space(g)
    st = g.voro(g.scale(P, 85.0), 1.0, feature="SMOOTH_F1", rand=1.0, smooth=0.10)
    sd = g.mr(st.outputs["Distance"], 0.0, 0.50, 1.0, 0.0)
    sid = g.voro(g.scale(P, 85.0), 1.0, feature="F1", rand=1.0)
    fines, _ = g.noise(g.scale(P, 300.0), 1.0, detail=7.0, rough=0.62)
    base = g.mixc(g.mr(fines, 0.30, 0.80, 0.0, 1.0),
                  g.rgb(*_srgb("#1a1814")[:3]), g.rgb(*_srgb("#26231d")[:3]))
    base = g.mixc(g.math("MULTIPLY", g.math("POWER", sd, 2.6), 0.38), base,
                  g.rgb(*_srgb("#4b463d")[:3]))
    base = g.mixc(g.mr(sid.outputs["Color"], 0.0, 1.0, 0.0, 0.20), base,
                  g.rgb(*_srgb("#2b2822")[:3]))
    ox, _ = g.noise(g.scale(P, 2.2), 1.0, detail=6.0, rough=0.55)
    base = g.mixc(g.math("MULTIPLY", g.mr(ox, 0.48, 0.86, 0.0, 1.0), 0.18),
                  base, g.rgb(*_srgb("#3c3933")[:3]))
    pol = _attr(g, "pol")
    nrm = g.bump(g.math("ADD", g.math("MULTIPLY", sd, 1.0),
                        g.math("MULTIPLY", fines, 0.50)),
                 strength=g.mr(pol, 0.0, 1.0, 1.0, 0.40), distance=0.0026)
    rgh = g.mixf(sd, 0.90, 0.72)
    rgh = g.mixf(g.math("POWER", pol, 1.2), rgh, 0.40)
    bsdf = g.n("ShaderNodeBsdfPrincipled")
    g.set(bsdf.inputs["Base Color"], base)
    g.set(bsdf.inputs["Roughness"], rgh)
    g.set(bsdf.inputs["Normal"], nrm)
    out = g.n("ShaderNodeOutputMaterial")
    m.node_tree.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return m


def mat_overband():
    """The bitumen overband painted over a reinstatement's sawn edge."""
    m, g = _mat(MPFX + "Overband")
    if g is None:
        return m
    P, _Pl, rnd = _obj_space(g)
    n1, _ = g.noise(g.scale(P, 140.0), 1.0, detail=6.0, rough=0.60)
    n2, _ = g.noise(g.scale(P, 8.0), 1.0, detail=5.0, rough=0.50)
    gv = g.voro(g.scale(P, 260.0), 1.0, feature="SMOOTH_F1", rand=1.0, smooth=0.1)
    gd = g.mr(gv.outputs["Distance"], 0.0, 0.55, 1.0, 0.0)
    base = g.mixc(g.mr(n2, 0.30, 0.80, 0.0, 1.0),
                  g.rgb(*_srgb("#1b1917")[:3]), g.rgb(*_srgb("#2c2925")[:3]))
    base = g.mixc(g.math("MULTIPLY", g.math("POWER", gd, 2.4), 0.22), base,
                  g.rgb(*_srgb("#6b6459")[:3]))
    nrm = g.bump(g.math("ADD", g.math("MULTIPLY", gd, 0.85),
                        g.math("MULTIPLY", n1, 0.50)),
                 strength=0.7, distance=0.0012)
    bsdf = g.n("ShaderNodeBsdfPrincipled")
    g.set(bsdf.inputs["Base Color"], base)
    g.set(bsdf.inputs["Roughness"], g.mixf(gd, 0.44, 0.82))
    g.set(bsdf.inputs["Normal"], nrm)
    out = g.n("ShaderNodeOutputMaterial")
    m.node_tree.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return m


def mat_formface():
    """The slab's own edge, seen down a joint: a sawn face on the transverse
    joints, a formed one on the longitudinal.  It is always in shade at a
    12.47 deg sun, so its ALBEDO is what decides whether the joint reads as a
    dark line or as a hole (R2 defect #48)."""
    m, g = _mat(MPFX + "FormFace")
    if g is None:
        return m
    P, _Pl, rnd = _obj_space(g)
    saw, _ = g.noise(g.vmul(g.scale(P, 150.0), (1.0, 1.0, 0.06)), 1.0,
                     detail=6.0, rough=0.60)
    hc = g.voro(g.scale(P, 55.0), 1.0, feature="SMOOTH_F1", rand=1.0, smooth=0.12)
    hd = g.mr(hc.outputs["Distance"], 0.0, 0.26, 1.0, 0.0)
    base = g.mixc(g.mr(saw, 0.30, 0.80, 0.0, 1.0),
                  g.rgb(*_srgb("#8b887f")[:3]), g.rgb(*_srgb("#6d6a62")[:3]))
    base = g.mixc(g.math("MULTIPLY", hd, 0.55), base,
                  g.rgb(*_srgb("#514d45")[:3]))
    dirt, _ = g.noise(g.scale(P, 18.0), 1.0, detail=6.0, rough=0.60)
    base = g.mixc(g.math("MULTIPLY", g.mr(dirt, 0.40, 0.90, 0.0, 1.0), 0.45),
                  base, g.rgb(*_srgb("#413d34")[:3]))
    nrm = g.bump(g.math("ADD", g.math("MULTIPLY", saw, 0.55),
                        g.math("MULTIPLY", hd, -0.85)),
                 strength=0.85, distance=0.0022)
    bsdf = g.n("ShaderNodeBsdfPrincipled")
    g.set(bsdf.inputs["Base Color"], base)
    g.set(bsdf.inputs["Roughness"], g.mixf(hd, 0.88, 0.96))
    g.set(bsdf.inputs["Normal"], nrm)
    out = g.n("ShaderNodeOutputMaterial")
    m.node_tree.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return m


def mat_bed():
    """Type-1 sub-base seen down a joint.  Dark, but never black."""
    m, g = _mat(MPFX + "Bed")
    if g is None:
        return m
    P, _Pl, rnd = _obj_space(g)
    st = g.voro(g.scale(P, 42.0), 1.0, feature="SMOOTH_F1", rand=1.0, smooth=0.10)
    sd = g.mr(st.outputs["Distance"], 0.0, 0.50, 1.0, 0.0)
    sid = g.voro(g.scale(P, 42.0), 1.0, feature="F1", rand=1.0)
    fn, _ = g.noise(g.scale(P, 120.0), 1.0, detail=6.0, rough=0.60)
    base = g.mixc(g.mr(fn, 0.30, 0.80, 0.0, 1.0),
                  g.rgb(*_srgb("#3b362d")[:3]), g.rgb(*_srgb("#4f4a3f")[:3]))
    base = g.mixc(g.math("MULTIPLY", sd, 0.50), base,
                  g.rgb(*_srgb("#6a6355")[:3]))
    base = g.mixc(g.mr(sid.outputs["Color"], 0.0, 1.0, 0.0, 0.40), base,
                  g.rgb(*_srgb("#5c5449")[:3]))
    nrm = g.bump(g.math("ADD", g.math("MULTIPLY", sd, 1.0),
                        g.math("MULTIPLY", fn, 0.45)),
                 strength=1.0, distance=0.0032)
    bsdf = g.n("ShaderNodeBsdfPrincipled")
    g.set(bsdf.inputs["Base Color"], base)
    g.set(bsdf.inputs["Roughness"], 0.95)
    g.set(bsdf.inputs["Normal"], nrm)
    out = g.n("ShaderNodeOutputMaterial")
    m.node_tree.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return m


def _bay_materials(me):
    for f in (mat_concrete, mat_asphalt, mat_overband, mat_formface):
        me.materials.append(f())


# =============================================================================
# 8.  EMIT
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


def _bay_object(bay, coll, pitch, name=None, fine=True, link=True):
    me = bay_mesh(bay, pitch, name=name, fine=fine)
    _bay_materials(me)
    ob = bpy.data.objects.new(me.name, me)
    wx, wy = bay.world_centre()
    ob.location = (float(wx), float(wy), bay.level)
    ob.rotation_euler = (0.0, 0.0, math.radians(C.ROT_DEG))
    if link:
        coll.objects.link(ob)
    return ob


def _instancer_group(name, library, n_sources, seed):
    ng = bpy.data.node_groups.new(name, "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT",
                            socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT",
                            socket_type="NodeSocketGeometry")
    gi = ng.nodes.new("NodeGroupInput"); gi.location = (-700, 0)
    go = ng.nodes.new("NodeGroupOutput"); go.location = (700, 0)
    ci = ng.nodes.new("GeometryNodeCollectionInfo"); ci.location = (-700, -240)
    ci.inputs["Collection"].default_value = library
    ci.inputs["Separate Children"].default_value = True
    ci.inputs["Reset Children"].default_value = True
    iop = ng.nodes.new("GeometryNodeInstanceOnPoints"); iop.location = (250, 0)
    iop.inputs["Pick Instance"].default_value = True
    ridx = ng.nodes.new("FunctionNodeRandomValue"); ridx.location = (-330, -520)
    ridx.data_type = "INT"
    for s in ridx.inputs:
        if not s.enabled:
            continue
        if s.name == "Min":
            s.default_value = 0
        elif s.name == "Max":
            s.default_value = max(0, n_sources - 1)
        elif s.name == "Seed":
            s.default_value = int(seed) % 30000
    # A bay laid the other way round is a different bay to the eye — the broom
    # runs the other way, the curl is on the other joint, the crack enters from
    # the other side.  It must be 0 or exactly pi: a bay is a rectangle and any
    # other angle would open a wedge of sub-base between it and its neighbour.
    # This sits ON TOP of the source variation, never instead of it: transform
    # randomisation is not variation.
    rflip = ng.nodes.new("FunctionNodeRandomValue"); rflip.location = (-560, -800)
    rflip.data_type = "FLOAT"
    for s in rflip.inputs:
        if not s.enabled:
            continue
        if s.name == "Min":
            s.default_value = 0.0
        elif s.name == "Max":
            s.default_value = 1.0
        elif s.name == "Seed":
            s.default_value = (int(seed) + 991) % 30000
    gt = ng.nodes.new("ShaderNodeMath"); gt.location = (-360, -800)
    gt.operation = "GREATER_THAN"
    gt.inputs[1].default_value = 0.5
    mul = ng.nodes.new("ShaderNodeMath"); mul.location = (-190, -800)
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = math.pi
    cxyz = ng.nodes.new("ShaderNodeCombineXYZ"); cxyz.location = (-20, -800)
    ng.links.new(gi.outputs[0], iop.inputs["Points"])
    ng.links.new(ci.outputs["Instances"], iop.inputs["Instance"])
    for s in ridx.outputs:
        if s.enabled:
            ng.links.new(s, iop.inputs["Instance Index"]); break
    for s in rflip.outputs:
        if s.enabled:
            ng.links.new(s, gt.inputs[0]); break
    ng.links.new(gt.outputs[0], mul.inputs[0])
    ng.links.new(mul.outputs[0], cxyz.inputs["Z"])
    ng.links.new(cxyz.outputs[0], iop.inputs["Rotation"])
    ng.links.new(iop.outputs["Instances"], go.inputs[0])
    return ng


def bucket_of(bay):
    """The library bucket a bay may be filled from.

    A library mesh is only legal in a slot that shares its FOOTPRINT (a 2.55 m
    bay in a 3.05 m slot would open a 500 mm hole in the apron), its POSITION
    ACROSS THE STRIP (or the wheel track would stop at the joint) and roughly its
    TRAFFIC LEVEL (or the polish would step).  Those three are the bucket.
    """
    li = min(range(len(BAY_L)), key=lambda i: abs(BAY_L[i] - bay.w))
    ac = int(min(ALONG_CLASSES - 1, max(0, bay.pa * ALONG_CLASSES)))
    return (li, bay.sclass, ac)


def build(anchor_world=None, quality="hero", rect_c=None, seed=SEED,
          coll_name=COLL_NAME, lib_per_class=None, stats=None,
          explicit_r=EXPLICIT_R_M, field_r=FIELD_R_M,
          view_az_deg=None, vert_budget=VERT_BUDGET):
    """Emit the paving.  -> stats dict.

    `anchor_world` is THE LENS.  Bays near it are individual unique meshes at a
    pitch that resolves TARGET_PX at their own distance; bays beyond
    `explicit_r` are instanced from libraries of unique bay meshes, one library
    per size class, at two coarser LOD bands.  That is the only way 5 560 bays
    over 49 645 m2 can exist at all — and it is honest about it: the report
    carries the repeat factor.
    """
    t0 = time.time()
    draft = (quality == "draft")
    coll = _collection(coll_name)
    libcoll = _collection(LIB_COLL_NAME, link=False)
    if lib_per_class is None:
        lib_per_class = 2 if draft else 12
    if draft:
        explicit_r = min(explicit_r, 9.0)
        field_r = min(field_r, 26.0)
        vert_budget = 2_600_000

    ax, ay = anchor_world[0], anchor_world[1]
    acx, acy = C.world_to_circuit(ax, ay)
    acx = float(acx); acy = float(acy)
    if rect_c is None:
        rect_c = (acx - field_r - 6.0, acx + field_r + 6.0,
                  acy - field_r - 6.0, acy + field_r + 6.0)

    bays = bay_layout(rect_c, seed)
    _index_bays(bays)
    print(">> layout: %d bays over %.0f m2 (mean %.3f m2, manifest %.3f m2)"
          % (len(bays), sum(b.area for b in bays),
             sum(b.area for b in bays) / max(len(bays), 1), BAY_MEAN_AREA_M2))

    anchor3 = Vector((ax, ay, anchor_world[2] if len(anchor_world) > 2 else 3.5))
    az = None if view_az_deg is None else math.radians(view_az_deg)

    near, far = [], []
    for b in bays:
        wx, wy = b.world_centre()
        d = math.sqrt((wx - ax) ** 2 + (wy - ay) ** 2
                      + (anchor3.z - b.level) ** 2)
        infront = True
        if az is not None:
            ang = math.atan2(wy - ay, wx - ax)
            dd = abs((ang - az + math.pi) % (2 * math.pi) - math.pi)
            infront = dd < math.radians(52.0)
        if d <= explicit_r and (infront or d < 5.0):
            near.append((d, b))
        else:
            far.append((d, b))

    # ---- 1. the explicit near field ----------------------------------------
    # Sorted by distance and cut off at the vertex budget, so the bays that get
    # the finest mesh are the ones the lens is actually near.  Everything the
    # budget drops falls through to the instanced band; nothing goes missing.
    objs = []
    quads = 0
    verts = 0
    dropped = []
    for d, b in sorted(near, key=lambda t: t[0]):
        p = lod_pitch(d)
        est = int((b.w / p + 3) * (b.h / p + 3) * 1.25)
        if verts + est > vert_budget:
            dropped.append((d, b))
            continue
        ob = _bay_object(b, coll, p, name="%sBay_%05d" % (PFX, b.idx), fine=True)
        objs.append(ob)
        quads += len(ob.data.polygons)
        verts += len(ob.data.vertices)
    if dropped:
        print(">> vertex budget: %d of %d near bays pushed to the instanced band"
              % (len(dropped), len(near)))
        far.extend(dropped)
        near = [t for t in near if t not in dropped]
    print(">> explicit near field: %d bays, %d quads, %d verts, "
          "pitch %.2f .. %.2f mm"
          % (len(objs), quads, verts,
             lod_pitch(min([d for d, _ in near])) * 1000 if near else 0.0,
             lod_pitch(max([d for d, _ in near])) * 1000 if near else 0.0))

    # ---- 2. the library ----------------------------------------------------
    pitch = LIB_PITCH
    buckets = {}
    for d, b in far:
        buckets.setdefault(bucket_of(b), []).append(b)
    libs = {}
    lib_n = 0
    for key, members in sorted(buckets.items()):
        n = min(lib_per_class, max(2, len(members)))
        cl = _collection("%s_%d_%d_%d" % ((LIB_COLL_NAME,) + key), link=False)
        if cl.name not in libcoll.children:
            libcoll.children.link(cl)
        srcs = []
        proto = members[0]
        for i in range(n):
            # A LIBRARY bay is not a copy of a placed bay.  It shares only what
            # the bucket forces it to share — footprint, position across the
            # strip, traffic level — and generates its own broom, curl, chips,
            # crazing, crack, patch and age from its own seed.  That is the
            # difference between a library and "one tree spammed 100 times".
            lb = Bay(**{k: getattr(proto, k) for k in Bay.__slots__})
            r = lambda k: float(_h(key[0], key[1], key[2], i, seed + k))  # noqa
            lb.seed = int(r(1301) * 1e6)
            lb.idx = 900000 + lib_n
            lb.level = 0.0
            lb.synth = True
            lb.fin = float(np.clip(0.30 + 0.80 * r(1303), 0.30, 1.0))
            lb.age = float(0.10 + 0.90 * r(1305))
            lb.curl = float(0.0006 + (CURL_MAX_M - 0.0006) * r(1307) ** 1.4)
            lb.tx = float((r(1309) - 0.5) * 0.0016 / max(lb.w, 0.6))
            lb.ty = float((r(1311) - 0.5) * 0.0016 / max(lb.h, 0.6))
            lb.dish = float((r(1313) - 0.45) * 0.0016)
            lb.broom_ang = math.radians((0.0 if r(1316) < 0.55 else 90.0)
                                        + (r(1315) - 0.5) * 28.0)
            lb.groove_p = float(0.0112 + 0.0092 * r(1317))
            lb.groove_d = float(0.00045 + 0.00095 * r(1319))
            lb.pass_w = float(0.42 + 0.22 * r(1321))
            lb.craze = float(max(0.0, r(1323) * 1.7 - 0.28))
            lb.crack = (r(1325) < 0.085)
            lb.reinst = (r(1327) < FRAC_REINSTATE * 1.6)
            lb.trowel = float(0.00016 + 0.00030 * r(1329))
            lb.popout = float(max(0.0, r(1331) * 1.6 - 0.32))
            lb.oil = float(max(0.0, r(1333) * 1.9 - 1.0))
            lb.damp = float(r(1335))
            lb.cx = 0.0; lb.cy = 0.0
            me = bay_mesh(lb, pitch,
                          name="%sB%d_%d_%d_%03d" % ((LIBPFX,) + key + (i,)),
                          fine=False)
            _bay_materials(me)
            ob = bpy.data.objects.new(me.name, me)
            ob.hide_render = True
            cl.objects.link(ob)
            srcs.append(ob)
            lib_n += 1
        libs[key] = (cl, srcs)

    # ---- 3. the instancers -------------------------------------------------
    # The instancer's own matrix carries the circuit frame, so its point cloud is
    # in CIRCUIT coordinates and the instanced bays come out axis-aligned to the
    # laying plan.  Getting this wrong rotates every far bay by 40 deg and opens
    # the apron like a broken tile floor.
    T0 = C.circuit_to_world(0.0, 0.0)
    inst_objs = []
    n_inst = 0
    for key, members in sorted(buckets.items()):
        cl, srcs = libs[key]
        pts = [(b.cx, b.cy, b.level) for b in members]
        me = bpy.data.meshes.new("%sField_%d_%d_%d" % ((PFX,) + key))
        me.from_pydata(pts, [], [])
        me.update()
        ob = bpy.data.objects.new(me.name, me)
        ob.location = (float(T0[0]), float(T0[1]), 0.0)
        ob.rotation_euler = (0.0, 0.0, math.radians(C.ROT_DEG))
        coll.objects.link(ob)
        ng = _instancer_group(me.name + "_GN", cl, len(srcs),
                              seed + 31 * key[0] + 7 * key[1] + key[2])
        md = ob.modifiers.new("paving", "NODES")
        md.node_group = ng
        ob["instances"] = len(pts)
        ob["library_sources"] = len(srcs)
        inst_objs.append(ob)
        n_inst += len(pts)
    print(">> instanced field: %d bays from %d buckets, %d unique source meshes "
          "at %.1f mm pitch (repeat %.1fx here)"
          % (n_inst, len(libs), lib_n, pitch * 1000,
             n_inst / max(lib_n, 1)))

    # ---- 4. joints and bed -------------------------------------------------
    joints = joint_segments(bays, seed)
    furn = joint_furniture(joints, coll, (acx, acy), seed,
                           max_r=min(explicit_r, 15.0) + 2.0)
    bed = bed_tiles(rect_c, coll, seed)

    st = dict(
        bays_total=len(bays), bays_explicit=len(objs),
        bays_instanced=len(far), instances=n_inst,
        library_meshes=lib_n, library_pitch_mm=round(pitch * 1000, 2),
        libraries=len(libs), joints=len(joints),
        joints_weeded=sum(1 for j in joints if j.weeded),
        joints_sealed=sum(1 for j in joints if j.sealed),
        joints_sawn=sum(1 for j in joints if j.kind == "sawn"),
        joints_formed=sum(1 for j in joints if j.kind == "formed"),
        reinstated=sum(1 for b in bays if b.reinst),
        objects=len(objs) + len(inst_objs) + len(furn) + len(bed),
        seconds=round(time.time() - t0, 1),
    )
    if stats is not None:
        stats.update(st)
    print(">> build: %s" % json.dumps(st))
    return st


# =============================================================================
# 9.  THE TEST SCENE
# =============================================================================
# A real patch of the paddock at its real world position, lit by the contract
# sun, with the camera at the manifest's own 4.6 m / 35 mm.
TEST_C = (-120.0, 76.0)         # circuit-frame centre of the search for the shot
VIEW_AZ_DEG = -50.0             # along the strips, 8 deg off the sun's bearing
CAM_PITCH_DEG = 54.0            # see camera_pose for why this and not a lower one


def apply_contract_sky():
    """Force the Sky Texture onto the contract's atmosphere.  MUST be called
    after any procedural_world(), including the one inside save_clean: that
    helper writes its own numbers, two of which are wrong for this Blender
    (`dust_density` does not exist; it is `aerosol_density`) and three of which
    are wrong for this contract."""
    w = bpy.context.scene.world
    if not (w and w.use_nodes):
        return 0
    n = 0
    for nd in w.node_tree.nodes:
        if nd.type != "TEX_SKY":
            continue
        for attr, val in (("sun_disc", C.SKY_SUN_DISC),
                          ("sun_intensity", 1.0),
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
    print(">> sun: elev %.3f deg  bearing %.3f deg  energy %.3f  shadow ratio %.4f"
          % (C.SUN_ELEV_DEG, C.SUN_BEARING_DEG, C.SUN_ENERGY,
             C.SUN_SHADOW_RATIO))
    return ob


def camera_pose(target_world, az_deg=VIEW_AZ_DEG, pitch_deg=CAM_PITCH_DEG,
                lens=LENS_AT_CLOSEST_MM, near_m=NEAREST_CAMERA_M):
    """Place the lens EXACTLY `near_m` from the paving.

    WHICH DISTANCE 4.6 m IS, and why the first attempt had it wrong.  The
    manifest derives `nearest_camera_m` as "the minimum over the camera
    corridor" — the closest the lens EVER gets to this item.  This item is a
    continuous ground plane, so the closest point is always the one directly
    under the lens, and "4.6 m from the paving" therefore means **the camera
    flies at 4.6 m altitude**.  Solving instead for the frame's bottom edge, as
    the first version did, put the lens at 3.53 m and produced a shot 1.07 m
    closer than the film ever gets — a harder test than the manifest specifies,
    which is not the same thing as the specified test.

    So: height = near_m exactly, and the axis is pitched steeply (62 deg) so the
    frame is filled with paving at 4.70 .. 6.41 m rather than with the horizon.
    At the frame centre that is 3733/5.21 = 717 px/m; at the near edge 795 px/m,
    against the manifest's 812 px/m at the nadir.  Every one of those numbers is
    printed below rather than claimed.
    """
    vhalf = math.degrees(math.atan(0.5 * SENSOR_MM * 2160 / 3840 / lens))
    bot = pitch_deg + vhalf
    h = near_m
    ground_near = h / math.tan(math.radians(bot))
    aim_d = h / math.tan(math.radians(pitch_deg))
    a = math.radians(az_deg)
    cam = Vector((target_world[0] - math.cos(a) * aim_d,
                  target_world[1] - math.sin(a) * aim_d, h))
    tgt = Vector((target_world[0], target_world[1], target_world[2]))
    top = pitch_deg - vhalf
    print(">> camera solve: lens %.1f mm  vhalf %.2f deg  axis %.1f deg down"
          % (lens, vhalf, pitch_deg))
    print(">>   height %.4f m; frame bottom %.2f deg -> %.3f m out, %.4f m slant"
          % (h, bot, ground_near, math.hypot(ground_near, h)))
    print(">>   frame centre %.2f m out (%.2f m slant); frame top %.2f deg -> "
          "%.2f m slant" % (aim_d, math.hypot(aim_d, h), top,
                            math.hypot(h / math.tan(math.radians(top)), h)
                            if top > 0.3 else float("inf")))
    for lbl, dd in (("nadir (the manifest's 4.600 m)", h),
                    ("frame bottom", math.hypot(ground_near, h)),
                    ("frame centre", math.hypot(aim_d, h))):
        print(">>   px/m at %-32s %6.2f m -> %6.1f px/m  (1 px = %.3f mm)"
              % (lbl, dd, RES_X_4K * lens / SENSOR_MM / dd,
                 1000.0 * SENSOR_MM * dd / (RES_X_4K * lens)))
    return cam, tgt, h


def macro_camera(scene, target_world, name="CAM_PPB_Macro"):
    cam_p, tgt, h = camera_pose(target_world)
    cd = bpy.data.cameras.new(name)
    cd.lens = LENS_AT_CLOSEST_MM
    cd.sensor_width = SENSOR_MM
    cd.clip_start = 0.02
    cd.clip_end = 2000.0
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
    """Report the distance from the lens to the nearest PPB_ vertex ACTUALLY
    BUILT.  A claim about the filmed distance that is not this number is a claim
    about the intent, not the artefact (R2-017)."""
    deps = bpy.context.evaluated_depsgraph_get()
    cp = np.array(cam.matrix_world.translation)
    best = 1e9; who = ""
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
    print(">> nearest %s vertex to the lens: %.4f m  (%s)  manifest %.3f m"
          % (PFX, best, who, NEAREST_CAMERA_M))
    return best


def choose_test_target(seed=SEED, centre=TEST_C, span=86.0):
    """Pick the patch of paddock the macro is shot on, and say why.

    The manifest names five variation axes.  A macro that happens to land on
    plain concrete proves none of them, and "it is in the code" is not evidence:
    R2-017 is exactly that failure.  So the frame is CHOSEN — scan the real
    layout for the bay with the most of the five inside the 3.5 x 5.4 m the
    frame actually covers at 4.6 m on a 35 mm lens, and print the inventory.

    The scan calls the same `bay_layout` the build calls, so what it reports is
    what gets built rather than a parallel opinion about it.
    """
    rect = (centre[0] - span * 0.5, centre[0] + span * 0.5,
            centre[1] - span * 0.5, centre[1] + span * 0.5)
    bays = bay_layout(rect, seed)
    joints = joint_segments(bays, seed)
    jc = np.array([[0.5 * (j.p0[0] + j.p1[0]), 0.5 * (j.p0[1] + j.p1[1])]
                   for j in joints]) if joints else np.zeros((0, 2))
    weeded = np.array([j.weeded for j in joints], bool)
    bcx = np.array([b.cx for b in bays]); bcy = np.array([b.cy for b in bays])
    reinst = np.array([b.reinst for b in bays], bool)
    crackf = np.array([b.crack for b in bays], bool)
    polf = np.array([b.polish for b in bays])
    oilf = np.array([b.oil for b in bays])
    finf = np.array([b.fin for b in bays])
    inside = C.apron_platform_mask(
        *C.circuit_to_world(bcx, bcy))
    print('>>   %d of %d candidate bays lie inside a declared apron region'
          % (int(inside.sum()), len(bays)))
    best, bestsc, bestwhy = None, -1.0, {}
    for b in bays:
        d = np.hypot(bcx - b.cx, bcy - b.cy)
        near = d < 3.8
        wx, wy = b.world_centre()
        n_weed = 0
        if jc.size:
            dj = np.hypot(jc[:, 0] - wx, jc[:, 1] - wy)
            n_weed = int((weeded & (dj < 2.6)).sum())
        n_re = int((reinst & near).sum())
        oil = float(oilf[near].max()) if near.any() else 0.0
        if not inside[b.idx]:
            continue
        # THE FRAME MUST CONTAIN THE AXES, NOT THE NEIGHBOURHOOD.  The first two
        # macros were both shot on a bay scored 8.0 out of 9.7 for having a
        # wheel track and an oil stain "within 3.8 m" — and neither was in the
        # 5.4 x 4.5 m the frame actually covers.  A score that can be satisfied
        # off-camera is not a measurement of the shot.  The wheel track has to
        # run through the TARGET BAY ITSELF.
        if polf[b.idx] < 0.45:
            continue
        if oil < 0.30:
            continue
        pol = float(polf[near].max()) if near.any() else 0.0
        crk = int((crackf & near).sum())
        spr = float(finf[near].max() - finf[near].min()) if near.any() else 0.0
        sc = (2.6 * min(n_re, 1) + 2.2 * min(pol / 0.7, 1.0)
              + 1.7 * min(n_weed / 3.0, 1.0) + 1.5 * min(oil / 0.5, 1.0)
              + 0.9 * min(crk, 2) / 2.0 + 0.8 * min(spr / 0.6, 1.0))
        if sc > bestsc:
            bestsc, best = sc, b
            bestwhy = dict(score=round(sc, 3), bay=b.idx,
                           circuit_xy=[round(b.cx, 2), round(b.cy, 2)],
                           reinstatements_within_3m=n_re,
                           weeded_joints_within_2p6m=n_weed,
                           wheel_track_polish=round(pol, 3),
                           oil=round(oil, 3), cracked_bays_within_3m=crk,
                           finish_spread=round(spr, 3))
    print(">> macro target chosen from %d candidate bays: %s"
          % (len(bays), json.dumps(bestwhy)))
    return best, bestwhy


def build_test_scene(quality="hero", out=None, seed=SEED):
    scene = bpy.context.scene
    _clear()
    tb, why = choose_test_target(seed)
    tw = (C.circuit_to_world(tb.cx, tb.cy) if tb is not None
          else C.circuit_to_world(TEST_C[0], TEST_C[1]))
    target = (float(tw[0]), float(tw[1]), 0.0)
    # the lens, so build() can decide LOD against it
    cam_p, tgt, h = camera_pose(target)
    stats = build(anchor_world=(cam_p.x, cam_p.y, cam_p.z), quality=quality,
                  seed=seed, view_az_deg=VIEW_AZ_DEG,
                  rect_c=None)
    stats["macro_target"] = why
    contract_sun(scene)
    cam = macro_camera(scene, target)
    stats["camera_nearest_m"] = round(measure_nearest(cam), 4)

    scene.render.engine = "CYCLES"
    scene.render.resolution_x = 3840
    scene.render.resolution_y = 2160
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
        scene.cycles.adaptive_threshold = 0.006
        scene.cycles.use_denoising = True
    except Exception as e:
        print("   (cycles settings: %s)" % e)

    if out:
        _save(out)
        stats["blend"] = out
        stats["blend_mb"] = round(os.path.getsize(out) / 1048576.0, 1)
        print(">> saved %s (%.1f MB)" % (out, stats["blend_mb"]))
    return stats


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


# =============================================================================
# 10.  SELF-MEASUREMENT — the things item_gate structurally cannot check
# =============================================================================
def verify(seed=SEED, out=None, world_rect=None):
    """Measure the ARTEFACT.  Every number is a physical quantity (R2-017).

    Four questions the gate cannot answer for this item:

      1. Does the bay-to-bay level step stay inside the manifest's tolerance?
         The gate measures screen pixels, not construction tolerance.  This walks
         every edge-adjacent pair in a full 5 560-bay world layout and reports the
         maximum step in millimetres.

      2. Are the five declared variation axes actually realised, at the declared
         rates?  18 % weed joints and 2.4 % reinstatement are numbers, so they
         are counted, not claimed.

      3. How far does the built concrete deviate from C.world_ground_z, which
         every other module will call?  Reported as a bound, both signs.

      4. What is the repeat factor of the instanced field?  The gate stops at
         `distinct_sources >= 40`; the user's bar is "no repeats", so the real
         ratio is printed whether it flatters this module or not.
    """
    rep = {}
    # ---- 1 & 2: a FULL world layout, not the test patch -------------------
    if world_rect is None:
        # the paddock proper, the biggest of the four apron regions
        world_rect = C.APRON_REGIONS_CIRCUIT["paddock"]
        world_rect = (world_rect[0], world_rect[1], world_rect[2], world_rect[3])
    bays = bay_layout(world_rect, seed)
    idx = {(b.si, b.bi): b for b in bays}
    steps = []
    for b in bays:
        for key in ((b.si, b.bi + 1), (b.si + 1, b.bi)):
            o = idx.get(key)
            if o is not None:
                steps.append(abs(b.level - o.level))
    steps = np.array(steps)
    lv = np.array([b.level for b in bays])
    joints = joint_segments(bays, seed)
    rep["world_layout"] = dict(
        rect_circuit=[round(v, 1) for v in world_rect],
        bays=len(bays), area_m2=round(sum(b.area for b in bays), 1),
        mean_bay_area_m2=round(sum(b.area for b in bays) / max(len(bays), 1), 4),
        manifest_mean_bay_area_m2=round(BAY_MEAN_AREA_M2, 4),
        level_step_max_mm=round(float(steps.max()) * 1000, 3),
        level_step_p99_mm=round(float(np.percentile(steps, 99)) * 1000, 3),
        level_step_mean_mm=round(float(steps.mean()) * 1000, 3),
        level_min_mm=round(float(lv.min()) * 1000, 3),
        level_max_mm=round(float(lv.max()) * 1000, 3),
        manifest_tolerance_mm=15.5, manifest_measured_mm=14.8,
        within_tolerance=bool(steps.max() <= 0.0155),
    )
    rep["variation_axes"] = dict(
        sawn_joints=sum(1 for j in joints if j.kind == "sawn"),
        formed_joints=sum(1 for j in joints if j.kind == "formed"),
        weed_joint_fraction=round(sum(1 for j in joints if j.weeded)
                                  / max(len(joints), 1), 4),
        weed_joint_fraction_declared=FRAC_WEED_JOINTS,
        reinstatement_fraction=round(sum(1 for b in bays if b.reinst)
                                     / max(len(bays), 1), 4),
        reinstatement_fraction_declared=FRAC_REINSTATE,
        oil_stained_bays=sum(1 for b in bays if b.oil > 0.08),
        wheel_track_bays=sum(1 for b in bays if b.polish > 0.15),
        distinct_footprints=len(set((round(b.w, 3), round(b.h, 3))
                                    for b in bays)),
    )
    # ---- 3: deviation from the contract datum -----------------------------
    rng = np.random.default_rng(7)
    dev = []
    for b in bays[:4000:7]:
        for _ in range(3):
            px = b.x0 + (b.x1 - b.x0) * rng.random()
            py = b.y0 + (b.y1 - b.y0) * rng.random()
            wx, wy = C.circuit_to_world(px, py)
            z, _i = bay_top_z(float(wx), float(wy))
            dev.append(z - C.APRON_Z)
    dev = np.array(dev)
    rep["datum_deviation"] = dict(
        samples=len(dev),
        min_mm=round(float(dev.min()) * 1000, 3),
        max_mm=round(float(dev.max()) * 1000, 3),
        mean_mm=round(float(dev.mean()) * 1000, 3),
        declared_min_mm=round(BAY_TOP_MIN_M * 1000, 1),
        declared_max_mm=round(BAY_TOP_MAX_M * 1000, 1),
        inside_declared=bool(dev.min() >= BAY_TOP_MIN_M - 1e-6
                             and dev.max() <= BAY_TOP_MAX_M + 1e-6),
    )
    # ---- 4: what is actually in the scene ---------------------------------
    scene_objs = [o for o in bpy.context.scene.objects
                  if o.type == "MESH" and o.name.startswith(PFX)]
    libs = [o for o in bpy.data.objects if o.name.startswith(LIBPFX)]
    n_inst = sum(int(o.get("instances", 0)) for o in scene_objs)
    rep["scene"] = dict(
        objects=len(scene_objs),
        explicit_bays=sum(1 for o in scene_objs if "Bay_" in o.name),
        instancers=sum(1 for o in scene_objs if "Field_" in o.name),
        instances=n_inst,
        library_meshes=len(libs),
        library_in_scene=sum(1 for o in bpy.context.scene.objects
                             if o.name.startswith(LIBPFX)),
        repeat_factor_here=round(n_inst / max(len(libs), 1), 2),
        repeat_factor_world_if_same_library=round(
            BAY_COUNT_WORLD / max(len(libs), 1), 2),
    )
    # ---- 5: unique-mesh proof over the explicit bays ----------------------
    sig = {}
    for o in scene_objs:
        if "Bay_" not in o.name:
            continue
        me = o.data
        co = np.empty(len(me.vertices) * 3, np.float32)
        me.vertices.foreach_get("co", co)
        sig[o.name] = (len(me.vertices), round(float(co[2::3].min()), 6),
                       round(float(co[2::3].max()), 6),
                       round(float(co[2::3].std()), 8))
    rep["explicit_uniqueness"] = dict(
        n=len(sig), distinct_signatures=len(set(sig.values())),
        distinct_vertex_counts=len(set(v[0] for v in sig.values())))
    if out:
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        json.dump(rep, open(out, "w"), indent=1)
    print(">> VERIFY " + json.dumps(rep, indent=1))
    return rep


def measure():
    objs = [o for o in bpy.context.scene.objects
            if o.type == "MESH" and o.name.startswith(PFX)]
    deps = bpy.context.evaluated_depsgraph_get()
    tris = verts = 0
    for ob in objs:
        oe = ob.evaluated_get(deps)
        me = oe.to_mesh()
        if me is None:
            continue
        verts += len(me.vertices)
        for p in me.polygons:
            tris += max(len(p.vertices) - 2, 1)
        oe.to_mesh_clear()
    return dict(objects=len(objs), triangles=tris, vertices=verts)


# =============================================================================
# 11.  CLI
# =============================================================================
def main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--test-blend", action="store_true")
    ap.add_argument("--quality", default="hero", choices=("hero", "draft"))
    ap.add_argument("--out", default=os.path.join(
        _HERE, "paddock_paving_bay_test.blend"))
    ap.add_argument("--verify", default=os.path.join(
        _ROOT, "render/items/paddock_paving_bay/verify.json"))
    ap.add_argument("--seed", type=int, default=SEED)
    a = ap.parse_args(argv)
    if a.test_blend:
        st = build_test_scene(quality=a.quality, out=a.out, seed=a.seed)
        st.update(measure())
        verify(seed=a.seed, out=a.verify)
        print(">> STAGE RESULT: %s" % json.dumps(st))


if __name__ == "__main__":
    main()
