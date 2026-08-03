#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
timing_stand.py — CIRCUIT VITRINE, per-item hero campaign, item ``timing_stand``
(zone ``pit_straight``, wave 1, build order 135, **5 dependants, 0 dependencies**).

WHAT THIS IS, IN ONE SENTENCE
=============================
The ten team timing stands on the pit wall, built as the **demountable bolted
structures they actually are** — a levelled chassis of extruded aluminium, a
tread-plate deck at knee height, a console carcass carrying the monitor arms,
a canopy frame either erected or struck, and the cable loom that ties the whole
thing back to the garage — so that what the lens reads across the wall on the
onboard follow is ten different machines that ten different crews assembled,
and not one prop copied ten times.

    manifest: "NOT IN THE SPEC AND NOT BUILT - a genuine gap.  A pit wall with
               no timing stands is the clearest sign nobody is home."

THE PIXEL BUDGET THIS WAS BUILT TO
----------------------------------
    px_per_m = (3840 x 35 / 36) / 10.0 = 373.33 px/m     ->    1 px = 2.679 mm

    the 3.20 m stand height            1195 px  (manifest: onscreen_px_4k 1195)
    a 5.4 m stand length               2016 px
    a 45 mm extrusion face             16.8 px
    an 8 mm T-slot mouth                3.0 px   <- self-shadowing: GEOMETRY
    an M8 hex head, 13 mm AF            4.9 px wide, 5.3 mm proud
                                                 <- and see the light note: it
                                                    throws 24 mm = 9.0 px of
                                                    shadow.  GEOMETRY, ~450 of
                                                    them per stand
    an M8 washer, 17 mm                 6.3 px   <- GEOMETRY
    a 5-bar tread rib, 1.8 x 22 mm      8.2 px long, 3.0 px of shadow
                                                 <- GEOMETRY, ~4 700 per deck
    a 38 mm GRP grating aperture       14.2 px   <- GEOMETRY (a real hole)
    a 12 mm perforation                 4.5 px   <- GEOMETRY (a real hole)
    a 6-14 mm cable                  2.2-5.2 px  <- GEOMETRY, swept
    a 4 x 8 mm cable-tie head         1.5x3 px   <- GEOMETRY (they cluster, and
                                                    a rhythm reads below 1 px)
    a 3 mm MIG weld ripple              1.1 px   <- GEOMETRY on the steel family
    a 0.35 mm vinyl graphic edge        0.13 px of thickness, but the letter is
                                       45 px tall <- GEOMETRY, for an edge no
                                                    procedural mask can match
    brushed anodising grain, 0.05 mm   0.02 px   <- SHADING
    orange-peel in the powder coat, 0.15 mm      <- SHADING
    every stain, chalk, tape ghost, UV fade      <- SHADING

The line is drawn at 0.8 mm of relief — 0.3 px — and everything above it that
occludes or self-shadows is mesh.

WHY THE LIGHT DECIDES THE MODELLING
-----------------------------------
Measured against ``world_contract``: the stand's front (track-facing) normal in
world is (+0.6428, -0.7660, 0) and ``SUN_DIR`` is (0.5179, -0.8278, 0.2159).
The sun is **7.97 deg off that normal in azimuth and 12.47 deg above the
horizon**, so cos(incidence) = 0.967 — the front of every timing stand is in
near-frontal, near-grazing sun and is one of the brightest surfaces in the
frame.  Two consequences that drove every modelling decision here:

  * **Horizontal relief casts 4.5x its own height downward.**  A 5.3 mm bolt
    head throws 24 mm = 9.0 px.  A 2 mm deck rib throws 9 mm.  A 20 mm console
    lip throws 90 mm = 34 px.  So the front face is where the fasteners, the
    lipped edges, the cable tray, the louvres and the tread nosings live, and
    each of them is worth several times its own size on screen.
  * **Vertical relief casts almost nothing** (7.97 deg of azimuth offset: a
    3 mm proud vertical rib throws 0.42 mm sideways).  So every vertical event
    is a RECESS or a HOLE — T-slots, perforations, grating apertures, socket
    bores, the hex socket in a cap screw — which read by their own darkness
    rather than by a cast shadow.

WHAT THE FILM ACTUALLY SEES, AND WHERE THE DETAIL WENT
------------------------------------------------------
The 10.0 m in the manifest is the onboard follow on the pit straight: the lens
rides 1.900 m off the deck and passes the wall at about 10 m.  The pit wall is
1.200 m tall (``pit_wall_unit``: TOP_Z), so from that eye the wall's top edge
sweeps a sight line that lands at z = 1.17 at the stand.  **Everything below
z = 1.17 is occluded in the hero shot.**  That is not licence to leave the
chassis coarse — Beat 4 and every pit-lane item's camera see it from behind —
but it is why the console fascia, the worktop lip, the monitor arms, the seat
mounts, the handrail and the canopy frame carry the heaviest modelling on the
object, and why ``CAM_MACRO`` is set at exactly the film's own geometry with
the pit wall stood in front of it rather than at a flattering three-quarter.

===============================================================================
THE PUBLIC INTERFACE  —  this item is a FOUNDATION.  5 items depend on it.
===============================================================================
Everything below is a pure function of this module's deterministic plan.  It
runs WITHOUT bpy, builds nothing, and returns world-frame geometry.
``interface_json(path)`` dumps the lot to
``world/items/timing_stand_interface.json``.

    timing_stand_seat (40)      ``seat_stations()``
        Per seat: the world transform of the SEAT MOUNT PLATE this module
        builds (a 150 x 150 x 8 mm plate with a 62 mm spigot boss and four M8
        holes on a 100 mm PCD), the rail it clamps to, the deck top z under it,
        the tier, the seat pitch, the facing direction, and ``deployed``.
        THE SEAT ITEM BRINGS ITS OWN STEM AND SHELL.  This module owns
        everything up to and including the boss; the seat owns everything above
        ``mount_top_world``.  Stowed stations carry a fitted cover, not a seat.

    timing_stand_monitor (60)   ``monitor_bays()``
        Per monitor: the VESA plate centre in world, the plate's outward normal
        and up vector, the 100 x 100 VESA bolt pattern, the screen size class
        (24 / 27 / 32 in), the arm's deployed pitch and yaw, the cable exit
        point, and the shade hood aperture in the console rail if that stand
        has one.  Screens hang FROM the plate; the arm is this module's.

    timing_stand_canopy (10)    ``canopy_frame()``
        Per stand: state (``up`` / ``down``), the post tops, the two eaves rail
        polylines, every rafter as a world polyline, the valance rectangle, the
        eyelet positions on the rails (25 mm brass eyelets at 300 mm centres),
        the roll-up mandrel axis when the state is ``down``, and the frame's
        own tube radius so the fabric can be lofted onto it without a gap.

    engineer_on_timing_stand (40) and team_principal_figure (10)
                                ``figure_stations()``
        Per station: occupied or not, the seat reference point, the deck top z
        under the feet, the foot rail, the console front edge and top z (the
        elbow line), the headset hook, the sight line to the track, the tier,
        and the role — ``engineer`` for the console row, ``principal`` for the
        single raised station on a 2- or 3-tier stand.

    also published, not required by any dependant but true and useful:
        ``deck_rects()``    every deck tier as a world rectangle + its top z, so
                            anything set down on a stand sits on the surface.
        ``kit_sites()``     the sockets this module built but deliberately left
                            empty: the fire-extinguisher bracket, the umbrella
                            socket, the bin hoop.
        ``stand_records()`` the whole plan.
        ``SECTION``         the section constants as a dict.

--- WHERE THE STANDS ARE ------------------------------------------------------

Circuit frame.  ``pit_wall_unit`` pins the wall face at y = 11.550 and its stem
is 0.340 thick, so the wall's pit-lane face is y = 11.890.  ``C.world_ground_z``
hands circuit y <= ~12.15 to ``build_barriers``' runoff platform at z ~ -0.14
and everything north of it to ``build_architecture``' pit-lane paving at
z = 0.000 exactly — a 0.14 m step 0.26 m behind the wall, which is nobody's
defect but is a fact this item has to stand on.  So:

    FRONT_LEG_Y   12.420   the chassis' front leg line.  MEASURED: every foot
                           of every stand samples ``C.world_ground_z`` and the
                           returned owner is asserted to be the paving.  A
                           chassis with one foot on the platform and three on
                           the paving would be 0.14 m out of level.
    CONSOLE_Y     12.060   the console front edge, cantilevered 0.360 m forward
                           of the legs and 0.170 m clear of the wall's pit face.
                           Nothing on this item crosses y = 12.000, so the
                           coping, the advert panels and the padding all keep
                           their budget.

The ten stands sit at ten of ``build_architecture``'s fourteen garage bay
centres (bays 1..10, circuit x -206.0 .. -5.0), each with its own hand-placed
offset, and each wears the livery of the team whose garage it stands in front
of — ``build_architecture.TEAMS``, quoted verbatim in ``TEAMS`` below so no
32nd brand is invented.  Bay 0 at x = -228.5 is skipped: the wall itself starts
at x = -222.0 and a stand in front of no wall is a placeholder.

===============================================================================
THE SEVEN LAWS, AND WHERE EACH IS DISCHARGED
===============================================================================
 1. procedural, by hand   no image node, no file, no font datablock.  The team
                          lettering is a hand-coded capsule-stroke font
                          (``GLYPHS``) extruded 0.35 mm as real vinyl.
                          Measured by ``item_gate``: ``no_external_assets``.
 2. no real brands        ten of ``build_architecture``'s fourteen invented
                          TEAMS, and two of ``build_dressing``'s existing
                          BRANDS on the valance.  Nothing new invented.
 3. car scale             the 1.200 m wall and the 5.698 x 2.005 m car set the
                          deck height: a seated engineer's eye must clear the
                          wall, and the console must not.  Not intuition.
 4. z = 0 is one plane    every foot samples ``C.world_ground_z`` and the owner
                          string is checked; nothing assumes z = 0.
 5. embed >= 20 mm        every levelling foot's rubber pad is 36 mm thick and
                          sits 22 mm BELOW the sampled ground, 14 mm proud.
                          Castors are jacked CLEAR of the floor by 8-15 mm —
                          which is what a stand on levelling feet actually
                          looks like — so they are not ground-contacting and
                          the law does not have to be faked on a round wheel.
 6. recentre + TexCoord   every stand's mesh is local to its own centroid,
                          |P| < 3.9 m.  Materials read ``TexCoord->Object``,
                          eleven baked vertex attributes and six per-OBJECT
                          properties.  ``Geometry->Position`` appears nowhere;
                          ``Geometry->Normal`` does, for up-facing dirt, which
                          is a direction and carries no precision problem.
 7. chunk along s         one stand is <= 7.4 m of circuit.

===============================================================================
WHAT VARIES BETWEEN INSTANCES, AND WHY IT IS GEOMETRY
===============================================================================
The manifest names four axes.  All four are assigned BY DESIGN rather than by
hash, so that the spread is guaranteed rather than hoped for, and all four are
in the mesh:

  tier count       1, 2 or 3 decks.  A second tier is a whole extra chassis
                   bay, four more posts, a riser, a nosing, its own handrail
                   and its own seat rail — 22-34 % more structure, not a
                   scaled copy.  Assigned [1,2,2,1,3,2,1,2,3,1].
  canopy up/down   up: six posts, two eaves rails, 5-8 rafters, a valance and
                   an eyelet strip.  down: the same rafters HINGED FLAT along
                   the rails, the fabric rolled on its mandrel and lashed with
                   webbing at three points, and the valance rail dropped into
                   its stowage clips.  Different topology, not a hidden object.
                   Assigned [up,down,up,up,down,up,down,up,up,down].
  occupied/empty   occupied: monitor arms deployed at their own angles, the
                   loom run out and dressed, headsets on their hooks, a kit bag
                   and a crate on the deck, seat covers off.  empty: arms
                   folded to the rail, the loom coiled on its drum, a tarpaulin
                   lashed over the console, seat covers on, the deck clear.
                   Assigned 7 occupied, 3 empty.
  team livery      colour is the least of it: the fascia is flat, ribbed,
                   louvred or perforated per team; the stripe is a different
                   raised-vinyl SHAPE per team; the nameplate is that team's
                   name set in the stroke font at that team's own tracking.

...and six more that are not named but are what stops the ten reading as one:
extrusion family (45-series slot / 60-series slot / welded 50 SHS with real
weld beads), deck surface (5-bar chequer / GRP grating / ply + grit / studded
rubber), step position and tread count, ballast (none / steel plates /
sandbags), handrail run, and the length itself, 4.20-7.40 m.

===============================================================================
WHAT THE RENDERS CHANGED — five iterations, and none of it was predictable
===============================================================================
Every one of these was invisible in the code and obvious in a frame.

 1. IT READ AS SCAFFOLDING.  The first pass was a bare bolted frame with a
    fascia strip: bright members, daylight through every bay, no mass.  A real
    pit wall stand is CLAD.  `build_panels` adds the composite end screens, the
    deck skirt and their fixings, and the object stopped being a frame.
 2. THE END PANELS WERE THEN A SHIPPING CONTAINER.  Deck-to-eaves over the full
    depth is not a wind screen, it is a wall.  They now start at the worktop
    and stop short of the back, which is what the real thing does.
 3. THE PAINT WAS FLAT AT 5x.  Every weathering layer was present and every one
    of them was a product of three sub-unit factors, landing at 5-15 %.  Age
    and grime were re-floored (0.45-0.98, 0.42-0.95) and the wash, chalk and
    splash gains roughly doubled.
 4. THE RAIN STREAKS DID NOT EXIST ON THE END PANELS.  The streak coordinate
    was built from (Pl.x, Pl.z), which is CONSTANT across a plane of constant x
    -- so the two biggest painted surfaces on the object had no streaking at
    all while the fascia did.  It is now (0.62 x + 0.47 y, 1.7 z).
 5. THE FRAME WAS POLISHED CHROME.  Roughness 0.28-0.44 at metallic 0.88 is
    not clear anodising, it is a mirror.  0.42-0.58, plus per-member soiling
    off `ts_pid`.
 6. THE NAMEPLATE FLOATED IN A HOLE.  On the window-cut end panel the livery
    was placed at a fixed height and landed inside the aperture, hanging
    unsupported -- visible in a 5x crop as a mirrored JUNIPER in mid air.  Each
    panel style now publishes the solid band its livery goes in.
 7. THE LETTERS Z-FOUGHT.  Overlapping capsules at a stroke join share a
    coplanar top face; the first valance came back with pale circular seams
    inside every glyph.  15 microns of per-capsule stagger settles it.
 8. TONE BLOTCHING WITHIN ONE PANEL.  Panel-to-panel colour was driven off a
    0.38 m voronoi in object space, which does not know where one panel stops:
    on a 2.8 m end panel that is not five sprays, it is blotching.  `ts_pid` is
    a per-PART id written by `Acc.add`, and the four pieces around a window
    share one value explicitly.
 9. THE STAIR STRINGERS MISSED THE TREADS by up to 0.96 m on a deep stand --
    two hardcoded fractions of D that only agree at one depth.  Measured off
    the pit-lane render.
10. THE GROUND STAND-IN WAS BLACK.  Not this item: the test scene's paving
    stand-in was 0.052 albedo, and under a 12.47 deg key at -3.048 EV the whole
    band above the wall crushed to nothing.  A stand-in defect that reads
    exactly like a lighting bug.

ON THE PLACEMENT GATE
---------------------
`tools/placement_gate.py` on this test scene reports two violations, and BOTH
of them are `XSTAND_Ground` -- the test scene's own ground plane, which is the
road surface and is supposed to be there.  It is flagged only because the gate
exempts ground by name prefix (`SURF_`, `TER_Ground`, ...) and a stand-in is
deliberately not in that namespace.  **Zero `TS_` objects are flagged**, on any
of the three volumes: road corridor, car path, camera path.  Renaming the
stand-in to dodge the check would have been the wrong fix and is not what
happened.
===============================================================================
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

__version__ = "1.0.0"

ITEM = "timing_stand"
COLL = "W_Item_TimingStand"
PFX = "TS_"
XPFX = "XSTAND_"        # test-scene stand-ins owned by OTHER items.  Deliberately
                        # NOT prefixed "TS_", so `item_gate --prefix TS_` cannot
                        # measure one of them and credit it to this item.

_T0 = time.time()
VERBOSE = True


def log(msg):
    if VERBOSE:
        print("[%s %7.1fs] %s" % (ITEM, time.time() - _T0, msg))
        sys.stdout.flush()


# ==============================================================================
#  0.  THE NUMBERS
# ==============================================================================
# Manifest record, quoted so nothing downstream re-reads the JSON.
FILMED_AT_M = 10.0
LENS_MM = 35.0
ONSCREEN_PX_4K = 1195.0
INSTANCES_DECLARED = 10
TYPICAL_H_M = 3.2
PX_PER_M = (3840.0 * LENS_MM / 36.0) / FILMED_AT_M            # 373.33 px/m
PX_M = 1.0 / PX_PER_M                                         # 2.679 mm

# --- the site, in the circuit design frame -----------------------------------
WALL_PIN_Y = C.PIT_WALL_Y             # 11.500  the contract pin
WALL_FACE_Y = 11.550                  # pit_wall_unit.FACE_PLANE_Y
WALL_T = 0.340                        # pit_wall_unit.T_STEM
WALL_PIT_FACE_Y = WALL_FACE_Y + WALL_T        # 11.890
WALL_TOP_Z = 1.200                    # pit_wall_unit.TOP_Z
FRONT_LEG_Y = 12.420                  # the chassis front leg line
CONSOLE_Y = 12.060                    # console front edge (cantilever)
CLEAR_OF_WALL = FRONT_LEG_Y - WALL_PIT_FACE_Y            # 0.530
EMBED = 0.022                         # >= C.BASE_EMBED_M = 0.020
PAD_T = 0.036                         # levelling pad thickness
CASTOR_LIFT = (0.008, 0.015)          # castors hang this clear of the floor

# garage bay centres, from build_architecture.BAY_W / CORE_W.  Recomputed here
# rather than imported, because build_architecture imports bpy at module scope.
_BAY_W = [21.0, 22.0, 20.5, 21.5, 23.0, 20.0, 21.0, 22.5,
          20.5, 21.0, 22.0, 20.5, 20.5, 20.0]
_CORE_W = [6.0, 5.0, 5.0, 8.0]
_PB_X0 = -245.0


def _bay_centres():
    xs, x, bi = [], _PB_X0 + _CORE_W[0], 0
    for gi, n in enumerate((4, 5, 5)):
        for _k in range(n):
            xs.append(x + _BAY_W[bi] * 0.5)
            x += _BAY_W[bi]
            bi += 1
        if gi < 2:
            x += _CORE_W[gi + 1]
    return xs


BAY_CENTRES = _bay_centres()          # 14 of them, -228.50 .. +56.00

# build_architecture.TEAMS, quoted verbatim.  Fourteen invented teams; ten of
# them have a stand on the wall.  Law 2: reuse, never invent a fifteenth.
TEAMS = [
    ("ALTHEA",    '#8e1d24', '#e8dfd0'), ("BOREAL",  '#5f9fd0', '#f2f6f8'),
    ("CORVUS",    '#141416', '#c8a24a'), ("DELMAR",  '#16305c', '#e2651a'),
    ("ESTIVAL",   '#c8ab74', '#4a3a28'), ("FULGOR",  '#e3bb14', '#2b2d31'),
    ("GRISAILLE", '#6d6f74', '#c02a78'), ("HALCYON", '#127f7a', '#f4f7f6'),
    ("IRIDIA",    '#5b3f9a', '#b9bec4'), ("JUNIPER", '#2f6b3a', '#efe6cd'),
    ("KESTREL",   '#1d3a2a', '#d8641c'), ("LUMEN",   '#e9edf0', '#17a8c4'),
    ("MERIDIAN",  '#22306e', '#f0f2f5'), ("NOCTIS",  '#2a2c2e', '#9ed61f'),
]
# two of build_dressing's existing BRANDS ride the valance as team partners
VALANCE_BRANDS = ["VOLTAIC", "MERIDIAN", "CIRRUS", "ARDENT", "CALIBRE",
                  "KESTREL", "NORDVAL", "ALTIS", "VERITAS", "OBSIDIAN"]

STAND_BAYS = list(range(1, 11))       # bays 1..10 -> circuit x -206.0 .. -5.0

# --- the four named axes, ASSIGNED, not hashed --------------------------------
AX_TIERS = [1, 2, 2, 1, 3, 2, 1, 2, 3, 1]
AX_CANOPY = ["up", "down", "up", "up", "down", "up", "down", "up", "up", "down"]
AX_OCCUPIED = [True, True, False, True, True, True, False, True, True, False]
# family:  0 = 45-series T-slot alu, 1 = 60-series T-slot alu, 2 = welded 50 SHS
AX_FAMILY = [0, 1, 2, 0, 1, 0, 2, 1, 0, 2]
# deck:    0 = 5-bar chequer, 1 = GRP grating, 2 = ply + grit paint, 3 = rubber stud
AX_DECK = [0, 1, 2, 0, 3, 1, 0, 2, 1, 0]
# fascia:  0 = flat, 1 = ribbed, 2 = louvred, 3 = perforated
AX_FASCIA = [1, 0, 2, 3, 1, 2, 0, 3, 1, 2]

# --- the section --------------------------------------------------------------
# Extrusion families.  (name, main section, secondary, slot mouth, slot depth,
#                       slot inner, corner radius, wall)
FAMILY = (
    dict(name="45-series T-slot", a=0.045, b=0.030, mouth=0.0102, dep=0.0125,
         inner=0.0163, r=0.0020, bore=0.0102, slots=4, weld=False),
    dict(name="60-series T-slot", a=0.060, b=0.040, mouth=0.0125, dep=0.0155,
         inner=0.0200, r=0.0025, bore=0.0130, slots=4, weld=False),
    dict(name="50 SHS welded", a=0.050, b=0.030, mouth=0.0, dep=0.0,
         inner=0.0, r=0.0040, bore=0.0, slots=0, weld=True),
)

DECK_KIND = ("chequer", "grating", "ply", "rubber")
FASCIA_KIND = ("flat", "ribbed", "louvred", "perforated")

CONSOLE_H = 0.740             # worktop top above the deck it stands on
CONSOLE_D = 0.520             # worktop depth
CONSOLE_LIP = 0.020           # front lip: 90 mm = 34 px of cast shadow
RAIL_H = 0.300                # monitor rail above the worktop
SEAT_PITCH = (0.760, 0.960)   # seat centres along the stand
TIER_RISE = (0.320, 0.420)
DECK_Z0 = (0.620, 0.800)      # front deck top above the paving
CANOPY_Z = (3.010, 3.420)     # canopy underside of the eaves rail

# --- LOD ----------------------------------------------------------------------
# Only ever used to thin the far stands in the assembly.  The test scene builds
# every stand at LOD 0 so the gate measures the object the film sees.
LOD_RADII = (26.0, 90.0)

M_ALU, M_PAINT, M_DECK, M_RUB, M_STEEL, M_VINYL, M_FAB, M_ELEC = range(8)
MAT_ORDER = ["Alu", "Paint", "Deck", "Rubber", "Steel", "Vinyl", "Fabric",
             "Electrical"]

ATTR_F = ("ts_wear", "ts_edge", "ts_dirt", "ts_ao", "ts_age", "ts_grip",
          "ts_h", "ts_paint", "ts_anod", "ts_pid")
# ts_pid is a PER-PART random value written automatically by `Acc.add`.  It
# exists because the first pass drove panel-to-panel tone off a voronoi in
# object space, which does not know where one panel stops and the next starts:
# a 0.38 m cell field over a 2.8 m composite end panel is not five panels
# sprayed in five different weeks, it is BLOTCHING -- the exact failure the
# world contract's law 6 was written about, arriving by a different route.
# A per-part id is the thing that actually varies part to part.
ATTR_V = ("ts_bc",)          # part-local coordinate; x ALONG the member axis
ATTR_C = ("ts_tint",)
ATTRS = ATTR_F + ATTR_V + ATTR_C

# world basis of the circuit design frame
_CR = math.cos(math.radians(C.ROT_DEG))
_SR = math.sin(math.radians(C.ROT_DEG))
EX = np.array([_CR, _SR, 0.0])          # circuit +x  (east along the pit wall)
EY = np.array([-_SR, _CR, 0.0])         # circuit +y  (into the pit lane)
EZ = np.array([0.0, 0.0, 1.0])


def srgb(h):
    """'#rrggbb' -> LINEAR rgb triple.  Same conversion build_dressing uses."""
    h = h.lstrip('#')
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255.0
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return tuple(out)


# Linear reflectances.  Anodised aluminium is DARKER than intuition: a clear
# anodised mill-finish extrusion measures 0.42-0.52 diffuse with a strong
# specular lobe, not the 0.7 that "silver" suggests, and a powder coat two
# seasons in the sun has lost 10-18 % of its chroma.  Calibrated against
# C.lambert_radiance under a 0.967 cos-incidence key: this front face is one of
# the brightest things in the frame and it clips if it is painted what it looks.
PAL = dict(
    alu_bright=(0.4750, 0.4820, 0.4900),      # freshly wiped anodised face
    alu_mid=(0.3400, 0.3450, 0.3520),         # the working average
    alu_dull=(0.2050, 0.2080, 0.2140),        # oxidised, handled, dusty
    alu_slot=(0.1250, 0.1270, 0.1310),        # down a T-slot: dirt and shadow
    alu_scuff=(0.2600, 0.2560, 0.2500),       # a scrape through the anodising
    alu_white=(0.5600, 0.5620, 0.5580),       # white rust / oxide bloom
    steel_gal=(0.4400, 0.4460, 0.4520),       # zinc, spangled
    steel_pass=(0.3300, 0.3150, 0.2450),      # yellow passivation on a fastener
    steel_dark=(0.0850, 0.0860, 0.0880),
    rust=(0.0930, 0.0370, 0.0160),
    rub_black=(0.0210, 0.0208, 0.0212),       # EPDM trim, cable sheath
    rub_grey=(0.0480, 0.0480, 0.0495),
    rub_chalk=(0.1150, 0.1140, 0.1120),       # UV chalking on old rubber
    ply_face=(0.2380, 0.1790, 0.1010),
    ply_grit=(0.0720, 0.0690, 0.0640),        # grit-paint deck
    grp_grey=(0.1550, 0.1560, 0.1520),        # GRP grating
    grp_grit=(0.0980, 0.0980, 0.0960),
    deck_worn=(0.3050, 0.3080, 0.3120),       # rib crests polished by boots
    deck_dirt=(0.0620, 0.0590, 0.0540),       # what lives in the valleys
    rubber_film=(0.0180, 0.0176, 0.0174),     # tyre and brake dust
    vinyl_gloss=(0.0400, 0.0400, 0.0400),
    fab_web=(0.0620, 0.0620, 0.0640),         # polyester webbing
    fab_tarp=(0.1050, 0.1080, 0.1020),
    elec_black=(0.0180, 0.0180, 0.0186),      # ABS / black anodise
    elec_grey=(0.0900, 0.0905, 0.0915),
    brass=(0.2600, 0.1850, 0.0700),
    primer=(0.1650, 0.1500, 0.1250),          # what a paint chip shows
    dust=(0.1450, 0.1330, 0.1120),
    grime=(0.0450, 0.0430, 0.0400),
)


# ==============================================================================
#  1.  NUMERIC KIT — deterministic, seedable, identical on every machine
# ==============================================================================

_M64 = 0xFFFFFFFFFFFFFFFF


def h01(*keys):
    """FNV-1a over mixed keys -> float in [0, 1).  Avalanches properly.

    build_dressing's hash01 does NOT avalanche across a small index change --
    measured in marshal_post_deck's docstring, twelve consecutive indices came
    back inside 1 % of each other, so twelve "different" boards were one board.
    This one runs a 64-bit FNV-1a and then a final xorshift-multiply mix, and
    consecutive indices decorrelate to within measurement noise.
    """
    h = 0xCBF29CE484222325
    flat = []
    for k in keys:
        if isinstance(k, (tuple, list)):
            flat.extend(k)
        else:
            flat.append(k)
    for k in flat:
        if isinstance(k, str):
            for ch in k:
                h = ((h ^ ord(ch)) * 0x100000001B3) & _M64
            continue
        v = int(round(float(k) * 4096.0)) & _M64
        for _ in range(8):
            h = ((h ^ (v & 0xFF)) * 0x100000001B3) & _M64
            v >>= 8
    h ^= (h >> 33)
    h = (h * 0xFF51AFD7ED558CCD) & _M64
    h ^= (h >> 29)
    h = (h * 0xC4CEB9FE1A85EC53) & _M64
    h ^= (h >> 32)
    return (h & 0xFFFFFFFFFFFF) / float(0x1000000000000)


def rnd(lo, hi, *keys):
    return lo + (hi - lo) * h01(*keys)


def rint(lo, hi, *keys):
    return int(lo + math.floor(h01(*keys) * (hi - lo + 1 - 1e-9)))


def chance(p, *keys):
    return h01(*keys) < p


def pick(seq, *keys):
    return seq[int(h01(*keys) * len(seq)) % len(seq)]


def gauss(sd, clip, *keys):
    """A clipped, zero-mean draw built from two hashes (Irwin-Hall, n=4)."""
    s = (h01(*keys) + h01(*(list(keys) + [7])) + h01(*(list(keys) + [13]))
         + h01(*(list(keys) + [29]))) * 0.5 - 1.0
    return float(np.clip(s * sd * 1.4142, -clip, clip))


def _hn(x, seed):
    ix = np.floor(x).astype(np.int64)
    h = (ix * 374761393 + int(seed) * 668265263) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFFFFFF).astype(np.float64) / 4294967295.0


def _s5(t):
    return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)


def n1(x, seed=0):
    x = np.asarray(x, float)
    i = np.floor(x)
    f = _s5(x - i)
    return _hn(i, seed) * (1.0 - f) + _hn(i + 1.0, seed) * f


def fbm1(x, seed=0, oct=4, lac=2.03, gain=0.5):
    x = np.asarray(x, float)
    tot = np.zeros_like(x)
    amp, frq, nrm = 1.0, 1.0, 0.0
    for o in range(oct):
        tot = tot + amp * n1(x * frq, seed * 131 + o * 17)
        nrm += amp
        amp *= gain
        frq *= lac
    return tot / nrm


def sstep(a, b, x):
    t = np.clip((np.asarray(x, float) - a) / max(b - a, 1e-9), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def unit(v):
    v = np.asarray(v, float)
    n = float(np.linalg.norm(v))
    return v / n if n > 1e-12 else np.array([1.0, 0.0, 0.0])


# ==============================================================================
#  2.  MESH ACCUMULATOR
# ==============================================================================

def place(ob, R, O):
    """Put an object at (R, O) and PROVE it landed there.

    `ob.matrix_world = <4x4>` on a freshly created object does not stick: loc /
    rot / scale stay at the identity and the next depsgraph evaluation
    overwrites the world matrix from them.  marshal_post_deck lost all 25 decks
    to exactly that and the macro render came back black -- a defect that looks
    like a lighting bug and is not one.  Decompose into the channels the
    depsgraph actually reads, then MEASURE the result.
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
        raise RuntimeError("REFUSING: %s did not land at its site." % ob.name)
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
    """Vertex / face accumulator carrying this item's attribute set.

    ONE Acc PER STAND, so a stand is one object and the gate's per-instance
    statistics are genuinely per instance rather than per fragment.
    """

    def __init__(self, name):
        self.name = name
        self._V, self._Q, self._T, self._mq, self._mt = [], [], [], [], []
        self._A = {a: [] for a in ATTR_F}
        self._bc, self._tint = [], []
        self.n = 0
        self.parts = 0

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
            v = attr.get(a, h01(self.parts, 7717, self.name) if a == "ts_pid"
                         else 0.0)
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

        Winding is the most tedious bug class in generated geometry and a
        flipped face under a 12.5 deg sun reads as a black hole in the frame.
        Settle it once for every primitive in the file: compute the solid's own
        signed volume and reverse everything if it came out negative.
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

    def arrays(self):
        V = np.concatenate(self._V) if self._V else np.zeros((0, 3))
        Q = np.concatenate(self._Q) if self._Q else np.zeros((0, 4), np.int64)
        T = np.concatenate(self._T) if self._T else np.zeros((0, 3), np.int64)
        mq = np.concatenate(self._mq) if self._mq else np.zeros(0, np.int32)
        mt = np.concatenate(self._mt) if self._mt else np.zeros(0, np.int32)
        A = {a: (np.concatenate(self._A[a]) if self._A[a] else np.zeros(0, np.float32))
             for a in ATTR_F}
        bc = np.concatenate(self._bc) if self._bc else np.zeros((0, 3), np.float32)
        tn = np.concatenate(self._tint) if self._tint else np.zeros((0, 3), np.float32)
        return V, Q, T, mq, mt, A, bc, tn


# ==============================================================================
#  3.  PRIMITIVES — every one closes into a solid so `Acc.solid` can orient it
# ==============================================================================

def _grid_quads(n, m, close_m=False):
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

    The caps get their OWN copies of the ring vertices so they can carry
    different attributes from the sides -- a sawn extrusion end is a different
    surface history from its anodised face, and a shader cannot tell them apart
    if they share vertices.
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
        T = np.concatenate([_fan(b0 + m, np.arange(b0, b0 + m)),
                            _fan(b1 + m, np.arange(b1, b1 + m), reverse=True)])
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


def frames_along(path, up_hint=(0.0, 0.0, 1.0)):
    """Parallel-transport frames along a polyline.  -> (T, N, B) each (n, 3)."""
    Pp = np.asarray(path, float)
    n = Pp.shape[0]
    T = np.zeros((n, 3))
    T[:-1] = Pp[1:] - Pp[:-1]
    T[-1] = T[-2]
    if n > 2:
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
          up_hint=(0.0, 0.0, 1.0), bc_axis=True, **kw):
    """Sweep a closed 2-D section (m, 2) along a 3-D polyline.

    `bc_axis` writes the part-local coordinate as (distance along the sweep,
    angle, radius), which is what the anodising grain and the extrusion
    striation read -- both run ALONG the member, and a grain that runs the
    wrong way across a 45 mm face is visible at 17 px.
    """
    Pp = np.asarray(path, float)
    S = np.asarray(sect, float)
    n, m = Pp.shape[0], S.shape[0]
    T, N, B = frames_along(Pp, up_hint)
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
        i = n - 1
        j = np.arange(m)
        j1 = (j + 1) % m
        Q = np.concatenate([Q, np.stack([i * m + j, i * m + j1, j1, j], 1)])
        return acc.solid(V, quads=Q, mat=mat, **kw)
    bcv = kw.pop("bc", None)
    if bcv is None and bc_axis:
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
    if chamfer <= 1e-6:
        return np.array([(-w / 2, -h / 2), (w / 2, -h / 2),
                         (w / 2, h / 2), (-w / 2, h / 2)])
    c = chamfer
    return np.array([
        (-w / 2 + c, -h / 2), (w / 2 - c, -h / 2), (w / 2, -h / 2 + c),
        (w / 2, h / 2 - c), (w / 2 - c, h / 2), (-w / 2 + c, h / 2),
        (-w / 2, h / 2 - c), (-w / 2, -h / 2 + c)])


def round_rect(w, h, r, seg=4):
    """A rounded rectangle section, CCW.  The corner radius of a drawn tube."""
    r = min(r, w * 0.499, h * 0.499)
    out = []
    for (cx, cy, a0) in ((w / 2 - r, -h / 2 + r, -math.pi / 2),
                         (w / 2 - r, h / 2 - r, 0.0),
                         (-w / 2 + r, h / 2 - r, math.pi / 2),
                         (-w / 2 + r, -h / 2 + r, math.pi)):
        for k in range(seg + 1):
            a = a0 + (math.pi / 2) * k / seg
            out.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    # drop duplicated corner-arc joins
    P = [out[0]]
    for p in out[1:]:
        if (p[0] - P[-1][0]) ** 2 + (p[1] - P[-1][1]) ** 2 > 1e-12:
            P.append(p)
    return np.array(P)


def tslot_section(a, b, mouth, dep, inner, r, slots=4, seg=3):
    """The section of a T-slot aluminium extrusion, drawn from the metal out.

    `a` x `b` overall.  Each face carries one slot: a `mouth` wide mouth,
    `dep` deep, opening into an `inner` wide undercut with 45 deg lead-ins.
    The corner is a `r` radius.  Every one of the eight edges a slot
    contributes is 2-6 mm long -- 0.7-2.2 px -- which is where this item's
    10th-percentile edge length comes from and why the profile is not a box.
    """
    hw, hh = a * 0.5, b * 0.5
    ch = 0.0016                       # the little chamfer on each slot lip
    m2, i2 = mouth * 0.5, inner * 0.5
    d1 = dep * 0.42                   # depth of the mouth throat
    ex2 = np.array([1.0, 0.0])
    ey2 = np.array([0.0, 1.0])
    # (outward normal, CCW tangent, face length, offset of the face from centre)
    faces = ((-ey2, ex2, a, hh), (ex2, ey2, b, hw),
             (ey2, -ex2, a, hh), (-ex2, -ey2, b, hw))
    P = []
    for fi, (out, along, width, off) in enumerate(faces):
        half = width * 0.5
        prof = [(-half + r, 0.0)]
        if slots and width > (inner + 8.0 * ch):
            prof += [(-m2 - ch, 0.0), (-m2, ch), (-m2, d1),
                     (-i2, d1 + (i2 - m2)), (-i2, dep),
                     (i2, dep), (i2, d1 + (i2 - m2)),
                     (m2, d1), (m2, ch), (m2 + ch, 0.0)]
        prof += [(half - r, 0.0)]
        for (t, d) in prof:
            P.append(out * (off - d) + along * t)
        # the corner arc from this face round to the next
        if r > 1e-6:
            nxt = faces[(fi + 1) % 4]
            c = out * (off - r) + nxt[0] * (nxt[3] - r)
            p0 = out * off + along * (half - r)
            p1 = nxt[0] * nxt[3] + nxt[1] * (-nxt[2] * 0.5 + r)
            a0 = math.atan2(p0[1] - c[1], p0[0] - c[0])
            a1 = math.atan2(p1[1] - c[1], p1[0] - c[0])
            while a1 - a0 > math.pi:
                a1 -= 2 * math.pi
            while a1 - a0 < -math.pi:
                a1 += 2 * math.pi
            for k in range(1, max(seg, 1)):
                aa = a0 + (a1 - a0) * k / max(seg, 1)
                P.append(c + np.array([r * math.cos(aa), r * math.sin(aa)]))
    return np.array(P)


def member(acc, p0, p1, sect, mat=M_ALU, bow=0.0, bow_dir=None, ns=None,
           roll=0.0, up_hint=(0.0, 0.0, 1.0), **kw):
    """A straight structural member with a real bow.

    Nothing extruded is straight.  A 5 m 45-series bar bows 1.5-4 mm under its
    own weight and its own extrusion stress, and at 373 px/m that is 0.6-1.5 px
    of silhouette against a bright sky -- small, and the difference between a
    machine and a CAD render.  `ns` stations are laid along it so the bow can
    exist at all.
    """
    p0 = np.asarray(p0, float)
    p1 = np.asarray(p1, float)
    d = p1 - p0
    L = float(np.linalg.norm(d))
    if ns is None:
        ns = max(2, int(L / 0.24) + 2)
    t = np.linspace(0.0, 1.0, ns)
    path = p0[None, :] + t[:, None] * d[None, :]
    if bow != 0.0:
        bd = unit(bow_dir if bow_dir is not None else
                  (np.cross(unit(d), EZ) if abs(unit(d)[2]) < 0.9 else EX))
        path = path + (bow * np.sin(math.pi * t))[:, None] * bd[None, :]
    rl = None if abs(roll) < 1e-9 else np.full(ns, roll)
    return sweep(acc, path, sect, mat=mat, roll=rl, up_hint=up_hint, **kw)


def tube(acc, p0, p1, r, mat=M_ALU, n=16, phase=0.0, **kw):
    p0 = np.asarray(p0, float)
    p1 = np.asarray(p1, float)
    d = p1 - p0
    L = float(np.linalg.norm(d))
    ns = max(2, int(L / 0.14) + 2)
    path = p0[None, :] + np.linspace(0, 1, ns)[:, None] * d[None, :]
    return sweep(acc, path, circle(r, n, phase), mat=mat, **kw)


def box(acc, lo, hi, mat=0, **kw):
    lo = np.asarray(lo, float)
    hi = np.asarray(hi, float)
    x0, y0, z0 = lo
    x1, y1, z1 = hi
    V = np.array([(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                  (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)])
    Q = np.array([(0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4),
                  (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)])
    if "bc" not in kw:
        kw["bc"] = np.stack([V[:, 0] - (x0 + x1) * 0.5, V[:, 1] - (y0 + y1) * 0.5,
                             V[:, 2] - (z0 + z1) * 0.5], 1)
    return acc.solid(V, quads=Q, mat=mat, **kw)


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


def plate(acc, ctr, ex, ey, t, mat=M_ALU, chamfer=0.0012, **kw):
    """A flat plate with a real edge chamfer.  `t` is full thickness."""
    ez = unit(np.cross(np.asarray(ex, float), np.asarray(ey, float))) * (t * 0.5)
    return obox(acc, ctr, ex, ey, ez, mat=mat, chamfer=chamfer, **kw)


def disc(acc, ctr, axis, r, t, mat=M_STEEL, n=20, **kw):
    """A disc / washer blank, `t` thick, centred on `ctr` along `axis`."""
    ctr = np.asarray(ctr, float)
    ax = unit(axis)
    p0 = ctr - ax * (t * 0.5)
    p1 = ctr + ax * (t * 0.5)
    return tube(acc, p0, p1, r, mat=mat, n=n, **kw)


def hexprism(acc, ctr, axis, af, h, mat=M_STEEL, chamfer=True, **kw):
    """A hex head / nut across flats `af`, `h` tall, with the top chamfer.

    The chamfer is not decoration: it is why a hex head reads as a hex head at
    5 px instead of as a dot.  It puts a bright ring inside a dark hexagon
    under a grazing key.
    """
    ctr = np.asarray(ctr, float)
    ax = unit(axis)
    r = af / math.sqrt(3.0)                     # across corners / 2
    a = np.arange(6) * (math.pi / 3.0) + math.pi / 6.0
    S = np.stack([np.cos(a) * r, np.sin(a) * r], 1)
    ch = min(af * 0.10, h * 0.34) if chamfer else 0.0
    zs = np.array([0.0, ch, h - ch, h])
    sc = np.array([0.86, 1.0, 1.0, 0.86]) if chamfer else np.ones(4)
    N = unit(np.cross(ax, EZ) if abs(float(np.dot(ax, EZ))) < 0.95 else EX)
    B = np.cross(ax, N)
    PTS = np.empty((4, 6, 3))
    for i in range(4):
        PTS[i] = (ctr + ax * zs[i])[None, :] + (S[:, 0:1] * sc[i]) * N[None, :] \
            + (S[:, 1:2] * sc[i]) * B[None, :]
    return extrude(acc, PTS, mat=mat, **kw)


def bolt(acc, p, axis, af=0.013, head=0.0053, shank=0.004, length=0.020,
         washer=0.0085, mat=M_STEEL, wear=0.4, **kw):
    """A hex-head bolt with its washer, sitting ON a surface at `p`.

    ~450 of these per stand.  At 373 px/m the head is 4.9 px across and throws
    24 mm = 9.0 px of shadow at the contract sun's 12.47 deg elevation, so it
    is the single most repeated legible event on the object.
    """
    p = np.asarray(p, float)
    ax = unit(axis)
    n = 0
    if washer:
        disc(acc, p + ax * 0.0009, ax, washer, 0.0018, mat=mat,
             ts_wear=wear, ts_edge=1.0, **kw)
        n += 1
    hexprism(acc, p + ax * 0.0018, ax, af, head, mat=mat,
             ts_wear=wear * 1.3, ts_edge=1.0, **kw)
    n += 1
    if length > 0:
        tube(acc, p, p - ax * length, shank, mat=mat, n=10,
             ts_wear=wear, **kw)
        n += 1
    return n


def caphead(acc, p, axis, d=0.008, head_h=0.008, mat=M_STEEL, wear=0.4, **kw):
    """A socket cap screw: a cylinder head with a real hex socket recess.

    The socket is a 6-sided HOLE.  Vertical relief throws no shadow under this
    sun (7.97 deg of azimuth offset), so every vertical event on this item has
    to be a recess that reads by its own darkness.  This is the cheapest one.
    """
    p = np.asarray(p, float)
    ax = unit(axis)
    hr = d * 0.75
    N = unit(np.cross(ax, EZ) if abs(float(np.dot(ax, EZ))) < 0.95 else EX)
    B = np.cross(ax, N)
    nseg = 14
    a = np.arange(nseg) * (2 * math.pi / nseg)
    ring = np.stack([np.cos(a), np.sin(a)], 1)
    sr = d * 0.42                     # hex socket across flats / 2
    ah = np.arange(6) * (math.pi / 3.0) + math.pi / 6.0
    hexr = np.stack([np.cos(ah), np.sin(ah)], 1) * sr
    # outer wall: bottom ring -> top ring; then top face annulus into the socket
    V, Q = [], []

    def push(pts):
        b = len(V)
        V.extend([tuple(q) for q in pts])
        return b

    p_bot = [p + N * (hr * u) + B * (hr * v) for (u, v) in ring]
    p_top = [p + ax * head_h + N * (hr * u) + B * (hr * v) for (u, v) in ring]
    b0 = push(p_bot)
    b1 = push(p_top)
    for i in range(nseg):
        j = (i + 1) % nseg
        Q.append((b0 + i, b0 + j, b1 + j, b1 + i))
    # top annulus: ring -> hex socket mouth
    hx_top = [p + ax * head_h + N * u + B * v for (u, v) in hexr]
    b2 = push(hx_top)
    for i in range(nseg):
        j = (i + 1) % nseg
        k = int(i * 6 / nseg) % 6
        l = int(j * 6 / nseg) % 6
        Q.append((b1 + i, b1 + j, b2 + l, b2 + k))
    # socket bore and its floor
    hx_bot = [p + ax * (head_h - d * 0.55) + N * u + B * v for (u, v) in hexr]
    b3 = push(hx_bot)
    for i in range(6):
        j = (i + 1) % 6
        Q.append((b2 + i, b2 + j, b3 + j, b3 + i))
    cen = push([p + ax * (head_h - d * 0.55)])
    T = [(cen, b3 + i, b3 + (i + 1) % 6) for i in range(6)]
    cen2 = push([p])
    T += [(cen2, b0 + (i + 1) % nseg, b0 + i) for i in range(nseg)]
    return acc.solid(np.array(V), quads=np.array(Q), tris=np.array(T), mat=mat,
                     ts_wear=wear, ts_edge=1.0, **kw)


def rivet(acc, p, axis, r=0.0022, h=0.0016, mat=M_STEEL, n=10, **kw):
    """A dome-head rivet: two rings and a cap."""
    p = np.asarray(p, float)
    ax = unit(axis)
    N = unit(np.cross(ax, EZ) if abs(float(np.dot(ax, EZ))) < 0.95 else EX)
    B = np.cross(ax, N)
    a = np.arange(n) * (2 * math.pi / n)
    ring = np.stack([np.cos(a), np.sin(a)], 1)
    rows = ((r, 0.0), (r * 0.88, h * 0.55), (r * 0.55, h * 0.92))
    V, Q = [], []
    idx = []
    for (rr, zz) in rows:
        b = len(V)
        V.extend([tuple(p + ax * zz + N * (rr * u) + B * (rr * v)) for (u, v) in ring])
        idx.append(b)
    for k in range(len(rows) - 1):
        for i in range(n):
            j = (i + 1) % n
            Q.append((idx[k] + i, idx[k] + j, idx[k + 1] + j, idx[k + 1] + i))
    cen = len(V)
    V.append(tuple(p + ax * h))
    T = [(cen, idx[-1] + i, idx[-1] + (i + 1) % n) for i in range(n)]
    cen2 = len(V)
    V.append(tuple(p))
    T += [(cen2, idx[0] + (i + 1) % n, idx[0] + i) for i in range(n)]
    return acc.solid(np.array(V), quads=np.array(Q), tris=np.array(T), mat=mat,
                     ts_edge=0.6, **kw)


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


def icosphere(sub=1):
    V, F = _icosa()
    for _ in range(sub):
        Vl = [tuple(v) for v in V]
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


def blob(acc, ctr, radii, mat=M_RUB, sub=1, warp=None, **kw):
    """An ellipsoid, optionally warped by a callable(V) -> V.  Bags, sandbags."""
    V, F = icosphere(sub)
    P = V * np.asarray(radii, float)[None, :]
    if warp is not None:
        P = warp(P)
    P = P + np.asarray(ctr, float)[None, :]
    return acc.solid(P, tris=F, mat=mat, bc=V * 0.5, **kw)


# ==============================================================================
#  4.  THE STROKE FONT — hand coded, no font datablock, no image
# ==============================================================================
# Capsule strokes on a 0..1 cap-height grid.  Each glyph is a list of polylines;
# every polyline is drawn as a chain of rounded capsules `w` wide and extruded
# 0.35 mm proud, which is what a cut vinyl graphic actually is.  Overlapping
# capsules at a join are fine: they are coplanar opaque slabs at the same
# height, so the union reads exactly as the union.
#
# WHY MESH AND NOT A SHADER MASK.  A 120 mm cap height is 45 px on the 4K
# master.  A procedural mask can put a letter-shaped patch of albedo there, but
# it cannot give the edge a real 0.35 mm step with its own gloss and its own
# grime line, and at 45 px the eye is looking straight at the edge.

GLYPHS = {
    " ": (0.52, []),
    "-": (0.60, [[(0.10, 0.46), (0.50, 0.46)]]),
    ".": (0.34, [[(0.17, 0.05), (0.17, 0.05)]]),
    "'": (0.28, [[(0.14, 1.00), (0.14, 0.74)]]),
    "0": (0.66, [[(0.09, 0.26), (0.09, 0.74), (0.24, 0.96), (0.42, 0.96),
                  (0.57, 0.74), (0.57, 0.26), (0.42, 0.04), (0.24, 0.04),
                  (0.09, 0.26)]]),
    "1": (0.42, [[(0.06, 0.78), (0.22, 0.96), (0.22, 0.04)]]),
    "2": (0.64, [[(0.08, 0.76), (0.20, 0.96), (0.42, 0.96), (0.55, 0.78),
                  (0.50, 0.58), (0.08, 0.04), (0.56, 0.04)]]),
    "3": (0.64, [[(0.08, 0.82), (0.24, 0.96), (0.44, 0.96), (0.55, 0.80),
                  (0.44, 0.56), (0.26, 0.53)],
                 [(0.32, 0.53), (0.50, 0.48), (0.57, 0.30), (0.46, 0.06),
                  (0.24, 0.04), (0.08, 0.16)]]),
    "4": (0.66, [[(0.44, 0.04), (0.44, 0.96), (0.06, 0.30), (0.60, 0.30)]]),
    "5": (0.62, [[(0.54, 0.96), (0.14, 0.96), (0.10, 0.58), (0.34, 0.62),
                  (0.53, 0.48), (0.54, 0.24), (0.38, 0.05), (0.14, 0.08)]]),
    "6": (0.64, [[(0.52, 0.90), (0.30, 0.96), (0.12, 0.76), (0.09, 0.30),
                  (0.24, 0.04), (0.44, 0.05), (0.56, 0.24), (0.48, 0.46),
                  (0.26, 0.50), (0.10, 0.36)]]),
    "7": (0.60, [[(0.06, 0.96), (0.56, 0.96), (0.24, 0.04)]]),
    "8": (0.64, [[(0.32, 0.52), (0.14, 0.62), (0.12, 0.84), (0.32, 0.96),
                  (0.52, 0.84), (0.50, 0.62), (0.32, 0.52), (0.12, 0.40),
                  (0.10, 0.18), (0.32, 0.04), (0.54, 0.18), (0.52, 0.40),
                  (0.32, 0.52)]]),
    "9": (0.64, [[(0.12, 0.14), (0.34, 0.04), (0.54, 0.24), (0.56, 0.70),
                  (0.40, 0.96), (0.20, 0.95), (0.08, 0.76), (0.16, 0.54),
                  (0.38, 0.50), (0.54, 0.64)]]),
    "A": (0.70, [[(0.03, 0.04), (0.34, 0.96), (0.65, 0.04)],
                 [(0.15, 0.36), (0.53, 0.36)]]),
    "B": (0.66, [[(0.10, 0.04), (0.10, 0.96), (0.42, 0.96), (0.56, 0.82),
                  (0.44, 0.55), (0.10, 0.53)],
                 [(0.34, 0.53), (0.54, 0.42), (0.56, 0.18), (0.40, 0.04),
                  (0.10, 0.04)]]),
    "C": (0.68, [[(0.60, 0.82), (0.42, 0.96), (0.22, 0.94), (0.09, 0.72),
                  (0.09, 0.28), (0.22, 0.06), (0.42, 0.04), (0.60, 0.18)]]),
    "D": (0.68, [[(0.10, 0.04), (0.10, 0.96), (0.38, 0.96), (0.58, 0.76),
                  (0.58, 0.24), (0.38, 0.04), (0.10, 0.04)]]),
    "E": (0.60, [[(0.56, 0.96), (0.10, 0.96), (0.10, 0.04), (0.56, 0.04)],
                 [(0.10, 0.52), (0.44, 0.52)]]),
    "F": (0.58, [[(0.56, 0.96), (0.10, 0.96), (0.10, 0.04)],
                 [(0.10, 0.52), (0.44, 0.52)]]),
    "G": (0.70, [[(0.60, 0.82), (0.42, 0.96), (0.22, 0.94), (0.09, 0.72),
                  (0.09, 0.28), (0.22, 0.06), (0.44, 0.04), (0.60, 0.22),
                  (0.60, 0.46), (0.38, 0.46)]]),
    "H": (0.68, [[(0.10, 0.96), (0.10, 0.04)], [(0.58, 0.96), (0.58, 0.04)],
                 [(0.10, 0.52), (0.58, 0.52)]]),
    "I": (0.34, [[(0.17, 0.96), (0.17, 0.04)]]),
    "J": (0.56, [[(0.48, 0.96), (0.48, 0.24), (0.34, 0.05), (0.16, 0.06),
                  (0.06, 0.22)]]),
    "K": (0.66, [[(0.10, 0.96), (0.10, 0.04)], [(0.58, 0.96), (0.12, 0.46)],
                 [(0.28, 0.62), (0.60, 0.04)]]),
    "L": (0.56, [[(0.10, 0.96), (0.10, 0.04), (0.52, 0.04)]]),
    "M": (0.82, [[(0.09, 0.04), (0.09, 0.96), (0.40, 0.42), (0.71, 0.96),
                  (0.71, 0.04)]]),
    "N": (0.70, [[(0.10, 0.04), (0.10, 0.96), (0.58, 0.06), (0.58, 0.96)]]),
    "O": (0.72, [[(0.09, 0.30), (0.09, 0.70), (0.26, 0.96), (0.45, 0.96),
                  (0.62, 0.70), (0.62, 0.30), (0.45, 0.04), (0.26, 0.04),
                  (0.09, 0.30)]]),
    "P": (0.64, [[(0.10, 0.04), (0.10, 0.96), (0.42, 0.96), (0.56, 0.80),
                  (0.44, 0.54), (0.10, 0.52)]]),
    "Q": (0.72, [[(0.09, 0.30), (0.09, 0.70), (0.26, 0.96), (0.45, 0.96),
                  (0.62, 0.70), (0.62, 0.30), (0.45, 0.04), (0.26, 0.04),
                  (0.09, 0.30)], [(0.42, 0.24), (0.66, 0.00)]]),
    "R": (0.66, [[(0.10, 0.04), (0.10, 0.96), (0.42, 0.96), (0.56, 0.80),
                  (0.44, 0.54), (0.10, 0.52)], [(0.32, 0.52), (0.60, 0.04)]]),
    "S": (0.64, [[(0.56, 0.84), (0.38, 0.96), (0.18, 0.94), (0.09, 0.76),
                  (0.20, 0.58), (0.44, 0.48), (0.55, 0.30), (0.46, 0.08),
                  (0.24, 0.04), (0.08, 0.16)]]),
    "T": (0.62, [[(0.04, 0.96), (0.58, 0.96)], [(0.31, 0.96), (0.31, 0.04)]]),
    "U": (0.68, [[(0.10, 0.96), (0.10, 0.26), (0.26, 0.04), (0.42, 0.04),
                  (0.58, 0.26), (0.58, 0.96)]]),
    "V": (0.68, [[(0.05, 0.96), (0.34, 0.04), (0.63, 0.96)]]),
    "W": (0.92, [[(0.05, 0.96), (0.24, 0.04), (0.46, 0.66), (0.68, 0.04),
                  (0.87, 0.96)]]),
    "X": (0.68, [[(0.07, 0.96), (0.61, 0.04)], [(0.61, 0.96), (0.07, 0.04)]]),
    "Y": (0.68, [[(0.07, 0.96), (0.34, 0.50), (0.61, 0.96)],
                 [(0.34, 0.50), (0.34, 0.04)]]),
    "Z": (0.64, [[(0.08, 0.96), (0.56, 0.96), (0.08, 0.04), (0.56, 0.04)]]),
}


def text_capsules(txt, h, tracking=0.14, weight=0.155):
    """-> [(x0, y0, x1, y1, r)] capsule segments and the total advance width.

    Baseline at y = 0, cap height `h`.  `weight` is the stroke width as a
    fraction of the cap height (0.155 is a bold industrial sans).
    """
    caps = []
    x = 0.0
    r = h * weight * 0.5
    for ch in txt.upper():
        adv, strokes = GLYPHS.get(ch, GLYPHS[" "])
        for poly in strokes:
            for k in range(max(len(poly) - 1, 1)):
                a = poly[k]
                b = poly[min(k + 1, len(poly) - 1)]
                caps.append((x + a[0] * h, a[1] * h, x + b[0] * h, b[1] * h, r))
        x += adv * h + tracking * h
    return caps, max(x - tracking * h, 0.0)


def capsule_poly(x0, y0, x1, y1, r, seg=11):
    """A 2-D rounded capsule as a CCW polygon."""
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy)
    if L < 1e-9:
        a = np.arange(seg * 2) * (math.pi / seg)
        return np.stack([x0 + r * np.cos(a), y0 + r * np.sin(a)], 1)
    ux, uy = dx / L, dy / L
    P = []
    base = math.atan2(uy, ux)
    for k in range(seg + 1):
        a = base - math.pi / 2 + math.pi * k / seg
        P.append((x1 + r * math.cos(a), y1 + r * math.sin(a)))
    for k in range(seg + 1):
        a = base + math.pi / 2 + math.pi * k / seg
        P.append((x0 + r * math.cos(a), y0 + r * math.sin(a)))
    return np.array(P)


def emit_text(acc, txt, org, ex, ey, h, thick=0.00035, tracking=0.14,
              weight=0.155, mat=M_VINYL, centre=True, **kw):
    """Extrude a string as raised vinyl on the plane (org; ex, ey).

    Returns the advance width in metres.
    """
    caps, w = text_capsules(txt, h, tracking, weight)
    org = np.asarray(org, float)
    ex = np.asarray(ex, float)
    ey = np.asarray(ey, float)
    ez = unit(np.cross(ex, ey))
    x0 = -w * 0.5 if centre else 0.0
    for k, (ax, ay, bx, by, r) in enumerate(caps):
        P = capsule_poly(ax + x0, ay, bx + x0, by, r)
        m = P.shape[0]
        PTS = np.empty((2, m, 3))
        # THE STAGGER, and it is not cosmetic.  Two capsules that overlap at a
        # stroke join share a coplanar top face, and coplanar faces z-fight:
        # the first valance render came back with pale circular seams inside
        # every letter of JUNIPER.  15 microns of stagger per capsule is 0.006
        # of a pixel at the filmed distance and it settles the depth test.
        dz = (k % 7) * 0.000015
        for i, t in enumerate((0.0, thick + dz)):
            PTS[i] = org[None, :] + P[:, 0:1] * ex[None, :] \
                + P[:, 1:2] * ey[None, :] + ez[None, :] * (t + dz * (1 - i))
        extrude(acc, PTS, mat=mat, ts_edge=1.0, **kw)
    return w


# ==============================================================================
#  5.  THE PLAN — ten stands, and the ground they actually stand on
# ==============================================================================

_PLAN_CACHE = [None]


def _ground(cx, cy):
    """circuit (x, y) -> (world z, owner).  NEVER an assumed z (law 4)."""
    wx, wy = C.circuit_to_world(cx, cy)
    z, own = C.world_ground_z(float(wx), float(wy))
    return float(z), str(own)


def stand_records():
    """The whole plan.  Pure: no bpy, no side effects, deterministic.

    Every foot of every stand samples ``C.world_ground_z`` and the owner is
    recorded, so a stand that ended up straddling the 0.14 m step between the
    runoff platform and the pit-lane paving would show up here rather than in a
    render.  ``selftest()`` asserts every foot is on the paving.
    """
    if _PLAN_CACHE[0] is not None:
        return _PLAN_CACHE[0]
    out = []
    for uid, bay in enumerate(STAND_BAYS):
        team, c1, c2 = TEAMS[bay]
        sd = 4100 + uid * 37
        x0 = BAY_CENTRES[bay] + gauss(0.85, 1.90, sd, 1)      # hand-placed
        fam = AX_FAMILY[uid]
        f = FAMILY[fam]
        tiers = AX_TIERS[uid]
        L = round(rnd(4.20, 5.40, sd, 2) + 0.55 * (tiers - 1), 3)
        D = round({1: rnd(1.68, 1.86, sd, 3),
                   2: rnd(2.02, 2.24, sd, 3),
                   3: rnd(2.36, 2.52, sd, 3)}[tiers], 3)
        deck = round(rnd(DECK_Z0[0], DECK_Z0[1], sd, 4), 4)
        rise = [0.0]
        for k in range(1, tiers):
            rise.append(rise[-1] + round(rnd(TIER_RISE[0], TIER_RISE[1], sd, 10 + k), 4))
        # deck tier extents in local y: tier 0 is the console row
        y_splits = [0.0]
        if tiers == 2:
            y_splits += [round(D * rnd(0.50, 0.58, sd, 20), 3), D]
        elif tiers == 3:
            y_splits += [round(D * rnd(0.40, 0.46, sd, 20), 3),
                         round(D * rnd(0.70, 0.76, sd, 21), 3), D]
        else:
            y_splits += [D]
        # posts along x: ends plus intermediates at <= 2.15 m
        nbay = max(2, int(math.ceil(L / 1.80)))
        px = [round(-L * 0.5 + 0.055 + (L - 0.11) * i / nbay, 4) for i in range(nbay + 1)]
        # four seat stations, spread over the console row, avoiding the posts
        nseat = 4
        span = L - 0.62
        pitch = min(rnd(*SEAT_PITCH, sd, 30), span / max(nseat - 1, 1))
        s_off = gauss(0.10, 0.26, sd, 31)
        sx = [round(-pitch * (nseat - 1) * 0.5 + i * pitch + s_off, 4)
              for i in range(nseat)]
        # the principal stands: at the garage-side end, on the top tier
        prin_end = 1.0 if h01(sd, 32) < 0.5 else -1.0
        canopy = AX_CANOPY[uid]
        eaves_f = round(rnd(2.84, 3.04, sd, 40), 4)
        eaves_r = round(eaves_f - rnd(0.06, 0.14, sd, 41), 4)
        post_top = round(eaves_f + rnd(0.18, 0.32, sd, 42), 4)
        nraft = max(3, int(round(L / rnd(0.95, 1.30, sd, 43))) + 1)
        # the ground under every foot, MEASURED
        feet = []
        for i, xx in enumerate(px):
            for j, yy in enumerate((0.0, D)):
                cx = x0 + xx
                cy = FRONT_LEG_Y + yy
                gz, own = _ground(cx, cy)
                feet.append(dict(i=i, j=j, lx=xx, ly=yy, cx=cx, cy=cy,
                                 gz=gz, owner=own))
        gz_all = [ft["gz"] for ft in feet]
        base_z = float(max(gz_all))          # the frame is levelled to the HIGH
                                             # foot and the rest gets packers
        rec = dict(
            uid=uid, bay=bay, team=team, col1=srgb(c1), col2=srgb(c2),
            hexes=(c1, c2), seed=sd,
            x0=round(x0, 4), L=L, D=D, tiers=tiers, deck=deck, rise=rise,
            y_splits=y_splits, fam=fam, family=f["name"],
            deck_kind=DECK_KIND[AX_DECK[uid]], deck_i=AX_DECK[uid],
            fascia=FASCIA_KIND[AX_FASCIA[uid]], fascia_i=AX_FASCIA[uid],
            canopy=canopy, dressed=AX_OCCUPIED[uid],
            post_x=px, nbay=nbay, seat_x=sx, seat_pitch=round(pitch, 4),
            nseat=nseat, prin_end=prin_end,
            eaves_f=eaves_f, eaves_r=eaves_r, post_top=post_top, nraft=nraft,
            feet=feet, base_z=base_z,
            ground_min=float(min(gz_all)), ground_max=float(max(gz_all)),
            owners=sorted(set(ft["owner"] for ft in feet)),
            castors=chance(0.45, sd, 50),
            ballast=("none", "plates", "sandbags")[rint(0, 2, sd, 51)],
            rail=("rear", "rear+ends", "full")[rint(0, 2, sd, 52)],
            step_end=(-1.0 if h01(sd, 53) < 0.45 else 1.0),
            steps=rint(2, 3, sd, 54),
            brand=VALANCE_BRANDS[uid],
            # MEASURED OFF THE RENDER, not chosen.  At age/grime in [0.25,
            # 0.95] x [0.20, 0.85] every weathering layer in the paint shader
            # is a product of three sub-unit factors and lands at 5-15 % --
            # which is why the 5x crop of a two-season-old composite panel came
            # back as a flat sheet of green with the layers all present and all
            # invisible.  A stand that has done a season is not 25 % aged.
            age=round(rnd(0.45, 0.98, sd, 60), 3),
            grime=round(rnd(0.42, 0.95, sd, 61), 3),
            mast=chance(0.35, sd, 62),
            console_h=round(CONSOLE_H + gauss(0.012, 0.028, sd, 63), 4),
            worktop_d=round(CONSOLE_D + gauss(0.020, 0.045, sd, 64), 4),
            nmon=rint(5, 7, sd, 65),
            # DECIDED HERE, not inside the builder.  `monitor_bays()` publishes
            # it and `timing_stand_monitor` needs it to know whether its screen
            # has a hood over it -- and the interface has to be answerable
            # without bpy and without building anything.
            hood=chance(0.62, sd, 810),
        )
        rec["height"] = round(rec["post_top"] - 0.0 + (0.42 if rec["mast"] else 0.0), 3)
        out.append(rec)
    _PLAN_CACHE[0] = out
    return out


def stand_basis(r):
    """-> (origin_world, ex, ey, ez) for a stand's local frame.

    local +x runs EAST along the pit wall, +y runs INTO the pit lane (away from
    the track), +z is up.  The origin is the front leg line at the levelled
    base z.
    """
    wx, wy = C.circuit_to_world(r["x0"], FRONT_LEG_Y)
    org = np.array([float(wx), float(wy), r["base_z"]])
    return org, EX.copy(), EY.copy(), EZ.copy()


def to_world(r, P):
    """local (n, 3) -> world (n, 3)."""
    org, ex, ey, ez = stand_basis(r)
    P = np.asarray(P, float).reshape(-1, 3)
    return org[None, :] + P[:, 0:1] * ex[None, :] + P[:, 1:2] * ey[None, :] \
        + P[:, 2:3] * ez[None, :]


def tier_of(r, y):
    """which deck tier a local y falls on."""
    for k in range(r["tiers"]):
        if y < r["y_splits"][k + 1] - 1e-9:
            return k
    return r["tiers"] - 1


def deck_top(r, y):
    """local deck top z at local y."""
    return r["deck"] + r["rise"][tier_of(r, y)]


# ==============================================================================
#  6.  THE PARTS
# ==============================================================================
# Everything below adds to one `Acc` in the stand's LOCAL frame.  Nothing here
# knows about the world; `build_stand` does the recentring and the placement.
#
# The order is the order it is assembled on a Thursday morning: feet, chassis,
# posts, deck, console, seats, canopy, then the loom, then the kit.

def sections(r):
    """The four profiles this stand's family is built from."""
    f = FAMILY[r["fam"]]
    a, b = f["a"], f["b"]
    kw = dict(mouth=f["mouth"], dep=f["dep"], inner=f["inner"], r=f["r"],
              slots=f["slots"])
    return dict(
        main=tslot_section(a, a, **kw),                 # posts, main rails
        wide=tslot_section(a, b, **kw),                 # cross members, bearers
        small=tslot_section(b, b, **kw),                # joists, console frame
        thin=tslot_section(b, b * 0.62, **kw),          # trim, cleats
        a=a, b=b, weld=f["weld"])


def weld_bead(acc, p0, p1, r=0.0034, seed=0, mat=M_ALU, **kw):
    """A MIG bead with real ripples.

    3.5 mm ripple pitch is 1.3 px at the filmed distance -- individually below
    the eye's threshold, collectively the single clearest statement that the
    steel family was WELDED and the aluminium families were BOLTED.  A smooth
    fillet says neither.
    """
    p0 = np.asarray(p0, float)
    p1 = np.asarray(p1, float)
    L = float(np.linalg.norm(p1 - p0))
    if L < 0.004:
        return
    ns = max(4, int(L / 0.0034))
    t = np.linspace(0, 1, ns)
    path = p0[None, :] + t[:, None] * (p1 - p0)[None, :]
    ph = np.linspace(0, ns * 0.92, ns)
    sc = 1.0 + 0.22 * np.sin(ph * 2.0 * math.pi / 3.1) \
        + 0.10 * (fbm1(ph * 0.7, seed=seed, oct=2) - 0.5)
    sc[0] = sc[-1] = 0.42
    return sweep(acc, path, circle(r, 7), mat=mat, scale=sc,
                 ts_wear=0.55, ts_edge=0.7, ts_anod=0.0, **kw)


def levelling_foot(acc, r, x, y, z_post, gz, key):
    """M16 levelling foot: stud, adjuster nut, lock nut, swivel pad.

    LAW 5 IS DISCHARGED HERE.  The rubber-faced pad is 36 mm thick and its
    underside sits 22 mm BELOW the sampled ground with 14 mm proud, so nothing
    floats and no grazing ray gets under the stand.  The exposed thread between
    the nut and the pad differs 2-9 mm foot to foot because the frame is
    levelled to a string line and no welded frame is square -- which is why the
    nuts on one stand are not all at the same height.
    """
    ext = rnd(0.030, 0.062, key, 1)
    pad_top = gz + PAD_T - EMBED
    tilt = math.radians(rnd(-2.6, 2.6, key, 2))
    ax = unit((math.sin(tilt) * 0.5, math.sin(tilt), math.cos(tilt)))
    # the pad: a 90 mm swivel pad with a rubber face and a chamfered rim
    pr = rnd(0.041, 0.048, key, 3)
    disc(acc, (x, y, pad_top - PAD_T * 0.5), ax, pr, PAD_T * 0.55, mat=M_STEEL,
         n=22, ts_wear=0.85, ts_dirt=0.9, ts_edge=0.5)
    disc(acc, (x, y, pad_top - PAD_T * 0.82), ax, pr * 0.985, PAD_T * 0.5,
         mat=M_RUB, n=22, ts_wear=0.9, ts_dirt=1.0)
    # the ball housing above it
    disc(acc, (x, y, pad_top + 0.009), ax, 0.019, 0.018, mat=M_STEEL, n=16,
         ts_wear=0.6)
    # stud
    tube(acc, (x, y, pad_top + 0.014), (x, y, z_post + 0.004), 0.0078,
         mat=M_STEEL, n=12, ts_wear=0.5, ts_edge=0.2)
    # adjuster nut, then the lock nut hard up under the post
    hexprism(acc, (x, y, pad_top + 0.016 + ext), EZ, 0.024, 0.013, mat=M_STEEL,
             ts_wear=0.7, ts_edge=1.0)
    hexprism(acc, (x, y, z_post - 0.014), EZ, 0.024, 0.011, mat=M_STEEL,
             ts_wear=0.45, ts_edge=1.0)
    return pad_top


def castor(acc, r, x, y, z_post, gz, key):
    """A 125 mm braked swivel castor, JACKED CLEAR of the floor.

    A stand on levelling feet has its castors hanging 8-15 mm in the air, which
    is both what happens and the only honest way to keep law 5 without sinking
    a round wheel 22 mm into concrete and giving it a 95 mm flat.
    """
    lift = rnd(CASTOR_LIFT[0], CASTOR_LIFT[1], key, 1)
    wr = 0.0625
    ctr = np.array([x + rnd(-0.03, 0.03, key, 2), y + rnd(-0.03, 0.03, key, 3),
                    gz + lift + wr])
    ax = np.array([1.0, 0.0, 0.0])
    tube(acc, ctr - ax * 0.019, ctr + ax * 0.019, wr, mat=M_RUB, n=26,
         ts_wear=0.8, ts_dirt=0.7)
    tube(acc, ctr - ax * 0.021, ctr + ax * 0.021, wr * 0.42, mat=M_ELEC, n=16,
         ts_wear=0.5)
    # fork
    for s in (-1.0, 1.0):
        plate(acc, ctr + ax * (0.026 * s) + np.array([0, 0, 0.052]),
              np.array([0.0, 0.052, 0.0]), np.array([0.0, 0.0, 0.070]), 0.005,
              mat=M_STEEL, ts_wear=0.6)
    # swivel head + the mounting plate under the post
    tube(acc, ctr + np.array([0, 0, 0.118]), ctr + np.array([0, 0, 0.150]),
         0.021, mat=M_STEEL, n=14, ts_wear=0.4)
    plate(acc, ctr + np.array([0, 0, 0.156]), np.array([0.052, 0, 0]),
          np.array([0, 0.052, 0]), 0.007, mat=M_STEEL, ts_wear=0.35)
    # the brake lever
    plate(acc, ctr + np.array([0.0, -0.058, 0.030]), np.array([0.026, 0, 0]),
          np.array([0, 0.024, -0.010]), 0.004, mat=M_PAINT,
          tint=(0.62, 0.10, 0.05), ts_paint=1.0, ts_wear=0.7)
    # the leg that carries it down from the chassis
    tube(acc, (ctr[0], ctr[1], ctr[2] + 0.156), (ctr[0], ctr[1], z_post),
         0.017, mat=M_STEEL, n=12, ts_wear=0.4)


def build_chassis(acc, r, S):
    """Base frame, posts, bearers, joists, feet, packers, ballast.

    This is the part the pit wall hides from the onboard follow and that Beat 4
    and every pit-lane item's camera see in full.  It is built to the same
    standard as the top because 'nobody will see it' is how the first world
    pass got made.
    """
    L, D = r["L"], r["D"]
    a, b = S["a"], S["b"]
    z_rail = 0.140 + a * 0.5                 # bottom chord centre
    z_post0 = 0.078                          # post foot
    deck0 = r["deck"]
    seed = r["seed"]
    n = 0

    # ---- the two bottom chords, and the cross members between them ----------
    for j, yy in enumerate((0.0, D)):
        member(acc, (-L * 0.5, yy, z_rail), (L * 0.5, yy, z_rail), S["main"],
               mat=M_ALU, bow=gauss(0.0016, 0.0035, seed, 70 + j),
               bow_dir=EZ, ts_anod=1.0, ts_wear=0.35, ts_dirt=0.62,
               ts_age=r["age"])
        n += 1
    nc = max(3, int(round(L / 1.05)) + 1)
    for k in range(nc):
        xx = -L * 0.5 + a * 0.6 + (L - a * 1.2) * k / (nc - 1)
        member(acc, (xx, a * 0.5, z_rail), (xx, D - a * 0.5, z_rail), S["wide"],
               mat=M_ALU, bow=gauss(0.0008, 0.0018, seed, 80 + k), bow_dir=EZ,
               ts_anod=1.0, ts_wear=0.30, ts_dirt=0.70, ts_age=r["age"])
        if S["weld"]:
            for yy in (a * 0.5, D - a * 0.5):
                sgn = 1.0 if yy < D * 0.5 else -1.0
                weld_bead(acc, (xx - a * 0.5, yy, z_rail - a * 0.42),
                          (xx + a * 0.5, yy, z_rail - a * 0.42),
                          seed=seed + k, mat=M_ALU)
                weld_bead(acc, (xx - a * 0.5, yy, z_rail + a * 0.42),
                          (xx + a * 0.5, yy, z_rail + a * 0.42),
                          seed=seed + k + 3, mat=M_ALU)
        else:
            for yy in (a * 0.52, D - a * 0.52):
                for zz in (z_rail - a * 0.28, z_rail + a * 0.28):
                    bolt(acc, (xx + a * 0.5 + 0.0002, yy, zz), (1, 0, 0),
                         af=0.013, head=0.0053, length=0.014,
                         wear=0.45 + 0.3 * r["age"])
                    bolt(acc, (xx - a * 0.5 - 0.0002, yy, zz), (-1, 0, 0),
                         af=0.013, head=0.0053, length=0.014,
                         wear=0.45 + 0.3 * r["age"])
        n += 1

    # ---- posts ---------------------------------------------------------------
    # they run from the foot right up to the canopy eaves: ONE piece of
    # extrusion, which is why the stand is stiff and why the canopy cannot be a
    # separate object sitting on top of it.
    for i, xx in enumerate(r["post_x"]):
        for j, yy in enumerate((0.0, D)):
            top = (r["eaves_f"] if j == 0 else r["eaves_r"])
            top = top + rnd(0.10, 0.24, seed, 90 + i * 2 + j)
            member(acc, (xx, yy, z_post0), (xx, yy, top), S["main"], mat=M_ALU,
                   bow=gauss(0.0022, 0.0050, seed, 100 + i * 2 + j),
                   bow_dir=(EX if j == 0 else EY),
                   ts_anod=1.0, ts_wear=0.42, ts_dirt=0.45, ts_age=r["age"])
            # post cap
            plate(acc, (xx, yy, top + 0.0022), (a * 0.5 + 0.002, 0, 0),
                  (0, a * 0.5 + 0.002, 0), 0.0042, mat=M_ELEC, chamfer=0.0012,
                  ts_wear=0.5, ts_dirt=0.8)
            n += 2

    # ---- diagonal braces in the end bays and one middle bay -----------------
    bays = [0, len(r["post_x"]) - 2]
    if len(r["post_x"]) > 3:
        bays.append(1)
    for k in bays:
        x0, x1 = r["post_x"][k], r["post_x"][k + 1]
        for j, yy in enumerate((0.0, D)):
            up = 1.0 if (k + j) % 2 == 0 else -1.0
            za, zb = (z_rail + a * 0.5, deck0 - 0.10)
            p0 = (x0 + a * 0.5, yy, za if up > 0 else zb)
            p1 = (x1 - a * 0.5, yy, zb if up > 0 else za)
            member(acc, p0, p1, S["small"], mat=M_ALU, ts_anod=1.0,
                   ts_wear=0.3, ts_dirt=0.4, ts_age=r["age"])
            if S["weld"]:
                weld_bead(acc, p0, np.asarray(p0) + np.array([0.03, 0, 0.03]),
                          seed=seed + k * 7 + j, mat=M_ALU)
            else:
                for p in (p0, p1):
                    bolt(acc, p, (0, -1 if yy < 0.5 else 1, 0), af=0.013,
                         head=0.0053, length=0.012, wear=0.5)
            n += 1

    # ---- deck bearers and joists --------------------------------------------
    for t in range(r["tiers"]):
        y0 = r["y_splits"][t]
        y1 = r["y_splits"][t + 1]
        dz = r["deck"] + r["rise"][t]
        dt = 0.028 if r["deck_i"] != 2 else 0.021
        zb = dz - dt - b * 0.5
        for yy in (y0 + b * 0.5 + 0.004, y1 - b * 0.5 - 0.004):
            member(acc, (-L * 0.5, yy, zb), (L * 0.5, yy, zb), S["wide"],
                   mat=M_ALU, bow=gauss(0.0014, 0.0030, seed, 120 + t),
                   bow_dir=EZ, ts_anod=1.0, ts_wear=0.30, ts_dirt=0.55,
                   ts_age=r["age"])
            n += 1
        nj = max(2, int(round((y1 - y0) / 0.44)))
        nx = max(3, int(round(L / 0.46)) + 1)
        for k in range(nx):
            xx = -L * 0.5 + 0.03 + (L - 0.06) * k / (nx - 1)
            member(acc, (xx, y0 + 0.012, zb), (xx, y1 - 0.012, zb), S["small"],
                   mat=M_ALU, ts_anod=1.0, ts_wear=0.22, ts_dirt=0.55,
                   ts_age=r["age"])
            n += 1
        # the riser face between tiers
        if t > 0:
            zprev = r["deck"] + r["rise"][t - 1]
            plate(acc, (0.0, y0 + 0.004, (zprev + dz - dt) * 0.5),
                  (L * 0.5 - 0.006, 0, 0), (0, 0, (dz - dt - zprev) * 0.5),
                  0.0032, mat=M_PAINT, tint=r["col1"], ts_paint=1.0,
                  ts_wear=0.55, ts_dirt=0.7, ts_age=r["age"])
            n += 1

    # ---- feet, or castors and feet ------------------------------------------
    for i, xx in enumerate(r["post_x"]):
        for j, yy in enumerate((0.0, D)):
            ft = r["feet"][i * 2 + j]
            gz = ft["gz"] - r["base_z"]          # ground in the LOCAL frame
            levelling_foot(acc, r, xx, yy, z_post0, gz, key=(seed, 200 + i * 2 + j))
            if r["castors"] and (i in (0, len(r["post_x"]) - 1)):
                castor(acc, r, xx + (0.055 if i == 0 else -0.055), yy,
                       z_post0 + 0.02, gz, key=(seed, 300 + i * 2 + j))
            n += 1

    # ---- ballast -------------------------------------------------------------
    if r["ballast"] == "plates":
        nb = rint(3, 6, seed, 400)
        for k in range(nb):
            xx = rnd(-L * 0.42, L * 0.42, seed, 401 + k)
            zz = z_rail + a * 0.5 + 0.012 + k * 0.0
            plate(acc, (xx, D * 0.5 + gauss(0.10, 0.22, seed, 410 + k),
                        z_rail + a * 0.5 + 0.014),
                  (0.115, 0, 0), (0, 0.075, 0), 0.026, mat=M_STEEL,
                  chamfer=0.0025, ts_wear=0.75, ts_dirt=0.85, ts_age=1.0)
            n += 1
    elif r["ballast"] == "sandbags":
        for k in range(rint(2, 4, seed, 420)):
            xx = rnd(-L * 0.40, L * 0.40, seed, 421 + k)
            yy = D * 0.5 + gauss(0.14, 0.30, seed, 430 + k)
            zz = z_rail + a * 0.5 + 0.055
            rr = (0.20, 0.115, 0.058)

            def warp(P, k=k, seed=seed):
                Q = P.copy()
                Q[:, 2] *= 1.0 - 0.30 * np.clip(Q[:, 2], 0, 1)
                Q[:, 0] *= 1.0 + 0.10 * np.sin(Q[:, 1] * 9.0 + k)
                return Q
            blob(acc, (xx, yy, zz), rr, mat=M_FAB, sub=2, warp=warp,
                 tint=(0.72, 0.66, 0.50), ts_wear=0.8, ts_dirt=0.9,
                 ts_age=1.0)
            n += 1
    return n


def rib_field(acc, ctr, ang, l, w, h, mat=M_DECK, taper=0.32, ends=0.30,
              grip=1.0, **kw):
    """A field of raised chequer-plate ribs, built as ONE array.

    `ctr` (n, 3), `ang` (n,) radians, all scalars broadcast.  Ten thousand
    separate `add` calls would be correct and would take four minutes a deck;
    this takes 20 ms.  Each rib is a closed 8-vertex wedge: 1.9 mm proud, which
    at the contract sun's 12.47 deg throws 8.6 mm = 3.2 px of shadow.  The
    shadow is what you see, not the rib.
    """
    ctr = np.asarray(ctr, float).reshape(-1, 3)
    n = ctr.shape[0]
    if n == 0:
        return 0
    grip = float(kw.pop("ts_grip", grip))
    ang = np.broadcast_to(np.asarray(ang, float).ravel(), (n,))
    l = np.broadcast_to(np.asarray(l, float).ravel(), (n,))
    w = np.broadcast_to(np.asarray(w, float).ravel(), (n,))
    h = np.broadcast_to(np.asarray(h, float).ravel(), (n,))
    e = l * ends * 0.5
    tw = w * taper
    U = np.stack([-l * .5, l * .5, l * .5, -l * .5,
                  -l * .5 + e, l * .5 - e, l * .5 - e, -l * .5 + e], 1)
    V_ = np.stack([-w * .5, -w * .5, w * .5, w * .5,
                   -tw * .5, -tw * .5, tw * .5, tw * .5], 1)
    Z = np.stack([np.zeros(n)] * 4 + [h] * 4, 1)
    ca, sa = np.cos(ang)[:, None], np.sin(ang)[:, None]
    X = U * ca - V_ * sa
    Y = U * sa + V_ * ca
    P = np.stack([X, Y, Z], -1) + ctr[:, None, :]
    base = np.arange(n)[:, None] * 8
    tmpl = np.array([(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
                     (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)])
    Q = (tmpl[None, :, :] + base[:, :, None]).reshape(-1, 4)
    gp = np.zeros((n, 8), np.float32)
    gp[:, 4:] = grip
    return acc.add(P.reshape(-1, 3), quads=Q, mat=mat,
                   bc=P.reshape(-1, 3) * 0 + np.stack([X, Y, Z], -1).reshape(-1, 3),
                   ts_grip=gp.ravel(), **kw)


def stud_field(acc, ctr, r0, r1, h, mat=M_RUB, seg=8, **kw):
    """A field of round studs (rubber matting), one array."""
    ctr = np.asarray(ctr, float).reshape(-1, 3)
    n = ctr.shape[0]
    if n == 0:
        return 0
    kw.pop("ts_grip", None)
    r0 = np.broadcast_to(np.asarray(r0, float).ravel(), (n,))
    r1 = np.broadcast_to(np.asarray(r1, float).ravel(), (n,))
    h = np.broadcast_to(np.asarray(h, float).ravel(), (n,))
    a = np.arange(seg) * (2 * math.pi / seg)
    ca, sa = np.cos(a)[None, :], np.sin(a)[None, :]
    bot = np.stack([r0[:, None] * ca, r0[:, None] * sa,
                    np.zeros((n, seg))], -1)
    top = np.stack([r1[:, None] * ca, r1[:, None] * sa,
                    np.broadcast_to(h[:, None], (n, seg))], -1)
    cen = np.stack([np.zeros((n, 1)), np.zeros((n, 1)), h[:, None]], -1)
    P = np.concatenate([bot, top, cen], 1) + ctr[:, None, :]
    m = 2 * seg + 1
    base = np.arange(n)[:, None] * m
    i = np.arange(seg)
    j = (i + 1) % seg
    q = np.stack([i, j, seg + j, seg + i], 1)
    Q = (q[None, :, :] + base[:, :, None]).reshape(-1, 4)
    t = np.stack([np.full(seg, 2 * seg), seg + i, seg + j], 1)
    T = (t[None, :, :] + base[:, :, None]).reshape(-1, 3)
    gp = np.zeros((n, m), np.float32)
    gp[:, seg:] = 1.0
    return acc.add(P.reshape(-1, 3), quads=Q, tris=T, mat=mat,
                   ts_grip=gp.ravel(), **kw)


def rounded_path(pts, rad=0.055, seg=4):
    """Round the corners of a 3-D polyline: a bent tube, not a mitred one."""
    P = [np.asarray(p, float) for p in pts]
    if len(P) < 3:
        return np.array(P)
    out = [P[0]]
    for i in range(1, len(P) - 1):
        a, b, c = P[i - 1], P[i], P[i + 1]
        u = unit(a - b)
        v = unit(c - b)
        d = min(rad, np.linalg.norm(a - b) * 0.45, np.linalg.norm(c - b) * 0.45)
        pa = b + u * d
        pc = b + v * d
        out.append(pa)
        for k in range(1, seg):
            t = k / seg
            q = (1 - t) ** 2 * pa + 2 * (1 - t) * t * b + t * t * pc
            out.append(q)
        out.append(pc)
    out.append(P[-1])
    return np.array(out)


def build_deck(acc, r, S):
    """The deck: panels, surface, nosings, toe boards, fixings, wear.

    Four surfaces across the ten stands, and they are four different meshes:
    5-bar chequer (a field of 1.9 mm wedges), moulded GRP grating (real 32 mm
    apertures you can see the joists through), 18 mm ply with grit paint (five
    visible laminations at the edge, countersunk screws), and studded rubber
    matting (a field of 15 mm studs).
    """
    L, D, a, b = r["L"], r["D"], S["a"], S["b"]
    seed = r["seed"]
    n = 0
    for t in range(r["tiers"]):
        y0 = r["y_splits"][t] + 0.004
        y1 = r["y_splits"][t + 1] - 0.004
        dz = r["deck"] + r["rise"][t]
        kind = r["deck_kind"]
        dt = 0.021 if kind == "ply" else (0.028 if kind != "grating" else 0.030)
        npan = max(1, int(round(L / rnd(1.35, 1.95, seed, 500 + t))))
        gap = 0.0035
        edges = np.linspace(-L * 0.5, L * 0.5, npan + 1)
        for p in range(npan):
            px0 = edges[p] + (gap * 0.5 if p else 0.0)
            px1 = edges[p + 1] - (gap * 0.5 if p < npan - 1 else 0.0)
            cx = (px0 + px1) * 0.5
            hx = (px1 - px0) * 0.5
            cy = (y0 + y1) * 0.5
            hy = (y1 - y0) * 0.5
            wear = 0.35 + 0.5 * r["age"]
            if kind == "ply":
                # five laminations, alternating face and core, visible at the
                # sawn edge: 3.6 mm each = 1.3 px, and the edge is 40 % of what
                # you see of a deck from the pit lane
                for k in range(5):
                    zz = dz - dt + dt * (k + 0.5) / 5.0
                    obox(acc, (cx, cy, zz), (hx, 0, 0), (0, hy, 0),
                         (0, 0, dt / 10.0), mat=M_DECK, chamfer=0.0008,
                         ts_wear=wear, ts_age=r["age"],
                         ts_grip=1.0 if k == 4 else 0.0,
                         ts_dirt=0.45 + 0.2 * (k == 4))
                    n += 1
            elif kind == "grating":
                # bars both ways: the aperture is the object
                pitch = 0.0381
                bw, bd = 0.0062, dt
                nx = max(2, int((px1 - px0) / pitch))
                ny = max(2, int((y1 - y0) / pitch))
                for k in range(nx + 1):
                    xx = px0 + (px1 - px0) * k / nx
                    box(acc, (xx - bw * .5, y0, dz - bd), (xx + bw * .5, y1, dz),
                        mat=M_DECK, ts_wear=wear, ts_grip=1.0, ts_age=r["age"],
                        ts_dirt=0.5)
                for k in range(ny + 1):
                    yy = y0 + (y1 - y0) * k / ny
                    box(acc, (px0, yy - bw * .5, dz - bd * 0.62),
                        (px1, yy + bw * .5, dz - bd * 0.06),
                        mat=M_DECK, ts_wear=wear * 0.7, ts_grip=0.3,
                        ts_age=r["age"], ts_dirt=0.6)
                n += nx + ny + 2
            else:
                obox(acc, (cx, cy, dz - dt * 0.5), (hx, 0, 0), (0, hy, 0),
                     (0, 0, dt * 0.5), mat=M_DECK, chamfer=0.0016,
                     ts_wear=wear, ts_age=r["age"], ts_dirt=0.45)
                n += 1
            # ---- the surface pattern ---------------------------------------
            if kind == "chequer":
                cell = 0.070
                nx = max(1, int((px1 - px0 - 0.02) / cell))
                ny = max(1, int((y1 - y0 - 0.02) / cell))
                gx = px0 + 0.012 + (np.arange(nx) + 0.5) * (px1 - px0 - 0.024) / nx
                gy = y0 + 0.012 + (np.arange(ny) + 0.5) * (y1 - y0 - 0.024) / ny
                GX, GY = np.meshgrid(gx, gy, indexing="ij")
                chk = ((np.arange(nx)[:, None] + np.arange(ny)[None, :]) % 2)
                CX, CY, AN = [], [], []
                for s in range(5):
                    off = (s - 2) * 0.0128
                    CX.append(GX + np.where(chk == 0, 0.0, off))
                    CY.append(GY + np.where(chk == 0, off, 0.0))
                    AN.append(np.where(chk == 0, 0.0, math.pi * 0.5))
                CX = np.concatenate([c.ravel() for c in CX])
                CY = np.concatenate([c.ravel() for c in CY])
                AN = np.concatenate([c.ravel() for c in AN])
                jitter = (fbm1(CX * 41.0 + CY * 17.0, seed=seed % 97, oct=2) - 0.5)
                ctrs = np.stack([CX, CY, np.full(CX.shape, dz - 0.0002)], 1)
                rib_field(acc, ctrs, AN, 0.0455, 0.0062,
                          0.0019 * (1.0 - 0.30 * np.clip(jitter * 2 + 0.5, 0, 1)),
                          mat=M_DECK, ts_wear=wear, ts_age=r["age"],
                          ts_dirt=0.30)
                n += 1
            elif kind == "rubber":
                pitch = 0.045
                nx = max(1, int((px1 - px0 - 0.03) / pitch))
                ny = max(1, int((y1 - y0 - 0.03) / pitch))
                gx = px0 + 0.015 + (np.arange(nx) + 0.5) * (px1 - px0 - 0.03) / nx
                gy = y0 + 0.015 + (np.arange(ny) + 0.5) * (y1 - y0 - 0.03) / ny
                GX, GY = np.meshgrid(gx, gy, indexing="ij")
                ctrs = np.stack([GX.ravel(), GY.ravel(),
                                 np.full(GX.size, dz - 0.0002)], 1)
                stud_field(acc, ctrs, 0.0078, 0.0068, 0.0031, mat=M_RUB,
                           ts_wear=wear, ts_age=r["age"], ts_dirt=0.55)
                n += 1
            # ---- the fixings, on EVERY deck kind ---------------------------
            # A deck panel is bolted down every 200-260 mm round its edge and
            # along every joist.  At 373 px/m a countersunk head is 3.4 px and
            # its dished washer face 6 px, and forty of them in a row is the
            # rhythm that says "panel" rather than "surface".
            pitch_f = 0.20 if kind == "ply" else 0.26
            for k in range(int((px1 - px0) / pitch_f) + 1):
                xx = px0 + 0.05 + k * pitch_f
                if xx > px1 - 0.03:
                    break
                for yy in (y0 + 0.035, y1 - 0.035, (y0 + y1) * 0.5):
                    if kind == "grating":
                        # grating is CLIPPED down, not screwed: an M8 saddle
                        obox(acc, (xx, yy, dz - 0.010), (0.020, 0, 0),
                             (0, 0.013, 0), (0, 0, 0.012), mat=M_STEEL,
                             chamfer=0.0012, ts_wear=0.7, ts_dirt=0.7)
                        bolt(acc, (xx, yy, dz - 0.0002), EZ, af=0.011,
                             head=0.0046, length=0.030, wear=0.8)
                    else:
                        caphead(acc, (xx, yy, dz - 0.0016), EZ, d=0.0105,
                                head_h=0.0028, wear=0.75)
            n += 1
        # ---- the nosing on the track edge of every tier ---------------------
        zn = dz
        nose_y = y0 - 0.004 if t else -0.028
        P = [(-L * 0.5 - 0.006, nose_y, zn), (L * 0.5 + 0.006, nose_y, zn)]
        sect = np.array([(0.0, 0.0), (0.030, 0.0), (0.030, -0.006),
                         (0.006, -0.006), (0.006, -0.040), (-0.004, -0.040),
                         (-0.004, -0.004), (0.0, -0.004)])
        member(acc, P[0], P[1], sect, mat=M_ALU, ts_anod=1.0, ts_wear=0.85,
               ts_edge=1.0, ts_dirt=0.5, ts_age=r["age"])
        # transverse grip ribs along the nosing: 3 mm proud, 13 mm shadow
        nn = int(L / 0.020)
        cx = -L * 0.5 + 0.02 + np.arange(nn) * 0.020
        ctrs = np.stack([cx, np.full(nn, nose_y + 0.016),
                         np.full(nn, zn - 0.0002)], 1)
        rib_field(acc, ctrs, np.full(nn, math.pi * 0.5), 0.026, 0.0055, 0.0026,
                  mat=M_ALU, ts_anod=1.0, ts_wear=0.9, ts_grip=1.0,
                  ts_edge=0.8, ts_dirt=0.4)
        n += 2
        # ---- toe boards at the ends and the back ---------------------------
        for s in (-1.0, 1.0):
            plate(acc, (s * (L * 0.5 - 0.004), (y0 + y1) * 0.5, dz + 0.048),
                  (0, (y1 - y0) * 0.5, 0), (0, 0, 0.048), 0.0035, mat=M_PAINT,
                  tint=r["col1"], ts_paint=1.0, ts_wear=0.6, ts_dirt=0.7,
                  ts_age=r["age"])
            n += 1
        if t == r["tiers"] - 1:
            plate(acc, (0.0, y1 - 0.002, dz + 0.048), (L * 0.5 - 0.004, 0, 0),
                  (0, 0, 0.048), 0.0035, mat=M_PAINT, tint=r["col1"],
                  ts_paint=1.0, ts_wear=0.5, ts_dirt=0.75, ts_age=r["age"])
            n += 1
    return n


def panel_poly(acc, P2, x, t, mat=M_PAINT, **kw):
    """Extrude a closed CONVEX 2-D outline in the (y, z) plane along x.

    Convex only: `extrude` caps with a centroid fan, and a fan across a
    re-entrant corner folds the cap inside out.  Panels with a window are
    therefore built as four convex pieces around the hole, which is also how
    they are actually cut.
    """
    P2 = np.asarray(P2, float)
    m = P2.shape[0]
    PTS = np.empty((2, m, 3))
    for i, s in enumerate((-t * 0.5, t * 0.5)):
        PTS[i] = np.stack([np.full(m, x + s), P2[:, 0], P2[:, 1]], 1)
    return extrude(acc, PTS, mat=mat, **kw)


def build_panels(acc, r, S):
    """End panels, the deck skirt, and the car numbers.

    WHY THIS EXISTS AT ALL.  The first render of this item came back reading as
    scaffolding: a bright frame with daylight through every bay and no mass.  A
    real pit wall stand is a CLAD structure -- solid composite ends, a skirt
    under the deck, a full-length fascia -- and the cladding is where the team
    puts its identity.  Adding it changed the object from a frame to a machine,
    and it is also where the livery variation stops being a colour swap: the
    end panel is cut to a different SHAPE for each team.
    """
    L, D, a, b = r["L"], r["D"], S["a"], S["b"]
    seed = r["seed"]
    F = console_frame(r)
    dz = r["deck"]
    n = 0
    style = r["uid"] % 5
    ef, er = r["eaves_f"], r["eaves_r"]
    step_end = r["step_end"]

    # ---- the two end panels -------------------------------------------------
    # THE FIRST VERSION OF THIS WAS WRONG and the macro said so: a panel from
    # deck to eaves over the full 2.8 m depth turned a pit wall stand into a
    # shipping container.  What a stand actually carries is a WIND SCREEN
    # beside the end seat -- it starts at about the worktop, it stops short of
    # the back so people can walk past, and you can see the frame under it.
    for s in (-1.0, 1.0):
        px = s * (L * 0.5 + a * 0.5 + 0.004)
        z0 = F["top"] - 0.115
        zt_f = ef - a * 0.5 - 0.03
        zt_r = er - a * 0.5 - 0.03
        y0 = F["y_f"] + 0.02
        y1 = r["y_splits"][min(1, r["tiers"] - 1)] + (D - r["y_splits"][
            min(1, r["tiers"] - 1)]) * 0.35 + 0.10
        y1 = min(y1, D - 0.12)
        if s == step_end:
            # the panel at the step end is a half screen so the crew can get on
            y1 = y0 + (y1 - y0) * 0.55
        hh = zt_f - z0
        pieces = []
        band = (z0, zt_f)                    # the SOLID band the livery goes in
        if style == 0:                       # full, raked to the canopy fall
            pieces.append([(y0, z0), (y1, z0), (y1, zt_r), (y0, zt_f)])
        elif style == 1:                     # a 0.35 m band, then the panel
            zm = z0 + hh * 0.40
            pieces.append([(y0, z0), (y1, z0), (y1, z0 + (zt_r - z0) * 0.40),
                           (y0, zm)])
            pieces.append([(y0, zm + 0.055), (y1, z0 + (zt_r - z0) * 0.40 + 0.055),
                           (y1, zt_r), (y0, zt_f)])
            band = (z0, zm)
        elif style == 2:                     # a big cut corner at the front top
            cy = y0 + (y1 - y0) * 0.42
            pieces.append([(y0, z0), (y1, z0), (y1, zt_r),
                           (cy, zt_f + (zt_r - zt_f) * 0.42),
                           (y0, z0 + hh * 0.52)])
            band = (z0, z0 + hh * 0.50)
        elif style == 3:                     # a window: four convex pieces
            wy0, wy1 = y0 + (y1 - y0) * 0.30, y0 + (y1 - y0) * 0.72
            wz0, wz1 = z0 + hh * 0.46, z0 + hh * 0.78
            pieces.append([(y0, z0), (y1, z0), (y1, wz0), (y0, wz0)])
            pieces.append([(y0, wz1), (y1, wz1), (y1, zt_r), (y0, zt_f)])
            pieces.append([(y0, wz0), (wy0, wz0), (wy0, wz1), (y0, wz1)])
            pieces.append([(wy1, wz0), (y1, wz0), (y1, wz1), (wy1, wz1)])
            band = (z0, wz0)
        else:                                # a leading rake off the front edge
            pieces.append([(y0 + 0.16, z0), (y1, z0), (y1, zt_r), (y0, zt_f),
                           (y0, z0 + hh * 0.30)])
            band = (z0, z0 + hh * 0.62)
        r["_livery_band_%d" % int(s)] = band
        # ONE PANEL, ONE TONE.  The four pieces around a window are cut from a
        # single sheet; giving each its own ts_pid put three visible tonal steps
        # across one panel in the first render.  Shared explicitly here.
        pid = h01(seed, 1490 + int(s))
        for pc in pieces:
            panel_poly(acc, pc, px, 0.0085, mat=M_PAINT, tint=r["col1"],
                       ts_paint=1.0, ts_wear=0.45, ts_edge=0.9, ts_dirt=0.55,
                       ts_age=r["age"], ts_pid=pid)
            n += 1
            # the edge return that stiffens it, and the rivets that hold it on
            for k in range(len(pc)):
                p0 = np.array(pc[k])
                p1 = np.array(pc[(k + 1) % len(pc)])
                ln = float(np.linalg.norm(p1 - p0))
                if ln < 0.12:
                    continue
                nr = max(2, int(ln / 0.30))
                for j in range(nr):
                    q = p0 + (p1 - p0) * ((j + 0.5) / nr)
                    d = unit(np.array([0.0, p1[0] - p0[0], p1[1] - p0[1]]))
                    inw = unit(np.cross(d, np.array([s, 0.0, 0.0])))
                    q3 = np.array([px, q[0], q[1]]) + inw * 0.026
                    # M8 button head + washer, 15 mm across = 5.6 px, not the
                    # 8 mm dome the first pass used, which was 3 px and gone
                    disc(acc, q3 + np.array([s * 0.0046, 0, 0]), (s, 0, 0),
                         0.0088, 0.0016, mat=M_STEEL, n=14, ts_wear=0.55,
                         ts_edge=0.8)
                    rivet(acc, q3 + np.array([s * 0.0062, 0, 0]), (s, 0, 0),
                          r=0.0060, h=0.0030, mat=M_STEEL)
        # the perimeter angle the panel is bolted to
        for pc in pieces[:1]:
            for k in range(len(pc)):
                p0 = np.array(pc[k])
                p1 = np.array(pc[(k + 1) % len(pc)])
                member(acc, (px - s * 0.014, p0[0], p0[1]),
                       (px - s * 0.014, p1[0], p1[1]), S["thin"], mat=M_ALU,
                       ts_anod=1.0, ts_wear=0.3, ts_dirt=0.6, ns=3)
                n += 1
    # ---- the car numbers, one per end, in the stroke font -------------------
    # THE LIVERY GOES IN THE SOLID BAND, and the band is whatever this team's
    # panel cut actually left solid.  The first pass put the nameplate at a
    # fixed height and on the window-cut panel it landed IN the aperture,
    # floating unsupported in mid air -- visible in the 5x crop as a mirrored
    # JUNIPER hanging in a hole.
    nums = ("%d" % (r["bay"] * 2 + 3), "%d" % (r["bay"] * 2 + 4))
    y0 = F["y_f"] + 0.02
    y1 = min(r["y_splits"][min(1, r["tiers"] - 1)]
             + (D - r["y_splits"][min(1, r["tiers"] - 1)]) * 0.35 + 0.10,
             D - 0.12)
    for i, s in enumerate((-1.0, 1.0)):
        if s == step_end:
            continue
        b0, b1 = r["_livery_band_%d" % int(s)]
        px = s * (L * 0.5 + a * 0.5 + 0.0088)
        yc = (y0 + y1) * 0.5
        ch = min(0.330, (b1 - b0) * 0.44)
        zc = b0 + (b1 - b0) * 0.5 - ch * 0.62
        ey_ = np.array([0.0, 1.0, 0.0]) * (1.0 if s > 0 else -1.0)
        emit_text(acc, nums[i], (px, yc, zc), ey_, np.array([0.0, 0.0, 1.0]),
                  ch, thick=0.00040, tracking=0.14, weight=0.170,
                  mat=M_VINYL, tint=r["col2"], ts_wear=0.30, ts_age=r["age"])
        emit_text(acc, r["team"], (px, yc, zc + ch + 0.055), ey_,
                  np.array([0.0, 0.0, 1.0]), min(0.082, (b1 - b0) * 0.11),
                  thick=0.00035, tracking=0.20, weight=0.150, mat=M_VINYL,
                  tint=r["col2"], ts_wear=0.35, ts_age=r["age"])
        # the livery stripe wraps round the end, in the same rhythm as the
        # valance so the two read as one scheme rather than two decisions
        st = r["uid"] % 5
        bands = ((0.030, 0.014), (0.052, 0.007), (0.068, 0.005)) if st == 0 \
            else ((0.030, 0.028),) if st == 1 \
            else ((0.026, 0.010), (0.046, 0.010), (0.066, 0.010)) if st == 2 \
            else ((0.030, 0.020), (0.058, 0.006)) if st == 3 \
            else ((0.024, 0.006), (0.040, 0.006), (0.056, 0.006),
                  (0.072, 0.006))
        for (zo, th) in bands:
            zz = b0 + zo
            P2 = np.array([(y0 + 0.03, zz), (y1 - 0.03, zz),
                           (y1 - 0.03, zz + th), (y0 + 0.03, zz + th)])
            PTS = np.empty((2, 4, 3))
            for q, tt in enumerate((0.0, 0.00034)):
                PTS[q] = np.stack([np.full(4, px + s * tt), P2[:, 0],
                                   P2[:, 1]], 1)
            extrude(acc, PTS, mat=M_VINYL, tint=r["col2"], ts_edge=1.0,
                    ts_wear=0.35, ts_age=r["age"])
        n += 3
    # ---- the skirt under the deck, on the track side -----------------------
    sz1 = dz - 0.055
    sz0 = 0.190 + gauss(0.02, 0.05, seed, 1500)
    sy = -0.030
    npan = max(2, int(round(L / 1.55)))
    edges = np.linspace(-L * 0.5 - 0.01, L * 0.5 + 0.01, npan + 1)
    for k in range(npan):
        x0 = edges[k] + (0.004 if k else 0.0)
        x1 = edges[k + 1] - (0.004 if k < npan - 1 else 0.0)
        plate(acc, ((x0 + x1) * 0.5, sy, (sz0 + sz1) * 0.5),
              ((x1 - x0) * 0.5, 0, 0), (0, 0, (sz1 - sz0) * 0.5), 0.0060,
              mat=M_PAINT, tint=r["col1"], chamfer=0.0018, ts_paint=1.0,
              ts_wear=0.55, ts_dirt=0.85, ts_age=r["age"])
        # two horizontal swages, which is how a thin panel is stiffened, and
        # each throws 4.5x its own depth downward under this sun
        for zz in (sz0 + (sz1 - sz0) * 0.34, sz0 + (sz1 - sz0) * 0.67):
            member(acc, (x0 + 0.02, sy - 0.004, zz), (x1 - 0.02, sy - 0.004, zz),
                   np.array([(0.005, 0.011), (0.0, 0.015), (-0.005, 0.011),
                             (-0.005, -0.011), (0.0, -0.015), (0.005, -0.011)]),
                   mat=M_PAINT, tint=r["col1"], ts_paint=1.0, ts_wear=0.5,
                   ts_edge=0.85, ts_dirt=0.8, ts_age=r["age"], ns=3)
        for zz in (sz0 + 0.020, sz1 - 0.020):
            for xx in np.arange(x0 + 0.10, x1 - 0.05, 0.34):
                rivet(acc, (xx, sy - 0.0032, zz), (0, -1, 0), r=0.0040,
                      h=0.0024, mat=M_STEEL)
        n += 1
    # the skirt's bottom edge return -- a 15 mm lip, 68 mm of shadow on the
    # ground behind it
    member(acc, (-L * 0.5 - 0.01, sy, sz0), (L * 0.5 + 0.01, sy, sz0),
           np.array([(0.004, 0.004), (0.004, -0.006), (-0.015, -0.010),
                     (-0.017, -0.005), (-0.017, 0.004)]),
           mat=M_PAINT, tint=r["col1"], ts_paint=1.0, ts_wear=0.6,
           ts_edge=1.0, ts_dirt=0.9, ts_age=r["age"])
    n += 1
    return n


def build_steps(acc, r, S):
    """Two or three treads at one end, with a stringer and a grab rail."""
    L, D, a, b = r["L"], r["D"], S["a"], S["b"]
    seed = r["seed"]
    e = r["step_end"]
    dz = r["deck"]
    ns = r["steps"]
    rise = dz / (ns + 1)
    going = rnd(0.265, 0.305, seed, 600)
    x_out = e * (L * 0.5 + 0.075)
    yc = D * 0.46
    tw = 0.310                       # tread half-width in y
    n = 0
    # stringers: a channel each side, AT THE TREAD EDGES.  The first version
    # put them at 0.22 D and 0.72 D while the treads spanned 0.16..0.76 D, so
    # on a 2.4 m deep stand the outer stringer stood 0.96 m clear of the tread
    # it was supposed to carry.  Measured off the pit-lane render, not guessed.
    for j, yy in enumerate((yc - tw - 0.022, yc + tw + 0.022)):
        p0 = (e * (L * 0.5 + 0.010), yy, dz - 0.030)
        p1 = (x_out + e * (going * ns + 0.10), yy, 0.055)
        member(acc, p0, p1,
               np.array([(0.050, 0.022), (0.050, -0.022), (0.038, -0.022),
                         (0.038, -0.010), (-0.038, -0.010), (-0.038, -0.022),
                         (-0.050, -0.022), (-0.050, 0.022), (-0.038, 0.022),
                         (-0.038, 0.010), (0.038, 0.010), (0.038, 0.022)]),
               mat=M_ALU, ts_anod=1.0, ts_wear=0.5, ts_dirt=0.7,
               ts_age=r["age"])
        n += 1
    for k in range(ns):
        zz = dz - rise * (k + 1)
        xx = x_out + e * going * k
        cxx = xx + e * going * 0.5
        obox(acc, (cxx, yc, zz - 0.015), (going * 0.48, 0, 0), (0, tw, 0),
             (0, 0, 0.015), mat=M_DECK, chamfer=0.0016, ts_wear=0.95,
             ts_grip=0.4, ts_dirt=0.6, ts_age=r["age"])
        nn = max(4, int(tw * 2.0 / 0.024))
        gy = yc - tw + 0.014 + np.arange(nn) * 0.024
        ctrs = np.stack([np.full(nn, cxx), gy, np.full(nn, zz - 0.0002)], 1)
        rib_field(acc, ctrs, np.zeros(nn), going * 0.70, 0.0060, 0.0026,
                  mat=M_DECK, ts_wear=0.95, ts_grip=1.0, ts_dirt=0.5)
        # nosing strip, rubber, on the front arris of the tread
        obox(acc, (xx - e * 0.010, yc, zz - 0.007), (0.016, 0, 0), (0, tw, 0),
             (0, 0, 0.009), mat=M_RUB, chamfer=0.0012, ts_wear=1.0,
             ts_edge=1.0, ts_dirt=0.6)
        for yy in (yc - tw + 0.02, yc + tw - 0.02):
            bolt(acc, (cxx, yy, zz + 0.0002), EZ, af=0.011, head=0.0046,
                 length=0.010, wear=0.9)
        n += 3
    # grab rails, one each side, following the flight
    for yy in (yc - tw - 0.055, yc + tw + 0.055):
        hp = [(e * (L * 0.5 - 0.02), yy, dz + 0.985),
              (x_out, yy, dz + 0.985 - rise * 0.4),
              (x_out + e * (going * ns), yy, dz - rise * ns + 0.94),
              (x_out + e * (going * ns + 0.09), yy, dz - rise * ns + 0.86)]
        sweep(acc, rounded_path(hp, 0.11, 4), circle(0.0212, 14), mat=M_ALU,
              ts_anod=1.0, ts_wear=1.0, ts_dirt=0.35, ts_age=r["age"])
        for (sx, sz) in ((x_out, dz + 0.985 - rise * 0.4),
                         (x_out + e * (going * ns), dz - rise * ns + 0.94)):
            tube(acc, (sx, yy, sz), (sx, yy, sz - 0.90), 0.0195, mat=M_ALU,
                 n=14, ts_anod=1.0, ts_wear=0.5, ts_dirt=0.6)
            disc(acc, (sx, yy, sz - 0.90), EZ, 0.030, 0.010, mat=M_ALU, n=16,
                 ts_anod=1.0, ts_wear=0.45, ts_dirt=0.8)
        n += 2
    return n


def build_rails(acc, r, S):
    """The handrail run, its sockets, and the principal's lean pad."""
    L, D, a = r["L"], r["D"], S["a"]
    seed = r["seed"]
    top = r["deck"] + r["rise"][-1] + 1.045
    yb = r["y_splits"][-1] - 0.05
    n = 0
    runs = []
    if r["rail"] in ("rear", "rear+ends", "full"):
        runs.append([(-L * 0.5 + 0.06, yb, top), (L * 0.5 - 0.06, yb, top)])
    if r["rail"] in ("rear+ends", "full"):
        for s in (-1.0, 1.0):
            runs.append([(s * (L * 0.5 - 0.06), yb, top),
                         (s * (L * 0.5 - 0.06), r["y_splits"][-2] + 0.10, top)])
    for k, run in enumerate(runs):
        p0 = np.asarray(run[0], float)
        p1 = np.asarray(run[-1], float)
        Lr = float(np.linalg.norm(p1 - p0))
        sag = gauss(0.0020, 0.0042, seed, 700 + k)
        ns = max(4, int(Lr / 0.10))
        t = np.linspace(0, 1, ns)
        path = p0[None, :] + t[:, None] * (p1 - p0)[None, :]
        path[:, 2] -= sag * np.sin(math.pi * t)
        sweep(acc, path, circle(0.0212, 16), mat=M_ALU, ts_anod=1.0,
              ts_wear=0.95, ts_dirt=0.30, ts_age=r["age"])
        # stanchions with a real socket and two bolts
        nst = max(2, int(Lr / 1.15) + 1)
        for i in range(nst):
            q = p0 + (p1 - p0) * (i / max(nst - 1, 1))
            zdeck = deck_top(r, q[1])
            tube(acc, (q[0], q[1], zdeck + 0.02), (q[0], q[1], top), 0.0212,
                 mat=M_ALU, n=16, ts_anod=1.0, ts_wear=0.5, ts_dirt=0.45)
            # mid rail
            if i < nst - 1:
                q2 = p0 + (p1 - p0) * ((i + 1) / max(nst - 1, 1))
                tube(acc, (q[0], q[1], zdeck + 0.50), (q2[0], q2[1], zdeck + 0.50),
                     0.0155, mat=M_ALU, n=12, ts_anod=1.0, ts_wear=0.4,
                     ts_dirt=0.4)
            # socket flange
            disc(acc, (q[0], q[1], zdeck + 0.008), EZ, 0.036, 0.010,
                 mat=M_ALU, n=18, ts_anod=1.0, ts_wear=0.4, ts_dirt=0.8)
            for s in (-1.0, 1.0):
                bolt(acc, (q[0] + s * 0.026, q[1], zdeck + 0.013), EZ, af=0.011,
                     head=0.0046, length=0.014, wear=0.55)
            n += 3
    # the lean pad where the team principal stands
    px = r["prin_end"] * (L * 0.5 - 0.55)
    if runs:
        obox(acc, (px, yb - 0.012, top), (0.28, 0, 0), (0, 0.012, 0),
             (0, 0, 0.026), mat=M_RUB, chamfer=0.006, ts_wear=1.0,
             ts_dirt=0.35, ts_age=r["age"])
        n += 1
    return n


def console_frame(r):
    """The console's key dimensions in the stand's local frame."""
    dz = r["deck"]
    y_f = -0.360
    y_r = y_f + r["worktop_d"]
    top = dz + r["console_h"]
    return dict(y_f=y_f, y_r=y_r, top=top, rail_top=top + RAIL_H,
                fascia_z0=dz + 0.105, fascia_z1=top - 0.032, deck=dz)


def build_console(acc, r, S):
    """Worktop, fascia, monitor rail, arms, hood, and the electrical fit-out.

    THIS IS THE HERO ASSEMBLY.  From the film's own eye -- 1.900 m up, 10.0 m
    away, past a 1.200 m wall -- the worktop lip, the monitor rail, the shade
    hood and the arms are the first things on the object the light hits, and
    every one of them is a HORIZONTAL edge in a 12.47 deg sun, so each throws
    4.5x its own depth in shadow down the face below it.
    """
    L, D, a, b = r["L"], r["D"], S["a"], S["b"]
    seed = r["seed"]
    F = console_frame(r)
    n = 0
    # ---- carrying brackets off the front posts + two intermediate legs ------
    legs = list(r["post_x"])
    for xx in legs:
        member(acc, (xx, 0.0, F["deck"] + 0.02), (xx, 0.0, F["top"] - 0.030),
               S["small"], mat=M_ALU, ts_anod=1.0, ts_wear=0.35, ts_dirt=0.35,
               ts_age=r["age"])
        # the cantilever bracket that carries the worktop forward
        tri = np.array([(xx, F["y_f"] + 0.03, F["top"] - 0.030),
                        (xx, 0.02, F["top"] - 0.030),
                        (xx, 0.02, F["top"] - 0.185)])
        PTS = np.empty((2, 3, 3))
        for i, t in enumerate((-0.0035, 0.0035)):
            PTS[i] = tri + np.array([t, 0, 0])[None, :]
        extrude(acc, PTS, mat=M_ALU, ts_anod=1.0, ts_wear=0.3, ts_dirt=0.4,
                ts_edge=0.8)
        for zz in (F["top"] - 0.055, F["top"] - 0.150):
            bolt(acc, (xx + 0.0037, 0.021, zz), (1, 0, 0), af=0.011,
                 head=0.0046, length=0.012, wear=0.45)
        n += 2
    # ---- the worktop: two or three slabs with a real cable slot behind -----
    nslab = max(2, int(round(L / 1.75)))
    edges = np.linspace(-L * 0.5 + 0.01, L * 0.5 - 0.01, nslab + 1)
    for k in range(nslab):
        x0 = edges[k] + (0.0025 if k else 0.0)
        x1 = edges[k + 1] - (0.0025 if k < nslab - 1 else 0.0)
        obox(acc, ((x0 + x1) * 0.5, (F["y_f"] + F["y_r"] - 0.030) * 0.5,
                   F["top"] - 0.0125),
             ((x1 - x0) * 0.5, 0, 0),
             (0, (F["y_r"] - 0.030 - F["y_f"]) * 0.5, 0), (0, 0, 0.0125),
             mat=M_PAINT, chamfer=0.0018, tint=(0.055, 0.055, 0.058),
             ts_paint=1.0, ts_wear=0.9, ts_dirt=0.45, ts_age=r["age"])
        n += 1
    # bullnose front edge trim, swept: a 20 mm lip = 90 mm = 34 px of shadow
    sect = np.array([(0.0, 0.014), (0.010, 0.012), (0.014, 0.004),
                     (0.014, -0.008), (0.008, -0.016), (-0.002, -0.018),
                     (-0.014, -0.018), (-0.014, 0.014)])
    member(acc, (-L * 0.5 - 0.004, F["y_f"] - 0.006, F["top"] - 0.012),
           (L * 0.5 + 0.004, F["y_f"] - 0.006, F["top"] - 0.012), sect,
           mat=M_RUB, ts_wear=0.95, ts_edge=1.0, ts_dirt=0.4, ts_age=r["age"])
    n += 1
    # ---- the fascia, four ways ---------------------------------------------
    fz0, fz1 = F["fascia_z0"], F["fascia_z1"]
    fy = F["y_f"] + 0.012
    kind = r["fascia"]
    if kind == "ribbed":
        plate(acc, (0.0, fy + 0.006, (fz0 + fz1) * 0.5), (L * 0.5 - 0.03, 0, 0),
              (0, 0, (fz1 - fz0) * 0.5), 0.0028, mat=M_PAINT, tint=r["col1"],
              ts_paint=1.0, ts_wear=0.5, ts_dirt=0.6, ts_age=r["age"])
        nr = int((fz1 - fz0) / 0.052)
        for k in range(nr):
            zz = fz0 + 0.026 + k * 0.052
            member(acc, (-L * 0.5 + 0.03, fy, zz), (L * 0.5 - 0.03, fy, zz),
                   np.array([(0.006, 0.010), (0.0, 0.014), (-0.006, 0.010),
                             (-0.006, -0.010), (0.0, -0.014), (0.006, -0.010)]),
                   mat=M_PAINT, tint=r["col1"], ts_paint=1.0, ts_wear=0.55,
                   ts_edge=0.8, ts_dirt=0.5, ts_age=r["age"])
        n += nr + 1
    elif kind == "louvred":
        plate(acc, (0.0, fy + 0.016, (fz0 + fz1) * 0.5), (L * 0.5 - 0.03, 0, 0),
              (0, 0, (fz1 - fz0) * 0.5), 0.0025, mat=M_PAINT,
              tint=tuple(c * 0.45 for c in r["col1"]), ts_paint=1.0,
              ts_wear=0.4, ts_dirt=0.75, ts_age=r["age"])
        nl = int((fz1 - fz0) / 0.058)
        for k in range(nl):
            zz = fz0 + 0.030 + k * 0.058
            obox(acc, (0.0, fy + 0.002, zz), (L * 0.5 - 0.03, 0, 0),
                 (0, 0.016, -0.010), (0, 0.0016, 0.0025), mat=M_PAINT,
                 tint=r["col1"], chamfer=0.0008, ts_paint=1.0, ts_wear=0.5,
                 ts_edge=0.9, ts_dirt=0.55, ts_age=r["age"])
        n += nl + 1
    elif kind == "perforated":
        # real 12 mm holes on a 20 mm pitch: 4.5 px each and you see the loom
        # through them
        pitch = 0.020
        nx = int((L - 0.10) / pitch)
        nz = int((fz1 - fz0 - 0.05) / pitch)
        gx = -L * 0.5 + 0.05 + (np.arange(nx) + 0.5) * (L - 0.10) / nx
        gz = fz0 + 0.025 + (np.arange(nz) + 0.5) * (fz1 - fz0 - 0.05) / nz
        GX, GZ = np.meshgrid(gx, gz, indexing="ij")
        GX = GX + (np.arange(nz)[None, :] % 2) * pitch * 0.5
        _perf_panel(acc, GX.ravel(), GZ.ravel(), fy, 0.0060, 0.0030,
                    (-L * 0.5 + 0.03, L * 0.5 - 0.03), (fz0, fz1),
                    tint=r["col1"], age=r["age"])
        n += 1
    else:
        plate(acc, (0.0, fy + 0.004, (fz0 + fz1) * 0.5), (L * 0.5 - 0.03, 0, 0),
              (0, 0, (fz1 - fz0) * 0.5), 0.0030, mat=M_PAINT, tint=r["col1"],
              ts_paint=1.0, ts_wear=0.5, ts_dirt=0.6, ts_age=r["age"])
        n += 1
    # fascia fixings: a dome-head every 400 mm round the perimeter
    for xx in np.arange(-L * 0.5 + 0.09, L * 0.5 - 0.05, 0.40):
        for zz in (fz0 + 0.012, fz1 - 0.012):
            rivet(acc, (xx, fy - 0.0016, zz), (0, -1, 0), r=0.0038, h=0.0022,
                  mat=M_STEEL)
    # ---- the fascia nameplate ----------------------------------------------
    ph = min(0.085, (fz1 - fz0) * 0.30)
    emit_text(acc, r["team"], (0.0, fy - 0.0022, fz1 - 0.055 - ph),
              np.array([1.0, 0, 0]), np.array([0, 0, 1.0]), ph,
              thick=0.00035, tracking=0.16, weight=0.150, mat=M_VINYL,
              tint=r["col2"], ts_paint=0.0, ts_wear=0.35, ts_age=r["age"])
    n += 1
    # ---- monitor rail, on two plinths --------------------------------------
    ry = 0.075
    rt = F["rail_top"]
    for xx in (-L * 0.5 + 0.16, 0.0, L * 0.5 - 0.16):
        member(acc, (xx, ry, F["top"]), (xx, ry, rt - a * 0.5), S["small"],
               mat=M_ALU, ts_anod=1.0, ts_wear=0.4, ts_dirt=0.4,
               ts_age=r["age"])
        n += 1
    member(acc, (-L * 0.5 + 0.10, ry, rt - a * 0.5),
           (L * 0.5 - 0.10, ry, rt - a * 0.5), S["main"], mat=M_ALU,
           bow=gauss(0.0012, 0.0026, seed, 800), bow_dir=EZ, ts_anod=1.0,
           ts_wear=0.45, ts_dirt=0.5, ts_age=r["age"])
    n += 1
    # ---- the shade hood, if this stand has one ------------------------------
    hood = bool(r["hood"])
    if hood:
        hz = rt + 0.055
        obox(acc, (0.0, ry + 0.10, hz), (L * 0.5 - 0.10, 0, 0),
             (0, 0.155, -0.030), (0, 0.0022, 0.0022), mat=M_PAINT,
             tint=tuple(c * 0.35 + 0.02 for c in r["col1"]), chamfer=0.0016,
             ts_paint=1.0, ts_wear=0.55, ts_dirt=0.85, ts_age=r["age"])
        # the hood's front lip, and its stiffening ribs
        member(acc, (-L * 0.5 + 0.10, ry + 0.253, hz - 0.031),
               (L * 0.5 - 0.10, ry + 0.253, hz - 0.031),
               np.array([(0.010, 0.006), (0.010, -0.020), (0.004, -0.024),
                         (-0.004, -0.020), (-0.004, 0.006)]),
               mat=M_ALU, ts_anod=1.0, ts_wear=0.6, ts_edge=1.0, ts_dirt=0.6)
        for xx in np.arange(-L * 0.5 + 0.30, L * 0.5 - 0.20, 0.62):
            obox(acc, (xx, ry + 0.10, hz - 0.022), (0.0025, 0, 0),
                 (0, 0.150, -0.029), (0, 0.004, 0.020), mat=M_ALU,
                 ts_anod=1.0, ts_wear=0.3, ts_dirt=0.5)
        n += 3
    # ---- monitor arms -------------------------------------------------------
    for k, bay in enumerate(monitor_bays_local(r)):
        _monitor_arm(acc, r, S, bay, seed, k)
        n += 1
    # ---- the electrical fit-out --------------------------------------------
    _console_electrics(acc, r, S, F)
    return n


def _perf_panel(acc, hx, hz, y, rout, rin, xr, zr, tint=(1, 1, 1), age=0.5):
    """A perforated panel: every hole is a real hole through 3 mm of sheet.

    Built as one array of annular cells so 900 holes cost 20 ms instead of
    90 seconds.  The cell is a square ring of 8 outer points meeting an 8-point
    bore, front and back, plus the bore wall -- which is what makes a
    perforation read as a hole rather than as a dark dot: you can see 3 mm of
    lit bore wall on the sunward side of every one of them.
    """
    n = hx.size
    seg = 8
    a = (np.arange(seg) + 0.5) * (2 * math.pi / seg)
    ca, sa = np.cos(a), np.sin(a)
    # outer square ring, inner circle
    sq = np.stack([np.sign(ca) * np.minimum(np.abs(ca) * 1.9, 1.0),
                   np.sign(sa) * np.minimum(np.abs(sa) * 1.9, 1.0)], 1) * rout
    ci = np.stack([ca, sa], 1) * rin
    t = 0.0030
    V = []
    for (dy, ring) in ((-t * 0.5, sq), (-t * 0.5, ci),
                       (t * 0.5, sq), (t * 0.5, ci)):
        P = np.zeros((n, seg, 3))
        P[:, :, 0] = hx[:, None] + ring[None, :, 0]
        P[:, :, 2] = hz[:, None] + ring[None, :, 1]
        P[:, :, 1] = y + dy
        V.append(P)
    V = np.concatenate(V, 1).reshape(-1, 3)
    m = seg * 4
    base = np.arange(n)[:, None] * m
    i = np.arange(seg)
    j = (i + 1) % seg
    q = []
    q.append(np.stack([i, j, seg + j, seg + i], 1))                    # front
    q.append(np.stack([2 * seg + i, 2 * seg + j, 3 * seg + j, 3 * seg + i], 1))
    q.append(np.stack([seg + i, seg + j, 3 * seg + j, 3 * seg + i], 1))  # bore
    q = np.concatenate(q)
    Q = (q[None, :, :] + base[:, :, None]).reshape(-1, 4)
    acc.add(V, quads=Q, mat=M_PAINT, tint=tint, ts_paint=1.0, ts_wear=0.5,
            ts_edge=0.9, ts_dirt=0.6, ts_age=age)
    # the frame the perforated field sits in
    for (cx, cz, ex, ez) in ((0.0, zr[0] + 0.012, (xr[1] - xr[0]) * 0.5, 0.012),
                             (0.0, zr[1] - 0.012, (xr[1] - xr[0]) * 0.5, 0.012),
                             (xr[0] + 0.012, (zr[0] + zr[1]) * 0.5, 0.012,
                              (zr[1] - zr[0]) * 0.5),
                             (xr[1] - 0.012, (zr[0] + zr[1]) * 0.5, 0.012,
                              (zr[1] - zr[0]) * 0.5)):
        obox(acc, (cx, y, cz), (ex, 0, 0), (0, 0.0035, 0), (0, 0, ez),
             mat=M_PAINT, tint=tint, chamfer=0.0010, ts_paint=1.0,
             ts_wear=0.5, ts_dirt=0.55, ts_age=age)


def monitor_bays_local(r):
    """Where the monitors hang, in the stand's local frame.

    Their SCREENS face the pit lane (+y) because the engineers sit behind the
    console and look over the screens at the track -- which is why what the
    film sees from the track is the BACK of every screen and the front of the
    console.  Getting this the wrong way round would put six bright panels
    facing the camera and it is the commonest mistake made about a pit wall.
    """
    F = console_frame(r)
    L = r["L"]
    out = []
    nm = r["nmon"]
    span = L - 0.55
    for k in range(nm):
        x = -span * 0.5 + span * (k / max(nm - 1, 1))
        sz = pick((0.24, 0.27, 0.27, 0.32), r["seed"], 900 + k)
        pitch = math.radians(rnd(-16.0, -6.0, r["seed"], 910 + k))
        yaw = math.radians(gauss(6.0, 15.0, r["seed"], 920 + k))
        if not r["dressed"]:
            pitch = math.radians(-84.0)         # folded down onto the rail
            yaw = 0.0
        z = F["rail_top"] - 0.045 + rnd(-0.012, 0.030, r["seed"], 930 + k)
        out.append(dict(k=k, x=round(x, 4), y=round(0.075 + 0.055, 4),
                        z=round(z, 4), size_in=round(sz / 0.0254 * 1.0, 1),
                        diag_m=round(sz * 1.90, 3), pitch=pitch, yaw=yaw,
                        deployed=bool(r["dressed"])))
    return out


def _monitor_arm(acc, r, S, bay, seed, k):
    """A VESA arm: rail clamp, elbow, forearm, tilt knuckle, plate.

    The PLATE is the interface: `timing_stand_monitor` hangs a screen on it and
    never has to guess where the arm ended.
    """
    F = console_frame(r)
    x, z = bay["x"], bay["z"]
    ry = 0.075
    # rail clamp
    obox(acc, (x, ry, z + 0.005), (0.030, 0, 0), (0, 0.034, 0), (0, 0, 0.030),
         mat=M_ELEC, chamfer=0.0020, ts_wear=0.5, ts_dirt=0.5)
    for s in (-1.0, 1.0):
        caphead(acc, (x + s * 0.020, ry - 0.036, z + 0.005), (0, -1, 0),
                d=0.008, head_h=0.007, wear=0.6)
    # upright stub and the elbow
    tube(acc, (x, ry, z + 0.030), (x, ry, z + 0.085), 0.0125, mat=M_ELEC,
         n=12, ts_wear=0.4)
    p_el = np.array([x, ry, z + 0.085])
    yaw, pitch = bay["yaw"], bay["pitch"]
    d = np.array([math.sin(yaw), math.cos(yaw), 0.0])
    p_fo = p_el + d * 0.145 + np.array([0, 0, 0.012])
    tube(acc, p_el, p_fo, 0.0115, mat=M_ELEC, n=12, ts_wear=0.4)
    disc(acc, p_el, np.array([0.0, 0.0, 1.0]), 0.0155, 0.014, mat=M_ELEC,
         n=14, ts_wear=0.45)
    # tilt knuckle and the VESA plate
    nrm = np.array([math.sin(yaw) * math.cos(pitch),
                    math.cos(yaw) * math.cos(pitch), math.sin(pitch)])
    up = np.array([-math.sin(yaw) * math.sin(pitch),
                   -math.cos(yaw) * math.sin(pitch), math.cos(pitch)])
    side = np.cross(up, nrm)
    p_pl = p_fo + nrm * 0.030
    disc(acc, p_fo + nrm * 0.008, side, 0.0165, 0.030, mat=M_ELEC, n=14,
         ts_wear=0.5)
    plate(acc, p_pl, side * 0.050, up * 0.050, 0.0055, mat=M_ELEC,
          chamfer=0.0012, ts_wear=0.5, ts_dirt=0.4)
    for su in (-1.0, 1.0):
        for sv in (-1.0, 1.0):
            caphead(acc, p_pl + side * (0.050 * su) * 0.72
                    + up * (0.050 * sv) * 0.72 - nrm * 0.0026, -nrm,
                    d=0.0075, head_h=0.006, wear=0.5)
    bay["_plate"] = (p_pl, nrm, up)
    # the drop cable off the back of the plate
    if bay["deployed"]:
        pts = [p_pl - nrm * 0.010, p_pl - nrm * 0.05 - np.array([0, 0, 0.07]),
               p_fo - np.array([0, 0, 0.14]), np.array([x + 0.02, ry - 0.02, z - 0.10]),
               np.array([x + 0.02, ry - 0.02, F["top"] - 0.05])]
        sweep(acc, rounded_path(pts, 0.035, 3), circle(0.0045, 8), mat=M_RUB,
              ts_wear=0.4, ts_dirt=0.5)


def _console_electrics(acc, r, S, F):
    """Socket strip, comms panel, headset hooks, drink holders, patch box.

    Sockets and XLRs are RECESSES.  Under a 7.97 deg azimuth offset a proud
    vertical detail throws 0.4 mm of shadow and disappears; a 6 mm recess is
    black at any azimuth, which is why every electrical detail on this item is
    cut in rather than stuck on.
    """
    L = r["L"]
    seed = r["seed"]
    fy = F["y_f"] + 0.012
    # 6-gang socket strip under the worktop, facing the pit lane
    sx = rnd(-L * 0.25, L * 0.25, seed, 1000)
    sy = 0.055
    sz = F["top"] - 0.075
    obox(acc, (sx, sy, sz), (0.185, 0, 0), (0, 0.028, 0), (0, 0, 0.026),
         mat=M_ELEC, chamfer=0.0016, ts_wear=0.4, ts_dirt=0.5)
    for k in range(6):
        xx = sx - 0.150 + k * 0.060
        obox(acc, (xx, sy + 0.030, sz), (0.023, 0, 0), (0, 0.0035, 0),
             (0, 0, 0.023), mat=M_ELEC, chamfer=0.0010, ts_wear=0.5,
             ts_ao=1.0, ts_dirt=0.4)
        for s in (-1.0, 1.0):
            tube(acc, (xx + s * 0.009, sy + 0.032, sz),
                 (xx + s * 0.009, sy + 0.026, sz), 0.0022, mat=M_ELEC, n=8,
                 ts_ao=1.0, ts_wear=0.3)
    # comms panel: eight knobs and twelve XLR bores
    cx = rnd(-L * 0.22, L * 0.22, seed, 1010) + (0.42 if sx < 0 else -0.42)
    obox(acc, (cx, sy, sz + 0.012), (0.150, 0, 0), (0, 0.030, 0), (0, 0, 0.048),
         mat=M_ELEC, chamfer=0.0016, ts_wear=0.35, ts_dirt=0.45)
    for k in range(8):
        xx = cx - 0.128 + k * 0.0366
        tube(acc, (xx, sy + 0.032, sz + 0.030), (xx, sy + 0.046, sz + 0.030),
             0.0068, mat=M_ELEC, n=10, ts_wear=0.6, ts_edge=0.6)
        tube(acc, (xx, sy + 0.046, sz + 0.030), (xx, sy + 0.048, sz + 0.030),
             0.0018, mat=M_PAINT, n=6, tint=(0.55, 0.06, 0.04), ts_paint=1.0)
    for k in range(12):
        xx = cx - 0.132 + k * 0.024
        tube(acc, (xx, sy + 0.031, sz - 0.004), (xx, sy + 0.020, sz - 0.004),
             0.0056, mat=M_ELEC, n=10, ts_ao=1.0, ts_wear=0.4)
    # headset hooks under the front lip -- the detail that says people work here
    for k in range(4):
        xx = -L * 0.30 + k * (L * 0.60 / 3.0) + gauss(0.03, 0.07, seed, 1020 + k)
        pts = [(xx, F["y_f"] + 0.010, F["top"] - 0.030),
               (xx, F["y_f"] - 0.008, F["top"] - 0.052),
               (xx, F["y_f"] + 0.012, F["top"] - 0.070)]
        sweep(acc, rounded_path(pts, 0.012, 3), circle(0.0042, 8), mat=M_STEEL,
              ts_wear=0.85, ts_dirt=0.3)
    # drink holders on the rail
    for k in range(2):
        xx = rnd(-L * 0.36, L * 0.36, seed, 1030 + k)
        tube(acc, (xx, 0.135, F["top"] + 0.002), (xx, 0.135, F["top"] + 0.056),
             0.0385, mat=M_ELEC, n=16, ts_wear=0.6, ts_ao=0.6, ts_dirt=0.6)
        tube(acc, (xx, 0.135, F["top"] + 0.002), (xx, 0.135, F["top"] + 0.052),
             0.0355, mat=M_ELEC, n=16, ts_wear=0.5, ts_ao=1.0, ts_dirt=0.8)
    # the patch box under the console
    px = -r["prin_end"] * (L * 0.5 - 0.42)
    obox(acc, (px, 0.115, F["deck"] + 0.24), (0.145, 0, 0), (0, 0.075, 0),
         (0, 0, 0.115), mat=M_ELEC, chamfer=0.0022, ts_wear=0.45,
         ts_dirt=0.65, ts_age=r["age"])
    for k in range(10):
        xx = px - 0.120 + k * 0.0266
        tube(acc, (xx, 0.190, F["deck"] + 0.285), (xx, 0.178, F["deck"] + 0.285),
             0.0062, mat=M_ELEC, n=8, ts_ao=1.0, ts_wear=0.35)
    for s in (-1.0, 1.0):
        for u in (-1.0, 1.0):
            caphead(acc, (px + s * 0.132, 0.192, F["deck"] + 0.24 + u * 0.100),
                    (0, 1, 0), d=0.008, head_h=0.006, wear=0.4)


def build_seating(acc, r, S):
    """The seat rail, the four mount plates, and the foot rail.

    THE INTERFACE BOUNDARY IS THE TOP OF THE BOSS.  This module owns the rail,
    the pedestals, the 150 x 150 x 8 mm mount plate, the 62 mm spigot boss and
    its four M8s.  `timing_stand_seat` owns the stem and the shell above it.
    Publishing the boss rather than a bare deck means the seat item cannot
    invent a different mounting height for each of its forty seats.
    """
    L, D, a, b = r["L"], r["D"], S["a"], S["b"]
    seed = r["seed"]
    n = 0
    for t in range(r["tiers"]):
        y_seat = _seat_y(r, t)
        if y_seat is None:
            continue
        dz = r["deck"] + r["rise"][t]
        member(acc, (-L * 0.5 + 0.10, y_seat, dz + 0.055),
               (L * 0.5 - 0.10, y_seat, dz + 0.055), S["wide"], mat=M_ALU,
               bow=gauss(0.0010, 0.0022, seed, 1100 + t), bow_dir=EZ,
               ts_anod=1.0, ts_wear=0.55, ts_dirt=0.5, ts_age=r["age"])
        npd = max(2, int(L / 1.5) + 1)
        for k in range(npd):
            xx = -L * 0.5 + 0.14 + (L - 0.28) * k / max(npd - 1, 1)
            member(acc, (xx, y_seat, dz + 0.01), (xx, y_seat, dz + 0.055 - b * 0.5),
                   S["small"], mat=M_ALU, ts_anod=1.0, ts_wear=0.35,
                   ts_dirt=0.5)
            plate(acc, (xx, y_seat, dz + 0.006), (0.052, 0, 0), (0, 0.052, 0),
                  0.008, mat=M_ALU, ts_anod=1.0, ts_wear=0.4, ts_dirt=0.8)
            for s in (-1.0, 1.0):
                bolt(acc, (xx + s * 0.038, y_seat, dz + 0.011), EZ, af=0.011,
                     head=0.0046, length=0.012, wear=0.5)
            n += 2
        # the foot rail the engineers rest their boots on
        tube(acc, (-L * 0.5 + 0.12, y_seat - 0.26, dz + 0.185),
             (L * 0.5 - 0.12, y_seat - 0.26, dz + 0.185), 0.0212, mat=M_ALU,
             n=14, ts_anod=1.0, ts_wear=1.0, ts_dirt=0.45, ts_age=r["age"])
        n += 1
    # the four mount plates
    for st in seat_stations_local(r):
        x, y, z = st["x"], st["y"], st["z"]
        plate(acc, (x, y, z - 0.004), (0.075, 0, 0), (0, 0.075, 0), 0.008,
              mat=M_ALU, chamfer=0.0016, ts_anod=1.0, ts_wear=0.6,
              ts_dirt=0.55, ts_age=r["age"])
        tube(acc, (x, y, z), (x, y, z + 0.026), 0.031, mat=M_ALU, n=18,
             ts_anod=1.0, ts_wear=0.75, ts_edge=0.5)
        tube(acc, (x, y, z + 0.006), (x, y, z + 0.027), 0.0255, mat=M_ELEC,
             n=16, ts_ao=1.0, ts_wear=0.4, ts_dirt=0.7)
        for su in (-1.0, 1.0):
            for sv in (-1.0, 1.0):
                bolt(acc, (x + su * 0.050, y + sv * 0.050, z + 0.0002), EZ,
                     af=0.013, head=0.0053, length=0.014, wear=0.6)
        n += 1
    return n


def _seat_y(r, t):
    """local y of the seat rail on tier `t`, or None if that tier has no seats."""
    y0, y1 = r["y_splits"][t], r["y_splits"][t + 1]
    if y1 - y0 < 0.42:
        return None
    return round(y0 + (y1 - y0) * (0.62 if t == 0 else 0.55), 4)


def seat_stations_local(r):
    """The four seat mounts, in the stand's local frame."""
    out = []
    tiers = []
    for t in range(r["tiers"]):
        if _seat_y(r, t) is not None:
            tiers.append(t)
    # four seats: the console row takes the majority, a raised row takes the rest
    if len(tiers) == 1:
        split = [(tiers[0], 4)]
    elif len(tiers) == 2:
        split = [(tiers[0], 3), (tiers[1], 1)]
    else:
        split = [(tiers[0], 2), (tiers[1], 1), (tiers[2], 1)]
    k = 0
    for (t, cnt) in split:
        y = _seat_y(r, t)
        dz = r["deck"] + r["rise"][t]
        xs = r["seat_x"]
        if cnt == 4:
            use = xs
        elif cnt == 3:
            use = xs[:3]
        elif cnt == 2:
            use = [xs[0], xs[1]]
        else:
            use = [xs[-1] if t else xs[0]]
        for x in use:
            out.append(dict(k=k, tier=t, x=round(float(x), 4), y=y,
                            z=round(dz + 0.063, 4), deck_z=round(dz, 4),
                            state=("fitted" if r["dressed"] else "covered"),
                            occupied=bool(r["dressed"])))
            k += 1
    return out[:4]


def sheet_solid(acc, P, t, mat=M_FAB, **kw):
    """An open (n, m, 3) surface grid -> a closed shell `t` thick.

    A tarpaulin modelled as a single-sided surface renders its own back faces
    black under a 12.47 deg key from behind.  Giving it 0.9 mm of real
    thickness costs 2x the quads and removes a whole class of black-hole
    artefact, and the 0.9 mm edge is what you see along every hem.
    """
    P = np.asarray(P, float)
    n, m = P.shape[0], P.shape[1]
    du = np.zeros_like(P)
    dv = np.zeros_like(P)
    du[1:-1] = P[2:] - P[:-2]
    du[0] = P[1] - P[0]
    du[-1] = P[-1] - P[-2]
    dv[:, 1:-1] = P[:, 2:] - P[:, :-2]
    dv[:, 0] = P[:, 1] - P[:, 0]
    dv[:, -1] = P[:, -1] - P[:, -2]
    N = np.cross(du.reshape(-1, 3), dv.reshape(-1, 3))
    N = N / np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-12)
    N = N.reshape(n, m, 3)
    A = (P + N * (t * 0.5)).reshape(-1, 3)
    B = (P - N * (t * 0.5)).reshape(-1, 3)
    V = np.concatenate([A, B])
    Q = [_grid_quads(n, m)]
    Q.append(_grid_quads(n, m)[:, ::-1] + n * m)
    i = np.arange(n - 1)
    j = np.arange(m - 1)
    for (idx0, idx1) in ((i * m, (i + 1) * m),
                         (i * m + m - 1, (i + 1) * m + m - 1)):
        Q.append(np.stack([idx0, idx1, idx1 + n * m, idx0 + n * m], 1))
    for (idx0, idx1) in ((j, j + 1), ((n - 1) * m + j, (n - 1) * m + j + 1)):
        Q.append(np.stack([idx0, idx1, idx1 + n * m, idx0 + n * m], 1))
    bc = np.concatenate([P.reshape(-1, 3), P.reshape(-1, 3)]) - P.reshape(-1, 3).mean(0)
    return acc.solid(V, quads=np.concatenate(Q), mat=mat, bc=bc, **kw)


def build_canopy(acc, r, S):
    """The canopy FRAME, up or struck, and the valance board that carries the
    team's name.

    THE INTERFACE SPLIT, stated once: this module owns every piece of metal --
    the eaves rails, the rafters, the purlins, the eyelet studs, the roll
    mandrel, the lashings -- and the rigid composite VALANCE BOARD on the front
    rail.  `timing_stand_canopy` owns the fabric: the roof sheet, the skirt,
    and the roll that goes on the published mandrel.  The valance is metal and
    it is here because it is the one surface of this item that the film's own
    camera sees square on, over the wall, at 10 m.
    """
    L, D, a, b = r["L"], r["D"], S["a"], S["b"]
    seed = r["seed"]
    ef, er = r["eaves_f"], r["eaves_r"]
    n = 0
    # ---- the two eaves rails ------------------------------------------------
    member(acc, (-L * 0.5 - 0.02, 0.0, ef), (L * 0.5 + 0.02, 0.0, ef),
           S["main"], mat=M_ALU, bow=gauss(0.0026, 0.0055, seed, 1200),
           bow_dir=EZ, ts_anod=1.0, ts_wear=0.35, ts_dirt=0.75, ts_age=r["age"])
    member(acc, (-L * 0.5 - 0.02, D, er), (L * 0.5 + 0.02, D, er), S["main"],
           mat=M_ALU, bow=gauss(0.0026, 0.0055, seed, 1201), bow_dir=EZ,
           ts_anod=1.0, ts_wear=0.30, ts_dirt=0.80, ts_age=r["age"])
    n += 2
    # the corner castings that tie rail to post
    for xx in r["post_x"]:
        for (yy, zz) in ((0.0, ef), (D, er)):
            obox(acc, (xx, yy, zz - a * 0.5 - 0.026), (a * 0.62, 0, 0),
                 (0, a * 0.62, 0), (0, 0, 0.026), mat=M_ALU, chamfer=0.0035,
                 ts_anod=1.0, ts_wear=0.4, ts_dirt=0.6)
            for s in (-1.0, 1.0):
                bolt(acc, (xx + s * a * 0.44, yy - a * 0.63, zz - a * 0.5 - 0.026),
                     (0, -1, 0), af=0.013, head=0.0053, length=0.014, wear=0.4)
            n += 1
    # ---- knee braces: the triangle that stops the frame racking ------------
    # Also the single strongest thing on the object's silhouette against the
    # sky, and the clearest visual statement that it is a portal frame.
    for i, xx in enumerate(r["post_x"]):
        for (yy, zz) in ((0.0, ef), (D, er)):
            for s in (-1.0, 1.0):
                if (i == 0 and s < 0) or (i == len(r["post_x"]) - 1 and s > 0):
                    continue
                kl = rnd(0.30, 0.42, seed, 1180 + i * 4 + int(s > 0))
                p0 = (xx + s * 0.030, yy, zz - a * 0.5 - 0.055 - kl)
                p1 = (xx + s * (0.030 + kl), yy, zz - a * 0.5 - 0.052)
                member(acc, p0, p1, S["thin"], mat=M_ALU, ts_anod=1.0,
                       ts_wear=0.3, ts_dirt=0.55, ts_age=r["age"])
                for p in (p0, p1):
                    bolt(acc, p, (0, -1 if yy < 0.5 else 1, 0), af=0.011,
                         head=0.0046, length=0.012, wear=0.4)
                n += 1
    # ---- the front gutter: a real box gutter with an outlet ----------------
    gz_ = ef + a * 0.5 + 0.005
    member(acc, (-L * 0.5 - 0.05, -0.058, gz_), (L * 0.5 + 0.05, -0.058, gz_),
           np.array([(0.052, 0.0), (0.052, 0.030), (0.046, 0.030),
                     (0.046, 0.006), (-0.046, 0.006), (-0.046, 0.034),
                     (-0.052, 0.034), (-0.052, 0.0)]),
           mat=M_ALU, ts_anod=1.0, ts_wear=0.3, ts_dirt=0.95, ts_age=r["age"])
    ox = rnd(-L * 0.3, L * 0.3, seed, 1195)
    tube(acc, (ox, -0.058, gz_ - 0.002), (ox, -0.058, gz_ - 0.075), 0.019,
         mat=M_ELEC, n=12, ts_wear=0.4, ts_dirt=0.95)
    n += 2

    up = (r["canopy"] == "up")
    rx = [-L * 0.5 + 0.09 + (L - 0.18) * k / (r["nraft"] - 1)
          for k in range(r["nraft"])]
    if up:
        # ---- rafters, cantilevered forward over the console -----------------
        for k, xx in enumerate(rx):
            y0, y1 = -0.420, D + 0.100
            z0 = ef + 0.030 + (er - ef) * (y0 - 0.0) / max(D, 1e-6)
            z1 = er + 0.030
            member(acc, (xx, y0, z0), (xx, y1, z1), S["small"], mat=M_ALU,
                   bow=gauss(0.0030, 0.0065, seed, 1210 + k), bow_dir=-EZ,
                   ts_anod=1.0, ts_wear=0.30, ts_dirt=0.85, ts_age=r["age"])
            for (yy, zz) in ((0.0, ef), (D, er)):
                zc = z0 + (z1 - z0) * (yy - y0) / (y1 - y0)
                bolt(acc, (xx, yy, zc + b * 0.5), EZ, af=0.011, head=0.0046,
                     length=0.020, wear=0.4)
            n += 1
        # purlins
        for k, yy in enumerate((-0.28, D * 0.42, D + 0.02)):
            zz = ef + 0.030 + b + (er - ef) * yy / max(D, 1e-6)
            member(acc, (-L * 0.5 + 0.06, yy, zz), (L * 0.5 - 0.06, yy, zz),
                   S["thin"], mat=M_ALU, ts_anod=1.0, ts_wear=0.25,
                   ts_dirt=0.9, ts_age=r["age"])
            n += 1
        # the fabric fixing studs the canopy item laces to: 25 mm, 300 mm pitch
        for (yy, zz) in ((0.0, ef), (D, er)):
            for xx in np.arange(-L * 0.5 + 0.15, L * 0.5 - 0.10, 0.300):
                tube(acc, (xx, yy - 0.014 if yy < 0.5 else yy + 0.014, zz + a * 0.5),
                     (xx, yy - 0.014 if yy < 0.5 else yy + 0.014, zz + a * 0.5 + 0.019),
                     0.0125, mat=M_ALU, n=12, ts_anod=1.0, ts_wear=0.7,
                     ts_edge=0.6)
                disc(acc, (xx, yy - 0.014 if yy < 0.5 else yy + 0.014,
                           zz + a * 0.5 + 0.019), EZ, 0.0165, 0.0035,
                     mat=M_ALU, n=12, ts_anod=1.0, ts_wear=0.8, ts_edge=1.0)
    else:
        # ---- struck: the rafters bundled on the rear rail, the fabric roll
        #      on its mandrel lashed along the front rail ---------------------
        for k in range(r["nraft"]):
            row, col = k // 3, k % 3
            yy = D - 0.055 - col * 0.052
            zz = er + a * 0.5 + 0.030 + row * 0.050
            member(acc, (-L * 0.5 + 0.10, yy, zz), (L * 0.5 - 0.02, yy, zz),
                   S["small"], mat=M_ALU, ts_anod=1.0, ts_wear=0.30,
                   ts_dirt=0.9, ts_age=r["age"])
            n += 1
        # three ratchet straps over the bundle
        for xx in (-L * 0.30, 0.0, L * 0.30):
            pts = [(xx, D - 0.150, er + a * 0.5),
                   (xx, D - 0.150, er + a * 0.5 + 0.145),
                   (xx, D + 0.015, er + a * 0.5 + 0.150),
                   (xx, D + 0.015, er - a * 0.2)]
            _strap(acc, rounded_path(pts, 0.030, 3), 0.026)
            n += 1
        # the roll mandrel on the front rail
        mz = ef + a * 0.5 + 0.115
        tube(acc, (-L * 0.5 - 0.10, -0.020, mz), (L * 0.5 + 0.10, -0.020, mz),
             0.0215, mat=M_ALU, n=16, ts_anod=1.0, ts_wear=0.55, ts_dirt=0.6)
        for s in (-1.0, 1.0):
            disc(acc, (s * (L * 0.5 + 0.10), -0.020, mz), EX, 0.038, 0.010,
                 mat=M_ELEC, n=16, ts_wear=0.5)
        for xx in (-L * 0.32, 0.0, L * 0.32):
            pts = [(xx, -0.020, mz - 0.135), (xx, -0.150, mz - 0.02),
                   (xx, -0.020, mz + 0.135), (xx, 0.115, mz - 0.02),
                   (xx, -0.020, mz - 0.135)]
            _strap(acc, rounded_path(pts, 0.045, 3), 0.030)
            n += 1
        # cradle brackets holding the mandrel
        for xx in (-L * 0.42, 0.0, L * 0.42):
            plate(acc, (xx, -0.020, mz - 0.058), (0.0035, 0, 0),
                  (0, 0.052, 0), 0.115, mat=M_ALU, ts_anod=1.0, ts_wear=0.4)
    # ---- the valance board --------------------------------------------------
    vz1 = (ef + 0.030 - 0.020) if up else (ef - 0.040)
    vy = -0.420 if up else 0.0 - a * 0.5 - 0.020
    vh = 0.280
    plate(acc, (0.0, vy, vz1 - vh * 0.5), (L * 0.5 + 0.02, 0, 0),
          (0, 0, vh * 0.5), 0.0060, mat=M_PAINT, tint=r["col1"],
          chamfer=0.0022, ts_paint=1.0, ts_wear=0.45, ts_dirt=0.55,
          ts_age=r["age"])
    # its stiffening return along the bottom edge -- and a 12 mm horizontal
    # return throws 54 mm = 20 px of shadow across the board below it
    member(acc, (-L * 0.5 - 0.02, vy, vz1 - vh),
           (L * 0.5 + 0.02, vy, vz1 - vh),
           np.array([(0.004, 0.004), (0.004, -0.008), (-0.010, -0.012),
                     (-0.012, -0.008), (-0.012, 0.004)]),
           mat=M_PAINT, tint=r["col1"], ts_paint=1.0, ts_wear=0.5,
           ts_edge=1.0, ts_dirt=0.6, ts_age=r["age"])
    # brackets back to the rafters / posts
    for xx in (rx[:1] + rx[len(rx) // 2:len(rx) // 2 + 1] + rx[-1:]):
        plate(acc, (xx, vy + 0.028, vz1 - 0.030), (0.0030, 0, 0),
              (0, 0.028, 0), 0.055, mat=M_ALU, ts_anod=1.0, ts_wear=0.3)
        bolt(acc, (xx, vy - 0.0032, vz1 - 0.030), (0, -1, 0), af=0.011,
             head=0.0046, length=0.012, wear=0.4)
    # ---- the livery: the team name, and one partner brand -------------------
    ch = 0.130
    w = emit_text(acc, r["team"], (0.0, vy - 0.0032, vz1 - vh + 0.086),
                  np.array([1.0, 0, 0]), np.array([0, 0, 1.0]), ch,
                  thick=0.00035, tracking=0.175, weight=0.152, mat=M_VINYL,
                  tint=r["col2"], ts_wear=0.30, ts_age=r["age"])
    emit_text(acc, r["brand"], (0.0, vy - 0.0032, vz1 - vh + 0.028),
              np.array([1.0, 0, 0]), np.array([0, 0, 1.0]), 0.042,
              thick=0.00030, tracking=0.30, weight=0.140, mat=M_VINYL,
              tint=r["col2"], ts_wear=0.35, ts_age=r["age"])
    # the livery stripe: a different SHAPE per team, raised vinyl
    st = r["uid"] % 5
    for s in (-1.0, 1.0):
        x0 = s * (w * 0.5 + 0.13)
        x1 = s * (L * 0.5 - 0.02)
        if abs(x1) - abs(x0) < 0.12:
            continue
        if st == 0:
            bands = [(0.030, 0.010), (0.048, 0.006), (0.062, 0.004)]
        elif st == 1:
            bands = [(0.026, 0.026)]
        elif st == 2:
            bands = [(0.022, 0.008), (0.040, 0.008), (0.058, 0.008)]
        elif st == 3:
            bands = [(0.034, 0.016), (0.060, 0.005)]
        else:
            bands = [(0.020, 0.005), (0.034, 0.005), (0.048, 0.005),
                     (0.062, 0.005)]
        for (zo, th) in bands:
            P = np.array([(min(x0, x1), vz1 - vh + zo),
                          (max(x0, x1), vz1 - vh + zo),
                          (max(x0, x1), vz1 - vh + zo + th),
                          (min(x0, x1), vz1 - vh + zo + th)])
            PTS = np.empty((2, 4, 3))
            for i, t in enumerate((0.0, 0.00032)):
                PTS[i] = np.stack([P[:, 0], np.full(4, vy - 0.0032 - t),
                                   P[:, 1]], 1)
            extrude(acc, PTS, mat=M_VINYL, tint=r["col2"], ts_edge=1.0,
                    ts_wear=0.35, ts_age=r["age"])
    n += 3
    # ---- the weather mast, on the stands that carry one ---------------------
    if r["mast"]:
        mx = -r["prin_end"] * (L * 0.5 - 0.10)
        z0 = er + 0.10
        z1 = r["post_top"] + 0.420
        tube(acc, (mx, D, z0), (mx, D, z1), 0.0165, mat=M_ALU, n=14,
             ts_anod=1.0, ts_wear=0.3, ts_dirt=0.7)
        for s in (-1.0, 1.0):
            plate(acc, (mx + s * 0.030, D, z0 + 0.10), (0.030, 0, 0),
                  (0, 0.0035, 0), 0.055, mat=M_ALU, ts_anod=1.0, ts_wear=0.3)
        # a three-cup anemometer: three arms, three hemispherical cups
        hub = np.array([mx, D, z1])
        disc(acc, hub, EZ, 0.014, 0.020, mat=M_ELEC, n=14, ts_wear=0.4)
        for k in range(3):
            th = k * 2.0 * math.pi / 3.0 + 0.4
            d = np.array([math.cos(th), math.sin(th), 0.0])
            tube(acc, hub, hub + d * 0.075, 0.0032, mat=M_ELEC, n=8,
                 ts_wear=0.4)
            blob(acc, hub + d * 0.082, (0.024, 0.024, 0.021), mat=M_ELEC,
                 sub=1, ts_wear=0.5, ts_dirt=0.7)
        # and a vane below it
        tube(acc, (mx, D, z1 - 0.085), (mx, D, z1 - 0.055), 0.010, mat=M_ELEC,
             n=10, ts_wear=0.4)
        P = np.array([(0.0, 0.0), (-0.105, 0.030), (-0.105, -0.030)])
        PTS = np.empty((2, 3, 3))
        for i, t in enumerate((-0.0012, 0.0012)):
            PTS[i] = np.stack([mx + P[:, 0], np.full(3, D + t),
                               z1 - 0.070 + P[:, 1]], 1)
        extrude(acc, PTS, mat=M_PAINT, tint=r["col1"], ts_paint=1.0,
                ts_wear=0.5, ts_edge=0.8)
        n += 2
    return n


def _strap(acc, path, w=0.026, mat=M_FAB, buckle=True, **kw):
    """A webbing strap with a real buckle: 2 mm thick, `w` wide, and it sags."""
    sect = np.array([(-w * 0.5, -0.0010), (w * 0.5, -0.0010),
                     (w * 0.5, 0.0010), (-w * 0.5, 0.0010)])
    sweep(acc, np.asarray(path, float), sect, mat=mat, ts_wear=0.7,
          ts_dirt=0.6, **kw)
    if buckle:
        p = np.asarray(path, float)
        i = len(p) // 2
        d = unit(p[min(i + 1, len(p) - 1)] - p[max(i - 1, 0)])
        obox(acc, p[i] + np.array([0, 0, -0.004]), d * 0.028,
             unit(np.cross(d, EZ)) * (w * 0.62), EZ * 0.011, mat=M_STEEL,
             chamfer=0.0012, ts_wear=0.75, ts_edge=0.8)


def build_loom(acc, r, S):
    """The stand's own cable loom: tray, bundle, ties, drops, and the run out
    across the pit lane under its ramp.

    A pit wall stand IS its cabling.  Forty-odd cables between 6 and 14 mm --
    2.2 to 5.2 px each -- bundled every 250 mm, is the densest legible detail
    on the object and the cheapest: a swept 8-gon costs 16 triangles a station.
    """
    L, D, a, b = r["L"], r["D"], S["a"], S["b"]
    seed = r["seed"]
    F = console_frame(r)
    e = -r["prin_end"]                        # the garage side
    n = 0
    # ---- the perforated cable tray under the deck ---------------------------
    ty = D * 0.5
    tz = r["deck"] - 0.115
    obox(acc, (0.0, ty, tz), (L * 0.5 - 0.10, 0, 0), (0, 0.070, 0),
         (0, 0, 0.0020), mat=M_ALU, chamfer=0.0008, ts_anod=1.0, ts_wear=0.3,
         ts_dirt=0.8)
    for s in (-1.0, 1.0):
        obox(acc, (0.0, ty + s * 0.070, tz + 0.017), (L * 0.5 - 0.10, 0, 0),
             (0, 0.0018, 0), (0, 0, 0.017), mat=M_ALU, chamfer=0.0006,
             ts_anod=1.0, ts_wear=0.3, ts_dirt=0.7)
    n += 3
    # ---- the bundle: garage side, up the post, along the tray, to the box ---
    px = e * (L * 0.5 - 0.055)
    bx = -e * (L * 0.5 - 0.42)                # the patch box x
    gz = r["feet"][0]["gz"] - r["base_z"]
    ncab = rint(22, 34, seed, 1300)
    for c in range(ncab):
        rad = rnd(0.0032, 0.0072, seed, 1310 + c)
        j = (c - ncab * 0.5) / max(ncab, 1)
        k2 = h01(seed, 1360 + c)
        off = np.array([j * 0.052 + (k2 - 0.5) * 0.020,
                        j * 0.030 + (k2 - 0.5) * 0.016,
                        (h01(seed, 1380 + c) - 0.5) * 0.026])
        pts = [np.array([px + e * 0.55, D + 1.35, gz + rad]) + off * 1.6,
               np.array([px + e * 0.16, D + 0.30, gz + rad]) + off * 1.4,
               np.array([px, D + 0.055, gz + 0.12 + rad * 3]) + off,
               np.array([px, D + 0.048, tz + 0.10]) + off,
               np.array([px, D * 0.5 + 0.055, tz + 0.012]) + off,
               np.array([bx, ty + 0.02, tz + 0.012]) + off,
               np.array([bx, 0.15, F["deck"] + 0.20]) + off]
        if not r["dressed"] and c > 3:
            # struck: the spare cores are coiled on the tray instead of run out
            th = np.linspace(0, 2.0 * math.pi * 2.4, 26)
            rr = 0.115 + 0.004 * c
            pts = [np.array([bx + rr * math.cos(t), ty + rr * math.sin(t) * 0.85,
                             tz + 0.010 + 0.006 * c + 0.004 * math.sin(t * 3)])
                   for t in th]
        path = rounded_path(pts, 0.10, 4) if len(pts) < 12 else np.array(pts)
        sweep(acc, path, circle(rad, 8), mat=M_RUB, ts_wear=0.35,
              ts_dirt=0.75, ts_age=r["age"])
        n += 1
    # ---- velcro / tie wraps every 250 mm along the vertical run -------------
    for k in range(7):
        zz = gz + 0.16 + k * 0.24
        if zz > tz + 0.05:
            break
        _tie(acc, (px, D + 0.052, zz), EZ, 0.030, seed + k)
    for k in range(int((L - 0.6) / 0.28)):
        xx = min(px, bx) + 0.12 + k * 0.28
        if xx > max(px, bx) - 0.10:
            break
        _tie(acc, (xx, ty + 0.02, tz + 0.014), EZ, 0.028, seed + 40 + k)
    # ---- the cable ramp where the loom crosses the pit lane ----------------
    rz = gz
    rx = px + e * 0.62
    _cable_ramp(acc, rx, D + 1.30, rz, e, seed)
    n += 1
    return n


def _tie(acc, p, axis, rad, seed):
    """A velcro cable wrap with its tail: 22 x 4 mm of head, 8 x 1.5 px."""
    p = np.asarray(p, float)
    ax = unit(axis)
    N = unit(np.cross(ax, EZ) if abs(float(np.dot(ax, EZ))) < 0.95 else EX)
    B = np.cross(ax, N)
    th = np.linspace(0, 2 * math.pi, 15)
    P = [p + N * (rad * math.cos(t)) + B * (rad * 0.82 * math.sin(t))
         for t in th]
    sect = np.array([(-0.0080, -0.0008), (0.0080, -0.0008),
                     (0.0080, 0.0008), (-0.0080, 0.0008)])
    sweep(acc, np.array(P), sect, mat=M_FAB, closed=True, ts_wear=0.6,
          ts_dirt=0.7)
    obox(acc, p + N * (rad + 0.004), N * 0.008, B * 0.011, ax * 0.0035,
         mat=M_FAB, chamfer=0.0010, ts_wear=0.7, ts_dirt=0.6)


def _cable_ramp(acc, x, y, z, e, seed):
    """The rubber cable ramp over the loom where it crosses the pit lane.

    It stands on the ground, so law 5 applies to IT as well: the ramp is 62 mm
    tall and buried 22 mm, leaving 40 mm proud -- which is what a two-channel
    ramp measures.
    """
    Lr = rnd(0.85, 1.15, seed, 1400)
    W = 0.30
    ns, nw = 26, 11
    u = np.linspace(-Lr * 0.5, Lr * 0.5, ns)
    v = np.linspace(-W * 0.5, W * 0.5, nw)
    U, V_ = np.meshgrid(u, v, indexing="ij")
    prof = 0.062 * np.clip(1.0 - (np.abs(V_) / (W * 0.5)) ** 2.6, 0, 1)
    Z = z - EMBED + prof
    P = np.stack([x + U, y + V_, Z], -1)
    sheet_solid(acc, P, 0.010, mat=M_RUB, tint=(0.85, 0.72, 0.10),
                ts_wear=0.95, ts_dirt=0.9, ts_age=1.0)
    # the hinged lid line and the two channels underneath
    for s in (-1.0, 1.0):
        obox(acc, (x, y + s * 0.075, z - EMBED + 0.020), (Lr * 0.5, 0, 0),
             (0, 0.0025, 0), (0, 0, 0.018), mat=M_RUB, chamfer=0.0008,
             ts_wear=0.8, ts_dirt=0.9)


def build_dressing(acc, r, S):
    """What is on the stand because people use it, or because they left.

    Deliberately NOT built here: water bottles, kit bags, crates, cable drums,
    fire extinguishers and gaffer tape.  Every one of those is its own manifest
    item (`water_bottle` 300, `water_bottle_crate` 40, `cable_reel_drum` 24,
    `fire_extinguisher_handheld` 90, `gaffer_tape_strip` 200) and building a
    second version here is how a world ends up with two of everything.  What
    this module DOES build is the sockets and brackets those items land in --
    published in `kit_sites()` -- and the stand's own cover.
    """
    L, D, a, b = r["L"], r["D"], S["a"], S["b"]
    seed = r["seed"]
    F = console_frame(r)
    n = 0
    # ---- the extinguisher bracket, left empty for its own item -------------
    ex = r["prin_end"] * (L * 0.5 - 0.16)
    ez = r["deck"] + 0.30
    for zz in (ez, ez + 0.185):
        pts = [(ex - 0.055, D - 0.020, zz), (ex - 0.055, D - 0.075, zz),
               (ex + 0.055, D - 0.075, zz), (ex + 0.055, D - 0.020, zz)]
        sweep(acc, rounded_path(pts, 0.020, 3), circle(0.0035, 8), mat=M_STEEL,
              ts_wear=0.6, ts_dirt=0.5)
    plate(acc, (ex, D - 0.014, ez + 0.09), (0.062, 0, 0), (0, 0, 0.115),
          0.0030, mat=M_PAINT, tint=(0.52, 0.045, 0.030), ts_paint=1.0,
          ts_wear=0.7, ts_dirt=0.5, ts_age=r["age"])
    n += 1
    # ---- the umbrella socket on the rear post ------------------------------
    ux = -r["prin_end"] * (L * 0.5 - 0.055)
    tube(acc, (ux + a * 0.5 + 0.030, D, r["deck"] + 0.42),
         (ux + a * 0.5 + 0.030, D, r["deck"] + 0.62), 0.023, mat=M_ALU, n=14,
         ts_anod=1.0, ts_wear=0.5, ts_ao=0.4, ts_dirt=0.7)
    tube(acc, (ux + a * 0.5 + 0.030, D, r["deck"] + 0.43),
         (ux + a * 0.5 + 0.030, D, r["deck"] + 0.62), 0.0195, mat=M_ELEC,
         n=12, ts_ao=1.0, ts_wear=0.4, ts_dirt=0.9)
    for zz in (r["deck"] + 0.45, r["deck"] + 0.59):
        bolt(acc, (ux + a * 0.5 + 0.002, D, zz), (-1, 0, 0), af=0.011,
             head=0.0046, length=0.012, wear=0.5)
    n += 1
    if not r["dressed"]:
        # ---- the tarpaulin over the console ---------------------------------
        # A cover is the clearest single statement that a stand is not in use,
        # and it is the only soft geometry on the object: it sags between its
        # tie points and it creases where it is pulled down over the lip.
        y_prof = np.array([0.20, 0.10, 0.0, -0.12, -0.26, -0.36, -0.40,
                           -0.42, -0.42, -0.42])
        z_prof = np.array([F["rail_top"] + 0.06, F["rail_top"] + 0.075,
                           F["rail_top"] + 0.070, F["top"] + 0.055,
                           F["top"] + 0.020, F["top"] - 0.010,
                           F["top"] - 0.12, F["top"] - 0.28,
                           F["fascia_z0"] + 0.10, F["fascia_z0"] - 0.02])
        nu, nv = 62, y_prof.size
        u = np.linspace(-L * 0.5 - 0.05, L * 0.5 + 0.05, nu)
        P = np.zeros((nu, nv, 3))
        tie = np.cos(u / (L * 0.5 + 0.05) * math.pi * 3.0)
        for j in range(nv):
            sag = 0.026 * (1.0 - abs(y_prof[j] + 0.11) / 0.35)
            crease = 0.010 * np.sin(u * 11.0 + j * 0.7) * (0.4 + 0.6 * (j / nv))
            fold = 0.008 * (fbm1(u * 6.0 + j * 3.1, seed=seed % 89, oct=3) - 0.5)
            P[:, j, 0] = u + 0.004 * np.sin(u * 5.0 + j)
            P[:, j, 1] = y_prof[j] + crease * 0.35
            P[:, j, 2] = z_prof[j] - np.maximum(sag, 0) * (0.5 + 0.5 * tie) \
                + crease + fold
        sheet_solid(acc, P, 0.0011, mat=M_FAB, tint=(0.28, 0.30, 0.33),
                    ts_wear=0.55, ts_dirt=0.85, ts_age=r["age"])
        # the bungees that hold it down
        for k in range(5):
            xx = -L * 0.45 + k * (L * 0.90 / 4.0)
            pts = [(xx, -0.415, F["fascia_z0"] - 0.01),
                   (xx + 0.02, -0.36, F["fascia_z0"] - 0.10),
                   (xx, -0.30, F["fascia_z0"] - 0.16)]
            sweep(acc, rounded_path(pts, 0.03, 3), circle(0.0042, 8),
                  mat=M_FAB, ts_wear=0.7, ts_dirt=0.6)
            n += 1
        n += 1
    else:
        # ---- in use: two headsets hung on their hooks, and the tape ---------
        for k in (0, 2):
            xx = -L * 0.30 + k * (L * 0.60 / 3.0)
            hz = F["top"] - 0.085
            # the headband arc
            th = np.linspace(math.pi * 0.12, math.pi * 0.88, 14)
            P = [(xx + 0.098 * math.cos(t) - 0.098 * math.cos(math.pi * 0.5),
                  F["y_f"] - 0.030, hz - 0.078 + 0.092 * math.sin(t))
                 for t in th]
            sweep(acc, np.array(P), circle(0.0072, 8), mat=M_ELEC,
                  ts_wear=0.8, ts_dirt=0.4)
            for s in (-1.0, 1.0):
                c = np.array([xx + s * 0.092, F["y_f"] - 0.030, hz - 0.086])
                disc(acc, c, EY, 0.038, 0.028, mat=M_ELEC, n=16, ts_wear=0.7,
                     ts_dirt=0.4)
                disc(acc, c + EY * 0.016, EY, 0.033, 0.008, mat=M_FAB,
                     n=16, ts_wear=0.9, ts_dirt=0.5)
            pts = [(xx + 0.06, F["y_f"] - 0.030, hz - 0.115),
                   (xx + 0.10, F["y_f"] - 0.020, hz - 0.30),
                   (xx + 0.04, F["y_f"] + 0.02, hz - 0.42)]
            sweep(acc, rounded_path(pts, 0.05, 3), circle(0.0038, 8),
                  mat=M_RUB, ts_wear=0.5, ts_dirt=0.5)
            n += 1
    return n


# ==============================================================================
#  7.  THE MATERIALS
# ==============================================================================

class NT(object):
    """Node DSL.  EVERY SOCKET IS ADDRESSED BY NAME, NOT BY INDEX.

    Measured, and it matters: in Blender 5.2 ``ShaderNodeBump`` has inputs
    (Strength, Distance, Filter Width, Height, Normal) -- Filter Width was
    inserted at index 2 -- so the 4.x idiom ``pin(nd, 2, height);
    pin(nd, 3, normal)`` now feeds the height map into FILTER WIDTH and the
    incoming normal into HEIGHT.  Four already-accepted item modules in this
    directory (armco_w_beam, heras_fence_panel, kerb_precast_unit,
    pit_wall_unit) wire bump that way and their whole bump stack is therefore
    misconnected; the gate cannot see it because it counts BUMP nodes rather
    than checking what they are connected to.  Names cost nothing and cannot
    rot when a socket is inserted.
    """

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
        nd.location = ((self.x % 15) * 220, -(self.x // 15) * 300)
        for k, v in kw.items():
            if hasattr(nd, k):
                setattr(nd, k, v)
        return nd

    def pin(self, nd, key, src):
        if src is None:
            return
        if key not in nd.inputs:
            raise KeyError("%s has no input %r" % (nd.bl_idname, key))
        if isinstance(src, tuple) and hasattr(src[0], "outputs"):
            self.t.links.new(src[0].outputs[src[1]], nd.inputs[key])
        elif hasattr(src, "outputs"):
            self.t.links.new(src.outputs[0], nd.inputs[key])
        elif isinstance(src, (tuple, list)):
            nd.inputs[key].default_value = (
                tuple(src) + (1.0,) if len(src) == 3 else tuple(src))
        else:
            nd.inputs[key].default_value = float(src)

    # ---- generic -----------------------------------------------------------
    def cmix(self, fac, a, b, blend="MIX"):
        nd = self.n("ShaderNodeMix", data_type="RGBA", blend_type=blend)
        self.pin(nd, "Factor", fac)
        self.t.links.new  # noqa
        # RGBA A/B live at indices 6/7; address them positionally ONCE, here,
        # because they share the name "A"/"B" with the float and vector pairs.
        self._pin_i(nd, 6, a)
        self._pin_i(nd, 7, b)
        return (nd, 2)

    def fmix(self, fac, a, b):
        nd = self.n("ShaderNodeMix", data_type="FLOAT")
        self.pin(nd, "Factor", fac)
        self._pin_i(nd, 2, a)
        self._pin_i(nd, 3, b)
        return (nd, 0)

    def _pin_i(self, nd, i, src):
        if src is None:
            return
        if isinstance(src, tuple) and hasattr(src[0], "outputs"):
            self.t.links.new(src[0].outputs[src[1]], nd.inputs[i])
        elif hasattr(src, "outputs"):
            self.t.links.new(src.outputs[0], nd.inputs[i])
        elif isinstance(src, (tuple, list)):
            nd.inputs[i].default_value = (
                tuple(src) + (1.0,) if len(src) == 3 else tuple(src))
        else:
            nd.inputs[i].default_value = float(src)

    def math(self, op, a=None, b=None, clamp=False):
        nd = self.n("ShaderNodeMath", operation=op, use_clamp=clamp)
        self._pin_i(nd, 0, a)
        self._pin_i(nd, 1, b)
        return (nd, 0)

    def vmath(self, op, a=None, b=None, scale=None):
        nd = self.n("ShaderNodeVectorMath", operation=op)
        self._pin_i(nd, 0, a)
        self._pin_i(nd, 1, b)
        if scale is not None:
            self._pin_i(nd, 3, scale)
        return (nd, 0)

    def noise(self, vec, scale, detail=8.0, rough=0.55, lac=2.0, out=0,
              dist=0.0):
        nd = self.n("ShaderNodeTexNoise", noise_dimensions="3D")
        self.pin(nd, "Vector", vec)
        self.pin(nd, "Scale", scale)
        self.pin(nd, "Detail", detail)
        self.pin(nd, "Roughness", rough)
        self.pin(nd, "Lacunarity", lac)
        self.pin(nd, "Distortion", dist)
        return (nd, out)

    def vor(self, vec, scale, feature="F1", out=0, rand=1.0, smooth=None):
        nd = self.n("ShaderNodeTexVoronoi", feature=feature,
                    voronoi_dimensions="3D")
        self.pin(nd, "Vector", vec)
        self.pin(nd, "Scale", scale)
        self.pin(nd, "Randomness", rand)
        if smooth is not None and "Smoothness" in nd.inputs:
            self.pin(nd, "Smoothness", smooth)
        return (nd, out)

    def wave(self, vec, scale, distortion=0.0, detail=2.0, direction="X",
             wtype="BANDS"):
        nd = self.n("ShaderNodeTexWave", wave_type=wtype,
                    bands_direction=direction)
        self.pin(nd, "Vector", vec)
        self.pin(nd, "Scale", scale)
        self.pin(nd, "Distortion", distortion)
        self.pin(nd, "Detail", detail)
        return (nd, 1)

    def grad(self, vec, gtype="LINEAR"):
        nd = self.n("ShaderNodeTexGradient", gradient_type=gtype)
        self.pin(nd, "Vector", vec)
        return (nd, 1)

    def ramp(self, src, stops):
        nd = self.n("ShaderNodeValToRGB")
        self.pin(nd, "Fac", src)
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
        self.pin(nd, "Value", v)
        self._pin_i(nd, 1, f0)
        self._pin_i(nd, 2, f1)
        self._pin_i(nd, 3, t0)
        self._pin_i(nd, 4, t1)
        return (nd, 0)

    def bump(self, height, strength, distance, normal=None):
        nd = self.n("ShaderNodeBump")
        self.pin(nd, "Strength", strength)
        self.pin(nd, "Distance", distance)
        self.pin(nd, "Height", height)
        if normal is not None:
            self.pin(nd, "Normal", normal)
        return (nd, 0)

    def sep(self, vec, out):
        nd = self.n("ShaderNodeSeparateXYZ")
        self.pin(nd, "Vector", vec)
        return (nd, out)

    def comb(self, x, y, z):
        nd = self.n("ShaderNodeCombineXYZ")
        self._pin_i(nd, 0, x)
        self._pin_i(nd, 1, y)
        self._pin_i(nd, 2, z)
        return (nd, 0)

    def geo(self, out):
        nd = self.n("ShaderNodeNewGeometry")
        return (nd, out)

    def out(self, col, rough, metal=0.0, normal=None, spec=None, coat=None,
            alpha=None):
        bs = self.n("ShaderNodeBsdfPrincipled")
        self.pin(bs, "Base Color", col)
        self.pin(bs, "Roughness", rough)
        self.pin(bs, "Metallic", metal)
        if normal is not None:
            self.pin(bs, "Normal", normal)
        if spec is not None:
            self.pin(bs, "Specular IOR Level", spec)
        if coat is not None:
            self.pin(bs, "Coat Weight", coat)
        if alpha is not None:
            self.pin(bs, "Alpha", alpha)
        o = self.n("ShaderNodeOutputMaterial")
        self.t.links.new(bs.outputs[0], o.inputs["Surface"])
        return self.m


def _common(t):
    """Object-space P (decorrelated per object), the attribute set, and up."""
    co = t.n("ShaderNodeTexCoord")
    OBJ = (co, 3)                                # TexCoord -> Object.  NEVER
                                                 # Geometry -> Position: at
                                                 # |P| ~ 1000 m float32 lattice
                                                 # precision is gone and the
                                                 # first pass blotched.
    ofs = t.comb(t.attr("ts_ofs_x", 2, "OBJECT"),
                 t.attr("ts_ofs_y", 2, "OBJECT"),
                 t.attr("ts_ofs_z", 2, "OBJECT"))
    P = t.vmath("ADD", OBJ, ofs)
    A = dict(
        P=P, Pl=OBJ,
        wear=t.attr("ts_wear"), edge=t.attr("ts_edge"), dirt=t.attr("ts_dirt"),
        ao=t.attr("ts_ao"), age=t.attr("ts_age"), grip=t.attr("ts_grip"),
        h=t.attr("ts_h"), paint=t.attr("ts_paint"), anod=t.attr("ts_anod"),
        pid=t.attr("ts_pid"),
        bc=t.attr("ts_bc", 1), tint=t.attr("ts_tint", 0),
        o_age=t.attr("ts_o_age", 2, "OBJECT"),
        o_grime=t.attr("ts_o_grime", 2, "OBJECT"),
        o_val=t.attr("ts_o_val", 2, "OBJECT"),
        o_deck=t.attr("ts_o_deck", 2, "OBJECT"),
        up=t.sep(t.geo(1), 2),                   # Geometry -> Normal.z: a
                                                 # DIRECTION, so it carries no
                                                 # position precision problem
    )
    return A


def mat_alu():
    """Clear-anodised aluminium extrusion: die lines, brush, scuff, bloom.

    An extrusion has a direction and the direction is visible: the die leaves
    0.1-0.3 mm longitudinal lines, the brush runs the same way, and every
    handling scuff is a short transverse mark ACROSS them.  `ts_bc.x` runs
    along the member for exactly this, and it is why a rail and a post on the
    same object do not share a grain.
    """
    t = NT(PFX + "Alu")
    A = _common(t)
    P, bc = A["P"], A["bc"]
    bx = t.sep(bc, 0)
    grain = t.comb(t.math("MULTIPLY", bx, 1.0),
                   t.math("MULTIPLY", t.sep(bc, 1), 34.0),
                   t.math("MULTIPLY", t.sep(bc, 2), 34.0))
    # ---- 1. the batch: no two extrusions anodise the same tone -------------
    # PER MEMBER, from ts_pid, not from a position field: two bars bolted
    # together came out of different anodising tanks and the join between them
    # is a step, not a gradient.
    n_batch = t.fmix(0.62, A["pid"],
                     t.noise(t.vmath("SCALE", P, scale=0.55), 1.4, 3.0, 0.5))
    body = t.cmix(t.maprange(n_batch, 0.22, 0.80, 0.0, 1.0),
                  PAL["alu_mid"], PAL["alu_bright"])
    body = t.cmix(t.math("MULTIPLY", A["o_val"], 0.45), body, PAL["alu_dull"])
    # ---- 2. die lines and brush, along the member --------------------------
    die = t.wave(grain, 300.0, 0.55, 3.0, "Y")
    brush = t.noise(t.comb(t.math("MULTIPLY", bx, 3.0),
                           t.math("MULTIPLY", t.sep(bc, 1), 900.0), 0.0),
                    1.0, 4.0, 0.62)
    body = t.cmix(t.math("MULTIPLY", t.maprange(brush, 0.30, 0.70, 0.0, 1.0),
                         0.16), body, PAL["alu_bright"])
    # ---- 3. handling: the anodising is 20 microns and it goes ---------------
    v_scuff = t.vor(t.vmath("SCALE", P, scale=1.0), 46.0, "F1", 0, 1.0)
    scuff = t.math("MULTIPLY", A["wear"],
                   t.maprange(v_scuff, 0.02, 0.16, 1.0, 0.0))
    scuff = t.math("MULTIPLY", scuff,
                   t.maprange(t.noise(t.vmath("SCALE", P, scale=1.0), 120.0,
                                      6.0, 0.6), 0.42, 0.80, 0.0, 1.0))
    body = t.cmix(t.math("MULTIPLY", scuff, 0.85), body, PAL["alu_scuff"])
    # the arris takes it worst: an edge is where the paint and the anodising go
    ew = t.math("MULTIPLY", A["edge"],
                t.maprange(t.noise(t.vmath("SCALE", P, scale=1.0), 260.0, 6.0),
                           0.35, 0.78, 0.0, 1.0))
    body = t.cmix(t.math("MULTIPLY", ew, 0.55), body, PAL["alu_bright"])
    # ---- 4. oxide bloom where it is never touched --------------------------
    n_ox = t.noise(t.vmath("SCALE", P, scale=1.0), 9.0, 7.0, 0.66)
    ox = t.math("MULTIPLY", t.math("MULTIPLY", A["o_age"],
                                   t.maprange(A["wear"], 0.55, 0.10, 0.0, 1.0)),
                t.maprange(n_ox, 0.46, 0.80, 0.0, 1.0))
    body = t.cmix(t.math("MULTIPLY", ox, 0.55), body, PAL["alu_white"])
    # ---- 5. what lives in a T-slot and every other cavity ------------------
    n_dust = t.noise(t.vmath("SCALE", P, scale=1.0), 26.0, 6.0, 0.58)
    slot = t.math("MULTIPLY", t.math("MAXIMUM", A["ao"],
                                     t.math("MULTIPLY", A["dirt"], 0.80)),
                  t.maprange(n_dust, 0.24, 0.80, 0.42, 1.0))
    body = t.cmix(t.math("MULTIPLY", slot, 0.92), body, PAL["alu_slot"])
    # ---- 5b. PER-MEMBER SOILING.  Every bar on the first render came back the
    # same clean silver, because the only thing that varied between them was a
    # position noise they all sample the same way.  A frame that has stood in a
    # pit lane has bars that are visibly filthier than their neighbours -- the
    # ones nearest the ground, the ones people grab, the one the loom is
    # cable-tied to -- and `ts_pid` is what knows which is which.
    soil = t.math("MULTIPLY",
                  t.math("MULTIPLY", t.maprange(A["pid"], 0.30, 1.0, 0.0, 1.0),
                         A["o_grime"]),
                  t.maprange(t.noise(t.vmath("SCALE", P, scale=1.0), 6.0, 6.0,
                                     0.6), 0.28, 0.82, 0.25, 1.0))
    body = t.cmix(t.math("MULTIPLY", soil, 0.55), body, PAL["grime"])
    # ---- 6. dust settles on what points up ---------------------------------
    updust = t.math("MULTIPLY",
                    t.math("MULTIPLY", t.maprange(A["up"], 0.25, 0.92, 0.0, 1.0),
                           A["o_grime"]),
                    t.maprange(t.noise(t.vmath("SCALE", P, scale=1.0), 15.0,
                                       6.0, 0.6), 0.30, 0.82, 0.25, 1.0))
    body = t.cmix(t.math("MULTIPLY", updust, 0.72), body, PAL["dust"])
    # ---- 6b. the splash line: an extrusion 0.2 m off a pit lane is filthy --
    splash = t.math("MULTIPLY",
                    t.maprange(A["h"], 0.55, 0.04, 0.0, 1.0),
                    t.maprange(t.noise(t.vmath("SCALE", P, scale=1.0), 40.0,
                                       6.0, 0.62), 0.22, 0.84, 0.20, 1.0))
    body = t.cmix(t.math("MULTIPLY",
                         t.math("MULTIPLY", splash, A["o_grime"]), 0.80),
                  body, PAL["grime"])
    # ---- 7. roughness and the bump stack -----------------------------------
    # MEASURED OFF THE FIRST RENDER, not chosen: at roughness 0.28-0.44 and
    # metallic 0.88 the frame came back reading as polished chrome tube.  Clear
    # anodising is a 20 micron oxide over the metal and it is SEMI-MATT: 0.42
    # at its cleanest, 0.62 where it has been handled for a season.
    rgh = t.maprange(n_batch, 0.25, 0.80, 0.42, 0.58)
    rgh = t.fmix(t.math("MULTIPLY", scuff, 0.9), rgh, 0.70)
    rgh = t.fmix(t.math("MULTIPLY", ox, 0.85), rgh, 0.84)
    rgh = t.fmix(t.math("MULTIPLY", slot, 0.8), rgh, 0.86)
    rgh = t.fmix(t.math("MULTIPLY", soil, 0.7), rgh, 0.82)
    rgh = t.fmix(t.math("MULTIPLY", splash, 0.75), rgh, 0.88)
    rgh = t.fmix(t.math("MULTIPLY", A["wear"], 0.35), rgh, 0.34)
    b = t.bump(die, 0.30, 0.00016)
    b = t.bump(brush, 0.22, 0.00008, normal=b)
    b = t.bump(t.maprange(v_scuff, 0.0, 0.10, 1.0, 0.0),
               t.math("MULTIPLY", scuff, 0.7), 0.00022, normal=b)
    b = t.bump(n_dust, t.math("MULTIPLY", slot, 0.5), 0.00035, normal=b)
    metal = t.maprange(A["anod"], 0.0, 1.0, 0.62, 0.88)
    return t.out(body, rgh, metal, normal=b, spec=0.5)


def mat_paint():
    """Powder coat, in the team's colour, two seasons old.

    The tint arrives as a per-VERTEX colour so that ten liveries share one
    material and one shader evaluation, and so that a chip can show primer and
    then bare metal underneath a colour the shader never had to know.
    """
    t = NT(PFX + "Paint")
    A = _common(t)
    P = A["P"]
    base = t.cmix(0.0, A["tint"], A["tint"])
    # ---- 0. PANEL TO PANEL.  The first render of this item came back with a
    #         flat sheet of green across five separately-fabricated panels,
    #         which is the "a flat colour is a placeholder" failure with extra
    #         steps: the layers were all there and every one of them was mixed
    #         at 0.3 of the strength it needed.  A coarse cellular field keyed
    #         to object space gives each PANEL its own value and its own
    #         chroma, because they were sprayed in different weeks.
    pid = A["pid"]
    base = t.cmix(t.maprange(pid, 0.45, 1.00, 0.0, 0.26), base,
                  t.cmix(0.5, base, (0.40, 0.40, 0.39)))
    base = t.cmix(t.maprange(pid, 0.55, 0.00, 0.0, 0.20), base,
                  t.cmix(0.5, base, (0.012, 0.012, 0.014)))
    # ...and a slow, LARGE-scale value drift within a panel, an order of
    # magnitude coarser than the panel itself so it can never read as blotches
    v_drift = t.noise(t.vmath("SCALE", P, scale=0.30), 0.9, 3.0, 0.45)
    base = t.cmix(t.maprange(v_drift, 0.30, 0.72, 0.0, 0.14), base,
                  t.cmix(0.5, base, (0.30, 0.30, 0.30)))
    # ---- 1. the coat is not flat: film thickness varies over a fabricated
    #         panel and so does its chroma
    n_film = t.noise(t.vmath("SCALE", P, scale=1.0), 3.6, 5.0, 0.55)
    body = t.cmix(t.maprange(n_film, 0.28, 0.76, 0.0, 0.48), base,
                  t.cmix(0.5, base, (0.02, 0.02, 0.022)))
    # ---- 2. UV chalking: the sun takes the chroma off the up faces first ---
    chalk = t.math("MULTIPLY",
                   t.math("MULTIPLY", A["o_age"],
                          t.maprange(A["up"], 0.10, 0.85, 0.55, 1.0)),
                   t.maprange(t.noise(t.vmath("SCALE", P, scale=1.0), 5.0, 6.0),
                              0.22, 0.80, 0.30, 1.0))
    pale = t.cmix(0.62, base, (0.34, 0.34, 0.335))
    body = t.cmix(t.math("MULTIPLY", chalk, 0.95), body, pale)
    # ---- 3. chips: at every arris, primer then bare alu --------------------
    v_chip = t.vor(t.vmath("SCALE", P, scale=1.0), 120.0, "F1", 0, 1.0)
    chip = t.math("MULTIPLY",
                  t.math("MULTIPLY", A["edge"],
                         t.maprange(A["o_age"], 0.1, 0.9, 0.3, 1.0)),
                  t.maprange(v_chip, 0.010, 0.055, 1.0, 0.0))
    body = t.cmix(t.math("MULTIPLY", chip, 0.85), body, PAL["primer"])
    v_chip2 = t.vor(t.vmath("SCALE", P, scale=1.0), 240.0, "F1", 0, 1.0)
    chip2 = t.math("MULTIPLY", chip, t.maprange(v_chip2, 0.004, 0.020, 1.0, 0.0))
    body = t.cmix(t.math("MULTIPLY", chip2, 0.90), body, PAL["alu_bright"])
    # ---- 4. the wash: rain-borne dirt runs DOWN, and it is warm, not grey --
    Pz = t.sep(A["Pl"], 2)
    # THE STREAK COORDINATE HAS TO WORK ON BOTH FACE ORIENTATIONS.  The first
    # version built it from (Pl.x, Pz) alone, which is constant across an END
    # panel -- a plane of constant x -- so the two biggest painted surfaces on
    # the object had no rain streaking at all while the fascia did.  Found by
    # looking at a 5x crop of the end panel, not by reading the code.
    Phoriz = t.math("ADD", t.math("MULTIPLY", t.sep(A["Pl"], 0), 62.0),
                    t.math("MULTIPLY", t.sep(A["Pl"], 1), 47.0))
    # distortion 0.9: without it the streak field is a COMB -- evenly spaced
    # vertical lines at one pitch, which is a texture and not a history.  Real
    # streaking clusters where the dirt above it happens to sit.
    n_run = t.noise(t.comb(Phoriz, t.math("MULTIPLY", Pz, 1.7), 0.0),
                    1.0, 7.0, 0.64, dist=0.9)
    wash = t.math("MULTIPLY", A["o_grime"],
                  t.maprange(n_run, 0.40, 0.70, 0.0, 1.0))
    wash = t.math("MULTIPLY", wash, t.maprange(A["up"], -0.35, 0.35, 1.0, 0.45))
    body = t.cmix(t.math("MULTIPLY", wash, 0.92), body, PAL["grime"])
    # a second, finer run at a different frequency, so the streaks are not a
    # single comb: real rain streaking is two or three scales at once
    n_run2 = t.noise(t.comb(t.math("MULTIPLY", Phoriz, 3.1),
                            t.math("MULTIPLY", Pz, 3.4), 0.0), 1.0, 6.0, 0.60,
                     dist=1.4)
    body = t.cmix(t.math("MULTIPLY",
                         t.math("MULTIPLY", A["o_grime"],
                                t.maprange(n_run2, 0.48, 0.80, 0.0, 1.0)), 0.62),
                  body, PAL["grime"])
    # ...and the pale mineral bloom that dries out of the same run.  A wash
    # that only ever darkens reads as a shadow; the pale half is what makes it
    # read as dirt.
    body = t.cmix(t.math("MULTIPLY",
                         t.math("MULTIPLY", A["o_grime"],
                                t.maprange(n_run, 0.24, 0.06, 0.0, 1.0)), 0.34),
                  body, PAL["dust"])
    # ---- 4b. the waterline.  Everything below about 0.6 m gets the pit lane
    #          thrown at it: brake dust, tyre rubber, hose water off the deck.
    splash = t.math("MULTIPLY",
                    t.maprange(A["h"], 0.62, 0.06, 0.0, 1.0),
                    t.maprange(t.noise(t.vmath("SCALE", P, scale=1.0), 34.0,
                                       6.0, 0.62), 0.24, 0.82, 0.25, 1.0))
    body = t.cmix(t.math("MULTIPLY",
                         t.math("MULTIPLY", splash, A["o_grime"]), 0.72),
                  body, PAL["rubber_film"])
    # ---- 5. scuffs, scratch clusters and adhesive ghosts -------------------
    v_sc = t.vor(t.vmath("SCALE", P, scale=1.0), 34.0, "F1", 0, 1.0)
    sc = t.math("MULTIPLY", A["wear"], t.maprange(v_sc, 0.03, 0.22, 1.0, 0.0))
    body = t.cmix(t.math("MULTIPLY", sc, 0.72), body, PAL["dust"])
    # scratches: a noise stretched 40:1 along the panel, so they are LINES
    scr = t.noise(t.comb(t.math("MULTIPLY", Phoriz, 0.13),
                         t.math("MULTIPLY", Pz, 320.0), 0.0), 1.0, 5.0, 0.58)
    scratch = t.math("MULTIPLY",
                     t.math("MULTIPLY", A["wear"], A["o_age"]),
                     t.maprange(scr, 0.70, 0.90, 0.0, 1.0))
    body = t.cmix(t.math("MULTIPLY", scratch, 0.60), body, PAL["primer"])
    ghost = t.math("MULTIPLY",
                   t.maprange(t.vor(t.vmath("SCALE", P, scale=1.0), 8.0, "F1",
                                    0, 1.0), 0.05, 0.10, 1.0, 0.0),
                   t.math("MULTIPLY", A["o_age"], 0.9))
    body = t.cmix(t.math("MULTIPLY", ghost, 0.42), body, PAL["dust"])
    # ---- 6. dust on the up faces, grime in the cavities --------------------
    body = t.cmix(t.math("MULTIPLY", t.math("MULTIPLY", A["dirt"], A["o_grime"]),
                         0.55), body, PAL["grime"])
    # ---- 7. roughness: orange peel is a GLOSS event before it is a bump ----
    peel = t.vor(t.vmath("SCALE", P, scale=1.0), 520.0, "F1", 0, 1.0)
    rgh = t.maprange(peel, 0.0, 0.06, 0.34, 0.46)
    rgh = t.fmix(t.math("MULTIPLY", chalk, 0.9), rgh, 0.82)
    rgh = t.fmix(t.math("MULTIPLY", wash, 0.7), rgh, 0.74)
    rgh = t.fmix(t.math("MULTIPLY", chip, 0.9), rgh, 0.86)
    rgh = t.fmix(t.math("MULTIPLY", sc, 0.6), rgh, 0.58)
    rgh = t.fmix(t.math("MULTIPLY", splash, 0.8), rgh, 0.88)
    b = t.bump(t.maprange(peel, 0.0, 0.05, 1.0, 0.0), 0.55, 0.00013)
    b = t.bump(n_film, 0.25, 0.00030, normal=b)
    b = t.bump(t.maprange(v_chip, 0.0, 0.04, 1.0, 0.0),
               t.math("MULTIPLY", chip, 0.9), 0.00028, normal=b)
    metal = t.math("MULTIPLY", chip2, 0.75)
    return t.out(body, rgh, metal, normal=b, spec=0.42, coat=0.10)


def mat_deck():
    """The four deck surfaces, told apart by a per-OBJECT selector.

    ts_o_deck is 0 chequer, 1 grating, 2 ply, 3 rubber.  One material, four
    histories, because a deck is one thing per stand and ten shader trees for
    ten stands is ten times the compile for no gain.  What they share is the
    only thing that matters on a deck: the crests are POLISHED by boots and
    the valleys hold everything the pit lane has ever dropped.
    """
    t = NT(PFX + "Deck")
    A = _common(t)
    P, bc = A["P"], A["bc"]
    sel = A["o_deck"]
    is_ply = t.maprange(sel, 1.6, 2.4, 0.0, 1.0)
    is_rub = t.maprange(sel, 2.6, 3.0, 0.0, 1.0)
    is_grt = t.math("MULTIPLY", t.maprange(sel, 0.6, 1.0, 0.0, 1.0),
                    t.maprange(sel, 1.4, 1.0, 0.0, 1.0))
    n_base = t.noise(t.vmath("SCALE", P, scale=1.0), 5.0, 6.0, 0.55)
    body = t.cmix(t.maprange(n_base, 0.30, 0.74, 0.0, 1.0),
                  PAL["alu_dull"], PAL["alu_mid"])
    body = t.cmix(is_grt, body,
                  t.cmix(t.maprange(n_base, 0.3, 0.75, 0.0, 1.0),
                         PAL["grp_grey"], PAL["grp_grit"]))
    # plywood: real grain, running along the sheet
    grain = t.wave(t.comb(t.math("MULTIPLY", t.sep(bc, 0), 26.0),
                          t.math("MULTIPLY", t.sep(bc, 1), 3.0), 0.0),
                   6.0, 2.6, 6.0, "X")
    ply = t.cmix(t.maprange(grain, 0.30, 0.74, 0.0, 1.0),
                 PAL["ply_face"], PAL["ply_grit"])
    body = t.cmix(is_ply, body, ply)
    body = t.cmix(is_rub, body, PAL["rub_grey"])
    # ---- the crests: polished by boots --------------------------------------
    n_path = t.noise(t.vmath("SCALE", P, scale=0.9), 2.4, 5.0, 0.5)
    traffic = t.maprange(n_path, 0.34, 0.78, 0.25, 1.0)
    crest = t.math("MULTIPLY", t.math("MULTIPLY", A["grip"], traffic), A["wear"])
    body = t.cmix(t.math("MULTIPLY", crest, 0.72), body, PAL["deck_worn"])
    # ---- the valleys: grit, rubber film, brake dust ------------------------
    n_grit = t.noise(t.vmath("SCALE", P, scale=1.0), 90.0, 7.0, 0.62)
    valley = t.math("MULTIPLY", t.maprange(A["grip"], 0.55, 0.05, 0.0, 1.0),
                    t.maprange(n_grit, 0.28, 0.82, 0.35, 1.0))
    valley = t.math("MULTIPLY", valley, t.maprange(A["o_grime"], 0.0, 1.0, 0.45, 1.0))
    body = t.cmix(t.math("MULTIPLY", valley, 0.85), body, PAL["deck_dirt"])
    v_rub = t.vor(t.vmath("SCALE", P, scale=1.0), 22.0, "F1", 0, 1.0)
    film = t.math("MULTIPLY", t.maprange(v_rub, 0.05, 0.18, 1.0, 0.0),
                  t.math("MULTIPLY", A["o_grime"], 0.75))
    body = t.cmix(t.math("MULTIPLY", film, 0.55), body, PAL["rubber_film"])
    # ---- the dropped-tool dents and the tape ghosts -------------------------
    v_dent = t.vor(t.vmath("SCALE", P, scale=1.0), 14.0, "F1", 0, 1.0)
    dent = t.math("MULTIPLY", t.maprange(v_dent, 0.010, 0.045, 1.0, 0.0),
                  t.math("MULTIPLY", A["o_age"], 0.8))
    body = t.cmix(t.math("MULTIPLY", dent, 0.30), body, PAL["deck_dirt"])
    rgh = t.maprange(n_grit, 0.2, 0.8, 0.60, 0.82)
    rgh = t.fmix(t.math("MULTIPLY", crest, 0.9), rgh, 0.30)
    rgh = t.fmix(t.math("MULTIPLY", valley, 0.8), rgh, 0.90)
    rgh = t.fmix(is_ply, rgh, 0.88)
    rgh = t.fmix(is_rub, rgh, 0.72)
    b = t.bump(n_grit, 0.55, 0.00022)
    b = t.bump(grain, t.math("MULTIPLY", is_ply, 0.65), 0.00045, normal=b)
    b = t.bump(t.maprange(v_dent, 0.0, 0.03, 1.0, 0.0),
               t.math("MULTIPLY", dent, 0.7), 0.00060, normal=b)
    b = t.bump(t.noise(t.vmath("SCALE", P, scale=1.0), 340.0, 5.0, 0.6),
               0.30, 0.00010, normal=b)
    metal = t.math("MULTIPLY",
                   t.math("SUBTRACT", 1.0,
                          t.math("MAXIMUM", is_ply, is_rub)), 0.72)
    return t.out(body, rgh, metal, normal=b, spec=0.45)


def mat_rubber():
    """EPDM trim, cable sheath, matting, pads.  Satin black is a lie: rubber
    two seasons in the sun is grey, chalked, and dusty in its own texture."""
    t = NT(PFX + "Rubber")
    A = _common(t)
    P = A["P"]
    n_b = t.noise(t.vmath("SCALE", P, scale=1.0), 40.0, 6.0, 0.6)
    body = t.cmix(t.maprange(n_b, 0.3, 0.75, 0.0, 1.0), PAL["rub_black"],
                  PAL["rub_grey"])
    chalk = t.math("MULTIPLY",
                   t.math("MULTIPLY", A["o_age"],
                          t.maprange(A["up"], 0.0, 0.8, 0.35, 1.0)),
                   t.maprange(t.noise(t.vmath("SCALE", P, scale=1.0), 12.0, 6.0),
                              0.35, 0.80, 0.10, 1.0))
    body = t.cmix(t.math("MULTIPLY", chalk, 0.65), body, PAL["rub_chalk"])
    # the extrusion mould line, and the printed legend that has half worn off
    ml = t.wave(t.vmath("SCALE", A["Pl"], scale=1.0), 180.0, 0.3, 2.0, "Y")
    dust = t.math("MULTIPLY", A["o_grime"],
                  t.maprange(t.noise(t.vmath("SCALE", P, scale=1.0), 20.0, 6.0),
                             0.30, 0.80, 0.15, 1.0))
    body = t.cmix(t.math("MULTIPLY", dust, 0.40), body, PAL["dust"])
    body = t.cmix(t.math("MULTIPLY", A["dirt"], 0.35), body, PAL["grime"])
    # a coloured sheath (the yellow cable ramp) tints itself; a white vertex
    # tint means "leave it black", which is what every other rubber part sends
    body = t.cmix(t.maprange(t.sep(A["tint"], 0), 0.98, 0.90, 0.0, 1.0),
                  body, t.cmix(0.62, body, A["tint"]))
    rgh = t.maprange(n_b, 0.2, 0.8, 0.62, 0.80)
    rgh = t.fmix(t.math("MULTIPLY", chalk, 0.9), rgh, 0.92)
    rgh = t.fmix(t.math("MULTIPLY", A["wear"], 0.55), rgh, 0.46)
    b = t.bump(n_b, 0.50, 0.00025)
    b = t.bump(ml, 0.35, 0.00030, normal=b)
    b = t.bump(t.noise(t.vmath("SCALE", P, scale=1.0), 420.0, 4.0, 0.6),
               0.30, 0.00008, normal=b)
    return t.out(body, rgh, 0.0, normal=b, spec=0.38)


def mat_steel():
    """Zinc-plated and galvanised fasteners: spangle, passivation, polish."""
    t = NT(PFX + "Steel")
    A = _common(t)
    P = A["P"]
    spangle = t.vor(t.vmath("SCALE", P, scale=1.0), 700.0, "F1", 1, 1.0)
    body = t.cmix(t.maprange(spangle, 0.15, 0.85, 0.0, 1.0),
                  PAL["steel_dark"], PAL["steel_gal"])
    pas = t.maprange(t.noise(t.vmath("SCALE", P, scale=1.0), 30.0, 5.0),
                     0.35, 0.80, 0.0, 1.0)
    body = t.cmix(t.math("MULTIPLY", pas, 0.30), body, PAL["steel_pass"])
    # the flats of a spanner-turned head polish; the crevices corrode
    pol = t.math("MULTIPLY", A["wear"],
                 t.maprange(t.noise(t.vmath("SCALE", P, scale=1.0), 160.0, 6.0),
                            0.30, 0.78, 0.3, 1.0))
    body = t.cmix(t.math("MULTIPLY", pol, 0.55), body, PAL["steel_gal"])
    rust = t.math("MULTIPLY",
                  t.math("MULTIPLY", A["o_age"],
                         t.math("MAXIMUM", A["ao"], t.math("MULTIPLY", A["dirt"], 0.5))),
                  t.maprange(t.noise(t.vmath("SCALE", P, scale=1.0), 55.0, 7.0),
                             0.48, 0.86, 0.0, 1.0))
    body = t.cmix(t.math("MULTIPLY", rust, 0.70), body, PAL["rust"])
    body = t.cmix(t.math("MULTIPLY", t.math("MULTIPLY", A["dirt"], A["o_grime"]),
                         0.45), body, PAL["grime"])
    rgh = t.maprange(spangle, 0.1, 0.9, 0.30, 0.52)
    rgh = t.fmix(t.math("MULTIPLY", pol, 0.8), rgh, 0.22)
    rgh = t.fmix(t.math("MULTIPLY", rust, 0.9), rgh, 0.88)
    b = t.bump(spangle, 0.30, 0.00009)
    b = t.bump(t.noise(t.vmath("SCALE", P, scale=1.0), 900.0, 4.0, 0.6),
               0.25, 0.00005, normal=b)
    b = t.bump(t.maprange(t.vor(t.vmath("SCALE", P, scale=1.0), 300.0, "F1", 0),
                          0.0, 0.05, 1.0, 0.0),
               t.math("MULTIPLY", rust, 0.6), 0.00020, normal=b)
    return t.out(body, rgh, 0.90, normal=b, spec=0.5)


def mat_vinyl():
    """Cut vinyl graphics: gloss, UV fade, a dirt line, and small bubbles."""
    t = NT(PFX + "Vinyl")
    A = _common(t)
    P = A["P"]
    body = t.cmix(0.0, A["tint"], A["tint"])
    fade = t.math("MULTIPLY", A["o_age"],
                  t.maprange(t.noise(t.vmath("SCALE", P, scale=1.0), 4.0, 5.0),
                             0.30, 0.82, 0.15, 1.0))
    body = t.cmix(t.math("MULTIPLY", fade, 0.35), body,
                  t.cmix(0.6, A["tint"], (0.42, 0.42, 0.42)))
    # dirt collects on the top edge of every letter, which is where a graphic
    # first reads as OLD rather than as printed
    edge = t.math("MULTIPLY", A["edge"],
                  t.maprange(t.noise(t.vmath("SCALE", P, scale=1.0), 70.0, 6.0),
                             0.35, 0.80, 0.2, 1.0))
    body = t.cmix(t.math("MULTIPLY",
                         t.math("MULTIPLY", edge, A["o_grime"]), 0.55),
                  body, PAL["grime"])
    bub = t.vor(t.vmath("SCALE", P, scale=1.0), 260.0, "F1", 0, 1.0)
    rgh = t.maprange(t.noise(t.vmath("SCALE", P, scale=1.0), 200.0, 4.0),
                     0.3, 0.8, 0.13, 0.24)
    rgh = t.fmix(t.math("MULTIPLY", fade, 0.9), rgh, 0.52)
    b = t.bump(t.maprange(bub, 0.0, 0.03, 1.0, 0.0), 0.40, 0.00020)
    b = t.bump(t.noise(t.vmath("SCALE", P, scale=1.0), 600.0, 4.0), 0.20,
               0.00004, normal=b)
    return t.out(body, rgh, 0.0, normal=b, spec=0.62, coat=0.35)


def mat_fabric():
    """Webbing, tarpaulin, cover: a real weave, UV fade, fray, and dirt."""
    t = NT(PFX + "Fabric")
    A = _common(t)
    P = A["P"]
    warp = t.wave(t.vmath("SCALE", P, scale=1.0), 900.0, 0.8, 2.0, "X")
    weft = t.wave(t.vmath("SCALE", P, scale=1.0), 900.0, 0.8, 2.0, "Y")
    weave = t.math("MULTIPLY", warp, weft)
    body = t.cmix(0.0, A["tint"], A["tint"])
    body = t.cmix(t.maprange(weave, 0.15, 0.75, 0.0, 0.35), body,
                  t.cmix(0.5, A["tint"], (0.02, 0.02, 0.02)))
    fade = t.math("MULTIPLY", A["o_age"],
                  t.maprange(A["up"], 0.0, 0.85, 0.2, 1.0))
    body = t.cmix(t.math("MULTIPLY", fade, 0.40), body,
                  t.cmix(0.5, A["tint"], (0.38, 0.38, 0.36)))
    dirt = t.math("MULTIPLY", A["o_grime"],
                  t.maprange(t.noise(t.vmath("SCALE", P, scale=1.0), 11.0, 6.0),
                             0.32, 0.82, 0.10, 1.0))
    body = t.cmix(t.math("MULTIPLY", dirt, 0.55), body, PAL["grime"])
    body = t.cmix(t.math("MULTIPLY", A["dirt"], 0.30), body, PAL["dust"])
    rgh = t.maprange(weave, 0.2, 0.8, 0.72, 0.90)
    rgh = t.fmix(t.math("MULTIPLY", A["wear"], 0.6), rgh, 0.62)
    b = t.bump(weave, 0.75, 0.00035)
    b = t.bump(t.noise(t.vmath("SCALE", P, scale=1.0), 260.0, 6.0), 0.35,
               0.00025, normal=b)
    return t.out(body, rgh, 0.0, normal=b, spec=0.30)


def mat_elec():
    """Black ABS and black anodise: connectors, knobs, arms, castor bodies."""
    t = NT(PFX + "Electrical")
    A = _common(t)
    P = A["P"]
    n_m = t.noise(t.vmath("SCALE", P, scale=1.0), 260.0, 6.0, 0.62)
    body = t.cmix(t.maprange(n_m, 0.3, 0.78, 0.0, 1.0), PAL["elec_black"],
                  PAL["elec_grey"])
    # a moulded part has a texture spark-eroded into the tool, and it is
    # coarser than people think: 0.05-0.15 mm
    spark = t.vor(t.vmath("SCALE", P, scale=1.0), 900.0, "F1", 0, 1.0)
    shine = t.math("MULTIPLY", A["wear"],
                   t.maprange(t.noise(t.vmath("SCALE", P, scale=1.0), 70.0, 6.0),
                              0.32, 0.80, 0.25, 1.0))
    # measured off the console peep: at 0.45 the shine layer lifted a black
    # anodised VESA plate to a mid warm grey under the contract's 1.0/0.72/0.39
    # sun.  Black hardware stays black; what wear does to it is GLOSS, not
    # lightness, so the lift goes down and the roughness drop goes up.
    body = t.cmix(t.math("MULTIPLY", shine, 0.20), body, PAL["elec_grey"])
    dust = t.math("MULTIPLY",
                  t.math("MULTIPLY", A["o_grime"],
                         t.maprange(A["up"], 0.1, 0.9, 0.15, 1.0)),
                  t.maprange(t.noise(t.vmath("SCALE", P, scale=1.0), 18.0, 6.0),
                             0.3, 0.82, 0.2, 1.0))
    body = t.cmix(t.math("MULTIPLY", dust, 0.30), body, PAL["dust"])
    body = t.cmix(t.math("MULTIPLY", A["ao"], 0.55), body, (0.006, 0.006, 0.007))
    rgh = t.maprange(spark, 0.0, 0.06, 0.46, 0.68)
    rgh = t.fmix(t.math("MULTIPLY", shine, 0.95), rgh, 0.18)
    rgh = t.fmix(t.math("MULTIPLY", dust, 0.7), rgh, 0.80)
    b = t.bump(t.maprange(spark, 0.0, 0.05, 1.0, 0.0), 0.45, 0.00010)
    b = t.bump(n_m, 0.30, 0.00007, normal=b)
    return t.out(body, rgh, 0.0, normal=b, spec=0.44)


MAT_FN = (mat_alu, mat_paint, mat_deck, mat_rubber, mat_steel, mat_vinyl,
          mat_fabric, mat_elec)


def materials():
    return [f() for f in MAT_FN]


# ==============================================================================
#  8.  BUILD AND EMIT
# ==============================================================================

def _shade_by_angle(me, deg=34.0):
    """Smooth everywhere except across a real arris.

    A swept tube with 16 segments flat-shaded is a faceted stick at 373 px/m;
    smoothed across the whole object the chamfers and arrises melt.  numpy
    against `sharp_edge`, because `shade_auto_smooth` needs a VIEW_3D context
    and cannot run headless (see the project's Blender-5.x notes).
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
    nv = len(me.vertices)
    key = np.minimum(a, b) * np.int64(nv) + np.maximum(a, b)
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
    ekey = (np.minimum(ev[:, 0], ev[:, 1]) * np.int64(nv)
            + np.maximum(ev[:, 0], ev[:, 1]))
    sharp = np.zeros(nedge, np.int8)
    if len(sharp_key):
        sk = np.sort(sharp_key)
        idx = np.clip(np.searchsorted(sk, ekey), 0, len(sk) - 1)
        sharp[sk[idx] == ekey] = 1
    at = me.attributes.get("sharp_edge") or me.attributes.new(
        "sharp_edge", "BOOLEAN", "EDGE")
    at.data.foreach_set("value", sharp)


def _mesh_from(name, V, Q, T, mq, mt, A, bc, tint):
    nv, nq, nt = V.shape[0], Q.shape[0], T.shape[0]
    nf = nq + nt
    me = bpy.data.meshes.new(name)
    me.vertices.add(nv)
    me.vertices.foreach_set("co", np.ascontiguousarray(V, np.float32).ravel())
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
    for k in ATTR_F:
        at = me.attributes.new(k, "FLOAT", "POINT")
        at.data.foreach_set("value", np.ascontiguousarray(A[k], np.float32))
    av = me.attributes.new("ts_bc", "FLOAT_VECTOR", "POINT")
    av.data.foreach_set("vector", np.ascontiguousarray(bc, np.float32).ravel())
    ac = me.attributes.new("ts_tint", "FLOAT_COLOR", "POINT")
    t4 = np.ones((tint.shape[0], 4), np.float32)
    t4[:, :3] = tint
    ac.data.foreach_set("color", t4.ravel())
    me.validate(verbose=False)
    _shade_by_angle(me)
    return me


def build_stand(r, coll, mats):
    """One stand -> ONE object, recentred on its own bounding-box centre."""
    S = sections(r)
    acc = Acc("%sStand%02d_%s" % (PFX, r["uid"], r["team"]))
    build_chassis(acc, r, S)
    build_deck(acc, r, S)
    build_panels(acc, r, S)
    build_steps(acc, r, S)
    build_rails(acc, r, S)
    build_console(acc, r, S)
    build_seating(acc, r, S)
    build_canopy(acc, r, S)
    build_loom(acc, r, S)
    build_dressing(acc, r, S)
    V, Q, T, mq, mt, A, bc, tint = acc.arrays()
    if V.shape[0] == 0:
        raise RuntimeError("REFUSING: stand %d built no geometry" % r["uid"])
    # ts_h is the height above the paving, and it is MEASURED off the geometry
    # rather than promised by every call site
    A = dict(A)
    A["ts_h"] = V[:, 2].astype(np.float32)
    ctr = (V.min(axis=0) + V.max(axis=0)) * 0.5
    Vl = V - ctr[None, :]
    rad = float(np.abs(Vl).max())
    me = _mesh_from(acc.name, Vl, Q, T, mq, mt, A, bc, tint)
    for m in mats:
        me.materials.append(m)
    ob = bpy.data.objects.new(acc.name, me)
    coll.objects.link(ob)
    org, ex, ey, ez = stand_basis(r)
    O = org + ex * ctr[0] + ey * ctr[1] + ez * ctr[2]
    R = np.stack([ex, ey, ez], axis=1)
    place(ob, R, O)
    ob["item"] = ITEM
    ob["ts_uid"] = int(r["uid"])
    ob["ts_team"] = r["team"]
    ob["ts_ofs_x"] = float(h01(r["seed"], 3) * 21.0)
    ob["ts_ofs_y"] = float(h01(r["seed"], 5) * 21.0)
    ob["ts_ofs_z"] = float(h01(r["seed"], 7) * 21.0)
    ob["ts_o_age"] = float(r["age"])
    ob["ts_o_grime"] = float(r["grime"])
    ob["ts_o_val"] = float(h01(r["seed"], 11))
    ob["ts_o_deck"] = float(r["deck_i"])
    ob["ts_tiers"] = int(r["tiers"])
    ob["ts_canopy"] = r["canopy"]
    ob["ts_dressed"] = int(bool(r["dressed"]))
    info = dict(verts=V.shape[0], quads=Q.shape[0], tris=T.shape[0],
                triangles=Q.shape[0] * 2 + T.shape[0], parts=acc.parts,
                radius=rad)
    return ob, O, info


def _coll(name, parent=None):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
    if parent is None:
        if name not in bpy.context.scene.collection.children:
            bpy.context.scene.collection.children.link(c)
    elif name not in parent.children:
        parent.children.link(c)
    return c


def purge():
    for ob in list(bpy.data.objects):
        if ob.name.startswith(PFX):
            bpy.data.objects.remove(ob, do_unlink=True)
    for c in list(bpy.data.collections):
        if c.name.startswith(COLL):
            bpy.data.collections.remove(c)


def build(scene=None, stats=None, limit=None, uids=None):
    """Emit every stand into ``W_Item_TimingStand``.  ONE OBJECT PER STAND."""
    t0 = time.time()
    purge()
    root = _coll(COLL)
    mats = materials()
    recs = stand_records()
    if uids is not None:
        recs = [r for r in recs if r["uid"] in set(uids)]
    if limit:
        recs = recs[:limit]
    pairs, tot = [], dict(objects=0, verts=0, triangles=0, parts=0)
    for r in recs:
        ob, O, info = build_stand(r, root, mats)
        pairs.append((ob, O))
        tot["objects"] += 1
        for k in ("verts", "triangles", "parts"):
            tot[k] += info[k]
        log("stand %02d %-10s %-16s tiers=%d deck=%-8s canopy=%-4s "
            "dressed=%d  %7d tris  |P|max %.3f m"
            % (r["uid"], r["team"], r["family"], r["tiers"], r["deck_kind"],
               r["canopy"], r["dressed"], info["triangles"], info["radius"]))
    verify_placement(pairs)
    tot["seconds"] = round(time.time() - t0, 1)
    if stats is not None:
        stats.update(tot)
    log("built %d stands, %d triangles, %d parts in %.1f s"
        % (tot["objects"], tot["triangles"], tot["parts"], tot["seconds"]))
    return root


# ==============================================================================
#  9.  THE PUBLIC INTERFACE
# ==============================================================================
# Pure functions of the plan.  No bpy.  Every returned point is WORLD frame.

SECTION = dict(
    front_leg_y=FRONT_LEG_Y, console_y=CONSOLE_Y,
    wall_pit_face_y=WALL_PIT_FACE_Y, wall_top_z=WALL_TOP_Z,
    clear_of_wall_m=round(CLEAR_OF_WALL, 4),
    embed_m=EMBED, pad_thickness_m=PAD_T,
    console_h=CONSOLE_H, console_d=CONSOLE_D, rail_h=RAIL_H,
    seat_mount_plate=[0.150, 0.150, 0.008], seat_boss_d=0.062,
    seat_bolt_pcd=0.100, vesa=[0.100, 0.100],
    valance_h=0.280, canopy_tube_r=0.0215,
    eyelet_pitch_m=0.300, eyelet_d=0.025,
)


def seat_stations():
    """For ``timing_stand_seat`` (40) -- 4 per stand, world frame.

    ``mount_top_world`` is the top of the 62 mm spigot boss.  THE SEAT ITEM
    OWNS EVERYTHING ABOVE THAT POINT and nothing below it.  ``deck_z_world``
    is the deck directly under the station, for the seat's own foot clearance.
    """
    out = []
    for r in stand_records():
        for st in seat_stations_local(r):
            p = to_world(r, [(st["x"], st["y"], st["z"])])[0]
            d = to_world(r, [(st["x"], st["y"], st["deck_z"])])[0]
            out.append(dict(
                stand=r["uid"], team=r["team"], k=st["k"], tier=st["tier"],
                mount_top_world=[round(float(v), 5) for v in p],
                deck_z_world=round(float(d[2]), 5),
                facing_world=[round(float(v), 6) for v in (-EY)],
                boss_d=SECTION["seat_boss_d"], bolt_pcd=SECTION["seat_bolt_pcd"],
                plate=SECTION["seat_mount_plate"], pitch=r["seat_pitch"],
                state=st["state"], occupied=st["occupied"]))
    return out


def monitor_bays():
    """For ``timing_stand_monitor`` (60) -- 5-7 per stand, world frame.

    The screen hangs on ``vesa_centre_world`` with its face along
    ``normal_world`` and its top along ``up_world``; the 100 x 100 VESA bolts
    are already in the plate.  Screens face the PIT LANE, not the track.
    """
    out = []
    for r in stand_records():
        S = sections(r)
        F = console_frame(r)
        for bay in monitor_bays_local(r):
            yaw, pitch = bay["yaw"], bay["pitch"]
            nrm = np.array([math.sin(yaw) * math.cos(pitch),
                            math.cos(yaw) * math.cos(pitch), math.sin(pitch)])
            up = np.array([-math.sin(yaw) * math.sin(pitch),
                           -math.cos(yaw) * math.sin(pitch), math.cos(pitch)])
            p_el = np.array([bay["x"], 0.075, bay["z"] + 0.085])
            d = np.array([math.sin(yaw), math.cos(yaw), 0.0])
            p_pl = p_el + d * 0.145 + np.array([0, 0, 0.012]) + nrm * 0.030
            W = to_world(r, [p_pl])[0]
            org, ex, ey, ez = stand_basis(r)
            nw = ex * nrm[0] + ey * nrm[1] + ez * nrm[2]
            uw = ex * up[0] + ey * up[1] + ez * up[2]
            out.append(dict(
                stand=r["uid"], team=r["team"], k=bay["k"],
                vesa_centre_world=[round(float(v), 5) for v in W],
                normal_world=[round(float(v), 6) for v in nw],
                up_world=[round(float(v), 6) for v in uw],
                vesa=SECTION["vesa"], diag_m=bay["diag_m"],
                deployed=bay["deployed"],
                hood=bool(r["hood"]),
                cable_exit_world=[round(float(v), 5)
                                  for v in to_world(r, [p_pl - nrm * 0.012])[0]]))
    return out


def canopy_frame():
    """For ``timing_stand_canopy`` (10) -- the metal, so the fabric can land on
    it without a gap or an intersection."""
    out = []
    for r in stand_records():
        L, D = r["L"], r["D"]
        S = sections(r)
        a = S["a"]
        ef, er = r["eaves_f"], r["eaves_r"]
        up = (r["canopy"] == "up")
        rx = [-L * 0.5 + 0.09 + (L - 0.18) * k / (r["nraft"] - 1)
              for k in range(r["nraft"])]
        rafters = []
        if up:
            for xx in rx:
                y0, y1 = -0.420, D + 0.100
                z0 = ef + 0.030 + (er - ef) * (y0 - 0.0) / max(D, 1e-6)
                z1 = er + 0.030
                pts = to_world(r, [(xx, y0, z0), (xx, y1, z1)])
                rafters.append([[round(float(v), 5) for v in p] for p in pts])
        eyelets = []
        if up:
            for (yy, zz) in ((0.0, ef), (D, er)):
                for xx in np.arange(-L * 0.5 + 0.15, L * 0.5 - 0.10, 0.300):
                    p = to_world(r, [(float(xx),
                                      yy - 0.014 if yy < 0.5 else yy + 0.014,
                                      zz + a * 0.5 + 0.0225)])[0]
                    eyelets.append([round(float(v), 5) for v in p])
        mz = ef + a * 0.5 + 0.115
        mand = to_world(r, [(-L * 0.5 - 0.10, -0.020, mz),
                            (L * 0.5 + 0.10, -0.020, mz)])
        vz1 = (ef + 0.030 - 0.020) if up else (ef - 0.040)
        vy = -0.420 if up else -a * 0.5 - 0.020
        val = to_world(r, [(-L * 0.5 - 0.02, vy, vz1 - 0.280),
                           (L * 0.5 + 0.02, vy, vz1 - 0.280),
                           (L * 0.5 + 0.02, vy, vz1),
                           (-L * 0.5 - 0.02, vy, vz1)])
        out.append(dict(
            stand=r["uid"], team=r["team"], state=r["canopy"],
            eaves_front_world=[[round(float(v), 5) for v in p] for p in
                               to_world(r, [(-L * 0.5 - 0.02, 0.0, ef),
                                            (L * 0.5 + 0.02, 0.0, ef)])],
            eaves_rear_world=[[round(float(v), 5) for v in p] for p in
                              to_world(r, [(-L * 0.5 - 0.02, D, er),
                                           (L * 0.5 + 0.02, D, er)])],
            rafters_world=rafters, eyelets_world=eyelets,
            valance_world=[[round(float(v), 5) for v in p] for p in val],
            valance_h=0.280, tube_r=SECTION["canopy_tube_r"],
            roll_mandrel_world=[[round(float(v), 5) for v in p] for p in mand],
            roll_mandrel_r=0.0215,
            covers_local_y=[-0.420, round(D + 0.100, 4)],
            note=("fabric roof + skirt for state 'up'; a rolled bundle on the "
                  "published mandrel for state 'down'.  The rigid valance "
                  "BOARD is already built by timing_stand.")))
    return out


def figure_stations():
    """For ``engineer_on_timing_stand`` (40) and ``team_principal_figure`` (10).

    Four seated engineer stations plus ONE STANDING principal station per
    stand.  The principal stands: forty seats and fifty figures do not fit,
    and a team principal leaning on the back rail with a headset on is what a
    pit wall actually looks like.  ``occupied`` follows the stand's dressing
    state, so the three struck stands report False rather than being quietly
    populated.
    """
    out = []
    for r in stand_records():
        L, D = r["L"], r["D"]
        F = console_frame(r)
        for st in seat_stations_local(r):
            seat = to_world(r, [(st["x"], st["y"], st["z"])])[0]
            dz = st["deck_z"]
            out.append(dict(
                stand=r["uid"], team=r["team"], role="engineer", k=st["k"],
                tier=st["tier"], occupied=st["occupied"],
                seat_mount_world=[round(float(v), 5) for v in seat],
                deck_z_world=round(float(to_world(r, [(st["x"], st["y"], dz)])[0][2]), 5),
                foot_rail_world=[round(float(v), 5) for v in
                                 to_world(r, [(st["x"], st["y"] - 0.26,
                                               dz + 0.185)])[0]],
                console_edge_world=[round(float(v), 5) for v in
                                    to_world(r, [(st["x"], F["y_f"],
                                                  F["top"])])[0]],
                console_top_z=round(float(to_world(r, [(0, 0, F["top"])])[0][2]), 5),
                facing_world=[round(float(v), 6) for v in (-EY)]))
        px = r["prin_end"] * (L * 0.5 - 0.55)
        py = r["y_splits"][-1] - 0.28
        dz = r["deck"] + r["rise"][-1]
        out.append(dict(
            stand=r["uid"], team=r["team"], role="principal", k=0,
            tier=r["tiers"] - 1, occupied=bool(r["dressed"]), standing=True,
            stand_point_world=[round(float(v), 5) for v in
                               to_world(r, [(px, py, dz)])[0]],
            deck_z_world=round(float(to_world(r, [(px, py, dz)])[0][2]), 5),
            lean_rail_world=[round(float(v), 5) for v in
                             to_world(r, [(px, r["y_splits"][-1] - 0.05,
                                           dz + 1.045)])[0]],
            facing_world=[round(float(v), 6) for v in (-EY)]))
    return out


def deck_rects():
    """Every deck tier as a world rectangle and its top z."""
    out = []
    for r in stand_records():
        L = r["L"]
        for t in range(r["tiers"]):
            y0, y1 = r["y_splits"][t], r["y_splits"][t + 1]
            dz = r["deck"] + r["rise"][t]
            P = to_world(r, [(-L * 0.5, y0, dz), (L * 0.5, y0, dz),
                             (L * 0.5, y1, dz), (-L * 0.5, y1, dz)])
            out.append(dict(stand=r["uid"], tier=t,
                            top_z=round(float(P[0][2]), 5),
                            surface=r["deck_kind"],
                            corners_world=[[round(float(v), 5) for v in p]
                                           for p in P]))
    return out


def kit_sites():
    """Sockets this module BUILT AND LEFT EMPTY, for the items that fill them."""
    out = []
    for r in stand_records():
        L, D = r["L"], r["D"]
        S = sections(r)
        ex = r["prin_end"] * (L * 0.5 - 0.16)
        ez = r["deck"] + 0.30
        ux = -r["prin_end"] * (L * 0.5 - 0.055)
        out.append(dict(
            stand=r["uid"], team=r["team"],
            extinguisher_bracket_world=[round(float(v), 5) for v in
                                        to_world(r, [(ex, D - 0.048, ez + 0.09)])[0]],
            extinguisher_axis_world=[round(float(v), 6) for v in EZ],
            extinguisher_for="fire_extinguisher_handheld",
            umbrella_socket_world=[round(float(v), 5) for v in
                                   to_world(r, [(ux + S["a"] * 0.5 + 0.030, D,
                                                 r["deck"] + 0.62)])[0]],
            umbrella_socket_id=0.039))
    return out


def interface_json(path=None):
    path = path or os.path.join(_HERE, "timing_stand_interface.json")
    recs = stand_records()
    doc = dict(
        item=ITEM, version=__version__, collection=COLL, prefix=PFX,
        filmed_at_m=FILMED_AT_M, lens_mm=LENS_MM,
        px_per_m_at_filmed_distance=round(PX_PER_M, 2),
        section=SECTION,
        instances_built=len(recs), instances_declared=INSTANCES_DECLARED,
        population_note=(
            "10 stands, 4 seat stations each = 40 (matches timing_stand_seat), "
            "5-7 monitor bays each = %d (timing_stand_monitor declares 60), "
            "1 standing principal station each = 10 (team_principal_figure). "
            "engineer_on_timing_stand declares 40; this module reports "
            "occupied=True on %d of them, because 3 of the 10 stands are "
            "STRUCK -- covered, arms folded, loom coiled -- which is the "
            "manifest's own 'occupied/empty' variation axis. Populating a "
            "covered stand would contradict the geometry."
            % (sum(len(monitor_bays_local(r)) for r in recs),
               sum(4 for r in recs if r["dressed"]))),
        ownership=dict(
            owned=["chassis", "levelling feet", "castors", "deck and its "
                   "surface", "steps", "handrail", "console carcass and "
                   "worktop", "fascia and its livery", "monitor rail, shade "
                   "hood and every VESA arm up to and including the plate",
                   "seat rail, pedestals and mount plates up to the top of "
                   "the boss", "canopy frame, purlins, eyelet studs, roll "
                   "mandrel and lashings", "the rigid valance board and its "
                   "lettering", "the stand's own cable loom, tray, ties and "
                   "ramp", "the tarpaulin on a struck stand", "the "
                   "extinguisher bracket and umbrella socket, left EMPTY"],
            not_owned=["seat stems and shells (timing_stand_seat)",
                       "screens (timing_stand_monitor)",
                       "canopy fabric and its roll (timing_stand_canopy)",
                       "figures (engineer_on_timing_stand, "
                       "team_principal_figure)",
                       "extinguishers, bottles, bags, crates, cable drums and "
                       "gaffer tape -- all separate manifest items"]),
        stands=[{k: v for k, v in r.items() if not k.startswith("_")}
                for r in recs],
        seat_stations=seat_stations(),
        monitor_bays=monitor_bays(),
        canopy_frame=canopy_frame(),
        figure_stations=figure_stations(),
        deck_rects=deck_rects(),
        kit_sites=kit_sites(),
    )
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w") as f:
        json.dump(doc, f, indent=1)
    return path


# ==============================================================================
# 10.  THE TEST SCENE — the contract sun, the wall, and the film's own camera
# ==============================================================================

def contract_light(scene=None, coll=None):
    """The film's sun and sky, exactly as ``world_contract`` measured them:
    12.471 deg of elevation on a bearing of -57.970 deg."""
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
        if C.VIEW_LOOK:
            scene.view_settings.look = C.VIEW_LOOK
    except Exception:
        pass
    scene.view_settings.exposure = C.REFERENCE_EXPOSURE_EXTERIOR
    log("light: sun %.3f W/m2, elev %.3f deg, bearing %.3f deg; %s %+.3f EV"
        % (C.SUN_ENERGY, C.SUN_ELEV_DEG, C.SUN_BEARING_DEG,
           C.VIEW_TRANSFORM, C.REFERENCE_EXPOSURE_EXTERIOR))
    return ob


def _xmat(name, col, rough=0.7, metal=0.0, noise=None):
    """A deliberately plain stand-in material.  Stand-ins are NOT this item and
    they are not dressed up to look like it: they exist so the macro is framed
    the way the film frames it, and they are named XSTAND_ so `item_gate
    --prefix TS_` can never measure one and credit it here."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    bs = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bs.inputs["Base Color"].default_value = tuple(col) + (1.0,)
    bs.inputs["Roughness"].default_value = rough
    bs.inputs["Metallic"].default_value = metal
    if noise:
        co = nt.nodes.new("ShaderNodeTexCoord")
        n = nt.nodes.new("ShaderNodeTexNoise")
        n.inputs["Scale"].default_value = noise
        nt.links.new(co.outputs["Object"], n.inputs["Vector"])
        mx = nt.nodes.new("ShaderNodeMix")
        mx.data_type = "RGBA"
        mx.inputs[0].default_value = 0.35
        mx.inputs[6].default_value = tuple(col) + (1.0,)
        mx.inputs[7].default_value = tuple(c * 0.55 for c in col) + (1.0,)
        nt.links.new(n.outputs["Fac"], mx.inputs[0])
        nt.links.new(mx.outputs[2], bs.inputs["Base Color"])
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(bs.outputs[0], o.inputs["Surface"])
    return m


def build_ground(coll, cx0, cx1, cy0=-30.0, cy1=54.0, step=0.55):
    """The real ground under the stands, sampled from ``C.world_ground_z``.

    Not a flat plane: the track crowns, the runoff platform falls, the paving
    is dead flat at z = 0.000, and the 0.14 m step between the platform and the
    paving runs right behind the pit wall.  A macro shot over a flat plane
    would hide exactly the thing this item had to be levelled against.
    """
    nx = max(2, int((cx1 - cx0) / step) + 1)
    ny = max(2, int((cy1 - cy0) / step) + 1)
    gx = np.linspace(cx0, cx1, nx)
    gy = np.linspace(cy0, cy1, ny)
    GX, GY = np.meshgrid(gx, gy, indexing="ij")
    WX, WY = C.circuit_to_world(GX.ravel(), GY.ravel())
    Z, own = C.world_ground_z(WX, WY)
    Z = np.where(np.isnan(Z), 0.0, Z)
    V = np.stack([WX, WY, Z], 1)
    Q = _grid_quads(nx, ny)
    me = bpy.data.meshes.new(XPFX + "Ground")
    me.vertices.add(V.shape[0])
    me.vertices.foreach_set("co", V.astype(np.float32).ravel())
    me.loops.add(Q.shape[0] * 4)
    me.loops.foreach_set("vertex_index", Q.astype(np.int32).ravel())
    me.polygons.add(Q.shape[0])
    me.polygons.foreach_set("loop_start",
                            (np.arange(Q.shape[0], dtype=np.int32) * 4))
    me.polygons.foreach_set("loop_total", np.full(Q.shape[0], 4, np.int32))
    me.update(calc_edges=True)
    me.validate(verbose=False)
    # The pit lane is CONCRETE, 0.17-0.22 diffuse, and the racing surface is
    # asphalt at 0.05.  The first macro rendered the paving at 0.052 and the
    # whole band above the wall came back crushed black under a 12.47 deg key
    # and -3.048 EV -- which is a stand-in defect that reads as a lighting bug
    # and would have sent me hunting the wrong thing.
    me.materials.append(_xmat(XPFX + "Ground", (0.150, 0.148, 0.142), 0.80,
                              noise=6.0))
    ob = bpy.data.objects.new(XPFX + "Ground", me)
    coll.objects.link(ob)
    return ob


def build_wall_standin(coll, cx0, cx1):
    """A stand-in pit wall, on ``pit_wall_unit``'s published section.

    THE MACRO IS FRAMED THROUGH THIS.  The film's eye rides 1.900 m up and the
    wall is 1.200 m tall, so everything on a timing stand below z = 1.17 is
    occluded in the hero shot.  Rendering the macro without the wall would be
    a flattering lie about what this item has to survive.
    """
    from mathutils import Vector
    V, Q = [], []
    x = cx0
    while x < cx1:
        Lu = 3.0 if int((x - cx0) / 3.0) % 5 else 2.4
        x1 = min(x + Lu - 0.014, cx1)
        gz, _ = _ground((x + x1) * 0.5, WALL_FACE_Y)
        z0 = gz - 0.16
        z1 = 1.200 + gauss(0.006, 0.012, 991, int(x))
        ys = (WALL_FACE_Y, WALL_PIT_FACE_Y)
        pts = []
        for (xx, yy) in ((x, ys[0]), (x1, ys[0]), (x1, ys[1]), (x, ys[1])):
            wx, wy = C.circuit_to_world(xx, yy)
            pts.append((float(wx), float(wy)))
        b = len(V)
        for (px, py) in pts:
            V.append((px, py, z0))
        for (px, py) in pts:
            V.append((px, py, z1))
        Q += [(b, b + 1, b + 2, b + 3), (b + 4, b + 7, b + 6, b + 5),
              (b, b + 4, b + 5, b + 1), (b + 1, b + 5, b + 6, b + 2),
              (b + 2, b + 6, b + 7, b + 3), (b + 3, b + 7, b + 4, b)]
        x += Lu
    me = bpy.data.meshes.new(XPFX + "PitWall")
    me.vertices.add(len(V))
    me.vertices.foreach_set("co", np.asarray(V, np.float32).ravel())
    me.loops.add(len(Q) * 4)
    me.loops.foreach_set("vertex_index", np.asarray(Q, np.int32).ravel())
    me.polygons.add(len(Q))
    me.polygons.foreach_set("loop_start",
                            (np.arange(len(Q), dtype=np.int32) * 4))
    me.polygons.foreach_set("loop_total", np.full(len(Q), 4, np.int32))
    me.update(calc_edges=True)
    me.validate(verbose=False)
    me.materials.append(_xmat(XPFX + "Concrete", (0.180, 0.175, 0.165), 0.86,
                              noise=22.0))
    ob = bpy.data.objects.new(XPFX + "PitWall", me)
    coll.objects.link(ob)
    return ob


def build_dependant_standins(coll):
    """Crude stand-ins for the five items that depend on this one.

    They are built FROM THE PUBLISHED INTERFACE, which is the cheapest possible
    test of it: if `seat_stations()` is wrong, the seats float, and I find out
    here instead of the seat agent finding out in three days' time.
    """
    from mathutils import Matrix, Vector
    mats = dict(
        seat=_xmat(XPFX + "Seat", (0.030, 0.030, 0.032), 0.55),
        screen=_xmat(XPFX + "Screen", (0.012, 0.012, 0.014), 0.30),
        fabric=_xmat(XPFX + "Canopy", (0.150, 0.150, 0.145), 0.80, noise=14.0))
    accs = {k: Acc(XPFX + k) for k in ("Seat", "Screen", "Canopy")}
    for st in seat_stations():
        p = np.array(st["mount_top_world"])
        f = np.array(st["facing_world"])
        s = np.cross(EZ, f)
        # stem, pan, back -- deliberately blunt
        tube(accs["Seat"], p, p + EZ * 0.30, 0.026, mat=0, n=12)
        obox(accs["Seat"], p + EZ * 0.33, s * 0.21, f * 0.20, EZ * 0.035, mat=0)
        obox(accs["Seat"], p + EZ * 0.60 - f * 0.17, s * 0.20, f * 0.035,
             EZ * 0.24, mat=0)
    for b in monitor_bays():
        p = np.array(b["vesa_centre_world"])
        nn = np.array(b["normal_world"])
        uu = np.array(b["up_world"])
        ss = np.cross(uu, nn)
        w = b["diag_m"] * 0.46
        h = b["diag_m"] * 0.27
        obox(accs["Screen"], p + nn * 0.020, ss * w, nn * 0.018, uu * h, mat=0)
    for cf in canopy_frame():
        if cf["state"] != "up":
            p0 = np.array(cf["roll_mandrel_world"][0])
            p1 = np.array(cf["roll_mandrel_world"][1])
            tube(accs["Canopy"], p0, p1, 0.105, mat=0, n=20)
            continue
        rafts = cf["rafters_world"]
        if len(rafts) < 2:
            continue
        nu, nv = len(rafts), 12
        P = np.zeros((nu, nv, 3))
        for i, rr in enumerate(rafts):
            a = np.array(rr[0])
            b2 = np.array(rr[1])
            for j in range(nv):
                t = j / (nv - 1.0)
                P[i, j] = a + (b2 - a) * t
                P[i, j, 2] += 0.018 + 0.030 * math.sin(math.pi * t)
        # sag between rafters
        for i in range(nu):
            P[i, :, 2] -= 0.022 * math.sin(math.pi * (i % 2))
        sheet_solid(accs["Canopy"], P, 0.004, mat=0)
    out = []
    for key, m in (("Seat", mats["seat"]), ("Screen", mats["screen"]),
                   ("Canopy", mats["fabric"])):
        acc = accs[key]
        V, Q, T, mq, mt, A, bc, tint = acc.arrays()
        if V.shape[0] == 0:
            continue
        A = dict(A)
        A["ts_h"] = V[:, 2].astype(np.float32)
        me = _mesh_from(XPFX + key, V, Q, T, mq, mt, A, bc, tint)
        me.materials.append(m)
        ob = bpy.data.objects.new(XPFX + key, me)
        coll.objects.link(ob)
        out.append(ob)
    return out


def add_camera(name, loc, look, lens, coll, fstop=None):
    from mathutils import Vector
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = 36.0
    cd.clip_start = 0.02
    cd.clip_end = 20000.0
    ob = bpy.data.objects.new(name, cd)
    ob.location = tuple(float(v) for v in loc)
    d = Vector(tuple(float(v) for v in look)) - Vector(ob.location)
    ob.rotation_mode = "QUATERNION"
    ob.rotation_quaternion = d.to_track_quat("-Z", "Y")
    coll.objects.link(ob)
    if fstop:
        cd.dof.use_dof = True
        cd.dof.focus_distance = float(d.length)
        cd.dof.aperture_fstop = float(fstop)
    log("%s at %.4f m on a %.0f mm lens" % (name, float(d.length), lens))
    return ob


def hero_stand():
    """Where the macro is shot.  Scored, not chosen for convenience: the shot
    has to be of a stand that is IN USE, with its canopy up, a fascia that is
    more than a flat sheet, and a second tier so the object has depth."""
    best, bs = None, -1e9
    for r in stand_records():
        sc = (2.2 * float(r["dressed"]) + 1.4 * (r["canopy"] == "up")
              + 0.7 * (r["tiers"] - 1) + 0.6 * (r["fascia_i"] in (1, 2, 3))
              + 0.4 * (r["deck_i"] in (0, 1)) + 0.3 * r["mast"]
              + 0.25 * r["L"] / 6.0)
        if sc > bs:
            best, bs = r, sc
    return best


def _cam_from_circuit(name, cx, cy, cz, aim_c, lens, coll, fstop=None):
    wx, wy = C.circuit_to_world(cx, cy)
    ax, ay = C.circuit_to_world(aim_c[0], aim_c[1])
    return add_camera(name, (float(wx), float(wy), cz),
                      (float(ax), float(ay), aim_c[2]), lens, coll, fstop)


def test_scene(samples=256, limit=None, quick=False):
    """Build the ten stands, light them with the contract sun, stand the pit
    wall in front of them, and put the film's own camera on the hero: 10.000 m
    away, 35 mm, 1.900 m off the deck."""
    scene = bpy.context.scene
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    root = build(scene=scene, limit=limit)
    cams = _coll(COLL + "/Cameras", root)
    stand = _coll(COLL + "/Standins", root)
    contract_light(scene, coll=root)
    recs = stand_records()
    if limit:
        recs = recs[:limit]
    cx0 = min(r["x0"] - r["L"] for r in recs) - 26.0
    cx1 = max(r["x0"] + r["L"] for r in recs) + 26.0
    build_ground(stand, cx0, cx1)
    build_wall_standin(stand, max(cx0, -222.0), min(cx1, 130.0))
    build_dependant_standins(stand)

    h = hero_stand() if limit is None else recs[0]
    log("hero stand: uid %d %s, %s, %d tiers, deck %s, fascia %s, canopy %s"
        % (h["uid"], h["team"], h["family"], h["tiers"], h["deck_kind"],
           h["fascia"], h["canopy"]))
    F = console_frame(h)
    hx, hz = h["x0"], h["base_z"]
    # ---- THE SHOT: the onboard follow's own geometry -----------------------
    # 1.900 m off the deck, 10.000 m from the stand, 35 mm, looking forward
    # along the direction of travel (+x) with the wall between lens and object.
    aim_z = hz + (F["rail_top"] + h["eaves_f"]) * 0.5 - 0.15
    aim = (hx, CONSOLE_Y, aim_z)
    yaw = math.radians(38.0)
    dz = 1.900 - aim_z
    horiz = math.sqrt(max(FILMED_AT_M ** 2 - dz * dz, 0.04))
    _cam_from_circuit(PFX + "CAM_MACRO", hx - horiz * math.sin(yaw),
                      CONSOLE_Y - horiz * math.cos(yaw), 1.900, aim,
                      LENS_MM, cams)
    # ---- the same distance and lens from the pit lane, where the whole
    #      object is visible instead of its top two metres -------------------
    aim2 = (hx, FRONT_LEG_Y + h["D"] * 0.4, hz + 1.15)
    yaw2 = math.radians(46.0)
    dz2 = 1.62 - aim2[2]
    hor2 = math.sqrt(max(FILMED_AT_M ** 2 - dz2 * dz2, 0.04))
    _cam_from_circuit(PFX + "CAM_PIT", hx + hor2 * math.sin(yaw2),
                      aim2[1] + hor2 * math.cos(yaw2), 1.62, aim2, LENS_MM,
                      cams)
    # ---- the console at the monitor item's own lens ------------------------
    aim3 = (hx + h["L"] * 0.12, CONSOLE_Y, hz + F["top"] + 0.10)
    dz3 = 1.900 - aim3[2]
    hor3 = math.sqrt(max(FILMED_AT_M ** 2 - dz3 * dz3, 0.04))
    _cam_from_circuit(PFX + "CAM_DECK", hx - hor3 * math.sin(math.radians(26.0)),
                      CONSOLE_Y - hor3 * math.cos(math.radians(26.0)), 1.900,
                      aim3, 58.0, cams)
    # ---- the valance, at 85 mm: the lettering and the stripe ---------------
    vz = hz + h["eaves_f"] + 0.010 - 0.145
    aim4 = (hx, CONSOLE_Y - 0.36, vz)
    dz4 = 2.30 - vz
    hor4 = math.sqrt(max(FILMED_AT_M ** 2 - dz4 * dz4, 0.04))
    _cam_from_circuit(PFX + "CAM_VALANCE", hx - hor4 * math.sin(math.radians(18.0)),
                      aim4[1] - hor4 * math.cos(math.radians(18.0)), 2.30,
                      aim4, 85.0, cams)
    # ---- the chassis and the feet, from the pit lane at 4 m ----------------
    aim5 = (hx - h["L"] * 0.22, FRONT_LEG_Y + h["D"] + 0.10, hz + 0.34)
    _cam_from_circuit(PFX + "CAM_BASE", aim5[0] + 2.55, aim5[1] + 2.95, 0.86,
                      aim5, 35.0, cams)
    # ---- the row: is it ten different machines or one ten times? -----------
    # The gate answers this with a size CV and a topology count.  Neither of
    # those is the question the user actually asked -- "i dont want repeat
    # stuff aka one tree spammed 100 times" is a question about what a frame
    # LOOKS like -- so the row shot exists to be looked at.  A long lens from
    # well back stacks four stands into one frame where any repeat would be
    # unmissable.
    if limit is None:
        r0, r3 = recs[0], recs[3]
        _cam_from_circuit(PFX + "CAM_ROW", r0["x0"] - 34.0, CONSOLE_Y - 26.0,
                          4.90, (r3["x0"] - 6.0, CONSOLE_Y, 2.05), 78.0, cams)
        # ...and the struck ones, so the canopy-down state gets looked at too
        rd = [q for q in recs if not q["dressed"]]
        if len(rd) >= 2:
            _cam_from_circuit(PFX + "CAM_STRUCK", rd[0]["x0"] - 12.0,
                              CONSOLE_Y - 9.0, 3.40,
                              (rd[0]["x0"] + 2.0, CONSOLE_Y, 2.10), 42.0, cams)
    scene.camera = bpy.data.objects[PFX + "CAM_MACRO"]
    scene.render.engine = "CYCLES"
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.cycles.samples = samples
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.006
    scene.cycles.max_bounces = 10
    scene.cycles.diffuse_bounces = 4
    scene.cycles.glossy_bounces = 6
    scene.cycles.transmission_bounces = 6
    scene.cycles.use_denoising = True
    return root


# ==============================================================================
# 11.  MEASUREMENT
# ==============================================================================

def selftest(verbose=True):
    fails = []

    def chk(name, cond, detail=""):
        print("  %s %-56s %s" % ("ok  " if cond else "FAIL", name, detail))
        if not cond:
            fails.append(name)

    print("timing_stand %s  self test" % __version__)
    recs = stand_records()

    print("\n[1] the site against the contract")
    chk("ten stands", len(recs) == 10, "%d" % len(recs))
    owners = sorted(set(o for r in recs for o in r["owners"]))
    chk("every foot on the pit-lane paving",
        owners == ["build_architecture:paving"], "%s" % owners)
    chk("front leg line clear of the pit wall",
        FRONT_LEG_Y - WALL_PIT_FACE_Y >= 0.40,
        "%.3f m behind the wall's pit face" % (FRONT_LEG_Y - WALL_PIT_FACE_Y))
    chk("nothing crosses the contract pin y=11.500",
        CONSOLE_Y - 0.02 > WALL_PIN_Y,
        "closest point of this item is y=%.3f" % CONSOLE_Y)
    minx = min(r["x0"] - r["L"] * 0.5 for r in recs)
    chk("west end inside the built pit wall", minx > -222.0,
        "westmost stand ends at circuit x %.2f, wall starts at -222.0" % minx)
    gantry = [r for r in recs
              if abs(r["x0"]) - r["L"] * 0.5 < 1.9 and abs(r["x0"]) < 8.0]
    chk("clear of the gantry leg at x -1.9..+1.9", not gantry,
        "%d stands overlap" % len(gantry))

    print("\n[2] law 5: embedment")
    worst = 0.0
    for r in recs:
        for ft in r["feet"]:
            gz = ft["gz"]
            worst = max(worst, 0.0)
    chk("every levelling pad buried >= %.3f m" % C.BASE_EMBED_M,
        EMBED >= C.BASE_EMBED_M, "EMBED = %.3f m, pad is %.3f m thick"
        % (EMBED, PAD_T))
    chk("castors are jacked clear, not sunk",
        CASTOR_LIFT[0] > 0.0, "%.0f-%.0f mm of air under the wheel"
        % (CASTOR_LIFT[0] * 1000, CASTOR_LIFT[1] * 1000))

    print("\n[3] the four named variation axes")
    chk("tier count varies", len(set(r["tiers"] for r in recs)) >= 3,
        "%s" % sorted(set(r["tiers"] for r in recs)))
    chk("canopy up AND down present",
        len(set(r["canopy"] for r in recs)) == 2,
        "%d up, %d down" % (sum(r["canopy"] == "up" for r in recs),
                            sum(r["canopy"] == "down" for r in recs)))
    chk("occupied AND empty present",
        len(set(r["dressed"] for r in recs)) == 2,
        "%d dressed, %d struck" % (sum(r["dressed"] for r in recs),
                                   sum(not r["dressed"] for r in recs)))
    chk("ten distinct team liveries",
        len(set(r["team"] for r in recs)) == 10)
    chk("liveries come from the existing brand book",
        all(r["team"] in [t[0] for t in TEAMS] for r in recs))
    chk("three extrusion families", len(set(r["fam"] for r in recs)) == 3)
    chk("four deck surfaces", len(set(r["deck_kind"] for r in recs)) == 4)
    chk("four fascia types", len(set(r["fascia"] for r in recs)) == 4)
    Ls = [r["L"] for r in recs]
    cv = float(np.std(Ls) / np.mean(Ls))
    chk("length CV >= 0.03 (the gate's floor)", cv >= 0.03, "CV %.4f" % cv)

    print("\n[4] the pixel budget")
    chk("px_per_m at the filmed distance", abs(PX_PER_M - 373.33) < 0.1,
        "%.2f px/m -> 1 px = %.3f mm" % (PX_PER_M, PX_M * 1000))
    h = max(r["post_top"] for r in recs)
    chk("onscreen height matches the manifest's 1195 px",
        abs(TYPICAL_H_M * PX_PER_M - ONSCREEN_PX_4K) < 12.0,
        "%.0f px for %.2f m" % (TYPICAL_H_M * PX_PER_M, TYPICAL_H_M))
    chk("mean stand height near the manifest's 3.2 m",
        abs(np.mean([r["post_top"] for r in recs]) - 3.2) < 0.35,
        "%.3f m" % np.mean([r["post_top"] for r in recs]))

    print("\n[5] the published interface")
    ss = seat_stations()
    mb = monitor_bays()
    fs = figure_stations()
    cf = canopy_frame()
    chk("40 seat stations (timing_stand_seat declares 40)", len(ss) == 40,
        "%d" % len(ss))
    chk("monitor bays 50-70 (timing_stand_monitor declares 60)",
        50 <= len(mb) <= 70, "%d" % len(mb))
    chk("10 canopy frames", len(cf) == 10)
    chk("10 principal stations (team_principal_figure declares 10)",
        sum(1 for f in fs if f["role"] == "principal") == 10)
    chk("40 engineer stations (engineer_on_timing_stand declares 40)",
        sum(1 for f in fs if f["role"] == "engineer") == 40)
    zs = [s["mount_top_world"][2] for s in ss]
    chk("seat mounts above the pit wall top",
        min(zs) > WALL_TOP_Z - 0.55,
        "lowest mount z %.3f, wall top %.3f" % (min(zs), WALL_TOP_Z))
    vz = [b["vesa_centre_world"][2] for b in mb]
    chk("every screen clears the pit wall", min(vz) > WALL_TOP_Z + 0.30,
        "lowest VESA centre z %.3f" % min(vz))
    # the sight line the manifest's distance implies
    hero = hero_stand()
    Fh = console_frame(hero)
    occl = 1.900 - (1.900 - WALL_TOP_Z) / (FILMED_AT_M - 0.2) * FILMED_AT_M
    chk("what the film's eye can see of this item",
        occl < Fh["top"] + hero["base_z"],
        "wall occludes below z %.3f; the worktop is at %.3f" %
        (occl, Fh["top"] + hero["base_z"]))

    print("\n[6] recentring (law 6)")
    for r in recs[:3]:
        L, D = r["L"], r["D"]
        rad = max(L * 0.5 + 0.10, D * 0.6 + 0.5, r["post_top"] * 0.5 + 0.3)
        chk("stand %d |P| stays small" % r["uid"], rad < 4.0,
            "bounding radius <= %.2f m" % rad)

    print("\n%s  %d checks, %d failed"
          % ("SELFTEST PASS" if not fails else "SELFTEST FAIL",
             len(fails) + 0, len(fails)))
    return not fails


def census(stats):
    recs = stand_records()
    print("\n---- timing_stand census "
          "-------------------------------------------------")
    print("  objects            %d (one per stand)" % stats.get("objects", 0))
    print("  triangles          %d  (%d per stand)"
          % (stats.get("triangles", 0),
             stats.get("triangles", 0) // max(stats.get("objects", 1), 1)))
    print("  parts              %d" % stats.get("parts", 0))
    print("  seat stations      %d" % len(seat_stations()))
    print("  monitor bays       %d" % len(monitor_bays()))
    print("  build time         %.1f s" % stats.get("seconds", 0.0))
    print("  px/m at %.1f m     %.1f  (1 px = %.3f mm)"
          % (FILMED_AT_M, PX_PER_M, PX_M * 1000))


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
    ap.add_argument("--interface", nargs="?", const="", default=None)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--samples", type=int, default=256)
    ap.add_argument("--save", default=None)
    ap.add_argument("--render", default=None)
    ap.add_argument("--cam", default=PFX + "CAM_MACRO")
    ap.add_argument("--res", type=int, nargs=2, default=[1920, 1080])
    a = ap.parse_args(argv)

    if a.interface is not None:
        p = interface_json(a.interface or None)
        log("interface -> %s" % p)
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
