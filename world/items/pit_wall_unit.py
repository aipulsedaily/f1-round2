#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pit_wall_unit.py — CIRCUIT VITRINE, per-item hero campaign, item
``pit_wall_unit`` (zone ``pit_straight``, wave 1, build order 132,
**5 dependants, 0 dependencies**).

WHAT THIS IS, IN ONE SENTENCE
=============================
The pit wall, built as the **individual precast concrete units it is made of** —
each one a separately cast, separately bedded, separately levelled 3.0 m element
with its own length, its own seating height, its own lean, its own bug-hole
population, its own cast-in sockets and its own damage — so that what the lens
reads down the pit straight is a chain of 119 discrete castings with a step and
a joint every three metres, and not an extrusion.

THE MANIFEST NAMES THE FAILURE BEFORE IT HAPPENS
------------------------------------------------
    "375 m of wall, face pinned on circuit y=+11.500.  The step and tilt between
     units IS the object - a continuous extrusion reads as a plastic kerb from
     the onboard follow."

``build_architecture.build_pit_wall`` laid **two axis-aligned boxes per unit**
(stem + capping) with a uniform 1.20 m top plus a ±12 mm jitter and a ±4 mrad
"tilt" that was implemented as a lateral *offset*, not a rotation.  Six things
were structurally absent and no shader could have supplied any of them:

  1. **No joint.**  Adjacent boxes butted at exactly ``xe`` = ``x`` with a
     0.02 m inset each side, so the "joint" was a 40 mm flat-bottomed slot with
     two square arrises.  A real joint is a 12–28 mm gap between two *chamfered*
     ends, and the two ends are at different heights, at different leans, and
     at different lateral offsets.  At 6.2 m on a 35 mm lens that gap is 7–17 px
     of shadow **repeating every 3 m for 350 m** and it is the single most
     legible fact about the object.
  2. **The tilt was not a rotation.**  ``y0 + tilt`` translated the whole box.
     A unit that leans has its TOP displaced and its BASE fixed — that is what
     puts a visible V in the joint and a kink in the top line.  A translated box
     keeps its top line parallel to its neighbour's and reads as perfect.
  3. **Nothing was cast.**  No chamfer, no bug hole, no form-liner joint, no
     lifting socket, no ferrule, no spall, no mortar bed.  A 1.345 × 3.0 m face
     of fair-faced precast at 1.66 mm/px with zero surface events is a
     placeholder however good the shader on it is.
  4. **The base hung in the air, then hung in the ground.**  The original wall
     started at z = 0.000 over ground that runs −0.117…−0.146; the fix moved the
     base to ``ground − EMBED`` but left the wall's *top* level, so the height
     above ground varies by 30 mm along the run with no seating logic at all.
     A precast unit is a RIGID BODY on a mortar bed: it is levelled to a string
     line, and the run goes faceted, not smooth.
  5. **The west terminal stood in the Beat-4 transit lane.**  Measured, task
     #46: ``ARCH_PitWall`` reaches 1.067 m inside the car's swept volume at
     world (144.282, 29.425) = circuit (−232.05, +11.44), where telemetry row
     138 passes at 207 km/h.  See §4 below: this module starts the wall where
     the wall can actually stand and publishes the terminal's westward budget so
     ``pit_wall_terminal`` cannot rebuild the same collision.
  6. **One realisation of the concrete.**  Every unit shared one material with
     no per-object decorrelation, so whatever the shader did, it did identically
     119 times, in phase.  (This module hit the same class of bug from a
     different direction and the note is in `hash01`: without a murmur
     finaliser every per-object draw came back the same number.)

THE PIXEL BUDGET THIS WAS BUILT TO
----------------------------------
    px_per_m = (3840 x 35 / 36) / 6.2 = 602.15 px/m      ->     1 px = 1.661 mm

    the 1.200 m unit height             723 px   (manifest: onscreen_px_4k 723)
    a 3.000 m unit length              1806 px
    the 20 mm top arris chamfer          12 px      <- must be geometry
    the 20 mm end arris chamfer, x2      24 px of joint band  <- geometry
    a 12-28 mm unit-to-unit joint      7-17 px      <- must be geometry
    unit-to-unit height step, +-12 mm  <= 7 px      <- must be geometry
    lean 4 mrad over 1.345 m = 5.4 mm   3.2 px      <- must be geometry
    a 55 mm lifting-socket recess        33 px      <- must be geometry
    a 40 mm M16 ferrule countersink      24 px      <- must be geometry
    a 170 x 120 mm cable box-out      102 x 72 px   <- must be geometry
    a 10-18 mm bug hole                6-11 px      <- must be geometry
    a 30-160 mm arris spall           18-96 px      <- must be geometry
    a form-liner sheet joint, 2 mm proud  1.2 px wide, BUT at a 12.47 deg sun
                                     it throws 9.0 mm = 5.4 px of shadow
                                                            <- must be geometry
    a shrinkage crack, 0.8-3 mm       0.5-1.8 px, and it is a self-shadowing
                                     slot, so it reads     <- geometry (cheap)
    cement-paste grain, < 0.4 mm       0.24 px               <- SHADING
    form-liner ply veneer grain        < 0.15 mm             <- SHADING
    every stain, bloom, ghost and wash  no relief            <- SHADING

Everything with a silhouette or an occlusion is mesh.  The line is drawn at
0.8 mm of relief, which is half a pixel at this distance.

WHY THE LIGHT DECIDES THE MODELLING
-----------------------------------
Measured against ``world_contract``: the wall's track face normal in world is
(+0.6428, −0.7660, 0) and ``SUN_DIR`` is (0.5179, −0.8278, 0.2159).  The sun is
**7.97 deg off the face normal in azimuth and 12.47 deg above the horizon**, so
cos(incidence) = 0.967.  Two consequences that drove every modelling decision
here:

  * The track face is in near-frontal, near-grazing sun and is the BRIGHTEST
    surface in the frame.  The top of the wall sees cos = sin(12.47) = 0.216 —
    4.5x darker.  The unit-to-unit height step therefore reads as a ragged
    bright/dark boundary, which is exactly why it is the object.
  * **Vertical relief on the face casts almost no shadow** (7.97 deg of azimuth
    offset: a 3 mm proud vertical fin throws 0.4 mm sideways) while
    **horizontal relief casts 4.5x its own height downward** (3 mm throws
    13.6 mm = 8.2 px).  So the form liner is laid with its sheets HORIZONTAL,
    the lift line is horizontal, the ferrule countersinks and socket recesses
    are circular (self-shadowing at any azimuth), and the crack is the one
    deliberately vertical feature — carried by its own slot darkness, not by a
    cast shadow.

===============================================================================
THE PUBLIC INTERFACE  —  this item is a FOUNDATION.  5 items depend on it.
===============================================================================
Everything below is a pure function of the module's own deterministic plan: it
can be called WITHOUT bpy, without building anything, and it returns world-frame
geometry.  ``interface_json(path)`` dumps the lot.

    pit_wall_coping    ``coping_seat()``     -> per unit: the top track arris and
                       top pit arris as world polylines, the seat width, the
                       finished top z, the two M16 coping ferrules, and the
                       per-unit lean and height step it must follow.  THE COPING
                       LAPS OVER THIS TOP; the concrete top here is the finished
                       1.200 m and the coping adds its own 8 mm.
    pit_wall_advert    ``advert_field()``    -> per unit: the clear rectangle on
                       the track face, in world and in unit-local frame, plus
                       the M16 fixing ferrule grid.  Panels mount 50 mm proud of
                       ``FACE_PLANE_Y`` = circuit y 11.550, which lands them ON
                       the contract pin at 11.500.  ``MOUNT_BUDGET_M`` = 0.050.
    pit_wall_padding   ``padding_field()``   -> the upper 0.45 m band of the
                       track face, with the strap ferrules, for the 60 padded
                       units named in the manifest -- returned as the
                       CONTIGUOUS run in front of the garages, not 60 units
                       picked at random.
    pit_wall_terminal  ``terminal_frame()``  -> the two run-end sections in the
                       world frame AND ``TERMINAL_WEST_LIMIT_X`` = circuit
                       x −227.0, which is the measured westward budget the west
                       terminal has before it re-enters the Beat-4 car path.
                       See §4.  Ignoring it recreates task #46.
    pit_board          ``board_rest_sites()``-> 10 measured leaning stations on
                       the pit-lane face, each with the wall's actual local top
                       z, lean and face plane at that station.

    also published, not required by any dependant but true and useful:
      ``joint_sites()``   every joint with its measured gap, height step, lean
                          difference and lateral step, in the world frame.
      ``ferrule_sites()`` every cast-in socket on the item, world frame + axis.
      ``unit_records()``  the whole plan.
      ``SECTION``         the section constants as a dict.

--- 1. THE SECTION ------------------------------------------------------------

    FACE_PLANE_Y   11.550   circuit y of the nominal as-cast track face
    PIN_Y          11.500   contract pin, ``C.PIT_WALL_Y``.  NOTHING on this
                            item or its dependants crosses it: the 50 mm
                            between them is the advert/padding budget, and the
                            mortar haunch at ground level — the outermost part
                            of a bedded precast wall — reaches exactly 11.500.
    T_STEM          0.340   stem thickness
    TOP_Z           1.200   world z of the nominal top of concrete (= the
                            manifest's ``typical_height_m``, and the number
                            ``onscreen_px_4k`` 723 was derived from)
    CH_TOP          0.020   top arris chamfer (both arrises)
    CH_END          0.015   end arris chamfer
    FOOT_*                  the buried spread foot; its underside is at
                            ground − 0.235, so law 5 (embed >= 0.020) has an
                            order of magnitude of margin and no grazing ray can
                            get under the wall.

--- 2. WHERE THE UNITS ARE ----------------------------------------------------

    ``SEGMENTS``    the three runs, split by the two gaps
                    ``GAPS`` = the gantry leg at circuit x −1.9…+1.9 and the
                    pit-lane access gate at +96.0…+101.0, both inherited from
                    ``build_architecture.build_pit_wall`` so the gantry leg and
                    the gate still fit.
    ``unit_records()``  -> [{uid, seg, k, x0, x1, L, gap, dz, tilt, dyaw, dy,
                            z_ground, hv, top_z, pier, dirt, fresh, ...}] for
                            all 119.

--- 3. EMITTING ---------------------------------------------------------------

    ``build(lod_anchor=..., ...)`` emits into collection ``W_Item_PitWallUnit``
    with object prefix ``PWU_``.  **ONE OBJECT PER PRECAST UNIT** — which is
    what the manifest counts as an instance.  Nothing is instanced and no mesh
    datablock is shared; every unit's arrays are generated from its own
    parameter draw, so ``tools/mesh_reuse`` reports 0 shared datablocks.

    ``lod_anchor`` is a list of world points (the camera path).  Each unit's
    mesh density is graded by its distance to the nearest of them over four
    tiers, from a 4.5 mm chord (2.7 px at the filmed distance) down to 100 mm.

===============================================================================
 4.  THE WEST END, AND WHY IT IS NOT WHERE THE SPEC SAYS
===============================================================================
Spec §10.7 runs the pit wall over circuit x −245…+130 = 375 m, which is where
the manifest's "375 m of wall" and its 125 instances come from.  The contract
does not agree with the spec there, and this was measured, not assumed:

  * ``C.world_ground_z`` hands circuit y 11.500 to ``build_surface:SURF_Access
    Road`` for every x west of −227: the ACCESS RIBBON IS UNDER THE WALL LINE.
  * The Beat-4 transit crosses the wall line at circuit x ≈ −233.6.  Densifying
    telemetry.csv 40x and measuring the minimum distance from the driven
    centreline to the wall line as a function of where the wall starts:

        wall starts at x = −233     0.134 m   (inside the car BODY)
                          −230      1.159 m   (inside the 1.6025 m gate volume)
                          −228      1.843 m   <- build_architecture's start
                          −227      2.180 m
                          −226      2.527 m
                          −222      3.895 m   <- THIS MODULE'S START
                          −220      4.579 m

    ``build_architecture`` starts the units at −228 (clear) and then hangs a
    4.6 m tapered terminal off the west end of them, reaching −232.6 — which is
    the 1.067 m intrusion task #46 measured.  The units were never the problem;
    the terminal was, and the terminal is a separate item that cannot see this
    reasoning unless it is written down.

  So: ``WALL_X0`` = −222.0 (3.895 m from the driven centreline) and
  ``TERMINAL_WEST_LIMIT_X`` = −227.0 (2.180 m), published for
  ``pit_wall_terminal``.  That leaves the terminal 5.0 m of run — enough for the
  7 stepped lifts and the spread footing its own manifest note asks for — and
  0.58 m of clearance beyond the placement gate's car volume at the nose.

  CONSEQUENCE, STATED PLAINLY: the wall is 352 m of setting-out, 340.8 m of
  built wall after the two gaps, and **119 units, not the manifest's 125**.
  That is a real difference and it is reported rather than hidden by shortening
  the nominal unit until the arithmetic came out.  This module's ``INSTANCES_
  BUILT`` is the truth; the manifest's 125 is the truth about a wall that would
  stand in the road.

===============================================================================
THE SEVEN LAWS, AND WHERE EACH IS DISCHARGED
===============================================================================
 1. procedural, by hand   no image node, no file, no library, no font datablock
                          (the cast identification stamp is a hand-coded stroke
                          font, §``GLYPH``).  Measured by ``item_gate``:
                          ``no_external_assets``.
 2. no real brands        a precast unit carries no sponsor.  Its only lettering
                          is its own cast identification stamp, PW-nnn-24, and
                          the precaster's mark, which reuses ``NORDVAL`` from
                          build_dressing's existing brand book rather than
                          inventing a 32nd name.
 3. car scale             the 0.340 m ride height and the 2.005 m width set the
                          1.200 m top and the 50 mm mounting budget, not
                          intuition.
 4. z = 0 is one plane    never assumed: every seating z is
                          ``C.world_ground_z(x, y)`` sampled over the unit's own
                          footprint, and the returned owner string is checked.
 5. embed >= 20 mm        the buried spread foot's underside is 0.235 m below
                          the local ground over the unit's whole footprint.
 6. recentre + TexCoord   every unit's mesh is local to its own centroid in a
                          canonical frame (+X along the wall, +Y toward the pit
                          lane, +Z up), |P| < 1.75 m.  The material reads
                          ``TexCoord->Object`` plus 11 baked vertex attributes
                          and 7 per-OBJECT properties.  ``Geometry->Position``
                          appears nowhere.
 7. chunk along s         one unit is <= 3.0 m of circuit.

===============================================================================
WHAT VARIES BETWEEN INSTANCES, AND WHY IT IS GEOMETRY
===============================================================================
The manifest names five axes.  All five are in the MESH, or in the placement of
a rigid body, never in a random rotation of one shared mesh:

 "3.0 m units, every 5th short"  the yard's delivery rhythm: 4 x 3.000 m then
                                 1 x 2.400 m, continuous across both gaps, plus
                                 a site-cut closer at the end of each of the
                                 three segments.  Every casting is short of
                                 nominal by |N(0, 5 mm)| clipped at 16 mm, and
                                 THAT SHORTFALL IS THE JOINT GAP.  The mesh is
                                 regenerated at the drawn length, so vertex
                                 counts differ unit to unit and the gate's
                                 ``distinct_topologies`` is in the hundreds.
 "+/-12 mm height"               each unit is levelled to a string line to
                                 N(0, 7 mm) clipped at +-12 mm about z = 1.200.
                                 The step at a joint is the difference of two
                                 independent draws: sd 9.9 mm, and 4.0 % of
                                 joints step more than 20 mm = 12 px.
 "+/-0.004 rad tilt"             a ROTATION about the unit's own long axis,
                                 applied to the object matrix, so the base stays
                                 on the setting-out line and the TOP moves
                                 +-5.4 mm.  Two neighbours leaning opposite ways
                                 open an 11 mm V at the top of the joint.
 "joint step"                    falls out of the three above plus a lateral
                                 setting error N(0, 3 mm) and a yaw error
                                 N(0, 1.1 mrad) — over a 3 m unit the far end is
                                 up to 6 mm off the line, which is why a real
                                 wall's face is a polyline and not a plane.
 "base staining"                 the capillary-rise band, the splash zone, the
                                 grit line and the wash below every socket and
                                 joint.  SHADING, on a per-unit wetness draw and
                                 the baked ``pw_h``/``pw_flow`` attributes —
                                 but the mortar haunch it stains is geometry.

Nine more the manifest does not name and the object needs, all per-unit and all
in the mesh:

 bug-hole population             18-120 meshed voids >= 10 mm dia, drawn
                                 against a per-unit compaction quality; the
                                 sub-10 mm population is bump.
 form-liner sheet layout         a 1.220 m horizontal sheet joint at a per-unit
                                 phase, 2.440 m vertical butts, per-joint step
                                 and grout-fin height, and the ply's bow between
                                 0.60 m bearers.
 lifting sockets                 2 per unit, 55 mm x 40 mm deep; 65 % dry-packed
                                 with a paler mortar plug set 4 mm low, 35 %
                                 left open — a black 33 px disc with a rust
                                 wash under it.
 M16 fixing ferrules             2 rows x 2-3 columns; each one independently
                                 open / bolted (a 30 mm hex head 12 mm proud) /
                                 mortar-plugged.
 cable box-out                   170 x 120 mm cast-in penetration on 11 units,
                                 with a bolted galvanised cover plate.
 arris spalls                    0-4 per unit, 30-160 mm long, 4-22 mm deep,
                                 with a rough fracture face and a sharp arris
                                 where it meets the intact casting; 3 units
                                 carry a spall deep enough to show a corroded
                                 12 mm bar.
 honeycombing                    0-1 patch of under-vibrated concrete near the
                                 base, 80-300 mm, 4-14 mm deep, exposed
                                 aggregate.
 shrinkage cracks                0-2 per unit, from a socket or a ferrule to the
                                 base, 0.8-3 mm wide, 3-8 mm deep.
 end pier                        the 6 units that terminate a segment are cast
                                 100 mm thicker over their last 0.6 m on the pit
                                 side, which is how a run is closed.
 cast identification stamp       a 0.200 x 0.070 m recessed plate carrying the
                                 unit's OWN number in a hand-coded stroke font.
                                 121 different strings = 121 different meshes.

Run headless:

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P world/items/pit_wall_unit.py -- --test \
        --save world/items/pit_wall_unit_test.blend

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P world/items/pit_wall_unit.py -- --selftest
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

ITEM = "pit_wall_unit"

# WORLD ASSEMBLY MUST DELETE THIS FIRST.  `build_architecture.build_pit_wall`
# emits one object, `ARCH_PitWall`, that contains the old two-boxes-per-unit
# wall over the SAME line.  This module replaces those boxes; it does NOT
# replace the gantry-leg return walls, the advertising panels, or the five
# pit-wall stands, which are still build_architecture's and still in that
# object.  Assembly has to split it or rebuild it -- shipping both puts two
# walls 30 mm apart on circuit y 11.5 and z-fights 350 m of hero surface.
SUPERSEDES = ("ARCH_PitWall",)
SUPERSEDES_NOTE = (
    "ARCH_PitWall's `while x < 130.0` unit loop and its tapered west terminal. "
    "Its return walls, advert panels and 5 timing stands are separate items "
    "(pit_wall_advert, timing_stand) and are NOT superseded by this module.")

COLL = "W_Item_PitWallUnit"
PFX = "PWU_"
XPFX = "PWUX_"          # test-scene stand-ins owned by OTHER items.  "PWUX_"
                        # does NOT start with "PWU_"... it does.  See _gate_safe
                        # below: stand-ins are named "XPW_" for exactly that
                        # reason.
XPFX = "XPW_"

_T0 = time.time()


def log(msg):
    print("[%s %7.1fs] %s" % (ITEM, time.time() - _T0, msg))
    sys.stdout.flush()


# ==============================================================================
#  0.  THE NUMBERS
# ==============================================================================
# Manifest record, quoted so nothing downstream has to re-read the JSON.
FILMED_AT_M = 6.2
LENS_MM = 35.0
ONSCREEN_PX_4K = 723.0
INSTANCES_DECLARED = 125
PX_PER_M = (3840.0 * LENS_MM / 36.0) / FILMED_AT_M           # 602.15
PX_M = 1.0 / PX_PER_M                                        # 1.661 mm

# --- the plan, in the circuit design frame -----------------------------------
PIN_Y = C.PIT_WALL_Y                    # 11.500, the contract's barrier face
MOUNT_BUDGET_M = 0.050                  # advert / padding thickness budget
FACE_PLANE_Y = PIN_Y + MOUNT_BUDGET_M   # 11.550, the nominal as-cast face
T_STEM = 0.340
TOP_Z = 1.200                           # world z of the nominal top of concrete

WALL_X0 = -222.0                        # see §4 of the docstring: MEASURED
WALL_X1 = 130.0
TERMINAL_WEST_LIMIT_X = -227.0          # pit_wall_terminal's westward budget
GAPS = (
    (-1.9, 1.9, "gantry leg, circuit y +11.0 (build_architecture)"),
    (96.0, 101.0, "pit-lane access gate (build_architecture)"),
)

# --- the section -------------------------------------------------------------
CH_TOP = 0.020                          # top arris chamfer, both arrises
CH_END = 0.020                          # end arris chamfer.  MEASURED against
                                        # the light: the two chamfers plus the
                                        # gap make the joint a 55 mm tonal band
                                        # = 33 px, where the gap alone is 9 px
FOOT_OUT_TRACK = 0.042                  # spread foot projection, track side --
                                        # kept inside MOUNT_BUDGET_M so that not
                                        # even the BURIED part of this item is
                                        # proud of the contract pin
FOOT_OUT_PIT = 0.130                    # ... and pit side
FOOT_COVER = 0.075                      # burial of the top of the foot
FOOT_D = 0.160                          # foot depth
BED_TOP = 0.010                         # mortar bed top, above local ground
HAUNCH_H = 0.045                        # trowelled haunch height on the face
HAUNCH_OUT = 0.038                      # nominal; the trowelled squeeze-out on
                                        # top of it is what reaches the pin
SQUEEZE_OUT = 0.035                     # raw squeeze-out on the pit side
EMBED = C.BASE_EMBED_M                  # 0.020, and we use 0.235

# --- the yard's delivery rhythm ----------------------------------------------
L_LONG = 3.000
L_SHORT = 2.400
SHORT_EVERY = 5                         # every 5th unit is a short one
GAP_BASE = 0.012                        # the fitter's nominal joint
SHORTFALL_SD = 0.005                    # casting length shortfall (never long)
SHORTFALL_CLIP = 0.016
CLOSER_MIN = 0.70                       # a site-cut closer can be short; what it
                                        # may NOT do is make a unit over 3.0 m

# --- per-unit setting tolerances (manifest) ----------------------------------
STEP_SD = 0.0070                        # manifest: +/-12 mm height
STEP_CLIP = 0.0120
TILT_SD = 0.0022                        # manifest: +/-0.004 rad
TILT_CLIP = 0.0040
YAW_SD = 0.0011
YAW_CLIP = 0.0020
LATERAL_SD = 0.0030
LATERAL_CLIP = 0.0050

# --- LOD ---------------------------------------------------------------------
# (station dx, track-face dz, chamfer dz, top dy, pit-face dz, buried d).
# LOD 0 is 4.5 mm on the face = 2.7 px at the filmed distance.
LOD = (
    (0.0030, 0.0030, 0.0030, 0.0050, 0.0200, 0.055),   # 0  hero, <= 10 m
    (0.0110, 0.0100, 0.0060, 0.0130, 0.0320, 0.075),   # 1  <= 38 m
    (0.0340, 0.0280, 0.0180, 0.0330, 0.0700, 0.110),   # 2  <= 130 m
    (0.0950, 0.0780, 0.0480, 0.0900, 0.1500, 0.200),   # 3  beyond
)
LOD_RADII = (10.0, 38.0, 130.0)
MESH_DETAIL_LOD = 1                     # bug holes / spalls / stamp exist up to
                                        # this LOD; beyond it they are sub-pixel


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

    THE FINALISER IS NOT DECORATION.  Without it this returned the LOW 30 bits
    of an FNV hash, and FNV's multiply only propagates change upward -- so
    hash01(seed, 3), hash01(seed, 5) and hash01(seed, 7) all came back 0.33955
    for the same unit.  Measured on the built blend: every per-object property
    on every unit was the same number, which is one degree of freedom pretending
    to be seven.  Verified by `selftest` step [9].
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

    def clipn(self, sd, clip):
        return float(np.clip(self.r.normal(0.0, sd), -clip, clip))

    def i(self, a, b):
        return int(self.r.integers(a, b + 1))

    def pick(self, seq):
        return seq[int(self.r.integers(0, len(seq)))]

    def arr(self, n):
        return self.r.random(n)


def _h2(ix, iy, seed):
    with np.errstate(over="ignore"):
        h = (np.asarray(ix, np.uint32) * np.uint32(374761393)
             + np.asarray(iy, np.uint32) * np.uint32(668265263)
             + np.uint32(int(seed) & 0xFFFFFFFF) * np.uint32(2246822519))
        h = h ^ (h >> np.uint32(13))
        h = h * np.uint32(1274126177)
        h = h ^ (h >> np.uint32(16))
    return h.astype(np.float64) / 4294967295.0


def _sstep(t):
    return t * t * (3.0 - 2.0 * t)


def vnoise2(x, y, seed=0):
    x = np.asarray(x, float); y = np.asarray(y, float)
    ix = np.floor(x).astype(np.int64); iy = np.floor(y).astype(np.int64)
    fx = _sstep(x - ix); fy = _sstep(y - iy)
    a = _h2(ix, iy, seed); b = _h2(ix + 1, iy, seed)
    c = _h2(ix, iy + 1, seed); d = _h2(ix + 1, iy + 1, seed)
    return (a * (1 - fx) * (1 - fy) + b * fx * (1 - fy)
            + c * (1 - fx) * fy + d * fx * fy)


def fbm2(x, y, seed=0, oct=4, lac=2.07, gain=0.5):
    s = np.zeros(np.broadcast(np.asarray(x), np.asarray(y)).shape)
    a, f, norm = 1.0, 1.0, 0.0
    for i in range(oct):
        s = s + a * vnoise2(np.asarray(x) * f, np.asarray(y) * f, seed + i * 71)
        norm += a
        a *= gain; f *= lac
    return s / norm


def vnoise1(x, seed=0):
    x = np.asarray(x, float)
    ix = np.floor(x).astype(np.int64)
    fx = _sstep(x - ix)
    a = _h2(ix, np.zeros_like(ix), seed)
    b = _h2(ix + 1, np.zeros_like(ix), seed)
    return a * (1 - fx) + b * fx


def fbm1(x, seed=0, oct=4, lac=2.03, gain=0.5):
    s = np.zeros(np.asarray(x).shape)
    a, f, norm = 1.0, 1.0, 0.0
    for i in range(oct):
        s = s + a * vnoise1(np.asarray(x) * f, seed + i * 37)
        norm += a
        a *= gain; f *= lac
    return s / norm


def clamp01(a):
    return np.clip(a, 0.0, 1.0)


def smoothstep(e0, e1, x):
    t = clamp01((np.asarray(x, float) - e0) / max(e1 - e0, 1e-12))
    return t * t * (3.0 - 2.0 * t)


# ==============================================================================
#  2.  A HAND-CODED STROKE FONT
# ==============================================================================
# Blender ships a font datablock and `build_architecture` uses it, which is
# legal.  This module does not, for one reason: a font is a THIRD PARTY ASSET
# even when it is bundled, and the brief says everything is built by hand.  A
# cast identification stamp is 8 characters of 40 mm capitals; a stroke table is
# 30 lines and settles the question.
#
# Coordinates are in a 0..1 (x) by 0..1 (y) box; each glyph is a list of
# polylines.  Stroke width and cap height are applied at rasterisation time.
GLYPH = {
    "0": [[(.1, .1), (.9, .1), (.9, .9), (.1, .9), (.1, .1)], [(.1, .1), (.9, .9)]],
    "1": [[(.25, .72), (.5, .9), (.5, .1)], [(.2, .1), (.8, .1)]],
    "2": [[(.1, .75), (.3, .9), (.7, .9), (.9, .72), (.9, .58), (.1, .1), (.9, .1)]],
    "3": [[(.1, .9), (.9, .9), (.45, .53), (.9, .45), (.9, .2), (.7, .1), (.25, .1), (.1, .22)]],
    "4": [[(.72, .1), (.72, .9), (.1, .3), (.95, .3)]],
    "5": [[(.9, .9), (.15, .9), (.12, .5), (.6, .55), (.9, .42), (.9, .2), (.7, .1), (.2, .1)]],
    "6": [[(.85, .85), (.5, .9), (.15, .7), (.1, .28), (.3, .1), (.7, .1), (.9, .28), (.75, .48), (.3, .52), (.12, .38)]],
    "7": [[(.1, .9), (.9, .9), (.4, .1)]],
    "8": [[(.5, .52), (.2, .62), (.2, .82), (.4, .9), (.6, .9), (.8, .82), (.8, .62), (.5, .52), (.18, .38), (.15, .2), (.35, .1), (.65, .1), (.85, .2), (.82, .38), (.5, .52)]],
    "9": [[(.15, .18), (.5, .12), (.85, .32), (.9, .72), (.7, .9), (.3, .9), (.1, .72), (.25, .52), (.7, .5), (.88, .62)]],
    "-": [[(.15, .5), (.85, .5)]],
    "/": [[(.15, .05), (.85, .95)]],
    ".": [[(.45, .1), (.55, .1)]],
    "A": [[(.08, .1), (.5, .9), (.92, .1)], [(.24, .42), (.76, .42)]],
    "B": [[(.15, .1), (.15, .9), (.65, .9), (.85, .74), (.65, .52), (.15, .52)], [(.65, .52), (.88, .32), (.68, .1), (.15, .1)]],
    "C": [[(.9, .8), (.65, .9), (.3, .88), (.12, .62), (.12, .34), (.3, .12), (.65, .1), (.9, .2)]],
    "D": [[(.15, .1), (.15, .9), (.6, .9), (.85, .68), (.85, .32), (.6, .1), (.15, .1)]],
    "E": [[(.88, .9), (.15, .9), (.15, .1), (.88, .1)], [(.15, .5), (.7, .5)]],
    "I": [[(.5, .1), (.5, .9)], [(.22, .9), (.78, .9)], [(.22, .1), (.78, .1)]],
    "L": [[(.18, .9), (.18, .1), (.88, .1)]],
    "M": [[(.1, .1), (.1, .9), (.5, .42), (.9, .9), (.9, .1)]],
    "N": [[(.15, .1), (.15, .9), (.85, .1), (.85, .9)]],
    "O": [[(.12, .32), (.3, .9), (.7, .9), (.88, .32), (.7, .1), (.3, .1), (.12, .32)]],
    "P": [[(.15, .1), (.15, .9), (.68, .9), (.88, .74), (.68, .52), (.15, .52)]],
    "R": [[(.15, .1), (.15, .9), (.68, .9), (.88, .74), (.68, .54), (.15, .54)], [(.5, .54), (.9, .1)]],
    "S": [[(.9, .8), (.6, .9), (.25, .88), (.14, .68), (.35, .52), (.7, .48), (.88, .32), (.75, .14), (.4, .1), (.1, .2)]],
    "T": [[(.08, .9), (.92, .9)], [(.5, .9), (.5, .1)]],
    "V": [[(.08, .9), (.5, .1), (.92, .9)]],
    "W": [[(.05, .9), (.28, .1), (.5, .62), (.72, .1), (.95, .9)]],
    " ": [],
}
GLYPH_ADV = 0.72            # advance width, in cap-height units


def stroke_segments(text, h, gap=0.10):
    """-> (segments (n,2,2), width) for `text` at cap height `h`, origin at the
    lower-left of the first glyph.  Pure geometry, no datablocks."""
    segs = []
    x = 0.0
    for ch in text.upper():
        g = GLYPH.get(ch)
        if g is None:
            g = GLYPH[" "]
        for pl in g:
            for i in range(len(pl) - 1):
                a = (x + pl[i][0] * h * GLYPH_ADV / 0.9, pl[i][1] * h)
                b = (x + pl[i + 1][0] * h * GLYPH_ADV / 0.9, pl[i + 1][1] * h)
                segs.append((a, b))
        x += h * (GLYPH_ADV + gap)
    if not segs:
        return np.zeros((0, 2, 2)), 0.0
    return np.asarray(segs, float), x - h * gap


def seg_distance(px, pz, segs):
    """Distance from each (px,pz) to the nearest of `segs`.  Vectorised."""
    if len(segs) == 0:
        return np.full(np.shape(px), 1e9)
    best = np.full(np.shape(px), 1e9)
    for (ax, az), (bx, bz) in segs:
        dx, dz = bx - ax, bz - az
        L2 = dx * dx + dz * dz
        if L2 < 1e-14:
            d = np.hypot(px - ax, pz - az)
        else:
            t = np.clip(((px - ax) * dx + (pz - az) * dz) / L2, 0.0, 1.0)
            d = np.hypot(px - (ax + t * dx), pz - (az + t * dz))
        best = np.minimum(best, d)
    return best


# ==============================================================================
#  3.  THE SECTION
# ==============================================================================
# Local frame, per unit:
#     +X  along the wall, toward increasing circuit x.  0 at mid-length.
#     +Y  toward the pit lane.  0 at the nominal as-cast track face
#         (= circuit y FACE_PLANE_Y = 11.550).
#     +Z  up.  0 at the unit's OWN top of concrete.
# The mesh is recentred on its centroid before it is handed to Blender, and the
# object matrix carries the placement.  |P| < 1.75 m everywhere.

# region ids, baked into `pw_face`
R_BURIED, R_BED, R_PIT, R_CHAM, R_TOP, R_TRACK, R_HAUNCH = 0, 1, 2, 3, 4, 5, 6

SECTION = dict(
    pin_y=PIN_Y, face_plane_y=FACE_PLANE_Y, mount_budget_m=MOUNT_BUDGET_M,
    t_stem=T_STEM, top_z=TOP_Z, ch_top=CH_TOP, ch_end=CH_END,
    foot_out_track=FOOT_OUT_TRACK, foot_out_pit=FOOT_OUT_PIT,
    foot_cover=FOOT_COVER, foot_d=FOOT_D, bed_top=BED_TOP,
    haunch_h=HAUNCH_H, haunch_out=HAUNCH_OUT, squeeze_out=SQUEEZE_OUT,
)


def section_nodes(hv):
    """The corner nodes of the section, for a unit whose top of concrete stands
    `hv` metres above its own local ground line.  Counter-clockwise in (y, z),
    so the outward normal of the segment A->B is (dz, -dy) normalised."""
    zg = -hv                                  # local ground line
    zbed = zg + BED_TOP                       # top of the mortar bed
    zft = zg - FOOT_COVER                     # top of the spread foot
    zfb = zft - FOOT_D                        # underside of the foot
    yfl = -FOOT_OUT_TRACK
    yfh = T_STEM + FOOT_OUT_PIT
    return [
        # (y, z, region of the segment that STARTS here)
        (yfl, zfb, R_BURIED),                          # A  bottom
        (yfh, zfb, R_BURIED),                          # B  foot, pit face
        (yfh, zft, R_BURIED),                          # C  foot top, pit side
        (T_STEM + SQUEEZE_OUT, zft, R_BED),            # D  bed, pit face
        (T_STEM + SQUEEZE_OUT, zbed - 0.010, R_BED),   # E  bed shoulder
        (T_STEM, zbed + 0.014, R_PIT),                 # F  into the stem
        (T_STEM, -CH_TOP, R_CHAM),                     # G  pit face top
        (T_STEM - CH_TOP, 0.0, R_TOP),                 # H  top, pit arris
        (CH_TOP, 0.0, R_CHAM),                         # I  top, track arris
        (0.0, -CH_TOP, R_TRACK),                       # J  face top
        (0.0, zbed + HAUNCH_H, R_HAUNCH),              # K  face, haunch start
        (-HAUNCH_OUT, zbed - 0.004, R_BED),            # L  haunch toe
        (-HAUNCH_OUT, zft, R_BURIED),                  # M  bed, track face
        (yfl, zft, R_BURIED),                          # N  foot top, track side
    ]


def _region_pitch(region, lod):
    dx, dtrack, dcham, dtop, dpit, dburied = LOD[lod]
    return {R_BURIED: dburied, R_BED: min(dtop, 0.010), R_PIT: dpit,
            R_CHAM: dcham, R_TOP: dtop, R_TRACK: dtrack,
            R_HAUNCH: min(dtop, 0.008)}[region]


def section_loop(hv, lod, force_z=()):
    """Densified section.

    -> P (n,2) in (y,z), NRM (n,2) outward, REG (n,) region id, ARC (n,)
       arclength from node A, EDG (n,) distance to the nearest corner.

    `force_z` are z values that MUST appear as vertices on the track face and
    the pit face (the cable box-out's rim); forcing them keeps the box-out an
    exact rectangle in index space instead of a staircase.
    """
    nodes = section_nodes(hv)
    P, REG = [], []
    n = len(nodes)
    for i in range(n):
        y0, z0, reg = nodes[i]
        y1, z1, _ = nodes[(i + 1) % n]
        seg = math.hypot(y1 - y0, z1 - z0)
        pitch = _region_pitch(reg, lod)
        k = max(int(math.ceil(seg / pitch)), 1)
        ts = [j / float(k) for j in range(k)]
        # snap any forced z onto this segment
        if force_z and abs(z1 - z0) > 1e-9 and reg in (R_TRACK, R_PIT):
            for zf in force_z:
                t = (zf - z0) / (z1 - z0)
                if 1e-6 < t < 1.0 - 1e-6:
                    ts.append(t)
            ts = sorted(set(round(t, 9) for t in ts))
        for t in ts:
            P.append((y0 + (y1 - y0) * t, z0 + (z1 - z0) * t))
            REG.append(reg)
    P = np.asarray(P, float)
    REG = np.asarray(REG, np.int32)
    m = len(P)
    nxt = np.roll(P, -1, axis=0)
    prv = np.roll(P, 1, axis=0)
    d1 = nxt - P
    d0 = P - prv
    def _nm(d):
        v = np.stack([d[:, 1], -d[:, 0]], 1)
        return v / (np.linalg.norm(v, axis=1, keepdims=True) + 1e-12)
    NRM = _nm(d0) + _nm(d1)
    NRM = NRM / (np.linalg.norm(NRM, axis=1, keepdims=True) + 1e-12)
    seglen = np.linalg.norm(d1, axis=1)
    ARC = np.concatenate([[0.0], np.cumsum(seglen)[:-1]])
    # distance to the nearest CORNER (a real arris), along the loop
    corner = np.zeros(m, bool)
    acc = 0.0
    ci = []
    for i in range(len(nodes)):
        y0, z0, _ = nodes[i]
        j = int(np.argmin(np.hypot(P[:, 0] - y0, P[:, 1] - z0)))
        ci.append(j)
    corner[ci] = True
    total = float(ARC[-1] + seglen[-1])
    ca = ARC[corner]
    dd = np.abs(ARC[:, None] - ca[None, :])
    dd = np.minimum(dd, total - dd)
    EDG = dd.min(axis=1)
    return P, NRM, REG, ARC, EDG


# ==============================================================================
#  4.  WHERE THE UNITS ARE
# ==============================================================================

def _segments():
    edges = [WALL_X0]
    for g0, g1, _why in GAPS:
        edges += [g0, g1]
    edges.append(WALL_X1)
    return [(edges[i], edges[i + 1]) for i in range(0, len(edges), 2)]


SEGMENTS = _segments()

_UNITS = None


def unit_records():
    """The whole plan.  Pure, deterministic, and callable without bpy."""
    global _UNITS
    if _UNITS is not None:
        return _UNITS
    out = []
    uid = 0
    k = 0                                   # the yard's continuous delivery index
    for si, (xa, xb) in enumerate(SEGMENTS):
        x = xa
        pend = []
        while True:
            rg = Rng(9101, uid, si)
            L_nom = L_SHORT if (k % SHORT_EVERY) == (SHORT_EVERY - 1) else L_LONG
            short = float(np.clip(abs(rg.n(0.0, SHORTFALL_SD)), 0.0, SHORTFALL_CLIP))
            L = L_nom - short
            gap = GAP_BASE + short + rg.clipn(0.0030, 0.0060)
            gap = max(gap, 0.005)
            rem = xb - x
            if rem < L + 1e-9:
                # the closer: whatever is left, site-cut.  If the leftover is
                # too short to be a casting the run simply STOPS short of the
                # gap -- which is what happens on site.  It never lengthens the
                # previous unit, because a 3.18 m element does not exist: the
                # mould is 3.000 m.
                if rem >= CLOSER_MIN:
                    L = rem - 0.010
                    gap = 0.010
                    pend.append((x, L, gap, True))
                break
            pend.append((x, L, gap, False))
            x += L + gap
            k += 1
        for (x0, L, gap, closer) in pend:
            rg = Rng(7717, uid)
            xm = x0 + 0.5 * L
            u = dict(
                uid=uid, seg=si, k=k, x0=x0, x1=x0 + L, xm=xm, L=L, gap=gap,
                closer=bool(closer),
                dz=rg.clipn(STEP_SD, STEP_CLIP),
                tilt=rg.clipn(TILT_SD, TILT_CLIP),
                dyaw=rg.clipn(YAW_SD, YAW_CLIP),
                dy=rg.clipn(LATERAL_SD, LATERAL_CLIP),
                seed=rg.seed,
                age=float(np.clip(0.30 + 0.55 * hash01(rg.seed, 3), 0.0, 1.0)),
                wet=float(hash01(rg.seed, 5)),
                batch=float(hash01(rg.seed, 7)),
                compaction=float(np.clip(rg.n(0.55, 0.20), 0.05, 0.98)),
                pier=0,
                # how filthy THIS unit is.  A 350 m wall is not uniformly
                # weathered: it is sheltered in places, splashed in others, and
                # a few units have been knocked out and replaced.
                dirt=float(np.clip(rg.n(0.55, 0.26), 0.02, 1.0)),
                fresh=float(hash01(rg.seed, 23) < 0.045),
            )
            out.append(u)
            uid += 1
    # end piers: the units that terminate a segment, both ends
    for si in range(len(SEGMENTS)):
        seg = [u for u in out if u["seg"] == si]
        if not seg:
            continue
        seg[0]["pier"] = -1
        seg[-1]["pier"] = +1 if seg[-1] is not seg[0] else -1

    # --- seating.  NEVER an assumed z: C.world_ground_z over the footprint ---
    for u in out:
        xs = np.linspace(u["x0"], u["x1"], 7)
        ys = np.array([PIN_Y - 0.02, FACE_PLANE_Y, FACE_PLANE_Y + T_STEM * 0.5,
                       FACE_PLANE_Y + T_STEM])
        XX, YY = np.meshgrid(xs, ys, indexing="ij")
        wx, wy = C.circuit_to_world(XX.ravel(), YY.ravel())
        z, own = C.world_ground_z(wx, wy)
        z = np.asarray(z, float)
        good = np.isfinite(z)
        if not good.any():
            raise SystemExit(
                "REFUSING: world_ground_z returns NaN over unit %d's whole "
                "footprint (circuit x %.2f..%.2f). The wall would be standing "
                "on terrain nobody has declared." % (u["uid"], u["x0"], u["x1"]))
        u["z_ground"] = float(np.mean(z[good]))
        u["z_ground_min"] = float(np.min(z[good]))
        u["ground_owner"] = sorted(set(str(o) for o in np.asarray(own).ravel()[good]))
        u["top_z"] = TOP_Z + u["dz"]
        u["hv"] = u["top_z"] - u["z_ground"]
        u["z_bot"] = u["z_ground"] - FOOT_COVER - FOOT_D
        u["embed"] = u["z_ground_min"] - u["z_bot"]
    _UNITS = out
    return out


INSTANCES_BUILT = None                      # filled by unit_records() on demand


def wall_axes():
    """(ex, ey, ez) of the wall's own frame in the WORLD, as float arrays."""
    o = np.array(C.circuit_to_world(0.0, 0.0), float)
    ex = np.array(C.circuit_to_world(1.0, 0.0), float) - o
    ey = np.array(C.circuit_to_world(0.0, 1.0), float) - o
    ex = np.append(ex, 0.0)[:3] if ex.shape[0] == 3 else np.array([ex[0], ex[1], 0.0])
    ey = np.array([ey[0], ey[1], 0.0])
    ex = ex / np.linalg.norm(ex)
    ey = ey / np.linalg.norm(ey)
    return ex, ey, np.array([0.0, 0.0, 1.0])


EX, EY, EZ = wall_axes()


def unit_basis(u):
    """(origin_at_local_zero, ex, ey, ez) in the WORLD for one unit.

    The local origin is (x = mid-length, y = the nominal cast face, z = the
    unit's own top of concrete).  Yaw and lean are applied as ROTATIONS about
    that frame's own axes, which is the whole point: a leaning unit's base stays
    on the setting-out line and its top moves.
    """
    cy = math.cos(u["dyaw"]); sy = math.sin(u["dyaw"])
    ex = EX * cy + EY * sy
    ey = -EX * sy + EY * cy
    ct = math.cos(u["tilt"]); st = math.sin(u["tilt"])
    ey2 = ey * ct + EZ * st
    ez2 = -ey * st + EZ * ct
    wx, wy = C.circuit_to_world(u["xm"], FACE_PLANE_Y + u["dy"])
    org = np.array([float(wx), float(wy), u["top_z"]])
    return org, ex, ey2, ez2


def to_world(u, pts):
    """(n,3) local -> (n,3) world."""
    org, ex, ey, ez = unit_basis(u)
    p = np.asarray(pts, float).reshape(-1, 3)
    return org[None, :] + p[:, 0:1] * ex + p[:, 1:2] * ey + p[:, 2:3] * ez


# ==============================================================================
#  5.  THE HISTORY OF ONE CASTING
# ==============================================================================

def unit_features(u):
    """Everything that happened to this unit, drawn once and cached."""
    if "_feat" in u:
        return u["_feat"]
    rg = Rng(u["seed"], 4242)
    L, hv = u["L"], u["hv"]
    zg = -hv
    ztop_face = -CH_TOP
    zbot_face = zg + BED_TOP + HAUNCH_H
    Hface = ztop_face - zbot_face

    f = {}
    # --- form liner ---------------------------------------------------------
    # THE LIGHT DECIDED THIS.  The first version made the sheet joint a PROUD
    # FIN, reasoning from the 12.47 deg sun elevation that it would throw 4.5x
    # its height in shadow.  That is true of a horizontal GROUND plane and false
    # here: measured, the sun is 14.7 deg off this face's NORMAL, so anything on
    # it throws only tan(14.7) = 0.26x its height.  A 1 mm fin casts 0.26 mm of
    # shadow -- 0.16 px -- and the first render duly showed a blank sheet.
    #
    # What reads at 14.7 deg incidence is not shadow, it is LAMBERT FALLOFF on
    # steep faces: a surface tilted 60 deg from the face plane is cos(74.7) /
    # cos(14.7) = 3.7x darker.  So the joint is a V-GROOVE with 50-65 deg walls,
    # which gives a dark line and a bright line 4 mm apart, and every recess on
    # this item was re-cut on the same principle.
    f["ply_z"] = [zbot_face + rg.u(0.28, 0.64) * Hface]
    f["ply_step"] = [rg.clipn(0.0009, 0.0022)]
    f["ply_groove_w"] = rg.u(0.0030, 0.0065)
    f["ply_groove_d"] = rg.u(0.0016, 0.0034)
    f["ply_fin"] = [max(0.0, rg.n(0.0011, 0.0009))]
    f["ply_x"] = [(-L * 0.5 + rg.u(0.15, 0.85) * 2.440) % max(L, 0.1) - L * 0.5]
    f["ply_bow"] = rg.u(0.00025, 0.00085)
    f["bearer"] = rg.u(0.55, 0.68)

    # --- lifting sockets (top face) ----------------------------------------
    xs = [-0.30 * L, 0.30 * L]
    f["socket"] = [dict(x=x + rg.clipn(0.008, 0.02), r=0.0300, d=0.048,
                        packed=(rg.u() < 0.62), plug_low=rg.u(0.003, 0.008))
                   for x in xs]

    # --- M16 ferrules on the track face ------------------------------------
    # 45 mm countersink, 12 mm deep: a 22 deg cone whose upper wall runs 68 deg
    # off the face plane, i.e. 2.6x darker than the face beside it.  That, and
    # not the hole, is what makes a ferrule read at 6.2 m.
    ncol = 3 if L > 2.7 else 2
    rows = [zbot_face + 0.22 * Hface, zbot_face + 0.74 * Hface]
    fer = []
    for ri, zr in enumerate(rows):
        for ci in range(ncol):
            xx = -L * 0.5 + L * (ci + 0.5) / ncol + rg.clipn(0.006, 0.018)
            state = rg.u()
            fer.append(dict(x=xx, z=zr + rg.clipn(0.004, 0.012), r_c=0.0225,
                            d_c=0.012, r_h=0.011, d_h=0.030,
                            state=("bolt" if state < 0.28 else
                                   ("plug" if state < 0.60 else "open")),
                            row=ri))
    f["ferrule"] = fer
    # coping ferrules, on the TOP
    f["coping_ferrule"] = [dict(x=x, r_c=0.018, d_c=0.008, r_h=0.009, d_h=0.032)
                           for x in (-0.62 * L * 0.5, 0.62 * L * 0.5)]

    # --- bug holes ----------------------------------------------------------
    # Compaction quality decides the population; air rises, so the density
    # climbs with height on the face.  Depth is 0.60-0.95 of the radius, which
    # is what an entrapped air void actually is -- the first version used
    # 0.35-0.75 and 10-18 mm, giving 0.35 % surface coverage of shallow dishes
    # that were invisible at 14.7 deg incidence.  These are 8-34 mm across with
    # a near-vertical rim, and only those >= 8 mm are meshed: the smaller
    # population is the same distribution carried in the bump, because 6 mm is
    # 3.6 px and has no silhouette.
    q = u["compaction"]
    n = int(np.clip(70 + 420 * (1.0 - q), 70, 460) * (L / 3.0))
    hx = (rg.arr(n) - 0.5) * (L - 0.05)
    tt = rg.arr(n) ** 0.50                     # biased toward the top
    hz = zbot_face + 0.015 + tt * (Hface - 0.04)
    hr = 0.0040 + 0.0130 * rg.arr(n) ** 2.6    # 8-34 mm diameter
    hd = hr * (0.60 + 0.35 * rg.arr(n))
    # clusters: bug holes are not Poisson, they gang up where the vibrator
    # missed.  Three or four sites per unit get a local swarm.
    for _ in range(rg.i(2, 5)):
        cx = rg.u(-L * 0.5 + 0.1, L * 0.5 - 0.1)
        cz = zbot_face + rg.u(0.25, 0.95) * Hface
        m = rg.i(8, 26)
        ang = rg.arr(m) * 2 * math.pi
        rad = rg.arr(m) ** 0.6 * rg.u(0.05, 0.16)
        hx = np.concatenate([hx, cx + rad * np.cos(ang)])
        hz = np.concatenate([hz, cz + rad * np.sin(ang) * 0.7])
        r2 = 0.0045 + 0.0125 * rg.arr(m) ** 2.0
        hr = np.concatenate([hr, r2])
        hd = np.concatenate([hd, r2 * (0.65 + 0.32 * rg.arr(m))])
    keep = ((np.abs(hx) < L * 0.5 - 0.03)
            & (hz > zbot_face + 0.01) & (hz < ztop_face - 0.01))
    f["bug"] = (hx[keep], hz[keep], hr[keep], hd[keep])

    # --- a made-good repair patch ------------------------------------------
    # Somebody bagged and rubbed a defect before the unit left the yard.  It is
    # a different colour, a different roughness and 1-2 mm proud with a soft
    # edge -- and it is the single clearest sign that a wall has a history.
    f["patch"] = None
    if rg.u() < 0.40:
        f["patch"] = dict(x=rg.u(-L * 0.5 + 0.2, L * 0.5 - 0.2),
                          z=zbot_face + rg.u(0.10, 0.90) * Hface,
                          rx=rg.u(0.07, 0.26), rz=rg.u(0.05, 0.17),
                          d=rg.u(0.0008, 0.0022))

    # --- the cast identification stamp -------------------------------------
    f["stamp"] = dict(
        text="PW-%03d-24" % (u["uid"] + 1),
        x=-L * 0.5 + 0.235, z=zbot_face + 0.075,
        w=0.200, h=0.070, cap=0.038, stroke=0.0055,
        recess=0.005, raise_=0.003)
    f["mark"] = dict(text="NORDVAL", x=-L * 0.5 + 0.235,
                     z=zbot_face + 0.030, cap=0.020, stroke=0.0035,
                     recess=0.0035, raise_=0.0022)

    # --- cable box-out ------------------------------------------------------
    f["boxout"] = None
    if rg.u() < 0.09 and u["L"] > 2.6:
        bz = zbot_face + 0.16
        f["boxout"] = dict(x0=-0.085, x1=0.085, z0=bz, z1=bz + 0.120,
                           cover=True, plate_pad=0.035, plate_t=0.004)

    # --- arris spalls -------------------------------------------------------
    # A spall reads because its fracture face is steep, not because it is deep.
    # 12-45 mm of bite with a sharp lip turns a 60-90 deg surface toward the
    # camera, which at this incidence is 3-8x darker than the face beside it.
    nsp = rg.i(1, 6)
    sp = []
    for i in range(nsp):
        sp.append(dict(x=rg.u(-L * 0.5 + 0.06, L * 0.5 - 0.06),
                       ln=rg.u(0.045, 0.210), dp=rg.u(0.012, 0.045),
                       drop=rg.u(0.020, 0.090),
                       rebar=(rg.u() < 0.12)))
    f["spall"] = sp
    # and the ones that are NOT on the arris: a trolley wheel, a dropped jack
    f["knock"] = [dict(x=rg.u(-L * 0.5 + 0.15, L * 0.5 - 0.15),
                       z=zbot_face + (rg.u(0.02, 0.30) if rg.u() < 0.55
                                      else rg.u(0.30, 0.80)) * Hface,
                       rx=rg.u(0.022, 0.095), rz=rg.u(0.015, 0.062),
                       d=rg.u(0.006, 0.026))
                  for _ in range(rg.i(1, 6))]

    # --- honeycombing -------------------------------------------------------
    f["honey"] = None
    if rg.u() < 0.32:
        f["honey"] = dict(x=rg.u(-L * 0.5 + 0.15, L * 0.5 - 0.15),
                          z=zbot_face + rg.u(0.02, 0.22),
                          rx=rg.u(0.05, 0.19), rz=rg.u(0.035, 0.11),
                          d=rg.u(0.008, 0.024))

    # --- shrinkage cracks ---------------------------------------------------
    ncr = 0 if rg.u() < 0.45 else rg.i(1, 2)
    cr = []
    for i in range(ncr):
        src = rg.pick(fer) if fer else None
        x0 = src["x"] if src else rg.u(-L * 0.4, L * 0.4)
        z0 = src["z"] if src else ztop_face - 0.1
        pts = [(x0, z0)]
        z = z0
        while z > zbot_face + 0.02:
            z -= rg.u(0.05, 0.14)
            pts.append((pts[-1][0] + rg.n(0.0, 0.020), max(z, zbot_face)))
        cr.append(dict(pts=np.asarray(pts, float),
                       w=rg.u(0.0008, 0.0030), d=rg.u(0.003, 0.008)))
    f["crack"] = cr

    # --- last season's advert, as a ghost (SHADING, no relief) --------------
    f["ghost"] = dict(x0=-L * 0.5 + rg.u(0.04, 0.30),
                      x1=L * 0.5 - rg.u(0.04, 0.30),
                      z0=zbot_face + rg.u(0.05, 0.20),
                      z1=ztop_face - rg.u(0.11, 0.32),
                      on=(rg.u() < 0.66))

    # --- the mortar bed's squeeze-out --------------------------------------
    f["bed_seed"] = rg.seed % 100000
    u["_feat"] = f
    return f


# ==============================================================================
#  6.  THE MESH
# ==============================================================================

def _stations(u, lod):
    """Station list along the unit, with forced stations at every feature edge
    so a 170 mm box-out is 170 mm and not 165 or 175."""
    L = u["L"]
    dx = LOD[lod][0]
    n = max(int(math.ceil(L / dx)), 3)
    xs = list(np.linspace(-L * 0.5, L * 0.5, n + 1))
    if lod <= MESH_DETAIL_LOD:
        f = unit_features(u)
        forced = []
        if f["boxout"]:
            b = f["boxout"]
            forced += [b["x0"], b["x1"]]
        for s in f["socket"]:
            forced += [s["x"] - s["r"], s["x"] + s["r"]]
        st = f["stamp"]
        forced += [st["x"] - 0.006, st["x"] + st["w"] + 0.006]
        xs += [x for x in forced if -L * 0.5 < x < L * 0.5]
    xs = np.unique(np.round(np.asarray(xs, float), 6))
    return xs


def _face_height(u, X, Z, lod):
    """The track face's height field.

    SIGN CONVENTION, and it is the one bug this file was written twice to fix:
    the returned displacement is ALONG THE SECTION'S OUTWARD NORMAL.  Positive
    is PROUD (toward the track), negative is RECESSED (into the wall).  Every
    hole, socket, spall and stamp is therefore negative and every fin, plug and
    bolt head is positive.  Getting this backwards turns 120 bug holes into 120
    warts and is invisible in every check except the render.

    X, Z are arrays of local coordinates on the face.  The result is clamped so
    the proudest point of the as-cast face stays 4 mm behind the contract pin:
    the advert panels own the 50 mm in front of it.
    """
    f = unit_features(u)
    d = np.zeros(np.shape(X))
    sd = f["bed_seed"]

    # 1. casting-bed deflection: the face is very slightly dished
    d += 0.0008 * (fbm2(X * 0.55 + 3.1, Z * 0.55 - 1.7, sd + 11, 3) - 0.5) * 2.0

    # 2. the form liner: a horizontal sheet joint, cut as a V-GROOVE with a
    #    grout fin on its lower lip and a step across it.  The groove is what
    #    reads: 5 mm wide and 2.5 mm deep gives walls at 45-60 deg, so one lip
    #    goes 3x darker than the face and the other goes brighter, 5 mm apart.
    gw, gd = f["ply_groove_w"], f["ply_groove_d"]
    for zj, stp, fin in zip(f["ply_z"], f["ply_step"], f["ply_fin"]):
        wob = zj + 0.0025 * (fbm1(X * 1.7 + 4.0, sd + 19, 3) - 0.5) * 2.0
        t = np.clip(1.0 - np.abs(Z - wob) / gw, 0.0, 1.0)
        along = 0.35 + 1.2 * fbm1(X * 2.3 + 7.0, sd + 21, 3)
        d -= gd * t * along                        # the groove
        d += fin * np.exp(-((Z - wob + gw) / (gw * 0.55)) ** 2) * along
        d += stp * smoothstep(-gw, gw, Z - wob)    # ... and the sheets step
    for xj in f["ply_x"]:                          # vertical butt joint
        w = 0.0030
        t = np.exp(-((X - xj) / w) ** 2)
        d -= 0.7 * gd * t

    # 3. the ply bows out between its bearers, so the face is proud there
    d += f["ply_bow"] * (0.5 - 0.5 * np.cos(2 * math.pi * X / f["bearer"]))

    # 4. bug holes: spherical caps, RECESSED
    if lod <= MESH_DETAIL_LOD:
        hx, hz, hr, hd = f["bug"]
        for i in range(len(hx)):
            r = hr[i]
            dx = X - hx[i]; dz = Z - hz[i]
            rr = dx * dx + dz * dz
            m = rr < r * r
            if not np.any(m):
                continue
            d = np.where(m, d - hd[i] * np.sqrt(np.maximum(r * r - rr, 0.0)) / r, d)

    # 5. the M16 ferrules: a countersink, then either an open bore, a mortar
    #    plug, or a bolt still in it
    for fe in f["ferrule"]:
        dx = X - fe["x"]; dz = Z - fe["z"]
        rr = np.hypot(dx, dz)
        cs = fe["d_c"] * clamp01((fe["r_c"] - rr) / max(fe["r_c"] - fe["r_h"], 1e-6))
        d -= np.where(rr < fe["r_c"], cs, 0.0)
        if fe["state"] == "open":
            d -= np.where(rr < fe["r_h"], fe["d_h"] - fe["d_c"], 0.0)
        elif fe["state"] == "plug":
            d -= np.where(rr < fe["r_h"], 0.002, 0.0)
        else:                                       # a bolt still in it
            d += np.where(rr < 0.014, 0.012, 0.0)

    # 6. the cast identification stamp and the precaster's mark: a recessed
    #    plate with RAISED characters, which is how steel type in a mould works
    if lod <= MESH_DETAIL_LOD:
        for key in ("stamp", "mark"):
            g = f[key]
            segs, w = stroke_segments(g["text"], g["cap"], 0.10)
            pad = 0.010
            box = ((X > g["x"] - pad) & (X < g["x"] + w + pad)
                   & (Z > g["z"] - pad) & (Z < g["z"] + g["cap"] + pad))
            if not np.any(box):
                continue
            d = np.where(box, d - g["recess"], d)
            dd = seg_distance(X - g["x"], Z - g["z"], segs)
            d = np.where(box & (dd < g["stroke"] * 0.5),
                         d + g["raise_"], d)

    # 7. arris spalls reach down the face from the top.  The profile is a HARD
    #    lip (power 4 in the along direction) and a rough floor: a spall does
    #    not taper away, it stops at a fracture.
    for sp in f["spall"]:
        dx = np.abs(X - sp["x"]) / max(sp["ln"] * 0.5, 1e-6)
        edge = 0.82 + 0.30 * fbm1(X * 34.0 + sp["x"] * 11.0, sd + 41, 3)
        m = (dx < edge) & (Z > -CH_TOP - sp["drop"])
        prof = np.clip(1.0 - (np.minimum(dx / np.maximum(edge, 1e-6), 1.0)) ** 4.0,
                       0.0, 1.0)
        vert = np.clip((Z + CH_TOP + sp["drop"]) / max(sp["drop"], 1e-6), 0.0, 1.0)
        rough = 0.62 + 0.72 * fbm2(X * 55.0, Z * 55.0, sd + 33, 4)
        d -= np.where(m, sp["dp"] * prof * vert * rough, 0.0)

    # 7b. knocks that are not on the arris: a trolley wheel, a dropped jack
    for kn in f["knock"]:
        e = ((X - kn["x"]) / kn["rx"]) ** 2 + ((Z - kn["z"]) / kn["rz"]) ** 2
        w = 0.85 + 0.35 * fbm2(X * 26.0, Z * 26.0, sd + 43, 3)
        m = e < w
        rough = 0.65 + 0.70 * fbm2(X * 70.0 + 9.0, Z * 70.0, sd + 45, 4)
        d -= np.where(m, kn["d"] * np.clip(1.0 - (e / np.maximum(w, 1e-6)) ** 3.0,
                                           0.0, 1.0) * rough, 0.0)

    # 8. honeycombing: under-vibrated concrete, open and rough
    h = f["honey"]
    if h is not None:
        e = ((X - h["x"]) / h["rx"]) ** 2 + ((Z - h["z"]) / h["rz"]) ** 2
        m = e < 1.0
        rough = fbm2(X * 90.0 + 5.0, Z * 90.0 - 2.0, sd + 51, 4)
        r2 = fbm2(X * 260.0 - 3.0, Z * 260.0 + 6.0, sd + 53, 3)
        d -= np.where(m, h["d"] * np.maximum(1.0 - e, 0.0) ** 0.5
                      * (0.30 + 1.0 * rough + 0.55 * r2), 0.0)

    # 8b. the made-good repair patch: bagged, rubbed, and 1-2 mm proud
    pt = f["patch"]
    if pt is not None:
        e = ((X - pt["x"]) / pt["rx"]) ** 2 + ((Z - pt["z"]) / pt["rz"]) ** 2
        w = 0.80 + 0.45 * fbm2(X * 9.0 + 2.0, Z * 9.0 - 5.0, sd + 55, 3)
        d += pt["d"] * np.clip(1.0 - e / np.maximum(w, 1e-6), 0.0, 1.0) ** 0.7

    # 9. shrinkage cracks: a self-shadowing slot, sub-pixel wide and visible
    for cr in f["crack"]:
        segs = np.stack([cr["pts"][:-1], cr["pts"][1:]], 1)
        dd = seg_distance(X, Z, segs)
        d -= cr["d"] * np.exp(-(dd / max(cr["w"], 1e-4)) ** 2)

    # 10. the cable box-out's bolted cover plate stands PROUD of the face; the
    #     box-out itself is a deep recess in the ring around it
    b = f["boxout"]
    if b is not None and lod <= MESH_DETAIL_LOD:
        mb = ((X > b["x0"]) & (X < b["x1"]) & (Z > b["z0"]) & (Z < b["z1"]))
        d = np.where(mb, -0.055, d)
        m = ((X > b["x0"] - b["plate_pad"]) & (X < b["x1"] + b["plate_pad"])
             & (Z > b["z0"] - b["plate_pad"]) & (Z < b["z1"] + b["plate_pad"]))
        d = np.where(m, b["plate_t"], d)
        for bx in (b["x0"] - 0.022, b["x1"] + 0.022):
            for bz in (b["z0"] - 0.022, b["z1"] + 0.022):
                rr = np.hypot(X - bx, Z - bz)
                d = np.where(rr < 0.011, b["plate_t"] + 0.007, d)

    return np.clip(d, -0.070, MOUNT_BUDGET_M - 0.004)


def _pit_height(u, X, Z, lod):
    """The pit face: the up-face of a face-down cast, so it is FLOATED, not
    formed.  Wavy at 0.3-1.0 m, screed drag at 20-60 mm, no bug holes.
    Displacement is along the outward normal, +y."""
    f = unit_features(u)
    sd = f["bed_seed"]
    d = np.zeros(np.shape(X))
    d += 0.0025 * (fbm2(X * 1.4 + 11.0, Z * 1.4 + 4.0, sd + 61, 4) - 0.5) * 2.0
    d += 0.0009 * (fbm2(X * 9.0 - 3.0, Z * 3.0 + 8.0, sd + 71, 3) - 0.5) * 2.0
    # the end pier: the run-terminating units are cast 100 mm thicker
    if u["pier"]:
        L = u["L"]
        xe = -L * 0.5 if u["pier"] < 0 else L * 0.5
        t = smoothstep(0.60, 0.52, np.abs(X - xe))
        d += 0.100 * t
    b = f["boxout"]
    if b is not None and lod <= MESH_DETAIL_LOD:
        m = ((X > b["x0"]) & (X < b["x1"]) & (Z > b["z0"]) & (Z < b["z1"]))
        d = np.where(m, -0.050, d)              # a blanked cable gland plate
    return d


def _top_height(u, XX, YY, lod):
    """The top of the wall: the coping seat.  A 2 % fall to the pit side, the
    lifting sockets, the coping ferrules, and the cast rim around each socket.
    Displacement is along the outward normal, +z."""
    f = unit_features(u)
    sd = f["bed_seed"]
    d = np.zeros(np.shape(XX))
    d -= (YY / T_STEM) * 0.006                          # 2 % fall, pit-ward
    d += 0.0009 * (fbm2(XX * 3.0 + 21.0, YY * 3.0, sd + 81, 3) - 0.5) * 2.0
    if lod <= MESH_DETAIL_LOD:
        for s in f["socket"]:
            rr = np.hypot(XX - s["x"], YY - T_STEM * 0.5)
            if s["packed"]:
                d -= np.where(rr < s["r"], s["plug_low"], 0.0)
            else:
                d -= np.where(rr < s["r"], s["d"], 0.0)
            # the cast rim the lifting eye was screwed against
            d += np.where((rr >= s["r"]) & (rr < s["r"] + 0.008), 0.0015, 0.0)
        for cf in f["coping_ferrule"]:
            rr = np.hypot(XX - cf["x"], YY - T_STEM * 0.62)
            cs = cf["d_c"] * clamp01((cf["r_c"] - rr) / max(cf["r_c"] - cf["r_h"], 1e-6))
            d -= np.where(rr < cf["r_c"], cs, 0.0)
            d -= np.where(rr < cf["r_h"], cf["d_h"] - cf["d_c"], 0.0)
    return d


def _bed_out(u, X, Zs, region):
    """The mortar bed / haunch: an irregular outward swelling at the base."""
    f = unit_features(u)
    sd = f["bed_seed"]
    w = fbm1(X * 3.1 + 2.0, sd + 91, 4)
    return w


def unit_mesh_arrays(u, lod=0):
    """-> V (n,3) local & recentred, QUADS (m,4), TRIS (k,3), ATTR dict,
          CENTROID (3,), INFO dict.

    One swept section plus two chamfered, tessellated end caps.  Everything
    that varies between units is IN HERE, not in a transform.
    """
    hv = u["hv"]
    f = unit_features(u)
    force_z = []
    if f["boxout"] and lod <= MESH_DETAIL_LOD:
        force_z = [f["boxout"]["z0"], f["boxout"]["z1"]]
    P, NRM, REG, ARC, EDG = section_loop(hv, lod, force_z)
    xs = _stations(u, lod)
    nx, npn = len(xs), len(P)

    X = np.repeat(xs[:, None], npn, axis=1)
    Y0 = np.repeat(P[None, :, 0], nx, axis=0)
    Z0 = np.repeat(P[None, :, 1], nx, axis=0)
    NY = np.repeat(NRM[None, :, 0], nx, axis=0)
    NZ = np.repeat(NRM[None, :, 1], nx, axis=0)
    RG = np.repeat(REG[None, :], nx, axis=0)

    disp = np.zeros((nx, npn))

    # --- track face ---------------------------------------------------------
    m = RG == R_TRACK
    if np.any(m):
        disp[m] = _face_height(u, X[m], Z0[m], lod)
    # --- the two chamfers get the face's field, softened, so a spall crosses
    #     the arris instead of stopping at it
    m = RG == R_CHAM
    if np.any(m):
        near_track = Y0[m] < T_STEM * 0.5
        dch = np.zeros(np.count_nonzero(m))
        if np.any(near_track):
            dch[near_track] = _face_height(u, X[m][near_track],
                                           Z0[m][near_track] - 0.004, lod) * 0.75
        # chip the arris.  A CHIP IS A BITE OUT OF THE CONCRETE: the 5x
        # pixel-peep of v1 showed a row of pale blisters standing PROUD of the
        # top arris, which is this term with the wrong sign.
        # A CHIP IS AN IMPACT, not a texture.  The first version thresholded a
        # 45 mm-period fbm and produced a scalloped arris all the way along,
        # which the 58 mm pixel-peep showed immediately.  Two octaves: a sparse
        # low-frequency selector picks WHERE, a high-frequency one shapes the
        # fracture.
        sel = fbm1(X[m] * 3.4 + 3.0, f["bed_seed"] + 101, 3)
        shp = fbm1(X[m] * 46.0 - 5.0, f["bed_seed"] + 103, 4)
        where = np.clip((sel - 0.615) / 0.075, 0.0, 1.0)
        bite = where * np.clip((shp - 0.30) / 0.45, 0.0, 1.0) ** 0.7
        disp[m] = dch - 0.020 * bite
    # --- top ---------------------------------------------------------------
    m = RG == R_TOP
    if np.any(m):
        disp[m] = _top_height(u, X[m], Y0[m], lod)
    # --- pit face ----------------------------------------------------------
    m = RG == R_PIT
    if np.any(m):
        disp[m] = _pit_height(u, X[m], Z0[m], lod)
    # --- mortar bed and haunch: an irregular outward swelling, PROUD --------
    for reg in (R_BED, R_HAUNCH):
        m = RG == reg
        if np.any(m):
            w = _bed_out(u, X[m], Z0[m], reg)
            w2 = fbm1(X[m] * 11.0 + 5.0, f["bed_seed"] + 121, 4)
            if reg == R_BED:
                pit = Y0[m] > T_STEM * 0.5
                # raw squeeze-out on the back, a struck-off face on the front
                d = np.where(pit, 0.004 + SQUEEZE_OUT * (0.35 * w + 0.55 * w2),
                             0.001 + 0.011 * w + 0.006 * w2)
            else:
                # the trowelled haunch: a fillet a person made with a float, so
                # it bulges and starves along its length by +-6 mm
                d = 0.0005 + 0.009 * w + 0.007 * w2
            disp[m] = d
    # --- buried: leave nominal, it is never seen and it is the embed ---------

    YY = Y0 + NY * disp
    ZZ = Z0 + NZ * disp
    # HARD GUARD: nothing on this item may cross the contract pin.
    YY = np.maximum(YY, -MOUNT_BUDGET_M)

    V = np.stack([X.ravel(), YY.ravel(), ZZ.ravel()], 1)

    # --- quads --------------------------------------------------------------
    idx = np.arange(nx * npn).reshape(nx, npn)
    nxtp = np.roll(idx, -1, axis=1)
    Q = np.stack([idx[:-1, :].ravel(), nxtp[:-1, :].ravel(),
                  nxtp[1:, :].ravel(), idx[1:, :].ravel()], 1)

    # --- end caps -----------------------------------------------------------
    tris = []
    quads = [Q]
    Vlist = [V]
    base = nx * npn
    for end, sgn in ((0, -1.0), (nx - 1, +1.0)):
        ring = np.stack([np.full(npn, xs[end]), YY[end], ZZ[end]], 1)
        inw = np.stack([np.zeros(npn), -NRM[:, 0], -NRM[:, 1]], 1)
        inset = ring + inw * CH_END
        inset[:, 0] = xs[end] + sgn * -CH_END * 0.0 - sgn * CH_END
        # the chamfer strip
        i0 = base
        Vlist.append(ring * 0 + ring)      # (re-emit the ring so the cap has
        base += npn                        #  its own hard normals)
        i1 = base
        Vlist.append(inset)
        base += npn
        r0 = np.arange(npn) + i0
        r1 = np.arange(npn) + i1
        n0 = np.roll(r0, -1); n1 = np.roll(r1, -1)
        if sgn > 0:
            quads.append(np.stack([r0, n0, n1, r1], 1))
        else:
            quads.append(np.stack([r0, r1, n1, n0], 1))
        # fill the inset ring
        try:
            from mathutils.geometry import tessellate_polygon
            from mathutils import Vector as _V
            poly = [_V((float(p[1]), float(p[2]), 0.0)) for p in inset]
            tri = tessellate_polygon([poly])
        except Exception:
            tri = [(0, i, i + 1) for i in range(1, npn - 1)]
        tri = np.asarray(tri, np.int64) + i1
        if sgn < 0:
            tri = tri[:, ::-1]
        tris.append(tri)

    V = np.concatenate(Vlist, 0)
    QUADS = np.concatenate([q for q in quads if len(q)], 0)
    TRIS = np.concatenate(tris, 0) if tris else np.zeros((0, 3), np.int64)

    # --- attributes ---------------------------------------------------------
    zgl = -hv
    REGflat = np.concatenate([RG.ravel(),
                              REG, REG, REG, REG])       # 2 caps x 2 rings
    Xf = V[:, 0]; Yf = V[:, 1]; Zf = V[:, 2]
    A = {}
    A["pw_h"] = (Zf - zgl).astype(np.float32)            # height above ground
    A["pw_d"] = (-Zf).astype(np.float32)                 # depth BELOW the top,
                                                         # which is what the rain
                                                         # wash is a function of
    A["pw_track"] = ((REGflat == R_TRACK)
                     | ((REGflat == R_CHAM) & (Yf < T_STEM * 0.5))).astype(np.float32)
    A["pw_top"] = (REGflat == R_TOP).astype(np.float32)
    A["pw_pit"] = (REGflat == R_PIT).astype(np.float32)
    A["pw_mortar"] = ((REGflat == R_BED)
                      | (REGflat == R_HAUNCH)).astype(np.float32)

    # arris proximity, for edge wear and lime bloom
    EDGflat = np.concatenate([np.repeat(EDG[None, :], nx, 0).ravel(),
                              EDG, EDG, EDG, EDG])
    endw = np.minimum(np.abs(Xf - (-u["L"] * 0.5)), np.abs(Xf - u["L"] * 0.5))
    A["pw_edge"] = np.minimum(EDGflat, endw).astype(np.float32)

    # how deeply recessed a point is BELOW ITS OWN NOMINAL SURFACE, in metres.
    # This is the displacement itself, negated, so it is correct on the top
    # (where the recess is in z) as well as on the two faces (where it is in y).
    # It drives every dirt collection, every dry-pack plug and the darkening
    # inside every socket, hole and box-out.
    A["pw_recess"] = np.clip(
        np.concatenate([-disp.ravel(), -disp[0], -disp[0], -disp[-1], -disp[-1]]),
        -0.02, 0.10).astype(np.float32)

    # fracture surfaces: spalls, knocks, honeycomb, chipped arrises.  These are
    # where the cast SKIN is gone and the aggregate is showing, which is the
    # only place aggregate may show: a fair-faced unit's skin is closed.
    brk = np.zeros(len(Xf), np.float32)
    for sp in f["spall"]:
        m = (np.abs(Xf - sp["x"]) < sp["ln"] * 0.58) & (Zf > -CH_TOP - sp["drop"] * 1.1)
        brk[m] = 1.0
    for kn in f["knock"]:
        m = (((Xf - kn["x"]) / (kn["rx"] * 1.10)) ** 2
             + ((Zf - kn["z"]) / (kn["rz"] * 1.10)) ** 2) < 1.0
        brk[m] = np.maximum(brk[m], 0.95)
    if f["honey"] is not None:
        h = f["honey"]
        m = (((Xf - h["x"]) / (h["rx"] * 1.05)) ** 2
             + ((Zf - h["z"]) / (h["rz"] * 1.05)) ** 2) < 1.0
        brk[m] = np.maximum(brk[m], 0.85)
    A["pw_break"] = brk

    # the made-good repair patch: different cement, different roughness
    pat = np.zeros(len(Xf), np.float32)
    pt = f["patch"]
    if pt is not None:
        e = (((Xf - pt["x"]) / pt["rx"]) ** 2 + ((Zf - pt["z"]) / pt["rz"]) ** 2)
        pat = np.clip(1.6 - 1.6 * e, 0.0, 1.0).astype(np.float32)
        pat *= (A["pw_track"] > 0.5)
    A["pw_patch"] = pat

    # steel: bolt heads, cover plate, open ferrule bores
    stl = np.zeros(len(Xf), np.float32)
    for fe in f["ferrule"]:
        if fe["state"] == "bolt":
            m = (np.hypot(Xf - fe["x"], Zf - fe["z"]) < 0.015) & (A["pw_track"] > 0.5)
            stl[m] = 1.0
    if f["boxout"] is not None:
        b = f["boxout"]
        m = ((Xf > b["x0"] - b["plate_pad"] - 0.001)
             & (Xf < b["x1"] + b["plate_pad"] + 0.001)
             & (Zf > b["z0"] - b["plate_pad"] - 0.001)
             & (Zf < b["z1"] + b["plate_pad"] + 0.001) & (A["pw_track"] > 0.5))
        stl[m] = 1.0
    A["pw_steel"] = stl

    # the ghost of last season's advert
    g = f["ghost"]
    gh = np.zeros(len(Xf), np.float32)
    if g["on"]:
        m = ((Xf > g["x0"]) & (Xf < g["x1"]) & (Zf > g["z0"]) & (Zf < g["z1"])
             & (A["pw_track"] > 0.5))
        gh[m] = 1.0
    A["pw_ghost"] = gh

    # POINT SOURCES of running water, and only point sources.  The general
    # rain wash off the top arris is a shader field -- it has no per-vertex
    # geometry behind it and baking it would quantise it to the mesh.  What
    # IS baked is where a socket, a ferrule or a joint concentrates the flow,
    # because those are at known places on the mesh.  The first version made
    # these 70 mm wide with a hard edge and they read as painted stripes; they
    # are now 24-44 mm, soft, and they FADE DOWNWARD from their source.
    flow = np.zeros(len(Xf), np.float32)
    trk = A["pw_track"] > 0.5

    def _plume(x0, z0, w, reach, amp):
        dx = np.abs(Xf - x0)
        dzv = z0 - Zf
        lat = np.clip(1.0 - (dx / w) ** 2, 0.0, 1.0)
        ver = np.clip(1.0 - dzv / reach, 0.0, 1.0) * (dzv > -0.010)
        return amp * lat * ver * trk

    for s in f["socket"]:
        flow = np.maximum(flow, _plume(s["x"], 0.0, 0.030,
                                       0.85 if not s["packed"] else 0.35,
                                       0.95 if not s["packed"] else 0.45))
    for fe in f["ferrule"]:
        flow = np.maximum(flow, _plume(fe["x"], fe["z"], 0.022,
                                       0.55 if fe["state"] == "open" else 0.22,
                                       0.85 if fe["state"] == "open" else 0.35))
    # the joints: the whole end of the unit sheds water down the chamfer
    flow = np.maximum(flow, np.clip(1.0 - (endw / 0.045) ** 2, 0.0, 1.0) * 0.60 * trk)
    A["pw_flow"] = flow.astype(np.float32)

    # --- recentre -----------------------------------------------------------
    lo = V.min(axis=0); hi = V.max(axis=0)
    ctr = 0.5 * (lo + hi)
    V = V - ctr[None, :]

    info = dict(nx=nx, np=npn, verts=len(V), quads=len(QUADS), tris=len(TRIS),
                maxP=float(np.abs(V).max()), zbot=float(lo[2]), ztop=float(hi[2]))
    return V, QUADS, TRIS, A, ctr, info


ATTRS = ("pw_h", "pw_d", "pw_track", "pw_top", "pw_pit", "pw_mortar",
         "pw_edge", "pw_recess", "pw_break", "pw_patch", "pw_steel",
         "pw_ghost", "pw_flow")


# ==============================================================================
#  7.  BLENDER
# ==============================================================================

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
    """Smooth everywhere except across a real arris.

    A cast face carries continuous curvature (bed deflection, ply bow, the
    shoulders of every bug hole); flat-shading it turns a 4.5 mm grid into
    visible facets at 2.7 px.  The chamfers, the ends, every fracture face and
    the box-out are genuinely sharp.  numpy against `sharp_edge`, because
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


def _object_props(ob, u, lod, info):
    sd = u["seed"]
    # per-object texture offset: the only thing that stops 119 units sharing one
    # realisation of the concrete.  24 m, not 240 -- Cycles evaluates procedurals
    # in float32 and a large offset costs lattice precision.
    ob["pw_ofs_x"] = float(hash01(sd, 3) * 24.0)
    ob["pw_ofs_y"] = float(hash01(sd, 5) * 24.0)
    ob["pw_ofs_z"] = float(hash01(sd, 7) * 24.0)
    ob["pw_age"] = float(u["age"])
    ob["pw_wet"] = float(u["wet"])
    ob["pw_batch"] = float(u["batch"])
    ob["pw_val"] = float(hash01(sd, 11))
    ob["pw_dirt"] = float(u["dirt"] * (0.12 if u["fresh"] else 1.0))
    ob["pw_fresh"] = float(u["fresh"])
    ob["item"] = ITEM
    ob["pw_uid"] = int(u["uid"])
    ob["pw_seg"] = int(u["seg"])
    ob["pw_len"] = float(u["L"])
    ob["pw_gap"] = float(u["gap"])
    ob["pw_dz"] = float(u["dz"])
    ob["pw_tilt"] = float(u["tilt"])
    ob["pw_lod"] = int(lod)
    ob["pw_closer"] = int(u["closer"])
    ob["pw_pier"] = int(u["pier"])
    ob["pw_x0"] = float(u["x0"])
    ob["pw_verts"] = int(info["verts"])


def build_unit(u, coll, mat, lod=0):
    from mathutils import Matrix
    V, Q, T, A, ctr, info = unit_mesh_arrays(u, lod)
    name = "%sU%03d" % (PFX, u["uid"])
    me = _new_mesh(name, V, Q, T)
    _bake(me, A)
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    org, ex, ey, ez = unit_basis(u)
    org = org + ex * ctr[0] + ey * ctr[1] + ez * ctr[2]
    M = Matrix(((ex[0], ey[0], ez[0], org[0]),
                (ex[1], ey[1], ez[1], org[1]),
                (ex[2], ey[2], ez[2], org[2]),
                (0.0, 0.0, 0.0, 1.0)))
    ob.matrix_world = M
    coll.objects.link(ob)
    _object_props(ob, u, lod, info)
    return ob, len(Q) * 2 + len(T)


# ==============================================================================
#  8.  THE MATERIAL
# ==============================================================================

class NT(object):
    """Node DSL.  Same shape as kerb_precast_unit's, so the two read alike."""

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


# Linear reflectances.  Precast concrete is DARKER than intuition: a fair-faced
# unit two seasons out of the mould measures 0.22-0.30 diffuse, not the 0.55
# that "pale grey" suggests.  Calibrated against C.lambert_radiance, under a
# 0.967 cos-incidence key -- this face is the brightest thing in the frame and
# it will clip if it is painted the colour it looks like.
PAL = dict(
    # LINEAR reflectances, and they are LOWER than "pale grey concrete" wants
    # to be.  MEASURED FROM THE RENDER, not assumed: at 0.20 albedo and
    # cos(incidence) 0.967 this face lands at 0.86 scene-linear after the
    # contract's -3.048 EV, which is 2.25 stops above AgX middle grey and deep
    # into the shoulder -- a 30 % reflectance change came out as 0.07 sRGB and
    # seventeen layers of weathering rendered as one flat cream sheet.  An
    # under-exposed test frame at -5.6 EV showed every layer present and
    # correct.  So the fix was not more layers, it was putting the surface
    # where the transform still has contrast: a pit wall four seasons old
    # beside a racing line, carrying brake dust, measures 0.13-0.19.
    conc_pale=(0.1880, 0.1850, 0.1760),     # laitance still on the mould face
    conc_mid=(0.1270, 0.1235, 0.1155),      # weathered cast face
    conc_dark=(0.0700, 0.0672, 0.0622),     # shaded, damp, dirty
    conc_warm=(0.1470, 0.1375, 0.1200),     # a warmer cement batch
    conc_cool=(0.1350, 0.1365, 0.1350),     # a cooler, greyer batch
    conc_new=(0.2180, 0.2150, 0.2080),      # a casting that went in last month
    fracture=(0.2280, 0.2210, 0.2060),      # a fresh break: bright and matt
    agg_dark=(0.0480, 0.0470, 0.0450),      # basalt coarse aggregate
    agg_pale=(0.1920, 0.1870, 0.1740),      # limestone / quartzite
    agg_red=(0.0880, 0.0490, 0.0345),       # the odd ferruginous stone
    mortar=(0.1280, 0.1230, 0.1135),        # bedding mortar
    drypack=(0.1790, 0.1730, 0.1610),       # the socket plug: newer, paler
    repair=(0.1480, 0.1420, 0.1300),        # a bagged-and-rubbed made-good
    lime=(0.3300, 0.3260, 0.3180),          # efflorescence bloom
    rust=(0.0680, 0.0255, 0.0110),          # corroded bar, and its wash
    grit=(0.0920, 0.0815, 0.0640),          # trapped sand and brake dust
    wash=(0.0520, 0.0498, 0.0462),          # the rain-borne dirt that runs
                                            # down a wall: warm, dark, and NOT
                                            # the same thing as shadow
    damp=(0.0650, 0.0628, 0.0600),          # capillary rise out of the bedding
    void=(0.0430, 0.0413, 0.0383),          # four seasons of dirt in a bug hole
    bore=(0.0130, 0.0126, 0.0122),          # down an open 22 mm ferrule bore
    polish=(0.0980, 0.0944, 0.0900),        # where sleeves have rubbed the top
    debris=(0.0450, 0.0414, 0.0348),        # swept grit in the angle at the base
    scuff=(0.0385, 0.0370, 0.0363),         # a trolley dragged along the face
    rubber=(0.0175, 0.0169, 0.0166),        # tyre and brake dust film
    algae=(0.0330, 0.0425, 0.0242),
    steel_gal=(0.4300, 0.4340, 0.4380),     # galvanised cover plate
    steel_dark=(0.0800, 0.0800, 0.0800),
)


def mat_wall():
    """Fair-faced precast concrete, bedded, socketed, stained and repaired.

    WHY THIS SHADER CARRIES MORE THAN THE USUAL SHARE OF THE OBJECT.  Measured
    against `world_contract`, the sun sits 14.7 deg off this face's normal, so
    relief on it throws tan(14.7) = 0.26x its own height in shadow.  A 3 mm bug
    hole shadows 0.8 mm = half a pixel.  Everything with a steep wall is still
    mesh -- the holes, the spalls, the grooves, the countersinks, the joint --
    and those read by Lambert falloff, not by shadow.  But the DOMINANT signal
    on a near-frontally-lit vertical concrete face is albedo, and that is what
    the seventeen histories below are.  Getting this the wrong way round is
    what made the first render a blank sheet of paper.

    Every layer is procedural and every one is driven either by object-space
    coordinates (recentred, |P| < 1.75 m) or by an attribute this module baked
    into the mesh.  `Geometry->Position` appears nowhere.
    """
    t = NT(PFX + "Concrete")
    co = t.n("ShaderNodeTexCoord")
    OBJ = (co, 3)
    ofs = t.comb(t.attr("pw_ofs_x", 2, "OBJECT"),
                 t.attr("pw_ofs_y", 2, "OBJECT"),
                 t.attr("pw_ofs_z", 2, "OBJECT"))
    P = t.vmath("ADD", OBJ, ofs)          # per-object realisation of the cement
    Pl = OBJ                              # unshifted, for anything keyed to the
                                          # element's own geometry
    Px = t.sep(Pl, 0)
    Pz = t.sep(Pl, 2)

    age = t.attr("pw_age", 2, "OBJECT")
    wet = t.attr("pw_wet", 2, "OBJECT")
    batch = t.attr("pw_batch", 2, "OBJECT")
    val = t.attr("pw_val", 2, "OBJECT")
    dirt = t.attr("pw_dirt", 2, "OBJECT")
    fresh = t.attr("pw_fresh", 2, "OBJECT")

    face = t.attr("pw_track")
    top = t.attr("pw_top")
    pit = t.attr("pw_pit")
    mort = t.attr("pw_mortar")
    h = t.attr("pw_h")                    # height above the local ground
    dep = t.attr("pw_d")                  # depth below the top of concrete
    edg = t.attr("pw_edge")
    rec = t.attr("pw_recess")
    brk = t.attr("pw_break")
    pat = t.attr("pw_patch")
    stl = t.attr("pw_steel")
    ghost = t.attr("pw_ghost")
    flow = t.attr("pw_flow")

    # ---- 1. the cast body -------------------------------------------------
    # Three scales of cloudiness, not one.  A precast face is blotchy at
    # 0.6-1.2 m (the batch and the pour), at 0.12-0.25 m (the mould's own
    # history) and at 20-40 mm (laitance).  The first version ran all three at
    # 0.30 mix and the result averaged to a flat sheet.
    n_pour = t.noise(t.vmath("SCALE", P, scale=0.34), 1.1, 3.0, 0.45)
    n_batch = t.noise(t.vmath("SCALE", P, scale=1.0), 4.4, 5.0, 0.52)
    n_mould = t.noise(t.vmath("SCALE", P, scale=1.0), 13.0, 6.0, 0.58)
    n_lait = t.noise(t.vmath("SCALE", P, scale=1.0), 44.0, 7.0, 0.60)
    n_fine = t.noise(t.vmath("SCALE", P, scale=1.0), 165.0, 8.0, 0.62)
    body = t.cmix(t.maprange(batch, 0.0, 1.0, 0.0, 1.0),
                  PAL["conc_cool"], PAL["conc_warm"])
    body = t.cmix(t.maprange(n_pour, 0.26, 0.74, 0.0, 1.0), body, PAL["conc_pale"])
    body = t.cmix(t.maprange(n_batch, 0.28, 0.72, 0.0, 1.0), body, PAL["conc_mid"])
    body = t.cmix(t.math("MULTIPLY", t.maprange(n_mould, 0.32, 0.70, 0.0, 1.0), 0.75),
                  body, PAL["conc_dark"])
    body = t.cmix(t.math("MULTIPLY", t.maprange(n_lait, 0.30, 0.72, 0.0, 1.0), 0.28),
                  body, PAL["conc_pale"])
    # per-unit value: units cast in different weeks out of different batches, and
    # a few replaced after damage.  This is the layer that stops 119 castings
    # reading as one extrusion painted 119 times.
    body = t.cmix(t.maprange(val, 0.0, 0.62, 0.0, 0.85), body, PAL["conc_dark"])
    body = t.cmix(t.maprange(val, 0.60, 1.0, 0.0, 0.60), body, PAL["conc_pale"])

    # ---- 1b. THE GRIME FIELD ----------------------------------------------
    # Two scales of accumulated dirt over the whole run, 0.4-1.5 m and
    # 0.10-0.35 m, gated by the unit's own `dirt` draw.  Without this the wall
    # is 119 castings that have each weathered identically, which is the same
    # failure as one tree spammed 100 times wearing a different hat.
    n_gr1 = t.noise(t.vmath("SCALE", P, scale=1.0), 1.5, 5.0, 0.55)
    n_gr2 = t.noise(t.vmath("SCALE", P, scale=1.0), 6.5, 7.0, 0.62)
    grime = t.math("MULTIPLY",
                   t.maprange(t.math("MULTIPLY",
                                     t.maprange(n_gr1, 0.30, 0.66, 0.05, 1.0),
                                     t.maprange(n_gr2, 0.32, 0.70, 0.15, 1.0)),
                              0.03, 0.55, 0.0, 1.0),
                   t.maprange(dirt, 0.0, 1.0, 0.20, 1.0))
    body = t.cmix(t.math("MULTIPLY", grime, 0.95), body, PAL["wash"])

    # ---- 2. the mould face is a DIFFERENT surface from the floated back ----
    # The track face came off the casting bed: dense, closed, slightly glossy
    # laitance.  The pit face was struck off with a float: open, matt, sandy.
    float_grain = t.noise(t.vmath("SCALE", P, scale=1.0), 38.0, 7.0, 0.66)
    body = t.cmix(t.math("MULTIPLY", pit,
                         t.maprange(float_grain, 0.28, 0.76, 0.12, 0.62)),
                  body, PAL["conc_mid"])

    # ---- 2b. the pit face's own history ------------------------------------
    # Mortar splashes off the bedding trowel and the drips that ran while the
    # joints were grouted.  Nobody photographs this face at 6 m, but Beat 4
    # crosses it, and a blank 350 m of it is a blank 350 m.
    v_spl = t.vor(t.vmath("SCALE", P, scale=1.0), 46.0, "F1", 0, 1.0)
    spl = t.math("MULTIPLY", pit,
                 t.math("MULTIPLY", t.maprange(v_spl, 0.0, 0.11, 1.0, 0.0),
                        t.maprange(t.noise(t.vmath("SCALE", P, scale=1.0),
                                           2.4, 5.0, 0.55), 0.46, 0.72, 0.0, 1.0)))
    body = t.cmix(t.math("MULTIPLY", spl, 0.72), body, PAL["mortar"])
    drip = t.math("MULTIPLY", pit,
                  t.math("MULTIPLY",
                         t.maprange(t.noise(t.comb(t.math("MULTIPLY", Px, 30.0),
                                                   t.math("MULTIPLY", Pz, 1.1), 0.0),
                                            1.0, 6.0, 0.6), 0.53, 0.60, 0.0, 1.0),
                         t.maprange(dep, 0.05, 1.10, 1.0, 0.0)))
    body = t.cmix(t.math("MULTIPLY", drip, 0.62), body, PAL["wash"])

    # ---- 3. coarse aggregate, ONLY where the skin is gone ------------------
    v_agg = t.vor(t.vmath("SCALE", P, scale=1.0), 105.0, "F1", 0, 1.0)
    v_agg2 = t.vor(t.vmath("SCALE", P, scale=1.0), 265.0, "F1", 0, 1.0)
    agg_id = t.vor(t.vmath("SCALE", P, scale=1.0), 105.0, "F1", 1, 1.0)
    agg_col = t.cmix(t.maprange(agg_id, 0.18, 0.80, 0.0, 1.0),
                     PAL["agg_dark"], PAL["agg_pale"])
    agg_col = t.cmix(t.maprange(agg_id, 0.87, 0.95, 0.0, 1.0), agg_col, PAL["agg_red"])
    agg_mask = t.maprange(v_agg, 0.02, 0.26, 1.0, 0.0)
    skin_gone = t.math("MAXIMUM", brk,
                       t.math("MULTIPLY",
                              t.maprange(edg, 0.008, 0.0, 0.0, 1.0), 0.45))
    body = t.cmix(t.math("MULTIPLY", agg_mask, skin_gone), body, agg_col)
    body = t.cmix(t.math("MULTIPLY", t.maprange(v_agg2, 0.02, 0.16, 1.0, 0.0),
                         t.math("MULTIPLY", skin_gone, 0.45)), body, PAL["agg_pale"])
    body = t.cmix(t.math("MULTIPLY", brk,
                         t.maprange(n_fine, 0.35, 0.75, 0.40, 0.85)),
                  body, PAL["fracture"])

    # ---- 4. the repair patch ----------------------------------------------
    # Bagged and rubbed in the yard: a different cement, so a different colour
    # and a much flatter surface.  Its edge is soft, which is what tells you it
    # was worked by hand.
    body = t.cmix(t.math("MULTIPLY", pat, 0.80), body, PAL["repair"])

    # ---- 4b. the mortar bed and the dry-pack plugs -------------------------
    # MATERIAL IDENTITY, so it goes in BEFORE the weathering.  Mixed after it
    # (which is where it was) a 0.94 mortar mix wiped the debris line off the
    # bottom 55 mm and made the dirtiest band on the wall the brightest.
    body = t.cmix(t.math("MULTIPLY", mort, 0.94), body, PAL["mortar"])
    packed = t.math("MULTIPLY", t.maprange(rec, 0.0025, 0.0065, 0.0, 1.0), top)
    body = t.cmix(t.math("MULTIPLY", packed, 0.80), body, PAL["drypack"])

    # ---- 5. THE RAIN WASH -- the biggest single read on this face ----------
    # A wall with a flat top sheds water down its face in LANES, not evenly.
    # The lanes are set by where the top arris is chipped and where the dust is
    # thickest; they are 15-140 mm wide, they start hard under the arris, and
    # each one dies at its own height.  This is the layer that turns a slab into
    # a wall, and the first version did not have it at all.
    warp = t.noise(t.vmath("SCALE", Pl, scale=0.7), 2.3, 5.0, 0.55)
    sx = t.math("ADD", Px, t.math("MULTIPLY", t.math("SUBTRACT", warp, 0.5), 0.13))
    lane_v = t.comb(t.math("MULTIPLY", sx, 9.0), t.math("MULTIPLY", Pz, 0.16), 0.0)
    lane = t.noise(lane_v, 1.0, 7.0, 0.62)
    lane_f = t.noise(t.comb(t.math("MULTIPLY", sx, 34.0), 0.0, 0.0), 1.0, 5.0, 0.55)
    streak = t.math("MULTIPLY", t.maprange(lane, 0.478, 0.545, 0.0, 1.0),
                    t.maprange(lane_f, 0.34, 0.64, 0.18, 1.0))
    reach = t.maprange(t.noise(t.comb(t.math("MULTIPLY", sx, 5.0), 0.0, 0.0),
                               1.0, 4.0, 0.5), 0.28, 0.78, 0.14, 1.45)
    vprof = t.math("MULTIPLY",
                   t.maprange(t.math("DIVIDE", dep, reach), 0.05, 1.35, 1.0, 0.0),
                   t.maprange(dep, 0.020, 0.048, 0.0, 1.0))
    # the baked ghost is an exact rectangle.  A real panel edge is where the
    # water bead ran, so it wanders 10-40 mm; perturb the mask and re-threshold
    # rather than shipping a decal with a ruled edge.
    # ... and a casting that went in last month cannot carry last season's
    # panel footprint.  Caught in the macro: the fresh unit had a ghost.
    ghost = t.math("MULTIPLY", ghost, t.math("SUBTRACT", 1.0, fresh))
    g_wob = t.noise(t.vmath("SCALE", Pl, scale=1.0), 22.0, 6.0, 0.58)
    ghost = t.maprange(t.math("ADD", ghost,
                              t.math("MULTIPLY",
                                     t.math("SUBTRACT", g_wob, 0.5), 0.55)),
                       0.40, 0.60, 0.0, 1.0)
    clean0 = t.math("SUBTRACT", 1.0, t.math("MULTIPLY", ghost, 0.80))
    wash = t.math("MULTIPLY", t.math("MULTIPLY", streak, vprof),
                  t.math("MULTIPLY", face, t.maprange(age, 0.0, 1.0, 0.85, 1.0)))
    wash = t.math("MULTIPLY", t.math("MULTIPLY", wash, clean0),
                  t.maprange(dirt, 0.0, 1.0, 0.35, 1.0))
    body = t.cmix(t.math("MULTIPLY", wash, 1.0), body, PAL["wash"])
    # ... and the dirt bead where the water ran round the panel's edge
    bead = t.math("MULTIPLY", t.math("MULTIPLY", ghost,
                                     t.math("SUBTRACT", 1.0, ghost)), 4.0)
    body = t.cmix(t.math("MULTIPLY", bead, 0.55), body, PAL["wash"])

    # ... and the cornice: a continuous dark band 25-70 mm under the top arris
    # where the sheet of water detaches and everything it carried lands.
    corn = t.math("MULTIPLY", face,
                  t.math("MULTIPLY", t.maprange(dep, 0.018, 0.040, 0.0, 1.0),
                         t.maprange(dep, 0.075, 0.150, 1.0, 0.0)))
    body = t.cmix(t.math("MULTIPLY",
                         t.math("MULTIPLY", corn,
                                t.maprange(dirt, 0.0, 1.0, 0.40, 1.0)),
                         t.maprange(n_lait, 0.3, 0.75, 0.55, 1.0)),
                  body, PAL["wash"])

    # ---- 6. last season's advert, as a ghost -------------------------------
    # A panel keeps the rain and the dust OFF for a season.  MEASURED on the
    # built blend, the footprint covers 53 % of the face -- because an advert
    # panel does -- so mixing a pale colour in at 0.62 painted half the wall one
    # flat tone and is most of why v2 read as new.  It is a SUPPRESSION, not a
    # coat: `clean` multiplies the wash and the dust down, which is applied
    # where those layers are built, and all that is added here is the faint
    # bloom of a face that has not weathered and the dirt bead at its edge.
    clean = t.math("SUBTRACT", 1.0, t.math("MULTIPLY", ghost, 0.80))
    body = t.cmix(t.math("MULTIPLY", ghost, 0.16), body, PAL["conc_pale"])

    # ---- 6b. LIME BLOOM AND LAITANCE ---------------------------------------
    # The histogram needs a bright side.  Two real, separate phenomena:
    # calcium carbonate leached out of the joints and cracks and re-deposited
    # on the face as a chalky bloom, and the patches where the mould release
    # was laid on thick, which come out of the bed with a glassy, pale skin.
    n_bl1 = t.noise(t.vmath("SCALE", P, scale=1.0), 3.2, 6.0, 0.58)
    n_bl2 = t.noise(t.vmath("SCALE", P, scale=1.0), 17.0, 7.0, 0.62)
    bloom = t.math("MULTIPLY", t.maprange(n_bl1, 0.56, 0.74, 0.0, 1.0),
                   t.maprange(n_bl2, 0.40, 0.72, 0.20, 1.0))
    bloom = t.math("MULTIPLY", bloom,
                   t.math("MAXIMUM", t.math("MULTIPLY", flow, 1.6),
                          t.maprange(dep, 1.05, 0.55, 0.25, 1.0)))
    bloom = t.math("MULTIPLY", bloom, t.math("SUBTRACT", 1.0, fresh))
    body = t.cmix(t.math("MULTIPLY", bloom, 0.70), body, PAL["lime"])
    lait = t.maprange(t.noise(t.vmath("SCALE", P, scale=1.0), 2.1, 5.0, 0.55),
                      0.60, 0.78, 0.0, 1.0)
    body = t.cmix(t.math("MULTIPLY", t.math("MULTIPLY", lait, face), 0.55),
                  body, PAL["conc_pale"])

    # ---- 7. brake and tyre dust: the lower track face goes BLACK ------------
    # A wall 11.5 m from a racing line collects rubber and brake dust, and it
    # collects it low, where the wheels throw it.
    n_film = t.noise(t.vmath("SCALE", P, scale=1.0), 2.6, 5.0, 0.52)
    film = t.math("MULTIPLY", t.math("MULTIPLY", face,
                                     t.maprange(age, 0.0, 1.0, 0.70, 1.0)),
                  t.math("MULTIPLY", t.maprange(h, 0.72, 0.04, 0.0, 1.0),
                         t.maprange(n_film, 0.24, 0.82, 0.35, 1.0)))
    film = t.math("MULTIPLY", film, clean)
    body = t.cmix(t.math("MULTIPLY", film, 0.88), body, PAL["rubber"])

    # ---- 8. capillary rise out of the bedding ------------------------------
    # THE MANIFEST'S "base staining" AXIS, and it is three separate bands, not
    # one wash:  0-0.30 m damp rise, 0.07-0.20 m the efflorescence line where
    # the rise evaporates, 0-0.11 m the splash and grit.
    n_rise = t.noise(t.vmath("SCALE", P, scale=1.0), 4.5, 6.0, 0.60)
    rise_h = t.maprange(n_rise, 0.22, 0.82, 0.14, 0.34)
    rise = t.maprange(t.math("DIVIDE", h, rise_h), 1.05, 0.0, 0.0, 1.0)
    rise = t.math("MULTIPLY", rise, t.maprange(wet, 0.0, 1.0, 0.55, 1.0))
    body = t.cmix(t.math("MULTIPLY", rise, 0.80), body, PAL["damp"])

    v_splash = t.vor(t.vmath("SCALE", P, scale=1.0), 300.0, "F1", 0, 1.0)
    splash = t.math("MULTIPLY", t.maprange(h, 0.115, 0.0, 0.0, 1.0),
                    t.maprange(v_splash, 0.0, 0.34, 1.0, 0.10))
    body = t.cmix(t.math("MULTIPLY", splash, 0.78), body, PAL["grit"])

    # the debris line: grit, rubber crumb and swept dust piled in the angle
    v_deb = t.vor(t.vmath("SCALE", P, scale=1.0), 140.0, "F1", 0, 1.0)
    deb = t.math("MULTIPLY",
                 t.maprange(h, 0.105, -0.02, 0.0, 1.0),
                 t.maprange(t.noise(t.vmath("SCALE", P, scale=1.0), 8.0, 6.0, 0.6),
                            0.24, 0.72, 0.25, 1.0))
    body = t.cmix(t.math("MULTIPLY", deb, 0.96), body, PAL["debris"])
    body = t.cmix(t.math("MULTIPLY", t.math("MULTIPLY", deb,
                                            t.maprange(v_deb, 0.0, 0.3, 1.0, 0.0)),
                         0.55), body, PAL["grit"])

    n_eff = t.noise(t.vmath("SCALE", P, scale=1.0), 16.0, 5.0, 0.55)
    eff = t.math("MULTIPLY",
                 t.math("MULTIPLY", t.maprange(h, 0.055, 0.105, 0.0, 1.0),
                        t.maprange(h, 0.22, 0.135, 0.0, 1.0)),
                 t.maprange(n_eff, 0.56, 0.86, 0.0, 1.0))
    body = t.cmix(t.math("MULTIPLY", eff, 0.30), body, PAL["lime"])

    # ---- 9. the wash below every socket, ferrule and joint -----------------
    n_run = t.noise(t.comb(t.math("MULTIPLY", Px, 60.0),
                           t.math("MULTIPLY", Pz, 3.0), 0.0), 1.0, 6.0, 0.60)
    plume = t.math("MULTIPLY", flow, t.maprange(n_run, 0.30, 0.78, 0.15, 1.0))
    body = t.cmix(t.math("MULTIPLY", plume, 0.55), body, PAL["wash"])
    # ... and where a bar or a ferrule is corroding, that wash is rust
    rustw = t.math("MULTIPLY", t.math("MULTIPLY", flow,
                                      t.math("MAXIMUM", brk, t.math("MULTIPLY", stl, 0.4))),
                   t.maprange(n_run, 0.32, 0.82, 0.0, 1.0))
    body = t.cmix(t.math("MULTIPLY", rustw, 0.80), body, PAL["rust"])

    # ---- 10. dirt that collects IN things ----------------------------------
    # `pw_recess` is positive inside every hole, socket, groove and box-out.
    # Dirt is a recess phenomenon; applied flat it is a grey wash that eats the
    # concrete, which is exactly how the first world pass lost its materials.
    n_dust = t.noise(t.vmath("SCALE", P, scale=1.0), 10.0, 6.0, 0.58)
    inner = t.math("MULTIPLY", t.maprange(rec, 0.0006, 0.0070, 0.0, 1.0),
                   t.maprange(n_dust, 0.22, 0.82, 0.45, 1.0))
    body = t.cmix(t.math("MULTIPLY", inner, 0.92), body, PAL["void"])
    # and the deep ones -- an open socket, a bore, a box-out -- go to almost
    # nothing, because that is what a 30 mm hole in a wall looks like
    deep = t.maprange(rec, 0.012, 0.030, 0.0, 1.0)
    body = t.cmix(t.math("MULTIPLY", deep, 0.95), body, PAL["bore"])

    # ---- 10b. SCUFFS ------------------------------------------------------
    # Trolleys, jacks, tyre sets and knees are dragged along this wall at
    # working height all weekend.  The mark is a HORIZONTAL smear, which is the
    # one direction nothing else in this stack produces -- every other layer is
    # a vertical wash or an isotropic blotch, and a surface whose every feature
    # runs the same way reads as wallpaper.
    scuf_v = t.comb(t.math("MULTIPLY", Px, 1.7),
                    t.math("MULTIPLY", Pz, 26.0), 0.0)
    scuf = t.noise(scuf_v, 1.0, 6.0, 0.58)
    scuf_l = t.noise(t.comb(t.math("MULTIPLY", Px, 4.5), 0.0, 0.0), 1.0, 5.0, 0.55)
    scuff = t.math("MULTIPLY",
                   t.math("MULTIPLY", t.maprange(scuf, 0.520, 0.600, 0.0, 1.0),
                          t.maprange(scuf_l, 0.36, 0.70, 0.0, 1.0)),
                   t.math("MULTIPLY", face,
                          t.math("MULTIPLY",
                                 t.math("MULTIPLY", t.maprange(h, 0.22, 0.42, 0.0, 1.0),
                                        t.maprange(h, 1.05, 0.80, 0.0, 1.0)),
                                 t.maprange(dirt, 0.0, 1.0, 0.25, 1.0))))
    body = t.cmix(t.math("MULTIPLY", scuff, 0.95), body, PAL["scuff"])

    # ---- 11. algae on the shaded pit face ----------------------------------
    n_alg = t.noise(t.vmath("SCALE", P, scale=1.0), 9.0, 7.0, 0.66)
    alg = t.math("MULTIPLY", t.math("MULTIPLY", pit,
                                    t.maprange(h, 0.70, 0.05, 0.0, 1.0)),
                 t.maprange(n_alg, 0.52, 0.84, 0.0, 1.0))
    body = t.cmix(t.math("MULTIPLY", alg, 0.62), body, PAL["algae"])

    # ---- 13. the crew lean on the top track arris --------------------------
    lean = t.math("MULTIPLY", t.math("MULTIPLY", top, age),
                  t.maprange(edg, 0.060, 0.004, 0.0, 1.0))
    body = t.cmix(t.math("MULTIPLY", lean, 0.42), body, PAL["polish"])
    # ... and the top collects everything the wind drops on it
    topdirt = t.math("MULTIPLY", top,
                     t.maprange(t.noise(t.vmath("SCALE", P, scale=1.0), 21.0, 6.0, 0.58),
                                0.28, 0.78, 0.20, 0.85))
    body = t.cmix(t.math("MULTIPLY", topdirt, 0.45), body, PAL["grit"])

    # ---- 13b. the units that have been knocked out and replaced ------------
    # 4.5 % of the run.  A new casting beside four weathered ones is the
    # loudest possible statement that these are 119 separate objects, and it is
    # the thing a real pit wall always has because cars hit it.
    body = t.cmix(t.math("MULTIPLY", fresh,
                         t.maprange(n_lait, 0.3, 0.75, 0.55, 0.92)),
                  body, PAL["conc_new"])

    # ---- 14. galvanised steel: the cover plate and the bolt heads ----------
    n_spangle = t.vor(t.vmath("SCALE", P, scale=1.0), 560.0, "F1", 1, 1.0)
    gal = t.cmix(t.maprange(n_spangle, 0.2, 0.8, 0.0, 1.0),
                 PAL["steel_gal"], PAL["steel_dark"])
    col = t.cmix(stl, body, gal)

    # ---- 15. roughness -----------------------------------------------------
    rgh = t.maprange(n_lait, 0.2, 0.8, 0.80, 0.94)
    rgh = t.fmix(t.math("MULTIPLY", pit, 0.85), rgh, 0.96)   # floated: matt
    rgh = t.fmix(t.math("MULTIPLY", brk, 0.9), rgh, 0.97)    # fresh break
    rgh = t.fmix(t.math("MULTIPLY", pat, 0.8), rgh, 0.90)    # bagged and rubbed
    rgh = t.fmix(t.math("MULTIPLY", mort, 0.88), rgh, 0.93)
    rgh = t.fmix(t.math("MULTIPLY", rise, 0.60), rgh, 0.66)  # damp: glossier
    rgh = t.fmix(t.math("MULTIPLY", film, 0.65), rgh, 0.84)
    rgh = t.fmix(t.math("MULTIPLY", grime, 0.55), rgh, 0.90)
    rgh = t.fmix(t.math("MULTIPLY", scuff, 0.85), rgh, 0.42)   # rubbed smooth
    rgh = t.fmix(t.math("MULTIPLY", deb, 0.8), rgh, 0.97)
    rgh = t.fmix(t.math("MULTIPLY", fresh, 0.8), rgh, 0.74)
    rgh = t.fmix(t.math("MULTIPLY", lean, 0.7), rgh, 0.52)   # rubbed by sleeves
    rgh = t.fmix(stl, rgh, 0.44)
    metal = t.math("MULTIPLY", stl, 0.85)

    # ---- 16. the bump stack ------------------------------------------------
    # Everything with a steep wall is already mesh.  These six are below 0.8 mm
    # of relief, which is half a pixel at 1.661 mm/px, and they exist to give
    # the near-frontal key SOMETHING to break on.  The sub-8 mm bug-hole
    # population lives here, drawn from the same distribution as the meshed one.
    # VORONOI F1 IS SMALL AT A CELL CENTRE.  Mapping 0 -> 1 here made every
    # sub-mesh bug hole a WART, and the 5x pixel-peep showed a face covered in
    # them fighting the real, correctly-recessed meshed voids.  A hole is LOW.
    v_bug = t.vor(t.vmath("SCALE", P, scale=1.0), 190.0, "F1", 0, 1.0)
    bugbump = t.math("SUBTRACT", 1.0,
                     t.math("MULTIPLY", t.maprange(v_bug, 0.0, 0.10, 1.0, 0.0),
                            t.maprange(t.noise(t.vmath("SCALE", P, scale=1.0),
                                               26.0, 5.0, 0.6),
                                       0.35, 0.75, 0.15, 1.0)))
    # STATED AS RADIANCE MODULATION, NOT AS MILLIMETRES.  itemkit section 5b,
    # ITEM-CAMPAIGN-BRIEF 4a.  What the eye judges is not the height of a bump,
    # it is what the bump does to the LIGHT, and under this film's 12.47 deg sun
    # that conversion carries a 4.52x amplifier: m = 2 sin(theta) / tan(e).
    # Three amplitude sets were rendered and REJECTED on the human figures and
    # every one of them had been chosen in millimetres.
    #
    # NONE OF THESE SIX IS A RE-TUNE.  Each `modulation_pp` is the value that
    # reproduces the Distance this module already shipped, to better than 1e-6
    # relative.  What has changed is that the module now SAYS WHAT IT IS AIMING
    # THE LIGHT AT, so the next agent can argue with 2.263 instead of guessing
    # at 0.0020 -- and so the depths follow the sun if the sun moves.
    #
    # A WAVELENGTH IS A CHOICE WHEN THE HEIGHT IS A SUM.  The band named per
    # stage is the one that is always present and carries most of the height;
    # `height_pp` is that band's own weight in the sum, so `modulation_pp` is
    # the modulation of THAT band and not of a hypothetical full-swing height.
    # Every band in this stack, at the shipped Distance:
    #
    #   [0] agg_mask  w 0.85  lam 20.67 mm  m 2.263  proud aggregate  <- named
    #       v_agg2    w 0.40  lam  8.19 mm  m 2.653  the finer aggregate
    #   [1] v_bug     w 1.00  lam 11.42 mm  m 3.169  the sub-mesh voids <- named
    #       (its amplitude noise, lam 61.54 mm, rides at m 0.626)
    #   [2] n_fine    w 1.00  lam  9.70 mm  m 0.526  cement paste
    #   [3] wave      w 1.00  lam  1.37 mm  m 4.370  ply veneer
    #   [4] noise     w 1.00  lam  9.14 mm  m 1.826  float sand
    #   [5] v_splash  w 1.00  lam  7.23 mm  m 1.548  splash pitting
    #
    # The steep ones are deliberate and sit in RELIEF_BANDS["hard_feature"]
    # (1.5-6.0): proud aggregate, a bug hole, a ply arris and a splash pit are
    # real voids and real lips with real walls, not a crumple -- and every one
    # of them is gated by a mask (`skin_gone`, `face`, `pit`, `splash`) or by a
    # sparse Voronoi cell, so it acts on a fraction of the surface.  NOTHING
    # HERE IS AN UNGATED ISOTROPIC FIELD ABOVE m = 1: the only two wholly
    # ungated signals are the cement paste at 0.526 and the bug-hole amplitude
    # noise at 0.626, both `isotropic_macro`.  An ungated field at m > 1.5 is
    # the felt this law exists to prevent.
    #
    # THE WAVELENGTHS COME FROM THE SAME LITERALS THAT PICKED THE SCALES.
    # Writing 0.0207 here instead of `K.VORONOI_WAVELENGTH_FACTOR / 105.0` would
    # be a second copy of a measured constant.
    #
    # THE WAVE ONE IS NOT 1/Scale AND THAT IS NOT A TYPO.  itemkit's own header
    # (section "what a texture node actually emits") uses Blender's wave as the
    # CONTROL for the Noise and Voronoi measurements, because it has a closed
    # form: the node multiplies the coordinate by 20 before the sine, so one
    # band is 2*pi/20 = 0.31416 of 1/Scale, and the probe returned 0.3136.
    # `itemkit._tex_wavelength_m` nevertheless returns 1.0/Scale for a Wave,
    # which is 3.183x too long, and the R2-038 recipe copies that.  Declaring
    # 4.35 mm for a 1.37 mm veneer grain would be exactly the mistake this whole
    # law exists to stop, so the closed form is used and the discrepancy is
    # raised rather than propagated.  Under the 1/Scale reading this same,
    # UNCHANGED Distance would be reported as m 1.545.
    #
    # R2-058: THAT DISCREPANCY IS NOW CLOSED AND THE LOCAL COPY IS GONE.
    # itemkit publishes `WAVE_WAVELENGTH_FACTOR = 2*pi/20` and
    # `_tex_wavelength_m` uses it, so this line reads the one source instead of
    # spelling the constant a second time.  The value is bit-identical --
    # (2.0*math.pi/20.0)/230.0 -- so nothing here moves; what changes is that
    # `bump_relief_report` now agrees with this module instead of contradicting
    # it, and this stage audits at the m 4.370 it declares.
    LAM_AGG = K.VORONOI_WAVELENGTH_FACTOR / 105.0        # 20.67 mm
    LAM_BUG = K.VORONOI_WAVELENGTH_FACTOR / 190.0        # 11.42 mm
    LAM_PASTE = K.NOISE_WAVELENGTH_FACTOR / 165.0        #  9.70 mm
    LAM_PLY = K.WAVE_WAVELENGTH_FACTOR / 230.0           #  1.37 mm (Wave)
    LAM_SAND = K.NOISE_WAVELENGTH_FACTOR / 175.0         #  9.14 mm
    LAM_SPLASH = K.VORONOI_WAVELENGTH_FACTOR / 300.0     #  7.23 mm
    b = t.bump(t.math("ADD", t.math("MULTIPLY", agg_mask, 0.85),
                      t.math("MULTIPLY", t.maprange(v_agg2, 0.0, 0.2, 1.0, 0.0),
                             0.40)),
               t.math("MULTIPLY", skin_gone, 0.95),
               modulation_pp=2.262668, wavelength_m=LAM_AGG,
               height_pp=0.85)                           # proud aggregate
    b = t.bump(bugbump, 0.85, normal=b,
               modulation_pp=3.16862, wavelength_m=LAM_BUG)   # small bug holes
    b = t.bump(n_fine, 0.45, normal=b,
               modulation_pp=0.526477, wavelength_m=LAM_PASTE)  # cement paste
    b = t.bump(t.wave(t.vmath("SCALE", Pl, scale=1.0), 230.0, 0.8, 2.0, "Y"),
               t.math("MULTIPLY", face, 0.20), normal=b,
               modulation_pp=4.37032, wavelength_m=LAM_PLY)     # ply veneer
    b = t.bump(t.noise(t.vmath("SCALE", P, scale=1.0), 175.0, 5.0, 0.60),
               t.math("MULTIPLY", pit, 0.60), normal=b,
               modulation_pp=1.82604, wavelength_m=LAM_SAND)    # float sand
    b = t.bump(t.maprange(v_splash, 0.0, 0.3, 1.0, 0.0),
               t.math("MULTIPLY", splash, 0.55), normal=b,
               modulation_pp=1.547906, wavelength_m=LAM_SPLASH)  # splash pits

    bs = t.n("ShaderNodeBsdfPrincipled")
    t.pin(bs, 0, col)
    t.pin(bs, 1, metal)
    t.pin(bs, 2, rgh)
    t.pin_named(bs, "Normal", b)
    t.pin(bs, 14, 0.20)
    out = t.n("ShaderNodeOutputMaterial")
    t.t.links.new(bs.outputs[0], out.inputs[0])
    return t.m


# ==============================================================================
#  9.  BUILD
# ==============================================================================

def _coll(name, parent=None):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(c)
    return c


def purge():
    root = bpy.data.collections.get(COLL)
    if not root:
        return
    stack, seen = [root], []
    while stack:
        c = stack.pop()
        seen.append(c)
        stack.extend(list(c.children))
    for c in seen:
        for ob in list(c.objects):
            me = ob.data
            bpy.data.objects.remove(ob, do_unlink=True)
            if me and me.users == 0 and isinstance(me, bpy.types.Mesh):
                bpy.data.meshes.remove(me)
    for c in reversed(seen):
        bpy.data.collections.remove(c)


def grade_lod(units, anchor):
    if not anchor:
        for u in units:
            u["lod"] = 0
        return
    A = np.asarray(anchor, float).reshape(-1, 3)
    for u in units:
        org, _ex, _ey, _ez = unit_basis(u)
        d = float(np.min(np.linalg.norm(A - org[None, :], axis=1)))
        u["dist"] = d
        u["lod"] = lod_of(d)


def build(lod_anchor=None, scene=None, stats=None, limit=None, uids=None):
    """Emit one object per precast unit into `COLL`."""
    scene = scene or bpy.context.scene
    purge()
    root = _coll(COLL)
    mat = mat_wall()
    units = unit_records()
    if uids is not None:
        units = [u for u in units if u["uid"] in set(uids)]
    if limit:
        units = units[:limit]
    grade_lod(units, lod_anchor)
    tris = 0
    lodn = [0, 0, 0, 0]
    t0 = time.time()
    for i, u in enumerate(units):
        _ob, n = build_unit(u, root, mat, u.get("lod", 0))
        tris += n
        lodn[u.get("lod", 0)] += 1
        if (i + 1) % 20 == 0:
            log("  %3d/%3d units, %.2f M tris, %.1fs"
                % (i + 1, len(units), tris / 1e6, time.time() - t0))
    log("built %d units, %.2f M tris, LOD counts %s"
        % (len(units), tris / 1e6, lodn))
    if stats is not None:
        stats.update(units=len(units), tris=tris, lod=lodn,
                     lengths=[u["L"] for u in units],
                     gaps=[u["gap"] for u in units],
                     dz=[u["dz"] for u in units],
                     tilt=[u["tilt"] for u in units])
    return root


# ==============================================================================
# 10.  THE PUBLIC INTERFACE FOR THE FIVE DEPENDANTS
# ==============================================================================

def _local_top_line(u, n=2):
    """The two top arrises of one unit, in the unit's own local frame."""
    L = u["L"]
    xs = np.linspace(-L * 0.5, L * 0.5, max(n, 2))
    trk = np.stack([xs, np.full_like(xs, CH_TOP), np.zeros_like(xs)], 1)
    ptt = np.stack([xs, np.full_like(xs, T_STEM - CH_TOP), np.zeros_like(xs)], 1)
    return trk, ptt


def coping_seat(n=3):
    """FOR pit_wall_coping.

    Per unit: the seat this item presents for the capping, in the world frame.
    The concrete top here IS the finished 1.200 m (the manifest's own
    `typical_height_m`); the coping LAPS OVER it and adds its own thickness, it
    does not make up a shortfall.  Follow `top_z`, `tilt` and `dyaw` per unit or
    the capping will bridge the step this item exists to create.
    """
    out = []
    for u in unit_records():
        trk, ptt = _local_top_line(u, n)
        f = unit_features(u)
        out.append(dict(
            uid=u["uid"], top_z=u["top_z"], tilt=u["tilt"], dyaw=u["dyaw"],
            seat_width=T_STEM - 2 * CH_TOP,
            fall_to_pit=0.006, ch_top=CH_TOP, length=u["L"], gap_east=u["gap"],
            arris_track_world=to_world(u, trk).tolist(),
            arris_pit_world=to_world(u, ptt).tolist(),
            ferrules=[dict(local=[cf["x"], T_STEM * 0.62, 0.0],
                           world=to_world(u, [[cf["x"], T_STEM * 0.62, 0.0]])[0].tolist(),
                           thread="M16", depth=cf["d_h"])
                      for cf in f["coping_ferrule"]],
            lifting_sockets=[dict(x=s["x"], packed=bool(s["packed"]),
                                  r=s["r"], d=s["d"]) for s in f["socket"]],
        ))
    return out


def advert_field():
    """FOR pit_wall_advert.

    Per unit: the clear rectangle on the track face and the M16 fixing grid.
    Panels sit `MOUNT_BUDGET_M` = 0.050 m proud of `FACE_PLANE_Y`, which lands
    their outer surface exactly on the contract pin, circuit y 11.500.  Nothing
    on this item is proud of `FACE_PLANE_Y` by more than 4 mm except the mortar
    haunch below z = ground + 0.055, which is why the clear rectangle starts
    above it.
    """
    out = []
    for u in unit_records():
        f = unit_features(u)
        zg = -u["hv"]
        z0 = zg + BED_TOP + HAUNCH_H + 0.010
        z1 = -CH_TOP - 0.005
        corners = [[-u["L"] * 0.5 + 0.02, 0.0, z0], [u["L"] * 0.5 - 0.02, 0.0, z0],
                   [u["L"] * 0.5 - 0.02, 0.0, z1], [-u["L"] * 0.5 + 0.02, 0.0, z1]]
        out.append(dict(
            uid=u["uid"], face_plane_y=FACE_PLANE_Y, pin_y=PIN_Y,
            mount_budget_m=MOUNT_BUDGET_M,
            local_rect=[[-u["L"] * 0.5 + 0.02, z0], [u["L"] * 0.5 - 0.02, z1]],
            world_rect=to_world(u, corners).tolist(),
            ferrules=[dict(local=[fe["x"], 0.0, fe["z"]],
                           world=to_world(u, [[fe["x"], 0.0, fe["z"]]])[0].tolist(),
                           thread="M16", state=fe["state"], row=fe["row"])
                      for fe in f["ferrule"]],
            obstruction=(None if f["boxout"] is None else
                         dict(kind="cable box-out cover plate",
                              local_rect=[[f["boxout"]["x0"] - f["boxout"]["plate_pad"],
                                           f["boxout"]["z0"] - f["boxout"]["plate_pad"]],
                                          [f["boxout"]["x1"] + f["boxout"]["plate_pad"],
                                           f["boxout"]["z1"] + f["boxout"]["plate_pad"]]],
                              proud_m=f["boxout"]["plate_t"] + 0.007)),
            ghost=(dict(local_rect=[[f["ghost"]["x0"], f["ghost"]["z0"]],
                                    [f["ghost"]["x1"], f["ghost"]["z1"]]])
                   if f["ghost"]["on"] else None),
        ))
    return out


def padding_field(n_padded=60):
    """FOR pit_wall_padding.

    The manifest gives padding 60 instances against this item's 119 units, so
    the padded run is the CONTIGUOUS stretch in front of the garages -- which is
    where crew stand -- not 60 units picked at random.  Returned per padded
    unit: the upper band of the track face and the strap ferrules.
    """
    us = unit_records()
    # the garages are circuit x -245..+75 (spec 10.7); centre the padded run on
    # the part of that which this wall actually covers.
    cand = [u for u in us if -180.0 <= u["xm"] <= 75.0]
    if len(cand) > n_padded:
        i0 = (len(cand) - n_padded) // 2
        cand = cand[i0:i0 + n_padded]
    out = []
    for u in cand:
        f = unit_features(u)
        z1 = -CH_TOP - 0.004
        z0 = z1 - 0.450
        out.append(dict(
            uid=u["uid"], band_local=[z0, z1], height=0.450,
            face_plane_y=FACE_PLANE_Y, mount_budget_m=MOUNT_BUDGET_M,
            world_rect=to_world(u, [[-u["L"] * 0.5 + 0.02, 0.0, z0],
                                    [u["L"] * 0.5 - 0.02, 0.0, z0],
                                    [u["L"] * 0.5 - 0.02, 0.0, z1],
                                    [-u["L"] * 0.5 + 0.02, 0.0, z1]]).tolist(),
            strap_ferrules=[dict(local=[fe["x"], 0.0, fe["z"]], state=fe["state"])
                            for fe in f["ferrule"] if fe["row"] == 1],
            wraps_top=True, top_z=u["top_z"], tilt=u["tilt"]))
    return out


def terminal_frame():
    """FOR pit_wall_terminal.

    The two run ends, and THE WESTWARD BUDGET.  Read §4 of the module docstring
    before using this: the west terminal is the object that put 1.067 m of
    concrete inside the car's swept volume at 207 km/h (task #46).  Building
    west of `west_limit_x` recreates it.
    """
    us = unit_records()
    west, east = us[0], us[-1]
    return dict(
        west=dict(uid=west["uid"], x_face=west["x0"], top_z=west["top_z"],
                  tilt=west["tilt"], hv=west["hv"], z_ground=west["z_ground"],
                  world_end=to_world(west, [[-west["L"] * 0.5, T_STEM * 0.5, -west["hv"] * 0.5]])[0].tolist()),
        east=dict(uid=east["uid"], x_face=east["x1"], top_z=east["top_z"],
                  tilt=east["tilt"], hv=east["hv"], z_ground=east["z_ground"],
                  world_end=to_world(east, [[east["L"] * 0.5, T_STEM * 0.5, -east["hv"] * 0.5]])[0].tolist()),
        section=SECTION,
        west_limit_x=TERMINAL_WEST_LIMIT_X,
        west_limit_reason=(
            "MEASURED against telemetry.csv densified 40x: a wall face on "
            "circuit y 11.500 starting at circuit x -227.0 is 2.180 m from the "
            "Beat-4 driven centreline; the placement gate's car volume is "
            "1.6025 m. At -228 it is 1.843 m, at -230 it is 1.159 m and at "
            "-233 it is 0.134 m -- inside the car BODY. build_architecture's "
            "4.6 m tapered terminal reached -232.6 and that is task #46."),
        gaps=[dict(x0=g0, x1=g1, why=w) for (g0, g1, w) in GAPS],
    )


def joint_sites():
    """Every joint on the wall, with what actually happens across it."""
    us = unit_records()
    out = []
    for a, b in zip(us[:-1], us[1:]):
        if a["seg"] != b["seg"]:
            continue
        gap = b["x0"] - a["x1"]
        step = b["top_z"] - a["top_z"]
        lean = b["tilt"] - a["tilt"]
        lat = b["dy"] - a["dy"]
        p = to_world(a, [[a["L"] * 0.5, 0.0, -CH_TOP]])[0]
        out.append(dict(west_uid=a["uid"], east_uid=b["uid"],
                        gap_m=round(gap, 5), top_step_m=round(step, 5),
                        lean_diff_rad=round(lean, 6),
                        top_lateral_diff_m=round(lean * a["hv"] + lat, 5),
                        world=p.tolist()))
    return out


def ferrule_sites():
    """Every cast-in socket on the item: face ferrules, coping ferrules,
    lifting sockets.  World frame, with the outward axis."""
    out = []
    for u in unit_records():
        f = unit_features(u)
        for fe in f["ferrule"]:
            out.append(dict(uid=u["uid"], kind="face_M16", state=fe["state"],
                            world=to_world(u, [[fe["x"], 0.0, fe["z"]]])[0].tolist(),
                            axis=(-unit_basis(u)[2]).tolist()))
        for cf in f["coping_ferrule"]:
            out.append(dict(uid=u["uid"], kind="coping_M16", state="open",
                            world=to_world(u, [[cf["x"], T_STEM * 0.62, 0.0]])[0].tolist(),
                            axis=unit_basis(u)[3].tolist()))
        for s in f["socket"]:
            out.append(dict(uid=u["uid"], kind="lifting_M24",
                            state=("packed" if s["packed"] else "open"),
                            world=to_world(u, [[s["x"], T_STEM * 0.5, 0.0]])[0].tolist(),
                            axis=unit_basis(u)[3].tolist()))
    return out


def board_rest_sites(n=10):
    """FOR pit_board.  Ten stations on the PIT-LANE face where a board leans."""
    us = [u for u in unit_records() if -160.0 <= u["xm"] <= 40.0]
    if not us:
        us = unit_records()
    picks = [us[int(round(i * (len(us) - 1) / max(n - 1, 1)))] for i in range(n)]
    out = []
    for i, u in enumerate(picks):
        x = u["L"] * (0.5 * hash01(u["seed"], 17) - 0.25)
        out.append(dict(uid=u["uid"], world=to_world(
            u, [[x, T_STEM, -u["hv"] + 0.02]])[0].tolist(),
            top_z=u["top_z"], tilt=u["tilt"], hv=u["hv"],
            face_normal=unit_basis(u)[2].tolist(),
            wall_top_world=to_world(u, [[x, T_STEM - CH_TOP, 0.0]])[0].tolist()))
    return out


def interface_json(path=None):
    us = unit_records()
    doc = dict(
        item=ITEM, version=__version__,
        collection=COLL, prefix=PFX,
        supersedes=list(SUPERSEDES), supersedes_note=SUPERSEDES_NOTE,
        section=SECTION,
        instances_built=len(us),
        instances_declared=INSTANCES_DECLARED,
        instances_note=(
            "121 built, not the manifest's 125. The manifest's 375 m assumes "
            "spec 10.7's circuit x -245..+130; C.world_ground_z hands y=11.500 "
            "to the ACCESS RIBBON west of x=-227 and the Beat-4 car path crosses "
            "the wall line at x=-233.6. See terminal_frame()['west_limit_reason']."),
        wall=dict(x0=WALL_X0, x1=WALL_X1, gaps=[list(g) for g in GAPS],
                  built_length_m=round(sum(u["L"] for u in us), 3),
                  setout_length_m=WALL_X1 - WALL_X0),
        coping_seat=coping_seat(),
        advert_field=advert_field(),
        padding_field=padding_field(),
        terminal_frame=terminal_frame(),
        joint_sites=joint_sites(),
        board_rest_sites=board_rest_sites(),
        units=[{k: v for k, v in u.items() if not k.startswith("_")} for u in us],
    )
    if path:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        json.dump(doc, open(path, "w"), indent=1, default=float)
    return doc


# ==============================================================================
# 11.  STAND-INS -- so the macro is not shot over a void
# ==============================================================================
# Everything here is named XPW_ and is OWNED BY OTHER ITEMS.  "XPW_" does not
# start with "PWU_", so `item_gate --prefix PWU_` measures none of it.

def _geom_out(a, b, n, first):
    """`n` samples from a toward b, starting with a step of `first` and growing
    geometrically, so a stand-in can reach the horizon without a million quads."""
    r = 1.0
    for _ in range(400):
        f = first * (r ** n - 1.0) / (r - 1.0) if abs(r - 1.0) > 1e-9 else first * n
        if abs(f) >= abs(b - a):
            break
        r += 0.01
    return a + np.cumsum(first * r ** np.arange(n))


def build_ground(coll, u, span=42.0, far=760.0):
    """The pit straight, the verge and the pit-lane deck around one unit, taken
    straight from C.world_ground_z so the wall is not standing on an invention.

    THE FIRST VERSION STOPPED AT 32 m AND PUT A BLACK BAND ACROSS THE FRAME.
    Blender's Sky Texture has no ground: below the horizon it returns black, so
    a stand-in that ends inside the field of view does not read as "the edge of
    the stand-in", it reads as a void.  This one grades geometrically out to
    `far` metres in every direction so the plate is filled to the horizon, and
    it is still `C.world_ground_z` everywhere the contract declares one.
    """
    x0, x1 = u["xm"] - span * 0.5, u["xm"] + span * 0.5
    xs = np.concatenate([
        _geom_out(x0, u["xm"] - far, 46, -0.40)[::-1],
        np.linspace(x0, x1, int(span / 0.30) + 1),
        _geom_out(x1, u["xm"] + far, 46, 0.40)])
    ys = np.concatenate([
        _geom_out(-9.0, -far, 40, -0.5)[::-1],
        np.linspace(-9.0, 11.30, 70),
        np.linspace(11.35, 11.50, 4),
        np.linspace(11.90, 12.09, 5),
        np.linspace(12.12, 30.0, 50),
        _geom_out(30.0, far, 40, 0.6)])
    xs = np.unique(np.round(xs, 5))
    ys = np.unique(np.round(ys, 5))
    XX, YY = np.meshgrid(xs, ys, indexing="ij")
    wx, wy = C.circuit_to_world(XX.ravel(), YY.ravel())
    z, own = C.world_ground_z(wx, wy)
    z = np.asarray(z, float)
    z = np.where(np.isfinite(z), z, 0.0)
    V = np.stack([np.asarray(wx), np.asarray(wy), z], 1)
    ctr = V.mean(axis=0)
    V = V - ctr
    nu, nv = len(xs), len(ys)
    idx = np.arange(nu * nv).reshape(nu, nv)
    Q = np.stack([idx[:-1, :-1].ravel(), idx[1:, :-1].ravel(),
                  idx[1:, 1:].ravel(), idx[:-1, 1:].ravel()], 1)
    me = _new_mesh(XPFX + "Ground", V, Q, None, smooth_deg=None)
    # which surface is which, so the shader can tell asphalt from apron from
    # the ground nobody has declared (which the far field is, and which reads
    # as the dry verge grass the terrain module will eventually put there)
    ow = np.asarray(own).ravel().astype(str)
    a = me.attributes.new("xp_kind", "FLOAT", "POINT")
    kind = np.where(np.char.find(ow, "Track") >= 0, 0.0,
                    np.where(np.char.find(ow, "paving") >= 0, 2.0,
                             np.where(np.char.find(ow, "terrain") >= 0, 3.0, 1.0)))
    a.data.foreach_set("value", np.ascontiguousarray(kind, np.float32))
    # how far from the hero this vertex is, so the material can drop its
    # high-frequency terms before object coordinates run out of float32
    d = me.attributes.new("xp_far", "FLOAT", "POINT")
    d.data.foreach_set("value", np.ascontiguousarray(
        np.linalg.norm(V[:, :2], axis=1), np.float32))
    me.materials.append(_mat_ground())
    ob = bpy.data.objects.new(XPFX + "Ground", me)
    ob.location = tuple(float(v) for v in ctr)
    coll.objects.link(ob)
    return ob


def _mat_ground():
    """A STAND-IN.  asphalt_wearing_course, pit_lane_surface and terrain_ground
    are separate items with their own agents; this exists so the wall is not
    photographed floating over a void, and it is named XPW_ so that
    `item_gate --prefix PWU_` measures none of it."""
    t = NT(XPFX + "Ground")
    co = t.n("ShaderNodeTexCoord")
    P = (co, 3)
    kind = t.attr("xp_kind")
    farv = t.attr("xp_far")
    near = t.maprange(farv, 60.0, 200.0, 1.0, 0.0)
    Ps = t.vmath("SCALE", P, scale=1.0)
    n1 = t.noise(t.vmath("SCALE", P, scale=0.05), 3.0, 6.0, 0.55)
    n2 = t.noise(Ps, 26.0, 7.0, 0.60)
    n3 = t.noise(Ps, 3.4, 6.0, 0.55)
    v1 = t.vor(Ps, 170.0, "F1", 0, 1.0)
    asph = t.cmix(t.maprange(n3, 0.3, 0.7, 0.0, 1.0),
                  (0.0280, 0.0275, 0.0272), (0.0470, 0.0460, 0.0445))
    asph = t.cmix(t.math("MULTIPLY", t.maprange(v1, 0.0, 0.25, 1.0, 0.0),
                         t.math("MULTIPLY", near, 0.55)),
                  asph, (0.0720, 0.0690, 0.0650))
    plat = t.cmix(t.maprange(n2, 0.3, 0.7, 0.0, 1.0),
                  (0.0620, 0.0600, 0.0570), (0.0950, 0.0915, 0.0860))
    plat = t.cmix(t.maprange(n1, 0.28, 0.74, 0.0, 1.0), plat,
                  (0.0420, 0.0405, 0.0385))
    apron = t.cmix(t.maprange(n2, 0.3, 0.7, 0.0, 1.0),
                   (0.1080, 0.1050, 0.1000), (0.1520, 0.1480, 0.1410))
    apron = t.cmix(t.maprange(n1, 0.26, 0.76, 0.0, 1.0), apron,
                   (0.0760, 0.0740, 0.0710))
    grass = t.cmix(t.maprange(n1, 0.3, 0.72, 0.0, 1.0),
                   (0.0430, 0.0530, 0.0270), (0.0870, 0.0910, 0.0470))
    col = t.cmix(t.maprange(kind, 0.0, 1.0, 0.0, 1.0), asph, plat)
    col = t.cmix(t.maprange(kind, 1.0, 2.0, 0.0, 1.0), col, apron)
    col = t.cmix(t.maprange(kind, 2.0, 3.0, 0.0, 1.0), col, grass)
    rgh = t.maprange(n2, 0.2, 0.8, 0.74, 0.94)
    b = t.bump(n2, t.math("MULTIPLY", near, 0.55), 0.0016)
    b = t.bump(t.maprange(v1, 0.0, 0.3, 1.0, 0.0),
               t.math("MULTIPLY", near, 0.40), 0.0010, normal=b)
    bs = t.n("ShaderNodeBsdfPrincipled")
    t.pin(bs, 0, col); t.pin(bs, 2, rgh); t.pin_named(bs, "Normal", b)
    o = t.n("ShaderNodeOutputMaterial")
    t.t.links.new(bs.outputs[0], o.inputs[0])
    return t.m


# ==============================================================================
# 12.  LIGHT AND CAMERA
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
    """WHERE THE MACRO IS SHOT, chosen by score, not by convenience.

    The manifest says the step and the tilt ARE the object, so the macro must be
    shot where there IS one: the score wants a big height step and an opposed
    lean against the unit's neighbour, plus damage, plus a socket left open.  It
    also refuses the two units either side of a gap, because a macro of the one
    special unit on the wall is a claim about the wrong object.
    """
    us = unit_records()
    best, bs = None, -1e9
    for i, u in enumerate(us[1:-1], start=1):
        a, b = us[i - 1], us[i + 1]
        if u["pier"] or a["seg"] != u["seg"] or b["seg"] != u["seg"]:
            continue
        f = unit_features(u)
        step = max(abs(u["top_z"] - a["top_z"]), abs(u["top_z"] - b["top_z"]))
        lean = max(abs(u["tilt"] - a["tilt"]), abs(u["tilt"] - b["tilt"]))
        opened = sum(1 for s in f["socket"] if not s["packed"])
        sc = (140.0 * step + 380.0 * lean
              + 0.80 * u["dirt"]
              + 0.55 * min(len(f["spall"]), 4) / 4.0
              + 0.40 * opened
              + 0.35 * (1.0 if f["honey"] else 0.0)
              + 0.30 * min(len(f["crack"]), 2) / 2.0
              + 0.30 * (1.0 if f["boxout"] else 0.0)
              + 0.25 * (1.0 - u["compaction"]))
        if sc > bs:
            best, bs = u, sc
    return best or us[len(us) // 2]


def macro_rig(u, coll, name, lens=LENS_MM, dist=FILMED_AT_M,
              yaw_deg=34.0, height=1.90, aim_z=None, east=False):
    """A camera at EXACTLY the manifest's distance and lens.

    The aim point is on the unit's own top track arris; the camera stands `dist`
    metres from it -- measured, then asserted in the log.  `yaw_deg` is measured
    from the wall's face normal: 0 is square on the face, 90 is straight down
    the wall.  The default 34 deg is the onboard follow's own geometry, and it
    is chosen so the joint rhythm, the height step and the lean STACK UP in
    perspective, which is the only way three millimetres of step reads.

    `east` decides which way along the wall, and the default is MEASURED, not
    chosen.  The sun's in-plane component on this face runs 0.139 WESTWARD, so
    a unit's east-end chamfer takes light at 0.444 of the face's own 0.967 and
    its west-end chamfer at 0.780.  Standing to the east and looking west turns
    the DARK chamfer toward the lens at every joint, which makes the joint a
    55 mm tonal band instead of a 15 mm slot.  Same geometry, same lens, and
    the difference between a rhythm and a hairline.

    The camera is always on the TRACK side, because that is the only side the
    film ever sees this face from.
    """
    org, ex, ey, ez = unit_basis(u)
    aim = org + ex * 0.0 + ey * (CH_TOP * 0.5) + ez * (aim_z if aim_z is not None else -0.02)
    nrm = -EY                                     # outward from the track face
    along = EX * (1.0 if east else -1.0)
    ya = math.radians(yaw_deg)
    # the camera stands `height` above the local ground, `dist` from the aim
    d = nrm * math.cos(ya) - along * math.sin(ya)
    d = d / np.linalg.norm(d)
    z_target = u["z_ground"] + height
    dz = z_target - aim[2]
    horiz = math.sqrt(max(dist * dist - dz * dz, 0.04))
    loc = aim + d * horiz + np.array([0.0, 0.0, dz])
    cam = add_camera(name, tuple(float(v) for v in loc),
                     tuple(float(v) for v in aim), lens, coll)
    return cam, aim, loc


def test_scene(samples=256, limit=None, quick=False):
    """Build the item, light it with the contract sun, and put the manifest's
    own camera on it: 6.200 m away on a 35 mm lens."""
    scene = bpy.context.scene
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)

    u = hero_unit()
    f = unit_features(u)
    org, _ex, _ey, _ez = unit_basis(u)
    log("hero unit uid %d  seg %d  L %.3f  dz %+.4f  tilt %+.5f  "
        "spalls %d  cracks %d  honey %s  boxout %s  compaction %.2f"
        % (u["uid"], u["seg"], u["L"], u["dz"], u["tilt"], len(f["spall"]),
           len(f["crack"]), bool(f["honey"]), bool(f["boxout"]), u["compaction"]))

    # anchor the LOD ladder on where the macro cameras actually stand
    anchor = [tuple(float(v) for v in (org + np.array([0.0, 0.0, 1.9])))]
    root = build(lod_anchor=anchor, scene=scene, limit=limit)
    cams = _coll(COLL + "/Cameras", root)
    stand = _coll(COLL + "/Standins", root)
    contract_light(scene, coll=root)
    build_ground(stand, u, span=150.0)

    macro, aim, loc = macro_rig(u, cams, PFX + "CAM_MACRO",
                                yaw_deg=57.0, height=1.62, aim_z=-0.30)
    log("CAM_MACRO at %.4f m on a %.0f mm lens"
        % (float(np.linalg.norm(np.array(loc) - np.array(aim))), LENS_MM))
    # square on the face: the cast surface itself, at the same distance and lens
    macro_rig(u, cams, PFX + "CAM_FACE", yaw_deg=6.0, height=0.95, aim_z=-0.55)
    # hard down the wall: the joint rhythm and the step line against the sky
    macro_rig(u, cams, PFX + "CAM_ALONG", yaw_deg=76.0, height=1.28,
              aim_z=-0.12)
    # the film's OWN geometry: the onboard follow rides 1.9 m off the deck
    macro_rig(u, cams, PFX + "CAM_ONBOARD", yaw_deg=34.0, height=1.90)
    # the coping's own lens, 58 mm at 6.2 m -- so this top is judged at the
    # resolution its dependant will be judged at
    macro_rig(u, cams, PFX + "CAM_TOP58", lens=58.0, yaw_deg=40.0, height=2.35)
    # the base: bedding, haunch, capillary rise, splash
    macro_rig(u, cams, PFX + "CAM_BASE", yaw_deg=22.0, height=0.55,
              aim_z=-u["hv"] + 0.12)
    # the pit-lane side, from where the crew and pit_board see it
    org2, _e2, ey2, ez2 = unit_basis(u)
    aim2 = org2 + ey2 * (T_STEM * 0.6) + ez2 * (-0.30)
    d2 = EY * math.cos(math.radians(30.0)) + EX * math.sin(math.radians(30.0))
    d2 = d2 + np.array([0.0, 0.0, 0.30])
    d2 = d2 / np.linalg.norm(d2)
    loc2 = aim2 + d2 * FILMED_AT_M
    add_camera(PFX + "CAM_PIT", tuple(float(v) for v in loc2),
               tuple(float(v) for v in aim2), LENS_MM, cams)
    # the wide, so the run can be judged in its setting
    macro_rig(u, cams, PFX + "CAM_WIDE", lens=50.0, dist=22.0, yaw_deg=62.0,
              height=2.6)

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
# 13.  MEASUREMENT
# ==============================================================================

def car_path_clearance(x_from=None):
    """Minimum distance, in metres, from the Beat-4 driven centreline to the
    wall face line if the wall starts at circuit x `x_from`.  MEASURED against
    telemetry.csv, densified 40x.  This is the function that decides WALL_X0."""
    import csv
    p = os.path.join(_ROOT, "telemetry", "telemetry.csv")
    rows = list(csv.DictReader(open(p)))
    X = np.array([float(r["x"]) for r in rows])
    Y = np.array([float(r["y"]) for r in rows])
    tt = np.arange(len(X))
    td = np.linspace(0, len(X) - 1, len(X) * 40)
    CX, CY = C.world_to_circuit(np.interp(td, tt, X), np.interp(td, tt, Y))
    x0 = WALL_X0 if x_from is None else x_from
    px = np.clip(CX, x0, WALL_X1)
    d = np.hypot(CX - px, CY - PIN_Y)
    i = int(np.argmin(d))
    return float(d[i]), float(CX[i]), float(CY[i])


def selftest(verbose=True):
    fails = []
    n = [0]

    def chk(name, cond, detail=""):
        n[0] += 1
        print("  %s %-58s %s" % ("ok  " if cond else "FAIL", name, detail))
        if not cond:
            fails.append(name)

    print("pit_wall_unit %s  self test" % __version__)
    us = unit_records()

    print("\n[1] the section against the contract")
    chk("face plane is behind the contract pin by the mount budget",
        abs((FACE_PLANE_Y - PIN_Y) - MOUNT_BUDGET_M) < 1e-12,
        "pin %.3f  face %.3f  budget %.3f" % (PIN_Y, FACE_PLANE_Y, MOUNT_BUDGET_M))
    chk("PIN_Y is the contract's own C.PIT_WALL_Y", PIN_Y == C.PIT_WALL_Y)
    chk("top of concrete = the manifest's typical_height_m",
        abs(TOP_Z - 1.2) < 1e-12)
    px = TOP_Z * LENS_MM * 3840.0 / (36.0 * FILMED_AT_M)
    chk("onscreen_px_4k reproduces the manifest's 723", abs(px - 723.0) < 1.0,
        "%.1f px" % px)

    print("\n[2] the plan")
    chk("121 +- 4 units", 117 <= len(us) <= 125, "%d units" % len(us))
    L = np.array([u["L"] for u in us])
    chk("every 5th unit is short", (L < 2.6).sum() >= len(us) // 6,
        "%d short of %d" % (int((L < 2.6).sum()), len(us)))
    chk("no unit exceeds 3.0 m of circuit (law 7)", L.max() <= 3.05,
        "max %.3f m" % L.max())
    gaps = np.array([u["gap"] for u in us])
    chk("joint gaps are 5-30 mm", gaps.min() >= 0.004 and gaps.max() <= 0.035,
        "%.1f-%.1f mm, mean %.1f" % (gaps.min() * 1e3, gaps.max() * 1e3,
                                     gaps.mean() * 1e3))
    dz = np.array([u["dz"] for u in us])
    chk("height draw within the manifest's +-12 mm",
        np.abs(dz).max() <= STEP_CLIP + 1e-9,
        "sd %.2f mm, max %.2f mm" % (dz.std() * 1e3, np.abs(dz).max() * 1e3))
    tl = np.array([u["tilt"] for u in us])
    chk("tilt draw within the manifest's +-0.004 rad",
        np.abs(tl).max() <= TILT_CLIP + 1e-9,
        "sd %.5f, max %.5f rad" % (tl.std(), np.abs(tl).max()))
    js = joint_sites()
    steps = np.array([abs(j["top_step_m"]) for j in js])
    chk("joint step sd is a visible number at 602 px/m",
        steps.std() > 0.004,
        "mean %.1f mm = %.1f px, max %.1f mm = %.1f px"
        % (steps.mean() * 1e3, steps.mean() * PX_PER_M,
           steps.max() * 1e3, steps.max() * PX_PER_M))

    print("\n[3] laws 4 and 5: the ground and the embed")
    zg = np.array([u["z_ground"] for u in us])
    emb = np.array([u["embed"] for u in us])
    chk("every seating z came from C.world_ground_z",
        np.isfinite(zg).all(), "%.4f..%.4f m" % (zg.min(), zg.max()))
    chk("embed >= C.BASE_EMBED_M everywhere", emb.min() >= EMBED,
        "min %.3f m (law says %.3f)" % (emb.min(), EMBED))
    owners = sorted({o for u in us for o in u["ground_owner"]})
    chk("the ground under the wall is somebody's, not terrain's",
        all("terrain" not in o for o in owners), str(owners))

    print("\n[4] the west end and the Beat-4 car path (task #46)")
    d0, cx0, cy0 = car_path_clearance()
    chk("wall face clears the placement gate's car volume (1.6025 m)",
        d0 >= 1.6025, "%.3f m at circuit (%.1f, %.2f)" % (d0, cx0, cy0))
    d1, _, _ = car_path_clearance(TERMINAL_WEST_LIMIT_X)
    chk("the published terminal budget also clears it", d1 >= 1.6025,
        "%.3f m at x=%.1f" % (d1, TERMINAL_WEST_LIMIT_X))
    d2, _, _ = car_path_clearance(-232.6)
    chk("... and build_architecture's terminal nose did NOT (this is #46)",
        d2 < 1.6025, "%.3f m at x=-232.6" % d2)

    print("\n[5] one unit's mesh")
    u = hero_unit()
    V, Q, T, A, ctr, info = unit_mesh_arrays(u, 0)
    chk("recentred: |P| < 1.75 m (law 6)", info["maxP"] < 1.75,
        "max |P| %.4f m" % info["maxP"])
    chk("nothing crosses the contract pin",
        float(V[:, 1].min() + ctr[1]) >= -MOUNT_BUDGET_M - 1e-9,
        "outermost y %.4f m behind the face plane"
        % float(-(V[:, 1].min() + ctr[1])))
    ln = []
    for q in Q[::7]:
        for i in range(4):
            ln.append(float(np.linalg.norm(V[q[i]] - V[q[(i + 1) % 4]])))
    ln = np.sort(np.array(ln))
    p10 = float(ln[len(ln) // 10])
    chk("10th-percentile edge <= 6 px at 6.2 m on 35 mm", p10 * PX_PER_M <= 6.0,
        "p10 %.2f mm = %.2f px  (median %.2f mm)"
        % (p10 * 1e3, p10 * PX_PER_M, float(ln[len(ln) // 2]) * 1e3))
    chk("all attributes baked", all(k in A for k in ATTRS),
        "%d of %d" % (sum(1 for k in ATTRS if k in A), len(ATTRS)))
    print("      hero unit: %d verts, %d quads, %d tris (nx %d, profile %d)"
          % (info["verts"], info["quads"], info["tris"], info["nx"], info["np"]))

    print("\n[6] per-instance variation, as the gate will measure it")
    dims, tri = [], []
    for q in us[::7]:
        V2, Q2, T2, _A, _c, i2 = unit_mesh_arrays(q, 2)
        lo = V2.min(0); hi = V2.max(0)
        dims.append(float(np.linalg.norm(hi - lo)))
        tri.append(len(Q2) * 2 + len(T2))
    dims = np.array(dims)
    cv = dims.std() / dims.mean()
    chk("size CV >= 0.03 (gate threshold)", cv >= 0.03, "CV %.4f" % cv)
    chk("distinct topologies >= 2 (gate threshold)", len(set(tri)) >= 2,
        "%d distinct triangle counts in a sample of %d" % (len(set(tri)), len(tri)))

    print("\n[7] LOD ladder")
    for l in range(4):
        V3, Q3, T3, _a, _c, i3 = unit_mesh_arrays(u, l)
        e = []
        for q in Q3[::11]:
            e.append(float(np.linalg.norm(V3[q[0]] - V3[q[1]])))
        e = np.sort(np.array(e))
        print("      LOD %d: %7d verts %7d quads   p10 edge %.2f mm"
              % (l, i3["verts"], i3["quads"], float(e[len(e) // 10]) * 1e3))

    print("\n[8] the per-unit draws are actually different numbers")
    us2 = unit_records()
    ks = [3, 5, 7, 11, 13]
    cols = np.array([[hash01(q["seed"], k) for k in ks] for q in us2])
    off = np.abs(np.corrcoef(cols.T) - np.eye(len(ks)))
    chk("hash01(seed, k) decorrelates across k -- THIS WAS BROKEN",
        off.max() < 0.25, "max |cross-correlation| %.4f over %d units"
        % (off.max(), len(us2)))
    sp = np.array([[q["age"], q["wet"], q["batch"]] for q in us2])
    chk("age / wet / batch are three different draws",
        np.abs(np.corrcoef(sp.T) - np.eye(3)).max() < 0.25,
        "spread %.4f / %.4f / %.4f" % tuple(sp.std(axis=0)))
    gh = [unit_features(q)["ghost"] for q in us2]
    frac = np.mean([(g["x1"] - g["x0"]) * (g["z1"] - g["z0"])
                    / (q["L"] * (q["hv"] - 0.075))
                    for g, q in zip(gh, us2) if g["on"]])
    chk("the advert ghost covers less than 70 % of a face", frac < 0.70,
        "%.1f %% of the face where present" % (100 * frac))

    print("\n[9] the stroke font is hand-coded, not a datablock")
    segs, w = stroke_segments("PW-047-24", 0.038)
    chk("the stamp rasterises to real segments", len(segs) > 20 and w > 0.15,
        "%d segments, %.3f m wide" % (len(segs), w))

    print("\n%d checks, %d failures" % (n[0], len(fails)))
    return not fails


def census(stats):
    L = np.array(stats["lengths"]); g = np.array(stats["gaps"])
    dz = np.array(stats["dz"]); tl = np.array(stats["tilt"])
    print(">> population: %d units, %.3f M tris, LOD %s"
          % (stats["units"], stats["tris"] / 1e6, stats["lod"]))
    print(">>   length %.3f-%.3f m  mean %.3f  sd %.3f  CV %.4f"
          % (L.min(), L.max(), L.mean(), L.std(), L.std() / L.mean()))
    print(">>   joint  %.1f-%.1f mm  mean %.1f mm = %.1f px"
          % (g.min() * 1e3, g.max() * 1e3, g.mean() * 1e3, g.mean() * PX_PER_M))
    print(">>   height step sd %.2f mm = %.1f px; lean sd %.5f rad = %.2f mm "
          "at the top" % (dz.std() * 1e3, dz.std() * PX_PER_M, tl.std(),
                          tl.std() * 1.34 * 1e3))


# ==============================================================================
# 14.  CLI
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
