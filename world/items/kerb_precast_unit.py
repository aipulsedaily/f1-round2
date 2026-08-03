#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
kerb_precast_unit.py — CIRCUIT VITRINE, per-item hero campaign, item
``kerb_precast_unit`` (zone ``kerbs_markings``, wave 1, build order 43,
**5 dependants**).

WHAT THIS IS, IN ONE SENTENCE
=============================
Every serrated kerb on the circuit, built as **individual precast concrete
elements** — two staggered rows of rigid castings bedded on mortar, each one its
own mesh with its own length, its own seating plane, its own chipped arris and
its own knocked-down crests, so that the thing the camera reads is the joint
rhythm and the unit-to-unit step and NOT a stripe painted on an extrusion.

WHY THE LAST ONE WAS THE WRONG OBJECT, AND WHAT CHANGED
--------------------------------------------------------
The manifest names the failure before it happens:

    "Wrong version: one extruded ribbon with a repeating stripe — the
     unit-to-unit step and roll is the whole read."

``build_surface._build_kerbs`` lofted **one ribbon per run** — 35 objects for
2 580 m of kerb — and then modulated a vertex attribute at a 2 m period to
suggest units.  Four things were structurally absent and no shader could have
supplied them:

  1. **No joints.**  A precast unit has two ends, a 4–16 mm gap, and a chamfer
     on every top arris.  At 2.5 m on a 35 mm lens that gap plus its two
     chamfers is 16 mm of shadow = **24 px**, repeating every 2 m.  It is the
     single most legible fact about the object and it did not exist.
  2. **Nothing was rigid.**  The ribbon's top followed ``ground_z`` sample by
     sample, so it bent smoothly over every undulation.  A 2 m concrete casting
     cannot.  It sits on a mortar bed, plane on plane, and where the ground line
     curves the kerb line goes FACETED — which is why a real kerb run reads as a
     chain of straight segments with a step at each joint.
  3. **One row.**  A 1.50 × 2.05 × 0.20 m element weighs 640 kg.  Kerb of this
     width is laid in two rows, joints staggered like brickwork, with a mortar
     joint down the middle at the point where the section changes slope.  That
     longitudinal joint is 10 mm wide = 15 px and runs the entire circuit.
  4. **The serration was a cosine.**  A cast serration is a 174.5 mm-radius
     crest arc, a 30 mm concave fillet and a 54 mm trough land.  The difference
     between that and a cosine is where the light breaks on the crest, which at
     a 12.47 deg sun is the whole modelling of the object.

THE PIXEL BUDGET THIS WAS BUILT TO
----------------------------------
    px_per_m = (3840 x 35 / 36) / 2.5 = 1493.3 px/m      ->     1 px = 0.670 mm

    the 75 mm peak section            112 px   (manifest: onscreen_px_4k 112)
    the 250 mm serration pitch        373 px
    the 25 mm serration amplitude      37 px
    a 4-16 mm transverse joint       6-24 px      <- must be geometry
    the 4 mm arris chamfer            6.0 px      <- must be geometry
    the 10 mm longitudinal joint       15 px      <- must be geometry
    unit-to-unit height step, 1 sd    3.3 px      <- must be geometry
    unit roll, 3.5 mrad over 1.5 m    7.8 px      <- must be geometry
    a knocked-down crest, 8-22 mm   12-33 px      <- must be geometry
    an arris chip, 3-12 mm deep      4-18 px      <- must be geometry
    cast waviness, +-1.2 mm          1.8 px, but it casts a 5.4 mm = 8 px
                                     shadow at a 12.47 deg sun  <- geometry
    exposed aggregate, 2-8 mm        3-12 px across, 0.3-1.1 mm proud
                                     = 0.5-1.6 px of relief     <- SHADING
    float marks / paint orange peel  < 0.3 mm                   <- SHADING

Everything with a silhouette is mesh.  The two entries at the bottom have no
silhouette and no occlusion at 0.67 mm/px and they are bump, exactly as
``armco_w_beam`` argued for zinc spangle.  The line is drawn at 3 mm of relief.

===============================================================================
THE PUBLIC INTERFACE  —  this item is a FOUNDATION.  5 items depend on it.
===============================================================================
Dependants named in the manifest, and what each of them must call:

    kerb_hero_t4         ``unit_records()`` + ``unit_mesh_arrays()`` +
                         ``SECTION`` + ``serration_z()``.  It re-builds the T4
                         apex units at 0.8 m / 21 mm (2800 px/m) instead of
                         2.5 m / 35 mm.  Pass ``lod=-1`` for the 1.1 mm chord
                         tier this module already supports but never uses.
    kerb_bedding_joint   ``joint_sites()``  — every transverse and longitudinal
                         joint, world frame, with its true gap and step.
    kerb_end_ramp        ``ramp_sites()``   — 70 terminals, each with the end
                         cross-section it must marry to.
    kerb_negative_trough ``NEG_SPLITS`` + ``run_records()`` — where the serrated
                         run stops for the -60 mm trough.
    dust_drift           ``trough_line()``  — the toe of the kerb on both faces,
                         where grit collects, as a world polyline with the
                         section's own shadow depth.

--- 1. THE SECTION ------------------------------------------------------------

    KERB_W        = 1.500   overall width, contract ``C.KERB_W``
    LIP_INNER     = 0.025   proud of the road at the track-side lip  (C)
    LIP_OUTER     = 0.050   proud of the road at the outer lip       (C)
    SERR_AMP      = 0.025   serration amplitude at the outer lip     (C)
    SERR_PITCH    = 0.250   serration pitch                          (C)
                            => 0.050 + 0.025 = 0.075 peak = 265 mm of plank
                            clearance against the car's 340 mm ride height.

    ``base_z(T)``      -> 0.025 + 0.025*T, the cast base plane, T = 0 at the
                          track-side lip, T = 1 at the outer lip.
    ``amp(T)``         -> 0.025*(0.25 + 0.75*T), the serration amplitude ramp.
                          The run-on end of the section is deliberately quiet;
                          the outer end is the full 25 mm.  Both agree with
                          ``C.kerb_top_z`` at every T, and never exceed it, so
                          the collision gate's clearance model stays true.
    ``serration_z(d)`` -> the cast crest profile, |d| from a crest centre:
                          a 174.5 mm arc out to |d| = 83.6 mm, a 30 mm concave
                          fillet to |d| = 98.0 mm, then a 54 mm trough land.
    ``ROW_SPLIT``      = 0.400  the longitudinal joint, in T
    ``JOINT_W``        = 0.010  its nominal width (m)

--- 2. WHERE THE UNITS ARE ----------------------------------------------------

    ``KERB_PLAN``      the 33 planned runs, verbatim from
                       ``build_surface.KERB_PLAN``, so this module's kerbs are
                       in the same places as that module's verge paint mask and
                       racing line.  Split by ``C.NEG_KERBS`` into 35 runs,
                       which is exactly the 70 terminals ``kerb_end_ramp``
                       declares.
    ``run_records()``  -> [{rid, tag, side, sign, s0, s1, phase, blk_len, ...}]
    ``unit_records()`` -> [{uid, rid, row, s_a, s_b, L, ncrest, k0, ...}] for
                          every element on the circuit.  THE CREST GRID IS
                          SHARED BY BOTH ROWS: crest k of a run sits at station
                          ``phase + k*0.250`` whichever row it is in, so the
                          serrations line up across the longitudinal joint while
                          the transverse joints stagger.  That is how it is set
                          out on site and it is why the mid-joint does not step.

--- 3. EMITTING ---------------------------------------------------------------

    ``build(lod_anchor=..., ...)`` emits into collection
    ``W_Item_KerbPrecastUnit`` with object prefix ``KPU_``.  **ONE OBJECT PER
    PRECAST ELEMENT** — which is what the manifest counts as an instance.
    ``lod_anchor`` is a list of world points (the camera path); each unit's mesh
    density is graded by its distance to the nearest of them, over four tiers
    from a 3.2 mm chord down to 55 mm.  World assembly passes the beat-5 camera
    corridor.

    Nothing is instanced and no mesh is shared.  ``mesh_reuse`` over the built
    population reports 0 shared datablocks; every element is generated from its
    own parameter draw.  See "WHAT VARIES" below.

===============================================================================
THE SEVEN LAWS, AND WHERE EACH IS DISCHARGED
===============================================================================
 1. procedural, by hand   no image node, no file, no library.  Measured by
                          ``item_gate``: ``no_external_assets``.
 2. no real brands        a kerb carries no lettering.  Red and white only.
 3. car scale             the 2.005 m car and the 0.340 m ride height set the
                          75 mm peak and the strike-zone width, not intuition.
 4. z = 0 is one plane    never assumed: every z is ``C.ground_z(s, u)``, and
                          the unit's seating plane is a least-squares fit to it.
 5. embed >= 20 mm        every element's skirt runs down to
                          ``min(ground) - C.BASE_EMBED_M`` over its own
                          footprint, so no grazing ray can get under it.
 6. recentre + TexCoord   every unit's mesh is local to its own centre in a
                          canonical frame (+X along the kerb, +Y outboard,
                          +Z up), |P| < 1.25 m.  The material reads
                          ``TexCoord->Object`` plus 12 per-vertex attributes and
                          a per-OBJECT texture offset.  ``Geometry->Position``
                          appears nowhere.
 7. chunk along s         one element is <= 2.3 m of circuit.

===============================================================================
WHAT VARIES BETWEEN INSTANCES, AND WHY IT IS GEOMETRY
===============================================================================
The manifest names five axes.  All five are in the MESH or in the placement of
a rigid body, never in a random rotation of one shared mesh:

  "precast section 1.85-2.25 m"   two moulds, 8 crests (2.000 m) and 9 crests
                                  (2.250 m), plus a site-cut closer at the end
                                  of every run; each casting is short of
                                  nominal by N(0, 6 mm) clipped at +-15 mm, and
                                  that shortfall IS the joint gap.  The mesh is
                                  regenerated at the drawn length -- vertex
                                  counts differ, so the gate's
                                  ``distinct_topologies`` is in the hundreds.
  "height step sigma 2.2 mm"      each element is a RIGID body seated on a
                                  least-squares plane through ``ground_z`` over
                                  its own footprint, plus N(0, 2.2 mm).  The
                                  step at a joint is the difference of two
                                  independent draws AND of two fitted slopes,
                                  which is what makes the run faceted.
  "roll sigma 3.5 mrad"           per element, about its own long axis; 3.5 mrad
                                  over the 1.5 m band is 5.3 mm across the top
                                  and 7.8 px of tilt in the macro.
  "2-6 knocked-down serration     per element, drawn against the local strike
   groups"                        intensity: a group is 1-3 consecutive crests
                                  truncated 8-22 mm with a rough fracture face
                                  and a sharp arris where it meets the intact
                                  casting.  Units in the strike zone draw 2-6;
                                  units 40 m from an apex draw 0-1, because
                                  that is where cars are.
  "red/white block length         the block phase belongs to the RUN, not the
   0.955-1.055 m"                 unit: a painter paints a run in one pass, so
                                  the colour boundaries cross the joints.  The
                                  serration phase also belongs to the run (the
                                  setting-out line).  The JOINTS belong to the
                                  unit.  Three independent rhythms over the same
                                  2 m -- that is what stops it reading as a
                                  pattern.

Two more that the manifest does not name and the object needs:

  cast radius error               a precast unit is cast to a radius from a
                                  discrete series (straight, 200, 120, 80, 60,
                                  45, 35, 28, 22, 18, 14, 11, 9, 7 m).  Laid on
                                  a setting-out arc of a different radius it
                                  bows in or out by (1/R_true - 1/R_cast)L^2/8
                                  -- up to 3.4 mm mid-unit, 5 px, and it is why
                                  the outer face line of a real kerb through a
                                  corner is scalloped rather than smooth.
  arris chip line                 the chamfer WIDTH and DEPTH are functions of
                                  station, so a chip is a local widening of the
                                  arris rather than a bump texture.  8-45 mm
                                  long, 2-12 mm deep, clustered where the car
                                  strikes.

===============================================================================
WHAT THE MACRO ITERATION CHANGED  —  five defects the gate could not see
===============================================================================
The acceptance gate passed on the FIRST build and the first macro was still
wrong.  All five of these were found by rendering at 2.5 m / 35 mm and looking:

  1. THE SUN RAKED ACROSS THE SERRATIONS INSTEAD OF ALONG THEM.  ``hero_aim``
     maximised ``1 - |tangent . sun|`` -- exactly backwards for a ridge that
     lies across the direction of travel.  The macro was shot at rake 0.054 on
     a hairpin that offers 0.999, and a 25 mm serration on a 250 mm pitch
     rendered as a flat painted stripe.  A 12.47 deg sun gives a crest 113 mm
     of shadow, 45 % of the pitch; that shadow is the object.
  2. THE PAINT WAS 32 % OPAQUE EVERYWHERE.  A speckle mask read
     ``map_range(noise, 0.24, 0.62)``, and a Noise texture sits at 0.5, so the
     mask evaluated to ~0.32 over the whole kerb.  The red read as pink over
     grey and no adjustment of the red could have fixed it.
  3. A REPAINT GHOST AT 0.30 RAN A SECOND RED/WHITE PATTERN over the first and
     averaged the two into mud with soft boundaries.
  4. THE CRESTS WERE GLASSY.  Every bump layer was gated on paint being ABSENT,
     so a painted crest carried none.  Two coats of road paint are 0.55 mm and
     a mould-face texture is 0.3-0.8 mm: it shows through.  Bug holes -- 1.5-5
     mm entrained-air craters, the signature of any cast concrete face -- were
     missing entirely.
  5. PAINT WEAR WAS A FUNCTION OF STATION ALONE, so it came off in clean full
     width stripes.  A tyre is 0.305 m wide; wear is 2-D and patchy.

And one the placement gate found: the cast-radius bow pushed mid-unit 4.4 mm
INBOARD on tight corners.  A fitter sets the FACE to the line and takes the
bulge up in the joint, so the bow now only shows on the outer face.

Run headless:

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P world/items/kerb_precast_unit.py -- --test \
        --save world/items/kerb_precast_unit_test.blend

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P world/items/kerb_precast_unit.py -- --selftest
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time

import numpy as np

try:
    import bpy
    HAVE_BPY = True
except Exception:                                   # pragma: no cover
    HAVE_BPY = False

_HERE = os.path.dirname(os.path.abspath(__file__))
_WORLD = os.path.dirname(_HERE)
_ROOT = os.path.dirname(_WORLD)
for _p in (_WORLD, _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import world_contract as C                                        # noqa: E402
import itemkit as K                                               # noqa: E402

__version__ = "1.0.0"

ITEM = "kerb_precast_unit"
COLL = "W_Item_KerbPrecastUnit"
PFX = "KPU_"
XPFX = "KPUX_"          # test-scene stand-ins owned by OTHER items.  "KPUX_"
                        # does NOT start with "KPU_", so running the gate with
                        # --prefix KPU_ measures none of them.

_T0 = time.time()


def log(msg):
    print("[%s %7.1fs] %s" % (ITEM, time.time() - _T0, msg))
    sys.stdout.flush()


# ==============================================================================
#  0.  THE NUMBERS
# ==============================================================================
# Manifest record, quoted so nothing downstream has to re-read the JSON.
FILMED_AT_M = 2.5
LENS_MM = 35.0
ONSCREEN_PX_4K = 112.0
INSTANCES_DECLARED = 3400
PX_PER_M = (3840.0 * LENS_MM / 36.0) / FILMED_AT_M           # 1493.3
PX_M = 1.0 / PX_PER_M                                        # 0.670 mm

# --- the section, all four numbers from the contract --------------------------
KERB_W = C.KERB_W                       # 1.500
LIP_INNER = C.KERB_LIP_INNER_M          # 0.025
LIP_OUTER = C.KERB_LIP_OUTER_M          # 0.050
SERR_AMP = C.KERB_SERRATION_AMP_M       # 0.025
SERR_PITCH = C.KERB_SERRATION_PITCH_M   # 0.250
PEAK = LIP_OUTER + SERR_AMP             # 0.075
EMBED = C.BASE_EMBED_M                  # 0.020

# The serration amplitude ramps across the section.  At T = 0 the car's plank is
# 25 mm over the lip and the casting is nearly smooth -- that is the run-on end,
# and a full 25 mm serration there would be a kerb that unsettles the car the
# instant it touches.  At T = 1 it is the full amplitude.  Identical to
# build_surface's shipped section so the two agree at every T.
AMP_AT_LIP = 0.25                       # fraction of SERR_AMP at T = 0

# --- the cast serration -------------------------------------------------------
# A cast serration is not a cosine.  It is a crest arc, a concave fillet into the
# trough, and a trough land -- because that is what comes out of a mould with a
# 25 mm rise on a 250 mm pitch and a draft angle the concrete will release from.
SERR_R = 0.17450                        # crest arc radius
SERR_RF = 0.03000                       # fillet radius, crest -> trough land
# derived, and checked in selftest():
#   arc meets the fillet at |d| = SERR_D_ARC, the fillet meets the land at
#   |d| = SERR_D_FIL, so the trough land is 2*(0.125 - SERR_D_FIL) wide.
_cf = SERR_R - SERR_AMP                                     # 0.14950
_xf = math.sqrt((SERR_R + SERR_RF) ** 2 - (SERR_RF + _cf) ** 2)
SERR_D_FIL = _xf                                            # 0.09798
SERR_D_ARC = SERR_R * _xf / (SERR_R + SERR_RF)              # 0.08363
SERR_LAND = 2.0 * (SERR_PITCH * 0.5 - SERR_D_FIL)           # 0.05404

# --- the two rows -------------------------------------------------------------
ROW_SPLIT = 0.400                       # longitudinal joint at T = 0.400
JOINT_W = 0.010                         # nominal joint width (m)
_JT = JOINT_W / KERB_W * 0.5            # half joint, in T
ROW_T = ((0.0, ROW_SPLIT - _JT), (ROW_SPLIT + _JT, 1.0))
ROW_W = tuple((b - a) * KERB_W for (a, b) in ROW_T)          # 0.595, 0.895

# --- arrises ------------------------------------------------------------------
CH_TRACK = 0.005        # chamfer at the track-side lip (the car's arris)
CH_OUTER = 0.008        # chamfer at the outer lip
CH_JOINT = 0.004        # chamfer either side of the longitudinal joint
CH_END = 0.004          # chamfer at the transverse ends

# --- moulds -------------------------------------------------------------------
# Crest counts, not lengths: the mould's internal pitch is exact and the end land
# is half a pitch, so an n-crest unit is n*0.250 m nominal.  The manifest's
# 1.85-2.25 m band is these two moulds plus the manufacturing shortfall.
MOULDS = ((8, 0.66), (9, 0.34))         # (crests, share)  -> 2.000 m, 2.250 m
SHORTFALL_SD = 0.006                    # casting length shortfall
SHORTFALL_CLIP = 0.015
GAP_BASE = 0.005                        # the fitter's nominal joint

# --- cast radius series -------------------------------------------------------
# What a precast yard actually stocks.  0.0 is "straight".
CAST_R = (0.0, 200.0, 120.0, 80.0, 60.0, 45.0, 35.0, 28.0,
          22.0, 18.0, 14.0, 11.0, 9.0, 7.0)

# --- per-unit setting tolerances ---------------------------------------------
STEP_SD = 0.0022                        # manifest: height step sigma 2.2 mm
ROLL_SD = 0.0035                        # manifest: roll sigma 3.5 mrad
LATERAL_SD = 0.0015                     # setting-out line following error

# --- paint --------------------------------------------------------------------
BLOCK_MIN, BLOCK_MAX = 0.955, 1.055     # manifest: red/white block length
PAINT_T = 0.00055                       # film thickness, two coats of road paint
PAINT_LAP = 0.00016                     # overlap ridge at a colour boundary

# --- LOD ----------------------------------------------------------------------
# (chord along s, column pitch mid-section, column pitch at the arrises).
# LOD -1 exists for kerb_hero_t4, which is filmed at 0.8 m on a 21 mm lens
# (2800 px/m) and needs 1.1 mm.  This module never uses it.
LOD = (
    (0.0011, 0.012, 0.003),     # -1  hero, kerb_hero_t4's tier
    (0.0032, 0.030, 0.008),     #  0  2.5 m on 35 mm: 4.8 px / 45 px / 12 px
    (0.0090, 0.055, 0.018),     #  1
    (0.0220, 0.110, 0.045),     #  2
    (0.0550, 0.220, 0.110),     #  3  silhouette only, > 350 m
)
LOD_BASE = 1                    # index of LOD 0 inside the tuple above
LOD_RADII = (60.0, 150.0, 420.0)


def lod_of(dist):
    for i, r in enumerate(LOD_RADII):
        if dist <= r:
            return i
    return len(LOD_RADII)


# ==============================================================================
#  1.  MATHS
# ==============================================================================

def hash01(*keys):
    """FNV-1a with a murmur3 finaliser.

    THE FINALISER IS NOT DECORATION, and this module shipped without it.
    Measured avalanche — the mean fraction of output bits that flip when ONE
    input bit flips — was **0.2718** against an ideal of 0.5. FNV's multiply
    only propagates change UPWARD, so taking the low 30 bits throws away exactly
    the part that moved, and several supposedly independent per-unit properties
    collapse onto one.

    This module builds 3,400 precast kerb elements. They sit at the track edge,
    in frame, along the whole lap — `KPU_` is in `placement_gate.EDGE_FAMILIES`
    precisely because it lives where the camera looks. Serration knock-down,
    paint wear, bedding step and grit were meant to vary per element.

    Ported from pit_wall_unit.py, which hit this and fixed it locally without
    the fix ever propagating. Also widened the mask: 0xFFFFFFFFFFFFFFF is
    fifteen F's — 60 bits — which silently discarded the top nibble of every key.

    NOTE: this CHANGES THE BUILT GEOMETRY. Re-gate the module.
    """
    h = 1469598103934665603
    for k in keys:
        h ^= int(k) & 0xFFFFFFFFFFFFFFFF
        h = (h * 1099511628211) & 0xFFFFFFFFFFFFFFFF
    h ^= h >> 33
    h = (h * 0xFF51AFD7ED558CCD) & 0xFFFFFFFFFFFFFFFF
    h ^= h >> 33
    h = (h * 0xC4CEB9FE1A85EC53) & 0xFFFFFFFFFFFFFFFF
    h ^= h >> 33
    return float(h % (1 << 30)) / float(1 << 30)


class Rng(object):
    """Deterministic per-unit stream.  Same seed -> same casting, always."""

    def __init__(self, *keys):
        s = 0
        for k in keys:
            s = (s * 1000003 + int(k)) & 0x7FFFFFFF
        self.r = np.random.default_rng(s)
        self.seed = s

    def u(self, a=0.0, b=1.0):
        return float(self.r.uniform(a, b))

    def n(self, mu=0.0, sd=1.0):
        return float(self.r.normal(mu, sd))

    def i(self, a, b):
        return int(self.r.integers(a, b))

    def pick(self, options, weights):
        w = np.asarray(weights, float)
        return options[int(self.r.choice(len(options), p=w / w.sum()))]


def _h2(ix, iy, seed):
    """Integer lattice hash -> [0,1).  Vectorised, wraps in int64 on purpose."""
    with np.errstate(over="ignore"):
        h = (ix.astype(np.int64) * np.int64(374761393)
             + iy.astype(np.int64) * np.int64(668265263)
             + np.int64(seed) * np.int64(2246822519))
        h = (h ^ (h >> np.int64(13))) * np.int64(1274126177)
        h = h ^ (h >> np.int64(16))
    return (h & np.int64(0xFFFFFF)).astype(np.float64) / float(0x1000000)


def _sstep(t):
    return t * t * (3.0 - 2.0 * t)


def vnoise2(x, y, seed=0):
    ix = np.floor(x); iy = np.floor(y)
    fx = _sstep(x - ix); fy = _sstep(y - iy)
    ix = ix.astype(np.int64); iy = iy.astype(np.int64)
    a = _h2(ix, iy, seed); b = _h2(ix + 1, iy, seed)
    c = _h2(ix, iy + 1, seed); d = _h2(ix + 1, iy + 1, seed)
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def fbm2(x, y, seed=0, oct=4, lac=2.07, gain=0.5):
    tot = np.zeros(np.broadcast(x, y).shape)
    amp = 1.0; nrm = 0.0; f = 1.0
    for i in range(oct):
        tot = tot + amp * vnoise2(x * f, y * f, seed + i * 131)
        nrm += amp; amp *= gain; f *= lac
    return tot / nrm


def vnoise1(x, seed=0):
    ix = np.floor(x)
    fx = _sstep(x - ix)
    ix = ix.astype(np.int64)
    z = np.zeros_like(ix)
    return _h2(ix, z, seed) * (1 - fx) + _h2(ix + 1, z, seed) * fx


def fbm1(x, seed=0, oct=4, lac=2.03, gain=0.5):
    tot = np.zeros(np.shape(x)); amp = 1.0; nrm = 0.0; f = 1.0
    for i in range(oct):
        tot = tot + amp * vnoise1(x * f, seed + i * 977)
        nrm += amp; amp *= gain; f *= lac
    return tot / nrm


def clamp01(a):
    return np.clip(a, 0.0, 1.0)


def smoothstep(e0, e1, x):
    return _sstep(clamp01((np.asarray(x, float) - e0) / (e1 - e0 + 1e-12)))


# ==============================================================================
#  2.  THE SECTION
# ==============================================================================

def base_z(T):
    """Cast base plane above the road datum, T = 0 track lip .. 1 outer lip."""
    return LIP_INNER + (LIP_OUTER - LIP_INNER) * np.asarray(T, float)


def amp(T):
    """Serration amplitude at T.  0.25 -> 1.0 of SERR_AMP across the section."""
    return SERR_AMP * (AMP_AT_LIP + (1.0 - AMP_AT_LIP) * np.asarray(T, float))


def serration_z(d):
    """Cast crest profile, normalised 0..1.  `d` = signed offset from a crest.

    |d| <= SERR_D_ARC   crest arc, radius SERR_R, centre (0, -(R - amp))
    |d| <= SERR_D_FIL   concave fillet, radius SERR_RF, centre (xf, RF)
    else                trough land, 0
    """
    a = np.abs(np.asarray(d, float))
    z = np.zeros_like(a)
    m = a <= SERR_D_ARC
    z[m] = np.sqrt(np.maximum(SERR_R ** 2 - a[m] ** 2, 0.0)) - _cf
    m = (a > SERR_D_ARC) & (a < SERR_D_FIL)
    z[m] = SERR_RF - np.sqrt(np.maximum(SERR_RF ** 2 - (a[m] - _xf) ** 2, 0.0))
    return z / SERR_AMP


def profile_offsets(lod):
    """Sample offsets across ONE pitch, [-0.125, +0.125], adaptive.

    Fine on the crest arc and the fillet where the surface turns; coarse on the
    trough land where it does not.  This is what puts the fine decile of the
    edge distribution on the part of the object the light actually breaks over,
    instead of spending it on flat concrete.
    """
    chord = LOD[lod + LOD_BASE][0]
    # crest arc: constant chord along the arc
    th = math.asin(SERR_D_ARC / SERR_R)
    n_arc = max(int(math.ceil(2.0 * th * SERR_R / chord)), 4)
    t = np.linspace(-th, th, n_arc + 1)
    d_arc = SERR_R * np.sin(t)
    # fillet: from SERR_D_ARC to SERR_D_FIL, both signs
    ph = math.atan2(SERR_D_FIL - SERR_D_ARC, abs(SERR_RF - (SERR_RF - 0.0)) + 1e-9)
    fil_arc = SERR_RF * th          # the fillet turns through the same angle
    n_fil = max(int(math.ceil(fil_arc / chord)), 2)
    d_fil = np.linspace(SERR_D_ARC, SERR_D_FIL, n_fil + 1)[1:]
    # trough land: coarse, but never coarser than 6 chords
    land = SERR_PITCH * 0.5 - SERR_D_FIL
    n_land = max(int(math.ceil(land / max(chord * 4.0, 0.004))), 1)
    d_land = np.linspace(SERR_D_FIL, SERR_PITCH * 0.5, n_land + 1)[1:]
    half = np.concatenate([d_arc[d_arc >= 0.0], d_fil, d_land])
    return np.unique(np.concatenate([-half[::-1], half]))


# ==============================================================================
#  3.  THE PLAN  —  verbatim from build_surface.KERB_PLAN
# ==============================================================================
#  side: 'in' = inside of the corner (apex side), 'out' = outside.
#  f0/f1 are fractions of the arc length measured from the arc start.
KERB_PLAN = {
    "T1":  [("in", -0.06, 1.12, "apex kerb, 330 km/h braking zone runs onto it"),
            ("out", -0.34, 0.06, "turn-in kerb: the car is still braking at the edge"),
            ("out", 0.62, 1.62, "exit kerb, wide open onto the T1-T2 link")],
    "T2":  [("in", -0.05, 1.20, "apex kerb of the linked left"),
            ("out", 0.70, 1.90, "exit kerb onto the east chute")],
    "T3":  [("in", -0.08, 1.15, "295 km/h kink: the apex kerb is the only one used"),
            ("out", 0.60, 1.75, "exit kerb, 4.89 g runs the car straight to the edge")],
    "T4":  [("in", -0.04, 1.10, "hairpin apex kerb - the hero corner of the film"),
            ("out", -0.58, 0.04, "entry kerb after 143.8 m of downhill braking"),
            ("out", 0.86, 1.70, "exit kerb at the foot of La Rampe")],
    "T5":  [("in", -0.03, 1.10, "apex kerb, uphill right"),
            ("out", 0.74, 1.75, "exit kerb onto the climb straight")],
    "T6":  [("in", -0.05, 1.22, "esse 1 apex"),
            ("out", 0.80, 2.05, "exit kerb; also serves as T7's turn-in kerb")],
    "T7":  [("in", -0.05, 1.22, "esse 2 apex"),
            ("out", 0.80, 1.95, "exit kerb into T8")],
    "T8":  [("in", -0.05, 1.25, "summit apex, off-camber; split by the negative kerb"),
            ("out", 0.85, 1.90, "exit kerb, car light over the crest")],
    "T9":  [("in", -0.05, 1.32, "esse 4 apex"),
            ("out", 0.85, 2.10, "exit kerb onto the summit run")],
    "T10": [("in", -0.04, 1.06, "first apex of the increasing-radius sweeper"),
            ("out", -0.30, 0.05, "turn-in kerb, 281 km/h")],
    "T11": [("in", -0.06, 1.12, "second apex, car accelerating to 294 km/h"),
            ("out", 0.78, 2.00, "long exit kerb - 55 m of runoff behind it")],
    "T12": [("in", -0.10, 1.22, "apex of the downhill heavy-braking left"),
            ("out", -0.75, 0.02, "turn-in kerb at the low point"),
            ("out", 0.90, 2.40, "exit kerb; split by the negative kerb")],
    "T13": [("in", -0.05, 1.55, "short slow left, the kerb outlives the arc"),
            ("out", 1.00, 2.60, "exit kerb through the link to T14")],
    "T14": [("in", -0.06, 1.45, "right flick apex"),
            ("out", 0.90, 2.40, "exit kerb into the T15 approach")],
    "T15": [("in", -0.04, 1.18, "final corner apex, 207 km/h onto the pit straight"),
            ("out", 0.72, 1.85, "exit kerb, 30 m of asphalt runoff behind it")],
}

RAMP_MIN, RAMP_MAX = 1.1, 2.8           # kerb_end_ramp's own manifest range

_RUNS = None
_UNITS = None
NEG_SPLITS = []


def _corner_dirs():
    return {c["name"].split()[0]: c["direction"] for c in C.SPEC["corners"]}


def _elements():
    return {e["tag"]: e for e in C._ELS}


def run_records():
    """The 35 serrated-kerb runs.  Cached; identical every call."""
    global _RUNS, NEG_SPLITS
    if _RUNS is not None:
        return _RUNS
    els = _elements()
    dirs = _corner_dirs()
    raw = []
    for tag in sorted(KERB_PLAN):
        e = els[tag]
        sg_in = 1.0 if dirs[tag] == "left" else -1.0
        for k, (side, f0, f1, why) in enumerate(KERB_PLAN[tag]):
            sgn = sg_in if side == "in" else -sg_in
            raw.append(dict(tag=tag, side=side, sign=sgn, idx=k, why=why,
                            s0=e["s0"] + e["L"] * f0, s1=e["s0"] + e["L"] * f1))

    # the negative-kerb troughs cut the serrated run: the trough is a hole in
    # the SURFACE, cut by C.ground_z, so its stations come from the contract or
    # the runs would be split somewhere other than where the road actually dips.
    neg = [(float(a), float(b), float(sd)) for (a, b, sd) in C.NEG_KERBS]
    NEG_SPLITS = neg
    out = []
    for r in raw:
        pieces = [(r["s0"], r["s1"])]
        for (a, b, side) in neg:
            if abs(side - r["sign"]) > 1e-6:
                continue
            nxt = []
            for (p0, p1) in pieces:
                if b < p0 - 1.0 or a > p1 + 1.0:
                    nxt.append((p0, p1)); continue
                if a - 1.6 > p0 + 3.0:
                    nxt.append((p0, a - 1.6))
                if b + 1.6 < p1 - 3.0:
                    nxt.append((b + 1.6, p1))
            pieces = nxt
        for j, (p0, p1) in enumerate(pieces):
            if p1 - p0 < 4.0:      # build_surface's own floor for a kerb run
                continue
            q = dict(r); q["s0"] = p0; q["s1"] = p1
            q["name"] = "%s_%s%d%s" % (r["tag"], r["side"], r["idx"],
                                       "" if len(pieces) == 1 else chr(97 + j))
            out.append(q)

    for i, r in enumerate(out):
        rg = Rng(90210, i)
        r["rid"] = i
        # the SETTING-OUT LINE: one crest phase for the whole run, shared by both
        # rows, which is why the serrations line up across the longitudinal
        # joint on a real kerb and why they must here.
        r["phase"] = r["s0"] + rg.u(0.0, SERR_PITCH)
        # the PAINTER's rhythm, independent of both the mould and the fitter.
        r["blk_len"] = rg.u(BLOCK_MIN, BLOCK_MAX)
        r["blk_phase"] = rg.u(0.0, 1.0)
        # the terminals kerb_end_ramp owns.  On a short stub between a negative
        # kerb and the end of a corner there is not room for two full ramps, so
        # they scale down together rather than eating the whole run.
        ri, ro = rg.u(RAMP_MIN, RAMP_MAX), rg.u(RAMP_MIN, RAMP_MAX)
        room = (r["s1"] - r["s0"]) - 2.4
        if ri + ro > room:
            k = max(room, 2.0 * RAMP_MIN * 0.35) / (ri + ro)
            ri *= k; ro *= k
        r["ramp_in"], r["ramp_out"] = ri, ro
        # where the cars actually hit this kerb, as a fraction of the run
        r["strike_at"] = 0.42 if r["side"] == "in" else 0.72
        r["strike_w"] = rg.u(0.22, 0.36)
        r["strike_i"] = rg.u(0.55, 1.0)
        # curvature of the setting-out line at mid-run, for the cast radius
        _, _, _, K = C.centreline_arrays(np.array([0.5 * (r["s0"] + r["s1"])]))
        r["kappa"] = float(K[0])
    _RUNS = out
    return out


def _mould_seq(rg, n_crest_avail):
    """Crest counts for one row of one run, ending in a site-cut closer."""
    seq = []
    left = n_crest_avail
    nmin = min(m[0] for m in MOULDS)
    while left >= nmin:
        n = rg.pick([m[0] for m in MOULDS], [m[1] for m in MOULDS])
        if n > left:
            n = nmin                    # never a part-mould: that is a closer
        seq.append(n)
        left -= n
    if left >= 2:
        seq.append(-left)               # negative = site-cut closer
    return seq


def unit_records():
    """Every precast element on the circuit.  Cached."""
    global _UNITS
    if _UNITS is not None:
        return _UNITS
    runs = run_records()
    units = []
    uid = 0
    for r in runs:
        s_a0 = r["s0"] + r["ramp_in"]
        s_b0 = r["s1"] - r["ramp_out"]
        if s_b0 - s_a0 < 2.0:
            continue
        for row in (0, 1):
            rg = Rng(31337, r["rid"], row)
            # first crest index at or after the start of the laid length
            k0 = int(math.ceil((s_a0 + 0.5 * SERR_PITCH - r["phase"]) / SERR_PITCH))
            kend = int(math.floor((s_b0 - 0.5 * SERR_PITCH - r["phase"]) / SERR_PITCH))
            navail = kend - k0 + 1
            if navail < 4:
                continue
            k = k0
            for n in _mould_seq(rg, navail):
                closer = n < 0
                n = abs(n)
                c0 = r["phase"] + k * SERR_PITCH
                c1 = r["phase"] + (k + n - 1) * SERR_PITCH
                a = c0 - 0.5 * SERR_PITCH
                b = c1 + 0.5 * SERR_PITCH
                if closer:
                    # a saw cut: the closer keeps its crests but loses land at
                    # the far end, and the cut face has no chamfer.
                    b = min(b, s_b0)
                # A casting comes out of the mould SHORT, never long: the mould
                # is the maximum.  The shortfall is what the fitter's joint has
                # to swallow, so gap = GAP_BASE + shortfall, 5-20 mm, and two
                # neighbours can never overlap.
                short = float(np.clip(abs(rg.n(0.0, SHORTFALL_SD)),
                                      0.0, SHORTFALL_CLIP))
                units.append(dict(
                    uid=uid, rid=r["rid"], row=row, k0=k, ncrest=n,
                    closer=closer, sign=r["sign"],
                    s_a=a + 0.5 * (GAP_BASE + short),
                    s_b=b - 0.5 * (GAP_BASE + short),
                    seq=len(units)))
                uid += 1
                k += n
    # per-unit setting draws, and the strike intensity that decides the damage
    for u in units:
        r = runs[u["rid"]]
        rg = Rng(0xBEEF, u["uid"])
        u["L"] = u["s_b"] - u["s_a"]
        u["s_m"] = 0.5 * (u["s_a"] + u["s_b"])
        u["dz"] = rg.n(0.0, STEP_SD)
        u["roll"] = rg.n(0.0, ROLL_SD)
        # OUTBOARD ONLY.  The kerb is an edge-defining family: the placement
        # gate holds it to the true half width, so it may sit AT the racing
        # surface edge and never inside it.  A two-sided draw put 2 mm of
        # concrete over the asphalt on half the population.
        u["dlat"] = abs(rg.n(0.0, LATERAL_SD))
        u["jit"] = rg.n(0.0, 0.0015)         # crest position, mould wear
        f = (u["s_m"] - r["s0"]) / max(r["s1"] - r["s0"], 1e-6)
        strike = math.exp(-((f - r["strike_at"]) / r["strike_w"]) ** 2) * r["strike_i"]
        u["strike"] = float(np.clip(strike + 0.14 * (rg.u() - 0.5), 0.0, 1.0))
        # the manifest's "2-6 knocked-down serration groups": that is a struck
        # unit.  A unit 40 m from the apex is not struck and must not pretend.
        lo = 2 if u["strike"] > 0.55 else 0
        hi = 7 if u["strike"] > 0.55 else (3 if u["strike"] > 0.25 else 2)
        u["ngroup"] = rg.i(lo, max(hi, lo + 1))
        u["nchip"] = rg.i(0, 4 + int(round(9 * u["strike"])))
        u["age"] = rg.u(0.0, 1.0)
        u["seed"] = rg.seed
        # cast radius: nearest stocked radius to the setting-out radius
        kap = abs(r["kappa"])
        Rtrue = (1.0 / kap) if kap > 1e-7 else 0.0
        if Rtrue == 0.0 or Rtrue > 260.0:
            u["R_cast"] = 0.0
        else:
            u["R_cast"] = min([x for x in CAST_R if x > 0.0],
                              key=lambda x: abs(1.0 / x - kap))
        # bow: (1/R_true - 1/R_cast) * L^2 / 8, signed outboard
        inv_t = kap
        inv_c = (1.0 / u["R_cast"]) if u["R_cast"] > 0 else 0.0
        sgn_turn = math.copysign(1.0, r["kappa"]) if abs(r["kappa"]) > 1e-9 else 1.0
        u["bow"] = (inv_t - inv_c) * u["L"] ** 2 / 8.0 * sgn_turn * (-u["sign"])
        # THE FITTER SETS THE FACE, NOT THE ENDS.  A unit cast to a flatter
        # radius than the arc bulges INBOARD at mid-length, and the placement
        # gate duly measured 4.4 mm of concrete over the racing surface on the
        # tight corners.  No fitter lays a kerb proud of the running surface:
        # he sets the whole element out by the bulge and takes it up in the
        # joint.  So the bow only ever shows on the OUTER face line -- which is
        # the scalloped read it exists for -- and the track-side lip stays at
        # or outboard of the surface edge, with a 1.2 mm setting-out clearance.
        #
        # 5 mm, not 1: a kerb is set out to a string line with a +5 mm face
        # tolerance because nobody lays concrete proud of the running surface,
        # AND the placement gate samples the corridor centreline every 1.0 m,
        # which on a 35 m hairpin puts its chord 3.6 mm inside the true arc and
        # reads an inside-of-corner kerb as 1-3 mm deeper than it is.  5 mm
        # clears both, and 5 mm of extra asphalt at the toe is 7 px.
        u["dlat"] += 0.0050 + max(0.0, -u["bow"])
    _UNITS = units
    return units


# ==============================================================================
#  4.  ONE UNIT  ->  MESH
# ==============================================================================

def _columns(u, lod):
    """Across-section sample positions, in T, for this unit's row.

    Fine at both arrises because that is where the chips are and where the
    chamfer has to be a real facet; coarse across the middle because the cast
    section is a straight line there and the relief that lives on it has an
    80-400 mm wavelength.
    """
    _, dmid, dedge = LOD[lod + LOD_BASE]
    t0, t1 = ROW_T[u["row"]]
    w = (t1 - t0) * KERB_W
    band = min(0.075, w * 0.30)
    cols = [0.0]
    x = dedge
    while x < band:
        cols.append(x); x += dedge
    x = band
    while x < w - band:
        cols.append(x); x += dmid
    x = w - band
    while x < w - 1e-6:
        cols.append(x); x += dedge
    cols.append(w)
    cols = np.unique(np.round(np.array(cols), 6))
    return t0 + cols / KERB_W


def _stations(u, r, lod):
    """Along-unit sample positions x in [0, L].

    Built FROM the crest grid, so every sample that matters lands exactly on the
    cast profile, plus the end chamfers and the paint-block boundaries, so those
    edges are real facets and not a staircase.
    """
    L = u["L"]
    off = profile_offsets(lod)
    xs = [0.0, CH_END, L - CH_END, L]
    for j in range(u["ncrest"]):
        c = (r["phase"] + (u["k0"] + j) * SERR_PITCH + u["jit"]) - u["s_a"]
        xs.append(c)
        xs.extend(list(c + off))
    # paint block boundaries: the painter's rhythm, in run stations
    b0 = (u["s_a"] - r["s0"]) / r["blk_len"] + r["blk_phase"]
    b1 = (u["s_b"] - r["s0"]) / r["blk_len"] + r["blk_phase"]
    for m in range(int(math.floor(b0)), int(math.ceil(b1)) + 1):
        x = (m - r["blk_phase"]) * r["blk_len"] + r["s0"] - u["s_a"]
        if 0.0 < x < L:
            xs.extend([x - 0.0025, x, x + 0.0025])
    x = np.array(xs, float)
    x = x[(x >= -1e-9) & (x <= L + 1e-9)]
    x = np.clip(x, 0.0, L)
    x = np.unique(np.round(x, 6))
    # never leave a gap longer than the LOD chord * 6 (the trough land at the
    # coarse tiers, and the site-cut closer's stub)
    gap = max(LOD[lod + LOD_BASE][0] * 6.0, 0.012)
    out = [x[0]]
    for i in range(1, len(x)):
        d = x[i] - out[-1]
        if d > gap:
            k = int(math.ceil(d / gap))
            out.extend(list(out[-1] + np.arange(1, k) * (d / k)))
        out.append(x[i])
    return np.array(out)


def _serr_factor(x, u, r):
    """Serration height factor 0..1 at along-unit position x."""
    s = u["s_a"] + x - r["phase"] - u["jit"]
    d = (s + 0.5 * SERR_PITCH) % SERR_PITCH - 0.5 * SERR_PITCH
    # suppress outside the unit's own crest span (the end lands are flat)
    return serration_z(d)


def _seating(u, r):
    """The rigid body's seating plane, fitted to the ground it stands on.

    A 2 m casting cannot follow the road.  It is bedded on mortar, so its top is
    a PLANE (plus its cast section) and the bedding takes up the difference.
    That is what makes a kerb run faceted instead of smooth, and the facet break
    at each joint is the thing the manifest calls "the whole read".
    """
    t0, t1 = ROW_T[u["row"]]
    tm = 0.5 * (t0 + t1)
    S = np.linspace(u["s_a"], u["s_b"], 9)
    Wh = C.half_width(S)
    um = u["sign"] * (Wh + tm * KERB_W)
    zg = np.asarray(C.ground_z(S, um), float)
    xs = S - u["s_m"]
    A = np.stack([np.ones_like(xs), xs], axis=1)
    coef, *_ = np.linalg.lstsq(A, zg, rcond=None)
    z0, grad = float(coef[0]), float(coef[1])
    # cross-slope of the road under this unit, measured not assumed
    ui = u["sign"] * (C.half_width(u["s_m"]) + t0 * KERB_W)
    uo = u["sign"] * (C.half_width(u["s_m"]) + t1 * KERB_W)
    zi = float(C.ground_z(u["s_m"], ui))
    zo = float(C.ground_z(u["s_m"], uo))
    cross = (zo - zi) / max((t1 - t0) * KERB_W, 1e-6)
    return z0, grad, cross, tm


def unit_mesh_arrays(u, lod=0, detail=True):
    """-> (V_local, quads, attrs, origin_world, basis) for one precast element.

    V_local is recentred on the unit's own centre in a canonical frame:
    +X along the kerb, +Y outboard, +Z up.  |P| < 1.25 m at every LOD.
    """
    r = run_records()[u["rid"]]
    rg = Rng(0xC0FFEE, u["uid"])
    L = u["L"]
    t0, t1 = ROW_T[u["row"]]
    row_w = (t1 - t0) * KERB_W

    X = _stations(u, r, lod)                       # (nx,)
    Tc = _columns(u, lod)                          # (nT,)
    nx, nT = len(X), len(Tc)

    # ---- the cast top surface -------------------------------------------
    f = _serr_factor(X, u, r)                      # (nx,)
    # the end lands are flat: no partial crest hanging off a cut face
    if u["closer"]:
        cend = (r["phase"] + (u["k0"] + u["ncrest"] - 1) * SERR_PITCH
                + u["jit"]) - u["s_a"]
        f = np.where(X > cend + SERR_D_FIL, 0.0, f)

    T2 = np.broadcast_to(Tc[None, :], (nx, nT))
    X2 = np.broadcast_to(X[:, None], (nx, nT))
    F2 = np.broadcast_to(f[:, None], (nx, nT))

    yl = (T2 - t0) * KERB_W                        # local y within the row

    # --- wear: the car polishes and flattens the crests it strikes -------
    # THE WEAR USED TO BE A FUNCTION OF STATION ALONE, so every crest lost its
    # paint uniformly across the full 1.5 m and the kerb read as grey bands with
    # red only surviving in the flanks.  A tyre is 0.305 m wide and lands where
    # it lands: paint goes in PATCHES, not in stripes.  The 2-D term is what
    # makes a worn crest read as worn rather than as a different colour of kerb.
    wear_prof = clamp01(u["strike"] * (0.55 + 0.45 * fbm1(X * 3.1, u["seed"] % 9973)))
    W2 = np.broadcast_to(wear_prof[:, None], (nx, nT))
    W2 = W2 * (0.35 + 0.65 * T2)          # the tyre and the plank land outboard
    if detail:
        W2 = W2 * (0.30 + 0.90 * fbm2(X2 / 0.26, yl / 0.26,
                                      (u["seed"] + 61) % 50021, oct=3))
    W2 = clamp01(W2)

    # --- knocked-down serration groups -----------------------------------
    # A wheel does not shear a ridge off cleanly across the full 1.5 m: it hits
    # a stretch of it and the concrete breaks back from there.  Each group gets
    # a lateral extent as well as a longitudinal one, and the truncation is a
    # FRACTION of the local crest, not an absolute depth.
    #
    # (An absolute 8-22 mm cap was the first version and it was wrong: the
    # serration is only 13.8 mm tall at the inboard edge of the outer row, so a
    # 22 mm cap cut 8 mm BELOW the trough and gouged a trench across the whole
    # element.)
    K2 = np.zeros((nx, nT))
    KF2 = np.zeros((nx, nT))
    groups = []
    if u["ngroup"] > 0 and u["ncrest"] > 0:
        for g in range(u["ngroup"]):
            j0 = rg.i(0, u["ncrest"])
            span = rg.i(1, 4)
            dep = rg.u(0.008, 0.022)                 # at the outer lip
            kfrac = float(np.clip(dep / SERR_AMP, 0.0, 0.90))
            # lateral extent: impacts land outboard, where the tyre and the
            # plank are, and break back toward the track a random distance
            t_in = t0 + (t1 - t0) * rg.u(0.0, 0.62)
            edge = rg.u(0.012, 0.070)                # how sharp the break is
            groups.append((j0, span, dep, t_in))
            lat = smoothstep(t_in, t_in + edge, T2)
            for j in range(j0, min(j0 + span, u["ncrest"])):
                c = (r["phase"] + (u["k0"] + j) * SERR_PITCH + u["jit"]) - u["s_a"]
                m = np.abs(X - c) < SERR_D_FIL
                mm = np.broadcast_to(m[:, None], (nx, nT)) * lat
                K2 = np.maximum(K2, mm)
                KF2 = np.maximum(KF2, mm * kfrac)

    # --- the cast surface, before damage ---------------------------------
    zc = base_z(T2) + amp(T2) * F2
    # crest polish: the top 6 mm of a struck crest wears flat
    zc = zc - W2 * 0.006 * np.clip((F2 - 0.55) / 0.45, 0.0, 1.0)

    # --- truncate the knocked groups with a rough fracture ---------------
    if detail and K2.any():
        frac = (fbm2(X2 * 22.0, yl * 22.0, (u["seed"] + 17) % 65521, oct=3) - 0.5)
        frac = frac + 0.55 * (fbm2(X2 * 95.0, yl * 95.0,
                                   (u["seed"] + 29) % 65521, oct=2) - 0.5)
        cap = base_z(T2) + amp(T2) * (1.0 - KF2) + frac * 0.0060
        cap = np.maximum(cap, base_z(T2) + 0.0012)
        zc = np.where(K2 > 0.02, np.minimum(zc, cap), zc)

    # --- cast waviness ---------------------------------------------------
    if detail:
        wav = (fbm2(X2 / 0.34, yl / 0.34, u["seed"] % 40961, oct=4) - 0.5) * 0.0024
        wav += (fbm2(X2 / 0.085, yl / 0.085, (u["seed"] + 3) % 40961, oct=3) - 0.5) * 0.0011
        zc = zc + wav

    # --- paint film -------------------------------------------------------
    blk = (u["s_a"] + X - r["s0"]) / r["blk_len"] + r["blk_phase"]
    parity = np.floor(blk) % 2.0
    dblk = np.abs(blk - np.round(blk)) * r["blk_len"]      # m to nearest boundary
    paint_wear = clamp01(W2 * 1.15 * np.clip((F2 - 0.30) / 0.70, 0.0, 1.0)
                         + K2 * 0.9)
    film = PAINT_T * (1.0 - clamp01(paint_wear * 1.25))
    film = film + PAINT_LAP * np.exp(-(np.broadcast_to(dblk[:, None], (nx, nT))
                                       / 0.012) ** 2)
    zc = zc + film

    # ---- the chamfers ----------------------------------------------------
    # A chip is a LOCAL WIDENING of the arris, not a texture.  The chamfer width
    # and depth are functions of station, so the arris line itself wanders.
    def arris(side_seed, base_w, base_h, nchip):
        cw = np.full(nx, base_w)
        chd = np.full(nx, base_h)
        rr = Rng(side_seed, u["uid"])
        for _ in range(nchip):
            c = rr.u(0.0, L)
            ln = rr.u(0.008, 0.045)
            dp = rr.u(0.002, 0.012)
            g = np.exp(-((X - c) / (ln * 0.6)) ** 2)
            g = g * (0.55 + 0.45 * vnoise1(X * 260.0, rr.seed % 30011))
            cw = cw + g * ln * 0.5
            chd = chd + g * dp
        return cw, chd

    n_in = int(round(u["nchip"] * 0.35))
    n_ou = u["nchip"] - n_in
    cw_i, cd_i = arris(0x1111, CH_END, CH_TRACK if u["row"] == 0 else CH_JOINT, n_in)
    cw_o, cd_o = arris(0x2222, CH_END, CH_JOINT if u["row"] == 0 else CH_OUTER, n_ou)
    if not detail:
        cw_i[:] = CH_END; cd_i[:] = CH_TRACK if u["row"] == 0 else CH_JOINT
        cw_o[:] = CH_END; cd_o[:] = CH_JOINT if u["row"] == 0 else CH_OUTER

    # chamfer drop: 45 deg from each of the four top arrises
    d_in = yl
    d_ou = row_w - yl
    d_a = X2
    d_b = L - X2
    drop = np.zeros((nx, nT))
    drop = np.maximum(drop, np.maximum(0.0, (cw_i[:, None] - d_in))
                      * (cd_i[:, None] / np.maximum(cw_i[:, None], 1e-6)))
    drop = np.maximum(drop, np.maximum(0.0, (cw_o[:, None] - d_ou))
                      * (cd_o[:, None] / np.maximum(cw_o[:, None], 1e-6)))
    ce = 0.0 if u["closer"] else CH_END
    if ce > 0.0:
        drop = np.maximum(drop, np.maximum(0.0, ce - d_a) * (CH_END / ce))
    drop = np.maximum(drop, np.maximum(0.0, CH_END - d_b) * (CH_END / CH_END))
    zc = zc - drop

    # ---- seat the rigid body --------------------------------------------
    z0, grad, cross, tm = _seating(u, r)
    seat = z0 + grad * (X2 - 0.5 * L) + cross * ((T2 - tm) * KERB_W)
    seat = seat + u["dz"] + u["roll"] * ((T2 - tm) * KERB_W)
    Zw = seat + zc

    # ---- world position --------------------------------------------------
    S = u["s_a"] + X
    Wh = C.half_width(S)
    tt = np.clip((X - 0.5 * L) / (0.5 * L), -1.0, 1.0)
    bow = u["bow"] * (1.0 - tt ** 2)
    Uw = u["sign"] * (Wh[:, None] + T2 * KERB_W + u["dlat"] + bow[:, None])
    Xc, Yc, H, _K = C.centreline_arrays(S)
    Xw = Xc[:, None] - np.sin(H)[:, None] * Uw
    Yw = Yc[:, None] + np.cos(H)[:, None] * Uw

    # ---- the skirt -------------------------------------------------------
    # every element's foot goes BELOW the datum by C.BASE_EMBED_M, measured
    # against the lowest ground under its own footprint.
    zg_edge = np.concatenate([
        np.asarray(C.ground_z(S, u["sign"] * (Wh + t0 * KERB_W)), float),
        np.asarray(C.ground_z(S, u["sign"] * (Wh + t1 * KERB_W)), float)])
    z_bot = float(zg_edge.min()) - EMBED

    # ---- local frame -----------------------------------------------------
    sm = u["s_m"]
    Xo, Yo, Ho, _ = C.centreline_arrays(np.array([sm]))
    uo = u["sign"] * (C.half_width(sm) + tm * KERB_W)
    ox = float(Xo[0] - math.sin(Ho[0]) * uo)
    oy = float(Yo[0] + math.cos(Ho[0]) * uo)
    oz = float(z0)
    th = float(Ho[0])
    ex = np.array([math.cos(th), math.sin(th), 0.0])
    ey = np.array([-math.sin(th), math.cos(th), 0.0]) * u["sign"]
    ez = np.array([0.0, 0.0, 1.0])

    P = np.stack([Xw.ravel() - ox, Yw.ravel() - oy, Zw.ravel() - oz], axis=1)
    Vt = np.stack([P @ ex, P @ ey, P @ ez], axis=1)

    # ---- assemble: top grid + skirt + bottom cap -------------------------
    idx = np.arange(nx * nT).reshape(nx, nT)
    if u["sign"] > 0:
        q_top = np.stack([idx[:-1, :-1], idx[1:, :-1], idx[1:, 1:], idx[:-1, 1:]],
                         axis=-1).reshape(-1, 4)
    else:
        q_top = np.stack([idx[:-1, :-1], idx[:-1, 1:], idx[1:, 1:], idx[1:, :-1]],
                         axis=-1).reshape(-1, 4)

    # boundary ring, counter-clockwise in (x, T)
    ring = (list(idx[0, :]) + list(idx[1:, -1]) + list(idx[-1, -2::-1])
            + list(idx[-2::-1, 0]))
    ring = np.array(ring, np.int64)
    Vr = Vt[ring].copy()
    Vr[:, 2] = z_bot - oz
    base_i = nx * nT
    V = np.concatenate([Vt, Vr], axis=0)
    nr = len(ring)
    a = ring
    b = np.roll(ring, -1)
    ra = base_i + np.arange(nr)
    rb = base_i + (np.arange(nr) + 1) % nr
    if u["sign"] > 0:
        q_sk = np.stack([a, ra, rb, b], axis=-1)
    else:
        q_sk = np.stack([a, b, rb, ra], axis=-1)
    # bottom cap: a planar fan from the centroid
    cen = np.array([[Vr[:, 0].mean(), Vr[:, 1].mean(), z_bot - oz]])
    V = np.concatenate([V, cen], axis=0)
    ci = len(V) - 1
    if u["sign"] > 0:
        t_bot = np.stack([np.full(nr, ci), rb, ra], axis=-1)
    else:
        t_bot = np.stack([np.full(nr, ci), ra, rb], axis=-1)

    quads = np.concatenate([q_top, q_sk], axis=0)

    # ---- per-vertex attributes ------------------------------------------
    nv = len(V)

    def pad(a2):
        a2 = np.asarray(a2, float)
        if a2.ndim == 0:
            a2 = np.full((nx, nT), float(a2))
        flat = a2.ravel()
        return np.concatenate([flat, flat[ring], [flat[ring].mean()]])

    face = np.zeros(nv)
    face[nx * nT:] = 1.0                       # skirt + cap
    att = {
        "kp_ridge": pad(F2),
        "kp_wear": pad(clamp01(W2)),
        "kp_knock": pad(K2),
        "kp_chip": pad(clamp01(drop / np.maximum(
            np.maximum(cd_i[:, None], cd_o[:, None]), 1e-6) - 0.15)),
        "kp_paint": pad(clamp01(1.0 - paint_wear)),
        "kp_block": pad(np.broadcast_to(blk[:, None], (nx, nT))),
        "kp_t": pad(T2),
        "kp_along": pad(X2 / max(L, 1e-6)),
        "kp_edge": pad(clamp01(1.0 - np.minimum(np.minimum(d_in, d_ou),
                                                np.minimum(d_a, d_b)) / 0.030)),
        "kp_grime": pad(clamp01(0.30 + 0.70 * (1.0 - F2) * (1.0 - 0.5 * T2))),
        "kp_face": face,
        "kp_dz": pad(zc - base_z(T2)),
    }
    return V, quads, t_bot, att, (ox, oy, oz), (ex, ey, ez), dict(
        nx=nx, nT=nT, groups=groups, z_bot=z_bot, z0=z0, grad=grad, cross=cross)


# ==============================================================================
#  5.  BLENDER MESH
# ==============================================================================
ATTRS = ("kp_ridge", "kp_wear", "kp_knock", "kp_chip", "kp_paint", "kp_block",
         "kp_t", "kp_along", "kp_edge", "kp_grime", "kp_face", "kp_dz")


def _new_mesh(name, verts, quads=None, tris=None, smooth_deg=31.0):
    me = bpy.data.meshes.new(name)
    verts = np.ascontiguousarray(verts, dtype=np.float32)
    me.vertices.add(len(verts))
    me.vertices.foreach_set("co", verts.ravel())
    polys, counts = [], []
    if quads is not None and len(quads):
        polys.append(np.asarray(quads, np.int32).ravel())
        counts.append(np.full(len(quads), 4, np.int32))
    if tris is not None and len(tris):
        polys.append(np.asarray(tris, np.int32).ravel())
        counts.append(np.full(len(tris), 3, np.int32))
    if polys:
        loops = np.concatenate(polys)
        counts = np.concatenate(counts)
        starts = np.concatenate([[0], np.cumsum(counts)[:-1]]).astype(np.int32)
        me.loops.add(len(loops))
        me.loops.foreach_set("vertex_index", loops)
        me.polygons.add(len(counts))
        me.polygons.foreach_set("loop_start", starts)
    me.update(calc_edges=True)
    me.validate(verbose=False)
    if smooth_deg is not None and len(me.polygons):
        _shade_by_angle(me, smooth_deg)
    return me


def _shade_by_angle(me, deg=31.0):
    """Smooth everywhere except across a real arris.

    The cast surface is tangent-continuous from trough land through fillet
    through crest arc; flat-shading it turns 70 facets per pitch into 70 visible
    bands.  The chamfers, the end faces, the skirt and every fracture face are
    genuinely sharp and must stay so.  numpy against `sharp_edge`, because
    shade_auto_smooth needs a VIEW_3D context and cannot run headless.
    """
    npoly = len(me.polygons); nloop = len(me.loops); nedge = len(me.edges)
    if not nedge:
        return
    me.polygons.foreach_set("use_smooth", np.ones(npoly, np.int8))
    fn = np.empty(npoly * 3, np.float32); me.polygons.foreach_get("normal", fn)
    fn = fn.reshape(npoly, 3)
    ls = np.empty(npoly, np.int32); me.polygons.foreach_get("loop_start", ls)
    lt = np.empty(npoly, np.int32); me.polygons.foreach_get("loop_total", lt)
    lv = np.empty(nloop, np.int32); me.loops.foreach_get("vertex_index", lv)
    nxt = np.arange(nloop, dtype=np.int64) + 1
    ends = (ls + lt - 1).astype(np.int64)
    nxt[ends] = ls.astype(np.int64)
    a = lv.astype(np.int64); b = lv[nxt].astype(np.int64)
    key = np.minimum(a, b) * np.int64(len(me.vertices)) + np.maximum(a, b)
    face_of_loop = np.repeat(np.arange(npoly, dtype=np.int64), lt)
    order = np.argsort(key, kind="stable")
    ks = key[order]; fs = face_of_loop[order]
    first = np.concatenate([[True], ks[1:] != ks[:-1]])
    grp = np.cumsum(first) - 1
    ng = int(grp[-1]) + 1
    f0 = np.zeros(ng, np.int64); f1 = np.full(ng, -1, np.int64)
    np.copyto(f0, fs[np.flatnonzero(first)])
    second = np.flatnonzero(~first)
    if len(second):
        f1[grp[second]] = fs[second]
    dot = np.ones(ng); two = f1 >= 0
    if two.any():
        dot[two] = np.einsum("ij,ij->i", fn[f0[two]], fn[f1[two]])
    ang = np.degrees(np.arccos(np.clip(dot, -1.0, 1.0)))
    sharp_key = ks[np.flatnonzero(first)][ang > deg]
    ev = np.empty(nedge * 2, np.int32); me.edges.foreach_get("vertices", ev)
    ev = ev.reshape(nedge, 2).astype(np.int64)
    ekey = (np.minimum(ev[:, 0], ev[:, 1]) * np.int64(len(me.vertices))
            + np.maximum(ev[:, 0], ev[:, 1]))
    sharp = np.zeros(nedge, np.int8)
    if len(sharp_key):
        sk = np.sort(sharp_key)
        idx = np.clip(np.searchsorted(sk, ekey), 0, len(sk) - 1)
        sharp[sk[idx] == ekey] = 1
    at = me.attributes.get("sharp_edge") or me.attributes.new(
        "sharp_edge", "BOOLEAN", "EDGE")
    at.data.foreach_set("value", sharp)


def _bake(me, attrs):
    for name in ATTRS:
        if name not in attrs:
            continue
        a = me.attributes.new(name, "FLOAT", "POINT")
        a.data.foreach_set("value", np.ascontiguousarray(attrs[name], np.float32))


def build_unit(u, coll, mat, lod=0):
    r = run_records()[u["rid"]]
    V, quads, tris, att, org, basis, info = unit_mesh_arrays(u, lod)
    name = "%sU%05d" % (PFX, u["uid"])
    me = _new_mesh(name, V, quads, tris)
    _bake(me, att)
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    ex, ey, ez = basis
    M = np.eye(4)
    M[:3, 0] = ex; M[:3, 1] = ey; M[:3, 2] = ez
    M[:3, 3] = org
    from mathutils import Matrix
    ob.matrix_world = Matrix([[float(M[i][j]) for j in range(4)] for i in range(4)])
    coll.objects.link(ob)
    _object_props(ob, u, r, lod, info)
    return ob, len(quads) * 2 + len(tris)


def _object_props(ob, u, r, lod, info):
    sd = u["seed"]
    # per-object texture offset: the only thing that stops 2500 elements sharing
    # one realisation of the concrete.  24 m, not 240 -- Cycles evaluates
    # procedurals in float32 and a large offset costs lattice precision.
    ob["kpu_ofs_x"] = float(hash01(sd, 3) * 24.0)
    ob["kpu_ofs_y"] = float(hash01(sd, 5) * 24.0)
    ob["kpu_ofs_z"] = float(hash01(sd, 7) * 24.0)
    ob["kpu_age"] = float(u["age"])
    ob["kpu_strike"] = float(u["strike"])
    ob["kpu_hue"] = float(hash01(sd, 11))
    ob["kpu_val"] = float(hash01(sd, 13))
    ob["item"] = ITEM
    ob["kpu_uid"] = int(u["uid"])
    ob["kpu_run"] = r["name"]
    ob["kpu_row"] = int(u["row"])
    ob["kpu_lod"] = int(lod)
    ob["kpu_len"] = float(u["L"])
    ob["kpu_ncrest"] = int(u["ncrest"])
    ob["kpu_closer"] = int(u["closer"])
    ob["kpu_ngroup"] = int(u["ngroup"])
    ob["kpu_station"] = float(u["s_m"])
    ob["kpu_reason"] = r["why"]


# ==============================================================================
#  6.  THE MATERIAL
# ==============================================================================

class NT(object):
    """Node DSL.  Same shape as armco_w_beam's, so the two read alike."""

    def __init__(self, name):
        m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
        m.use_nodes = True
        self.m = m
        self.t = m.node_tree
        self.t.nodes.clear()
        self.x = 0

    def n(self, typ, **kw):
        nd = self.t.nodes.new(typ)
        self.x += 1
        nd.location = ((self.x % 14) * 220, -(self.x // 14) * 300)
        for k, v in kw.items():
            if hasattr(nd, k):
                setattr(nd, k, v)
        return nd

    def pin(self, nd, idx, src):
        if src is None:
            return
        if isinstance(src, tuple) and hasattr(src[0], "outputs"):
            self.t.links.new(src[0].outputs[src[1]], nd.inputs[idx])
        elif hasattr(src, "outputs"):
            self.t.links.new(src.outputs[0], nd.inputs[idx])
        elif isinstance(src, (tuple, list)):
            nd.inputs[idx].default_value = (
                tuple(src) + (1.0,) if len(src) == 3 else tuple(src))
        else:
            nd.inputs[idx].default_value = float(src)

    def pin_named(self, nd, name, src):
        """`pin`, addressing the socket BY NAME, and RAISING if it is gone.

        R2-057.  This class is a private copy of itemkit's node DSL, so
        itemkit's socket check -- which asserts the indices ITEMKIT assumes --
        is blind to every index used here.  Blender 5.2 moved
        ShaderNodeBsdfPrincipled's `Normal` from 5 to 6 (a `Thin Wall` socket
        was inserted at 5); the modules that still said 5 delivered their whole
        bump chain into `Thin Wall` and rendered plausibly with no relief at
        all.  The indices in this file happened to be right; being right by
        luck is not a property worth keeping, so the socket that moves is now
        addressed by the name that does not.
        """
        if src is None:
            return
        for i, s in enumerate(nd.inputs):
            if s.name == name:
                return self.pin(nd, i, src)
        raise RuntimeError(
            "%s has no input named %r; it has %s"
            % (nd.bl_idname, name, [s.name for s in nd.inputs]))

    def cmix(self, fac, a, b, blend="MIX"):
        nd = self.n("ShaderNodeMix", data_type="RGBA", blend_type=blend)
        self.pin(nd, 0, fac); self.pin(nd, 6, a); self.pin(nd, 7, b)
        return (nd, 2)

    def fmix(self, fac, a, b):
        nd = self.n("ShaderNodeMix", data_type="FLOAT")
        self.pin(nd, 0, fac); self.pin(nd, 2, a); self.pin(nd, 3, b)
        return (nd, 0)

    def math(self, op, a=None, b=None, clamp=False):
        nd = self.n("ShaderNodeMath", operation=op, use_clamp=clamp)
        self.pin(nd, 0, a); self.pin(nd, 1, b)
        return (nd, 0)

    def vmath(self, op, a=None, b=None, scale=None):
        nd = self.n("ShaderNodeVectorMath", operation=op)
        self.pin(nd, 0, a); self.pin(nd, 1, b)
        if scale is not None:
            self.pin(nd, 3, scale)
        return (nd, 0)

    def noise(self, vec, scale, detail=8.0, rough=0.55, lac=2.0, out=0):
        nd = self.n("ShaderNodeTexNoise", noise_dimensions="3D")
        self.pin(nd, 0, vec); self.pin(nd, 2, scale); self.pin(nd, 3, detail)
        self.pin(nd, 4, rough); self.pin(nd, 5, lac)
        return (nd, out)

    def vor(self, vec, scale, feature="F1", out=0, rand=1.0):
        nd = self.n("ShaderNodeTexVoronoi", feature=feature,
                    voronoi_dimensions="3D")
        self.pin(nd, 0, vec); self.pin(nd, 2, scale); self.pin(nd, 8, rand)
        return (nd, out)

    def wave(self, vec, scale, distortion=0.0, detail=2.0, direction="X"):
        nd = self.n("ShaderNodeTexWave", wave_type="BANDS",
                    bands_direction=direction)
        self.pin(nd, 0, vec); self.pin(nd, 1, scale)
        self.pin(nd, 2, distortion); self.pin(nd, 3, detail)
        return (nd, 1)

    def ramp(self, src, stops):
        nd = self.n("ShaderNodeValToRGB")
        self.pin(nd, 0, src)
        el = nd.color_ramp.elements
        while len(el) > 1:
            el.remove(el[-1])
        el[0].position = stops[0][0]
        el[0].color = tuple(stops[0][1]) + (1.0,)
        for pos, col in stops[1:]:
            e = el.new(pos)
            e.color = tuple(col) + (1.0,)
        return (nd, 0)

    def attr(self, name, out=2, typ="GEOMETRY"):
        nd = self.n("ShaderNodeAttribute", attribute_type=typ)
        nd.attribute_name = name
        return (nd, out)

    def maprange(self, v, f0, f1, t0, t1, clamp=True):
        nd = self.n("ShaderNodeMapRange")
        nd.clamp = clamp
        self.pin(nd, 0, v); self.pin(nd, 1, f0); self.pin(nd, 2, f1)
        self.pin(nd, 3, t0); self.pin(nd, 4, t1)
        return (nd, 0)

    def bump(self, height, strength, distance=None, normal=None,
             modulation_pp=None, wavelength_m=None, height_pp=1.0):
        """Height -> normal perturbation.  WIRED BY NAME, stated in RADIANCE.

        TWO defects lived in the four lines this replaces.

        WIRED BY NAME (R2-038).  Blender 5.2 inserted `Filter Width` at index 2,
        so the live socket order is

            [0] Strength  [1] Distance  [2] Filter Width  [3] Height  [4] Normal

        The old body pinned `height` to index 2 and the incoming normal chain to
        index 3: the height signal went into Filter Width, and the Height socket
        of the FIRST bump in every chain kept its constant default.  A constant
        has zero gradient, so that stage contributed NO relief at all, and every
        later stage read a normal chain where its height should be.  It was
        silent -- the material built, rendered, and passed the gate's node-count
        check; only `relief_reads_as_lip_and_shade` could ever have seen it.
        Never pin this node by index again.

        STATE THE RADIANCE MODULATION, NOT THE METRES (itemkit section 5b,
        ITEM-CAMPAIGN-BRIEF 4a).  Give `modulation_pp` with `wavelength_m` and
        the depth is derived from the contract sun: m = 2 sin(theta) / tan(e),
        a 4.52x amplifier at this film's 12.47 deg.  An amplitude with no
        wavelength is not a relief specification -- the same 0.5 mm is m = 0.57
        on an 8 mm crumple and m = 0.045 on a 100 mm flute.  `height_pp` is the
        peak-to-peak swing of the height signal reaching the socket, so a stage
        can state the modulation of the BAND it means rather than of a
        hypothetical full-range height.
        """
        if (distance is None) == (modulation_pp is None):
            raise ValueError("bump() takes exactly one of distance= or "
                             "modulation_pp= (with wavelength_m=): itemkit 5b")
        if modulation_pp is not None:
            if not wavelength_m:
                raise ValueError("bump(modulation_pp=) needs wavelength_m=; an "
                                 "amplitude with no wavelength is not a relief "
                                 "specification.")
            try:
                _s = abs(float(strength))
            except (TypeError, ValueError):
                _s = 1.0         # a masked strength: aim at where the mask is 1
            distance = (K.relief_amplitude_for(modulation_pp, wavelength_m)
                        * 1e-3 / max(_s * float(height_pp), 1e-9))
        nd = self.n("ShaderNodeBump")
        self.pin(nd, nd.inputs.find("Strength"), strength)
        self.pin(nd, nd.inputs.find("Distance"), distance)
        self.pin(nd, nd.inputs.find("Height"), height)
        if normal is not None:
            self.pin(nd, nd.inputs.find("Normal"), normal)
        return (nd, 0)

    def sep(self, vec, out):
        nd = self.n("ShaderNodeSeparateXYZ")
        self.pin(nd, 0, vec)
        return (nd, out)

    def comb(self, x, y, z):
        nd = self.n("ShaderNodeCombineXYZ")
        self.pin(nd, 0, x); self.pin(nd, 1, y); self.pin(nd, 2, z)
        return (nd, 0)


# Linear reflectances.  Concrete is DARKER than intuition: a weathered precast
# kerb measures 0.24-0.30 diffuse, not the 0.6 that "grey" suggests, and road
# paint that has been outside two seasons has lost a third of its brightness.
PAL = dict(
    conc_pale=(0.2180, 0.2135, 0.2020),     # dry, laitance still on it
    conc_mid=(0.1580, 0.1535, 0.1440),      # weathered cast face
    conc_dark=(0.0930, 0.0900, 0.0840),     # shaded, damp, dirty
    fracture=(0.2760, 0.2670, 0.2480),      # a fresh break: bright and matt
    agg_dark=(0.0680, 0.0665, 0.0640),      # basalt / granite coarse aggregate
    agg_pale=(0.2450, 0.2380, 0.2230),      # limestone / quartzite
    red_new=(0.3650, 0.0182, 0.0118),       # chlorinated rubber road red
    red_old=(0.2140, 0.0295, 0.0218),       # chalked, two seasons of UV
    white_new=(0.5500, 0.5380, 0.5120),
    white_old=(0.2950, 0.2830, 0.2620),
    rubber=(0.0215, 0.0208, 0.0205),        # tyre transfer
    grit=(0.1330, 0.1180, 0.0930),          # trapped sand and brake dust
    lime=(0.4100, 0.4050, 0.3950),          # efflorescence bloom
    algae=(0.0490, 0.0630, 0.0355),
    mortar=(0.1620, 0.1560, 0.1450),
)


def mat_kerb():
    """Precast concrete, painted red and white, four seasons beside a circuit.

    Fourteen surface histories in the order the concrete acquired them.  Every
    one of them is procedural and every one is driven either by object-space
    coordinates (recentred, |P| < 1.25 m) or by an attribute this module baked
    into the mesh.  `Geometry->Position` appears nowhere.
    """
    t = NT(PFX + "Concrete")
    co = t.n("ShaderNodeTexCoord")
    OBJ = (co, 3)
    ofs = t.comb(t.attr("kpu_ofs_x", 2, "OBJECT"),
                 t.attr("kpu_ofs_y", 2, "OBJECT"),
                 t.attr("kpu_ofs_z", 2, "OBJECT"))
    P = t.vmath("ADD", OBJ, ofs)                       # per-object realisation
    Pl = OBJ                                           # unshifted, for anything
                                                       # that must key to the
                                                       # element's own geometry
    age = t.attr("kpu_age", 2, "OBJECT")
    hue = t.attr("kpu_hue", 2, "OBJECT")
    val = t.attr("kpu_val", 2, "OBJECT")

    ridge = t.attr("kp_ridge")
    wear = t.attr("kp_wear")
    knock = t.attr("kp_knock")
    chip = t.attr("kp_chip")
    paint = t.attr("kp_paint")
    block = t.attr("kp_block")
    tt = t.attr("kp_t")
    edge = t.attr("kp_edge")
    grime = t.attr("kp_grime")
    face = t.attr("kp_face")

    # ---- 1. the cast body ------------------------------------------------
    # batch-to-batch cement colour, then the mould's own blotching
    n_batch = t.noise(t.vmath("SCALE", P, scale=0.55), 1.6, 3.0, 0.45)
    n_cast = t.noise(t.vmath("SCALE", P, scale=1.0), 9.0, 6.0, 0.58)
    n_fine = t.noise(t.vmath("SCALE", P, scale=1.0), 62.0, 8.0, 0.62)
    body = t.cmix(t.maprange(n_batch, 0.30, 0.70, 0.0, 1.0),
                  PAL["conc_mid"], PAL["conc_pale"])
    body = t.cmix(t.math("MULTIPLY", t.maprange(n_cast, 0.28, 0.74, 0.0, 1.0), 0.55),
                  body, PAL["conc_dark"])
    body = t.cmix(t.math("MULTIPLY", t.maprange(val, 0.0, 1.0, 0.0, 1.0), 0.22),
                  body, PAL["conc_pale"])

    # ---- 2. coarse aggregate, seen where the skin is gone ---------------
    v_agg = t.vor(t.vmath("SCALE", P, scale=1.0), 138.0, "F1", 0, 1.0)
    v_agg2 = t.vor(t.vmath("SCALE", P, scale=1.0), 320.0, "F1", 0, 1.0)
    agg_id = t.vor(t.vmath("SCALE", P, scale=1.0), 138.0, "F1", 1, 1.0)
    agg_col = t.cmix(t.maprange(agg_id, 0.25, 0.75, 0.0, 1.0),
                     PAL["agg_dark"], PAL["agg_pale"])
    agg_mask = t.maprange(v_agg, 0.02, 0.26, 1.0, 0.0)
    # the skin only opens where the casting is broken or has been ground away
    skin_gone = t.math("MAXIMUM",
                       t.math("MULTIPLY", knock, 0.92),
                       t.math("MULTIPLY", t.math("MULTIPLY", wear, ridge), 0.55))
    skin_gone = t.math("MAXIMUM", skin_gone, t.math("MULTIPLY", chip, 0.85))
    body = t.cmix(t.math("MULTIPLY", agg_mask, skin_gone), body, agg_col)
    body = t.cmix(t.math("MULTIPLY", t.maprange(v_agg2, 0.02, 0.16, 1.0, 0.0),
                         t.math("MULTIPLY", skin_gone, 0.45)), body, PAL["agg_pale"])
    # a fresh break is brighter than everything around it and it is why a
    # knocked-down crest reads at all
    body = t.cmix(t.math("MULTIPLY", knock,
                         t.maprange(n_fine, 0.35, 0.75, 0.55, 0.95)),
                  body, PAL["fracture"])

    # ---- 2b. bug holes -- the signature of a precast face -----------------
    # Entrained air that did not escape the mould: round craters 3-5 mm across
    # and 0.6-1.8 mm deep, in drifts on the faces the mould held.  They survive
    # under paint because the film is 0.55 mm and the hole is three times that,
    # and they are the single most recognisable thing about a cast concrete
    # surface.  Absent, the crests read as extruded plastic -- which is exactly
    # what the 0.8 m frame showed.
    #
    # Voronoi F1 Distance is in CELL units, so a crater of radius r cells at
    # scale k is 2r/k metres across.  The first attempt used r = 0.115 at
    # k = 265, i.e. 0.9 mm holes -- invisible.  r = 0.42 at k = 190 is a 4.4 mm
    # hole on a 5.3 mm lattice: 6.6 px at 1493 px/m, 12 px at 0.8 m.
    v_bug = t.vor(t.vmath("SCALE", P, scale=1.0), 190.0, "F1", 0, 0.85)
    bug_id = t.vor(t.vmath("SCALE", P, scale=1.0), 190.0, "F1", 1, 0.85)
    # A HARD BAND, not a soft cone.  map_range(0, 0.42) makes a smooth hill
    # centred on each feature point, which under a denoiser is indistinguishable
    # from low-frequency mottle -- the 3x pixel-peep showed exactly that.  A
    # bug hole has a RIM: it is flat concrete, then a 0.4 mm lip, then a
    # hemispherical void.  (0.26, 0.36) is a 3.8 mm disc with a 1.1 mm rim.
    bug = t.math("MULTIPLY",
                 t.maprange(v_bug, 0.36, 0.26, 0.0, 1.0),
                 t.maprange(bug_id, 0.55, 0.72, 0.0, 1.0))     # only some cells
    bug = t.math("MULTIPLY", bug,
                 t.maprange(t.noise(t.vmath("SCALE", P, scale=1.0),
                                    11.0, 5.0, 0.55), 0.34, 0.66, 0.15, 1.0))
    bug_pre = bug
    body = t.cmix(t.math("MULTIPLY", bug, 0.60), body, PAL["conc_dark"])

    # ---- 3. efflorescence in the troughs --------------------------------
    n_eff = t.noise(t.vmath("SCALE", P, scale=1.0), 24.0, 5.0, 0.55)
    eff = t.math("MULTIPLY", t.maprange(ridge, 0.45, 0.02, 0.0, 1.0),
                 t.maprange(n_eff, 0.52, 0.82, 0.0, 1.0))
    body = t.cmix(t.math("MULTIPLY", eff, 0.45), body, PAL["lime"])

    # ---- 4. the paint ----------------------------------------------------
    # block parity: floor(block) mod 2.  The attribute is linear along the run,
    # so the boundary is exact and lands mid-face, which is where a painted
    # boundary lands.
    par = t.math("MODULO", t.math("FLOOR", block), 2.0)
    n_pw = t.noise(t.vmath("SCALE", P, scale=1.0), 46.0, 7.0, 0.60)
    n_ghost = t.noise(t.vmath("SCALE", P, scale=1.0), 3.4, 4.0, 0.50)
    # THE PAINT'S OWN TONE.  A flat colour under a bump map still reads as
    # enamel, because what the eye uses to tell paint-on-concrete from moulded
    # plastic is TONAL variation at the substrate's own scale: the roller lays
    # thick in the hollows and thin on the high spots, so the colour follows the
    # cast texture even where the normal barely moves.  Without this the crests
    # rendered as ceramic tile at 0.8 m however hard the bump was driven.
    n_roll = t.noise(t.vmath("SCALE", P, scale=1.0), 165.0, 6.0, 0.62)
    n_stip = t.noise(t.vmath("SCALE", P, scale=1.0), 700.0, 4.0, 0.58)
    tone = t.math("ADD", 0.80,
                  t.math("ADD", t.math("MULTIPLY",
                                       t.maprange(n_roll, 0.22, 0.80, 0.0, 1.0),
                                       0.30),
                         t.math("MULTIPLY",
                                t.maprange(n_stip, 0.25, 0.78, 0.0, 1.0), 0.14)))
    fade = t.maprange(age, 0.0, 1.0, 0.25, 1.0)
    red = t.cmix(t.math("MULTIPLY", fade, t.maprange(n_pw, 0.3, 0.8, 0.4, 1.0)),
                 PAL["red_new"], PAL["red_old"])
    white = t.cmix(t.math("MULTIPLY", fade, t.maprange(n_pw, 0.3, 0.8, 0.4, 1.0)),
                   PAL["white_new"], PAL["white_old"])
    pcol = t.cmix(par, white, red)
    # The previous repaint, showing through where this coat is thin.  THIS WAS
    # THE THING THAT KILLED THE FIRST MACRO: at 0.30 mix over a smooth noise it
    # ran a second, offset red/white pattern across the whole kerb, and the two
    # patterns averaged into pink-brown mud with soft boundaries.  A repaint
    # ghost is visible in PATCHES where the new coat is thin, not everywhere --
    # so the mask is thresholded hard and the mix is 0.13.
    ghost = t.cmix(t.math("MODULO", t.math("FLOOR",
                                           t.math("ADD", block, 0.37)), 2.0),
                   PAL["white_old"], PAL["red_old"])
    pcol = t.cmix(t.math("MULTIPLY", t.maprange(n_ghost, 0.62, 0.71, 0.0, 1.0),
                         0.13), pcol, ghost)
    pcol = t.cmix(1.0, pcol, t.comb(tone, tone, tone), blend="MULTIPLY")
    # a bug hole is not painted: the roller bridges it and you see a dark ring
    pcol = t.cmix(t.math("MULTIPLY", bug_pre, 0.80), pcol, PAL["conc_dark"])
    # Paint does not survive on a crest that has been driven over, and it goes
    # in speckled patches, not evenly.
    #
    # THE BAND HERE WAS 0.24-0.62 AND IT COST THE FIRST TWO MACROS.  A Noise
    # texture sits around 0.5, so that band evaluated to about 0.32 EVERYWHERE:
    # the paint was 32 % opaque over the entire kerb, the red read as pale pink
    # over grey concrete, and no amount of adjusting the red fixed it because
    # the red was never being applied.  0.70-0.88 puts the mask at 1.0 over ~85 %
    # of the surface and takes the paint off in patches, which is the thing it
    # was always meant to do.
    p_mask = t.math("MULTIPLY", paint,
                    t.maprange(t.noise(t.vmath("SCALE", P, scale=1.0),
                                       210.0, 5.0, 0.6), 0.70, 0.88, 1.0, 0.0))
    p_mask = t.math("MULTIPLY", p_mask, t.maprange(face, 0.0, 1.0, 1.0, 0.0))
    col = t.cmix(p_mask, body, pcol)

    # ---- 4b. the arrises -------------------------------------------------
    # A chamfer is the first thing to get dirty and the first thing to lose its
    # paint: it is 4-8 mm of near-vertical cast face that the roller never
    # reaches and the broom always does.  Left clean it reads as a bright cream
    # piping round every element, which is exactly what the last macro showed.
    n_arr = t.noise(t.vmath("SCALE", P, scale=1.0), 88.0, 6.0, 0.6)
    arris = t.math("MULTIPLY", t.math("POWER", edge, 1.6),
                   t.maprange(n_arr, 0.25, 0.75, 0.35, 1.0))
    col = t.cmix(t.math("MULTIPLY", arris, 0.55), col, PAL["conc_mid"])
    col = t.cmix(t.math("MULTIPLY", t.math("MULTIPLY", arris, chip), 0.75),
                 col, PAL["fracture"])

    # ---- 5. rubber transfer ---------------------------------------------
    n_rub = t.noise(t.vmath("SCALE", P, scale=1.0), 18.0, 6.0, 0.62)
    rub = t.math("MULTIPLY", t.math("MULTIPLY", wear, ridge),
                 t.maprange(n_rub, 0.35, 0.78, 0.15, 1.0))
    col = t.cmix(t.math("MULTIPLY", rub, 0.72), col, PAL["rubber"])

    # ---- 6. grit and dust, IN THE TROUGHS ONLY --------------------------
    # `kp_grime` has a 0.30 floor everywhere, which is right for how dirty a
    # kerb is but wrong as a colour mix: applied at 0.55 across the whole
    # surface it laid a uniform tan wash over the paint and took the red with
    # it.  Grit is a TROUGH phenomenon -- it is washed and blown off the crests
    # every time a car goes over -- so the mask is squared against the ridge.
    v_grit = t.vor(t.vmath("SCALE", P, scale=1.0), 420.0, "F1", 0, 1.0)
    n_dust = t.noise(t.vmath("SCALE", P, scale=1.0), 7.5, 6.0, 0.55)
    trough = t.math("POWER", t.maprange(ridge, 0.55, 0.02, 0.0, 1.0), 2.0)
    dust = t.math("MULTIPLY", t.math("MULTIPLY", grime, trough),
                  t.maprange(n_dust, 0.30, 0.78, 0.10, 1.0))
    dust = t.math("MULTIPLY", dust, t.maprange(v_grit, 0.0, 0.35, 1.0, 0.35))
    col = t.cmix(t.math("MULTIPLY", dust, 0.86), col, PAL["grit"])

    # ---- 6b. road film ----------------------------------------------------
    # THE SHADOWED TROUGHS RENDERED ELECTRIC BLUE, and the light is not the
    # defect: `SKY_IRRADIANCE` is (4.228, 7.577, 13.573) against a direct
    # horizontal of (24.996, 17.905, 9.676), so in the BLUE channel this film's
    # sky is brighter than its sun and anything the sun cannot reach is blue by
    # construction.  What was missing is that a real trough is not a clean
    # painted surface waiting to be lit -- it is where four months of tyre
    # rubber, brake dust and blown sand end up, because nothing sweeps it and
    # the rain that would wash it runs along it rather than across.  A dirty
    # surface in blue light reads as dirt; a clean one reads as blue paint.
    n_film = t.noise(t.vmath("SCALE", P, scale=1.0), 5.2, 7.0, 0.58)
    film_m = t.math("MULTIPLY", t.maprange(ridge, 0.72, 0.05, 0.20, 1.0),
                    t.maprange(n_film, 0.28, 0.80, 0.35, 1.0))
    film_m = t.math("MULTIPLY", film_m, t.maprange(age, 0.0, 1.0, 0.55, 1.0))
    col = t.cmix(t.math("MULTIPLY", film_m, 0.48), col, (0.0430, 0.0400, 0.0355))

    # ---- 6c. speckle ------------------------------------------------------
    # 1.4 mm grit and tyre-crumb sitting ON the paint, everywhere, not only in
    # the troughs.  Two pixels each at 1493 px/m -- which is precisely the
    # frequency the 3x peep showed the surface had none of, and the reason a
    # correct bump stack still read as smooth: there was nothing at the pixel
    # scale for the eye to lock onto.
    v_spk = t.vor(t.vmath("SCALE", P, scale=1.0), 700.0, "F1", 0, 1.0)
    spk_id = t.vor(t.vmath("SCALE", P, scale=1.0), 700.0, "F1", 1, 1.0)
    spk = t.math("MULTIPLY", t.maprange(v_spk, 0.30, 0.16, 0.0, 1.0),
                 t.maprange(spk_id, 0.62, 0.78, 0.0, 1.0))
    spk = t.math("MULTIPLY", spk,
                 t.maprange(t.noise(t.vmath("SCALE", P, scale=1.0),
                                    16.0, 5.0, 0.55), 0.30, 0.70, 0.25, 1.0))
    col = t.cmix(t.math("MULTIPLY", spk, 0.70), col, PAL["rubber"])
    v_spk2 = t.vor(t.vmath("SCALE", P, scale=1.0), 1150.0, "F1", 0, 1.0)
    spk2 = t.math("MULTIPLY", t.maprange(v_spk2, 0.32, 0.18, 0.0, 1.0),
                  t.maprange(t.noise(t.vmath("SCALE", P, scale=1.0),
                                     9.0, 4.0, 0.55), 0.45, 0.80, 0.0, 1.0))
    col = t.cmix(t.math("MULTIPLY", spk2, 0.42), col, PAL["agg_pale"])

    # ---- 7. algae on the shaded outer face ------------------------------
    n_alg = t.noise(t.vmath("SCALE", P, scale=1.0), 13.0, 7.0, 0.66)
    alg = t.math("MULTIPLY", t.maprange(tt, 0.55, 1.0, 0.0, 1.0),
                 t.maprange(n_alg, 0.58, 0.86, 0.0, 1.0))
    alg = t.math("MULTIPLY", alg, t.math("MULTIPLY", face, 0.9))
    col = t.cmix(t.math("MULTIPLY", alg, 0.62), col, PAL["algae"])

    # ---- 8. water staining down the faces --------------------------------
    n_run = t.wave(t.vmath("SCALE", Pl, scale=1.0), 26.0, 2.6, 3.0, "Y")
    stain = t.math("MULTIPLY", face, t.maprange(n_run, 0.35, 0.75, 0.0, 0.45))
    col = t.cmix(stain, col, PAL["conc_dark"])

    # ---- 9. roughness ----------------------------------------------------
    # Kerb paint is a chalked, sanded, four-season road paint, not a car body:
    # 0.42 gloss put a sheen on every crest and made the object read as ceramic.
    rgh = t.maprange(n_cast, 0.2, 0.8, 0.84, 0.96)
    rgh = t.fmix(p_mask, rgh, t.maprange(n_pw, 0.2, 0.8, 0.58, 0.84))
    rgh = t.fmix(t.math("MULTIPLY", rub, 0.8), rgh, 0.46)
    rgh = t.fmix(t.math("MULTIPLY", knock, 0.9), rgh, 0.97)
    rgh = t.fmix(t.math("MULTIPLY", dust, 0.7), rgh, 0.97)

    col = t.cmix(t.math("MULTIPLY", bug, 0.55), col, PAL["conc_dark"])

    # ---- 11. the bump stack ---------------------------------------------
    # Everything with a silhouette is already mesh.  These are all below 3 mm of
    # relief and have neither silhouette nor occlusion at 0.670 mm/px.
    #
    # STATED AS RADIANCE MODULATION, NOT MILLIMETRES (itemkit 5b, brief 4a).
    # What the eye judges is not the height of a bump, it is what the bump does
    # to the LIGHT, and under this film's 12.47 deg sun that conversion carries
    # a 4.52x amplifier: m = 2 sin(theta) / tan(e).  Three amplitude sets were
    # rendered and REJECTED on the human figures and every one of them had been
    # chosen in millimetres.
    #
    # THESE EIGHT NUMBERS ARE NOT A RE-TUNE.  Each `modulation_pp` is the value
    # that reproduces the Distance this module already shipped, to the sixth
    # decimal; `work/r2038/prove_noop.py` checks that off the built graph, not
    # off arithmetic that never reached a node.  What has changed is that the
    # module now SAYS WHAT IT IS AIMING THE LIGHT AT, so the next agent can
    # argue with 2.325 instead of guessing at 0.00022 -- and so the depths move
    # if the sun does.
    #
    # WHICH BAND EACH STAGE NAMES.  Where the height is a SUM, a single
    # wavelength for the stage is a choice and not a reading, so the one named
    # is the band that is always present and carries most of the height, and
    # `height_pp` is that band's own weight in the sum: `modulation_pp` is then
    # the modulation of THAT band and not of a hypothetical full-swing height.
    # Where `strength` is a mask node the helper aims at where the mask is 1,
    # and so does this table.  Every band in the stack, at the depth it ships:
    #
    #   [0] bug     w 1.00  lam 11.42 mm  m 3.250  round voids with a 1.1 mm
    #                                              rim: hard_feature, and they
    #                                              act on a few per cent of area
    #   [1] agg     w 0.75  lam 15.73 mm  m 2.108  proud aggregate, gated by
    #       agg2    w 0.35  lam  6.78 mm  m 2.271  skin_gone -- broken faces only
    #   [2] n_fine  w 1.00  lam 25.81 mm  m 0.454  cement fines: isotropic_macro
    #   [3] n_skin  w 1.00  lam  8.65 mm  m 1.553  the mould face's meso tooth
    #   [4] n_tooth w 1.00  lam  1.82 mm  m 2.325  the ~1 mm grain of the fines
    #   [5] spk     w 0.85  lam  3.10 mm  m 3.872  grit and tyre crumb sitting ON
    #       spk2    w 0.45  lam  1.89 mm  m 3.445  the paint: particles, not a
    #                                              field -- both are sparse
    #   [6] ply     w 1.00  lam  1.05 mm  m 6.050  mould-board grain, and it is
    #                                              DIRECTIONAL, not isotropic
    #   [7] n_pw    w 1.00  lam 34.78 mm  m 0.180  paint mottle: isotropic_micro
    #
    # [3] AND [4] ARE THE TWO TO ARGUE WITH, and they are left alone.  They are
    # the only UNGATED ISOTROPIC fields in the stack, and 1.55 and 2.33 are over
    # the 1.5 that RELIEF_BANDS supports for something acting on the whole
    # surface -- 2.33 is the neighbourhood of the 3.76 that rendered as coarse
    # stucco.  They ship unchanged because (a) 0.48 mm of mould tooth and
    # 0.154 mm of fines grain are exactly what section 11's own note above says
    # a cast skin measures, so the millimetres are right and it is the sun that
    # is loud, and (b) at 0.670 mm/px a 1.82 mm band is 2.7 px, so the pixel
    # filter takes back part of what m claims -- neither argument is a render,
    # and this stack has never been rendered awake (R2-038).  If the A/B comes
    # back as stucco: [4] at isotropic_micro's 0.45 is Distance x0.187, [3] at
    # isotropic_macro's 0.95 is x0.606.  Do not split the difference.
    #
    # THE WAVELENGTHS ARE WRITTEN FROM THE SAME LITERALS THAT PICKED THE SCALES.
    # Writing 0.01142 here instead of `K.VORONOI_WAVELENGTH_FACTOR / 190.0`
    # would be a second copy of a measured constant.
    LAM_BUG = K.VORONOI_WAVELENGTH_FACTOR / 190.0        # 11.42 mm
    LAM_AGG = K.VORONOI_WAVELENGTH_FACTOR / 138.0        # 15.73 mm
    LAM_FINE = K.NOISE_WAVELENGTH_FACTOR / 62.0          # 25.81 mm
    LAM_SKIN = K.NOISE_WAVELENGTH_FACTOR / 185.0         #  8.65 mm
    LAM_TOOTH = K.NOISE_WAVELENGTH_FACTOR / 880.0        #  1.82 mm
    LAM_SPK = K.VORONOI_WAVELENGTH_FACTOR / 700.0        #  3.10 mm
    # R2-058: THIS READ `1.0 / 300.0` AND WAS 3.183x TOO LONG. Blender's Wave
    # multiplies the coordinate by 20 before the sine, so a band is
    # 2*pi/20 = 0.31416 of 1/Scale (measured flat to six digits over Scale
    # 5..230; itemkit WAVE_WAVELENGTH_FACTOR). THE DISTANCE ON THE SOCKET HAS
    # NOT MOVED -- 0.000300 m, the depth this module shipped -- what moved is
    # the declaration: at the true 1.05 mm pitch the same 0.30 mm is a 42.0 deg
    # wall, not a 15.8 deg one, so this stage is m 6.050 and was being reported
    # as 2.460. IT IS NOW ABOVE RELIEF_BANDS["hard_feature"] (ceiling 6.00), by
    # 0.8 %. Reported, not nudged: nudging it would change a surface that was
    # rendered and judged, and this stage is a form-liner arris gated by the
    # cast-skin mask, which is what that band is for.
    LAM_PLY = K.WAVE_WAVELENGTH_FACTOR / 300.0           #  1.05 mm (Wave)
    LAM_PW = K.NOISE_WAVELENGTH_FACTOR / 46.0            # 34.78 mm
    b = t.bump(t.math("MULTIPLY", bug, 1.0), 1.0,
               modulation_pp=3.249931, wavelength_m=LAM_BUG)
    b = t.bump(t.math("ADD", t.math("MULTIPLY", agg_mask, 0.75),
                      t.math("MULTIPLY", t.maprange(v_agg2, 0.0, 0.2, 1.0, 0.0),
                             0.35)),
               t.math("ADD", t.math("MULTIPLY", skin_gone, 0.70), 0.30),
               normal=b, modulation_pp=2.108361, wavelength_m=LAM_AGG,
               height_pp=0.75)
    # the cast skin's own tooth, THROUGH the paint.  Two coats of road paint are
    # 0.55 mm and a mould-face texture is 0.3-0.8 mm, so it does not disappear
    # under them; gating this on (1 - p_mask) is what left the painted crests
    # glassy.
    # the cast skin has TWO scales and the first build had neither: a 5-6 mm
    # meso-tooth from the mould face and a ~1 mm grain from the fines.  A single
    # 16 mm noise reads as marble, which is what the 0.8 m frame showed.
    n_skin = t.noise(t.vmath("SCALE", P, scale=1.0), 185.0, 6.0, 0.62)
    n_tooth = t.noise(t.vmath("SCALE", P, scale=1.0), 880.0, 4.0, 0.58)
    b = t.bump(t.math("MULTIPLY", n_fine, 1.0), 0.55, normal=b,
               modulation_pp=0.453554, wavelength_m=LAM_FINE)
    b = t.bump(t.math("MULTIPLY", n_skin, 1.0), 0.80, normal=b,
               modulation_pp=1.553352, wavelength_m=LAM_SKIN)
    b = t.bump(t.math("MULTIPLY", n_tooth, 1.0), 0.70, normal=b,
               modulation_pp=2.325456, wavelength_m=LAM_TOOTH)
    b = t.bump(t.math("ADD", t.math("MULTIPLY", spk, 0.85),
                      t.math("MULTIPLY", spk2, 0.45)), 1.0, normal=b,
               modulation_pp=3.871931, wavelength_m=LAM_SPK, height_pp=0.85)
    b = t.bump(t.wave(t.vmath("SCALE", Pl, scale=1.0), 300.0, 0.6, 2.0, "X"),
               t.math("ADD", t.math("MULTIPLY",
                                    t.math("SUBTRACT", 1.0, p_mask), 0.22),
                      0.10), normal=b,
               modulation_pp=6.049694, wavelength_m=LAM_PLY)
    b = t.bump(t.math("MULTIPLY", n_pw, 1.0),
               t.math("MULTIPLY", p_mask, 0.30), normal=b,
               modulation_pp=0.179661, wavelength_m=LAM_PW)

    bs = t.n("ShaderNodeBsdfPrincipled")
    t.pin(bs, 0, col)
    t.pin(bs, 2, rgh)
    t.pin_named(bs, "Normal", b)
    t.pin(bs, 14, 0.16)                      # a little specular; it is not chalk
    out = t.n("ShaderNodeOutputMaterial")
    t.t.links.new(bs.outputs[0], out.inputs[0])
    return t.m


# ==============================================================================
#  7.  BUILD
# ==============================================================================

def _coll(name, parent=None):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(c)
    return c


def purge():
    for cname in (COLL,):
        root = bpy.data.collections.get(cname)
        if root:
            stack, seen = [root], []
            while stack:
                c = stack.pop()
                seen.append(c)
                stack.extend(list(c.children))
            for c in seen:
                for o in list(c.objects):
                    bpy.data.objects.remove(o, do_unlink=True)
            for c in seen:
                bpy.data.collections.remove(c)
    for lib in (bpy.data.objects, bpy.data.meshes, bpy.data.materials,
                bpy.data.lights, bpy.data.cameras, bpy.data.worlds):
        for d in list(lib):
            if d.name.startswith(PFX) or d.name.startswith(XPFX):
                try:
                    lib.remove(d)
                except Exception:
                    pass


def _unit_world_xy(u):
    r = run_records()[u["rid"]]
    tm = 0.5 * (ROW_T[u["row"]][0] + ROW_T[u["row"]][1])
    X, Y, H, _ = C.centreline_arrays(np.array([u["s_m"]]))
    uo = u["sign"] * (C.half_width(u["s_m"]) + tm * KERB_W)
    return (float(X[0] - math.sin(H[0]) * uo), float(Y[0] + math.cos(H[0]) * uo))


def grade_lod(units, anchor):
    if not anchor:
        for u in units:
            u["lod"] = 1
        return
    A = np.asarray(anchor, float)[:, :2]
    for u in units:
        x, y = _unit_world_xy(u)
        d = float(np.min(np.hypot(A[:, 0] - x, A[:, 1] - y)))
        u["lod"] = lod_of(d)
        u["anchor_d"] = d


def build(lod_anchor=None, scene=None, stats=None, limit=None, runs=None,
          uniform_lod=None):
    """Emit the item.  ONE OBJECT PER PRECAST ELEMENT into W_Item_KerbPrecastUnit.

    lod_anchor   list of world points (the camera path).  Mesh density is graded
                 by distance to the nearest of them.  None -> uniform LOD 1.
    runs         restrict to these run ids (debug).
    uniform_lod  force one LOD for everything (debug / selftest).
    """
    scene = scene or bpy.context.scene
    purge()
    root = _coll(COLL)
    mat = mat_kerb()
    us = unit_records()
    if runs is not None:
        us = [u for u in us if u["rid"] in set(runs)]
    grade_lod(us, lod_anchor)
    if uniform_lod is not None:
        for u in us:
            u["lod"] = int(uniform_lod)
    if limit:
        us = us[:limit]

    st = stats if stats is not None else {}
    st.setdefault("units", 0); st.setdefault("tris", 0)
    st.setdefault("lod", [0, 0, 0, 0]); st.setdefault("lengths", [])
    st.setdefault("ngroup", []); st.setdefault("ncrest", [])

    for i, u in enumerate(us):
        ob, tri = build_unit(u, root, mat, u["lod"])
        st["units"] += 1
        st["tris"] += tri
        st["lod"][min(u["lod"], 3)] += 1
        st["lengths"].append(u["L"])
        st["ngroup"].append(u["ngroup"])
        st["ncrest"].append(u["ncrest"])
        if (i + 1) % 400 == 0:
            log("   ... %d/%d units, %.2f M tris" % (i + 1, len(us), st["tris"] / 1e6))

    C.stamp(root)
    root["item"] = ITEM
    root["units"] = st["units"]
    log("BUILT %d elements, %.3f M tris  (LOD %s)"
        % (st["units"], st["tris"] / 1e6, st["lod"]))
    return root


# ==============================================================================
#  8.  THE INTERFACE OTHER ITEMS CALL
# ==============================================================================

def _unit_end_frame(u, at_start):
    """World frame of one end face of a unit: point, tangent, outboard, up."""
    s = u["s_a"] if at_start else u["s_b"]
    tm = 0.5 * (ROW_T[u["row"]][0] + ROW_T[u["row"]][1])
    X, Y, H, _ = C.centreline_arrays(np.array([s]))
    uo = u["sign"] * (C.half_width(s) + tm * KERB_W)
    p = np.array([float(X[0] - math.sin(H[0]) * uo),
                  float(Y[0] + math.cos(H[0]) * uo), 0.0])
    tg = np.array([math.cos(H[0]), math.sin(H[0]), 0.0])
    nm = np.array([-math.sin(H[0]), math.cos(H[0]), 0.0]) * u["sign"]
    z0, grad, cross, _ = _seating(u, run_records()[u["rid"]])
    p[2] = z0 + grad * (s - u["s_m"]) + u["dz"]
    return p, tg, nm


def joint_sites(kind="all"):
    """Every joint in the kerb, world frame.  For ``kerb_bedding_joint``.

    kind 'transverse' -> the gap between two consecutive elements in a row:
         {s, side, row, world, tangent, normal, gap_m, step_m, top_z}
    kind 'longitudinal' -> the 10 mm mortar line at T = 0.400, sampled every
         0.5 m: {s, side, world, tangent, normal, gap_m, step_m}
    """
    us = unit_records()
    out = []
    by = {}
    for u in us:
        by.setdefault((u["rid"], u["row"]), []).append(u)
    if kind in ("all", "transverse"):
        for key, lst in by.items():
            lst.sort(key=lambda q: q["s_a"])
            for a, b in zip(lst[:-1], lst[1:]):
                pa, tg, nm = _unit_end_frame(a, False)
                pb, _, _ = _unit_end_frame(b, True)
                out.append(dict(kind="transverse", rid=a["rid"], row=a["row"],
                                side=int(a["sign"]), s=0.5 * (a["s_b"] + b["s_a"]),
                                world=[0.5 * (pa[0] + pb[0]), 0.5 * (pa[1] + pb[1]),
                                       0.5 * (pa[2] + pb[2])],
                                tangent=list(tg), normal=list(nm),
                                gap_m=float(b["s_a"] - a["s_b"]),
                                step_m=float(pb[2] - pa[2]),
                                uid_a=a["uid"], uid_b=b["uid"]))
    if kind in ("all", "longitudinal"):
        for r in run_records():
            s = r["s0"] + r["ramp_in"]
            while s < r["s1"] - r["ramp_out"]:
                X, Y, H, _ = C.centreline_arrays(np.array([s]))
                uo = r["sign"] * (C.half_width(s) + ROW_SPLIT * KERB_W)
                out.append(dict(kind="longitudinal", rid=r["rid"], row=-1,
                                side=int(r["sign"]), s=float(s),
                                world=[float(X[0] - math.sin(H[0]) * uo),
                                       float(Y[0] + math.cos(H[0]) * uo),
                                       float(C.ground_z(s, uo)
                                             + base_z(ROW_SPLIT))],
                                tangent=[math.cos(H[0]), math.sin(H[0]), 0.0],
                                normal=[-math.sin(H[0]) * r["sign"],
                                        math.cos(H[0]) * r["sign"], 0.0],
                                gap_m=JOINT_W, step_m=0.0))
                s += 0.5
    return out


def ramp_sites():
    """The 70 terminals, for ``kerb_end_ramp``.

    Each record gives the station the serrated run stops at, the ramp length
    reserved for it, and the CROSS-SECTION it must marry to at that station, so
    the ramp's top edge and the last element's end face are the same line.
    """
    out = []
    for r in run_records():
        for at_start in (True, False):
            s = r["s0"] if at_start else r["s1"]
            s_join = (r["s0"] + r["ramp_in"]) if at_start else (r["s1"] - r["ramp_out"])
            X, Y, H, _ = C.centreline_arrays(np.array([s_join]))
            uo = r["sign"] * (C.half_width(s_join) + 0.5 * KERB_W)
            out.append(dict(rid=r["rid"], tag=r["tag"], side=int(r["sign"]),
                            is_start=bool(at_start),
                            s_toe=float(s), s_join=float(s_join),
                            length_m=float(r["ramp_in"] if at_start else r["ramp_out"]),
                            world=[float(X[0] - math.sin(H[0]) * uo),
                                   float(Y[0] + math.cos(H[0]) * uo),
                                   float(C.ground_z(s_join, uo))],
                            tangent=[math.cos(H[0]), math.sin(H[0]), 0.0],
                            normal=[-math.sin(H[0]) * r["sign"],
                                    math.cos(H[0]) * r["sign"], 0.0],
                            section=dict(width_m=KERB_W,
                                         lip_inner=LIP_INNER, lip_outer=LIP_OUTER,
                                         serr_amp=SERR_AMP, serr_pitch=SERR_PITCH,
                                         phase=float(r["phase"]),
                                         row_split=ROW_SPLIT, joint_w=JOINT_W)))
    return out


def trough_line(side=None, ds=1.0):
    """The toe of the kerb on both faces, where grit and dust collect.

    For ``dust_drift``.  Returns, per sample: the world point at the track-side
    toe (T = 0) and at the outer toe (T = 1), the local shadow depth (how far
    the kerb stands proud there) and the run's strike intensity, because grit
    drifts into the lee and the lee is decided by the section, not by taste.
    """
    out = []
    for r in run_records():
        if side is not None and abs(r["sign"] - side) > 1e-6:
            continue
        s = r["s0"] + r["ramp_in"]
        while s < r["s1"] - r["ramp_out"]:
            Wh = C.half_width(s)
            X, Y, H, _ = C.centreline_arrays(np.array([s]))
            rec = dict(rid=r["rid"], s=float(s), side=int(r["sign"]))
            for tag, T in (("inner", 0.0), ("outer", 1.0)):
                uo = r["sign"] * (Wh + T * KERB_W)
                rec[tag] = [float(X[0] - math.sin(H[0]) * uo),
                            float(Y[0] + math.cos(H[0]) * uo),
                            float(C.ground_z(s, uo))]
                rec[tag + "_proud"] = float(base_z(T))
            out.append(rec)
            s += ds
    return out


def interface_json(path=None):
    d = dict(
        item=ITEM, version=__version__,
        section=dict(width_m=KERB_W, lip_inner_m=LIP_INNER, lip_outer_m=LIP_OUTER,
                     serr_amp_m=SERR_AMP, serr_pitch_m=SERR_PITCH, peak_m=PEAK,
                     serr_crest_r_m=SERR_R, serr_fillet_r_m=SERR_RF,
                     serr_d_arc_m=SERR_D_ARC, serr_d_fillet_m=SERR_D_FIL,
                     serr_land_m=SERR_LAND, amp_at_lip=AMP_AT_LIP,
                     row_split_T=ROW_SPLIT, joint_w_m=JOINT_W,
                     row_T=[list(x) for x in ROW_T], row_w_m=list(ROW_W),
                     chamfer=dict(track=CH_TRACK, outer=CH_OUTER,
                                  joint=CH_JOINT, end=CH_END),
                     embed_m=EMBED),
        runs=[{k: (v if not isinstance(v, np.floating) else float(v))
               for k, v in r.items()} for r in run_records()],
        ramps=ramp_sites(),
        neg_kerb_splits=[list(x) for x in NEG_SPLITS],
        counts=dict(runs=len(run_records()), units=len(unit_records()),
                    declared=INSTANCES_DECLARED),
        lod=[list(x) for x in LOD], lod_radii=list(LOD_RADII),
    )
    if path:
        json.dump(d, open(path, "w"), indent=1)
    return d


# ==============================================================================
#  9.  TEST-SCENE STAND-INS  —  owned by OTHER items, prefix KPUX_
# ==============================================================================

def _graded(fine_lo, fine_hi, d_fine, far_lo, far_hi, growth=1.19, d_max=4.0):
    """Samples that are `d_fine` apart in the middle and grow geometrically out
    to `far_lo`/`far_hi`.  One array, so there is no seam to reconcile."""
    mid = list(np.arange(fine_lo, fine_hi + 1e-9, d_fine))
    x, d = fine_hi, d_fine
    while x < far_hi:
        d = min(d * growth, d_max); x += d; mid.append(min(x, far_hi))
    x, d = fine_lo, d_fine
    while x > far_lo:
        d = min(d * growth, d_max); x -= d; mid.append(max(x, far_lo))
    return np.unique(np.round(np.array(mid), 5))


def build_ground(coll, s_mid, span=44.0, sign=1.0):
    """The racing surface, the painted verge and the runoff platform under and
    around the kerb, so the macro is not shot over a void.

    Owned by build_surface (asphalt, verge paint) and build_barriers (platform).
    A STAND-IN, prefixed accordingly: not one triangle of it is this item's.

    IT REACHES 150 m, AND THAT IS NOT DECORATION.  The first macro rendered the
    serration troughs electric blue: they are in the sun's shadow at 12.47 deg
    and lit only by what is around them, and a 52 x 16 m patch of ground leaves
    two thirds of the lower hemisphere as open sky.  A kerb in the world has
    ground under that hemisphere, and the warm bounce off it is most of what is
    in a shadowed trough.  Coarse far away, 55 mm at the kerb -- one mesh, so
    there is no seam and no lit ledge where two stand-ins would have met.
    """
    ds = 0.055
    S = s_mid + _graded(-0.5 * span, 0.5 * span, ds, -150.0, 150.0)
    Wh = C.half_width(S)
    # inboard across the racing surface, the 1.5 m kerb band (left as the road
    # datum -- the elements stand on it), the 1.0 m verge, then the runoff
    # platform and the ground beyond it.
    us = np.concatenate([
        _graded(-6.0, -0.35, 0.22, -40.0, -6.0),
        np.linspace(-0.30, 0.0, 10),
        np.linspace(0.02, KERB_W, 18),
        np.linspace(KERB_W + 0.02, KERB_W + C.VERGE_W, 14),
        _graded(KERB_W + C.VERGE_W + 0.1, KERB_W + C.VERGE_W + 9.0, 0.42,
                KERB_W + C.VERGE_W + 0.1, 150.0)])
    U = sign * (Wh[:, None] + us[None, :])
    S2 = np.broadcast_to(S[:, None], U.shape)
    Z = np.asarray(C.ground_z(S2, U), float)
    Xc, Yc, H, _ = C.centreline_arrays(S2.ravel())
    Xw = (Xc - np.sin(H) * U.ravel()).reshape(U.shape)
    Yw = (Yc + np.cos(H) * U.ravel()).reshape(U.shape)
    V = np.stack([Xw.ravel(), Yw.ravel(), Z.ravel()], axis=1)
    ny, nu = U.shape
    idx = np.arange(ny * nu).reshape(ny, nu)
    if sign > 0:
        Q = np.stack([idx[:-1, :-1], idx[1:, :-1], idx[1:, 1:], idx[:-1, 1:]],
                     axis=-1).reshape(-1, 4)
    else:
        Q = np.stack([idx[:-1, :-1], idx[:-1, 1:], idx[1:, 1:], idx[1:, :-1]],
                     axis=-1).reshape(-1, 4)
    ctr = V.mean(axis=0)
    me = _new_mesh(XPFX + "Ground", V - ctr, Q, smooth_deg=None)
    # bake the across-section coordinate so the stand-in shader can put the
    # white line and the green verge where build_surface puts them
    band = np.broadcast_to(us[None, :], U.shape).ravel()
    a = me.attributes.new("kpx_u", "FLOAT", "POINT")
    a.data.foreach_set("value", np.ascontiguousarray(band, np.float32))
    me.materials.append(_mat_ground())
    ob = bpy.data.objects.new(XPFX + "Ground", me)
    ob.location = tuple(float(x) for x in ctr)
    coll.objects.link(ob)
    return ob


def _mat_ground():
    t = NT(XPFX + "GroundMat")
    co = t.n("ShaderNodeTexCoord")
    P = (co, 3)
    u = t.attr("kpx_u")
    # 10-14 mm surface course: the coarse stone is 62 mm apart, and at 1493 px/m
    # every one of them is 15-20 px across.  A flat dark grey here is the same
    # placeholder the brief rejected on the grass.
    v1 = t.vor(P, 62.0, "F1", 0, 1.0)
    vid = t.vor(P, 62.0, "F1", 1, 1.0)
    v2 = t.vor(P, 195.0, "F1", 0, 1.0)
    v3 = t.vor(P, 620.0, "F1", 0, 1.0)
    n1 = t.noise(P, 3.2, 8.0, 0.60)
    n2 = t.noise(P, 95.0, 7.0, 0.60)
    n3 = t.noise(P, 640.0, 4.0, 0.55)
    binder = t.cmix(t.maprange(n1, 0.28, 0.72, 0.0, 1.0),
                    (0.0126, 0.0122, 0.0120), (0.0262, 0.0250, 0.0238))
    stone = t.cmix(t.maprange(vid, 0.2, 0.8, 0.0, 1.0),
                   (0.0430, 0.0410, 0.0385), (0.1150, 0.1090, 0.0995))
    asph = t.cmix(t.math("MULTIPLY", t.maprange(v1, 0.03, 0.24, 1.0, 0.0),
                         t.maprange(n2, 0.30, 0.72, 0.45, 1.0)), binder, stone)
    asph = t.cmix(t.math("MULTIPLY", t.maprange(v2, 0.02, 0.15, 1.0, 0.0), 0.35),
                  asph, (0.0640, 0.0610, 0.0570))
    # rubber laid down on the racing line, and the swept clean strip at the edge
    rub = t.math("MULTIPLY", t.maprange(u, -2.6, -0.9, 1.0, 0.0),
                 t.maprange(n2, 0.25, 0.70, 0.45, 1.0))
    asph = t.cmix(t.math("MULTIPLY", rub, 0.55), asph, (0.0132, 0.0128, 0.0126))

    # the 100 mm track-edge white line, then the 1.0 m green verge outboard of
    # the kerb -- both painted asphalt, both build_surface's.  A road line is
    # not white: it is a worn thermoplastic that the aggregate shows through.
    line = t.math("MULTIPLY",
                  t.maprange(u, -0.116, -0.099, 0.0, 1.0),
                  t.maprange(u, -0.016, -0.001, 1.0, 0.0))
    line = t.math("MULTIPLY", line, t.maprange(n2, 0.22, 0.62, 0.35, 1.0))
    line = t.math("MULTIPLY", line, t.maprange(v3, 0.0, 0.30, 0.55, 1.0))
    verge = t.math("MULTIPLY",
                   t.maprange(u, KERB_W - 0.01, KERB_W + 0.02, 0.0, 1.0),
                   t.maprange(u, KERB_W + C.VERGE_W - 0.03,
                              KERB_W + C.VERGE_W, 1.0, 0.0))
    # the green is a thin coat rolled onto open-textured asphalt: it survives on
    # the binder and wears off the stone, which is why real green run-off reads
    # mottled and never as a flat field
    vwear = t.math("MULTIPLY", t.maprange(v1, 0.03, 0.20, 0.30, 1.0),
                   t.maprange(n2, 0.20, 0.70, 0.45, 1.0))
    verge = t.math("MULTIPLY", verge, vwear)
    gcol = t.cmix(t.maprange(t.noise(P, 14.0, 6.0, 0.55), 0.35, 0.72, 0.0, 1.0),
                  (0.0175, 0.0530, 0.0225), (0.0330, 0.0910, 0.0345))
    col = t.cmix(line, asph, (0.3050, 0.3010, 0.2880))
    col = t.cmix(verge, col, gcol)
    col = t.cmix(t.math("MULTIPLY", t.maprange(n3, 0.62, 0.88, 0.0, 1.0), 0.35),
                 col, (0.0180, 0.0175, 0.0170))
    # beyond the runoff platform this stand-in is terrain, not asphalt: dry
    # summer grass over gravel.  It exists to fill the lower hemisphere with
    # warm bounce, which is what a shadowed serration trough is actually lit by.
    # the transition wanders: a dead-straight line parallel to the track, 16 m
    # out, is a giveaway even on a stand-in
    wob = t.math("MULTIPLY", t.maprange(t.noise(P, 0.22, 4.0, 0.55),
                                        0.2, 0.8, -4.5, 4.5), 1.0)
    uu = t.math("ADD", u, wob)
    far = t.maprange(uu, KERB_W + C.VERGE_W + 6.0, KERB_W + C.VERGE_W + 16.0,
                     0.0, 1.0)
    far = t.math("MAXIMUM", far, t.maprange(uu, -9.0, -16.0, 0.0, 1.0))
    ter = t.cmix(t.maprange(t.noise(P, 1.4, 7.0, 0.60), 0.30, 0.72, 0.0, 1.0),
                 (0.0470, 0.0525, 0.0270), (0.1180, 0.1085, 0.0640))
    ter = t.cmix(t.math("MULTIPLY", t.maprange(n1, 0.55, 0.85, 0.0, 1.0), 0.55),
                 ter, (0.1520, 0.1330, 0.0850))
    col = t.cmix(far, col, ter)
    b = t.bump(t.math("ADD", t.math("MULTIPLY",
                                    t.maprange(v1, 0.0, 0.22, 1.0, 0.0), 0.85),
                      t.math("MULTIPLY", t.maprange(v2, 0.0, 0.16, 1.0, 0.0),
                             0.45)), 1.0, 0.0055)
    b = t.bump(t.math("MULTIPLY", v3, 0.8), 0.55, 0.0011, normal=b)
    b = t.bump(t.math("MULTIPLY", n3, 1.0), 0.40, 0.00035, normal=b)
    # Roughness 0.66 put a broad forward-scatter lobe on the whole road, and
    # looking into a 12.47 deg sun that rendered 40 m of asphalt as featureless
    # wet sand.  Dry open-textured asphalt is 0.84-0.98 and its specular is
    # closer to 0.04 than to 0.14.
    bs = t.n("ShaderNodeBsdfPrincipled")
    t.pin(bs, 0, col); t.pin(bs, 2, t.maprange(n2, 0.2, 0.8, 0.84, 0.985))
    t.pin_named(bs, "Normal", b); t.pin(bs, 14, 0.045)
    o = t.n("ShaderNodeOutputMaterial")
    t.t.links.new(bs.outputs[0], o.inputs[0])
    return t.m


def build_bedding(coll, units):
    """The mortar bed showing in the joints.  Owned by ``kerb_bedding_joint``.

    Without it every transverse and longitudinal joint is an open 10 mm slot to
    20 mm below the datum, which at a 12.47 deg sun is a black line the whole
    length of the circuit.  A STAND-IN so the macro is honest about what the
    joint looks like; the real item replaces it with squeeze-out, washout and
    weed.  Prefixed KPUX_.
    """
    if not units:
        return None
    V, Q = [], []
    base = 0
    for u in units:
        r = run_records()[u["rid"]]
        n = max(int(u["L"] / 0.06) + 2, 3)
        S = np.linspace(u["s_a"] - 0.02, u["s_b"] + 0.02, n)
        t0, t1 = ROW_T[u["row"]]
        Ts = np.array([t0 - 0.008, t1 + 0.008])
        Wh = C.half_width(S)
        U = u["sign"] * (Wh[:, None] + Ts[None, :] * KERB_W)
        S2 = np.broadcast_to(S[:, None], U.shape)
        z0, grad, cross, tm = _seating(u, r)
        Z = (z0 + grad * (S2 - u["s_m"]) + cross * ((np.broadcast_to(
            Ts[None, :], U.shape) - tm) * KERB_W)
            + base_z(np.broadcast_to(Ts[None, :], U.shape)) - 0.006)
        Xc, Yc, H, _ = C.centreline_arrays(S2.ravel())
        Xw = (Xc - np.sin(H) * U.ravel()).reshape(U.shape)
        Yw = (Yc + np.cos(H) * U.ravel()).reshape(U.shape)
        V.append(np.stack([Xw.ravel(), Yw.ravel(), Z.ravel()], axis=1))
        idx = np.arange(U.size).reshape(U.shape) + base
        Q.append(np.stack([idx[:-1, :-1], idx[1:, :-1], idx[1:, 1:], idx[:-1, 1:]],
                          axis=-1).reshape(-1, 4))
        base += U.size
    V = np.concatenate(V); Q = np.concatenate(Q)
    ctr = V.mean(axis=0)
    me = _new_mesh(XPFX + "Bedding", V - ctr, Q, smooth_deg=None)
    t = NT(XPFX + "BeddingMat")
    co = t.n("ShaderNodeTexCoord")
    P = (co, 3)
    n1 = t.noise(P, 34.0, 7.0, 0.6)
    n2 = t.noise(P, 260.0, 5.0, 0.6)
    v1 = t.vor(P, 480.0, "F1", 0, 1.0)
    col = t.cmix(t.maprange(n1, 0.3, 0.75, 0.0, 1.0),
                 PAL["mortar"], PAL["conc_dark"])
    col = t.cmix(t.math("MULTIPLY", t.maprange(v1, 0.0, 0.3, 1.0, 0.0), 0.5),
                 col, PAL["grit"])
    b = t.bump(t.math("ADD", t.math("MULTIPLY", n2, 0.7),
                      t.math("MULTIPLY", v1, 0.5)), 0.8, 0.0012)
    bs = t.n("ShaderNodeBsdfPrincipled")
    t.pin(bs, 0, col); t.pin(bs, 2, t.maprange(n1, 0.2, 0.8, 0.85, 0.97))
    t.pin_named(bs, "Normal", b); t.pin(bs, 14, 0.10)
    o = t.n("ShaderNodeOutputMaterial")
    t.t.links.new(bs.outputs[0], o.inputs[0])
    me.materials.append(t.m)
    ob = bpy.data.objects.new(XPFX + "Bedding", me)
    ob.location = tuple(float(x) for x in ctr)
    coll.objects.link(ob)
    return ob


# ==============================================================================
# 10.  LIGHT AND CAMERA
# ==============================================================================

def contract_light(scene=None, coll=None):
    """The film's sun and sky, exactly as world_contract measured them."""
    from mathutils import Vector
    scene = scene or bpy.context.scene
    w = bpy.data.worlds.new(PFX + "World")
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    sky = nt.nodes.new("ShaderNodeTexSky")
    avail = {e.identifier for e in sky.bl_rna.properties["sky_type"].enum_items}
    for want in ("MULTIPLE_SCATTERING", "SINGLE_SCATTERING", "HOSEK_WILKIE"):
        if want in avail:
            sky.sky_type = want
            break
    for attr, val in (("sun_disc", False),
                      ("sun_size", math.radians(C.SUN_ANGULAR_DIAM_DEG)),
                      ("sun_intensity", 1.0),
                      ("sun_elevation", math.radians(C.SUN_ELEV_DEG)),
                      ("sun_rotation", math.radians(C.SKY_SUN_ROTATION_DEG)),
                      ("altitude", C.SKY_ALTITUDE),
                      ("air_density", C.SKY_AIR),
                      ("aerosol_density", C.SKY_AEROSOL),
                      ("ozone_density", C.SKY_OZONE)):
        if hasattr(sky, attr):
            setattr(sky, attr, val)
    bg.inputs["Strength"].default_value = 1.0
    nt.links.new(sky.outputs["Color"], bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    scene.world = w

    lt = bpy.data.lights.new(PFX + "Sun", "SUN")
    lt.energy = C.SUN_ENERGY
    lt.color = C.SUN_COLOR
    lt.angle = math.radians(C.SUN_ANGULAR_DIAM_DEG)
    ob = bpy.data.objects.new(PFX + "Sun", lt)
    d = Vector(C.SUN_DIR)
    ob.rotation_mode = "QUATERNION"
    ob.rotation_quaternion = d.to_track_quat("Z", "Y")
    ob.location = (d.x * 2000.0, d.y * 2000.0, d.z * 2000.0)
    ob.visible_camera = False
    (coll or scene.collection).objects.link(ob)

    scene.view_settings.view_transform = C.VIEW_TRANSFORM
    try:
        scene.view_settings.look = C.VIEW_LOOK
    except Exception:
        pass
    scene.view_settings.exposure = C.REFERENCE_EXPOSURE_EXTERIOR
    log("light: sun %.3f W/m2 elev %.2f deg bearing %.2f deg; %s %.3f EV"
        % (C.SUN_ENERGY, C.SUN_ELEV_DEG, C.SUN_BEARING_DEG,
           C.VIEW_TRANSFORM, C.REFERENCE_EXPOSURE_EXTERIOR))
    return ob


def add_camera(name, loc, look, lens, coll, fstop=None):
    from mathutils import Vector
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = 36.0
    cd.clip_start = 0.005
    cd.clip_end = 20000.0
    ob = bpy.data.objects.new(name, cd)
    ob.location = loc
    d = Vector(look) - Vector(loc)
    ob.rotation_mode = "QUATERNION"
    ob.rotation_quaternion = d.to_track_quat("-Z", "Y")
    coll.objects.link(ob)
    if fstop:
        cd.dof.use_dof = True
        cd.dof.focus_distance = float(d.length)
        cd.dof.aperture_fstop = float(fstop)
    return ob


def hero_unit():
    """WHERE THE MACRO IS SHOT, chosen by score, not by taste.

    Three things decide it and none of them is convenience:
      * it must be on the T4 hairpin apex kerb, because that is the corner the
        film's static camera sits on for 3.9 s (manifest, beat 5);
      * THE SUN MUST RUN ALONG THE KERB.  The serration crests lie ACROSS the
        direction of travel, so a ridge is modelled by light travelling ALONG
        it -- and the first version of this function maximised the opposite,
        picked a unit at rake 0.054, and produced a macro in which a 25 mm
        serration on a 250 mm pitch read as a flat painted stripe.  At a 12.47
        deg sun a crest casts 113 mm of shadow, 45 % of the pitch: that shadow
        IS the object.  The hairpin sweeps 180 deg, so somewhere on it the rake
        is 0.999, and that is where the macro is shot.
      * the unit must carry damage -- a knocked-down group and a chipped arris
        -- because a macro of the one undamaged element on the circuit is a
        claim about the wrong object.
    """
    us = unit_records()
    runs = run_records()
    sun = np.array(C.SUN_DIR[:2], float)
    sun = sun / (np.linalg.norm(sun) + 1e-9)
    best, bs = None, -1e9
    for u in us:
        r = runs[u["rid"]]
        if r["tag"] != "T4" or r["side"] != "in":
            continue
        X, Y, H, _ = C.centreline_arrays(np.array([u["s_m"]]))
        tg = np.array([math.cos(H[0]), math.sin(H[0])])
        rake = abs(float(np.dot(tg, sun)))          # 1 = sun along the kerb
        if rake < 0.80:
            continue
        sc = (3.0 * rake + 1.5 * u["strike"]
              + 0.9 * min(u["ngroup"], 4) / 4.0 + 0.5 * min(u["nchip"], 8) / 8.0
              + 0.6 * (u["row"] == 1))
        if sc > bs:
            best, bs = u, sc
    return best


def macro_rig(u, coll, name, lens=LENS_MM, dist=FILMED_AT_M,
              yaw_deg=52.0, elev_deg=26.0, side=+1, sunward=True, tm=None):
    """A camera at EXACTLY the manifest's distance and lens.

    The aim point is the top of the kerb at the unit's own centre; the camera
    stands `dist` metres from it -- measured, then asserted in the log -- at
    `yaw_deg` off the kerb's own axis and `elev_deg` above its seating plane.

    `sunward` decides WHICH WAY along the kerb.  With the sun running along the
    serrations, standing down-sun and looking back up-sun puts every crest
    shadow facing the lens; standing up-sun hides all of them behind their own
    crests.  Same geometry, same lens, and the difference between an object and
    a stripe.  `side` +1 puts the camera outboard over the verge, -1 inboard
    over the racing surface, which is where the film's own hairpin camera is.
    """
    r = run_records()[u["rid"]]
    if tm is None:
        tm = 0.5 * (ROW_T[u["row"]][0] + ROW_T[u["row"]][1])
    X, Y, H, _ = C.centreline_arrays(np.array([u["s_m"]]))
    uo = u["sign"] * (C.half_width(u["s_m"]) + tm * KERB_W)
    z0, grad, cross, _ = _seating(u, r)
    aim = np.array([float(X[0] - math.sin(H[0]) * uo),
                    float(Y[0] + math.cos(H[0]) * uo),
                    float(z0 + u["dz"] + base_z(tm) + 0.5 * amp(tm))])
    tg = np.array([math.cos(H[0]), math.sin(H[0]), 0.0])
    nm = np.array([-math.sin(H[0]), math.cos(H[0]), 0.0]) * u["sign"]
    sun = np.array([C.SUN_DIR[0], C.SUN_DIR[1], 0.0])
    sun = sun / (np.linalg.norm(sun) + 1e-9)
    st = 1.0 if float(np.dot(tg, sun)) >= 0.0 else -1.0    # tg*st -> toward sun
    ya = math.radians(yaw_deg); el = math.radians(elev_deg)
    along = (-st if sunward else st) * math.cos(ya)
    d = (tg * along + nm * (side * math.sin(ya))) * math.cos(el)
    d = d + np.array([0.0, 0.0, 1.0]) * math.sin(el)
    d = d / np.linalg.norm(d)
    loc = aim + d * dist
    cam = add_camera(name, tuple(loc), tuple(aim), lens, coll)
    return cam, aim, loc


def test_scene(samples=256, limit=None, quick=False, anchor_pad=True):
    """Build the item, light it with the contract sun, and put the manifest's
    own camera on it: 2.500 m away on a 35 mm lens."""
    scene = bpy.context.scene
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)

    u = hero_unit()
    r = run_records()[u["rid"]]
    tm = 0.5 * (ROW_T[u["row"]][0] + ROW_T[u["row"]][1])
    X, Y, H, _ = C.centreline_arrays(np.array([u["s_m"]]))
    uo = u["sign"] * (C.half_width(u["s_m"]) + tm * KERB_W)
    hx = float(X[0] - math.sin(H[0]) * uo)
    hy = float(Y[0] + math.cos(H[0]) * uo)
    anchor = [(hx, hy, 0.0)]
    log("hero unit uid %d  run %s  row %d  s %.1f  L %.3f  ngroup %d  nchip %d"
        % (u["uid"], r["name"], u["row"], u["s_m"], u["L"], u["ngroup"], u["nchip"]))

    root = build(lod_anchor=anchor, scene=scene, limit=limit)
    cams = _coll(COLL + "/Cameras", root)
    stand = _coll(COLL + "/Standins", root)
    contract_light(scene, coll=root)

    # stand-ins, only around the hero site: they exist so the macro is not shot
    # over a void, not to be a second world.
    build_ground(stand, u["s_m"], span=52.0, sign=u["sign"])
    near = [q for q in unit_records()
            if abs(q["s_m"] - u["s_m"]) < 26.0 and q["rid"] == u["rid"]]
    build_bedding(stand, near)

    macro, aim, loc = macro_rig(u, cams, PFX + "CAM_MACRO")
    log("CAM_MACRO at %.4f m on a %.0f mm lens"
        % (float(np.linalg.norm(np.array(loc) - np.array(aim))), LENS_MM))
    # down the run, where the joint rhythm and the unit-to-unit steps are the
    # subject rather than one casting's surface
    macro_rig(u, cams, PFX + "CAM_ALONG", yaw_deg=15.0, elev_deg=9.0)
    # dead square on the section: the profile check
    macro_rig(u, cams, PFX + "CAM_SECTION", yaw_deg=86.0, elev_deg=5.0)
    # from the track side, where the car and the film's own hairpin camera are
    macro_rig(u, cams, PFX + "CAM_TRACKSIDE", yaw_deg=46.0, elev_deg=21.0,
              side=-1)
    # front-lit, to check the object is not only working because it is backlit
    macro_rig(u, cams, PFX + "CAM_FRONTLIT", yaw_deg=52.0, elev_deg=26.0,
              sunward=False)
    # from the driver's eye, at the height the onboard follow crosses it
    macro_rig(u, cams, PFX + "CAM_ONBOARD", yaw_deg=26.0, elev_deg=14.0,
              dist=3.4, lens=35.0, side=-1)
    # the wide, so the run can be judged in its setting
    macro_rig(u, cams, PFX + "CAM_WIDE", yaw_deg=40.0, elev_deg=17.0,
              dist=11.0, lens=50.0)
    # kerb_hero_t4's own station: 0.8 m on a 21 mm lens, so this module can be
    # judged at the distance its dependant will be judged at
    macro_rig(u, cams, PFX + "CAM_HERO08", yaw_deg=44.0, elev_deg=30.0,
              dist=0.8, lens=21.0)

    scene.camera = macro
    scene.render.engine = "CYCLES"
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.cycles.samples = samples
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.008
    scene.cycles.max_bounces = 10
    scene.cycles.diffuse_bounces = 4
    scene.cycles.glossy_bounces = 6
    scene.cycles.use_denoising = True
    return root


# ==============================================================================
# 11.  MEASUREMENT
# ==============================================================================

def selftest(verbose=True):
    fails = []
    n = [0]

    def chk(name, cond, detail=""):
        n[0] += 1
        print("  %s %-56s %s" % ("ok  " if cond else "FAIL", name, detail))
        if not cond:
            fails.append(name)

    print("kerb_precast_unit %s  self test" % __version__)
    print("\n[1] the section against the contract")
    chk("peak = lip_outer + serr_amp = 0.075",
        abs(PEAK - 0.075) < 1e-9, "%.6f" % PEAK)
    chk("plank clearance 0.340 - peak = 0.265",
        abs((0.340 - PEAK) - 0.265) < 1e-9)
    d = np.linspace(-0.125, 0.125, 4001)
    z = serration_z(d)
    chk("serration peaks at 1.0 and troughs at 0.0",
        abs(z.max() - 1.0) < 1e-9 and abs(z.min()) < 1e-12,
        "max %.9f min %.9f" % (z.max(), z.min()))
    dz = np.diff(z * SERR_AMP) / np.diff(d)
    chk("serration profile is C1 (no slope jump > 0.02)",
        float(np.abs(np.diff(dz)).max()) < 0.02,
        "max d(slope) %.5f" % float(np.abs(np.diff(dz)).max()))
    chk("trough land 54.0 mm", abs(SERR_LAND - 0.054040) < 5e-5,
        "%.4f m" % SERR_LAND)
    T = np.linspace(0, 1, 101)
    top = base_z(T) + amp(T)
    ct = C.kerb_top_z(np.full_like(T, 940.0), np.full_like(T, 0.0)) * 0.0
    chk("cast top never exceeds C.kerb_top_z's clearance model",
        bool(np.all(top <= (C.KERB_LIP_INNER_M
                            + (C.KERB_LIP_OUTER_M - C.KERB_LIP_INNER_M) * T
                            + C.KERB_SERRATION_AMP_M) + 1e-12)),
        "max %.5f" % float(top.max()))
    chk("row widths sum to 1.50 m minus one joint",
        abs(ROW_W[0] + ROW_W[1] + JOINT_W - KERB_W) < 1e-9,
        "%.4f + %.4f + %.4f" % (ROW_W[0], ROW_W[1], JOINT_W))

    print("\n[2] the population")
    runs = run_records()
    us = unit_records()
    tot = sum(r["s1"] - r["s0"] for r in runs)
    chk("35 runs -> 70 terminals for kerb_end_ramp", len(runs) == 35,
        "%d runs, %d ramp sites" % (len(runs), len(ramp_sites())))
    L = np.array([u["L"] for u in us])
    chk("every element is 1.85-2.30 m or a declared site-cut closer",
        bool(np.all([(1.84 <= u["L"] <= 2.30) or u["closer"] for u in us])),
        "L %.3f-%.3f m, %d closers"
        % (L.min(), L.max(), sum(1 for u in us if u["closer"])))
    full = np.array([u["L"] for u in us if not u["closer"]])
    chk("full-mould length CV >= 0.03 (the gate's own floor)",
        float(full.std() / full.mean()) >= 0.03,
        "CV %.4f  mean %.3f m" % (full.std() / full.mean(), full.mean()))
    gaps = [j["gap_m"] for j in joint_sites("transverse")]
    steps = [abs(j["step_m"]) for j in joint_sites("transverse")]
    chk("transverse joint gaps are 0-20 mm",
        min(gaps) > -1e-9 and max(gaps) < 0.021,
        "%.1f-%.1f mm, mean %.1f" % (min(gaps) * 1e3, max(gaps) * 1e3,
                                     float(np.mean(gaps)) * 1e3))
    chk("unit-to-unit step sd is the manifest's 2.2 mm scale",
        0.0015 < float(np.std(steps)) < 0.010,
        "sd %.2f mm, max %.2f mm" % (np.std(steps) * 1e3, max(steps) * 1e3))
    ng = np.array([u["ngroup"] for u in us])
    st = np.array([u["strike"] for u in us])
    chk("struck units carry 2-6 knocked-down groups",
        bool(np.all(ng[st > 0.55] >= 2)) and int(ng.max()) <= 6,
        "struck mean %.2f, unstruck mean %.2f, max %d"
        % (ng[st > 0.55].mean() if (st > 0.55).any() else -1,
           ng[st <= 0.25].mean() if (st <= 0.25).any() else -1, ng.max()))
    print("      %d elements over %.1f m of kerb (%.2f m/element); "
          "manifest declares %d" % (len(us), tot, tot * 2.0 / len(us),
                                    INSTANCES_DECLARED))

    print("\n[3] crest registration between the two rows")
    bad = 0
    for r in runs[:6]:
        for u in [q for q in us if q["rid"] == r["rid"]][:12]:
            c = r["phase"] + u["k0"] * SERR_PITCH
            if not (u["s_a"] - 1e-6 <= c <= u["s_b"] + 1e-6):
                bad += 1
    chk("every unit's first crest lies inside the unit", bad == 0, "%d bad" % bad)
    r0 = runs[0]
    rows = {0: [], 1: []}
    for u in us:
        if u["rid"] == r0["rid"]:
            rows[u["row"]].append(u["s_a"])
    off = []
    for a in rows[0]:
        off.append(min(abs(a - b) for b in rows[1]) if rows[1] else 9.0)
    chk("the two rows' transverse joints are staggered, not aligned",
        float(np.median(off)) > 0.10,
        "median offset %.3f m over %d joints" % (float(np.median(off)), len(off)))

    print("\n[4] placement against the contract")
    worst_in, worst_out = 1e9, -1e9
    for u in us[::37]:
        Wh = C.half_width(u["s_m"])
        t0, t1 = ROW_T[u["row"]]
        worst_in = min(worst_in, Wh + t0 * KERB_W + u["dlat"] - Wh)
        worst_out = max(worst_out, t1 * KERB_W + u["dlat"])
    # The kerb is an EDGE-DEFINING family: it may sit at the racing-surface
    # boundary and never inside it.  The setting-out clearance is deliberately
    # one-sided, so the outer edge lands a few mm into the 1.00 m painted verge
    # -- which is where a kerb laid to a string line actually lands, and 9 mm of
    # a 1000 mm verge is not an intrusion into anything.
    chk("no element intrudes inboard of the racing-surface edge",
        worst_in >= 0.0, "worst %+.4f m (setting-out clearance)" % worst_in)
    chk("outer edge stays inside the 1.00 m painted verge",
        worst_out <= KERB_W + 0.050,
        "worst %.4f m = %.1f mm into the verge"
        % (worst_out, (worst_out - KERB_W) * 1e3))

    print("\n[5] mesh, at the LOD the macro is shot at")
    u = hero_unit()
    V, Q, Tr, att, org, basis, info = unit_mesh_arrays(u, 0)
    ex, ey, ez = basis
    chk("recentred: |P| < 1.25 m", float(np.abs(V).max()) < 1.25,
        "max |P| %.4f m" % float(np.abs(V).max()))
    chk("basis is orthonormal, +Z up",
        abs(np.dot(ex, ey)) < 1e-12 and abs(np.linalg.norm(ex) - 1) < 1e-12
        and abs(ez[2] - 1.0) < 1e-12)
    # edge length distribution at the filmed distance
    ln = []
    for q in Q:
        for i in range(4):
            a, b = V[q[i]], V[q[(i + 1) % 4]]
            ln.append(float(np.linalg.norm(a - b)))
    ln = np.sort(np.array(ln))
    p10 = float(ln[len(ln) // 10])
    chk("10th-percentile edge <= 6 px at 2.5 m on 35 mm",
        p10 * PX_PER_M <= 6.0,
        "p10 %.2f mm = %.2f px  (median %.2f mm)"
        % (p10 * 1e3, p10 * PX_PER_M, float(ln[len(ln) // 2]) * 1e3))
    chk("mesh is watertight-ish: skirt reaches BASE_EMBED below the ground",
        info["z_bot"] <= info["z0"] - EMBED + 1e-9,
        "z_bot %.4f, seat %.4f" % (info["z_bot"], info["z0"]))
    print("      hero element: %d verts, %d quads, %d tris, nx %d nT %d"
          % (len(V), len(Q), len(Q) * 2 + len(Tr), info["nx"], info["nT"]))

    print("\n[6] LOD ladder")
    for l in (-1, 0, 1, 2, 3):
        V2, Q2, T2_, _, _, _, i2 = unit_mesh_arrays(u, l)
        print("      LOD %2d: %7d verts %7d quads  nx %4d nT %3d"
              % (l, len(V2), len(Q2), i2["nx"], i2["nT"]))

    print("\n%d checks, %d failures" % (n[0], len(fails)))
    return not fails


def census(stats):
    L = np.array(stats["lengths"]); g = np.array(stats["ngroup"])
    c = np.array(stats["ncrest"])
    print(">> population: %d elements, %.3f M tris" % (stats["units"], stats["tris"] / 1e6))
    print(">>   length  %.3f-%.3f m  mean %.3f  sd %.3f  CV %.4f"
          % (L.min(), L.max(), L.mean(), L.std(), L.std() / L.mean()))
    print(">>   crests  %d-%d  mean %.2f" % (c.min(), c.max(), c.mean()))
    print(">>   knocked-down groups per element: mean %.2f, max %d, "
          "%.1f %% carry at least one"
          % (g.mean(), g.max(), 100.0 * (g > 0).mean()))
    print(">>   LOD %s" % stats["lod"])


# ==============================================================================
# 12.  CLI
# ==============================================================================

def main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", action="store_true")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--interface", default=None)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--samples", type=int, default=256)
    ap.add_argument("--save", default=None)
    ap.add_argument("--render", default=None)
    ap.add_argument("--cam", default=PFX + "CAM_MACRO")
    ap.add_argument("--res", type=int, nargs=2, default=[1920, 1080])
    a = ap.parse_args(argv)

    if a.interface:
        interface_json(os.path.abspath(a.interface))
        log("interface -> %s" % a.interface)
    if a.selftest:
        sys.exit(0 if selftest() else 1)
    if a.test or a.save or a.render:
        test_scene(samples=a.samples, limit=a.limit)
    elif a.build:
        st = {}
        build(stats=st, limit=a.limit)
        census(st)
    if a.save:
        p = os.path.abspath(a.save)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        ext = [i.filepath for i in bpy.data.images if i.source == "FILE"]
        if ext:
            raise SystemExit("REFUSING TO SAVE: external images %s" % ext)
        bpy.ops.wm.save_as_mainfile(filepath=p, compress=True, relative_remap=False)
        log("saved %s (%.1f MB)" % (p, os.path.getsize(p) / 1048576.0))
    if a.render:
        sc = bpy.context.scene
        sc.camera = bpy.data.objects[a.cam]
        sc.render.resolution_x, sc.render.resolution_y = a.res
        sc.cycles.samples = a.samples
        sc.render.filepath = os.path.abspath(a.render)
        os.makedirs(os.path.dirname(sc.render.filepath), exist_ok=True)
        bpy.ops.render.render(write_still=True)
        log("rendered %s" % sc.render.filepath)


if __name__ == "__main__":
    main()
