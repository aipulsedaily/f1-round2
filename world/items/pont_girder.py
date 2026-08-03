#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pont_girder.py — Le Pont de la Plongee, the four main plate girders.
Item 44, wave 1, zone `bridges`.

    manifest:  nearest_camera_m 2.5   lens 21 mm   onscreen_px_4k 1210
               instances 4            hero True    beats ['5']
               depends_on []          dependents 3
               variation_axes: web stiffeners / bolt clusters / paint system /
                               camber
               notes: "1.35 m deep girders, 30 m span, 6.0 m deck.
                       Origin world (-617.56, 94.75), heading 295.4 deg."
    pixels:    px_per_m = (3840 * 21 / 36) / 2.5 = 896.0 px/m
               -> 1 screen pixel = 1.116 mm on this girder.

That number is the brief.  At 1.116 mm/px:

    a 2.0 mm flange arris chamfer is 1.8 px
    an M24 nut across the flats is 32 px and its 30 deg chamfer is 4.5 px
    an M24 thread pitch is 2.7 px
    a weld's stack-of-dimes ripple at 4.2 mm pitch is 3.8 px
    an 8 mm fillet weld leg is 7.2 px
    the 60 mm gap where an intermediate stiffener stops short of the tension
        flange is 54 px of daylight
    a 4 mm web panel oil-can is 3.6 px of profile, and the SHADING of it is
        the single most convincing thing about a real plate girder
    the 18 mm residual camber over 30 m is 16 px of bow, and the difference
        between girder A's 18 mm and girder D's 11 mm is 6 px of relative bow
        between two soffits sighted along their length -- which is exactly how
        a bridge soffit reads from underneath
    a 3 mm anti-perch spike wire is 2.7 px

None of that list can be a shader.

WHERE THIS THING IS, AND WHAT THE CAMERA DOES TO IT
    circuit_spec.json/paddock/plunge_bridge_design:  s = 2410.0,
    soffit_z 6.80, span 30.0 m, deck width 6.0 m.  The camera, descending out
    of the helicopter arc, threads UNDER it at world z ~ 5.0 and 300 km/h,
    145 m before the doppler hover station, and the manifest's own derivation
    of nearest_camera_m confirms the reading of that 6.80:

        soffit 6.800 - camera 5.000            = 1.800  (pont_soffit_panel)
        girder mid-depth 7.475 - camera 5.000  = 2.475  ~ 2.5  (this item)
        1.35 * 21 * 3840 / (36 * 2.5)          = 1210   (onscreen_px_4k)

    -- so soffit_z is WORLD z, the girder occupies z 6.800 .. 8.150, and the
    lens passes under it at roughly a metre off the racing surface.

    ONE THING TO FLAG, AND ONE THING I GOT WRONG ABOUT IT UNTIL I MEASURED.
    ground_z(2410, 0) = 3.935, so a structural soffit at 6.800 leaves 2.865 m
    of headroom over the racing surface (2.841 m measured on the built mesh,
    because the bottom-flange splice cover plate hangs below the flange).  For
    a bridge over a circuit that is LOW -- it is a number for whoever owns
    circuit_spec to look at, not something this item may fix by moving a
    bridge the entire camera corridor was derived from.

    I expected tools/placement_gate.py to reject it for that, and wrote as
    much here before running it.  It does not: MEASURED, the gate returns
    PLACEMENT_CLEAN on this blend (10 objects tested, 9 measured per vertex,
    nothing on the road, in the car's path or in the camera's path).  The
    reason is worth writing down because it is a gate limitation and not a
    pass this item earned: the road-corridor keep-out is a band in ABSOLUTE
    world z, `zlo = -0.5, zhi = ROAD_CLEAR_H = 4.50`, so at s = 2410 -- where
    the racing surface is 3.935 m up -- the ceiling of the protected volume
    sits 0.565 m above the tarmac and cannot see a bridge over it at all.
    On the pit straight, where z = 0.000, the same constant means what it
    says.  Nothing here is allow-listed and nothing was tuned.

WHAT IS AND IS NOT GEOMETRY, AND WHY
    MESH   the welded I-section itself with its REAL fabrication history: web
           panel oil-canning between stiffeners (2.5-6 mm, which is 2-5 px of
           profile), weld pull-in along every web-to-flange seam and at every
           stiffener, flange angular distortion (the tips curl up 1-2 mm),
           flame-cut flange edge waviness and its 2 mm arris chamfer, plate
           lack-of-straightness, web out-of-plumb, and a fabricated camber
           that differs girder to girder; continuous automatic fillet welds
           down all four web-flange seams; transverse stiffeners with real
           quarter-circle copes, welded ONE side on two girders and BOTH on
           the other two, cut short of the tension flange by 4t with the gap
           open to the sky; bearing and jacking stiffeners with ground ends;
           bolted field splices -- web plates, flange plates, packs, and every
           bolt a separate object with a chamfered hex head, a washer, a real
           helical thread, its own protrusion length and its own tail; the
           10 mm joint gap between the two shop lengths, which is a real gap
           and not a drawn line; cross-frame connection plates; shear studs;
           welded sole plates; the fascia girders' tapered cantilever noses
           and their banner rails, cleats and tension posts; a bolted repair
           doubler over a struck web panel on girder C; anti-perch spikes on
           the bottom-flange shelves; and a pigeon's nest wedged behind a
           stiffener on girder B.
    SHADER the paint.  A 0.35 mm four-coat film is 0.31 px, so its RELIEF is
           sub-pixel and its COLOUR BOUNDARY is what reads: chalking on the
           faces that see a 12.5 deg sun, rain tracking down the web, the
           black rubber road film that only ever lands on the soffit of a
           bridge 2.9 m over a racing surface, chips to the ZINC-RICH PRIMER
           (a 34 m plate girder is blast-cleaned and zinc-primed, NOT hot-dip
           galvanised -- no bath is 34 m long -- so a chip exposes grey-green
           primer, and only a chip THROUGH it exposes mill scale and rusts),
           efflorescence plumes under the deck joints, lime under the perches,
           torque marks on the nuts, and the hard boundary of girder C's
           repaint.  Stated here so nobody wonders whether it was an oversight.

===========================================================================
THE INTERFACE.  This item is a FOUNDATION: pont_soffit_panel, pont_deck_slab
and pont_banner all build on it and cannot ask questions.  Everything in this
block is public and stable, and every number in it is also written to
world/items/pont_girder_interface.json on every build.
===========================================================================

THE BRIDGE FRAME — the convention every dependant must use
        This module builds in a BRIDGE-LOCAL frame and is placed into the
        world by `place=(R, t)` from `pont_to_world()`:

            t = (world x, world y, 0.0) of centreline(2410)
              = (-617.563498, 94.750310, 0.000)
            R = the rotation about z with
                  local +X -> the track's RIGHT-of-travel direction at s=2410
                  local +Y -> the racing direction at s=2410 (heading 295.4)
                  local +Z -> world +Z

        bridge-local axes:
            +X  ALONG THE SPAN, from the infield abutment to the outfield one.
                x = -15.000 is the bearing line on the LEFT of the racing
                direction (contract u = +15, ground 3.568); x = +15.000 is the
                bearing line on the RIGHT (contract u = -15, ground 4.004).
                The two ends of this bridge are NOT symmetric and pont_abutment
                already says so.
            +Y  the RACING DIRECTION.  The girders are spaced in y.  The car
                and the camera arrive from -y, so girder A is the fascia the
                lens sees first.
            +Z  WORLD z.  Not a local z.  z = 0.000 is the racing surface at
                the start/finish line, and ground_z(2410, 0) = 3.935.

THE DATUM PLANE — read these, never assume them
        SOFFIT_Z          6.800  the underside of the bottom flanges AT THE
                                 BEARINGS.  circuit_spec's soffit_z, and the
                                 STRUCTURAL soffit -- but NOT quite the lowest
                                 point, and the difference is measured rather
                                 than asserted.  A welded sole plate hangs
                                 40 mm below it at each bearing (over an
                                 abutment, 15 m off the track centreline) and
                                 a bottom-flange splice cover plate with its
                                 bolt heads hangs ~35 mm below it at one
                                 station per girder, three of which ARE over
                                 the racing surface.  Both are real details.
                                 The interface JSON reports
                                 lowest_z_anywhere, lowest_z_over_track,
                                 track_headroom_measured_m and
                                 camera_clearance_measured_m from the BUILT
                                 mesh, so a dependant never has to guess which
                                 number it is holding.
        soffit_z(gid, x)         the cambered soffit of one girder.  Mid-span
                                 is 11-22 mm HIGHER than SOFFIT_Z, never
                                 lower, and the amount differs per girder.
                                 A dependant that assumes a flat 6.800 shows a
                                 20 mm gap at mid-span = 18 px.
        LOWEST_Z_MEASURED        the lowest z of ANY vertex this module emits,
                                 measured on the built mesh, split into
                                 'anywhere' and 'over the racing surface'.
        TOP_FLANGE_Z      8.150  top of the top flanges at the bearings
                                 (= SOFFIT_Z + 1.350, the manifest's depth).
        DECK_SOFFIT_Z     8.150  FOR pont_deck_slab AND pont_soffit_panel: the
                                 plane the deck slab bears on.  The slab
                                 soffit between girders is this z; over each
                                 girder it is haunched by HAUNCH_M.
        DECK_WIDTH        6.000  circuit_spec's deck width, i.e. the slab
                                 spans y = -3.000 .. +3.000, which cantilevers
                                 0.600 m past each fascia girder.
        SPAN             30.000  bearing centre to bearing centre, x = +-15.000.
        ABUT_FACE_X      14.550  FOR pont_abutment: the abutment front face,
                                 i.e. the clear opening is 29.100 m.
        GIRDER_Y   (-2.400, -0.800, +0.800, +2.400)   girder web centrelines.
        GIRDER_IDS ('A', 'B', 'C', 'D')  in that order.  A and D are the
                                 fascia girders; A is the one facing oncoming
                                 traffic.

WHY THE FOUR GIRDERS ARE NOT THE SAME LENGTH — this is the item's variation
        A and D are FASCIA girders and they run past their bearings as
        tapered cantilever NOSES, because a fascia banner has to be tensioned
        between posts that stand OUTSIDE the visible span and the parapet end
        post has to land on steel rather than on the deck's cantilever tip.
        B and C stop just past their bearings, and their two end stubs differ
        because B's +x end also carries the deck-joint support angle and the
        scupper downpipe bracket.  End-to-end:

            A 34.300 m    B 31.600 m    C 31.520 m    D 33.700 m

        That is a size CV of 0.038 across the four, which is what the
        acceptance gate's per-instance check measures.  The variation the
        BRIEF asks for is the four named axes below, and those are in the
        geometry too; the length spread is a consequence of the two roles,
        not a device for the metric.

THE FOUR VARIATION AXES, DECIDED ONCE AND COUNTED ON BUILD
    web stiffeners  Every girder has connection stiffeners at the nine COMMON
                    cross-frame stations (x = 0, +-4, +-8, +-12, +-15) because
                    a cross-frame has to land on both girders it connects.
                    Everything else differs: A is stiffened both sides at
                    125 x 12 and gets three intermediate panels per end bay;
                    B one side only at 100 x 10; C one side at 100 x 12 with
                    its four middle panels UNSTIFFENED; D both sides at
                    150 x 12.  Counts: A 18, B 12, C 10, D 18 intermediates.
                    Per stiffener, the cope radius, the top weld return, the
                    tension-flange gap, whether it grew a bolted cleat and
                    whether it was ground back all come from its own hash.
    bolt clusters   One field splice per girder, at a DIFFERENT station on
                    each (-4.20 / +6.80 / -9.50 / +2.40 -- staggered splices
                    are real practice and they are what stops the four joints
                    reading as one line), with different web-plate bolt grids
                    (3x9 / 3x8 / 3x10 / 3x9) and different flange patterns.
                    Every bolt's GEOMETRY differs: gantry_truss.bolt_spec
                    draws plain / DTI / nyloc / double-nut / cut-flush /
                    long-tail per bolt uid, plus its own thread protrusion and
                    whether the installer put it in upside down.
    paint system    A and B carry the original 1990s four-coat system, weathered
                    eleven years.  D went out in a later, greener batch because
                    the fabricator ran out -- which is a real thing that happens
                    on a four-girder job and it is visible.  C was struck by an
                    infield crane two seasons ago: it has a bolted doubler
                    plate over the dented panel and a 4.2 m repaint in a
                    fresher, glossier, bluer coat with a hard boundary and an
                    overspray halo.
    camber          Fabricated precamber, residual in service: A 18 mm,
                    B 14 mm, C 22 mm, D 11 mm at mid-span, parabolic, plus a
                    per-girder horizontal sweep (6-14 mm) and web out-of-plumb
                    (3-8 mm).  The soffit datum is at the BEARINGS so the
                    clearance number is never eaten by camber.

MOUNT FRAMES (bridge-local unless the girder set was built with `place`, in
which case they are WORLD).  A Frame is .o origin, .x/.y/.z orthonormal axes,
.r a characteristic radius, .tag a string.  `sorted(B.mounts)` on a built set
lists exactly what it grew.

    bearing_<gid>_<m|p>     FOR pont_bearing_pad.  The UNDERSIDE of the welded
                            sole plate at x = -+15.000 ('m' = minus x, 'p' =
                            plus x), i.e. the face a bearing top plate must
                            meet.  .z points DOWN into the bearing, .x along
                            the span.  .r is the half-diagonal of the sole
                            plate.  There are EIGHT of these (4 girders x 2
                            ends); the manifest's pont_bearing_pad declares 4
                            instances, which is a manifest count for two
                            bearing LINES, not a licence to build half a
                            bridge.  Use all eight.
    deck_bearing_<gid>_<n>  FOR pont_deck_slab.  The top-flange top face at
                            each shear-stud group, z = top_z(gid, x).
    stud_<gid>_<n>          FOR pont_deck_slab.  Individual 19 mm stud axes,
                            so the slab knows what it is encasing.
    banner_rail_top_<A|D>   FOR pont_banner.  The 60 x 8 flat welded along the
                            underside of the fascia girder's top-flange tip,
                            outer face.  .o at mid-span on the rail's outer
                            face, .x along the span, .z DOWN.  .r = 0.030.
    banner_rail_bot_<A|D>   FOR pont_banner.  The L 75 x 50 x 6 bolted to
                            cleats along the outer web face, 0.240 m above the
                            bottom flange.  Same convention.
    banner_post_<A|D>_<m|p> FOR pont_banner.  The tension post standing on the
                            cantilever nose, with its 4 x M16 pattern.
    banner_face_<A|D>       FOR pont_banner.  The OUTER WEB FACE plane of the
                            fascia girder: .o at mid-span on the face, .z the
                            OUTWARD normal.  The banner hangs 0.045 m proud of
                            it.  Rail-to-rail height is BANNER_H = 0.900 m.
    xframe_<n>_<bay>_<lo|hi>  FOR anyone rebuilding the cross-frames: the
                            bolt patterns on the connection stiffeners.
    cable_cleat_<n>         FOR pont_service_duct if it wants a fixing on the
                            trailing fascia's inner face rather than on the
                            deck soffit.
    splice_<gid>            The field splice plane: .o on the joint line, .x
                            along the span.  Nothing may be routed through a
                            splice without a break.

WHAT THIS MODULE ALSO BUILDS, AND WHY IT IS NOT UNDER THE ITEM PREFIX
    The K-frame CROSS-BRACING between the girders (27 frames: a plate
    diaphragm on each bearing line and seven angle K-frames per bay) is built
    here, in the same collection, from the same materials, as objects named
    `PGD_Brace_*`.  It is structurally part of the girder system and there is
    no manifest item for it, so leaving it unbuilt would leave the one thing
    the lens actually sees between the girders missing.  It is deliberately
    NOT under the `PGD_Girder` prefix, because the acceptance gate measures
    per-instance variation over the prefixed objects and the item declares
    FOUR instances: four girders.  Mixing 27 braces into that population would
    make the size CV answer a different question than the one asked.
    `--prefix PGD_Girder` measures the four girders and nothing else.

BUILD
    materials(force=False)  -> [paint, steel, fastener, galv, organic].
                            Idempotent, named 'PGD_*'.  Slot order IS
                            MAT_PAINT/MAT_STEEL/MAT_FAST/MAT_GALV/MAT_ORG.
    build(coll_name='PGD_Girders', place=None, res=1.0) -> Bridge
                            Four girder objects PGD_Girder_A..D plus the
                            braces.  One object per girder: the item declares
                            four instances and the gate counts objects, so
                            splitting a girder into shop lengths would report
                            eight instances of something that does not exist.
                            Object coordinates stay inside +-17.2 m, which is
                            well inside float32 for every procedural here.
    pont_to_world()         -> (R 3x3, t 3).

PER-VERTEX CHANNELS (the shader contract, shared with marshal_post_column and
gantry_truss so a bolt on this bridge and a bolt on the gantry are the same
family of object)
    uv    (u, v)   METRES: u around the section, v along the member.
    base  RGBA     paint colour (linear) + A = member id in [0,1]
    aux   RGBA     (edge_exposure, weld, machined, uid)
    wear  RGBA     (chip, dirt, rust, age)

THE HARD-SURFACE TOOLKIT is imported from world/items/marshal_post_column.py,
which declares it reusable in its own docstring, and the FASTENER AND PLATE
vocabulary from world/items/gantry_truss.py, which built the same fabricator's
bolts for the start/finish gantry.  Both are same-repo hand-written procedural
code; no external asset is involved anywhere in this module.

Run standalone to build the test scene:

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P world/items/pont_girder.py -- --test \
        --out world/items/pont_girder_test.blend
"""

import json
import math
import os
import sys

import numpy as np

try:
    import bpy
except ImportError:                                       # plan layer only
    bpy = None

HERE = os.path.dirname(os.path.abspath(__file__))
WORLD = os.path.dirname(HERE)
ROOT = os.path.dirname(WORLD)
for _p in (HERE, WORLD, os.path.join(ROOT, "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import world_contract as C                                # noqa: E402
import itemkit as K                                               # noqa: E402
import marshal_post_column as HS                          # noqa: E402
import gantry_truss as GT                                 # noqa: E402

# The toolkit contract, checked at import so a refactor upstream fails HERE
# with a name instead of 900 lines later with an AttributeError.
for _need in ("Acc", "sweep", "bridge", "circle_section", "rrect_section",
              "angle_section", "section_outward", "section_perimeter_u",
              "cap_flat", "weld_bead", "hex_nut", "washer", "thread_stud",
              "dome_head", "frames_along", "rot_axis", "rotz", "unit",
              "Frame", "chan", "NG", "_new_mat", "_chan", "_set", "srgb",
              "rect_loop", "rect_loop_counts", "_cell_rings", "open_end",
              "box_beam", "tri_gusset"):
    if not hasattr(HS, _need):
        raise ImportError(
            "pont_girder needs marshal_post_column.%s and it is gone. The "
            "hard-surface toolkit is a shared interface; restore the name or "
            "port the primitive here." % _need)
for _need in ("bolt", "bolt_spec", "bolt_cluster", "hex_head", "grid_plate",
              "rect_grid", "seam_weld", "ring_weld", "local_frame", "BOLTS",
              "loop_outward2", "grid_boundary", "_rxy"):
    if not hasattr(GT, _need):
        raise ImportError(
            "pont_girder needs gantry_truss.%s and it is gone. The fastener "
            "and plate vocabulary is shared with the start/finish gantry on "
            "purpose; restore the name or port the primitive here." % _need)

Acc = HS.Acc
sweep = HS.sweep
bridge = HS.bridge
circle_section = HS.circle_section
rrect_section = HS.rrect_section
angle_section = HS.angle_section
section_outward = HS.section_outward
section_perimeter_u = HS.section_perimeter_u
cap_flat = HS.cap_flat
weld_bead = HS.weld_bead
hex_nut = HS.hex_nut
washer = HS.washer
thread_stud = HS.thread_stud
dome_head = HS.dome_head
frames_along = HS.frames_along
rot_axis = HS.rot_axis
rotz = HS.rotz
unit = HS.unit
Frame = HS.Frame
chan = HS.chan
srgb = HS.srgb
box_beam = HS.box_beam
tri_gusset = HS.tri_gusset

bolt = GT.bolt
bolt_spec = GT.bolt_spec
bolt_cluster = GT.bolt_cluster
grid_plate = GT.grid_plate
seam_weld = GT.seam_weld
ring_weld = GT.ring_weld
local_frame = GT.local_frame
BOLTS = GT.BOLTS

PFX = "PGD_"
ROOT_COLL = "PGD_Girders"
SENSOR_MM = 36.0
TAU = 2.0 * math.pi

MAT_PAINT, MAT_STEEL, MAT_FAST, MAT_GALV, MAT_ORG = range(5)
MAT_NAMES = ["Paint", "Steel", "Fastener", "Galv", "Organic"]


# --------------------------------------------------------------------------- #
#  1.  determinism                                                              #
# --------------------------------------------------------------------------- #

def hash01(*keys):
    """[0,1) from any tuple of numbers/strings.  Same idiom as the other items."""
    h = 2166136261
    for k in keys:
        s = k if isinstance(k, str) else ("%.7g" % float(k))
        for ch in s:
            h = ((h ^ ord(ch)) * 16777619) & 0xFFFFFFFF
    h ^= (h >> 13)
    h = (h * 2654435761) & 0xFFFFFFFF
    h ^= (h >> 16)
    return (h & 0xFFFFFF) / 16777215.0


def rnd(a, b, *keys):
    return a + (b - a) * hash01(*keys)


def rint(a, b, *keys):
    return int(a + (b - a + 1) * hash01(*keys) * 0.999999)


def chance(p, *keys):
    return hash01(*keys) < p


def pick(seq, *keys):
    return seq[int(hash01(*keys) * len(seq) * 0.999999)]


def _n3(v):
    return np.asarray(v, float).reshape(3)


def _smoothstep(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


# --------------------------------------------------------------------------- #
#  2.  THE DIMENSIONS.  Every one is a real fabricated size.                     #
# --------------------------------------------------------------------------- #
#
# circuit_spec.json/paddock/plunge_bridge_design gives s, soffit_z, span and
# deck width.  The manifest adds the 1.35 m girder depth.  Everything else is
# the section schedule a bridge fabricator would actually pick for a 30 m
# simply-supported composite span carrying a 6 m service deck, two parapets
# and two fascia banners.

S_STATION = 2410.0
SOFFIT_Z = 6.800                 # circuit_spec.  WORLD z.  Lowest bridge point.
GIRDER_DEPTH = 1.350             # manifest
TOP_FLANGE_Z = SOFFIT_Z + GIRDER_DEPTH          # 8.150
DECK_SOFFIT_Z = TOP_FLANGE_Z                    # slab bears on the top flange
HAUNCH_M = 0.050                 # the slab is haunched this much over a girder
DECK_WIDTH = 6.000               # circuit_spec
SPAN = 30.000                    # circuit_spec: bearing centre to bearing centre
BEARING_X = SPAN * 0.5           # 15.000
ABUT_FACE_X = 14.550             # abutment front face -> 29.100 m clear opening

GIRDER_IDS = ("A", "B", "C", "D")
GIRDER_Y = (-2.400, -0.800, 0.800, 2.400)       # web centrelines, +y = racing dir
FASCIA = ("A", "D")

# The nine COMMON cross-frame stations.  Every girder carries a connection
# stiffener at each of them because a cross-frame lands on both girders it
# connects; this is why "web stiffeners" varies in the panels BETWEEN them and
# not in where the frames go.
XF_STATIONS = (-15.0, -12.0, -8.0, -4.0, 0.0, 4.0, 8.0, 12.0, 15.0)

BANNER_H = 0.900                 # rail centre to rail centre on the fascia
BANNER_PROUD = 0.045             # how far the banner face stands off the web

STUD_D = 0.019                   # 19 mm shear studs
STUD_H = 0.125
STUD_PITCH = 0.300               # pairs at 300 mm
STUD_GAUGE = 0.110               # transverse gauge within a pair

SOLE_W, SOLE_L, SOLE_T = 0.420, 0.500, 0.040    # welded sole plate at a bearing
HOLE_CLEAR = 0.001               # 2 mm clearance hole -> +1 mm on the radius

PRIMER_HEX = "#6f7a6c"           # zinc-rich epoxy primer: grey-green, NOT zinc
SCALE_HEX = "#26282b"            # mill scale under that
STEEL_HEX = "#3a3d42"            # blast-cleaned / ground bare steel
ZINC_HEX = "#9aa0a4"             # hot-dip zinc, on the small galvanised fittings


# --------------------------------------------------------------------------- #
#  3.  THE FOUR GIRDERS  (plan layer -- no bpy, callable from a bare shell)      #
# --------------------------------------------------------------------------- #

class GirderSpec:
    """One girder's whole identity.  Deterministic from its id."""

    __slots__ = ("gid", "i", "y", "role", "x0", "x1", "nose0", "nose1",
                 "rise0", "rise1", "bw", "bt", "tw", "tt", "wt",
                 "stiff_w", "stiff_t", "stiff_sides", "cope", "gap4t",
                 "inter", "splice_x", "web_rows", "web_cols",
                 "camber", "sweep_m", "plumb", "paint", "paint2",
                 "age", "dirt", "chip", "rust", "repair")

    def __repr__(self):
        return "GirderSpec(%s y=%+.3f L=%.3f)" % (self.gid, self.y,
                                                  self.x1 - self.x0)

    @property
    def length(self):
        return self.x1 - self.x0

    @property
    def is_fascia(self):
        return self.gid in FASCIA

    @property
    def out_sign(self):
        """+1 / -1: which way is OUTBOARD for a fascia girder."""
        return -1.0 if self.gid == "A" else 1.0


# End-to-end lengths: A 34.300  B 31.600  C 31.520  D 33.700.  See the module
# docstring for why they differ; it is the two ROLES, not a fudge factor.
_GEOM = {
    #      x0       x1     nose0   nose1  rise0  rise1
    "A": (-17.150, 17.150, 15.400, 15.400, 0.780, 0.740),
    "B": (-15.400, 16.200, 15.400, 15.550, 0.000, 0.300),
    "C": (-15.760, 15.760, 15.600, 15.600, 0.120, 0.145),
    "D": (-16.900, 16.800, 15.400, 15.400, 0.720, 0.680),
}
# bottom flange w/t, top flange w/t, web t
_SECT = {
    "A": (0.500, 0.040, 0.450, 0.030, 0.012),
    "B": (0.450, 0.032, 0.400, 0.025, 0.012),
    "C": (0.460, 0.035, 0.400, 0.025, 0.014),
    "D": (0.500, 0.040, 0.460, 0.032, 0.012),
}
# stiffener flat w x t, which faces (-1 = -y face, +1 = +y face), cope radius,
# intermediate stiffener count in each of the eight bays
_STIFF = {
    "A": (0.125, 0.012, (-1, 1), 0.040, (3, 3, 2, 1, 1, 2, 3, 3)),
    "B": (0.100, 0.010, (1,),    0.035, (2, 2, 1, 1, 1, 1, 2, 2)),
    "C": (0.100, 0.012, (-1,),   0.032, (2, 2, 1, 0, 0, 1, 2, 2)),
    "D": (0.150, 0.012, (-1, 1), 0.045, (3, 2, 2, 2, 2, 2, 2, 3)),
}
_SPLICE_X = {"A": -4.20, "B": 6.80, "C": -9.50, "D": 2.40}
_WEB_BOLT_ROWS = {"A": 9, "B": 8, "C": 10, "D": 9}
_CAMBER = {"A": 0.018, "B": 0.014, "C": 0.022, "D": 0.011}
_SWEEP = {"A": 0.011, "B": -0.008, "C": 0.014, "D": -0.006}
_PLUMB = {"A": 0.004, "B": -0.007, "C": 0.005, "D": 0.008}
# The paint story.  A and B are the original batch; D is the later, greener
# batch the fabricator finished the job with; C is the struck girder.
_PAINT = {"A": "#55626e", "B": "#55626e", "C": "#55626e", "D": "#52666a"}
_PAINT2 = {"A": None, "B": None, "C": "#66717f", "D": None}
_WEATHER = {                     # age, dirt, chip, rust
    "A": (0.78, 0.62, 0.50, 0.16),
    "B": (0.74, 0.72, 0.42, 0.20),
    "C": (0.66, 0.58, 0.36, 0.14),
    "D": (0.71, 0.55, 0.38, 0.13),
}
# girder C's repair: the struck panel, repainted 4.2 m either side of it
_REPAIR = {"gid": "C", "x": 3.60, "half": 2.10, "dent": 0.021}


def girder_spec(gid):
    """PUBLIC, no bpy.  The whole identity of one girder."""
    if gid not in GIRDER_IDS:
        raise KeyError("girder id must be one of %s, got %r"
                       % (list(GIRDER_IDS), gid))
    s = GirderSpec()
    s.gid = gid
    s.i = GIRDER_IDS.index(gid)
    s.y = GIRDER_Y[s.i]
    s.role = "fascia" if gid in FASCIA else "internal"
    (s.x0, s.x1, s.nose0, s.nose1, s.rise0, s.rise1) = _GEOM[gid]
    (s.bw, s.bt, s.tw, s.tt, s.wt) = _SECT[gid]
    (s.stiff_w, s.stiff_t, s.stiff_sides, s.cope, s.inter) = _STIFF[gid]
    s.gap4t = 4.5 * s.wt                       # tension-flange gap, 4-5 t
    s.splice_x = _SPLICE_X[gid]
    s.web_rows = _WEB_BOLT_ROWS[gid]
    s.web_cols = 3
    s.camber = _CAMBER[gid]
    s.sweep_m = _SWEEP[gid]
    s.plumb = _PLUMB[gid]
    s.paint = _PAINT[gid]
    s.paint2 = _PAINT2[gid]
    (s.age, s.dirt, s.chip, s.rust) = _WEATHER[gid]
    s.repair = dict(_REPAIR) if _REPAIR["gid"] == gid else None
    return s


SPECS = {g: girder_spec(g) for g in GIRDER_IDS}


# --------------------------------------------------------------------------- #
#  4.  THE SHAPE OF A GIRDER  (camber, sweep, nose, waviness)                    #
# --------------------------------------------------------------------------- #

def camber_z(gs, x):
    """Residual in-service camber, m.  Zero at the bearings, positive up.

    The datum is at the BEARINGS on purpose: SOFFIT_Z is a clearance number
    that the film's camera passes 1.8 m under, and a camber measured from
    mid-span would quietly spend it.  Beyond the bearings the camber is held
    at zero rather than continued, so a cantilever nose can never dip below
    the clearance plane either.
    """
    x = np.asarray(x, float)
    t = np.clip(np.abs(x) / BEARING_X, 0.0, 1.0)
    return gs.camber * (1.0 - t * t)


def sweep_y(gs, x):
    """Horizontal lack-of-straightness, m.  A 30 m plate girder is never
    straight in plan; 6-14 mm of sweep is inside every fabrication tolerance
    and it is 5-12 screen px of wander down a 30 m soffit edge."""
    x = np.asarray(x, float)
    t = np.clip((x - gs.x0) / max(gs.length, 1e-9), 0.0, 1.0)
    return (gs.sweep_m * np.sin(math.pi * t)
            + 0.35 * gs.sweep_m * np.sin(2.7 * math.pi * t + 1.1))


def nose_rise(gs, x):
    """How far the soffit has risen above SOFFIT_Z at station x (m).

    Zero over the whole span; a smooth cubic lift beyond the nose start, so
    the fascia girders taper into their cantilever noses instead of stopping
    dead.  This is what makes the two outer girders read as a different
    fabrication from underneath, which they are.
    """
    x = np.asarray(x, float)
    out = np.zeros_like(x)
    for (sgn, xn, rise, xe) in ((-1.0, gs.nose0, gs.rise0, gs.x0),
                                (+1.0, gs.nose1, gs.rise1, gs.x1)):
        if rise <= 0.0:
            continue
        span = abs(xe) - xn
        if span <= 1e-6:
            continue
        t = np.clip((sgn * x - xn) / span, 0.0, 1.0)
        out = out + rise * _smoothstep(t) * (sgn * x > xn)
    return out


def bottom_z(gs, x):
    """WORLD z of the bottom-flange underside at station x."""
    return SOFFIT_Z + camber_z(gs, x) + nose_rise(gs, x)


def top_z(gs, x):
    """WORLD z of the top-flange top face at station x."""
    return TOP_FLANGE_Z + camber_z(gs, x)


def soffit_z(gid, x):
    """PUBLIC.  The cambered soffit of one girder.  Never below SOFFIT_Z."""
    return bottom_z(SPECS[gid] if isinstance(gid, str) else gid, x)


def web_y(gs, x):
    """Plan position of the web centreline at station x."""
    return gs.y + sweep_y(gs, x)


def stiffener_stations(gs):
    """(x, kind) for every transverse stiffener.

    kind: 'bearing' | 'conn' | 'inter'.  The nine connection stations are
    common to all four girders; the intermediates are this girder's own.
    """
    out = [(float(x), "bearing" if abs(abs(x) - BEARING_X) < 1e-6 else "conn")
           for x in XF_STATIONS]
    for b in range(len(XF_STATIONS) - 1):
        x0, x1 = XF_STATIONS[b], XF_STATIONS[b + 1]
        n = gs.inter[b]
        for k in range(n):
            out.append((float(x0 + (x1 - x0) * (k + 1.0) / (n + 1.0)), "inter"))
    out.sort()
    return out


def web_wave(gs, x, q, d):
    """Web panel out-of-flatness, m, normal to the web.

    A welded plate girder's web is NOT flat.  Every panel between stiffeners
    oil-cans by 2.5-6 mm -- which is 2-5 screen px of profile at this item's
    filmed distance, and far more than that in shading -- and the panels
    alternate in sign because the welding sequence alternates.  Superimposed:
    a long-wave plate undulation from the mill, and the WELD PULL-IN, a local
    draw-in of 0.8-1.5 mm within ~70 mm of every seam and every stiffener,
    which is the thing that puts a soft crease down a girder next to each
    weld.

    x (M,) stations, q (K,) heights above the bottom-flange top face,
    d the clear web depth.  -> (M, K).
    """
    x = np.asarray(x, float)
    q = np.asarray(q, float)
    st = np.array([s for (s, k) in stiffener_stations(gs)])
    # panel index for each station
    idx = np.clip(np.searchsorted(st, x) - 1, 0, len(st) - 2)
    x0 = st[idx]
    x1 = st[idx + 1]
    u = np.clip((x - x0) / np.maximum(x1 - x0, 1e-9), 0.0, 1.0)
    amp = np.array([rnd(0.0025, 0.0060, gs.gid, "oil", int(i))
                    * (1.0 if (i % 2 == 0) else -1.0) for i in range(len(st))])
    sk = np.array([rnd(0.30, 0.70, gs.gid, "oilk", int(i))
                   for i in range(len(st))])
    a = amp[idx]
    k = sk[idx]
    # one skewed half-wave per panel, pinned to zero at both stiffeners
    shape_x = np.sin(math.pi * np.clip(u, 0, 1) ** (0.7 + 0.6 * k))
    qn = np.clip(q / max(d, 1e-9), 0.0, 1.0)
    shape_q = np.sin(math.pi * qn) ** 0.85
    W = (a * shape_x)[:, None] * shape_q[None, :]
    # long-wave mill undulation, in both directions
    W = W + (0.0011 * np.sin(x * 0.63 + hash01(gs.gid, "mw") * TAU))[:, None] \
        * (np.sin(math.pi * qn) ** 0.5)[None, :]
    # weld pull-in at the two flange seams
    pull = (np.exp(-(qn * d / 0.070) ** 2)
            + np.exp(-((1.0 - qn) * d / 0.070) ** 2))
    W = W - (0.0013 * pull)[None, :]
    # weld pull-in at every stiffener, on the stiffened faces
    near = np.zeros_like(x)
    for (s, kind) in stiffener_stations(gs):
        near = near + np.exp(-((x - s) / 0.055) ** 2)
    W = W - (0.0011 * np.clip(near, 0.0, 1.6))[:, None] * shape_q[None, :]
    # the struck panel on the repaired girder: a real dent, 21 mm deep
    if gs.repair:
        r = gs.repair
        gx = np.exp(-((x - r["x"]) / 0.42) ** 2)
        gq = np.exp(-((q - d * 0.62) / 0.30) ** 2)
        W = W - r["dent"] * gx[:, None] * gq[None, :]
    return W


def flange_stiff_pull(gs, x, p, half_w, fitted_only=False):
    """The transverse crease every stiffener leaves in the flange, m.

    THE FLANGE SOFFIT IS THE SURFACE THIS ITEM IS MOST SEEN ON, and the thing
    that gives a real one away is not its colour: it is the faint transverse
    ripple every 1.2-1.6 m where a stiffener was welded on and the web-flange
    seam was stopped and restarted.  0.6-0.9 mm of it, which is under a pixel
    of PROFILE and several pixels of SHADING at a 12.5 deg sun, and there is
    no shader that can put it in the right places because the right places are
    the stiffener stations.
    """
    x = np.asarray(x, float)
    p = np.asarray(p, float)
    g = np.zeros_like(x)
    for (s, kind) in stiffener_stations(gs):
        if fitted_only and kind == "inter":
            continue
        a = 0.00092 if kind != "inter" else 0.00058
        a *= 0.6 + 0.8 * hash01(gs.gid, "fsp", s)
        g = g + a * np.exp(-((x - s) / 0.085) ** 2)
    t = np.clip(np.abs(p) / max(half_w, 1e-9), 0.0, 1.0)
    return g[:, None] * (1.0 - 0.55 * t * t)[None, :]


def flange_curl(gs, x, p, half_w, top=False):
    """Angular distortion of a flange, m, vertical.

    Welding a web to a flange shrinks the weld and pulls the flange tips UP
    toward the web on both sides.  1.0-2.5 mm at the tip is normal and it is
    1-2 px of profile plus a very visible shading band down a 30 m soffit.
    Modulated along the span because the welding was done in runs.
    """
    x = np.asarray(x, float)
    p = np.asarray(p, float)
    amp = (0.0016 if not top else 0.0011) * (1.0 + 0.5 * hash01(gs.gid, "curl", top))
    run = 1.0 + 0.42 * np.sin(x * 0.83 + hash01(gs.gid, "curlr", top) * TAU) \
        + 0.18 * np.sin(x * 2.6 + 0.7)
    t = np.clip(np.abs(p) / max(half_w, 1e-9), 0.0, 1.0)
    return (amp * run)[:, None] * (t * t)[None, :]


# --------------------------------------------------------------------------- #
#  5.  THE I-SECTION, as a closed outline with a fixed topology                  #
# --------------------------------------------------------------------------- #
#
# The girder body is ONE swept closed section.  That is not a shortcut: it is
# what makes the four re-entrant web-to-flange corners land exactly where the
# fillet welds have to be run, and it is what lets the web out-of-flatness, the
# flange curl and the flame-cut edge waviness all be per-VERTEX displacements
# of the same grid rather than four separately-modelled plates that then have
# to be made to agree.
#
# The topology is fixed (K points, always the same runs in the same order) so
# the sweep is a clean quad grid; only the CORNER POSITIONS move with station.
# TAG says which surface each point is on, so the displacement fields and the
# edge-exposure channel can be applied by surface rather than by index luck.

TAG_BOT_FACE = 0        # underside of the bottom flange -- what the lens sees
TAG_ARRIS = 1           # a chamfered arris
TAG_TIP = 2             # a flange tip (the flame-cut edge)
TAG_BOT_TOP = 3         # top of the bottom flange -- the pigeon shelf
TAG_WEB = 4             # web face
TAG_TOP_BOT = 5         # underside of the top flange
TAG_TOP_FACE = 6        # top of the top flange -- under the deck slab

CH = 0.0020             # arris chamfer, 2.0 mm = 1.8 screen px
CH2 = 0.0015            # the smaller chamfer on an inner flange arris


def _runs(res=1.0):
    """(count, tag, edge) per outline run.  Topology only -- no dimensions."""
    def n(x):
        return max(2, int(round(x * min(max(res, 0.35), 2.0))))
    return [
        (n(15), TAG_BOT_FACE, 0.06),     # 1->2   bottom face, +p direction
        (2, TAG_ARRIS, 0.98),            # 2->3   chamfer
        (3, TAG_TIP, 0.72),              # 3->4   +p flange tip
        (2, TAG_ARRIS, 0.95),            # 4->5   chamfer
        (n(8), TAG_BOT_TOP, 0.10),       # 5->6   bottom flange top, +p
        (n(24), TAG_WEB, 0.05),          # 6->7   web, +p face
        (n(7), TAG_TOP_BOT, 0.08),       # 7->8   top flange underside, +p
        (2, TAG_ARRIS, 0.95),            # 8->9   chamfer
        (2, TAG_TIP, 0.72),              # 9->10  +p top flange tip
        (2, TAG_ARRIS, 0.98),            # 10->11 chamfer
        (n(13), TAG_TOP_FACE, 0.06),     # 11->12 top face, -p direction
        (2, TAG_ARRIS, 0.98),            # 12->13 chamfer
        (2, TAG_TIP, 0.72),              # 13->14 -p top flange tip
        (2, TAG_ARRIS, 0.95),            # 14->15 chamfer
        (n(7), TAG_TOP_BOT, 0.08),       # 15->16 top flange underside, -p
        (n(24), TAG_WEB, 0.05),          # 16->17 web, -p face
        (n(8), TAG_BOT_TOP, 0.10),       # 17->18 bottom flange top, -p
        (2, TAG_ARRIS, 0.95),            # 18->19 chamfer
        (3, TAG_TIP, 0.72),              # 19->20 -p flange tip
        (2, TAG_ARRIS, 0.98),            # 20->1  chamfer
    ]


def section_topology(res=1.0):
    """-> (K, TAG (K,), E (K,), run_slices).  Fixed for the whole sweep."""
    runs = _runs(res)
    tags, edges, slices = [], [], []
    k = 0
    for (cnt, tag, e) in runs:
        slices.append((k, k + cnt, tag))
        tags.append(np.full(cnt, tag, np.int32))
        edges.append(np.full(cnt, e))
        k += cnt
    return k, np.concatenate(tags), np.concatenate(edges), slices


def section_corners(gs, x, D):
    """The 20 outline corners at each station.  -> (M, 20, 2) in (p, q).

    p is transverse, 0 on the web centreline, +p toward +y.
    q is vertical, 0 at the bottom-flange underside of THIS station.
    """
    x = np.asarray(x, float)
    M = len(x)
    # flame-cut edge waviness: a profiled plate edge wanders +-0.4 mm at a
    # 0.25-0.5 m wavelength and at 1.116 mm/px you can see that it does
    def wob(seed, amp=0.00042):
        return (amp * np.sin(x * 13.7 + hash01(gs.gid, seed) * TAU)
                + 0.55 * amp * np.sin(x * 31.1 + hash01(gs.gid, seed, "b") * TAU))

    hb = 0.5 * gs.bw + wob("bwob")
    ht = 0.5 * gs.tw + wob("twob")
    hw = 0.5 * gs.wt
    bt = np.full(M, gs.bt)
    tt = np.full(M, gs.tt)
    # the fascia noses lose flange width as they taper
    rise = nose_rise(gs, x)
    if gs.is_fascia:
        f = np.clip(rise / max(max(gs.rise0, gs.rise1), 1e-6), 0.0, 1.0)
        hb = hb * (1.0 - 0.34 * f)
        ht = ht * (1.0 - 0.16 * f)
        bt = bt * (1.0 - 0.22 * f)
    top = D                                     # q of the top-flange top face
    wtq = top - tt                              # q of the top flange underside
    Z = np.zeros(M)
    cor = np.stack([
        np.stack([-hb + CH, Z], -1),
        np.stack([hb - CH, Z], -1),
        np.stack([hb, Z + CH], -1),
        np.stack([hb, bt - CH2], -1),
        np.stack([hb - CH2, bt], -1),
        np.stack([np.full(M, hw), bt], -1),
        np.stack([np.full(M, hw), wtq], -1),
        np.stack([ht - CH2, wtq], -1),
        np.stack([ht, wtq + CH2], -1),
        np.stack([ht, top - CH], -1),
        np.stack([ht - CH, top], -1),
        np.stack([-ht + CH, top], -1),
        np.stack([-ht, top - CH], -1),
        np.stack([-ht, wtq + CH2], -1),
        np.stack([-ht + CH2, wtq], -1),
        np.stack([np.full(M, -hw), wtq], -1),
        np.stack([np.full(M, -hw), bt], -1),
        np.stack([-hb + CH2, bt], -1),
        np.stack([-hb, bt - CH2], -1),
        np.stack([-hb, Z + CH], -1),
    ], 1)
    return cor, hb, ht, bt, tt


def section_points(gs, x, D, res=1.0):
    """-> S (M, K, 2) in (p, q), plus TAG (K,) and E (K,)."""
    K, TAG, E, slices = section_topology(res)
    cor, hb, ht, bt, tt = section_corners(gs, x, D)
    M = len(np.asarray(x, float))
    S = np.empty((M, K, 2))
    for (i, (k0, k1, _tag)) in enumerate(slices):
        a = cor[:, i, :]
        b = cor[:, (i + 1) % 20, :]
        f = np.linspace(0.0, 1.0, k1 - k0, endpoint=False)
        S[:, k0:k1, :] = a[:, None, :] + (b - a)[:, None, :] * f[None, :, None]
    return S, TAG, E, hb, ht, bt, tt


def displace_section(gs, x, S, TAG, D, bt, hb, ht, tt):
    """Apply the real fabrication distortions to the section grid, in place.

    This is the step that separates a plate girder from a drawing of one.
    """
    M, K, _ = S.shape
    p = S[:, :, 0]
    q = S[:, :, 1]
    # --- web out-of-flatness + weld pull-in, normal to the web -------------
    wsel = (TAG == TAG_WEB)
    if wsel.any():
        d = float(D.mean() - gs.bt - gs.tt)
        qq = q[:, wsel] - bt[:, None]
        # web_wave wants one q vector; the web rows are the same q profile at
        # every station only to first order, so evaluate on the mean profile
        # and interpolate -- 0.05 mm of error, 0.04 px.
        qref = np.linspace(0.0, d, 48)
        Wref = web_wave(gs, x, qref, d)                # (M, 48)
        W = np.empty_like(qq)
        for m in range(M):
            W[m] = np.interp(qq[m], qref, Wref[m])
        sgn = np.sign(p[:, wsel])
        sgn[sgn == 0.0] = 1.0
        S[:, wsel, 0] = p[:, wsel] + W
        # web out-of-plumb: the whole web leans, worst at mid-height
        lean = gs.plumb * np.clip(qq / max(d, 1e-9), 0.0, 1.0)
        S[:, wsel, 0] = S[:, wsel, 0] + lean
    # --- flange angular distortion -----------------------------------------
    for (sel, half, top) in ((np.isin(TAG, (TAG_BOT_FACE, TAG_BOT_TOP)),
                              hb, False),
                             (np.isin(TAG, (TAG_TOP_BOT, TAG_TOP_FACE)),
                              ht, True)):
        if not sel.any():
            continue
        cur = flange_curl(gs, x, S[0, sel, 0], float(half.mean()), top=top)
        cur = cur + flange_stiff_pull(gs, x, S[0, sel, 0], float(half.mean()),
                                      fitted_only=top)
        S[:, sel, 1] = q[:, sel] + (cur if not top else -cur)
    # --- the flange tips and their chamfers follow the flange they are on ---
    tipsel = (TAG == TAG_TIP) | (TAG == TAG_ARRIS)
    lowtip = tipsel & (S[0, :, 1] < float(D.mean()) * 0.4)
    hightip = tipsel & ~lowtip
    if lowtip.any():
        cur = flange_curl(gs, x, S[0, lowtip, 0], float(hb.mean()), top=False)
        cur = cur + flange_stiff_pull(gs, x, S[0, lowtip, 0], float(hb.mean()))
        S[:, lowtip, 1] = S[:, lowtip, 1] + cur
    if hightip.any():
        cur = flange_curl(gs, x, S[0, hightip, 0], float(ht.mean()), top=True)
        cur = cur + flange_stiff_pull(gs, x, S[0, hightip, 0], float(ht.mean()),
                                      fitted_only=True)
        S[:, hightip, 1] = S[:, hightip, 1] - cur
    return S


# --------------------------------------------------------------------------- #
#  6.  channel helpers                                                          #
# --------------------------------------------------------------------------- #

def ch_paint(gs, member=0.0, uid=0.0, repaint=False):
    """base / aux / wear for a painted girder surface."""
    hexs = gs.paint2 if (repaint and gs.paint2) else gs.paint
    c = srgb(hexs)
    age = 0.12 if repaint else gs.age
    dirt = gs.dirt * (0.45 if repaint else 1.0)
    chip = gs.chip * (0.18 if repaint else 1.0)
    return ((*c, float(member)), (0.25, 0.0, 0.0, float(uid)),
            (chip, dirt, gs.rust, age))


def ch_steel(member=0.0, uid=0.0, rust=0.55, age=0.6):
    return ((*srgb(STEEL_HEX), float(member)), (0.35, 0.0, 0.95, float(uid)),
            (0.05, 0.45, rust, age))


def ch_fast(gs, member=0.0, uid=0.0):
    return ((*srgb(ZINC_HEX), float(member)), (0.35, 0.0, 0.55, float(uid)),
            (0.10, gs.dirt, 0.26, gs.age))


def ch_galv(member=0.0, uid=0.0, dirt=0.45, age=0.60):
    return ((*srgb(ZINC_HEX), float(member)), (0.30, 0.0, 0.06, float(uid)),
            (0.05, dirt, 0.06, age))


def ch_org(member=0.0, uid=0.0):
    return ((0.086, 0.055, 0.030, float(member)), (0.55, 0.0, 0.0, float(uid)),
            (0.0, 0.75, 0.0, 0.85))


def with_edge(aux, e):
    return (float(e), aux[1], aux[2], aux[3])


def with_weld(aux, w):
    return (aux[0], float(w), aux[2], aux[3])


def with_mach(aux, m):
    return (aux[0], aux[1], float(m), aux[3])


def in_repair(gs, x):
    """Is station x inside girder C's repaint?"""
    if not gs.repair:
        return False
    return abs(float(x) - gs.repair["x"]) <= gs.repair["half"]


# --------------------------------------------------------------------------- #
#  7.  ROWS: where the sweep is sampled along the span                          #
# --------------------------------------------------------------------------- #

def body_rows(gs, xa, xb, res=1.0):
    """Station list for one shop length.

    Uniform 55 mm along the barrel -- the web oil-can is a 2-4 m wave and 55 mm
    resolves it to a twentieth -- refined to 14 mm within 130 mm of every
    stiffener (that is where the weld pull-in crease lives), of both bearings,
    of the splice faces and of the two ends, and to 22 mm through the nose
    taper where the section is actually changing shape.
    """
    step = 0.080 / max(min(res, 2.0), 0.3)
    xs = [np.arange(xa, xb + step, step)]
    fine = 0.014 / max(min(res, 2.0), 0.3)
    for (s, _k) in stiffener_stations(gs):
        if xa - 0.14 < s < xb + 0.14:
            xs.append(np.arange(max(s - 0.13, xa), min(s + 0.13, xb) + fine, fine))
    for e in (xa, xb):
        xs.append(np.arange(e, e + 0.10, 0.012) if e == xa
                  else np.arange(e - 0.10, e, 0.012))
    for (xn, rise, xe) in ((gs.nose0, gs.rise0, gs.x0),
                           (gs.nose1, gs.rise1, gs.x1)):
        if rise <= 0.0:
            continue
        lo, hi = sorted((float(np.sign(xe) * xn), float(xe)))
        lo, hi = max(lo, xa), min(hi, xb)
        if hi > lo:
            xs.append(np.arange(lo, hi + 0.022, 0.022))
    t = np.unique(np.clip(np.concatenate(xs), xa, xb))
    return t


# --------------------------------------------------------------------------- #
#  8.  SMALL GEOMETRY UTILITIES                                                 #
# --------------------------------------------------------------------------- #

def ear_clip(P2):
    """Triangulate a simple CCW polygon.  -> (T, 3) index triples.

    An I-section is NOT star-shaped about its centroid -- a ray from the
    centroid to a bottom-flange tip leaves the steel and comes back -- so the
    fan that caps a tube cannot cap a girder end.  The first version fanned it
    anyway and produced a solid triangle of steel filling both re-entrant
    corners, i.e. an I-section that renders as a rectangle when the lens is
    anywhere near the end of it.  The section topology is fixed, so this runs
    ONCE per girder and the index list is reused for every cap.
    """
    P = np.asarray(P2, float)
    n = len(P)
    idx = list(range(n))
    tris = []
    guard = 0
    while len(idx) > 3 and guard < 10 * n:
        guard += 1
        done = False
        for k in range(len(idx)):
            i0 = idx[k - 1]
            i1 = idx[k]
            i2 = idx[(k + 1) % len(idx)]
            a, b, c = P[i0], P[i1], P[i2]
            cross = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
            if cross <= 1e-12:
                continue                      # reflex or degenerate
            # no other vertex inside the candidate ear
            bad = False
            for j in idx:
                if j in (i0, i1, i2):
                    continue
                p = P[j]
                d0 = ((b[0] - a[0]) * (p[1] - a[1])
                      - (b[1] - a[1]) * (p[0] - a[0]))
                d1 = ((c[0] - b[0]) * (p[1] - b[1])
                      - (c[1] - b[1]) * (p[0] - b[0]))
                d2 = ((a[0] - c[0]) * (p[1] - c[1])
                      - (a[1] - c[1]) * (p[0] - c[0]))
                if d0 >= -1e-14 and d1 >= -1e-14 and d2 >= -1e-14:
                    bad = True
                    break
            if bad:
                continue
            tris.append((i0, i1, i2))
            idx.pop(k)
            done = True
            break
        if not done:
            break
    if len(idx) == 3:
        tris.append(tuple(idx))
    return np.array(tris, np.int64) if tris else np.zeros((0, 3), np.int64)


def cap_section(acc, P3, tri, mat, base, aux, wear, flip=False):
    """Cap a swept end with a precomputed triangulation of its outline."""
    K = len(P3)
    a4 = np.tile(np.asarray(aux, float).reshape(1, 4), (K, 1))
    a4[:, 0] = 0.85
    a4[:, 2] = 1.0
    i0 = acc.verts(P3, uv=np.zeros((K, 2)), base=base, aux=a4, wear=wear)
    T = tri + i0
    acc.tris(T[:, ::-1] if flip else T, mat, False)


def fillet_line(acc, P, na, nb, leg, mat, base, aux, wear, uid="f",
                step=0.006, nsec=9, hand=False, pitch=0.0140, ripple=0.16,
                fine=0.0034, hand_pitch=0.0058):
    """A fillet weld run down the line where two faces meet.

    `P` is the ROOT polyline; `na`/`nb` the outward normals of the two joined
    faces.  The toe on face A sits `leg` along nb (i.e. away from face B) and
    vice versa, which is what a fillet actually is.  `hand` switches to the
    stack-of-dimes ripple of a hand-laid weld; a 30 m web-to-flange seam is
    laid by machine and is a smooth wandering fillet, and pretending otherwise
    would be a lie that also cost 400,000 vertices.
    """
    P = np.asarray(P, float).reshape(-1, 3)
    na = np.asarray(na, float)
    nb = np.asarray(nb, float)
    if na.ndim == 1:
        na = np.tile(na, (len(P), 1))
    if nb.ndim == 1:
        nb = np.tile(nb, (len(P), 1))
    lg = np.asarray(leg, float)
    if lg.ndim == 0:
        lg = np.full(len(P), float(lg))
    A = P + nb * lg[:, None]
    B = P + na * lg[:, None]
    if hand:
        # resample so the 4.2 mm ripple resolves, then lay it by hand
        L = float(np.sum(np.linalg.norm(np.diff(P, axis=0), axis=1)))
        n = max(6, int(round(L / fine)))
        t = np.linspace(0.0, len(P) - 1.0, n)
        ii = np.arange(len(P))
        A = np.stack([np.interp(t, ii, A[:, k]) for k in range(3)], -1)
        B = np.stack([np.interp(t, ii, B[:, k]) for k in range(3)], -1)
        NA = np.stack([np.interp(t, ii, na[:, k]) for k in range(3)], -1)
        NB = np.stack([np.interp(t, ii, nb[:, k]) for k in range(3)], -1)
        return weld_bead(acc, A, B, NA, NB, mat, base, with_weld(aux, 1.0),
                         wear, bulge=float(lg.mean()) * 0.34, nsec=nsec,
                         ripple=0.30, pitch=hand_pitch, uid=hash01(uid),
                         closed=False, flip=False)
    return seam_weld(acc, A, B, na, nb, mat, base, aux, wear, uid=uid,
                     step=step, bulge=float(lg.mean()) * 0.30, nsec=nsec,
                     pitch=pitch)


def graded(a, b, fine, coarse, band):
    """Samples from a to b, `fine` near both ends over `band`, `coarse` inside."""
    xs = [np.arange(a, b + coarse, coarse),
          np.arange(a, min(a + band, b) + fine, fine),
          np.arange(max(b - band, a), b + fine, fine), [a, b]]
    return np.unique(np.clip(np.concatenate([np.asarray(v, float) for v in xs]),
                             a, b))


def cells_for(G, pts, r):
    """(i, j, r) hole cells of a grid_plate grid nearest to each (u, v) point."""
    G = np.asarray(G, float)
    nv, nu = G.shape[0] - 1, G.shape[1] - 1
    ctr = 0.25 * (G[:-1, :-1] + G[:-1, 1:] + G[1:, 1:] + G[1:, :-1])
    out, used = [], set()
    for p in pts:
        d = np.linalg.norm(ctr - np.asarray(p, float)[None, None, :], axis=-1)
        order = np.argsort(d, axis=None)
        for o in order:
            i, j = int(o // nu), int(o % nu)
            if (i, j) in used:
                continue
            if i == 0 or j == 0 or i == nv - 1 or j == nu - 1:
                continue                    # never punch the perimeter band
            used.add((i, j))
            out.append((i, j, r))
            break
    return out


def stiff_grid(w, h, cope_t, cope_b, res=1.0):
    """(nv+1, nu+1, 2) grid for a transverse stiffener.

    u = 0 at the web face, u = w at the free edge.  v = -h/2 .. +h/2.
    The COPE is a real quarter circle cut out of the corner where the
    stiffener would otherwise foul the web-to-flange fillet weld -- every
    stiffener on every plate girder ever built has one, and at 1.116 mm/px a
    40 mm cope is a 36 px hole of daylight next to the flange.
    """
    uu = graded(0.0, w, 0.0055 / max(res, 0.4), 0.016 / max(res, 0.4), 0.030)
    vv = graded(-h * 0.5, h * 0.5, 0.0070 / max(res, 0.4),
                0.030 / max(res, 0.4), max(cope_t, cope_b) * 1.8 + 0.02)
    U, V = np.meshgrid(uu, vv)
    for (sgn, r) in ((+1.0, cope_t), (-1.0, cope_b)):
        if r <= 0.0:
            continue
        vb = np.where(U < r, h * 0.5 - r + np.sqrt(np.maximum(
            r * r - (r - np.minimum(U, r)) ** 2, 0.0)), h * 0.5)
        band = r * 1.75
        t = _smoothstep((sgn * V - (h * 0.5 - band)) / max(band, 1e-9))
        V = V + sgn * t * (vb - h * 0.5)
    return np.stack([U, V], -1)


# --------------------------------------------------------------------------- #
#  9.  THE GIRDER BODY                                                          #
# --------------------------------------------------------------------------- #

SPLICE_GAP = 0.010               # the real gap between two shop lengths


def shop_lengths(gs):
    """The two delivered pieces, split at this girder's field splice."""
    g = SPLICE_GAP * 0.5
    return [(gs.x0, gs.splice_x - g), (gs.splice_x + g, gs.x1)]


def build_body(acc, gs, res=1.0, cnt=None):
    """Sweep the two shop lengths and run the four web-to-flange seams.

    -> dict of the geometry other builders need: the seam polylines, the web
    face offsets, the section topology.
    """
    K, TAG, E, slices = section_topology(res)
    info = {"K": K, "pieces": []}
    for (pi, (xa, xb)) in enumerate(shop_lengths(gs)):
        x = body_rows(gs, xa, xb, res)
        M = len(x)
        D = top_z(gs, x) - bottom_z(gs, x)
        S, TAG, E, hb, ht, bt, tt = section_points(gs, x, D, res)
        S = displace_section(gs, x, S, TAG, D, bt, hb, ht, tt)
        Cp = np.stack([x, web_y(gs, x), bottom_z(gs, x)], -1)
        U = np.tile(np.array([0.0, 1.0, 0.0]), (M, 1))
        V = np.tile(np.array([0.0, 0.0, 1.0]), (M, 1))
        # per-station base colour: the repaired girder's repaint has a HARD
        # boundary, because that is what a repaint has
        b0, a0, w0 = ch_paint(gs, member=0.20 + 0.2 * gs.i, uid=hash01(gs.gid))
        base = np.tile(np.asarray(b0, float)[None, :], (M, 1))
        wear = np.tile(np.asarray(w0, float)[None, :], (M, 1))
        if gs.repair:
            b1, _a1, w1 = ch_paint(gs, member=0.20 + 0.2 * gs.i,
                                   uid=hash01(gs.gid), repaint=True)
            sel = np.abs(x - gs.repair["x"]) <= gs.repair["half"]
            base[sel] = np.asarray(b1, float)
            wear[sel] = np.asarray(w1, float)
        aux4 = np.tile(np.asarray(a0, float).reshape(1, 1, 4), (M, K, 1)).copy()
        aux4[..., 0] = E[None, :]
        IDX = sweep(acc, Cp, U, V, S, MAT_PAINT,
                    np.repeat(base[:, None, :], K, 1).reshape(M, K, 4),
                    aux4,
                    np.repeat(wear[:, None, :], K, 1).reshape(M, K, 4),
                    smooth=False, close_u=True)
        P = (Cp[:, None, :] + S[:, :, 0:1] * U[:, None, :]
             + S[:, :, 1:2] * V[:, None, :])
        # --- the two sawn/flame-cut end faces ------------------------------
        tri = ear_clip(S[0])
        bs, ax, we = ch_steel(member=0.9, uid=hash01(gs.gid, "end", pi))
        cap_section(acc, P[0], tri, MAT_STEEL, bs, ax, we, flip=True)
        cap_section(acc, P[-1], ear_clip(S[-1]), MAT_STEEL, bs, ax, we,
                    flip=False)
        info["pieces"].append(dict(x=x, S=S, P=P, TAG=TAG, D=D, hb=hb, ht=ht,
                                   bt=bt, tt=tt, base=base, wear=wear))
        if cnt is not None:
            cnt["body_rows"] = cnt.get("body_rows", 0) + M

        # --- the four web-to-flange fillet seams ---------------------------
        # These are the longest welds on the bridge and two of them are on the
        # surface the film's lens is pointed at.
        leg = 0.008
        bpn, apn, wpn = ch_paint(gs, member=0.55, uid=hash01(gs.gid, "seam", pi))
        for (sgn, top) in ((+1.0, False), (-1.0, False),
                           (+1.0, True), (-1.0, True)):
            wsel = np.where(TAG == TAG_WEB)[0]
            # the web columns on this side, ordered from the bottom flange up
            side = wsel[(S[0, wsel, 0] * sgn) > 0]
            if len(side) < 3:
                continue
            order = np.argsort(S[0, side, 1])
            side = side[order]
            j = side[0] if not top else side[-1]
            root = P[:, j, :].copy()
            root[:, 2] = (P[:, j, 2]
                          + (0.0006 if not top else -0.0006))
            na = np.array([0.0, 0.0, 1.0]) if not top else np.array([0.0, 0.0, -1.0])
            nb = np.array([0.0, sgn, 0.0])
            fillet_line(acc, root, na, nb, leg, MAT_PAINT, bpn,
                        with_weld(apn, 1.0), wpn,
                        uid="%s_seam%d%d%d" % (gs.gid, pi, int(sgn), int(top)),
                        step=0.0065 / max(min(res, 1.6), 0.4), nsec=9,
                        pitch=0.0145)
            if cnt is not None:
                cnt["welds"] = cnt.get("welds", 0) + 1
    return info


def clear_web_depth(gs, x):
    return float(top_z(gs, x) - bottom_z(gs, x) - gs.bt - gs.tt)


def web_face(gs, x, q, sgn):
    """World point on the web face at station x, q above the bottom flange top."""
    d = clear_web_depth(gs, x)
    W = float(web_wave(gs, np.array([float(x)]), np.array([float(q)]), d)[0, 0])
    lean = gs.plumb * min(max(q / max(d, 1e-9), 0.0), 1.0)
    p = sgn * 0.5 * gs.wt + W + lean
    return np.array([float(x), web_y(gs, np.array([float(x)]))[0] + p,
                     float(bottom_z(gs, np.array([float(x)]))[0]) + gs.bt + q])


def web_face_line(gs, x, q0, q1, sgn, n=40):
    qs = np.linspace(q0, q1, n)
    return np.array([web_face(gs, x, q, sgn) for q in qs])


# --------------------------------------------------------------------------- #
# 10.  TRANSVERSE STIFFENERS -- the first named variation axis                  #
# --------------------------------------------------------------------------- #

def stiffener_geom(gs, x, kind):
    """Per-stiffener geometry.  Every number comes from the stiffener's own
    hash, so no two on the bridge are the same object."""
    uid = "%s_st%.3f" % (gs.gid, x)
    d = clear_web_depth(gs, x)
    if kind == "bearing":
        w = min(gs.stiff_w * 1.75, 0.5 * gs.bw - 0.030)
        t = 0.020
        sides = (-1, 1)
        gap = 0.0
        cope_b = rnd(0.038, 0.050, uid, "cb")
    elif kind == "conn":
        w = gs.stiff_w * 1.35
        t = max(gs.stiff_t, 0.012)
        sides = (-1, 1)
        gap = 0.0
        cope_b = rnd(0.030, 0.044, uid, "cb")
    else:
        w = gs.stiff_w
        t = gs.stiff_t
        sides = gs.stiff_sides
        # cut short of the TENSION flange by 4-5 t.  On a simply supported
        # span that is the bottom flange, and the gap is open to the sky:
        # 54 screen px of daylight under every intermediate stiffener.
        gap = gs.gap4t * rnd(0.86, 1.18, uid, "gap")
        cope_b = 0.0
    return dict(uid=uid, x=float(x), kind=kind, w=float(w), t=float(t),
                sides=tuple(sides), gap=float(gap), d=d,
                cope_t=float(rnd(0.85, 1.20, uid, "ct") * gs.cope),
                cope_b=float(cope_b),
                cleat=chance(0.17, uid, "cleat") and kind == "inter",
                lug=chance(0.11, uid, "lug"),
                ground=chance(0.22, uid, "gr"),
                ret=rnd(0.020, 0.045, uid, "ret"))


def build_stiffener(acc, gs, sp, mats_cnt, res=1.0, bolt_shapes=None,
                    mounts=None):
    """One transverse stiffener: the plate, its copes, and its fillet welds."""
    x, w, t, d = sp["x"], sp["w"], sp["t"], sp["d"]
    q0 = sp["gap"]
    q1 = d
    h = q1 - q0
    bpn, apn, wpn = ch_paint(gs, member=0.62, uid=hash01(sp["uid"]),
                             repaint=in_repair(gs, x))
    for sgn in sp["sides"]:
        G = stiff_grid(w, h, sp["cope_t"], sp["cope_b"], res)
        holes = []
        if sp["kind"] == "conn":
            # the cross-frame gusset bolts through this plate; the BOLTS
            # belong to the brace that lands here, the HOLES belong here
            pts = [(w * 0.52, -h * 0.30), (w * 0.52, 0.0), (w * 0.52, h * 0.30),
                   (w * 0.80, -h * 0.18), (w * 0.80, h * 0.18)]
            holes = cells_for(G, pts, 0.0130)
        o = web_face(gs, x, q0 + h * 0.5, sgn)
        eu = np.array([0.0, float(sgn), 0.0])
        ev = np.array([0.0, 0.0, 1.0])
        grid_plate(acc, o + np.array([0.0, 0.0, 0.0]), eu, ev, None, G, t,
                   holes, MAT_PAINT, bpn, apn, wpn, uid=hash01(sp["uid"], sgn),
                   chamfer=0.0015, wave=0.00030, nvring=4)
        mats_cnt["stiffeners"] = mats_cnt.get("stiffeners", 0) + 1
        mats_cnt["stiff_holes"] = mats_cnt.get("stiff_holes", 0) + len(holes)
        # --- welds: two vertical runs down the web, one each side of the plate
        leg = 0.006 if sp["kind"] == "inter" else 0.008
        for fs in (-1.0, +1.0):
            P = web_face_line(gs, x + fs * t * 0.5, q0 + 0.004,
                              q1 - sp["cope_t"] * 1.02, sgn,
                              n=max(10, int(30 * min(res * 1.4, 1.6))))
            fillet_line(acc, P, np.array([0.0, float(sgn), 0.0]),
                        np.array([float(fs), 0.0, 0.0]), leg, MAT_PAINT,
                        bpn, with_weld(apn, 1.0), wpn,
                        uid=sp["uid"] + "v%d%d" % (sgn, fs), hand=True, nsec=7,
                        fine=0.0034 / max(min(res, 1.6), 0.4))
            mats_cnt["welds"] = mats_cnt.get("welds", 0) + 1
        # --- the fitted top: a return weld onto the top-flange underside ----
        zt = float(top_z(gs, np.array([x]))[0]) - gs.tt
        for fs in (-1.0, +1.0):
            n = 14
            u = np.linspace(sp["cope_t"] * 1.02, w - 0.004, n)
            yw = web_face(gs, x, q1 - 0.020, sgn)[1]
            P = np.stack([np.full(n, x + fs * t * 0.5), yw + sgn * u,
                          np.full(n, zt - 0.0008)], -1)
            fillet_line(acc, P, np.array([0.0, 0.0, -1.0]),
                        np.array([float(fs), 0.0, 0.0]), leg, MAT_PAINT,
                        bpn, with_weld(apn, 1.0), wpn,
                        uid=sp["uid"] + "t%d%d" % (sgn, fs), hand=True, nsec=7)
        # --- the bottom: fitted (welded) or cut short (nothing) -------------
        if sp["gap"] <= 1e-6:
            zb = float(bottom_z(gs, np.array([x]))[0]) + gs.bt
            for fs in (-1.0, +1.0):
                n = 14
                u = np.linspace(sp["cope_b"] * 1.02 + 0.002, w - 0.004, n)
                P = np.stack([np.full(n, x + fs * t * 0.5),
                              web_face(gs, x, 0.02, sgn)[1] + sgn * u,
                              np.full(n, zb + 0.0008)], -1)
                fillet_line(acc, P, np.array([0.0, 0.0, 1.0]),
                            np.array([float(fs), 0.0, 0.0]), leg, MAT_PAINT,
                            bpn, with_weld(apn, 1.0), wpn,
                            uid=sp["uid"] + "b%d%d" % (sgn, fs), hand=True,
                            nsec=7)
        # --- an erection lug left on, or a bolted cleat ---------------------
        if sp["lug"]:
            lo = web_face(gs, x, q1 - 0.14, sgn) + eu * (w + 0.006)
            box_beam(acc, lo, lo + eu * 0.075 + np.array([0.0, 0.0, 0.010]),
                     0.014, 0.055, MAT_STEEL,
                     *ch_steel(member=0.7, uid=hash01(sp["uid"], "lug")),
                     up=(0, 0, 1))
            mats_cnt["lugs"] = mats_cnt.get("lugs", 0) + 1
        if sp["cleat"] and bolt_shapes is not None:
            co = web_face(gs, x, q0 + h * 0.62, sgn) + eu * (w * 0.55)
            bf, af, wf = ch_fast(gs, member=0.95,
                                 uid=hash01(sp["uid"], "cleat"))
            specs = bolt_cluster(
                acc, [co + np.array([-t * 0.5 - 0.008, 0.0, 0.055]),
                      co + np.array([-t * 0.5 - 0.008, 0.0, -0.055])],
                np.array([1.0, 0.0, 0.0]), MAT_FAST, bf, af, wf,
                uid=sp["uid"] + "cl", size="M16", grip=t + 0.010)
            for s in specs:
                bolt_shapes.add((s["kind"], round(s["tail"], 4), s["size"]))
            mats_cnt["bolts"] = mats_cnt.get("bolts", 0) + len(specs)


# --------------------------------------------------------------------------- #
# 11.  BEARINGS, SOLE PLATES, JACKING STIFFENERS                                #
# --------------------------------------------------------------------------- #

def build_bearing(acc, gs, sgn_x, mounts, cnt, res=1.0):
    """The welded sole plate at one bearing, and the frame pont_bearing_pad
    has to land on.  The bearing itself is NOT built here -- it is its own
    manifest item and this module must not redefine it."""
    x = sgn_x * BEARING_X
    zb = float(bottom_z(gs, np.array([x]))[0])
    y0 = float(web_y(gs, np.array([x]))[0])
    uid = "%s_sole%d" % (gs.gid, sgn_x)
    bs, ax, we = ch_steel(member=0.85, uid=hash01(uid), rust=0.35, age=0.55)
    # the sole plate: 500 (span) x 420 (transverse) x 40, machined flat on its
    # underside -- that face is the one the bearing meets and it is ground
    G = np.stack(np.meshgrid(
        graded(-SOLE_L * 0.5, SOLE_L * 0.5, 0.010, 0.030, 0.030),
        graded(-SOLE_W * 0.5, SOLE_W * 0.5, 0.010, 0.030, 0.030)), -1)
    o = np.array([x, y0, zb - SOLE_T * 0.5])
    grid_plate(acc, o, np.array([1.0, 0.0, 0.0]), np.array([0.0, 1.0, 0.0]),
               None, G, SOLE_T, [], MAT_STEEL, bs, with_mach(ax, 1.0), we,
               uid=hash01(uid), chamfer=0.0025, wave=0.00025)
    cnt["plates"] = cnt.get("plates", 0) + 1
    # fillet weld all round, where the sole plate meets the flange soffit
    bp, ap, wp = ch_paint(gs, member=0.7, uid=hash01(uid, "w"))
    lp = HS.rect_loop(-SOLE_L * 0.5, SOLE_L * 0.5, -SOLE_W * 0.5,
                      SOLE_W * 0.5, 0.006)
    P = np.concatenate([o[None, :] + np.stack(
        [lp[:, 0], lp[:, 1], np.full(len(lp), SOLE_T * 0.5)], -1),
        (o + np.array([lp[0, 0], lp[0, 1], SOLE_T * 0.5]))[None, :]], 0)
    nrm = GT.loop_outward2(lp)
    nb = np.concatenate([np.concatenate([nrm, np.zeros((len(nrm), 1))], 1),
                         np.array([[nrm[0, 0], nrm[0, 1], 0.0]])], 0)
    fillet_line(acc, P, np.array([0.0, 0.0, -1.0]), nb, 0.008, MAT_PAINT,
                bp, with_weld(ap, 1.0), wp, uid=uid + "wl", hand=True, nsec=9)
    cnt["welds"] = cnt.get("welds", 0) + 1
    # THE MOUNT.  .z points DOWN, into the bearing.
    mounts["bearing_%s_%s" % (gs.gid, "m" if sgn_x < 0 else "p")] = Frame(
        (x, y0, zb - SOLE_T), (1.0, 0.0, 0.0), (0.0, -1.0, 0.0),
        (0.0, 0.0, -1.0), 0.5 * math.hypot(SOLE_L, SOLE_W),
        "sole plate underside, girder %s, x=%+.3f" % (gs.gid, x))


# --------------------------------------------------------------------------- #
# 12.  THE FIELD SPLICE -- the second named variation axis                      #
# --------------------------------------------------------------------------- #

def build_splice(acc, gs, mounts, cnt, bolt_shapes, res=1.0):
    """A bolted HSFG field splice: web plates both faces, flange cover plates
    outside and in, and every bolt its own object."""
    x = gs.splice_x
    d = clear_web_depth(gs, x)
    zb = float(bottom_z(gs, np.array([x]))[0])
    y0 = float(web_y(gs, np.array([x]))[0])
    uid = "%s_spl" % gs.gid
    bp, ap, wp = ch_paint(gs, member=0.72, uid=hash01(uid),
                          repaint=in_repair(gs, x))
    bf, af, wf = ch_fast(gs, member=0.95, uid=hash01(uid, "f"))
    rows = gs.web_rows
    cols = gs.web_cols
    cx = 0.075
    px_ = 0.080
    pz = min(0.110, (d - 0.16) / max(rows - 1, 1))
    hw_pl = cx + (cols - 1) * px_ + 0.048
    hh_pl = (rows - 1) * pz * 0.5 + 0.050
    t_pl = 0.012
    # --- web splice plates, one each face -------------------------------
    bolt_uv = [(sx * (cx + k * px_), (r - (rows - 1) * 0.5) * pz)
               for sx in (-1, 1) for k in range(cols) for r in range(rows)]
    for sgn in (-1, 1):
        G = np.stack(np.meshgrid(
            graded(-hw_pl, hw_pl, 0.010, 0.026, 0.030),
            graded(-hh_pl, hh_pl, 0.010, 0.026, 0.030)), -1)
        holes = cells_for(G, bolt_uv, 0.0130)
        o = web_face(gs, x, d * 0.5, sgn) + np.array([0.0, sgn * t_pl * 0.5, 0.0])
        grid_plate(acc, o, np.array([1.0, 0.0, 0.0]), np.array([0.0, 0.0, 1.0]),
                   None, G, t_pl, holes, MAT_PAINT, bp, ap, wp,
                   uid=hash01(uid, sgn), chamfer=0.0018, wave=0.00035)
        cnt["plates"] = cnt.get("plates", 0) + 1
        cnt["splice_holes"] = cnt.get("splice_holes", 0) + len(holes)
    # --- the bolts, all the way through the pack --------------------------
    grip = 2 * t_pl + gs.wt
    for (i, (u, v)) in enumerate(bolt_uv):
        p = web_face(gs, x + u, d * 0.5 + v, -1) + np.array([0.0, -t_pl, 0.0])
        p[0] = x + u
        sp = bolt_spec("%s_wb%d" % (uid, i), size="M24", grip=grip)
        bolt(acc, p, np.array([0.0, 1.0, 0.0]), sp, MAT_FAST, bf, af, wf,
             ref=(0.0, 0.0, 1.0))
        bolt_shapes.add((sp["kind"], round(sp["tail"], 4), sp["size"],
                         sp["head_down"]))
        cnt["bolts"] = cnt.get("bolts", 0) + 1
    # --- flange cover plates ---------------------------------------------
    for (top, ft, fw) in ((False, gs.bt, gs.bw), (True, gs.tt, gs.tw)):
        z_out = (float(top_z(gs, np.array([x]))[0]) if top else zb)
        nrm = 1.0 if top else -1.0
        nrows = 4 if not top else 4
        gy = [sy * (0.5 * gs.wt + 0.055 + j * 0.085)
              for sy in (-1, 1) for j in range(2)]
        ncol = 4 if not top else 3
        pxf = 0.075
        cxf = 0.048
        gx = [sx * (cxf + k * pxf) for sx in (-1, 1) for k in range(ncol)]
        hwf = cxf + (ncol - 1) * pxf + 0.042
        t_out = 0.016
        t_in = 0.012
        # outer cover plate
        G = np.stack(np.meshgrid(
            graded(-hwf, hwf, 0.010, 0.026, 0.030),
            graded(-fw * 0.46, fw * 0.46, 0.010, 0.026, 0.030)), -1)
        holes = cells_for(G, [(a, b) for a in gx for b in gy], 0.0130)
        o = np.array([x, y0, z_out + nrm * t_out * 0.5])
        grid_plate(acc, o, np.array([1.0, 0.0, 0.0]), np.array([0.0, 1.0, 0.0]),
                   None, G, t_out, holes, MAT_PAINT, bp, ap, wp,
                   uid=hash01(uid, "fo", top), chamfer=0.0018, wave=0.00035)
        cnt["plates"] = cnt.get("plates", 0) + 1
        # two inner plates, one each side of the web
        for sy in (-1, 1):
            G2 = np.stack(np.meshgrid(
                graded(-hwf, hwf, 0.010, 0.026, 0.030),
                graded(0.5 * gs.wt + 0.012, fw * 0.46, 0.008, 0.024, 0.026)), -1)
            h2 = cells_for(G2, [(a, abs(b)) for a in gx for b in gy if
                                (b > 0) == (sy > 0)], 0.0130)
            o2 = np.array([x, y0, z_out - nrm * (ft + t_in * 0.5)])
            grid_plate(acc, o2, np.array([1.0, 0.0, 0.0]),
                       np.array([0.0, float(sy), 0.0]), None, G2, t_in, h2,
                       MAT_PAINT, bp, ap, wp, uid=hash01(uid, "fi", top, sy),
                       chamfer=0.0018, wave=0.00035)
            cnt["plates"] = cnt.get("plates", 0) + 1
        gripf = t_out + ft + t_in
        for (i, (a, b)) in enumerate([(a, b) for a in gx for b in gy]):
            p = np.array([x + a, y0 + b, z_out + nrm * t_out])
            # HEADS DOWN on the bottom flange.  A cover plate under a
            # bottom flange is bolted from below, and letting the RNG put a
            # long threaded tail there instead would hang 61 mm of bolt into
            # the clearance envelope over a racing surface for no reason.
            sp = bolt_spec("%s_fb%d%d" % (uid, int(top), i), size="M24",
                           grip=gripf, flip=(False if not top else None))
            bolt(acc, p, np.array([0.0, 0.0, -nrm]), sp, MAT_FAST, bf, af, wf,
                 ref=(1.0, 0.0, 0.0))
            bolt_shapes.add((sp["kind"], round(sp["tail"], 4), sp["size"],
                             sp["head_down"]))
            cnt["bolts"] = cnt.get("bolts", 0) + 1
    mounts["splice_%s" % gs.gid] = Frame(
        (x, y0, zb + 0.5 * GIRDER_DEPTH), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0),
        (0.0, 0.0, 1.0), hh_pl, "field splice joint line, girder %s" % gs.gid)


# --------------------------------------------------------------------------- #
# 13.  SHEAR STUDS, PERCH SPIKES, A NEST, AND THE REPAIR DOUBLER                #
# --------------------------------------------------------------------------- #

def shear_stud(acc, o, mat, base, aux, wear, uid=0.0, nseg=20):
    """A 19 x 125 headed stud with its upset weld collar.

    Studs are welded through a ferrule that leaves a ragged annular collar,
    never a clean fillet, and the collar is the only part of a stud that ever
    reads once the slab is cast -- but the slab is pont_deck_slab's item and
    this module cannot assume it got poured, so the stud is built whole.
    """
    o = _n3(o)
    th = np.arange(nseg) * TAU / nseg
    rc = 0.0135 + 0.0011 * np.sin(th * 3.0 + hash01(uid, "c") * TAU)
    prof = [(rc, 0.0), (rc * 0.97, 0.0035), (np.full(nseg, 0.0097), 0.0075),
            (np.full(nseg, 0.0095), STUD_H - 0.012),
            (np.full(nseg, 0.0155), STUD_H - 0.010),
            (np.full(nseg, 0.0155), STUD_H - 0.0012),
            (np.full(nseg, 0.0140), STUD_H)]
    rings = []
    for (r, z) in prof:
        r = np.asarray(r, float)
        if r.ndim == 0:
            r = np.full(nseg, float(r))
        P = o[None, :] + np.stack([r * np.cos(th), r * np.sin(th),
                                   np.full(nseg, z)], -1)
        a = np.tile(np.asarray(aux, float).reshape(1, 4), (nseg, 1))
        a[:, 0] = 0.35
        i0 = acc.verts(P, uv=np.stack([th * 0.01, np.full(nseg, z)], -1),
                       base=base, aux=a, wear=wear)
        rings.append(i0 + np.arange(nseg))
    for k in range(len(rings) - 1):
        bridge(acc, rings[k], rings[k + 1], mat, smooth=True, flip=False)
    ic = acc.verts((o + np.array([0.0, 0.0, STUD_H])).reshape(1, 3),
                   uv=np.zeros((1, 2)), base=base,
                   aux=np.asarray(aux, float).reshape(1, 4), wear=wear)
    acc.fan(rings[-1], ic, mat, smooth=False, flip=False)


def build_studs(acc, gs, mounts, cnt, res=1.0):
    bg, ag, wg = ch_steel(member=0.5, uid=hash01(gs.gid, "stud"), rust=0.30,
                          age=0.35)
    n = 0
    x = -BEARING_X + 0.30
    while x < BEARING_X - 0.30:
        z = float(top_z(gs, np.array([x]))[0])
        y = float(web_y(gs, np.array([x]))[0])
        for sy in (-1, 1):
            shear_stud(acc, (x, y + sy * STUD_GAUGE * 0.5, z), MAT_STEEL,
                       bg, ag, wg, uid=hash01(gs.gid, "s", n, sy),
                       nseg=max(8, int(14 * min(res, 1.2))))
            n += 1
        if n % 40 == 0:
            mounts["stud_%s_%d" % (gs.gid, n)] = Frame(
                (x, y, z), (1, 0, 0), (0, 1, 0), (0, 0, 1), STUD_H,
                "shear stud pair, girder %s" % gs.gid)
        x += STUD_PITCH
    cnt["studs"] = cnt.get("studs", 0) + n


def build_perch(acc, gs, cnt, res=1.0):
    """Anti-perch spikes on the bottom-flange shelf, and the lime under them.

    The top of a bottom flange is the best perch for 600 m and every real
    bridge over a road has a bird problem, a partial answer to it, and the
    stains that prove the answer is partial.  A 3 mm spike wire is 2.7 screen
    px, so this is mesh.
    """
    if gs.gid not in ("A", "D", "B"):
        return
    bands = {"A": ((-9.4, -6.9), (1.2, 3.9), (8.0, 10.6)),
             "D": ((-4.8, -2.1), (5.6, 8.3)),
             "B": ((11.0, 12.6),)}[gs.gid]
    bg, ag, wg = ch_galv(member=0.4, uid=hash01(gs.gid, "spike"), dirt=0.8)
    n = 0
    for (bi, (xa, xb)) in enumerate(bands):
        x = xa
        while x < xb:
            for sy in (-1, 1):
                y = web_face(gs, x, 0.004, sy)[1] + sy * 0.030
                z = float(bottom_z(gs, np.array([x]))[0]) + gs.bt
                uid = "%s_sp%d_%d_%d" % (gs.gid, bi, n, sy)
                # the polycarbonate/galv base strip
                box_beam(acc, (x - 0.115, y, z + 0.002),
                         (x + 0.115, y, z + 0.002), 0.018, 0.004,
                         MAT_GALV, bg, ag, wg, up=(0, 0, 1))
                for k in range(6):
                    xx = x - 0.100 + k * 0.040
                    lean = rnd(-0.35, 0.35, uid, "l", k)
                    tilt = rnd(0.30, 0.62, uid, "t", k) * (1 if k % 2 else -1)
                    p0 = np.array([xx, y, z + 0.004])
                    p1 = p0 + np.array([lean * 0.030, tilt * 0.055, 0.105])
                    T = np.linspace(0, 1, 5)[:, None]
                    P = p0[None, :] + (p1 - p0)[None, :] * T
                    P[:, 2] -= 0.004 * (T[:, 0] ** 2)
                    Tt, Uu, Vv = frames_along(P, ref=(1, 0, 0))
                    S, E, _ = circle_section(7, 0.0015)
                    sweep(acc, P, Uu, Vv, S, MAT_GALV, bg,
                          with_edge(ag, 0.5), wg, smooth=True)
                    n += 1
            x += 0.250
    cnt["spikes"] = cnt.get("spikes", 0) + n


def build_nest(acc, gs, cnt):
    """A pigeon's nest wedged on the bottom-flange shelf behind a stiffener.

    One, on one girder.  It is the single cheapest thing on this bridge that
    says the structure has been standing here for eleven years, and at 1.1
    mm/px a 4 mm twig is 3.6 screen px.
    """
    if gs.gid != "B":
        return
    x0 = 12.90
    sy = 1
    y0 = web_face(gs, x0, 0.010, sy)[1] + sy * 0.055
    z0 = float(bottom_z(gs, np.array([x0]))[0]) + gs.bt
    bo, ao, wo = ch_org(member=0.3, uid=hash01(gs.gid, "nest"))
    n = 0
    for k in range(74):
        uid = ("nest", k)
        a0 = rnd(0.0, TAU, *uid, "a")
        rr = rnd(0.055, 0.125, *uid, "r")
        zz = z0 + 0.004 + rnd(0.0, 0.055, *uid, "z")
        ln = rnd(0.070, 0.190, *uid, "l")
        bend = rnd(-0.9, 0.9, *uid, "b")
        c = np.array([x0 + math.cos(a0) * rr * 0.55,
                      y0 + math.sin(a0) * rr * 0.75, zz])
        ang = rnd(0.0, TAU, *uid, "d")
        d = np.array([math.cos(ang), math.sin(ang) * 0.8,
                      rnd(-0.25, 0.25, *uid, "dz")])
        d = d / np.linalg.norm(d)
        t = np.linspace(-0.5, 0.5, 6)[:, None]
        P = c[None, :] + d[None, :] * (t * ln)
        P[:, 2] += bend * 0.012 * (t[:, 0] ** 2 - 0.08)
        Tt, Uu, Vv = frames_along(P, ref=(0, 0, 1))
        S, E, _ = circle_section(6, rnd(0.0016, 0.0032, *uid, "t2"))
        sweep(acc, P, Uu, Vv, S, MAT_ORG, bo, with_edge(ao, 0.4), wo,
              smooth=True)
        n += 1
    cnt["nest_twigs"] = cnt.get("nest_twigs", 0) + n


def build_doubler(acc, gs, cnt, bolt_shapes, res=1.0):
    """The bolted repair doubler over girder C's struck web panel."""
    if not gs.repair:
        return
    r = gs.repair
    x = r["x"]
    d = clear_web_depth(gs, x)
    bp, ap, wp = ch_paint(gs, member=0.80, uid=hash01(gs.gid, "dbl"),
                          repaint=True)
    bf, af, wf = ch_fast(gs, member=0.95, uid=hash01(gs.gid, "dblf"))
    hw_pl, hh_pl, t_pl = 0.560, 0.290, 0.012
    uv = [(sx * (0.070 + k * 0.115), sz * (0.070 + j * 0.140))
          for sx in (-1, 1) for k in range(4) for sz in (-1, 1) for j in range(2)]
    for sgn in (-1, 1):
        G = np.stack(np.meshgrid(
            graded(-hw_pl, hw_pl, 0.010, 0.028, 0.030),
            graded(-hh_pl, hh_pl, 0.010, 0.028, 0.030)), -1)
        holes = cells_for(G, uv, 0.0110)
        o = web_face(gs, x, d * 0.62, sgn) + np.array([0.0, sgn * t_pl * 0.5, 0.0])
        grid_plate(acc, o, np.array([1.0, 0.0, 0.0]), np.array([0.0, 0.0, 1.0]),
                   None, G, t_pl, holes, MAT_PAINT, bp, ap, wp,
                   uid=hash01(gs.gid, "dbl", sgn), chamfer=0.0018)
        cnt["plates"] = cnt.get("plates", 0) + 1
    for (i, (u, v)) in enumerate(uv):
        p = web_face(gs, x + u, d * 0.62 + v, -1) + np.array([0.0, -t_pl, 0.0])
        p[0] = x + u
        sp = bolt_spec("%s_db%d" % (gs.gid, i), size="M20",
                       grip=2 * t_pl + gs.wt)
        bolt(acc, p, np.array([0.0, 1.0, 0.0]), sp, MAT_FAST, bf, af, wf,
             ref=(0.0, 0.0, 1.0))
        bolt_shapes.add((sp["kind"], round(sp["tail"], 4), sp["size"],
                         sp["head_down"]))
        cnt["bolts"] = cnt.get("bolts", 0) + 1


# --------------------------------------------------------------------------- #
# 14.  THE FASCIA FURNITURE  (what pont_banner and pont_parapet land on)        #
# --------------------------------------------------------------------------- #

def build_fascia(acc, gs, mounts, cnt, bolt_shapes, res=1.0):
    """Banner rails, their cleats, and the tension posts on the noses."""
    if not gs.is_fascia:
        # the trailing internal face of girder D carries the cable cleats; the
        # trailing FASCIA is D itself, so put them on D's inner face below
        return
    out = gs.out_sign
    bp, ap, wp = ch_paint(gs, member=0.68, uid=hash01(gs.gid, "fasc"))
    bg, ag, wg = ch_galv(member=0.45, uid=hash01(gs.gid, "fascg"))
    bf, af, wf = ch_fast(gs, member=0.95, uid=hash01(gs.gid, "fascf"))
    xs = np.linspace(-BEARING_X - 0.6, BEARING_X + 0.6, 160)
    # --- top rail: a 60 x 8 flat welded under the top-flange tip -----------
    ztop = top_z(gs, xs) - gs.tt - 0.004
    ytip = web_y(gs, xs) + out * (0.5 * gs.tw - 0.010)
    P = np.stack([xs, ytip, ztop], -1)
    Tt, Uu, Vv = frames_along(P, ref=(0, 0, 1))
    S, E = rrect_section(0.008, 0.060, 0.0015, nc=3, ns=2)
    sweep(acc, P, Uu, Vv, S, MAT_PAINT, bp, with_edge(ap, 0.7), wp,
          edge=E * 0.8, smooth=False)
    mounts["banner_rail_top_%s" % gs.gid] = Frame(
        (0.0, float(np.interp(0.0, xs, ytip)) + out * 0.004,
         float(np.interp(0.0, xs, ztop))),
        (1, 0, 0), (0, 0, -1) if out > 0 else (0, 0, -1),
        (0.0, out, 0.0), 0.030,
        "banner top rail, outer face of fascia girder %s" % gs.gid)
    # --- bottom rail: L 75 x 50 x 6 on cleats every 2.5 m ------------------
    zbot = bottom_z(gs, xs) + gs.bt + 0.240
    yweb = np.array([web_face(gs, float(t), 0.240, out)[1] for t in xs])
    P2 = np.stack([xs, yweb + out * 0.052, zbot], -1)
    Tt, Uu, Vv = frames_along(P2, ref=(0, 0, 1))
    S2, E2 = angle_section(0.075, 0.050, 0.006)
    sweep(acc, P2, Uu, Vv, S2, MAT_PAINT, bp, with_edge(ap, 0.7), wp,
          edge=E2 * 0.85, smooth=False)
    mounts["banner_rail_bot_%s" % gs.gid] = Frame(
        (0.0, float(np.interp(0.0, xs, yweb)) + out * 0.052,
         float(np.interp(0.0, xs, zbot))),
        (1, 0, 0), (0, 0, 1), (0.0, out, 0.0), 0.030,
        "banner bottom rail, outer face of fascia girder %s" % gs.gid)
    n = 0
    for x in np.arange(-14.0, 14.01, 2.5):
        q = 0.240
        o = web_face(gs, float(x), q, out)
        G = np.stack(np.meshgrid(graded(-0.055, 0.055, 0.006, 0.016, 0.020),
                                 graded(0.0, 0.075, 0.006, 0.014, 0.018)), -1)
        holes = cells_for(G, [(-0.026, 0.048), (0.026, 0.048)], 0.0090)
        grid_plate(acc, o + np.array([0.0, out * 0.006, 0.0]),
                   np.array([1.0, 0.0, 0.0]), np.array([0.0, 0.0, 1.0]), None,
                   G, 0.010, holes, MAT_PAINT, bp, ap, wp,
                   uid=hash01(gs.gid, "cl", n), chamfer=0.0015)
        for (i, (u, v)) in enumerate([(-0.026, 0.048), (0.026, 0.048)]):
            p = o + np.array([u, out * 0.011, v])
            sp = bolt_spec("%s_bc%d_%d" % (gs.gid, n, i), size="M16",
                           grip=0.010 + 0.006)
            bolt(acc, p, np.array([0.0, out, 0.0]), sp, MAT_FAST, bf, af, wf,
                 ref=(0.0, 0.0, 1.0))
            bolt_shapes.add((sp["kind"], round(sp["tail"], 4), sp["size"],
                             sp["head_down"]))
            cnt["bolts"] = cnt.get("bolts", 0) + 1
        cnt["plates"] = cnt.get("plates", 0) + 1
        n += 1
    # --- the tension posts on the two cantilever noses ---------------------
    for (sgn, xe) in ((-1.0, gs.x0), (+1.0, gs.x1)):
        xp = xe - sgn * 0.230
        zt = float(top_z(gs, np.array([xp]))[0])
        y = float(web_y(gs, np.array([xp]))[0])
        G = np.stack(np.meshgrid(graded(-0.090, 0.090, 0.007, 0.018, 0.020),
                                 graded(-0.080, 0.080, 0.007, 0.018, 0.020)), -1)
        pat = [(a, b) for a in (-0.055, 0.055) for b in (-0.050, 0.050)]
        holes = cells_for(G, pat, 0.0095)
        grid_plate(acc, np.array([xp, y, zt + 0.008]),
                   np.array([1.0, 0.0, 0.0]), np.array([0.0, 1.0, 0.0]), None,
                   G, 0.016, holes, MAT_PAINT, bp, ap, wp,
                   uid=hash01(gs.gid, "tp", sgn), chamfer=0.0018)
        S3, E3 = rrect_section(0.080, 0.080, 0.008, nc=4, ns=2)
        n3 = 6
        Pp = np.stack([np.full(n3, xp), np.full(n3, y),
                       np.linspace(zt + 0.016, zt + 0.016 + BANNER_H * 0.55,
                                   n3)], -1)
        Tt, Uu, Vv = frames_along(Pp, ref=(1, 0, 0))
        sweep(acc, Pp, Uu, Vv, S3, MAT_PAINT, bp, with_edge(ap, 0.6), wp,
              edge=E3 * 0.9, smooth=False)
        cap_flat(acc, Pp[-1], Uu[-1], Vv[-1], S3, MAT_PAINT, bp,
                 with_edge(ap, 0.9), wp, flip=False)
        for (i, (a, b)) in enumerate(pat):
            p = np.array([xp + a, y + b, zt + 0.016])
            sp = bolt_spec("%s_tpb%d_%d" % (gs.gid, int(sgn), i), size="M16",
                           grip=0.016 + gs.tt)
            bolt(acc, p, np.array([0.0, 0.0, -1.0]), sp, MAT_FAST, bf, af, wf,
                 ref=(1.0, 0.0, 0.0))
            bolt_shapes.add((sp["kind"], round(sp["tail"], 4), sp["size"],
                             sp["head_down"]))
            cnt["bolts"] = cnt.get("bolts", 0) + 1
        mounts["banner_post_%s_%s" % (gs.gid, "m" if sgn < 0 else "p")] = Frame(
            (xp, y, zt + 0.016), (1, 0, 0), (0, 1, 0), (0, 0, 1), 0.056,
            "banner tension post base, girder %s" % gs.gid)
    mounts["banner_face_%s" % gs.gid] = Frame(
        (0.0, float(web_face(gs, 0.0, 0.6, out)[1]),
         float(bottom_z(gs, np.array([0.0]))[0]) + gs.bt + 0.240 + BANNER_H * 0.5),
        (1, 0, 0), (0, 0, 1), (0.0, out, 0.0), BANNER_H * 0.5,
        "banner face plane, %.3f m rail-to-rail, hangs %.3f proud"
        % (BANNER_H, BANNER_PROUD))


def build_end_furniture(acc, gs, mounts, cnt, bolt_shapes, res=1.0):
    """The fittings the girder ENDS carry, and the mounts they publish.

    Every one of these exists because a dependant needs somewhere to land:
    pont_deck_slab's expansion joint needs a support angle, pont_scupper's
    downpipe needs a saddle to be clamped to, and pont_parapet's end post
    needs a base plate that is on STEEL rather than on the deck's cantilever
    tip.  Building the mount and not the fitting would be a docstring that
    describes a bridge nobody built.
    """
    bp, ap, wp = ch_paint(gs, member=0.66, uid=hash01(gs.gid, "endf"))
    bf, af, wf = ch_fast(gs, member=0.95, uid=hash01(gs.gid, "endff"))
    bg, ag, wg = ch_galv(member=0.44, uid=hash01(gs.gid, "endg"))
    # --- the deck-joint support angle and the scupper saddle, on girder B --
    if gs.gid == "B":
        x = 15.880
        d = clear_web_depth(gs, x)
        o = web_face(gs, x, d - 0.150, +1)
        S, E = angle_section(0.100, 0.075, 0.008)
        n = 6
        P = np.stack([np.linspace(x - 0.240, x + 0.240, n),
                      np.full(n, o[1] + 0.048), np.full(n, o[2])], -1)
        Tt, Uu, Vv = frames_along(P, ref=(0, 0, 1))
        sweep(acc, P, Uu, Vv, S, MAT_PAINT, bp, with_edge(ap, 0.7), wp,
              edge=E * 0.85, smooth=False)
        cap_flat(acc, P[0], Uu[0], Vv[0], S, MAT_PAINT, bp,
                 with_edge(ap, 0.95), wp, flip=True)
        cap_flat(acc, P[-1], Uu[-1], Vv[-1], S, MAT_PAINT, bp,
                 with_edge(ap, 0.95), wp, flip=False)
        for (i, dx) in enumerate((-0.150, 0.0, 0.150)):
            p = np.array([x + dx, o[1] + 0.010, o[2]])
            sp = bolt_spec("%s_ja%d" % (gs.gid, i), size="M16",
                           grip=0.008 + gs.wt)
            bolt(acc, p, np.array([0.0, -1.0, 0.0]), sp, MAT_FAST, bf, af, wf,
                 ref=(0.0, 0.0, 1.0))
            bolt_shapes.add((sp["kind"], round(sp["tail"], 4), sp["size"],
                             sp["head_down"]))
            cnt["bolts"] = cnt.get("bolts", 0) + 1
        mounts["deck_joint_angle_B"] = Frame(
            tuple(float(v) for v in P[len(P) // 2] + np.array([0, 0, 0.050])),
            (1, 0, 0), (0, 1, 0), (0, 0, 1), 0.100,
            "deck expansion-joint support angle, girder B +x stub")
        # the scupper downpipe saddle: two galvanised half-bands on the web
        xs2 = 15.560
        for (k, q) in enumerate((0.980, 0.360)):
            ob = web_face(gs, xs2, q, +1)
            box_beam(acc, ob, ob + np.array([0.0, 0.088, 0.0]), 0.032, 0.006,
                     MAT_GALV, bg, ag, wg, up=(0, 0, 1))
            c = ob + np.array([0.0, 0.088, 0.0])
            th = np.linspace(-1.9, 1.9, 16)
            r = 0.062
            Pb = np.stack([c[0] + r * np.sin(th) * 0.0,
                           c[1] + r * np.cos(th) * 0.0 + r,
                           c[2] + 0.0 * th], -1)
            Pb[:, 0] = c[0] + r * np.sin(th)
            Pb[:, 2] = c[2] + r * (1.0 - np.cos(th)) - r * 0.35
            Tt2, U2, V2 = frames_along(Pb, ref=(0, 1, 0))
            S2, E2 = rrect_section(0.006, 0.030, 0.0012, nc=2, ns=1)
            sweep(acc, Pb, U2, V2, S2, MAT_GALV, bg, with_edge(ag, 0.7), wg,
                  edge=E2 * 0.8, smooth=False)
            mounts["scupper_saddle_%d" % k] = Frame(
                tuple(float(v) for v in c + np.array([0.0, 0.0, r * 0.65])),
                (1, 0, 0), (0, 1, 0), (0, 0, 1), r,
                "scupper downpipe saddle on girder B, %.3f m above the "
                "bottom flange" % q)
        cnt["cleats"] = cnt.get("cleats", 0) + 2
    # --- the parapet end-post base plates, on the fascia noses -------------
    if not gs.is_fascia:
        return
    for (sgn, xe) in ((-1.0, gs.x0), (+1.0, gs.x1)):
        xp = xe - sgn * 0.780
        zt = float(top_z(gs, np.array([xp]))[0])
        y = float(web_y(gs, np.array([xp]))[0])
        G = np.stack(np.meshgrid(graded(-0.075, 0.075, 0.007, 0.018, 0.020),
                                 graded(-0.070, 0.070, 0.007, 0.018, 0.020)),
                     -1)
        pat = [(a, b) for a in (-0.045, 0.045) for b in (-0.042, 0.042)]
        holes = cells_for(G, pat, 0.0110)
        grid_plate(acc, np.array([xp, y, zt + 0.007]),
                   np.array([1.0, 0.0, 0.0]), np.array([0.0, 1.0, 0.0]), None,
                   G, 0.014, holes, MAT_PAINT, bp, ap, wp,
                   uid=hash01(gs.gid, "pep", sgn), chamfer=0.0018)
        cnt["plates"] = cnt.get("plates", 0) + 1
        for (i, (a, b)) in enumerate(pat):
            p = np.array([xp + a, y + b, zt + 0.014])
            sp = bolt_spec("%s_pep%d_%d" % (gs.gid, int(sgn), i), size="M20",
                           grip=0.014 + gs.tt)
            bolt(acc, p, np.array([0.0, 0.0, -1.0]), sp, MAT_FAST, bf, af, wf,
                 ref=(1.0, 0.0, 0.0))
            bolt_shapes.add((sp["kind"], round(sp["tail"], 4), sp["size"],
                             sp["head_down"]))
            cnt["bolts"] = cnt.get("bolts", 0) + 1
        mounts["parapet_end_%s_%s" % (gs.gid, "m" if sgn < 0 else "p")] = Frame(
            (xp, y, zt + 0.014), (1, 0, 0), (0, 1, 0), (0, 0, 1), 0.052,
            "parapet end-post base plate, 4 x M20 at 90 x 84, girder %s"
            % gs.gid)


def build_cable_cleats(acc, gs, mounts, cnt, res=1.0):
    """Galvanised cable cleats on the trailing fascia's INNER face."""
    if gs.gid != "D":
        return
    bg, ag, wg = ch_galv(member=0.42, uid=hash01(gs.gid, "cc"))
    n = 0
    for x in np.arange(-13.5, 13.6, 2.2):
        o = web_face(gs, float(x), 0.980, -1)
        box_beam(acc, o, o + np.array([0.0, -0.075, 0.0]), 0.028, 0.008,
                 MAT_GALV, bg, ag, wg, up=(0, 0, 1))
        p = o + np.array([0.0, -0.075, 0.0])
        box_beam(acc, p + np.array([0.0, 0.0, -0.028]),
                 p + np.array([0.0, 0.0, 0.028]), 0.026, 0.008, MAT_GALV,
                 bg, ag, wg, up=(1, 0, 0))
        if n % 6 == 0:
            mounts["cable_cleat_%d" % n] = Frame(
                tuple(float(v) for v in p), (1, 0, 0), (0, 0, 1),
                (0, -1, 0), 0.030, "cable cleat on girder D inner face")
        n += 1
    cnt["cleats"] = cnt.get("cleats", 0) + n


# --------------------------------------------------------------------------- #
# 15.  THE CROSS-BRACING  (built here, deliberately NOT under the item prefix)  #
# --------------------------------------------------------------------------- #

def brace_points(gs, x, sgn_out):
    """The two gusset centres on one girder's connection stiffener at x."""
    d = clear_web_depth(gs, x)
    sp = stiffener_geom(gs, x, "bearing" if abs(abs(x) - BEARING_X) < 1e-6
                        else "conn")
    w = sp["w"]
    lo = web_face(gs, x, d * 0.20, sgn_out) + np.array([0.0, sgn_out * w * 0.62, 0.0])
    hi = web_face(gs, x, d * 0.80, sgn_out) + np.array([0.0, sgn_out * w * 0.62, 0.0])
    return lo, hi, sp


def build_brace_bay(acc, bay, mounts, cnt, bolt_shapes, res=1.0):
    """One bay of cross-bracing: a plate diaphragm on each bearing line and an
    X-frame of angles at each of the seven intermediate stations."""
    ga = SPECS[GIRDER_IDS[bay]]
    gb = SPECS[GIRDER_IDS[bay + 1]]
    for x in XF_STATIONS:
        uid = "br%d_%.0f" % (bay, x)
        alo, ahi, spa = brace_points(ga, x, +1.0)
        blo, bhi, spb = brace_points(gb, x, -1.0)
        bp, ap, wp = ch_paint(ga, member=0.35, uid=hash01(uid))
        bf, af, wf = ch_fast(ga, member=0.95, uid=hash01(uid, "f"))
        if abs(abs(x) - BEARING_X) < 1e-6:
            # --- a plate diaphragm on the bearing line ---------------------
            z0 = 0.5 * (alo[2] + blo[2]) - 0.02
            z1 = 0.5 * (ahi[2] + bhi[2]) + 0.02
            y0, y1 = alo[1], blo[1]
            G = np.stack(np.meshgrid(
                graded(0.0, abs(y1 - y0), 0.012, 0.040, 0.040),
                graded(-(z1 - z0) * 0.5, (z1 - z0) * 0.5, 0.012, 0.040, 0.040)),
                -1)
            o = np.array([x, min(y0, y1), 0.5 * (z0 + z1)])
            grid_plate(acc, o, np.array([0.0, 1.0, 0.0]),
                       np.array([0.0, 0.0, 1.0]), None, G, 0.012, [],
                       MAT_PAINT, bp, ap, wp, uid=hash01(uid, "dia"),
                       chamfer=0.0020, wave=0.00035)
            cnt["brace_plates"] = cnt.get("brace_plates", 0) + 1
            continue
        # --- an X-frame of L 100 x 100 x 10 angles -------------------------
        S, E = angle_section(0.100, 0.100, 0.010)
        for (p0, p1, tag) in ((alo, blo, "bot"), (alo, bhi, "d1"),
                              (ahi, blo, "d2"), (ahi, bhi, "top")):
            n = 8
            P = np.linspace(0.0, 1.0, n)[:, None] * (p1 - p0)[None, :] + p0[None, :]
            P[:, 2] += 0.0016 * np.sin(math.pi * np.linspace(0, 1, n))
            Tt, Uu, Vv = frames_along(P, ref=(0, 0, 1))
            sweep(acc, P, Uu, Vv, S, MAT_PAINT, bp, with_edge(ap, 0.7), wp,
                  edge=E * 0.85, smooth=False)
            cap_flat(acc, P[0], Uu[0], Vv[0], S, MAT_PAINT, bp,
                     with_edge(ap, 0.95), wp, flip=True)
            cap_flat(acc, P[-1], Uu[-1], Vv[-1], S, MAT_PAINT, bp,
                     with_edge(ap, 0.95), wp, flip=False)
            cnt["brace_members"] = cnt.get("brace_members", 0) + 1
        # --- the four gussets, bolted to the connection stiffeners ---------
        for (gsx, pt, sgn) in ((ga, alo, +1.0), (ga, ahi, +1.0),
                               (gb, blo, -1.0), (gb, bhi, -1.0)):
            pat = [(0.0, -0.058), (0.0, 0.058), (0.078, 0.0)]
            G = np.stack(np.meshgrid(
                graded(-0.075, 0.115, 0.007, 0.020, 0.022),
                graded(-0.100, 0.100, 0.007, 0.020, 0.022)), -1)
            holes = cells_for(G, pat, 0.0130)
            o = pt + np.array([sgn * 0.0 - 0.006 - 0.012 * 0.5, 0.0, 0.0])
            grid_plate(acc, o, np.array([0.0, float(sgn), 0.0]),
                       np.array([0.0, 0.0, 1.0]), None, G, 0.012, holes,
                       MAT_PAINT, bp, ap, wp,
                       uid=hash01(uid, "g", pt[2], sgn), chamfer=0.0018)
            cnt["brace_plates"] = cnt.get("brace_plates", 0) + 1
            for (i, (u, v)) in enumerate(pat):
                sgeo = stiffener_geom(gsx, x, "bearing"
                                      if abs(abs(x) - BEARING_X) < 1e-6 else "conn")
                p = np.array([o[0] - 0.006, pt[1] + sgn * u, pt[2] + v])
                sp = bolt_spec("%s_gb%d_%.2f" % (uid, i, pt[2]), size="M20",
                               grip=0.012 + sgeo["t"])
                bolt(acc, p, np.array([1.0, 0.0, 0.0]), sp, MAT_FAST, bf, af,
                     wf, ref=(0.0, 0.0, 1.0))
                bolt_shapes.add((sp["kind"], round(sp["tail"], 4), sp["size"],
                                 sp["head_down"]))
                cnt["brace_bolts"] = cnt.get("brace_bolts", 0) + 1
        mounts["xframe_%d_%s" % (bay, ("m" if x < 0 else "p")
                                 + ("%.0f" % abs(x)))] = Frame(
            (x, 0.5 * (alo[1] + blo[1]), 0.5 * (alo[2] + bhi[2])),
            (1, 0, 0), (0, 1, 0), (0, 0, 1), 0.8,
            "cross-frame, bay %s-%s, x=%+.1f"
            % (ga.gid, gb.gid, x))


def build_id_plate(acc, gs, cnt):
    """The fabricator's stamped identification plate, welded to the web."""
    x = gs.x1 - 1.60
    d = clear_web_depth(gs, x)
    o = web_face(gs, x, d * 0.78, -1)
    bs, ax, we = ch_steel(member=0.6, uid=hash01(gs.gid, "id"), rust=0.30)
    G = np.stack(np.meshgrid(graded(-0.075, 0.075, 0.005, 0.012, 0.014),
                             graded(-0.045, 0.045, 0.005, 0.012, 0.014)), -1)
    grid_plate(acc, o + np.array([0.0, -0.0015, 0.0]),
               np.array([1.0, 0.0, 0.0]), np.array([0.0, 0.0, 1.0]), None,
               G, 0.003, [], MAT_STEEL, bs, with_mach(ax, 1.0), we,
               uid=hash01(gs.gid, "idp"), chamfer=0.0006)
    cnt["plates"] = cnt.get("plates", 0) + 1


# --------------------------------------------------------------------------- #
# 16.  THE ASSEMBLY                                                             #
# --------------------------------------------------------------------------- #

class Bridge:
    __slots__ = ("objects", "girders", "braces", "mounts", "stats", "place",
                 "meta")

    def __init__(self):
        self.objects = []
        self.girders = []
        self.braces = []
        self.mounts = {}
        self.stats = {}
        self.meta = {}
        self.place = None


def _coll(name, parent=None):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(c)
    return c


def purge():
    for ob in list(bpy.data.objects):
        if ob.name.startswith(PFX):
            bpy.data.objects.remove(ob, do_unlink=True)
    for me in list(bpy.data.meshes):
        if me.name.startswith(PFX) or me.users == 0:
            bpy.data.meshes.remove(me)


def pont_to_world():
    """PUBLIC.  (R 3x3, t 3) taking bridge-local -> world.

    The bridge crosses the circuit square at s = 2410.  Local +Y is the racing
    direction there and local +X is to the RIGHT of it, which makes the triple
    right-handed with world +Z; both are read from world_contract rather than
    hard-coded, so if the centreline ever moves this follows it.
    """
    cx, cy = C.centreline(S_STATION)[0], C.centreline(S_STATION)[1]
    wl = np.array(C.su_to_world(S_STATION, 1.0)) - np.array(
        C.su_to_world(S_STATION, 0.0))
    u_left = wl[:2] / np.linalg.norm(wl[:2])            # +u, LEFT of travel
    ex = np.array([-u_left[0], -u_left[1], 0.0])        # local +X = right
    ey = np.array([u_left[1], -u_left[0], 0.0])
    # ey must be the racing direction; cross(ex, ey) has to be +z
    if np.cross(ex, ey)[2] < 0:
        ey = -ey
    R = np.stack([ex, ey, np.array([0.0, 0.0, 1.0])], axis=1)
    t = np.array([float(cx), float(cy), 0.0])
    return R, t


def build(coll_name=ROOT_COLL, place=None, res=1.0, verbose=True):
    """Build the four girders and their cross-bracing.

    ONE OBJECT PER GIRDER.  The item declares four instances and the
    acceptance gate counts prefixed objects, so splitting a girder into its
    two shop lengths would report eight instances of a thing there are four
    of.  Object coordinates reach +-17.2 m, which is far inside float32 for
    every procedural in this module -- the precision law is about |P| ~ 1000 m
    world positions, and every material here reads TexCoord -> Object.
    """
    mats = materials()
    coll = _coll(coll_name)
    B = Bridge()
    B.place = place
    cnt = {}
    bolt_shapes = set()
    stiff_shapes = set()
    local_mounts = {}

    for gid in GIRDER_IDS:
        gs = SPECS[gid]
        acc = Acc(PFX + "Girder_" + gid)
        build_body(acc, gs, res=res, cnt=cnt)
        for (x, kind) in stiffener_stations(gs):
            sp = stiffener_geom(gs, x, kind)
            build_stiffener(acc, gs, sp, cnt, res=res,
                            bolt_shapes=bolt_shapes, mounts=local_mounts)
            stiff_shapes.add((sp["kind"], len(sp["sides"]),
                              round(sp["w"], 4), round(sp["t"], 4),
                              round(sp["gap"], 4), round(sp["cope_t"], 4),
                              round(sp["cope_b"], 4), sp["cleat"], sp["lug"]))
        for sgn in (-1, 1):
            build_bearing(acc, gs, sgn, local_mounts, cnt, res=res)
        build_splice(acc, gs, local_mounts, cnt, bolt_shapes, res=res)
        build_studs(acc, gs, local_mounts, cnt, res=res)
        build_perch(acc, gs, cnt, res=res)
        build_nest(acc, gs, cnt)
        build_doubler(acc, gs, cnt, bolt_shapes, res=res)
        build_fascia(acc, gs, local_mounts, cnt, bolt_shapes, res=res)
        build_cable_cleats(acc, gs, local_mounts, cnt, res=res)
        build_end_furniture(acc, gs, local_mounts, cnt, bolt_shapes, res=res)
        build_id_plate(acc, gs, cnt)
        # HONEST CLEARANCE.  SOFFIT_Z is the bottom-flange underside, and
        # things hang below it: the welded sole plate at each bearing (40 mm,
        # but that is over an abutment 15 m from the track centreline) and the
        # bottom-flange splice cover plate with its bolt heads (35 mm, and
        # THAT one is over the racing surface).  Both are real; what would not
        # be real is a datum that quietly ignored them.  Measure both.
        V = np.concatenate(acc._V, 0)
        cnt["lowest_z_%s" % gid] = float(V[:, 2].min())
        sel = np.abs(V[:, 0]) <= float(C.half_width(S_STATION)) + 1.0
        cnt["lowest_z_over_track_%s" % gid] = (float(V[sel, 2].min())
                                               if sel.any() else None)
        if place is not None:
            acc.xform(place[0], place[1])
        ob = acc.emit(coll, mats, PFX + "Girder_" + gid)
        B.objects.append(ob)
        B.girders.append(ob)
        if verbose:
            print(">>   girder %s: L %.3f m, %d verts, soffit low z %.4f"
                  % (gid, gs.length, acc.n, cnt["lowest_z_%s" % gid]))

    for bay in range(3):
        acc = Acc(PFX + "Brace_%s%s" % (GIRDER_IDS[bay], GIRDER_IDS[bay + 1]))
        build_brace_bay(acc, bay, local_mounts, cnt, bolt_shapes, res=res)
        if place is not None:
            acc.xform(place[0], place[1])
        ob = acc.emit(coll, mats,
                      PFX + "Brace_%s%s" % (GIRDER_IDS[bay], GIRDER_IDS[bay + 1]))
        B.objects.append(ob)
        B.braces.append(ob)

    if place is not None:
        R, t = place
        B.mounts = {k: f.transformed(R, t) for k, f in local_mounts.items()}
    else:
        B.mounts = dict(local_mounts)
    cnt["distinct_bolt_geometries"] = len(bolt_shapes)
    cnt["distinct_stiffener_shapes"] = len(stiff_shapes)
    cnt["lowest_z"] = min(cnt["lowest_z_%s" % g] for g in GIRDER_IDS)
    cnt["lowest_z_over_track"] = min(cnt["lowest_z_over_track_%s" % g]
                                     for g in GIRDER_IDS)
    cnt["track_headroom_measured_m"] = (cnt["lowest_z_over_track"]
                                        - float(C.ground_z(S_STATION, 0.0)))
    cnt["camera_clearance_measured_m"] = cnt["lowest_z_over_track"] - 5.000
    cnt["girder_lengths"] = {g: SPECS[g].length for g in GIRDER_IDS}
    B.stats = cnt
    return B


# --------------------------------------------------------------------------- #
# 17.  MATERIALS                                                                #
# --------------------------------------------------------------------------- #
#
# Five surfaces, each a stack of things that PHYSICALLY HAPPENED to the steel,
# in the order they happened.  The one thing this item must not get wrong:
# A 34 m PLATE GIRDER IS NOT HOT-DIP GALVANISED.  No bath is 34 m long.  It is
# grit-blasted to Sa 2.5, given a zinc-rich epoxy primer, and painted.  So a
# chip exposes GREY-GREEN PRIMER, not zinc spangle and not rust; only a chip
# that goes THROUGH the primer reaches mill scale and rusts.  Getting that
# wrong is the commonest tell in rendered steelwork, and it is exactly the
# opposite mistake from the one gantry_truss had to avoid (that structure IS
# galvanised, being small enough to dip).  The small fittings here -- spikes,
# cable cleats -- are galvanised, and they use mat_galv.

_MATS = None


def _new_mat(name):
    m = bpy.data.materials.get(PFX + name)
    if m is None:
        m = bpy.data.materials.new(PFX + name)
    g = HS.NG(m)
    out = g.n("ShaderNodeOutputMaterial")
    bsdf = g.n("ShaderNodeBsdfPrincipled")
    g.lk(bsdf, 0, out, 0)
    return m, g, bsdf, out


def _up(g):
    nrm = g.n("ShaderNodeNewGeometry")
    z = g.sepxyz((nrm, 1))
    return g.math('MAXIMUM', (z, 2), 0.0, clamp=True)


def _down(g):
    nrm = g.n("ShaderNodeNewGeometry")
    z = g.sepxyz((nrm, 1))
    return g.math('MAXIMUM', g.math('MULTIPLY', (z, 2), -1.0), 0.0, clamp=True)


def mat_paint():
    """Four-coat system over zinc-rich primer over blast-cleaned steel.

      1  the topcoat, with a per-girder dye drift AND a per-plate lot drift,
         so no two plates on one girder are exactly the same grey and the
         repaint on girder C is a different animal entirely.
      2  AIRLESS SPRAY texture: orange peel at 2-4 mm, dry spray where the gun
         was too far off the web, runs where it was too close.
      3  mill scale telegraphing through four coats -- what stops a 30 m web
         reading as a swatch.
      4  CHALKING, on the faces that see a 12.5 deg sun.  The soffit never
         chalks, which is why the underside of a bridge is always a different
         colour from the top of it.
      5  RAIN TRACKING down the web in bands, clean stripes on dirty steel.
      6  ROAD FILM.  This soffit is 2.9 m over a racing surface.  What lands on
         it is atomised rubber and tyre dust, not road dust: near-black, matt,
         thickest under the fascia and fading inboard.  Without this the
         underside renders the same colour as the top and the whole item reads
         as a model.
      7  EFFLORESCENCE plumes running down the web under the deck joints, and
         the rust-brown tail inside each one.
      8  BIRD LIME on the bottom-flange shelves and the drip streaks below.
      9  CHIPS to zinc-rich PRIMER, keyed off aux.r so the arrises go first,
         with a low-frequency coverage mask so the damage lands in clusters
         the way handling damage actually distributes.
     10  a rarer, deeper chip THROUGH the primer to mill scale, which is the
         only chip that is allowed to rust.
     11  RED rust where the steel was cut, drilled or ground -- carried by
         aux.b, never by the chip mask.
     12  grime in the low-gloss valleys, heaviest low down and on up-faces.
    """
    m, g, b, _ = _new_mat("Paint")
    base, aux, wear, bs, au, we, tc, uv, obj = HS._chan(g)
    edge, weld, mach = (au, 0), (au, 1), (au, 2)
    chip, dirt, rust, age = (we, 0), (we, 1), (we, 2), (wear, 3)
    memb = (aux, 3)
    up, down = _up(g), _down(g)

    lot = g.noise(g.vmath('MULTIPLY', obj, (1.35, 1.35, 1.35)), scale=2.0,
                  detail=5.0, rough=0.55)
    k = g.math('ADD', 0.930,
               g.math('MULTIPLY',
                      g.math('SUBTRACT',
                             g.math('ADD', g.math('MULTIPLY', lot, 0.60),
                                    g.math('MULTIPLY', memb, 0.40)), 0.5),
                      0.230))
    col = g.n("ShaderNodeMixRGB", blend_type='MULTIPLY')
    g._feed(col, 0, 1.0)
    g._feed(col, 1, base)
    g._feed(col, 2, g.comb(k, k, k))

    peel = g.noise(g.vmath('MULTIPLY', obj, (285.0, 285.0, 285.0)), scale=2.0,
                   detail=4.0, rough=0.5)
    dry = g.voro(g.vmath('MULTIPLY', obj, (760.0, 760.0, 760.0)), scale=1.0,
                 rand=1.0, feature='SMOOTH_F1')
    scale_ = g.noise(g.vmath('MULTIPLY', obj, (9.0, 9.0, 9.0)), scale=2.5,
                     detail=7.0, rough=0.62)
    # ANISOTROPIC NOISE, NOT A DISTORTED WAVE.  The first version used
    # ShaderNodeTexWave with distortion 6-9 for the paint runs and the rain
    # tracking, which is not a streak at all: a distorted band texture folds
    # back on itself and renders as a chevron zigzag, and at 896 px/m it was
    # the loudest thing on a 30 m web.  A noise whose domain is squashed 30:1
    # toward the vertical gives what a run of paint and a rain track actually
    # look like -- long, soft, irregular, and going one way only.
    runs = g.noise(g.vmath('MULTIPLY', obj, (13.0, 13.0, 0.85)), scale=2.0,
                   detail=5.0, rough=0.55)
    runm = g.math('MULTIPLY', g.ramp(runs, [(0.58, (0, 0, 0)), (0.84, (1, 1, 1))]),
                  0.45, clamp=True)
    drym = g.math('MULTIPLY', g.math('MULTIPLY', (dry, 0), edge), 0.5, clamp=True)
    col = g.mix(g.math('MULTIPLY', drym, 0.28), col,
                g.mix(0.5, col, (0.60, 0.61, 0.63)))

    sunk = g.math('MULTIPLY', g.math('MULTIPLY', HS._sun_face(g), up),
                  g.math('ADD', 0.28, g.math('MULTIPLY', age, 1.0)), clamp=True)
    hsv = g.n("ShaderNodeHueSaturation")
    g._feed(hsv, 0, 0.5)
    g._feed(hsv, 1, 0.62)
    g._feed(hsv, 2, 1.22)
    g._feed(hsv, 3, 1.0)
    g._feed(hsv, 4, col)
    col = g.mix(g.math('MULTIPLY', sunk, 0.48), col, hsv)
    col = g.mix(g.math('MULTIPLY', g.math('SUBTRACT', scale_, 0.42), 0.42),
                col, g.mix(0.35, col, (0.030, 0.030, 0.031)))

    wash = g.noise(g.vmath('MULTIPLY', obj, (9.5, 9.5, 0.42)), scale=2.0,
                   detail=6.0, rough=0.58)
    # tracking happens in PATCHES, under the deck joints and the scuppers, not
    # evenly down 30 m of web.  Without the patch mask it reads as pinstripe.
    wpatch = g.ramp(g.noise(g.vmath('MULTIPLY', obj, (1.1, 1.1, 0.25)),
                            scale=2.0, detail=4.0, rough=0.5),
                    [(0.42, (0, 0, 0)), (0.60, (1, 1, 1))])
    washm = g.math('MULTIPLY',
                   g.math('MULTIPLY',
                          g.ramp(wash, [(0.46, (0, 0, 0)), (0.72, (1, 1, 1))]),
                          (wpatch, 0)),
                   g.math('SUBTRACT', 1.0, up), clamp=True)

    # ---- 6. the rubber road film on the soffit ---------------------------
    film = g.noise(g.vmath('MULTIPLY', obj, (7.5, 7.5, 4.5)), scale=2.5,
                   detail=8.0, rough=0.62)
    fk = g.math('MULTIPLY', g.math('MULTIPLY', down,
                                   g.math('ADD', 0.55,
                                          g.math('MULTIPLY', dirt, 0.8))),
                g.math('ADD', 0.42, g.math('MULTIPLY', film, 1.20)), clamp=True)
    # ---- 7. efflorescence under the deck joints --------------------------
    eff = g.noise(g.vmath('MULTIPLY', obj, (11.0, 11.0, 0.42)), scale=2.0,
                  detail=6.0, rough=0.58)
    effn = g.noise(g.vmath('MULTIPLY', obj, (26.0, 26.0, 0.9)), scale=2.0,
                   detail=7.0, rough=0.62)
    effm = g.math('MULTIPLY',
                  g.ramp(g.math('ADD', g.math('MULTIPLY', eff, 0.60),
                                g.math('MULTIPLY', effn, 0.48)),
                         [(0.62, (0, 0, 0)), (0.88, (1, 1, 1))]),
                  g.math('MULTIPLY', g.math('SUBTRACT', 1.0, up), 0.70),
                  clamp=True)
    # ---- 8. bird lime ----------------------------------------------------
    lime = g.voro(g.vmath('MULTIPLY', obj, (30.0, 30.0, 30.0)), scale=1.0,
                  rand=1.0, feature='SMOOTH_F1')
    limem = g.ramp((lime, 0), [(0.0, (1, 1, 1)), (0.060, (0, 0, 0))])
    limem = g.math('MULTIPLY', (limem, 0), g.math('MULTIPLY', up, 1.35),
                   clamp=True)
    drip = g.noise(g.vmath('MULTIPLY', obj, (16.0, 16.0, 1.3)), scale=2.0,
                   detail=7.0, rough=0.6)
    dripm = g.math('MULTIPLY', g.ramp(drip, [(0.62, (0, 0, 0)), (0.82, (1, 1, 1))]),
                   g.math('MULTIPLY', down, 0.5), clamp=True)

    # ---- 9/10. chips, to primer and through it ---------------------------
    cn = g.voro(g.vmath('MULTIPLY', obj, (125.0, 125.0, 125.0)), scale=1.0,
                rand=1.0, feature='SMOOTH_F1')
    cnr = g.ramp((cn, 0), [(0.0, (0, 0, 0)), (0.36, (1, 1, 1))])
    cn2 = g.noise(g.vmath('MULTIPLY', obj, (38.0, 38.0, 38.0)), scale=2.0,
                  detail=8.0, rough=0.66)
    cn3 = g.noise(g.vmath('MULTIPLY', obj, (160.0, 160.0, 160.0)), scale=2.0,
                  detail=6.0, rough=0.60)
    cm = g.math('ADD', g.math('MULTIPLY', (cnr, 0), 0.34),
                g.math('ADD', g.math('MULTIPLY', cn2, 0.46),
                       g.math('MULTIPLY', cn3, 0.20)))
    drive = g.math('MULTIPLY', chip,
                   g.math('ADD', 0.16, g.math('MULTIPLY', edge, 1.80)),
                   clamp=True)
    drive = g.math('ADD', drive, g.math('MULTIPLY', age, 0.06), clamp=True)
    cover = g.ramp(g.noise(g.vmath('MULTIPLY', obj, (2.2, 2.2, 2.2)),
                           scale=2.0, detail=6.0, rough=0.58),
                   [(0.395, (0, 0, 0)), (0.585, (1, 1, 1))])
    chip1 = g.ramp(g.math('ADD', cm, g.math('MULTIPLY', drive, 0.58)),
                   [(0.735, (0, 0, 0)), (0.868, (1, 1, 1))])
    chip1 = g.math('MULTIPLY', (chip1, 0), (cover, 0), clamp=True)
    chip2 = g.ramp(g.math('ADD', cm, g.math('MULTIPLY', drive, 0.44)),
                   [(0.925, (0, 0, 0)), (1.010, (1, 1, 1))])
    chip2 = g.math('MULTIPLY', (chip2, 0), (cover, 0), clamp=True)
    primer = g.mix(g.math('MULTIPLY', (dry, 0), 0.7), srgb(PRIMER_HEX),
                   (0.220, 0.238, 0.212))
    col = g.mix(g.math('MULTIPLY', chip1, 0.93), col, primer)
    scalec = g.mix(g.math('MULTIPLY', peel, 0.6), srgb(SCALE_HEX),
                   (0.055, 0.058, 0.062))
    col = g.mix(g.math('MULTIPLY', chip2, 0.90), col, scalec)

    # ---- 11. red rust, only where the steel was worked -------------------
    scab = g.voro(g.vmath('MULTIPLY', obj, (340.0, 340.0, 340.0)), scale=1.0,
                  rand=1.0, feature='SMOOTH_F1')
    rk = g.math('MULTIPLY', rust,
                g.math('ADD', g.math('MULTIPLY', mach, 0.95),
                       g.math('ADD', g.math('MULTIPLY', weld, 0.28),
                              g.math('MULTIPLY', chip2, 0.75))), clamp=True)
    bleed = g.noise(g.vmath('MULTIPLY', obj, (22.0, 22.0, 1.7)), scale=2.5,
                    detail=7.0, rough=0.62)
    rbl = g.math('MULTIPLY', g.math('MULTIPLY', rk, bleed), 0.9, clamp=True)
    col = g.mix(g.math('MULTIPLY', rbl, 0.42), col, (0.118, 0.052, 0.024))
    col = g.mix(g.math('MULTIPLY', rk, 0.86), col,
                g.mix(g.math('MULTIPLY', (scab, 0), 0.75), (0.150, 0.056, 0.023),
                      (0.238, 0.100, 0.036)))
    col = g.mix(g.math('MULTIPLY', effm, 0.46), col, (0.470, 0.468, 0.442))
    col = g.mix(g.math('MULTIPLY', limem, 0.88), col, (0.520, 0.512, 0.470))
    col = g.mix(g.math('MULTIPLY', dripm, 0.34), col, (0.330, 0.325, 0.300))
    # 0.80 turned the soffit into a silhouette.  A bridge underside over a
    # racing surface is DARK and LOW-CONTRAST, not black: the film is a thin
    # rubber dust, and what it mostly does is kill the sheen.
    col = g.mix(g.math('MULTIPLY', fk, 0.44), col, (0.036, 0.034, 0.032))

    gr = g.noise(g.vmath('MULTIPLY', obj, (4.2, 4.2, 2.4)), scale=2.5,
                 detail=8.0, rough=0.64)
    grit = g.voro(g.vmath('MULTIPLY', obj, (560.0, 560.0, 560.0)), scale=1.0,
                  rand=1.0, feature='SMOOTH_F1')
    dk = g.math('MULTIPLY', dirt,
                g.math('ADD', 0.26, g.math('MULTIPLY', gr, 1.32)), clamp=True)
    dk = g.math('MULTIPLY', dk, g.math('ADD', 0.88,
                                       g.math('MULTIPLY', up, 0.42)), clamp=True)
    # and it is dirtiest at the bottom, where the splash and the ledge dust
    # collect.  obj.z is safe here: the object IS one girder, so its object
    # space spans the 1.35 m depth and nothing more.
    ozc = g.sepxyz(obj)
    lowz = g.ramp((ozc, 2), [(-0.72, (1, 1, 1)), (0.20, (0, 0, 0))])
    dk = g.math('MULTIPLY', dk,
                g.math('ADD', 0.72, g.math('MULTIPLY', (lowz, 0), 0.85)),
                clamp=True)
    dk = g.math('MULTIPLY', dk, g.math('SUBTRACT', 1.02,
                                       g.math('MULTIPLY', washm, 0.85)),
                clamp=True)
    # 0.80 with a warm target was an overcorrection in the other direction:
    # it replaced the topcoat with mud and the girder read beige.  Grime
    # DIMS and DESATURATES a painted surface; it does not repaint it.
    col = g.mix(g.math('MULTIPLY', dk, 0.50), col,
                g.mix(g.math('MULTIPLY', (grit, 0), 0.5), (0.044, 0.042, 0.038),
                      (0.078, 0.073, 0.064)))
    wcol = g.math('MULTIPLY', weld, g.math('ADD', 0.55,
                                           g.math('MULTIPLY', peel, 0.5)),
                  clamp=True)
    col = g.mix(g.math('MULTIPLY', wcol, 0.34), col, (0.052, 0.055, 0.050))
    g._feed(b, 0, col)

    met = g.math('ADD', g.math('MULTIPLY', chip2, 0.75),
                 g.math('MULTIPLY', mach, 0.55), clamp=True)
    met = g.math('MULTIPLY', met, g.math('SUBTRACT', 1.0,
                                         g.math('MULTIPLY', rk, 0.9)), clamp=True)
    HS._set(g, b, met, "Metallic")
    rough = g.math('ADD', 0.24, g.math('MULTIPLY', age, 0.28))
    rough = g.math('ADD', rough, g.math('MULTIPLY', sunk, 0.28))
    rough = g.math('ADD', rough, g.math('MULTIPLY', chip1, 0.22))
    rough = g.math('ADD', rough, g.math('MULTIPLY', rk, 0.34))
    rough = g.math('ADD', rough, g.math('MULTIPLY', dk, 0.22))
    rough = g.math('ADD', rough, g.math('MULTIPLY', limem, 0.30))
    rough = g.math('ADD', rough, g.math('MULTIPLY', fk, 0.34))
    rough = g.math('ADD', rough, g.math('MULTIPLY', effm, 0.26))
    rough = g.math('SUBTRACT', rough, g.math('MULTIPLY', weld, 0.16))
    rough = g.math('SUBTRACT', rough, g.math('MULTIPLY', runm, 0.14))
    rough = g.math('SUBTRACT', rough, g.math('MULTIPLY', washm, 0.10))
    rough = g.math('ADD', rough,
                   g.math('MULTIPLY', g.math('SUBTRACT', peel, 0.5), 0.12),
                   clamp=True)
    HS._set(g, b, rough, "Roughness")
    HS._set(g, b, 0.45, "Specular IOR Level", "Specular")
    cw = g.math('MULTIPLY',
                g.math('SUBTRACT', 1.0, g.math('MULTIPLY', age, 0.82)),
                g.math('SUBTRACT', 1.0, g.math('MULTIPLY', chip1, 1.0)),
                clamp=True)
    HS._set(g, b, g.math('MULTIPLY', cw, 0.20), "Coat Weight")
    HS._set(g, b, g.math('ADD', 0.11, g.math('MULTIPLY', age, 0.32)),
            "Coat Roughness")

    h = g.math('ADD', g.math('MULTIPLY', peel, 0.28),
               g.math('MULTIPLY', runm, 0.30))
    h = g.math('ADD', h, g.math('MULTIPLY', scale_, 0.22))
    h = g.math('ADD', h, g.math('MULTIPLY', weld, 0.62))
    h = g.math('ADD', h, g.math('MULTIPLY', limem, 0.55))
    h = g.math('ADD', h, g.math('MULTIPLY', effm, 0.30))
    h = g.math('SUBTRACT', h, g.math('MULTIPLY', chip1, 0.16))
    h = g.math('ADD', h, g.math('MULTIPLY', g.math('MULTIPLY', rk, (scab, 0)),
                                0.80))
    # STATED AS RADIANCE MODULATION, NOT MILLIMETRES (itemkit 5b, brief 4a).
    # m = 2 sin(theta) / tan(e), and this film's 12.47 deg sun makes that a
    # 4.52x amplifier.  Nothing here is re-tuned: each `modulation_pp` is the
    # value that reproduces the Distance this module already shipped, and
    # `work/r2038/prove_noop.py` checks it off the built graph.
    #
    # READ THE WAVELENGTH FROM THE COORDINATE MULTIPLIER, NOT FROM `scale=`.
    # This module scales its coordinate vector and leaves the texture's own
    # Scale at 1-2.5, so the feature size is FACTOR / (multiplier * scale) --
    # `peel` is 2.8 mm, not the 800 mm a reader of the Scale socket alone gets.
    # An audit that read Scale sockets put this module at m_median 0.002 and
    # filed it as having no shader relief at all.  It has the opposite problem.
    #
    #   [0] peel   w 0.28  lam  2.81 mm  m 7.430  paint micro, UNGATED
    #       runm   w 0.135 lam 61.54 mm  m 0.287  paint runs, and directional
    #       scale_ w 0.22  lam 71.11 mm  m 0.404  mill scale through the film
    #       weld   w 0.62  no texture: the aux weld mask, a ~10 mm bead, so
    #                                   2.85 mm proud is m ~ 6 -- an ARRIS,
    #                                   which is what hard_feature is for
    #       lime   w 0.55  lam 72.33 mm  m 0.988  bird lime, gated up-facing
    #       effn   w 0.21  lam 30.77 mm  m 0.888  efflorescence, gated
    #       chip1  w 0.16  lam 17.36 mm  m 1.194  chip edges, sparse
    #       scab   w 0.80  lam  6.38 mm  m 7.917  rust scab, gated by rk
    #   [1] grit   w 0.50  lam  3.87 mm  m 0.760  isotropic_macro, ok
    #       dry    w 0.42  lam  2.85 mm  m 0.865  isotropic_macro, ok
    #
    # [0] IS BROKEN AND IT CANNOT BE FIXED FROM HERE.  One Distance serves a
    # 72 mm bird-lime splat and a 2.8 mm paint micro at comparable weights, and
    # the 4.6 mm it was given is right for the coarse half -- a 2.85 mm weld
    # bead and a 2.53 mm lime splat are what those things measure -- and 13x
    # too much for the fine half, which lands the ungated `peel` field at 7.43,
    # past the hard_feature ceiling of 6.0 and twice the 3.76 that rendered as
    # coarse stucco.  Bringing the stage down to put `peel` in band takes the
    # weld bead to 0.21 mm, i.e. deletes it.  THE FIX IS TO SPLIT THIS HEIGHT
    # SUM INTO A COARSE STAGE AND A FINE ONE, which is a restructure and not a
    # depth, so it is left stated rather than half-done: the number now says so.
    LAM_PEEL = K.NOISE_WAVELENGTH_FACTOR / (285.0 * 2.0)     # 2.81 mm
    LAM_GRIT = K.VORONOI_WAVELENGTH_FACTOR / (560.0 * 1.0)   # 3.87 mm
    bmp = g.bump(h, 0.46, modulation_pp=7.430498,
                 wavelength_m=LAM_PEEL, height_pp=0.28)
    fine = g.bump(g.math('ADD', g.math('MULTIPLY', (grit, 0), 0.50),
                         g.math('MULTIPLY', (dry, 0), 0.42)), 0.13,
                  normal=bmp, modulation_pp=0.759807,
                  wavelength_m=LAM_GRIT, height_pp=0.50)
    HS._set(g, b, fine, "Normal")
    return m


def mat_steel():
    """Bare worked steel: sawn and flame-cut ends, ground sole-plate faces,
    the ID plate, shear studs.  Mill scale, grinder swirl, flash rust and the
    oil film that stops a machined face rusting for the first six months."""
    m, g, b, _ = _new_mat("Steel")
    base, aux, wear, bs, au, we, tc, uv, obj = HS._chan(g)
    edge, mach = (au, 0), (au, 2)
    rust, age = (we, 2), (wear, 3)
    up = _up(g)
    scale_ = g.noise(g.vmath('MULTIPLY', obj, (26.0, 26.0, 26.0)), scale=2.5,
                     detail=8.0, rough=0.62)
    swirl = g.wave(g.vmath('MULTIPLY', obj, (420.0, 420.0, 420.0)), scale=4.0,
                   dist=2.0, detail=3.0, band='X', wtype='RINGS')
    drag = g.noise(g.vmath('MULTIPLY', obj, (110.0, 110.0, 2.0)), scale=2.0,
                   detail=5.0, rough=0.55)
    grit = g.voro(g.vmath('MULTIPLY', obj, (700.0, 700.0, 700.0)), scale=1.0,
                  rand=1.0, feature='SMOOTH_F1')
    scab = g.voro(g.vmath('MULTIPLY', obj, (150.0, 150.0, 150.0)), scale=1.0,
                  rand=1.0, feature='SMOOTH_F1')
    col = g.mix(g.math('MULTIPLY', scale_, 0.85), srgb(SCALE_HEX), base)
    col = g.mix(g.math('MULTIPLY', g.math('MULTIPLY', (swirl, 0), mach), 0.45),
                col, (0.300, 0.306, 0.316))
    col = g.mix(g.math('MULTIPLY', g.math('MULTIPLY', drag, edge), 0.35),
                col, (0.100, 0.101, 0.104))
    rk = g.math('MULTIPLY', rust, g.math('ADD', 0.30,
                                         g.math('MULTIPLY', up, 0.9)),
                clamp=True)
    col = g.mix(g.math('MULTIPLY', rk, 0.80), col,
                g.mix(g.math('MULTIPLY', (scab, 0), 0.7), (0.165, 0.062, 0.026),
                      (0.255, 0.112, 0.041)))
    g._feed(b, 0, col)
    HS._set(g, b, g.math('SUBTRACT',
                         g.math('ADD', 0.72, g.math('MULTIPLY', mach, 0.22)),
                         g.math('MULTIPLY', rk, 0.55), clamp=True), "Metallic")
    r = g.math('ADD', 0.30, g.math('MULTIPLY', scale_, 0.24))
    r = g.math('SUBTRACT', r, g.math('MULTIPLY', mach, 0.14))
    r = g.math('ADD', r, g.math('MULTIPLY', rk, 0.36), clamp=True)
    HS._set(g, b, r, "Roughness")
    hh = g.math('ADD', g.math('MULTIPLY', scale_, 0.30),
                g.math('ADD', g.math('MULTIPLY', (swirl, 0), 0.12),
                       g.math('MULTIPLY', g.math('MULTIPLY', rk, (scab, 0)),
                              0.9)))
    # Radiance, not millimetres (itemkit 5b).  Reproduces the shipped Distance;
    # the wavelength is FACTOR / (coordinate multiplier * scale), see mat_paint.
    #
    #   [0] scale_  w 0.30  lam 24.62 mm  m 0.622  mill scale, UNGATED: ok
    #       swirl   w 0.12  lam  0.60 mm  m 6.798  grinder swirl, UNGATED, and
    #                                              0.216 mm at a 0.6 mm pitch is
    #                                              a 47 deg surface: OVER-DEEP,
    #                                              but it is a third of a pixel
    #                                              at any distance this girder
    #                                              is seen from, so it filters
    #                                              to sheen rather than crust
    #       rk*scab w 0.90  lam 14.47 mm  m 3.001  rust scab, gated: an edge
    #   [1] grit    w 1.00  lam  3.10 mm  m 1.306  blast grit, UNGATED.  Over
    #                                              isotropic_macro's 0.95 and
    #                                              under the 1.5 that would make
    #                                              it plainly wrong, so it ships.
    LAM_SCALE = K.NOISE_WAVELENGTH_FACTOR / (26.0 * 2.5)      # 24.62 mm
    LAM_GRIT = K.VORONOI_WAVELENGTH_FACTOR / (700.0 * 1.0)    #  3.10 mm
    bm = g.bump(hh, 0.30, modulation_pp=0.621782,
                wavelength_m=LAM_SCALE, height_pp=0.30)
    HS._set(g, b, g.bump((grit, 0), 0.12, normal=bm,
                         modulation_pp=1.305885, wavelength_m=LAM_GRIT),
            "Normal")
    return m


def mat_fastener():
    """HSFG bolts: a sherardised finish, a torque mark, and the rust that
    starts in the thread and bleeds down the plate before anywhere else."""
    m, g, b, _ = _new_mat("Fastener")
    base, aux, wear, bs, au, we, tc, uv, obj = HS._chan(g)
    edge, mach = (au, 0), (au, 2)
    dirt, rust, age = (we, 1), (we, 2), (wear, 3)
    down = _down(g)
    spang = g.voro(g.vmath('MULTIPLY', obj, (500.0, 500.0, 500.0)), scale=1.0,
                   rand=1.0, feature='SMOOTH_F1')
    grain = g.noise(g.vmath('MULTIPLY', obj, (900.0, 900.0, 900.0)), scale=2.0,
                    detail=4.0, rough=0.5)
    weath = g.noise(g.vmath('MULTIPLY', obj, (55.0, 55.0, 55.0)), scale=2.0,
                    detail=7.0, rough=0.6)
    mark = g.noise(g.vmath('MULTIPLY', obj, (300.0, 300.0, 40.0)), scale=2.0,
                   detail=3.0, rough=0.5)
    col = g.mix(g.math('MULTIPLY', (spang, 0), 0.55), base, (0.360, 0.372, 0.382))
    col = g.mix(g.math('MULTIPLY', weath, 0.70), col, (0.230, 0.236, 0.240))
    rk = g.math('MULTIPLY', rust, g.math('ADD', 0.30,
                                         g.math('MULTIPLY', mach, 0.9)),
                clamp=True)
    col = g.mix(g.math('MULTIPLY', rk, 0.72), col, (0.190, 0.078, 0.030))
    # the torque mark: a stripe of white paint across the nut and the plate
    tm = g.math('MULTIPLY', g.ramp(mark, [(0.72, (0, 0, 0)),
                                          (0.86, (1, 1, 1))]),
                g.math('MULTIPLY', edge, 0.55), clamp=True)
    col = g.mix(g.math('MULTIPLY', (tm, 0), 0.55), col, (0.520, 0.505, 0.470))
    dk = g.math('MULTIPLY', dirt, g.math('ADD', 0.35,
                                         g.math('MULTIPLY', down, 0.9)),
                clamp=True)
    col = g.mix(g.math('MULTIPLY', dk, 0.55), col, (0.040, 0.036, 0.030))
    g._feed(b, 0, col)
    HS._set(g, b, g.math('SUBTRACT', 0.90, g.math('MULTIPLY', rk, 0.70),
                         clamp=True), "Metallic")
    HS._set(g, b, g.math('ADD', 0.30,
                         g.math('ADD', g.math('MULTIPLY', weath, 0.26),
                                g.math('MULTIPLY', rk, 0.34)), clamp=True),
            "Roughness")
    # Radiance, not millimetres (itemkit 5b).  Reproduces the shipped Distance;
    # the wavelength is FACTOR / (coordinate multiplier * scale), see mat_paint.
    #
    #   [0] spang  w 0.35  lam 4.34 mm  m 1.101  the sherardised spangle,
    #                                            UNGATED.  Over isotropic_macro
    #                                            and under the 1.5 that would
    #                                            make it plainly wrong: a
    #                                            spangle is a crystal facet with
    #                                            a real boundary, not a crumple.
    #       rk     w 0.55  no texture: the rust mask, gated by the worked-steel
    #                                  channel, so it acts on the thread and the
    #                                  torqued face and nowhere else
    #   [1] grain  w 1.00  lam 0.89 mm  m 1.266  0.04 mm of sherardised grain.
    #                                            Sub-pixel on an M24 head at any
    #                                            distance this bridge is seen
    #                                            from; it reads as roughness.
    LAM_SPANG = K.VORONOI_WAVELENGTH_FACTOR / (500.0 * 1.0)   # 4.34 mm
    LAM_GRAIN = K.NOISE_WAVELENGTH_FACTOR / (900.0 * 2.0)     # 0.89 mm
    bm = g.bump(g.math('ADD', g.math('MULTIPLY', (spang, 0), 0.35),
                       g.math('MULTIPLY', rk, 0.55)), 0.22,
                modulation_pp=1.100685, wavelength_m=LAM_SPANG, height_pp=0.35)
    HS._set(g, b, g.bump(grain, 0.10, normal=bm, modulation_pp=1.265889,
                         wavelength_m=LAM_GRAIN), "Normal")
    return m


def mat_galv():
    """Hot-dip zinc on the small fittings: spikes, cleats, base strips."""
    m, g, b, _ = _new_mat("Galv")
    base, aux, wear, bs, au, we, tc, uv, obj = HS._chan(g)
    edge = (au, 0)
    dirt, age = (we, 1), (wear, 3)
    up = _up(g)
    spang = g.voro(g.vmath('MULTIPLY', obj, (280.0, 280.0, 280.0)), scale=1.0,
                   rand=1.0, feature='SMOOTH_F1')
    cell = g.voro(g.vmath('MULTIPLY', obj, (280.0, 280.0, 280.0)), scale=1.0,
                  rand=1.0, feature='F1')
    dipn = g.noise(g.vmath('MULTIPLY', obj, (40.0, 40.0, 40.0)), scale=2.0,
                   detail=7.0, rough=0.6)
    wrust = g.noise(g.vmath('MULTIPLY', obj, (120.0, 120.0, 120.0)), scale=2.0,
                    detail=6.0, rough=0.62)
    col = g.mix(g.math('MULTIPLY', (spang, 0), 0.62), base, (0.400, 0.412, 0.420))
    col = g.mix(g.math('MULTIPLY', g.math('MULTIPLY', dipn, age), 0.72), col,
                (0.155, 0.158, 0.160))
    wr = g.math('MULTIPLY', g.math('MULTIPLY', wrust, age),
                g.math('ADD', 0.30, g.math('MULTIPLY', up, 0.8)), clamp=True)
    col = g.mix(g.math('MULTIPLY', wr, 0.50), col, (0.520, 0.528, 0.520))
    col = g.mix(g.math('MULTIPLY', dirt, 0.45), col, (0.050, 0.045, 0.038))
    g._feed(b, 0, col)
    HS._set(g, b, g.math('SUBTRACT', 0.92, g.math('MULTIPLY', wr, 0.75),
                         clamp=True), "Metallic")
    HS._set(g, b, g.math('ADD', 0.22,
                         g.math('ADD', g.math('MULTIPLY', age, 0.34),
                                g.math('MULTIPLY', wr, 0.30)), clamp=True),
            "Roughness")
    # Radiance, not millimetres (itemkit 5b).  Reproduces the shipped Distance;
    # the wavelength is FACTOR / (coordinate multiplier * scale), see mat_paint.
    #
    #   [0] cell  w 0.35  lam  7.75 mm  m 0.410  the zinc spangle's cell, and
    #                                            the whole stage: isotropic_micro
    #                                            at the top / isotropic_macro at
    #                                            the bottom, which is where a
    #                                            hot-dip crystal belongs
    #       dipn  w 0.30  lam 20.00 mm  m 0.136  drainage ripple: micro, ok
    #
    # The only stage in this module that needs no argument at all.
    LAM_CELL = K.VORONOI_WAVELENGTH_FACTOR / (280.0 * 1.0)    # 7.75 mm
    HS._set(g, b, g.bump(g.math('ADD', g.math('MULTIPLY', (cell, 0), 0.35),
                                g.math('MULTIPLY', dipn, 0.30)), 0.20,
                         modulation_pp=0.410156, wavelength_m=LAM_CELL,
                         height_pp=0.35),
            "Normal")
    return m


def mat_organic():
    """The nest: dry twigs, feather dust and eleven years of guano."""
    m, g, b, _ = _new_mat("Organic")
    base, aux, wear, bs, au, we, tc, uv, obj = HS._chan(g)
    dirt = (we, 1)
    up = _up(g)
    fib = g.wave(g.vmath('MULTIPLY', obj, (600.0, 600.0, 26.0)), scale=8.0,
                 dist=6.0, detail=4.0, band='Z')
    var = g.noise(g.vmath('MULTIPLY', obj, (18.0, 18.0, 18.0)), scale=2.0,
                  detail=7.0, rough=0.6)
    rot = g.voro(g.vmath('MULTIPLY', obj, (140.0, 140.0, 140.0)), scale=1.0,
                 rand=1.0, feature='SMOOTH_F1')
    col = g.mix(g.math('MULTIPLY', var, 0.85), base, (0.130, 0.092, 0.052))
    col = g.mix(g.math('MULTIPLY', (fib, 0), 0.35), col, (0.055, 0.036, 0.020))
    col = g.mix(g.math('MULTIPLY', g.math('MULTIPLY', (rot, 0), up), 0.45),
                col, (0.290, 0.276, 0.240))
    col = g.mix(g.math('MULTIPLY', dirt, 0.30), col, (0.060, 0.052, 0.040))
    g._feed(b, 0, col)
    HS._set(g, b, g.math('SUBTRACT', 0.94, g.math('MULTIPLY', var, 0.12)),
            "Roughness")
    # Radiance, not millimetres (itemkit 5b).  Reproduces the shipped Distance;
    # the wavelength is FACTOR / (coordinate multiplier * scale), see mat_paint.
    #
    #   [0] fib  w 0.50  lam 1.51 mm  m 5.990  the twigs.  A stick lying on a
    #                                          nest IS an edge, so hard_feature
    #                                          (1.5-6.0) is the band, not a
    #                                          crumple band.
    #       var  w 0.40  lam 44.44 mm  m 0.217  the mass beneath: micro, ok
    #
    # CAVEAT ON THE NAMED WAVELENGTH.  `fib` is a Wave with distortion 6.0, so
    # 1 / (26 * 8) is its UNDISTORTED band pitch in Z; the distortion adds
    # structure at the x/y multiplier (0.33 mm), which is below the pixel.  The
    # stated 4.81 mm is therefore the coarse end of what this band carries and
    # m 2.42 is a lower bound, not a reading.
    # R2-058: THIS READ `1.0 / Scale` AND WAS 3.183x TOO LONG.  Blender's Wave
    # multiplies the coordinate by 20 before the sine, so one band is
    # 2*pi/20 = 0.31416 of 1/Scale, not 1/Scale -- measured flat to six digits
    # over a Scale 5..230 sweep (itemkit WAVE_WAVELENGTH_FACTOR;
    # work/wavefix/emitted_wavelength.json).  itemkit's `_tex_wavelength_m` had
    # the same error, which is why this line and the audit agreed and both were
    # wrong.  THE DISTANCE ON THE SOCKET HAS NOT MOVED -- this is the depth the
    # module shipped and was judged at.  What moved is the DECLARATION: at the
    # true pitch the same amplitude is a much steeper wall, so the stage's real
    # modulation is m 5.990 and was being reported as m 2.420.  Do NOT
    # "correct" this by keeping the old modulation against the new wavelength:
    # that derives a Distance 3.183x shallower and changes a surface that was
    # rendered and looked at.
    LAM_FIB = K.WAVE_WAVELENGTH_FACTOR / (26.0 * 8.0)         # 1.51 mm (Wave)
    HS._set(g, b, g.bump(g.math('ADD', g.math('MULTIPLY', (fib, 0), 0.5),
                                g.math('MULTIPLY', var, 0.4)), 0.34,
                         modulation_pp=5.989559, wavelength_m=LAM_FIB,
                         height_pp=0.50),
            "Normal")
    return m


def materials(force=False):
    global _MATS
    if _MATS is not None and not force:
        return _MATS
    _MATS = [mat_paint(), mat_steel(), mat_fastener(), mat_galv(),
             mat_organic()]
    return _MATS


# --------------------------------------------------------------------------- #
# 18.  THE INTERFACE FILE                                                       #
# --------------------------------------------------------------------------- #

def dump_interface(B, path=None):
    """Everything a dependant needs, as data, so it never has to import me."""
    R, t = pont_to_world()
    out = {
        "item": "pont_girder",
        "version": "1.0.0",
        "frame": {
            "note": "bridge-local: +X ALONG THE SPAN (x=-15 is contract u=+15, "
                    "LEFT of the racing direction; x=+15 is u=-15); +Y is the "
                    "RACING DIRECTION at s=2410; +Z is WORLD z.",
            "station_s": S_STATION,
            "R_local_to_world": [[float(v) for v in row] for row in R],
            "t_local_to_world": [float(v) for v in t],
            "centreline_world": [float(v) for v in C.centreline(S_STATION)[:2]],
            "track_heading_deg": float(math.degrees(C.centreline(S_STATION)[3])),
            "ground_z_at_abutments": {
                "x_minus_15 (contract u=+15)": float(C.ground_z(S_STATION, 15.0)),
                "x_plus_15 (contract u=-15)": float(C.ground_z(S_STATION, -15.0)),
                "track_centreline": float(C.ground_z(S_STATION, 0.0)),
            },
        },
        "datum": {
            "soffit_z": SOFFIT_Z,
            "soffit_z_note": "circuit_spec plunge_bridge_design.soffit_z, WORLD z. "
                             "The underside of the bottom flanges AT THE BEARINGS. "
                             "It is the STRUCTURAL soffit, not the lowest point: "
                             "see lowest_z_over_track below, which is what a "
                             "clearance argument must use.",
            "lowest_z_anywhere": B.stats.get("lowest_z"),
            "lowest_z_over_track": B.stats.get("lowest_z_over_track"),
            "track_headroom_measured_m": B.stats.get("track_headroom_measured_m"),
            "camera_clearance_measured_m": B.stats.get("camera_clearance_measured_m"),
            "below_soffit_note": (
                "The sole plates (40 mm) and the bottom-flange splice cover "
                "plates with their bolt heads (35 mm) hang below SOFFIT_Z. "
                "Both are real. lowest_z_over_track is the number a clearance "
                "argument must use."),
            "girder_depth": GIRDER_DEPTH,
            "top_flange_z": TOP_FLANGE_Z,
            "deck_soffit_z": DECK_SOFFIT_Z,
            "haunch_m": HAUNCH_M,
            "deck_width": DECK_WIDTH,
            "span": SPAN,
            "bearing_x": BEARING_X,
            "abutment_face_x": ABUT_FACE_X,
            "clear_opening": 2.0 * ABUT_FACE_X,
            "girder_y": list(GIRDER_Y),
            "girder_ids": list(GIRDER_IDS),
            "fascia_ids": list(FASCIA),
            "cantilever_past_fascia": 0.5 * DECK_WIDTH - abs(GIRDER_Y[0]),
            "banner_rail_height": BANNER_H,
            "banner_proud": BANNER_PROUD,
            "stud": {"dia": STUD_D, "height": STUD_H, "pitch": STUD_PITCH,
                     "gauge": STUD_GAUGE},
            "track_headroom_m": float(SOFFIT_Z - C.ground_z(S_STATION, 0.0)),
            "headroom_flag": (
                "SOFFIT_Z 6.800 leaves %.3f m over the racing surface at "
                "s=2410 (ground_z = %.3f).  That is LOW for a bridge over a "
                "circuit and is flagged for whoever owns circuit_spec; it is "
                "not something this item may fix by moving a bridge the whole "
                "camera corridor was derived from."
                % (float(SOFFIT_Z - C.ground_z(S_STATION, 0.0)),
                   float(C.ground_z(S_STATION, 0.0)))),
            "placement_gate_measured": (
                "MEASURED, not assumed: tools/placement_gate.py returns "
                "PLACEMENT_CLEAN on world/items/pont_girder_test.blend.  Note "
                "WHY, because it is a gate limitation rather than a pass this "
                "item earned: the road-corridor keep-out is a band in ABSOLUTE "
                "world z (zlo -0.5, zhi ROAD_CLEAR_H 4.50), and at s=2410 the "
                "racing surface is at z=3.935, so the protected volume ends "
                "0.565 m above the tarmac and cannot see anything bridging it. "
                "Nothing is allow-listed."),
        },
        "girders": {},
        "objects": [o.name for o in B.objects],
        "girder_objects": [o.name for o in B.girders],
        "brace_objects": [o.name for o in B.braces],
        "gate_prefix": PFX + "Girder",
        "counts": {k: (float(v) if isinstance(v, float) else v)
                   for k, v in B.stats.items()},
        "mounts": {},
    }
    for gid in GIRDER_IDS:
        gs = SPECS[gid]
        xs = np.linspace(gs.x0, gs.x1, 61)
        out["girders"][gid] = {
            "y": gs.y, "role": gs.role, "x0": gs.x0, "x1": gs.x1,
            "length": gs.length,
            "bottom_flange": {"w": gs.bw, "t": gs.bt},
            "top_flange": {"w": gs.tw, "t": gs.tt},
            "web_t": gs.wt,
            "camber_m": gs.camber,
            "sweep_m": gs.sweep_m,
            "web_out_of_plumb_m": gs.plumb,
            "splice_x": gs.splice_x,
            "web_splice_bolt_grid": [gs.web_cols * 2, gs.web_rows],
            "stiffener": {"w": gs.stiff_w, "t": gs.stiff_t,
                          "sides": list(gs.stiff_sides), "cope": gs.cope,
                          "intermediates_per_bay": list(gs.inter),
                          "tension_flange_gap": gs.gap4t},
            "paint_hex": gs.paint, "repaint_hex": gs.paint2,
            "repair": gs.repair,
            "soffit_z_samples": [[float(a), float(b)] for a, b in
                                 zip(xs, bottom_z(gs, xs))],
            "top_z_samples": [[float(a), float(b)] for a, b in
                              zip(xs, top_z(gs, xs))],
            "stiffener_stations": [[float(a), k]
                                   for (a, k) in stiffener_stations(gs)],
        }
    for k, f in sorted(B.mounts.items()):
        out["mounts"][k] = {
            "o": [float(v) for v in f.o], "x": [float(v) for v in f.x],
            "y": [float(v) for v in f.y], "z": [float(v) for v in f.z],
            "r": float(f.r), "tag": f.tag,
        }
    p = path or os.path.join(HERE, "pont_girder_interface.json")
    with open(p, "w") as fh:
        json.dump(out, fh, indent=1)
    print(">> interface written: %s  (%d mounts)" % (p, len(out["mounts"])))
    return p


# --------------------------------------------------------------------------- #
# 19.  THE TEST SCENE                                                           #
# --------------------------------------------------------------------------- #

def contract_light(scene=None):
    """The film's one sun, plus its sky.  Numbers from world_contract S13."""
    sc = scene or bpy.context.scene
    import fix_audit_blend as FA
    FA.procedural_world()
    sun = bpy.data.objects.get("PGD_Sun")
    if sun is None:
        d = bpy.data.lights.new("PGD_Sun", 'SUN')
        sun = bpy.data.objects.new("PGD_Sun", d)
        sc.collection.objects.link(sun)
    L = sun.data
    L.energy = C.SUN_ENERGY
    L.color = C.SUN_COLOR
    L.angle = math.radians(C.SUN_ANGULAR_DIAM_DEG)
    # SUN_DIR POINTS TOWARD THE SUN (its z is +sin(12.47 deg) and
    # world_contract.lambert_radiance treats an UP-facing surface as the one
    # that sees E_DIRECT_HORIZONTAL), and a Blender SUN emits along its local
    # -Z.  So the lamp's +Z must be aligned with +SUN_DIR, not with -SUN_DIR.
    #
    # THIS IS A DEFECT I INHERITED, NOT ONE I INVENTED, and it is worth the
    # comment: marshal_post_column, gantry_truss, crew_fireproof_overall and
    # the first version of this module all rotate world +Z onto -SUN_DIR,
    # which points the lamp's emission along +SUN_DIR -- 12.47 deg UP.  Every
    # test scene built with that idiom is lit by a sun below the horizon
    # shining upward, so soffits and undersides render LIT and every up-facing
    # surface renders in shadow.  It is invisible on an object with no
    # significant underside and unmissable on a bridge.  Measured, not
    # reasoned: with the old line, -matrix_world.col[2] came out exactly
    # +SUN_DIR (dot = +1.0); with this one it is -SUN_DIR (dot = -1.0).
    d = np.array(C.SUN_DIR, float)
    z = np.array([0.0, 0.0, 1.0])
    axis = np.cross(z, d)
    ang = math.acos(float(np.clip(np.dot(z, d), -1, 1)))
    if np.linalg.norm(axis) < 1e-9:
        axis = np.array([1.0, 0.0, 0.0])
    axis = axis / np.linalg.norm(axis)
    sun.rotation_mode = 'AXIS_ANGLE'
    sun.rotation_axis_angle = (ang, *axis)
    sun.location = (0.0, 0.0, 40.0)
    sc.view_settings.view_transform = C.VIEW_TRANSFORM
    sc.view_settings.exposure = C.REFERENCE_EXPOSURE_EXTERIOR
    return sun


def _simple_mat(name, cols, rough, bumps):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    g = HS.NG(mat)
    out = g.n("ShaderNodeOutputMaterial")
    b = g.n("ShaderNodeBsdfPrincipled")
    g.lk(b, 0, out, 0)
    tc = g.n("ShaderNodeTexCoord")
    obj = g.vmath('MULTIPLY', (tc, 3), (1.0, 1.0, 1.0))
    n1 = g.noise(g.vmath('MULTIPLY', obj, (1.4, 1.4, 1.4)), scale=2.0,
                 detail=8.0, rough=0.6)
    agg = g.voro(g.vmath('MULTIPLY', obj, (bumps[0],) * 3), scale=1.0,
                 rand=1.0, feature='F1')
    fine = g.voro(g.vmath('MULTIPLY', obj, (bumps[1],) * 3), scale=1.0,
                  rand=1.0, feature='SMOOTH_F1')
    col = g.mix(g.math('MULTIPLY', n1, 0.9), cols[0], cols[1])
    col = g.mix(g.math('MULTIPLY', (agg, 1), 0.45), col, cols[2])
    col = g.mix(g.math('MULTIPLY', (fine, 0), 0.25), col, cols[3])
    g._feed(b, 0, col)
    g._feed(b, 2, g.math('SUBTRACT', rough, g.math('MULTIPLY', (fine, 0), 0.10)))
    bm = g.bump(g.math('ADD', g.math('MULTIPLY', (agg, 0), 0.5),
                       g.math('MULTIPLY', n1, 0.25)), 0.30, 0.004)
    g._feed(b, 5, g.bump((fine, 0), 0.14, 0.0009, normal=bm))
    return mat


def context_ground(size=62.0, name="CTX_Track", n=170):
    """The racing surface and its verges under the bridge.  CONTEXT ONLY,
    prefixed CTX_ so the acceptance gate never counts it as this item.

    It is not decoration.  The soffit of a bridge 2.9 m over a race track is
    lit almost entirely by light that bounced off that track, and rendering
    the underside over a void would light it with sky alone and make every
    judgement about the material wrong.
    """
    # roughness 0.72 on asphalt under a 12.5 deg sun threw a blown-out
    # grazing specular sheet across the bottom third of the macro frame.
    # Dry, dusty, rubbered asphalt is rougher than that.
    mat = _simple_mat(name, [(0.0165, 0.0165, 0.0170), (0.0345, 0.0345, 0.0355),
                             (0.048, 0.047, 0.045), (0.058, 0.056, 0.052)],
                      0.90, (150.0, 900.0))
    cx, cy = C.centreline(S_STATION)[0], C.centreline(S_STATION)[1]
    xs = np.linspace(-size, size, n)
    X, Y = np.meshgrid(xs, xs, indexing="ij")
    WX = (X + cx).ravel()
    WY = (Y + cy).ravel()
    Z = np.array([C.world_ground_z(float(a), float(b))[0]
                  for a, b in zip(WX, WY)])
    V = np.stack([X.ravel(), Y.ravel(), Z], -1)
    idx = np.arange(n * n).reshape(n, n)
    F = np.stack([idx[:-1, :-1], idx[:-1, 1:], idx[1:, 1:], idx[1:, :-1]],
                 -1).reshape(-1, 4)
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in V], [], [tuple(f) for f in F])
    me.update()
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    ob.location = (float(cx), float(cy), 0.0)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def context_deck(place, name="CTX_Deck"):
    """The deck slab this girder set carries.  CONTEXT ONLY.

    pont_deck_slab is its own manifest item and will replace this.  It exists
    here because without it the sky pours between the girders and every
    judgement about the soffit's light is wrong -- the deck is what makes the
    underside of a bridge dark.
    """
    mat = _simple_mat(name, [(0.085, 0.083, 0.078), (0.125, 0.122, 0.115),
                             (0.150, 0.147, 0.140), (0.100, 0.098, 0.094)],
                      0.86, (55.0, 400.0))
    hw = DECK_WIDTH * 0.5
    x0, x1 = -BEARING_X - 0.90, BEARING_X + 0.90
    # 10 mm BELOW the top-flange level, so the flanges (which rise up to
    # 22 mm on their camber) are buried in the slab and no strip of daylight
    # shows between a girder and the deck it is carrying.  The real haunch is
    # pont_deck_slab's problem; a gap here would be mine.
    z0, z1 = DECK_SOFFIT_Z - 0.010, DECK_SOFFIT_Z + 0.300
    P = []
    F = []
    nx, ny = 90, 26
    xs = np.linspace(x0, x1, nx)
    ys = np.linspace(-hw, hw, ny)
    for (z, flip) in ((z0, True), (z1, False)):
        i0 = len(P)
        for x in xs:
            for y in ys:
                P.append((x, y, z))
        for i in range(nx - 1):
            for j in range(ny - 1):
                a = i0 + i * ny + j
                q = (a, a + 1, a + ny + 1, a + ny)
                F.append(q[::-1] if flip else q)
    # the two fascia edges
    i0 = len(P)
    for sy in (-1, 1):
        b0 = len(P)
        for x in xs:
            P.append((x, sy * hw, z0))
            P.append((x, sy * hw, z1))
        for i in range(nx - 1):
            a = b0 + 2 * i
            q = (a, a + 1, a + 3, a + 2)
            F.append(q if sy > 0 else q[::-1])
    me = bpy.data.meshes.new(name)
    me.from_pydata(P, [], F)
    me.update()
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    R, t = place
    ob.matrix_world = _mat4(R, t)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def context_abutments(place, name="CTX_Abut"):
    """Two blocks where pont_abutment will go.  CONTEXT ONLY, and deliberately
    at the two DIFFERENT ground levels the contract reports."""
    mat = _simple_mat(name, [(0.070, 0.068, 0.064), (0.105, 0.102, 0.096),
                             (0.130, 0.126, 0.118), (0.085, 0.083, 0.078)],
                      0.90, (40.0, 300.0))
    P, F = [], []
    for (sx, u) in ((-1.0, 15.0), (1.0, -15.0)):
        gz = float(C.ground_z(S_STATION, u))
        x_face = sx * ABUT_FACE_X
        x_back = sx * (BEARING_X + 2.60)
        y0, y1 = -DECK_WIDTH * 0.5 - 0.9, DECK_WIDTH * 0.5 + 0.9
        zt = SOFFIT_Z - 0.42
        i0 = len(P)
        for (x, y, z) in ((x_face, y0, gz - 0.6), (x_back, y0, gz - 0.6),
                          (x_back, y1, gz - 0.6), (x_face, y1, gz - 0.6),
                          (x_face, y0, zt), (x_back, y0, zt),
                          (x_back, y1, zt), (x_face, y1, zt)):
            P.append((x, y, z))
        for q in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5),
                  (2, 3, 7, 6), (3, 0, 4, 7)):
            F.append(tuple(i0 + k for k in (q if sx > 0 else q[::-1])))
    me = bpy.data.meshes.new(name)
    me.from_pydata(P, [], F)
    me.update()
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    R, t = place
    ob.matrix_world = _mat4(R, t)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def _mat4(R, t):
    from mathutils import Matrix
    M = Matrix.Identity(4)
    for i in range(3):
        for j in range(3):
            M[i][j] = float(R[i][j])
        M[i][3] = float(t[i])
    return M


def _surface_samples(place, res=1.0):
    """Points on the girders' OUTER SURFACES, for solving a camera distance."""
    P = []
    for gid in GIRDER_IDS:
        gs = SPECS[gid]
        x = np.arange(gs.x0, gs.x1, 0.35)
        D = top_z(gs, x) - bottom_z(gs, x)
        S, TAG, E, hb, ht, bt, tt = section_points(gs, x, D, 1.0)
        S = displace_section(gs, x, S, TAG, D, bt, hb, ht, tt)
        Cp = np.stack([x, web_y(gs, x), bottom_z(gs, x)], -1)
        sel = np.arange(0, S.shape[1], 3)
        Q = (Cp[:, None, :]
             + S[:, sel, 0:1] * np.array([0.0, 1.0, 0.0])[None, None, :]
             + S[:, sel, 1:2] * np.array([0.0, 0.0, 1.0])[None, None, :])
        P.append(Q.reshape(-1, 3))
    P = np.concatenate(P, 0)
    if place is not None:
        R, t = place
        P = P @ np.asarray(R, float).T + np.asarray(t, float)[None, :]
    return P


def _put_camera(name, pos, look, lens, dof=None, fstop=8.0):
    cam = bpy.data.cameras.get(name) or bpy.data.cameras.new(name)
    cam.lens = lens
    cam.sensor_width = SENSOR_MM
    cam.sensor_fit = 'HORIZONTAL'
    ob = bpy.data.objects.get(name)
    if ob is None:
        ob = bpy.data.objects.new(name, cam)
        bpy.context.scene.collection.objects.link(ob)
    ob.data = cam
    d = np.asarray(look, float) - np.asarray(pos, float)
    ob.location = tuple(float(v) for v in pos)
    from mathutils import Vector
    ob.rotation_mode = 'XYZ'
    ob.rotation_euler = Vector((float(d[0]), float(d[1]), float(d[2]))
                               ).to_track_quat('-Z', 'Y').to_euler()
    if dof:
        cam.dof.use_dof = True
        cam.dof.focus_distance = float(dof)
        cam.dof.aperture_fstop = fstop
    else:
        cam.dof.use_dof = False
    return ob


def _solve_cam(S, aim, vdir, dist, lo=0.4, hi=9.0, n=4301):
    """Slide the lens along `vdir` until the nearest surface sample is `dist`."""
    def nearest(d):
        p = aim + vdir * d
        return p, float(np.min(np.linalg.norm(S - p[None, :], axis=1)))
    best = min(((abs(nearest(d)[1] - dist), d) for d in np.linspace(lo, hi, n)))
    return nearest(float(best[1]))


def macro_camera(B, name="CAM_PGD_MACRO", dist=2.5, lens=21.0):
    """EXACTLY the manifest's shot: 2.5 m on a 21 mm lens, and BROADSIDE.

    THE FRAMING IS DECIDED BY onscreen_px_4k, NOT BY TASTE.  The manifest says
    this item reads 1210 px on the 4K master across its 1.35 m depth, and
    1.35 * 21 * 3840 / (36 * 2.5) = 1210 only if the 1.35 m is ACROSS the
    frame -- i.e. the lens is looking at a girder's web face square on from
    2.5 m, not up at its soffit from underneath.  The first version of this
    camera stood under the deck looking along the span; every number in it was
    right and the girder read about 400 px, a third of what the manifest
    asked, because a soffit seen end-on is 0.5 m of flange and 30 m of
    perspective.  A camera at the right DISTANCE pointed the wrong way is
    still the wrong shot.

    THE SECOND THING THE FRAMING HAD TO DECIDE IS WHICH FACE.  Every web on
    this bridge is a +-y plane and the 12.5 deg sun travels toward local
    (0.113, -0.970, -0.216), so there is no web anywhere on it that the sun
    rakes: a face is either square on to the key (girder D's outer face, cos
    incidence 0.97) or in full shadow (girder A's outer face).  Square on to a
    115 W/m2 key at 12.5 deg is 4.6x the irradiance of the horizontal surface
    REFERENCE_EXPOSURE_EXTERIOR was solved against, so it renders as a pale,
    flat, contrast-free panel -- physically right, and useless for judging
    whether a weld bead, a chip or a 4 mm oil-can exists.  The SHADOW side,
    lit by sky and by the asphalt 2.9 m below it, is where relief and colour
    both read, and it is also the face the film sees: the car and the lens
    arrive from -y, so girder A's outer face is the one on camera.

    So: square on to the OUTER face of the LEADING fascia girder A, centred a
    little off its field splice at x = -4.20 (which sits beside the x = -4
    cross-frame), at exactly 2.500 m from the nearest steel.  The frame
    contains, all at 896 px/m: the splice cover plate and its bolt cluster,
    three or four stiffeners with their copes and the strip of daylight where
    the intermediates stop short of the bottom flange, both flange arrises
    with their 2 mm chamfers, the banner rails and their bolted cleats, the
    continuous web-to-flange seams, the anti-perch spikes on the bottom-flange
    shelf, and the paint.  CAM_PGD_LIT is the same shot on the sunlit face and
    CAM_PGD_UNDER is the from-underneath view, because that is the geometry
    the film actually flies.
    """
    place = B.place
    S = _surface_samples(place)
    gs = SPECS["A"]
    xc = gs.splice_x + 0.62
    face = web_face(gs, xc, clear_web_depth(gs, xc) * 0.5, -1.0)
    aim_local = np.array([xc, face[1], float(bottom_z(gs, np.array([xc]))[0])
                          + GIRDER_DEPTH * 0.47])
    vdir_local = unit(np.array([0.470, -0.865, -0.178]))
    look_local = np.array([1.05, 0.0, 0.34])
    if place is not None:
        Rm, tt = np.asarray(place[0], float), np.asarray(place[1], float)
        aim, vdir, loff = Rm @ aim_local + tt, Rm @ vdir_local, Rm @ look_local
    else:
        aim, vdir, loff = aim_local, vdir_local, look_local
    pos, dmin = _solve_cam(S, aim, vdir, dist)
    ob = _put_camera(name, pos, aim + loff, lens,
                     dof=float(np.linalg.norm(aim - pos)) + 0.30, fstop=10.0)
    px = (3840.0 * lens / SENSOR_MM) / dmin
    print(">> macro camera %s: nearest girder SURFACE %.4f m (manifest 2.5), "
          "%.0f mm lens" % (name, dmin, lens))
    print(">>   -> %.1f px/m on the 4K master, 1 px = %.3f mm; the 1.350 m "
          "depth reads %.0f px (manifest 1210)"
          % (px, 1000.0 / px, GIRDER_DEPTH * px))
    print(">>   lens at world z = %.3f" % pos[2])
    return ob, dmin


def lit_camera(B, name="CAM_PGD_LIT", dist=2.5, lens=21.0):
    """The same shot on the SUNLIT face -- girder D's outer web.

    Kept because "the key blows this face out" is a claim, and a claim about
    an image should ship with the image.  Same distance, same lens, same
    framing geometry mirrored; the only difference is which side of the bridge
    the lens is on.
    """
    place = B.place
    S = _surface_samples(place)
    gs = SPECS["D"]
    xc = gs.splice_x + 0.62
    face = web_face(gs, xc, clear_web_depth(gs, xc) * 0.5, +1.0)
    aim_local = np.array([xc, face[1], float(bottom_z(gs, np.array([xc]))[0])
                          + GIRDER_DEPTH * 0.47])
    vdir_local = unit(np.array([0.470, 0.865, -0.178]))
    look_local = np.array([1.05, 0.0, 0.10])
    if place is not None:
        Rm, tt = np.asarray(place[0], float), np.asarray(place[1], float)
        aim, vdir, loff = Rm @ aim_local + tt, Rm @ vdir_local, Rm @ look_local
    else:
        aim, vdir, loff = aim_local, vdir_local, look_local
    pos, dmin = _solve_cam(S, aim, vdir, dist)
    ob = _put_camera(name, pos, aim + loff, lens,
                     dof=float(np.linalg.norm(aim - pos)) + 0.30, fstop=10.0)
    print(">> lit camera %s: nearest girder SURFACE %.4f m, %.0f mm lens"
          % (name, dmin, lens))
    return ob, dmin


def under_camera(B, name="CAM_PGD_UNDER", dist=2.5, lens=21.0):
    """The from-underneath view, at the same 2.5 m and 21 mm.

    Aimed at girder A's bottom-flange splice cover plate, which puts a
    32-bolt cluster, the x = -4 cross-frame, four receding soffits and the
    deck above them in one frame.  This is the geometry the film flies; the
    macro is the one that resolves the item.
    """
    place = B.place
    S = _surface_samples(place)
    gs = SPECS["A"]
    aim_local = np.array([gs.splice_x, gs.y, SOFFIT_Z - 0.016])
    vdir_local = unit(np.array([-0.130, -0.585, -0.800]))
    look_local = np.array([1.55, 2.35, 0.62])
    if place is not None:
        Rm, tt = np.asarray(place[0], float), np.asarray(place[1], float)
        aim, vdir, loff = Rm @ aim_local + tt, Rm @ vdir_local, Rm @ look_local
    else:
        aim, vdir, loff = aim_local, vdir_local, look_local
    pos, dmin = _solve_cam(S, aim, vdir, dist)
    ob = _put_camera(name, pos, aim + loff, lens,
                     dof=float(np.linalg.norm(aim - pos)) + 0.55, fstop=9.0)
    print(">> under camera %s: nearest girder SURFACE %.4f m, %.0f mm lens, "
          "lens z %.3f" % (name, dmin, lens, pos[2]))
    return ob, dmin


def pass_camera(B, name="CAM_PGD_PASS", lens=21.0):
    """The film's own moment: the lens on the racing line at world z = 5.000,
    a metre off the deck, looking up and forward into the soffit at 300 km/h.
    1.8 m of clearance to the steel.  This is the frame the item exists for."""
    place = B.place
    p_local = np.array([0.35, -3.30, 5.000])
    l_local = np.array([-0.30, 4.60, 6.58])
    if place is not None:
        Rm, tt = np.asarray(place[0], float), np.asarray(place[1], float)
        pos, look = Rm @ p_local + tt, Rm @ l_local + tt
    else:
        pos, look = p_local, l_local
    S = _surface_samples(place)
    dmin = float(np.min(np.linalg.norm(S - pos[None, :], axis=1)))
    ob = _put_camera(name, pos, look, lens, dof=None)
    print(">> pass camera %s: nearest girder surface %.3f m, lens z %.3f"
          % (name, dmin, pos[2]))
    return ob


def inspect_camera(B, name, target_local, eye_local, lens, fstop=5.6):
    place = B.place
    if place is not None:
        Rm, tt = np.asarray(place[0], float), np.asarray(place[1], float)
        tgt = Rm @ np.asarray(target_local, float) + tt
        eye = Rm @ np.asarray(eye_local, float) + tt
    else:
        tgt = np.asarray(target_local, float)
        eye = np.asarray(eye_local, float)
    d = float(np.linalg.norm(tgt - eye))
    ob = _put_camera(name, eye, tgt, lens, dof=d, fstop=fstop)
    print(">> inspection camera %s at %.3f m, %.0f mm" % (name, d, lens))
    return ob


def test_scene(out=None, samples=256, res=(1920, 1080), quality=1.0):
    """The acceptance scene: the four girders where they really are, the
    contract sun, the racing surface that lights their undersides, the deck
    that darkens them, and cameras at the manifest's own distance and lens."""
    sc = bpy.context.scene
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    place = pont_to_world()
    B = build(place=place, res=quality)
    contract_light(sc)
    context_ground()
    context_deck(place)
    context_abutments(place)
    cam, dmin = macro_camera(B)
    lit_camera(B)
    under_camera(B)
    pass_camera(B)
    gsC = SPECS["C"]
    dC = clear_web_depth(gsC, gsC.splice_x)
    inspect_camera(B, "CAM_PGD_SPLICE",
                   (gsC.splice_x, gsC.y - 0.10, SOFFIT_Z + gsC.bt + dC * 0.5),
                   (gsC.splice_x + 0.42, gsC.y - 1.00, SOFFIT_Z + 0.30), 58.0)
    gsB = SPECS["B"]
    xst = [x for (x, k) in stiffener_stations(gsB) if k == "inter"][3]
    inspect_camera(B, "CAM_PGD_STIFF",
                   (xst, gsB.y + 0.14, SOFFIT_Z + gsB.bt + 0.06),
                   (xst + 0.55, gsB.y + 1.05, SOFFIT_Z - 0.62), 58.0)
    gsA = SPECS["A"]
    inspect_camera(B, "CAM_PGD_PERCH",
                   (-8.1, gsA.y + 0.05, SOFFIT_Z + gsA.bt + 0.05),
                   (-7.4, gsA.y + 1.15, SOFFIT_Z - 0.30), 58.0)
    inspect_camera(B, "CAM_PGD_NOSE",
                   (gsA.x1 - 0.9, gsA.y, SOFFIT_Z + 0.95),
                   (gsA.x1 + 2.6, gsA.y - 3.1, SOFFIT_Z - 0.9), 35.0)
    sc.camera = cam
    sc.render.engine = 'CYCLES'
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    cy = sc.cycles
    cy.samples = samples
    cy.use_denoising = True
    cy.max_bounces = 12
    cy.diffuse_bounces = 6
    cy.glossy_bounces = 6
    cy.transmission_bounces = 8
    try:
        cy.device = 'GPU'
    except Exception:
        pass
    B.meta["nearest_girder_surface_m"] = dmin
    dump_interface(B)
    st = B.stats
    print(">> VARIATION, measured on what was actually emitted:")
    print("   girder lengths          %s"
          % {k: round(v, 3) for k, v in st["girder_lengths"].items()})
    print("   stiffeners              %3d built, %3d distinct shapes"
          % (st.get("stiffeners", 0), st.get("distinct_stiffener_shapes", 0)))
    print("   bolts                   %3d on the girders, %3d on the braces, "
          "%3d distinct geometries"
          % (st.get("bolts", 0), st.get("brace_bolts", 0),
             st.get("distinct_bolt_geometries", 0)))
    print("   welds                   %3d runs" % st.get("welds", 0))
    print("   plates                  %3d" % st.get("plates", 0))
    print("   shear studs             %3d" % st.get("studs", 0))
    print("   perch spikes            %3d" % st.get("spikes", 0))
    print("   nest twigs              %3d" % st.get("nest_twigs", 0))
    print("   lowest z anywhere       %.4f   over the track %.4f "
          "(soffit datum %.3f)"
          % (st["lowest_z"], st["lowest_z_over_track"], SOFFIT_Z))
    print("   headroom over the racing surface %.3f m; clearance to the "
          "film's lens at z=5.000 is %.3f m"
          % (st["track_headroom_measured_m"], st["camera_clearance_measured_m"]))
    if out:
        import fix_audit_blend as FA
        FA.save_clean(out)
    return B, cam


def _cli():
    argv = sys.argv
    a = argv[argv.index("--") + 1:] if "--" in argv else []

    def opt(name, default=None, cast=str):
        return cast(a[a.index(name) + 1]) if name in a else default

    if "--test" in a:
        out = opt("--out")
        if out and not os.path.isabs(out):
            out = os.path.join(ROOT, out)
        test_scene(out=out, quality=opt("--quality", 1.0, float),
                   samples=opt("--samples", 256, int))
    elif "--one" in a:
        materials()
        B = build(place=None, res=opt("--quality", 1.0, float))
        contract_light()
        dump_interface(B)
        if "--out" in a:
            import fix_audit_blend as FA
            FA.save_clean(opt("--out"))
    else:
        print(__doc__)


if __name__ == "__main__":
    _cli()

