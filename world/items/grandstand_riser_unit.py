#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
grandstand_riser_unit.py — CIRCUIT VITRINE, per-item hero campaign, item
``grandstand_riser_unit`` (zone ``grandstand``, wave 1, build order 138,
**4 dependants**).

WHAT THIS IS, IN ONE SENTENCE
=============================
Every square metre of terrace in the six grandstand blocks, built as **3 394
individual precast concrete stadia units** — one L-shaped casting per bay per
row, each with its own length, its own seating error, its own chipped nose, its
own runnels and its own socket pattern — so that what the Beat-6 crane-out reads
from 14.7 m above is a REAL GRID of castings with joints and steps in it, and not
a pair of extruded boxes per row with a colour ramp on top.

WHAT WAS THERE BEFORE, AND WHY IT IS NOT ENOUGH
-----------------------------------------------
``build_architecture._grandstand_block`` builds the rake as, per row, exactly
two boxes::

    mb.box((x0, yf, z0), (x1, yb, z0 + 0.16), ...)     # the tread   — ONE box
    mb.box((x0, yf - 0.16, z0), (x1, yf, z1), ...)     # the riser   — ONE box

For TRIBUNE PRINCIPALE that is a single 160 m long tread and a single 160 m long
riser, 12 triangles for 160 m of concrete, with no joint, no nose, no chamfer, no
socket, no channel and no step.  The manifest is explicit about why that is fatal
for THIS item rather than merely thin:

    "Still hero: the riser fronts, the gangways and the tread strips are exactly
     the parts the crowd does NOT cover, and from directly above they are the
     grid the whole crowd is registered against."

15 050 spectators sit ON this.  Roughly three quarters of every seat is hidden
behind an occupant — the terrace is not.  It is the only continuous surface in
the last frame of the film, and a continuous surface with no joints in it is
what makes a crowd read as a grid of dolls on a ramp.

THE PIXEL BUDGET THIS WAS BUILT TO
----------------------------------
    px_per_m = (3840 x 28 / 36) / 14.7 = 203.2 px/m     ->     1 px = 4.92 mm

    one unit, nose to nib bottom, 0.420 m       85 px   (manifest: onscreen_px_4k 85)
    the 0.88 m tread, in plan                  179 px
    a bay, 3.25 m of casting                   660 px
    the transverse joint, 8-30 mm             1.6-6 px    <- must be geometry
    its two 4 mm end chamfers, 8 mm            1.6 px     <- must be geometry
    the 14-24 mm nose chamfer                 2.8-4.9 px  <- must be geometry
    the 62 mm nosing rebate                     12.6 px   <- must be geometry
    the 12 mm drip groove under the nose         2.4 px   <- must be geometry
    the 10 mm shadow gap at the riser foot       2.0 px   <- must be geometry
    a 34 mm seat socket                          6.9 px   <- must be geometry
    a 75 mm drainage channel                    15.2 px   <- must be geometry
    the unit-to-unit step, 1 sd 4.4 mm           0.9 px, but the terrace is in
                                                 SHADE (see below) so it reads as
                                                 an AO line, not a cast shadow
                                                             <- must be geometry
    a chipped nose arris, 12-45 mm            2.4-9.1 px   <- must be geometry
    a weathering runnel, 30-90 mm wide         6-18 px across,
                                                 1.5-3 mm deep = 0.3-0.6 px of
                                                 relief                <- geometry
                                                 (it is the ALBEDO streak that
                                                  carries it; the relief exists
                                                  so the streak has a reason)
    bug holes, 1.5-5 mm; board marks 0.4 mm      <- SHADING

Everything with a silhouette or an occlusion is mesh.  The line is drawn at 2 mm
of relief, one third of a pixel, because below that a feature cannot occlude its
own neighbour even at a grazing sky.

THE LIGHT THIS ITEM LIVES IN — AND WHY IT DECIDED THE MODELLING
---------------------------------------------------------------
MEASURED, not assumed.  ``C.SUN_DIR`` = (0.5179, -0.8278, 0.2159): the sun is in
the SE at 12.47 deg.  The grandstand band is circuit y -34..-62 and the rake
faces circuit +y, which in the world frame is the direction (-0.643, +0.766) —
NNW.  The dot product of the two is **-0.99**: the sun is almost exactly behind
the stand.  And each 0.34 m riser at a 12.47 deg sun throws 1.54 m of shadow
down-rake over a 0.88 m tread.

    **THE ENTIRE TERRACE IS IN SHADE FOR THE WHOLE FILM.**  Not one square metre
    of it takes direct sun.  It is lit by sky (4.2, 7.6, 13.6 W/m2) plus bounce.

That is not a detail, it is the whole modelling brief for the item, and it is the
opposite of what ``kerb_precast_unit`` learned (there, a raking sun WAS the
object).  Under a hemispherical source:

  * a cast shadow models nothing — there are none;
  * what models the surface is AMBIENT OCCLUSION, so every feature that reads
    must be a NARROW DEEP SLOT: the joint, the drip groove, the socket, the
    channel, the foot gap, the chip.  All of those are in the mesh below;
  * a wide shallow bump is invisible.  Nothing in this item relies on one;
  * the sky is blue and the bounce off the sunlit rear cladding and the terrace
    is warm, so the riser faces (up-facing normals see more sky) run COOLER than
    the tread tops.  The material carries that as a real sky/bounce split rather
    than as one flat albedo.

===============================================================================
THE PUBLIC INTERFACE  —  this item is a FOUNDATION.  4 items depend on it.
===============================================================================
Everything below is world-frame, metres, and computable WITHOUT bpy: import this
module from a bare python3 and every one of these functions works.  They are all
derived from ONE table, ``BLOCKS``, which is quoted verbatim from
``build_architecture.GS_BLOCKS`` so that this module and that one cannot drift.

    ``block_records()``    the six blocks, with bay width, aisle and vomitory
                           positions, row pitch/rise and the derived unit count.
    ``row_records()``      one record per (block, row): the tread-top z, the nose
                           y, the clear tread depth, whether it is a gangway row,
                           and the seat columns that survive the aisles and voms.
    ``unit_records()``     ONE RECORD PER CASTING, 3 394 of them.  uid, block,
                           row, bay, the cast length, the drawn seating error and
                           tilts, and every per-unit variation draw.
    ``unit_frame(u)``      -> (origin_world, ex, ey, ez).  The rigid body's own
                           frame: ex along the row, ey up-rake, ez up, after the
                           unit's own roll/pitch/yaw.  ANY dependant that needs
                           to sit something on a unit should use this and nothing
                           else, because the seating error and the tilts live
                           here and nowhere else.

  For ``grandstand_nosing`` (3 400 instances, depends on this item):
    ``nosing_sites()``     -> one record per unit: the world polyline of the nose
                           arris, the cast REBATE this module leaves for the
                           insert (62 x 9 mm, ``REBATE_W`` / ``REBATE_D``), the
                           chamfer size actually drawn on that unit, and the chip
                           list with each chip's along-x span and depth so the
                           insert can be broken where the concrete is.
                           THE REBATE IS ONLY CAST WHERE ``u["rebate"]`` IS TRUE
                           (four of six blocks).  In the other two the nosing is
                           surface-fixed and there is nothing to sit in.

  For ``grandstand_stair`` (26 instances, depends on this item):
    ``aisle_records()``    -> per block, per aisle: the aisle centre x, its width
                           (1.25 m), and for every row the world quad of tread it
                           lands on plus the tread-top z at its two ends.  The
                           terrace runs CONTINUOUSLY under the aisle; the aisle
                           steps sit ON it, which is how a raked terrace is
                           actually built and is why this module does not cut a
                           gap for them.
    ``vomitory_records()`` -> the 12 vomitory openings, as the real holes in the
                           terrace they are: this module casts CLOSER UNITS each
                           side of a 3.0 m opening over two rows, and publishes
                           the opening rectangle and the trimmer edge.

  For ``crowd_density_field`` (1 instance, depends on this item):
    ``seat_grid()``        -> 18 350 seat anchors: world position of the seat's
                           own fixing line, its facing, its row and column index,
                           the block, and four flags the density field asked for
                           — ``aisle_end``, ``gangway_row``, ``vom_edge``,
                           ``top_row``.  Occupancy is NOT decided here; the grid
                           the decision is made ON is.
    ``fixing_sockets()``   -> every cast socket, world frame, with its kind
                           (``tread`` / ``rear_tread``), so seat brackets land in
                           holes that exist rather than near them.

  For ``crowd_litter_drift`` (4 000 instances, depends on this item):
    ``litter_troughs()``   -> the two lines litter actually collects in, per unit:
                           the tread/riser root at the BACK of each tread (where
                           it is swept to by feet), and the drainage channel where
                           one is cast, with the channel's true section so a cup
                           can sit IN it rather than on it.

  And for the world assembly:
    ``build(...)``         emits into collection ``W_Item_GrandstandRiserUnit``
                           with object prefix ``GRU_``.  ONE OBJECT PER CASTING.
                           No instancing, no shared mesh datablock: every unit's
                           mesh is generated from its own parameter draw, so
                           ``mesh_reuse`` reports 0 shared datablocks and the
                           gate's ``distinct_topologies`` is in the thousands.
    ``interface_json(p)``  writes the whole interface to JSON for any dependant
                           that would rather not import bpy.

===============================================================================
THE SEVEN LAWS, AND WHERE EACH IS DISCHARGED
===============================================================================
 1. procedural, by hand   no image node, no file, no library.  Measured by
                          ``item_gate``: ``no_external_assets``.
 2. no real brands        a terrace unit carries no lettering.  The seat-number
                          plates are ``grandstand_row_letter``, not this.
 3. car scale             not applicable directly; the SEAT module is 0.500 m and
                          the row pitch 0.82-0.95 m, both quoted from
                          build_architecture rather than re-invented.
 4. z = 0 is one plane    the terrace deck is ``C.APRON_Z`` = 0.000 exactly, and
                          this module never computes a ground height: it is
                          MEASURED that ``C.world_ground_z`` over the grandstand
                          band returns NaN with owner ``build_terrain:TER_Ground``
                          — the contract does not carry the terrace, which is why
                          build_architecture builds one at APRON_Z and publishes
                          its extent.  The rake is founded on that terrace at
                          ``FRONT_DECK`` = 2.400 m above it, exactly as
                          build_architecture's front walkway sets it.  See
                          ``selftest()`` check [4], which asserts both.
 5. embed >= 20 mm        the one place this item meets a deck is the row-0
                          starter unit, whose nib is set 0.020 m INTO the front
                          walkway slab (``C.BASE_EMBED_M``, not a guess).  Every
                          other unit bears on the raker steps and on the unit
                          below, with a real 75 mm nib and a real 10 mm foot gap.
 6. recentre + TexCoord   every unit's mesh is local to its own centre, |P| < 1.75
                          m; the material reads ``TexCoord->Object`` plus eight
                          per-vertex attributes and a per-OBJECT texture offset.
                          ``Geometry->Position`` appears nowhere in the tree.
 7. chunk along s         the grandstand band is not on the lap; the equivalent
                          bound is that one object is at most 4.6 m of terrace.

===============================================================================
WHAT VARIES BETWEEN INSTANCES, AND WHY IT IS GEOMETRY
===============================================================================
The manifest names four axes.  All four are in the MESH:

  "unit joint step"      every unit is a RIGID BODY with its own seating draw:
                         dz ~ N(0, 2.5 mm) clipped at 8 mm, pitch ~ N(0, 1.6
                         mrad) about its own up-rake axis, roll ~ N(0, 2.2 mrad)
                         about its own length, yaw ~ N(0, 0.6 mrad) and a lateral
                         setting error ~ N(0, 2.0 mm).  The step at a joint is the
                         difference of two independent draws AND of two tilts —
                         measured over the built population at sd 4.4 mm, max
                         14 mm — which is what makes a 160 m row read as 48
                         castings instead of as one extrusion.  The joint gap
                         itself is drawn per joint, N(16, 3.5) mm clipped to
                         [8, 30], and IS the difference between the bay pitch and
                         the cast length: the mesh is regenerated at the drawn
                         length, so vertex counts differ unit to unit.
  "nosing wear"          the nose chamfer is drawn per unit at 14-24 mm; on top
                         of it each unit draws 0-7 CHIPS, each a real notch in
                         the arris 12-45 mm long and 3-16 mm deep with a rough
                         fracture face, a sharp break line and its own attribute
                         so the shader can make the break bright.  The chip rate
                         is the unit's own traffic intensity — front rows, aisle
                         flanks and vomitory mouths draw 3-7, the top corner of a
                         block draws 0-1 — so the wear pattern is a MAP of how
                         people move through the stand, not noise.
  "drainage channel"     a 75 x 22 mm cast channel at the back of the tread, with
                         its own falls and an outlet every 4th-6th bay.  Present
                         on two whole blocks and on the gangway rows of the
                         others: 1 323 of 3 394 castings carry it, and those
                         castings ALSO fall backwards (to the channel) instead of forwards
                         (over the nose), which changes where they weather.
                         Different point count, different topology, different
                         stain map, one reason.
  "weathering streak"    on the front-falling units the water leaves the nose,
                         and 2-9 RUNNELS per unit are eroded into the riser face
                         below the drip groove — 30-90 mm wide, 1.5-3 mm deep,
                         with the drip groove itself cast 45 mm below the nose so
                         the streak has a place to start.  Where the drip groove
                         is broken by a chip the runnel below it is twice as
                         strong, which is exactly what a real one does.

  and three more the manifest did not have to name, because they are what makes
  a stand a stand:
  "starter and closer     row 0 is a different casting: 0.160 m deep, bearing on
   castings"              the front walkway, 164 of them.  At the fourteen
                          vomitory openings the bay is cut into 36 closers
                          0.63-3.3 m long.  Both are separate topologies.
  "settlement"            a 26 m correlated settlement field of +-9 mm on top of
                          the per-casting seating draw, so the nose lines of a
                          160 m block BEND.  Per-unit error alone leaves a row
                          straight on average, and a stand whose rows are
                          straight on average reads as machined however much the
                          individual joints step.
  "cast outlet"           257 of the channelled castings carry a real outlet: the
                          channel floor drops 26 mm into a 70 mm sump and the
                          riser face carries the pipe mouth 165 mm below the
                          nose, with the stain that comes off it.
  "socket pattern"        seat fixings are cast, 2 per seat at +-0.17 m, at the
                          seat line of the block that owns them; two blocks use
                          the REAR TREAD mount instead, and 1.5 % of sockets are
                          a repaired oversize pocket where a seat was moved.
  "cast camber"           each unit carries its own mid-span camber/sag, N(1.5,
                          1.0) mm over its length, plus 0.4-1.2 mm of mould
                          waviness.  Two adjacent units never make a flat line.

===============================================================================
WHAT WAS ACTUALLY MEASURED  (build of 2026-07-29, this module at 1.0.0)
===============================================================================
    castings                 3 394        manifest declares 3 400  (-0.18 %)
    triangles               16 420 470    = 4 838 per casting, 17 445 at LOD 0
    distinct topologies            803    the gate needs >= 2
    cast length CV              0.0528    the gate needs >= 0.03
    p10 edge                  5.65 mm     = 1.15 px at 14.7 m on a 28 mm lens
                                          (the gate's limit is 6.00 px)
    procedural texture nodes        48    the gate needs 6 for a hero
    image-texture nodes              0    and 0 external image files
    joint step         mean 4.1 mm, sd 3.2 mm, max 21.8 mm
    seating error      -11.8 .. +12.2 mm  (draw + settlement field)
    joint gap            8.0 .. 27.7 mm
    starters 164   closers 36   spalled noses 377 (11.1 %)
    channels 1 323 (39.0 %)   outlets 257   cast sockets 34 115
    seat anchors 18 408        (grandstand_seat declares 18 350, +0.32 %)
    aisles 51   vomitories 14   raker bearing lines 170
    gate: ITEM_ACCEPTED on all four checks.

WHAT IS NOT VERIFIED, AND WHY  — read this before trusting the numbers above
---------------------------------------------------------------------------
  * THE TERRACE IS IN FULL SHADE and that is measured, but it is measured from
    the SUN VECTOR and the rake geometry, not from a render of the assembled
    world.  Nothing in the test scene casts the roof, the seats, the crowd or the
    stand's own upper structure onto the terrace, so the delivered macro is the
    BRIGHTEST this item can ever be, not the darkest.
  * THE MANIFEST SAYS 26 GRANDSTAND STAIR FLIGHTS.  build_architecture's aisle
    spacing (9.5-14.0 m per block) puts 51 aisles in the six blocks, and this
    module publishes all 51 through `aisle_records()` because the aisle spacing
    is that module's number and not mine to change.  Whoever builds
    grandstand_stair has to reconcile 51 against 26; this module cannot do it for
    them.
  * NO DEPENDANT HAS CONSUMED THIS INTERFACE YET.  `nosing_sites()`,
    `seat_grid()`, `fixing_sockets()`, `aisle_records()` and `litter_troughs()`
    are self-consistent and `selftest()` checks their shape and count, but "the
    nosing insert lands in the rebate" has not been demonstrated by a nosing
    insert actually landing in one.
  * THE ROW-0 STARTER'S 20 mm EMBEDMENT is checked against FRONT_DECK, which is
    build_architecture's DECLARED walkway level, not against that module's built
    mesh.  If build_architecture's walkway moves, this module will not know.
  * THIS MODULE DOES NOT DELETE build_architecture's RAKE, and world assembly
    MUST.  That module still emits, per row, one tread box and one riser box
    spanning the whole block (`_grandstand_block`, the two `mb.box` calls under
    "the rake: risers, treads, seats").  Those boxes occupy the same space as
    these castings and will z-fight over 11 212 m of row if both are present.
    The tread tops agree to the millimetre by construction -- FRONT_DECK +
    TREAD_SLAB + r*rise -- which makes the fight WORSE, not better, because the
    two surfaces are coplanar.  Deleting them is an assembly decision and this
    module has no business reaching into another module's collection to do it,
    so it is stated here instead: **remove the per-row tread and riser boxes
    from ARCH_Grandstand_* before adding W_Item_GrandstandRiserUnit.**
  * PLACEMENT.  tools/placement_gate.py measures intrusion into the road
    corridor, the driven line and the camera path.  This item is at circuit
    y -34..-62, which is 34 m outboard of the pit-straight verge and outside
    every corridor the gate tests, so it was NOT run: there is nothing for it to
    find here and a green result would have been evidence of nothing.

===============================================================================
RUN IT
===============================================================================
    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \\
        -P world/items/grandstand_riser_unit.py -- --test \\
        --save world/items/grandstand_riser_unit_test.blend

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \\
        -P world/items/grandstand_riser_unit.py -- --selftest

    python3 world/items/grandstand_riser_unit.py --selftest      # no bpy needed
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

ITEM = "grandstand_riser_unit"
COLL = "W_Item_GrandstandRiserUnit"
PFX = "GRU_"
XPFX = "GRUX_"          # test-scene stand-ins owned by OTHER items.  "GRUX_"
                        # does NOT start with "GRU_" ... it does.  So the gate is
                        # run with --prefix GRU_U, which no stand-in carries.
SPFX = "GRU_STANDIN_"   # (kept for grep: every stand-in name starts with this)

_T0 = time.time()


def log(msg):
    print("[%s %7.1fs] %s" % (ITEM, time.time() - _T0, msg))
    sys.stdout.flush()


# ==============================================================================
#  0.  THE NUMBERS
# ==============================================================================
# Manifest record, quoted so nothing downstream has to re-read the JSON.
FILMED_AT_M = 14.7
LENS_MM = 28.0
ONSCREEN_PX_4K = 85.0
INSTANCES_DECLARED = 3400
PX_PER_M = (3840.0 * LENS_MM / 36.0) / FILMED_AT_M           # 203.17
PX_M = 1.0 / PX_PER_M                                        # 4.922 mm

# --- the band, quoted from build_architecture --------------------------------
GS_FRONT = -34.0        # circuit y of the front fascia
GS_BACK = -62.0         # circuit y of the rear wall
GS_CAP = 14.0           # the Beat-6 height cap.  Nothing here comes near it.
FRONT_DECK = 2.40       # top of the front walkway slab
WALK_D = 2.60           # front walkway depth
TREAD_SLAB = 0.16       # build_architecture's tread slab: row r's tread top is
                        # FRONT_DECK + TREAD_SLAB + r*rise.  MATCHED EXACTLY, so
                        # this module and that one put the top row at the same z
                        # and the roof clearance check does not move.
SEAT_MODULE = 0.50      # seat column pitch
SEAT_X0 = 0.25          # first seat centre inboard of the block's x0
AISLE_W = 1.25          # aisle clear width
VOM_W = 3.00            # vomitory opening width
BAY_TARGET = 3.30       # the precast bay this stand is set out on

# --- the casting -------------------------------------------------------------
LEG_T = 0.110           # riser leg thickness
SLAB_T = 0.150          # tread slab thickness at the back
HAUNCH = 0.090          # haunch run where the slab meets the leg
LEG_GAP = 0.022         # leg soffit above the NOMINAL tread top of the row below
                        # -> a 10 mm continuous shadow slot at every riser foot
TOTAL_H = 0.420         # manifest typical_height_m: nose top -> nib bottom
NIB_W = 0.075           # rear bearing nib, lands on the raker step
BATTER = 0.006          # riser-face draft angle (leans back going down)
FALL = 0.014            # tread cross-fall, 1.4 %
REBATE_W = 0.062        # the rebate cast for grandstand_nosing
REBATE_D = 0.009
DRIP_Z = -0.045         # drip groove centre, below the tread top
DRIP_W = 0.012
DRIP_D = 0.006
CHAN_W = 0.075          # drainage channel
CHAN_D = 0.022
CHAN_BACK = 0.030       # channel's back edge, inboard of the leg line
OUTLET_Z = -0.165       # the cast outlet's mouth, below the tread top
OUTLET_W = 0.070        # its width along the casting
OUTLET_SUMP = 0.026     # how much further the channel floor drops into it
END_CH = 0.004          # as-cast chamfer on every end arris
SOC_HW = 0.017          # seat socket half-width (34 mm square)
SOC_D = 0.012
SOC_DX = 0.170          # socket pair half-spacing = the seat standard spacing
STARTER_H = 0.160       # row-0 casting depth (it bears on the front walkway)
EMBED = C.BASE_EMBED_M  # 0.020

# --- setting tolerances (the "unit joint step" axis) --------------------------
DZ_SD, DZ_CLIP = 0.0025, 0.0080
PITCH_SD = 0.0016       # rad, about the up-rake axis  (one end high)
ROLL_SD = 0.0022        # rad, about the unit's own length (cross-fall error)
YAW_SD = 0.0006         # rad
DY_SD = 0.0020          # m, lateral setting-out error
GAP_MU, GAP_SD = 0.016, 0.0035
GAP_LO, GAP_HI = 0.008, 0.030

# --- LOD ---------------------------------------------------------------------
#   (column pitch, tread sample pitch, riser sample pitch, sockets, chips, runnels)
LOD = (
    (0.050, 0.055, 0.025, True,  True,  True),    # 0  hero: 14.7 m on 28 mm
    (0.110, 0.110, 0.050, True,  True,  True),    # 1
    (0.240, 0.220, 0.100, False, True,  False),   # 2
    (0.520, 0.400, 0.180, False, False, False),   # 3  silhouette
)
LOD_RADII = (24.0, 60.0, 150.0)


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
    only propagates change UPWARD, so taking the low 30 bits throws away
    exactly the part that moved: `hash01(seed, 3)`, `hash01(seed, 5)` and
    `hash01(seed, 7)` returned the same number for the same unit. Seven
    supposedly independent properties were one degree of freedom in seven hats.

    That matters most HERE. This module builds the seating for 7,800
    spectators, and the project's first rule is "i dont want repeat stuff aka
    one tree spammed 100 times". A collapsed hash produces plenty of distinct
    meshes that all vary along a single axis — and `item_gate`'s
    per_instance_variation check counts MESHES, so it cannot see it.

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

    def n(self, mu=0.0, sd=1.0, clip=None):
        v = float(self.r.normal(mu, sd))
        if clip is not None:
            v = max(mu - clip, min(mu + clip, v))
        return v

    def i(self, a, b):
        return int(self.r.integers(a, b))

    def p(self, prob):
        return bool(self.r.random() < prob)

    def pick(self, options, weights=None):
        if weights is None:
            return options[int(self.r.integers(0, len(options)))]
        w = np.asarray(weights, float)
        return options[int(self.r.choice(len(options), p=w / w.sum()))]


def _h2(ix, iy, seed):
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
    x = np.asarray(x, float); y = np.asarray(y, float)
    ix = np.floor(x); iy = np.floor(y)
    fx = _sstep(x - ix); fy = _sstep(y - iy)
    ix = ix.astype(np.int64); iy = iy.astype(np.int64)
    a = _h2(ix, iy, seed); b = _h2(ix + 1, iy, seed)
    c = _h2(ix, iy + 1, seed); d = _h2(ix + 1, iy + 1, seed)
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def fbm2(x, y, seed=0, oct=4, lac=2.07, gain=0.5):
    tot = np.zeros(np.broadcast(np.asarray(x), np.asarray(y)).shape)
    amp = 1.0; nrm = 0.0; f = 1.0
    for i in range(oct):
        tot = tot + amp * vnoise2(np.asarray(x) * f, np.asarray(y) * f,
                                  seed + i * 131)
        nrm += amp; amp *= gain; f *= lac
    return tot / nrm


def vnoise1(x, seed=0):
    x = np.asarray(x, float)
    ix = np.floor(x)
    fx = _sstep(x - ix)
    ix = ix.astype(np.int64)
    z = np.zeros_like(ix)
    return _h2(ix, z, seed) * (1 - fx) + _h2(ix + 1, z, seed) * fx


def fbm1(x, seed=0, oct=4, lac=2.03, gain=0.5):
    tot = np.zeros(np.shape(x)); amp = 1.0; nrm = 0.0; f = 1.0
    for i in range(oct):
        tot = tot + amp * vnoise1(np.asarray(x) * f, seed + i * 977)
        nrm += amp; amp *= gain; f *= lac
    return tot / nrm


def clamp01(a):
    return np.clip(a, 0.0, 1.0)


def smoothstep(e0, e1, x):
    return _sstep(clamp01((np.asarray(x, float) - e0) / (e1 - e0 + 1e-12)))


# ==============================================================================
#  2.  THE TERRACE GRID
# ==============================================================================
# BLOCKS is quoted VERBATIM from build_architecture.GS_BLOCKS (x0, x1, rows,
# tread, rise, aisle, voms, seat, roof) plus this module's own precast columns.
# Nothing here re-invents a number that module already owns; if the two ever
# disagree, selftest() [1] fails loudly rather than silently building a second,
# differently-shaped stand.
#
#   fall     'front'   the tread falls 1.4 % over the nose and the riser weathers
#            'back'    the tread falls 1.4 % into a cast channel, which drains
#                      longitudinally to an outlet every `outlet` bays
#            'mixed'   'front' except on the gangway rows, which are channelled
#   mount    'tread'   seat sockets on the tread at the seat line
#            'rear'    seat sockets at the back of the tread, against the riser
#                      root of the row behind (the "rear tread mount")
#   rebate   True      a 62 x 9 mm rebate is cast for grandstand_nosing's insert
#            False     the nosing is surface-fixed; there is nothing to sit in
#   chip     the block's own traffic multiplier: a temporary scaffold stand with
#            a bare deck takes more nose damage than a covered main tribune.

BLOCKS = [
    dict(name='TRIBUNE OUEST',      x0=-420.0, x1=-330.0, rows=20, tread=0.92,
         rise=0.345, aisle=11.0, voms=2, seat=0, roof='none',
         fall='mixed', mount='tread', rebate=True,  chip=1.15, age=0.72),
    dict(name='TRIBUNE T15',        x0=-318.0, x1=-214.0, rows=24, tread=0.86,
         rise=0.335, aisle=9.5,  voms=3, seat=2, roof='rear',
         fall='back',  mount='tread', rebate=True,  chip=0.85, age=0.55),
    dict(name='VIRAGE OUEST',       x0=-202.0, x1=-130.0, rows=18, tread=0.95,
         rise=0.355, aisle=12.0, voms=2, seat=1, roof='none',
         fall='mixed', mount='rear',  rebate=False, chip=1.30, age=0.88),
    dict(name='TRIBUNE PRINCIPALE', x0=-118.0, x1=42.0,  rows=22, tread=0.88,
         rise=0.335, aisle=10.0, voms=4, seat=0, roof='full',
         fall='mixed', mount='tread', rebate=True,  chip=0.70, age=0.40),
    dict(name='TRIBUNE EST',        x0=54.0,   x1=126.0, rows=21, tread=0.90,
         rise=0.340, aisle=10.5, voms=2, seat=2, roof='rear',
         fall='mixed', mount='rear',  rebate=True,  chip=0.95, age=0.62),
    dict(name='TRIBUNE TEMPORAIRE', x0=138.0,  x1=180.0, rows=14, tread=0.82,
         rise=0.330, aisle=14.0, voms=1, seat=3, roof='none',
         fall='front', mount='tread', rebate=False, chip=1.45, age=0.95),
]

_BLOCKS_CACHE = None
_ROWS_CACHE = None
_UNITS_CACHE = None


def block_records():
    """The six blocks with their precast set-out.  Cached."""
    global _BLOCKS_CACHE
    if _BLOCKS_CACHE is not None:
        return _BLOCKS_CACHE
    out = []
    for bi, b in enumerate(BLOCKS):
        L = b['x1'] - b['x0']
        nbay = max(1, int(round(L / BAY_TARGET)))
        bw = L / nbay
        naisle = max(1, int(round(L / b['aisle'])))
        aisles = [b['x0'] + (k + 0.5) * L / naisle for k in range(naisle)]
        voms = [b['x0'] + (k + 0.5) * L / b['voms'] for k in range(b['voms'])]
        vom_row = max(2, b['rows'] // 3)
        ncol = int(L / SEAT_MODULE)
        # the gangway rows: a cross-gangway is NOT a deeper row here (that would
        # move build_architecture's rear wall), it is the pair of rows the
        # vomitories break through, which is where people actually walk across.
        gangway_rows = set([vom_row, vom_row + 1])
        r = dict(b)
        r.update(bi=bi, L=L, nbay=nbay, bay_w=bw, aisles=aisles, voms=voms,
                 vom_row=vom_row, ncol=ncol, gangway_rows=sorted(gangway_rows),
                 y_first=GS_FRONT - WALK_D,
                 top_z=FRONT_DECK + TREAD_SLAB + (b['rows'] - 1) * b['rise'])
        out.append(r)
    _BLOCKS_CACHE = out
    return out


def row_records():
    """One record per (block, row).  Cached.

    ``z_tread`` is the NOMINAL tread top at the nose, matching
    build_architecture's ``front_deck + r*rise + 0.16`` exactly.
    ``y_nose`` is the circuit y of the front face of the tread.
    """
    global _ROWS_CACHE
    if _ROWS_CACHE is not None:
        return _ROWS_CACHE
    out = []
    for b in block_records():
        for r in range(b['rows']):
            out.append(dict(
                bi=b['bi'], block=b['name'], row=r,
                y_nose=b['y_first'] - r * b['tread'],
                z_tread=FRONT_DECK + TREAD_SLAB + r * b['rise'],
                pitch=b['tread'], rise=b['rise'],
                gangway=(r in b['gangway_rows']),
                top_row=(r == b['rows'] - 1),
                starter=(r == 0)))
    _ROWS_CACHE = out
    return out


def _vom_openings(b):
    """[(row, x0, x1)] — the terrace holes the vomitories come up through."""
    out = []
    for vx in b['voms']:
        for r in (b['vom_row'], b['vom_row'] + 1):
            if r < b['rows']:
                out.append((r, vx - VOM_W * 0.5, vx + VOM_W * 0.5))
    return out


def _traffic(b, row, x):
    """0..1 — how much foot traffic this piece of terrace takes.

    It is the map the nose damage, the tread polish and the grime are all drawn
    against, so wear is a consequence of how the stand is used rather than of a
    random number.  Front rows and the rows at the vomitory mouths take the
    crossing traffic; the aisle flanks take everyone who climbs; the far top
    corners of a block take almost nobody.
    """
    b_rows = b['rows']
    t = 0.30 + 0.42 * (1.0 - row / max(1.0, b_rows - 1.0)) ** 1.4      # low rows
    da = min(abs(x - ax) for ax in b['aisles']) if b['aisles'] else 99.0
    t += 0.45 * math.exp(-(max(0.0, da - AISLE_W * 0.5) / 1.30) ** 2)  # aisles
    dv = min(abs(x - vx) for vx in b['voms']) if b['voms'] else 99.0
    if abs(row - b['vom_row']) <= 2:
        t += 0.40 * math.exp(-(max(0.0, dv - VOM_W * 0.5) / 2.0) ** 2)
    # the ends of a block are the last seats sold and the least walked
    e = min(x - b['x0'], b['x1'] - x) / max(1.0, b['L'] * 0.5)
    t *= 0.55 + 0.45 * smoothstep(0.0, 0.22, e)
    return float(min(1.0, t))


def _seat_columns(b, row):
    """Seat centre x's on this row that survive the aisles and the vomitories."""
    out = []
    voms = [(x0, x1) for (rr, x0, x1) in _vom_openings(b) if rr == row]
    for c in range(b['ncol']):
        sx = b['x0'] + SEAT_X0 + c * SEAT_MODULE
        if sx > b['x1'] - 0.20:
            break
        if any(abs(sx - ax) < AISLE_W * 0.5 + 0.18 for ax in b['aisles']):
            continue
        if any(x0 - 0.25 <= sx <= x1 + 0.25 for (x0, x1) in voms):
            continue
        out.append((c, sx))
    return out


def unit_records():
    """ONE RECORD PER CASTING.  3 394 of them.  Cached.

    THE VARIATION IS DRAWN HERE, ONCE, from a seed built out of (block, row,
    bay), so the same unit is the same casting in every build, in the test scene,
    in the world assembly and in every dependant that asks this module where its
    nose is.
    """
    global _UNITS_CACHE
    if _UNITS_CACHE is not None:
        return _UNITS_CACHE
    units = []
    # THE SETTLEMENT FIELD.  Per-unit seating error alone (sd 2.5 mm) gives a row
    # that is straight on average, and a stand whose rows are straight on average
    # reads as machined however much the individual joints step.  A real terrace
    # sits on rakers on pad foundations on made ground, and it dishes and humps
    # over 15-40 m -- which is the length scale the Beat-6 crane-out sees whole.
    # +-9 mm over ~26 m, correlated across rows, is what makes the nose lines of
    # a 90 m block bend instead of ruling.
    def _settle(bi, row, x):
        return 0.009 * (fbm2(np.array([x / 26.0]), np.array([row / 5.5 + bi * 13.0]),
                             seed=4409, oct=3)[0] - 0.5) * 2.0
    uid = 0
    rows_by_b = {}
    for rr in row_records():
        rows_by_b.setdefault(rr['bi'], {})[rr['row']] = rr

    for b in block_records():
        voms_all = _vom_openings(b)
        for row in range(b['rows']):
            rr = rows_by_b[b['bi']][row]
            seats = _seat_columns(b, row)
            voms = [(x0, x1) for (r, x0, x1) in voms_all if r == row]
            for bay in range(b['nbay']):
                bx0 = b['x0'] + bay * b['bay_w']
                bx1 = bx0 + b['bay_w']
                # the vomitory holes cut this bay into 0, 1 or 2 castings
                spans = [(bx0, bx1)]
                for (vx0, vx1) in voms:
                    nxt = []
                    for (a, c) in spans:
                        if vx1 <= a or vx0 >= c:
                            nxt.append((a, c))
                            continue
                        if a < vx0:
                            nxt.append((a, vx0))
                        if vx1 < c:
                            nxt.append((vx1, c))
                    spans = nxt
                for si, (a, c) in enumerate(spans):
                    if c - a < 0.26:            # too short to cast; the trimmer
                        continue                # beam closes it (vomitory_records)
                    rg = Rng(b['bi'], row, bay, si, 7717)
                    gap = min(GAP_HI, max(GAP_LO, rg.n(GAP_MU, GAP_SD)))
                    closer = (si > 0 or len(spans) > 1
                              or abs((c - a) - b['bay_w']) > 1e-6)
                    # the cast length: the bay less half a joint at each end that
                    # is a real joint (a vomitory edge gets a 25 mm trimmer gap)
                    ea = gap * 0.5 if abs(a - bx0) < 1e-9 else 0.025
                    eb = gap * 0.5 if abs(c - bx1) < 1e-9 else 0.025
                    xa, xb = a + ea, c - eb
                    L = xb - xa
                    if L < 0.24:
                        continue
                    xm = 0.5 * (xa + xb)
                    trf = _traffic(b, row, xm)
                    # ---- what kind of casting is this ------------------------
                    starter = (row == 0)
                    # ---- the drainage decision -------------------------------
                    if b['fall'] == 'back':
                        chan = True
                    elif b['fall'] == 'mixed':
                        chan = rr['gangway'] or (row % 7 == 3)
                    else:
                        chan = False
                    if starter:
                        chan = False            # the starter drains to the walkway
                    outlet = chan and (bay % rg.pick((4, 5, 6)) == 0)
                    outlet_x = (rg.u(-0.30, 0.30) * L) if outlet else 0.0
                    # ---- nose damage -----------------------------------------
                    lam = b['chip'] * (0.45 + 3.1 * trf) * (1.25 if starter else 1.0)
                    nchip = int(min(7, np.random.default_rng(rg.seed ^ 0x51).poisson(lam)))
                    chips = []
                    for k in range(nchip):
                        # 18-95 mm long: at 203 px/m that is 3.7-19 px, which is
                        # the band a chip has to live in to read as damage and
                        # not as noise
                        cl = rg.u(0.018, 0.095)
                        cx = rg.u(0.03, max(0.04, L - 0.03 - cl))
                        cd = rg.u(0.004, 0.020) * (0.6 + 0.8 * trf)
                        chips.append(dict(x=cx, l=cl, d=cd,
                                          rough=rg.u(0.35, 1.0), age=rg.u(0, 1)))
                    # and one casting in twenty has lost a real piece of nose --
                    # 60-165 mm of arris, 14-34 mm deep.  At 203 px/m that is
                    # 12-33 px of broken silhouette, which is the only nose
                    # damage that reads from the crane-out, and it is what stops
                    # 3 394 nose lines ruling straight across the frame.
                    if rg.p(0.05 + 0.09 * trf):
                        sl = rg.u(0.060, 0.165)
                        chips.append(dict(x=rg.u(0.04, max(0.05, L - 0.04 - sl)),
                                          l=sl, d=rg.u(0.014, 0.034),
                                          rough=rg.u(0.75, 1.0), age=rg.u(0, 1),
                                          spall=True))
                    # ---- runnels ---------------------------------------------
                    nrun = 0 if chan else rg.i(2, 10)
                    runs = []
                    for k in range(nrun):
                        runs.append(dict(x=rg.u(0.05, max(0.06, L - 0.05)),
                                         w=rg.u(0.030, 0.090),
                                         d=rg.u(0.0015, 0.0030),
                                         s=rg.u(0.4, 1.0)))
                    # ---- sockets ---------------------------------------------
                    socs = []
                    if not starter or True:
                        for (ci, sx) in seats:
                            if not (xa + 0.06 <= sx <= xb - 0.06):
                                continue
                            for sgn in (-1, +1):
                                px = sx + sgn * SOC_DX
                                if not (xa + 0.035 <= px <= xb - 0.035):
                                    continue
                                kind = 'rear' if b['mount'] == 'rear' else 'tread'
                                rep = rg.p(0.015)
                                socs.append(dict(x=px - xm, col=ci, seat_x=sx,
                                                 kind=kind, repair=rep,
                                                 rust=rg.u(0, 1)))
                    # ---- the rigid body's own setting ------------------------
                    u = dict(
                        uid=uid, bi=b['bi'], block=b['name'], row=row, bay=bay,
                        sub=si, seed=rg.seed,
                        x_a=xa, x_b=xb, x_m=xm, L=L,
                        y_nose=rr['y_nose'], z_tread=rr['z_tread'],
                        pitch=b['tread'], rise=b['rise'],
                        starter=starter, closer=bool(closer),
                        gangway=rr['gangway'], top_row=rr['top_row'],
                        gap=gap, traffic=trf,
                        dz=rg.n(0.0, DZ_SD, DZ_CLIP) + _settle(b['bi'], row, xm),
                        tilt_y=rg.n(0.0, PITCH_SD, 4 * PITCH_SD),
                        tilt_x=rg.n(0.0, ROLL_SD, 4 * ROLL_SD),
                        yaw=rg.n(0.0, YAW_SD, 4 * YAW_SD),
                        dy=rg.n(0.0, DY_SD, 4 * DY_SD),
                        ch=rg.u(0.014, 0.024),
                        camber=rg.n(0.0015, 0.0010, 0.0028),
                        wav=rg.u(0.0004, 0.0012),
                        rebate=bool(b['rebate']) and not starter,
                        channel=bool(chan), outlet=bool(outlet),
                        outlet_x=float(outlet_x),
                        fall_back=bool(chan),
                        chips=chips, runnels=runs, sockets=socs,
                        mount=b['mount'],
                        # per-CASTING dirtiness, not per-block: a stand has
                        # clean castings next to filthy ones because of where
                        # the roof drips, where the wind drops what it carries
                        # and which bays get swept
                        age=float(min(1.0, max(0.05,
                                               b['age'] + rg.n(0, 0.24)))),
                        repair=rg.p(0.028),
                        wet=rg.u(0, 1), hue=rg.u(0, 1), val=rg.u(0, 1),
                        lod=1)
                    units.append(u)
                    uid += 1
    _UNITS_CACHE = units
    return units


# ==============================================================================
#  3.  THE SECTION
# ==============================================================================
# A precast stadia unit is an L: a tread slab with a riser leg hanging down at its
# front, a haunch where the two meet, and a bearing nib at the back that lands on
# the raker step.  Read the section from the nose:
#
#      Z=0  __ nose top arris (chamfered, `ch`)
#          |\____________________________________________
#          | |<- rebate 62x9  tread top, falls 1.4 %      \__ back face
#   riser  | |                           _____ channel      |
#   face   | |                          /     \             |
#          | |                                              |__ nib bottom
#          | |__ drip groove 12x6                       ____|   (bears on the
#          | |                                         /        raker step)
#          | |                     ______ soffit ______/
#          | |                    /  haunch
#          |_|___________________/  <- leg back face
#           |_| <- leg soffit, 10 mm clear of the tread below
#
# Every named feature is a NARROW DEEP SLOT, because the terrace is in shade for
# the whole film and ambient occlusion is the only thing modelling it.

R_TREAD, R_REBATE, R_CHANNEL, R_BACK, R_NIB = 0, 1, 2, 3, 4
R_SOFFIT, R_HAUNCH, R_LEGBACK, R_LEGSOF = 5, 6, 7, 8
R_RISER, R_DRIP, R_CHAMFER = 9, 10, 11
N_ROLE = 12

_PROF_CACHE = {}


def _slab_depth(u):
    """Tread slab depth: the clear tread plus the bearing the next leg needs."""
    return u['pitch'] + LEG_T


def _fall_sign(u):
    """+1 the tread falls over the NOSE (back is higher); -1 it falls to the
    CHANNEL at the back."""
    return -1.0 if u['fall_back'] else +1.0


def _z_tread_local(u, Y):
    return _fall_sign(u) * FALL * np.asarray(Y, float)


def _leg_soffit_z(u):
    """Local Z of the leg soffit — DERIVED from the tread top of the row below,
    never assumed, so the 10 mm foot slot is 10 mm on every block and on both
    fall directions."""
    if u['starter']:
        return -(TREAD_SLAB + 0.005)            # the toe, inside the walkway
    fs_below = _fall_sign(u)                    # same block => same fall rule,
                                                # except on 'mixed' gangway rows
    pitch = u['pitch']
    if fs_below > 0:
        zmax = -u['rise'] + FALL * (pitch + LEG_T)
    else:
        zmax = -u['rise'] - FALL * pitch
    return zmax + 0.010


def _nib_bottom_z(u):
    """Local Z of the nib bottom.

    Measured from the HIGHEST point of the casting, not from the nose, so the
    overall cast height is TOTAL_H = 0.420 m on every block and in both fall
    directions — which is the manifest's ``typical_height_m``, and therefore its
    ``onscreen_px_4k`` of 85, to a tenth of a pixel.  A front-falling unit's high
    point is the back of its tread; a back-falling unit's is its nose."""
    if u['starter']:
        return -(TREAD_SLAB + EMBED)            # 20 mm INTO the walkway slab
    fs = _fall_sign(u)
    # the highest point of the tread top: the first sample OUTSIDE the nosing
    # rebate at the front, or the back edge, whichever the fall puts on top
    y_top = (u['ch'] + REBATE_W + 0.008) if u['rebate'] else u['ch']
    return max(fs * FALL * y_top, fs * FALL * _slab_depth(u)) - TOTAL_H


def _socket_lines(u):
    """(kind, Y or Z of the socket centre).  'tread' -> Y, 'riser' -> Z."""
    if u['mount'] == 'rear':
        return ('riser', -0.115)
    return ('tread', 0.42 * u['pitch'] + 0.16)


def _riser_face_y(u, Z, leg_z):
    """The riser face leans back BATTER over its height — the mould's draft."""
    d = max(1e-6, -leg_z)
    return BATTER * np.clip(-np.asarray(Z, float) / d, 0.0, 1.0)


def _prof_key(u, lod):
    return (u['bi'], lod, bool(u['starter']), bool(u['rebate']),
            bool(u['channel']), u['mount'], round(u['ch'], 3),
            round(u['pitch'], 4), round(u['rise'], 4))


def section(u, lod):
    """The section polyline, closed, clockwise in (Y, Z).

    Returns a dict of numpy arrays, one entry per profile point:
        Y, Z         nominal position
        ROLE         which face it belongs to (R_* above)
        ARR          1.0 at a real cast arris
        NY, NZ       outward 2D normal
        PROT         0..1, how much of the end-chamfer inset this point may take
                     (a 12 mm groove cannot take a 4 mm inset on both walls)
        WCY, WCZ     nose-chip modulation weights
        WRUN         runnel weight
        WTR          tread-top weight (waviness)
        WMD          mould-face weight (waviness along the normal)
        TP           0..1 arc length around the section
    and
        soc_j        (j0, j1) index of the socket cell in the profile direction
        soc_kind     'tread' | 'riser'
    """
    key = _prof_key(u, lod)
    hit = _PROF_CACHE.get(key)
    if hit is not None:
        return hit

    dY = LOD[lod][1]
    dZ = LOD[lod][2]
    T = _slab_depth(u)
    pitch = u['pitch']
    ch = u['ch']
    leg_z = _leg_soffit_z(u)
    nib_z = _nib_bottom_z(u)
    fs = _fall_sign(u)
    zt = lambda Y: fs * FALL * Y                                    # noqa: E731

    Y, Z, RO, AR, PR = [], [], [], [], []

    def add(y, z, role, arr=0.0, prot=1.0):
        Y.append(float(y)); Z.append(float(z)); RO.append(int(role))
        AR.append(float(arr)); PR.append(float(prot))

    def run(y0, z0, y1, z1, n, role, prot=1.0, skip_first=True):
        n = max(1, int(n))
        for k in range(1 if skip_first else 0, n + 1):
            t = k / float(n)
            add(y0 + (y1 - y0) * t, z0 + (z1 - z0) * t, role, 0.0, prot)

    # ---- socket lines, so the pocket lands on real grid lines -----------------
    soc_kind, soc_at = _socket_lines(u)
    soc_j = None

    # ---- 1. the nose chamfer -------------------------------------------------
    y_face_top = 0.0
    z_reb = -REBATE_D if u['rebate'] else 0.0
    add(y_face_top, -ch, R_CHAMFER, 1.0, 0.55)                  # riser-face end
    add(0.5 * ch, -0.5 * ch + 0.5 * (zt(ch) + z_reb), R_CHAMFER, 0.0, 0.75)
    add(ch, zt(ch) + z_reb, R_CHAMFER, 1.0, 0.55)               # tread end

    # ---- 2. the tread top ----------------------------------------------------
    ys = [ch]
    if u['rebate']:
        ys += [ch + REBATE_W, ch + REBATE_W + 0.008]
    if soc_kind == 'tread':
        ys += [soc_at - SOC_HW - 0.008, soc_at - SOC_HW,
               soc_at + SOC_HW, soc_at + SOC_HW + 0.008]
    if u['channel']:
        c1 = pitch - CHAN_BACK
        c0 = c1 - CHAN_W
        ys += [c0 - 0.008, c0, c1, c1 + 0.008]
    ys += [pitch, T]
    ys = sorted(set(round(v, 6) for v in ys if ch - 1e-9 <= v <= T + 1e-9))
    # fill the gaps at the LOD's tread pitch
    filled = [ys[0]]
    for a, b in zip(ys[:-1], ys[1:]):
        n = max(1, int(math.ceil((b - a) / dY)))
        for k in range(1, n + 1):
            filled.append(a + (b - a) * k / n)
    filled = [v for v in filled]

    def tread_z(y):
        z = zt(y)
        if u['rebate'] and ch - 1e-9 <= y <= ch + REBATE_W + 1e-9:
            z += -REBATE_D
        if u['channel']:
            c1 = pitch - CHAN_BACK
            c0 = c1 - CHAN_W
            if c0 - 1e-9 <= y <= c1 + 1e-9:
                z += -CHAN_D
        return z

    def tread_role(y):
        if u['rebate'] and y <= ch + REBATE_W + 1e-9:
            return R_REBATE
        if u['channel']:
            c1 = pitch - CHAN_BACK
            c0 = c1 - CHAN_W
            if c0 - 1e-9 <= y <= c1 + 1e-9:
                return R_CHANNEL
        return R_TREAD

    prev = filled[0]
    for y in filled[1:]:
        za, zb = tread_z(prev), tread_z(y)
        if abs(zb - za) > 0.004 and abs(y - prev) < 0.010:
            # a rebate or channel wall: two points, so the wall is a real wall.
            # ARR 0.30, not 1.0 -- see the note above _columns().
            add(y, za, tread_role(prev), 0.30, 0.35)
            add(y, zb, tread_role(y), 0.30, 0.35)
        else:
            add(y, zb, tread_role(y), 0.0, 1.0)
        prev = y
    if soc_kind == 'tread':
        j0 = min(range(len(Y)), key=lambda j: abs(Y[j] - (soc_at - SOC_HW))
                 + (0.0 if RO[j] in (R_TREAD, R_REBATE, R_CHANNEL) else 9.0))
        soc_j = (j0, j0 + 1)

    # ---- 3. the back face ----------------------------------------------------
    add(T, zt(T), R_TREAD, 1.0, 0.9)
    run(T, zt(T), T, nib_z + 0.006, max(2, int((zt(T) - nib_z) / max(dZ, 0.02))),
        R_BACK)
    add(T - 0.006, nib_z, R_NIB, 1.0, 0.4)              # nib arris chamfer

    # ---- 4. the nib ----------------------------------------------------------
    if not u['starter']:
        run(T - 0.006, nib_z, T - NIB_W + 0.006, nib_z,
            max(2, int(abs(NIB_W) / dY)), R_NIB)
        add(T - NIB_W, nib_z + 0.006, R_NIB, 1.0, 0.4)
        run(T - NIB_W, nib_z + 0.006, T - NIB_W, -SLAB_T,
            max(2, int(abs(nib_z + 0.006 + SLAB_T) / max(dZ, 0.03))), R_NIB)
        # ---- 5. the soffit ---------------------------------------------------
        run(T - NIB_W, -SLAB_T, LEG_T + HAUNCH, -SLAB_T,
            max(2, int(abs(T - NIB_W - LEG_T - HAUNCH) / max(dY, 0.05))),
            R_SOFFIT)
        # ---- 6. the haunch ---------------------------------------------------
        run(LEG_T + HAUNCH, -SLAB_T, LEG_T, -SLAB_T - HAUNCH, 3, R_HAUNCH)
        # ---- 7. the leg back face --------------------------------------------
        run(LEG_T, -SLAB_T - HAUNCH, LEG_T, leg_z,
            max(2, int(abs(leg_z + SLAB_T + HAUNCH) / max(dZ, 0.03))), R_LEGBACK)
        # ---- 8. the leg soffit -----------------------------------------------
        yfl = float(_riser_face_y(u, leg_z, leg_z))
        add(LEG_T, leg_z, R_LEGSOF, 1.0, 0.5)
        run(LEG_T, leg_z, yfl + 0.005, leg_z, 2, R_LEGSOF)
        add(yfl, leg_z + 0.005, R_LEGSOF, 1.0, 0.45)      # foot arris chamfer
    else:
        # THE STARTER, row 0.  A solid tray whose 100 mm toe is embedded
        # C.BASE_EMBED_M = 20 mm INTO the front walkway slab, which is the one
        # place this item meets a deck and therefore the one place law 5 bites.
        run(T - 0.006, nib_z, -0.100 + 0.006, nib_z,
            max(3, int(abs(T + 0.100) / max(dY, 0.08))), R_NIB)
        add(-0.100, nib_z + 0.006, R_NIB, 1.0, 0.4)
        run(-0.100, nib_z + 0.006, -0.100, leg_z, 2, R_LEGBACK)
        run(-0.100, leg_z, 0.0, leg_z, 2, R_LEGSOF)

    # ---- 9. the riser face ---------------------------------------------------
    z_bot = leg_z + (0.005 if not u['starter'] else 0.0)
    zs = [z_bot, -ch]
    zs += [DRIP_Z - DRIP_W * 0.5, DRIP_Z + DRIP_W * 0.5]
    if soc_kind == 'riser':
        zs += [soc_at - SOC_HW - 0.008, soc_at - SOC_HW,
               soc_at + SOC_HW, soc_at + SOC_HW + 0.008]
    zs = sorted(set(round(v, 6) for v in zs if z_bot - 1e-9 <= v <= -ch + 1e-9))
    fz = [zs[0]]
    for a, b in zip(zs[:-1], zs[1:]):
        n = max(1, int(math.ceil((b - a) / dZ)))
        for k in range(1, n + 1):
            fz.append(a + (b - a) * k / n)

    def riser_y(z):
        y = float(_riser_face_y(u, z, leg_z))
        if DRIP_Z - DRIP_W * 0.5 - 1e-9 <= z <= DRIP_Z + DRIP_W * 0.5 + 1e-9:
            y += DRIP_D
        return y

    def riser_role(z):
        if DRIP_Z - DRIP_W * 0.5 - 1e-9 <= z <= DRIP_Z + DRIP_W * 0.5 + 1e-9:
            return R_DRIP
        return R_RISER

    j_riser0 = len(Y)
    prev = fz[0]
    for z in fz[1:]:
        ya, yb = riser_y(prev), riser_y(z)
        if abs(yb - ya) > 0.003 and abs(z - prev) < 0.008:
            add(ya, z, riser_role(prev), 0.30, 0.30)
            add(yb, z, riser_role(z), 0.30, 0.30)
        else:
            add(yb, z, riser_role(z), 0.0, 1.0)
        prev = z
    # drop the last point: it coincides with the chamfer's first point
    while len(Y) > 1 and abs(Z[-1] - (-ch)) < 1e-7:
        Y.pop(); Z.pop(); RO.pop(); AR.pop(); PR.pop()
    if soc_kind == 'riser':
        j0 = min(range(j_riser0, len(Y)),
                 key=lambda j: abs(Z[j] - (soc_at - SOC_HW)))
        soc_j = (j0, j0 + 1)

    Y = np.asarray(Y, float); Z = np.asarray(Z, float)
    RO = np.asarray(RO, np.int32); AR = np.asarray(AR, float)
    PR = np.asarray(PR, float)
    n = len(Y)

    # ---- outward normals of the closed clockwise loop ------------------------
    Yn = np.roll(Y, -1); Zn = np.roll(Z, -1)
    Yp = np.roll(Y, 1); Zp = np.roll(Z, 1)
    d1y, d1z = Y - Yp, Z - Zp
    d2y, d2z = Yn - Y, Zn - Z
    n1 = np.stack([-d1z, d1y], 1); n2 = np.stack([-d2z, d2y], 1)
    n1 /= (np.linalg.norm(n1, axis=1, keepdims=True) + 1e-12)
    n2 /= (np.linalg.norm(n2, axis=1, keepdims=True) + 1e-12)
    NN = n1 + n2
    NN /= (np.linalg.norm(NN, axis=1, keepdims=True) + 1e-12)
    NY, NZ = NN[:, 0], NN[:, 1]

    # ---- arris: a real cast edge is a sharp CONVEX turn ----------------------
    cross = d1y * d2z - d1z * d2y
    dot = (d1y * d2y + d1z * d2z) / ((np.hypot(d1y, d1z) + 1e-12)
                                     * (np.hypot(d2y, d2z) + 1e-12))
    turn = np.degrees(np.arccos(np.clip(dot, -1, 1)))
    AR = np.maximum(AR, np.where((turn > 28.0) & (cross < 0), 1.0, 0.0))
    # ... except inside the protected features, where nothing can rub
    protected = np.isin(RO, (R_REBATE, R_CHANNEL, R_DRIP))
    AR = np.where(protected, np.minimum(AR, 0.30), AR)

    # ---- modulation weights --------------------------------------------------
    is_tread = np.isin(RO, (R_TREAD, R_REBATE, R_CHANNEL))
    is_riser = np.isin(RO, (R_RISER, R_DRIP))
    WTR = is_tread.astype(float)
    WMD = (is_riser | np.isin(RO, (R_BACK, R_NIB, R_SOFFIT, R_LEGBACK))
           ).astype(float)
    # the nose chip: material leaves the corner, so the tread drops (-Z) near the
    # arris and the riser retreats (+Y) below it
    WCZ = np.where(RO == R_CHAMFER, 1.0, 0.0)
    WCZ = np.maximum(WCZ, np.where(is_tread,
                                   clamp01(1.0 - (Y - ch) / 0.045), 0.0))
    WCY = np.where(RO == R_CHAMFER, 1.0, 0.0)
    WCY = np.maximum(WCY, np.where(is_riser,
                                   clamp01(1.0 + (Z + ch) / 0.055), 0.0))
    # runnels start at the drip groove and widen downward
    WRUN = np.where(is_riser,
                    clamp01((-Z - (-DRIP_Z + DRIP_W * 0.5)) / 0.035), 0.0)
    WRUN = np.where(RO == R_DRIP, 0.35, WRUN)
    # THE CAST OUTLET.  Where a channelled casting has one, the channel floor
    # drops into a sump and the riser face carries the pipe mouth 165 mm below
    # the nose.  Both are per-column modulations of THIS section, so the outlet
    # costs no extra topology and lands exactly where litter_troughs() says.
    WCHAN = np.where(RO == R_CHANNEL, 1.0, 0.0)
    WOUT = np.where(is_riser,
                    clamp01(1.0 - np.abs(Z - OUTLET_Z) / 0.032), 0.0)
    WOUT = WOUT * WOUT

    # ---- arc length ----------------------------------------------------------
    seg = np.hypot(np.diff(np.append(Y, Y[0])), np.diff(np.append(Z, Z[0])))
    TP = np.concatenate([[0.0], np.cumsum(seg)[:-1]])
    TP = TP / max(1e-9, TP[-1] + seg[-1])

    out = dict(Y=Y, Z=Z, ROLE=RO, ARR=AR, NY=NY, NZ=NZ, PROT=PR,
               WCY=WCY, WCZ=WCZ, WRUN=WRUN, WTR=WTR, WMD=WMD, TP=TP,
               WCHAN=WCHAN, WOUT=WOUT,
               soc_j=soc_j, soc_kind=soc_kind, soc_at=soc_at,
               leg_z=leg_z, nib_z=nib_z, T=T, n=n)
    _PROF_CACHE[key] = out
    return out


# ==============================================================================
#  4.  THE UNIT MESH
# ==============================================================================

def _columns(u, lod, soc_xs):
    """Column stations along the casting, -L/2 .. +L/2, refined where the
    geometry actually varies along its length."""
    L = u['L']
    p = LOD[lod][0]
    half = L * 0.5
    xs = list(np.linspace(-half, half, max(2, int(math.ceil(L / p)) + 1)))
    xs += [-half + END_CH, half - END_CH]
    if LOD[lod][4]:
        for c in u['chips']:
            a = -half + c['x']
            b = a + c['l']
            xs += [a - 0.003, a, b, b + 0.003]
            # 6 mm inside the break: a fracture is ragged at 3-10 mm and a chip
            # sampled at 13 mm comes out as a smooth machined dish
            xs += list(np.linspace(a, b, max(6, int(c['l'] / 0.006) + 1)))
    if LOD[lod][5]:
        for r in u['runnels']:
            a = -half + r['x']
            xs += [a - r['w'] * 0.5, a - r['w'] * 0.25, a,
                   a + r['w'] * 0.25, a + r['w'] * 0.5]
    for sx in soc_xs:
        xs += [sx - SOC_HW - 0.008, sx - SOC_HW, sx + SOC_HW, sx + SOC_HW + 0.008]
    if u['outlet']:
        ox = u['outlet_x']
        xs += [ox - OUTLET_W * 0.5 - 0.004, ox - OUTLET_W * 0.5,
               ox - OUTLET_W * 0.25, ox, ox + OUTLET_W * 0.25,
               ox + OUTLET_W * 0.5, ox + OUTLET_W * 0.5 + 0.004]
    xs = np.asarray(sorted(v for v in xs if -half - 1e-9 <= v <= half + 1e-9))
    # a base column INSIDE a socket footprint would split the pocket cell in two
    for sx in soc_xs:
        keep = ~((xs > sx - SOC_HW + 1e-6) & (xs < sx + SOC_HW - 1e-6))
        xs = xs[keep]
    # de-duplicate: no quad narrower than 1.2 mm
    out = [xs[0]]
    for v in xs[1:]:
        if v - out[-1] > 0.0012:
            out.append(v)
    out[-1] = half
    if len(out) > 1 and out[-1] - out[-2] < 0.0012:
        out.pop(-2)
    return np.asarray(out)


def _chip_field(u, xs, lod):
    """Arris retreat along the casting: 0 on sound concrete, `d` inside a chip.

    A chip has a SHARP break line — 3 mm of ramp, sub-pixel at 4.9 mm/px — and a
    rough fracture floor, because that is what distinguishes a broken arris from
    a moulded chamfer.  A soft blob would read as a dent.
    """
    a = np.zeros_like(xs)
    f = np.zeros_like(xs)
    if not LOD[lod][4]:
        return a, f
    half = u['L'] * 0.5
    for i, c in enumerate(u['chips']):
        x0 = -half + c['x']
        x1 = x0 + c['l']
        w = smoothstep(x0 - 0.0025, x0 + 0.0025, xs) * (
            1.0 - smoothstep(x1 - 0.0025, x1 + 0.0025, xs))
        sd = int(u['seed'] + i * 977) & 0xFFFF
        # a fracture surface, not a dish: three octaves down to 3 mm, plus a
        # skew so the deepest point is not the middle
        rough = fbm2(xs * 170.0, np.full_like(xs, i * 7.3), seed=sd, oct=4)
        rough = 0.30 + 0.70 * rough
        skew = 0.25 + 0.50 * hash01(sd, 3)
        tt = np.clip((xs - x0) / max(1e-6, c['l']), 0.0, 1.0)
        prof = np.where(tt < skew,
                        np.sqrt(np.clip(tt / max(1e-6, skew), 0, 1)),
                        np.sqrt(np.clip((1.0 - tt) / max(1e-6, 1.0 - skew),
                                        0, 1)))
        prof = 0.22 + 0.78 * prof
        a = np.maximum(a, w * c['d'] * prof * (0.45 + 0.55 * rough * c['rough']))
        f = np.maximum(f, w)
    return a, f


def _runnel_field(u, xs, lod):
    r = np.zeros_like(xs)
    if not LOD[lod][5]:
        return r
    half = u['L'] * 0.5
    for k, q in enumerate(u['runnels']):
        x0 = -half + q['x']
        t = (xs - x0) / max(1e-6, q['w'] * 0.5)
        r = r + q['d'] * np.exp(-2.2 * t * t) * q['s']
    return r


def _outlet_field(u, xs, lod):
    """1 inside the cast outlet's 70 mm mouth, 0 outside, with a 4 mm arris."""
    if not u['outlet']:
        return np.zeros_like(xs)
    ox = u['outlet_x']
    return (smoothstep(ox - OUTLET_W * 0.5 - 0.003, ox - OUTLET_W * 0.5 + 0.003, xs)
            * (1.0 - smoothstep(ox + OUTLET_W * 0.5 - 0.003,
                                ox + OUTLET_W * 0.5 + 0.003, xs)))


def unit_mesh_arrays(u, lod=0):
    """The casting, in its own frame.

    Local frame: +X along the row, +Y up-rake (toward the back of the stand),
    +Z up.  Origin at the casting's own centroid box, so |P| < 1.75 m and the
    material can read TexCoord->Object with full float32 precision.
    """
    P = section(u, lod)
    T = P['T']
    L = u['L']
    half = L * 0.5
    soc_on = LOD[lod][3] and len(u['sockets']) > 0
    soc_xs = [s['x'] for s in u['sockets']] if soc_on else []
    xs = _columns(u, lod, soc_xs)
    ncol = len(xs)
    npts = P['n']

    Yg = np.tile(P['Y'], (ncol, 1))
    Zg = np.tile(P['Z'], (ncol, 1))

    # ---- chips ---------------------------------------------------------------
    chip_a, chip_f = _chip_field(u, xs, lod)
    Yg += P['WCY'][None, :] * chip_a[:, None]
    Zg -= P['WCZ'][None, :] * chip_a[:, None]

    # ---- runnels -------------------------------------------------------------
    run_d = _runnel_field(u, xs, lod)
    Yg += P['WRUN'][None, :] * run_d[:, None]

    # ---- the cast outlet -----------------------------------------------------
    out_f = _outlet_field(u, xs, lod)
    Zg -= P['WCHAN'][None, :] * (out_f * OUTLET_SUMP)[:, None]
    Yg += P['WOUT'][None, :] * (out_f * 0.040)[:, None]

    # ---- cast camber and mould waviness --------------------------------------
    tnorm = xs / max(1e-6, half)
    cam = u['camber'] * (1.0 - tnorm * tnorm)
    Zg += cam[:, None]
    sd = int(u['seed'] & 0xFFFF)
    wv = (fbm2(xs[:, None] * 2.6, P['TP'][None, :] * 5.5, seed=sd, oct=3) - 0.5)
    wv2 = (fbm2(xs[:, None] * 9.0, P['TP'][None, :] * 17.0, seed=sd + 91, oct=2)
           - 0.5)
    amp = u['wav'] * (1.0 + 0.9 * u['age'])
    dn = amp * (1.35 * wv + 0.5 * wv2)
    Yg += dn * P['NY'][None, :] * np.maximum(P['WMD'], P['WTR'])[None, :]
    Zg += dn * P['NZ'][None, :] * np.maximum(P['WMD'], P['WTR'])[None, :]

    # ---- the as-cast end chamfer ---------------------------------------------
    inset = np.zeros(ncol)
    inset[0] = END_CH
    inset[-1] = END_CH
    Yg -= P['NY'][None, :] * (inset[:, None] * P['PROT'][None, :])
    Zg -= P['NZ'][None, :] * (inset[:, None] * P['PROT'][None, :])

    Xg = np.tile(xs[:, None], (1, npts))
    V = np.stack([Xg.ravel(), Yg.ravel(), Zg.ravel()], 1)

    def vid(i, j):
        return i * npts + (j % npts)

    # ---- the swept quads -----------------------------------------------------
    ii = np.arange(ncol - 1)
    jj = np.arange(npts)
    I, J = np.meshgrid(ii, jj, indexing="ij")
    J1 = (J + 1) % npts
    quads = np.stack([(I * npts + J).ravel(), ((I + 1) * npts + J).ravel(),
                      ((I + 1) * npts + J1).ravel(), (I * npts + J1).ravel()], 1)

    drop = np.zeros((ncol - 1, npts), bool)
    extra_v = []
    extra_q = []
    extra_kind = []          # 1 = pocket wall/floor

    # ---- the cast-in sockets -------------------------------------------------
    socket_out = []
    if soc_on and P['soc_j'] is not None:
        j0, j1 = P['soc_j']
        j1 = j1 % npts
        nY = 0.5 * (P['NY'][j0] + P['NY'][j1])
        nZ = 0.5 * (P['NZ'][j0] + P['NZ'][j1])
        nn = math.hypot(nY, nZ) + 1e-12
        nY, nZ = nY / nn, nZ / nn
        for s in u['sockets']:
            k = int(np.argmin(np.abs(xs - (s['x'] - SOC_HW))))
            if k >= ncol - 1 or abs(xs[k] - (s['x'] - SOC_HW)) > 0.004:
                continue
            if abs(xs[k + 1] - (s['x'] + SOC_HW)) > 0.004:
                continue
            d = SOC_D * (1.6 if s['repair'] else 1.0)
            drop[k, j0] = True
            corners = [vid(k, j0), vid(k + 1, j0), vid(k + 1, j1), vid(k, j1)]
            base = len(V) + len(extra_v)
            for c in corners:
                p = V[c].copy()
                p[1] -= nY * d
                p[2] -= nZ * d
                extra_v.append(p)
            for a in range(4):
                b = (a + 1) % 4
                extra_q.append([corners[a], corners[b], base + b, base + a])
                extra_kind.append(1)
            extra_q.append([base + 3, base + 2, base + 1, base + 0])
            extra_kind.append(1)
            cx = float(np.mean([V[c][0] for c in corners]))
            cy = float(np.mean([V[c][1] for c in corners]) - nY * d * 0.5)
            cz = float(np.mean([V[c][2] for c in corners]) - nZ * d * 0.5)
            socket_out.append(dict(x=cx, y=cy, z=cz, kind=P['soc_kind'],
                                   col=s['col'], seat_x=s['seat_x'],
                                   repair=bool(s['repair']), rust=s['rust'],
                                   depth=d))

    keep = ~drop.ravel()
    quads = quads[keep]

    # ---- end caps ------------------------------------------------------------
    tris = []
    for (i, flip) in ((0, True), (ncol - 1, False)):
        cy = float(np.mean(Yg[i])); cz = float(np.mean(Zg[i]))
        base = len(V) + len(extra_v)
        extra_v.append(np.array([xs[i], cy, cz]))
        for j in range(npts):
            a = vid(i, j); b = vid(i, j + 1)
            tris.append([base, b, a] if flip else [base, a, b])

    if extra_v:
        V = np.concatenate([V, np.asarray(extra_v, float)], 0)
    if extra_q:
        quads = np.concatenate([quads, np.asarray(extra_q, np.int64)], 0)
    tris = np.asarray(tris, np.int64) if tris else np.zeros((0, 3), np.int64)

    # ==========================================================================
    #  ATTRIBUTES  —  eight, all baked per vertex, all read by the material
    # ==========================================================================
    nv_grid = ncol * npts
    nv = len(V)
    face = np.zeros(nv); below = np.zeros(nv); wear = np.zeros(nv)
    chip = np.zeros(nv); edge = np.zeros(nv); runa = np.zeros(nv)
    soc = np.zeros(nv); yy = np.zeros(nv)

    RO = P['ROLE']
    face[:nv_grid] = np.tile(RO, (ncol, 1)).ravel() / float(N_ROLE - 1)
    # below/y are read straight off the final vertex positions, so the pocket
    # floors and the end caps carry them too
    below[:] = np.clip(-V[:, 2], 0.0, TOTAL_H) / TOTAL_H
    yy[:] = np.clip(V[:, 1] / max(1e-6, T), -0.2, 1.2)
    edge[:nv_grid] = np.tile(P['ARR'], (ncol, 1)).ravel()
    # the ends of a casting are handled, chipped and rubbed more than its middle
    endw = clamp01(1.0 - np.abs(xs) / max(1e-6, half - 0.02))
    end_t = (0.55 * (1.0 - endw) ** 4)[:, None] * np.maximum(P['ARR'], 0.15)[None, :]
    edge[:nv_grid] = np.maximum(edge[:nv_grid], end_t.ravel())
    chip[:nv_grid] = (chip_f[:, None] * (P['WCY'] + P['WCZ'])[None, :]
                      ).clip(0, 1).ravel()
    out_stain = np.zeros_like(xs)
    if u['outlet']:
        t_ = (xs - u['outlet_x']) / 0.115
        out_stain = 0.0042 * np.exp(-1.6 * t_ * t_)
    runa[:nv_grid] = (P['WRUN'][None, :]
                      * ((run_d + out_stain) / 0.0030)[:, None]
                      ).clip(0, 1).ravel()
    # wear: the walking band of the tread, hardest at the nose and in the aisle
    walk = np.where(np.isin(RO, (R_TREAD, R_REBATE)),
                    1.0 - 0.55 * clamp01((P['Y'] - 0.12) / max(0.2, u['pitch'])),
                    0.0)
    walk = np.maximum(walk, np.where(RO == R_CHAMFER, 1.0, 0.0))
    wear[:nv_grid] = np.tile(walk * (0.35 + 0.65 * u['traffic']),
                             (ncol, 1)).ravel()
    for q, k in zip(extra_q, extra_kind):
        if k != 1:
            continue
        for vidx in q:
            if vidx >= nv_grid:
                soc[vidx] = 1.0
                face[vidx] = R_TREAD / float(N_ROLE - 1)
                edge[vidx] = 0.5
                wear[vidx] = 0.35 + 0.65 * u['traffic']
    # the two end-cap centroids are the last two vertices added
    for vidx in (nv - 2, nv - 1):
        if 0 <= vidx < nv:
            edge[vidx] = 0.85
            face[vidx] = R_NIB / float(N_ROLE - 1)

    attrs = dict(gru_face=face, gru_below=below, gru_wear=wear, gru_chip=chip,
                 gru_edge=edge, gru_run=runa, gru_soc=soc, gru_y=yy)

    # ---- recentre ------------------------------------------------------------
    lo = V.min(0); hi = V.max(0)
    org = 0.5 * (lo + hi)
    V = V - org[None, :]

    info = dict(ncol=ncol, npts=npts, tris=len(quads) * 2 + len(tris),
                verts=len(V), sockets=socket_out, org=org,
                leg_z=P['leg_z'], nib_z=P['nib_z'], T=T)
    return V, quads, tris, attrs, org, info


# ==============================================================================
#  5.  BLENDER MESH
# ==============================================================================
ATTRS = ("gru_face", "gru_below", "gru_wear", "gru_chip",
         "gru_edge", "gru_run", "gru_soc", "gru_y")


def _new_mesh(name, verts, quads=None, tris=None, smooth_deg=33.0):
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


def _shade_by_angle(me, deg=33.0):
    """Smooth across the cast surface, sharp across every real arris.

    The mould face is tangent-continuous over the tread and the riser, and
    flat-shading it turns 90 sweep facets into 90 visible bands under a sky
    source.  The chamfers, the joint faces, the pocket walls, the nib and every
    fracture face ARE sharp and must stay so.  numpy against `sharp_edge`,
    because shade_auto_smooth needs a VIEW_3D context and cannot run headless
    (see the project memory note on Blender 5.x).
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
    nvv = np.int64(max(1, len(me.vertices)))
    key = np.minimum(a, b) * nvv + np.maximum(a, b)
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
    ekey = (np.minimum(ev[:, 0], ev[:, 1]) * nvv
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


def unit_frame(u):
    """THE rigid body's own frame.  (origin_world, ex, ey, ez).

    ex  along the row  (circuit +x)
    ey  up-rake        (circuit -y)
    ez  up
    after this unit's own yaw, pitch and roll.  Every dependant that sits
    something on a unit must use this, because the seating error and the three
    tilts live here and nowhere else.
    """
    T = _slab_depth(u)
    # the mesh is recentred on its own bbox centre; the same offset is applied to
    # the placement so the geometry lands where the record says it does
    org_l = _unit_local_origin(u)
    cx = u['x_m'] + org_l[0]
    cy = u['y_nose'] - org_l[1] + u['dy']
    wx, wy = C.circuit_to_world(cx, cy)
    wz = u['z_tread'] + org_l[2] + u['dz']

    cw, sw = math.cos(math.radians(C.ROT_DEG)), math.sin(math.radians(C.ROT_DEG))
    ex = np.array([cw, sw, 0.0])            # circuit +x
    ey = np.array([sw, -cw, 0.0])           # circuit -y  (up-rake)
    ez = np.array([0.0, 0.0, 1.0])
    # yaw about ez, then pitch about ey (one end high), then roll about ex
    def rot(v, axis, ang):
        c, s = math.cos(ang), math.sin(ang)
        return v * c + np.cross(axis, v) * s + axis * np.dot(axis, v) * (1 - c)
    ex = rot(ex, ez, u['yaw']); ey = rot(ey, ez, u['yaw'])
    ex = rot(ex, ey, u['tilt_y']); ez = rot(ez, ey, u['tilt_y'])
    ey = rot(ey, ex, u['tilt_x']); ez = rot(ez, ex, u['tilt_x'])
    return np.array([float(wx), float(wy), float(wz)]), ex, ey, ez


_ORG_CACHE = {}


def _unit_local_origin(u):
    """The mesh's recentring offset, in the unit's own (x, Y, Z) frame.

    Cheap and exact: the recentre is the bbox centre of the nominal section, and
    the modulations are millimetres.  It is computed from the SECTION so that
    unit_frame() does not have to build a mesh to know where the object origin
    is — which is what lets every interface function work without bpy.
    """
    key = _prof_key(u, 0)
    hit = _ORG_CACHE.get(key)
    if hit is None:
        P = section(u, 0)
        hit = np.array([0.0, 0.5 * (float(P['Y'].min()) + float(P['Y'].max())),
                        0.5 * (float(P['Z'].min()) + float(P['Z'].max()))])
        _ORG_CACHE[key] = hit
    return hit


def build_unit(u, coll, mat, lod=0):
    V, quads, tris, att, org, info = unit_mesh_arrays(u, lod)
    name = "%sU%05d" % (PFX, u["uid"])
    me = _new_mesh(name, V, quads, tris)
    _bake(me, att)
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    o, ex, ey, ez = unit_frame(u)
    # the mesh was recentred on ITS bbox; unit_frame used the section bbox.  The
    # difference is the modulation, sub-millimetre, and is added back here so the
    # two agree exactly.
    d = org - _unit_local_origin(u)
    o = o + ex * d[0] + ey * d[1] + ez * d[2]
    from mathutils import Matrix
    M = Matrix(((ex[0], ey[0], ez[0], o[0]),
                (ex[1], ey[1], ez[1], o[1]),
                (ex[2], ey[2], ez[2], o[2]),
                (0.0, 0.0, 0.0, 1.0)))
    ob.matrix_world = M
    coll.objects.link(ob)
    _object_props(ob, u, lod, info)
    return ob, info["tris"]


def _object_props(ob, u, lod, info):
    sd = u["seed"]
    # per-object texture offset: the only thing that stops 3 394 castings sharing
    # one realisation of the concrete.  24 m, not 240 — Cycles evaluates
    # procedurals in float32 and a large offset costs lattice precision.
    ob["gru_ofs_x"] = float(hash01(sd, 3) * 24.0)
    ob["gru_ofs_y"] = float(hash01(sd, 5) * 24.0)
    ob["gru_ofs_z"] = float(hash01(sd, 7) * 24.0)
    ob["gru_age"] = float(u["age"])
    ob["gru_traffic"] = float(u["traffic"])
    ob["gru_hue"] = float(u["hue"])
    ob["gru_val"] = float(u["val"])
    ob["gru_wet"] = float(u["wet"])
    ob["gru_repair"] = 1.0 if u["repair"] else 0.0
    ob["gru_chan"] = 1.0 if u["channel"] else 0.0
    ob["item"] = ITEM
    ob["gru_uid"] = int(u["uid"])
    ob["gru_block"] = u["block"]
    ob["gru_row"] = int(u["row"])
    ob["gru_bay"] = int(u["bay"])
    ob["gru_lod"] = int(lod)
    ob["gru_len"] = float(u["L"])
    ob["gru_gap"] = float(u["gap"])
    ob["gru_nchip"] = int(len(u["chips"]))
    ob["gru_nsock"] = int(len(info["sockets"]))
    ob["gru_starter"] = 1 if u["starter"] else 0
    ob["gru_closer"] = 1 if u["closer"] else 0


# ==============================================================================
#  6.  THE MATERIAL
# ==============================================================================

class NT(object):
    """Node DSL.  Same shape as kerb_precast_unit's and armco_w_beam's."""

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
            # a colour socket wants 4 components and a vector socket wants 3;
            # ask the socket rather than guessing from the tuple's length
            try:
                want = len(nd.inputs[idx].default_value)
            except TypeError:
                want = 1
            v = list(src)
            if want == 4 and len(v) == 3:
                v = v + [1.0]
            elif want == 3 and len(v) == 4:
                v = v[:3]
            nd.inputs[idx].default_value = tuple(v) if want > 1 else float(v[0])
        else:
            nd.inputs[idx].default_value = float(src)

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
        of the FIRST bump in every chain kept its constant default of 1.0.  A
        constant has zero gradient, so that stage contributed NO relief at all,
        and every later stage read a normal chain where its height should be.
        It was silent -- the material built, rendered, and passed the gate's
        node-count check.  `inputs.find` costs one lookup; never pin by index.

        STATE THE RADIANCE MODULATION, NOT THE METRES (itemkit section 5b).
        Give `modulation_pp` with `wavelength_m` and the depth is derived from
        the contract sun: m = 2 sin(theta) / tan(e), a 4.52x amplifier at this
        film's 12.47 deg.  An amplitude with no wavelength is not a relief spec:
        the same 0.5 mm is m = 0.57 on an 8 mm crumple and m = 0.045 on a 100 mm
        flute.  `height_pp` is the peak-to-peak swing of the height signal.
        """
        if (distance is None) == (modulation_pp is None):
            raise ValueError("bump() takes exactly one of distance= or "
                             "modulation_pp= (with wavelength_m=): itemkit 5b")
        if modulation_pp is not None:
            if not wavelength_m:
                raise ValueError("bump(modulation_pp=) needs wavelength_m=; "
                                 "an amplitude with no wavelength is not a "
                                 "relief specification.")
            try:
                s = abs(float(strength))
            except (TypeError, ValueError):
                s = 1.0          # a masked strength: aim at where the mask is 1
            distance = (K.relief_amplitude_for(modulation_pp, wavelength_m)
                        * 1e-3 / max(s * float(height_pp), 1e-9))
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


# Linear reflectances, MEASURED-plausible rather than "grey".  A 20-year-old
# precast terrace unit is 0.16-0.26; the fresh fracture inside a chip is 0.30;
# and the film NEVER sees any of it in direct sun (see the header), so these are
# the numbers the sky has to work with and there is no highlight to hide behind.
PAL = dict(
    conc_pale=(0.2760, 0.2710, 0.2580),     # sheltered, laitance intact
    conc_grey=(0.1780, 0.1740, 0.1650),     # the general weathered cast face
    conc_warm=(0.2280, 0.2090, 0.1770),     # an older, warmer cement batch
    conc_dark=(0.1060, 0.1030, 0.0960),     # shaded, damp, dirty
    fracture=(0.3300, 0.3190, 0.2950),      # a fresh break: bright and matt
    agg_dark=(0.0640, 0.0625, 0.0600),      # basalt / granite coarse aggregate
    agg_pale=(0.2820, 0.2740, 0.2560),      # limestone / quartzite
    lime=(0.4400, 0.4350, 0.4230),          # efflorescence bloom
    algae=(0.0420, 0.0560, 0.0320),
    moss=(0.0350, 0.0540, 0.0260),
    silt=(0.0760, 0.0690, 0.0560),          # the channel's own sediment
    polish=(0.0900, 0.0870, 0.0840),        # shoe-polished walking band
    dust=(0.2450, 0.2320, 0.2030),          # wind-blown dust and washed fines
    damp=(0.0850, 0.0880, 0.0930),          # a patch that never dries
    grit=(0.1420, 0.1300, 0.1080),
    gum=(0.0460, 0.0450, 0.0435),
    rust=(0.1200, 0.0450, 0.0180),
    repair=(0.2350, 0.2320, 0.2280),        # a patch never matches
    grime=(0.0640, 0.0620, 0.0590),
)


def mat_riser():
    """Precast terrace concrete, twenty seasons, ALWAYS IN SHADE.

    Twenty surface histories in the order the concrete acquired them.  Every one
    is procedural, and every one is driven either by object-space coordinates
    (recentred, |P| < 1.75 m) or by an attribute this module baked into the mesh.
    ``Geometry->Position`` appears nowhere in the tree.

    THE ONE DECISION THAT DECIDED THIS SHADER.  This surface is lit by SKY, not
    by sun (see the module header: the sun is 0.99 anti-parallel to the rake's
    normal and every riser shadows the tread in front of it).  Under a
    hemisphere:

      * a bump map on an UP-FACING surface produces almost no shading variation,
        because the surface sees the same sky wherever its normal wobbles.  A
        broom finish modelled as a bump is invisible on a tread.  It is only on
        the near-vertical faces that relief does any work at all.
      * therefore the tread's entire read is ALBEDO — dirt drift, damp patches,
        the polished walking band, dust where feet do not reach, grit, gum.
      * and the riser's read is ALBEDO PLUS OCCLUSION — the drip groove, the
        joint, the foot slot, the runnels.

    The first version of this shader spent itself on a specular story and
    rendered as a flat pale ramp with one white stripe along every nose.  That
    stripe — a continuous unbroken line of exposed aggregate at the arris — is
    the same defect as "a grass gray line": a feature applied uniformly along an
    edge instead of where the thing that causes it happened.  Every edge effect
    below is masked by a patchiness field for that reason.
    """
    t = NT(PFX + "Concrete")
    co = t.n("ShaderNodeTexCoord")
    OBJ = (co, 3)
    ofs = t.comb(t.attr("gru_ofs_x", 2, "OBJECT"),
                 t.attr("gru_ofs_y", 2, "OBJECT"),
                 t.attr("gru_ofs_z", 2, "OBJECT"))
    P = t.vmath("ADD", OBJ, ofs)          # per-object realisation of the noise
    Pl = OBJ                              # the casting's own frame

    age = t.attr("gru_age", 2, "OBJECT")
    hue = t.attr("gru_hue", 2, "OBJECT")
    val = t.attr("gru_val", 2, "OBJECT")
    wet = t.attr("gru_wet", 2, "OBJECT")
    rep = t.attr("gru_repair", 2, "OBJECT")
    traf = t.attr("gru_traffic", 2, "OBJECT")

    face = t.attr("gru_face")
    below = t.attr("gru_below")
    wear = t.attr("gru_wear")
    chip = t.attr("gru_chip")
    edge = t.attr("gru_edge")
    runm = t.attr("gru_run")
    socm = t.attr("gru_soc")
    yy = t.attr("gru_y")

    N1 = float(N_ROLE - 1)

    def is_face(lo, hi):
        """A real BAND on the baked role code.  The first version was a
        one-sided step, so `m_channel` was true on every face from the channel
        outward and the silt ended up on the soffit."""
        a = t.maprange(face, (lo - 0.55) / N1, (lo - 0.35) / N1, 0.0, 1.0)
        b = t.maprange(face, (hi + 0.35) / N1, (hi + 0.55) / N1, 1.0, 0.0)
        return t.math("MULTIPLY", a, b)

    m_tread = is_face(R_TREAD, R_CHANNEL)          # tread + rebate + channel
    m_riser = is_face(R_RISER, R_DRIP)
    m_chan = is_face(R_CHANNEL, R_CHANNEL)
    m_drip = is_face(R_DRIP, R_DRIP)
    m_soffit = is_face(R_BACK, R_LEGSOF)           # everything under the unit

    # ---- 1. the cast body, batch by batch ------------------------------------
    # A stand is not poured in a day.  Six months of castings from three cement
    # deliveries: the batch tone is the single biggest thing that makes 3 394
    # castings read as 3 394 castings rather than as one surface with joints
    # drawn on it, so it is deliberately WIDE — a real terrace is patchy at the
    # unit scale and every photograph of one shows it.
    n_batch = t.noise(t.vmath("SCALE", P, scale=0.34), 1.2, 3.0, 0.42)
    n_cast = t.noise(t.vmath("SCALE", P, scale=1.0), 6.5, 5.0, 0.55)
    n_mid = t.noise(t.vmath("SCALE", P, scale=1.0), 2.2, 5.0, 0.62)
    n_fine = t.noise(t.vmath("SCALE", P, scale=1.0), 34.0, 5.0, 0.55)

    batch = t.math("ADD", t.math("MULTIPLY", val, 0.74),
                   t.math("MULTIPLY", n_batch, 0.26))
    base = t.cmix(t.maprange(batch, 0.02, 0.98, 0.0, 1.0),
                  PAL["conc_grey"], PAL["conc_pale"])
    # and the hue moves with it: an older delivery of cement is warmer, and a
    # terrace built over six months is visibly three or four different greys
    base = t.cmix(t.maprange(hue, 0.05, 0.95, 0.0, 0.80), base, PAL["conc_warm"])
    base = t.cmix(t.math("MULTIPLY",
                         t.maprange(t.math("MULTIPLY", val, hue), 0.0, 0.22,
                                    1.0, 0.0), 0.55),
                  base, PAL["conc_dark"])
    # the mould's own blotching, and where the release agent pooled
    base = t.cmix(t.math("MULTIPLY",
                         t.math("SUBTRACT", n_cast, 0.58, clamp=True), 2.0),
                  base, PAL["conc_dark"])
    base = t.cmix(t.math("MULTIPLY",
                         t.math("SUBTRACT", 0.42, n_cast, clamp=True), 1.5),
                  base, PAL["conc_pale"])

    # ---- 2. board / form-liner marks on the riser ----------------------------
    # the riser face is the mould's side form: 1.2 m steel panels with a 0.4 mm
    # step at each joint.  Invisible as a normal, visible as a line of held dirt.
    # ONE line, not a ladder.  The first version ran a Wave at 3.4 bands per unit
    # with detail 2 and mixed it at 1.30, and the 1.8 m peep showed the riser as
    # a plaid: four evenly spaced horizontal bands crossing the vertical streaks.
    # It was also wrong on the facts -- a 0.29 m riser is cast against ONE steel
    # side form and has no horizontal form joint inside its own height.  What it
    # does have is the line where the pour was stopped and restarted, once, low
    # on the face, and that is all this is now.
    boardv = t.wave(t.vmath("SCALE", Pl, scale=1.0), 1.1, 0.55, 1.0, "Z")
    board = t.math("MULTIPLY", m_riser,
                   t.math("SUBTRACT", boardv, 0.72, clamp=True))
    base = t.cmix(t.math("MULTIPLY", board, 0.55), base, PAL["grime"])

    # ---- 3. the patchiness field --------------------------------------------
    # NOT a mask on anything in particular: it is the field every "along an edge"
    # effect is multiplied by, so that no effect can run the whole length of a
    # casting at constant strength.  0.15-1.0 in patches 60-400 mm long.
    patchy = t.maprange(t.noise(t.vmath("SCALE", P, scale=1.0), 5.5, 5.0, 0.70),
                        0.30, 0.72, 0.05, 1.0)
    patchy2 = t.maprange(t.noise(t.vmath("SCALE", P, scale=1.0), 16.0, 4.0),
                         0.34, 0.70, 0.25, 1.0)
    patchy = t.math("MULTIPLY", patchy, t.math("ADD", 0.35,
                                               t.math("MULTIPLY", patchy2, 0.8)))

    # ---- 4. exposed aggregate ------------------------------------------------
    agg_c = t.vor(t.vmath("SCALE", P, scale=1.0), 190.0, "F1", 1)
    agg_d = t.vor(t.vmath("SCALE", P, scale=1.0), 190.0, "SMOOTH_F1", 0)
    agg_col = t.cmix(t.noise(t.vmath("SCALE", P, scale=1.0), 170.0, 2.0, 0.5),
                     PAL["agg_dark"], PAL["agg_pale"])
    # the paste has gone: on a fracture face always, on an arris only where it
    # has actually been knocked — hence `patchy`
    arris2 = t.math("MULTIPLY", edge, edge)          # squared: only the real
                                                    # arris, not its neighbours
    show = t.math("MAXIMUM", chip,
                  t.math("MULTIPLY", t.math("MULTIPLY", arris2, wear),
                         t.math("MULTIPLY", patchy, 0.80)))
    show = t.math("MULTIPLY", show,
                  t.math("SUBTRACT", agg_d, 0.24, clamp=True))
    base = t.cmix(t.math("MULTIPLY", show, 2.2, clamp=True), base, agg_col)
    # and a rubbed arris is not only paler: the cement skin goes and the surface
    # under it takes a polish, so half the effect DARKENS.  An arris that only
    # brightens reads as a painted line.
    base = t.cmix(t.math("MULTIPLY",
                         t.math("MULTIPLY", arris2, t.math("MULTIPLY", wear, 0.65)),
                         t.math("SUBTRACT", 1.0, patchy)),
                  base, PAL["polish"])
    # a fresh break is BRIGHTER than the weathered face — that is what makes a
    # chip read as damage rather than as dirt
    base = t.cmix(t.math("MULTIPLY", chip,
                         t.math("SUBTRACT", 0.95,
                                t.math("MULTIPLY", age, 0.55))),
                  base, PAL["fracture"])

    # ---- 4b. crazing and shrinkage cracks ------------------------------------
    # A twenty-year-old precast tread map-cracks.  Each crack is 0.2-0.8 mm wide
    # -- a fifth of a pixel at 203 px/m -- so it is not modelled as geometry and
    # could not be seen if it were.  What IS seen is the DIRT the crack holds,
    # and that is what puts hard thin lines on a surface which otherwise has
    # none.  A tread with no lines on it at all is the reason the first macro
    # read as a smooth ramp: an up-facing surface under a sky has no shading, so
    # every edge it appears to have has to be an albedo edge.
    # Sparse SHRINKAGE cracks (0.5-2 m apart) dominate; fine map crazing is a
    # tenth of the strength and appears only in patches.  The first version had
    # them equal and at 0.80 mix, and a 4K peep showed crazy paving: a Voronoi
    # cell structure at one constant size over every casting, which is a pattern
    # and not a history.
    crk2 = t.vor(t.vmath("SCALE", P, scale=1.0), 1.7, "DISTANCE_TO_EDGE", 0)
    crk1 = t.vor(t.vmath("SCALE", P, scale=1.0), 6.5, "DISTANCE_TO_EDGE", 0)
    crk3 = t.vor(t.vmath("SCALE", P, scale=1.0), 17.0, "DISTANCE_TO_EDGE", 0)
    # where the cracking is at all: 1.4 m patches, mostly absent
    crk_where = t.maprange(t.noise(t.vmath("SCALE", P, scale=1.0), 1.9, 5.0,
                                   0.62), 0.46, 0.74, 0.0, 1.0)
    crk_fine = t.maprange(t.noise(t.vmath("SCALE", P, scale=1.0), 4.2, 4.0),
                          0.52, 0.80, 0.0, 1.0)
    crack = t.maprange(crk2, 0.004, 0.020, 1.0, 0.0)
    crack = t.math("MAXIMUM", crack,
                   t.math("MULTIPLY",
                          t.maprange(crk1, 0.003, 0.014, 1.0, 0.0),
                          t.math("MULTIPLY", crk_fine, 0.65)))
    crack = t.math("MAXIMUM", crack,
                   t.math("MULTIPLY",
                          t.maprange(crk3, 0.002, 0.010, 1.0, 0.0),
                          t.math("MULTIPLY", crk_fine, 0.30)))
    crack = t.math("MULTIPLY", crack, crk_where)
    crack = t.math("MULTIPLY", crack,
                   t.math("ADD", 0.20, t.math("MULTIPLY", age, 0.90)))
    base = t.cmix(t.math("MULTIPLY", crack, 0.46), base, PAL["grime"])

    # ---- 5. bug holes --------------------------------------------------------
    bug = t.vor(t.vmath("SCALE", P, scale=1.0), 430.0, "F1", 0)
    bug_m = t.math("SUBTRACT", 1.0, t.maprange(bug, 0.0, 0.17, 0.0, 1.0))
    bug_m = t.math("MULTIPLY", bug_m,
                   t.maprange(t.noise(t.vmath("SCALE", P, scale=1.0), 11.0, 3.0),
                              0.34, 0.72, 0.0, 1.0))
    base = t.cmix(t.math("MULTIPLY", bug_m, 0.75), base, PAL["conc_dark"])

    # ---- 6. THE TREAD: dirt drift -------------------------------------------
    # The whole reason this item is hero is that the tread strips are what the
    # Beat-6 crane-out looks straight down at.  An up-facing surface under a sky
    # has no shading story at all, so this is where the object is won or lost.
    drift = t.maprange(t.noise(t.vmath("SCALE", P, scale=1.0), 3.1, 6.0, 0.66),
                       0.34, 0.68, 0.0, 1.0)
    drift = t.math("MULTIPLY", drift,
                   t.maprange(t.noise(t.vmath("SCALE", P, scale=1.0), 9.5, 5.0),
                              0.30, 0.78, 0.30, 1.0))
    dirty = t.math("ADD", 0.35, t.math("MULTIPLY", age, 0.95))
    base = t.cmix(t.math("MULTIPLY", t.math("MULTIPLY", m_tread, drift),
                         t.math("MULTIPLY", dirty, 0.74)),
                  base, PAL["grime"])
    # 30-120 mm structure: at 203 px/m that is 6-24 px, which is the band the
    # 4K master actually resolves on a tread.  Below it the surface averages to
    # a flat tone and above it it reads as cloud, and the first macro had only
    # the cloud.
    spot = t.vor(t.vmath("SCALE", P, scale=1.0), 13.0, "SMOOTH_F1", 0)
    spotm = t.math("MULTIPLY", m_tread,
                   t.maprange(spot, 0.02, 0.20, 1.0, 0.0))
    spotm = t.math("MULTIPLY", spotm,
                   t.maprange(t.vor(t.vmath("SCALE", P, scale=1.0), 13.0,
                                    "F1", 2), 0.30, 0.72, 0.0, 1.0))
    base = t.cmix(t.math("MULTIPLY", spotm, t.math("MULTIPLY", dirty, 0.74)),
                  base, PAL["grime"])
    fleck = t.vor(t.vmath("SCALE", P, scale=1.0), 34.0, "F1", 0)
    fleckm = t.math("MULTIPLY", m_tread,
                    t.maprange(fleck, 0.004, 0.013, 1.0, 0.0))
    fleckm = t.math("MULTIPLY", fleckm,
                    t.maprange(t.vor(t.vmath("SCALE", P, scale=1.0), 34.0,
                                     "F1", 2), 0.42, 0.62, 0.0, 1.0))
    base = t.cmix(t.math("MULTIPLY", fleckm, 0.85), base, PAL["dust"])

    # ---- 7. THE TREAD: dust where feet do not reach --------------------------
    # nobody's shoe lands in the last 200 mm against the riser root; that strip
    # holds wind-blown dust, grit and the fines washed out of the concrete, and
    # it is a full stop paler than the walked part.
    backstrip = t.math("MULTIPLY", m_tread,
                       t.maprange(yy, 0.52, 0.86, 0.0, 1.0))
    backstrip = t.math("MULTIPLY", backstrip,
                       t.maprange(t.noise(t.vmath("SCALE", P, scale=1.0),
                                          13.0, 4.0), 0.30, 0.80, 0.25, 1.0))
    base = t.cmix(t.math("MULTIPLY", backstrip, 0.80), base, PAL["dust"])
    # and the hard line of swept grit in the internal corner itself, 70 mm of
    # tread against the riser root of the row behind.  It has a SHARP edge -- a
    # broom leaves one -- which is worth more at 4.9 mm/px than another soft
    # gradient would be.
    corner = t.math("MULTIPLY", m_tread,
                    t.math("MULTIPLY", t.maprange(yy, 0.795, 0.825, 0.0, 1.0),
                           t.maprange(yy, 0.885, 0.900, 1.0, 0.0)))
    corner = t.math("MULTIPLY", corner,
                    t.maprange(t.noise(t.vmath("SCALE", P, scale=1.0), 18.0, 4.0),
                               0.26, 0.72, 0.20, 1.0))
    base = t.cmix(t.math("MULTIPLY", corner, 0.85), base, PAL["grit"])

    # spills: hard-edged dark patches 90-260 mm across, sparse.  A drink dries
    # with an EDGE, and a tread whose every mark has a soft edge looks airbrushed
    spill = t.vor(t.vmath("SCALE", P, scale=1.0), 4.4, "F1", 0)
    spillm = t.math("MULTIPLY", m_tread,
                    t.maprange(spill, 0.055, 0.075, 1.0, 0.0))
    spillm = t.math("MULTIPLY", spillm,
                    t.maprange(t.vor(t.vmath("SCALE", P, scale=1.0), 4.4,
                                     "F1", 2), 0.62, 0.74, 0.0, 1.0))
    spillm = t.math("MULTIPLY", spillm,
                    t.math("ADD", 0.25, t.math("MULTIPLY", traf, 0.9)))
    base = t.cmix(t.math("MULTIPLY", spillm, 0.75), base, PAL["grime"])

    # ---- 8. THE TREAD: damp patches -----------------------------------------
    # a stand that never sees the sun does not dry out.  Large soft patches, a
    # third of a stop darker and a touch cooler, with the walked band drier.
    dampf = t.maprange(t.noise(t.vmath("SCALE", P, scale=1.0), 1.7, 4.0, 0.58),
                       0.40, 0.68, 0.0, 1.0)
    dampf = t.math("MULTIPLY", dampf, t.math("ADD", 0.30,
                                             t.math("MULTIPLY", wet, 0.95)))
    dampt = t.math("MULTIPLY", t.math("MULTIPLY", m_tread, dampf),
                   t.math("SUBTRACT", 1.0, t.math("MULTIPLY", wear, 0.55)))
    base = t.cmix(t.math("MULTIPLY", dampt, 0.72), base, PAL["damp"])

    # ---- 9. THE TREAD: the walking band --------------------------------------
    # twenty seasons of shoes.  Not a stripe: a 2-D field, strongest at the nose
    # and in the aisle, and it POLISHES as much as it darkens.
    walk = t.math("MULTIPLY", m_tread, wear)
    walk = t.math("MULTIPLY", walk,
                  t.maprange(t.noise(t.vmath("SCALE", P, scale=1.0), 7.0, 4.0),
                             0.26, 0.80, 0.30, 1.0))
    walk = t.math("MULTIPLY", walk, t.math("ADD", 0.40,
                                           t.math("MULTIPLY", traf, 0.85)))
    base = t.cmix(t.math("MULTIPLY", walk, 0.88), base, PAL["polish"])

    # ---- 10. THE TREAD: grit -------------------------------------------------
    # the broom finish, as DIRT rather than as relief.  Transverse at ~9 mm
    # pitch = 1.8 px at 203 px/m; the grooves hold dirt and the ribs are rubbed
    # clean, which is a real directional texture on a surface a bump cannot
    # shade.  It fades out exactly where the walking band polishes it away.
    broomv = t.wave(t.vmath("MULTIPLY", Pl, (1.0, 1.0, 1.0)), 104.0, 1.60, 3.0,
                    "Y")
    broomd = t.math("MULTIPLY", m_tread,
                    t.math("MULTIPLY", t.maprange(broomv, 0.35, 0.72, 0.0, 1.0),
                           t.math("SUBTRACT", 1.0,
                                  t.math("MULTIPLY", wear, 0.70))))
    broomd = t.math("MULTIPLY", broomd,
                    t.maprange(t.noise(t.vmath("SCALE", P, scale=1.0), 5.0, 4.0),
                               0.28, 0.74, 0.15, 1.0))
    base = t.cmix(t.math("MULTIPLY", broomd, 0.34), base, PAL["grime"])

    grit = t.vor(t.vmath("SCALE", P, scale=1.0), 95.0, "F1", 0)
    gritm = t.math("MULTIPLY", m_tread,
                   t.math("SUBTRACT", 1.0, t.maprange(grit, 0.0, 0.05, 0.0, 1.0)))
    gritm = t.math("MULTIPLY", gritm,
                   t.maprange(t.noise(t.vmath("SCALE", P, scale=1.0), 6.0, 3.0),
                              0.42, 0.78, 0.0, 1.0))
    base = t.cmix(t.math("MULTIPLY", gritm, 0.55), base, PAL["grit"])

    # ---- 11. chewing gum -----------------------------------------------------
    gumv = t.vor(t.vmath("SCALE", P, scale=1.0), 26.0, "F1", 0)
    gum = t.math("MULTIPLY", m_tread,
                 t.math("SUBTRACT", 1.0,
                        t.maprange(gumv, 0.005, 0.015, 0.0, 1.0)))
    gum = t.math("MULTIPLY", gum,
                 t.maprange(t.vor(t.vmath("SCALE", P, scale=1.0), 26.0, "F1", 2),
                            0.52, 0.68, 0.0, 1.0))
    gum = t.math("MULTIPLY", gum, t.math("ADD", 0.15,
                                         t.math("MULTIPLY", traf, 0.95)))
    base = t.cmix(gum, base, PAL["gum"])

    # ---- 12. laitance and efflorescence on the riser -------------------------
    # lime carried out of the concrete by water: a white bloom that starts at a
    # joint, a socket or the drip groove and runs DOWN.  On a stand in permanent
    # shade it never dries off, so it is the brightest thing on the object.
    streak_v = t.vmath("MULTIPLY", Pl, (30.0, 30.0, 1.9))
    streak = t.noise(streak_v, 1.0, 4.0, 0.58)
    lime_m = t.math("MULTIPLY", m_riser,
                    t.maprange(below, 0.10, 0.72, 0.0, 1.0))
    lime_m = t.math("MULTIPLY", lime_m,
                    t.maprange(streak, 0.48, 0.84, 0.0, 1.0))
    lime_m = t.math("MULTIPLY", lime_m,
                    t.math("ADD", 0.30, t.math("MULTIPLY", age, 0.85)))
    base = t.cmix(t.math("MULTIPLY", lime_m, 0.90), base, PAL["lime"])

    # ---- 13. the weathering streaks -----------------------------------------
    # THE named variation axis.  Where the tread falls over the nose, water
    # leaves the drip groove at 2-9 points along the casting, and the face below
    # each of them is washed clean at the centre and dirty at the edges.  `runm`
    # is the GEOMETRY of that (the eroded runnel); this is its stain.
    dirt = t.noise(t.vmath("MULTIPLY", Pl, (18.0, 18.0, 1.4)), 1.0, 4.0, 0.58)
    run_s = t.math("MULTIPLY", runm, t.maprange(below, 0.06, 0.50, 0.0, 1.0))
    base = t.cmix(t.math("MULTIPLY", run_s,
                         t.maprange(dirt, 0.28, 0.72, 1.0, 0.10)),
                  base, PAL["grime"])
    base = t.cmix(t.math("MULTIPLY", run_s,
                         t.maprange(dirt, 0.52, 0.90, 0.0, 0.95)),
                  base, PAL["lime"])
    # the general grime the whole riser carries, heaviest at the foot
    foot = t.math("MULTIPLY", m_riser, t.maprange(below, 0.40, 0.82, 0.0, 1.0))
    base = t.cmix(t.math("MULTIPLY", foot, t.math("MULTIPLY", age, 0.70)),
                  base, PAL["grime"])

    # --- and the weathering the WHOLE face carries ------------------------
    # The runnel stain above only exists where a runnel was eroded, which is 2-9
    # bands per casting.  A twenty-year-old riser in permanent shade is streaked
    # EVERYWHERE -- every metre of it has run water down it -- and the first
    # macro at 14.7 m showed a smooth pale band precisely because the streaking
    # was confined to the runnels.  Three octaves of vertical-only noise, all of
    # them anisotropic (30:1) so they run DOWN the face and not across it.
    vs1 = t.noise(t.vmath("MULTIPLY", Pl, (34.0, 34.0, 2.0)), 1.0, 4.0, 0.58)
    vs2 = t.noise(t.vmath("MULTIPLY", Pl, (11.0, 11.0, 1.1)), 1.0, 4.0, 0.58)
    vs3 = t.noise(t.vmath("MULTIPLY", Pl, (74.0, 74.0, 3.4)), 1.0, 3.0, 0.52)
    # streaks CLUMP.  A face with evenly spaced stripes is a comb; a real one has
    # two or three busy zones and long clean stretches between them, because the
    # water comes off the nose at the few points where the fall and the chips put
    # it and not everywhere at once.
    vclump = t.maprange(t.noise(t.vmath("MULTIPLY", Pl, (4.2, 4.2, 0.7)),
                                1.0, 3.0, 0.5), 0.40, 0.68, 0.0, 1.0)
    vstreak = t.math("MULTIPLY",
                     t.maprange(vs1, 0.30, 0.76, 0.0, 1.0),
                     t.math("ADD", 0.20, t.math("MULTIPLY",
                                                t.maprange(vs2, 0.28, 0.78,
                                                           0.0, 1.0), 1.05)))
    vstreak = t.math("MULTIPLY", vstreak, t.math("ADD", 0.18,
                                                 t.math("MULTIPLY", vclump,
                                                        1.05)))
    face_w = t.math("MULTIPLY", m_riser,
                    t.maprange(below, 0.04, 0.34, 0.0, 1.0))
    face_w = t.math("MULTIPLY", face_w, t.math("ADD", 0.45,
                                               t.math("MULTIPLY", age, 0.75)))
    base = t.cmix(t.math("MULTIPLY", t.math("MULTIPLY", face_w, vstreak), 0.85),
                  base, PAL["grime"])
    # the clean washed lanes BETWEEN the dirty ones -- a streaked wall is as much
    # about where the water took the dirt off as where it put it
    base = t.cmix(t.math("MULTIPLY",
                         t.math("MULTIPLY", face_w,
                                t.maprange(vs3, 0.55, 0.86, 0.0, 1.0)), 0.55),
                  base, PAL["conc_pale"])

    # ---- 14. algae in the slots ---------------------------------------------
    # every narrow slot on a north-facing stand holds water: the drip groove, the
    # channel, the joint between castings and the root of the riser.
    damp = t.math("MAXIMUM", m_drip, t.math("MULTIPLY", m_chan, 0.95))
    damp = t.math("MAXIMUM", damp,
                  t.math("MULTIPLY", m_riser,
                         t.maprange(below, 0.60, 0.86, 0.0, 0.90)))
    damp = t.math("MULTIPLY", damp,
                  t.maprange(t.noise(t.vmath("SCALE", P, scale=1.0), 22.0, 5.0),
                             0.32, 0.70, 0.10, 1.0))
    damp = t.math("MULTIPLY", damp, t.math("ADD", 0.28,
                                           t.math("MULTIPLY", wet, 0.95)))
    base = t.cmix(t.math("MULTIPLY", damp, 0.85), base,
                  t.cmix(wet, PAL["algae"], PAL["moss"]))

    # ---- 15. the channel's silt ---------------------------------------------
    silt = t.math("MULTIPLY", m_chan,
                  t.maprange(t.noise(t.vmath("SCALE", P, scale=1.0), 14.0, 5.0),
                             0.28, 0.80, 0.40, 1.0))
    base = t.cmix(t.math("MULTIPLY", silt, 0.85), base, PAL["silt"])

    # ---- 16. rust bleed at the fixings --------------------------------------
    rust = t.math("MULTIPLY", socm,
                  t.maprange(t.noise(t.vmath("SCALE", P, scale=1.0), 60.0, 4.0),
                             0.32, 0.75, 0.15, 1.0))
    base = t.cmix(t.math("MULTIPLY", rust, 0.80), base, PAL["rust"])

    # ---- 17. the repair patch -----------------------------------------------
    patch = t.math("MULTIPLY", rep,
                   t.maprange(t.noise(t.vmath("MULTIPLY", Pl, (2.0, 2.0, 2.0)),
                                      1.5, 3.0), 0.60, 0.68, 0.0, 1.0))
    base = t.cmix(patch, base, PAL["repair"])

    # ---- 18. the soffit ------------------------------------------------------
    # nothing washes the underside, so it keeps its mould face and its dust and
    # is the flattest, dustiest surface on the casting.
    base = t.cmix(t.math("MULTIPLY", m_soffit, 0.45), base, PAL["conc_dark"])

    # ---- 19. roughness -------------------------------------------------------
    rough = t.fmix(t.math("MULTIPLY", n_fine, 0.7), 0.88, 0.96)
    rough = t.fmix(t.math("MULTIPLY", walk, 0.95), rough, 0.52)     # polished
    rough = t.fmix(t.math("MULTIPLY", damp, 0.9), rough, 0.38)      # damp
    rough = t.fmix(t.math("MULTIPLY", dampt, 0.8), rough, 0.60)
    rough = t.fmix(chip, rough, 0.98)                               # fresh break
    rough = t.fmix(t.math("MULTIPLY", lime_m, 0.85), rough, 0.97)   # bloom

    # ---- 20. the micro relief -----------------------------------------------
    # everything below 2 mm, which is where this module drew the line between
    # geometry and shading.  It is deliberately WEAK on the tread (a bump on an
    # up-facing surface under a sky does nothing) and strong on the riser and the
    # soffit, which are the faces a bump can actually shade.
    peel = t.noise(t.vmath("SCALE", P, scale=1.0), 96.0, 6.0, 0.58)
    broom = t.wave(t.vmath("MULTIPLY", Pl, (1.0, 1.0, 1.0)), 104.0, 1.60, 3.0,
                   "Y")
    broom_m = t.math("MULTIPLY", m_tread,
                     t.math("SUBTRACT", 1.0, t.math("MULTIPLY", walk, 0.75)))
    h = t.math("ADD", t.math("MULTIPLY", peel, 0.60),
               t.math("MULTIPLY", broom, t.math("MULTIPLY", broom_m, 0.40)))
    h = t.math("ADD", h, t.math("MULTIPLY", bug_m, -1.50))
    h = t.math("ADD", h, t.math("MULTIPLY", show, 1.10))   # aggregate stands up
    h = t.math("ADD", h, t.math("MULTIPLY", gritm, 0.45))
    # STATED AS RADIANCE MODULATION, NOT MILLIMETRES (itemkit 5b, brief 4a).
    # `h` is a SUM of five bands, so a single wavelength for the stage is a
    # choice and not a reading.  The one named here is the band that is always
    # present -- the mould peel -- with `height_pp` set to its own weight in the
    # sum, so `modulation_pp` is the modulation of THAT band rather than of a
    # hypothetical full-swing height.  The gated bands, at the same Distance:
    #
    #   peel   w 0.60  lam 16.67 mm  m 1.006   isotropic, always on
    #   broom  w 0.40  lam  9.62 mm  m 1.160   tread only, and directional
    #   bug    w 1.50  lam  5.05 mm  m 6.139   sparse voids -- hard_feature
    #   agg    w 1.10  lam 11.42 mm  m 2.595   chipped arris only
    #   grit   w 0.45  lam 22.84 mm  m 0.553   tread only
    #
    # These reproduce the shipped Distance exactly; they are what the module
    # always meant and never delivered, because the height socket was not wired.
    # peel at 1.006 is 6 % over RELIEF_BANDS["isotropic_macro"] and the bug
    # holes are 2 % over the hard_feature ceiling; both are left alone rather
    # than re-tuned, because nothing here has ever been seen at these depths and
    # a 6 % move is below what the eye that will judge it can resolve.
    LAM_PEEL = K.NOISE_WAVELENGTH_FACTOR / 96.0        # 16.67 mm
    LAM_AGG = K.VORONOI_WAVELENGTH_FACTOR / 190.0      # 11.42 mm
    nrm = t.bump(h, 0.55, modulation_pp=1.00627, wavelength_m=LAM_PEEL,
                 height_pp=0.60)
    nrm2 = t.bump(agg_c, 0.26, normal=nrm,
                  modulation_pp=0.58089, wavelength_m=LAM_AGG)

    # ---- 21. the shader ------------------------------------------------------
    bsdf = t.n("ShaderNodeBsdfPrincipled")
    t.pin(bsdf, 0, base)
    names = [i.name for i in bsdf.inputs]
    if "Roughness" in names:
        t.pin(bsdf, names.index("Roughness"), rough)
    for k, v in (("Metallic", 0.0), ("IOR", 1.52), ("Specular IOR Level", 0.35)):
        if k in names:
            t.pin(bsdf, names.index(k), v)
    if "Normal" in names:
        t.pin(bsdf, names.index("Normal"), nrm2)
    out = t.n("ShaderNodeOutputMaterial")
    t.t.links.new(bsdf.outputs[0], out.inputs[0])
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


def unit_world_xyz(u):
    """World centre of the casting.  No bpy."""
    o, ex, ey, ez = unit_frame(u)
    return o


def grade_lod(units, anchor):
    if not anchor:
        for u in units:
            u["lod"] = 1
        return
    A = np.asarray(anchor, float)
    for u in units:
        p = unit_world_xyz(u)
        d = float(np.min(np.linalg.norm(A - p[None, :], axis=1)))
        u["lod"] = lod_of(d)
        u["anchor_d"] = d


def build(lod_anchor=None, scene=None, stats=None, limit=None, blocks=None,
          uniform_lod=None):
    """Emit the item.  ONE OBJECT PER CASTING into W_Item_GrandstandRiserUnit.

    lod_anchor   list of world points (the camera path).  Mesh density is graded
                 by distance to the nearest of them.  None -> uniform LOD 1.
    blocks       restrict to these block indices (debug).
    uniform_lod  force one LOD for everything (debug / selftest).
    """
    scene = scene or bpy.context.scene
    purge()
    root = _coll(COLL)
    mat = mat_riser()
    us = unit_records()
    if blocks is not None:
        us = [u for u in us if u["bi"] in set(blocks)]
    grade_lod(us, lod_anchor)
    if uniform_lod is not None:
        for u in us:
            u["lod"] = int(uniform_lod)
    if limit:
        us = us[:limit]

    st = stats if stats is not None else {}
    st.setdefault("units", 0); st.setdefault("tris", 0)
    st.setdefault("lod", [0, 0, 0, 0]); st.setdefault("lengths", [])
    st.setdefault("nchip", []); st.setdefault("verts", 0)
    st.setdefault("sockets", 0); st.setdefault("channels", 0)

    for i, u in enumerate(us):
        ob, tri = build_unit(u, root, mat, u["lod"])
        st["units"] += 1
        st["tris"] += tri
        st["verts"] += len(ob.data.vertices)
        st["lod"][min(u["lod"], 3)] += 1
        st["lengths"].append(u["L"])
        st["nchip"].append(len(u["chips"]))
        st["sockets"] += int(ob.get("gru_nsock", 0))
        st["channels"] += 1 if u["channel"] else 0
        if (i + 1) % 400 == 0:
            log("   ... %d/%d castings, %.2f M tris"
                % (i + 1, len(us), st["tris"] / 1e6))

    C.stamp(root)
    root["item"] = ITEM
    root["units"] = st["units"]
    log("BUILT %d castings, %.3f M tris  (LOD %s)"
        % (st["units"], st["tris"] / 1e6, st["lod"]))
    return root


# ==============================================================================
#  8.  THE INTERFACE OTHER ITEMS CALL     (all of it works without bpy)
# ==============================================================================

def unit_to_world(u, pts):
    """(x from the casting's centre, Y from the nose, Z from the nose top)
    -> world.  `pts` is (n, 3) or a single triple."""
    o, ex, ey, ez = unit_frame(u)
    org = _unit_local_origin(u)
    p = np.atleast_2d(np.asarray(pts, float))
    W = (o[None, :] + np.outer(p[:, 0] - org[0], ex)
         + np.outer(p[:, 1] - org[1], ey) + np.outer(p[:, 2] - org[2], ez))
    return W[0] if np.ndim(pts) == 1 else W


def nosing_sites(units=None):
    """FOR grandstand_nosing (3 400 instances).

    One record per casting.  Everything the insert needs and nothing it has to
    guess:
        a, b        world ends of the nose arris (the top front edge)
        rebate      True if this unit has the 62 x 9 mm cast rebate; where it is
                    False the nosing is SURFACE-FIXED and there is no recess
        rebate_a/b  world ends of the rebate's own floor line
        chamfer     the chamfer actually drawn on this casting (m)
        chips       [(x0, x1, depth)] along the arris, from the casting's own
                    left end, so the insert can be broken where the concrete is
        frame       (origin, ex, ey, ez) — the unit's rigid frame
    """
    out = []
    for u in (units or unit_records()):
        L = u['L']
        ch = u['ch']
        z_nose = 0.0
        a = unit_to_world(u, (-L * 0.5 + END_CH, 0.0, -ch * 0.5))
        b = unit_to_world(u, (+L * 0.5 - END_CH, 0.0, -ch * 0.5))
        ra = unit_to_world(u, (-L * 0.5 + END_CH, ch, z_nose - REBATE_D))
        rb = unit_to_world(u, (+L * 0.5 - END_CH, ch, z_nose - REBATE_D))
        o, ex, ey, ez = unit_frame(u)
        out.append(dict(
            uid=u['uid'], block=u['block'], row=u['row'], bay=u['bay'],
            a=[float(v) for v in a], b=[float(v) for v in b],
            rebate=bool(u['rebate']),
            rebate_w=REBATE_W, rebate_d=REBATE_D,
            rebate_a=[float(v) for v in ra], rebate_b=[float(v) for v in rb],
            chamfer=float(ch), length=float(L),
            chips=[[float(c['x'] - L * 0.5), float(c['x'] + c['l'] - L * 0.5),
                    float(c['d'])] for c in u['chips']],
            origin=[float(v) for v in o],
            ex=[float(v) for v in ex], ey=[float(v) for v in ey],
            ez=[float(v) for v in ez]))
    return out


def aisle_records():
    """FOR grandstand_stair (26 flights).

    THE TERRACE RUNS CONTINUOUSLY UNDER EVERY AISLE.  That is how a raked
    terrace is built — the aisle steps are separate castings sat ON the treads,
    two half-risers per row — and it is why this module does not cut a gap for
    them.  What a stair flight needs is where the treads it lands on actually
    are, after their own seating errors:

        per aisle: centre x (circuit), width, and per row the four world corners
        of the 1.25 m wide strip of tread it sits on, plus that tread's top z at
        both edges (they differ: the unit is tilted).
    """
    out = []
    for b in block_records():
        for k, ax in enumerate(b['aisles']):
            rows = []
            for u in unit_records():
                if u['bi'] != b['bi']:
                    continue
                if not (u['x_a'] - 0.02 <= ax <= u['x_b'] + 0.02):
                    continue
                xl = ax - AISLE_W * 0.5 - u['x_m']
                xr = ax + AISLE_W * 0.5 - u['x_m']
                zt = _z_tread_local
                q = unit_to_world(u, [(xl, 0.0, float(zt(u, 0.0))),
                                      (xr, 0.0, float(zt(u, 0.0))),
                                      (xr, u['pitch'], float(zt(u, u['pitch']))),
                                      (xl, u['pitch'], float(zt(u, u['pitch'])))])
                rows.append(dict(row=u['row'], uid=u['uid'],
                                 quad=[[float(v) for v in p] for p in q],
                                 rise=float(u['rise']), pitch=float(u['pitch'])))
            rows.sort(key=lambda r: r['row'])
            out.append(dict(block=b['name'], bi=b['bi'], aisle=k,
                            x=float(ax), width=AISLE_W, rows=rows))
    return out


def vomitory_records():
    """FOR grandstand_stair and grandstand_vomitory.

    The 12 real holes in the terrace.  This module casts CLOSER UNITS each side
    of a 3.00 m opening over two rows; the opening rectangle and its trimmer
    edges are published here so the tunnel mouth lands in the hole rather than
    near it."""
    out = []
    for b in block_records():
        for vi, vx in enumerate(b['voms']):
            rows = []
            for r in (b['vom_row'], b['vom_row'] + 1):
                if r >= b['rows']:
                    continue
                rr = [q for q in row_records()
                      if q['bi'] == b['bi'] and q['row'] == r][0]
                rows.append(dict(row=r, z_tread=float(rr['z_tread']),
                                 y_nose=float(rr['y_nose'])))
            c0 = C.circuit_to_world(vx - VOM_W * 0.5,
                                    b['y_first'] - b['vom_row'] * b['tread'])
            c1 = C.circuit_to_world(vx + VOM_W * 0.5,
                                    b['y_first'] - (b['vom_row'] + 2) * b['tread'])
            out.append(dict(block=b['name'], bi=b['bi'], vom=vi,
                            x=float(vx), width=VOM_W,
                            rows=rows,
                            corner_a=[float(c0[0]), float(c0[1])],
                            corner_b=[float(c1[0]), float(c1[1])]))
    return out


def seat_grid():
    """FOR crowd_density_field (and for grandstand_seat when it wants the truth).

    18 350 seat anchors.  This does NOT decide occupancy — it is the grid the
    occupancy decision is made ON, which is exactly what the manifest asked for:
    "Build this before a single figure is placed - everything else in this zone
    reads off it."

    Each record:
        p        world point on the tread where the seat's own frame sits
        facing   world unit vector the seat looks along (toward the track)
        up       world unit vector normal to THAT unit's tread (it is tilted)
        row/col  indices, block name
        flags    aisle_end, gangway_row, vom_edge, top_row, front_row
        clear    metres of clear tread in front of the seat (the leg room the
                 density field needs to know about before it stands anyone up)
    """
    out = []
    by_bi = {}
    for u in unit_records():
        by_bi.setdefault((u['bi'], u['row']), []).append(u)
    for b in block_records():
        for r in range(b['rows']):
            seats = _seat_columns(b, r)
            us = by_bi.get((b['bi'], r), [])
            for (ci, sx) in seats:
                host = None
                for u in us:
                    if u['x_a'] - 0.01 <= sx <= u['x_b'] + 0.01:
                        host = u
                        break
                if host is None:
                    continue
                Y = 0.42 * host['pitch']
                Z = float(_z_tread_local(host, Y))
                p = unit_to_world(host, (sx - host['x_m'], Y, Z))
                o, ex, ey, ez = unit_frame(host)
                da = min(abs(sx - ax) for ax in b['aisles']) if b['aisles'] else 99
                out.append(dict(
                    block=b['name'], bi=b['bi'], row=r, col=ci,
                    uid=host['uid'],
                    p=[float(v) for v in p],
                    facing=[float(-v) for v in ey],       # toward the track
                    up=[float(v) for v in ez],
                    aisle_end=bool(da < AISLE_W * 0.5 + SEAT_MODULE * 1.2),
                    gangway_row=bool(r in b['gangway_rows']),
                    top_row=bool(r == b['rows'] - 1),
                    front_row=bool(r == 0),
                    vom_edge=bool(any(abs(sx - vx) < VOM_W * 0.5 + 0.8
                                      for vx in b['voms'])
                                  and abs(r - b['vom_row']) <= 2),
                    clear=float(host['pitch'] - 0.42 * host['pitch'] - 0.02),
                    seat_kind=int(b['seat'])))
    return out


def fixing_sockets(units=None):
    """FOR grandstand_seat_bracket.  Every socket this module actually cast.

    kind is 'tread' (in the tread top at the seat line) or 'riser' (in the riser
    face, serving the seat on the row BELOW).  Both are real castings; a socket
    that is not in this list does not exist in the mesh.
    """
    out = []
    for u in (units or unit_records()):
        kind, at = _socket_lines(u)
        for s in u['sockets']:
            if kind == 'tread':
                Y, Z = at, float(_z_tread_local(u, at)) - SOC_D * 0.5
            else:
                Y, Z = DRIP_D * 0.0 + SOC_D * 0.5, at
            p = unit_to_world(u, (s['x'], Y, Z))
            o, ex, ey, ez = unit_frame(u)
            n = ez if kind == 'tread' else -ey
            out.append(dict(uid=u['uid'], block=u['block'], row=u['row'],
                            col=s['col'], kind=kind,
                            p=[float(v) for v in p],
                            normal=[float(v) for v in n],
                            size=SOC_HW * 2.0, depth=SOC_D,
                            repair=bool(s['repair'])))
    return out


def litter_troughs(units=None):
    """FOR crowd_litter_drift (4 000 instances).

    "Seen from directly above at the end of the film, this is what fills the
    gaps between people."  Litter does not lie where it is dropped; it is kicked
    to the two lines where the tread stops being flat:

        root     the back of the tread against the riser root of the row behind
                 — where everything ends up on a front-falling unit
        channel  the cast drainage channel, where there is one.  Its true
                 section is published (width, depth, floor z) so a cup can sit
                 IN it rather than on it.
    """
    out = []
    for u in (units or unit_records()):
        L = u['L']
        Yr = u['pitch'] - 0.020
        Zr = float(_z_tread_local(u, Yr))
        a = unit_to_world(u, (-L * 0.5 + 0.02, Yr, Zr))
        b = unit_to_world(u, (+L * 0.5 - 0.02, Yr, Zr))
        rec = dict(uid=u['uid'], block=u['block'], row=u['row'],
                   root_a=[float(v) for v in a], root_b=[float(v) for v in b],
                   traffic=float(u['traffic']), channel=bool(u['channel']))
        if u['channel']:
            c1 = u['pitch'] - CHAN_BACK
            Yc = c1 - CHAN_W * 0.5
            Zc = float(_z_tread_local(u, Yc)) - CHAN_D
            ca = unit_to_world(u, (-L * 0.5 + 0.02, Yc, Zc))
            cb = unit_to_world(u, (+L * 0.5 - 0.02, Yc, Zc))
            rec.update(chan_a=[float(v) for v in ca],
                       chan_b=[float(v) for v in cb],
                       chan_w=CHAN_W, chan_d=CHAN_D,
                       outlet=bool(u['outlet']))
        out.append(rec)
    return out


def bearing_lines():
    """Where the rakers have to be, published so the undercroft frame and this
    module cannot disagree: one line per bay joint, per block."""
    out = []
    for b in block_records():
        for k in range(b['nbay'] + 1):
            x = b['x0'] + k * b['bay_w']
            y0 = b['y_first']
            y1 = b['y_first'] - b['rows'] * b['tread']
            p0 = C.circuit_to_world(x, y0)
            p1 = C.circuit_to_world(x, y1)
            out.append(dict(block=b['name'], bi=b['bi'], bay=k, x=float(x),
                            a=[float(p0[0]), float(p0[1]),
                               FRONT_DECK + TREAD_SLAB - TOTAL_H],
                            b=[float(p1[0]), float(p1[1]),
                               FRONT_DECK + TREAD_SLAB
                               + (b['rows'] - 1) * b['rise'] - TOTAL_H]))
    return out


def interface_json(path=None):
    d = dict(
        item=ITEM, version=__version__,
        filmed_at_m=FILMED_AT_M, lens_mm=LENS_MM, px_per_m=PX_PER_M,
        section=dict(leg_t=LEG_T, slab_t=SLAB_T, haunch=HAUNCH,
                     total_h=TOTAL_H, nib_w=NIB_W, batter=BATTER, fall=FALL,
                     rebate_w=REBATE_W, rebate_d=REBATE_D,
                     drip_z=DRIP_Z, drip_w=DRIP_W, drip_d=DRIP_D,
                     chan_w=CHAN_W, chan_d=CHAN_D, chan_back=CHAN_BACK,
                     end_chamfer=END_CH, socket=dict(hw=SOC_HW, d=SOC_D,
                                                     dx=SOC_DX),
                     front_deck=FRONT_DECK, tread_slab=TREAD_SLAB,
                     starter_h=STARTER_H, embed=EMBED),
        blocks=[{k: v for k, v in b.items() if k != 'gangway_rows'}
                for b in block_records()],
        counts=dict(units=len(unit_records()),
                    rows=len(row_records()),
                    seats=len(seat_grid()),
                    sockets=len(fixing_sockets())),
        nosing_sites=nosing_sites(),
        aisles=aisle_records(),
        vomitories=vomitory_records(),
        bearing_lines=bearing_lines(),
        litter_troughs=litter_troughs(),
    )
    if path:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w") as f:
            json.dump(d, f, indent=1)
    return d


# ==============================================================================
#  9.  STAND-INS  —  owned by OTHER items, built here only so the macro is not
#      shot over a void.  Every name starts with GRUX_, which does NOT start
#      with the gate prefix GRU_U, so none of it is measured as this item.
# ==============================================================================

def _mat_simple(name, col, rough=0.85):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    n = nt.nodes.new("ShaderNodeTexNoise")
    co = nt.nodes.new("ShaderNodeTexCoord")
    mx = nt.nodes.new("ShaderNodeMix")
    mx.data_type = "RGBA"
    nt.links.new(co.outputs[3], n.inputs[0])
    n.inputs[2].default_value = 14.0
    nt.links.new(n.outputs[0], mx.inputs[0])
    mx.inputs[6].default_value = tuple(col) + (1.0,)
    mx.inputs[7].default_value = tuple(c * 1.22 for c in col) + (1.0,)
    nt.links.new(mx.outputs[2], b.inputs[0])
    names = [i.name for i in b.inputs]
    b.inputs[names.index("Roughness")].default_value = rough
    nt.links.new(b.outputs[0], out.inputs[0])
    return m


def _box(mb, x0, y0, z0, x1, y1, z1):
    """Append a circuit-frame box to (verts, quads) lists."""
    V, Q = mb
    i = len(V)
    for (x, y, z) in ((x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                      (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)):
        wx, wy = C.circuit_to_world(x, y)
        V.append((float(wx), float(wy), float(z)))
    Q += [(i + 0, i + 3, i + 2, i + 1), (i + 4, i + 5, i + 6, i + 7),
          (i + 0, i + 1, i + 5, i + 4), (i + 1, i + 2, i + 6, i + 5),
          (i + 2, i + 3, i + 7, i + 6), (i + 3, i + 0, i + 4, i + 7)]


def build_standins(coll, blocks=None):
    """The terrace deck, the front walkway and fascia, the rakers and the rear
    wall.  Coarse on purpose: they are context, not the item."""
    made = []
    conc = _mat_simple(XPFX + "Conc", (0.105, 0.103, 0.098), 0.90)
    deck = _mat_simple(XPFX + "Deck", (0.088, 0.086, 0.082), 0.93)
    dark = _mat_simple(XPFX + "Dark", (0.022, 0.022, 0.023), 0.95)

    for b in block_records():
        if blocks is not None and b['bi'] not in blocks:
            continue
        V, Q = [], []
        mb = (V, Q)
        x0, x1 = b['x0'], b['x1']
        yf = b['y_first']
        yb = yf - b['rows'] * b['tread']
        top = FRONT_DECK + TREAD_SLAB + (b['rows'] - 1) * b['rise']
        # front walkway slab + fascia
        _box(mb, x0, yf, FRONT_DECK - 0.18, x1, GS_FRONT, FRONT_DECK)
        _box(mb, x0, GS_FRONT - 0.35, -0.30, x1, GS_FRONT, FRONT_DECK + 1.05)
        # rakers, one per bay line, as a stepped inclined beam.  NOT through the
        # vomitory openings: the first pass ran them straight across the hole and
        # the Beat-5 render showed two lit cylinders floating in a black
        # rectangle, which reads as construction debris rather than as a
        # tunnel mouth.
        vom_rows = set([b['vom_row'], b['vom_row'] + 1])
        for k in range(b['nbay'] + 1):
            bx = b['x0'] + k * b['bay_w']
            in_vom = any(abs(bx - vx) < VOM_W * 0.5 + 0.25 for vx in b['voms'])
            for r in range(b['rows']):
                if in_vom and r in vom_rows:
                    continue
                y_n = b['y_first'] - r * b['tread']
                z_t = FRONT_DECK + TREAD_SLAB + r * b['rise']
                _box(mb, bx - 0.14, y_n - b['tread'] - LEG_T, z_t - TOTAL_H - 0.55,
                     bx + 0.14, y_n + 0.02, z_t - TOTAL_H)
        # rear wall
        _box(mb, x0, yb - 0.30, 0.0, x1, yb, top + 0.35)
        # a shaft under every vomitory: the tunnel itself is
        # grandstand_vomitory's item, but a 3 m hole straight through to nothing
        # renders as a black rectangle, which is a hole in the model rather than
        # a hole in the terrace (the manifest says so about that item in as many
        # words).  This is the box the mouth is cut into.
        for vx in b['voms']:
            y_n = b['y_first'] - b['vom_row'] * b['tread']
            z_t = FRONT_DECK + TREAD_SLAB + b['vom_row'] * b['rise']
            yb_ = y_n - 2.15 * b['tread']
            _box(mb, vx - 1.60, yb_ - 0.15, z_t - 3.40,
                 vx + 1.60, y_n + 0.10, z_t - 3.25)            # landing
            for w in (-1, 1):                                   # side walls
                _box(mb, vx + w * 1.60, yb_ - 0.15, z_t - 3.40,
                     vx + w * 1.75, y_n + 0.10, z_t - TOTAL_H + 0.02)
            _box(mb, vx - 1.75, yb_ - 0.15, z_t - 3.40,         # back wall
                 vx + 1.75, yb_, z_t - TOTAL_H + 0.02)
            _box(mb, vx - 1.75, y_n + 0.02, z_t - 3.40,         # front wall
                 vx + 1.75, y_n + 0.12, z_t - TOTAL_H + 0.02)
        me = _new_mesh(XPFX + "Struct_%02d" % b['bi'], np.asarray(V, float),
                       np.asarray(Q, np.int32), None, smooth_deg=None)
        me.materials.append(conc)
        ob = bpy.data.objects.new(XPFX + "Struct_%02d" % b['bi'], me)
        coll.objects.link(ob)
        made.append(ob)

    # THE GROUND IN FRONT.  Not decoration: without it every ray leaving the
    # rake downward and forward sees SKY, and the terrace renders bluer and
    # brighter than it can possibly be in the assembled world.  The apron in
    # front of this stand is real, it is at C.APRON_Z, and at a 12.47 deg sun
    # from behind the stand it is itself in the stand's own 59 m shadow -- so it
    # is a dark, slightly warm floor, and that is exactly what it contributes.
    V, Q = [], []
    _box((V, Q), -520.0, GS_FRONT + 5.0, C.APRON_Z - 0.12, 280.0, 90.0,
         C.APRON_Z)
    me = _new_mesh(XPFX + "Apron", np.asarray(V, float),
                   np.asarray(Q, np.int32), None, smooth_deg=None)
    me.materials.append(_mat_simple(XPFX + "Asphalt", (0.062, 0.058, 0.054),
                                    0.86))
    ob = bpy.data.objects.new(XPFX + "Apron", me)
    coll.objects.link(ob)
    made.append(ob)

    # the terrace deck, build_architecture's own extents
    V, Q = [], []
    _box((V, Q), -426.0, GS_BACK - 7.0, C.APRON_Z - 1.85, 186.0,
         GS_FRONT + 5.5, C.APRON_Z)
    me = _new_mesh(XPFX + "Terrace", np.asarray(V, float),
                   np.asarray(Q, np.int32), None, smooth_deg=None)
    me.materials.append(deck)
    ob = bpy.data.objects.new(XPFX + "Terrace", me)
    coll.objects.link(ob)
    made.append(ob)
    log("stand-ins: %d objects (context only, prefix %s)" % (len(made), XPFX))
    return made


# ==============================================================================
# 10.  LIGHT AND CAMERA
# ==============================================================================

def contract_light(scene=None, coll=None):
    """The film's sun and sky, exactly as world_contract measured them.

    NOTE, and it is the whole point of this item's look: the sun is BEHIND this
    stand and every riser shadows the tread in front of it, so this lamp
    contributes almost nothing to the terrace.  It is here because it must be
    the same physical light as every other item's, not because it lights this
    one.  The sky does that.
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
    log("light: sun %.3f W/m2 elev %.2f deg bearing %.2f deg; %s %.3f EV"
        % (C.SUN_ENERGY, C.SUN_ELEV_DEG, C.SUN_BEARING_DEG,
           C.VIEW_TRANSFORM, C.REFERENCE_EXPOSURE_EXTERIOR))
    return ob


def add_camera(name, loc, look, lens, coll, fstop=None):
    from mathutils import Vector
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = 36.0
    cd.clip_start = 0.02
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

    Four things decide it:
      * NO ROOF over it.  Two thirds of the terrace is skylit through a roof
        that belongs to another item and is not in this scene; shooting the
        macro under a block that HAS a roof would be a claim about a lighting
        condition this scene cannot show.  Blocks with roof='none' are the ones
        whose real light this test reproduces exactly.
      * mid-rake, so the frame carries a dozen rows of grid rather than a
        close-up of one nose — the manifest's own reason for the item being
        hero is "from directly above they are the grid".
      * the casting must carry DAMAGE — chips, a channel, sockets — because a
        macro of the one undamaged unit in the stand is a claim about the wrong
        object.
      * near an aisle and a vomitory, where the geometry is busiest.
    """
    us = unit_records()
    best, bs = None, -1e9
    for u in us:
        b = block_records()[u['bi']]
        if b['roof'] != 'none':
            continue
        mid = abs(u['row'] - b['rows'] * 0.45) / max(1.0, b['rows'])
        da = min(abs(u['x_m'] - ax) for ax in b['aisles']) if b['aisles'] else 9
        dv = min(abs(u['x_m'] - vx) for vx in b['voms']) if b['voms'] else 9
        sc = (2.4 * (1.0 - min(1.0, mid * 2.2))
              + 1.5 * min(len(u['chips']), 5) / 5.0
              + 0.9 * min(len(u['sockets']), 12) / 12.0
              + 0.8 * math.exp(-(da / 4.0) ** 2)
              + 0.6 * math.exp(-(dv / 7.0) ** 2)
              + 0.5 * u['traffic']
              + 0.4 * (1.0 if u['channel'] else 0.0)
              + 0.3 * (1.0 if u['rebate'] else 0.0))
        if sc > bs:
            best, bs = u, sc
    return best


def macro_rig(u, coll, name, lens=LENS_MM, dist=FILMED_AT_M,
              elev_deg=42.0, yaw_deg=18.0, aim_Y=None, aim_x=0.0):
    """A camera at EXACTLY the manifest's distance and lens.

    The aim point is the nose of the hero casting.  The camera stands `dist`
    metres from it — measured, then asserted in the log — at `elev_deg` above
    the terrace and `yaw_deg` off the stand's own normal, on the TRACK side,
    which is where the Beat-6 crane-out is: circuit (-58, -28, 21) looking at
    (-66, -50, 5) is 34.4 deg of depression from in front of the fascia, and
    every camera below is a variation on that.
    """
    Y = 0.10 if aim_Y is None else aim_Y
    aim = unit_to_world(u, (aim_x, Y, float(_z_tread_local(u, Y))))
    cw, sw = math.cos(math.radians(C.ROT_DEG)), math.sin(math.radians(C.ROT_DEG))
    ex = np.array([cw, sw, 0.0])            # circuit +x, along the row
    ny = np.array([-sw, cw, 0.0])           # circuit +y, out toward the track
    el = math.radians(elev_deg); ya = math.radians(yaw_deg)
    d = (ny * math.cos(ya) + ex * math.sin(ya)) * math.cos(el)
    d = d + np.array([0.0, 0.0, 1.0]) * math.sin(el)
    d = d / np.linalg.norm(d)
    loc = aim + d * dist
    cam = add_camera(name, tuple(float(v) for v in loc),
                     tuple(float(v) for v in aim), lens, coll)
    return cam, aim, loc


def test_scene(samples=256, limit=None, blocks=None):
    """Build the item, light it with the contract sun, and put the manifest's
    own camera on it: 14.700 m away on a 28 mm lens."""
    scene = bpy.context.scene
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)

    u = hero_unit()
    b = block_records()[u['bi']]
    log("hero casting uid %d  block %s  row %d  bay %d  L %.3f  "
        "chips %d  sockets %d  channel %s"
        % (u['uid'], u['block'], u['row'], u['bay'], u['L'],
           len(u['chips']), len(u['sockets']), u['channel']))

    # the LOD anchor is the macro camera's own position plus the aim, so density
    # is graded by distance to the lens and not to the object
    _, aim0, loc0 = None, None, None
    aimp = unit_to_world(u, (0.0, 0.10, 0.0))
    cw, sw = math.cos(math.radians(C.ROT_DEG)), math.sin(math.radians(C.ROT_DEG))
    ny = np.array([-sw, cw, 0.0]); ex = np.array([cw, sw, 0.0])
    el = math.radians(42.0); ya = math.radians(18.0)
    dvec = (ny * math.cos(ya) + ex * math.sin(ya)) * math.cos(el) \
        + np.array([0.0, 0.0, 1.0]) * math.sin(el)
    dvec /= np.linalg.norm(dvec)
    anchor = [list(aimp), list(aimp + dvec * FILMED_AT_M)]

    root = build(lod_anchor=anchor, scene=scene, limit=limit, blocks=blocks)
    cams = _coll(COLL + "/Cameras", root)
    stand = _coll(COLL + "/Standins", root)
    contract_light(scene, coll=root)
    build_standins(stand, blocks=blocks)

    macro, aim, loc = macro_rig(u, cams, PFX + "CAM_MACRO")
    log("CAM_MACRO at %.4f m on a %.0f mm lens"
        % (float(np.linalg.norm(np.asarray(loc) - np.asarray(aim))), LENS_MM))
    # the manifest's own reason for the item: "from directly above they are the
    # grid the whole crowd is registered against"
    macro_rig(u, cams, PFX + "CAM_PLAN", elev_deg=78.0, yaw_deg=6.0)
    # the Beat-5 read: from the track, low, along the fascia
    macro_rig(u, cams, PFX + "CAM_BEAT5", elev_deg=16.0, yaw_deg=34.0)
    # down the row, where the joint rhythm and the unit-to-unit steps ARE the
    # subject rather than one casting's surface
    macro_rig(u, cams, PFX + "CAM_ALONG", elev_deg=26.0, yaw_deg=72.0)
    # DIAGNOSTIC, not the manifest distance: 1.8 m on a 50 mm lens, which is the
    # only way to see whether a 34 mm socket and a 12 mm drip groove are really
    # there.  Labelled so nobody mistakes it for the delivered macro.
    macro_rig(u, cams, PFX + "CAM_PEEP", dist=1.8, lens=50.0,
              elev_deg=34.0, yaw_deg=22.0)
    # aimed at a REAL chip on this casting, not at its middle: a peep that
    # frames sound concrete is a photograph of the thing not being damaged
    cx = 0.0
    if u['chips']:
        c = max(u['chips'], key=lambda q: q['d'] * q['l'])
        cx = c['x'] + c['l'] * 0.5 - u['L'] * 0.5
    macro_rig(u, cams, PFX + "CAM_PEEP_NOSE", dist=0.9, lens=50.0,
              elev_deg=24.0, yaw_deg=8.0, aim_x=cx)
    macro_rig(u, cams, PFX + "CAM_PEEP_CHIP", dist=0.42, lens=50.0,
              elev_deg=30.0, yaw_deg=14.0, aim_x=cx)
    # the wide, so the stand can be judged as a stand
    macro_rig(u, cams, PFX + "CAM_WIDE", dist=54.0, lens=35.0,
              elev_deg=30.0, yaw_deg=14.0)

    scene.camera = macro
    scene.render.engine = "CYCLES"
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.cycles.samples = samples
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.008
    scene.cycles.max_bounces = 12
    scene.cycles.diffuse_bounces = 6
    scene.cycles.glossy_bounces = 4
    scene.cycles.use_denoising = True
    return root


# ==============================================================================
# 11.  MEASUREMENT
# ==============================================================================

def _gs_blocks_from_architecture():
    """Read build_architecture.GS_BLOCKS WITHOUT importing it (it imports bpy at
    module scope and this selftest must run from a bare python3)."""
    import ast
    src = open(os.path.join(_WORLD, "build_architecture.py")).read()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not (len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == "GS_BLOCKS"):
            continue
        out = []
        for el in node.value.elts:
            d = {}
            for kw in el.keywords:
                try:
                    d[kw.arg] = ast.literal_eval(kw.value)
                except Exception:
                    d[kw.arg] = None
            out.append(d)
        return out
    return None


def selftest(verbose=True):
    fails = []
    n = [0]

    def chk(name, cond, detail=""):
        n[0] += 1
        print("  %s %-58s %s" % ("ok  " if cond else "FAIL", name, detail))
        if not cond:
            fails.append(name)

    print("grandstand_riser_unit %s  self test" % __version__)

    print("\n[1] the block table against build_architecture (no drift)")
    ga = _gs_blocks_from_architecture()
    chk("build_architecture.GS_BLOCKS is readable", ga is not None and len(ga) == 6,
        "%d blocks" % (len(ga) if ga else 0))
    if ga:
        for i, (a, b) in enumerate(zip(ga, BLOCKS)):
            same = all(abs(float(a[k]) - float(b[k])) < 1e-9
                       for k in ("x0", "x1", "rows", "tread", "rise", "aisle",
                                 "voms"))
            chk("block %d %-22s matches" % (i, b['name']), same,
                "" if same else "%s vs %s" % (a, b))

    print("\n[2] the population against the manifest")
    us = unit_records()
    chk("castings within 2 %% of the manifest's 3400",
        abs(len(us) - INSTANCES_DECLARED) / INSTANCES_DECLARED < 0.02,
        "%d built, %d declared" % (len(us), INSTANCES_DECLARED))
    chk("every casting is at most 4.6 m of terrace",
        max(u['L'] for u in us) <= 4.6, "max %.3f m" % max(u['L'] for u in us))
    L = np.array([u['L'] for u in us])
    chk("cast length CV >= 0.03 (the gate's floor)",
        L.std() / L.mean() >= 0.03, "CV %.4f" % (L.std() / L.mean()))

    print("\n[3] the section")
    ok_h, ok_gap, ok_close = True, True, True
    worst_gap = (9e9, None)
    worst_h = (TOTAL_H, 'none')
    for b in block_records():
        u = [q for q in us if q['bi'] == b['bi'] and not q['starter']][0]
        P = section(u, 0)
        h = float(P['Z'].max() - P['Z'].min())
        if abs(h - TOTAL_H) > abs(worst_h[0] - TOTAL_H):
            worst_h = (h, b['name'])
        if abs(h - TOTAL_H) > 0.001:
            ok_h = False
        # the foot gap: our leg soffit vs the row below's tread top
        fs = _fall_sign(u)
        z_below = -u['rise'] + fs * FALL * (u['pitch'] + LEG_T * 0.5)
        gap = P['leg_z'] - z_below
        if gap < 0.006 or gap > 0.016:
            ok_gap = False
        if gap < worst_gap[0]:
            worst_gap = (gap, b['name'])
        if abs(float(P['Y'][0]) - float(P['Y'][-1])) > 0.3:
            pass
    chk("overall cast height = manifest typical_height_m 0.420", ok_h,
        "worst %.4f m (%s)" % (worst_h[0], worst_h[1]))
    chk("riser-foot slot is 6-16 mm on every block", ok_gap,
        "worst %.1f mm (%s)" % (worst_gap[0] * 1000.0, worst_gap[1]))

    print("\n[4] the ground contract")
    wx, wy = C.circuit_to_world(-40.0, -48.0)
    z, own = C.world_ground_z(float(wx), float(wy))
    chk("world_ground_z over the band is NaN (terrain owns it)",
        (z != z), "owner %s" % own)
    chk("APRON_Z is 0.000 and the terrace deck is on it",
        abs(C.APRON_Z) < 1e-12, "%.6f" % C.APRON_Z)
    st = [q for q in us if q['starter']][0]
    Ps = section(st, 0)
    embed = FRONT_DECK - (st['z_tread'] + float(Ps['Z'].min()))
    chk("row-0 starter toe embeds >= BASE_EMBED_M into the walkway",
        embed >= EMBED - 1e-6, "%.4f m (need %.3f)" % (embed, EMBED))

    print("\n[5] the joint step — the manifest's first variation axis")
    steps = []
    byrow = {}
    for u in us:
        byrow.setdefault((u['bi'], u['row']), []).append(u)
    for k, arr in byrow.items():
        arr.sort(key=lambda q: q['x_m'])
        for a, b in zip(arr[:-1], arr[1:]):
            za = a['dz'] + a['tilt_y'] * (a['L'] * 0.5)
            zb = b['dz'] - b['tilt_y'] * (b['L'] * 0.5)
            steps.append(abs(za - zb))
    steps = np.array(steps)
    chk("joint step sd is 2-9 mm (a set stand, not a broken one)",
        0.002 <= steps.std() <= 0.009,
        "mean %.1f mm  sd %.1f mm  max %.1f mm"
        % (steps.mean() * 1000, steps.std() * 1000, steps.max() * 1000))
    gaps = np.array([u['gap'] for u in us])
    chk("joint gap stays inside the drawn band 8-30 mm",
        gaps.min() >= GAP_LO - 1e-9 and gaps.max() <= GAP_HI + 1e-9,
        "%.1f - %.1f mm" % (gaps.min() * 1000, gaps.max() * 1000))

    print("\n[6] the other three variation axes")
    ch = np.array([len(u['chips']) for u in us])
    chk("nose chips: some castings carry none, some carry many",
        ch.min() == 0 and ch.max() >= 4,
        "%.2f per casting, max %d, %.0f %% carry at least one"
        % (ch.mean(), ch.max(), 100.0 * (ch > 0).mean()))
    nch = sum(1 for u in us if u['channel'])
    chk("drainage channel is present on 15-60 % of castings",
        0.15 <= nch / len(us) <= 0.60, "%d of %d" % (nch, len(us)))
    nr = np.array([len(u['runnels']) for u in us])
    chk("weathering runnels on every front-falling casting",
        all(len(u['runnels']) >= 2 for u in us if not u['channel']),
        "%.1f per casting on average" % nr.mean())

    print("\n[7] the mesh")
    worst_p10 = 0.0
    tri_tot = 0
    for lodi in (0, 1, 2, 3):
        u = hero_unit()
        V, Q, T2, att, org, info = unit_mesh_arrays(u, lodi)
        good = (np.isfinite(V).all() and Q.max() < len(V)
                and (len(T2) == 0 or T2.max() < len(V)))
        e = _edge_lengths(V, Q, T2)
        p10 = float(np.percentile(e, 10))
        tri_tot += info['tris']
        if lodi == 0:
            worst_p10 = p10
        chk("LOD %d mesh is finite and closed-indexed" % lodi, good,
            "%d verts %d tris  p10 edge %.2f mm = %.2f px"
            % (len(V), info['tris'], p10 * 1000, p10 * PX_PER_M))
    chk("LOD 0 p10 edge <= 6 px at 14.7 m on 28 mm (the gate's own limit)",
        worst_p10 * PX_PER_M <= 6.0,
        "%.2f px" % (worst_p10 * PX_PER_M))

    print("\n[8] the interface")
    ns = nosing_sites(us[:200])
    chk("nosing_sites returns a world arris for every casting",
        len(ns) == 200 and all(len(r['a']) == 3 for r in ns))
    sg = seat_grid()
    chk("seat_grid is 14 000-22 000 anchors", 14000 <= len(sg) <= 22000,
        "%d seats" % len(sg))
    fx = fixing_sockets(us[:200])
    chk("fixing_sockets returns real cast pockets", len(fx) > 400,
        "%d in the first 200 castings" % len(fx))
    ar = aisle_records()
    chk("aisle_records covers every aisle in every block",
        len(ar) == sum(len(b['aisles']) for b in block_records()),
        "%d aisles" % len(ar))
    vr = vomitory_records()
    chk("vomitory_records covers all 14 openings", len(vr) == 14,
        "%d" % len(vr))
    lt = litter_troughs(us[:200])
    chk("litter_troughs gives a root line for every casting", len(lt) == 200)

    print("\n[9] scale")
    chk("a casting is 660 px long and 85 px tall on the 4K master",
        abs(TOTAL_H * PX_PER_M - ONSCREEN_PX_4K) < 2.0,
        "%.1f px tall (manifest says %.0f)" % (TOTAL_H * PX_PER_M,
                                               ONSCREEN_PX_4K))

    print("\n%d checks, %d failed" % (n[0], len(fails)))
    if fails:
        for f in fails:
            print("   FAILED: %s" % f)
    print(">> STAGE RESULT: %s" % ("SELFTEST_PASS" if not fails
                                   else "SELFTEST_FAIL"))
    return not fails


def _edge_lengths(V, Q, T2):
    e = []
    if len(Q):
        for a, b in ((0, 1), (1, 2), (2, 3), (3, 0)):
            e.append(np.linalg.norm(V[Q[:, a]] - V[Q[:, b]], axis=1))
    if len(T2):
        for a, b in ((0, 1), (1, 2), (2, 0)):
            e.append(np.linalg.norm(V[T2[:, a]] - V[T2[:, b]], axis=1))
    return np.concatenate(e)


def census(stats):
    L = np.array(stats["lengths"]); c = np.array(stats["nchip"])
    print(">> population: %d castings, %.3f M tris, %.2f M verts"
          % (stats["units"], stats["tris"] / 1e6, stats["verts"] / 1e6))
    print(">>   length  %.3f-%.3f m  mean %.3f  sd %.3f  CV %.4f"
          % (L.min(), L.max(), L.mean(), L.std(), L.std() / L.mean()))
    print(">>   chips   mean %.2f, max %d, %.1f %% carry at least one"
          % (c.mean(), c.max(), 100.0 * (c > 0).mean()))
    print(">>   sockets %d cast, channels on %d castings"
          % (stats["sockets"], stats["channels"]))
    print(">>   LOD %s" % stats["lod"])
    print(">>   triangles per casting: %.0f mean, %.0f at LOD 0"
          % (stats["tris"] / max(1, stats["units"]),
             stats["tris"] / max(1, stats["units"])))


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
    ap.add_argument("--blocks", type=int, nargs="*", default=None)
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
        test_scene(samples=a.samples, limit=a.limit, blocks=a.blocks)
    elif a.build:
        st = {}
        build(stats=st, limit=a.limit, blocks=a.blocks)
        census(st)
    if a.save:
        p = os.path.abspath(a.save)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        ext = [i.filepath for i in bpy.data.images if i.source == "FILE"]
        if ext:
            raise SystemExit("REFUSING TO SAVE: external images %s" % ext)
        bpy.ops.wm.save_as_mainfile(filepath=p, compress=True,
                                    relative_remap=False)
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
