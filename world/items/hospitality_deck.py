#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hospitality_deck.py — CIRCUIT VITRINE, per-item hero campaign, item
``hospitality_deck`` (zone ``paddock``, wave 1, build order 139).

WHAT THIS IS, IN ONE SENTENCE
=============================
The five raised terrace platforms that stand in front of the paddock hospitality
units — every deck board an individually generated solid on a real adjustable-
pedestal sub-frame, with real gaps you see daylight through, real countersunk
fixings, real step nosings worn to different degrees, and five different
perimeter trims.

THE ARITHMETIC THAT DECIDES HOW FAR TO TAKE IT
----------------------------------------------
    px_per_m = (3840 * 35 / 36) / 22.0 = 169.697 px/m   ->   1 px = 5.893 mm

so at the distance the manifest films this item:

    a 145 mm deck board       = 24.61 px  -> every board is an object
    a   7 mm board gap        =  1.19 px  -> a HOLE, not a dark line
    a  16 mm countersink dish =  2.72 px  -> the dish is meshed, the screw sits in it
    a  20 mm trim return      =  3.39 px  -> and throws 90 mm of shadow (see below)
    a   3 mm arris chamfer    =  0.51 px  -> a highlight line, so it is real geometry
    a 600 mm deck height      = 101.82 px -> the manifest's own onscreen_px_4k

THE SUN IS THE REASON MOST OF THIS IS GEOMETRY.  ``world_contract`` puts it at
12.47061 deg elevation, bearing -57.96966 deg.  In the CIRCUIT frame that is
azimuth -97.970 deg — within 8 deg of normal to the deck's front face — so:

  * the 0.6 m front face is in full direct sun and every 20 mm trim return
    throws 20 x cot(12.47) = 90 mm = 15 px of shadow down it.  A bump map does
    not do that.
  * the deck TOP is lit at 12.47 deg grazing.  A 2 mm cupped board edge throws
    9 mm; a 1 mm proud board throws 4.5 mm; a board standing 4 mm proud throws
    18 mm = 3 px.  All of that is modelled as displacement of real vertices.
  * a 7 mm gap between 28 mm boards needs 127 mm of horizontal run to be lit at
    this elevation, so every gap is BLACK.  That only reads if the gap is a hole.

THE PUBLIC INTERFACE  (this item is a FOUNDATION — four items depend on it)
==========================================================================
Named in the manifest as dependants: ``motorhome_unit``, ``folding_chair``,
``folding_table``, ``parasol``.  None of them can ask questions, so every number
they need is a function here and every one of them is measured, not asserted.

--- 0. THE FRAME, and it matters -------------------------------------------

    DECK-LOCAL:  +x is the deck's WIDTH along the hospitality frontage,
                 +y points from the paddock lane TOWARDS the unit,
                 +z is up,
                 the origin is ON THE GROUND at the deck's plan centre
                 (z = C.world_ground_z there, which on the paddock apron is
                 exactly C.APRON_Z = 0.000).

    So the FRONT edge — the one the camera sees, the one the steps come off —
    is at y = -D/2, and the unit threshold is at y = +D/2.  Deck-local z is
    height above grade, so the finished deck level is d.H.

    plan()            -> [Deck x 5]   THE PLACEMENT AUTHORITY for this family.
    site_frame(d)     -> (R, O)       3x3 rotation, 3-vector origin, local->world
    to_world(d, P)    -> (n,3)        apply it to an array of local points
    footprint_world(d)-> (4,2)        the deck outline in world XY, for anyone
                                      who needs to not stand where it stands

--- 1. STANDING ON IT  (folding_chair, folding_table, parasol) ---------------

    deck_top_z(d, x, y) -> z      LOCAL z of the walking surface at local (x,y),
                                  including the board's cup, bow, twist, the
                                  screw dishes, the raised grain and any board
                                  that is standing proud.  It is the SURFACE,
                                  not the nominal plane: over the five decks it
                                  departs from d.H by -3.9 mm .. +4.6 mm.  A
                                  chair leg placed on d.H floats or sinks; a
                                  chair leg placed on this lands.  Never NaN —
                                  over a gap it returns the level a foot
                                  bridging the gap would rest on.

    over_gap(d, x, y)   -> bool   True where (x,y) is over a hole rather than
                                  over board.  A 7 mm gap is 1.19 px and a chair
                                  leg standing in one is a visible lie.
    on_deck(d, x, y)    -> bool   True inside this deck's own outline.

    floor_slots(d)      -> [Slot] the free rectangles left once the traffic
                                  path, the step head, the threshold landings,
                                  the awning anchors and the rail swing are
                                  accounted for.  Each carries its centre, its
                                  half-extents, the board direction under it,
                                  the clear height to the awning, which edge it
                                  faces and a `quality` 0..1.  ``folding_table``
                                  and ``folding_chair`` should place into these,
                                  best `quality` first.

    parasol_bases(d)    -> [...]  the places this module has already built a
                                  load-spreading plate into the deck for a
                                  parasol foot: local (x,y), the deck top z
                                  there, the plate size, and whether the boards
                                  under it are doubled.  ``parasol`` stands on
                                  these; it does not invent its own.

--- 2. BOLTING TO IT  (motorhome_unit, hospitality_awning) -------------------

    threshold(d)        -> Threshold   the REAR edge: the line the unit's own
                                       face must land on, the 0.15 m shadow gap
                                       this module leaves, the closure flashing
                                       it already built, the finished deck level
                                       at the threshold, and the two chequer-
                                       plate door landings with their local x.
                                       ``motorhome_unit`` builds its floor to
                                       `deck_level` and its face at `face_y`.

    unit_bays(d)        -> [Bay x 2]   the flanking bays at each end of the deck
                                       where the motorhome bodies park, with the
                                       clear width, the deck's own side fascia
                                       they abut, and the apron z under them.

    awning_anchors(d)   -> [...]       where ``hospitality_awning``'s legs land:
                                       local (x,y), deck top z, the 200x200x10
                                       base plate and its four M12 studs which
                                       THIS MODULE ALREADY BUILT, and the stud
                                       pattern.  The awning lands on these.

--- 3. THE STEPS AND THE EDGE ------------------------------------------------

    step_runs(d)        -> [Run]   every step run: centre x, clear width, rise,
                                   going, riser count, the nosing profile and
                                   its `wear` 0..1, and the apron z at its foot.
    edge_trim(d)        -> Trim    which of the five perimeter trims this deck
                                   has, its section, and its outer face y/x so
                                   nothing else overlaps it.
    rail(d)             -> Rail    the edge protection: kind, height, post
                                   positions, and the swing clearance that
                                   `floor_slots` has already subtracted.
    under_deck(d)       -> Under   the clear box under the deck, the cable tray
                                   and bundles this module put there, and what
                                   is left free.

--- 4. WHAT VARIES BETWEEN THE FIVE, AND WHERE THE VARIATION LIVES -----------
The manifest names three axes — **board gaps**, **step nosing wear**, **edge
trim** — and all three are GEOMETRY here, not a shader parameter:

  board gaps      4.0 / 5.5 / 7.0 / 9.0 / 11.0 mm, and the gap changes the
                  board count, the board pitch, the screw rows and what you can
                  see of the frame through the deck.  It is a different mesh.
  nosing wear     0.15 / 0.30-0.55 / 0.55 / 0.75 / 0.90.  The carborundum
                  insert's grit is real displaced geometry; wear removes the
                  particles, flattens the strip and rounds the leading arris of
                  the aluminium.  A worn nosing has FEWER VERTICES IN DIFFERENT
                  PLACES than a new one.
  edge trim       five different sections: bronze anodised angle / timber
                  bullnose fascia / folded stainless drip with oil-canning /
                  black PVC bullnose extrusion / aluminium shadow-gap channel.

and on top of those, because three axes is not five different objects:
board axis (x or y), board width, board thickness, board profile (reeded /
smooth / micro-ribbed / wide-reeded), species and weathering, fastening
(face-screwed in four patterns vs. hidden clips on the composite deck), frame
kind (two-tier bearer+joist vs. single-tier close-spaced bearers), pedestal
grid, skirt treatment (composite / open / louvred / painted ply / half-height),
rail (none / cable / glass / mesh / rope), and the plan size itself.

THE GATE MEASURES THE FIVE AS FIVE OBJECTS.  `instances: 5` and this module
emits exactly five meshes, so `item_gate.py` walks real per-object statistics
rather than chunk statistics — there is no geometry-nodes instancing here and
therefore nothing about per-instance variation that goes unmeasured.

WHAT I COULD NOT MEASURE is listed at the bottom of the module, in `selftest`'s
own words, and repeated in the hand-back note.

-------------------------------------------------------------------------------
WHAT LOOKING AT IT FOUND — the second pass, and why iteration is the method
-------------------------------------------------------------------------------
Every one of these passed the acceptance gate before it was fixed.  The gate
measures whether an object COULD look right; only the eye decides whether it
DOES.  Each is documented at the line that fixes it.

  1. THE FASCIA WAS BUBBLEGUM PINK.  `brand_rgb / max(brand_rgb)` turned a
     0.163 aubergine into a full-white blue channel.  A colour divided by its
     own maximum has thrown away the only quantity that decides how bright a
     painted panel is.  -> `brand_paint`, PAINT_MAX.
  2. FOUR TIMBER DECKS RENDERED AS ONE TIMBER.  `species` changed the ring
     pitch and never reached a pixel, because `mat_board` builds its grain from
     oak for all of them.  -> the species ratio is folded into the per-board
     tint in `build_board`.
  3. THE STEP RUN WAS A PAPER MODEL.  8 mm plate stringers, 5 mm plate treads,
     nothing joining them.  -> folded channel stringers, folded tread pans,
     bolts, cleats, base plates, shims, a kick rail.
  4. THE NOSING AND THE RISER WERE ON THE WRONG EDGE OF EVERY TREAD — `ty1`,
     against the deck, instead of `ty0`, the nose.  The manifest's own
     variation axis was being applied to an edge nobody treads on, and the
     stair was see-through from the front.
  5. 26 m OF MESH INFILL WAS EMITTED AT hd_anod = 0.60 — 60 % of the way to
     natural — and came back as a white venetian blind.  -> `rail()` now
     specifies the anodising, graphite for mesh.
  6. THE STEP OPENING IN THE SKIRT WAS A 2.8 x 0.6 m HOLE of unlit void.
     -> returns and a header, which is how the opening is really closed.
  7. A PARASOL PLATE AT hd_wear = 0.5 IS A HALF-MIRROR and returned the sky as
     a flat blue rectangle lying on the boards.
  8. `_convex_hull_tris` EMITTED EVERY SUPPORTING TRIPLE, so each face of a
     chamfered box came out as 56 overlapping triangles instead of 6: 392
     triangles per box against the 68 the shape has.  1.4 M triangles of pure
     duplication, and coincident coplanar faces to render through.
  9. THE MACRO CAMERA READ AS THE WORLD ORIGIN because `matrix_world` is stale
     until the depsgraph updates, so the context paving was laid 300 m away
     from the item it was context for — with every stage reporting success.
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
    from mathutils import Vector
    HAVE_BPY = True
except Exception:                                            # pragma: no cover
    HAVE_BPY = False

_HERE = os.path.dirname(os.path.abspath(__file__))           # .../world/items
_WORLD = os.path.dirname(_HERE)                              # .../world
_ROOT = os.path.dirname(_WORLD)                              # .../f1-round2
for _p in (_HERE, _WORLD, os.path.join(_ROOT, "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import world_contract as C                                   # noqa: E402

# --------------------------------------------------------------------------- ids
ITEM = "hospitality_deck"
PFX = "HD_"
CTX = "CTX_"                     # context objects: NOT part of this item
COLL = "ITEM_HOSPITALITY_DECK"

# --------------------------------------------------- the manifest's own numbers
FILMED_AT_M = 22.0               # nearest_camera_m
LENS_MM = 35.0                   # lens_at_closest_mm
SENSOR_MM = 36.0
RES_X_4K = 3840
PX_PER_M = (RES_X_4K * LENS_MM / SENSOR_MM) / FILMED_AT_M     # 169.697 px/m
PX_M = 1.0 / PX_PER_M                                          # 5.8929 mm
ONSCREEN_PX_4K = 102
INSTANCES = 5
HERO = False                     # manifest: hero=false -> gate limit is 16 px
GATE_EDGE_PX = 16.0
HERO_EDGE_PX = 6.0               # built to the HERO limit anyway
HERO_EDGE_M = HERO_EDGE_PX * PX_M                              # 35.36 mm

BASE_EMBED_M = C.BASE_EMBED_M    # 0.020 — law 5, re-exported for dependants
SEED = 20260729

# circuit -> world is a pure rotation of +40.000 deg about the world Z plus a
# translation; measured from C.circuit_to_world rather than assumed.
_CW_PHI = math.atan2(*(lambda a, b: (float(b[1] - a[1]), float(b[0] - a[0])))(
    C.circuit_to_world(0.0, 0.0), C.circuit_to_world(1.0, 0.0)))

# --------------------------------------------------------------------------- #
#  SITES — five terraces, one per hospitality unit frontage.                   #
#                                                                              #
#  cx        circuit-frame x of the deck's plan centre                         #
#  cy_rear   circuit-frame y of the deck's REAR edge.  The unit frontage is at #
#            cy = 66.000 (build_architecture's hospitality row), and this       #
#            module leaves a 0.15 m shadow gap, so cy_rear = 65.850 on all      #
#            five.  That gap is not decoration: it is where the unit's own      #
#            drip and the deck's closure flashing meet, and `threshold()`       #
#            hands it to motorhome_unit as a number.                            #
#  W, D      deck width along the frontage / depth front-to-back                #
#  H         FINISHED DECK LEVEL above grade.  The manifest's typical_height_m  #
#            is 0.6; these are the five pedestal settings that average to it.   #
#  yaw       setting-out error, degrees.  A deck erected against a building     #
#            face is square to it to about a quarter of a degree, not to zero.  #
#                                                                              #
#  D IS BOUNDED BY THE STEP FOOT, NOT BY THE DECK EDGE.  build_architecture     #
#  round 1 runs a jersey-barrier line along cy = 60.60 across the x spans of    #
#  decks 1, 3 and 5.  The first version of this table sized the decks against   #
#  the BUILDING and got all three clear at the deck edge — and then put their   #
#  step runs, which project 3 x 0.300 m in front of it, 0.23 / 0.15 / 0.40 m    #
#  INSIDE the barrier.  A deck that clears an obstruction everywhere except     #
#  where people actually walk off it has not been sited, it has been drawn.     #
#                                                                               #
#  So decks 1, 3 and 5 are sized from `step foot >= cy 60.95`, which is what    #
#  the site actually permits, and decks 2 and 4 — whose x spans fall in the     #
#  gaps between the three barrier runs — keep their full depth.  That is why    #
#  the depths are 3.72 / 3.86 / 3.94 against 4.62 / 4.72: not a stylistic       #
#  choice, a site constraint, which is how depths get set on a real paddock.    #
#  `selftest` MEASURES this clearance rather than trusting the comment.          #
# --------------------------------------------------------------------------- #
JERSEY_R1 = [(-160.0, -120.0), (-70.0, -30.0), (16.0, 60.0)]   # x spans
JERSEY_R1_CY = 60.60
JERSEY_R1_HALFWIDTH = 0.30

SITES = [
    dict(n=1, name="Versant", cx=-141.50, cy_rear=65.850, W=12.60, D=3.86,
         H=0.548, yaw=+0.22, unit=(-155.0, -126.0),
         axis="y", bw=0.145, bt=0.028, gap=0.0055, profile="reeded",
         species="thermo_ash", fasten="face", pattern=0.28,
         frame="two_tier", ped=(1.22, 1.07),
         trim="alu_angle", skirt="composite", railkind="cable",
         steps=((+2.30, 2.40, 3, 0.75),),
         age=0.55, wet=0.18, oil=0.10,
         shade=(-1.6, 3.4)),
    dict(n=2, name="Ardent", cx=-100.60, cy_rear=65.850, W=15.85, D=4.62,
         H=0.612, yaw=-0.31, unit=(-118.0, -84.0),
         axis="x", bw=0.120, bt=0.032, gap=0.0090, profile="smooth",
         species="bangkirai", fasten="face", pattern=0.33,
         frame="two_tier", ped=(1.34, 1.16),
         trim="timber_fascia", skirt="open", railkind="none",
         steps=((-4.60, 1.60, 3, 0.30), (+5.10, 3.20, 3, 0.55)),
         age=0.86, wet=0.34, oil=0.00,
         shade=(2.0, 5.2)),
    dict(n=3, name="Zephyr", cx=-56.40, cy_rear=65.850, W=10.35, D=3.94,
         H=0.585, yaw=+0.09, unit=(-72.0, -40.0),
         axis="y", bw=0.168, bt=0.026, gap=0.0040, profile="micro_ribbed",
         species="wpc_grey", fasten="hidden", pattern=0.0,
         frame="single", ped=(0.00, 0.42),
         trim="stainless_drip", skirt="louvre", railkind="glass",
         steps=((0.00, 3.60, 3, 0.15),),
         age=0.22, wet=0.12, oil=0.00,
         shade=(-3.0, 1.0)),
    dict(n=4, name="Pallas", cx=-11.30, cy_rear=65.850, W=16.90, D=4.72,
         H=0.660, yaw=-0.14, unit=(-28.0, 6.0),
         axis="y", bw=0.140, bt=0.030, gap=0.0070, profile="reeded_wide",
         species="euro_oak", fasten="face", pattern=0.30,
         frame="two_tier", ped=(1.18, 1.10),
         trim="pvc_bullnose", skirt="painted_ply", railkind="mesh",
         steps=((+4.80, 2.80, 4, 0.55),),
         age=0.62, wet=0.26, oil=0.05,
         shade=(-5.4, 1.8)),
    dict(n=5, name="Halcyon", cx=+40.30, cy_rear=65.850, W=13.70, D=3.72,
         H=0.574, yaw=+0.38, unit=(18.0, 62.0),
         axis="x", bw=0.155, bt=0.028, gap=0.0110, profile="smooth_wide",
         species="iroko", fasten="face", pattern=0.26,
         frame="single", ped=(0.00, 0.44),
         trim="alu_channel", skirt="half", railkind="rope",
         steps=((-3.90, 2.00, 3, 0.90),),
         age=0.44, wet=0.20, oil=0.42,
         shade=(1.2, 5.6)),
]

# --------------------------------------------------------------------------- #
#  PALETTE — LINEAR reflectances, chosen against C.lambert_radiance rather      #
#  than picked in sRGB.  A 0.18 horizontal surface renders at 1.4888 linear     #
#  under this sky, which is what REFERENCE_EXPOSURE_EXTERIOR was solved for.    #
# --------------------------------------------------------------------------- #
P = dict(
    # --- timber decking, five species at five stages of weathering ----------
    ash_early=(0.2320, 0.1640, 0.0870),   # thermally modified ash, earlywood
    ash_late=(0.1180, 0.0770, 0.0390),    # latewood band: darker, harder
    ash_silver=(0.1500, 0.1420, 0.1280),
    bang_early=(0.1240, 0.0720, 0.0340),  # bangkirai, dense red-brown
    bang_late=(0.0640, 0.0340, 0.0170),
    bang_silver=(0.1150, 0.1120, 0.1060),
    oak_early=(0.2050, 0.1520, 0.0850),
    oak_late=(0.1020, 0.0700, 0.0380),
    oak_silver=(0.1620, 0.1560, 0.1440),
    iroko_early=(0.1880, 0.1240, 0.0520),
    iroko_late=(0.0910, 0.0560, 0.0230),
    iroko_silver=(0.1440, 0.1380, 0.1250),
    wpc_face=(0.1560, 0.1540, 0.1470),    # grey wood-plastic composite
    wpc_fleck=(0.0980, 0.0930, 0.0860),
    wpc_chalk=(0.2240, 0.2210, 0.2130),   # chalked, UV-bleached surface
    wood_end=(0.1420, 0.1030, 0.0570),    # end grain: porous, lighter, matt
    wood_knot=(0.0560, 0.0350, 0.0160),
    wood_oiled=(0.0840, 0.0490, 0.0210),  # freshly oiled, much darker
    algae=(0.0330, 0.0510, 0.0270),       # the green-black in a damp gap
    # --- aluminium ----------------------------------------------------------
    anod_bronze=(0.0870, 0.0640, 0.0430),
    anod_black=(0.0270, 0.0270, 0.0290),
    anod_natural=(0.4900, 0.4930, 0.4960),
    anod_champagne=(0.4180, 0.3780, 0.2980),
    mill_alu=(0.4460, 0.4520, 0.4600),
    mill_dull=(0.2680, 0.2720, 0.2780),
    alu_oxide=(0.3050, 0.3080, 0.3050),
    alu_cast=(0.3400, 0.3450, 0.3520),
    # --- steel --------------------------------------------------------------
    stainless=(0.5600, 0.5620, 0.5660),
    stain_dull=(0.3400, 0.3420, 0.3460),
    tea_stain=(0.2050, 0.1420, 0.0780),   # the brown weep off 304 outdoors
    galv=(0.4280, 0.4390, 0.4460),
    rust=(0.1150, 0.0470, 0.0180),
    # --- polymers -----------------------------------------------------------
    pvc_black=(0.0210, 0.0210, 0.0225),
    pvc_grey=(0.0880, 0.0900, 0.0930),
    rubber=(0.0180, 0.0180, 0.0190),
    grit_dark=(0.0290, 0.0280, 0.0270),   # carborundum
    grit_worn=(0.1450, 0.1440, 0.1420),
    resin=(0.0620, 0.0600, 0.0570),
    cable_black=(0.0250, 0.0250, 0.0260),
    cable_blue=(0.0330, 0.0620, 0.1450),
    glass_tint=(0.7400, 0.7800, 0.7600),
    # --- ground / grime -----------------------------------------------------
    conc=(0.2350, 0.2320, 0.2230),
    grime=(0.0480, 0.0450, 0.0400),
    dust=(0.2260, 0.2060, 0.1720),
)

# the six invented brands whose colours the painted skirts and the anodising
# borrow.  Names and colours are build_dressing's brand book, verbatim; NO
# LETTERING is carried by this item, only the colours and the geometric marks.
BRAND = [
    ("VERSANT",  (0.0088, 0.0347, 0.1119), "chevron"),
    ("ARDENT",   (0.7011, 0.0838, 0.0075), "delta"),
    ("ZEPHYR",   (0.0040, 0.2016, 0.3813), "arcs"),
    ("PALLAS",   (0.0975, 0.0243, 0.1626), "ring"),
    ("HALCYON",  (0.0089, 0.0684, 0.0424), "arch"),
    ("KESTREL",  (0.0296, 0.0782, 0.1500), "wing"),
]

# THE BRAND COLOUR IS A REFLECTANCE, NOT A HUE TO BE RENORMALISED.
#
# The first version of the painted skirt did
#
#     tint = brand_rgb / max(brand_rgb)
#
# which took PALLAS's deep aubergine (0.0975, 0.0243, 0.1626) — a linear
# reflectance a real 2-pack purple actually has — and returned
# (0.600, 0.150, 1.000): a BLUE CHANNEL AT FULL WHITE.  Under the contract sun
# at 12.47 deg that panel came back out of AgX as bubblegum pink, and it was the
# brightest, most saturated thing in the macro frame — 4 m2 of a paddock deck
# reading as a toy.  Dividing a colour by its own maximum discards exactly the
# quantity that decides how bright a painted panel is.
#
# So: use the brand colour AS the reflectance, and only ever scale it DOWN.
# PAINT_MAX is the cap.  Cadmium-red powder coat is about the most reflective
# saturated colour that exists outdoors and it measures ~0.34 linear in its
# strongest channel; ARDENT's (0.7011, ...) is a screen colour, not a paint, so
# it gets brought back to that ceiling.  Everything darker is left alone,
# because a navy skirt IS nearly black in full sun and that is what it should
# render as.
PAINT_MAX = 0.34

# ...AND THE SUN IS 4.5x BRIGHTER ON A WALL THAN ON THE GROUND HERE.  At 12.471
# deg elevation a vertical face square to the sun takes cos(12.5 deg) = 0.976 of
# the direct beam where the apron takes cos(77.5 deg) = 0.216.  The reference
# exposure is solved for a HORIZONTAL 0.18 surface, so every vertical face in
# this frame is 4.5 stops of irradiance above what that exposure was set for,
# and AgX desaturates hard at the top: the deep aubergine at its own honest
# 0.163 came out of the second macro as pastel mauve.  It is not the colour that
# is wrong, it is that a panel which has stood in that sun for a season is not
# at its factory reflectance.  WEATHERED is measured off real faded 2-pack: 0.62
# of new, which puts PALLAS at Y = 0.031 and reads as the colour it is.
PAINT_WEATHERED = 0.48


def brand_paint(brand, cap=PAINT_MAX, weathered=PAINT_WEATHERED):
    """Brand colour -> a physically-possible weathered powder-coat reflectance."""
    c = np.array(brand[1], float)
    mx = float(np.max(c))
    c = c * (cap / mx) if mx > cap else c
    return c * float(weathered)

# --------------------------------------------------------------------------- #
#  MATERIAL SLOTS — the same order on every one of the five objects, so         #
#  material_index means the same thing across the whole family.                 #
# --------------------------------------------------------------------------- #
(M_BOARD, M_ANOD, M_MILL, M_STEEL, M_PAINT,
 M_GRIT, M_TRIM, M_GLASS, M_COMP, M_CABLE) = range(10)
MAT_ORDER = ["Board", "Anodised", "MillAlu", "Stainless", "Paint",
             "Grit", "Trim", "Glass", "Composite", "Cable"]

# per-vertex attributes every material reads.  Anything emitting geometry into
# these materials must write all of them; `Acc` defaults them.
ATTR_F = ("hd_wear",    # foot-traffic polish 0..1
          "hd_age",     # UV weathering / silvering 0..1
          "hd_wet",     # standing damp, drives algae and darkening
          "hd_end",     # 1 on end-grain / cut faces
          "hd_grime",   # settled dirt
          "hd_edge",    # nearness to an arris, drives edge wear
          "hd_anod",    # anodising index 0..1 (bronze..natural)
          "hd_paint",   # 1 = powder coated
          "hd_id",      # per-part random, breaks up repeats
          "hd_shade")   # 1 where the awning has kept the UV off
ATTR_V = ("hd_bc",)     # part-local coordinate: x ALONG the grain
ATTR_C = ("hd_tint",)
ATTRS = ATTR_F + ATTR_V + ATTR_C

VERBOSE = True


def log(*a):
    if VERBOSE:
        print(">>", *a)
        sys.stdout.flush()


# ================================================================================
#  1.  DETERMINISTIC NOISE — every number in this file comes from here
# ================================================================================

def h01(*keys):
    """Scalar hash -> [0, 1).  Avalanches: one bit in changes half the bits out."""
    h = np.int64(SEED & 0xFFFFFFFF)
    for k in keys:
        v = np.int64(int(round(float(k) * 1000003.0)) & 0xFFFFFFFF)
        h = np.int64((int(h) ^ int(v)) & 0xFFFFFFFF)
        h = np.int64((int(h) * 2654435761) & 0xFFFFFFFF)
        h = np.int64((int(h) ^ (int(h) >> 15)) & 0xFFFFFFFF)
        h = np.int64((int(h) * 2246822519) & 0xFFFFFFFF)
        h = np.int64((int(h) ^ (int(h) >> 13)) & 0xFFFFFFFF)
    return float(int(h) & 0xFFFFFFFF) / 4294967296.0


def rnd(lo, hi, *keys):
    return lo + (hi - lo) * h01(*keys)


def rint(lo, hi, *keys):
    return int(lo + (hi - lo + 1) * h01(*keys) * 0.999999)


def chance(p, *keys):
    return h01(*keys) < p


def pick(seq, *keys):
    return seq[int(h01(*keys) * len(seq) * 0.999999)]


def _hn(ix, seed):
    """Vectorised integer hash -> [0, 1)."""
    h = (np.asarray(ix, np.int64) & 0xFFFFFFFF) * np.int64(374761393)
    h = (h + np.int64(int(seed) * 668265263)) & np.int64(0xFFFFFFFF)
    h = ((h ^ (h >> 13)) * np.int64(1274126177)) & np.int64(0xFFFFFFFF)
    h = h ^ (h >> 16)
    return (h & np.int64(0xFFFFFFFF)).astype(np.float64) / 4294967296.0


def _hn2(ix, iy, seed):
    a = (np.asarray(ix, np.int64) * np.int64(73856093)) ^ \
        (np.asarray(iy, np.int64) * np.int64(19349663))
    return _hn(a & np.int64(0xFFFFFFFF), seed)


def _s5(t):
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)


def n1(x, seed=0):
    """1-D value noise, C1, period 1."""
    x = np.asarray(x, float)
    i = np.floor(x)
    f = _s5(x - i)
    ii = i.astype(np.int64)
    return _hn(ii, seed) * (1.0 - f) + _hn(ii + 1, seed) * f


def n2(x, y, seed=0):
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    ix, iy = np.floor(x), np.floor(y)
    fx, fy = _s5(x - ix), _s5(y - iy)
    ix = ix.astype(np.int64)
    iy = iy.astype(np.int64)
    a = _hn2(ix, iy, seed)
    b = _hn2(ix + 1, iy, seed)
    c = _hn2(ix, iy + 1, seed)
    d = _hn2(ix + 1, iy + 1, seed)
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def fbm1(x, seed=0, oct=4, lac=2.03, gain=0.5):
    t = np.zeros_like(np.asarray(x, float))
    a, f, s = 1.0, 1.0, 0.0
    for k in range(oct):
        t = t + a * n1(np.asarray(x, float) * f, seed + k * 977)
        s += a
        a *= gain
        f *= lac
    return t / s


def fbm2(x, y, seed=0, oct=4, lac=2.03, gain=0.5):
    t = np.zeros_like(np.asarray(x, float) + np.asarray(y, float))
    a, f, s = 1.0, 1.0, 0.0
    for k in range(oct):
        t = t + a * n2(np.asarray(x, float) * f, np.asarray(y, float) * f,
                       seed + k * 613)
        s += a
        a *= gain
        f *= lac
    return t / s


def sstep(a, b, x):
    t = np.clip((np.asarray(x, float) - a) / (b - a + 1e-12), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


# ================================================================================
#  2.  MESH ACCUMULATOR
# ================================================================================

def place(ob, R, O):
    """Put an object at (R, O) and PROVE it landed there.

    `ob.matrix_world = <4x4>` on a freshly created object does not stick: the
    object's loc/rot/scale stay at the identity and the next depsgraph
    evaluation overwrites the world matrix from them.  That failure mode is
    already in this project's defect log — five decks built correctly and left
    at the world origin, 300 m from the camera pointed at their sites, renders
    back black.  It looks exactly like a lighting bug and is not one.

    So decompose into the channels the depsgraph actually reads, then MEASURE.
    """
    from mathutils import Matrix
    q = Matrix([[float(R[0][0]), float(R[0][1]), float(R[0][2])],
                [float(R[1][0]), float(R[1][1]), float(R[1][2])],
                [float(R[2][0]), float(R[2][1]), float(R[2][2])]]).to_quaternion()
    ob.rotation_mode = "QUATERNION"
    ob.rotation_quaternion = q
    ob.location = (float(O[0]), float(O[1]), float(O[2]))
    ob.scale = (1.0, 1.0, 1.0)
    got = np.array(ob.matrix_basis)
    if (not np.allclose(got[:3, 3], np.asarray(O, float), atol=1e-4)
            or not np.allclose(got[:3, :3], np.asarray(R, float), atol=1e-4)):
        raise RuntimeError(
            "REFUSING: %s did not land at its site. asked for O=%s, got %s"
            % (ob.name, np.round(np.asarray(O, float), 4), np.round(got[:3, 3], 4)))
    return ob


def verify_placement(pairs):
    """Re-check every object's EVALUATED world matrix against its site."""
    bpy.context.view_layer.update()
    bad = []
    for ob, O in pairs:
        got = np.array(ob.matrix_world)[:3, 3]
        if not np.allclose(got, np.asarray(O, float), atol=1e-3):
            bad.append("%s at %s, expected %s"
                       % (ob.name, np.round(got, 3), np.round(np.asarray(O, float), 3)))
    if bad:
        raise RuntimeError("REFUSING: %d object(s) are not at their sites: %s"
                           % (len(bad), "; ".join(bad[:4])))
    log("placement verified: %d objects at their own sites (max |dO| < 1 mm)"
        % len(pairs))


class Acc(object):
    """Vertex/face accumulator carrying the item's per-vertex attribute set.

    ONE Acc PER DECK, so a deck is one object and the gate's per-instance
    statistics are genuinely per instance rather than per fragment.
    """

    def __init__(self, name):
        self.name = name
        self._V, self._Q, self._T, self._mq, self._mt = [], [], [], [], []
        self._sq, self._st = [], []
        self._A = {a: [] for a in ATTR_F}
        self._bc, self._tint = [], []
        self.n = 0
        self.parts = 0

    def add(self, V, quads=None, tris=None, mat=0, bc=None, tint=None,
            smooth=False, **attr):
        V = np.ascontiguousarray(np.asarray(V, np.float64).reshape(-1, 3))
        m = V.shape[0]
        if m == 0:
            return 0
        base = self.n
        self._V.append(V)
        if quads is not None and len(quads):
            q = np.asarray(quads, np.int64).reshape(-1, 4) + base
            self._Q.append(q)
            self._mq.append(np.full(q.shape[0], mat, np.int32))
            self._sq.append(np.full(q.shape[0], bool(smooth), bool))
        if tris is not None and len(tris):
            t = np.asarray(tris, np.int64).reshape(-1, 3) + base
            self._T.append(t)
            self._mt.append(np.full(t.shape[0], mat, np.int32))
            self._st.append(np.full(t.shape[0], bool(smooth), bool))
        for a in ATTR_F:
            v = attr.get(a, 0.0)
            if np.ndim(v) == 0:
                self._A[a].append(np.full(m, float(v), np.float32))
            else:
                self._A[a].append(np.broadcast_to(
                    np.asarray(v, np.float32).ravel(), (m,)).astype(np.float32))
        if bc is None:
            self._bc.append(np.zeros((m, 3), np.float32))
        else:
            b = np.asarray(bc, np.float32)
            self._bc.append(np.ascontiguousarray(
                b.reshape(-1, 3) if b.size > 3 else
                np.broadcast_to(b.reshape(1, 3), (m, 3))).astype(np.float32))
        if tint is None:
            self._tint.append(np.ones((m, 3), np.float32))
        else:
            t = np.asarray(tint, np.float32)
            self._tint.append(np.ascontiguousarray(
                t.reshape(-1, 3) if t.size > 3 else
                np.broadcast_to(t.reshape(1, 3), (m, 3))).astype(np.float32))
        self.n += m
        self.parts += 1
        return base

    def solid(self, V, quads=None, tris=None, **kw):
        """Add a CLOSED solid, orienting every face outward by signed volume.

        Winding is the most tedious bug class in generated geometry and at a
        12.5 deg sun a flipped face reads as a black hole in the frame.  Settle
        it once, here, for every primitive in the file.
        """
        V = np.asarray(V, np.float64).reshape(-1, 3)
        Q = None if quads is None else np.asarray(quads, np.int64).reshape(-1, 4)
        T = None if tris is None else np.asarray(tris, np.int64).reshape(-1, 3)
        vol = 0.0
        if T is not None and len(T):
            a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
            vol += float(np.einsum("ij,ij->i", a, np.cross(b, c)).sum())
        if Q is not None and len(Q):
            for (i, j, k) in ((0, 1, 2), (0, 2, 3)):
                a, b, c = V[Q[:, i]], V[Q[:, j]], V[Q[:, k]]
                vol += float(np.einsum("ij,ij->i", a, np.cross(b, c)).sum())
        if vol < 0.0:
            if Q is not None and len(Q):
                Q = Q[:, ::-1].copy()
            if T is not None and len(T):
                T = T[:, ::-1].copy()
        return self.add(V, quads=Q, tris=T, **kw)

    def build(self, coll, mats, R, O, name=None):
        V = np.concatenate(self._V) if self._V else np.zeros((0, 3))
        Q = np.concatenate(self._Q) if self._Q else np.zeros((0, 4), np.int64)
        T = np.concatenate(self._T) if self._T else np.zeros((0, 3), np.int64)
        mq = np.concatenate(self._mq) if self._mq else np.zeros(0, np.int32)
        mt = np.concatenate(self._mt) if self._mt else np.zeros(0, np.int32)
        sq = np.concatenate(self._sq) if self._sq else np.zeros(0, bool)
        st = np.concatenate(self._st) if self._st else np.zeros(0, bool)
        nv, nq, nt = V.shape[0], Q.shape[0], T.shape[0]
        if nv == 0:
            raise RuntimeError("REFUSING: %s is empty" % self.name)
        nf = nq + nt
        me = bpy.data.meshes.new(name or self.name)
        me.vertices.add(nv)
        me.vertices.foreach_set("co", V.astype(np.float32).ravel())
        me.loops.add(nq * 4 + nt * 3)
        loops = np.empty(nq * 4 + nt * 3, np.int32)
        loops[:nq * 4] = Q.astype(np.int32).ravel()
        loops[nq * 4:] = T.astype(np.int32).ravel()
        me.loops.foreach_set("vertex_index", loops)
        me.polygons.add(nf)
        ls = np.empty(nf, np.int32)
        lt = np.empty(nf, np.int32)
        ls[:nq] = np.arange(nq, dtype=np.int32) * 4
        lt[:nq] = 4
        ls[nq:] = nq * 4 + np.arange(nt, dtype=np.int32) * 3
        lt[nq:] = 3
        me.polygons.foreach_set("loop_start", ls)
        me.polygons.foreach_set("loop_total", lt)
        mi = np.empty(nf, np.int32)
        mi[:nq] = mq
        mi[nq:] = mt
        me.polygons.foreach_set("material_index", mi)
        sm = np.empty(nf, bool)
        sm[:nq] = sq
        sm[nq:] = st
        me.polygons.foreach_set("use_smooth", sm)
        me.update(calc_edges=True)
        for a in ATTR_F:
            at = me.attributes.new(a, "FLOAT", "POINT")
            at.data.foreach_set("value", np.concatenate(self._A[a]))
        bc = me.attributes.new("hd_bc", "FLOAT_VECTOR", "POINT")
        bc.data.foreach_set("vector", np.concatenate(self._bc).ravel())
        tn = me.attributes.new("hd_tint", "FLOAT_COLOR", "POINT")
        tc = np.concatenate(self._tint)
        tc4 = np.ones((tc.shape[0], 4), np.float32)
        tc4[:, :3] = tc
        tn.data.foreach_set("color", tc4.ravel())
        me.validate(verbose=False)
        ob = bpy.data.objects.new(name or self.name, me)
        for m in mats:
            ob.data.materials.append(m)
        coll.objects.link(ob)
        place(ob, R, O)
        return ob, dict(verts=nv, quads=nq, tris=nt,
                        triangles=nq * 2 + nt, parts=self.parts)


# ================================================================================
#  3.  PRIMITIVES — every one closes into a solid, so `Acc.solid` can orient it
# ================================================================================

def _grid_quads(n, m, close_m=False):
    """quad indices for an (n, m) lattice; close_m wraps the second axis."""
    mm = m if close_m else m - 1
    i = np.arange(n - 1)[:, None]
    j = np.arange(mm)[None, :]
    j1 = (j + 1) % m
    a = (i * m + j).ravel()
    b = (i * m + j1).ravel()
    c = ((i + 1) * m + j1).ravel()
    d = ((i + 1) * m + j).ravel()
    return np.stack([a, b, c, d], axis=1)


def _fan(centre_idx, ring, reverse=False):
    m = len(ring)
    a = np.full(m, centre_idx, np.int64)
    b = np.asarray(ring, np.int64)
    c = np.roll(b, -1)
    return np.stack([a, c, b], 1) if reverse else np.stack([a, b, c], 1)


def frames_along(P, up=(0.0, 0.0, 1.0)):
    """Tangent / side / normal at every station of a polyline."""
    P = np.asarray(P, float)
    T = np.empty_like(P)
    if len(P) == 1:
        T[0] = (0.0, 0.0, 1.0)
    else:
        T[1:-1] = P[2:] - P[:-2]
        T[0] = P[1] - P[0]
        T[-1] = P[-1] - P[-2]
    T /= (np.linalg.norm(T, axis=1, keepdims=True) + 1e-15)
    U = np.broadcast_to(np.asarray(up, float), P.shape).copy()
    S = np.cross(U, T)
    bad = np.linalg.norm(S, axis=1) < 1e-6
    if bad.any():
        S[bad] = np.cross(np.array([1.0, 0.0, 0.0]), T[bad])
        bad2 = np.linalg.norm(S, axis=1) < 1e-6
        if bad2.any():
            S[bad2] = np.cross(np.array([0.0, 1.0, 0.0]), T[bad2])
    S /= (np.linalg.norm(S, axis=1, keepdims=True) + 1e-15)
    N = np.cross(T, S)
    N /= (np.linalg.norm(N, axis=1, keepdims=True) + 1e-15)
    return T, S, N


def sweep(acc, P, SEC, mat=0, caps=True, scale=None, roll=None,
          up=(0.0, 0.0, 1.0), close_path=False, bc=None, **kw):
    """Sweep a CLOSED 2-D section along a polyline.  SEC is (M, 2) in (u, v)."""
    P = np.asarray(P, float).reshape(-1, 3)
    SEC = np.asarray(SEC, float).reshape(-1, 2)
    n, m = len(P), len(SEC)
    T, S, N = frames_along(P, up)
    sc = np.ones((n, 2)) if scale is None else \
        np.broadcast_to(np.asarray(scale, float).reshape(-1, 2), (n, 2))
    U = SEC[None, :, 0] * sc[:, 0:1]
    W = SEC[None, :, 1] * sc[:, 1:2]
    if roll is not None:
        r = np.broadcast_to(np.asarray(roll, float).reshape(-1, 1), (n, 1))
        c, s = np.cos(r), np.sin(r)
        U, W = U * c - W * s, U * s + W * c
    V = (P[:, None, :] + U[:, :, None] * S[:, None, :]
         + W[:, :, None] * N[:, None, :]).reshape(-1, 3)
    Q = _grid_quads(n, m, close_m=True)
    if close_path:
        j = np.arange(m)
        j1 = (j + 1) % m
        a = ((n - 1) * m + j)
        b = ((n - 1) * m + j1)
        Q = np.concatenate([Q, np.stack([a, b, j1, j], 1)])
        return acc.solid(V, quads=Q, mat=mat, bc=bc, **kw)
    if not caps:
        return acc.add(V, quads=Q, mat=mat, bc=bc, **kw)
    c0 = P[0] + (U[0].mean() * S[0] + W[0].mean() * N[0])
    c1 = P[-1] + (U[-1].mean() * S[-1] + W[-1].mean() * N[-1])
    V = np.concatenate([V, c0[None, :], c1[None, :]])
    i0, i1 = n * m, n * m + 1
    Tr = np.concatenate([_fan(i0, np.arange(m), reverse=True),
                         _fan(i1, (n - 1) * m + np.arange(m))])
    return acc.solid(V, quads=Q, tris=Tr, mat=mat, bc=bc, **kw)


def hollow(acc, P, OUT, IN, mat=0, up=(0.0, 0.0, 1.0), roll=None, bc=None, **kw):
    """Sweep a HOLLOW extrusion: outer ring, inner ring, annular end caps.

    An aluminium box section cut off square shows its 2.5 mm wall at the end.
    At 169.7 px/m that is 0.42 px — a bright line the eye reads as a hollow
    tube rather than a solid bar, and it costs 4 extra quads per end.
    """
    P = np.asarray(P, float).reshape(-1, 3)
    OUT = np.asarray(OUT, float).reshape(-1, 2)
    IN = np.asarray(IN, float).reshape(-1, 2)
    n, mo, mi = len(P), len(OUT), len(IN)
    if mo != mi:
        raise ValueError("hollow(): outer and inner sections need equal counts")
    T, S, N = frames_along(P, up)
    SEC = np.concatenate([OUT, IN])
    U = SEC[None, :, 0] * np.ones((n, 1))
    W = SEC[None, :, 1] * np.ones((n, 1))
    if roll is not None:
        r = np.broadcast_to(np.asarray(roll, float).reshape(-1, 1), (n, 1))
        c, s = np.cos(r), np.sin(r)
        U, W = U * c - W * s, U * s + W * c
    V = (P[:, None, :] + U[:, :, None] * S[:, None, :]
         + W[:, :, None] * N[:, None, :]).reshape(-1, 3)
    m = mo + mi
    j = np.arange(mo)
    j1 = (j + 1) % mo
    i = np.arange(n - 1)[:, None]
    qo = np.stack([(i * m + j).ravel(), (i * m + j1).ravel(),
                   ((i + 1) * m + j1).ravel(), ((i + 1) * m + j).ravel()], 1)
    qi = np.stack([(i * m + mo + j).ravel(), (i * m + mo + j1).ravel(),
                   ((i + 1) * m + mo + j1).ravel(),
                   ((i + 1) * m + mo + j).ravel()], 1)
    qi = qi[:, ::-1].copy()
    cap0 = np.stack([j, j1, mo + j1, mo + j], 1)
    e = (n - 1) * m
    cap1 = np.stack([e + j, e + j1, e + mo + j1, e + mo + j], 1)[:, ::-1].copy()
    Q = np.concatenate([qo, qi, cap0, cap1])
    return acc.solid(V, quads=Q, mat=mat, bc=bc, **kw)


def circle(r, n=16, phase=0.0):
    a = np.linspace(0.0, 2 * np.pi, n, endpoint=False) + phase
    return np.stack([np.cos(a) * r, np.sin(a) * r], 1)


def rect(w, h, chamfer=0.0, fillet_n=0):
    """Closed rectangular section, optionally chamfered or filleted."""
    hw, hh = w * 0.5, h * 0.5
    c = min(chamfer, hw * 0.9, hh * 0.9)
    if c <= 1e-6:
        return np.array([[-hw, -hh], [hw, -hh], [hw, hh], [-hw, hh]])
    if fillet_n <= 0:
        return np.array([[-hw + c, -hh], [hw - c, -hh], [hw, -hh + c],
                         [hw, hh - c], [hw - c, hh], [-hw + c, hh],
                         [-hw, hh - c], [-hw, -hh + c]])
    pts = []
    for (sx, sy, a0) in ((1, -1, -np.pi / 2), (1, 1, 0.0),
                         (-1, 1, np.pi / 2), (-1, -1, np.pi)):
        cx, cy = sx * (hw - c), sy * (hh - c)
        a = np.linspace(a0, a0 + np.pi / 2, fillet_n + 1)
        pts.append(np.stack([cx + np.cos(a) * c, cy + np.sin(a) * c], 1))
    return np.concatenate(pts)


def tube(acc, p0, p1, r, mat=0, n=16, phase=0.0, smooth=True, **kw):
    return sweep(acc, [p0, p1], circle(r, n, phase), mat=mat, smooth=smooth, **kw)


def box(acc, lo, hi, mat=0, **kw):
    lo = np.asarray(lo, float)
    hi = np.asarray(hi, float)
    V = np.array([[lo[0], lo[1], lo[2]], [hi[0], lo[1], lo[2]],
                  [hi[0], hi[1], lo[2]], [lo[0], hi[1], lo[2]],
                  [lo[0], lo[1], hi[2]], [hi[0], lo[1], hi[2]],
                  [hi[0], hi[1], hi[2]], [lo[0], hi[1], hi[2]]])
    Q = np.array([[0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4],
                  [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]])
    return acc.solid(V, quads=Q, mat=mat, **kw)


def obox(acc, ctr, ex, ey, ez, mat=0, chamfer=0.0, **kw):
    """Oriented box from three half-axis vectors, with a uniform chamfer."""
    ctr = np.asarray(ctr, float)
    ex = np.asarray(ex, float)
    ey = np.asarray(ey, float)
    ez = np.asarray(ez, float)
    if chamfer <= 1e-6:
        S = np.array([[-1, -1, -1], [1, -1, -1], [1, 1, -1], [-1, 1, -1],
                      [-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]], float)
        V = ctr + S[:, 0:1] * ex + S[:, 1:2] * ey + S[:, 2:3] * ez
        Q = np.array([[0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4],
                      [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]])
        return acc.solid(V, quads=Q, mat=mat, **kw)
    lx, ly, lz = np.linalg.norm(ex), np.linalg.norm(ey), np.linalg.norm(ez)
    c = min(chamfer, lx * 0.45, ly * 0.45, lz * 0.45)
    ax, ay, az = 1.0 - c / lx, 1.0 - c / ly, 1.0 - c / lz
    S = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                S.append((sx * ax, sy, sz))
                S.append((sx, sy * ay, sz))
                S.append((sx, sy, sz * az))
    S = np.array(S, float)
    V = ctr + S[:, 0:1] * ex + S[:, 1:2] * ey + S[:, 2:3] * ez
    return acc.solid(V, tris=_chamfer_box_tris(), mat=mat, **kw)


_CHAMFER_TRIS = None


def _chamfer_box_tris():
    """The 24-point chamfered box's triangulation, computed ONCE.

    The point ORDER above is fixed and ax, ay, az are always in [0.55, 1), so
    the hull's topology is the same for every chamfered box in the file.  The
    first version ran a 2,024-combination brute-force hull per call, roughly
    40 ms x 1,200 boxes x 5 decks = four minutes of pure duplicate work.
    """
    global _CHAMFER_TRIS
    if _CHAMFER_TRIS is None:
        S = []
        for sx in (-1, 1):
            for sy in (-1, 1):
                for sz in (-1, 1):
                    S.append((sx * 0.70, sy, sz))
                    S.append((sx, sy * 0.75, sz))
                    S.append((sx, sy, sz * 0.80))
        _CHAMFER_TRIS = _convex_hull_tris(np.array(S, float))
    return _CHAMFER_TRIS


def _convex_hull_tris(V):
    """Convex hull of the <= 24-point chamfered box, ONE triangle set per face.

    THE VERSION THIS REPLACES EMITTED EVERY SUPPORTING TRIPLE.  A chamfered
    box's six main faces carry EIGHT coplanar points each, and every one of the
    C(8,3) = 56 triples through them passes the "all other points on one side"
    test — so each face came out as 56 overlapping triangles instead of 6, with
    mixed winding.  Measured: 392 triangles per chamfered box against the 68 the
    shape actually has, on 1,200+ boxes per deck.  That is where 14 of the item's
    17.1 M triangles came from: not detail, duplication.  Coincident coplanar
    faces are also exactly what causes shading and z-fight artefacts, and they
    make the edge-length statistics meaningless — the "finest decile" was
    measuring the 1 mm gap between a chamfer point and the corner it replaced,
    over and over.

    So: find the supporting planes, GROUP the points by plane, and fan each
    plane's polygon once, ordered by angle about its own centroid with the
    outward normal deciding the winding.  68 triangles, no duplicates, no
    inconsistent normals.
    """
    from itertools import combinations
    n = len(V)
    planes = {}
    for (i, j, k) in combinations(range(n), 3):
        a, b, c = V[i], V[j], V[k]
        nrm = np.cross(b - a, c - a)
        ln = np.linalg.norm(nrm)
        if ln < 1e-12:
            continue
        nrm = nrm / ln
        d = (V - a) @ nrm
        if np.all(d <= 1e-9):
            pass                                   # +nrm already points outward
        elif np.all(d >= -1e-9):
            nrm = -nrm
        else:
            continue                               # not a supporting plane
        key = tuple(np.round(np.append(nrm, float(V[i] @ nrm)), 5))
        planes.setdefault(key, set()).update((i, j, k))
    tris = []
    for key, pts in planes.items():
        nrm = np.array(key[:3], float)
        idx = sorted(pts)
        P = V[idx]
        ctr = P.mean(0)
        u = P[0] - ctr
        u = u - nrm * float(u @ nrm)
        nu = float(np.linalg.norm(u))
        if nu < 1e-12:
            continue
        u /= nu
        w = np.cross(nrm, u)
        ang = np.arctan2((P - ctr) @ w, (P - ctr) @ u)
        ring = [idx[t] for t in np.argsort(ang)]
        for t in range(1, len(ring) - 1):
            tris.append((ring[0], ring[t], ring[t + 1]))
    return np.array(tris, np.int64) if tris else np.zeros((0, 3), np.int64)


def hexnut(acc, ctr, axis, r, h, mat=0, **kw):
    """A hex nut / bolt head: across-flats 2r, chamfered top and bottom."""
    ctr = np.asarray(ctr, float)
    ax = np.asarray(axis, float)
    ax = ax / (np.linalg.norm(ax) + 1e-15)
    rr = r / math.cos(math.pi / 6.0)                 # across corners
    sec = circle(rr, 6, phase=math.pi / 6.0)
    P = np.stack([ctr - ax * h * 0.5, ctr - ax * h * 0.36,
                  ctr + ax * h * 0.36, ctr + ax * h * 0.5])
    sc = np.array([[0.86, 0.86], [1.0, 1.0], [1.0, 1.0], [0.86, 0.86]])
    return sweep(acc, P, sec, mat=mat, scale=sc, up=(1, 0, 0) if abs(ax[2]) > 0.9
                 else (0, 0, 1), **kw)


def washer(acc, ctr, axis, r0, r1, t, mat=0, n=16, **kw):
    ctr = np.asarray(ctr, float)
    ax = np.asarray(axis, float)
    ax = ax / (np.linalg.norm(ax) + 1e-15)
    P = np.stack([ctr - ax * t * 0.5, ctr + ax * t * 0.5])
    return hollow(acc, P, circle(r1, n), circle(r0, n), mat=mat,
                  up=(1, 0, 0) if abs(ax[2]) > 0.9 else (0, 0, 1),
                  smooth=True, **kw)


def helix(p0, axis, r, turns, pitch, n_per_turn=18):
    """Path of a thread ridge, for the pedestal screw jacks."""
    p0 = np.asarray(p0, float)
    ax = np.asarray(axis, float)
    ax = ax / (np.linalg.norm(ax) + 1e-15)
    ref = np.array([1.0, 0.0, 0.0]) if abs(ax[2]) > 0.9 else np.array([0.0, 0.0, 1.0])
    e1 = np.cross(ref, ax)
    e1 /= np.linalg.norm(e1) + 1e-15
    e2 = np.cross(ax, e1)
    n = max(6, int(turns * n_per_turn))
    t = np.linspace(0.0, turns * 2 * np.pi, n)
    return (p0[None, :] + (np.cos(t)[:, None] * e1 + np.sin(t)[:, None] * e2) * r
            + ax[None, :] * (t / (2 * np.pi) * pitch)[:, None])


# ================================================================================
#  4.  THE FIVE DECKS
# ================================================================================

SPECIES = {
    "thermo_ash": dict(early=P["ash_early"], late=P["ash_late"],
                       silver=P["ash_silver"], ring=0.0072, hard=0.55,
                       knots=0.9, raise_grain=0.00075),
    "bangkirai": dict(early=P["bang_early"], late=P["bang_late"],
                      silver=P["bang_silver"], ring=0.0041, hard=0.88,
                      knots=0.25, raise_grain=0.00042),
    "euro_oak": dict(early=P["oak_early"], late=P["oak_late"],
                     silver=P["oak_silver"], ring=0.0095, hard=0.62,
                     knots=1.4, raise_grain=0.00090),
    "iroko": dict(early=P["iroko_early"], late=P["iroko_late"],
                  silver=P["iroko_silver"], ring=0.0063, hard=0.74,
                  knots=0.6, raise_grain=0.00055),
    "wpc_grey": dict(early=P["wpc_face"], late=P["wpc_fleck"],
                     silver=P["wpc_chalk"], ring=0.0028, hard=1.0,
                     knots=0.0, raise_grain=0.00012),
}

# board profiles.  (name -> groove centres as a fraction of the board width,
# groove width m, groove depth m, chamfer m)
PROFILE = {
    "reeded":       dict(n=5, gw=0.0060, gd=0.0030, ch=0.0030, span=0.72),
    "reeded_wide":  dict(n=3, gw=0.0140, gd=0.0035, ch=0.0032, span=0.66),
    "micro_ribbed": dict(n=17, gw=0.0022, gd=0.0009, ch=0.0022, span=0.84),
    "smooth":       dict(n=0, gw=0.0, gd=0.0, ch=0.0035, span=0.0),
    "smooth_wide":  dict(n=0, gw=0.0, gd=0.0, ch=0.0045, span=0.0),
}

TRIM_SECTION = {
    # name -> (outward projection m, drop below deck top m, kind)
    "alu_angle":      (0.040, 0.060, "angle"),
    "timber_fascia":  (0.022, 0.145, "fascia"),
    "stainless_drip": (0.018, 0.052, "drip"),
    "pvc_bullnose":   (0.026, 0.048, "bullnose"),
    "alu_channel":    (0.014, 0.070, "channel"),
}


class Deck(object):
    """One terrace.  Everything derived here so nothing downstream re-derives it."""

    def __init__(self, s):
        self.__dict__.update(s)
        k = float(self.n) * 17.0 + 3.0
        self.k = k
        # --- world frame -----------------------------------------------------
        cyc = self.cy_rear - self.D * 0.5
        wx, wy = C.circuit_to_world(self.cx, cyc)
        self.wx, self.wy = float(wx), float(wy)
        gz, own = C.world_ground_z(self.wx, self.wy)
        if not np.isfinite(gz):
            raise RuntimeError("REFUSING: deck %d sits on terrain-owned ground "
                               "at (%.2f, %.2f); the paddock apron should own it"
                               % (self.n, self.wx, self.wy))
        self.gz = float(gz)
        self.owner = str(own)
        th = _CW_PHI + math.radians(self.yaw)
        c, s_ = math.cos(th), math.sin(th)
        self.R = np.array([[c, -s_, 0.0], [s_, c, 0.0], [0.0, 0.0, 1.0]])
        self.O = np.array([self.wx, self.wy, self.gz])
        # --- build-up --------------------------------------------------------
        self.pitch = self.bw + self.gap
        self.prof = PROFILE[self.profile]
        self.sp = SPECIES[self.species]
        if self.frame == "two_tier":
            self.joist_h, self.joist_w = 0.080, 0.040
            self.bearer_h, self.bearer_w = 0.100, 0.050
            self.joist_cc = 0.400 if self.bw < 0.150 else 0.450
        else:
            self.joist_h, self.joist_w = 0.100, 0.050
            self.bearer_h, self.bearer_w = 0.0, 0.0
            self.joist_cc = self.ped[1]
        self.joist_top = self.H - self.bt
        self.bearer_top = self.joist_top - self.joist_h
        self.ped_top = (self.bearer_top - self.bearer_h if self.frame == "two_tier"
                        else self.joist_top - self.joist_h)
        # --- the traffic path: step head -> the busiest unit door -------------
        sx = self.steps[0][0]
        self.path_x0 = sx
        self.path_x1 = rnd(-0.30, 0.30, k, 41) * self.W * 0.5 + self.W * 0.10
        self.path_w = rnd(0.85, 1.25, k, 42)
        # --- named brand for the painted / anodised parts ---------------------
        self.brand = BRAND[(self.n - 1) % len(BRAND)]
        # --- derived deck-plane helpers --------------------------------------
        self._boards = None
        self._joists = None

    # ------------------------------------------------------------------ frame
    @property
    def x0(self):
        return -self.W * 0.5

    @property
    def x1(self):
        return self.W * 0.5

    @property
    def y0(self):
        return -self.D * 0.5

    @property
    def y1(self):
        return self.D * 0.5


def plan():
    return [Deck(s) for s in SITES]


def site_frame(d):
    """Deck-local -> world.  Returns (R 3x3, O 3-vector)."""
    return d.R, d.O


def to_world(d, Pl):
    return np.asarray(Pl, float).reshape(-1, 3) @ d.R.T + d.O


def footprint_world(d, margin=0.0):
    """The deck outline in world XY, counter-clockwise.  For anyone who has to
    not stand where this stands."""
    m = margin
    Pl = np.array([[d.x0 - m, d.y0 - m, 0.0], [d.x1 + m, d.y0 - m, 0.0],
                   [d.x1 + m, d.y1 + m, 0.0], [d.x0 - m, d.y1 + m, 0.0]])
    return to_world(d, Pl)[:, :2]


# ================================================================================
#  5.  BOARD LAYOUT — the boards are the item; everything else carries them
# ================================================================================

def joist_lines(d):
    """LOCAL coordinates of every board support, in the across-board axis.

    Boards run along `d.axis`; the supports run across it.  For `two_tier` those
    are joists on bearers; for `single` they are close-spaced bearers straight
    on the pedestals and there is no second tier.
    """
    if d._joists is not None:
        return d._joists
    span = d.D if d.axis == "y" else d.W
    lo = (-d.D * 0.5 if d.axis == "y" else -d.W * 0.5)
    n = max(2, int(round(span / d.joist_cc)) + 1)
    t = np.linspace(lo + 0.045, lo + span - 0.045, n)
    d._joists = t
    return t


def board_layout(d):
    """Every board PIECE on this deck, as a record.  The list IS the deck.

    Boards are laid from the FRONT edge (or the -x end) with the last board
    ripped to fit, which is what actually happens on site and is why the last
    board is a different width from all the others.
    """
    if d._boards is not None:
        return d._boards
    across = d.W if d.axis == "y" else d.D
    a_lo = (-d.W * 0.5 if d.axis == "y" else -d.D * 0.5)
    along = d.D if d.axis == "y" else d.W
    t_lo = (-d.D * 0.5 if d.axis == "y" else -d.W * 0.5)
    sup = joist_lines(d)

    nfull = int(math.floor((across + d.gap) / d.pitch))
    rip = across - (nfull * d.pitch - d.gap)
    if rip < 0.035:                      # too thin to lay: widen the gaps instead
        nfull -= 1
        rip = across - (nfull * d.pitch - d.gap)

    out = []
    for r in range(nfull + 1):
        w = d.bw if r < nfull else rip
        if w < 0.030:
            continue
        a0 = a_lo + r * d.pitch
        wc = a0 + w * 0.5
        kk = d.k * 100.0 + r
        # ---- how many pieces this run is made of, and where they butt -------
        maxlen = rnd(3.6, 5.4, kk, 11)
        if along <= maxlen + 0.2:
            cuts = [t_lo, t_lo + along]
        else:
            npc = int(math.ceil(along / maxlen))
            # butt joints land ON a support, staggered run to run
            share = along / npc
            cuts = [t_lo]
            for q in range(1, npc):
                want = t_lo + share * q + rnd(-0.45, 0.45, kk, 12 + q)
                j = sup[int(np.argmin(np.abs(sup - want)))]
                cuts.append(float(j))
            cuts.append(t_lo + along)
            cuts = sorted(set(round(v, 5) for v in cuts))
        for pi in range(len(cuts) - 1):
            t0, t1 = cuts[pi], cuts[pi + 1]
            L = t1 - t0
            if L < 0.12:
                continue
            pk = kk * 10.0 + pi
            replaced = chance(0.045, pk, 21)
            lifted = chance(0.020, pk, 22)
            age = float(np.clip(d.age + rnd(-0.16, 0.16, pk, 23)
                                - (0.55 if replaced else 0.0), 0.02, 1.0))
            rec = dict(
                run=r, piece=pi, w=w, wc=wc, t0=t0, t1=t1, L=L,
                replaced=replaced, lifted=lifted, age=age,
                # cup: weathered boards cup UP at the edges as the top dries
                cup=(rnd(0.0008, 0.0032, pk, 24) * (0.35 + age)
                     * (0.25 if d.species == "wpc_grey" else 1.0)),
                crown=rnd(-0.0006, 0.0006, pk, 25),
                bow=rnd(-0.0022, 0.0022, pk, 26) * min(1.0, L / 3.0),
                twist=rnd(-0.0035, 0.0035, pk, 27) / max(L, 0.5),
                proud=(rnd(0.0025, 0.0055, pk, 28) if lifted else
                       rnd(-0.0009, 0.0012, pk, 29)),
                tone=rnd(-1.0, 1.0, pk, 30),
                wet=float(np.clip(d.wet + rnd(-0.12, 0.20, pk, 31), 0.0, 1.0)),
                oil=(d.oil * rnd(0.3, 1.0, pk, 32)),
                grain_off=rnd(0.0, 90.0, pk, 33),
                knot=[], split=[], screws=[])
            # ---- knots ------------------------------------------------------
            nk = int(d.sp["knots"] * L * rnd(0.4, 1.6, pk, 34))
            for q in range(nk):
                rec["knot"].append((t0 + rnd(0.06, L - 0.06, pk, 35 + q),
                                    rnd(-0.34, 0.34, pk, 60 + q) * w,
                                    rnd(0.008, 0.021, pk, 80 + q)))
            # ---- fixings ----------------------------------------------------
            if d.fasten == "face":
                for j in sup:
                    if not (t0 + 0.028 <= j <= t1 - 0.028):
                        continue
                    for sgn in (-1.0, 1.0):
                        sw = sgn * d.pattern * w
                        rec["screws"].append(dict(
                            t=float(j), w=float(sw),
                            missing=chance(0.011, pk, 120 + int(j * 977)),
                            proud=rnd(-0.0016, 0.0011, pk, 140 + int(j * 977)),
                            skew=rnd(-0.10, 0.10, pk, 160 + int(j * 977)),
                            rust=h01(pk, 180 + int(j * 977))))
            # ---- splits, radiating from an end fixing ------------------------
            if chance(0.085 + 0.10 * age, pk, 36) and d.species != "wpc_grey":
                e = 0 if chance(0.5, pk, 37) else 1
                sl = rnd(0.05, 0.26, pk, 38)
                sw = rnd(-0.30, 0.30, pk, 39) * w
                rec["split"].append(dict(end=e, len=sl, w=float(sw),
                                         depth=rnd(0.004, 0.011, pk, 40),
                                         open=rnd(0.0009, 0.0028, pk, 41)))
            out.append(rec)
    d._boards = out
    return out


def _board_of(d, a):
    """Which board covers across-coordinate `a`?  -> (rec-list-index, None)."""
    bs = board_layout(d)
    a_lo = (-d.W * 0.5 if d.axis == "y" else -d.D * 0.5)
    r = int(math.floor((a - a_lo) / d.pitch))
    best = None
    for rec in bs:
        if rec["run"] != r:
            continue
        if abs(a - rec["wc"]) <= rec["w"] * 0.5:
            best = rec
            break
    return best


def board_top_disp(d, rec, t, w):
    """LOCAL height of the board's top surface above the nominal deck plane.

    Vectorised over t and w together (broadcast).  This is the SAME function the
    mesh is built from, which is the only way `deck_top_z` can be trusted by an
    agent that never sees the mesh.
    """
    t = np.asarray(t, float)
    w = np.asarray(w, float)
    hw = rec["w"] * 0.5
    u = np.clip(w / max(hw, 1e-6), -1.0, 1.0)
    s = (t - rec["t0"]) / max(rec["L"], 1e-6)
    # cup (edges up, centre down) + crown, dying out at the supported ends
    z = rec["cup"] * (u * u - 0.34) + rec["crown"] * (1.0 - u * u)
    # bow along the length, zero at the ends where it is screwed down
    z = z + rec["bow"] * np.sin(np.pi * np.clip(s, 0.0, 1.0))
    # twist
    z = z + rec["twist"] * (t - (rec["t0"] + rec["t1"]) * 0.5) * u * hw
    z = z + rec["proud"]
    # raised grain: the softer earlywood erodes and the latewood stands proud
    rg = d.sp["raise_grain"] * (0.25 + 0.95 * rec["age"])
    g = np.sin((w * 6.5 + t * 0.35 + rec["grain_off"]) / d.sp["ring"] * 0.55)
    z = z + rg * (0.5 + 0.5 * np.sign(g) * np.abs(g) ** 0.6)
    # foot traffic sands the grain flat again
    tw = traffic(d, t, w, rec)
    z = z - rg * 0.85 * tw
    # knots stand proud, they are harder than the wood around them
    for (kt, kw, kr) in rec["knot"]:
        rr = np.hypot(t - kt, (w - kw) * 1.9) / max(kr, 1e-5)
        z = z + 0.0011 * (1.0 + 0.9 * rec["age"]) * np.clip(1.0 - rr * rr, 0.0, 1.0)
    # countersink dishes
    for sc in rec["screws"]:
        rr = np.hypot(t - sc["t"], w - sc["w"]) / 0.0080
        z = z - 0.0021 * np.clip(1.0 - rr * rr, 0.0, 1.0)
    # splits
    for sp in rec["split"]:
        te = rec["t0"] if sp["end"] == 0 else rec["t1"]
        along = np.abs(t - te)
        f = np.clip(1.0 - along / max(sp["len"], 1e-6), 0.0, 1.0)
        acr = np.clip(1.0 - np.abs(w - sp["w"]) / max(sp["open"] * 1.6, 1e-6),
                      0.0, 1.0)
        z = z - sp["depth"] * f * acr
    return z


def traffic(d, t, w, rec=None):
    """0..1 foot-traffic exposure at a local across/along coordinate."""
    if d.axis == "y":
        x = (rec["wc"] + w) if rec is not None else w
        y = t
    else:
        x = t
        y = (rec["wc"] + w) if rec is not None else w
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    # the path runs from the step head to the busiest door
    ay, by = d.y0 + 0.35, d.y1 - 0.45
    ax, bx = d.path_x0, d.path_x1
    s = np.clip((y - ay) / max(by - ay, 1e-6), 0.0, 1.0)
    cx = ax + (bx - ax) * s
    wob = 0.16 * (fbm1(y * 0.9 + d.k, int(d.k) * 7 + 5, 3) - 0.5)
    dd = np.abs(x - cx - wob) / (d.path_w * (0.65 + 0.55 * s))
    return np.clip(1.0 - dd * dd, 0.0, 1.0) * (0.55 + 0.45 * (1.0 - s))


def deck_top_z(d, x, y):
    """LOCAL z of the WALKING SURFACE at local (x, y).

    Includes cup, bow, twist, raised grain, screw dishes and any board standing
    proud.  Never NaN: over a gap it returns the level a foot bridging the gap
    would rest on, which is where a chair leg actually ends up.
    """
    scalar = (np.ndim(x) == 0 and np.ndim(y) == 0)
    x = np.atleast_1d(np.asarray(x, float))
    y = np.atleast_1d(np.asarray(y, float))
    a = x if d.axis == "y" else y
    t = y if d.axis == "y" else x
    A, T = np.broadcast_arrays(a, t)
    out = np.full(A.shape, d.H, float)
    a_lo = (-d.W * 0.5 if d.axis == "y" else -d.D * 0.5)
    run = np.floor((A - a_lo) / d.pitch).astype(np.int64)
    for rec in board_layout(d):
        m = ((run == rec["run"]) & (np.abs(A - rec["wc"]) <= rec["w"] * 0.5)
             & (T >= rec["t0"]) & (T <= rec["t1"]))
        if not m.any():
            continue
        out[m] = d.H + board_top_disp(d, rec, T[m], A[m] - rec["wc"])
    return float(out.ravel()[0]) if scalar else out


def over_gap(d, x, y):
    """True where (x, y) is over a HOLE rather than over board."""
    x = np.atleast_1d(np.asarray(x, float))
    y = np.atleast_1d(np.asarray(y, float))
    a = x if d.axis == "y" else y
    t = y if d.axis == "y" else x
    A, T = np.broadcast_arrays(np.asarray(a, float), np.asarray(t, float))
    hit = np.zeros(A.shape, bool)
    a_lo = (-d.W * 0.5 if d.axis == "y" else -d.D * 0.5)
    run = np.floor((A - a_lo) / d.pitch).astype(np.int64)
    for rec in board_layout(d):
        hit |= ((run == rec["run"]) & (np.abs(A - rec["wc"]) <= rec["w"] * 0.5)
                & (T >= rec["t0"] - 1e-6) & (T <= rec["t1"] + 1e-6))
    return ~hit


def on_deck(d, x, y, margin=0.0):
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    return ((x >= d.x0 + margin) & (x <= d.x1 - margin)
            & (y >= d.y0 + margin) & (y <= d.y1 - margin))


# ================================================================================
#  6.  THE BOARD ITSELF
# ================================================================================

def board_section(d, rec):
    """-> (SEC (M,2), tw (M,), tag (M,)) for ONE board.

    SEC[:,0] is across the board from -w/2 to +w/2; SEC[:,1] is height relative
    to the board's nominal top face (0) down to -bt.  `tw` is how strongly each
    section vertex follows the TOP surface displacement (1) rather than the
    bottom (0), so the cup, the grain and the screw dishes deform the top face
    and its arrises and die out through the thickness.  `tag` is 0 top face,
    1 chamfer, 2 side, 3 bottom, 4 groove wall — it drives `hd_edge`.

    The across-sample spacing is 5 mm.  At 169.7 px/m that is 0.85 px, so the
    cup is a curve and not three facets, and a 6 mm reeded groove has four
    samples in it instead of being a stripe in a texture.
    """
    w, t = rec["w"], d.bt
    hw = w * 0.5
    pr = d.prof
    ch = pr["ch"]
    step = 0.005
    # --- across-sample list, refined where geometry needs it -----------------
    xs = list(np.arange(-hw + ch, hw - ch + 1e-9, step))
    if not xs or xs[-1] < hw - ch - 1e-9:
        xs.append(hw - ch)
    grooves = []
    if pr["n"] > 0:
        span = w * pr["span"]
        for q in range(pr["n"]):
            gc = (-span * 0.5 + span * (q + 0.5) / pr["n"]) if pr["n"] > 1 else 0.0
            grooves.append(gc)
            g2 = pr["gw"] * 0.5
            xs += [gc - g2, gc - g2 * 0.62, gc + g2 * 0.62, gc + g2]
    for sp in rec["split"]:
        o = sp["open"]
        xs += [sp["w"] - o * 1.7, sp["w"] - o, sp["w"] - o * 0.35,
               sp["w"], sp["w"] + o * 0.35, sp["w"] + o, sp["w"] + o * 1.7]
    for sc in rec["screws"]:
        for dv in (-0.009, -0.005, -0.0025, 0.0, 0.0025, 0.005, 0.009):
            xs.append(sc["w"] + dv)
    xs = np.array(sorted(set(round(v, 6) for v in xs)))
    xs = xs[(xs >= -hw + ch - 1e-9) & (xs <= hw - ch + 1e-9)]

    # --- the top polyline ----------------------------------------------------
    hs = np.zeros_like(xs)
    tag = np.zeros(len(xs), np.int8)
    for gc in grooves:
        g2 = pr["gw"] * 0.5
        m = np.abs(xs - gc) <= g2 + 1e-9
        prof = np.clip((np.abs(xs - gc) - g2 * 0.62) / (g2 * 0.38 + 1e-9), 0.0, 1.0)
        hs[m] = -pr["gd"] * (1.0 - prof[m])
        tag[m] = 4
    for sp in rec["split"]:
        m = np.abs(xs - sp["w"]) <= sp["open"] * 1.7
        tag[m] = 4
    # hidden-clip decks have a groove machined in each edge for the clip
    clipg = (d.fasten == "hidden")

    pts = [(-hw, -ch), (-hw + ch, 0.0)]
    tg = [1, 1]
    tws = [1.0, 1.0]
    for i in range(len(xs)):
        pts.append((float(xs[i]), float(hs[i])))
        tg.append(int(tag[i]))
        tws.append(1.0)
    pts += [(hw - ch, 0.0), (hw, -ch)]
    tg += [1, 1]
    tws += [1.0, 1.0]
    # --- right side, bottom, left side --------------------------------------
    cb = min(0.0022, t * 0.16)
    if clipg:
        pts += [(hw, -t * 0.30), (hw - 0.0055, -t * 0.40),
                (hw - 0.0055, -t * 0.56), (hw, -t * 0.66)]
        tg += [2, 4, 4, 2]
        tws += [0.55, 0.45, 0.35, 0.28]
    pts += [(hw, -t + cb), (hw - cb, -t)]
    tg += [2, 1]
    tws += [0.10, 0.02]
    nb = max(3, int(w / 0.020))
    for q in range(nb - 1, 0, -1):
        pts.append((-hw + cb + (w - 2 * cb) * q / nb, -t))
        tg.append(3)
        tws.append(0.0)
    pts += [(-hw + cb, -t), (-hw, -t + cb)]
    tg += [1, 2]
    tws += [0.02, 0.10]
    if clipg:
        pts += [(-hw, -t * 0.66), (-hw + 0.0055, -t * 0.56),
                (-hw + 0.0055, -t * 0.40), (-hw, -t * 0.30)]
        tg += [2, 4, 4, 2]
        tws += [0.28, 0.35, 0.45, 0.55]
    SEC = np.array(pts, float)
    return SEC, np.array(tws, float), np.array(tg, np.int8)


def board_stations(d, rec):
    """Along-board sample list, refined at the fixings, splits and ends."""
    L = rec["L"]
    ds = 0.035
    base = list(np.arange(0.0, L + 1e-9, ds))
    if base[-1] < L - 1e-9:
        base.append(L)
    extra = []
    for sc in rec["screws"]:
        ts = sc["t"] - rec["t0"]
        for dv in (-0.018, -0.009, -0.0045, 0.0, 0.0045, 0.009, 0.018):
            v = ts + dv
            if 0.002 < v < L - 0.002:
                extra.append(v)
    for (kt, kw, kr) in rec["knot"]:
        ts = kt - rec["t0"]
        for dv in (-kr, -kr * 0.5, 0.0, kr * 0.5, kr):
            v = ts + dv
            if 0.002 < v < L - 0.002:
                extra.append(v)
    for sp in rec["split"]:
        e = 0.0 if sp["end"] == 0 else L
        for v in np.linspace(0.0, sp["len"], 9):
            vv = e + v if sp["end"] == 0 else e - v
            if 0.0 <= vv <= L:
                extra.append(vv)
    for e in (0.0, L):
        for dv in (0.0018, 0.0045, 0.010):
            extra.append(e + dv if e == 0.0 else e - dv)
    T = np.unique(np.round(np.array(base + extra, float), 6))
    return T[(T >= -1e-9) & (T <= L + 1e-9)]


def build_board(acc, d, rec, lod=1.0):
    """One deck board, as a closed solid with its own history."""
    SEC, TW, TAG = board_section(d, rec)
    TS = board_stations(d, rec)
    if lod < 1.0:
        TS = TS[::max(1, int(round(1.0 / max(lod, 0.05))))]
        if TS[-1] < rec["L"] - 1e-9:
            TS = np.append(TS, rec["L"])
    n, m = len(TS), len(SEC)
    t_abs = rec["t0"] + TS
    W2 = SEC[:, 0]
    H0 = SEC[:, 1]
    TT, WW = np.meshgrid(t_abs, W2, indexing="ij")
    disp_top = board_top_disp(d, rec, TT, WW)
    # the underside sags a little between supports and is otherwise flat
    s = np.clip((TT - rec["t0"]) / max(rec["L"], 1e-6), 0.0, 1.0)
    disp_bot = rec["proud"] + rec["bow"] * 0.75 * np.sin(np.pi * s)
    Z = H0[None, :] + TW[None, :] * disp_top + (1.0 - TW[None, :]) * disp_bot
    # end chamfer: a sawn board's arris is knocked off, more so when weathered
    ech = 0.0016 + 0.0022 * rec["age"]
    de = np.minimum(TT - rec["t0"], rec["t1"] - TT)
    Z = Z - np.clip(1.0 - de / ech, 0.0, 1.0) * ech * 0.55 * TW[None, :]
    WOUT = WW.copy()
    for sp in rec["split"]:
        te = rec["t0"] if sp["end"] == 0 else rec["t1"]
        f = np.clip(1.0 - np.abs(TT - te) / max(sp["len"], 1e-6), 0.0, 1.0)
        near = np.abs(WW - sp["w"]) <= sp["open"] * 1.75
        WOUT = WOUT + np.sign(WW - sp["w"] + 1e-9) * sp["open"] * 0.45 * f * near

    if d.axis == "y":
        V = np.stack([rec["wc"] + WOUT, TT, d.H + Z], -1).reshape(-1, 3)
        bcv = np.stack([TT - rec["t0"], WOUT, Z], -1).reshape(-1, 3)
    else:
        V = np.stack([TT, rec["wc"] + WOUT, d.H + Z], -1).reshape(-1, 3)
        bcv = np.stack([TT - rec["t0"], WOUT, Z], -1).reshape(-1, 3)

    Q = _grid_quads(n, m, close_m=True)
    c0 = V[:m].mean(0)
    c1 = V[(n - 1) * m:].mean(0)
    V = np.concatenate([V, c0[None, :], c1[None, :]])
    bcv = np.concatenate([bcv, bcv[:m].mean(0)[None, :], bcv[(n - 1) * m:].mean(0)[None, :]])
    i0, i1 = n * m, n * m + 1
    Tr = np.concatenate([_fan(i0, np.arange(m), reverse=True),
                         _fan(i1, (n - 1) * m + np.arange(m))])

    # ---- per-vertex history -------------------------------------------------
    tw = traffic(d, TT, WW, rec).ravel()
    edge = np.where(TAG == 1, 1.0, np.where(TAG == 4, 0.55,
                    np.where(TAG == 2, 0.30, 0.06)))
    edge = np.broadcast_to(edge[None, :], (n, m)).ravel()
    endm = np.clip(1.0 - de / 0.006, 0.0, 1.0).ravel()
    endv = np.concatenate([endm, [1.0, 1.0]])
    # the gap edges stay damp, and the shaded end of the deck never dries
    if d.axis == "y":
        gx, gy = (rec["wc"] + WOUT).ravel(), TT.ravel()
    else:
        gx, gy = TT.ravel(), (rec["wc"] + WOUT).ravel()
    shade = sstep(d.shade[0] - 0.8, d.shade[0] + 0.4, gx) * \
        (1.0 - sstep(d.shade[1] - 0.4, d.shade[1] + 0.8, gx))
    wet = np.clip(rec["wet"] * (0.55 + 0.75 * edge) * (0.7 + 0.6 * shade)
                  + 0.22 * np.clip(1.0 - np.abs(gy - d.y1) / 0.5, 0.0, 1.0), 0.0, 1.0)
    age = np.clip(rec["age"] * (1.0 - 0.42 * shade) - 0.30 * tw, 0.0, 1.0)
    grime = np.clip(0.18 + 0.55 * edge * (0.4 + rec["wet"]) - 0.35 * tw
                    + 0.25 * shade, 0.0, 1.0)
    # A PER-BOARD MULTIPLIER, not a colour to be renormalised.  The first
    # version built `species_colour * (1 + 0.14*tone)` and then divided by its
    # own largest channel -- a scalar times a colour, normalised by the max of
    # that same product, is the SAME colour for every value of `tone`.  508
    # boards, one tone.  A board's variation is hue AND value, and the two are
    # not the same axis: heartwood runs redder, sapwood runs paler and greyer,
    # and a replacement board is both fresher and lighter than its neighbours.
    tn = rec["tone"]
    val = 1.0 + 0.13 * tn + (0.26 if rec["replaced"] else 0.0)
    tint = np.array([val * (1.0 + 0.15 * tn),
                     val * (1.0 + 0.05 * tn),
                     val * (1.0 - 0.11 * tn)], float)
    tint = np.clip(tint * (1.0 + 0.09 * (h01(d.k, rec["run"], 77) - 0.5)),
                   0.60, 1.60)
    # ...AND THE SPECIES, which until now never reached a pixel.  `mat_board`
    # builds its grain from SPECIES["euro_oak"] because one shader has to serve
    # all four timber decks; the species is carried HERE, as the ratio of this
    # species' earlywood reflectance to oak's.  Without it, `species` was a
    # field in the site table that changed the ring pitch and nothing else, and
    # thermo-ash, bangkirai, oak and iroko all rendered as the same brown —
    # four decks, one timber, which is the "one asset spammed" failure wearing a
    # different name.  Bangkirai comes out at 0.60/0.47/0.40 of oak (dense, dark
    # red-brown) and iroko at 0.92/0.82/0.61 (golden), which is what they are.
    # Applied AFTER the clip: a legitimate 0.40 species factor is not a stray
    # per-board outlier and must not be clamped away.
    if d.species != "wpc_grey":
        ref = np.array(SPECIES["euro_oak"]["early"], float)
        tint = tint * (np.array(d.sp["early"], float) / ref)
    ex = dict(hd_wear=np.concatenate([tw, [tw[:m].mean(), tw[-m:].mean()]]),
              hd_age=np.concatenate([age, [age[:m].mean(), age[-m:].mean()]]),
              hd_wet=np.concatenate([wet, [wet[:m].mean(), wet[-m:].mean()]]),
              hd_end=endv,
              hd_grime=np.concatenate([grime, [grime[:m].mean(), grime[-m:].mean()]]),
              hd_edge=np.concatenate([edge, [1.0, 1.0]]),
              hd_id=h01(d.k, rec["run"], rec["piece"]),
              hd_shade=np.concatenate([shade, [shade[:m].mean(), shade[-m:].mean()]]),
              hd_anod=0.0, hd_paint=0.0)
    mat = M_COMP if d.species == "wpc_grey" else M_BOARD
    acc.solid(V, quads=Q, tris=Tr, mat=mat, bc=bcv, tint=tint, **ex)


def build_screw(acc, d, rec, sc, lod=1.0):
    """A countersunk deck screw sitting in the dish this module cut for it.

    A 4.5 mm head is 0.76 px, which is below the pixel — but the 16 mm dish is
    2.72 px, the head's shadow inside it at a 12.47 deg sun is 2.5 px long, and
    over 10,700 fixings the pattern of them IS the deck's surface.  So the head
    is a solid with a real recess and the dish is real displaced board.
    """
    if sc["missing"]:
        return
    t, w = sc["t"], sc["w"]
    if d.axis == "y":
        x, y = rec["wc"] + w, t
    else:
        x, y = t, rec["wc"] + w
    z = d.H + board_top_disp(d, rec, np.array([t]), np.array([w]))[0]
    ax = np.array([sc["skew"] * 0.10, sc["skew"] * 0.07, 1.0])
    ax /= np.linalg.norm(ax)
    top = np.array([x, y, z + sc["proud"]])
    n = 12 if lod >= 1.0 else 8
    # head: a countersunk cone, then the shank into the board
    Pth = np.stack([top, top - ax * 0.0024, top - ax * 0.0090])
    sec = circle(1.0, n)
    scl = np.array([[0.00440, 0.00440], [0.00300, 0.00300], [0.00215, 0.00215]])
    sweep(acc, Pth, sec, mat=M_STEEL, scale=scl, smooth=True,
          hd_id=sc["rust"], hd_edge=0.8, hd_grime=0.35 + 0.4 * sc["rust"],
          hd_wet=rec["wet"], hd_anod=0.0)
    # the torx recess: six lobes, 1.1 mm deep
    a = np.linspace(0, 2 * np.pi, 12, endpoint=False)
    rr = np.where(np.arange(12) % 2 == 0, 0.00185, 0.00105)
    star = np.stack([np.cos(a) * rr, np.sin(a) * rr], 1)
    Pr = np.stack([top + ax * 0.00012, top - ax * 0.00110])
    sweep(acc, Pr, star, mat=M_STEEL, hd_id=sc["rust"], hd_edge=0.5,
          hd_grime=0.55, hd_wet=rec["wet"])


# ================================================================================
#  7.  WHAT HOLDS IT UP
# ================================================================================

def pedestal_grid(d):
    """LOCAL (x, y) of every adjustable pedestal, and the head z it is set to.

    Law 5: the base plate BOTTOM sits at -BASE_EMBED_M, never at 0.  The apron
    is dead flat here (C.world_ground_z returns C.APRON_Z = 0.000 across the
    whole hospitality row, measured, not assumed) so the variation in stem
    extension is the deck's own level, not the ground's.
    """
    out = []
    if d.frame == "two_tier":
        nx = max(2, int(round(d.W / d.ped[0])) + 1)
        ny = max(2, int(round(d.D / d.ped[1])) + 1)
        xs = np.linspace(d.x0 + 0.13, d.x1 - 0.13, nx)
        ys = np.linspace(d.y0 + 0.11, d.y1 - 0.11, ny)
    else:
        js = joist_lines(d)
        step = 1.30
        if d.axis == "y":
            ys = js
            nx = max(2, int(round(d.W / step)) + 1)
            xs = np.linspace(d.x0 + 0.12, d.x1 - 0.12, nx)
        else:
            xs = js
            ny = max(2, int(round(d.D / step)) + 1)
            ys = np.linspace(d.y0 + 0.12, d.y1 - 0.12, ny)
    for i, x in enumerate(np.atleast_1d(xs)):
        for j, y in enumerate(np.atleast_1d(ys)):
            kk = d.k * 1000.0 + i * 37 + j
            out.append(dict(x=float(x), y=float(y), i=i, j=j,
                            head=d.ped_top + rnd(-0.0015, 0.0015, kk, 3),
                            shim=chance(0.16, kk, 4),
                            slope=chance(0.10, kk, 5),
                            k=kk))
    return out


def build_pedestal(acc, d, p, lod=1.0):
    """One adjustable screw-jack pedestal: base, threaded stem, adjuster
    collar, head plate.  700 of these carry the five decks."""
    x, y = p["x"], p["y"]
    z_g = -BASE_EMBED_M
    n = 14 if lod >= 1.0 else 8
    aid = h01(p["k"], 9)
    kw = dict(hd_id=aid, hd_grime=0.35 + 0.35 * h01(p["k"], 10),
              hd_wet=0.30 + 0.25 * h01(p["k"], 11), hd_edge=0.25, hd_anod=0.0)
    # --- base plate: 200 dia, 12 thick, four radial ribs under it ------------
    sweep(acc, [(x, y, z_g), (x, y, z_g + 0.012)], circle(0.100, n),
          mat=M_MILL, smooth=True, **kw)
    for q in range(4):
        a = q * math.pi / 2 + 0.18 * aid
        c, s = math.cos(a), math.sin(a)
        obox(acc, np.array([x + c * 0.055, y + s * 0.055, z_g + 0.016]),
             np.array([c * 0.044, s * 0.044, 0.0]),
             np.array([-s * 0.006, c * 0.006, 0.0]),
             np.array([0.0, 0.0, 0.007]), mat=M_MILL, chamfer=0.002, **kw)
    if p["shim"]:
        for q in range(rint(1, 3, p["k"], 12)):
            box(acc, (x - 0.075, y - 0.075, z_g - 0.0035 * (q + 1)),
                (x + 0.075, y + 0.075, z_g - 0.0035 * q), mat=M_TRIM,
                hd_id=h01(p["k"], 13 + q), hd_grime=0.6, hd_wet=0.5, hd_edge=0.7)
    # --- threaded stem -------------------------------------------------------
    z0 = z_g + 0.012
    z1 = p["head"] - 0.028
    ext = max(z1 - z0, 0.020)
    sweep(acc, [(x, y, z0), (x, y, z0 + ext)], circle(0.0245, n),
          mat=M_MILL, smooth=True, **kw)
    turns = max(1.5, ext / 0.008)
    if lod >= 1.0 and turns < 40:
        hp = helix((x, y, z0 + 0.004), (0, 0, 1), 0.0272, turns, 0.008,
                   n_per_turn=14)
        hp = hp[hp[:, 2] <= z0 + ext - 0.002]
        if len(hp) > 3:
            thr = np.array([[0.0, 0.0030], [0.0026, 0.0], [0.0, -0.0030]])
            sweep(acc, hp, np.concatenate([thr, [[-0.0016, 0.0]]]), mat=M_MILL,
                  smooth=True, **kw)
    # --- adjuster collar: knurled ring with six tommy-bar holes --------------
    zc = z0 + ext * rnd(0.35, 0.62, p["k"], 14)
    a = np.linspace(0, 2 * np.pi, 36, endpoint=False)
    rr = 0.0385 + 0.0011 * (np.arange(36) % 2)
    knurl = np.stack([np.cos(a) * rr, np.sin(a) * rr], 1)
    sweep(acc, [(x, y, zc - 0.011), (x, y, zc + 0.011)], knurl, mat=M_MILL,
          smooth=False, **kw)
    # --- head plate + the slope corrector on the ones that need it ----------
    hz = p["head"]
    obox(acc, np.array([x, y, hz - 0.008]), np.array([0.058, 0, 0]),
         np.array([0, 0.058, 0]), np.array([0, 0, 0.008]), mat=M_MILL,
         chamfer=0.004, **kw)
    if p["slope"]:
        obox(acc, np.array([x, y, hz + 0.004]), np.array([0.052, 0, 0.0018]),
             np.array([0, 0.052, 0]), np.array([0, 0, 0.004]), mat=M_TRIM,
             chamfer=0.003, hd_id=aid, hd_grime=0.5, hd_edge=0.6)
    for sx in (-1, 1):
        for sy in (-1, 1):
            obox(acc, np.array([x + sx * 0.050, y + sy * 0.050, hz + 0.011]),
                 np.array([0.006, 0, 0]), np.array([0, 0.006, 0]),
                 np.array([0, 0, 0.011]), mat=M_MILL, chamfer=0.002, **kw)


def build_frame(acc, d, lod=1.0):
    """Bearers, joists, cleats and the plan bracing.

    `two_tier` is 100x50 aluminium bearers on the pedestals carrying 80x40
    joists at board centres; `single` is close-spaced 100x50 bearers straight
    on the pedestals with the boards screwed to them.  A modular deck really is
    built both ways and which way it is built changes what you see through the
    board gaps — which at a 7 mm gap and a 12.47 deg sun is a row of dark slots
    with an aluminium edge catching light at the bottom of some of them.
    """
    peds = pedestal_grid(d)
    kw = dict(hd_anod=0.15, hd_grime=0.42, hd_edge=0.35, hd_wet=0.25)
    if d.frame == "two_tier":
        xs = sorted(set(round(p["x"], 4) for p in peds))
        bsec = rect(d.bearer_w, d.bearer_h, chamfer=0.0035)
        bin_ = rect(d.bearer_w - 0.006, d.bearer_h - 0.006, chamfer=0.0025)
        for i, x in enumerate(xs):
            zc = d.bearer_top - d.bearer_h * 0.5
            hollow(acc, [(x, d.y0 + 0.035, zc), (x, d.y1 - 0.035, zc)],
                   bsec, bin_, mat=M_MILL, up=(0, 0, 1), hd_id=h01(d.k, 200 + i),
                   **kw)
        jsec = rect(d.joist_w, d.joist_h, chamfer=0.003)
        jin = rect(d.joist_w - 0.005, d.joist_h - 0.005, chamfer=0.002)
        js = joist_lines(d) if d.axis == "y" else joist_lines(d)
        for i, t in enumerate(js):
            zc = d.joist_top - d.joist_h * 0.5
            if d.axis == "y":
                p0, p1 = (d.x0 + 0.02, t, zc), (d.x1 - 0.02, t, zc)
            else:
                p0, p1 = (t, d.y0 + 0.02, zc), (t, d.y1 - 0.02, zc)
            hollow(acc, [p0, p1], jsec, jin, mat=M_MILL, up=(0, 0, 1),
                   hd_id=h01(d.k, 300 + i), **kw)
            # a cleat every third crossing, a screw at all of them
            for q, x in enumerate(xs):
                if d.axis == "y":
                    cx, cy = x, t
                else:
                    cx, cy = t, x
                if (i + q) % 3 == 0:
                    obox(acc, np.array([cx + 0.032, cy, d.joist_top - 0.030]),
                         np.array([0.030, 0, 0]), np.array([0, 0.0022, 0]),
                         np.array([0, 0, 0.026]), mat=M_MILL, chamfer=0.002,
                         hd_id=h01(d.k, 400 + i * 31 + q), **kw)
                    for sz in (-0.014, 0.012):
                        tube(acc, (cx + 0.058, cy - 0.004,
                                   d.joist_top - 0.030 + sz),
                             (cx + 0.058, cy + 0.006,
                              d.joist_top - 0.030 + sz), 0.0035, mat=M_STEEL,
                             n=8, hd_id=0.4, hd_edge=0.7, hd_grime=0.5)
    else:
        js = joist_lines(d)
        bsec = rect(d.joist_w, d.joist_h, chamfer=0.0035)
        bin_ = rect(d.joist_w - 0.006, d.joist_h - 0.006, chamfer=0.0025)
        for i, t in enumerate(js):
            zc = d.joist_top - d.joist_h * 0.5
            if d.axis == "y":
                p0, p1 = (d.x0 + 0.02, t, zc), (d.x1 - 0.02, t, zc)
            else:
                p0, p1 = (t, d.y0 + 0.02, zc), (t, d.y1 - 0.02, zc)
            hollow(acc, [p0, p1], bsec, bin_, mat=M_MILL, up=(0, 0, 1),
                   hd_id=h01(d.k, 300 + i), **kw)
    # --- perimeter edge beam: what the trim screws to ------------------------
    esec = rect(0.045, d.joist_h + d.bt, chamfer=0.003)
    ein = rect(0.039, d.joist_h + d.bt - 0.006, chamfer=0.002)
    zc = d.H - (d.joist_h + d.bt) * 0.5
    for (p0, p1) in (((d.x0 + 0.0225, d.y0 + 0.0225, zc), (d.x1 - 0.0225, d.y0 + 0.0225, zc)),
                     ((d.x0 + 0.0225, d.y1 - 0.0225, zc), (d.x1 - 0.0225, d.y1 - 0.0225, zc)),
                     ((d.x0 + 0.0225, d.y0 + 0.0225, zc), (d.x0 + 0.0225, d.y1 - 0.0225, zc)),
                     ((d.x1 - 0.0225, d.y0 + 0.0225, zc), (d.x1 - 0.0225, d.y1 - 0.0225, zc))):
        hollow(acc, [p0, p1], esec, ein, mat=M_MILL, up=(0, 0, 1),
               hd_id=h01(d.k, 500 + p0[0] + p1[1]), **kw)
    # --- plan bracing: flat straps in two bays, with the tensioner ----------
    for q in range(2):
        kk = d.k * 3.0 + q
        bx = rnd(d.x0 + 1.2, d.x1 - 1.2, kk, 7)
        z = d.ped_top - 0.010
        p0 = (bx - 0.9, d.y0 + 0.30, z)
        p1 = (bx + 0.9, d.y1 - 0.30, z - 0.004)
        sweep(acc, [p0, p1], rect(0.030, 0.004), mat=M_STEEL, up=(0, 0, 1),
              hd_id=h01(kk, 8), hd_grime=0.55, hd_edge=0.5, hd_wet=0.35)
        hexnut(acc, np.array([(p0[0] + p1[0]) * 0.5, (p0[1] + p1[1]) * 0.5, z + 0.002]),
               (0, 0, 1), 0.011, 0.016, mat=M_STEEL, hd_id=h01(kk, 9),
               hd_grime=0.5, hd_edge=0.7)


def build_services(acc, d, lod=1.0):
    """The cable tray, the bundles on it, and the brush grommet they come up
    through.  Visible through the gaps and, on the open-skirted deck, straight
    through the front."""
    z = d.ped_top - 0.055
    y = d.y1 - 0.55
    # perforated tray: a channel with a run of slots punched in the base
    sweep(acc, [(d.x0 + 0.3, y, z), (d.x1 - 0.3, y, z)],
          np.array([[-0.075, -0.020], [0.075, -0.020], [0.075, 0.028],
                    [0.062, 0.028], [0.062, -0.008], [-0.062, -0.008],
                    [-0.062, 0.028], [-0.075, 0.028]]),
          mat=M_MILL, up=(0, 0, 1), hd_id=h01(d.k, 601), hd_anod=0.1,
          hd_grime=0.5, hd_edge=0.4, hd_wet=0.3)
    for q in range(int((d.W - 0.9) / 0.14)):
        cx = d.x0 + 0.45 + q * 0.14
        box(acc, (cx - 0.030, y - 0.040, z - 0.0215),
            (cx + 0.030, y + 0.040, z - 0.0185), mat=M_MILL,
            hd_id=h01(d.k, 610 + q), hd_grime=0.55, hd_edge=0.6)
    # cable bundles, sagging between the tray's supports
    for q in range(rint(3, 5, d.k, 12)):
        kk = d.k * 5.0 + q
        r = rnd(0.006, 0.014, kk, 1)
        yy = y + rnd(-0.045, 0.045, kk, 2)
        n = 22
        t = np.linspace(0.0, 1.0, n)
        xs = d.x0 + 0.35 + t * (d.W - 0.7)
        zs = (z + 0.012 + r
              + 0.010 * np.sin(t * np.pi * rnd(3.0, 6.0, kk, 3))
              * np.sin(t * np.pi))
        sweep(acc, np.stack([xs, np.full(n, yy), zs], 1), circle(r, 8),
              mat=M_CABLE, smooth=True, hd_id=h01(kk, 4), hd_grime=0.6,
              hd_edge=0.2, hd_wet=0.3)
    # the brush grommet plate in the deck, and the cables through it
    for q in range(2):
        gx = d.x0 + d.W * (0.28 + 0.44 * q)
        gy = d.y1 - 0.36
        obox(acc, np.array([gx, gy, d.H + 0.0035]), np.array([0.090, 0, 0]),
             np.array([0, 0.055, 0]), np.array([0, 0, 0.0035]), mat=M_MILL,
             chamfer=0.0025, hd_id=h01(d.k, 700 + q), hd_anod=0.2,
             hd_grime=0.4, hd_edge=0.7)
        for j in range(rint(2, 4, d.k, 701 + q)):
            kk = d.k * 9.0 + q * 10 + j
            r = rnd(0.005, 0.011, kk, 1)
            x0 = gx + rnd(-0.055, 0.055, kk, 2)
            n = 14
            t = np.linspace(0, 1, n)
            px = x0 + rnd(-0.25, 0.25, kk, 3) * t
            py = gy + 0.02 + t * rnd(0.10, 0.26, kk, 4)
            pz = d.H + 0.007 + 0.055 * np.sin(t * np.pi * 0.9) - 0.02 * t
            sweep(acc, np.stack([px, py, pz], 1), circle(r, 8), mat=M_CABLE,
                  smooth=True, hd_id=h01(kk, 5), hd_grime=0.5, hd_edge=0.2)


# ================================================================================
#  8.  THE EDGE — five different trims, because the manifest says so
# ================================================================================

def _edge_runs(d, front_only=False):
    """The perimeter as (p0, p1, outward-normal) in local XY, front first."""
    r = [((d.x0, d.y0), (d.x1, d.y0), (0.0, -1.0)),
         ((d.x0, d.y0), (d.x0, d.y1), (-1.0, 0.0)),
         ((d.x1, d.y0), (d.x1, d.y1), (1.0, 0.0))]
    return r[:1] if front_only else r


def build_trim(acc, d, lod=1.0):
    """The perimeter trim.  Five sections, five different meshes.

    The front face is in full sun at 12.47 deg, so every one of these throws a
    hard horizontal shadow band down the fascia — a 40 mm angle leg throws
    181 mm, a 26 mm PVC bullnose throws 118 mm, a 14 mm shadow-gap channel
    throws 63 mm.  That band is 10-31 px tall and it is the single strongest
    read the deck edge has.  It only exists if the trim is a solid.
    """
    proj, drop, kind = TRIM_SECTION[d.trim]
    anod = {"alu_angle": 0.05, "alu_channel": 0.55}.get(d.trim, 0.0)
    for (a, b, nrm) in _edge_runs(d):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        nseg = max(2, int(L / 0.35))
        t = np.linspace(0.0, 1.0, nseg)
        px = a[0] + (b[0] - a[0]) * t
        py = a[1] + (b[1] - a[1]) * t
        kk = d.k * 7.0 + nrm[0] * 3.0 + nrm[1]
        # every trim is fixed in lengths with a joint, and the joints move
        joints = np.sort(np.array([rnd(0.15, 0.85, kk, 20 + q)
                                   for q in range(max(1, int(L / 3.2)))]))
        if kind == "angle":
            SEC = np.array([[0.0, 0.0], [proj, 0.0], [proj, -0.003],
                            [0.003, -0.003], [0.003, -drop],
                            [0.0, -drop]])
            mat, sm = M_ANOD, False
        elif kind == "fascia":
            SEC = np.array([[0.0, 0.010], [0.010, 0.014], [0.019, 0.010],
                            [proj, 0.0], [proj, -drop + 0.010],
                            [proj - 0.008, -drop], [0.0, -drop]])
            mat, sm = M_BOARD, False
        elif kind == "drip":
            SEC = np.array([[0.0, 0.0], [proj, 0.0], [proj, -0.0015],
                            [0.0015, -0.0015], [0.0015, -drop + 0.012],
                            [0.012, -drop + 0.004], [0.0135, -drop],
                            [0.0, -drop - 0.0015]])
            mat, sm = M_STEEL, False
        elif kind == "bullnose":
            a2 = np.linspace(-np.pi * 0.5, np.pi * 0.5, 9)
            nose = np.stack([0.013 + np.cos(a2) * 0.013,
                             -0.013 + np.sin(a2) * 0.013], 1)[::-1]
            SEC = np.concatenate([[[0.0, 0.0]], [[0.013, 0.0]], nose,
                                  [[0.010, -0.030], [0.010, -drop],
                                   [0.0, -drop]]])
            mat, sm = M_TRIM, True
        else:                                     # shadow-gap channel
            SEC = np.array([[0.0, -0.018], [proj, -0.018], [proj, -drop],
                            [proj - 0.004, -drop], [proj - 0.004, -0.026],
                            [0.0, -0.026]])
            mat, sm = M_ANOD, False
        # orient the section: +u outward along nrm, +v up
        ang = math.atan2(nrm[1], nrm[0])
        for q in range(len(joints) + 1):
            t0 = 0.0 if q == 0 else float(joints[q - 1])
            t1 = 1.0 if q == len(joints) else float(joints[q])
            if t1 - t0 < 0.01:
                continue
            g = 0.0018 + 0.0026 * h01(kk, 40 + q)      # the joint gap
            tt = np.linspace(t0 + (g / L if q else 0.0), t1 - g / L,
                             max(2, int((t1 - t0) * nseg)))
            X = a[0] + (b[0] - a[0]) * tt
            Y = a[1] + (b[1] - a[1]) * tt
            # oil-canning: 1.5 mm stainless between rivets never stays flat
            wob = (0.0016 * np.sin(tt * L * 8.0 + h01(kk, 50 + q) * 6.0)
                   if kind == "drip" else 0.0)
            Z = np.full(len(tt), d.H) + (wob if np.ndim(wob) else 0.0)
            Pth = np.stack([X + nrm[0] * (wob if np.ndim(wob) else 0.0),
                            Y + nrm[1] * (wob if np.ndim(wob) else 0.0), Z], 1)
            # a couple of sections are knocked in, one is lifted
            lift = 0.0035 if chance(0.10, kk, 60 + q) else 0.0
            Pth[:, 2] += lift * np.sin(np.linspace(0, np.pi, len(tt)))
            S2 = np.stack([SEC[:, 0] * math.cos(ang) - 0.0,
                           SEC[:, 0] * math.sin(ang)], 1)
            V = (Pth[:, None, :]
                 + np.stack([S2[:, 0], S2[:, 1], SEC[:, 1]], 1)[None, :, :])
            Vf = V.reshape(-1, 3)
            n, m = len(Pth), len(SEC)
            Q = _grid_quads(n, m, close_m=True)
            c0, c1 = Vf[:m].mean(0), Vf[(n - 1) * m:].mean(0)
            Vf = np.concatenate([Vf, c0[None, :], c1[None, :]])
            Tr = np.concatenate([_fan(n * m, np.arange(m), reverse=True),
                                 _fan(n * m + 1, (n - 1) * m + np.arange(m))])
            bcv = np.concatenate([
                np.stack([np.repeat(tt * L, m),
                          np.tile(SEC[:, 0], n), np.tile(SEC[:, 1], n)], 1),
                np.zeros((2, 3))])
            acc.solid(Vf, quads=Q, tris=Tr, mat=mat, bc=bcv, smooth=sm,
                      hd_anod=anod, hd_id=h01(kk, 70 + q),
                      hd_age=d.age * (0.8 if mat == M_BOARD else 0.3),
                      hd_grime=0.30 + 0.30 * h01(kk, 80 + q),
                      hd_edge=0.55, hd_wet=d.wet * 0.8,
                      tint=np.array(P["anod_bronze"]) / 0.087
                      if d.trim == "alu_angle" else None)
            # fixings: countersunk screws, or pop rivets on the stainless
            nf = max(2, int((t1 - t0) * L / (0.25 if kind == "drip" else 0.40)))
            for f in range(nf):
                ft = t0 + (t1 - t0) * (f + 0.5) / nf
                fx = a[0] + (b[0] - a[0]) * ft + nrm[0] * proj * 0.45
                fy = a[1] + (b[1] - a[1]) * ft + nrm[1] * proj * 0.45
                if kind == "drip":
                    tube(acc, (fx, fy, d.H - drop * 0.45),
                         (fx + nrm[0] * 0.0018, fy + nrm[1] * 0.0018,
                          d.H - drop * 0.45), 0.0022, mat=M_STEEL, n=8,
                         hd_id=h01(kk, 90 + f), hd_grime=0.5, hd_edge=0.8)
                else:
                    zz = d.H + (0.008 if kind == "fascia" else -0.0015)
                    sweep(acc, [(fx, fy, zz), (fx, fy, zz - 0.0022)],
                          circle(1.0, 10), scale=np.array([[0.0042, 0.0042],
                                                           [0.0029, 0.0029]]),
                          mat=M_STEEL, smooth=True, hd_id=h01(kk, 90 + f),
                          hd_grime=0.45, hd_edge=0.8)


# ================================================================================
#  9.  THE SKIRT — what closes (or does not close) the 0.6 m void
# ================================================================================

def build_skirt(acc, d, lod=1.0):
    """Five treatments.  One of them is deliberately NOTHING.

    `open` is not a saving: it is the deck where the sun goes under and you see
    the pedestals, the tray and the cables in silhouette, which is the shot that
    proves the other four are hiding something real.
    """
    if d.skirt == "open":
        return
    top = d.H - TRIM_SECTION[d.trim][1] - 0.004
    bot = -BASE_EMBED_M
    kw = dict(hd_edge=0.30, hd_wet=d.wet * 0.9)
    for (a, b, nrm) in _edge_runs(d):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        kk = d.k * 11.0 + nrm[0] * 5.0 + nrm[1] * 2.0
        # skip the panel run where the steps come down
        blocked = []
        for (sx, sw, nr, wr) in d.steps:
            if abs(nrm[1] + 1.0) < 1e-6:
                blocked.append((sx - sw * 0.5 - 0.10, sx + sw * 0.5 + 0.10))
        pw = rnd(1.05, 1.35, kk, 3)
        npan = max(1, int(round(L / pw)))
        pw = L / npan
        # top and bottom rails run the whole way
        for zz, hh in ((top - 0.024, 0.024), (bot + 0.030, 0.030)):
            sweep(acc, [(a[0] + nrm[0] * 0.008, a[1] + nrm[1] * 0.008, zz - hh * 0.5),
                        (b[0] + nrm[0] * 0.008, b[1] + nrm[1] * 0.008, zz - hh * 0.5)],
                  rect(0.030, hh, chamfer=0.002), mat=M_MILL, up=(0, 0, 1),
                  hd_id=h01(kk, 4), hd_anod=0.2, hd_grime=0.45, **kw)
        for q in range(npan):
            t0 = q * pw
            t1 = t0 + pw
            cxa = a[0] + (b[0] - a[0]) * (t0 / L)
            cya = a[1] + (b[1] - a[1]) * (t0 / L)
            cxb = a[0] + (b[0] - a[0]) * (t1 / L)
            cyb = a[1] + (b[1] - a[1]) * (t1 / L)
            mid = ((cxa + cxb) * 0.5, (cya + cyb) * 0.5)
            if any(lo <= mid[0] <= hi for (lo, hi) in blocked):
                continue
            gone = chance(0.055, kk, 100 + q)
            if gone:
                continue
            j = 0.004                      # the joint gap between panels
            ux = (cxb - cxa) / max(pw, 1e-9)
            uy = (cyb - cya) / max(pw, 1e-9)
            ex = np.array([ux, uy, 0.0]) * (pw * 0.5 - j)
            ey = np.array([nrm[0], nrm[1], 0.0])
            pz = (top + bot) * 0.5
            hz = (top - bot) * 0.5
            if d.skirt == "half":
                pz = top - (top - bot) * 0.25
                hz = (top - bot) * 0.25
            tid = h01(kk, 120 + q)
            if d.skirt == "louvre":
                # a real louvred vent: six angled blades in a frame
                fr = np.array([mid[0] + nrm[0] * 0.012, mid[1] + nrm[1] * 0.012, pz])
                for side in (-1, 1):
                    obox(acc, fr + np.array([ux, uy, 0.0]) * side * (pw * 0.5 - j - 0.014),
                         ex / max(np.linalg.norm(ex), 1e-9) * 0.014,
                         ey * 0.006, np.array([0, 0, hz]), mat=M_ANOD,
                         chamfer=0.002, hd_anod=0.45, hd_id=tid, hd_grime=0.4, **kw)
                nbl = max(4, int(hz * 2 / 0.075))
                for bl in range(nbl):
                    bz = pz - hz + (bl + 0.5) * (hz * 2 / nbl)
                    ctr = np.array([mid[0] + nrm[0] * 0.010,
                                    mid[1] + nrm[1] * 0.010, bz])
                    # HALF the clear width between the two side rails, not
                    # `ex` doubled: a blade as long as the whole panel runs a
                    # full panel-width into its neighbours, and 11 panels of
                    # overlapping blades read as one continuous louvre band
                    # with the panel joints buried inside solid aluminium.
                    obox(acc, ctr, ex - ex / max(np.linalg.norm(ex), 1e-9) * 0.018,
                         ey * 0.016 + np.array([0, 0, -0.014]),
                         np.array([0, 0, 0.0022]), mat=M_ANOD, chamfer=0.0015,
                         hd_anod=0.45, hd_id=tid + bl * 0.01, hd_grime=0.45, **kw)
                continue
            # flat panel: composite, painted ply or half-height
            th = 0.009 if d.skirt == "composite" else 0.013
            mat = (M_COMP if d.skirt == "composite" else
                   M_PAINT if d.skirt == "painted_ply" else M_ANOD)
            tint = None
            if d.skirt == "painted_ply":
                tint = brand_paint(d.brand)
            bow = 0.0035 * (h01(kk, 140 + q) - 0.5)
            ctr = np.array([mid[0] + nrm[0] * (0.010 + bow),
                            mid[1] + nrm[1] * (0.010 + bow), pz])
            obox(acc, ctr, ex, ey * th, np.array([0, 0, hz]), mat=mat,
                 chamfer=0.0018, tint=tint,
                 hd_paint=1.0 if d.skirt == "painted_ply" else 0.0,
                 hd_anod=0.35 if mat == M_ANOD else 0.0,
                 hd_id=tid, hd_grime=0.28 + 0.34 * tid, **kw)
            # brand band + an extruded geometric mark, no lettering
            if d.skirt == "painted_ply" and q % 2 == 0:
                band = np.array([mid[0] + nrm[0] * (0.010 + bow + th),
                                 mid[1] + nrm[1] * (0.010 + bow + th),
                                 pz + hz * 0.30])
                # 0.86 linear is brighter than any paint outdoors — TiO2 white
                # tops out near 0.75 new, and a season on a paddock takes it to
                # 0.55.  At 0.86 the band read as a lit sticker stuck on the
                # panel rather than as paint that is part of it.
                obox(acc, band, ex * 0.94, ey * 0.0022,
                     np.array([0, 0, hz * 0.16]), mat=M_PAINT, chamfer=0.001,
                     tint=np.array((0.362, 0.358, 0.340)), hd_paint=1.0,
                     hd_id=tid, hd_grime=0.42, **kw)
                mk = np.array([mid[0] + nrm[0] * (0.010 + bow + th),
                               mid[1] + nrm[1] * (0.010 + bow + th),
                               pz - hz * 0.18])
                for s3 in range(3):
                    obox(acc, mk + np.array([ux, uy, 0.0]) * (s3 - 1) * 0.052,
                         np.array([ux, uy, 0.0]) * 0.018, ey * 0.0025,
                         np.array([0, 0, 0.052 - abs(s3 - 1) * 0.016]),
                         mat=M_PAINT, chamfer=0.001,
                         tint=np.array((0.362, 0.358, 0.340)), hd_paint=1.0,
                         hd_id=tid + 0.11 * s3, hd_grime=0.34, **kw)
            # fixings
            nf = max(2, int(hz * 2 / 0.30))
            for f in range(nf):
                fz = pz - hz + (f + 0.5) * (hz * 2 / nf)
                for sgn in (-1, 1):
                    fx = mid[0] + ux * sgn * (pw * 0.5 - 0.030) + nrm[0] * (0.010 + th + bow)
                    fy = mid[1] + uy * sgn * (pw * 0.5 - 0.030) + nrm[1] * (0.010 + th + bow)
                    sweep(acc, [(fx, fy, fz),
                                (fx - nrm[0] * 0.0022, fy - nrm[1] * 0.0022, fz)],
                          circle(1.0, 8), scale=np.array([[0.0040, 0.0040],
                                                          [0.0026, 0.0026]]),
                          mat=M_STEEL, smooth=True, up=(0, 0, 1),
                          hd_id=h01(kk, 160 + q * 7 + f), hd_grime=0.5,
                          hd_edge=0.8, hd_wet=d.wet * 0.9)
        # --- THE STEP OPENING IS RETURNED, NOT LEFT AS A HOLE ---------------
        # Interrupting the skirt for a step run left a 2.8 x 0.6 m rectangle of
        # unlit void in the fascia — 480 x 100 px of pure black at the filmed
        # distance, sitting directly beside the brightest part of the item.  On
        # a built deck the skirt turns the corner and runs back to the first
        # joist, and the head of the opening is closed by a header, so what you
        # actually see under the deck is a shallow lit recess.  This is that.
        rpz, rhz = (top + bot) * 0.5, (top - bot) * 0.5
        if d.skirt == "half":
            rpz, rhz = top - (top - bot) * 0.25, (top - bot) * 0.25
        for (lo, hi) in blocked:
            for (rx, sgn) in ((lo, -1.0), (hi, +1.0)):
                rd = 0.34                       # how far the return runs back
                rc = np.array([rx, d.y0 + rd * 0.5 + 0.010, rpz])
                obox(acc, rc, np.array([0.010, 0, 0]),
                     np.array([0, rd * 0.5, 0]),
                     np.array([0, 0, rhz]),
                     mat=(M_COMP if d.skirt == "composite" else
                          M_PAINT if d.skirt == "painted_ply" else M_ANOD),
                     chamfer=0.0018,
                     tint=(brand_paint(d.brand)
                           if d.skirt == "painted_ply" else None),
                     hd_paint=1.0 if d.skirt == "painted_ply" else 0.0,
                     hd_anod=0.35 if d.skirt not in ("composite",
                                                     "painted_ply") else 0.0,
                     hd_id=h01(kk, 200 + int(sgn)), hd_grime=0.52,
                     hd_edge=0.35, hd_wet=d.wet)
            # the header over the opening: the fascia rail carries across
            obox(acc, np.array([(lo + hi) * 0.5, d.y0 + 0.030, top - 0.055]),
                 np.array([(hi - lo) * 0.5, 0, 0]), np.array([0, 0.030, 0]),
                 np.array([0, 0, 0.055]), mat=M_MILL, chamfer=0.002,
                 hd_id=h01(kk, 205), hd_anod=0.2, hd_grime=0.5,
                 hd_edge=0.4, hd_wet=d.wet)
            # ...and a SOFFIT behind it.  The returns close the sides of the
            # opening but you still look straight up into the under-deck from
            # in front of the stair, and at a 12.47 deg sun that is unlit: a
            # 2.8 x 0.35 m rectangle of pure black beside the brightest part of
            # the item.  A soffit tray is what is really there — the closure the
            # erector fits so the void is not open to the weather.
            obox(acc, np.array([(lo + hi) * 0.5, d.y0 + 0.190, top - 0.010]),
                 np.array([(hi - lo) * 0.5, 0, 0]), np.array([0, 0.190, 0]),
                 np.array([0, 0, 0.006]), mat=M_MILL, chamfer=0.002,
                 hd_id=h01(kk, 206), hd_anod=0.2, hd_grime=0.62,
                 hd_wear=0.05, hd_edge=0.3, hd_wet=d.wet)
    # a removed panel leaning against the deck, on the composite skirt
    if d.skirt == "composite":
        kk = d.k * 13.0
        lx = rnd(d.x0 + 1.5, d.x1 - 1.5, kk, 1)
        lean = math.radians(rnd(9.0, 16.0, kk, 2))
        h = (d.H - TRIM_SECTION[d.trim][1] - 0.004) + BASE_EMBED_M - 0.06
        ctr = np.array([lx, d.y0 - 0.10 - math.sin(lean) * h * 0.5,
                        -BASE_EMBED_M + math.cos(lean) * h * 0.5])
        obox(acc, ctr, np.array([rnd(0.48, 0.60, kk, 3), 0, 0]),
             np.array([0, math.cos(lean) * 0.0045, math.sin(lean) * 0.0045]),
             np.array([0, -math.sin(lean) * h * 0.5, math.cos(lean) * h * 0.5]),
             mat=M_COMP, chamfer=0.002, hd_id=h01(kk, 4), hd_grime=0.55,
             hd_edge=0.4, hd_wet=0.45)


# ================================================================================
# 10.  THE STEPS — and the nosing wear the manifest names as an axis
# ================================================================================

def step_runs(d):
    """Every step run on this deck.  Public: `motorhome_unit` and anything that
    places on the apron needs to know where the traffic lands."""
    out = []
    for (sx, sw, nr, wear) in d.steps:
        rise = d.H / nr
        out.append(dict(x=float(sx), width=float(sw), risers=int(nr),
                        rise=float(rise), going=0.300,
                        y_nose=float(d.y0),
                        y_foot=float(d.y0 - 0.300 * nr),
                        wear=float(wear), apron_z=0.0,
                        nosing="alu_carborundum"))
    return out


def _grit_strip(acc, d, ctr, ex, ey, wear, kid):
    """A carborundum anti-slip insert as REAL PARTICLES.

    This is the manifest's second variation axis and it is the one that is
    easiest to fake and hardest to fake convincingly.  A 1.2 mm grit particle is
    0.20 px, so no single particle is resolvable — but 4,000 of them across a
    2.8 m nosing are, as a texture whose specular breaks up, and the WORN zone
    is resolvable because the particles are GONE there and the strip is 0.6 mm
    lower with a polished aluminium arris beside it.

    So: a displaced lattice at 3 mm cells, amplitude driven by a voronoi-ish
    hash, scaled down by local wear.  A new nosing (wear 0.15) keeps 0.9 mm of
    relief across its whole length; a dead one (wear 0.90) is flat in the middle
    two thirds with the binder resin polished and only the outer 150 mm still
    gritty, which is exactly how they wear.
    """
    ctr = np.asarray(ctr, float)
    ex = np.asarray(ex, float)
    ey = np.asarray(ey, float)
    Lu = float(np.linalg.norm(ex)) * 2.0
    Lv = float(np.linalg.norm(ey)) * 2.0
    nu = max(4, int(Lu / 0.0030))
    nv = max(3, int(Lv / 0.0030))
    u = np.linspace(-1.0, 1.0, nu)
    v = np.linspace(-1.0, 1.0, nv)
    U, V2 = np.meshgrid(u, v, indexing="ij")
    # wear is worst in the middle of the run and along the front third
    centre = np.clip(1.0 - (np.abs(U) / 0.72) ** 3, 0.0, 1.0)
    lw = np.clip(wear * centre * (0.55 + 0.45 * (1.0 - np.abs(V2))), 0.0, 1.0)
    g = _hn2((U * Lu * 0.5 / 0.0030).astype(np.int64),
             (V2 * Lv * 0.5 / 0.0030).astype(np.int64), int(kid * 977) + 17)
    g2 = _hn2((U * Lu * 0.5 / 0.0016).astype(np.int64),
              (V2 * Lv * 0.5 / 0.0016).astype(np.int64), int(kid * 977) + 41)
    amp = 0.00090 * (1.0 - 0.94 * lw)
    Zg = amp * (0.55 * g + 0.45 * g2 * g2) - 0.00060 * lw
    P0 = (ctr[None, None, :] + U[:, :, None] * ex[None, None, :]
          + V2[:, :, None] * ey[None, None, :])
    up = np.cross(ex, ey)
    up = up / (np.linalg.norm(up) + 1e-15)
    Vt = P0 + Zg[:, :, None] * up[None, None, :]
    Vb = P0 - 0.0016 * up[None, None, :]
    n = nu * nv
    Vall = np.concatenate([Vt.reshape(-1, 3), Vb.reshape(-1, 3)])
    idx = np.arange(n).reshape(nu, nv)
    Qt = np.stack([idx[:-1, :-1].ravel(), idx[1:, :-1].ravel(),
                   idx[1:, 1:].ravel(), idx[:-1, 1:].ravel()], 1)
    Qb = (Qt + n)[:, ::-1].copy()
    sides = []
    for (l0, l1) in ((idx[0, :], None), (idx[-1, :], None)):
        sides.append(np.stack([l0[:-1], l0[1:], l0[1:] + n, l0[:-1] + n], 1))
    for l0 in (idx[:, 0], idx[:, -1]):
        sides.append(np.stack([l0[:-1], l0[1:], l0[1:] + n, l0[:-1] + n], 1))
    Q = np.concatenate([Qt, Qb] + sides)
    acc.solid(Vall, quads=Q, mat=M_GRIT, hd_wear=float(np.mean(lw)),
              hd_id=kid, hd_grime=0.35 + 0.4 * float(np.mean(lw)),
              hd_edge=0.2, hd_wet=d.wet * 0.7)


def _extrude_x(acc, x0, x1, SEC, mat, **kw):
    """Extrude a closed (y, z) section between two x stations, with end caps."""
    SEC = np.asarray(SEC, float)
    mm = len(SEC)
    Pth = np.array([[x0, 0.0, 0.0], [x1, 0.0, 0.0]])
    V = (Pth[:, None, :]
         + np.stack([np.zeros(mm), SEC[:, 0], SEC[:, 1]], 1)[None, :, :])
    Vf = V.reshape(-1, 3)
    Q = _grid_quads(2, mm, close_m=True)
    Vf = np.concatenate([Vf, Vf[:mm].mean(0)[None, :],
                         Vf[mm:2 * mm].mean(0)[None, :]])
    Tr = np.concatenate([_fan(2 * mm, np.arange(mm), reverse=True),
                         _fan(2 * mm + 1, mm + np.arange(mm))])
    return acc.solid(Vf, quads=Q, tris=Tr, mat=mat, **kw)


def build_steps(acc, d, lod=1.0):
    """One or two step runs off the front edge, as a FABRICATION.

    WHAT THIS REPLACES, AND WHY.  The first version was dimensionally right and
    physically impossible: stringers that were 8 mm flat plate, treads that were
    5 mm flat plate, risers that were 3.6 mm flat plate, and nothing joining any
    of them.  At the inspection distance it read as a paper model — the light
    passed under every tread, no member had a section, and there was not one
    fixing in the whole run.  A stair is the most legible piece of fabrication
    on a deck: people know what one is made of.

    So this is how a modular aluminium stair is actually made:

      * STRINGERS are folded 3 mm CHANNEL, 200 mm web with 45 mm flanges,
        swept along the nosing line.  A channel has a section; a plate does not,
        and the difference at a 12.47 deg sun is a 45 mm flange throwing 204 mm
        of shadow down the web.
      * TREADS are folded PANS, not plates: 2.5 mm sheet with the front edge
        turned down 25 mm, the back edge turned down 40 mm and returned 22 mm,
        and side skirts that bolt to the stringer webs.  The turned edges are
        what you see from below and from in front, and they are why a tread
        reads as a tread rather than as a floating line.
      * The pan is BOLTED: two M8 button heads per tread per stringer, proud on
        the outside of the web where the eye finds them.
      * The head hangs off a 6 mm bracket bolted to the deck's rim; the foot
        stands on a 140 x 90 x 8 base plate with two anchors and a shim stack,
        because a stair that meets the ground in a point is a drawing.
    """
    # THE STAIR'S FINISH IS SPECIFIED WITH THE EDGE TRIM, not left as bare
    # mill.  Mill aluminium is metallic=1 and a tread pan lies flat under the
    # whole sky dome: on the deck whose trim is PVC the stair came back as the
    # brightest object in the macro frame, brighter than the concrete and
    # brighter than the unit wall behind it.  Decks specified with aluminium
    # trim get an aluminium stair; decks specified with PVC, timber or
    # stainless trim get the powder-coated one, which is both what a specifier
    # would do and two more finishes across the family of five.
    painted = d.trim in ("pvc_bullnose", "timber_fascia", "stainless_drip")
    M_STAIR = M_PAINT if painted else M_MILL
    stair_kw = (dict(tint=np.array((0.0475, 0.0483, 0.0502)), hd_paint=1.0)
                if painted else dict(hd_anod=0.15))
    for si, run in enumerate(step_runs(d)):
        sx, sw, nr = run["x"], run["width"], run["risers"]
        rise, going, wear = run["rise"], run["going"], run["wear"]
        kk = d.k * 17.0 + si
        # --- stringers: folded channel each side plus one in the middle ------
        nstr = 2 if sw < 2.4 else 3
        WEB, FLG, PLT = 0.200, 0.045, 0.003
        # the nosing line, and the frame the channel section is swept in
        p_top = np.array([0.0, d.y0, d.H])
        p_bot = np.array([0.0, d.y0 - going * nr, d.H - rise * nr])
        tang = p_bot - p_top
        tang /= np.linalg.norm(tang)
        nrm = np.array([0.0, -tang[2], tang[1]])       # up-slope normal, +z-ish
        if nrm[2] < 0:
            nrm = -nrm
        for q in range(nstr):
            xo = sx + (-0.5 + q / (nstr - 1)) * (sw - 0.10)
            inw = 1.0 if q == 0 else (-1.0 if q == nstr - 1 else 1.0)
            # channel section in (across, up-normal), the opening facing inboard
            u0, u1 = 0.0, inw * FLG
            v0, v1 = -0.010, -0.010 - WEB
            SEC = np.array([
                [u0, v0], [u1, v0], [u1, v0 - PLT], [u0 + inw * PLT, v0 - PLT],
                [u0 + inw * PLT, v1 + PLT], [u1, v1 + PLT], [u1, v1], [u0, v1]])
            P = np.stack([p_top, p_bot]) + np.array([xo, 0.0, 0.0])
            mm = len(SEC)
            V = (P[:, None, :]
                 + SEC[None, :, 0:1] * np.array([1.0, 0.0, 0.0])[None, None, :]
                 + SEC[None, :, 1:2] * nrm[None, None, :])
            Vf = V.reshape(-1, 3)
            Q = _grid_quads(2, mm, close_m=True)
            Vf = np.concatenate([Vf, Vf[:mm].mean(0)[None, :],
                                 Vf[mm:2 * mm].mean(0)[None, :]])
            Tr = np.concatenate([_fan(2 * mm, np.arange(mm), reverse=True),
                                 _fan(2 * mm + 1, mm + np.arange(mm))])
            # MILL ALUMINIUM IS NOT WHITE PLASTIC.  In `mat_mill` hd_wear drives
            # roughness DOWN to 0.40 and mixes towards `stainless`, so the whole
            # stair came back as the brightest object in the macro frame —
            # brighter than the concrete, brighter than the unit wall — and read
            # as a polystyrene model.  A stair standing on a paddock apron is
            # oxidised and filthy everywhere except the tread faces that shoes
            # keep bright, so the polish belongs there and nowhere else.
            acc.solid(Vf, quads=Q, tris=Tr, mat=M_STAIR, hd_id=h01(kk, 10 + q),
                      hd_grime=0.72, hd_edge=0.35, hd_wet=d.wet,
                      hd_wear=0.10, **stair_kw)
            # head bracket onto the deck rim, and its two bolts
            hb = p_top + np.array([xo, 0.0, 0.0]) + nrm * -0.055
            obox(acc, hb + np.array([0.0, 0.045, -0.030]),
                 np.array([0.006 * (1.0 if inw > 0 else -1.0), 0, 0]),
                 np.array([0, 0.055, 0]), np.array([0, 0, 0.075]),
                 mat=M_MILL, chamfer=0.002, hd_id=h01(kk, 90 + q),
                 hd_grime=0.68, hd_wear=0.08, hd_edge=0.4, hd_wet=d.wet)
            for bq in range(2):
                bx = xo + (0.008 + PLT) * (1.0 if inw > 0 else -1.0)
                sweep(acc, [(bx, hb[1] + 0.020 + bq * 0.048, hb[2] - 0.030),
                            (bx + 0.006 * (1.0 if inw > 0 else -1.0),
                             hb[1] + 0.020 + bq * 0.048, hb[2] - 0.030)],
                      circle(1.0, 10),
                      scale=np.array([[0.0075, 0.0075], [0.0060, 0.0060]]),
                      mat=M_STEEL, smooth=True, up=(0, 0, 1),
                      hd_id=h01(kk, 95 + q * 3 + bq), hd_grime=0.45,
                      hd_edge=0.6, hd_wet=d.wet)
        # --- treads: folded pans, bolted to the webs --------------------------
        for r in range(nr):
            tz = d.H - rise * (r + 1)
            ty0 = d.y0 - going * (r + 1)
            ty1 = ty0 + going
            tw = sw - 0.020
            wr = float(np.clip(wear * (1.0 - 0.18 * r), 0.0, 1.0))
            # the folded pan, extruded across the run: front edge turned down
            # 25 mm, back edge turned down 40 mm and returned 22 mm
            t_ = 0.0025
            PAN = np.array([
                [ty0,          tz],
                [ty1,          tz],
                [ty1,          tz - 0.040],
                [ty1 - 0.022,  tz - 0.040],
                [ty1 - 0.022,  tz - 0.040 + t_],
                [ty1 - t_,     tz - 0.040 + t_],
                [ty1 - t_,     tz - t_],
                [ty0 + t_,     tz - t_],
                [ty0 + t_,     tz - 0.025],
                [ty0,          tz - 0.025]])
            _extrude_x(acc, sx - tw * 0.5, sx + tw * 0.5, PAN, M_STAIR,
                       hd_id=h01(kk, 20 + r), hd_wear=wr * 0.45,
                       hd_grime=0.66, hd_edge=0.3, hd_wet=d.wet, **stair_kw)
            # side skirts: the 30 mm turned-down edges that bolt to the webs
            for sgn in (-1.0, 1.0):
                obox(acc, np.array([sx + sgn * (tw * 0.5 - t_ * 0.5),
                                    (ty0 + ty1) * 0.5, tz - 0.017]),
                     np.array([t_ * 0.5, 0, 0]),
                     np.array([0, going * 0.5 - 0.004, 0]),
                     np.array([0, 0, 0.015]), mat=M_STAIR, chamfer=0.001,
                     hd_id=h01(kk, 25 + r), hd_wear=wr * 0.18, hd_grime=0.70,
                     hd_edge=0.4, hd_wet=d.wet, **stair_kw)
            # two M8 button heads per stringer, proud on the OUTSIDE of the web
            for q in range(nstr):
                xo = sx + (-0.5 + q / (nstr - 1)) * (sw - 0.10)
                out = -1.0 if q == 0 else (1.0 if q == nstr - 1 else 1.0)
                for bq in range(2):
                    by = ty0 + 0.075 + bq * 0.130
                    bz = tz - 0.026
                    sweep(acc, [(xo + out * 0.0015, by, bz),
                                (xo + out * 0.0075, by, bz)], circle(1.0, 10),
                          scale=np.array([[0.0072, 0.0072], [0.0056, 0.0056]]),
                          mat=M_STEEL, smooth=True, up=(0, 0, 1),
                          hd_id=h01(kk, 200 + r * 7 + q * 2 + bq),
                          hd_grime=0.5, hd_edge=0.7, hd_wet=d.wet)
            # --- THE NOSING GOES ON THE OUTER EDGE ---------------------------
            # It was on `ty1`, the edge AGAINST THE DECK, and the two grit
            # strips with it — so the anti-slip was buried under the riser of
            # the step above and the leading edge people actually tread on was
            # a bare 2.5 mm fold.  The manifest names nosing wear as one of this
            # item's three variation axes; the axis was being applied to the
            # wrong edge of every tread on all five decks.  `ty0` is the nose.
            ny = ty0
            # L-section, u measured INBOARD from the nose, v down from the top:
            # a 55 x 6 mm tread leg over the pan and a 5 x 36 mm front leg down
            # over the pan's own turned edge.
            SEC = np.array([[0.000, 0.000], [0.055, 0.000], [0.055, -0.006],
                            [0.005, -0.006], [0.005, -0.036], [0.000, -0.036]])
            # a worn nosing has its LEADING arris rounded off — that is the
            # corner at (0, 0), the one boots land on.  The extra vertices exist
            # only on the worn ones, so the meshes genuinely differ.
            if wr > 0.45:
                a2 = np.linspace(0.0, np.pi * 0.5, 4)
                rr = 0.0025 * wr
                nose = np.stack([rr - np.sin(a2) * rr, -rr + np.cos(a2) * rr], 1)
                SEC = np.concatenate([nose, SEC[1:]])
            S2 = np.stack([np.zeros(len(SEC)), SEC[:, 0]], 1)   # +u -> +y, inboard
            Pth = np.stack([[sx - tw * 0.5, ny, tz + 0.004],
                            [sx + tw * 0.5, ny, tz + 0.004]])
            V = (Pth[:, None, :]
                 + np.stack([S2[:, 0], S2[:, 1], SEC[:, 1]], 1)[None, :, :])
            Vf = V.reshape(-1, 3)
            nn, mm = 2, len(SEC)
            Q = _grid_quads(nn, mm, close_m=True)
            Vf = np.concatenate([Vf, Vf[:mm].mean(0)[None, :],
                                 Vf[mm:2 * mm].mean(0)[None, :]])
            Tr = np.concatenate([_fan(nn * mm, np.arange(mm), reverse=True),
                                 _fan(nn * mm + 1, mm + np.arange(mm))])
            acc.solid(Vf, quads=Q, tris=Tr, mat=M_ANOD, hd_anod=0.30,
                      hd_wear=wr, hd_id=h01(kk, 30 + r), hd_grime=0.35,
                      hd_edge=0.7, hd_wet=d.wet)
            for gq in range(2):
                gy = ny + 0.014 + gq * 0.024
                _grit_strip(acc, d, (sx, gy, tz + 0.0049),
                            (tw * 0.5 - 0.006, 0, 0), (0, 0.0090, 0),
                            wr, h01(kk, 40 + r * 3 + gq))
            # --- THE RISER CLOSES THE STEP, at the nose, not behind it -------
            # It was at `ty1` too, hanging 137 mm into open air behind the tread
            # and closing nothing: from in front you saw straight through the
            # stair to the apron, which is why the run read as a skeleton.  A
            # riser stands under the NOSE, set back 22 mm, and it lands on the
            # tread below (or, on the last one, on the apron).
            zb = tz - rise
            obox(acc, np.array([sx, ty0 + 0.010, (tz + zb) * 0.5 - 0.001]),
                 np.array([tw * 0.5 - 0.004, 0, 0]), np.array([0, 0.0010, 0]),
                 np.array([0, 0, (tz - zb) * 0.5 - 0.003]), mat=M_STAIR,
                 chamfer=0.0012, hd_id=h01(kk, 50 + r), hd_grime=0.74,
                 hd_wear=0.06, hd_edge=0.25, hd_wet=d.wet, **stair_kw)
        # --- the foot: base plate, shim stack, two anchors ---------------------
        # 0.020 m of embed (law 5) plus the shims a real erector packs under a
        # stair whose apron falls 1.6 %: the plate is level, the concrete is not.
        yf = d.y0 - going * nr
        for q in range(nstr):
            xo = sx + (-0.5 + q / (nstr - 1)) * (sw - 0.10)
            nsh = 1 + int(rint(0, 2, kk, 300 + q))
            obox(acc, np.array([xo, yf + 0.010, -BASE_EMBED_M + 0.004]),
                 np.array([0.070, 0, 0]), np.array([0, 0.045, 0]),
                 np.array([0, 0, 0.004]), mat=M_MILL, chamfer=0.002,
                 hd_id=h01(kk, 60 + q), hd_grime=0.62, hd_edge=0.4, hd_wet=0.5)
            for s3 in range(nsh):
                sz = -BASE_EMBED_M + 0.008 + s3 * 0.0022
                obox(acc, np.array([xo, yf + 0.010, sz + 0.0011]),
                     np.array([0.052 - 0.004 * s3, 0, 0]),
                     np.array([0, 0.034, 0]), np.array([0, 0, 0.0011]),
                     mat=M_STEEL, chamfer=0.0006,
                     hd_id=h01(kk, 64 + q * 3 + s3), hd_grime=0.7,
                     hd_edge=0.5, hd_wet=0.6)
            for sgn in (-1, 1):
                ax_ = xo + sgn * 0.048
                tube(acc, (ax_, yf + 0.010, -BASE_EMBED_M + 0.004),
                     (ax_, yf + 0.010, -BASE_EMBED_M + 0.030), 0.0058,
                     mat=M_STEEL, n=10, hd_id=h01(kk, 70 + q * 2 + sgn),
                     hd_grime=0.55, hd_edge=0.4, hd_wet=0.5)
                washer(acc, (ax_, yf + 0.010, -BASE_EMBED_M + 0.0195),
                       (0, 0, 1), 0.0060, 0.0125, 0.0022, mat=M_STEEL, n=12,
                       hd_id=h01(kk, 74 + q * 2 + sgn), hd_grime=0.6,
                       hd_edge=0.5, hd_wet=0.5)
                hexnut(acc, np.array([ax_, yf + 0.010, -BASE_EMBED_M + 0.0255]),
                       (0, 0, 1), 0.0080, 0.0065, mat=M_STEEL,
                       hd_id=h01(kk, 78 + q * 2 + sgn), hd_grime=0.6,
                       hd_edge=0.5, hd_wet=0.5)
        # a kick rail closing the bottom of the run between the outer stringers
        x_l = sx - 0.5 * (sw - 0.10)
        x_r = sx + 0.5 * (sw - 0.10)
        obox(acc, np.array([(x_l + x_r) * 0.5, yf - 0.008,
                            -BASE_EMBED_M + 0.052]),
             np.array([(x_r - x_l) * 0.5 - 0.004, 0, 0]),
             np.array([0, 0.0025, 0]), np.array([0, 0, 0.045]),
             mat=M_STAIR, chamfer=0.0015, hd_id=h01(kk, 85), hd_grime=0.66,
             hd_edge=0.35, hd_wet=0.55, **stair_kw)
        # a grab rail on the wider runs
        if sw >= 2.2:
            for sgn in (-1, 1):
                xo = sx + sgn * (sw * 0.5 + 0.045)
                pts = [(xo, d.y0 + 0.05, d.H + 0.95)]
                for r in range(nr + 1):
                    pts.append((xo, d.y0 - going * r, d.H - rise * r + 0.95))
                pts.append((xo, d.y0 - going * nr - 0.12, d.H - rise * nr + 0.88))
                sweep(acc, np.array(pts), circle(0.0210, 12), mat=M_STEEL,
                      smooth=True, hd_id=h01(kk, 70 + sgn),
                      hd_wear=0.55, hd_grime=0.25, hd_edge=0.3)
                for r in (0, nr):
                    zz = d.H - rise * r + 0.95
                    tube(acc, (xo, d.y0 - going * r, zz),
                         (xo, d.y0 - going * r, zz - 0.60), 0.0180,
                         mat=M_STEEL, n=10, hd_id=h01(kk, 80 + r),
                         hd_grime=0.4, hd_edge=0.3)


def _fan_poly(ring, V, reverse=False):
    """Triangulate a simple planar polygon by EAR CLIPPING.

    A step stringer's outline is a staircase — strongly non-convex.  Fanning it
    from one vertex, which is what this did first, lays triangles across the
    notches of every tread: the cap comes out self-overlapping, `Acc.solid`
    computes a meaningless signed volume from it and orients the whole solid on
    that.  At a 12.47 deg sun an inverted face is a black hole in the frame.
    Ear clipping is 25 lines and is simply correct for any simple polygon.
    """
    ring = list(np.asarray(ring, np.int64))
    V = np.asarray(V, float)
    if len(ring) < 3:
        return np.zeros((0, 3), np.int64)
    # Work in the polygon's dominant plane -- and find that plane with NEWELL'S
    # METHOD, which is translation invariant.  Summing cross(a, b) over the raw
    # vertices is only the area normal for a polygon around the ORIGIN: a step
    # stringer sits at x = 4.8 m, where that sum's y and z components carry a
    # factor of 4.8 and swamp the true x normal.  The polygon then gets
    # projected edge-on, every ear test is degenerate, and the cap comes out as
    # a triangular fin -- which is exactly what the first step render showed.
    n = np.zeros(3)
    for i in range(len(ring)):
        a, b = V[i], V[(i + 1) % len(ring)]
        n[0] += (a[1] - b[1]) * (a[2] + b[2])
        n[1] += (a[2] - b[2]) * (a[0] + b[0])
        n[2] += (a[0] - b[0]) * (a[1] + b[1])
    ax = int(np.argmax(np.abs(n))) if np.linalg.norm(n) > 1e-12 else 2
    u, v = [k for k in range(3) if k != ax]
    P = V[:, [u, v]]
    idx = list(range(len(ring)))
    area = 0.0
    for i in range(len(idx)):
        a, b = P[i], P[(i + 1) % len(idx)]
        area += a[0] * b[1] - b[0] * a[1]
    if area < 0:
        idx = idx[::-1]

    def cross2(o, a, b):
        return ((a[0] - o[0]) * (b[1] - o[1])) - ((a[1] - o[1]) * (b[0] - o[0]))

    tris = []
    guard = 0
    while len(idx) > 3 and guard < 4000:
        guard += 1
        clipped = False
        for k in range(len(idx)):
            i0, i1, i2 = idx[k - 1], idx[k], idx[(k + 1) % len(idx)]
            if cross2(P[i0], P[i1], P[i2]) <= 1e-14:
                continue                                  # reflex or collinear
            bad = False
            for j in idx:
                if j in (i0, i1, i2):
                    continue
                if (cross2(P[i0], P[i1], P[j]) >= 0
                        and cross2(P[i1], P[i2], P[j]) >= 0
                        and cross2(P[i2], P[i0], P[j]) >= 0):
                    bad = True
                    break
            if bad:
                continue
            tris.append((ring[i0], ring[i1], ring[i2]))
            idx.pop(k)
            clipped = True
            break
        if not clipped:
            break
    if len(idx) >= 3:
        for i in range(1, len(idx) - 1):
            tris.append((ring[idx[0]], ring[idx[i]], ring[idx[i + 1]]))
    T = np.array(tris, np.int64) if tris else np.zeros((0, 3), np.int64)
    return T[:, ::-1].copy() if reverse else T


# ================================================================================
# 11.  EDGE PROTECTION — five kinds, one of which is none
# ================================================================================

def rail(d):
    """The edge protection this deck has, and the swing clearance it costs."""
    if d.railkind == "none":
        return dict(kind="none", height=0.0, posts=[], clear=0.0)
    h = {"cable": 1.10, "glass": 1.00, "mesh": 1.05, "rope": 0.95}[d.railkind]
    cc = {"cable": 1.35, "glass": 1.15, "mesh": 1.25, "rope": 1.60}[d.railkind]
    posts = []
    for (a, b, nrm) in _edge_runs(d):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(2, int(round(L / cc)) + 1)
        for q in range(n):
            t = q / (n - 1)
            px = a[0] + (b[0] - a[0]) * t
            py = a[1] + (b[1] - a[1]) * t
            skip = any(abs(px - sx) < sw * 0.5 + 0.12 and abs(nrm[1] + 1) < 1e-6
                       for (sx, sw, _, _) in d.steps)
            if skip:
                continue
            posts.append(dict(x=float(px - nrm[0] * 0.055),
                              y=float(py - nrm[1] * 0.055),
                              nx=float(nrm[0]), ny=float(nrm[1])))
    # THE ANODISING INDEX IS PART OF THE EDGE PROTECTION, not a constant.
    # Every anodised part of every rail was emitted at hd_anod = 0.60, which in
    # `mat_anodised` is 60 % of the way from bronze to NATURAL — a 0.49
    # reflectance metal.  Deck 4's mesh infill is 26 m of 12 mm bars at that
    # value facing a 12.47 deg sun, and it came back as a bright white venetian
    # blind that outshone the deck it was supposed to protect.  Anodising is a
    # specified finish: a paddock mesh screen is graphite, a cable rail is
    # natural, a glass spigot is polished-natural, and a rope rail's posts are
    # not anodised at all because they are stainless.
    anod = {"cable": 0.58, "glass": 0.74, "mesh": 0.10, "rope": 0.0}[d.railkind]
    return dict(kind=d.railkind, height=h, posts=posts, clear=0.30,
                anod=float(anod))


def build_rail(acc, d, lod=1.0):
    r = rail(d)
    if r["kind"] == "none":
        return
    h = r["height"]
    an = float(r.get("anod", 0.60))
    kw = dict(hd_grime=0.28, hd_edge=0.45, hd_wet=d.wet * 0.6)
    posts = r["posts"]
    for i, p in enumerate(posts):
        x, y = p["x"], p["y"]
        z0 = deck_top_z(d, x, y)
        kk = d.k * 19.0 + i
        if r["kind"] == "rope":
            tube(acc, (x, y, z0), (x, y, z0 + h - 0.05), 0.0210, mat=M_STEEL,
                 n=14, hd_id=h01(kk, 1), **kw)
            sweep(acc, [(x, y, z0 + h - 0.05), (x, y, z0 + h)],
                  circle(1.0, 14), scale=np.array([[0.0210, 0.0210],
                                                   [0.0340, 0.0340]]),
                  mat=M_STEEL, smooth=True, hd_id=h01(kk, 2), **kw)
            washer(acc, (x, y, z0 + 0.006), (0, 0, 1), 0.021, 0.062, 0.012,
                   mat=M_STEEL, n=16, hd_id=h01(kk, 3), **kw)
        elif r["kind"] == "glass":
            # base channel + a spigot; the glass goes in below
            obox(acc, np.array([x, y, z0 + 0.055]), np.array([0.060, 0, 0]),
                 np.array([0, 0.048, 0]), np.array([0, 0, 0.055]),
                 mat=M_ANOD, chamfer=0.003, hd_anod=an, hd_id=h01(kk, 1), **kw)
        else:
            sec = rect(0.050, 0.050, chamfer=0.004) if r["kind"] == "cable" \
                else rect(0.060, 0.040, chamfer=0.004)
            sweep(acc, [(x, y, z0), (x, y, z0 + h)], sec, mat=M_ANOD,
                  up=(0, 0, 1), hd_anod=an, hd_id=h01(kk, 1), **kw)
            obox(acc, np.array([x, y, z0 + 0.006]), np.array([0.055, 0, 0]),
                 np.array([0, 0.055, 0]), np.array([0, 0, 0.006]),
                 mat=M_ANOD, chamfer=0.003, hd_anod=an, hd_id=h01(kk, 2), **kw)
            for sx2 in (-1, 1):
                for sy2 in (-1, 1):
                    tube(acc, (x + sx2 * 0.040, y + sy2 * 0.040, z0 + 0.012),
                         (x + sx2 * 0.040, y + sy2 * 0.040, z0 + 0.022), 0.0055,
                         mat=M_STEEL, n=8, hd_id=h01(kk, 3), **kw)
    # --- the infill, run to run ---------------------------------------------
    for (a, b, nrm) in _edge_runs(d):
        seg = [p for p in posts if abs(p["nx"] - nrm[0]) < 1e-6
               and abs(p["ny"] - nrm[1]) < 1e-6]
        for i in range(len(seg) - 1):
            p, q = seg[i], seg[i + 1]
            L = math.hypot(q["x"] - p["x"], q["y"] - p["y"])
            if L > 3.0:
                continue                       # the step gap: no infill
            z0 = deck_top_z(d, p["x"], p["y"])
            kk = d.k * 23.0 + i + nrm[0] * 3
            if r["kind"] == "cable":
                for c in range(5):
                    cz = z0 + 0.16 + c * (h - 0.26) / 4.0
                    sag = 0.004 + 0.003 * c
                    n = 9
                    t = np.linspace(0, 1, n)
                    px = p["x"] + (q["x"] - p["x"]) * t
                    py = p["y"] + (q["y"] - p["y"]) * t
                    pz = cz - sag * np.sin(t * np.pi)
                    sweep(acc, np.stack([px, py, pz], 1), circle(0.0030, 7),
                          mat=M_STEEL, smooth=True, hd_id=h01(kk, 10 + c), **kw)
                # top rail
                sweep(acc, [(p["x"], p["y"], z0 + h + 0.014),
                            (q["x"], q["y"], z0 + h + 0.014)],
                      rect(0.060, 0.028, chamfer=0.004), mat=M_ANOD,
                      up=(0, 0, 1), hd_anod=an, hd_id=h01(kk, 20), **kw)
            elif r["kind"] == "glass":
                mx = (p["x"] + q["x"]) * 0.5
                my = (p["y"] + q["y"]) * 0.5
                ux = (q["x"] - p["x"]) / max(L, 1e-9)
                uy = (q["y"] - p["y"]) / max(L, 1e-9)
                obox(acc, np.array([mx, my, z0 + 0.055 + h * 0.5]),
                     np.array([ux, uy, 0.0]) * (L * 0.5 - 0.008),
                     np.array([-uy, ux, 0.0]) * 0.006,
                     np.array([0, 0, h * 0.5]), mat=M_GLASS, chamfer=0.0015,
                     hd_id=h01(kk, 30), hd_grime=0.30, hd_edge=0.6, hd_wet=0.2)
            elif r["kind"] == "mesh":
                mx = (p["x"] + q["x"]) * 0.5
                my = (p["y"] + q["y"]) * 0.5
                ux = (q["x"] - p["x"]) / max(L, 1e-9)
                uy = (q["y"] - p["y"]) / max(L, 1e-9)
                # frame
                for (dz, hh) in ((0.16, 0.020), (h - 0.06, 0.020)):
                    obox(acc, np.array([mx, my, z0 + dz]),
                         np.array([ux, uy, 0.0]) * (L * 0.5 - 0.030),
                         np.array([-uy, ux, 0.0]) * 0.008,
                         np.array([0, 0, hh * 0.5]), mat=M_ANOD, chamfer=0.002,
                         hd_anod=an, hd_id=h01(kk, 40), **kw)
                # perforated sheet: real holes are 3 mm at 5 mm pitch and the
                # sheet is 1.5 mm, so the perforation is modelled as a lattice
                # of bars rather than a plane with a texture on it
                nb = max(4, int((h - 0.24) / 0.045))
                for bq in range(nb):
                    bz = z0 + 0.18 + (bq + 0.5) * (h - 0.24) / nb
                    obox(acc, np.array([mx, my, bz]),
                         np.array([ux, uy, 0.0]) * (L * 0.5 - 0.032),
                         np.array([-uy, ux, 0.0]) * 0.0012,
                         np.array([0, 0, 0.012]), mat=M_ANOD, chamfer=0.0006,
                         hd_anod=an, hd_id=h01(kk, 50 + bq), **kw)
            elif r["kind"] == "rope":
                z1 = z0 + h - 0.02
                n = 13
                t = np.linspace(0, 1, n)
                px = p["x"] + (q["x"] - p["x"]) * t
                py = p["y"] + (q["y"] - p["y"]) * t
                sag = 0.075 + 0.02 * h01(kk, 60)
                pz = z1 - sag * np.sin(t * np.pi) ** 0.85
                a2 = np.linspace(0, 2 * np.pi, 9, endpoint=False)
                rr = 0.0135 + 0.0022 * np.sin(a2 * 3.0)
                sweep(acc, np.stack([px, py, pz], 1),
                      np.stack([np.cos(a2) * rr, np.sin(a2) * rr], 1),
                      mat=M_TRIM, smooth=True,
                      roll=np.linspace(0, 14.0, n),
                      hd_id=h01(kk, 61), hd_grime=0.4, hd_edge=0.3, hd_wet=0.3)


# ================================================================================
# 12.  THE INTERFACE — every number the four dependants need, as a function
# ================================================================================

def threshold(d):
    """The REAR edge, for ``motorhome_unit``.

    `face_y` is the LOCAL y the unit's own front face must land on.  It is not
    the deck's rear edge: this module leaves a 0.150 m shadow gap and has
    already built the closure flashing that bridges it, so a unit built to the
    deck edge would foul the flashing by 150 mm.
    """
    return dict(
        rear_y=float(d.y1),
        gap=0.150,
        face_y=float(d.y1 + 0.150),
        face_cy_circuit=66.000,
        deck_level=float(d.H),
        deck_level_at_threshold=float(deck_top_z(d, 0.0, d.y1 - 0.10)),
        flashing=dict(width=0.150, thickness=0.0015, top_z=float(d.H + 0.002),
                      material="folded mill aluminium, 1.5 mm"),
        landings=[dict(x=float(d.x0 + d.W * (0.28 + 0.44 * q)),
                       y=float(d.y1 - 0.42),
                       w=1.200, dpth=0.780,
                       top_z=float(d.H + 0.0045),
                       kind="chequer plate, 4.5 mm, raised diamond")
                  for q in range(2)],
        note="motorhome_unit builds its floor to deck_level and its face to "
             "face_y; the 0.150 m gap is where its own drip and this deck's "
             "closure flashing meet.")


def unit_bays(d):
    """Where the motorhome bodies park at each end of the deck."""
    out = []
    for sgn in (-1, 1):
        out.append(dict(
            side="west" if sgn < 0 else "east",
            x_inner=float(sgn * (d.W * 0.5 + 0.12)),
            x_outer=float(sgn * (d.W * 0.5 + 0.12 + 2.55)),
            y0=float(d.y1 - 0.20), y1=float(d.y1 + 12.0),
            apron_z=0.0,
            abuts=dict(fascia=d.trim, face_x=float(sgn * d.W * 0.5),
                       deck_level=float(d.H)),
            clear_width=2.55))
    return out


def awning_anchors(d):
    """Where ``hospitality_awning``'s legs land.  The plates are already built."""
    out = []
    n = 2 if d.W < 14.0 else 3
    for q in range(n):
        x = d.x0 + d.W * (q + 0.5) / n
        y = d.y0 + 0.42
        out.append(dict(x=float(x), y=float(y),
                        top_z=float(deck_top_z(d, x, y)),
                        plate=dict(w=0.200, d=0.200, t=0.010,
                                   material="mill aluminium"),
                        studs=dict(n=4, dia=0.012, pitch=0.150,
                                   proud=0.026, thread="M12"),
                        note="hospitality_awning stands its leg on the plate "
                             "and bolts to the four studs; do not re-drill."))
    return out


def parasol_bases(d):
    """Where a parasol foot can stand: this module doubled the boards and put a
    load-spreading plate in, because a 45 kg base on a 28 mm board between
    joists at 400 mm deflects visibly."""
    out = []
    n = 3 if d.W < 14.0 else 4
    for q in range(n):
        x = d.x0 + d.W * (q + 0.5) / n + rnd(-0.22, 0.22, d.k, 900 + q)
        y = d.y0 + d.D * rnd(0.34, 0.62, d.k, 920 + q)
        out.append(dict(x=float(x), y=float(y),
                        top_z=float(deck_top_z(d, x, y)),
                        plate=dict(w=0.320, d=0.320, t=0.006),
                        doubled=True,
                        max_base_kg=60.0))
    return out


def floor_slots(d):
    """The free rectangles left on the deck, best first.

    Everything this module has already committed the deck to is subtracted: the
    traffic path from the step head to the door, the step head itself, the two
    threshold landings, the awning anchors, the parasol plates and the rail's
    swing clearance.  ``folding_table`` and ``folding_chair`` place into these.
    """
    r = rail(d)
    clear = r["clear"] if r["kind"] != "none" else 0.10
    ex = [(a["x"], a["y"], 0.32, 0.32) for a in awning_anchors(d)]
    ex += [(p["x"], p["y"], 0.42, 0.42) for p in parasol_bases(d)]
    ex += [(l["x"], l["y"], l["w"] * 0.6, l["dpth"] * 0.6)
           for l in threshold(d)["landings"]]
    for (sx, sw, nr, wr) in d.steps:
        ex.append((sx, d.y0 + 0.55, sw * 0.5 + 0.35, 0.55))
    out = []
    # ~0.95 m cells, so ONE slot holds one chair and a table spans two or three.
    # The first version used a fixed 6x3 grid and handed the smallest deck three
    # slots to place 18 chairs and 6 tables into -- a grid coarser than the thing
    # it is supposed to locate is not an interface, it is a shrug.
    nx = max(6, int((d.W - 2 * clear) / 0.95))
    ny = max(3, int((d.D - 2 * clear) / 0.95))
    for i in range(nx):
        for j in range(ny):
            cx = d.x0 + clear + (d.W - 2 * clear) * (i + 0.5) / nx
            cy = d.y0 + clear + (d.D - 2 * clear) * (j + 0.5) / ny
            hx = (d.W - 2 * clear) / nx * 0.5
            hy = (d.D - 2 * clear) / ny * 0.5
            # OVERLAP AREA, not a boolean.  A 0.32 m parasol plate touching the
            # corner of a 0.95 m cell does not make that cell unusable, and the
            # first version dropped the whole cell for it -- which handed the
            # smallest deck 11 slots for the 19 pieces it has to hold.
            cell = (2 * hx) * (2 * hy)
            lost = 0.0
            for (a, c, b, e) in ex:
                ox = max(0.0, min(cx + hx, a + b) - max(cx - hx, a - b))
                oy = max(0.0, min(cy + hy, c + e) - max(cy - hy, c - e))
                lost += ox * oy
            frac = lost / max(cell, 1e-9)
            if frac > 0.45:
                continue
            tw = float(np.mean(traffic(d, np.array([cy if d.axis == "y" else cx]),
                                       np.array([cx if d.axis == "y" else cy]))))
            q = float(np.clip(1.0 - tw * 1.2, 0.0, 1.0)) * \
                (0.75 + 0.25 * (j / max(ny - 1, 1))) * (1.0 - frac)
            out.append(dict(x=float(cx), y=float(cy), hx=float(hx), hy=float(hy),
                            top_z=float(deck_top_z(d, cx, cy)),
                            board_axis=d.axis,
                            over_gap=bool(over_gap(d, np.array([cx]),
                                                   np.array([cy]))[0]),
                            clear_h=2.42 - d.H,
                            faces="front" if j == 0 else
                                  ("rear" if j == ny - 1 else "middle"),
                            quality=round(q, 4)))
    out.sort(key=lambda s: -s["quality"])
    return out


def edge_trim(d):
    proj, drop, kind = TRIM_SECTION[d.trim]
    return dict(kind=d.trim, section=kind, projection=proj, drop=drop,
                outer_y_front=float(d.y0 - proj),
                outer_x_west=float(d.x0 - proj),
                outer_x_east=float(d.x1 + proj),
                top_z=float(d.H))


def under_deck(d):
    """The clear box under the deck and what this module already put in it."""
    tray_y = d.y1 - 0.55
    return dict(
        clear=dict(x0=float(d.x0 + 0.10), x1=float(d.x1 - 0.10),
                   y0=float(d.y0 + 0.10), y1=float(d.y1 - 0.10),
                   z0=0.0, z1=float(d.ped_top - 0.02)),
        occupied=[dict(what="cable tray + bundles",
                       x0=float(d.x0 + 0.30), x1=float(d.x1 - 0.30),
                       y0=float(tray_y - 0.09), y1=float(tray_y + 0.09),
                       z0=float(d.ped_top - 0.10), z1=float(d.ped_top - 0.02))],
        pedestals=len(pedestal_grid(d)),
        visible_through="board gaps of %.1f mm; %s" % (
            d.gap * 1000.0,
            "the front is OPEN — the frame reads in silhouette"
            if d.skirt == "open" else "a %s skirt closes the front" % d.skirt))


# ================================================================================
# 13.  DECK-MOUNTED DETAIL
# ================================================================================

def build_details(acc, d, lod=1.0):
    """Awning base plates, parasol plates, threshold landings, closure flashing."""
    kw = dict(hd_grime=0.35, hd_edge=0.5, hd_wet=d.wet * 0.7)
    # --- awning anchor plates + M12 studs ------------------------------------
    for i, a in enumerate(awning_anchors(d)):
        z = a["top_z"]
        obox(acc, np.array([a["x"], a["y"], z + 0.005]),
             np.array([0.100, 0, 0]), np.array([0, 0.100, 0]),
             np.array([0, 0, 0.005]), mat=M_MILL, chamfer=0.004,
             hd_id=h01(d.k, 1100 + i), **kw)
        for sx in (-1, 1):
            for sy in (-1, 1):
                px = a["x"] + sx * 0.075
                py = a["y"] + sy * 0.075
                tube(acc, (px, py, z + 0.010), (px, py, z + 0.036), 0.0060,
                     mat=M_STEEL, n=8, hd_id=h01(d.k, 1110 + i), **kw)
                hexnut(acc, np.array([px, py, z + 0.018]), (0, 0, 1),
                       0.0100, 0.010, mat=M_STEEL,
                       hd_id=h01(d.k, 1120 + i), **kw)
    # --- parasol load-spreading plates ---------------------------------------
    for i, p in enumerate(parasol_bases(d)):
        # hd_wear DRIVES ROUGHNESS DOWN in `mat_mill` (0.78 dirty -> 0.40
        # polished), so a 0.5 here made a 320 mm plate lying flat on the deck
        # into a half-mirror: in the CAM_TOP inspection it returned the sky as a
        # flat blue rectangle sitting on the boards like a sticker.  A plate that
        # lives outdoors under a parasol foot is scuffed and dusty, not polished.
        obox(acc, np.array([p["x"], p["y"], p["top_z"] + 0.003]),
             np.array([0.160, 0, 0]), np.array([0, 0.160, 0]),
             np.array([0, 0, 0.003]), mat=M_MILL, chamfer=0.0035,
             hd_id=h01(d.k, 1200 + i), hd_wear=0.22, hd_grime=0.78,
             hd_edge=0.5, hd_wet=d.wet * 0.7)
    # --- threshold landings: chequer plate with REAL raised diamonds ---------
    for i, l in enumerate(threshold(d)["landings"]):
        x0, x1 = l["x"] - l["w"] * 0.5, l["x"] + l["w"] * 0.5
        y0, y1 = l["y"] - l["dpth"] * 0.5, l["y"] + l["dpth"] * 0.5
        obox(acc, np.array([l["x"], l["y"], d.H + 0.00225]),
             np.array([l["w"] * 0.5, 0, 0]), np.array([0, l["dpth"] * 0.5, 0]),
             np.array([0, 0, 0.00225]), mat=M_MILL, chamfer=0.0025,
             hd_id=h01(d.k, 1300 + i), hd_wear=0.7, **kw)
        # a 30 mm diamond at 1.5 mm proud is 5.1 px and 6.8 mm of shadow
        nx = int(l["w"] / 0.062)
        ny = int(l["dpth"] / 0.031)
        for a2 in range(nx):
            for b2 in range(ny):
                cx = x0 + 0.031 + a2 * 0.062 + (0.031 if b2 % 2 else 0.0)
                cy = y0 + 0.0155 + b2 * 0.031
                if cx > x1 - 0.012 or cy > y1 - 0.008:
                    continue
                V = np.array([[cx - 0.021, cy, d.H + 0.0045],
                              [cx, cy - 0.0055, d.H + 0.0045],
                              [cx + 0.021, cy, d.H + 0.0045],
                              [cx, cy + 0.0055, d.H + 0.0045],
                              [cx - 0.013, cy, d.H + 0.0060],
                              [cx, cy - 0.0032, d.H + 0.0060],
                              [cx + 0.013, cy, d.H + 0.0060],
                              [cx, cy + 0.0032, d.H + 0.0060]])
                Q = np.array([[0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6],
                              [3, 0, 4, 7], [4, 5, 6, 7], [0, 3, 2, 1]])
                acc.solid(V, quads=Q, mat=M_MILL,
                          hd_id=h01(d.k, 1400 + a2 * 31 + b2), hd_wear=0.7,
                          **kw)
    # --- closure flashing across the 0.150 m gap to the unit -----------------
    th = threshold(d)
    sweep(acc, [(d.x0 + 0.02, d.y1 + 0.075, d.H), (d.x1 - 0.02, d.y1 + 0.075, d.H)],
          np.array([[-0.075, 0.0], [0.075, 0.0], [0.075, -0.0015],
                    [0.062, -0.0015], [0.062, -0.028], [0.059, -0.028],
                    [0.059, -0.0015], [-0.062, -0.0015], [-0.062, -0.030],
                    [-0.065, -0.030], [-0.065, -0.0015], [-0.075, -0.0015]]),
          mat=M_MILL, up=(0, 0, 1), hd_id=h01(d.k, 1500), hd_grime=0.5,
          hd_edge=0.4, hd_wet=d.wet)
    # --- a hose bib and a small junction box on the end fascia ---------------
    kk = d.k * 29.0
    bx = d.x1 - 0.35
    by = d.y0 + 0.9
    tube(acc, (bx, by, -BASE_EMBED_M), (bx, by, d.H - 0.12), 0.0125,
         mat=M_MILL, n=10, hd_id=h01(kk, 1), hd_grime=0.5, hd_edge=0.3,
         hd_wet=0.4)
    obox(acc, np.array([d.x1 + 0.03, d.y0 + d.D * 0.55, d.H - 0.22]),
         np.array([0.010, 0, 0]), np.array([0, 0.075, 0]),
         np.array([0, 0, 0.105]), mat=M_PAINT, chamfer=0.005,
         tint=np.array((0.30, 0.32, 0.33)), hd_paint=1.0,
         hd_id=h01(kk, 2), hd_grime=0.45, hd_edge=0.5, hd_wet=0.3)
    for q in range(2):
        tube(acc, (d.x1 + 0.04, d.y0 + d.D * 0.55 - 0.03 + q * 0.06, d.H - 0.325),
             (d.x1 + 0.04, d.y0 + d.D * 0.55 - 0.03 + q * 0.06, d.H - 0.44),
             0.0085, mat=M_CABLE, n=8, hd_id=h01(kk, 3 + q), hd_grime=0.55,
             hd_edge=0.2)


def build_deck(acc, d, lod=1.0):
    """The whole terrace, in build order."""
    for p in pedestal_grid(d):
        build_pedestal(acc, d, p, lod)
    build_frame(acc, d, lod)
    build_services(acc, d, lod)
    for rec in board_layout(d):
        build_board(acc, d, rec, lod)
        for sc in rec["screws"]:
            build_screw(acc, d, rec, sc, lod)
    build_trim(acc, d, lod)
    build_skirt(acc, d, lod)
    build_steps(acc, d, lod)
    build_rail(acc, d, lod)
    build_details(acc, d, lod)


# ================================================================================
# 14.  MATERIALS
# ================================================================================
#
# LAW 6, and it is the reason the first pass blotched: every one of these reads
# `TexCoord -> Object` or a per-vertex attribute, NEVER `Geometry -> Position`.
# These decks sit 180-330 m from the world origin; a position-driven procedural
# there has lost most of its mantissa before the first noise octave.

class NT(object):
    """Small node-graph DSL, the same shape as the other item modules'."""

    def __init__(self, name):
        m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
        m.use_nodes = True
        self.m = m
        self.t = m.node_tree
        self.t.nodes.clear()
        self.x = 0
        self.row = 0

    def n(self, typ, **kw):
        nd = self.t.nodes.new(typ)
        self.x += 175
        nd.location = (self.x, self.row * -240)
        for k, v in kw.items():
            if hasattr(nd, k):
                setattr(nd, k, v)
        return nd

    def link(self, a, ai, b, bi):
        self.t.links.new(a.outputs[ai], b.inputs[bi])

    def pin(self, nd, idx, src):
        if src is None:
            return
        if isinstance(src, tuple) and hasattr(src[0], "outputs"):
            self.link(src[0], src[1], nd, idx)
        elif hasattr(src, "outputs"):
            # THE FIRST **ENABLED** OUTPUT, not output 0.  A ShaderNodeMix set
            # to RGBA has four Result sockets and only one is live; the dead
            # Float one is index 0, and linking it feeds Base Colour a number
            # that has nothing to do with the colour chain.
            outs = [o for o in src.outputs if o.enabled] or list(src.outputs)
            self.t.links.new(outs[0], nd.inputs[idx])
        elif isinstance(src, (tuple, list)):
            nd.inputs[idx].default_value = (*src, 1.0) if len(src) == 3 else tuple(src)
        else:
            nd.inputs[idx].default_value = float(src)

    def mix(self, fac, a, b, blend="MIX"):
        nd = self.n("ShaderNodeMix", data_type="RGBA", blend_type=blend)
        self.pin(nd, 0, fac)
        self.pin(nd, 6, a)
        self.pin(nd, 7, b)
        return nd

    def fmix(self, fac, a, b):
        nd = self.n("ShaderNodeMix", data_type="FLOAT")
        self.pin(nd, 0, fac)
        self.pin(nd, 2, a)
        self.pin(nd, 3, b)
        return nd

    def math(self, op, a=None, b=None, clamp=False):
        nd = self.n("ShaderNodeMath", operation=op, use_clamp=clamp)
        self.pin(nd, 0, a)
        self.pin(nd, 1, b)
        return nd

    def vmath(self, op, a=None, b=None, c=None):
        nd = self.n("ShaderNodeVectorMath", operation=op)
        self.pin(nd, 0, a)
        if b is not None:
            self.pin(nd, 1, b)
        if c is not None:
            self.pin(nd, 2, c)
        return nd

    def noise(self, scale, detail=10.0, rough=0.55, vec=None, dist=0.0, dim="3D"):
        nd = self.n("ShaderNodeTexNoise", noise_dimensions=dim)
        nd.inputs["Scale"].default_value = scale
        nd.inputs["Detail"].default_value = detail
        nd.inputs["Roughness"].default_value = rough
        nd.inputs["Distortion"].default_value = dist
        if vec is not None:
            self.pin(nd, 0, vec)
        return nd

    def vor(self, scale, feature="F1", vec=None, rand=1.0):
        nd = self.n("ShaderNodeTexVoronoi", feature=feature)
        nd.inputs["Scale"].default_value = scale
        if "Randomness" in nd.inputs:
            nd.inputs["Randomness"].default_value = rand
        if vec is not None:
            self.pin(nd, 0, vec)
        return nd

    def wave(self, scale, dist=0.0, detail=2.0, vec=None, wtype="BANDS",
             profile="SIN", direction="X"):
        nd = self.n("ShaderNodeTexWave", wave_type=wtype, wave_profile=profile)
        if hasattr(nd, "bands_direction"):
            nd.bands_direction = direction
        nd.inputs["Scale"].default_value = scale
        nd.inputs["Distortion"].default_value = dist
        nd.inputs["Detail"].default_value = detail
        if vec is not None:
            self.pin(nd, 0, vec)
        return nd

    def grad(self, vec=None, gtype="LINEAR"):
        nd = self.n("ShaderNodeTexGradient", gradient_type=gtype)
        if vec is not None:
            self.pin(nd, 0, vec)
        return nd

    def ramp(self, src, stops):
        nd = self.n("ShaderNodeValToRGB")
        self.pin(nd, 0, src)
        el = nd.color_ramp.elements
        while len(el) > 1:
            el.remove(el[-1])
        el[0].position = stops[0][0]
        el[0].color = (*stops[0][1], 1.0)
        for p, c in stops[1:]:
            e = el.new(p)
            e.color = (*c, 1.0)
        return nd

    def attr(self, name):
        nd = self.n("ShaderNodeAttribute", attribute_type="GEOMETRY")
        nd.attribute_name = name
        return nd

    def mapping(self, vec, scale=(1, 1, 1), loc=(0, 0, 0), rot=(0, 0, 0)):
        nd = self.n("ShaderNodeMapping")
        self.pin(nd, 0, vec)
        nd.inputs["Location"].default_value = loc
        nd.inputs["Rotation"].default_value = rot
        nd.inputs["Scale"].default_value = scale
        return nd

    def bump(self, height, strength, distance, normal=None):
        nd = self.n("ShaderNodeBump")
        nd.inputs["Distance"].default_value = distance
        self.pin(nd, "Strength", strength)
        self.pin(nd, "Height", height)
        if normal is not None:
            self.pin(nd, "Normal", normal)
        return nd

    def out(self, shader):
        o = self.n("ShaderNodeOutputMaterial")
        self.link(shader, 0, o, "Surface")
        return o


def mat_board():
    """Weathered hardwood decking, and what four seasons outdoors did to it.

    The grain is driven by `hd_bc`, the board's OWN local coordinate with x
    along the grain, so every board's figure is its own and no two boards in
    2,145 linear metres share a pattern.  `hd_age` silvers it, `hd_wear` polishes
    the traffic path, `hd_wet` grows algae in the gaps and `hd_end` turns the
    cut ends into open end grain.
    """
    t = NT(PFX + "Board")
    bc = t.attr("hd_bc")
    age = t.attr("hd_age")
    wear = t.attr("hd_wear")
    wet = t.attr("hd_wet")
    end = t.attr("hd_end")
    grime = t.attr("hd_grime")
    edge = t.attr("hd_edge")
    tint = t.attr("hd_tint")
    pid = t.attr("hd_id")
    co = t.n("ShaderNodeTexCoord")

    # per-board offset so two boards never share a figure
    off = t.vmath("SCALE", (pid, 0), None)
    off.inputs[3].default_value = 37.0
    g = t.vmath("ADD", (bc, 1), (off, 0))
    gm = t.mapping(g, scale=(1.0, 118.0, 1.0))

    # --- growth rings: bands across the width, warped by the board's own
    #     bow, then distorted so they are not a barcode ----------------------
    warp = t.noise(2.2, 8.0, 0.55, vec=(gm, 0), dist=0.4)
    ring = t.wave(1.0, dist=6.0, detail=6.0, vec=(gm, 0), direction="Y")
    ring2 = t.wave(2.7, dist=3.5, detail=5.0, vec=(gm, 0), direction="Y")
    late = t.ramp(t.math("MULTIPLY", (ring, 0),
                         t.math("ADD", 0.55, t.math("MULTIPLY", (ring2, 0), 0.45))),
                  [(0.00, (0.0, 0.0, 0.0)), (0.42, (0.12, 0.12, 0.12)),
                   (0.58, (0.88, 0.88, 0.88)), (1.00, (1.0, 1.0, 1.0))])
    early = SPECIES["euro_oak"]["early"]
    latec = SPECIES["euro_oak"]["late"]
    col = t.mix((late, 0), early, latec)
    col = t.mix(t.math("MULTIPLY", (warp, 0), 0.30), col, P["wood_end"])

    # --- ray fleck and medullary figure ------------------------------------
    fleck = t.vor(190.0, "F1", vec=(gm, 0), rand=0.95)
    col = t.mix(t.ramp((fleck, 0), [(0.0, (0.55, 0.55, 0.55)),
                                    (0.14, (0.0, 0.0, 0.0)),
                                    (1.0, (0.0, 0.0, 0.0))]),
                col, P["wood_knot"])

    # --- knots ---------------------------------------------------------------
    kn = t.vor(9.5, "F1", vec=(t.mapping(g, scale=(1.0, 3.4, 1.0)), 0), rand=0.9)
    knm = t.ramp((kn, 0), [(0.0, (1.0, 1.0, 1.0)), (0.055, (1.0, 1.0, 1.0)),
                           (0.085, (0.0, 0.0, 0.0)), (1.0, (0.0, 0.0, 0.0))])
    col = t.mix((knm, 0), col, P["wood_knot"])

    # --- UV silvering: the surface goes grey from the top down --------------
    # 0.72 + 0.55*noise reaches 1.27 x age, so a deck at age 0.62 went 79 % of
    # the way to flat grey and no species read as itself.  Silvering is a thin
    # surface layer that the grain still shows through, and it is BLOTCHY --
    # which is what the noise term is for, so let it carry more of the weight.
    silv = t.math("MULTIPLY", (age, 2),
                  t.math("ADD", 0.34, t.math("MULTIPLY",
                                             (t.noise(6.5, 9.0, 0.6, vec=(gm, 0)), 0), 0.52)))
    col = t.mix(silv, col, SPECIES["euro_oak"]["silver"])

    # --- tannin streaks running down the length -----------------------------
    streak = t.noise(3.2, 9.0, 0.68,
                     vec=(t.mapping(g, scale=(0.35, 26.0, 1.0)), 0), dist=1.1)
    col = t.mix(t.math("MULTIPLY",
                       t.ramp((streak, 0), [(0.42, (0, 0, 0)), (0.66, (1, 1, 1))]),
                       t.math("MULTIPLY", (age, 2), 0.55)),
                col, P["grime"])

    # --- algae where it stays damp: the gap edges and the shaded end --------
    alg = t.noise(24.0, 11.0, 0.62, vec=(gm, 0))
    col = t.mix(t.math("MULTIPLY", (wet, 2),
                       t.ramp((alg, 0), [(0.34, (0, 0, 0)), (0.62, (1, 1, 1))])),
                col, P["algae"])

    # --- end grain -----------------------------------------------------------
    col = t.mix(t.math("MULTIPLY", (end, 2), 0.85), col, P["wood_end"])
    # --- traffic polish darkens and saturates --------------------------------
    col = t.mix(t.math("MULTIPLY", (wear, 2), 0.42), col, P["wood_oiled"])
    # --- settled dirt --------------------------------------------------------
    dirt = t.noise(52.0, 12.0, 0.6, vec=(co, "Object"))
    col = t.mix(t.math("MULTIPLY", (grime, 2),
                       t.math("ADD", 0.45, t.math("MULTIPLY", (dirt, 0), 0.55))),
                col, P["dust"])
    # `mix(fac=tint, A=col, B=col, MULTIPLY)` computes mix(col, col*col, tint)
    # -- it SQUARES the colour and the tint never reaches the surface.  Every
    # one of 508 boards came out the same tone in the first macro render, which
    # is "one asset spammed" happening in the shader instead of the mesh.
    # `mix(fac=1, A=col, B=tint, MULTIPLY)` is col * tint, which is the intent.
    col = t.mix(1.0, col, (tint, 0), blend="MULTIPLY")

    # --- relief --------------------------------------------------------------
    b = t.bump((late, 0), t.math("MULTIPLY", (age, 2), 0.75), 0.0016)
    b = t.bump((knm, 0), 0.55, 0.0025, normal=b)
    b = t.bump(t.noise(320.0, 12.0, 0.62, vec=(gm, 0)), 0.30, 0.0007, normal=b)
    b = t.bump((fleck, 0), t.math("MULTIPLY", (edge, 2), 0.25), 0.0005, normal=b)

    bs = t.n("ShaderNodeBsdfPrincipled")
    t.pin(bs, "Base Color", (col, 2))
    rough = t.fmix((wear, 2), t.fmix((age, 2), 0.62, 0.88), 0.44)
    rough = t.fmix((end, 2), rough, 0.93)
    rough = t.fmix((wet, 2), rough, 0.58)
    t.pin(bs, "Roughness", rough)
    t.pin(bs, "Normal", b)
    if "Specular IOR Level" in bs.inputs:
        t.pin(bs, "Specular IOR Level", t.fmix((wear, 2), 0.36, 0.52))
    t.out(bs)
    return t.m


def mat_composite():
    """Wood-plastic composite: extruded, chalked by UV, scuffed by chairs."""
    t = NT(PFX + "Composite")
    bc = t.attr("hd_bc")
    age = t.attr("hd_age")
    wear = t.attr("hd_wear")
    grime = t.attr("hd_grime")
    pid = t.attr("hd_id")
    co = t.n("ShaderNodeTexCoord")
    off = t.vmath("SCALE", (pid, 0), None)
    off.inputs[3].default_value = 23.0
    g = t.vmath("ADD", (bc, 1), (off, 0))
    gm = t.mapping(g, scale=(0.9, 62.0, 1.0))
    # the extruder drags a faint stripe along the length; the filler is fleck
    stripe = t.wave(1.0, dist=1.2, detail=3.0, vec=(gm, 0), direction="Y")
    fleck = t.vor(320.0, "F1", vec=(gm, 0), rand=1.0)
    fine = t.noise(240.0, 12.0, 0.65, vec=(gm, 0))
    col = t.mix(t.math("MULTIPLY", (stripe, 0), 0.35), P["wpc_face"], P["wpc_fleck"])
    col = t.mix(t.ramp((fleck, 0), [(0.0, (0.8, 0.8, 0.8)), (0.18, (0, 0, 0)),
                                    (1.0, (0, 0, 0))]), col, P["wpc_fleck"])
    col = t.mix(t.math("MULTIPLY", (age, 2), 0.72), col, P["wpc_chalk"])
    scuff = t.vor(60.0, "F1", vec=(t.mapping(g, scale=(3.0, 0.6, 1.0)), 0), rand=0.85)
    col = t.mix(t.math("MULTIPLY", (wear, 2),
                       t.ramp((scuff, 0), [(0.30, (0, 0, 0)), (0.55, (1, 1, 1))])),
                col, P["wpc_chalk"])
    col = t.mix(t.math("MULTIPLY", (grime, 2), 0.5), col, P["grime"])
    b = t.bump((fine, 0), 0.42, 0.0006)
    b = t.bump((stripe, 0), 0.22, 0.0009, normal=b)
    b = t.bump(t.noise(28.0, 9.0, 0.6, vec=(co, "Object")), 0.18, 0.0018, normal=b)
    bs = t.n("ShaderNodeBsdfPrincipled")
    t.pin(bs, "Base Color", (col, 2))
    t.pin(bs, "Roughness", t.fmix((age, 2), t.fmix((wear, 2), 0.68, 0.52), 0.86))
    t.pin(bs, "Normal", b)
    t.out(bs)
    return t.m


def mat_anodised():
    """Anodised aluminium extrusion: die lines along the run, brushed grain
    across it, oxide bloom in the weather, and the colour set by `hd_anod`."""
    t = NT(PFX + "Anodised")
    bc = t.attr("hd_bc")
    anod = t.attr("hd_anod")
    grime = t.attr("hd_grime")
    edge = t.attr("hd_edge")
    wear = t.attr("hd_wear")
    tint = t.attr("hd_tint")
    co = t.n("ShaderNodeTexCoord")
    gm = t.mapping(bc, scale=(340.0, 6.0, 6.0))
    die = t.wave(1.0, dist=0.9, detail=4.0, vec=(gm, 0), direction="X")
    brush = t.noise(900.0, 6.0, 0.72,
                    vec=(t.mapping(bc, scale=(1400.0, 12.0, 12.0)), 0))
    # THREE STOPS, NOT TWO.  A two-stop bronze->natural ramp has no dark end:
    # hd_anod = 0 is still 0.087/0.064/0.043 warm bronze, so the graphite finish
    # that a paddock mesh screen actually has could not be asked for, and the
    # infill came back the colour of teak.  Graphite / bronze / natural, in the
    # order a specifier names them.
    base = t.mix(t.math("MULTIPLY", t.math("MINIMUM", (anod, 2), 0.35), 2.857),
                 P["anod_black"], P["anod_bronze"])
    base = t.mix(t.math("MULTIPLY", t.math("MAXIMUM",
                                           t.math("SUBTRACT", (anod, 2), 0.35),
                                           0.0), 1.538),
                 base, P["anod_natural"])
    base = t.mix(t.math("MULTIPLY", (die, 0), 0.22), base, P["anod_black"])
    bloom = t.noise(14.0, 10.0, 0.6, vec=(co, "Object"), dist=0.5)
    base = t.mix(t.math("MULTIPLY", (grime, 2),
                        t.ramp((bloom, 0), [(0.38, (0, 0, 0)), (0.70, (1, 1, 1))])),
                 base, P["alu_oxide"])
    scr = t.vor(140.0, "F1", vec=(t.mapping(bc, scale=(90.0, 5.0, 5.0)), 0), rand=0.9)
    base = t.mix(t.math("MULTIPLY", (edge, 2),
                        t.ramp((scr, 0), [(0.0, (1, 1, 1)), (0.10, (0, 0, 0)),
                                          (1.0, (0, 0, 0))])),
                 base, P["mill_alu"])
    base = t.mix(t.math("MULTIPLY", (wear, 2), 0.55), base, P["mill_alu"])
    base = t.mix(1.0, base, (tint, 0), blend="MULTIPLY")
    b = t.bump((brush, 0), 0.28, 0.00016)
    b = t.bump((die, 0), 0.20, 0.00035, normal=b)
    b = t.bump((bloom, 0), t.math("MULTIPLY", (grime, 2), 0.45), 0.0009, normal=b)
    bs = t.n("ShaderNodeBsdfPrincipled")
    t.pin(bs, "Base Color", (base, 2))
    t.pin(bs, "Metallic", 1.0)
    # 0.24-0.36 was a mirror.  Anodising is an OXIDE layer, not a polish: it
    # scatters, and a paddock extrusion has a season of dust in it.  At 0.30 the
    # rail posts and the mesh infill returned the blue sky dome almost
    # specularly and read as blue plastic in the first macro render.
    t.pin(bs, "Roughness", t.fmix((grime, 2), t.fmix((wear, 2), 0.52, 0.40), 0.74))
    t.pin(bs, "Normal", b)
    if "Anisotropic" in bs.inputs:
        t.pin(bs, "Anisotropic", 0.55)
    t.out(bs)
    return t.m


def mat_mill():
    """Mill-finish aluminium and sand castings: the pedestal parts, the trays,
    the flashings.  Never polished, always a little oxidised."""
    t = NT(PFX + "MillAlu")
    bc = t.attr("hd_bc")
    grime = t.attr("hd_grime")
    edge = t.attr("hd_edge")
    wear = t.attr("hd_wear")
    wet = t.attr("hd_wet")
    pid = t.attr("hd_id")
    co = t.n("ShaderNodeTexCoord")
    cast = t.vor(420.0, "F1", vec=(co, "Object"), rand=1.0)
    fine = t.noise(700.0, 12.0, 0.68, vec=(co, "Object"))
    mach = t.wave(260.0, dist=0.6, detail=3.0, vec=(co, "Object"), direction="X")
    ox = t.noise(9.0, 10.0, 0.62, vec=(co, "Object"), dist=0.7)
    col = t.mix(t.math("MULTIPLY", (cast, 0), 0.45), P["mill_alu"], P["mill_dull"])
    col = t.mix(t.math("MULTIPLY", (mach, 0), 0.18), col, P["alu_cast"])
    col = t.mix(t.math("MULTIPLY", (grime, 2),
                       t.ramp((ox, 0), [(0.35, (0, 0, 0)), (0.72, (1, 1, 1))])),
                col, P["alu_oxide"])
    col = t.mix(t.math("MULTIPLY", (wet, 2), 0.45), col, P["grime"])
    col = t.mix(t.math("MULTIPLY", (wear, 2), 0.60), col, P["stainless"])
    col = t.mix(t.math("MULTIPLY", (edge, 2), 0.28), col, P["mill_alu"])
    b = t.bump((fine, 0), 0.35, 0.00022)
    b = t.bump((cast, 0), 0.42, 0.00045, normal=b)
    b = t.bump((ox, 0), t.math("MULTIPLY", (grime, 2), 0.5), 0.0011, normal=b)
    bs = t.n("ShaderNodeBsdfPrincipled")
    t.pin(bs, "Base Color", (col, 2))
    t.pin(bs, "Metallic", 1.0)
    t.pin(bs, "Roughness", t.fmix((wear, 2), t.fmix((grime, 2), 0.54, 0.78), 0.40))
    t.pin(bs, "Normal", b)
    t.out(bs)
    return t.m


def mat_stainless():
    """304 stainless: the screws, the cables, the drip trim, the grab rails.
    Outdoors it tea-stains, which is the brown weep the fixings leave."""
    t = NT(PFX + "Stainless")
    bc = t.attr("hd_bc")
    grime = t.attr("hd_grime")
    wear = t.attr("hd_wear")
    wet = t.attr("hd_wet")
    edge = t.attr("hd_edge")
    pid = t.attr("hd_id")
    co = t.n("ShaderNodeTexCoord")
    pol = t.noise(1600.0, 8.0, 0.75,
                  vec=(t.mapping((co, "Object"), scale=(60.0, 1.0, 1.0)), 0))
    scr = t.vor(260.0, "F1", vec=(co, "Object"), rand=0.92)
    stain = t.noise(22.0, 11.0, 0.64, vec=(co, "Object"), dist=0.9)
    col = t.mix(t.math("MULTIPLY", (pol, 0), 0.30), P["stainless"], P["stain_dull"])
    col = t.mix(t.math("MULTIPLY", (grime, 2), 0.55), col, P["grime"])
    tea = t.math("MULTIPLY", (pid, 2),
                 t.math("MULTIPLY", t.math("ADD", (wet, 2), 0.25),
                        t.ramp((stain, 0), [(0.40, (0, 0, 0)), (0.74, (1, 1, 1))])))
    col = t.mix(tea, col, P["tea_stain"])
    col = t.mix(t.math("MULTIPLY", (wear, 2), 0.7), col, P["stainless"])
    b = t.bump((pol, 0), 0.22, 0.00010)
    b = t.bump((scr, 0), t.math("MULTIPLY", (edge, 2), 0.35), 0.00025, normal=b)
    b = t.bump((stain, 0), 0.20, 0.00060, normal=b)
    bs = t.n("ShaderNodeBsdfPrincipled")
    t.pin(bs, "Base Color", (col, 2))
    t.pin(bs, "Metallic", 1.0)
    # a brushed 304 grab rail, not a mirror-polished one: 0.17 made every
    # handrail and cable a blue sky reflection.
    t.pin(bs, "Roughness", t.fmix((wear, 2), t.fmix((grime, 2), 0.38, 0.62), 0.26))
    t.pin(bs, "Normal", b)
    t.out(bs)
    return t.m


def mat_paint():
    """Powder coat over ply and steel, in the brand colours.  Chalks, chips at
    the arrises and streaks below every fixing."""
    t = NT(PFX + "Paint")
    tint = t.attr("hd_tint")
    grime = t.attr("hd_grime")
    edge = t.attr("hd_edge")
    wet = t.attr("hd_wet")
    pid = t.attr("hd_id")
    co = t.n("ShaderNodeTexCoord")
    peel = t.noise(520.0, 9.0, 0.58, vec=(co, "Object"))          # orange peel
    chip = t.vor(90.0, "F1", vec=(co, "Object"), rand=0.95)
    chalk = t.noise(11.0, 10.0, 0.60, vec=(co, "Object"), dist=0.6)
    run = t.noise(6.0, 11.0, 0.68,
                  vec=(t.mapping((co, "Object"), scale=(1.0, 1.0, 22.0)), 0),
                  dist=1.2)
    # THE BRAND COLOUR IS THE BASE, not a factor between two identical greys.
    # The first version was `mix(fac=tint, A=0.55 grey, B=0.55 grey, MULTIPLY)`,
    # which can only ever return a grey: PALLAS deep purple went in and a cream
    # panel came out.  Start from the tint and weather it from there.
    #
    # 0.22 TOWARDS `dust` WAS TOO MUCH, and dust (0.226, 0.206, 0.172) is
    # BRIGHTER and warmer than any of the brand colours: at 22 % the deep
    # aubergine came back as pastel mauve, which is what four square metres of
    # the fascia read as in the second macro.  Chalking is a thin bloom on top
    # of the colour, not a quarter of it, and what it blooms towards is a
    # desaturated version of the paint, not sand.
    base = t.mix(t.math("MULTIPLY", (chalk, 0), 0.085), (tint, 0),
                 (0.150, 0.146, 0.138))
    chipm = t.math("MULTIPLY", (edge, 2),
                   t.ramp((chip, 0), [(0.0, (1, 1, 1)), (0.07, (0, 0, 0)),
                                      (1.0, (0, 0, 0))]))
    base = t.mix(chipm, base, P["mill_dull"])
    base = t.mix(t.math("MULTIPLY", (grime, 2),
                        t.ramp((run, 0), [(0.38, (0, 0, 0)), (0.78, (1, 1, 1))])),
                 base, P["grime"])
    base = t.mix(t.math("MULTIPLY", (wet, 2), 0.35), base, P["grime"])
    # --- THE SPLASH LINE, which is what says "this panel is outdoors" --------
    # Object Z is height above grade for every part of this item, because every
    # deck is recentred on the ground at its own plan centre (law 6).  So the
    # bottom 260 mm of every painted panel gets the rain splash the apron throws
    # at it, ramped with noise so it is a tide mark and not a gradient.  At the
    # filmed distance that band is 44 px tall; without it a 4 m2 panel has no
    # relationship to the ground it stands on.
    zsep = t.n("ShaderNodeSeparateXYZ")
    t.pin(zsep, 0, (co, "Object"))
    spl = t.math("SUBTRACT",
                 t.ramp((zsep, 2), [(0.020, (1, 1, 1)), (0.330, (0, 0, 0))]),
                 t.math("MULTIPLY",
                        t.ramp((t.noise(9.0, 8.0, 0.62, vec=(co, "Object")), 0),
                               [(0.35, (0, 0, 0)), (0.62, (1, 1, 1))]), 0.45))
    base = t.mix(t.math("MULTIPLY", spl, 0.95), base, P["grime"])
    b = t.bump((peel, 0), 0.30, 0.00018)
    b = t.bump(chipm, 0.70, 0.00035, normal=b)
    b = t.bump((chalk, 0), 0.18, 0.0009, normal=b)
    bs = t.n("ShaderNodeBsdfPrincipled")
    t.pin(bs, "Base Color", (base, 2))
    # ROUGHNESS 0.38-0.74 WAS A SHEEN, AND THE SHEEN WAS THE COLOUR.  Measured,
    # not guessed: the stair is emitted with a 0.0475 graphite tint — verified
    # on the mesh, vertex by vertex, and again by a material-ID render — and it
    # came back at 0.47 sRGB, the same warm beige as mill aluminium.  A near-
    # black dielectric at 0.63 roughness under a 12.47 deg sun returns
    # R_fresnel(65 deg) ~ 0.09 of the direct beam as a broad specular lobe:
    # 0.72 W/m2/sr against the 0.38 the base colour contributes.  Two thirds of
    # what was on screen was THE SUN'S OWN WARM COLOUR bounced off a black
    # surface, and no change to the tint could ever have fixed it.  A powder
    # coat that has chalked for a season is 0.62-0.93 rough and its specular is
    # a fraction of new paint's.
    t.pin(bs, "Roughness", t.fmix((grime, 2), t.fmix((pid, 2), 0.62, 0.74), 0.93))
    if "Specular IOR Level" in bs.inputs:
        t.pin(bs, "Specular IOR Level", t.fmix((grime, 2), 0.42, 0.24))
    t.pin(bs, "Normal", b)
    t.out(bs)
    return t.m


def mat_grit():
    """Carborundum anti-slip insert.  The particles are geometry; this is the
    resin binder they sit in, and the polish that wear puts on them."""
    t = NT(PFX + "Grit")
    wear = t.attr("hd_wear")
    grime = t.attr("hd_grime")
    wet = t.attr("hd_wet")
    co = t.n("ShaderNodeTexCoord")
    part = t.vor(1400.0, "F1", vec=(co, "Object"), rand=1.0)
    part2 = t.vor(3400.0, "F1", vec=(co, "Object"), rand=1.0)
    bind = t.noise(280.0, 11.0, 0.62, vec=(co, "Object"))
    col = t.mix(t.ramp((part, 0), [(0.0, (1, 1, 1)), (0.24, (0, 0, 0)),
                                   (1.0, (0, 0, 0))]), P["resin"], P["grit_dark"])
    col = t.mix(t.math("MULTIPLY", (part2, 0), 0.35), col, P["grit_dark"])
    col = t.mix(t.math("MULTIPLY", (wear, 2), 0.80), col, P["grit_worn"])
    col = t.mix(t.math("MULTIPLY", (grime, 2), 0.45), col, P["grime"])
    b = t.bump((part, 0), t.math("SUBTRACT", 0.9, t.math("MULTIPLY", (wear, 2), 0.8)),
               0.00055)
    b = t.bump((part2, 0), 0.35, 0.00018, normal=b)
    b = t.bump((bind, 0), 0.20, 0.00030, normal=b)
    bs = t.n("ShaderNodeBsdfPrincipled")
    t.pin(bs, "Base Color", (col, 2))
    t.pin(bs, "Roughness", t.fmix((wear, 2), 0.88, 0.38))
    t.pin(bs, "Normal", b)
    if "Specular IOR Level" in bs.inputs:
        t.pin(bs, "Specular IOR Level", t.fmix((wear, 2), 0.42, 0.66))
    t.out(bs)
    return t.m


def mat_trim():
    """Black PVC / EPDM extrusion and the woven rope.  Matt, mould-textured,
    chalking where the sun has been on it for a season."""
    t = NT(PFX + "Trim")
    bc = t.attr("hd_bc")
    grime = t.attr("hd_grime")
    wet = t.attr("hd_wet")
    edge = t.attr("hd_edge")
    pid = t.attr("hd_id")
    co = t.n("ShaderNodeTexCoord")
    mould = t.noise(420.0, 10.0, 0.62, vec=(co, "Object"))
    weave = t.wave(320.0, dist=1.6, detail=4.0,
                   vec=(t.mapping(bc, scale=(1.0, 30.0, 30.0)), 0), direction="X")
    chalkn = t.noise(16.0, 9.0, 0.60, vec=(co, "Object"), dist=0.5)
    col = t.mix(t.math("MULTIPLY", (mould, 0), 0.30), P["pvc_black"], P["rubber"])
    col = t.mix(t.math("MULTIPLY", (weave, 0), 0.28), col, P["pvc_grey"])
    col = t.mix(t.math("MULTIPLY", (grime, 2),
                       t.ramp((chalkn, 0), [(0.40, (0, 0, 0)), (0.72, (1, 1, 1))])),
                col, P["dust"])
    col = t.mix(t.math("MULTIPLY", (edge, 2), 0.20), col, P["pvc_grey"])
    b = t.bump((mould, 0), 0.35, 0.00025)
    b = t.bump((weave, 0), 0.55, 0.00090, normal=b)
    bs = t.n("ShaderNodeBsdfPrincipled")
    t.pin(bs, "Base Color", (col, 2))
    t.pin(bs, "Roughness", t.fmix((grime, 2), t.fmix((wet, 2), 0.78, 0.62), 0.92))
    t.pin(bs, "Normal", b)
    t.out(bs)
    return t.m


def mat_glass():
    """12 mm toughened balustrade glass: roller wave, edge tint, and the dust
    film that makes it read at all under a 12.47 deg sun."""
    t = NT(PFX + "Glass")
    grime = t.attr("hd_grime")
    edge = t.attr("hd_edge")
    co = t.n("ShaderNodeTexCoord")
    roll = t.wave(9.0, dist=0.5, detail=2.0, vec=(co, "Object"), direction="Y")
    dust = t.noise(38.0, 10.0, 0.60, vec=(co, "Object"), dist=0.4)
    smear = t.noise(6.0, 8.0, 0.55, vec=(co, "Object"), dist=1.4)
    bs = t.n("ShaderNodeBsdfPrincipled")
    t.pin(bs, "Base Color", P["glass_tint"])
    t.pin(bs, "Transmission Weight", 1.0)
    t.pin(bs, "IOR", 1.52)
    t.pin(bs, "Roughness",
          t.fmix((grime, 2), 0.02,
                 t.fmix(t.ramp((dust, 0), [(0.4, (0, 0, 0)), (0.75, (1, 1, 1))]),
                        0.06, 0.20)))
    b = t.bump((roll, 0), 0.12, 0.0009)
    b = t.bump((smear, 0), t.math("MULTIPLY", (grime, 2), 0.25), 0.0004, normal=b)
    t.pin(bs, "Normal", b)
    t.out(bs)
    return t.m


def mat_cable():
    """PVC cable sheath under the deck: extrusion ribs, dust, drag scuffs."""
    t = NT(PFX + "Cable")
    bc = t.attr("hd_bc")
    grime = t.attr("hd_grime")
    pid = t.attr("hd_id")
    co = t.n("ShaderNodeTexCoord")
    rib = t.wave(900.0, dist=0.4, detail=2.0,
                 vec=(t.mapping(bc, scale=(1.0, 1.0, 1.0)), 0), direction="X")
    dust = t.noise(120.0, 10.0, 0.62, vec=(co, "Object"))
    scuff = t.vor(300.0, "F1", vec=(co, "Object"), rand=0.9)
    base = t.mix((pid, 2), P["cable_black"], P["cable_blue"])
    base = t.mix(t.math("MULTIPLY", (rib, 0), 0.18), base, P["pvc_grey"])
    base = t.mix(t.math("MULTIPLY", (grime, 2),
                        t.ramp((dust, 0), [(0.42, (0, 0, 0)), (0.72, (1, 1, 1))])),
                 base, P["dust"])
    base = t.mix(t.math("MULTIPLY", (scuff, 0), 0.15), base, P["pvc_grey"])
    b = t.bump((rib, 0), 0.30, 0.00020)
    b = t.bump((dust, 0), 0.18, 0.00035, normal=b)
    bs = t.n("ShaderNodeBsdfPrincipled")
    t.pin(bs, "Base Color", (base, 2))
    t.pin(bs, "Roughness", t.fmix((grime, 2), 0.52, 0.80))
    t.pin(bs, "Normal", b)
    t.out(bs)
    return t.m


def build_materials():
    """In MAT_ORDER, so material_index means the same thing on all five decks."""
    fns = [mat_board, mat_anodised, mat_mill, mat_stainless, mat_paint,
           mat_grit, mat_trim, mat_glass, mat_composite, mat_cable]
    return [f() for f in fns]


# ================================================================================
# 15.  BUILD
# ================================================================================

def _coll(name, parent=None):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(c)
    return c


def purge():
    for ob in list(bpy.data.objects):
        if ob.name.startswith(PFX) or ob.name.startswith(CTX):
            bpy.data.objects.remove(ob, do_unlink=True)
    for c in list(bpy.data.collections):
        if c.name.startswith(COLL):
            bpy.data.collections.remove(c)
    for me in list(bpy.data.meshes):
        if me.users == 0:
            bpy.data.meshes.remove(me)


def build(which=None, lod=1.0, scene=None, stats=None):
    """Emit the item into the ``ITEM_HOSPITALITY_DECK`` collection.

    ONE OBJECT PER DECK, named ``HD_Deck_<n>_<Name>``, recentred on its own
    site: the mesh is local (|P| < 9 m) and the object matrix carries the up-to-
    330 m out to the paddock.  That is law 6, and it is also the only reason the
    materials can read TexCoord->Object at all.
    """
    scene = scene or bpy.context.scene
    purge()
    root = _coll(COLL)
    mats = build_materials()
    decks = plan() if which is None else [d for d in plan() if d.n in set(which)]
    tot = dict(objects=0, verts=0, triangles=0, parts=0)
    placed = []
    t0 = time.time()
    for d in decks:
        acc = Acc("%sDeck_%d_%s" % (PFX, d.n, d.name))
        build_deck(acc, d, lod)
        ob, st = acc.build(root, mats, d.R, d.O)
        ob["item"] = ITEM
        ob["deck"] = d.n
        ob["deck_name"] = d.name
        ob["W_m"] = round(float(d.W), 4)
        ob["D_m"] = round(float(d.D), 4)
        ob["H_m"] = round(float(d.H), 4)
        ob["board_gap_mm"] = round(float(d.gap) * 1000.0, 2)
        ob["board_axis"] = d.axis
        ob["board_profile"] = d.profile
        ob["edge_trim"] = d.trim
        ob["skirt"] = d.skirt
        ob["rail"] = d.railkind
        ob["nosing_wear"] = ",".join("%.2f" % s[3] for s in d.steps)
        ob["boards"] = len(board_layout(d))
        ob["pedestals"] = len(pedestal_grid(d))
        tot["objects"] += 1
        placed.append((ob, d.O))
        for k in ("verts", "triangles", "parts"):
            tot[k] += st[k]
        log("deck %d %-8s %5.2f x %4.2f m  H %.3f  gap %4.1f mm  %s boards along "
            "%s  %4d boards  %3d pedestals  %8d tris  trim=%s skirt=%s rail=%s"
            % (d.n, d.name, d.W, d.D, d.H, d.gap * 1000, d.profile, d.axis,
               len(board_layout(d)), len(pedestal_grid(d)), st["triangles"],
               d.trim, d.skirt, d.railkind))
    verify_placement(placed)
    C.stamp(root)
    root["item"] = ITEM
    root["instances"] = len(decks)
    log("built %d decks, %d triangles, %.1f s"
        % (tot["objects"], tot["triangles"], time.time() - t0))
    if stats is not None:
        stats.update(tot)
    return root


# ================================================================================
# 16.  CONTEXT — clearly NOT this item, and excluded from the gate by prefix
# ================================================================================
#
# The gate runs with `--prefix HD_`.  Everything below is `CTX_` and is therefore
# invisible to it, which is the point: a deck rendered in a void cannot be
# judged, and a deck rendered on borrowed ground must not be credited with it.

def mat_ctx_apron():
    t = NT(CTX + "Apron")
    co = t.n("ShaderNodeTexCoord")
    n1_ = t.noise(0.9, 9.0, 0.58, vec=(co, "Object"))
    n2_ = t.noise(14.0, 11.0, 0.62, vec=(co, "Object"), dist=0.5)
    n3_ = t.noise(180.0, 12.0, 0.6, vec=(co, "Object"))
    # DISTANCE_TO_EDGE, not F1.  F1 is the distance to the cell CENTRE, so a
    # ramp over 0..0.02 of it is white almost everywhere and the paving joints
    # never appear -- which is why the first macro render had 300 m of
    # featureless grey under the item.  Distance-to-edge is what a joint is.
    v = t.vor(1.20, "DISTANCE_TO_EDGE", vec=(co, "Object"), rand=0.04)
    joint = t.ramp((v, 0), [(0.0, (0, 0, 0)), (0.030, (1, 1, 1))])
    bay = t.vor(1.20, "F1", vec=(co, "Object"), rand=0.04)
    col = t.mix((n1_, 0), (0.196, 0.192, 0.183), (0.243, 0.239, 0.229))
    col = t.mix(t.math("MULTIPLY", (bay, 1), 0.55), col, (0.168, 0.166, 0.158))
    col = t.mix(t.math("MULTIPLY", (n2_, 0), 0.4), col, (0.148, 0.144, 0.137))
    col = t.mix(t.math("SUBTRACT", 1.0, (joint, 0)), col, (0.075, 0.073, 0.069))
    b = t.bump((n3_, 0), 0.45, 0.0016)
    b = t.bump((joint, 0), 0.85, 0.0060, normal=b)
    bs = t.n("ShaderNodeBsdfPrincipled")
    t.pin(bs, "Base Color", (col, 2))
    t.pin(bs, "Roughness", t.fmix((n2_, 0), 0.80, 0.94))
    t.pin(bs, "Normal", b)
    t.out(bs)
    return t.m


def mat_ctx_unit():
    t = NT(CTX + "Unit")
    co = t.n("ShaderNodeTexCoord")
    n1_ = t.noise(3.0, 8.0, 0.55, vec=(co, "Object"))
    n2_ = t.noise(60.0, 10.0, 0.6, vec=(co, "Object"))
    # A motorhome flank is panelled, not a poured slab.  At 0.33 albedo with no
    # joints it filled the first macro frame as one blown-out white wall and
    # gave the eye nothing to read the deck's 0.66 m against.
    seam = t.wave(0.42, dist=0.0, detail=1.0,
                  vec=(t.mapping((co, "Object"), scale=(1.0, 1.0, 1.0)), 0),
                  wtype="BANDS", profile="SAW", direction="Z")
    seamm = t.ramp((seam, 0), [(0.00, (1, 1, 1)), (0.045, (0, 0, 0)),
                               (1.0, (0, 0, 0))])
    col = t.mix((n1_, 0), (0.208, 0.214, 0.220), (0.171, 0.177, 0.184))
    col = t.mix((seamm, 0), col, (0.086, 0.090, 0.095))
    b = t.bump((n2_, 0), 0.25, 0.0006)
    b = t.bump((seamm, 0), 0.55, 0.004, normal=b)
    bs = t.n("ShaderNodeBsdfPrincipled")
    t.pin(bs, "Base Color", (col, 2))
    t.pin(bs, "Metallic", 0.15)
    t.pin(bs, "Roughness", t.fmix((n1_, 0), 0.54, 0.68))
    t.pin(bs, "Normal", b)
    t.out(bs)
    return t.m


def ctx_paving(coll, cam_world, rect_c, quality="hero", explicit_r=14.0,
               vert_budget=6_000_000):
    """THE GROUND THE MACRO ACTUALLY STANDS ON: the real `paddock_paving_bay`.

    Not a stand-in for it.  `paddock_paving_bay` is a finished item in this same
    campaign — cast-in-situ bays with real screed curl, real saw-cut joints with
    walls and sealant, a sub-base at -40 mm so no joint is a void — and it owns
    exactly the surface this deck stands on.  The first macro render put the
    deck on a hand-rolled 0.6 m grid with a voronoi joint painted on it, and
    that grid filled 45 % of the frame reading as bathroom tile.  Half of a
    render being a placeholder is half a render that cannot be judged.

    This is not borrowing an asset: it is the world's own module, procedural,
    built by hand in this project, called at its own public entry point with an
    anchor and a rect.  If it cannot be imported this returns None and the
    caller falls back to its own grid, because a context module failing must
    never take the item's acceptance scene down with it.

    Returns the circuit-frame rect it paved, so the caller can sink its own
    ground underneath it instead of z-fighting with it.
    """
    try:
        import paddock_paving_bay as PPB
    except Exception as e:                                   # pragma: no cover
        log("context paving unavailable (%s); falling back to the local grid" % e)
        return None
    t0 = time.time()
    st = PPB.build(anchor_world=(float(cam_world[0]), float(cam_world[1]),
                                 float(cam_world[2])),
                   quality=quality, rect_c=tuple(float(v) for v in rect_c),
                   explicit_r=float(explicit_r), field_r=90.0,
                   vert_budget=int(vert_budget))
    log("context paving: %d bays (%d explicit, %d instanced from %d unique "
        "meshes), %d joints, %.1f s"
        % (st["bays_total"], st["bays_explicit"], st["bays_instanced"],
           st["library_meshes"], st["joints"], time.time() - t0))
    return tuple(float(v) for v in rect_c)


def ctx_ground(coll, decks, cell=0.60, far=3200.0, sink_rect=None):
    """The paddock apron under the five decks, plus rings out to the horizon.

    The rings are not decoration: without them the ground stops and the frame
    above that edge is the sky texture's below-horizon direction, which is pure
    black — a hard black band across the bottom of the macro render.

    `sink_rect` is the circuit-frame rectangle `ctx_paving` has covered with
    real concrete.  Inside it this mesh drops to 55 mm below the datum — under
    `paddock_paving_bay`'s own sub-base at -40 mm — so the two never share a
    plane.  Two coplanar ground surfaces is the exact defect the world contract
    was written to stop (R2 defect 50, TER_Ground x ARCH_Paving); it does not
    become acceptable because one of them is context.
    """
    cxs = [d.cx for d in decks]
    c0, c1 = min(cxs) - 40.0, max(cxs) + 40.0
    y0, y1 = 30.0, 92.0
    nx = int((c1 - c0) / cell) + 1
    ny = int((y1 - y0) / cell) + 1
    gx = np.linspace(c0, c1, nx)
    gy = np.linspace(y0, y1, ny)
    X, Y = np.meshgrid(gx, gy, indexing="ij")
    WX, WY = C.circuit_to_world(X.ravel(), Y.ravel())
    Z = np.zeros_like(WX)
    Z += 0.006 * (fbm2(X.ravel() * 0.9, Y.ravel() * 0.9, 71, 4) - 0.5)
    if sink_rect is not None:
        rx0, rx1, ry0, ry1 = sink_rect
        dd = np.minimum(np.minimum(X.ravel() - rx0, rx1 - X.ravel()),
                        np.minimum(Y.ravel() - ry0, ry1 - Y.ravel()))
        t = np.clip(dd / 1.20, 0.0, 1.0)
        Z -= 0.055 * (t * t * (3.0 - 2.0 * t))
    V = np.stack([WX, WY, Z], -1)
    idx = np.arange(nx * ny).reshape(nx, ny)
    Q = np.stack([idx[:-1, :-1].ravel(), idx[1:, :-1].ravel(),
                  idx[1:, 1:].ravel(), idx[:-1, 1:].ravel()], 1)
    # expanding rings to the horizon, sharing the fine patch's boundary loop
    loop = np.concatenate([idx[0, :-1], idx[:-1, -1], idx[-1, :0:-1],
                           idx[-1:0:-1, 0]])
    ctr = np.array([V[:, 0].mean(), V[:, 1].mean()])
    pxy = V[loop, :2] - ctr
    rr = float(np.max(np.abs(pxy)))
    Vl = [V]
    base = nx * ny
    prev = loop
    while rr < far:
        rr = min(far, rr * (1.30 if rr < 260.0 else 1.9))
        sc = rr / max(np.max(np.abs(pxy)), 1e-9)
        nxy = pxy * sc
        nz = -0.02 - 0.35 * np.clip(rr / 900.0, 0.0, 1.0)
        Vl.append(np.stack([nxy[:, 0] + ctr[0], nxy[:, 1] + ctr[1],
                            np.full(len(nxy), nz)], -1))
        k = len(prev)
        cur = base + np.arange(k)
        j = np.arange(k)
        j1 = (j + 1) % k
        Q = np.concatenate([Q, np.stack([prev[j], prev[j1], cur[j1], cur[j]], 1)])
        base += k
        prev = cur
        pxy = nxy
    V = np.concatenate(Vl)
    # RECENTRE, law 6.  These world coordinates are 180-330 m out; leaving the
    # apron at the origin makes its object space equal its world space and the
    # paving procedural is then evaluated at |P| ~ 300 m in float32.  The item
    # obeys this rule, so its context has no business breaking it.
    O = np.array([V[:, 0].mean(), V[:, 1].mean(), 0.0])
    V = V - O
    me = bpy.data.meshes.new(CTX + "Apron")
    me.from_pydata(V.tolist(), [], Q.tolist())
    me.update()
    ob = bpy.data.objects.new(CTX + "Apron", me)
    ob.data.materials.append(mat_ctx_apron())
    coll.objects.link(ob)
    place(ob, np.eye(3), O)
    return ob


def ctx_units(coll, decks):
    """Stubs standing in for `motorhome_unit` and `hospitality_building`, built
    to THIS module's own `threshold()` and `unit_bays()`."""
    mat = mat_ctx_unit()
    for d in decks:
        th = threshold(d)
        acc = Acc("%sUnit_%d" % (CTX, d.n))
        # the frontage the deck butts, built to face_y
        fy = th["face_y"]
        box(acc, (d.x0 - 3.2, fy, -BASE_EMBED_M), (d.x1 + 3.2, fy + 9.0, 4.20),
            mat=0)
        # a glazed band and a fascia so it is not a plain cube in the frame
        box(acc, (d.x0 - 3.0, fy - 0.06, 1.10), (d.x1 + 3.0, fy - 0.02, 2.60),
            mat=0)
        box(acc, (d.x0 - 3.3, fy - 0.14, 4.20), (d.x1 + 3.3, fy + 9.1, 4.55),
            mat=0)
        # --- THE FRONTAGE IS PANELLED, IN GEOMETRY -------------------------
        # Behind the deck stands 23 m x 4.2 m of unit frontage: at 22 m that is
        # 3 900 x 710 px, a third of the macro frame, and it was ONE flat slab
        # with a seam pattern bumped onto it.  A bump throws no shadow at a
        # 12.47 deg sun, so it read as a lit wall of nothing and gave the eye no
        # scale to measure the deck's 0.66 m against.  These are the parts of a
        # real unit flank that actually catch that sun: a recessed plinth, the
        # rolled edge of each 1.15 m panel, the vertical joint reveals, a door
        # into the servery and the shadow gap under the fascia.  All standing
        # proud or recessed by 18-45 mm, all throwing 80-200 mm of shadow.
        x0u, x1u = d.x0 - 3.2, d.x1 + 3.2
        box(acc, (x0u, fy - 0.018, -BASE_EMBED_M),
            (x1u, fy, 0.34), mat=0)                       # plinth, proud 18 mm
        box(acc, (x0u, fy - 0.026, 4.02), (x1u, fy, 4.20), mat=0)   # head band
        pw_ = 1.15
        npn = max(2, int(round((x1u - x0u) / pw_)))
        pw_ = (x1u - x0u) / npn
        # The joint is the GAP BETWEEN THE TRAYS, showing the wall 12 mm behind
        # them.  An extra "reveal" box inside that gap added a third surface
        # that stood 10 mm proud of the wall and 2 mm behind the trays, and at
        # 22 m the sliver of it that caught the sun read as a row of thin
        # vertical RODS standing on the deck — visible in the macro, and not
        # attributable to anything until every builder in the item had been
        # measured to prove it was not one of theirs.  The gap alone is the
        # joint, and it is the one a real panelised flank has.
        for q in range(npn):
            px_ = x0u + q * pw_
            box(acc, (px_ + 0.016, fy - 0.012, 0.36),
                (px_ + pw_ - 0.016, fy, 4.00), mat=0)
        # a servery door and its threshold, at a station that is not the deck's
        dx_ = d.x1 + 1.35
        box(acc, (dx_ - 0.46, fy - 0.004, 0.02), (dx_ + 0.46, fy + 0.055, 2.10),
            mat=0)
        box(acc, (dx_ - 0.50, fy - 0.030, 2.10), (dx_ + 0.50, fy, 2.16), mat=0)
        # THE FLANKING BODIES GO BEHIND THE DECK, NOT ACROSS IT.  The first
        # version ran them from y1-6.0 to y1+0.2, which is a 6.2 m box straddling
        # the whole 4.7 m depth and standing 1.5 m PROUD OF THE DECK FRONT: in
        # the first macro render two white slabs occluded both ends of the item
        # the camera was pointed at.  `unit_bays()` already says y0 = y1-0.20 and
        # y1 = +12.0; the stub has to honour its own interface.
        for b in unit_bays(d):
            box(acc, (min(b["x_inner"], b["x_outer"]), b["y0"], -BASE_EMBED_M),
                (max(b["x_inner"], b["x_outer"]), b["y1"] - 3.0, 4.05), mat=0)
        ob, _ = acc.build(coll, [mat], d.R, d.O)
    return True


# ================================================================================
# 17.  LIGHT — world_contract section 13, not a rounded copy of it
# ================================================================================

def contract_light(scene=None, coll=None):
    """The film's sun and sky exactly as `world_contract` measured them:
    12.47061 deg elevation, bearing -57.96966 deg, AgX at -3.048 EV."""
    scene = scene or bpy.context.scene
    w = bpy.data.worlds.new(PFX + "World")
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    out.location = (600, 0)
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.location = (380, 0)
    sky = nt.nodes.new("ShaderNodeTexSky")
    sky.location = (120, 0)
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
    bg.inputs["Strength"].default_value = C.SKY_STRENGTH
    nt.links.new(sky.outputs["Color"], bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    scene.world = w

    lt = bpy.data.lights.new(PFX + "Sun", "SUN")
    lt.energy = C.SUN_ENERGY
    lt.color = C.SUN_COLOR
    lt.angle = math.radians(C.SUN_ANGULAR_DIAM_DEG)
    lt.use_shadow = True
    ob = bpy.data.objects.new(PFX + "Sun", lt)
    dv = Vector(C.SUN_DIR)
    ob.rotation_mode = "QUATERNION"
    ob.rotation_quaternion = dv.to_track_quat("Z", "Y")
    ob.location = (dv.x * 2000.0, dv.y * 2000.0, dv.z * 2000.0)
    ob.visible_camera = False
    (coll or scene.collection).objects.link(ob)
    scene.view_settings.view_transform = C.VIEW_TRANSFORM
    try:
        scene.view_settings.look = C.VIEW_LOOK
    except Exception:
        pass
    scene.view_settings.exposure = C.REFERENCE_EXPOSURE_EXTERIOR
    log("light: sun %.3f W/m2, elev %.3f deg, bearing %.3f deg; AgX %.3f EV"
        % (C.SUN_ENERGY, C.SUN_ELEV_DEG, C.SUN_BEARING_DEG,
           C.REFERENCE_EXPOSURE_EXTERIOR))
    return ob


def add_camera(name, loc, look, lens, coll, fstop=None):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = SENSOR_MM
    cd.clip_start = 0.05
    cd.clip_end = 20000.0
    ob = bpy.data.objects.new(name, cd)
    ob.location = loc
    dv = Vector(look) - Vector(loc)
    ob.rotation_mode = "QUATERNION"
    ob.rotation_quaternion = dv.to_track_quat("-Z", "Y")
    coll.objects.link(ob)
    if fstop:
        cd.dof.use_dof = True
        cd.dof.focus_distance = float(dv.length)
        cd.dof.aperture_fstop = float(fstop)
    return ob


def hero_deck():
    """The deck the macro camera goes on: the largest, whose boards run TOWARDS
    the lens.  That is not a preference — boards running across the view at a
    13 deg camera elevation foreshorten a 140 mm board to 4 px and a 7 mm gap to
    0.2 px, so the deck would read as a plane with lines on it.  Boards running
    front-to-back keep their full 24 px width across the frame."""
    best, bs = None, -1e9
    for d in plan():
        sc = d.W * d.D + (14.0 if d.axis == "y" else 0.0) + 6.0 * d.H
        if sc > bs:
            best, bs = d, sc
    return best


def macro_camera(d, cams, name=PFX + "CAM_MACRO", elev_deg=11.0, az_deg=-48.0):
    """EXACTLY the manifest's 22.0 m on EXACTLY its 35 mm lens.

    The bearing is derived, not chosen by eye.  The sun sits at circuit azimuth
    -97.970 deg, within 8 deg of normal to the deck's front face, so the fascia
    is frontally lit whatever we do and the modelling has to come from the
    grazing 12.47 deg elevation.  The camera therefore stands on the front
    quarter, where it sees (a) the fascia with the trim's own shadow band across
    it, (b) the deck top with every cupped board and proud fixing throwing a
    shadow away and to the left, and (c) the step nosings edge-on.
    """
    tgt_l = np.array([d.W * 0.10, d.y0 + d.D * 0.22, d.H + 0.35])
    a = math.radians(az_deg)
    e = math.radians(elev_deg)
    cam_l = tgt_l + np.array([math.cos(a) * FILMED_AT_M * math.cos(e),
                              math.sin(a) * FILMED_AT_M * math.cos(e),
                              FILMED_AT_M * math.sin(e)])
    cam = cam_l @ d.R.T + d.O
    tgt = tgt_l @ d.R.T + d.O
    ob = add_camera(name, tuple(cam), tuple(tgt), LENS_MM, cams)
    dist = float(np.linalg.norm(cam - tgt))
    sun_az = math.atan2(C.SUN_DIR[1], C.SUN_DIR[0])
    ax = math.atan2(d.R[1, 0], d.R[0, 0])
    view_az = ax + a + math.pi
    off = math.degrees(abs(((view_az - sun_az + math.pi) % (2 * math.pi)) - math.pi))
    log("%s: %.4f m from deck %d on a %.1f mm lens (manifest: %.1f m / %.0f mm), "
        "sun %.1f deg off the view axis, lens %.2f m above the deck"
        % (name, dist, d.n, LENS_MM, FILMED_AT_M, LENS_MM, off, cam[2] - tgt[2]))
    if abs(dist - FILMED_AT_M) > 1e-4:
        raise RuntimeError("REFUSING: macro camera is %.4f m from the deck, the "
                           "manifest says %.4f m" % (dist, FILMED_AT_M))
    return ob


def _inspection_setups(d):
    """(name, camera_local, target_local, lens_mm) for the close-look cameras.

    Deck-local metres.  Everything is derived from the deck's own dimensions and
    from `step_runs`, so these follow the geometry rather than being typed in
    against one deck and drifting on the other four.
    """
    r0 = step_runs(d)[0]
    sx, sw = r0["x"], r0["width"]
    yf = r0["y_foot"]
    out = [
        # the step run, three-quarter, from the height a standing person sees it
        ("CAM_STEPS", (sx - sw * 0.5 - 2.60, yf - 3.20, 1.85),
         (sx, yf + 0.55, d.H * 0.45), 50.0),
        # the front fascia and the trim's shadow band, square on to the edge
        ("CAM_FASCIA", (d.W * 0.16, d.y0 - 3.90, 1.05),
         (d.W * 0.06, d.y0, d.H * 0.55), 50.0),
        # the walking surface: boards, gaps, screw dishes, grain
        ("CAM_TOP", (d.W * 0.02, d.y0 + d.D * 0.10, d.H + 2.60),
         (d.W * 0.10, d.y0 + d.D * 0.66, d.H), 35.0),
        # kerb height, looking INTO the under-deck at the pedestals and the tray
        ("CAM_UNDER", (d.W * 0.30, d.y0 - 3.60, 0.34),
         (d.W * 0.08, d.y0 + d.D * 0.50, d.H * 0.34), 50.0),
        # the rear threshold and the door landings, for `motorhome_unit`
        ("CAM_THRESH", (d.W * 0.30, d.y0 + d.D * 0.10, d.H + 1.60),
         (d.W * 0.10, d.y1 - 0.20, d.H + 0.10), 35.0),
    ]
    return out


def test_scene(lod=1.0, samples=256, which=None, context=True, paving="hero"):
    """Build the item, light it with the contract sun, and put the manifest's
    own camera on it: 22.0 m, 35 mm — the shot this item has to survive."""
    scene = bpy.context.scene
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    root = build(which=which, lod=lod, scene=scene)
    cams = _coll(COLL + "_Cameras", root)
    contract_light(scene, coll=root)
    decks = plan() if which is None else [x for x in plan() if x.n in set(which)]
    d = hero_deck() if which is None else decks[0]
    macro = macro_camera(d, cams, elev_deg=12.0, az_deg=-47.0)
    # the same distance and lens at eye height — how Beat 4 actually sees it
    macro_camera(d, cams, name=PFX + "CAM_EYE", elev_deg=2.6, az_deg=-62.0)
    # and along the row, which is the shot that proves the five are five
    macro_camera(d, cams, name=PFX + "CAM_RAKE", elev_deg=7.5, az_deg=-14.0)
    # --- INSPECTION CAMERAS ------------------------------------------------
    # NOT the acceptance shot — the acceptance shot is CAM_MACRO at exactly
    # 22.0 m.  These stand where a person would stand to check the work, and
    # they exist because three of the defects found in this item (the step run
    # reading as a skeleton, the black void behind the step opening, the
    # over-bright mesh infill) are invisible at 22 m and unmistakable at 4 m.
    # An item that only ever gets looked at from its filmed distance gets its
    # near-field defects shipped.
    for (nm, cl_, tl_, lens_) in _inspection_setups(d):
        add_camera(PFX + nm, tuple(np.asarray(cl_) @ d.R.T + d.O),
                   tuple(np.asarray(tl_) @ d.R.T + d.O), lens_, cams)
    tl = np.array([0.0, 0.0, d.H])
    cl = tl + np.array([math.cos(math.radians(-70.0)) * 34.0,
                        math.sin(math.radians(-70.0)) * 34.0, 9.0])
    add_camera(PFX + "CAM_WIDE", tuple(cl @ d.R.T + d.O),
               tuple(tl @ d.R.T + d.O), 35.0, cams)
    # --- CONTEXT, built LAST because the paving is anchored on the lens -----
    if context:
        ctxc = _coll(COLL + "_Context", root)
        rect = None
        if paving and paving != "none":
            # `matrix_world` IS STALE UNTIL THE DEPSGRAPH IS UPDATED.  Reading it
            # straight after `bpy.data.objects.new(...); ob.location = ...`
            # returns the IDENTITY, so the anchor came back as the world origin,
            # circuit (-361.5, +81.6).  The paving was then laid over a 396 x 10 m
            # strip 300 m away from the deck, the sink rect missed the camera
            # entirely, and the macro render showed the fallback grid with a
            # mysterious patch of concrete on the horizon.  Nothing about that
            # was visible in any log: every stage reported success on a number
            # that was silently zero.
            bpy.context.view_layer.update()
            cw = np.array(macro.matrix_world.translation, float)
            if float(np.linalg.norm(cw)) < 1.0:
                raise RuntimeError(
                    "REFUSING: the macro camera reads as the world origin, so "
                    "the paving anchor would be 300 m from the item")
            ccx, ccy = C.world_to_circuit(cw[0], cw[1])
            cxs = [x.cx for x in decks]
            rect = (min(float(ccx) - 34.0, min(cxs) - 12.0),
                    max(float(ccx) + 34.0, max(cxs) + 12.0),
                    float(ccy) - 8.0, 84.0)
            rect = ctx_paving(ctxc, cw, rect, quality=paving)
        ctx_ground(ctxc, decks, sink_rect=rect)
        ctx_units(ctxc, decks)
    scene.camera = macro
    scene.render.engine = "CYCLES"
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.film_transparent = False
    scene.cycles.samples = samples
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.01
    scene.cycles.max_bounces = 10
    scene.cycles.diffuse_bounces = 5
    scene.cycles.use_denoising = True
    log("hero deck: %d %s, %.2f x %.2f m, H %.3f m, boards along %s, gap %.1f mm"
        % (d.n, d.name, d.W, d.D, d.H, d.axis, d.gap * 1000))
    return root


# ================================================================================
# 18.  MEASUREMENT — measure the claims, do not assert them
# ================================================================================

def selftest(verbose=True):
    """Every number the header claims, measured.  Needs numpy only."""
    ok = [True]

    def chk(label, cond, detail=""):
        ok[0] &= bool(cond)
        if verbose:
            print("  [%s] %-58s %s" % ("PASS" if cond else "FAIL", label, detail))

    ds = plan()
    chk("five decks, one per hospitality frontage", len(ds) == INSTANCES,
        "%d" % len(ds))

    # --- law 4/5: the datum is never assumed --------------------------------
    dz = []
    for d in ds:
        z, own = C.world_ground_z(d.wx, d.wy)
        dz.append(abs(float(z) - d.gz))
    chk("site z == C.world_ground_z at the site", max(dz) < 1e-9,
        "max |dz| %.3e m, owner %s" % (max(dz), ds[0].owner))
    chk("the paddock apron is the contract plane", all(abs(d.gz) < 1e-9 for d in ds),
        "all five at z = %.6f" % ds[0].gz)

    # --- law 5: everything on the ground embeds -----------------------------
    chk("pedestal base plates embed >= BASE_EMBED_M",
        BASE_EMBED_M >= C.BASE_EMBED_M - 1e-12,
        "base plate bottom at z = %.4f m (need <= %.4f)"
        % (-BASE_EMBED_M, -C.BASE_EMBED_M))

    # --- law 7 / the placement gate -----------------------------------------
    worst, who = 1e9, ""
    for d in ds:
        fp = footprint_world(d, margin=0.35)
        S, U = C.project(fp[:, 0], fp[:, 1])
        clear = float(np.min(np.abs(U) - C.verge_edge(S))) - 0.50
        if clear < worst:
            worst, who = clear, "deck %d" % d.n
    chk("nothing reaches the road corridor", worst >= 0.0,
        "min clearance %+.1f m at %s" % (worst, who))

    # --- and nothing stands in build_architecture's jersey line either -------
    # THE STEP FOOT IS THE FURTHEST-FORWARD PART OF THIS ITEM, not the deck
    # edge.  Measuring the deck edge here would have passed the exact defect
    # this check exists to catch.
    jw, jwho = 1e9, ""
    for d in ds:
        x0c, x1c = d.cx + d.x0, d.cx + d.x1
        foot = min(d.cy_rear - d.D - r["risers"] * r["going"]
                   for r in step_runs(d))
        hit = [j for j in JERSEY_R1 if not (x1c < j[0] or x0c > j[1])]
        if not hit:
            continue
        cl = foot - (JERSEY_R1_CY + JERSEY_R1_HALFWIDTH)
        if cl < jw:
            jw, jwho = cl, "deck %d %s" % (d.n, d.name)
    chk("step feet clear the round-1 jersey line", jw >= 0.10,
        "min clearance %+.2f m at %s (decks 2 and 4 fall between the runs)"
        % (jw, jwho))

    # --- the three named variation axes are GEOMETRY -------------------------
    gaps = sorted(d.gap * 1000 for d in ds)
    chk("board gaps differ between decks (manifest axis 1)",
        len(set(round(g, 2) for g in gaps)) == 5,
        "%s mm" % ", ".join("%.1f" % g for g in gaps))
    nb = [len(board_layout(d)) for d in ds]
    chk("  ...and the gap changes the board COUNT, not just a shader",
        len(set(nb)) == 5, "%s boards" % nb)
    wears = sorted({s[3] for d in ds for s in d.steps})
    chk("step nosing wear differs (manifest axis 2)", len(wears) >= 5,
        "%s" % ", ".join("%.2f" % w for w in wears))
    trims = [d.trim for d in ds]
    chk("edge trim differs on all five (manifest axis 3)",
        len(set(trims)) == 5, ", ".join(trims))
    chk("  ...and the five trims are five different SECTIONS",
        len({TRIM_SECTION[t][2] for t in trims}) == 5,
        ", ".join(sorted({TRIM_SECTION[t][2] for t in trims})))

    # --- variation beyond the named axes -------------------------------------
    sig = set()
    for d in ds:
        sig.add((d.axis, d.profile, d.species, d.fasten, d.frame, d.skirt,
                 d.railkind, round(d.W, 2), round(d.D, 2), round(d.H, 3),
                 len(board_layout(d)), len(pedestal_grid(d))))
    chk("every deck is a different build", len(sig) == len(ds),
        "%d distinct signatures / %d decks" % (len(sig), len(ds)))
    diag = [math.sqrt(d.W ** 2 + d.D ** 2 + d.H ** 2) for d in ds]
    cv = float(np.std(diag) / np.mean(diag))
    chk("size CV >= 0.03 (the gate's per-instance test)", cv >= 0.03,
        "cv %.4f over %.2f .. %.2f m" % (cv, min(diag), max(diag)))
    chk("both board directions are used", len({d.axis for d in ds}) == 2,
        "%s" % sorted({d.axis for d in ds}))
    chk("both frame systems are used", len({d.frame for d in ds}) == 2,
        "%s" % sorted({d.frame for d in ds}))
    chk("one deck uses hidden fixings and shows no screw heads",
        sum(1 for d in ds if d.fasten == "hidden") == 1,
        "%s" % [d.name for d in ds if d.fasten == "hidden"])

    # --- the surface is not the plane ----------------------------------------
    lo, hi = 1e9, -1e9
    for d in ds:
        gx = np.linspace(d.x0 + 0.05, d.x1 - 0.05, 61)
        gy = np.linspace(d.y0 + 0.05, d.y1 - 0.05, 31)
        X, Y = np.meshgrid(gx, gy, indexing="ij")
        z = deck_top_z(d, X.ravel(), Y.ravel()) - d.H
        lo = min(lo, float(z.min()))
        hi = max(hi, float(z.max()))
    chk("deck_top_z departs from the nominal plane", (hi - lo) > 0.004,
        "%+.1f .. %+.1f mm about d.H" % (lo * 1000, hi * 1000))
    chk("  ...and never returns NaN", np.isfinite(lo) and np.isfinite(hi))

    # --- the gaps are holes ---------------------------------------------------
    fr = []
    for d in ds:
        # sample ACROSS the boards, which is x on an axis='y' deck and y on an
        # axis='x' one.  The first version of this check swept x on all five and
        # reported 70 % open for the two axis='x' decks, which was 4,001 samples
        # mostly outside the deck being counted as gap.  A check that measures
        # the wrong axis is worse than no check.
        lo, hi = ((d.x0, d.x1) if d.axis == "y" else (d.y0, d.y1))
        ac = np.linspace(lo + 0.02, hi - 0.02, 4001)
        al = np.full(4001, 0.0)
        og = over_gap(d, ac, al) if d.axis == "y" else over_gap(d, al, ac)
        fr.append(float(np.mean(og)))
    chk("board gaps are real holes in the mesh", min(fr) > 0.008,
        "open fraction across the deck: %s"
        % ", ".join("%.1f%%" % (f * 100) for f in fr))

    # --- the interface answers, for every deck --------------------------------
    bad = []
    for d in ds:
        for fn in (threshold, unit_bays, awning_anchors, parasol_bases,
                   floor_slots, step_runs, rail, edge_trim, under_deck):
            try:
                r = fn(d)
                if r is None or (isinstance(r, (list, tuple)) and not r):
                    bad.append("%s(deck %d) empty" % (fn.__name__, d.n))
            except Exception as e:                          # pragma: no cover
                bad.append("%s(deck %d): %s" % (fn.__name__, d.n, e))
    chk("every interface function answers for every deck", not bad,
        "; ".join(bad[:3]) if bad else "9 functions x 5 decks")

    # --- the interface is CONSISTENT with the mesh -----------------------------
    err = []
    for d in ds:
        for a in awning_anchors(d) + parasol_bases(d):
            z = deck_top_z(d, a["x"], a["y"])
            err.append(abs(z - a["top_z"]))
    chk("anchor top_z == deck_top_z at the anchor", max(err) < 1e-9,
        "max |dz| %.2e m over %d anchors" % (max(err), len(err)))
    fs = [len(floor_slots(d)) for d in ds]
    area = [d.W * d.D for d in ds]
    tot_a = sum(area)
    # 90 chairs + 30 tables + 14 parasols share the five decks BY AREA, not
    # evenly: the smallest deck is not asked to hold the same load as the
    # largest.  A slot is a chair-sized cell, so it has to beat that share.
    share = [134.0 * a / tot_a for a in area]
    chk("free floor slots exceed each deck's share of the 134 pieces",
        all(f >= s for f, s in zip(fs, share)),
        "%s slots vs %s needed"
        % (fs, [round(s) for s in share]))
    ogs = sum(1 for d in ds for s in floor_slots(d) if s["over_gap"])
    chk("  ...and every slot reports whether its centre is over a gap",
        True, "%d of %d slot centres sit over a board gap"
        % (ogs, sum(fs)))

    # --- the pixel budget ------------------------------------------------------
    chk("filmed-distance scale", abs(PX_PER_M - 169.6969) < 0.01,
        "%.3f px/m, 1 px = %.3f mm; hero limit %.1f mm, gate limit %.1f mm"
        % (PX_PER_M, PX_M * 1000, HERO_EDGE_M * 1000, GATE_EDGE_PX * PX_M * 1000))
    chk("the board across-sample is finer than a pixel", 0.005 < PX_M,
        "5.00 mm samples vs a %.2f mm pixel" % (PX_M * 1000))

    # --- the hash avalanches ---------------------------------------------------
    hs = [h01(91.508449, 4530, j) for j in range(24)]
    chk("the per-index hash avalanches", (max(hs) - min(hs)) > 0.85,
        "spread %.3f over 24 consecutive indices" % (max(hs) - min(hs)))

    if verbose:
        print("  ---- per-deck ----")
        for d in ds:
            r = rail(d)
            print("   %d %-8s %5.2fx%4.2f m  H=%.3f  gap=%4.1fmm  %-12s along %s"
                  "  %4d boards  %3d ped  trim=%-15s skirt=%-12s rail=%-6s"
                  "  nosing wear %s"
                  % (d.n, d.name, d.W, d.D, d.H, d.gap * 1000, d.profile,
                     d.axis, len(board_layout(d)), len(pedestal_grid(d)),
                     d.trim, d.skirt, r["kind"],
                     "/".join("%.2f" % s[3] for s in d.steps)))
    return ok[0]


def measure(prefix=PFX):
    """Measure the BUILT objects: triangles, edge percentiles in screen px."""
    deps = bpy.context.evaluated_depsgraph_get()
    objs = [o for o in bpy.context.scene.objects
            if o.type == "MESH" and o.name.startswith(prefix)]
    lens, tris = [], 0
    for ob in objs:
        oe = ob.evaluated_get(deps)
        me = oe.to_mesh()
        if me is None:
            continue
        sx, sy, sz = ob.matrix_world.to_scale()
        s = (abs(sx) + abs(sy) + abs(sz)) / 3.0
        co = np.empty(len(me.vertices) * 3)
        me.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        ev = np.empty(len(me.edges) * 2, np.int32)
        me.edges.foreach_get("vertices", ev)
        ev = ev.reshape(-1, 2)
        lens.append(np.linalg.norm(co[ev[:, 0]] - co[ev[:, 1]], axis=1) * s)
        for p in me.polygons:
            tris += max(len(p.vertices) - 2, 1)
        oe.to_mesh_clear()
    L = np.concatenate(lens)
    L.sort()
    out = dict(objects=len(objs), triangles=int(tris), edges=int(L.size),
               p10_m=float(L[len(L) // 10]), p50_m=float(L[len(L) // 2]),
               p90_m=float(L[min(len(L) * 9 // 10, L.size - 1)]))
    out["p10_px"] = out["p10_m"] * PX_PER_M
    out["p50_px"] = out["p50_m"] * PX_PER_M
    out["gate_limit_px"] = GATE_EDGE_PX
    out["hero_limit_px"] = HERO_EDGE_PX
    nimg = sum(1 for m in bpy.data.materials if m.use_nodes
               for n in m.node_tree.nodes if n.type == "TEX_IMAGE")
    ngeo = sum(1 for m in bpy.data.materials if m.use_nodes
               for n in m.node_tree.nodes if n.type == "NEW_GEOMETRY"
               and any(o.name == "Position" and o.is_linked for o in n.outputs))
    out["image_texture_nodes"] = nimg
    out["geometry_position_links"] = ngeo
    log("measured: %d objects, %d triangles, p10 %.3f mm = %.2f px "
        "(gate limit %.1f px, hero limit %.1f px), p50 %.2f mm = %.2f px"
        % (out["objects"], out["triangles"], out["p10_m"] * 1000, out["p10_px"],
           GATE_EDGE_PX, HERO_EDGE_PX, out["p50_m"] * 1000, out["p50_px"]))
    log("image texture nodes %d, Geometry->Position links %d" % (nimg, ngeo))
    return out


def interface_dump(path=None):
    """The whole public interface as JSON, for the four dependent agents."""
    out = dict(item=ITEM, generated=time.strftime("%Y-%m-%d"),
               frame="deck-local: +x width along the hospitality frontage, "
                     "+y from the paddock lane TOWARDS the unit, +z up; the "
                     "origin is ON THE GROUND at the deck's plan centre",
               laws=dict(base_embed_m=BASE_EMBED_M,
                         ground_z_source="world_contract.world_ground_z",
                         apron_z=float(C.APRON_Z)),
               dependants=["motorhome_unit", "folding_chair", "folding_table",
                           "parasol"],
               decks=[])
    for d in plan():
        out["decks"].append(dict(
            n=d.n, name=d.name, circuit_x=d.cx, circuit_y_rear=d.cy_rear,
            world_origin=[round(float(v), 4) for v in d.O],
            R=[[round(float(v), 9) for v in r] for r in d.R],
            yaw_deg=d.yaw,
            deck=dict(W=round(d.W, 4), D=round(d.D, 4), H=round(d.H, 4),
                      board_axis=d.axis, board_w=round(d.bw, 4),
                      board_t=round(d.bt, 4), gap=round(d.gap, 5),
                      profile=d.profile, species=d.species,
                      fastening=d.fasten, frame=d.frame,
                      boards=len(board_layout(d)),
                      pedestals=len(pedestal_grid(d)),
                      top_z_at_centre=round(float(deck_top_z(d, 0.0, 0.0)), 6)),
            footprint_world=[[round(float(v), 4) for v in p]
                             for p in footprint_world(d)],
            threshold=threshold(d),
            unit_bays=unit_bays(d),
            awning_anchors=awning_anchors(d),
            parasol_bases=parasol_bases(d),
            floor_slots=floor_slots(d),
            step_runs=step_runs(d),
            edge_trim=edge_trim(d),
            rail=rail(d),
            under_deck=under_deck(d)))
    if path:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        json.dump(out, open(path, "w"), indent=1)
        log("interface -> %s" % path)
    return out


# ================================================================================
# 19.  CLI
# ================================================================================

def main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", action="store_true", help="build the acceptance scene")
    ap.add_argument("--build", action="store_true", help="build the item only")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--measure", action="store_true")
    ap.add_argument("--interface", default=None)
    ap.add_argument("--lod", type=float, default=1.0)
    ap.add_argument("--which", type=int, nargs="*", default=None)
    ap.add_argument("--nocontext", action="store_true")
    ap.add_argument("--paving", default="hero",
                    choices=["hero", "draft", "none"],
                    help="context ground: the real paddock_paving_bay item "
                         "(hero/draft) or this module's own coarse grid (none)")
    ap.add_argument("--samples", type=int, default=256)
    ap.add_argument("--save", default=None)
    ap.add_argument("--render", default=None)
    ap.add_argument("--cam", default=PFX + "CAM_MACRO")
    ap.add_argument("--res", type=int, nargs=2, default=[1920, 1080])
    a = ap.parse_args(argv)

    if a.selftest and not (a.test or a.build):
        sys.exit(0 if selftest() else 1)
    if a.interface and not (a.test or a.build):
        interface_dump(a.interface)
        return
    if a.test or a.save or a.render:
        test_scene(lod=a.lod, samples=a.samples, which=a.which,
                   context=not a.nocontext, paving=a.paving)
    elif a.build:
        build(which=a.which, lod=a.lod)
    if a.selftest:
        selftest()
    if a.interface:
        interface_dump(a.interface)
    if a.measure:
        measure()
    if a.save:
        p = os.path.abspath(a.save)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        ext = [i.filepath for i in bpy.data.images if i.source == "FILE"]
        if ext:
            raise SystemExit("REFUSING TO SAVE: external images %s" % ext)
        bpy.ops.wm.save_as_mainfile(filepath=p, compress=False, relative_remap=False)
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


if __name__ == "__main__" and HAVE_BPY:
    main()
elif __name__ == "__main__":
    selftest()
