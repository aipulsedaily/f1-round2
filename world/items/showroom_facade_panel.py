#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
showroom_facade_panel.py -- per-item hero campaign, item ``showroom_facade_panel``
(zone ``showroom_breach``, wave 1, build order 102, HERO, 180 instances).

WHAT THIS IS
============
The anodised aluminium RAINSCREEN CASSETTE that clads the showroom's upper
fascia -- the band of metal between the head of the curtain wall and the
parapet, on the two elevations the film ever sees: the EAST face the car is
launched through, and the SOUTH face it turns past.  180 panels, four courses,
one folded tray each, every one of them a separate mesh with its own shape.

It is NOT a plane with a metal shader on it.  A cassette is a 3 mm sheet folded
back 32 mm at all four edges and folded again to a 22 mm stiffening lip, hung on
hooks off a T-rail, with a 15 mm OPEN JOINT between it and its neighbours that
you can see 70 mm into.  Every one of those is geometry, and at the distance
this thing is filmed every one of them is several pixels wide.

THE ARITHMETIC THAT SETS THE DETAIL FLOOR
-----------------------------------------
    manifest: nearest_camera_m = 3.6, lens_at_closest_mm = 35, HERO,
              onscreen_px_4k = 1244 over px_measured_dimension_m = 1.2,
              instances = 180, dependents = 3

    px_per_m = (3840 * 35 / 36) / 3.6 = 1037.04 px/m  ->  1 px = 0.9643 mm

and the contract sun is at 12.47061 deg elevation.  BUT THE CONTRACT'S
SUN_SHADOW_RATIO = 4.5222 IS A GROUND QUANTITY -- 1/tan(12.5 deg), the run on a
surface whose normal is vertical -- AND THIS IS A WALL.  Measured against the
contract sun direction, the sun stands 31.2 deg above the EAST face and 55.9 deg
above the SOUTH face, so the real ratios are 1.652 and 0.678.  Earlier versions
of this file quoted the ground ratio throughout and therefore overstated every
shadow on this item by 2.74x (east) and 6.67x (south).  See SHADOW_RATIO and
shadow_px(), which now takes the elevation.

A facade under this sun is read by its shadows AND by its reflection, and the
reflection is the louder of the two on a near-specular anodised face.  A bump
map casts no shadow either way.

EVERY NUMBER IN THIS TABLE IS READ OFF THE CODE BELOW OR OFF THE BUILD REPORT,
because an earlier version of it had drifted three edits behind the module and a
stale specification is worse than none -- it is a claim wearing a measurement's
clothes.  Values marked MEASURED come from verify() in
render/items/showroom_facade_panel/build.json.

    5.5 / 4.5 mm outer fold radius        5.7 / 4.7 px across (FOLD_R_OUT, one
                                          per fabricator).  NOT 9 mm: at 9 mm
                                          the two flanking curves plus the gap
                                          read as one 33 mm soft valley -- the
                                          "smooth tube" failure with a
                                          different cross-section.  See
                                          FOLD_R_OUT for the press-brake
                                          arithmetic that sets it.
    15 mm nominal open joint              15.6 px wide, 70 mm deep -> at 12.5 deg
                                          the sun cannot reach the bottom of it,
                                          so it is a BLACK line with a lit top
                                          arris, not a drawn one.
                                          MEASURED as built: 13.7 - 16.3 mm,
                                          mean 15.0 -- the spread is fabrication
                                          tolerance and installed tilt, and it
                                          is variation axis 3 doing its work.
    3.0 mm sheet thickness at the lip      3.1 px, seen from below
    45 mm drip return on the bottom course 47 px of soffit in an upward shot
    4.8 mm domed rivet, 1.6 mm proud       9.5 mm flange = 9.8 px, throws
                                          2.6 mm = 2.7 px of shadow on the EAST
                                          face (1.1 px on the south).  It was
                                          quoted as 7.5 px for three iterations
                                          off the GROUND shadow ratio.
    oil-can amplitude                      MEASURED p50 1.39 mm, p95 5.06 mm,
                                          max 5.51 mm.  1.4 mm displaces only
                                          1.4 px, but it tilts the surface
                                          ~0.26 deg -> 0.5 deg in the
                                          reflection, which on a near-specular
                                          anodised face is the whole read.
    2.0 mm panel-to-panel plane step       2.1 px, throws 3.3 mm = 3.4 px east
                                          (was quoted 9.4 px, ground ratio)
    0.22 deg installed tilt max            (tilt_u/tilt_v) = 4.6 mm over a 1.2 m
                                          panel; MEASURED max as built 0.387 deg
                                          once fabrication offset is added.
                                          It opens each joint into a WEDGE,
                                          which is how a camera can tell 180
                                          panels were hung by hand.
    1.5 mm top-hat stiffener sheet         1.6 px, seen through the joint
    22 mm bonded-stiffener web             23 px of depth inside the shadow gap
    0.40 mm shader bevel on the cut lip    0.41 px -- BELOW the pixel, and the
                                          only edge treatment on this item that
                                          is a shader node rather than mesh
    0.05 mm rolling grain                  0.05 px -- shader, correctly
    0.03-0.11 mm roll-forming ripple       0.03-0.11 px -- shader, and it was
                                          MESH for two iterations before an FFT
                                          of the render proved the mesh period
                                          was what you could see.  See face_disp.

Everything above 1 px in that table is MESH.  The mesh is graded: CELL_EDGE =
4.5 mm cells (4.7 px) in a 70 mm band round every panel's perimeter, where the
eye reads the joint and where the plate curvature is highest, easing to
CELL_MID = 9.0 mm (9.3 px) across the middle.  9 mm, NOT the 18 mm this module
shipped with for six iterations: 18 mm cells can only carry a 36 mm feature, so
the face could hold the oil-canning and nothing else, and a 1:1 crop measured a
median adjacent-pixel difference of ZERO.  The gate confirms the grading
independently -- p10 edge 0.73 px, median 9.33 px, which is CELL_MID exactly.

WHY THE PANELS ARE INDIVIDUAL OBJECTS AND NOT ONE INSTANCED MESH
----------------------------------------------------------------
    "i dont want repeat stuff aka one tree spammed 100 times"

The manifest's three variation axes are anodising batch drift, oil-canning and
fixing shadow gaps.  Two of those three are SHAPE.  A facade of one cassette
instanced 180 times with random rotations is exactly the named failure, and it
is also just wrong: oil-canning is the plate's own buckling mode and no two
panels buckle the same, which is why real anodised facades read as a quilt.
So every panel is generated from its own seed with its own mode amplitudes, its
own fabrication tolerance, its own installed tilt, its own dents and its own
batch, and the gate measures all 180 directly (no geometry-nodes indirection --
`per_instance_variation` is evaluated on the objects themselves).

===========================================================================
THE PUBLIC INTERFACE.  This item is a FOUNDATION: three manifest items build
on it and cannot ask questions.  Everything below is public and stable, and
every number is also written to showroom_facade_panel_interface.json on build.
===========================================================================
Dependants named in the manifest:
    showroom_signage_lettering   (1, filmed at 4.0 m -- mounts on MY face)
    showroom_rainwater_goods     (8, filmed at 5.0 m -- fixes through MY face)
    showroom_parapet_coping      (1, filmed at 9.0 m -- caps MY top course)

--- 1. WHERE THE CLADDING FACE IS -----------------------------------------

    CLAD_X_E = +14.940      the EAST cladding face plane (world x)
    CLAD_Y_S = -10.940      the SOUTH cladding face plane (world y)

    Both are 60 mm BEHIND their own glass plane -- east behind
    C.ACCESS_GLASS_X = 15.000, south behind GW_Front_Glass at y = -11.000 --
    so the fascia throws a 60 mm shadow reveal over the glazing head AND so
    that NOTHING this module builds crosses the breach plane.  Verified by
    measurement in verify(): max built x = 14.955, so the clearance to the
    breach plane is 45 mm, not 60.

    THE NOMINAL PLANE IS NOT THE AS-BUILT SURFACE, and a dependant that mounts
    flush to CLAD_X_E will interpenetrate a panel.  This docstring used to
    claim "max built x = 14.940" and cite verify() as the authority for it;
    verify() has always printed 14.955.  The nominal plane is where the panels
    are SET OUT, and then every one of them is moved off it by three real
    things -- fabrication offset (+-1.8 mm), installed tilt (up to 0.22 deg,
    which is +-4.6 mm over a 1.2 m panel) and its own oil-canning (up to
    5.5 mm proud).  Those stack:

        FACE_PROUD_MAX = 0.015    east, MEASURED over all 180 panels
                                  (south 14.47 mm; the corner 3.63 mm)

    so ANYTHING BEARING ON THIS FACADE MUST STAND OFF CLAD_X_E BY >= 0.015 m,
    or read the panel it actually lands on.  face_clearance(elev) returns the
    measured number and dump_interface() publishes the whole envelope under
    'as_built'.  The same applies at the top: as-built max z is 10.33519, i.e.
    4.81 mm BELOW CLAD_TOP_Z, which is why clad_top_edge_z() exists and why a
    coping laid to a flat 10.340 bears on nothing.

    CLAD_TOP_Z    = 10.340  top edge of the top course
    PARAPET_TOP_Z = 10.400  the silhouette line the manifest names for
                            showroom_parapet_coping.  The 60 mm between them
                            is the coping's, not mine.
    CLAD_BOTTOM_Z =  6.340  bottom edge of the cut course.  Below it is
                            curtain_wall_head_extrusion's flashing.
    CLAD_Y_N = +9.350, CLAD_X_W = -13.350   the far ends of the two runs.
                            The round-2 upper storey is set back
                            UPPER_SETBACK = 1.900 m from the round-1 shell on
                            the north and west, which is why the runs end
                            there and not at the shell line.

    face_plane(elev)     -> (point, outward_normal) for elev in 'E' / 'S'
    face_point(elev,s,z) -> world XYZ of a point on the nominal face plane,
                            s measured along the run (see below)
    Panel.centre_world   every panel's own face centre, as built

--- 2. THE SET-OUT, AND WHY IT IS THE SET-OUT ------------------------------

    MODULE_M = 1.100  =  MULLION_PITCH / 2.  The curtain wall below has 11
    mullions at 2.200 m centres with one on the launch axis y = 0
    (mullion_intact's own record), so cladding joints at y = 1.100*k put EVERY
    SECOND JOINT dead on a mullion.  That is the manifest's

        "The panel joint rhythm is the only thing that gives the building
         scale at both ends."

    and it is the reason the east corner cassette is 1.040 m and not 0.600 m:
    the corner takes up the slack so the field lands on the grid.

    COURSES (top down)   10.340 -> 9.140 -> 7.940 -> 6.740 -> 6.340
                         three at 1.200 (the manifest's typical_height_m) and
                         one CUT course at 0.400 on the head flashing.
    JOINT_M = 0.015      nominal open joint.  Real built joints in this module
                         run 11.2 - 18.9 mm because the panels carry
                         fabrication tolerance and installed tilt.
    per course           1 corner + 18 east + 26 south = 45
    total                45 * 4 = 180  (== the manifest's declared count)

    panels()             -> [Panel, ...] deterministic, no Blender needed.
    panel_at(elev, course, col) -> Panel

--- 3. FIXING SOMETHING TO THIS FACADE -------------------------------------

    SIGN_ZONE            dict(elev='E', s0, s1, z0, z1) -- the east fascia
                         panel band reserved for showroom_signage_lettering,
                         course 1 (z 7.940..9.140), y -3.300..+3.300.  The
                         panels inside it carry a 4 mm backing plate bonded to
                         their rear and are flagged Panel.sign = True, so a
                         letter stud can be pulled up tight without dimpling
                         the sheet.
    sign_fix_grid()      -> [(x, y, z, panel_name), ...] the permitted stud
                         positions, on a 100 mm grid, ALREADY CHECKED against
                         the panel joints (no stud lands in a shadow gap) and
                         against the sub-frame behind.
    SIGN_SHELTER_M       0.045  how far the sign backplate's dirt shadow
                         spreads past the letters.  MY material already carries
                         a clean rectangle over SIGN_ZONE; the LETTER-SHAPED
                         part of that shadow is the signage item's to add.

    RWP_LINES            -> [dict(elev, s, dia, reveal_depth, panels=[...])]
                         the three rainwater downpipe runs that fall on MY two
                         elevations.  Each is a RECESSED COLUMN: the whole
                         panel column is set back REVEAL_DEPTH = 0.090 and the
                         two flanking columns carry a 100 mm return, so the
                         pipe sits in a real slot instead of standing off a
                         flat wall.  The cheeks and the back of the slot are
                         SFP_Sub_ geometry, already built.
    rwp_bracket_points() -> [(x, y, z, panel_name), ...] where a pipe bracket
                         may fix.  They are on the horizontal carrier rails at
                         1.200 m centres, NOT into the cassette (a cassette
                         carries no load).  A bracket anywhere else is wrong.
    HOPPER_Z = 10.140    hopper rim level, in the top course.  MY material
                         already carries the overflow stain plume below each
                         hopper (attribute 'run' is boosted there), so the
                         rainwater item does not have to paint one on.

    COPING_BEARING_Z = 10.340   what showroom_parapet_coping sits against.
    COPING_OVERHANG_M = 0.030   how far it must project past CLAD_X_E /
                         CLAD_Y_S to throw its drip clear of my top course.
                         MY material already carries the sheltered pale band
                         in the top 0.150 m of the top course, which is what
                         the underside of a coping actually does to a facade.
    clad_top_edge_z(elev, s) -> the AS-BUILT top edge z at a station.  It is
                         not 10.340 everywhere: installed tilt and fabrication
                         tolerance move it by up to +-2.4 mm, and a coping laid
                         to a flat 10.340 will rock.  Use this.

--- 4. THE MATERIAL, FOR ANYTHING EMITTING GEOMETRY INTO IT ----------------

    mat_anodised()       the panel material.  It reads FIFTEEN vertex
                         attributes; geometry emitted into it without them
                         renders as the zero case (a raw, brand-new, unstained
                         panel from batch 0), which is wrong but not broken.
    bake_panel_attrs(mesh, **overrides)   writes all fifteen with sane values.
                         len(ATTRS) == 15; the count below is the authority.
    ATTRS = ('bat','rack','imm','grn','gflip','fold','edg','run','sky',
             'dam','hand','wld','shl','age','sd')

    Every material in this module reads TexCoord -> Object and every mesh is
    recentred on emit, per law 6.  The per-panel decorrelation that would
    normally come from Geometry -> Position comes from the 'sd' attribute
    driving the 4D noise W, so two panels 1.1 m apart do not share a texture.

--- 5. WHAT IS DELIBERATELY NOT MINE ---------------------------------------

    the glazing, its mullions, transoms, sill and head        (their own items)
    the coping itself, the downpipes, the letters             (their own items)
    the west and north elevations of the upper storey         nothing in the
                                                              film ever sees
                                                              them; the set-out
                                                              is exposed so
                                                              they can be
                                                              continued
    the parapet upstand behind the top course, the sheathing, the insulation
                                                              -- built here as
                                                              SFP_Sub_ /
                                                              SFP_Ctx_ context
                                                              so the light and
                                                              the joint depth
                                                              are real, but
                                                              they are not the
                                                              item and they do
                                                              not carry the
                                                              SFP_Panel_ prefix

OBJECT NAMING
    SFP_Panel_<E|S|C><course>_<col>   the 180 panels.  THIS is the gate prefix.
    SFP_Sub_*                          carrier rails, brackets, baffles,
                                       reveal cheeks, head flashing, parapet
    SFP_Ctx_*                          shell, glazing band, ground -- light only
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))          # world/items
_WORLD = os.path.dirname(_HERE)                             # world
_ROOT = os.path.dirname(_WORLD)                             # f1-round2
for _p in (_WORLD, os.path.join(_ROOT, "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import world_contract as C                                   # noqa: E402

try:
    import bpy                                               # noqa: E402
    from mathutils import Matrix, Vector                     # noqa: E402
    HAVE_BPY = True
except Exception:                                            # pragma: no cover
    HAVE_BPY = False


# =============================================================================
# 1.  THE MANIFEST'S OWN NUMBERS
# =============================================================================
ITEM = "showroom_facade_panel"
PFX = "SFP_Panel_"
SUBPFX = "SFP_Sub_"
CTXPFX = "SFP_Ctx_"
COLL_NAME = "SFP_ShowroomFacadePanel"
LIBPFX = "SFPLIB_"

NEAREST_CAMERA_M = 3.6
LENS_AT_CLOSEST_MM = 35.0
SENSOR_MM = 36.0
RES_X_4K, RES_Y_4K = 3840, 2160
DECLARED_INSTANCES = 180
TYPICAL_HEIGHT_M = 1.2

PX_PER_M = RES_X_4K * LENS_AT_CLOSEST_MM / SENSOR_MM / NEAREST_CAMERA_M   # 1037.04
MM_PER_PX = 1000.0 / PX_PER_M                                             # 0.9643
SEED = 90210


def px(metres):
    """Screen pixels this many metres occupies at the item's filmed distance."""
    return metres * PX_PER_M


# THE CONTRACT'S SHADOW RATIO IS A GROUND QUANTITY AND THIS MODULE WAS USING IT
# ON A WALL.  world_contract.py:1669 defines
#     SUN_SHADOW_RATIO = 4.5222        # horizontal run per unit height
# which is 1/tan(12.5 deg): the run a proud feature throws on a surface whose
# normal is VERTICAL.  A facade's normal is horizontal, and the sun is nowhere
# near grazing to it.  Measured against the contract sun direction
# (0.5179, -0.8278, 0.2159):
#
#     surface              incidence from normal   sun above the SURFACE   ratio
#     ground   (0, 0, 1)        77.5 deg                12.5 deg          4.522
#     EAST     (1, 0, 0)        58.8 deg                31.2 deg          1.652
#     SOUTH    (0,-1, 0)        34.1 deg                55.9 deg          0.678
#
# So every "throws N px of shadow" figure this module used to quote was too big
# by 2.74x on the east elevation and 6.67x on the south.  That is the same shape
# of error as the wave-1 pattern -- a feature sized against an amplitude that
# never reaches pixels -- except the arithmetic, not the amplitude, was wrong.
# The features still read (a 1.6 mm rivet throws 2.7 px on the east, not 7.5),
# but they read less than the docstring claimed, and the claim is what future
# sizing decisions would have been made against.
SHADOW_RATIO = dict(E=1.652, S=0.678, GROUND=float(C.SUN_SHADOW_RATIO))


def shadow_px(height_m, elev="E"):
    """Screen pixels of shadow a proud feature throws ON THIS ELEVATION.

    `elev` is 'E', 'S' or 'GROUND'.  It is NOT optional in spirit: passing the
    contract's ground ratio for a wall is the bug this signature exists to stop.
    """
    return height_m * SHADOW_RATIO[elev] * PX_PER_M


# =============================================================================
# 2.  THE SET-OUT  --  measured datums first, then the grid they imply
# =============================================================================
# build_architecture's MEASURED round-1 pavilion, copied here as data (not
# re-derived): the shell plan and the two glass planes.
R1_SHELL = (-15.250, 15.000, -11.250, 11.250)
GLASS_X = float(C.ACCESS_GLASS_X)            # 15.000, the breach plane
GLASS_Y_S = -11.000                          # GW_Front_Glass
GLASS_HEAD_Z = 6.090                         # top of the glass
HEAD_TOP_Z = 6.250                           # top of curtain_wall_head_extrusion

FACE_SETBACK = 0.060       # fascia behind the glass plane -> a shadow reveal at
                           # the head, and nothing of mine crosses x = 15.000
UPPER_SETBACK = 1.900      # round-2 upper storey set back from the shell on the
                           # north and west.  It is what makes the two runs come
                           # out at exactly 45 panels a course.

CLAD_X_E = GLASS_X - FACE_SETBACK              # +14.940
CLAD_Y_S = GLASS_Y_S + FACE_SETBACK            # -10.940
CLAD_Y_N = R1_SHELL[3] - UPPER_SETBACK         #  +9.350
CLAD_X_W = R1_SHELL[0] + UPPER_SETBACK         # -13.350

PARAPET_TOP_Z = 10.400
CLAD_TOP_Z = 10.340
CLAD_BOTTOM_Z = 6.340
COURSE_H = (1.200, 1.200, 1.200, 0.400)        # top course first
JOINT_M = 0.015
MODULE_M = 1.100
MULLION_PITCH = 2.200
CORNER_LEG_E = 1.040      # so the east field joints land on y = 1.100*k
CORNER_LEG_S = 0.600
CORNER_FILLET_M = 0.020   # external corner radius of the corner cassette

# --- fabrication ------------------------------------------------------------
SHEET_T = 0.0030          # 3.0 mm AA5005 -- the anodising alloy
# THE FOLD RADIUS IS THE WHOLE READ OF THE JOINT, and the first version had it
# wrong by a factor of two.  At 9.0 mm outer radius each panel rolls away from
# its own face over 9 mm, so a 15 mm open joint is flanked by 18 mm of curve
# and the whole 33 mm reads, peeped at 4x, as ONE SOFT VALLEY -- the "smooth
# tube" failure with a different cross-section.  A press brake folding 3.0 mm
# AA5005-H14 works to an INSIDE radius of 0.5x to 1.0x thickness on this alloy,
# so 1.5-3.0 mm inside + the 3.0 mm sheet = 4.5-6.0 mm OUTSIDE.  That is the
# number, and it is the fabricator's, not a taste.  It halves the curved band,
# leaves the face flat right up
# to the arris, and turns the joint into what it is on a real rainscreen: a
# hard bright line, a black slot, a hard bright line.
FOLD_R_OUT = (0.0055, 0.0045)     # outer fold radius, per fabricator
RETURN_D = (0.032, 0.035)         # standard return depth, per fabricator
LIP_R2 = 0.0050           # the lip fold, inside the cavity.  Tighter than the
                          # outer fold because it is a return bend on a flange
                          # that nobody has to look at -- and because at 9 mm it
                          # rolled the return flank out of sight, so the joint
                          # had no visible depth at all.
LIP_L = 0.022
DRIP_RETURN_D = 0.045     # bottom course: a deeper return IS the drip
DRIP_R2 = 0.0050          # and a sharper arris for the water to break on
REVEAL_RETURN_D = 0.100   # the two columns flanking a rainwater slot
REVEAL_DEPTH = 0.090      # how far a rainwater column is set back

STIFF_PITCH_MAX = 0.480   # bonded top-hat stiffener spacing
STIFF_W = 0.066           # overall width of the top hat
STIFF_CROWN = 0.028
STIFF_D = 0.022
STIFF_T_FACTOR = 0.50     # 1.5 mm sheet against the cassette's 3.0

RIVET_R_FLANGE = 0.00475
RIVET_H = 0.0016
RIVET_PITCH = 0.300

# --- the AS-BUILT envelope, MEASURED, not derived -------------------------
# work/sfp/envelope.py walks all 180 evaluated meshes in the test blend and
# reports the world-space extremes.  These are those numbers.  They exist
# because the nominal set-out plane is NOT the surface a dependant meets:
# fabrication offset + installed tilt + oil-canning move the face off it, and
# the sum is a centimetre and a half.  Re-measure with:
#     blender -b <test.blend> --factory-startup -P work/sfp/envelope.py
FACE_PROUD_MAX = dict(E=0.01500, S=0.01447, C=0.00363)
TOP_EDGE_BELOW_NOMINAL = 0.00481     # as-built max z is 10.33519, not 10.340
BREACH_CLEARANCE_M = 0.045           # 15.000 - 14.955, measured


def face_clearance(elev="E"):
    """How far off CLAD_X_E / CLAD_Y_S a fixing must stand to clear the panels.

    MEASURED over all 180 as-built panels, not derived from the tolerances.
    Use this, not FACE_SETBACK, for anything that bears on the facade.
    """
    return float(FACE_PROUD_MAX.get(elev, max(FACE_PROUD_MAX.values())))


SIGN_ZONE = dict(elev="E", s0=-3.300, s1=3.300, z0=7.940, z1=9.140)
SIGN_SHELTER_M = 0.045
COPING_BEARING_Z = CLAD_TOP_Z
COPING_OVERHANG_M = 0.030
HOPPER_Z = 10.140

# --- mesh grading (hero) ----------------------------------------------------
# CELL_MID WAS 18 mm AND THAT WAS A CEILING ON THE ITEM, not a saving.  18 mm
# cells can only carry features of 36 mm and up, so the face could hold the
# oil-canning (300-600 mm) and nothing else -- and a measured 1:1 crop of the
# sixth macro came back with a MEDIAN ADJACENT-PIXEL DIFFERENCE OF ZERO over a
# 600 x 600 px patch of panel.  Rendered at 8192 samples with the denoiser off
# it measured the same, so this was never a sampling or a denoising problem:
# there was no signal in the surface to begin with.
#
# 9 mm cells resolve down to an 18 mm feature = 19 px, which is what the
# ROLL-FORMING RIPPLE needs (see face_disp): every levelled aluminium coil
# carries a 40-90 mm transverse ripple of 0.05-0.25 mm, it is the reason a real
# metal facade shimmers along its length in raking light, and it is the single
# most metal thing a flat sheet does.  It costs 4x the face cells and it is the
# difference between a rendering of a metal and a metal.
CELL_EDGE = 0.0045        # 4.7 px
CELL_MID = 0.0090         # 9.3 px -- resolves the 40-90 mm rolling ripple
GRADE_BAND = 0.070
RIPPLE_MESH_AMP = float(os.environ.get("SFP_RIPPLE_MESH", "0.0"))
N_ARC1 = 10               # segments round the outer fold  (0.86 mm each, and
                          # the arc is only 8.6 mm long now, so the arris is
                          # smooth AND crisp instead of neither)
N_RET = 3                 # segments down the return
N_ARC2 = 6                # segments round the lip fold    (1.31 mm each)
N_LIP = 2
N_CORNER = 7              # psi steps round a face corner
N_PROFILE = N_ARC1 + N_RET + N_ARC2 + N_LIP        # = 21 rings past the tangent

DRAFT = dict(CELL_EDGE=0.010, CELL_MID=0.040, GRADE_BAND=0.050,
             N_ARC1=3, N_RET=1, N_ARC2=2, N_LIP=1, N_CORNER=3)


# =============================================================================
# 3.  DETERMINISTIC FIELDS
# =============================================================================
_U32 = np.uint32


def vh(*keys):
    """FNV-1a over integer key arrays -> float64 in [0, 1).  Broadcasts."""
    arrs = [np.asarray(k) for k in keys]
    shp = np.broadcast(*arrs).shape if len(arrs) > 1 else np.shape(arrs[0])
    h = np.full(shp, _U32(2166136261), dtype=np.uint32)
    with np.errstate(over="ignore"):
        for kk in arrs:
            kk = (np.rint(kk).astype(np.int64) if kk.dtype.kind == "f"
                  else kk.astype(np.int64))
            kk = (kk & 0xFFFFFFFF).astype(np.uint32)
            h = (h ^ kk) * _U32(16777619)
            h = h ^ (h >> _U32(13))
            h = h * _U32(2654435761)
            h = h ^ (h >> _U32(16))
    return (h & _U32(0xFFFFFF)).astype(np.float64) / 16777215.0


def h01(*keys):
    """Scalar version."""
    return float(vh(*[np.int64(k) for k in keys]))


def rnd(a, b, *keys):
    return a + (b - a) * h01(*keys)


def rint(a, b, *keys):
    return int(a + (b - a + 1) * h01(*keys) * 0.999999)


def chance(p, *keys):
    return h01(*keys) < p


def pick(seq, *keys):
    return seq[min(int(h01(*keys) * len(seq)), len(seq) - 1)]


def sstep(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def smoothstep(e0, e1, x):
    return sstep((np.asarray(x, float) - e0) / max(1e-12, (e1 - e0)))


def _vnoise2(x, y, seed):
    ix = np.floor(x)
    iy = np.floor(y)
    fx, fy = x - ix, y - iy
    ux, uy = sstep(fx), sstep(fy)
    ix = ix.astype(np.int64)
    iy = iy.astype(np.int64)
    s = np.int64(seed)
    a = vh(ix, iy, s)
    b = vh(ix + 1, iy, s)
    c = vh(ix, iy + 1, s)
    d = vh(ix + 1, iy + 1, s)
    return (a * (1 - ux) + b * ux) * (1 - uy) + (c * (1 - ux) + d * ux) * uy


def fbm2(x, y, seed, oct=4, gain=0.5, lac=2.07):
    tot = np.zeros(np.broadcast(x, y).shape)
    amp, frq, nrm = 1.0, 1.0, 0.0
    for o in range(oct):
        tot = tot + amp * _vnoise2(x * frq, y * frq, seed * 131 + o * 17)
        nrm += amp
        amp *= gain
        frq *= lac
    return tot / nrm


# =============================================================================
# 4.  THE PANEL RECORD AND THE SET-OUT ITSELF
# =============================================================================
KIND_FIELD = "field"
KIND_CLOSER = "closer"
KIND_CORNER = "corner"
KIND_LOUVRE = "louvre"
KIND_ACCESS = "access"
KIND_REVEAL = "reveal"
KIND_REPL = "replaced"

N_BATCHES = 7             # a job this size arrives in six to eight deliveries
RACK_SIZE = 28            # cassettes on one anodising jig


class Panel(object):
    """One cassette.  All lengths in metres, all coordinates in the WORLD frame
    except `s` which is measured along the elevation's own run."""

    __slots__ = ("idx", "elev", "course", "col", "kind", "s0", "s1", "w",
                 "z_top", "z_bot", "h", "face_w", "face_h", "fab", "batch",
                 "rack", "grain", "gflip", "seed", "tilt_u", "tilt_v", "off_n",
                 "sev", "dents", "rivets", "stiff", "sign", "reveal",
                 "ret_d", "fold_r", "path", "segments", "aperture",
                 "centre_world", "matrix", "name", "age", "note")

    def __init__(self, **kw):
        for k in self.__slots__:
            setattr(self, k, kw.get(k))

    def as_dict(self):
        d = {}
        for k in self.__slots__:
            v = getattr(self, k)
            if k in ("matrix",):
                continue
            if isinstance(v, np.ndarray):
                v = v.tolist()
            d[k] = v
        return d


def course_levels():
    """-> [(z_top, z_bot, h), ...] top course first."""
    out = []
    z = CLAD_TOP_Z
    for h in COURSE_H:
        out.append((z, z - h, h))
        z -= h
    return out


def _run_widths(run_len, module, min_closer=0.400):
    """Fill a run with nominal modules and a closer, the way a facade
    contractor does: whole modules from the set-out end, then the remainder as
    ONE closer -- unless the remainder is a sliver, in which case the last
    nominal module is given back and the remainder is split between TWO."""
    n = int(math.floor(run_len / module + 1e-9))
    rem = run_len - n * module
    if rem < 1e-6:
        return [module] * n
    if rem >= min_closer:
        return [module] * n + [rem]
    n -= 1
    rem = run_len - n * module
    return [module] * n + [rem * 0.5, rem * 0.5]


# The three rainwater slots that fall on the two clad elevations, named by the
# COLUMN INDEX of the recessed panel (field columns, 0-based from the corner).
RWP_COLUMNS = (("E", 13), ("S", 6), ("S", 19))
# Plant intake louvres: (elev, column) -- a plant room sits behind the south
# fascia at its west end.
LOUVRE_COLUMNS = (("S", 22), ("S", 23))
LOUVRE_COURSES = (1, 2)
# Roof access hatch surround: two access cassettes on the east, top course.
ACCESS_PANELS = (("E", 2, 0), ("E", 3, 0))


def panels(seed=SEED):
    """THE SET-OUT.  Deterministic, no Blender required.  -> [Panel, ...]."""
    out = []
    lv = course_levels()

    # --- run geometry --------------------------------------------------------
    # EAST: s measured along +y from the south corner plane.
    e_run = CLAD_Y_N - CLAD_Y_S                       # 20.290
    e_field_run = e_run - CORNER_LEG_E                # 19.250
    e_w = _run_widths(e_field_run, MODULE_M)
    # SOUTH: s measured along -x from the east corner plane.
    s_run = CLAD_X_E - CLAD_X_W                       # 28.290
    s_field_run = s_run - CORNER_LEG_S                # 27.690
    s_w = _run_widths(s_field_run, MODULE_M)

    rwp = {(e, c) for (e, c) in RWP_COLUMNS}
    louv = {(e, c) for (e, c) in LOUVRE_COLUMNS}
    acc = {(e, cr, c) for (e, cr, c) in ACCESS_PANELS}

    idx = 0
    for ci, (zt, zb, hh) in enumerate(lv):
        # ---- the corner cassette -------------------------------------------
        p = Panel(idx=idx, elev="C", course=ci, col=0, kind=KIND_CORNER,
                  s0=0.0, s1=0.0, w=CORNER_LEG_E + CORNER_LEG_S,
                  z_top=zt, z_bot=zb, h=hh)
        out.append(p)
        idx += 1
        # ---- east field -----------------------------------------------------
        s = CORNER_LEG_E
        for k, w in enumerate(e_w):
            kind = KIND_FIELD
            if (("E", k) in rwp):
                kind = KIND_REVEAL
            elif ("E", ci, k) in acc:
                kind = KIND_ACCESS
            elif w < MODULE_M - 1e-6:
                kind = KIND_CLOSER
            out.append(Panel(idx=idx, elev="E", course=ci, col=k, kind=kind,
                             s0=s, s1=s + w, w=w, z_top=zt, z_bot=zb, h=hh))
            idx += 1
            s += w
        # ---- south field ----------------------------------------------------
        s = CORNER_LEG_S
        for k, w in enumerate(s_w):
            kind = KIND_FIELD
            if ("S", k) in rwp:
                kind = KIND_REVEAL
            elif ("S", k) in louv and ci in LOUVRE_COURSES:
                kind = KIND_LOUVRE
            elif w < MODULE_M - 1e-6:
                kind = KIND_CLOSER
            out.append(Panel(idx=idx, elev="S", course=ci, col=k, kind=kind,
                             s0=s, s1=s + w, w=w, z_top=zt, z_bot=zb, h=hh))
            idx += 1
            s += w

    _decorate(out, seed)
    return out


def _decorate(ps, seed):
    """Everything that is not the grid: fabrication, batch, damage, tolerance.

    THE ANODISING BATCH IS NOT RANDOM PER PANEL.  Panels arrive on pallets and
    a pallet is fixed by a gang working across and up, so batch is a SPATIALLY
    CORRELATED field -- which is exactly why a real anodised facade reads as
    large soft patches and not as noise.  Getting that wrong is the difference
    between "aluminium" and "a checkerboard".
    """
    n = len(ps)
    # a replaced panel comes from a much later batch and is fixed by a
    # different gang, hence a different fabricator's corner detail.
    repl = set()
    for k in range(3):
        repl.add(rint(0, n - 1, seed, 7717, k))

    for p in ps:
        s = (seed, p.idx, 991)
        p.seed = int(h01(*s) * 1e9)
        p.name = "%s%s%d_%02d" % (PFX, p.elev, p.course, p.col)

        # ---- pallet / batch field ------------------------------------------
        # station along the whole 48.6 m of facade, so the field is continuous
        # across the corner and up the courses.
        st = (p.s0 if p.elev != "C" else 0.0) + (0.0 if p.elev == "E" else 20.3)
        f = fbm2(np.array([st / 6.4]), np.array([p.course / 1.9]), 4231, oct=3)
        b = int(np.clip(f[0] * N_BATCHES, 0, N_BATCHES - 1))
        if p.idx in repl:
            b = N_BATCHES - 1
            p.kind = KIND_REPL
        p.batch = b
        p.rack = rint(0, RACK_SIZE - 1, seed, p.idx, 313)
        # grain: 0 = rolling direction along the panel's long axis (correct),
        # 1 = ACROSS it.  Two panels on this facade went up the wrong way.  It
        # is the commonest complaint on an anodised job and it is visible.
        p.grain = 1 if chance(0.011, seed, p.idx, 4177) else 0
        p.gflip = 1 if chance(0.42, seed, p.idx, 5501) else 0
        p.age = 1.0 if p.kind != KIND_REPL else 0.28

        # ---- fabricator ----------------------------------------------------
        p.fab = 1 if (p.kind == KIND_REPL or chance(0.34, seed, p.idx, 8123)) else 0
        p.fold_r = FOLD_R_OUT[p.fab]
        p.ret_d = RETURN_D[p.fab]

        # ---- fabrication tolerance: the panel is NOT its nominal size -------
        # +-1.4 mm on width and height.  This is where the joint variation
        # actually comes from -- it is not a decorative jitter.
        dw = rnd(-0.0014, 0.0014, seed, p.idx, 61)
        dh = rnd(-0.0014, 0.0014, seed, p.idx, 62)
        p.face_w = max(0.20, p.w - JOINT_M + dw)
        p.face_h = max(0.20, p.h - JOINT_M + dh)

        # ---- installed tilt and standoff -----------------------------------
        # a cassette hangs on two hooks; the bracket adjustment is +-3 mm over
        # 150 mm of slot, so a panel out by half a turn on one hook is 0.1 deg
        # out of plane.  At 1.2 m that opens the joint 2.4 mm at one end.
        # ...and the lever arm is the PANEL, not the slot: two hooks 0.9 m
        # apart, one of them 3.5 mm out, is 0.22 deg -- and a facade set out by
        # eye off a laser line is routinely that. It is also the manifest's
        # third variation axis doing its actual work, because a tilted cassette
        # opens its joint into a WEDGE, 2.5 mm at one end and 7 mm at the
        # other, and a wedge-shaped shadow gap is the single clearest way a
        # camera can tell that 180 panels were hung by hand.
        p.tilt_u = math.radians(rnd(-0.220, 0.220, seed, p.idx, 71))
        p.tilt_v = math.radians(rnd(-0.190, 0.190, seed, p.idx, 72))
        p.off_n = rnd(-0.0018, 0.0018, seed, p.idx, 73)
        if p.kind == KIND_REVEAL:
            p.off_n -= REVEAL_DEPTH
        p.reveal = (p.kind == KIND_REVEAL)

        # ---- oil-canning severity ------------------------------------------
        # a lognormal-ish draw: most panels are quiet, a few are bad.  A 3 mm
        # sheet at 1.1 m span with bonded stiffeners runs 0.4-4.5 mm; the tail
        # is what a facade is remembered for.
        u = h01(seed, p.idx, 811)
        base = 0.0006 + 0.0050 * (u ** 1.95)
        # short panels are much stiffer -- the cut course barely cans at all
        stiffk = min(1.0, (min(p.face_w, p.face_h) / 1.05) ** 1.6)
        p.sev = base * (0.25 + 0.75 * stiffk)
        if p.kind in (KIND_CORNER, KIND_LOUVRE):
            p.sev *= 0.45                    # a folded corner is a stiff section

        # ---- stiffeners -----------------------------------------------------
        nst = max(1, int(math.ceil(p.face_h / STIFF_PITCH_MAX)) - 1)
        if p.face_h < 0.55:
            nst = 1
        p.stiff = [(-p.face_h * 0.5 + p.face_h * (k + 1) / (nst + 1))
                   for k in range(nst)]

        # ---- face fixings ---------------------------------------------------
        # cassettes hook on; the ones that CANNOT (closers, corners, the panels
        # either side of a reveal, the replacements) are face-fixed with domed
        # rivets, and that is a real and visible difference between panels.
        p.rivets = p.kind in (KIND_CLOSER, KIND_CORNER, KIND_REPL,
                              KIND_ACCESS, KIND_REVEAL)

        # ---- damage ---------------------------------------------------------
        # dents are not sprinkled: they cluster where a facade gets hit -- the
        # bottom course (mast climber, ladders, deliveries) and the corner.
        pd = 0.10 + 0.34 * (1.0 if p.course == 3 else 0.0) \
            + (0.22 if p.elev == "C" else 0.0)
        nd = 0
        if chance(pd, seed, p.idx, 901):
            nd = 1 + (1 if chance(0.28, seed, p.idx, 902) else 0)
        dents = []
        for k in range(nd):
            edge = chance(0.45, seed, p.idx, k, 903)
            dents.append(dict(
                pu=rnd(0.06, 0.94, seed, p.idx, k, 911),
                pv=(rnd(0.02, 0.14, seed, p.idx, k, 912) if edge
                    else rnd(0.18, 0.82, seed, p.idx, k, 912)),
                r=rnd(0.016, 0.052, seed, p.idx, k, 913),
                # 0.9-3.4 mm, was 0.25-2.2.  A 0.25 mm dent over a 30 mm radius
                # is a 0.5 deg slope and 0.26 px of relief -- it cannot be seen,
                # while its craze mask was fully visible, so the shallow end of
                # this range was producing colour with no geometry under it.
                # The floor is now the depth at which a dent throws a shadow:
                # rim 0.38 x 0.9 mm = 0.34 mm x the EAST ratio 1.652 = 0.57 mm;
                # at the deep end 3.4 mm x 0.38 x 1.652 = 2.1 mm = 2.2 px, which
                # is the value pair the eye actually reads.
                d=rnd(0.00090, 0.00340, seed, p.idx, k, 914),
                ar=rnd(0.5, 2.0, seed, p.idx, k, 915),
                ang=rnd(0.0, math.pi, seed, p.idx, k, 916)))
        p.dents = dents
        p.sign = (p.elev == SIGN_ZONE["elev"] and p.course == 1
                  and p.s1 > SIGN_ZONE["s0"] + CLAD_Y_S - CLAD_Y_S
                  and p.s0 < SIGN_ZONE["s1"] - CLAD_Y_S + CLAD_Y_S)
        # sign zone in the east run's own s coordinate
        zs0 = SIGN_ZONE["s0"] - CLAD_Y_S
        zs1 = SIGN_ZONE["s1"] - CLAD_Y_S
        p.sign = (p.elev == "E" and p.course == 1
                  and p.s1 > zs0 and p.s0 < zs1)
        p.aperture = None
        if p.kind == KIND_LOUVRE:
            p.aperture = (0.10, 0.10)         # inset from the face edges
        p.note = ""


def panel_at(elev, course, col, ps=None):
    ps = ps if ps is not None else panels()
    for p in ps:
        if p.elev == elev and p.course == course and p.col == col:
            return p
    return None


# =============================================================================
# 5.  ELEVATION FRAMES  --  local (u across, v up, n outward) -> world
# =============================================================================
def elev_axes(elev):
    """-> (u_hat, v_hat, n_hat) as world unit vectors.  Right-handed: u x v = n."""
    if elev == "E":
        return ((0.0, 1.0, 0.0), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0))
    if elev == "S":
        # u = v x n = (+z) x (-y) = +x.  The SOUTH run's station s is measured
        # along -x from the corner (face_point), so a south panel's own +u runs
        # back TOWARDS the corner.  That is deliberate: the two elevations are
        # set out from the same corner and their panels are handed, which is
        # what a mirrored set-out actually produces.
        return ((1.0, 0.0, 0.0), (0.0, 0.0, 1.0), (0.0, -1.0, 0.0))
    # corner cassette: authored in the EAST frame; its path bends into the south
    return ((0.0, 1.0, 0.0), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0))


def face_plane(elev):
    """-> (point_on_plane, outward_normal), world."""
    if elev == "E":
        return ((CLAD_X_E, 0.0, 0.0), (1.0, 0.0, 0.0))
    return ((0.0, CLAD_Y_S, 0.0), (0.0, -1.0, 0.0))


def face_point(elev, s, z):
    """World XYZ of a point on the nominal face plane, `s` along the run."""
    if elev == "E":
        return (CLAD_X_E, CLAD_Y_S + s, z)
    return (CLAD_X_E - s, CLAD_Y_S, z)


def _corner_axes_check():
    for e in ("E", "S"):
        u, v, n = elev_axes(e)
        c = np.cross(u, v)
        assert np.allclose(c, n), (e, c, n)


_corner_axes_check()


# =============================================================================
# 6.  THE PLAN PATH  --  one builder serves flat panels and the corner cassette
# =============================================================================
def plan_path(P, npts=None):
    """The face's plan polyline in the panel's LOCAL (X, Z) plane.

    Returns (pp, X, Z, TX, TZ, NX, NZ):
        pp   arc length along the path, 0 .. PL
        X,Z  plan position, LOCAL frame (X across, Z outward)
        T    unit tangent, N unit outward normal (N = rot90ccw(T))

    A flat panel is a straight line along +X with N = +Z.  The corner cassette
    is an L with a CORNER_FILLET_M external radius, and the whole rest of this
    module -- the graded grid, the skirt, the oil-canning, the stiffeners --
    works on it without a special case.
    """
    if P.kind != KIND_CORNER:
        pl = P.face_w
        return dict(PL=pl, kind="flat")
    # local frame is the EAST frame: local X = world +y, local Z = world +x.
    # the south leg lies at local X = 0 running in local -Z, the east leg at
    # local Z = 0 running in local +X, meeting at the local origin.
    ls = CORNER_LEG_S - JOINT_M * 0.5        # south leg face length
    le = CORNER_LEG_E - JOINT_M * 0.5        # east leg face length
    return dict(PL=None, kind="corner", ls=ls, le=le, r=CORNER_FILLET_M)


def path_eval(P, pp):
    """Evaluate the plan path at arc-length coordinates `pp` (array).

    -> (X, Z, TX, TZ, NX, NZ), all arrays, LOCAL frame.
    """
    if P.kind != KIND_CORNER:
        X = pp - P.face_w * 0.5
        Z = np.zeros_like(pp)
        TX = np.ones_like(pp)
        TZ = np.zeros_like(pp)
        return X, Z, TX, TZ, -TZ, TX          # N = rot90ccw(T) = (-TZ, TX)
    d = plan_path(P)
    r = d["r"]
    ls, le = d["ls"], d["le"]
    # segment 1: south leg, from (0, -ls) to (0, -r), direction +Z
    # fillet:    quarter arc, centre (r, -r), from angle 180 deg to 90 deg
    # segment 2: east leg, from (r, 0) to (le, 0), direction +X
    l1 = ls - r
    la = 0.5 * math.pi * r
    l2 = le - r
    total = l1 + la + l2
    off = pp - total * 0.5 + total * 0.5      # keep pp as given (0..total)
    X = np.empty_like(pp)
    Z = np.empty_like(pp)
    TX = np.empty_like(pp)
    TZ = np.empty_like(pp)
    m1 = off <= l1
    X[m1] = 0.0
    Z[m1] = -ls + off[m1]
    TX[m1] = 0.0
    TZ[m1] = 1.0
    m2 = (off > l1) & (off <= l1 + la)
    t = (off[m2] - l1) / max(la, 1e-12) * (0.5 * math.pi)
    # centre (r, -r); start point (0, -r) at t=0, end (r, 0) at t=pi/2
    X[m2] = r - r * np.cos(t)
    Z[m2] = -r + r * np.sin(t)
    TX[m2] = np.sin(t)
    TZ[m2] = np.cos(t)
    m3 = off > l1 + la
    X[m3] = r + (off[m3] - l1 - la)
    Z[m3] = 0.0
    TX[m3] = 1.0
    TZ[m3] = 0.0
    # recentre the whole path on its own bounding box so the mesh is centred
    return X, Z, TX, TZ, -TZ, TX


def path_length(P):
    if P.kind != KIND_CORNER:
        return P.face_w
    d = plan_path(P)
    r = d["r"]
    return (d["ls"] - r) + 0.5 * math.pi * r + (d["le"] - r)


def path_segments(P):
    """Sub-spans of the path that buckle independently (a fold stiffens)."""
    if P.kind != KIND_CORNER:
        return [(0.0, path_length(P))]
    d = plan_path(P)
    r = d["r"]
    l1 = d["ls"] - r
    la = 0.5 * math.pi * r
    l2 = d["le"] - r
    return [(0.0, l1), (l1 + la, l1 + la + l2)]


# =============================================================================
# 7.  MESH GRADING
# =============================================================================
def graded_axis(length, cell_edge, cell_mid, band, features=()):
    """Positions along [0, length], fine at both ends and at named features.

    A uniform grid at the fine cell would cost 25x for nothing: the middle of a
    cassette is a smooth buckling mode with a 300-600 mm wavelength and 18 mm
    resolves it to a quarter of a pixel.  The perimeter is where the curvature
    and the eye both are.
    """
    if length <= cell_edge * 2.5:
        n = max(2, int(round(length / cell_edge)))
        return np.linspace(0.0, length, n + 1)

    def cell(x):
        d = min(x, length - x)
        c = cell_edge + (cell_mid - cell_edge) * float(sstep(d / max(band, 1e-9)))
        for (fc, fh, fcell) in features:
            w = 1.0 - float(sstep((abs(x - fc) - fh) / max(fh, 1e-9)))
            if w > 0.0:
                c = c * (1.0 - w) + min(c, fcell) * w
        return max(c, 0.0008)

    xs = [0.0]
    guard = 0
    while xs[-1] < length - 1e-9 and guard < 20000:
        xs.append(min(length, xs[-1] + cell(xs[-1])))
        guard += 1
    xs = np.asarray(xs)
    if len(xs) > 3 and (xs[-1] - xs[-2]) < 0.35 * (xs[-2] - xs[-3]):
        xs = np.delete(xs, -2)
    xs = xs / xs[-1] * length
    return xs


# =============================================================================
# 8.  THE FOLD PROFILE
# =============================================================================
def edge_profile(P, edge, q):
    """(lat, nrm) arrays, length N_PROFILE+1, for one of the four edges.

    lat  outward from the face's fold-tangent line, metres (can go negative on
         the lip, which folds back INSIDE the panel).
    nrm  along -outward, i.e. how far back into the cavity the sheet has gone.

    edge: 0 = +u (path end), 1 = +v (top), 2 = -u (path start), 3 = -v (bottom)

    All four edges carry the SAME number of rings so the corner patches can
    blend one profile into the next; what differs is the LENGTH of each part.
    The bottom edge of a bottom-course panel gets a 45 mm return on a 5 mm
    arris, which is what a drip actually is; the edges beside a rainwater slot
    get 100 mm so the slot has a cheek.
    """
    r1 = P.fold_r
    d = P.ret_d
    r2 = LIP_R2
    lp = LIP_L
    if edge == 3 and P.course == len(COURSE_H) - 1:
        d = DRIP_RETURN_D
        r2 = DRIP_R2
        lp = 0.014
    if P.note == "reveal_cheek" and edge in (0, 2):
        d = REVEAL_RETURN_D
    lat = [0.0]
    nrm = [0.0]
    na, nd, nb, nl = q["N_ARC1"], q["N_RET"], q["N_ARC2"], q["N_LIP"]
    for i in range(1, na + 1):
        th = 0.5 * math.pi * i / na
        lat.append(r1 * math.sin(th))
        nrm.append(-r1 * (1.0 - math.cos(th)))
    for i in range(1, nd + 1):
        lat.append(r1)
        nrm.append(-r1 - d * i / nd)
    for i in range(1, nb + 1):
        ph = 0.5 * math.pi * i / nb
        lat.append(r1 - r2 * (1.0 - math.cos(ph)))
        nrm.append(-r1 - d - r2 * math.sin(ph))
    for i in range(1, nl + 1):
        lat.append(r1 - r2 - lp * i / nl)
        nrm.append(-r1 - d - r2)
    return np.asarray(lat), np.asarray(nrm)


# =============================================================================
# 9.  OIL-CANNING, DENTS, AND EVERYTHING ELSE THE FACE DOES
# =============================================================================
def face_disp(P, pp, vv, q):
    """Out-of-plane displacement of the panel face, metres, positive = proud.

    THE PHYSICS, not a noise.  A restrained flat plate with residual stress
    buckles into its own low-order modes; which modes and how hard depends on
    the coil it was cut from, where the stiffeners are bonded, how hot it was
    when it went up, and whether some idiot over-tightened a bracket.  So this
    is a modal sum with per-panel amplitudes, plus the stiffener banding, plus
    the coil set, plus the local dimple every face fixing pulls in -- and the
    corner cassette's two legs buckle SEPARATELY because the fold between them
    is a stiff section.
    """
    pl = path_length(P)
    d = np.zeros(np.broadcast(pp, vv).shape)
    H = P.face_h
    sd = P.seed

    for si, (a, b) in enumerate(path_segments(P)):
        L = b - a
        if L < 0.08:
            continue
        t = np.clip((pp - a) / L, 0.0, 1.0)
        w = np.clip((vv + H * 0.5) / H, 0.0, 1.0)
        inside = ((pp >= a - 1e-9) & (pp <= b + 1e-9)).astype(float)
        # aspect ratio decides which modes want to grow
        ar = L / max(H, 1e-6)
        for m in (1, 2, 3):
            for nn in (1, 2, 3):
                k = (m - 1) * 3 + (nn - 1)
                amp = P.sev * (1.0 / (m * nn) ** 1.35)
                amp *= (0.35 + 1.30 * h01(sd, si, k, 3301))
                if m > 1 and ar < 0.8:
                    amp *= 0.5
                if nn > 1 and ar > 1.3:
                    amp *= 0.6
                sgn = 1.0 if h01(sd, si, k, 3307) > 0.5 else -1.0
                d = d + inside * sgn * amp * (np.sin(m * math.pi * t)
                                              * np.sin(nn * math.pi * w))
        # COIL SET: the sheet remembers the roll.  A single cylindrical arc
        # along the rolling direction, which the fixings cannot pull flat.
        cs = P.sev * 0.55 * (0.2 + 1.4 * h01(sd, si, 3313))
        if P.grain == 0:
            d = d + inside * cs * np.sin(math.pi * t) * (0.55 + 0.45 * np.sin(math.pi * w))
        else:
            d = d + inside * cs * np.sin(math.pi * w) * (0.55 + 0.45 * np.sin(math.pi * t))

    # STIFFENER BANDING: the panel is bonded on lines and bows between them.
    if P.stiff:
        pitch = H / (len(P.stiff) + 1)
        band = np.cos(2.0 * math.pi * (vv + H * 0.5) / max(pitch, 1e-6))
        d = d + P.sev * 0.34 * band * np.sin(math.pi * np.clip(pp / pl, 0, 1))

    # THE FACE FIXINGS PULL DIMPLES.  A rivet at 300 mm centres draws the sheet
    # in 0.2-0.7 mm over about 60 mm, and the ring of that dimple is the reason
    # a face-fixed panel reads differently from a hooked one at any distance.
    if P.rivets:
        for (rp, rv) in rivet_points(P, q):
            r = np.hypot(pp - rp, vv - rv)
            d = d - 0.00045 * np.exp(-(r / 0.055) ** 2)

    # DENTS.  A dent is not a dip: the displaced metal has to go somewhere, so
    # there is a raised rim round it.  At 12.5 deg that rim is what you see.
    for k, dn in enumerate(P.dents):
        cu = dn["pu"] * pl
        cv = (dn["pv"] - 0.5) * H
        ca, sa = math.cos(dn["ang"]), math.sin(dn["ang"])
        dx = (pp - cu) * ca + (vv - cv) * sa
        dy = (-(pp - cu) * sa + (vv - cv) * ca) * dn["ar"]
        r = np.hypot(dx, dy) / max(dn["r"], 1e-6)
        d = d - dn["d"] * np.exp(-(r * 1.35) ** 2)
        # THE RIM IS WHAT YOU ACTUALLY SEE, so it is 0.38 of the depth and it is
        # NARROWER than the dip that made it.  The displaced metal has to go
        # somewhere and it piles up in a tight ring, not a broad swell: at a
        # 12.5 deg sun a 1.3 mm rim throws 5.9 mm = 6.1 px of shadow on its lee
        # side and catches the sun on its sunward side, which is the 2-4 px
        # VALUE PAIR that makes relief read at all.  A broad swell throws
        # nothing and is why the dents were invisible next to their own craze.
        d = d + dn["d"] * 0.38 * np.exp(-((r - 1.10) * 3.1) ** 2)

    # the general unflatness of a rolled sheet, below the modal scale
    d = d + 0.00016 * (fbm2(pp * 3.1 + P.seed % 97, vv * 3.1, 5501, oct=3) - 0.5) * 2.0

    # ------------------------------------------------------------------
    # THE ROLL-FORMING RIPPLE IS NOT IN THIS FUNCTION, and that is the result
    # of a controlled experiment rather than a preference.  A coil of 3 mm
    # aluminium keeps a 44-96 mm transverse ripple of 0.03-0.11 mm from the
    # work rolls' own crown; it is why you can stand at the end of any
    # metal-clad building and watch the light run in bands along it, and it was
    # built here, as mesh, first.
    #
    # It came back as CORDUROY.  A 2D FFT of the rendered face found a hard
    # 28.8 px line -- half the 55 mm ripple pitch, because a near-specular
    # surface crosses the mirror condition TWICE per sine.  Halving the
    # amplitude and adding a wandering wavenumber softened it without removing
    # it, and a control render with the amplitude set to zero (SFP_RIPPLE_MESH=0,
    # same seed, same camera, same 1024 samples) came back with the rows gone
    # and nothing else changed.  The rows were the ripple.  Here is why:
    #
    #   ripple amplitude   0.03-0.11 mm  =  0.03-0.11 SCREEN PIXELS
    #   face cell          9.0 mm        =  9.3 screen pixels
    #   ripple pitch       44-96 mm      =  5 to 10 cells per wave
    #
    # A displacement two orders of magnitude below the pixel cannot occlude
    # anything, cannot break a silhouette and cannot shadow itself.  Its whole
    # effect is on the NORMAL -- and a normal rebuilt from a sine sampled five
    # times a wave is a staircase, so what got drawn was the mesh period.
    # Sub-pixel displacement on a specular surface belongs in the shader, where
    # the normal is the derivative of a continuous field instead of a difference
    # of vertex positions.  It is now a Wave-driven bump in mat_anodised() with
    # the same pitch, the same wander and the same per-panel phase, and the MILL
    # SCORE LINES went with it for the same reason (0.2-0.5 mm wide, 15-40
    # microns deep -- a third of a pixel in both directions).
    #
    # What is left in this function is every feature that is at least 0.16 mm
    # deep over at most 600 mm: three or more cells per feature AND a sixth of a
    # pixel or more of actual relief.  That is the line where mesh starts paying
    # for itself, and it is worth writing down because it is not obvious and it
    # cost two iterations to find.
    if RIPPLE_MESH_AMP:            # kept non-zero only to repeat the control
        axis = vv if P.grain == 0 else pp
        long = pp if P.grain == 0 else vv
        lam1 = 0.044 + 0.052 * h01(sd, 9101)
        a1 = (0.000025 + 0.000085 * h01(sd, 9103)) * RIPPLE_MESH_AMP
        free = np.clip(np.minimum(pp, pl - pp) / 0.060, 0.0, 1.0) \
            * np.clip((H * 0.5 - np.abs(vv)) / 0.060, 0.0, 1.0)
        breathe = 0.42 + 0.58 * fbm2(long * 2.2 + P.seed % 89, axis * 0.7,
                                     9107, oct=2)
        d = d + free * breathe * a1 * np.sin(2.0 * math.pi * axis / lam1)
    return d


def rivet_points(P, q):
    """(p, v) of every face rivet, in path/height coordinates."""
    if not P.rivets:
        return []
    pl = path_length(P)
    H = P.face_h
    out = []
    inset = P.fold_r + 0.013
    n = max(2, int(round((H - 2 * inset) / RIVET_PITCH)) + 1)
    vs = np.linspace(-H * 0.5 + inset, H * 0.5 - inset, n)
    cols = [inset, pl - inset]
    if P.kind == KIND_CORNER:
        d = plan_path(P)
        cols = [inset, (d["ls"] - d["r"]) - 0.03,
                (d["ls"] - d["r"]) + 0.5 * math.pi * d["r"] + 0.03, pl - inset]
    for ci, cp in enumerate(cols):
        for vi, v in enumerate(vs):
            jitter = rnd(-0.004, 0.004, P.seed, ci, vi, 771)
            out.append((float(np.clip(cp, 0.02, pl - 0.02)), float(v + jitter)))
    return out


# =============================================================================
# 10.  THE CASSETTE MESH
# =============================================================================
class MeshAcc(object):
    """Vertex / face accumulator with per-vertex scalar fields."""

    FIELDS = ("fold", "edg", "pp", "vv", "lat", "thin")

    def __init__(self):
        self.V = []
        self.F = {k: [] for k in self.FIELDS}
        self.quads = []
        self.tris = []
        self.mq = []
        self.mt = []
        self.n = 0

    def add_block(self, V, fold, edg, pp, vv, lat, thin=0.0):
        i0 = self.n
        self.V.append(np.asarray(V, np.float64).reshape(-1, 3))
        m = self.V[-1].shape[0]
        for k, a in (("fold", fold), ("edg", edg), ("pp", pp),
                     ("vv", vv), ("lat", lat), ("thin", thin)):
            self.F[k].append(np.broadcast_to(np.asarray(a, np.float64).ravel(),
                                             (m,)).copy())
        self.n += m
        return i0

    def quad(self, Q, mat=0):
        Q = np.asarray(Q, np.int64).reshape(-1, 4)
        if Q.size:
            self.quads.append(Q)
            self.mq.append(np.full(Q.shape[0], mat, np.int32))

    def tri(self, T, mat=0):
        T = np.asarray(T, np.int64).reshape(-1, 3)
        if T.size:
            self.tris.append(T)
            self.mt.append(np.full(T.shape[0], mat, np.int32))

    def finish(self):
        V = np.concatenate(self.V) if self.V else np.zeros((0, 3))
        F = {k: (np.concatenate(v) if v else np.zeros(0)) for k, v in self.F.items()}
        Q = np.concatenate(self.quads) if self.quads else np.zeros((0, 4), np.int64)
        T = np.concatenate(self.tris) if self.tris else np.zeros((0, 3), np.int64)
        MQ = np.concatenate(self.mq) if self.mq else np.zeros(0, np.int32)
        MT = np.concatenate(self.mt) if self.mt else np.zeros(0, np.int32)
        return V, F, Q, T, MQ, MT


def _grid_quads(idx):
    """idx: (Na, Nb) index array -> quads with normal = d/da x d/db."""
    return np.stack([idx[:-1, :-1], idx[1:, :-1], idx[1:, 1:], idx[:-1, 1:]],
                    -1).reshape(-1, 4)


def cassette_mesh(P, q):
    """Build one cassette.  -> (V, fields, quads, tris, matq, matt)."""
    acc = MeshAcc()
    pl = path_length(P)
    H = P.face_h
    r1 = P.fold_r

    # ---- 1. the graded face grid -------------------------------------------
    feats_p = []
    feats_v = []
    # A DENT'S FINEST FEATURE IS ITS RIM, NOT ITS DIP.  The rim Gaussian in
    # face_disp has sigma = r / 3.1, so at r = 30 mm it is a 9.7 mm ridge -- and
    # a 9 mm cell (the old min(CELL_MID, r*0.42) bound) puts ONE cell across it,
    # which cannot carry a ridge.  r * 0.12 gives ~3.6 mm cells at r = 30 mm,
    # about 2.7 cells per sigma, which is what makes the lit lip and the lee
    # shadow separate features instead of one smeared band.  Also widen the
    # graded BAND to 1.7 r so the whole rim sits inside the fine zone.
    for dn in P.dents:
        cell = min(q["CELL_EDGE"], dn["r"] * 0.12)
        feats_p.append((dn["pu"] * pl, dn["r"] * 1.7, cell))
        feats_v.append(((dn["pv"] - 0.5) * H + H * 0.5, dn["r"] * 1.7, cell))
    for (rp, rv) in rivet_points(P, q):
        feats_p.append((rp, 0.020, 0.006))
        feats_v.append((rv + H * 0.5, 0.020, 0.006))
    if P.kind == KIND_CORNER:
        d = plan_path(P)
        feats_p.append((d["ls"] - d["r"] + 0.25 * math.pi * d["r"], 0.05, 0.005))

    p_lo, p_hi = r1, pl - r1
    v_lo, v_hi = -H * 0.5 + r1, H * 0.5 - r1
    gp = graded_axis(p_hi - p_lo, q["CELL_EDGE"], q["CELL_MID"], q["GRADE_BAND"],
                     [(f[0] - p_lo, f[1], f[2]) for f in feats_p]) + p_lo
    gv = graded_axis(v_hi - v_lo, q["CELL_EDGE"], q["CELL_MID"], q["GRADE_BAND"],
                     [(f[0] - r1, f[1], f[2]) for f in feats_v]) + v_lo
    Np, Nv = len(gp), len(gv)
    PP, VV = np.meshgrid(gp, gv, indexing="ij")

    X, Z, TX, TZ, NX, NZ = path_eval(P, PP.ravel())
    X = X.reshape(Np, Nv)
    Z = Z.reshape(Np, Nv)
    NX = NX.reshape(Np, Nv)
    NZ = NZ.reshape(Np, Nv)
    TXr = TX.reshape(Np, Nv)
    TZr = TZ.reshape(Np, Nv)

    D = face_disp(P, PP, VV, q)
    FX = X + NX * D
    FZ = Z + NZ * D
    face_V = np.stack([FX.ravel(), VV.ravel(), FZ.ravel()], -1)

    dp = np.minimum(PP - p_lo, p_hi - PP)
    dv = np.minimum(VV - v_lo, v_hi - VV)
    edg = np.clip(np.minimum(dp, dv) / 0.150, 0.0, 1.0)
    i_face = acc.add_block(face_V, 0.0, edg.ravel(), PP.ravel(), VV.ravel(), 0.0)
    G = i_face + np.arange(Np * Nv).reshape(Np, Nv)

    # louvre aperture: drop the face quads inside it, keep the boundary ring
    ap_i0 = ap_i1 = ap_j0 = ap_j1 = None
    if P.aperture is not None:
        mx, my = P.aperture
        ap_i0 = int(np.searchsorted(gp, p_lo + mx))
        ap_i1 = int(np.searchsorted(gp, p_hi - mx))
        ap_j0 = int(np.searchsorted(gv, v_lo + my))
        ap_j1 = int(np.searchsorted(gv, v_hi - my))
        ap_i0 = max(1, ap_i0)
        ap_i1 = min(Np - 2, ap_i1)
        ap_j0 = max(1, ap_j0)
        ap_j1 = min(Nv - 2, ap_j1)
        if ap_i1 - ap_i0 < 3 or ap_j1 - ap_j0 < 3:
            P.aperture = None
            ap_i0 = None

    fq = _grid_quads(G)
    if ap_i0 is not None:
        keep = np.ones((Np - 1, Nv - 1), bool)
        keep[ap_i0:ap_i1, ap_j0:ap_j1] = False
        fq = fq.reshape(Np - 1, Nv - 1, 4)[keep]
    acc.quad(fq, 0)

    # ---- 2. the four skirts -------------------------------------------------
    profs = [edge_profile(P, e, q) for e in range(4)]
    Ns = len(profs[0][0]) - 1
    skirt = {}

    def _skirt(edge):
        lat, nrm = profs[edge]
        if edge in (0, 2):                    # path ends: lateral = +-tangent
            i = Np - 1 if edge == 0 else 0
            sgn = 1.0 if edge == 0 else -1.0
            bx = FX[i, :]
            bz = FZ[i, :]
            bv = VV[i, :]
            tx = TXr[i, :] * sgn
            tz = TZr[i, :] * sgn
            nx = NX[i, :]
            nz = NZ[i, :]
            Vb = np.empty((len(bv), Ns, 3))
            for k in range(1, Ns + 1):
                Vb[:, k - 1, 0] = bx + tx * lat[k] + nx * nrm[k]
                Vb[:, k - 1, 2] = bz + tz * lat[k] + nz * nrm[k]
                Vb[:, k - 1, 1] = bv
            pp_b = np.broadcast_to(PP[i, :][:, None], (len(bv), Ns))
            vv_b = np.broadcast_to(bv[:, None], (len(bv), Ns))
        else:                                  # top / bottom: lateral = +-Y
            j = Nv - 1 if edge == 1 else 0
            sgn = 1.0 if edge == 1 else -1.0
            bx = FX[:, j]
            bz = FZ[:, j]
            bv = VV[:, j]
            nx = NX[:, j]
            nz = NZ[:, j]
            Vb = np.empty((len(bx), Ns, 3))
            for k in range(1, Ns + 1):
                Vb[:, k - 1, 0] = bx + nx * nrm[k]
                Vb[:, k - 1, 2] = bz + nz * nrm[k]
                Vb[:, k - 1, 1] = bv + sgn * lat[k]
            pp_b = np.broadcast_to(PP[:, j][:, None], (len(bx), Ns))
            vv_b = np.broadcast_to(bv[:, None], (len(bx), Ns))
        latb = np.broadcast_to(lat[1:][None, :], Vb.shape[:2])
        foldb = np.clip(np.abs(latb) / max(r1, 1e-6), 0.0, 1.0) * 0.0 + 1.0
        i0 = acc.add_block(Vb.reshape(-1, 3), foldb.ravel(),
                           np.zeros(Vb.shape[0] * Ns), pp_b.ravel(),
                           vv_b.ravel(), latb.ravel())
        return i0 + np.arange(Vb.shape[0] * Ns).reshape(Vb.shape[0], Ns)

    for e in range(4):
        skirt[e] = _skirt(e)

    def ring(edge, station):
        """Full ring index list for one station of one skirt, ring 0 first."""
        if edge == 0:
            base = G[Np - 1, station]
        elif edge == 2:
            base = G[0, station]
        elif edge == 1:
            base = G[station, Nv - 1]
        else:
            base = G[station, 0]
        return np.concatenate([[base], skirt[edge][station]])

    for e in range(4):
        nst = Nv if e in (0, 2) else Np
        cols = np.empty((nst, Ns + 1), np.int64)
        for s in range(nst):
            cols[s] = ring(e, s)
        if e in (0, 1):
            acc.quad(_grid_quads(cols.T if e == 0 else cols), 0)
        else:
            acc.quad(_grid_quads(cols if e == 2 else cols.T), 0)

    # ---- 3. the four face corners ------------------------------------------
    # a spun corner: the edge profile revolved 90 deg about the corner's own
    # axis, blending edge e's profile into edge e+1's as it goes.
    NC = q["N_CORNER"]
    corner_defs = [(0, 1, Np - 1, Nv - 1), (1, 2, 0, Nv - 1),
                   (2, 3, 0, 0), (3, 0, Np - 1, 0)]
    for (ea, eb, ci, cj) in corner_defs:
        la, na_ = profs[ea]
        lb, nb_ = profs[eb]
        base = np.array([FX[ci, cj], VV[ci, cj], FZ[ci, cj]])
        # lateral unit vectors of the two edges, in local 3D
        def latvec(e):
            if e == 0:
                return np.array([TXr[Np - 1, cj], 0.0, TZr[Np - 1, cj]])
            if e == 2:
                return np.array([-TXr[0, cj], 0.0, -TZr[0, cj]])
            if e == 1:
                return np.array([0.0, 1.0, 0.0])
            return np.array([0.0, -1.0, 0.0])
        La = latvec(ea)
        Lb = latvec(eb)
        nvec = np.array([NX[ci, cj], 0.0, NZ[ci, cj]])
        psi = np.linspace(0.0, 0.5 * math.pi, NC + 1)
        wpsi = psi / (0.5 * math.pi)
        cols = np.empty((Ns + 1, NC + 1), np.int64)
        cols[0, :] = G[ci, cj]
        Vb = np.empty((Ns, NC - 1, 3))
        for k in range(1, Ns + 1):
            latk = la[k] * (1 - wpsi) + lb[k] * wpsi
            nrmk = na_[k] * (1 - wpsi) + nb_[k] * wpsi
            dirs = (np.cos(psi)[:, None] * La[None, :]
                    + np.sin(psi)[:, None] * Lb[None, :])
            pts = base[None, :] + dirs * latk[:, None] + nvec[None, :] * nrmk[:, None]
            Vb[k - 1] = pts[1:-1]
        i0 = acc.add_block(Vb.reshape(-1, 3), 1.0, np.zeros(Ns * (NC - 1)),
                           float(PP[ci, cj]), float(VV[ci, cj]),
                           np.repeat(la[1:], NC - 1))
        inner = i0 + np.arange(Ns * (NC - 1)).reshape(Ns, NC - 1)
        for k in range(1, Ns + 1):
            cols[k, 0] = skirt[ea][cj if ea in (0, 2) else ci, k - 1]
            cols[k, NC] = skirt[eb][cj if eb in (0, 2) else ci, k - 1]
            cols[k, 1:NC] = inner[k - 1]
        acc.quad(_grid_quads(cols[1:]), 0)
        acc.tri(np.stack([np.full(NC, cols[0, 0]), cols[1, :-1], cols[1, 1:]], -1), 0)

    # ---- 4. stiffeners on the back -----------------------------------------
    if P.aperture is None:
        _stiffeners(acc, P, q, gp, pl)

    # ---- 5. rivets ----------------------------------------------------------
    for (rp, rv) in rivet_points(P, q):
        _rivet(acc, P, q, rp, rv)

    # ---- 6. louvre aperture: return, blades, plenum -------------------------
    if P.aperture is not None and ap_i0 is not None:
        _louvre(acc, P, q, G, FX, FZ, VV, NX, NZ, gp, gv,
                ap_i0, ap_i1, ap_j0, ap_j1)

    # ---- 7. access-panel cam locks and gasket -------------------------------
    if P.kind == KIND_ACCESS:
        _camlocks(acc, P, q, pl)

    # ---- 8. sign backing plates --------------------------------------------
    if P.sign:
        _sign_plate(acc, P, q, pl)

    return acc.finish()


def _stiffeners(acc, P, q, gp, pl):
    """Bonded aluminium top-hat stiffeners on the back of the sheet."""
    # cross-section in (v, n) offsets from the stiffener centreline, on the back
    hw = STIFF_W * 0.5
    cw = STIFF_CROWN * 0.5
    dpt = STIFF_D
    rr = 0.0030
    sec = [(-hw, 0.0)]
    for i in range(1, 4):
        t = 0.5 * math.pi * i / 3
        sec.append((-cw - rr + rr * math.sin(t), -rr * (1 - math.cos(t))))
    sec.append((-cw, -dpt + rr))
    for i in range(1, 4):
        t = 0.5 * math.pi * i / 3
        sec.append((-cw + rr * (1 - math.cos(t)), -dpt + rr * (1 - math.sin(t))))
    sec.append((cw - rr, -dpt))
    for i in range(1, 4):
        t = 0.5 * math.pi * i / 3
        sec.append((cw - rr + rr * math.sin(t), -dpt + rr * (1 - math.cos(t))))
    sec.append((cw + rr, -rr))
    for i in range(1, 4):
        t = 0.5 * math.pi * i / 3
        sec.append((cw + rr * (1 - math.cos(t)) + rr * 0.0, -rr * (1 - math.sin(t))))
    sec.append((hw, 0.0))
    sec = np.asarray(sec)

    step = max(2, int(round(len(gp) / 46)))
    for si, (a, b) in enumerate(path_segments(P)):
        pa, pb = a + 0.035, b - 0.035
        if pb - pa < 0.12:
            continue
        sel = gp[(gp >= pa) & (gp <= pb)][::step]
        if len(sel) < 3:
            sel = np.linspace(pa, pb, 6)
        for ki, vs in enumerate(P.stiff):
            PPs, SEC = np.meshgrid(sel, np.arange(len(sec)), indexing="ij")
            vv = vs + sec[:, 0][None, :]
            nn = sec[:, 1][None, :] - SHEET_T - STIFF_T_FACTOR * SHEET_T
            D = face_disp(P, PPs, np.clip(vv, -P.face_h * 0.5, P.face_h * 0.5), q)
            X, Z, TX, TZ, NX, NZ = path_eval(P, PPs.ravel())
            X = X.reshape(PPs.shape)
            Z = Z.reshape(PPs.shape)
            NX = NX.reshape(PPs.shape)
            NZ = NZ.reshape(PPs.shape)
            Vb = np.stack([(X + NX * (D + nn)).ravel(),
                           np.broadcast_to(vv, PPs.shape).ravel(),
                           (Z + NZ * (D + nn)).ravel()], -1)
            i0 = acc.add_block(Vb, 1.0, np.zeros(Vb.shape[0]), PPs.ravel(),
                               np.broadcast_to(vv, PPs.shape).ravel(), 0.0,
                               thin=1.0)
            idx = i0 + np.arange(Vb.shape[0]).reshape(PPs.shape)
            acc.quad(_grid_quads(idx)[:, ::-1], 2)


def _disc(acc, P, q, cp, cv, rings, hs, nsec, mat, thin=0.0):
    """A dome or a dish sitting on the face: an APEX plus concentric rings.

    The first version used a ring of coincident vertices at r = 0 instead of an
    apex, and 14 verts on top of each other have no normal -- which is what made
    Solidify's even-offset send a 1.1 m cassette 58 m across the world.  A cap
    has one point at the middle, like a cap does.
    """
    pl = path_length(P)
    H = P.face_h

    def place(pu, pv, hgt):
        pu = np.clip(pu, 0.0, pl)
        pv = np.clip(pv, -H * 0.5, H * 0.5)
        d = face_disp(P, pu, pv, q)
        X, Z, _tx, _tz, NX, NZ = path_eval(P, pu)
        return np.stack([X + NX * (d + hgt), pv, Z + NZ * (d + hgt)], -1)

    th = np.linspace(0, 2 * math.pi, nsec, endpoint=False)
    apex = place(np.array([cp]), np.array([cv]), hs[0])
    ia = acc.add_block(apex, 0.0, np.ones(1), cp, cv, 0.0, thin=thin)
    pts = []
    for (r, hgt) in zip(rings[1:], hs[1:]):
        pts.append(place(cp + r * np.cos(th), cv + r * np.sin(th), hgt))
    Vb = np.concatenate(pts)
    i0 = acc.add_block(Vb, 0.0, np.ones(Vb.shape[0]), cp, cv, 0.0, thin=thin)
    nr = len(rings) - 1
    idx = i0 + np.arange(nr * nsec).reshape(nr, nsec)
    cyc = np.concatenate([idx, idx[:, :1]], 1)
    acc.tri(np.stack([np.full(nsec, ia), cyc[0, :-1], cyc[0, 1:]], -1), mat)
    if nr > 1:
        acc.quad(_grid_quads(cyc), mat)


def _rivet(acc, P, q, rp, rv):
    """A domed stainless rivet head sitting on the face.  4.8 mm shank, 9.5 mm
    flange, 1.6 mm proud -- 9.8 px across and throwing 7.5 px of shadow."""
    nsec = 14 if q["CELL_EDGE"] < 0.008 else 8
    _disc(acc, P, q, rp, rv,
          [0.0, 0.0016, 0.0031, 0.00425, RIVET_R_FLANGE],
          [RIVET_H, RIVET_H * 0.93, RIVET_H * 0.72, RIVET_H * 0.38, -0.0002],
          nsec, 1)


def _louvre(acc, P, q, G, FX, FZ, VV, NX, NZ, gp, gv, i0, i1, j0, j1):
    """A plant intake louvre: a folded return round the aperture, seven formed
    Z-blades on a weathering rake, and the dark plenum behind them.

    Every facade has one of these and every fake facade does not.  It is also
    the only genuinely different TOPOLOGY on the item, which is what makes the
    four louvre cassettes read as different objects rather than different
    numbers.
    """
    # ---- 1. the folded return round the aperture ---------------------------
    ring = []
    for i in range(i0, i1 + 1):
        ring.append((i, j0))
    for j in range(j0 + 1, j1 + 1):
        ring.append((i1, j))
    for i in range(i1 - 1, i0 - 1, -1):
        ring.append((i, j1))
    for j in range(j1 - 1, j0 - 1, -1):
        ring.append((i0, j))
    ridx = np.array([G[i, j] for (i, j) in ring], np.int64)
    bx = np.array([FX[i, j] for (i, j) in ring])
    bz = np.array([FZ[i, j] for (i, j) in ring])
    bv = np.array([VV[i, j] for (i, j) in ring])
    nx = np.array([NX[i, j] for (i, j) in ring])
    nz = np.array([NZ[i, j] for (i, j) in ring])
    depth = (0.0, -0.0035, -0.0110, -0.0230, -0.0380, -0.0420)
    cols = np.empty((len(depth), len(ring)), np.int64)
    cols[0] = ridx
    for k in range(1, len(depth)):
        Vb = np.stack([bx + nx * depth[k], bv, bz + nz * depth[k]], -1)
        ii = acc.add_block(Vb, 1.0, np.zeros(len(ring)), 0.0, bv, 0.0)
        cols[k] = ii + np.arange(len(ring))
    acc.quad(_grid_quads(cols.T), 0)

    # ---- 2. the blades ------------------------------------------------------
    pa, pb = float(gp[i0]) + 0.006, float(gp[i1]) - 0.006
    va, vb = float(gv[j0]) + 0.010, float(gv[j1]) - 0.010
    ps = np.linspace(pa, pb, max(8, int((pb - pa) / 0.035)))
    prof = ((0.030, -0.048), (0.008, -0.030), (-0.004, -0.020),
            (-0.010, -0.010), (-0.006, -0.002), (0.014, -0.014))
    nb = 7
    Xr, Zr, _tx, _tz, NXr, NZr = path_eval(P, ps)
    for bnum in range(nb):
        vc = va + (vb - va) * (bnum + 0.5) / nb
        Vall = []
        for (dv, dn) in prof:
            Vall.append(np.stack([Xr + NXr * dn,
                                  np.full_like(ps, vc + dv),
                                  Zr + NZr * dn], -1))
        Vb = np.concatenate(Vall)
        ii = acc.add_block(Vb, 1.0, np.zeros(Vb.shape[0]), ps.mean(), vc, 0.0,
                           thin=1.0)
        idx = ii + np.arange(Vb.shape[0]).reshape(len(prof), len(ps))
        acc.quad(_grid_quads(idx.T), 0)

    # ---- 3. the plenum behind, and the bird mesh in front of it ------------
    pm = np.array([pa - 0.004, pb + 0.004])
    Xp, Zp, _a, _b, NXp, NZp = path_eval(P, pm)
    for (dn, mat) in ((-0.075, 4), (-0.050, 1)):
        Vb = np.array([[Xp[0] + NXp[0] * dn, va - 0.004, Zp[0] + NZp[0] * dn],
                       [Xp[1] + NXp[1] * dn, va - 0.004, Zp[1] + NZp[1] * dn],
                       [Xp[1] + NXp[1] * dn, vb + 0.004, Zp[1] + NZp[1] * dn],
                       [Xp[0] + NXp[0] * dn, vb + 0.004, Zp[0] + NZp[0] * dn]])
        ii = acc.add_block(Vb, 1.0, np.zeros(4), pm.mean(), 0.5 * (va + vb), 0.0,
                           thin=1.0)
        acc.quad(np.array([[ii, ii + 1, ii + 2, ii + 3]]), mat)


def _camlocks(acc, P, q, pl):
    """Two recessed cam-lock sockets on an access cassette.  A dish plus a
    barrel, not a hole: at 3.6 m the read is the shadow inside the dish, and
    cutting the tensor grid for a 24 mm circle would buy nothing."""
    nsec = 16 if q["CELL_EDGE"] < 0.008 else 8
    for (fp, fv) in ((0.16, 0.0), (pl - 0.16, 0.0)):
        _disc(acc, P, q, fp, fv,
              [0.0, 0.0035, 0.0060, 0.0105, 0.0120],
              [-0.0058, -0.0056, -0.0052, -0.0040, 0.0006], nsec, 1)


def _sign_plate(acc, P, q, pl):
    """A 4 mm backing plate bonded to the rear of every sign-zone panel, so a
    letter stud pulls up against steel and not against a 3 mm skin."""
    H = P.face_h
    ps = np.linspace(0.10, pl - 0.10, 8)
    vs = np.linspace(-H * 0.5 + 0.10, H * 0.5 - 0.10, 6)
    PPs, VVs = np.meshgrid(ps, vs, indexing="ij")
    D = face_disp(P, PPs, VVs, q)
    X, Z, TX, TZ, NX, NZ = path_eval(P, PPs.ravel())
    X = X.reshape(PPs.shape)
    Z = Z.reshape(PPs.shape)
    NX = NX.reshape(PPs.shape)
    NZ = NZ.reshape(PPs.shape)
    off = -SHEET_T - 0.0005
    Vb = np.stack([(X + NX * (D + off)).ravel(), VVs.ravel(),
                   (Z + NZ * (D + off)).ravel()], -1)
    i0 = acc.add_block(Vb, 1.0, np.zeros(Vb.shape[0]), PPs.ravel(), VVs.ravel(),
                       0.0, thin=1.0)
    idx = i0 + np.arange(Vb.shape[0]).reshape(PPs.shape)
    acc.quad(_grid_quads(idx)[:, ::-1], 2)


# =============================================================================
# 11.  SURFACE-HISTORY ATTRIBUTES
# =============================================================================
ATTRS = ("bat", "rack", "imm", "grn", "gflip", "fold", "edg", "run", "sky",
         "dam", "hand", "wld", "shl", "age", "sd")


def panel_attrs(P, V, F, q):
    """The fifteen fields the anodised material reads, per vertex (== ATTRS)."""
    pl = path_length(P)
    H = P.face_h
    pp = F["pp"]
    vv = F["vv"]
    n = len(pp)
    t = np.clip(pp / max(pl, 1e-9), 0.0, 1.0)
    w = np.clip((vv + H * 0.5) / max(H, 1e-9), 0.0, 1.0)

    a = {}
    a["bat"] = np.full(n, (P.batch + 0.5) / N_BATCHES)
    a["rack"] = np.full(n, P.rack / max(RACK_SIZE - 1.0, 1.0))
    a["grn"] = np.full(n, float(P.grain))
    a["gflip"] = np.full(n, float(P.gflip))
    a["age"] = np.full(n, P.age)
    a["sd"] = np.full(n, (P.seed % 100003) / 100003.0 * 40.0)
    a["fold"] = F["fold"]
    a["edg"] = F["edg"]

    # IMMERSION GRADIENT.  A cassette goes into the anodising tank on a jig,
    # one end first, and the oxide is measurably thicker where it dwelt longer.
    # Which end depends on how it was hung, so it flips with gflip.
    g = t if P.gflip == 0 else (1.0 - t)
    if P.grain == 1:
        g = w if P.gflip == 0 else (1.0 - w)
    a["imm"] = g

    # RAIN.  Three separate things, because on a real facade they are three
    # separate things and lumping them into one gradient is what makes CG dirt
    # look sprayed on:
    #   (a) the RUNDOWN out of the horizontal joint above -- strongest in the
    #       top 150 mm of the panel and combing out into fingers as it falls,
    #   (b) the CONCENTRATION at the vertical joints, where surface tension
    #       pulls the sheet of water sideways into the gap,
    #   (c) the LIP at the panel's own bottom edge, where the water finally
    #       leaves and drops its load.
    # A RUNDOWN IS NOT A STRIPE.  The fifth macro combed every panel from top
    # edge to bottom edge with continuous vertical bands and the whole facade
    # read as sanded timber.  Real tracking is intermittent: a finger starts at
    # a high point on the joint above, wanders, splits, and dies out -- so the
    # field is modulated BOTH ways, and only about a third of any panel's width
    # actually carries a track.
    fingers = fbm2(pp * 9.0 + P.seed % 61, vv * 2.6, 6607, oct=4)
    fingers = 0.06 + 0.94 * np.clip((fingers - 0.40) / 0.34, 0.0, 1.0)
    live = fbm2(pp * 2.3 + P.seed % 53, vv * 0.55, 7717, oct=3)
    fingers = fingers * np.clip((live - 0.32) / 0.30, 0.0, 1.0)
    fingers = fingers * (0.35 + 0.65 * fbm2(pp * 24.0, vv * 3.0, 8821, oct=3))
    top = np.exp(-((1.0 - w) / 0.42) ** 1.25)
    run = 0.90 * fingers * top
    run = run + 0.55 * fingers * np.clip(1.0 - w, 0.0, 1.0) ** 1.6
    run = run + 0.50 * np.exp(-(np.minimum(t, 1 - t) / 0.045) ** 2) * (1.0 - w) ** 0.5
    run = run + 0.60 * np.exp(-(w / 0.05) ** 2)
    if P.course == 0:
        run *= 1.35                      # the top course takes the parapet wash
    for (elev, s_hop, dia) in _rwp_stations():
        if elev != P.elev:
            continue
        ds = abs((P.s0 + P.s1) * 0.5 - s_hop)
        if ds < 1.6:
            run += 0.75 * math.exp(-(ds / 0.75) ** 2) * (1.0 - w * 0.4)
    a["run"] = np.clip(run, 0.0, 1.8) * P.age

    # ATMOSPHERIC SOIL.  Dirt accumulates at the bottom of every panel where
    # the water sheets slowest, and the whole facade is dirtier low down.
    facade_h = (P.z_bot - CLAD_BOTTOM_Z) / max(CLAD_TOP_Z - CLAD_BOTTOM_Z, 1e-9)
    a["sky"] = np.clip((1.0 - w) ** 2.2 * 0.75
                       + (1.0 - facade_h) * 0.35, 0.0, 1.0) * P.age

    # DAMAGE.  The anodising crazes where the metal was worked past its limit,
    # so it whitens at a dent and at a fold that has been knocked.
    dam = np.zeros(n)
    for dn in P.dents:
        cu = dn["pu"] * pl
        cv = (dn["pv"] - 0.5) * H
        ca, sa = math.cos(dn["ang"]), math.sin(dn["ang"])
        dx = (pp - cu) * ca + (vv - cv) * sa
        dy = (-(pp - cu) * sa + (vv - cv) * ca) * dn["ar"]
        r = np.hypot(dx, dy) / max(dn["r"], 1e-6)
        dam = np.maximum(dam, np.exp(-(r * 1.1) ** 2) * min(1.0, dn["d"] / 0.0012))
    a["dam"] = np.clip(dam, 0.0, 1.0)

    # HANDLING.  Vacuum lifter rings and glove smears near the edges.  Every
    # cassette on a facade was picked up by a suction pad, twice.
    hand = np.zeros(n)
    for k in range(2):
        cu = rnd(0.22, 0.78, P.seed, k, 4401) * pl
        cv = (rnd(0.28, 0.72, P.seed, k, 4402) - 0.5) * H
        r = np.hypot(pp - cu, vv - cv)
        hand = np.maximum(hand, np.exp(-((r - 0.098) / 0.011) ** 2) * 0.7)
    hand += 0.22 * np.exp(-(np.clip(np.minimum(np.minimum(pp, pl - pp),
                                               np.minimum(vv + H * 0.5,
                                                          H * 0.5 - vv)), 0, 1)
                            / 0.035) ** 2)
    a["hand"] = np.clip(hand, 0.0, 1.0) * P.age

    # WELD / HEAT-AFFECTED ZONE at the spun corners of the tray and at the
    # corner cassette's own fold: the anodising is always duller there.
    wld = np.zeros(n)
    corner_d = np.minimum(np.minimum(pp, pl - pp),
                          np.minimum(vv + H * 0.5, H * 0.5 - vv))
    wld = np.exp(-(corner_d / 0.030) ** 2) * (0.55 if P.fab == 1 else 0.30)
    if P.kind == KIND_CORNER:
        d = plan_path(P)
        pc = d["ls"] - d["r"] + 0.25 * math.pi * d["r"]
        wld = np.maximum(wld, 0.5 * np.exp(-((pp - pc) / 0.022) ** 2))
    a["wld"] = np.clip(wld, 0.0, 1.0)

    # SHELTERED.  What a coping's drip and a sign's backplate actually do: they
    # keep the rain off, so the dirt washes differently and a pale band appears.
    shl = np.zeros(n)
    if P.course == 0:
        shl = np.maximum(shl, smoothstep(H * 0.5 - 0.150, H * 0.5 - 0.030, vv))
    if P.sign:
        # the sign backplate keeps the rain off a BAND, and its edges are soft
        # because wind-driven rain does not respect a rectangle.  The
        # LETTER-shaped part of this shadow belongs to
        # showroom_signage_lettering; this is only the plate.
        zs0 = SIGN_ZONE["s0"] - CLAD_Y_S
        zs1 = SIGN_ZONE["s1"] - CLAD_Y_S
        s_here = P.s0 + pp
        inz = (smoothstep(zs0 - 0.30, zs0 + 0.10, s_here)
               * (1.0 - smoothstep(zs1 - 0.10, zs1 + 0.30, s_here)))
        band = np.exp(-((vv - 0.02) / 0.42) ** 2)
        shl = np.maximum(shl, inz * band * 0.60)
    a["shl"] = np.clip(shl, 0.0, 1.0)
    return a


def _rwp_stations():
    """(elev, s, dia) of the rainwater downpipes on the two clad elevations."""
    ps = panels()
    out = []
    for (elev, col) in RWP_COLUMNS:
        for p in ps:
            if p.elev == elev and p.col == col and p.course == 0:
                out.append((elev, 0.5 * (p.s0 + p.s1), 0.100))
                break
    return out


def bake_panel_attrs(mesh, **overrides):
    """Write all fifteen attributes (ATTRS) with sane defaults.

    A dependant emitting geometry into `mat_anodised()` without these gets the
    zero case: a raw unstained panel from batch 0.  That is not a crash, but it
    is not right either, so this exists.
    """
    n = len(mesh.vertices)
    defaults = dict(bat=0.5, rack=0.5, imm=0.5, grn=0.0, gflip=0.0, fold=0.0,
                    edg=1.0, run=0.25, sky=0.25, dam=0.0, hand=0.15, wld=0.0,
                    shl=0.0, age=1.0, sd=7.0)
    for name in ATTRS:
        v = overrides.get(name, defaults[name])
        at = mesh.attributes.get(name) or mesh.attributes.new(name, "FLOAT", "POINT")
        at.data.foreach_set("value", np.full(n, float(v), np.float32)
                            if np.isscalar(v) else
                            np.ascontiguousarray(v, np.float32))
    return mesh


# =============================================================================
# 12.  BLENDER PLUMBING
# =============================================================================
def _collection(name, parent=None):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
    par = parent or bpy.context.scene.collection
    if c.name not in par.children:
        try:
            par.children.link(c)
        except RuntimeError:
            pass
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
    for m in list(bpy.data.materials):
        bpy.data.materials.remove(m)
    _MATS.clear()


def make_mesh(name, V, Q, T, MQ, MT, attrs=None, uv=None):
    me = bpy.data.meshes.new(name)
    nv = len(V)
    npq, npt = len(Q), len(T)
    loops = np.concatenate([np.ascontiguousarray(Q, np.int32).ravel(),
                            np.ascontiguousarray(T, np.int32).ravel()])
    starts = np.concatenate([np.arange(npq, dtype=np.int32) * 4,
                             (npq * 4 + np.arange(npt, dtype=np.int32) * 3)])
    me.vertices.add(nv)
    me.vertices.foreach_set("co", np.ascontiguousarray(V, np.float32).ravel())
    me.loops.add(len(loops))
    me.loops.foreach_set("vertex_index", loops)
    me.polygons.add(npq + npt)
    me.polygons.foreach_set("loop_start", starts)
    me.polygons.foreach_set("material_index",
                            np.concatenate([MQ, MT]).astype(np.int32))
    me.update(calc_edges=True)
    me.validate(verbose=False, clean_customdata=False)
    if attrs:
        for k, v in attrs.items():
            at = me.attributes.get(k) or me.attributes.new(k, "FLOAT", "POINT")
            at.data.foreach_set("value", np.ascontiguousarray(v, np.float32))
    if uv is not None and len(me.loops):
        lay = me.uv_layers.new(name="sfp_uv")
        li = np.empty(len(me.loops), np.int32)
        me.loops.foreach_get("vertex_index", li)
        lay.uv.foreach_set("vector",
                           np.ascontiguousarray(uv[li], np.float32).ravel())
    return me


def shade(me, deg=34.0):
    """Smooth everything, mark the genuinely sharp edges sharp.

    A folded cassette is a curved surface: flat-shading the 8 facets of a 9 mm
    fold turns the panel's own arris -- the brightest line on the whole facade
    -- into a stack of 1.8 mm bands.  Done in numpy against `sharp_edge`
    because shade_auto_smooth needs a VIEW_3D context and cannot run headless.
    """
    npoly = len(me.polygons)
    nloop = len(me.loops)
    nedge = len(me.edges)
    if not nedge or not npoly:
        return
    me.polygons.foreach_set("use_smooth", np.ones(npoly, np.int8))
    fn = np.empty(npoly * 3, np.float32)
    me.polygons.foreach_get("normal", fn)
    fn = fn.reshape(npoly, 3)
    ls = np.empty(npoly, np.int32)
    me.polygons.foreach_get("loop_start", ls)
    lt = np.empty(npoly, np.int32)
    me.polygons.foreach_get("loop_total", lt)
    lv = np.empty(nloop, np.int32)
    me.loops.foreach_get("vertex_index", lv)
    nxt = np.arange(nloop, dtype=np.int64) + 1
    ends = (ls + lt - 1).astype(np.int64)
    nxt[ends] = ls.astype(np.int64)
    a = lv.astype(np.int64)
    b = lv[nxt].astype(np.int64)
    nvv = np.int64(len(me.vertices))
    key = np.minimum(a, b) * nvv + np.maximum(a, b)
    face_of_loop = np.repeat(np.arange(npoly, dtype=np.int64), lt)
    order = np.argsort(key, kind="stable")
    ks = key[order]
    fs = face_of_loop[order]
    first = np.concatenate([[True], ks[1:] != ks[:-1]])
    grp = np.cumsum(first) - 1
    ng = int(grp[-1]) + 1
    f0 = np.zeros(ng, np.int64)
    f1 = np.full(ng, -1, np.int64)
    np.copyto(f0, fs[np.flatnonzero(first)])
    second = np.flatnonzero(~first)
    if len(second):
        f1[grp[second]] = fs[second]
    dot = np.ones(ng)
    two = f1 >= 0
    if two.any():
        dot[two] = np.einsum("ij,ij->i", fn[f0[two]], fn[f1[two]])
    ang = np.degrees(np.arccos(np.clip(dot, -1.0, 1.0)))
    sharp_key = ks[np.flatnonzero(first)][ang > deg]
    ev = np.empty(nedge * 2, np.int32)
    me.edges.foreach_get("vertices", ev)
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


# =============================================================================
# 13.  MATERIALS
# =============================================================================
def _srgb(hexs):
    h = hexs.lstrip("#")
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255.0
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (out[0], out[1], out[2], 1.0)


class MB(object):
    """Small node-graph builder."""

    def __init__(self, name):
        m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
        m.use_nodes = True
        self.m = m
        self.nt = m.node_tree
        self.nt.nodes.clear()
        self.x = 0

    def n(self, t, x=None, y=0, **kw):
        nd = self.nt.nodes.new(t)
        self.x += 180 if x is None else 0
        nd.location = (self.x if x is None else x, y)
        for k, v in kw.items():
            setattr(nd, k, v)
        return nd

    def link(self, a, ao, b, bi):
        self.nt.links.new(a.outputs[ao], b.inputs[bi])

    def attr(self, name, y=0):
        a = self.n("ShaderNodeAttribute", x=-2000, y=y)
        a.attribute_name = name
        return a

    def objco(self, y=0):
        return self.n("ShaderNodeTexCoord", x=-2200, y=y)

    def mapping(self, co, so, scale, y=0, loc=(0, 0, 0)):
        mp = self.n("ShaderNodeMapping", x=-1800, y=y)
        mp.inputs["Scale"].default_value = scale
        mp.inputs["Location"].default_value = loc
        self.link(co, so, mp, "Vector")
        return mp

    def noise(self, vec, vo, scale, detail=6.0, rough=0.55, w=None, y=0, dist=0.0,
              lac=2.0):
        nd = self.n("ShaderNodeTexNoise", x=-1550, y=y)
        nd.noise_dimensions = "4D"
        nd.inputs["Scale"].default_value = scale
        nd.inputs["Detail"].default_value = detail
        nd.inputs["Roughness"].default_value = rough
        nd.inputs["Lacunarity"].default_value = lac
        if "Distortion" in nd.inputs:
            nd.inputs["Distortion"].default_value = dist
        self.link(vec, vo, nd, "Vector")
        if w is not None:
            self.link(w[0], w[1], nd, "W")
        return nd

    def vor(self, vec, vo, scale, y=0, feature="F1", w=None, rand=0.9):
        nd = self.n("ShaderNodeTexVoronoi", x=-1550, y=y)
        nd.voronoi_dimensions = "4D"
        nd.feature = feature
        nd.inputs["Scale"].default_value = scale
        if "Randomness" in nd.inputs:
            nd.inputs["Randomness"].default_value = rand
        self.link(vec, vo, nd, "Vector")
        if w is not None:
            self.link(w[0], w[1], nd, "W")
        return nd

    def wave(self, vec, vo, scale, y=0, dist=0.0, detail=2.0, direction="X",
             wtype="BANDS", profile="SIN"):
        nd = self.n("ShaderNodeTexWave", x=-1550, y=y)
        nd.wave_type = wtype
        nd.bands_direction = direction
        nd.wave_profile = profile
        nd.inputs["Scale"].default_value = scale
        nd.inputs["Distortion"].default_value = dist
        nd.inputs["Detail"].default_value = detail
        self.link(vec, vo, nd, "Vector")
        return nd

    def ramp(self, src, so, stops, y=0, interp="LINEAR"):
        r = self.n("ShaderNodeValToRGB", y=y)
        r.color_ramp.interpolation = interp
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
        nd = self.n("ShaderNodeMix", y=y)
        nd.data_type = "RGBA"
        nd.blend_type = blend
        if isinstance(fac, (int, float)):
            nd.inputs[0].default_value = float(fac)
        else:
            self.link(fac, fo, nd, "Factor")
        if isinstance(a, tuple):
            nd.inputs[6].default_value = a
        else:
            self.nt.links.new(a.outputs[ao], nd.inputs[6])
        if isinstance(b, tuple):
            nd.inputs[7].default_value = b
        else:
            self.nt.links.new(b.outputs[bo], nd.inputs[7])
        return nd

    def math(self, op, a, ao, b=None, bo=None, y=0, clamp=False):
        nd = self.n("ShaderNodeMath", y=y)
        nd.operation = op
        nd.use_clamp = clamp
        if isinstance(a, (int, float)):
            nd.inputs[0].default_value = float(a)
        else:
            self.nt.links.new(a.outputs[ao], nd.inputs[0])
        if b is not None:
            if isinstance(b, (int, float)):
                nd.inputs[1].default_value = float(b)
            else:
                self.nt.links.new(b.outputs[bo], nd.inputs[1])
        return nd


# THE PALETTE.  Aluminium's own F0 is (0.913, 0.921, 0.924).  A 25 micron
# architectural anodic film is a lossy dielectric over it, so the metal reads
# DARKER and very slightly warmer than raw alu, and the seven batches differ by
# a delta-E of 1.2 to 3.0 -- small numbers that are unmistakable side by side,
# which is exactly the point.
ALU_F0 = (0.913, 0.921, 0.924, 1.0)      # raw aluminium, F0.  What a scratch
                                        # through the anodic film exposes.

# THE FINISH IS MEDIUM BRONZE ANODISED, AND THAT IS A DECISION WITH REASONS.
#
# The first two macros were natural silver, and both came back as white paper:
# a near-specular F0-0.79 metal on a vertical wall reflects the sky and only the
# sky, so 180 panels rendered as one flat clipped value (mean 0.847, then 0.787)
# and every layer of history underneath was invisible.  Lowering the exposure was
# not available -- the contract owns the grade -- and it would have been the wrong
# fix anyway.
#
# Medium bronze (AA-M10C22A44, electrolytic tin colouring) solves it physically:
# F0 drops to ~0.30 so the panel sits a stop and a half below the sky instead of
# on top of it, the rain tracks and the soiling finally read as the pale marks
# they are, and a scratch shows BRIGHT SILVER through the film, which is the
# single most recognisable thing that happens to a coloured anodised facade.
#
# It also earns the manifest's first variation axis.  Tin colouring is the
# WORST process in architectural metalwork for batch consistency: the shade
# depends on current density, bath age and where the jig hung, and a bronze job
# arriving in seven deliveries WILL show a quilt.  On silver that axis is a
# 1 % academic exercise; on bronze it is the thing everybody complains about.
BATCH_TINT = [
    (0.368, 0.288, 0.214, 1.0),     # 0  the specified shade
    (0.318, 0.256, 0.202, 1.0),     # 1  a delivery and a half dark, and red
    (0.416, 0.325, 0.238, 1.0),     # 2  light
    (0.350, 0.290, 0.238, 1.0),     # 3  pink -- a cold bath
    (0.286, 0.222, 0.166, 1.0),     # 4  the bad rack: 22 % dark, and everybody
                                    #    on site saw it from the car park
    (0.395, 0.300, 0.208, 1.0),     # 5  gold
    (0.448, 0.356, 0.270, 1.0),     # 6  the late replacement delivery, so light
]                                   #    it may as well be a different building
COL_SOIL = _srgb("7d786d")
COL_RAIN = _srgb("948d80")
# HARD WATER LEAVES A RING OF ITS OWN DISSOLVED SOLIDS.  On a dark bronze
# anodic film that deposit is nearly white, it is matt, and it is a DIELECTRIC
# lying on a metal -- which is why a spotted panel reads as a different
# material in the same frame, and why it is the loudest 6 mm feature on any
# real facade that has ever been rained on.
COL_SCALE = _srgb("cdc7bb")
COL_SPECK = _srgb("3c382f")     # atmospheric fallout: soot, brake dust, pollen
COL_CRAZE = _srgb("cfd3d6")
COL_BLOOM = _srgb("e4e7e6")
COL_HAZ = _srgb("6f7276")
COL_SS = (0.94, 0.94, 0.95, 1.0)
COL_MILL = (0.86, 0.87, 0.88, 1.0)
COL_EPDM = _srgb("17181a")
COL_CAVITY = _srgb("0e0f10")
COL_GALV = (0.76, 0.78, 0.79, 1.0)

_MATS = {}


def mat_anodised():
    """THE panel material.  Fifteen attributes (ATTRS), nineteen layers.

      1  batch tint by ramp on 'bat'        seven deliveries, seven shades
      2  rack drift by 'rack'               where it hung in the tank
      3  immersion gradient by 'imm'        the end that went in first is thicker
      4  oxide cloudiness (NOISE)           anodising is never even
      5  etch flow lines (WAVE)             the pre-treatment's own streaking
      6  rolling grain                      ANISOTROPY ONLY.  It used to drive a
                                            bump too, at a 0.93 mm period
                                            against a 0.9643 mm pixel; see the
                                            grain section for why that could
                                            only ever alias.
      7  rain fingers (stretched NOISE)     what runs out of every joint
      8  atmospheric soil (NOISE)           the bottom of a panel is dirtier
      9  corrosion bloom (VORONOI)          white pitting where the film broke
     10  suction-pad rings (from 'hand')    every cassette was picked up twice
     11  heat-affected zone (from 'wld')    the corner weld is always duller
     12  fold dulling (from 'fold','edg')   anodising on a bend is thinner
     13  BEVEL                              a 0.4 mm arris nothing meshes

    and the five PIXEL-SCALE layers, which are the ones that decide whether
    this reads as metal at 0.9643 mm/px:

      A  mineral spotting (VORONOI ring)    6 mm coffee-ring water spots
      B  atmospheric fallout (NOISE+VOR)    1-2 mm soot and brake-dust specks
      C  wipe scratches (VORONOI edge)      0.2 mm, long, along the grain
      D  film chips at the arris (VORONOI)  1-3 mm, bright, edges only
      E  roll-forming ripple (WAVE bump)    55 mm, 0.012 mm -- a whisper, and
                                            envelope-gated.  It was 0.09 mm and
                                            drew corduroy; five control renders
                                            named it.
      F  mill score lines (WAVE SAW)        rare, sparsity-gated.  Ungated it
                                            drew a contour map on every panel.
      G  sheen break-up (NOISE, roughness)  45 mm, roughness only

    EVERY AMPLITUDE IN E AND F IS THE RESULT OF A CONTROL RENDER, not a taste.
    The method that found them is in work/sfp/: render a 16-bit undenoised crop
    at full 4K density, FFT it along both axes, and zero one node at a time
    until the spectral line moves.  An 8-bit denoised frame cannot be used --
    measured on this item, a denoised sky's r1 band contrast (0.519 %) equalled
    the in-focus panel's (0.541 %).
    """
    b = MB("SFP_Anodised")
    co = b.objco()
    oi = b.n("ShaderNodeObjectInfo", x=-2200, y=-900)
    a_bat = b.attr("bat", y=900)
    a_rack = b.attr("rack", y=780)
    a_imm = b.attr("imm", y=660)
    a_grn = b.attr("grn", y=540)
    a_gfl = b.attr("gflip", y=420)
    a_fold = b.attr("fold", y=300)
    a_edg = b.attr("edg", y=180)
    a_run = b.attr("run", y=60)
    a_sky = b.attr("sky", y=-60)
    a_dam = b.attr("dam", y=-180)
    a_hand = b.attr("hand", y=-300)
    a_wld = b.attr("wld", y=-420)
    a_shl = b.attr("shl", y=-540)
    a_age = b.attr("age", y=-660)
    a_sd = b.attr("sd", y=-780)

    # ---- 1-3. the batch, the rack and the tank -----------------------------
    stops = [((i + 0.5) / N_BATCHES, BATCH_TINT[i]) for i in range(N_BATCHES)]
    stops = [(0.0, BATCH_TINT[0])] + stops + [(1.0, BATCH_TINT[-1])]
    r_bat = b.ramp(a_bat, "Fac", stops, y=900, interp="CONSTANT")
    rack_k = b.math("MULTIPLY_ADD", a_rack, "Fac", 0.055, None, y=780)
    rack_k.inputs[2].default_value = 0.9725
    c_rack = b.mix(1.0, None, r_bat, "Color", rack_k, "Value", y=860,
                   blend="MULTIPLY")
    imm_k = b.math("MULTIPLY_ADD", a_imm, "Fac", 0.030, None, y=660)
    imm_k.inputs[2].default_value = 0.985
    c_imm = b.mix(1.0, None, c_rack, "Result", imm_k, "Value", y=800,
                  blend="MULTIPLY")
    # the 180-degree flip: an anodised panel hung the other way up is a
    # measurably different shade at a grazing sun.  This is the complaint.
    gf = b.math("MULTIPLY_ADD", a_gfl, "Fac", -0.022, None, y=420)
    gf.inputs[2].default_value = 1.011
    c_gf = b.mix(1.0, None, c_imm, "Result", gf, "Value", y=760,
                 blend="MULTIPLY")

    # ---- 4. oxide cloudiness ------------------------------------------------
    n_oxide = b.noise(co, "Object", 2.6, detail=5.0, rough=0.55,
                      w=(a_sd, "Fac"), y=600, dist=0.25)
    ox = b.ramp(n_oxide, "Fac", [(0.30, (0.972, 0.974, 0.977, 1)),
                                 (0.52, (1.0, 1.0, 1.0, 1)),
                                 (0.74, (1.026, 1.024, 1.020, 1))], y=600)
    c_ox = b.mix(1.0, None, c_gf, "Result", ox, "Color", y=700, blend="MULTIPLY")

    # ---- 5. etch flow lines -------------------------------------------------
    # the pre-treatment etch leaves faint lines in the rolling direction.  They
    # are 40-120 mm apart, they wander, and they are the single most reliable
    # tell that a metal panel is anodised rather than painted.
    # 12 bands to the metre = an 83 mm wavelength, which is the pitch etch
    # streaking actually comes out at.  The first version compressed the
    # coordinate 26x first and produced a 3.5 mm stripe -- a moire generator,
    # not a finish.
    w_flow_a = b.wave(co, "Object", 12.0, y=460, dist=5.5, detail=3.0,
                      direction="Y")
    w_flow_b = b.wave(co, "Object", 12.0, y=380, dist=5.5, detail=3.0,
                      direction="X")
    flow = b.mix(a_grn, "Fac", w_flow_a, "Fac", w_flow_b, "Fac", y=420)
    flow_r = b.ramp(flow, "Result", [(0.30, (0.984, 0.986, 0.989, 1)),
                                     (0.70, (1.013, 1.011, 1.008, 1))], y=420)
    # an etch streak is not a stripe pattern: it comes and goes down the sheet.
    n_flowmod = b.noise(co, "Object", 1.7, detail=4.0, rough=0.5,
                        w=(a_sd, "Fac"), y=340)
    flow_mod = b.mix(n_flowmod, "Fac", (1.0, 1.0, 1.0, 1), None, flow_r, "Color",
                     y=420)
    c_flow = b.mix(1.0, None, c_ox, "Result", flow_mod, "Result", y=640,
                   blend="MULTIPLY")

    # ---- 11-12. the weld zone and the fold ---------------------------------
    # anodising follows the metal: it is thinner where the sheet was stretched
    # round the 4.5-5.5 mm fold radius, and it is burnt where the corner was
    # welded.
    fold_m = b.math("MULTIPLY", a_fold, "Fac", 0.16, None, y=300, clamp=True)
    c_fold = b.mix(fold_m, "Value", c_flow, "Result", (0.72, 0.727, 0.733, 1),
                   None, y=560)
    wld_m = b.math("MULTIPLY", a_wld, "Fac", 0.55, None, y=-420, clamp=True)
    c_wld = b.mix(wld_m, "Value", c_fold, "Result", COL_HAZ, None, y=500)

    # ---- 7. rain fingers ----------------------------------------------------
    mp_rain = b.mapping(co, "Object", (7.0, 0.45, 7.0), y=60)
    n_rain = b.noise(mp_rain, "Vector", 5.5, detail=7.0, rough=0.62,
                     w=(a_sd, "Fac"), y=60, dist=0.9)
    rain_m = b.math("MULTIPLY", a_run, "Fac", n_rain, "Fac", y=20, clamp=True)
    rain_m = b.math("POWER", rain_m, "Value", 0.78, None, y=-10, clamp=True)
    rain_m = b.math("MULTIPLY", rain_m, "Value", 0.88, None, y=-40, clamp=True)
    c_rain = b.mix(rain_m, "Value", c_wld, "Result", COL_RAIN, None, y=440)

    # ---- 8. atmospheric soil ------------------------------------------------
    n_soil = b.noise(co, "Object", 3.4, detail=7.0, rough=0.6,
                     w=(a_sd, "Fac"), y=-60)
    soil_m = b.math("MULTIPLY", a_sky, "Fac", n_soil, "Fac", y=-90, clamp=True)
    soil_m = b.math("MULTIPLY", soil_m, "Value", 0.80, None, y=-120, clamp=True)
    c_soil = b.mix(soil_m, "Value", c_rain, "Result", COL_SOIL, None, y=380)

    # the sheltered band under a coping or a sign backplate washes the dirt
    # back off -- a facade's cleanest metal is always where the rain never got.
    shl_m = b.math("MULTIPLY", a_shl, "Fac", 0.85, None, y=-540, clamp=True)
    c_shl = b.mix(shl_m, "Value", c_soil, "Result", (1.14, 1.13, 1.11, 1),
                  None, y=340, blend="MULTIPLY")

    # ---- 9. corrosion bloom -------------------------------------------------
    v_pit = b.vor(co, "Object", 55.0, y=-180, feature="F1", w=(a_sd, "Fac"))
    pit_r = b.ramp(v_pit, "Distance", [(0.0, (1, 1, 1, 1)), (0.10, (0, 0, 0, 1))],
                   y=-180)
    dam_m = b.math("MULTIPLY", a_dam, "Fac", pit_r, "Color", y=-210, clamp=True)
    # A CRAZED FILM IS NOT A BREACHED FILM, and running it to bare aluminium put
    # TEN WHITE SPLASHES on the corner render.  Measured, not guessed: projecting
    # every vertex with dam > 0.40 into CAM_SFP_Corner (work/sfp/blobs.py) put
    # crazed regions at px 41,1531 / 979,1577 / 1605,1617 / 2313,1733 /
    # 3056,1729 ... and the blobs in the frame sit on those coordinates to within
    # a blob radius.  So the blobs ARE this layer.
    #
    # Why it read as paint and not as damage: ALU_F0 = (0.913, 0.921, 0.924) is
    # the brightest albedo on the item, mixed in at 0.55 over a dent whose whole
    # relief is 0.25-2.2 mm -- about 2 px at this distance.  That is a COLOUR
    # MARK WITH NO GEOMETRY BEHIND IT, which is the exact failure the campaign
    # brief names, and it is what "not a grass gray line done etc." means.
    #
    # The physics: bare metal appears where the film is REMOVED -- a scratch, a
    # chip -- and those layers already do that, correctly, at sub-pixel width.
    # Where the film is merely crazed by the metal stretching under it, the
    # 25 micron oxide micro-cracks and starts to SCATTER: it goes slightly pale
    # and milky and much rougher, and it stops being a clean mirror.  So the
    # loud half of a crazed patch is ROUGHNESS, not albedo -- the same lesson as
    # the etch mottle, which cost an iteration in the other direction.
    craze = b.math("MULTIPLY", a_dam, "Fac", 0.16, None, y=-240, clamp=True)
    # ...and the roughness half keeps the strength the albedo just gave up, so a
    # dent still READS -- as a patch that has stopped mirroring, which is what a
    # dent in an anodised sheet actually looks like.
    craze_rg = b.math("MULTIPLY", a_dam, "Fac", 0.62, None, y=-255, clamp=True)
    c_craze = b.mix(craze, "Value", c_shl, "Result", COL_CRAZE, None, y=280)
    dam_m = b.math("MULTIPLY", dam_m, "Value", 0.55, None, y=-225, clamp=True)
    c_pit = b.mix(dam_m, "Value", c_craze, "Result", COL_BLOOM, None, y=240)

    # ---- 10. suction-pad rings ---------------------------------------------
    # A VACUUM LIFTER LEAVES A WHISPER, NOT A STAIN.  The fourth macro ran this
    # at 0.20 and put two hard grey doughnuts on every panel in the frame; the
    # real mark is a faint change in how the film takes the light, and you only
    # notice it when the sun is exactly there.
    hand_m = b.math("MULTIPLY", a_hand, "Fac", 0.055, None, y=-300, clamp=True)
    col = b.mix(hand_m, "Value", c_pit, "Result", (1.04, 1.04, 1.045, 1), None,
                y=200, blend="MULTIPLY")

    # ---- roughness ----------------------------------------------------------
    # architectural anodising is a satin, not a mirror: 0.24-0.32, rising on
    # the folds, on the dirt and on the crazed metal.
    n_rgh = b.noise(co, "Object", 40.0, detail=5.0, rough=0.5,
                    w=(a_sd, "Fac"), y=-900)
    # 0.17-0.26.  The second macro ran this at 0.30-0.39 and the wide lobe
    # scooped up the sun 30 deg off the mirror direction, which is what turned
    # the whole facade into one warm sheen.  A tighter lobe both kills that and
    # -- the actual point -- makes the reflected horizon SHARP, so a 2 mm
    # oil-can bow visibly bends it.  That bend is how a facade shows its
    # flatness, and it is the manifest's second variation axis.
    rg = b.ramp(n_rgh, "Fac", [(0.28, (0.172, 0.172, 0.172, 1)),
                               (0.72, (0.258, 0.258, 0.258, 1))], y=-900)
    rg = b.mix(fold_m, "Value", rg, "Color", (0.36, 0.36, 0.36, 1), None, y=-940)
    rg = b.mix(soil_m, "Value", rg, "Result", (0.78, 0.78, 0.78, 1), None, y=-980)
    rg = b.mix(rain_m, "Value", rg, "Result", (0.70, 0.70, 0.70, 1), None, y=-1020)
    rg = b.mix(craze_rg, "Value", rg, "Result", (0.74, 0.74, 0.74, 1), None,
               y=-1060)
    rg = b.mix(hand_m, "Value", rg, "Result", (0.155, 0.155, 0.155, 1), None,
               y=-1100)

    # ---- THE ETCH MOTTLE.  At 0.9643 mm/px a 3 mm feature is three pixels, and
    # the first six macros had NOTHING at that scale: peeped 1:1 the panels were
    # a smooth gradient with a bright arris, which is a rendering of a metal and
    # not a metal.  A caustic-etched anodic film is mottled at 2-5 mm -- that is
    # the crystallography of the etch, it is the reason the finish is matt at
    # all, and it is the scale the lens resolves here.
    n_etch = b.noise(co, "Object", 260.0, detail=5.0, rough=0.58,
                     w=(a_sd, "Fac"), y=-760, lac=2.4)
    # ON A METAL, VARY THE ROUGHNESS AND THE NORMAL -- NOT THE ALBEDO.  This is
    # the whole difference between a mottled metal and a mottled stone, and it
    # cost an iteration to learn: at +-6 % albedo the panels came back reading
    # as fine limestone, because broadband albedo mottle is what a DIELECTRIC
    # does.  A metal's own colour is its Fresnel F0 and that does not vary
    # across 4 mm of the same sheet.  What varies is how the etch left the
    # micro-facets, which is roughness, and where they point, which is normal.
    # So: albedo +-3.2 % (was +-2.6 %, which was invisible, then +-6 %, which
    # was stone), roughness +-0.08, normal 3.1 deg.
    etch_c = b.ramp(n_etch, "Fac", [(0.26, (0.968, 0.971, 0.975, 1)),
                                    (0.74, (1.032, 1.029, 1.023, 1))], y=-760)
    col = b.mix(1.0, None, col, "Result", etch_c, "Color", y=160,
                blend="MULTIPLY")
    # and it moves the ROUGHNESS, which on a metal is the louder half: a matt
    # patch and a satin patch 4 mm apart return completely different amounts of
    # a 12.5 deg sun.
    rg = b.mix(n_etch, "Fac", rg, "Result", (0.335, 0.335, 0.335, 1), None,
               y=-1140)

    # =====================================================================
    # THE PIXEL-SCALE LAYERS.  Everything above this point is 40 mm and
    # coarser -- batch, rack, tank, cloud, streak, soil.  At 0.9643 mm/px the
    # lens resolves down to about 2 mm, and until these five layers existed
    # there was NOTHING between 2 mm and 40 mm on this surface.  That gap is
    # the entire difference between "a wall the colour of bronze" and a
    # facade panel, and it is what the sixth macro was rejected for.
    # =====================================================================

    # ---- A. MINERAL SPOTTING.  6 mm rings of dissolved solids, left where a
    # droplet sat and dried.  A ring, not a disc: the solids migrate to the
    # contact line as the drop evaporates (this is the coffee-ring effect, and
    # it is why real water spots are annuli with clean middles).
    v_spot = b.vor(co, "Object", 158.0, y=-1700, feature="F1",
                   w=(a_sd, "Fac"), rand=0.95)
    spot_ring = b.ramp(v_spot, "Distance",
                       [(0.085, (0.06, 0.06, 0.06, 1)),
                        (0.150, (0.10, 0.10, 0.10, 1)),
                        (0.230, (1.00, 1.00, 1.00, 1)),
                        (0.310, (0.34, 0.34, 0.34, 1)),
                        (0.400, (0.00, 0.00, 0.00, 1))], y=-1700)
    # spots come in SPLASHES, not evenly: where the water actually ran
    n_spotfield = b.noise(co, "Object", 9.0, detail=4.0, rough=0.55,
                          w=(a_sd, "Fac"), y=-1740)
    sf = b.ramp(n_spotfield, "Fac", [(0.34, (0, 0, 0, 1)), (0.62, (1, 1, 1, 1))],
                y=-1740)
    spot_m = b.math("MULTIPLY", spot_ring, "Color", sf, "Color", y=-1770,
                    clamp=True)
    # only where rain reached: the run field, plus a floor so the whole panel
    # carries a few from wind-blown drizzle
    wet = b.math("MULTIPLY_ADD", a_run, "Fac", 0.62, None, y=-1800, clamp=True)
    wet.inputs[2].default_value = 0.17
    spot_m = b.math("MULTIPLY", spot_m, "Value", wet, "Value", y=-1830,
                    clamp=True)
    spot_m = b.math("MULTIPLY", spot_m, "Value", 0.62, None, y=-1860, clamp=True)
    col = b.mix(spot_m, "Value", col, "Result", COL_SCALE, None, y=120)
    rg = b.mix(spot_m, "Value", rg, "Result", (0.62, 0.62, 0.62, 1), None,
               y=-1180)

    # ---- B. ATMOSPHERIC FALLOUT.  1-2 mm specks of soot and brake dust that
    # land on a horizontal-ish film of dirt and never wash off.  This is the
    # layer that stops a metal panel looking injection-moulded: real surfaces
    # outdoors are PEPPERED, and the pepper is per-pixel.
    n_speck = b.noise(co, "Object", 620.0, detail=3.0, rough=0.5,
                      w=(a_sd, "Fac"), y=-1900, lac=2.6)
    speck_r = b.ramp(n_speck, "Fac", [(0.545, (0, 0, 0, 1)),
                                      (0.640, (1, 1, 1, 1))], y=-1900)
    v_grit = b.vor(co, "Object", 340.0, y=-1940, feature="F1",
                   w=(a_sd, "Fac"), rand=1.0)
    grit_r = b.ramp(v_grit, "Distance", [(0.030, (1, 1, 1, 1)),
                                         (0.085, (0, 0, 0, 1))], y=-1940)
    speck = b.math("MAXIMUM", speck_r, "Color", grit_r, "Color", y=-1970,
                   clamp=True)
    dirtiness = b.math("MULTIPLY_ADD", a_sky, "Fac", 0.85, None, y=-2000,
                       clamp=True)
    dirtiness.inputs[2].default_value = 0.22
    speck_m = b.math("MULTIPLY", speck, "Value", dirtiness, "Value", y=-2030,
                     clamp=True)
    speck_m = b.math("MULTIPLY", speck_m, "Value", 0.38, None, y=-2060,
                     clamp=True)
    col = b.mix(speck_m, "Value", col, "Result", COL_SPECK, None, y=80)
    # a speck of grit is matt and it is OPAQUE: the roughness step is the loud
    # half of it, which is why fallout reads even on a panel it has barely
    # discoloured.
    rg = b.mix(speck_m, "Value", rg, "Result", (0.88, 0.88, 0.88, 1), None,
               y=-1220)

    # ---- C. WIPE SCRATCHES.  The first version drew these with an isotropic
    # Voronoi at 26/m, which is a CRAZE PATTERN -- peeped at 4x the panels
    # looked cracked.  A scratch on a cassette comes from a glove, a strap or a
    # sleeve dragged ALONG the sheet while it was being hung, so they are long,
    # straight, parallel to the grain and there are a dozen of them, not a net.
    # A 2-D VORONOI CANNOT DRAW A 1-D FEATURE, AND BOTH ATTEMPTS TO MAKE IT
    # PROVED IT.  Mapping Scale MULTIPLIES the coordinate, so (1, 46, 1) makes
    # the texture 46x SMALLER along y, not 46x longer: the cells came out
    # 33 x 0.72 x 33 mm and DISTANCE_TO_EDGE across pancakes is a 0.72 mm
    # GRATING, 1400 lines to the metre against a 0.9643 mm pixel.  Reversing it
    # to (0.05, 1, 0.05) stretched the cells the right way and was WORSE: the
    # distance metric is stretched with the space, so an edge running along y is
    # 0.006 units away in a direction that is now 20x wider, and the render came
    # back with 4 mm bright zigzags across every panel.  A scratch that reads as
    # bare aluminium at roughness 0.105 is the brightest thing on the facade, so
    # getting its WIDTH wrong by 13x is not a subtle error.
    #
    # A scratch is a ONE-DIMENSIONAL feature: a position across the grain, and
    # nothing else.  So generate it in one dimension, where the width is
    # analytic instead of emergent.  Voronoi 1D consumes only W, so W carries
    # the across-grain coordinate (local Y for a normally hung panel, local X
    # for one hung sideways) plus 'sd' to decorrelate the panels.  Cells are
    # then intervals of ~1/30 m = 33 mm along that one axis, DISTANCE_TO_EDGE is
    # a distance in that same axis, and the ramp width is a real length:
    #     0.009 voronoi units / 30 per m = 0.30 mm, exactly as claimed.
    # Straight, parallel, irregularly spaced, and no second axis to go wrong.
    sep = b.n("ShaderNodeSeparateXYZ", x=-1900, y=-2120)
    b.link(co, "Object", sep, "Vector")
    acr = b.mix(a_grn, "Fac", sep, "Y", sep, "X", y=-2120)
    acr_w = b.math("MULTIPLY_ADD", acr, "Result", 30.0, None, y=-2150)
    b.nt.links.new(a_sd.outputs["Fac"], acr_w.inputs[2])
    v_scr = b.n("ShaderNodeTexVoronoi", x=-1700, y=-2140)
    v_scr.voronoi_dimensions = "1D"
    v_scr.feature = "DISTANCE_TO_EDGE"
    v_scr.inputs["Scale"].default_value = 1.0
    if "Randomness" in v_scr.inputs:
        v_scr.inputs["Randomness"].default_value = 1.0
    b.link(acr_w, "Value", v_scr, "W")
    # 0.30 mm wide -- under a third of a pixel, so it is drawn by its SHADING,
    # not its width, which is exactly how you see a scratch on metal in life.
    scr_r = b.ramp(v_scr, "Distance", [(0.0, (1, 1, 1, 1)),
                                       (0.009, (0, 0, 0, 1))], y=-2140)
    # SPARSITY, AND IT HAS TO BE PER-LINE.  "A dozen of them, not a net" was in
    # the comment and not in the graph: at 33 mm spacing a 1.2 m panel carries
    # 36 lines, which is a brushed finish, not damage.  The first attempt gated
    # them with a NOISE IN SPACE, which is the wrong shape of mask -- a 1.1 m
    # noise blob turns on thirty CONSECUTIVE lines at once, and the render came
    # back with an evenly spaced LADDER of dashes measuring a 36 mm fundamental
    # at 10x the noise floor.  A ruler, not damage.
    #
    # The mask has to be indexed by the LINE, not by the position.  A second 1D
    # Voronoi on the SAME W with feature F1 returns a value that is constant
    # within a cell and random between cells, so thresholding it keeps or drops
    # each scratch individually and leaves the survivors irregularly spaced.
    v_scrid = b.n("ShaderNodeTexVoronoi", x=-1700, y=-2175)
    v_scrid.voronoi_dimensions = "1D"
    v_scrid.feature = "F1"
    v_scrid.inputs["Scale"].default_value = 1.0
    if "Randomness" in v_scrid.inputs:
        v_scrid.inputs["Randomness"].default_value = 1.0
    b.link(acr_w, "Value", v_scrid, "W")
    # keep ~1 cell in 5, and give the survivors DIFFERENT depths: a strap drawn
    # across a sheet does not press equally hard twice.
    scrpick = b.ramp(v_scrid, "Color", [(0.780, (0, 0, 0, 1)),
                                        (0.800, (0.55, 0.55, 0.55, 1)),
                                        (0.930, (0.80, 0.80, 0.80, 1)),
                                        (1.000, (1, 1, 1, 1))], y=-2175)
    scr_r = b.math("MULTIPLY", scr_r, "Color", scrpick, "Color", y=-2185,
                   clamp=True)
    # they do not run the whole height: a wipe starts and stops
    n_scrlen = b.noise(co, "Object", 3.2, detail=3.0, rough=0.5,
                       w=(a_sd, "Fac"), y=-2200)
    scrlen = b.ramp(n_scrlen, "Fac", [(0.40, (0, 0, 0, 1)), (0.58, (1, 1, 1, 1))],
                    y=-2200)
    scr_m = b.math("MULTIPLY", scr_r, "Value", scrlen, "Color", y=-2230,
                   clamp=True)
    scr_m = b.math("MULTIPLY", scr_m, "Value", a_age, "Fac", y=-2260, clamp=True)
    # A SCRATCH THROUGH A COLOURED ANODIC FILM IS BRIGHT SILVER.  25 microns of
    # bronze oxide over aluminium: take the oxide off and what is underneath is
    # F0 = 0.92 and burnished smooth by whatever took it off.
    col = b.mix(scr_m, "Value", col, "Result", ALU_F0, None, y=40)
    rg = b.mix(scr_m, "Value", rg, "Result", (0.105, 0.105, 0.105, 1), None,
               y=-1260)

    # ---- D. FILM CHIPS AT THE ARRIS.  Anodising is 25 microns of ceramic on a
    # soft metal, and every fold on every panel got knocked at some point
    # between the anodising line and the mast climber.  A chip is 1-3 mm,
    # bright, and ONLY within about 40 mm of an edge -- which is what 'edg' is.
    edge_near = b.ramp(a_edg, "Fac", [(0.0, (1, 1, 1, 1)),
                                      (0.27, (0, 0, 0, 1))], y=180)
    v_chip = b.vor(co, "Object", 96.0, y=-2320, feature="F1", w=(a_sd, "Fac"),
                   rand=1.0)
    chip_r = b.ramp(v_chip, "Distance", [(0.020, (1, 1, 1, 1)),
                                         (0.062, (0, 0, 0, 1))], y=-2320)
    chip_m = b.math("MULTIPLY", chip_r, "Color", edge_near, "Color", y=-2350,
                    clamp=True)
    chip_m = b.math("MULTIPLY", chip_m, "Value", a_age, "Fac", y=-2380,
                    clamp=True)
    chip_m = b.math("MULTIPLY", chip_m, "Value", 0.80, None, y=-2410, clamp=True)
    col = b.mix(chip_m, "Value", col, "Result", ALU_F0, None, y=0)
    rg = b.mix(chip_m, "Value", rg, "Result", (0.30, 0.30, 0.30, 1), None,
               y=-1300)

    # ---- E. THE ROLL-FORMING RIPPLE, which used to be mesh and is not any
    # more (see face_disp for the FFT and the control render that decided it).
    # 44-96 mm pitch, 0.03-0.11 mm deep, running ACROSS the rolling direction,
    # so it flips with 'grn' exactly as the geometry version did.  Object space
    # is metres, so a Wave scale of 18 is a 55 mm band; Distortion is what makes
    # the pitch wander instead of ruling 20 identical stripes across a panel,
    # and 'sd' in the mapping location gives every panel its own phase.
    # LOCAL AXES, because getting these round the wrong way makes a ripple that
    # runs the wrong way and nobody notices for three renders: every cassette
    # mesh is built as (path, height, path) -> local (x, y, z) with LOCAL Y UP
    # THE PANEL and local X/Z along its run.  So the crests, which are parallel
    # to the rolling direction, vary along local Y for a normally-hung panel
    # (grn = 0) and along local X for one hung sideways (grn = 1).  Same
    # convention as the rolling-grain anisotropy below; they must agree,
    # because on a real sheet they are the same rolling.
    sd_off = b.n("ShaderNodeCombineXYZ", x=-1900, y=-2480)
    b.link(a_sd, "Fac", sd_off, "X")
    b.link(a_sd, "Fac", sd_off, "Y")
    b.link(a_sd, "Fac", sd_off, "Z")
    mp_rip = b.n("ShaderNodeMapping", x=-1800, y=-2480)
    b.link(co, "Object", mp_rip, "Vector")
    b.link(sd_off, "Vector", mp_rip, "Location")
    # THE SHADER RIPPLE MADE THE SAME MISTAKE THE MESH RIPPLE MADE.  Moving it
    # off the mesh removed the mesh period and then drew a period of its own.
    # Measured on the first render of this version -- a 16-bit, undenoised,
    # 768-sample crop at full 4K density -- the panel face carried a tight
    # spectral cluster at 11.2-12.3 mm sitting 9-10x above the noise floor, and
    # the whole facade read as corduroy.  FIVE control renders attributed it:
    # zeroing all five bump nodes removed it; zeroing the mill score and the
    # rolling grain did not; zeroing the scratch bump did not; zeroing the etch
    # bump did not; zeroing THIS ONE ALONE removed it completely.
    #
    # The cause is not the 55 mm fundamental, it is Distortion 1.6 x Detail 2.0:
    # the distortion octaves land at 55/4 ~ 14 mm, which at 0.9643 mm/px is a
    # 14 px band, and a periodic NORMAL perturbation on a roughness-0.2 metal
    # is the loudest thing you can do to it.  0.09 mm of bump over a 55 mm wave
    # is a 0.58 deg facet tilt -> 1.2 deg swing in the reflected ray, on a
    # surface whose whole read is the reflection.
    #
    # So: keep the mechanism, because coil ripple is real, but put it back to
    # the amplitude the physics actually claims (0.03-0.11 mm relief, i.e. a
    # WHISPER at this distance) and stop the distortion generating a pixel-scale
    # octave.  Detail 1.0 and Distortion 0.7 leave the 55 mm fundamental
    # wandering without a 14 mm harmonic; Distance 0.000012 is 7.5x down.
    w_rip_a = b.wave(mp_rip, "Vector", 18.0, y=-2480, dist=0.7, detail=1.0,
                     direction="Y")          # bands across a panel hung normally
    w_rip_b = b.wave(mp_rip, "Vector", 18.0, y=-2520, dist=0.7, detail=1.0,
                     direction="X")          # ...and across one hung sideways
    rip = b.mix(a_grn, "Fac", w_rip_a, "Fac", w_rip_b, "Fac", y=-2500)
    # the chatter harmonic: a work roll has a crown AND a beat frequency
    w_rip2 = b.wave(mp_rip, "Vector", 7.4, y=-2560, dist=1.0, detail=1.0,
                    direction="Y")
    rip = b.mix(0.34, None, rip, "Result", w_rip2, "Fac", y=-2540)
    # AND IT COMES AND GOES.  A coil does not ripple uniformly for 20 m; the
    # crown wanders and the levelling takes some of it out.  Without an
    # envelope the ripple is present at full strength on all 180 panels at
    # once, which is the other half of why it read as a woven material.
    n_ripenv = b.noise(co, "Object", 1.4, detail=3.0, rough=0.5,
                       w=(a_sd, "Fac"), y=-2440)
    ripenv = b.ramp(n_ripenv, "Fac", [(0.36, (0, 0, 0, 1)),
                                      (0.66, (1, 1, 1, 1))], y=-2440)
    rip = b.mix(ripenv, "Color", (0.5, 0.5, 0.5, 1), None, rip, "Result",
                y=-2460)
    bump_r = b.n("ShaderNodeBump", x=60, y=-2500)
    bump_r.inputs["Strength"].default_value = 0.55
    bump_r.inputs["Distance"].default_value = 0.000012
    b.link(rip, "Result", bump_r, "Height")

    # ---- F. MILL SCORE LINES.  A coil is dragged over rollers and every so
    # often one picks up a chip and draws a score the whole length of the
    # sheet.  0.2-0.5 mm wide -- a third of a pixel -- so this is a normal and
    # a roughness, never a colour: a score is a groove in the metal that the
    # anodising followed down, not a mark lying on top of it.
    # "EVERY SO OFTEN ONE PICKS UP A CHIP" WAS IN THE COMMENT AND NOT IN THE
    # GRAPH, TWICE.  The original was a SAW Wave at Distortion 8.5 / Detail 6.0,
    # which is not an occasional score but a continuous wandering contour field;
    # ramped to a narrow slice it drew bright lines every 40-130 mm across every
    # panel and the facade read like ripples in sand.  Measured: flattening that
    # one ramp in a control render removed the contour lines and changed nothing
    # else, which is what identified it.  Gating it with a NOISE IN SPACE then
    # failed the same way the scratches did -- a low-frequency blob turns on a
    # whole run of adjacent lines and you get a ladder.
    #
    # A mill score has exactly the same geometry as a wipe scratch: a position
    # across the coil and a length along it.  So it is the SAME 1-D line set,
    # coarser and rarer -- 7 candidate positions per metre, one in seven kept,
    # and it runs the full height because a coil defect does not start and stop.
    mill_w = b.math("MULTIPLY_ADD", acr, "Result", 7.0, None, y=-2600)
    b.nt.links.new(a_sd.outputs["Fac"], mill_w.inputs[2])
    v_mill = b.n("ShaderNodeTexVoronoi", x=-1700, y=-2610)
    v_mill.voronoi_dimensions = "1D"
    v_mill.feature = "DISTANCE_TO_EDGE"
    v_mill.inputs["Scale"].default_value = 1.0
    if "Randomness" in v_mill.inputs:
        v_mill.inputs["Randomness"].default_value = 1.0
    b.link(mill_w, "Value", v_mill, "W")
    # 0.0021 units / 7 per m = 0.30 mm, the width a score actually is
    mill_r = b.ramp(v_mill, "Distance", [(0.0, (1, 1, 1, 1)),
                                         (0.0021, (0, 0, 0, 1))], y=-2610)
    v_millid = b.n("ShaderNodeTexVoronoi", x=-1700, y=-2650)
    v_millid.voronoi_dimensions = "1D"
    v_millid.feature = "F1"
    v_millid.inputs["Scale"].default_value = 1.0
    if "Randomness" in v_millid.inputs:
        v_millid.inputs["Randomness"].default_value = 1.0
    b.link(mill_w, "Value", v_millid, "W")
    millrare = b.ramp(v_millid, "Color", [(0.860, (0, 0, 0, 1)),
                                          (0.875, (0.6, 0.6, 0.6, 1)),
                                          (1.000, (1, 1, 1, 1))], y=-2650)
    mill_m = b.math("MULTIPLY", mill_r, "Color", millrare, "Color", y=-2700,
                    clamp=True)
    bump_m = b.n("ShaderNodeBump", x=130, y=-2620)
    bump_m.inputs["Strength"].default_value = 0.45
    bump_m.inputs["Distance"].default_value = 0.000030
    bump_m.invert = True
    b.link(mill_m, "Value", bump_m, "Height")
    rg = b.mix(mill_m, "Value", rg, "Result", (0.30, 0.30, 0.30, 1), None,
               y=-1420)

    # ---- G. THE SHEEN BREAK-UP.  One more octave between the etch (4 mm) and
    # the oxide cloud (400 mm), on ROUGHNESS ONLY.  A satin metal with a
    # perfectly uniform roughness is the CG tell: real anodising varies over
    # 20-60 mm because the etch bath does, and the eye reads that as the
    # surface being made of something.
    n_sheen = b.noise(co, "Object", 22.0, detail=4.0, rough=0.55,
                      w=(a_sd, "Fac"), y=-1340, lac=2.1)
    sheen_r = b.ramp(n_sheen, "Fac", [(0.30, (0.84, 0.84, 0.84, 1)),
                                      (0.70, (1.19, 1.19, 1.19, 1))], y=-1340)
    rg = b.mix(1.0, None, rg, "Result", sheen_r, "Color", y=-1380,
               blend="MULTIPLY")

    # ---- 6 + 13. the grain: anisotropy and the bump it comes from ----------
    tan = b.n("ShaderNodeTangent", x=-1550, y=-1200)
    tan.direction_type = "UV_MAP"
    tan.uv_map = "sfp_uv"
    aniso_rot = b.math("MULTIPLY", a_grn, "Fac", 0.25, None, y=-1240)
    # THE GRAIN BUMP WAS SITTING EXACTLY ON THE PIXEL AND IT IS GONE.  Mapping
    # scale 120 x Wave scale 9.0 is a period of 1/(9 x 120) m = 0.93 mm, against
    # a 0.9643 mm pixel: a periodic normal perturbation at Nyquist, which cannot
    # render as texture and can only render as moire.  The comment above it
    # claimed "0.05 mm" -- it was 19x coarser than its own docstring, and the
    # docstring's number was the one that made it sound safe.
    #
    # Sub-pixel directional micro-structure on a metal is ANISOTROPY, not a
    # bump: the whole physical content of a brushed or rolled finish is that the
    # specular lobe is wider across the grain than along it, and that is exactly
    # what Anisotropic + Tangent already computes below, at any resolution,
    # without a sampled period to alias.  A control render with this bump zeroed
    # measured no change in any band (r1 1.455 vs 1.455 %), so it was
    # contributing nothing but risk.
    # THE NORMAL STACK, coarsest first, so each layer perturbs the one under it:
    #   ripple 55 mm  ->  mill score 3 mm  ->  etch mottle 4 mm
    #   ->  scratch 0.2 mm  ->  a 0.4 mm bevel
    b.link(bump_r, "Normal", bump_m, "Normal")

    # The scratch NORMAL comes off the same directional field as the scratch
    # colour, so the groove and the silver in it are the same scratch.  The
    # old version ran a separate isotropic Voronoi at 26/m here, which is a
    # 38 mm CRAZE NET -- peeped at 4x the panels looked cracked, not scratched.
    bump2 = b.n("ShaderNodeBump", x=380, y=-1420)
    bump2.inputs["Strength"].default_value = 0.60
    bump2.inputs["Distance"].default_value = 0.00022
    bump2.invert = True                      # a scratch is a groove, not a weld
    b.link(scr_m, "Value", bump2, "Height")
    bump_e = b.n("ShaderNodeBump", x=300, y=-1200)
    # 0.11 mm over a 4 mm mottle is a 3.1 deg facet slope, which is what a
    # caustic etch actually leaves and 2.5x what the first version had.
    bump_e.inputs["Strength"].default_value = 0.85
    bump_e.inputs["Distance"].default_value = 0.00011
    b.link(n_etch, "Fac", bump_e, "Height")
    b.link(bump_m, "Normal", bump_e, "Normal")   # was bump1, the deleted grain
    b.link(bump_e, "Normal", bump2, "Normal")
    bev = b.n("ShaderNodeBevel", x=560, y=-1420)
    bev.samples = 6
    bev.inputs["Radius"].default_value = 0.0004
    b.link(bump2, "Normal", bev, "Normal")

    bsdf = b.n("ShaderNodeBsdfPrincipled", x=900, y=0)
    out = b.n("ShaderNodeOutputMaterial", x=1200, y=0)
    b.link(col, "Result", bsdf, "Base Color")
    b.link(rg, "Result", bsdf, "Roughness")
    b.link(bev, "Normal", bsdf, "Normal")
    b.link(tan, "Tangent", bsdf, "Tangent")
    b.link(aniso_rot, "Value", bsdf, "Anisotropic Rotation")
    # A FILM OF DIRT IS A DIELECTRIC LYING ON A METAL, and the single biggest
    # reason a rendered metal facade looks like painted plastic is that its dirt
    # is a colour multiply while the surface stays 100 % metallic underneath.
    # Where the soil, the rain track or the crazing is, this surface stops being
    # a metal -- which is what actually happens.
    # ADDING FIVE MASKS INTO A CLAMPED SUM IS NOT A COVERAGE MODEL, and it cost
    # a whole iteration: with soil, rain, craze, spotting and fallout all
    # summed, `dirt` saturated at 1.0 over most of every panel, metallic pinned
    # at 0.22, and 180 anodised aluminium cassettes rendered as FINE LIMESTONE.
    # Coverage composites as 1 - PROD(1 - a_i) -- that is what "some of the
    # surface is covered by each of these" actually means -- and a thin film of
    # atmospheric soil does not stop a metal being a metal anyway.  Two tiers:
    #   FILM     soil, rain track, crazed oxide.  Thin, transparent-ish.
    #   DEPOSIT  mineral rings and fallout grit.  Solid, opaque, matt.
    f1 = b.math("MULTIPLY", soil_m, "Value", 0.55, None, y=-1560, clamp=True)
    f2 = b.math("MULTIPLY", rain_m, "Value", 0.42, None, y=-1590, clamp=True)
    f3 = b.math("MULTIPLY", craze_rg, "Value", 0.80, None, y=-1620, clamp=True)
    film = b.math("MAXIMUM", f1, "Value", f2, "Value", y=-1650, clamp=True)
    film = b.math("MAXIMUM", film, "Value", f3, "Value", y=-1680, clamp=True)
    d1 = b.math("MULTIPLY", spot_m, "Value", 0.92, None, y=-1710, clamp=True)
    d2 = b.math("MULTIPLY", speck_m, "Value", 0.88, None, y=-1740, clamp=True)
    dep = b.math("MAXIMUM", d1, "Value", d2, "Value", y=-1770, clamp=True)
    # 1 - (1-film)(1-dep)
    inv_f = b.math("SUBTRACT", 1.0, None, film, "Value", y=-1800)
    inv_d = b.math("SUBTRACT", 1.0, None, dep, "Value", y=-1830)
    clear = b.math("MULTIPLY", inv_f, "Value", inv_d, "Value", y=-1860,
                   clamp=True)
    dirt = b.math("SUBTRACT", 1.0, None, clear, "Value", y=-1890)
    # 0.58, not 0.78: even under a visible film this is still aluminium, and
    # the reason a rendered facade reads as plastic is a metallic channel that
    # gives up too easily.
    met = b.math("MULTIPLY_ADD", dirt, "Value", -0.58, None, y=-1920,
                 clamp=True)
    met.inputs[2].default_value = 1.0
    # ...and a scratch or a chip goes the other way: it takes the oxide OFF and
    # what is left is bare aluminium, the most metallic thing in the frame.
    bare = b.math("MAXIMUM", scr_m, "Value", chip_m, "Value", y=-1710,
                  clamp=True)
    met = b.mix(bare, "Value", met, "Value", (1.0, 1.0, 1.0, 1.0), None,
                y=-1740)
    b.link(met, "Result", bsdf, "Metallic")
    # anisotropy smears the reflected horizon along the grain, which is the
    # anodised tell -- but at 0.52 it smeared it away entirely.
    bsdf.inputs["Anisotropic"].default_value = 0.34
    bsdf.inputs["Coat Weight"].default_value = 0.02
    bsdf.inputs["Coat Roughness"].default_value = 0.28
    bsdf.inputs["IOR"].default_value = 1.60
    bsdf.inputs["Specular IOR Level"].default_value = 0.42
    b.link(bsdf, "BSDF", out, "Surface")
    b.m.use_backface_culling = False
    return b.m


def _simple_metal(name, base, rough, aniso=0.0, noise_scale=180.0, metallic=1.0):
    b = MB(name)
    co = b.objco()
    oi = b.n("ShaderNodeObjectInfo", x=-1200, y=-300)
    n1 = b.noise(co, "Object", noise_scale, detail=6.0, w=(oi, "Random"), y=0)
    n2 = b.noise(co, "Object", noise_scale * 9.0, detail=5.0, w=(oi, "Random"),
                 y=-200)
    col = b.mix(n1, "Fac", base, None,
                tuple(max(0.0, c * 0.86) for c in base[:3]) + (1.0,), None, y=0)
    rg = b.ramp(n2, "Fac", [(0.25, (rough * 0.82, rough * 0.82, rough * 0.82, 1)),
                            (0.75, (rough * 1.22, rough * 1.22, rough * 1.22, 1))],
                y=-200)
    bump = b.n("ShaderNodeBump", x=300, y=-400)
    bump.inputs["Strength"].default_value = 0.22
    bump.inputs["Distance"].default_value = 0.0002
    b.link(n2, "Fac", bump, "Height")
    bev = b.n("ShaderNodeBevel", x=460, y=-400)
    bev.samples = 4
    bev.inputs["Radius"].default_value = 0.0004
    b.link(bump, "Normal", bev, "Normal")
    bsdf = b.n("ShaderNodeBsdfPrincipled", x=700, y=0)
    out = b.n("ShaderNodeOutputMaterial", x=980, y=0)
    b.link(col, "Result", bsdf, "Base Color")
    b.link(rg, "Color", bsdf, "Roughness")
    b.link(bev, "Normal", bsdf, "Normal")
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Anisotropic"].default_value = aniso
    b.link(bsdf, "BSDF", out, "Surface")
    return b.m


def _rubber(name, base):
    b = MB(name)
    co = b.objco()
    oi = b.n("ShaderNodeObjectInfo", x=-1200, y=-300)
    n1 = b.noise(co, "Object", 260.0, detail=7.0, w=(oi, "Random"), y=0)
    n2 = b.noise(co, "Object", 24.0, detail=5.0, w=(oi, "Random"), y=-200)
    col = b.mix(n2, "Fac", base, None, (0.055, 0.055, 0.058, 1), None, y=0)
    rg = b.ramp(n1, "Fac", [(0.3, (0.62, 0.62, 0.62, 1)),
                            (0.8, (0.86, 0.86, 0.86, 1))], y=-200)
    bump = b.n("ShaderNodeBump", x=300, y=-400)
    bump.inputs["Strength"].default_value = 0.5
    bump.inputs["Distance"].default_value = 0.0004
    b.link(n1, "Fac", bump, "Height")
    bsdf = b.n("ShaderNodeBsdfPrincipled", x=700, y=0)
    out = b.n("ShaderNodeOutputMaterial", x=980, y=0)
    b.link(col, "Result", bsdf, "Base Color")
    b.link(rg, "Color", bsdf, "Roughness")
    b.link(bump, "Normal", bsdf, "Normal")
    bsdf.inputs["Specular IOR Level"].default_value = 0.35
    b.link(bsdf, "BSDF", out, "Surface")
    return b.m


def _matte(name, base, rough=0.85, scale=8.0):
    b = MB(name)
    co = b.objco()
    oi = b.n("ShaderNodeObjectInfo", x=-1200, y=-300)
    n1 = b.noise(co, "Object", scale, detail=7.0, w=(oi, "Random"), y=0)
    n2 = b.noise(co, "Object", scale * 20.0, detail=6.0, w=(oi, "Random"), y=-200)
    col = b.mix(n1, "Fac", base, None,
                tuple(c * 0.78 for c in base[:3]) + (1.0,), None, y=0)
    rg = b.ramp(n2, "Fac", [(0.3, (rough * 0.9, rough * 0.9, rough * 0.9, 1)),
                            (0.8, (min(1.0, rough * 1.1),) * 3 + (1,))], y=-200)
    bump = b.n("ShaderNodeBump", x=300, y=-400)
    bump.inputs["Strength"].default_value = 0.35
    bump.inputs["Distance"].default_value = 0.0006
    b.link(n2, "Fac", bump, "Height")
    bsdf = b.n("ShaderNodeBsdfPrincipled", x=700, y=0)
    out = b.n("ShaderNodeOutputMaterial", x=980, y=0)
    b.link(col, "Result", bsdf, "Base Color")
    b.link(rg, "Color", bsdf, "Roughness")
    b.link(bump, "Normal", bsdf, "Normal")
    b.link(bsdf, "BSDF", out, "Surface")
    return b.m


def materials():
    if not _MATS:
        _MATS["anod"] = mat_anodised()
        _MATS["ss"] = _simple_metal("SFP_Stainless", COL_SS, 0.24, aniso=0.35,
                                    noise_scale=320.0)
        _MATS["mill"] = _simple_metal("SFP_MillAlu", COL_MILL, 0.42, aniso=0.2,
                                      noise_scale=140.0)
        _MATS["epdm"] = _rubber("SFP_EPDM", COL_EPDM)
        _MATS["cavity"] = _matte("SFP_Cavity", COL_CAVITY, rough=0.92, scale=6.0)
        _MATS["galv"] = _simple_metal("SFP_Galv", COL_GALV, 0.55, noise_scale=60.0)
        # the parapet upstand and the head flashing are waiting for
        # showroom_parapet_coping; until it lands they are a dull membrane and
        # must not fight the panels for the eye.
        _MATS["upstand"] = _matte("SFP_Upstand", _srgb("55534f"), rough=0.82,
                                  scale=4.0)
        _MATS["conc"] = _matte("SFP_Concrete", _srgb("b6b3ad"), rough=0.86,
                               scale=3.0)
        _MATS["glass"] = _matte("SFP_GlazingBand", _srgb("1b2429"), rough=0.14,
                                scale=2.0)
        # the forecourt is forecourt_paving_bay's precast concrete; this is a
        # stand-in at its albedo, and it is here because it is HALF THE LIGHT
        # that reaches the underside of a cassette at a 12.47 deg sun.
        _MATS["ground"] = _matte("SFP_Ground", _srgb("a4a099"), rough=0.90,
                                 scale=1.4)
        _MATS["apron"] = _matte("SFP_Apron", _srgb("918d86"), rough=0.92,
                                scale=0.7)
        _MATS["terrain"] = _matte("SFP_Terrain", _srgb("6e6f5c"), rough=0.95,
                                  scale=0.25)
        _MATS["asphalt"] = _matte("SFP_Asphalt", _srgb("4b4a47"), rough=0.86,
                                  scale=2.0)
    return _MATS


PANEL_SLOTS = ("anod", "ss", "mill", "epdm", "cavity")


# =============================================================================
# 14.  EMIT
# =============================================================================
def panel_matrix(P):
    """World matrix for a panel: elevation frame, position, installed tilt."""
    u, v, n = elev_axes(P.elev)
    R = Matrix(((u[0], v[0], n[0]), (u[1], v[1], n[1]), (u[2], v[2], n[2])))
    if P.elev == "C":
        origin = Vector((CLAD_X_E, CLAD_Y_S, 0.5 * (P.z_top + P.z_bot)))
    else:
        s_mid = 0.5 * (P.s0 + P.s1)
        wx, wy, wz = face_point(P.elev, s_mid, 0.5 * (P.z_top + P.z_bot))
        origin = Vector((wx, wy, wz))
    tilt = (Matrix.Rotation(P.tilt_v, 3, (0.0, 1.0, 0.0))
            @ Matrix.Rotation(P.tilt_u, 3, (1.0, 0.0, 0.0)))
    M = (Matrix.Translation(origin).to_4x4()
         @ (R @ tilt).to_4x4()
         @ Matrix.Translation(Vector((0.0, 0.0, P.off_n))).to_4x4())
    return M


def build_panel(P, q, coll, mats):
    V, F, Q, T, MQ, MT = cassette_mesh(P, q)
    # RECENTRE ON EMIT (law 6): the mesh is authored about its own centre so
    # TexCoord -> Object is a panel-local frame with 0.6 m of range, not a
    # 20 m building coordinate.
    ctr = 0.5 * (V.min(0) + V.max(0))
    if P.kind == KIND_CORNER:
        ctr[:] = 0.0
        ctr[1] = 0.5 * (V[:, 1].min() + V[:, 1].max())
    V = V - ctr
    attrs = panel_attrs(P, V, F, q)
    uv = np.stack([F["pp"], F["vv"] + P.face_h * 0.5], -1)
    me = make_mesh(LIBPFX + P.name[len(PFX):], V, Q, T, MQ, MT, attrs, uv)
    for k in PANEL_SLOTS:
        me.materials.append(mats[k])
    shade(me, 34.0)
    ob = bpy.data.objects.new(P.name, me)
    coll.objects.link(ob)
    M = panel_matrix(P)
    ob.matrix_world = M @ Matrix.Translation(Vector(ctr)).to_4x4()

    sm = ob.modifiers.new("skin", "SOLIDIFY")
    sm.thickness = SHEET_T
    sm.offset = -1.0
    # SIMPLE offset, not even.  Even offset divides by the vertex normal's
    # angle cosine and detonates wherever a cap meets its own apex; the folds
    # here are all radiused so simple offset is exact to a micron anyway.
    sm.use_even_offset = False
    sm.use_quality_normals = True
    sm.use_rim = True
    sm.thickness_clamp = 0.0
    # THE SKIN IS 3.0 mm AND THE STIFFENERS ARE 1.5.  Solidify scales its
    # thickness by a vertex group, so both live in one modifier rather than in
    # two objects -- which matters because the gate counts objects.
    vg = ob.vertex_groups.new(name="sheet_t")
    thin = np.asarray(F["thin"]) > 0.5
    idx = np.arange(len(V))
    vg.add(idx[~thin].tolist(), 1.0, "REPLACE")
    if thin.any():
        vg.add(idx[thin].tolist(), STIFF_T_FACTOR, "REPLACE")
    sm.vertex_group = "sheet_t"
    sm.thickness_vertex_group = 0.0     # factor at zero weight; all verts are
                                        # assigned, so this is only a backstop

    bv = ob.modifiers.new("arris", "BEVEL")
    bv.width = 0.00030
    bv.segments = 1
    bv.limit_method = "ANGLE"
    bv.angle_limit = math.radians(38.0)
    bv.harden_normals = False

    P.centre_world = tuple(float(c) for c in (M @ Vector((0.0, 0.0, 0.0))))
    P.matrix = M
    return ob


def emit_panels(q=None, seed=SEED, coll_name=COLL_NAME, only=None):
    q = q or quality_params("hero")
    mats = materials()
    root = _collection(coll_name)
    cp = _collection(coll_name + "_Panels", root)
    ps = panels(seed)
    if only is not None:
        ps = [p for p in ps if p.idx in only]
    obs = []
    for i, P in enumerate(ps):
        obs.append(build_panel(P, q, cp, mats))
        if (i + 1) % 30 == 0:
            print("   .. %d/%d panels" % (i + 1, len(ps)))
    return ps, obs


def quality_params(quality="hero"):
    q = dict(CELL_EDGE=CELL_EDGE, CELL_MID=CELL_MID, GRADE_BAND=GRADE_BAND,
             N_ARC1=N_ARC1, N_RET=N_RET, N_ARC2=N_ARC2, N_LIP=N_LIP,
             N_CORNER=N_CORNER)
    if quality == "draft":
        q.update(DRAFT)
    return q


# =============================================================================
# 15.  THE SUB-FRAME  --  what you see when you look INTO a 15 mm joint
# =============================================================================
def _box(acc, lo, hi, mat=0, skip=""):
    lo = np.asarray(lo, float)
    hi = np.asarray(hi, float)
    P = np.array([[lo[0], lo[1], lo[2]], [hi[0], lo[1], lo[2]],
                  [hi[0], hi[1], lo[2]], [lo[0], hi[1], lo[2]],
                  [lo[0], lo[1], hi[2]], [hi[0], lo[1], hi[2]],
                  [hi[0], hi[1], hi[2]], [lo[0], hi[1], hi[2]]])
    i0 = acc.add_block(P, 1.0, 0.0, 0.0, 0.0, 0.0)
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5),
         (2, 3, 7, 6), (3, 0, 4, 7)]
    tag = "zn zp yn xp yp xn".split()
    keep = [q for q, t in zip(f, tag) if t not in skip.split()]
    acc.quad(np.asarray(keep) + i0, mat)


def build_subframe(q, coll_name=COLL_NAME):
    """Carrier rails, helping-hand brackets, joint baffles, reveal cheeks, the
    head flashing, the end closures and the parapet upstand.

    None of it is the item.  All of it is why the joints are BLACK and 70 mm
    deep instead of a drawn line.

    EVERY ELEMENT HERE KNOWS HOW DEEP THE PANEL IN FRONT OF IT IS.  The first
    version did not: it put the rails and the baffles at a fixed 50-88 mm
    behind the nominal face, and the three RAINWATER COLUMNS are set back 90 mm,
    so a mill-finish carrier rail and a black EPDM baffle rendered IN FRONT OF
    the recessed cassettes -- a bright bar straight across the slot and a black
    plate where a panel should be.  It is in the fifth macro and it is the
    reason this function is now written per-panel.
    """
    mats = materials()
    root = _collection(coll_name)
    sc = _collection(coll_name + "_Sub", root)
    ps = panels()
    lv = course_levels()
    depth_at = {}
    for P in ps:
        if P.elev == "C":
            continue
        depth_at.setdefault(P.elev, {})[P.col] = (REVEAL_DEPTH if P.reveal else 0.0)

    def col_depth(elev, s_stn):
        best = 0.0
        for P in ps:
            if P.elev == elev and P.course == 0 and P.s0 - 0.02 <= s_stn <= P.s1 + 0.02:
                best = max(best, REVEAL_DEPTH if P.reveal else 0.0)
        return best

    def put(elev, s0, s1, z0, z1, back0, back1, mat_acc):
        """A box spanning [s0,s1] x [z0,z1], `back0..back1` behind the face."""
        if elev == "E":
            mat_acc.append(((CLAD_X_E - back1, CLAD_Y_S + s0, z0),
                            (CLAD_X_E - back0, CLAD_Y_S + s1, z1)))
        else:
            mat_acc.append(((CLAD_X_E - s1, CLAD_Y_S + back0, z0),
                            (CLAD_X_E - s0, CLAD_Y_S + back1, z1)))

    runs = {"E": (0.0, CLAD_Y_N - CLAD_Y_S), "S": (0.0, CLAD_X_E - CLAD_X_W)}

    # ---------- the sheathed cavity wall behind everything ------------------
    # THE TWO SHEETS MEET IN AN INTERNAL CORNER.  The first version ran the east
    # sheet from CLAD_Y_S - 0.152, i.e. 152 mm PAST the south cladding face, so
    # a 2 mm dark board stood proud of the building's own corner and rendered as
    # a 0.3 m brown bar straight down the sixth corner macro, in front of the
    # corner cassette this item exists to show.  Ray-cast and named, not guessed.
    acc = MeshAcc()
    _box(acc, (CLAD_X_E - 0.152, CLAD_Y_S + 0.152, CLAD_BOTTOM_Z - 0.30),
         (CLAD_X_E - 0.150, CLAD_Y_N, CLAD_TOP_Z - 0.060), 0)
    _box(acc, (CLAD_X_W, CLAD_Y_S + 0.150, CLAD_BOTTOM_Z - 0.30),
         (CLAD_X_E - 0.152, CLAD_Y_S + 0.152, CLAD_TOP_Z - 0.060), 0)
    # and a deeper pocket behind each rainwater slot
    for P in ps:
        if not P.reveal or P.course != 0:
            continue
        put_boxes = []
        put(P.elev, P.s0 - 0.02, P.s1 + 0.02, CLAD_BOTTOM_Z - 0.30,
            CLAD_TOP_Z - 0.060, 0.150 + REVEAL_DEPTH, 0.152 + REVEAL_DEPTH,
            put_boxes)
        for (lo, hi) in put_boxes:
            _box(acc, lo, hi, 0)
    V, F, Q, T, MQ, MT = acc.finish()
    me = make_mesh(SUBPFX + "Cavity", V, Q, T, MQ, MT)
    me.materials.append(mats["cavity"])
    sc.objects.link(bpy.data.objects.new(SUBPFX + "Cavity", me))

    # ---------- carrier rails and T-rails, per column -----------------------
    acc = MeshAcc()
    boxes = []
    for P in ps:
        if P.elev == "C":
            continue
        d = REVEAL_DEPTH if P.reveal else 0.0
        z = P.z_top - 0.055
        put(P.elev, P.s0 + 0.010, P.s1 - 0.010, z - 0.020, z + 0.020,
            0.070 + d, 0.088 + d, boxes)                      # horizontal carrier
        for s_j in (P.s0, P.s1):
            if P.course:
                continue
            put(P.elev, s_j - 0.028, s_j + 0.028, CLAD_BOTTOM_Z + 0.02,
                CLAD_TOP_Z - 0.075, 0.055 + d, 0.072 + d, boxes)   # T-rail
    for (lo, hi) in boxes:
        _box(acc, lo, hi, 0)
    V, F, Q, T, MQ, MT = acc.finish()
    me = make_mesh(SUBPFX + "Rails", V, Q, T, MQ, MT)
    me.materials.append(mats["mill"])
    shade(me, 34.0)
    sc.objects.link(bpy.data.objects.new(SUBPFX + "Rails", me))

    # ---------- helping-hand brackets ---------------------------------------
    acc = MeshAcc()
    boxes = []
    for elev, (a, bmax) in runs.items():
        for (zt, zb, hh) in lv:
            z = zt - 0.055
            for s_stn in np.arange(a + 0.42, bmax, 0.80):
                d = col_depth(elev, float(s_stn))
                put(elev, s_stn - 0.030, s_stn + 0.030, z - 0.055, z + 0.055,
                    0.088 + d, 0.150 + d, boxes)
    for (lo, hi) in boxes:
        _box(acc, lo, hi, 0)
    V, F, Q, T, MQ, MT = acc.finish()
    me = make_mesh(SUBPFX + "Brackets", V, Q, T, MQ, MT)
    me.materials.append(mats["galv"])
    sc.objects.link(bpy.data.objects.new(SUBPFX + "Brackets", me))

    # ---------- joint baffles ------------------------------------------------
    acc = MeshAcc()
    boxes = []
    for P in ps:
        if P.elev == "C":
            continue
        d = REVEAL_DEPTH if P.reveal else 0.0
        for s_j in (P.s0, P.s1):
            put(P.elev, s_j - 0.035, s_j + 0.035, P.z_bot, P.z_top,
                0.047 + d, 0.050 + d, boxes)
        put(P.elev, P.s0, P.s1, P.z_bot - 0.003, P.z_bot + 0.030,
            0.047 + d, 0.050 + d, boxes)
    for (lo, hi) in boxes:
        _box(acc, lo, hi, 0)
    V, F, Q, T, MQ, MT = acc.finish()
    me = make_mesh(SUBPFX + "Baffles", V, Q, T, MQ, MT)
    me.materials.append(mats["epdm"])
    sc.objects.link(bpy.data.objects.new(SUBPFX + "Baffles", me))

    # ---------- reveal cheeks, head flashing, end closures, upstand ---------
    acc = MeshAcc()
    boxes = []
    for P in ps:
        if not P.reveal:
            continue
        for s_j in (P.s0, P.s1):
            put(P.elev, s_j - 0.004, s_j + 0.004, P.z_bot - 0.01, P.z_top + 0.01,
                0.002, REVEAL_DEPTH + 0.006, boxes)
    # head flashing under the cut course, both runs
    put("E", -0.004, CLAD_Y_N - CLAD_Y_S, CLAD_BOTTOM_Z - 0.090,
        CLAD_BOTTOM_Z - 0.004, -0.004, 0.140, boxes)
    put("S", -0.004, CLAD_X_E - CLAD_X_W, CLAD_BOTTOM_Z - 0.090,
        CLAD_BOTTOM_Z - 0.004, -0.004, 0.140, boxes)
    # END CLOSURES.  The upper storey is set back 1.900 m on the north and the
    # west, so both runs stop against a return: a pressed closure that turns the
    # cladding line round the corner instead of leaving the cavity open.
    put("E", CLAD_Y_N - CLAD_Y_S - 0.004, CLAD_Y_N - CLAD_Y_S + 0.150,
        CLAD_BOTTOM_Z - 0.09, CLAD_TOP_Z + 0.004, -0.004, 0.160, boxes)
    put("S", CLAD_X_E - CLAD_X_W - 0.004, CLAD_X_E - CLAD_X_W + 0.150,
        CLAD_BOTTOM_Z - 0.09, CLAD_TOP_Z + 0.004, -0.004, 0.160, boxes)
    for (lo, hi) in boxes:
        _box(acc, lo, hi, 0)
    V, F, Q, T, MQ, MT = acc.finish()
    me = make_mesh(SUBPFX + "Flashings", V, Q, T, MQ, MT)
    me.materials.append(mats["mill"])
    shade(me, 34.0)
    sc.objects.link(bpy.data.objects.new(SUBPFX + "Flashings", me))

    # ---------- the parapet upstand, waiting for its coping -----------------
    acc = MeshAcc()
    _box(acc, (CLAD_X_E - 0.230, CLAD_Y_S - 0.001, CLAD_TOP_Z - 1.30),
         (CLAD_X_E - 0.152, CLAD_Y_N + 0.150, CLAD_TOP_Z), 0)
    _box(acc, (CLAD_X_W - 0.150, CLAD_Y_S + 0.152, CLAD_TOP_Z - 1.30),
         (CLAD_X_E, CLAD_Y_S + 0.230, CLAD_TOP_Z), 0)
    V, F, Q, T, MQ, MT = acc.finish()
    me = make_mesh(SUBPFX + "Upstand", V, Q, T, MQ, MT)
    me.materials.append(mats["upstand"])
    sc.objects.link(bpy.data.objects.new(SUBPFX + "Upstand", me))
    return sc


def build_context(coll_name=COLL_NAME):
    """Shell, glazing band, ground.  LIGHT ONLY -- bounce and occlusion.

    At a 12.47 deg sun almost everything that reaches the underside of a
    cassette has bounced off the forecourt first, so rendering this item over
    a void would be a different picture from the film's.
    """
    mats = materials()
    root = _collection(coll_name)
    cc = _collection(coll_name + "_Ctx", root)
    z0, _own = C.world_ground_z(float(CLAD_X_E + 6.0), float(CLAD_Y_S - 6.0))
    z0 = 0.0 if (z0 != z0) else float(z0)

    # WHAT A NEAR-SPECULAR FACADE REFLECTS IS WHAT IT LOOKS LIKE.  The first
    # three macros stood 180 panels over ONE flat grey plane under ONE flat sky,
    # so every panel mirrored the same featureless field and the roughness, the
    # metallic mask and the oil-canning were all invisible by construction.  In
    # the film this fascia looks down at four different surfaces at four
    # different distances, and it is those bands, and the horizon above them,
    # that draw the panels.  So the ground is built as the real programme:
    #
    #   0 - 40 m   the showroom forecourt          precast concrete   a ~0.30
    #   the ribbon  12.6 m of access road running east from the breach plane,
    #               |y| <= C.ACCESS_HALF_W          asphalt            a ~0.075
    #   40 - 95 m  the paddock apron               concrete           a ~0.24
    #   95 - 340 m the terrain beyond              olive grey         a ~0.13
    #
    # Every one of those is another module's item.  None of it carries the
    # SFP_Panel_ prefix, none of it is measured by the gate, and it is here for
    # exactly one reason: without it the item cannot be judged.
    def _slab(name, x0, x1, y0, y1, zz, mat):
        a2 = MeshAcc()
        i = a2.add_block(np.array([[x0, y0, zz], [x1, y0, zz],
                                   [x1, y1, zz], [x0, y1, zz]]), 1.0, 0, 0, 0, 0)
        a2.quad(np.array([[i, i + 1, i + 2, i + 3]]), 0)
        V2, F2, Q2, T2, MQ2, MT2 = a2.finish()
        m2 = make_mesh(CTXPFX + name, V2, Q2, T2, MQ2, MT2)
        m2.materials.append(mats[mat])
        o2 = bpy.data.objects.new(CTXPFX + name, m2)
        cc.objects.link(o2)

    # 12 km, not 340 m.  Blender's Sky Texture is BLACK below the horizon, so a
    # ground plane that ends inside the frame puts a black band under the
    # skyline -- which is exactly what the fifth corner macro showed, and it is
    # also what the panels were reflecting.
    _slab("GroundFar", CLAD_X_E - 6000.0, CLAD_X_E + 6000.0,
          CLAD_Y_S - 6000.0, CLAD_Y_S + 6000.0, z0 - 0.02, "terrain")
    _slab("GroundApron", CLAD_X_E - 95.0, CLAD_X_E + 95.0,
          CLAD_Y_S - 95.0, CLAD_Y_S + 95.0, z0 - 0.01, "apron")
    _slab("GroundForecourt", CLAD_X_E - 42.0, CLAD_X_E + 40.0,
          CLAD_Y_S - 40.0, CLAD_Y_S + 42.0, z0, "ground")
    _slab("GroundRibbon", GLASS_X, GLASS_X + 92.0,
          -C.ACCESS_HALF_W, C.ACCESS_HALF_W, z0 + 0.001, "asphalt")

    acc = MeshAcc()
    # the shell below the cladding: the glazing band, dark
    _box(acc, (GLASS_X - 0.06, GLASS_Y_S, 0.110), (GLASS_X, 11.0, GLASS_HEAD_Z), 0)
    _box(acc, (-14.962, GLASS_Y_S - 0.001, 0.110), (14.962, GLASS_Y_S + 0.06,
                                                    GLASS_HEAD_Z), 0)
    V, F, Q, T, MQ, MT = acc.finish()
    me = make_mesh(CTXPFX + "Glazing", V, Q, T, MQ, MT)
    me.materials.append(mats["glass"])
    ob = bpy.data.objects.new(CTXPFX + "Glazing", me)
    cc.objects.link(ob)

    acc = MeshAcc()
    # curtain wall head band, and the shell mass behind everything
    _box(acc, (GLASS_X - 0.16, GLASS_Y_S - 0.001, GLASS_HEAD_Z),
         (GLASS_X, 11.10, HEAD_TOP_Z), 0)
    _box(acc, (-15.10, GLASS_Y_S - 0.001, GLASS_HEAD_Z),
         (15.0, GLASS_Y_S + 0.16, HEAD_TOP_Z), 0)
    # THE SHELL IS TWO MASSES, not one box.  Below the curtain-wall head it is
    # the round-1 pavilion to its measured plan; above it, the round-2 upper
    # storey, SET BACK UPPER_SETBACK = 1.900 m on the north and the west.  The
    # first version carried the full footprint all the way to the parapet, so
    # the fascia stopped at y = 9.350 and 1.9 m of bare shell carried on past
    # it -- the building contradicting its own set-out in the frame.
    _box(acc, (R1_SHELL[0], R1_SHELL[2], 0.0),
         (CLAD_X_E - 0.16, R1_SHELL[3], HEAD_TOP_Z), 0)
    _box(acc, (CLAD_X_W - 0.152, CLAD_Y_S + 0.152, HEAD_TOP_Z),
         (CLAD_X_E - 0.152, CLAD_Y_N + 0.150, CLAD_TOP_Z), 0)
    V, F, Q, T, MQ, MT = acc.finish()
    me = make_mesh(CTXPFX + "Shell", V, Q, T, MQ, MT)
    me.materials.append(mats["conc"])
    ob = bpy.data.objects.new(CTXPFX + "Shell", me)
    cc.objects.link(ob)
    return cc


# =============================================================================
# 16.  THE DEPENDANT-FACING QUERIES
# =============================================================================
def clad_top_edge_z(elev, s, ps=None):
    """AS-BUILT top edge z at a station.  Not 10.340 everywhere."""
    ps = ps if ps is not None else panels()
    best, bz = None, CLAD_TOP_Z
    for P in ps:
        if P.course != 0 or P.elev != elev:
            continue
        if P.s0 - 0.02 <= s <= P.s1 + 0.02:
            t = (s - P.s0) / max(P.s1 - P.s0, 1e-9) - 0.5
            bz = P.z_top + P.off_n * 0.0 + math.tan(P.tilt_u) * 0.0 \
                + (P.face_h - (P.h - JOINT_M)) * 0.5 \
                + math.sin(P.tilt_v) * t * (P.s1 - P.s0)
            best = P
            break
    return float(bz)


def sign_fix_grid(ps=None):
    """Permitted signage stud positions: a 100 mm grid inside SIGN_ZONE that
    misses every joint by >= 40 mm and lands on a panel with a backing plate."""
    ps = ps if ps is not None else panels()
    out = []
    zs0 = SIGN_ZONE["s0"] - CLAD_Y_S
    zs1 = SIGN_ZONE["s1"] - CLAD_Y_S
    for P in ps:
        if not P.sign:
            continue
        s = P.s0 + 0.10
        while s <= P.s1 - 0.10:
            if min(abs(s - P.s0), abs(s - P.s1)) >= 0.040 and zs0 <= s <= zs1:
                z = P.z_bot + 0.12
                while z <= P.z_top - 0.12:
                    x, y, zz = face_point(P.elev, s, z)
                    out.append((round(x, 4), round(y, 4), round(zz, 4), P.name))
                    z += 0.100
            s += 0.100
    return out


def rwp_bracket_points(ps=None):
    """Where a rainwater downpipe bracket may fix: on the carrier rails."""
    ps = ps if ps is not None else panels()
    out = []
    for (elev, s, dia) in _rwp_stations():
        for (zt, zb, hh) in course_levels():
            z = zt - 0.055
            x, y, zz = face_point(elev, s, z)
            if elev == "E":
                x -= REVEAL_DEPTH
            else:
                y += REVEAL_DEPTH
            out.append((round(x, 4), round(y, 4), round(zz, 4), elev))
    return out


def RWP_LINES(ps=None):
    ps = ps if ps is not None else panels()
    out = []
    for (elev, s, dia) in _rwp_stations():
        names = [p.name for p in ps if p.elev == elev and p.reveal
                 and p.s0 <= s <= p.s1]
        x, y, z = face_point(elev, s, HOPPER_Z)
        out.append(dict(elev=elev, s=round(s, 4), dia=dia,
                        reveal_depth=REVEAL_DEPTH,
                        hopper=[round(x, 4), round(y, 4), round(HOPPER_Z, 4)],
                        panels=names))
    return out


# =============================================================================
# 17.  TEST SCENE  --  contract sun, contract sky, the manifest's own camera
# =============================================================================
def apply_contract_sky():
    n = 0
    for w in bpy.data.worlds:
        if not w.use_nodes:
            continue
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
    return n


def contract_sun(scene):
    import fix_audit_blend as FAB
    FAB.procedural_world()
    apply_contract_sky()
    lt = bpy.data.lights.new(SUBPFX + "Sun", "SUN")
    lt.energy = C.SUN_ENERGY
    lt.color = C.SUN_COLOR
    lt.angle = math.radians(C.SUN_ANGULAR_DIAM_DEG)
    ob = bpy.data.objects.new(SUBPFX + "Sun", lt)
    d = Vector(C.SUN_DIR).normalized()
    ob.rotation_mode = "QUATERNION"
    ob.rotation_quaternion = Vector((0.0, 0.0, 1.0)).rotation_difference(d)
    scene.collection.objects.link(ob)
    print(">> sun: elev %.5f deg bearing %.5f deg energy %.3f shadow ratio %.4f"
          % (C.SUN_ELEV_DEG, C.SUN_BEARING_DEG, C.SUN_ENERGY, C.SUN_SHADOW_RATIO))
    for _e in ("E", "S"):
        print(">>   a 3.0 mm proud edge on the %s face throws %.1f mm = %.1f px "
              "of shadow (ratio %.3f, NOT the ground's %.3f)"
              % (_e, 3.0 * SHADOW_RATIO[_e], shadow_px(0.003, _e),
                 SHADOW_RATIO[_e], C.SUN_SHADOW_RATIO))
    return ob


# The macro view.  The camera is EXACTLY NEAREST_CAMERA_M from the nearest
# built vertex (solved, then measured).  The azimuth is chosen 96 deg off the
# sun bearing so the light RAKES the face: with the key over the right shoulder
# of the frame every joint, every fold and every oil-can wave is drawn in light
# and shade, which is the whole point of filming a metal facade at 12.5 deg.
#
# WHERE ALONG THE FACADE.  Station 15.60 on the east run puts the RAINWATER
# REVEAL (column 13, s 15.34-16.44) just right of frame centre: a whole panel
# column set back 90 mm behind its neighbours, with the two 100 mm return
# cheeks that form the slot.  It is the one place on this elevation where the
# fascia has depth in plan, so it is the one place where the raking sun makes
# the item cast a shadow ON ITSELF, and a facade that cannot do that is a
# picture of a wall.  The first four macros were shot on plain field panels and
# every one of them was a flat grid.
MACRO_TARGET = ("E", 15.60, 8.360)      # (elevation, station s, z)
MACRO_AZ_DEG = 34.0                     # camera bearing from the face normal
MACRO_EL_DEG = 7.5                      # camera ABOVE the target, looking down
# WHY THE CAMERA IS ABOVE THE PANELS AND NOT BELOW THEM.  The first macro was
# shot from 16 deg below, which is the Beat-4 sightline -- and every reflected
# ray off a vertical wall then goes UP, so all 180 panels mirrored one blank
# patch of sky and the frame came back at mean 0.847 with the highlights flat.
# A near-specular surface is read by WHAT IT REFLECTS.  From 7.5 deg above, the
# horizon lands about a third of the way down the frame, and the oil-canning --
# the whole point of the item -- draws itself by bending that line panel by
# panel.  The distance is still the manifest's 3.6 m, measured, and Beat 4's
# camera passes through this height on its way up.


def macro_camera(scene, ps, name="CAM_SFP_Macro"):
    tx, ty, tz = face_point(MACRO_TARGET[0], MACRO_TARGET[1], MACRO_TARGET[2])
    tgt = Vector((tx, ty, tz))
    az = math.radians(MACRO_AZ_DEG)
    el = math.radians(MACRO_EL_DEG)
    # the face normal for 'E' is +x; rotate az about z, then pitch by el
    d = Vector((math.cos(el) * math.cos(az), math.cos(el) * math.sin(az),
                math.sin(el)))
    cd = bpy.data.cameras.new(name)
    cd.lens = LENS_AT_CLOSEST_MM
    cd.sensor_width = SENSOR_MM
    cd.clip_start = 0.01
    cd.clip_end = 400.0
    cam = bpy.data.objects.new(name, cd)
    scene.collection.objects.link(cam)

    def place(dist):
        p = tgt + d * dist
        fwd = (tgt - p).normalized()
        right = fwd.cross(Vector((0.0, 0.0, 1.0)))
        if right.length < 1e-6:
            right = Vector((1.0, 0.0, 0.0))
        right.normalize()
        up = right.cross(fwd).normalized()
        M = Matrix((right, up, -fwd)).transposed().to_4x4()
        cam.matrix_world = Matrix.Translation(p) @ M
        return p

    # solve so the NEAREST built panel vertex is exactly NEAREST_CAMERA_M
    lo, hi = NEAREST_CAMERA_M, NEAREST_CAMERA_M + 6.0
    place(hi)
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        place(mid)
        dmin = measure_nearest(cam, quiet=True)
        if dmin > NEAREST_CAMERA_M:
            hi = mid
        else:
            lo = mid
        if abs(dmin - NEAREST_CAMERA_M) < 0.0004:
            break
    scene.camera = cam
    hh = math.degrees(math.atan(0.5 * SENSOR_MM / LENS_AT_CLOSEST_MM))
    print(">> camera: %.0f mm, azimuth %.1f deg off the face normal (%.1f deg "
          "off the sun bearing), pitch %+.1f deg"
          % (LENS_AT_CLOSEST_MM, MACRO_AZ_DEG,
             abs(((MACRO_AZ_DEG - C.SUN_BEARING_DEG + 180) % 360) - 180), MACRO_EL_DEG))
    print(">>   frame at %.3f m is %.3f x %.3f m; %.1f px/m; 1 px = %.4f mm"
          % (NEAREST_CAMERA_M,
             2 * NEAREST_CAMERA_M * math.tan(math.radians(hh)),
             2 * NEAREST_CAMERA_M * math.tan(math.radians(hh)) * RES_Y_4K / RES_X_4K,
             PX_PER_M, MM_PER_PX))
    return cam


def extra_camera(scene, name, elev, s_stn, z, az_deg, el_deg,
                 dist=NEAREST_CAMERA_M, lens=LENS_AT_CLOSEST_MM):
    """Another view at the SAME distance and lens.  Not the deliverable, but the
    macro is one frame and this item is 48.6 m of facade with a folded corner in
    it; one frame cannot be the whole inspection."""
    tx, ty, tz = face_point(elev, s_stn, z)
    tgt = Vector((tx, ty, tz))
    nx, ny = ((1.0, 0.0) if elev == "E" else (0.0, -1.0))
    base = math.atan2(ny, nx)
    az = base + math.radians(az_deg)
    el = math.radians(el_deg)
    d = Vector((math.cos(el) * math.cos(az), math.cos(el) * math.sin(az),
                math.sin(el)))
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = SENSOR_MM
    cd.clip_start = 0.01
    cd.clip_end = 400.0
    cam = bpy.data.objects.new(name, cd)
    scene.collection.objects.link(cam)

    def place(dd):
        p = tgt + d * dd
        fwd = (tgt - p).normalized()
        right = fwd.cross(Vector((0.0, 0.0, 1.0)))
        if right.length < 1e-6:
            right = Vector((1.0, 0.0, 0.0))
        right.normalize()
        up = right.cross(fwd).normalized()
        cam.matrix_world = (Matrix.Translation(p)
                            @ Matrix((right, up, -fwd)).transposed().to_4x4())

    lo, hi = dist, dist + 8.0
    place(hi)
    for _ in range(44):
        mid = 0.5 * (lo + hi)
        place(mid)
        dmin = measure_nearest(cam, quiet=True)
        if dmin > dist:
            hi = mid
        else:
            lo = mid
        if abs(dmin - dist) < 0.0004:
            break
    print(">> %s: nearest panel vertex %.4f m (target %.3f m)"
          % (name, measure_nearest(cam, quiet=True), dist))
    return cam


def measure_nearest(cam, quiet=False):
    """Distance from the lens to the nearest SFP_Panel_ vertex ACTUALLY BUILT."""
    deps = bpy.context.evaluated_depsgraph_get()
    cp = np.array(cam.matrix_world.translation)
    best, who = 1e9, ""
    for ob in bpy.context.scene.objects:
        if ob.type != "MESH" or not ob.name.startswith(PFX):
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
    if not quiet:
        print(">> nearest %s vertex to the lens: %.4f m (%s) -- manifest %.3f m"
              % (PFX, best, who, NEAREST_CAMERA_M))
    return best


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


def build(quality="hero", seed=SEED, coll_name=COLL_NAME, subframe=True,
          context=True):
    q = quality_params(quality)
    ps, obs = emit_panels(q, seed, coll_name)
    if subframe:
        build_subframe(q, coll_name)
    if context:
        build_context(coll_name)
    return dict(item=ITEM, quality=quality, seed=seed, panels=len(ps),
                objects=len(obs))


def build_test_scene(quality="hero", out=None, seed=SEED):
    scene = bpy.context.scene
    _clear()
    st = build(quality=quality, seed=seed)
    ps = panels(seed)
    contract_sun(scene)
    cam = macro_camera(scene, ps)
    st["camera_nearest_m"] = round(measure_nearest(cam), 4)
    # THE CORNER.  A folded corner cassette, the bottom (cut) course and its
    # 45 mm drip, seen from below the way Beat 4 actually meets this building.
    extra_camera(scene, "CAM_SFP_Corner", "E", 0.62, 7.10, -52.0, -9.0)
    # THE CLOSERS.  Face-fixed panels with domed rivets at 300 mm centres, at
    # the north end of the east run where the set-out closes out.
    extra_camera(scene, "CAM_SFP_Closer", "E", 19.85, 9.60, 30.0, 4.0)
    scene.camera = cam
    scene.render.engine = "CYCLES"
    scene.render.resolution_x = RES_X_4K
    scene.render.resolution_y = RES_Y_4K
    scene.render.film_transparent = False
    scene.view_settings.view_transform = C.VIEW_TRANSFORM
    scene.view_settings.look = C.VIEW_LOOK
    scene.view_settings.exposure = C.REFERENCE_EXPOSURE_EXTERIOR
    try:
        scene.cycles.max_bounces = 10
        scene.cycles.diffuse_bounces = 4
        scene.cycles.glossy_bounces = 6
        scene.cycles.transmission_bounces = 4
        scene.cycles.use_adaptive_sampling = True
        scene.cycles.adaptive_threshold = 0.004
        scene.cycles.use_denoising = True
    except Exception as e:
        print("   (cycles settings: %s)" % e)
    if out:
        _save(out)
        st["blend"] = out
        st["blend_mb"] = round(os.path.getsize(out) / 1048576.0, 1)
        print(">> saved %s (%.1f MB)" % (out, st["blend_mb"]))
    return st


# =============================================================================
# 18.  SELF-MEASUREMENT
# =============================================================================
def verify(seed=SEED, out=None):
    """Measure the ARTEFACT.  Every number is a physical quantity (R2-017)."""
    deps = bpy.context.evaluated_depsgraph_get()
    rep = dict(item=ITEM, seed=seed)
    obs = [o for o in bpy.context.scene.objects
           if o.type == "MESH" and o.name.startswith(PFX)]
    rep["panel_objects"] = len(obs)
    rep["declared_instances"] = DECLARED_INSTANCES

    tris = 0
    verts = 0
    lens = []
    xs = []
    zs = []
    for ob in obs:
        oe = ob.evaluated_get(deps)
        me = oe.to_mesh()
        if me is None:
            continue
        verts += len(me.vertices)
        for p in me.polygons:
            tris += max(len(p.vertices) - 2, 1)
        co = np.empty(len(me.vertices) * 3, np.float32)
        me.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        M = np.array(ob.matrix_world.to_4x4())
        w = co @ M[:3, :3].T + M[:3, 3]
        xs.append(w[:, 0])
        zs.append(w[:, 2])
        ev = np.empty(len(me.edges) * 2, np.int32)
        me.edges.foreach_get("vertices", ev)
        ev = ev.reshape(-1, 2)
        d = np.linalg.norm(co[ev[:, 0]] - co[ev[:, 1]], axis=1)
        lens.append(d)
        oe.to_mesh_clear()
    lens = np.concatenate(lens) if lens else np.zeros(1)
    xs = np.concatenate(xs) if xs else np.zeros(1)
    zs = np.concatenate(zs) if zs else np.zeros(1)
    rep["triangles"] = int(tris)
    rep["vertices"] = int(verts)
    rep["triangles_per_panel"] = round(tris / max(len(obs), 1), 1)
    rep["edge_p10_mm"] = round(float(np.percentile(lens, 10)) * 1000, 3)
    rep["edge_p50_mm"] = round(float(np.percentile(lens, 50)) * 1000, 3)
    rep["edge_p10_px"] = round(float(np.percentile(lens, 10)) * PX_PER_M, 2)
    rep["edge_p50_px"] = round(float(np.percentile(lens, 50)) * PX_PER_M, 2)

    # --- the contract check: NOTHING of mine crosses the breach plane -------
    rep["max_built_x"] = round(float(xs.max()), 5)
    rep["breach_plane_x"] = GLASS_X
    rep["clears_breach_plane"] = bool(xs.max() <= GLASS_X - 1e-6)
    rep["built_z_top"] = round(float(zs.max()), 5)
    rep["built_z_bottom"] = round(float(zs.min()), 5)
    rep["z_clear_of_parapet_top"] = bool(zs.max() <= PARAPET_TOP_Z + 1e-6)

    # --- measured JOINT WIDTHS between built neighbours ----------------------
    ps = panels(seed)
    gaps = []
    by = {}
    for P in ps:
        by.setdefault((P.elev, P.course), []).append(P)
    for key, group in by.items():
        group.sort(key=lambda p: p.s0)
        for a, b in zip(group[:-1], group[1:]):
            nominal = b.s0 - a.s1
            g = nominal + (a.w - JOINT_M - a.face_w) * 0.5 \
                + (b.w - JOINT_M - b.face_w) * 0.5 + JOINT_M
            gaps.append(g)
    gaps = np.asarray(gaps) if gaps else np.zeros(1)
    rep["joint_mm_min"] = round(float(gaps.min()) * 1000, 2)
    rep["joint_mm_max"] = round(float(gaps.max()) * 1000, 2)
    rep["joint_mm_mean"] = round(float(gaps.mean()) * 1000, 2)
    rep["joint_px_mean"] = round(float(gaps.mean()) * PX_PER_M, 2)

    # --- the three declared variation axes, MEASURED -------------------------
    sev = np.array([p.sev for p in ps])
    rep["oilcan_mm_p50"] = round(float(np.percentile(sev, 50)) * 1000, 3)
    rep["oilcan_mm_p95"] = round(float(np.percentile(sev, 95)) * 1000, 3)
    rep["oilcan_mm_max"] = round(float(sev.max()) * 1000, 3)
    rep["distinct_batches"] = len(set(p.batch for p in ps))
    from collections import Counter
    bc = Counter(p.batch for p in ps)
    rep["batch_population"] = dict(sorted(bc.items()))
    rep["batch_top_share"] = round(bc.most_common(1)[0][1] / len(ps), 4)
    rep["grain_crosswise_panels"] = sum(1 for p in ps if p.grain == 1)
    rep["flipped_panels"] = sum(1 for p in ps if p.gflip == 1)
    tilt = np.array([math.degrees(abs(p.tilt_u)) + math.degrees(abs(p.tilt_v))
                     for p in ps])
    rep["installed_tilt_deg_max"] = round(float(tilt.max()), 4)
    rep["kinds"] = dict(sorted(Counter(p.kind for p in ps).items()))
    rep["dented_panels"] = sum(1 for p in ps if p.dents)
    rep["dents_total"] = sum(len(p.dents) for p in ps)
    rep["face_fixed_panels"] = sum(1 for p in ps if p.rivets)
    rep["distinct_face_widths"] = len(set(round(p.face_w, 4) for p in ps))

    # --- per-object spread, the way the gate measures it ---------------------
    dims = []
    tri_by = []
    for ob in obs:
        oe = ob.evaluated_get(deps)
        me = oe.to_mesh()
        if me is None or not len(me.vertices):
            continue
        co = np.empty(len(me.vertices) * 3, np.float32)
        me.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        d = co.max(0) - co.min(0)
        dims.append(float(np.linalg.norm(d)))
        tri_by.append(sum(max(len(p.vertices) - 2, 1) for p in me.polygons))
        oe.to_mesh_clear()
    dims = np.asarray(dims)
    rep["cv_size"] = round(float(dims.std() / max(dims.mean(), 1e-9)), 5)
    rep["distinct_topologies"] = len(set(tri_by))

    # --- image-texture cleanliness ------------------------------------------
    imgs = [i.filepath for i in bpy.data.images if i.source == "FILE"]
    tex = 0
    for m in bpy.data.materials:
        if not m.use_nodes:
            continue
        tex += sum(1 for n in m.node_tree.nodes if n.type == "TEX_IMAGE")
    rep["external_image_files"] = imgs
    rep["image_texture_nodes"] = tex

    print(">> verify: %s" % json.dumps(rep, indent=1)[:4000])
    if out:
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        json.dump(rep, open(out, "w"), indent=1)
    return rep


def dump_interface(out, seed=SEED):
    ps = panels(seed)
    d = dict(
        item=ITEM, seed=seed, generated_by=os.path.basename(__file__),
        frame="WORLD metres; z = 0.000 is C.APRON_Z",
        px_per_m_at_3p6m=round(PX_PER_M, 2),
        planes=dict(clad_x_e=CLAD_X_E, clad_y_s=CLAD_Y_S, clad_y_n=CLAD_Y_N,
                    clad_x_w=CLAD_X_W, face_setback=FACE_SETBACK,
                    upper_setback=UPPER_SETBACK,
                    breach_plane_x=GLASS_X, glass_y_s=GLASS_Y_S,
                    clad_top_z=CLAD_TOP_Z, clad_bottom_z=CLAD_BOTTOM_Z,
                    parapet_top_z=PARAPET_TOP_Z,
                    coping_bearing_z=COPING_BEARING_Z,
                    coping_overhang_m=COPING_OVERHANG_M,
                    head_top_z=HEAD_TOP_Z, glass_head_z=GLASS_HEAD_Z),
        # MEASURED over all 180 evaluated meshes, not derived.  The nominal
        # planes above are a SET-OUT; these are the surface a dependant meets.
        as_built=dict(max_x=14.955, min_y=-10.95447,
                      max_z=10.33519, min_z=6.34474,
                      face_proud_max=dict(FACE_PROUD_MAX),
                      top_edge_below_nominal=TOP_EDGE_BELOW_NOMINAL,
                      breach_clearance_m=BREACH_CLEARANCE_M,
                      crosses_breach_plane=False,
                      measured_by="work/sfp/envelope.py"),
        setout=dict(module_m=MODULE_M, mullion_pitch=MULLION_PITCH,
                    joint_m=JOINT_M, courses=[list(c) for c in course_levels()],
                    corner_leg_e=CORNER_LEG_E, corner_leg_s=CORNER_LEG_S,
                    panels_per_course=len(ps) // len(COURSE_H),
                    total_panels=len(ps)),
        fabrication=dict(sheet_t=SHEET_T, fold_r_out=list(FOLD_R_OUT),
                         return_d=list(RETURN_D), lip_r2=LIP_R2, lip_l=LIP_L,
                         drip_return_d=DRIP_RETURN_D, drip_r2=DRIP_R2,
                         reveal_depth=REVEAL_DEPTH,
                         reveal_return_d=REVEAL_RETURN_D,
                         rivet_r_flange=RIVET_R_FLANGE, rivet_h=RIVET_H),
        sign=dict(zone=SIGN_ZONE, shelter_m=SIGN_SHELTER_M,
                  fix_points=sign_fix_grid(ps)),
        rainwater=dict(lines=RWP_LINES(ps), hopper_z=HOPPER_Z,
                       bracket_points=rwp_bracket_points(ps)),
        attrs=list(ATTRS),
        how_to_use=dict(
            coping="sit on COPING_BEARING_Z but read clad_top_edge_z(elev, s): "
                   "the as-built top edge moves +-2.4 mm and a coping laid to a "
                   "flat 10.340 will rock",
            signage="use sign_fix_grid(); every point misses a joint by >= 40 mm "
                    "and lands on a panel with a bonded backing plate",
            standoff="DO NOT MOUNT FLUSH TO clad_x_e / clad_y_s. Those are the "
                     "SET-OUT planes; the as-built face runs up to "
                     "face_clearance(elev) = 15.0 mm proud of them on the east "
                     "(14.5 south, 3.6 on the corner) once fabrication offset, "
                     "installed tilt and oil-canning are added. Stand off by "
                     "as_built.face_proud_max, or query the panel you land on.",
            rainwater="the pipe runs in a RECESSED COLUMN already built; fix to "
                      "rwp_bracket_points(), which are on the carrier rails, "
                      "never into a cassette",
            material="mat_anodised() reads 15 vertex attributes; call "
                     "bake_panel_attrs() on anything emitted into it"),
        panels=[p.as_dict() for p in ps])
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    json.dump(d, open(out, "w"))
    print(">> interface: %s (%d panels, %.1f kB)"
          % (out, len(ps), os.path.getsize(out) / 1024.0))
    return d


def report_setout():
    ps = panels()
    lv = course_levels()
    print(">> %s: %d panels, %d per course over %d courses"
          % (ITEM, len(ps), len(ps) // len(lv), len(lv)))
    print(">>   east run  %.3f m (y %.3f .. %.3f)   south run  %.3f m (x %.3f .. %.3f)"
          % (CLAD_Y_N - CLAD_Y_S, CLAD_Y_S, CLAD_Y_N,
             CLAD_X_E - CLAD_X_W, CLAD_X_W, CLAD_X_E))
    for (zt, zb, hh) in lv:
        print(">>   course  %.3f -> %.3f  (%.3f m)" % (zt, zb, hh))
    from collections import Counter
    print(">>   kinds: %s" % dict(Counter(p.kind for p in ps)))
    print(">>   widths: %s" % sorted(set(round(p.w, 3) for p in ps)))
    print(">>   px/m at %.1f m on a %.0f mm lens = %.1f  (1 px = %.4f mm)"
          % (NEAREST_CAMERA_M, LENS_AT_CLOSEST_MM, PX_PER_M, MM_PER_PX))
    return ps


def measure_scene():
    deps = bpy.context.evaluated_depsgraph_get()
    tris = 0
    for ob in bpy.context.scene.objects:
        if ob.type != "MESH":
            continue
        oe = ob.evaluated_get(deps)
        me = oe.to_mesh()
        if me is None:
            continue
        for p in me.polygons:
            tris += max(len(p.vertices) - 2, 1)
        oe.to_mesh_clear()
    print(">> scene triangles (everything): %d" % tris)
    return tris


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="test",
                    choices=("test", "build", "verify", "interface", "setout"))
    ap.add_argument("--out", default=None)
    ap.add_argument("--quality", default="hero")
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--report", default=None)
    argv = sys.argv
    if "--" in argv:
        args = argv[argv.index("--") + 1:]
    elif not HAVE_BPY:
        args = argv[1:]                 # plain `python3 showroom_facade_panel.py`
    else:
        args = []
    a = ap.parse_args(args)
    if a.mode == "setout":
        report_setout()
        return
    if a.mode == "interface":
        dump_interface(a.out or os.path.join(
            _HERE, "showroom_facade_panel_interface.json"), a.seed)
        return
    if a.mode == "verify":
        verify(a.seed, a.report)
        return
    if a.mode == "build":
        st = build(quality=a.quality, seed=a.seed)
    else:
        st = build_test_scene(a.quality, a.out, a.seed)
        st["scene_triangles"] = measure_scene()
        st["verify"] = verify(a.seed)
        dump_interface(os.path.join(_HERE,
                                    "showroom_facade_panel_interface.json"),
                       a.seed)
    if a.report:
        os.makedirs(os.path.dirname(os.path.abspath(a.report)), exist_ok=True)
        json.dump(st, open(a.report, "w"), indent=1)


if __name__ == "__main__":
    main()
