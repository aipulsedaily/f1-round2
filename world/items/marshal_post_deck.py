#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
marshal_post_deck.py — CIRCUIT VITRINE, per-item hero campaign, item
``marshal_post_deck`` (zone ``trackside``, wave 1, build order 131).

WHAT THIS IS, IN ONE SENTENCE
=============================
The standing surface of all 25 marshal posts, built as **real boards with real
gaps you can see the ground through** — every board an individually generated
solid with its own cup, bow, twist, raised grain, splits, sunk fixings and
galvanised end bands, laid on real framing, with the space underneath used for
storage the way a marshal post's underdeck actually is.

WHY IT IS GEOMETRY AND NOT A TEXTURE  (the manifest said so, in these words)
---------------------------------------------------------------------------
    "The rejected render showed this as flat cardboard - it needs board gaps,
     a wear path, and things stored under the deck."
                                    -- docs/item_manifest.json, this item

The arithmetic that decides how far to take it:

    px_per_m = (3840 * 35 / 36) / 6.0 = 622.2 px/m   ->   1 px = 1.607 mm

so at the distance this item is filmed:

    a  6 mm board gap            =  3.7 px   -> must be a HOLE, not a dark line
    a 38 mm board thickness      = 23.6 px   -> the front edge is a real arris
    an 8 mm countersunk screw    =  5.0 px   -> head, dish and slot are meshed
    a  0.9 mm hoop-iron end band =  0.6 px   -> reads as a bright line, so it is
                                                a 0.9 mm strap, not a stripe
    a  0.8 mm raised grain ridge under the contract sun (12.471 deg elevation,
       C.SUN_SHADOW_RATIO = 4.522) throws a 3.6 mm = 2.2 px cast shadow

A bump map cannot cast that shadow, cannot show daylight through a gap, and has
no silhouette against the sky at the deck's front edge.  So all of it is mesh.

THE PUBLIC INTERFACE  (this item is a FOUNDATION — six items depend on it)
==========================================================================
Named in the manifest as dependants: ``marshal_post_handrail``,
``marshal_post_stair``, ``marshal_chair``, ``marshal_absorbent_bin``,
``marshal_water_cooler``, ``marshal_broom``.  None of them can ask questions,
so every number they need is a function here.

--- 1. WHERE THE 25 DECKS ARE ------------------------------------------------

    deck_plan() -> [Deck, ...]      25 records, ``n`` = 1..25, sorted by lap
                                    station.  THIS IS THE PLACEMENT AUTHORITY
                                    for the whole marshal-post family.

    Each ``Deck`` carries: ``n s side lat kind wx wy gz yaw_deg W D H`` plus the
    derived deck box.  ``kind`` is the archetype, 0..3, and it is NOT this
    module's invention — it is ``build_dressing.marshal_post_plan()``'s own
    ``kind``, frozen into ``SITES`` below so that a rebuild of build_dressing
    cannot silently move a post out from under its deck.  See §SITES.

    site_frame(d)  -> (R, O)        3x3 rotation, 3-vector origin.  Deck-local
                                    -> world.  ``O`` is ON THE GROUND at the
                                    post anchor (z = C.world_ground_z there),
                                    so deck-local z is height above grade.
    to_world(d, P) -> (n,3)         apply it to an array of local points.

    LOCAL FRAME, and it matters: +x is the deck's WIDTH, along the barrier line;
    **+y points AWAY from the track**, so the deck's FRONT (the edge a marshal
    stands at, facing the circuit) is at y = -Dd/2.  Same convention as
    build_dressing's marshal post, deliberately.

--- 2. STANDING ON IT --------------------------------------------------------

    deck_top_z(d, x, y) -> z        LOCAL z of the walking surface at a local
                                    (x, y), including the board's cup, bow, sag,
                                    the wear hollow and the raised grain.  It is
                                    the surface, not the nominal plane: over the
                                    25 decks it departs from ``d.H`` by
                                    -6.9 mm .. +2.3 mm.  A chair leg or a bin
                                    foot placed on ``d.H`` floats or sinks;
                                    placed on this it lands.  Never NaN: over a
                                    gap it returns the SUPPORTING level, which
                                    is where a foot bridging the gap rests.

    over_gap(d, x, y) -> bool       True where (x, y) is over a hole rather than
                                    over board.  A 12 mm gap at 622 px/m is 7 px
                                    wide and a chair leg standing in one is a
                                    visible lie.
    on_deck(d, x, y) -> bool        True inside the deck's own outline.

    floor_slots(d) -> [Slot, ...]   the free rectangles left on the deck once
                                    the flag rack, the access opening and the
                                    wear path are accounted for, each with the
                                    board direction under it, ``clear_h`` to the
                                    roof, and which edge it faces.  This is what
                                    ``marshal_chair`` / ``marshal_water_cooler``
                                    / ``marshal_absorbent_bin`` should place
                                    into, worst-to-best by ``quality``.

--- 3. BOLTING TO IT ---------------------------------------------------------

    handrail_sockets(d) -> [...]    where ``marshal_post_handrail`` stands its
                                    posts: local (x, y), the deck top z there,
                                    the fixing already built into this module
                                    (a welded lug, a bolted flange or a scaffold
                                    coupler), its size, and the outward normal.
                                    The deck HAS the lugs and the bolt holes;
                                    the rail must land on them.

    stair_landing(d) -> Landing     which edge the stair arrives at, the exact
                                    local (x, y) of the landing nose, the deck
                                    top z, the total rise to grade, the going
                                    the treads have to divide, the clear opening
                                    width in the toe board, and the nosing
                                    overhang.  ``marshal_post_stair`` builds
                                    DOWN from here.  The opening is already cut.

    lean_points(d) -> [...]         where a broom, a shovel or a rake can lean:
                                    a local foot point, the surface it leans
                                    against, its normal and the lean angle.
                                    ``marshal_broom`` picks from this.

    column_sockets(d) -> [...]      ** READ THIS ONE FIRST, marshal_post_column.
                                    ** The four (or six) places this deck's
                                    framing is carried, with the section it
                                    expects (48.3 mm OD tube / 60x60 box /
                                    100x50 timber), the z the bearing sits at,
                                    the ground z under it, the base plate and
                                    sole board this module ALREADY built, and
                                    whether the deck is notched around it.
                                    The column lands here, on this, at this
                                    diameter.  Nothing else in the family owns
                                    this contact.

--- 4. THE SPACE UNDERNEATH --------------------------------------------------

    under_deck(d) -> Under          clear box under the deck, the stored items
                                    this module put there as axis-aligned boxes
                                    (so nothing else places into them), and the
                                    remaining free boxes.  ``occupied`` is in
                                    LOCAL coordinates.

--- 5. WHAT VARIES, AND WHERE THE VARIATION LIVES ----------------------------

The manifest names four axes.  All four are GEOMETRY, per instance:

  archetype        4 genuinely different constructions, not one mesh scaled:
                   0 ``canopy``   timber duckboard on bearers laid on the pad,
                                  145 x 32 boards, ring-shank nails, no bands
                   1 ``hut``      18 mm WBP ply floor on 100x50 joists over
                                  sleepers, sheet joints, worn doorway, hatch
                   2 ``stand``    galvanised RHS frame carrying open steel bar
                                  grating: 30x5 load bars at 34 mm with twisted
                                  cross rods — the deck you can see through
                                  entirely
                   3 ``platform`` scaffold: 48.3 mm ledgers and transoms with
                                  right-angle couplers, 225 x 38 scaffold boards
                                  with hoop-iron end bands, toe boards, and on
                                  some decks a pressed-steel hook-on deck unit
  board gaps       per deck 5-17 mm nominal, per board +-3 mm, and each gap
                   OPENS AND CLOSES along its length because the boards bow
  wear path        a real walked line from the access edge to the flag stance,
                   eroding the board tops 0.4-2.4 mm, opening the arris, raising
                   the grain where the soft earlywood has gone, and standing the
                   nail heads proud of the wood that has worn away around them
  height above     0.10 m (duckboard) to 1.29 m (scaffold platform), drawn per
  grade            instance, and the framing changes with it — and it also
                   decides WHERE the kit goes: above ~0.17 m it goes under the
                   deck, below that nothing fits and it stands on the
                   hardstanding beside it (``Deck.stores_beside()``)

THE SEVEN LAWS, AND WHERE EACH ONE IS DISCHARGED
================================================
 1. procedural, by hand      no image node, no file, no library.  Every board is
                             generated from its own parameter draw.
 2. no real brands           this item carries no lettering.
 3. car scale                not a scale-carrying item; deck heights are set
                             against a 1.75 m marshal, not against the car.
 4. z = 0 is one plane       never assumed: every ground contact comes from
                             ``C.world_ground_z(x, y)`` at that footing's own
                             world position, and the ground under a 3 m deck is
                             not flat — the packing shims prove it.
 5. embed >= 20 mm           every sleeper, sole board, base plate, pad block
                             and sandbag that touches ground is sunk
                             ``C.BASE_EMBED_M`` into it.  ``selftest`` measures
                             the minimum over all 25 decks.
 6. recentre + TexCoord      each deck's mesh is local to its own origin
                             (|P| < 3.3 m); the object matrix carries the up-to
                             900 m out to the circuit.  Materials read
                             ``TexCoord->Object`` and the baked ``mpd_*``
                             attributes.  ``Geometry->Position`` appears nowhere.
 7. chunk along s            one object per post; the largest spans 3.3 m.

** ASSEMBLY MUST SUPPRESS build_dressing's OWN DECK. **  `build_shelter()` in
build_dressing still emits a platform deck of its own for `kind == 3` (the
`lo.box` deck slab plus its 220 mm plank strips) and a bench for `kind == 1`.
This item REPLACES that geometry at the same station, the same lateral and the
same height — leave both in and every platform post z-fights across its whole
deck. Whoever assembles the world deletes build_dressing's deck strips, or
calls `build_shelter(..., deck=False)` once that argument exists. Nothing else
in build_dressing's marshal post collides: the legs, roof, skin, flag rack and
equipment are all other items' or still build_dressing's.

WHAT WAS MEASURED  (`--selftest`, `--measure`, and `tools/item_gate.py`)
=======================================================================
    25 decks, worst station gap 253.9 m          == the manifest's own figures
    5,406,908 triangles, 216,276 per deck
    10th-percentile edge 1.50 mm = 0.93 px       (hero limit 6 px)
    median edge          6.32 mm = 3.93 px
    64 procedural texture nodes over 8 materials (hero floor 6)
    0 image-texture nodes, 0 external files, 0 `Geometry->Position` links
    size CV across the 25 decks 0.234, 25 distinct topologies
    minimum ground embedment 0.0200 m            == `C.BASE_EMBED_M`
    deck_top_z departs -16.5 .. +7.5 mm from the plane it was set out to

TWO DEFECTS THIS ITEM'S OWN MACRO RENDER CAUGHT
===============================================
Both were invisible to the acceptance gate, which is the point of the render.

 1. **Every board sampled the same grain.**  `mpd_bc` was baked as the raw
    board coordinate, so all twelve boards of a deck read the same point of the
    same noise: same rings, same knots, same weathering patch.  Twelve planks
    that were one plank twelve times — the user's named failure inside a single
    object.  Fixed by `board_grain_offset()`.

 2. **The inherited hash does not avalanche.**  `build_dressing.hash01` keyed
    with a trailing small index returns a 1 % spread over twelve indices
    (measured: 0.532..0.542), so EVERY per-board draw — cup, bow, split count,
    fixing skew, colour — came back nearly identical.  Kept as
    `h01_dressing()` for the one quantity that must match build_dressing, and
    replaced everywhere else by a splitmix64 finalizer that measures 0.791.

SITES — WHY THEY ARE FROZEN IN THIS FILE
========================================
``build_dressing.marshal_post_plan()`` is the placement authority and this table
is its output, captured on 2026-07-29 with ``--replan``.  It is frozen rather
than recomputed at build time for two reasons: importing build_dressing costs
9 s and drags in build_barriers, and — the real one — a plan that moves when
somebody edits build_dressing would move the deck out from under the column, the
stair and the handrail, which are built by four agents who never meet.

ONE RECONCILIATION, AND IT IS EXACT.  The manifest records **25 posts, max gap
253.9 m**.  Today's plan returns 24 with a **338.3 m** hole between s = 1925.4
and s = 2263.7 — and 253.9 m is exactly the SECOND-largest gap in it.  So the
manifest's 25th post is the straight-infill that splits that hole, dropped by a
later edit to build_dressing.  ``--replan`` puts it back through the module's own
infill rule (midpoint of the worst gap, side by ``hash01(s, 902)``, flipped off
concrete/no-barrier, then ``_finalise_posts``) and the result is 25 posts with a
worst gap of 253.9 m: both manifest numbers, reproduced, not asserted.

Run headless:

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P world/items/marshal_post_deck.py -- --test --save \
        world/items/marshal_post_deck_test.blend

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P world/items/marshal_post_deck.py -- --selftest
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
for _p in (_WORLD, os.path.join(_ROOT, "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import world_contract as C                                   # noqa: E402

# --------------------------------------------------------------------------- ids
ITEM = "marshal_post_deck"
PFX = "MPD_"
CTX = "CTX_"                     # context objects: NOT part of this item
COLL = "ITEM_MARSHAL_POST_DECK"

# --------------------------------------------------- the manifest's own numbers
FILMED_AT_M = 6.0                # nearest_camera_m
LENS_MM = 35.0                   # lens_at_closest_mm
SENSOR_MM = 36.0
RES_X_4K = 3840
PX_PER_M = (RES_X_4K * LENS_MM / SENSOR_MM) / FILMED_AT_M     # 622.22 px/m
PX_M = 1.0 / PX_PER_M                                          # 1.607 mm
ONSCREEN_PX_4K = 560
INSTANCES = 25
HERO_EDGE_PX = 6.0               # the gate's limit for a hero item
HERO_EDGE_M = HERO_EDGE_PX * PX_M                              # 9.64 mm

BASE_EMBED_M = C.BASE_EMBED_M    # 0.020 — law 5, re-exported for dependants
SEED = 20260729

ARCHETYPE = {0: "canopy", 1: "hut", 2: "stand", 3: "platform"}

# --------------------------------------------------------------------------- #
#  SITES — build_dressing.marshal_post_plan(), frozen.  See the header.         #
#  s, lat, side  lap station / lateral / +1 left of travel                      #
#  kind          0 canopy  1 hut  2 stand  3 platform                           #
#  wx, wy, gz    world anchor ON THE GROUND (gz = C.world_ground_z there)       #
#  nx, ny        unit world lateral pointing AWAY from the track                #
#  yaw           the post's own yaw jitter, degrees                             #
#  W, D          shelter footprint; Hh its eaves height                         #
#  padw, padd    the hardstanding this post owns                                #
# --------------------------------------------------------------------------- #
SITES = [
    dict(n= 1, s=  138.541, side=-1, lat= 21.8080, kind=3, tier=2, k=  91.508449, wx=   449.5424, wy=   242.1665, gz= -0.30671, nx=+0.64278761, ny=-0.76604444, yaw= +2.6594, W=2.9429, D=2.0129, Hh=2.4063, padw=5.0125, padd=3.7946),
    dict(n= 2, s=  367.550, side=-1, lat= 70.9204, kind=3, tier=2, k= 198.574682, wx=   621.8719, wy=   451.7931, gz= -0.98721, nx=+0.97814763, ny=+0.20791156, yaw= -8.3660, W=2.1466, D=1.5287, Hh=2.1642, padw=2.9435, padd=2.3282),
    dict(n= 3, s=  464.180, side=+1, lat= 35.2682, kind=0, tier=1, k= 288.925556, wx=   488.4635, wy=   500.3967, gz= -0.63983, nx=-0.74314471, ny=-0.66913074, yaw= -8.3280, W=2.1490, D=1.5327, Hh=2.1662, padw=2.9396, padd=2.3295),
    dict(n= 4, s=  640.428, side=-1, lat= 37.8990, kind=0, tier=0, k= 139.777097, wx=   424.9047, wy=   680.3325, gz= -1.01233, nx=+0.74314471, ny=+0.66913074, yaw= +6.4073, W=3.2127, D=2.1905, Hh=2.4956, padw=5.8757, padd=4.4300),
    dict(n= 5, s=  816.675, side=+1, lat= 28.9173, kind=1, tier=0, k= 225.167705, wx=   276.4362, wy=   794.1456, gz= -1.51828, nx=-0.97029567, ny=-0.24192212, yaw= -6.8885, W=2.2529, D=1.5963, Hh=2.1971, padw=3.1773, padd=2.5007),
    dict(n= 6, s=  897.265, side=+1, lat= 19.9079, kind=2, tier=3, k= 395.615479, wx=   265.6816, wy=   874.5209, gz= -2.65873, nx=-0.97029567, ny=-0.24192212, yaw= +6.3703, W=3.2102, D=2.1822, Hh=2.4911, padw=5.8390, padd=4.3884),
    dict(n= 7, s= 1035.794, side=+1, lat= 16.7996, kind=3, tier=3, k= 502.523356, wx=   238.4638, wy=   901.0196, gz= -3.26579, nx=+0.98480787, ny=+0.17364750, yaw= +1.1137, W=2.8223, D=1.9489, Hh=2.3749, padw=5.2707, padd=4.0204),
    dict(n= 8, s= 1202.222, side=+1, lat= 33.1236, kind=0, tier=1, k= 556.616826, wx=   283.5529, wy=   739.1034, gz=  4.62640, nx=+0.98897590, ny=+0.14807659, yaw= -1.5771, W=2.6305, D=1.8309, Hh=2.3152, padw=3.6785, padd=2.8426),
    dict(n= 9, s= 1298.904, side=+1, lat= 35.0180, kind=3, tier=1, k= 524.024809, wx=   222.5175, wy=   623.1053, gz=  5.92481, nx=+0.41717059, ny=-0.90882820, yaw= -1.2046, W=2.6635, D=1.8459, Hh=2.3227, padw=4.2264, padd=3.2450),
    dict(n=10, s= 1482.717, side=+1, lat= 35.6935, kind=0, tier=0, k= 216.694023, wx=    36.0445, wy=   580.0459, gz=  6.30557, nx=+0.20791142, ny=-0.97814766, yaw= -6.4601, W=2.2851, D=1.6134, Hh=2.2072, padw=3.2523, padd=2.5503),
    dict(n=11, s= 1603.577, side=-1, lat= 34.9150, kind=0, tier=0, k= 304.366640, wx=  -108.3901, wy=   595.1183, gz=  6.71978, nx=-0.76416164, ny=+0.64502480, yaw= -7.2211, W=2.2277, D=1.5812, Hh=2.1892, padw=3.1415, padd=2.4771),
    dict(n=12, s= 1772.962, side=+1, lat= 34.9396, kind=0, tier=2, k= 491.364562, wx=  -211.7920, wy=   469.0685, gz=  7.60229, nx=+0.41009584, ny=-0.91204243, yaw= +1.8257, W=2.8814, D=1.9820, Hh=2.3913, padw=4.8541, padd=3.6975),
    dict(n=13, s= 1851.213, side=-1, lat= 49.0970, kind=0, tier=2, k= 237.072566, wx=  -319.0133, wy=   476.0213, gz=  7.05320, nx=-0.78801027, ny=+0.61566209, yaw= -8.6904, W=2.1219, D=1.5144, Hh=2.1574, padw=2.8900, padd=2.2919),
    dict(n=14, s= 1867.894, side=-1, lat= 49.1090, kind=1, tier=2, k= 252.619349, wx=  -325.4176, wy=   468.5475, gz=  7.01251, nx=-0.69506696, ny=+0.71894500, yaw= -2.4662, W=2.5708, D=1.7887, Hh=2.2945, padw=3.9788, padd=3.0694),
    dict(n=15, s= 1925.372, side=+1, lat= 35.2173, kind=3, tier=2, k= 877.345166, wx=  -327.9918, wy=   373.0229, gz=  7.13284, nx=+0.37460572, ny=-0.92718421, yaw= -0.9869, W=2.6691, D=1.8508, Hh=2.3279, padw=4.2754, padd=3.2873),
    dict(n=16, s= 2094.523, side=+1, lat= 33.3677, kind=3, tier=1, k= 388.033096, wx=  -485.5190, wy=   311.3728, gz=  4.54824, nx=+0.37460572, ny=-0.92718421, yaw= +0.0305, W=2.7514, D=1.9020, Hh=2.3509, padw=4.4892, padd=3.4371),
    dict(n=17, s= 2263.674, side=-1, lat= 83.7589, kind=3, tier=1, k= 383.169556, wx=  -698.0450, wy=   265.3903, gz=  3.10848, nx=-0.93705680, ny=+0.34917697, yaw= +4.0761, W=3.0398, D=2.0786, Hh=2.4395, padw=5.2810, padd=4.0038),
    dict(n=18, s= 2443.927, side=+1, lat= 37.1430, kind=3, tier=2, k= 519.084878, wx=  -569.4586, wy=    80.0350, gz=  3.17949, nx=+0.90333590, ny=+0.42893385, yaw= +7.0536, W=3.2594, D=2.2130, Hh=2.5064, padw=6.0144, padd=4.5163),
    dict(n=19, s= 2642.711, side=-1, lat= 37.0032, kind=3, tier=3, k= 329.258452, wx=  -551.1723, wy=  -131.3377, gz= -1.68888, nx=-0.90333590, ny=-0.42893385, yaw= -8.3987, W=2.1439, D=1.5277, Hh=2.1640, padw=3.0026, padd=2.3766),
    dict(n=20, s= 2734.548, side=-1, lat= 43.9085, kind=2, tier=2, k= 696.055366, wx=  -488.5205, wy=  -230.9363, gz= -4.38855, nx=-0.43435078, ny=-0.90074381, yaw= +4.2031, W=3.0531, D=2.0815, Hh=2.4437, padw=5.3076, padd=4.0021),
    dict(n=21, s= 2889.662, side=-1, lat= 36.1155, kind=3, tier=0, k= 829.563135, wx=  -311.4252, wy=  -233.4310, gz= -3.19908, nx=+0.16332576, ny=-0.98657220, yaw= +2.5546, W=2.9340, D=2.0177, Hh=2.4067, padw=5.0070, padd=3.8091),
    dict(n=22, s= 2919.380, side=+1, lat= 35.9070, kind=0, tier=0, k= 442.831658, wx=  -285.1112, wy=  -159.6907, gz= -2.84903, nx=+0.07457571, ny=+0.99721535, yaw= -8.6742, W=2.1374, D=1.5233, Hh=2.1611, padw=2.9023, padd=2.2965),
    dict(n=23, s= 3101.664, side=+1, lat= 37.7450, kind=1, tier=1, k=  32.636987, wx=  -130.7263, wy=  -166.2874, gz= -1.13343, nx=-0.54057642, ny=+0.84129492, yaw= -6.5429, W=2.2883, D=1.6082, Hh=2.2044, padw=3.2798, padd=2.5569),
    dict(n=24, s= 3355.523, side=-1, lat= 22.0023, kind=0, tier=0, k= 506.349115, wx=    98.8041, wy=   -52.3901, gz= -0.30219, nx=+0.64278797, ny=-0.76604414, yaw= +2.6316, W=2.9389, D=2.0211, Hh=2.4082, padw=5.0266, padd=3.8263),
    dict(n=25, s= 3604.309, side=-1, lat= 21.1459, kind=1, tier=2, k= 470.289397, wx=   288.8346, wy=   108.1826, gz= -0.28937, nx=+0.64278797, ny=-0.76604414, yaw= -3.7729, W=2.4783, D=1.7360, Hh=2.2682, padw=3.7241, padd=2.8937),
]

# --------------------------------------------------------------------------- #
#  PALETTE — linear reflectances.  Measured-plausible, not picked in sRGB.      #
# --------------------------------------------------------------------------- #
P = dict(
    # softwood, from fresh-sawn through to fully silvered
    wood_fresh=(0.2480, 0.1810, 0.0980),
    wood_mid=(0.1720, 0.1230, 0.0680),
    wood_late=(0.0980, 0.0680, 0.0380),      # latewood band, darker and harder
    wood_silver=(0.1560, 0.1490, 0.1350),    # UV-bleached grey
    wood_silver_d=(0.0930, 0.0890, 0.0820),
    wood_wet=(0.0560, 0.0420, 0.0250),
    wood_knot=(0.0620, 0.0400, 0.0190),
    wood_end=(0.1350, 0.0970, 0.0530),
    tanalith=(0.1080, 0.1240, 0.0790),       # the green of pressure treatment
    # plywood
    ply_face=(0.2760, 0.2070, 0.1160),
    ply_core=(0.2050, 0.1580, 0.0930),
    ply_glue=(0.0850, 0.0640, 0.0430),
    # zinc
    galv=(0.4280, 0.4390, 0.4460),
    galv_dull=(0.2650, 0.2680, 0.2710),
    galv_white=(0.5200, 0.5250, 0.5150),     # white rust
    steel=(0.1900, 0.1930, 0.1980),
    rust=(0.1150, 0.0470, 0.0180),
    rust_pale=(0.2100, 0.1050, 0.0480),
    # paint
    conc=(0.2350, 0.2320, 0.2230),
    conc_wet=(0.1180, 0.1160, 0.1110),
    sand=(0.2650, 0.2280, 0.1620),           # polypropylene sack, sun-faded
    sand_new=(0.3450, 0.3200, 0.2450),
    poly_yellow=(0.4100, 0.2900, 0.0420),
    poly_blue=(0.0420, 0.0880, 0.2050),
    poly_green=(0.0480, 0.1150, 0.0520),
    poly_red=(0.2100, 0.0330, 0.0250),
    tarp_blue=(0.0520, 0.0980, 0.1900),
    tarp_green=(0.0620, 0.1000, 0.0500),
    grit=(0.0680, 0.0640, 0.0590),
)

# the six invented brand colours this family borrows for painted steelwork.
# NO LETTERING is carried by this item; these are paint tins, not logos.
FRAME_PAINT = [
    (0.0290, 0.0620, 0.1180),    # deep petrol blue
    (0.0640, 0.0850, 0.0470),    # olive
    (0.1450, 0.0290, 0.0230),    # oxide red
    (0.0350, 0.0370, 0.0410),    # graphite
    (0.2050, 0.1560, 0.0420),    # ochre
    (0.0400, 0.0930, 0.0850),    # teal
]

# --------------------------------------------------------------------------- #
#  MATERIAL SLOTS — the same order on every object, so material_index is        #
#  meaningful across all 25 decks.                                              #
# --------------------------------------------------------------------------- #
M_TIMBER, M_PLY, M_GALV, M_PAINT, M_CONC, M_WOVEN, M_POLY, M_TARP = range(8)
MAT_ORDER = ["Timber", "Ply", "Galv", "Paint", "Concrete", "Woven", "Poly", "Tarp"]

# per-vertex attributes every material reads.  A dependant emitting geometry
# into these materials must write all of them; `Acc` defaults them.
ATTR_F = ("mpd_wear", "mpd_age", "mpd_wet", "mpd_moss", "mpd_rust",
          "mpd_end", "mpd_paint", "mpd_id", "mpd_ao", "mpd_grit")
ATTR_V = ("mpd_bc",)             # part-local coordinate: x ALONG the grain
ATTR_C = ("mpd_tint",)
ATTRS = ATTR_F + ATTR_V + ATTR_C

VERBOSE = True


def log(*a):
    if VERBOSE:
        print("[MPD]", *a)
        sys.stdout.flush()


# ================================================================================
#  1.  NUMERIC KIT — deterministic, seedable, identical on every machine
# ================================================================================

_M64 = 0xFFFFFFFFFFFFFFFF


def h01_dressing(*keys):
    """build_dressing.hash01, byte for byte.

    KEPT, and used for EXACTLY ONE draw: the shelter leg radius, which
    `column_sockets()` promises is the leg build_dressing actually built.  A
    shared quantity has to come from the shared function.

    It is not used for anything else, because it does not avalanche.  Measured:
    `hash01(91.508449, 4530, j)` for j = 0..11 returns 0.532, 0.532, 0.533,
    0.537, 0.538, 0.539, 0.538, 0.536, 0.536, 0.537, 0.536, 0.542 -- a spread of
    1 % across twelve indices.  Every per-board draw keyed that way (cup, bow,
    split count, fixing skew, colour) came back nearly identical, so a deck of
    twelve boards was twelve copies of one board with different lengths.  That
    is the user's named failure at the scale of a single object, and it survived
    two rounds of looking at renders because the boards were *almost* different.
    """
    h = 0xCBF29CE484222325
    for k in keys:
        if isinstance(k, str):
            for ch in k:
                h = ((h ^ ord(ch)) * 0x100000001B3) & _M64
            continue
        v = int(round(float(k) * 1024.0)) & _M64
        h = ((h ^ v) * 0x100000001B3) & _M64
        h = h ^ (h >> 29)
    return (h & 0xFFFFFFFF) / 4294967296.0


def h01(*keys):
    """Deterministic float in [0,1), and it actually avalanches.

    splitmix64's finalizer per key.  Same spread test as above returns
    0.043 .. 0.982 over the twelve indices.  `selftest` measures it.
    """
    h = 0x9E3779B97F4A7C15
    for k in keys:
        if isinstance(k, str):
            v = 0
            for ch in k:
                v = (v * 131 + ord(ch)) & _M64
        else:
            v = int(round(float(k) * 4096.0)) & _M64
        z = (h ^ v) & _M64
        z = (z + 0x9E3779B97F4A7C15) & _M64
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & _M64
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & _M64
        h = z ^ (z >> 31)
    return (h >> 11) / 9007199254740992.0


def rnd(lo, hi, *keys):
    return lo + (hi - lo) * h01(*keys)


def rint(lo, hi, *keys):
    return int(lo + math.floor(h01(*keys) * (hi - lo + 1 - 1e-9)))


def chance(p, *keys):
    return h01(*keys) < p


def pick(seq, *keys):
    return seq[int(h01(*keys) * len(seq)) % len(seq)]


def _hn(x, seed):
    x = np.asarray(x, np.int64)
    h = (x * np.int64(1597334677)) ^ np.int64(int(seed) * 2654435761)
    h = (h ^ (h >> np.int64(15))) * np.int64(2246822519)
    h = (h ^ (h >> np.int64(13))) * np.int64(3266489917)
    return ((h ^ (h >> np.int64(16))) & np.int64(0x7FFFFFFF)).astype(np.float64) / 2147483647.0


def _hn2(x, y, seed):
    x = np.asarray(x, np.int64)
    y = np.asarray(y, np.int64)
    h = (x * np.int64(1597334677)) ^ (y * np.int64(3812015801)) ^ np.int64(int(seed) * 2654435761)
    h = (h ^ (h >> np.int64(15))) * np.int64(2246822519)
    h = (h ^ (h >> np.int64(13))) * np.int64(3266489917)
    return ((h ^ (h >> np.int64(16))) & np.int64(0x7FFFFFFF)).astype(np.float64) / 2147483647.0


def _s5(t):
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)


def n1(x, seed=0):
    """1-D value noise, C2."""
    x = np.asarray(x, float)
    i = np.floor(x)
    f = _s5(x - i)
    i = i.astype(np.int64)
    return _hn(i, seed) * (1 - f) + _hn(i + 1, seed) * f


def n2(x, y, seed=0):
    """2-D value noise, C2."""
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    ix = np.floor(x)
    iy = np.floor(y)
    fx = _s5(x - ix)
    fy = _s5(y - iy)
    ix = ix.astype(np.int64)
    iy = iy.astype(np.int64)
    a = _hn2(ix, iy, seed)
    b = _hn2(ix + 1, iy, seed)
    c = _hn2(ix, iy + 1, seed)
    d = _hn2(ix + 1, iy + 1, seed)
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def fbm1(x, seed=0, oct=4, lac=2.03, gain=0.5):
    t = np.zeros_like(np.asarray(x, float))
    a, f, nrm = 1.0, 1.0, 0.0
    for o in range(oct):
        t = t + a * n1(np.asarray(x, float) * f, seed * 71 + o * 13)
        nrm += a
        a *= gain
        f *= lac
    return t / nrm


def fbm2(x, y, seed=0, oct=4, lac=2.03, gain=0.5):
    t = np.zeros(np.broadcast(np.asarray(x, float), np.asarray(y, float)).shape)
    a, f, nrm = 1.0, 1.0, 0.0
    for o in range(oct):
        t = t + a * n2(np.asarray(x, float) * f, np.asarray(y, float) * f,
                       seed * 71 + o * 13)
        nrm += a
        a *= gain
        f *= lac
    return t / nrm


def sstep(a, b, x):
    t = np.clip((np.asarray(x, float) - a) / max(1e-12, (b - a)), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def unit(v):
    v = np.asarray(v, float)
    n = np.linalg.norm(v)
    return v / n if n > 1e-12 else np.array([1.0, 0.0, 0.0])


def seg_dist2(px, py, ax, ay, bx, by):
    """squared distance from points (px,py) to the segment a->b.  Vectorised."""
    vx, vy = bx - ax, by - ay
    L2 = vx * vx + vy * vy
    if L2 < 1e-12:
        return (px - ax) ** 2 + (py - ay) ** 2
    t = np.clip(((px - ax) * vx + (py - ay) * vy) / L2, 0.0, 1.0)
    dx = px - (ax + t * vx)
    dy = py - (ay + t * vy)
    return dx * dx + dy * dy


# ================================================================================
#  2.  MESH ACCUMULATOR
# ================================================================================

def place(ob, R, O):
    """Put an object at (R, O) and PROVE it landed there.

    `ob.matrix_world = <4x4>` on a freshly created object does not stick: the
    object's loc/rot/scale stay at the identity and the next depsgraph
    evaluation overwrites the world matrix with them.  All 25 decks were built
    correctly and left at the world origin, 900 m from the camera pointed at
    their sites, and the macro render came back black — a defect that looks
    exactly like a lighting bug and is not one.

    So: decompose explicitly into the channels the depsgraph actually reads, and
    then MEASURE the result rather than trusting it.  An object that did not
    land where it was told raises here instead of rendering as an empty frame.
    """
    from mathutils import Matrix
    q = Matrix([[float(R[0][0]), float(R[0][1]), float(R[0][2])],
                [float(R[1][0]), float(R[1][1]), float(R[1][2])],
                [float(R[2][0]), float(R[2][1]), float(R[2][2])]]).to_quaternion()
    ob.rotation_mode = "QUATERNION"
    ob.rotation_quaternion = q
    ob.location = (float(O[0]), float(O[1]), float(O[2]))
    ob.scale = (1.0, 1.0, 1.0)
    # `matrix_world` is a CACHE the depsgraph fills; reading it straight after a
    # write returns the stale value and proves nothing.  `matrix_basis` is
    # derived from loc/rot/scale on read, so it is what to check here — and
    # `verify_placement()` re-checks matrix_world after a view-layer update,
    # which is the number that actually reaches the renderer.
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
    return ob


class Acc(object):
    """Vertex/face accumulator with the item's per-vertex attribute set.

    One Acc per DECK, so a deck is one object and the gate's per-instance
    statistics are genuinely per instance rather than per fragment.
    """

    def __init__(self, name):
        self.name = name
        self._V, self._Q, self._T, self._mq, self._mt = [], [], [], [], []
        self._A = {a: [] for a in ATTR_F}
        self._bc, self._tint = [], []
        self.n = 0
        self.parts = 0

    # ---------------------------------------------------------------- adding
    def add(self, V, quads=None, tris=None, mat=0, bc=None, tint=None, **attr):
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
        if tris is not None and len(tris):
            t = np.asarray(tris, np.int64).reshape(-1, 3) + base
            self._T.append(t)
            self._mt.append(np.full(t.shape[0], mat, np.int32))
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
                b.reshape(-1, 3) if b.size > 3 else np.broadcast_to(b.reshape(1, 3), (m, 3))
            ).astype(np.float32))
        if tint is None:
            self._tint.append(np.ones((m, 3), np.float32))
        else:
            t = np.asarray(tint, np.float32)
            self._tint.append(np.ascontiguousarray(
                t.reshape(-1, 3) if t.size > 3 else np.broadcast_to(t.reshape(1, 3), (m, 3))
            ).astype(np.float32))
        self.n += m
        self.parts += 1
        return base

    # -------------------------------------------------------------- geometry
    def solid(self, V, quads=None, tris=None, **kw):
        """Add a CLOSED solid, orienting every face outward by signed volume.

        Winding is the single most tedious bug class in generated geometry and a
        flipped face at a 12.5 deg sun reads as a black hole in the frame.  This
        settles it once for every primitive in the file instead of per call
        site: compute the solid's signed volume from its own faces and, if it
        came out negative, reverse them all.
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

    # ----------------------------------------------------------------- output
    def build(self, coll, mats, R, O, name=None):
        V = np.concatenate(self._V) if self._V else np.zeros((0, 3))
        Q = np.concatenate(self._Q) if self._Q else np.zeros((0, 4), np.int64)
        T = np.concatenate(self._T) if self._T else np.zeros((0, 3), np.int64)
        mq = np.concatenate(self._mq) if self._mq else np.zeros(0, np.int32)
        mt = np.concatenate(self._mt) if self._mt else np.zeros(0, np.int32)
        nv, nq, nt = V.shape[0], Q.shape[0], T.shape[0]
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
        me.update(calc_edges=True)
        for a in ATTR_F:
            at = me.attributes.new(a, "FLOAT", "POINT")
            at.data.foreach_set("value", np.concatenate(self._A[a]))
        bc = me.attributes.new("mpd_bc", "FLOAT_VECTOR", "POINT")
        bc.data.foreach_set("vector", np.concatenate(self._bc).ravel())
        tn = me.attributes.new("mpd_tint", "FLOAT_COLOR", "POINT")
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


def extrude(acc, PTS, mat=0, caps=True, bc=None, cap_over=None, **kw):
    """PTS: (n, m, 3) closed-section extrusion -> one closed solid.

    The end caps get their OWN copies of the ring vertices so they can carry
    different attributes from the sides.  That is not tidiness: the end of a
    sawn board is END GRAIN, a different material history from its face — it
    drinks water, it greys first and it checks — and a shader cannot tell the
    two apart if they share vertices.

    R2-179 — BOTH CAPS WERE WOUND INWARD.  The side quads from `_grid_quads`
    have normal `t x e` (ring tangent cross extrude direction), outward for a
    ring wound CCW about `e`.  For that ring the START cap's outward normal is
    `-e` and the END cap's is `+e`, so it is the START cap that must be
    REVERSED — this had it the other way round, so every solid in the file was
    a correct tube with both lids facing into itself.  `Acc.solid` could not
    see it: four outward sides and two inward caps integrate to +V/3, positive,
    so no flip. On a 21 mm deck board the caps are 98 % of the area, which is
    how 1.267 m² of this item ended up presenting its underside to the lens.
    Identical defect and identical fix in `timing_stand.py`.
    """
    PTS = np.asarray(PTS, float)
    n, m = PTS.shape[0], PTS.shape[1]
    blocks = [PTS.reshape(-1, 3)]
    Q = _grid_quads(n, m, close_m=True)
    T = None
    if caps:
        c0 = PTS[0].mean(axis=0)
        c1 = PTS[-1].mean(axis=0)
        blocks += [PTS[0], c0[None, :], PTS[-1], c1[None, :]]
        b0 = n * m
        b1 = b0 + m + 1
        T = np.concatenate([_fan(b0 + m, np.arange(b0, b0 + m), reverse=True),
                            _fan(b1 + m, np.arange(b1, b1 + m))])
    V = np.concatenate(blocks)

    def _pad(a, capval=None):
        a = np.asarray(a)
        if a.ndim == 0 or a.shape[0] != n * m:
            return a
        if capval is None:
            c0v, c1v = a[:m], a[-m:]
        else:
            c0v = np.broadcast_to(np.asarray(capval, a.dtype), a[:m].shape)
            c1v = c0v
        return np.concatenate([a, c0v, c0v[:1], c1v, c1v[:1]])

    if caps:
        cap_over = cap_over or {}
        if bc is not None:
            bc = _pad(np.asarray(bc, np.float32).reshape(-1, 3), cap_over.get("bc"))
        for kk in list(kw):
            kw[kk] = _pad(kw[kk], cap_over.get(kk))
    return acc.solid(V, quads=Q, tris=T, mat=mat, bc=bc, **kw)


# ---------------------------------------------------------------- R2-179 ----
#  THE GUARD FOR THE CLASS ABOVE, LIVING BESIDE WHAT IT GUARDS.
#
#  Two instruments existed and both were blind:
#
#    `Acc.solid` decides by SIGNED VOLUME, and four correct sides plus two
#    inverted lids integrate to +V/3 -- positive, so no flip, on a solid a
#    third of whose area is wrong.  On a 21 mm deck board the lids are 98 % of
#    the area and the number stays cheerfully positive.
#
#    `tools/winding_audit.py` decides from the sign of a PIECE's volume, and
#    `extrude` gives each cap its own copy of the ring vertices -- so a lid is
#    a separate, zero-thickness, VOLUMELESS piece, classed `undecidable`, and
#    `--fix` correctly abstains.
#
#  So this check is neither.  Topology plus a facing law, needing no piece to
#  enclose anything:
#
#    CONSISTENT  every undirected edge used exactly twice, once each way.
#    OUTWARD     divergence-theorem volume about the mesh's OWN centroid --
#                not the world origin, which is what let `box`'s reversed
#                bottom quad hide whenever it sat on z = 0.
#    LIDS        of the horizontal faces the HIGHEST faces up and the LOWEST
#                faces down: the sentence the defect violated, and the one a
#                reader can check against a rendered picture.
def winding_stats(V, Q, T):
    """-> dict. Pure arithmetic on arrays; no bpy, no scene, no accumulator."""
    V = np.asarray(V, float)
    Q = np.asarray(Q, np.int64).reshape(-1, 4)
    T = np.asarray(T, np.int64).reshape(-1, 3)
    tris = []
    if len(Q):
        tris.append(Q[:, (0, 1, 2)])
        tris.append(Q[:, (0, 2, 3)])
    if len(T):
        tris.append(T)
    F = np.concatenate(tris) if tris else np.zeros((0, 3), np.int64)
    if not len(F):
        return {"faces": 0, "consistent": False, "volume": 0.0,
                "measured": False}
    # Topology ON WELDED INDICES.  `extrude` gives every cap its own copy of
    # the ring vertices on purpose, so a correct solid out of this file is
    # geometrically closed and topologically split; counting raw indices calls
    # every primitive inconsistent, which is measurably what the first version
    # of this check did.  Weld by POSITION and the question becomes the one
    # that was meant: does the SURFACE close, whatever the vertex table says.
    _, wid = np.unique(np.round(V, 7), axis=0, return_inverse=True)
    wid = np.asarray(wid).ravel()
    W = wid[F]
    E = np.concatenate([W[:, (0, 1)], W[:, (1, 2)], W[:, (2, 0)]])
    E = E[E[:, 0] != E[:, 1]]                        # collapsed by the weld
    nw = int(wid.max()) + 1 if len(wid) else 1
    key = E[:, 0] * nw + E[:, 1]
    rev = E[:, 1] * nw + E[:, 0]
    uk, cnt = np.unique(key, return_counts=True)
    dup = int((cnt > 1).sum())
    unpaired = int((~np.isin(rev, uk)).sum())
    P = V[F]
    nrm = np.cross(P[:, 1] - P[:, 0], P[:, 2] - P[:, 0])
    area = 0.5 * np.linalg.norm(nrm, axis=1)
    live = area > 1e-14
    c = V.mean(0)
    vol = float(np.einsum("ij,ij->i", P[:, 0] - c,
                          np.cross(P[:, 1] - c, P[:, 2] - c)).sum()) / 6.0
    u = nrm / np.maximum(np.linalg.norm(nrm, axis=1), 1e-30)[:, None]
    zc = P[:, :, 2].mean(1)
    flat = live & (np.abs(u[:, 2]) > 0.99)
    lids_ok, top_nz, bot_nz = None, float("nan"), float("nan")
    if flat.any():
        zf = zc[flat]
        hi = zf >= zf.max() - 1e-6
        lo = zf <= zf.min() + 1e-6
        top_nz = float(u[flat][hi][:, 2].mean())
        bot_nz = float(u[flat][lo][:, 2].mean())
        lids_ok = bool(top_nz > 0.0 and bot_nz < 0.0)
    return {"faces": int(live.sum()), "area": float(area[live].sum()),
            "duplicate_directed_edges": dup, "unpaired_edges": unpaired,
            "consistent": bool(dup == 0 and unpaired == 0),
            "volume": vol, "outward": bool(vol > 0.0),
            "flat_faces": int(flat.sum()), "top_nz": top_nz,
            "bottom_nz": bot_nz, "lids_ok": lids_ok, "measured": True}


def _acc_arrays(acc):
    """V, Q, T out of an accumulator without caring which one it is."""
    V = np.concatenate(acc._V) if acc._V else np.zeros((0, 3))
    Q = np.concatenate(acc._Q) if acc._Q else np.zeros((0, 4), np.int64)
    T = np.concatenate(acc._T) if acc._T else np.zeros((0, 3), np.int64)
    return V, Q, T


def _slab_lids_inverted(acc, ctr, ex, ey, ez):
    """THE NEGATIVE CONTROL, MANUFACTURED FROM LIVE SOURCE EVERY RUN.

    The historical wiring, byte for byte: same ring, same side quads, and the
    cap fans the way `extrude` had them until R2-179 -- start cap not
    reversed, end cap reversed.  It goes through `acc.add`, NOT `acc.solid`,
    because `solid` is one of the two instruments this control exists to prove
    blind, and letting it re-orient the control would be the bug again.

    R2-072: a control that NAMES a broken artefact dies the day that artefact
    is repaired, and it dies into a cheerful pass.  This one is manufactured
    from the same `_grid_quads` and `_fan` the fixed code uses, so it can only
    stop failing if those change underneath it -- in which case it SHOULD.
    """
    ctr, ex, ey, ez = (np.asarray(v, float) for v in (ctr, ex, ey, ez))
    sect = rect(2.0, 2.0, 0.0)
    m = sect.shape[0]
    PTS = np.empty((2, m, 3))
    for i, t in enumerate((-1.0, 1.0)):
        PTS[i] = (ctr + t * ez)[None, :] + sect[:, 0:1] * ex[None, :] \
            + sect[:, 1:2] * ey[None, :]
    n = PTS.shape[0]
    Q = _grid_quads(n, m, close_m=True)
    c0, c1 = PTS[0].mean(axis=0), PTS[-1].mean(axis=0)
    V = np.concatenate([PTS.reshape(-1, 3), PTS[0], c0[None, :],
                        PTS[-1], c1[None, :]])
    b0 = n * m
    b1 = b0 + m + 1
    T = np.concatenate([_fan(b0 + m, np.arange(b0, b0 + m)),
                        _fan(b1 + m, np.arange(b1, b1 + m), reverse=True)])
    return acc.add(V, quads=Q, tris=T, mat=0)


def winding_selftest(chk):
    """Every primitive this file owns, plus both controls, on live source."""
    prims = (
        ("obox, deck-board shaped", lambda a: obox(
            a, (0, 0, 1.2), (0.7, 0, 0), (0, 0.075, 0), (0, 0, 0.0105),
            chamfer=0.0012)),
        ("obox, unchamfered", lambda a: obox(
            a, (0, 0, 0.5), (0.3, 0, 0), (0, 0.2, 0), (0, 0, 0.1))),
        ("box", lambda a: box(a, (-1, -1, 0.61), (1, 1, 0.66))),
        ("tube", lambda a: tube(a, (0, 0, 0), (0, 0, 1), 0.05)),
        ("slab_grid, deck sheet", lambda a: slab_grid(
            a, -0.6, 0.6, -0.5, 0.5, lambda X, Y: np.full_like(X, 1.2),
            0.018, step=0.05)),
    )
    for nm, fn in prims:
        a = Acc("wchk")
        fn(a)
        s = winding_stats(*_acc_arrays(a))
        ok = s["consistent"] and s["outward"] and (s["lids_ok"] is not False)
        chk("winding: %s" % nm, ok,
            "%d faces, %d bad edges, vol %+.6g, top_nz %+.3f, bottom_nz %+.3f"
            % (s["faces"], s["duplicate_directed_edges"] + s["unpaired_edges"],
               s["volume"], s["top_nz"], s["bottom_nz"]))

    # THE CONTROL THAT WOULD HAVE FOUND THE THIRD SITE ON DAY ONE.
    # `Acc.solid` integrates its signed volume about the WORLD ORIGIN, so on a
    # mesh that is not consistently wound the answer depends on WHERE THE
    # PIECE STANDS -- and `slab_grid` was not consistently wound, so 24 of 25
    # hut floors came out right way up by luck and `MPD_Deck_05_hut` at
    # z = -1.03 did not. Build the same slab at five heights and require the
    # same verdict: a primitive whose orientation is a function of its
    # position is broken even where it happens to be correct.
    for zz in (-5.0, -1.03, 0.0, 1.2, 40.0):
        a = Acc("wchk_z")
        slab_grid(a, -0.6, 0.6, -0.5, 0.5, lambda X, Y, _z=zz:
                  np.full_like(X, _z), 0.018, step=0.05)
        s = winding_stats(*_acc_arrays(a))
        chk("winding: slab_grid at z %+.2f" % zz,
            s["consistent"] and s["outward"] and s["lids_ok"] is True,
            "vol %+.6g, top_nz %+.3f, bottom_nz %+.3f"
            % (s["volume"], s["top_nz"], s["bottom_nz"]))

    a = Acc("wctl_ok")
    obox(a, (0, 0, 1.2), (0.7, 0, 0), (0, 0.075, 0), (0, 0, 0.0105))
    good = winding_stats(*_acc_arrays(a))
    chk("CONTROL a correctly built board is SILENT",
        good["consistent"] and good["outward"] and good["lids_ok"] is True,
        "top_nz %+.3f, bottom_nz %+.3f, vol %+.6g"
        % (good["top_nz"], good["bottom_nz"], good["volume"]))

    a = Acc("wctl_bad")
    _slab_lids_inverted(a, (0, 0, 1.2), (0.7, 0, 0), (0, 0.075, 0),
                        (0, 0, 0.0105))
    bad = winding_stats(*_acc_arrays(a))
    # It must fail, AND it must fail as the DEFECT: the board's top face
    # pointing at the ground with the sheet below it pointing up.  Asserting
    # only "not ok" would pass on a control that broke some other way.
    chk("CONTROL the pre-R2-179 board is NAMED, and named correctly",
        (not bad["consistent"]) and bad["lids_ok"] is False
        and bad["top_nz"] < -0.99 and bad["bottom_nz"] > 0.99,
        "top_nz %+.3f (want -1), bottom_nz %+.3f (want +1), %d bad edges"
        % (bad["top_nz"], bad["bottom_nz"],
           bad["duplicate_directed_edges"] + bad["unpaired_edges"]))


def stations(L, base, refine=(), rad=0.017, fine=0.0038, ends=0.055):
    """positions along [-L/2, +L/2], denser at the ends and near `refine`.

    Uniform sampling is the wrong answer twice over: it wastes triangles down
    the middle of a board where nothing happens, and it is too coarse exactly
    where everything does — the sawn end, the check that opens there, and the
    8 mm dish around a countersunk screw, which at 622 px/m is 5 px across and
    has to read as a dish rather than a dot.
    """
    a = [np.linspace(-L * 0.5, L * 0.5, max(2, int(round(L / base)) + 1))]
    for u in refine:
        a.append(np.arange(u - rad, u + rad + 1e-9, fine))
    a.append(np.linspace(-L * 0.5, -L * 0.5 + ends, 13))
    a.append(np.linspace(L * 0.5 - ends, L * 0.5, 13))
    x = np.clip(np.unique(np.concatenate(a)), -L * 0.5, L * 0.5)
    keep = [x[0]]
    for v in x[1:]:
        if v - keep[-1] > 0.0007:
            keep.append(v)
    keep[-1] = L * 0.5
    return np.array(keep)


def frames_along(path, up_hint=(0.0, 0.0, 1.0)):
    """Parallel-transport frames along a polyline.  -> (T, N, B) each (n,3)."""
    Pp = np.asarray(path, float)
    n = Pp.shape[0]
    T = np.zeros((n, 3))
    T[:-1] = Pp[1:] - Pp[:-1]
    T[-1] = T[-2]
    T[1:-1] = Pp[2:] - Pp[:-2]
    L = np.linalg.norm(T, axis=1, keepdims=True)
    T = T / np.maximum(L, 1e-12)
    N = np.zeros((n, 3))
    up = unit(up_hint)
    r = np.cross(up, T[0])
    if np.linalg.norm(r) < 1e-6:
        r = np.cross(np.array([1.0, 0.0, 0.0]), T[0])
    N[0] = unit(r)
    for i in range(1, n):
        v = N[i - 1] - T[i] * float(np.dot(N[i - 1], T[i]))
        if np.linalg.norm(v) < 1e-9:
            v = np.cross(up, T[i])
        N[i] = unit(v)
    B = np.cross(T, N)
    return T, N, B


def sweep(acc, path, sect, mat=0, closed=False, scale=None, roll=None,
          bc_mode="path", **kw):
    """Sweep a closed 2-D section (m,2) along a 3-D polyline.

    Used for tube, hoop-iron end band, hose coil, rope, twisted cross rod.
    `scale` (n,) or (n,2) tapers it; `roll` (n,) radians twists it.
    """
    Pp = np.asarray(path, float)
    S = np.asarray(sect, float)
    n, m = Pp.shape[0], S.shape[0]
    T, N, B = frames_along(Pp)
    a = np.broadcast_to(S[None, :, 0], (n, m)).copy()
    b = np.broadcast_to(S[None, :, 1], (n, m)).copy()
    if roll is not None:
        r = np.asarray(roll, float).reshape(n, 1)
        ca, sa = np.cos(r), np.sin(r)
        a, b = a * ca - b * sa, a * sa + b * ca
    if scale is not None:
        sc = np.asarray(scale, float)
        if sc.ndim == 1:
            a = a * sc[:, None]
            b = b * sc[:, None]
        else:
            a = a * sc[:, 0:1]
            b = b * sc[:, 1:2]
    PTS = (Pp[:, None, :] + a[:, :, None] * N[:, None, :]
           + b[:, :, None] * B[:, None, :])
    if closed:
        V = PTS.reshape(-1, 3)
        Q = _grid_quads(n, m, close_m=True)
        # a closed loop: stitch the last station back to the first
        i = n - 1
        j = np.arange(m)
        j1 = (j + 1) % m
        Q = np.concatenate([Q, np.stack([i * m + j, i * m + j1, j1, j], 1)])
        return acc.solid(V, quads=Q, mat=mat, **kw)
    bcv = None
    if bc_mode == "path":
        s = np.zeros(n)
        s[1:] = np.cumsum(np.linalg.norm(Pp[1:] - Pp[:-1], axis=1))
        ang = np.arctan2(S[:, 1], S[:, 0])
        rad = np.hypot(S[:, 0], S[:, 1])
        bcv = np.stack([np.broadcast_to(s[:, None], (n, m)),
                        np.broadcast_to(ang[None, :] * 0.05, (n, m)),
                        np.broadcast_to(rad[None, :], (n, m))], -1).reshape(-1, 3)
    return extrude(acc, PTS, mat=mat, caps=True, bc=bcv, **kw)


def circle(r, n=16, phase=0.0):
    a = np.arange(n) * (2.0 * math.pi / n) + phase
    return np.stack([np.cos(a) * r, np.sin(a) * r], 1)


def rect(w, h, chamfer=0.0):
    """CCW rectangle section, optionally chamfered at the corners."""
    if chamfer <= 1e-6:
        return np.array([(-w / 2, -h / 2), (w / 2, -h / 2),
                         (w / 2, h / 2), (-w / 2, h / 2)])
    c = chamfer
    return np.array([
        (-w / 2 + c, -h / 2), (w / 2 - c, -h / 2), (w / 2, -h / 2 + c),
        (w / 2, h / 2 - c), (w / 2 - c, h / 2), (-w / 2 + c, h / 2),
        (-w / 2, h / 2 - c), (-w / 2, -h / 2 + c)])


def tube(acc, p0, p1, r, mat=0, n=16, phase=0.0, **kw):
    p0 = np.asarray(p0, float)
    p1 = np.asarray(p1, float)
    d = p1 - p0
    L = float(np.linalg.norm(d))
    ns = max(2, int(L / 0.09) + 2)
    path = p0[None, :] + np.linspace(0, 1, ns)[:, None] * d[None, :]
    return sweep(acc, path, circle(r, n, phase), mat=mat, **kw)


def box(acc, lo, hi, mat=0, **kw):
    lo = np.asarray(lo, float)
    hi = np.asarray(hi, float)
    x0, y0, z0 = lo
    x1, y1, z1 = hi
    V = np.array([(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                  (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)])
    # R2-179, second site.  `(0, 1, 2, 3)` walks +x then +y round the BOTTOM
    # face — CCW from above, normal +z, INTO the box.  The other five were
    # right.  `Acc.solid` integrates about the WORLD ORIGIN, so this face
    # contributes `area * z0 / 3` and vanishes for a box on z = 0 — the case
    # it was eyeballed against.  Elsewhere it can invert the whole solid.
    Q = np.array([(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4),
                  (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)])
    bc = np.stack([V[:, 0] - (x0 + x1) * 0.5, V[:, 1] - (y0 + y1) * 0.5,
                   V[:, 2] - (z0 + z1) * 0.5], 1)
    return acc.solid(V, quads=Q, mat=mat, bc=bc, **kw)


def obox(acc, ctr, ex, ey, ez, mat=0, chamfer=0.0, **kw):
    """oriented box: centre + three half-extent vectors."""
    ctr = np.asarray(ctr, float)
    ex = np.asarray(ex, float)
    ey = np.asarray(ey, float)
    ez = np.asarray(ez, float)
    sect = rect(2.0, 2.0, chamfer)
    m = sect.shape[0]
    PTS = np.empty((2, m, 3))
    for i, t in enumerate((-1.0, 1.0)):
        PTS[i] = (ctr + t * ez)[None, :] + sect[:, 0:1] * ex[None, :] \
            + sect[:, 1:2] * ey[None, :]
    return extrude(acc, PTS, mat=mat, **kw)


def _icosa():
    t = (1.0 + 5.0 ** 0.5) / 2.0
    V = np.array([(-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0),
                  (0, -1, t), (0, 1, t), (0, -1, -t), (0, 1, -t),
                  (t, 0, -1), (t, 0, 1), (-t, 0, -1), (-t, 0, 1)], float)
    F = np.array([(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11),
                  (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
                  (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9),
                  (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)])
    return V / np.linalg.norm(V, axis=1, keepdims=True), F


def icosphere(sub=2):
    V, F = _icosa()
    for _ in range(sub):
        Vl = list(map(tuple, V))
        idx = {tuple(np.round(v, 9)): i for i, v in enumerate(V)}
        nf = []
        for (a, b, c) in F:
            mid = []
            for (i, j) in ((a, b), (b, c), (c, a)):
                p = (V[i] + V[j]) * 0.5
                p = p / np.linalg.norm(p)
                key = tuple(np.round(p, 9))
                if key not in idx:
                    idx[key] = len(Vl)
                    Vl.append(tuple(p))
                mid.append(idx[key])
            ab, bc, ca = mid
            nf += [(a, ab, ca), (ab, b, bc), (ca, bc, c), (ab, bc, ca)]
        V = np.array(Vl)
        F = np.array(nf)
    return V, F


# ================================================================================
#  4.  THE DECK RECORD — the placement authority for the marshal-post family
# ================================================================================

class Deck(object):
    """One marshal post's deck.  Constructed from a frozen SITE record.

    Everything a dependant needs is derived here, deterministically, from the
    site's own hash key `k` — the SAME key build_dressing drew the post's
    shelter from, through a byte-identical `h01`.  So `column_sockets()` returns
    the leg positions build_dressing actually built, not a guess at them.

    Needs numpy and world_contract only.  No bpy: five other agents have to be
    able to ask this object questions without opening Blender.
    """

    __slots__ = ("site", "n", "s", "side", "lat", "kind", "arch", "tier", "k",
                 "wx", "wy", "gz", "nx", "ny", "yaw", "W", "D", "Hh",
                 "padw", "padd", "R", "O", "Wd", "Dd", "H", "axis", "bw", "bt",
                 "gap", "tiltx", "tilty", "legr", "col_kind", "col_size",
                 "wear_amp", "age", "moss", "wet", "acc_edge", "flag_x",
                 "path", "store", "_gg", "_gx0", "_gy0", "_gstep", "boards",
                 "notch", "toe", "paint", "seed")

    def __init__(self, site):
        self.site = site
        for f in ("n", "s", "side", "lat", "kind", "tier", "k", "wx", "wy",
                  "gz", "nx", "ny", "W", "D", "Hh", "padw", "padd"):
            setattr(self, f, site[f])
        self.yaw = site["yaw"]
        self.arch = ARCHETYPE[self.kind]
        k = self.k
        self.seed = int(self.n * 7919 + 13)

        # ---- frame: +y AWAY from the track, then the post's own yaw jitter --
        ey = np.array([self.nx, self.ny, 0.0])
        ez = np.array([0.0, 0.0, 1.0])
        ex = np.cross(ey, ez)
        R0 = np.column_stack([ex, ey, ez])
        a = math.radians(self.yaw)
        ca, sa = math.cos(a), math.sin(a)
        self.R = R0 @ np.array([[ca, -sa, 0.0], [sa, ca, 0.0], [0.0, 0.0, 1.0]])
        self.O = np.array([self.wx, self.wy, self.gz])

        # ---- the leg build_dressing actually built, reproduced exactly ------
        # build_shelter: legr = rnd(0.038, 0.058, k, 207).  Same hash, same key,
        # same number.  marshal_post_column inherits it through column_sockets().
        self.legr = 0.038 + 0.020 * h01_dressing(k, 207)
        self.col_kind = "tube" if chance(0.62, k, 4101) else "box"
        self.col_size = (round(rnd(0.048, 0.052, k, 4102), 4)
                         if self.col_kind == "tube" else
                         round(pick([0.050, 0.060, 0.080], k, 4103), 4))

        # ---- deck box and height above grade --------------------------------
        if self.kind == 0:            # duckboard inside the canopy footprint
            self.Wd = self.W - rnd(0.14, 0.34, k, 4110)
            self.Dd = self.D - rnd(0.12, 0.30, k, 4111)
            self.H = rnd(0.098, 0.215, k, 4112)
            self.bw = rnd(0.138, 0.152, k, 4113)
            self.bt = rnd(0.030, 0.036, k, 4114)
            self.gap = rnd(0.011, 0.024, k, 4115)
        elif self.kind == 1:          # hut floor, laid inside the leg line
            self.Wd = self.W - 2.0 * self.legr - rnd(0.022, 0.055, k, 4110)
            self.Dd = self.D - 2.0 * self.legr - rnd(0.020, 0.050, k, 4111)
            self.H = rnd(0.295, 0.520, k, 4112)
            self.bw = 1.220                       # ply sheet width
            self.bt = 0.018
            self.gap = rnd(0.0035, 0.0080, k, 4115)
        elif self.kind == 2:          # equipment stand: bar grating on RHS
            self.Wd = self.W * rnd(0.62, 0.80, k, 4110)
            self.Dd = self.D * rnd(0.52, 0.72, k, 4111)
            self.H = rnd(0.118, 0.262, k, 4112)
            self.bw = 0.0300                      # load bar depth
            self.bt = 0.0050                      # load bar thickness
            self.gap = rnd(0.026, 0.032, k, 4115)  # clear between load bars
        else:                         # scaffold platform
            self.Wd = self.W - 2.0 * 0.0483 - rnd(0.012, 0.030, k, 4110)
            self.Dd = self.D - 2.0 * 0.0483 - rnd(0.010, 0.026, k, 4111)
            self.H = rnd(0.735, 1.345, k, 4112)
            self.bw = rnd(0.221, 0.229, k, 4113)   # 225 nominal scaffold board
            self.bt = rnd(0.036, 0.039, k, 4114)   # 38 nominal
            # A scaffold deck is laid by eye against board clips, not machined:
            # 7-19 mm, and the first build's 5 mm minimum was a gap the lens
            # cannot see into at any angle it ever films this from.
            self.gap = rnd(0.007, 0.019, k, 4115)

        # boards run along the deck's LONGER axis on most posts, but not all:
        # a real deck is laid whichever way the bearers happen to run.
        self.axis = "x" if (self.Wd >= self.Dd) == chance(0.78, k, 4120) else "y"
        self.tiltx = math.radians(rnd(-0.55, 0.55, k, 4121))
        self.tilty = math.radians(rnd(-0.30, 1.15, k, 4122))   # falls to the front
        # the floor stops short of the legs rather than being notched round
        # them: a 60 mm notch on a 12 mm grid has a stepped edge, and 12 mm is
        # 7 px at the filmed distance.  A real perimeter gap is both truer and
        # cheaper than a jagged one.
        self.notch = False
        self.toe = self.kind == 3               # toe boards
        self.paint = pick(FRAME_PAINT, k, 4123)

        # ---- history --------------------------------------------------------
        self.age = rnd(0.18, 0.97, k, 4130)          # weathering / silvering
        self.wear_amp = rnd(0.35, 1.00, k, 4131)     # how hard it is walked
        self.moss = rnd(0.0, 0.85, k, 4132) * (0.35 + 0.65 * self.age)
        self.wet = rnd(0.05, 0.75, k, 4133)

        # ---- the walked line ------------------------------------------------
        # marshals arrive from BEHIND (the access road side, +y), stand at the
        # front to watch and wave, and the flag rack is at the front too.  The
        # path is that, with a real dogleg, not a straight line.
        self.acc_edge = pick(["back", "left", "right"], k, 4140) \
            if self.kind == 3 else "back"
        self.flag_x = rnd(-0.34, 0.34, k, 4141) * self.Wd
        ax, ay = self._access_point()
        mx = rnd(-0.25, 0.25, k, 4142) * self.Wd
        my = rnd(-0.10, 0.22, k, 4143) * self.Dd
        self.path = [(ax, ay), (mx, my), (self.flag_x, -self.Dd * 0.42),
                     (rnd(-0.40, 0.40, k, 4144) * self.Wd, -self.Dd * 0.36)]

        # ---- what is stored underneath --------------------------------------
        self.store = self._pick_store()
        self._gg = None
        self.boards = None

    # ------------------------------------------------------------------ misc
    def _access_point(self):
        if self.acc_edge == "back":
            return rnd(-0.30, 0.30, self.k, 4145) * self.Wd, self.Dd * 0.5
        sgn = 1.0 if self.acc_edge == "right" else -1.0
        return sgn * self.Wd * 0.5, rnd(0.05, 0.35, self.k, 4146) * self.Dd

    def under_clear(self):
        """Headroom under the deck.  Below ~0.12 m nothing goes under it and the
        kit lives BESIDE it on the hardstanding instead — which is what a
        duckboard 100 mm off the ground actually looks like."""
        return self.H - 0.055

    def stores_beside(self):
        return self.under_clear() < 0.115

    def _pick_store(self):
        """What is kept at this deck.  The manifest asked for it by name."""
        clear = 1.20 if self.stores_beside() else self.under_clear()
        pool = []
        if clear > 0.075:
            pool += ["hose", "offcuts"]
        if clear > 0.175:
            pool += ["sandbags", "slabs", "stakes"]
        if clear > 0.255:
            pool += ["boardstack", "tarp", "jerrycan", "bucket"]
        if not pool:
            return []
        n = rint(1, min(4, len(pool)), self.k, 4150)
        out, used = [], set()
        for i in range(n):
            for t in range(9):
                c = pick(pool, self.k, 4151, i, t)
                if c not in used:
                    used.add(c)
                    out.append(c)
                    break
        return out

    # ------------------------------------------------------- ground sampling
    def _ground_grid(self):
        """Local ground height on a 0.2 m lattice over the pad, from the CONTRACT.

        Law 5: never an assumed z.  `C.world_ground_z` is the datum; where it
        hands back NaN (the point is outside every road-programme owner and
        belongs to terrain) the runoff platform's own extension is used, which
        is what terrain ties into there.
        """
        if self._gg is not None:
            return
        half = max(self.padw, self.padd) * 0.5 + 1.2
        step = 0.2
        nn = int(math.ceil(2 * half / step)) + 1
        gx = -half + np.arange(nn) * step
        X, Y = np.meshgrid(gx, gx, indexing="ij")
        P = np.stack([X.ravel(), Y.ravel(), np.zeros(X.size)], 1) @ self.R.T + self.O
        z, _own = C.world_ground_z(P[:, 0], P[:, 1])
        bad = ~np.isfinite(z)
        if bad.any():
            ss, uu = C.project(P[bad, 0], P[bad, 1])
            z[bad] = C.ground_z(ss, uu)
        self._gg = (z - self.gz).reshape(nn, nn)
        self._gx0 = -half
        self._gy0 = -half
        self._gstep = step

    def gnd(self, x, y):
        """LOCAL ground z under a local (x, y).  Bilinear on the contract datum."""
        self._ground_grid()
        g = self._gg
        nn = g.shape[0]
        fx = np.clip((np.asarray(x, float) - self._gx0) / self._gstep, 0, nn - 1.001)
        fy = np.clip((np.asarray(y, float) - self._gy0) / self._gstep, 0, nn - 1.001)
        i0 = fx.astype(np.int64) if np.ndim(fx) else int(fx)
        j0 = fy.astype(np.int64) if np.ndim(fy) else int(fy)
        tx = fx - i0
        ty = fy - j0
        return (g[i0, j0] * (1 - tx) * (1 - ty) + g[i0 + 1, j0] * tx * (1 - ty)
                + g[i0, j0 + 1] * (1 - tx) * ty + g[i0 + 1, j0 + 1] * tx * ty)

    # ------------------------------------------------------------ the surface
    def plane_z(self, x, y):
        """the deck's nominal (built-level) plane, before boards."""
        return self.H + np.asarray(x, float) * math.tan(self.tiltx) \
            + np.asarray(y, float) * math.tan(self.tilty)

    def wear(self, x, y):
        """0..1 foot traffic at a local (x, y).  The manifest's 'wear path'."""
        x = np.asarray(x, float)
        y = np.asarray(y, float)
        w = np.zeros(np.broadcast(x, y).shape)
        for i in range(len(self.path) - 1):
            ax, ay = self.path[i]
            bx, by = self.path[i + 1]
            r = 0.20 + 0.16 * h01(self.k, 4160, i)
            w = np.maximum(w, 1.0 - sstep(r * 0.35, r, np.sqrt(
                seg_dist2(x, y, ax, ay, bx, by))))
        # the stance: where a marshal stands watching, at the front edge
        for i, (sx, sy) in enumerate(self.path[2:]):
            d = np.hypot(x - sx, y - sy)
            w = np.maximum(w, 1.0 - sstep(0.10, 0.42, d))
        # and the whole front strip gets some traffic
        w = np.maximum(w, 0.45 * (1.0 - sstep(0.05, 0.34, y + self.Dd * 0.5)))
        w = w * (0.72 + 0.56 * fbm2(x * 3.1 + self.seed, y * 3.1, self.seed + 5, 3))
        return np.clip(w * self.wear_amp, 0.0, 1.0)


def deck_plan():
    """The 25 decks, in lap-station order.  THE placement authority."""
    return [Deck(s) for s in SITES]


_PLAN_CACHE = []


def plan():
    if not _PLAN_CACHE:
        _PLAN_CACHE.extend(deck_plan())
    return _PLAN_CACHE


def site_frame(d):
    """deck-local -> world.  Returns (R 3x3, O 3-vector on the ground)."""
    return d.R, d.O


def to_world(d, Pl):
    Pl = np.asarray(Pl, float).reshape(-1, 3)
    return Pl @ d.R.T + d.O


# ================================================================================
#  5.  THE DECK SURFACE — one field, used by the builder AND by every query
# ================================================================================
#
# The boards are laid out ONCE, deterministically, and the same functions that
# generate the mesh answer `deck_top_z`.  If a chair agent asks where the surface
# is, it gets the surface that was built, to the micrometre, including the wear
# hollow and the raised grain — not the nominal plane the deck was set out to.

TUBE_R = 0.02415                 # 48.3 mm OD scaffold tube


def z_transom(d, x=0.0, y=0.0):
    """centreline of the tube the boards actually sit on."""
    return float(d.plane_z(x, y)) - d.bt - TUBE_R


def z_ledger(d, x=0.0, y=0.0):
    """centreline of the tube under that one, which the couplers grip."""
    return z_transom(d, x, y) - 2.0 * TUBE_R - 0.001


def _bearers(d):
    """positions ALONG the board axis where framing crosses under it."""
    A = d.Wd if d.axis == "x" else d.Dd
    if d.kind == 3:
        ins = 0.055
        return [-A * 0.5 + ins, A * 0.5 - ins]
    if d.kind == 0:
        return [-A * 0.5 + 0.075, 0.0, A * 0.5 - 0.075]
    n = max(2, int(round(A / 0.42)) + 1)
    return list(np.linspace(-A * 0.5 + 0.06, A * 0.5 - 0.06, n))


def board_layout(d):
    """The boards, in order across the deck.  Cached on the Deck.

    A real deck is not n identical boards: the last one is RIPPED to fit, the
    gaps are set by eye so they differ, one board has been replaced and is
    younger than the rest, and none of them is straight.
    """
    if d.boards is not None:
        return d.boards
    A = d.Wd if d.axis == "x" else d.Dd          # along the boards
    B = d.Dd if d.axis == "x" else d.Wd          # across them
    k = d.k
    bw, g0 = d.bw, d.gap
    nb = max(2, int(math.floor((B + g0) / (bw + g0))))
    rest = B - (nb * bw + (nb - 1) * g0)
    ripped = rest > 0.052
    boards = []
    c = -B * 0.5
    total = nb + (1 if ripped else 0)
    # a replaced board: newer timber, tighter grain, brighter, fewer splits
    newb = rint(-1, total - 1, k, 4200)
    for j in range(total):
        w = (rest - 0.006) if (ripped and j == total - 1) else bw * rnd(0.994, 1.006, k, 4201, j)
        gj = g0 + rnd(-0.0032, 0.0032, k, 4202, j)
        if j:
            c += gj
        cc = c + w * 0.5
        c += w
        fresh = (j == newb)
        t = d.bt * rnd(0.975, 1.02, k, 4203, j)
        L = A + rnd(0.018, 0.062, k, 4204, j) + rnd(0.018, 0.062, k, 4205, j)
        u0 = (rnd(0.018, 0.062, k, 4204, j) - rnd(0.018, 0.062, k, 4205, j)) * 0.5
        age = np.clip(d.age * (0.20 if fresh else 1.0)
                      + rnd(-0.10, 0.10, k, 4206, j), 0.0, 1.0)
        cup = rnd(-0.0022, 0.0052, k, 4207, j) * (0.35 + 1.3 * age)
        bow = rnd(-0.0026, 0.0026, k, 4208, j)
        sag = rnd(0.0004, 0.0042, k, 4209, j) * (A / 2.4) ** 2
        tw = rnd(-0.010, 0.010, k, 4210, j) * (0.3 + age)
        # splits: checks that open along the grain as the board weathers
        nsp = 0 if fresh else rint(0, 3, k, 4211, j)
        splits = []
        for q in range(nsp):
            su = rnd(-0.42, 0.42, k, 4212, j, q) * L
            sl = rnd(0.10, 0.55, k, 4213, j, q) * L
            splits.append(dict(v=rnd(-0.40, 0.40, k, 4214, j, q) * w,
                               u0=su - sl * 0.5, u1=su + sl * 0.5,
                               hw=rnd(0.0011, 0.0038, k, 4215, j, q),
                               dep=min(0.30 * t,
                                       rnd(0.0022, 0.011, k, 4216, j, q) * (0.4 + age))))
        # fixings
        fix = []
        for bi, bu in enumerate(_bearers(d)):
            nf = 2
            for f in range(nf):
                fv = (-1.0 if f == 0 else 1.0) * w * rnd(0.23, 0.32, k, 4217, j, bi, f)
                fix.append(dict(u=bu + rnd(-0.006, 0.006, k, 4218, j, bi, f),
                                v=fv,
                                sink=rnd(0.0008, 0.0031, k, 4219, j, bi, f),
                                kind=("screw" if d.kind in (1, 3) else "nail"),
                                skew=rnd(-9.0, 9.0, k, 4220, j, bi, f),
                                rust=rnd(0.15, 0.95, k, 4221, j, bi, f)))
        boards.append(dict(j=j, c=cc, w=w, t=t, L=L, u0=u0, age=float(age),
                           fresh=fresh, cup=cup, bow=bow, sag=sag, tw=tw,
                           phase=rnd(0, 6.283, k, 4222, j), splits=splits,
                           fix=fix, band=(d.kind == 3 and not chance(0.18, k, 4223, j)),
                           gap_before=(gj if j else 0.0),
                           grain_seed=int(h01(k, 4224, j) * 100000)))
    d.boards = boards
    return boards


def _board_xy(d, b, u, v):
    """board (u along, v across) -> deck-local (x, y)."""
    if d.axis == "x":
        return u + b["u0"], v + b["c"]
    return v + b["c"], u + b["u0"]


def _grain(d, b, u, v):
    """latewood band field in [0,1] across the board, coherent along it."""
    vg = (b["c"] + v) * 1.0
    w = fbm1(vg * 62.0 + b["grain_seed"], b["grain_seed"], 3, 2.11, 0.46)
    w = w + 0.35 * (n1(vg * 143.0 + 7.0, b["grain_seed"] + 3) - 0.5)
    mod = 0.80 + 0.40 * n1(u * 2.7 + b["grain_seed"] * 0.01, b["grain_seed"] + 9)
    return np.clip((w - 0.42) * 2.4 * mod + 0.5, 0.0, 1.0)


def board_base(d, b, u, v):
    """The board's NEUTRAL surface: the built plane plus how the board itself
    has moved — sag under load, natural bow, cup across the width, and twist.

    Split out from `board_top` because the underside must follow the board, and
    only the board: a 2 mm wear hollow in the top face does not make the bottom
    of the board 2 mm thinner, and modelling it as `top - thickness` is exactly
    how a generated board ends up with an impossible section.
    """
    u = np.asarray(u, float)
    v = np.asarray(v, float)
    x, y = _board_xy(d, b, u, v)
    # plane_z is the WALKING SURFACE — `H` is the height of the deck you stand
    # on, not of its framing — so the board's neutral axis sits half a thickness
    # below it.  Getting this backwards stands every board 19 mm proud of the
    # level it was set out to, which `selftest` caught as a +24.5 mm departure.
    z = d.plane_z(x, y) - b["t"] * 0.5
    L, w = b["L"], b["w"]
    tt = np.clip(2.0 * u / max(L, 1e-6), -1.0, 1.0)
    z = z - b["sag"] * (1.0 - tt * tt) ** 1.2
    z = z + b["bow"] * np.cos(math.pi * tt * 0.5 + b["phase"] * 0.0)
    z = z + b["cup"] * ((2.0 * v / max(w, 1e-6)) ** 2 - 1.0 / 3.0)
    z = z + b["tw"] * tt * (2.0 * v / max(w, 1e-6)) * 0.5
    return z


def board_bottom(d, b, u, v):
    """The underside: rough-sawn, still carrying the band-saw ripple and, on
    the odd board, the wane where the log ran out."""
    u = np.asarray(u, float)
    v = np.asarray(v, float)
    z = board_base(d, b, u, v) - b["t"] * 0.5
    z = z - 0.00035 * n1(u * 22.0 + b["grain_seed"], b["grain_seed"] + 41)
    z = z + 0.0022 * np.clip(
        (np.abs(v) - b["w"] * 0.40) / (b["w"] * 0.10), 0.0, 1.0) ** 2 \
        * sstep(-0.35, 0.15, n1(u * 1.4, b["grain_seed"] + 77) - 0.5)
    return z


def board_top(d, b, u, v, wear=None):
    """LOCAL z of a board's top surface at board coordinates (u, v).

    This is the deck.  Every millimetre of it is here: the built plane and its
    fall, the board's own cup, bow, sag and twist, the grain the weather has
    raised, the hollow the boots have worn, the dish round every fixing and the
    lips of every split.
    """
    u = np.asarray(u, float)
    v = np.asarray(v, float)
    x, y = _board_xy(d, b, u, v)
    z = board_base(d, b, u, v) + b["t"] * 0.5
    L, w = b["L"], b["w"]
    g = _grain(d, b, u, v)
    if wear is None:
        wear = d.wear(x, y)
    age = b["age"]
    # weathering RAISES the grain: the soft earlywood erodes first, so the
    # latewood bands stand proud.  Traffic then planes the whole thing down.
    z = z + (0.00016 + 0.00082 * age) * (g - 0.45)
    z = z - wear * (0.00042 + 0.00205 * age) * (1.0 - 0.72 * g)
    # dished round every fixing
    for f in b["fix"]:
        r2 = (u - f["u"]) ** 2 + (v - f["v"]) ** 2
        z = z - f["sink"] * np.clip(1.0 - r2 / (0.0085 ** 2), 0.0, 1.0) ** 1.5
    # splits
    for sp in b["splits"]:
        al = sstep(sp["u0"], sp["u0"] + 0.04, u) * (1.0 - sstep(sp["u1"] - 0.04, sp["u1"], u))
        ac = np.clip(1.0 - (np.abs(v - sp["v"]) / sp["hw"]) ** 2, 0.0, 1.0)
        z = z - sp["dep"] * al * ac ** 0.55
    # the very ends dry out, check and lift
    z = z + 0.0009 * age * sstep(L * 0.5 - 0.075, L * 0.5 - 0.012, np.abs(u)) \
        * (0.5 + 0.5 * np.cos(v * 84.0))
    return z


def deck_top_z(d, x, y):
    """LOCAL z of the WALKING SURFACE at local (x, y).

    Never NaN: over a board gap it returns the supporting surface (the level a
    foot or a chair leg bridging the gap would rest at), which is what a
    placement agent needs.  Use `over_gap()` for the gap test itself.
    """
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    if d.kind == 1:
        return _sheet_top(d, x, y)
    if d.kind == 2:
        return d.plane_z(x, y)
    bs = board_layout(d)
    cs = np.array([b["c"] for b in bs])
    across = y if d.axis == "x" else x
    idx = np.argmin(np.abs(np.atleast_1d(across)[:, None] - cs[None, :]), axis=1)
    out = np.empty(np.atleast_1d(across).shape)
    ax = np.atleast_1d(x)
    ay = np.atleast_1d(y)
    for j in np.unique(idx):
        m = idx == j
        b = bs[int(j)]
        u = (ax[m] - b["u0"]) if d.axis == "x" else (ay[m] - b["u0"])
        v = (ay[m] - b["c"]) if d.axis == "x" else (ax[m] - b["c"])
        out[m] = board_top(d, b, u, np.clip(v, -b["w"] * 0.5, b["w"] * 0.5))
    return out if np.ndim(x) or np.ndim(y) else float(out[0])


def _sheet_top(d, x, y):
    """the hut's ply floor: sheet + the worn hollow in the doorway."""
    z = d.plane_z(x, y)
    wr = d.wear(x, y)
    z = z - wr * 0.0018 * (0.4 + 0.9 * d.age)
    for (jx, jy, ax) in _sheet_joints(d):
        dd = np.abs((x - jx) if ax == "x" else (y - jy))
        z = z - 0.0016 * np.clip(1.0 - dd / 0.030, 0.0, 1.0) ** 1.4
    return z


def _sheet_joints(d):
    out = []
    nx = max(1, int(round(d.Wd / 1.22)))
    for i in range(1, nx):
        out.append((-d.Wd * 0.5 + d.Wd * i / nx, 0.0, "x"))
    if d.Dd > 1.30:
        out.append((0.0, rnd(-0.12, 0.12, d.k, 4230), "y"))
    return out


def over_gap(d, x, y):
    """True where the query is over a hole in the deck rather than over board."""
    if d.kind == 1:
        return np.zeros(np.broadcast(np.asarray(x, float),
                                     np.asarray(y, float)).shape, bool)
    if d.kind == 2:
        across = np.asarray(x if d.axis == "y" else y, float)
        p = d.bw * 0.0 + d.bt + d.gap
        ph = np.mod(across + 0.5 * p, p) - 0.5 * p
        return np.abs(ph) > d.bt * 0.5
    bs = board_layout(d)
    across = np.asarray(y if d.axis == "x" else x, float)
    ok = np.zeros(np.broadcast(np.asarray(x, float), across).shape, bool)
    for b in bs:
        ok |= np.abs(across - b["c"]) <= b["w"] * 0.5
    return ~ok


def on_deck(d, x, y):
    """True where the deck exists at all (inside its outline, not in a notch)."""
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    ins = (np.abs(x) <= d.Wd * 0.5) & (np.abs(y) <= d.Dd * 0.5)
    if d.notch:
        for (nx_, ny_, r) in _notches(d):
            ins &= ~((np.abs(x - nx_) < r) & (np.abs(y - ny_) < r))
    return ins


def _notches(d):
    """corner squares cut out of the floor so the shelter legs pass through."""
    r = d.legr + 0.014
    return [(sx * d.W * 0.5, sy * d.D * 0.5, r)
            for sx in (-1, 1) for sy in (-1, 1)]


# ================================================================================
#  6.  THE PUBLIC INTERFACE FOR THE SIX DEPENDANTS
# ================================================================================
#
# OWNERSHIP, stated once so four agents who never meet cannot build it twice:
#
#   THIS MODULE owns  the walking surface and everything that carries it within
#                     0.55 m of the ground: deck boards, ply floor, grating,
#                     joists, bearers, ledgers, transoms, couplers, toe boards,
#                     the sleepers and sole boards on the ground, and the stuff
#                     stored underneath.
#   marshal_post_column owns every vertical member taller than 0.55 m — the
#                     shelter legs and the scaffold standards.  It lands on
#                     `column_sockets()` and nothing else in the family owns
#                     that contact.
#   marshal_post_stair owns everything below `stair_landing()`.
#   marshal_post_handrail owns everything above `handrail_sockets()`.  The LUGS
#                     and the coupler bosses are built HERE, on the deck.

def column_sockets(d):
    """Where this deck is carried, and by what.  For ``marshal_post_column``.

    The positions are build_dressing's own shelter-leg positions, and `legr` is
    its own leg radius, reproduced through a byte-identical hash from the same
    key — so the column that replaces build_dressing's legs lands exactly where
    the rest of the world already expects the post to be.
    """
    out = []
    W, D = d.W, d.D
    if d.kind == 2:
        pos = [(-W * 0.40, 0.0, "rail"), (W * 0.40, 0.0, "rail")]
    else:
        pos = [(sx * W * 0.5, sy * D * 0.5, "corner")
               for sx in (-1, 1) for sy in (-1, 1)]
        if d.kind == 3 and W > 2.85:
            pos += [(0.0, sy * D * 0.5, "mid") for sy in (-1, 1)]
    for i, (x, y, role) in enumerate(pos):
        gz = float(d.gnd(x, y))
        if d.kind == 3:
            kind, size = d.col_kind, d.col_size
            bear = z_ledger(d, x, y)          # ledger centreline
            plate = dict(w=0.150, d=0.150, t=0.006,
                         z=round(gz - BASE_EMBED_M * 0.25, 5))
            sole = dict(w=0.600, d=0.225, t=0.038, z=round(gz - BASE_EMBED_M, 5))
            carries = True
        else:
            kind, size = "tube", round(d.legr * 2.0, 4)
            bear = gz
            plate = dict(w=0.300, d=0.300, t=0.075,
                         z=round(gz - BASE_EMBED_M, 5))
            sole = None
            carries = (d.kind == 1)
        out.append(dict(i=i, role=role, x=round(x, 4), y=round(y, 4),
                        kind=kind, size=size, ground_z=round(gz, 5),
                        bearing_z=round(float(bear), 5),
                        deck_top_z=round(float(d.plane_z(x, y)), 5),
                        base_plate=plate, sole_board=sole,
                        carries_deck=carries,
                        notched=bool(d.notch and role == "corner"),
                        built_here=("base plate + sole board" if d.kind == 3
                                    else "concrete pad")))
    return out


def handrail_sockets(d):
    """Where ``marshal_post_handrail`` stands its posts.  The lugs exist."""
    out = []
    edges = []
    if d.kind == 3:
        for e in ("front", "left", "right"):
            if e == "back":
                continue
            if (d.acc_edge == "left" and e == "left") or \
               (d.acc_edge == "right" and e == "right"):
                continue
            edges.append(e)
        edges.append("back")
    else:
        edges = ["front"]
    for e in edges:
        if e in ("front", "back"):
            y = -d.Dd * 0.5 if e == "front" else d.Dd * 0.5
            nrm = (0.0, -1.0) if e == "front" else (0.0, 1.0)
            L, ctr = d.Wd, 0.0
        else:
            x = (-1.0 if e == "left" else 1.0) * d.Wd * 0.5
            nrm = (-1.0 if e == "left" else 1.0, 0.0)
            L, ctr = d.Dd, 0.0
        npst = max(2, int(round(L / 1.15)) + 1)
        for i in range(npst):
            t = -L * 0.5 + L * i / (npst - 1)
            if e in ("front", "back"):
                px, py = t, y
            else:
                px, py = x, t
            corner = (i in (0, npst - 1))
            if d.kind == 3:
                mount = "coupler" if corner else "lug"
                z = z_ledger(d, px, py) if corner else \
                    float(deck_top_z(d, px, py))
            else:
                mount = "ground"
                z = float(d.gnd(px, py))
            out.append(dict(edge=e, x=round(float(px), 4), y=round(float(py), 4),
                            z=round(z, 5),
                            deck_top_z=round(float(deck_top_z(d, px, py)), 5),
                            normal=nrm, mount=mount,
                            dia=(0.0483 if d.kind == 3 else round(d.legr * 2, 4)),
                            lug=dict(w=0.070, h=0.055, t=0.006, hole=0.013)
                            if mount == "lug" else None))
    return out


def stair_landing(d):
    """Where ``marshal_post_stair`` arrives.  The toe-board opening is cut."""
    ax, ay = d._access_point()
    e = d.acc_edge
    if e == "back":
        nrm, w_open = (0.0, 1.0), rnd(0.56, 0.76, d.k, 4300)
    else:
        nrm = (-1.0 if e == "left" else 1.0, 0.0)
        w_open = rnd(0.52, 0.70, d.k, 4300)
    gz = float(d.gnd(ax, ay))
    top = float(deck_top_z(d, ax * 0.92, ay * 0.92))
    rise = top - gz
    return dict(edge=e, x=round(float(ax), 4), y=round(float(ay), 4),
                deck_top_z=round(top, 5), ground_z=round(gz, 5),
                total_rise_m=round(rise, 5),
                needs_stair=bool(rise > 0.42),
                risers=max(1, int(round(rise / 0.195))),
                clear_width_m=round(float(w_open), 4),
                toe_board_opening=bool(d.toe),
                nosing_overhang_m=round(rnd(0.018, 0.042, d.k, 4301), 4),
                normal=nrm,
                note="build DOWN from deck_top_z; the deck's own edge board "
                     "already overhangs by nosing_overhang_m")


def floor_slots(d):
    """Free rectangles on the deck, best first.  For chair / cooler / bin."""
    slots = []
    step = 0.05
    nx = max(3, int(d.Wd / step))
    ny = max(3, int(d.Dd / step))
    gx = np.linspace(-d.Wd * 0.5 + 0.10, d.Wd * 0.5 - 0.10, nx)
    gy = np.linspace(-d.Dd * 0.5 + 0.10, d.Dd * 0.5 - 0.10, ny)
    X, Y = np.meshgrid(gx, gy, indexing="ij")
    wr = d.wear(X, Y)
    ok = on_deck(d, X, Y)
    # keep clear of the flag rack at the front and of the access opening
    ax, ay = d._access_point()
    clear = (np.hypot(X - d.flag_x, Y + d.Dd * 0.5 - 0.28) > 0.34) & \
            (np.hypot(X - ax, Y - ay) > 0.45)
    q = (1.0 - wr) * ok * clear
    for i in range(6):
        if q.max() <= 0.12:
            break
        a = int(np.argmax(q))
        ix, iy = a // q.shape[1], a % q.shape[1]
        px, py = float(X[ix, iy]), float(Y[ix, iy])
        slots.append(dict(x=round(px, 4), y=round(py, 4),
                          z=round(float(deck_top_z(d, px, py)), 5),
                          quality=round(float(q[ix, iy]), 4),
                          over_gap=bool(over_gap(d, px, py)),
                          board_axis=d.axis,
                          clear_h=round(float(d.Hh + d.H - deck_top_z(d, px, py)), 4),
                          facing=("front" if py < 0 else "back")))
        q[np.hypot(X - px, Y - py) < 0.42] = 0.0
    return slots


def lean_points(d):
    """Where a broom, shovel or rake can lean.  For ``marshal_broom``."""
    out = []
    bx = rnd(-0.35, 0.35, d.k, 4310) * d.Wd
    out.append(dict(what="back edge of the deck", x=round(float(bx), 4),
                    y=round(float(d.Dd * 0.5 - 0.06), 4),
                    z=round(float(deck_top_z(d, bx, d.Dd * 0.5 - 0.06)), 5),
                    lean_deg=round(rnd(9.0, 17.0, d.k, 4311), 2),
                    normal=(0.0, 1.0), surface="deck")
               )
    for sc in column_sockets(d)[:2]:
        out.append(dict(what="against the %s column" % sc["role"],
                        x=sc["x"], y=sc["y"], z=sc["ground_z"],
                        lean_deg=round(rnd(7.0, 15.0, d.k, 4312, sc["i"]), 2),
                        normal=(0.0, 1.0), surface="ground"))
    if d.toe:
        out.append(dict(what="hooked over the toe board", x=round(float(-bx), 4),
                        y=round(float(-d.Dd * 0.5 + 0.02), 4),
                        z=round(float(deck_top_z(d, -bx, -d.Dd * 0.5 + 0.05)) + 0.15, 5),
                        lean_deg=round(rnd(4.0, 11.0, d.k, 4313), 2),
                        normal=(0.0, -1.0), surface="toe board"))
    return out


STORE_SIZE = dict(sandbags=(0.62, 0.44, 0.17), boardstack=(2.05, 0.30, 0.16),
                  hose=(0.52, 0.52, 0.14), tarp=(0.95, 0.26, 0.26),
                  slabs=(0.62, 0.46, 0.19), stakes=(1.10, 0.16, 0.13),
                  jerrycan=(0.34, 0.20, 0.34), bucket=(0.30, 0.30, 0.29),
                  offcuts=(0.75, 0.34, 0.11))


def store_layout(d):
    """What is under this deck, and exactly where.  Deterministic.

    The manifest asked for this in as many words: "things stored under the
    deck".  A raised deck with nothing under it reads as a stage flat.
    """
    out = []
    if not d.store:
        return out
    if d.stores_beside():
        # on the hardstanding at the back and the sheltered side, clear of the
        # front where the marshal stands and of the walked line
        bw = d.Wd * 0.5
        bd = d.Dd * 0.5
        slots = [(-bw * 0.55, bd + 0.42), (bw * 0.62, bd + 0.36),
                 (bw + 0.40, -bd * 0.25), (-bw - 0.42, bd * 0.30),
                 (0.10, bd + 0.62)]
    else:
        cw = d.Wd * 0.5 - 0.10
        cd = d.Dd * 0.5 - 0.10
        slots = [(-cw * 0.55, cd * 0.45), (cw * 0.55, cd * 0.40),
                 (-cw * 0.50, -cd * 0.35), (cw * 0.48, -cd * 0.40),
                 (0.0, cd * 0.55)]
    for i, what in enumerate(d.store):
        sx, sy = slots[i % len(slots)]
        sx += rnd(-0.09, 0.09, d.k, 4320, i)
        sy += rnd(-0.09, 0.09, d.k, 4321, i)
        w, l, h = STORE_SIZE[what]
        yaw_ = rnd(0, 180, d.k, 4322, i)
        out.append(dict(what=what, x=round(float(sx), 4), y=round(float(sy), 4),
                        yaw=round(float(yaw_), 3),
                        size=(w, l, h), seed=int(h01(d.k, 4323, i) * 99991)))
    return out


def under_deck(d):
    """The clear volume under the deck, and what this module already put in it."""
    occ = []
    for it in store_layout(d):
        w, l, h = it["size"]
        r = math.hypot(w, l) * 0.5
        gz = float(d.gnd(it["x"], it["y"]))
        occ.append(dict(what=it["what"],
                        lo=(round(it["x"] - r, 4), round(it["y"] - r, 4), round(gz - 0.03, 4)),
                        hi=(round(it["x"] + r, 4), round(it["y"] + r, 4), round(gz + h, 4))))
    zmin = float(np.min([d.gnd(x, y) for x in (-d.Wd * 0.5, d.Wd * 0.5)
                         for y in (-d.Dd * 0.5, d.Dd * 0.5)]))
    return dict(stored_beside=bool(d.stores_beside()),
                clear=dict(lo=(round(-d.Wd * 0.5, 4), round(-d.Dd * 0.5, 4), round(zmin, 4)),
                           hi=(round(d.Wd * 0.5, 4), round(d.Dd * 0.5, 4),
                               round(float(d.plane_z(0, 0)) - d.bt - 0.10, 4))),
                headroom_m=round(float(d.plane_z(0, 0)) - d.bt - 0.10 - zmin, 4),
                occupied=occ)


# ================================================================================
#  7.  BOARD GEOMETRY — a board is a solid, not a box with a wood colour
# ================================================================================

_ARC = np.array([0.25, 0.50, 0.75]) * (math.pi * 0.5)


def board_section(w, t, arr, ch, ntop):
    """Cross-section of a sawn board, as (VV (n,m), MODE (m,), OFF (n,m)).

    MODE 0 = the point rides on the TOP surface, 1 = on the underside; OFF is
    its offset from that surface.  So the arris is a real quarter-round that
    follows the worn, cupped, grained top rather than a chamfer on a nominal
    plane — which is what makes a deck's front edge catch the light along its
    length instead of reading as one straight highlight.
    """
    arr = np.atleast_1d(np.asarray(arr, float))
    n = arr.shape[0]
    h = w * 0.5
    vt = np.linspace(-h + arr, h - arr, ntop, axis=-1)          # (n, ntop)
    cs, sn = np.cos(_ARC), np.sin(_ARC)
    parts = []                       # (V (n,k), mode, OFF (n,k))
    vb = np.linspace(-h + ch, h - ch, 5)
    parts.append((np.broadcast_to(vb, (n, 5)), 1, np.zeros((n, 5))))
    parts.append((np.full((n, 1), h), 1, np.full((n, 1), ch)))
    parts.append((np.full((n, 1), h), 1, np.full((n, 1), t * 0.55)))
    parts.append((np.full((n, 1), h), 0, -arr[:, None]))
    parts.append((h - arr[:, None] + arr[:, None] * cs[None, :], 0,
                  -arr[:, None] + arr[:, None] * sn[None, :]))
    parts.append((vt[:, ::-1], 0, np.zeros((n, ntop))))
    parts.append((-h + arr[:, None] - arr[:, None] * cs[None, ::-1], 0,
                  -arr[:, None] + arr[:, None] * sn[None, ::-1]))
    parts.append((np.full((n, 1), -h), 0, -arr[:, None]))
    parts.append((np.full((n, 1), -h), 1, np.full((n, 1), t * 0.55)))
    parts.append((np.full((n, 1), -h), 1, np.full((n, 1), ch)))
    VV = np.concatenate([p[0] for p in parts], axis=1)
    OFF = np.concatenate([p[2] for p in parts], axis=1)
    MODE = np.concatenate([np.full(p[0].shape[1], p[1], np.int8) for p in parts])
    return VV, MODE, OFF


def board_solid(acc, U, VV, MODE, OFF, ztop, zbot, pt, mat=M_TIMBER,
                attrs=None, cap_over=None, bc=None, tint=None):
    """Assemble one board from its stations, its section and its two surfaces."""
    n, m = VV.shape
    UU = np.broadcast_to(np.asarray(U, float)[:, None], (n, m))
    Z = np.empty((n, m))
    tm = MODE == 0
    if tm.any():
        Z[:, tm] = ztop(UU[:, tm], VV[:, tm]) + OFF[:, tm]
    if (~tm).any():
        Z[:, ~tm] = zbot(UU[:, ~tm], VV[:, ~tm]) + OFF[:, ~tm]
    P = pt(UU, VV, Z)
    kw = {} if attrs is None else {k: np.asarray(v).ravel() for k, v in attrs.items()}
    return extrude(acc, P, mat=mat, caps=True, bc=bc, cap_over=cap_over,
                   tint=tint, **kw)


def _flat(a, n, m):
    return np.broadcast_to(np.asarray(a, float), (n, m)).ravel()


def board_grain_offset(k, j, salt=0):
    """Where in the grain field this particular board was cut from."""
    return (rnd(-260.0, 260.0, k, 4406 + salt, j),
            rnd(-260.0, 260.0, k, 4407 + salt, j))


def board_tint(k, j, fresh=False, spread=1.0):
    """Per-board colour multiplier.  +-32 %, and it moves hue as well as value:
    one board is redder heartwood, the next is a pale sapwood board, a third
    still carries the green of its preservative treatment."""
    v = 0.70 + 0.62 * h01(k, 4401, j)
    r = v * (1.0 + spread * (h01(k, 4402, j) - 0.5) * 0.34)
    g = v * (1.0 + spread * (h01(k, 4403, j) - 0.5) * 0.22)
    b = v * (1.0 + spread * (h01(k, 4404, j) - 0.5) * 0.30)
    if fresh:
        r, g, b = r * 1.22, g * 1.16, b * 1.02
    if h01(k, 4405, j) < 0.16:            # a tanalised board among the plain ones
        r, g, b = r * 0.86, g * 1.06, b * 0.80
    return np.array([r, g, b])


def build_deck_board(acc, d, b, lod=1.0):
    """One deck board, with everything that has happened to it."""
    w, t, L = b["w"], b["t"], b["L"]
    ch = 0.0012 + 0.0016 * b["age"]
    U = stations(L, 0.0135 / lod, refine=[f["u"] for f in b["fix"]])
    n = U.shape[0]
    xs, ys = _board_xy(d, b, U, 0.0)
    wr = d.wear(xs, ys)
    # the arris is rounded off by boots: a worn board has no sharp edge left
    arr = 0.0011 + 0.0026 * b["age"] + 0.0042 * wr
    ntop = max(9, int(round((w - 0.006) / (0.0053 / lod))))
    VV, MODE, OFF = board_section(w, t, arr, ch, ntop)
    m = VV.shape[1]

    def ztop(u, v):
        return board_top(d, b, u, v)

    def zbot(u, v):
        return board_bottom(d, b, u, v)

    if d.axis == "x":
        def pt(u, v, z):
            return np.stack([u + b["u0"], v + b["c"], z], -1)
    else:
        def pt(u, v, z):
            return np.stack([v + b["c"], u + b["u0"], z], -1)

    UU = np.broadcast_to(U[:, None], (n, m))
    px, py = _board_xy(d, b, UU, VV)
    wear2 = d.wear(px, py) * (MODE[None, :] == 0)
    top = (MODE[None, :] == 0).astype(float)
    edge = np.clip((np.abs(VV) - w * 0.5 + 0.010) / 0.010, 0.0, 1.0)
    # damp lives on the underside, in the gaps and at the ends
    wet = d.wet * (0.30 + 0.70 * (1.0 - top)) + 0.25 * edge * d.wet
    moss = d.moss * (0.25 + 0.75 * (1.0 - top)) * (1.0 - 0.85 * wear2) \
        * (0.35 + 0.65 * edge)
    ao = 0.15 + 0.75 * (1.0 - top) + 0.35 * edge
    # iron staining round every fixing: wet timber and a steel nail make a black
    # halo you can see from across a paddock.  Baked as a field so the shader
    # blooms exactly where the geometry has a fixing, not where a noise happens
    # to fire.
    grit = np.zeros((n, m))
    for f in b["fix"]:
        r = np.sqrt((UU - f["u"]) ** 2 + (VV - f["v"]) ** 2)
        grit = np.maximum(grit, np.clip(1.0 - r / 0.034, 0.0, 1.0) ** 1.5 * f["rust"])
    grit = grit * (MODE[None, :] == 0)
    attrs = dict(
        mpd_wear=wear2.ravel(),
        mpd_age=_flat(b["age"], n, m),
        mpd_wet=np.clip(wet, 0, 1).ravel(),
        mpd_moss=np.clip(moss, 0, 1).ravel(),
        mpd_rust=_flat(0.0, n, m),
        mpd_end=np.clip((np.abs(UU) - L * 0.5 + 0.055) / 0.055, 0, 1).ravel() * 0.45,
        mpd_paint=_flat(0.0, n, m),
        mpd_id=_flat(h01(d.k, 4400, b["j"]), n, m),
        mpd_ao=np.clip(ao, 0, 1).ravel(),
        mpd_grit=grit.ravel())
    # EVERY BOARD ITS OWN TREE.  The first build baked `bc` as the raw board
    # coordinate, so all 12 boards on a deck sampled the same point of the same
    # noise field: identical rings, identical knots, identical weathering
    # patches, and a 4K macro of 12 planks that were visibly one plank repeated
    # -- "one tree spammed 100 times" at the scale of a single object.  The
    # offset walks each board to its own place in the field.
    ox, oy = board_grain_offset(d.k, b["j"])
    bc = np.stack([UU + ox, VV + oy, np.zeros_like(UU)], -1).reshape(-1, 3)
    # per-board colour: real boards come from different trees, different mills
    # and different years, and a deck of 10 identical planks is the tell.
    tint = board_tint(d.k, b["j"], b["fresh"])
    board_solid(acc, U, VV, MODE, OFF, ztop, zbot, pt, mat=M_TIMBER,
                attrs=attrs, bc=bc, tint=tint,
                cap_over=dict(mpd_end=1.0, mpd_wear=0.0, mpd_ao=0.55))
    for f in b["fix"]:
        build_fixing(acc, d, b, f, lod)
    if b["band"]:
        for sgn in (-1.0, 1.0):
            build_end_band(acc, d, b, sgn, VV, MODE, OFF, ch, lod)


def build_fixing(acc, d, b, f, lod=1.0):
    """A screw or a nail, dished into the board it holds down.

    The head is 8 mm across — 5 px at the filmed distance — so it is a cone, a
    rim and a recess, not a dot.  On a worn board the wood around it has gone
    and the head stands proud of the surface it was driven flush with.
    """
    u, v = f["u"], f["v"]
    z0 = float(board_top(d, b, np.array([u]), np.array([v]))[0])
    x, y = _board_xy(d, b, u, v)
    wr = float(d.wear(x, y))
    proud = wr * b["age"] * 0.0016
    if f["kind"] == "screw":
        zs = np.array([-0.0062, -0.0011, 0.0, -0.0011, -0.0018]) + proud
        rs = np.array([0.0021, 0.0041, 0.0041, 0.0022, 0.00035])
    else:
        zs = np.array([-0.0040, -0.0009, 0.0007, 0.0013, 0.0011]) + proud
        rs = np.array([0.0018, 0.0033, 0.0036, 0.0029, 0.00040])
    a = math.radians(f["skew"])
    nseg = 10 if lod >= 0.9 else 8
    path = np.stack([x + zs * math.sin(a), y + zs * math.sin(a * 0.7),
                     z0 + zs * math.cos(a)], -1)
    sect = circle(1.0, nseg)
    P = np.empty((len(zs), nseg, 3))
    T, N, B = frames_along(path)
    for i in range(len(zs)):
        P[i] = path[i][None, :] + (sect[:, 0:1] * rs[i]) * N[i][None, :] \
            + (sect[:, 1:2] * rs[i]) * B[i][None, :]
    extrude(acc, P, mat=M_GALV, caps=True,
            mpd_rust=f["rust"], mpd_wear=wr, mpd_age=b["age"],
            mpd_wet=d.wet, mpd_ao=0.55, mpd_id=h01(d.k, 4410, f["u"], f["v"]),
            bc=np.array([0.0, 0.0, 0.0]))


def build_end_band(acc, d, b, sgn, VV, MODE, OFF, ch, lod=1.0):
    """Hoop iron round a scaffold board's end: 0.9 mm plate, 32 mm wide.

    0.9 mm is 0.56 px at this distance, which is exactly why it must be a strap
    and not a painted stripe: what the lens sees is a bright galvanised line
    with a shadow under it, and a stripe has no shadow.
    """
    L = b["L"]
    bw = rnd(0.028, 0.036, d.k, 4420, b["j"], sgn)
    uc = sgn * (L * 0.5 - bw * 0.5 - rnd(0.004, 0.014, d.k, 4421, b["j"], sgn))
    U1 = np.array([uc])
    arr = np.array([0.0011 + 0.0026 * b["age"]])
    V1, M1, O1 = board_section(b["w"], b["t"], arr, ch, 14)
    m = V1.shape[1]
    zt = board_top(d, b, np.full((1, m), uc), V1)
    zb = board_bottom(d, b, np.full((1, m), uc), V1)
    Z = np.where(M1[None, :] == 0, zt, zb) + O1
    poly = np.stack([V1[0], Z[0]], -1)                      # (m, 2) in (v, z)
    # outward normals of the closed section, to stand the band off the timber
    tng = np.roll(poly, -1, 0) - np.roll(poly, 1, 0)
    nrm = np.stack([tng[:, 1], -tng[:, 0]], -1)
    nl = np.linalg.norm(nrm, axis=1, keepdims=True)
    nrm = nrm / np.maximum(nl, 1e-9)
    ctr = poly.mean(0)
    if float(np.mean(np.einsum("ij,ij->i", nrm, poly - ctr))) < 0:
        nrm = -nrm
    off = 0.00055
    ring = poly + nrm * off
    if d.axis == "x":
        path = np.stack([np.full(m, uc + b["u0"]), ring[:, 0] + b["c"], ring[:, 1]], -1)
        upd = np.array([1.0, 0.0, 0.0])
    else:
        path = np.stack([ring[:, 0] + b["c"], np.full(m, uc + b["u0"]), ring[:, 1]], -1)
        upd = np.array([0.0, 1.0, 0.0])
    T, N, B = frames_along(path, up_hint=upd)
    sect = rect(0.0009, bw)
    P = path[:, None, :] + sect[None, :, 0:1] * N[:, None, :] \
        + sect[None, :, 1:2] * B[:, None, :]
    V = P.reshape(-1, 3)
    Q = _grid_quads(m, 4, close_m=True)
    j = np.arange(4)
    Q = np.concatenate([Q, np.stack([(m - 1) * 4 + j, (m - 1) * 4 + (j + 1) % 4,
                                     (j + 1) % 4, j], 1)])
    acc.solid(V, quads=Q, mat=M_GALV,
              mpd_rust=rnd(0.10, 0.75, d.k, 4422, b["j"], sgn),
              mpd_wear=rnd(0.1, 0.6, d.k, 4423, b["j"]), mpd_age=b["age"],
              mpd_wet=d.wet, mpd_ao=0.35,
              mpd_id=h01(d.k, 4424, b["j"], sgn))
    # two nails through the band into the end grain
    for q in (-1, 1):
        vv = q * b["w"] * rnd(0.20, 0.32, d.k, 4425, b["j"], q)
        zz = float(board_top(d, b, np.array([uc]), np.array([vv]))[0]) + 0.0004
        xx, yy = _board_xy(d, b, uc, vv)
        p0 = np.array([xx, yy, zz - 0.002])
        p1 = np.array([xx, yy, zz + 0.0016])
        tube(acc, p0, p1, 0.0021, mat=M_GALV, n=8,
             mpd_rust=rnd(0.3, 0.95, d.k, 4426, b["j"], q), mpd_ao=0.4,
             mpd_age=b["age"], mpd_wet=d.wet)


# ================================================================================
#  8.  SHARED PARTS — the things every archetype is assembled from
# ================================================================================

def free_board(acc, acc_d, O, eu, ev, ez, L, w, t, seed, age=0.5, wear=0.0,
               mat=M_TIMBER, lod=1.0, tint=None, moss=0.0, wet=0.2, sawn=True,
               cup=None, bow=None, ao=0.3):
    """A board that is not part of the deck surface: toe board, spare, offcut.

    Same section, same arris, same grain and the same end grain as a deck
    board — because it is the same timber, and a stack of spares under the deck
    that does not match the deck above it is a tell.
    """
    O = np.asarray(O, float)
    eu = unit(eu)
    ev = unit(ev)
    ez = unit(ez)
    cup = rnd(-0.0014, 0.0026, seed, 51) if cup is None else cup
    bow = rnd(-0.0022, 0.0022, seed, 52) if bow is None else bow
    ch = 0.0010 + 0.0014 * age
    arrv = 0.0009 + 0.0022 * age + 0.0030 * wear
    U = stations(L, 0.017 / lod, ends=0.045)
    n = U.shape[0]
    arr = np.full(n, arrv)
    ntop = max(7, int(round((w - 0.005) / (0.0062 / lod))))
    VV, MODE, OFF = board_section(w, t, arr, ch, ntop)
    m = VV.shape[1]
    gseed = int(h01(seed, 53) * 90000)

    def _g(u, v):
        gg = fbm1(v * 62.0 + gseed, gseed, 3, 2.11, 0.46)
        return np.clip((gg - 0.42) * 2.4 + 0.5, 0.0, 1.0)

    def ztop(u, v):
        tt = np.clip(2.0 * u / max(L, 1e-9), -1, 1)
        z = t * 0.5 + cup * ((2.0 * v / max(w, 1e-9)) ** 2 - 1.0 / 3.0)
        z = z + bow * np.cos(math.pi * tt * 0.5)
        z = z + (0.00014 + 0.0007 * age) * (_g(u, v) - 0.45)
        z = z - wear * (0.0004 + 0.0016 * age) * (1.0 - 0.7 * _g(u, v))
        return z

    def zbot(u, v):
        tt = np.clip(2.0 * u / max(L, 1e-9), -1, 1)
        return (-t * 0.5 + cup * ((2.0 * v / max(w, 1e-9)) ** 2 - 1.0 / 3.0)
                + bow * np.cos(math.pi * tt * 0.5)
                - 0.0003 * n1(u * 22.0 + gseed, gseed + 41))

    def pt(u, v, z):
        return (O[None, None, :] + u[:, :, None] * eu[None, None, :]
                + v[:, :, None] * ev[None, None, :]
                + z[:, :, None] * ez[None, None, :])

    UU = np.broadcast_to(U[:, None], (n, m))
    endm = np.clip((np.abs(UU) - L * 0.5 + 0.05) / 0.05, 0, 1) * 0.5
    attrs = dict(mpd_wear=_flat(wear, n, m), mpd_age=_flat(age, n, m),
                 mpd_wet=_flat(wet, n, m), mpd_moss=_flat(moss, n, m),
                 mpd_rust=_flat(0.0, n, m), mpd_end=endm.ravel(),
                 mpd_paint=_flat(0.0, n, m), mpd_id=_flat(h01(seed, 54), n, m),
                 mpd_ao=_flat(ao, n, m), mpd_grit=_flat(0.0, n, m))
    ox, oy = board_grain_offset(seed, 55, 3)
    bc = np.stack([UU + ox, VV + oy, np.zeros_like(UU)], -1).reshape(-1, 3)
    if tint is None:
        tint = board_tint(seed, 55)
    return board_solid(acc, U, VV, MODE, OFF, ztop, zbot, pt, mat=mat,
                       attrs=attrs, bc=bc, tint=tint,
                       cap_over=dict(mpd_end=1.0 if sawn else 0.4,
                                     mpd_wear=0.0, mpd_ao=0.5))


def ground_beam(acc, d, p0, p1, w, top_z, mat=M_TIMBER, seed=0.0, h_min=0.045,
                embed=None, ch=0.002, lod=1.0, **attrs):
    """A member laid ON the ground with a LEVEL top: sleeper, bearer, sole board.

    The bottom follows `C.world_ground_z` through `Deck.gnd`, sunk by
    `BASE_EMBED_M` — law 5 — so it cannot open a lit gap under itself at a
    12.5 deg sun.  The gap it leaves at the high end is what the packing shims
    are for, and the shims are built because the gap is real.
    """
    embed = BASE_EMBED_M if embed is None else embed
    p0 = np.asarray(p0, float).ravel()
    p1 = np.asarray(p1, float).ravel()
    if p0.size == 2:
        p0 = np.array([p0[0], p0[1], 0.0])
    if p1.size == 2:
        p1 = np.array([p1[0], p1[1], 0.0])
    p0 = p0.copy(); p0[2] = 0.0
    p1 = p1.copy(); p1[2] = 0.0
    dvec = p1 - p0
    L = float(np.linalg.norm(dvec))
    eu = dvec / max(L, 1e-9)
    ev = np.array([-eu[1], eu[0], 0.0])
    ns = max(4, int(L / (0.06 / lod)) + 2)
    tt = np.linspace(0, 1, ns)
    X = p0[0] + dvec[0] * tt
    Y = p0[1] + dvec[1] * tt
    gz = d.gnd(X, Y) - embed
    zt = np.full(ns, float(top_z)) if np.ndim(top_z) == 0 else np.asarray(top_z, float)
    gz = np.minimum(gz, zt - h_min)
    vv = np.array([-w * 0.5 + ch, w * 0.5 - ch, w * 0.5, w * 0.5,
                   w * 0.5 - ch, -w * 0.5 + ch, -w * 0.5, -w * 0.5])
    m = 8
    Z = np.empty((ns, m))
    Z[:, 0] = gz
    Z[:, 1] = gz
    Z[:, 2] = gz + ch
    Z[:, 3] = zt - ch
    Z[:, 4] = zt
    Z[:, 5] = zt
    Z[:, 6] = zt - ch
    Z[:, 7] = gz + ch
    P = (p0[None, None, :] + (tt * L)[:, None, None] * eu[None, None, :]
         + vv[None, :, None] * ev[None, None, :])
    P[:, :, 2] = Z
    UU = np.broadcast_to((tt * L)[:, None], (ns, m))
    VV = np.broadcast_to(vv[None, :], (ns, m))
    dep = np.clip((zt[:, None] - Z) / max(0.001, float(np.max(zt - gz))), 0, 1)
    a = dict(mpd_wear=0.0, mpd_age=0.85, mpd_wet=np.clip(0.35 + 0.6 * dep, 0, 1).ravel(),
             mpd_moss=np.clip(0.25 + 0.7 * dep, 0, 1).ravel(), mpd_rust=0.0,
             mpd_end=0.0, mpd_paint=0.0, mpd_id=h01(seed, 61),
             mpd_ao=np.clip(0.3 + 0.65 * dep, 0, 1).ravel(), mpd_grit=0.0)
    a.update(attrs)
    return extrude(acc, P, mat=mat, caps=True,
                   bc=np.stack([UU, VV, np.zeros_like(UU)], -1).reshape(-1, 3),
                   cap_over=dict(mpd_end=1.0), **a)


def packer(acc, d, x, y, z_top, seed, w=0.11, l=0.14, mat=M_TIMBER, **attrs):
    """A shim under a bearer: an offcut, a flat stone or a folded piece of ply.

    Nobody builds a level deck on unlevel ground without them, and their absence
    is one of the things that makes generated geometry look drawn rather than
    built.
    """
    gz = float(d.gnd(x, y)) - BASE_EMBED_M
    if z_top - gz < 0.004:
        return
    n = max(1, int(round((z_top - gz) / rnd(0.010, 0.026, seed, 71))))
    z = gz
    for i in range(n):
        t = (z_top - gz) / n
        a = math.radians(rnd(0, 180, seed, 72, i))
        ex = np.array([math.cos(a), math.sin(a), 0.0]) * w * 0.5 * rnd(0.75, 1.15, seed, 73, i)
        ey = np.array([-math.sin(a), math.cos(a), 0.0]) * l * 0.5 * rnd(0.7, 1.2, seed, 74, i)
        obox(acc, (x + rnd(-0.012, 0.012, seed, 75, i),
                   y + rnd(-0.012, 0.012, seed, 76, i), z + t * 0.5),
             ex, ey, np.array([0.0, 0.0, t * 0.5]), mat=mat, chamfer=0.12,
             mpd_age=0.9, mpd_wet=0.6, mpd_moss=0.5, mpd_ao=0.8,
             mpd_id=h01(seed, 77, i), **attrs)
        z += t


def coupler(acc, ctr, ax1, ax2, r=0.0242, seed=0.0, **attrs):
    """A scaffold right-angle coupler: two half-shells, a boss and a nut.

    ~90 mm across and 56 px at the filmed distance.  It is the single most
    recognisable object on a scaffold and a smooth tube with no couplers reads
    as a handrail from a hardware shop.
    """
    ctr = np.asarray(ctr, float)
    ax1 = unit(ax1)
    ax2 = unit(ax2)
    for (ax, off) in ((ax1, -0.0), (ax2, 0.052)):
        c = ctr + unit(np.cross(ax1, ax2)) * off
        a = np.linspace(-2.3, 2.3, 11)
        sect = np.stack([np.cos(a) * (r + 0.0035), np.sin(a) * (r + 0.0035)], -1)
        sect2 = np.stack([np.cos(a[::-1]) * (r + 0.0004), np.sin(a[::-1]) * (r + 0.0004)], -1)
        ring = np.concatenate([sect, sect2])
        p0 = c - ax * 0.025
        p1 = c + ax * 0.025
        path = np.stack([p0 + (p1 - p0) * s for s in (0.0, 0.5, 1.0)])
        T, N, B = frames_along(path, up_hint=np.cross(ax1, ax2))
        P = (path[:, None, :] + ring[None, :, 0:1] * N[:, None, :]
             + ring[None, :, 1:2] * B[:, None, :])
        extrude(acc, P, mat=M_GALV, caps=True, mpd_rust=attrs.get("mpd_rust", 0.3),
                mpd_ao=0.5, mpd_id=h01(seed, 81, off), mpd_age=0.6,
                mpd_wet=attrs.get("mpd_wet", 0.3))
    # the bolt and its nut, on the side the shells open
    b = unit(np.cross(ax1, ax2))
    side = unit(np.cross(ax1, b))
    for sgn in (-1.0, 1.0):
        base = ctr + side * (r + 0.010) * sgn + b * 0.026
        tube(acc, base - b * 0.030, base + b * 0.006, 0.0055, mat=M_GALV, n=8,
             mpd_rust=0.45, mpd_ao=0.5, mpd_age=0.6)
        obox(acc, base + b * 0.010, side * 0.0085, unit(np.cross(side, b)) * 0.0085,
             b * 0.0055, mat=M_GALV, chamfer=0.18, mpd_rust=0.5, mpd_ao=0.5,
             mpd_age=0.6)


def weld_bead(acc, p0, p1, r=0.0032, seed=0.0, **attrs):
    """A fillet weld: a lumpy bead, not a chamfer.  8 px wide at 6 m."""
    p0 = np.asarray(p0, float)
    p1 = np.asarray(p1, float)
    L = float(np.linalg.norm(p1 - p0))
    n = max(4, int(L / 0.006))
    tt = np.linspace(0, 1, n)
    path = p0[None, :] + (p1 - p0)[None, :] * tt[:, None]
    sc = 1.0 + 0.30 * (n1(tt * L * 190.0 + seed, int(seed) + 3) - 0.5) * 2.0
    sweep(acc, path, circle(r, 7), mat=M_GALV, scale=sc,
          mpd_rust=attrs.get("mpd_rust", 0.5), mpd_ao=0.6, mpd_age=0.7,
          mpd_wet=attrs.get("mpd_wet", 0.3), mpd_id=h01(seed, 91))


def slab_grid(acc, x0, x1, y0, y1, ztop, t, mat=M_PLY, step=0.013, seed=0.0,
              attrs=None, attr_fn=None, bcs=1.0, tint=None):
    """A sheet: displaced top, flat-ish underside, four closed edges."""
    nx = max(3, int(round((x1 - x0) / step)) + 1)
    ny = max(3, int(round((y1 - y0) / step)) + 1)
    gx = np.linspace(x0, x1, nx)
    gy = np.linspace(y0, y1, ny)
    X, Y = np.meshgrid(gx, gy, indexing="ij")
    ZT = ztop(X, Y)
    ZB = ZT - t - 0.0004 * n1(X * 31.0 + seed, int(seed) + 7)
    NT = nx * ny
    V = np.concatenate([np.stack([X, Y, ZT], -1).reshape(-1, 3),
                        np.stack([X, Y, ZB], -1).reshape(-1, 3)])
    idx = np.arange(NT).reshape(nx, ny)
    # R2-179, THIRD SITE, AND THE WORST-BEHAVED OF THE THREE.
    #
    # `top` used to walk (i,j) -> (i,j+1) -> (i+1,j+1) -> (i+1,j): +y then +x,
    # so `cross(+y, +x) = -z` and the WALKING SURFACE FACED THE GROUND, with
    # `bot` (its reverse) facing up. Two of the four edge strips were wound
    # outward and two inward, which is what made this one so hard to see:
    #
    #   x = x0 strip   +y then -z -> -x   OUTWARD, correct
    #   x = x1 strip   +y then -z -> -x   INWARD
    #   y = y0 strip   +x then -z -> +y   INWARD
    #   y = y1 strip   +x then -z -> +y   OUTWARD, correct
    #
    # A mesh wound partly one way and partly the other has no meaningful
    # signed volume, and `Acc.solid` decides the orientation of the whole
    # slab from exactly that number, integrated about the WORLD ORIGIN. So
    # whether a hut floor came out right way up depended on WHERE IT STOOD.
    # Twenty-four of the twenty-five decks were flipped back by luck;
    # `MPD_Deck_05_hut`, whose floor sits at z = -1.03, was not, and it is
    # 1.513 m2 of walking surface facing down. That is not a defect that can
    # be found by reading one deck.
    #
    # Every face is now authored outward, so `solid` has a true volume to
    # judge and cannot change its mind about a slab because it moved.
    top = np.stack([idx[:-1, :-1].ravel(), idx[1:, :-1].ravel(),
                    idx[1:, 1:].ravel(), idx[:-1, 1:].ravel()], 1)
    bot = top[:, ::-1] + NT
    strips = []
    for (a, b, flip) in ((idx[0, :], idx[0, :] + NT, False),
                         (idx[-1, :], idx[-1, :] + NT, True),
                         (idx[:, 0], idx[:, 0] + NT, True),
                         (idx[:, -1], idx[:, -1] + NT, False)):
        q = np.stack([a[:-1], a[1:], b[1:], b[:-1]], 1)
        strips.append(q[:, ::-1] if flip else q)
    Q = np.concatenate([top, bot] + strips)
    a = dict(mpd_wear=0.0, mpd_age=0.5, mpd_wet=0.2, mpd_moss=0.0, mpd_rust=0.0,
             mpd_end=0.0, mpd_paint=0.0, mpd_id=h01(seed, 101), mpd_ao=0.2,
             mpd_grit=0.0)
    if attrs:
        a.update(attrs)
    # PER-VERTEX fields are computed on THIS function's own lattice.  The caller
    # cannot rebuild it: `int(w/step)+1` and `int(round(w/step))+1` differ by one
    # row often enough that the first build died on a 9072-vs-9184 broadcast.
    if attr_fn:
        for k, v in attr_fn(X, Y).items():
            a[k] = np.concatenate([np.asarray(v).ravel()] * 2)
    bc = np.concatenate([np.stack([X, Y, np.zeros_like(X)], -1).reshape(-1, 3)] * 2) * bcs
    return acc.solid(V, quads=Q, mat=mat, bc=bc, tint=tint, **a)


def chequer_patch(acc, d, cx, cy, w, l, seed, z_fn, lod=1.0):
    """A chequer-plate offcut screwed over the deck where a board gave way.

    The teardrops are 55 x 8 mm and stand 2 mm proud: 34 x 5 px, with a 9 mm
    cast shadow at the contract sun angle.  They are geometry.
    """
    a = math.radians(rnd(-4, 4, seed, 111))
    ex = np.array([math.cos(a), math.sin(a), 0.0])
    ey = np.array([-math.sin(a), math.cos(a), 0.0])
    zc = float(z_fn(cx, cy)) + 0.0022
    ctr = np.array([cx, cy, zc])
    obox(acc, ctr, ex * w * 0.5, ey * l * 0.5, np.array([0, 0, 0.0022]),
         mat=M_GALV, chamfer=0.10, mpd_rust=rnd(0.25, 0.8, seed, 112),
         mpd_wear=0.55, mpd_ao=0.35, mpd_age=0.7, mpd_id=h01(seed, 113))
    px = int(w / 0.052) + 1
    py = int(l / 0.046) + 1
    for i in range(px):
        for j in range(py):
            if (i + j) % 2 and chance(0.5, seed, 114, i, j):
                continue
            ox = -w * 0.5 + w * (i + 0.5) / px
            oy = -l * 0.5 + l * (j + 0.5) / py
            for q in range(2):
                th = a + math.radians(38.0 if q else -38.0)
                dx = np.array([math.cos(th), math.sin(th), 0.0])
                dy = np.array([-math.sin(th), math.cos(th), 0.0])
                c2 = ctr + ex * ox + ey * oy + (ex * 0.010 - ey * 0.008) * (1 if q else -1)
                c2 = c2 + np.array([0, 0, 0.0022 + 0.0010])
                obox(acc, c2, dx * 0.0265, dy * 0.0040,
                     np.array([0, 0, 0.0010]), mat=M_GALV, chamfer=0.30,
                     mpd_rust=rnd(0.2, 0.7, seed, 115, i, j, q),
                     mpd_wear=0.75, mpd_ao=0.2, mpd_age=0.7,
                     mpd_id=h01(seed, 116, i, j))
    for (sx, sy) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        p = ctr + ex * sx * (w * 0.5 - 0.022) + ey * sy * (l * 0.5 - 0.020)
        zs = np.array([-0.0055, -0.0010, 0.0, -0.0010, -0.0016])
        rs = np.array([0.0022, 0.0043, 0.0043, 0.0023, 0.0004])
        path = np.stack([np.full(5, p[0]), np.full(5, p[1]), p[2] + zs], -1)
        T, N, B = frames_along(path)
        P = np.empty((5, 9, 3))
        cc = circle(1.0, 9)
        for i in range(5):
            P[i] = path[i][None, :] + cc[:, 0:1] * rs[i] * N[i][None, :] \
                + cc[:, 1:2] * rs[i] * B[i][None, :]
        extrude(acc, P, mat=M_GALV, caps=True, mpd_rust=rnd(0.4, 0.95, seed, 117, sx, sy),
                mpd_ao=0.5, mpd_age=0.7, mpd_wear=0.4)


# ================================================================================
#  9.  THE FOUR ARCHETYPES
# ================================================================================

def build_platform(acc, d, lod=1.0):
    """kind 3 — scaffold: standards' bases, ledgers, transoms, couplers, boards,
    toe boards.  The deck the camera is closest to."""
    rt = TUBE_R
    bs = board_layout(d)
    zdeck = float(d.plane_z(0.0, 0.0))
    ztr = z_transom(d)                           # transom centreline
    zld = z_ledger(d)                            # ledger centreline, under it
    hw, hd = d.W * 0.5, d.D * 0.5
    # --- transoms: directly under the boards, at the bearer stations ---------
    for i, bu in enumerate(_bearers(d)):
        if d.axis == "x":
            p0 = np.array([bu, -hd - 0.02, ztr])
            p1 = np.array([bu, hd + 0.02, ztr])
            ax1 = np.array([0.0, 1.0, 0.0])
            cy = [-hd + rt * 2, hd - rt * 2]
            cps = [np.array([bu, c, zld]) for c in cy]
        else:
            p0 = np.array([-hw - 0.02, bu, ztr])
            p1 = np.array([hw + 0.02, bu, ztr])
            ax1 = np.array([1.0, 0.0, 0.0])
            cx = [-hw + rt * 2, hw - rt * 2]
            cps = [np.array([c, bu, zld]) for c in cx]
        tube(acc, p0, p1, rt, mat=M_GALV, n=14,
             mpd_rust=rnd(0.10, 0.55, d.k, 4500, i), mpd_ao=0.35,
             mpd_age=0.65, mpd_wet=d.wet, mpd_id=h01(d.k, 4501, i))
        for j, cp in enumerate(cps):
            coupler(acc, cp + np.array([0, 0, rt]), ax1,
                    np.array([1.0, 0.0, 0.0]) if d.axis == "y" else np.array([0.0, 1.0, 0.0]),
                    r=rt, seed=d.k + i * 3 + j, mpd_rust=rnd(0.2, 0.7, d.k, 4502, i, j),
                    mpd_wet=d.wet)
    # --- ledgers: parallel to the boards, between the standards --------------
    for i, sgn in enumerate((-1.0, 1.0)):
        if d.axis == "x":
            p0 = np.array([-hw - 0.09, sgn * (hd - rt * 2), zld])
            p1 = np.array([hw + 0.09, sgn * (hd - rt * 2), zld])
        else:
            p0 = np.array([sgn * (hw - rt * 2), -hd - 0.09, zld])
            p1 = np.array([sgn * (hw - rt * 2), hd + 0.09, zld])
        tube(acc, p0, p1, rt, mat=M_GALV, n=14,
             mpd_rust=rnd(0.10, 0.55, d.k, 4503, i), mpd_ao=0.3, mpd_age=0.65,
             mpd_wet=d.wet, mpd_id=h01(d.k, 4504, i))
    # --- the boards ----------------------------------------------------------
    for b in bs:
        build_deck_board(acc, d, b, lod=lod)
    # board clamps: the fitting that stops a scaffold board lifting, one every
    # few boards, and the only bright metal on the deck field itself
    for b in bs:
        if not chance(0.34, d.k, 4530, b["j"]):
            continue
        bu = _bearers(d)[0 if chance(0.5, d.k, 4531, b["j"]) else -1]
        cx, cy = _board_xy(d, b, bu, rnd(-0.2, 0.2, d.k, 4532, b["j"]) * b["w"])
        ztop = float(deck_top_z(d, cx, cy))
        ex = np.array([1.0, 0.0, 0.0]) if d.axis == "y" else np.array([0.0, 1.0, 0.0])
        ey = np.array([-ex[1], ex[0], 0.0])
        obox(acc, np.array([cx, cy, ztop + 0.0035]), ex * 0.026, ey * 0.011,
             np.array([0, 0, 0.0035]), mat=M_GALV, chamfer=0.20,
             mpd_rust=rnd(0.2, 0.85, d.k, 4533, b["j"]), mpd_wear=0.6,
             mpd_ao=0.35, mpd_age=0.6, mpd_wet=d.wet)
        # its leg, hooked down past the board edge onto the transom
        hx = cx + ey[0] * (b["w"] * 0.5 + 0.006)
        hy = cy + ey[1] * (b["w"] * 0.5 + 0.006)
        obox(acc, np.array([hx, hy, ztop - b["t"] * 0.5]), ex * 0.018,
             ey * 0.0022, np.array([0, 0, b["t"] * 0.5 + 0.010]), mat=M_GALV,
             chamfer=0.12, mpd_rust=rnd(0.3, 0.95, d.k, 4534, b["j"]),
             mpd_ao=0.6, mpd_age=0.65, mpd_wet=d.wet)
    # a plate over the board that failed
    if chance(0.36, d.k, 4505):
        bsel = bs[rint(0, len(bs) - 1, d.k, 4506)]
        cx, cy = _board_xy(d, bsel, rnd(-0.28, 0.28, d.k, 4507) * bsel["L"], 0.0)
        chequer_patch(acc, d, float(cx), float(cy), 0.30, 0.46, d.k + 17.0,
                      lambda x, y: deck_top_z(d, x, y), lod)
    # --- toe boards on every edge but the one you climb in at ----------------
    if d.toe:
        th = rnd(0.145, 0.160, d.k, 4510)
        tt = rnd(0.023, 0.028, d.k, 4511)
        for e in ("front", "back", "left", "right"):
            if e == d.acc_edge or (d.acc_edge == "back" and e == "back"):
                continue
            if e in ("front", "back"):
                y = (-1.0 if e == "front" else 1.0) * (d.Dd * 0.5 + tt * 0.5)
                O = np.array([0.0, y, float(d.plane_z(0.0, y)) + th * 0.5 - 0.004])
                eu = np.array([1.0, 0.0, 0.0])
                L = d.Wd + tt
            else:
                x = (-1.0 if e == "left" else 1.0) * (d.Wd * 0.5 + tt * 0.5)
                O = np.array([x, 0.0, float(d.plane_z(x, 0.0)) + th * 0.5 - 0.004])
                eu = np.array([0.0, 1.0, 0.0])
                L = d.Dd + tt
            ev = np.array([0.0, 0.0, 1.0])
            ez = np.cross(eu, ev)
            free_board(acc, d, O, eu, ev, ez, L, th, tt,
                       seed=d.k + 40 + "fblr".index(e[0]), age=d.age,
                       wear=0.35 * d.wear_amp, moss=d.moss * 0.5, wet=d.wet,
                       mat=M_TIMBER, lod=lod, ao=0.35)
            # toe-board clips
            for q in (-1.0, 1.0):
                cp = O + eu * (L * 0.5 - 0.10) * q
                obox(acc, cp - ez * (tt * 0.5 + 0.004) + np.array([0, 0, -th * 0.30]),
                     eu * 0.020, ev * 0.045, ez * 0.004, mat=M_GALV, chamfer=0.2,
                     mpd_rust=rnd(0.2, 0.8, d.k, 4512, e, q), mpd_ao=0.5,
                     mpd_age=0.6, mpd_wet=d.wet)
    # --- base plates and sole boards: this module's ground contact -----------
    for sc in column_sockets(d):
        x, y = sc["x"], sc["y"]
        so = sc["sole_board"]
        if so:
            ang = 0.0 if abs(x) > abs(y) else math.pi * 0.5
            ex = np.array([math.cos(ang), math.sin(ang), 0.0])
            p0 = np.array([x, y, 0.0]) - ex * so["w"] * 0.5
            p1 = np.array([x, y, 0.0]) + ex * so["w"] * 0.5
            top = float(d.gnd(x, y)) - BASE_EMBED_M + so["t"]
            ground_beam(acc, d, p0[:2], p1[:2], so["d"], top, mat=M_TIMBER,
                        seed=d.k + sc["i"], lod=lod, h_min=so["t"])
            pl = sc["base_plate"]
            obox(acc, np.array([x, y, top + pl["t"] * 0.5]),
                 np.array([pl["w"] * 0.5, 0, 0]), np.array([0, pl["d"] * 0.5, 0]),
                 np.array([0, 0, pl["t"] * 0.5]), mat=M_GALV, chamfer=0.06,
                 mpd_rust=rnd(0.3, 0.9, d.k, 4520, sc["i"]), mpd_ao=0.7,
                 mpd_age=0.75, mpd_wet=min(1.0, d.wet + 0.25))


def build_canopy(acc, d, lod=1.0):
    """kind 0 — a duckboard: bearers on the pad, boards nailed across, packers
    under the low ends, and the litter that collects between the boards."""
    bs = board_layout(d)
    zdeck = float(d.plane_z(0.0, 0.0))
    for i, bu in enumerate(_bearers(d)):
        if d.axis == "x":
            p0 = np.array([bu, -d.Dd * 0.5 - 0.03])
            p1 = np.array([bu, d.Dd * 0.5 + 0.03])
        else:
            p0 = np.array([-d.Wd * 0.5 - 0.03, bu])
            p1 = np.array([d.Wd * 0.5 + 0.03, bu])
        top = zdeck - d.bt - 0.001
        ground_beam(acc, d, p0, p1, rnd(0.094, 0.104, d.k, 4530, i), top,
                    mat=M_TIMBER, seed=d.k + i, lod=lod, h_min=0.042)
        for q in np.linspace(0.12, 0.88, 3):
            pq = p0 + (p1 - p0) * q
            packer(acc, d, float(pq[0]), float(pq[1]), top - 0.046, d.k + i * 5 + q,
                   mat=M_TIMBER)
    for b in bs:
        build_deck_board(acc, d, b, lod=lod)


def build_hut(acc, d, lod=1.0):
    """kind 1 — a hut floor: sleepers, joists, ply sheets, a worn doorway and a
    hatch.  Sheet material, so the topology is nothing like a board deck."""
    zdeck = float(d.plane_z(0.0, 0.0))
    jt = 0.047
    jh = 0.097
    zj = zdeck - d.bt
    nsl = max(2, int(round(d.Dd / 0.85)) + 1)
    for i in range(nsl):
        y = -d.Dd * 0.5 + d.Dd * i / (nsl - 1)
        ground_beam(acc, d, (-d.Wd * 0.5 - 0.02, y), (d.Wd * 0.5 + 0.02, y),
                    0.100, zj - jh, mat=M_TIMBER, seed=d.k + i, lod=lod,
                    h_min=0.050)
    njo = max(3, int(round(d.Wd / 0.40)) + 1)
    for i in range(njo):
        x = -d.Wd * 0.5 + d.Wd * i / (njo - 1)
        obox(acc, np.array([x, 0.0, zj - jh * 0.5]),
             np.array([jt * 0.5, 0, 0]), np.array([0, d.Dd * 0.5, 0]),
             np.array([0, 0, jh * 0.5]), mat=M_TIMBER, chamfer=0.03,
             mpd_age=0.75, mpd_wet=min(1.0, d.wet + 0.2), mpd_moss=d.moss * 0.4,
             mpd_ao=0.75, mpd_id=h01(d.k, 4540, i))
    # ply sheets
    joints = _sheet_joints(d)
    xs = [-d.Wd * 0.5] + sorted(j[0] for j in joints if j[2] == "x") + [d.Wd * 0.5]
    for i in range(len(xs) - 1):
        x0 = xs[i] + (d.gap * 0.5 if i else 0.0)
        x1 = xs[i + 1] - (d.gap * 0.5 if i < len(xs) - 2 else 0.0)

        def zt(X, Y, _d=d):
            return _sheet_top(_d, X, Y)

        at = dict(mpd_age=d.age, mpd_wet=float(d.wet),
                  mpd_moss=float(d.moss) * 0.25, mpd_ao=0.15,
                  mpd_id=h01(d.k, 4541, i))

        def afn(X, Y, _d=d):
            wr = _d.wear(X, Y)
            edge = np.clip(1.0 - np.minimum(
                np.abs(X - x0), np.abs(X - x1)) / 0.05, 0.0, 1.0)
            return dict(mpd_wear=wr, mpd_grit=edge * 0.35,
                        mpd_ao=0.15 + 0.5 * edge)

        slab_grid(acc, x0, x1, -d.Dd * 0.5, d.Dd * 0.5, zt, d.bt, mat=M_PLY,
                  step=0.013, seed=d.k + i, attrs=at, attr_fn=afn)
        # countersunk screws on the joist lines
        for jx in range(njo):
            sx = -d.Wd * 0.5 + d.Wd * jx / (njo - 1)
            if sx < x0 + 0.02 or sx > x1 - 0.02:
                continue
            nsy = max(3, int(d.Dd / 0.19))
            for jy in range(nsy):
                sy = -d.Dd * 0.5 + 0.05 + (d.Dd - 0.10) * jy / max(1, nsy - 1)
                zc = float(_sheet_top(d, np.array([sx]), np.array([sy]))[0])
                zs = np.array([-0.0050, -0.0009, 0.0, -0.0009, -0.0015])
                rs = np.array([0.0019, 0.0038, 0.0038, 0.0020, 0.00035])
                path = np.stack([np.full(5, sx), np.full(5, sy), zc + zs], -1)
                T, N, B = frames_along(path)
                cc = circle(1.0, 9)
                Pp = np.empty((5, 9, 3))
                for q in range(5):
                    Pp[q] = path[q][None, :] + cc[:, 0:1] * rs[q] * N[q][None, :] \
                        + cc[:, 1:2] * rs[q] * B[q][None, :]
                extrude(acc, Pp, mat=M_GALV, caps=True,
                        mpd_rust=rnd(0.2, 0.9, d.k, 4542, i, jx, jy),
                        mpd_ao=0.45, mpd_age=0.6, mpd_wet=d.wet)
    # threshold plate at the access edge, worn bright
    ax, ay = d._access_point()
    ex = np.array([1.0, 0.0, 0.0]) if d.acc_edge == "back" else np.array([0.0, 1.0, 0.0])
    ey = np.array([-ex[1], ex[0], 0.0])
    zt0 = float(deck_top_z(d, ax * 0.9, ay * 0.9))
    obox(acc, np.array([ax * 0.94, ay * 0.94, zt0 + 0.0016]), ex * 0.28,
         ey * 0.034, np.array([0, 0, 0.0016]), mat=M_GALV, chamfer=0.12,
         mpd_rust=0.25, mpd_wear=0.95, mpd_ao=0.3, mpd_age=0.6, mpd_wet=d.wet)


def build_stand(acc, d, lod=1.0):
    """kind 2 — an equipment stand: a welded RHS frame carrying open steel bar
    grating.  The one deck you can see the ground through from above, which is
    exactly why it needs to be bars and not a plane with a grid texture."""
    sq = 0.040
    zt = float(d.plane_z(0.0, 0.0))
    zbar = zt - d.bw                              # underside of the load bars
    zr = zbar - sq * 0.5
    hw, hd = d.Wd * 0.5, d.Dd * 0.5
    col = d.paint
    pa = dict(mpd_paint=1.0, mpd_rust=rnd(0.10, 0.55, d.k, 4600), mpd_ao=0.35,
              mpd_age=d.age, mpd_wet=d.wet)
    # perimeter rails
    for (p0, p1, i) in ((( -hw, -hd), (hw, -hd), 0), ((-hw, hd), (hw, hd), 1),
                        ((-hw, -hd), (-hw, hd), 2), ((hw, -hd), (hw, hd), 3)):
        a = np.array([p0[0], p0[1], zr])
        b = np.array([p1[0], p1[1], zr])
        ex = (b - a) * 0.5
        ey = np.array([-ex[1], ex[0], 0.0])
        ey = ey / max(np.linalg.norm(ey), 1e-9) * sq * 0.5
        obox(acc, (a + b) * 0.5, ex, ey, np.array([0, 0, sq * 0.5]), mat=M_PAINT,
             chamfer=0.06, tint=col, mpd_id=h01(d.k, 4601, i), **pa)
    # legs, sunk into the ground
    for (sx, sy) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        x = sx * (hw - sq * 0.5)
        y = sy * (hd - sq * 0.5)
        gz = float(d.gnd(x, y)) - BASE_EMBED_M
        obox(acc, np.array([x, y, (gz + zr) * 0.5]),
             np.array([sq * 0.5, 0, 0]), np.array([0, sq * 0.5, 0]),
             np.array([0, 0, (zr - gz) * 0.5]), mat=M_PAINT, chamfer=0.06,
             tint=col, mpd_id=h01(d.k, 4602, sx, sy), **pa)
        weld_bead(acc, (x - sq * 0.5, y, zr - sq * 0.5),
                  (x + sq * 0.5, y, zr - sq * 0.5), r=0.0030, seed=d.k + sx * 3 + sy)
        # a foot plate, embedded
        obox(acc, np.array([x, y, gz + 0.004]), np.array([0.055, 0, 0]),
             np.array([0, 0.055, 0]), np.array([0, 0, 0.004]), mat=M_PAINT,
             chamfer=0.10, tint=col, mpd_paint=0.7, mpd_rust=0.75, mpd_ao=0.8,
             mpd_age=0.9, mpd_wet=min(1.0, d.wet + 0.3))
    # --- the grating ---------------------------------------------------------
    A = d.Wd if d.axis == "x" else d.Dd
    B = d.Dd if d.axis == "x" else d.Wd
    pitch = d.bt + d.gap
    nb = max(3, int(B / pitch))
    off = (B - (nb - 1) * pitch) * 0.5 - B * 0.5
    for i in range(nb):
        c = off + i * pitch
        if d.axis == "x":
            a = np.array([-A * 0.5, c, zbar + d.bw * 0.5])
            ex = np.array([A * 0.5, 0, 0])
            ey = np.array([0, d.bt * 0.5, 0])
        else:
            a = np.array([c, -A * 0.5, zbar + d.bw * 0.5])
            ex = np.array([0, A * 0.5, 0])
            ey = np.array([d.bt * 0.5, 0, 0])
        obox(acc, a + ex, ex, ey, np.array([0, 0, d.bw * 0.5]), mat=M_GALV,
             chamfer=0.035, mpd_rust=rnd(0.05, 0.40, d.k, 4610, i),
             mpd_wear=0.55 if abs(c) < B * 0.25 else 0.25, mpd_ao=0.4,
             mpd_age=d.age, mpd_wet=d.wet, mpd_id=h01(d.k, 4611, i))
    # cross rods: 6 mm square, twisted, at 100 mm
    nr = max(3, int(A / 0.100))
    for i in range(nr):
        u = -A * 0.5 + (A / max(1, nr - 1)) * i
        ns = max(6, int(B / 0.012))
        tt = np.linspace(0, 1, ns)
        if d.axis == "x":
            path = np.stack([np.full(ns, u), -B * 0.5 + B * tt,
                             np.full(ns, zbar + d.bw - 0.004)], -1)
        else:
            path = np.stack([-B * 0.5 + B * tt, np.full(ns, u),
                             np.full(ns, zbar + d.bw - 0.004)], -1)
        sweep(acc, path, rect(0.0060, 0.0060), mat=M_GALV,
              roll=tt * B / 0.028 * 2.0 * math.pi,
              mpd_rust=rnd(0.05, 0.5, d.k, 4612, i), mpd_wear=0.35,
              mpd_ao=0.45, mpd_age=d.age, mpd_wet=d.wet)
    # banding bar at both ends of the panel, plus its welds
    for i, sgn in enumerate((-1.0, 1.0)):
        if d.axis == "x":
            ctr = np.array([sgn * A * 0.5, 0.0, zbar + d.bw * 0.5])
            ex = np.array([0.0035, 0, 0])
            ey = np.array([0, B * 0.5, 0])
        else:
            ctr = np.array([0.0, sgn * A * 0.5, zbar + d.bw * 0.5])
            ex = np.array([0, 0.0035, 0])
            ey = np.array([B * 0.5, 0, 0])
        obox(acc, ctr, ex, ey, np.array([0, 0, d.bw * 0.5]), mat=M_GALV,
             chamfer=0.05, mpd_rust=rnd(0.1, 0.6, d.k, 4613, i), mpd_wear=0.4,
             mpd_ao=0.4, mpd_age=d.age, mpd_wet=d.wet)
    if chance(0.55, d.k, 4620):
        chequer_patch(acc, d, rnd(-0.2, 0.2, d.k, 4621) * d.Wd,
                      rnd(-0.15, 0.15, d.k, 4622) * d.Dd, 0.34, 0.42,
                      d.k + 23.0, lambda x, y: d.plane_z(x, y), lod)


# ================================================================================
# 10.  WHAT IS STORED UNDER THE DECK  — the manifest asked for it by name
# ================================================================================

def st_sandbags(acc, d, it, lod=1.0):
    """Ballast bags, slumped.  Each one is its own shape: a bag that has been
    dropped is not a bag that has been stacked."""
    sd = it["seed"]
    n = rint(2, 5, sd, 1)
    z0 = float(d.gnd(it["x"], it["y"]))
    for i in range(n):
        a = math.radians(it["yaw"] + rnd(-40, 40, sd, 2, i))
        R = rnd(0.145, 0.185, sd, 3, i)
        H = rnd(0.055, 0.082, sd, 4, i)
        cx = it["x"] + rnd(-0.13, 0.13, sd, 5, i)
        cy = it["y"] + rnd(-0.10, 0.10, sd, 6, i)
        base = z0 - BASE_EMBED_M * 0.35 + i * H * rnd(0.72, 0.92, sd, 7, i)
        nu, nt = 22, 16
        u = np.linspace(0.02, 0.98, nu)
        th = np.arange(nt) * (2 * math.pi / nt)
        r = np.sin(np.pi * u) ** 0.48
        wob = 1.0 + 0.14 * (n2(u[:, None] * 6.0 + i, th[None, :] * 1.4, sd + i) - 0.5) * 2
        aa = (R * r)[:, None] * wob
        bb = (H * r)[:, None] * wob * (0.55 + 0.45 * np.abs(np.sin(th))[None, :])
        X = (u - 0.5)[:, None] * (R * 2.35) * np.ones((1, nt))
        Y = aa * np.cos(th)[None, :] * 0.92
        Z = bb * np.sin(th)[None, :]
        Z = np.maximum(Z, -H * 0.42)                       # slumped flat
        P = np.stack([X * math.cos(a) - Y * math.sin(a) + cx,
                      X * math.sin(a) + Y * math.cos(a) + cy,
                      Z + base + H * 0.44], -1)
        bcv = np.stack([np.broadcast_to(u[:, None], (nu, nt)) * 0.9,
                        np.broadcast_to(th[None, :], (nu, nt)) * 0.06,
                        np.zeros((nu, nt))], -1).reshape(-1, 3)
        extrude(acc, P, mat=M_WOVEN, caps=True, bc=bcv,
                tint=np.array([1.06 - 0.20 * h01(sd, 8, i), 1.0,
                               0.94 - 0.12 * h01(sd, 9, i)]),
                mpd_age=rnd(0.35, 0.95, sd, 10, i), mpd_wet=min(1.0, d.wet + 0.2),
                mpd_ao=0.65, mpd_moss=d.moss * 0.3, mpd_id=h01(sd, 11, i),
                mpd_wear=rnd(0.1, 0.5, sd, 12, i))


def st_hose(acc, d, it, lod=1.0):
    """A coiled hose.  Nothing says 'this place is used' like a coil of hose."""
    sd = it["seed"]
    z0 = float(d.gnd(it["x"], it["y"]))
    turns = rnd(2.6, 4.2, sd, 21)
    r0, r1 = rnd(0.075, 0.10, sd, 22), rnd(0.19, 0.25, sd, 23)
    dia = rnd(0.0115, 0.0155, sd, 24)
    ns = max(48, int(turns * 40))
    t = np.linspace(0, 1, ns)
    th = t * turns * 2 * math.pi + math.radians(it["yaw"])
    r = r0 + (r1 - r0) * t
    zz = z0 + dia * 0.5 + dia * 0.9 * np.floor(t * turns / 2.2) \
        + 0.002 * n1(t * 9.0 + sd, int(sd) + 1)
    path = np.stack([it["x"] + r * np.cos(th), it["y"] + r * np.sin(th), zz], -1)
    tail = path[-1] + np.array([math.cos(th[-1]) * 0.14, math.sin(th[-1]) * 0.10,
                                -dia * 0.2])
    path = np.concatenate([path, tail[None, :]])
    col = pick([P["poly_yellow"], P["poly_blue"], P["poly_green"], P["poly_red"]],
               sd, 25)
    sweep(acc, path, circle(dia * 0.5, 9), mat=M_POLY,
          tint=np.array(col) * 2.0, mpd_age=rnd(0.3, 0.9, sd, 26), mpd_wet=d.wet, mpd_ao=0.55,
          mpd_id=h01(sd, 27), mpd_wear=0.4)


def st_boardstack(acc, d, it, lod=1.0):
    """Spare boards, stacked flat where they stay dry-ish."""
    sd = it["seed"]
    z0 = float(d.gnd(it["x"], it["y"]))
    n = rint(2, 5, sd, 31)
    L = min(it["size"][0], d.Wd * 0.92)
    a = math.radians(it["yaw"])
    eu = np.array([math.cos(a), math.sin(a), 0.0])
    ev = np.array([-eu[1], eu[0], 0.0])
    z = z0 + 0.006
    for i in range(n):
        w = rnd(0.135, 0.230, sd, 32, i)
        t = rnd(0.028, 0.038, sd, 33, i)
        o = np.array([it["x"] + rnd(-0.05, 0.05, sd, 34, i),
                      it["y"] + rnd(-0.03, 0.03, sd, 35, i), z + t * 0.5])
        free_board(acc, d, o, eu, ev, np.array([0.0, 0.0, 1.0]),
                   L * rnd(0.85, 1.0, sd, 36, i), w, t, seed=sd + i,
                   age=rnd(0.4, 0.98, sd, 37, i), wear=0.05,
                   moss=d.moss * 0.6, wet=min(1.0, d.wet + 0.25), lod=lod * 0.55,
                   ao=0.7)
        z += t * rnd(1.0, 1.10, sd, 38, i)


def st_offcuts(acc, d, it, lod=1.0):
    sd = it["seed"]
    z0 = float(d.gnd(it["x"], it["y"]))
    for i in range(rint(2, 5, sd, 41)):
        a = math.radians(rnd(0, 180, sd, 42, i))
        eu = np.array([math.cos(a), math.sin(a), 0.0])
        ev = np.array([-eu[1], eu[0], 0.0])
        t = rnd(0.022, 0.040, sd, 43, i)
        free_board(acc, d, np.array([it["x"] + rnd(-0.16, 0.16, sd, 44, i),
                                     it["y"] + rnd(-0.12, 0.12, sd, 45, i),
                                     z0 + t * 0.5 - BASE_EMBED_M * 0.3]),
                   eu, ev, np.array([0.0, 0.0, 1.0]),
                   rnd(0.18, 0.62, sd, 46, i), rnd(0.07, 0.20, sd, 47, i), t,
                   seed=sd + 7 * i, age=rnd(0.5, 1.0, sd, 48, i), wear=0.0,
                   moss=min(1.0, d.moss + 0.25), wet=min(1.0, d.wet + 0.3),
                   lod=lod * 0.5, ao=0.8)


def st_slabs(acc, d, it, lod=1.0):
    sd = it["seed"]
    z0 = float(d.gnd(it["x"], it["y"]))
    z = z0 - BASE_EMBED_M * 0.5
    for i in range(rint(2, 4, sd, 51)):
        a = math.radians(it["yaw"] + rnd(-16, 16, sd, 52, i))
        t = rnd(0.032, 0.044, sd, 53, i)
        w = rnd(0.19, 0.30, sd, 54, i)
        l = rnd(0.19, 0.30, sd, 55, i)
        obox(acc, np.array([it["x"] + rnd(-0.03, 0.03, sd, 56, i),
                            it["y"] + rnd(-0.03, 0.03, sd, 57, i), z + t * 0.5]),
             np.array([math.cos(a), math.sin(a), 0.0]) * w,
             np.array([-math.sin(a), math.cos(a), 0.0]) * l,
             np.array([0, 0, t * 0.5]), mat=M_CONC, chamfer=0.05,
             mpd_age=rnd(0.5, 1.0, sd, 58, i), mpd_wet=min(1.0, d.wet + 0.3),
             mpd_moss=min(1.0, d.moss + 0.3), mpd_ao=0.7, mpd_id=h01(sd, 59, i))
        z += t


def st_stakes(acc, d, it, lod=1.0):
    """A bundle of marker stakes, tied.  Pointed, because they get driven in."""
    sd = it["seed"]
    z0 = float(d.gnd(it["x"], it["y"]))
    a = math.radians(it["yaw"])
    eu = np.array([math.cos(a), math.sin(a), 0.0])
    ev = np.array([-eu[1], eu[0], 0.0])
    n = rint(4, 8, sd, 61)
    L = rnd(0.75, 1.15, sd, 62)
    sq = 0.021
    for i in range(n):
        off = ev * rnd(-0.055, 0.055, sd, 63, i)
        lift = sq * (0.5 + (i // 3) * 0.95)
        c = np.array([it["x"], it["y"], z0 + lift]) + off
        pth = np.stack([c - eu * L * 0.5, c + eu * (L * 0.5 - 0.05),
                        c + eu * L * 0.5], 0)
        sweep(acc, pth, rect(sq, sq, 0.002), mat=M_TIMBER,
              scale=np.array([1.0, 0.85, 0.06]),
              mpd_age=rnd(0.4, 0.95, sd, 64, i), mpd_wet=min(1.0, d.wet + 0.2),
              mpd_moss=d.moss * 0.4, mpd_ao=0.7, mpd_id=h01(sd, 65, i))
    tp = np.array([it["x"], it["y"], z0 + sq * 1.0])
    ns = 26
    th = np.arange(ns) * (2 * math.pi / ns)
    ring = tp[None, :] + (np.cos(th)[:, None] * eu[None, :] * 0.075
                          + np.sin(th)[:, None] * ev[None, :] * 0.062
                          + np.sin(th * 2)[:, None] * np.array([0, 0, 0.004])[None, :])
    sweep(acc, ring, circle(0.0022, 6), mat=M_POLY, closed=True,
          mpd_age=0.8, mpd_ao=0.6, mpd_id=h01(sd, 66))


def st_jerrycan(acc, d, it, lod=1.0):
    sd = it["seed"]
    z0 = float(d.gnd(it["x"], it["y"]))
    a = math.radians(it["yaw"])
    ex = np.array([math.cos(a), math.sin(a), 0.0])
    ey = np.array([-math.sin(a), math.cos(a), 0.0])
    w, l, h = 0.165, 0.098, 0.315
    ctr = np.array([it["x"], it["y"], z0 + h * 0.5 - BASE_EMBED_M * 0.3])
    col = pick([P["poly_green"], P["poly_red"], P["poly_blue"]], sd, 71)
    tint = np.array(col) * 2.0
    obox(acc, ctr, ex * w * 0.5, ey * l * 0.5, np.array([0, 0, h * 0.5]),
         mat=M_POLY, chamfer=0.16, tint=tint, mpd_age=rnd(0.3, 0.9, sd, 72),
         mpd_wet=d.wet, mpd_ao=0.5, mpd_id=h01(sd, 73))
    for i in range(3):
        obox(acc, ctr + np.array([0, 0, (i - 1) * h * 0.24]),
             ex * (w * 0.5 + 0.003), ey * (l * 0.5 * 0.55),
             np.array([0, 0, 0.010]), mat=M_POLY, chamfer=0.35, tint=tint,
             mpd_age=0.6, mpd_ao=0.6, mpd_id=h01(sd, 74, i))
    tube(acc, ctr + np.array([0, 0, h * 0.5]), ctr + np.array([0, 0, h * 0.5 + 0.030]),
         0.024, mat=M_POLY, n=10, tint=tint * 0.7, mpd_age=0.5, mpd_ao=0.4)
    hp = np.stack([ctr + ex * w * 0.22 + np.array([0, 0, h * 0.5]),
                   ctr + ex * w * 0.22 + np.array([0, 0, h * 0.5 + 0.040]),
                   ctr - ex * w * 0.22 + np.array([0, 0, h * 0.5 + 0.040]),
                   ctr - ex * w * 0.22 + np.array([0, 0, h * 0.5])])
    sweep(acc, hp, rect(0.020, 0.011, 0.003), mat=M_POLY, tint=tint,
          mpd_age=0.6, mpd_ao=0.45)


def st_bucket(acc, d, it, lod=1.0):
    sd = it["seed"]
    z0 = float(d.gnd(it["x"], it["y"]))
    rb, rt_, h = 0.108, 0.142, 0.265
    tipped = chance(0.35, sd, 81)
    zs = np.array([0.0, 0.006, h * 0.5, h - 0.010, h, h - 0.004])
    rs = np.array([rb, rb + 0.002, (rb + rt_) * 0.5, rt_ - 0.001, rt_, rt_ - 0.012])
    path = np.stack([np.full(6, it["x"]), np.full(6, it["y"]),
                     z0 + zs - BASE_EMBED_M * 0.3], -1)
    if tipped:
        a = math.radians(it["yaw"])
        ex = np.array([math.cos(a), math.sin(a), 0.0])
        path = np.stack([np.array([it["x"], it["y"], z0 + rb]) + ex * (zz - h * 0.4)
                         + np.array([0, 0, 0.0]) for zz in zs])
    col = pick([P["poly_blue"], P["poly_green"], P["poly_red"]], sd, 82)
    ns = 14
    th = np.arange(ns) * (2 * math.pi / ns)
    T, N, B = frames_along(path)
    Pp = np.empty((6, ns, 3))
    for i in range(6):
        Pp[i] = path[i][None, :] + (np.cos(th)[:, None] * rs[i]) * N[i][None, :] \
            + (np.sin(th)[:, None] * rs[i]) * B[i][None, :]
    extrude(acc, Pp, mat=M_POLY, caps=True, tint=np.array(col) * 2.0,
            mpd_age=rnd(0.4, 0.95, sd, 83), mpd_wet=d.wet, mpd_ao=0.5,
            mpd_id=h01(sd, 84), mpd_wear=0.3)


def st_tarp(acc, d, it, lod=1.0):
    """A rolled tarpaulin, tied.  Folds, not a smooth cylinder."""
    sd = it["seed"]
    z0 = float(d.gnd(it["x"], it["y"]))
    a = math.radians(it["yaw"])
    eu = np.array([math.cos(a), math.sin(a), 0.0])
    L = rnd(0.62, 1.05, sd, 91)
    R = rnd(0.085, 0.125, sd, 92)
    ns = 26
    tt = np.linspace(0, 1, ns)
    path = np.stack([it["x"] + (tt - 0.5) * L * eu[0],
                     it["y"] + (tt - 0.5) * L * eu[1],
                     np.full(ns, z0 + R * 0.86 - BASE_EMBED_M * 0.3)], -1)
    nt = 20
    th = np.arange(nt) * (2 * math.pi / nt)
    lob = 1.0 + 0.11 * np.sin(th * 6.0 + 1.1) + 0.06 * np.sin(th * 11.0)
    T, N, B = frames_along(path)
    Pp = np.empty((ns, nt, 3))
    for i in range(ns):
        sc = R * (0.80 + 0.20 * math.sin(math.pi * min(1.0, max(0.0, tt[i]))) ** 0.4)
        sc = sc * (1.0 + 0.05 * (n1(np.array([tt[i] * 7.0 + sd]), int(sd) + 5)[0] - 0.5))
        rr = lob * sc
        Pp[i] = path[i][None, :] + (np.cos(th)[:, None] * rr[:, None] * 1.0) * N[i][None, :] \
            + (np.sin(th)[:, None] * rr[:, None] * 0.86) * B[i][None, :]
    Pp[:, :, 2] = np.maximum(Pp[:, :, 2], z0 - BASE_EMBED_M * 0.3)
    col = pick([P["tarp_blue"], P["tarp_green"]], sd, 93)
    extrude(acc, Pp, mat=M_TARP, caps=True, tint=np.array(col) * 2.0,
            mpd_age=rnd(0.3, 0.95, sd, 94), mpd_wet=d.wet, mpd_ao=0.55,
            mpd_id=h01(sd, 95), mpd_wear=0.25)
    for q in (-1, 1):
        c = path[int(ns * (0.5 + q * 0.28))]
        ring = c[None, :] + (np.cos(th)[:, None] * (R * 1.02) * np.array([0.0, 0.0, 1.0])[None, :]
                             + np.sin(th)[:, None] * (R * 0.90)
                             * np.cross(eu, np.array([0.0, 0.0, 1.0]))[None, :])
        sweep(acc, ring, circle(0.0028, 6), mat=M_POLY, closed=True,
              mpd_age=0.7, mpd_ao=0.6, mpd_id=h01(sd, 96, q))


STORE_FN = dict(sandbags=st_sandbags, hose=st_hose, boardstack=st_boardstack,
                offcuts=st_offcuts, slabs=st_slabs, stakes=st_stakes,
                jerrycan=st_jerrycan, bucket=st_bucket, tarp=st_tarp)


def gap_debris(acc, d, lod=1.0):
    """Grit, chippings and leaf litter lodged in the board gaps.

    A deck that has stood outdoors for a season has something in every gap.  At
    622 px/m a 4 mm stone is 2.5 px with a 9 mm cast shadow at the contract sun
    angle, so it is worth 80 triangles: it is the difference between a gap that
    reads as a slot in a real deck and one that reads as a modelled void.
    """
    if d.kind not in (0, 3):
        return
    bs = board_layout(d)
    V0, F0 = icosphere(1)
    A = d.Wd if d.axis == "x" else d.Dd
    n = 0
    for j in range(1, len(bs)):
        b0, b1 = bs[j - 1], bs[j]
        gc = (b0["c"] + b0["w"] * 0.5 + b1["c"] - b1["w"] * 0.5) * 0.5
        gw = (b1["c"] - b1["w"] * 0.5) - (b0["c"] + b0["w"] * 0.5)
        if gw < 0.0035:
            continue
        for q in range(rint(1, 5, d.k, 4700, j)):
            u = rnd(-0.46, 0.46, d.k, 4701, j, q) * A
            x, y = (u, gc) if d.axis == "x" else (gc, u)
            wr = float(d.wear(x, y))
            r = rnd(0.0016, 0.0042, d.k, 4702, j, q) * (1.0 + 0.5 * wr)
            r = min(r, gw * 0.44)
            zt = float(deck_top_z(d, x, y)) - rnd(0.004, 0.020, d.k, 4703, j, q)
            sx = np.array([r * rnd(0.8, 1.5, d.k, 4704, j, q), 0, 0])
            sy = np.array([0, r * rnd(0.7, 1.3, d.k, 4705, j, q), 0])
            sz = np.array([0, 0, r * rnd(0.5, 1.0, d.k, 4706, j, q)])
            a = math.radians(rnd(0, 360, d.k, 4707, j, q))
            ca, sa = math.cos(a), math.sin(a)
            Rz = np.array([[ca, -sa, 0], [sa, ca, 0], [0, 0, 1.0]])
            wob = 1.0 + 0.30 * (fbm2(V0[:, 0] * 2.4 + q, V0[:, 1] * 2.4 + j,
                                     int(d.k) + j * 7 + q, 2) - 0.5) * 2.0
            P = (V0 * wob[:, None]) @ np.stack([sx, sy, sz]) @ Rz.T \
                + np.array([x, y, zt])
            acc.solid(P, tris=F0, mat=M_CONC,
                      mpd_age=rnd(0.5, 1.0, d.k, 4708, j, q),
                      mpd_wet=min(1.0, d.wet + 0.3),
                      mpd_moss=min(1.0, d.moss + 0.2) * (1.0 - wr),
                      mpd_ao=0.85, mpd_id=h01(d.k, 4709, j, q))
            n += 1
    return n


def build_store(acc, d, lod=1.0):
    for it in store_layout(d):
        STORE_FN[it["what"]](acc, d, it, lod)


# ================================================================================
# 11.  MATERIALS — layered history, and not one image node anywhere
# ================================================================================
#
# THE COORDINATE LAW, and why this module obeys it twice over.  Law 6 forbids
# `Geometry->Position`: at |P| ~ 900 m a position-driven procedural loses all
# precision and blotches.  Every material here reads `TexCoord->Object`, which is
# local to the deck (|P| < 3.3 m) — and for anything with a GRAIN it reads
# `mpd_bc` instead, the part-local coordinate baked per vertex with x ALONG the
# grain.  That is strictly better than object space: a deck holds 14 boards at
# two orientations and one shared object-space wood texture would run the grain
# across half of them.

class NT(object):
    """Small node-graph DSL, the same shape as build_terrain's so they read alike."""

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
            # THE FIRST **ENABLED** OUTPUT, not output 0.  A `ShaderNodeMix` set
            # to RGBA has four Result sockets and only one of them is live; the
            # dead Float one is index 0, and linking it feeds a Principled's Base
            # Colour a number that has nothing to do with the colour chain.  That
            # is what made every surface render at ~0.5 albedo instead of the
            # 0.10-0.25 the palette specifies -- a blown-out macro that looks
            # like an exposure error and is a wiring error.
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


def mat_timber():
    """Weathered softwood, and what the last ten years did to it.

    Sixteen procedural textures over four bump scales.  Every mask that changes
    the COLOUR also changed the GEOMETRY: the silvering rides the same latewood
    field the raised grain was cut from, the traffic band that polishes the
    surface is the same `mpd_wear` that eroded it and opened its arris, and the
    iron bloom is centred on `mpd_grit`, which was baked from the actual fixing
    positions rather than from a noise that happens to fire nearby.

    The first version of this shader silvered EVERYTHING: `age` went straight
    into one mix toward a flat grey and the macro came back as beige plastic
    decking.  Weathering is patchy -- it follows the water, it stalls under the
    edge that shelters it, and the traffic band scrubs it off -- so the silver
    mask here is a field, not a number.
    """
    t = NT(PFX + "Timber")
    co = t.n("ShaderNodeTexCoord")
    bc = t.attr("mpd_bc")
    a_wear = t.attr("mpd_wear")
    a_age = t.attr("mpd_age")
    a_wet = t.attr("mpd_wet")
    a_moss = t.attr("mpd_moss")
    a_end = t.attr("mpd_end")
    a_ao = t.attr("mpd_ao")
    a_grit = t.attr("mpd_grit")
    tint = t.attr("mpd_tint")

    # ---- grain space: stretched 26:1 along the board -----------------------
    # THE SCALES, and the first build had all three wrong.  `bc` is in metres,
    # x along the grain.
    #   rings  a softwood growth ring is 3-9 mm across the board.  The first
    #          build put the wave at 21 cycles/m = 48 mm bands, which is a
    #          decking board from a garden centre.  62 matches the ring field
    #          the MESH relief was cut from; 178 adds the sub-millimetre banding
    #          the mesh cannot carry.
    #   knots  a knot is ~40-90 mm across and they come every 0.3-1.2 m ALONG a
    #          board.  The first build sampled voronoi in a space squashed 0.012
    #          in x, so a "knot" cell was 16 m long -- every knot was an endless
    #          streak and not one of them read as a knot.
    #   tone   a plank changes colour along its length.  There was no along-board
    #          field at all, so every board was a set of perfectly parallel
    #          stripes: printed, not grown.
    gm = t.mapping(bc, scale=(0.038, 1.0, 1.0))
    gm2 = t.mapping(bc, scale=(0.012, 0.55, 1.0))
    gk = t.mapping(bc, scale=(0.34, 1.0, 1.0))
    gt = t.mapping(bc, scale=(0.85, 0.85, 1.0))
    fine = t.mapping(bc, scale=(0.10, 3.4, 1.0))

    ring = t.wave(62.0, dist=2.6, detail=6.0, vec=gm, direction="Y")
    ring2 = t.wave(178.0, dist=1.7, detail=5.0, vec=gm, direction="Y")
    fib = t.noise(260.0, 12.0, 0.62, vec=fine, dist=0.4)
    med = t.noise(38.0, 9.0, 0.52, vec=gm2)
    broad = t.noise(2.4, 7.0, 0.55, vec=gm2, dist=0.4)
    tone = t.noise(1.7, 6.0, 0.52, vec=gt, dist=0.5)
    tone2 = t.noise(6.4, 8.0, 0.58, vec=gt, dist=0.7)
    knot = t.vor(3.2, "F1", vec=gk, rand=0.92)
    knotd = t.vor(3.2, "DISTANCE_TO_EDGE", vec=gk, rand=0.92)
    kmask = t.ramp((knotd, 0), [(0.00, (1, 1, 1)), (0.075, (0, 0, 0))])
    kfin = t.math("MULTIPLY", (kmask, 0), t.math("GREATER_THAN", (knot, 0), 0.72))

    latew = t.math("ADD", (ring, 0), t.math("MULTIPLY", (ring2, 0), 0.42))
    latew = t.math("MULTIPLY", latew, 0.70, clamp=True)

    # ---- the timber -------------------------------------------------------
    base = t.mix(latew, P["wood_fresh"], P["wood_late"])
    base = t.mix(t.math("MULTIPLY", (med, 0), 0.55), base, P["wood_mid"])
    base = t.mix(t.math("MULTIPLY", (fib, 0), 0.45), base, P["wood_late"])
    # the board changes colour along its length, and again in patches
    base = t.mix(t.math("MULTIPLY", (tone, 0), 0.62), base, P["wood_end"])
    base = t.mix(t.math("MULTIPLY", (tone2, 0), 0.30), base, P["wood_late"])
    base = t.mix(kfin, base, P["wood_knot"])
    base = t.mix(1.0, base, tint, blend="MULTIPLY")

    # ---- weathering, PATCHY: it follows the water and stalls in the lee ----
    patch = t.math("ADD", 0.18, t.math("MULTIPLY", (broad, 0), 1.55))
    silvf = t.math("MULTIPLY", (a_age, 2), patch, clamp=True)
    # ... and the traffic band scrubs it back off
    silvf = t.math("MULTIPLY", silvf,
                   t.math("SUBTRACT", 1.0, t.math("MULTIPLY", (a_wear, 2), 0.72)),
                   clamp=True)
    silv = t.mix((fib, 0), P["wood_silver"], P["wood_silver_d"])
    silv = t.mix(1.0, silv, tint, blend="MULTIPLY")
    weath = t.mix(silvf, base, silv)
    # silvered wood is still GRAIN: the latewood stays darker and harder
    weath = t.mix(t.math("MULTIPLY", latew, 0.42), weath,
                  t.mix(0.55, weath, P["wood_late"]))

    # ---- runoff streaks: dirt washes DOWN, in world z ----------------------
    streak = t.noise(30.0, 10.0, 0.65,
                     vec=t.mapping((co, "Object"), scale=(6.0, 6.0, 0.35)), dist=0.6)
    weath = t.mix(t.math("MULTIPLY", (streak, 0),
                         t.math("MULTIPLY", (a_wet, 2), 0.85)),
                  weath, (0.052, 0.043, 0.031))

    # ---- end grain: darker, thirstier, ringed ------------------------------
    endr = t.wave(150.0, dist=1.6, detail=3.0, vec=(co, "Object"), wtype="RINGS")
    endc = t.mix((endr, 0), P["wood_end"], P["wood_knot"])
    endc = t.mix(t.math("MULTIPLY", silvf, 0.7), endc, P["wood_silver_d"])
    col = t.mix((a_end, 2), weath, endc)

    # ---- iron staining round every fixing ----------------------------------
    gr = t.math("MULTIPLY", (a_grit, 2),
                t.math("ADD", 0.45, t.math("MULTIPLY", (med, 0), 0.9)))
    col = t.mix(t.math("MULTIPLY", gr, 0.85), col, (0.043, 0.029, 0.019))
    col = t.mix(t.math("MULTIPLY", gr,
                       t.math("MULTIPLY", (fib, 0), 0.55)), col, P["rust"])

    # ---- moss and algae: in the shade, on the edges, out of the traffic ----
    mo = t.noise(52.0, 9.0, 0.62, vec=(co, "Object"), dist=0.5)
    mo2 = t.vor(140.0, "F1", vec=(co, "Object"))
    mof = t.math("MULTIPLY", (a_moss, 2),
                 t.ramp((mo, 0), [(0.36, (0, 0, 0)), (0.66, (1, 1, 1))]))
    mof = t.math("MULTIPLY", mof,
                 t.math("SUBTRACT", 1.0, t.math("MULTIPLY", (a_wear, 2), 0.9)),
                 clamp=True)
    col = t.mix(mof, col, t.mix((mo2, 0), (0.026, 0.047, 0.021), (0.038, 0.058, 0.030)))

    # ---- damp darkens what it touches -------------------------------------
    col = t.mix(t.math("MULTIPLY", (a_wet, 2), 0.5), col,
                t.mix(0.62, col, P["wood_wet"]))

    # ---- dirt in the crevices ---------------------------------------------
    dirt = t.noise(24.0, 7.0, 0.6, vec=(co, "Object"))
    aof = t.math("MULTIPLY", (a_ao, 2),
                 t.math("ADD", 0.35, t.math("MULTIPLY", (dirt, 0), 0.6)))
    col = t.mix(t.math("MULTIPLY", aof, 0.66), col, (0.024, 0.021, 0.017))

    # ---- and the walked band, which is darker AND cleaner ------------------
    wpol = t.math("MULTIPLY", (a_wear, 2), (a_wear, 2))
    col = t.mix(t.math("MULTIPLY", wpol, 0.72), col,
                t.mix((fib, 0), (0.049, 0.040, 0.030), (0.082, 0.068, 0.051)))

    # ---- roughness ---------------------------------------------------------
    rough = t.fmix(silvf, 0.66, 0.90)
    rough = t.fmix(wpol, rough, 0.38)
    rough = t.math("SUBTRACT", rough, t.math("MULTIPLY", (a_wet, 2), 0.13), clamp=True)
    rough = t.math("ADD", rough, t.math("MULTIPLY", (fib, 0), 0.07), clamp=True)

    # ---- relief: fibre, raised grain, knots, and the fixing dish -----------
    graina = t.math("MULTIPLY", t.math("ADD", 0.25, t.math("MULTIPLY", (a_age, 2), 0.85)),
                    t.math("SUBTRACT", 1.0, t.math("MULTIPLY", (a_wear, 2), 0.62)),
                    clamp=True)
    b1 = t.bump((fib, 0), 0.55, 0.00075)
    b2 = t.bump(latew, graina, 0.0026, normal=b1)
    b2b = t.bump((ring2, 0), t.math("MULTIPLY", graina, 0.5), 0.0009, normal=b2)
    b3 = t.bump(kfin, 0.75, 0.0038, normal=b2b)
    b4 = t.bump((mo2, 0), t.math("MULTIPLY", (a_moss, 2), 0.5), 0.0011, normal=b3)

    bsdf = t.n("ShaderNodeBsdfPrincipled")
    t.pin(bsdf, "Base Color", (col, 2))
    t.pin(bsdf, "Roughness", rough)
    t.pin(bsdf, "Metallic", 0.0)
    t.pin(bsdf, "Normal", b4)
    t.out(bsdf)
    return t.m


def mat_ply():
    """WBP ply: face veneer, patched knots, and the core showing through where
    the face has been walked off."""
    t = NT(PFX + "Ply")
    co = t.n("ShaderNodeTexCoord")
    bc = t.attr("mpd_bc")
    a_wear = t.attr("mpd_wear")
    a_age = t.attr("mpd_age")
    a_wet = t.attr("mpd_wet")
    a_ao = t.attr("mpd_ao")
    gm = t.mapping(bc, scale=(0.055, 1.0, 1.0))
    gm2 = t.mapping(bc, scale=(0.9, 0.06, 1.0))
    face = t.wave(34.0, dist=2.6, detail=4.0, vec=gm, direction="Y")
    fib = t.noise(190.0, 11.0, 0.6, vec=gm, dist=0.35)
    patch = t.vor(7.5, "F1", vec=gm, rand=0.85)
    pmask = t.ramp((patch, 0), [(0.62, (0, 0, 0)), (0.70, (1, 1, 1))])
    core = t.wave(22.0, dist=1.2, detail=3.0, vec=gm2, direction="X")
    grime = t.noise(30.0, 8.0, 0.58, vec=(co, "Object"))

    base = t.mix((face, 0), P["ply_face"], t.mix(0.5, P["ply_face"], P["ply_core"]))
    base = t.mix((fib, 0), base, P["ply_glue"], blend="MULTIPLY")
    base = t.mix((pmask, 0), base, t.mix(0.4, P["ply_core"], P["wood_knot"]))
    wornf = t.math("MULTIPLY", (a_wear, 2), (a_wear, 2))
    worn = t.mix((core, 0), P["ply_core"], P["ply_glue"])
    col = t.mix(t.math("MULTIPLY", wornf, 0.92), base, worn)
    col = t.mix(t.math("MULTIPLY", (a_age, 2), 0.55), col,
                t.mix((fib, 0), P["wood_silver"], P["wood_silver_d"]))
    col = t.mix(t.math("MULTIPLY", (a_wet, 2), 0.5), col, (0.045, 0.033, 0.021))
    col = t.mix(t.math("MULTIPLY", (a_ao, 2),
                       t.math("ADD", 0.4, t.math("MULTIPLY", (grime, 0), 0.7))),
                col, (0.030, 0.026, 0.021))
    rough = t.fmix((a_wear, 2), 0.78, 0.42)
    rough = t.math("ADD", rough, t.math("MULTIPLY", (fib, 0), 0.07), clamp=True)
    b1 = t.bump((fib, 0), 0.22, 0.0007)
    b2 = t.bump((face, 0), 0.30, 0.0014, normal=b1)
    b3 = t.bump((pmask, 0), 0.35, 0.0016, normal=b2)
    bsdf = t.n("ShaderNodeBsdfPrincipled")
    t.pin(bsdf, "Base Color", (col, 2))
    t.pin(bsdf, "Roughness", rough)
    t.pin(bsdf, "Normal", b3)
    t.out(bsdf)
    return t.m


def mat_galv():
    """Hot-dip galvanising: spangle, white rust, zinc runs, red rust at the cuts."""
    t = NT(PFX + "Galv")
    co = t.n("ShaderNodeTexCoord")
    a_rust = t.attr("mpd_rust")
    a_wear = t.attr("mpd_wear")
    a_ao = t.attr("mpd_ao")
    a_wet = t.attr("mpd_wet")
    a_age = t.attr("mpd_age")
    sp = t.vor(190.0, "F1", vec=(co, "Object"), rand=1.0)
    spe = t.vor(190.0, "DISTANCE_TO_EDGE", vec=(co, "Object"), rand=1.0)
    run = t.noise(24.0, 9.0, 0.6, vec=t.mapping((co, "Object"), scale=(1.0, 1.0, 0.10)))
    wr = t.noise(58.0, 10.0, 0.62, vec=(co, "Object"), dist=0.5)
    rst = t.noise(38.0, 12.0, 0.66, vec=(co, "Object"), dist=0.8)
    rstf = t.noise(220.0, 10.0, 0.6, vec=(co, "Object"))
    base = t.mix((sp, 0), P["galv"], P["galv_dull"])
    base = t.mix(t.ramp((spe, 0), [(0.0, (1, 1, 1)), (0.09, (0, 0, 0))]),
                 base, P["galv_white"])
    base = t.mix(t.math("MULTIPLY", (run, 0), 0.45), base, P["galv_dull"])
    wrf = t.math("MULTIPLY", (a_wet, 2), t.math("MULTIPLY", (wr, 0), 1.6))
    base = t.mix(wrf, base, P["galv_white"])
    rmask = t.math("MULTIPLY", (a_rust, 2), None)
    t.pin(rmask, 1, t.ramp((rst, 0), [(0.34, (0, 0, 0)), (0.62, (1, 1, 1))]))
    rcol = t.mix((rstf, 0), P["rust"], P["rust_pale"])
    col = t.mix(rmask, base, rcol)
    col = t.mix(t.math("MULTIPLY", (a_wear, 2), 0.55), col, P["galv"])
    col = t.mix(t.math("MULTIPLY", (a_ao, 2), 0.4), col, (0.035, 0.031, 0.027))
    rough = t.fmix((sp, 0), 0.34, 0.52)
    rough = t.fmix(rmask, rough, 0.88)
    rough = t.fmix((a_wear, 2), rough, 0.21)
    metal = t.math("SUBTRACT", 1.0, t.math("MULTIPLY", rmask, 0.85), clamp=True)
    b1 = t.bump((spe, 0), 0.16, 0.0004)
    b2 = t.bump((rst, 0), t.math("MULTIPLY", (a_rust, 2), 0.7), 0.0011, normal=b1)
    bsdf = t.n("ShaderNodeBsdfPrincipled")
    t.pin(bsdf, "Base Color", (col, 2))
    t.pin(bsdf, "Roughness", rough)
    t.pin(bsdf, "Metallic", metal)
    t.pin(bsdf, "Normal", b2)
    t.out(bsdf)
    return t.m


def mat_paint():
    """Paint over primer over steel, chipping back to both."""
    t = NT(PFX + "Paint")
    co = t.n("ShaderNodeTexCoord")
    a_rust = t.attr("mpd_rust")
    a_wear = t.attr("mpd_wear")
    a_ao = t.attr("mpd_ao")
    a_age = t.attr("mpd_age")
    tint = t.attr("mpd_tint")
    chip = t.vor(120.0, "F1", vec=(co, "Object"), rand=1.0)
    chip2 = t.noise(85.0, 12.0, 0.68, vec=(co, "Object"), dist=1.1)
    chalk = t.noise(16.0, 8.0, 0.55, vec=(co, "Object"))
    rst = t.noise(60.0, 11.0, 0.64, vec=(co, "Object"), dist=0.6)
    dirt = t.noise(9.0, 7.0, 0.55, vec=t.mapping((co, "Object"), scale=(1, 1, 0.15)))
    pc = t.mix(1.0, (0.09, 0.10, 0.11), tint, blend="MULTIPLY")
    pc = t.mix(t.math("MULTIPLY", (chalk, 0), t.math("MULTIPLY", (a_age, 2), 0.55)),
               pc, (0.20, 0.20, 0.19))
    cmask = t.math("MULTIPLY", None, None)
    t.pin(cmask, 0, t.ramp((chip, 0), [(0.55, (0, 0, 0)), (0.74, (1, 1, 1))]))
    t.pin(cmask, 1, t.math("ADD", t.math("MULTIPLY", (a_age, 2), 0.8),
                           t.math("MULTIPLY", (a_wear, 2), 0.7)))
    cmask = t.math("MULTIPLY", cmask, t.ramp((chip2, 0), [(0.40, (0, 0, 0)), (0.60, (1, 1, 1))]))
    prim = t.mix((rst, 0), (0.150, 0.098, 0.052), (0.115, 0.075, 0.040))
    col = t.mix(cmask, pc, prim)
    rmask = t.math("MULTIPLY", (a_rust, 2), t.math("MULTIPLY", cmask, 1.4))
    col = t.mix(rmask, col, t.mix((rst, 0), P["rust"], P["rust_pale"]))
    col = t.mix(t.math("MULTIPLY", (dirt, 0), t.math("MULTIPLY", (a_ao, 2), 0.7)),
                col, (0.026, 0.024, 0.021))
    rough = t.fmix((a_age, 2), 0.36, 0.70)
    rough = t.fmix(cmask, rough, 0.85)
    rough = t.fmix((a_wear, 2), rough, 0.28)
    b1 = t.bump(cmask, 0.55, 0.0006)
    b2 = t.bump((rst, 0), t.math("MULTIPLY", rmask, 0.6), 0.0009, normal=b1)
    bsdf = t.n("ShaderNodeBsdfPrincipled")
    t.pin(bsdf, "Base Color", (col, 2))
    t.pin(bsdf, "Roughness", rough)
    t.pin(bsdf, "Metallic", t.math("MULTIPLY", cmask, 0.35))
    t.pin(bsdf, "Normal", b2)
    t.out(bsdf)
    return t.m


def mat_conc():
    t = NT(PFX + "Concrete")
    co = t.n("ShaderNodeTexCoord")
    a_wet = t.attr("mpd_wet")
    a_moss = t.attr("mpd_moss")
    a_ao = t.attr("mpd_ao")
    a_age = t.attr("mpd_age")
    agg = t.vor(95.0, "F1", vec=(co, "Object"), rand=0.95)
    agge = t.vor(95.0, "DISTANCE_TO_EDGE", vec=(co, "Object"), rand=0.95)
    void = t.vor(210.0, "F1", vec=(co, "Object"), rand=1.0)
    lait = t.noise(20.0, 9.0, 0.55, vec=(co, "Object"))
    stain = t.noise(5.5, 8.0, 0.6, vec=(co, "Object"), dist=0.7)
    col = t.mix((lait, 0), P["conc"], (0.196, 0.194, 0.186))
    col = t.mix(t.ramp((agge, 0), [(0.0, (1, 1, 1)), (0.06, (0, 0, 0))]),
                col, (0.145, 0.140, 0.132))
    col = t.mix(t.math("MULTIPLY", (agg, 0), 0.28), col, (0.265, 0.255, 0.240))
    col = t.mix(t.ramp((void, 0), [(0.80, (0, 0, 0)), (0.92, (1, 1, 1))]),
                col, (0.055, 0.053, 0.050))
    col = t.mix(t.math("MULTIPLY", (stain, 0), t.math("MULTIPLY", (a_age, 2), 0.7)),
                col, (0.105, 0.098, 0.086))
    col = t.mix(t.math("MULTIPLY", (a_wet, 2), 0.6), col, P["conc_wet"])
    col = t.mix(t.math("MULTIPLY", (a_moss, 2), 0.75), col, (0.030, 0.050, 0.026))
    col = t.mix(t.math("MULTIPLY", (a_ao, 2), 0.42), col, (0.032, 0.030, 0.027))
    rough = t.fmix((lait, 0), 0.80, 0.94)
    rough = t.math("SUBTRACT", rough, t.math("MULTIPLY", (a_wet, 2), 0.22), clamp=True)
    b1 = t.bump((agge, 0), 0.35, 0.0010)
    b2 = t.bump((void, 0), 0.30, 0.0016, normal=b1)
    bsdf = t.n("ShaderNodeBsdfPrincipled")
    t.pin(bsdf, "Base Color", (col, 2))
    t.pin(bsdf, "Roughness", rough)
    t.pin(bsdf, "Normal", b2)
    t.out(bsdf)
    return t.m


def mat_woven():
    """Polypropylene sack: a real weave, sun-faded, dusty."""
    t = NT(PFX + "Woven")
    co = t.n("ShaderNodeTexCoord")
    bc = t.attr("mpd_bc")
    a_age = t.attr("mpd_age")
    a_wet = t.attr("mpd_wet")
    a_ao = t.attr("mpd_ao")
    tint = t.attr("mpd_tint")
    m1 = t.mapping(bc, scale=(1.0, 1.0, 1.0))
    warp = t.wave(430.0, dist=0.6, detail=2.0, vec=m1, profile="SAW", direction="X")
    weft = t.wave(430.0, dist=0.6, detail=2.0, vec=m1, profile="SAW", direction="Y")
    fray = t.noise(150.0, 10.0, 0.62, vec=(co, "Object"))
    dust = t.noise(14.0, 8.0, 0.55, vec=(co, "Object"))
    wv = t.math("MULTIPLY", (warp, 0), (weft, 0))
    base = t.mix(1.0, (0.62, 0.56, 0.44), tint, blend="MULTIPLY")
    base = t.mix(t.math("MULTIPLY", (a_age, 2), 0.85), base, P["sand"])
    col = t.mix(t.math("MULTIPLY", wv, 0.55), base, (0.115, 0.098, 0.070))
    col = t.mix(t.math("MULTIPLY", (fray, 0), 0.30), col, P["sand_new"])
    col = t.mix(t.math("MULTIPLY", (dust, 0), 0.45), col, (0.155, 0.140, 0.115))
    col = t.mix(t.math("MULTIPLY", (a_wet, 2), 0.55), col, (0.055, 0.046, 0.033))
    col = t.mix(t.math("MULTIPLY", (a_ao, 2), 0.45), col, (0.028, 0.025, 0.021))
    b1 = t.bump(wv, 0.85, 0.0011)
    b2 = t.bump((fray, 0), 0.25, 0.0006, normal=b1)
    bsdf = t.n("ShaderNodeBsdfPrincipled")
    t.pin(bsdf, "Base Color", (col, 2))
    t.pin(bsdf, "Roughness", t.fmix((a_age, 2), 0.74, 0.92))
    t.pin(bsdf, "Normal", b2)
    t.out(bsdf)
    return t.m


def mat_poly():
    """Extruded plastic: hose, can, bucket.  Die lines, scuffs and dust."""
    t = NT(PFX + "Poly")
    co = t.n("ShaderNodeTexCoord")
    bc = t.attr("mpd_bc")
    a_age = t.attr("mpd_age")
    a_ao = t.attr("mpd_ao")
    a_wear = t.attr("mpd_wear")
    tint = t.attr("mpd_tint")
    die = t.wave(210.0, dist=0.4, detail=2.0, vec=t.mapping(bc, scale=(1, 8.0, 1)),
                 direction="X")
    scuff = t.noise(140.0, 11.0, 0.66, vec=(co, "Object"), dist=0.9)
    dust = t.noise(11.0, 8.0, 0.55, vec=(co, "Object"))
    uvd = t.noise(3.4, 6.0, 0.5, vec=(co, "Object"))
    base = t.mix(1.0, (0.5, 0.5, 0.5), tint, blend="MULTIPLY")
    base = t.mix(t.math("MULTIPLY", (uvd, 0), t.math("MULTIPLY", (a_age, 2), 0.75)),
                 base, t.mix(0.55, base, (0.24, 0.23, 0.21)))
    col = t.mix(t.math("MULTIPLY", (die, 0), 0.18), base, (0.35, 0.34, 0.32))
    col = t.mix(t.math("MULTIPLY", (scuff, 0), t.math("MULTIPLY", (a_wear, 2), 0.7)),
                col, (0.28, 0.27, 0.26))
    col = t.mix(t.math("MULTIPLY", (dust, 0), 0.42), col, (0.14, 0.13, 0.11))
    col = t.mix(t.math("MULTIPLY", (a_ao, 2), 0.4), col, (0.024, 0.023, 0.021))
    rough = t.fmix((a_age, 2), 0.32, 0.66)
    rough = t.math("ADD", rough, t.math("MULTIPLY", (scuff, 0), 0.12), clamp=True)
    b1 = t.bump((die, 0), 0.18, 0.0005)
    b2 = t.bump((scuff, 0), 0.22, 0.0004, normal=b1)
    bsdf = t.n("ShaderNodeBsdfPrincipled")
    t.pin(bsdf, "Base Color", (col, 2))
    t.pin(bsdf, "Roughness", rough)
    t.pin(bsdf, "Normal", b2)
    t.out(bsdf)
    return t.m


def mat_tarp():
    """Woven polytarp: a coarser weave than a sack, creased where it was folded."""
    t = NT(PFX + "Tarp")
    co = t.n("ShaderNodeTexCoord")
    bc = t.attr("mpd_bc")
    a_age = t.attr("mpd_age")
    a_ao = t.attr("mpd_ao")
    a_wet = t.attr("mpd_wet")
    tint = t.attr("mpd_tint")
    m1 = t.mapping(bc, scale=(1, 1, 1))
    warp = t.wave(300.0, dist=0.5, detail=2.0, vec=m1, profile="SAW", direction="X")
    weft = t.wave(300.0, dist=0.5, detail=2.0, vec=m1, profile="SAW", direction="Y")
    crease = t.noise(20.0, 10.0, 0.68, vec=(co, "Object"), dist=1.4)
    grime = t.noise(7.0, 8.0, 0.55, vec=(co, "Object"))
    wv = t.math("MULTIPLY", (warp, 0), (weft, 0))
    base = t.mix(1.0, (0.5, 0.5, 0.5), tint, blend="MULTIPLY")
    base = t.mix(t.math("MULTIPLY", (a_age, 2), 0.7), base,
                 t.mix(0.6, base, (0.30, 0.31, 0.30)))
    col = t.mix(t.math("MULTIPLY", wv, 0.5), base, (0.030, 0.045, 0.070))
    col = t.mix(t.math("MULTIPLY", (crease, 0), 0.35), col, (0.22, 0.22, 0.22))
    col = t.mix(t.math("MULTIPLY", (grime, 0), 0.5), col, (0.075, 0.070, 0.060))
    col = t.mix(t.math("MULTIPLY", (a_wet, 2), 0.4), col, (0.020, 0.026, 0.034))
    col = t.mix(t.math("MULTIPLY", (a_ao, 2), 0.45), col, (0.020, 0.020, 0.020))
    b1 = t.bump(wv, 0.70, 0.0013)
    b2 = t.bump((crease, 0), 0.40, 0.0026, normal=b1)
    bsdf = t.n("ShaderNodeBsdfPrincipled")
    t.pin(bsdf, "Base Color", (col, 2))
    t.pin(bsdf, "Roughness", t.fmix((a_age, 2), 0.52, 0.80))
    t.pin(bsdf, "Normal", b2)
    t.out(bsdf)
    return t.m


def build_materials():
    fns = [mat_timber, mat_ply, mat_galv, mat_paint, mat_conc, mat_woven,
           mat_poly, mat_tarp]
    return [f() for f in fns]


# ================================================================================
# 12.  BUILD
# ================================================================================

BUILDER = {0: build_canopy, 1: build_hut, 2: build_stand, 3: build_platform}


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
    """Emit the item into the ``ITEM_MARSHAL_POST_DECK`` collection.

    One object per deck, named ``MPD_Deck_<nn>_<archetype>``, recentred on its
    own site: the mesh is local (|P| < 3.3 m) and the object matrix carries the
    up-to-900 m out to the circuit.  That is law 6, and it is also why the
    materials can read ``TexCoord->Object`` at all.
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
        acc = Acc("%sDeck_%02d_%s" % (PFX, d.n, d.arch))
        BUILDER[d.kind](acc, d, lod)
        gap_debris(acc, d, lod)
        build_store(acc, d, lod)
        ob, st = acc.build(root, mats, d.R, d.O)
        ob["item"] = ITEM
        ob["post"] = d.n
        ob["archetype"] = d.arch
        ob["deck_H_m"] = round(float(d.H), 4)
        ob["board_gap_m"] = round(float(d.gap), 4)
        ob["stored_under"] = ",".join(d.store) if d.store else ""
        tot["objects"] += 1
        placed.append((ob, d.O))
        for k in ("verts", "triangles", "parts"):
            tot[k] += st[k]
        log("deck %2d %-8s  H %.3f m  %5d parts  %7d tris  gap %4.1f mm  under: %s"
            % (d.n, d.arch, d.H, st["parts"], st["triangles"], d.gap * 1000,
               ",".join(d.store) or "-"))
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
# 13.  CONTEXT — clearly NOT this item, and excluded from the gate by prefix
# ================================================================================
#
# The gate is run with `--prefix MPD_`.  Everything below is prefixed `CTX_` and
# is therefore invisible to it, which is the point: a deck rendered floating in a
# void cannot be judged, and a deck rendered on borrowed ground must not be
# credited with it.  The columns here are STUBS standing in for
# `marshal_post_column`, built to this module's own `column_sockets()`.

def mat_ctx_ground():
    t = NT(CTX + "Ground")
    co = t.n("ShaderNodeTexCoord")
    n1_ = t.noise(2.6, 9.0, 0.58, vec=(co, "Object"))
    n2_ = t.noise(19.0, 11.0, 0.62, vec=(co, "Object"), dist=0.6)
    n3_ = t.noise(120.0, 12.0, 0.6, vec=(co, "Object"))
    v = t.vor(46.0, "F1", vec=(co, "Object"))
    col = t.mix((n1_, 0), (0.062, 0.052, 0.035), (0.105, 0.086, 0.056))
    col = t.mix((n2_, 0), col, (0.040, 0.048, 0.022))
    col = t.mix(t.math("MULTIPLY", (v, 0), 0.35), col, (0.135, 0.120, 0.098))
    b = t.bump((n3_, 0), 0.5, 0.004)
    b = t.bump((v, 0), 0.35, 0.010, normal=b)
    bs = t.n("ShaderNodeBsdfPrincipled")
    t.pin(bs, "Base Color", (col, 2))
    t.pin(bs, "Roughness", t.fmix((n2_, 0), 0.82, 0.96))
    t.pin(bs, "Normal", b)
    t.out(bs)
    return t.m


def ctx_ground(coll, d, radius=13.0, cell=0.10, mat=None, far=0.0):
    """A patch of contract-datum ground under one deck, for shadows and scale.

    `far` grows the patch out to the horizon in expanding square rings that
    SHARE the boundary vertices of the ring inside them, so there is no crack.
    Without it the ground stops at `radius` and the frame above that edge is the
    sky texture's below-horizon direction, which is pure black -- a hard black
    band across the top third of the first macro render.
    """
    nn = int(radius * 2 / cell) + 1
    g = np.linspace(-radius, radius, nn)
    X, Y = np.meshgrid(g, g, indexing="ij")
    Z = d.gnd(X, Y)
    Z = Z + 0.012 * (fbm2(X * 1.7, Y * 1.7, 91, 4) - 0.5) \
        + 0.004 * (fbm2(X * 9.0, Y * 9.0, 92, 3) - 0.5)
    V = np.stack([X, Y, Z], -1).reshape(-1, 3)
    idx = np.arange(nn * nn).reshape(nn, nn)
    # wound so the normal is UP.  The first version had it the other way and the
    # whole lower two thirds of the macro render came back pure black: a lambert
    # surface whose shading normal points at the ground receives no sun.
    Q = np.stack([idx[:-1, :-1].ravel(), idx[1:, :-1].ravel(),
                  idx[1:, 1:].ravel(), idx[:-1, 1:].ravel()], 1)
    if far > radius:
        # the boundary loop of the fine patch, counter-clockwise
        loop = np.concatenate([idx[0, :-1], idx[:-1, -1], idx[-1, :0:-1],
                               idx[-1:0:-1, 0]])
        rr = radius
        Vl = [V]
        base = nn * nn
        prev = loop
        pxy = V[loop, :2].copy()
        while rr < far:
            # gently at first: a ring that jumps 1.7x leaves 10 m long radial
            # quads at 15 m out, and flat-shaded 10 m quads read as a fan of
            # streaks converging on the deck in the macro frame.
            rr = min(far, rr * (1.22 if rr < radius * 4.0 else 1.85))
            sc = rr / max(np.max(np.abs(pxy)), 1e-9)
            nxy = pxy * sc
            nz = d.gnd(nxy[:, 0], nxy[:, 1])
            nz = nz + 0.012 * (fbm2(nxy[:, 0] * 1.7, nxy[:, 1] * 1.7, 91, 4) - 0.5) \
                + 0.09 * (fbm2(nxy[:, 0] * 0.06, nxy[:, 1] * 0.06, 93, 4) - 0.5) \
                * np.clip(rr / 40.0, 0.0, 1.0)
            Vl.append(np.stack([nxy[:, 0], nxy[:, 1], nz], -1))
            k = len(prev)
            cur = base + np.arange(k)
            j = np.arange(k)
            j1 = (j + 1) % k
            Q = np.concatenate([Q, np.stack([prev[j], prev[j1], cur[j1], cur[j]], 1)])
            base += k
            prev = cur
            pxy = nxy
        V = np.concatenate(Vl)
    me = bpy.data.meshes.new("%sGround_%02d" % (CTX, d.n))
    me.from_pydata(V.tolist(), [], Q.tolist())
    me.update()
    ob = bpy.data.objects.new("%sGround_%02d" % (CTX, d.n), me)
    ob.data.materials.append(mat or mat_ctx_ground())
    coll.objects.link(ob)
    place(ob, d.R, d.O)
    return ob


def ctx_columns(coll, d, mats):
    """Stubs standing in for `marshal_post_column`, on this deck's own sockets."""
    acc = Acc("%sColumn_%02d" % (CTX, d.n))
    for sc in column_sockets(d):
        x, y = sc["x"], sc["y"]
        z0 = sc["ground_z"] if d.kind != 3 else (
            sc["ground_z"] - BASE_EMBED_M + sc["sole_board"]["t"] + sc["base_plate"]["t"])
        z1 = float(d.plane_z(x, y)) + (d.Hh if sc["role"] != "rail" else 1.30)
        if sc["kind"] == "tube":
            tube(acc, (x, y, z0), (x, y, z1), sc["size"] * 0.5, mat=M_GALV, n=14,
                 mpd_rust=0.3, mpd_ao=0.3, mpd_age=0.6, mpd_wet=d.wet)
        else:
            obox(acc, np.array([x, y, (z0 + z1) * 0.5]),
                 np.array([sc["size"] * 0.5, 0, 0]),
                 np.array([0, sc["size"] * 0.5, 0]),
                 np.array([0, 0, (z1 - z0) * 0.5]), mat=M_PAINT, chamfer=0.05,
                 tint=np.array(d.paint) / max(max(d.paint), 1e-6),
                 mpd_paint=1.0, mpd_rust=0.3, mpd_ao=0.3, mpd_age=0.6)
    ob, _ = acc.build(coll, mats, d.R, d.O)
    return ob


# ================================================================================
# 14.  LIGHT — world_contract §13, not a rounded copy of it
# ================================================================================

def contract_light(scene=None, coll=None):
    """The film's sun and sky exactly as `world_contract` measured them:
    12.471 deg elevation, bearing -57.970 deg, AgX at -3.048 EV."""
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
    bg.inputs["Strength"].default_value = 1.0
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
    cd.clip_start = 0.01
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
    """The deck the macro camera is put on: the biggest platform with a full
    underdeck, which is the archetype the manifest's own note is about."""
    best, bs = None, -1e9
    for d in plan():
        sc = (d.Wd * d.Dd) + 2.0 * (d.kind == 3) + 0.6 * len(d.store) \
            + 0.8 * d.H + 90.0 * d.gap
        if sc > bs:
            best, bs = d, sc
    return best


def macro_camera(d, cams, name=PFX + "CAM_MACRO", low=False):
    """Placed at EXACTLY the manifest's 6.0 m on EXACTLY its 35 mm lens.

    The bearing is derived, not chosen by eye: the camera stands on the TRACK
    side, because that is the face a marshal post presents to the circuit and
    the only side the film ever sees, and its azimuth is picked so the contract
    sun (12.471 deg elevation) rakes ACROSS the boards.  At that elevation a
    0.8 mm raised grain ridge throws a 3.6 mm shadow and a 12 mm board gap
    throws 54 mm of it; light down the boards would hide both.
    """
    Wl = float(d.Wd)
    tgt_l = np.array([Wl * 0.06, -d.Dd * 0.16, float(d.plane_z(0.0, 0.0)) + 0.06])
    tgt = tgt_l @ d.R.T + d.O
    ax = math.atan2(d.R[1, 0], d.R[0, 0])            # local +x azimuth in world
    sun_az = math.atan2(C.SUN_DIR[1], C.SUN_DIR[0])
    best, bq = None, -1e9
    for deg in np.arange(-168.0, -12.0, 2.0):        # camera on the -y (track) side
        th = math.radians(deg)
        view_az = ax + th + math.pi                  # camera -> target
        off = abs(((view_az - sun_az + math.pi) % (2 * math.pi)) - math.pi)
        q = -abs(math.degrees(off) - 96.0) - 0.35 * abs(deg + 90.0) * 0.25
        if q > bq:
            best, bq = th, q
    # 19.5 deg, not 13.5: at 13.5 deg a 12 mm gap between 38 mm boards is
    # completely occluded by the board in front of it (you need 17.5 deg to see
    # the bottom of one), so the deck read as a continuous plane with lines
    # drawn on it -- the exact "flat cardboard" the manifest rejected.
    el = math.radians(6.5 if low else 19.5)
    cam_l = tgt_l + np.array([math.cos(best) * FILMED_AT_M * math.cos(el),
                             math.sin(best) * FILMED_AT_M * math.cos(el),
                             FILMED_AT_M * math.sin(el)])
    if low:
        cam_l[2] = float(d.gnd(cam_l[0], cam_l[1])) + 0.42
        v = cam_l - tgt_l
        v = v / np.linalg.norm(v) * FILMED_AT_M
        cam_l = tgt_l + v
    cam = cam_l @ d.R.T + d.O
    ob = add_camera(name, tuple(cam), tuple(tgt), LENS_MM, cams)
    dist = float(np.linalg.norm(cam - tgt))
    view_az = ax + best + math.pi
    off = math.degrees(abs(((view_az - sun_az + math.pi) % (2 * math.pi)) - math.pi))
    log("%s: %.4f m from the deck on a %.0f mm lens (manifest: %.1f m / %.0f mm), "
        "sun %.1f deg off axis, camera %.3f m over the deck"
        % (name, dist, LENS_MM, FILMED_AT_M, LENS_MM, off, cam[2] - tgt[2]))
    return ob


def test_scene(lod=1.0, samples=256, which=None, context=True):
    """Build the item, light it with the contract sun, and put the manifest's
    own camera on it: 6.0 m, 35 mm — the shot this item has to survive."""
    scene = bpy.context.scene
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    root = build(which=which, lod=lod, scene=scene)
    cams = _coll(COLL + "_Cameras", root)
    contract_light(scene, coll=root)
    d = hero_deck() if which is None else [x for x in plan() if x.n in set(which)][0]
    if context:
        ctxc = _coll(COLL + "_Context", root)
        mats = [m for m in bpy.data.materials if m.name.startswith(PFX)]
        gm = mat_ctx_ground()
        for dd in ([x for x in plan() if x.n in set(which)] if which else plan()):
            ctx_columns(ctxc, dd, mats)
            ctx_ground(ctxc, dd, radius=(15.0 if dd is d else 7.0),
                       cell=(0.045 if dd is d else 0.35), mat=gm,
                       far=(2400.0 if dd is d else 0.0))
    macro = macro_camera(d, cams)
    macro_camera(d, cams, name=PFX + "CAM_UNDER", low=True)
    # a wider look so the deck can be judged in its setting
    ax = math.atan2(d.R[1, 0], d.R[0, 0])
    tl = np.array([0.0, 0.0, float(d.plane_z(0, 0))])
    cl = tl + np.array([math.cos(math.radians(-118.0)) * 9.5,
                        math.sin(math.radians(-118.0)) * 9.5, 3.1])
    add_camera(PFX + "CAM_WIDE", tuple(cl @ d.R.T + d.O), tuple(tl @ d.R.T + d.O),
               35.0, cams)
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
    log("hero deck: post %d, %s, %.2f x %.2f m, H %.3f m, under: %s"
        % (d.n, d.arch, d.Wd, d.Dd, d.H, ",".join(d.store) or "-"))
    return root


# ================================================================================
# 15.  MEASUREMENT — measure the claims, do not assert them
# ================================================================================

def selftest(verbose=True):
    """Every number the header claims, measured.  Needs numpy only."""
    ok = [True]

    def chk(label, cond, detail=""):
        ok[0] &= bool(cond)
        if verbose:
            print("  [%s] %-56s %s" % ("PASS" if cond else "FAIL", label, detail))

    ds = plan()
    chk("25 decks, one per marshal post", len(ds) == INSTANCES,
        "%d" % len(ds))
    ss = sorted(d.s for d in ds)
    gaps = [(ss[(i + 1) % len(ss)] - s) % C.LAP for i, s in enumerate(ss)]
    chk("max gap matches the manifest's 253.9 m", abs(max(gaps) - 253.9) < 0.15,
        "%.1f m" % max(gaps))
    kinds = {k: sum(1 for d in ds if d.kind == k) for k in range(4)}
    chk("all four archetypes present", min(kinds.values()) >= 1, str(kinds))

    # --- law 5: everything that touches ground is embedded ------------------
    worst = 1e9
    worst_at = ""
    for d in ds:
        for sc in column_sockets(d):
            if d.kind == 3:
                emb = sc["ground_z"] - sc["sole_board"]["z"]
            else:
                emb = sc["ground_z"] - sc["base_plate"]["z"]
            if emb < worst:
                worst, worst_at = emb, "post %d" % d.n
    chk("ground contacts embed >= BASE_EMBED_M", worst >= BASE_EMBED_M - 2e-5,
        "min %.4f m at %s (need %.3f)" % (worst, worst_at, BASE_EMBED_M))

    # --- the datum: never assumed ------------------------------------------
    dz = []
    for d in ds:
        z, own = C.world_ground_z(np.array([d.wx]), np.array([d.wy]))
        dz.append(abs(float(z[0]) - d.gz))
    chk("site z == C.world_ground_z at the site", max(dz) < 1e-4,
        "max |dz| %.6f m" % max(dz))

    # --- the surface is not the plane --------------------------------------
    lo, hi = 1e9, -1e9
    for d in ds:
        g = np.linspace(-0.42, 0.42, 21)
        X, Y = np.meshgrid(g * d.Wd, g * d.Dd, indexing="ij")
        dd = deck_top_z(d, X.ravel(), Y.ravel()) - d.plane_z(X.ravel(), Y.ravel())
        lo = min(lo, float(dd.min()))
        hi = max(hi, float(dd.max()))
    chk("deck_top_z departs from the nominal plane", (hi - lo) > 0.004,
        "%.1f .. %+.1f mm about the plane" % (lo * 1000, hi * 1000))

    # --- variation is in the geometry, not the transform --------------------
    sig = set()
    for d in ds:
        bs = board_layout(d) if d.kind in (0, 3) else []
        sig.add((d.kind, len(bs), round(d.Wd, 3), round(d.Dd, 3), round(d.H, 3),
                 round(d.gap, 4), d.axis, tuple(d.store)))
    chk("every deck is a different build", len(sig) == len(ds),
        "%d distinct signatures / %d decks" % (len(sig), len(ds)))
    hs = [d.H for d in ds]
    cv = float(np.std(hs) / np.mean(hs))
    chk("height above grade varies (gate needs cv_size >= 0.03)", cv >= 0.03,
        "cv %.3f, %.3f .. %.3f m" % (cv, min(hs), max(hs)))
    gapmm = [d.gap * 1000 for d in ds]
    chk("board gaps vary between decks", (max(gapmm) - min(gapmm)) > 3.0,
        "%.1f .. %.1f mm" % (min(gapmm), max(gapmm)))
    nstore = sum(len(d.store) for d in ds)
    chk("things are stored under the decks", nstore >= 25,
        "%d items over %d decks, %d kinds"
        % (nstore, len(ds), len({w for d in ds for w in d.store})))

    # --- the interface answers ---------------------------------------------
    bad = []
    for d in ds:
        for fn in (column_sockets, handrail_sockets, floor_slots, lean_points):
            try:
                r = fn(d)
                if not r:
                    bad.append("%s(post %d) empty" % (fn.__name__, d.n))
            except Exception as e:                          # pragma: no cover
                bad.append("%s(post %d): %s" % (fn.__name__, d.n, e))
        try:
            stair_landing(d)
            under_deck(d)
        except Exception as e:                              # pragma: no cover
            bad.append("landing/under(post %d): %s" % (d.n, e))
    chk("every interface function answers for every deck", not bad,
        "; ".join(bad[:3]) if bad else "6 functions x 25 decks")

    # --- nothing may reach the racing surface or the barrier line -----------
    worst_clear, worst_who = 1e9, ""
    for d in ds:
        cs = []
        for sx in (-1.0, 1.0):
            for sy in (-1.0, 1.0):
                for (ex, ey) in ((d.Wd * 0.5, d.Dd * 0.5), (d.W * 0.5, d.D * 0.5)):
                    cs.append((sx * ex, sy * ey))
        for it in store_layout(d):
            r = math.hypot(*it["size"][:2]) * 0.5
            cs += [(it["x"] - r, it["y"] - r), (it["x"] + r, it["y"] + r),
                   (it["x"] - r, it["y"] + r), (it["x"] + r, it["y"] - r)]
        Pl = np.array([[x, y, 0.0] for (x, y) in cs])
        Pw = Pl @ d.R.T + d.O
        S, U = C.project(Pw[:, 0], Pw[:, 1])
        # THE ROAD EDGE, not the barrier line.  `barrier_offset` is the wrong
        # datum here and the first version of this check used it: on the T4
        # hairpin INSIDE the contract puts the barrier 67 m out across a paved
        # apron, and build_dressing deliberately stands post 6 on that apron as
        # the inside flag point.  Measuring against the barrier called a
        # correctly-placed post a 48 m intrusion.  What placement actually
        # forbids is reaching the ROAD: `verge_edge` is the outermost edge of
        # build_surface's own mesh, plus the project's 0.50 m courtesy margin.
        clear = float(np.min(np.abs(U) - C.verge_edge(S))) - 0.50
        if clear < worst_clear:
            worst_clear, worst_who = clear, "post %d" % d.n
    chk("nothing reaches the road corridor", worst_clear >= 0.0,
        "min clearance %+.3f m at %s (deck box, pad box and stored kit)"
        % (worst_clear, worst_who))

    # --- pixels -------------------------------------------------------------
    hs = [h01(91.508449, 4530, j) for j in range(12)]
    hd = [h01_dressing(91.508449, 4530, j) for j in range(12)]
    chk("the per-index hash avalanches", (max(hs) - min(hs)) > 0.75,
        "spread %.3f (build_dressing's: %.3f)"
        % (max(hs) - min(hs), max(hd) - min(hd)))
    chk("filmed-distance scale", abs(PX_PER_M - 622.222) < 0.01,
        "%.1f px/m, 1 px = %.3f mm, hero limit %.2f mm"
        % (PX_PER_M, PX_M * 1000, HERO_EDGE_M * 1000))

    # --- winding: which side of every primitive the lens gets (R2-179) ------
    winding_selftest(chk)

    if verbose:
        print("  ---- per-deck ----")
        for d in ds:
            print("   %2d %-8s s=%8.2f  %4.2fx%4.2f m  H=%.3f  gap=%4.1fmm  "
                  "axis=%s  boards=%s  under=%s"
                  % (d.n, d.arch, d.s, d.Wd, d.Dd, d.H, d.gap * 1000, d.axis,
                     len(board_layout(d)) if d.kind in (0, 3) else "-",
                     ",".join(d.store) or "-"))
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
    out["hero_limit_px"] = HERO_EDGE_PX
    nimg = sum(1 for m in bpy.data.materials if m.use_nodes
               for n in m.node_tree.nodes if n.type == "TEX_IMAGE")
    ngeo = sum(1 for m in bpy.data.materials if m.use_nodes
               for n in m.node_tree.nodes if n.type == "NEW_GEOMETRY"
               and any(o.name == "Position" and o.is_linked for o in n.outputs))
    out["image_texture_nodes"] = nimg
    out["geometry_position_links"] = ngeo
    log("measured: %d objects, %d triangles, p10 %.2f mm = %.2f px "
        "(hero limit %.1f px), p50 %.2f mm = %.2f px"
        % (out["objects"], out["triangles"], out["p10_m"] * 1000, out["p10_px"],
           HERO_EDGE_PX, out["p50_m"] * 1000, out["p50_px"]))
    log("image texture nodes %d, Geometry->Position links %d"
        % (nimg, ngeo))
    return out


def interface_dump(path=None):
    """The whole public interface as JSON, for the six dependent agents."""
    out = dict(item=ITEM, generated=time.strftime("%Y-%m-%d"),
               frame="deck-local: +x width along the barrier, +y AWAY from the "
                     "track, +z up; origin ON the ground at the post anchor",
               decks=[])
    for d in plan():
        out["decks"].append(dict(
            n=d.n, s=d.s, side=d.side, lat=d.lat, archetype=d.arch,
            world_origin=[round(float(v), 4) for v in d.O],
            R=[[round(float(v), 8) for v in r] for r in d.R],
            deck=dict(W=round(d.Wd, 4), D=round(d.Dd, 4), H=round(d.H, 4),
                      board_axis=d.axis, board_w=round(d.bw, 4),
                      board_t=round(d.bt, 4), gap=round(d.gap, 4),
                      top_z_at_centre=round(float(deck_top_z(d, 0.0, 0.0)), 5)),
            column_sockets=column_sockets(d),
            handrail_sockets=handrail_sockets(d),
            stair_landing=stair_landing(d),
            floor_slots=floor_slots(d),
            lean_points=lean_points(d),
            under_deck=under_deck(d)))
    if path:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        json.dump(out, open(path, "w"), indent=1)
        log("interface -> %s" % path)
    return out


def replan():
    """Regenerate SITES from build_dressing.  Prints the literal to paste back.

    Deliberately manual: a foundation item whose placement moves when somebody
    edits another module moves the deck out from under the column, the stair and
    the handrail, built by four agents who never meet.
    """
    import build_dressing as D
    posts = D.marshal_post_plan()

    def gaps(ps):
        ps = sorted(ps, key=lambda p: p["s"])
        return [(((ps[(i + 1) % len(ps)]["s"] - p["s"]) % D.LAP), i)
                for i, p in enumerate(ps)]
    g = sorted(gaps(posts), reverse=True)
    print(">> plan returns %d posts, worst gaps %s"
          % (len(posts), [round(x[0], 1) for x in g[:4]]))
    if len(posts) < INSTANCES:
        posts.sort(key=lambda p: p["s"])
        gap, i = g[0]
        p, q = posts[i], posts[(i + 1) % len(posts)]
        ss = (p["s"] + gap * 0.5) % D.LAP
        sd = p["side"] if D.hash01(ss, 902) < 0.5 else q["side"]
        if D.barrier_type(ss, sd) in (2, 3):
            sd = -sd
        posts.append(dict(s=ss, side=sd, why="straight infill (manifest 25th)"))
        D._finalise_posts(posts)
        print(">> restored the manifest's 25th post at s=%.1f; worst gap now %.1f m"
              % (ss, max(x[0] for x in gaps(posts))))
    for p in posts:
        W, Dp, Hh, padw, padd = D.post_pad(p["k"])
        wx, wy, z, la = D.anchor("post%02d" % p["n"], p["s"], p["lat"], p["side"],
                                 embed=D.BASE_EMBED, foot=padd * 0.55 + 0.2,
                                 behind=True, clear=padd * 0.45 + 0.25,
                                 height=Hh + 0.9, halfspan=padw * 0.5,
                                 register=False)
        nx, ny = D.normal_world(p["s"], p["side"])
        gz, _ = C.world_ground_z(float(wx), float(wy))
        print("    dict(n=%2d, s=%9.3f, side=%+d, lat=%8.4f, kind=%d, tier=%d, "
              "k=%11.6f, wx=%11.4f, wy=%11.4f, gz=%9.5f, nx=%+.8f, ny=%+.8f, "
              "yaw=%+8.4f, W=%.4f, D=%.4f, Hh=%.4f, padw=%.4f, padd=%.4f),"
              % (p["n"], p["s"], p["side"], la, p["kind"], p["tier"], p["k"],
                 wx, wy, gz, nx, ny, D.rnd(-9, 9, p["k"], 300), W, Dp, Hh,
                 padw, padd))


# ================================================================================
# 16.  CLI
# ================================================================================

def main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", action="store_true", help="build the acceptance scene")
    ap.add_argument("--build", action="store_true", help="build the item only")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--measure", action="store_true")
    ap.add_argument("--replan", action="store_true")
    ap.add_argument("--interface", default=None)
    ap.add_argument("--lod", type=float, default=1.0)
    ap.add_argument("--which", type=int, nargs="*", default=None)
    ap.add_argument("--nocontext", action="store_true")
    ap.add_argument("--samples", type=int, default=256)
    ap.add_argument("--save", default=None)
    ap.add_argument("--render", default=None)
    ap.add_argument("--cam", default=PFX + "CAM_MACRO")
    ap.add_argument("--res", type=int, nargs=2, default=[1920, 1080])
    a = ap.parse_args(argv)

    if a.selftest:
        sys.exit(0 if selftest() else 1)
    if a.replan:
        replan()
        return
    if a.interface and not (a.test or a.build):
        interface_dump(a.interface)
        return
    if a.test or a.save or a.render:
        test_scene(lod=a.lod, samples=a.samples, which=a.which,
                   context=not a.nocontext)
    elif a.build:
        build(which=a.which, lod=a.lod)
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
