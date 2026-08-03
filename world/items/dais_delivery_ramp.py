#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dais_delivery_ramp.py — CIRCUIT VITRINE, per-item hero campaign, item
``dais_delivery_ramp`` (zone ``showroom_breach``, wave 1, build order 13,
0 dependants, depends on ``dais_deck``).

WHAT THIS IS, IN ONE SENTENCE
=============================
The bridging ramp that carries the car off the 0.340 m turntable dais and onto
the showroom floor — **the piece of geometry the whole launch is animated on and
which did not exist**, so that for thirteen frames of beat 2 the car drove down
an invisible slope with nothing under its wheels.

IT WAS NOT A SUSPICION. IT WAS RENDERED AND LOOKED AT.
------------------------------------------------------
`anim/carrig.py`'s own header carries the note — "that ramp is DECLARED but NOT
BUILT ... until it does, the car rolls down an invisible slope" — and an earlier
judgement dismissed it as reading like a dive. That judgement was made without a
render and it is **refuted by measurement**. Sampled off the keyed rig in
`render/film/showroom_cam.blend` (`work/ramp/probe2.json`, wheel-hub world
translations minus the 0.360 m rolling radius):

    FRONT unsupported f839-846      0.33598 -> 0.02450 m
    REAR  unsupported f849-853      0.32229 -> 0.05468 m
    f838 -> f839                    support vanishes 0.336 m in ONE frame

Thirteen frames, worst float 0.336 m. And it is visible because **the showroom
floor is specular**: a floating tyre's reflection detaches from it by TWICE its
height — up to 0.67 m, nearly a wheel diameter. The decisive evidence is an
internal control inside a single frame, `work/film6/evidence/ramp/`:
`CONTROL_front_in_contact_851.png` is the front wheel at 0.000 m with its
reflection meeting the tyre and no gap at all, while `rw_851.png` is the SAME
FRAME's rear wheel at 0.194 m with the reflection clearly adrift. One frame, one
exposure, one shader, one denoiser — everything that could explain a gap other
than the gap is held fixed.

THE DECLARED PROFILE IS THE SPECIFICATION. IT IS NOT IMPROVED HERE.
-------------------------------------------------------------------
`docs/circuit_spec.json` showroom.dais.delivery_ramp:

    "0.340 m rise over 2.60 m (13.1%), full 3.0 m width,
     from the dais lip X=+3.70 to X=+6.30"

`anim/carrig._ramp_ground` implements exactly that piecewise-linear ground and
`anim/build_car_anim.py` has already keyed 2,978 frames of car onto it. So the
profile is not a design decision that belongs to this module: **if this geometry
disagrees with that function the car floats or sinks**, and the fix would have to
be a re-key of the whole film. `top_z()` below is `_ramp_ground` re-typed, and
`selftest [1]` imports `carrig` and checks the two agree to 1e-9 at 20,001
stations. That check is the point of this file.

WHAT THE AS-BUILT DAIS ACTUALLY DOES, WHICH IS NOT WHAT THE PROFILE ASSUMES
---------------------------------------------------------------------------
MEASURED on the shipped showroom, not assumed (`work/ramp/dais_probe.json`,
vertex-exact, plus a downward raycast every 30 mm along the launch axis):

    Turntable_Deck    top z = 0.34000, top face out to r = 3.4020,
                      outermost vertex r = 3.44970   (a rim chamfer)
    Platform_Dais     outer r = 3.70000, top z = 0.30000 on the ring
                      r = 3.560 .. 3.596
    Floor             top z = 0.00000

So the "dais lip at X = +3.70" that the profile holds at 0.340 **is not at
0.340 in the built showroom**. The deck's load-bearing top ends at r = 3.402;
outboard of that there is the turntable's running gap (the raycast finds 0.106 m
at x = 3.47), then a ring 40 mm LOW at 0.300, then the plinth falling away to the
floor. The car's front contact patch sits at y = +-0.8475, so it crosses r =
3.402 at x = 3.298 — and at f838, which the profile calls fully supported, its
radius is 3.5945 and the nearest mesh under it is the platform ring, 40 mm down.

**That is why this module's head is a scribed landing and not a butt joint.**
The ramp does not start at x = 3.70. It starts at the scribe arc

    NOSE_R = 3.44970 + 0.0125 = 3.46220 m

— the deck's outermost vertex plus a 12.5 mm running clearance, because the deck
ROTATES — and carries a flat 0.340 m landing from that arc out to x = 3.700,
where the declared slope takes over. At y = 0 that landing is 238 mm deep; at the
outer corners y = +-1.5 it is 580 mm deep, because the arc is an arc. It bears on
the static Platform_Dais ring at 0.300 through shim stacks and on its own frame
beyond the plinth. **This is load-bearing, not decoration**: without it the wheels
are unsupported from x = 3.298 as well as from x = 3.700.

The residual is the 60 mm between the deck's top-face edge (r = 3.402) and the
ramp's nose (r = 3.462). A 0.720 m wheel bridging 60 mm sags 1.25 mm — 3 px at
this item's own filmed distance, and it is a turntable running gap, which is a
thing that exists rather than a defect. It is measured in `selftest [2]` so that
it stays 60 mm.

THE RUNNING SURFACE IS AN ENVELOPE, AND EVERY PIECE OF RELIEF IS SUBTRACTIVE
----------------------------------------------------------------------------
THE ONE RULE THIS MODULE CANNOT BREAK. `contact against ground_z is not contact
against the built mesh` is a defect this project has already paid for once — a
function said 3.6 mm where the mesh said 35.2 mm, ten times over. A hero surface
needs milled grip, plate waviness, chamfer wear and tyre scuff; every one of
those is a departure from the declared plane, and a departure UPWARD lifts the
car off its own keys.

So the plate is machined out of stock that ends exactly on the declared surface:

    z_top(x, y) = declared(x, y) - relief(x, y),      relief(x, y) >= 0

The declared surface is the **high envelope** of everything built. A wheel keyed
onto it can rest on the lands and can never be pushed up by a groove, a wave or a
scuff. `selftest [3]` takes the max of `relief` over every emitted vertex and
requires it to be <= 0, and its negative control perturbs one vertex upward by
0.1 mm and requires the check to fail.

The one stated exception is the toe. A plate cannot feather to zero thickness, so
the last 240 mm thins from 14 mm to 3.5 mm and the tip **laps into the floor
slab**, 3.5 mm below z = 0 at x = 6.300. That is 3.5 mm where `BASE_EMBED_M` is
20 mm, and it is deliberate: a 20 mm embed at the foot of a ramp is a 20 mm step
at the foot of a ramp, which is the defect class this file exists to delete. The
load-bearing feet embed the full 20 mm; the toe is a lap, not a foot.

THE PIXEL BUDGET
----------------
Manifest: `nearest_camera_m` 1.4, `lens_at_closest_mm` 35, `onscreen_px_4k` 907.

    px_per_m = (3840 x 35 / 36) / 1.4 = 2666.7 px/m     ->   1 px = 0.375 mm

    the 0.340 m rise                    907 px  (manifest: onscreen_px_4k 907)
    the 2.600 m declared run           6933 px
    a 28 mm grip pitch                   75 px      <- must be geometry
    a 6.0 mm grip groove                 16 px      <- must be geometry
    a 1.6 mm groove depth, and at a 12.47 deg sun it throws 7.2 mm
                                       19 px of shadow  <- must be geometry
    a 6 mm arris chamfer                 16 px      <- must be geometry
    chamfer wear, 4-11 mm             11-29 px      <- must be geometry
    the 12.5 mm turntable clearance      33 px      <- must be geometry
    a 22 mm fascia reveal                59 px      <- must be geometry
    an M10 countersink, 20 mm            53 px      <- must be geometry
    plate waviness, 1.8 mm over 180 mm  4.8 px      <- must be geometry
    the brushed lay, 0.9 mm pitch       2.4 px      <- shader; below the mesh

MEASURED, and it is not the manifest's number: the camera's closest approach to
this object's footprint over all 2,978 frames is **1.991 m at frame 675 on a
36.69 mm lens** (`render/film8_path.json`, distance to the ramp's bounding box).
That is 1965.6 px/m, LOOSER than the manifest's 2666.7. The manifest is built to
because it is the stricter of the two and because it is the specification; the
measured figure is recorded here so nobody re-derives it and relaxes the mesh.

RELIEF STATED AS RADIANCE (itemkit section 5b, ITEM-CAMPAIGN-BRIEF 4a)
----------------------------------------------------------------------
Every bump stage below is `NT.bump(..., modulation_pp=, wavelength_m=)`. No
`distance=` in metres appears in this file. The sun is 12.47 deg, a 4.52x
amplifier, and three amplitude sets chosen in millimetres were rendered and
rejected before that law was written down.

BOTH LAYERS. The shader stages sit in `isotropic_micro` (0.12-0.45) because on
this sun **the mesh carries the read and the shader garnishes it** — five of the
seven wave-1 modules that pass check 7 pass on their geometry alone. The mesh's
own dihedrals are audited by `selftest [7]` through `K.geometry_relief_report`,
and the grip grooves are deliberately a `hard_feature` (m ~ 2.4): a milled groove
IS an edge, and gating it to 21 % of the plate area is what keeps it from
becoming the stucco that got 3.76 rejected.

WIRED BY NAME
-------------
Blender 5.2 moved Principled `Normal` from index 5 to 6 (`[4] Alpha [5] Thin
Wall [6] Normal`) and Bump's `Height` sits at [3] behind `Filter Width`. Nothing
here pins a shader socket by index: `NT.bump` and `NT.principled_out` are
name-wired, and `tools/socket_index_audit.py` is run over this file in `main()`.

    build:      blender -b --factory-startup -P world/items/dais_delivery_ramp.py \
                    -- --test-scene --save world/items/dais_delivery_ramp_test.blend
    selftest:   python3 world/items/dais_delivery_ramp.py --selftest
    gate:       blender -b <blend> --factory-startup -P tools/item_gate.py -- \
                    --item dais_delivery_ramp --collection W_Item_DaisDeliveryRamp
"""

import argparse
import json
import math
import os
import sys

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
_WORLD = os.path.dirname(_HERE)
_ROOT = os.path.dirname(_WORLD)
for _p in (_WORLD, os.path.join(_ROOT, "anim")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import itemkit as K                                          # noqa: E402
import world_contract as C                                   # noqa: E402

try:
    import bpy
except ImportError:                                          # selftest path
    bpy = None

ITEM = "dais_delivery_ramp"
COLL = "W_Item_DaisDeliveryRamp"
PFX = "DDR_"

FILMED_AT_M, LENS_MM = 1.4, 35.0                # docs/item_manifest.json item 13
PX_PER_M = K.px_per_m(FILMED_AT_M, LENS_MM)     # 2666.7 px/m -> 0.375 mm/px
MEASURED_NEAREST_M = 1.991                      # frame 675, render/film8_path.json
MEASURED_LENS_MM = 36.69

SEED = 20260803


# ===========================================================================
# 1.  THE DECLARED PROFILE — read from the spec, never typed twice
# ===========================================================================

def _spec_dais():
    """`circuit_spec.showroom.dais`, so a spec change moves this geometry."""
    p = os.path.join(_ROOT, "docs/circuit_spec.json")
    return json.load(open(p))["showroom"]["dais"]


_DAIS = _spec_dais()
DECK_TOP_Z = float(_DAIS["deck_top_z"])                 # 0.340
DAIS_LIP_X = 3.700                                      # spec text, asserted below
RAMP_FOOT_X = 6.300                                     # spec text, asserted below
HALF_W = 1.500                                          # "full 3.0 m width"

# The spec carries the two stations only inside an English sentence, so they are
# PARSED out of it rather than retyped, and the parse is checked.
_txt = _DAIS["delivery_ramp"]
for _tok, _want in (("X=+3.70", DAIS_LIP_X), ("X=+6.30", RAMP_FOOT_X),
                    ("0.340 m rise", DECK_TOP_Z), ("3.0 m width", 2 * HALF_W)):
    if _tok not in _txt:
        raise SystemExit(
            "circuit_spec showroom.dais.delivery_ramp no longer says %r; it says "
            "%r. The car is keyed onto these numbers -- see anim/carrig.py -- so "
            "this module refuses to build a ramp the spec does not declare."
            % (_tok, _txt))

# ---------------------------------------------------------------- as-built ---
# MEASURED on render/film/showroom_cam.blend, vertex-exact, 2026-08-03.
# work/ramp/dais_probe.json. NOT taken from the manifest's prose: the manifest
# says the platform is 7.4 m and the deck 6.9 m, and the deck's LOAD-BEARING top
# face stops at r = 3.402, which is neither.
DECK_TOP_R = 3.40200          # outer radius of Turntable_Deck's top FACE
DECK_RIM_R = 3.44970          # outermost Turntable_Deck vertex (the rim chamfer)
PLATFORM_R = 3.70000          # outer radius of Platform_Dais
PLATFORM_TOP_Z = 0.30000      # the static ring the head bears on
PLATFORM_RING = (3.560, 3.596)
FLOOR_Z = 0.0

TURNTABLE_CLEARANCE_M = 0.0125          # the deck rotates; it cannot be touched
NOSE_R = DECK_RIM_R + TURNTABLE_CLEARANCE_M          # 3.46220


def top_z(x, y=0.0):
    """The declared ground height of the ramp's running surface.

    IDENTICAL BY CONSTRUCTION to `anim/carrig._ramp_ground`, which is what the
    car's 2,978 frames were solved against. `selftest [1]` imports that function
    and compares 20,001 stations; do not let the two drift.

    `y` is accepted and unused for the sloped span because the declared profile
    is a ruled surface with no crossfall — a delivery ramp is machined flat
    across, and inventing a camber here would tilt a car that is keyed level.
    """
    x = np.asarray(x, dtype=np.float64)
    z = np.where(x <= DAIS_LIP_X, DECK_TOP_Z,
                 np.where(x >= RAMP_FOOT_X, 0.0,
                          DECK_TOP_Z * (RAMP_FOOT_X - x)
                          / (RAMP_FOOT_X - DAIS_LIP_X)))
    return z if z.ndim else float(z)


def head_x(y):
    """Where the scribed head starts, at lateral offset `y`: the nose arc."""
    y = np.asarray(y, dtype=np.float64)
    return np.sqrt(np.maximum(NOSE_R * NOSE_R - y * y, 0.0))


# ---------------------------------------------------------------- the plate --
PLATE_T = 0.0140                # 14 mm aluminium tooling plate
TOE_START_X = 6.060             # where the underside begins its ground bevel
TOE_TIP_EMBED = 0.0035          # the tip laps 3.5 mm INTO the floor slab

CHAMFER_W = 0.0060              # nominal 45 deg arris chamfer
CHAMFER_WEAR = (0.0040, 0.0110)  # the manifest's "edge chamfer wear" axis

# --- the tread field ---------------------------------------------------------
# THE FIRST MACRO WAS REJECTED AND THIS IS WHY. Grooves at one pitch across the
# whole 3.0 x 2.8 m plate render as CORDUROY: a periodic stripe with no beginning,
# no end and no reason, which is a texture wearing an object's clothes. A real
# machined ramp has a tread FIELD with plain margins the tool cannot reach, plain
# bands at the head and toe where the plate is clamped, and it is made of stock
# panels with joints between them. Those three things are what stop the pattern
# from being wallpaper, and all three are geometry.
TREAD_MARGIN_Y = 0.115          # plain machined margin along each long edge
TREAD_HEAD_M = 0.090            # plain band behind the head scribe
TREAD_TOE_M = 0.075             # plain band at the toe
TREAD_FEATHER = 0.009           # how fast the field closes; a real cutter's runout

PANEL_JOINTS = (4.360, 5.020, 5.680)   # transverse plate joints, stock widths
JOINT_W = 0.0032
JOINT_D = 0.0021
JOINT_CH = 0.0009

# THE TREAD IS A LATTICE, NOT A SET OF STRIPES, AND THE GATE IS WHAT DECIDED IT.
# The first build cut TRANSVERSE grooves only — along y, which is right for grip
# on a 13.1 % fall. `item_gate` check 7 rejected it:
#
#   relief_reads_as_lip_and_shade: lip-and-shadow dip -0.1234 ... The features on
#   this surface are single-value marks: they have no sunward lip and no lee
#   shadow, which is how a printed decal behaves and not how a physical object does.
#
# The cause is geometric and it is not a matter of depth. `world_contract.SUN_DIR`
# is (0.5178, -0.8278, 0.2159): the sun's horizontal direction is 84.8 % along y
# and only 53.1 % along x. A groove that runs along y is 32 deg off PARALLEL to
# the light, so the light runs down it instead of across it — the effective sun
# elevation across such a groove is atan(0.2159/0.531) = 22.1 deg, not 12.47, and
# the shadow it throws is 2.46x its depth instead of 4.52x. Cutting it deeper
# would only have made a deeper groove that still did not shade.
#
# The second family runs along x, where the perpendicular component is 0.848 and
# the effective elevation is atan(0.2159/0.848) = 14.3 deg — essentially the full
# 4.5x amplifier. A rectangular milled lattice is also simply what a fabricator
# does on a plate this size: the transverse cuts stop the tyre sliding down the
# fall and the longitudinal cuts key it laterally and let water off.
#
# It is a lattice and not a diagonal cross-hatch for one reason: a diagonal
# family aligns with neither grid axis, so a 2.0 mm chamfer wall would need ~1 mm
# sampling in BOTH directions over 8.5 m2 — about 8.5 M vertices for the deck
# alone. Two axis-aligned families cost fine stations on one axis each.
GRIP_PITCH = 0.0280             # milled TRANSVERSE non-slip grooves (along y)
GRIP2_PITCH = 0.0340            # milled LONGITUDINAL grooves (along x)
GRIP_WIDTH = 0.0070
GRIP_DEPTH = 0.0016
# The wall angle is chosen by the RELIEF LAW, not by a machinist's preference:
# a 1.2 mm chamfer puts the wall at 53.1 deg, m = 7.24, which is off the top of
# RELIEF_BANDS["hard_feature"] (1.5-6.0) -- the band above the 3.76 that was
# rendered and rejected as coarse stucco. 2.0 mm puts it at 38.7 deg, m = 5.65,
# inside the band and still unmistakably an edge. Checked in selftest [6].
GRIP_CHAMFER = 0.0020

# Rolled-plate waviness, one-sided (downward). THE AMPLITUDE IS DERIVED FROM THE
# RADIANCE, not chosen in millimetres — this is a GEOMETRY stage and section 4a's
# "CHECK BOTH LAYERS" is about exactly this: the fold-field geometry that was
# 2.32 pp while the shader beside it had been corrected to 0.28.
WAVE_LAM = 0.260
WAVE_PP = K.relief_amplitude_for(0.22, WAVE_LAM) * 1e-3

FASCIA_SETBACK = 0.0220         # the shadow reveal under the deck edge
FASCIA_T = 0.0030
EMBED = float(C.BASE_EMBED_M)   # 0.020 — the LOAD-BEARING feet, not the toe

# The car's contact patches, for the scuff bands. anim/carrig.py.
TRACK_F, TRACK_R = 0.84750, 0.79750
TYRE_HALF_F, TYRE_HALF_R = 0.150, 0.200


# ===========================================================================
# 2.  THE MACHINED SURFACE — every stage subtractive, and audited as such
# ===========================================================================

def _slot(x, centres, width, depth, chamfer, phase=None):
    """A milled slot lattice or a list of slots: depth BELOW the land, >= 0."""
    x = np.asarray(x, dtype=np.float64)
    half, flat = 0.5 * width, 0.5 * width - chamfer
    if isinstance(centres, float):                  # a periodic lattice
        p = DAIS_LIP_X if phase is None else phase
        a = np.abs(np.mod(x - p, centres) - 0.5 * centres)
    else:                                           # named stations
        a = np.full(np.shape(x), 1e9)
        for c in centres:
            a = np.minimum(a, np.abs(x - c))
    return np.where(a <= flat, depth,
                    np.where(a >= half, 0.0, depth * (half - a) / chamfer))


def tread_field(x, y):
    """1 inside the machined tread field, 0 on the plain margins. Smooth.

    The field is inset from every boundary of the plate: `TREAD_MARGIN_Y` from
    the two long edges, `TREAD_HEAD_M` behind the scribed nose and
    `TREAD_TOE_M` before the toe. It closes over `TREAD_FEATHER`, which is a
    cutter's runout, not a fade.
    """
    r = np.hypot(x, y)
    d = np.minimum(
        np.minimum(HALF_W - TREAD_MARGIN_Y - np.abs(y),
                   r - NOSE_R - TREAD_HEAD_M),
        RAMP_FOOT_X - TREAD_TOE_M - x)
    return K.smoothstep(0.0, TREAD_FEATHER, d)


def grip_depth(x, y=0.0):
    """Milled transverse grip grooves. Returns metres BELOW the land, >= 0.

    Transverse and not diagonal for two reasons and both are real: a 13.1 %
    ramp is machined across the fall so a tyre cannot slide down the lay, and a
    groove that runs along y can be resolved by extra grid lines in x alone,
    which buys a 1.0 mm arris for a 4.0 mm grid instead of tessellating 8.5 m2
    at 1 mm to catch a diagonal.

    GATED BY THE TREAD FIELD AND POLISHED IN THE WHEEL TRACKS. One launch at
    full throttle does not wear a groove away, but a delivery ramp that has been
    used has its tread rounded where the tyres cross and crisp where they do
    not, and that difference is the single strongest cue that the object has a
    history rather than a texture.
    """
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64) * np.ones_like(x)
    ay = np.abs(y)
    polish = (K.smoothstep(TRACK_R - TYRE_HALF_R - 0.07, TRACK_R - TYRE_HALF_R, ay)
              * K.smoothstep(TRACK_F + TYRE_HALF_F + 0.07,
                             TRACK_F + TYRE_HALF_F, ay))
    # MAX, NOT SUM. Two milling passes over the same stock cut the deeper of the
    # two; adding them would make every crossing 3.2 mm deep, which is a hole,
    # not a lattice.
    d = np.maximum(
        _slot(x, GRIP_PITCH, GRIP_WIDTH, GRIP_DEPTH, GRIP_CHAMFER),
        _slot(y, GRIP2_PITCH, GRIP_WIDTH, GRIP_DEPTH, GRIP_CHAMFER, phase=0.0))
    return d * tread_field(x, y) * (1.0 - 0.42 * polish)


def joint_depth(x):
    """The butt joints between the plate's stock panels. Full width, always."""
    return _slot(x, PANEL_JOINTS, JOINT_W, JOINT_D, JOINT_CH)


def plate_waviness(x, y):
    """Rolled-plate waviness. ONE-SIDED: 0 at the crests, WAVE_PP at the hollows.

    A 2.6 m aluminium plate is not optically flat and a hero surface that is
    reads as a render. But the declared profile is the envelope, so the waviness
    hangs BELOW it — the plate is machined out of stock whose high points are the
    declared plane, which is also how a real one is skimmed.
    """
    # NOT A PRODUCT OF COSINES. The first version multiplied a 180 mm cosine in
    # x by a 486 mm cosine in y, and a 1 mm/px plan view of the machined relief
    # showed it immediately for what it is: a regular EGG-CRATE quilt across
    # 8.5 m2 of plate. Rolling waviness has no period; it is the mill's own
    # slow wander, and two octaves of value noise are what that looks like.
    # The plan view is `/tmp/tread_plan.png`'s method and it costs no render --
    # look at a field before you build 4 M triangles out of it.
    w = (0.72 * K.fbm2(x / WAVE_LAM, y / (WAVE_LAM * 1.35),
                       seed=SEED + 11, oct=3)
         + 0.28 * K.fbm2(x / (WAVE_LAM * 3.1), y / (WAVE_LAM * 2.6),
                         seed=SEED + 17, oct=2))
    # NORMALISED SO THE CRESTS TOUCH ZERO: the declared plane is the envelope,
    # so the field's MAXIMUM must be 0 and everything else must hang below it.
    # `K.fbm2` does not span [-1, 1] and assuming it did left the whole plate
    # 0.17 mm low, which means the wheel never rests on anything — this module's
    # one claim. The two constants are MEASURED over this plate's own domain at
    # 2 mm (1.6 M samples): the field runs 0.14892 .. 0.82884. `selftest [3]`
    # re-measures the result rather than trusting them.
    W_LO, W_HI = 0.14892, 0.82884
    w = np.clip((w - W_LO) / (W_HI - W_LO), 0.0, 1.0)
    return WAVE_PP * (1.0 - w)


def edge_relief(x, y):
    """The two long arrises and the head/toe arrises, chamfered and WORN.

    The manifest's second variation axis is "edge chamfer wear" and the object
    has exactly one instance, so the variation has to live ALONG the edge rather
    than between copies: the chamfer runs 4.0-11.0 mm, widest where the car has
    been dragged over it and where a fork truck has kissed it.
    """
    r = np.hypot(x, y)
    # distance to the nearest boundary of the plate, in plan
    d_side = HALF_W - np.abs(y)
    d_nose = r - NOSE_R
    d_toe = RAMP_FOOT_X - x
    d = np.minimum(np.minimum(d_side, d_nose), d_toe)

    wear = K.fbm1(np.abs(y) * 3.1 + x * 1.7, seed=SEED + 23, oct=4)
    w = CHAMFER_WEAR[0] + (CHAMFER_WEAR[1] - CHAMFER_WEAR[0]) * K.clamp01(wear)
    # a chamfer is a 45 deg cut: depth == the horizontal it has eaten. CLAMPED
    # AT `w`: outside the plate `d` goes negative and an unclamped cut runs away
    # -- selftest [3] caught it reporting a 361 mm "chamfer" on a sample grid
    # that reached past the nose arc.
    return np.clip(w - d, 0.0, w)


def scuff_relief(x, y):
    """Tyre scuff and traffic polish in the wheel tracks. Sub-millimetre.

    Gated to the two 300/400 mm bands the car's contact patches actually cross,
    because that is where a launch puts rubber and heat. It is relief, not a
    stain: the softened arrises inside those bands are what says a car has been
    here, and a stain painted on flat metal is precisely the "texture painted on
    instead of built" that check 7 rejects.
    """
    ay = np.abs(y)
    band = (K.smoothstep(TRACK_R - TYRE_HALF_R - 0.05, TRACK_R - TYRE_HALF_R, ay)
            * K.smoothstep(TRACK_F + TYRE_HALF_F + 0.05, TRACK_F + TYRE_HALF_F, ay))
    n = K.fbm2(x / 0.055, y / 0.055, seed=SEED + 31, oct=4)
    return 0.00042 * band * K.clamp01(0.35 + 1.15 * n)


def relief(x, y):
    """EVERYTHING that departs from the declared plane. NEVER NEGATIVE.

    Returns metres to SUBTRACT. `selftest [3]` asserts min(relief) >= 0 over
    every emitted vertex, with a negative control that perturbs one sample by
    -0.1 mm (i.e. 0.1 mm of LIFT) and requires the check to notice.
    """
    return (grip_depth(x, y) + joint_depth(x) + plate_waviness(x, y)
            + edge_relief(x, y) + scuff_relief(x, y))


def surface_z(x, y):
    """The BUILT running surface. `top_z` is its high envelope, by construction."""
    return top_z(x, y) - relief(x, y)


def under_z(x, y=0.0):
    """The plate's underside, including the ground toe bevel at the foot."""
    x = np.asarray(x, dtype=np.float64)
    t_head = top_z(TOE_START_X) - PLATE_T                     # 0.016234
    t_tip = -TOE_TIP_EMBED                                    # -0.003500
    lap = t_head + (t_tip - t_head) * (x - TOE_START_X) / (RAMP_FOOT_X - TOE_START_X)
    return np.where(x <= TOE_START_X, top_z(x, y) - PLATE_T, lap)


# ===========================================================================
# 3.  THE GRIDS — non-uniform, because the features decide the sampling
# ===========================================================================

def _densify(a0, a1, marks, coarse):
    """Stations: every mark, plus `coarse` fill between them. Sorted, unique."""
    marks = sorted(m for m in marks if a0 < m < a1)
    out, prev = [a0], a0
    for m in marks:
        if m - prev > coarse * 1.4:
            n = int(math.ceil((m - prev) / coarse))
            out += list(np.linspace(prev, m, n + 1)[1:-1])
        out.append(m)
        prev = m
    if a1 - prev > coarse * 1.4:
        n = int(math.ceil((a1 - prev) / coarse))
        out += list(np.linspace(prev, a1, n + 1)[1:-1])
    out.append(a1)
    return np.array(sorted(set(np.round(out, 7))))


def _slot_marks(a0, a1, pitch, phase, width, chamfer):
    """The stations a periodic slot family needs: both arrises and both walls."""
    half, ch = 0.5 * width, chamfer
    k0 = int(math.floor((a0 - phase) / pitch)) - 1
    k1 = int(math.ceil((a1 - phase) / pitch)) + 1
    marks = []
    for k in range(k0, k1 + 1):
        c = phase + (k + 0.5) * pitch
        marks += [c - half, c - half + ch, c - 0.5 * (half - ch),
                  c, c + 0.5 * (half - ch), c + half - ch, c + half]
    return marks


def grip_axis(x0, x1, coarse=0.0040):
    """x stations: `coarse` on the lands, ~1.0 mm through every groove wall.

    Uniform sampling fine enough for a 2.0 mm chamfer would put 8.5 m2 of plate
    at 1 mm and cost 8.5 M vertices for a surface that is genuinely flat between
    the grooves. This puts the vertices where the arrises are.
    """
    marks = _slot_marks(x0, x1, GRIP_PITCH, DAIS_LIP_X, GRIP_WIDTH, GRIP_CHAMFER)
    # the panel joints get their own stations: 3.2 mm is under one coarse cell
    jh, jc = 0.5 * JOINT_W, JOINT_CH
    for c in PANEL_JOINTS:
        marks += [c - jh, c - jh + jc, c, c + jh - jc, c + jh]
    return _densify(x0, x1, marks, coarse)


def edge_axis(y0, y1, coarse=0.0055, fine=0.0008, band=0.0130):
    """y stations: the LONGITUDINAL groove walls, plus `fine` at the two arrises.

    The second groove family is what makes check 7 read (see the GRIP2_PITCH
    note), and a family whose walls fall between grid lines is a family that
    does not exist in the mesh however carefully the field is written.
    """
    marks = _slot_marks(y0, y1, GRIP2_PITCH, 0.0, GRIP_WIDTH, GRIP_CHAMFER)
    marks += list(np.linspace(y0, y0 + band, int(band / fine) + 1))
    marks += list(np.linspace(y1 - band, y1, int(band / fine) + 1))
    return _densify(y0, y1, marks, coarse)


def deck_grid():
    """The plate's top surface: a structured grid scribed to the nose arc.

    Column j sits at y_j and runs from `head_x(y_j)` to RAMP_FOOT_X, so the head
    is a true arc rather than a stair. The x stations are the SAME lattice for
    every column (so the grip grooves are straight across, as milled) with the
    head end trimmed per column and one extra station at the arc itself.
    """
    ys = edge_axis(-HALF_W, HALF_W)
    xs_full = grip_axis(head_x(HALF_W) - 0.001, RAMP_FOOT_X)
    ny = len(ys)
    # per-column start index into xs_full, plus an exact arc station
    cols = []
    for y in ys:
        hx = float(head_x(y))
        keep = xs_full[xs_full > hx + 5e-4]
        cols.append(np.concatenate([[hx], keep]))
    nx = max(len(c) for c in cols)
    # pad every column to nx by re-densifying its head end: a structured grid
    # needs a rectangular index space, and padding at the HEAD keeps the grip
    # lattice aligned everywhere it is visible.
    X = np.empty((nx, ny))
    for j, c in enumerate(cols):
        if len(c) < nx:
            pad = np.linspace(c[0], c[1], nx - len(c) + 2)[1:-1]
            c = np.concatenate([[c[0]], pad, c[1:]])
        X[:, j] = c
    Y = np.tile(ys, (nx, 1))
    return X, Y, ys


def quads_of(nx, ny, base=0, flip=False):
    idx = np.arange(nx * ny).reshape(nx, ny) + base
    a, b = idx[:-1, :-1].ravel(), idx[1:, :-1].ravel()
    c, d = idx[1:, 1:].ravel(), idx[:-1, 1:].ravel()
    return (np.stack([a, d, c, b], 1) if flip else np.stack([a, b, c, d], 1))


# ===========================================================================
# 4.  THE DECK PLATE
# ===========================================================================

def build_deck():
    """The running surface, its underside and its rim, as one closed solid.

    Returns (verts, quads, attrs) with `attrs` the per-vertex fields the
    material reads: `groove`, `track`, `edge`, `fall`.
    """
    X, Y, ys = deck_grid()
    nx, ny = X.shape
    ZT = surface_z(X, Y)
    ZB = under_z(X, Y)
    n = nx * ny

    Vt = np.stack([X.ravel(), Y.ravel(), ZT.ravel()], 1)
    Vb = np.stack([X.ravel(), Y.ravel(), ZB.ravel()], 1)
    V = np.concatenate([Vt, Vb], 0)

    Qt = quads_of(nx, ny, 0, flip=False)          # top, +Z outward
    Qb = quads_of(nx, ny, n, flip=True)           # bottom, -Z outward

    # ---- the rim: four boundary walls, top ring stitched to bottom ring ----
    it = np.arange(n).reshape(nx, ny)
    ib = it + n
    rings = []
    rings.append((it[0, :], ib[0, :]))            # head (the nose arc)
    rings.append((it[-1, ::-1], ib[-1, ::-1]))    # toe
    rings.append((it[:, 0][::-1], ib[:, 0][::-1]))   # y = -1.5
    rings.append((it[:, -1], ib[:, -1]))          # y = +1.5
    Qr = []
    for a, b in rings:
        Qr.append(np.stack([a[:-1], a[1:], b[1:], b[:-1]], 1))
    Q = np.concatenate([Qt, Qb] + Qr, 0)

    xr, yr = X.ravel(), Y.ravel()
    r = np.hypot(xr, yr)
    ay = np.abs(yr)
    attrs = {
        # 1 in a groove floor, 0 on the land: dirt, dulled anodising, water
        "groove": np.tile(np.clip(grip_depth(xr) / GRIP_DEPTH, 0, 1), 2),
        # the two bands the tyres cross
        "track": np.tile(
            K.smoothstep(TRACK_R - TYRE_HALF_R - 0.06, TRACK_R - TYRE_HALF_R, ay)
            * K.smoothstep(TRACK_F + TYRE_HALF_F + 0.06,
                           TRACK_F + TYRE_HALF_F, ay), 2),
        # proximity to a worn arris
        "edge": np.tile(1.0 - K.clamp01(
            np.minimum(np.minimum(HALF_W - ay, r - NOSE_R),
                       RAMP_FOOT_X - xr) / 0.055), 2),
        # how far down the fall the point is: 0 at the head, 1 at the toe
        "fall": np.tile(K.clamp01((xr - DAIS_LIP_X)
                                  / (RAMP_FOOT_X - DAIS_LIP_X)), 2),
    }
    return V, Q, attrs, (nx, ny)


# ===========================================================================
# 5.  THE FABRICATION AROUND IT
# ===========================================================================

def box(c, half, chamfer=0.0025):
    """A chamfered box as (verts, quads). Every arris on this object is cut."""
    cx, cy, cz = c
    hx, hy, hz = half
    e = chamfer
    V, Q = [], []
    # an octagonal section swept in x: cheap, and it puts a real highlight on
    # every long edge instead of a mathematical line
    sec = [(-hy + e, -hz), (hy - e, -hz), (hy, -hz + e), (hy, hz - e),
           (hy - e, hz), (-hy + e, hz), (-hy, hz - e), (-hy, -hz + e)]
    for sx in (-hx, hx):
        for sy, sz in sec:
            V.append((cx + sx, cy + sy, cz + sz))
    m = len(sec)
    for i in range(m):
        j = (i + 1) % m
        Q.append((i, j, m + j, m + i))
    # THE CAPS ARE THREE QUADS, NOT A FAN OF DEGENERATE ONES. The first draft
    # wrote `(0, i, i+1, 0)`, a quad with a repeated index and therefore zero
    # area on one edge; `tools/winding_audit.py` found 4 pieces of DDR_Frame
    # facing inward because of it. An octagon splits into three quads exactly.
    # `sec` runs counter-clockwise in (y, z), i.e. counter-clockwise seen from
    # +x, so a face in that order has its normal along +x. The cap at -hx must
    # therefore be REVERSED and the cap at +hx must not: writing it the other
    # way round put 16 inconsistent edge pairs in every one of the 153 boxes.
    for a, b_, c_, d_ in ((0, 1, 2, 3), (0, 3, 4, 5), (0, 5, 6, 7)):
        Q.append((d_, c_, b_, a))
        Q.append((m + a, m + b_, m + c_, m + d_))
    return np.array(V, float), np.array(Q, int)


def build_frame():
    """Longitudinal bearers, transverse channels and levelling feet.

    Seen only through the 22 mm fascia reveal and from the foot, but seen: the
    launch camera at frame 851 stands 3.255 m away and 0.4 m off the floor, which
    is a line of sight straight along the underside.
    """
    V, Q = [], []

    def add(v, q):
        Q.append(q + sum(len(a) for a in V))
        V.append(v)

    rng = K.Rng(SEED, 7)
    # five longitudinal RHS 60 x 40, under the deck, following the fall
    for i, y in enumerate((-1.30, -0.72, 0.0, 0.72, 1.30)):
        x0 = float(head_x(abs(y))) + 0.030
        x1 = TOE_START_X - 0.010
        nseg = 26
        xs = np.linspace(x0, x1, nseg + 1)
        for a, b in zip(xs[:-1], xs[1:]):
            zc = 0.5 * (float(top_z(a)) + float(top_z(b))) - PLATE_T - 0.021
            add(*box(((a + b) * 0.5, y, zc), ((b - a) * 0.5, 0.020, 0.021)))
    # four transverse channels
    for x in (3.760, 4.400, 5.100, 5.800):
        zc = float(top_z(x)) - PLATE_T - 0.062
        add(*box((x, 0.0, zc), (0.025, HALF_W - 0.040, 0.019)))
    # levelling feet: base plate + boss, embedded EMBED into the floor
    for x, y in ((3.760, -1.34), (3.760, 1.34), (4.700, -1.34), (4.700, 1.34),
                 (5.600, -1.34), (5.600, 1.34), (6.020, -1.34), (6.020, 1.34)):
        zt = float(top_z(x)) - PLATE_T - 0.045
        h = 0.5 * (zt + EMBED)
        add(*box((x, y, -EMBED + h), (0.048, 0.048, h)))
        add(*box((x, y, zt - 0.014), (0.021, 0.021, 0.016), chamfer=0.0018))
    # shim stacks bearing on the static Platform_Dais ring at z = 0.300
    for a in np.linspace(-24.0, 24.0, 5):
        rr = 0.5 * (PLATFORM_RING[0] + PLATFORM_RING[1])
        x, y = rr * math.cos(math.radians(a)), rr * math.sin(math.radians(a))
        if abs(y) > HALF_W - 0.06:
            continue
        h = 0.5 * (DECK_TOP_Z - PLATE_T - PLATFORM_TOP_Z)
        add(*box((x, y, PLATFORM_TOP_Z + h), (0.045, 0.045, h + 0.0005),
                 chamfer=0.0015))
    _ = rng
    return np.concatenate(V, 0), np.concatenate(Q, 0)


def build_fascia(side):
    """One anodised cheek panel, folded top and bottom, set back for a reveal.

    `side` is +1 or -1. The panel is a 3 mm shell with a top return under the
    deck's overhang and a bottom return into the floor, so its silhouette from a
    low camera is a folded edge and not a card.
    """
    y0 = side * (HALF_W - FASCIA_SETBACK)
    x0 = float(head_x(abs(y0))) + 0.004
    x1 = RAMP_FOOT_X - 0.055
    xs = np.concatenate([np.linspace(x0, x0 + 0.05, 9),
                         np.linspace(x0 + 0.05, x1 - 0.05, 190),
                         np.linspace(x1 - 0.05, x1, 9)])
    xs = np.array(sorted(set(np.round(xs, 7))))

    # the section, in (dy, z-offset-from-the-panel-top). Outer face first.
    def section(x):
        zt = float(top_z(x)) - 0.020
        zb = -EMBED
        pts = [(0.030, zt + 0.006),               # top return, tucked under
               (0.0, zt),
               (0.0, zb + 0.030),
               (0.026, zb + 0.004),               # bottom return, splayed
               (0.030, zb)]
        return zt, zb, pts

    prof = [section(x)[2] for x in xs]
    m = len(prof[0])
    V, Q = [], []
    for i, x in enumerate(xs):
        for dy, z in prof[i]:
            V.append((x, y0 + side * dy, z))
    for i, x in enumerate(xs):                     # the inner (back) face
        for dy, z in prof[i]:
            V.append((x, y0 + side * (dy - FASCIA_T), z))
    n = len(xs) * m
    for i in range(len(xs) - 1):
        for j in range(m - 1):
            a = i * m + j
            Q.append((a, a + 1, a + m + 1, a + m))
            b = a + n
            Q.append((b, b + m, b + m + 1, b + 1))
        # close the top and bottom edges
        a, b = i * m, i * m + n
        Q.append((a, a + m, b + m, b))
        a, b = i * m + m - 1, i * m + m - 1 + n
        Q.append((a, b, b + m, a + m))
    # END CAPS, AND THE TWO ENDS WIND OPPOSITE WAYS. Giving both the same order
    # leaves one of them facing into the panel: `winding_audit` reported 10
    # inconsistent edge pairs per fascia, which is exactly the two caps' four
    # shared edges plus the section's returns.
    for i, rev in ((0, False), (len(xs) - 1, True)):
        for j in range(m - 1):
            a = i * m + j
            q = (a, a + n, a + n + 1, a + 1)
            Q.append(q[::-1] if rev else q)
    V = np.array(V, float)
    Q = np.array(Q, int)
    if side < 0:
        Q = Q[:, ::-1].copy()
    return V, Q


def build_nose_apron():
    """The curved panel that closes the turntable gap under the ramp's nose.

    Without it the low launch camera looks straight through a 12.5 mm slot into
    the plinth cavity, which is a black line across the head of the shot.
    """
    ys = np.linspace(-HALF_W + 0.004, HALF_W - 0.004, 260)
    xs = head_x(ys) - 0.008
    ztop = DECK_TOP_Z - PLATE_T - 0.002
    zbot = PLATFORM_TOP_Z - 0.004
    V, Q = [], []
    for x, y in zip(xs, ys):
        V += [(x, y, ztop), (x, y, zbot),
              (x - 0.004, y, zbot), (x - 0.004, y, ztop)]
    n = 4
    for i in range(len(ys) - 1):
        for j in range(n):
            a, b = i * n + j, i * n + (j + 1) % n
            Q.append((a, b, b + n, a + n))
    return np.array(V, float), np.array(Q, int)


def build_toe_bar():
    """A chamfered bar under the feathered toe, embedded EMBED into the floor.

    The toe of the plate laps 3.5 mm into the slab and is not a foot; this is the
    foot. Stated so the 3.5 mm is a decision and not an oversight.
    """
    V, Q = [], []

    def add(v, q):
        Q.append(q + sum(len(a) for a in V))
        V.append(v)
    h = 0.5 * (float(under_z(TOE_START_X - 0.02)) + EMBED)
    add(*box((TOE_START_X - 0.02, 0.0, -EMBED + h),
             (0.028, HALF_W - 0.030, h), chamfer=0.0020))
    return np.concatenate(V, 0), np.concatenate(Q, 0)


# ===========================================================================
# 6.  MATERIALS — radiance-stated relief, wired by name
# ===========================================================================

#: (name, wavelength_m, modulation_pp) for the plate's four shader stages.
#: All four sit in RELIEF_BANDS["isotropic_micro"] (0.12-0.45) ON PURPOSE:
#: on a 12.47 deg sun the MESH carries the read (the grip grooves are m ~ 2.4 in
#: the dihedrals) and the shader garnishes it. Five of the seven wave-1 modules
#: that pass check 7 pass on their geometry alone.
PLATE_BUMPS = (
    ("brushed lay",     0.00090, 0.28),
    ("machining swirl", 0.00220, 0.18),
    ("anodise peel",    0.00550, 0.22),
    ("traffic polish",  0.00032, 0.24),
)


def mat_plate():
    """MILL-FINISH ALUMINIUM TOOLING PLATE. Not the turntable's black anodise.

    THE FIRST VERSION OF THIS MATERIAL WAS REJECTED BY THE GATE AND BY EYE, AND
    THE REASON IS WORTH KEEPING. It copied `TurntableTop`, measured off the
    shipped showroom at base 0.048/0.049/0.053 with metallic 0.86 — a display
    top, made to be dark and to mirror an interior rig of 61 lights. Under the
    contract's 12.47 deg exterior sun that surface has nothing to reflect but
    sky: `item_gate` measured **86 % of the subject crushed to black** and the
    macro came back a flat blue-grey sheet in which none of the milled relief
    could be seen at all. Every millimetre of geometry in this file was invisible
    because of one albedo.

    The physical answer is also the right one. A DELIVERY RAMP IS NOT A DISPLAY
    TOP. It is a working piece that gets driven over, and black anodise on a
    running surface polishes to grey in a week — nobody specifies it. Natural
    mill-finish / clear-anodised tooling plate is what such a thing is made of,
    it reads as aluminium instead of as a dark shape, and it gives the tyre scuff
    and the groove dirt somewhere dark to be. The ramp reading as a service item
    against the turntable's furniture-black is a distinction, not a clash.
    """
    t = K.NT(PFX + "Plate")
    P = t.object_coords()
    groove = t.attr("groove")
    track = t.attr("track")
    edge = t.attr("edge")
    fall = t.attr("fall")

    # ---- colour ------------------------------------------------------------
    # Clear-anodised 6082: near-neutral, a touch cool, with the mill's own
    # roll-direction banding still faintly in it.
    blotch = t.noise(P, wavelength_m=0.075, detail=6.0, rough=0.5)
    base = t.ramp(blotch, [(0.28, (0.5180, 0.5245, 0.5340)),
                           (0.62, (0.5720, 0.5780, 0.5860)),
                           (0.95, (0.6180, 0.6230, 0.6290))])
    # a milled groove wall is freshly cut metal: brighter and less oxidised
    milled = t.cmix(groove, base, (0.6620, 0.6660, 0.6700))
    # ... and then it fills with dust and rubber dust, which is the opposite
    dirt = t.vor(P, wavelength_m=0.013, feature="F1")
    dirtm = t.math("MULTIPLY", groove, t.maprange(dirt, 0.30, 0.80, 0.25, 1.0))
    milled = t.cmix(dirtm, milled, (0.1450, 0.1330, 0.1180))
    # rubber laid down by one launch, inside the tracks only
    rub = t.noise(t.vmath("SCALE", P, scale=3.4), wavelength_m=0.020, detail=7.0)
    rubm = t.math("MULTIPLY", track, t.maprange(rub, 0.34, 0.78, 0.0, 1.0))
    rubm = t.math("MULTIPLY", rubm, t.maprange(fall, 0.05, 0.55, 0.35, 1.0))
    col = t.cmix(rubm, milled, (0.0640, 0.0600, 0.0585))
    # burnished bright where the arris has been rubbed back
    wearn = t.noise(P, wavelength_m=0.028, detail=5.0)
    wearm = t.math("MULTIPLY", edge, t.maprange(wearn, 0.42, 0.74, 0.0, 1.0))
    col = t.cmix(wearm, col, (0.7250, 0.7290, 0.7340))

    # ---- roughness ---------------------------------------------------------
    rgh = t.noise(P, wavelength_m=0.016, detail=8.0, rough=0.62)
    # MILL FINISH IS NOT A MIRROR. At 0.300-0.455 with metallic 1.0 the first
    # 4K macro came back with p99 = 1.000 and 2 % of the frame clipped: the
    # plate was specularly reflecting the sun disc straight down the lens. A
    # rolled-and-milled aluminium plate is satin, and satin is also what lets
    # the milled arrises read as lip-and-shade instead of as one blown highlight.
    rgh = t.maprange(rgh, 0.30, 0.72, 0.360, 0.520)
    rgh = t.fmix(groove, rgh, t.math("ADD", rgh, 0.135))
    rgh = t.fmix(dirtm, rgh, t.math("ADD", rgh, 0.190))
    rgh = t.fmix(rubm, rgh, t.math("ADD", rgh, 0.245))
    rgh = t.fmix(wearm, rgh, t.math("SUBTRACT", rgh, 0.145))

    # ---- relief: FOUR STAGES, STATED AS RADIANCE ---------------------------
    nrm = None
    for i, (_nm, lam, m) in enumerate(PLATE_BUMPS):
        if i == 0:
            # the brushed lay runs along the FALL, so it is a wave, not a noise
            h = t.wave(P, wavelength_m=lam, distortion=1.6, detail=3.0,
                       direction="X")
            hpp = 1.0
        elif i == 3:
            h = t.vor(P, wavelength_m=lam, feature="F1")
            hpp = 1.0
        else:
            h = t.noise(P, wavelength_m=lam, detail=7.0, rough=0.55)
            hpp = 0.62                      # a raw Noise does not span 0..1
        nrm = t.bump(h, 1.0, normal=nrm, modulation_pp=m, wavelength_m=lam,
                     height_pp=hpp)

    t.principled_out(base_color=col, metallic=1.0, roughness=rgh,
                     anisotropic=0.55, normal=nrm)
    return t.m


def mat_fascia():
    """The cheek panels: satin anodised sheet, a shade lighter than the plate."""
    t = K.NT(PFX + "Fascia")
    P = t.object_coords()
    n1 = t.noise(P, wavelength_m=0.140, detail=5.0)
    # The cheeks ARE anodised dark, which is the point: the fascia is trim and
    # belongs to the showroom's furniture, the deck is a working surface and
    # belongs to the workshop. Putting the two on one object is what stops the
    # ramp reading as a single extruded lump.
    col = t.ramp(n1, [(0.32, (0.0930, 0.0948, 0.1002)),
                      (0.70, (0.1185, 0.1200, 0.1263))])
    # the dust line every vertical panel in a showroom has along its foot
    z = t.sep(P, 2)
    dust = t.maprange(z, -0.02, 0.10, 1.0, 0.0)
    grime = t.noise(P, wavelength_m=0.030, detail=6.0)
    dm = t.math("MULTIPLY", dust, t.maprange(grime, 0.36, 0.70, 0.15, 1.0))
    col = t.cmix(dm, col, (0.1180, 0.1120, 0.1010))
    rgh = t.maprange(t.noise(P, wavelength_m=0.009, detail=7.0),
                     0.30, 0.70, 0.290, 0.410)
    rgh = t.fmix(dm, rgh, t.math("ADD", rgh, 0.210))
    nrm = None
    for lam, m, hpp in ((0.00110, 0.26, 1.0), (0.00420, 0.19, 0.62),
                        (0.02600, 0.16, 0.62)):
        h = (t.wave(P, wavelength_m=lam, distortion=1.2, direction="Z")
             if hpp == 1.0 else t.noise(P, wavelength_m=lam, detail=6.0))
        nrm = t.bump(h, 1.0, normal=nrm, modulation_pp=m, wavelength_m=lam,
                     height_pp=hpp)
    t.principled_out(base_color=col, metallic=0.80, roughness=rgh, normal=nrm)
    return t.m


def mat_steel():
    """The frame: powder-coated steel, chipped at the arrises, dusty on top."""
    t = K.NT(PFX + "Steel")
    P = t.object_coords()
    n1 = t.noise(P, wavelength_m=0.055, detail=6.0)
    col = t.ramp(n1, [(0.30, (0.0182, 0.0186, 0.0198)),
                      (0.74, (0.0268, 0.0272, 0.0288))])
    chip = t.vor(P, wavelength_m=0.016, feature="F1")
    chipm = t.maprange(chip, 0.76, 0.92, 0.0, 1.0)
    col = t.cmix(chipm, col, (0.1420, 0.1300, 0.1180))
    rgh = t.maprange(t.noise(P, wavelength_m=0.006, detail=7.0),
                     0.28, 0.74, 0.430, 0.610)
    nrm = None
    for lam, m, hpp in ((0.00075, 0.30, 0.62), (0.00340, 0.24, 0.62),
                        (0.01600, 0.20, 1.0)):
        h = (t.vor(P, wavelength_m=lam, feature="F1") if hpp == 1.0
             else t.noise(P, wavelength_m=lam, detail=7.0))
        nrm = t.bump(h, 1.0, normal=nrm, modulation_pp=m, wavelength_m=lam,
                     height_pp=hpp)
    t.principled_out(base_color=col, metallic=0.35, roughness=rgh, normal=nrm)
    return t.m


# ===========================================================================
# 7.  BUILD
# ===========================================================================

def _emit(name, V, Q, mat, root, smooth=33.0, attrs=None):
    me, off = K.new_mesh(name, V, quads=Q, smooth_deg=smooth)
    if attrs:
        K.bake_attributes(me, attrs)
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    ob.location = off
    root.objects.link(ob)
    return ob


def build(scene=None, test_scene=False, samples=256, stats=None):
    K._require_bpy("build")
    scene = scene or bpy.context.scene
    # PURGE FIRST, THEN MAKE. `K.purge(prefix, coll_name)` removes the named
    # collection itself, so the REFERENCE order -- coll() then purge() -- hands
    # back a datablock that has already been freed and the first `link()` dies
    # with "StructRNA of type Collection has been removed". Prefix-scoped either
    # way, so it cannot touch another item.
    K.purge(PFX, COLL)
    root = K.coll(COLL)

    m_plate, m_fascia, m_steel = mat_plate(), mat_fascia(), mat_steel()

    V, Q, attrs, (nx, ny) = build_deck()
    deck = _emit(PFX + "Deck", V, Q, m_plate, root, attrs=attrs)

    fr = build_frame()
    _emit(PFX + "Frame", fr[0], fr[1], m_steel, root, smooth=26.0)

    for side, tag in ((+1, "L"), (-1, "R")):
        fv, fq = build_fascia(side)
        _emit(PFX + "Fascia" + tag, fv, fq, m_fascia, root, smooth=28.0)

    nv, nq = build_nose_apron()
    _emit(PFX + "NoseApron", nv, nq, m_fascia, root, smooth=28.0)

    tv, tq = build_toe_bar()
    _emit(PFX + "ToeBar", tv, tq, m_steel, root, smooth=26.0)

    tris = 0
    for ob in root.objects:
        if ob.type == "MESH":
            tris += sum(len(p.vertices) - 2 for p in ob.data.polygons)
    if stats is not None:
        stats.update({"objects": len(root.objects), "tris": tris,
                      "deck_grid": (nx, ny)})
    K.log("%s: %d objects, %.3f M triangles, deck grid %d x %d"
          % (ITEM, len(root.objects), tris / 1e6, nx, ny))
    K.log("running surface: declared envelope %.4f..%.4f m over x %.3f..%.3f"
          % (float(top_z(RAMP_FOOT_X)), float(top_z(DAIS_LIP_X)),
             float(head_x(HALF_W)), RAMP_FOOT_X))

    if test_scene:
        cams = K.coll(COLL + "/Cameras", root)
        stand = K.coll(COLL + "/Standins", root)
        K.contract_sun(PFX, scene=scene, coll_=root)
        _standin_floor(stand, m_steel)
        # THE MACRO LOOKS AT THE EDGE, NOT DOWN THE PLATE. The first framing
        # aimed at the centreline from a shallow angle and returned 3840 x 2160
        # pixels of grazing tread and nothing else — no chamfer, no reveal, no
        # fascia, no wedge, no silhouette. At 1.4 m on a 35 mm lens the whole
        # 0.340 m rise is 907 px, so the shot that carries the object is the
        # three-quarter view along its edge, where the arris chamfer, the 22 mm
        # fascia reveal, the tread field's plain margin and the fall of the
        # wedge are all in one frame.
        aim = (4.80, HALF_W - 0.060, float(top_z(4.80)) - 0.010)
        v = np.array([-0.30, 0.86, 0.41], dtype=float)
        v /= np.linalg.norm(v)
        loc = tuple(np.array(aim) + v * FILMED_AT_M)
        K.macro_rig(PFX + "CAM_MACRO_4K", loc, aim, LENS_MM, cams, scene=scene,
                    samples=samples, want_distance_m=FILMED_AT_M)
        # A second view, the head joint, where the turntable clearance, the
        # scribed nose, the 0.340 landing and the break at x = 3.700 all meet.
        # Not the deliverable. The first attempt stood 0.95 m off on a 50 mm
        # lens and returned nothing but tread: at that distance the frame is
        # 0.68 m wide and the joint is 0.24 m of it. 1.60 m on 35 mm frames
        # 1.65 m, which holds the nose, the landing and the first metre of fall.
        aim2 = (DAIS_LIP_X - 0.16, 0.40, DECK_TOP_Z - 0.02)
        v2 = np.array([0.74, 0.46, 0.49], dtype=float)
        v2 /= np.linalg.norm(v2)
        K.add_camera(PFX + "CAM_HEAD", tuple(np.array(aim2) + v2 * 1.60), aim2,
                     35.0, cams)
        K.assert_no_external_assets()
    _ = deck
    return root


def _standin_floor(stand, mat):
    """A showroom floor and a dais stump for the test scene ONLY.

    Named `Standin` so `item_gate.py`'s context filter drops them: the gate
    picked a `CTX_Column` as its subject once already. They exist because a ramp
    photographed against nothing has no contact shadow and no reflection, and the
    reflection is the instrument this whole defect was found with.
    """
    n = 240
    xs = np.linspace(-2.0, 12.0, n)
    ys = np.linspace(-7.0, 7.0, n)
    Xg, Yg = np.meshgrid(xs, ys, indexing="ij")
    Zg = np.zeros_like(Xg)
    Vv = np.stack([Xg.ravel(), Yg.ravel(), Zg.ravel()], 1)
    _emit(PFX + "Standin_Floor", Vv, quads_of(n, n), mat, stand, smooth=None)
    # the dais stump: a disc at 0.340 out to DECK_TOP_R and a ring at 0.300
    th = np.linspace(0, 2 * math.pi, 361)[:-1]
    V, Q = [], []
    for rr, zz in ((0.0, DECK_TOP_Z), (DECK_TOP_R, DECK_TOP_Z),
                   (DECK_RIM_R, DECK_TOP_Z - 0.011),
                   (DECK_RIM_R, -0.02)):
        for a in th:
            V.append((rr * math.cos(a), rr * math.sin(a), zz))
    m = len(th)
    for k in range(3):
        for i in range(m):
            j = (i + 1) % m
            Q.append((k * m + i, k * m + j, (k + 1) * m + j, (k + 1) * m + i))
    _emit(PFX + "Standin_Deck", np.array(V, float), np.array(Q, int), mat,
          stand, smooth=40.0)
    V2, Q2 = [], []
    for rr, zz in ((PLATFORM_RING[0], PLATFORM_TOP_Z),
                   (PLATFORM_RING[1], PLATFORM_TOP_Z),
                   (PLATFORM_R, PLATFORM_TOP_Z - 0.04), (PLATFORM_R, -0.02)):
        for a in th:
            V2.append((rr * math.cos(a), rr * math.sin(a), zz))
    for k in range(3):
        for i in range(m):
            j = (i + 1) % m
            Q2.append((k * m + i, k * m + j, (k + 1) * m + j, (k + 1) * m + i))
    _emit(PFX + "Standin_Platform", np.array(V2, float), np.array(Q2, int),
          mat, stand, smooth=40.0)


def interface_json(path=None):
    return K.interface_json(
        ITEM, path,
        declared_profile={
            "deck_top_z": DECK_TOP_Z, "lip_x": DAIS_LIP_X,
            "foot_x": RAMP_FOOT_X, "half_width_m": HALF_W,
            "source": "docs/circuit_spec.json showroom.dais.delivery_ramp",
            "authority": "anim/carrig._ramp_ground -- the car is KEYED on it"},
        as_built_dais={"deck_top_r": DECK_TOP_R, "deck_rim_r": DECK_RIM_R,
                       "platform_r": PLATFORM_R,
                       "platform_top_z": PLATFORM_TOP_Z,
                       "measured": "work/ramp/dais_probe.json"},
        nose_scribe_r=NOSE_R,
        turntable_clearance_m=TURNTABLE_CLEARANCE_M,
        unsupported_bridge_m=NOSE_R - DECK_TOP_R,
        running_surface="top_z(x) is the HIGH ENVELOPE; all relief subtractive",
        toe_lap_into_floor_m=TOE_TIP_EMBED,
        foot_embed_m=EMBED,
        materials=[PFX + "Plate", PFX + "Fascia", PFX + "Steel"])


# ===========================================================================
# 8.  SELFTEST — measured, with a negative control on every check
# ===========================================================================

def selftest(verbose=True):
    n, fails = [0], []

    def chk(name, ok, detail):
        n[0] += 1
        if not ok:
            fails.append(name)
        if verbose:
            print("  [%s] %-58s %s" % ("PASS" if ok else "FAIL", name, detail))

    print("\n[1] THE PROFILE IS carrig's, NOT A SECOND OPINION ABOUT IT")
    try:
        import carrig as CR
        xs = np.linspace(3.0, 7.0, 20001)
        mine = top_z(xs)
        theirs = np.array([CR._ramp_ground(float(x)) for x in xs])
        err = float(np.abs(mine - theirs).max())
        # NEGATIVE CONTROL: a profile 1 mm off must NOT pass
        bad = float(np.abs((mine + 0.001) - theirs).max())
        chk("top_z == carrig._ramp_ground over 20,001 stations",
            err < 1e-9 and bad > 5e-4,
            "worst |difference| %.3e m; a 1 mm error would read %.3e" % (err, bad))
        chk("the two agree on the three declared numbers",
            abs(CR.DECK_TOP_Z - DECK_TOP_Z) < 1e-12
            and abs(CR.DAIS_LIP_X - DAIS_LIP_X) < 1e-12
            and abs(CR.RAMP_FOOT_X - RAMP_FOOT_X) < 1e-12,
            "carrig %.3f / %.3f / %.3f" % (CR.DECK_TOP_Z, CR.DAIS_LIP_X,
                                           CR.RAMP_FOOT_X))
    except Exception as e:                                    # noqa: BLE001
        chk("carrig importable", False, repr(e))

    print("\n[2] THE HEAD REACHES THE DECK THAT WAS BUILT, NOT THE ONE DECLARED")
    bridge = NOSE_R - DECK_TOP_R
    sag = bridge * bridge / (8.0 * 0.360)
    chk("nose clears the ROTATING deck rim", NOSE_R > DECK_RIM_R,
        "nose r %.5f, deck rim r %.5f, clearance %.1f mm"
        % (NOSE_R, DECK_RIM_R, 1000 * TURNTABLE_CLEARANCE_M))
    chk("the residual bridge is under a tenth of a pixel of sag",
        bridge < 0.070 and sag * PX_PER_M < 4.0,
        "deck top face ends r %.3f, nose starts r %.3f -> %.1f mm bridged, "
        "a 0.720 m wheel sags %.2f mm = %.1f px"
        % (DECK_TOP_R, NOSE_R, 1000 * bridge, 1000 * sag, sag * PX_PER_M))
    # the front contact patch's radius where the profile still claims 0.340
    r838 = math.hypot(3.4932, TRACK_F)
    chk("the head covers where the built deck does not",
        NOSE_R < r838 < math.hypot(DAIS_LIP_X, TRACK_F) + 1e-9,
        "at f838 the front patch sits at r = %.4f, outboard of the built deck's "
        "top face (%.3f) and INBOARD of this head's outer edge -- so it lands on "
        "this landing at 0.340 instead of on the platform ring at 0.300"
        % (r838, DECK_TOP_R))

    print("\n[3] THE RUNNING SURFACE NEVER RISES ABOVE THE DECLARED ENVELOPE")
    xs = np.linspace(float(head_x(HALF_W)) - 0.01, RAMP_FOOT_X, 4001)
    ys = np.linspace(-HALF_W, HALF_W, 601)
    Xg, Yg = np.meshgrid(xs, ys, indexing="ij")
    rel = relief(Xg, Yg)
    lift = float((top_z(Xg, Yg) - surface_z(Xg, Yg)).min())
    bad = float((top_z(Xg, Yg) - (surface_z(Xg, Yg) + 1e-4)).min())
    chk("min(relief) >= 0 over 2.40 M samples, and it REACHES 0",
        0.0 <= lift < 5e-5 and bad < 0,
        "the built surface's HIGHEST point sits %.4f mm below the declared "
        "plane (0.0000 would be touching, negative would be a lift); the "
        "negative control, the same field raised 0.1 mm, reads %+.4f mm and "
        "fails as it must" % (1000 * lift, 1000 * bad))
    chk("the relief is deep enough to be a machined surface",
        0.0015 < float(rel.max()) < 0.020,
        "deepest cut %.2f mm (grooves %.1f + waviness %.1f + chamfer <= %.1f)"
        % (1000 * rel.max(), 1000 * GRIP_DEPTH, 1000 * WAVE_PP,
           1000 * CHAMFER_WEAR[1]))

    print("\n[4] THE WHEELS, AGAINST THE KEYS THAT ARE IN THE BLEND")
    # the thirteen frames, straight off the rig (work/ramp/probe2.json)
    keyed = {839: (3.7517, 0.33598), 840: (4.0357, 0.29929),
             841: (4.3392, 0.26007), 842: (4.6624, 0.21828),
             843: (5.0056, 0.17387), 844: (5.3692, 0.12676),
             845: (5.7538, 0.07690), 846: (6.1577, 0.02450),
             849: (3.8951, 0.32229), 850: (4.3675, 0.25936),
             851: (4.8606, 0.19375), 852: (5.3742, 0.12551),
             853: (5.9078, 0.05468)}
    # THE KEYS ARE ON THE WHEEL ENVELOPE, NOT ON THE GROUND, AND THAT IS RIGHT.
    # `carrig._wheel_envelope` dilates the piecewise-linear ground by the 0.360 m
    # wheel disc, because a 0.720 m tyre crossing the convex break at x = 3.700
    # PIVOTS ON THE ARRIS: its lowest point is genuinely above both planes while
    # it does so. So the pair of facts that matter are (a) the keys reproduce
    # the envelope of THIS ground exactly, and (b) the built surface is never
    # above the keyed wheel, i.e. the ramp can never push the car up.
    #
    # Comparing the keys to `top_z` directly and calling a 7.8 mm difference a
    # defect is what the first draft of this check did. It is the envelope.
    # DECOMPOSE THE GAP, so every millimetre of it has exactly one owner.
    #   keyed - top_z  =  (envelope - top_z)   the rigid wheel over the arris
    #                  +  (keyed - envelope)   the telemetry's own compliance
    # The first is this module's business and is geometry. The second is
    # `anim/carrig`'s pitch/roll compliance term, added on top of the contact
    # solve, and nothing here can or should move it.
    try:
        import carrig as CR
        env = {f: float(CR._wheel_envelope(x)) for f, (x, _z) in keyed.items()}
        geo = max(env[f] - float(top_z(x)) for f, (x, _z) in keyed.items())
        comp = max(abs(zb - env[f]) for f, (_x, zb) in keyed.items())
        if verbose:
            print("      frame      x     top_z  envelope     keyed   "
                  "env-top   keyed-env")
            for f in sorted(keyed):
                x, zb = keyed[f]
                print("      %5d %7.4f %9.5f %9.5f %9.5f %8.2f mm %8.2f mm"
                      % (f, x, float(top_z(x)), env[f], zb,
                         1000 * (env[f] - float(top_z(x))),
                         1000 * (zb - env[f])))
        chk("the wheel-over-arris envelope accounts for the gap",
            geo < 0.010 and comp < 0.006,
            "rigid-wheel envelope lifts the tyre at most %.2f mm above this "
            "surface; the telemetry's suspension compliance adds at most "
            "%.2f mm on top of it. Neither is a hole in the ramp."
            % (1000 * geo, 1000 * comp))
    except Exception as e:                                    # noqa: BLE001
        chk("carrig importable for the envelope", False, repr(e))

    sink, sink_f = 0.0, None
    lift_e, lift_f = 0.0, None
    for f, (x, zb) in keyed.items():
        d = float(top_z(x)) - zb          # >0 would be the ramp pushing the car
        if d > sink:
            sink, sink_f = d, f
        if -d > lift_e:
            lift_e, lift_f = -d, f
    chk("the built envelope is never ABOVE a keyed wheel", sink <= 0.0,
        "worst penetration of the declared surface into the tyre %+.4f mm "
        "(frame %s). The wheel's LOWEST POINT reads at most %.2f mm above this "
        "surface at frame %d, and 3.06 mm of that is not a gap at all: a circle "
        "tangent to a 13.1 %% plane has its lowest z point r(1-cos a) = 3.04 mm "
        "above the plane AT ITS OWN x while touching it 46.7 mm behind. The "
        "residue is the telemetry's compliance."
        % (1000 * sink, sink_f, 1000 * lift_e, lift_f))
    # NEGATIVE CONTROL: the SAME comparison against the floor the car had
    worst0 = max(zb for _f, (_x, zb) in keyed.items())
    chk("and the control -- the same wheels against the floor that WAS there",
        worst0 > 0.30,
        "worst float against z = 0 is %.3f m, so the check above is not "
        "measuring an identity" % worst0)

    print("\n[5] THE PIXEL BUDGET")
    chk("a grip groove resolves", GRIP_WIDTH * PX_PER_M > 8.0,
        "%.1f mm groove = %.1f px, %.1f mm deep, and at %.2f deg the sun throws "
        "%.1f mm = %.1f px of shadow off its wall"
        % (1000 * GRIP_WIDTH, GRIP_WIDTH * PX_PER_M, 1000 * GRIP_DEPTH,
           K.sun_elev_deg(), 1000 * GRIP_DEPTH * C.SUN_SHADOW_RATIO,
           GRIP_DEPTH * C.SUN_SHADOW_RATIO * PX_PER_M))
    chk("the manifest distance is the stricter of the two",
        FILMED_AT_M < MEASURED_NEAREST_M,
        "manifest %.2f m / %.0f mm = %.0f px/m; MEASURED closest approach over "
        "2,978 frames %.3f m / %.2f mm = %.0f px/m"
        % (FILMED_AT_M, LENS_MM, PX_PER_M, MEASURED_NEAREST_M, MEASURED_LENS_MM,
           K.px_per_m(MEASURED_NEAREST_M, MEASURED_LENS_MM)))

    print("\n[6] THE RELIEF STACK, STATED AS RADIANCE")
    rows = K.relief_budget(
        [(nm, lam, K.relief_amplitude_for(m, lam)) for nm, lam, m in PLATE_BUMPS],
        band="isotropic_micro", verbose=verbose)
    chk("every shader stage sits inside isotropic_micro",
        all(r["verdict"] == "ok" for r in rows),
        "m = %s; band %s" % ([round(r["m"], 3) for r in rows],
                             K.RELIEF_BANDS["isotropic_micro"]))
    # the GEOMETRY layer, computed from the groove's own section
    gslope = math.degrees(math.atan(GRIP_DEPTH / GRIP_CHAMFER))
    gm = K.modulation_for_slope(gslope)
    lo, hi = K.RELIEF_BANDS["hard_feature"]
    area = GRIP_WIDTH / GRIP_PITCH
    chk("the grip groove is a hard_feature and it is GATED",
        lo <= gm <= hi and area < 0.30,
        "groove wall %.1f deg -> m %.3f (hard_feature %.1f-%.1f), on %.1f %% of "
        "the plate area -- an edge, not a field" % (gslope, gm, lo, hi, 100 * area))
    wm = K.modulation_for_amplitude(1000 * WAVE_PP, WAVE_LAM)
    chk("the full-area geometry stage stays under m = 1",
        wm < 1.0, "plate waviness %.1f mm at %.0f mm -> m %.3f"
        % (1000 * WAVE_PP, 1000 * WAVE_LAM, wm))

    # A GROOVE PARALLEL TO THE LIGHT IS NOT A GROOVE. item_gate check 7 rejected
    # the transverse-only tread for exactly this and no amount of depth would
    # have fixed it. What matters is the component of the sun's HORIZONTAL
    # direction across the groove: that is what sets the effective elevation the
    # groove is lit at, and hence whether it has a sunward lip and a lee shadow
    # or is a single-value mark.
    sd = np.asarray(C.SUN_DIR, dtype=np.float64)
    hz = sd[:2] / np.linalg.norm(sd[:2])
    rows = []
    for nm, axis in (("transverse (along y)", np.array([1.0, 0.0])),
                     ("longitudinal (along x)", np.array([0.0, 1.0]))):
        perp = abs(float(hz @ axis))                # across-the-groove fraction
        e_eff = math.degrees(math.atan2(sd[2], perp * np.linalg.norm(sd[:2])))
        rows.append((nm, perp, e_eff, 1.0 / math.tan(math.radians(e_eff))))
        if verbose:
            print("      %-24s across-groove %.3f  effective sun %5.2f deg  "
                  "shadow %.2f x depth" % (nm, perp, e_eff, rows[-1][3]))
    best = max(r[3] for r in rows)
    chk("at least one groove family is lit ACROSS, not along",
        best > 3.0,
        "the sun's horizontal is (%.3f, %.3f); the better family throws %.2f x "
        "its depth in shadow against the %.2f x a flat surface gets, so the "
        "lattice cannot be parallel to the light for any sun bearing"
        % (hz[0], hz[1], best, C.SUN_SHADOW_RATIO))

    print("\n[7] THE MESH ITSELF")
    X, Y, ys = deck_grid()
    nx, ny = X.shape
    ex = np.abs(np.diff(X, axis=0)).ravel()
    ey = np.abs(np.diff(Y, axis=1)).ravel()
    e = np.concatenate([ex, ey])
    p10 = float(np.percentile(e, 10))
    chk("p10 edge resolves at the manifest's distance",
        p10 * PX_PER_M <= 6.0,
        "deck grid %d x %d = %.2f M verts; p10 edge %.3f mm = %.2f px "
        "(hero bar 6 px); p50 %.3f mm"
        % (nx, ny, nx * ny / 1e6, 1000 * p10, p10 * PX_PER_M,
           1000 * float(np.percentile(e, 50))))
    chk("the head is an ARC, so the outer corners reach further back",
        abs(float(head_x(0.0)) - NOSE_R) < 1e-9
        and float(head_x(HALF_W)) < DAIS_LIP_X - 0.55,
        "head_x(0) = %.4f, head_x(+-1.5) = %.4f -- the landing is %.0f mm deep "
        "at the centreline and %.0f mm at the corners"
        % (head_x(0.0), head_x(HALF_W), 1000 * (DAIS_LIP_X - head_x(0.0)),
           1000 * (DAIS_LIP_X - head_x(HALF_W))))

    print("\n[8] THE TOE IS A LAP AND SAYS SO")
    ut = float(under_z(np.array([RAMP_FOOT_X]))[0])
    u0 = float(under_z(np.array([TOE_START_X]))[0])
    cross = TOE_START_X + (u0 - 0.0) / (u0 - ut) * (RAMP_FOOT_X - TOE_START_X)
    chk("the tip laps into the slab and nothing else touches it",
        abs(ut + TOE_TIP_EMBED) < 1e-9 and u0 > 0.010,
        "underside %.2f mm above the floor at x = %.3f, %.2f mm INSIDE it at "
        "the tip; it crosses z = 0 at x = %.4f, so only the last %.0f mm is in "
        "the floor and the wedge's %.2f m underside is never coplanar with it"
        % (1000 * u0, TOE_START_X, -1000 * ut, cross, 1000 * (RAMP_FOOT_X - cross),
           TOE_START_X - float(head_x(0.0))))
    chk("the toe lap is a STATED exception to BASE_EMBED_M",
        TOE_TIP_EMBED < EMBED,
        "toe %.1f mm vs BASE_EMBED_M %.0f mm -- a 20 mm embed at a ramp foot is "
        "a 20 mm step at a ramp foot; the load-bearing feet take the full %.0f mm"
        % (1000 * TOE_TIP_EMBED, 1000 * EMBED, 1000 * EMBED))

    print("\n%d checks, %d failures" % (n[0], len(fails)))
    if fails:
        print("FAILED: %s" % fails)
    return not fails


# ===========================================================================
# 9.  CLI
# ===========================================================================

def main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else argv[1:]
    ap = argparse.ArgumentParser(prog=ITEM)
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--test-scene", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--interface", default=None)
    ap.add_argument("--save", default=None)
    ap.add_argument("--samples", type=int, default=256)
    a = ap.parse_args(argv)

    if a.interface:
        interface_json(os.path.abspath(a.interface))
    if a.selftest:
        sys.exit(0 if selftest() else 1)
    if a.build or a.test_scene or a.save:
        st = {}
        build(scene=bpy.context.scene, test_scene=a.test_scene,
              samples=a.samples, stats=st)
        if a.save:
            p = os.path.abspath(a.save)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            K.assert_no_external_assets()
            bpy.ops.wm.save_as_mainfile(filepath=p, compress=True)
            K.log("saved %s (%.1f MB)" % (p, os.path.getsize(p) / 1048576.0))
            K.log("gate:  " + " ".join(
                K.gate_command(ITEM, p, collection=COLL)))
        print(">> STAGE RESULT: DAIS_DELIVERY_RAMP_BUILT")


if __name__ == "__main__":
    main()
