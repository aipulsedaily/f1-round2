#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gantry_truss.py — THE start/finish gantry truss beam.  Item 64, wave 1.

    manifest:  nearest_camera_m 3.0   lens 35 mm   onscreen_px_4k 1493
               instances 1            hero True    beats ['4', '5', '6']
               depends_on ['gantry_leg']   dependents 4
               variation_axes: node plates / bolt clusters / walkway edge
               notes: "Soffit at z=+9.00, 2.2 m deep.  THE CAMERA PASSES UNDER
                       IT AT 3.0 m.  Every bolt cluster and node plate on the
                       underside is on camera."
    pixels:    px_per_m = (3840 * 35 / 36) / 3.0 = 1244.4 px/m
               -> 1 screen pixel = 0.804 mm on this truss.

That number is the whole brief.  At 0.80 mm/px:

    an M20 nut is 37 px across the flats and its 30 deg chamfer is 3.7 px
    a weld's stack-of-dimes ripple, 2.6 mm pitch, is 3.2 px
    a flame-cut plate's 1.5 mm chamfer is 1.9 px
    a 12 mm galvanising drain hole is 15 px, and its 10 mm wall is 12 px
    an M20 thread pitch is 3.1 px
    a load-indicating washer's 0.5 mm bump is 0.6 px
    the 31 mm precamber over the 22 m span is 39 px of curvature

Nothing on that list can be a shader.  All of it is mesh.

WHAT IS AND IS NOT GEOMETRY, AND WHY
    MESH   SHS chords with rolled corner radii, mill waviness, face dishing and
           weld pull-in at every panel point; the 31 mm parabolic precamber; CHS
           web members with real lack-of-straightness and saw-cut ends; the
           bolted end-plate field splices with their 3 mm packing shims and the
           0.6 mm joint line; 34 node gusset plates, every one a DIFFERENT
           outline; flat-bar plan bracing lapping opposite faces of those
           gussets and crossing on a loose pack at every bay centre; 313
           bolts, every one with a chamfered hex head, a washer, a chamfered
           nut, a real helical thread and its own protrusion length; DTI
           (load-indicating) washers with their squashed bumps; through drain
           holes with the tube's 10 mm wall visible in the bore and a frozen
           zinc icicle hanging from the rim; fillet welds with stack-of-dimes
           ripple; weld spatter; flame-cut edge waviness and drag lines; the
           bearing assemblies; the walkway edge angle with its per-bay
           variations; fascia brackets; TV-pod pads; signal hangers; the
           soffit service channel with its slots.
    SHADER paint.  A 0.25 mm two-pack film is 0.3 px, so its RELIEF is
           sub-pixel and its COLOUR BOUNDARY is what reads: chalking on the
           sun side, chips that expose DULL GREY ZINC (not rust - the steel is
           galvanised under the paint, and that distinction is the single most
           common mistake in painted-steelwork rendering), white-rust bloom,
           bird lime on the upward faces and streaks under them, rain tracking
           off the walkway grating, torque marks on the nuts, and the heat
           tint on the unpainted field welds.  Stated here so nobody has to
           wonder whether it was an oversight.

===========================================================================
THE INTERFACE  (this item is a FOUNDATION.  gantry_soffit_panel,
                gantry_walkway, gantry_fascia and gantry_tv_pod all build on
                it and cannot ask questions.  gantry_leg lands ON it.
                Everything below is public, stable, and dumped to
                world/items/gantry_truss_interface.json on every build.)
===========================================================================

THE GANTRY FRAME  — the convention every dependant must use
        This module builds in the CIRCUIT (design) frame, at the start/finish
        line, and is placed into the world by `place=(R, t)`:

            R = world_contract rotation about z by ROT_DEG (40 deg)
            t = circuit_to_world(0, 0) = (329.396, 169.820, 0.0)

        gantry-local axes, which ARE the circuit axes:
            +X  along the pit straight, the racing direction.  The truss is
                1.90 m wide in x (chord axes at x = +-0.950).
            +Y  to the LEFT of the racing direction, i.e. toward the pit wall.
                The truss SPANS in y, from -11.600 to +11.600.
            +Z  up.  WORLD z, not a local z: z = 0.000 is the pit straight.

        `gantry_to_world()` returns (R, t) so a dependant never re-derives it.

THE DATUM PLANE — read these, do not assume them
        SOFFIT_Z          9.000   the lowest point of the STRUCTURE (the
                                  underside of the bottom chords), at the
                                  BEARINGS.  The manifest's "+9.00".
        soffit_z(y)               the cambered soffit, SOFFIT_Z + camber(y).
                                  Mid-span is 31 mm HIGHER, never lower.  A
                                  soffit panel that assumes a flat 9.000 will
                                  show a 31 mm gap at mid-span = 39 px.
        LOWEST_FITTING_Z          the lowest point of ANY geometry this module
                                  emits, fittings included (the service
                                  channel and the hanger cleats hang below the
                                  chords).  Measured on the built mesh, not
                                  asserted; reported in the interface JSON.
        TOP_Z            11.200   top of the top chords = 2.200 m structural
                                  depth.  The walkway bears on this plane.
        BEARING_Y        11.000   |y| of the leg bearing centrelines.
        CHORD_X           0.950   |x| of the chord axes.

MOUNT FRAMES (all gantry-local unless the truss was built with `place`, in
which case they are WORLD).  A Frame is .o origin, .x/.y/.z orthonormal axes,
.r a characteristic radius, .tag a string.  `sorted(truss.mounts)` on a built
truss lists exactly what it grew.

    leg_head_<S|N>          FOR gantry_leg.  The bearing seat under the bottom
                            chord at y = -+11.000.  .o is on the UNDERSIDE of
                            the 30 mm bearing plate, i.e. the face the leg head
                            must meet; .z points DOWN, into the leg; .x is the
                            circuit +x.  .r is the half-diagonal of the 420 x
                            360 mm plate.  There are TWO per bearing line, one
                            per chord (suffixed _e / _w for x = +0.95 / -0.95),
                            plus a mid frame `leg_head_<S|N>` at x = 0 for a
                            single-shaft leg.  The four M30 holding-down bolts
                            are at leg_head_<S|N>_<e|w>_bolt<0..3>; their
                            slotted holes are 36 x 46 mm, so the leg has
                            +-5 mm of setting-out tolerance in x and y.
    soffit_rail_<e|w>       FOR gantry_soffit_panel.  The 41 x 41 mm C-channel
                            welded along the underside of each bottom chord,
                            its 16 mm slot opening DOWN and CONTINUOUS over the
                            whole shipped length - so a tray hanger goes
                            anywhere on it with an M12 channel nut and there is
                            no slot pitch to line up with.  .o at mid-span on
                            the channel's open face, .y along the span, .z
                            DOWN, .r = 0.0205.  It BREAKS at the two field
                            splices; see `splice_w` / `splice_e`.
    soffit_cleat_<n>        FOR gantry_soffit_panel.  A 10 mm plate cleat
                            welded to the chord soffit with one 14 mm hole,
                            every 4th panel point, alternating sides.
    tv_pad_<0..2>           FOR gantry_tv_pod.  An 18 mm pad on the chord
                            soffit with a 4 x M16 pattern at 150 x 150 mm and
                            a 32 mm cable grommet.  .z points DOWN.
    signal_hanger_<0..4>_<e|w>   FOR start_light_backing (5 pods).  A pair of
                            16 mm hanger plates with 2 x M20 holes each,
                            hanging 120 mm below the chord soffit.
    fascia_bracket_<t|p>_<n>     FOR gantry_fascia.  't' = track face
                            (x = -0.950 side, the face the camera sees on the
                            onboard follow), 'p' = pit face.  A 12 mm outrigger
                            plate at every 2nd panel point, projecting 180 mm
                            outboard, with 2 x M16 holes at 110 mm gauge.
                            .x is the OUTWARD normal, .o on the outer face.
    walkway_bearer_<n>      FOR gantry_walkway.  Top face of the transverse
                            RHS 150 x 100 bearer, z = TOP_Z + camber.
    walkway_edge_<e|w>      FOR gantry_walkway.  The 100 x 75 x 8 edge angle
                            welded along the outer top arris of each top
                            chord; its vertical leg is a 100 mm toe upstand.
                            `walkway_edge_bays` names what each bay grew
                            (plain / splice_cover / stanchion / weep_pipe /
                            cleat / lifting_lug - all six occur on both sides)
                            so the walkway's kick plate can dodge them.
    walkway_level_z(y)      the grating bearing plane, TOP_Z + camber(y).
    stanchion_base_<n>      FOR gantry_walkway.  A 12 mm base plate with a
                            4 x M12 pattern at 90 x 90 mm on the edge angle.
    anchor_eye_<n>          fall-arrest eye bolts on the top chord.
    splice_<w|e>            the field splice plane: .o on the joint line, .y
                            the span direction.  Nothing may be routed through
                            a splice without a break.

BUILD
    materials(force=False)  -> [paint, galv, fastener, machined, elasto].
                            Idempotent, named 'GTR_*'.  Slot order IS
                            MAT_PAINT/MAT_GALV/MAT_FASTENER/MAT_MACHINED/
                            MAT_ELASTO = 0..4.
    build(coll_name='GTR_Truss', place=None, res=1.0) -> Truss
                            Three objects, GTR_Truss_A/_B/_C, split at the two
                            FIELD SPLICES, because that is how a 23.2 m truss
                            is actually delivered and because it keeps every
                            object's TexCoord->Object domain inside +-4.0 m.
    gantry_to_world()       -> (R 3x3, t 3) for the placement above.

WHY THREE OBJECTS AND NOT ONE.  LAW 6 says recentre on emit and read
TexCoord->Object.  A single 23.2 m object has object coordinates out to
+-11.6 m, and the 420 cells/m voronoi that carries the zinc spangle would be
4,900 cycles of float32 across it.  Split at the splices, the domain is
+-4.0 m and the same shader resolves.  The split is not a rendering trick: it
is where the truss is actually bolted together, and the bolt rings are on
camera.

PER-VERTEX CHANNELS (the shader contract, shared with marshal_post_column)
    uv    (u, v)   METRES: u around the section, v along the member.
    base  RGBA     paint colour (linear) + A = member id in [0,1]
    aux   RGBA     (edge_exposure, weld, machined, uid)
    wear  RGBA     (chip, dirt, rust, age)

THE HARD-SURFACE TOOLKIT is imported from world/items/marshal_post_column.py,
which declares it reusable in its own module docstring: "every marshal_* and
most trackside items need bolts, welds and sections, and re-deriving them 30
times is how a world stops looking like one world".  Acc, sweep, the sections,
weld_bead, hex_nut, washer, thread_stud, plate and the frame helpers come from
there; every material and every piece of geometry below is this module's own.
It is a same-repo import of hand-written procedural code - no external asset
is involved.

Run standalone to build the test scene:

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P world/items/gantry_truss.py -- --test \
        --out world/items/gantry_truss_test.blend
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

# The toolkit contract, checked at import so a refactor upstream fails HERE
# with a name instead of 400 lines later with an AttributeError.
for _need in ("Acc", "sweep", "bridge", "circle_section", "rrect_section",
              "angle_section", "section_outward", "section_perimeter_u",
              "cap_flat", "weld_bead", "hex_nut", "washer", "thread_stud",
              "dome_head", "frames_along", "rot_axis", "rotz", "unit",
              "Frame", "chan", "NG", "_new_mat", "_chan", "_set", "srgb",
              "rect_loop", "rect_loop_counts", "_cell_rings", "open_end"):
    if not hasattr(HS, _need):
        raise ImportError(
            "gantry_truss needs marshal_post_column.%s and it is gone. "
            "The hard-surface toolkit is a shared interface; restore the "
            "name or port the primitive here." % _need)

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
rect_loop = HS.rect_loop
rect_loop_counts = HS.rect_loop_counts
_cell_rings = HS._cell_rings

PFX = "GTR_"
ROOT_COLL = "GTR_Truss"
SENSOR_MM = 36.0
TAU = 2.0 * math.pi

MAT_PAINT, MAT_GALV, MAT_FASTENER, MAT_MACHINED, MAT_ELASTO = range(5)
MAT_NAMES = ["Paint", "Galv", "Fastener", "Machined", "Elasto"]


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


# --------------------------------------------------------------------------- #
#  2.  THE DIMENSIONS.  Every one of these is a real fabricated size.           #
# --------------------------------------------------------------------------- #
#
# The gantry is dimensioned by circuit_spec / build_architecture: legs on
# circuit y = +-11.000, soffit z = 9.000, and the manifest adds "2.2 m deep".
# Everything else here is the section schedule a fabricator would actually
# choose for a 22 m simply-supported box truss carrying a 22 x 1.2 m banner,
# a walkway, five signal pods and three camera pods.

SOFFIT_Z = 9.000                 # underside of the bottom chords AT THE BEARINGS
TRUSS_DEPTH = 2.200              # manifest
TOP_Z = SOFFIT_Z + TRUSS_DEPTH   # 11.200, top face of the top chords

CHORD_W = 0.200                  # SHS 200 x 200 x 10
CHORD_T = 0.010
CHORD_R = 0.015                  # outer corner radius (t + 5 mm, EN 10210 hot-formed)
CHORD_X = 0.950                  # |x| of the chord AXES -> 1.900 m centres
BOT_AXIS_Z = SOFFIT_Z + CHORD_W * 0.5      # 9.100
TOP_AXIS_Z = TOP_Z - CHORD_W * 0.5         # 11.100
AXIS_DEPTH = TOP_AXIS_Z - BOT_AXIS_Z       # 2.000

BEARING_Y = 11.000               # leg centrelines, circuit y = +-11.0
N_PANEL = 14                     # panels between the bearings
PANEL = 2.0 * BEARING_Y / N_PANEL          # 1.571429 m -> diagonals at 51.85 deg
OVERHANG = 0.600                 # cantilever past each bearing
END_Y = BEARING_Y + OVERHANG     # 11.600

CAMBER = 0.031                   # span/710 precamber, parabolic, at mid-span
TIP_SAG = 0.004                  # the cantilever tips droop this much

# web members
VERT_OD, VERT_T = 0.1397, 0.0063           # CHS 139.7 x 6.3, side verticals
DIAG_OD, DIAG_T = 0.1143, 0.0050           # CHS 114.3 x 5.0, side diagonals
TIE_OD, TIE_T = 0.0889, 0.0040             # CHS 88.9 x 4.0, transverse ties
TIE_DZ = -0.045                  # ties ride BELOW the chord axis; see build()
PLAN_W, PLAN_T = 0.150, 0.012              # flat 150 x 12, bottom plan bracing.
#   NOT an angle.  An L100 cross-braced at two levels is a textbook detail
#   until you draw it: whichever way the toes point, the lower brace's 90 mm
#   leg passes through the upper brace at the crossing - at all 16 crossings,
#   150 mm from the lens.  Toes down instead clash with the transverse tie.  A
#   flat bar lives entirely inside its own 12 mm band, which is why plane wind
#   bracing is detailed in flat bar in the first place; and from below, the
#   only view this item ever gets, an angle with its toe up reads as a flat
#   band anyway.  Nothing is lost but the clash.
TOPBAR_W, TOPBAR_T = 0.090, 0.010          # flat 90 x 10, top plan bracing
BEARER_W, BEARER_H, BEARER_T = 0.150, 0.100, 0.006   # RHS 150x100x6 walkway bearer

# connections
GUSSET_T = 0.020                 # node gusset plates
GUSSET_Z0 = BOT_AXIS_Z + 0.050   # 9.150, plate underside inside the chord depth
PACK_T = 0.012                   # packing plate at the plan-brace crossing
SPLICE_T = 0.025                 # end-plate splice
SPLICE_GAP = 0.0006              # the joint line: two plates never bed perfectly
SPLICE_Y = np.array([-3.928571, 3.928571])   # mid-panel, k=4/5 and k=9/10
ENDCAP_T = 0.012

# the walkway edge
EDGE_A, EDGE_B, EDGE_T = 0.100, 0.075, 0.008    # L 100 x 75 x 8, heel out

# the soffit service channel (what gantry_soffit_panel bolts to)
CHAN_W, CHAN_H, CHAN_T = 0.041, 0.041, 0.0025
CHAN_SLOT = (0.018, 0.042)       # slot w x l
CHAN_PITCH = 0.400

# bolt schedule: (across flats, head height, nut height, washer OD, washer t,
#                 shank r, pitch)
BOLTS = {
    "M12": (0.019, 0.0075, 0.0102, 0.024, 0.0025, 0.0060, 0.00175),
    "M16": (0.024, 0.0100, 0.0130, 0.030, 0.0030, 0.0080, 0.00200),
    "M20": (0.030, 0.0125, 0.0160, 0.037, 0.0030, 0.0100, 0.00250),
    "M24": (0.036, 0.0150, 0.0190, 0.044, 0.0040, 0.0120, 0.00300),
    "M30": (0.046, 0.0187, 0.0240, 0.056, 0.0040, 0.0150, 0.00350),
}
HOLE_CLEAR = 0.001               # 2 mm clearance hole -> +1 mm on the radius

# where the dependants land
TV_PAD_Y = (-6.60, 1.20, 4.80)             # gantry_tv_pod, 3 instances
SIGNAL_Y = (-4.00, -2.00, 0.00, 2.00, 4.00)  # start_light_backing, 5 instances

PAINT_HEX = "#c9ccce"            # the gantry's two-pack topcoat: a light warm grey
PRIMER_HEX = "#8d6a3c"           # zinc-phosphate primer under it
ZINC_HEX = "#9aa0a4"             # the hot-dip layer under THAT


# --------------------------------------------------------------------------- #
#  3.  THE GEOMETRY OF THE SPAN  (plan layer - no bpy)                          #
# --------------------------------------------------------------------------- #

def stations():
    """Panel-point y stations, ends included.  17 cross-frames."""
    k = np.arange(N_PANEL + 1)
    core = -BEARING_Y + k * PANEL
    return np.concatenate([[-END_Y], core, [END_Y]])


STATIONS = stations()
N_STA = len(STATIONS)
BAYS = [(STATIONS[i], STATIONS[i + 1]) for i in range(N_STA - 1)]


def camber(y):
    """Fabrication precamber, m.  0 at the bearings, +CAMBER at mid-span.

    THE SIGN MATTERS.  A cambered truss is HIGHER in the middle, so the
    clearance-critical soffit level is at the bearings and the manifest's
    9.000 is a minimum, never an average.  Beyond the bearings the cantilever
    tips droop back down by TIP_SAG.
    """
    y = np.asarray(y, float)
    t = np.clip(np.abs(y) / BEARING_Y, 0.0, None)
    inner = CAMBER * (1.0 - np.minimum(t, 1.0) ** 2)
    over = np.clip((np.abs(y) - BEARING_Y) / OVERHANG, 0.0, 1.0)
    return inner - TIP_SAG * over ** 2


def sweep_x(y):
    """Erection lack-of-straightness: the truss is 9 mm off line at mid-span.

    A 23 m truss set by two cranes is never straight to the millimetre.  9 mm
    over 23 m is 11 screen px of drift down the soffit line, which is exactly
    the sort of thing that reads as 'built' rather than 'modelled'.
    """
    y = np.asarray(y, float)
    return (0.0090 * np.sin(math.pi * (y + END_Y) / (2.0 * END_Y))
            + 0.0028 * np.sin(2.3 * math.pi * y / END_Y + 0.7))


def twist(y):
    """0.42 deg of erection twist, as a rotation about the span axis (rad)."""
    y = np.asarray(y, float)
    return math.radians(0.42) * (y / END_Y)


def soffit_z(y):
    """PUBLIC.  The cambered soffit level at span station y."""
    return SOFFIT_Z + camber(y)


def walkway_level_z(y):
    """PUBLIC.  The grating bearing plane at span station y."""
    return TOP_Z + camber(y)


def chord_points(side, level, ys):
    """(M,3) axis points of a chord.  side +-1 in x, level 0 bottom / 1 top."""
    ys = np.atleast_1d(np.asarray(ys, float))
    z0 = BOT_AXIS_Z if level == 0 else TOP_AXIS_Z
    cam = camber(ys)
    sw = sweep_x(ys)
    tw = twist(ys)
    # the twist rotates the section about the truss's own longitudinal axis,
    # which lifts one chord and drops the other
    dx = side * CHORD_X
    dz = (z0 - 0.5 * (BOT_AXIS_Z + TOP_AXIS_Z))
    x = sw + dx * np.cos(tw) - dz * np.sin(tw)
    z = 0.5 * (BOT_AXIS_Z + TOP_AXIS_Z) + cam + dx * np.sin(tw) + dz * np.cos(tw)
    return np.stack([x, ys, z], -1)


def chord_at(side, level, y):
    return chord_points(side, level, [y])[0]


def segment_of(y):
    """Which delivered section a span station belongs to: 0 west, 1 centre, 2 east."""
    y = float(y)
    if y < SPLICE_Y[0]:
        return 0
    if y > SPLICE_Y[1]:
        return 2
    return 1


SEG_NAMES = ("A", "B", "C")


# --------------------------------------------------------------------------- #
#  4.  THE VARIATION AXES, DECIDED ONCE                                         #
# --------------------------------------------------------------------------- #
#
# The manifest names three: node plates, bolt clusters, walkway edge.  This
# item declares ONE instance, so the acceptance gate's per-instance check is
# skipped - which means the variation is on ME to prove, not on the gate to
# catch.  Every one of these three families is enumerated below with its own
# distinct-shape count, and build() counts what it actually emitted and puts
# the counts in the interface JSON.  An axis that turns out to have produced
# one shape 34 times is a defect I would rather find here than in a frame.

NODE_KINDS = ("splay", "clip", "notch", "kite", "stub", "boot")


def node_plate_spec(sta_i, side):
    """The gusset at bottom node (station sta_i, chord side +-1).

    Returns the plate's outline in the chord-local (v, u) plane - v ALONG the
    span, u ACROSS toward the truss centreline - plus its bolt cluster.  No
    two are the same: the kind, the reach, the taper, the corner clips, the
    re-entrant notch, the rat hole, the number of bolts, the bolt gauge, the
    bolt size and which way up each bolt went in are all drawn from the node's
    own hash.
    """
    y = float(STATIONS[sta_i])
    uid = "np%d_%d" % (sta_i, int(side))
    kind = NODE_KINDS[int(hash01(uid, "kind") * len(NODE_KINDS) * 0.999999)]
    # how many plan-brace ends land here: the X bracing gives 2 per bay, so an
    # interior node takes 2, an end node takes 1
    ends = 2 if 0 < sta_i < N_STA - 1 else 1
    reach = rnd(0.300, 0.395, uid, "reach")            # inboard from the chord face
    half_v = rnd(0.185, 0.265, uid, "halfv")           # +-along the span
    if kind == "kite":
        half_v = rnd(0.235, 0.310, uid, "halfv2")
        reach = rnd(0.265, 0.330, uid, "reach2")
    if kind == "stub":
        reach = rnd(0.215, 0.275, uid, "reach3")
    nb = 2 if kind in ("stub", "clip") else rint(2, 3, uid, "nb")
    size = "M20" if not chance(0.22, uid, "sz") else "M24"
    gauge = rnd(0.082, 0.108, uid, "gauge")            # across the brace fin
    pitch = rnd(0.078, 0.104, uid, "pitch")            # along the brace
    clip = rnd(0.030, 0.062, uid, "clip")              # corner clip
    rat = rnd(0.024, 0.038, uid, "rat")                # rat hole at the chord weld
    notch = rnd(0.045, 0.085, uid, "notch") if kind in ("notch", "boot") else 0.0
    stiff = chance(0.34, uid, "stiff")                 # a welded edge stiffener rib
    lug = chance(0.28, uid, "lug")                     # an erection / rigging lug
    drain = chance(0.55, uid, "drain")                 # a 16 mm drain hole
    return dict(uid=uid, y=y, side=int(side), sta=sta_i, kind=kind, ends=ends,
                reach=reach, half_v=half_v, nb=nb, size=size, gauge=gauge,
                pitch=pitch, clip=clip, rat=rat, notch=notch, stiff=stiff,
                lug=lug, drain=drain)


BOLT_KINDS = ("plain", "dti", "nyloc", "double_nut", "cut_flush", "long_tail")


def bolt_spec(uid, size="M20", grip=0.036, flip=None):
    """One bolt's GEOMETRY, not its transform.

    "Transform randomisation is not variation" - so what differs between two
    bolts here is the number of threads showing, whether there is a load
    indicating washer under the head with its five squashed bumps, whether the
    nut is a nyloc with its polymer collar, whether a second nut was run down
    behind it, whether the installer put it in upside down, and how far the
    thread was cut off.  All of that is mesh.
    """
    kind = BOLT_KINDS[int(hash01(uid, "bk") * len(BOLT_KINDS) * 0.999999)]
    af, hh, nh, wo, wt, sr, pitch = BOLTS[size]
    tail = {"cut_flush": rnd(0.0004, 0.0022, uid, "t"),
            "long_tail": rnd(0.022, 0.038, uid, "t"),
            }.get(kind, rnd(0.005, 0.016, uid, "t"))
    return dict(uid=uid, size=size, kind=kind, af=af, head_h=hh, nut_h=nh,
                wash_od=wo, wash_t=wt, shank_r=sr, pitch=pitch,
                grip=float(grip), tail=tail,
                dti=(kind == "dti"), nyloc=(kind == "nyloc"),
                double_nut=(kind == "double_nut"),
                head_down=(chance(0.34, uid, "fd") if flip is None else bool(flip)),
                spin=rnd(0.0, TAU, uid, "spin"),
                tight=rnd(0.86, 1.0, uid, "tq"))


EDGE_KINDS = ("plain", "splice_cover", "stanchion", "weep_pipe",
              "cleat", "lifting_lug")


def walkway_edge_spec(bay_i, side):
    """What the walkway edge angle grew in this bay, on this side."""
    uid = "we%d_%d" % (bay_i, int(side))
    y0, y1 = BAYS[bay_i]
    # the two bays containing a field splice ALWAYS get a bolted cover plate:
    # the edge angle is shipped in three pieces too
    for sy in SPLICE_Y:
        if y0 - 1e-6 <= sy <= y1 + 1e-6:
            return dict(uid=uid, bay=bay_i, side=int(side), kind="splice_cover",
                        y0=float(y0), y1=float(y1), at=float(sy))
    kind = EDGE_KINDS[int(hash01(uid, "k") * (len(EDGE_KINDS) - 1) * 0.999999) + 1]
    if chance(0.34, uid, "plain"):
        kind = "plain"
    return dict(uid=uid, bay=bay_i, side=int(side), kind=kind,
                y0=float(y0), y1=float(y1),
                at=float(rnd(y0 + 0.28, y1 - 0.28, uid, "at")))


# --------------------------------------------------------------------------- #
#  5.  channel helpers                                                          #
# --------------------------------------------------------------------------- #

_PAINT = srgb(PAINT_HEX)
_ZINC = srgb(ZINC_HEX)


def ch_paint(member=0.0, uid=0.0, chip=0.44, dirt=0.56, rust=0.10, age=0.70,
             tint=0.0):
    """base / aux / wear for a painted structural member."""
    c = tuple(v * (1.0 + tint) for v in _PAINT)
    return ((*c, float(member)), (0.25, 0.0, 0.0, float(uid)),
            (chip, dirt, rust, age))


def ch_galv(member=0.0, uid=0.0, dirt=0.45, age=0.60):
    return ((*_ZINC, float(member)), (0.30, 0.0, 0.0, float(uid)),
            (0.05, dirt, 0.06, age))


def ch_fast(member=0.0, uid=0.0, dirt=0.55, rust=0.22, age=0.65):
    return ((*_ZINC, float(member)), (0.35, 0.0, 0.55, float(uid)),
            (0.10, dirt, rust, age))


def ch_mach(member=0.0, uid=0.0):
    return ((0.34, 0.345, 0.352, float(member)), (0.40, 0.0, 0.95, float(uid)),
            (0.05, 0.30, 0.35, 0.45))


def with_edge(aux, e):
    return (float(e), aux[1], aux[2], aux[3])


def with_weld(aux, w):
    return (aux[0], float(w), aux[2], aux[3])


def local_frame(w, ref=(0.0, 1.0, 0.0)):
    """Orthonormal (u, v, w) with w given."""
    w = unit(np.asarray(w, float))
    r = np.asarray(ref, float)
    if abs(float(np.dot(r, w))) > 0.95:
        r = np.array([1.0, 0.0, 0.0])
        if abs(float(np.dot(r, w))) > 0.95:
            r = np.array([0.0, 0.0, 1.0])
    u = unit(r - w * float(np.dot(r, w)))
    v = np.cross(w, u)
    return u, v, w


# --------------------------------------------------------------------------- #
#  6.  PUNCHING A REAL HOLE THROUGH A SWEPT SURFACE                             #
# --------------------------------------------------------------------------- #
#
# A galvanising drain hole in the soffit of the bottom chord is 12 mm across
# and 15 screen px at the filmed distance, and looking straight up into it the
# lens sees the 10 mm wall in section - 12 px of it.  A dimple with a dark
# texture would not survive that, and neither would a recessed socket, because
# the camera passes UNDER the truss and the parallax through the hole moves.
# So the hole is a real hole: the faces of a 4 x 4 cell block of the swept grid
# are deleted and replaced by a circle-to-block annulus, then the bore is
# extruded through the wall and closed with the dark inside of the tube.

def swept_quads(IDX, skip=None, flip=False):
    """Quads of an (M,K) index grid, wrapping in K, minus the skipped cells.

    `skip` is a set of (i, j) cell indices.  Returns the quad array so the
    caller can hand it to Acc.quads directly.
    """
    IDX = np.asarray(IDX, np.int64)
    M, K = IDX.shape
    j0 = np.arange(K)
    j1 = (j0 + 1) % K
    A = IDX[:-1][:, j0]
    B = IDX[:-1][:, j1]
    Cc = IDX[1:][:, j1]
    D = IDX[1:][:, j0]
    Q = np.stack([A, B, Cc, D], -1)
    if skip:
        m = np.ones((M - 1, K), bool)
        for (i, j) in skip:
            m[i, j % K] = False
        Q = Q[m]
    else:
        Q = Q.reshape(-1, 4)
    if flip:
        Q = Q[:, ::-1]
    return Q.reshape(-1, 4)


def block_loop(IDX, i0, j0, ni, nj):
    """CCW boundary loop of a (ni x nj) cell block of a grid, as indices."""
    K = IDX.shape[1]
    top = [IDX[i0, (j0 + t) % K] for t in range(nj + 1)]
    right = [IDX[i0 + t, (j0 + nj) % K] for t in range(1, ni + 1)]
    bot = [IDX[i0 + ni, (j0 + nj - t) % K] for t in range(1, nj + 1)]
    left = [IDX[i0 + ni - t, j0 % K] for t in range(1, ni)]
    return np.array(top + right + bot + left, np.int64)


def cell_rings_ell(outer, centre, rx, ry, nv, grade=1.7):
    """Rings from an ELLIPSE at `centre` out to the closed loop `outer`.

    marshal_post_column._cell_rings only does circles; a slotted holding-down
    hole is 36 x 46 mm and the slot is the whole point of it, so this is the
    same construction with two radii.
    """
    outer = np.asarray(outer, float)
    centre = np.asarray(centre, float)
    d = outer - centre[None, :]
    ang = np.arctan2(d[:, 1], d[:, 0])
    inner = centre[None, :] + np.stack([rx * np.cos(ang), ry * np.sin(ang)], -1)
    t = np.linspace(0.0, 1.0, nv + 1) ** grade
    return inner[None] + (outer - inner)[None] * t[:, None, None], ang


def _rxy(r):
    """A hole radius may be a scalar or an (rx, ry) slot."""
    if isinstance(r, (tuple, list, np.ndarray)):
        return float(r[0]), float(r[1])
    return float(r), float(r)


def punch_hole(acc, P, IDX, i0, j0, r, wall, mat, base, aux, wear, uid=0.0,
               ni=4, nj=4, nring=3, burr=0.00013):
    """Replace a cell block of a swept grid with a REAL through hole.

    P (M,K,3) the swept positions, IDX (M,K) their absolute indices.  Returns
    the set of skipped cells so the caller can omit them from its quads.
    """
    K = IDX.shape[1]
    loop_i = block_loop(IDX, i0, j0, ni, nj)
    L = len(loop_i)
    # gather the loop's 3D points from P using the same traversal
    pts = []
    for t in range(nj + 1):
        pts.append(P[i0, (j0 + t) % K])
    for t in range(1, ni + 1):
        pts.append(P[i0 + t, (j0 + nj) % K])
    for t in range(1, nj + 1):
        pts.append(P[i0 + ni, (j0 + nj - t) % K])
    for t in range(1, ni):
        pts.append(P[i0 + ni - t, j0 % K])
    loop_p = np.asarray(pts, float)

    c = P[i0 + ni // 2, (j0 + nj // 2) % K]
    # local plane frame from the block's own tangents
    tv = P[i0 + ni, (j0 + nj // 2) % K] - P[i0, (j0 + nj // 2) % K]
    tu = P[i0 + ni // 2, (j0 + nj) % K] - P[i0 + ni // 2, j0 % K]
    n = unit(np.cross(tu, tv))
    ev = unit(tv)
    eu = unit(np.cross(ev, n))
    n = np.cross(eu, ev)

    def to2(Q):
        d = np.asarray(Q, float) - c[None, :]
        return np.stack([d @ eu, d @ ev], -1)

    def to3(Q2, off=0.0):
        Q2 = np.asarray(Q2, float)
        return (c[None, :] + Q2[:, 0:1] * eu[None, :] + Q2[:, 1:2] * ev[None, :]
                + n[None, :] * off)

    outer2 = to2(loop_p)
    rx, ry = _rxy(r)
    ch = 0.0006
    R2, ang = cell_rings_ell(outer2, (0.0, 0.0), rx + ch, ry + ch, nring,
                             grade=1.55)
    # ring nring is the block boundary (EXISTING verts); walk outer -> inner
    rings = [loop_i]
    for k in range(nring - 1, 0, -1):
        a4 = np.tile(np.asarray(aux, float).reshape(1, 4), (L, 1))
        a4[:, 0] = 0.10
        i = acc.verts(to3(R2[k]), uv=R2[k], base=base, aux=a4, wear=wear)
        rings.append(i + np.arange(L))
    # the chamfered rim itself, with a drilling burr on it
    rim2 = np.stack([(rx + ch) * np.cos(ang), (ry + ch) * np.sin(ang)], -1)
    a4 = np.tile(np.asarray(aux, float).reshape(1, 4), (L, 1))
    a4[:, 0] = 0.98
    a4[:, 2] = 0.85
    # a drilled lip is a WAVE, not a sawtooth: two low harmonics round the
    # bore plus a little noise, so it reads as rolled metal rather than teeth
    _k = np.arange(L) * TAU / L
    bz = burr * (0.55 + 0.45 * np.sin(_k * 2.0 + hash01(uid, "b0") * 6.0)
                 + 0.30 * np.sin(_k * 3.0 + hash01(uid, "b1") * 6.0))
    bz = bz + burr * 0.22 * np.array([hash01(uid, "b", k) for k in range(L)])
    irim = acc.verts(to3(rim2) + n[None, :] * bz[:, None], uv=rim2, base=base,
                     aux=a4, wear=wear)
    rings.append(irim + np.arange(L))
    for k in range(len(rings) - 1):
        bridge(acc, rings[k], rings[k + 1], mat, smooth=False, wrap=True,
               flip=False)
    # bore: chamfer in, then straight through the wall, then the dark inside
    bore2 = np.stack([rx * np.cos(ang), ry * np.sin(ang)], -1)
    prev = rings[-1]
    for (off, ee, mc) in ((-ch * 1.1, 0.85, 0.90), (-wall * 0.55, 0.10, 0.95),
                          (-wall, 0.05, 0.90)):
        a4 = np.tile(np.asarray(aux, float).reshape(1, 4), (L, 1))
        a4[:, 0] = ee
        a4[:, 2] = mc
        i = acc.verts(to3(bore2, off),
                      uv=np.stack([np.arange(L) * rx * TAU / L,
                                   np.full(L, off)], -1),
                      base=base, aux=a4, wear=wear)
        cur = i + np.arange(L)
        bridge(acc, prev, cur, mat, smooth=(off < -ch), wrap=True, flip=False)
        prev = cur
    # the tube's dark interior, seen straight up through the hole
    a4 = np.tile(np.asarray(aux, float).reshape(1, 4), (L, 1))
    a4[:, 0] = 0.0
    idk = acc.verts(to3(bore2 * 0.94, -wall - 0.055),
                    uv=np.zeros((L, 2)), base=(0.012, 0.012, 0.013, base[3]),
                    aux=a4, wear=np.asarray(wear, float))
    bridge(acc, prev, idk + np.arange(L), mat, smooth=False, wrap=True,
           flip=False)
    icd = acc.verts((c - n * (wall + 0.060)).reshape(1, 3), uv=np.zeros((1, 2)),
                    base=(0.010, 0.010, 0.011, base[3]),
                    aux=np.array([[0.0, 0.0, 0.2, aux[3]]]),
                    wear=np.asarray(wear, float).reshape(1, 4))
    acc.fan(idk + np.arange(L), icd, mat, smooth=False, flip=False)
    skip = {(i0 + a, (j0 + b) % K) for a in range(ni) for b in range(nj)}
    return skip, c, n, rx


def zinc_drip(acc, o, dirn, r, length, mat, base, aux, wear, uid=0.0, nseg=12):
    """A frozen zinc icicle: what a hot-dip bath leaves on every downward edge.

    3-6 mm long, so 4-7 screen px, and the reason a galvanised member never
    has a clean arris underneath it.
    """
    o = np.asarray(o, float)
    w = unit(np.asarray(dirn, float))
    u, v, _ = local_frame(w)
    t = np.linspace(0.0, 1.0, 7)
    rr = r * np.sqrt(np.clip(1.0 - t ** 1.7, 0.0, 1.0)) * (
        1.0 + 0.10 * np.sin(t * 9.0 + hash01(uid, "d") * 6.0))
    rr[0] = r * 1.06
    th = np.arange(nseg) * TAU / nseg
    Cp = o[None, :] + w[None, :] * (t[:, None] * length)
    Cp += u[None, :] * (0.16 * r * np.sin(t * 3.4 + hash01(uid, "b") * 5.0))[:, None]
    S = np.stack([rr[:, None] * np.cos(th)[None, :],
                  rr[:, None] * np.sin(th)[None, :]], -1)
    a = np.tile(np.asarray(aux, float).reshape(1, 1, 4), (len(t), nseg, 1)).copy()
    a[..., 0] = 0.55
    G = sweep(acc, Cp, np.tile(u, (len(t), 1)), np.tile(v, (len(t), 1)), S,
              mat, base, a, wear, smooth=True)
    ic = acc.verts((o + w * length * 1.02).reshape(1, 3), uv=np.zeros((1, 2)),
                   base=base, aux=np.asarray(aux, float).reshape(1, 4), wear=wear)
    acc.fan(G[-1], ic, mat, smooth=True, flip=False)


def spatter(acc, ctr, nrm, n, mat, base, aux, wear, uid=0.0, rmin=0.0006,
            rmax=0.0021, spread=0.045):
    """Weld spatter: frozen beads of metal thrown 20-60 mm from the arc."""
    ctr = np.asarray(ctr, float)
    u, v, w = local_frame(nrm)
    for k in range(n):
        a = hash01(uid, "sa", k) * TAU
        d = spread * (0.25 + 0.75 * hash01(uid, "sd", k) ** 0.6)
        r = rmin + (rmax - rmin) * hash01(uid, "sr", k) ** 1.8
        p = ctr + u * (math.cos(a) * d) + v * (math.sin(a) * d)
        dome_head(acc, p, u, v, w, r, r * rnd(0.55, 0.95, uid, "sh", k), mat,
                  base, with_edge(aux, 0.8), wear, nseg=10, nrow=3, flat=0.35)


# --------------------------------------------------------------------------- #
#  7.  PLATES:  an arbitrary shaped plate with real drilled holes               #
# --------------------------------------------------------------------------- #

def loop_outward2(L2):
    """Outward 2D normals of a CCW open/closed loop."""
    L2 = np.asarray(L2, float)
    nxt = np.roll(L2, -1, 0)
    prv = np.roll(L2, 1, 0)
    d1 = nxt - L2
    d2 = L2 - prv
    n1 = np.stack([d1[:, 1], -d1[:, 0]], -1)
    n2 = np.stack([d2[:, 1], -d2[:, 0]], -1)
    return unit(n1 + n2)


def grid_boundary(nv, nu):
    """CCW boundary index pairs of an (nv+1, nu+1) grid."""
    idx = []
    for j in range(nu + 1):
        idx.append((0, j))
    for i in range(1, nv + 1):
        idx.append((i, nu))
    for j in range(nu - 1, -1, -1):
        idx.append((nv, j))
    for i in range(nv - 1, 0, -1):
        idx.append((i, 0))
    return idx


def grid_plate(acc, o, eu, ev, en, G, t, holes, mat, base, aux, wear, uid=0.0,
               chamfer=0.0015, wave=0.00035, face_edge=0.10, hole_ch=0.0008,
               nvring=4, drag=True):
    """A steel plate of arbitrary outline with REAL drilled, chamfered holes.

    G is an (nv+1, nu+1, 2) array of 2D grid points in the (eu, ev) plane,
    o is the plate's mid-thickness origin, en its normal.  `holes` is a list
    of (i, j, radius) naming the CELL a hole is drilled through; the cell is
    remeshed as a circle-to-quad annulus, which gives a clean bore, a real
    chamfer and no boolean.

    The perimeter carries a 1.5 mm chamfer (1.9 screen px) with a 0.35 mm
    flame-cut waviness on it, because a profiled plate edge is never straight
    and at this distance you can see that it isn't.
    """
    G = np.asarray(G, float)
    nv, nu = G.shape[0] - 1, G.shape[1] - 1
    o = _n3(o)
    eu, ev = unit(_n3(eu)), unit(_n3(ev))
    # THE NORMAL IS DERIVED, NOT TRUSTED.  Half the callers hand in a
    # right-handed triple and half a left-handed one (a gusset on the +x chord
    # faces the other way from the one on the -x chord), and a plate whose
    # winding disagrees with its normal renders inside out.  The plate is
    # centred on `o` either way, so deriving it costs the caller nothing.
    en = unit(np.cross(eu, ev))
    hole_by_cell = {(i, j): r for (i, j, r) in holes}

    def to3(Q2, off):
        Q2 = np.asarray(Q2, float).reshape(-1, 2)
        return (o[None, :] + Q2[:, 0:1] * eu[None, :] + Q2[:, 1:2] * ev[None, :]
                + en[None, :] * off)

    idx_top = np.full((nv + 1, nu + 1), -1, np.int64)
    idx_bot = np.full((nv + 1, nu + 1), -1, np.int64)
    flat = G.reshape(-1, 2)
    a4 = np.tile(np.asarray(aux, float).reshape(1, 4), (len(flat), 1))
    a4[:, 0] = face_edge
    i0 = acc.verts(to3(flat, +t * 0.5), uv=flat, base=base, aux=a4, wear=wear)
    idx_top = (i0 + np.arange(len(flat))).reshape(nv + 1, nu + 1)
    i1 = acc.verts(to3(flat, -t * 0.5), uv=flat, base=base, aux=a4, wear=wear)
    idx_bot = (i1 + np.arange(len(flat))).reshape(nv + 1, nu + 1)

    QT, QB = [], []
    for i in range(nv):
        for j in range(nu):
            if (i, j) in hole_by_cell:
                continue
            QT.append([idx_top[i, j], idx_top[i, j + 1],
                       idx_top[i + 1, j + 1], idx_top[i + 1, j]])
            QB.append([idx_bot[i, j], idx_bot[i + 1, j],
                       idx_bot[i + 1, j + 1], idx_bot[i, j + 1]])
    if QT:
        acc.quads(np.array(QT, np.int64), mat, False)
        acc.quads(np.array(QB, np.int64), mat, False)

    # --- the holes ---------------------------------------------------------
    for (i, j, r) in holes:
        cell = np.array([G[i, j], G[i, j + 1], G[i + 1, j + 1], G[i + 1, j]])
        loop2 = []
        for (a, b) in ((G[i, j], G[i, j + 1]), (G[i, j + 1], G[i + 1, j + 1]),
                       (G[i + 1, j + 1], G[i + 1, j]), (G[i + 1, j], G[i, j])):
            f = np.linspace(0.0, 1.0, 7)[:-1]
            loop2.append(a[None, :] + (b - a)[None, :] * f[:, None])
        loop2 = np.concatenate(loop2, 0)
        Lc = len(loop2)
        ctr = cell.mean(0)
        rx, ry = _rxy(r)
        R2, ang = cell_rings_ell(loop2, ctr, rx + hole_ch, ry + hole_ch,
                                 nvring, grade=1.6)
        rings_t, rings_b = [], []
        for k in range(nvring + 1):
            aa = np.tile(np.asarray(aux, float).reshape(1, 4), (Lc, 1))
            aa[:, 0] = 0.72 if k == 0 else face_edge
            aa[:, 2] = 0.55 if k == 0 else 0.15
            it = acc.verts(to3(R2[k], +t * 0.5), uv=R2[k], base=base, aux=aa,
                           wear=wear)
            ib = acc.verts(to3(R2[k], -t * 0.5), uv=R2[k], base=base, aux=aa,
                           wear=wear)
            rings_t.append(it + np.arange(Lc))
            rings_b.append(ib + np.arange(Lc))
        for k in range(nvring):
            bridge(acc, rings_t[k], rings_t[k + 1], mat, False, True, flip=True)
            bridge(acc, rings_b[k], rings_b[k + 1], mat, False, True, flip=False)
        # The annulus's OUTER ring lies exactly on the cell boundary, so it
        # meets the neighbouring cells' quads along a straight line with no
        # gap.  It is deliberately NOT stitched to the four grid corners: the
        # first version fanned it to them and every one of those triangles was
        # degenerate, because the ring points are collinear with the edge they
        # sit on.  A collinear T-junction is invisible; a zero-area triangle is
        # a shading artefact.
        # bore
        bore2 = np.stack([ctr[0] + rx * np.cos(ang),
                          ctr[1] + ry * np.sin(ang)], -1)
        for (side, ring, sgn) in ((+1, rings_t[0], +1.0), (-1, rings_b[0], -1.0)):
            aa = np.tile(np.asarray(aux, float).reshape(1, 4), (Lc, 1))
            aa[:, 0] = 0.9
            aa[:, 2] = 0.95
            ii = acc.verts(to3(bore2, sgn * (t * 0.5 - hole_ch)), uv=bore2,
                           base=base, aux=aa, wear=wear)
            if side > 0:
                bore_t = ii + np.arange(Lc)
            else:
                bore_b = ii + np.arange(Lc)
        bridge(acc, rings_t[0], bore_t, mat, False, True, flip=False)
        bridge(acc, bore_t, bore_b, mat, True, True, flip=False)
        bridge(acc, bore_b, rings_b[0], mat, False, True, flip=False)

    # --- perimeter band, with the flame-cut chamfer -------------------------
    bnd = grid_boundary(nv, nu)
    inner2 = np.array([G[i, j] for (i, j) in bnd])
    nrm2 = loop_outward2(inner2)
    Lb = len(inner2)
    wv = np.array([wave * (hash01(uid, "w", k) - 0.5) * 2.0 for k in range(Lb)])
    wv += np.array([wave * 0.6 * math.sin(k * 0.9 + hash01(uid, "w2") * 6.0)
                    for k in range(Lb)])
    outer2 = inner2 + nrm2 * (chamfer + wv)[:, None]
    it = np.array([idx_top[i, j] for (i, j) in bnd])
    ib = np.array([idx_bot[i, j] for (i, j) in bnd])
    rings = [it]
    for (off, ee) in ((+t * 0.5 - chamfer, 1.0), (-t * 0.5 + chamfer, 1.0)):
        aa = np.tile(np.asarray(aux, float).reshape(1, 4), (Lb, 1))
        aa[:, 0] = ee
        # drag lines: an oxy-cut edge is scored down its thickness
        dl = (0.00016 * np.sin(np.arange(Lb) * 2.7 + hash01(uid, "dl") * 6.0)
              if drag else np.zeros(Lb))
        ii = acc.verts(to3(outer2 + nrm2 * dl[:, None], off),
                       uv=outer2, base=base, aux=aa, wear=wear)
        rings.append(ii + np.arange(Lb))
    rings.append(ib)
    for k in range(3):
        bridge(acc, rings[k], rings[k + 1], mat, False, True, flip=True)
    return idx_top, idx_bot


def rect_grid(hw, hd, nu, nv, taper=0.0, notch=0.0, clip=0.0, skewv=0.0):
    """(nv+1, nu+1, 2) grid on a shaped quadrilateral.

    u runs -hw..hw, v runs -hd..hd.  `taper` narrows one end, `clip` cuts the
    two far corners, `notch` cuts a re-entrant bite out of the near edge and
    `skewv` shears it.  Between them these four numbers give every node plate
    its own outline without a boolean anywhere.
    """
    uu = np.linspace(-hw, hw, nu + 1)
    vv = np.linspace(-hd, hd, nv + 1)
    U, V = np.meshgrid(uu, vv)
    tt = (U + hw) / (2.0 * hw)
    V = V * (1.0 - taper * tt)
    U = U + skewv * V
    # THE CORNER CLIP AND THE NOTCH MUST BE CONTINUOUS IN v.  The first version
    # gated them on a boolean (|v| > 0.55*hd), which meant one grid row was
    # pulled in by 40 mm and its neighbour by nothing: every clipped plate grew
    # a 40 mm rectangular step in its outline, 50 screen px of sawtooth on an
    # edge that a plate profiler cuts in one smooth motion.  Both are ramps now.
    if clip > 0.0:
        f = np.clip((U - (hw - clip)) / max(clip, 1e-9), 0.0, 1.0)
        f = f * f * (3.0 - 2.0 * f)
        s = np.clip((np.abs(V) / max(hd, 1e-9) - 0.42) / 0.58, 0.0, 1.0)
        V = V - np.sign(V) * (f * clip * 0.80) * (s * s * (3.0 - 2.0 * s))
    if notch > 0.0:
        gg = np.exp(-((U + hw * 0.15) / (hw * 0.42)) ** 2)
        s = np.clip((np.abs(V) / max(hd, 1e-9) - 0.60) / 0.40, 0.0, 1.0)
        V = V - np.sign(V) * (s * s * (3.0 - 2.0 * s)) * gg * notch
    return np.stack([U, V], -1)


# --------------------------------------------------------------------------- #
#  8.  FASTENERS                                                                #
# --------------------------------------------------------------------------- #

def hex_head(acc, o, u, v, w, af, h, mat, base, aux, wear, nseg=40, uid=0.0,
             mark=True):
    """A hex bolt head: the 30 deg chamfer, the bearing face, the grade mark.

    The chamfer is what makes a head read as a head - it turns the six corners
    into a circle on the top face and leaves those curved intersection lines
    running down the flats.  Modelled by intersecting the hex prism with a
    cone, exactly as marshal_post_column does for its nuts, so a bolt and a nut
    on the same joint are the same family of object.
    """
    o, u, v, w = _n3(o), _n3(u), _n3(v), _n3(w)
    th = np.arange(nseg) * TAU / nseg
    ap = af * 0.5
    hexr = ap / np.cos(((th + math.pi / 6) % (math.pi / 3)) - math.pi / 6)
    rface = ap * 1.012
    ch = (hexr.max() - rface) * math.tan(math.radians(30.0))
    zs = np.concatenate([np.linspace(0.0, 0.0016, 3),
                         np.linspace(0.0016, h - ch, 4)[1:],
                         np.linspace(h - ch, h, 6)[1:]])
    Rr = np.minimum(hexr[None, :],
                    (rface + np.minimum(zs, 1e9) * 0.0 + (h - zs)
                     * math.tan(math.radians(60.0)))[:, None])
    Rr[0] = hexr * 1.004                       # the bearing face is slightly proud
    Cp = o[None, :] + w[None, :] * zs[:, None]
    S = np.stack([Rr * np.cos(th)[None, :], Rr * np.sin(th)[None, :]], -1)
    a = np.tile(np.asarray(aux, float).reshape(1, 1, 4), (len(zs), nseg, 1)).copy()
    a[..., 0] = 0.30 + 0.65 * (np.abs(hexr[None, :] - Rr) < 1e-6)
    a[..., 2] = 0.30
    G = sweep(acc, Cp, np.tile(u, (len(zs), 1)), np.tile(v, (len(zs), 1)), S,
              mat, base, a, wear, smooth=False)
    # BEARING FACE.  It has to start from the sweep's OWN first ring, which is
    # the full hexagon, not from the chamfer circle: taking the annulus from
    # `rface` instead left a 2.1 mm crescent of open mesh at each of the six
    # corners of every one of the 500 bolts - 2.6 screen px of hole under the
    # head, on the surface the lens is pointed at.
    rr = af * 0.30
    P = o[None, :] + rr * (np.cos(th)[:, None] * u[None, :]
                           + np.sin(th)[:, None] * v[None, :])
    aa = np.tile(np.asarray(aux, float).reshape(1, 4), (nseg, 1))
    aa[:, 0] = 0.45
    aa[:, 2] = 0.85
    ii = acc.verts(P, uv=np.stack([th * rr, np.zeros(nseg)], -1), base=base,
                   aux=aa, wear=wear)
    inner = ii + np.arange(nseg)
    bridge(acc, G[0], inner, mat, smooth=False, flip=True)
    ic = acc.verts((o).reshape(1, 3), uv=np.zeros((1, 2)), base=base,
                   aux=np.asarray(aux, float).reshape(1, 4), wear=wear)
    acc.fan(inner, ic, mat, smooth=False, flip=True)
    # top face, dished 0.2 mm by the forging die, with the grade mark ribs
    top = [G[-1]]
    for (rr2, zz) in ((rface * 0.55, h - 0.00018), (0.0, h - 0.00026)):
        if rr2 <= 0.0:
            ic2 = acc.verts((o + w * zz).reshape(1, 3), uv=np.zeros((1, 2)),
                            base=base, aux=np.asarray(aux, float).reshape(1, 4),
                            wear=wear)
            acc.fan(top[-1], ic2, mat, smooth=False, flip=False)
            break
        P = o[None, :] + w[None, :] * zz + rr2 * (
            np.cos(th)[:, None] * u[None, :] + np.sin(th)[:, None] * v[None, :])
        aa = np.tile(np.asarray(aux, float).reshape(1, 4), (nseg, 1))
        aa[:, 0] = 0.15
        ii = acc.verts(P, uv=np.stack([th * rr2, np.full(nseg, zz)], -1),
                       base=base, aux=aa, wear=wear)
        cur = ii + np.arange(nseg)
        bridge(acc, top[-1], cur, mat, smooth=False, flip=False)
        top.append(cur)
    if mark:
        # three radial grade ribs, 0.35 mm proud: the property-class marking
        for k in range(3):
            a0 = hash01(uid, "gm") * TAU + k * TAU / 3.0
            p = o + w * h + (u * math.cos(a0) + v * math.sin(a0)) * (rface * 0.62)
            dome_head(acc, p, u, v, w, rface * 0.16, 0.00035, mat, base,
                      with_edge(aux, 0.6), wear, nseg=8, nrow=2, flat=0.5)


def dti_washer(acc, o, u, v, w, r_out, r_in, t, mat, base, aux, wear, uid=0.0,
               nbump=5, squash=0.55):
    """A load-indicating (DTI) washer: five bumps, squashed by the tightening.

    0.5 mm of bump is 0.6 screen px - right at the limit, which is exactly why
    it belongs in the mesh: it is the difference between 'a washer' and 'a
    washer that has been torqued'.  The squash factor is per-bolt, so some
    still have a feeler gap and some are flat.
    """
    o, u, v, w = _n3(o), _n3(u), _n3(v), _n3(w)
    nseg = 40
    th = np.arange(nseg) * TAU / nseg
    ph = hash01(uid, "dph") * TAU
    bump = np.zeros(nseg)
    for k in range(nbump):
        a0 = ph + k * TAU / nbump
        d = np.abs(((th - a0 + math.pi) % TAU) - math.pi)
        bump += np.exp(-(d / 0.30) ** 2)
    bump *= 0.00052 * (1.0 - squash)
    rings = []
    rm = 0.5 * (r_in + r_out)
    for (rr, zz, ee) in ((r_in, 0.0, 0.6), (r_out, 0.0, 0.9),
                         (r_out, t, 0.9), (rm, t, 0.3), (r_in, t, 0.6)):
        bz = (bump if (zz > 0 and abs(rr - rm) < (r_out - r_in) * 0.30)
              else np.zeros(nseg))
        P = o[None, :] + w[None, :] * (zz + bz)[:, None] + rr * (
            np.cos(th)[:, None] * u[None, :] + np.sin(th)[:, None] * v[None, :])
        aa = np.tile(np.asarray(aux, float).reshape(1, 4), (nseg, 1))
        aa[:, 0] = ee
        aa[:, 2] = 0.7
        ii = acc.verts(P, uv=np.stack([th * rr, np.full(nseg, zz)], -1),
                       base=base, aux=aa, wear=wear)
        rings.append(ii + np.arange(nseg))
    for k in range(len(rings) - 1):
        bridge(acc, rings[k], rings[k + 1], mat, smooth=(k >= 2), flip=False)
    bridge(acc, rings[-1], rings[0], mat, smooth=False, flip=False)


def bolt(acc, o, axis, spec, mat, base, aux, wear, ref=(0.0, 0.0, 1.0)):
    """A whole bolted connection: head, washers, shank, nut, thread, tail.

    `o` is the hole centre on the HEAD side face of the pack; `axis` points
    THROUGH the pack toward the nut; `spec['grip']` is the pack thickness.  If
    spec['head_down'] the installer put it in the other way up, which on the
    underside of a truss decides whether the lens sees a hex head or a nut and
    three threads - and both happen on a real job.
    """
    o = _n3(o)
    w = unit(_n3(axis))
    if spec["head_down"]:
        o = o + w * spec["grip"]
        w = -w
    u, v, _ = local_frame(w, ref)
    R = rot_axis(w, math.degrees(spec["spin"]))
    u = R @ u
    v = np.cross(w, u)
    af, hh, nh = spec["af"], spec["head_h"], spec["nut_h"]
    wo, wt, sr = spec["wash_od"], spec["wash_t"], spec["shank_r"]
    grip, pitch, tail = spec["grip"], spec["pitch"], spec["tail"]
    uid = spec["uid"]

    # --- head side ---------------------------------------------------------
    z = 0.0
    if spec["dti"]:
        dti_washer(acc, o - w * wt, u, v, w, wo * 0.52, sr * 1.12, wt, mat,
                   base, aux, wear, uid=uid, squash=spec["tight"])
        z -= wt
    else:
        washer(acc, o - w * wt, u, v, w, wo * 0.5, sr * 1.10, wt, mat, base,
               with_edge(aux, 0.7), wear, nseg=36)
        z -= wt
    # -v, not v: hex_head sweeps about its OWN third axis, so the triple has to
    # stay right-handed when that axis is reversed.  cross(u, -v) = -w.
    hex_head(acc, o + w * z, u, -v, -w, af, hh, mat, base, aux, wear, uid=uid)
    # --- shank through the pack -------------------------------------------
    th = np.arange(20) * TAU / 20
    zs = np.array([0.0, grip * 0.5, grip])
    Cp = o[None, :] + w[None, :] * zs[:, None]
    S = np.stack([np.tile(sr * np.cos(th), (3, 1)),
                  np.tile(sr * np.sin(th), (3, 1))], -1)
    sweep(acc, Cp, np.tile(u, (3, 1)), np.tile(v, (3, 1)), S, mat, base,
          with_edge(aux, 0.1), wear, smooth=True)
    # --- nut side ----------------------------------------------------------
    p = o + w * grip
    washer(acc, p, u, v, w, wo * 0.5, sr * 1.10, wt, mat, base,
           with_edge(aux, 0.7), wear, nseg=36)
    p = p + w * wt
    thread_len = nh * (2.0 if spec["double_nut"] else 1.0) + tail + 0.004
    thread_stud(acc, p - w * 0.004, u, v, w, sr * 0.985, pitch, thread_len,
                mat, base, with_edge(aux, 0.55), wear, nseg=26,
                rows_per_pitch=5, uid=uid)
    hex_nut(acc, p, u, v, w, af, nh, sr * 0.90, mat, base, aux, wear,
            nseg=36, pitch=pitch, uid=uid)
    p = p + w * nh
    if spec["double_nut"]:
        hex_nut(acc, p, u, v, w, af, nh * 0.62, sr * 0.90, mat, base, aux,
                wear, nseg=36, pitch=pitch, uid=uid + "b")
        p = p + w * nh * 0.62
    if spec["nyloc"]:
        # the polymer insert collar, proud of the nut and a different colour
        nsg = 36
        ang = np.arange(nsg) * TAU / nsg
        rings = []
        for (rad, zz) in ((af * 0.52, 0.0), (af * 0.52, 0.0032),
                          (af * 0.32, 0.0032)):
            P = p[None, :] + w[None, :] * zz + rad * (
                np.cos(ang)[:, None] * u[None, :]
                + np.sin(ang)[:, None] * v[None, :])
            aa = np.tile(np.asarray(aux, float).reshape(1, 4), (nsg, 1))
            aa[:, 0] = 0.8
            aa[:, 2] = 0.0
            ii = acc.verts(P, uv=np.stack([ang * rad, np.full(nsg, zz)], -1),
                           base=(0.055, 0.048, 0.028, base[3]), aux=aa,
                           wear=wear)
            rings.append(ii + np.arange(nsg))
        for k in range(2):
            bridge(acc, rings[k], rings[k + 1], mat, smooth=False, flip=False)
    return p + w * tail


def bolt_cluster(acc, pts, axis, mat, base, aux, wear, uid="c", size="M20",
                 grip=0.036, ref=(0.0, 0.0, 1.0), flip=None):
    """A pattern of bolts, each with its OWN geometry.  Returns the specs."""
    out = []
    for k, p in enumerate(pts):
        sp = bolt_spec("%s_%d" % (uid, k), size=size, grip=grip, flip=flip)
        bolt(acc, p, axis, sp, mat, base, aux, wear, ref=ref)
        out.append(sp)
    return out


# --------------------------------------------------------------------------- #
#  9.  MEMBERS:  a section swept between two CUT PLANES                         #
# --------------------------------------------------------------------------- #
#
# Every web member in a truss is cut to fit the face it lands on, and the cut
# is oblique wherever the member is.  Modelling members as capsules between two
# points and hoping the weld hides the difference is what makes a rendered
# truss look like a diagram, so the sweep here solves, per section vertex, the
# parameter at which that vertex's own generator meets the landing plane.  The
# end ring then lies EXACTLY on the chord face, which is also what lets the
# fillet weld be run round it with no guessing.

def plane_param(p0, w, dk, q, n):
    """s such that (p0 + w*s + dk) lies on the plane (q, n).  dk is (K,3)."""
    num = (np.asarray(q, float)[None, :] - p0[None, :] - dk) @ np.asarray(n, float)
    den = float(np.dot(w, np.asarray(n, float)))
    if abs(den) < 1e-6:
        den = 1e-6 * (1.0 if den >= 0 else -1.0)
    return num / den


def member_rows(smin, smax, res=1.0, ends=0.055, fine=0.0045, base=0.022):
    """Row parameters along a member: dense at both welded ends."""
    L = float(smax - smin)
    base = base / max(res, 0.25)
    fine = fine / max(res, 0.25)
    a = np.arange(0.0, L + base, base)
    b = np.arange(0.0, min(ends, L * 0.45) + fine, fine)
    c = L - b
    t = np.unique(np.clip(np.concatenate([a, b, c, [0.0, L]]), 0.0, L))
    return t / max(L, 1e-9)


def prism_member(acc, p0, p1, S, E, mat, base, aux, wear, uid="m",
                 up=(0.0, 0.0, 1.0), cut0=None, cut1=None, bow=0.0012,
                 res=1.0, rowbase=0.022, cap0=True, cap1=True,
                 disp=None, smooth=True, uoff=0.0, end_edge=0.0):
    """Sweep the closed section S from p0 to p1 between two cut planes.

    cut0 / cut1 are (point, normal) or None for a square cut at the end point.
    Returns (IDX, P, u, v, w, ring0_pts, ring1_pts).
    """
    p0, p1 = _n3(p0), _n3(p1)
    d = p1 - p0
    L = float(np.linalg.norm(d))
    w = d / max(L, 1e-9)
    u, v, _ = local_frame(w, up)
    S = np.asarray(S, float)
    K = len(S)
    dk = S[:, 0:1] * u[None, :] + S[:, 1:2] * v[None, :]
    s0 = plane_param(p0, w, dk, p0, w) if cut0 is None else \
        plane_param(p0, w, dk, cut0[0], cut0[1])
    s1 = plane_param(p0, w, dk, p1, w) if cut1 is None else \
        plane_param(p0, w, dk, cut1[0], cut1[1])
    t = member_rows(0.0, 1.0, res=res, ends=min(0.10, 0.35), fine=0.006,
                    base=rowbase / max(L, 1e-9))
    M = len(t)
    ss = s0[None, :] + (s1 - s0)[None, :] * t[:, None]
    # lack of straightness: every rolled member is bowed, 1-2 mm over 2 m
    bdir = unit(np.cross(w, u)) if abs(bow) > 0 else u
    ph = hash01(uid, "bow") * TAU
    off = bow * np.sin(math.pi * t) * math.cos(ph)
    off2 = bow * 0.5 * np.sin(math.pi * t) * math.sin(ph)
    Cp = (p0[None, None, :] + w[None, None, :] * ss[:, :, None]
          + bdir[None, None, :] * off[:, None, None]
          + u[None, None, :] * off2[:, None, None])
    S3 = np.broadcast_to(S[None, :, :], (M, K, 2)).copy()
    if disp is not None:
        n2 = section_outward(S)
        S3 = S3 + n2[None, :, :] * disp(t, S)[:, :, None]
    a4 = np.tile(np.asarray(aux, float).reshape(1, 1, 4), (M, K, 1)).copy()
    a4[..., 0] = np.asarray(E, float)[None, :]
    if end_edge:
        # A CIRCULAR section has no arris, so its edge-exposure is uniformly
        # low and it never chips - which is right along the barrel and wrong
        # at the ends, where the weld toe, the handling damage and the
        # touch-up all live.  Raise it over the last 60 mm of each end.
        w60 = 0.060 / max(L, 1e-6)
        boost = end_edge * (np.exp(-(t / w60) ** 2)
                            + np.exp(-((1.0 - t) / w60) ** 2))
        a4[..., 0] = np.clip(a4[..., 0] + boost[:, None], 0.0, 1.0)
    IDX = sweep(acc, Cp, np.tile(u, (M, 1)), np.tile(v, (M, 1)), S3, mat, base,
                a4, wear, smooth=smooth, uoff=uoff)
    P = (Cp + S3[:, :, 0:1] * u[None, None, :] + S3[:, :, 1:2] * v[None, None, :])
    if cap0:
        ic = acc.verts(P[0].mean(0).reshape(1, 3), uv=np.zeros((1, 2)),
                       base=base, aux=np.asarray(aux, float).reshape(1, 4),
                       wear=wear)
        acc.fan(IDX[0], ic, mat, smooth=False, flip=True)
    if cap1:
        ic = acc.verts(P[-1].mean(0).reshape(1, 3), uv=np.zeros((1, 2)),
                       base=base, aux=np.asarray(aux, float).reshape(1, 4),
                       wear=wear)
        acc.fan(IDX[-1], ic, mat, smooth=False, flip=False)
    return IDX, P, u, v, w


def resample_loop(P, step):
    """Resample a closed 3D polyline to roughly `step` spacing."""
    P = np.asarray(P, float)
    Q = np.vstack([P, P[:1]])
    d = np.linalg.norm(np.diff(Q, axis=0), axis=1)
    s = np.concatenate([[0.0], np.cumsum(d)])
    n = max(12, int(round(s[-1] / step)))
    ss = np.linspace(0.0, s[-1], n, endpoint=False)
    out = np.empty((n, 3))
    for k in range(3):
        out[:, k] = np.interp(ss, s, Q[:, k])
    return out


def ring_weld(acc, ring, face_n, axis_w, mat, base, aux, wear, uid="w",
              leg=0.0075, step=0.0026, nsec=11, pitch=0.0042, mat_only=None):
    """The fillet weld where a member lands on a flat face.

    The bead is run round the member's OWN end ring, resampled to 2.6 mm so
    the 4.2 mm stack-of-dimes ripple - 5 screen px - actually resolves.  This
    is the single most repeated object on the truss: 250-odd of them, and
    every one of them is on camera on the underside.
    """
    R = resample_loop(ring, step)
    ctr = R.mean(0)
    n = unit(np.asarray(face_n, float))
    w = unit(np.asarray(axis_w, float))
    rad = R - ctr[None, :]
    rad = rad - n[None, :] * (rad @ n)[:, None]
    rad = unit(rad)
    A = R + rad * leg * 1.35
    B = R + w[None, :] * (leg * 1.05)
    NA = np.tile(n, (len(R), 1))
    NB = rad
    return weld_bead(acc, A, B, NA, NB, mat, base, with_weld(aux, 1.0), wear,
                     bulge=leg * 0.34, nsec=nsec, ripple=0.30, pitch=pitch,
                     uid=hash01(uid), closed=True, flip=False)


def seam_weld(acc, A, B, NA, NB, mat, base, aux, wear, uid="s", step=0.005,
              bulge=0.0022, nsec=7, pitch=0.012):
    """A long machine-run fillet seam.

    A production seam laid by a submerged-arc or MIG gun is NOT a stack of
    dimes - it is a smooth, slightly wandering fillet with a 10-15 mm
    undulation, and pretending otherwise on a 23 m run would be a lie that
    also cost 400,000 vertices.  Hand welds at the nodes get `ring_weld`.
    """
    A = np.asarray(A, float)
    B = np.asarray(B, float)
    n = max(6, int(round(np.linalg.norm(A[-1] - A[0]) / step)))
    t = np.linspace(0.0, 1.0, n)
    idx = np.linspace(0.0, len(A) - 1.0, n)
    Ai = np.stack([np.interp(idx, np.arange(len(A)), A[:, k]) for k in range(3)], -1)
    Bi = np.stack([np.interp(idx, np.arange(len(B)), B[:, k]) for k in range(3)], -1)
    NAi = np.tile(np.asarray(NA, float).reshape(-1, 3)[0], (n, 1)) \
        if np.ndim(NA) == 1 else np.stack(
            [np.interp(idx, np.arange(len(NA)), np.asarray(NA)[:, k])
             for k in range(3)], -1)
    NBi = np.tile(np.asarray(NB, float).reshape(-1, 3)[0], (n, 1)) \
        if np.ndim(NB) == 1 else np.stack(
            [np.interp(idx, np.arange(len(NB)), np.asarray(NB)[:, k])
             for k in range(3)], -1)
    return weld_bead(acc, Ai, Bi, NAi, NBi, mat, base, with_weld(aux, 1.0),
                     wear, bulge=bulge, nsec=nsec, ripple=0.16, pitch=pitch,
                     uid=hash01(uid), closed=False, flip=False)


# --------------------------------------------------------------------------- #
# 10.  THE CHORD                                                                #
# --------------------------------------------------------------------------- #

def chord_frame(side, level, y):
    """Axis point and the section's across/up unit axes at span station y."""
    p = chord_at(side, level, float(y))
    tw = float(twist(np.array([float(y)]))[0])
    ex = np.array([math.cos(tw), 0.0, math.sin(tw)])
    ez = np.array([-math.sin(tw), 0.0, math.cos(tw)])
    return p, ex, ez


def chord_face(side, level, y, which):
    """(point, outward normal) of a named face of a chord at station y.

    which: 'out' (away from the truss centreline), 'in', 'up', 'down'.
    """
    p, ex, ez = chord_frame(side, level, y)
    h = CHORD_W * 0.5
    if which == "out":
        return p + ex * (side * h), ex * side
    if which == "in":
        return p - ex * (side * h), -ex * side
    if which == "up":
        return p + ez * h, ez
    return p - ez * h, -ez


def chord_disp(ys, S, E, nodes, uid="c"):
    """Radial surface displacement on a chord, (M,K), metres.

    Three things that are true of every welded hollow section and that all
    read at 0.8 mm/px:
      1. WELD PULL-IN.  Every node weld shrinks as it cools and sucks the
         chord face in by 0.4-1.1 mm over a ~90 mm patch.  On a 23 m chord
         with 17 nodes that is a periodic scallop down the soffit and it is
         the single most recognisable signature of a welded truss.
      2. FACE DISHING.  A hot-formed SHS face is never flat; it is dished
         0.3-0.5 mm between the corner radii.
      3. MILL WAVINESS, a slow 0.25 mm undulation along the length.
    """
    M, K = len(ys), len(S)
    S = np.asarray(S, float)
    flat = np.asarray(E, float) < 0.35          # the flat runs, not the corners
    d = np.zeros((M, K))
    # 1. pull-in at every node
    pull = np.zeros(M)
    for j, yn in enumerate(nodes):
        amp = 0.00040 + 0.00070 * hash01(uid, "pull", j)
        pull -= amp * np.exp(-((ys - yn) / 0.090) ** 2)
    d += pull[:, None] * flat[None, :]
    # 2. face dishing: parabolic across each flat run
    run = np.zeros(K)
    i = 0
    while i < K:
        if not flat[i]:
            i += 1
            continue
        j = i
        while j < K and flat[j]:
            j += 1
        n = j - i
        if n > 1:
            tt = (np.arange(n) + 0.5) / n
            run[i:j] = -(1.0 - (2.0 * tt - 1.0) ** 2)
        i = j
    d += (0.00030 + 0.00018 * np.sin(ys * 0.41)[:, None]) * run[None, :]
    # 3. mill waviness along the length, and a slow corner-radius drift
    d += 0.00022 * np.sin(ys * 1.9 + hash01(uid, "w1") * 6.0)[:, None]
    d += 0.00013 * np.sin(ys * 5.7 + hash01(uid, "w2") * 6.0)[:, None] \
        * (1.0 - flat)[None, :]
    d += 0.00035 * np.sin(ys * 0.23 + hash01(uid, "cr") * 6.0)[:, None] \
        * (1.0 - flat)[None, :]
    return d


def build_chord_piece(acc, side, level, y0, y1, mats_idx, base, aux, wear,
                      drains=(), res=1.0, uid="ch"):
    """One shop length of one chord: SHS 200 x 200 x 10, cambered, with real
    galvanising drain holes punched through the soffit."""
    nc, ns = 9, 14
    S, E = rrect_section(CHORD_W, CHORD_W, CHORD_R, nc=nc, ns=ns)
    K = len(S)
    # rows: 30 mm plain, 6 mm at the nodes, 4 mm at the ends, and an explicit
    # 8 mm cluster wherever a hole has to be punched
    rows = [np.arange(y0, y1 + 0.030, 0.030 / max(res, 0.3))]
    for yn in STATIONS:
        if y0 - 0.25 < yn < y1 + 0.25:
            rows.append(np.linspace(max(yn - 0.22, y0), min(yn + 0.22, y1), 46))
    rows.append(np.linspace(y0, min(y0 + 0.09, y1), 22))
    rows.append(np.linspace(max(y1 - 0.09, y0), y1, 22))
    for (yh, _r) in drains:
        rows.append(yh + np.arange(-5, 6) * 0.0045)
    ys = np.unique(np.clip(np.concatenate(rows), y0, y1))
    M = len(ys)
    P0 = chord_points(side, level, ys)
    tw = twist(ys)
    # U = -ex, V = +ez.  THE SIGN IS NOT COSMETIC: `sweep` builds its faces on
    # the convention cross(U, V) == the sweep direction, which here is +y.
    # cross(+ex, +ez) is -y, so a chord swept with the obvious frame comes out
    # inside out along its whole 23 m.  Negating U fixes the winding and keeps
    # +V = up, which is what the soffit column index below depends on.
    U = np.stack([-np.cos(tw), np.zeros(M), -np.sin(tw)], -1)
    V = np.stack([-np.sin(tw), np.zeros(M), np.cos(tw)], -1)
    disp = chord_disp(ys, S, E, STATIONS, uid=uid)
    n2 = section_outward(S)
    S3 = np.broadcast_to(S[None, :, :], (M, K, 2)) + n2[None, :, :] * disp[:, :, None]
    a4 = np.tile(np.asarray(aux, float).reshape(1, 1, 4), (M, K, 1)).copy()
    a4[..., 0] = np.asarray(E, float)[None, :]
    IDX = sweep(acc, P0, U, V, S3, mats_idx, base, a4, wear, smooth=False,
                faces=False)
    Pw = (P0[:, None, :] + S3[:, :, 0:1] * U[:, None, :]
          + S3[:, :, 1:2] * V[:, None, :])
    # the soffit face column range: rrect_section lays the -y (here -V, i.e.
    # DOWN) run last, so it is the final `ns` entries
    j_down0 = 4 * nc + 3 * ns
    skip = set()
    holes_made = []
    for (yh, rh) in drains:
        i_c = int(np.argmin(np.abs(ys - yh)))
        if i_c < 5 or i_c > M - 6:
            continue
        # OFF THE CENTRELINE.  The drains were on the middle of the soffit
        # face, which is exactly where the 41 mm service channel is welded, so
        # all 18 of them were built and all 18 were invisible behind it.  A
        # detailer would have moved them; so does this.  +-43 mm puts the bore
        # 16 mm clear of the channel's edge and leaves the zinc icicle hanging
        # in the open beside it.
        j_c = j_down0 + (ns - 3 if hash01(uid, "hj", yh) > 0.5 else 3)
        # 24 boundary points, not 14: at 12 mm diameter a 14-point bore is
        # an octagon whose facets are 2.7 mm = 3.4 screen px, and the lens
        # looks straight into it.
        sk, c, n, _ = punch_hole(acc, Pw, IDX, i_c - 4, j_c - 2, rh, CHORD_T,
                                 mats_idx, base, aux, wear,
                                 uid=hash01(uid, "dh", yh), ni=8, nj=4)
        skip |= sk
        holes_made.append((c, n, rh))
    acc.quads(swept_quads(IDX, skip), mats_idx, False)
    # end caps (they live inside the splice / end plates, but the mesh closes)
    for (row, flip) in ((0, True), (M - 1, False)):
        ic = acc.verts(Pw[row].mean(0).reshape(1, 3), uv=np.zeros((1, 2)),
                       base=base, aux=np.asarray(aux, float).reshape(1, 4),
                       wear=wear)
        acc.fan(IDX[row], ic, mats_idx, smooth=False, flip=flip)
    return Pw, IDX, ys, holes_made


# --------------------------------------------------------------------------- #
# 11.  THE ASSEMBLY                                                             #
# --------------------------------------------------------------------------- #

class Truss:
    __slots__ = ("objects", "mounts", "stats", "place", "meta")

    def __init__(self):
        self.objects = []
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


def gantry_to_world():
    """PUBLIC.  (R 3x3, t 3) taking gantry-local -> world.

    The gantry stands on the start/finish line: circuit (x, y) = (0, 0), which
    world_contract puts at world (329.396, 169.820) with the circuit frame
    rotated ROT_DEG = 40 deg about z.  z is shared, because z = 0.000 is the
    pit-straight racing surface in both frames.
    """
    wx, wy = C.circuit_to_world(0.0, 0.0)
    R = rotz(C.ROT_DEG)
    t = np.array([float(wx), float(wy), 0.0])
    return R, t


def _bay_pattern(i):
    """Which way the side-face diagonal leans in bay i."""
    return 1 if (i % 2 == 0) else -1


def build(coll_name=ROOT_COLL, place=None, res=1.0, verbose=True):
    """Build the truss.  Three objects, split at the two field splices."""
    mats = materials()
    coll = _coll(coll_name)
    A = [Acc(PFX + "Truss_" + s) for s in SEG_NAMES]
    T = Truss()
    T.place = place
    cnt = dict(bolts=0, welds=0, node_plates=0, plates=0, members=0,
               drains=0, drips=0)
    node_shapes, bolt_shapes, edge_shapes = set(), set(), set()

    def acc_for(y):
        return A[segment_of(y)]

    # ---- 1. the four chords, in three shop lengths each -------------------
    gap = SPLICE_GAP * 0.5
    cuts = [(-END_Y, SPLICE_Y[0] - gap - SPLICE_T),
            (SPLICE_Y[0] + gap + SPLICE_T, SPLICE_Y[1] - gap - SPLICE_T),
            (SPLICE_Y[1] + gap + SPLICE_T, END_Y)]
    chord_drains = {}
    for level in (0, 1):
        for side in (-1, 1):
            for seg, (ya, yb) in enumerate(cuts):
                uid = "chord%d%d%d" % (level, side + 1, seg)
                dr = []
                if level == 0:                       # drains on the soffit only
                    for f in (0.10, 0.5, 0.90):
                        yh = ya + (yb - ya) * f
                        dr.append((yh, 0.0060))
                pw, idx, ys, made = build_chord_piece(
                    A[seg], side, level, ya, yb, MAT_PAINT,
                    *ch_paint(member=0.10 + 0.2 * level, uid=hash01(uid)),
                    drains=dr, res=res, uid=uid)
                chord_drains[(level, side, seg)] = made
                cnt["members"] += 1
                cnt["drains"] += len(made)
                # a zinc icicle under every drain hole: a hot-dip bath leaves
                # one every time, and it is 5 px of hanging metal
                for (c, n, rh) in made:
                    b2, a2, w2 = ch_galv(member=0.9, uid=hash01(uid, "drip"))
                    zinc_drip(A[seg], c + n * 0.0002, n, rh * 0.38,
                              rnd(0.005, 0.0125, uid, "dl", c[1]), MAT_GALV,
                              b2, a2, w2, uid=hash01(uid, "dr", c[1]))
                    cnt["drips"] += 1

    # ---- 2. the side faces: verticals and diagonals -----------------------
    for side in (-1, 1):
        for i, y in enumerate(STATIONS):
            pu, nu_ = chord_face(side, 0, y, "up")
            pd, nd = chord_face(side, 1, y, "down")
            b, a, w = ch_paint(member=0.35, uid=hash01("v", i, side))
            S, E, _th = circle_section(34, VERT_OD * 0.5)
            E = E * 0.72
            idx, P, u, v, ww = prism_member(
                acc_for(y), pu + nu_ * 0.004, pd + nd * 0.004, S, E,
                MAT_PAINT, b, a, w, uid="vert%d_%d" % (i, side),
                up=(0, 1, 0), cut0=(pu, nu_), cut1=(pd, nd),
                bow=rnd(0.0006, 0.0020, "vb", i, side), res=res, rowbase=0.030,
                end_edge=0.62)
            cnt["members"] += 1
            ring_weld(acc_for(y), P[0], nu_, ww, MAT_PAINT, b, a, w,
                      uid="wv0%d%d" % (i, side))
            ring_weld(acc_for(y), P[-1], nd, -ww, MAT_PAINT, b, a, w,
                      uid="wv1%d%d" % (i, side))
            cnt["welds"] += 2
        # diagonals, offset 115 mm along the chord from the vertical so the
        # joint is a real gap K-joint and not two tubes fighting for the same
        # 200 mm of chord face
        for i in range(N_STA - 1):
            y0, y1 = BAYS[i]
            lean = _bay_pattern(i)
            if lean > 0:
                ya, la, yb, lb = y0 + 0.115, 0, y1 - 0.115, 1
            else:
                ya, la, yb, lb = y0 + 0.115, 1, y1 - 0.115, 0
            pa, na = chord_face(side, la, ya, "up" if la == 0 else "down")
            pb, nb = chord_face(side, lb, yb, "up" if lb == 0 else "down")
            b, a, w = ch_paint(member=0.5, uid=hash01("d", i, side))
            S, E, _th = circle_section(32, DIAG_OD * 0.5)
            E = E * 0.72
            ym = 0.5 * (ya + yb)
            idx, P, u, v, ww = prism_member(
                acc_for(ym), pa + na * 0.004, pb + nb * 0.004, S, E,
                MAT_PAINT, b, a, w, uid="diag%d_%d" % (i, side),
                up=(0, 1, 0), cut0=(pa, na), cut1=(pb, nb),
                bow=rnd(0.0008, 0.0026, "db", i, side), res=res, rowbase=0.030,
                end_edge=0.62)
            cnt["members"] += 1
            ring_weld(acc_for(ym), P[0], na, ww, MAT_PAINT, b, a, w,
                      uid="wd0%d%d" % (i, side))
            ring_weld(acc_for(ym), P[-1], nb, -ww, MAT_PAINT, b, a, w,
                      uid="wd1%d%d" % (i, side))
            cnt["welds"] += 2

    # ---- 3. the bottom face: ties, node gussets, plan X-bracing -----------
    for i, y in enumerate(STATIONS):
        pa, na = chord_face(-1, 0, y, "in")
        pb, nb = chord_face(+1, 0, y, "in")
        # THE TIE RIDES LOW IN THE CHORD.  On the chord axis a CHS 114 occupied
        # z 9.043-9.157, which is straight through the node gusset at 9.150 and
        # through the plan-bracing angle legs: three members sharing the same
        # 20 mm of depth at all 34 nodes.  A CHS 88.9 dropped 45 mm sits in
        # 9.010-9.100 - inside the chord, 10 mm clear of the soffit, and 18 mm
        # under the lowest bracing leg.
        pa = pa + np.array([0.0, 0.0, TIE_DZ])
        pb = pb + np.array([0.0, 0.0, TIE_DZ])
        b, a, w = ch_paint(member=0.62, uid=hash01("tie", i))
        S, E, _th = circle_section(32, TIE_OD * 0.5)
        E = E * 0.72
        idx, P, u, v, ww = prism_member(
            acc_for(y), pa + na * 0.004, pb + nb * 0.004, S, E,
            MAT_PAINT, b, a, w, uid="tie%d" % i, up=(0, 0, 1),
            cut0=(pa, na), cut1=(pb, nb),
            bow=rnd(0.0004, 0.0016, "tb", i), res=res, rowbase=0.030,
            end_edge=0.62)
        cnt["members"] += 1
        ring_weld(acc_for(y), P[0], na, ww, MAT_PAINT, b, a, w, uid="wt0%d" % i)
        ring_weld(acc_for(y), P[-1], nb, -ww, MAT_PAINT, b, a, w,
                  uid="wt1%d" % i)
        cnt["welds"] += 2

    gussets = {}
    for i, y in enumerate(STATIONS):
        for side in (-1, 1):
            sp = node_plate_spec(i, side)
            gussets[(i, side)] = build_node_gusset(acc_for(y), sp, mats, cnt,
                                                   res=res)
            node_shapes.add((sp["kind"], round(sp["reach"], 3),
                             round(sp["half_v"], 3), sp["nb"], sp["size"],
                             sp["stiff"], sp["lug"], sp["notch"] > 0))
            cnt["node_plates"] += 1

    build_plan_bracing(A, gussets, mats, cnt, bolt_shapes, res=res)

    # ---- 4. the top face: walkway bearers, plan bars, the edge angle ------
    for i, y in enumerate(STATIONS):
        pa, na = chord_face(-1, 1, y, "in")
        pb, nb = chord_face(+1, 1, y, "in")
        b, a, w = ch_paint(member=0.72, uid=hash01("br", i))
        zt = TOP_Z + float(camber(np.array([y]))[0])
        S, E = rrect_section(BEARER_W, BEARER_H, 0.012, nc=5, ns=6)
        # RHS 100 wide x 150 deep, top face flush with the walkway plane
        pa2 = pa.copy()
        pb2 = pb.copy()
        pa2[2] = pb2[2] = zt - BEARER_H * 0.5
        idx, P, u, v, ww = prism_member(
            acc_for(y), pa2 + na * 0.004, pb2 + nb * 0.004, S, E * 0.55,
            MAT_PAINT, b, a, w, uid="bearer%d" % i, up=(0, 0, 1),
            cut0=(pa, na), cut1=(pb, nb), bow=0.0006, res=res, rowbase=0.035)
        cnt["members"] += 1
        ring_weld(acc_for(y), P[0], na, ww, MAT_PAINT, b, a, w, uid="wb0%d" % i,
                  leg=0.006)
        ring_weld(acc_for(y), P[-1], nb, -ww, MAT_PAINT, b, a, w,
                  uid="wb1%d" % i, leg=0.006)
        cnt["welds"] += 2
        T.mounts["walkway_bearer_%d" % i] = Frame(
            (0.0, y, zt), (1, 0, 0), (0, 1, 0), (0, 0, 1), BEARER_W * 0.5,
            "walkway bearer top, y=%.4f" % y)

    for i in range(N_STA - 1):
        y0, y1 = BAYS[i]
        ym = 0.5 * (y0 + y1)
        zb = TOP_Z + float(camber(np.array([ym]))[0]) - BEARER_H - 0.006
        for k in (0, 1):
            xa = -CHORD_X if k == 0 else CHORD_X
            pa = np.array([xa * 0.86, y0, zb])
            pb = np.array([-xa * 0.86, y1, zb])
            b, a, w = ch_paint(member=0.80, uid=hash01("tp", i, k))
            S, E = rrect_section(TOPBAR_W, TOPBAR_T, 0.0018, nc=3, ns=3)
            prism_member(acc_for(ym), pa, pb, S, E * 0.9, MAT_PAINT, b, a, w,
                         uid="topbar%d_%d" % (i, k), up=(0, 0, 1), bow=0.0018,
                         res=res, rowbase=0.05)
            cnt["members"] += 1

    build_walkway_edge(A, T, mats, cnt, edge_shapes, bolt_shapes, res=res)

    # ---- 5. the field splices --------------------------------------------
    for si, ys in enumerate(SPLICE_Y):
        build_splice(A, T, si, float(ys), mats, cnt, bolt_shapes, res=res)

    # ---- 6. the bearings (THE gantry_leg interface) -----------------------
    for sgn, tag in ((-1.0, "S"), (+1.0, "N")):
        build_bearing(A, T, sgn, tag, mats, cnt, bolt_shapes, res=res)

    # ---- 7. end caps, fittings, and everything the dependants land on ----
    build_end_caps(A, T, mats, cnt, res=res)
    build_soffit_services(A, T, mats, cnt, bolt_shapes, res=res)
    build_fascia_brackets(A, T, mats, cnt, bolt_shapes, res=res)
    build_anchor_eyes(A, T, mats, cnt, res=res)

    # ---- emit -------------------------------------------------------------
    R, t = (place if place is not None else (None, None))
    lo = np.array([1e9, 1e9, 1e9])
    for k, acc in enumerate(A):
        if acc.n == 0:
            continue
        if R is not None:
            acc.xform(R, t)
        b0, b1 = acc.bounds()
        lo = np.minimum(lo, b0)
        ob = acc.emit(coll, mats, name=PFX + "Truss_" + SEG_NAMES[k])
        ob["gtr_soffit_z"] = SOFFIT_Z
        ob["gtr_segment"] = SEG_NAMES[k]
        T.objects.append(ob)
    if R is not None:
        for k, f in list(T.mounts.items()):
            T.mounts[k] = f.transformed(R, t)
    T.stats = cnt
    T.stats["lowest_z"] = float(lo[2])
    T.stats["distinct_node_plate_shapes"] = len(node_shapes)
    T.stats["distinct_bolt_geometries"] = len(bolt_shapes)
    T.stats["distinct_walkway_edge_bays"] = len(edge_shapes)
    T.stats["triangles"] = sum(
        len(o.data.polygons) + sum(max(len(p.vertices) - 3, 0)
                                   for p in o.data.polygons)
        for o in T.objects)
    T.stats["vertices"] = sum(len(o.data.vertices) for o in T.objects)
    if verbose:
        print(">> gantry truss: %d objects, %d verts, %d tris"
              % (len(T.objects), T.stats["vertices"], T.stats["triangles"]))
        for k in sorted(cnt):
            print("   %-28s %s" % (k, cnt[k]))
    return T


# --------------------------------------------------------------------------- #
# 12.  CONNECTIONS                                                              #
# --------------------------------------------------------------------------- #

GUSSET_DZ = GUSSET_Z0 - BOT_AXIS_Z        # gusset underside above the chord axis
CROSS_PACK_T = 0.020                      # == GUSSET_T; see build_plan_bracing
PLAN_BOLT_OFF = 0.000                     # a flat bar is bolted on its centreline


def p3(o, eu, ev, uv, off=0.0, en=None):
    """2D plate coordinates -> 3D."""
    uv = np.asarray(uv, float).reshape(-1, 2)
    P = (_n3(o)[None, :] + uv[:, 0:1] * _n3(eu)[None, :]
         + uv[:, 1:2] * _n3(ev)[None, :])
    if en is not None and off:
        P = P + _n3(en)[None, :] * off
    return P


def cell_centres(G):
    G = np.asarray(G, float)
    return 0.25 * (G[:-1, :-1] + G[:-1, 1:] + G[1:, 1:] + G[1:, :-1])


def snap_holes(G, pts, r):
    """Put a hole in the CELL nearest each requested point; no cell twice.

    Returns [(i, j, r)] and the ACTUAL 2D centres, so the bolt goes exactly
    where the hole is instead of 8 mm beside it.
    """
    cc = cell_centres(G)
    used, holes, ctrs = set(), [], []
    for p in pts:
        d = np.linalg.norm(cc - np.asarray(p, float)[None, None, :], axis=-1)
        for f in np.argsort(d.ravel()):
            i, j = np.unravel_index(f, d.shape)
            if (int(i), int(j)) in used:
                continue
            used.add((int(i), int(j)))
            holes.append((int(i), int(j), r))
            ctrs.append(cc[i, j].copy())
            break
    return holes, (np.array(ctrs) if ctrs else np.zeros((0, 2)))


def plate_edge_weld(acc, o, eu, ev, en, edge_uv, t, face_n, mat, base, aux,
                    wear, uid, leg=0.007, step=0.006):
    """Two fillet seams where a plate is welded EDGE-ON to a face."""
    E = np.asarray(edge_uv, float)
    for sgn in (+1.0, -1.0):
        A = p3(o, eu, ev, E, off=sgn * (t * 0.5 + leg), en=en)
        B = p3(o, eu, ev, E + np.array([leg * 1.2, 0.0])[None, :],
               off=sgn * t * 0.5, en=en)
        seam_weld(acc, A, B, np.asarray(face_n, float),
                  _n3(en) * sgn, mat, base, aux, wear,
                  uid=uid + str(sgn), step=step, bulge=leg * 0.30)


def build_node_gusset(acc, sp, mats, cnt, res=1.0):
    """The horizontal gusset at a bottom node, and everything welded to it.

    THIS IS THE OBJECT THE MANIFEST IS TALKING ABOUT.  It hangs inside the
    bottom bay, 150 mm above the soffit, and the lens looks straight up at its
    underside and at the nuts on it from 3 m.  No two of the 34 are the same
    plate: the kind, reach, taper, corner clips, re-entrant notch, rat hole,
    bolt count, bolt gauge, bolt size and bolt handedness all come off the
    node's own hash.
    """
    y, side = sp["y"], sp["side"]
    pf, nf = chord_face(side, 0, y, "in")            # inner face, outward normal
    zmid = pf[2] + GUSSET_DZ + GUSSET_T * 0.5
    o = np.array([pf[0], pf[1], zmid])
    eu = unit(np.array([nf[0], 0.0, 0.0]))           # inboard
    ev = np.array([0.0, 1.0, 0.0])
    en = np.array([0.0, 0.0, 1.0])

    # the two brace lines through this node, in plate coordinates
    dirs = []
    if sp["sta"] < N_STA - 1:
        dirs.append(unit(np.array([2.0 * (CHORD_X - CHORD_W * 0.5),
                                   STATIONS[sp["sta"] + 1] - y])))
    if sp["sta"] > 0:
        dirs.append(unit(np.array([2.0 * (CHORD_X - CHORD_W * 0.5),
                                   STATIONS[sp["sta"] - 1] - y])))
    bolt_uv, bolt_dirs = [], []
    first = 0.085
    for bd in dirs:
        for k in range(sp["nb"]):
            bolt_uv.append(bd * (first + k * sp["pitch"]))
            bolt_dirs.append(bd)
    bolt_uv = np.array(bolt_uv) if bolt_uv else np.zeros((0, 2))

    need_u = float(np.max(bolt_uv[:, 0])) + 0.045 if len(bolt_uv) else 0.20
    need_v = float(np.max(np.abs(bolt_uv[:, 1]))) + 0.045 if len(bolt_uv) else 0.15
    reach = max(sp["reach"], need_u)
    half_v = max(sp["half_v"], need_v)
    nu = max(6, int(round(reach / 0.052)))
    nv = max(8, int(round(2.0 * half_v / 0.052)))
    G = rect_grid(reach * 0.5, half_v, nu, nv, taper=0.0,
                  notch=sp["notch"], clip=sp["clip"])
    G[..., 0] += reach * 0.5                          # u = 0 at the chord face
    # the rat hole: the plate is cut back where the chord's own corner weld runs
    G[0, :, 1] += sp["rat"] * 0.55
    G[-1, :, 1] -= sp["rat"] * 0.55
    G[:, 0, 0] += sp["rat"] * 0.30

    b, a, w = ch_paint(member=0.28, uid=hash01(sp["uid"]))
    hr = BOLTS[sp["size"]][5] + HOLE_CLEAR
    holes, ctrs = snap_holes(G, bolt_uv, hr)
    if sp["drain"]:
        h2, c2 = snap_holes(G, [np.array([reach * 0.80, half_v * 0.62])], 0.008)
        holes += h2
    grid_plate(acc, o, eu, ev, en, G, GUSSET_T, holes, MAT_PAINT, b, a, w,
               uid=hash01(sp["uid"], "gp"), chamfer=0.0015, face_edge=0.10)
    cnt["plates"] += 1
    # welded edge-on to the chord: two 7 mm fillets down its whole near edge
    edge = np.stack([np.zeros(nv + 1), G[:, 0, 1]], -1)
    plate_edge_weld(acc, o, eu, ev, en, edge, GUSSET_T, nf, MAT_PAINT, b, a, w,
                    uid=sp["uid"] + "ew")
    cnt["welds"] += 2
    # a stiffener rib on top of the plate, on some nodes
    if sp["stiff"]:
        pa = p3(o, eu, ev, [[0.030, 0.0]], off=GUSSET_T * 0.5, en=en)[0]
        pb = p3(o, eu, ev, [[reach * 0.78, 0.0]], off=GUSSET_T * 0.5, en=en)[0]
        S, E = rrect_section(0.010, 0.060, 0.0015, nc=3, ns=3)
        prism_member(acc, pa + en * 0.030, pb + en * 0.030, S, E * 0.9,
                     MAT_PAINT, b, a, w, uid=sp["uid"] + "rib", up=(0, 0, 1),
                     bow=0.0004, res=res, rowbase=0.03)
        cnt["members"] += 1
    if sp["lug"]:
        # an erection lug: 16 mm plate standing on the gusset with a 26 mm hole
        lo = p3(o, eu, ev, [[reach * 0.62, half_v * 0.70]],
                off=GUSSET_T * 0.5, en=en)[0]
        Gl = rect_grid(0.055, 0.048, 4, 4, taper=0.35)
        hl, _ = snap_holes(Gl, [np.array([0.0, 0.010])], 0.013)
        grid_plate(acc, lo + en * 0.048, ev, en, eu, Gl, 0.016, hl,
                   MAT_MACHINED, *ch_mach(member=0.4, uid=hash01(sp["uid"], "lug")),
                   uid=hash01(sp["uid"], "lg"), chamfer=0.0018)
        cnt["plates"] += 1
    return dict(sp=sp, o=o, eu=eu, ev=ev, en=en, reach=reach, half_v=half_v,
                ctrs=ctrs, dirs=bolt_dirs, zmid=zmid, side=side, y=y,
                b=b, a=a, w=w)


def build_plan_bracing(A, gussets, mats, cnt, bolt_shapes, res=1.0):
    """Flat 150 x 12 cross bracing in the bottom plane, bolted at every end.

    THE TWO BRACES LAP OPPOSITE FACES OF THE SAME GUSSET.  Brace A goes under
    it, brace B on top of it, so the 20 mm plate that connects them is also
    exactly the packing that separates them, and the same 20 mm gap reappears
    at the crossing where a loose pack fills it.  No node packs, no member
    sharing a millimetre of depth with any other member, and a bolt cluster at
    the centre of every bay as well as at every node - sixteen more clusters
    directly over the racing line.

    The z schedule, which every dependant can rely on (add camber(y)):
        transverse tie CHS 88.9   9.0106 .. 9.0994
        brace A (under gusset)    9.1380 .. 9.1500
        gusset / crossing pack    9.1500 .. 9.1700
        brace B (over gusset)     9.1700 .. 9.1820
    """
    S, E = rrect_section(PLAN_W, PLAN_T, 0.0018, nc=3, ns=6)
    for i in range(N_STA - 1):
        y0, y1 = BAYS[i]
        ym = 0.5 * (y0 + y1)
        acc = A[segment_of(ym)]
        for lvl, (sA, sB) in enumerate(((-1, +1), (+1, -1))):
            g0 = gussets[(i, sA)]
            g1 = gussets[(i + 1, sB)]
            # lvl 0 laps the gusset's UNDERSIDE, lvl 1 its TOP.
            zax = (g0["zmid"] - GUSSET_T * 0.5 - PLAN_T * 0.5 if lvl == 0
                   else g0["zmid"] + GUSSET_T * 0.5 + PLAN_T * 0.5)
            d3 = unit(np.array([g1["o"][0] - g0["o"][0], y1 - y0, 0.0]))
            pa = np.array([g0["o"][0], y0, zax]) + d3 * 0.045
            pb = np.array([g1["o"][0], y1, zax]) - d3 * 0.045
            # a flat bar is bolted on its own centreline: the setting-out line
            # IS the member axis
            perp = unit(np.cross(np.array([0.0, 0.0, 1.0]), d3))
            off = perp * PLAN_BOLT_OFF
            b, a, w = ch_paint(member=0.44 + 0.06 * lvl,
                               uid=hash01("plan", i, lvl))
            idx, P, u_, v_, w_ = prism_member(
                acc, pa + off, pb + off, S, E * 0.95, MAT_PAINT, b, a, w,
                uid="plan%d_%d" % (i, lvl), up=tuple(perp), bow=0.0022,
                res=res, rowbase=0.030)
            cnt["members"] += 1
            # bolts at both ends
            for g, sgn in ((g0, +1.0), (g1, -1.0)):
                grip = GUSSET_T + PLAN_T
                # head on the topmost face of the pack: the gusset top for the
                # brace that laps underneath, the brace's own top for the one
                # that laps over.  Either way the NUT hangs underneath, which
                # is what the lens sees.
                head_off = GUSSET_T * 0.5 + (PLAN_T if lvl else 0.0)
                # WHICH BOLTS ARE THIS BRACE'S.  A gusset carries two brace
                # ends and each has its own bolt line, so the wanted direction
                # has to be expressed in THAT GUSSET'S OWN plate frame - whose
                # +u is inboard, and therefore points the opposite way in
                # world x on the two sides of the truss.  Comparing against a
                # world vector picked the wrong half of the cluster on every
                # +x node, which put both braces' bolts through one brace.
                dirw = d3 * sgn
                want = unit(np.array([float(np.dot(dirw, g["eu"])),
                                      float(np.dot(dirw, g["ev"]))]))
                pts = []
                for k, c in enumerate(g["ctrs"]):
                    if float(np.dot(unit(g["dirs"][k]), want)) < 0.5:
                        continue
                    pts.append(p3(g["o"], g["eu"], g["ev"], [c],
                                  off=head_off, en=g["en"])[0])
                for k, p in enumerate(pts):
                    spec = bolt_spec("pb%d_%d_%d_%d" % (i, lvl, int(sgn), k),
                                     size=g["sp"]["size"], grip=grip)
                    bolt(acc, p, np.array([0.0, 0.0, -1.0]), spec, MAT_FASTENER,
                         *ch_fast(member=0.9, uid=hash01(spec["uid"])))
                    cnt["bolts"] += 1
                    bolt_shapes.add((spec["size"], spec["kind"],
                                     round(spec["tail"], 4), spec["head_down"],
                                     round(spec["grip"], 4)))
        # ---- the crossing ------------------------------------------------
        gA0, gA1 = gussets[(i, -1)], gussets[(i + 1, +1)]
        cx = 0.5 * (gA0["o"][0] + gA1["o"][0])
        # the crossing pack IS the gusset's own 20 mm plate, at the gusset's
        # own level: brace A passes under it and brace B over it, exactly as
        # they do at the nodes.
        ctr = np.array([cx, ym, gA0["zmid"]])
        b, a, w = ch_paint(member=0.50, uid=hash01("xp", i))
        Gc = rect_grid(0.115, 0.098, 4, 4, clip=0.024)
        pts2 = [np.array([0.0, +0.048]), np.array([0.0, -0.048])]
        hc, cc2 = snap_holes(Gc, pts2, BOLTS["M20"][5] + HOLE_CLEAR)
        grid_plate(acc, ctr, np.array([1.0, 0, 0]), np.array([0, 1.0, 0]),
                   np.array([0, 0, 1.0]), Gc, CROSS_PACK_T, hc, MAT_PAINT,
                   b, a, w, uid=hash01("xpl", i), chamfer=0.0018)
        cnt["plates"] += 1
        for k, c in enumerate(cc2):
            p = np.array([ctr[0] + c[0], ctr[1] + c[1],
                          gA0["zmid"] + GUSSET_T * 0.5 + PLAN_T + 0.0002])
            spec = bolt_spec("xb%d_%d" % (i, k), size="M20",
                             grip=PLAN_T + CROSS_PACK_T + PLAN_T)
            bolt(acc, p, np.array([0.0, 0.0, -1.0]), spec, MAT_FASTENER,
                 *ch_fast(member=0.92, uid=hash01(spec["uid"])))
            cnt["bolts"] += 1
            bolt_shapes.add((spec["size"], spec["kind"], round(spec["tail"], 4),
                             spec["head_down"], round(spec["grip"], 4)))


def build_walkway_edge(A, T, mats, cnt, edge_shapes, bolt_shapes, res=1.0):
    """L100x75x8 capping angle along the outer top arris of each top chord.

    gantry_walkway lands its grating and its handrail on this.  Every bay's
    piece of it grew something different: a bolted splice cover, a stanchion
    base plate, a scupper drain pipe, a fascia cleat or a lifting lug.
    """
    S, E = angle_section(0.075, 0.100, EDGE_T, nc=5, ns=7)
    for side in (-1, 1):
        for seg, (ya, yb) in enumerate(
                [(-END_Y, SPLICE_Y[0]), (SPLICE_Y[0], SPLICE_Y[1]),
                 (SPLICE_Y[1], END_Y)]):
            acc = A[seg]
            ys = np.arange(ya, yb + 0.05, 0.05)
            ys = np.unique(np.clip(np.concatenate([ys, [ya, yb]]), ya, yb))
            if side < 0:
                ys = ys[::-1]
            M = len(ys)
            zt = TOP_Z + camber(ys) + 0.040
            xf = np.array([chord_face(side, 1, float(y), "out")[0][0]
                           for y in ys])
            u = np.array([float(side), 0.0, 0.0])
            v = np.array([0.0, 0.0, -1.0])
            Cp = np.stack([xf + side * 0.0375, ys, zt], -1)
            b, a, w = ch_paint(member=0.86, uid=hash01("edge", side, seg))
            a4 = np.tile(np.asarray(a, float).reshape(1, 1, 4),
                         (M, len(S), 1)).copy()
            a4[..., 0] = np.asarray(E, float)[None, :] * 0.9
            IDX = sweep(acc, Cp, np.tile(u, (M, 1)), np.tile(v, (M, 1)),
                        np.broadcast_to(S[None], (M, len(S), 2)),
                        MAT_PAINT, b, a4, w, smooth=False)
            P = (Cp[:, None, :] + S[None, :, 0:1] * u[None, None, :]
                 + S[None, :, 1:2] * v[None, None, :])
            for (row, flip) in ((0, True), (M - 1, False)):
                ic = acc.verts(P[row].mean(0).reshape(1, 3), uv=np.zeros((1, 2)),
                               base=b, aux=np.asarray(a, float).reshape(1, 4),
                               wear=w)
                acc.fan(IDX[row], ic, MAT_PAINT, smooth=False, flip=flip)
            cnt["members"] += 1
            # welded to the chord's outer face along its whole length
            zw = TOP_Z + camber(ys) - 0.010
            Aw = np.stack([xf, ys, zw - 0.007], -1)
            Bw = np.stack([xf + side * 0.007, ys, zw], -1)
            seam_weld(acc, Aw, Bw, np.array([float(side), 0, 0]),
                      np.array([0, 0, -1.0]), MAT_PAINT, b, a, w,
                      uid="ew%d%d" % (side, seg), step=0.006)
            cnt["welds"] += 1

        for i in range(N_STA - 1):
            spec = walkway_edge_spec(i, side)
            edge_shapes.add((spec["kind"], side))
            build_edge_feature(A[segment_of(spec["at"])], T, spec, side, cnt,
                               bolt_shapes, res=res)
        T.mounts["walkway_edge_%s" % ("e" if side > 0 else "w")] = Frame(
            (side * (CHORD_X + CHORD_W * 0.5), 0.0, TOP_Z + CAMBER),
            (float(side), 0, 0), (0, 1, 0), (0, 0, 1), 0.075,
            "walkway edge angle L100x75x8, heel outboard")


def build_edge_feature(acc, T, spec, side, cnt, bolt_shapes, res=1.0):
    y = float(spec["at"])
    kind = spec["kind"]
    zt = TOP_Z + float(camber(np.array([y]))[0])
    xo = float(chord_face(side, 1, y, "out")[0][0])
    b, a, w = ch_paint(member=0.88, uid=hash01(spec["uid"]))
    ex = np.array([float(side), 0.0, 0.0])
    ey = np.array([0.0, 1.0, 0.0])
    ez = np.array([0.0, 0.0, 1.0])
    if kind == "splice_cover":
        o = np.array([xo + side * 0.006, y, zt + 0.040])
        G = rect_grid(0.115, 0.038, 5, 3)
        pts = [np.array([-0.075, -0.020]), np.array([-0.075, 0.020]),
               np.array([0.075, -0.020]), np.array([0.075, 0.020])]
        h, c = snap_holes(G, pts, BOLTS["M16"][5] + HOLE_CLEAR)
        grid_plate(acc, o, ey, ez, ex, G, 0.010, h, MAT_PAINT, b, a, w,
                   uid=hash01(spec["uid"], "sc"), chamfer=0.0016)
        cnt["plates"] += 1
        for k, cc in enumerate(c):
            p = o + ey * cc[0] + ez * cc[1] + ex * 0.005
            sp = bolt_spec(spec["uid"] + "b%d" % k, size="M16", grip=0.018)
            bolt(acc, p, -ex, sp, MAT_FASTENER,
                 *ch_fast(member=0.93, uid=hash01(sp["uid"])), ref=(0, 0, 1))
            cnt["bolts"] += 1
            bolt_shapes.add((sp["size"], sp["kind"], round(sp["tail"], 4),
                             sp["head_down"], round(sp["grip"], 4)))
    elif kind == "stanchion":
        o = np.array([xo + side * 0.052, y, zt + 0.096])
        G = rect_grid(0.062, 0.062, 4, 4, clip=0.016)
        pts = [np.array([-0.045, -0.045]), np.array([0.045, -0.045]),
               np.array([-0.045, 0.045]), np.array([0.045, 0.045])]
        h, c = snap_holes(G, pts, BOLTS["M12"][5] + HOLE_CLEAR)
        grid_plate(acc, o, ex, ey, ez, G, 0.012, h, MAT_GALV,
                   *ch_galv(member=0.5, uid=hash01(spec["uid"])),
                   uid=hash01(spec["uid"], "sb"), chamfer=0.0016)
        cnt["plates"] += 1
        for k, cc in enumerate(c):
            p = o + ex * cc[0] + ey * cc[1] + ez * 0.006
            sp = bolt_spec(spec["uid"] + "s%d" % k, size="M12", grip=0.020)
            bolt(acc, p, -ez, sp, MAT_FASTENER,
                 *ch_fast(member=0.94, uid=hash01(sp["uid"])))
            cnt["bolts"] += 1
            bolt_shapes.add((sp["size"], sp["kind"], round(sp["tail"], 4),
                             sp["head_down"], round(sp["grip"], 4)))
        T.mounts["stanchion_base_%d_%s" % (spec["bay"],
                                           "e" if side > 0 else "w")] = Frame(
            o + ez * 0.006, ex, ey, ez, 0.062, "handrail stanchion base plate")
    elif kind == "weep_pipe":
        o = np.array([xo + side * 0.050, y, zt + 0.086])
        S, E, _th = circle_section(20, 0.011)
        prism_member(acc, o, o - ez * 0.075, S, E * 0.4, MAT_GALV,
                     *ch_galv(member=0.55, uid=hash01(spec["uid"])),
                     uid=spec["uid"] + "wp", up=(0, 1, 0), bow=0.0002,
                     res=res, rowbase=0.02)
        cnt["members"] += 1
        ring_weld(acc, np.array([o + (ex * math.cos(t) + ey * math.sin(t))
                                 * 0.011 for t in np.linspace(0, TAU, 40,
                                                              endpoint=False)]),
                  ez, -ez, MAT_GALV,
                  *ch_galv(member=0.55, uid=hash01(spec["uid"])),
                  uid=spec["uid"] + "ww", leg=0.005)
        cnt["welds"] += 1
    elif kind == "cleat":
        o = np.array([xo + side * 0.014, y, zt + 0.030])
        G = rect_grid(0.050, 0.038, 3, 3, taper=0.30)
        grid_plate(acc, o, ey, ez, ex, G, 0.010, [], MAT_PAINT, b, a, w,
                   uid=hash01(spec["uid"], "cl"), chamfer=0.0016)
        cnt["plates"] += 1
    else:                                    # lifting lug or plain
        if kind == "lifting_lug":
            o = np.array([xo + side * 0.030, y, zt + 0.140])
            G = rect_grid(0.055, 0.050, 4, 4, taper=0.30)
            h, _ = snap_holes(G, [np.array([0.0, 0.014])], 0.014)
            grid_plate(acc, o, ey, ez, ex, G, 0.016, h, MAT_MACHINED,
                       *ch_mach(member=0.45, uid=hash01(spec["uid"])),
                       uid=hash01(spec["uid"], "ll"), chamfer=0.002)
            cnt["plates"] += 1


def build_splice(A, T, si, ys, mats, cnt, bolt_shapes, res=1.0):
    """The bolted end-plate field splice: 4 chords x 8 M24, twice.

    A 23.2 m truss is delivered in three pieces and bolted together on site.
    Getting that wrong - one continuous extrusion - is what makes CG steelwork
    look extruded.  Here the two plates are 0.6 mm apart (0.75 screen px of
    dark joint line), the packing shims that took up the fit-up error are
    still in the joint, and every bolt in the ring has its own thread
    protrusion.
    """
    gap = SPLICE_GAP * 0.5
    for level in (0, 1):
        for side in (-1, 1):
            pw, ex, ez = chord_frame(side, level, ys)
            ey = np.array([0.0, 1.0, 0.0])
            hw = 0.170
            G = rect_grid(hw, hw, 6, 6, clip=0.030)
            want = [np.array([sx * 0.135, sz * 0.062]) for sx in (-1, 1)
                    for sz in (-1, 1)]
            want += [np.array([sx * 0.062, sz * 0.135]) for sx in (-1, 1)
                     for sz in (-1, 1)]
            hr = BOLTS["M24"][5] + HOLE_CLEAR
            holes, ctrs = snap_holes(G, want, hr)
            b, a, w = ch_paint(member=0.20, uid=hash01("spl", si, level, side))
            for (sgn, seg) in ((-1.0, 0 if si == 0 else 1),
                               (+1.0, 1 if si == 0 else 2)):
                o = pw + ey * (sgn * (gap + SPLICE_T * 0.5))
                acc = A[seg]
                grid_plate(acc, o, ex, ez, ey, G, SPLICE_T, holes, MAT_PAINT,
                           b, a, w, uid=hash01("sp", si, level, side, sgn),
                           chamfer=0.0022, face_edge=0.12)
                cnt["plates"] += 1
                # the plate is welded all round the chord it caps
                ring = np.array([pw + ex * (math.cos(t) * 0.100)
                                 + ez * (math.sin(t) * 0.100)
                                 + ey * (sgn * (gap + SPLICE_T))
                                 for t in np.linspace(0, TAU, 96,
                                                      endpoint=False)])
                ring_weld(acc, ring, ey * sgn, ey * sgn, MAT_PAINT, b, a, w,
                          uid="sw%d%d%d%.0f" % (si, level, side, sgn), leg=0.008)
                cnt["welds"] += 1
                # two stiffener ribs per plate
                for kz in (-1, 1):
                    pa = pw + ez * (kz * 0.100) + ey * (sgn * (gap + SPLICE_T))
                    S2, E2 = rrect_section(0.140, 0.012, 0.002, nc=3, ns=4)
                    prism_member(acc, pa, pa + ey * (sgn * 0.115), S2, E2 * 0.9,
                                 MAT_PAINT, b, a, w,
                                 uid="srib%d%d%d%d%.0f" % (si, level, side, kz, sgn),
                                 up=(0, 0, 1), bow=0.0002, res=res, rowbase=0.03)
                    cnt["members"] += 1
            # the shim pack: fit-up is never perfect and the shims stay in
            if chance(0.55, "shim", si, level, side):
                nsh = rint(1, 3, "shimn", si, level, side)
                for k in range(nsh):
                    t = 0.0008 + 0.0004 * k
                    Gs = rect_grid(0.150, 0.062, 3, 2)
                    o = pw + ey * (-gap - 0.0002 - t * 0.5) \
                        + ez * (0.090 * (1 if k % 2 else -1))
                    grid_plate(A[1], o, ex, ez, ey, Gs, t, [], MAT_MACHINED,
                               *ch_mach(member=0.3, uid=hash01("shim", si, k)),
                               uid=hash01("shm", si, level, side, k),
                               chamfer=0.0004, wave=0.0002)
                    cnt["plates"] += 1
            # the bolts, through both plates
            grip = 2.0 * SPLICE_T + SPLICE_GAP
            for k, c in enumerate(ctrs):
                p = pw + ex * c[0] + ez * c[1] - ey * (gap + SPLICE_T)
                sp = bolt_spec("sb%d_%d_%d_%d" % (si, level, side, k),
                               size="M24", grip=grip)
                bolt(A[1], p, ey, sp, MAT_FASTENER,
                     *ch_fast(member=0.96, uid=hash01(sp["uid"])), ref=(0, 0, 1))
                cnt["bolts"] += 1
                bolt_shapes.add((sp["size"], sp["kind"], round(sp["tail"], 4),
                                 sp["head_down"], round(sp["grip"], 4)))
    T.mounts["splice_%s" % ("w" if si == 0 else "e")] = Frame(
        (0.0, float(ys), BOT_AXIS_Z), (1, 0, 0), (0, 1, 0), (0, 0, 1), 1.1,
        "field splice joint plane")


def build_bearing(A, T, sgn, tag, mats, cnt, bolt_shapes, res=1.0):
    """THE gantry_leg INTERFACE: what the leg head has to meet.

    A 30 mm bearing plate welded under each bottom chord with four ribs, a
    25 mm elastomeric pad under it, and four M30 holding-down bolts in 36 x
    46 mm SLOTTED holes - which is where the +-5 mm of setting-out tolerance
    between a fabricated truss and a fabricated leg actually goes.
    """
    y = sgn * BEARING_Y
    acc = A[segment_of(y)]
    for side in (-1, 1):
        pd, nd = chord_face(side, 0, y, "down")
        ex = np.array([1.0, 0.0, 0.0])
        ey = np.array([0.0, 1.0, 0.0])
        ez = np.array([0.0, 0.0, 1.0])
        o = pd - ez * 0.015
        G = rect_grid(0.210, 0.180, 6, 6, clip=0.026)
        want = [np.array([sx * 0.150, sy * 0.120]) for sx in (-1, 1)
                for sy in (-1, 1)]
        holes, ctrs = snap_holes(G, want, (0.018, 0.023))
        b, a, w = ch_mach(member=0.15, uid=hash01("bear", tag, side))
        grid_plate(acc, o, ex, ey, ez, G, 0.030, holes, MAT_MACHINED, b, a, w,
                   uid=hash01("bp", tag, side), chamfer=0.0025, face_edge=0.14)
        cnt["plates"] += 1
        bp, ba, bw = ch_paint(member=0.16, uid=hash01("bearw", tag, side))
        ring = np.array([pd + ex * (math.cos(t) * 0.100)
                         + ey * (math.sin(t) * 0.100)
                         for t in np.linspace(0, TAU, 96, endpoint=False)])
        ring_weld(acc, ring, -ez, ez, MAT_PAINT, bp, ba, bw,
                  uid="bw%s%d" % (tag, side), leg=0.009)
        cnt["welds"] += 1
        for k, sx in enumerate((-1, 1)):
            pa = pd + ex * (sx * 0.100)
            S2, E2 = rrect_section(0.012, 0.150, 0.002, nc=3, ns=4)
            prism_member(acc, pa, pa - ez * 0.014, S2, E2 * 0.9, MAT_PAINT,
                         bp, ba, bw, uid="brib%s%d%d" % (tag, side, k),
                         up=(0, 1, 0), bow=0.0, res=res, rowbase=0.03)
            cnt["members"] += 1
        # the elastomeric pad
        Gp = rect_grid(0.150, 0.120, 4, 4)
        grid_plate(acc, o - ez * (0.015 + 0.0125), ex, ey, ez, Gp, 0.025, [],
                   MAT_ELASTO, (0.018, 0.018, 0.019, 0.5), (0.4, 0.0, 0.0, 0.3),
                   (0.0, 0.5, 0.0, 0.7), uid=hash01("pad", tag, side),
                   chamfer=0.0028, wave=0.0009)
        cnt["plates"] += 1
        for k, c in enumerate(ctrs):
            p = o + ex * c[0] + ey * c[1] + ez * 0.015
            sp = bolt_spec("hd%s_%d_%d" % (tag, side, k), size="M30",
                           grip=0.030, flip=False)
            sp["tail"] = rnd(0.018, 0.040, "hdt", tag, side, k)
            bolt(acc, p, -ez, sp, MAT_FASTENER,
                 *ch_fast(member=0.98, uid=hash01(sp["uid"])))
            cnt["bolts"] += 1
            bolt_shapes.add((sp["size"], sp["kind"], round(sp["tail"], 4),
                             sp["head_down"], round(sp["grip"], 4)))
            T.mounts["leg_head_%s_%s_bolt%d" % (
                tag, "e" if side > 0 else "w", k)] = Frame(
                p - ez * 0.045, ex, ey, -ez, 0.019,
                "M30 holding-down bolt, 36 x 46 slotted hole")
        T.mounts["leg_head_%s_%s" % (tag, "e" if side > 0 else "w")] = Frame(
            o - ez * 0.015, ex, ey, -ez, 0.276,
            "bearing plate underside, 420 x 360 x 30, +25 mm elastomer pad")
    T.mounts["leg_head_%s" % tag] = Frame(
        (0.0, y, SOFFIT_Z - 0.030), (1, 0, 0), (0, 1, 0), (0, 0, -1),
        CHORD_X + 0.21, "leg bearing line, both chords")


def build_end_caps(A, T, mats, cnt, res=1.0):
    """Cap plates on the eight chord ends, with drain notches and rigging holes."""
    for sgn in (-1.0, 1.0):
        y = sgn * END_Y
        acc = A[segment_of(y)]
        for level in (0, 1):
            for side in (-1, 1):
                pw, ex, ez = chord_frame(side, level, y)
                ey = np.array([0.0, 1.0, 0.0])
                G = rect_grid(0.130, 0.130, 4, 4, clip=0.028)
                pts = [np.array([0.0, -0.088])]
                if level == 1:
                    pts.append(np.array([0.0, 0.070]))
                h, c = snap_holes(G, pts, 0.011)
                b, a, w = ch_paint(member=0.24,
                                   uid=hash01("cap", sgn, level, side))
                grid_plate(acc, pw + ey * (sgn * (ENDCAP_T * 0.5)), ex, ez, ey,
                           G, ENDCAP_T, h, MAT_PAINT, b, a, w,
                           uid=hash01("ec", sgn, level, side), chamfer=0.002)
                cnt["plates"] += 1
                ring = np.array([pw + ex * (math.cos(t) * 0.100)
                                 + ez * (math.sin(t) * 0.100)
                                 + ey * (sgn * ENDCAP_T)
                                 for t in np.linspace(0, TAU, 84,
                                                      endpoint=False)])
                ring_weld(acc, ring, ey * sgn, ey * sgn, MAT_PAINT, b, a, w,
                          uid="cw%.0f%d%d" % (sgn, level, side), leg=0.007)
                cnt["welds"] += 1


def build_soffit_services(A, T, mats, cnt, bolt_shapes, res=1.0):
    """Everything gantry_soffit_panel, gantry_tv_pod and the signals bolt to."""
    # --- the continuous C-channel, opening DOWN ---------------------------
    w2, h2, t2, gp = CHAN_W, CHAN_H, CHAN_T, 0.016
    lip = 0.007
    pts = [(gp * 0.5, -h2 * 0.5), (w2 * 0.5, -h2 * 0.5), (w2 * 0.5, h2 * 0.5),
           (-w2 * 0.5, h2 * 0.5), (-w2 * 0.5, -h2 * 0.5), (-gp * 0.5, -h2 * 0.5),
           (-gp * 0.5, -h2 * 0.5 + lip), (-w2 * 0.5 + t2, -h2 * 0.5 + lip),
           (-w2 * 0.5 + t2, h2 * 0.5 - t2), (w2 * 0.5 - t2, h2 * 0.5 - t2),
           (w2 * 0.5 - t2, -h2 * 0.5 + lip), (gp * 0.5, -h2 * 0.5 + lip)]
    dense = []
    for k in range(len(pts)):
        a0 = np.array(pts[k], float)
        a1 = np.array(pts[(k + 1) % len(pts)], float)
        n = max(1, int(round(np.linalg.norm(a1 - a0) / 0.0035)))
        f = np.linspace(0.0, 1.0, n + 1)[:-1]
        dense.append(a0[None, :] + (a1 - a0)[None, :] * f[:, None])
    Sc = np.concatenate(dense, 0)
    Ec = np.clip(np.abs(np.gradient(section_outward(Sc), axis=0)).sum(1) * 8.0,
                 0.10, 1.0)
    for side in (-1, 1):
        for seg, (ya, yb) in enumerate(
                [(-END_Y, SPLICE_Y[0] - 0.030), (SPLICE_Y[0] + 0.030,
                                                 SPLICE_Y[1] - 0.030),
                 (SPLICE_Y[1] + 0.030, END_Y)]):
            acc = A[seg]
            ys = np.arange(ya, yb + 0.06, 0.06)
            ys = np.unique(np.clip(np.concatenate([ys, [ya, yb]]), ya, yb))
            M = len(ys)
            zc = SOFFIT_Z + camber(ys) - h2 * 0.5
            xs = np.array([chord_at(side, 0, float(v))[0] for v in ys])
            # cross(U, V) must equal the sweep direction (+y); the C section is
            # symmetric in x, so negating U costs nothing and keeps +V = up,
            # which is what puts the 16 mm slot on the DOWN side.
            u = np.array([-1.0, 0.0, 0.0])
            v3 = np.array([0.0, 0.0, 1.0])
            Cp = np.stack([xs, ys, zc], -1)
            b, a, w = ch_galv(member=0.66, uid=hash01("chan", side, seg))
            a4 = np.tile(np.asarray(a, float).reshape(1, 1, 4),
                         (M, len(Sc), 1)).copy()
            a4[..., 0] = Ec[None, :]
            IDX = sweep(acc, Cp, np.tile(u, (M, 1)), np.tile(v3, (M, 1)),
                        np.broadcast_to(Sc[None], (M, len(Sc), 2)),
                        MAT_GALV, b, a4, w, smooth=False)
            P = (Cp[:, None, :] + Sc[None, :, 0:1] * u[None, None, :]
                 + Sc[None, :, 1:2] * v3[None, None, :])
            for (row, flip) in ((0, True), (M - 1, False)):
                ic = acc.verts(P[row].mean(0).reshape(1, 3), uv=np.zeros((1, 2)),
                               base=b, aux=np.asarray(a, float).reshape(1, 4),
                               wear=w)
                acc.fan(IDX[row], ic, MAT_GALV, smooth=False, flip=flip)
            cnt["members"] += 1
            # stitch welds, 60 mm every 400 mm, both sides
            for yv in np.arange(ya + 0.20, yb - 0.10, CHAN_PITCH):
                xv = float(chord_at(side, 0, float(yv))[0])
                zv = SOFFIT_Z + float(camber(np.array([yv]))[0])
                for sx in (-1, 1):
                    Aw = np.stack([np.full(6, xv + sx * (w2 * 0.5 + 0.006)),
                                   np.linspace(yv, yv + 0.060, 6),
                                   np.full(6, zv)], -1)
                    Bw = np.stack([np.full(6, xv + sx * w2 * 0.5),
                                   np.linspace(yv, yv + 0.060, 6),
                                   np.full(6, zv - 0.006)], -1)
                    seam_weld(acc, Aw, Bw, np.array([0, 0, -1.0]),
                              np.array([float(sx), 0, 0]), MAT_GALV, b, a, w,
                              uid="cs%d%d%.2f%d" % (side, seg, yv, sx),
                              step=0.0032, bulge=0.0016, nsec=9, pitch=0.0045)
                    cnt["welds"] += 1
        T.mounts["soffit_rail_%s" % ("e" if side > 0 else "w")] = Frame(
            (side * CHORD_X, 0.0, SOFFIT_Z + CAMBER - CHAN_H),
            (1, 0, 0), (0, 1, 0), (0, 0, -1), 0.0205,
            "41x41 C channel, continuous 16 mm slot, M12 channel nuts")

    # --- soffit cleats ----------------------------------------------------
    n = 0
    for i in range(1, N_STA - 1, 3):
        y = float(STATIONS[i]) + 0.42
        side = 1 if (i // 3) % 2 == 0 else -1
        acc = A[segment_of(y)]
        pd, nd = chord_face(side, 0, y, "down")
        ex = np.array([1.0, 0.0, 0.0])
        ey = np.array([0.0, 1.0, 0.0])
        ez = np.array([0.0, 0.0, 1.0])
        G = rect_grid(0.048, 0.042, 3, 3, taper=0.28)
        h, c = snap_holes(G, [np.array([0.0, -0.012])], 0.008)
        b, a, w = ch_paint(member=0.30, uid=hash01("cleat", i))
        o = pd - ez * 0.048 - ex * 0.0 + ey * 0.0
        grid_plate(acc, o, ey, ez, ex, G, 0.010, h, MAT_PAINT, b, a, w,
                   uid=hash01("cl", i), chamfer=0.0016)
        cnt["plates"] += 1
        T.mounts["soffit_cleat_%d" % n] = Frame(
            o - ez * 0.020, ex, ey, -ez, 0.048, "10 mm cleat, one 16 mm hole")
        n += 1

    # --- TV camera pads ---------------------------------------------------
    for k, y in enumerate(TV_PAD_Y):
        side = 1 if k % 2 == 0 else -1
        acc = A[segment_of(y)]
        pd, nd = chord_face(side, 0, y, "down")
        ex = np.array([1.0, 0.0, 0.0])
        ey = np.array([0.0, 1.0, 0.0])
        ez = np.array([0.0, 0.0, 1.0])
        G = rect_grid(0.110, 0.110, 5, 5, clip=0.020)
        want = [np.array([sx * 0.075, sy * 0.075]) for sx in (-1, 1)
                for sy in (-1, 1)]
        h, c = snap_holes(G, want, BOLTS["M16"][5] + HOLE_CLEAR)
        h2_, c2 = snap_holes(G, [np.array([0.0, 0.0])], 0.016)
        b, a, w = ch_paint(member=0.32, uid=hash01("tvp", k))
        o = pd - ez * 0.009
        grid_plate(acc, o, ex, ey, ez, G, 0.018, h + h2_, MAT_PAINT, b, a, w,
                   uid=hash01("tv", k), chamfer=0.002)
        cnt["plates"] += 1
        ring = np.array([pd + ex * (math.cos(t) * 0.110)
                         + ey * (math.sin(t) * 0.110)
                         for t in np.linspace(0, TAU, 72, endpoint=False)])
        T.mounts["tv_pad_%d" % k] = Frame(
            o - ez * 0.009, ex, ey, -ez, 0.110,
            "18 mm pad, 4 x M16 at 150 x 150, 32 mm cable grommet")

    # --- signal hangers ---------------------------------------------------
    for k, y in enumerate(SIGNAL_Y):
        for side in (-1, 1):
            acc = A[segment_of(y)]
            pd, nd = chord_face(side, 0, y, "down")
            ex = np.array([1.0, 0.0, 0.0])
            ey = np.array([0.0, 1.0, 0.0])
            ez = np.array([0.0, 0.0, 1.0])
            for j, dx in enumerate((-0.055, 0.055)):
                G = rect_grid(0.052, 0.045, 3, 3, taper=0.22)
                h, c = snap_holes(G, [np.array([-0.026, -0.014]),
                                      np.array([0.026, -0.014])],
                                  BOLTS["M20"][5] + HOLE_CLEAR)
                b, a, w = ch_paint(member=0.34, uid=hash01("sig", k, side, j))
                o = pd + ex * dx - ez * 0.045
                grid_plate(acc, o, ey, ez, ex, G, 0.016, h, MAT_PAINT, b, a, w,
                           uid=hash01("sg", k, side, j), chamfer=0.0018)
                cnt["plates"] += 1
            T.mounts["signal_hanger_%d_%s" % (k, "e" if side > 0 else "w")] = \
                Frame(pd - ez * 0.090, ex, ey, -ez, 0.055,
                      "pair of 16 mm hanger plates, 2 x M20 each")


def build_fascia_brackets(A, T, mats, cnt, bolt_shapes, res=1.0):
    """The outriggers gantry_fascia bolts its banner frame to."""
    n = 0
    for i in range(1, N_STA - 1, 2):
        y = float(STATIONS[i])
        acc = A[segment_of(y)]
        for side in (-1, 1):
            for level in (0, 1):
                po, no = chord_face(side, level, y, "out")
                ey = np.array([0.0, 1.0, 0.0])
                ez = np.array([0.0, 0.0, 1.0])
                ex = unit(no)
                G = rect_grid(0.105, 0.075, 4, 3, taper=0.34)
                want = [np.array([0.062, -0.040]), np.array([0.062, 0.040])]
                h, c = snap_holes(G, want, BOLTS["M16"][5] + HOLE_CLEAR)
                b, a, w = ch_paint(member=0.38, uid=hash01("fb", i, side, level))
                o = po + ex * 0.100
                grid_plate(acc, o, ex, ez, ey, G, 0.012, h, MAT_PAINT, b, a, w,
                           uid=hash01("fbp", i, side, level), chamfer=0.0018)
                cnt["plates"] += 1
                A2 = np.stack([po + ez * (-0.070 + 0.140 * t) for t in
                               np.linspace(0, 1, 8)], 0)
                B2 = A2 + ex * 0.008
                seam_weld(acc, A2, B2, ex, ey, MAT_PAINT, b, a, w,
                          uid="fbw%d%d%d" % (i, side, level), step=0.005,
                          bulge=0.0018)
                cnt["welds"] += 1
                tag = "t" if side < 0 else "p"
                T.mounts["fascia_bracket_%s_%d" % (tag, n)] = Frame(
                    o + ex * 0.006, ex, ey, ez, 0.105,
                    "12 mm outrigger, 2 x M16 at 80 mm gauge, level %d" % level)
        n += 1


def build_anchor_eyes(A, T, mats, cnt, res=1.0):
    """Fall-arrest anchor eyes on the top chord: a walkway needs them."""
    n = 0
    for i in range(2, N_STA - 2, 4):
        y = float(STATIONS[i]) + 0.30
        side = 1 if (i // 4) % 2 == 0 else -1
        acc = A[segment_of(y)]
        pu, nu_ = chord_face(side, 1, y, "up")
        ex = np.array([1.0, 0.0, 0.0])
        ey = np.array([0.0, 1.0, 0.0])
        ez = np.array([0.0, 0.0, 1.0])
        G = rect_grid(0.048, 0.062, 3, 4, taper=0.42)
        h, _ = snap_holes(G, [np.array([0.0, 0.026])], 0.014)
        b, a, w = ch_mach(member=0.42, uid=hash01("eye", i))
        o = pu + ez * 0.062
        grid_plate(acc, o, ey, ez, ex, G, 0.014, h, MAT_MACHINED, b, a, w,
                   uid=hash01("ey", i), chamfer=0.002)
        cnt["plates"] += 1
        T.mounts["anchor_eye_%d" % n] = Frame(o + ez * 0.026, ex, ey, ez, 0.014,
                                              "fall-arrest anchor eye")
        n += 1


# --------------------------------------------------------------------------- #
# 13.  MATERIALS                                                                #
# --------------------------------------------------------------------------- #
#
# Five surfaces, each built as a stack of things that PHYSICALLY HAPPENED to
# the steel, in the order they happened.  The one thing this item must not get
# wrong: the structure is HOT-DIP GALVANISED AND THEN PAINTED, so a paint chip
# exposes DULL GREY ZINC, not rust.  Rust only appears where something cut,
# drilled or ground through the zinc afterwards - the site-drilled holes, the
# field welds, the sawn ends - and that is carried by aux.b (machined), not by
# the chip mask.  Painting rust into every chip is the single commonest tell
# in rendered steelwork and it is wrong for anything built since about 1970.

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


def _up_face(g):
    """0..1 how much a surface faces UP.  Decides dirt, moss and bird lime."""
    nrm = g.n("ShaderNodeNewGeometry")
    z = g.sepxyz((nrm, 1))
    return g.math('MAXIMUM', (z, 2), 0.0, clamp=True)


def _down_face(g):
    nrm = g.n("ShaderNodeNewGeometry")
    z = g.sepxyz((nrm, 1))
    return g.math('MAXIMUM', g.math('MULTIPLY', (z, 2), -1.0), 0.0, clamp=True)


def mat_paint():
    """Two-pack epoxy/PU over hot-dip galvanised steel.  Eleven layers.

      1  topcoat, with a per-member dye drift so no two chords are exactly the
         same grey and the site-applied touch-up is a shade off.
      2  AIRLESS SPRAY texture: orange peel at 2-4 mm, dry-spray sparkle where
         the gun was too far away, and runs where it was too close.
      3  mill scale telegraphing through two coats, which is what stops a flat
         face reading as a swatch.
      4  CHALKING on the sun side.  A 12.5 deg sun all season lightens and
         desaturates the up-facing surfaces; the soffit never chalks, which is
         why the underside of a gantry is always a different colour from the
         top of it.
      5  RAIN WASHING.  Water runs off the walkway grating and streaks down
         the outer faces in bands 20-60 mm apart.  Clean stripes on dirty
         steel, not dirty stripes on clean steel.
      6  BIRD LIME on the up faces and the drip streaks below them.  A gantry
         is the tallest perch for 400 m and it looks it.
      7  CHIPS to bare ZINC, keyed off aux.r so the arrises go first.
      8  a rarer, deeper chip through the zinc to steel.
      9  WHITE RUST: zinc carbonate bloom creeping out of every chip edge.
     10  RED rust ONLY where aux.b says the zinc was machined away.
     11  road grime in the low-gloss valleys, heaviest low down.
    """
    m, g, b, _ = _new_mat("Paint")
    base, aux, wear, bs, au, we, tc, uv, obj = HS._chan(g)
    edge, weld, mach = (au, 0), (au, 1), (au, 2)
    chip, dirt, rust, age = (we, 0), (we, 1), (we, 2), (wear, 3)
    memb = (aux, 3)
    up, down = _up_face(g), _down_face(g)

    lot = g.noise(g.vmath('MULTIPLY', obj, (1.7, 1.7, 1.7)), scale=2.0,
                  detail=5.0, rough=0.55)
    k = g.math('ADD', 0.955, g.math('MULTIPLY',
                                    g.math('SUBTRACT',
                                           g.math('ADD',
                                                  g.math('MULTIPLY', lot, 0.62),
                                                  g.math('MULTIPLY', memb, 0.38)),
                                           0.5), 0.115))
    col = g.n("ShaderNodeMixRGB", blend_type='MULTIPLY')
    g._feed(col, 0, 1.0)
    g._feed(col, 1, base)
    g._feed(col, 2, g.comb(k, k, k))

    peel = g.noise(g.vmath('MULTIPLY', obj, (300.0, 300.0, 300.0)), scale=2.0,
                   detail=4.0, rough=0.5)
    dry = g.voro(g.vmath('MULTIPLY', obj, (900.0, 900.0, 900.0)), scale=1.0,
                 rand=1.0, feature='SMOOTH_F1')
    scale_ = g.noise(g.vmath('MULTIPLY', obj, (11.0, 11.0, 11.0)), scale=2.5,
                     detail=7.0, rough=0.62)
    runs = g.wave(g.vmath('MULTIPLY', obj, (26.0, 26.0, 1.05)), scale=6.0,
                  dist=6.0, detail=3.0, band='Z')
    runm = g.math('MULTIPLY', g.ramp(runs, [(0.66, (0, 0, 0)), (0.88, (1, 1, 1))]),
                  0.5, clamp=True)
    drym = g.math('MULTIPLY', g.math('MULTIPLY', (dry, 0), edge), 0.55,
                  clamp=True)
    col = g.mix(g.math('MULTIPLY', drym, 0.30), col,
                g.mix(0.5, col, (0.62, 0.63, 0.64)))

    sunk = g.math('MULTIPLY', g.math('MULTIPLY', HS._sun_face(g), up),
                  g.math('ADD', 0.30, g.math('MULTIPLY', age, 1.0)), clamp=True)
    hsv = g.n("ShaderNodeHueSaturation")
    g._feed(hsv, 0, 0.5)
    g._feed(hsv, 1, 0.66)
    g._feed(hsv, 2, 1.20)
    g._feed(hsv, 3, 1.0)
    g._feed(hsv, 4, col)
    col = g.mix(g.math('MULTIPLY', sunk, 0.46), col, hsv)
    col = g.mix(g.math('MULTIPLY', g.math('SUBTRACT', scale_, 0.45), 0.28),
                col, g.mix(0.35, col, (0.030, 0.029, 0.028)))

    # ---- 5. rain washing off the walkway ----------------------------------
    wash = g.wave(g.vmath('MULTIPLY', obj, (33.0, 33.0, 0.55)), scale=5.0,
                  dist=9.0, detail=4.0, band='Z')
    washm = g.math('MULTIPLY', g.ramp(wash, [(0.42, (0, 0, 0)), (0.78, (1, 1, 1))]),
                   g.math('SUBTRACT', 1.0, up), clamp=True)

    # ---- 6. bird lime -------------------------------------------------------
    lime = g.voro(g.vmath('MULTIPLY', obj, (34.0, 34.0, 34.0)), scale=1.0,
                  rand=1.0, feature='SMOOTH_F1')
    limem = g.ramp((lime, 0), [(0.0, (1, 1, 1)), (0.055, (0, 0, 0))])
    limem = g.math('MULTIPLY', (limem, 0), g.math('MULTIPLY', up, 1.25),
                   clamp=True)
    drip = g.noise(g.vmath('MULTIPLY', obj, (18.0, 18.0, 1.4)), scale=2.0,
                   detail=7.0, rough=0.6)
    dripm = g.math('MULTIPLY', g.ramp(drip, [(0.60, (0, 0, 0)), (0.80, (1, 1, 1))]),
                   g.math('MULTIPLY', down, 0.55), clamp=True)

    # ---- 7/8. chips, to zinc and to steel -----------------------------------
    cn = g.voro(g.vmath('MULTIPLY', obj, (140.0, 140.0, 140.0)), scale=1.0,
                rand=1.0, feature='SMOOTH_F1')
    cnr = g.ramp((cn, 0), [(0.0, (0, 0, 0)), (0.36, (1, 1, 1))])
    cn2 = g.noise(g.vmath('MULTIPLY', obj, (42.0, 42.0, 42.0)), scale=2.0,
                  detail=8.0, rough=0.66)
    cn3 = g.noise(g.vmath('MULTIPLY', obj, (175.0, 175.0, 175.0)), scale=2.0,
                  detail=6.0, rough=0.60)
    cm = g.math('ADD', g.math('MULTIPLY', (cnr, 0), 0.34),
                g.math('ADD', g.math('MULTIPLY', cn2, 0.46),
                       g.math('MULTIPLY', cn3, 0.20)))
    drive = g.math('MULTIPLY', chip,
                   g.math('ADD', 0.16, g.math('MULTIPLY', edge, 1.75)),
                   clamp=True)
    drive = g.math('ADD', drive, g.math('MULTIPLY', age, 0.06), clamp=True)
    # TWO THINGS DECIDE A CHIP: whether this patch of steel ever got hit, and
    # whether the film failed at this exact spot.  The first version used only
    # the second, over a ramp window so tight that nothing fired; opening the
    # window then turned the whole truss into 24 mm camouflage mottle, because
    # a per-point threshold with no COVERAGE term chips everywhere at once.
    # `cover` is that missing term: a low-frequency mask that lets roughly a
    # fifth of the surface chip at all, so the chips land in clusters - round
    # a lifting point, along an arris, where the erection sling bore - the way
    # damage actually distributes on a fabricated member.
    cover = g.ramp(g.noise(g.vmath('MULTIPLY', obj, (2.6, 2.6, 2.6)),
                           scale=2.0, detail=6.0, rough=0.58),
                   [(0.505, (0, 0, 0)), (0.640, (1, 1, 1))])
    chip1 = g.ramp(g.math('ADD', cm, g.math('MULTIPLY', drive, 0.58)),
                   [(0.858, (0, 0, 0)), (0.962, (1, 1, 1))])
    chip1 = g.math('MULTIPLY', (chip1, 0), (cover, 0), clamp=True)
    chip2 = g.ramp(g.math('ADD', cm, g.math('MULTIPLY', drive, 0.44)),
                   [(0.962, (0, 0, 0)), (1.045, (1, 1, 1))])
    chip2 = g.math('MULTIPLY', (chip2, 0), (cover, 0), clamp=True)
    zinc = g.mix(g.math('MULTIPLY', (dry, 0), 0.75), srgb(ZINC_HEX),
                 (0.300, 0.312, 0.322))
    col = g.mix(g.math('MULTIPLY', chip1, 0.93), col, zinc)
    steelc = g.mix(g.math('MULTIPLY', peel, 0.6), (0.115, 0.116, 0.120),
                   (0.190, 0.192, 0.198))
    col = g.mix(g.math('MULTIPLY', chip2, 0.90), col, steelc)

    # ---- 9. white rust ------------------------------------------------------
    bloom = g.noise(g.vmath('MULTIPLY', obj, (85.0, 85.0, 85.0)), scale=2.0,
                    detail=7.0, rough=0.6)
    wr = g.math('MULTIPLY', g.math('MULTIPLY', chip1, bloom),
                g.math('ADD', 0.30, g.math('MULTIPLY', age, 0.9)), clamp=True)
    col = g.mix(g.math('MULTIPLY', wr, 0.55), col, (0.560, 0.566, 0.560))

    # ---- 10. RED rust, only where the zinc was machined off -----------------
    scab = g.voro(g.vmath('MULTIPLY', obj, (380.0, 380.0, 380.0)), scale=1.0,
                  rand=1.0, feature='SMOOTH_F1')
    rk = g.math('MULTIPLY', rust,
                g.math('ADD', g.math('MULTIPLY', mach, 0.95),
                       g.math('MULTIPLY', weld, 0.30)), clamp=True)
    bleed = g.noise(g.vmath('MULTIPLY', obj, (26.0, 26.0, 1.9)), scale=2.5,
                    detail=7.0, rough=0.62)
    rbl = g.math('MULTIPLY', g.math('MULTIPLY', rk, bleed), 0.9, clamp=True)
    col = g.mix(g.math('MULTIPLY', rbl, 0.40), col, (0.118, 0.052, 0.024))
    col = g.mix(g.math('MULTIPLY', rk, 0.88), col,
                g.mix(g.math('MULTIPLY', (scab, 0), 0.75), (0.150, 0.056, 0.023),
                      (0.238, 0.100, 0.036)))
    col = g.mix(g.math('MULTIPLY', limem, 0.88), col, (0.520, 0.512, 0.470))
    col = g.mix(g.math('MULTIPLY', dripm, 0.34), col, (0.330, 0.325, 0.300))
    # ROAD FILM.  The soffit of a gantry over a racing surface is the one face
    # rain never washes, and what settles on it is rubber and tyre dust, not
    # the pale road dust that lands on the top.  Without this the underside
    # renders the same colour as the walkway, which is the single most
    # noticeable thing about a real gantry seen from below.
    film = g.noise(g.vmath('MULTIPLY', obj, (9.0, 9.0, 5.5)), scale=2.5,
                   detail=8.0, rough=0.62)
    fk = g.math('MULTIPLY', g.math('MULTIPLY', down, dirt),
                g.math('ADD', 0.45, g.math('MULTIPLY', film, 1.15)), clamp=True)
    col = g.mix(g.math('MULTIPLY', fk, 0.72), col, (0.031, 0.029, 0.028))

    # ---- 11. grime ----------------------------------------------------------
    gr = g.noise(g.vmath('MULTIPLY', obj, (5.0, 5.0, 2.6)), scale=2.5,
                 detail=8.0, rough=0.64)
    grit = g.voro(g.vmath('MULTIPLY', obj, (640.0, 640.0, 640.0)), scale=1.0,
                  rand=1.0, feature='SMOOTH_F1')
    dk = g.math('MULTIPLY', dirt,
                g.math('ADD', 0.28, g.math('MULTIPLY', gr, 1.30)), clamp=True)
    dk = g.math('MULTIPLY', dk, g.math('ADD', 0.55,
                                       g.math('MULTIPLY', up, 0.75)), clamp=True)
    dk = g.math('MULTIPLY', dk, g.math('SUBTRACT', 1.02,
                                       g.math('MULTIPLY', washm, 0.85)),
                clamp=True)
    col = g.mix(g.math('MULTIPLY', dk, 0.94), col,
                g.mix(g.math('MULTIPLY', (grit, 0), 0.5), (0.046, 0.040, 0.031),
                      (0.076, 0.064, 0.050)))
    g._feed(b, 0, col)

    met = g.math('ADD', g.math('MULTIPLY', chip2, 0.80),
                 g.math('MULTIPLY', mach, 0.55), clamp=True)
    met = g.math('MULTIPLY', met, g.math('SUBTRACT', 1.0,
                                         g.math('MULTIPLY', rk, 0.9)), clamp=True)
    HS._set(g, b, met, "Metallic")
    rough = g.math('ADD', 0.26, g.math('MULTIPLY', age, 0.26))
    rough = g.math('ADD', rough, g.math('MULTIPLY', sunk, 0.26))
    rough = g.math('ADD', rough, g.math('MULTIPLY', chip1, 0.20))
    rough = g.math('ADD', rough, g.math('MULTIPLY', rk, 0.34))
    rough = g.math('ADD', rough, g.math('MULTIPLY', dk, 0.22))
    rough = g.math('ADD', rough, g.math('MULTIPLY', limem, 0.30))
    rough = g.math('ADD', rough, g.math('MULTIPLY', fk, 0.30))
    rough = g.math('SUBTRACT', rough, g.math('MULTIPLY', runm, 0.14))
    rough = g.math('SUBTRACT', rough, g.math('MULTIPLY', washm, 0.10))
    rough = g.math('ADD', rough,
                   g.math('MULTIPLY', g.math('SUBTRACT', peel, 0.5), 0.12),
                   clamp=True)
    HS._set(g, b, rough, "Roughness")
    HS._set(g, b, 0.45, "Specular IOR Level", "Specular")
    cw = g.math('MULTIPLY',
                g.math('SUBTRACT', 1.0, g.math('MULTIPLY', age, 0.80)),
                g.math('SUBTRACT', 1.0, g.math('MULTIPLY', chip1, 1.0)),
                clamp=True)
    HS._set(g, b, g.math('MULTIPLY', cw, 0.17), "Coat Weight")
    HS._set(g, b, g.math('ADD', 0.13, g.math('MULTIPLY', age, 0.30)),
            "Coat Roughness")

    h = g.math('ADD', g.math('MULTIPLY', peel, 0.28),
               g.math('MULTIPLY', runm, 0.30))
    h = g.math('ADD', h, g.math('MULTIPLY', scale_, 0.20))
    h = g.math('ADD', h, g.math('MULTIPLY', weld, 0.34))
    h = g.math('ADD', h, g.math('MULTIPLY', limem, 0.55))
    h = g.math('SUBTRACT', h, g.math('MULTIPLY', chip1, 0.14))
    h = g.math('ADD', h, g.math('MULTIPLY', g.math('MULTIPLY', rk, (scab, 0)),
                                0.80))
    # STATED AS RADIANCE MODULATION, NOT MILLIMETRES (itemkit 5b, brief 4a).
    # What the eye judges is what the bump does to the LIGHT, and under this
    # film's 12.47 deg sun that carries a 4.52x amplifier: m = 2 sin(theta) /
    # tan(e).  Three amplitude sets were rendered and REJECTED on the human
    # figures and every one had been chosen in millimetres.  Every
    # `modulation_pp` in this module REPRODUCES the Distance it already shipped,
    # to better than 1e-6 relative -- NOTHING HERE IS A RE-TUNE.
    #
    # THE WAVELENGTHS COME FROM THE SAME LITERALS THAT PICKED THE SCALES, and
    # where the coordinate is PRE-MULTIPLIED the two literals multiply:
    # `vmath('MULTIPLY', obj, (300,300,300))` into `noise(scale=2.0)` is a
    # 2.67 mm feature -- the 2-4 mm orange peel the docstring claims -- not the
    # 800 mm a reader of the Scale socket alone would report.
    # (`bump_relief_report` reads that socket alone; do not copy its column.)
    #
    # EVERY HEIGHT HERE IS A SUM, so one wavelength per stage is a CHOICE.  The
    # band named is the ungated one that carries most of the height, and
    # `height_pp` is its own weight in that sum, so the stated m is THAT band's
    # modulation.  At the same Distance:
    #
    #   [0] orange peel   w 0.28  lam   2.67 mm  m 6.917  <- named, ungated
    #       paint runs    w 0.30  lam 158.73 mm  m 0.193  gated ramp, x0.5
    #       mill scale    w 0.20  lam  58.18 mm  m 0.351  ungated
    #       weld bead     w 0.34  vertex mask -- no wavelength
    #       bird lime     w 0.55  lam  63.82 mm  m 0.877  gated to up-faces
    #       chip1 (-ve)   w 0.14  mask        -- no wavelength
    #       rust scab     w 0.80  lam   5.71 mm  m 7.648  gated by wear.b
    #   [1] road grit     w 0.50  lam   3.39 mm  m 0.867  <- named
    #       dry spray     w 0.42  lam   2.41 mm  m 1.023
    #
    # NOT RE-TUNED, AND WHY [0] IS LEFT AT 6.917.  An ungated isotropic field
    # above m ~ 1.5 is the felt this law exists to prevent, and airless-spray
    # orange peel at 6.9 is one -- 1.0 mm p-p on a 2.7 mm feature is a 50 deg
    # surface, which is not paint.  It cannot be corrected from a call site:
    # ONE Distance serves seven bands whose m spans 0.19 to 7.65, and the 15x
    # cut that would put the peel in isotropic_micro would take the rust scab
    # -- a real scale with real walls -- to m 0.5 with it.  The fix is to split
    # the sum across stages or reweight it; both are structural and outside
    # this migration.  Stated out loud and reported instead of nudged.
    LAM_PEEL = K.NOISE_WAVELENGTH_FACTOR / (300.0 * 2.0)   # 2.67 mm
    LAM_GRIT = K.VORONOI_WAVELENGTH_FACTOR / 640.0         # 3.39 mm
    bmp = g.bump(h, 0.36, modulation_pp=6.917426, wavelength_m=LAM_PEEL,
                 height_pp=0.28)
    fine = g.bump(g.math('ADD', g.math('MULTIPLY', (grit, 0), 0.50),
                         g.math('MULTIPLY', (dry, 0), 0.42)), 0.13, normal=bmp,
                  modulation_pp=0.867414, wavelength_m=LAM_GRIT,
                  height_pp=0.50)
    HS._set(g, b, fine, "Normal")
    return m


def mat_galv():
    """Bare hot-dip galvanised steel: the channel, the stanchion bases, the
    scupper pipes and every icicle the bath left behind.

      1  the SPANGLE.  Zinc freezes into 3-10 mm crystals; at 1244 px/m they
         are 4-12 px across, and each one gets its own normal tilt and its own
         brightness.  It is the single thing that says 'galvanised'.
      2  the dip: vertical drainage runs and the slightly wavy skin.
      3  weathering from bright spangle to matt carbonate grey, by wear.a.
      4  WHITE RUST where water sat in a crevice.
      5  the wet/dry line, where the section stood in the rack.
      6  grime, heavier on the up faces.
    """
    m, g, b, _ = _new_mat("Galv")
    base, aux, wear, bs, au, we, tc, uv, obj = HS._chan(g)
    edge, weld, mach = (au, 0), (au, 1), (au, 2)
    chip, dirt, rust, age = (we, 0), (we, 1), (we, 2), (wear, 3)
    up = _up_face(g)

    sp = g.voro(g.vmath('MULTIPLY', obj, (180.0, 180.0, 180.0)), scale=1.0,
                rand=1.0, feature='F1')
    spc = g.sep((sp, 1))
    spd = g.voro(g.vmath('MULTIPLY', obj, (180.0, 180.0, 180.0)), scale=1.0,
                 rand=1.0, feature='DISTANCE_TO_EDGE')
    fine = g.voro(g.vmath('MULTIPLY', obj, (620.0, 620.0, 620.0)), scale=1.0,
                  rand=1.0, feature='SMOOTH_F1')
    runs = g.wave(g.vmath('MULTIPLY', obj, (48.0, 48.0, 1.1)), scale=6.0,
                  dist=8.0, detail=4.0, band='Z')
    skin = g.noise(g.vmath('MULTIPLY', obj, (16.0, 16.0, 16.0)), scale=2.5,
                   detail=7.0, rough=0.6)
    wetline = g.noise(g.vmath('MULTIPLY', obj, (3.0, 3.0, 9.0)), scale=2.0,
                      detail=6.0, rough=0.6)

    col = g.mix(g.math('MULTIPLY', (spc, 0), 0.85), (0.300, 0.312, 0.322),
                (0.470, 0.482, 0.492))
    col = g.mix(g.math('MULTIPLY', g.ramp((spd, 0), [(0.0, (1, 1, 1)),
                                                     (0.030, (0, 0, 0))]), 0.45),
                col, (0.235, 0.244, 0.252))
    col = g.mix(g.math('MULTIPLY', skin, 0.30), col, (0.352, 0.360, 0.368))
    weath = g.math('MULTIPLY', age, g.math('ADD', 0.35,
                                           g.math('MULTIPLY', up, 0.75)),
                   clamp=True)
    col = g.mix(g.math('MULTIPLY', weath, 0.62), col, (0.245, 0.250, 0.252))
    wr = g.math('MULTIPLY', g.math('MULTIPLY', rust, wetline),
                g.math('ADD', 0.25, g.math('MULTIPLY', age, 0.9)), clamp=True)
    col = g.mix(g.math('MULTIPLY', wr, 0.70), col, (0.585, 0.590, 0.578))
    col = g.mix(g.math('MULTIPLY', g.math('MULTIPLY', dirt, up), 0.55), col,
                g.mix(g.math('MULTIPLY', (fine, 0), 0.5), (0.050, 0.044, 0.034),
                      (0.084, 0.072, 0.056)))
    g._feed(b, 0, col)
    HS._set(g, b, g.math('SUBTRACT', 0.92,
                         g.math('MULTIPLY', weath, 0.30), clamp=True), "Metallic")
    rough = g.math('ADD', 0.20, g.math('MULTIPLY', weath, 0.42))
    rough = g.math('ADD', rough, g.math('MULTIPLY', wr, 0.30))
    rough = g.math('ADD', rough, g.math('MULTIPLY',
                                        g.math('SUBTRACT', (spc, 0), 0.5), 0.16),
                   clamp=True)
    HS._set(g, b, rough, "Roughness")
    h = g.math('ADD', g.math('MULTIPLY', (spc, 0), 0.55),
               g.math('MULTIPLY', runs, 0.25))
    h = g.math('ADD', h, g.math('MULTIPLY', weld, 0.35))
    h = g.math('ADD', h, g.math('MULTIPLY', skin, 0.18))
    # STATED AS RADIANCE MODULATION, NOT MILLIMETRES (itemkit 5b, brief 4a).
    # Both reproduce the shipped Distance; neither is a re-tune.
    #
    #   [0] spangle cells w 0.55  lam  12.06 mm  m 2.081  <- named, ungated
    #       drainage runs w 0.25  lam 151.52 mm  m 0.077  ungated
    #       weld bead     w 0.35  vertex mask -- no wavelength
    #       dip skin      w 0.18  lam  40.00 mm  m 0.211  ungated
    #   [1] fine grain    w 1.00  lam   3.50 mm  m 1.064  <- named (single
    #                             texture, so height_pp is 1.0)
    #
    # WHY m 2.081 IS A HARD_FEATURE CLAIM AND NOT AN ISOTROPIC ONE.  The named
    # band is `spc` -- the Voronoi COLOR output, a PER-CELL RANDOM.  It is flat
    # inside a crystal and steps at the boundary, so this height field puts no
    # slope on the face of a spangle and all of it on the grain boundary: an
    # arris every 12.06 mm.  RELIEF_BANDS["hard_feature"] (1.50-6.00) is the
    # band an arris belongs in, so 2.081 is the right kind of number here even
    # though the same figure on a crumple would be the felt.  (Contrast
    # marshal_post_column's spangle, which uses the F1 DISTANCE and so does
    # tilt each crystal face.)  Left as shipped.
    LAM_SPANGLE = K.VORONOI_WAVELENGTH_FACTOR / 180.0      # 12.06 mm
    LAM_FINE = K.VORONOI_WAVELENGTH_FACTOR / 620.0         #  3.50 mm
    bmp = g.bump(h, 0.30, modulation_pp=2.081242,
                 wavelength_m=LAM_SPANGLE, height_pp=0.55)
    HS._set(g, b, g.bump((fine, 0), 0.12, normal=bmp,
                         modulation_pp=1.064042, wavelength_m=LAM_FINE),
            "Normal")
    return m


def mat_fastener():
    """Spun-galvanised bolts, nuts and washers.

      1  the centrifuged zinc: thinner and finer-grained than a dipped
         section, so a much tighter spangle.
      2  WRENCH POLISH on the flats and the corners: aux.r is 1.0 exactly on
         the six corners of every nut and head, and that is where a socket
         burnishes the zinc bright.
      3  thread grease, which collects grit and goes black.
      4  rust bleeding out of the crevice under the washer.
      5  the torque stripe: a stripe of yellow paint across the nut and onto
         the plate, so an inspector can see whether it has moved.
    """
    m, g, b, _ = _new_mat("Fastener")
    base, aux, wear, bs, au, we, tc, uv, obj = HS._chan(g)
    edge, weld, mach = (au, 0), (au, 1), (au, 2)
    chip, dirt, rust, age = (we, 0), (we, 1), (we, 2), (wear, 3)
    uid = (aux, 3)

    sp = g.voro(g.vmath('MULTIPLY', obj, (900.0, 900.0, 900.0)), scale=1.0,
                rand=1.0, feature='F1')
    spc = g.sep((sp, 1))
    grit = g.voro(g.vmath('MULTIPLY', obj, (2200.0, 2200.0, 2200.0)), scale=1.0,
                  rand=1.0, feature='SMOOTH_F1')
    grime = g.noise(g.vmath('MULTIPLY', obj, (60.0, 60.0, 60.0)), scale=2.0,
                    detail=7.0, rough=0.62)
    crev = g.noise(g.vmath('MULTIPLY', obj, (240.0, 240.0, 240.0)), scale=2.0,
                   detail=6.0, rough=0.6)
    stripe = g.wave(g.vmath('MULTIPLY', obj, (90.0, 90.0, 90.0)), scale=3.0,
                    dist=0.0, detail=1.0, band='X')

    col = g.mix(g.math('MULTIPLY', (spc, 0), 0.75), (0.275, 0.286, 0.296),
                (0.430, 0.442, 0.452))
    pol = g.math('MULTIPLY', edge, g.math('ADD', 0.30,
                                          g.math('MULTIPLY', grime, 0.8)),
                 clamp=True)
    col = g.mix(g.math('MULTIPLY', pol, 0.55), col, (0.545, 0.552, 0.560))
    gk = g.math('MULTIPLY', mach, g.math('ADD', 0.35,
                                         g.math('MULTIPLY', grime, 1.1)),
                clamp=True)
    col = g.mix(g.math('MULTIPLY', gk, 0.60), col, (0.045, 0.042, 0.035))
    rk = g.math('MULTIPLY', rust, g.math('ADD', 0.20,
                                         g.math('MULTIPLY', crev, 1.3)),
                clamp=True)
    col = g.mix(g.math('MULTIPLY', rk, 0.55), col, (0.180, 0.078, 0.030))
    tq = g.math('MULTIPLY',
                g.ramp(stripe, [(0.46, (0, 0, 0)), (0.50, (1, 1, 1)),
                                (0.54, (0, 0, 0))]),
                g.ramp(uid, [(0.55, (0, 0, 0)), (0.58, (1, 1, 1))]), clamp=True)
    col = g.mix(g.math('MULTIPLY', (tq, 0), 0.80), col, (0.480, 0.330, 0.030))
    col = g.mix(g.math('MULTIPLY', g.math('MULTIPLY', dirt, (grit, 0)), 0.40),
                col, (0.062, 0.055, 0.044))
    g._feed(b, 0, col)
    HS._set(g, b, g.math('SUBTRACT', 0.95, g.math('MULTIPLY', rk, 0.85),
                         clamp=True), "Metallic")
    rough = g.math('ADD', 0.24, g.math('MULTIPLY', age, 0.22))
    rough = g.math('SUBTRACT', rough, g.math('MULTIPLY', pol, 0.16))
    rough = g.math('ADD', rough, g.math('MULTIPLY', rk, 0.42))
    rough = g.math('ADD', rough, g.math('MULTIPLY', gk, 0.30), clamp=True)
    HS._set(g, b, rough, "Roughness")
    h = g.math('ADD', g.math('MULTIPLY', (spc, 0), 0.40),
               g.math('MULTIPLY', (grit, 0), 0.35))
    h = g.math('ADD', h, g.math('MULTIPLY', g.math('MULTIPLY', rk, crev), 0.9))
    # STATED AS RADIANCE MODULATION, NOT MILLIMETRES (itemkit 5b, brief 4a).
    # Both reproduce the shipped Distance; neither is a re-tune.
    #
    #   [0] spun spangle  w 0.40  lam 2.41 mm  m 1.632  <- named, ungated
    #       thread grit   w 0.35  lam 0.99 mm  m 3.303  ungated
    #       rust in crev  w 0.90  lam 3.33 mm  m 2.587  gated by wear.b
    #   [1] thread grit   w 1.00  lam 0.99 mm  m 1.533  <- named (single
    #                             texture, so height_pp is 1.0)
    #
    # As in mat_galv the named band is the Voronoi COLOR, a per-cell random, so
    # the relief is a step at every grain boundary rather than a tilt across a
    # crystal: hard_feature (1.50-6.00) is the right band and 1.632 is at its
    # floor.  The spun-galvanised spangle is 2.41 mm against the dipped
    # section's 12.06 mm, which is the docstring's "much tighter spangle" and
    # is a genuine claim about the process, not a copied number.
    # THE GRIT AT m 3.30 IS THE ONE TO WATCH: 0.12 mm p-p on a 0.99 mm cell is
    # ungated, and if a pixel-peep of the fasteners comes back gritty rather
    # than galvanised that band -- not the spangle -- is the cause.  Left as
    # shipped; the two share a Distance and cannot be separated from here.
    LAM_SPANGLE = K.VORONOI_WAVELENGTH_FACTOR / 900.0      # 2.41 mm
    LAM_GRIT = K.VORONOI_WAVELENGTH_FACTOR / 2200.0        # 0.99 mm
    bmp = g.bump(h, 0.16, modulation_pp=1.63184,
                 wavelength_m=LAM_SPANGLE, height_pp=0.40)
    HS._set(g, b, g.bump((grit, 0), 0.09, normal=bmp,
                         modulation_pp=1.532874, wavelength_m=LAM_GRIT),
            "Normal")
    return m


def mat_machined():
    """Bright machined and flame-cut steel: bearing plates, shims, lugs.

    These parts were burned or milled AFTER galvanising, so they are the only
    surfaces on the truss with genuine red rust on them.  Mill marks run in
    one direction, oxy-cut drag lines in another, and the heat-affected zone
    round a field weld carries the straw-blue-purple temper colours.
    """
    m, g, b, _ = _new_mat("Machined")
    base, aux, wear, bs, au, we, tc, uv, obj = HS._chan(g)
    edge, weld, mach = (au, 0), (au, 1), (au, 2)
    chip, dirt, rust, age = (we, 0), (we, 1), (we, 2), (wear, 3)

    mill = g.wave(g.vmath('MULTIPLY', obj, (520.0, 520.0, 520.0)), scale=6.0,
                  dist=3.0, detail=3.0, band='X')
    drag = g.wave(g.vmath('MULTIPLY', obj, (330.0, 330.0, 330.0)), scale=5.0,
                  dist=2.0, detail=2.0, band='Z')
    bloom = g.noise(g.vmath('MULTIPLY', obj, (55.0, 55.0, 55.0)), scale=2.0,
                    detail=7.0, rough=0.62)
    pit = g.voro(g.vmath('MULTIPLY', obj, (700.0, 700.0, 700.0)), scale=1.0,
                 rand=1.0, feature='SMOOTH_F1')
    heat = g.noise(g.vmath('MULTIPLY', obj, (34.0, 34.0, 34.0)), scale=2.0,
                   detail=5.0, rough=0.55)
    grime = g.noise(g.vmath('MULTIPLY', obj, (7.0, 7.0, 4.0)), scale=2.5,
                    detail=7.0, rough=0.6)

    col = g.mix(g.math('MULTIPLY', mill, 0.35), (0.230, 0.234, 0.240),
                (0.330, 0.336, 0.344))
    col = g.mix(g.math('MULTIPLY', g.math('MULTIPLY', drag, edge), 0.45), col,
                (0.150, 0.150, 0.152))
    rk = g.math('MULTIPLY', rust, g.math('ADD', 0.30,
                                         g.math('MULTIPLY', bloom, 1.3)),
                clamp=True)
    col = g.mix(g.math('MULTIPLY', rk, 0.85), col,
                g.mix(g.math('MULTIPLY', (pit, 0), 0.7), (0.165, 0.062, 0.026),
                      (0.255, 0.112, 0.040)))
    tint = g.math('MULTIPLY', weld, g.math('ADD', 0.3,
                                           g.math('MULTIPLY', heat, 1.2)),
                  clamp=True)
    tcol = g.ramp(heat, [(0.30, (0.42, 0.30, 0.10)), (0.50, (0.16, 0.19, 0.30)),
                         (0.70, (0.22, 0.11, 0.26))])
    col = g.mix(g.math('MULTIPLY', tint, 0.70), col, tcol)
    col = g.mix(g.math('MULTIPLY', g.math('MULTIPLY', dirt, grime), 0.45), col,
                (0.052, 0.046, 0.036))
    g._feed(b, 0, col)
    HS._set(g, b, g.math('SUBTRACT', 0.96, g.math('MULTIPLY', rk, 0.9),
                         clamp=True), "Metallic")
    rough = g.math('ADD', 0.22, g.math('MULTIPLY', rk, 0.48))
    rough = g.math('ADD', rough, g.math('MULTIPLY',
                                        g.math('SUBTRACT', mill, 0.5), 0.14))
    rough = g.math('ADD', rough, g.math('MULTIPLY', age, 0.18), clamp=True)
    HS._set(g, b, rough, "Roughness")
    h = g.math('ADD', g.math('MULTIPLY', mill, 0.30),
               g.math('MULTIPLY', g.math('MULTIPLY', drag, edge), 0.45))
    h = g.math('ADD', h, g.math('MULTIPLY', weld, 0.40))
    h = g.math('ADD', h, g.math('MULTIPLY', g.math('MULTIPLY', rk, (pit, 0)),
                                0.90))
    # STATED AS RADIANCE MODULATION, NOT MILLIMETRES (itemkit 5b, brief 4a).
    # Both reproduce the shipped Distance; neither is a re-tune.
    #
    #   [0] mill marks    w 0.30  lam 0.10 mm  m 8.871  <- named, ungated
    #       oxy drag line w 0.45  lam 0.61 mm  m 7.083  gated by aux.r
    #       weld bead     w 0.40  vertex mask -- no wavelength
    #       rust pitting  w 0.90  lam 3.10 mm  m 3.996  gated by wear.b
    #   [1] rust pitting  w 1.00  lam 3.10 mm  m 0.731  <- named (single
    #                             texture, so height_pp is 1.0)
    #
    # THIS IS THE DEEPEST STAGE IN THE MODULE AND IT IS THE ONE TO ARGUE WITH.
    # 0.162 mm p-p on a 0.32 mm mill pitch is a 58 deg groove wall; a milled
    # face is 0.01-0.02 mm Ra and reads as a SHEEN, which is why the roughness
    # term above already carries `mill` and does not need the normal to.  m
    # 7.652 is over RELIEF_BANDS["hard_feature"] (ceiling 6.00) and only 15 %
    # under the 9.04 this sun can deliver at any slope at all.
    #
    # NOT RE-TUNED, AND WHY.  One Distance serves four bands.  Bringing the
    # mill marks to a defensible m ~ 2 is a 7x cut, and it would take the rust
    # pitting -- a real void with real walls, correctly at 4.0 -- down to 0.63
    # with it, i.e. it would trade a wrong sheen for a wrong rust.  The
    # separation needs the sum split across stages, which is structural.  The
    # number is now stated so it can be argued with; it is REPORTED as the
    # module's worst relief claim rather than nudged.
    # R2-058: THIS READ `1.0 / Scale` AND WAS 3.183x TOO LONG.  Blender's Wave
    # multiplies the coordinate by 20 before the sine, so one band is
    # 2*pi/20 = 0.31416 of 1/Scale, not 1/Scale -- measured flat to six digits
    # over a Scale 5..230 sweep (itemkit WAVE_WAVELENGTH_FACTOR;
    # work/wavefix/emitted_wavelength.json).  itemkit's `_tex_wavelength_m` had
    # the same error, which is why this line and the audit agreed and both were
    # wrong.  THE DISTANCE ON THE SOCKET HAS NOT MOVED -- this is the depth the
    # module shipped and was judged at.  What moved is the DECLARATION: at the
    # true pitch the same amplitude is a much steeper wall, so the stage's real
    # modulation is m 8.871 and was being reported as m 7.652.  Do NOT
    # "correct" this by keeping the old modulation against the new wavelength:
    # that derives a Distance 3.183x shallower and changes a surface that was
    # rendered and looked at.
    LAM_MILL = K.WAVE_WAVELENGTH_FACTOR / (6.0 * 520.0)    # 0.10 mm (Wave)
    LAM_PIT = K.VORONOI_WAVELENGTH_FACTOR / 700.0          # 3.10 mm
    bmp = g.bump(h, 0.18, modulation_pp=8.871405, wavelength_m=LAM_MILL,
                 height_pp=0.30)
    HS._set(g, b, g.bump((pit, 0), 0.10, normal=bmp,
                         modulation_pp=0.730778, wavelength_m=LAM_PIT),
            "Normal")
    return m


def mat_elasto():
    """The elastomeric bearing pad: moulded neoprene, ozone-cracked at the
    edges, with the mould's own texture and a rim of squeezed-out dust."""
    m, g, b, _ = _new_mat("Elasto")
    base, aux, wear, bs, au, we, tc, uv, obj = HS._chan(g)
    edge = (au, 0)
    dirt, age = (we, 1), (wear, 3)
    mould = g.noise(g.vmath('MULTIPLY', obj, (260.0, 260.0, 260.0)), scale=2.0,
                    detail=6.0, rough=0.6)
    crack = g.voro(g.vmath('MULTIPLY', obj, (46.0, 46.0, 46.0)), scale=1.0,
                   rand=1.0, feature='DISTANCE_TO_EDGE')
    dust = g.voro(g.vmath('MULTIPLY', obj, (900.0, 900.0, 900.0)), scale=1.0,
                  rand=1.0, feature='SMOOTH_F1')
    bl = g.noise(g.vmath('MULTIPLY', obj, (12.0, 12.0, 12.0)), scale=2.0,
                 detail=6.0, rough=0.6)
    col = g.mix(g.math('MULTIPLY', bl, 0.5), (0.0130, 0.0132, 0.0138),
                (0.0215, 0.0218, 0.0225))
    ck = g.math('MULTIPLY', g.ramp((crack, 0), [(0.0, (1, 1, 1)),
                                                (0.020, (0, 0, 0))]),
                g.math('MULTIPLY', edge, g.math('ADD', 0.4,
                                                g.math('MULTIPLY', age, 0.9))),
                clamp=True)
    col = g.mix(g.math('MULTIPLY', (ck, 0), 0.75), col, (0.0055, 0.0055, 0.0058))
    col = g.mix(g.math('MULTIPLY', g.math('MULTIPLY', dirt, (dust, 0)), 0.55),
                col, (0.080, 0.072, 0.058))
    g._feed(b, 0, col)
    HS._set(g, b, 0.0, "Metallic")
    HS._set(g, b, g.math('ADD', 0.62, g.math('MULTIPLY', mould, 0.24)),
            "Roughness")
    # STATED AS RADIANCE MODULATION, NOT MILLIMETRES (itemkit 5b, brief 4a).
    # Both reproduce the shipped Distance; neither is a re-tune.
    #
    #   [0] mould skin    w 0.45  lam  3.08 mm  m 3.373  <- named, ungated
    #       ozone cracks  w 0.90  lam 47.17 mm  m 0.474  gated by aux.r x age,
    #                             and SUBTRACTED -- a crack is a groove
    #   [1] squeezed dust w 1.00  lam  2.41 mm  m 0.705  <- named (single
    #                             texture, so height_pp is 1.0)
    #
    # NOT RE-TUNED, AND WHY.  The mould skin is UNGATED and isotropic at 3.373,
    # which is over the isotropic bands and inside hard_feature -- the felt
    # shape.  A moulded neoprene pad does have a real mould-surface texture, but
    # 0.39 mm p-p on a 3.1 mm feature is a 22 deg surface and that is a casting
    # defect, not a skin.  It is left alone because the DEPTH IS SHARED with
    # the ozone cracks, which are the thing the eye is meant to find on this
    # part and which are already only m 0.47; cutting the stage to fix the skin
    # would erase them.  Reported.  This is the smallest, darkest surface on
    # the truss (base colour ~0.013) so it is also the cheapest to be wrong
    # about, which is why it is last on the list to fix.
    LAM_MOULD = K.NOISE_WAVELENGTH_FACTOR / (260.0 * 2.0)  # 3.08 mm
    LAM_DUST = K.VORONOI_WAVELENGTH_FACTOR / 900.0         # 2.41 mm
    bmp = g.bump(g.math('SUBTRACT', g.math('MULTIPLY', mould, 0.45),
                        g.math('MULTIPLY', (ck, 0), 0.9)), 0.35,
                 modulation_pp=3.37327, wavelength_m=LAM_MOULD, height_pp=0.45)
    HS._set(g, b, g.bump((dust, 0), 0.10, normal=bmp,
                         modulation_pp=0.70484, wavelength_m=LAM_DUST),
            "Normal")
    return m


def materials(force=False):
    """The five slots, in index order.  Idempotent."""
    global _MATS
    if _MATS is not None and not force:
        if all(m.name in bpy.data.materials for m in _MATS):
            return _MATS
    _MATS = [mat_paint(), mat_galv(), mat_fastener(), mat_machined(),
             mat_elasto()]
    return _MATS


# --------------------------------------------------------------------------- #
# 14.  THE INTERFACE FILE                                                       #
# --------------------------------------------------------------------------- #

def dump_interface(T, path=None):
    """Everything a dependant needs, as data, so it never has to import me."""
    R, t = gantry_to_world()
    out = {
        "item": "gantry_truss",
        "version": "1.0.0",
        "frame": {
            "note": "gantry-local == circuit design frame at the S/F line; "
                    "+X racing direction, +Y to the left (toward the pit "
                    "wall), +Z world up.  z is WORLD z in both frames.",
            "R_local_to_world": [[float(v) for v in row] for row in R],
            "t_local_to_world": [float(v) for v in t],
            "rot_deg_about_z": float(C.ROT_DEG),
        },
        "datum": {
            "soffit_z_at_bearings": SOFFIT_Z,
            "soffit_z_at_midspan": float(soffit_z(0.0)),
            "camber_m": CAMBER,
            "camber_formula": "SOFFIT_Z + CAMBER*(1-(y/11.0)^2) inside the "
                              "bearings; -TIP_SAG*t^2 on the cantilevers",
            "top_z": TOP_Z,
            "structural_depth_m": TRUSS_DEPTH,
            "lowest_point_z_measured": T.stats.get("lowest_z"),
            "chord_x": CHORD_X,
            "chord_section": "SHS 200x200x10, r_out 15 mm",
            "bearing_y": BEARING_Y,
            "end_y": END_Y,
            "panel_m": PANEL,
            "stations_y": [float(v) for v in STATIONS],
            "splice_y": [float(v) for v in SPLICE_Y],
        },
        "objects": [o.name for o in T.objects],
        "counts": {k: (float(v) if isinstance(v, float) else v)
                   for k, v in T.stats.items()},
        "walkway_edge_bays": [walkway_edge_spec(i, s)
                              for i in range(N_STA - 1) for s in (-1, 1)],
        "mounts": {},
    }
    for k, f in sorted(T.mounts.items()):
        out["mounts"][k] = {
            "o": [float(v) for v in f.o], "x": [float(v) for v in f.x],
            "y": [float(v) for v in f.y], "z": [float(v) for v in f.z],
            "r": float(f.r), "tag": f.tag,
        }
    p = path or os.path.join(HERE, "gantry_truss_interface.json")
    with open(p, "w") as fh:
        json.dump(out, fh, indent=1)
    print(">> interface written: %s  (%d mounts)" % (p, len(out["mounts"])))
    return p


# --------------------------------------------------------------------------- #
# 15.  THE TEST SCENE                                                           #
# --------------------------------------------------------------------------- #

def contract_light(scene=None):
    """The film's one sun, plus its sky.  Numbers from world_contract S13."""
    sc = scene or bpy.context.scene
    import fix_audit_blend as FA
    FA.procedural_world()
    sun = bpy.data.objects.get("GTR_Sun")
    if sun is None:
        d = bpy.data.lights.new("GTR_Sun", 'SUN')
        sun = bpy.data.objects.new("GTR_Sun", d)
        sc.collection.objects.link(sun)
    L = sun.data
    L.energy = C.SUN_ENERGY
    L.color = C.SUN_COLOR
    L.angle = math.radians(C.SUN_ANGULAR_DIAM_DEG)
    d = np.array(C.SUN_DIR, float)
    z = np.array([0.0, 0.0, 1.0])
    axis = np.cross(z, -d)
    ang = math.acos(float(np.clip(np.dot(z, -d), -1, 1)))
    if np.linalg.norm(axis) < 1e-9:
        axis = np.array([1.0, 0.0, 0.0])
    axis = axis / np.linalg.norm(axis)
    sun.rotation_mode = 'AXIS_ANGLE'
    sun.rotation_axis_angle = (ang, *axis)
    sun.location = (0.0, 0.0, 40.0)
    sc.view_settings.view_transform = C.VIEW_TRANSFORM
    sc.view_settings.look = C.VIEW_LOOK
    sc.view_settings.exposure = C.REFERENCE_EXPOSURE_EXTERIOR
    return sun


def context_ground(centre, size=90.0, name="CTX_Track"):
    """The pit straight under the gantry.  CONTEXT ONLY, prefixed CTX_ so the
    acceptance gate never counts it as this item.

    It is not decoration: the soffit of a gantry is lit almost entirely by
    light that bounced off the asphalt 9 m below it, and rendering the
    underside over a void would light it with sky alone and make every
    judgement about the material wrong.
    """
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    g = HS.NG(mat)
    out = g.n("ShaderNodeOutputMaterial")
    b = g.n("ShaderNodeBsdfPrincipled")
    g.lk(b, 0, out, 0)
    tc = g.n("ShaderNodeTexCoord")
    obj = g.vmath('MULTIPLY', (tc, 3), (1.0, 1.0, 1.0))
    n1 = g.noise(g.vmath('MULTIPLY', obj, (1.4, 1.4, 1.4)), scale=2.0,
                 detail=8.0, rough=0.6)
    agg = g.voro(g.vmath('MULTIPLY', obj, (150.0, 150.0, 150.0)), scale=1.0,
                 rand=1.0, feature='F1')
    aggc = g.sep((agg, 1))
    fine = g.voro(g.vmath('MULTIPLY', obj, (900.0, 900.0, 900.0)), scale=1.0,
                  rand=1.0, feature='SMOOTH_F1')
    col = g.mix(g.math('MULTIPLY', n1, 0.9), (0.0165, 0.0165, 0.0170),
                (0.0345, 0.0345, 0.0355))
    col = g.mix(g.math('MULTIPLY', (aggc, 0), 0.55), col, (0.048, 0.047, 0.045))
    col = g.mix(g.math('MULTIPLY', (fine, 0), 0.25), col, (0.058, 0.056, 0.052))
    g._feed(b, 0, col)
    g._feed(b, 2, g.math('SUBTRACT', 0.72, g.math('MULTIPLY', (fine, 0), 0.10)))
    bm = g.bump(g.math('ADD', g.math('MULTIPLY', (agg, 0), 0.5),
                       g.math('MULTIPLY', n1, 0.25)), 0.30, 0.004)
    # R2-070.  This was `g._feed(b, 5, ...)`, written when index 5 of
    # ShaderNodeBsdfPrincipled was `Normal`.  Blender 5.2's live order is
    #   [4] Alpha  [5] THIN WALL  [6] Normal  [7] Weight ...
    # so CTX_Track's relief chain went into `Thin Wall` and its Principled
    # BSDF shipped with `Normal` unconnected -- verified in
    # world/items/gantry_truss_test.blend, not inferred from the source.  The
    # material is opaque (Transmission Weight 0, Subsurface Weight 0, Alpha
    # 1.0, Coat Weight 0, all unlinked), so Thin Wall had nothing to switch
    # and this degenerated to "the context ground is flat".  Measured, not
    # assumed: a material carrying transmission would have been worse.
    #
    # The DSL is `marshal_post_column.NG` (imported as HS), repaired for
    # R2-057; its two importers -- this file and pont_girder.py -- were missed.
    # BY NAME, so the next socket insertion raises instead of sliding.
    g._feed_named(b, "Normal", g.bump((fine, 0), 0.14, 0.0009, normal=bm))
    n = 220
    xs = np.linspace(-size, size, n)
    ys = np.linspace(-size, size, n)
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    Z = 0.004 * np.sin(X * 0.9) * np.cos(Y * 0.7) - 0.0018 * np.cos(X * 2.3)
    V = np.stack([X, Y, Z], -1).reshape(-1, 3)
    idx = np.arange(n * n).reshape(n, n)
    F = np.stack([idx[:-1, :-1], idx[:-1, 1:], idx[1:, 1:], idx[1:, :-1]],
                 -1).reshape(-1, 4)
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in V], [], [tuple(f) for f in F])
    me.update()
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    ob.location = (float(centre[0]), float(centre[1]), float(centre[2]))
    bpy.context.scene.collection.objects.link(ob)
    return ob


def _chord_samples(place):
    """Dense samples of the four chord AXES, in the placed frame."""
    ys = np.linspace(-END_Y, END_Y, 900)
    P = []
    for level in (0, 1):
        for side in (-1, 1):
            P.append(chord_points(side, level, ys))
    P = np.concatenate(P, 0)
    if place is not None:
        R, t = place
        P = P @ np.asarray(R, float).T + np.asarray(t, float)[None, :]
    return P


def macro_camera(T, name="CAM_GTR_MACRO", dist=3.0, lens=35.0):
    """EXACTLY the manifest's shot: 3.0 m on a 35 mm lens, from UNDERNEATH.

    "THE CAMERA PASSES UNDER IT AT 3.0 m.  Every bolt cluster and node plate
    on the underside is on camera."  So the lens goes under the soffit, off to
    the track side, and looks up and along the span - which puts a node
    gusset, its bolt cluster and the bay-centre crossing plate in the near
    field and four more bays receding.  `dist` is solved so the NEAREST CHORD
    AXIS is exactly 3.000 m from the lens, which is the same convention
    marshal_post_column used and the stricter reading of the manifest: the
    nearest chord SURFACE is then 2.86 m and the pixel budget is 1300 px/m.
    """
    place = T.place
    S = _chord_samples(place)
    # aim: the bottom node gusset at mid-span on the track side
    # THE LENS GOES UNDER THE TRUSS, NOT BESIDE IT.  The first framing stood
    # off to one side at the same solved 3.000 m and produced a handsome
    # architectural portrait of the whole span - in which the underside, the
    # only part of this object the film ever shows, was edge-on and 8 m away.
    # The aim point is now the plan-bracing crossing plate in the bay next to
    # mid-span, and the lens is 2.9 m BELOW the soffit looking up along it, so
    # the near node gusset and its nuts, the crossing bolt pair, the transverse
    # tie, both service channels and four bays of receding soffit are in frame.
    aim_local = np.array([0.0, float(STATIONS[8]) + 0.55, BOT_AXIS_Z - 0.020])
    vdir_local = unit(np.array([-0.090, -0.455, -0.886]))
    look_local = np.array([0.26, 1.42, 0.46])
    if place is not None:
        Rm = np.asarray(place[0], float)
        aim = Rm @ aim_local + np.asarray(place[1], float)
        vdir = Rm @ vdir_local
        loff = Rm @ look_local
    else:
        aim, vdir, loff = aim_local, vdir_local, look_local

    def nearest(d):
        p = aim + vdir * d
        return p, float(np.min(np.linalg.norm(S - p[None, :], axis=1)))

    best = min(((abs(nearest(d)[1] - dist), d)
                for d in np.linspace(0.5, 9.0, 3401)))
    dused = float(best[1])
    pos, dmin = nearest(dused)
    look = aim + loff
    cam = bpy.data.cameras.get(name) or bpy.data.cameras.new(name)
    cam.lens = lens
    cam.sensor_width = SENSOR_MM
    cam.sensor_fit = 'HORIZONTAL'
    ob = bpy.data.objects.get(name)
    if ob is None:
        ob = bpy.data.objects.new(name, cam)
        bpy.context.scene.collection.objects.link(ob)
    ob.data = cam
    d = look - pos
    ob.location = tuple(float(v) for v in pos)
    from mathutils import Vector
    ob.rotation_mode = 'XYZ'
    ob.rotation_euler = Vector((float(d[0]), float(d[1]), float(d[2]))
                               ).to_track_quat('-Z', 'Y').to_euler()
    cam.dof.use_dof = True
    # f/11 focused a little past the aim: this frame exists to be pixel-peeped
    # over 4 receding bays, so the near bolt cluster AND the third node have to
    # be resolvable.  The film's own camera runs wider than this.
    cam.dof.focus_distance = float(np.linalg.norm(aim - pos)) + 0.85
    cam.dof.aperture_fstop = 11.0
    px = (3840.0 * lens / SENSOR_MM) / dmin
    print(">> macro camera %s: nearest chord AXIS %.4f m (manifest 3.0), "
          "%.0f mm lens" % (name, dmin, lens))
    print(">>   -> %.1f px/m on the 4K master, 1 px = %.3f mm"
          % (px, 1000.0 / px))
    print(">>   lens at z = %.3f, soffit at z = %.3f, aim %.3f m away"
          % (pos[2], SOFFIT_Z, float(np.linalg.norm(aim - pos))))
    return ob, dmin


def inspect_camera(T, name, target_local, eye_local, lens):
    """A close inspection camera on ONE detail.

    Not the deliverable - the macro is - but the two details this item is most
    likely to have got wrong are the ones no wide shot can adjudicate: the
    punched galvanising drain holes (a hand-written hole through a swept
    surface, which is either a hole or a hole-shaped crater) and the bearing
    seat that gantry_leg has to land on.  They ship as cameras so the next
    agent can re-check them without rebuilding anything.
    """
    place = T.place
    if place is not None:
        Rm = np.asarray(place[0], float)
        tt = np.asarray(place[1], float)
        tgt = Rm @ np.asarray(target_local, float) + tt
        eye = Rm @ np.asarray(eye_local, float) + tt
    else:
        tgt = np.asarray(target_local, float)
        eye = np.asarray(eye_local, float)
    cam = bpy.data.cameras.get(name) or bpy.data.cameras.new(name)
    cam.lens = lens
    cam.sensor_width = SENSOR_MM
    cam.sensor_fit = 'HORIZONTAL'
    ob = bpy.data.objects.get(name)
    if ob is None:
        ob = bpy.data.objects.new(name, cam)
        bpy.context.scene.collection.objects.link(ob)
    ob.data = cam
    d = tgt - eye
    ob.location = tuple(float(v) for v in eye)
    from mathutils import Vector
    ob.rotation_mode = 'XYZ'
    ob.rotation_euler = Vector((float(d[0]), float(d[1]), float(d[2]))
                               ).to_track_quat('-Z', 'Y').to_euler()
    cam.dof.use_dof = False
    print(">> inspection camera %s at %.3f m, %.0f mm"
          % (name, float(np.linalg.norm(d)), lens))
    return ob


def test_scene(out=None, samples=256, res=(1920, 1080), quality=1.0):
    """The acceptance scene: the truss where it really stands, the contract
    sun, the asphalt that lights its underside, and one camera at the
    manifest's own distance and lens."""
    sc = bpy.context.scene
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    place = gantry_to_world()
    T = build(place=place, res=quality)
    contract_light(sc)
    R, t = place
    context_ground((float(t[0]), float(t[1]), 0.0), 90.0)
    cam, dmin = macro_camera(T)
    # the two details the macro cannot adjudicate
    inspect_camera(T, "CAM_GTR_DRAIN",
                   (-CHORD_X, 0.02, SOFFIT_Z - 0.005),
                   (-CHORD_X + 0.03, -0.34, SOFFIT_Z - 0.50), 58.0)
    inspect_camera(T, "CAM_GTR_BEARING",
                   (-CHORD_X, -BEARING_Y, SOFFIT_Z - 0.045),
                   (-CHORD_X - 0.95, -BEARING_Y - 1.30, SOFFIT_Z - 1.05), 35.0)
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
    T.meta["nearest_chord_axis_m"] = dmin
    dump_interface(T)
    print(">> VARIATION, measured on what was actually emitted:")
    print("   node gusset plates      %3d built, %3d distinct shapes"
          % (T.stats["node_plates"], T.stats["distinct_node_plate_shapes"]))
    print("   bolts                   %3d built, %3d distinct geometries"
          % (T.stats["bolts"], T.stats["distinct_bolt_geometries"]))
    print("   walkway edge bays       %3d kinds across the two sides"
          % T.stats["distinct_walkway_edge_bays"])
    print("   lowest point of the item   z = %.4f (soffit datum %.3f)"
          % (T.stats["lowest_z"], SOFFIT_Z))
    if out:
        import fix_audit_blend as FA
        FA.save_clean(out)
    return T, cam


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
        T = build(place=None, res=opt("--quality", 1.0, float))
        contract_light()
        dump_interface(T)
        if "--out" in a:
            import fix_audit_blend as FA
            FA.save_clean(opt("--out"))
    else:
        print(__doc__)


if __name__ == "__main__":
    _cli()
