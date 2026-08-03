#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
armco_post.py — CIRCUIT VITRINE, per-item hero campaign, item ``armco_post``
(zone ``barriers``, wave 1, build order 54, **3 dependants**).

WHAT THIS IS, IN ONE SENTENCE
=============================
Every driven guardrail post on the circuit, built as a **closed cold-rolled
steel shell** with a real wall thickness, real rolled corner radii, a real
punched bolt slot with die-roll and burr, a **hammered driven head** whose zinc
is gone and whose edge has rolled over, an **impact hinge** where a car has hit
it, and its own **collar of disturbed ground** with the crescent rock-gap that a
post which has been leaned on for six years actually has.

    "The single most-repeated object trackside.  Every post is driven, so every
     post has a slightly different height, lean and collar of disturbed ground.
     Identical posts on a perfect line is what made the round-1 barriers read as
     'smeared plastic'."                                  -- the manifest record

Because it is the most-repeated object, it is also the one where a single
repeated mesh would be most visible.  **No two posts in this build share a
mesh.**  Every one of the ~3 250 is meshed from its own record: its own section
family, its own stock length, its own embedment, lean, twist, settlement,
driven-head deformation, impact hinge and collar.  There is no instancer and no
source-mesh pool, which is why the acceptance gate measures this item on the
OBJECT path (3 250 objects > half the declared 3 641) rather than on realized
geometry-nodes instances.

THE PIXEL BUDGET THIS WAS BUILT TO
----------------------------------
    px_per_m = (3840 x 35 / 36) / 2.6 = 1435.9 px/m     ->     1 px = 0.696 mm

    the 1.500 m post                2154 px          (manifest: onscreen_px_4k)
    the 0.982 m that stands proud   1410 px
    the 120 mm section depth         172 px
    the 5.0 mm wall thickness        7.2 px          <- must be geometry
    the 7.5 mm rolled corner         10.8 px         <- must be geometry
    the 9 mm sigma stiffening rib    12.9 px         <- must be geometry
    a 17 x 40 mm bolt slot           24 x 57 px      <- must be a hole
    the 0.35 mm punch die-roll       0.50 px         <- geometry, sub-pixel but
                                                       it is a 57 px long
                                                       highlight, not a point
    the 2.5 mm rolled head burr      3.6 px          <- must be geometry
    the 4 mm collar rim lip          5.7 px          <- must be geometry
    3-8 mm stones in the collar      4-11 px         <- must be geometry
    zinc spangle, 5-40 mm            7-57 px         <- shading, and it is

Everything in that list except the spangle is mesh.

===============================================================================
THE PUBLIC INTERFACE  —  this item is a FOUNDATION.  3 items depend on it.
===============================================================================
Dependants named in the manifest, and what each of them must call:

    armco_spacer_block   ``spacer_sites(side)``    the seat between post and rail
    barrier_cable_conduit``conduit_clip_sites(side)``the clip line on the post back
    armco_w_beam         ``post_sites(side)``      (see the note on direction below)

--- 0. WHICH WAY ROUND THE DEPENDENCY GOES ------------------------------------
The manifest lists ``armco_w_beam.depends_on = ['armco_post']`` and
``armco_post.depends_on = []``, but ``armco_w_beam`` was built first (order 52 vs
54) and it had to decide where its splices fall.  A W-beam splice is made AT a
post, so the beam's element breakdown *is* the post line.  Re-deriving it here
would be a second implementation of the same 200 lines, and the two would drift
the first time either changed -- which is exactly the class of defect
``world_contract`` exists to prevent.

    THEREFORE:  ``armco_w_beam.post_sites(side)`` is the authority for WHERE a
    post stands (station and lap centre).  THIS module is the authority for
    WHAT a post is -- section, length, embedment, deformation, head, collar --
    and for the ~62 posts the beam does not name (see §2).

    ``armco_post.post_sites(side)`` returns the ENRICHED record and is what the
    dependants should call.  It is a superset: every field the beam publishes is
    passed through unchanged.

--- 1. THE SECTION ------------------------------------------------------------

    ``SECTIONS``      seven real cold-rolled families, keyed by name:
                      SIGMA_120, SIGMA_100, C_120, U_100, OMEGA_110, RHS_100
                      and RHS_120A (the heavy anchor post at run ends and gate
                      jambs).  Each carries W (width ALONG the barrier), D
                      (depth AWAY from the track), t (wall), and the corner
                      radii.  ``section_profile(fam, lod)`` returns the sampled
                      mid-surface, its outward normals and the index range of
                      the flat front face.
    ``FACE_T``        = 0.283 m.  The post's FRONT FACE lies this far outboard
                      of the barrier traffic face, i.e. of
                      ``world_contract.barrier_offset(s, side)``.  It is
                      ``armco_w_beam.SEC_D`` (0.083, traffic face -> centre
                      ridge) plus ``SPACER_D``.
    ``SPACER_D``      = 0.200 m.  The depth of ``armco_spacer_block``, which is
                      the manifest's own ``px_measured_dimension_m`` for that
                      item.  THIS IS THE NUMBER THAT ITEM MUST BUILD TO.
    ``POST_SLOT``     = (0.017 wide, 0.040 tall) vertical stadium slot, punched
                      through the front wall at every rail bolt height.  The
                      beam's own slot is 70 x 22 HORIZONTAL
                      (``armco_w_beam.POST_SLOT``); between the two, a post that
                      is 37 mm out of station and a rail that is 20 mm out of
                      height both still bolt up.  That is why both slots exist
                      and why they are perpendicular.

--- 2. WHERE THE POSTS ARE ----------------------------------------------------

    ``post_sites(side)`` -> the enriched record for every post on one side.
                      3 190 of them are the beam's lap centres and mid-element
                      posts, verbatim.  ``kind='line'``.
                      +62 are RUN-END posts: the beam's last element in every
                      run has a splice post at its near end and nothing at its
                      far end, and a W-beam element that is bolted at one end
                      only is not a thing.  ``kind='end'``.
                      +32 are GATE JAMB posts, a second heavy post 0.30 m behind
                      each run end that abuts a marshal gate.  ``kind='jamb'``.
                      -> 3 284 built against the manifest's estimate of 3 641
                      (-9.8 %).  THE DIFFERENCE IS REAL AND IT IS EXPLAINED:
                      the manifest's figure is exactly 2 x its 1 821-bay
                      estimate for the beam, i.e. it assumes two posts per bay
                      everywhere.  157 of the built bays are 1.33 m elements and
                      172 are 2.00 m elements on radii too tight to cold-bend a
                      4 m sheet, and a short element carries ONE post, not two.
                      Post PITCH is 2.00 m on the 4 m elements and 1.33-2.00 m
                      on the short ones, which is right; the bay count is what
                      moved.  See ``--selftest``, which prints the pitch
                      histogram.

--- 3. THE MOUNTING POINTS OTHER ITEMS NEED -----------------------------------

    ``spacer_sites(side)``       -> one per post: {world seat point on the post
                                    front face, tangent, normal (pointing at the
                                    TRACK), up, rail_z[], slot_z[], face_w,
                                    depth (= SPACER_D), post_fam, crush}.
                                    ``crush`` is this module's per-post impact
                                    energy 0..1, so the spacer's own crush axis
                                    lands on the same post the dent is on.
    ``conduit_clip_sites(side)`` -> one per post at CONDUIT_Z on the post BACK,
                                    with the clear width available between the
                                    section's return lips.
    ``bolt_axis(rec, k)``        -> (world point on the front face, axis vector
                                    pointing at the track) for rail k's post
                                    bolt.  The slot is already a hole.
    ``face_point(rec, h)``       -> world point on the post front face at height
                                    h above the local ground datum.

    Every one of them returns WORLD coordinates already, and every z comes from
    ``world_contract.ground_z``.  No dependant needs the local frame.

--- 4. EMITTING ---------------------------------------------------------------

    ``build(sides=(+1,-1), lod_anchor=..., windows=...)`` emits into collection
    ``W_Item_ArmcoPost`` with object prefix ``AP_``.  ONE OBJECT PER POST, which
    is what the manifest counts as an instance.  ``lod_anchor`` is a list of
    world points (the camera path); mesh density is graded by distance to the
    nearest of them.

===============================================================================
THE SEVEN LAWS, AND WHERE EACH IS DISCHARGED
===============================================================================
 1. procedural, by hand   no image node, no file, no library.  Measured by
                          ``item_gate``: ``no_external_assets``.
 2. no real brands        a driven guardrail post carries no lettering.  The
                          only mark on it is a punched inventory hole and a
                          rolled-in heat number, and neither spells anything.
 3. car scale             the impact hinge heights and the crush lobe widths
                          come off the 2.005 m car and the 0.340 m ride height:
                          a modern F1 front wing endplate strikes a post at
                          0.06-0.11 m and the tyre shoulder at 0.24-0.36 m,
                          which is where the hinges are.
 4. z = 0 is one plane    never assumed: every z is ``C.ground_z(s, u)``,
                          sampled at the POST's own xy, not at the barrier
                          line's -- the post is 0.283 m further outboard and the
                          runoff platform falls 1.6 %, so that is 4.5 mm.
 5. embed >= 20 mm        the post embeds 0.42-1.05 m.  The COLLAR, which is
                          the only part of this item that could float, has its
                          rim skirt driven to ground - 0.050 m and its top
                          surface never closer than 4 mm to the datum, so there
                          is no coplanar pair anywhere and no lit gap at a
                          12.5 deg sun.
 6. recentre + TexCoord   every post's mesh is local to its own centre in a
                          canonical frame (+X along the barrier, +Y away from
                          the track, +Z up), |P| < 1.1 m.  The material reads
                          ``TexCoord->Object`` plus per-vertex attributes plus a
                          per-OBJECT texture offset, so no two posts get the
                          same spangle.  ``Geometry->Position`` appears nowhere.
 7. chunk along s         one post is a point.  Nothing spans anything.

===============================================================================
WHAT VARIES BETWEEN INSTANCES, AND WHY IT IS GEOMETRY
===============================================================================
The manifest names five axes.  All five are in the MESH:

  "settlement -57 mm"      ``settle`` in [0, 0.057], drawn against the post's
                           own maintenance run and the local ground.  It changes
                           the standing height, therefore the embedment,
                           therefore the length of steel above the collar AND
                           the height of every bolt slot relative to the rail.
                           A settled post's slot sits high in the beam's slot,
                           which is visible.
  "+/-37 mm lateral        applied ALONG the barrier (the beam's own post slot
   wander"                 is 70 mm horizontal precisely to swallow it) plus a
                           smaller +/-12 mm of depth wander that the spacer
                           block takes up.  Both move the mesh, not a modifier.
  "+/-0.004 rad lean"      the manifest's figure is the PLUMB TOLERANCE of a
                           freshly driven post and it is used as the sd of the
                           undisturbed population.  Posts that have been hit,
                           or that stand in gravel rather than in the compacted
                           platform, lean up to 0.075 rad.  Lean is baked into
                           the mesh, not into the object rotation, so the gate
                           measures it as shape.
  "galvanising age by      ``galv_age`` is constant within a maintenance run
   maintenance run"        (``armco_w_beam.History.run_id``), so a whole 60-140 m
                           stretch of posts ages together and the next stretch
                           does not -- which is what a re-galvanised section of
                           barrier looks like.  It drives the shader AND the
                           head/edge rust masks.
  "impact bend"            a real plastic hinge: an angle change at a height set
                           by what hit it, PLUS section ovalisation at the
                           hinge, PLUS compression-flange buckling wrinkles,
                           PLUS a cracked-zinc band, PLUS a re-driven collar.
                           Five geometric consequences, because that is what a
                           car does to a 5 mm section.

and four more that are not in the manifest but are in the object:

  section family           7 real cold-rolled families across the population,
                           allocated by maintenance run: a circuit re-posts a
                           stretch at a time and buys whatever the supplier had.
  stock length             1.35 / 1.50 / 1.75 / 2.00 m, modal 1.50 (the
                           manifest's ``typical_height_m``).
  head condition           every driven head is unique: mushroom 0.4-3.6 mm,
                           roll-over burr, drive-cap dish, shear-cut tilt.
                           5 % carry a pressed cap instead.
  collar                   plan radius, heave profile, stone size, and the
                           eccentric rock-gap that opens on the lean side.

Run headless:

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P world/items/armco_post.py -- --test --save world/items/armco_post_test.blend

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P world/items/armco_post.py -- --selftest
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
for _p in (_HERE, _WORLD, _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import world_contract as C                                        # noqa: E402
import itemkit as K                                               # noqa: E402
import armco_w_beam as W                                          # noqa: E402

__version__ = "1.0.0"

ITEM = "armco_post"
COLL = "W_Item_ArmcoPost"
PFX = "AP_"
XPFX = "APSTAND_"           # test-scene stand-ins owned by OTHER items.  The
                            # gate is run with --prefix AP_ and AP_ is not a
                            # prefix of APSTAND_, so not one triangle of them is
                            # measured as this item's work.

_T0 = time.time()


def log(msg):
    print("[%s %7.1fs] %s" % (ITEM, time.time() - _T0, msg))
    sys.stdout.flush()


# ==============================================================================
#  0.  THE NUMBERS
# ==============================================================================
# Manifest record, quoted so nothing downstream has to re-read the JSON.
FILMED_AT_M = 2.6
LENS_MM = 35.0
ONSCREEN_PX_4K = 2154.0
INSTANCES_DECLARED = 3641
TYPICAL_LEN_M = 1.5
PX_PER_M = (3840.0 * LENS_MM / 36.0) / FILMED_AT_M           # 1435.9
PX_M = 1.0 / PX_PER_M                                        # 0.696 mm

# --- where the post stands, across the section --------------------------------
SEC_D = W.SEC_D                       # 0.0830  beam traffic face -> centre ridge
SPACER_D = 0.200                      # armco_spacer_block's depth (manifest 0.2)
FACE_T = SEC_D + SPACER_D             # 0.2830  barrier face -> post FRONT face

ARMCO_TOP = W.ARMCO_TOP               # 1.012, FIA 3-beam.  contract + beam.
RAIL_HZ3 = list(W.RAIL_HZ3)           # [0.072, 0.386, 0.700]
RAIL_HZ2 = list(W.RAIL_HZ2)           # [0.150, 0.560]
RAIL_BOLT_V = 0.1560                  # bolt height above a rail's bottom edge
                                      # (mid-height of the 312 mm section) --
                                      # armco_w_beam.post_sites publishes exactly
                                      # ground_z + rail_h + 0.1560.

# --- the standing height ------------------------------------------------------
# The post top is 30 mm BELOW the top of the top rail on a 3-beam run, which is
# what a European installation looks like: the rail protects the post head.  On a
# 2-beam run the same post is used and the rails sit lower, so 110 mm of head
# stands proud -- 158 px of bare, rusting, hammered steel on 600 of the 3 284
# posts, and it is the single most legible thing this item has.
STAND_NOM = ARMCO_TOP - 0.030         # 0.982
PROUD_FRACTION = 0.18                 # of 3-beam posts left deliberately proud
PROUD_M = (0.008, 0.042)

# --- stock lengths ------------------------------------------------------------
# The manifest's `typical_height_m` = 1.5 is the TOTAL length of a post, the same
# convention catch_fence_post used (6.0 m long, 1.2 m embed, 4.8 m stand).  1.50 m
# is the modal European guardrail post and it is the modal post here; the
# high-energy runs carry 1.75 and 2.00 m stock because 0.52 m of embedment does
# not hold a 3-beam barrier against an F1 car, and the light runs carry 1.35 m.
STOCK_L = [1.350, 1.500, 1.750, 2.000]
STOCK_W = [0.10, 0.52, 0.24, 0.14]     # population weights -> mean 1.545, mode 1.50

# --- the punched slot ---------------------------------------------------------
POST_SLOT = (0.016, 0.040)            # (across the face, up the face) m
SLOT_DIE_ROLL = 0.00035               # entry-face draw-in of a punched hole
SLOT_BURR = 0.00018                   # exit-face burr
TAG_HOLE_D = 0.010                    # inventory hole, 34 % of posts
CONDUIT_Z = 0.350                     # where barrier_cable_conduit clips on

# --- driving ------------------------------------------------------------------
HEAD_MUSH = (0.0004, 0.0036)          # radial mushroom at the driven head
HEAD_ROLL_N = {0: 5, 1: 3, 2: 2, 3: 1}   # samples around the rolled top edge
CAP_FRACTION = 0.05                   # pressed steel caps
SPLINT_FRACTION = 0.030               # bolted repair splints on bent posts

# --- the collar ---------------------------------------------------------------
COLLAR_R = (0.170, 0.345)             # plan radius range
COLLAR_HEAVE = (0.010, 0.046)         # ground pushed up against the shaft
COLLAR_RIM = 0.006                    # rim proud of the datum: NEVER coplanar.
                                      # 6 mm is 8.6 px of lip and, at the
                                      # contract's 12.5 deg sun, 27 mm = 39 px
                                      # of cast shadow -- which is the only
                                      # thing that makes a collar read at all
                                      # from a camera 0.5 m off the ground.
COLLAR_SKIRT = 0.050                  # and buried this far, so there is no seam
COLLAR_GAP = (0.002, 0.016)           # the crescent the post has rocked open
# THE COLLAR HAS TO CARRY STONES, AND A STONE IS 3-8 mm = 4-11 px.
# 96 angular samples round a 0.30 m collar is a 20 mm arc, which cannot express
# anything smaller than a clod; 200 gives 9 mm at the rim and 16 radial rings
# give 13 mm, so a 6 mm chipping has vertices to sit on.  9 600 triangles of
# collar on a hero post, and there are 16 hero posts in the acceptance scene.
COLLAR_N = {0: 200, 1: 84, 2: 32, 3: 14}
COLLAR_RINGS = {0: 16, 1: 8, 2: 4, 3: 2}

# --- lean, wander, settlement -------------------------------------------------
LEAN_SD = 0.004                       # rad -- the manifest's plumb tolerance
LEAN_MAX = 0.075                      # rad -- a post that has been leaned on
WANDER_ALONG = 0.037                  # m, the manifest's figure, along the line
WANDER_DEPTH = 0.012                  # m, across it; the spacer takes it up
SETTLE_MAX = 0.057                    # m, the manifest's figure
TWIST_MAX = 0.055                     # rad over the full length

# --- impact -------------------------------------------------------------------
# What hits a guardrail post, and where.  The car is 2.005 m wide with 0.340 m of
# ride height; its front-wing endplate rides at 0.06-0.11 m and the tyre shoulder
# loads the post at 0.24-0.36 m.  Those two bands are where the hinges are.
HINGE_BANDS = [(0.060, 0.115, 0.42), (0.240, 0.360, 0.58)]
BEND_MAX = 0.34                       # rad at the hinge
BUCKLE_AMP = 0.0055                   # compression-flange wrinkle amplitude
BUCKLE_LAM = 0.048                    # wrinkle wavelength

GATE_STATIONS = list(W.GATE_STATIONS)
GATE_CLEAR_M = W.GATE_CLEAR_M
LAP_LEN = C.LAP
BASE_EMBED_M = C.BASE_EMBED_M

# per-vertex attributes.  Anything constant over a post is an OBJECT property.
ATTRS = ("ap_head", "ap_burr", "ap_cut", "ap_slot", "ap_bend", "ap_buried",
         "ap_hz", "ap_inside", "ap_ground", "ap_stone", "ap_front")
OBJ_PROPS = ("ap_age", "ap_run", "ap_ofs_x", "ap_ofs_y", "ap_ofs_z",
             "ap_seed", "ap_crush")

SEED = 20260729


# ==============================================================================
#  1.  DETERMINISTIC NOISE  —  the contract's own, so this module's per-post
#      draws land on the same metre of circuit as build_barriers' paint transfer
# ==============================================================================

hash01 = W.hash01
h01 = W.h01
vnoise1 = W.vnoise1
fbm1 = W.fbm1
clamp01 = W.clamp01
smoothstep = W.smoothstep
lerp = W.lerp


def _vnoise2(x, y, seed):
    """2D value noise on the contract's own hash.  Quintic interpolation."""
    ix = np.floor(x)
    iy = np.floor(y)
    fx = x - ix
    fy = y - iy
    ux = fx * fx * fx * (fx * (fx * 6.0 - 15.0) + 10.0)
    uy = fy * fy * fy * (fy * (fy * 6.0 - 15.0) + 10.0)
    sd = np.full(np.shape(x), int(seed))
    a = hash01(ix, iy, sd)
    b = hash01(ix + 1.0, iy, sd)
    c = hash01(ix, iy + 1.0, sd)
    d = hash01(ix + 1.0, iy + 1.0, sd)
    return (a * (1 - ux) + b * ux) * (1 - uy) + (c * (1 - ux) + d * ux) * uy


def _fbm2(x, y, seed=0, oct=3, lac=2.07, gain=0.5):
    """2D fbm.  THE COLLAR NEEDS THIS AND A 1D NOISE CANNOT SUBSTITUTE.

    Displacing ring k of the collar by ``fbm1(angle + 13*k)`` gives every ring
    an independent field, so the surface is decorrelated in the RADIAL
    direction at the ring pitch -- 13 mm -- which is aliasing, and it renders
    as a raft of flat 9 mm plates lying at random angles.  It looked like
    crumpled foil, which is precisely what per-vertex white noise looks like
    when you flat-shade it.  A field that is coherent in both directions is the
    fix, and it is 20 lines.
    """
    tot = np.zeros(np.shape(x), float)
    amp, frq, nrm = 1.0, 1.0, 0.0
    for o in range(oct):
        tot += amp * _vnoise2(x * frq, y * frq, seed * 131 + o * 17)
        nrm += amp
        amp *= gain
        frq *= lac
    return tot / nrm


def _pick(u, weights):
    """u in [0,1) -> index, by cumulative weight."""
    c = np.cumsum(np.asarray(weights, float))
    c /= c[-1]
    return int(np.searchsorted(c, u, side="right"))


def _tri(u, lo, hi):
    """u in [0,1) -> a triangular deviate on [lo, hi] (peaked in the middle)."""
    t = (u + h01(int(u * 1e6) + 7, 3)) * 0.5
    return lo + (hi - lo) * t


# ==============================================================================
#  2.  THE SECTIONS  —  seven real cold-rolled guardrail post families
# ==============================================================================
#
# CONVENTION, and it is the one thing a dependant must not get wrong:
#
#     a  = ACROSS the barrier, i.e. along the tangent.  a = 0 is the post axis.
#     b  = AWAY FROM THE TRACK, i.e. along the outward normal.  b = 0 is the
#          post's FRONT FACE -- the face the spacer block bears on.  b grows
#          backwards, so the whole section lies in b >= 0.
#     z  = up, z = 0 at the local ground datum.
#
# W is the OUTSIDE width (along the barrier) and D the OUTSIDE depth.  The
# profiles below are MID-SURFACE, so they are inset by t/2 from both.
#
# Every profile is written in the same rotational order -- starting at the free
# edge on the +a side of the BACK and running round to the free edge on the -a
# side -- so that the outward normal is always rot90ccw(tangent).  `_profile`
# asserts it on the front face.

SECTIONS = {
    # name          W       D       t        kind      share
    "SIGMA_120": dict(W=0.055, D=0.120, t=0.00500, kind="sigma", rib=0.0090,
                      slot=0.012, lip=0.018, share=0.30,
                      desc="sigma 120x55x5.0, ribbed webs, 12 mm slotted back"),
    "SIGMA_100": dict(W=0.055, D=0.100, t=0.00425, kind="sigma", rib=0.0080,
                      slot=0.014, lip=0.016, share=0.18,
                      desc="sigma 100x55x4.25, ribbed webs, 14 mm slotted back"),
    "C_120":     dict(W=0.060, D=0.120, t=0.00500, kind="c", lip=0.020,
                      share=0.19,
                      desc="lipped channel 120x60x5.0, 20 mm back returns"),
    "U_100":     dict(W=0.055, D=0.100, t=0.00400, kind="u", share=0.11,
                      desc="plain channel 100x55x4.0, open back"),
    "OMEGA_110": dict(W=0.055, D=0.110, t=0.00450, kind="omega", flange=0.026,
                      share=0.13,
                      desc="top-hat 110x55x4.5, 26 mm outward flanges"),
    "RHS_100":   dict(W=0.055, D=0.100, t=0.00400, kind="rhs", share=0.09,
                      desc="RHS 100x55x4.0, closed"),
    "RHS_120A":  dict(W=0.060, D=0.120, t=0.00600, kind="rhs", share=0.00,
                      desc="RHS 120x60x6.0 anchor post (run ends, gate jambs)"),
}
FAM_LINE = [k for k in SECTIONS if SECTIONS[k]["share"] > 0]
FAM_SHARE = [SECTIONS[k]["share"] for k in FAM_LINE]
FAM_ANCHOR = "RHS_120A"


def _rot90(d):
    return np.stack([-d[..., 1], d[..., 0]], axis=-1)


def _fillet2d(corners, radii, closed, seg_max, arc_deg, seg_step=None):
    """Corner list -> sampled path, with a tag per sample naming its segment.

    corners  (N,2) polyline corners.  radii  (N,) fillet radius at each corner,
    0 = sharp.  For an OPEN path the two end corners are never filleted.
    seg_step {corner_index: step} overrides seg_max on that straight.

    Returns (pts (M,2), tag (M,) int, is_arc (M,) bool).  `tag` is the index of
    the corner a straight sample starts from, or -1 on an arc: this is how the
    front-face flat is located later without hunting for it geometrically.
    """
    P = np.asarray(corners, float)
    N = len(P)
    R = np.asarray(radii, float).copy()
    if not closed:
        R[0] = R[-1] = 0.0
    idx = range(N) if closed else range(1, N - 1)

    # tangency points and arcs, per corner
    T1 = P.copy()
    T2 = P.copy()
    arcs = [None] * N
    for i in idx:
        c = P[i]
        p = P[(i - 1) % N]
        n = P[(i + 1) % N]
        d1 = p - c
        d2 = n - c
        l1 = np.linalg.norm(d1)
        l2 = np.linalg.norm(d2)
        if l1 < 1e-9 or l2 < 1e-9 or R[i] <= 0.0:
            continue
        d1 = d1 / l1
        d2 = d2 / l2
        cosang = float(np.clip(np.dot(d1, d2), -1.0, 1.0))
        ang = math.acos(cosang)
        if ang < 1e-4 or abs(math.pi - ang) < 1e-4:
            continue
        half = ang * 0.5
        tl = R[i] / math.tan(half)
        tl = min(tl, 0.45 * l1, 0.45 * l2)
        r = tl * math.tan(half)
        bis = d1 + d2
        bl = np.linalg.norm(bis)
        if bl < 1e-9:
            continue
        bis = bis / bl
        ctr = c + bis * (r / math.sin(half))
        T1[i] = c + d1 * tl
        T2[i] = c + d2 * tl
        a1 = math.atan2(T1[i][1] - ctr[1], T1[i][0] - ctr[0])
        a2 = math.atan2(T2[i][1] - ctr[1], T2[i][0] - ctr[0])
        da = (a2 - a1 + math.pi) % (2.0 * math.pi) - math.pi
        ns = max(2, int(math.ceil(abs(math.degrees(da)) / arc_deg)))
        tt = np.linspace(0.0, 1.0, ns + 1)[1:-1]
        arcs[i] = (ctr, r, a1, da, tt)

    pts, tag = [], []
    segs = range(N) if closed else range(N - 1)
    for i in segs:
        j = (i + 1) % N
        # the arc AT corner i (entering it)
        if arcs[i] is not None:
            ctr, r, a1, da, tt = arcs[i]
            pts.append(T1[i]); tag.append(-1)
            for u in tt:
                aa = a1 + da * u
                pts.append(ctr + r * np.array([math.cos(aa), math.sin(aa)]))
                tag.append(-1)
            pts.append(T2[i]); tag.append(-1)
        else:
            pts.append(P[i]); tag.append(-1)
        # the straight from corner i to corner j
        A = T2[i] if arcs[i] is not None else P[i]
        B = T1[j] if arcs[j] is not None else P[j]
        L = float(np.linalg.norm(B - A))
        step = (seg_step or {}).get(i, seg_max)
        ns = max(1, int(math.ceil(L / max(step, 1e-6))))
        if seg_step and i in seg_step:
            # a named segment must always leave interior samples behind: it is
            # how the caller finds the flat face again, and at LOD3 the step is
            # longer than the face is wide.
            ns = max(ns, 3)
        for k in range(1, ns):
            pts.append(A + (B - A) * (k / ns))
            tag.append(i)
    if closed:
        pass
    else:
        j = N - 1
        if arcs[j] is not None:
            ctr, r, a1, da, tt = arcs[j]
            pts.append(T1[j]); tag.append(-1)
        else:
            pts.append(P[j]); tag.append(-1)

    Q = np.asarray(pts, float)
    T = np.asarray(tag, np.int64)
    # drop consecutive duplicates
    keep = np.ones(len(Q), bool)
    d = np.linalg.norm(np.diff(Q, axis=0), axis=1)
    keep[1:] = d > 1e-7
    return Q[keep], T[keep]


_PROF_CACHE = {}

# how finely the profile is sampled, per LOD.  `front` is the step ALONG the flat
# front face, which sets the column pitch the bolt slot is punched into.
PROF_STEP = {0: (0.0042, 0.0034, 8.0), 1: (0.0095, 0.0075, 18.0),
             2: (0.0240, 0.0180, 46.0), 3: (0.1300, 0.0600, 200.0)}
# LOD3 is 400 m away and 3 px wide.  Its fillets are sharp corners, because a
# 7.5 mm radius sampled at 200 deg is one extra vertex for nothing.
PROF_SHARP_LOD = 3


def section_profile(fam, lod):
    """-> dict(mid (K,2), nrm (K,2), closed, t, front (j0,j1), W, D, name).

    `front` is the inclusive index range of the samples that lie on the FLAT
    front face, between the two corner fillets.  That band is where the bolt
    slot is punched and it is the only part of the section that must stay
    planar, because a spacer block bears on it.
    """
    key = (fam, lod)
    if key in _PROF_CACHE:
        return _PROF_CACHE[key]
    S = SECTIONS[fam]
    Wd, D, t = S["W"], S["D"], S["t"]
    tt = t * 0.5
    half = Wd * 0.5 - tt
    bf = tt
    bb = D - tt
    r = 1.55 * t                       # cold-formed mid-surface corner radius
    rl = 1.30 * t                       # at a lip
    if lod >= PROF_SHARP_LOD:
        r = rl = 0.0
    kind = S["kind"]
    step, fstep, arcdeg = PROF_STEP[lod]

    if kind == "sigma":
        rib = S["rib"]
        sl = S["slot"] * 0.5
        lip = S["lip"]
        b1 = bf + (bb - bf) * 0.60
        bm = bf + (bb - bf) * 0.50
        b2 = bf + (bb - bf) * 0.40
        cor = [(+sl, bb - lip), (+sl, bb), (+half, bb),
               (+half, b1), (+half - rib, bm), (+half, b2), (+half, bf),
               (-half, bf), (-half, b2), (-half + rib, bm), (-half, b1),
               (-half, bb), (-sl, bb), (-sl, bb - lip)]
        rad = [0.0, rl, r, rl, rl, rl, r, r, rl, rl, rl, r, rl, 0.0]
        front = 6
        closed = False
    elif kind == "c":
        lip = S["lip"]
        cor = [(+half - lip, bb), (+half, bb), (+half, bf),
               (-half, bf), (-half, bb), (-half + lip, bb)]
        rad = [0.0, r, r, r, r, 0.0]
        front = 2
        closed = False
    elif kind == "u":
        cor = [(+half, bb), (+half, bf), (-half, bf), (-half, bb)]
        rad = [0.0, r, r, 0.0]
        front = 1
        closed = False
    elif kind == "omega":
        fl = S["flange"]
        cor = [(+half + fl, bb), (+half, bb), (+half, bf),
               (-half, bf), (-half, bb), (-half - fl, bb)]
        rad = [0.0, r, r, r, r, 0.0]
        front = 2
        closed = False
    elif kind == "rhs":
        rr = 2.0 * t if lod < PROF_SHARP_LOD else 0.6 * t
        cor = [(+half, bf), (-half, bf), (-half, bb), (+half, bb)]
        rad = [rr, rr, rr, rr]
        front = 0
        closed = True
    else:
        raise ValueError(fam)

    mid, tag = _fillet2d(cor, rad, closed, step, arcdeg, seg_step={front: fstep})

    # outward normal = rot90ccw(tangent), with the ends extrapolated
    d = np.zeros_like(mid)
    if closed:
        d = np.roll(mid, -1, axis=0) - np.roll(mid, 1, axis=0)
    else:
        d[1:-1] = mid[2:] - mid[:-2]
        d[0] = mid[1] - mid[0]
        d[-1] = mid[-1] - mid[-2]
    d /= np.maximum(np.linalg.norm(d, axis=1, keepdims=True), 1e-12)
    nrm = _rot90(d)

    fi = np.flatnonzero(tag == front)
    if not len(fi):
        raise RuntimeError("%s: no front-face samples" % fam)
    j0, j1 = int(fi[0]), int(fi[-1])
    # the tangency points either side belong to the flat too (they are ON it)
    j0 = max(0, j0 - 1)
    j1 = min(len(mid) - 1, j1 + 1)
    # THE ASSERT THAT KEEPS THE WHOLE MODULE HONEST: the front face's outward
    # normal must point at the TRACK, i.e. -b.  If a profile is ever written the
    # other way round, every post turns inside out and the bolt slot is punched
    # through the back.
    nfront = nrm[(j0 + j1) // 2]
    if nfront[1] > -0.9:
        raise RuntimeError("%s: front-face normal is %s, expected -b" %
                           (fam, nfront))

    out = dict(mid=mid, nrm=nrm, closed=closed, t=t, front=(j0, j1),
               W=Wd, D=D, name=fam, tag=tag,
               perim=float(np.sum(np.linalg.norm(np.diff(mid, axis=0), axis=1))))
    _PROF_CACHE[key] = out
    return out


# ==============================================================================
#  3.  THE POPULATION
# ==============================================================================

_SITE_CACHE = {}


def _post_ground(S, side, extra):
    """Ground z under a post, ANALYTICALLY, at (station, barrier lateral + extra).

    NOT by projecting the post's xy back onto the centreline.  `C.project`
    answers "which station is nearest", and near the pit straight the access
    road and the main straight run within a few metres of each other, so for
    about 1 % of the posts the nearest station is on the wrong piece of
    circuit and `ground_z` comes back metres out.  The first version of this
    function did exactly that and produced posts 5.9 m tall and 3.8 m out of
    the ground -- a defect that a mean and a p95 both hid, and that only the
    min/max caught.

    The barrier line is CONSTRUCTED from (s, off), so evaluating the datum at
    (s, off + extra) is not an approximation of where the post is; it is the
    definition of it.

    `world_ground_z` is deliberately not used: it returns NaN where terrain owns
    the ground, and `ground_z(s, u)` is the continuous runoff-platform formula
    that build_barriers actually meshes under a barrier.  Same choice
    armco_w_beam.build_ground made, for the same reason.
    """
    S = np.asarray(S, float)
    lat_j, ver_j = W.HIST.align(S, side)
    lat_j = np.clip(lat_j, -W.BARRIER_JITTER_MAX_M, W.BARRIER_JITTER_MAX_M)
    off = C.barrier_offset(S, side) + lat_j
    return (np.asarray(C.ground_z(S, (off + extra) * side), float),
            np.asarray(C.ground_z(S, off * side), float) + ver_j)


def _run_end_posts(side):
    """The posts the beam does not name: one at the far end of every run, and a
    heavy jamb post behind every run end that abuts a marshal gate.

    A W-beam element bolted at one end only is not a thing.  The beam's
    `post_sites` walks `panels()` and puts a post at each element's LAP CENTRE
    plus a mid-element post on anything over 3 m -- so the LAST element of every
    run has a post near its start and nothing holding its far end.
    """
    ln = W.barrier_line(side)
    out = []
    for (ra, rb) in W._armco_runs(ln):
        for (q, is_start) in ((ra, True), (rb, False)):
            o, t, n, u = W._frame(ln, q)
            s = float(W._sample_line(ln, q, "s"))
            # step 0.10 m inboard of the very end so the post is under steel
            qq = q + (0.10 if is_start else -0.10)
            o, t, n, u = W._frame(ln, qq)
            s = float(W._sample_line(ln, qq, "s"))
            nr = int(W.rail_count(np.array([s]), side)[0])
            hz = RAIL_HZ3 if nr == 3 else RAIL_HZ2
            base = dict(s=s, arc=float(qq), side=side, world=tuple(o),
                        tangent=tuple(t), normal=tuple(n), up=tuple(u),
                        ground_z=float(o[2]),
                        slot_z=[float(o[2] + h + RAIL_BOLT_V) for h in hz],
                        slot_w=W.POST_SLOT[0], slot_h=W.POST_SLOT[1],
                        nrail=nr, panel=-1)
            base["kind"] = "end"
            out.append(base)
            # a gate jamb gets a second, heavier post 0.30 m behind the end
            near_gate = min(abs(((s - g + LAP_LEN * 0.5) % LAP_LEN) - LAP_LEN * 0.5)
                            for g in GATE_STATIONS)
            if near_gate < GATE_CLEAR_M:
                qj = qq + (-0.30 if is_start else 0.30)
                o2, t2, n2, u2 = W._frame(ln, qj)
                s2 = float(W._sample_line(ln, qj, "s"))
                j = dict(base)
                j.update(s=s2, arc=float(qj), world=tuple(o2),
                         tangent=tuple(t2), normal=tuple(n2), up=tuple(u2),
                         ground_z=float(o2[2]),
                         slot_z=[float(o2[2] + h + RAIL_BOLT_V) for h in hz],
                         kind="jamb")
                out.append(j)
    return out


def post_sites(side):
    """EVERY post on one side, as an enriched record.  THE public interface.

    The beam's lap centres, verbatim, plus the run-end and gate-jamb posts the
    beam does not name (§2 of the module docstring), each carrying the section,
    the lengths and every deformation this module will mesh.  A dependant that
    needs to know where a post is, what shape it is, or how hard it has been hit
    reads it from here and never re-derives it.
    """
    if side in _SITE_CACHE:
        return _SITE_CACHE[side]
    base = []
    for st in W.post_sites(side):
        st = dict(st)
        st["kind"] = "line"
        base.append(st)
    base += _run_end_posts(side)
    base.sort(key=lambda r: r["arc"])

    # Ground under the POST, which is FACE_T + ~D/2 further outboard than the
    # barrier line.  The platform falls 1.6 %, so that alone is 4.5 mm, and
    # 4.5 mm is 6.5 px at the filmed distance.
    Sarr = np.array([r["s"] for r in base], float)
    Zc, Zline = _post_ground(Sarr, side, FACE_T + 0.055)
    # THE LOCAL SLOPE OF THE PLATFORM UNDER EACH POST.  The collar is the only
    # part of this item that lies nearly parallel to build_barriers' runoff
    # mesh, so a collar whose rim sits at a CONSTANT height above the POST's
    # datum crosses the true ground wherever the platform falls -- measured,
    # 9.3 % of the sampled rim came within 0.5 mm of the platform, which is a
    # coplanar pair and a stipple.  Over 0.7 m the platform is a plane to well
    # under a millimetre (its shortest undulation wavelength is 3 m), so two
    # finite differences are enough to make the collar sit ON it instead of
    # crossing it.
    _d = 0.30
    _z_sp = _post_ground(Sarr + _d, side, FACE_T + 0.055)[0]
    _z_sm = _post_ground(Sarr - _d, side, FACE_T + 0.055)[0]
    _z_up = _post_ground(Sarr, side, FACE_T + 0.055 + _d)[0]
    _z_um = _post_ground(Sarr, side, FACE_T + 0.055 - _d)[0]
    _gx = (_z_sp - _z_sm) / (2.0 * _d)        # dz per metre ALONG the barrier
    _gy = (_z_up - _z_um) / (2.0 * _d)        # dz per metre OUTBOARD
    # CLAMPED, because the finite difference is not always differentiating a
    # surface.  At s = 904 and s = 250 the runoff programme's zone ramps swing
    # `barrier_offset` fast enough that the two samples straddle a step in the
    # cross-section, and the fit came back at 78 % slope -- which would lift a
    # collar 0.27 m off the ground.  The runoff platform's real cross-fall is
    # 1.6 % and its longitudinal grade never exceeds ~4 %, so 6 % is a generous
    # bound and a bound is the point.
    _gx = np.clip(_gx, -0.06, 0.06)
    _gy = np.clip(_gy, -0.06, 0.06)
    # cross-check: the analytic barrier-line datum must reproduce the z the
    # beam's own polyline carries.  A drift here means the two modules have
    # stopped agreeing about where the barrier is.
    _res = np.abs(Zline - np.array([r["ground_z"] for r in base], float))
    if len(_res) and _res.max() > 0.02:
        log("WARNING: barrier-line datum drift up to %.1f mm vs "
            "armco_w_beam.barrier_line" % (1000 * _res.max()))

    out = []
    for i, r in enumerate(base):
        sgn = 1 if r["side"] > 0 else 0
        k = i * 3 + sgn * 100003
        run = int(W.HIST.run_id(r["s"], side))
        u = [h01(SEED, k, j) for j in range(24)]

        # --- section family: allocated BY MAINTENANCE RUN.  A circuit re-posts a
        # stretch at a time and buys whatever the supplier had that year, so the
        # family is constant over 60-140 m and then changes.  That is what makes
        # the barrier read as having a history instead of a catalogue number.
        if r["kind"] in ("end", "jamb"):
            fam = FAM_ANCHOR
        else:
            fr = h01(SEED + 11, run, 5)
            fam = FAM_LINE[_pick(fr, FAM_SHARE)]
            # 12 % of posts inside a run are replacements from a later batch
            if u[0] < 0.12:
                fam = FAM_LINE[_pick(u[1], FAM_SHARE)]
        S = SECTIONS[fam]

        # --- crash exposure at this station, which drives bend and lean
        expo = float(W.HIST.scars(np.array([r["s"]]), side)[0][0])   # push-back, m

        # --- lengths -------------------------------------------------------
        stock = STOCK_L[_pick(u[2], STOCK_W)]
        if r["kind"] in ("end", "jamb"):
            stock = 2.000
        elif expo > 0.04 and u[3] < 0.55:
            stock = max(stock, 1.750)
        settle = SETTLE_MAX * (u[4] ** 1.8) * (0.35 + 0.65 * min(expo / 0.09, 1.0))
        proud = 0.0
        if r["nrail"] == 2:
            proud = 0.004 + 0.010 * u[5]
        elif u[6] < PROUD_FRACTION:
            proud = PROUD_M[0] + (PROUD_M[1] - PROUD_M[0]) * u[7]
        # TWO DATUMS, AND THEY ARE NOT THE SAME NUMBER.
        # The RAILS are hung off `armco_w_beam`'s barrier line, whose z carries
        # build_barriers' own vertical erection jitter (sd 8 mm, up to 48 mm).
        # The GROUND the post is driven into is the contract's runoff platform
        # at the post's own xy, 0.283 m further outboard.  The two differ by
        # 4-43 mm and the post has to satisfy both: its head must sit 30 mm
        # under the rail it holds, and its collar must sit on the ground that
        # is actually meshed there.  So the standing height is measured to the
        # BEAM datum and then re-expressed against the post's own ground.
        # Getting this wrong buries the collar or floats it, which at 1436 px/m
        # is a 30-60 px lit gap under every post on the circuit.
        dz_beam = float(np.clip(float(r["ground_z"]) - float(Zc[i]),
                                -0.120, 0.120))
        stand = STAND_NOM + proud - settle + dz_beam
        embed = stock - stand
        if embed < 0.42:                       # a post that short was never used
            stock = STOCK_L[2] if stock <= 1.5 else STOCK_L[3]
            embed = stock - stand

        # --- set-out error --------------------------------------------------
        wander_a = (u[8] - 0.5) * 2.0 * WANDER_ALONG
        wander_b = (u[9] - 0.5) * 2.0 * WANDER_DEPTH

        # --- lean.  the manifest's 0.004 rad is the plumb tolerance of a
        # freshly driven post; the tail belongs to posts that have been leaned on
        gv = C.runoff_widths(np.array([r["s"]]), side)["gravel"][0]
        soft = 0.35 + 0.65 * clamp01(gv / 20.0)
        # THE MANIFEST'S 0.004 rad IS AN SD, NOT A CAP.  It is the plumb
        # tolerance of a freshly driven post, so it is the sd of the
        # undisturbed population and 95 % of posts sit inside +/-0.008 rad.
        # A gravel bed holds a post less well than the compacted platform, and
        # a post that has been hit does not go back to plumb, so both carry a
        # tail -- but the tail is 2 % of the population, not the middle of it.
        # Three uniforms summed is a good enough gaussian for a lean angle.
        g1 = (u[10] + h01(SEED, k, 40) + h01(SEED, k, 41) - 1.5) * 1.15
        g2 = (u[11] + h01(SEED, k, 42) + h01(SEED, k, 43) - 1.5) * 1.15
        lean = LEAN_SD * g1 * (1.0 + 0.9 * soft)
        lean_b = LEAN_SD * g2 * (1.0 + 0.6 * soft)
        crush = float(clamp01(expo / 0.09))
        if crush > 0.02:
            lean_b += min(LEAN_MAX, 0.85 * crush ** 1.6 * (0.25 + 0.75 * u[12]))
        lean = float(np.clip(lean, -LEAN_MAX, LEAN_MAX))
        lean_b = float(np.clip(lean_b, -LEAN_MAX, LEAN_MAX))
        twist = (2.0 * u[13] - 1.0) * TWIST_MAX * (0.25 + 0.75 * soft) * \
            (0.35 + 0.65 * u[13])

        # --- impact hinge ---------------------------------------------------
        bend_ang = 0.0
        bend_z = 0.0
        buckle = 0.0
        if crush > 0.085 and u[14] < 0.30 + 0.95 * crush:
            band = HINGE_BANDS[0 if u[15] < HINGE_BANDS[0][2] else 1]
            bend_z = band[0] + (band[1] - band[0]) * u[16]
            bend_ang = BEND_MAX * crush * (0.25 + 0.75 * u[17])
            buckle = clamp01(bend_ang / (BEND_MAX * 0.55))
        straightened = bool(bend_ang > 0.0 and u[18] < 0.30)

        # --- head, cap, splint, tag ------------------------------------------
        mush = HEAD_MUSH[0] + (HEAD_MUSH[1] - HEAD_MUSH[0]) * (u[19] ** 0.8)
        head_tilt = (2.0 * u[20] - 1.0) * math.radians(2.2)
        capped = bool(u[21] < CAP_FRACTION and r["kind"] == "line")
        splint = bool(bend_ang > 0.10 and u[22] < SPLINT_FRACTION / 0.12)
        tag_hole = bool(u[23] < 0.34)

        # --- galvanising age, CONSTANT WITHIN A MAINTENANCE RUN --------------
        galv = 0.18 + 0.78 * h01(SEED + 41, run, side > 0)
        galv = float(clamp01(galv + 0.10 * (u[0] - 0.5)))

        o = np.array(r["world"], float)
        n = np.array(r["normal"], float)
        t = np.array(r["tangent"], float)
        origin = o + n * FACE_T + t * wander_a + n * wander_b
        gz = float(Zc[i])
        origin[2] = gz

        hz = RAIL_HZ3 if r["nrail"] == 3 else RAIL_HZ2
        rec = dict(r)
        rec.update(
            idx=i, run=run, fam=fam, W=S["W"], D=S["D"], t=S["t"],
            origin=tuple(origin), post_ground_z=gz,
            stock=stock, stand=stand, embed=embed, settle=settle, proud=proud,
            wander_a=wander_a, wander_b=wander_b,
            lean_a=lean, lean_b=lean_b, twist=twist,
            bend_z=bend_z, bend_ang=bend_ang, buckle=buckle,
            straightened=straightened, crush=crush, expo=expo,
            mush=mush, head_tilt=head_tilt, capped=capped, splint=splint,
            tag_hole=tag_hole, galv=galv,
            rail_h=list(hz), dz_beam=dz_beam,
            bolt_z=list(r["slot_z"]),
            g_slope=(float(_gx[i]), float(_gy[i])),
            collar_r=COLLAR_R[0] + (COLLAR_R[1] - COLLAR_R[0]) * u[3],
            collar_heave=COLLAR_HEAVE[0] + (COLLAR_HEAVE[1] - COLLAR_HEAVE[0])
            * (0.35 + 0.65 * crush) * u[5],
            collar_gap=COLLAR_GAP[0] + (COLLAR_GAP[1] - COLLAR_GAP[0])
            * clamp01(abs(lean_b) / 0.03 + 0.4 * crush) * (0.4 + 0.6 * u[7]),
            seed=int(SEED + k * 7919 + (side > 0) * 104729),
            lod=2)
        out.append(rec)
    _SITE_CACHE[side] = out
    return out


def spacer_sites(side):
    """One per post: the seat ``armco_spacer_block`` bears on.  WORLD frame.

    `normal` points AT THE TRACK (the direction the block is pushed), which is
    the opposite sign from the beam's `normal`; that is deliberate and it is
    named in the key.  `depth` is SPACER_D and it is the number the block must
    be built to: the beam's centre ridge is exactly `depth` in front of `world`.

    HEIGHTS, UNAMBIGUOUSLY.  `world` is the point on the post's FRONT FACE at
    the post's own ground datum, so world.z == `ground_z_post`.  `bolt_z` is
    ABSOLUTE world z for each rail's post bolt and is the one to use.
    `rail_h` is each rail's bottom edge above the BEAM's datum, which is
    `ground_z_beam` -- a different number from `ground_z_post` by `dz_beam`
    (4-43 mm, build_barriers' vertical erection jitter).  Both are published so
    nobody has to guess which datum a height is against.
    """
    out = []
    for r in post_sites(side):
        o = np.array(r["origin"], float)
        n = np.array(r["normal"], float)
        t = np.array(r["tangent"], float)
        pr = section_profile(r["fam"], 2)
        flat = pr["mid"][pr["front"][0]:pr["front"][1] + 1]
        out.append(dict(
            s=r["s"], side=side, idx=r["idx"], world=tuple(o),
            tangent=tuple(t), normal=tuple(-n), up=(0.0, 0.0, 1.0),
            toward_track=tuple(-n), depth=SPACER_D,
            ground_z_post=r["post_ground_z"], ground_z_beam=r["ground_z"],
            dz_beam=r["dz_beam"], stand=r["stand"], nrail=r["nrail"],
            face_w=float(flat[:, 0].max() - flat[:, 0].min()),
            post_fam=r["fam"], post_W=r["W"], post_D=r["D"],
            rail_h=list(r["rail_h"]), bolt_z=list(r["bolt_z"]),
            slot=POST_SLOT, crush=r["crush"], galv=r["galv"],
            lean_a=r["lean_a"], lean_b=r["lean_b"], kind=r["kind"]))
    return out


def conduit_clip_sites(side):
    """One per post on the post BACK, where ``barrier_cable_conduit`` clips.

    `clear` is the width available between the section's return lips: an open
    channel gives the conduit somewhere to sit, an RHS does not and the clip has
    to go round the outside.  `inside` says which.
    """
    out = []
    for r in post_sites(side):
        o = np.array(r["origin"], float)
        n = np.array(r["normal"], float)
        t = np.array(r["tangent"], float)
        S = SECTIONS[r["fam"]]
        inside = S["kind"] in ("sigma", "c", "u", "omega")
        clear = {"sigma": S.get("slot", 0.012), "c": S["W"] - 2 * S.get("lip", 0.02),
                 "u": S["W"] - 2 * S["t"], "omega": S["W"] - 2 * S["t"],
                 "rhs": 0.0}[S["kind"]]
        p = o + n * r["D"] + np.array([0.0, 0.0, r["post_ground_z"] * 0.0 + CONDUIT_Z])
        p[2] = r["post_ground_z"] + CONDUIT_Z
        out.append(dict(s=r["s"], side=side, idx=r["idx"], world=tuple(p),
                        tangent=tuple(t), normal=tuple(n), up=(0.0, 0.0, 1.0),
                        inside=bool(inside), clear=float(clear),
                        post_fam=r["fam"], kind=r["kind"]))
    return out


def bolt_axis(rec, k):
    """(world point on the post front face, axis pointing AT THE TRACK) for the
    post bolt of rail `k`.  The slot is already a hole in the mesh."""
    o = np.array(rec["origin"], float)
    n = np.array(rec["normal"], float)
    p = o + np.array([0.0, 0.0, rec["bolt_z"][k] - rec["post_ground_z"]])
    return tuple(p), tuple(-n)


def face_point(rec, h):
    """World point on the post FRONT FACE at height `h` above the local datum."""
    o = np.array(rec["origin"], float)
    return tuple(o + np.array([0.0, 0.0, h]))


# ==============================================================================
#  4.  THE WARP  —  lean, twist, settlement, the plastic hinge, the buckle
# ==============================================================================

def _warp(rec, z):
    """-> (dx, dy, twist, sa, sb) at height z.  z = 0 is the ground datum.

    A driven post is not a prism.  Four things move it, and all four are here so
    that the mesher only ever asks "where is the section at this height".
    """
    z = np.asarray(z, float)
    lean_a, lean_b = rec["lean_a"], rec["lean_b"]
    dx = z * math.tan(lean_a)
    dy = z * math.tan(lean_b)

    # driving bow: a driven post picks up a gentle S over its buried length and
    # the top half straightens out.  amplitude 2-9 mm, it is 3-13 px.
    amp = 0.0020 + 0.0070 * h01(rec["seed"], 3)
    ph = 2.0 * math.pi * h01(rec["seed"], 4)
    L = rec["stock"]
    dx = dx + amp * np.sin(2.0 * math.pi * (z + rec["embed"]) / L + ph)
    dy = dy + amp * 0.6 * np.cos(2.6 * math.pi * (z + rec["embed"]) / L + ph)

    tw = rec["twist"] * np.clip((z + rec["embed"]) / max(L, 1e-6), 0.0, 1.0)

    sa = np.ones_like(z)
    sb = np.ones_like(z)
    if rec["bend_ang"] > 1e-6:
        zb = rec["bend_z"]
        ang = rec["bend_ang"] * (0.25 if rec["straightened"] else 1.0)
        # the hinge: everything above zb rotates about it, smoothed over 40 mm so
        # the metal has a radius rather than a crease
        w = np.clip((z - zb) / 0.040, 0.0, 1.0)
        w = w * w * (3.0 - 2.0 * w)
        dy = dy + np.tan(ang) * np.maximum(z - zb, 0.0) * w
        dx = dx + np.tan(ang * 0.35 * (2.0 * h01(rec["seed"], 5) - 1.0)) \
            * np.maximum(z - zb, 0.0) * w
        # ovalisation AT the hinge: the section flattens in the bending plane and
        # spreads across it.  strain falls off over +-55 mm.
        e = np.exp(-0.5 * ((z - zb) / 0.055) ** 2) * rec["buckle"]
        sb = sb * (1.0 - 0.26 * e)
        sa = sa * (1.0 + 0.19 * e)
    return dx, dy, tw, sa, sb


def _buckle_offset(rec, z, b):
    """Compression-flange wrinkles at the hinge, along the outward normal.

    Only the FRONT half of the section buckles: the hinge closes the front and
    opens the back, and 5 mm steel wrinkles on the compression side.  Amplitude
    5.5 mm = 8 px, wavelength 48 mm = 69 px, so it is four visible waves.
    """
    if rec["buckle"] <= 1e-6:
        return np.zeros_like(z)
    zb = rec["bend_z"]
    env = np.exp(-0.5 * ((z - zb) / 0.052) ** 2)
    ph = 2.0 * math.pi * h01(rec["seed"], 9)
    wave = np.sin(2.0 * math.pi * (z - zb) / BUCKLE_LAM + ph)
    front = np.clip(1.0 - b / (rec["D"] * 0.55), 0.0, 1.0)
    return BUCKLE_AMP * rec["buckle"] * env * wave * front


def _z_stations(rec, lod):
    """Adaptive z stations: dense where the geometry is, coarse where it is not.

    A straight post needs almost no rows; the head, the ground line, the hinge
    and every bolt slot need a lot.  Uniform rows would spend 90 % of the budget
    on flat steel that has one normal.
    """
    z0 = -rec["embed"]
    z1 = rec["stand"]
    coarse = {0: 0.075, 1: 0.130, 2: 0.210, 3: 0.620}[lod]
    fine = {0: 0.0045, 1: 0.0110, 2: 0.038, 3: 0.230}[lod]
    zs = list(np.arange(z0, z1, coarse)) + [z1]

    def refine(zc, half, step):
        n = max(2, int(round(2 * half / step)))
        zs.extend(np.linspace(max(z0, zc - half), min(z1, zc + half), n + 1))

    refine(z1, 0.045, fine)                       # the driven head
    refine(0.0, 0.075, fine * 1.6)                # the ground line and collar
    if rec["bend_ang"] > 1e-6:
        refine(rec["bend_z"], 0.110, fine)        # the hinge and its wrinkles
    if lod <= 1:
        for bz in rec["bolt_z"]:
            zc = bz - rec["post_ground_z"]
            if z0 < zc < z1:
                refine(zc, POST_SLOT[1] * 0.86, fine * 1.15)
        if rec["tag_hole"]:
            refine(z1 - 0.075, 0.014, fine)
    z = np.unique(np.round(np.clip(np.array(sorted(zs)), z0, z1), 6))
    # never leave a row closer than 0.4 mm to its neighbour: degenerate quads
    keep = [0]
    for i in range(1, len(z)):
        if z[i] - z[keep[-1]] > 0.0004:
            keep.append(i)
    if z[keep[-1]] < z1 - 1e-9:
        keep[-1] = len(z) - 1
    return z[keep]


# ==============================================================================
#  5.  MESHING
# ==============================================================================

def _stadium(w, h, n):
    """A vertical stadium (slot) outline, n points, CCW, centred on the origin."""
    r = w * 0.5
    st = max(h * 0.5 - r, 1e-5)
    # perimeter: 2 straights of 2*st + 2 half-circles of pi*r
    per = 4.0 * st + 2.0 * math.pi * r
    s = np.linspace(0.0, per, n, endpoint=False)
    P = np.empty((n, 2))
    for i, q in enumerate(s):
        if q < 2.0 * st:                        # right straight, going up
            P[i] = (r, -st + q)
        elif q < 2.0 * st + math.pi * r:        # top cap
            a = (q - 2.0 * st) / r
            P[i] = (r * math.cos(a), st + r * math.sin(a))
        elif q < 4.0 * st + math.pi * r:        # left straight, going down
            P[i] = (-r, st - (q - 2.0 * st - math.pi * r))
        else:                                   # bottom cap
            a = (q - 4.0 * st - math.pi * r) / r
            P[i] = (-r * math.cos(a), -st - r * math.sin(a))
    return P


def _ring_loop(r0, r1, c0, c1):
    """The boundary loop of grid cells [r0..r1) x [c0..c1) as (row, col) pairs,
    walked once anticlockwise in (col, row) space starting at (r0, c0)."""
    L = []
    for c in range(c0, c1 + 1):
        L.append((r0, c))
    for r in range(r0 + 1, r1 + 1):
        L.append((r, c1))
    for c in range(c1 - 1, c0 - 1, -1):
        L.append((r1, c))
    for r in range(r1 - 1, r0, -1):
        L.append((r, c0))
    return L


class PostMesh(object):
    """Accumulates verts, quads, tris and per-vertex attributes for one post."""

    __slots__ = ("V", "Q", "T", "A", "n")

    def __init__(self):
        self.V = []
        self.Q = []
        self.T = []
        self.A = {k: [] for k in ATTRS}
        self.n = 0

    def add(self, V, attrs=None):
        """-> the base index of the block just added."""
        base = self.n
        V = np.asarray(V, float).reshape(-1, 3)
        self.V.append(V)
        self.n += len(V)
        for k in ATTRS:
            a = (attrs or {}).get(k, 0.0)
            self.A[k].append(np.full(len(V), a, np.float32)
                             if np.ndim(a) == 0 else
                             np.asarray(a, np.float32).ravel())
        return base

    def quads(self, Q):
        if len(Q):
            self.Q.append(np.asarray(Q, np.int64).reshape(-1, 4))

    def tris(self, T):
        if len(T):
            self.T.append(np.asarray(T, np.int64).reshape(-1, 3))

    def finish(self):
        V = np.vstack(self.V) if self.V else np.zeros((0, 3))
        Q = np.vstack(self.Q) if self.Q else np.zeros((0, 4), np.int64)
        T = np.vstack(self.T) if self.T else np.zeros((0, 3), np.int64)
        A = {k: (np.concatenate(v) if v else np.zeros(0, np.float32))
             for k, v in self.A.items()}
        return V, Q, T, A


def _shell(rec, pr, zs, lod):
    """The post shaft: outer and inner surfaces, caps, rolled head, slots.

    Returns (PostMesh).  Everything is in the post's LOCAL canonical frame:
    +X along the barrier, +Y away from the track, +Z up, origin at the front
    face on the ground datum.
    """
    m = PostMesh()
    mid = pr["mid"]
    nrm = pr["nrm"]
    K = len(mid)
    NZ = len(zs)
    t = pr["t"]
    closed = pr["closed"]
    j0, j1 = pr["front"]

    dx, dy, tw, sa, sb = _warp(rec, zs)
    cs = np.cos(tw)
    sn = np.sin(tw)

    # --- the mushroomed driven head -----------------------------------------
    # the last 30 mm of a driven post is 0.4-3.6 mm wider than the rest of it,
    # most at the flats and least at the corners, because that is where the
    # section can spread.  It is 0.6-5 px of silhouette and it is the difference
    # between a post that was driven and a post that was extruded.
    hz = rec["stand"]
    mushz = np.clip((zs - (hz - 0.032)) / 0.032, 0.0, 1.0) ** 1.7
    # per-profile-point spread: the flats spread, the corners do not
    dotn = np.sum(nrm[:-1] * nrm[1:], axis=1)
    curv = np.concatenate([[0.0], np.arccos(np.clip(dotn, -1.0, 1.0))])
    curv = np.maximum(curv, np.concatenate([curv[1:], [0.0]]))
    flat = np.exp(-curv * 26.0)
    mush_j = rec["mush"] * (0.55 + 0.45 * flat)
    mush_j = mush_j * (0.7 + 0.6 * np.array(
        [h01(rec["seed"], 300 + (j * 7) % 97) for j in range(K)]))

    OUT = np.empty((NZ, K, 3))
    INN = np.empty((NZ, K, 3))
    ao = mid[:, 0]
    bo = mid[:, 1]
    for i in range(NZ):
        buck = _buckle_offset(rec, np.full(K, zs[i]), bo)
        e = mush_j * mushz[i] + buck
        po = mid + nrm * (t * 0.5 + e[:, None])
        pi_ = mid + nrm * (-t * 0.5 + e[:, None])
        for P, DST in ((po, OUT), (pi_, INN)):
            a = P[:, 0] * sa[i]
            b = (P[:, 1] - rec["D"] * 0.5) * sb[i] + rec["D"] * 0.5
            DST[i, :, 0] = a * cs[i] - b * sn[i] + dx[i]
            DST[i, :, 1] = a * sn[i] + b * cs[i] + dy[i]
            DST[i, :, 2] = zs[i]

    # --- vertex attributes ---------------------------------------------------
    zz = np.repeat(zs, K)
    def att(inside):
        hzz = zz
        a = dict(
            ap_hz=np.clip(hzz / max(rec["stand"], 1e-6), -1.0, 1.0).astype(np.float32),
            ap_buried=(hzz < 0.0).astype(np.float32),
            ap_head=np.repeat((mushz ** 0.7).astype(np.float32), K),
            ap_inside=np.full(NZ * K, 1.0 if inside else 0.0, np.float32),
            ap_front=np.tile((np.abs(nrm[:, 1] + 1.0) < 0.35).astype(np.float32), NZ),
            ap_ground=np.zeros(NZ * K, np.float32),
            ap_stone=np.zeros(NZ * K, np.float32),
            ap_burr=np.zeros(NZ * K, np.float32),
            ap_cut=np.zeros(NZ * K, np.float32),
            ap_slot=np.zeros(NZ * K, np.float32),
        )
        if rec["bend_ang"] > 1e-6:
            a["ap_bend"] = (np.exp(-0.5 * ((zz - rec["bend_z"]) / 0.050) ** 2)
                            * rec["buckle"]).astype(np.float32)
        else:
            a["ap_bend"] = np.zeros(NZ * K, np.float32)
        return a

    bo_i = m.add(OUT.reshape(-1, 3), att(False))
    bi_i = m.add(INN.reshape(-1, 3), att(True))

    # --- which grid cells are removed by a punched slot -----------------------
    holes = []
    if lod <= 1 and pr["front"][1] > pr["front"][0] + 3:
        fa = mid[j0:j1 + 1, 0]
        for hi, bz in enumerate(rec["bolt_z"]):
            zc = bz - rec["post_ground_z"]
            if not (zs[0] + 0.02 < zc < zs[-1] - 0.02):
                continue
            holes.append((zc, POST_SLOT[0], POST_SLOT[1], 1.0))
        if rec["tag_hole"] and lod == 0 and len(rec["bolt_z"]) >= 2:
            # BETWEEN two rails, not 75 mm under the head: at 75 mm the
            # inventory hole's removal rectangle overlapped the top bolt slot's
            # and the two O-grids were built over each other -- 32 boundary
            # edges and 24 edges with three faces on them, i.e. a torn hole
            # with a flap of steel in it.
            zt = 0.5 * (rec["bolt_z"][-1] + rec["bolt_z"][-2]) \
                - rec["post_ground_z"]
            holes.append((zt, TAG_HOLE_D, TAG_HOLE_D, 0.0))

    removed = np.zeros((NZ - 1, K - 1 if not closed else K), bool)
    hole_specs = []
    for (zc, hw, hh, slot) in holes:
        # the removal rectangle: 1.6x the hole across, 1.5x up it
        aw = min(hw * 1.62, abs(mid[j1, 0] - mid[j0, 0]) * 0.5 - 0.0035)
        ah = hh * 0.75 + 0.010
        if aw < hw * 0.62:
            continue
        # snap to existing grid rows and columns
        ac = 0.5 * (mid[j0, 0] + mid[j1, 0])
        cols = np.flatnonzero((mid[:, 0] >= ac - aw) & (mid[:, 0] <= ac + aw)
                              & (np.arange(K) >= j0) & (np.arange(K) <= j1))
        rows = np.flatnonzero((zs >= zc - ah) & (zs <= zc + ah))
        if len(cols) < 5 or len(rows) < 5:
            continue
        c0, c1 = int(cols[0]), int(cols[-1])
        r0, r1 = int(rows[0]), int(rows[-1])
        if removed[r0:r1, c0:c1].any():
            continue                        # never punch through a punched hole
        removed[r0:r1, c0:c1] = True
        hole_specs.append((r0, r1, c0, c1, zc, hw, hh, slot))

    # --- outer / inner surface quads -----------------------------------------
    ncol = K if closed else K - 1
    ii, jj = np.meshgrid(np.arange(NZ - 1), np.arange(ncol), indexing="ij")
    jn = (jj + 1) % K
    keep = ~removed
    ii = ii[keep]; jj = jj[keep]; jn = jn[keep]
    Qo = np.stack([bo_i + ii * K + jj, bo_i + ii * K + jn,
                   bo_i + (ii + 1) * K + jn, bo_i + (ii + 1) * K + jj], axis=-1)
    Qi = np.stack([bi_i + ii * K + jn, bi_i + ii * K + jj,
                   bi_i + (ii + 1) * K + jj, bi_i + (ii + 1) * K + jn], axis=-1)
    m.quads(Qo)
    m.quads(Qi)

    # --- the punched slots ----------------------------------------------------
    for (r0, r1, c0, c1, zc, hw, hh, slot) in hole_specs:
        loop = _ring_loop(r0, r1, c0, c1)
        N = len(loop)
        OL = np.array([bo_i + r * K + c for (r, c) in loop], np.int64)
        IL = np.array([bi_i + r * K + c for (r, c) in loop], np.int64)
        # the hole outline, sampled at the same count, aligned by angle
        S = _stadium(hw, hh, N)
        BL = np.array([[mid[c, 0] - 0.5 * (mid[c0, 0] + mid[c1, 0]), zs[r] - zc]
                       for (r, c) in loop])

        def signed_area(P):
            return float(np.sum(P[:, 0] * np.roll(P[:, 1], -1)
                                - np.roll(P[:, 0], -1) * P[:, 1]))

        # WINDING FIRST, THEN PHASE.  The boundary loop is walked in whatever
        # direction the grid runs; if the hole outline is walked the other way
        # the ring quads cross over themselves and the slot renders as a bow
        # tie.  Reversing after aligning re-breaks the alignment, so the order
        # matters.
        if signed_area(S) * signed_area(BL) < 0:
            S = S[::-1].copy()
        p0 = BL[0]
        ang0 = math.atan2(p0[1], p0[0])
        angs = np.arctan2(S[:, 1], S[:, 0])
        roll = int(np.argmin(np.abs(((angs - ang0 + math.pi) % (2 * math.pi))
                                    - math.pi)))
        S = np.roll(S, -roll, axis=0)

        ac = 0.5 * (mid[c0, 0] + mid[c1, 0])
        nrings = 3 if slot > 0.5 else 2
        prev_o, prev_i = OL, IL
        for k in range(1, nrings + 1):
            f = k / float(nrings)
            aa = BL[:, 0] * (1.0 - f) + S[:, 0] * f + ac
            zz2 = BL[:, 1] * (1.0 - f) + S[:, 1] * f + zc
            # the last ring is the hole edge itself: draw it in with the die roll
            drz = SLOT_DIE_ROLL if k == nrings else 0.0
            V_o = np.empty((N, 3))
            V_i = np.empty((N, 3))
            for q in range(N):
                z = float(zz2[q])
                i_lo = int(np.clip(np.searchsorted(zs, z) - 1, 0, NZ - 2))
                fz = (z - zs[i_lo]) / max(zs[i_lo + 1] - zs[i_lo], 1e-9)
                dxl = dx[i_lo] * (1 - fz) + dx[i_lo + 1] * fz
                dyl = dy[i_lo] * (1 - fz) + dy[i_lo + 1] * fz
                twl = tw[i_lo] * (1 - fz) + tw[i_lo + 1] * fz
                sal = sa[i_lo] * (1 - fz) + sa[i_lo + 1] * fz
                sbl = sb[i_lo] * (1 - fz) + sb[i_lo + 1] * fz
                a = float(aa[q]) * sal
                b_out = (0.0 + drz - rec["D"] * 0.5) * sbl + rec["D"] * 0.5
                b_in = (t - drz * 0.5 - rec["D"] * 0.5) * sbl + rec["D"] * 0.5
                cq, sq = math.cos(twl), math.sin(twl)
                V_o[q] = (a * cq - b_out * sq + dxl,
                          a * sq + b_out * cq + dyl, z)
                V_i[q] = (a * cq - b_in * sq + dxl,
                          a * sq + b_in * cq + dyl, z)
            edge = 1.0 if k == nrings else 0.0
            ao_ = m.add(V_o, dict(ap_slot=edge, ap_cut=edge,
                                  ap_hz=np.clip(zz2 / max(rec["stand"], 1e-6), -1, 1),
                                  ap_front=1.0))
            ai_ = m.add(V_i, dict(ap_slot=edge, ap_cut=edge, ap_inside=1.0,
                                  ap_hz=np.clip(zz2 / max(rec["stand"], 1e-6), -1, 1),
                                  ap_front=1.0))
            r_ = np.arange(N)
            rn = (r_ + 1) % N
            m.quads(np.stack([prev_o[r_], prev_o[rn], ao_ + rn, ao_ + r_], axis=-1))
            m.quads(np.stack([prev_i[rn], prev_i[r_], ai_ + r_, ai_ + rn], axis=-1))
            prev_o, prev_i = ao_ + r_, ai_ + r_
        # the wall of the hole, with the exit burr
        r_ = np.arange(N)
        rn = (r_ + 1) % N
        m.quads(np.stack([prev_o[rn], prev_o[r_], prev_i[r_], prev_i[rn]], axis=-1))

    # --- the rolled driven head ----------------------------------------------
    # NOT a flat cap.  A sheared end that has been hit 40 times by a drive cap
    # rolls over into a burr with a radius of about half the wall thickness --
    # 2.1-3.0 mm, which is 3.0-4.3 px, and it is the top edge of the object.
    nroll = HEAD_ROLL_N[lod]
    tilt = rec["head_tilt"]
    top_o = OUT[NZ - 1]
    top_i = INN[NZ - 1]
    mid_top = 0.5 * (top_o + top_i)
    nn = top_o - top_i
    nl = np.maximum(np.linalg.norm(nn[:, :2], axis=1, keepdims=True), 1e-12)
    nn2 = nn[:, :2] / nl
    rr = 0.5 * t * (0.80 + 0.55 * np.array(
        [h01(rec["seed"], 400 + (j * 13) % 89) for j in range(K)]))
    # the drive cap also dishes the head by 0.3-1.2 mm and tilts it
    dish = (0.0003 + 0.0009 * h01(rec["seed"], 7))
    prev = np.arange(K) + bo_i + (NZ - 1) * K
    ring_prev = prev
    roll_rings = []
    for k in range(1, nroll + 1):
        f = k / float(nroll + 1)
        ang = math.pi * f
        V = np.empty((K, 3))
        V[:, :2] = mid_top[:, :2] + nn2 * (rr * math.cos(ang))[:, None]
        V[:, 2] = (mid_top[:, 2] + rr * math.sin(ang)
                   + tilt * mid_top[:, 0] - dish * math.sin(ang))
        a = m.add(V, dict(ap_head=1.0, ap_burr=math.sin(ang), ap_cut=1.0,
                          ap_hz=1.0))
        r_ = np.arange(K)
        rn = (r_ + 1) % K if closed else np.minimum(r_ + 1, K - 1)
        sel = r_ if closed else r_[:-1]
        m.quads(np.stack([ring_prev[sel], ring_prev[rn[sel]],
                          a + rn[sel], a + sel], axis=-1))
        ring_prev = a + r_
        roll_rings.append(a)
    r_ = np.arange(K)
    rn = (r_ + 1) % K if closed else np.minimum(r_ + 1, K - 1)
    sel = r_ if closed else r_[:-1]
    ti = np.arange(K) + bi_i + (NZ - 1) * K
    m.quads(np.stack([ring_prev[sel], ring_prev[rn[sel]], ti[rn[sel]], ti[sel]],
                     axis=-1))
    if not closed:
        # THE SHEARED CORNER.  An open section has two free edges, and the
        # rolled top has to close across each of them or the post has a 5 x 2.5
        # mm hole in it at the exact corner the eye goes to.  That is 7 x 4 px
        # and it was there.
        for j in (0, K - 1):
            chain = ([bo_i + (NZ - 1) * K + j]
                     + [rr + j for rr in roll_rings]
                     + [bi_i + (NZ - 1) * K + j])
            m.tris(np.array([[chain[0], chain[q], chain[q + 1]]
                             for q in range(1, len(chain) - 1)], np.int64))

    # --- the bottom cap (driven toe) -----------------------------------------
    bo_row = np.arange(K) + bo_i
    bi_row = np.arange(K) + bi_i
    m.quads(np.stack([bo_row[rn[sel]], bo_row[sel], bi_row[sel], bi_row[rn[sel]]],
                     axis=-1))

    # --- the sheared edges of an open section --------------------------------
    if not closed:
        for (j, flip) in ((0, False), (K - 1, True)):
            oc = bo_i + np.arange(NZ) * K + j
            ic = bi_i + np.arange(NZ) * K + j
            a_ = np.arange(NZ - 1)
            if flip:
                m.quads(np.stack([oc[a_], oc[a_ + 1], ic[a_ + 1], ic[a_]], axis=-1))
            else:
                m.quads(np.stack([oc[a_ + 1], oc[a_], ic[a_], ic[a_ + 1]], axis=-1))
    return m


def _cap_mesh(rec, pr, m):
    """A pressed steel cap over the driven head.  5 % of posts carry one.

    A CLOSED pressing, not a fan collapsed to a point: the first version ended
    its dome on K coincident vertices, which is K zero-length edges and K
    zero-area faces, and a zero-area face has no normal.  This one is a real
    0.8 mm pressing with an outer face, an inner face and a rolled bottom rim,
    and it closes on a single apex vertex on each surface.

    The cap spans the OPEN back of a channel section, which is what a cap is
    for, so its rings are always closed loops whatever the post's profile is.
    """
    mid = pr["mid"]
    nrm = pr["nrm"]
    K = len(mid)
    t = pr["t"]
    ct = 0.0008                                  # cap sheet thickness
    z = rec["stand"]
    dx, dy, tw, sa, sb = _warp(rec, np.array([z]))
    skirt = 0.011 + 0.007 * h01(rec["seed"], 21)
    seat = 0.0013                                # clearance over the post
    out = mid + nrm * (t * 0.5 + seat)
    ctr2 = out.mean(axis=0)

    def place(P2, dz, sgn):
        """(K,2) section points -> world-local (K,3) at the cap's frame."""
        V = np.empty((len(P2), 3))
        a = P2[:, 0] * sa[0]
        b = (P2[:, 1] - rec["D"] * 0.5) * sb[0] + rec["D"] * 0.5
        cq, sq = math.cos(tw[0]), math.sin(tw[0])
        V[:, 0] = a * cq - b * sq + dx[0]
        V[:, 1] = a * sq + b * cq + dy[0]
        V[:, 2] = z + dz + rec["head_tilt"] * P2[:, 0] + sgn * 0.0
        return V

    # (dz, shrink toward the section centroid).  The dome is a real pressing:
    # a vertical skirt, a rolled shoulder, then a shallow crown.
    LV = [(-skirt, 1.000), (-0.0012, 1.000), (0.0016, 0.955),
          (0.0038, 0.780), (0.0052, 0.480), (0.0059, 0.180)]
    O, I = [], []
    for (dz, sh) in LV:
        P2 = ctr2 + (out - ctr2) * sh
        O.append(m.add(place(P2, dz, +1),
                       dict(ap_head=0.30, ap_cut=0.20, ap_hz=1.0)))
        P2i = ctr2 + (out - ctr2) * sh - (out - ctr2) / np.maximum(
            np.linalg.norm(out - ctr2, axis=1, keepdims=True), 1e-9) * ct
        I.append(m.add(place(P2i, dz - ct, +1),
                       dict(ap_head=0.30, ap_cut=0.20, ap_inside=1.0, ap_hz=1.0)))
    apex_o = m.add(place(np.array([ctr2]), LV[-1][0] + 0.0006, +1),
                   dict(ap_head=0.30, ap_hz=1.0))
    apex_i = m.add(place(np.array([ctr2]), LV[-1][0] + 0.0006 - ct, +1),
                   dict(ap_head=0.30, ap_inside=1.0, ap_hz=1.0))

    r_ = np.arange(K)
    rn = (r_ + 1) % K
    for k in range(len(LV) - 1):
        m.quads(np.stack([O[k] + r_, O[k] + rn, O[k + 1] + rn, O[k + 1] + r_],
                         axis=-1))
        m.quads(np.stack([I[k] + rn, I[k] + r_, I[k + 1] + r_, I[k + 1] + rn],
                         axis=-1))
    m.tris(np.stack([O[-1] + r_, O[-1] + rn, np.full(K, apex_o)], axis=-1))
    m.tris(np.stack([I[-1] + rn, I[-1] + r_, np.full(K, apex_i)], axis=-1))
    # the rolled bottom rim closes the pressing
    m.quads(np.stack([O[0] + rn, O[0] + r_, I[0] + r_, I[0] + rn], axis=-1))


def _splint_mesh(rec, pr, m, lod):
    """A repair splint: 320 mm of channel bolted over a bent post, which is what
    a circuit does at 11 pm on a Saturday rather than pull the post."""
    z0 = rec["bend_z"] - 0.150
    z1 = rec["bend_z"] + 0.170
    n = {0: 26, 1: 14, 2: 6, 3: 3}[lod]
    zs = np.linspace(z0, z1, n)
    Wd = rec["W"] + 0.014
    D = min(rec["D"] * 0.55, 0.062)
    ts = 0.005
    half = Wd * 0.5
    cor = [(+half, D), (+half, 0.0), (-half, 0.0), (-half, D)]
    rad = [0.0, 0.010, 0.010, 0.0]
    step = {0: 0.0035, 1: 0.008, 2: 0.020, 3: 0.050}[lod]
    mid, _tg = _fillet2d(cor, rad, False, step, {0: 8.0, 1: 16.0, 2: 40.0,
                                                 3: 80.0}[lod])
    d = np.zeros_like(mid)
    d[1:-1] = mid[2:] - mid[:-2]
    d[0] = mid[1] - mid[0]
    d[-1] = mid[-1] - mid[-2]
    d /= np.maximum(np.linalg.norm(d, axis=1, keepdims=True), 1e-12)
    nr = _rot90(d)
    K = len(mid)
    dx, dy, tw, sa, sb = _warp(rec, zs)
    OUT = np.empty((n, K, 3))
    INN = np.empty((n, K, 3))
    # the splint is bolted on STRAIGHT: it is a new piece of steel, and the gap
    # between it and the bent post is the whole point of it being visible
    for i in range(n):
        for P, DST, sgn in ((mid, OUT, +1), (mid, INN, -1)):
            q = P + nr * (sgn * ts * 0.5)
            a = q[:, 0]
            b = q[:, 1] - 0.004
            cq, sq = math.cos(tw[0]), math.sin(tw[0])
            DST[i, :, 0] = a * cq - b * sq + dx[0] + (zs[i] - zs[0]) * math.tan(rec["lean_a"])
            DST[i, :, 1] = a * sq + b * cq + dy[0] + (zs[i] - zs[0]) * math.tan(rec["lean_b"])
            DST[i, :, 2] = zs[i]
    ao = m.add(OUT.reshape(-1, 3), dict(ap_cut=0.15, ap_hz=0.4))
    ai = m.add(INN.reshape(-1, 3), dict(ap_cut=0.15, ap_inside=1.0, ap_hz=0.4))
    ii, jj = np.meshgrid(np.arange(n - 1), np.arange(K - 1), indexing="ij")
    ii = ii.ravel(); jj = jj.ravel()
    m.quads(np.stack([ao + ii * K + jj, ao + ii * K + jj + 1,
                      ao + (ii + 1) * K + jj + 1, ao + (ii + 1) * K + jj], axis=-1))
    m.quads(np.stack([ai + ii * K + jj + 1, ai + ii * K + jj,
                      ai + (ii + 1) * K + jj, ai + (ii + 1) * K + jj + 1], axis=-1))
    a_ = np.arange(n - 1)
    for (j, flip) in ((0, False), (K - 1, True)):
        oc = ao + np.arange(n) * K + j
        ic = ai + np.arange(n) * K + j
        if flip:
            m.quads(np.stack([oc[a_], oc[a_ + 1], ic[a_ + 1], ic[a_]], axis=-1))
        else:
            m.quads(np.stack([oc[a_ + 1], oc[a_], ic[a_], ic[a_ + 1]], axis=-1))
    j_ = np.arange(K - 1)
    for (i, flip) in ((0, True), (n - 1, False)):
        oc = ao + i * K + np.arange(K)
        ic = ai + i * K + np.arange(K)
        if flip:
            m.quads(np.stack([oc[j_], oc[j_ + 1], ic[j_ + 1], ic[j_]], axis=-1))
        else:
            m.quads(np.stack([oc[j_ + 1], oc[j_], ic[j_], ic[j_ + 1]], axis=-1))


def _collar_mesh(rec, pr, m, lod):
    """The collar of disturbed ground the manifest asks for, by name.

    A driven post heaves a ring of platform against its shaft, and six years of
    being leaned on opens a crescent gap on the lean side.  The rim is
    COLLAR_RIM (4 mm) proud of the datum and its skirt is driven COLLAR_SKIRT
    (50 mm) below it, so there is no coplanar pair with build_barriers' runoff
    platform anywhere -- which is the only way this item could have produced a
    z-fight, and it cannot.
    """
    NA = COLLAR_N[lod]
    NR = COLLAR_RINGS[lod]
    ang = np.linspace(0.0, 2.0 * math.pi, NA, endpoint=False)
    ca, sa_ = np.cos(ang), np.sin(ang)
    sd = rec["seed"]

    # plan radius: not a disc.  fbm around the ring, plus a bias downhill.
    rj = fbm1(ang * 2.4 + h01(sd, 31) * 20.0, seed=sd % 997, oct=3)
    r_out = rec["collar_r"] * (0.74 + 0.52 * rj)

    # the lean direction: where the crescent gap opens and the heave piles up
    gsx, gsy = rec.get("g_slope", (0.0, 0.0))
    lean_dir = math.atan2(rec["lean_b"], rec["lean_a"] + 1e-9)
    lean_mag = math.hypot(rec["lean_a"], rec["lean_b"])
    crescent = np.cos(ang - lean_dir)

    # The inner boundary follows the SECTION, not a circle: the hole a driven
    # sigma post leaves is the shape of a sigma post.
    #
    # AND IT FOLLOWS THE SECTION WHERE THE SECTION ACTUALLY IS.  The shaft is
    # bowed, leaned and twisted, so at the ground line it is displaced by up to
    # 9 mm from the nominal axis; a collar cut around the NOMINAL section leaves
    # a 9 mm crescent of daylight on one side, which is 13 px of hole that
    # nobody asked for.  The warp at z = 0 is applied to the outline first.
    mid = pr["mid"]
    t = pr["t"]
    ext = mid + pr["nrm"] * (t * 0.5)
    _dx0, _dy0, _tw0, _sa0, _sb0 = _warp(rec, np.array([0.0]))
    _a = ext[:, 0] * _sa0[0]
    _b = (ext[:, 1] - rec["D"] * 0.5) * _sb0[0] + rec["D"] * 0.5
    _cq, _sq = math.cos(_tw0[0]), math.sin(_tw0[0])
    ext = np.stack([_a * _cq - _b * _sq + _dx0[0],
                    _a * _sq + _b * _cq + _dy0[0]], axis=1)
    # the BOUNDING-BOX centre, not the mean of the samples: an open channel is
    # sampled unevenly round its outline and the mean walks toward whichever
    # face carries the most points.
    cx = float(0.5 * (ext[:, 0].min() + ext[:, 0].max()))
    cy = float(0.5 * (ext[:, 1].min() + ext[:, 1].max()))
    ea = np.arctan2(ext[:, 1] - cy, ext[:, 0] - cx)
    er = np.hypot(ext[:, 0] - cx, ext[:, 1] - cy)
    o = np.argsort(ea)
    ea, er = ea[o], er[o]
    ea = np.concatenate([ea - 2 * math.pi, ea, ea + 2 * math.pi])
    er = np.concatenate([er, er, er])
    r_sec = np.interp(ang, ea, er)
    gap = rec["collar_gap"] * (0.35 + 0.65 * clamp01(0.5 + 0.5 * crescent))
    r_in = r_sec + gap
    r_out = np.maximum(r_out, r_in + 0.055)

    heave = rec["collar_heave"] * (0.55 + 0.45 * clamp01(0.5 - 0.5 * crescent)) \
        * (0.6 + 0.8 * fbm1(ang * 3.1 + 7.0 * h01(sd, 32), seed=(sd + 5) % 991, oct=3))
    # the gap side is a HOLE, not a mound: the post has rocked the ground away
    dig = 0.018 * clamp01(lean_mag / 0.03 + rec["crush"]) \
        * clamp01(0.5 + 0.5 * crescent)

    rings = []
    for k in range(NR + 1):
        f = k / float(NR)
        r = r_in + (r_out - r_in) * (f ** 0.78)
        z = (heave * (1.0 - f) ** 1.9 - dig * (1.0 - f) ** 2.6
             + COLLAR_RIM * f ** 1.4)
        # STONES.  A COHERENT 2D FIELD over the collar's own plane, sampled
        # at the vertex's real position -- so the same lump appears on the two
        # rings that straddle it and reads as a stone rather than as two
        # unrelated plates.  Two scales: 70 mm clods of turned spoil and 28 mm
        # chippings, which at 1436 px/m are 100 px and 40 px.
        if lod <= 2 and k > 0:
            amp1, amp2 = {0: (0.0055, 0.0024), 1: (0.0042, 0.0014),
                          2: (0.0026, 0.0)}[lod]
            px = cx + r * ca + h01(sd, 33) * 60.0
            py = cy + r * sa_ + h01(sd, 34) * 60.0
            z = z + amp1 * (_fbm2(px / 0.070, py / 0.070, seed=sd % 887,
                                  oct=3) - 0.5) * 2.0 * (0.40 + f)
            if amp2 > 0.0:
                z = z + amp2 * (_fbm2(px / 0.028, py / 0.028,
                                      seed=(sd + 13) % 883, oct=2) - 0.5) \
                    * 2.0 * (0.35 + f)
        # ride the platform's own slope, so the rim is COLLAR_RIM proud of
        # the real ground everywhere instead of crossing it
        z = z + gsx * (cx + r * ca) + gsy * (cy + r * sa_)
        P = np.stack([cx + r * ca, cy + r * sa_, z], axis=1)
        stone = np.full(NA, 0.0 if k == 0 else 1.0)
        rings.append(m.add(P, dict(ap_ground=1.0, ap_stone=stone,
                                   ap_hz=0.0, ap_buried=0.0)))
    # THE COLLAR IS A CLOSED RING SOLID, not a disc with two open boundaries.
    # The first version left the inner boundary (against the shaft) and the
    # skirt bottom open: 2 x NA non-manifold edges, a hole you can see the
    # underside of the ground through at a 12.5 deg sun, and a signed volume
    # that made `recalc_face_normals` orient the WHOLE object inside out.
    # Outer skirt down, bottom annulus back in, inner skirt back up to ring 0.
    z_bot = COLLAR_RIM - COLLAR_SKIRT + gsx * (cx + r_out * ca) \
        + gsy * (cy + r_out * sa_)
    P = np.stack([cx + r_out * ca, cy + r_out * sa_, z_bot], axis=1)
    rings.append(m.add(P, dict(ap_ground=1.0, ap_stone=1.0, ap_buried=1.0)))
    z_in0 = heave - dig + gsx * (cx + r_in * ca) + gsy * (cy + r_in * sa_)
    P = np.stack([cx + r_in * ca, cy + r_in * sa_,
                  np.minimum(z_in0 - 0.055, z_bot)], axis=1)
    rings.append(m.add(P, dict(ap_ground=1.0, ap_stone=0.0, ap_buried=1.0)))

    r_ = np.arange(NA)
    rn = (r_ + 1) % NA
    for k in range(len(rings) - 1):
        m.quads(np.stack([rings[k] + r_, rings[k] + rn,
                          rings[k + 1] + rn, rings[k + 1] + r_], axis=-1))
    # and the inner skirt closes it back onto the top surface's inner ring
    m.quads(np.stack([rings[-1] + r_, rings[-1] + rn,
                      rings[0] + rn, rings[0] + r_], axis=-1))


def build_post_mesh(rec, lod):
    """One post -> (verts, quads, tris, attrs) in its own local frame."""
    pr = section_profile(rec["fam"], lod)
    zs = _z_stations(rec, lod)
    m = _shell(rec, pr, zs, lod)
    if rec["capped"]:
        _cap_mesh(rec, pr, m)
    if rec["splint"] and lod <= 2:
        _splint_mesh(rec, pr, m, lod)
    _collar_mesh(rec, pr, m, lod)
    return m.finish()


# ==============================================================================
#  6.  THE MATERIALS
# ==============================================================================

NT = W.NT
PAL = dict(W.PAL)

# Zinc carbonate bloom as it actually reads on a six-year-old post: a thin
# chalky film over mid-grey metal.  ``PAL["white_rust"]`` is 0.295 linear, which
# is right for a fresh bloom on a rail that is still 0.88 metallic and therefore
# has almost no diffuse term -- but on a post whose metallic has been dropped to
# let the film show, 0.295 diffuse under a 115 W/m2 sun renders as white plaster.
# 0.19 is where a post lands beside the rail it holds.
CHALK = (0.190, 0.186, 0.178)


def mat_post():
    """Hot-dip galvanised post steel, driven, and then left outside for years.

    Nine surface histories, in the order the metal acquired them:

      1  the spangle           the zinc crystal, 5-40 mm, two scales
      2  the withdrawal runs   vertical drip lines from the galvanising bath
      3  the age of the run    `ap_age` is constant over a maintenance run
      4  white rust            zinc carbonate bloom, worst where water sits
      5  the driven head       zinc destroyed by the drive cap -> bare steel
      6  red rust from the     which then bleeds DOWN the post, so it is a
         head and the punched  height-dependent streak and not a blotch
         edges
      7  cracked zinc at the   a plastic hinge cracks the coating in a band
         impact hinge
      8  the splash line       0-0.32 m: track spray, rubber and brake dust
      9  soil at the collar    and the wet line where the ground holds water

    Every one of them reads TexCoord->Object.  `Geometry->Position` appears
    nowhere: at |P| ~ 1000 m it has no precision left, which is what caused the
    blotching in the first pass.
    """
    name = PFX + "PostSteel"
    old = bpy.data.materials.get(name)
    if old is not None:
        return old
    t = NT(name)
    co = t.n("ShaderNodeTexCoord")
    ofs = t.comb(t.attr("ap_ofs_x", 2, "OBJECT"), t.attr("ap_ofs_y", 2, "OBJECT"),
                 t.attr("ap_ofs_z", 2, "OBJECT"))
    P = t.vmath("ADD", (co, 3), ofs)                 # Object coords + per-post offset
    Pz = t.sep(P, 2)

    age = t.attr("ap_age", 2, "OBJECT")
    a_head = t.attr("ap_head")
    a_burr = t.attr("ap_burr")
    a_cut = t.attr("ap_cut")
    a_slot = t.attr("ap_slot")
    a_bend = t.attr("ap_bend")
    a_hz = t.attr("ap_hz")
    a_in = t.attr("ap_inside")
    a_gnd = t.attr("ap_ground")
    a_stone = t.attr("ap_stone")
    a_bur = t.attr("ap_buried")

    # 1. the spangle, two scales
    sp1 = t.vor(P, 34.0, "F1", 0, 0.95)
    sp1d = t.vor(P, 34.0, "F1", 1, 0.95)
    sp2 = t.vor(t.vmath("SCALE", P, scale=1.0), 128.0, "F1", 0, 1.0)
    # 2. the withdrawal runs: vertical, so scale z hard and a/b softly
    runv = t.comb(t.math("MULTIPLY", t.sep(P, 0), 9.0),
                  t.math("MULTIPLY", t.sep(P, 1), 9.0),
                  t.math("MULTIPLY", Pz, 0.55))
    runs = t.noise(runv, 26.0, 7.0, 0.62)
    # 4. white rust
    wr = t.noise(P, 62.0, 8.0, 0.66)
    wr2 = t.noise(P, 8.5, 6.0, 0.55)
    # 6. red rust field
    rr = t.noise(P, 190.0, 7.0, 0.62)
    grime = t.noise(P, 14.0, 8.0, 0.58)

    # --- base zinc, aged ------------------------------------------------------
    zinc = t.cmix(t.maprange(sp1, 0.05, 0.92, 0.0, 1.0),
                  PAL["zinc_dull"], PAL["zinc_fresh"])
    zinc = t.cmix(t.math("MULTIPLY", t.maprange(sp2, 0.10, 0.85, 0.0, 1.0), 0.40),
                  zinc, PAL["zinc_dark"])
    zinc = t.cmix(t.math("MULTIPLY", age, 0.55), zinc, PAL["zinc_dark"])
    # the withdrawal runs are BRIGHTER (thicker zinc holds its spangle longer)
    zinc = t.cmix(t.math("MULTIPLY", t.maprange(runs, 0.52, 0.80, 0.0, 1.0),
                         t.math("SUBTRACT", 0.50, t.math("MULTIPLY", age, 0.32))),
                  zinc, PAL["zinc_fresh"])

    # --- 5. the driven head, the punched edges: the zinc is GONE --------------
    # computed BEFORE the carbonate bloom, because a drive cap knocks the bloom
    # off with the coating and a head that is both bare steel AND chalked is
    # neither.  The first version layered chalk over everything and the head
    # came back the colour of bone.
    bare = t.math("MULTIPLY", a_head, t.maprange(rr, 0.25, 0.75, 0.55, 1.0))
    bare = t.math("ADD", bare, t.math("MULTIPLY", a_burr, 0.60))
    bare = t.math("ADD", bare, t.math("MULTIPLY", a_slot, 0.85))
    bare = t.math("ADD", bare, t.math("MULTIPLY", a_cut, 0.30))
    bare = t.math("MINIMUM", bare, 1.0)

    # --- 4. the carbonate bloom ("white rust") -------------------------------
    # DARKER THAN THE ZINC IT SITS ON, not lighter.  It is a thin chalky film
    # over a mid-grey metal, and once the metal underneath stops contributing a
    # specular lobe the pair has to land near 0.19 or the post renders brighter
    # than the rail it holds -- which is physically impossible, because they
    # came out of the same bath.
    wmask = t.math("MULTIPLY", t.maprange(wr, 0.46, 0.88, 0.0, 1.0),
                   t.math("ADD", t.math("MULTIPLY", age, 0.62),
                          t.math("MULTIPLY", a_in, 0.24)))
    wmask = t.math("MULTIPLY", wmask,
                   t.maprange(wr2, 0.24, 0.80, 0.40, 1.0))
    wmask = t.math("MULTIPLY", wmask,
                   t.math("SUBTRACT", 1.0, t.math("MULTIPLY", bare, 0.92)))
    wmask = t.math("MINIMUM", wmask, 1.0)
    col = t.cmix(wmask, zinc, CHALK)

    col = t.cmix(t.math("MULTIPLY", bare, 0.88), col, PAL["steel_bare"])
    # 6. and bare steel rusts, and the rust bleeds DOWN
    bleed = t.math("MULTIPLY", t.maprange(a_hz, 0.55, 1.00, 0.0, 1.0),
                   t.maprange(rr, 0.42, 0.80, 0.0, 1.0))
    rustm = t.math("ADD", t.math("MULTIPLY", bare, 0.85),
                   t.math("MULTIPLY", bleed,
                          t.math("ADD", 0.20, t.math("MULTIPLY", age, 0.50))))
    rustm = t.math("MULTIPLY", t.math("MINIMUM", rustm, 1.0),
                   t.maprange(rr, 0.30, 0.85, 0.45, 1.0))
    col = t.cmix(t.math("MULTIPLY", rustm, 0.92), col, PAL["red_rust"])
    col = t.cmix(t.math("MULTIPLY", t.math("MULTIPLY", rustm,
                                           t.maprange(rr, 0.66, 0.92, 0.0, 1.0)),
                        0.55), col, PAL["rust_bright"])

    # --- 7. cracked zinc at the hinge -----------------------------------------
    crack = t.math("MULTIPLY", a_bend,
                   t.maprange(t.vor(P, 320.0, "F1", 0, 1.0), 0.0, 0.22, 1.0, 0.0))
    col = t.cmix(t.math("MULTIPLY", crack, 0.70), col, PAL["steel_bare"])

    # --- 8. NOTHING TRACKSIDE IS CLEAN ---------------------------------------
    # a general film of tyre dust, brake dust and dry mud over the whole post,
    # heavier as it ages.  Without it a galvanised post renders as a laboratory
    # sample: the geometry is right and the object still looks new.
    soil_n = t.noise(P, 3.4, 8.0, 0.60)
    film = t.math("MULTIPLY", t.maprange(soil_n, 0.34, 0.86, 0.10, 1.0),
                  t.math("ADD", 0.22, t.math("MULTIPLY", age, 0.46)))
    col = t.cmix(t.math("MULTIPLY", film, 0.62), col, PAL["dust"])
    # and rain washes it back off in vertical streaks, which is the single
    # most recognisable thing about a weathered upright.  Squash the texture
    # 14:1 in z and the noise becomes a run of drip lines.
    strv = t.comb(t.math("MULTIPLY", t.sep(P, 0), 14.0),
                  t.math("MULTIPLY", t.sep(P, 1), 14.0),
                  t.math("MULTIPLY", Pz, 0.62))
    streak = t.noise(strv, 30.0, 6.0, 0.58)
    streakm = t.math("MULTIPLY", t.maprange(streak, 0.48, 0.86, 0.0, 1.0),
                     t.math("MULTIPLY",
                            t.maprange(a_hz, 1.02, 0.10, 0.10, 1.0),
                            t.math("ADD", 0.30, t.math("MULTIPLY", age, 0.55))))
    col = t.cmix(t.math("MULTIPLY", streakm, 0.55), col, PAL["grime"])

    # --- 9. the splash line ---------------------------------------------------
    splash = t.math("MULTIPLY", t.maprange(a_hz, 0.34, -0.02, 0.0, 1.0),
                    t.maprange(grime, 0.34, 0.80, 0.15, 1.0))
    col = t.cmix(t.math("MULTIPLY", splash, 0.85), col, PAL["grime"])
    col = t.cmix(t.math("MULTIPLY",
                        t.math("MULTIPLY", splash,
                               t.maprange(grime, 0.55, 0.90, 0.0, 1.0)), 0.60),
                 col, PAL["rubber"])
    # 10. soil at the very bottom, and the buried length
    soil = t.maprange(a_hz, 0.075, 0.004, 0.0, 1.0)
    col = t.cmix(t.math("MULTIPLY", soil, 0.78), col, PAL["dust"])
    col = t.cmix(t.math("MULTIPLY", a_bur, 0.9), col, (0.052, 0.044, 0.036))
    # 11. lichen on the shaded inside face of an old post
    lich = t.math("MULTIPLY", t.math("MULTIPLY", age, a_in),
                  t.maprange(t.noise(P, 40.0, 6.0, 0.6), 0.62, 0.88, 0.0, 1.0))
    col = t.cmix(t.math("MULTIPLY", lich, 0.34), col, PAL["lichen"])

    # --- the surface ----------------------------------------------------------
    # STATED AS RADIANCE MODULATION, NOT MILLIMETRES (itemkit 5b, brief 4a).
    # m = 2 sin(theta) / tan(e), a 4.52x amplifier at this film's 12.47 deg sun.
    # Nothing here is re-tuned: each `modulation_pp` reproduces the Distance the
    # module already shipped, checked off the built graph by prove_noop.py.  The
    # band named is the one that is always present and carries most of the
    # height, with `height_pp` set to its own weight in the sum.
    #
    #   [0] sp1d  w 0.55  lam 63.82 mm  m 0.057  the zinc spangle
    #       runs  w 0.30  lam  6.84 mm  m 0.288  the withdrawal runs, and the
    #                                            band that actually carries this
    #                                            stage: isotropic_micro, ok.
    #                                            (6.84 mm because the domain is
    #                                            squashed 9:1 before the noise.)
    #       wr    w 0.25  lam 25.81 mm  m 0.064  white-rust field
    #   [1] rustm w 1.00  lam  8.42 mm  m 0.519  red rust, gated to the driven
    #                                            head and the punched edges:
    #                                            isotropic_macro, ok
    #       sp2   w 0.30  lam 16.95 mm  m 0.077  the fine spangle
    #   [2] grime w 1.00  lam 114.29 mm m 0.007  DOES NOTHING.  See below.
    #
    # TWO THINGS TO ARGUE WITH, AND BOTH SHIP UNCHANGED.
    # `sp1d` at 0.057 is under isotropic_micro's 0.12, but it is the Voronoi
    # CELL ID -- a piecewise-constant facet field, not a sinusoid -- so what is
    # visible is the step at the cell wall and the sinusoid conversion is a
    # floor on it, not a reading.  The stage is carried by `runs` at 0.288
    # regardless, so it is not a dead stage.
    # [2] IS a dead stage: 0.0264 mm at a 114 mm wavelength is m 0.007, which is
    # 0.4 % of what the record's smallest accepted relief does.  It is left
    # alone rather than raised because the honest reading is that a film of
    # tyre dust HAS no relief -- it is a colour, and it is already applied as
    # one.  If a later pass wants this stage to exist, isotropic_micro's floor
    # of 0.12 is Distance x18.3 (0.483 mm p-p), and that is a dent in a steel
    # post, not dirt.  Deleting the stage would be the better fix.
    LAM_SPANGLE = K.VORONOI_WAVELENGTH_FACTOR / 34.0     #  63.82 mm
    LAM_RUST = K.NOISE_WAVELENGTH_FACTOR / 190.0         #   8.42 mm
    LAM_GRIME = K.NOISE_WAVELENGTH_FACTOR / 14.0         # 114.29 mm
    bump = t.bump(t.math("ADD",
                         t.math("MULTIPLY", sp1d, 0.55),
                         t.math("ADD", t.math("MULTIPLY", runs, 0.30),
                                t.math("MULTIPLY", wr, 0.25))),
                  0.42, modulation_pp=0.056554, wavelength_m=LAM_SPANGLE,
                  height_pp=0.55)
    bump = t.bump(t.math("ADD", t.math("MULTIPLY", rustm, 1.0),
                         t.math("MULTIPLY", sp2, 0.30)),
                  0.55, normal=bump,
                  modulation_pp=0.518703, wavelength_m=LAM_RUST)
    bump = t.bump(t.math("MULTIPLY", grime, 1.0), 0.22, normal=bump,
                  modulation_pp=0.006563, wavelength_m=LAM_GRIME)

    rough = t.maprange(wr, 0.20, 0.85, 0.26, 0.46)
    rough = t.fmix(t.math("MULTIPLY", age, 0.95), rough,
                   t.maprange(wr, 0.2, 0.8, 0.46, 0.72))
    rough = t.fmix(t.math("MULTIPLY", wmask, 0.9), rough, 0.80)
    rough = t.fmix(t.math("MINIMUM", rustm, 1.0), rough, 0.88)
    rough = t.fmix(t.math("MULTIPLY", film, 0.85), rough, 0.78)
    rough = t.fmix(t.math("MULTIPLY", streakm, 0.8), rough, 0.84)
    rough = t.fmix(t.math("MULTIPLY", splash, 0.9), rough, 0.80)

    # ZINC IS ONLY A MIRROR WHILE IT IS NEW, but it never stops being metal.
    # Driving `metallic` to 1.0 across the whole post -- which the first version
    # did -- leaves a flat vertical face with nothing to show but the reflection
    # of a dark runoff platform, and 3,304 posts render as charcoal bars.
    # Driving it to 0.10 under a chalk layer is the opposite error and rendered
    # them as white plaster.  Aged zinc keeps a real specular lobe under the
    # carbonate; 0.92 -> 0.44 is where the pair sits.
    dielec = t.math("MINIMUM",
                    t.math("ADD", t.math("MULTIPLY", wmask, 0.80),
                           t.math("ADD", rustm,
                                  t.math("ADD", t.math("MULTIPLY", film, 0.55),
                                         t.math("ADD",
                                                t.math("MULTIPLY", streakm, 0.5),
                                                t.math("MULTIPLY", splash, 0.75))))),
                    1.0)
    metal = t.fmix(dielec, 0.92, 0.44)

    bs = t.n("ShaderNodeBsdfPrincipled")
    t.pin(bs, 0, col)
    t.pin(bs, 1, metal)
    t.pin(bs, 2, rough)
    # R2-070.  BY NAME.  Index 6 is `Normal` on Blender 5.2 and all three of
    # this module's sites were correct, but 6 is the socket directly behind
    # `Thin Wall`, the one 5.2 inserted -- the same insertion that silently
    # emptied nine DR_ materials (R2-057) and four CTX_ ones (R2-070).  A
    # correct index is a fragile index.
    t.pin_named(bs, "Normal", bump)
    out = t.n("ShaderNodeOutputMaterial")
    t.t.links.new(bs.outputs[0], out.inputs[0])
    return t.m




def mat_collar():
    """The disturbed ground ring: broken platform crust, stones, driving spoil."""
    name = PFX + "PostCollar"
    old = bpy.data.materials.get(name)
    if old is not None:
        return old
    t = NT(name)
    co = t.n("ShaderNodeTexCoord")
    ofs = t.comb(t.attr("ap_ofs_x", 2, "OBJECT"), t.attr("ap_ofs_y", 2, "OBJECT"),
                 t.attr("ap_ofs_z", 2, "OBJECT"))
    P = t.vmath("ADD", (co, 3), ofs)
    a_stone = t.attr("ap_stone")
    a_bur = t.attr("ap_buried")
    # 1 on the COLLAR, 0 on the surrounding platform: the stand-in ground
    # carries no attributes, and in the assembled world build_barriers' runoff
    # platform is a different material entirely.  Without this the collar is
    # the same colour as the ground it was dug out of, and a 0.5 m ring of
    # disturbed spoil reads as nothing at all from 2.6 m -- which is what the
    # first composed macro showed, and the manifest asks for this ring BY NAME.
    a_col = t.attr("ap_ground")
    age = t.attr("ap_age", 2, "OBJECT")

    v1 = t.vor(P, 52.0, "F1", 0, 1.0)          # 19 mm stones
    v2 = t.vor(P, 168.0, "F1", 0, 1.0)         # 6 mm chippings
    v3 = t.vor(P, 620.0, "F1", 0, 1.0)         # grit
    n1 = t.noise(P, 6.0, 9.0, 0.62)
    n2 = t.noise(P, 44.0, 8.0, 0.60)
    n3 = t.noise(P, 300.0, 5.0, 0.55)

    col = t.cmix(t.maprange(n1, 0.28, 0.74, 0.0, 1.0),
                 (0.030, 0.027, 0.024), (0.070, 0.063, 0.053))
    col = t.cmix(t.math("MULTIPLY", t.maprange(v1, 0.0, 0.26, 1.0, 0.0), 0.66),
                 col, (0.108, 0.099, 0.084))
    col = t.cmix(t.math("MULTIPLY", t.maprange(v2, 0.0, 0.20, 1.0, 0.0), 0.52),
                 col, (0.140, 0.130, 0.112))
    col = t.cmix(t.math("MULTIPLY", t.maprange(v3, 0.0, 0.16, 1.0, 0.0), 0.30),
                 col, (0.086, 0.079, 0.068))
    # freshly turned spoil is DARKER and damper than the crust around it
    col = t.cmix(t.math("MULTIPLY", t.maprange(n2, 0.40, 0.82, 0.0, 1.0),
                        t.math("SUBTRACT", 1.0, t.math("MULTIPLY", age, 0.6))),
                 col, (0.022, 0.019, 0.016))
    col = t.cmix(t.math("MULTIPLY", a_bur, 0.95), col, (0.016, 0.014, 0.012))
    # turned spoil: darker, damper, and with the fines washed out of it
    spoil = t.math("MULTIPLY", a_col,
                   t.maprange(t.noise(P, 26.0, 7.0, 0.60), 0.22, 0.82, 0.35, 1.0))
    col = t.cmix(t.math("MULTIPLY", spoil, 0.62), col, (0.019, 0.016, 0.013))
    col = t.cmix(t.math("MULTIPLY", t.math("MULTIPLY", a_col,
                                           t.maprange(v2, 0.0, 0.16, 1.0, 0.0)),
                        0.55), col, (0.152, 0.140, 0.118))
    # a little weed at the rim of an old collar
    col = t.cmix(t.math("MULTIPLY", t.math("MULTIPLY", age, a_stone),
                        t.maprange(t.noise(P, 90.0, 6.0, 0.6), 0.70, 0.92, 0.0, 0.55)),
                 col, (0.026, 0.040, 0.017))

    # STATED AS RADIANCE MODULATION, NOT MILLIMETRES (itemkit 5b, brief 4a).
    # Nothing here is re-tuned: each `modulation_pp` reproduces the Distance the
    # module already shipped.  THIS SURFACE IS THE EXCEPTION TO "THE MESH
    # CARRIES THE READ": the collar is a flat ring of triangles and every stone
    # in it is shading, so the whole stack sits in `hard_feature` (1.5-6.0) on
    # purpose.  A 19 mm stone in a dug ring has a real edge and a real shadow;
    # this is not an isotropic crumple and the crumple bands do not apply.
    #
    #   [0] v1  w 0.60  lam 41.73 mm  m 2.255  19 mm stones, and the stage
    #       v2  w 0.40  lam 12.92 mm  m 4.386  6 mm chippings
    #       n2  w 0.35  lam 36.36 mm  m 1.536  the spoil's own lumpiness
    #   [1] v3  w 0.60  lam  3.50 mm  m 3.029  grit
    #       n3  w 0.50  lam  5.33 mm  m 1.726  fines between the grit
    #   [2] v1  w 0.70  lam 41.73 mm  m 1.401  the same stones again, gated to
    #       v2  w 0.50  lam 12.92 mm  m 3.077  the collar by a_col: the turned
    #                                          spoil is coarser than the crust
    #
    # The one to watch is [0] v2 at 4.386 -- 2.28 mm of relief on a 12.9 mm
    # chipping is a 29 deg face, which is a stone standing on edge.  It is what
    # the module asked for and it is inside hard_feature, so it ships.
    LAM_STONE = K.VORONOI_WAVELENGTH_FACTOR / 52.0       # 41.73 mm
    LAM_GRIT = K.VORONOI_WAVELENGTH_FACTOR / 620.0       #  3.50 mm
    b = t.bump(t.math("ADD", t.math("MULTIPLY", v1, 0.60),
                      t.math("ADD", t.math("MULTIPLY", v2, 0.40),
                             t.math("MULTIPLY", n2, 0.35))), 0.95,
               modulation_pp=2.254823, wavelength_m=LAM_STONE, height_pp=0.60)
    b = t.bump(t.math("ADD", t.math("MULTIPLY", v3, 0.6),
                      t.math("MULTIPLY", n3, 0.5)), 0.55, normal=b,
               modulation_pp=3.028808, wavelength_m=LAM_GRIT, height_pp=0.60)
    # and the spoil is coarser than the crust it was dug out of
    b = t.bump(t.math("MULTIPLY", a_col,
                      t.math("ADD", t.math("MULTIPLY", v1, 0.7),
                             t.math("MULTIPLY", v2, 0.5))), 0.85,
               normal=b, modulation_pp=1.400671, wavelength_m=LAM_STONE,
               height_pp=0.70)
    bs = t.n("ShaderNodeBsdfPrincipled")
    t.pin(bs, 0, col)
    t.pin(bs, 2, t.maprange(n2, 0.2, 0.8, 0.78, 0.98))
    t.pin_named(bs, "Normal", b)
    t.pin(bs, 14, 0.10)
    out = t.n("ShaderNodeOutputMaterial")
    t.t.links.new(bs.outputs[0], out.inputs[0])
    return t.m


# ==============================================================================
#  7.  EMIT
# ==============================================================================

_new_mesh = W._new_mesh          # one mesh builder for the whole barrier zone
_shade_by_angle = W._shade_by_angle


def _emit_mesh(name, V, Q, T, A, smooth_deg=32.0):
    """Verts + faces + attributes -> a clean, correctly-oriented Blender mesh.

    Four things happen here that the raw builder cannot do, and all four are
    defects this item actually had:

      1. LOOSE VERTICES.  Punching a slot deletes the grid quads inside the
         removal rectangle but not the vertices they used, so a LOD0 post
         carried 300-700 orphans.
      2. DEGENERATE FACES.  Welding at 1 micron removes anything a fillet
         sampler or a collapsed fan produced with zero area, which is the only
         kind of face that has no normal.
      3. ORIENTATION.  `recalc_face_normals` makes the winding CONSISTENT, not
         necessarily OUTWARD -- on a shell whose signed volume it reads as
         negative it happily unifies the whole object inside out, which renders
         as a black post.  The signed volume is the test, and it is applied
         after the mesh is closed, so it is meaningful.
      4. The attributes must survive all of it, so they are baked BEFORE the
         bmesh pass and carried through as custom data layers.
    """
    import bmesh
    used = np.zeros(len(V), bool)
    for F in (Q, T):
        if len(F):
            used[np.asarray(F).ravel()] = True
    if not used.all():
        remap = np.cumsum(used) - 1
        V = V[used]
        A = {k: (a[used] if len(a) == len(used) else a) for k, a in A.items()}
        Q = remap[Q] if len(Q) else Q
        T = remap[T] if len(T) else T

    me = _new_mesh(name, V, Q, T, recalc=False, smooth_deg=None)
    for k in ATTRS:
        a = A.get(k)
        if a is not None and len(a) == len(V):
            at = me.attributes.new(k, "FLOAT", "POINT")
            at.data.foreach_set("value", np.ascontiguousarray(a, np.float32))

    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if bm.calc_volume(signed=True) < 0.0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    me.update()
    if smooth_deg is not None and len(me.polygons):
        _shade_by_angle(me, smooth_deg)
    return me


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


def _grade_lod(recs, anchor):
    if anchor is None or not len(anchor):
        for r in recs:
            r["lod"] = 2
        return
    A = np.asarray(anchor, float)
    P = np.array([r["origin"] for r in recs], float)
    P = P + np.array([0.0, 0.0, 0.5])
    d = np.min(np.linalg.norm(A[None, :, :] - P[:, None, :], axis=2), axis=1)
    for i, r in enumerate(recs):
        dd = float(d[i])
        r["lod"] = 0 if dd < 6.5 else (1 if dd < 26.0 else (2 if dd < 110.0 else 3))


def _world_frame(rec):
    """Right-handed local->world basis, and the local-x sign that goes with it.

    THE DEFECT THIS EXISTS TO PREVENT, because it cost 1,715 objects.
    The natural frame for a barrier item is [tangent, outward normal, up].  On
    the LEFT of travel that is right-handed; on the RIGHT of travel the outward
    normal points the other way and the triple is a REFLECTION, det = -1.
    ``mathutils.Matrix.to_quaternion()`` does not refuse a reflection -- it
    silently returns the quaternion of some rotation, and Blender applies that.
    Every post on the right of travel was therefore stood up in an arbitrary
    orientation: the macro showed a shaft running off the top of the frame with
    its collar 0.84 m up it, which is a post lying on its side.

    Two things made it survive three rounds of checking.  A post is nearly
    symmetric about its own axis, so most of them still read as "a post" from
    2.6 m.  And `ob.location + local_z` -- the obvious way to verify placement
    without a depsgraph -- is only valid if the rotation preserves z, which is
    exactly the assumption under test.  It reported 0 / 3,304 wrong.
    ``matrix_world`` reported the truth and was the thing being distrusted.

    Negating the tangent flips the determinant back to +1 and is exact: for any
    local point, [t, n, up] @ (a, b, c) == [-t, n, up] @ (-a, b, c).
    """
    tg = np.array(rec["tangent"], float)
    nm = np.array(rec["normal"], float)
    up = np.array([0.0, 0.0, 1.0])
    M = np.stack([tg, nm, up], axis=1)
    if np.linalg.det(M) < 0.0:
        return np.stack([-tg, nm, up], axis=1), -1.0
    return M, 1.0


def build_post(rec, coll, mats):
    """One post -> one object, recentred, in a canonical local frame."""
    V, Q, T, A = build_post_mesh(rec, rec["lod"])
    o = np.array(rec["origin"], float)
    M, xs = _world_frame(rec)
    V = V.copy()
    V[:, 0] *= xs

    ctr = V.mean(axis=0)
    Loc = V - ctr[None, :]
    name = "%sPost_%s%05d" % (PFX, "L" if rec["side"] > 0 else "R", rec["idx"])
    me = _emit_mesh(name, Loc, Q, T, A, smooth_deg=32.0)
    me.materials.append(mats[0])
    me.materials.append(mats[1])
    # the collar gets slot 1: it is ground, not steel.  Read back off the baked
    # attribute rather than off the pre-weld arrays, because the weld may have
    # renumbered the vertices.
    npoly = len(me.polygons)
    at = me.attributes.get("ap_ground")
    if npoly and at is not None:
        gi = np.empty(len(me.vertices), np.float32)
        at.data.foreach_get("value", gi)
        li = np.empty(len(me.loops), np.int32)
        me.loops.foreach_get("vertex_index", li)
        ls = np.empty(npoly, np.int32)
        me.polygons.foreach_get("loop_start", ls)
        mats_idx = (gi[li[ls]] > 0.5).astype(np.int32)
        me.polygons.foreach_set("material_index", mats_idx)

    ob = bpy.data.objects.new(name, me)
    world_ctr = o + M @ ctr
    ob.location = tuple(float(x) for x in world_ctr)
    ob.rotation_mode = "QUATERNION"
    from mathutils import Matrix
    ob.rotation_quaternion = Matrix(((M[0][0], M[0][1], M[0][2]),
                                     (M[1][0], M[1][1], M[1][2]),
                                     (M[2][0], M[2][1], M[2][2]))).to_quaternion()
    sd = rec["seed"]
    ob["ap_age"] = float(rec["galv"])
    ob["ap_run"] = float(rec["run"])
    ob["ap_crush"] = float(rec["crush"])
    ob["ap_seed"] = float(sd % 100003)
    # THE PER-POST TEXTURE OFFSET.  Object-space textures are the contract's
    # rule; this is the only thing that stops 3 304 posts sharing one spangle.
    ob["ap_ofs_x"] = float(h01(sd, 71) * 240.0)
    ob["ap_ofs_y"] = float(h01(sd, 72) * 240.0)
    ob["ap_ofs_z"] = float(h01(sd, 73) * 240.0)
    coll.objects.link(ob)
    return ob, len(V), len(Q) + len(T)


def build(sides=(+1, -1), lod_anchor=None, limit=None, scene=None,
          stats=None, windows=None):
    """Emit the item.  One object per post into ``W_Item_ArmcoPost``.

    sides       which sides of the circuit (+1 left, -1 right of travel)
    lod_anchor  list of world points (the camera path).  Mesh density is graded
                by distance to the nearest of them.  None -> uniform LOD 2.
    windows     {side: (s0, s1)} to build only part of a side.
    """
    scene = scene or bpy.context.scene
    purge()
    root = _coll(COLL)
    mats = (mat_post(), mat_collar())

    st = stats if stats is not None else {}
    st.setdefault("posts", 0)
    st.setdefault("verts", 0)
    st.setdefault("faces", 0)
    st.setdefault("lod", [0, 0, 0, 0])
    st.setdefault("fam", {})
    st.setdefault("stand", [])
    st.setdefault("bent", 0)

    for side in sides:
        recs = post_sites(side)
        w = (windows or {}).get(side)
        if w:
            recs = [r for r in recs if w[0] <= r["s"] <= w[1]]
        _grade_lod(recs, lod_anchor)
        if limit:
            recs = recs[:limit]
        log("side %+d: %d posts  (%s)" % (
            side, len(recs),
            " ".join("L%d=%d" % (l, sum(1 for r in recs if r["lod"] == l))
                     for l in range(4))))
        for i, r in enumerate(recs):
            ob, nv, nf = build_post(r, root, mats)
            st["posts"] += 1
            st["verts"] += nv
            st["faces"] += nf
            st["lod"][r["lod"]] += 1
            st["fam"][r["fam"]] = st["fam"].get(r["fam"], 0) + 1
            st["stand"].append(r["stand"])
            st["bent"] += 1 if r["bend_ang"] > 1e-6 else 0
            if (i + 1) % 400 == 0:
                log("   ... %d/%d  (%.2f M verts so far)"
                    % (i + 1, len(recs), st["verts"] / 1e6))

    C.stamp(root)
    root["item"] = ITEM
    root["posts"] = st["posts"]
    log("BUILT %d posts, %.3f M verts, %.3f M faces  (LOD %s)"
        % (st["posts"], st["verts"] / 1e6, st["faces"] / 1e6, st["lod"]))
    log("   families: " + ", ".join("%s=%d" % kv for kv in sorted(st["fam"].items())))
    log("   %d posts carry an impact hinge (%.1f %%)"
        % (st["bent"], 100.0 * st["bent"] / max(st["posts"], 1)))
    return root


# ==============================================================================
#  7b.  TEST-SCENE STAND-INS  —  owned by OTHER items, prefix APSTAND_
# ==============================================================================
# armco_spacer_block (build order 57) and the post bolt do not exist yet.  A
# macro of a post with a rail floating 283 mm in front of it and three empty
# holes in its face would be a worse test than one with stand-ins, so there are
# stand-ins -- under a prefix the gate is NOT run with, so not one triangle of
# them is measured as this item's work.  When armco_spacer_block lands, delete
# `build_standins` and call `spacer_sites()`.

def _standin_mat():
    mat = bpy.data.materials.get(XPFX + "Steel")
    if mat is not None:
        return mat
    t = NT(XPFX + "Steel")
    co = t.n("ShaderNodeTexCoord")
    P = (co, 3)
    v = t.vor(P, 40.0, "F1", 1, 0.92)
    n2 = t.noise(P, 240.0, 6.0, 0.6)
    col = t.cmix(t.maprange(t.sep(v, 0), 0.05, 0.95, 0.0, 1.0),
                 PAL["zinc_dull"], PAL["zinc_fresh"])
    col = t.cmix(t.math("MULTIPLY", t.maprange(n2, 0.62, 0.88, 0.0, 1.0), 0.45),
                 col, PAL["red_rust"])
    b = t.bump(t.math("MULTIPLY", n2, 1.0), 0.35, 0.0005)
    bs = t.n("ShaderNodeBsdfPrincipled")
    t.pin(bs, 0, col)
    t.pin(bs, 1, 0.86)
    t.pin(bs, 2, t.maprange(n2, 0.2, 0.8, 0.32, 0.58))
    t.pin_named(bs, "Normal", b)
    o = t.n("ShaderNodeOutputMaterial")
    t.t.links.new(bs.outputs[0], o.inputs[0])
    return t.m


def _box_shell(a0, a1, b0, b1, z0, z1):
    """An open-backed channel: two flanges and a web, 6 mm plate.  -> V, Q."""
    tt = 0.006
    prof = np.array([(a0, b1), (a0, b0), (a1, b0), (a1, b1)])
    nrm = np.array([(-1.0, 0.0), (-1.0, 0.0), (1.0, 0.0), (1.0, 0.0)])
    nrm[1] = (0.0, -1.0)
    nrm[2] = (0.0, -1.0)
    V, Q = [], []
    zs = np.array([z0, z1])
    for sgn in (+1, -1):
        for z in zs:
            for k in range(4):
                q = prof[k] + nrm[k] * (sgn * tt * 0.5)
                V.append((q[0], q[1], z))
    V = np.array(V)
    # outer 0-7, inner 8-15 (each: z0 ring 0-3, z1 ring 4-7)
    for base, flip in ((0, False), (8, True)):
        for k in range(3):
            f = (base + k, base + k + 1, base + 4 + k + 1, base + 4 + k)
            Q.append(f[::-1] if flip else f)
    for k in range(3):
        Q.append((k, k + 1, 8 + k + 1, 8 + k))              # bottom edge
        Q.append((4 + k + 1, 4 + k, 12 + k, 12 + k + 1))    # top edge
    for (k, fl) in ((0, False), (3, True)):
        f = (k, 4 + k, 12 + k, 8 + k)
        Q.append(f[::-1] if fl else f)
    return V, np.array(Q, np.int64)


def _bolt(o, axis, up, side_v, r, head_h, shank, nut):
    """An M16 button head on `axis`, with a shank, a nut and thread behind.

    `axis` points AT THE TRACK; d = 0 is the head's bearing face, which on a
    W-beam is the track side of the CENTRE RIDGE -- the deepest part of the
    section -- not the traffic face.  `nut` is how far back the nut sits.
    """
    K = 18
    ang = np.linspace(0, 2 * math.pi, K, endpoint=False)
    nb = nut + 0.013
    rings = [(-shank, r * 0.50), (-nb, r * 0.50), (-nb, r * 0.80),
             (-nut, r * 0.80), (-nut, r * 0.52), (-0.0016, r * 0.52),
             (-0.0016, r * 0.86), (0.0, r * 0.99), (head_h * 0.35, r * 0.94),
             (head_h * 0.78, r * 0.72), (head_h, r * 0.36)]
    V = []
    for (d, rr) in rings:
        for a in ang:
            V.append(o + axis * d + up * (math.sin(a) * rr)
                     + side_v * (math.cos(a) * rr))
    V.append(o + axis * (head_h + 0.0016))
    V.append(o - axis * shank)
    V = np.array(V)
    tip, base = len(V) - 2, len(V) - 1
    Q, T = [], []
    for i in range(len(rings) - 1):
        for k in range(K):
            Q.append((i * K + k, i * K + (k + 1) % K,
                      (i + 1) * K + (k + 1) % K, (i + 1) * K + k))
    last = (len(rings) - 1) * K
    for k in range(K):
        T.append((last + k, last + (k + 1) % K, tip))
        T.append((k, (k + 1) % K, base))
    return V, np.array(Q, np.int64), np.array(T, np.int64)


def build_ground(coll, s_c, side, name, s_half=26.0, u_out=24.0):
    """A patch of the runoff platform under the hero, built in (s, u).

    OWNED BY build_barriers -- this is a stand-in so the macro is not shot over
    a void, and it is prefixed accordingly.

    IT IS NOT BUILT BY PROJECTING xy BACK ONTO THE CENTRELINE.  That is what
    ``armco_w_beam.build_ground`` does, and at s = 251 the pit straight and the
    T1 exit run close enough together that ``C.project`` returns the wrong
    station for part of the patch; the ground came out ~0.5 m low, the hero
    post's collar was left standing on a plinth of its own buried skirt, and the
    first composed macro had a 0.77 m slab of daylight under it.  A grid laid
    out in (s, u) and pushed through ``su_to_world`` cannot have that failure,
    because there is nothing to invert.

    The grid is graded: 30 mm cells within 5 m of the hero, coarsening to
    0.45 m at the edge, so the ground beside the collar resolves at the same
    scale the collar does and the far field is not paid for twice.
    """
    def graded(c, half, fine, coarse, r_fine):
        a = [c]
        x = c
        while x < c + half:
            d = abs(x - c)
            st = fine + (coarse - fine) * clamp01((d - r_fine) / max(half - r_fine, 1e-6))
            x += st
            a.append(x)
        x = c
        while x > c - half:
            d = abs(x - c)
            st = fine + (coarse - fine) * clamp01((d - r_fine) / max(half - r_fine, 1e-6))
            x -= st
            a.insert(0, x)
        return np.array(a)

    off = float(C.barrier_offset(np.array([s_c]), side)[0])
    S = graded(s_c, s_half, 0.030, 0.45, 5.0)
    # ACROSS THE TRACK, NOT JUST OUTBOARD.  The macro camera stands outboard
    # and looks through the 98 mm gap between the two rails of a 2-beam run
    # straight at whatever is behind them -- and the first composed macro had a
    # 75 px black band across the whole frame because the ground patch had been
    # clipped at `verge_edge` and there was nothing there.  `ground_z(s, u)` is
    # the contract's datum for |u| <= verge_edge as well (it IS build_surface's
    # mesh to the millimetre), so the patch simply carries on across.
    # The inboard reach is set by the SIGHT LINE, not by tidiness: the camera
    # stands 2.6 m outboard at 0.50 m and looks through a 98 mm gap between two
    # rails, so its ray is within a degree of horizontal and does not meet the
    # ground for tens of metres.  Anything short of ~26 m past the barrier
    # leaves a black band across the frame, which is what the first composed
    # macro had.  The Nishita sky is near-black below the horizon, so a void
    # reads as a hole, not as haze.
    U = graded(off + FACE_T, off + FACE_T + 26.0, 0.030, 0.45, 5.0)
    U = U[U <= off + FACE_T + u_out]
    SS, UU = np.meshgrid(S, U, indexing="ij")
    P = np.asarray(C.su_to_world(SS.ravel(), UU.ravel() * side), float)
    # relief, so the collar's 4 mm rim has something to be 4 mm above
    P[:, 2] += 0.026 * (fbm1(SS.ravel() * 0.55, seed=41, oct=4) - 0.5)
    P[:, 2] += 0.013 * (fbm1(UU.ravel() * 1.30, seed=77, oct=4) - 0.5)
    P[:, 2] += 0.006 * (fbm1((SS.ravel() + UU.ravel()) * 4.4, seed=131, oct=3) - 0.5)
    P[:, 2] += 0.0032 * (fbm1((SS.ravel() - UU.ravel()) * 11.0, seed=17, oct=2) - 0.5)
    ns, nu = len(S), len(U)
    ii, jj = np.meshgrid(np.arange(ns - 1), np.arange(nu - 1), indexing="ij")
    Q = np.stack([ii * nu + jj, (ii + 1) * nu + jj,
                  (ii + 1) * nu + jj + 1, ii * nu + jj + 1], axis=-1).reshape(-1, 4)
    ctr = P.mean(axis=0)
    me = _new_mesh(XPFX + name, P - ctr, Q, None, recalc=False, smooth_deg=None)
    me.materials.append(mat_collar())
    ob = bpy.data.objects.new(XPFX + name, me)
    ob.location = tuple(float(x) for x in ctr)
    coll.objects.link(ob)
    log("ground stand-in '%s': %d x %d cells, s %.1f..%.1f, u %.1f..%.1f"
        % (name, ns, nu, S[0], S[-1], U[0], U[-1]))
    return ob


def build_standins(coll, anchor, near_m=30.0):
    """The spacer block and the post bolt, near the camera only."""
    mat = _standin_mat()
    A = np.asarray(anchor, float) if anchor is not None else None
    n_sp = n_bo = 0
    from mathutils import Matrix
    for side in (+1, -1):
        for r in post_sites(side):
            o = np.array(r["origin"], float)
            if A is not None and np.min(
                    np.linalg.norm(A - (o + np.array([0, 0, 0.5]))[None, :],
                                   axis=1)) > near_m:
                continue
            t = np.array(r["tangent"], float)
            n = np.array(r["normal"], float)
            up = np.array([0.0, 0.0, 1.0])
            M, xs = _world_frame(r)
            hz = r["rail_h"]
            gz = r["post_ground_z"]
            dzb = r["dz_beam"]
            # ONE spacer per post, spanning the rails: the manifest gives
            # armco_spacer_block exactly one instance per post.
            z0 = dzb + hz[0] - 0.020
            z1 = dzb + hz[-1] + 0.312 + 0.020
            V, Q = _box_shell(-r["W"] * 0.55, r["W"] * 0.55,
                              -SPACER_D, 0.0, z0, z1)
            V = np.asarray(V, float).copy()
            V[:, 0] *= xs
            ctr = V.mean(axis=0)
            me = _new_mesh("%sSpacer_%s%05d" % (XPFX, "L" if side > 0 else "R",
                                                n_sp), V - ctr, Q, None)
            me.materials.append(mat)
            ob = bpy.data.objects.new(me.name, me)
            ob.location = tuple(float(x) for x in (o + M @ ctr))
            ob.rotation_mode = "QUATERNION"
            ob.rotation_quaternion = Matrix(
                ((M[0][0], M[0][1], M[0][2]), (M[1][0], M[1][1], M[1][2]),
                 (M[2][0], M[2][1], M[2][2]))).to_quaternion()
            coll.objects.link(ob)
            n_sp += 1
            for bz in r["bolt_z"]:
                # the head bears on the track side of the beam's CENTRE RIDGE,
                # which is SPACER_D in front of the post face plus the 3 mm of
                # sheet, and the nut lands just behind the post's front wall.
                p = o + np.array([0.0, 0.0, bz - gz]) - n * (SPACER_D + 0.003)
                V, Q, T = _bolt(p, -n, up, t, 0.0155, 0.0062,
                                SPACER_D + 0.003 + r["t"] + 0.030,
                                SPACER_D + 0.003 + r["t"] + 0.001)
                ctr = V.mean(axis=0)
                me = _new_mesh("%sBolt_%s%06d" % (XPFX, "L" if side > 0 else "R",
                                                  n_bo), V - ctr, Q, T)
                me.materials.append(mat)
                ob = bpy.data.objects.new(me.name, me)
                ob.location = tuple(float(x) for x in ctr)
                coll.objects.link(ob)
                n_bo += 1
    log("stand-ins: %d spacer blocks, %d post bolts (prefix %s, NOT gated as "
        "this item)" % (n_sp, n_bo, XPFX))
    return n_sp, n_bo


# ==============================================================================
#  8.  THE TEST SCENE
# ==============================================================================

add_camera = W.add_camera


def contract_light(scene=None, coll=None):
    """The film's sun and sky, exactly as world_contract measured them.

    A COPY of ``armco_w_beam.contract_light``, and the copy is the point.  That
    function names its world ``AWB_World`` and its sun ``AWB_Sun``, and
    ``armco_w_beam.purge()`` -- which runs at the top of ``armco_w_beam.build``
    -- deletes every datablock whose name starts with AWB_.  Calling the beam's
    light helper and then the beam's builder therefore deletes the light and
    the world, and the acceptance render comes back BLACK: mean 0.00032, two
    distinct luminance levels across 2,073,600 pixels.  That is exactly what
    the first macro of this item was.

    A light named with another module's prefix is a light that module can
    delete.  This one is named with ours.
    """
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
    log("light: sun %.3f W/m2 elev %.2f deg bearing %.2f deg; AgX %.3f EV"
        % (C.SUN_ENERGY, C.SUN_ELEV_DEG, C.SUN_BEARING_DEG,
           C.REFERENCE_EXPOSURE_EXTERIOR))
    return ob


def hero_aim(sides=(-1, +1), exclude=(), min_sep_m=40.0, want_bend=True,
             min_bend=0.0, relax=False):
    """Where the macro camera looks, and from where.  Chosen by SCORE.

    Four things decide it and none of them is taste:

      1. THE POST MUST BE LIT ON THE FACE THE CAMERA SEES.  The camera is
         outboard (behind the barrier) for the hero shot, because that is the
         only vantage from which a post is not 80 % hidden by the rail it holds,
         and the film does go there -- the helicopter arc over the infield bowl
         and the whip-and-catch both look across the barrier line.  58 deg of
         incidence on the post's outboard face: still lit, and every rolled
         corner, rib, lip and buckle throws a shadow.
      2. IT MUST HAVE A HISTORY.  A pristine post is a rendering of a catalogue.
         The score wants an impact hinge in frame.
      3. IT MUST BE SOMEWHERE THE FILM GOES -- inside one of build_barriers'
         eight hero windows, weighted by the window's own tier.
      4. ITS NEIGHBOURS MUST DIFFER FROM IT.  The named failure is "one tree
         spammed 100 times", so the macro is deliberately aimed where the next
         three posts along are a different family, a different length and a
         different lean.  If the item is repetitive, this frame proves it.
    """
    sun = np.array(C.SUN_DIR, float)
    sh = sun[:2] / np.linalg.norm(sun[:2])
    cos_e = math.cos(math.radians(C.SUN_ELEV_DEG))
    cand = []
    for side in sides:
        recs = post_sites(side)
        for i, r in enumerate(recs):
            wins = W.hero_windows_at(r["s"], side)
            if not wins and not relax:
                continue
            # NOT AT A RUN END, and not a run-end anchor.  A macro shot at the
            # last post of a run is half a frame of guardrail and half a frame
            # of empty runoff, and the anchors are 3.4 % of the population.
            # The first composed macro was exactly that.
            if r["kind"] != "line":
                continue
            nb4 = recs[max(0, i - 4):i + 5]
            if len(nb4) < 9 or any(x["kind"] != "line" for x in nb4):
                continue
            if max(abs(np.diff([x["arc"] for x in nb4]))) > 3.2:
                continue
            if r["bend_ang"] < min_bend:
                continue
            n = np.array(r["normal"], float)
            face = n[:2] / np.linalg.norm(n[:2])       # the OUTBOARD face
            inc = math.degrees(math.acos(
                float(np.clip(np.dot(face, sh) * cos_e, -1.0, 1.0))))
            # AND THE RAIL BEHIND IT MUST BE GALVANISED, NOT PAINTED.
            # `armco_w_beam` paints 30 % of maintenance runs in one of
            # build_dressing's nine invented liveries.  A macro of a galvanised
            # post shot against a silver-enamelled rail fills 80 % of the frame
            # with flat paint and gives the eye nothing to compare this item's
            # zinc against -- the first composed macro was exactly that.  It is
            # a hard filter and not a score term, because as a score term it
            # lost to a 12-point "2-beam run" bonus the first time it was tried.
            if float(W.run_paint(np.array([r["run"]]))[0][0]) > 0.5 and not relax:
                continue
            # and it must be LIT, not back-lit.  Past 92 deg the outboard face
            # is in its own shadow and the object is a silhouette; the second
            # hero came back at 104.3 deg the first time the bend requirement
            # was made mandatory, because nothing else was left.
            if inc > 92.0:
                continue
            nb = recs[i + 1:i + 4]
            variety = len({x["fam"] for x in nb} | {r["fam"]}) \
                + len({round(x["stock"], 3) for x in nb} | {round(r["stock"], 3)})
            # LIGHT FIRST.  The first version let a 45-point damage bonus
            # buy an 18 deg lighting error, and picked a post at 79.9 deg of
            # incidence: a face lit at cos(79.9) = 0.17 of normal, which on
            # metal with a dark foreground renders as a charcoal bar.  A hinge
            # you cannot see is worth nothing, so the lighting term is now
            # heavy enough that no other term can outbid it.
            score = (-abs(inc - 58.0) * 2.60
                     + (26.0 * r["crush"] if want_bend else 0.0)
                     + (16.0 if r["bend_ang"] > 0.08 else 0.0)
                     + 5.0 * variety
                     + 4.0 * (max(w[4] for w in wins) if wins else 0.0)
                     + (12.0 if r["nrail"] == 2 else 0.0)
                     # and a MODAL section: the two sigma families are 47 % of
                     # the population and a macro of the 7 % RHS is a claim
                     # about 223 posts rather than about 1,548.
                     + (9.0 if r["fam"].startswith("SIGMA") else 0.0))
            cand.append((score, side, i, r, inc,
                         wins[0][0] if wins else "(outside a hero window)"))
    cand.sort(key=lambda c: -c[0])
    for c in cand:
        _sc, side, i, r, inc, win = c
        if any(abs(r["s"] - e) < min_sep_m and side == es for (e, es) in exclude):
            continue
        return dict(rec=r, index=i, side=side, sun_incidence_deg=inc,
                    window=win, score=_sc)
    raise RuntimeError("no hero post found")


def macro_rig(aim, cams, name, out=True, yaw_deg=12.0, elev_deg=3.0,
              aim_h=0.50):
    """Place a camera at EXACTLY `nearest_camera_m` on `lens_at_closest_mm`.

    2.600 m is the NEAREST the lens ever gets, so the camera sits on the
    perpendicular through the aim point at exactly 2.600 m and is then ROTATED,
    not moved, to look along the barrier.  Moving it to get the angle would
    bring the nearer posts inside 2.600 m.

    THE YAW IS SMALL, AND THAT IS THE WHOLE COMPOSITION.  Rotating the camera
    by `yaw_deg` slides the subject toward the frame edge by
    tan(yaw) / tan(hfov/2); on a 35 mm lens the half-FOV is 27.7 deg, so 24 deg
    of yaw puts the hero post 85 % of the way to the edge and fills the frame
    with the RAIL instead.  That is what the first macro of this item was: a
    2.7 m wide picture of somebody else's guardrail with two thin dark bars in
    it.  12 deg puts the post 47 % out -- off centre enough to be a photograph,
    close enough that the object being judged is the object in the middle.
    """
    r = aim["rec"]
    o = np.array(r["origin"], float)
    t = np.array(r["tangent"], float)
    n = np.array(r["normal"], float)
    surf = o + n * (r["D"] * 0.5) + np.array([0.0, 0.0, aim_h])
    el = math.radians(elev_deg)
    dirn = (n if out else -n)
    off = dirn * math.cos(el) + np.array([0.0, 0.0, 1.0]) * math.sin(el)
    off = off / np.linalg.norm(off)
    cam_p = surf + off * FILMED_AT_M
    look = surf + t * (FILMED_AT_M * math.tan(math.radians(yaw_deg)))
    cam = add_camera(name, tuple(cam_p), tuple(look), LENS_MM, cams)
    d = float(np.linalg.norm(cam_p - surf))
    log("%s: %.4f m from the post on a %.1f mm lens (manifest %.1f m / %.0f mm)"
        % (name, d, LENS_MM, FILMED_AT_M, LENS_MM))
    log("   s=%.1f side %+d window '%s' family %s stock %.3f m stand %.3f m"
        % (r["s"], r["side"], aim["window"], r["fam"], r["stock"], r["stand"]))
    log("   sun incidence on the outboard face %.1f deg; hinge %.1f deg at "
        "%.3f m; lean %.1f mrad; settle %.0f mm"
        % (aim["sun_incidence_deg"], math.degrees(r["bend_ang"]), r["bend_z"],
           1000.0 * math.hypot(r["lean_a"], r["lean_b"]), 1000.0 * r["settle"]))
    fh = d * 20.25 / LENS_MM
    log("   frame %.3f x %.3f m; the %.3f m post reads %.0f px of 2160 "
        "(manifest %.0f)" % (d * 36.0 / LENS_MM, fh, r["stock"],
                             r["stock"] / fh * 2160.0, ONSCREEN_PX_4K))
    return cam, cam_p, surf


def test_scene(sides=(+1, -1), samples=256, limit=None, beam=True):
    """Build the item, light it with the contract sun, and put the manifest's
    own camera on it: 2.600 m away on a 35 mm lens."""
    scene = bpy.context.scene
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)

    # TWO hero sites, not one.  A macro of the one post that happens to be
    # prettiest is a claim about one post; this item has 3 304 of them.
    aimA = hero_aim()
    # B IS THE DAMAGED ONE, BY REQUIREMENT.  With the lighting term weighted
    # heavily enough to be decisive, the best-lit post on the circuit is a
    # pristine one -- so the second macro asks for a real plastic hinge and
    # takes the best-lit post that has one.  A hero pair of "typical" and
    # "hit" says more about 3,304 objects than two of either.
    # RELAXED for B: only 95 of the 3,304 posts carry a plastic hinge, and
    # requiring one AND a hero window AND a galvanised run AND front lighting
    # leaves the empty set.  B drops the window and the paint requirement --
    # it is the DAMAGE frame, and a bent post 40 m outside a camera window is
    # still this item's geometry.
    aimB = hero_aim(exclude=[(aimA["rec"]["s"], aimA["side"])], min_sep_m=150.0,
                    min_bend=0.05, relax=True)

    anchor = []
    for a in (aimA, aimB):
        r = a["rec"]
        o = np.array(r["origin"], float)
        n = np.array(r["normal"], float)
        surf = o + n * (r["D"] * 0.5) + np.array([0.0, 0.0, 0.48])
        el = math.radians(7.0)
        for dirn in (n, -n):
            od = dirn * math.cos(el) + np.array([0.0, 0.0, 1.0]) * math.sin(el)
            anchor.append(tuple(surf + od / np.linalg.norm(od) * FILMED_AT_M))
        anchor.append(tuple(surf))

    root = build(sides=sides, lod_anchor=anchor, limit=limit, scene=scene)
    cams = _coll(COLL + "/Cameras", root)
    stand = _coll(COLL + "/Standins", root)

    # ---- CONTEXT, all of it owned by OTHER items and prefixed accordingly ----
    # THIS RUNS BEFORE THE LIGHT AND BEFORE THE GROUND.  See contract_light's
    # docstring and the ordering note below: armco_w_beam.build purges by name
    # prefix and takes the ground patches and, if it is called after it, the sky
    # and the sun with them.
    if beam:
        wins = {}
        for a in (aimA, aimB):
            wins.setdefault(a["side"], []).append(a["rec"]["s"])
        W.build(sides=tuple(wins.keys()), lod_anchor=anchor,
                windows={side: (min(ss) - 34.0, max(ss) + 34.0)
                         for side, ss in wins.items()})
        # armco_w_beam.build takes ONE window per side, so when both heroes
        # land on the same side of the circuit that window is the span BETWEEN
        # them -- 1,561 m and 324 bays of rail nobody is going to photograph,
        # which took the test blend from 160 MB to a quarter of a gigabyte.
        # Keep only the bays that are actually near a camera.
        A = np.asarray(anchor, float)
        # `ob.location`, not `ob.matrix_world`: the matrix is derived and is
        # still identity until the depsgraph is evaluated, so measuring
        # distances with it drops every bay in the scene.
        drop = [ob for ob in list(bpy.data.objects)
                if ob.name.startswith("AWB_Bay_")
                and float(np.min(np.linalg.norm(
                    A - np.array(ob.location, float)[None, :],
                    axis=1))) > 46.0]
        for ob in drop:
            bpy.data.objects.remove(ob, do_unlink=True)
        nb = sum(1 for ob in bpy.data.objects if ob.name.startswith("AWB_Bay_"))
        log("context: %d real armco_w_beam bays kept near the two hero "
            "stations (%d distant bays dropped)" % (nb, len(drop)))
        for (a, half, nm) in ((aimA, 26.0, "GroundA"), (aimB, 22.0, "GroundB")):
            build_ground(stand, a["rec"]["s"], a["side"], nm, s_half=half)
        build_standins(stand, anchor, near_m=30.0)

    contract_light(scene, coll=root)

    macro, cam_p, surf = macro_rig(aimA, cams, PFX + "CAM_MACRO", out=True)
    macroB, _cb, _sb = macro_rig(aimB, cams, PFX + "CAM_MACRO_B", out=True,
                                 yaw_deg=-16.0, elev_deg=1.0)
    # the track-side read: what the film mostly sees of a post, through the gaps
    macroC, _cc, _sc = macro_rig(aimA, cams, PFX + "CAM_MACRO_TRACK", out=False,
                                 yaw_deg=20.0, elev_deg=2.0, aim_h=0.34)

    r = aimA["rec"]
    o = np.array(r["origin"], float)
    t = np.array(r["tangent"], float)
    n = np.array(r["normal"], float)
    # the driven head, from above and outboard: burr, mushroom, bare steel
    add_camera(PFX + "CAM_HEAD",
               tuple(o + n * 0.44 + t * 0.24 + np.array([0.0, 0.0, r["stand"] + 0.34])),
               tuple(o + np.array([0.0, 0.0, r["stand"] - 0.03])), 70.0, cams)
    # THE COLLAR, FROM THE TRACK SIDE.  At a 12.5 deg sun a 1.012 m barrier
    # lays a 4.6 m shadow across the ground OUTBOARD of it, so the outboard
    # collar is in shadow every hour of the day this film is set in; the first
    # collar frame was 1920 x 1080 of denoised sky-lit mud.  The track side of
    # the same post is lit, and it is also the side the film actually watches
    # from -- the doppler hover and the T4 kerb-height station are both inboard.
    add_camera(PFX + "CAM_COLLAR",
               tuple(o - n * 1.05 + t * 0.55 + np.array([0.0, 0.0, 0.56])),
               tuple(o - n * 0.04 + np.array([0.0, 0.0, 0.055])), 50.0, cams)
    # dead square on the section, from outboard: the profile check
    add_camera(PFX + "CAM_SECTION",
               tuple(o + n * (r["D"] + 0.70) + np.array([0.0, 0.0, 0.55])),
               tuple(o + n * (r["D"] * 0.5) + np.array([0.0, 0.0, 0.55])), 65.0, cams)
    # straight down the post line: the read that catches a repeated mesh
    add_camera(PFX + "CAM_ALONG",
               tuple(o - t * 7.0 + n * 1.05 + np.array([0.0, 0.0, 1.15])),
               tuple(o + t * 13.0 + np.array([0.0, 0.0, 0.45])), 85.0, cams)
    # the bolt slot, square on the front face from the track side
    add_camera(PFX + "CAM_SLOT",
               tuple(o - n * 0.42 + np.array([0.0, 0.0, r["bolt_z"][-1]
                                              - r["post_ground_z"]])),
               tuple(o + np.array([0.0, 0.0, r["bolt_z"][-1] - r["post_ground_z"]])),
               85.0, cams)
    # a wide, so the run can be judged in its setting
    add_camera(PFX + "CAM_WIDE",
               tuple(o + n * 8.0 + t * 3.0 + np.array([0.0, 0.0, 2.1])),
               tuple(o + t * 4.0 + np.array([0.0, 0.0, 0.5])), 40.0, cams)

    # THE MACRO MUST NOT BE SHOT OVER A VOID.  Counted, not assumed: the ground
    # patches are made by another module's helper and another module's purge can
    # take them away again (see the ordering note above).
    ng = sum(1 for o in bpy.data.objects if o.name.startswith(XPFX) or
             o.name.startswith("AWBSTAND_"))
    nb = sum(1 for o in bpy.data.objects if o.name.startswith("AWB_"))
    np_ = sum(1 for o in bpy.data.objects if o.name.startswith(PFX)
              and o.type == "MESH")
    log("scene: %d posts (AP_), %d beam bays (AWB_), %d context objects "
        "(ground + stand-ins)" % (np_, nb, ng))
    if beam and ng < 2:
        raise RuntimeError("the ground patches are gone -- the macro would be "
                           "shot over a void")
    nsun = sum(1 for o in bpy.data.objects if o.type == "LIGHT")
    if scene.world is None or nsun < 1:
        raise RuntimeError("no world (%s) or no light (%d) -- the macro would "
                           "come back BLACK" % (scene.world, nsun))

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
#  9.  MEASUREMENT
# ==============================================================================

def selftest():
    """Measure the things the gate cannot: the section, the population, the
    pitch, the variation, and whether the post is where the beam thinks it is."""
    ok = True
    print("=" * 78)
    print("armco_post selftest   (px_per_m %.1f at %.1f m / %.0f mm)"
          % (PX_PER_M, FILMED_AT_M, LENS_MM))
    print("=" * 78)

    # --- 1. the sections -----------------------------------------------------
    print("\n1. SECTIONS")
    for fam in SECTIONS:
        for lod in range(4):
            pr = section_profile(fam, lod)
        pr = section_profile(fam, 0)
        seg = np.linalg.norm(np.diff(pr["mid"], axis=0), axis=1)
        j0, j1 = pr["front"]
        fw = abs(pr["mid"][j1, 0] - pr["mid"][j0, 0])
        edge = (SECTIONS[fam]["W"] - POST_SLOT[0]) * 0.5
        print("   %-10s %-50s %3d pts  flat %4.1f mm  edge dist %4.1f mm  "
              "min seg %4.2f mm = %4.1f px"
              % (fam, SECTIONS[fam]["desc"], len(pr["mid"]), fw * 1000,
                 edge * 1000, seg.min() * 1000, seg.min() * PX_PER_M))
        if fw < POST_SLOT[0] + 0.008 or edge < 0.014:
            print("      ** front face too narrow for the %.0f mm slot"
                  % (POST_SLOT[0] * 1000))
            ok = False

    # --- 2. the population ---------------------------------------------------
    print("\n2. POPULATION")
    tot = 0
    pitches = []
    fams = {}
    stands, stocks, leans, settles = [], [], [], []
    bent = 0
    for side in (+1, -1):
        recs = post_sites(side)
        tot += len(recs)
        arcs = sorted(r["arc"] for r in recs)
        d = np.diff(np.array(arcs))
        pitches += [x for x in d if 0.2 < x < 6.0]
        for r in recs:
            fams[r["fam"]] = fams.get(r["fam"], 0) + 1
            stands.append(r["stand"])
            stocks.append(r["stock"])
            leans.append(math.hypot(r["lean_a"], r["lean_b"]))
            settles.append(r["settle"])
            bent += 1 if r["bend_ang"] > 1e-6 else 0
        kinds = {}
        for r in recs:
            kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
        print("   side %+d: %4d posts  %s" % (side, len(recs), kinds))
    print("   TOTAL %d against the manifest's %d  (%+.1f %%)"
          % (tot, INSTANCES_DECLARED, 100.0 * (tot - INSTANCES_DECLARED)
             / INSTANCES_DECLARED))
    P = np.array(pitches)
    print("   post pitch: median %.3f m, p10 %.3f, p90 %.3f  "
          "(2.00 m nominal, 1.33 m on tight radii)"
          % (np.median(P), np.percentile(P, 10), np.percentile(P, 90)))
    print("   families: " + ", ".join("%s=%d (%.0f%%)" % (k, v, 100.0 * v / tot)
                                      for k, v in sorted(fams.items())))
    st = np.array(stands)
    print("   standing height: mean %.4f m sd %.4f m  min %.3f max %.3f"
          % (st.mean(), st.std(), st.min(), st.max()))
    print("   stock length:    mean %.3f m  modal %.3f m  (manifest typical %.1f)"
          % (np.mean(stocks), max(set(stocks), key=stocks.count), TYPICAL_LEN_M))
    print("   lean:            mean %.2f mrad  p95 %.2f mrad  max %.2f mrad"
          % (1000 * np.mean(leans), 1000 * np.percentile(leans, 95),
             1000 * np.max(leans)))
    print("   settlement:      mean %.1f mm  max %.1f mm  (manifest -57 mm)"
          % (1000 * np.mean(settles), 1000 * np.max(settles)))
    print("   impact hinges:   %d posts (%.1f %%)" % (bent, 100.0 * bent / tot))
    if st.std() < 0.004:
        print("   ** standing heights are too uniform")
        ok = False

    # --- 3. agreement with the beam ------------------------------------------
    print("\n3. AGREEMENT WITH armco_w_beam")
    worst = 0.0
    for side in (+1, -1):
        bs = {(round(p["arc"], 4)) for p in W.post_sites(side)}
        for r in post_sites(side):
            if r["kind"] != "line":
                continue
            if round(r["arc"], 4) not in bs:
                print("   ** post at arc %.4f is not a beam lap centre" % r["arc"])
                ok = False
                break
            o = np.array(r["origin"], float)
            b = np.array(r["world"], float)
            n = np.array(r["normal"], float)
            depth = float(np.dot(o - b, n))
            worst = max(worst, abs(depth - FACE_T - r["wander_b"]))
    print("   every 'line' post is a beam lap centre; worst depth error "
          "%.3f mm (front face at %.3f m outboard of the traffic face)"
          % (worst * 1000, FACE_T))
    if worst > 1e-6:
        ok = False

    # --- 3b. the local frame is RIGHT-HANDED ----------------------------------
    print("\n3b. THE LOCAL -> WORLD FRAME")
    # `Matrix.to_quaternion()` accepts a reflection and returns the quaternion
    # of some unrelated rotation, so a det = -1 basis does not raise, it just
    # stands the object up wrong.  Every post on the right of travel was built
    # that way until this check existed.  Measured on every record, both sides.
    dets_raw, dets_fixed = [], []
    for side in (+1, -1):
        for r in post_sites(side):
            tg = np.array(r["tangent"], float)
            nm = np.array(r["normal"], float)
            up = np.array([0.0, 0.0, 1.0])
            dets_raw.append(float(np.linalg.det(np.stack([tg, nm, up], axis=1))))
            M, _xs = _world_frame(r)
            dets_fixed.append(float(np.linalg.det(M)))
    dr = np.array(dets_raw)
    df = np.array(dets_fixed)
    print("   naive [tangent, normal, up]: %d of %d records are LEFT-handed "
          "(det = -1) -- every one of them is a post on the right of travel"
          % (int((dr < 0).sum()), len(dr)))
    print("   `_world_frame`:              det min %.6f max %.6f; "
          "%d left-handed" % (df.min(), df.max(), int((df < 0).sum())))
    if (df < 0).any() or abs(df - 1.0).max() > 1e-9:
        print("   ** a post would be stood up in an arbitrary orientation")
        ok = False

    # --- 4. embedment and the ground ------------------------------------------
    print("\n4. GROUND AND EMBEDMENT")
    emb = []
    dz = []
    for side in (+1, -1):
        for r in post_sites(side):
            emb.append(r["embed"])
            dz.append(r["post_ground_z"] - r["ground_z"])
    emb = np.array(emb)
    dz = np.array(dz)
    print("   embedment: min %.3f m  median %.3f m  max %.3f m  "
          "(BASE_EMBED_M = %.3f)" % (emb.min(), np.median(emb), emb.max(),
                                     BASE_EMBED_M))
    print("   post ground vs the beam's barrier-line datum: median %+.1f mm, "
          "p05 %+.1f, p95 %+.1f  (build_barriers' vertical erection jitter, "
          "which the standing height is corrected for)"
          % (1000 * np.median(dz), 1000 * np.percentile(dz, 5),
             1000 * np.percentile(dz, 95)))
    if emb.min() < BASE_EMBED_M:
        print("   ** a post does not embed")
        ok = False

    # --- 5. mesh resolution at the filmed distance ---------------------------
    print("\n5. MESH RESOLUTION AT %.3f m" % FILMED_AT_M)
    recs = post_sites(-1)
    sample = [recs[i] for i in range(0, len(recs), max(1, len(recs) // 40))][:40]
    for lod in (0, 1, 2, 3):
        L = []
        nf = 0
        for r in sample[:8]:
            rr = dict(r)
            rr["lod"] = lod
            V, Q, T, A = build_post_mesh(rr, lod)
            nf += len(Q) * 2 + len(T)
            for F in (Q, T):
                if not len(F):
                    continue
                for k in range(F.shape[1]):
                    a = V[F[:, k]]
                    b = V[F[:, (k + 1) % F.shape[1]]]
                    L.append(np.linalg.norm(a - b, axis=1))
        L = np.concatenate(L)
        print("   LOD%d: %6.0f tris/post   edge p10 %6.3f mm = %5.2f px   "
              "median %6.2f mm = %6.1f px"
              % (lod, nf / 8.0, 1000 * np.percentile(L, 10),
                 PX_PER_M * np.percentile(L, 10), 1000 * np.median(L),
                 PX_PER_M * np.median(L)))

    # --- 5b. the collar against the ground it stands on -----------------------
    print("\n5b. THE COLLAR AGAINST THE GROUND DATUM")
    # THE ONE WAY THIS ITEM COULD Z-FIGHT.  The collar is the only part of it
    # that lies nearly parallel to build_barriers' runoff platform, so its rim
    # height above the TRUE datum at the rim's own (s, u) -- not at the post's
    # -- is the number that decides whether there is a coplanar pair, a lit gap
    # under the rim, or a buried edge.  The design intent is "a few mm proud,
    # never coplanar, and buried rather than floating where the platform falls
    # away".  Measured, not asserted.
    dz_rim = []
    floats = 0
    for side in (+1, -1):
        recs = post_sites(side)
        smp = recs[::max(1, len(recs) // 120)]
        for r in smp:
            pr = section_profile(r["fam"], 2)
            ang = np.linspace(0.0, 2 * math.pi, 16, endpoint=False)
            rj = fbm1(ang * 2.4 + h01(r["seed"], 31) * 20.0,
                      seed=r["seed"] % 997, oct=3)
            r_out = r["collar_r"] * (0.74 + 0.52 * rj)
            ext = pr["mid"] + pr["nrm"] * (pr["t"] * 0.5)
            cx = float(0.5 * (ext[:, 0].min() + ext[:, 0].max()))
            cy = float(0.5 * (ext[:, 1].min() + ext[:, 1].max()))
            lx = cx + r_out * np.cos(ang)
            ly = cy + r_out * np.sin(ang)
            off = C.barrier_offset(np.array([r["s"]]), side)[0]
            zg = C.ground_z(r["s"] + lx,
                            (off + FACE_T + r["wander_b"] + ly) * side)
            gsx, gsy = r["g_slope"]
            rim = r["post_ground_z"] + COLLAR_RIM + gsx * lx + gsy * ly
            d = rim - np.asarray(zg, float)
            dz_rim.append(d)
            if d.max() > COLLAR_SKIRT:
                floats += 1
    D = np.concatenate(dz_rim)
    print("   rim minus true ground: p05 %+.1f mm  median %+.1f mm  p95 %+.1f mm"
          % (1000 * np.percentile(D, 5), 1000 * np.median(D),
             1000 * np.percentile(D, 95)))
    print("   |rim - ground| < 0.5 mm on %.2f %% of the sampled rim "
          "(a coplanar pair would z-fight; %d mm of skirt is buried below it)"
          % (100.0 * np.mean(np.abs(D) < 0.0005), int(COLLAR_SKIRT * 1000)))
    print("   %d of %d sampled posts have any rim point more than the %.0f mm "
          "skirt above ground" % (floats, sum(len(x) // 16 for x in [D]),
                                  COLLAR_SKIRT * 1000))
    if np.mean(np.abs(D) < 0.0005) > 0.02:
        print("   ** too much of the rim is coplanar with the platform")
        ok = False

    # --- 6. is any post the same as any other? --------------------------------
    print("\n6. REPETITION")
    keys = set()
    dup = 0
    for side in (+1, -1):
        for r in post_sites(side):
            k = (r["fam"], round(r["stock"], 4), round(r["stand"], 5),
                 round(r["lean_a"], 6), round(r["lean_b"], 6),
                 round(r["twist"], 6), round(r["bend_ang"], 6),
                 round(r["bend_z"], 5), round(r["collar_r"], 5),
                 round(r["collar_heave"], 6), round(r["mush"], 6))
            if k in keys:
                dup += 1
            keys.add(k)
    print("   %d distinct post specifications over %d posts; %d exact duplicates"
          % (len(keys), tot, dup))
    if dup:
        print("   ** two posts would mesh identically")
        ok = False

    print("\n%s" % ("SELFTEST PASSED" if ok else "SELFTEST FAILED"))
    return ok


def write_interface(path=None):
    """The machine-readable contract for the three dependants."""
    path = path or os.path.join(_HERE, "armco_post_interface.json")
    d = dict(item=ITEM, version=__version__, generated="2026-07-29",
             collection=COLL, prefix=PFX,
             constants=dict(
                 FACE_T=FACE_T, SPACER_D=SPACER_D, SEC_D=SEC_D,
                 ARMCO_TOP=ARMCO_TOP, RAIL_HZ3=RAIL_HZ3, RAIL_HZ2=RAIL_HZ2,
                 RAIL_BOLT_V=RAIL_BOLT_V, STAND_NOM=STAND_NOM,
                 POST_SLOT=list(POST_SLOT), TAG_HOLE_D=TAG_HOLE_D,
                 CONDUIT_Z=CONDUIT_Z, BASE_EMBED_M=BASE_EMBED_M,
                 STOCK_L=STOCK_L, SETTLE_MAX=SETTLE_MAX,
                 WANDER_ALONG=WANDER_ALONG, WANDER_DEPTH=WANDER_DEPTH),
             sections={k: dict(v) for k, v in SECTIONS.items()},
             note=("post_sites(side) is the authority for WHAT a post is; "
                   "armco_w_beam.post_sites(side) is the authority for WHERE "
                   "the line posts stand.  spacer_sites() and "
                   "conduit_clip_sites() return world frames already."),
             counts={}, posts={})
    for side in (+1, -1):
        recs = post_sites(side)
        d["counts"]["side_%+d" % side] = len(recs)
        d["posts"]["side_%+d" % side] = [
            {k: (list(v) if isinstance(v, tuple) else v)
             for k, v in r.items() if k not in ("panel",)}
            for r in recs]
    d["counts"]["total"] = sum(v for k, v in d["counts"].items()
                               if k.startswith("side_"))

    def _plain(o):
        if isinstance(o, (np.bool_,)):
            return bool(o)
        if isinstance(o, np.integer):
            return int(o)
        if isinstance(o, np.floating):
            return float(o)
        if isinstance(o, np.ndarray):
            return o.tolist()
        raise TypeError(type(o).__name__)

    with open(path, "w") as f:
        json.dump(d, f, indent=1, default=_plain)
    log("interface -> %s (%.1f MB)" % (path, os.path.getsize(path) / 1e6))
    return path


# ==============================================================================
# 10.  MAIN
# ==============================================================================

def main():
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    elif not HAVE_BPY:
        argv = argv[1:]                 # run as a bare python script
    else:
        argv = []
    p = argparse.ArgumentParser()
    p.add_argument("--test", action="store_true")
    p.add_argument("--selftest", action="store_true")
    p.add_argument("--interface", action="store_true")
    p.add_argument("--save", default=None)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--samples", type=int, default=256)
    p.add_argument("--no-beam", action="store_true")
    a = p.parse_args(argv)

    if a.selftest:
        ok = selftest()
        if a.interface:
            write_interface()
        sys.exit(0 if ok else 1)
    if a.interface and not a.test:
        write_interface()
        return
    if a.test:
        if not HAVE_BPY:
            raise SystemExit("--test needs Blender")
        test_scene(samples=a.samples, limit=a.limit, beam=not a.no_beam)
        if a.interface:
            write_interface()
        if a.save:
            bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.save))
            log("saved %s" % a.save)
        return
    p.print_help()


if __name__ == "__main__":
    main()
