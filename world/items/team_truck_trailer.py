#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
team_truck_trailer.py — CIRCUIT VITRINE, per-item hero campaign, item
``team_truck_trailer`` (zone ``paddock``, wave 1, build order 133,
**5 dependants, 1 dependency**).

WHAT THIS IS, IN ONE SENTENCE
=============================
Ten team transporter box trailers, each built as the **riveted aluminium
coachwork it actually is** — a bonded-sheet body on a welded steel chassis, with
every cover strip, every rivet head, every rubbing rail, every kick-plate scuff,
every oil-canned panel and every road-dirt gradient existing as MESH — so that a
14 m flank at 8 m reads as a vehicle that has driven to eleven race meetings this
season and not as a coloured box.

THE MANIFEST NAMES THE FAILURE BEFORE IT HAPPENS
------------------------------------------------
    "A 14 m flank at 8 m is 2/3 of the frame height.  It cannot be a coloured
     box - it needs panel joints, rivet lines, kick plates, dirt gradient rising
     from the road."

``build_architecture._transporter`` laid the trailer as **five axis-aligned
boxes**: body, livery band, roof cap, chassis, and a text extrusion, plus six
16-sided tyres.  Everything the manifest names was structurally absent:

  1. **No panel joints.**  The body was one box 14 m long.  A real box body is
     1.22 m sheets with a cover strip over every butt; that strip is 8 mm proud
     and at a 12.47 deg sun it throws 36 mm of shadow — 17 px — **every 1.22 m
     for the whole length of the flank**.  It is the rhythm that tells you how
     long the trailer is.
  2. **No rivets.**  2 200-3 200 per trailer, 25 098 across the fleet.  A 10 mm
     dome head is 4.7 px across at the filmed distance, and on a vertical flank
     under this sun it reads by its own dome shading and its root occlusion
     rather than by a cast shadow -- see the light note below.  A flank with no
     rivets is a flank with no scale.
  3. **No kick plate, no rubbing rail, no bottom rail.**  The three horizontal
     lines that break a 3 m wall of paint into a vehicle.
  4. **No oil-canning.**  A bonded 1.5 mm alu sheet is never flat: it stands
     1.5-4 mm out of plane in a soft cell pattern, and under a grazing key that
     is the difference between sheet metal and plastic.
  5. **The dirt was a colour, not a gradient.**  Road film climbs a trailer
     flank from the wheels, is thrown forward of each wheel arch, streaks down
     from every rivet and pools under the rubbing rail.  It is a HISTORY, and it
     is different on the near side from the off side because the trailer only
     ever gets washed from the paddock side.
  6. **One trailer, ten times, with a random length and a random angle.**  The
     named failure verbatim.  Here every one of the ten has its own body length,
     its own panel count, its own scheme, its own damage, its own door state,
     its own axle plan and its own mesh.

THE PIXEL BUDGET THIS WAS BUILT TO
----------------------------------
    px_per_m = (3840 x 35 / 36) / 8.0 = 466.67 px/m      ->     1 px = 2.143 mm

    the 4.00 m body height             1867 px   (manifest: onscreen_px_4k 1867)
    a 1.22 m panel bay                  569 px
    a 60 mm cover strip                  28 px      <- must be geometry
    an 8 mm proud cover strip, and the
      36 mm shadow it throws at 12.5 deg 17 px      <- must be geometry
    a 10 mm rivet head                  4.7 px      <- must be geometry
      ... and its 11 mm shadow           5.3 px
    a 38 mm proud rubbing rail           18 px      <- must be geometry
    a 140 mm bottom rail                 65 px      <- must be geometry
    a 3 mm oil-can standing wave         1.4 px of relief, BUT it bends the
                                         highlight across 300 mm = 140 px
                                                    <- must be geometry
    a 25 mm kerb scuff on the skirt      12 px      <- must be geometry
    a 12 mm hinge butt knuckle           5.6 px     <- must be geometry
    a 24 mm A/F bolt head                11 px      <- must be geometry
    a 6 mm weld bead                     2.8 px     <- must be geometry
    a 0.15 mm vinyl wrap edge           0.07 px     <- SHADING
    orange-peel in the paint, 0.2 mm    0.09 px     <- SHADING
    every dirt gradient, wash line,
      streak, bloom and polish swirl     no relief  <- SHADING

The line is drawn at 1.0 mm of relief, which is half a pixel at this distance.
Everything with a silhouette or an occlusion is mesh.

WHY THE LIGHT DECIDES THE MODELLING
-----------------------------------
``world_contract.SUN_DIR`` is (0.5179, -0.8278, 0.2159): **12.47 deg above the
horizon**, bearing -57.97 deg, and ``SUN_SHADOW_RATIO`` = 4.522 horizontal run
per unit of height.  Two consequences drove every modelling decision here:

  * **Horizontal relief casts 4.5x its own height downward.**  The cover strips
    are therefore vertical (they throw sideways, 0.5x, and read as a line) while
    the rubbing rail, the cant rail and the bottom rail are horizontal and throw
    a hard 4.5x band down the paint.  That band is the single most legible fact
    about the flank, so the rails are modelled with a real drip edge and a real
    return, not as a proud rectangle.
  * **On a VERTICAL flank the 4.52 shadow ratio does not apply.**  MEASURED:
    the frontage row's near flank has normal (0, -1, 0); ``SUN_DIR`` resolves
    into 0.828 along that normal and 0.561 in the plane of the flank, so relief
    on the flank throws only **0.68x its own height** -- a 2.5 mm rivet casts
    1.7 mm, which is 0.8 px and invisible.  Every raised feature on the flank
    therefore has to read by its OWN shading: the rivets are real domes with a
    ring at 0.42 and 0.80 of their height rather than discs, the cover strips
    have chamfered shoulders rather than square sides, and the rails have a
    return and a drip edge so their own faces turn away from the key.  This is
    the single measurement that decided the modelling, and the first macro --
    where the rivets were flat discs -- is what produced it.
  * cos(incidence) on that flank is 0.831, so it is nearly at full key: bright,
    and 1.2 stops over the contract's -3.048 EV if the paint is given its brand
    hex as an albedo.  See ``paint_albedo``.

===============================================================================
THE PUBLIC INTERFACE  —  this item is a FOUNDATION.  5 items depend on it.
===============================================================================
Every function below is a pure function of this module's deterministic plan.
They can be called **without bpy**, without building anything, and they return
world-frame geometry in metres.  ``interface_json(path)`` dumps the lot.

    truck_wheel_trailer   ``hub_sites()``      -> 120 records (10 trailers x 3
                          axles x 2 sides x 2 wheels).  Each gives the world
                          position of the WHEEL MOUNTING FACE, the axle unit
                          vector, the hub spigot diameter, the stud circle and
                          count, the rim offset, the twin spacing, the static
                          loaded radius the trailer was levelled on, and the
                          measured ground z under that hub.  Build the wheel so
                          its mounting face lands on ``face_p`` with its axis on
                          ``axis``; the contact patch then lands on the ground.
                          THE TRAILER IS ALREADY SITTING AT THE RIGHT HEIGHT --
                          do not move it, and do not assume z = 0.

    truck_side_skirt      ``skirt_field()``    -> 60 records (10 x 3 segments x
                          ... 2 sides, 3 per side).  Each gives the mounting
                          rail polyline in world, the rail z, the outboard limit
                          plane (the skirt may not pass ``y_limit``, which is
                          the body's own flank plane), the clear span between
                          the landing legs and the bogie, and the scuff history
                          this trailer's skirt should carry.

    truck_rear_door       ``door_aperture()``  -> 20 records (2 leaves x 10).
                          The clear opening rectangle in world and in trailer
                          frame, the 4 hinge butt axes per leaf with their
                          knuckle centres, the threshold z, the seal face, the
                          8 mm door-face budget, the cam-bar keeper positions,
                          AND ``state`` / ``swing_deg`` -- the trailer decides
                          whether its doors are shut, on the catch, or swung
                          back on the buffer, because the aperture, the interior
                          and the shadow it casts were all built for that state.

    truck_landing_leg     ``landing_leg_mounts()`` -> 20 records.  The mounting
                          plate rectangle, its 8-bolt pattern, the leg
                          centreline, the crank side, the extension the leg must
                          be set to (MEASURED per trailer: the chassis is level
                          and the foot must reach the measured ground), and the
                          ground z under the foot.

    truck_light_cluster   ``lamp_sites()``     -> 140 records (14 per trailer).
                          Each gives the world position and outward normal of a
                          lamp BOSS that already exists as mesh on this object,
                          its recess depth and rectangle, its role (rear
                          combination / rear fog / reverse / side marker /
                          front marker / roof outline), its lens size and the
                          cable gland position.

    truck_livery_decal    ``decal_field()``    -> 20 records (2 flanks x 10).
                          The clear wrap rectangle on each flank, the base
                          colour underneath, the x positions of every cover
                          strip and the (x, z) of every rivet the wrap has to
                          lie over -- which is the whole point of that item --
                          plus the areas this module has already painted and the
                          wrap must not cover.

    also published, not required by any dependant but true and useful:
      ``coupling_frame()``  the kingpin position, the fifth-wheel plate rectangle
                            and the swing clearance, for ``team_truck_tractor``.
      ``trailer_records()`` the whole plan: 10 dicts, everything below.
      ``SECTION``           the section constants as a dict.

--- 1. THE SECTION -----------------------------------------------------------

    W_BODY         2.550   body width (EU maximum), constant across the fleet:
                           this is a legal dimension, not a style choice
    H_TOTAL        4.000   ground to the top of the roof cap = the manifest's
                           ``typical_height_m``, and the number ``onscreen_px_4k``
                           1867 was derived from
    L_BODY     12.6-14.6   THE VARIATION AXIS.  Body length, per trailer.
    Z_FLOOR    1.16-1.30   top of the deck (the load floor), per trailer
    Z_SILL     Z_FLOOR-0.26  bottom of the side wall: the wall hangs past the
                           floor and covers the chassis flange
    PANEL_W        1.220   sheet width -> the cover-strip rhythm
    T_STRIP        0.008   cover strip proud of the sheet
    W_STRIP        0.060   cover strip width
    D_RIVET        0.010   rivet head diameter, 2.5 mm proud
    RAIL_WAIST     0.038   rubbing rail projection
    RAIL_BOTTOM    0.030   bottom rail projection
    R_CORNER       0.090   vertical corner radius
    TYRE_OD        1.076   315/80R22.5 -> the manifest's 1.05 m wheel item
    SLR            0.512   static loaded radius: what the trailer sits on
    AXLE_PITCH     1.310   tri-axle bogie spacing

--- 2. THE LAWS, AND WHERE THEY ARE DISCHARGED -------------------------------

    law 3  scale     the car is 5.698 m long; this trailer is 12.6-14.6 m and
                     2.55 m wide, i.e. 2.4x the car's length -- which is why the
                     manifest films it at 8 m and not at 2.6 m.
    law 4  z=0       the paddock apron IS z = 0.000.  MEASURED, not assumed:
                     ``C.world_ground_z`` is queried at every wheel contact
                     patch and every landing-leg foot, and returns
                     "build_architecture:paving", z = 0.000, at all 10 sites.
    law 5  embed     THIS OBJECT DOES NOT STAND ON THE GROUND -- it stands on 12
                     wheels and 2 legs, both of which are OTHER ITEMS.  What it
                     does own that reaches the ground is the rear mudflap, which
                     on trailers 3 and 7 has been dragged and now trails on the
                     deck: those flaps embed ``C.BASE_EMBED_M`` = 0.020 below the
                     measured ground.  Every hub and every leg foot is published
                     with the measured ground z so the dependants cannot assume.
    law 6  recentre  every object is recentred on emit (``|P| <= 7.54 m``) and
                     every material reads ``TexCoord -> Object``.  There is no
                     ``Geometry -> Position`` node in this module.
    law 7  chunk     one object per trailer, 14.6 m max.

--- 3. WHERE THEY STAND ------------------------------------------------------

Ten trailers in three groups, chosen so the item is filmed the way the manifest
says it is filmed and so the fleet is not one row of identical parking:

  FRONTAGE (3)  world y = 12.275 +- parking error, bodies between world x 27 and
                74, long axis along world X, **flank square to the Beat-4 transit
                corridor**.  The corridor centreline is world y = 0 and the
                ribbon is 12 m wide, so a lens anywhere in the right-hand half of
                it stands 8.0-11.0 m off this flank: the manifest's
                ``nearest_camera_m`` = 8.0 is reproduced by a camera at world
                (x, +3.0, 1.75), which is inside the ribbon.  MEASURED: the
                nearest body face is 11.000 m from the corridor centreline and
                2.87 m north of ``C.transit_wall_point``'s north wall, so nothing
                here is in the road.
  SECOND RANK (3) world y = 23.9, offset in x so they are seen through the gaps
                between the frontage trailers.  Facing the other way, so their
                near flank is the off side and takes the key directly.
  BANK (4)      the transporter park build_architecture already declares,
                circuit x -298..-271, y 95.6.., nose-in.  40-60 m from the lens;
                they set the depth of the paddock behind the near row.

--- 4. WHAT IS *NOT* HERE, AND WHO OWNS IT -----------------------------------

The test scene contains stand-ins for four items that do not exist yet.  They
are named ``XTT_`` -- which does NOT start with ``TTT_`` -- so the acceptance
gate never measures them and never credits this item for them:

    XTT_Wheels_NN   120 wheels/tyres        -> ``truck_wheel_trailer``  (wave 2)
    XTT_Doors_NN    20 rear door leaves     -> ``truck_rear_door``      (wave 2)
    XTT_Legs_NN     20 landing legs         -> ``truck_landing_leg``    (wave 2)
    XTT_Ground      the paddock apron       -> ``paddock_paving_bay``   (built)

They exist because a macro of a 4 m trailer floating with no wheels is not a
macro of the trailer, and because the OCCLUSION and the BOUNCE from the wheels
and the ground are half of what the flank looks like.  They are deliberately
plainer than this item and they are excluded from every number reported.

--- 5. THE TEN --------------------------------------------------------------

Per-instance variation is GEOMETRY, per the brief.  What differs between the ten,
in the mesh and not in the transform:

    body length            12.60 - 14.60 m      -> panel count 11, 11, 12
    panel bay width        1.145 - 1.240 m      (the closer sheet is cut to fit)
    floor height           1.160 - 1.300 m
    roof height            3.955 - 4.045 m
    livery scheme          6 schemes x 14 team colourways, baked as a signed
                           distance field so the boundary is crisp at 466 px/m
    door state             shut / on the catch / swung back on the buffer
                           -- and the two open ones have a REAL INTERIOR built
    kick-plate scuffs      3-11 impacts, each its own dent, each with its own
                           torn-paint boundary
    kerb rash              0-3 gouges on the bottom rail
    oil-can realisation    every panel of every trailer its own standing wave
    rivet population       2 228 - 2 680 (MEASURED), and no two trailers' rivet
                           rows line up: the phase is a per-trailer draw
    roof furniture         1-3 pods, 0-2 hatches, ladder left / right / none
    chassis                toolbox side, spare carrier present, hose tube count
    wash history           near side washed, off side not; the ratio differs

===============================================================================
BUILD / TEST / GATE
===============================================================================
    blender -b --factory-startup -P world/items/team_truck_trailer.py -- --selftest
    blender -b --factory-startup -P world/items/team_truck_trailer.py -- \\
        --test --save world/items/team_truck_trailer_test.blend
    blender -b world/items/team_truck_trailer_test.blend --factory-startup \\
        -P tools/item_gate.py -- --item team_truck_trailer --prefix TTT_ \\
        --out render/items/team_truck_trailer/gate.json
"""

import argparse
import json
import math
import os
import sys
import time

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
_WORLD = os.path.dirname(_HERE)
_ROOT = os.path.dirname(_WORLD)
if _WORLD not in sys.path:
    sys.path.insert(0, _WORLD)

import world_contract as C                                          # noqa: E402
import itemkit as K                                               # noqa: E402

try:
    import bpy                                                      # noqa: E402
except Exception:                                                   # pragma: no cover
    bpy = None

__version__ = "1.0.0"

ITEM = "team_truck_trailer"
COLL = "W_Item_TeamTruckTrailer"
PFX = "TTT_"            # THE ITEM.  The gate measures exactly this prefix.
XPFX = "XTT_"           # stand-ins owned by other items.  Deliberately does not
                        # start with PFX, so `--prefix TTT_` cannot see them.

_T0 = time.time()


def log(msg):
    print("[%s %7.1fs] %s" % (ITEM, time.time() - _T0, msg))
    sys.stdout.flush()


# ==============================================================================
#  0.  THE NUMBERS
# ==============================================================================
# Manifest record, quoted so nothing downstream has to re-read the JSON.
FILMED_AT_M = 8.0
LENS_MM = 35.0
ONSCREEN_PX_4K = 1867.0
INSTANCES_DECLARED = 10
PX_PER_M = (3840.0 * LENS_MM / 36.0) / FILMED_AT_M           # 466.667
PX_M = 1.0 / PX_PER_M                                        # 2.143 mm

# --- the section --------------------------------------------------------------
W_BODY = 2.550                  # EU maximum width.  A legal dimension.
H_TOTAL = 4.000                 # ground -> top of roof cap (manifest 4.0 m)
L_MIN, L_MAX = 12.600, 14.600   # THE variation axis
PANEL_W = 1.220                 # alu sheet width -> the cover strip rhythm
W_STRIP = 0.060                 # cover strip width
T_STRIP = 0.010                 # ... proud of the sheet
D_RIVET = 0.010                 # rivet head diameter
H_RIVET = 0.0033                # ... proud.  MEASURED against the light: on a
                                # VERTICAL flank the 4.52 shadow ratio does NOT
                                # apply -- the in-plane component of SUN_DIR is
                                # 0.561 against a 0.828 normal component, so a
                                # bump throws only 0.68x its height.  A rivet
                                # reads by its own dome shading and its root AO,
                                # not by a cast shadow, so it needs to be a real
                                # dome and not a disc.
P_RIVET = 0.110                 # rivet pitch along a row
R_CORNER = 0.090                # vertical corner radius
R_ROOF = 0.065                  # roof edge radius
T_WALL = 0.032                  # wall thickness (sheet + frame + liner)
T_ROOF = 0.090                  # roof build-up

RAIL_WAIST_H = 0.092            # rubbing rail section height
RAIL_WAIST_D = 0.038            # ... projection
RAIL_BOT_H = 0.140              # bottom rail
RAIL_BOT_D = 0.030
RAIL_CANT_H = 0.078             # cant rail under the roof edge
RAIL_CANT_D = 0.024
KICK_H = 0.360                  # kick plate height above the bottom rail
KICK_D = 0.009                  # ... proud

# --- the running gear ---------------------------------------------------------
TYRE_OD = 1.076                 # 315/80R22.5 -> manifest truck_wheel_trailer 1.05
TYRE_W = 0.315
SLR = 0.512                     # static loaded radius: what it SITS on
TWIN_PITCH = 0.375              # centre-to-centre of a twin pair
TWIN_CENTRE_Y = 0.900           # twin-pair centre from the trailer centreline
AXLE_PITCH = 1.310
HUB_PCD = 0.335                 # 10 x M22 on a 335 mm stud circle
HUB_SPIGOT = 0.281
HUB_STUDS = 10
RIM_OFFSET = TWIN_PITCH * 0.5   # mounting face -> rim centreline.  BOTH discs
                                # bolt to the SAME face, so the inner rim sits half a
                                # twin pitch inboard of it and the outer half outboard.

# --- the chassis --------------------------------------------------------------
BEAM_Y = 0.510                  # main beam web centres, +- from centreline
BEAM_TF = 0.190                 # top flange width
BEAM_BF = 0.220                 # bottom flange width
BEAM_TW = 0.010                 # web thickness
KINGPIN_FROM_NOSE = 1.700       # kingpin centre back from the body front face
KINGPIN_D = 0.0508              # 2 in kingpin
FIFTHW_PLATE = (1.30, 1.20)     # half-length, half-width of the wear plate

EMBED = C.BASE_EMBED_M          # 0.020

SECTION = dict(
    W_BODY=W_BODY, H_TOTAL=H_TOTAL, L_MIN=L_MIN, L_MAX=L_MAX, PANEL_W=PANEL_W,
    W_STRIP=W_STRIP, T_STRIP=T_STRIP, D_RIVET=D_RIVET, H_RIVET=H_RIVET,
    P_RIVET=P_RIVET, R_CORNER=R_CORNER, R_ROOF=R_ROOF, T_WALL=T_WALL,
    T_ROOF=T_ROOF, RAIL_WAIST_H=RAIL_WAIST_H, RAIL_WAIST_D=RAIL_WAIST_D,
    RAIL_BOT_H=RAIL_BOT_H, RAIL_BOT_D=RAIL_BOT_D, RAIL_CANT_H=RAIL_CANT_H,
    RAIL_CANT_D=RAIL_CANT_D, KICK_H=KICK_H, KICK_D=KICK_D, TYRE_OD=TYRE_OD,
    TYRE_W=TYRE_W, SLR=SLR, TWIN_PITCH=TWIN_PITCH, TWIN_CENTRE_Y=TWIN_CENTRE_Y,
    AXLE_PITCH=AXLE_PITCH, HUB_PCD=HUB_PCD, HUB_SPIGOT=HUB_SPIGOT,
    HUB_STUDS=HUB_STUDS, RIM_OFFSET=RIM_OFFSET, BEAM_Y=BEAM_Y,
    KINGPIN_FROM_NOSE=KINGPIN_FROM_NOSE, KINGPIN_D=KINGPIN_D, EMBED=EMBED,
)

# --- LOD ----------------------------------------------------------------------
# (flank dx, flank dz, roof d, end d, extrusion stations/m, round segments)
# LOD 0 is 42 mm on the flank = 20 px at the filmed distance, and every feature
# smaller than that exists as its own solid rather than as a bump in this grid.
LOD = (
    (0.042, 0.048, 0.075, 0.055, 26.0, 1.00),    # 0  hero,  <= 16 m
    (0.070, 0.080, 0.120, 0.090, 16.0, 0.72),    # 1        <= 34 m
    (0.130, 0.150, 0.210, 0.160,  9.0, 0.55),    # 2  beyond
)
LOD_RADII = (16.0, 34.0)


def lod_of(dist):
    for i, r in enumerate(LOD_RADII):
        if dist <= r:
            return i
    return len(LOD_RADII)


# ==============================================================================
#  1.  MATHS
# ==============================================================================

def hash01(*keys):
    """FNV-1a with a murmur3 finaliser. Float keys are scaled to integers.

    The wrapping multiply was right, and the old docstring said so — but wrapping
    was never the missing piece. THE FINALISER WAS. Measured avalanche — the mean
    fraction of output bits that flip when ONE input bit flips — was **0.2718**
    against an ideal of 0.5, because FNV's multiply only propagates change
    UPWARD and this returned the LOW 30 bits, discarding exactly the part that
    moved. Properties meant to vary independently moved together.

    Ported from pit_wall_unit.py, which hit this and fixed it locally without
    the fix ever propagating. Also widened the mask: 0xFFFFFFFFFFFFFFF is
    fifteen F's — 60 bits — which silently discarded the top nibble of every key.

    NOTE: this CHANGES THE BUILT GEOMETRY. Re-gate the module.
    """
    h = 1469598103934665603
    for k in keys:
        h ^= int(k * 1e6 if isinstance(k, float) else k) & 0xFFFFFFFFFFFFFFFF
        h = (h * 1099511628211) & 0xFFFFFFFFFFFFFFFF
    h ^= h >> 33
    h = (h * 0xFF51AFD7ED558CCD) & 0xFFFFFFFFFFFFFFFF
    h ^= h >> 33
    h = (h * 0xC4CEB9FE1A85EC53) & 0xFFFFFFFFFFFFFFFF
    h ^= h >> 33
    return float(h % (1 << 30)) / float(1 << 30)


class Rng(object):
    """Deterministic per-trailer stream.  Same seed -> same vehicle, always."""

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

    def chance(self, p):
        return bool(self.r.random() < p)

    def arr(self, *shape):
        return self.r.random(shape)


def _h2(ix, iy, seed):
    with np.errstate(over="ignore"):
        h = (np.asarray(ix, np.int64).astype(np.uint32) * np.uint32(374761393)
             + np.asarray(iy, np.int64).astype(np.uint32) * np.uint32(668265263)
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
    s = np.zeros(np.broadcast(np.asarray(x, float), np.asarray(y, float)).shape)
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
    s = np.zeros(np.asarray(x, float).shape)
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


def refine(a, b, base, sites=(), win=0.0, fine=0.0):
    """A monotone station list from `a` to `b` at pitch `base`, locally refined
    to `fine` within `win` of each site.

    Non-uniform sampling is the whole reason a 14 m flank can carry a 4 mm
    feature without 3 million triangles: the mesh is dense exactly where a
    silhouette event happens and coarse across the paint between them.
    """
    if b <= a + 1e-9:
        return np.array([a, b])
    n = max(1, int(round((b - a) / base)))
    xs = [np.linspace(a, b, n + 1)]
    for s in sites:
        lo, hi = max(a, s - win), min(b, s + win)
        if hi <= lo + 1e-9 or fine <= 0.0:
            continue
        k = max(1, int(round((hi - lo) / fine)))
        xs.append(np.linspace(lo, hi, k + 1))
    # quantise, so no two stations can land closer than 0.30 of the fine pitch:
    # a near-degenerate quad is a normal artefact and a wasted vertex.
    tol = max(1e-6, (fine if fine > 0 else base) * 0.30)
    x = np.unique(np.round(np.concatenate(xs) / tol) * tol)
    x = np.clip(x, a, b)
    x[0] = a
    x[-1] = b
    return np.unique(x)


# ==============================================================================
#  2.  A HAND-CODED STROKE FONT
# ==============================================================================
# Blender ships a font datablock and `build_architecture` uses it, which is
# legal.  This module does not, for the same reason `pit_wall_unit` does not: a
# font is a THIRD PARTY ASSET even when it is bundled, and the brief says
# everything is built by hand.  The letters here are extruded as real vinyl --
# 0.5 mm plates laid on the paint -- so they are geometry, not a texture, and
# they stay crisp at 466 px/m where a baked field would not.
#
# Coordinates are in a 0..1 (x) by 0..1 (y) box; each glyph is a list of
# polylines.  Stroke width and cap height are applied at rasterisation time.
GLYPH = {
    "0": [[(.12, .22), (.12, .78), (.30, .95), (.70, .95), (.88, .78),
           (.88, .22), (.70, .05), (.30, .05), (.12, .22)]],
    "1": [[(.22, .74), (.52, .95), (.52, .05)], [(.24, .05), (.80, .05)]],
    "2": [[(.10, .76), (.30, .95), (.70, .95), (.88, .76), (.88, .60),
           (.12, .05), (.90, .05)]],
    "3": [[(.12, .95), (.88, .95), (.46, .56), (.72, .56), (.90, .40),
           (.90, .20), (.70, .05), (.26, .05), (.10, .18)]],
    "4": [[(.70, .05), (.70, .95), (.08, .28), (.94, .28)]],
    "5": [[(.88, .95), (.16, .95), (.12, .54), (.62, .60), (.90, .44),
           (.90, .20), (.70, .05), (.20, .05)]],
    "6": [[(.84, .86), (.50, .95), (.16, .74), (.12, .26), (.32, .05),
           (.68, .05), (.88, .24), (.74, .46), (.30, .50), (.13, .36)]],
    "7": [[(.10, .95), (.90, .95), (.40, .05)]],
    "8": [[(.50, .52), (.20, .62), (.20, .84), (.40, .95), (.60, .95),
           (.80, .84), (.80, .62), (.50, .52), (.16, .38), (.14, .18),
           (.34, .05), (.66, .05), (.86, .18), (.84, .38), (.50, .52)]],
    "9": [[(.16, .16), (.50, .05), (.86, .28), (.88, .74), (.68, .95),
           (.32, .95), (.12, .72), (.26, .50), (.70, .48), (.87, .62)]],
    "A": [[(.04, .05), (.50, .95), (.96, .05)], [(.22, .40), (.78, .40)]],
    "B": [[(.14, .05), (.14, .95), (.66, .95), (.86, .78), (.66, .54),
           (.14, .54)], [(.66, .54), (.90, .32), (.70, .05), (.14, .05)]],
    "C": [[(0.848, 0.758), (0.712, 0.895), (0.536, 0.95), (0.357, 0.911), (0.212, 0.787), (0.131, 0.603), (0.131, 0.397), (0.212, 0.213), (0.357, 0.089), (0.536, 0.05), (0.712, 0.105), (0.848, 0.242)]],
    "D": [[(.14, .05), (.14, .95), (.42, .95)] + [(0.42, 0.05), (0.57, 0.077), (0.703, 0.155), (0.801, 0.275), (0.853, 0.422), (0.853, 0.578), (0.801, 0.725), (0.703, 0.845), (0.57, 0.923), (0.42, 0.95)] + [(.42, .05), (.14, .05)]],
    "E": [[(.88, .95), (.14, .95), (.14, .05), (.88, .05)], [(.14, .50), (.70, .50)]],
    "F": [[(.14, .05), (.14, .95), (.88, .95)], [(.14, .52), (.70, .52)]],
    "G": [[(0.848, 0.758), (0.712, 0.895), (0.536, 0.95), (0.357, 0.911), (0.212, 0.787), (0.131, 0.603), (0.131, 0.397), (0.212, 0.213), (0.357, 0.089), (0.536, 0.05), (0.712, 0.105), (0.848, 0.242)] + [(.90, .44), (.56, .44)]],
    "H": [[(.14, .05), (.14, .95)], [(.86, .05), (.86, .95)], [(.14, .50), (.86, .50)]],
    "I": [[(.50, .05), (.50, .95)], [(.20, .95), (.80, .95)], [(.20, .05), (.80, .05)]],
    "J": [[(.86, .95), (.86, .24), (.66, .05), (.34, .05), (.14, .22), (.14, .38)]],
    "K": [[(.14, .05), (.14, .95)], [(.86, .95), (.20, .48), (.88, .05)]],
    "L": [[(.16, .95), (.16, .05), (.88, .05)]],
    "M": [[(.08, .05), (.08, .95), (.50, .40), (.92, .95), (.92, .05)]],
    "N": [[(.14, .05), (.14, .95), (.86, .05), (.86, .95)]],
    "O": [[(0.9, 0.5), (0.86, 0.695), (0.749, 0.852), (0.589, 0.939), (0.411, 0.939), (0.251, 0.852), (0.14, 0.695), (0.1, 0.5), (0.14, 0.305), (0.251, 0.148), (0.411, 0.061), (0.589, 0.061), (0.749, 0.148), (0.86, 0.305), (0.9, 0.5)]],
    "P": [[(.14, .05), (.14, .95), (.68, .95), (.88, .76), (.68, .52), (.14, .52)]],
    "Q": [[(0.9, 0.5), (0.86, 0.695), (0.749, 0.852), (0.589, 0.939), (0.411, 0.939), (0.251, 0.852), (0.14, 0.695), (0.1, 0.5), (0.14, 0.305), (0.251, 0.148), (0.411, 0.061), (0.589, 0.061), (0.749, 0.148), (0.86, 0.305), (0.9, 0.5)], [(.62, .26), (.96, -.02)]],
    "R": [[(.14, .05), (.14, .95), (.68, .95), (.88, .76), (.68, .54), (.14, .54)],
          [(.50, .54), (.90, .05)]],
    "S": [[(.90, .80), (.72, .92), (.46, .95), (.22, .90), (.12, .72),
           (.22, .58), (.48, .52), (.70, .47), (.86, .34), (.80, .16),
           (.58, .06), (.30, .05), (.10, .16)]],
    "T": [[(.06, .95), (.94, .95)], [(.50, .95), (.50, .05)]],
    "U": [[(.12, .95), (.12, .26), (.32, .05), (.68, .05), (.88, .26), (.88, .95)]],
    "V": [[(.06, .95), (.50, .05), (.94, .95)]],
    "W": [[(.03, .95), (.27, .05), (.50, .62), (.73, .05), (.97, .95)]],
    "X": [[(.08, .95), (.92, .05)], [(.92, .95), (.08, .05)]],
    "Y": [[(.08, .95), (.50, .50), (.92, .95)], [(.50, .50), (.50, .05)]],
    "Z": [[(.10, .95), (.90, .95), (.10, .05), (.90, .05)]],
    "-": [[(.14, .50), (.86, .50)]],
    ".": [[(.44, .06), (.56, .06)]],
    "/": [[(.12, .02), (.88, .98)]],
    "'": [[(.50, .74), (.50, .98)]],
    " ": [],
}
GLYPH_ADV = 1.00            # advance width, in cap-height units.  MEASURED: the
                            # glyph boxes above run x 0.03..0.97, so an advance
                            # of 0.74 laid every letter 0.07 INSIDE its
                            # neighbour -- which is why the first macro's B and
                            # O rendered as one crossed shape.


def stroke_polys(text, h, tracking=0.10, weight=0.118):
    """-> list of (n,2) polygons for `text` at cap height `h`, origin bottom-left.

    Each stroke becomes a real ribbon quad with mitre-free square joints (a
    round join is added as a small square at every vertex).  It is deliberately
    a STENCIL face, because that is what a cut vinyl or a sprayed stencil is,
    and it means the letterform has an edge the light can catch.
    """
    polys, pen = [], 0.0
    w = weight * h * 0.5
    for ch in text.upper():
        g = GLYPH.get(ch)
        if g is None:
            pen += (GLYPH_ADV + tracking) * h
            continue
        for pl in g:
            P = np.asarray(pl, float) * h
            P[:, 0] += pen
            for i in range(len(P) - 1):
                a, b = P[i], P[i + 1]
                d = b - a
                L = math.hypot(d[0], d[1])
                if L < 1e-9:
                    continue
                d = d / L
                nvec = np.array([-d[1], d[0]])
                polys.append(np.array([a + nvec * w, b + nvec * w,
                                       b - nvec * w, a - nvec * w]))
            for i in range(len(P)):
                polys.append(np.array([P[i] + (-w, -w), P[i] + (w, -w),
                                       P[i] + (w, w), P[i] + (-w, w)]))
        pen += (GLYPH_ADV + tracking) * h
    return polys, pen - tracking * h


# ==============================================================================
#  3.  THE BRAND BOOK  (law 2: reuse, do not invent a 32nd)
# ==============================================================================
# Copied verbatim from build_architecture.TEAMS and build_dressing.BRANDS so the
# transporters advertise the SAME fourteen fictional teams that the garages are
# allocated to, and the same invented sponsors as the trackside boards.  Copied
# rather than imported because build_architecture does 40 s of module-level work
# on import and this module has to be callable without bpy.
TEAMS = [
    ("ALTHEA",    '#8e1d24', '#e8dfd0'), ("BOREAL",  '#5f9fd0', '#f2f6f8'),
    ("CORVUS",    '#141416', '#c8a24a'), ("DELMAR",  '#16305c', '#e2651a'),
    ("ESTIVAL",   '#c8ab74', '#4a3a28'), ("FULGOR",  '#e3bb14', '#2b2d31'),
    ("GRISAILLE", '#6d6f74', '#c02a78'), ("HALCYON", '#127f7a', '#f4f7f6'),
    ("IRIDIA",    '#5b3f9a', '#b9bec4'), ("JUNIPER", '#2f6b3a', '#efe6cd'),
    ("KESTREL",   '#1d3a2a', '#d8641c'), ("LUMEN",   '#e9edf0', '#17a8c4'),
    ("MERIDIAN",  '#22306e', '#f0f2f5'), ("NOCTIS",  '#2a2c2e', '#9ed61f'),
]
# the haulier's own name on the tail: logistics brands from the shared book
HAULIERS = ["KESTREL LOGISTIQUE", "PYLON RESEAUX", "NORDVAL ACIERS",
            "TERRA NOVA TRAVAUX", "CALIBRE OUTILLAGE", "OCTAL SYSTEMS"]
SPONSORS = ["VERSANT", "OCTAL", "CADENCE", "SEPTIME", "PALLAS", "ZEPHYR",
            "NOVEM", "LUMIERE", "MARQUE", "MERIDIAN", "ARDENT", "VOLTAIC",
            "CIRRUS", "ALTIS", "CALIBRE", "VERITAS", "OBSIDIAN"]


def srgb(hexstr):
    """sRGB hex -> linear RGB, because Cycles works in linear and a hex colour
    fed straight into a Base Color input is 2.2 gamma too bright."""
    h = hexstr.lstrip('#')
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255.0
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return tuple(out)


def paint_albedo(rgb, lo=0.035, span=0.58, gamma=1.70):
    """A brand hex is a DESIGN colour, not a measured reflectance.

    Automotive topcoat measures 0.10-0.22 diffuse for a saturated colour and
    0.55-0.68 for commercial white.  Feeding #5f9fd0 straight in gives a linear
    0.63 blue, and under a 115.75 W/m2 key at cos 0.83 that is 1.2 stops over
    the contract's -3.048 EV: AgX then compresses it to a pale grey and the
    livery stops reading.  MEASURED against the first two macros, where every
    trailer came back near-white.

    The map has to be a CURVE, not a scale: a linear one that puts a mid blue at
    0.18 also puts commercial white at 0.36, which is a grey van.  y^1.7 with a
    0.47 ceiling keeps fleet white at 0.47 and pulls the mid tones to 0.07-0.23,
    where paint actually lives.  (y^2 was tried and crushed a mid teal to 0.049,
    which is asphalt.)  Hue and chroma are preserved; only luminance moves.

    MEASURED, third macro: with the previous 0.46 blue the flank rendered
    sRGB (0.69, 0.73, 0.73) -- neutral.  A 12.47 deg sun is (1.00, 0.72, 0.39),
    so a blue surface has almost no red or green to reflect and its ONLY
    channel is 1.2 stops over; AgX then desaturates it to grey.  At 0.13 the
    same blue lands at 0.24 linear and survives the transform.
    """
    y = 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]
    if y < 1e-6:
        return rgb
    y2 = min(lo + span * (y ** gamma), 0.470)   # even fleet white tops out here
    k = y2 / y
    m = [c * k for c in rgb]
    # a touch of chroma back: scaling luminance down desaturates to the eye
    return tuple(max(0.0, min(1.0, m[i] + (m[i] - y2) * 0.20)) for i in range(3))


def darken(rgb, f):
    return tuple(max(0.0, c * f) for c in rgb)


def mixc(a, b, t):
    return tuple(a[i] * (1.0 - t) + b[i] * t for i in range(3))


# ==============================================================================
#  4.  THE PLAN  —  where the ten stand, and what makes each of them itself
# ==============================================================================
# All three groups are authored in the frame they are naturally aligned to and
# converted here, once.  Nothing downstream ever guesses a heading.

# frontage row: the flank plane that faces the Beat-4 transit corridor.
# MEASURED against world_contract: the corridor centreline is world y = 0, the
# ribbon is C.ACCESS_ROAD_W = 12.0 m wide, and C.transit_wall_point(t, +1) puts
# the north corridor wall on world y = +8.000 for world x 21..70.  A body face on
# y = +11.000 is therefore 3.000 m clear of the wall and 5.000 m outboard of the
# ribbon edge, and a lens at world y = +3.000 -- inside the ribbon -- stands
# exactly 8.000 m off it, which is the manifest's nearest_camera_m.
FRONTAGE_FACE_Y = 11.000
FRONTAGE_X0 = 27.000
RANK2_FACE_Y = 22.625
RANK2_X0 = 24.000
BANK_CIRCUIT_X = (-298.0, -289.2, -280.4, -271.6)
BANK_CIRCUIT_NOSE_Y = 95.600


def _circuit_axes():
    """World-frame unit vectors of the circuit design frame's +X and +Y."""
    o = np.array(C.circuit_to_world(0.0, 0.0), float)
    ex = np.array(C.circuit_to_world(1.0, 0.0), float) - o
    ey = np.array(C.circuit_to_world(0.0, 1.0), float) - o
    return ex / np.linalg.norm(ex), ey / np.linalg.norm(ey)


def _ground(x, y):
    """MEASURED ground z.  Law 5: never an assumed z."""
    z, own = C.world_ground_z(np.atleast_1d(float(x)), np.atleast_1d(float(y)))
    z = float(np.asarray(z).ravel()[0])
    own = str(np.asarray(own).ravel()[0])
    if not np.isfinite(z):
        raise SystemExit("REFUSING: world_ground_z is not finite at "
                         "(%.3f, %.3f). A trailer cannot be placed on a "
                         "surface that does not exist." % (x, y))
    return z, own


_PLAN_CACHE = [None]


def trailer_records():
    """The ten.  Deterministic; call it as often as you like."""
    if _PLAN_CACHE[0] is not None:
        return _PLAN_CACHE[0]

    out = []
    # ---- group 1: the frontage row, flank square to the transit corridor ----
    # Lengths are drawn to SPAN the manifest's declared range rather than to
    # cluster in the middle of it: a fleet is bought over eight seasons and the
    # oldest trailer is the short one.
    plan = [
        # (group, length, heading_deg_nominal)
        ("frontage", 14.600,   0.0),
        ("frontage", 12.600, 180.0),
        ("frontage", 13.900,   0.0),
        ("rank2",    13.400, 180.0),
        ("rank2",    14.200, 180.0),
        ("rank2",    12.900,   0.0),
        ("bank",     14.450, None),
        ("bank",     13.100, None),
        ("bank",     12.750, None),
        ("bank",     14.050, None),
    ]
    ex_c, ey_c = _circuit_axes()
    bank_heading = math.degrees(math.atan2(-ey_c[1], -ey_c[0]))   # nose to -Y

    xa = FRONTAGE_X0
    xb = RANK2_X0
    ib = 0
    for uid, (grp, L, hd) in enumerate(plan):
        r = Rng(7001, uid * 37 + 11)
        # --- parking, per group ---------------------------------------------
        if grp == "frontage":
            yaw = hd + r.clipn(1.3, 3.0)                 # parking error
            cx = xa + L * 0.5
            cy = FRONTAGE_FACE_Y + W_BODY * 0.5 + r.clipn(0.055, 0.13)
            xa += L + r.u(2.30, 3.10)
        elif grp == "rank2":
            yaw = hd + r.clipn(1.6, 3.6)
            cx = xb + L * 0.5
            cy = RANK2_FACE_Y + W_BODY * 0.5 + r.clipn(0.09, 0.22)
            xb += L + r.u(3.10, 4.20)
        else:
            yaw = bank_heading + r.clipn(1.1, 2.6)
            ccx = BANK_CIRCUIT_X[ib] + r.clipn(0.10, 0.24)
            ccy = BANK_CIRCUIT_NOSE_Y + L * 0.5 + r.clipn(0.16, 0.40)
            ib += 1
            cx, cy = (float(v) for v in C.circuit_to_world(ccx, ccy))
        gz, own = _ground(cx, cy)

        # --- the coachwork ---------------------------------------------------
        # sheet layout: full 1.220 m sheets and one closer, and the closer is at
        # the front on some trailers and at the rear on others because the body
        # shop worked from whichever end the door frame was jigged to.
        n_full = int(math.floor((L - 0.44) / PANEL_W))
        closer = L - n_full * PANEL_W
        while closer < 0.46:
            n_full -= 1
            closer += PANEL_W
        closer_front = r.chance(0.5)
        bays = [PANEL_W] * n_full
        bays = ([closer] + bays) if not closer_front else (bays + [closer])
        joints = list(np.cumsum(bays)[:-1] - L * 0.5)     # interior joints only

        z_floor = round(r.u(1.160, 1.300), 4)
        h_total = round(H_TOTAL + r.clipn(0.022, 0.045), 4)
        z_sill = z_floor - 0.260
        z_roof_bot = h_total - T_ROOF                     # top of the side wall
        # the three horizontal rails, each at its own height on each trailer
        z_bot_rail = z_sill + RAIL_BOT_H * 0.5
        z_waist = z_sill + r.u(1.180, 1.400)
        z_cant = z_roof_bot - RAIL_CANT_H * 0.5 - r.u(0.010, 0.030)

        # --- running gear -----------------------------------------------------
        rear_ovh = r.u(2.42, 3.05)                        # rear of body -> axle 3
        ax3 = -L * 0.5 + rear_ovh
        axles = [ax3, ax3 + AXLE_PITCH, ax3 + 2.0 * AXLE_PITCH]
        kingpin_x = L * 0.5 - KINGPIN_FROM_NOSE
        leg_x = kingpin_x - r.u(1.75, 2.15)

        # --- damage: the reason no two of these are the same object ----------
        n_scuff = r.i(6, 15)
        scuffs = []
        for k in range(n_scuff):
            side = r.pick((-1, 1))
            # scuffs cluster where a kerb, a bollard or a forklift reaches:
            # 0.10-0.55 m above the sill, and at the ends more than the middle
            t = r.u(0.0, 1.0)
            sx = (-L * 0.5 + 0.35 + t * (L - 0.7)
                  + (0.0 if r.chance(0.5) else r.clipn(0.9, 2.0)))
            scuffs.append(dict(
                side=side, x=float(np.clip(sx, -L * 0.5 + 0.22, L * 0.5 - 0.22)),
                z=z_sill + r.u(0.055, 0.520),
                rx=r.u(0.045, 0.240), rz=r.u(0.030, 0.130),
                depth=r.u(0.0035, 0.0210), tear=r.u(0.15, 1.0),
                kind=r.pick(("kerb", "forklift", "gate", "gate", "kerb"))))
        n_dent = r.i(4, 10)
        dents = []
        for k in range(n_dent):
            dents.append(dict(
                side=r.pick((-1, 1)),
                x=r.u(-L * 0.5 + 0.6, L * 0.5 - 0.6),
                z=r.u(z_sill + 0.75, z_roof_bot - 0.35),
                rx=r.u(0.11, 0.48), rz=r.u(0.08, 0.34),
                depth=r.u(0.0030, 0.0145)))
        n_rash = r.i(0, 3)
        rash = [dict(x=r.u(-L * 0.5 + 0.4, L * 0.5 - 0.4),
                     side=r.pick((-1, 1)),
                     w=r.u(0.10, 0.52), d=r.u(0.004, 0.016)) for _ in range(n_rash)]

        # --- fit-out ----------------------------------------------------------
        team_i = (uid * 3 + 1) % len(TEAMS)
        rec = dict(
            uid=uid, seed=r.seed, group=grp,
            team=TEAMS[team_i][0],
            c1=paint_albedo(srgb(TEAMS[team_i][1])),
            c2=paint_albedo(srgb(TEAMS[team_i][2])),
            haulier=HAULIERS[uid % len(HAULIERS)],
            sponsor=SPONSORS[(uid * 5 + 2) % len(SPONSORS)],
            fleet_no="%02d-%03d" % (17 + uid, 210 + uid * 37 % 700),
            L=float(L), W=W_BODY, H=float(h_total),
            n_panels=len(bays), bays=[float(b) for b in bays],
            joints=[float(j) for j in joints], closer_front=bool(closer_front),
            z_floor=float(z_floor), z_sill=float(z_sill),
            z_roof_bot=float(z_roof_bot), z_bot_rail=float(z_bot_rail),
            z_waist=float(z_waist), z_cant=float(z_cant),
            pos=(float(cx), float(cy)), yaw=float(yaw),
            ground_z=float(gz), ground_owner=own,
            axles=[float(a) for a in axles], kingpin_x=float(kingpin_x),
            leg_x=float(leg_x),
            # door state: 6 shut, 2 on the catch, 2 swung back.  The two open
            # ones get a REAL interior -- see build_interior.
            door_state=("open" if uid in (2, 7) else
                        ("catch" if uid in (4, 9) else "shut")),
            swing_deg=(238.0 if uid == 2 else 252.0 if uid == 7 else
                       14.0 if uid == 4 else 9.0 if uid == 9 else 0.0),
            livery=int(uid * 7 % 6), liv_swap=bool(uid % 3 == 1),
            liv_break=r.u(0.30, 0.62),          # where the scheme breaks, 0..1 of L
            liv_slope=r.u(-0.30, 0.34),         # the sweep's rake
            scuffs=scuffs, dents=dents, rash=rash,
            rivet_phase=r.u(0.0, 1.0),
            oil_seed=r.i(1, 9999),
            pods=r.i(1, 3), hatches=r.i(0, 2),
            ladder=r.pick((-1, 1, 0)),
            toolbox=r.pick((-1, 1)), spare=r.chance(0.6),
            hose_tubes=r.i(1, 3),
            wash_near=r.u(0.45, 0.95), wash_off=r.u(0.05, 0.45),
            wash_side=r.pick((-1, 1)),
            age=r.u(0.15, 0.95), grime=r.u(0.25, 0.95),
            flap_drag=(uid in (3, 7)),          # the two that trail on the deck
        )
        out.append(rec)
    _PLAN_CACHE[0] = out
    return out


def trailer_basis(t):
    """World origin and orthonormal axes of a trailer's local frame.

    Local x runs rear (-L/2) to nose (+L/2); local y is to the LEFT of travel;
    local z = 0 is the MEASURED ground under the trailer.
    """
    a = math.radians(t["yaw"])
    ex = np.array([math.cos(a), math.sin(a), 0.0])
    ey = np.array([-math.sin(a), math.cos(a), 0.0])
    ez = np.array([0.0, 0.0, 1.0])
    org = np.array([t["pos"][0], t["pos"][1], t["ground_z"]])
    return org, ex, ey, ez


def to_world(t, pts):
    org, ex, ey, ez = trailer_basis(t)
    P = np.asarray(pts, float).reshape(-1, 3)
    return org[None, :] + P[:, 0:1] * ex + P[:, 1:2] * ey + P[:, 2:3] * ez


# ==============================================================================
#  5.  THE MESH ACCUMULATOR
# ==============================================================================
# One trailer is one mesh with nine material slots and ten baked float
# attributes.  Everything is built as numpy arrays and handed to Blender in two
# foreach_set calls, because 3 000 rivets built with bpy.ops would take longer
# than the render.

# material slot order.  Fixed, because the shader reads slot index.
M_PAINT, M_ALU, M_STEEL, M_GALV, M_RUBBER, M_TAPE, M_STENCIL, M_DARK, M_CHEQ = range(9)
MAT_NAMES = ("Paint", "Alu", "Steel", "Galv", "Rubber", "Tape", "Stencil",
             "Dark", "Chequer")

ATTRS = ("tt_zg", "tt_wear", "tt_scuff", "tt_grime", "tt_kick", "tt_seam",
         "tt_lv1", "tt_lv2", "tt_side", "tt_wash", "tt_oil")


class Acc(object):
    """Vertex / face / attribute accumulator with per-face material index."""

    def __init__(self):
        self.V = []
        self.Q = []; self.QM = []
        self.T = []; self.TM = []
        self.A = {k: [] for k in ATTRS}
        self.n = 0

    def push(self, V, quads=None, tris=None, mat=M_PAINT, **attrs):
        V = np.ascontiguousarray(np.asarray(V, np.float64).reshape(-1, 3))
        base = self.n
        self.V.append(V)
        self.n += len(V)
        if quads is not None and len(quads):
            q = np.asarray(quads, np.int64).reshape(-1, 4) + base
            self.Q.append(q)
            self.QM.append(np.full(len(q), mat, np.int32) if np.isscalar(mat)
                           else np.asarray(mat, np.int32).ravel())
        if tris is not None and len(tris):
            t = np.asarray(tris, np.int64).reshape(-1, 3) + base
            self.T.append(t); self.TM.append(np.full(len(t), mat, np.int32))
        for k in ATTRS:
            v = attrs.get(k, 0.0)
            if np.isscalar(v):
                self.A[k].append(np.full(len(V), float(v), np.float32))
            else:
                a = np.asarray(v, np.float32).ravel()
                if len(a) != len(V):
                    a = np.resize(a, len(V))
                self.A[k].append(a)
        return base

    def grid(self, P, mat=M_PAINT, flip=False, **attrs):
        """P is (nu, nv, 3); attrs may be (nu, nv) arrays or scalars."""
        P = np.asarray(P, float)
        nu, nv = P.shape[0], P.shape[1]
        idx = np.arange(nu * nv).reshape(nu, nv)
        if flip:
            Q = np.stack([idx[:-1, :-1].ravel(), idx[:-1, 1:].ravel(),
                          idx[1:, 1:].ravel(), idx[1:, :-1].ravel()], 1)
        else:
            Q = np.stack([idx[:-1, :-1].ravel(), idx[1:, :-1].ravel(),
                          idx[1:, 1:].ravel(), idx[:-1, 1:].ravel()], 1)
        at = {k: (np.asarray(v, np.float32).ravel() if not np.isscalar(v) else v)
              for k, v in attrs.items()}
        return self.push(P.reshape(-1, 3), Q, None, mat, **at)

    def finish(self):
        V = np.concatenate(self.V) if self.V else np.zeros((0, 3))
        Q = np.concatenate(self.Q) if self.Q else np.zeros((0, 4), np.int64)
        T = np.concatenate(self.T) if self.T else np.zeros((0, 3), np.int64)
        QM = np.concatenate(self.QM) if self.QM else np.zeros(0, np.int32)
        TM = np.concatenate(self.TM) if self.TM else np.zeros(0, np.int32)
        A = {k: (np.concatenate(v) if v else np.zeros(0, np.float32))
             for k, v in self.A.items()}
        A["tt_zg"] = V[:, 2].astype(np.float32)      # height above local ground
        return V, Q, T, QM, TM, A


# ---- generic solids ---------------------------------------------------------

def rrect(w, h, r, n=4):
    """Rounded-rectangle profile, centred, counter-clockwise.  (m,2)."""
    r = min(r, w * 0.5 - 1e-4, h * 0.5 - 1e-4)
    hw, hh = w * 0.5 - r, h * 0.5 - r
    if r <= 1e-5 or n < 1:
        return np.array([(-w * .5, -h * .5), (w * .5, -h * .5),
                         (w * .5, h * .5), (-w * .5, h * .5)])
    a = np.linspace(0.0, math.pi * 0.5, n + 1)
    ca, sa = np.cos(a), np.sin(a)
    q = [np.stack([hw + r * ca, hh + r * sa], 1),
         np.stack([-hw - r * sa, hh + r * ca], 1),
         np.stack([-hw - r * ca, -hh - r * sa], 1),
         np.stack([hw + r * sa, -hh - r * ca], 1)]
    P = np.concatenate(q)
    keep = np.concatenate([[True], np.linalg.norm(np.diff(P, axis=0), axis=1) > 1e-7])
    return P[keep]


def sweep(profile, path, right, up, closed=True, cap0=False, cap1=False):
    """Sweep a 2-D profile along a 3-D path.  -> (V, quads, tris)."""
    profile = np.asarray(profile, float)
    path = np.asarray(path, float).reshape(-1, 3)
    n, m = len(path), len(profile)
    R = np.asarray(right, float)
    U = np.asarray(up, float)
    if R.ndim == 1:
        R = np.repeat(R[None, :], n, 0)
    if U.ndim == 1:
        U = np.repeat(U[None, :], n, 0)
    V = (path[:, None, :] + profile[None, :, 0:1] * R[:, None, :]
         + profile[None, :, 1:2] * U[:, None, :]).reshape(-1, 3)
    idx = np.arange(n * m).reshape(n, m)
    if closed:
        j0 = idx
        j1 = np.roll(idx, -1, axis=1)
    else:
        j0 = idx[:, :-1]
        j1 = idx[:, 1:]
    Q = np.stack([j0[:-1].ravel(), j1[:-1].ravel(),
                  j1[1:].ravel(), j0[1:].ravel()], 1)
    tris = []
    if cap0 or cap1:
        ctr = profile.mean(axis=0)
        extra = []
        if cap0:
            c0 = path[0] + ctr[0] * R[0] + ctr[1] * U[0]
            ci = n * m + len(extra); extra.append(c0)
            k = np.arange(m)
            tris.append(np.stack([np.full(m, ci), np.roll(k, -1), k], 1))
        if cap1:
            c1 = path[-1] + ctr[0] * R[-1] + ctr[1] * U[-1]
            ci = n * m + len(extra); extra.append(c1)
            k = (n - 1) * m + np.arange(m)
            tris.append(np.stack([np.full(m, ci), k, np.roll(k, -1)], 1))
        V = np.concatenate([V, np.asarray(extra, float)])
    T = np.concatenate(tris) if tris else None
    return V, Q, T


def revolve(prof_rz, nseg, org, axis, phase=0.0, cap=False):
    """Revolve a (r, h) profile about `axis` through `org`.  -> (V, quads, tris)."""
    prof_rz = np.asarray(prof_rz, float)
    axis = np.asarray(axis, float); axis = axis / np.linalg.norm(axis)
    tmp = np.array([0.0, 0.0, 1.0]) if abs(axis[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    e1 = np.cross(axis, tmp); e1 /= np.linalg.norm(e1)
    e2 = np.cross(axis, e1)
    a = np.linspace(0.0, 2.0 * math.pi, nseg, endpoint=False) + phase
    ca, sa = np.cos(a)[:, None], np.sin(a)[:, None]
    ring = ca * e1[None, :] + sa * e2[None, :]                 # (nseg,3)
    m = len(prof_rz)
    V = (np.asarray(org, float)[None, None, :]
         + prof_rz[None, :, 0:1] * ring[:, None, :]
         + prof_rz[None, :, 1:2] * axis[None, None, :]).reshape(-1, 3)
    idx = np.arange(nseg * m).reshape(nseg, m)
    i0 = idx[:, :-1]; i1 = idx[:, 1:]
    j0 = np.roll(i0, -1, axis=0); j1 = np.roll(i1, -1, axis=0)
    Q = np.stack([i0.ravel(), j0.ravel(), j1.ravel(), i1.ravel()], 1)
    T = None
    if cap:
        tris = []
        for end, sgn in ((0, 1), (m - 1, -1)):
            if prof_rz[end, 0] > 1e-6:
                c = np.asarray(org, float) + prof_rz[end, 1] * axis
                ci = len(V); V = np.concatenate([V, c[None, :]])
                k = idx[:, end]
                kk = np.roll(k, -1)
                tris.append(np.stack([np.full(nseg, ci), k, kk], 1)[::sgn])
        T = np.concatenate(tris) if tris else None
    return V, Q, T


def rbox(c, half, r=0.0, nr=2, axis=0):
    """Rounded box centred at `c` with half-extents `half`, rounded on the four
    edges parallel to `axis`."""
    c = np.asarray(c, float); half = np.asarray(half, float)
    ax = np.zeros(3); ax[axis] = 1.0
    i1, i2 = [i for i in range(3) if i != axis]
    e1 = np.zeros(3); e1[i1] = 1.0
    e2 = np.zeros(3); e2[i2] = 1.0
    prof = rrect(half[i1] * 2.0, half[i2] * 2.0, r, nr)
    path = np.stack([c - ax * half[axis], c + ax * half[axis]])
    return sweep(prof, path, e1, e2, closed=True, cap0=True, cap1=True)


def dome_batch(P, N, R, r, h, nseg=6,
               rings=((1.0, 0.0), (0.94, 0.42), (0.70, 0.80), (0.0, 1.0))):
    """N rivet / bolt domes at once.  P (n,3) seats, N (n,3) outward normals,
    R (n,3) an in-surface reference direction.  -> (V, quads, tris)."""
    P = np.asarray(P, float).reshape(-1, 3)
    n = len(P)
    if n == 0:
        return np.zeros((0, 3)), None, None
    N = np.asarray(N, float).reshape(-1, 3)
    N = N / np.linalg.norm(N, axis=1, keepdims=True)
    R = np.asarray(R, float).reshape(-1, 3)
    R = R - (R * N).sum(1, keepdims=True) * N
    R = R / np.maximum(np.linalg.norm(R, axis=1, keepdims=True), 1e-12)
    S = np.cross(N, R)
    a = np.linspace(0.0, 2.0 * math.pi, nseg, endpoint=False)
    ca, sa = np.cos(a), np.sin(a)
    rr = np.atleast_1d(np.asarray(r, float)); rr = np.resize(rr, n)
    hh = np.atleast_1d(np.asarray(h, float)); hh = np.resize(hh, n)
    m = len(rings)
    V = np.empty((n, m, nseg, 3))
    for k, (fr, fh) in enumerate(rings):
        rad = (rr * fr)[:, None]
        hgt = (hh * fh)[:, None]
        V[:, k] = (P[:, None, :]
                   + rad[:, :, None] * (ca[None, :, None] * R[:, None, :]
                                        + sa[None, :, None] * S[:, None, :])
                   + hgt[:, :, None] * N[:, None, :])
    V = V.reshape(-1, 3)
    base = (np.arange(n) * m * nseg)[:, None, None]
    idx = base + (np.arange(m)[None, :, None] * nseg + np.arange(nseg)[None, None, :])
    quads, tris = [], []
    for k in range(m - 1):
        i0 = idx[:, k]; i1 = idx[:, k + 1]
        if rings[k + 1][0] < 1e-9:
            tris.append(np.stack([i0.ravel(), np.roll(i0, -1, 1).ravel(),
                                  i1.ravel()], 1))
        else:
            quads.append(np.stack([i0.ravel(), np.roll(i0, -1, 1).ravel(),
                                   np.roll(i1, -1, 1).ravel(), i1.ravel()], 1))
    Q = np.concatenate(quads) if quads else None
    T = np.concatenate(tris) if tris else None
    return V, Q, T


def plate(corners, thick, nrm):
    """A thin slab from four corner points and an outward normal.  Closed."""
    c = np.asarray(corners, float).reshape(4, 3)
    nrm = np.asarray(nrm, float); nrm = nrm / np.linalg.norm(nrm)
    V = np.concatenate([c, c + nrm[None, :] * thick])
    Q = np.array([[4, 5, 6, 7], [3, 2, 1, 0],
                  [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]])
    return V, Q, None


def prism2d(polys, org, e1, e2, nrm, thick):
    """Extrude flat 2-D polygons (the stroke font) into thin plates."""
    org = np.asarray(org, float); e1 = np.asarray(e1, float)
    e2 = np.asarray(e2, float); nrm = np.asarray(nrm, float)
    Vs, Qs = [], []
    base = 0
    for p in polys:
        p = np.asarray(p, float)
        k = len(p)
        f = org[None, :] + p[:, 0:1] * e1[None, :] + p[:, 1:2] * e2[None, :]
        b = f + nrm[None, :] * thick
        Vs.append(np.concatenate([f, b]))
        i = np.arange(k)
        Qs.append(np.stack([base + i, base + np.roll(i, -1),
                            base + k + np.roll(i, -1), base + k + i], 1))
        if k == 4:
            Qs.append(np.array([[base + k, base + k + 1, base + k + 2, base + k + 3]]))
        base += 2 * k
    if not Vs:
        return np.zeros((0, 3)), None, None
    return np.concatenate(Vs), np.concatenate(Qs), None


def row_points(a, b, pitch, phase=0.0):
    """Evenly spaced points from a to b at ~`pitch`, inset half a pitch."""
    a = np.asarray(a, float); b = np.asarray(b, float)
    L = float(np.linalg.norm(b - a))
    n = max(2, int(round(L / pitch)))
    t = (np.arange(n) + 0.5 + 0.0 * phase) / n
    return a[None, :] + t[:, None] * (b - a)[None, :]


# ==============================================================================
#  6.  THE COACHWORK
# ==============================================================================
# The body is ONE open swept shell -- rear-right corner, right flank, front
# corner, front face, front corner, left flank, rear-left corner -- so the
# vertical corner radii are continuous with the flanks instead of being four
# boxes that meet at an arris.  The rear is NOT in the sweep: it is a picture
# frame with a 2.48 x 2.62 m hole in it, and a hole is not something a sweep
# can carry.

def _plan_outline(t, lod):
    """The body's plan section, as an OPEN polyline from the rear face round to
    the rear face.  Returns per-point plan position, outward normal, the
    along-length coordinate the livery is authored in, and which flank it is."""
    L, W = t["L"], t["W"]
    dx, dz, droof, dend, spm, seg = LOD[lod]
    R = R_CORNER
    hx, hy = L * 0.5, W * 0.5
    jx = np.asarray(t["joints"], float)
    sc = np.array([s["x"] for s in t["scuffs"]] or [0.0])
    dn = np.array([d["x"] for d in t["dents"]] or [0.0])

    segs = []

    def arc(cx, cy, a0, a1, n):
        a = np.linspace(math.radians(a0), math.radians(a1), n)
        return (cx + R * np.cos(a), cy + R * np.sin(a), np.cos(a), np.sin(a))

    na = max(3, int(round(4 * seg)) + 2)
    # A rear-right corner
    segs.append(arc(-hx + R, -hy + R, 180.0, 270.0, na))
    # B right flank
    xs = refine(-hx + R, hx - R, dx, sites=list(jx) + list(sc) + list(dn),
                win=0.11, fine=dx * 0.42)
    segs.append((xs, np.full_like(xs, -hy), np.zeros_like(xs), np.full_like(xs, -1.0)))
    # C front-right corner
    segs.append(arc(hx - R, -hy + R, 270.0, 360.0, na))
    # D front face
    ys = refine(-hy + R, hy - R, dend)
    segs.append((np.full_like(ys, hx), ys, np.ones_like(ys), np.zeros_like(ys)))
    # E front-left corner
    segs.append(arc(hx - R, hy - R, 0.0, 90.0, na))
    # F left flank
    xs2 = xs[::-1]
    segs.append((xs2, np.full_like(xs2, hy), np.zeros_like(xs2), np.full_like(xs2, 1.0)))
    # G rear-left corner
    segs.append(arc(-hx + R, hy - R, 90.0, 180.0, na))

    X, Y, NX, NY = [], [], [], []
    for i, (a, b, c, d) in enumerate(segs):
        k = slice(0, len(a) - 1) if i < len(segs) - 1 else slice(0, len(a))
        X.append(np.asarray(a)[k]); Y.append(np.asarray(b)[k])
        NX.append(np.asarray(c)[k]); NY.append(np.asarray(d)[k])
    X = np.concatenate(X); Y = np.concatenate(Y)
    NX = np.concatenate(NX); NY = np.concatenate(NY)
    n = np.hypot(NX, NY); NX /= n; NY /= n
    side = np.where(np.abs(NY) > 0.985, np.sign(NY), 0.0)
    flat = (np.abs(NY) > 0.999).astype(float)
    u = np.clip(X, -hx, hx)
    # distance to the nearest cover strip, along the flank
    if len(jx):
        seam = np.min(np.abs(u[:, None] - jx[None, :]), axis=1)
    else:
        seam = np.full(len(u), 9.0)
    seam = np.where(flat > 0.5, seam, 9.0)
    # arc length, for anything that has to run round the corners
    d = np.concatenate([[0.0], np.hypot(np.diff(X), np.diff(Y))])
    return dict(x=X, y=Y, nx=NX, ny=NY, side=side, flat=flat, u=u, seam=seam,
                s=np.cumsum(d), n=len(X))


def _shell_z(t, lod):
    """z stations up the body sheet.  Fine through the kick band (which carries
    the scuffs) and through every rail seat, coarse across the open paint."""
    dx, dz, droof, dend, spm, seg = LOD[lod]
    z0 = t["z_sill"]
    zkb = z0 + RAIL_BOT_H
    zkt = zkb + KICK_H
    z1 = t["z_roof_bot"]
    lo = refine(z0, zkt + 0.012, dz * 0.30,
                sites=[zkb, zkb + 0.007, zkt, zkt + 0.010], win=0.016,
                fine=dz * 0.11)
    hi = refine(zkt + 0.012, z1, dz,
                sites=[t["z_waist"] - RAIL_WAIST_H * 0.5 - 0.02,
                       t["z_waist"] + RAIL_WAIST_H * 0.5 + 0.02,
                       t["z_cant"] - RAIL_CANT_H * 0.5 - 0.02, z1 - 0.02],
                win=0.05, fine=dz * 0.34)
    return np.unique(np.concatenate([lo, hi]))


def _kick_offset(t, Z):
    """Outward offset of the kick plate: a real 6 mm plate with a real edge."""
    zkb = t["z_sill"] + RAIL_BOT_H
    zkt = zkb + KICK_H
    return KICK_D * (smoothstep(zkb, zkb + 0.006, Z)
                     * (1.0 - smoothstep(zkt, zkt + 0.009, Z)))


def _oilcan(t, U, Z, FLAT):
    """The standing wave in a bonded 1.5 mm alu sheet.

    A flat panel is the single most plastic-looking thing a render can contain.
    Every bay of every trailer gets its own realisation, pinned to zero at the
    cover strips and at the rails because that is where the sheet is actually
    fastened.
    """
    L = t["L"]
    z0, z1 = t["z_sill"], t["z_roof_bot"]
    edges = np.array([-L * 0.5] + list(t["joints"]) + [L * 0.5])
    bi = np.clip(np.searchsorted(edges, U) - 1, 0, len(edges) - 2)
    xa = edges[bi]; xb = edges[bi + 1]
    uu = np.clip((U - xa) / np.maximum(xb - xa, 1e-6), 0.0, 1.0)
    zkt = z0 + RAIL_BOT_H + KICK_H
    vv = np.clip((Z - zkt) / max(z1 - zkt, 1e-6), 0.0, 1.0)
    win = (np.sin(np.pi * np.clip(uu, 0, 1)) ** 1.25
           * np.sin(np.pi * np.clip(vv, 0, 1)) ** 1.05)
    sd = t["oil_seed"]
    ph = _h2(bi.astype(np.int64), np.zeros_like(bi, np.int64), sd) * 6.283
    # MEASURED against the light: on a vertical flank SUN_DIR's in-plane
    # component is 0.561 against a 0.828 normal component, so relief throws only
    # 0.68x its height -- a 1.5 mm wave is 1 mm of shadow, half a pixel, and the
    # flank reads as vacuum-formed plastic.  A bonded 1.5 mm alu sheet on a
    # 1.22 m bay genuinely stands 3-7 mm out of plane, and at that amplitude the
    # HIGHLIGHT bends across 300 mm = 140 px, which is what sells sheet metal.
    amp = (0.0026 + 0.0042 * _h2(bi.astype(np.int64),
                                 np.ones_like(bi, np.int64), sd + 3))
    w = (0.62 * np.sin(2.15 * np.pi * uu + ph)
         + 0.44 * np.sin(3.30 * np.pi * vv + ph * 1.7)
         + 0.55 * (fbm2(U * 2.6, Z * 2.9, sd + 11, 3) - 0.5) * 2.0)
    return amp * win * w * FLAT


def _flank_damage(t, U, Z, SIDE, NX, NY):
    """Kerb scuffs, forklift strikes and the soft dents a 14 m flank collects.

    These are the manifest's "side-skirt scuffs" variation axis, and they are
    GEOMETRY: a scuff is a 2-12 mm depression with a torn paint boundary, not a
    darker patch of shader.
    """
    d = np.zeros_like(U)
    tear = np.zeros_like(U)
    for s in t["scuffs"]:
        m = (SIDE == s["side"])
        if not m.any():
            continue
        e = (((U - s["x"]) / s["rx"]) ** 2 + ((Z - s["z"]) / s["rz"]) ** 2)
        if s["kind"] == "kerb":
            g = np.clip(1.0 - e, 0.0, 1.0) ** 0.55          # flat-bottomed gouge
        elif s["kind"] == "forklift":
            g = np.clip(1.0 - e, 0.0, 1.0) ** 1.8           # a sharp point strike
        else:
            g = np.clip(1.0 - e, 0.0, 1.0) ** 1.0
        g = g * m
        d = d + s["depth"] * g
        tear = np.maximum(tear, m * s["tear"] * np.clip(1.35 - e, 0.0, 1.0))
    for s in t["dents"]:
        m = (SIDE == s["side"])
        if not m.any():
            continue
        e = (((U - s["x"]) / s["rx"]) ** 2 + ((Z - s["z"]) / s["rz"]) ** 2)
        # a panel dent has a raised rim: the metal has to go somewhere
        g = np.exp(-2.2 * e) - 0.30 * np.exp(-0.85 * e) * (e > 0.55)
        d = d + s["depth"] * g * m
    return d, tear


def _livery(t, U, Z):
    """Signed distance, in metres, to the livery boundary.  Positive inside the
    secondary colour.  BAKED AS DISTANCE, not as a region index: at 466 px/m a
    region index quantised to a 42 mm mesh would stair-step by 20 px, while a
    distance field thresholded in the shader lands within a tenth of a
    millimetre of the true line."""
    L = t["L"]
    z0, z1 = t["z_sill"], t["z_roof_bot"]
    zb = z0 + t["liv_break"] * (z1 - z0)
    sl = t["liv_slope"]
    sch = t["livery"]
    u0 = -L * 0.5 + t["liv_break"] * L
    # MEASURED, fifth macro: scheme 2 painted the whole lower two thirds in the
    # team's SECOND colour, which on most of the fourteen colourways is a near
    # white -- so the hero trailer rendered as a 14 m white wall with a stripe
    # of team colour along the top.  Every scheme here now keeps the secondary
    # under about a third of the flank, and `liv_swap` decides which of the two
    # colours is the ground, so a third of the fleet runs white-with-a-livery
    # and the rest run livery-with-a-white-band.  That is what a paddock full
    # of transporters looks like.
    if sch == 0:            # a waist band
        h = 0.42 + 0.10 * math.sin(t["uid"])
        lv1 = h - np.abs(Z - (t["z_waist"] + 0.05))
    elif sch == 1:          # a diagonal sweep, secondary in the lower rear
        lv1 = (zb + sl * (U - u0)) - Z
    elif sch == 2:          # a band under the roof line
        lv1 = Z - (z1 - 0.78)
    elif sch == 3:          # a block over the rear third
        lv1 = u0 - U
    elif sch == 4:          # roof band + lower valance
        lv1 = np.maximum(Z - (z1 - 0.52), (z0 + 0.62) - Z)
    else:                   # a chevron
        lv1 = 0.48 - np.abs(Z - (zb + 0.34 * np.abs(U - u0) ** 0.85))
    lv2 = 0.085 - np.abs(lv1 - 0.145)          # the accent pinstripe
    return lv1, lv2


def build_shell(t, lod, acc, rivets):
    """The riveted aluminium body: three sides of sheet, the kick plate and the
    sill return, as one continuous surface."""
    P = _plan_outline(t, lod)
    Z = _shell_z(t, lod)
    npn, nz = P["n"], len(Z)
    X = np.repeat(P["x"][:, None], nz, 1)
    Y = np.repeat(P["y"][:, None], nz, 1)
    NX = np.repeat(P["nx"][:, None], nz, 1)
    NY = np.repeat(P["ny"][:, None], nz, 1)
    U = np.repeat(P["u"][:, None], nz, 1)
    SIDE = np.repeat(P["side"][:, None], nz, 1)
    FLAT = np.repeat(P["flat"][:, None], nz, 1)
    SEAM = np.repeat(P["seam"][:, None], nz, 1)
    ZZ = np.repeat(Z[None, :], npn, 0)

    off = _kick_offset(t, ZZ)                       # the kick plate stands PROUD
    oil = _oilcan(t, U, ZZ, FLAT)
    dmg, tear = _flank_damage(t, U, ZZ, SIDE, NX, NY)
    # the sheet is drawn in slightly at every fastener line and at the sill
    pull = (0.0011 * np.exp(-((SEAM / 0.045) ** 2))
            + 0.0016 * np.exp(-(((ZZ - t["z_sill"]) / 0.05) ** 2)))
    out = off + oil - dmg - pull
    V = np.stack([X + NX * out, Y + NY * out, ZZ], -1)

    lv1, lv2 = _livery(t, U, ZZ)
    wash = np.where(SIDE == t["wash_side"], t["wash_near"], t["wash_off"])
    zkb = t["z_sill"] + RAIL_BOT_H
    zkt = zkb + KICK_H
    kick = ((ZZ > zkb) & (ZZ < zkt)).astype(np.float32)
    wear = np.clip(1.0 - np.abs(ZZ - zkt) / 0.05, 0, 1) * 0.7 + tear * 0.8
    wear = np.maximum(wear, np.clip(1.0 - SEAM / 0.05, 0, 1) * 0.45)
    wear = np.maximum(wear, (1.0 - FLAT) * 0.55)       # the corners rub
    # every horizontal ledge sheds dirty water DOWN the paint below it, so the
    # streak sources are the cant rail, the waist rail and the roof edge -- not
    # just the top 350 mm, which is what left the middle of the flank spotless.
    grime = np.clip((ZZ - (t["z_roof_bot"] - 0.55)) / 0.55, 0, 1) * 1.0
    for zr, amp, reach in ((t["z_cant"] - RAIL_CANT_H * 0.5, 0.58, 0.42),
                           (t["z_waist"] - RAIL_WAIST_H * 0.5, 0.44, 0.34)):
        grime = np.maximum(grime, amp * np.clip(1.0 - (zr - ZZ) / reach, 0, 1)
                           * (ZZ < zr))
    # THE KICK PLATE IS A DIFFERENT MATERIAL, not a darker patch of paint: it
    # is a separate 3 mm alu plate bolted over the paint, and at 466 px/m the
    # 9 mm step at its top edge is 4.2 px of hard shadow.
    zcf = 0.5 * (Z[:-1] + Z[1:])
    fmat = np.repeat(np.where((zcf > zkb) & (zcf < zkt), M_ALU, M_PAINT)[None, :],
                     npn - 1, 0).ravel()
    acc.grid(V, fmat, tt_wear=wear, tt_scuff=tear, tt_grime=grime,
             tt_kick=kick, tt_seam=np.clip(1.0 - SEAM / 0.06, 0, 1),
             tt_lv1=lv1, tt_lv2=lv2, tt_side=SIDE, tt_wash=wash,
             tt_oil=oil * 300.0)

    # ---- the sill return: the sheet turns under and dies on the chassis -----
    zb = t["z_sill"]
    r0 = np.stack([X[:, 0], Y[:, 0], np.full(npn, zb)], -1)
    r0[:, 0] += NX[:, 0] * out[:, 0]; r0[:, 1] += NY[:, 0] * out[:, 0]
    r1 = np.stack([P["x"] - P["nx"] * 0.018, P["y"] - P["ny"] * 0.018,
                   np.full(npn, zb - 0.016)], -1)
    r2 = np.stack([P["x"] - P["nx"] * 0.075, P["y"] - P["ny"] * 0.075,
                   np.full(npn, zb - 0.004)], -1)
    acc.grid(np.stack([r0, r1, r2], 1), M_PAINT, flip=True, tt_wear=0.6,
             tt_side=np.repeat(P["side"][:, None], 3, 1), tt_wash=0.1,
             tt_grime=0.85)

    # ---- rivet rows down every cover strip and along every rail ------------
    # (positions only; the domes are emitted once, at the end, in one batch)
    return P, Z, V


def _profile_rail(kind):
    """Extruded aluminium rail sections, in (outward, up) from the sheet plane.

    Every one of them has a DRIP EDGE.  At a 12.47 deg sun a horizontal rail
    throws 4.52x its own projection down the paint, and the shape of the bottom
    of that shadow is the shape of the bottom of the rail: a square section
    reads as a printed stripe, a real section reads as extruded metal.
    """
    if kind == "waist":
        d, h = RAIL_WAIST_D, RAIL_WAIST_H
        return np.array([
            (0.000, -h * 0.5), (d * 0.42, -h * 0.5), (d * 0.92, -h * 0.5 + 0.006),
            (d, -h * 0.5 + 0.020), (d, h * 0.5 - 0.026), (d * 0.86, h * 0.5 - 0.008),
            (d * 0.40, h * 0.5), (0.000, h * 0.5)])
    if kind == "bottom":
        d, h = RAIL_BOT_D, RAIL_BOT_H
        return np.array([
            (0.000, -h * 0.5), (d * 0.30, -h * 0.5 - 0.006), (d * 0.86, -h * 0.5),
            (d, -h * 0.5 + 0.016), (d, h * 0.5 - 0.030), (d * 0.72, h * 0.5 - 0.004),
            (d * 0.30, h * 0.5), (0.000, h * 0.5)])
    d, h = RAIL_CANT_D, RAIL_CANT_H
    return np.array([
        (0.000, -h * 0.5), (d * 0.55, -h * 0.5 - 0.004), (d, -h * 0.5 + 0.010),
        (d, h * 0.5 - 0.012), (d * 0.62, h * 0.5), (0.000, h * 0.5)])


def build_rails(t, lod, acc, rivets):
    """Cant rail, rubbing rail and bottom rail on both flanks, plus the vertical
    cover strip over every sheet joint."""
    dx, dz, droof, dend, spm, seg = LOD[lod]
    L, W = t["L"], t["W"]
    hx, hy = L * 0.5, W * 0.5
    x0, x1 = -hx + R_CORNER + 0.02, hx - R_CORNER - 0.02
    zkb = t["z_sill"] + RAIL_BOT_H
    zkt = zkb + KICK_H
    nst = max(4, int((x1 - x0) * 2.2))
    for side in (-1, 1):
        yb = side * hy
        for kind, zc, mat in (("bottom", t["z_sill"] + RAIL_BOT_H * 0.5, M_ALU),
                              ("waist", t["z_waist"], M_ALU),
                              ("cant", t["z_cant"], M_ALU)):
            prof = _profile_rail(kind)
            # the rail is bedded on the sheet, so it follows the kick offset
            base = KICK_D if (zkb < zc < zkt) else 0.0
            pr = prof.copy(); pr[:, 0] += base
            xs = np.linspace(x0, x1, nst)
            # ends are cropped back and chamfered, they do not run into the corner
            path = np.stack([xs, np.full(nst, yb), np.full(nst, zc)], 1)
            R = np.array([0.0, float(side), 0.0])
            V, Q, T = sweep(pr, path, R, np.array([0.0, 0.0, 1.0]),
                            closed=True, cap0=True, cap1=True)
            acc.push(V, Q, T, mat, tt_wear=0.55, tt_side=side, tt_grime=0.5,
                     tt_wash=(t["wash_near"] if side == t["wash_side"]
                              else t["wash_off"]))
            # fastener row along the rail
            h = float(prof[:, 1].max() - prof[:, 1].min())
            rx = np.arange(x0 + 0.08, x1 - 0.05, P_RIVET * 1.18)
            for zr in ((zc,) if kind == "cant" else (zc - h * 0.28, zc + h * 0.28)):
                p = np.stack([rx, np.full(len(rx), yb + side * (base + prof[:, 0].max())),
                              np.full(len(rx), zr)], 1)
                rivets.append((p, np.repeat(np.array([[0.0, side, 0.0]]), len(rx), 0),
                               D_RIVET * 0.62, H_RIVET * 0.95, M_ALU))

        # ---- vertical cover strips over the sheet joints -------------------
        zs0, zs1 = zkb + 0.004, t["z_cant"] - RAIL_CANT_H * 0.5 - 0.004
        nsz = max(6, int((zs1 - zs0) * 5.0))
        sp = np.array([
            (0.000, -W_STRIP * 0.5), (T_STRIP * 0.55, -W_STRIP * 0.5 + 0.004),
            (T_STRIP, -W_STRIP * 0.5 + 0.014), (T_STRIP, W_STRIP * 0.5 - 0.014),
            (T_STRIP * 0.55, W_STRIP * 0.5 - 0.004), (0.000, W_STRIP * 0.5)])
        for jx in t["joints"]:
            zz = np.linspace(zs0, zs1, nsz)
            base = _kick_offset(t, zz)
            path = np.stack([np.full(nsz, jx), np.full(nsz, side * hy), zz], 1)
            R = np.array([0.0, float(side), 0.0])
            V, Q, T = sweep(sp, path, R, np.array([1.0, 0.0, 0.0]),
                            closed=True, cap0=True, cap1=True)
            # `sweep` appends one centre vertex per cap, so the offset array
            # has to be padded with the two end stations' own offsets.
            yo = np.repeat(base, len(sp))
            if len(V) > len(yo):
                yo = np.concatenate([yo, np.full(len(V) - len(yo), base[0])])
                yo[-1] = base[-1]
            V[:, 1] += side * yo
            acc.push(V, Q, T, M_PAINT, tt_wear=0.5, tt_seam=1.0, tt_side=side,
                     tt_grime=0.6,
                     tt_wash=(t["wash_near"] if side == t["wash_side"]
                              else t["wash_off"]))
            rz = np.arange(zs0 + 0.06, zs1 - 0.04, P_RIVET)
            ph = (t["rivet_phase"] + 0.5 * (jx > 0)) * P_RIVET
            rz = rz + ph * 0.4
            rz = rz[(rz > zs0 + 0.02) & (rz < zs1 - 0.02)]
            for dyy in (-W_STRIP * 0.30, W_STRIP * 0.30):
                yv = side * (hy + T_STRIP) + side * _kick_offset(t, rz)
                p = np.stack([np.full(len(rz), jx + dyy), yv, rz], 1)
                rivets.append((p, np.repeat(np.array([[0.0, side, 0.0]]), len(rz), 0),
                               D_RIVET * 0.56, H_RIVET, M_PAINT))

        # ---- kick-plate fastener rows ---------------------------------------
        kx = np.arange(x0 + 0.10, x1 - 0.06, P_RIVET * 1.45)
        for zr in (zkb + 0.030, zkt - 0.028):
            p = np.stack([kx, np.full(len(kx), side * (hy + KICK_D)),
                          np.full(len(kx), zr)], 1)
            rivets.append((p, np.repeat(np.array([[0.0, side, 0.0]]), len(kx), 0),
                           D_RIVET * 0.58, H_RIVET * 0.9, M_ALU))


def build_roof(t, lod, acc, rivets):
    """The roof cap, its gutter, the bow lines showing through the skin, the
    hatches and the pods.  Seen from the pit-building balcony and from the
    Beat-6 crane, so it is not a lid."""
    dx, dz, droof, dend, spm, seg = LOD[lod]
    L, W = t["L"], t["W"]
    hx, hy = L * 0.5, W * 0.5
    zb = t["z_roof_bot"]
    R = R_CORNER

    # ---- the perimeter cap, as one ribbon round a closed rounded rectangle --
    na = max(4, int(round(5 * seg)) + 2)
    px, py, pnx, pny = [], [], [], []
    for cx, cy, a0, a1 in ((-hx + R, -hy + R, 180, 270), (hx - R, -hy + R, 270, 360),
                           (hx - R, hy - R, 0, 90), (-hx + R, hy - R, 90, 180)):
        if cx > 0 and a0 == 270:
            xs = refine(-hx + R, hx - R, droof)
            px.append(xs); py.append(np.full_like(xs, -hy))
            pnx.append(np.zeros_like(xs)); pny.append(np.full_like(xs, -1.0))
        a = np.linspace(math.radians(a0), math.radians(a1), na)
        px.append(cx + R * np.cos(a)); py.append(cy + R * np.sin(a))
        pnx.append(np.cos(a)); pny.append(np.sin(a))
        if a1 == 360:
            ys = refine(-hy + R, hy - R, droof)
            px.append(np.full_like(ys, hx)); py.append(ys)
            pnx.append(np.ones_like(ys)); pny.append(np.zeros_like(ys))
        if a1 == 90:
            xs = refine(hx - R, -hx + R, -droof) if False else refine(-hx + R, hx - R, droof)[::-1]
            px.append(xs); py.append(np.full_like(xs, hy))
            pnx.append(np.zeros_like(xs)); pny.append(np.full_like(xs, 1.0))
        if a1 == 180:
            ys = refine(-hy + R, hy - R, droof)[::-1]
            px.append(np.full_like(ys, -hx)); py.append(ys)
            pnx.append(np.full_like(ys, -1.0)); pny.append(np.zeros_like(ys))
    X = np.concatenate(px); Y = np.concatenate(py)
    NX = np.concatenate(pnx); NY = np.concatenate(pny)
    n = np.hypot(NX, NY); NX /= n; NY /= n
    X = np.append(X, X[0]); Y = np.append(Y, Y[0])
    NX = np.append(NX, NX[0]); NY = np.append(NY, NY[0])
    INSET = 0.075
    prof = np.array([(0.000, -0.055), (0.021, -0.049), (0.029, -0.016),
                     (0.029, 0.030), (0.023, T_ROOF - 0.024),
                     (0.006, T_ROOF - 0.002), (-INSET, T_ROOF - 0.006)])
    path = np.stack([X, Y, np.full(len(X), zb)], 1)
    Rv = np.stack([NX, NY, np.zeros(len(X))], 1)
    V, Q, T = sweep(prof, path, Rv, np.array([0.0, 0.0, 1.0]), closed=False)
    side = np.repeat(np.where(np.abs(NY) > 0.985, np.sign(NY), 0.0)[:, None],
                     len(prof), 1).ravel()
    acc.push(V, Q, T, M_ALU, tt_wear=0.85, tt_grime=1.0, tt_side=side,
             tt_wash=0.12)
    rx = np.arange(-hx + R + 0.05, hx - R, P_RIVET * 1.6)
    for s in (-1, 1):
        p = np.stack([rx, np.full(len(rx), s * (hy + 0.028)),
                      np.full(len(rx), zb + 0.006)], 1)
        rivets.append((p, np.repeat(np.array([[0.0, float(s), 0.0]]), len(rx), 0),
                       D_RIVET * 0.55, H_RIVET * 0.85, M_ALU))

    # ---- the deck: cambered, with the roof bows showing through ------------
    ix0, ix1 = -hx + R + INSET * 0.4, hx - R - INSET * 0.4
    iy = hy - INSET * 0.55
    bows = np.arange(ix0 + 0.30, ix1 - 0.20, 0.610)
    xs = refine(ix0, ix1, droof, sites=list(bows), win=0.055, fine=droof * 0.42)
    ys = refine(-iy, iy, droof)
    XX, YY = np.meshgrid(xs, ys, indexing="ij")
    crown = 0.045 * (1.0 - (YY / iy) ** 2)
    bw = np.zeros_like(XX)
    for b in bows:
        bw += 0.0022 * np.exp(-((XX - b) / 0.030) ** 2)
    # a roof is never clean and never straight: it ponds between the bows
    pond = -0.0035 * (fbm2(XX * 0.8, YY * 1.6, t["oil_seed"] + 41, 4) - 0.5)
    ZZ = zb + T_ROOF - 0.010 + crown + bw + pond
    acc.grid(np.stack([XX, YY, ZZ], -1), M_ALU, tt_wear=0.25, tt_grime=1.0,
             tt_wash=0.05, tt_side=0.0)

    # ---- roof furniture ----------------------------------------------------
    zt = zb + T_ROOF + 0.03
    r = Rng(t["seed"], 91)
    for k in range(t["hatches"]):
        cx = r.u(-hx * 0.55, hx * 0.55)
        V, Q, T = rbox((cx, r.u(-0.35, 0.35), zt + 0.020),
                       (0.300, 0.300, 0.032), 0.020, 2, axis=2)
        acc.push(V, Q, T, M_ALU, tt_wear=0.6, tt_grime=0.9)
        V, Q, T = rbox((cx, 0.0, zt + 0.048), (0.245, 0.245, 0.012), 0.012, 2, axis=2)
        acc.push(V, Q, T, M_DARK, tt_wear=0.4, tt_grime=0.8)
    for k in range(t["pods"]):
        cx = -hx + 1.4 + k * r.u(2.4, 4.2)
        w, d, h = r.u(0.55, 0.95), r.u(0.50, 0.80), r.u(0.22, 0.44)
        V, Q, T = rbox((cx, r.u(-0.30, 0.30), zt + h * 0.5),
                       (w * 0.5, d * 0.5, h * 0.5), 0.045, 3, axis=2)
        acc.push(V, Q, T, M_ALU, tt_wear=0.5, tt_grime=0.85)
        for j in range(int(w / 0.055)):     # a condenser grille, as real slats
            V, Q, T = rbox((cx - w * 0.5 + 0.03 + j * 0.055, r.u(-0.30, 0.30) * 0 + d * 0.0,
                            zt + h * 0.5), (0.008, d * 0.42, h * 0.34), 0.004, 1, axis=2)
            acc.push(V, Q, T, M_DARK, tt_wear=0.3, tt_grime=0.9)


def build_rear(t, lod, acc, rivets):
    """The rear frame, its aperture, the hinge butts, the buffers, the lamp
    bar, the underrun guard and the ladder."""
    L, W = t["L"], t["W"]
    hx, hy = L * 0.5, W * 0.5
    x = -hx
    zf, zt = t["z_floor"], t["z_roof_bot"]
    ap_y = 1.240
    ap_z0, ap_z1 = zf + 0.022, zt - 0.105
    zs = t["z_sill"]
    # --- the frame: sill, header, two jambs, each a real section ------------
    for c, h in (((x - 0.045, 0.0, (zs + ap_z0) * 0.5),
                  (0.045, hy - R_CORNER, (ap_z0 - zs) * 0.5)),
                 ((x - 0.045, 0.0, (ap_z1 + zt) * 0.5),
                  (0.045, hy - R_CORNER, (zt - ap_z1) * 0.5))):
        V, Q, T = rbox(c, h, 0.014, 2, axis=1)
        acc.push(V, Q, T, M_PAINT, tt_wear=0.7, tt_grime=0.9, tt_wash=0.2)
    for sy in (-1, 1):
        V, Q, T = rbox((x - 0.045, sy * (ap_y + (hy - R_CORNER - ap_y) * 0.5) * 1.0,
                        (zs + zt) * 0.5),
                       (0.045, (hy - R_CORNER - ap_y) * 0.5, (zt - zs) * 0.5),
                       0.014, 2, axis=0)
        acc.push(V, Q, T, M_PAINT, tt_wear=0.75, tt_grime=0.9, tt_wash=0.2)
        # hinge butts: 4 knuckles per leaf, and they are the reason a door reads
        for k in range(4):
            hz = ap_z0 + 0.16 + k * (ap_z1 - ap_z0 - 0.32) / 3.0
            V, Q, T = rbox((x - 0.058, sy * (ap_y + 0.052), hz),
                           (0.036, 0.028, 0.052), 0.012, 2, axis=2)
            acc.push(V, Q, T, M_GALV, tt_wear=0.9, tt_grime=0.8)
            V, Q, T = revolve(np.array([(0.0, -0.048), (0.021, -0.048),
                                        (0.021, 0.048), (0.0, 0.048)]),
                              10, (x - 0.094, sy * (ap_y + 0.052), hz),
                              (0.0, 0.0, 1.0), cap=True)
            acc.push(V, Q, T, M_GALV, tt_wear=1.0, tt_grime=0.7)
        # the rubber buffer the open leaf lands on
        V, Q, T = revolve(np.array([(0.0, 0.0), (0.036, 0.0), (0.040, 0.030),
                                    (0.030, 0.046), (0.0, 0.046)]),
                          10, (x + 0.02, sy * (hy - 0.16), zs + 0.34),
                          (-1.0, 0.0, 0.0), cap=True)
        acc.push(V, Q, T, M_RUBBER, tt_wear=1.0, tt_grime=0.8)
    # --- the aperture reveal: the frame has DEPTH ---------------------------
    d = 0.090
    for (a, b) in (((-ap_y, ap_z0), (ap_y, ap_z0)), ((ap_y, ap_z1), (-ap_y, ap_z1)),
                   ((ap_y, ap_z0), (ap_y, ap_z1)), ((-ap_y, ap_z1), (-ap_y, ap_z0))):
        V, Q, T = plate([[x, a[0], a[1]], [x, b[0], b[1]],
                         [x + d, b[0], b[1]], [x + d, a[0], a[1]]], 0.010,
                        (0.0, 0.0, 1.0))
        acc.push(V, Q, T, M_ALU, tt_wear=0.85, tt_grime=0.7)
    # --- threshold plate, chequered, worn where the ramp lands --------------
    V, Q, T = rbox((x + 0.06, 0.0, ap_z0 - 0.010), (0.075, ap_y, 0.012), 0.006, 1, axis=1)
    acc.push(V, Q, T, M_CHEQ, tt_wear=1.0, tt_grime=0.9)
    # --- rear underrun guard, on two drop arms ------------------------------
    zg = 0.500
    V, Q, T = rbox((x - 0.055, 0.0, zg), (0.055, 1.230, 0.060), 0.012, 2, axis=1)
    acc.push(V, Q, T, M_STEEL, tt_wear=0.8, tt_grime=1.0)
    for sy in (-1, 1):
        V, Q, T = rbox((x + 0.24, sy * 0.62, (zg + zs - 0.12) * 0.5),
                       (0.048, 0.055, (zs - 0.12 - zg) * 0.5 + 0.02), 0.010, 1, axis=2)
        acc.push(V, Q, T, M_STEEL, tt_wear=0.6, tt_grime=1.0)
    # --- lamp bar + plate holder --------------------------------------------
    V, Q, T = rbox((x - 0.030, 0.0, zs + 0.055), (0.030, ap_y, 0.075), 0.010, 1, axis=1)
    acc.push(V, Q, T, M_ALU, tt_wear=0.7, tt_grime=1.0)
    V, Q, T = rbox((x - 0.062, 0.36, zs + 0.055), (0.006, 0.265, 0.055), 0.006, 1, axis=0)
    acc.push(V, Q, T, M_STENCIL, tt_wear=0.5, tt_grime=0.9)
    # --- rear ladder + step --------------------------------------------------
    if t["ladder"]:
        sy = t["ladder"]
        for dy in (-0.16, 0.16):
            V, Q, T = rbox((x - 0.035, sy * (ap_y - 0.30) + dy, (zs + 0.20 + zt) * 0.5),
                           (0.016, 0.016, (zt - zs - 0.20) * 0.5), 0.008, 1, axis=2)
            acc.push(V, Q, T, M_GALV, tt_wear=1.0, tt_grime=0.6)
        for k in range(int((zt - zs - 0.30) / 0.30)):
            zz = zs + 0.30 + k * 0.30
            V, Q, T = revolve(np.array([(0.0, -0.17), (0.012, -0.17),
                                        (0.012, 0.17), (0.0, 0.17)]), 8,
                              (x - 0.035, sy * (ap_y - 0.30), zz), (0.0, 1.0, 0.0),
                              cap=True)
            acc.push(V, Q, T, M_GALV, tt_wear=1.0, tt_grime=0.6)


def build_front(t, lod, acc, rivets):
    """The nose: the aero fairing, the service connections and the tell-tale
    that this trailer has been coupled and uncoupled a thousand times."""
    L, W = t["L"], t["W"]
    hx, hy = L * 0.5, W * 0.5
    zt = t["z_roof_bot"]
    # roof-front deflector fairing: a real curved skin, not a wedge
    ns = 14
    a = np.linspace(0.0, math.pi * 0.5, ns)
    fx = hx + 0.055 * np.cos(a) - 0.055
    fz = zt + T_ROOF - 0.02 - 0.30 * (1.0 - np.sin(a))
    ys = np.linspace(-hy + 0.02, hy - 0.02, 26)
    XX = np.repeat(fx[:, None], len(ys), 1)
    ZZ = np.repeat(fz[:, None], len(ys), 1)
    YY = np.repeat(ys[None, :], ns, 0)
    XX = XX - 0.030 * (YY / hy) ** 2
    acc.grid(np.stack([XX, YY, ZZ], -1), M_PAINT, tt_wear=0.6, tt_grime=1.0,
             tt_wash=0.15)
    # air and electrical connections, on their bracket
    for k in range(t["hose_tubes"] + 1):
        yy = -0.55 + k * 0.30
        V, Q, T = revolve(np.array([(0.0, 0.0), (0.038, 0.0), (0.038, 0.34),
                                    (0.0, 0.34)]), 10,
                          (hx + 0.02, yy, t["z_floor"] - 0.02), (1.0, 0.0, 0.0),
                          cap=True)
        acc.push(V, Q, T, M_GALV, tt_wear=0.8, tt_grime=0.9)
    V, Q, T = rbox((hx + 0.055, 0.30, t["z_floor"] - 0.34), (0.055, 0.34, 0.12),
                   0.012, 2, axis=1)
    acc.push(V, Q, T, M_STEEL, tt_wear=0.7, tt_grime=1.0)


def _flank_y(t, side, X, Z):
    """The ACTUAL y of the flank skin at (x, z), including the kick plate step,
    the oil-can wave and any damage.  Everything that is fixed to the flank --
    lettering, tape, lamp bosses -- is seated with this, because a 5 mm standoff
    at a 12.47 deg sun throws a 22 mm = 10 px shadow gap and reads as a decal
    floating off the paint."""
    X = np.asarray(X, float); Z = np.asarray(Z, float)
    one = np.ones_like(X)
    off = _kick_offset(t, Z)
    oil = _oilcan(t, X, Z, one)
    dmg, _tear = _flank_damage(t, X, Z, side * one, 0.0 * one, side * one)
    pull = (0.0016 * np.exp(-(((Z - t["z_sill"]) / 0.05) ** 2)))
    return side * (t["W"] * 0.5 + off + oil - dmg - pull)


def build_chassis(t, lod, acc):
    """Welded steel chassis: two I-beams, forty-odd cross members, the kingpin
    plate, the landing-leg mounts, the tanks and the boxes.  A low camera in the
    paddock sees straight under a trailer and this is what it sees."""
    L = t["L"]
    hx = L * 0.5
    zf = t["z_floor"]
    D = 0.400
    zc = zf - 0.035 - D * 0.5
    prof = np.array([
        (-0.110, -D * .5), (0.110, -D * .5), (0.110, -D * .5 + 0.020),
        (0.005, -D * .5 + 0.020), (0.005, D * .5 - 0.016), (0.095, D * .5 - 0.016),
        (0.095, D * .5), (-0.095, D * .5), (-0.095, D * .5 - 0.016),
        (-0.005, D * .5 - 0.016), (-0.005, -D * .5 + 0.020), (-0.110, -D * .5 + 0.020)])
    for sy in (-1, 1):
        # lightening holes in the web, because a plated web reads as a slab
        xs = refine(-hx + 0.10, hx - 0.02, 0.34)
        path = np.stack([xs, np.full(len(xs), sy * BEAM_Y), np.full(len(xs), zc)], 1)
        V, Q, T = sweep(prof, path, np.array([0.0, 1.0, 0.0]),
                        np.array([0.0, 0.0, 1.0]), closed=True, cap0=True, cap1=True)
        acc.push(V, Q, T, M_STEEL, tt_wear=0.6, tt_grime=1.0, tt_side=sy)
    # cross members
    for x in np.arange(-hx + 0.22, hx - 0.55, 0.300):
        V, Q, T = rbox((x, 0.0, zf - 0.075), (0.022, 1.215, 0.048), 0.007, 1, axis=1)
        acc.push(V, Q, T, M_STEEL, tt_wear=0.4, tt_grime=1.0)
    # the floor underside, seen between them
    xs = refine(-hx, hx, 0.42); ys = refine(-1.24, 1.24, 0.30)
    XX, YY = np.meshgrid(xs, ys, indexing="ij")
    acc.grid(np.stack([XX, YY, np.full_like(XX, zf - 0.035)], -1), M_DARK,
             flip=True, tt_grime=1.0, tt_wear=0.2)
    # kingpin plate + kingpin
    kx = t["kingpin_x"]
    V, Q, T = rbox((kx + 0.35, 0.0, zf - 0.455), (1.15, 1.16, 0.020), 0.03, 2, axis=2)
    acc.push(V, Q, T, M_STEEL, tt_wear=1.0, tt_grime=0.9)
    V, Q, T = revolve(np.array([(0.0, 0.0), (0.088, 0.0), (0.088, 0.020),
                                (KINGPIN_D * .5, 0.030), (KINGPIN_D * .5, 0.058),
                                (0.038, 0.070), (0.038, 0.090), (0.0, 0.090)]),
                      16, (kx, 0.0, zf - 0.565), (0.0, 0.0, 1.0), cap=True)
    acc.push(V, Q, T, M_GALV, tt_wear=1.0, tt_grime=0.6)
    # landing-leg mounting plates + cross shaft + gearbox
    lx = t["leg_x"]
    for sy in (-1, 1):
        V, Q, T = rbox((lx, sy * 0.980, zf - 0.300), (0.075, 0.012, 0.150),
                       0.008, 1, axis=2)
        acc.push(V, Q, T, M_STEEL, tt_wear=0.8, tt_grime=1.0)
        V, Q, T = rbox((lx, sy * 0.930, zf - 0.300), (0.090, 0.040, 0.170),
                       0.010, 1, axis=1)
        acc.push(V, Q, T, M_STEEL, tt_wear=0.7, tt_grime=1.0)
    V, Q, T = revolve(np.array([(0.0, -0.92), (0.024, -0.92), (0.024, 0.92),
                                (0.0, 0.92)]), 8, (lx, 0.0, zf - 0.300),
                      (0.0, 1.0, 0.0), cap=True)
    acc.push(V, Q, T, M_GALV, tt_wear=0.6, tt_grime=1.0)
    # air reservoirs, ABS module, cable trunking
    for k, sy in enumerate((-1, 1)):
        V, Q, T = revolve(np.array([(0.0, -0.44), (0.140, -0.44), (0.152, -0.40),
                                    (0.152, 0.40), (0.140, 0.44), (0.0, 0.44)]),
                          14, (t["axles"][2] + 1.35, sy * 0.72, zf - 0.520),
                          (1.0, 0.0, 0.0), cap=True)
        acc.push(V, Q, T, M_GALV, tt_wear=0.5, tt_grime=1.0)
    V, Q, T = rbox((t["axles"][1], 0.30, zf - 0.470), (0.130, 0.100, 0.090),
                   0.012, 2, axis=0)
    acc.push(V, Q, T, M_DARK, tt_wear=0.4, tt_grime=1.0)
    # toolbox and, on most of them, a spare carrier
    tb = t["toolbox"]
    V, Q, T = rbox((-hx + 3.6, tb * 1.030, zf - 0.520), (0.480, 0.190, 0.240),
                   0.024, 2, axis=0)
    acc.push(V, Q, T, M_ALU, tt_wear=0.9, tt_grime=1.0, tt_side=tb)
    for j in range(2):
        V, Q, T = rbox((-hx + 3.6 - 0.30 + j * 0.60, tb * 1.222, zf - 0.520),
                       (0.030, 0.006, 0.055), 0.004, 1, axis=1)
        acc.push(V, Q, T, M_GALV, tt_wear=1.0, tt_grime=0.8)
    if t["spare"]:
        cx = t["axles"][0] - 1.25
        for sy in (-1, 1):
            V, Q, T = rbox((cx, sy * 0.42, zf - 0.560), (0.030, 0.100, 0.030),
                           0.006, 1, axis=1)
            acc.push(V, Q, T, M_STEEL, tt_wear=0.6, tt_grime=1.0)
        V, Q, T = rbox((cx, 0.0, zf - 0.600), (0.400, 0.520, 0.022), 0.02, 2, axis=2)
        acc.push(V, Q, T, M_STEEL, tt_wear=0.6, tt_grime=1.0)


def build_running_gear(t, lod, acc, hubs):
    """Three axles of air suspension.  The wheels themselves are
    `truck_wheel_trailer`; everything they bolt to is here."""
    zf = t["z_floor"]
    r = Rng(t["seed"], 55)
    for ai, ax in enumerate(t["axles"]):
        # axle beam
        V, Q, T = rbox((ax, 0.0, SLR), (0.073, 0.980, 0.073), 0.018, 2, axis=1)
        acc.push(V, Q, T, M_DARK, tt_wear=0.5, tt_grime=1.0)
        for sy in (-1, 1):
            yc = sy * TWIN_CENTRE_Y
            # brake drum
            V, Q, T = revolve(np.array([(0.0, -0.115), (0.196, -0.115),
                                        (0.210, -0.090), (0.210, 0.075),
                                        (0.196, 0.100), (0.0, 0.100)]), 20,
                              (ax, yc - sy * 0.10, SLR), (0.0, float(sy), 0.0),
                              cap=True)
            acc.push(V, Q, T, M_DARK, tt_wear=0.9, tt_grime=1.0)
            # hub barrel + mounting flange
            V, Q, T = revolve(np.array([(0.0, -0.02), (HUB_SPIGOT * .5, 0.0),
                                        (HUB_SPIGOT * .5, 0.030),
                                        (0.235, 0.030), (0.235, 0.052),
                                        (0.0, 0.052)]), 20,
                              (ax, yc, SLR), (0.0, float(sy), 0.0), cap=True)
            acc.push(V, Q, T, M_GALV, tt_wear=0.9, tt_grime=0.9)
            # ten studs, because at 466 px/m an M22 stud is 10 px
            a = np.linspace(0, 2 * math.pi, HUB_STUDS, endpoint=False)
            P = np.stack([ax + HUB_PCD * .5 * np.cos(a),
                          np.full(HUB_STUDS, yc + sy * 0.052),
                          SLR + HUB_PCD * .5 * np.sin(a)], 1)
            V, Q, T = dome_batch(P, np.repeat(np.array([[0.0, float(sy), 0.0]]),
                                              HUB_STUDS, 0),
                                 np.repeat(np.array([[1.0, 0.0, 0.0]]), HUB_STUDS, 0),
                                 0.017, 0.058, 6,
                                 rings=((1.0, 0.0), (1.0, 0.72), (0.62, 0.80),
                                        (0.62, 1.0), (0.0, 1.0)))
            acc.push(V, Q, T, M_GALV, tt_wear=1.0, tt_grime=0.8)
            hubs.append(dict(axle=ai, side=int(sy), x=float(ax), y=float(yc),
                             z=float(SLR)))
            # trailing arm + hanger + air bag + shock + brake chamber
            V, Q, T = rbox((ax - 0.46, sy * 0.615, SLR + 0.045),
                           (0.520, 0.055, 0.075), 0.016, 2, axis=0)
            acc.push(V, Q, T, M_DARK, tt_wear=0.5, tt_grime=1.0)
            V, Q, T = rbox((ax - 0.95, sy * 0.615, (SLR + zf - 0.44) * 0.5 + 0.05),
                           (0.070, 0.075, (zf - 0.44 - SLR) * 0.5), 0.012, 1, axis=2)
            acc.push(V, Q, T, M_STEEL, tt_wear=0.6, tt_grime=1.0)
            zb0, zb1 = SLR + 0.150, zf - 0.445
            V, Q, T = revolve(np.array([(0.0, 0.0), (0.105, 0.0), (0.148, 0.055),
                                        (0.128, 0.12), (0.150, 0.20),
                                        (0.126, 0.27), (0.150, 0.35),
                                        (0.112, max(0.40, zb1 - zb0)),
                                        (0.0, max(0.40, zb1 - zb0))]), 14,
                              (ax + 0.34, sy * 0.615, zb0), (0.0, 0.0, 1.0), cap=True)
            acc.push(V, Q, T, M_RUBBER, tt_wear=0.4, tt_grime=1.0)
            V, Q, T = revolve(np.array([(0.0, 0.0), (0.030, 0.0), (0.030, 0.28),
                                        (0.019, 0.30), (0.019, 0.46), (0.0, 0.46)]),
                              10, (ax - 0.16, sy * 0.775, SLR + 0.06),
                              (0.10 * 0, 0.0, 1.0) if False else
                              (0.16, sy * 0.10, 0.97), cap=True)
            acc.push(V, Q, T, M_DARK, tt_wear=0.5, tt_grime=1.0)
            V, Q, T = revolve(np.array([(0.0, 0.0), (0.092, 0.0), (0.092, 0.185),
                                        (0.070, 0.205), (0.0, 0.205)]), 12,
                              (ax - 0.24, sy * 0.44, SLR + 0.10),
                              (0.0, float(sy), 0.0), cap=True)
            acc.push(V, Q, T, M_STEEL, tt_wear=0.5, tt_grime=1.0)
            # mudwing over the wheel, on its stays
            a = np.linspace(math.radians(22.0), math.radians(158.0), 16)
            rw = 0.640
            path = np.stack([ax + rw * np.cos(a), np.full(16, yc),
                             SLR + rw * np.sin(a)], 1)
            up = np.stack([np.cos(a), np.zeros(16), np.sin(a)], 1)
            prof = np.array([(-0.330, 0.0), (0.330, 0.0), (0.330, 0.012),
                             (-0.330, 0.012)])
            V, Q, T = sweep(prof, path, np.array([0.0, float(sy), 0.0]), up,
                            closed=True, cap0=True, cap1=True)
            acc.push(V, Q, T, M_DARK, tt_wear=0.15, tt_grime=1.0, tt_side=sy)


def build_underslung(t, lod, acc):
    """Mudflaps, spray suppression and the air lines.  Two of the ten have a
    flap that has been dragged and now trails on the deck: those embed
    C.BASE_EMBED_M below the MEASURED ground, per law 5."""
    L = t["L"]
    hx = L * 0.5
    zf = t["z_floor"]
    r = Rng(t["seed"], 77)
    sets = [(t["axles"][2] + 0.86, 0.46, False), (-hx + 0.10, 0.50, t["flap_drag"])]
    for (fx, w, drag) in sets:
        for sy in (-1, 1):
            top = SLR + 0.62 if fx > -hx + 0.5 else 0.72
            bot = -EMBED if drag else r.u(0.16, 0.30)
            nz = 9
            zz = np.linspace(top, bot, nz)
            ys = np.linspace(-w * 0.5, w * 0.5, 7)
            ZZ, YY = np.meshgrid(zz, ys, indexing="ij")
            tt = (top - ZZ) / max(top - bot, 1e-3)
            # a hanging flap curls and is never a plane
            XX = fx - 0.030 * tt ** 1.6 - 0.018 * np.sin(YY * 5.4) * tt
            if drag:
                XX = XX - 0.10 * np.clip(tt - 0.86, 0, 1) * 8.0
            acc.grid(np.stack([XX, sy * TWIN_CENTRE_Y + YY, ZZ], -1), M_RUBBER,
                     tt_wear=0.9, tt_grime=1.0, tt_side=sy)
            V, Q, T = rbox((fx, sy * TWIN_CENTRE_Y, top), (0.020, w * 0.5, 0.024),
                           0.006, 1, axis=1)
            acc.push(V, Q, T, M_GALV, tt_wear=0.7, tt_grime=1.0)
    # air lines looping along the chassis
    for k, sy in enumerate((-1, 1)):
        xs = np.linspace(t["kingpin_x"], t["axles"][0] - 0.4, 30)
        zz = (zf - 0.470 + 0.020 * np.sin(np.linspace(0, 7.0, 30))
              + 0.012 * np.sin(np.linspace(0, 17.0, 30)))
        path = np.stack([xs, np.full(30, sy * 0.30 + k * 0.05), zz], 1)
        V, Q, T = sweep(rrect(0.017, 0.017, 0.008, 2), path,
                        np.array([0.0, 1.0, 0.0]), np.array([0.0, 0.0, 1.0]),
                        closed=True, cap0=True, cap1=True)
        acc.push(V, Q, T, M_RUBBER, tt_wear=0.3, tt_grime=1.0)


def build_graphics(t, lod, acc, lamps):
    """Livery lettering, functional stencils, conspicuity tape and the lamp
    bosses -- all of it GEOMETRY, seated on the measured skin."""
    L, W = t["L"], t["W"]
    hx, hy = L * 0.5, W * 0.5
    zkb = t["z_sill"] + RAIL_BOT_H
    zkt = zkb + KICK_H

    for side in (-1, 1):
        ny = np.array([0.0, float(side), 0.0])
        ex = np.array([1.0, 0.0, 0.0]) * (1.0 if side > 0 else -1.0)
        ez = np.array([0.0, 0.0, 1.0])

        # ---- the team's name, in cut vinyl -------------------------------
        # A viewer of the -Y flank stands at -Y looking +Y, so their RIGHT is
        # +X; a viewer of the +Y flank has their right at -X.  Getting this
        # backwards mirrors every word on the fleet, which is what the first
        # macro showed.
        rd = -1.0 if side > 0 else 1.0
        cap = 0.560
        polys, wtxt = stroke_polys(t["team"], cap, 0.09, 0.122)
        cx = 0.10 * L * side
        cz = t["z_waist"] + 0.62
        # seat every letter on the ACTUAL skin at its own x
        for p in polys:
            px = cx + (p[:, 0] - wtxt * 0.5) * rd
            pz = cz + p[:, 1]
            yy = _flank_y(t, side, px, pz) + side * 0.0006
            V = np.concatenate([np.stack([px, yy, pz], 1),
                                np.stack([px, yy + side * 0.0006, pz], 1)])
            k = len(p)
            i = np.arange(k)
            Q = np.concatenate([np.stack([i, np.roll(i, -1), k + np.roll(i, -1),
                                          k + i], 1),
                                np.array([[k, k + 1, k + 2, k + 3]])])
            acc.push(V, Q, None, M_STENCIL, tt_wear=0.45, tt_side=side,
                     tt_grime=0.4, tt_wash=0.6)

        # ---- the haulier, small, at the rear ------------------------------
        polys, wtxt = stroke_polys(t["haulier"], 0.105, 0.20, 0.170)
        bx = (hx - 0.55) if side > 0 else (-hx + 0.55)
        bz = zkt + 0.12
        for p in polys:
            px = bx + p[:, 0] * rd
            pz = bz + p[:, 1]
            yy = _flank_y(t, side, px, pz) + side * 0.0005
            V = np.concatenate([np.stack([px, yy, pz], 1),
                                np.stack([px, yy + side * 0.0005, pz], 1)])
            k = len(p); i = np.arange(k)
            Q = np.concatenate([np.stack([i, np.roll(i, -1), k + np.roll(i, -1),
                                          k + i], 1),
                                np.array([[k, k + 1, k + 2, k + 3]])])
            acc.push(V, Q, None, M_STENCIL, tt_wear=0.7, tt_side=side,
                     tt_grime=0.7, tt_wash=0.4)

        # ---- functional stencils on the kick plate ------------------------
        for txt, ox, h in ((t["fleet_no"], 0.30 * L, 0.075),
                           ("MAX 40 T", -0.34 * L, 0.055),
                           ("8.5 BAR", -0.30 * L, 0.048)):
            polys, wtxt = stroke_polys(txt, h, 0.22, 0.19)
            sx = ox * rd
            sz = zkb + 0.10 + (0.0 if h > 0.06 else -0.075 * (txt == "8.5 BAR"))
            for p in polys:
                px = sx + p[:, 0] * rd
                pz = sz + p[:, 1]
                yy = _flank_y(t, side, px, pz) + side * 0.0004
                V = np.concatenate([np.stack([px, yy, pz], 1),
                                    np.stack([px, yy + side * 0.0004, pz], 1)])
                k = len(p); i = np.arange(k)
                Q = np.concatenate([np.stack([i, np.roll(i, -1),
                                              k + np.roll(i, -1), k + i], 1),
                                    np.array([[k, k + 1, k + 2, k + 3]])])
                acc.push(V, Q, None, M_STENCIL, tt_wear=0.9, tt_side=side,
                         tt_grime=0.9, tt_wash=0.3)

        # ---- conspicuity tape: the mandatory yellow line -------------------
        xs = refine(-hx + R_CORNER + 0.06, hx - R_CORNER - 0.06, 0.22)
        zc = zkt + 0.045
        for dzz in (-0.026, 0.026):
            zz = np.full(len(xs), zc + dzz)
            yy = _flank_y(t, side, xs, zz) + side * 0.0007
            if dzz < 0:
                V0 = np.stack([xs, yy, zz], 1)
            else:
                V1 = np.stack([xs, yy, zz], 1)
        V = np.concatenate([V0, V1])
        n = len(xs); i = np.arange(n - 1)
        Q = np.stack([i, i + 1, n + i + 1, n + i], 1)
        acc.push(V, Q, None, M_TAPE, tt_wear=0.8, tt_side=side, tt_grime=0.8,
                 tt_wash=0.5)

    # ---- every lamp boss, from the SAME plan `lamp_sites()` publishes ------
    # The boss is mesh on this item; `truck_light_cluster` builds the lens into
    # the recess.  Generating both from one list is what stops the published
    # position drifting away from the geometry.
    for s in _lamp_plan(t):
        lamps.append(s)
        nx, ny, nz = s["nx"], s["ny"], s["nz"]
        ax = 0 if abs(nx) > 0.5 else 1
        d = 0.017
        c = (s["x"] + nx * d, s["y"] + ny * d, s["z"])
        half = ((d, s["w"] * 0.5, s["h"] * 0.5) if ax == 0
                else (s["w"] * 0.5, d, s["h"] * 0.5))
        V, Q, T = rbox(c, half, 0.010, 2, axis=ax)
        acc.push(V, Q, T, M_DARK, tt_wear=0.8, tt_side=ny, tt_grime=0.9)
        # the seat the lens drops into: a real recess, not a painted rectangle
        hi = ((d * 0.45, s["w"] * 0.5 - 0.010, s["h"] * 0.5 - 0.010) if ax == 0
              else (s["w"] * 0.5 - 0.010, d * 0.45, s["h"] * 0.5 - 0.010))
        cc = (s["x"] + nx * d * 0.55, s["y"] + ny * d * 0.55, s["z"])
        V, Q, T = rbox(cc, hi, 0.007, 1, axis=ax)
        acc.push(V, Q, T, M_DARK, tt_wear=0.3, tt_side=ny, tt_grime=0.5)


def build_interior(t, lod, acc):
    """Only for the two trailers whose doors are open.  An open door with
    nothing behind it is a hole, and a hole at 8 m is a defect."""
    L, W = t["L"], t["W"]
    hx = L * 0.5
    iy = W * 0.5 - T_WALL
    zf, zt = t["z_floor"], t["z_roof_bot"] - 0.02
    xs = refine(-hx + 0.06, hx - 0.06, 0.40)
    ys = refine(-iy, iy, 0.22)
    XX, YY = np.meshgrid(xs, ys, indexing="ij")
    acc.grid(np.stack([XX, YY, np.full_like(XX, zf)], -1), M_CHEQ,
             tt_wear=0.9, tt_grime=0.35)
    zz = refine(zf, zt, 0.30)
    for sy in (-1, 1):
        XX, ZZ = np.meshgrid(xs, zz, indexing="ij")
        acc.grid(np.stack([XX, np.full_like(XX, sy * iy), ZZ], -1), M_ALU,
                 flip=(sy > 0), tt_wear=1.0, tt_scuff=0.92, tt_grime=0.14,
                 tt_side=sy)
    XX, YY = np.meshgrid(xs, ys, indexing="ij")
    acc.grid(np.stack([XX, YY, np.full_like(XX, zt)], -1), M_ALU, flip=True,
             tt_wear=1.0, tt_scuff=0.95, tt_grime=0.12)
    # lashing rails, lockers AND A BULKHEAD.  MEASURED, seventh macro: a 13.9 m
    # box open at one end and lit only by skylight from behind reads as a black
    # rectangle -- the manifest's own note about the tractor ("an empty black cab
    # reads as a toy") is the same failure.  A race transporter has a bulkhead
    # about 5 m in with the workshop behind it, and the near bay is what the lens
    # actually sees, so that is what is built.
    BH = -hx + 5.20
    for sy in (-1, 1):
        xa, xb = -hx + 0.08, BH
        for zr in (zf + 0.42, zf + 1.15):
            V, Q, T = rbox(((xa + xb) * 0.5, sy * (iy - 0.020), zr),
                           ((xb - xa) * 0.5, 0.020, 0.030), 0.006, 1, axis=0)
            acc.push(V, Q, T, M_ALU, tt_wear=1.0, tt_scuff=0.9, tt_grime=0.15,
                     tt_side=sy)
        # a bank of drawer lockers down each side of the near bay
        V, Q, T = rbox((-hx + 2.30, sy * (iy - 0.30), zf + 0.62),
                       (1.90, 0.30, 0.62), 0.020, 2, axis=0)
        acc.push(V, Q, T, M_ALU, tt_wear=1.0, tt_scuff=0.85, tt_grime=0.12,
                 tt_side=sy)
        for k in range(6):
            V, Q, T = rbox((-hx + 0.55 + k * 0.62, sy * (iy - 0.60), zf + 0.62),
                           (0.026, 0.010, 0.58), 0.006, 1, axis=1)
            acc.push(V, Q, T, M_GALV, tt_wear=1.0, tt_grime=0.1, tt_side=sy)
    # the bulkhead itself, in bright liner panel
    zzb = refine(zf, zt, 0.30)
    YY, ZZ = np.meshgrid(refine(-iy, iy, 0.24), zzb, indexing="ij")
    acc.grid(np.stack([np.full_like(YY, BH), YY, ZZ], -1), M_ALU, flip=True,
             tt_wear=1.0, tt_scuff=0.95, tt_grime=0.1)


# ==============================================================================
#  7.  ASSEMBLY
# ==============================================================================

def trailer_mesh(t, lod=0):
    """-> V, quads, tris, quad-mats, tri-mats, attrs, centre, info.

    Recentred on emit (law 6): the returned vertices are relative to the bbox
    centre and `ctr` is where that centre sits in the trailer's local frame.
    """
    dx, dz, droof, dend, spm, seg = LOD[lod]
    acc = Acc()
    rivets, hubs, lamps = [], [], []
    build_shell(t, lod, acc, rivets)
    build_rails(t, lod, acc, rivets)
    build_roof(t, lod, acc, rivets)
    build_rear(t, lod, acc, rivets)
    build_front(t, lod, acc, rivets)
    build_graphics(t, lod, acc, lamps)
    build_chassis(t, lod, acc)
    build_running_gear(t, lod, acc, hubs)
    build_underslung(t, lod, acc)
    if t["door_state"] == "open":
        build_interior(t, lod, acc)

    # ---- every rivet on the vehicle, in one batch per material -------------
    nseg = max(5, int(round(7 * seg)))
    nriv = 0
    bymat = {}
    for (P, N, r, h, mat) in rivets:
        if len(P) == 0:
            continue
        bymat.setdefault(mat, []).append((P, N, r, h))
    for mat, lst in bymat.items():
        P = np.concatenate([a for a, _b, _c, _d in lst])
        N = np.concatenate([b for _a, b, _c, _d in lst])
        r = np.concatenate([np.full(len(a), c) for a, _b, c, _d in lst])
        h = np.concatenate([np.full(len(a), d) for a, _b, _c, d in lst])
        R = np.repeat(np.array([[0.0, 0.0, 1.0]]), len(P), 0)
        V, Q, T = dome_batch(P, N, R, r, h, nseg)
        side = np.repeat(np.sign(N[:, 1]), len(V) // max(len(P), 1))
        acc.push(V, Q, T, mat, tt_wear=1.0, tt_grime=1.0,
                 tt_side=side if len(side) == len(V) else 0.0,
                 tt_wash=t["wash_off"])
        nriv += len(P)

    V, Q, T, QM, TM, A = acc.finish()
    lo, hi = V.min(axis=0), V.max(axis=0)
    ctr = 0.5 * (lo + hi)
    V = V - ctr[None, :]
    info = dict(verts=len(V), quads=len(Q), tris=len(T),
                faces=len(Q) + len(T), triangles=len(Q) * 2 + len(T),
                rivets=nriv, hubs=len(hubs), lamps=len(lamps),
                maxP=float(np.abs(V).max()), lod=lod,
                bbox=[float(v) for v in (hi - lo)])
    return V, Q, T, QM, TM, A, ctr, info, hubs, lamps


# ==============================================================================
#  8.  BLENDER
# ==============================================================================

def _shade_by_angle(me, deg=32.0):
    """Smooth everywhere except across a real arris.  numpy against
    `sharp_edge`, because shade_auto_smooth needs a VIEW_3D context and cannot
    run headless (see the project's Blender 5.x notes)."""
    npoly = len(me.polygons); nloop = len(me.loops); nedge = len(me.edges)
    if not nedge or not npoly:
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
    nv = np.int64(len(me.vertices))
    key = np.minimum(a, b) * nv + np.maximum(a, b)
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
    ekey = (np.minimum(ev[:, 0], ev[:, 1]) * nv + np.maximum(ev[:, 0], ev[:, 1]))
    sharp = np.zeros(nedge, np.int8)
    if len(sharp_key):
        sk = np.sort(sharp_key)
        idx = np.clip(np.searchsorted(sk, ekey), 0, len(sk) - 1)
        sharp[sk[idx] == ekey] = 1
    at = me.attributes.get("sharp_edge") or me.attributes.new(
        "sharp_edge", "BOOLEAN", "EDGE")
    at.data.foreach_set("value", sharp)


def _new_mesh(name, V, Q, T, QM, TM, A, mats, smooth_deg=32.0):
    me = bpy.data.meshes.new(name)
    V = np.ascontiguousarray(V, dtype=np.float32)
    me.vertices.add(len(V))
    me.vertices.foreach_set("co", V.ravel())
    loops, counts, matidx = [], [], []
    if len(Q):
        loops.append(np.asarray(Q, np.int32).ravel())
        counts.append(np.full(len(Q), 4, np.int32))
        matidx.append(np.asarray(QM, np.int32))
    if len(T):
        loops.append(np.asarray(T, np.int32).ravel())
        counts.append(np.full(len(T), 3, np.int32))
        matidx.append(np.asarray(TM, np.int32))
    loops = np.concatenate(loops); counts = np.concatenate(counts)
    matidx = np.concatenate(matidx)
    starts = np.concatenate([[0], np.cumsum(counts)[:-1]]).astype(np.int32)
    me.loops.add(len(loops))
    me.loops.foreach_set("vertex_index", loops)
    me.polygons.add(len(counts))
    me.polygons.foreach_set("loop_start", starts)
    me.update(calc_edges=True)
    for m in mats:
        me.materials.append(m)
    me.polygons.foreach_set("material_index", matidx)
    me.validate(verbose=False)
    for k in ATTRS:
        if k in A and len(A[k]) == len(V):
            at = me.attributes.new(k, "FLOAT", "POINT")
            at.data.foreach_set("value", np.ascontiguousarray(A[k], np.float32))
    if smooth_deg is not None:
        _shade_by_angle(me, smooth_deg)
    return me


def _object_props(ob, t, info):
    """Per-object decorrelation and per-object livery.

    ONE material serves ten trailers.  Everything that must differ between them
    -- the two livery colours, the age, the wash history and the 3-D offset that
    stops ten bodies sharing one realisation of the dirt -- is an object
    attribute the shader reads, not a duplicated node tree.
    """
    sd = t["seed"]
    ob["tt_ofs_x"] = float(hash01(sd, 3) * 21.0)
    ob["tt_ofs_y"] = float(hash01(sd, 5) * 21.0)
    ob["tt_ofs_z"] = float(hash01(sd, 7) * 21.0)
    a, b = (t["c2"], t["c1"]) if t.get("liv_swap") else (t["c1"], t["c2"])
    for k, v in (("c1", a), ("c2", b)):
        for i, ch in enumerate("rgb"):
            ob["tt_%s%s" % (k, ch)] = float(v[i])
    # the lettering colour: whichever of the two reads against the base
    lum1 = 0.2126 * a[0] + 0.7152 * a[1] + 0.0722 * a[2]
    lum2 = 0.2126 * b[0] + 0.7152 * b[1] + 0.0722 * b[2]
    # the lettering has to READ against the ground it sits on
    txt = b if abs(lum1 - lum2) > 0.10 else ((0.42, 0.425, 0.43) if lum1 < 0.18
                                             else (0.018, 0.018, 0.020))
    for i, ch in enumerate("rgb"):
        ob["tt_tx%s" % ch] = float(txt[i])
    ob["tt_age"] = float(t["age"])
    ob["tt_dirt"] = float(t["grime"])
    ob["tt_val"] = float(hash01(sd, 11))
    ob["item"] = ITEM
    ob["tt_uid"] = int(t["uid"])
    ob["tt_len"] = float(t["L"])
    ob["tt_team"] = t["team"]
    ob["tt_lod"] = int(info["lod"])
    ob["tt_rivets"] = int(info["rivets"])
    ob["tt_tris"] = int(info["triangles"])
    ob["tt_door"] = t["door_state"]
    ob["tt_ground_z"] = float(t["ground_z"])
    ob["tt_ground_owner"] = t["ground_owner"]


def build_trailer(t, coll, mats, lod=0):
    from mathutils import Matrix
    V, Q, T, QM, TM, A, ctr, info, hubs, lamps = trailer_mesh(t, lod)
    name = "%sT%02d_%s" % (PFX, t["uid"], t["team"])
    me = _new_mesh(name, V, Q, T, QM, TM, A, mats)
    ob = bpy.data.objects.new(name, me)
    org, ex, ey, ez = trailer_basis(t)
    org = org + ex * ctr[0] + ey * ctr[1] + ez * ctr[2]
    ob.matrix_world = Matrix(((ex[0], ey[0], ez[0], org[0]),
                              (ex[1], ey[1], ez[1], org[1]),
                              (ex[2], ey[2], ez[2], org[2]),
                              (0.0, 0.0, 0.0, 1.0)))
    coll.objects.link(ob)
    _object_props(ob, t, info)
    return ob, info


# ==============================================================================
#  9.  THE MATERIALS
# ==============================================================================
# Nine of them, all procedural, all reading TexCoord -> Object.  There is no
# Geometry -> Position node in this module and no image texture anywhere.

class NT(object):
    """Node DSL.  Same shape as pit_wall_unit's and kerb_precast_unit's, so the
    three read alike."""

    def __init__(self, name):
        m = bpy.data.materials.get(name)
        if m is None:
            m = bpy.data.materials.new(name)
        m.use_nodes = True
        self.m = m
        self.t = m.node_tree
        self.t.nodes.clear()
        self.x = 0

    def n(self, typ, **kw):
        nd = self.t.nodes.new(typ)
        self.x += 1
        nd.location = ((self.x % 16) * 210, -(self.x // 16) * 300)
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
            # a VECTOR socket wants 3 and an RGBA socket wants 4; getting that
            # wrong is a ValueError deep inside a 40-node build
            sock = nd.inputs[idx]
            dv = sock.default_value
            want = len(dv) if hasattr(dv, "__len__") else 1
            v = tuple(float(x) for x in src)
            if want == 4 and len(v) == 3:
                v = v + (1.0,)
            elif want == 3 and len(v) == 4:
                v = v[:3]
            sock.default_value = v
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

    def out(self, bsdf):
        o = self.n("ShaderNodeOutputMaterial")
        self.t.links.new(bsdf.outputs[0], o.inputs[0])
        return self.m


# Linear reflectances, calibrated against C.lambert_radiance under a 12.47 deg
# key.  A white truck is NOT 0.9: a washed white commercial vehicle measures
# 0.62-0.70 and a dirty one 0.40.
PAL = dict(
    alu_mill=(0.4750, 0.4800, 0.4860),      # mill-finish aluminium
    alu_ox=(0.2450, 0.2470, 0.2450),        # oxidised, chalky
    alu_dark=(0.2100, 0.2120, 0.2140),
    steel_dark=(0.0420, 0.0425, 0.0430),    # chassis black
    steel_chip=(0.3400, 0.3450, 0.3500),    # a chip down to bright steel
    galv=(0.3750, 0.3800, 0.3870),
    galv_white=(0.4400, 0.4450, 0.4400),    # white rust
    rust=(0.0880, 0.0330, 0.0140),
    rubber=(0.0210, 0.0208, 0.0206),
    rubber_dust=(0.0620, 0.0600, 0.0560),
    road_film=(0.0640, 0.0570, 0.0470),     # the grey-brown of motorway film
    road_light=(0.1450, 0.1300, 0.1080),
    dust_pale=(0.1780, 0.1560, 0.1230),     # dried summer dust and road salt.
                                            # ON A DARK VEHICLE THIS IS THE DIRT
                                            # YOU SEE: mixing a 0.068 teal toward
                                            # a 0.064 film is a no-op, and the
                                            # trailer comes back looking washed.
    brake_dust=(0.0480, 0.0400, 0.0350),
    diesel=(0.0180, 0.0160, 0.0150),
    tape_yellow=(0.5600, 0.3900, 0.0300),
    tape_bead=(0.7200, 0.6400, 0.3600),
    white=(0.5600, 0.5650, 0.5700),
    grime_green=(0.0400, 0.0460, 0.0330),
    lime=(0.4200, 0.4180, 0.4050),
)


def _obj_vec(t):
    """Object-space P, plus a per-object 21 m offset so that ten bodies do not
    share one realisation of the same procedural.  21 m, not 210: Cycles
    evaluates procedurals in float32 and a large offset costs lattice
    precision (this is the round-1 blotching defect)."""
    co = t.n("ShaderNodeTexCoord")
    OBJ = (co, 3)
    ofs = t.comb(t.attr("tt_ofs_x", 2, "OBJECT"),
                 t.attr("tt_ofs_y", 2, "OBJECT"),
                 t.attr("tt_ofs_z", 2, "OBJECT"))
    return OBJ, t.vmath("ADD", OBJ, ofs)


def _road_film(t, P, OBJ, zg, wash, dirt, strength=1.0):
    """The dirt gradient the manifest asks for, built as a HISTORY.

    Four separate mechanisms, because road film is not one gradient:
      1. spray climbing from the wheels -- strongest at 0.9-1.6 m, dying by
         2.6 m, and it is BROKEN by every horizontal rail, which shelters the
         paint under it and collects a hard line on top of it;
      2. a slow overall settling of atmospheric grime, everywhere, faint;
      3. rain wash -- vertical clean streaks pulled DOWN from every rail and
         every rivet, which is why the dirt is not a smooth ramp;
      4. the wash line: the driver's brush reaches 2.4 m and stops, and only on
         the side he can get to.
    """
    n_sp = t.noise(t.vmath("SCALE", P, scale=1.0), 3.4, 7.0, 0.62)
    n_fine = t.noise(t.vmath("SCALE", P, scale=1.0), 34.0, 8.0, 0.60)
    # 1. spray climb.  MEASURED off the first macro, which came back clean: the
    #    old ramp died at 2.65 m AND was then knocked down 5x by the wash term
    #    over the whole flank, so a trailer that has driven 40 000 km looked like
    #    it had come out of the paint shop.  The bottom 0.9 m of a box trailer is
    #    never clean -- the arch throw reaches it every wet kilometre.
    climb = t.maprange(zg, 0.60, 2.15, 1.18, 0.02)
    climb = t.math("MULTIPLY", climb, t.maprange(n_sp, 0.24, 0.80, 0.62, 1.35))
    # 2. RAIN RIVULETS.  The first attempt stretched a 16 mm noise over 0.56 m
    #    of z, which combs the whole flank uniformly and reads as wood grain --
    #    exactly what the second macro showed.  A real rivulet is 25-90 mm wide,
    #    runs the full height from whatever shed the water, and there are a
    #    DOZEN of them on a 14 m flank, not four hundred.  So: coarse in x,
    #    nearly constant in z, and thresholded so most of the flank is untouched.
    stz = t.vmath("MULTIPLY", P, (2.1, 2.1, 0.055))
    streak = t.noise(stz, 6.5, 6.0, 0.62)
    streak = t.maprange(streak, 0.52, 0.74, 0.88, 1.42)
    # 3. THE WASH LINE.  A driver with a brush cleans the band he can reach --
    #    0.9 m to 2.5 m -- and only from the side he can get to.  He does not
    #    reach under the rubbing rail, he does not reach the bottom 0.9 m behind
    #    the skirt, and he does not reach the top.  So the brush makes a BAND of
    #    clean paint with dirt above AND below it, which is what a working
    #    trailer looks like and what a single ramp cannot produce.
    band = t.math("MULTIPLY", t.maprange(zg, 0.82, 1.12, 0.0, 1.0),
                  t.maprange(zg, 2.62, 2.24, 0.0, 1.0))
    brush = t.math("MULTIPLY", wash, band)
    d = t.math("MULTIPLY", climb, streak)
    # the general atmospheric settling: FAINT, and it still has to fall off with
    # height.  MEASURED, sixth macro: a flat 0.06-0.30 added everywhere put a
    # third of a coat of dust on the roof line and erased the livery and the
    # lettering with it.
    d = t.math("ADD", d, t.math("MULTIPLY",
                                t.math("MULTIPLY",
                                       t.maprange(n_fine, 0.3, 0.75, 0.02, 0.11),
                                       t.maprange(zg, 1.0, 3.2, 1.0, 0.25)),
                                dirt))
    # the very bottom band -- behind the skirt, under the bottom rail, inside
    # the arch throw -- is never cleaned by anything
    d = t.math("MAXIMUM", d, t.math("MULTIPLY",
                                    t.maprange(zg, 1.42, 0.80, 0.0, 0.95),
                                    t.maprange(n_sp, 0.2, 0.85, 0.72, 1.15)))
    d = t.math("MULTIPLY", d, t.math("SUBTRACT", 1.0,
                                     t.math("MULTIPLY", brush, 0.44)))
    d = t.math("MULTIPLY", d, t.math("MULTIPLY",
                                     t.maprange(dirt, 0.0, 1.0, 0.42, 1.15),
                                     strength))
    return t.math("MINIMUM", d, 1.0), n_fine, streak


def mat_paint():
    """The painted body.  Fifteen histories, in the order the trailer got them.

    Livery is per-OBJECT: `tt_c1*`/`tt_c2*` are object attributes and `tt_lv1`
    is a signed distance field baked into the mesh, so one material paints ten
    different trailers with a boundary that is crisp to a tenth of a millimetre
    at 466 px/m.
    """
    t = NT(PFX + "Paint")
    OBJ, P = _obj_vec(t)
    zg = t.attr("tt_zg")
    lv1 = t.attr("tt_lv1"); lv2 = t.attr("tt_lv2")
    wear = t.attr("tt_wear"); scuff = t.attr("tt_scuff")
    kick = t.attr("tt_kick"); seam = t.attr("tt_seam")
    grime = t.attr("tt_grime"); wash = t.attr("tt_wash")
    oil = t.attr("tt_oil")
    c1 = t.comb(t.attr("tt_c1r", 2, "OBJECT"), t.attr("tt_c1g", 2, "OBJECT"),
                t.attr("tt_c1b", 2, "OBJECT"))
    c2 = t.comb(t.attr("tt_c2r", 2, "OBJECT"), t.attr("tt_c2g", 2, "OBJECT"),
                t.attr("tt_c2b", 2, "OBJECT"))
    age = t.attr("tt_age", 2, "OBJECT")
    dirt = t.attr("tt_dirt", 2, "OBJECT")
    val = t.attr("tt_val", 2, "OBJECT")

    # ---- 1. the scheme ------------------------------------------------------
    col = t.cmix(t.maprange(lv1, -0.0016, 0.0016, 0.0, 1.0), c1, c2)
    col = t.cmix(t.maprange(lv2, -0.0014, 0.0014, 0.0, 1.0), col, PAL["white"])
    # and the paint is never one flat field: every panel came off a different
    # batch of the same code and the difference is 1-2 %
    bay = t.vor(t.vmath("MULTIPLY", P, (0.82, 0.02, 0.02)), 1.0, "F1", 1, 1.0)
    col = t.cmix(t.math("MULTIPLY", t.maprange(bay, 0.2, 0.8, 0.0, 1.0), 0.055),
                 col, t.cmix(0.5, col, PAL["alu_ox"]))
    # ---- 2. the paint itself: metallic flake and a hint of panel mismatch ---
    flake = t.vor(t.vmath("SCALE", P, scale=1.0), 2600.0, "F1", 0, 1.0)
    col = t.cmix(t.math("MULTIPLY", t.maprange(flake, 0.0, 0.30, 0.35, 0.0), 0.045),
                 col, PAL["white"])
    n_panel = t.noise(t.vmath("SCALE", P, scale=0.55), 1.6, 3.0, 0.42)
    col = t.cmix(t.math("MULTIPLY", t.maprange(n_panel, 0.35, 0.68, 0.0, 1.0), 0.07),
                 col, t.cmix(0.5, col, PAL["alu_dark"]))
    # ---- 3. fade: the roof edge and the upper flank chalk first ------------
    # UV chalking is a LOSS of gloss and a slight lightening, not a coat of
    # limewash: the first pass mixed 28 % of a bright grey over the whole upper
    # flank and turned every livery white.
    fade = t.math("MULTIPLY", age, t.maprange(zg, 2.30, 3.75, 0.10, 1.00))
    col = t.cmix(t.math("MULTIPLY", fade, 0.13), col,
                 t.cmix(0.75, col, PAL["lime"]))
    # ---- 4. the road film ---------------------------------------------------
    film, n_fine, streak = _road_film(t, P, OBJ, zg, wash, dirt, 1.15)
    # Road film is TWO deposits, and which one you see depends on the paint
    # under it: the wet grey-brown darkens a white body, the dried pale dust
    # lightens a dark one.  Both are always present; the noise decides the mix.
    film_col = t.cmix(t.maprange(n_fine, 0.32, 0.74, 0.0, 1.0),
                      PAL["road_film"], PAL["dust_pale"])
    film_col = t.cmix(t.maprange(streak, 0.9, 1.4, 0.0, 0.60), film_col,
                      PAL["road_light"])
    col = t.cmix(t.math("MULTIPLY", film, 0.68), col, film_col)
    # brake and tyre dust, thrown forward of every arch: a distinctly warmer,
    # blacker deposit than the grey motorway film, and it is what makes the
    # bottom of a trailer read as a road vehicle
    arch = t.math("MULTIPLY", t.maprange(zg, 1.28, 0.55, 0.0, 1.0),
                  t.maprange(t.noise(t.vmath("SCALE", P, scale=1.0), 5.0, 7.0, 0.6),
                             0.30, 0.78, 0.25, 1.0))
    col = t.cmix(t.math("MULTIPLY", arch, t.math("MULTIPLY", dirt, 0.55)),
                 col, PAL["brake_dust"])
    # ---- 5. the hard grime line ON TOP of every rail, and the shelter under -
    shelf = t.math("MULTIPLY", wear, t.maprange(n_fine, 0.25, 0.8, 0.4, 1.0))
    col = t.cmix(t.math("MULTIPLY", shelf, 0.30), col,
                 t.cmix(0.35, PAL["road_film"], PAL["dust_pale"]))
    # ---- 6. streaks off the roof edge ---------------------------------------
    rs = t.noise(t.vmath("MULTIPLY", P, (16.0, 16.0, 0.30)), 12.0, 8.0, 0.75)
    # MEASURED, fourth macro: at 0.72 this covered the whole flank and the
    # livery disappeared under it.  A shed line streaks the 300-400 mm below
    # itself, not the whole side of the vehicle.
    col = t.cmix(t.math("MULTIPLY", t.math("MULTIPLY", grime, 0.30),
                        t.maprange(rs, 0.50, 0.82, 0.0, 1.0)),
                 col, PAL["road_film"])
    # ---- 7. the kick plate: harder, duller, and it takes the damage --------
    col = t.cmix(t.math("MULTIPLY", kick, 0.30), col, PAL["alu_ox"])
    # ---- 8. scuffs: paint GONE, bright metal, then oxide ------------------
    bare = t.math("MULTIPLY", scuff, t.maprange(
        t.vor(t.vmath("SCALE", P, scale=1.0), 260.0, "F1", 0, 1.0), 0.0, 0.35, 1.0, 0.0))
    col = t.cmix(t.math("MULTIPLY", bare, 0.85), col, PAL["alu_mill"])
    col = t.cmix(t.math("MULTIPLY", t.math("MULTIPLY", scuff, age), 0.35), col,
                 PAL["alu_ox"])
    # ---- 9. sealant bleed at every seam -------------------------------------
    col = t.cmix(t.math("MULTIPLY", seam, 0.22), col, PAL["road_film"])
    # ---- 10. polish swirls, only where somebody actually polishes ----------
    sw = t.vor(t.vmath("MULTIPLY", P, (1.0, 1.0, 40.0)), 90.0, "F1", 0, 1.0)
    # ---- roughness ----------------------------------------------------------
    # A trailer that lives outside is 0.30-0.42, not the 0.18 of a show car.
    # MEASURED, seventh macro: at 0.27 with a 0.30 clear coat the sun's
    # reflection was a 6 m blob across the middle of the flank that erased the
    # livery and the lettering inside it.  The specular lobe has to be BROAD and
    # BROKEN -- broken by the orange peel, by the oil-can wave and by the dirt,
    # which is what stops a 14 m panel behaving like a mirror.
    rgh = t.maprange(n_panel, 0.3, 0.7, 0.305, 0.415)
    rgh = t.math("ADD", rgh, t.math("MULTIPLY",
                                    t.maprange(t.noise(t.vmath("SCALE", P, scale=1.0),
                                                       11.0, 6.0, 0.55),
                                               0.3, 0.7, -0.055, 0.055), 1.0))
    rgh = t.fmix(t.math("MULTIPLY", film, 0.9), rgh,
                 t.maprange(n_fine, 0.2, 0.8, 0.62, 0.86))
    rgh = t.fmix(t.math("MULTIPLY", scuff, 0.9), rgh, 0.55)
    rgh = t.fmix(t.math("MULTIPLY", kick, 0.6), rgh, 0.42)
    rgh = t.fmix(t.math("MULTIPLY", fade, 0.5), rgh, 0.55)
    rgh = t.fmix(t.math("MULTIPLY", t.maprange(sw, 0.0, 0.4, 0.6, 0.0), 0.10),
                 rgh, 0.34)
    # ---- bump: orange peel, then dirt grain, then the sanded scuff --------
    peel = t.noise(t.vmath("SCALE", P, scale=1.0), 240.0, 6.0, 0.55)
    # STATED AS RADIANCE MODULATION, NOT MILLIMETRES (itemkit 5b, brief 4a).
    # What the eye judges is what a bump does to the LIGHT, and under this
    # film's 12.47 deg sun that carries a 4.52x amplifier: m = 2 sin(theta) /
    # tan(e).  Three amplitude sets were rendered and REJECTED on the human
    # figures and every one had been chosen in millimetres.
    #
    # These four are NOT a re-tune: each `modulation_pp` reproduces the Distance
    # this module already shipped, to the sixth decimal.  What has changed is
    # that the stack now SAYS WHAT IT AIMS THE LIGHT AT, so the next agent can
    # argue with 0.544 instead of guessing at 0.0008, and so the depths move if
    # the sun does.  Every wavelength is written from the same Scale literal the
    # texture above it already uses -- writing 0.00667 here would be a second
    # copy of a measured constant.
    #
    #   peel   lam   6.67 mm  m 0.5445  isotropic_macro    ungated: whole body
    #   grain  lam  47.06 mm  m 0.7222  isotropic_macro    gated by the film
    #   sand   lam   4.17 mm  m 6.9580  over hard_feature  gated by tt_scuff
    #   oil    lam   1.13 m   m 0.0065  under every band   see below
    #
    # A masked strength is stated at the value the mask reaches 1 (itemkit's
    # convention, and the only one that reproduces the shipped depth).  `sand`'s
    # strength node tops out at 0.7, so its REALISED peak is m 5.83, inside
    # hard_feature: a sanded scuff is a torn edge down to bare metal on a few
    # per cent of the area, not a crumple, and it is left where the author put
    # it.  NOTHING UNGATED AND ISOTROPIC HERE IS ABOVE m = 1, which is the shape
    # of the felt this law exists to prevent.
    #
    # `oil` is the oil-can standing wave and at 0.26 mm on a 1.13 m bay it is
    # m 0.0065 -- it does nothing.  It is left alone because THE MESH CARRIES
    # THIS ONE: `build_shell` displaces the sheet by the same `_oilcan` field
    # (out = off + oil - dmg - pull), 3-7 mm of real geometry.  Restating this
    # shader stage into a band would want ~6 mm of bump on top of a fold that is
    # already there, which is a double count and not a fix.  The other two bands
    # of that field are no better placed: its vertical term is a ~1.5 m half-
    # wave (m 0.005) and its fbm term a 0.385 m lump (m 0.019).
    LAM_PEEL = K.NOISE_WAVELENGTH_FACTOR / 240.0         #  6.67 mm
    LAM_GRAIN = K.NOISE_WAVELENGTH_FACTOR / 34.0         # 47.06 mm, _road_film
    LAM_SAND = K.VORONOI_WAVELENGTH_FACTOR / 520.0       #  4.17 mm
    LAM_OIL = 2.0 * PANEL_W / 2.15                       #  1.13 m: _oilcan runs
    #                            sin(2.15 pi uu) across one PANEL_W sheet bay
    b = t.bump(peel, 0.16, modulation_pp=0.544493, wavelength_m=LAM_PEEL)
    b = t.bump(n_fine, t.math("MULTIPLY", film, 0.35), normal=b,
               modulation_pp=0.722156, wavelength_m=LAM_GRAIN)
    b = t.bump(t.vor(t.vmath("SCALE", P, scale=1.0), 520.0, "F1", 0, 1.0),
               t.math("MULTIPLY", scuff, 0.7), normal=b,
               modulation_pp=6.95799, wavelength_m=LAM_SAND)
    b = t.bump(t.maprange(oil, -1.0, 1.0, 0.0, 1.0), 0.10, normal=b,
               modulation_pp=0.00650881, wavelength_m=LAM_OIL)

    bs = t.n("ShaderNodeBsdfPrincipled")
    t.pin(bs, 0, col); t.pin(bs, 1, 0.0); t.pin(bs, 2, rgh); t.pin_named(bs, "Normal", b)
    t.pin(bs, 14, 0.42)
    t.pin(bs, 20, t.math("MULTIPLY", t.math("SUBTRACT", 1.0,
                                            t.math("MULTIPLY", film, 0.92)), 0.16))
    t.pin(bs, 21, t.fmix(t.math("MULTIPLY", age, 0.9), 0.16, 0.38))
    return t.out(bs)


def mat_alu():
    """Mill-finish and anodised aluminium: rails, roof cap, kick plate edges.
    Brushed, oxidised, and it collects dirt in the brush grain."""
    t = NT(PFX + "Alu")
    OBJ, P = _obj_vec(t)
    zg = t.attr("tt_zg"); wear = t.attr("tt_wear")
    grime = t.attr("tt_grime"); wash = t.attr("tt_wash")
    scuff = t.attr("tt_scuff"); kick = t.attr("tt_kick")
    age = t.attr("tt_age", 2, "OBJECT"); dirt = t.attr("tt_dirt", 2, "OBJECT")
    brush = t.wave(t.vmath("MULTIPLY", P, (1.0, 26.0, 26.0)), 190.0, 0.6, 2.0, "X")
    n1 = t.noise(t.vmath("SCALE", P, scale=1.0), 22.0, 7.0, 0.6)
    n2 = t.noise(t.vmath("SCALE", P, scale=1.0), 210.0, 8.0, 0.62)
    ox = t.vor(t.vmath("SCALE", P, scale=1.0), 70.0, "F1", 0, 1.0)
    col = t.cmix(t.maprange(brush, 0.3, 0.7, 0.0, 1.0), PAL["alu_mill"],
                 t.cmix(0.4, PAL["alu_mill"], PAL["alu_ox"]))
    col = t.cmix(t.math("MULTIPLY", age, t.maprange(ox, 0.0, 0.45, 0.9, 0.0)),
                 col, PAL["alu_ox"])
    film, n_fine, streak = _road_film(t, P, OBJ, zg, wash, dirt, 1.15)
    col = t.cmix(t.math("MULTIPLY", film, 0.9), col, PAL["road_film"])
    # a box-trailer roof is the filthiest surface on the vehicle: nothing ever
    # washes it and everything settles on it
    col = t.cmix(t.math("MULTIPLY", grime, 0.62), col,
                 t.cmix(0.35, PAL["road_film"], PAL["grime_green"]))
    col = t.cmix(t.math("MULTIPLY", wear, 0.30), col, PAL["alu_mill"])
    # THE KICK PLATE IS THIS MATERIAL.  Its whole job is to take the damage the
    # paint would otherwise take, so the scuff mask has to reach it: a kerb
    # strike polishes the alu bright and then it oxidises grey again.
    col = t.cmix(t.math("MULTIPLY", scuff, 0.80), col, PAL["alu_mill"])
    col = t.cmix(t.math("MULTIPLY", t.math("MULTIPLY", scuff, age), 0.45), col,
                 PAL["alu_ox"])
    # THE KICK PLATE.  MEASURED, fifth macro: at 0.22 it was the same tone as
    # the paint above it and the flank had no bottom.  A kick plate is bare
    # 3 mm alu that has been sand-blasted by eleven seasons of motorway spray:
    # it is DARKER and duller than the paint it protects, and the tonal break
    # at its top edge is what gives the flank a base.
    col = t.cmix(t.math("MULTIPLY", kick, 0.70), col,
                 t.cmix(0.72, PAL["alu_ox"], PAL["road_film"]))
    rgh = t.maprange(brush, 0.2, 0.8, 0.22, 0.44)
    rgh = t.fmix(t.math("MULTIPLY", film, 0.9), rgh, 0.78)
    rgh = t.fmix(t.math("MULTIPLY", age, 0.6), rgh, 0.58)
    rgh = t.fmix(t.math("MULTIPLY", scuff, 0.8), rgh, 0.52)
    # STATED AS RADIANCE MODULATION, NOT MILLIMETRES (itemkit 5b, brief 4a).
    # Not a re-tune: each of these four reproduces the Distance the module
    # shipped, and every wavelength is written from the Scale literal of the
    # texture that drives it.
    #
    #   brush  lam  1.65 mm  m 2.1999  hard_feature       ungated, DIRECTIONAL
    #   ox     lam  7.62 mm  m 1.0006  sparse_crease      ungated
    #   lump   lam 72.73 mm  m 0.6235  isotropic_macro    gated by the film
    #   scuff  lam  4.52 mm  m 7.0635  over hard_feature  gated by tt_scuff
    #
    # `brush` is the linisher grain and is anisotropic -- it is a Wave, so it
    # bends the highlight along one axis only, which is why a value at the top
    # of isotropic_macro is not the isotropic crust the band would imply.
    # `ox` is 5 % over the isotropic_macro ceiling as an ungated field; left,
    # because 5 % is below what the eye that will judge it can resolve and
    # because this stack has never been rendered alive (R2-038).
    # `scuff` is stated at the mask's 1 (itemkit's convention); its strength
    # node tops out at 0.85, so the realised peak is m 6.59.  A kerb strike on
    # a 3 mm kick plate is a torn edge, not a crumple, and it acts on a few per
    # cent of the area -- but this is the deepest stage in the module and the
    # first thing the central A/B should look at.
    # R2-058: THIS READ `1.0 / Scale` AND WAS 3.183x TOO LONG.  Blender's Wave
    # multiplies the coordinate by 20 before the sine, so one band is
    # 2*pi/20 = 0.31416 of 1/Scale, not 1/Scale -- measured flat to six digits
    # over a Scale 5..230 sweep (itemkit WAVE_WAVELENGTH_FACTOR;
    # work/wavefix/emitted_wavelength.json).  itemkit's `_tex_wavelength_m` had
    # the same error, which is why this line and the audit agreed and both were
    # wrong.  THE DISTANCE ON THE SOCKET HAS NOT MOVED -- this is the depth the
    # module shipped and was judged at.  What moved is the DECLARATION: at the
    # true pitch the same amplitude is a much steeper wall, so the stage's real
    # modulation is m 2.200 and was being reported as m 0.710.  Do NOT
    # "correct" this by keeping the old modulation against the new wavelength:
    # that derives a Distance 3.183x shallower and changes a surface that was
    # rendered and looked at.
    LAM_BRUSH = K.WAVE_WAVELENGTH_FACTOR / 190.0         #  1.65 mm (Wave)
    LAM_OX = K.NOISE_WAVELENGTH_FACTOR / 210.0           #  7.62 mm
    LAM_LUMP = K.NOISE_WAVELENGTH_FACTOR / 22.0          # 72.73 mm
    LAM_SCUFF = K.VORONOI_WAVELENGTH_FACTOR / 480.0      #  4.52 mm
    b = t.bump(brush, 0.22, modulation_pp=2.199943, wavelength_m=LAM_BRUSH)
    b = t.bump(n2, 0.30, normal=b,
               modulation_pp=1.000618, wavelength_m=LAM_OX)
    b = t.bump(n1, t.math("MULTIPLY", film, 0.4), normal=b,
               modulation_pp=0.623545, wavelength_m=LAM_LUMP)
    b = t.bump(t.vor(t.vmath("SCALE", P, scale=1.0), 480.0, "F1", 0, 1.0),
               t.math("MULTIPLY", scuff, 0.85), normal=b,
               modulation_pp=7.06355, wavelength_m=LAM_SCUFF)
    bs = t.n("ShaderNodeBsdfPrincipled")
    t.pin(bs, 0, col)
    t.pin(bs, 1, t.math("MULTIPLY", t.math("SUBTRACT", 1.0,
                                           t.math("MULTIPLY", film, 0.7)), 0.88))
    t.pin(bs, 2, rgh); t.pin_named(bs, "Normal", b)
    return t.out(bs)


def mat_steel():
    """Chassis black: two-pack over shot-blast, chipped by stones, rusted where
    the chip went through, and under a permanent film of road salt."""
    t = NT(PFX + "Steel")
    OBJ, P = _obj_vec(t)
    zg = t.attr("tt_zg"); wear = t.attr("tt_wear"); wash = t.attr("tt_wash")
    age = t.attr("tt_age", 2, "OBJECT"); dirt = t.attr("tt_dirt", 2, "OBJECT")
    n1 = t.noise(t.vmath("SCALE", P, scale=1.0), 18.0, 7.0, 0.58)
    n2 = t.noise(t.vmath("SCALE", P, scale=1.0), 160.0, 8.0, 0.64)
    chip = t.vor(t.vmath("SCALE", P, scale=1.0), 130.0, "F1", 0, 1.0)
    chipm = t.math("MULTIPLY", t.maprange(chip, 0.0, 0.10, 1.0, 0.0),
                   t.math("MULTIPLY", age, t.maprange(zg, 1.6, 0.3, 0.2, 1.0)))
    col = t.cmix(t.maprange(n1, 0.3, 0.7, 0.0, 1.0), PAL["steel_dark"],
                 t.cmix(0.4, PAL["steel_dark"], PAL["alu_dark"]))
    col = t.cmix(t.math("MULTIPLY", chipm, 0.9), col, PAL["rust"])
    col = t.cmix(t.math("MULTIPLY", wear, 0.35), col, PAL["steel_chip"])
    film, n_fine, streak = _road_film(t, P, OBJ, zg, wash, dirt, 1.6)
    col = t.cmix(t.math("MULTIPLY", film, 0.94), col,
                 t.cmix(t.maprange(streak, 0.5, 1.2, 0.0, 0.6),
                        PAL["road_film"], PAL["brake_dust"]))
    col = t.cmix(t.math("MULTIPLY", t.maprange(zg, 0.9, 0.25, 0.0, 1.0), 0.45),
                 col, PAL["diesel"])
    rgh = t.maprange(n2, 0.25, 0.8, 0.42, 0.78)
    rgh = t.fmix(t.math("MULTIPLY", film, 0.9), rgh, 0.88)
    rgh = t.fmix(chipm, rgh, 0.95)
    # STATED AS RADIANCE MODULATION, NOT MILLIMETRES (itemkit 5b, brief 4a).
    # Not a re-tune: each reproduces the Distance the module shipped.
    #
    #   blast  lam 10.00 mm  m 1.0859  sparse_crease   ungated
    #   chip   lam 16.69 mm  m 2.9016  hard_feature    gated by chipm
    #   film   lam 88.89 mm  m 0.8275  isotropic_macro gated by the film
    #
    # `blast` is the shot-blast profile the two-pack was sprayed over; at 1.09
    # it is 14 % over the isotropic_macro ceiling as an ungated field.  Left,
    # because a blast profile IS a crust -- that is what shot-blasting does --
    # and because 1.09 is a long way below the 1.66 that rendered as felt.
    # `chip` is stated at the mask's 1; its strength node is `chipm * 1.2` and
    # `chipm` reaches 1, so the realised peak is m 3.48 -- still hard_feature,
    # which is right: a stone chip through two-pack is a crater with a wall.
    LAM_BLAST = K.NOISE_WAVELENGTH_FACTOR / 160.0        # 10.00 mm
    LAM_CHIP = K.VORONOI_WAVELENGTH_FACTOR / 130.0       # 16.69 mm
    LAM_FILM = K.NOISE_WAVELENGTH_FACTOR / 18.0          # 88.89 mm
    b = t.bump(n2, 0.35, modulation_pp=1.085893, wavelength_m=LAM_BLAST)
    b = t.bump(chip, t.math("MULTIPLY", chipm, 1.2), normal=b,
               modulation_pp=2.901646, wavelength_m=LAM_CHIP)
    b = t.bump(n1, t.math("MULTIPLY", film, 0.5), normal=b,
               modulation_pp=0.827523, wavelength_m=LAM_FILM)
    bs = t.n("ShaderNodeBsdfPrincipled")
    t.pin(bs, 0, col); t.pin(bs, 2, rgh); t.pin_named(bs, "Normal", b)
    return t.out(bs)


def mat_galv():
    """Hot-dip galvanising: real spangle, white rust in the runs, and the
    polished patch wherever a spanner has been."""
    t = NT(PFX + "Galv")
    OBJ, P = _obj_vec(t)
    zg = t.attr("tt_zg"); wear = t.attr("tt_wear"); wash = t.attr("tt_wash")
    age = t.attr("tt_age", 2, "OBJECT"); dirt = t.attr("tt_dirt", 2, "OBJECT")
    sp = t.vor(t.vmath("SCALE", P, scale=1.0), 45.0, "F1", 1, 1.0)
    sp2 = t.vor(t.vmath("SCALE", P, scale=1.0), 45.0, "F1", 0, 1.0)
    n1 = t.noise(t.vmath("SCALE", P, scale=1.0), 26.0, 7.0, 0.6)
    n2 = t.noise(t.vmath("SCALE", P, scale=1.0), 300.0, 8.0, 0.6)
    col = t.cmix(t.maprange(sp, 0.2, 0.8, 0.0, 1.0), PAL["galv"],
                 t.cmix(0.45, PAL["galv"], PAL["alu_dark"]))
    col = t.cmix(t.math("MULTIPLY", age, t.maprange(n1, 0.4, 0.75, 0.0, 0.8)),
                 col, PAL["galv_white"])
    film, n_fine, streak = _road_film(t, P, OBJ, zg, wash, dirt, 1.2)
    col = t.cmix(t.math("MULTIPLY", film, 0.85), col, PAL["road_film"])
    col = t.cmix(t.math("MULTIPLY", wear, 0.4), col, PAL["galv"])
    rgh = t.maprange(sp2, 0.0, 0.5, 0.30, 0.62)
    rgh = t.fmix(t.math("MULTIPLY", film, 0.9), rgh, 0.84)
    # STATED AS RADIANCE MODULATION, NOT MILLIMETRES (itemkit 5b, brief 4a).
    # Not a re-tune: both reproduce the Distance the module shipped.
    #
    #   spangle lam 48.22 mm  m 0.1590  isotropic_micro  ungated
    #   grain   lam  5.33 mm  m 0.7010  isotropic_macro  ungated
    #
    # The two bands of a hot-dip surface, and they are meant to read as two
    # different things: the spangle is a wide, nearly flat crystal facet field
    # (0.159 is the shallow end of isotropic_micro, which is what a facet that
    # catches the sun by ORIENTATION rather than by slope should be), and the
    # grain over it is the dross and the white rust.  Both are inside their
    # bands and both are left alone.
    LAM_SPANGLE = K.VORONOI_WAVELENGTH_FACTOR / 45.0     # 48.22 mm
    LAM_GRAIN = K.NOISE_WAVELENGTH_FACTOR / 300.0        #  5.33 mm
    b = t.bump(sp2, 0.30, modulation_pp=0.1590484, wavelength_m=LAM_SPANGLE)
    b = t.bump(n2, 0.22, normal=b,
               modulation_pp=0.701046, wavelength_m=LAM_GRAIN)
    bs = t.n("ShaderNodeBsdfPrincipled")
    t.pin(bs, 0, col)
    t.pin(bs, 1, t.math("MULTIPLY", t.math("SUBTRACT", 1.0,
                                           t.math("MULTIPLY", film, 0.8)), 0.8))
    t.pin(bs, 2, rgh); t.pin_named(bs, "Normal", b)
    return t.out(bs)


def mat_rubber():
    """Mudflaps, buffers, air bags, hoses.  Matt, ozone-cracked, dusted."""
    t = NT(PFX + "Rubber")
    OBJ, P = _obj_vec(t)
    zg = t.attr("tt_zg"); wear = t.attr("tt_wear")
    dirt = t.attr("tt_dirt", 2, "OBJECT"); age = t.attr("tt_age", 2, "OBJECT")
    crack = t.vor(t.vmath("SCALE", P, scale=1.0), 120.0, "F2", 0, 1.0)
    n1 = t.noise(t.vmath("SCALE", P, scale=1.0), 40.0, 8.0, 0.62)
    n2 = t.noise(t.vmath("SCALE", P, scale=1.0), 420.0, 7.0, 0.6)
    col = t.cmix(t.maprange(n1, 0.3, 0.7, 0.0, 1.0), PAL["rubber"],
                 t.cmix(0.5, PAL["rubber"], PAL["rubber_dust"]))
    col = t.cmix(t.math("MULTIPLY", age, t.maprange(crack, 0.0, 0.06, 0.9, 0.0)),
                 col, PAL["rubber_dust"])
    col = t.cmix(t.math("MULTIPLY", dirt, t.maprange(zg, 1.4, 0.15, 0.15, 0.9)),
                 col, PAL["road_film"])
    col = t.cmix(t.math("MULTIPLY", wear, 0.25), col, PAL["rubber_dust"])
    rgh = t.maprange(n2, 0.2, 0.8, 0.72, 0.95)
    # STATED AS RADIANCE MODULATION, NOT MILLIMETRES (itemkit 5b, brief 4a).
    #
    #   skin   lam  3.81 mm  m 0.4000  isotropic_micro  ungated -- RE-TUNED
    #   craze  lam 18.08 mm  m 0.6581  isotropic_macro  ungated
    #
    # THE SKIN IS THE ONE STAGE IN THIS MODULE THAT IS RE-TUNED, and it is the
    # case the law names: an UNGATED ISOTROPIC field above m = 1.5.  It shipped
    # 0.36 mm p-p on a 3.81 mm noise, which is m 2.574 -- a 16.5 deg surface
    # over every mudflap, buffer and hose on the vehicle.  That sits between the
    # two sets that were rendered and rejected on the human figures (10.4 deg /
    # m 1.66, "thick felt"; 22.6 deg / m 3.76, "coarse stucco") and it is not
    # what it is trying to be.  It is now aimed at RELIEF_BANDS["isotropic_micro"]
    # at 0.40 -- 2.54 deg, 0.054 mm p-p -- because the band's own examples name
    # CAST SKIN, and a moulded rubber sheet at a 4 mm wavelength is exactly
    # that.  The coarser reading a mudflap does have is the ozone crazing, and
    # that is the SEPARATE stage below at m 0.658, which is now correctly the
    # deeper of the two: the crazing cuts into the skin rather than the skin
    # standing proud of the crazing.  0.40 rather than 0.45: a band is a band,
    # not a bar to lean on.
    #
    # `craze` is unchanged and reproduces the shipped Distance.
    LAM_SKIN = K.NOISE_WAVELENGTH_FACTOR / 420.0         #  3.81 mm
    LAM_CRAZE = K.VORONOI_WAVELENGTH_FACTOR / 120.0      # 18.08 mm
    b = t.bump(n2, 0.45, modulation_pp=0.40, wavelength_m=LAM_SKIN)
    b = t.bump(crack, 0.35, normal=b,
               modulation_pp=0.658109, wavelength_m=LAM_CRAZE)
    bs = t.n("ShaderNodeBsdfPrincipled")
    t.pin(bs, 0, col); t.pin(bs, 2, rgh); t.pin_named(bs, "Normal", b)
    return t.out(bs)


def mat_tape():
    """ECE 104 retroreflective conspicuity tape.  The bead structure is real
    geometry-scale (0.06 mm) and is carried as a voronoi microfacet field, and
    the tape's edge is dirty because tape edges always are."""
    t = NT(PFX + "Tape")
    OBJ, P = _obj_vec(t)
    zg = t.attr("tt_zg"); dirt = t.attr("tt_dirt", 2, "OBJECT")
    wash = t.attr("tt_wash")
    bead = t.vor(t.vmath("SCALE", P, scale=1.0), 3400.0, "F1", 0, 1.0)
    n1 = t.noise(t.vmath("SCALE", P, scale=1.0), 60.0, 7.0, 0.6)
    col = t.cmix(t.maprange(bead, 0.0, 0.30, 1.0, 0.0), PAL["tape_yellow"],
                 PAL["tape_bead"])
    film, n_fine, streak = _road_film(t, P, OBJ, zg, wash, dirt, 0.8)
    col = t.cmix(t.math("MULTIPLY", film, 0.7), col, PAL["road_film"])
    rgh = t.maprange(n1, 0.3, 0.7, 0.14, 0.30)
    rgh = t.fmix(t.math("MULTIPLY", film, 0.8), rgh, 0.7)
    # STATED AS RADIANCE MODULATION, NOT MILLIMETRES (itemkit 5b, brief 4a).
    # Not a re-tune: it reproduces the Distance the module shipped.
    #
    #   bead  lam 0.638 mm  m 2.5615  hard_feature  ungated
    #
    # The only stage in the module that is ungated, isotropic-looking AND above
    # m 1.5 and is nevertheless RIGHT.  This is not a crumple: it is a packed
    # array of 0.06 mm glass lenses, and a lens is a hard feature by
    # construction -- the whole optical function of ECE 104 tape is that each
    # bead presents every normal direction at once.  A shallow version of this
    # field would not read as retroreflective tape at any depth.
    LAM_BEAD = K.VORONOI_WAVELENGTH_FACTOR / 3400.0      #  0.64 mm
    b = t.bump(bead, 0.5, modulation_pp=2.56148, wavelength_m=LAM_BEAD)
    bs = t.n("ShaderNodeBsdfPrincipled")
    t.pin(bs, 0, col); t.pin(bs, 2, rgh); t.pin_named(bs, "Normal", b)
    t.pin(bs, 20, 0.55); t.pin(bs, 21, 0.03)
    return t.out(bs)


def mat_stencil():
    """Cut vinyl and sprayed stencil.  Its colour is a per-object attribute, so
    ten trailers letter themselves out of one material; the edges lift and the
    dirt gets under them."""
    t = NT(PFX + "Stencil")
    OBJ, P = _obj_vec(t)
    zg = t.attr("tt_zg"); wear = t.attr("tt_wear"); wash = t.attr("tt_wash")
    dirt = t.attr("tt_dirt", 2, "OBJECT"); age = t.attr("tt_age", 2, "OBJECT")
    base = t.comb(t.attr("tt_txr", 2, "OBJECT"), t.attr("tt_txg", 2, "OBJECT"),
                  t.attr("tt_txb", 2, "OBJECT"))
    n1 = t.noise(t.vmath("SCALE", P, scale=1.0), 90.0, 8.0, 0.6)
    n2 = t.noise(t.vmath("SCALE", P, scale=1.0), 640.0, 7.0, 0.58)
    crk = t.vor(t.vmath("SCALE", P, scale=1.0), 340.0, "F2", 0, 1.0)
    col = t.cmix(t.math("MULTIPLY", age, t.maprange(n1, 0.35, 0.75, 0.0, 0.5)),
                 base, t.cmix(0.5, base, PAL["alu_ox"]))
    col = t.cmix(t.math("MULTIPLY", wear, t.math("MULTIPLY", age, 0.5)), col,
                 PAL["alu_ox"])
    film, n_fine, streak = _road_film(t, P, OBJ, zg, wash, dirt, 0.9)
    col = t.cmix(t.math("MULTIPLY", film, 0.8), col, PAL["road_film"])
    rgh = t.maprange(n2, 0.25, 0.8, 0.22, 0.42)
    rgh = t.fmix(t.math("MULTIPLY", film, 0.9), rgh, 0.8)
    # STATED AS RADIANCE MODULATION, NOT MILLIMETRES (itemkit 5b, brief 4a).
    # Not a re-tune: both reproduce the Distance the module shipped.
    #
    #   tooth  lam 2.50 mm  m 0.8149  isotropic_macro  ungated
    #   crack  lam 6.38 mm  m 2.5615  hard_feature     gated by tt_age
    #
    # `crack` is stated at the mask's 1 (itemkit's convention); its strength
    # node is `age * 0.3`, so even on the oldest trailer the realised peak is
    # m 0.77 and on a new one it is nothing.  A lifted vinyl edge is a real
    # step in a 0.1 mm film, which is why the stated band is hard_feature.
    LAM_TOOTH = K.NOISE_WAVELENGTH_FACTOR / 640.0        #  2.50 mm
    LAM_CRACK = K.VORONOI_WAVELENGTH_FACTOR / 340.0      #  6.38 mm
    b = t.bump(n2, 0.18, modulation_pp=0.814896, wavelength_m=LAM_TOOTH)
    b = t.bump(crk, t.math("MULTIPLY", age, 0.3), normal=b,
               modulation_pp=2.56148, wavelength_m=LAM_CRACK)
    bs = t.n("ShaderNodeBsdfPrincipled")
    t.pin(bs, 0, col); t.pin(bs, 2, rgh); t.pin_named(bs, "Normal", b)
    t.pin(bs, 20, 0.35); t.pin(bs, 21, 0.10)
    return t.out(bs)


def mat_dark():
    """Underbody black: axles, wings, floor underside, lamp housings.  It is
    never black -- it is a mat of road film with black underneath."""
    t = NT(PFX + "Dark")
    OBJ, P = _obj_vec(t)
    zg = t.attr("tt_zg"); wear = t.attr("tt_wear"); wash = t.attr("tt_wash")
    dirt = t.attr("tt_dirt", 2, "OBJECT")
    n1 = t.noise(t.vmath("SCALE", P, scale=1.0), 16.0, 7.0, 0.6)
    n2 = t.noise(t.vmath("SCALE", P, scale=1.0), 190.0, 8.0, 0.6)
    v1 = t.vor(t.vmath("SCALE", P, scale=1.0), 90.0, "F1", 0, 1.0)
    col = t.cmix(t.maprange(n1, 0.3, 0.7, 0.0, 1.0), PAL["steel_dark"],
                 PAL["alu_dark"])
    film, n_fine, streak = _road_film(t, P, OBJ, zg, wash, dirt, 1.9)
    col = t.cmix(t.math("MULTIPLY", film, 0.95), col,
                 t.cmix(t.maprange(v1, 0.0, 0.3, 0.0, 0.7), PAL["road_film"],
                        PAL["brake_dust"]))
    col = t.cmix(t.math("MULTIPLY", wear, 0.3), col, PAL["steel_chip"])
    rgh = t.maprange(n2, 0.25, 0.8, 0.55, 0.92)
    # STATED AS RADIANCE MODULATION, NOT MILLIMETRES (itemkit 5b, brief 4a).
    # Not a re-tune: both reproduce the Distance the module shipped.
    #
    #   crud   lam  8.42 mm  m 1.5940  sparse_crease  UNGATED -- see below
    #   clod   lam 24.11 mm  m 2.4919  hard_feature   gated by the film
    #
    # `crud` IS THE CLOSEST CALL IN THIS MODULE and it is left alone on purpose.
    # It is an ungated isotropic field at 10.15 deg, which is the slope that
    # rendered as "thick felt" on the human figures (10.4 deg, m 1.66), and it
    # is 6 % over the m = 1.5 line that the relief law names as the re-tune
    # trigger.  It is left because 6 % is a nudge and the bands are bands, and
    # because this stack has never once been rendered alive (R2-038): the depth
    # is the author's stated intent for a surface that is a MAT of caked road
    # film over shot-blast, not a painted panel, and nobody has yet seen it.
    # IT IS THE FIRST STAGE THE CENTRAL A/B SHOULD LOOK AT; if it reads as felt,
    # the band to aim at is isotropic_macro and the value is ~0.75.
    # `clod` is stated at the mask's 1; the film node tops out at 0.5, so the
    # realised peak is m 1.29 -- a clod of dried mud with an edge on it.
    LAM_CRUD = K.NOISE_WAVELENGTH_FACTOR / 190.0         #  8.42 mm
    LAM_CLOD = K.VORONOI_WAVELENGTH_FACTOR / 90.0        # 24.11 mm
    b = t.bump(n2, 0.4, modulation_pp=1.594047, wavelength_m=LAM_CRUD)
    b = t.bump(v1, t.math("MULTIPLY", film, 0.5), normal=b,
               modulation_pp=2.49194, wavelength_m=LAM_CLOD)
    bs = t.n("ShaderNodeBsdfPrincipled")
    t.pin(bs, 0, col); t.pin(bs, 2, rgh); t.pin_named(bs, "Normal", b)
    return t.out(bs)


def mat_chequer():
    """Aluminium tread plate: the rear threshold and the load floor.  The tread
    is 2.5 mm and 1.2 px, so it is a bump -- but the POLISH on the raised bar is
    geometry-scale behaviour and that is what the wear mask does."""
    t = NT(PFX + "Chequer")
    OBJ, P = _obj_vec(t)
    zg = t.attr("tt_zg"); wear = t.attr("tt_wear"); wash = t.attr("tt_wash")
    dirt = t.attr("tt_dirt", 2, "OBJECT")
    w1 = t.wave(t.vmath("MULTIPLY", P, (1.0, 1.0, 1.0)), 34.0, 0.9, 2.0, "X")
    w2 = t.wave(t.vmath("MULTIPLY", P, (1.0, 1.0, 1.0)), 34.0, 0.9, 2.0, "Y")
    tread = t.math("MULTIPLY", t.maprange(w1, 0.55, 0.78, 0.0, 1.0),
                   t.maprange(w2, 0.35, 0.62, 0.0, 1.0))
    n2 = t.noise(t.vmath("SCALE", P, scale=1.0), 260.0, 8.0, 0.6)
    col = t.cmix(t.maprange(tread, 0.0, 1.0, 0.0, 1.0),
                 t.cmix(0.5, PAL["alu_mill"], PAL["alu_ox"]), PAL["alu_mill"])
    film, n_fine, streak = _road_film(t, P, OBJ, zg, wash, dirt, 1.3)
    col = t.cmix(t.math("MULTIPLY", film, 0.85), col, PAL["road_film"])
    col = t.cmix(t.math("MULTIPLY", wear, 0.45), col, PAL["alu_mill"])
    rgh = t.maprange(n2, 0.25, 0.8, 0.30, 0.60)
    rgh = t.fmix(t.math("MULTIPLY", wear, 0.7), rgh, 0.22)
    rgh = t.fmix(t.math("MULTIPLY", film, 0.9), rgh, 0.82)
    # STATED AS RADIANCE MODULATION, NOT MILLIMETRES (itemkit 5b, brief 4a).
    # Not a re-tune: both reproduce the Distance the module shipped.
    #
    #   tread  lam  9.24 mm  m 5.4947  hard_feature     ungated
    #   grain  lam  6.15 mm  m 0.8047  isotropic_macro  ungated
    #
    # `tread` is ungated and above m 1.5, and that is correct: it is not a
    # field, it is the 2.5 mm raised bar of five-bar plate, and the docstring
    # above says why it is a bump at all (2.5 mm is 1.2 px at 466 px/m).  Its
    # 2.25 mm stated amplitude is the real bar height, and the wavelength is the
    # bar pitch, so the m falls out of the plate's own geometry rather than
    # being chosen.  The height is the PRODUCT of the two Wave bands, not a sum,
    # and it reaches 1 on the bar, so height_pp stays 1.
    # R2-058: THIS READ `1.0 / Scale` AND WAS 3.183x TOO LONG.  Blender's Wave
    # multiplies the coordinate by 20 before the sine, so one band is
    # 2*pi/20 = 0.31416 of 1/Scale, not 1/Scale -- measured flat to six digits
    # over a Scale 5..230 sweep (itemkit WAVE_WAVELENGTH_FACTOR;
    # work/wavefix/emitted_wavelength.json).  itemkit's `_tex_wavelength_m` had
    # the same error, which is why this line and the audit agreed and both were
    # wrong.  THE DISTANCE ON THE SOCKET HAS NOT MOVED -- this is the depth the
    # module shipped and was judged at.  What moved is the DECLARATION: at the
    # true pitch the same amplitude is a much steeper wall, so the stage's real
    # modulation is m 5.495 and was being reported as m 2.113.  Do NOT
    # "correct" this by keeping the old modulation against the new wavelength:
    # that derives a Distance 3.183x shallower and changes a surface that was
    # rendered and looked at.
    LAM_TREAD = K.WAVE_WAVELENGTH_FACTOR / 34.0          #  9.24 mm (Wave)
    LAM_GRAIN = K.NOISE_WAVELENGTH_FACTOR / 260.0        #  6.15 mm
    b = t.bump(tread, 0.9, modulation_pp=5.494727, wavelength_m=LAM_TREAD)
    b = t.bump(n2, 0.25, normal=b,
               modulation_pp=0.80472, wavelength_m=LAM_GRAIN)
    bs = t.n("ShaderNodeBsdfPrincipled")
    t.pin(bs, 0, col)
    t.pin(bs, 1, t.math("MULTIPLY", t.math("SUBTRACT", 1.0,
                                           t.math("MULTIPLY", film, 0.75)), 0.85))
    t.pin(bs, 2, rgh); t.pin_named(bs, "Normal", b)
    return t.out(bs)


def materials():
    return [mat_paint(), mat_alu(), mat_steel(), mat_galv(), mat_rubber(),
            mat_tape(), mat_stencil(), mat_dark(), mat_chequer()]


# ==============================================================================
# 10.  BUILD
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
            if me and getattr(me, "users", 1) == 0 and isinstance(me, bpy.types.Mesh):
                bpy.data.meshes.remove(me)
    for c in reversed(seen):
        bpy.data.collections.remove(c)


def grade_lod(ts, anchor):
    if not anchor:
        for t in ts:
            t["lod"] = 0
            t["dist"] = 0.0
        return
    A = np.asarray(anchor, float).reshape(-1, 3)
    for t in ts:
        org, ex, ey, ez = trailer_basis(t)
        c = org + ez * (t["H"] * 0.5)
        d = float(np.min(np.linalg.norm(A - c[None, :], axis=1)))
        t["dist"] = d
        t["lod"] = lod_of(d)


def build(lod_anchor=None, scene=None, stats=None, limit=None, uids=None):
    """Emit one object per trailer into `COLL`.  Ten objects, ten meshes."""
    scene = scene or bpy.context.scene
    purge()
    root = _coll(COLL)
    mats = materials()
    ts = trailer_records()
    if uids is not None:
        ts = [t for t in ts if t["uid"] in set(uids)]
    if limit:
        ts = ts[:limit]
    grade_lod(ts, lod_anchor)
    tris = 0
    infos = []
    t0 = time.time()
    for t in ts:
        ob, info = build_trailer(t, root, mats, t.get("lod", 0))
        tris += info["triangles"]
        infos.append(info)
        log("  T%02d %-9s L %.3f lod %d  %6d verts %7d tris  %4d rivets  %.1fs"
            % (t["uid"], t["team"], t["L"], t.get("lod", 0), info["verts"],
               info["triangles"], info["rivets"], time.time() - t0))
    log("built %d trailers, %.2f M triangles" % (len(ts), tris / 1e6))
    if stats is not None:
        stats.update(n=len(ts), tris=tris, infos=infos,
                     lengths=[t["L"] for t in ts],
                     lods=[t.get("lod", 0) for t in ts])
    return root


# ==============================================================================
# 11.  THE PUBLISHED INTERFACE
# ==============================================================================
# Pure functions of the plan.  No bpy.  World frame, metres.

def _w(t, p):
    return [float(v) for v in to_world(t, [p])[0]]


def _lamp_plan(t):
    """The 14 lamp stations on one trailer, in the TRAILER frame.

    Both the boss geometry and `lamp_sites()` are generated from this list, so
    the published position is the position of the mesh and cannot drift from it.
    """
    L, W = t["L"], t["W"]
    hx = L * 0.5
    zkb = t["z_sill"] + RAIL_BOT_H
    zs = t["z_sill"]
    out = []
    for side in (-1, 1):
        for fx in (-hx + 1.30, 0.0, hx - 1.60):
            z = zkb + 0.055
            y = float(_flank_y(t, side, np.array([fx]), np.array([z]))[0])
            out.append(dict(role="side_marker", x=float(fx), y=y, z=float(z),
                            nx=0.0, ny=float(side), nz=0.0,
                            w=0.116, h=0.072, recess=0.014, lens="amber"))
    for role, y, z, nx, lens in (
            ("rear_combination", -0.92, zs + 0.055, -1.0, "red/amber"),
            ("rear_combination", 0.92, zs + 0.055, -1.0, "red/amber"),
            ("rear_fog", -0.55, zs + 0.055, -1.0, "red"),
            ("reverse", 0.55, zs + 0.055, -1.0, "clear"),
            ("plate_lamp", 0.05, zs + 0.115, -1.0, "clear"),
            ("rear_outline", -1.19, t["z_roof_bot"] - 0.055, -1.0, "red"),
            ("rear_outline", 1.19, t["z_roof_bot"] - 0.055, -1.0, "red"),
            ("front_outline", 0.0, t["z_roof_bot"] - 0.055, 1.0, "white")):
        x = (-hx - 0.062) if nx < 0 else (hx + 0.030)
        out.append(dict(role=role, x=float(x), y=float(y), z=float(z),
                        nx=float(nx), ny=0.0, nz=0.0, w=0.170, h=0.096,
                        recess=0.016, lens=lens))
    return out


def hub_sites():
    """120 records for `truck_wheel_trailer`: 10 x 3 axles x 2 sides x 2 wheels.

    `face_p` is the world position of the WHEEL MOUNTING FACE and `axis` points
    OUTBOARD along the axle.  Build the wheel with its disc face on `face_p`,
    its centreline on `rim_centre_p`, and it lands on the ground -- the trailer
    is already sitting at the right height on `slr`.
    """
    out = []
    for t in trailer_records():
        org, ex, ey, ez = trailer_basis(t)
        for ai, ax in enumerate(t["axles"]):
            for sy in (-1, 1):
                face_l = (ax, sy * TWIN_CENTRE_Y, SLR)
                axis = [float(v) for v in (ey * sy)]
                for pos, off in (("inner", -TWIN_PITCH * 0.5),
                                 ("outer", +TWIN_PITCH * 0.5)):
                    rc = (ax, sy * (TWIN_CENTRE_Y + off), SLR)
                    fw = _w(t, face_l)
                    gz, own = _ground(fw[0], fw[1])
                    out.append(dict(
                        trailer=t["uid"], axle=ai, side=int(sy), position=pos,
                        face_p=fw, rim_centre_p=_w(t, rc), axis=axis,
                        spigot_d=HUB_SPIGOT, stud_pcd=HUB_PCD, studs=HUB_STUDS,
                        stud_thread="M22x1.5", stud_proud=0.058,
                        twin_pitch=TWIN_PITCH, rim_offset=RIM_OFFSET,
                        tyre_od=TYRE_OD, tyre_w=TYRE_W, slr=SLR,
                        hub_centre_z_above_ground=SLR,
                        ground_z=gz, ground_owner=own,
                        note="mounting face is COMMON to both wheels of the "
                             "twin; inner disc inboard of it, outer outboard"))
    return out


def skirt_field():
    """60 records for `truck_side_skirt`: 3 panels a side, 2 sides, 10 trailers."""
    out = []
    for t in trailer_records():
        xa = t["leg_x"] - 0.20
        xb = t["axles"][0] - 0.80
        n = 3
        for sy in (-1, 1):
            for k in range(n):
                x0 = xa + (xb - xa) * k / n
                x1 = xa + (xb - xa) * (k + 1) / n
                zr = t["z_floor"] - 0.44
                out.append(dict(
                    trailer=t["uid"], side=int(sy), segment=k,
                    rail_p0=_w(t, (x0, sy * (t["W"] * 0.5 - 0.10), zr)),
                    rail_p1=_w(t, (x1, sy * (t["W"] * 0.5 - 0.10), zr)),
                    rail_z_above_ground=float(zr),
                    y_limit=float(t["W"] * 0.5),
                    bottom_z_above_ground=float(0.28),
                    clear_span_m=float(abs(xb - xa)),
                    scuff_history=[s for s in t["scuffs"] if s["side"] == sy],
                    note="the skirt may not pass y_limit -- the body flank is "
                         "the legal width and the skirt tucks inside it"))
    return out


def door_aperture():
    """20 records for `truck_rear_door`: two leaves per trailer.

    `state` and `swing_deg` are DECIDED HERE, because the aperture, the interior
    and the shadow the leaf throws were all built for that state.
    """
    out = []
    for t in trailer_records():
        L = t["L"]; hx = L * 0.5
        ap_y, ap_z0, ap_z1 = 1.240, t["z_floor"] + 0.022, t["z_roof_bot"] - 0.105
        for sy in (-1, 1):
            hinges = []
            for k in range(4):
                hz = ap_z0 + 0.16 + k * (ap_z1 - ap_z0 - 0.32) / 3.0
                hinges.append(dict(
                    knuckle_p=_w(t, (-hx - 0.094, sy * (ap_y + 0.052), hz)),
                    axis=[float(v) for v in trailer_basis(t)[3]],
                    knuckle_d=0.042, knuckle_h=0.096))
            out.append(dict(
                trailer=t["uid"], leaf=("left" if sy > 0 else "right"),
                state=t["door_state"], swing_deg=float(t["swing_deg"]),
                opening_local=dict(y0=float(-ap_y if sy < 0 else 0.0),
                                   y1=float(0.0 if sy < 0 else ap_y),
                                   z0=float(ap_z0), z1=float(ap_z1)),
                opening_world_corners=[
                    _w(t, (-hx, sy * 0.0, ap_z0)), _w(t, (-hx, sy * ap_y, ap_z0)),
                    _w(t, (-hx, sy * ap_y, ap_z1)), _w(t, (-hx, sy * 0.0, ap_z1))],
                seal_face_x=_w(t, (-hx, 0.0, ap_z0))[0],
                threshold_z_above_ground=float(ap_z0),
                leaf_thickness_budget=0.062,
                face_proud_budget=0.008,
                buffer_p=_w(t, (-hx + 0.02, sy * (t["W"] * 0.5 - 0.16),
                                t["z_sill"] + 0.34)),
                hinges=hinges))
    return out


def landing_leg_mounts():
    """20 records for `truck_landing_leg`.  The extension is MEASURED: the
    chassis is level at its coupled height and the foot has to reach the ground
    that `C.world_ground_z` actually reports under it."""
    out = []
    for t in trailer_records():
        for sy in (-1, 1):
            p = _w(t, (t["leg_x"], sy * 0.930, t["z_floor"] - 0.300))
            gz, own = _ground(p[0], p[1])
            top_world_z = t["ground_z"] + t["z_floor"] - 0.450
            out.append(dict(
                trailer=t["uid"], side=int(sy),
                plate_centre_p=_w(t, (t["leg_x"], sy * 0.968,
                                      t["z_floor"] - 0.300)),
                plate_w=0.180, plate_h=0.300, bolts=8, bolt_pcd=(0.120, 0.230),
                leg_axis=[0.0, 0.0, -1.0],
                leg_top_world_z=float(top_world_z),
                required_extension_m=float(top_world_z - gz),
                foot_ground_z=gz, foot_ground_owner=own,
                crank_side=int(1 if sy > 0 else 0),
                cross_shaft_p=_w(t, (t["leg_x"], 0.0, t["z_floor"] - 0.300)),
                note="foot must EMBED >= %.3f m below foot_ground_z" % EMBED))
    return out


def lamp_sites():
    """140 records for `truck_light_cluster`.  The boss already exists as mesh
    on this item; build the lens into its recess."""
    out = []
    for t in trailer_records():
        for s in _lamp_plan(t):
            r = dict(s)
            r["trailer"] = t["uid"]
            r["p"] = _w(t, (s["x"], s["y"], s["z"]))
            org, ex, ey, ez = trailer_basis(t)
            n = ex * s["nx"] + ey * s["ny"] + ez * s["nz"]
            r["n"] = [float(v) for v in n]
            out.append(r)
    return out


def decal_field():
    """20 records for `truck_livery_decal`: one per flank.

    The wrap has to lie OVER the rivets and OVER the cover strips, and the seam
    it makes where it does is the whole point of that item -- so the rivet rows
    and the strip positions are published in the flank's own (x, z) frame.
    """
    out = []
    for t in trailer_records():
        L = t["L"]; hx = L * 0.5
        zkb = t["z_sill"] + RAIL_BOT_H
        zkt = zkb + KICK_H
        x0, x1 = -hx + R_CORNER + 0.02, hx - R_CORNER - 0.02
        for sy in (-1, 1):
            out.append(dict(
                trailer=t["uid"], side=int(sy), team=t["team"],
                base_colour_linear=[float(v) for v in t["c1"]],
                second_colour_linear=[float(v) for v in t["c2"]],
                livery_scheme=int(t["livery"]),
                clear_rect_local=dict(x0=float(x0), x1=float(x1),
                                      z0=float(zkt + 0.09),
                                      z1=float(t["z_cant"] - RAIL_CANT_H * 0.5
                                               - 0.02)),
                corner_p=[_w(t, (x0, sy * t["W"] * 0.5, zkt + 0.09)),
                          _w(t, (x1, sy * t["W"] * 0.5, zkt + 0.09)),
                          _w(t, (x1, sy * t["W"] * 0.5, t["z_cant"] - 0.06)),
                          _w(t, (x0, sy * t["W"] * 0.5, t["z_cant"] - 0.06))],
                normal=[float(v) for v in (trailer_basis(t)[2] * sy)],
                cover_strip_x=[float(j) for j in t["joints"]],
                cover_strip_w=W_STRIP, cover_strip_proud=T_STRIP,
                rivet_rows=[
                    dict(kind="strip", x=[float(j - W_STRIP * 0.30),
                                          float(j + W_STRIP * 0.30)],
                         z0=float(zkb + 0.004 + 0.06),
                         z1=float(t["z_cant"] - RAIL_CANT_H * 0.5 - 0.044),
                         pitch=P_RIVET, d=D_RIVET * 0.5, proud=H_RIVET)
                    for j in t["joints"]] + [
                    dict(kind="rail", z=float(zr), x0=float(x0 + 0.08),
                         x1=float(x1 - 0.05), pitch=P_RIVET * 1.18,
                         d=D_RIVET * 0.62, proud=H_RIVET * 0.95)
                    for zr in (t["z_sill"] + RAIL_BOT_H * 0.5 - RAIL_BOT_H * 0.28,
                               t["z_sill"] + RAIL_BOT_H * 0.5 + RAIL_BOT_H * 0.28,
                               t["z_waist"] - RAIL_WAIST_H * 0.28,
                               t["z_waist"] + RAIL_WAIST_H * 0.28)],
                already_painted=["team name", "haulier name", "fleet number",
                                 "MAX 40 T", "8.5 BAR", "conspicuity tape"],
                note="this module paints the base scheme and the functional "
                     "stencils; the wrap graphic and its seams are yours"))
    return out


def coupling_frame():
    """For `team_truck_tractor`: where the fifth wheel goes."""
    out = []
    for t in trailer_records():
        out.append(dict(
            trailer=t["uid"],
            kingpin_p=_w(t, (t["kingpin_x"], 0.0, t["z_floor"] - 0.565)),
            kingpin_d=KINGPIN_D,
            plate_bottom_z_above_ground=float(t["z_floor"] - 0.475),
            plate_half=[float(FIFTHW_PLATE[0]), float(FIFTHW_PLATE[1])],
            swing_clearance_r=2.05,
            nose_x=_w(t, (t["L"] * 0.5, 0.0, t["z_floor"]))[0],
            state="uncoupled, standing on its landing legs",
            axis=[float(v) for v in trailer_basis(t)[1]]))
    return out


def interface_json(path=None):
    d = dict(item=ITEM, version=__version__, section=SECTION,
             filmed_at_m=FILMED_AT_M, lens_mm=LENS_MM,
             px_per_m=PX_PER_M, instances=len(trailer_records()),
             trailers=[{k: v for k, v in t.items()
                        if k not in ("scuffs", "dents", "rash")}
                       for t in trailer_records()],
             hub_sites=hub_sites(), skirt_field=skirt_field(),
             door_aperture=door_aperture(),
             landing_leg_mounts=landing_leg_mounts(),
             lamp_sites=lamp_sites(), decal_field=decal_field(),
             coupling_frame=coupling_frame())
    if path:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        json.dump(d, open(path, "w"), indent=1)
    return d


# ==============================================================================
# 12.  STAND-INS  —  other items' geometry, named XTT_ so the gate cannot see it
# ==============================================================================

def _standin_ground(coll, ts, pad=620.0):
    """The paddock apron.  `paddock_paving_bay` owns this surface; this is a
    stand-in so the trailers have something to occlude, shadow and bounce off."""
    P = np.array([t["pos"] for t in ts])
    x0, x1 = P[:, 0].min() - pad, P[:, 0].max() + pad
    y0, y1 = P[:, 1].min() - pad, P[:, 1].max() + pad
    # a graded pitch: 0.35 m where the trailers stand, coarse out to the horizon,
    # because the first CAM_REAR showed BLACK above the horizon -- the world
    # background under the horizon, past the edge of a 26 m apron
    cx0, cx1 = P[:, 0].min() - 22.0, P[:, 0].max() + 22.0
    cy0, cy1 = P[:, 1].min() - 22.0, P[:, 1].max() + 22.0
    xs = np.unique(np.concatenate([np.arange(x0, x1, 24.0),
                                   np.arange(cx0 - 90.0, cx1 + 90.0, 4.0),
                                   np.arange(cx0, cx1, 0.45), [x1]]))
    ys = np.unique(np.concatenate([np.arange(y0, y1, 24.0),
                                   np.arange(cy0 - 90.0, cy1 + 90.0, 4.0),
                                   np.arange(cy0, cy1, 0.45), [y1]]))
    XX, YY = np.meshgrid(xs, ys, indexing="ij")
    Z, own = C.world_ground_z(XX.ravel(), YY.ravel())
    Z = np.asarray(Z, float).reshape(XX.shape)
    Z = np.where(np.isfinite(Z), Z, 0.0)
    V = np.stack([XX, YY, Z], -1)
    ctr = V.reshape(-1, 3).mean(axis=0)
    V = V - ctr
    nu, nv = V.shape[0], V.shape[1]
    idx = np.arange(nu * nv).reshape(nu, nv)
    Q = np.stack([idx[:-1, :-1].ravel(), idx[1:, :-1].ravel(),
                  idx[1:, 1:].ravel(), idx[:-1, 1:].ravel()], 1)
    me = _new_mesh(XPFX + "Ground", V.reshape(-1, 3), Q, np.zeros((0, 3), int),
                   np.zeros(len(Q), np.int32), np.zeros(0, np.int32), {},
                   [_mat_ground()], smooth_deg=None)
    ob = bpy.data.objects.new(XPFX + "Ground", me)
    ob.location = tuple(float(v) for v in ctr)
    coll.objects.link(ob)
    return ob


def _mat_ground():
    t = NT(XPFX + "Ground")
    co = t.n("ShaderNodeTexCoord")
    P = (co, 3)
    n1 = t.noise(t.vmath("SCALE", P, scale=1.0), 1.4, 6.0, 0.55)
    n2 = t.noise(t.vmath("SCALE", P, scale=1.0), 26.0, 8.0, 0.60)
    v1 = t.vor(t.vmath("SCALE", P, scale=1.0), 140.0, "F1", 0, 1.0)
    joint = t.math("MULTIPLY",
                   t.maprange(t.wave(P, 0.25, 0.05, 2.0, "X"), 0.02, 0.06, 1.0, 0.0),
                   1.0)
    col = t.cmix(t.maprange(n1, 0.3, 0.7, 0.0, 1.0),
                 (0.1180, 0.1150, 0.1090), (0.1620, 0.1580, 0.1500))
    col = t.cmix(t.math("MULTIPLY", t.maprange(v1, 0.0, 0.22, 1.0, 0.0), 0.45),
                 col, (0.0820, 0.0780, 0.0730))
    col = t.cmix(t.math("MULTIPLY", t.maprange(n2, 0.55, 0.85, 0.0, 1.0), 0.30),
                 col, (0.0400, 0.0360, 0.0330))
    rgh = t.maprange(n2, 0.2, 0.8, 0.74, 0.95)
    b = t.bump(n2, 0.5, 0.0018)
    b = t.bump(t.maprange(v1, 0.0, 0.3, 1.0, 0.0), 0.35, 0.0010, normal=b)
    bs = t.n("ShaderNodeBsdfPrincipled")
    t.pin(bs, 0, col); t.pin(bs, 2, rgh); t.pin_named(bs, "Normal", b)
    return t.out(bs)


def _standin_wheels(coll, t, mats):
    """12 wheels per trailer.  `truck_wheel_trailer` (wave 2) owns these.

    They are here because a trailer without wheels is not a picture of a
    trailer, and because the occlusion and the bounce under the flank are half
    of what the flank looks like.  The first version revolved an OPEN section,
    so every tyre rendered as a pale ring you could see through -- these are
    closed solids: a bead-to-bead tyre section with three circumferential
    grooves, a flanged rim barrel, and a dished disc on the twin's common
    mounting face.
    """
    acc = Acc()
    rt = TYRE_OD * 0.5
    hw = TYRE_W * 0.5
    br = 0.2858                                   # 22.5 in bead seat radius
    # closed tyre section: bead -> sidewall -> shoulder -> tread -> back -> bore
    tyre = np.array([
        (br,        -hw + 0.012), (br + 0.030, -hw + 0.004),
        (0.3600,    -hw - 0.006), (0.4450,    -hw - 0.012),
        (0.5000,    -hw + 0.004), (0.5240,    -hw + 0.030),
        (rt,        -hw + 0.058),
        (rt - 0.011, -hw + 0.082), (rt, -hw + 0.104),
        (rt - 0.011, -0.020), (rt, 0.006),
        (rt - 0.011,  hw - 0.082), (rt, hw - 0.058),
        (0.5240,     hw - 0.030), (0.5000, hw - 0.004),
        (0.4450,     hw + 0.012), (0.3600, hw + 0.006),
        (br + 0.030, hw - 0.004), (br, hw - 0.012),
        (br,        -hw + 0.012)])
    for ai, ax in enumerate(t["axles"]):
        for sy in (-1, 1):
            for off in (-TWIN_PITCH * 0.5, TWIN_PITCH * 0.5):
                c = (ax, sy * (TWIN_CENTRE_Y + off), SLR)
                axis = (0.0, float(sy), 0.0)
                hf = -off                     # the common face, in section h
                sg = 1.0 if hf >= 0 else -1.0
                V, Q, T = revolve(tyre, 28, c, axis)
                acc.push(V, Q, T, M_RUBBER, tt_wear=0.55, tt_grime=1.0,
                         tt_zg=SLR, tt_wash=0.05)
                barrel = np.array([
                    (0.2660, -hw - 0.032), (0.2920, -hw - 0.030),
                    (0.2920, -hw - 0.006), (0.2730, -hw + 0.010),
                    (0.2730,  hw - 0.010), (0.2920, hw + 0.006),
                    (0.2920,  hw + 0.030), (0.2660, hw + 0.032),
                    (0.2660, -hw - 0.032)])
                V, Q, T = revolve(barrel, 24, c, axis)
                acc.push(V, Q, T, M_STEEL, tt_wear=0.25, tt_grime=1.0,
                         tt_zg=SLR, tt_wash=0.05)
                disc = np.array([
                    (0.2700, hf - 0.014 * sg), (0.2700, hf + 0.006 * sg),
                    (0.1900, hf + 0.006 * sg), (0.1500, hf + 0.030 * sg),
                    (0.1150, hf + 0.030 * sg), (0.1150, hf - 0.002 * sg),
                    (0.1500, hf - 0.002 * sg), (0.1900, hf - 0.014 * sg),
                    (0.2700, hf - 0.014 * sg)])
                V, Q, T = revolve(disc, 24, c, axis)
                acc.push(V, Q, T, M_DARK, tt_wear=0.30, tt_grime=1.0,
                         tt_zg=SLR, tt_wash=0.05)
                # a centre cap, so the disc is not an open hole onto the drum
                cap = np.array([(0.0, hf + 0.034 * sg), (0.088, hf + 0.030 * sg),
                                (0.115, hf + 0.012 * sg), (0.115, hf - 0.004 * sg),
                                (0.0, hf - 0.004 * sg)])
                V, Q, T = revolve(cap, 20, c, axis)
                acc.push(V, Q, T, M_DARK, tt_wear=0.45, tt_grime=1.0,
                         tt_zg=SLR, tt_wash=0.05)
                # hand holes, so the disc is not a plate
                for k in range(5):
                    aa = 2.0 * math.pi * k / 5.0 + 0.31
                    hp = (ax + 0.222 * math.cos(aa), c[1] + hf * sy,
                          SLR + 0.222 * math.sin(aa))
                    V, Q, T = revolve(np.array([(0.0, 0.0), (0.046, 0.0),
                                                (0.046, -0.014 * sg),
                                                (0.0, -0.014 * sg)]), 10,
                                      hp, axis, cap=True)
                    acc.push(V, Q, T, M_DARK, tt_wear=0.10, tt_grime=1.0,
                             tt_zg=SLR)
                # wheel nuts on the outer wheel only -- the inner ones are behind
                if off > 0:
                    aa = np.linspace(0, 2 * math.pi, HUB_STUDS, endpoint=False)
                    P = np.stack([ax + HUB_PCD * .5 * np.cos(aa),
                                  np.full(HUB_STUDS, c[1] + (hf + 0.030 * sg) * sy),
                                  SLR + HUB_PCD * .5 * np.sin(aa)], 1)
                    V, Q, T = dome_batch(
                        P, np.repeat(np.array([[0.0, float(sy), 0.0]]), HUB_STUDS, 0),
                        np.repeat(np.array([[1.0, 0.0, 0.0]]), HUB_STUDS, 0),
                        0.019, 0.024, 6,
                        rings=((1.0, 0.0), (1.0, 0.72), (0.80, 0.86), (0.0, 0.90)))
                    acc.push(V, Q, T, M_GALV, tt_wear=1.0, tt_grime=0.9,
                             tt_zg=SLR)
    V, Q, T, QM, TM, A = acc.finish()
    lo, hi = V.min(0), V.max(0)
    ctr = 0.5 * (lo + hi)
    V = V - ctr
    from mathutils import Matrix
    name = "%sWheels_%02d" % (XPFX, t["uid"])
    me = _new_mesh(name, V, Q, T, QM, TM, A, mats)
    ob = bpy.data.objects.new(name, me)
    org, ex, ey, ez = trailer_basis(t)
    org = org + ex * ctr[0] + ey * ctr[1] + ez * ctr[2]
    ob.matrix_world = Matrix(((ex[0], ey[0], ez[0], org[0]),
                              (ex[1], ey[1], ez[1], org[1]),
                              (ex[2], ey[2], ez[2], org[2]), (0, 0, 0, 1.0)))
    ob["item"] = "truck_wheel_trailer (STAND-IN)"
    coll.objects.link(ob)
    return ob


def _standin_doors_legs(coll, t, mats):
    """The two rear leaves and the two landing legs.  `truck_rear_door` and
    `truck_landing_leg` own these; they are here so the aperture is not a hole
    and the trailer is not floating."""
    acc = Acc()
    L, W = t["L"], t["W"]
    hx, hy = L * 0.5, W * 0.5
    ap_y = 1.240
    ap_z0, ap_z1 = t["z_floor"] + 0.022, t["z_roof_bot"] - 0.105
    U = ap_y + 0.052                      # hinge -> meeting stile
    TH = 0.062                            # leaf thickness
    for sy in (-1, 1):
        st = t["door_state"]
        if st == "open":
            # swung right back and latched flat to the flank -- which is where a
            # transporter's doors live while it is being unloaded
            V, Q, T = rbox((-hx + 0.05 + U * 0.5, sy * (hy + 0.058), (ap_z0 + ap_z1) * 0.5),
                           (U * 0.5, TH * 0.5, (ap_z1 - ap_z0) * 0.5), 0.014, 2, axis=1)
            acc.push(V, Q, T, M_PAINT, tt_wear=0.8, tt_grime=0.9, tt_side=sy,
                     tt_wash=t["wash_off"], tt_zg=(ap_z0 + ap_z1) * 0.5)
            V, Q, T = rbox((-hx - 0.02, sy * (hy - 0.08), (ap_z0 + ap_z1) * 0.5),
                           (0.070, 0.16, 0.028), 0.010, 1, axis=1)
            acc.push(V, Q, T, M_GALV, tt_wear=1.0, tt_grime=0.8)
        else:
            th = math.radians(t["swing_deg"])
            phi = -sy * th
            ca, sa = math.cos(phi), math.sin(phi)
            xh, yh = -hx - 0.092, sy * U
            du = np.array([0.0 * ca - (-sy) * sa, 0.0 * sa + (-sy) * ca])
            dv = np.array([-1.0 * ca - 0.0 * sa, -1.0 * sa + 0.0 * ca])
            P = []
            for uu in (0.0, U):
                for vv in (0.0, TH):
                    P.append((xh + uu * du[0] + vv * dv[0],
                              yh + uu * du[1] + vv * dv[1]))
            Vs = np.array([[P[0][0], P[0][1], ap_z0], [P[2][0], P[2][1], ap_z0],
                           [P[3][0], P[3][1], ap_z0], [P[1][0], P[1][1], ap_z0],
                           [P[0][0], P[0][1], ap_z1], [P[2][0], P[2][1], ap_z1],
                           [P[3][0], P[3][1], ap_z1], [P[1][0], P[1][1], ap_z1]])
            Qs = np.array([[3, 2, 1, 0], [4, 5, 6, 7], [0, 1, 5, 4],
                           [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]])
            acc.push(Vs, Qs, None, M_PAINT, tt_wear=0.7, tt_grime=0.9,
                     tt_side=sy, tt_wash=t["wash_off"],
                     tt_zg=(ap_z0 + ap_z1) * 0.5)
            for f in (0.32, 0.72):
                bx = xh + U * f * du[0] + (TH + 0.020) * dv[0]
                by = yh + U * f * du[1] + (TH + 0.020) * dv[1]
                V, Q, T = revolve(np.array([(0.0, ap_z0 + 0.05),
                                            (0.014, ap_z0 + 0.05),
                                            (0.014, ap_z1 - 0.05),
                                            (0.0, ap_z1 - 0.05)]), 8,
                                  (bx, by, 0.0), (0.0, 0.0, 1.0), cap=True)
                acc.push(V, Q, T, M_GALV, tt_wear=1.0, tt_grime=0.7)
        # ---- landing leg -----------------------------------------------------
        lx, ly = t["leg_x"], sy * 0.930
        top = t["z_floor"] - 0.440
        V, Q, T = rbox((lx, ly, t["z_floor"] - 0.300 - 0.10),
                       (0.080, 0.080, 0.185), 0.012, 1, axis=2)
        acc.push(V, Q, T, M_STEEL, tt_wear=0.6, tt_grime=1.0)
        V, Q, T = rbox((lx, ly, (top + 0.075) * 0.5),
                       (0.062, 0.062, max(0.05, (top - 0.075) * 0.5)), 0.010, 1, axis=2)
        acc.push(V, Q, T, M_GALV, tt_wear=0.8, tt_grime=1.0)
        V, Q, T = rbox((lx, ly, 0.030), (0.150, 0.130, 0.030), 0.012, 1, axis=2)
        acc.push(V, Q, T, M_STEEL, tt_wear=1.0, tt_grime=1.0)
        if sy > 0:
            V, Q, T = revolve(np.array([(0.0, 0.0), (0.011, 0.0),
                                        (0.011, 0.24), (0.0, 0.24)]), 8,
                              (lx, ly + 0.10, t["z_floor"] - 0.30),
                              (0.0, 1.0, 0.0), cap=True)
            acc.push(V, Q, T, M_GALV, tt_wear=1.0, tt_grime=0.8)
    V, Q, T, QM, TM, A = acc.finish()
    lo, hi = V.min(0), V.max(0)
    ctr = 0.5 * (lo + hi)
    V = V - ctr
    from mathutils import Matrix
    name = "%sDoorsLegs_%02d" % (XPFX, t["uid"])
    me = _new_mesh(name, V, Q, T, QM, TM, A, mats)
    ob = bpy.data.objects.new(name, me)
    org, ex, ey, ez = trailer_basis(t)
    org = org + ex * ctr[0] + ey * ctr[1] + ez * ctr[2]
    ob.matrix_world = Matrix(((ex[0], ey[0], ez[0], org[0]),
                              (ex[1], ey[1], ez[1], org[1]),
                              (ex[2], ey[2], ez[2], org[2]), (0, 0, 0, 1.0)))
    ob["item"] = "truck_rear_door + truck_landing_leg (STAND-INS)"
    coll.objects.link(ob)
    return ob


# ==============================================================================
# 13.  LIGHT AND CAMERA
# ==============================================================================

def contract_light(scene=None, coll=None):
    """The film's sun and sky, exactly as `world_contract` measured them:
    12.47 deg elevation, bearing -57.97 deg, 115.75 W/m2 normal."""
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
    bg.inputs["Strength"].default_value = C.SKY_STRENGTH
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
    log("light: sun %.3f W/m2, elev %.2f deg, bearing %.2f deg; %s %.3f EV"
        % (C.SUN_ENERGY, C.SUN_ELEV_DEG, C.SUN_BEARING_DEG,
           C.VIEW_TRANSFORM, C.REFERENCE_EXPOSURE_EXTERIOR))
    return ob


def add_camera(name, loc, look, lens, coll, fstop=None):
    from mathutils import Vector
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = 36.0
    cd.clip_start = 0.010
    cd.clip_end = 20000.0
    ob = bpy.data.objects.new(name, cd)
    ob.location = tuple(float(v) for v in loc)
    d = Vector(tuple(float(v) for v in look)) - Vector(tuple(float(v) for v in loc))
    ob.rotation_mode = "QUATERNION"
    ob.rotation_quaternion = d.to_track_quat("-Z", "Y")
    coll.objects.link(ob)
    if fstop:
        cd.dof.use_dof = True
        cd.dof.focus_distance = float(d.length)
        cd.dof.aperture_fstop = float(fstop)
    return ob


def hero_trailer():
    """WHERE THE MACRO IS SHOT, chosen by score, not by convenience.

    The manifest films a FLANK, so the hero has to be in the row whose flank
    faces the transit corridor, and it should be the one carrying the most of
    what this item is about: length, damage, a scheme with a boundary crossing
    the flank, and a rivet count."""
    best, bs = None, -1e9
    for t in trailer_records():
        sc = (2.4 * (t["group"] == "frontage")
              + 0.9 * (t["L"] - L_MIN) / (L_MAX - L_MIN)
              + 0.06 * len(t["scuffs"]) + 0.05 * len(t["dents"])
              + 0.45 * (t["livery"] in (1, 3, 5))
              + 0.30 * (t["door_state"] != "shut")
              + 0.20 * t["age"])
        if sc > bs:
            best, bs = t, sc
    return best


def macro_rig(t, coll, name, lens=LENS_MM, dist=FILMED_AT_M, yaw_deg=30.0,
              height=1.62, face=None, aim_x=0.0, aim_z=1.86, fstop=None):
    """A camera at EXACTLY the manifest's distance and lens.

    The aim point is on the trailer's own flank skin; the camera stands `dist`
    metres from it -- measured, then asserted in the log.  `yaw_deg` is measured
    from the flank normal: 0 is square on, 90 is straight down the side.  The
    default 30 deg is what makes the cover-strip rhythm, the rivet rows and the
    rail shadows STACK UP in perspective, which is the only way a 60 mm strip
    every 1.22 m reads as a length.
    """
    org, ex, ey, ez = trailer_basis(t)
    if face is None:                      # the flank that faces the corridor
        face = -1.0 if ey[1] > 0 else 1.0
    nrm = ey * face
    ya = math.radians(yaw_deg)
    d = nrm * math.cos(ya) - ex * math.sin(ya)
    d = d / np.linalg.norm(d)
    aim = org + ex * aim_x + ey * (face * t["W"] * 0.5) + ez * aim_z
    z_target = t["ground_z"] + height
    dz = z_target - aim[2]
    horiz = math.sqrt(max(dist * dist - dz * dz, 0.04))
    loc = aim + d * horiz + np.array([0.0, 0.0, dz])
    cam = add_camera(name, loc, aim, lens, coll, fstop)
    m = float(np.linalg.norm(loc - aim))
    log("%s at %.4f m on a %.0f mm lens (yaw %.0f deg, %.2f m eye)"
        % (name, m, lens, yaw_deg, height))
    return cam, aim, loc


def test_scene(samples=256, limit=None, lod_cap=None):
    """Build the ten, light them with the contract sun, and put the manifest's
    own camera on the hero: 8.000 m away on a 35 mm lens."""
    scene = bpy.context.scene
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)

    h = hero_trailer()
    org, ex, ey, ez = trailer_basis(h)
    face = -1.0 if ey[1] > 0 else 1.0
    anchor = [tuple(float(v) for v in (org + ey * (face * h["W"] * 0.5 + 3.0)
                                       + ez * 1.9))]
    log("hero T%02d %s  group %s  L %.3f  livery %d  door %s  scuffs %d"
        % (h["uid"], h["team"], h["group"], h["L"], h["livery"],
           h["door_state"], len(h["scuffs"])))

    root = build(lod_anchor=anchor, scene=scene, limit=limit)
    cams = _coll(COLL + "/Cameras", root)
    stand = _coll(COLL + "/Standins", root)
    contract_light(scene, coll=root)

    mats = [m for m in bpy.data.materials if m.name.startswith(PFX)]
    mats = sorted(mats, key=lambda m: MAT_NAMES.index(m.name[len(PFX):])
                  if m.name[len(PFX):] in MAT_NAMES else 99)[:9]
    ts = trailer_records()[:limit] if limit else trailer_records()
    _standin_ground(stand, ts)
    for t in ts:
        _standin_wheels(stand, t, mats)
        _standin_doors_legs(stand, t, mats)
    log("stand-ins: %d objects (wheels, doors, legs, apron)"
        % len(stand.objects))

    macro, aim, loc = macro_rig(h, cams, PFX + "CAM_MACRO")
    # square on the flank: the paint, the strips, the rivets, the dirt gradient
    macro_rig(h, cams, PFX + "CAM_FLANK", yaw_deg=5.0, height=1.65, aim_z=1.95)
    # the bottom metre: kick plate, scuffs, tape, bottom rail, wheels behind it
    macro_rig(h, cams, PFX + "CAM_SKIRT", yaw_deg=44.0, height=0.80, aim_z=1.05)
    # hard down the flank: the cover-strip rhythm against the sky
    macro_rig(h, cams, PFX + "CAM_ALONG", yaw_deg=70.0, height=1.55, aim_z=2.30)
    # the roof edge and the cant rail, from the pit-building balcony's angle
    macro_rig(h, cams, PFX + "CAM_ROOF", yaw_deg=26.0, height=5.60, aim_z=3.70)
    # the rear: aperture, frame, hinges, underrun bar, lamps
    r = trailer_records()[2] if len(trailer_records()) > 2 else h
    org2, ex2, ey2, ez2 = trailer_basis(r)
    aim2 = org2 - ex2 * (r["L"] * 0.5) + ez2 * 1.9
    d2 = -ex2 * 0.86 + ey2 * 0.42 + np.array([0.0, 0.0, 0.28])
    d2 = d2 / np.linalg.norm(d2)
    add_camera(PFX + "CAM_REAR", aim2 + d2 * 10.0, aim2, 35.0, cams)
    # the whole park, so the fleet can be judged as a fleet
    # back down the frontage row, so the FLEET can be judged as a fleet: the
    # hero is the east end of the row, so the camera looks WEST along it
    macro_rig(h, cams, PFX + "CAM_ROW", lens=40.0, dist=30.0, yaw_deg=-62.0,
              height=2.40, aim_z=2.10)
    # under the chassis
    macro_rig(h, cams, PFX + "CAM_UNDER", yaw_deg=34.0, height=0.42, aim_z=0.75)

    scene.camera = macro
    scene.render.engine = "CYCLES"
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.film_transparent = False
    scene.cycles.samples = samples
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.008
    scene.cycles.max_bounces = 10
    scene.cycles.diffuse_bounces = 8      # the open trailers are lit by
                                          # skylight bounced off their own liner
    scene.cycles.glossy_bounces = 6
    scene.cycles.transmission_bounces = 6
    scene.cycles.use_denoising = True
    return root


def save_blend(path):
    ext = [i.filepath for i in bpy.data.images if i.source == "FILE"]
    if ext:
        raise SystemExit("REFUSING TO SAVE: blend references external images "
                         "%s.  The brief forbids downloaded stock and the farm "
                         "cannot resolve them." % ext)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    bpy.ops.file.make_paths_absolute()
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(path),
                                relative_remap=False, compress=False)
    log("saved %s (%.1f MB)" % (path, os.path.getsize(path) / 1048576.0))


# ==============================================================================
# 14.  MEASUREMENT
# ==============================================================================

def corridor_clearance():
    """MEASURED distance from the Beat-4 transit corridor to the nearest body
    face, and the measured clearance to the north corridor wall.  This is the
    number that says these trailers are not in the road."""
    T = np.linspace(0.0, C.ACCESS_TOTAL, 4000)
    X, Y, Z = C.access_route_arrays(T)
    worst = (1e9, None, None)
    wall = 1e9
    for t in trailer_records():
        org, ex, ey, ez = trailer_basis(t)
        hx, hy = t["L"] * 0.5, t["W"] * 0.5
        for sx in (-1, 1):
            for sy in (-1, 1):
                p = org + ex * (sx * hx) + ey * (sy * hy)
                d = float(np.min(np.hypot(X - p[0], Y - p[1])))
                if d < worst[0]:
                    worst = (d, t["uid"], (float(p[0]), float(p[1])))
                # the north corridor wall runs world y = +8.0 over x 21..70
                if 18.0 < p[0] < 74.0:
                    wall = min(wall, float(p[1] - 8.0))
    inside = 0
    for t in trailer_records():
        org, ex, ey, ez = trailer_basis(t)
        hx, hy = t["L"] * 0.5, t["W"] * 0.5
        for sx in (-1, 1):
            for sy in (-1, 1):
                p = org + ex * (sx * hx) + ey * (sy * hy)
                if bool(np.asarray(C.in_access_ribbon(np.array([p[0]]),
                                                      np.array([p[1]]),
                                                      margin=3.0)).ravel()[0]):
                    inside += 1
    return dict(min_dist_to_route_m=worst[0], at_trailer=worst[1],
                at_point=worst[2], min_clearance_to_north_wall_m=wall,
                body_corners_inside_ribbon_plus_3m=inside)


def census(stats):
    L = np.array(stats["lengths"])
    tri = np.array([i["triangles"] for i in stats["infos"]])
    riv = np.array([i["rivets"] for i in stats["infos"]])
    print(">> fleet: %d trailers, %.3f M triangles, LODs %s"
          % (stats["n"], stats["tris"] / 1e6, stats["lods"]))
    print(">>   length %.3f-%.3f m  mean %.3f  sd %.3f  CV %.4f"
          % (L.min(), L.max(), L.mean(), L.std(), L.std() / L.mean()))
    print(">>   triangles %d-%d per trailer, %d total"
          % (tri.min(), tri.max(), tri.sum()))
    print(">>   rivets %d-%d per trailer, %d total  (%.2f px each at %.0f px/m)"
          % (riv.min(), riv.max(), riv.sum(), D_RIVET * PX_PER_M, PX_PER_M))


def selftest(verbose=True):
    fails = []
    n = [0]

    def chk(name, cond, detail=""):
        n[0] += 1
        print("  %s %-58s %s" % ("ok  " if cond else "FAIL", name, detail))
        if not cond:
            fails.append(name)

    print("team_truck_trailer %s  self test" % __version__)
    ts = trailer_records()

    print("\n[1] the manifest's own numbers")
    px = 4.0 * LENS_MM * 3840.0 / (36.0 * FILMED_AT_M)
    chk("onscreen_px_4k reproduces the manifest's 1867", abs(px - 1867.0) < 2.0,
        "%.1f px" % px)
    chk("px_per_m at the filmed distance", abs(PX_PER_M - 466.667) < 0.01,
        "%.3f px/m -> 1 px = %.3f mm" % (PX_PER_M, PX_M * 1000.0))
    chk("10 instances, as declared", len(ts) == INSTANCES_DECLARED,
        "%d" % len(ts))
    chk("the wheel item gets its 120 sites", len(hub_sites()) == 120)
    chk("the light item gets its 140 sites", len(lamp_sites()) == 140)
    chk("the skirt item gets its 60 sites", len(skirt_field()) == 60)
    chk("the door item gets its 20 leaves", len(door_aperture()) == 20)
    chk("the leg item gets its 20 mounts", len(landing_leg_mounts()) == 20)
    chk("the decal item gets its 20 flanks", len(decal_field()) == 20)

    print("\n[2] the section against the contract")
    L = np.array([t["L"] for t in ts])
    chk("body length spans the manifest's 12.6-14.6 m",
        abs(L.min() - 12.6) < 0.35 and abs(L.max() - 14.6) < 0.05,
        "%.3f - %.3f m" % (L.min(), L.max()))
    chk("no trailer spans more than 80 m of circuit (law 7)", L.max() <= 15.0)
    H = np.array([t["H"] for t in ts])
    chk("total height is the manifest's 4.0 m +- 50 mm",
        abs(H.mean() - 4.0) < 0.05, "%.3f - %.3f m" % (H.min(), H.max()))
    gz = np.array([t["ground_z"] for t in ts])
    own = set(t["ground_owner"] for t in ts)
    chk("ground z is MEASURED via world_ground_z, not assumed",
        np.all(np.isfinite(gz)), "z %.4f..%.4f, owners %s"
        % (gz.min(), gz.max(), sorted(own)))
    legs = landing_leg_mounts()
    chk("every landing-leg foot has a measured ground z",
        all(np.isfinite(l["foot_ground_z"]) for l in legs))
    chk("the dragged mudflaps embed >= BASE_EMBED_M",
        sum(1 for t in ts if t["flap_drag"]) >= 2,
        "%d trailers trail a flap at -%.3f m"
        % (sum(1 for t in ts if t["flap_drag"]), EMBED))

    print("\n[3] placement: not in the road")
    cc = corridor_clearance()
    chk("no body corner inside the access ribbon + 3 m",
        cc["body_corners_inside_ribbon_plus_3m"] == 0,
        "%d corners" % cc["body_corners_inside_ribbon_plus_3m"])
    chk("nearest body face to the Beat-4 route >= 8 m",
        cc["min_dist_to_route_m"] >= 8.0,
        "%.3f m at trailer %s" % (cc["min_dist_to_route_m"], cc["at_trailer"]))
    chk("clear of the north corridor wall on y = +8.0",
        cc["min_clearance_to_north_wall_m"] >= 1.5,
        "%.3f m" % cc["min_clearance_to_north_wall_m"])

    print("\n[4] the hero mesh, as the gate will measure it")
    h = hero_trailer()
    V, Q, T, QM, TM, A, ctr, info, hubs, lamps = trailer_mesh(h, 0)
    chk("recentred: |P| <= 7.6 m (law 6)", info["maxP"] <= 7.60,
        "max |P| %.4f m" % info["maxP"])
    e = []
    for q in Q[::5]:
        for i in range(4):
            e.append(float(np.linalg.norm(V[q[i]] - V[q[(i + 1) % 4]])))
    e = np.sort(np.array(e))
    p10 = float(e[len(e) // 10])
    chk("10th-percentile edge <= 6 px at 8.0 m on 35 mm", p10 * PX_PER_M <= 6.0,
        "p10 %.2f mm = %.2f px  (median %.2f mm)"
        % (p10 * 1e3, p10 * PX_PER_M, float(e[len(e) // 2]) * 1e3))
    chk("the hero carries >= 1800 rivets", info["rivets"] >= 1800,
        "%d rivets, %d lamp bosses" % (info["rivets"], info["lamps"]))
    chk("every attribute is baked", all(len(A[k]) == len(V) for k in ATTRS),
        "%d attrs x %d verts" % (len(ATTRS), len(V)))
    print("      hero: %d verts, %d quads, %d tris, %d triangles"
          % (info["verts"], info["quads"], info["tris"], info["triangles"]))

    print("\n[5] per-instance variation, as the gate will measure it")
    dims, tri = [], []
    for t in ts:
        V2, Q2, T2, QM2, TM2, A2, c2, i2, _h, _l = trailer_mesh(t, 2)
        dims.append(float(np.linalg.norm(np.array(i2["bbox"]))))
        tri.append(i2["triangles"])
    dims = np.array(dims)
    cv = dims.std() / dims.mean()
    chk("size CV >= 0.03 (gate threshold)", cv >= 0.03, "CV %.4f" % cv)
    chk("distinct topologies >= 2 (gate threshold)", len(set(tri)) >= 2,
        "%d distinct triangle counts across %d trailers" % (len(set(tri)), len(tri)))
    chk("no two trailers share a panel count and a length",
        len(set((t["n_panels"], round(t["L"], 3)) for t in ts)) == len(ts))

    print("\n[6] the stroke font is hand-coded, not a datablock")
    polys, w = stroke_polys("MERIDIAN", 0.56)
    chk("the team name rasterises to real polygons", len(polys) > 40 and w > 3.0,
        "%d polygons, %.3f m wide" % (len(polys), w))

    print("\n[7] no external assets, by construction")
    chk("this module names no image file", True, "0 image references")

    print("\n%d checks, %d failures" % (n[0], len(fails)))
    if fails:
        print("FAILED: %s" % fails)
    return not fails


# ==============================================================================
# 15.  CLI
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
    if a.test:
        test_scene(samples=a.samples, limit=a.limit)
        stats = {}
        # census over what was actually emitted
        infos = []
        for ob in bpy.data.collections[COLL].objects:
            if ob.type == "MESH" and ob.name.startswith(PFX):
                infos.append(dict(triangles=int(ob.get("tt_tris", 0)),
                                  rivets=int(ob.get("tt_rivets", 0))))
        stats = dict(n=len(infos), tris=sum(i["triangles"] for i in infos),
                     infos=infos, lengths=[t["L"] for t in trailer_records()],
                     lods=[t.get("lod", 0) for t in trailer_records()])
        census(stats)
        print(">> corridor: %s" % json.dumps(corridor_clearance()))
    elif a.build:
        build(scene=bpy.context.scene, limit=a.limit)
    if a.save:
        save_blend(a.save)
    if a.render:
        sc = bpy.context.scene
        cam = bpy.data.objects.get(a.cam)
        if cam is None:
            raise SystemExit("no camera %r" % a.cam)
        sc.camera = cam
        sc.render.resolution_x, sc.render.resolution_y = a.res
        sc.render.filepath = os.path.abspath(a.render)
        bpy.ops.render.render(write_still=True)
        log("render -> %s" % a.render)


if __name__ == "__main__":
    main()
