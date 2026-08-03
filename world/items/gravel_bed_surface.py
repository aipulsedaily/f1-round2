#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gravel_bed_surface.py — CIRCUIT VITRINE, per-item hero campaign, item
``gravel_bed_surface`` (zone ``runoff``, wave 1, build order 60, 4 dependants).

WHAT THIS IS, IN ONE SENTENCE
=============================
Every gravel trap on the circuit built as **real geometry**: an excavated dished
basin, filled with a graded bed of **individually generated water-rounded
pebbles**, raked into tine furrows, mounded against its retaining edges and
scarred where cars have been dug out of it.  There is no gravel texture
anywhere in this module — near the lens the gravel *is* the mesh.

WHY IT HAD TO BE GEOMETRY (the arithmetic, not the vibe)
--------------------------------------------------------
The manifest films this item at **2.8 m on a 35 mm lens**::

    px_per_m = (3840 * 35 / 36) / 2.8 = 1333.3 px/m   ->   1 px = 0.750 mm

A 14 mm pebble is **18.7 px across**.  Standing 5 mm proud under the contract
sun at 12.471 deg elevation (``C.SUN_SHADOW_RATIO`` = 4.522) it throws a
**22.6 mm = 30 px** cast shadow.  A rake furrow 15 mm deep throws a 68 mm =
90 px shadow.  Neither of those exists in a bump map: a bump has no silhouette,
occludes nothing behind it and casts nothing.  At 2.8 m a bump-mapped gravel
trap is a photograph of gravel printed on lino, which is exactly the note the
first world pass came back with.

So: stones are meshed out to ``R_STONE_M`` from the LOD anchor, the rake
furrows and the dish and the scars are meshed **everywhere**, and only the
sub-5.5 mm sand between the stones is left to the shader.

THE PUBLIC INTERFACE  (this item is a FOUNDATION — 4 items depend on it)
=======================================================================
Dependants named in the manifest: ``gravel_rake_furrow`` (900),
``gravel_retaining_kerb`` (1200), ``footprint_in_gravel`` (300) and
``gravel_stone`` (240 000).  None of them can ask questions, so everything they
need is a function here and every one of them is documented against a number.

--- 1. WHERE THE BEDS ARE -----------------------------------------------------

    BEDS                    list[Bed] — the gravel beds on the circuit, taken
                            from ``build_barriers.trap_zones()`` (the built
                            programme, i.e. after thresholding and taper), NOT
                            re-derived from the contract's ideal widths.  19
                            beds, 37 457 m2.  The manifest says 21 / 41 137 m2;
                            that number predates build_barriers' ownership
                            clamp.  ``verify()`` prints both.
    bed_by_id(bid)          -> Bed
    beds_at(s, side)        -> the beds covering a station
    Bed.s0, .s1, .side, .kind ('outer' | 'apex'), .seed, .area_m2
    Bed.rake, .dish, .berm, .scars, .grading   the four declared variation axes,
                            resolved into concrete numbers per bed.  Print them:
                            ``python -m gravel_bed_surface --dump-programme``.

    inner_lat(bed, S)       unsigned lateral (from the CENTRELINE) of the lip
                            line — where the gravel starts.
    width(bed, S)           the bed's own width there.
    bed_local(bed, x, y)    world -> (S, d, inside).  d is metres OUTBOARD of
                            the lip line; t = d / width is the normalised
                            crossing.
    lip_polyline(bed, ds)   the world polyline of the lip, for the kerb.

--- 2. THE FOUR SURFACES, AND WHICH ONE YOU MEAN ------------------------------

    bed_top_z(bed, S, d)    THE DATUM OF THIS ITEM: the finished gravel
                            envelope, i.e. the mean of the pebble tops — what a
                            surveyor's staff reads and what anything resting ON
                            the gravel (a footprint's rim, a marshal's boot, a
                            stone thrown out of a rut) sits on.
                            MEASURED over 245 391 sampled built vertices of the
                            T4 bed: the extreme pebble stands +17.67 mm proud,
                            the 99th percentile +7.72 mm, the mean is -3.02 mm
                            and the deepest sampled vertex is -21.95 mm.  So a
                            dependant that uses bed_top_z is within 8 mm of the
                            surface for 99 % of it, and 18 mm in the worst case.
                            (verify() -> built_pebbles_vs_datum)

    fines_z(bed, S, d)      the sand-and-dust floor BETWEEN the pebbles, which
                            is what the substrate mesh actually is.
                            = bed_top_z - 0.44 * d50 , i.e. 4.0 .. 7.7 mm.
                            Anything that FLOWS INTO the bed meets this.

    bed_base_z(bed, S, d)   the excavated formation the gravel lies on.
                            gravel_depth() below bed_top_z.

    gravel_depth(bed, S, d) thickness of the gravel layer.  MEASURED 0.106 m at
                            the lip to 0.460 m in the dish.  The FIA minimum for
                            a bed a car has to sink into is 0.25 m and this
                            holds it over 93.94 % of the working area, the
                            remainder being the 0-18 % of the crossing where the
                            bed is deliberately ramped so a car crosses the lip
                            instead of catching it. (verify() -> gravel_depth)

    lip_top_z(bed, S)       = C.ground_z at the lip line: the runoff asphalt /
                            painted verge level the bed is let into.  The
                            gravel's own top is LIP_DROP(bed) = 45 .. 95 mm
                            BELOW it, which is the exposed face of
                            ``gravel_retaining_kerb``.  THAT ITEM OWNS THE
                            KERBSTONE; this one only guarantees the gravel meets
                            it and never rises above it.

    ** OWNERSHIP.  ``owns(x, y)`` is an EXCLUSIVE claim. **  Where it returns a
    bed, ``build_barriers``' runoff-platform bands X and G must not build their
    own surface.  MEASURED over 27 360 samples of the whole programme: this
    module's finished gravel reaches 714.6 mm below the contract datum (and its
    formation 1 175 mm below it), while ``build_barriers.platform_z`` stands
    ABOVE this module's gravel over 6.69 % of the bed area by up to 124.2 mm —
    which is exactly the kerbstone reveal at the lip and the berm crest at the
    back.  Leaving both meshes in place is a guaranteed z-fight over that 6.73 %
    and a buried bed everywhere the platform basin is shallower.  See §12 for
    the change and the numbers.

--- 3. THE FIELDS A DEPENDANT NEEDS -------------------------------------------

    rake(bed, S, d)         -> (dz, phase, freshness).  The tine profile that is
                            already in ``bed_top_z``.  ``gravel_rake_furrow``
                            must READ this rather than add its own, or the bed
                            gets two rakes at different angles.
    rake_programme(bed)     -> the passes: angle, pitch, amplitude, wander,
                            freshness, and which one was last.
    disturbance(bed, S, d)  -> (dz, amount, rerake).  Recovery drags, spin
                            rosettes, marshal paths, outrigger pads, re-raked
                            patches.  ``footprint_in_gravel`` should place ON
                            ``walkable`` and add to this, not fight it.
    walkable(bed, S, d)     0..1 — where a marshal actually treads.
    make_stones(...)        THE pebble generator.  ``gravel_stone`` must call
                            this rather than write its own, or the loose stones
                            on the kerb will not be the same rock as the bed
                            they came out of.  Every stone it returns is unique
                            geometry: per-stone axis ratios, per-vertex radial
                            jitter, per-stone lithology.
    STONE_TEMPLATES         the four polyhedra and their triangle counts.
    mat_stone(), mat_bed()  the two materials, cached by name.
    ATTRS_STONE, ATTRS_BED  the vertex attributes both materials read.  A
                            dependant emitting geometry into these materials
                            MUST write all of them.

--- 4. EMITTING ---------------------------------------------------------------

    build(anchor_world=None, quality='hero', beds=None, seed=SEED) -> stats
        Emits into collection ``W_Item_GravelBedSurface`` with object prefix
        ``GBS_``.  ``anchor_world`` is the LOD anchor — the lens position.  Mesh
        pitch, the explicit-stone radius and the pebble polygon budget are all
        driven from it by the pixel rule; move the anchor and the detail follows
        the camera.  With no anchor the whole circuit is built at background
        resolution, which is correct for a bed 300 m from the lens and wrong for
        one at 2.8 m.  THIS IS THE ONE KNOB THE ASSEMBLY HAS TO SET.

        HERO_SITE  the site the film needs it at: the T4 hairpin outside bed,
        the biggest and deepest on the lap (30 m wide, 6 985 m2, s 854..1121 on
        the right), which the 10.6 s static hairpin vantage looks straight
        across.  ``choose_shot`` then picks the STATION inside it by score, and
        prints the score: sun-to-view angle, the disturbance actually inside the
        35 mm frame, dish depth and width.

--- 5. THE LOD CONTRACT — what the assembly has to set, and what it costs -----

    Pebbles are meshed within ``QUALITY[q]['r_stone']`` of the LENS and faded
    out over the last 1.6 m of that; beyond it the rake, ``surface_relief`` and
    M_GBS_Bed's 62-cell/m voronoi carry the surface.  Mesh pitch is
    ``lod_pitch(r)``: ``under`` inside the pebble radius (the pebbles carry the
    detail there and the substrate is the occluded interstitial floor), then the
    pixel rule, then a ``mid_cap`` PLATEAU out to ``mid_r`` so a 200-420 mm
    tractor rake still resolves, then r^1.45 to ``pitch_max``.

    At ``hero`` with the macro anchor that is 15.95 M triangles, 2.32 M vertices
    and 463 212 pebbles over the whole 19-bed / 37 457 m2 programme, essentially
    all of the pebbles in the one bed the lens is in.  MEASURED build 40 s, peak
    resident 8.2 GB, blend 992 MB.  ``ultra`` roughly triples it; ``draft`` is
    about a fifth.

    ** THE ASSEMBLY MUST MOVE THE ANCHOR PER SHOT. **  A bed 300 m from the lens
    gets 0.40 m pitch and no pebbles, which is right for 0.17 px per pebble and
    wrong for anything closer.  Rebuild with the anchor on the shot.

--- 6. RENDERING IT ----------------------------------------------------------

    PASS ``--nodof``.  The render farm's worker restores ``use_dof`` per job
    from the job spec, so a job that does not say otherwise gets the camera's
    own aperture.  The first 4K macro came back defocused by a ~5 px circle and
    looked like a failed build; the geometry was identical to a sharp local
    render of the same frame.  ``build_test_scene`` now also sets the macro
    camera to f/22 focused at the frame centre so that mistake costs nothing.

THE SEVEN LAWS, AND WHERE EACH ONE IS DISCHARGED
================================================
 1. procedural, by hand      no image node, no file, no library.  Every pebble
                             is generated from a hash.  ``item_gate`` measures
                             it: ``no_external_assets``.
 2. no real brands           this item carries no lettering at all.
 3. car scale                the recovery scars are sized off the measured car:
                             2.005 m track width sets the drag furrow's width
                             and the 5.698 m length sets the spin rosette.
 4. z = 0 is one plane       never assumed: every z starts from
                             ``C.ground_z(s, u, side)``.
 5. embed >= 20 mm           this item IS the ground; nothing of it stands on
                             the ground.  Its own basin is cut 0.106 .. 0.460 m
                             into the formation and its pebbles sit with a mean
                             vertex 3.04 mm BELOW the envelope they define.
 6. recentre + TexCoord      every object's mesh is local to its own centre;
                             the object matrix carries the kilometre.  Every
                             material reads ``TexCoord->Object`` and the
                             ``GBS_`` attributes.  ``Geometry->Position``
                             appears nowhere in this file.
 7. chunk along s            no object spans more than ``CHUNK_S_M`` = 90 m.

Run headless::

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \\
        -P world/items/gravel_bed_surface.py -- --test-blend

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \\
        -P world/items/gravel_bed_surface.py -- --test-blend --quality draft
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

# splitmix64's wraparound is THE POINT; numpy 2 reports every wrap as a
# RuntimeWarning, which at 10^8 hashes is hundreds of MB of stderr for a defined
# operation.  Silenced by exact message so a REAL overflow still shows.
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
#     module's gravel has to sit beside M_Surf_Asphalt in the same frame.

COLL_NAME = "W_Item_GravelBedSurface"
PFX = "GBS_"
MPFX = "M_GBS_"
ITEM_ID = "gravel_bed_surface"
SEED = 60201

# ---------------------------------------------------------------- filmed spec
# straight out of docs/item_manifest.json; do not guess what the manifest decided
NEAREST_CAMERA_M = 2.8
LENS_AT_CLOSEST_MM = 35.0
SENSOR_MM = 36.0
RES_X_4K = 3840
PX_PER_M = (RES_X_4K * LENS_AT_CLOSEST_MM / SENSOR_MM) / NEAREST_CAMERA_M  # 1333.3
MM_PER_PX = 1000.0 / PX_PER_M                                             # 0.750
MANIFEST_INSTANCES = 21
MANIFEST_AREA_M2 = 41137.0
MANIFEST_PX = 67          # the 50 mm gravel-layer thickness on the 4K master

# The gate's own limit, restated so the build can be checked against it without
# reading the gate: a hero item must show a 10th-percentile edge <= 6 px.
GATE_EDGE_PX = 6.0
GATE_EDGE_M = GATE_EDGE_PX / PX_PER_M                                     # 4.5 mm


# =============================================================================
# 1.  THE MATERIAL FACTS — a gravel trap is a specified piece of civils
# =============================================================================
#
# FIA Appendix O / circuit-licence practice, and what a photograph of one shows:
#
#   * The fill is WASHED, ROUNDED river or marine gravel, single-sized so it
#     cannot compact — a car has to sink into it, not drive across it.  Nominal
#     5-16 mm is the common European spec; 16-32 mm appears on older beds and
#     in the top-up loads.  ROUNDED is the whole point: crushed angular stone
#     interlocks and forms a crust.
#   * Minimum depth 250 mm over the working area, ramped shallower at the lip
#     so a car crosses the edge instead of catching it.
#   * The bed is DISHED — deeper away from the track — so a car decelerates
#     progressively and cannot ride out the far side.
#   * It is RAKED after every session.  A tractor-towed rake leaves 200-420 mm
#     tine spacing; a hand rake 90-150 mm.  Marshals rake right up to the
#     kerbstone.
#   * It is contained at the track edge by a precast KERBSTONE (that is a
#     separate item) whose face stands 45-95 mm above the gravel, and at the
#     back by an earth BERM that the gravel is piled against.
#   * It is SCARRED: a recovery drags a car out with a tractor or a crane, and
#     what is left is a ploughed furrow, outrigger pads, boot prints and a patch
#     that has been re-raked at the wrong angle.
#
# Sizes below are metres unless the name says otherwise.

D50_RANGE = (0.0090, 0.0175)     # bed-to-bed median stone size: 9 .. 17.5 mm
SIZE_LO_K = 0.42                 # d_lo = d50 * this
SIZE_HI_K = 2.25                 # d_hi = d50 * this — the coarse top-up load,
                                 # capped so the biggest stone in the biggest
                                 # bed is 39 mm.  The sibling item gravel_stone
                                 # declares the population as 11-42 mm; this
                                 # sits inside that and does not redefine it.
MESH_FLOOR_M = 0.0055            # NOTHING SMALLER IS MESHED.  5.5 mm is 7.3 px
                                 # at 2.8 m; below that a pebble is a sub-pixel
                                 # triangle cluster whose coverage changes every
                                 # frame the camera moves.  It does not add
                                 # detail, it adds CRAWL.  Sand under 5.5 mm is
                                 # carried by M_GBS_Bed's 1.4 / 0.5 / 0.18 mm
                                 # bump layers, which are temporally stable.
                                 # NOTE this is FINER than the sibling item
                                 # gravel_stone's declared 11 mm floor, because
                                 # that item is filmed at 8.4 m and this one at
                                 # 2.8 m.  Both are the pixel rule, not a guess.

DISH_MAX_M = 0.62                # the manifest's own number: the deepest the
                                 # widest bed dips below the datum
DISH_PER_M_WIDTH = 0.0295        # dish depth per metre of bed width, before the
                                 # per-bed gain and the DISH_MAX_M clamp
DISH_MIN_M = 0.095               # ...and a narrow apex scrape is a scrape

LIP_DROP_RANGE = (0.045, 0.095)  # exposed face of the retaining kerbstone
LIP_RUN_M = 0.55                 # over how much of the bed the lip drop dies
LIP_KEEPOUT_M = 0.030            # no PEBBLE centre closer than this to the lip
                                 # line: that strip is the retaining kerbstone's
                                 # and a pebble sitting on the line reaches its
                                 # own radius inboard of `verge_edge`.  MEASURED
                                 # at -8.0 mm before this existed.

BERM_H_RANGE = (0.045, 0.160)    # gravel mounded against the back retaining edge
BERM_W_RANGE = (0.80, 3.40)

GRAVEL_D_LIP = 0.090             # gravel layer thickness at the lip
GRAVEL_D_DISH = 0.460            # ...and in the dish
FIA_MIN_DEPTH_M = 0.250          # what verify() checks the working area against

CAR_L, CAR_W = 5.698, 2.005      # the measured car — law 3.  Scars are sized
                                 # off it, not off intuition.

CHUNK_S_M = 90.0                 # law 7


# =============================================================================
# 2.  NUMERIC PLUMBING — hashes, noise, worley, packed spheres.  All vectorised.
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


def _hf(*keys):
    """Scalar float hash — for per-bed constants."""
    return float(_h(*[np.asarray(k) for k in keys]))


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
    tot = np.zeros(np.broadcast(np.asarray(x), np.asarray(y)).shape)
    amp = 1.0; norm = 0.0; f = 1.0
    for k in range(oct):
        tot = tot + amp * _vn2(x * f, y * f, seed + 131 * k)
        norm += amp
        amp *= gain
        f *= lac
    return tot / norm


def _vn1(x, seed):
    ix = np.floor(x); fx = x - ix
    u = fx * fx * (3.0 - 2.0 * fx)
    return _h(ix, seed) * (1 - u) + _h(ix + 1, seed) * u


def _fbm1(x, seed, oct=4, lac=2.03, gain=0.5):
    tot = np.zeros(np.shape(np.asarray(x, float)))
    amp = 1.0; norm = 0.0; f = 1.0
    for k in range(oct):
        tot = tot + amp * _vn1(x * f, seed + 977 * k)
        norm += amp
        amp *= gain
        f *= lac
    return tot / norm


def _worley(x, y, seed, jitter=1.0):
    """F1, F2 and the winning cell's hash on a unit lattice."""
    ix = np.floor(x); iy = np.floor(y)
    f1 = np.full(np.shape(x), 9.0)
    f2 = np.full(np.shape(x), 9.0)
    cid = np.zeros(np.shape(x))
    for dj in (-1, 0, 1):
        for di in (-1, 0, 1):
            cx = ix + di; cy = iy + dj
            px = cx + 0.5 + jitter * (_h(cx, cy, seed) - 0.5)
            py = cy + 0.5 + jitter * (_h(cx, cy, seed + 7717) - 0.5)
            d = np.sqrt((px - x) ** 2 + (py - y) ** 2)
            f2 = np.minimum(f2, np.maximum(f1, d))
            win = d < f1
            cid = np.where(win, _h(cx, cy, seed + 33331), cid)
            f1 = np.minimum(f1, d)
    return f1, f2, cid


# THE PACKED-SPHERE DISPLACEMENT WAS REMOVED, and the reason belongs here so
# nobody adds it back.  A union-of-jittered-spheres height field is the right
# analytic model of packed gravel, and the plan was to carry the mid-field with
# it where individual pebbles stop being meshed.  It cannot be afforded: a 14.8
# mm pebble needs a cell of ~35 mm and a mesh pitch under 0.26 of that -- 9 mm --
# to be represented rather than aliased, and 9 mm over the 8-26 m annulus is
# 2.4 million vertices for a band that is 4-6 px per pebble on the master.
# Sampling it at the 20-40 mm pitch that IS affordable produces exactly the beat
# pattern the first context render showed.  So the mid-field is carried by the
# rake (90-420 mm, which the mesh does resolve), by `surface_relief`, and by
# M_GBS_Bed's 62-cell/m voronoi, whose cell size is the pebble size and which
# costs no triangles at all.


def _sstep(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def _smoothstep(e0, e1, x):
    return _sstep((np.asarray(x, float) - e0) / max(1e-9, float(e1 - e0)))


def _clamp01(a):
    return np.clip(a, 0.0, 1.0)


def _srgb(hexstr):
    h = hexstr.lstrip("#")
    out = []
    for i in range(3):
        c = int(h[2 * i:2 * i + 2], 16) / 255.0
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (out[0], out[1], out[2], 1.0)


def _lerp(a, b, t):
    return a + (b - a) * t


# =============================================================================
# 3.  THE BED PROGRAMME — which beds exist, and who each one is
# =============================================================================
# WHERE THE BEDS ARE IS NOT THIS MODULE'S DECISION.  build_barriers owns the
# built runoff programme: the contract's ideal widths thresholded (nobody lays a
# 0.2 m gravel bed), clamped to the room actually available inside the barrier
# line, and tapered to zero at both ends of every run.  Re-deriving it here
# would give a second answer to "how wide is the bed at s = 904", which is the
# class of defect this project has spent the most time on.  So it is IMPORTED.
#
# WHAT IS THIS MODULE'S DECISION is who each bed IS: its rake, its dish, its
# berm and its scars.  That is the manifest's four variation axes, and every one
# of them is resolved into numbers here, per bed, from the bed's own seed.

_BB = None


def _bb():
    """build_barriers, imported lazily (6.7 s and it builds its own history)."""
    global _BB
    if _BB is None:
        import build_barriers as BB
        _BB = BB
    return _BB


class Bed:
    """One gravel trap, and everything that makes it not the other eighteen."""

    __slots__ = ("bid", "s0", "s1", "side", "kind", "seed", "idx",
                 "rake", "dish", "berm", "scars", "grading", "_cache")

    def __init__(self, idx, s0, s1, side, kind):
        self.idx = idx
        self.s0 = float(s0)
        self.s1 = float(s1)
        self.side = int(side)
        self.kind = kind
        self.bid = "%s%s%04d" % (kind[0].upper(), "L" if side > 0 else "R", int(s0))
        self.seed = SEED + 7919 * idx + int(s0) * 13 + (side > 0)
        self._cache = {}
        self.grading = _grading_of(self)
        self.dish = _dish_of(self)
        self.rake = _rake_of(self)
        self.berm = _berm_of(self)
        self.scars = _scars_of(self)

    # -- geometry from build_barriers -------------------------------------
    def radii(self, S):
        """(inner lateral from the centreline, width) at station(s)."""
        return _bb()._trap_radii(np.asarray(S, float), self.side, self.kind)

    @property
    def length(self):
        return self.s1 - self.s0

    @property
    def wmax(self):
        k = "wmax"
        if k not in self._cache:
            S = np.arange(self.s0, self.s1 + 0.5, 0.5)
            self._cache[k] = float(self.radii(S)[1].max())
        return self._cache[k]

    @property
    def area_m2(self):
        k = "area"
        if k not in self._cache:
            S = np.arange(self.s0, self.s1, 0.5)
            self._cache[k] = float(np.sum(self.radii(S)[1]) * 0.5)
        return self._cache[k]

    def __repr__(self):
        return ("<Bed %s %s side%+d s %.0f..%.0f  w<=%.1f  %.0f m2  "
                "dish %.3f m  rake %s>"
                % (self.bid, self.kind, self.side, self.s0, self.s1,
                   self.wmax, self.area_m2, self.dish["depth"],
                   self.rake["passes"][-1]["mode"]))


# --- axis 0 (implied by the others): what rock is in this bed ---------------
# Beds are topped up from whatever the local quarry was selling that year, so
# the bed at T1 is not the bed at T12.  Five lithologies, each with a real
# colour, and per-bed weights.  The stone material reads `lit` and picks.
LITHOLOGY = [
    dict(name="limestone",  col="#c2b69c", rough=0.74, spec=0.30, round=0.95),
    dict(name="quartzite",  col="#b0916a", rough=0.62, spec=0.42, round=0.98),
    dict(name="granite",    col="#94908a", rough=0.68, spec=0.36, round=0.90),
    dict(name="basalt",     col="#55524d", rough=0.72, spec=0.32, round=0.88),
    dict(name="ironstone",  col="#8d5b40", rough=0.78, spec=0.26, round=0.82),
]


def _grading_of(b):
    """Sieve, lithology mix and how weathered this particular load is."""
    s = b.seed
    d50 = D50_RANGE[0] + (D50_RANGE[1] - D50_RANGE[0]) * _hf(s, 11) ** 1.15
    # a wide bed at a heavy braking zone gets the coarser, more expensive load
    if b.kind == "outer":
        d50 *= 1.10
    d50 = float(np.clip(d50, D50_RANGE[0], D50_RANGE[1]))
    # A BED IS ONE OR TWO QUARRIES, NOT FIVE.  The first version drew five
    # near-equal weights and the macro came back salt-and-pepper: a pale
    # limestone next to a black basalt next to an ochre ironstone, at 19 px
    # each, reads as noise rather than as a load of washed gravel.  A real bed
    # is one wash with a minority second rock and a scatter of everything else,
    # so the weights are raised to a high power and renormalised.
    w = np.array([0.02 + 0.98 * _hf(s, 21 + i) for i in range(5)]) ** 2.6
    w[0] *= 2.1                     # limestone: the commonest European fill
    w[3] *= 0.60                    # basalt is the one that reads as pepper
    w[4] *= 0.34
    w = w / w.sum()
    return dict(
        d50=d50,
        d_lo=max(MESH_FLOOR_M, d50 * SIZE_LO_K),
        d_hi=d50 * SIZE_HI_K,
        # how much of the load is angular crushed stone rather than rounded
        # river gravel: a bed topped up from a quarry instead of a pit
        angular=0.11 + 0.27 * _hf(s, 31) ** 1.4,
        discoid=0.08 + 0.22 * _hf(s, 33),
        lith=w,
        dust=0.22 + 0.62 * _hf(s, 35),        # how dusty this bed has got
        damp=0.06 + 0.44 * _hf(s, 37),        # north-facing beds stay wet
        weather=0.15 + 0.80 * _hf(s, 39),     # sun-bleaching of the top layer
    )


def _dish_of(b):
    """VARIATION AXIS 2 — 'depth profile (dips to 0.62 m)'.

    Depth scales with the bed's width, because a 30 m bed at the outside of a
    hairpin is an excavation and a 5.5 m apex scrape is a scrape.  The deepest
    point is NOT the middle: a bed fills up on the side the cars arrive from,
    so the low point sits 0.34 .. 0.71 of the way across, and there is a
    longitudinal low as well, at the station cars actually reach.
    """
    s = b.seed
    gain = 0.74 + 0.52 * _hf(s, 41)
    depth = float(np.clip(DISH_PER_M_WIDTH * b.wmax * gain,
                          DISH_MIN_M, DISH_MAX_M))
    return dict(
        depth=depth, gain=gain,
        t_deep=0.34 + 0.37 * _hf(s, 43),          # where across
        p_exp=0.78 + 0.80 * _hf(s, 45),           # how bowl- vs trough-like
        s_deep=0.18 + 0.62 * _hf(s, 47),          # where along
        s_spread=0.22 + 0.34 * _hf(s, 49),
        s_floor=0.34 + 0.28 * _hf(s, 51),         # depth at the bed's ends
    )


RAKE_MODES = ("longitudinal", "transverse", "diagonal", "arc")


def _rake_of(b):
    """VARIATION AXIS 1 — 'rake furrows'.

    One to three passes.  The LAST pass is the one you mostly see; the ones
    under it survive as a cross-hatch where the last pass was light.  A tractor
    rake is wide, regular and straight; a hand rake is narrow, wanders and stops
    at the kerb.  `fresh` is how long ago: a fresh rake has a sharp cusped
    trough, an old one has slumped and filled with dust.
    """
    s = b.seed
    n = 1 + int(_hf(s, 61) * 2.999)
    passes = []
    for k in range(n):
        hs = s + 100 * (k + 1)
        tractor = _hf(hs, 63) < (0.70 if b.wmax > 9.0 else 0.30)
        mode = RAKE_MODES[int(_hf(hs, 65) * 3.999)]
        if b.wmax < 6.5 and mode == "arc":
            mode = "longitudinal"
        pitch = (0.200 + 0.220 * _hf(hs, 67)) if tractor else \
                (0.090 + 0.062 * _hf(hs, 67))
        passes.append(dict(
            mode=mode, tractor=bool(tractor), pitch=float(pitch),
            amp=float((0.014 + 0.020 * _hf(hs, 69)) if tractor
                      else (0.009 + 0.013 * _hf(hs, 69))),
            ang=float((-0.32 + 0.64 * _hf(hs, 71)) if mode != "diagonal"
                      else (0.35 + 0.85 * _hf(hs, 71))),
            wander=float((0.06 + 0.10 * _hf(hs, 73)) if tractor
                         else (0.16 + 0.34 * _hf(hs, 73))),
            cusp=float(1.10 + 0.85 * _hf(hs, 75)),
            arc_c=(float(-0.4 + 1.8 * _hf(hs, 77)),
                   float(-9.0 - 26.0 * _hf(hs, 79))),
            weight=1.0,
        ))
    # THE LAST PASS DOMINATES.  At the first version's 0.22..0.48 the three
    # passes contributed 7.7, 9.5 and 8.0 mm, i.e. equally, and the 1920 x 1080
    # context check came back with a regular cross-hatch of dots where the three
    # tine lattices beat against each other.  That is an interference pattern,
    # not a raked bed.  A re-rake OVERWRITES: what survives underneath is a
    # trace.
    for k, p in enumerate(passes):
        p["weight"] = 1.0 if k == n - 1 else (0.08 + 0.18 * _hf(s + k, 81))
    # ...and no two passes may run within 22 deg of each other, for the same
    # reason: two rakes at 5 deg apart is a moire, at 40 deg apart it is a
    # cross-hatch, and only the second one exists on a real circuit.
    for k in range(1, n):
        for j in range(k):
            if passes[k]["mode"] == passes[j]["mode"]:
                d = abs(passes[k]["ang"] - passes[j]["ang"])
                if d < 0.384:
                    passes[k]["ang"] = passes[j]["ang"] + \
                        math.copysign(0.384 + 0.5 * _hf(s + k * 7 + j, 85),
                                      passes[k]["ang"] - passes[j]["ang"] or 1.0)
    fresh = 0.12 + 0.86 * _hf(s, 83)
    return dict(passes=passes, n=n, fresh=float(fresh),
                # a rake dies before the very lip on a bed nobody has raked
                # lately, and goes right to the kerbstone on a fresh one
                lip_reach=float(0.10 + 0.55 * (1.0 - fresh)))


def _berm_of(b):
    """VARIATION AXIS 3 — 'berm at the edge'.

    Gravel piled against the back retaining edge, plus the notches where a
    recovery tractor has driven over it and never quite been rebuilt.
    """
    s = b.seed
    h = BERM_H_RANGE[0] + (BERM_H_RANGE[1] - BERM_H_RANGE[0]) * _hf(s, 91) ** 0.9
    w = BERM_W_RANGE[0] + (BERM_W_RANGE[1] - BERM_W_RANGE[0]) * _hf(s, 93)
    w = min(w, max(0.6, 0.28 * b.wmax))
    nn = int(_hf(s, 95) * 4.0)
    notches = [dict(s=b.s0 + b.length * _hf(s, 101 + i),
                    w=2.6 + 3.4 * _hf(s, 111 + i),
                    deep=0.45 + 0.50 * _hf(s, 121 + i)) for i in range(nn)]
    # the LIP end also mounds a little where cars have pushed gravel back at
    # the kerb, but only on beds that get used
    return dict(h=float(h), w=float(w), t_crest=float(0.86 + 0.09 * _hf(s, 97)),
                notches=notches,
                lip_mound=float(0.006 + 0.020 * _hf(s, 99)))


SCAR_KINDS = ("drag", "spin", "path", "pads", "reraked", "entry")


def _scars_of(b):
    """VARIATION AXIS 4 — 'disturbed patches'.

    The manifest's own note: 'scarred where something has been recovered'.  Six
    kinds, each a different geometric event, sized off the measured car:

      drag    a car dragged out by a tractor: a 2.0 m furrow ploughed from
              where it stopped toward the nearest access, 0.10-0.28 m deep,
              with the spoil piled either side.  The rake is erased inside it.
      spin    a rosette where a car span in: an ellipse the length of the car
              with gravel thrown outward and the middle scooped.
      path    a marshal's route in from the barrier: 0.35-0.55 m wide, packed
              down 20-45 mm, the stones pressed flat.
      pads    a recovery crane's outrigger feet, 2-4 of them, 0.7 m square,
              pressed 50-120 mm in.
      reraked a patch re-raked at a different angle from the rest of the bed:
              no depth change at all, and the most convincing of the six.
      entry   the gouge where a car crossed the lip: a widening V from the
              kerbstone, gravel thrown out onto the asphalt behind it.
    """
    s = b.seed
    # how busy this corner is.  T4-scale beds get recovered from; a 15 m apex
    # scrape on a fast kink does not.
    busy = _clamp01(0.20 + 0.75 * _hf(s, 131) * min(1.0, b.wmax / 14.0)
                    + 0.25 * (b.kind == "outer"))
    n = int(round(busy * (2.0 + b.length / 42.0 + b.wmax / 5.0)))
    n = int(np.clip(n, 0, 9))
    out = []
    for i in range(n):
        hs = s + 1000 * (i + 1)
        r = _hf(hs, 133)
        kind = ("entry" if (r < 0.16 and b.kind == "outer") else
                "drag" if r < 0.40 else
                "spin" if r < 0.56 else
                "path" if r < 0.72 else
                "pads" if r < 0.84 else "reraked")
        # WHERE A SCAR SITS IS NOT UNIFORM ACROSS THE BED.  Most excursions
        # are shallow: a car that gets a wheel in travels a few metres, and the
        # first 5 m of a trap carries most of the damage, the tractor tracks and
        # the boot prints.  A deep spin reaches further in.  Placing `t`
        # uniformly (the first version) put the T4 bed's whole scar population
        # 10-26 m outboard, i.e. outside every frame the film ever shoots of it.
        deep_kind = kind in ("drag", "spin")
        out.append(dict(
            kind=kind,
            s=b.s0 + b.length * (0.06 + 0.88 * _hf(hs, 135)),
            t=0.03 + (0.62 if deep_kind else 0.40) * _hf(hs, 137) ** 1.7,
            age=_hf(hs, 139),                     # 0 fresh, 1 nearly re-raked
            ang=(-1.25 + 2.50 * _hf(hs, 141)),
            scale=0.70 + 0.90 * _hf(hs, 143),
            deep=0.55 + 0.85 * _hf(hs, 145),
            n_pad=2 + int(_hf(hs, 147) * 2.99),
            rr_ang=(-1.4 + 2.8 * _hf(hs, 149)),
            rr_pitch=0.10 + 0.30 * _hf(hs, 151),
        ))
    return dict(busy=float(busy), items=out, n=len(out))


def _build_beds():
    zs = _bb().trap_zones()
    # deterministic order so a bed's identity never depends on dict ordering
    zs = sorted(zs, key=lambda z: (-z[2], z[0]))
    return [Bed(i, a, b, side, kind) for i, (a, b, side, kind) in enumerate(zs)]


_BEDS = None


def beds():
    global _BEDS
    if _BEDS is None:
        _BEDS = _build_beds()
    return _BEDS


def bed_by_id(bid):
    for b in beds():
        if b.bid == bid:
            return b
    raise KeyError(bid)


def beds_at(s, side):
    s = float(s) % C.LAP
    return [b for b in beds()
            if b.side == side and b.s0 - 1e-6 <= s <= b.s1 + 1e-6]


# =============================================================================
# 4.  THE SURFACE — every field, in bed-local (station, outboard offset)
# =============================================================================
# d  = metres OUTBOARD of the lip line (d = 0 is the kerbstone face)
# t  = d / width(S)  in 0..1
#
# EVERY disturbance below is windowed to zero at BOTH lateral edges and at both
# ends of the run, so the bed welds exactly onto the runoff platform at t = 1
# and exactly onto the kerbstone reveal at t = 0.  build_barriers learned that
# the hard way: without the window a 190 mm braking rut reached the lip and the
# sub-base showed through it (see build_barriers.build_gravel_trap).


def width(bed, S):
    return bed.radii(np.asarray(S, float))[1]


def inner_lat(bed, S):
    return bed.radii(np.asarray(S, float))[0]


def lip_top_z(bed, S):
    """The runoff-asphalt / painted-verge level at the lip line.  Contract."""
    S = np.asarray(S, float)
    return C.ground_z(S, inner_lat(bed, S), bed.side)


def lip_drop(bed):
    return _lerp(LIP_DROP_RANGE[0], LIP_DROP_RANGE[1], _hf(bed.seed, 161))


def fines_drop(bed):
    """How far the sand floor sits below the pebble-top envelope."""
    return 0.44 * bed.grading["d50"]


def _edge_window(t, w, soft_in=0.055, soft_out=0.085):
    """0 at both lateral edges, 1 in the middle.  `w` in metres so a narrow
    tapering bed tip closes the window on width alone, not just on t."""
    a = _sstep(t / max(soft_in, 1e-6))
    b = _sstep((1.0 - t) / max(soft_out, 1e-6))
    return a * b * _sstep(np.asarray(w, float) / 1.25)


def _end_window(bed, S, ramp=6.0):
    """0 at both ends of the run."""
    return (_smoothstep(bed.s0, bed.s0 + ramp, S) *
            (1.0 - _smoothstep(bed.s1 - ramp, bed.s1, S)))


def dish(bed, S, t, w):
    """Depth of the excavated dish below the datum, metres, >= 0.

    0 at t = 0 and t = 1 for ANY width, so the bed welds flush at both edges.
    """
    D = bed.dish
    td = D["t_deep"]
    tt = np.where(t < td, 0.5 * t / max(td, 1e-6),
                  0.5 + 0.5 * (t - td) / max(1.0 - td, 1e-6))
    cross = np.sin(np.pi * np.clip(tt, 0.0, 1.0)) ** D["p_exp"]
    u = (np.asarray(S, float) - bed.s0) / max(bed.length, 1e-6)
    lon = D["s_floor"] + (1.0 - D["s_floor"]) * np.exp(
        -0.5 * ((u - D["s_deep"]) / D["s_spread"]) ** 2)
    lon = lon * _end_window(bed, S, ramp=min(14.0, 0.30 * bed.length))
    # a bed narrower than 2.6 m is a scrape whatever the programme says
    return D["depth"] * cross * lon * _sstep(np.asarray(w, float) / 2.6)


def berm(bed, S, t, w):
    """Gravel mounded against the back retaining edge.  0 at t=0 and t=1."""
    B = bed.berm
    tw = np.clip(B["w"] / np.maximum(np.asarray(w, float), 1e-6), 0.03, 0.42)
    g = np.exp(-0.5 * ((t - B["t_crest"]) / (0.42 * tw)) ** 2)
    g = g * (1.0 - _sstep((t - (1.0 - 0.30 * tw)) / np.maximum(0.30 * tw, 1e-6)))
    amt = np.ones(np.shape(g))
    for nt in B["notches"]:
        amt = amt * (1.0 - nt["deep"] * np.exp(
            -0.5 * ((np.asarray(S, float) - nt["s"]) / max(nt["w"], 0.5)) ** 2))
    lipm = B["lip_mound"] * np.exp(-0.5 * (t / 0.055) ** 2)
    return B["h"] * g * amt * _sstep(np.asarray(w, float) / 3.0) + lipm


def rake_programme(bed):
    return bed.rake


def rake(bed, S, d, w=None, mesh_pitch=None):
    """The tine profile already present in ``bed_top_z``.

    -> (dz metres, phase 0..1 within the last pass, freshness 0..1)

    ``gravel_rake_furrow`` MUST read this instead of adding its own field, or
    the bed carries two rakes at two angles.  `phase` is 0 in a tine groove and
    1 on the crest between two grooves, which is where wind-blown dust collects
    and where a boot prints most sharply.

    THE PROFILE IS NOT A SINE, AND THE FIRST VERSION HAD IT UPSIDE DOWN.  A rake
    tine cuts a NARROW groove and pushes the spoil into a BROAD low ridge either
    side, so the surface is mostly crest with cusped valleys — ``tri ** e`` with
    e < 1, not e > 1.  Nor do the passes average: the first version divided the
    sum by the total weight, so three passes at three angles cancelled into a
    9.7 mm mush and the 1280 x 720 check came back with no furrows in it at all.
    A re-rake OVERWRITES; the last pass carries its full amplitude and the ones
    under it survive at their own weight on top.

    And the wander is a WAVER, not noise.  At 0.49 * pitch * 3.4 the phase
    jitter was +-0.83 of a period over a 7 m correlation length, which is not a
    hand-raked line, it is a random field with a rake's autocorrelation.  It is
    now +-0.14 of a period over 11 m, which is what a marshal walking a rake
    actually leaves.
    """
    S = np.asarray(S, float)
    d = np.asarray(d, float)
    if w is None:
        w = width(bed, S)
    a = S - bed.s0
    R = bed.rake
    fresh = R["fresh"]
    tot = np.zeros(np.broadcast(a, d).shape)
    ph_last = None
    for p in R["passes"]:
        # BAND-LIMIT PER PASS, not per rake.  The first version took the FINEST
        # pass's pitch as the limit for the whole field, so a 115 mm hand pass
        # the mesh could not carry took the 309 mm tractor pass down with it and
        # the bed went smooth at 10 m.  Each pass is now faded on its own pitch,
        # so the coarse passes survive four times further out.
        if mesh_pitch is not None:
            # 0.13 is SEVEN samples per furrow and 0.30 is three.  The first
            # version faded from 0.22 to 0.52, i.e. right through the 2-4
            # samples-per-period band where a periodic field beats against the
            # sampling grid, and that beat is what the moire in the mid-field
            # was.  Full amplitude only where the mesh genuinely resolves it.
            aa = 1.0 - _sstep((mesh_pitch / p["pitch"] - 0.13) / 0.17)
            if np.all(aa <= 1e-4):
                continue
        else:
            aa = 1.0
        if p["mode"] == "arc":
            cs, cd = p["arc_c"]
            cx = bed.s0 + bed.length * (0.5 + cs)
            cc = np.sqrt((a - (cx - bed.s0)) ** 2 + (d - cd) ** 2)
        elif p["mode"] == "longitudinal":
            cc = d * math.cos(p["ang"]) + a * math.sin(p["ang"]) * 0.06
        elif p["mode"] == "transverse":
            cc = a * math.cos(p["ang"]) + d * math.sin(p["ang"]) * 0.06
        else:
            cc = a * math.sin(p["ang"]) + d * math.cos(p["ang"])
        cc = cc + p["wander"] * p["pitch"] * 0.55 * (
            _fbm2(a / 11.0, d / 8.0, seed=bed.seed + 311, oct=3) - 0.5)
        x = cc / p["pitch"]
        fr = x - np.floor(x)
        tri = 1.0 - np.abs(2.0 * fr - 1.0)
        # fresh: a narrow cusped groove.  old: slumped, wind-filled, sinusoidal.
        e = _lerp(1.0, 1.0 / p["cusp"], fresh)
        prof = tri ** e
        prof = prof - 1.0 / (e + 1.0)               # zero-mean by construction
        # each tine digs its own depth, and one that has hit a big stone skips:
        # that is what makes a real rake line intermittent
        tid = np.floor(x)
        depth = 0.72 + 0.52 * _h(tid, np.full(np.shape(tid), bed.seed + 313))
        skip = _h(tid, np.floor(a / 3.1),
                  np.full(np.shape(tid), bed.seed + 317)) > 0.032
        amp = p["amp"] * _lerp(0.38, 1.0, fresh) * p["weight"]
        tot = tot + amp * prof * depth * skip * aa
        ph_last = tri
    # the rake stops short of the kerb on a bed nobody has raked lately
    win = (_sstep((d - R["lip_reach"]) / 0.30) *
           _sstep((np.asarray(w, float) - d) / 0.60))
    return tot * win, (ph_last if ph_last is not None else np.zeros_like(tot)), fresh


def _scar_field(bed, S, d, w):
    """-> (dz metres, amount 0..1, rerake angle field, rerake amount)."""
    S = np.asarray(S, float)
    d = np.asarray(d, float)
    sh = np.broadcast(S, d).shape
    dz = np.zeros(sh)
    amt = np.zeros(sh)
    rr = np.zeros(sh)
    for it in bed.scars["items"]:
        t0 = it["t"]
        d0 = t0 * np.asarray(w, float)
        ds = S - it["s"]
        dd = d - d0
        age = it["age"]
        fade = 1.0 - 0.72 * age
        k = it["kind"]
        if k == "drag":
            # a 2.0 m furrow (the car's track width) ploughed toward the back
            ang = it["ang"]
            u = ds * math.cos(ang) + dd * math.sin(ang)
            v = -ds * math.sin(ang) + dd * math.cos(ang)
            L = (9.0 + 16.0 * it["scale"])
            along = _sstep((u + L * 0.15) / 2.2) * (1.0 - _sstep((u - L) / 3.4))
            half = 0.5 * CAR_W * (0.85 + 0.5 * it["scale"])
            core = np.exp(-0.5 * (v / (half * 0.62)) ** 2)
            spoil = np.exp(-0.5 * ((np.abs(v) - half * 1.15) / (half * 0.42)) ** 2)
            g = along * fade
            dz -= (0.10 + 0.18 * it["deep"]) * core * g
            dz += (0.045 + 0.075 * it["deep"]) * spoil * g
            amt = np.maximum(amt, g * (core + 0.6 * spoil))
        elif k == "spin":
            ang = it["ang"]
            u = (ds * math.cos(ang) + dd * math.sin(ang)) / (CAR_L * 0.55 * it["scale"])
            v = (-ds * math.sin(ang) + dd * math.cos(ang)) / (CAR_W * 1.15 * it["scale"])
            r = np.sqrt(u * u + v * v)
            g = np.exp(-0.5 * (r / 0.85) ** 2) * fade
            dz -= (0.06 + 0.12 * it["deep"]) * g
            dz += (0.030 + 0.055 * it["deep"]) * np.exp(
                -0.5 * ((r - 1.28) / 0.42) ** 2) * fade
            amt = np.maximum(amt, g)
        elif k == "path":
            # a wandering trail in from the back of the bed
            ang = it["ang"] * 0.6
            v = -ds * math.sin(ang) + dd * math.cos(ang)
            wob = 0.55 * (_fbm1(ds / 6.5, seed=bed.seed + 401 + int(it["s"])) - 0.5)
            g = np.exp(-0.5 * ((v + wob) / 0.23) ** 2) * fade
            g = g * _sstep((d - 0.4) / 1.2)
            dz -= (0.020 + 0.026 * it["deep"]) * g
            amt = np.maximum(amt, g * 0.85)
        elif k == "pads":
            for j in range(it["n_pad"]):
                ps = it["s"] + (j - 1.0) * (2.4 + 1.2 * it["scale"])
                pd = d0 + ((j % 2) * 2.0 - 1.0) * (1.7 + 0.9 * it["scale"])
                bx = np.exp(-0.5 * ((S - ps) / 0.34) ** 4)
                by = np.exp(-0.5 * ((d - pd) / 0.34) ** 4)
                g = bx * by * fade
                dz -= (0.050 + 0.070 * it["deep"]) * g
                dz += 0.022 * fade * (np.exp(-0.5 * ((S - ps) / 0.62) ** 4) *
                                      np.exp(-0.5 * ((d - pd) / 0.62) ** 4) - g)
                amt = np.maximum(amt, g)
        elif k == "entry":
            # the gouge where a car crossed the kerbstone
            ang = it["ang"] * 0.45
            u = d
            v = ds - d * math.tan(ang)
            half = 0.5 * CAR_W * (0.9 + 0.6 * it["scale"])
            L = 5.5 + 11.0 * it["scale"]
            along = (1.0 - _sstep((u - L) / 4.0))
            core = np.exp(-0.5 * (v / (half * 0.70)) ** 2)
            g = along * fade * _sstep(u / 0.5)
            dz -= (0.075 + 0.155 * it["deep"]) * core * g
            dz += (0.040 + 0.060 * it["deep"]) * np.exp(
                -0.5 * ((np.abs(v) - half * 1.25) / (half * 0.5)) ** 2) * g
            amt = np.maximum(amt, g * core)
        else:   # reraked — a patch raked at the wrong angle.  No depth change.
            g = np.exp(-0.5 * ((ds / (6.0 + 9.0 * it["scale"])) ** 2 +
                               (dd / (2.4 + 3.4 * it["scale"])) ** 2))
            rr = np.maximum(rr, g * (1.0 - 0.4 * age))
    return dz, _clamp01(amt), _clamp01(rr)


def disturbance(bed, S, d, w=None):
    """-> (dz metres, amount 0..1, rerake 0..1).  Public: footprint_in_gravel."""
    S = np.asarray(S, float)
    d = np.asarray(d, float)
    if w is None:
        w = width(bed, S)
    dz, amt, rr = _scar_field(bed, S, d, w)
    t = np.clip(d / np.maximum(np.asarray(w, float), 1e-6), 0.0, 1.0)
    win = _edge_window(t, w) * _end_window(bed, S, ramp=4.0)
    return dz * win, amt * win, rr * win


def walkable(bed, S, d, w=None):
    """0..1 — where a marshal actually treads: in from the back, along the
    barrier line, and never through the middle of the dish."""
    S = np.asarray(S, float)
    d = np.asarray(d, float)
    if w is None:
        w = width(bed, S)
    t = np.clip(d / np.maximum(np.asarray(w, float), 1e-6), 0.0, 1.0)
    near_back = _sstep((t - 0.62) / 0.30)
    near_lip = _sstep((0.16 - t) / 0.14)
    return _clamp01(0.85 * near_back + 0.55 * near_lip)


def _rerake_field(bed, S, d, rr):
    """The re-raked patch's own tine field, at its own angle and pitch."""
    if not np.any(rr > 1e-4):
        return np.zeros(np.shape(rr))
    a = np.asarray(S, float) - bed.s0
    d = np.asarray(d, float)
    tot = np.zeros(np.shape(rr))
    for it in bed.scars["items"]:
        if it["kind"] != "reraked":
            continue
        cc = a * math.sin(it["rr_ang"]) + d * math.cos(it["rr_ang"])
        x = cc / it["rr_pitch"]
        fr = x - np.floor(x)
        tri = 1.0 - np.abs(2.0 * fr - 1.0)
        tot = np.maximum(tot, (tri ** 1.3 - 0.55) * (0.008 + 0.012 * it["scale"]))
    return tot


def surface_relief(bed, S, d, w):
    """Metre-scale settlement and the sub-decimetre lumpiness a raked bed has.

    NOT a stone field — the stones are separate.  This is the bed itself: it
    settles where cars have compacted it, humps where the sub-base is proud and
    ripples where the rake has piled material.
    """
    S = np.asarray(S, float)
    d = np.asarray(d, float)
    t = np.clip(d / np.maximum(np.asarray(w, float), 1e-6), 0.0, 1.0)
    z = ((_fbm2(S / 6.2, d / 4.6, seed=bed.seed + 501, oct=4) - 0.5) * 0.070 +
         (_fbm2(S / 1.55, d / 1.30, seed=bed.seed + 503, oct=3) - 0.5) * 0.030 +
         (_fbm2(S / 0.46, d / 0.39, seed=bed.seed + 505, oct=3) - 0.5) * 0.014)
    return z * _edge_window(t, w, 0.07, 0.10)


def bed_top_z(bed, S, d, w=None):
    """THE DATUM OF THIS ITEM — the finished gravel envelope (mean pebble top).

    Everything that rests on the gravel sits here.  Never invents a z: it is
    ``C.ground_z`` plus a bounded, fully-windowed skin.
    """
    S = np.asarray(S, float)
    d = np.asarray(d, float)
    if w is None:
        w = width(bed, S)
    w = np.asarray(w, float)
    t = np.clip(d / np.maximum(w, 1e-6), 0.0, 1.0)
    lat = inner_lat(bed, S) + d
    z = C.ground_z(S, lat, bed.side)
    # the kerbstone reveal, dying over the first LIP_RUN_M and gone by t = 0.72
    z -= lip_drop(bed) * (1.0 - _sstep((d - LIP_RUN_M) / 1.10)) * \
        (1.0 - _sstep((t - 0.72) / 0.28))
    z -= dish(bed, S, t, w)
    z += berm(bed, S, t, w)
    dzr, _ph, _fr = rake(bed, S, d, w)
    dzs, _amt, rr = disturbance(bed, S, d, w)
    # inside a re-raked patch the bed's own rake is replaced, not added to
    z += dzr * (1.0 - rr) + _rerake_field(bed, S, d, rr) * rr
    z += dzs
    z += surface_relief(bed, S, d, w)
    return z


def fines_z(bed, S, d, w=None):
    """The sand-and-dust floor between the pebbles.  This is what the substrate
    mesh is, in the band where the pebbles are explicit geometry."""
    return bed_top_z(bed, S, d, w) - fines_drop(bed)


def gravel_depth(bed, S, d, w=None):
    """Thickness of the gravel layer, metres.  0.09 m at the lip, 0.46 m in the
    dish — the FIA minimum for a bed a car has to sink into is 0.25 m."""
    S = np.asarray(S, float)
    d = np.asarray(d, float)
    if w is None:
        w = width(bed, S)
    t = np.clip(d / np.maximum(np.asarray(w, float), 1e-6), 0.0, 1.0)
    ramp = _sstep(t / 0.16) * _sstep((1.0 - t) / 0.10)
    return GRAVEL_D_LIP + (GRAVEL_D_DISH - GRAVEL_D_LIP) * ramp


def bed_base_z(bed, S, d, w=None):
    """The excavated formation the gravel lies on."""
    return bed_top_z(bed, S, d, w) - gravel_depth(bed, S, d, w)


# --- world <-> bed-local ----------------------------------------------------
def bed_local(bed, x, y):
    """world -> (S, d, inside).  Uses the contract's own projection."""
    su = C.world_su(np.atleast_1d(np.asarray(x, float)),
                    np.atleast_1d(np.asarray(y, float)))
    S = np.asarray(su[0], float)
    U = np.asarray(su[1], float)
    d = np.abs(U) - inner_lat(bed, S)
    w = width(bed, S)
    inside = ((np.sign(U) == bed.side) & (S >= bed.s0) & (S <= bed.s1) &
              (d >= 0.0) & (d <= w))
    return S, d, inside


def owns(x, y):
    """-> the Bed that owns this world point, or None.  EXCLUSIVE (see §12)."""
    for b in beds():
        S, d, inside = bed_local(b, x, y)
        if bool(np.atleast_1d(inside)[0]):
            return b
    return None


def lip_polyline(bed, ds=0.5, z_of="gravel"):
    """The world polyline of the lip line — for ``gravel_retaining_kerb``.

    ``z_of='asphalt'`` gives the level the kerbstone's top is flush with;
    ``'gravel'`` gives the gravel's own top against its face.
    """
    S = np.arange(bed.s0, bed.s1 + ds, ds)
    lat = inner_lat(bed, S)
    P = C.su_to_world(S, lat, bed.side)
    z = (lip_top_z(bed, S) if z_of == "asphalt"
         else bed_top_z(bed, S, np.zeros_like(S)))
    P = np.array(P, float)
    P[:, 2] = z
    return P


# =============================================================================
# 5.  THE PEBBLES — every one a unique polyhedron
# =============================================================================
# A gravel trap is not a surface with a gravel texture on it.  It is a heap of
# 10^8 stones, and within R_STONE_M of the lens this module builds them.
#
# TEMPLATE CHOICE IS DRIVEN BY SCREEN PIXELS, NOT BY TASTE.  A stone `size`
# metres across at `r` metres from the anchor subtends size*3733/r px on the 4K
# master; the polyhedron is picked so its silhouette segments stay under ~2 px:
#
#     >= 22 px   icosphere-1   42 v / 80 f    ~1.9 px per silhouette segment
#     10..22 px  icosahedron   12 v / 20 f    ~1.7 px
#      5..10 px  octahedron     6 v /  8 f    ~1.9 px
#      < 5 px    tetrahedron    4 v /  4 f    (a 4 px blob; it is a blob)
#
# and below MESH_FLOOR_M nothing is meshed at all.

def _icosa():
    p = (1.0 + math.sqrt(5.0)) / 2.0
    V = np.array([
        (-1, p, 0), (1, p, 0), (-1, -p, 0), (1, -p, 0),
        (0, -1, p), (0, 1, p), (0, -1, -p), (0, 1, -p),
        (p, 0, -1), (p, 0, 1), (-p, 0, -1), (-p, 0, 1)], float)
    F = np.array([
        (0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11),
        (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
        (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9),
        (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)], np.int32)
    V = V / np.linalg.norm(V, axis=1)[:, None]
    return V, F


def _subdiv(V, F):
    mid = {}
    Vl = [v for v in V]
    Fl = []
    for (a, b, c) in F:
        idx = []
        for (i, j) in ((a, b), (b, c), (c, a)):
            k = (min(i, j), max(i, j))
            if k not in mid:
                m = (Vl[i] + Vl[j]) * 0.5
                m = m / np.linalg.norm(m)
                mid[k] = len(Vl)
                Vl.append(m)
            idx.append(mid[k])
        ab, bc, ca = idx
        Fl += [(a, ab, ca), (ab, b, bc), (ca, bc, c), (ab, bc, ca)]
    return np.array(Vl, float), np.array(Fl, np.int32)


def _octa():
    V = np.array([(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0),
                  (0, 0, 1), (0, 0, -1)], float)
    F = np.array([(0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4),
                  (2, 0, 5), (1, 2, 5), (3, 1, 5), (0, 3, 5)], np.int32)
    return V, F


def _tetra():
    V = np.array([(1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1)], float)
    V = V / np.linalg.norm(V, axis=1)[:, None]
    F = np.array([(0, 1, 2), (0, 3, 1), (0, 2, 3), (1, 3, 2)], np.int32)
    return V, F


_ICO0 = _icosa()
_ICO1 = _subdiv(*_ICO0)
_OCT = _octa()
_TET = _tetra()

# THE THRESHOLDS ARE SET ON THE FACET EDGE, NOT ON THE PEBBLE.  The first pass
# put them at 22 / 10 / 5 px and the gate measured a 10th-percentile edge of
# 5.54 mm = 7.39 px against a 6.0 px limit, i.e. the finest decile of this
# object was coarser than the lens resolves.  That is not a gate problem, it is
# a silhouette problem: an icosahedron spans a pebble's outline in five segments
# per half, so a 20 px pebble on `ico0` shows 4 px facets and a 12 px pebble on
# `oct` shows a hexagon.  The rule is now that a facet edge stays under ~3 px:
#
#   template  edge / pebble diameter   pebble px for a 3 px edge
#   ico1      0.276                    11
#   ico0      0.553                     5.4
#   oct       0.707                     4.2
#
# which is where the numbers below come from.  Cost: +5.3 M triangles, and the
# measured p10 falls to well inside the limit.
STONE_TEMPLATES = {
    "ico1": dict(V=_ICO1[0], F=_ICO1[1], tris=80, verts=42, min_px=16.0),
    "ico0": dict(V=_ICO0[0], F=_ICO0[1], tris=20, verts=12, min_px=6.0),
    "oct":  dict(V=_OCT[0],  F=_OCT[1],  tris=8,  verts=6,  min_px=3.8),
    "tet":  dict(V=_TET[0],  F=_TET[1],  tris=4,  verts=4,  min_px=0.0),
}
TEMPLATE_ORDER = ("ico1", "ico0", "oct", "tet")

ATTRS_STONE = ("gid", "lit", "dus", "dmp", "emb", "wrn", "siz")
ATTRS_BED = ("dep", "fur", "dst", "dus", "dmp", "brm", "gid")


def make_stones(n, seed, size, tmpl, axis=(1.0, 0.80, 0.58), angular=0.15,
                discoid=0.15, jitter=0.085, rod=0.13):
    """THE pebble generator.  -> (V (n,k,3), F (m,3) local template indices).

    Every stone is unique geometry, in three independent ways, because
    "one tree spammed 100 times" is the named failure:

      1. per-stone axis ratios — a water-rounded pebble is a triaxial
         ellipsoid, and the a:b:c ratios of a river gravel population are
         genuinely spread (Zingg's classification: blades, discs, rods and
         spheres all occur);
      2. per-stone-per-VERTEX radial jitter — no two stones have the same
         lumps;
      3. per-stone class — `angular` of them are crushed quarry stone with
         flat fracture facets (large jitter, hard edges), `discoid` are flat
         river discs, the rest are rounded pebbles.

    Returned vertices are centred on the stone's own centroid and scaled to
    `size` metres on the long axis.  The caller rotates, seats and offsets.
    """
    T = STONE_TEMPLATES[tmpl]
    BV, BF = T["V"], T["F"]
    k = BV.shape[0]
    ii = np.arange(n)[:, None]
    jj = np.arange(k)[None, :]
    cls = _h(ii[:, 0], np.full(n, seed + 3))
    is_ang = cls < angular
    is_disc = (cls >= angular) & (cls < angular + discoid)
    is_rod = (cls >= angular + discoid) & (cls < angular + discoid + rod)
    # 1. axis ratios — ZINGG'S FOUR CLASSES.  A river gravel population is not
    #    one ellipsoid with jitter: it is spheres, discs (b/a high, c/b low),
    #    blades and rods (b/a low), in real proportions, and the 4K macro of
    #    the first pass read as "beans in a tray" precisely because every
    #    pebble was the same triaxial shape at a different size.
    ax = np.empty((n, 3))
    ax[:, 0] = 1.0
    ax[:, 1] = axis[1] * (0.68 + 0.62 * _h(ii[:, 0], np.full(n, seed + 5)))
    ax[:, 2] = axis[2] * (0.52 + 0.82 * _h(ii[:, 0], np.full(n, seed + 7)))
    ax[is_disc, 2] *= 0.46
    ax[is_disc, 1] *= 1.22
    ax[is_rod, 1] *= 0.58
    ax[is_rod, 2] *= 0.72
    # 2. per-vertex radial jitter
    amp = np.where(is_ang, jitter * 2.9, jitter)[:, None]
    jit = 1.0 - amp + 2.0 * amp * _h(np.repeat(ii, k, 1),
                                     np.tile(jj, (n, 1)),
                                     np.full((n, k), seed + 11))
    V = BV[None, :, :] * jit[..., None] * ax[:, None, :]
    # 3. angular stones get flat fracture facets: push every vertex onto the
    #    nearest of three random planes, which is what a crushed stone is
    if np.any(is_ang):
        ia = np.nonzero(is_ang)[0]
        for pl in range(3):
            th = _h(ia, np.full(len(ia), seed + 21 + pl)) * 2 * math.pi
            ph = np.arccos(1.0 - 2.0 * _h(ia, np.full(len(ia), seed + 31 + pl)))
            nrm = np.stack([np.sin(ph) * np.cos(th), np.sin(ph) * np.sin(th),
                            np.cos(ph)], axis=1)
            off = 0.52 + 0.34 * _h(ia, np.full(len(ia), seed + 41 + pl))
            dot = np.einsum("ijk,ik->ij", V[ia], nrm)
            over = dot > off[:, None]
            corr = (dot - off[:, None]) * over
            V[ia] -= corr[:, :, None] * nrm[:, None, :]
    # normalise to `size` on the long axis, centre on the centroid
    V = V - V.mean(axis=1, keepdims=True)
    ext = np.abs(V).max(axis=(1, 2))
    V = V * (np.asarray(size, float).reshape(-1, 1, 1) * 0.5
             / np.maximum(ext, 1e-9).reshape(-1, 1, 1))
    return V, BF, dict(angular=is_ang, discoid=is_disc, rod=is_rod)


def _rot_apply(V, yaw, tilt, roll):
    """Rotate (n,k,3) by per-stone yaw about z, then tilt about x, then roll."""
    cy, sy = np.cos(yaw)[:, None], np.sin(yaw)[:, None]
    ct, st = np.cos(tilt)[:, None], np.sin(tilt)[:, None]
    cr, sr = np.cos(roll)[:, None], np.sin(roll)[:, None]
    x, y, z = V[..., 0], V[..., 1], V[..., 2]
    x1 = x * cr - y * sr
    y1 = x * sr + y * cr
    y2 = y1 * ct - z * st
    z2 = y1 * st + z * ct
    x3 = x1 * cy - y2 * sy
    y3 = x1 * sy + y2 * cy
    return np.stack([x3, y3, z2], axis=-1)

# =============================================================================
# 6.  LOD — the pixel rule, applied to mesh pitch and to pebble polygons
# =============================================================================
# ONE anchor: the lens position in world space.  Everything else follows from
# the distance to it, because that is what decides how many pixels a feature
# gets.  Move the anchor and the detail moves with the camera.

QUALITY = {
    # R_stone: how far from the LENS individual pebbles are still meshed.
    #          Beyond it the rake furrows (90-420 mm, 12-90 px at these ranges)
    #          carry the read, plus a packed-sphere displacement on the
    #          substrate and M_GBS_Bed's own voronoi cells.
    #  under     pitch inside the explicit-stone radius (the pebbles carry it)
    #  pitch_k    px rule outside it, metres of pitch per metre of range
    #  mid_cap    the MID-FIELD PLATEAU.  A tractor rake is 200-420 mm, so a
    #             75 mm mesh still carries three of its four passes out to
    #             mid_r; without the plateau the pitch ran away at 15 m and the
    #             bed went glass-smooth exactly where a real trap is all
    #             furrows.
    #  mid_r      where the plateau ends and pitch grows as r^1.45
    "hero":  dict(r_stone=9.6,  budget=1000000, pitch_k=0.0030, pitch_min=0.020,
                  mid_cap=0.040, mid_r=26.0, pitch_max=0.40, under=0.026,
                  chunk_half=26.0),
    "ultra": dict(r_stone=11.0, budget=2000000, pitch_k=0.0022, pitch_min=0.014,
                  mid_cap=0.028, mid_r=40.0, pitch_max=0.35, under=0.020,
                  chunk_half=32.0),
    "draft": dict(r_stone=9.6,  budget=110000, pitch_k=0.0090, pitch_min=0.055,
                  mid_cap=0.160, mid_r=16.0, pitch_max=0.90, under=0.075,
                  chunk_half=20.0),
}

STONE_MIN_PX = 3.6        # below this a pebble is not worth a triangle


def lod_pitch(r, q):
    """Substrate mesh pitch at `r` metres from the lens, metres.

    Inside the explicit-stone radius the substrate is the interstitial floor and
    is largely occluded by the pebbles standing on it, so it is deliberately
    COARSER there than just outside: the pebbles carry the detail, and the
    analytic surface is expressed by their SEATING at full precision, not by the
    tessellation under them.  Outside, the mesh is the only thing carrying the
    rake, so it goes fine and then grows with distance.
    """
    if r <= q["r_stone"]:
        return q["under"]
    p = float(np.clip(q["pitch_k"] * r, q["pitch_min"], q["mid_cap"]))
    if r > q["mid_r"]:
        p = min(q["mid_cap"] * (r / q["mid_r"]) ** 1.45, q["pitch_max"])
    return p


def _graded_axis(lo, hi, focus, h0, q, cap=200000):
    """Monotone samples over [lo, hi], dense near `focus`, from the pixel rule.

    `h0` is the lens's height above the surface, so a point directly under the
    lens is `h0` away, not 0 — which is what stops the pitch collapsing to
    nothing at the focus and generating a million rows nobody sees.
    """
    lo = float(lo); hi = float(hi)
    if hi - lo < 1e-6:
        return np.array([lo, hi])
    out = [min(max(focus, lo), hi)]
    x = out[0]
    while x < hi:
        x += lod_pitch(math.hypot(x - focus, h0), q)
        out.append(min(x, hi))
        if len(out) > cap:
            break
    x = out[0]
    left = []
    while x > lo:
        x -= lod_pitch(math.hypot(x - focus, h0), q)
        left.append(max(x, lo))
        if len(left) > cap:
            break
    a = np.array(sorted(set(left[::-1] + out)), float)
    a[0] = lo
    a[-1] = hi
    return np.unique(a)


def stone_template_for(size_m, r_m):
    """Which polyhedron a pebble of `size_m` at `r_m` from the lens gets."""
    px = size_m * (RES_X_4K * LENS_AT_CLOSEST_MM / SENSOR_MM) / max(r_m, 0.05)
    for k in TEMPLATE_ORDER:
        if px >= STONE_TEMPLATES[k]["min_px"]:
            return k, px
    return "tet", px


# =============================================================================
# 7.  MESH ASSEMBLY
# =============================================================================
class _MB:
    """Accumulates triangles + per-vertex float attributes, then emits."""

    def __init__(self, attrs):
        self.attrs = tuple(attrs)
        self.V = []
        self.F = []
        self.A = {a: [] for a in self.attrs}
        self.sm = []
        self.n = 0

    def add(self, V, F, attrs, smooth=True):
        V = np.asarray(V, np.float64).reshape(-1, 3)
        F = np.asarray(F, np.int64).reshape(-1, 3) + self.n
        self.V.append(V)
        self.F.append(F)
        for a in self.attrs:
            v = attrs.get(a, 0.0)
            self.A[a].append(np.broadcast_to(np.asarray(v, np.float32),
                                             (len(V),)).copy())
        self.sm.append(np.full(len(F), bool(smooth))
                       if np.ndim(smooth) == 0 else np.asarray(smooth, bool))
        self.n += len(V)

    @property
    def tris(self):
        return sum(len(f) for f in self.F)

    def emit(self, name, coll, mat):
        if not self.V or self.n == 0:
            return None
        V = np.concatenate(self.V)
        F = np.concatenate(self.F)
        sm = np.concatenate(self.sm)
        ctr = V.mean(axis=0)
        V = V - ctr                       # LAW 6: recentre on emit
        me = bpy.data.meshes.new(name)
        me.vertices.add(len(V))
        me.vertices.foreach_set("co", V.ravel().astype(np.float32))
        nf = len(F)
        me.loops.add(nf * 3)
        me.polygons.add(nf)
        me.polygons.foreach_set("loop_start", np.arange(nf, dtype=np.int32) * 3)
        me.polygons.foreach_set("loop_total", np.full(nf, 3, np.int32))
        me.loops.foreach_set("vertex_index", F.ravel().astype(np.int32))
        me.update()
        me.polygons.foreach_set("use_smooth", sm)
        for a in self.attrs:
            at = me.attributes.new(name=a, type="FLOAT", domain="POINT")
            at.data.foreach_set("value", np.concatenate(self.A[a]))
        me.validate(verbose=False)
        ob = bpy.data.objects.new(name, me)
        ob.location = Vector(ctr)
        me.materials.append(mat)
        coll.objects.link(ob)
        self.V = []; self.F = []; self.sm = []
        self.A = {a: [] for a in self.attrs}
        self.n = 0
        return ob


def _grid_faces(ni, nj, keep=None):
    """Triangles of an ni x nj tensor grid, row-major."""
    i = np.arange(ni - 1)[:, None]
    j = np.arange(nj - 1)[None, :]
    a = i * nj + j
    b = a + 1
    c = a + nj
    d = c + 1
    F = np.concatenate([np.stack([a, c, d], -1).reshape(-1, 3),
                        np.stack([a, d, b], -1).reshape(-1, 3)])
    if keep is not None:
        k = np.concatenate([keep.reshape(-1), keep.reshape(-1)])
        F = F[k]
    return F


def _bed_frame(S, side):
    """Unit (along-station, outboard, up) basis in world, per sample."""
    X, Y, H, _ = C.centreline_arrays(np.asarray(S, float))
    es = np.stack([np.cos(H), np.sin(H), np.zeros_like(H)], -1)
    ed = np.stack([-np.sin(H), np.cos(H), np.zeros_like(H)], -1) * float(side)
    return X, Y, es, ed


def _bed_world(bed, S, d):
    """(S, d) -> world xy on the centreline frame (z handled separately)."""
    S = np.asarray(S, float)
    lat = (inner_lat(bed, S) + np.asarray(d, float)) * bed.side
    X, Y, H, _ = C.centreline_arrays(S)
    return X - np.sin(H) * lat, Y + np.cos(H) * lat


def _bed_chunk(bed, s_axis, d_axis, q, sa, da, h0, mb, near_bed=True):
    """One substrate chunk: a tensor grid in (station, outboard offset).

    BAND-LIMITED AT MESH TIME.  ``bed_top_z`` is the analytic surface and stays
    exact for every caller; what a MESH may carry is bounded by its own pitch.
    A 0.20 m rake furrow sampled on a 0.45 m grid is not a coarse furrow, it is
    aliasing — low-frequency moiré that reads as blotching, which is exactly
    what the first world pass was rejected for.  So the rake and the packed-
    sphere displacement are faded out per vertex wherever the local pitch cannot
    carry them, and the shader picks them up instead.
    """
    ni, nj = len(s_axis), len(d_axis)
    S = np.repeat(s_axis[:, None], nj, 1)
    w = width(bed, s_axis)
    Wm = max(float(np.max(w)), 1e-6)
    D = d_axis[None, :] * (w[:, None] / Wm)
    ww = np.repeat(w[:, None], nj, 1)
    Z = bed_top_z(bed, S, D, ww)
    fd = fines_drop(bed)
    Z = Z - fd
    # local mesh pitch, per vertex, in metres
    ps = np.gradient(s_axis) if ni > 1 else np.array([1.0])
    pd = np.gradient(d_axis) * (Wm and 1.0) if nj > 1 else np.array([1.0])
    pitch = np.maximum(np.repeat(np.abs(ps)[:, None], nj, 1),
                       np.abs(pd)[None, :] * (w[:, None] / Wm))
    # --- band-limit the rake, per pass -------------------------------------
    dzr, ph, _fr = rake(bed, S, D, ww)
    dzr_bl, _ph, _f = rake(bed, S, D, ww, mesh_pitch=pitch)
    _dzs, amt, rr = disturbance(bed, S, D, ww)
    Z = Z - (dzr - dzr_bl) * (1.0 - rr)
    Xw, Yw = _bed_world(bed, S, D)
    # --- attributes ---------------------------------------------------------
    t = np.clip(D / np.maximum(ww, 1e-6), 0.0, 1.0)
    dep = _clamp01(dish(bed, S, t, ww) / max(bed.dish["depth"], 1e-6))
    br = _clamp01(berm(bed, S, t, ww) / max(bed.berm["h"], 1e-6))
    gg = bed.grading
    dus = _clamp01(gg["dust"] * (0.35 + 0.65 * ph) * (1.0 - 0.75 * amt)
                   * (0.55 + 0.65 * _fbm2(S / 2.6, D / 2.1,
                                          seed=bed.seed + 701, oct=3)))
    dmp = _clamp01(gg["damp"] * (0.30 + 0.85 * dep)
                   * (0.5 + 0.8 * _fbm2(S / 4.4, D / 3.1,
                                        seed=bed.seed + 703, oct=3)))
    # `gid` for the substrate is a SMOOTH 3 m tone field, not the dome cell
    # hash: see mat_bed.  A per-vertex random is useless to a shader that
    # interpolates it.
    tone = _fbm2(S / 3.4, D / 2.7, seed=bed.seed + 707, oct=4)
    keep = np.ones((ni - 1, nj - 1), bool)
    narrow = (w < 0.25)
    if np.any(narrow):
        keep &= ~(narrow[:-1, None] & narrow[1:, None])
    P = np.stack([Xw, Yw, Z], -1).reshape(-1, 3)
    mb.add(P, _grid_faces(ni, nj, keep),
           dict(dep=dep.ravel(), fur=ph.ravel(), dst=amt.ravel(),
                dus=dus.ravel(), dmp=dmp.ravel(), brm=br.ravel(),
                gid=tone.ravel()), smooth=True)
    return ni * nj


# =============================================================================
# 8.  THE SCATTER — 10^5 pebbles, each one its own polyhedron
# =============================================================================
def _tiers(bed):
    """Sieve tiers for this bed, and the areal density of each.

    The keep probabilities are not taste: a tier only shows where the coarser
    tiers have left a gap, so keep = exp(-coverage_of_everything_coarser).
    With d50 = 14 mm that lands at 1 665 + 2 685 + 2 350 = 6 700 visible stone
    tops per m2, which is what a monolayer of 9-22 mm gravel actually is.
    """
    g = bed.grading
    d50 = g["d50"]
    out = []
    cov = 0.0
    for (lo_k, hi_k, pitch_k) in ((1.45, SIZE_HI_K, 1.75),
                                  (0.85, 1.45, 1.05),
                                  (SIZE_LO_K, 0.85, 0.85)):
        lo, hi = lo_k * d50, hi_k * d50
        if hi < MESH_FLOOR_M:
            continue
        lo = max(lo, MESH_FLOOR_M)
        p = pitch_k * d50
        keep = math.exp(-cov)
        dens = keep / (p * p)
        mean_d = 0.5 * (lo + hi) * 0.86
        cov += dens * math.pi * 0.25 * mean_d * mean_d
        out.append(dict(lo=lo, hi=hi, pitch=p, keep=keep, dens=dens))
    return out


def _scatter(bed, q, sa, da, h0, budget, stats, rng_seed=0, view_sd=None,
             view_half_deg=72.0):
    """-> list of dicts, one per emitted pebble batch, in bed-local coords."""
    res = []
    R = q["r_stone"]
    if h0 > R:
        return res
    reach = math.sqrt(max(R * R - h0 * h0, 0.0))
    s_lo = max(bed.s0, sa - reach)
    s_hi = min(bed.s1, sa + reach)
    if s_hi - s_lo < 0.05:
        return res
    n_left = budget
    for ti, T in enumerate(_tiers(bed)):
        if n_left <= 0:
            break
        p = T["pitch"]
        d_lo = max(0.0, da - reach)
        d_hi = da + reach
        ns = int((s_hi - s_lo) / p) + 1
        nd = int((d_hi - d_lo) / p) + 1
        if ns < 1 or nd < 1:
            continue
        # a jittered lattice, generated in station bands so peak memory stays
        # bounded however big the hero patch is
        band = max(1, int(2.4e6 / max(nd, 1)))
        for b0 in range(0, ns, band):
            b1 = min(ns, b0 + band)
            gi = np.arange(b0, b1)[:, None]
            gj = np.arange(nd)[None, :]
            sd = bed.seed + 9001 + 137 * ti + rng_seed
            hs = _h(gi, gj, np.full((b1 - b0, nd), sd))
            hd = _h(gi, gj, np.full((b1 - b0, nd), sd + 1))
            hk = _h(gi, gj, np.full((b1 - b0, nd), sd + 2))
            hz = _h(gi, gj, np.full((b1 - b0, nd), sd + 3))
            Sp = s_lo + (gi + 0.12 + 0.76 * hs) * p
            Dp = d_lo + (gj + 0.12 + 0.76 * hd) * p
            Sp = np.broadcast_to(Sp, (b1 - b0, nd))
            Dp = np.broadcast_to(Dp, (b1 - b0, nd))
            ok = hk < T["keep"]
            wq = width(bed, Sp)
            ok &= (Sp >= bed.s0) & (Sp <= bed.s1)
            # NO PEBBLE CENTRE INSIDE THE KERBSTONE'S FOOTPRINT.  Measured on
            # the built mesh: with the limit at 0.0 the outermost vertex of a
            # pebble sitting on the lip line reached 8 mm INBOARD of
            # `verge_edge`, i.e. 8 mm into the racing surface's own corridor.
            # It is 45-95 mm below the datum there and physically under the
            # kerbstone, but `placement_gate` holds edge-defining families to
            # the true half-width -- at the boundary, never inside it -- so the
            # scatter starts 30 mm out and the strip belongs to
            # `gravel_retaining_kerb`, which is whose it is anyway.
            ok &= (Dp >= LIP_KEEPOUT_M) & (Dp <= wq)
            # distance from the LENS, in 3-space
            rr = np.sqrt((Sp - sa) ** 2 + (Dp - da) ** 2 + h0 * h0)
            # FADE, do not cut.  A hard radius put a visible circle of pebbles
            # on the bed in the 1280 x 720 context check.  The keep probability
            # ramps to zero over the last 1.60 m, and M_GBS_Bed's voronoi cell
            # field — whose cells ARE the pebble size — carries the surface from
            # there, so there is no boundary to find.
            pk = _clamp01((R - rr) / 1.60)
            if view_sd is not None:
                # FRUSTUM-AWARE LOD, and it is declared rather than hidden.
                # Pebbles are meshed in a +-72 deg fan about the lens axis, 45
                # deg wider each side than the 35 mm lens's own 27.2 deg half
                # angle, so nothing the shot can see is missing and nothing 100
                # deg behind the lens is paid for.  Pass view_world=None to get
                # the full disc; the assembly does that for a moving camera.
                dxs = Sp - sa
                dys = Dp - da
                rr2 = np.maximum(np.hypot(dxs, dys), 1e-6)
                ca = (dxs * view_sd[0] + dys * view_sd[1]) / rr2
                lim = math.cos(math.radians(view_half_deg))
                soft = _clamp01((ca - lim) / 0.14)
                pk = pk * np.maximum(soft, _clamp01((2.4 - rr2) / 0.8))
            ok &= hz < pk
            if not np.any(ok):
                continue
            Sp = Sp[ok]; Dp = Dp[ok]; rr = rr[ok]; hz = hz[ok]; wq = wq[ok]
            size = T["lo"] + (T["hi"] - T["lo"]) * hz ** 1.35
            # the pixel floor: nothing under STONE_MIN_PX is worth a triangle
            fl = np.maximum(MESH_FLOOR_M, STONE_MIN_PX * rr /
                            (RES_X_4K * LENS_AT_CLOSEST_MM / SENSOR_MM))
            m = size >= fl
            if not np.any(m):
                continue
            Sp = Sp[m]; Dp = Dp[m]; rr = rr[m]; size = size[m]; wq = wq[m]
            if len(Sp) > n_left:
                Sp = Sp[:n_left]; Dp = Dp[:n_left]; rr = rr[:n_left]
                size = size[:n_left]; wq = wq[:n_left]
            n_left -= len(Sp)
            res.append(dict(S=Sp, D=Dp, r=rr, size=size, w=wq, tier=ti))
            if n_left <= 0:
                break
    return res


def _emit_stones(bed, batches, mb, stats):
    """Turn scatter batches into unique polyhedra, seated on the bed."""
    if not batches:
        return 0
    gg = bed.grading
    d_hi = gg["d_hi"]
    lithcum = np.cumsum(gg["lith"])
    total = 0
    for bi, B in enumerate(batches):
        S, D, r, size, wq = B["S"], B["D"], B["r"], B["size"], B["w"]
        n = len(S)
        if n == 0:
            continue
        # split by template so each group is one homogeneous array op
        px = size * (RES_X_4K * LENS_AT_CLOSEST_MM / SENSOR_MM) / np.maximum(r, 0.05)
        # coarsest threshold FIRST so the finest template wins the overwrite;
        # doing it the other way round gave every pebble a tetrahedron
        tname = np.full(n, "tet", dtype=object)
        for k in reversed(TEMPLATE_ORDER):
            tname[px >= STONE_TEMPLATES[k]["min_px"]] = k
        # fields at the stone positions
        env = bed_top_z(bed, S, D, wq)
        _dz, ph, _fr = rake(bed, S, D, wq)
        _dzs, amt, _rr = disturbance(bed, S, D, wq)
        t = np.clip(D / np.maximum(wq, 1e-6), 0.0, 1.0)
        dep = _clamp01(dish(bed, S, t, wq) / max(bed.dish["depth"], 1e-6))
        seedv = np.full(n, bed.seed + 4001 + 71 * bi)
        kk = np.arange(n)
        gid = _h(kk, seedv)
        lit = np.searchsorted(lithcum, _h(kk, seedv + 5)) / len(lithcum) \
            + 0.5 / len(lithcum)
        # a graded packing: the coarse fraction defines the envelope and the
        # fines sit below it, so a small stone is nestled, never floating
        rel = (1.0 - np.clip(size / d_hi, 0.0, 1.0)) ** 1.20
        top = env - fines_drop(bed) * rel * 0.92 \
            + (_h(kk, seedv + 7) - 0.5) * 0.30 * gg["d50"]
        for k in TEMPLATE_ORDER:
            m = (tname == k)
            if not np.any(m):
                continue
            idx = np.nonzero(m)[0]
            nn = len(idx)
            sub = bed.seed + 5000 + 137 * bi + 17 * TEMPLATE_ORDER.index(k)
            V, F, cls = make_stones(nn, sub, size[idx], k,
                                    angular=gg["angular"], discoid=gg["discoid"])
            # imbrication: a settled pebble lies with its SHORT axis up.  A
            # disturbed one does not, which is what makes a scar read.
            dist = amt[idx]
            tilt = (0.07 + 0.30 * _h(idx, np.full(nn, sub + 21))) \
                * (1.0 + 2.6 * dist)
            tilt = np.minimum(tilt, 1.45)
            yaw = _h(idx, np.full(nn, sub + 23)) * 2 * math.pi
            roll = _h(idx, np.full(nn, sub + 25)) * 2 * math.pi
            V = _rot_apply(V, yaw, tilt, roll)
            half = V[..., 2].max(axis=1)
            emb = 0.40 + 0.38 * _h(idx, np.full(nn, sub + 27))
            zc = top[idx] - half * (2.0 * emb - 1.0)
            # world placement
            Ss, Dd = S[idx], D[idx]
            X, Y, H, _ = C.centreline_arrays(Ss)
            lat = (inner_lat(bed, Ss) + Dd) * bed.side
            px0 = X - np.sin(H) * lat
            py0 = Y + np.cos(H) * lat
            es = np.stack([np.cos(H), np.sin(H)], -1)
            ed = np.stack([-np.sin(H), np.cos(H)], -1) * bed.side
            Wx = px0[:, None] + V[..., 0] * es[:, 0:1] + V[..., 1] * ed[:, 0:1]
            Wy = py0[:, None] + V[..., 0] * es[:, 1:2] + V[..., 1] * ed[:, 1:2]
            Wz = zc[:, None] + V[..., 2]
            kv = V.shape[1]
            P = np.stack([Wx, Wy, Wz], -1).reshape(-1, 3)
            FF = (np.tile(F[None, :, :], (nn, 1, 1))
                  + (np.arange(nn) * kv)[:, None, None]).reshape(-1, 3)
            # per-stone attributes, replicated per vertex
            dus = _clamp01(gg["dust"] * (0.30 + 0.70 * ph[idx])
                           * (1.0 - 0.80 * dist)
                           * (0.45 + 0.75 * _h(idx, np.full(nn, sub + 31))))
            dmp = _clamp01(gg["damp"] * (0.25 + 0.90 * dep[idx])
                           * (0.40 + 0.90 * _h(idx, np.full(nn, sub + 33))))
            wrn = _clamp01((1.0 - t[idx]) ** 2.4 * 0.9
                           * (0.4 + 0.9 * _h(idx, np.full(nn, sub + 35))))
            rep = lambda a: np.repeat(a, kv)          # noqa: E731
            smooth = np.repeat(~cls["angular"], len(F))
            mb.add(P, FF,
                   dict(gid=rep(gid[idx]), lit=rep(lit[idx]), dus=rep(dus),
                        dmp=rep(dmp), emb=rep(emb), wrn=rep(wrn),
                        siz=rep(size[idx] / d_hi)),
                   smooth=smooth)
            stats["stones"] += nn
            stats["stone_tris"] += nn * len(F)
            stats["by_template"][k] = stats["by_template"].get(k, 0) + nn
            total += nn
    return total


# =============================================================================
# 9.  MATERIALS — all TexCoord->Object, all decorrelated by a baked attribute
# =============================================================================
def _mat(name):
    m = bpy.data.materials.get(name)
    if m:
        return m, None
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.node_tree.nodes.clear()
    return m, G(m.node_tree)


def _attr(g, name):
    a = g.n("ShaderNodeAttribute")
    a.attribute_name = name
    return a.outputs["Fac"]


def _obj_space(g, decorr=None, span=9.0):
    """``TexCoord -> Object`` plus a per-thing decorrelation offset.

    LAW 6, and the reason the first pass blotched.  Object coordinates keep
    |P| under ~45 m however far round the lap the chunk is.  But every pebble in
    a chunk would then share one noise field, so the offset is driven by the
    baked per-stone ``gid`` (or by Object Info Random for a whole object) —
    a per-thing scalar, never a world position.
    """
    tc = g.n("ShaderNodeTexCoord")
    if decorr is None:
        oi = g.n("ShaderNodeObjectInfo")
        decorr = oi.outputs["Random"]
    fr = lambda a, b: g.math("FRACT", g.math("MULTIPLY", a, b))   # noqa: E731
    off = g.comb(g.math("MULTIPLY", fr(decorr, 1.0), span),
                 g.math("MULTIPLY", fr(decorr, 7.13), span * 0.73),
                 g.math("MULTIPLY", fr(decorr, 3.71), span * 0.48))
    return g.vadd(tc.outputs["Object"], off), tc.outputs["Object"], decorr


def mat_stone():
    """One water-rounded pebble out of five quarries, seen at 0.75 mm/px.

    THE LAYERS, in cycles per metre against the stone's own object coordinate:

      lithology     --      five rocks, picked by the baked `lit`; each one has
                            its own colour, roughness and specular level
      per-stone tone --     a 0.74..1.30 GAIN on the finished colour, driven by
                            `gid`.  This is the single strongest cue that a bed
                            is 300 000 stones and not one stone: a mix toward
                            another grey can be undone by the next layer, a
                            multiply cannot.
      grain         640     the rock's own mottling
      micro         2400    the sub-millimetre tooth that catches the low sun
      crystal       1500    voronoi speckle, gated to the granite band
      banding       120     TexWave, gated to the quartzite band — bedding
                            planes in a river cobble are visible at 19 px
      pitting       900     voronoi F1, the weathered pockmarks
      dust          9 + 55  a pale coat, on UPWARD faces only (Geometry->Normal,
                            never Geometry->Position), scaled by `dus`
      damp          --      `dmp` darkens by up to 0.52 and drops roughness:
                            the bottom of the dish stays wet for days
      wear          --      `wrn` polishes the stones nearest the kerb, where
                            cars have run over them
      bedding dirt  --      `emb` puts soil round the waterline of every stone
    """
    m, g = _mat(MPFX + "Stone")
    if g is None:
        return m
    gid = _attr(g, "gid")
    lit = _attr(g, "lit")
    dus = _attr(g, "dus")
    dmp = _attr(g, "dmp")
    emb = _attr(g, "emb")
    wrn = _attr(g, "wrn")
    siz = _attr(g, "siz")
    P, Pl, _ = _obj_space(g, decorr=gid, span=11.0)

    mul = lambda a, b: g.math("MULTIPLY", a, b)          # noqa: E731
    add = lambda a, b: g.math("ADD", a, b)               # noqa: E731
    sub = lambda a, b: g.math("SUBTRACT", a, b)          # noqa: E731

    # ---- lithology ---------------------------------------------------------
    col = g.rgb(*_srgb(LITHOLOGY[0]["col"])[:3])
    rgh = 0.0
    rgh_n = g.math("MULTIPLY", g.band(lit, 0.0, 0.2, 0.02),
                   LITHOLOGY[0]["rough"])
    spc = g.math("MULTIPLY", g.band(lit, 0.0, 0.2, 0.02), LITHOLOGY[0]["spec"])
    for i in range(1, 5):
        b = g.band(lit, i * 0.2, (i + 1) * 0.2, 0.02)
        col = g.mixc(b, col, g.rgb(*_srgb(LITHOLOGY[i]["col"])[:3]))
        rgh_n = add(rgh_n, mul(b, LITHOLOGY[i]["rough"]))
        spc = add(spc, mul(b, LITHOLOGY[i]["spec"]))
    rgh = rgh_n

    # ---- the rock's own surface -------------------------------------------
    # THE FREQUENCIES ARE CHOSEN AGAINST THE PIXEL, and the first pass had them
    # an octave and a half too high.  At the macro station a 30 mm pebble is
    # 40 px, i.e. 1.16 px per millimetre, so the 640 and 2400 cycles/m layers
    # were 1.8 px and 0.5 px features: the first read as noise and the second
    # was pure aliasing.  A pebble's visible surface is its 2-3 mm grain, its
    # 1 mm tooth and its 15 mm mottling, so those are the three scales.
    grain, _ = g.noise(g.scale(P, 380.0), 1.0, detail=8.0, rough=0.60)
    micro, _ = g.noise(g.scale(P, 1300.0), 1.0, detail=6.0, rough=0.55)
    blot, _ = g.noise(g.scale(P, 62.0), 1.0, detail=7.0, rough=0.64, dist=0.9)
    cry = g.voro(g.scale(P, 900.0), 1.0, feature="F1", rand=1.0)
    crys = g.mr(cry.outputs["Distance"], 0.06, 0.34, 1.0, 0.0)
    pit = g.voro(g.scale(P, 420.0), 1.0, feature="F1", rand=0.95)
    pits = g.mr(pit.outputs["Distance"], 0.02, 0.30, 1.0, 0.0)
    wv = g.n("ShaderNodeTexWave", wave_type="BANDS", bands_direction="Z",
             wave_profile="SIN")
    g.set(wv.inputs["Vector"], P)
    g.set(wv.inputs["Scale"], 78.0)
    g.set(wv.inputs["Distortion"], 6.5)
    g.set(wv.inputs["Detail"], 3.0)
    band_q = mul(g.band(lit, 0.2, 0.4, 0.02),
                 g.mr(wv.outputs["Fac"], 0.25, 0.75, 0.0, 1.0))

    # darken/lighten the rock by its own grain, as a MULTIPLY so the mean holds
    tone = g.mr(grain, 0.24, 0.80, 0.64, 1.32)
    tone = mul(tone, g.mr(blot, 0.28, 0.74, 0.76, 1.24))
    col = g.vmulc(col, g.grey(tone))
    col = g.mixc(mul(g.band(lit, 0.4, 0.6, 0.02), mul(crys, 0.55)),
                 col, g.rgb(*_srgb("#d8d4cb")[:3]))
    col = g.mixc(mul(band_q, 0.40), col, g.rgb(*_srgb("#8d6f4c")[:3]))
    col = g.mixc(mul(pits, 0.30), col, g.rgb(*_srgb("#6f6a60")[:3]))

    # per-STONE tone gain — the layer that makes 300 000 stones not one stone
    pst = g.mr(g.math("FRACT", mul(gid, 17.7)), 0.0, 1.0, 0.66, 1.38)
    pst = mul(pst, g.mr(siz, 0.0, 1.0, 1.08, 0.90))   # big stones read darker
    col = g.vmulc(col, g.grey(pst))
    # ...and a per-stone WARM/COOL shift on top of the per-stone value.  Two
    # stones out of the same quarry are not the same colour: one has an iron
    # film on it and the one beside it has a manganese one, and a bed where
    # every pebble sits on the same hue is the giveaway a lens finds first.
    hsh = g.math("FRACT", mul(gid, 5.31))
    warm = g.n("ShaderNodeCombineColor")
    g.set(warm.inputs[0], g.mr(hsh, 0.0, 1.0, 1.10, 0.93))
    g.set(warm.inputs[1], g.mr(hsh, 0.0, 1.0, 1.02, 0.99))
    g.set(warm.inputs[2], g.mr(hsh, 0.0, 1.0, 0.86, 1.12))
    col = g.vmulc(col, warm.outputs[0])

    # ---- dust, on upward faces only ---------------------------------------
    geo = g.n("ShaderNodeNewGeometry")
    _nx, _ny, nz = g.sep(geo.outputs["Normal"])
    up = g.mr(nz, 0.18, 0.86, 0.0, 1.0)
    dmask, _ = g.noise(g.scale(P, 55.0), 1.0, detail=7.0, rough=0.60)
    dcoarse, _ = g.noise(g.scale(P, 9.0), 1.0, detail=6.0, rough=0.62, dist=0.6)
    dfac = mul(mul(dus, up), g.mr(mul(dmask, dcoarse), 0.16, 0.62, 0.15, 1.0))
    col = g.mixc(g.math("MULTIPLY", dfac, 0.92, clamp=True),
                 col, g.rgb(*_srgb("#c8bda4")[:3]))

    # ---- damp, wear, bedding dirt -----------------------------------------
    col = g.vmulc(col, g.grey(g.mr(dmp, 0.0, 1.0, 1.0, 0.48)))
    col = g.mixc(g.math("MULTIPLY", emb,
                        g.mr(nz, 0.35, -0.20, 0.0, 1.0), clamp=True),
                 col, g.rgb(*_srgb("#4a4034")[:3]))

    rough = mul(rgh, g.mr(micro, 0.2, 0.8, 0.86, 1.14))
    rough = add(rough, mul(dfac, 0.18))
    rough = sub(rough, mul(dmp, 0.26))
    rough = sub(rough, mul(wrn, 0.18))
    # a wet pebble is still a rough pebble: the floor is 0.22, not 0.055.  At
    # 0.055 the damp stones in the dish went to plastic under a 12.5 deg sun.
    rough = g.math("MINIMUM", g.math("MAXIMUM", rough, 0.22), 0.95)

    # ---- bump: 1.3 mm of grain and pitting ---------------------------------
    # The first pass ran the bump at 0.42 mm, which at 1.16 px/mm is half a
    # pixel: the 4K macro came back with pebbles that read as smooth ceramic.
    # A water-rounded pebble is not smooth at 2 mm — it is pitted, grained and
    # slightly faceted where it has been chipped — and 1.3 mm is that.
    hgt = add(mul(grain, 0.62), add(mul(micro, 0.22), mul(pits, 0.68)))
    nrm = g.bump(hgt, strength=0.85, distance=0.0013)
    nrm = g.bump(add(mul(micro, 0.7), mul(g.mr(crys, 0.0, 1.0, 0.0, 1.0), 0.5)),
                 strength=0.40, distance=0.00028, normal=nrm)

    bsdf = g.n("ShaderNodeBsdfPrincipled")
    g.set(bsdf.inputs["Base Color"], col)
    g.set(bsdf.inputs["Roughness"], rough)
    g.set(bsdf.inputs["Specular IOR Level"], spc)
    g.set(bsdf.inputs["Normal"], nrm)
    g.set(bsdf.inputs["Diffuse Roughness"], 0.35)
    out = g.n("ShaderNodeOutputMaterial")
    g.nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return m


def mat_bed():
    """The bed itself: the sand-and-fines floor between the pebbles, and — past
    the explicit-stone radius — the packed gravel as a shader.

    The far surface is NOT a noise.  It is a voronoi CELL FIELD at 62 cells/m
    (16 mm) with the cell's own hash driving its tone and the distance-to-edge
    driving the interstitial shadow, which is the same statistic the meshed
    pebbles produce at close range.  That is why the crossfade at R_STONE does
    not show: on both sides of it the surface is a packing of 16 mm stones with
    the same size, the same tone spread and the same interstitial darkness.

      cells         62      the pebbles themselves
      fine cells    185     the fraction between them
      interstice    --      DISTANCE_TO_EDGE -> the shadow between stones
      fines         420     the sand that has washed down between them
      dust          3.5     wind-blown, pooled in the rake troughs via `fur`
      damp          --      `dmp`
      churn         --      `dst` turns fresh unweathered rock up, which is
                            DARKER and less dusty than the sun-bleached top
      berm          --      `brm` the piled edge is looser and paler
      depth         --      `dep` the dish bottom holds water and silt
    """
    m, g = _mat(MPFX + "Bed")
    if g is None:
        return m
    dep = _attr(g, "dep")
    fur = _attr(g, "fur")
    dst = _attr(g, "dst")
    dus = _attr(g, "dus")
    dmp = _attr(g, "dmp")
    brm = _attr(g, "brm")
    gid = _attr(g, "gid")            # a SMOOTH metre-scale field, see below
    # LAW 6, AND THE BUG THE CONTEXT RENDER FOUND.  The first version offset the
    # texture coordinate by the baked `gid`, which for the substrate was a
    # per-VERTEX random (the dome field's cell hash).  A per-vertex random
    # interpolates across every face, so the offset varied by metres inside a
    # single triangle, every procedural in the graph became white noise at pixel
    # scale, and 37 000 m2 of gravel rendered as flat pale cream.  The
    # decorrelation for an OBJECT must be constant over the object: Object Info
    # Random.  `gid` is now a smooth 3 m field and is used as a TONE, never as a
    # coordinate.
    P, Pl, _ = _obj_space(g, span=6.0)

    mul = lambda a, b: g.math("MULTIPLY", a, b)          # noqa: E731
    add = lambda a, b: g.math("ADD", a, b)               # noqa: E731
    sub = lambda a, b: g.math("SUBTRACT", a, b)          # noqa: E731

    v1 = g.voro(g.scale(P, 62.0), 1.0, feature="F1", rand=0.95)
    v1e = g.voro(g.scale(P, 62.0), 1.0, feature="DISTANCE_TO_EDGE", rand=0.95)
    v2 = g.voro(g.scale(P, 185.0), 1.0, feature="F1", rand=0.92)
    v2e = g.voro(g.scale(P, 185.0), 1.0, feature="DISTANCE_TO_EDGE", rand=0.92)
    fines, _ = g.noise(g.scale(P, 420.0), 1.0, detail=8.0, rough=0.56)
    mott, _ = g.noise(g.scale(P, 3.5), 1.0, detail=7.0, rough=0.62, dist=0.8)
    silt, _ = g.noise(g.scale(P, 26.0), 1.0, detail=7.0, rough=0.58)

    # per-cell tone: the SAME 0.74..1.30 spread the meshed pebbles get
    c1 = g.sep(v1.outputs["Color"])[0]
    c2 = g.sep(v2.outputs["Color"])[0]
    # THE FAR BED MUST BE THE SAME ROCK AS THE NEAR BED, AND AS DARK AS A ROUGH
    # SURFACE ACTUALLY IS.  Two corrections, both from renders.  The first
    # version's base was #b2a68d and the 1920 x 1080 context frame showed the
    # explicit-pebble patch as a dark disc on a cream field.  Taking it to the
    # pebbles' own albedo was still not enough: a monolayer of pebbles under a
    # 12.5 deg sun SHADOWS ITSELF, and the area-averaged radiance of the meshed
    # field measured 0.319 against 0.411 for the flat shader beside it.  The
    # shader stands in for the whole rough surface, not for one stone's face, so
    # it carries that self-shadowing as a lower base -- which is what a
    # macro-scale BRDF for a rough surface IS.  These three are the dominant
    # limestone, the minority granite and the shadowed interstice of the SAME
    # palette M_GBS_Stone uses, taken down by the measured 0.78.
    base = g.rgb(*_srgb("#7f7466")[:3])
    base = g.mixc(g.mr(c2, 0.0, 1.0, 0.0, 0.60), base,
                  g.rgb(*_srgb("#68625b")[:3]))
    base = g.mixc(g.mr(mul(c1, c1), 0.0, 1.0, 0.0, 0.80), base,
                  g.rgb(*_srgb("#48443c")[:3]))
    base = g.vmulc(base, g.grey(g.mr(c1, 0.0, 1.0, 0.70, 1.34)))
    base = g.vmulc(base, g.grey(g.mr(fines, 0.25, 0.78, 0.86, 1.14)))
    base = g.vmulc(base, g.grey(g.mr(mott, 0.28, 0.74, 0.85, 1.15)))
    # the metre-scale tone of a bed that has been walked, raked and rained on
    base = g.vmulc(base, g.grey(g.mr(gid, 0.22, 0.78, 0.88, 1.14)))

    # the interstitial shadow — what tells a lens this is stones, not a slab
    inter = mul(g.mr(v1e.outputs["Distance"], 0.0, 0.16, 1.0, 0.0),
                g.mr(v2e.outputs["Distance"], 0.0, 0.10, 1.0, 0.0))
    base = g.vmulc(base, g.grey(g.mr(inter, 0.0, 1.0, 1.0, 0.38)))

    # sand and dust pooled in the rake troughs (fur = 0 in a trough)
    dpool = mul(dus, g.mr(fur, 0.85, 0.15, 0.25, 1.0))
    dpool = mul(dpool, g.mr(silt, 0.30, 0.70, 0.30, 1.0))
    base = g.mixc(g.math("MULTIPLY", dpool, 0.52, clamp=True), base,
                  g.rgb(*_srgb("#8e836d")[:3]))
    # churned ground: fresh rock and soil, darker than the bleached top
    base = g.mixc(g.math("MULTIPLY", dst, 0.62, clamp=True), base,
                  g.rgb(*_srgb("#6c6152")[:3]))
    # the piled berm is looser and paler; the dish bottom is silted and damp
    base = g.mixc(g.math("MULTIPLY", brm, 0.28, clamp=True), base,
                  g.rgb(*_srgb("#968c78")[:3]))
    base = g.vmulc(base, g.grey(g.mr(mul(dep, dmp), 0.0, 1.0, 1.0, 0.50)))
    base = g.vmulc(base, g.grey(g.mr(dmp, 0.0, 1.0, 1.0, 0.62)))

    rough = g.mr(fines, 0.2, 0.8, 0.74, 0.94)
    rough = add(rough, mul(dpool, 0.10))
    rough = sub(rough, mul(dmp, 0.26))
    rough = g.math("MINIMUM", g.math("MAXIMUM", rough, 0.10), 0.98)

    hgt = add(mul(g.mr(v1e.outputs["Distance"], 0.0, 0.20, 0.0, 1.0), 0.62),
              add(mul(g.mr(v2e.outputs["Distance"], 0.0, 0.12, 0.0, 1.0), 0.26),
                  mul(fines, 0.22)))
    nrm = g.bump(hgt, strength=0.85, distance=0.0034)
    nrm = g.bump(fines, strength=0.30, distance=0.00018, normal=nrm)

    bsdf = g.n("ShaderNodeBsdfPrincipled")
    g.set(bsdf.inputs["Base Color"], base)
    g.set(bsdf.inputs["Roughness"], rough)
    g.set(bsdf.inputs["Specular IOR Level"], 0.24)
    g.set(bsdf.inputs["Normal"], nrm)
    g.set(bsdf.inputs["Diffuse Roughness"], 0.45)
    out = g.n("ShaderNodeOutputMaterial")
    g.nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return m


# =============================================================================
# 10.  BUILD
# =============================================================================
def _collection(name, parent=None):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(c)
    return c


def _clear():
    for ob in [o for o in bpy.data.objects if o.name.startswith(PFX)]:
        bpy.data.objects.remove(ob, do_unlink=True)
    for me in [m for m in bpy.data.meshes if m.users == 0]:
        bpy.data.meshes.remove(me)


def _lens_frame(bed, A):
    """-> (lens station in THIS bed's frame, lens outboard offset, lens height
    above the local ground, true 3-D distance from the lens to the bed).

    The station is UNWRAPPED toward this bed and NOT clipped into it: clipping
    it would put the fine-pitch focus at the bed's own end whenever the lens was
    somewhere else on the lap, and hand a 300 m-distant bed a 20 mm mesh.  That
    is a 40-million-vertex mistake and it is why this is a function.
    """
    A = np.asarray(A, float)
    S0, d0, _in = bed_local(bed, np.array([A[0]]), np.array([A[1]]))
    sa = float(S0[0])
    mid = 0.5 * (bed.s0 + bed.s1)
    sa += C.LAP * round((mid - sa) / C.LAP)
    da = float(d0[0])
    sc = float(np.clip(sa, bed.s0, bed.s1))
    gz = float(C.ground_z(np.array([sc]), inner_lat(bed, np.array([sc])),
                          bed.side)[0])
    h0 = max(0.45, abs(float(A[2]) - gz))
    # the true nearest distance, measured over the bed rather than assumed
    Sq = np.arange(bed.s0, bed.s1 + 2.0, 2.0)
    r0q, wq = bed.radii(Sq)
    best = 1e9
    for f in (0.0, 0.25, 0.5, 0.75, 1.0):
        lat = r0q + wq * f
        P = np.asarray(C.su_to_world(Sq, lat, bed.side), float)
        best = min(best, float(np.linalg.norm(P - A[None, :], axis=1).min()))
    return sa, da, h0, best


HERO_SITE = dict(bid="OR0854", s=985.0, note="T4 hairpin outside bed — 30 m "
                                             "wide, 6 985 m2, the biggest and "
                                             "deepest on the lap, and the bed "
                                             "the 10.6 s static hairpin "
                                             "vantage looks straight across")


def hero_anchor(bid=None, s=None, inset=2.24, height=1.62):
    """The default LOD anchor: a lens on the track edge looking into the bed."""
    b = bed_by_id(bid or HERO_SITE["bid"])
    ss = float(s if s is not None else HERO_SITE["s"])
    lat = float(inner_lat(b, np.array([ss]))[0]) - inset
    P = C.su_to_world(np.array([ss]), np.array([lat]), b.side)
    z = float(C.ground_z(np.array([ss]), np.array([lat]), b.side)[0])
    return (float(P[0, 0]), float(P[0, 1]), z + height), b


def build(anchor_world=None, quality="hero", beds_wanted=None, seed=SEED,
          budget=None, verbose=True, view_world=None, view_half_deg=72.0):
    """Emit every gravel bed.

    ``anchor_world``  the LENS POSITION.  Mesh pitch, the explicit-pebble radius
                      and the per-pebble polygon budget all follow from the
                      distance to it.
    ``view_world``    optional (x, y) of the lens axis.  Given, pebbles are
                      meshed only in a +-``view_half_deg`` fan about it (72 deg
                      by default, against the 35 mm lens's own 27.2 deg half
                      angle).  Omit it for a moving camera and get the full
                      disc at 2.6x the triangles.
    """
    t0 = time.time()
    q = dict(QUALITY[quality])
    if budget:
        q["budget"] = int(budget)
    _clear()
    root = _collection(COLL_NAME)
    c_bed = _collection(COLL_NAME + "_Beds", root)
    c_stn = _collection(COLL_NAME + "_Stones", root)
    m_bed, m_stn = mat_bed(), mat_stone()

    if anchor_world is None:
        anchor_world, _hb = hero_anchor()
    A = np.array(anchor_world, float)

    BS = beds() if beds_wanted is None else [bed_by_id(b) for b in beds_wanted]
    stats = dict(item=ITEM_ID, quality=quality, beds=len(BS), objects=0,
                 verts=0, tris=0, stones=0, stone_tris=0, by_template={},
                 anchor=[round(v, 3) for v in anchor_world], per_bed=[])

    for bed in BS:
        sa, da, h0, far = _lens_frame(bed, A)
        # a bed 300 m away gets background pitch and no explicit stones, which
        # is correct: at 300 m a 14 mm pebble is 0.17 px.
        near_bed = far < q["r_stone"] + 2.0

        wmax = bed.wmax
        # THE PITCH MUST SEE THE WHOLE 3-D DISTANCE, not one axis of it.  A bed
        # 467 m round the lap has a lens projection somewhere in its own frame,
        # and grading the lateral axis on |d - da| alone handed it a 90 mm mesh
        # for a surface 0.4 px across.  So each axis carries the OTHER axis's
        # standoff in its effective height.
        ds_min = max(0.0, bed.s0 - sa, sa - bed.s1)
        dd_min = max(0.0, 0.0 - da, da - wmax)
        h_d = math.hypot(h0, ds_min)
        h_s = math.hypot(h0, dd_min)
        d_axis = _graded_axis(0.0, wmax, da, h_d, q)
        # chunk along s (law 7); the chunk containing the lens is the hero chunk
        cuts = [bed.s0]
        if near_bed:
            for x in (sa - q["chunk_half"], sa + q["chunk_half"]):
                if bed.s0 + 4.0 < x < bed.s1 - 4.0:
                    cuts.append(x)
        cuts.append(bed.s1)
        cuts = sorted(set(cuts))
        exp2 = []
        for a0, a1 in zip(cuts[:-1], cuts[1:]):
            n = max(1, int(math.ceil((a1 - a0) / CHUNK_S_M)))
            exp2 += list(np.linspace(a0, a1, n + 1))
        cuts = sorted(set(round(v, 6) for v in exp2))

        mb = _MB(ATTRS_BED)
        nv = 0
        for ci, (a0, a1) in enumerate(zip(cuts[:-1], cuts[1:])):
            s_axis = _graded_axis(a0, a1, sa, h_s, q)
            nv += _bed_chunk(bed, s_axis, d_axis, q, sa, da, h0, mb,
                             near_bed=near_bed)
            tri = mb.tris
            ob = mb.emit("%sBed_%s_c%02d" % (PFX, bed.bid, ci), c_bed, m_bed)
            if ob is not None:
                stats["objects"] += 1
                stats["tris"] += tri
        stats["verts"] += nv

        ns = 0
        if near_bed:
            mbs = _MB(ATTRS_STONE)
            vsd = None
            if view_world is not None:
                X, Y, H, _ = C.centreline_arrays(np.array([sa]))
                es = np.array([math.cos(H[0]), math.sin(H[0])])
                ed = np.array([-math.sin(H[0]), math.cos(H[0])]) * bed.side
                v = np.array(view_world[:2], float)
                v = v / max(np.linalg.norm(v), 1e-9)
                vsd = np.array([float(v @ es), float(v @ ed)])
                vsd = vsd / max(np.linalg.norm(vsd), 1e-9)
            batches = _scatter(bed, q, sa, da, h0, q["budget"], stats,
                               view_sd=vsd, view_half_deg=view_half_deg)
            ns = _emit_stones(bed, batches, mbs, stats)
            if ns:
                # chunk the stones too: one object per ~180 k pebbles
                tri = mbs.tris
                ob = mbs.emit("%sStones_%s" % (PFX, bed.bid), c_stn, m_stn)
                if ob is not None:
                    stats["objects"] += 1
                    stats["tris"] += tri
        stats["per_bed"].append(dict(
            bid=bed.bid, kind=bed.kind, side=bed.side,
            s=[round(bed.s0, 1), round(bed.s1, 1)],
            wmax=round(bed.wmax, 2), area_m2=round(bed.area_m2, 1),
            lens_m=round(far, 2), grid_verts=nv, stones=ns,
            dish_m=round(bed.dish["depth"], 4),
            rake=bed.rake["passes"][-1]["mode"],
            rake_pitch_mm=round(bed.rake["passes"][-1]["pitch"] * 1000, 1),
            rake_passes=bed.rake["n"], fresh=round(bed.rake["fresh"], 3),
            berm_mm=round(bed.berm["h"] * 1000, 1),
            scars=bed.scars["n"],
            scar_kinds=sorted(set(i["kind"] for i in bed.scars["items"])),
            d50_mm=round(bed.grading["d50"] * 1000, 2)))
        if verbose:
            print(">>   %-8s %-5s side%+d  %6.0f m2  lens %7.2f m  "
                  "grid %8d v  stones %8d" % (bed.bid, bed.kind, bed.side,
                                              bed.area_m2, far, nv, ns))
    stats["build_s"] = round(time.time() - t0, 1)
    if verbose:
        print(">> built %d objects, %d triangles, %d pebbles in %.1f s"
              % (stats["objects"], stats["tris"], stats["stones"],
                 stats["build_s"]))
        print(">> pebble templates: %s" % stats["by_template"])
    return stats

# =============================================================================
# 11.  THE TEST SCENE — the manifest's own 2.8 m on its own 35 mm lens
# =============================================================================
CAM_PITCH_DEG = 34.0
CAM_HEIGHT_M = 1.62


def apply_contract_sky():
    """Force the Sky Texture onto the contract's atmosphere.  MUST be called
    after any procedural_world(), including the one inside save_clean: that
    helper writes its own numbers, one of which does not exist in this Blender
    (`dust_density`; it is `aerosol_density`) and three of which are wrong for
    this contract."""
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
    """The one sun the whole film is lit by: 12.471 deg elevation, -57.970 deg
    bearing, 4.5222 of horizontal shadow per unit of height.  A 5 mm pebble
    throws 22.6 mm; that ratio is why this item is geometry."""
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
    print(">> sun: elev %.3f deg  bearing %.3f deg  energy %.3f  shadow ratio "
          "%.4f" % (C.SUN_ELEV_DEG, C.SUN_BEARING_DEG, C.SUN_ENERGY,
                    C.SUN_SHADOW_RATIO))
    return ob


def _sun_az_deg():
    d = np.array(C.SUN_DIR, float)
    return math.degrees(math.atan2(d[1], d[0]))


def choose_shot(bed, verbose=True):
    """Pick the station the macro is filmed at, and say why.

    A macro that happens to land on plain raked gravel proves one of the four
    declared axes.  "It is in the code" is not evidence, so the station is
    CHOSEN, by score, to put a recovery scar, the deep part of the dish and a
    cross-sun rake angle in the same frame — and the score is printed.
    """
    S = np.arange(bed.s0 + 8.0, bed.s1 - 8.0, 1.0)
    if len(S) < 3:
        S = np.array([0.5 * (bed.s0 + bed.s1)])
    r0, w = bed.radii(S)
    # the outboard direction in world, at each station
    _X, _Y, H, _ = C.centreline_arrays(S)
    outb = np.degrees(np.arctan2(np.cos(H) * bed.side, -np.sin(H) * bed.side))
    rel = np.abs(((outb - _sun_az_deg() + 180.0) % 360.0) - 180.0)
    # 95..150 deg between the view axis and the sun: the sun crosses the frame
    # low from behind-left, so every pebble's shadow runs toward the lens and
    # every rake furrow is a 68 mm shadow bar.  Straight into the sun blows out;
    # straight down-sun flattens.
    sun_score = np.exp(-0.5 * ((rel - 122.0) / 26.0) ** 2)
    d_deep = dish(bed, S, np.full(len(S), bed.dish["t_deep"]), w)
    deep_score = d_deep / max(float(d_deep.max()), 1e-6)
    # THE SCAR TERM IS MEASURED IN THE FRAME, not near it.  The first version
    # scored proximity to a scar's declared station with a 7 m sigma, and the
    # macro it chose put the bed's one recovery scar 26 m outboard of a frame
    # that is 4.7 m deep.  A shot that contains none of a declared variation
    # axis proves none of it.  This samples `disturbance` over the ACTUAL
    # footprint the 35 mm lens covers at 2.8 m and scores what is in it.
    fs = np.linspace(-3.4, 3.4, 9)
    fd = np.linspace(0.15, 5.0, 11)
    FS, FD = np.meshgrid(fs, fd, indexing="ij")
    scar_score = np.zeros(len(S))
    for i, ss in enumerate(S):
        _dz, amt, rr = disturbance(bed, ss + FS, FD)
        scar_score[i] = float(np.maximum(amt, 0.75 * rr).mean() * 3.2)
    scar_score = np.clip(scar_score, 0.0, 1.0)
    wide = w / max(float(w.max()), 1e-6)
    score = 0.30 * sun_score + 0.34 * scar_score + 0.18 * deep_score + 0.18 * wide
    i = int(np.argmax(score))
    why = dict(s=float(S[i]), score=round(float(score[i]), 4),
               sun_to_view_deg=round(float(rel[i]), 1),
               sun_term=round(float(sun_score[i]), 3),
               scar_term=round(float(scar_score[i]), 3),
               deep_term=round(float(deep_score[i]), 3),
               width_m=round(float(w[i]), 2),
               dish_here_m=round(float(d_deep[i]), 4),
               scars_in_frame=[it["kind"] for it in bed.scars["items"]
                               if abs(it["s"] - S[i]) < 26.0])
    if verbose:
        print(">> shot chosen on %s at s = %.1f: %s" % (bed.bid, S[i], why))
    return float(S[i]), why


def _look_matrix(cam_p, tgt):
    fwd = (Vector(tgt) - Vector(cam_p)).normalized()
    right = fwd.cross(Vector((0.0, 0.0, 1.0)))
    if right.length < 1e-6:
        right = Vector((1.0, 0.0, 0.0))
    right.normalize()
    up = right.cross(fwd).normalized()
    M = Matrix((right, up, -fwd)).transposed().to_4x4()
    return Matrix.Translation(Vector(cam_p)) @ M


def camera_pose(bed, s_shot, near=NEAREST_CAMERA_M, pitch_deg=CAM_PITCH_DEG,
                lens=LENS_AT_CLOSEST_MM):
    """Lens over the runoff, looking outboard across the bed.

    WHICH DISTANCE 2.8 m IS, AND WHY THE FIRST SOLVE HAD IT WRONG.  The manifest
    derives ``nearest_camera_m`` as the minimum over the camera corridor.  The
    first version of this function put the lens 2.8 m ABOVE the lip line, which
    satisfies the number and films the wrong thing: the ground directly under
    the lens is 2.8 m away and OUT OF FRAME below the bottom edge, so the frame
    itself started 4.2 m out and the whole explicit-stone band sat behind the
    camera.  The 640 x 360 check came back a flat brown wash, which is what a
    correctly-built gravel bed looks like when you photograph the part of it
    that was never built.

    So the lens is set BACK over the asphalt by ``inset`` and up by ``h`` with

        inset = near * cos(pitch + vhalf)      h = near * sin(pitch + vhalf)

    which puts the retaining lip EXACTLY on the bottom edge of the frame at
    EXACTLY ``near`` metres slant, and nothing built is closer.  The frame then
    runs from the lip at 1333 px/m to d = 4.9 m at 533 px/m, and every pixel of
    it is gravel that exists as geometry.
    """
    vhalf = math.degrees(math.atan(0.5 * SENSOR_MM * 2160 / 3840 / lens))
    bot = pitch_deg + vhalf
    top = pitch_deg - vhalf
    inset = near * math.cos(math.radians(bot))
    h = near * math.sin(math.radians(bot))
    lat0 = float(inner_lat(bed, np.array([s_shot]))[0])
    Pc = C.su_to_world(np.array([s_shot]), np.array([lat0 - inset]), bed.side)
    zc = float(C.ground_z(np.array([s_shot]), np.array([lat0 - inset]),
                          bed.side)[0])
    cam = (float(Pc[0, 0]), float(Pc[0, 1]), zc + h)
    d_aim = h / math.tan(math.radians(pitch_deg)) - inset
    Pa = C.su_to_world(np.array([s_shot]), np.array([lat0 + d_aim]), bed.side)
    za = float(bed_top_z(bed, np.array([s_shot]), np.array([d_aim]))[0])
    tgt = (float(Pa[0, 0]), float(Pa[0, 1]), za)
    d_top = h / math.tan(math.radians(max(top, 0.4))) - inset
    return cam, tgt, dict(
        vhalf_deg=round(vhalf, 3), pitch_deg=pitch_deg,
        frame_bottom_deg=round(bot, 2), frame_top_deg=round(top, 2),
        lens_inset_m=round(inset, 4), lens_height_m=round(h, 4),
        d_at_frame_bottom_m=0.0, d_at_frame_centre_m=round(d_aim, 3),
        d_at_frame_top_m=round(d_top, 2),
        slant_at_frame_centre_m=round(math.hypot(d_aim + inset, h), 3),
        slant_at_frame_top_m=round(math.hypot(d_top + inset, h), 2),
        px_per_m_at_frame_top=round(RES_X_4K * lens / SENSOR_MM /
                                    max(math.hypot(d_top + inset, h), 1e-3), 1))


def context_camera(scene, bed, s_shot, name="CAM_GBS_Context"):
    """NOT the acceptance shot — a wider vantage so the dish, the berm and the
    scars can be looked at as well as the 4.9 m the 35 mm macro reaches."""
    lat0 = float(inner_lat(bed, np.array([s_shot]))[0])
    h = 4.6
    inset = 5.5
    Pc = C.su_to_world(np.array([s_shot - 14.0]), np.array([lat0 - inset]),
                       bed.side)
    zc = float(C.ground_z(np.array([s_shot - 14.0]), np.array([lat0 - inset]),
                          bed.side)[0])
    d_aim = 13.0
    Pa = C.su_to_world(np.array([s_shot + 8.0]), np.array([lat0 + d_aim]),
                       bed.side)
    za = float(bed_top_z(bed, np.array([s_shot + 8.0]),
                         np.array([d_aim]))[0])
    cd = bpy.data.cameras.get(name) or bpy.data.cameras.new(name)
    cd.lens = 35.0
    cd.sensor_width = SENSOR_MM
    cd.clip_start = 0.02
    cd.clip_end = 4000.0
    ob = bpy.data.objects.get(name)
    if ob is None:
        ob = bpy.data.objects.new(name, cd)
        scene.collection.objects.link(ob)
    ob.matrix_world = _look_matrix((float(Pc[0, 0]), float(Pc[0, 1]), zc + h),
                                   (float(Pa[0, 0]), float(Pa[0, 1]), za))
    return ob


def measure_nearest(cam):
    """Distance from the lens to the nearest GBS_ vertex ACTUALLY BUILT.

    A claim about the filmed distance that is not this number is a claim about
    the intent, not the artefact (R2-017).
    """
    deps = bpy.context.evaluated_depsgraph_get()
    cp = np.array(cam.matrix_world.translation, float)
    best, who = 1e9, ""
    for ob in bpy.context.scene.objects:
        if ob.type != "MESH" or not ob.name.startswith(PFX):
            continue
        me = ob.data
        n = len(me.vertices)
        if not n:
            continue
        co = np.empty(n * 3, np.float32)
        me.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3).astype(np.float64)
        M = np.array(ob.matrix_world.to_4x4(), float)
        co = co @ M[:3, :3].T + M[:3, 3]
        d = float(np.linalg.norm(co - cp, axis=1).min())
        if d < best:
            best, who = d, ob.name
    return best, who


REF_PFX = "REF_"


def reference_ground(bed, s0, s1, name="REF_Runoff"):
    """A STAND-IN, and labelled one.  Not part of this item and deliberately
    outside the ``GBS_`` prefix the gate measures.

    The macro looks across the retaining lip, so the bottom of the frame is the
    runoff surface the bed is let into — which belongs to ``runoff_asphalt_mat``
    and ``gravel_retaining_kerb``, not to this module.  With nothing there the
    frame bottom rendered black and eight per cent of the acceptance shot was an
    absence rather than a surface.  This is a flat strip on ``C.ground_z`` in a
    plain matte, so the lip interface can be SEEN and judged.  It carries no
    detail on purpose: anything that looked finished here would be this module
    claiming ground it does not own.
    """
    m = bpy.data.materials.get(REF_PFX + "Mat")
    if m is None:
        m = bpy.data.materials.new(REF_PFX + "Mat")
        m.use_nodes = True
        nt = m.node_tree
        b = nt.nodes.get("Principled BSDF")
        if b:
            b.inputs["Base Color"].default_value = (0.055, 0.052, 0.050, 1.0)
            b.inputs["Roughness"].default_value = 0.72
    S = np.arange(s0, s1 + 1.0, 1.0)
    r0 = inner_lat(bed, S)
    w = width(bed, S)
    rows = []
    for (a, b_) in ((-9.0, -0.02), (0.02, 0.0)):
        pass
    strips = [np.linspace(-9.0, -0.015, 26)]
    strips.append(None)                      # outboard strip, width-relative
    V = []
    F = []
    n = 0
    for si, DD in enumerate(strips):
        if DD is None:
            D = np.stack([w + f for f in np.linspace(0.02, 12.0, 20)], axis=1)
        else:
            D = np.repeat(DD[None, :], len(S), 0)
        nj = D.shape[1]
        SS = np.repeat(S[:, None], nj, 1)
        lat = (r0[:, None] + D) * bed.side
        X, Y, H, _ = C.centreline_arrays(SS)
        px = X - np.sin(H) * lat
        py = Y + np.cos(H) * lat
        pz = C.ground_z(SS, np.abs(r0[:, None] + D), bed.side)
        V.append(np.stack([px, py, pz], -1).reshape(-1, 3))
        F.append(_grid_faces(len(S), nj) + n)
        n += len(S) * nj
    V = np.concatenate(V)
    F = np.concatenate(F)
    ctr = V.mean(axis=0)
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(V))
    me.vertices.foreach_set("co", (V - ctr).ravel().astype(np.float32))
    nf = len(F)
    me.loops.add(nf * 3)
    me.polygons.add(nf)
    me.polygons.foreach_set("loop_start", np.arange(nf, dtype=np.int32) * 3)
    me.polygons.foreach_set("loop_total", np.full(nf, 3, np.int32))
    me.loops.foreach_set("vertex_index", F.ravel().astype(np.int32))
    me.update()
    me.validate(verbose=False)
    ob = bpy.data.objects.new(name, me)
    ob.location = Vector(ctr)
    me.materials.append(m)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def build_test_scene(quality="hero", out=None, seed=SEED, bid=None,
                     want_near=NEAREST_CAMERA_M):
    """Build the beds, light them with the contract sun, and solve the camera
    until the MEASURED nearest gravel vertex is the manifest's 2.800 m."""
    scene = bpy.context.scene
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    b = bed_by_id(bid or HERO_SITE["bid"])
    s_shot, why = choose_shot(b)

    # the anchor is the LENS.  Solve the slant range so the MEASURED nearest
    # built vertex is 2.800 m: scaling `near` scales every distance in the shot
    # linearly and leaves the composition identical, so it converges in three.
    near_want = want_near
    nn = want_near
    stats = None
    hist = []
    for it in range(5):
        cam_p, tgt, geo = camera_pose(b, s_shot, near=nn)
        vw = (tgt[0] - cam_p[0], tgt[1] - cam_p[1])
        stats = build(anchor_world=cam_p, quality=quality, seed=seed,
                      verbose=(it == 0), view_world=vw)
        cd = bpy.data.cameras.get("CAM_GBS_Macro") or \
            bpy.data.cameras.new("CAM_GBS_Macro")
        cd.lens = LENS_AT_CLOSEST_MM
        cd.sensor_width = SENSOR_MM
        cd.clip_start = 0.02
        cd.clip_end = 3000.0
        # DOF IS OFF, and it is also SAFE if something turns it on.  The render
        # farm's worker restores `use_dof` per job from the spec, so a caller
        # that omits `--nodof` gets the camera's own aperture: at the default
        # f/2.8 focused at 10 m this shot came back defocused by a 5 px circle
        # and looked like a failed build.  f/22 focused at the frame centre
        # makes that a non-event.
        cd.dof.use_dof = False
        cd.dof.aperture_fstop = 22.0
        cd.dof.focus_distance = float(geo["slant_at_frame_centre_m"])
        cam = bpy.data.objects.get("CAM_GBS_Macro")
        if cam is None:
            cam = bpy.data.objects.new("CAM_GBS_Macro", cd)
            scene.collection.objects.link(cam)
        cam.matrix_world = _look_matrix(cam_p, tgt)
        scene.camera = cam
        near, who = measure_nearest(cam)
        hist.append((round(nn, 4), round(near, 4), who))
        print(">> camera solve %d: near param %.4f m -> nearest built vertex "
              "%.4f m (%s)" % (it, nn, near, who))
        if abs(near - near_want) < 0.004:
            break
        nn *= near_want / max(near, 1e-3)
    context_camera(scene, b, s_shot)
    reference_ground(b, max(b.s0, s_shot - 60.0), min(b.s1, s_shot + 60.0))
    h = geo["lens_height_m"]
    near, who = measure_nearest(cam)

    stats["shot"] = why
    stats["camera"] = dict(
        height_m=round(h, 4), near_param_m=round(nn, 4),
        lens_mm=LENS_AT_CLOSEST_MM, sensor_mm=SENSOR_MM,
        nearest_built_vertex_m=round(near, 4),
        nearest_object=who, manifest_m=NEAREST_CAMERA_M,
        px_per_m_at_nearest=round(RES_X_4K * LENS_AT_CLOSEST_MM /
                                  SENSOR_MM / max(near, 1e-3), 1),
        mm_per_px_at_nearest=round(1000.0 * SENSOR_MM * near /
                                   (RES_X_4K * LENS_AT_CLOSEST_MM), 4),
        solve=hist, **geo)
    print(">> px/m: lip %.1f (1 px = %.3f mm)  centre %.1f  frame top %.1f"
          % (stats["camera"]["px_per_m_at_nearest"],
             stats["camera"]["mm_per_px_at_nearest"],
             RES_X_4K * LENS_AT_CLOSEST_MM / SENSOR_MM /
             max(geo["slant_at_frame_centre_m"], 1e-3),
             geo["px_per_m_at_frame_top"]))

    contract_sun(scene)
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
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    FAB.save_clean(out)
    apply_contract_sky()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out),
                                relative_remap=False, compress=False)
    left = [i.filepath for i in bpy.data.images if i.source == "FILE"]
    if left:
        raise SystemExit("REFUSING: external images survived the save: %s" % left)
    return out


# =============================================================================
# 12.  SELF-MEASUREMENT — the things item_gate structurally cannot check
# =============================================================================
def verify(out=None, quality="hero"):
    """Measure the ARTEFACT.  Every number is a physical quantity (R2-017).

    Six questions the gate cannot answer for this item:

      1. Do the 19 beds actually DIFFER, on the four axes the manifest names?
         The gate measures a size CV over objects; that is not the same
         question.  This counts distinct rake modes, pitches, dish depths, berm
         heights and scar populations across the whole programme.
      2. Is the gravel layer ever thinner than the FIA's 250 mm over the
         working area?
      3. How far does the built gravel deviate from ``C.ground_z``, which every
         other module calls?  Reported as a bound, both signs.
      4. Is every pebble unique geometry?  Signatures over a sample.
      5. WHERE DOES THIS ITEM COLLIDE WITH build_barriers?  The ownership claim
         in §2 is only useful if the overlap is measured.
      6. What would the WHOLE programme cost at hero quality, as opposed to the
         one bed the test scene builds at it?
    """
    rep = dict(item=ITEM_ID)
    BS = beds()
    q = QUALITY[quality]

    # ---- 1: the four declared variation axes, over the whole programme -----
    rk = [b.rake for b in BS]
    rep["variation_axes"] = dict(
        beds=len(BS),
        rake_modes=sorted(set(p["mode"] for b in rk for p in b["passes"])),
        rake_last_mode_counts={k: sum(1 for b in rk if b["passes"][-1]["mode"] == k)
                               for k in RAKE_MODES},
        rake_pitch_mm=[round(b["passes"][-1]["pitch"] * 1000, 1) for b in rk],
        rake_pitch_distinct=len(set(round(b["passes"][-1]["pitch"], 4) for b in rk)),
        rake_passes=[b["n"] for b in rk],
        rake_fresh=[round(b["fresh"], 3) for b in rk],
        tractor_beds=sum(1 for b in rk if b["passes"][-1]["tractor"]),
        dish_depth_m=[round(b.dish["depth"], 4) for b in BS],
        dish_depth_max_m=round(max(b.dish["depth"] for b in BS), 4),
        dish_depth_min_m=round(min(b.dish["depth"] for b in BS), 4),
        manifest_dish_max_m=DISH_MAX_M,
        dish_t_deep=[round(b.dish["t_deep"], 3) for b in BS],
        berm_mm=[round(b.berm["h"] * 1000, 1) for b in BS],
        berm_width_m=[round(b.berm["w"], 2) for b in BS],
        berm_notches=[len(b.berm["notches"]) for b in BS],
        scars_per_bed=[b.scars["n"] for b in BS],
        scars_total=sum(b.scars["n"] for b in BS),
        scar_kind_counts={k: sum(1 for b in BS for i in b.scars["items"]
                                 if i["kind"] == k) for k in SCAR_KINDS},
        d50_mm=[round(b.grading["d50"] * 1000, 2) for b in BS],
        distinct_bed_signatures=len(set(
            (round(b.dish["depth"], 4), b.rake["passes"][-1]["mode"],
             round(b.rake["passes"][-1]["pitch"], 4), round(b.berm["h"], 4),
             b.scars["n"], round(b.grading["d50"], 5)) for b in BS)),
    )

    # ---- 2: gravel layer thickness against the FIA minimum ----------------
    thin = tot = 0
    dmin, dmax = 1e9, -1e9
    for b in BS:
        S = np.linspace(b.s0, b.s1, 140)
        w = width(b, S)
        for f in np.linspace(0.02, 0.98, 40):
            g = gravel_depth(b, S, f * w, w)
            dmin = min(dmin, float(g.min()))
            dmax = max(dmax, float(g.max()))
            if f > 0.18:                        # the working area, not the lip
                tot += int(g.size)
                thin += int(np.sum(g < FIA_MIN_DEPTH_M))
    rep["gravel_depth"] = dict(
        min_m=round(dmin, 4), max_m=round(dmax, 4),
        fia_min_m=FIA_MIN_DEPTH_M,
        working_area_samples=tot,
        thinner_than_fia=thin,
        fraction_at_or_over_fia=round(1.0 - thin / max(tot, 1), 4))

    # ---- 3: deviation from the contract datum -----------------------------
    dev = []
    for b in BS:
        S = np.linspace(b.s0 + 1.0, b.s1 - 1.0, 90)
        w = width(b, S)
        for f in np.linspace(0.0, 1.0, 26):
            d = f * w
            dev.append(bed_top_z(b, S, d, w) -
                       C.ground_z(S, inner_lat(b, S) + d, b.side))
    dev = np.concatenate(dev)
    rep["datum_deviation"] = dict(
        samples=int(dev.size),
        min_mm=round(float(dev.min()) * 1000, 2),
        max_mm=round(float(dev.max()) * 1000, 2),
        mean_mm=round(float(dev.mean()) * 1000, 2),
        note="negative = the bed is cut into the datum, which is what a gravel "
             "trap is.  The maximum POSITIVE value is the berm crest.")

    # ---- 4: pebble uniqueness --------------------------------------------
    b = BS[0]
    V, F, cls = make_stones(4000, 12345, np.full(4000, 0.014), "ico0",
                            angular=b.grading["angular"],
                            discoid=b.grading["discoid"])
    sig = np.round(np.concatenate([V.reshape(4000, -1),
                                   np.linalg.norm(V, axis=2)], axis=1), 7)
    uniq = len(set(map(tuple, sig.tolist())))
    rep["pebble_uniqueness"] = dict(
        sampled=4000, distinct_vertex_signatures=uniq,
        repeat_factor=round(4000 / max(uniq, 1), 4),
        angular_fraction=round(float(cls["angular"].mean()), 4),
        discoid_fraction=round(float(cls["discoid"].mean()), 4),
        templates={k: dict(verts=v["verts"], tris=v["tris"],
                           min_px=v["min_px"]) for k, v in STONE_TEMPLATES.items()})

    # ---- 5: the ownership overlap with build_barriers ---------------------
    over = []
    for b in BS:
        S = np.linspace(b.s0 + 1.0, b.s1 - 1.0, 60)
        w = width(b, S)
        r0 = inner_lat(b, S)
        for f in np.linspace(0.02, 0.98, 24):
            d = f * w
            mine = bed_top_z(b, S, d, w)
            theirs = _bb().platform_z(S, r0 + d, b.side)
            over.append(theirs - mine)
    over = np.concatenate(over)
    rep["ownership_overlap_with_build_barriers"] = dict(
        samples=int(over.size),
        platform_above_gravel_max_mm=round(float(over.max()) * 1000, 1),
        fraction_where_platform_is_above=round(float((over > 0).mean()), 4),
        action=("build_barriers' runoff-platform bands X and G must NOT be "
                "built where owns(x, y) returns a bed: this module's surface "
                "is below build_barriers' platform_z over the fraction above, "
                "so leaving that mesh in place z-fights.  The two-line change "
                "is to skip band X / band G in build_barriers.build_platform "
                "and to call gravel_bed_surface.bed_base_z for the sub-base."))

    # ---- 6: what the whole programme costs -------------------------------
    tot_area = sum(b.area_m2 for b in BS)
    rep["programme"] = dict(
        beds_built=len(BS), area_m2=round(tot_area, 1),
        manifest_beds=MANIFEST_INSTANCES, manifest_area_m2=MANIFEST_AREA_M2,
        note="the manifest's 21 beds / 41 137 m2 predates build_barriers' "
             "ownership clamp, which scales the declared runoff back to the "
             "room actually inside the barrier line.  What is BUILT is the "
             "figure above; both are printed so the difference is visible "
             "rather than quietly reconciled.",
        r_stone_m=q["r_stone"], stone_budget=q["budget"],
        mesh_floor_mm=round(MESH_FLOOR_M * 1000, 2),
        px_per_m_at_manifest_distance=round(PX_PER_M, 1),
        mm_per_px=round(MM_PER_PX, 4),
        gate_edge_limit_mm=round(GATE_EDGE_M * 1000, 3))

    # ---- 7: THE BUILT PEBBLES, against the datum they claim to define ------
    # Everything above is the MODEL.  This is the ARTEFACT: the vertices that
    # are actually in the scene, measured against bed_top_z, which is what
    # every dependant will call.  Without it the docstring's "pebbles stand up
    # to X mm proud" is a claim about intent (R2-017).
    obs = [o for o in bpy.context.scene.objects
           if o.type == "MESH" and o.name.startswith(PFX + "Stones_")]
    if obs:
        zs, tops, n = [], [], 0
        for ob in obs:
            bid = ob.name.split("_")[-1]
            try:
                b = bed_by_id(bid)
            except KeyError:
                continue
            me = ob.data
            nv = len(me.vertices)
            if not nv:
                continue
            co = np.empty(nv * 3, np.float32)
            me.vertices.foreach_get("co", co)
            co = co.reshape(-1, 3).astype(np.float64)
            M = np.array(ob.matrix_world.to_4x4(), float)
            co = co @ M[:3, :3].T + M[:3, 3]
            step = max(1, nv // 240000)
            co = co[::step]
            S, d, _in = bed_local(b, co[:, 0], co[:, 1])
            keep = (d >= -0.05) & (d <= width(b, S) + 0.05)
            if not np.any(keep):
                continue
            S = S[keep]; d = d[keep]
            zs.append(co[keep, 2])
            tops.append(bed_top_z(b, S, d))
            n += nv
        if zs:
            dz = (np.concatenate(zs) - np.concatenate(tops)) * 1000.0
            rep["built_pebbles_vs_datum"] = dict(
                objects=len(obs), vertices_in_scene=int(n),
                vertices_sampled=int(dz.size),
                proud_max_mm=round(float(dz.max()), 2),
                buried_min_mm=round(float(dz.min()), 2),
                mean_mm=round(float(dz.mean()), 2),
                p99_proud_mm=round(float(np.percentile(dz, 99)), 2),
                p01_mm=round(float(np.percentile(dz, 1)), 2),
                note="vertex z minus bed_top_z, in mm.  Positive = standing "
                     "proud of the surveyed envelope.  Anything that rests ON "
                     "the gravel should use bed_top_z; this is the bound on "
                     "how wrong that is for a single pebble.")

    if out:
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        json.dump(rep, open(out, "w"), indent=1)
    print(">> VERIFY " + json.dumps(rep, indent=1)[:6000])
    return rep


def measure():
    objs = [o for o in bpy.context.scene.objects
            if o.type == "MESH" and o.name.startswith(PFX)]
    tris = verts = 0
    for ob in objs:
        me = ob.data
        verts += len(me.vertices)
        tris += len(me.polygons)
    return dict(objects=len(objs), triangles=tris, vertices=verts)


def dump_programme():
    for b in beds():
        print(repr(b))
        print("     grading d50 %.1f mm  lo %.1f  hi %.1f  angular %.2f  "
              "lith %s" % (b.grading["d50"] * 1000, b.grading["d_lo"] * 1000,
                           b.grading["d_hi"] * 1000, b.grading["angular"],
                           np.round(b.grading["lith"], 3)))
        print("     dish  %.3f m  t_deep %.2f  p %.2f  s_deep %.2f"
              % (b.dish["depth"], b.dish["t_deep"], b.dish["p_exp"],
                 b.dish["s_deep"]))
        for p in b.rake["passes"]:
            print("     rake  %-13s pitch %5.0f mm  amp %5.1f mm  %s  "
                  "wander %.2f  w %.2f" % (p["mode"], p["pitch"] * 1000,
                                           p["amp"] * 1000,
                                           "tractor" if p["tractor"] else "hand",
                                           p["wander"], p["weight"]))
        print("     berm  %.0f mm over %.2f m, %d notches   fresh %.2f"
              % (b.berm["h"] * 1000, b.berm["w"], len(b.berm["notches"]),
                 b.rake["fresh"]))
        print("     scars %d: %s" % (b.scars["n"],
                                     [i["kind"] for i in b.scars["items"]]))


# =============================================================================
# 13.  CLI
# =============================================================================
def main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--test-blend", action="store_true")
    ap.add_argument("--dump-programme", action="store_true")
    ap.add_argument("--quality", default="hero",
                    choices=tuple(QUALITY.keys()))
    ap.add_argument("--bid", default=None)
    ap.add_argument("--out", default=os.path.join(
        _HERE, "gravel_bed_surface_test.blend"))
    ap.add_argument("--verify", default=os.path.join(
        _ROOT, "render/items/gravel_bed_surface/verify.json"))
    ap.add_argument("--seed", type=int, default=SEED)
    a = ap.parse_args(argv)
    if a.dump_programme:
        dump_programme()
        return
    if a.test_blend:
        st = build_test_scene(quality=a.quality, out=a.out, seed=a.seed,
                              bid=a.bid)
        st.update(measure())
        verify(out=a.verify, quality=a.quality)
        st.pop("per_bed", None)
        print(">> STAGE RESULT: %s" % json.dumps(st))


if __name__ == "__main__":
    main()
