#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
access_road_slab.py — CIRCUIT VITRINE, per-item hero campaign, item
``access_road_slab`` (zone ``transit_corridor``, wave 1, build order 23, HERO,
3 dependants).

WHAT THIS IS, IN ONE SENTENCE
=============================
The 244.32 m pit-exit access road built as **jointed plain concrete pavement** —
every pour bay is its own slab object with its own screed level, its own broom
direction, its own crazing and crack history, separated by joints that are
modelled slots with sawn walls, a sealant meniscus and spalled arrises; never a
dark line painted on a flat ribbon, and never the circuit's asphalt shader.

THE MANIFEST RECORD THIS IS BUILT TO (docs/item_manifest.json, verbatim)
-----------------------------------------------------------------------
    nearest_camera_m       1.7          lens_at_closest_mm   35
    onscreen_px_4k         2160         overfills_frame      true
    px_measured_dimension_m 1.0         instances            1
    hero                   true         build_wave           1
    variation_axes         pour-bay joints / broom-finish direction /
                           unrubbered (mu 0.90) so it stays pale
    notes                  "12.0 m wide, 244.3 m long; the first 49.6 m is DEAD
                            FLAT at z=0.000.  Unrubbered concrete: it must not
                            carry the track's rubber line.  Wrong version: same
                            asphalt shader as the circuit."

THE ARITHMETIC THAT SETS THE DETAIL FLOOR
-----------------------------------------
    px_per_m = (3840 * 35 / 36) / 1.7 = 2196.1 px/m   ->   1 px = 0.4553 mm

MEASURED against every other row in the manifest, that is the 24th finest pixel
budget of 435 — the top 6 %.  (The first draft of this docstring said "third
finest"; it was not, and a number written down without being computed is the
defect this project keeps catching.)  On the 4K master, at the contract sun
(12.4706 deg elevation, shadow ratio 4.5222):

    a 14.2 mm broom groove pitch        31.2 px  — corduroy, unmistakable
    a 1.4 mm groove depth               casts 6.3 mm = 13.9 px of shadow
    a 10 mm sawn joint reservoir        22.0 px wide, 44 px deep in shadow
    a 4.5 mm joint faulting step        casts 20.4 mm = 44.7 px of shadow
    a 2.0 mm crazing crack               4.4 px — a hairline you can see
    a 9 mm aggregate popout             19.8 px across, 3 mm deep = 6.6 px
    a 0.30 mm sand-grain cell            0.66 px — the ONLY thing below a pixel,
                                        and the only thing left to the bump map

Everything in that list except the last line is MESH in this module.  At a
12.47 deg sun the entire read of a pavement is the shadow its relief throws, and
a bump map throws none.

THE THING THIS ITEM MUST NOT BE
-------------------------------
The manifest names the wrong version explicitly: *"same asphalt shader as the
circuit"*.  This is concrete, it is **unrubbered**, and it is the only large
pale surface in Beat 4.  There is no racing line on it, no rubber pickup, no
bitumen.  Its friction is mu = 0.90 (declared on every emitted object as
``friction_mu``) against the circuit's polished-and-rubbered asphalt.  What
darkens it instead is dust, damp, diesel drips off the transporters and the odd
scuff arc where a truck has turned tight — all of them local, none of them a
continuous line down the middle.

It also must not be `paddock_paving_bay`.  That item is a hand-laid apron on a
5-pass paver plan with 2.8 x 3.15 m bays and formed longitudinal joints carrying
the level steps.  This is a ROAD: 4 lanes of 3.0 m, transverse contraction
joints at 3.40/3.70/4.00 m dowelled across the traffic direction, longitudinal
tie-bar joints, a portal isolation joint at world X = +58, faulting, curl, and a
gore that dies into the pit straight.  Different construction, different joint
grammar, different wear.

=============================================================================
THE PUBLIC INTERFACE  —  this item is a FOUNDATION, 3 items depend on it
=============================================================================
Dependants named in the manifest, none of whom can ask questions:

    access_road_saw_joint   240 instances, filmed at 1.7 m on a 58 mm lens
                            "The rhythm that tells you it is concrete and not
                             tarmac at 1.7 m."
    access_road_kerb        400 instances, 3.0 m, "individual units, not an
                            extruded ribbon"
    pit_exit_portal_frame     1 instance, 1.5 m, at world X = +58, and THE
                            CAMERA PASSES THROUGH IT

--- 1. WHERE THE SURFACE IS -------------------------------------------------

    slab_top_z(x, y)        -> (z, bay_index) for any WORLD point on the road.
                               The level a surveyor's staff reads: contract
                               datum + bay level + tilt + curl + slipform screed
                               wave.  It does NOT include the broom groove
                               (-0.7..-1.7 mm), the crazing (-0.4..-0.9 mm) or a
                               popout, because anything standing on the slab
                               bridges those.  Anything laid ON the road — a
                               kerb, a gully frame, a cone, a portal footing —
                               sits on this number.

    slab_top_z_route(t, v)  -> the same in ROUTE coordinates (t metres from the
                               glass plane at world x = +15, v metres left of
                               travel).  Vectorised.

    C.world_ground_z(x, y) returns C.access_z(t, v) over this whole ribbon —
    exactly 0.000 for t <= 49.60.  THIS MODULE IS THE MESH UNDER THAT NUMBER and
    it is not flat: bay tops run between SLAB_TOP_MIN_M and SLAB_TOP_MAX_M
    against that datum.  A module that keeps calling C.world_ground_z is never
    more than SLAB_TOP_MAX_M above the concrete nor more than |SLAB_TOP_MIN_M|
    below it.  Both bounds are MEASURED by ``verify()`` on the built mesh, not
    asserted.  SLAB_TOP_MAX_M = +0.0045 is held deliberately below
    build_architecture's MARK_Z = 0.0075, so a marking laid on this road still
    has 3.0 mm of air under it at the highest bay in the world.

--- 2. THE JOINTS — what access_road_saw_joint (240 instances) needs ---------

    joint_segments(bays)    -> [Joint, ...], one per joint SEGMENT (a transverse
                               joint across one lane, or a longitudinal joint
                               down one bay).  The count is a measured output,
                               printed by ``measure()``; the manifest's 240 is
                               the number this layout was tuned to reproduce.

        j.p0, j.p1      world-frame endpoints of the joint CENTRELINE, z taken
                        at the arris (the top of the slot)
        j.kind          'sawn'     transverse contraction joint, 6 mm induced
                                   kerf under a 10 mm x 20 mm sealant reservoir
                        'formed'   longitudinal tie-bar joint between paving
                                   lanes, 12 mm, tooled arris
                        'isolation' at the glass threshold (t = 0) and around
                                   the portal at world X = +58, 20 mm, filler
                                   board and a sealant cap
        j.width_m       clear width of the slot AT THE TOP
        j.depth_m       reservoir depth below the arris
        j.arris_z0/z1   slab top z at each end — they differ, because bays fault
        j.fault_m       the step across the joint, signed toward side `right`
        j.bed_z         z of the SEALANT or DETRITUS surface inside the slot —
                        the level a seed germinates on, 3..21 mm below the arris
        j.sealed        True where a sealant bead fills the slot
        j.spall         0..1 how much of the arris has chipped away
        j.age           0..1 sealant age (0 fresh black, 1 grey and crazed)
        j.left, j.right bay indices either side (None at the ribbon edge)
        j.t0, j.t1, j.v0, j.v1   the same segment in ROUTE coordinates

    joint_bed_z(j, s)       -> z of the slot bed at parameter s in [0, 1].
    joint_frame(j, s)       -> (world point on the centreline, unit tangent,
                               unit left-normal) so a dependant can orient a
                               sealant bead, a backer rod or a weed without
                               re-deriving the route frame.

    A dependant that supersedes the joint fill should call
    ``build(..., build_joint_fill=False)``; see section 6.

--- 3. THE EDGE — what access_road_kerb (400 units) needs --------------------

    edge_polyline(side, ds=0.5) -> dict with `xy` (N,2) world, `z` (N,) at the
                               ARRIS of the slab edge, `t` (N,) route station,
                               `v` (N,) route lateral, `tangent` (N,2) and
                               `normal` (N,2) pointing OUTBOARD.  side = +1 is
                               left of travel (the retaining-wall side), -1 is
                               right (the track side).

    The kerb's back face butts this line and its top sits KERB_SEAT_M above the
    arris z; the slab is built with a formed vertical face down to SKIRT_Z so a
    kerb bedded against it meets concrete, not a hole.

    EDGE_ARRIS_CHAMFER_M and the measured mean/max of the edge arris z are
    reported by ``verify()``.

--- 4. LETTING SOMETHING INTO THE SLAB ---------------------------------------

    reserve(polygon_world, kind='cover', depth_m=RECESS_LIP_M)
                            registers an exclusion BEFORE build().  Bays are cut
                            to the POLYGON (not its bounding box — a world-
                            aligned box over-cuts a gully in a route frame
                            rotated up to 40 deg) and a sawn wall is built from
                            the cut boundary down to the same soffit as the outer
                            skirt, so access_road_gully (14 frames with a 14 mm
                            rebate ring) and pit_exit_portal_frame's footings
                            drop into a real pocket with a real concrete face
                            behind them.

    portal_isolation(t=PORTAL_T) -> the pair of isolation joints the road is cast
                            against at world X = +58, already in the layout.

--- 5. THE MATERIALS ---------------------------------------------------------

    mat_concrete(), mat_sealant(), mat_detritus(), mat_subbase(),
    mat_edgeface(), mat_patch_asphalt()   — all cached by name.

    Every one reads ``TexCoord -> Object`` plus the baked vertex attributes in
    ``ATTRS``.  ``Geometry -> Position`` appears NOWHERE in this file: the ribbon
    reaches world x = 230, y = 93, and a position-driven procedural at |P| ~ 250
    m is already losing its low bits.  Per-bay decorrelation is done with the
    ``bay`` attribute (a per-bay constant hash), not with world position, so the
    last bay of the gore has exactly the precision of the first bay at the glass.

    ATTRS = ('pol', 'dst', 'dmp', 'arr', 'oil', 'scf', 'lat', 'rst',
             'exp', 'saw', 'dmg', 'hgt')

        pol  wheel-path polish        dst  dust film        dmp  standing damp
        arr  joint-arris proximity    oil  diesel drip      scf  tyre scuff
        lat  laitance skin            rst  tie-bar rust     exp  aggregate showing
        saw  1 = diamond-sawn face, 0.2 = slipformed face, 0 = the slab top
        dmg  crack / spall / corner-break proximity
        hgt  1 on the broom LAND, ~0.3 at the bottom of a groove

    They are packed into three FLOAT_COLOR point attributes (``ATTR_LAYERS``) —
    same bytes, a quarter of the write calls, one Attribute node per four
    channels.  Write them with ``bake_attrs(mesh, dst=..., dmp=...)``; unnamed
    channels default to 0.0 except ``hgt``, which defaults to 1.0 because 0.0
    means "at the bottom of a groove" and a mesh that leaves it there renders as
    if every vertex were in shadow.

    PER-BAY CONSTANTS DO NOT GET A PER-VERTEX CHANNEL.  ``Object Info -> Random``
    decorrelates every procedural per bay and ``Object Info -> Color`` carries
    ``(finish/5, age, crazing, bay random)``.  A dependant emitting an object
    into ``mat_concrete()`` should set ``ob.color`` the same way, or it will
    render as a brand-new uncrazed slab.

    ``dst`` is the dust film and ``dmp`` is standing damp; a mesh that leaves
    both at 0 reads as concrete that has never been outdoors.

--- 6. EMITTING --------------------------------------------------------------

    build(anchor_world=None, quality='hero', seed=SEED, t_range=None,
          build_joint_fill=True, build_bed=True, vert_budget=VERT_BUDGET,
          view_dir=None) -> dict

        Emits into collection ``W_Item_AccessRoadSlab``, object prefix ``ARS_``.

        `anchor_world` is THE LENS.  Every bay is meshed on a graded anisotropic
        grid whose spacing is solved against the distance from that point, fine
        ACROSS the broom grooves and coarse along them, because a broom finish is
        a one-dimensional feature and meshing it isotropically spends 6x the
        triangles on the axis that carries no information.  Pass None and the
        whole road is built at the coarse tier.

        `view_dir` is a SHOT-SPECIFIC economy and the assembly should leave it
        None.  It coarsens bays outside the frame by up to VIEW_PENALTY, which is
        what lets the single-camera test scene put 9.05 M vertices where the
        macro can see them on an 11 GB machine.  The film's camera flies the
        whole corridor, so a full build must either pass view_dir=None or call
        build() once per station with its own anchor.

        `build_joint_fill` emits the sealant beads, the grit in the unsealed
        joints and the routed-and-sealed crack overbands into the sub-collection
        ``W_Item_AccessRoadSlab_JointFill``.  IT IS ON BY DEFAULT so this item
        stands alone and its macro render is honest.  ``access_road_saw_joint``
        supersedes it: when that item lands, the assembly calls this with
        build_joint_fill=False and the slot geometry — arris, kerf walls, spall,
        reservoir — is still this module's, because it is the slab's concrete.

        `t_range` restricts the build to a route-station window; the joints,
        levels and finishes of a window are IDENTICAL to those of the same
        stations in a full build, because ``bay_layout`` is a pure function of
        the seed.

--- 7. WHAT IS DELIBERATELY NOT HERE -----------------------------------------

    * kerbs, gullies, the portal, markings, cones, the corridor walls — all
      separate manifest items.
    * The 0.30 m sawn edge strip along the OUTBOARD edge IS here: the contract
      calls it "the sawn edge strip build_surface lays along the ribbon", it is
      the line build_architecture cuts its paving to, and leaving it out reopens
      the 0.30 m slot that `world_contract` 1.0.1 was written to close.  The
      footprint is taken from ``build_surface._access_layout()`` so that this
      mesh is a drop-in replacement for ``SURF_AccessRoad`` with byte-identical
      edges.

=============================================================================
RUNNING IT
=============================================================================
    # build the test scene (contract sun, manifest camera at 1.7 m / 35 mm)
    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P world/items/access_road_slab.py -- scene \
        --out world/items/access_road_slab_test.blend

    # the acceptance gate
    /opt/blender-5.2.0-linux-x64/blender -b world/items/access_road_slab_test.blend \
        --factory-startup -P tools/item_gate.py -- --item access_road_slab \
        --prefix ARS_ --out render/items/access_road_slab/gate.json

    # the things the gate structurally cannot check
    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P world/items/access_road_slab.py -- verify \
        --out render/items/access_road_slab/verify.json
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
import warnings

import numpy as np

try:
    import bpy
    from mathutils import Matrix, Vector
except Exception:                                   # pure-numpy import for tools
    bpy = None
    Matrix = Vector = None

# splitmix64's wraparound is THE POINT; numpy 2 reports every wrap as a
# RuntimeWarning, which at 10^8 hashes per build is hundreds of MB of stderr for
# a defined operation.  Silenced by exact message so a REAL overflow elsewhere
# still shows.
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

# build_surface is imported for TWO things and nothing else:
#   * `_G`, the project's shader-graph DSL.  A second copy of the node idiom is a
#     second place for it to drift, and this concrete has to sit beside
#     M_Surf_Asphalt in the same frame at the merge.
#   * `_access_layout`, which is the AUTHORITATIVE footprint of the ribbon —
#     including the sawn edge strip and the three fixed-point passes that push
#     the inboard edge off the racing surface.  Re-deriving it here would be a
#     second opinion about a boundary that already has an owner.
import build_surface as BS                                  # noqa: E402
from build_surface import _G as G                           # noqa: E402

COLL_NAME = "W_Item_AccessRoadSlab"
FILL_COLL_NAME = "W_Item_AccessRoadSlab_JointFill"
PFX = "ARS_"
MPFX = "M_ARS_"
ITEM_ID = "access_road_slab"

# ---------------------------------------------------------------- filmed spec
# straight out of docs/item_manifest.json; do not guess what the manifest decided
NEAREST_CAMERA_M = 1.7
LENS_AT_CLOSEST_MM = 35.0
SENSOR_MM = 36.0
RES_X_4K = 3840
RES_Y_4K = 2160
PX_PER_M = (RES_X_4K * LENS_AT_CLOSEST_MM / SENSOR_MM) / NEAREST_CAMERA_M   # 2196.1
M_PER_PX = 1.0 / PX_PER_M                                                   # 0.4553 mm
#   metres per screen pixel at an ARBITRARY distance d:
M_PER_PX_PER_M = SENSOR_MM / (RES_X_4K * LENS_AT_CLOSEST_MM)                # 2.679e-4

MANIFEST_JOINT_SEGMENTS = 240       # access_road_saw_joint's declared instances;
                                    # the layout below is tuned to reproduce it
FRICTION_MU = 0.90                  # UNRUBBERED.  Declared on every object.

SEED = 20260729


# =============================================================================
# 1.  THE CONSTRUCTION — every dimension is a real one
# =============================================================================
#
# THE ROAD.  12.0 m between the ribbon edges (C.ACCESS_ROAD_W), 244.3198 m long
# (C.ACCESS_TOTAL), dead flat at z = 0.000 for the first 49.60 m (C.ACCESS_L2)
# and then easing onto C.ground_z across the R150 merge arc.  Past t ~ 95 m the
# inboard edge is clipped by the racing surface and the road becomes a gore that
# closes to a nose at t = 244.32.  All of that is the contract's arithmetic; this
# module only decides how the concrete was POURED.
#
# THE POUR.  Four 3.0 m paving lanes.  3.0 m is a slipform paver's narrow pass
# and also the width a hand-screeded bay can be struck off from both sides, and
# 4 x 3.0 lands exactly on the contract's 12.0 m so the outer lanes end on the
# declared edge instead of on an arbitrary offcut.
LANE_W = 3.0
LANE_EDGES_V = (-6.0, -3.0, 0.0, 3.0, 6.0)      # route lateral, + is LEFT of travel
N_LANE = len(LANE_EDGES_V) - 1

# THE TRANSVERSE JOINT SPACING.  A 240 mm unreinforced slab cracks if a panel is
# longer than about 24 x its thickness (5.76 m) or more slender than 1.25 : 1.
# 3.0 m lanes therefore want 3.40 .. 4.00 m panels (1.13 .. 1.33 : 1), and the
# saw crew works to a chalk line that moves when it meets a gully or a portal.
# Three canonical spacings, never a jitter around them: a jittered spacing means
# no two bays are the same size, which is true of nothing that was ever set out
# with a tape.
BAY_L = (3.40, 3.70, 4.00)
BAY_L_MEAN = sum(BAY_L) / len(BAY_L)            # 3.700

# FORCED JOINTS.  A pavement is always cast against a structure, never through
# it.  Two structures cross this road:
#   t = 0.00   the breach plane at world x = +15 — the showroom threshold.  An
#              isolation joint with a compressible filler board, because the
#              building and the road settle differently.
#   t = 43.00  the pit-exit portal at world x = +58 (C.TRANSIT_PORTAL_X).  The
#              road was poured around its footings, so there is an isolation
#              joint each side of the frame.
PORTAL_T = float(C.TRANSIT_PORTAL_X - C.ACCESS_GLASS_X)          # 43.0
PORTAL_ISOL_HALF = 0.55                        # half the gap the frame sits in
FORCED_JOINT_T = (0.0, PORTAL_T - PORTAL_ISOL_HALF, PORTAL_T + PORTAL_ISOL_HALF)

# THE SLAB ITSELF
SLAB_T = 0.240                  # nominal thickness (PQ concrete under 44 t)
BED_Z = -0.048                  # visible sub-base surface, seen only through the
                                # joints and the spalls
SKIRT_Z = -0.072                # bay soffit: BELOW the bed, so no line of sight
                                # under a slab can ever reach open sky
SUBSLAB_Z = -SLAB_T             # formation level, not modelled (never visible)

# THE JOINTS.  A modern contraction joint is a two-stage cut: an early-entry
# 6 mm kerf that induces the crack, then a wider shallow reservoir sawn later to
# hold a sealant with a sane shape factor.  Both are modelled: the reservoir is
# what you see, the kerf is what you see at the bottom of it.
JOINT_KERF_W = 0.0060           # induced-crack kerf
JOINT_KERF_D = 0.0620           # = D/4 + a little; below the reservoir
JOINT_SAWN_W = 0.0100           # transverse sealant reservoir, top width
JOINT_SAWN_D = 0.0200           # reservoir depth (2 : 1 shape factor)
JOINT_FORMED_W = 0.0120         # longitudinal tie-bar joint between lanes
JOINT_FORMED_D = 0.0230
JOINT_ISOL_W = 0.0200           # isolation joint at a structure
JOINT_ISOL_D = 0.0400

# ARRISES.  A sawn joint has no chamfer at all — only the 1.2 mm of micro-spall
# the blade leaves.  A tooled longitudinal joint has a real quarter-round.  The
# difference between those two lines is most of what says "this was built in
# stages" at 2196 px/m.
ARRIS_SAWN_M = 0.0012
ARRIS_FORMED_R = 0.0045
ARRIS_ISOL_R = 0.0060
EDGE_ARRIS_CHAMFER_M = 0.0150   # the outer road edge: a slipform edge slumps and
                                # is then tooled, giving a soft 15 mm arris

# SEALANT
SEAL_RECESS = (0.0022, 0.0050)  # how far the sealant surface sits below the arris
SEAL_MENISCUS = 0.0018          # depth of the concave dish in the middle
SEAL_OVERBAND_W = (0.045, 0.075)  # a re-sealed joint gets a band spread ON the slab
SEAL_OVERBAND_H = 0.0030
FRAC_UNSEALED = 0.14            # joints whose sealant has failed and gone
FRAC_OVERBANDED = 0.17          # joints re-sealed with an overband

# BAY LEVELS.  The whole road is a declared plane at z = 0.000 for its first
# 49.6 m, so this envelope is TIGHT — much tighter than a paddock apron's.  The
# ceiling is held below build_architecture's MARK_Z = 0.0075 so a marking laid on
# this road never z-fights it, and the floor is held so a 20 mm embedded object
# (C.BASE_EMBED_M) still has 10 mm of concrete under it at the lowest bay.
#
#   THE ENVELOPE IS SOLVED, NOT GUESSED.  Four terms move the concrete off the
#   contract datum, and their amplitudes are budgeted so their SUM cannot leave
#   the declared envelope:
#
#       bay datum offset   dz      -0.0064 .. +0.0010   (the level walk)
#       screed wave                       +- 0.0016
#       bay tilt                          +- 0.0016
#       daytime curl                  -0.0022 .. 0      (edges down, one-signed)
#       -----------------------------------------------------------------
#       total                      -0.0118 .. +0.0042
#
#   +4.2 mm is 3.3 mm below build_architecture's MARK_Z; -11.8 mm still leaves
#   8.2 mm of concrete under a C.BASE_EMBED_M object.  Both ends are MEASURED on
#   the built mesh by verify(), because a budget is an intention until it is.
SLAB_TOP_MAX_M = 0.0042
SLAB_TOP_MIN_M = -0.0118
LEVEL_DZ_MAX = 0.0010
LEVEL_DZ_MIN = -0.0064
LEVEL_STEP_CAP_M = 0.0060       # bay-to-bay datum step the level walk may take
FAULT_DOWELLED_M = 0.0045       # step across a dowelled transverse joint
FAULT_UNDOWELLED_M = 0.0110     # ... and across the few that lost their dowels
FRAC_UNDOWELLED = 0.09
CURL_LEN_M = 0.42               # how far in from a joint a slab curls
CURL_MAX_M = 0.0022             # daytime curl: hot top, edges DOWN, centre up
SCREED_WAVE_L = (1.9, 3.4)      # slipform screed oscillation wavelength
SCREED_WAVE_A = 0.0016          # ... and amplitude

RECESS_LIP_M = 0.004            # seating shoulder for a cover frame
KERB_SEAT_M = 0.125             # kerb top above the slab arris (half-battered)

# THE FINISH.  The manifest's second variation axis is "broom-finish direction",
# and on a road that is not decoration: a bay is broomed by one person walking
# one way, and the direction he walked is legible forever at a 12.47 deg sun.
FIN_TRANS = 0       # grooves ACROSS the road — the normal road finish
FIN_LONG = 1        # grooves ALONG the road — a bay finished from the edge
FIN_SKEW = 2        # transverse but dragged 7..17 deg off square
FIN_BURLAP = 3      # burlap/hessian drag: 4-6 mm pitch, a third of the depth
FIN_FLOAT = 4       # hand-floated smooth — an infill bay, or one it rained on
FIN_ASPH = 5        # the bay was taken out and replaced in cold-mix asphalt
FIN_WEIGHTS = (0.50, 0.15, 0.14, 0.11, 0.075, 0.025)
FIN_NAMES = ("transverse", "longitudinal", "skewed", "burlap", "floated",
             "asphalt_patch")

BROOM_PITCH = (0.0125, 0.0142, 0.0160, 0.0182)   # bristle spacing, per bay
BROOM_DEPTH = (0.00095, 0.00225)                 # groove depth range
BROOM_DUTY = 0.55                                # groove width / pitch
#   MEASURED ON THE FIRST HERO MACRO: at 0.36 the grooves rendered as thin dark
#   RULED LINES with a wide flat land between them — corrugated card, not
#   concrete.  A stiff broom dragged through green concrete leaves grooves that
#   nearly touch; 0.55 duty at a 14.2 mm pitch is a 7.8 mm groove and a 6.4 mm
#   land, which is what a straightedge laid across a real one measures.
BURLAP_PITCH = (0.0042, 0.0058)
BURLAP_DEPTH = (0.00018, 0.00044)
BROOM_PASS_W = (0.62, 0.78, 0.95)                # broom head width -> pass seams
BROOM_SKEW_DEG = (7.0, 17.0)
EDGE_TROWEL_M = (0.018, 0.042)                   # smooth margin the edger leaves
                                                 # along every joint — a hard,
                                                 # bright band 40..92 px wide
BROOM_WANDER_A = 0.0009                          # how far a groove line wanders
BROOM_WANDER_L = 0.42                            # ... over this along-groove run

# SURFACE HISTORY
TOOTH_CELL = (0.0060, 0.0095)   # mortar/sand cell size
TOOTH_A = 0.00062               # ... and its relief (0.48 px of shadow; the rest
                                # of the grain is bump, and only the rest)
POPOUT_CELL = 0.048             # one candidate popout per cell
FRAC_POPOUT = 0.048             # ... of which this many actually popped
POPOUT_R = (0.0032, 0.0080)     # crater semi-axis ACROSS the grooves
POPOUT_ELONG = (1.6, 3.1)       # ... and how much longer it is ALONG them,
                                # because a spall on a broomed slab runs with the
                                # corduroy and not across it
POPOUT_D = (0.0012, 0.0040)
CRAZE_CELL = (0.075, 0.180)     # plastic-shrinkage map cracking cell size
CRAZE_W = 0.0026
CRAZE_D = (0.00048, 0.00120)
FRAC_CRACKED = 0.11             # bays with a through crack
FRAC_CORNER_BREAK = 0.045       # bays with a broken corner
CRACK_W = (0.0018, 0.0060)
CRACK_D = (0.0055, 0.0130)
FRAC_REINSTATED = 0.035         # bays taken out and re-cast (new, pale, floated)

# TRAFFIC.  A private shakedown's access road: transporters, a recovery truck, a
# van, and once, a car.  Two travel lanes, wheel paths at a 1.98 m track.
TRAVEL_V = (-2.55, +2.55)
TRACK_GAUGE_M = 1.98
TRACK_HALF_W = 0.155
POLISH_MAX = 0.62               # how much of the broom groove traffic has taken
FRAC_SCUFF = 0.05               # bays carrying a turning scuff arc

# LOD.  See `_pitch_fine` / `_pitch_coarse`.  The grid is ANISOTROPIC and aligned
# to the broom: fine across the grooves, coarse along them.  A broom finish is a
# 1-D feature and meshing it isotropically spends 5x the triangles on the axis
# that carries no information.
PITCH_FINE_PX = 2.2             # screen px per sample ACROSS the grooves
PITCH_COARSE_PX = 6.0           # ... and ALONG them
PITCH_FINE_MIN = 0.00090
PITCH_FINE_MAX = 0.045
PITCH_COARSE_MIN = 0.0034
PITCH_COARSE_MAX = 0.130
# WHY THE ANISOTROPY IS 3.4 : 1 AND NOT 5 : 1.  The broom groove itself needs
# nothing along its length, and at 9 px of coarse spacing it still looked right —
# but the CRAZING does not run with the grooves.  A 2.2 mm hairline whose normal
# points along the coarse axis was being sampled at 4.8 mm and came out dotted.
# 3.4 mm costs 1.4x the vertices in the near band and the frustum penalty pays
# for it; what is left below 3.4 mm is carried by the crazing term in
# mat_concrete's bump, which is the right place for a sub-3-pixel line.
GROOVE_MESH_R = 16.0            # inside this radius the broom groove is MESH.
#   MEASURED ON THE CORRIDOR SHOT — the one the film actually takes, 1.7 m off
#   the deck looking 40 m down the road.  At 11 m the corduroy stopped dead and
#   everything beyond it was smooth concrete, which is the "barrier is a smooth
#   tube" defect with a different surface.  A 14.2 mm pitch at 16 m is still
#   3.3 screen px on the 4K master, so it is a FEATURE out to there and the mesh
#   has to carry it.  Past 16 m it is under 3 px and the loss is honest.
EDGE_ZONE_M = 0.055             # width of the fine band held along every joint
EDGE_PITCH_M = 0.0011           # ... and its spacing, so the arris, the chamfer
                                # and the spall exist on EVERY bay however coarse
                                # its middle is
EDGE_PITCH_FAR_M = 0.0060       # ... relaxed beyond FAR_R
FAR_R = 55.0
VERT_BUDGET = 11_000_000        # ceiling on the explicit field, so a careless
                                # anchor cannot make a 40 GB blend on an 11 GB box

# THE VERTEX CHANNELS.  Twelve masks, packed into three FLOAT_COLOR point
# attributes rather than twelve float layers: same bytes, a quarter of the
# foreach_set calls, and one Attribute node per four channels in the shader.
# `bake_attrs` is the public way to write them, so the packing stays an
# implementation detail behind a stable name.
ATTR_LAYERS = (("ars1", ("pol", "dst", "dmp", "arr")),
               ("ars2", ("oil", "scf", "lat", "rst")),
               ("ars3", ("exp", "saw", "dmg", "hgt")))
ATTRS = tuple(c for _n, ch in ATTR_LAYERS for c in ch)
# Per-BAY constants do not need a per-vertex channel and do not get one:
#   Object Info -> Random   decorrelates every procedural per bay
#   Object Info -> Color    carries (finish/5, age, crazing, bay random)
# which is why a 2 M-vertex bay costs 48 bytes/vertex of masks and not 80.
OBJCOL_DOC = "(fin/5, age, craze, rnd)"

# BED
BED_PITCH = 0.28                # the sub-base is only ever seen through a 10 mm
                                # slot; its relief belongs in mat_subbase's bump


# =============================================================================
# 2.  NUMERIC PLUMBING — hashes, noise, worley, all vectorised
# =============================================================================
_HK = (np.uint64(0x9E3779B97F4A7C15), np.uint64(0xC2B2AE3D27D4EB4F),
       np.uint64(0x165667B19E3779F9), np.uint64(0x27D4EB2F165667C5),
       np.uint64(0x85EBCA77C2B2AE63), np.uint64(0xD6E8FEB86659FD93))
_U32 = np.uint64(32)
_U29 = np.uint64(29)
_U31 = np.uint64(31)


def _h(*keys):
    """Deterministic float64 in [0, 1) from integer arrays / scalars.  Vectorised.

    splitmix64's finaliser in unsigned arithmetic: it wraps silently instead of
    tripping numpy's signed-overflow warning on every call, and it decorrelates
    the low bits, which a plain multiply-shift does not.  The +2^40 bias makes
    negative lattice coordinates legal — cell (-3, -7) is a real cell and the
    route's v axis is signed.
    """
    n = np.uint64(0)
    for i, k in enumerate(keys):
        a = np.asarray(k)
        a = (np.rint(a).astype(np.int64) if a.dtype.kind == "f"
             else a.astype(np.int64))
        a = (a + (1 << 40)).astype(np.uint64)
        n = n ^ (a * _HK[i % len(_HK)])
        n = (n ^ (n >> _U31)) * _HK[(i + 3) % len(_HK)]
    n = (n ^ (n >> _U32)) * _HK[1]
    n = (n ^ (n >> _U29)) * _HK[4]
    n = n ^ (n >> _U32)
    return (n >> np.uint64(11)).astype(np.float64) * (1.0 / 9007199254740992.0)


def _hf(*keys):
    """Scalar convenience: _h on python ints -> python float."""
    return float(_h(*[np.array(k) for k in keys]))


def _vn2(x, y, seed):
    """Value noise on the unit lattice, quintic-smoothed.  [0, 1)."""
    ix = np.floor(x); iy = np.floor(y)
    fx = x - ix; fy = y - iy
    ux = fx * fx * fx * (fx * (fx * 6.0 - 15.0) + 10.0)
    uy = fy * fy * fy * (fy * (fy * 6.0 - 15.0) + 10.0)
    ix = ix.astype(np.int64); iy = iy.astype(np.int64)
    a = _h(ix, iy, seed); b = _h(ix + 1, iy, seed)
    c = _h(ix, iy + 1, seed); d = _h(ix + 1, iy + 1, seed)
    return (a * (1 - ux) + b * ux) * (1 - uy) + (c * (1 - ux) + d * ux) * uy


def _fbm2(x, y, seed, oct=4, lac=2.03, gain=0.5):
    tot = np.zeros(np.broadcast(x, y).shape); amp = 1.0; nrm = 0.0
    fx, fy = x, y
    for i in range(oct):
        tot = tot + amp * _vn2(fx, fy, seed + i * 7919)
        nrm += amp
        amp *= gain
        fx = fx * lac; fy = fy * lac
    return tot / nrm


def _vn1(x, seed):
    ix = np.floor(x); fx = x - ix
    u = fx * fx * fx * (fx * (fx * 6.0 - 15.0) + 10.0)
    ix = ix.astype(np.int64)
    return _h(ix, seed) * (1 - u) + _h(ix + 1, seed) * u


def _worley(x, y, seed, jitter=1.0, want=("f1",)):
    """Worley / cellular noise.  Returns a dict of the requested features.

    'f1'   distance to the nearest feature point
    'f2'   distance to the second nearest
    'id'   a 0..1 hash of the owning cell
    'cx','cy'  the feature point itself, so a crater can be placed ON it
    """
    ix = np.floor(x).astype(np.int64); iy = np.floor(y).astype(np.int64)
    f1 = np.full(x.shape, 1e9); f2 = np.full(x.shape, 1e9)
    bx = np.zeros(x.shape, np.int64); by = np.zeros(x.shape, np.int64)
    px = np.zeros(x.shape); py = np.zeros(x.shape)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            cx = ix + dx; cy = iy + dy
            ox = _h(cx, cy, seed) * jitter + (0.5 - 0.5 * jitter)
            oy = _h(cx, cy, seed + 4483) * jitter + (0.5 - 0.5 * jitter)
            qx = cx + ox; qy = cy + oy
            d = (qx - x) ** 2 + (qy - y) ** 2
            closer = d < f1
            f2 = np.where(closer, f1, np.minimum(f2, d))
            bx = np.where(closer, cx, bx); by = np.where(closer, cy, by)
            px = np.where(closer, qx, px); py = np.where(closer, qy, py)
            f1 = np.where(closer, d, f1)
    out = {}
    if "f1" in want:
        out["f1"] = np.sqrt(f1)
    if "f2" in want:
        out["f2"] = np.sqrt(f2)
    if "id" in want:
        out["id"] = _h(bx, by, seed + 90210)
    if "cx" in want:
        out["cx"] = px; out["cy"] = py; out["bx"] = bx; out["by"] = by
    return out


def _sstep(e0, e1, x):
    """Smoothstep that also works DESCENDING (e0 > e1).

    The obvious `max(e1 - e0, 1e-12)` guard silently turns a descending ramp
    into a step function at e0, which is how a "traffic thins toward the gore"
    term became "traffic everywhere".  Guard the magnitude, keep the sign.
    """
    d = float(e1) - float(e0)
    if abs(d) < 1e-12:
        d = math.copysign(1e-12, d if d else 1.0)
    t = np.clip((x - e0) / d, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def _pick(seq, u):
    """Deterministic choice from a tuple by a 0..1 hash."""
    i = int(np.clip(u, 0.0, 0.999999) * len(seq))
    return seq[i]


def _pick_w(seq, weights, u):
    c = 0.0
    for v, w in zip(seq, weights):
        c += w
        if u < c:
            return v
    return seq[-1]


def _lerp(a, b, u):
    return a + (b - a) * u


def _srgb(hexstr):
    """'#a1b2c3' -> linear RGB triple.  Every colour in this file is written as
    the sRGB value a paint chip would carry and converted here, so the numbers in
    the source are ones a human can check against a real material."""
    h = hexstr.lstrip("#")
    out = []
    for i in range(3):
        c = int(h[2 * i:2 * i + 2], 16) / 255.0
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return tuple(out)


# =============================================================================
# 3.  THE RIBBON — the contract's footprint, sampled once and cached
# =============================================================================
#
# `BS._access_layout` is the authoritative boundary of the pit-exit ribbon: the
# contract edges `C.access_edges`, plus the 0.30 m sawn edge strip where the
# neighbour is architecture's paving, plus three fixed-point passes that push the
# inboard edge off the racing surface (without them 126 vertices of the ribbon
# lie up to 50 mm ON SURF_Track around t = 125).  Re-deriving any of that here
# would be a second opinion about a boundary that already has an owner, so it is
# called, not copied.

_RIB = None


def ribbon(ds=0.25):
    """Cached ribbon tables: T, X, Y, H, lo, hi at `ds` metres of route."""
    global _RIB
    if _RIB is None or abs(_RIB["ds"] - ds) > 1e-9:
        L = BS._access_layout(ds=ds, nc=2)
        _RIB = dict(ds=ds, T=L["T"], X=L["X"], Y=L["Y"], H=L["H"],
                    lo=L["lo"], hi=L["hi"], vin=L["vin"], vout=L["vout"],
                    saw_in=L["saw_in"], saw_out=L["saw_out"],
                    free_in=L["free_in"])
    return _RIB


def edge_v(t):
    """-> (lo, hi): the ribbon's inboard and outboard lateral edges at station t.

    lo is the RIGHT-of-travel (track-side) edge and is the more negative one.
    Both include the sawn edge strip exactly where build_surface lays it.
    """
    R = ribbon()
    t = np.atleast_1d(np.asarray(t, float))
    return (np.interp(t, R["T"], R["lo"]), np.interp(t, R["T"], R["hi"]))


def route_frame(t):
    """-> (x, y, heading) at station t, interpolated from the cached table."""
    R = ribbon()
    t = np.atleast_1d(np.asarray(t, float))
    return (np.interp(t, R["T"], R["X"]), np.interp(t, R["T"], R["Y"]),
            np.interp(t, R["T"], R["H"]))


def route_xy(t, v):
    """(route station, lateral) -> world (x, y).  v is positive LEFT of travel."""
    X, Y, H = route_frame(t)
    v = np.asarray(v, float)
    return (X - np.sin(H) * v, Y + np.cos(H) * v)


# --- the contract datum, tabulated ------------------------------------------
# `C.access_z` is exact but expensive: it projects every point onto the 3675 m
# lap.  At 10^7 surface samples that is not affordable and not necessary — the
# datum's shortest wavelength is `C._undulation`'s 4.8 m term, so a 0.20 m table
# resolves it 24x over.  The interpolation error is MEASURED by verify() against
# `C.world_ground_z` at random points, not assumed.
#
# THE STEP IS MEASURED, NOT ASSUMED.  At 0.20 x 0.20 m the table disagreed with
# `C.access_z` by up to 0.883 mm — not at the smooth undulation, which a 0.20 m
# step resolves 24x over, but at the KINKS: `ground_z` is only C0 where the
# painted verge starts to drain harder and where the apron tie takes over, and
# interpolating across a kink loses error linearly in h, not quadratically.  So
# the step is 0.10 x 0.05 m and verify() reports what that actually bought.
_DTAB = None
_DT_T0, _DT_DT = 0.0, 0.10
_DT_V0, _DT_DV = -7.0, 0.05


def _datum_table():
    global _DTAB
    if _DTAB is None:
        nt = int(math.ceil((C.ACCESS_TOTAL + 1.0 - _DT_T0) / _DT_DT)) + 1
        nv = int(math.ceil((7.0 - _DT_V0) / _DT_DV)) + 1
        T = _DT_T0 + np.arange(nt) * _DT_DT
        V = _DT_V0 + np.arange(nv) * _DT_DV
        TT, VV = np.meshgrid(T, V, indexing="ij")
        Z = C.access_z(TT.ravel(), VV.ravel()).reshape(TT.shape)
        _DTAB = dict(T=T, V=V, Z=Z, nt=nt, nv=nv)
    return _DTAB


def datum_z(t, v):
    """The CONTRACT's ribbon surface at (t, v) — exactly 0.000 for t <= 49.60.

    This is `C.access_z`, which is what `C.world_ground_z` returns inside the
    ribbon.  Nothing in this module ever assumes a z.
    """
    D = _datum_table()
    t = np.asarray(t, float); v = np.asarray(v, float)
    ft = np.clip((t - _DT_T0) / _DT_DT, 0, D["nt"] - 1.0001)
    fv = np.clip((v - _DT_V0) / _DT_DV, 0, D["nv"] - 1.0001)
    i0 = ft.astype(np.int64); j0 = fv.astype(np.int64)
    a = ft - i0; b = fv - j0
    Z = D["Z"]
    return ((Z[i0, j0] * (1 - a) + Z[i0 + 1, j0] * a) * (1 - b)
            + (Z[i0, j0 + 1] * (1 - a) + Z[i0 + 1, j0 + 1] * a) * b)


# =============================================================================
# 4.  THE LAYING PLAN — rows, lanes, bays
# =============================================================================
class Bay:
    """One pour bay.  Everything about it is a pure function of (seed, row, lane).

    A dependant can therefore recompute the whole road without this module
    having emitted a single vertex.
    """
    __slots__ = ("idx", "row", "lane", "t0", "t1", "va", "vb",
                 "dz", "tilt_t", "tilt_v", "curl", "screed_l", "screed_p",
                 "fin", "phi", "bpitch", "bdepth", "duty", "pass_w", "pass_ph",
                 "trowel", "rnd", "age", "exp", "dst", "dmp", "lat", "oil",
                 "scf", "rst", "craze", "craze_cell", "crack", "corner",
                 "reinst", "undowelled", "tc", "vc", "area", "kind")

    def __init__(self, **kw):
        for k in self.__slots__:
            setattr(self, k, kw.get(k))

    def world_centre(self):
        x, y = route_xy(np.array([self.tc]), np.array([self.vc]))
        return float(x[0]), float(y[0])

    def span_v(self, t):
        """The bay's concrete edges at station t, clipped to the ribbon and set
        back by half a joint on every interior side."""
        lo, hi = edge_v(t)
        a = np.maximum(self.va, lo)
        b = np.minimum(self.vb, hi)
        # the interior lane joints are real slots; the ribbon edge is not
        if self.va > LANE_EDGES_V[0] + 1e-6:
            a = a + JOINT_FORMED_W * 0.5
        if self.vb < LANE_EDGES_V[-1] - 1e-6:
            b = b - JOINT_FORMED_W * 0.5
        return a, b

    def __repr__(self):
        return ("Bay(%d r%d l%d t %.2f-%.2f v %.2f-%.2f %s)"
                % (self.idx, self.row, self.lane, self.t0, self.t1,
                   self.va, self.vb, FIN_NAMES[self.fin]))


def row_stations(seed=SEED):
    """The transverse joint stations, in metres from the glass plane.

    The saw crew works to a chalk line that moves when it meets a structure, so
    the sequence is three canonical spacings chosen by hash — never a jitter
    around a mean, which would make no two bays the same size, which is true of
    nothing that was ever set out with a tape.  Two structures force a joint:
    the showroom threshold at t = 0 and the pit-exit portal at world x = +58.
    """
    R = ribbon()
    t_end = float(R["T"][-1])
    forced = sorted(set(round(f, 4) for f in FORCED_JOINT_T if 0.0 < f < t_end))
    stations = [0.0]
    k = 0
    while stations[-1] < t_end - 0.35:
        t = stations[-1]
        nxt = _pick(BAY_L, _hf(k, 7717, seed))
        cand = t + nxt
        # snap onto a forced joint if we are about to step over one
        for f in forced:
            if t < f - 1e-6 and cand > f - 0.55:
                cand = f
                break
        stations.append(min(cand, t_end))
        k += 1
    if t_end - stations[-1] < 0.9 and len(stations) > 2:
        stations[-1] = t_end
    else:
        stations.append(t_end)
    return np.array(sorted(set(round(s, 5) for s in stations)))


def _level_field(nrow, seed=SEED):
    """Bay datum offsets, bounded so their sum with tilt/curl/screed cannot leave
    the declared envelope.  Long-wavelength across the field (the sub-base
    settles in patches, not per bay) plus a per-bay component (the screed rail
    was set by eye)."""
    r = np.arange(nrow)[:, None].astype(float)
    l = np.arange(N_LANE)[None, :].astype(float)
    base = (_fbm2(r / 6.5, l / 2.1, seed + 311, oct=3) - 0.5) * 2.0
    fine = (_h(np.arange(nrow)[:, None], np.arange(N_LANE)[None, :],
               seed + 977) - 0.5) * 2.0
    raw = np.clip(base * 0.66 + fine * 0.34, -1.0, 1.0)
    mid = 0.5 * (LEVEL_DZ_MAX + LEVEL_DZ_MIN)
    half = 0.5 * (LEVEL_DZ_MAX - LEVEL_DZ_MIN)
    dz = mid + raw * half
    # bound the neighbour step: a paving crew that left a 9 mm lip would be back
    # to grind it.  Iterated because clamping one pair can open another.
    for _ in range(24):
        moved = 0.0
        for ax in (0, 1):
            d = np.diff(dz, axis=ax)
            over = np.abs(d) - LEVEL_STEP_CAP_M
            if over.max() <= 0:
                continue
            corr = np.sign(d) * np.maximum(over, 0.0) * 0.5
            if ax == 0:
                dz[:-1] += corr; dz[1:] -= corr
            else:
                dz[:, :-1] += corr; dz[:, 1:] -= corr
            moved = max(moved, float(over.max()))
        if moved <= 1e-9:
            break
    return np.clip(dz, LEVEL_DZ_MIN, LEVEL_DZ_MAX)


def bay_layout(seed=SEED):
    """The whole road, as bays.  Deterministic: same seed, same road, forever."""
    st = row_stations(seed)
    nrow = len(st) - 1
    dzf = _level_field(nrow, seed)

    # --- which (row, lane) cells actually exist ------------------------------
    # THE OUTER LANES RUN TO THE RIBBON, NOT TO +-6.0.  `edge_v` already carries
    # the 0.30 m sawn edge strip build_surface lays where the neighbour is
    # architecture's paving, so lane 0 and lane N-1 are given sentinel bounds and
    # the clip decides.  Without this the strip is simply not built and the
    # 0.30 m slot world_contract 1.0.1 closed reopens on this module's side.
    # THE LANES ARE CUT FROM THE RIBBON, NOT STAMPED ONTO IT.
    #
    # The first version tested each 3.0 m lane against the ribbon and DROPPED it
    # where the clipped width fell below 0.16 m.  Measured on 100 000 stratified
    # samples that left 11.94 % of the ribbon with no concrete on it: the last
    # 30 m of the gore, where the whole road has narrowed to a 20..160 mm nose,
    # had no bay at all.  0.18 % of the AREA and 100 % of a hole in a surface the
    # car crosses at 130 km/h.
    #
    # So the lane boundaries are the subset of LANE_EDGES_V that still has 0.16 m
    # of ribbon either side of it, and the outer two segments run to the ribbon
    # edge on sentinel bounds.  The segments then tile [lo, hi] EXACTLY at every
    # station by construction, a 12 m row gets its four 3.0 m lanes, and a 90 mm
    # nose gets one hand-formed closure strip — which is also what a real paving
    # gang would do with it.
    cand = []
    for r in range(nrow):
        t0, t1 = float(st[r]), float(st[r + 1])
        tc = 0.5 * (t0 + t1)
        lo, hi = edge_v(np.array([t0, tc, t1]))
        lo_max = float(lo.max()); hi_min = float(hi.min())
        # THE TEST IS ON THE ROW'S WIDEST STATION, NOT ITS NARROWEST.  Using
        # hi_min - lo_max here left the last 7.0 m of the gore unbuilt, because
        # `BS._access_layout` only guarantees 20 mm of width PER STATION and the
        # row minimum dips under it.  `_bay_span_arrays` floors the width at
        # 10 mm, so a sliver row is legal geometry and a missing one is a hole.
        if float((hi - lo).max()) < 0.005:
            continue
        interior = [e for e in LANE_EDGES_V[1:-1]
                    if lo_max + 0.16 < e < hi_min - 0.16]
        bounds = [-9.0] + interior + [9.0]
        for k in range(len(bounds) - 1):
            va, vb = bounds[k], bounds[k + 1]
            a = np.maximum(va, lo); b = np.minimum(vb, hi)
            w = np.clip(b - a, 0.0, None)
            wmean = float(w.mean())
            vmid = 0.5 * (float(a[1]) + float(b[1]))
            l = int(np.clip(np.searchsorted(np.array(LANE_EDGES_V), vmid,
                                            side="right") - 1, 0, N_LANE - 1))
            cand.append((r, l, t0, t1, tc, va, vb, wmean,
                         float(a[1]), float(b[1])))

    # --- the RARE histories are rank-selected, not coin-flipped --------------
    # A 3.5 % coin on a (row, lane) lattice most of whose cells are in the gore
    # produced ZERO reinstated bays out of 159 — a declared variation axis that
    # simply did not exist in the built road, and the kind of thing that is only
    # ever noticed by counting it back out.  Ranking the bays that EXIST by hash
    # and taking the lowest k makes the declared rate a construction instead of
    # an expectation, and it stays deterministic in the seed.
    def _rank_select(frac, salt):
        n = int(round(frac * len(cand)))
        if n <= 0:
            return set()
        order = sorted(range(len(cand)),
                       key=lambda i: _hf(cand[i][0], cand[i][1], salt))
        return {(cand[i][0], cand[i][1]) for i in order[:n]}

    reinst_set = _rank_select(FRAC_REINSTATED, seed + 83)
    corner_set = _rank_select(FRAC_CORNER_BREAK, seed + 541)
    scuff_set = _rank_select(FRAC_SCUFF, seed + 463)

    bays = []
    idx = 0
    for (r, l, t0, t1, tc, va, vb, wmean, amid, bmid) in cand:
        u = _h(np.array(r), np.array(l), np.array(seed))
        rnd = float(u)
        fin = _pick_w(range(6), FIN_WEIGHTS, _hf(r, l, seed + 41))
        # a re-cast bay is always hand-floated, and an asphalt patch has no
        # broom at all: the finish and the history are not independent
        reinst = (r, l) in reinst_set
        if reinst and fin not in (FIN_FLOAT, FIN_ASPH):
            fin = FIN_FLOAT
        uphi = _hf(r, l, seed + 127)
        if fin == FIN_LONG:
            phi = math.radians(90.0 + (uphi - 0.5) * 8.0)
        elif fin == FIN_SKEW:
            s = 1.0 if _hf(r, l, seed + 131) < 0.5 else -1.0
            phi = math.radians(s * _lerp(BROOM_SKEW_DEG[0],
                                         BROOM_SKEW_DEG[1], uphi))
        elif fin == FIN_BURLAP:
            phi = math.radians((uphi - 0.5) * 6.0)
        else:
            phi = math.radians((uphi - 0.5) * 3.0)
        if fin == FIN_BURLAP:
            bp = _lerp(BURLAP_PITCH[0], BURLAP_PITCH[1], _hf(r, l, seed + 211))
            bd = _lerp(BURLAP_DEPTH[0], BURLAP_DEPTH[1], _hf(r, l, seed + 213))
            duty = 0.52
        elif fin in (FIN_FLOAT, FIN_ASPH):
            bp = 0.0142; bd = 0.0; duty = BROOM_DUTY
        else:
            bp = _pick(BROOM_PITCH, _hf(r, l, seed + 217))
            bd = _lerp(BROOM_DEPTH[0], BROOM_DEPTH[1], _hf(r, l, seed + 219))
            duty = BROOM_DUTY * _lerp(0.82, 1.18, _hf(r, l, seed + 223))
        # fbm returns 0.30..0.70 for almost every cell, so using it raw put
        # every bay in the middle of the age range and NOTHING crazed: measured
        # crazing was 0.000 on the macro bay and on its four neighbours.  The
        # field is remapped onto the full 0..1 so the road has genuinely old
        # panels and genuinely young ones, which is what a 40-year pit exit that
        # has been patched twice actually looks like.
        age = float(np.clip((_fbm2(np.array(r / 9.0), np.array(l / 3.0),
                                   seed + 331, oct=3) - 0.30) * 2.35, 0.0, 1.0))
        if reinst:
            age *= 0.22
        b_ = Bay(
            idx=idx, row=r, lane=l, t0=t0, t1=t1, va=va, vb=vb,
            tc=tc, vc=0.5 * (amid + bmid),
            area=wmean * (t1 - t0),
            dz=float(dzf[r, l]),
            tilt_t=(_hf(r, l, seed + 401) - 0.5) * 2.0,
            tilt_v=(_hf(r, l, seed + 403) - 0.5) * 2.0,
            curl=_lerp(0.35, 1.0, _hf(r, l, seed + 407)),
            screed_l=_lerp(SCREED_WAVE_L[0], SCREED_WAVE_L[1],
                           _hf(r, l, seed + 409)),
            screed_p=_hf(r, l, seed + 411) * 6.2831853,
            fin=fin, phi=phi, bpitch=bp, bdepth=bd, duty=duty,
            pass_w=_pick(BROOM_PASS_W, _hf(r, l, seed + 431)),
            pass_ph=_hf(r, l, seed + 433),
            trowel=_lerp(EDGE_TROWEL_M[0], EDGE_TROWEL_M[1],
                         _hf(r, l, seed + 437)),
            rnd=rnd, age=age,
            exp=float(np.clip(0.10 + 0.55 * age
                              + 0.25 * (_hf(r, l, seed + 439) - 0.5), 0, 1)),
            dst=float(np.clip(_fbm2(np.array(r / 5.0), np.array(l / 2.0),
                                    seed + 443, oct=3) * 1.25 - 0.12, 0, 1)),
            dmp=float(np.clip(_fbm2(np.array(r / 7.5), np.array(l / 2.6),
                                    seed + 449, oct=3) * 1.5 - 0.45, 0, 1)),
            lat=_hf(r, l, seed + 457),
            oil=(_hf(r, l, seed + 461) ** 3.2),
            scf=(1.0 if _hf(r, l, seed + 463) < FRAC_SCUFF else 0.0)
                * _hf(r, l, seed + 467),
            rst=_hf(r, l, seed + 471) ** 2.0,
            # MEASURED: with the 0.42..0.92 gate the hero bay came out at
            # craze = 0.017 and its four neighbours at zero — the map cracking
            # existed in the code and nowhere in the frame.  Plastic-shrinkage
            # crazing is not rare; it is on most hand-finished concrete that was
            # closed on a windy afternoon.  The gate opens at 0.15 and about two
            # thirds of the road carries some.
            craze=float(_sstep(0.15, 0.70, age)
                        * (0.25 + 0.75 * _hf(r, l, seed + 479))),
            craze_cell=_lerp(CRAZE_CELL[0], CRAZE_CELL[1],
                             _hf(r, l, seed + 481)),
            crack=None, corner=None,
            reinst=reinst,
            undowelled=(_hf(r, seed + 487) < FRAC_UNDOWELLED),
            kind="bay",
        )
        # --- the crack history --------------------------------------------
        # A through crack forms in the middle third of the longest dimension
        # and it is more likely on an old bay than a new one, which is why
        # `age` gates it rather than a flat coin.
        if not reinst and _hf(r, l, seed + 491) < FRAC_CRACKED * (0.4 + 1.2 * age):
            # THE CRACK MUST BE SAMPLED BY THE FINE AXIS.  A 2 mm crack whose
            # normal points along the coarse axis is aliased into a dashed line.
            # This is not a compromise: a mid-panel crack in jointed plain
            # concrete forms parallel to the SHORTER joint direction, which on a
            # 3.0 x 3.7 m panel is transverse, which is also the direction a
            # transverse broom makes fine.  The two agree.
            across_t = abs(math.cos(phi)) >= abs(math.sin(phi))
            b_.crack = dict(
                across_t=across_t,
                pos=_lerp(0.34, 0.66, _hf(r, l, seed + 497)),
                wander=_lerp(0.06, 0.20, _hf(r, l, seed + 499)),
                w=_lerp(CRACK_W[0], CRACK_W[1], _hf(r, l, seed + 503)),
                d=_lerp(CRACK_D[0], CRACK_D[1], _hf(r, l, seed + 509)),
                seal=(_hf(r, l, seed + 521) < 0.45),
                seed=int(_hf(r, l, seed + 523) * 1e6))
        if not reinst and (r, l) in corner_set:
            b_.corner = dict(
                which=int(_hf(r, l, seed + 547) * 4) % 4,
                r=_lerp(0.16, 0.42, _hf(r, l, seed + 557)),
                d=_lerp(0.006, 0.020, _hf(r, l, seed + 563)),
                seed=int(_hf(r, l, seed + 569) * 1e6))
        bays.append(b_)
        idx += 1
    return bays


_BAY_INDEX = None


def _index_bays(bays):
    global _BAY_INDEX
    rows = {}
    for b in bays:
        rows.setdefault(b.row, []).append(b)
    ts = sorted({(b.t0, b.t1, b.row) for b in bays})
    _BAY_INDEX = dict(rows=rows, ts=np.array([x[0] for x in ts]),
                      te=np.array([x[1] for x in ts]),
                      rid=np.array([x[2] for x in ts]), bays=bays)
    return _BAY_INDEX


def bay_at(t, v, bays=None):
    """-> the Bay containing route point (t, v), or None."""
    if _BAY_INDEX is None or (bays is not None and _BAY_INDEX["bays"] is not bays):
        _index_bays(bays if bays is not None else bay_layout())
    ix = _BAY_INDEX
    j = int(np.searchsorted(ix["ts"], t, side="right") - 1)
    if j < 0 or j >= len(ix["ts"]):
        return None
    for b in ix["rows"].get(int(ix["rid"][j]), ()):
        if b.va - 1e-9 <= v <= b.vb + 1e-9:
            return b
    return None


# =============================================================================
# 5.  THE SURFACE — the level a surveyor's staff reads
# =============================================================================
def _bay_level(bay, T, V, ab=None):
    """dz + tilt + curl + screed wave for one bay, at route coords (T, V).

    NOT included: the broom groove, the crazing, a popout.  Anything that stands
    on the slab bridges those, so this is the number a kerb, a gully frame or a
    portal footing is set to.

    `ab` lets a caller that has already computed the per-row concrete edges pass
    them in; the answer is identical, it just does not re-interpolate the ribbon
    tables for ten million points.
    """
    L = max(bay.t1 - bay.t0, 1e-6)
    a, b = bay.span_v(T) if ab is None else ab
    W = np.maximum(b - a, 1e-6)
    ft = (T - bay.tc) / (0.5 * L)
    fv = (V - 0.5 * (a + b)) / (0.5 * W)
    z = bay.dz + 0.0016 * (bay.tilt_t * np.clip(ft, -1, 1)
                           + bay.tilt_v * np.clip(fv, -1, 1)) * 0.5
    # slipform screed oscillation, along the direction of paving
    z = z + SCREED_WAVE_A * bay.curl * np.sin(
        2.0 * np.pi * T / bay.screed_l + bay.screed_p)
    # DAYTIME CURL.  The top of a slab in a 12.47 deg afternoon sun is warmer
    # than its bottom, so the edges go DOWN and the centre lifts.  Night curl is
    # the other way, and getting the sign wrong makes every joint read as a ridge
    # instead of a valley.
    dt = np.minimum(T - bay.t0, bay.t1 - T)
    dv = np.minimum(V - a, b - V)
    e = np.minimum(np.clip(dt, 0, None), np.clip(dv, 0, None))
    z = z - CURL_MAX_M * bay.curl * (1.0 - _sstep(0.0, CURL_LEN_M, e))
    return z


def slab_top_z_route(t, v, bays=None):
    """-> z of the finished slab top at route (t, v).  Vectorised.

    Points not on any bay (inside a joint slot, or off the ribbon) get the
    contract datum, so a caller never gets a NaN back.
    """
    if bays is None:
        bays = bay_layout()
    if _BAY_INDEX is None or _BAY_INDEX["bays"] is not bays:
        _index_bays(bays)
    t = np.atleast_1d(np.asarray(t, float))
    v = np.atleast_1d(np.asarray(v, float))
    t, v = np.broadcast_arrays(t, v)
    z = datum_z(t, v).copy()
    flat_t = t.ravel(); flat_v = v.ravel(); flat_z = z.ravel().copy()
    # lane 0 and lane N-1 carry SENTINEL bounds (+-9.0) so that `edge_v` decides
    # where the outer lanes stop; without this clip a query 1 m off the road
    # would be answered with the outermost bay's level instead of the datum.
    rlo, rhi = edge_v(flat_t)
    on = (flat_v >= rlo - 1e-9) & (flat_v <= rhi + 1e-9)
    for b in bays:
        m = (on & (flat_t >= b.t0) & (flat_t <= b.t1)
             & (flat_v >= b.va) & (flat_v <= b.vb))
        if not m.any():
            continue
        flat_z[m] = flat_z[m] + _bay_level(b, flat_t[m], flat_v[m])
    return flat_z.reshape(t.shape)


def slab_top_z(x, y, bays=None):
    """-> (z, bay_index) at WORLD (x, y).  bay_index is -1 off the road."""
    x = np.atleast_1d(np.asarray(x, float))
    y = np.atleast_1d(np.asarray(y, float))
    t, v = C.access_project(x, y)
    z = slab_top_z_route(t, v, bays)
    if bays is None:
        bays = bay_layout()
    _index_bays(bays)
    bi = np.full(x.shape, -1, np.int64)
    for i in range(x.size):
        b = bay_at(float(t.ravel()[i]), float(v.ravel()[i]), bays)
        if b is not None:
            bi.ravel()[i] = b.idx
    return z, bi


# =============================================================================
# 6.  THE JOINTS — 240 segments, and what access_road_saw_joint needs from each
# =============================================================================
class Joint:
    __slots__ = ("idx", "kind", "t0", "t1", "v0", "v1", "p0", "p1",
                 "width_m", "depth_m", "arris_z0", "arris_z1", "fault_m",
                 "bed_z", "sealed", "overband", "spall", "age", "grit",
                 "left", "right", "row", "lane")

    def __init__(self, **kw):
        for k in self.__slots__:
            setattr(self, k, kw.get(k))

    def __repr__(self):
        return ("Joint(%d %s t %.2f-%.2f v %.2f-%.2f w %.0fmm fault %+.1fmm %s)"
                % (self.idx, self.kind, self.t0, self.t1, self.v0, self.v1,
                   self.width_m * 1000, self.fault_m * 1000,
                   "sealed" if self.sealed else "open"))


def joint_frame(j, s):
    """-> (world xyz on the centreline, unit tangent, unit outboard-left normal).

    `s` in [0, 1] along the joint.  Given so a dependant orienting a sealant
    bead, a backer rod, a weed or a 58 mm macro camera does not have to
    re-derive the route frame and get the 40 deg rotation wrong.
    """
    s = float(np.clip(s, 0.0, 1.0))
    t = j.t0 + (j.t1 - j.t0) * s
    v = j.v0 + (j.v1 - j.v0) * s
    X, Y, H = route_frame(np.array([t]))
    x = float(X[0] - math.sin(float(H[0])) * v)
    y = float(Y[0] + math.cos(float(H[0])) * v)
    z = j.arris_z0 + (j.arris_z1 - j.arris_z0) * s
    dt = j.t1 - j.t0; dv = j.v1 - j.v0
    n = math.hypot(dt, dv) or 1.0
    h = float(H[0])
    tang = (math.cos(h) * dt / n - math.sin(h) * dv / n,
            math.sin(h) * dt / n + math.cos(h) * dv / n)
    nrm = (-tang[1], tang[0])
    return (x, y, z), tang, nrm


def joint_bed_z(j, s):
    """-> z of the sealant / detritus surface inside the slot at parameter s.

    This is the level a seed germinates on and the level a backer rod sits on;
    it is 3..21 mm below the arris depending on whether the joint is sealed,
    overbanded, or open and half full of grit.
    """
    s = float(np.clip(s, 0.0, 1.0))
    a = j.arris_z0 + (j.arris_z1 - j.arris_z0) * s
    return a - (j.bed_z if j.bed_z is not None else 0.0)


def joint_segments(bays=None, seed=SEED):
    """Every joint SEGMENT in the road.  See the module docstring, section 2."""
    if bays is None:
        bays = bay_layout(seed)
    _index_bays(bays)
    rows = _BAY_INDEX["rows"]
    st = sorted({(b.row, b.t0, b.t1) for b in bays})
    row_t = {r: (t0, t1) for (r, t0, t1) in st}
    out = []
    idx = 0

    def _mk(kind, t0, t1, v0, v1, left, right, row, lane):
        nonlocal idx
        w = {"sawn": JOINT_SAWN_W, "formed": JOINT_FORMED_W,
             "isolation": JOINT_ISOL_W}[kind]
        d = {"sawn": JOINT_SAWN_D, "formed": JOINT_FORMED_D,
             "isolation": JOINT_ISOL_D}[kind]
        u = _h(np.array(idx), np.array(seed + 6011))
        sealed = float(u) > FRAC_UNSEALED
        over = sealed and _hf(idx, seed + 6013) < FRAC_OVERBANDED
        age = _hf(idx, seed + 6017)
        spall = float(np.clip((_hf(idx, seed + 6019) ** 1.7) * 1.25, 0, 1))
        rec = _lerp(SEAL_RECESS[0], SEAL_RECESS[1], _hf(idx, seed + 6023))
        # the bed: sealant surface if sealed, grit if not
        bed = rec if sealed else _lerp(0.008, 0.021, _hf(idx, seed + 6029))
        za0 = float(_edge_arris_z(t0, v0, left, right, bays))
        za1 = float(_edge_arris_z(t1, v1, left, right, bays))
        fa = _fault_at(t0, t1, v0, v1, left, right, bays)
        p0x, p0y = route_xy(np.array([t0]), np.array([v0]))
        p1x, p1y = route_xy(np.array([t1]), np.array([v1]))
        j = Joint(idx=idx, kind=kind, t0=t0, t1=t1, v0=v0, v1=v1,
                  p0=(float(p0x[0]), float(p0y[0]), za0),
                  p1=(float(p1x[0]), float(p1y[0]), za1),
                  width_m=w, depth_m=d, arris_z0=za0, arris_z1=za1,
                  fault_m=fa, bed_z=bed, sealed=sealed, overband=over,
                  spall=spall, age=age,
                  grit=(0.0 if sealed else _lerp(0.35, 1.0,
                                                 _hf(idx, seed + 6031))),
                  left=left, right=right, row=row, lane=lane)
        out.append(j)
        idx += 1
        return j

    # --- transverse joints: one per lane, at every row boundary ---------------
    all_rows = sorted(row_t)
    for r in all_rows:
        t0, _t1 = row_t[r]
        kind = "isolation" if any(abs(t0 - f) < 1e-6 for f in FORCED_JOINT_T) \
            else "sawn"
        for b in rows.get(r, ()):
            prev = None
            for pb in rows.get(r - 1, ()):
                if pb.lane == b.lane:
                    prev = pb
            a, bb = b.span_v(np.array([t0]))
            _mk(kind, t0, t0, float(a[0]), float(bb[0]),
                prev.idx if prev else None, b.idx, r, b.lane)
    # the closing joint at the far end of the last row
    rlast = all_rows[-1]
    for b in rows.get(rlast, ()):
        a, bb = b.span_v(np.array([b.t1]))
        if float(bb[0] - a[0]) > 0.16:
            _mk("sawn", b.t1, b.t1, float(a[0]), float(bb[0]), b.idx, None,
                rlast + 1, b.lane)

    # --- longitudinal joints -------------------------------------------------
    # Paired off the boundaries the bays ACTUALLY share, not off lane indices:
    # in the gore two segments can be lanes 0 and 2 with a real tooled joint
    # between them, and an index-based pairing silently drops it.
    for r in all_rows:
        t0, t1 = row_t[r]
        seg = sorted(rows.get(r, ()), key=lambda b: b.va)
        for i in range(len(seg) - 1):
            lft, rgt = seg[i + 1], seg[i]        # left = higher v
            if abs(rgt.vb - lft.va) > 1e-6:
                continue
            v = float(rgt.vb)
            _mk("formed", t0, t1, v, v, lft.idx, rgt.idx, r, rgt.lane)
    return out


def _edge_arris_z(t, v, left, right, bays):
    """Slab top z at a joint arris — the mean of the two sides, because the
    joint's own centreline has no concrete in it."""
    zs = []
    for bi in (left, right):
        if bi is None:
            continue
        b = bays[bi]
        tt = float(np.clip(t, b.t0, b.t1)); vv = float(np.clip(v, b.va, b.vb))
        zs.append(float(datum_z(np.array([tt]), np.array([vv]))[0]
                        + _bay_level(b, np.array([tt]), np.array([vv]))[0]))
    if not zs:
        return float(datum_z(np.array([t]), np.array([v]))[0])
    return float(np.mean(zs))


def _fault_at(t0, t1, v0, v1, left, right, bays):
    """The STEP across the joint, signed positive when `right` is the higher
    side.  This is the number that throws a 45 px shadow at the contract sun,
    and it falls out of the level field rather than being invented on top of
    it."""
    if left is None or right is None:
        return 0.0
    tm = 0.5 * (t0 + t1); vm = 0.5 * (v0 + v1)
    zs = []
    for bi in (left, right):
        b = bays[bi]
        tt = float(np.clip(tm, b.t0, b.t1)); vv = float(np.clip(vm, b.va, b.vb))
        zs.append(float(_bay_level(b, np.array([tt]), np.array([vv]))[0]))
    return float(zs[1] - zs[0])


def portal_isolation(bays=None):
    """-> the two isolation joints the road is cast against at world X = +58.

    `pit_exit_portal_frame` sits in the PORTAL_ISOL_HALF * 2 = 1.10 m gap between
    them; its footings bear on the sub-base, not on the slab.
    """
    js = joint_segments(bays)
    want = (PORTAL_T - PORTAL_ISOL_HALF, PORTAL_T + PORTAL_ISOL_HALF)
    return [j for j in js if j.kind == "isolation"
            and min(abs(j.t0 - w) for w in want) < 1e-4]


def edge_polyline(side, ds=0.5, bays=None):
    """The road's outer arris, for access_road_kerb.  See docstring section 3."""
    R = ribbon()
    t = np.arange(0.0, float(R["T"][-1]) + ds * 0.5, ds)
    lo, hi = edge_v(t)
    v = hi if side > 0 else lo
    inset = EDGE_ARRIS_CHAMFER_M
    v = v - inset if side > 0 else v + inset
    x, y = route_xy(t, v)
    z = slab_top_z_route(t, v, bays)
    X, Y, H = route_frame(t)
    tang = np.stack([np.cos(H), np.sin(H)], axis=1)
    nrm = np.stack([-np.sin(H), np.cos(H)], axis=1) * (1.0 if side > 0 else -1.0)
    return dict(side=int(side), xy=np.stack([x, y], axis=1), z=z, t=t, v=v,
                tangent=tang, normal=nrm, kerb_seat_m=KERB_SEAT_M,
                arris_chamfer_m=EDGE_ARRIS_CHAMFER_M, skirt_z=SKIRT_Z)


# =============================================================================
# 7.  RESERVATIONS — letting a gully or a portal footing into the slab
# =============================================================================
_RESERVED = []


def reserve(polygon_world, kind="cover", depth_m=RECESS_LIP_M):
    """Register an exclusion BEFORE build().  Polygon in WORLD (N, 2).

    Bays are cut to the POLYGON, not to its bounding box: this route frame is
    rotated by up to 40 deg against world axes, and a world-aligned box over a
    0.72 m gully removes 1.9x the concrete it should.  A sawn wall is built from
    the cut boundary down to the skirt soffit, so what lands in the pocket meets
    a real concrete face instead of z-fighting a slab that is still there.
    """
    p = np.asarray(polygon_world, float).reshape(-1, 2)
    t, v = C.access_project(p[:, 0], p[:, 1])
    _RESERVED.append(dict(kind=kind, world=p, tv=np.stack([t, v], axis=1),
                          depth_m=float(depth_m)))
    return len(_RESERVED) - 1


def clear_reservations():
    _RESERVED.clear()


def _poly_mask_tv(T, V, tv):
    """Even-odd point-in-polygon in ROUTE coordinates.  Vectorised."""
    inside = np.zeros(T.shape, bool)
    n = len(tv)
    for i in range(n):
        a = tv[i]; b = tv[(i + 1) % n]
        cond = ((a[1] > V) != (b[1] > V))
        with np.errstate(divide="ignore", invalid="ignore"):
            xin = (b[0] - a[0]) * (V - a[1]) / (b[1] - a[1] + 1e-30) + a[0]
        inside ^= cond & (T < xin)
    return inside


def _reservation_mask(T, V):
    if not _RESERVED:
        return None
    m = np.zeros(T.shape, bool)
    for r in _RESERVED:
        tv = r["tv"]
        if (tv[:, 0].max() < T.min() - 0.05 or tv[:, 0].min() > T.max() + 0.05
                or tv[:, 1].max() < V.min() - 0.05
                or tv[:, 1].min() > V.max() + 0.05):
            continue
        m |= _poly_mask_tv(T, V, tv)
    return m if m.any() else None


# =============================================================================
# 8.  LOD — an ANISOTROPIC grid, aligned to the broom
# =============================================================================
#
# A broom finish is a ONE-DIMENSIONAL feature: 14.2 mm of pitch across the
# grooves carries every bit of the information, and along them the surface is
# straight for a metre at a time.  Meshing it isotropically at the pitch the
# across-axis needs spends 5x the triangles on the axis that carries nothing.
#
# So every bay is meshed on a grid aligned to its own broom direction — fine
# across, coarse along — and the two pitches are solved separately against the
# distance from the lens.  The consequence is the whole reason this item can be
# 2.7 mm-resolved at 1.7 m and still fit in an 11 GB machine.
#
# Both axes are additionally FORCED FINE in a band along every joint
# (EDGE_ZONE_M / EDGE_PITCH_M), because the arris, its chamfer and its spall are
# the strongest lines in the frame and they must exist on every bay however
# coarse its middle is.

def _m_per_px(d):
    """Metres per 4K screen pixel at distance d, on this item's own lens."""
    return M_PER_PX_PER_M * np.maximum(d, 0.05)


def _pitch_fine(d, bpitch, groove_r=GROOVE_MESH_R):
    """Sample spacing ACROSS the broom grooves.

    Two regimes.  Inside `groove_r` the spacing is whatever it takes to carry
    the groove — at least 6 samples per pitch, so the 36 %-duty groove gets
    2 to 3 samples across its floor and the cosine land is smooth.  Outside it
    the groove has fallen below a pixel and the spacing goes back to being
    screen-driven.
    """
    d = np.asarray(d, float)
    px = PITCH_FINE_PX * _m_per_px(d)
    groove = np.full(d.shape, bpitch / 6.0) if bpitch > 1e-6 else \
        np.full(d.shape, PITCH_FINE_MAX)
    p = np.where(d <= groove_r, np.minimum(px, groove), px)
    return np.clip(p, PITCH_FINE_MIN, PITCH_FINE_MAX)


def _pitch_coarse(d):
    """Sample spacing ALONG the grooves — screen-driven, with a floor that keeps
    a popout crater from becoming a slit."""
    return np.clip(PITCH_COARSE_PX * _m_per_px(np.asarray(d, float)),
                   PITCH_COARSE_MIN, PITCH_COARSE_MAX)


def _graded_axis(x0, x1, pitch_at, edge_zone, edge_pitch, nmax=400000):
    """Sample positions from x0..x1 whose local spacing is `pitch_at(x)`.

    Integrate the sample DENSITY and invert it.  A naive "walk forward by
    pitch(x)" biases the last cell and cannot land exactly on x1; this lands on
    both ends exactly, which matters because the ends are the joint arrises.
    """
    L = float(x1) - float(x0)
    if L <= 1e-9:
        return np.array([float(x0), float(x1)])
    m = int(np.clip(L / 0.0008, 96, 12000))
    xs = np.linspace(x0, x1, m)
    p = np.asarray(pitch_at(xs), float)
    e = np.minimum(xs - x0, x1 - xs)
    if edge_zone > 0:
        p = np.where(e < edge_zone, np.minimum(p, edge_pitch), p)
    dens = 1.0 / np.maximum(p, 1e-6)
    cum = np.concatenate([[0.0], np.cumsum(0.5 * (dens[1:] + dens[:-1])
                                           * np.diff(xs))])
    n = int(np.clip(math.ceil(cum[-1]), 2, nmax))
    q = np.linspace(0.0, cum[-1], n + 1)
    out = np.interp(q, cum, xs)
    out[0] = x0; out[-1] = x1
    return out


def _bay_edges_tv(bay):
    """-> (tA, tB, kind_t0, kind_t1) the bay's concrete extent along the route
    and the joint kind at each end."""
    def kind(t):
        return "isolation" if any(abs(t - f) < 1e-6 for f in FORCED_JOINT_T) \
            else "sawn"
    k0, k1 = kind(bay.t0), kind(bay.t1)
    w0 = {"sawn": JOINT_SAWN_W, "isolation": JOINT_ISOL_W}[k0]
    w1 = {"sawn": JOINT_SAWN_W, "isolation": JOINT_ISOL_W}[k1]
    return bay.t0 + 0.5 * w0, bay.t1 - 0.5 * w1, k0, k1


def _bay_side_kinds(bay):
    """-> (kind_v0, kind_v1): 'ribbon' where the bay's lateral edge IS the
    ribbon boundary (a slipformed / sawn free edge), 'formed' where it is a
    tooled tie-bar joint against the next paving lane."""
    lo, hi = edge_v(np.array([bay.tc]))
    k0 = "ribbon" if bay.va <= float(lo[0]) + 1e-6 else "formed"
    k1 = "ribbon" if bay.vb >= float(hi[0]) - 1e-6 else "formed"
    return k0, k1


VIEW_HFOV_DEG = 33.0        # half the 35 mm frame's DIAGONAL angle, plus margin
VIEW_PENALTY = 3.6          # how much coarser a bay outside the frame may be
VIEW_ROLLOFF_DEG = 20.0     # over how many degrees the penalty comes in


def _eff_dist(x, y, z, anchor, view_dir):
    """Distance from the lens, PENALISED for being outside the frame.

    Distance-only LOD spends its budget on geometry the specified shot cannot
    see: the anchor IS the camera, so the bay 2.0 m behind it is graded exactly
    as finely as the bay 2.0 m in front of it.  On the draft build that was most
    of the near-field vertex count.

    The number the pitch is solved against is therefore the true distance times
    a penalty that ramps from 1.0 inside the frame to VIEW_PENALTY well outside
    it.  Multiplying the DISTANCE is exactly equivalent to multiplying the pitch
    — pitch is linear in distance — and it leaves one number to reason about.

    THIS IS A PROPERTY OF THE SHOT, NOT OF THE ITEM.  The film's camera flies
    the whole corridor, so the assembly passes `view_dir=None` (or one anchor
    per station) and pays for the whole road at hero pitch.  Stated here because
    a dependant reading only the LOD constants would otherwise conclude that the
    far bays are permanently coarse.  They are not; THIS BUILD's are.
    """
    d = np.sqrt((x - anchor[0]) ** 2 + (y - anchor[1]) ** 2
                + (z - anchor[2]) ** 2)
    if view_dir is None:
        return d
    dd = np.maximum(d, 1e-6)
    cosa = np.clip(((x - anchor[0]) * view_dir[0]
                    + (y - anchor[1]) * view_dir[1]
                    + (z - anchor[2]) * view_dir[2]) / dd, -1.0, 1.0)
    ang = np.degrees(np.arccos(cosa))
    pen = 1.0 + (VIEW_PENALTY - 1.0) * _sstep(
        VIEW_HFOV_DEG, VIEW_HFOV_DEG + VIEW_ROLLOFF_DEG, ang)
    return d * pen


def _bay_axes(bay, anchor, scale=1.0, view_dir=None):
    """The two graded sample axes for one bay: (T samples, f samples in [0,1]).

    `anchor` is the lens.  The distance used to grade each axis is the CLOSEST
    APPROACH of the lens to the line of constant coordinate within the bay, not
    the bay-centre distance — so a bay straddling 1.8 m to 6.5 m is fine at its
    near end and coarse at its far end instead of uniformly one or the other.
    """
    tA, tB, _k0, _k1 = _bay_edges_tv(bay)
    lo, hi = edge_v(np.array([bay.tc]))
    a_mid = max(bay.va, float(lo[0])); b_mid = min(bay.vb, float(hi[0]))
    if bay.va > LANE_EDGES_V[0] + 1e-6:
        a_mid += JOINT_FORMED_W * 0.5
    if bay.vb < LANE_EDGES_V[-1] - 1e-6:
        b_mid -= JOINT_FORMED_W * 0.5
    W = max(b_mid - a_mid, 0.02)

    if anchor is None:
        at, av, aH = bay.tc, 0.0, 0.0
        far = True
    else:
        att, avv = C.access_project(np.array([anchor[0]]), np.array([anchor[1]]))
        at, av = float(att[0]), float(avv[0])
        far = False

    def dist_t(ts):
        if far:
            return np.full(ts.shape, 200.0)
        vv = np.clip(av, a_mid, b_mid)
        x, y = route_xy(ts, np.full(ts.shape, vv))
        z = datum_z(ts, np.full(ts.shape, vv))
        return _eff_dist(x, y, z, anchor, view_dir)

    def dist_f(fs):
        if far:
            return np.full(fs.shape, 200.0)
        vv = a_mid + (b_mid - a_mid) * fs
        tt = np.full(fs.shape, float(np.clip(at, tA, tB)))
        x, y = route_xy(tt, vv)
        z = datum_z(tt, vv)
        return _eff_dist(x, y, z, anchor, view_dir)

    dmin = float(min(dist_t(np.linspace(tA, tB, 33)).min(),
                     dist_f(np.linspace(0.0, 1.0, 33)).min()))
    epitch = EDGE_PITCH_M if dmin < FAR_R else EDGE_PITCH_FAR_M
    epitch *= scale
    ezone = EDGE_ZONE_M if dmin < FAR_R else EDGE_ZONE_M * 0.6

    fine_is_t = abs(math.cos(bay.phi)) >= abs(math.sin(bay.phi))
    bp = bay.bpitch if bay.fin not in (FIN_FLOAT, FIN_ASPH) else 0.0

    if fine_is_t:
        T = _graded_axis(tA, tB,
                         lambda x: _pitch_fine(dist_t(x), bp) * scale,
                         ezone, epitch)
        F = _graded_axis(0.0, 1.0,
                         lambda x: _pitch_coarse(dist_f(x)) * scale / W,
                         ezone / W, epitch / W)
    else:
        T = _graded_axis(tA, tB,
                         lambda x: _pitch_coarse(dist_t(x)) * scale,
                         ezone, epitch)
        F = _graded_axis(0.0, 1.0,
                         lambda x: _pitch_fine(dist_f(x), bp) * scale / W,
                         ezone / W, epitch / W)
    return T, F, dmin, fine_is_t, (a_mid, b_mid)


# =============================================================================
# 9.  THE SURFACE HISTORY — every term is geometry
# =============================================================================
def _chips(along, d, amount, seed, scale=0.105):
    """Spall chips along an arris.

    A concrete arris does not fail evenly: it loses BITES.  Chip centres sit on
    a 105 mm lattice, ~55 % of them fire at full `amount`, and each takes a lens
    of 16..80 mm along the joint, 4..24 mm in from it and 0.9..5.9 mm deep.  At
    2196 px/m the smallest of those is 35 px long and throws 4 mm of shadow.
    """
    out = np.zeros(along.shape)
    if amount <= 1e-4:
        return out
    k = np.floor(along / scale).astype(np.int64)
    for dk in (-1, 0, 1):
        kk = k + dk
        fire = _h(kk, np.array(seed)) < amount * 0.55
        c = (kk.astype(np.float64) + _h(kk, np.array(seed + 11))) * scale
        w = 0.008 + 0.032 * _h(kk, np.array(seed + 13))
        dep = 0.0009 + 0.0050 * _h(kk, np.array(seed + 17))
        reach = 0.004 + 0.020 * _h(kk, np.array(seed + 19))
        s = 1.0 - ((along - c) / w) ** 2
        r = 1.0 - d / reach
        chip = dep * np.clip(s, 0, 1) ** 0.6 * np.clip(r, 0, 1) ** 0.85
        out = np.maximum(out, np.where(fire, chip, 0.0))
    return out


def _arris_cut(bay, T, V, tA, tB, aE, bE, kinds, jspall):
    """The chamfer + spall removal along all four edges of a bay.

    Returns (cut_m, arr01) — the depth to remove, and a 0..1 proximity mask the
    material uses for efflorescence and edge dirt.
    """
    dt0 = T - tA; dt1 = tB - T
    dv0 = V - aE; dv1 = bE - V
    R = {"sawn": ARRIS_SAWN_M, "isolation": ARRIS_ISOL_R,
         "formed": ARRIS_FORMED_R, "ribbon": EDGE_ARRIS_CHAMFER_M}
    cut = np.zeros(T.shape)
    for (d, along, kind, key) in ((dt0, V, kinds[0], 1), (dt1, V, kinds[1], 2),
                                  (dv0, T, kinds[2], 3), (dv1, T, kinds[3], 4)):
        r = R[kind]
        # a quarter-round: z(d) = -(r - sqrt(r^2 - (r-d)^2)) for d < r
        dd = np.clip(d, 0.0, r)
        prof = r - np.sqrt(np.maximum(r * r - (r - dd) ** 2, 0.0))
        prof = np.where(d < r, prof, 0.0)
        # a SAWN arris has no chamfer, only micro-spall: the quarter round above
        # is 1.2 mm, and what actually reads is the chip field
        amt = jspall * (1.35 if kind == "sawn" else 0.85)
        if kind == "ribbon":
            amt = jspall * 1.7          # the road edge takes the wheel hits
        prof = prof + _chips(along, d, amt, bay.idx * 977 + key * 131)
        cut = np.maximum(cut, prof)
    e = np.minimum(np.minimum(dt0, dt1), np.minimum(dv0, dv1))
    arr = 1.0 - _sstep(0.0, 0.09, e)
    return cut, arr


def _broom(bay, T, V, q, r, pol, groove_mesh):
    """The broom / burlap groove field.  Metres of removal, >= 0."""
    if bay.fin in (FIN_FLOAT, FIN_ASPH) or bay.bdepth <= 0 or not groove_mesh:
        return np.zeros(T.shape)
    P = bay.bpitch
    # the operator's hand wanders as he drags: +-0.9 mm over 0.42 m of stroke
    wander = BROOM_WANDER_A * (_vn1(r / BROOM_WANDER_L
                                    + bay.rnd * 13.0, bay.idx * 31 + 7) - 0.5) * 2.0
    # broom PASSES.  The head is 0.62..0.95 m wide, so the strokes come in bands
    # with a phase jump and an amplitude change at every band edge, and a smeared
    # lap where two passes overlap.  This is the single most recognisable thing
    # about a hand-broomed slab and it is invisible in every shader-only version.
    # THE PASS BOUNDARY IS NOT A STRAIGHT LINE.  A man walking backwards
    # dragging a 0.8 m broom wanders +-60 mm, and a dead-straight seam every
    # 0.75 m is what made the first hero macro read as tiling.
    rs = (r + bay.pass_ph * bay.pass_w
          + 0.075 * (_vn1(q / 0.85 + bay.idx * 5.3, bay.idx * 41 + 9) - 0.5) * 2.0)
    pk = np.floor(rs / bay.pass_w).astype(np.int64)
    ph = _h(pk, np.array(bay.idx), np.array(9311)) * P
    # THE PASS PHASE JUMPS; THE PASS PRESSURE DOES NOT.
    # The first hero macro showed a rectangular TILING across every broomed bay:
    # amplitude was hashed per (groove index, pass index), so every groove
    # changed depth at every pass boundary and the two lattices printed a grid of
    # 0.75 x 0.014 m cells over the whole road.  The phase jump at a pass edge is
    # real -- the operator restarts the stroke -- but the pressure he leans on is
    # continuous, so it is a 1-D noise along the stroke, not a per-cell hash.
    pamp = 0.74 + 0.46 * _vn1(r / (bay.pass_w * 0.85) + bay.idx * 3.1,
                              bay.idx * 29 + 3)
    lap = 1.0 - 0.55 * np.exp(-((rs % bay.pass_w) / 0.011) ** 2)
    u = (q + wander + ph) / P
    gi = np.floor(u).astype(np.int64)
    frac = u - gi
    # per-groove constant (this bristle is stiffer than that one) PLUS a smooth
    # drift along the groove (it wore down as he pulled), decorrelated per groove
    gamp = (0.42 + 0.52 * _h(gi, np.array(bay.idx + 5))
            + 0.34 * (_vn1(r / 0.62 + gi.astype(np.float64) * 3.77,
                           bay.idx * 31 + 7) - 0.5) * 2.0)
    # BRISTLES BUNCH.  A broom does not lay 70 evenly spaced grooves; it lays
    # groups of four or five that are deeper, with shallow ones between.
    gamp = gamp * (0.72 + 0.56 * _vn1(q / 0.085 + bay.idx * 1.7,
                                      bay.idx * 37 + 11))
    miss = _h(gi, np.array(bay.idx + 6)) < 0.045          # a bristle is gone
    gamp = np.clip(np.where(miss, gamp * 0.14, gamp), 0.0, 1.25)
    hw = 0.5 * bay.duty * P
    x = (frac - 0.5) * P
    prof = np.where(np.abs(x) < hw,
                    0.5 * (1.0 + np.cos(np.pi * np.clip(x / hw, -1, 1))), 0.0)
    # traffic takes the top off the grooves without darkening the concrete:
    # this road is UNRUBBERED (mu 0.90) and stays pale
    return bay.bdepth * gamp * pamp * lap * prof * (1.0 - POLISH_MAX * pol)


def _float_swirl(bay, q, r):
    """A HAND-FLOATED bay's arcs.

    A bay closed with a magnesium float instead of a broom is not smooth — it
    carries the arcs of the float, 40..95 mm apart and 0.25..0.65 mm deep,
    sweeping from wherever the finisher was kneeling.  At 2196 px/m that is an
    88..209 px rhythm throwing 3 mm of shadow at the contract sun, and without it
    the 20 floated bays in this road are the only glassy surfaces in the film.

    Two centres, not one, because a bullseye is what one centre looks like and
    nobody closes a 9 m2 bay without moving.
    """
    if bay.fin != FIN_FLOAT:
        return np.zeros(q.shape)
    amp = _lerp(0.00038, 0.00090, bay.rnd)
    sp = _lerp(0.040, 0.095, _hf(bay.idx, 7001))
    out = np.zeros(q.shape)
    for k in range(2):
        cq = (_hf(bay.idx, 7003 + k) - 0.5) * 2.6
        cr = (_hf(bay.idx, 7011 + k) - 0.5) * 2.6
        dq = q - cq; dr = r - cr
        rad = np.sqrt(dq * dq + dr * dr)
        ang = np.arctan2(dr, dq)
        # the float wobbles as it sweeps, so the arcs are not concentric circles
        wob = 0.22 * sp * (_vn1(ang * 2.1 + bay.idx * 0.7,
                                bay.idx * 13 + k) - 0.5) * 2.0
        prof = 0.5 * (1.0 + np.cos(2.0 * np.pi * (rad + wob) / sp))
        # a sweep covers about 120 deg, and it fades where the float lifted
        reach = _sstep(1.55, 0.35, rad) * (0.35 + 0.9 * _vn1(
            ang * 1.35 + k * 3.1, bay.idx * 17 + k))
        out = np.maximum(out, amp * prof * np.clip(reach, 0.0, 1.0))
    return out


def _patch_relief(bay, T, V, q, r, tA, tB, aE, bE):
    """A COLD-MIX ASPHALT reinstatement, as geometry.

    A bay broken out and patched by two men and a rake sits 3..9 mm below the
    concrete around it, its 14 mm stone stands 1..3 mm proud of the binder, and
    the rake left ridges.  Giving it only a dark shader and a flat surface is the
    same defect as "the barrier is a smooth tube": at 1.7 m the STEP down into
    the patch throws 14..41 mm of shadow, and that step is the whole read.
    """
    if bay.fin != FIN_ASPH:
        return np.zeros(T.shape)
    sd = bay.idx * 8101 + 5
    dip = _lerp(0.0030, 0.0090, bay.rnd)
    e = np.minimum(np.minimum(T - tA, tB - T), np.minimum(V - aE, bE - V))
    # the patch does not meet the arris cleanly: the saw cut round it was ragged
    rag = 0.020 * (_vn1((q * 3.0 + r * 2.0), sd) - 0.5) * 2.0
    lip = _sstep(0.0, 0.055, np.maximum(e + rag, 0.0))
    stones = _worley(q / 0.017, r / 0.017, sd + 1, jitter=1.0, want=("f1",))["f1"]
    lump = -0.0026 * np.clip(1.0 - stones * 1.7, 0.0, 1.0) ** 0.7
    rake = 0.0011 * (_vn1(q / 0.075 + r * 0.6, sd + 2) - 0.5) * 2.0
    coarse = 0.0016 * (_fbm2(q * 3.4, r * 3.4, sd + 3, oct=4) - 0.5) * 2.0
    return dip * lip + lump + rake + coarse


def _bugholes(bay, q, r, seed):
    """Entrapped-air voids and pinholes.

    Every concrete surface is pitted.  On a floated bay the bubbles that rose
    through the paste and burst leave 3..7 mm craters 0.8..2.2 mm deep; on a
    broomed bay the broom tore most of them open but the lands still carry them.
    At 2196 px/m a 5 mm pinhole is 11 px across and throws 4..10 mm of shadow at
    the contract sun -- which is to say it is a FEATURE, not a texture, and the
    first hero macro's smooth lands between the grooves were the tell.
    """
    dens = 0.42 if bay.fin in (FIN_FLOAT, FIN_ASPH) else 0.24
    cell = 0.021
    w = _worley(q / cell, r / cell, seed, jitter=1.0, want=("cx", "cy"))
    bx, by = w["bx"], w["by"]
    fire = _h(bx, by, np.array(seed + 3)) < dens
    rad = (0.0015 + 0.0020 * _h(bx, by, np.array(seed + 5))) * (
        1.0 + 0.5 * bay.exp)
    dep = 0.0008 + 0.0014 * _h(bx, by, np.array(seed + 7))
    dq = q - w["cx"] * cell
    dr = r - w["cy"] * cell
    d = np.sqrt(dq * dq + dr * dr) / np.maximum(rad, 1e-6)
    # a burst bubble is a spherical cap, not a cone
    pit = dep * np.sqrt(np.clip(1.0 - d * d, 0.0, 1.0))
    return np.where(fire, pit, 0.0)


def _tooth(q, r, seed):
    """Mortar / fine-aggregate cells.  0.16 mm, which throws 0.7 mm = 1.6 px of
    shadow at the contract sun.  Everything finer than this is bump, and only
    everything finer than this."""
    cell = 0.5 * (TOOTH_CELL[0] + TOOTH_CELL[1])
    w = _worley(q / cell, r / cell, seed, jitter=0.95, want=("f1",))
    w2 = _worley(q / (cell * 0.38), r / (cell * 0.38), seed + 17, jitter=1.0,
                 want=("f1",))
    return TOOTH_A * (0.68 * np.clip(w["f1"] * 1.35, 0.0, 1.0)
                      + 0.32 * np.clip(w2["f1"] * 1.5, 0.0, 1.0))


def _popouts(bay, q, r, seed):
    """Aggregate popouts: where a piece of coarse stone has spalled out and left
    a crater.  Elongated ALONG the grooves, because a spall on a broomed slab
    runs with the corduroy and not across it — which is also the direction the
    mesh is coarse in, so the feature and the sampling agree."""
    ce = POPOUT_CELL
    el = _lerp(POPOUT_ELONG[0], POPOUT_ELONG[1], bay.rnd)
    w = _worley(q / ce, r / (ce * el), seed, jitter=1.0, want=("cx", "cy"))
    bx, by = w["bx"], w["by"]
    fire = _h(bx, by, np.array(seed + 71)) < FRAC_POPOUT * (0.35 + 1.4 * bay.exp)
    a = POPOUT_R[0] + (POPOUT_R[1] - POPOUT_R[0]) * _h(bx, by, np.array(seed + 73))
    dep = POPOUT_D[0] + (POPOUT_D[1] - POPOUT_D[0]) * _h(bx, by,
                                                         np.array(seed + 79))
    dq = (q - w["cx"] * ce) / np.maximum(a, 1e-6)
    dr = (r - w["cy"] * ce * el) / np.maximum(a * el, 1e-6)
    d = np.sqrt(dq * dq + dr * dr)
    crater = dep * np.clip(1.0 - d * d, 0.0, 1.0) ** 0.62
    return np.where(fire, crater, 0.0)


def _crazing(bay, q, r, seed):
    """Plastic-shrinkage map cracking: the polygonal hairline net an over-worked
    or fast-dried slab carries.  2.2 mm wide is 4.8 px."""
    if bay.craze <= 0.02:
        return np.zeros(q.shape)
    cc = bay.craze_cell
    w = _worley(q / cc + 11.0, r / cc - 7.0, seed, jitter=1.0, want=("f1", "f2"))
    edge = (w["f2"] - w["f1"]) * cc
    dep = _lerp(CRAZE_D[0], CRAZE_D[1], bay.rnd)
    return dep * bay.craze * (1.0 - _sstep(0.0, CRAZE_W, edge))


def _crack(bay, T, V, tA, tB, aE, bE):
    """A through crack: the bay found its own joint because the sawn one was cut
    late, or the sub-base moved.  Returns (removal_m, mask01)."""
    if not bay.crack:
        return np.zeros(T.shape), np.zeros(T.shape)
    ck = bay.crack
    sd = ck["seed"]
    if ck["across_t"]:
        base = tA + (tB - tA) * ck["pos"]
        wob = ck["wander"] * (_vn1(V / 0.55 + sd * 0.001, sd) - 0.5) * 2.0 \
            + 0.35 * ck["wander"] * (_vn1(V / 0.13 + sd * 0.003, sd + 5) - 0.5)
        d = np.abs(T - (base + wob))
    else:
        base = aE + (bE - aE) * ck["pos"]
        wob = ck["wander"] * (_vn1(T / 0.55 + sd * 0.001, sd) - 0.5) * 2.0 \
            + 0.35 * ck["wander"] * (_vn1(T / 0.13 + sd * 0.003, sd + 5) - 0.5)
        d = np.abs(V - (base + wob))
    hw = 0.5 * ck["w"] * (0.6 + 0.8 * _vn1((T + V) / 0.22 + sd, sd + 9))
    core = np.clip(1.0 - d / np.maximum(hw, 1e-5), 0.0, 1.0) ** 0.55
    lip = np.clip(1.0 - d / (hw * 5.5), 0.0, 1.0) ** 2.4 * 0.22
    return ck["d"] * (core + lip), np.clip(core + lip * 2.0, 0.0, 1.0)


def _corner_break(bay, T, V, tA, tB, aE, bE):
    """A broken corner: the classic failure of an undowelled slab corner under a
    44 t transporter.  Removes a wedge with a rough fracture face."""
    if not bay.corner:
        return np.zeros(T.shape), np.zeros(T.shape)
    cb = bay.corner
    ct = tA if cb["which"] in (0, 1) else tB
    cv = aE if cb["which"] in (0, 3) else bE
    dt = np.abs(T - ct); dv = np.abs(V - cv)
    rr = cb["r"]
    # the fracture runs corner-to-corner with a rough edge, not on an arc
    line = dt + dv
    rough = rr * (0.22 * (_vn1((dt - dv) / 0.09 + cb["seed"], cb["seed"]) - 0.5)
                  + 0.10 * (_vn1((dt - dv) / 0.028, cb["seed"] + 3) - 0.5))
    inside = _sstep(0.010, 0.0, line - (rr + rough))
    floor_ = cb["d"] * (0.72 + 0.28 * _vn1((T * 5.3 + V * 7.1), cb["seed"] + 7))
    return floor_ * inside, inside


def _traffic(bay, T, V):
    """Wheel-path polish.  UNRUBBERED: this takes the top off the broom groove
    and drops the roughness; it does NOT lay a black line down the middle.  The
    manifest is explicit — "it must not carry the track's rubber line"."""
    pol = np.zeros(T.shape)
    for lane_v in TRAVEL_V:
        for s in (-1.0, 1.0):
            c = lane_v + s * TRACK_GAUGE_M * 0.5
            w = TRACK_HALF_W * (1.0 + 0.18 * _vn1(T / 7.0 + c, 4517))
            wob = 0.085 * (_vn1(T / 11.0 + c * 3.0, 4519) - 0.5) * 2.0
            pol = np.maximum(pol, np.clip(1.0 - np.abs(V - c - wob) / w, 0, 1) ** 0.8)
    # traffic thins toward the gore, where only the racing car ever went
    pol *= _sstep(C.ACCESS_MERGE + 40.0, C.ACCESS_L2, np.asarray(T, float)) * 0.55 + 0.45
    return np.clip(pol * (0.55 + 0.55 * bay.rnd), 0.0, 1.0)


# =============================================================================
# 10.  THE BAY MESH
# =============================================================================
CHUNK = 220_000         # points per field-evaluation chunk.  This box has 11 GB
                        # of RAM and a 2 M-vertex bay carries ~40 intermediate
                        # float64 fields; evaluating it whole is 640 MB of
                        # transient per bay.  Chunking bounds it at 70 MB.


def _bay_span_arrays(bay, T):
    """Per-row concrete edges (a, b) in route lateral, already set back from the
    lane joints and clipped to the ribbon."""
    lo, hi = edge_v(T)
    a = np.maximum(bay.va, lo)
    b = np.minimum(bay.vb, hi)
    if bay.va > LANE_EDGES_V[0] + 1e-6:
        a = a + JOINT_FORMED_W * 0.5
    if bay.vb < LANE_EDGES_V[-1] - 1e-6:
        b = b - JOINT_FORMED_W * 0.5
    return a, np.maximum(b, a + 0.010)


def _bay_surface(bay, TT, VV, aE, bE, tA, tB, kinds, groove_mesh, jspall):
    """z and the twelve masks for one bay, evaluated in memory-bounded chunks.

    -> (z, ch) where ch is a dict of the ATTRS channels, all float32.
    """
    n = TT.size
    z = np.empty(n, np.float64)
    ch = {k: np.zeros(n, np.float32) for k in ATTRS}
    tc = bay.tc
    vc = 0.5 * (float(np.mean(aE)) + float(np.mean(bE)))
    cp, sp = math.cos(bay.phi), math.sin(bay.phi)
    sd = bay.idx * 6151 + 13

    Tf = TT.ravel(); Vf = VV.ravel()
    aF = aE.ravel(); bF = bE.ravel()
    for i0 in range(0, n, CHUNK):
        i1 = min(n, i0 + CHUNK)
        T = Tf[i0:i1]; V = Vf[i0:i1]
        a = aF[i0:i1]; b = bF[i0:i1]
        zd = datum_z(T, V)
        lev = _bay_level(bay, T, V, ab=(a, b))
        dt = T - tc; dv = V - vc
        q = dt * cp + dv * sp
        r = -dt * sp + dv * cp

        pol = _traffic(bay, T, V)
        # the edger leaves a hard, smooth, BRIGHT margin along every joint: it is
        # 40..92 px wide at 2196 px/m and it is what makes a joint read as a joint
        e = np.minimum(np.minimum(T - tA, tB - T), np.minimum(V - a, b - V))
        trowel = _sstep(bay.trowel, bay.trowel + 0.011, e)

        cut = _broom(bay, T, V, q, r, pol, groove_mesh) * trowel
        cut = cut + _float_swirl(bay, q, r) * trowel
        cut = cut + _patch_relief(bay, T, V, q, r, tA, tB, a, b)
        cut = cut + _tooth(q, r, sd + 1) * (0.35 + 0.65 * bay.exp)
        cut = cut + _popouts(bay, q, r, sd + 2)
        cut = cut + _bugholes(bay, q, r, sd + 11)
        cut = cut + _crazing(bay, q, r, sd + 3)
        ck, ckm = _crack(bay, T, V, tA, tB, a, b)
        cb, cbm = _corner_break(bay, T, V, tA, tB, a, b)
        cut = cut + ck + cb
        ar, arr = _arris_cut(bay, T, V, tA, tB, a, b, kinds, jspall)
        cut = np.maximum(cut, ar) + np.minimum(cut, ar) * 0.35

        zz = zd + lev - cut
        z[i0:i1] = zz
        rel = zz - (zd + lev)
        ch["pol"][i0:i1] = pol
        ch["arr"][i0:i1] = arr
        ch["dmg"][i0:i1] = np.clip(ckm + cbm + np.clip(ar / 0.004, 0, 1) * 0.6,
                                   0, 1)
        ch["hgt"][i0:i1] = np.clip(1.0 + rel / 0.0025, 0.0, 1.0)
        # ---- THE GRIME, IN ROUTE COORDINATES --------------------------------
        # The first hero macro's real failure: every history field was a per-BAY
        # CONSTANT modulated by a little fine noise, so each 9 m2 slab rendered
        # as one flat tone and 55 cm of concrete at 1:1 had no incident in it at
        # all.  Dust banks, damp patches and laitance run in metres and they do
        # NOT stop at a joint.
        #
        # So the fields are three shared fbm layers evaluated in ROUTE
        # coordinates (t, v) — continuous across every bay in the road — combined
        # with different signs and weights per channel so they decorrelate
        # without costing four more noise evaluations.
        #
        # THIS IS NOT A BREACH OF LAW 6.  Law 6 forbids a MATERIAL reading
        # Geometry -> Position, because at |P| ~ 1000 m the shader's floats run
        # out of mantissa.  This is float64 numpy evaluated once at build time
        # and BAKED INTO A VERTEX ATTRIBUTE; |t| <= 245 and |v| <= 6.3, and the
        # result is exact.  Baking is precisely the mechanism that lets a
        # world-continuous field exist without a position-driven shader.
        G0 = _fbm2(T / 8.5, V / 8.5, sd + 41, oct=3)      # 8.5 m weather
        G1 = _fbm2(T / 2.3, V / 2.3, sd + 43, oct=4)      # 2.3 m patches
        G2 = _fbm2(T / 0.58, V / 0.58, sd + 47, oct=4)    # 0.58 m mottle
        edge01 = 1.0 - np.clip(np.minimum(V - a, b - V) / 1.1, 0, 1)
        ch["dst"][i0:i1] = np.clip(
            0.34 * bay.dst + 1.15 * (G0 - 0.46) + 0.70 * (G1 - 0.48)
            + 0.30 * (G2 - 0.50) + 0.42 * edge01 - 0.40 * pol, 0, 1)
        ch["dmp"][i0:i1] = np.clip(
            0.30 * bay.dmp - 0.95 * (G0 - 0.50) + 1.15 * (G1 - 0.55)
            + 0.35 * (G2 - 0.50) + 0.75 * np.clip(-rel / 0.0016, 0, 1)
            + 0.30 * arr, 0, 1)
        ch["lat"][i0:i1] = np.clip(
            0.34 + 0.42 * bay.lat + 0.95 * (G1 - 0.47) + 0.62 * (G2 - 0.50)
            - 0.42 * (G0 - 0.50), 0, 1)
        ch["exp"][i0:i1] = np.clip(
            bay.exp * (0.55 + 0.75 * pol) + 0.85 * (G2 - 0.52)
            + 0.45 * (G1 - 0.50)
            + 0.55 * np.clip(ar / 0.003, 0, 1) + 0.7 * ckm, 0, 1)
        # DIESEL AND HYDRAULIC DRIPS.  A transporter parked on this road leaks
        # under its own footprint, not in a stripe down the middle.
        if bay.oil > 0.02:
            ox = _fbm2(q * 1.7 + 31.0 * bay.oil, r * 1.7, sd + 7, oct=4)
            ch["oil"][i0:i1] = np.clip((ox - (1.0 - bay.oil * 0.55)) * 6.0,
                                       0, 1) * (0.35 + 0.65 * (1.0 - trowel * 0))
        if bay.scf > 0.02:
            # a turning scuff is an ARC, because that is what a steered wheel
            # draws.  Straight black stripes are what a rubbered track has, and
            # this road is unrubbered.
            rr = 1.8 + 2.4 * bay.rnd
            cxq = (bay.rnd - 0.5) * 1.3
            d = np.abs(np.sqrt((q - cxq) ** 2 + (r * 1.15) ** 2) - rr)
            ch["scf"][i0:i1] = np.clip(
                (1.0 - d / 0.085) * bay.scf
                * (0.45 + 0.85 * _fbm2(q * 5.0, r * 5.0, sd + 8, oct=3)), 0, 1)
        # tie-bar rust bleeds out of the LONGITUDINAL joints only
        if kinds[2] == "formed" or kinds[3] == "formed":
            dvv = np.minimum(V - a if kinds[2] == "formed" else 9.9,
                             b - V if kinds[3] == "formed" else 9.9)
            ch["rst"][i0:i1] = np.clip(
                bay.rst * (1.0 - _sstep(0.0, 0.22, dvv))
                * (0.25 + 1.15 * _fbm2(q * 3.1, r * 3.1, sd + 9, oct=3)), 0, 1)
    return z, ch


def bay_mesh(bay, anchor=None, scale=1.0, groove_mesh=True, jspall=0.35,
             name=None, view_dir=None):
    """One pour bay as a solid: top surface, chamfered/spalled arris, slot walls
    down to SKIRT_Z.  Returns (mesh, stats) or (None, stats) if it collapsed."""
    T, F, dmin, fine_is_t, (a_mid, b_mid) = _bay_axes(bay, anchor, scale,
                                                     view_dir)
    nt, nf = len(T), len(F)
    if nt < 2 or nf < 2:
        return None, dict(verts=0)
    tA, tB, k0, k1 = _bay_edges_tv(bay)
    kv0, kv1 = _bay_side_kinds(bay)
    kinds = (k0, k1, kv0, kv1)
    aE1, bE1 = _bay_span_arrays(bay, T)
    TT = np.repeat(T[:, None], nf, axis=1)
    VV = aE1[:, None] + (bE1 - aE1)[:, None] * F[None, :]
    aE = np.repeat(aE1[:, None], nf, axis=1)
    bE = np.repeat(bE1[:, None], nf, axis=1)

    z, ch = _bay_surface(bay, TT, VV, aE, bE, tA, tB, kinds,
                         groove_mesh and dmin <= GROOVE_MESH_R, jspall)

    X, Y, H = route_frame(T)
    PX = X[:, None] - np.sin(H)[:, None] * VV
    PY = Y[:, None] + np.cos(H)[:, None] * VV
    co = np.stack([PX.ravel(), PY.ravel(), z], axis=1)

    idx = np.arange(nt * nf).reshape(nt, nf)
    quads = np.stack([idx[:-1, :-1], idx[1:, :-1], idx[1:, 1:], idx[:-1, 1:]],
                     axis=-1).reshape(-1, 4)

    # --- reservations: cut to the polygon, not to its bounding box -----------
    res = _reservation_mask(TT, VV)
    holes = 0
    if res is not None and res.any():
        qm = ~(res.ravel()[quads].any(axis=1))
        holes = int((~qm).sum())
        quads = quads[qm]
        if not len(quads):
            return None, dict(verts=0)
        ek = np.sort(np.stack([quads[:, [0, 1]], quads[:, [1, 2]],
                               quads[:, [2, 3]], quads[:, [3, 0]]],
                              axis=1).reshape(-1, 2), axis=1)
        key = ek[:, 0].astype(np.int64) * (nt * nf) + ek[:, 1]
        u, cnt = np.unique(key, return_counts=True)
        bnd = u[cnt == 1]
        ring_pairs = np.stack([bnd // (nt * nf), bnd % (nt * nf)], axis=1)
    else:
        ring = np.concatenate([idx[0, :], idx[1:, -1], idx[-1, -2::-1],
                               idx[-2:0:-1, 0]])
        ring_pairs = np.stack([ring, np.roll(ring, -1)], axis=1)

    # --- the slot / edge walls ----------------------------------------------
    # Every boundary edge is extruded straight down to SKIRT_Z as its own quad.
    # No ring ordering, so a bay with a gully pocket in it gets a sawn wall
    # around the pocket for free.  There is NO bottom cap: SKIRT_Z is 24 mm
    # BELOW the sub-base surface the bed mesh lays at, so no line of sight from
    # above ground can reach the open soffit.  That is a measured relationship
    # (verify() checks it), not a hope.
    nb = len(ring_pairs)
    base_n = co.shape[0]
    bot = np.empty((nb * 2, 3))
    bot[0::2] = co[ring_pairs[:, 0]]
    bot[1::2] = co[ring_pairs[:, 1]]
    bot[:, 2] = SKIRT_Z
    wall = np.stack([ring_pairs[:, 0], ring_pairs[:, 1],
                     base_n + np.arange(nb) * 2 + 1,
                     base_n + np.arange(nb) * 2], axis=1)
    co = np.concatenate([co, bot], axis=0)
    for k in ATTRS:
        ch[k] = np.concatenate([ch[k], np.repeat(ch[k][ring_pairs.ravel()], 1)])
    # THE WALL'S OWN CHARACTER.  An interior joint wall is a diamond-sawn face —
    # coarse aggregate sliced flat and pale, with the blade's arc marks on it.
    # The ribbon edge is a SLIPFORMED face — slumped, with the mould's drag lines
    # and honeycomb where the mix was harsh.  They look nothing alike at 1.7 m,
    # so `saw` says which one this vertex is on and the shader reads it.
    rv = ring_pairs.ravel()
    jj = rv % nf
    is_rib = (((jj == 0) & (kv0 == "ribbon"))
              | ((jj == nf - 1) & (kv1 == "ribbon")))
    sawv = np.where(is_rib, 0.20, 1.0).astype(np.float32)
    ch["saw"] = np.concatenate([np.zeros(base_n, np.float32), sawv])
    ch["arr"] = np.concatenate([ch["arr"][:base_n],
                                np.ones(nb * 2, np.float32)])

    me = _mesh_mixed(name or (PFX + "Bay_%04d" % bay.idx), co,
                     [(quads, 0), (wall, 1)])
    _bake_channels(me, ch)
    return me, dict(verts=int(co.shape[0]), quads=int(len(quads) + nb),
                    nt=nt, nf=nf, dmin=float(dmin), holes=holes,
                    fine_is_t=bool(fine_is_t))


# =============================================================================
# 11.  BLENDER PLUMBING
# =============================================================================
def _mesh_mixed(name, co, batches, smooth=True):
    """Build a mesh from batches of (face_array, material_index).

    Face arrays may have different vertex counts per batch, which `_new_mesh`'s
    all-quads fast path cannot express and which the wall + cap geometry needs.
    """
    me = bpy.data.meshes.new(name)
    nv = co.shape[0]
    me.vertices.add(nv)
    me.vertices.foreach_set("co", np.ascontiguousarray(co, np.float32).ravel())
    loops = []
    starts = []
    mats = []
    off = 0
    for arr, mi in batches:
        if arr is None or not len(arr):
            continue
        k = arr.shape[1]
        loops.append(np.ascontiguousarray(arr, np.int32).ravel())
        starts.append(off + np.arange(arr.shape[0], dtype=np.int32) * k)
        mats.append(np.full(arr.shape[0], mi, np.int32))
        off += arr.size
    if not loops:
        bpy.data.meshes.remove(me)
        return None
    L = np.concatenate(loops)
    S = np.concatenate(starts)
    M = np.concatenate(mats)
    me.loops.add(int(L.size))
    me.loops.foreach_set("vertex_index", L)
    me.polygons.add(int(S.size))
    me.polygons.foreach_set("loop_start", S)
    me.update()
    me.validate(verbose=False)
    if len(me.polygons) == S.size:
        me.polygons.foreach_set("material_index", M)
        if smooth:
            me.polygons.foreach_set("use_smooth", np.ones(S.size, bool))
    me.update()
    return me


def _bake_channels(me, ch):
    """Write the twelve masks as three FLOAT_COLOR point attributes."""
    nv = len(me.vertices)
    for lname, chans in ATTR_LAYERS:
        buf = np.empty((nv, 4), np.float32)
        for i, c in enumerate(chans):
            a = ch.get(c)
            if a is None:
                buf[:, i] = 0.0
            else:
                a = np.asarray(a, np.float32).ravel()
                buf[:, i] = a[:nv] if a.size >= nv else np.pad(a, (0, nv - a.size))
        at = me.color_attributes.new(lname, "FLOAT_COLOR", "POINT")
        at.data.foreach_set("color", buf.ravel())


def bake_attrs(me, **channels):
    """PUBLIC.  Write the ATTRS channels onto any mesh a dependant emits into
    these materials.  Unnamed channels default to 0.0; `hgt` defaults to 1.0
    because 1.0 means "on the land, not in a groove" and a mesh that leaves it
    at 0 reads as if every vertex were at the bottom of a broom groove."""
    nv = len(me.vertices)
    ch = {k: np.zeros(nv, np.float32) for k in ATTRS}
    ch["hgt"][:] = 1.0
    for k, v in channels.items():
        if k not in ch:
            raise KeyError("%s is not one of ATTRS %s" % (k, ATTRS))
        ch[k] = (np.full(nv, float(v), np.float32) if np.ndim(v) == 0
                 else np.asarray(v, np.float32).ravel())
    _bake_channels(me, ch)
    return me


def _collection(name, parent=None, link=True):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        if link:
            (parent or bpy.context.scene.collection).children.link(c)
    return c


def _obj(name, me, coll, mats, colour=None, props=None):
    ob = bpy.data.objects.new(name, me)
    for m in (mats or ()):
        me.materials.append(m)
    if colour is not None:
        ob.color = colour
    ob["friction_mu"] = FRICTION_MU
    ob["item_id"] = ITEM_ID
    for k, v in (props or {}).items():
        ob[k] = v
    coll.objects.link(ob)
    return ob


def _recentre(me, ob):
    """Law 6: recentre on emit.  Object space is then <= 4.3 m across, so every
    procedural in the shader has full float precision at world x = 230."""
    n = len(me.vertices)
    co = np.empty(n * 3, np.float32)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    c = 0.5 * (co.min(axis=0) + co.max(axis=0))
    co -= c
    me.vertices.foreach_set("co", co.ravel())
    ob.location = (float(c[0]), float(c[1]), float(c[2]))
    return c


def _clear():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for me in list(bpy.data.meshes):
        bpy.data.meshes.remove(me)
    for m in list(bpy.data.materials):
        bpy.data.materials.remove(m)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)


# =============================================================================
# 12.  JOINT FURNITURE — the sealant, the grit, the overbands
# =============================================================================
#
# This is the ONLY part of the module `access_road_saw_joint` supersedes.  The
# slot itself — the sawn walls, the arris, the chamfer, the spall — is the
# SLAB's concrete and stays here whatever that item does.

def _side_z(bays, bi, t, v):
    if bi is None:
        return None
    b = bays[bi]
    tt = np.clip(t, b.t0 + 1e-4, b.t1 - 1e-4)
    a_, b_ = _bay_span_arrays(b, tt)
    vv = np.clip(v, a_ + 1e-4, b_ - 1e-4)
    return datum_z(tt, vv) + _bay_level(b, tt, vv, ab=(a_, b_))


def _joint_fill_obj(j, bays, coll, mats, anchor, seed=SEED):
    """-> list of (object) for one joint: the bead (or the grit) and, if it was
    re-sealed, the overband spread onto the slab either side."""
    dt = j.t1 - j.t0; dv = j.v1 - j.v0
    L = math.hypot(dt, dv)
    if L < 0.10:
        return []
    # THE SIGN CONVENTION.  A transverse joint has zero extent in t, so its
    # across-direction is +t and `right` (built at the higher station) lies that
    # way.  A longitudinal joint runs in t, and its `right` is the LOWER-v lane
    # by construction in joint_segments, so its across-direction is -v.
    ntv = (1.0, 0.0) if abs(dt) < 1e-9 else (0.0, -1.0)
    mx, my = route_xy(np.array([0.5 * (j.t0 + j.t1)]),
                      np.array([0.5 * (j.v0 + j.v1)]))
    d = (math.dist((float(mx[0]), float(my[0]), 0.0), anchor)
         if anchor is not None else 200.0)
    ds = float(np.clip(7.0 * M_PER_PX_PER_M * d, 0.0022, 0.075))
    ns = int(np.clip(math.ceil(L / ds), 3, 3000)) + 1
    s = np.linspace(0.0, 1.0, ns)
    T = j.t0 + dt * s
    V = j.v0 + dv * s

    hw_wall = 0.5 * j.width_m
    eps = 0.0012
    zR = _side_z(bays, j.right, T + ntv[0] * (hw_wall + eps),
                 V + ntv[1] * (hw_wall + eps))
    zL = _side_z(bays, j.left, T - ntv[0] * (hw_wall + eps),
                 V - ntv[1] * (hw_wall + eps))
    if zR is None and zL is None:
        return []
    if zR is None:
        zR = zL
    if zL is None:
        zL = zR

    X, Y, H = route_frame(T)
    bx = X - np.sin(H) * V
    by = Y + np.cos(H) * V
    dirx = ntv[0] * np.cos(H) - ntv[1] * np.sin(H)
    diry = ntv[0] * np.sin(H) + ntv[1] * np.cos(H)

    out = []
    wet = 0.0016                       # how far the bead climbs the slot wall
    hw = hw_wall + wet
    nx = 9
    xs = np.linspace(-hw, hw, nx)
    sd = j.idx * 7919 + 3
    rec = j.bed_z if j.sealed else 0.0

    # --- the bead / the grit -------------------------------------------------
    co = np.empty((ns * nx, 3))
    for k, x in enumerate(xs):
        w = (x + hw) / (2.0 * hw)
        zw = zL * (1.0 - w) + zR * w
        if j.sealed:
            # sealant shrinks back from the arris and dishes in the middle; a
            # hot-poured bead climbs the wall as it cools
            climb = 1.0 - 0.62 * _sstep(hw_wall * 0.78, hw, abs(x))
            dish = SEAL_MENISCUS * max(0.0, 1.0 - (x / max(hw_wall, 1e-6)) ** 2)
            wob = 0.00035 * (_vn1(s * L / 0.16 + sd, sd + 1) - 0.5) * 2.0
            zt = zw - rec * climb - dish + wob
        else:
            # grit: wind-blown sand and tyre-carried grit half filling the slot,
            # with a rough top that catches the 12.47 deg sun
            fillv = j.bed_z * (0.82 + 0.30 * _vn1(s * L / 0.28 + sd, sd + 2))
            zt = zw - fillv + 0.0009 * (_vn1(s * L / 0.035 + sd, sd + 3) - 0.5) \
                * 2.0 * (1.0 - (abs(x) / hw) ** 2)
        co[k::nx] = np.stack([bx + dirx * x, by + diry * x, zt], axis=1)
    idx = np.arange(ns * nx).reshape(ns, nx)
    quads = np.stack([idx[:-1, :-1], idx[1:, :-1], idx[1:, 1:], idx[:-1, 1:]],
                     axis=-1).reshape(-1, 4)
    nm = PFX + ("Seal_%04d" % j.idx if j.sealed else "Grit_%04d" % j.idx)
    me = _mesh_mixed(nm, co, [(quads, 0)])
    if me is not None:
        bake_attrs(me, dst=(0.25 if j.sealed else 0.75), arr=1.0, dmp=0.25)
        ob = _obj(nm, me, coll,
                  [mats["seal"] if j.sealed else mats["grit"]],
                  colour=(j.age, j.spall, 1.0 if j.sealed else 0.0, j.idx % 97
                          / 97.0),
                  props={"joint_idx": j.idx, "joint_kind": j.kind})
        _recentre(me, ob)
        out.append(ob)

    # --- the overband: a re-sealed joint gets bitumen spread ON the slab ------
    if j.sealed and j.overband:
        bw = _lerp(SEAL_OVERBAND_W[0], SEAL_OVERBAND_W[1],
                   _hf(j.idx, seed + 8101))
        hb = 0.5 * bw
        nxb = 11
        xsb = np.linspace(-hb, hb, nxb)
        cob = np.empty((ns * nxb, 3))
        for k, x in enumerate(xsb):
            w = (x + hb) / (2.0 * hb)
            zw = zL * (1.0 - w) + zR * w - ARRIS_SAWN_M
            # A PLATEAU, NOT A DOME.  Bitumen squeegeed over a routed joint sets
            # with a flat top and a sharp shoulder; the first hero macro's ^0.62
            # dome read as a rubber snake lying on the road.
            edge = np.clip(1.0 - (abs(x) / hb) ** 5, 0.0, 1.0) ** 0.35
            ragged = 0.75 + 0.5 * _vn1(s * L / 0.09 + sd + x * 130.0, sd + 4)
            cob[k::nxb] = np.stack(
                [bx + dirx * x, by + diry * x,
                 zw + SEAL_OVERBAND_H * edge * ragged], axis=1)
        ib = np.arange(ns * nxb).reshape(ns, nxb)
        qb = np.stack([ib[:-1, :-1], ib[1:, :-1], ib[1:, 1:], ib[:-1, 1:]],
                      axis=-1).reshape(-1, 4)
        nmb = PFX + "Overband_%04d" % j.idx
        meb = _mesh_mixed(nmb, cob, [(qb, 0)])
        if meb is not None:
            bake_attrs(meb, dst=0.35, arr=0.8)
            obb = _obj(nmb, meb, coll, [mats["seal"]],
                       colour=(j.age * 0.6, 0.0, 1.0, 0.5),
                       props={"joint_idx": j.idx, "overband": True})
            _recentre(meb, obb)
            out.append(obb)
    return out


def _crack_overband(bay, coll, mats, anchor, seed=SEED):
    """A routed-and-sealed crack: the repair that says somebody looks after this
    road.  Reads as a black snake 45..75 mm wide wandering across a pale bay."""
    ck = bay.crack
    if not ck or not ck["seal"]:
        return []
    tA, tB, _k0, _k1 = _bay_edges_tv(bay)
    aM, bM = _bay_span_arrays(bay, np.array([bay.tc]))
    a0, b0 = float(aM[0]), float(bM[0])
    sd = ck["seed"]
    if ck["across_t"]:
        V = np.linspace(a0 + 0.004, b0 - 0.004, 220)
        base = tA + (tB - tA) * ck["pos"]
        wob = ck["wander"] * (_vn1(V / 0.55 + sd * 0.001, sd) - 0.5) * 2.0 \
            + 0.35 * ck["wander"] * (_vn1(V / 0.13 + sd * 0.003, sd + 5) - 0.5)
        T = np.clip(base + wob, tA + 0.01, tB - 0.01)
        n_t, n_v = 1.0, 0.0
    else:
        T = np.linspace(tA + 0.004, tB - 0.004, 220)
        base = a0 + (b0 - a0) * ck["pos"]
        wob = ck["wander"] * (_vn1(T / 0.55 + sd * 0.001, sd) - 0.5) * 2.0 \
            + 0.35 * ck["wander"] * (_vn1(T / 0.13 + sd * 0.003, sd + 5) - 0.5)
        V = np.clip(base + wob, a0 + 0.01, b0 - 0.01)
        n_t, n_v = 0.0, 1.0
    bw = _lerp(0.045, 0.075, _hf(bay.idx, seed + 8209))
    hb = 0.5 * bw
    X, Y, H = route_frame(T)
    bx = X - np.sin(H) * V
    by = Y + np.cos(H) * V
    dirx = n_t * np.cos(H) - n_v * np.sin(H)
    diry = n_t * np.sin(H) + n_v * np.cos(H)
    a_, b_ = _bay_span_arrays(bay, T)
    ztop = datum_z(T, V) + _bay_level(bay, T, V, ab=(a_, b_))
    nx = 11
    co = np.empty((len(T) * nx, 3))
    ss = np.linspace(0.0, 1.0, len(T))
    for k, x in enumerate(np.linspace(-hb, hb, nx)):
        edge = np.clip(1.0 - (abs(x) / hb) ** 5, 0.0, 1.0) ** 0.35
        ragged = 0.72 + 0.55 * _vn1(ss * 6.0 + x * 140.0 + sd, sd + 11)
        co[k::nx] = np.stack([bx + dirx * x, by + diry * x,
                              ztop - 0.0006 + 0.0026 * edge * ragged], axis=1)
    ix = np.arange(len(T) * nx).reshape(len(T), nx)
    q = np.stack([ix[:-1, :-1], ix[1:, :-1], ix[1:, 1:], ix[:-1, 1:]],
                 axis=-1).reshape(-1, 4)
    nm = PFX + "CrackSeal_%04d" % bay.idx
    me = _mesh_mixed(nm, co, [(q, 0)])
    if me is None:
        return []
    bake_attrs(me, dst=0.4, arr=0.5)
    ob = _obj(nm, me, coll, [mats["seal"]], colour=(0.22, 0.0, 1.0, 0.3),
              props={"bay_idx": bay.idx, "crack_seal": True})
    _recentre(me, ob)
    return [ob]


# =============================================================================
# 13.  THE SUB-BASE — what you see down a 10 mm slot
# =============================================================================
def _bed(coll, mat, t0, t1, seed=SEED, chunk=62.0):
    """Crushed-rock sub-base at BED_Z, 24 mm above the bay soffit so no line of
    sight from above ground can reach the open bottom of a slab.  Chunked at
    62 m of route (law 7: no object spans more than ~80-260 m)."""
    objs = []
    k = 0
    t = t0
    while t < t1 - 1e-6:
        te = min(t + chunk, t1)
        T = np.arange(t, te + BED_PITCH * 0.5, BED_PITCH)
        lo, hi = edge_v(T)
        lo = lo - 0.22; hi = hi + 0.22
        nf = max(int(math.ceil(float((hi - lo).max()) / BED_PITCH)), 3)
        f = np.linspace(0.0, 1.0, nf)
        V = lo[:, None] + (hi - lo)[:, None] * f[None, :]
        TT = np.repeat(T[:, None], nf, axis=1)
        X, Y, H = route_frame(T)
        PX = X[:, None] - np.sin(H)[:, None] * V
        PY = Y[:, None] + np.cos(H)[:, None] * V
        Z = (datum_z(TT, V) + BED_Z
             + 0.010 * (_fbm2(TT / 1.35, V / 1.35, seed + 5501, oct=4) - 0.5) * 2.0
             + 0.0045 * (_vn2(TT / 0.32, V / 0.32, seed + 5503) - 0.5) * 2.0)
        co = np.stack([PX.ravel(), PY.ravel(), Z.ravel()], axis=1)
        ix = np.arange(len(T) * nf).reshape(len(T), nf)
        q = np.stack([ix[:-1, :-1], ix[1:, :-1], ix[1:, 1:], ix[:-1, 1:]],
                     axis=-1).reshape(-1, 4)
        nm = PFX + "Bed_%02d" % k
        me = _mesh_mixed(nm, co, [(q, 0)])
        if me is not None:
            bake_attrs(me, dst=0.8, dmp=0.5, exp=1.0)
            ob = _obj(nm, me, coll, [mat], colour=(0.0, 0.5, 0.0, 0.5),
                      props={"route_t_range_m": [float(t), float(te)]})
            _recentre(me, ob)
            objs.append(ob)
        t = te
        k += 1
    return objs


# =============================================================================
# 14.  THE MATERIALS
# =============================================================================
#
# Every graph here reads TexCoord -> Object.  `Geometry -> Position` appears
# NOWHERE in this file: the ribbon reaches world (230, 93) and object space is
# never more than 4.3 m across, so a 130 cyc/m voronoi has full float precision
# at the far end of the gore and none of the blotching the first world pass had.
#
# Per-BAY decorrelation is Object Info -> Random; per-bay CONSTANTS ride in
# Object Info -> Color = (finish/5, age, crazing, bay random).  Neither costs a
# per-vertex channel.

# THE FIRST DRAFT RENDER CAME BACK CREAM.  Every driver of the base colour sat
# near its own mean, every endpoint was within 8 % of every other, and 164 bays
# rendered as one flat plaster tone -- "a grass gray line done", one material
# down.  So: the paste is DARKER (linear 0.27, which is what weathered PQ
# concrete actually measures, not 0.38), and the pour is drawn from three cement
# families rather than one, because bays cast on three different days with three
# different loads do not match and everybody who has looked at a concrete road
# knows it.
CEM = _srgb("#8f8b82")       # cement paste, cured, unrubbered  (linear 0.271)
CEM_WARM = _srgb("#96877a")  # a warm buff pour -- higher sand, more iron
CEM_COOL = _srgb("#84868a")  # a cool grey pour -- more GGBS in the mix
CEM_HI = _srgb("#bab5a9")    # laitance skin / curing-compound sheen
CEM_LO = _srgb("#5f5c56")    # the same paste, wet
EFFL = _srgb("#ded9cf")      # efflorescence bloom at a joint
AGG_LT = _srgb("#a8a294")    # limestone coarse aggregate
AGG_DK = _srgb("#5d5951")    # flint / basalt in the same mix
SANDC = _srgb("#94897a")     # fine aggregate
DUSTC = _srgb("#ab9a7c")     # warm mineral dust off the paddock
OILC = _srgb("#1b1916")      # diesel / hydraulic drip
SCUFFC = _srgb("#3b3936")    # a turning tyre's scuff, NOT a racing line
RUSTC = _srgb("#8b5a33")     # tie-bar bleed
BITU = _srgb("#191715")      # hot-poured bitumen, fresh
BITU_OLD = _srgb("#4c4941")  # ... and after four summers
GRITC = _srgb("#8b8174")     # grit in an open joint
ROCKC = _srgb("#948b7c")     # crushed sub-base
ASPH = _srgb("#2b2723")      # cold-mix bay repair — NOT the circuit's asphalt


def _mat(name):
    full = MPFX + name
    m = bpy.data.materials.get(full)
    if m is not None:
        return m, False
    m = bpy.data.materials.new(full)
    m.use_nodes = True
    m.node_tree.nodes.clear()
    return m, True


def _objco(g, scale=1.0):
    tc = g.n("ShaderNodeTexCoord")
    if abs(scale - 1.0) < 1e-9:
        return tc.outputs["Object"]
    vm = g.n("ShaderNodeVectorMath", operation="SCALE")
    g.set(vm.inputs[0], tc.outputs["Object"])
    g.set(vm.inputs["Scale"], scale)
    return vm.outputs[0]


def _vscale(g, vec, sx, sy=None, sz=None):
    vm = g.n("ShaderNodeVectorMath", operation="MULTIPLY")
    g.set(vm.inputs[0], vec)
    g.set(vm.inputs[1], (sx, sy if sy is not None else sx,
                         sz if sz is not None else sx))
    return vm.outputs[0]


def _chan(g):
    """-> a function name -> socket, reading the packed vertex channels."""
    cache = {}

    def get(name):
        for lname, chans in ATTR_LAYERS:
            if name in chans:
                i = chans.index(name)
                if lname not in cache:
                    at = g.n("ShaderNodeAttribute", attribute_name=lname)
                    sep = g.n("ShaderNodeSeparateColor")
                    g.set(sep.inputs["Color"], at.outputs["Color"])
                    cache[lname] = (sep, at)
                sep, at = cache[lname]
                return sep.outputs[i] if i < 3 else at.outputs["Alpha"]
        raise KeyError(name)
    return get


def _objinfo(g):
    oi = g.n("ShaderNodeObjectInfo")
    sep = g.n("ShaderNodeSeparateColor")
    g.set(sep.inputs["Color"], oi.outputs["Color"])
    return dict(rand=oi.outputs["Random"], fin=sep.outputs[0],
                age=sep.outputs[1], craze=sep.outputs[2],
                bay=oi.outputs["Alpha"])


def _set_in(g, node, name, v):
    if name in node.inputs:
        g.set(node.inputs[name], v)


def _out(m, g, bsdf, disp=None):
    o = g.n("ShaderNodeOutputMaterial")
    g.nt.links.new(bsdf.outputs[0], o.inputs["Surface"])
    if disp is not None:
        g.nt.links.new(disp, o.inputs["Displacement"])
    return o


def mat_concrete():
    """Unrubbered PQ concrete.  Nine colour layers, six roughness layers.

    THE POINT OF EACH LAYER, because a shader with 40 nodes and no reason is
    still a flat colour:
      1  paste vs laitance     the skin the float brought up, in 0.9 m patches
      2  per-bay tint          each pour is a different day and a different load
      3  coarse aggregate      shows where the paste has worn or spalled (`exp`)
      4  fine aggregate        the tooth, at 7 mm
      5  groove shading        dirt lodges in the broom grooves (`hgt`)
      6  dust film             blown against the kerb line (`dst`)
      7  damp                  low spots that have not dried (`dmp`)
      8  efflorescence         white bloom bleeding out of the joints (`arr`)
      9  oil / scuff / rust    local, never a stripe down the middle
    """
    m, new = _mat("Concrete")
    if not new:
        return m
    g = G(m.node_tree)
    ch = _chan(g)
    oi = _objinfo(g)
    P = _objco(g)

    # per-bay decorrelation: shift object space by a per-object random so two
    # bays never share a noise phase, WITHOUT using world position
    off = g.n("ShaderNodeVectorMath", operation="ADD")
    g.set(off.inputs[0], P)
    cmb = g.n("ShaderNodeCombineXYZ")
    g.set(cmb.inputs[0], g.math("MULTIPLY", oi["rand"], 37.0))
    g.set(cmb.inputs[1], g.math("MULTIPLY", oi["bay"], 53.0))
    g.set(cmb.inputs[2], g.math("MULTIPLY", oi["rand"], 11.0))
    g.set(off.inputs[1], cmb.outputs[0])
    Pb = off.outputs[0]

    lat_f, _ = g.noise(_vscale(g, Pb, 1.15), 1.0, detail=6.0, rough=0.55)
    med_f, _ = g.noise(_vscale(g, Pb, 5.5), 1.0, detail=5.0, rough=0.5)
    fine_f, _ = g.noise(_vscale(g, Pb, 34.0), 1.0, detail=4.0, rough=0.5)
    cure_f, _ = g.noise(_vscale(g, Pb, 0.42), 1.0, detail=3.0, rough=0.62)

    vagg = g.voro(_vscale(g, Pb, 46.0), 1.0, feature="F1")     # 22 mm stones
    vfine = g.voro(_vscale(g, Pb, 132.0), 1.0, feature="F1")   # 7.6 mm mortar
    vsand = g.voro(_vscale(g, Pb, 660.0), 1.0, feature="F1")   # 1.5 mm sand
    vagg_id = g.voro(_vscale(g, Pb, 46.0), 1.0, feature="F2")

    lat = ch("lat"); dst = ch("dst"); dmp = ch("dmp"); arr = ch("arr")
    pol = ch("pol"); exp = ch("exp"); oil = ch("oil"); scf = ch("scf")
    rst = ch("rst"); hgt = ch("hgt"); dmg = ch("dmg")

    # 1 -- WHICH POUR THIS BAY IS.  Three cement families, chosen per object;
    # `Object Info -> Random` and the `bay` alpha are two INDEPENDENT per-bay
    # randoms (Blender's own object hash, and this module's layout hash), so the
    # family and the value do not move together and 164 bays do not fall into
    # three visible groups.
    pour = g.mixc(g.mr(oi["rand"], 0.0, 0.55, 0.0, 1.0),
                  g.rgb(*CEM_COOL), g.rgb(*CEM))
    pour = g.mixc(g.mr(oi["rand"], 0.45, 1.0, 0.0, 1.0), pour, g.rgb(*CEM_WARM))
    # 2 -- paste vs the laitance skin the float brought up.  The mapping is STEEP
    # (0.30..0.80 rather than 0.15..0.95) because the drivers cluster near their
    # means and a gentle mapping is what produced one flat cream tone.
    latmix = g.math("ADD", g.math("MULTIPLY", lat, 0.62),
                    g.math("MULTIPLY", lat_f, 0.62))
    base = g.mixc(g.mr(latmix, 0.30, 0.80, 0.0, 1.0), pour, g.rgb(*CEM_HI))
    base = g.vmulc(base, g.grey(g.mr(oi["bay"], 0.0, 1.0, 0.82, 1.16)))
    # a curing-compound blotch: the sprayer overlapped, and it still shows
    base = g.mixc(g.math("MULTIPLY", g.mr(cure_f, 0.45, 0.80, 0.0, 0.34),
                         g.math("SUBTRACT", 1.0, oi["age"])),
                  base, g.rgb(*CEM_HI))

    # 3 + 4 -- aggregate, exposed where the paste is gone
    aggcol = g.mixc(g.mr(vagg_id.outputs["Distance"], 0.0, 0.9, 0.0, 1.0),
                    g.rgb(*AGG_DK), g.rgb(*AGG_LT))
    aggmask = g.mr(vagg.outputs["Distance"], 0.27, 0.02, 0.0, 1.0)
    base = g.mixc(g.math("MULTIPLY", exp,
                         g.math("ADD", g.math("MULTIPLY", aggmask, 0.95), 0.16)),
                  base, aggcol)
    # 4 -- THE MORTAR CELLS.  A 7.6 mm cell at 1.7 m is 16.7 px, so it is a
    # legible feature and not a texture: each cell gets its OWN tint out of the
    # F2 hash, which is what stops 55 cm of concrete from being one flat colour
    # at 1:1.  This is the layer the first hero macro had almost none of.
    sandmask = g.mr(vfine.outputs["Distance"], 0.30, 0.06, 0.0, 1.0)
    vfine_id = g.voro(_vscale(g, Pb, 132.0), 1.0, feature="F2")
    cellcol = g.mixc(g.mr(vfine_id.outputs["Distance"], 0.10, 0.85, 0.0, 1.0),
                     g.rgb(*SANDC), g.rgb(*CEM_HI))
    base = g.mixc(g.math("MULTIPLY", sandmask, 0.34), base, cellcol)
    base = g.vmulc(base, g.grey(g.mr(vfine_id.outputs["Distance"],
                                     0.0, 1.0, 0.92, 1.08)))

    # 5 -- the grooves hold dirt; the lands are bright.  `hgt` is 1 on the land
    #      and 0.3 at the bottom of a 2.2 mm groove, and this is what turns a
    #      corduroy of geometry into a corduroy you can SEE at 31 px of pitch.
    base = g.vmulc(base, g.grey(g.mr(hgt, 0.0, 1.0, 0.62, 1.05)))

    # 6 -- dust
    dstf = g.math("MULTIPLY", dst,
                  g.mr(med_f, 0.25, 0.85, 0.35, 1.0))
    base = g.mixc(g.math("MULTIPLY", dstf, 0.88), base, g.rgb(*DUSTC))
    # 7 -- damp
    base = g.mixc(g.math("MULTIPLY", dmp,
                         g.mr(fine_f, 0.3, 0.9, 0.55, 1.0)), base, g.rgb(*CEM_LO))
    # 7b -- THE JOINT HALO.  Water runs to the joints and stands there, so the
    # 60 mm either side of every joint is a shade darker than the middle of the
    # bay -- unless the joint is old enough to be leaching lime, in which case it
    # is a shade paler.  Both are true of the same road at the same time, which is
    # why they are two terms driven by the same `arr` and split on age.
    halo = g.math("MULTIPLY", g.mr(arr, 0.25, 1.0, 0.0, 1.0),
                  g.math("SUBTRACT", 1.0, oi["age"]))
    base = g.mixc(g.math("MULTIPLY", halo,
                         g.mr(med_f, 0.2, 0.9, 0.20, 0.46)), base, g.rgb(*CEM_LO))
    # 8 -- efflorescence out of the joints
    eff = g.math("MULTIPLY", g.math("MULTIPLY", arr, oi["age"]),
                 g.mr(fine_f, 0.35, 0.95, 0.0, 0.85))
    base = g.mixc(eff, base, g.rgb(*EFFL))
    # 8b -- THE WHEEL PATH IS A POLISH, NOT A LINE.
    # At 0.88 it read, in the corridor shot down the road, as a dark stripe
    # running to the vanishing point -- which is precisely the racing line the
    # manifest forbids this item to carry ("it must not carry the track's rubber
    # line", and mu = 0.90 unrubbered).  0.955 is a wheel path you can find if
    # you look for it and cannot see if you do not.
    base = g.vmulc(base, g.grey(g.mr(pol, 0.0, 1.0, 1.0, 0.955)))
    # 9 -- the local stains
    base = g.mixc(g.math("MULTIPLY", oil, 0.92), base, g.rgb(*OILC))
    base = g.mixc(g.math("MULTIPLY", scf, 0.80), base, g.rgb(*SCUFFC))
    base = g.mixc(g.math("MULTIPLY", rst, 0.55), base, g.rgb(*RUSTC))
    # damage darkens: a fresh fracture face is paler, an old one is filthy
    base = g.mixc(g.math("MULTIPLY", dmg, 0.30), base,
                  g.mixc(oi["age"], g.rgb(*CEM_HI), g.rgb(*CEM_LO)))

    # --- roughness ----------------------------------------------------------
    # ROUGHNESS VARIANCE IS NOT FREE AT A GRAZING ANGLE.
    # The Beat-4 corridor shot looks 21 deg down the road, and every 0.14 of
    # roughness spread turned into a hard blue-white specular blotch reflecting
    # the horizon sky -- the road read as if it had puddles on it.  The spread is
    # therefore tight (0.60..0.84 for everything except oil, which SHOULD be
    # shiny), and the character that used to live in roughness now lives in the
    # colour layers, where a grazing angle cannot amplify it.
    r = g.math("ADD", 0.72, g.math("MULTIPLY",
                                   g.math("SUBTRACT", fine_f, 0.5), 0.10))
    r = g.math("SUBTRACT", r, g.math("MULTIPLY", pol, 0.12))
    r = g.math("SUBTRACT", r, g.math("MULTIPLY", oil, 0.36))
    r = g.math("SUBTRACT", r, g.math("MULTIPLY", dmp, 0.06))
    r = g.math("ADD", r, g.math("MULTIPLY", dst, 0.07))
    r = g.math("ADD", r, g.math("MULTIPLY", g.math("SUBTRACT", 1.0, hgt), 0.05))
    r = g.math("MINIMUM", g.math("MAXIMUM", r, 0.30), 0.92)

    # --- normal: the sand grain, and only the sand grain --------------------
    # 1.5 mm cells at 0.66 px are the ONE thing on this surface too fine to be
    # mesh.  Everything coarser than a pixel is geometry, which is why the bump
    # strength here is 0.14 and not 1.0.
    bmp = g.n("ShaderNodeBump")
    g.set(bmp.inputs["Strength"], 0.50)
    g.set(bmp.inputs["Distance"], 0.0016)
    grain = g.math("ADD",
                   g.math("MULTIPLY", vsand.outputs["Distance"], 0.75),
                   g.math("MULTIPLY", fine_f, 0.25))
    # THE CRAZING'S LAST TWO PIXELS.  The map-cracking net is mesh, but the mesh
    # is anisotropic and a 2.2 mm hairline whose normal points along the coarse
    # axis lands between samples.  This is the SAME net at the SAME cell size,
    # driven by the SAME per-bay `craze` the geometry used (Object Info -> Color
    # blue), so the two agree instead of double-printing.
    cz1 = g.voro(_vscale(g, Pb, 9.0), 1.0, feature="F1")
    cz2 = g.voro(_vscale(g, Pb, 9.0), 1.0, feature="F2")
    czl = g.mr(g.math("SUBTRACT", cz2.outputs["Distance"],
                      cz1.outputs["Distance"]), 0.0, 0.030, 1.0, 0.0)
    grain = g.math("SUBTRACT", grain,
                   g.math("MULTIPLY", g.math("MULTIPLY", czl, oi["craze"]), 0.9))
    g.set(bmp.inputs["Height"], grain)
    bev = g.n("ShaderNodeBevel", samples=4)
    g.set(bev.inputs["Radius"], 0.0009)
    g.set(bev.inputs["Normal"], bmp.outputs["Normal"])

    bsdf = g.n("ShaderNodeBsdfPrincipled")
    _set_in(g, bsdf, "Base Color", base)
    _set_in(g, bsdf, "Roughness", r)
    _set_in(g, bsdf, "Metallic", 0.0)
    _set_in(g, bsdf, "Specular IOR Level", g.mr(dmp, 0.0, 1.0, 0.44, 0.50))
    _set_in(g, bsdf, "IOR", 1.486)
    _set_in(g, bsdf, "Normal", bev.outputs["Normal"])
    _out(m, g, bsdf)
    return m


def mat_cutface():
    """The vertical faces.  Two materials in one, switched by `saw`:

    saw = 1.0   a DIAMOND-SAWN joint wall: aggregate sliced flat and pale, with
                the blade's arc marks across it and no laitance at all
    saw = 0.2   a SLIPFORMED ribbon edge: slumped, drag lines down it from the
                mould, honeycomb where the mix was harsh at the edge

    They look nothing alike at 1.7 m, and the first version of this module had
    one grey for both.
    """
    m, new = _mat("CutFace")
    if not new:
        return m
    g = G(m.node_tree)
    ch = _chan(g)
    oi = _objinfo(g)
    P = _objco(g)
    saw = ch("saw"); dst = ch("dst"); dmp = ch("dmp")

    vagg = g.voro(_vscale(g, P, 52.0), 1.0, feature="F1")
    vagg2 = g.voro(_vscale(g, P, 52.0), 1.0, feature="F2")
    # blade arc marks: a saw leaves concentric scores, and a wave texture is
    # exactly that
    arc = g.n("ShaderNodeTexWave", wave_type="RINGS", bands_direction="Z")
    g.set(arc.inputs["Vector"], _vscale(g, P, 1.0, 1.0, 12.0))
    g.set(arc.inputs["Scale"], 26.0)
    g.set(arc.inputs["Distortion"], 1.5)
    g.set(arc.inputs["Detail"], 2.0)
    # slipform drag: vertical streaks
    drag = g.n("ShaderNodeTexNoise", noise_dimensions="3D")
    g.set(drag.inputs["Vector"], _vscale(g, P, 40.0, 40.0, 2.0))
    g.set(drag.inputs["Scale"], 3.0)
    g.set(drag.inputs["Detail"], 5.0)
    honey = g.voro(_vscale(g, P, 90.0), 1.0, feature="F1")

    sawcol = g.mixc(g.mr(vagg2.outputs["Distance"], 0.0, 0.75, 0.0, 1.0),
                    g.rgb(*AGG_DK), g.rgb(*AGG_LT))
    sawcol = g.mixc(g.mr(vagg.outputs["Distance"], 0.02, 0.14, 1.0, 0.0),
                    sawcol, g.rgb(*CEM))
    sawcol = g.vmulc(sawcol, g.grey(g.mr(arc.outputs["Fac"], 0.0, 1.0,
                                         0.90, 1.06)))
    formcol = g.mixc(g.mr(drag.outputs["Fac"], 0.25, 0.8, 0.0, 0.7),
                     g.rgb(*CEM), g.rgb(*CEM_LO))
    formcol = g.mixc(g.mr(honey.outputs["Distance"], 0.09, 0.015, 0.0, 0.85),
                     formcol, g.rgb(*AGG_DK))
    col = g.mixc(saw, formcol, sawcol)
    col = g.mixc(g.math("MULTIPLY", dst, 0.5), col, g.rgb(*DUSTC))
    col = g.mixc(g.math("MULTIPLY", dmp, 0.6), col, g.rgb(*CEM_LO))

    bmp = g.n("ShaderNodeBump")
    g.set(bmp.inputs["Strength"], 0.5)
    g.set(bmp.inputs["Distance"], 0.0025)
    g.set(bmp.inputs["Height"],
          g.mixf(saw, g.math("ADD", g.math("MULTIPLY", drag.outputs["Fac"], 0.6),
                             g.math("MULTIPLY", honey.outputs["Distance"], 0.4)),
                 g.math("ADD", g.math("MULTIPLY", vagg.outputs["Distance"], 0.7),
                        g.math("MULTIPLY", arc.outputs["Fac"], 0.3))))

    bsdf = g.n("ShaderNodeBsdfPrincipled")
    _set_in(g, bsdf, "Base Color", col)
    _set_in(g, bsdf, "Roughness",
            g.mixf(saw, g.mr(drag.outputs["Fac"], 0, 1, 0.72, 0.88),
                   g.mr(vagg.outputs["Distance"], 0, 0.2, 0.55, 0.78)))
    _set_in(g, bsdf, "Metallic", 0.0)
    _set_in(g, bsdf, "Normal", bmp.outputs["Normal"])
    _out(m, g, bsdf)
    return m


def mat_sealant():
    """Hot-poured bitumen.  Fresh it is near-black and semi-gloss; four summers
    later it is grey, crazed, dust-loaded and matte, and it has crept."""
    m, new = _mat("Sealant")
    if not new:
        return m
    g = G(m.node_tree)
    ch = _chan(g)
    oi = _objinfo(g)
    P = _objco(g)
    age = oi["fin"]                 # ob.color.r carries the joint's age here
    dst = ch("dst")

    craze = g.voro(_vscale(g, P, 240.0), 1.0, feature="F2")
    craze1 = g.voro(_vscale(g, P, 240.0), 1.0, feature="F1")
    grain, _ = g.noise(_vscale(g, P, 900.0), 1.0, detail=3.0)
    slump, _ = g.noise(_vscale(g, P, 26.0), 1.0, detail=4.0, rough=0.6)
    crk = g.mr(g.math("SUBTRACT", craze.outputs["Distance"],
                      craze1.outputs["Distance"]), 0.0, 0.05, 1.0, 0.0)

    col = g.mixc(g.math("MULTIPLY", age, 0.95), g.rgb(*BITU), g.rgb(*BITU_OLD))
    col = g.mixc(g.math("MULTIPLY", g.math("MULTIPLY", crk, age), 0.55),
                 col, g.rgb(*CEM_LO))
    col = g.mixc(g.math("MULTIPLY", dst, g.math("MULTIPLY", age, 0.55)),
                 col, g.rgb(*DUSTC))

    bmp = g.n("ShaderNodeBump")
    g.set(bmp.inputs["Strength"], 0.55)
    g.set(bmp.inputs["Distance"], 0.0012)
    g.set(bmp.inputs["Height"],
          g.math("ADD", g.math("MULTIPLY", slump, 0.55),
                 g.math("MULTIPLY", g.math("SUBTRACT", 1.0, crk), 0.45)))

    bsdf = g.n("ShaderNodeBsdfPrincipled")
    _set_in(g, bsdf, "Base Color", col)
    _set_in(g, bsdf, "Roughness",
            g.math("ADD", g.mr(age, 0.0, 1.0, 0.30, 0.82),
                   g.math("MULTIPLY", grain, 0.08)))
    _set_in(g, bsdf, "Metallic", 0.0)
    _set_in(g, bsdf, "Specular IOR Level", g.mr(age, 0.0, 1.0, 0.55, 0.32))
    _set_in(g, bsdf, "Normal", bmp.outputs["Normal"])
    _out(m, g, bsdf)
    return m


def mat_detritus():
    """Grit half filling an unsealed joint: wind-blown sand, tyre-carried stone,
    and the fines that wash out of the sub-base."""
    m, new = _mat("Detritus")
    if not new:
        return m
    g = G(m.node_tree)
    P = _objco(g)
    ch = _chan(g)
    peb = g.voro(_vscale(g, P, 420.0), 1.0, feature="F1")
    pid = g.voro(_vscale(g, P, 420.0), 1.0, feature="F2")
    fines, _ = g.noise(_vscale(g, P, 90.0), 1.0, detail=5.0)
    col = g.mixc(g.mr(pid.outputs["Distance"], 0.0, 0.7, 0.0, 1.0),
                 g.rgb(*GRITC), g.rgb(*AGG_DK))
    col = g.mixc(g.mr(fines, 0.3, 0.85, 0.0, 0.7), col, g.rgb(*SANDC))
    col = g.mixc(g.math("MULTIPLY", ch("dmp"), 0.7), col, g.rgb(*CEM_LO))
    bmp = g.n("ShaderNodeBump")
    g.set(bmp.inputs["Strength"], 0.85)
    g.set(bmp.inputs["Distance"], 0.0018)
    g.set(bmp.inputs["Height"],
          g.math("ADD", g.math("MULTIPLY", peb.outputs["Distance"], 0.7),
                 g.math("MULTIPLY", fines, 0.3)))
    bsdf = g.n("ShaderNodeBsdfPrincipled")
    _set_in(g, bsdf, "Base Color", col)
    _set_in(g, bsdf, "Roughness", g.mr(fines, 0, 1, 0.82, 0.95))
    _set_in(g, bsdf, "Normal", bmp.outputs["Normal"])
    _out(m, g, bsdf)
    return m


def mat_subbase():
    """Crushed limestone sub-base, seen only down a 10 mm slot — which is why
    its relief is a bump and its geometry is a 0.28 m grid."""
    m, new = _mat("SubBase")
    if not new:
        return m
    g = G(m.node_tree)
    P = _objco(g)
    rock = g.voro(_vscale(g, P, 55.0), 1.0, feature="F1")
    rid = g.voro(_vscale(g, P, 55.0), 1.0, feature="F2")
    fines, _ = g.noise(_vscale(g, P, 14.0), 1.0, detail=6.0)
    col = g.mixc(g.mr(rid.outputs["Distance"], 0.0, 0.8, 0.0, 1.0),
                 g.rgb(*ROCKC), g.rgb(*AGG_DK))
    col = g.mixc(g.mr(fines, 0.35, 0.9, 0.0, 0.6), col, g.rgb(*CEM_LO))
    bmp = g.n("ShaderNodeBump")
    g.set(bmp.inputs["Strength"], 1.0)
    g.set(bmp.inputs["Distance"], 0.010)
    g.set(bmp.inputs["Height"],
          g.math("ADD", g.math("MULTIPLY", rock.outputs["Distance"], 0.65),
                 g.math("MULTIPLY", fines, 0.35)))
    bsdf = g.n("ShaderNodeBsdfPrincipled")
    _set_in(g, bsdf, "Base Color", col)
    _set_in(g, bsdf, "Roughness", 0.93)
    _set_in(g, bsdf, "Normal", bmp.outputs["Normal"])
    _out(m, g, bsdf)
    return m


def mat_patch_asphalt():
    """A bay taken out and reinstated in COLD-MIX, laid by two men and a rake.

    Deliberately NOT the circuit's wearing course: no racing line, no closed
    surface, no roller sheen.  Loose 14 mm stone standing proud of a soft
    binder, a fatty patch where the mix segregated, and edges that were never
    trimmed.  The manifest names "same asphalt shader as the circuit" as the
    wrong version of this item; this is the answer to that.
    """
    m, new = _mat("PatchAsphalt")
    if not new:
        return m
    g = G(m.node_tree)
    P = _objco(g)
    ch = _chan(g)
    st = g.voro(_vscale(g, P, 72.0), 1.0, feature="F1")
    sid = g.voro(_vscale(g, P, 72.0), 1.0, feature="F2")
    fat, _ = g.noise(_vscale(g, P, 3.2), 1.0, detail=5.0, rough=0.6)
    fine, _ = g.noise(_vscale(g, P, 210.0), 1.0, detail=3.0)
    stone = g.mr(st.outputs["Distance"], 0.14, 0.02, 0.0, 1.0)
    col = g.mixc(g.math("MULTIPLY", stone, 0.72), g.rgb(*ASPH),
                 g.mixc(g.mr(sid.outputs["Distance"], 0, 0.8, 0, 1),
                        g.rgb(*AGG_DK), g.rgb(*AGG_LT)))
    col = g.mixc(g.mr(fat, 0.55, 0.85, 0.0, 0.75), col, g.rgb(*BITU))
    col = g.mixc(g.math("MULTIPLY", ch("dst"), 0.45), col, g.rgb(*DUSTC))
    bmp = g.n("ShaderNodeBump")
    g.set(bmp.inputs["Strength"], 1.0)
    g.set(bmp.inputs["Distance"], 0.0045)
    g.set(bmp.inputs["Height"],
          g.math("ADD", g.math("MULTIPLY", st.outputs["Distance"], 0.7),
                 g.math("MULTIPLY", fine, 0.3)))
    bsdf = g.n("ShaderNodeBsdfPrincipled")
    _set_in(g, bsdf, "Base Color", col)
    _set_in(g, bsdf, "Roughness",
            g.math("SUBTRACT", g.mr(fine, 0, 1, 0.78, 0.92),
                   g.math("MULTIPLY", g.mr(fat, 0.55, 0.9, 0.0, 1.0), 0.34)))
    _set_in(g, bsdf, "Normal", bmp.outputs["Normal"])
    _out(m, g, bsdf)
    return m


def _materials():
    return dict(concrete=mat_concrete(), cut=mat_cutface(),
                patch=mat_patch_asphalt(), seal=mat_sealant(),
                grit=mat_detritus(), bed=mat_subbase())


# =============================================================================
# 15.  BUILD
# =============================================================================
QUALITY_SCALE = {"hero": 1.0, "high": 1.5, "draft": 3.0, "coarse": 6.0}


def build(anchor_world=None, quality="hero", seed=SEED, t_range=None,
          build_joint_fill=True, build_bed=True, vert_budget=VERT_BUDGET,
          verbose=True, view_dir=None):
    """Emit the road.  See the module docstring, section 6."""
    t_start = time.time()
    coll = _collection(COLL_NAME)
    fcoll = _collection(FILL_COLL_NAME, coll) if build_joint_fill else None
    mats = _materials()

    bays = bay_layout(seed)
    joints = joint_segments(bays, seed)
    if t_range is not None:
        keep = set()
        bays2 = []
        for b in bays:
            if b.t1 > t_range[0] - 1e-9 and b.t0 < t_range[1] + 1e-9:
                bays2.append(b); keep.add(b.idx)
        joints = [j for j in joints
                  if j.t1 >= t_range[0] - 0.1 and j.t0 <= t_range[1] + 0.1]
        build_set = bays2
    else:
        build_set = bays

    # the arris spall on a bay's edge is the spall of the joints that bound it,
    # so the concrete and the sealant agree about how chewed that joint is
    spall = {}
    for j in joints:
        for bi in (j.left, j.right):
            if bi is not None:
                spall[bi] = max(spall.get(bi, 0.0), j.spall)

    qs = QUALITY_SCALE.get(quality, 1.0)

    # --- pass 1: cost the field, and back off if it will not fit ------------
    est = 0
    for b in build_set:
        T, F, _d, _fi, _ab = _bay_axes(b, anchor_world, qs, view_dir)
        est += len(T) * len(F)
    scale = qs
    if est > vert_budget:
        scale = qs * math.sqrt(est / float(vert_budget))
        if verbose:
            print(">> LOD backed off: %.1f M vertices estimated at quality '%s' "
                  "against a %.1f M budget -> pitch x %.3f"
                  % (est / 1e6, quality, vert_budget / 1e6, scale / qs))
    if verbose:
        print(">> %d bays, %d joint segments, anchor %s, pitch scale %.3f"
              % (len(build_set), len(joints),
                 ("(%.2f, %.2f, %.2f)" % tuple(anchor_world))
                 if anchor_world else "none", scale))

    # --- pass 2: emit --------------------------------------------------------
    nv = nq = 0
    fin_hist = [0] * 6
    dmins = []
    objs = []
    for i, b in enumerate(build_set):
        me, st = bay_mesh(b, anchor_world, scale,
                          jspall=float(np.clip(spall.get(b.idx, 0.3), 0.0, 1.0)),
                          view_dir=view_dir)
        if me is None:
            continue
        slot0 = mats["patch"] if b.fin == FIN_ASPH else mats["concrete"]
        ob = _obj(PFX + "Bay_%04d" % b.idx, me, coll, [slot0, mats["cut"]],
                  colour=(b.fin / 5.0, b.age, b.craze, b.rnd),
                  props={"bay_idx": b.idx, "row": b.row, "lane": b.lane,
                         "finish": FIN_NAMES[b.fin],
                         "route_t_range_m": [b.t0, b.t1],
                         "route_v_range_m": [b.va, b.vb],
                         "reinstated": bool(b.reinst),
                         "cracked": bool(b.crack is not None),
                         "grid": [st["nt"], st["nf"]]})
        _recentre(me, ob)
        objs.append(ob)
        nv += st["verts"]; nq += st["quads"]
        fin_hist[b.fin] += 1
        dmins.append(st["dmin"])
        if verbose and (i % 25 == 0 or i == len(build_set) - 1):
            print("   bay %3d/%d  %-13s %5dx%-5d  d=%6.2f m  %8.2f M verts"
                  % (i + 1, len(build_set), FIN_NAMES[b.fin], st["nt"],
                     st["nf"], st["dmin"], nv / 1e6))

    nfill = 0
    if build_joint_fill:
        bset = {b.idx for b in build_set}
        for j in joints:
            if (j.left is not None and j.left not in bset) and \
               (j.right is not None and j.right not in bset):
                continue
            nfill += len(_joint_fill_obj(j, bays, fcoll, mats, anchor_world,
                                         seed))
        for b in build_set:
            nfill += len(_crack_overband(b, fcoll, mats, anchor_world, seed))

    nbed = 0
    if build_bed:
        t0 = t_range[0] if t_range else 0.0
        t1 = t_range[1] if t_range else float(ribbon()["T"][-1])
        nbed = len(_bed(coll, mats["bed"], t0, t1, seed))

    stats = dict(
        item=ITEM_ID, seed=seed, quality=quality, pitch_scale=round(scale, 4),
        bays_total=len(bays), bays_built=len(objs), joints=len(joints),
        joint_fill_objects=nfill, bed_objects=nbed,
        vertices=int(nv), faces=int(nq),
        finish_histogram={FIN_NAMES[i]: fin_hist[i] for i in range(6)},
        nearest_bay_m=(round(float(min(dmins)), 3) if dmins else None),
        friction_mu=FRICTION_MU,
        route_length_m=round(float(ribbon()["T"][-1]), 4),
        build_s=round(time.time() - t_start, 1))
    if verbose:
        print(">> built %d bay objects, %d fill objects, %d bed chunks"
              % (len(objs), nfill, nbed))
        print(">> %.2f M vertices, %.2f M faces, %.1f s"
              % (nv / 1e6, nq / 1e6, stats["build_s"]))
        print(">> finishes: %s" % json.dumps(stats["finish_histogram"]))
    return stats


# =============================================================================
# 16.  THE TEST SCENE — contract sun, manifest camera
# =============================================================================
VIEW_AZ_DEG = 4.0          # essentially down the road (+X on the flat run),
                           # which is the direction Beat 4 actually travels, with
                           # the 12.47 deg sun 62 deg off the axis so it rakes
                           # ACROSS the transverse broom grooves
CAM_PITCH_DEG = 38.0       # see camera_pose
TEST_T_RANGE = (5.0, 47.0)  # the walled corridor, on the DEAD FLAT run


def apply_contract_sky():
    """Force the Sky Texture onto the contract's atmosphere.

    MUST be called after any procedural_world(), including the one inside
    save_clean: that helper writes its own numbers, one of which does not exist
    in this Blender (`dust_density`; it is `aerosol_density`) and three of which
    are wrong for this contract.
    """
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
    print(">> sun: elev %.3f deg  bearing %.3f deg  energy %.3f  shadow ratio "
          "%.4f" % (C.SUN_ELEV_DEG, C.SUN_BEARING_DEG, C.SUN_ENERGY,
                    C.SUN_SHADOW_RATIO))
    return ob


def choose_test_target(seed=SEED):
    """Pick the metre of road the macro is shot on, and say why.

    The manifest names three variation axes.  A macro that happens to land on
    plain concrete proves none of them, and "it is in the code" is not evidence
    — R2-017 is exactly that failure.  So the frame is CHOSEN: scan the real
    layout for the bay whose 3.0 x 3.5 m frame at 1.7 m on a 35 mm lens contains
    the most of a transverse joint, a longitudinal joint, a BROOM DIRECTION
    CHANGE across a joint, faulting, crazing, a crack and an open joint — and
    print the inventory that made it win.
    """
    bays = bay_layout(seed)
    joints = joint_segments(bays, seed)
    jt = {}
    for j in joints:
        jt.setdefault(j.right, []).append(j)
        jt.setdefault(j.left, []).append(j)
    best, bestsc, why = None, -1.0, {}
    for b in bays:
        if not (TEST_T_RANGE[0] <= b.tc <= TEST_T_RANGE[1]):
            continue
        # THE FRAME MUST BE REPRESENTATIVE.  The first scoring pass landed on the
        # 1.10 m closure strip between the portal's two isolation joints -- a
        # real and interesting piece of road, and the one panel in 164 that is
        # NOT the rhythm the manifest asks this item to establish.  A macro has
        # to show the typical thing before it shows the exception.
        if (b.t1 - b.t0) < 3.0 or (b.vb - b.va) < 2.5:
            continue
        # ... and on the finish this item is FOR.  A macro of the one bay that
        # was hand-floated smooth proves nothing about a broom finish.
        if b.fin not in (FIN_TRANS, FIN_SKEW):
            continue
        js = jt.get(b.idx, [])
        if not js:
            continue
        nb = [o for o in bays if o.row in (b.row - 1, b.row, b.row + 1)
              and abs(o.lane - b.lane) <= 1 and o.idx != b.idx]
        dirchg = sum(1 for o in nb if o.fin != b.fin)
        fault = max([abs(j.fault_m) for j in js] or [0.0])
        openj = sum(1 for j in js if not j.sealed)
        overb = sum(1 for j in js if j.overband)
        spall = max([j.spall for j in js] or [0.0])
        crk = (1 if b.crack else 0) + sum(1 for o in nb if o.crack)
        sc = (2.4 * min(dirchg, 2) / 2.0
              + 2.1 * min(fault / 0.0045, 1.0)
              + 1.6 * min(b.craze / 0.55, 1.0)
              + 1.5 * min(crk, 2) / 2.0
              + 1.2 * min(openj + overb, 2) / 2.0
              + 1.0 * min(spall / 0.6, 1.0)
              + 0.8 * min(len(js) / 4.0, 1.0)
              + 1.4 * min(b.craze / 0.5, 1.0)
              + 0.6 * (1.0 if any(o.fin in (FIN_LONG, FIN_BURLAP, FIN_FLOAT,
                                            FIN_ASPH) for o in nb) else 0.0))
        if sc > bestsc:
            bestsc, best = sc, b
            why = dict(score=round(sc, 3), bay=b.idx, row=b.row, lane=b.lane,
                       finish=FIN_NAMES[b.fin],
                       neighbour_finishes=sorted({FIN_NAMES[o.fin] for o in nb}),
                       finish_changes_adjacent=dirchg,
                       max_fault_mm=round(fault * 1000, 2),
                       crazing=round(b.craze, 3),
                       cracked_bays_adjacent=crk,
                       open_or_overbanded_joints=openj + overb,
                       max_arris_spall=round(spall, 3),
                       route_t=[round(b.t0, 2), round(b.t1, 2)],
                       route_v=[round(b.va, 2), round(b.vb, 2)])
    print(">> macro target chosen from the real layout: %s" % json.dumps(why))
    return best, why


def camera_pose(target_world, az_deg=VIEW_AZ_DEG, pitch_deg=CAM_PITCH_DEG,
                lens=LENS_AT_CLOSEST_MM, near_m=NEAREST_CAMERA_M):
    """Place the lens EXACTLY `near_m` from the road.

    WHICH DISTANCE 1.7 m IS.  The manifest derives `nearest_camera_m` as the
    minimum over the 4507-sample camera corridor — the closest the lens EVER
    gets to this item.  A road is a continuous ground plane, so the closest
    point is always the one directly under the lens, and "1.7 m from the road"
    therefore means THE CAMERA FLIES AT 1.7 m ALTITUDE.  Solving instead for the
    frame's bottom edge would put the lens at 1.05 m and produce a shot 0.65 m
    closer than the film ever gets: a harder test than the manifest specifies,
    which is not the same thing as the specified test.

    So: height = near_m exactly.  The axis is pitched 38 deg down, which puts the
    frame on road 1.23 .. 4.24 m out — three metres of road, enough for a whole
    bay and both of its transverse joints, at 1781 px/m at the near edge against
    the manifest's 2196 px/m at the nadir.  Every one of those numbers is
    printed below rather than claimed.
    """
    vhalf = math.degrees(math.atan(0.5 * SENSOR_MM * RES_Y_4K / RES_X_4K / lens))
    bot = pitch_deg + vhalf
    top = pitch_deg - vhalf
    h = near_m
    ground_near = h / math.tan(math.radians(bot))
    aim_d = h / math.tan(math.radians(pitch_deg))
    a = math.radians(az_deg)
    cam = Vector((target_world[0] - math.cos(a) * aim_d,
                  target_world[1] - math.sin(a) * aim_d, h))
    tgt = Vector((target_world[0], target_world[1], target_world[2]))
    print(">> camera solve: lens %.1f mm  vhalf %.2f deg  axis %.1f deg down"
          % (lens, vhalf, pitch_deg))
    print(">>   height %.4f m; frame bottom %.2f deg -> %.3f m out, %.4f m slant"
          % (h, bot, ground_near, math.hypot(ground_near, h)))
    print(">>   frame top %.2f deg -> %.3f m out, %.3f m slant"
          % (top, h / math.tan(math.radians(top)),
             math.hypot(h / math.tan(math.radians(top)), h)))
    for lbl, dd in (("nadir (the manifest's 1.700 m)", h),
                    ("frame bottom", math.hypot(ground_near, h)),
                    ("frame centre", math.hypot(aim_d, h)),
                    ("frame top", math.hypot(h / math.tan(math.radians(top)), h))):
        print(">>   px/m at %-32s %7.3f m -> %7.1f px/m  (1 px = %.4f mm)"
              % (lbl, dd, RES_X_4K * lens / SENSOR_MM / dd,
                 1000.0 * SENSOR_MM * dd / (RES_X_4K * lens)))
    return cam, tgt, h


def _cam(scene, name, pos, tgt, lens, make_active=False):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = SENSOR_MM
    cd.clip_start = 0.01
    cd.clip_end = 2000.0
    cam = bpy.data.objects.new(name, cd)
    scene.collection.objects.link(cam)
    fwd = (Vector(tgt) - Vector(pos)).normalized()
    right = fwd.cross(Vector((0.0, 0.0, 1.0)))
    if right.length < 1e-6:
        right = Vector((1.0, 0.0, 0.0))
    right.normalize()
    up = right.cross(fwd).normalized()
    M = Matrix((right, up, -fwd)).transposed().to_4x4()
    cam.matrix_world = Matrix.Translation(Vector(pos)) @ M
    if make_active:
        scene.camera = cam
    return cam


def measure_nearest(cam, prefix=PFX):
    """Distance from the lens to the nearest ARS_ vertex ACTUALLY BUILT.

    A claim about the filmed distance that is not this number is a claim about
    the intent, not the artefact (R2-017).
    """
    deps = bpy.context.evaluated_depsgraph_get()
    cp = np.array(cam.matrix_world.translation)
    best, who = 1e9, ""
    for ob in bpy.context.scene.objects:
        if ob.type != "MESH" or not ob.name.startswith(prefix):
            continue
        me = ob.data
        if not len(me.vertices):
            continue
        co = np.empty(len(me.vertices) * 3, np.float32)
        me.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        M = np.array(ob.matrix_world.to_4x4())
        co = co @ M[:3, :3].T + M[:3, 3]
        d = float(np.linalg.norm(co - cp, axis=1).min())
        if d < best:
            best, who = d, ob.name
    print(">> nearest %s vertex to the lens: %.4f m  (%s)  manifest %.3f m"
          % (prefix, best, who, NEAREST_CAMERA_M))
    return best


def build_test_scene(quality="hero", out=None, seed=SEED, t_range=None,
                     vert_budget=VERT_BUDGET):
    scene = bpy.context.scene
    _clear()
    clear_reservations()
    tb, why = choose_test_target(seed)
    if tb is None:
        raise SystemExit("REFUSING: no candidate bay in the test window.")
    # aim at the DOWNSTREAM joint of the chosen bay, so the frame is guaranteed
    # to contain a joint rather than to contain it on average
    # THE AIM POINT IS COMPOSED, NOT CENTRED.
    #   along the road: 1.35 m short of the bay's downstream joint, so the frame
    #     (1.23..4.24 m out) holds 2.3 m of the target bay, the transverse joint
    #     at 78 % of frame height with its faulting shadow, and a strip of the
    #     next bay's different finish above it.
    #   across: 0.55 m inboard of the bay's own longitudinal joint, so that joint
    #     runs from the bottom edge to the top edge of the frame.  A transverse
    #     joint alone reads as a crack; the two together read as a POUR PLAN,
    #     which is the manifest's first variation axis.
    aim_t = tb.t1 - 1.35
    aE, bE = _bay_span_arrays(tb, np.array([aim_t]))
    a0, b0 = float(aE[0]), float(bE[0])
    kv0, kv1 = _bay_side_kinds(tb)
    if kv1 == "formed":
        v_aim = b0 - 0.55
    elif kv0 == "formed":
        v_aim = a0 + 0.55
    else:
        v_aim = 0.5 * (a0 + b0)
    tv = (aim_t, float(np.clip(v_aim, a0 + 0.15, b0 - 0.15)))
    tx, ty = route_xy(np.array([tv[0]]), np.array([tv[1]]))
    tz = float(slab_top_z_route(np.array([tv[0]]), np.array([tv[1]]))[0])
    target = (float(tx[0]), float(ty[0]), tz)
    cam_p, tgt, h = camera_pose(target)

    if t_range is None:
        t_range = (0.0, float(ribbon()["T"][-1]))
    vd = (tgt - cam_p).normalized()
    stats = build(anchor_world=(cam_p.x, cam_p.y, cam_p.z), quality=quality,
                  seed=seed, t_range=t_range, vert_budget=vert_budget,
                  view_dir=(vd.x, vd.y, vd.z))
    stats["macro_target"] = why

    contract_sun(scene)
    cam = _cam(scene, "CAM_ARS_Macro", cam_p, tgt, LENS_AT_CLOSEST_MM, True)
    stats["camera_nearest_m"] = round(measure_nearest(cam), 4)

    # --- the other looks this item has to survive ---------------------------
    # the Beat-4 shot itself: 1.7 m altitude, nearly level, down the corridor
    cx, cy = route_xy(np.array([8.0]), np.array([1.6]))
    fx, fy = route_xy(np.array([46.0]), np.array([0.9]))
    _cam(scene, "CAM_ARS_Corridor",
         Vector((float(cx[0]), float(cy[0]), 1.70)),
         Vector((float(fx[0]), float(fy[0]), 0.55)), 35.0)
    # a 58 mm on a single joint — the lens access_road_saw_joint is filmed with
    jx, jy = route_xy(np.array([tb.t1]), np.array([tv[1]]))
    _cam(scene, "CAM_ARS_Joint",
         Vector((float(jx[0]) - 0.95, float(jy[0]) - 0.20, 1.70)),
         Vector((float(jx[0]), float(jy[0]), tz)), 58.0)
    # into the sun, where a pale surface either has tooth or does not
    sx, sy = route_xy(np.array([tv[0] + 3.2]), np.array([tv[1]]))
    _cam(scene, "CAM_ARS_Backlit",
         Vector((float(sx[0]) - 5.4, float(sy[0]) + 3.1, 1.70)),
         Vector((float(tx[0]), float(ty[0]), tz)), 35.0)
    # the whole width, from where a person would stand
    wx, wy = route_xy(np.array([tv[0] - 9.0]), np.array([0.0]))
    _cam(scene, "CAM_ARS_Wide",
         Vector((float(wx[0]), float(wy[0]), 5.2)),
         Vector((float(tx[0]), float(ty[0]), 0.0)), 35.0)

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
# 17.  SELF-MEASUREMENT — the things item_gate structurally cannot check
# =============================================================================
def verify(seed=SEED, out=None, scene=False):
    """Measure the ARTEFACT.  Every number is a physical quantity (R2-017).

    Eight questions the acceptance gate cannot answer for this item:

      1. Is the road where the CONTRACT says it is?  The gate measures screen
         pixels; it has no opinion about `C.world_ground_z`.  This samples the
         built datum against the contract at random points and reports the worst
         disagreement in millimetres.
      2. Does the finished concrete stay inside the declared envelope?  z = 0.000
         is a LAW for the first 49.6 m and a budget is an intention until it is
         measured.
      3. How big is the worst bay-to-bay step, and is it a step a paving crew
         would have left?
      4. Are the three declared variation axes actually realised, at rates a
         person would recognise as a road?
      5. Can a slab's open soffit ever be seen?  SKIRT_Z below the bed is a
         RELATIONSHIP, not a hope.
      6. Does `reserve()` cut to the polygon, or to its bounding box?  The
         difference is 1.9x on a gully in a frame rotated 40 deg.
      7. Is it UNRUBBERED?  The manifest's hard requirement is that this road
         must not carry the track's rubber line, so the scuff and oil coverage
         is counted off the built vertex masks, not asserted in a comment.
      8. Does the mesh actually reach the lens at 1.7 m?
    """
    t0 = time.time()
    R = ribbon()
    bays = bay_layout(seed)
    joints = joint_segments(bays, seed)
    rep = dict(item=ITEM_ID, seed=seed, when=time.strftime("%Y-%m-%dT%H:%M:%S"))

    # --- 1. the contract ----------------------------------------------------
    rng = np.random.default_rng(7)
    tt = rng.uniform(0.0, float(R["T"][-1]), 6000)
    lo, hi = edge_v(tt)
    vv = lo + (hi - lo) * rng.uniform(0.02, 0.98, tt.size)
    exact = C.access_z(tt, vv)
    approx = datum_z(tt, vv)
    px_, py_ = route_xy(tt, vv)
    wz, own = C.world_ground_z(px_, py_)
    inrib = np.array([str(o).endswith("SURF_AccessRoad") for o in own])
    rep["datum"] = dict(
        table_interp_err_max_mm=round(float(np.abs(exact - approx).max()) * 1000, 4),
        table_interp_err_p99_mm=round(
            float(np.percentile(np.abs(exact - approx), 99)) * 1000, 4),
        vs_world_ground_z_max_mm=round(
            float(np.abs(exact[inrib] - wz[inrib]).max()) * 1000, 4)
        if inrib.any() else None,
        samples_owned_by_ribbon=int(inrib.sum()), samples=int(tt.size),
        flat_run_max_abs_mm=round(
            float(np.abs(exact[tt <= C.ACCESS_L2]).max()) * 1000, 6))

    # --- 2. the envelope ----------------------------------------------------
    zmin, zmax = 1e9, -1e9
    who_min = who_max = None
    for b in bays:
        T = np.linspace(*_bay_edges_tv(b)[:2], 41)
        a_, b_ = _bay_span_arrays(b, T)
        f = np.linspace(0.0, 1.0, 25)
        TT = np.repeat(T[:, None], 25, axis=1)
        VV = a_[:, None] + (b_ - a_)[:, None] * f[None, :]
        lv = _bay_level(b, TT, VV, ab=(np.repeat(a_[:, None], 25, axis=1),
                                       np.repeat(b_[:, None], 25, axis=1)))
        if lv.min() < zmin:
            zmin, who_min = float(lv.min()), b.idx
        if lv.max() > zmax:
            zmax, who_max = float(lv.max()), b.idx
    rep["level_envelope"] = dict(
        min_mm=round(zmin * 1000, 3), max_mm=round(zmax * 1000, 3),
        declared_min_mm=SLAB_TOP_MIN_M * 1000,
        declared_max_mm=SLAB_TOP_MAX_M * 1000,
        inside=bool(zmin >= SLAB_TOP_MIN_M - 1e-9
                    and zmax <= SLAB_TOP_MAX_M + 1e-9),
        worst_low_bay=who_min, worst_high_bay=who_max,
        headroom_under_MARK_Z_mm=round((0.0075 - zmax) * 1000, 3),
        concrete_under_BASE_EMBED_mm=round(
            (zmin + SLAB_T - C.BASE_EMBED_M) * 1000, 1))

    # --- 3. faulting --------------------------------------------------------
    f = np.array([abs(j.fault_m) for j in joints])
    rep["faulting"] = dict(
        max_mm=round(float(f.max()) * 1000, 3),
        p95_mm=round(float(np.percentile(f, 95)) * 1000, 3),
        mean_mm=round(float(f.mean()) * 1000, 3),
        joints_over_3mm=int((f > 0.003).sum()),
        shadow_of_worst_mm=round(float(f.max()) * C.SUN_SHADOW_RATIO * 1000, 1),
        shadow_of_worst_px=round(float(f.max()) * C.SUN_SHADOW_RATIO * PX_PER_M, 1))

    # --- 4. the variation axes ----------------------------------------------
    fin = np.array([b.fin for b in bays])
    kinds = {}
    for j in joints:
        kinds[j.kind] = kinds.get(j.kind, 0) + 1
    areas = np.array([b.area for b in bays])
    rep["variation"] = dict(
        bays=len(bays), bay_area_mean_m2=round(float(areas.mean()), 3),
        bay_area_total_m2=round(float(areas.sum()), 1),
        joint_segments=len(joints), manifest_joint_segments=MANIFEST_JOINT_SEGMENTS,
        joint_kinds=kinds,
        joints_unsealed=sum(1 for j in joints if not j.sealed),
        joints_overbanded=sum(1 for j in joints if j.overband),
        finish_histogram={FIN_NAMES[i]: int((fin == i).sum()) for i in range(6)},
        distinct_finishes=int(len(set(fin.tolist()))),
        broom_pitches_mm=sorted({round(b.bpitch * 1000, 1) for b in bays
                                 if b.fin not in (FIN_FLOAT, FIN_ASPH)}),
        broom_angles_deg=[round(x, 1) for x in
                          sorted({round(math.degrees(b.phi), 0) for b in bays})],
        bays_cracked=sum(1 for b in bays if b.crack),
        bays_corner_broken=sum(1 for b in bays if b.corner),
        bays_reinstated=sum(1 for b in bays if b.reinst),
        bay_lengths_m=sorted({round(b.t1 - b.t0, 3) for b in bays}))

    # --- 4b. IS THERE A HOLE IN THE ROAD? -----------------------------------
    # A gap in a surface the car crosses at 130 km/h is not a cosmetic defect.
    # 20 000 stratified samples of the ribbon; every one must land inside a bay
    # or inside a joint slot, and the report says which.
    tt2 = np.linspace(0.02, float(R["T"][-1]) - 0.02, 4000)
    lo2, hi2 = edge_v(tt2)
    fr = np.linspace(0.004, 0.996, 25)
    TTc = np.repeat(tt2[:, None], 25, axis=1).ravel()
    VVc = (lo2[:, None] + (hi2 - lo2)[:, None] * fr[None, :]).ravel()
    covered = np.zeros(TTc.shape, bool)
    for b in bays:
        sel = ((TTc >= b.t0) & (TTc <= b.t1) & (VVc >= b.va) & (VVc <= b.vb))
        if not sel.any():
            continue
        tA_, tB_, _a, _b = _bay_edges_tv(b)
        aa, bb2 = _bay_span_arrays(b, TTc[sel])
        covered[sel] |= ((TTc[sel] >= tA_) & (TTc[sel] <= tB_)
                         & (VVc[sel] >= aa) & (VVc[sel] <= bb2))
    inslot = np.zeros(TTc.shape, bool)
    for j in joints:
        hw2 = 0.5 * j.width_m + 0.0015
        if abs(j.t1 - j.t0) < 1e-9:
            inslot |= (np.abs(TTc - j.t0) <= hw2) & (VVc >= j.v0 - 0.02) \
                & (VVc <= j.v1 + 0.02)
        else:
            inslot |= (np.abs(VVc - j.v0) <= hw2) & (TTc >= j.t0 - 0.02) \
                & (TTc <= j.t1 + 0.02)
    hole = ~covered & ~inslot
    rep["coverage"] = dict(
        ribbon_area_m2=round(float(np.trapezoid(np.maximum(hi2 - lo2, 0.0),
                                                tt2)), 1),
        samples=int(TTc.size),
        concrete_fraction=round(float(covered.mean()), 5),
        joint_slot_fraction=round(float((~covered & inslot).mean()), 5),
        unexplained_fraction=round(float(hole.mean()), 6),
        unexplained_t_range=([round(float(TTc[hole].min()), 2),
                              round(float(TTc[hole].max()), 2)]
                             if hole.any() else None),
        no_holes=bool(hole.mean() < 0.002))

    # --- 4c. DOES THE PUBLIC INTERFACE ACTUALLY WORK? -----------------------
    # Three items are going to be built on top of this one by agents who cannot
    # ask questions.  An interface function that exists and returns nonsense is
    # worse than one that is missing, because the missing one gets noticed.  So
    # every entry point in the module docstring is CALLED here and its answer is
    # checked against something independent.
    ifr = {}
    tprobe = np.array([3.0, 20.0, 43.0, 70.0, 120.0])
    lo3, hi3 = edge_v(tprobe)
    vprobe = lo3 + (hi3 - lo3) * 0.42
    xw, yw = route_xy(tprobe, vprobe)
    z_route = slab_top_z_route(tprobe, vprobe, bays)
    z_world, bidx = slab_top_z(xw, yw, bays)
    ifr["slab_top_z_vs_route_max_mm"] = round(
        float(np.abs(z_world - z_route).max()) * 1000, 4)
    ifr["slab_top_z_found_a_bay"] = int((bidx >= 0).sum())
    ifr["slab_top_z_probes"] = int(tprobe.size)

    jt = joints[len(joints) // 3]
    (jx, jy, jz), tang, nrm = joint_frame(jt, 0.5)
    mx, my = route_xy(np.array([0.5 * (jt.t0 + jt.t1)]),
                      np.array([0.5 * (jt.v0 + jt.v1)]))
    ifr["joint_frame_offset_mm"] = round(
        1000.0 * math.hypot(jx - float(mx[0]), jy - float(my[0])), 4)
    ifr["joint_frame_tangent_norm"] = round(math.hypot(*tang), 6)
    ifr["joint_frame_normal_dot_tangent"] = round(
        abs(tang[0] * nrm[0] + tang[1] * nrm[1]), 9)
    bz = joint_bed_z(jt, 0.5)
    ifr["joint_bed_below_arris_mm"] = round((jz - bz) * 1000, 3)
    ifr["joint_bed_in_slot"] = bool(0.0 < (jz - bz) < 0.030)

    pj = portal_isolation(bays)
    ifr["portal_isolation_joints"] = len(pj)
    ifr["portal_isolation_stations"] = sorted({round(j.t0, 3) for j in pj})
    ifr["portal_world_x"] = [round(float(route_xy(np.array([j.t0]),
                                                 np.array([0.0]))[0][0]), 3)
                             for j in pj[:1]]

    ep = edge_polyline(+1, 1.0, bays)
    en = edge_polyline(-1, 1.0, bays)
    tt3 = ep["t"]
    lo4, hi4 = edge_v(tt3)
    ifr["edge_points_each_side"] = int(len(tt3))
    ifr["edge_left_outside_ribbon"] = int((ep["v"] > hi4 + 1e-6).sum())
    ifr["edge_right_outside_ribbon"] = int((en["v"] < lo4 - 1e-6).sum())
    ifr["edge_z_range_mm"] = [round(float(ep["z"].min()) * 1000, 2),
                              round(float(ep["z"].max()) * 1000, 2)]
    ifr["edge_normals_unit"] = round(
        float(np.abs(np.hypot(ep["normal"][:, 0], ep["normal"][:, 1])
                     - 1.0).max()), 9)
    ifr["ok"] = bool(ifr["slab_top_z_vs_route_max_mm"] < 0.01
                     and ifr["slab_top_z_found_a_bay"] == ifr["slab_top_z_probes"]
                     and ifr["joint_frame_offset_mm"] < 0.01
                     and ifr["joint_bed_in_slot"]
                     and len(pj) > 0
                     and ifr["edge_left_outside_ribbon"] == 0
                     and ifr["edge_right_outside_ribbon"] == 0)
    rep["interface"] = ifr

    # --- 5. can the soffit be seen? -----------------------------------------
    bed_lo = BED_Z - 0.010 - 0.0045
    rep["soffit"] = dict(
        skirt_z=SKIRT_Z, bed_z_nominal=BED_Z,
        bed_z_worst_low=round(bed_lo, 4),
        clearance_mm=round((bed_lo - SKIRT_Z) * 1000, 1),
        occluded=bool(bed_lo > SKIRT_Z))

    # --- 6. reserve() cuts to the polygon -----------------------------------
    clear_reservations()
    b0 = min(bays, key=lambda b: abs(b.tc - 20.0) + abs(b.vc))
    cx, cy = b0.world_centre()
    side = 0.72
    ang = math.radians(23.0)
    poly = np.array([[cx + side * 0.5 * math.cos(ang + k * math.pi / 2)
                      - side * 0.5 * math.sin(ang + k * math.pi / 2),
                      cy + side * 0.5 * math.sin(ang + k * math.pi / 2)
                      + side * 0.5 * math.cos(ang + k * math.pi / 2)]
                     for k in range(4)])
    reserve(poly, "gully")
    T = np.linspace(*_bay_edges_tv(b0)[:2], 600)
    a_, b_ = _bay_span_arrays(b0, T)
    fgr = np.linspace(0.0, 1.0, 240)
    TT = np.repeat(T[:, None], 240, axis=1)
    VV = a_[:, None] + (b_ - a_)[:, None] * fgr[None, :]
    msk = _reservation_mask(TT, VV)
    cell = ((T[-1] - T[0]) / 599.0) * float((b_ - a_).mean()) / 239.0
    got = float(msk.sum()) * cell if msk is not None else 0.0
    clear_reservations()
    rep["reserve"] = dict(polygon_area_m2=round(side * side, 5),
                          cut_area_m2=round(got, 5),
                          error_pct=round(100.0 * (got - side * side)
                                          / (side * side), 2),
                          bounding_box_area_m2=round(
                              float((poly[:, 0].max() - poly[:, 0].min())
                                    * (poly[:, 1].max() - poly[:, 1].min())), 5))

    # --- 7 + 8. the built mesh ----------------------------------------------
    if scene and bpy is not None:
        obs = [o for o in bpy.context.scene.objects
               if o.type == "MESH" and o.name.startswith(PFX)]
        bayobs = [o for o in obs if "Bay_" in o.name]
        tris = 0
        scf_n = oil_n = tot_n = 0
        worst_scf = 0.0
        for o in bayobs:
            me = o.data
            for p in me.polygons:
                tris += max(len(p.vertices) - 2, 1)
            at = me.color_attributes.get("ars2")
            if at is not None:
                n = len(me.vertices)
                buf = np.empty(n * 4, np.float32)
                at.data.foreach_get("color", buf)
                buf = buf.reshape(-1, 4)
                s = float((buf[:, 1] > 0.25).mean())
                worst_scf = max(worst_scf, s)
                scf_n += int((buf[:, 1] > 0.25).sum())
                oil_n += int((buf[:, 0] > 0.25).sum())
                tot_n += n
        # the envelope AS BUILT, on a random sample of real vertices
        rs = np.random.default_rng(11)
        pick = rs.choice(len(bayobs), size=min(len(bayobs), 24), replace=False)
        dev = []
        for k in pick:
            o = bayobs[int(k)]
            me = o.data
            n = len(me.vertices)
            co = np.empty(n * 3, np.float32)
            me.vertices.foreach_get("co", co)
            co = co.reshape(-1, 3)
            M = np.array(o.matrix_world.to_4x4())
            co = co @ M[:3, :3].T + M[:3, 3]
            sel = rs.choice(n, size=min(n, 4000), replace=False)
            co = co[sel]
            co = co[co[:, 2] > SKIRT_Z + 0.02]        # top surface only
            if not len(co):
                continue
            tt2, vv2 = C.access_project(co[:, 0], co[:, 1])
            dev.append(co[:, 2] - datum_z(tt2, vv2))
        dev = np.concatenate(dev) if dev else np.zeros(1)
        rep["mesh"] = dict(
            objects=len(obs), bay_objects=len(bayobs), triangles=int(tris),
            surface_dev_min_mm=round(float(dev.min()) * 1000, 3),
            surface_dev_max_mm=round(float(dev.max()) * 1000, 3),
            surface_dev_p01_mm=round(float(np.percentile(dev, 1)) * 1000, 3),
            surface_dev_p99_mm=round(float(np.percentile(dev, 99)) * 1000, 3),
            note=("surface_dev INCLUDES the broom groove and the crazing, which "
                  "the level envelope deliberately excludes: a thing standing on "
                  "the slab bridges them"),
            scuff_vertex_fraction=round(scf_n / max(tot_n, 1), 5),
            oil_vertex_fraction=round(oil_n / max(tot_n, 1), 5),
            worst_bay_scuff_fraction=round(worst_scf, 4),
            unrubbered=bool(scf_n / max(tot_n, 1) < 0.02))

    rep["verify_s"] = round(time.time() - t0, 1)
    if out:
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        json.dump(rep, open(out, "w"), indent=1)
        print(">> wrote %s" % out)
    print(json.dumps(rep, indent=1))
    return rep


def interface_json(seed=SEED, out=None, ds=0.5):
    """The whole interface as DATA, for a dependant that would rather read a
    file than import a module.

    `access_road_saw_joint` (240 instances) and `access_road_kerb` (400 units)
    are built by agents who cannot ask questions and who may not want a numpy
    dependency to find out where a joint is.  Everything either of them needs is
    in here, in world coordinates, already evaluated.
    """
    bays = bay_layout(seed)
    joints = joint_segments(bays, seed)
    d = dict(
        item=ITEM_ID, version="1.0", seed=seed,
        module=os.path.abspath(__file__),
        collection=COLL_NAME, object_prefix=PFX, material_prefix=MPFX,
        contract=dict(
            route_total_m=float(ribbon()["T"][-1]),
            glass_plane_x=C.ACCESS_GLASS_X, flat_run_m=C.ACCESS_L2,
            road_width_m=C.ACCESS_ROAD_W, lane_edges_v=list(LANE_EDGES_V),
            portal_t_m=PORTAL_T, portal_isolation_half_m=PORTAL_ISOL_HALF,
            slab_thickness_m=SLAB_T, bed_z=BED_Z, skirt_z=SKIRT_Z,
            slab_top_min_m=SLAB_TOP_MIN_M, slab_top_max_m=SLAB_TOP_MAX_M,
            friction_mu=FRICTION_MU,
            kerb_seat_m=KERB_SEAT_M,
            edge_arris_chamfer_m=EDGE_ARRIS_CHAMFER_M,
            recess_lip_m=RECESS_LIP_M,
            attrs=list(ATTRS), attr_layers=[[n, list(c)] for n, c in ATTR_LAYERS],
            object_colour=OBJCOL_DOC),
        joint_section=dict(
            sawn=dict(width_m=JOINT_SAWN_W, depth_m=JOINT_SAWN_D,
                      kerf_w_m=JOINT_KERF_W, kerf_d_m=JOINT_KERF_D,
                      arris_m=ARRIS_SAWN_M),
            formed=dict(width_m=JOINT_FORMED_W, depth_m=JOINT_FORMED_D,
                        arris_r_m=ARRIS_FORMED_R),
            isolation=dict(width_m=JOINT_ISOL_W, depth_m=JOINT_ISOL_D,
                           arris_r_m=ARRIS_ISOL_R),
            seal_recess_m=list(SEAL_RECESS), seal_meniscus_m=SEAL_MENISCUS,
            overband_w_m=list(SEAL_OVERBAND_W), overband_h_m=SEAL_OVERBAND_H),
        bays=[dict(idx=b.idx, row=b.row, lane=b.lane,
                   t0=round(b.t0, 4), t1=round(b.t1, 4),
                   va=round(b.va, 4), vb=round(b.vb, 4),
                   world_centre=[round(x, 4) for x in b.world_centre()],
                   area_m2=round(b.area, 4),
                   finish=FIN_NAMES[b.fin],
                   broom_pitch_m=round(b.bpitch, 5),
                   broom_depth_m=round(b.bdepth, 6),
                   broom_across_deg=round(math.degrees(b.phi), 2),
                   datum_offset_m=round(b.dz, 5),
                   age=round(b.age, 4), crazing=round(b.craze, 4),
                   aggregate_exposure=round(b.exp, 4),
                   reinstated=bool(b.reinst), undowelled=bool(b.undowelled),
                   cracked=bool(b.crack), corner_broken=bool(b.corner))
              for b in bays],
        joints=[dict(idx=j.idx, kind=j.kind,
                     t0=round(j.t0, 4), t1=round(j.t1, 4),
                     v0=round(j.v0, 4), v1=round(j.v1, 4),
                     p0=[round(x, 5) for x in j.p0],
                     p1=[round(x, 5) for x in j.p1],
                     width_m=j.width_m, depth_m=j.depth_m,
                     arris_z0=round(j.arris_z0, 6),
                     arris_z1=round(j.arris_z1, 6),
                     fault_m=round(j.fault_m, 6),
                     bed_below_arris_m=round(j.bed_z, 5),
                     sealed=bool(j.sealed), overband=bool(j.overband),
                     spall=round(j.spall, 4), age=round(j.age, 4),
                     grit=round(j.grit, 4), left=j.left, right=j.right,
                     row=j.row, lane=j.lane)
                for j in joints],
        edges={}, counts=dict(bays=len(bays), joints=len(joints),
                              manifest_joint_segments=MANIFEST_JOINT_SEGMENTS))
    for side, nm in ((+1, "left"), (-1, "right")):
        e = edge_polyline(side, ds, bays)
        d["edges"][nm] = dict(
            side=side, ds_m=ds,
            t=[round(float(x), 4) for x in e["t"]],
            v=[round(float(x), 4) for x in e["v"]],
            xyz=[[round(float(e["xy"][i, 0]), 5), round(float(e["xy"][i, 1]), 5),
                  round(float(e["z"][i]), 6)] for i in range(len(e["t"]))],
            tangent=[[round(float(a), 5), round(float(b), 5)]
                     for a, b in e["tangent"]],
            outboard_normal=[[round(float(a), 5), round(float(b), 5)]
                             for a, b in e["normal"]])
    if out:
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        json.dump(d, open(out, "w"), indent=1)
        print(">> wrote %s (%.1f KB): %d bays, %d joints, %d + %d edge points"
              % (out, os.path.getsize(out) / 1024.0, len(bays), len(joints),
                 len(d["edges"]["left"]["t"]), len(d["edges"]["right"]["t"])))
    return d


def measure(seed=SEED):
    """Print the layout's headline numbers without touching Blender."""
    R = ribbon()
    bays = bay_layout(seed)
    joints = joint_segments(bays, seed)
    print(">> access_road_slab: %.4f m of route, %d bays, %d joint segments"
          % (float(R["T"][-1]), len(bays), len(joints)))
    print(">> px/m at the manifest's %.1f m on a %.0f mm lens: %.1f  "
          "(1 px = %.4f mm)"
          % (NEAREST_CAMERA_M, LENS_AT_CLOSEST_MM, PX_PER_M, M_PER_PX * 1000))
    for lbl, mm in (("broom groove pitch", 14.2), ("groove depth", 1.4),
                    ("sawn joint reservoir", JOINT_SAWN_W * 1000),
                    ("crazing crack width", CRAZE_W * 1000),
                    ("sand grain cell", 1.5)):
        print("   %-24s %6.2f mm = %7.2f px" % (lbl, mm, mm * PX_PER_M / 1000.0))
    return bays, joints


# =============================================================================
# 18.  CLI
# =============================================================================
def main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser(prog="access_road_slab")
    p.add_argument("cmd", choices=("scene", "verify", "measure", "interface"))
    p.add_argument("--out", default=None)
    p.add_argument("--quality", default="hero",
                   choices=tuple(QUALITY_SCALE))
    p.add_argument("--seed", type=int, default=SEED)
    p.add_argument("--budget", type=int, default=VERT_BUDGET)
    p.add_argument("--t0", type=float, default=None)
    p.add_argument("--t1", type=float, default=None)
    p.add_argument("--verify-out", default=None)
    p.add_argument("--interface-out", default=None)
    a = p.parse_args(argv)

    if a.cmd == "measure":
        measure(a.seed)
        return
    if a.cmd == "interface":
        interface_json(a.seed, a.out or a.interface_out)
        return
    if a.cmd == "verify":
        verify(a.seed, a.out, scene=(bpy is not None
                                     and any(o.name.startswith(PFX)
                                             for o in bpy.data.objects)))
        return
    tr = None
    if a.t0 is not None or a.t1 is not None:
        tr = (a.t0 or 0.0, a.t1 if a.t1 is not None else float(ribbon()["T"][-1]))
    st = build_test_scene(quality=a.quality, out=a.out, seed=a.seed,
                          t_range=tr, vert_budget=a.budget)
    print(">> STATS %s" % json.dumps(
        {k: v for k, v in st.items() if k != "macro_target"}))
    interface_json(a.seed, a.interface_out or os.path.join(
        _HERE, "access_road_slab_interface.json"))
    if a.verify_out:
        verify(a.seed, a.verify_out, scene=True)
    print(">> STAGE RESULT: ACCESS_ROAD_SLAB_SCENE_BUILT")


if __name__ == "__main__":
    main()







