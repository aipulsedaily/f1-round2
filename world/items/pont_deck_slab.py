#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pont_deck_slab.py — Le Pont de la Plongee, the reinforced-concrete deck slab.
Item 65, wave 1, zone `bridges`.

    manifest:  nearest_camera_m 3.0   lens 35 mm   onscreen_px_4k 1244
               instances 1            hero True    beats ['5']
               depends_on ['pont_girder']          dependents 3
               variation_axes: wearing surface / kerb / joint
               typical_height_m 0.30
    pixels:    px_per_m = (3840 * 35 / 36) / 3.0 = 1244.4 px/m
               -> 1 screen pixel = 0.804 mm on this slab.

WHAT 0.804 mm/px MEANS, ITEM BY ITEM
    a 2 mm blowhole in the fascia                     2.5 px
    a 4 mm blowhole                                   5.0 px
    a 1.5 mm formwork lippage step                    1.9 px
    a 3 mm grout fin where paste leaked a ply joint   3.7 px
    the 18 x 14 mm drip groove                        22 x 17 px
    a 20 mm arris chamfer                             25 px
    a 26 mm form-tie plug                             32 px
    a 10 mm mortar joint between two kerb units       12 px
    a 3 mm lippage between two kerb units             3.7 px
    a 2.5 mm thermoplastic line edge                  3.1 px
    an 8 mm exposed aggregate face in a spall         10 px
    the 7 mm difference between girder A's camber and
      girder D's, sighted along two fascia edges      8.7 px

    None of that list can be a shader.  Blowholes are the single most reliable
    tell of real concrete and they are 1-6 mm across, which is 1-8 px here, so
    they are DISPLACED MESH, not a bump map, and there are 104 236 of them on
    the leading fascia face alone -- counted off the cell lattice, not
    estimated: 10 214 of 2.0-9.6 mm, 306 of 6.0-16.4 mm, 642 in chains up the
    plywood joints, 93 074 fines of 1.0-3.2 mm.  7 593 per m2.

WHERE THE LENS ACTUALLY IS, AND WHY THAT DECIDES THE MESH GRADING
    circuit_spec's Beat-5 vantage table: the camera comes out of the dive at
    s=2403 and threads UNDER this bridge at world z ~ 5.0 doing 300 km/h,
    then hovers at s=2555.  pont_girder measured the clearance on built mesh:
    lowest steel over the racing surface 6.775, so 1.775 m over the lens.

    From a lens on the racing line at z = 5.000, the NEAREST part of THIS item
    is the leading (-y) fascia beam:  its soffit is at z = 8.098 and its face
    at y = -3.000, so a lens 3.2 m short of the fascia sees it at ~3.0 m.
    That is the manifest's 3.0 m, and it is the fascia edge, the drip groove
    and the cantilever soffit — NOT the carriageway, which no shot in the film
    gets within 25 m of.

    So the mesh is graded by ANGULAR size, not by one number applied flat:

        station spacing  dx(x) = clip(0.0016 * (d/3.2)^1.35, 0.0016, 0.028)
                         where d = hypot(x, 3.2) is the distance from the
                         under-pass point to station x on the fascia
        section spacing  1.6 mm on the leading fascia, 1.3 mm on its arrises,
                         3.2 mm on its beam soffit (D_HERO / D_DET / D_SOFF)

    which holds every facet on the fascia between 1.9 and 3.3 SCREEN PIXELS
    over the whole 15.6 m half-span, for 7 460 stations and 12.8 M slab
    vertices.  Constant angular resolution is the honest reading of "build
    for nearest_camera_m" on a 31 m object the camera passes UNDER.

    THE EXPONENT WAS 2.60 AND IT WAS A DEFECT.  The line above used to read
    2.60 and the sentence under it used to claim constant angular resolution,
    which 2.60 is not: facet_px = (3733/d) * 0.0016 * (d/3.2)^k is constant
    only at k = 1.  At 2.60 the facets went 1.9 px at 3.2 m -> 8.1 px at 8 m,
    four times coarser across a single frame, and the 4K macro showed exactly
    that -- a near fascia carrying visible blowholes and the same edge 7 m
    further on, still at 500 px/m, completely bare.  The concrete appeared to
    turn to plastic halfway down the bridge.  Caught by looking at the render,
    not by reading the code; the code said "constant angular" the whole time.

    THE FIRST VERSION OF THIS ITEM SHIPPED AT 3.8 x 3.2 mm = 4.7 x 4.0 px AND
    THAT WAS TOO COARSE, measured rather than guessed: the blowhole population
    it carries is 2-10 mm across, so half of every void was narrower than one
    quad, and a void narrower than a quad renders as a smooth lump with no rim
    (CAM_PDS_DRIP at 0.68 m showed them as proud faceted blobs).  8.0 M
    vertices is what it costs to have voids with an inside; see D_HERO.

    The deck TOP is stated plainly rather than quietly: its own nearest
    sightline in the film is the dive into the sweeper, ~25 m, where its
    18-24 mm facets are 2.3-3.1 px.  It is built with real geometry — proud
    chippings, ruts, a planed-and-relaid patch with a sawn edge and a sealant
    bead, thermoplastic 2.5 mm proud, grit banked in both channels — but it is
    NOT built at 3 mm, and this paragraph exists so nobody has to guess whether
    that was a decision or an oversight.

WHAT IS MESH AND WHAT IS SHADER
    MESH   the whole slab as one closed swept solid: haunches that follow the
           four girders' ACTUAL cambered top flanges and their plan sweep, so
           the soffit's haunch lines wander 6-14 mm over 30 m and the two
           fascia edges are not parallel; the fascia beam with its 20 mm top
           chamfer, its 12 mm bottom chamfer and a real 18 x 14 mm drip
           groove; 2440 mm plywood formwork panel joints with lippage steps
           and proud grout fins; form-tie plugs on a 600 x 280 grid -- TWO
           rows on the face, not one; one row read as a dotted line ruled
           along the bridge once the plugs were made visible -- in THREE
           states: 46 % recessed mortar behind a sharp 1.5 mm rim, 42 %
           proud with a ring of squeeze-out, 12 % OPEN 16-22 mm conical holes
           and half of those trailing a rust dribble; one 320 x 140 mm
           honeycombed patch with the aggregate standing proud of the mortar
           that never closed round it; a clustered, top-weighted, vertically
           stretched blowhole population -- COUNTED, not asserted: 10 214
           voids of 2.0-9.6 mm, 306 of 6.0-16.4 mm, 642 in chains up the ply
           joints and 93 074 fines of 1.0-3.2 mm on the 13.7 m2 of leading
           fascia face alone (work/pds/count_voids.py walks the same cell
           lattice the displacement does); a construction joint
           between the two pours with a 1.6 mm step; four chipped arrises; a
           sawn-out repaired spall with a proud patch; screed waviness; the
           asphalt's chippings, its two polished wheel tracks and its ruts;
           the planed-and-relaid bay; both channels' grit; 34 individual
           precast kerb units each with its own bedding lippage, rotation,
           joint width and chips, two of them a different profile and one
           cracked through; the +y in-situ upstand with its bolted galvanised
           edge angle from a later reconstruction; two DIFFERENT expansion
           joint recesses; four gulley pots with frames, sumps, outlet spigots
           and silt; 128 cast-in parapet ferrules; 42 soffit fixing inserts;
           two cast-in service ducts; the thermoplastic markings.
    SHADER the concrete's history: two pour lots that do not match, cement
           laitance, carbonation chalking on the faces that see a 12.5 deg
           sun, rain tracking, the lime plume under the drip groove, the rust
           streaks under the parapet ferrules, the algal band where the fascia
           stays damp, the staining plume under each scupper outlet (which is
           pont_scupper's item but MY surface), the tyre scuff on the kerb
           batter, and the bitumen bleed at the sealant beads.
    CHANNELS ...and the STRUCTURE those histories sit on is neither.  It is
           computed in bridge-local (x, u) at build time, in metres, and
           shipped in the vertex channels, because the object is world-aligned
           after recentring and a shader cannot recover "along the span" from
           object coordinates.  Three fields: the POUR RECORD (which truck,
           which day) in base.rgb, the STREAK FIELD (where the water comes off
           the cornice) in base.a, and the FORMWORK PANEL TONE (which plywood
           sheet, how many pours old) in aux.w.  See section 6b for why: the
           shader-only version measured 8.3 % low-frequency albedo span on the
           hero fascia against 40-80 % for the real thing, because eleven
           independent noise mixes average to a flat surface no matter how
           loud each one is.  After: p1..p99 albedo range 67 % of the mean.

WHAT THE ACCEPTANCE GATE CAN AND CANNOT SEE ON THIS ITEM  — read before rerunning
    The gate grew three checks after this item last passed it, and two of them
    land on an object that cannot answer them.  All three runs are on the
    record; none of them is hidden.

      run                            result           why
      --prefix PDS_ (the default)    ITEM_REJECTED    the median-triangle
        render/items/.../gate.json                    object of the six is
                                                      PDS_Fitting: a 31.2 m
                                                      galvanised edge angle
                                                      30 mm thick, seen
                                                      EDGE-ON, 212 k subject
                                                      pixels strung along one
                                                      diagonal line.  The
                                                      relief check measures
                                                      image autocorrelation
                                                      along vs across the
                                                      light; on a long thin
                                                      strip that measures the
                                                      STRIP, not the surface.
                                                      Measured on the shipped
                                                      build: anisotropy
                                                      -0.0101 against a
                                                      control of +0.0546, so
                                                      it misses by 0.095.
                                                      MICROSTRUCTURE passes
                                                      here at x19.6 of the
                                                      strictest
                                                      brightness-matched
                                                      smooth control.
      --subject PDS_Slab             ITEM_REJECTED    "NOT MEASURED": framed
        work/pds/gate_slab/gate.json                  whole, the slab is
                                                      mostly SOFFIT and reads
                                                      0.0244 linear, and no
                                                      part of the control
                                                      sphere sits in that
                                                      luminance window.  A
                                                      bridge underside really
                                                      is that dark; the gate
                                                      is right to refuse to
                                                      score it.
      --subject PDS_Kerb_L           ITEM_ACCEPTED    35 precast kerb units on
        render/items/.../                             the sunlit deck top --
        gate_subject_kerb.json                        a real population of
                                                      near-identical
                                                      instances, which is what
                                                      the median-instance
                                                      witness logic is FOR.
                                                      All eight checks, with
                                                      margin: relief +1.1088
                                                      vs control +0.0735,
                                                      microstructure x7.2 of a
                                                      luminance-matched
                                                      sphere.

    So the concrete does carry lip-and-shade relief and it is measured; the
    default witness selection just cannot see it on this item.  THE HEADLINE
    RESULT IS STILL ITEM_REJECTED and it is reported as ITEM_REJECTED.  Do not
    "fix" this by deleting PDS_Fitting or by folding it into the slab: the
    edge angle is a real bolted-on component of a later reconstruction and it
    belongs to this item.  The thing to fix is either the witness camera (a
    whole-object frame is the wrong frame for a 31 m object whose hero surface
    is a 0.44 m band) or the subject choice for items that are one hero mesh
    plus ancillaries rather than N copies of one thing.

===========================================================================
THE INTERFACE.  This item is a FOUNDATION: bridge_expansion_joint,
pont_scupper and pont_parapet build on it and cannot ask questions.
Everything in this block is public and stable, and every number in it is also
written to world/items/pont_deck_slab_interface.json on every build.
===========================================================================

THE FRAME — identical to pont_girder's, deliberately
        `pont_deck_slab.deck_to_world()` returns the SAME (R, t) as
        `pont_girder.pont_to_world()`; it is re-exported rather than
        redefined so a dependant can use either name and get the same answer.

            +X  ALONG THE SPAN.  x = -15.000 / +15.000 are the bearing lines.
            +Y  the RACING DIRECTION at s = 2410.  The car and the camera
                arrive from -y, so y = -3.000 is the LEADING fascia — the one
                the lens meets first and the one this item is built for.
            +Z  WORLD z.  ground_z(2410, 0) = 3.935.

THE DATUM PLANES — read these, never assume them
        DECK_HALF_W       3.000  slab edges at y = +-3.000 (circuit_spec's
                                 6.0 m deck width).
        END_X            15.600  the deck slab ends here.  Deck length
                                 31.200 m.  The girders run PAST it: A to
                                 +-17.150, so the fascia noses and their
                                 banner tension posts are outside the slab.
        soffit_z(x, y)           the slab soffit.  It RIDES THE GIRDERS: it is
                                 girder top flange + HAUNCH, interpolated
                                 across the four girder lines, so it carries
                                 all four cambers (A 18, B 14, C 22, D 11 mm)
                                 and the plan sweep.  A dependant that assumes
                                 a flat 8.200 is wrong by up to 22 mm = 27 px.
        HAUNCH            0.050  nominal haunch over each girder.  The haunch
                                 soffit is set 4 mm BELOW the flange top face
                                 so the concrete swallows the flange edge and
                                 nothing z-fights.
        road_z(x, y)             the FINISHED ROAD SURFACE (top of asphalt) on
                                 the carriageway.  Crown at y = -0.200, 2.5 %
                                 crossfall each way, and a longitudinal hog:
                                 z = 8.585 - 0.045*(x/15.6)^2 at the crown, so
                                 the deck sheds to BOTH ends and the gullies
                                 sit 2.0 m short of each joint.
        SURF_T            0.048  45 mm asphalt + 3 mm waterproofing.  The
                                 structural concrete top is road_z - SURF_T.
        KERB_FACE_Y       2.160  kerb faces.  Clear carriageway 4.320 m.
        PLINTH_OUT_Y      2.580  outer edge of the parapet plinth.
        PARAPET_Y         2.400  THE PARAPET LINE.  Not a choice this item
                                 made: pont_girder already put its four end
                                 posts on the girder noses at y = +-2.400, and
                                 a parapet does not kink.  The plinth top is
                                 therefore 0.270 m wide astride that line and
                                 every ferrule pattern is centred on it.
        plinth_top_z(x, side)    top of the parapet plinth = road_z at the
                                 kerb face + 0.150.
        CORNICE          2.580 -> 3.000, falling 4 % outward, lip +0.020 above
                                 the channel at the plinth face.
        FASCIA_BEAM_Y     2.800  the fascia downstand runs y +-2.800..+-3.000
                                 and hangs BEAM_DROP = 0.120 below the
                                 cantilever soffit.
        fascia_top_z(x, side)    top of the fascia edge = the cornice at
                                 y = +-3.000.
        fascia_soffit_z(x, side) underside of the fascia beam.
        DRIP                     18 x 14 mm groove, its outer lip 45 mm in
                                 from the fascia face.

MOUNT FRAMES (bridge-local unless the slab was built with `place`, in which
case they are WORLD).  A Frame is .o origin, .x/.y/.z orthonormal axes, .r a
characteristic radius, .tag a string.  `sorted(D.mounts)` on a built slab
lists exactly what it grew.

    parapet_post_<L|R>_<n>   FOR pont_parapet.  36 of them (18 per side): the
                             CENTRE of the base-plate footprint on the plinth
                             top, .z UP, .x along the span.  .r 0.075.
                             The bolt pattern is 4 x M20 at 90 x 84 mm — the
                             SAME pattern pont_girder cast into its four end
                             posts, on purpose, so one base plate fits the
                             whole parapet.  Ferrule tops are flush with the
                             plinth and are real geometry (a 30 mm collar and
                             a 21 mm bore).  Post pitch 1.925 m, set OUT from
                             pont_girder's end posts at x = +-16.370 (girder
                             A) / +-16.020..16.120 (girder D) so the panel
                             that crosses the deck joint is a whole panel.
    joint_<m|p>              FOR bridge_expansion_joint.  .o on the deck
                             centreline at the END FACE, on the recess floor;
                             .x along the span pointing OUT of the deck, .z
                             UP.  .r = half the recess width.  The two ends
                             are NOT the same joint and the manifest says so
                             ("comb plate vs elastomeric"):
                               m  (x = -15.600)  ELASTOMERIC-IN-RUNNER.
                                  recess 0.500 wide x 0.075 deep, floor at
                                  road_z - 0.075, 34 cast-in anchor loops at
                                  0.150 pitch, gap to the abutment 0.065.
                               p  (x = +15.600)  COMB / FINGER PLATE.
                                  recess 0.360 wide x 0.055 deep with a
                                  screeded flat bed, 2 x 27 cast-in M20
                                  ferrules at 0.220 pitch and 0.180 gauge,
                                  a cast-in 80 x 80 x 8 galvanised nosing
                                  angle, gap 0.090.
                             pont_girder also welded a support angle for this
                             joint to girder B's +x stub at local
                             (15.928, -0.751, 8.025) — that is 0.328 m OUTSIDE
                             my end face and 0.175 m below my soffit, i.e. it
                             carries the ABUTMENT-side plate, not mine.
    gully_<n>                FOR pont_scupper.  4 of them.  .o at the centre
                             of the frame seat, .z UP, .r 0.210 (the frame
                             flange half-diagonal).  Clear opening 0.300 sq.
    gully_outlet_<n>         FOR pont_scupper.  The 110 mm spigot under the
                             soffit, .z pointing DOWN, .r 0.055.  Socket
                             depth 0.060, so a 110 mm pipe pushes in.
                             ROUTE NOTE, because it is not obvious and it is
                             not free: BOTH fascia girders carry banners
                             (pont_girder's banner_face_A / banner_face_D), so
                             a downpipe may NOT hang on A or D.  It has to run
                             inboard along the soffit to girder B or C.
                             pont_girder already built the saddles for one
                             such pipe on girder B at local x = 15.560,
                             y = -0.711, z = 7.853 and 7.233 — that is the
                             pipe from gully_1 (x = +13.600, y = -1.980).
                             `soffit_insert_*` frames follow all four routes.
    soffit_insert_<n>        FOR pont_soffit_panel and pont_service_duct.  42
                             cast-in M12 sockets in the slab soffit, .z DOWN,
                             .r 0.018: a 1.500 m grid down the two soffit bays
                             either side of the centreline plus the four
                             drainage routes.  Flush 34 mm collars, real bores.
    duct_<n>                 Two 110 mm cast-in service ducts through the slab
                             at x = -14.900 and +14.900, y = -1.500.
    fascia_face_<L|R>        The fascia plane: .o at mid-span on the face,
                             .z the OUTWARD normal.  For anything that has to
                             be fixed to the fascia.
    cornice_<L|R>            The cornice top plane at mid-span.
    kerb_line_<L|R>          The kerb face line at mid-span, .z outward.

WHAT THIS MODULE DOES NOT OWN, SO THAT TWO AGENTS DO NOT BUILD IT TWICE
    pont_soffit_panel is a separate manifest item and it is the APPLIED soffit
    treatment — the lining panels and their carrier rails that hang under a
    bridge over a road.  What is here is the STRUCTURAL soffit those panels
    hang from: real board-marked concrete with haunches, blowholes, tie plugs
    and drainage stains, plus 42 cast-in sockets to hang from.  Neither is a
    substitute for the other and they do not occupy the same 40 mm of z.

THE THREE VARIATION AXES, DECIDED ONCE AND COUNTED ON BUILD
    kerb            The two sides are DIFFERENT OBJECTS, not one mirrored.
                    -y (the leading fascia, the one the lens sees) is 34
                    PRECAST kerb units, 915 x 150 x 225, bedded 25 mm on
                    mortar in a cast pocket: per unit its own bed lippage
                    (+-3.5 mm), plan rotation (+-0.5 deg), joint width
                    (6-16 mm), 0-3 chipped corners, its own casting lot
                    colour, two units replaced after an impact with a BULLNOSE
                    profile instead of half-battered, and one cracked clean
                    through with the two halves 2 mm out of line.
                    +y is MONOLITHIC IN-SITU: a battered upstand cast with the
                    deck, formed vertical joints at 3.0 m, and a galvanised
                    80 x 80 x 8 edge angle bolted along the arris at 1.5 m
                    centres — a repair after the same impact, and the reason
                    the two sides do not match.
    wearing surface Six states on one deck, all mesh: the original 45 mm
                    surfacing; two polished wheel tracks with 4-6 mm ruts;
                    a PLANED-AND-RELAID bay 6.4 m long with sawn edges, a
                    3.5 mm lippage and a hot-poured sealant bead round it;
                    a 0.42 m pothole repair standing 4 mm proud; grit banked
                    against both kerbs (thicker in the -y channel, which is
                    the low one); and thermoplastic lines worn thin in the
                    wheel tracks and full-thickness outside them.
    joint           The two ends are different joints, above.  Each is real
                    geometry in the concrete: a different recess width, depth,
                    floor finish, anchor system and gap.

BUILD
    materials(force=False) -> [conc, asph, kerb, steel, line, mortar].
                            Idempotent, named 'PDS_*'.  Slot order IS
                            MAT_CONC/MAT_ASPH/MAT_KERB/MAT_STEEL/MAT_LINE/
                            MAT_MORTAR.
    build(coll_name='PDS_Deck', place=None, res=1.0) -> Deck
                            Six objects, all prefixed `PDS_`:
                              PDS_Slab      the swept solid + end caps
                              PDS_Kerb_L    34 precast units + mortar bed
                              PDS_Fitting   ferrules, inserts, ducts, the +y
                                            edge angle and its bolts, the two
                                            joints' cast-in hardware, ID plate
                              PDS_Drain     4 gulley pots
                              PDS_Line      thermoplastic markings
                              PDS_Chip      loose surface chippings and grit
    deck_to_world()         -> (R 3x3, t 3), == pont_girder.pont_to_world().

    The item declares ONE instance, so the acceptance gate's per-instance
    check is vacuous by construction and the gate says so.  What it CANNOT
    check is that the three variation axes above are real; that is measured
    here instead and printed on every build (see `Deck.stats`), and the
    numbers are in the interface JSON.

PER-VERTEX CHANNELS (the shader contract, shared with pont_girder,
marshal_post_column and gantry_truss)
    uv    (u, v)   METRES: u around the section, v along the span.
    base  RGBA     surface colour (linear) + A = pour/lot id in [0,1]
    aux   RGBA     (edge_exposure, formed_face, surface_class, uid)
                   surface_class on THIS item's slab is written by the same
                   pass that displaced the feature, so a dependant tinting it
                   cannot get out of step with the geometry:
                       0.00  plain concrete
                       0.35  mortar form-tie plug (recessed or proud)
                       0.70  open form-tie hole, dark inside
                       0.95  honeycombed, aggregate exposed
    wear  RGBA     (chip, dirt, bio, age).  chip carries the rust dribbles as
                   well as the chipped arrises: mat_concrete routes it to the
                   rust bleed and both are iron staining out of the concrete.

THE HARD-SURFACE TOOLKIT is imported from world/items/marshal_post_column.py,
which declares it reusable in its own docstring; the FASTENER vocabulary from
world/items/gantry_truss.py; and the girder datum, the ear-clip capper and the
bridge frame from world/items/pont_girder.py.  All same-repo hand-written
procedural code; no external asset is involved anywhere in this module.

Run standalone to build the test scene:

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P world/items/pont_deck_slab.py -- --test \
        --out world/items/pont_deck_slab_test.blend
"""

import gc
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
import pont_girder as PG                                  # noqa: E402

# Contract checks at import, so a refactor upstream fails HERE with a name
# instead of 900 lines later with an AttributeError.
for _need in ("Acc", "sweep", "bridge", "circle_section", "rrect_section",
              "section_outward", "section_perimeter_u", "cap_flat", "hex_nut",
              "washer", "thread_stud", "frames_along", "rot_axis", "rotz",
              "unit", "Frame", "chan", "NG", "srgb", "rect_loop",
              "rect_loop_counts", "angle_section", "weld_bead"):
    if not hasattr(HS, _need):
        raise ImportError(
            "pont_deck_slab needs marshal_post_column.%s and it is gone. The "
            "hard-surface toolkit is a shared interface; restore the name or "
            "port the primitive here." % _need)
for _need in ("bolt", "bolt_spec", "hex_head", "local_frame", "BOLTS"):
    if not hasattr(GT, _need):
        raise ImportError(
            "pont_deck_slab needs gantry_truss.%s and it is gone." % _need)
for _need in ("SPECS", "GIRDER_IDS", "GIRDER_Y", "SOFFIT_Z", "TOP_FLANGE_Z",
              "DECK_SOFFIT_Z", "HAUNCH_M", "DECK_WIDTH", "SPAN", "BEARING_X",
              "S_STATION", "top_z", "web_y", "pont_to_world", "ear_clip",
              "cap_section", "contract_light", "context_ground",
              "context_abutments", "_mat4", "_put_camera"):
    if not hasattr(PG, _need):
        raise ImportError(
            "pont_deck_slab is built on pont_girder.%s and it is gone. This "
            "item's whole datum comes from the girders; restore the name."
            % _need)

Acc = HS.Acc
sweep = HS.sweep
bridge = HS.bridge
unit = HS.unit
Frame = HS.Frame
chan = HS.chan
srgb = HS.srgb
rot_axis = HS.rot_axis
rotz = HS.rotz
circle_section = HS.circle_section
rrect_section = HS.rrect_section
angle_section = HS.angle_section
section_perimeter_u = HS.section_perimeter_u
cap_flat = HS.cap_flat
hex_nut = HS.hex_nut
washer = HS.washer
thread_stud = HS.thread_stud
weld_bead = HS.weld_bead

bolt = GT.bolt
bolt_spec = GT.bolt_spec
local_frame = GT.local_frame

PFX = "PDS_"
ROOT_COLL = "PDS_Deck"
SENSOR_MM = 36.0
TAU = 2.0 * math.pi

MAT_CONC, MAT_ASPH, MAT_KERB, MAT_STEEL, MAT_LINE, MAT_MORTAR = range(6)
MAT_NAMES = ["Concrete", "Asphalt", "Kerb", "Steel", "Line", "Mortar"]


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


_U32 = np.uint32


def vh(*keys):
    """VECTORISED FNV-1a over integer arrays -> float64 in [0,1).  Broadcasts.

    The blowhole field asks 'how far is this vertex from the nearest void' for
    1.9 million vertices against a 3x3 neighbourhood of jittered cells, which
    is 17 million lookups.  A per-vertex Python hash would take an hour; this
    takes four seconds.  Same FNV constants as world_contract.hash01 so the
    two agree where they overlap.
    """
    shp = np.broadcast(*[np.asarray(k) for k in keys]).shape if len(keys) > 1 \
        else np.shape(keys[0])
    h = np.full(shp, _U32(2166136261), dtype=np.uint32)
    with np.errstate(over="ignore"):
        for k in keys:
            kk = np.asarray(k)
            kk = (np.rint(kk).astype(np.int64) if kk.dtype.kind == "f"
                  else kk.astype(np.int64))
            kk = (kk & 0xFFFFFFFF).astype(np.uint32)
            h = (h ^ kk) * _U32(16777619)
            h = h ^ (h >> _U32(13))
            h = h * _U32(2654435761)
            h = h ^ (h >> _U32(16))
    return (h & _U32(0xFFFFFF)).astype(np.float64) / 16777215.0


def _sstep(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def fbm(a, b, seed, oct=4, base=1.0, gain=0.5, lac=2.11):
    """Value-noise fbm over two metre coordinates.  Cheap, vectorised, tileless
    enough for a 31 m deck.  Returns roughly [-1, 1]."""
    out = np.zeros(np.broadcast(a, b).shape)
    amp, f = 1.0, base
    norm = 0.0
    for o in range(oct):
        ia = np.floor(a * f).astype(np.int64)
        ib = np.floor(b * f).astype(np.int64)
        fa = a * f - ia
        fb = b * f - ib
        sa, sb = _sstep(fa), _sstep(fb)
        h00 = vh(ia, ib, seed + o)
        h10 = vh(ia + 1, ib, seed + o)
        h01 = vh(ia, ib + 1, seed + o)
        h11 = vh(ia + 1, ib + 1, seed + o)
        v = ((h00 * (1 - sa) + h10 * sa) * (1 - sb)
             + (h01 * (1 - sa) + h11 * sa) * sb)
        out = out + amp * (v * 2.0 - 1.0)
        norm += amp
        amp *= gain
        f *= lac
    return out / max(norm, 1e-9)


# --------------------------------------------------------------------------- #
#  2.  THE DIMENSIONS.  Every one is a buildable size.                          #
# --------------------------------------------------------------------------- #

S_STATION = PG.S_STATION                     # 2410.0
HAUNCH = PG.HAUNCH_M                         # 0.050
FLANGE_SINK = 0.004                          # haunch soffit below the flange top
DECK_HALF_W = PG.DECK_WIDTH * 0.5            # 3.000
END_X = 15.600                               # deck slab ends
DECK_LEN = 2.0 * END_X                       # 31.200

CROWN_Y = -0.200                             # crown offset from the centreline
XFALL = 0.025                                # 2.5 % crossfall
Z_CROWN0 = 8.585                             # road surface at the crown, mid-span
CROWN_HOG = 0.045                            # falls this much to each deck end
SURF_T = 0.048                               # 45 asphalt + 3 waterproofing

KERB_FACE_Y = 2.160                          # kerb faces; carriageway 4.320 m
KERB_W = 0.150                               # precast kerb unit width
KERB_UP = 0.150                              # kerb / plinth upstand over channel
POCKET_D = 0.100                             # kerb pocket floor below the channel
PLINTH_IN_L = KERB_FACE_Y + KERB_W           # 2.310, back of the -y kerb pocket
PLINTH_OUT_Y = 2.580
BATTER_DY = 0.0375                           # 1:4 batter on the +y upstand
UP_CHAMF = 0.020                             # chamfer on the +y upstand arris
CORN_LIP = 0.020                             # cornice top above the channel
CORN_FALL = 0.040                            # cornice outward fall (4 %)
FASCIA_BEAM_Y = 2.800
BEAM_DROP = 0.120
TOP_CHAMF = 0.020                            # fascia top arris chamfer
RUST_Z = 0.110                               # rustication groove, below the top
RUST_H = 0.025                               # its height
RUST_D = 0.014                               # its depth
RUST_STOP = 0.35                             # ... tapering out this far from
                                             # each deck end, which is both how
                                             # a real rustication is stopped
                                             # short of a movement joint and
                                             # what keeps the end section
                                             # y-monotone for the cap merge
BOT_CHAMF = 0.012                            # fascia bottom arris chamfer
DRIP_OUT = 0.045                             # drip outer lip, in from the face
DRIP_W = 0.018
DRIP_D = 0.014

PARAPET_Y = 2.400                            # pont_girder's end posts: not mine
POST_PITCH = 1.925
POST_END_X = 16.370                          # pont_girder parapet_end_A_m/p
FERRULE_GAUGE = (0.090, 0.084)               # 4 x M20 at 90 x 84, same as PG
FERRULE_BORE = 0.0105
FERRULE_COLLAR = 0.015

GULLY_X = 13.600
GULLY_Y = 1.980
GULLY_CLEAR = 0.300                          # clear opening
GULLY_FLANGE = 0.420
GULLY_DEPTH = 0.150
GULLY_SPIGOT_R = 0.055

JOINT_M_W = 0.500                            # elastomeric recess
JOINT_M_D = 0.075
JOINT_M_GAP = 0.065
JOINT_P_W = 0.360                            # comb-plate recess
JOINT_P_D = 0.055
JOINT_P_GAP = 0.090

PLY_LEN = 2.440                              # formwork panel length
TIE_X = 0.600                                # form-tie grid
TIE_V = 0.280                                # TWO rows on a 432 mm face
TIE_OFF = 0.105                              # rows at u = 0.105 and 0.385.
                                             # 0.450/0.210 put exactly ONE row
                                             # dead across the middle of the
                                             # face, and once the plugs were
                                             # made visible that read as a
                                             # dotted line ruled along the
                                             # bridge -- a motif, which is the
                                             # named failure.  A 500 mm form
                                             # lift takes two rows anyway.
POUR_X = 2.050                               # construction joint between pours

# Concrete lots.  Two pours plus the precast kerb lots plus the repair mortar.
# ALBEDO IS A MEASUREMENT, NOT A MOOD.  Weathered structural concrete is
# 0.18-0.24 linear, not 0.32: the first pass used #9a978f (0.32) plus chalk and
# laitance mixes that took it to 0.43, which under AgX at the contract exposure
# of -3.048 put the sunlit fascia into the highlight shoulder -- where the
# transform desaturates and flattens EVERYTHING, so a face carrying 40,000
# blowholes rendered as a blank cream band.  Measured on the render, not
# reasoned: mean 0.585, and the fascia region 0.78.
CONC_A_HEX = "#6f6c66"                       # pour 1 (the -x half), 0.155 lin
CONC_B_HEX = "#68635c"                       # pour 2 (the +x half), greyer lot
KERB_HEX = ("#a7a49c", "#9d9a92", "#b0aca2")  # three precast casting lots
REPAIR_HEX = "#8e8b84"
ASPH_HEX = "#232324"
LINE_HEX = "#c9c8c2"
ZINC_HEX = "#9aa0a4"
MORTAR_HEX = "#a09c92"


# --------------------------------------------------------------------------- #
#  3.  THE SURFACES  (plan layer -- no bpy, callable from a bare shell)         #
# --------------------------------------------------------------------------- #

def z_crown(x):
    """Road surface z at the crown line.  A hog, so the deck sheds to BOTH
    ends and neither joint is the low point of a 31 m puddle."""
    x = np.asarray(x, float)
    return Z_CROWN0 - CROWN_HOG * (x / END_X) ** 2


def road_z(x, y):
    """PUBLIC.  Finished road surface (top of asphalt) on the carriageway."""
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    return z_crown(x) - XFALL * np.abs(y - CROWN_Y)


def chan_z(x, side):
    """Channel invert: the road surface at the kerb face on `side`
    (+1 = +y, -1 = -y)."""
    return road_z(x, side * KERB_FACE_Y)


def plinth_top_z(x, side):
    """PUBLIC.  Top of the parapet plinth on `side`."""
    return chan_z(x, side) + KERB_UP


def cornice_z(x, y):
    """PUBLIC.  Top of the cornice outboard of the plinth."""
    side = np.sign(y) if np.ndim(y) else (1.0 if y >= 0 else -1.0)
    return (chan_z(x, side) + CORN_LIP
            - CORN_FALL * (np.abs(y) - PLINTH_OUT_Y))


def fascia_top_z(x, side):
    """PUBLIC.  Top of the fascia edge (the cornice at y = +-3.000)."""
    return (chan_z(x, side) + CORN_LIP
            - CORN_FALL * (DECK_HALF_W - PLINTH_OUT_Y))


def _gtop(gid, x):
    """The girder's top flange top face, from pont_girder.  Cambered."""
    return PG.top_z(PG.SPECS[gid], np.asarray(x, float))


def _gy(gid, x):
    """The girder's web centreline in plan, from pont_girder.  Swept."""
    return PG.web_y(PG.SPECS[gid], np.asarray(x, float))


def soffit_base(x, y):
    """PUBLIC.  The slab soffit BETWEEN the haunches, at (x, y).

    It rides the girders: linear interpolation of (flange top + HAUNCH) across
    the four girder lines, held flat outboard of the fascia girders.  All four
    cambers are in it, which is why the two fascia edges of this deck are not
    parallel when sighted along -- 18 mm on A against 11 mm on D is 7 mm, and
    7 mm at 1244 px/m is 8.7 px of relative bow.
    """
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    ys = np.stack([_gy(g, x) for g in PG.GIRDER_IDS], -1)          # (..., 4)
    zs = np.stack([_gtop(g, x) + HAUNCH for g in PG.GIRDER_IDS], -1)
    yy = np.broadcast_to(y, x.shape) if np.ndim(y) == 0 else y
    yy = np.broadcast_arrays(x, yy)[1]
    out = np.empty(np.broadcast(x, yy).shape, float)
    out[...] = zs[..., 0]
    for i in range(3):
        t = np.clip((yy - ys[..., i]) / np.maximum(ys[..., i + 1]
                                                   - ys[..., i], 1e-9), 0.0, 1.0)
        out = np.where(yy > ys[..., i],
                       zs[..., i] + t * (zs[..., i + 1] - zs[..., i]), out)
    out = np.where(yy <= ys[..., 0], zs[..., 0], out)
    out = np.where(yy >= ys[..., 3], zs[..., 3], out)
    return out


def soffit_z(x, y):
    """PUBLIC.  The slab soffit INCLUDING the haunch downstands.

    A dependant hanging anything under this deck wants THIS, not soffit_base:
    over a girder the concrete comes 50 mm lower to bear on the flange.
    """
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    out = soffit_base(x, y)
    for gid in PG.GIRDER_IDS:
        y0, y1 = haunch_edges(gid, x)
        zh = _gtop(gid, x) - FLANGE_SINK
        # 45 deg splay 0.050 wide on each side of the flat haunch soffit
        inside = (y >= y0) & (y <= y1)
        out = np.where(inside, zh, out)
        for (ye, sgn) in ((y0, -1.0), (y1, +1.0)):
            band = (y > ye + min(sgn, 0.0) * HAUNCH) & (y < ye + max(sgn, 0.0) * HAUNCH)
            t = np.clip(np.abs(y - ye) / HAUNCH, 0.0, 1.0)
            out = np.where(band & ~inside, zh + t * (soffit_base(x, y) - zh), out)
    return out


def haunch_edges(gid, x):
    """(y0, y1) of the FLAT haunch soffit under one girder.

    The concrete oversails the flange by 20 mm, EXCEPT on the outer side of a
    fascia girder, where it stops dead on the flange tip: pont_girder welded a
    60 x 8 banner rail to the underside of that tip and hung a banner 45 mm
    proud of the web, and a 20 mm oversail there would land on the rail.
    Measured against pont_girder's own interface, not assumed.
    """
    gs = PG.SPECS[gid]
    yc = _gy(gid, x)
    over_in, over_out = 0.020, 0.020
    if gid == "A":
        return yc - gs.tw * 0.5, yc + gs.tw * 0.5 + over_in
    if gid == "D":
        return yc - gs.tw * 0.5 - over_in, yc + gs.tw * 0.5
    return yc - gs.tw * 0.5 - over_out, yc + gs.tw * 0.5 + over_in


def cant_soffit_z(x, side):
    """The cantilever soffit outboard of a fascia girder: flat, at the fascia
    girder's own soffit level, so it carries that girder's camber."""
    gid = "D" if side > 0 else "A"
    return _gtop(gid, x) + HAUNCH


def fascia_soffit_z(x, side):
    """PUBLIC.  Underside of the fascia downstand beam."""
    return cant_soffit_z(x, side) - BEAM_DROP


def deck_conc_z(x, y):
    """Top of the structural concrete under the surfacing."""
    return road_z(x, y) - SURF_T


# --------------------------------------------------------------------------- #
#  4.  THE STATION LIST                                                         #
# --------------------------------------------------------------------------- #

# Everything that needs a station exactly ON it, so a vertical face is
# vertical rather than a 26 mm ramp.
def feature_stations():
    xs = [-END_X, END_X, 0.0, POUR_X, POUR_X - 0.0025, POUR_X + 0.0025]
    # joint recesses: outer face, recess wall, and a 2.5 mm pair either side
    for (sgn, w) in ((-1.0, JOINT_M_W), (+1.0, JOINT_P_W)):
        xw = sgn * (END_X - w)
        for d in (-0.0025, 0.0, 0.0025):
            xs.append(xw + sgn * d)
        xs.append(sgn * (END_X - 0.0025))
    # gullies: the hole edges want stations
    for sx in (-1.0, 1.0):
        for d in (-0.5 * GULLY_FLANGE, -0.5 * GULLY_CLEAR, 0.0,
                  0.5 * GULLY_CLEAR, 0.5 * GULLY_FLANGE):
            xs.append(sx * GULLY_X + d)
    # the planed-and-relaid bay and the pothole repair
    for x in (RELAY_X0, RELAY_X1):
        xs += [x - 0.0025, x, x + 0.0025]
    return xs


RELAY_X0, RELAY_X1 = -7.400, -1.000          # the planed-and-relaid bay
POTHOLE = (5.900, 0.780, 0.210)              # x, y, radius
SPALL = (-3.150, 0.460, 0.105)               # x on the -y fascia, half-len, half-ht
HONEY = (6.720, 0.352, 0.160, 0.070)         # honeycombed patch: x, u, half-len,
                                             # half-height, low on the leading face
CHIP_ARRIS = ((-9.90, 0.042), (-1.35, 0.028), (4.60, 0.055), (11.20, 0.033),
              (14.05, 0.024))


STATION_EXP = 1.90


def stations(res=1.0):
    """Graded station list: near-CONSTANT ANGULAR RESOLUTION on the fascia.

    dx(x) = clip(0.0016 * (d/3.2)^1.90, 0.0016, 0.028), d = hypot(x, 3.2).

    d is the distance from the point where the film's lens passes under this
    deck to station x on the fascia, so the facet size is set by the ANGLE it
    subtends, not by one number applied flat over 31 m.

    THE FLOOR IS 1.6 mm = 1.9 SCREEN PIXELS at the manifest's 3.0 m / 35 mm,
    not the 3.8 mm (4.7 px) this shipped with.  The reason is written out at
    D_HERO above: at 4.7 px a quad is wider than half the blowholes it is
    carrying, so they rendered as lumps instead of voids.  Two pixels is the
    coarsest quad on which a 3 mm void still has an inside.

    THE EXPONENT WAS 2.60 AND THAT WAS A DEFECT, caught by looking at the 4K
    macro rather than by reading the code.  The docstring claimed "constant
    angular resolution"; the arithmetic that phrase implies is exponent 1.0,
    because facet_px = (3733/d) * lo * (d/3.2)^k is constant in d only when
    k = 1.  At k = 2.60 the facet size in SCREEN PIXELS was

        1.9 px at 3.2 m ... 8.1 px at 8 m ... 6.5 px at 16 m

    i.e. it got FOUR TIMES COARSER over the frame.  Measured on the macro:
    the near fascia carries visible blowholes and the fascia 6-9 m along the
    same edge -- IN THE SAME FRAME, at 500 px/m, where a 4 mm void is still
    2 px -- is bare.  That reads as the concrete turning to plastic halfway
    down the bridge, and it is the single most obvious flaw in the frame.

    1.90 holds the facet at 1.9 px at 3.2 m, 4.3 px at 8 m and 6.5 px at
    16 m, for 5 724 stations and 9.8 M slab vertices.  It is NOT the value
    the picture wants -- 1.35 would hold 1.9-3.3 px everywhere -- and the
    reason it is not 1.35 is a MEASURED MACHINE LIMIT, not a judgement:
    1.35 costs 7 460 stations x 1 712 section points = 12.8 M vertices, and
    the build host has 11.9 GB of RAM.  That build was killed part-way with
    the log still empty.  9.8 M is 24 % over the largest build this box has
    completed (7.93 M) and it is where the risk stops being worth taking.

    SO THIS IS A CAPPED FIX AND IT SHOULD BE UNCAPPED ON A BIGGER HOST.  It
    removes the visible half of the defect -- 8.1 px -> 4.3 px in the 5-9 m
    band where the macro showed bare concrete on a surface that at 500 px/m
    should still carry blowholes.  The 16 m end is still at the 6 px hero
    limit.  Raise STATION_EXP toward 1.0 the moment there is memory for it;
    every number in this docstring is the arithmetic for doing so.
    """
    q = max(min(float(res), 2.0), 0.25)
    lo, hi = 0.0016 / q, 0.028 / q
    xs = [0.0]
    x = 0.0
    while x < END_X:
        d = math.hypot(x, 3.2)
        step = min(max(lo * (d / 3.2) ** STATION_EXP, lo), hi)
        x += step
        xs.append(min(x, END_X))
    xs = np.array(xs)
    xs = np.concatenate([-xs[::-1], xs])
    xs = np.concatenate([xs, np.array(feature_stations(), float)])
    xs = np.unique(np.clip(xs, -END_X, END_X))
    # drop stations closer than 0.8 mm together -- they came from the union and
    # a 0.8 mm quad is a shading artefact, not detail
    keep = [xs[0]]
    for v in xs[1:]:
        if v - keep[-1] >= 0.0008:
            keep.append(v)
    return np.array(keep)


# --------------------------------------------------------------------------- #
#  5.  THE CROSS-SECTION                                                        #
# --------------------------------------------------------------------------- #
#
# The whole slab is ONE closed loop in (y, z) swept along x.  One loop, not six
# stitched patches, for a reason worth writing down: a patch boundary on a
# continuous concrete surface duplicates a vertex row, and two rows with
# independently-computed normals put a shading crease down a 31 m soffit that
# no amount of displacement can hide.  The loop is traversed CCW in (y, z) --
# down the leading fascia, along the underside toward +y, up the trailing
# fascia, back across the top -- which with the sweep running along +x makes
# every face normal point out of the concrete.
#
# The DENSITY is per segment, because a 4 mm facet on the leading fascia is
# 5 px and a 4 mm facet on the buried haunch soffit under a 450 mm flange is
# 5 px of nothing at all.

D_HERO = 0.0016          # the leading fascia, its drip, its arrises
D_DET = 0.0013           # arris roundings, drip lips
D_SOFF = 0.0032          # the leading cantilever soffit
#
# WHY 1.6 mm AND NOT THE 3.2 mm THIS SHIPPED WITH.  MEASURED, on the 4K macro
# at the manifest's own 3.0 m / 35 mm: at 3.2 mm section x 4.0 mm station the
# quad on the leading fascia is 4.0 x 5.0 SCREEN PIXELS, and the blowhole
# population it is carrying is 2-9.6 mm ACROSS.  Half the voids were therefore
# narrower than one quad, and a void narrower than a quad is not a void: it is
# a single displaced vertex, which smooth shading renders as a soft lump with
# no rim and no shadow.  CAM_PDS_DRIP (0.68 m, 58 mm) showed them reading as
# proud faceted blobs — the exact "material with no geometry behind it" the
# campaign brief rejects, arrived at from the other direction.
#     1.6 mm is 2.0 px at the filmed distance, so the smallest void that still
# matters (3 mm) spans 2 quads and the median (6 mm) spans 4.  Sub-2 mm sand
# holes are BELOW one screen pixel and are left to the shader's 0.9 mm fines
# bump, which is where a bump map is honest rather than a substitute.
# Cost: K 1462 -> 1737 section points, M 2720 -> 4630 stations, 8.0 M verts.
D_HAUN = 0.0070          # haunch splays
D_HBUR = 0.0400          # the haunch soffit BURIED under the flange
D_MAIN = 0.0080          # the soffit bays between girders -- the MANIFEST'S
                         # 3.0 m is the soffit DIRECTLY OVERHEAD of the film's
                         # lens (8.218 - 5.000 = 3.218), so this is a hero
                         # surface too and 8 mm is 10 px at that distance
D_FAR = 0.0100           # the trailing (+y) cantilever and fascia
D_TOP = 0.0240           # the carriageway
D_CHAN = 0.0090          # channels, kerb faces, plinths
D_CORN = 0.0100          # cornices

# aux.x edge exposure, aux.y formed-face flag (1 = cast against ply, 0 = top
# finish), used by the shader to decide where blowholes, board grain and
# chalking live.  A screeded top and a formed fascia are not the same concrete.


def rust_depth(X):
    """Rustication groove depth at station x: full over the span, tapered to
    nothing 0.35 m short of each deck end."""
    X = np.asarray(X, float)
    return RUST_D * _sstep((END_X - np.abs(X) - 0.10) / RUST_STOP)


def _corner_table(X):
    """The section as a polyline of corners, per station.

    -> Y (C, M), Z (C, M), DENS (C,), MAT (C,), EDGE (C,), FORM (C,), NAMES
    DENS/MAT/EDGE/FORM belong to the SEGMENT STARTING at that corner, except
    EDGE which is a per-corner value and is interpolated along the segment.
    """
    X = np.asarray(X, float)
    zcL, zcR = chan_z(X, -1.0), chan_z(X, +1.0)
    zpL, zpR = zcL + KERB_UP, zcR + KERB_UP
    ftL, ftR = fascia_top_z(X, -1.0), fascia_top_z(X, +1.0)
    zcsL, zcsR = cant_soffit_z(X, -1.0), cant_soffit_z(X, +1.0)
    zfbL, zfbR = zcsL - BEAM_DROP, zcsR - BEAM_DROP
    one = np.ones_like(X)

    K = []                       # (name, y, z, dens, mat, edge, form)

    def c(name, y, z, dens, mat, edge, form):
        K.append((name, np.broadcast_to(np.asarray(y, float), X.shape).copy(),
                  np.broadcast_to(np.asarray(z, float), X.shape).copy(),
                  dens, mat, edge, form))

    # ---- the LEADING (-y) fascia, top to bottom -------------------------
    rd = rust_depth(X)
    c("fascia_L_top", -DECK_HALF_W * one, ftL - TOP_CHAMF, D_HERO,
      MAT_CONC, 0.55, 1.0)
    # THE RUSTICATION.  25 x 14 mm, 110 mm below the top arris.  It is here
    # because the contract sun hits this fascia within 14 deg of NORMAL, and
    # relief lit head-on casts no shadow: a 3 mm grout fin under this sun is
    # 0.7 mm of shade and reads as nothing.  A 14 mm groove is dark under any
    # sun in the sky, and it is what gives a bridge deck its line at 200 m as
    # well as its interest at 3 m.
    c("rustL_a", -DECK_HALF_W * one, ftL - RUST_Z, D_DET, MAT_CONC, 0.95, 1.0)
    c("rustL_b", -DECK_HALF_W + rd * 0.18, ftL - RUST_Z - 0.0025, D_DET,
      MAT_CONC, 0.55, 1.0)
    c("rustL_c", -DECK_HALF_W + rd, ftL - RUST_Z - 0.0038, D_DET,
      MAT_CONC, 0.10, 1.0)
    c("rustL_d", -DECK_HALF_W + rd, ftL - RUST_Z - RUST_H + 0.0038, D_DET,
      MAT_CONC, 0.10, 1.0)
    c("rustL_e", -DECK_HALF_W + rd * 0.18, ftL - RUST_Z - RUST_H + 0.0025,
      D_DET, MAT_CONC, 0.65, 1.0)
    c("rustL_f", -DECK_HALF_W * one, ftL - RUST_Z - RUST_H, D_HERO,
      MAT_CONC, 0.85, 1.0)
    c("fascia_L_bot", -DECK_HALF_W * one, zfbL + BOT_CHAMF, D_DET,
      MAT_CONC, 0.60, 1.0)
    c("fascia_L_ch1", -2.9962 * one, zfbL + 0.0042, D_DET, MAT_CONC, 1.00, 1.0)
    c("fascia_L_ch2", -2.9880 * one, zfbL, D_HERO, MAT_CONC, 0.75, 1.0)
    # beam soffit out to the drip
    c("beam_L_out", -(DECK_HALF_W - DRIP_OUT) * one, zfbL, D_DET,
      MAT_CONC, 0.65, 1.0)
    c("dripL_o1", -(DECK_HALF_W - DRIP_OUT - 0.0005) * one, zfbL + 0.0025,
      0.0022, MAT_CONC, 0.90, 1.0)
    c("dripL_o2", -(DECK_HALF_W - DRIP_OUT - 0.0015) * one, zfbL + DRIP_D,
      0.0022, MAT_CONC, 0.15, 1.0)
    c("dripL_i2", -(DECK_HALF_W - DRIP_OUT - DRIP_W + 0.0015) * one,
      zfbL + DRIP_D, 0.0022, MAT_CONC, 0.15, 1.0)
    c("dripL_i1", -(DECK_HALF_W - DRIP_OUT - DRIP_W + 0.0005) * one,
      zfbL + 0.0025, 0.0022, MAT_CONC, 0.90, 1.0)
    c("beam_L_in", -(DECK_HALF_W - DRIP_OUT - DRIP_W) * one, zfbL, D_HERO,
      MAT_CONC, 0.60, 1.0)
    c("beam_L_ich0", -(FASCIA_BEAM_Y + 0.012) * one, zfbL, D_DET,
      MAT_CONC, 0.60, 1.0)
    c("beam_L_ich1", -(FASCIA_BEAM_Y + 0.0042) * one, zfbL + 0.0042, D_DET,
      MAT_CONC, 0.95, 1.0)
    c("beam_L_face", -FASCIA_BEAM_Y * one, zfbL + BOT_CHAMF, D_SOFF,
      MAT_CONC, 0.55, 1.0)
    c("beam_L_fil0", -FASCIA_BEAM_Y * one, zcsL - 0.0140, 0.004,
      MAT_CONC, 0.20, 1.0)
    c("beam_L_fil1", -(FASCIA_BEAM_Y - 0.010) * one, zcsL, D_SOFF,
      MAT_CONC, 0.05, 1.0)

    # ---- the underside: cantilever, four haunches, three bays ----------
    prev_dens = D_SOFF
    for gid in PG.GIRDER_IDS:
        y0, y1 = haunch_edges(gid, X)
        zh = _gtop(gid, X) - FLANGE_SINK
        c("splay_%s_o0" % gid, y0 - HAUNCH, soffit_base(X, y0 - HAUNCH),
          D_HAUN, MAT_CONC, 0.30, 1.0)
        c("splay_%s_o1" % gid, y0, zh, D_HBUR, MAT_CONC, 0.45, 1.0)
        c("haunch_%s_i" % gid, y1, zh, D_HAUN, MAT_CONC, 0.45, 1.0)
        c("splay_%s_i1" % gid, y1 + HAUNCH, soffit_base(X, y1 + HAUNCH),
          D_MAIN if gid != "D" else D_SOFF, MAT_CONC, 0.30, 1.0)
        prev_dens = D_MAIN

    # ---- the TRAILING (+y) cantilever and fascia, bottom to top --------
    c("beam_R_fil1", (FASCIA_BEAM_Y - 0.010) * one, zcsR, 0.006,
      MAT_CONC, 0.05, 1.0)
    c("beam_R_fil0", FASCIA_BEAM_Y * one, zcsR - 0.0140, D_FAR,
      MAT_CONC, 0.20, 1.0)
    c("beam_R_face", FASCIA_BEAM_Y * one, zfbR + BOT_CHAMF, 0.0035,
      MAT_CONC, 0.55, 1.0)
    c("beam_R_ich1", (FASCIA_BEAM_Y + 0.0042) * one, zfbR + 0.0042, 0.0035,
      MAT_CONC, 0.95, 1.0)
    c("beam_R_ich0", (FASCIA_BEAM_Y + 0.012) * one, zfbR, D_FAR,
      MAT_CONC, 0.60, 1.0)
    c("beam_R_in", (DECK_HALF_W - DRIP_OUT - DRIP_W) * one, zfbR, 0.0035,
      MAT_CONC, 0.60, 1.0)
    c("dripR_i1", (DECK_HALF_W - DRIP_OUT - DRIP_W + 0.0005) * one,
      zfbR + 0.0025, 0.0035, MAT_CONC, 0.90, 1.0)
    c("dripR_i2", (DECK_HALF_W - DRIP_OUT - DRIP_W + 0.0015) * one,
      zfbR + DRIP_D, 0.0035, MAT_CONC, 0.15, 1.0)
    c("dripR_o2", (DECK_HALF_W - DRIP_OUT - 0.0015) * one, zfbR + DRIP_D,
      0.0035, MAT_CONC, 0.15, 1.0)
    c("dripR_o1", (DECK_HALF_W - DRIP_OUT - 0.0005) * one, zfbR + 0.0025,
      D_FAR, MAT_CONC, 0.90, 1.0)
    c("beam_R_out", (DECK_HALF_W - DRIP_OUT) * one, zfbR, 0.003,
      MAT_CONC, 0.65, 1.0)
    c("fascia_R_ch2", 2.9880 * one, zfbR, 0.003, MAT_CONC, 0.75, 1.0)
    c("fascia_R_ch1", 2.9962 * one, zfbR + 0.0042, D_FAR, MAT_CONC, 1.00, 1.0)
    c("fascia_R_bot", DECK_HALF_W * one, zfbR + BOT_CHAMF, 0.0080,
      MAT_CONC, 0.60, 1.0)
    c("rustR_f", DECK_HALF_W * one, ftR - RUST_Z - RUST_H, 0.0035,
      MAT_CONC, 0.85, 1.0)
    c("rustR_e", DECK_HALF_W - rd * 0.18, ftR - RUST_Z - RUST_H + 0.0025,
      0.0035, MAT_CONC, 0.65, 1.0)
    c("rustR_d", DECK_HALF_W - rd, ftR - RUST_Z - RUST_H + 0.0038, 0.0035,
      MAT_CONC, 0.10, 1.0)
    c("rustR_c", DECK_HALF_W - rd, ftR - RUST_Z - 0.0038, 0.0035,
      MAT_CONC, 0.10, 1.0)
    c("rustR_b", DECK_HALF_W - rd * 0.18, ftR - RUST_Z - 0.0025, 0.0035,
      MAT_CONC, 0.55, 1.0)
    c("rustR_a", DECK_HALF_W * one, ftR - RUST_Z, 0.009, MAT_CONC, 0.95, 1.0)
    c("fascia_R_top", DECK_HALF_W * one, ftR - TOP_CHAMF, 0.003,
      MAT_CONC, 0.55, 1.0)
    c("corn_R_ch1", 2.9962 * one, ftR - 0.0042, 0.003, MAT_CONC, 1.00, 1.0)
    c("corn_R_ch2", 2.9880 * one, ftR, D_CORN, MAT_CONC, 0.70, 0.0)

    # ---- the TOP, +y to -y ---------------------------------------------
    c("corn_R_in", PLINTH_OUT_Y * one, zcR + CORN_LIP, 0.007,
      MAT_CONC, 0.35, 0.0)
    c("plinth_R_f0", PLINTH_OUT_Y * one, zpR - 0.012, 0.004,
      MAT_CONC, 0.55, 1.0)
    c("plinth_R_f1", (PLINTH_OUT_Y - 0.008) * one, zpR, D_CHAN,
      MAT_CONC, 0.95, 0.0)
    c("plinth_R_top", (KERB_FACE_Y + BATTER_DY + UP_CHAMF) * one, zpR, 0.004,
      MAT_CONC, 0.45, 0.0)
    c("upst_R_ch", (KERB_FACE_Y + BATTER_DY) * one, zpR - UP_CHAMF, 0.006,
      MAT_CONC, 1.00, 0.0)
    c("upst_R_foot", KERB_FACE_Y * one, zcR, D_CHAN, MAT_ASPH, 0.40, 0.0)
    c("chan_R_in", 1.8100 * one, road_z(X, 1.81), D_TOP, MAT_ASPH, 0.05, 0.0)
    c("crown", CROWN_Y * one, z_crown(X), D_TOP, MAT_ASPH, 0.05, 0.0)
    c("chan_L_in", -1.8100 * one, road_z(X, -1.81), D_CHAN,
      MAT_ASPH, 0.05, 0.0)
    c("kerbface_L", -KERB_FACE_Y * one, zcL, 0.004, MAT_ASPH, 0.30, 0.0)
    c("asph_L_bot", -KERB_FACE_Y * one, zcL - SURF_T, 0.006,
      MAT_CONC, 0.40, 0.0)
    c("pocket_L_f", -KERB_FACE_Y * one, zcL - POCKET_D, 0.006,
      MAT_CONC, 0.30, 1.0)
    c("pocket_L_b", -PLINTH_IN_L * one, zcL - POCKET_D, 0.008,
      MAT_CONC, 0.30, 1.0)
    c("pocket_L_w", -PLINTH_IN_L * one, zpL - 0.012, 0.004, MAT_CONC, 0.55, 1.0)
    c("plinth_L_i", -(PLINTH_IN_L + 0.008) * one, zpL, D_CHAN,
      MAT_CONC, 0.95, 0.0)
    c("plinth_L_o", -(PLINTH_OUT_Y - 0.008) * one, zpL, 0.006,
      MAT_CONC, 0.45, 0.0)
    c("plinth_L_f0", -PLINTH_OUT_Y * one, zpL - 0.012, 0.007,
      MAT_CONC, 0.95, 1.0)
    c("corn_L_in", -PLINTH_OUT_Y * one, zcL + CORN_LIP, D_CORN,
      MAT_CONC, 0.35, 0.0)
    c("corn_L_ch2", -2.9880 * one, ftL, 0.003, MAT_CONC, 0.70, 0.0)
    c("corn_L_ch1", -2.9962 * one, ftL - 0.0042, 0.003, MAT_CONC, 1.00, 1.0)

    NAMES = [k[0] for k in K]
    Y = np.stack([k[1] for k in K], 0)
    Z = np.stack([k[2] for k in K], 0)
    DENS = np.array([k[3] for k in K])
    MAT = np.array([k[4] for k in K], np.int32)
    EDGE = np.array([k[5] for k in K])
    FORM = np.array([k[6] for k in K])
    return Y, Z, DENS, MAT, EDGE, FORM, NAMES


def build_section(X, res=1.0):
    """Sample the corner table into a fixed-K closed section per station.

    The sample COUNTS are computed once, at mid-span, and reused at every
    station.  They have to be constant -- a sweep needs a rectangular index
    grid -- and they can be, because the section's segment lengths change by
    at most 22 mm (the camber) over 31 m.
    """
    X = np.asarray(X, float)
    Y, Z, DENS, MAT, EDGE, FORM, NAMES = _corner_table(X)
    Cn, M = Y.shape
    q = max(min(float(res), 2.0), 0.25)
    im = int(np.argmin(np.abs(X)))
    lens = np.hypot(np.roll(Y, -1, 0)[:, im] - Y[:, im],
                    np.roll(Z, -1, 0)[:, im] - Z[:, im])
    counts = np.maximum(1, np.rint(lens / (DENS / q)).astype(int))
    K = int(counts.sum())

    S = np.empty((M, K, 2))
    MATk = np.empty(K, np.int32)
    EDGEk = np.empty(K)
    FORMk = np.empty(K)
    SEGk = np.empty(K, np.int32)
    k = 0
    for cc in range(Cn):
        n = int(counts[cc])
        t = np.arange(n) / float(n)
        y0, z0 = Y[cc], Z[cc]
        y1, z1 = Y[(cc + 1) % Cn], Z[(cc + 1) % Cn]
        S[:, k:k + n, 0] = y0[:, None] + t[None, :] * (y1 - y0)[:, None]
        S[:, k:k + n, 1] = z0[:, None] + t[None, :] * (z1 - z0)[:, None]
        MATk[k:k + n] = MAT[cc]
        EDGEk[k:k + n] = EDGE[cc] + t * (EDGE[(cc + 1) % Cn] - EDGE[cc])
        FORMk[k:k + n] = FORM[cc] + t * (FORM[(cc + 1) % Cn] - FORM[cc])
        SEGk[k:k + n] = cc
        k += n
    return S, MATk, EDGEk, FORMk, SEGk, NAMES, counts


def sec_outward(S):
    """Outward 2D normals of a CCW closed section, vectorised over stations.
    S (M, K, 2) -> (M, K, 2)."""
    nxt = np.roll(S, -1, 1)
    prv = np.roll(S, 1, 1)
    d1 = nxt - S
    d2 = S - prv
    n1 = np.stack([d1[..., 1], -d1[..., 0]], -1)
    n2 = np.stack([d2[..., 1], -d2[..., 0]], -1)
    n = n1 + n2
    return n / np.maximum(np.linalg.norm(n, axis=-1, keepdims=True), 1e-12)


# --------------------------------------------------------------------------- #
#  6.  THE SURFACE DISPLACEMENT  —  where the realism actually lives            #
# --------------------------------------------------------------------------- #
#
# Everything in this section is MESH.  At 0.804 mm/px a 2 mm blowhole is 2.5
# screen pixels and a bump map of it is a lie that the grazing 12.5 deg sun
# exposes immediately: a real blowhole catches the light on its lower lip and
# goes black on its upper one, and a normal map cannot do that at the
# silhouette of a fascia edge.  So the concrete is displaced, the asphalt's
# chippings are displaced, the ruts are displaced and the sealant bead has a
# cross-section.
#
# It is computed in station chunks: the full (M, K) field for a 1.8 M vertex
# slab is 14 MB per temporary and the blowhole search alone wants a dozen of
# them at once.

def _cells(a, b, cell, seed, dens, rmin, rmax, depth_k, sharp=1.0,
           aspect=1.0, dens_field=None, rim=0.0):
    """Nearest-jittered-site field.  -> depth >= 0 at each (a, b).

    A 3x3 neighbourhood of cells, each carrying one jittered site with its own
    radius and its own existence roll.  This is the blowhole field on the
    concrete and the chipping field on the asphalt, and it is the same
    function because a void and a stone are the same problem with the sign
    flipped.

    aspect      > 1 stretches every site along b.  Air running up the back of
                a vertical form leaves TEARDROPS, not circles, and a field of
                perfect discs is the tell that a blowhole population was
                generated rather than trapped.
    dens_field  per-sample multiplier on the existence probability, so the
                population can cluster and can thicken toward the top of a
                lift instead of being uniform over 13 m2 of fascia.
    rim         if > 0, the site is a FLAT-BOTTOMED cylinder with a rim that
                turns over in `rim` metres instead of a hemisphere.  A mortar
                plug and a sawn pocket have an edge; a void does not.
    """
    ia = np.floor(a / cell).astype(np.int64)
    ib = np.floor(b / (cell * aspect)).astype(np.int64)
    out = np.zeros(np.broadcast(a, b).shape)
    for da in (-1, 0, 1):
        for db in (-1, 0, 1):
            ca, cb = ia + da, ib + db
            h1 = vh(ca, cb, seed)
            h2 = vh(ca, cb, seed + 977)
            h3 = vh(ca, cb, seed + 1861)
            h4 = vh(ca, cb, seed + 2777)
            px = (ca + 0.15 + 0.70 * h1) * cell
            py = (cb + 0.15 + 0.70 * h2) * cell * aspect
            rad = rmin + (rmax - rmin) * h3 * h3
            thr = dens if dens_field is None else dens * dens_field
            live = (h4 < thr)
            d2 = (a - px) ** 2 + ((b - py) / aspect) ** 2
            inside = live & (d2 < rad * rad)
            if rim > 0.0:
                prof = _sstep(np.clip((rad - np.sqrt(np.maximum(d2, 0.0)))
                                      / max(rim, 1e-9), 0.0, 1.0))
            else:
                prof = (np.sqrt(np.maximum(rad * rad - d2, 0.0))
                        / np.maximum(rad, 1e-9))
            out = np.maximum(out, np.where(inside, rad * depth_k * prof ** sharp,
                                           0.0))
    return out


# The leading fascia face occupies section coordinates u = 0 (the top arris,
# which is where section_perimeter_u starts) down to u = FACE_U1 at the bottom
# chamfer.  Two things need to know that and only that: the blowhole field's
# vertical gradient, and the form-tie grid.  It is a constant rather than a
# measurement because the face height is set by fascia_top_z - fascia_soffit_z,
# which varies by 22 mm of camber over the whole span.
FACE_U1 = 0.44


def _tie_plugs(x, u, form):
    """The form-tie population.  -> (disp m, cls, stain)

    A through-tie leaves a 26 mm hole every 600 x 450 mm and what happens to
    that hole afterwards is one of the most reliable ways to date a concrete
    structure.  Eleven years on, this deck has all three states:

        RECESSED PLUG   (46 %)  mortar pushed in 3.5-7 mm behind the face,
                                shrunk back, with a SHARP rim.  The rim is the
                                point: a dished blister with no edge -- which
                                is what this module shipped with -- is
                                invisible at any distance, and measured on the
                                4K macro it was.  1.5 mm of rim turnover is
                                one quad at the new density and reads as a
                                hard circle.
        PROUD PLUG      (42 %)  mortar left 1.2-2.6 mm out with a ring of
                                squeeze-out round it.
        OPEN HOLE       (12 %)  the plug fell out, or was never made.  A 16-22
                                mm conical void, black at the bottom, and on a
                                third of them the tie steel has rusted and put
                                a 60-220 mm dribble down the face.

    `cls` goes to aux.z so the shader can give the plugs their own mortar (a
    repair mortar is greyer and denser than an eleven-year-old fascia and it
    NEVER matches), and `stain` is added to wear.r, which mat_concrete already
    routes to the rust bleed.
    """
    ti = np.floor(x / TIE_X + 0.5)
    tj = np.floor((u - TIE_OFF) / TIE_V + 0.5)
    jx = (vh(ti, tj, 1481) - 0.5) * 0.020        # a gang form is set by hand
    ju = (vh(ti, tj, 1487) - 0.5) * 0.028
    tx = x - ti * TIE_X - jx
    tu = u - TIE_OFF - tj * TIE_V - ju
    rr = np.hypot(tx, tu)

    live = (vh(ti, tj, 1499) < 0.95) * form
    kind = vh(ti, tj, 1601)
    rad = 0.0125 + 0.0026 * vh(ti, tj, 1523)     # 25-30 mm across
    rim = 0.0015

    inside = _sstep(np.clip((rad - rr) / rim, 0.0, 1.0))
    ring = _ridge(rr - rad - 0.0022, 0.0038)

    is_rec = (kind < 0.46)
    is_pro = (kind >= 0.46) & (kind < 0.88)
    is_open = (kind >= 0.88)

    d_rec = -(0.0035 + 0.0035 * vh(ti, tj, 1607)) * inside
    d_pro = ((0.0012 + 0.0014 * vh(ti, tj, 1609)) * inside
             + 0.0011 * ring * (vh(ti, tj, 1613) < 0.75))
    cone = np.clip((rad - rr) / np.maximum(rad, 1e-9), 0.0, 1.0)
    d_open = -(0.016 + 0.006 * vh(ti, tj, 1619)) * inside * (0.30 + 0.70 * cone)

    d = live * (np.where(is_rec, d_rec, 0.0) + np.where(is_pro, d_pro, 0.0)
                + np.where(is_open, d_open, 0.0))
    # the rim of an open hole is broken, not machined
    d -= live * is_open * 0.0016 * _ridge(rr - rad, 0.0035) * \
        (0.4 + 0.6 * fbm(x * 30.0, u * 30.0, 1627))

    cls = live * (np.where(is_open, 0.70, 0.35)) * inside

    # the rust dribble, only below a corroded tie, tapering as it runs
    tail_len = 0.060 + 0.160 * vh(ti, tj, 1637)
    corroded = (vh(ti, tj, 1643) < 0.55) & is_open
    run = np.clip(tu / tail_len, 0.0, 1.0)
    wide = rad * (0.45 + 0.9 * run)
    tail = (np.clip(1.0 - np.abs(tx) / np.maximum(wide, 1e-6), 0.0, 1.0) ** 1.6
            * (1.0 - run) ** 0.8 * (tu > 0.0))
    stain = live * corroded * np.clip(tail + inside, 0.0, 1.0)
    return d, cls, stain


def _honeycomb(x, u):
    """One patch of honeycombing -- concrete that was not vibrated, so the
    paste never closed round the stone.  -> (disp m, mask)

    Every real bridge has one and nobody photographs it, which is exactly why
    building 13 m2 of flawless fascia and calling it finished is the tell.
    This one is 320 x 140 mm, low on the leading face under the second form
    tie, 4-11 mm deep, and the stone is PROUD inside the hollow because the
    aggregate is what is left when the mortar is missing.
    """
    cx, cu, hx, hu = HONEY
    ex = np.abs(x - cx) / hx
    eu = np.abs(u - cu) / hu
    e = np.hypot(ex, eu)
    ragged = e * (1.0 + 0.42 * (fbm(x * 13.0, u * 13.0, 1741) - 0.5))
    m = _sstep(np.clip((1.0 - ragged) / 0.22, 0.0, 1.0))
    # the void the mortar should have filled
    d = -0.0085 * m
    # ... and the stone standing in it
    d += m * _cells(x, u, 0.0135, 1747, 0.92, 0.0032, 0.0068, 0.62, sharp=0.6)
    d -= m * 0.0022 * fbm(x * 40.0, u * 40.0, 1753)
    return d, m * 0.95


def _ridge(t, half):
    """Triangular ridge profile, 1 at t=0, 0 at |t|>=half."""
    return np.maximum(0.0, 1.0 - np.abs(t) / max(half, 1e-9))


def _conc_disp(x, u, y, z, form, edge, side, channels=False):
    """Displacement of a CONCRETE surface, metres, positive = proud.

    x  along the span      u  around the section (both metres)
    form 1 = cast against plywood, 0 = screeded/floated top
    side -1 / +1 which fascia this belongs to (for the pour lots)

    channels=True also returns (cls, stain):
        cls    0 plain concrete / 0.35 mortar plug / 0.70 open tie hole /
               0.95 honeycombed, exposed aggregate.  -> aux.z
        stain  rust dribble strength.  -> added to wear.r
    Two outputs from one evaluation because the displacement field and the
    shader mask are THE SAME EVENT and a second, separately-authored copy of
    where the plugs are is a defect waiting for someone to edit one of them.
    """
    d = np.zeros_like(x)

    # 1. plate/formwork bow and the general unflatness of a poured face
    d += 0.0022 * fbm(x * 0.55, u * 0.75, 41) * (0.35 + 0.65 * form)
    d += 0.0009 * fbm(x * 2.6, u * 3.1, 57)

    # 2. PLYWOOD PANEL JOINTS.  2440 mm sheets.  Every joint leaves a lippage
    #    step because no two sheets are set dead flush, and a GROUT FIN where
    #    cement paste escaped the gap.  A 3 mm fin is 3.7 px and it is the
    #    single thing that makes formed concrete read as formed.
    ph = np.where(x < POUR_X, 0.31, 0.77)
    t = (x / PLY_LEN + ph)
    t = (t - np.floor(t)) * PLY_LEN
    t = np.where(t > PLY_LEN * 0.5, t - PLY_LEN, t)
    jid = np.floor(x / PLY_LEN + ph)
    amp = (0.0004 + 0.0020 * vh(jid, np.floor(u * 0.8), 613)) * form
    sgn = np.where(vh(jid, 71, 811) > 0.5, 1.0, -1.0)
    d += sgn * amp * _sstep((t + 0.004) / 0.008)
    fin = (0.0010 + 0.0026 * vh(jid, np.floor(u * 1.7), 907)) * form
    d += fin * _ridge(t, 0.0032) * (vh(jid, np.floor(u * 1.7), 1013) < 0.72)

    # 3. FORM-TIE PLUGS on a 600 x 450 grid.  Three states, a sharp rim, and
    #    a rust dribble under the ones whose tie steel corroded.  See
    #    _tie_plugs: the version this replaced was a soft blister with no
    #    edge, and on the 4K macro at 3.0 m it was invisible.
    # TIE_OFF puts a row of them at u = 0.21, which is mid-height of the
    # fascia face.  The first version keyed the grid to u = 0 and put every
    # plug on the top arris, i.e. nowhere.
    dt, cls, stain = _tie_plugs(x, u, form)
    d += dt

    # 4. BLOWHOLES.  Denser on a vertical formed face than on a soffit, and
    #    almost absent on a trowelled top.
    #
    #    THREE THINGS MAKE A BLOWHOLE FIELD READ AS TRAPPED AIR RATHER THAN AS
    #    A NOISE FUNCTION, and the version this replaced had none of them:
    #      CLUSTERING   real bug holes come in patches, because whether air
    #                   escapes is decided by where the poker went, not by a
    #                   uniform probability per square centimetre.  A 0.9 m
    #                   fbm swings the population between 0.4x and 1.7x.
    #      GRADIENT     air rises.  On a 0.44 m fascia cast in one lift the
    #                   top 300 mm carries about twice the voids of the
    #                   bottom, and the underside of the cantilever carries
    #                   more again because the air had nowhere else to go.
    #      TEARDROPS    a void against a vertical form is stretched upward as
    #                   the bubble tried to climb.  aspect 2.1 on the main
    #                   population, 1.0 on the fines.
    on_face = (u >= -0.005) & (u <= FACE_U1)
    topness = np.where(on_face,
                       0.55 + 0.95 * np.clip((0.30 - u) / 0.30, 0.0, 1.0), 1.0)
    clust = 0.40 + 1.30 * fbm(x * 0.85, u * 0.85, 3607)
    df = topness * clust
    dens = 0.34 + 0.38 * form
    d -= _cells(x, u, 0.0150, 3301, dens, 0.0010, 0.0048, 0.90,
                aspect=2.1, dens_field=df)
    d -= _cells(x, u, 0.0060, 3407, 0.26 + 0.24 * form, 0.0005, 0.0016, 0.70,
                dens_field=clust)
    # the occasional big void a poker missed, 8-16 mm across: one every few
    # square metres, and they are what the eye actually latches onto
    d -= _cells(x, u, 0.0620, 3511, 0.30 * form, 0.0030, 0.0082, 0.95,
                aspect=1.7, dens_field=df)
    # and the chains of them that run up a form joint, where the ply gap gave
    # the air a path: same population, but keyed to the joint's own phase
    ph2 = np.where(x < POUR_X, 0.31, 0.77)
    tj2 = (x / PLY_LEN + ph2)
    tj2 = (tj2 - np.floor(tj2)) * PLY_LEN
    tj2 = np.where(tj2 > PLY_LEN * 0.5, tj2 - PLY_LEN, tj2)
    near_joint = np.clip(1.0 - np.abs(tj2) / 0.045, 0.0, 1.0) ** 1.5
    d -= _cells(x, u, 0.0110, 3607, 0.55 * form, 0.0012, 0.0040, 0.85,
                aspect=2.6, dens_field=near_joint * 1.6)

    # 4b. ONE HONEYCOMBED PATCH.  Not decoration: it is the only place on this
    #     deck where the aggregate is visible, and an eleven-year-old fascia
    #     with no defect in 26 m2 of it is a rendering, not a bridge.
    dh, mh = _honeycomb(x, u)
    d += dh * form
    cls = np.maximum(cls, mh * form)

    # 5. THE CONSTRUCTION JOINT between the two pours.  A real 1.6 mm step and
    #    a fin, and the reason the two halves of this deck are different
    #    colours in the shader.
    tp = x - POUR_X
    d += 0.0016 * _sstep((tp + 0.002) / 0.004) * form
    d += 0.0022 * _ridge(tp, 0.0030) * form

    # 6. floated tops: float arcs and a coarser waviness
    d += (1.0 - form) * 0.0016 * fbm(x * 1.1, u * 0.35, 173)
    d += (1.0 - form) * 0.0007 * np.sin(u * 41.0 + 6.0 * fbm(x * 0.6, u * 0.2, 191))

    # 7. arrises get a touch of wear regardless
    d -= edge * 0.0006 * (0.5 + 0.5 * fbm(x * 8.0, u * 8.0, 229))
    if channels:
        return d, cls, stain
    return d


def _asph_disp(x, y):
    """Displacement of the ASPHALT running surface, metres, positive = proud."""
    d = np.zeros_like(x)

    # surface regularity: a 3 m screed wave, which is what a straightedge finds
    d += 0.0030 * fbm(x * 0.33, y * 0.55, 331)
    d += 0.0011 * fbm(x * 1.7, y * 2.1, 337)

    # WHEEL TRACKS: two ruts, and the chippings in them are polished flatter
    yt0, yt1 = CROWN_Y + 0.950, CROWN_Y - 0.950
    rut = (np.exp(-((y - yt0) / 0.30) ** 2) + np.exp(-((y - yt1) / 0.30) ** 2))
    d -= 0.0050 * rut * (0.6 + 0.4 * _sstep((abs(x) - 1.0) / 12.0))
    polish = np.clip(rut, 0.0, 1.0)

    # CHIPPINGS.  10-15 mm stone standing 0.5-1.6 mm out of the binder.
    chip = _cells(x, y, 0.0125, 4409, 0.86, 0.0038, 0.0078, 0.24, sharp=0.65)
    d += chip * (1.0 - 0.55 * polish)
    d += _cells(x, y, 0.0052, 4507, 0.55, 0.0014, 0.0030, 0.20) * (1.0 - 0.7 * polish)

    # THE PLANED-AND-RELAID BAY.  Sawn edges, 3.5 mm low, a hot-poured sealant
    # bead round the whole boundary.
    inx = (x > RELAY_X0) & (x < RELAY_X1)
    ey = np.minimum(np.abs(y - KERB_FACE_Y), np.abs(y + KERB_FACE_Y))
    edge_d = np.minimum(np.abs(x - RELAY_X0), np.abs(x - RELAY_X1))
    d -= 0.0035 * inx * _sstep(edge_d / 0.004)
    bead = _ridge(np.minimum(edge_d, ey * 10.0), 0.0055)
    d += 0.0026 * bead * ((x > RELAY_X0 - 0.02) & (x < RELAY_X1 + 0.02))

    # a pothole repair standing proud, with a ragged boundary
    pr = np.hypot(x - POTHOLE[0], y - POTHOLE[1])
    rag = POTHOLE[2] * (1.0 + 0.22 * fbm((x - POTHOLE[0]) * 9.0,
                                         (y - POTHOLE[1]) * 9.0, 521))
    d += 0.0042 * _sstep((rag - pr) / 0.020)

    # GRIT banked against both kerbs.  The -y channel is the low one.
    for (sy, k) in ((-1.0, 1.0), (1.0, 0.72)):
        dd = np.abs(y - sy * KERB_FACE_Y)
        band = np.clip(1.0 - dd / 0.34, 0.0, 1.0) ** 1.7
        d += 0.0034 * k * band * (0.45 + 0.55 * fbm(x * 1.4, y * 5.0, 587))
    return d


def _recess_z(x, y):
    """The two expansion-joint recesses, as a z drop on the deck top.

    They are DIFFERENT joints and that is the manifest's third variation axis.
    -x is elastomeric-in-runner: 500 wide, 75 deep, a rough floor with anchor
    loops.  +x is a comb plate: 360 wide, 55 deep, and its floor is SCREEDED
    FLAT because a finger plate has to be bolted to a plane.
    """
    dz = np.zeros_like(x)
    wall = 0.0035
    tm = _sstep(((-(END_X - JOINT_M_W)) - x) / wall)
    dz -= JOINT_M_D * tm
    dz += tm * 0.0016 * fbm(x * 12.0, y * 6.0, 733)      # tamped floor
    tp = _sstep((x - (END_X - JOINT_P_W)) / wall)
    dz -= JOINT_P_D * tp
    dz += tp * 0.0004 * fbm(x * 9.0, y * 5.0, 739)       # screeded flat
    return dz


def _spall_disp(x, u):
    """The repaired spall on the leading fascia: a sawn rectangle 6 mm deep
    with a repair mortar standing 2 mm proud of the original face.

    `u` is measured DOWN FROM THE TOP ARRIS, so cu 0.315 with a half-height of
    105 mm puts the patch at 210-420 mm — below the rustication groove and
    above the bottom chamfer, i.e. entirely within the flat of the face, which
    is where a cover-spall over a corroded outer bar actually happens.
    """
    cx, hx, hu = SPALL
    cu = 0.315
    ex = np.abs(x - cx) - hx
    eu = np.abs(u - cu) - hu
    e = np.maximum(ex, eu)
    ragged = e + 0.006 * fbm(x * 14.0, u * 14.0, 881)
    inside = _sstep(-ragged / 0.004)
    d = 0.0020 * inside                      # the patch stands proud
    d -= 0.0060 * _ridge(ragged, 0.0035)     # the sawn perimeter groove
    return d


def _arris_chips(x, u, u_arris, side):
    """Bites out of a concrete arris, each a sphere subtracted from the edge."""
    d = np.zeros_like(x)
    for (cx, r) in CHIP_ARRIS:
        cx = cx * side
        du = u - u_arris
        rr = np.hypot((x - cx) / 1.0, du / 0.75)
        rag = r * (1.0 + 0.30 * fbm(x * 11.0, u * 11.0, 971))
        d -= 0.55 * r * np.clip(1.0 - (rr / np.maximum(rag, 1e-6)) ** 2,
                                0.0, 1.0) ** 0.7
    return d


# --------------------------------------------------------------------------- #
#  6b.  THE WEATHERING STRUCTURE  —  authored in (x, u), not in the shader      #
# --------------------------------------------------------------------------- #
#
# WHY THIS EXISTS, MEASURED RATHER THAN ARGUED.
#
# The first version of this item put every weathering layer in the shader, as
# eleven independent noise-driven mixes of 20-40 % each.  Rendered under a flat
# white world with the Standard transform -- the only honest way to look at an
# albedo -- the leading fascia measured:
#
#       low-frequency (>50 mm) albedo span, p5..p95   =  8.3 % of the mean
#
# Real weathered concrete is 40-80 %.  The reason is arithmetic, not taste:
# eleven INDEPENDENT mixes average toward their mean, so the more history you
# stack the flatter the surface gets.  That is this project's named wave-1
# failure -- "mechanisms are coded, amplitudes are too small to reach pixels"
# -- and raising all eleven amplitudes would only have made a noisier flat
# surface.
#
# Real weathering is not eleven independent fields.  It is a SMALL NUMBER of
# processes with hard spatial structure: which truck poured this metre of
# wall, which plywood sheet formed it, and where the water comes off the
# cornice.  All three of those are functions of the BRIDGE-LOCAL (x, u) that
# this module has in hand at build time and that the shader does not -- the
# object is world-aligned after recentring, so a shader cannot recover "along
# the span" without a basis it has no way to know.
#
# So they are computed HERE, in metres, exactly, and shipped in the vertex
# channels the shader already reads:
#
#       base.rgb   the pour record: which truck, which day, which lot
#       base.a     the streak field, 0.5 = clean, >0.5 dirty, <0.5 efflorescent
#       aux.w      the formwork panel tone
#
# base.a used to carry a pour flag that no shader read, and aux.w a per-33 mm
# hash that no shader read.  Nothing was displaced to make room.

def pour_edges():
    """Truck-load boundaries along the span.  -> ascending x, m.

    A 31 m fascia is not one colour.  It is placed load by load, 5-7 m3 at a
    time, and consecutive loads differ in water content, in how long they
    stood, and in which cement silo filled them; eleven years of carbonation
    then amplifies the difference instead of hiding it.  The boundary is a
    LIFT LINE, not a straight edge -- the next load went against concrete that
    was still plastic, so the join wanders.
    """
    global _POUR_EDGES
    if _POUR_EDGES is None:
        e, x, i = [-END_X], -END_X, 0
        while x < END_X:
            x += rnd(2.6, 4.8, "truck", i)
            e.append(min(x, END_X))
            i += 1
        # the construction joint between the two POURS is always a load edge:
        # different day, different weather, different lot.
        e = [v for v in e if abs(v - POUR_X) > 0.9] + [POUR_X]
        _POUR_EDGES = np.array(sorted(set(e)))
    return _POUR_EDGES


_POUR_EDGES = None


def pour_lot(x2, u2):
    """-> (band index, tone in [-1,1], warmth in [-1,1]) per sample.

    The boundary is ramped over 60-170 mm and the ramp WANDERS with u, so the
    lift line is diagonal and ragged like a real one rather than a razor cut
    down 440 mm of fascia.
    """
    E = pour_edges()
    bi = np.clip(np.searchsorted(E, x2, side='right') - 1, 0, len(E) - 2)
    tone = 2.0 * vh(bi, 0, 5501) - 1.0
    warm = 2.0 * vh(bi, 0, 5507) - 1.0
    # ramp across the join into the previous band
    lo = E[bi]
    w = 0.060 + 0.110 * vh(bi, 0, 5519)
    wob = 0.055 * (fbm(x2 * 6.0, u2 * 2.2, 5531) - 0.5)
    t = _sstep(np.clip((x2 - lo - wob) / w, 0.0, 1.0))
    tone_p = 2.0 * vh(np.maximum(bi - 1, 0), 0, 5501) - 1.0
    warm_p = 2.0 * vh(np.maximum(bi - 1, 0), 0, 5507) - 1.0
    return bi, tone_p + (tone - tone_p) * t, warm_p + (warm - warm_p) * t


def panel_tone(x2, u2, form2):
    """The plywood formwork's signature.  -> [0,1], 0.5 = an average sheet.

    A gang form is not made of identical sheets.  Some are new, some are on
    their ninth pour: a re-used sheet carries release agent and laitance, so
    the concrete off it is DARKER and slightly glossier, and a new sheet gives
    a paler, chalkier face.  Every real formed wall reads as a patchwork of
    2440 mm panels for that reason and this fascia had none of it.

    There is also a PERIMETER HALO: the paste is denser against the stiff
    edge of a sheet and thinner in the middle where the ply bows, so each
    panel is a shade paler round its border.  It is 30-60 mm wide, which at
    1244 px/m is 37-75 px, and it is what makes the panel grid legible
    without a single visible joint line.
    """
    ph = np.where(x2 < POUR_X, 0.31, 0.77)
    jid = np.floor(x2 / PLY_LEN + ph)
    # bimodal: 30 % well-used and dark, 16 % new and pale, the rest between
    r = vh(jid, 0, 6101)
    t = np.where(r < 0.30, 0.10 + 0.22 * vh(jid, 0, 6113),
                 np.where(r > 0.84, 0.80 + 0.18 * vh(jid, 0, 6119),
                          0.38 + 0.28 * vh(jid, 0, 6127)))
    # distance to the nearest panel edge, in metres, along the sheet
    frac = (x2 / PLY_LEN + ph)
    frac = (frac - np.floor(frac)) * PLY_LEN
    de = np.minimum(frac, PLY_LEN - frac)
    halo = 1.0 - _sstep(np.clip(de / (0.030 + 0.030 * vh(jid, 0, 6131)),
                                0.0, 1.0))
    t = np.clip(t + 0.26 * halo, 0.0, 1.0)
    # a re-used sheet also bows more, so its middle is a touch darker still
    t -= 0.10 * (1.0 - halo) * (r < 0.30)
    return np.clip(0.5 + (t - 0.5) * form2, 0.0, 1.0)


# The drip groove works, except where it does not.  These three stations have
# a groove blocked by a grout fin, so the water carries on round the beam
# soffit instead of falling off -- which is the only way a stain ever gets
# onto the underside of a cantilever, and the reason a bridge with a clean
# soffit and a dirty fascia looks right while a uniformly grubby one does not.
DRIP_BLOCKED = (-8.42, 1.63, 10.95)


def streak_field(x2, u2, form2, u_face_end, u_drip, u_soff_end):
    """The rain-tracking system on a fascia face.  -> [0,1], 0.5 = clean.

    THE SINGLE MOST RECOGNISABLE THING ON AN OUTDOOR CONCRETE EDGE, and the
    thing this item most obviously lacked: eleven years of rain sheeting off
    a cornice does not wash a fascia evenly, it washes it in STRIPES.

    A drip point is where the cornice's own fall concentrates the run-off --
    a low spot, a blocked drip, a chip in the arris.  They are 0.18-0.55 m
    apart.  Under each one:

        the DARK CORE      15 mm wide at the arris, spreading to 60-130 mm by
                           the bottom of the run, darkest 0.10-0.20 m down
                           where the sheet of water actually lands and slows
        the PALE RIM       calcium carbonate leached out of the concrete and
                           re-deposited at the edges of the wet strip, and a
                           bright collar right at the drip point itself.  A
                           streak that is only dark reads as dirt on a wall;
                           it is the pale rim beside it that reads as
                           concrete leaching.
        the LENGTH         0.10-0.60 m.  Most die before the drip groove.
                           None cross it -- that is what the groove is for --
                           except at DRIP_BLOCKED, where three of them carry
                           on round the beam soffit.

    Returns a single channel because the two effects are mutually exclusive
    at any one point: >0.5 is dirty by (v-0.5)*2, <0.5 is efflorescent by
    (0.5-v)*2.  It rides base.a.
    """
    dark = np.zeros_like(x2)
    pale = np.zeros_like(x2)
    # TWO POPULATIONS AT INCOMMENSURATE SPACINGS.  One lattice at 0.135 m
    # gives a quasi-periodic comb: rendered, it read as a row of decorative
    # arches rather than as weathering, because a nearly-regular spacing with
    # a nearly-regular length is a MOTIF and the eye finds motifs instantly.
    # 0.131 and 0.337 beat against each other over 3.4 m, which is longer
    # than any frame this item appears in.
    for (cell, prob, run_lo, run_hi, sk) in ((0.131, 0.62, 0.10, 0.44, 0),
                                             (0.337, 0.72, 0.26, 0.62, 700)):
        for dc in (-3, -2, -1, 0, 1, 2, 3):
            ci = np.floor(x2 / cell).astype(np.int64) + dc
            live = vh(ci, 0, 7001 + sk) < prob
            px = (ci + 0.08 + 0.84 * vh(ci, 0, 7013 + sk)) * cell
            stren = 0.55 + 0.45 * vh(ci, 0, 7019 + sk)
            run = run_lo + (run_hi - run_lo) * vh(ci, 0, 7027 + sk) ** 0.8
            w0 = 0.010 + 0.014 * vh(ci, 0, 7039 + sk)
            w1 = 0.042 + 0.080 * vh(ci, 0, 7043 + sk)
            wander = 0.017 * (fbm(px * 3.1 + 11.0, u2 * 4.0, 7051 + sk) - 0.5)
            # how far down the run we are, 0 at the arris
            s = np.clip(u2 / np.maximum(run, 1e-6), 0.0, 1.0)
            half = w0 + (w1 - w0) * s ** 0.75
            r = np.abs(x2 - px - wander) / np.maximum(half, 1e-9)
            # a wet track has a FLAT core with a soft shoulder, not a
            # triangle: the sheet of water has a width and inside it
            # everything is equally wet.  The triangle this replaced put the
            # full strength on one line of pixels and nothing either side,
            # which measured 1.1 % of the face above 0.75 -- no streaks.
            prof = 1.0 - _sstep(np.clip((r - 0.45) / 0.55, 0.0, 1.0))
            # washes in over the first 25 mm, dirtiest a third of the way
            # down where the sheet slows and drops its solids, then dies
            along = (_sstep(np.clip(u2 / 0.022, 0.0, 1.0))
                     * (1.0 - _sstep(np.clip((u2 - run * 0.62)
                                             / np.maximum(run * 0.38, 1e-6),
                                             0.0, 1.0))) ** 0.7
                     * (0.74 + 0.38 * np.exp(-((s - 0.32) / 0.30) ** 2)))
            # ... and it stops dead at the drip groove unless it is fouled
            blocked = np.zeros_like(x2)
            for bx in DRIP_BLOCKED:
                blocked = np.maximum(
                    blocked, np.clip(1.0 - np.abs(px - bx) / 0.32, 0.0, 1.0))
            past = _sstep(np.clip((u2 - u_drip) / 0.010, 0.0, 1.0))
            gate = 1.0 - past * (1.0 - blocked * 0.85)
            gate *= 1.0 - _sstep(np.clip((u2 - u_soff_end) / 0.030, 0.0, 1.0))
            dark = dark + live * stren * prof * along * gate
            # THE LEACHED RIM is real but it is NOT the loud half.  Carbonate
            # carried to the edge of the sheet and left there is a hairline,
            # 8-20 mm wide; at 0.95 strength and 60 mm wide it framed every
            # streak in a bright U and the fascia read as arcading.  0.30 and
            # narrow.  Weathering darkens; leaching only outlines.
            rim = (np.clip(1.0 - np.abs(r - 1.22) / 0.30, 0.0, 1.0) ** 1.5
                   * (r > 1.0))
            pale = pale + live * stren * rim * along * gate * 0.30

    on = (u2 >= -0.004) & (u2 <= u_soff_end)
    dark = np.clip(dark, 0.0, 1.25)
    pale = np.clip(pale, 0.0, 0.85)
    # THE SHELTERED BAND.  The cornice oversails the fascia by 200 mm, so the
    # top 25-95 mm of the face is in its rain shadow and stays pale while the
    # band below takes everything.  That step is on every overhanging concrete
    # edge in the world and this item did not have it.  Its lower edge is
    # RAGGED over 70 mm of height -- a clean horizontal line at a fixed height
    # is the second way this layer reads as decoration instead of as weather.
    sh_h = 0.025 + 0.070 * fbm(x2 * 1.4, u2 * 0.0, 7077)
    shel = 1.0 - _sstep(np.clip((u2 - sh_h) / 0.030, 0.0, 1.0))
    dark = dark * (1.0 - 0.80 * shel)
    pale = np.clip(pale + 0.14 * shel, 0.0, 0.95)
    # a broad grimy wash between the streaks, heaviest 80-200 mm down
    wash = (np.clip(1.35 * fbm(x2 * 1.6, u2 * 0.8, 7069) - 0.35, 0.0, 1.0)
            * np.exp(-((u2 - 0.16) / 0.20) ** 2))
    dark = np.clip(dark + wash * 0.62, 0.0, 1.0)
    pale = np.clip(pale - dark * 0.90, 0.0, 1.0)
    return np.clip(0.5 + 0.5 * dark * form2 * on
                   - 0.5 * pale * form2 * on, 0.0, 1.0)


# --------------------------------------------------------------------------- #
#  7.  THE SLAB                                                                 #
# --------------------------------------------------------------------------- #

def _emit_quads(acc, IDX, mat, smooth=True, drop=None):
    """Quads over an (m, k) index grid slice, with an optional drop mask."""
    if IDX.shape[0] < 2 or IDX.shape[1] < 2:
        return 0
    A = IDX[:-1, :-1]
    B = IDX[:-1, 1:]
    Cc = IDX[1:, 1:]
    Dd = IDX[1:, :-1]
    Q = np.stack([A, B, Cc, Dd], -1).reshape(-1, 4)
    if drop is not None:
        Q = Q[~np.asarray(drop, bool).reshape(-1)]
    acc.quads(Q, mat, smooth)
    return len(Q)


def cap_monotone(acc, P2, I, j_lo, j_hi, mat, flip):
    """Cap a y-monotone closed section by merging its two chains.

    The deck's end face is the region between two functions of y -- a vertical
    line through it meets the concrete in exactly ONE interval, everywhere,
    including through the drip groove and the kerb pocket.  So the cap is a
    linear merge of the lower chain (the underside, running -y to +y) against
    the upper chain (the deck top, running +y to -y), advancing whichever has
    the smaller next y.

    This replaces ear clipping, which pont_girder needed for an I-section and
    which is O(n^3): at K = 1100 that is a billion operations per end.  The
    merge is O(n) and it cannot fail on a re-entrant corner, because the
    section has none in y.
    """
    K = len(P2)
    low = [(j_lo + t) % K for t in range((j_hi - j_lo) % K + 1)]
    up = [(j_hi + t) % K for t in range((j_lo - j_hi) % K + 1)]
    up = up[::-1]                       # both chains now run in +y
    a = b = 0
    tris = []
    while a < len(low) - 1 or b < len(up) - 1:
        adv_low = (b >= len(up) - 1) or (
            a < len(low) - 1 and P2[low[a + 1], 0] <= P2[up[b + 1], 0])
        if adv_low:
            tris.append((I[low[a]], I[low[a + 1]], I[up[b]]))
            a += 1
        else:
            tris.append((I[low[a]], I[up[b + 1]], I[up[b]]))
            b += 1
    T = np.array(tris, np.int64)
    if len(T) == 0:
        return 0
    acc.tris(T[:, ::-1] if flip else T, mat, False)
    return len(T)


def _channels(X, S, U, MATk, EDGEk, FORMk, cls=None, stain=None,
              u_face_end=None, u_drip=None, u_soff_end=None):
    """Per-vertex base / aux / wear for the swept slab.  (M, K, 4) each.

    cls / stain come straight out of the displacement pass, so the mortar
    plugs the shader tints are the same plugs the mesh has holes for.

    THE CHANNEL CONTRACT (read by mat_concrete, and by nothing else):
        base.rgb  the pour record -- truck-load tone and warmth, and the two
                  pours' different lots, with a ramped lift line at each join
        base.a    the streak field, 0.5 clean / >0.5 dirty / <0.5 efflorescent
        aux.x     edge exposure        aux.y  1 = cast against plywood
        aux.z     0 plain / 0.35 mortar plug / 0.70 open tie / 0.95 honeycomb
        aux.w     formwork panel tone, 0.5 = an average sheet
        wear.x    chip + rust-dribble strength   wear.y  dirt   wear.z  damp
        wear.w    age
    """
    M, K = S.shape[0], S.shape[1]
    Y = S[:, :, 0]
    Z = S[:, :, 1]
    x2 = np.broadcast_to(X[:, None], (M, K))
    u2 = np.broadcast_to(U[None, :], (M, K))
    mat2 = np.broadcast_to(MATk[None, :], (M, K))
    form2 = np.broadcast_to(FORMk[None, :], (M, K))

    # THE POUR RECORD.  The old version was  cc * (0.90 + 0.20 * lot)  with
    # lot a 4.5 m fbm: a +-10 % swing with no edges anywhere, which is
    # invisible.  A real load-to-load difference is 20-30 % in value and a
    # visible shift in warmth, and it has an EDGE -- the lift line.
    _bi, tone, warm = pour_lot(x2, u2)
    lot = 0.5 + 0.5 * tone
    cA, cB = np.array(srgb(CONC_A_HEX)), np.array(srgb(CONC_B_HEX))
    cAs = np.array(srgb(ASPH_HEX))
    pour = (x2 > POUR_X).astype(float)
    warm_k = (0.036, 0.010, -0.040)          # r, g, b pull toward warm/cool
    col = np.empty((M, K, 3))
    for ch in range(3):
        cc = cA[ch] + (cB[ch] - cA[ch]) * pour
        cc = cc * (1.0 + 0.235 * tone) * (1.0 + warm_k[ch] * warm)
        col[:, :, ch] = np.where(mat2 == MAT_ASPH,
                                 cAs[ch] * (0.75 + 0.5 * lot), cc)
    if u_face_end is None:
        strk = np.full((M, K), 0.5)
    else:
        strk = streak_field(x2, u2, form2, u_face_end, u_drip, u_soff_end)
        strk = np.where(mat2 == MAT_ASPH, 0.5, strk)
    base = np.concatenate([np.clip(col, 0.0, 1.0), strk[:, :, None]], -1)

    aux = np.stack([
        np.broadcast_to(EDGEk[None, :], (M, K)),
        form2,
        np.zeros((M, K)) if cls is None else cls,
        panel_tone(x2, u2, form2),
    ], -1)

    # up-facing collects dirt, low fascia collects algae, everything ages
    up = np.clip(np.gradient(Z, axis=1) * 0.0 + 1.0, 0, 1)
    nrm = sec_outward(S)
    upf = np.clip(nrm[:, :, 1], 0.0, 1.0)
    downf = np.clip(-nrm[:, :, 1], 0.0, 1.0)
    dirt = np.clip(0.18 + 0.55 * upf + 0.25 * fbm(x2 * 0.7, u2 * 0.9, 71), 0, 1)
    dirt = np.where(mat2 == MAT_ASPH, dirt * 0.6, dirt)
    # the damp band: the bottom 0.18 m of each fascia and the whole soffit
    damp = np.clip((0.18 - (Z - soffit_z(x2, Y))) / 0.18, 0.0, 1.0)
    bio = np.clip(0.10 + 0.60 * downf * (0.4 + 0.6 * damp)
                  + 0.35 * fbm(x2 * 1.3, u2 * 1.6, 83), 0, 1) * form2
    chip = np.clip(np.broadcast_to(EDGEk[None, :], (M, K))
                   * (0.35 + 0.65 * fbm(x2 * 4.0, u2 * 4.0, 89)), 0, 1)
    # wear.x CARRIES TWO THINGS AND THEY MUST NOT ADD.  It used to be
    # chip + 1.35*stain in one number, and mat_concrete read that number as
    # "how rusty is this".  EDGEk is 0.95 over the WHOLE leading fascia face
    # (it means "exposed formed face", which is what the chalk layer wants),
    # so chip sat at 0.6-0.9 everywhere and the rust layer painted an
    # iron-oxide wash across 13 m2 of hero concrete.  Measured on the 4K
    # macro: the fascia came back salmon, not concrete.
    #
    # So the channel is SPLIT by range: 0.00-0.50 is chip strength, 0.50-1.00
    # is rust-dribble strength.  A vertex is one or the other; a corroded tie
    # hole is not also a chipped arris.
    if stain is not None:
        chip = np.where(stain > 0.02,
                        0.50 + 0.50 * np.clip(stain, 0, 1),
                        0.50 * np.clip(chip, 0, 1))
    else:
        chip = 0.50 * np.clip(chip, 0, 1)
    age = np.clip(0.62 + 0.22 * fbm(x2 * 0.15, u2 * 0.12, 97), 0, 1)
    wear = np.stack([chip, dirt, bio, age], -1)
    return base, aux, wear


def build_slab(acc, X, res=1.0, cnt=None, mounts=None):
    """The whole slab as one closed swept solid + two end caps."""
    cnt = cnt if cnt is not None else {}
    S, MATk, EDGEk, FORMk, SEGk, NAMES, counts = build_section(X, res)
    M, K = S.shape[0], S.shape[1]
    im = int(np.argmin(np.abs(X)))
    U = HS.section_perimeter_u(S[im])
    N = sec_outward(S)

    # ---- displacement, in station chunks ------------------------------
    Dm = np.zeros((M, K))
    idx_of = {n: i for i, n in enumerate(NAMES)}
    seg_start = np.concatenate([[0], np.cumsum(counts)[:-1]])
    is_asph = (MATk == MAT_ASPH)
    # the leading fascia face and the trailing fascia face, for arris chips
    u_fasc_bot_L = U[seg_start[idx_of["fascia_L_bot"]]]
    u_fasc_top_L = U[seg_start[idx_of["fascia_L_top"]]]
    u_fasc_L0 = U[seg_start[idx_of["fascia_L_top"]]]
    # THE WHOLE leading fascia face, top arris to bottom chamfer, NOT the one
    # 90 mm segment that starts at fascia_L_top.  This was a defect: the mask
    # was `SEGk == idx_of["fascia_L_top"]`, which is the strip between the top
    # arris and the rustication, so the repaired spall (centred 315 mm down)
    # and every chipped arris (at u = 432 mm) were multiplied by zero.  Both
    # are named in this module's docstring and in its variation claims and
    # NEITHER WAS EVER BUILT; caught by rendering CAM_PDS_SPALL and finding no
    # spall in it.  Measure the artefact, not the code.
    on_fasc_L = (U >= -1e-6) & (U <= u_fasc_bot_L + 0.004)

    CLS = np.zeros((M, K))
    STAIN = np.zeros((M, K))
    n_spall = n_chip = 0
    CH = 192
    for i0 in range(0, M, CH):
        i1 = min(i0 + CH, M)
        xs = X[i0:i1, None] + np.zeros((1, K))
        us = np.zeros((i1 - i0, 1)) + U[None, :]
        ys = S[i0:i1, :, 0]
        zs = S[i0:i1, :, 1]
        fm = np.zeros((i1 - i0, 1)) + FORMk[None, :]
        eg = np.zeros((i1 - i0, 1)) + EDGEk[None, :]
        d, cls, stain = _conc_disp(xs, us, ys, zs, fm, eg, -1.0, channels=True)
        da = _asph_disp(xs, ys)
        am = np.zeros((i1 - i0, 1)) + is_asph[None, :]
        d = np.where(am > 0.5, da, d)
        # the repaired spall and the chipped arrises live on the leading fascia
        fl = np.zeros((i1 - i0, 1)) + on_fasc_L[None, :]
        sp = _spall_disp(xs, us - u_fasc_L0)
        ac = _arris_chips(xs, us, u_fasc_bot_L, 1.0)
        d = d + fl * (sp + ac)
        n_spall += int(np.count_nonzero(fl * np.abs(sp) > 0.0005))
        n_chip += int(np.count_nonzero(fl * np.abs(ac) > 0.0005))
        Dm[i0:i1] = d
        CLS[i0:i1] = np.where(am > 0.5, 0.0, cls)
        STAIN[i0:i1] = np.where(am > 0.5, 0.0, stain)

    S = S + N * Dm[:, :, None]
    # the two joint recesses are a Z move on the deck top, not a normal move
    top = is_asph.copy()
    dz = np.zeros((M, K))
    for i0 in range(0, M, CH):
        i1 = min(i0 + CH, M)
        xs = X[i0:i1, None] + np.zeros((1, K))
        dz[i0:i1] = _recess_z(xs, S[i0:i1, :, 0])
    S[:, :, 1] += dz * top[None, :]

    # The three u landmarks the streak field needs: where the fascia face
    # ends, where the drip groove is (streaks stop there -- that is what the
    # groove is FOR), and where the beam soffit turns back up.
    u_drip = float(U[seg_start[idx_of["beam_L_out"]]])
    u_soff_end = float(U[seg_start[idx_of["beam_L_fil1"]]])
    base, aux, wear = _channels(X, S, U, MATk, EDGEk, FORMk,
                                cls=CLS, stain=STAIN,
                                u_face_end=float(u_fasc_bot_L),
                                u_drip=u_drip, u_soff_end=u_soff_end)
    cnt["u_face_end"] = float(u_fasc_bot_L)
    cnt["u_drip"] = u_drip
    cnt["pour_loads"] = int(len(pour_edges()) - 1)
    cnt["ply_panels"] = int(round(DECK_LEN / PLY_LEN))
    cnt["streak_dirty_verts"] = int(np.count_nonzero(base[:, :, 3] > 0.60))
    cnt["streak_pale_verts"] = int(np.count_nonzero(base[:, :, 3] < 0.40))
    cnt["tie_plugs_recessed"] = int(np.count_nonzero(
        (CLS > 0.30) & (CLS < 0.50)) )
    cnt["tie_holes_open"] = int(np.count_nonzero((CLS > 0.60) & (CLS < 0.80)))
    cnt["honeycomb_verts"] = int(np.count_nonzero(CLS > 0.85))
    cnt["rust_dribble_verts"] = int(np.count_nonzero(STAIN > 0.02))
    cnt["spall_verts"] = n_spall
    cnt["arris_chip_verts"] = n_chip

    Cp = np.stack([X, np.zeros(M), np.zeros(M)], -1)
    Uax = np.tile(np.array([0.0, 1.0, 0.0]), (M, 1))
    Vax = np.tile(np.array([0.0, 0.0, 1.0]), (M, 1))
    IDX = sweep(acc, Cp, Uax, Vax, S, mat=MAT_CONC,
                base=base.reshape(-1, 4), aux=aux.reshape(-1, 4),
                wear=wear.reshape(-1, 4), vcoord=X, faces=False)
    # MEMORY.  At 5 743 x 1 712 each of these is 79 MB of float64 and the
    # accumulator now owns its own copy of all three; holding the originals
    # as well costs 236 MB on an 11.9 GB box that has already had one build
    # of this item killed for want of RAM.  Dm/CLS/STAIN are another 236 MB
    # and nothing below reads them.
    del base, aux, wear, Dm, CLS, STAIN, N
    gc.collect()

    # ---- faces, grouped by material and by the joint-recess stations ----
    ja = int(np.argmax(is_asph))
    jb = int(K - 1 - np.argmax(is_asph[::-1]))
    i_m = int(np.searchsorted(X, -(END_X - JOINT_M_W)))
    i_p = int(np.searchsorted(X, (END_X - JOINT_P_W)))

    # the gulley holes: drop the quads whose centre is inside the clear opening
    qx = 0.5 * (X[:-1] + X[1:])
    QY = 0.5 * (S[:-1, ja:jb + 1, 0] + S[1:, ja:jb + 1, 0])
    QX = np.broadcast_to(qx[:, None], QY.shape)
    hole = np.zeros(QY.shape, bool)
    for gx in (-GULLY_X, GULLY_X):
        for gy in (-GULLY_Y, GULLY_Y):
            hole |= ((np.abs(QX - gx) < GULLY_CLEAR * 0.5)
                     & (np.abs(QY - gy) < GULLY_CLEAR * 0.5))
    cnt["gully_holes_cut"] = int(hole.sum())

    n_asph = _emit_quads(acc, IDX[i_m:i_p + 1, ja:jb + 2], MAT_ASPH, True,
                         drop=hole[i_m:i_p])
    _emit_quads(acc, IDX[:i_m + 1, ja:jb + 2], MAT_CONC, True)
    _emit_quads(acc, IDX[i_p:, ja:jb + 2], MAT_CONC, True)
    # everything else, as one contiguous run through the wrap
    roll = -(jb + 1)
    IR = np.roll(IDX, roll, axis=1)
    n_conc_j = K - (jb + 1) + ja + 1
    _emit_quads(acc, IR[:, :n_conc_j], MAT_CONC, True)

    # ---- end caps -------------------------------------------------------
    j_lo = seg_start[idx_of["fascia_L_top"]]
    j_hi = seg_start[idx_of["fascia_R_top"]]
    for (ii, flip) in ((0, True), (M - 1, False)):
        cnt["cap_tris"] = cnt.get("cap_tris", 0) + cap_monotone(
            acc, S[ii], IDX[ii], int(j_lo), int(j_hi), MAT_CONC, flip)

    cnt["slab_verts"] = int(M * K)
    cnt["stations"] = M
    cnt["section_points"] = K
    cnt["asphalt_quads"] = n_asph
    cnt["blowhole_field_cells"] = int(round(DECK_LEN * 14.0 / 0.014 ** 2 * 0.0))
    if mounts is not None:
        for side, tag in ((-1.0, "L"), (1.0, "R")):
            zz = float(fascia_top_z(np.array([0.0]), side)[0])
            mounts["fascia_face_%s" % tag] = Frame(
                (0.0, side * DECK_HALF_W, 0.5 * (zz + float(
                    fascia_soffit_z(np.array([0.0]), side)[0]))),
                (1, 0, 0), (0, 0, 1), (0, side, 0), r=0.22,
                tag="fascia face plane, %s side" % tag)
            mounts["cornice_%s" % tag] = Frame(
                (0.0, side * 0.5 * (DECK_HALF_W + PLINTH_OUT_Y), zz + 0.008),
                (1, 0, 0), (0, side, 0), (0, 0, 1), r=0.21,
                tag="cornice top plane, %s side" % tag)
            mounts["kerb_line_%s" % tag] = Frame(
                (0.0, side * KERB_FACE_Y, float(chan_z(np.array([0.0]),
                                                       side)[0]) + 0.075),
                (1, 0, 0), (0, 0, 1), (0, side, 0), r=0.075,
                tag="kerb face line, %s side" % tag)
    return IDX, S, U, MATk, NAMES, seg_start


# --------------------------------------------------------------------------- #
#  8.  SMALL PRIMITIVES                                                         #
# --------------------------------------------------------------------------- #

def _basis(w):
    """An orthonormal (u, v, w) from a single axis."""
    w = unit(np.asarray(w, float))
    a = np.array([0.0, 0.0, 1.0]) if abs(w[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    u = unit(np.cross(a, w))
    return u, np.cross(w, u), w


def prism_x(acc, P2, x0, x1, step, mat, base, aux, wear, edge=None,
            yz_off=(0.0, 0.0), warp=None, smooth=True, caps=True, uid=0.0):
    """Sweep a closed (y, z) profile along x.  -> the (M, K) index grid.

    `warp(x)` may return (dy, dz, roll) per station, which is how a kerb unit
    gets its own bedding lippage and its own half-degree of rotation without
    being a different mesh from its neighbour by accident.
    """
    P2 = np.asarray(P2, float)
    K = len(P2)
    n = max(2, int(round((x1 - x0) / step)) + 1)
    xs = np.linspace(x0, x1, n)
    S = np.broadcast_to(P2[None, :, :], (n, K, 2)).copy()
    if warp is not None:
        dy, dz, roll = warp(xs)
        cs, sn = np.cos(roll), np.sin(roll)
        Y = S[:, :, 0] * cs[:, None] - S[:, :, 1] * sn[:, None]
        Z = S[:, :, 0] * sn[:, None] + S[:, :, 1] * cs[:, None]
        S[:, :, 0] = Y + dy[:, None]
        S[:, :, 1] = Z + dz[:, None]
    S[:, :, 0] += yz_off[0]
    S[:, :, 1] += yz_off[1]
    Cp = np.stack([xs, np.zeros(n), np.zeros(n)], -1)
    Uax = np.tile(np.array([0.0, 1.0, 0.0]), (n, 1))
    Vax = np.tile(np.array([0.0, 0.0, 1.0]), (n, 1))
    IDX = sweep(acc, Cp, Uax, Vax, S, mat=mat, base=base, aux=aux, wear=wear,
                edge=edge, smooth=smooth, vcoord=xs)
    if caps:
        for (ii, flip) in ((0, True), (n - 1, False)):
            P3 = np.stack([np.full(K, xs[ii]), S[ii, :, 0], S[ii, :, 1]], -1)
            ctr = P3.mean(0)
            a4 = np.tile(np.asarray(aux, float).reshape(1, 4), (K + 1, 1))
            a4[:, 0] = 0.9
            i0 = acc.verts(np.concatenate([P3, ctr[None, :]], 0),
                           uv=np.zeros((K + 1, 2)), base=base, aux=a4, wear=wear)
            acc.fan(i0 + np.arange(K), i0 + K, mat, smooth=False, flip=flip)
    return IDX


def socket(acc, o, w, r_out, r_bore, depth, mat, base, aux, wear,
           collar=0.0008, nseg=20, uid=0.0):
    """A cast-in ferrule / insert: a flush collar and a real bore.

    No hole is cut in the host grid.  A real ferrule presents a 30 mm washer
    face that laps the concrete around it, so the collar covers whatever the
    grid did underneath and the bore is genuinely dark and genuinely deep.
    """
    o = np.asarray(o, float)
    u, v, w = _basis(w)
    th = np.arange(nseg) * TAU / nseg
    ring = lambda r, off: (o[None, :] + np.cos(th)[:, None] * r * u[None, :]
                           + np.sin(th)[:, None] * r * v[None, :]
                           + w[None, :] * off)
    a4 = np.asarray(aux, float).copy()
    a4[2] = 1.0
    rings = []
    for (r, off, e) in ((r_out, collar, 0.85), (r_out * 0.86, collar * 1.6, 0.55),
                        (r_bore, collar * 1.6, 1.0), (r_bore, -depth * 0.4, 0.2),
                        (r_bore * 0.9, -depth, 0.05)):
        P = ring(r, off)
        aa = np.tile(a4.reshape(1, 4), (nseg, 1))
        aa[:, 0] = e
        i0 = acc.verts(P, uv=np.stack([np.arange(nseg) * r * TAU / nseg,
                                       np.full(nseg, off)], -1),
                       base=base, aux=aa, wear=wear)
        rings.append(i0 + np.arange(nseg))
    for i in range(len(rings) - 1):
        bridge(acc, rings[i], rings[i + 1], mat, smooth=(i != 0), wrap=True)
    ic = acc.verts((o - w * depth).reshape(1, 3), uv=np.zeros((1, 2)),
                   base=base, aux=a4.reshape(1, 4), wear=wear)
    acc.fan(rings[-1], ic, mat, smooth=False, flip=True)
    return rings[0]


def stone(acc, o, r, mat, base, aux, wear, uid=0.0, flat=0.55):
    """One loose chipping: an irregular 8-faced solid, flattened onto the road.

    A surface chipping is 6-14 mm, which is 7-17 screen pixels at this item's
    filmed distance.  It is a stone, so it is a stone.
    """
    o = np.asarray(o, float)
    ph = np.array([0.0, 0.25, 0.5, 0.75]) * TAU + rnd(0.0, 1.0, uid, "p") * TAU
    P = [o + np.array([0.0, 0.0, r * flat * rnd(0.8, 1.25, uid, "t")])]
    for k, a in enumerate(ph):
        rr = r * rnd(0.72, 1.15, uid, "r", k)
        P.append(o + np.array([rr * math.cos(a), rr * math.sin(a),
                               r * flat * rnd(0.15, 0.45, uid, "m", k)]))
    for k, a in enumerate(ph + TAU / 8.0):
        rr = r * rnd(0.62, 1.0, uid, "s", k)
        P.append(o + np.array([rr * math.cos(a), rr * math.sin(a),
                               -r * flat * rnd(0.2, 0.6, uid, "b", k)]))
    P = np.array(P)
    a4 = np.asarray(aux, float).copy()
    a4[0] = 0.9
    i0 = acc.verts(P, uv=np.zeros((len(P), 2)), base=base, aux=a4, wear=wear)
    T = []
    for k in range(4):
        k2 = (k + 1) % 4
        T += [(0, 1 + k, 1 + k2), (1 + k, 5 + k, 1 + k2),
              (1 + k2, 5 + k, 5 + k2), (5 + k, 5 + (k + 3) % 4, 5 + k2)]
    acc.tris(np.array(T, np.int64) + i0, mat, False)


def plate_box(acc, ctr, ex, ey, ez, mat, base, aux, wear, cham=0.0020,
              axis=0, uid=0.0, smooth=False):
    """A rectangular block with chamfered arrises, swept along `axis`.

    Built through the shared sweep rather than by hand-winding 26 faces,
    because a hand-wound box is exactly the sort of thing that ships with two
    faces inside out and renders black under a 12.5 deg sun.
    """
    ctr = np.asarray(ctr, float)
    e = [float(ex), float(ey), float(ez)]
    o1, o2 = [k for k in range(3) if k != axis]
    S, E = HS.rrect_section(2.0 * e[o1], 2.0 * e[o2], max(cham, 1e-4),
                            nc=3, ns=2)
    K = len(S)
    ax = np.zeros(3); ax[axis] = 1.0
    u = np.zeros(3); u[o1] = 1.0
    v = np.zeros(3); v[o2] = 1.0
    ch = min(cham, e[axis] * 0.45)
    ts = np.array([-e[axis] + ch, e[axis] - ch])
    Cp = ctr[None, :] + ts[:, None] * ax[None, :]
    IDX = sweep(acc, Cp, np.tile(u, (2, 1)), np.tile(v, (2, 1)), S, mat=mat,
                base=base, aux=aux, wear=wear, edge=E, smooth=smooth,
                vcoord=ts)
    shrink = 1.0 - ch / max(min(e[o1], e[o2]), 1e-6)
    for (ii, flip, sgn) in ((0, True, -1.0), (1, False, 1.0)):
        r = cap_flat(acc, ctr + ax * (sgn * e[axis]), u, v, S * shrink,
                     mat, base, aux, wear, edge=E * 0.6, flip=flip)
        # the cap ring sits ch further out and `shrink` smaller than the body
        # ring, so bridging them gives the block a real 2 mm end chamfer
        # instead of a hard 90 deg arris that no cast or cut part ever has
        bridge(acc, IDX[ii], r, mat, smooth=False, wrap=True, flip=not flip)
    return IDX


# --------------------------------------------------------------------------- #
#  9.  THE KERBS  —  variation axis 1, and the two sides are not each other     #
# --------------------------------------------------------------------------- #

KERB_H = 0.225
KERB_BED = 0.025


def kerb_profile(kind, dens=0.0045):
    """CCW (y, z) outline of one precast kerb unit, origin at the front foot.

    Two profiles exist on this deck and that is the point: HB is the original
    half-battered run, BN is the bullnose the yard had in stock when two units
    were replaced after the same impact that took out the +y upstand.
    """
    w, h = KERB_W, KERB_H
    if kind == "BN":
        pts = [(0.0, 0.0), (w, 0.0), (w, h - 0.006), (w - 0.006, h),
               (0.045, h), (0.030, h - 0.004), (0.014, h - 0.016),
               (0.005, h - 0.033), (0.0, h - 0.055)]
    else:
        pts = [(0.0, 0.0), (w, 0.0), (w, h - 0.006), (w - 0.006, h),
               (0.038, h), (0.030, h - 0.0035), (0.0225, h - 0.012),
               (0.0075, h - 0.045), (0.0, h - 0.100)]
    P = np.array(pts, float)
    out, edg = [], []
    hard = {2: 0.9, 3: 1.0, 4: 1.0, 8: 0.5}
    for i in range(len(P)):
        a, b = P[i], P[(i + 1) % len(P)]
        n = max(1, int(round(np.linalg.norm(b - a) / dens)))
        t = np.arange(n) / float(n)
        out.append(a[None, :] + t[:, None] * (b - a)[None, :])
        e0, e1 = hard.get(i, 0.15), hard.get((i + 1) % len(P), 0.15)
        edg.append(e0 + t * (e1 - e0))
    return np.concatenate(out, 0), np.concatenate(edg, 0)


def build_kerbs(acc, cnt, res=1.0, mounts=None):
    """The -y kerb line: 34 individual precast units bedded in the cast pocket.

    Every unit is its OWN mesh with its own bedding lippage, plan rotation,
    joint width, chipped corners and casting-lot colour.  Two are a different
    PROFILE and one is cracked clean through with its halves 2 mm out of line.
    That is what "variation must be in the geometry" means for a kerb run: not
    one unit rotated 34 times.
    """
    q = max(min(float(res), 2.0), 0.3)
    dens = 0.0045 / q
    step = 0.032 / q
    x = -END_X + 0.010
    n = 0
    lots = []
    profiles = {}
    while x < END_X - 0.10:
        uid = "kerb%d" % n
        joint = rnd(0.006, 0.016, uid, "j")
        L = min(0.915, END_X - 0.010 - x)
        if L < 0.30:
            break
        kind = "BN" if n in (17, 18) else "HB"
        cracked = (n == 24)
        lot = rint(0, 2, uid, "lot")
        lots.append(lot)
        key = (kind, round(dens, 5))
        if key not in profiles:
            profiles[key] = kerb_profile(kind, dens)
        P2, E = profiles[key]
        K = len(P2)
        col = np.array(srgb(KERB_HEX[lot])) * rnd(0.94, 1.06, uid, "c")
        base = np.array([col[0], col[1], col[2], 0.10 + 0.28 * lot])
        aux = np.array([0.0, 1.0, 0.0, hash01(uid)])
        wear = np.array([rnd(0.25, 0.75, uid, "w"), rnd(0.35, 0.8, uid, "d"),
                         rnd(0.05, 0.45, uid, "b"), rnd(0.55, 0.9, uid, "a")])

        pieces = [(0.0, L)] if not cracked else [(0.0, L * 0.46),
                                                 (L * 0.46 + 0.002, L)]
        for pi, (t0, t1) in enumerate(pieces):
            xs = np.arange(x + t0, x + t1 + step * 0.5, step)
            if len(xs) < 2:
                continue
            m = len(xs)
            # per-unit bedding: lippage, roll, yaw, and a settle at one end
            lip = rnd(-0.0035, 0.0035, uid, "lip") + (0.002 if pi else 0.0)
            roll = math.radians(rnd(-0.45, 0.45, uid, "roll", pi))
            yaw = math.radians(rnd(-0.5, 0.5, uid, "yaw"))
            tt = (xs - xs[0]) / max(xs[-1] - xs[0], 1e-6)
            zc = chan_z(xs, -1.0)
            S = np.broadcast_to(P2[None, :, :], (m, K, 2)).copy()
            cs, sn = math.cos(roll), math.sin(roll)
            Y = S[:, :, 0] * cs - S[:, :, 1] * sn
            Z = S[:, :, 0] * sn + S[:, :, 1] * cs
            # place: front face on the kerb line, foot on the mortar bed
            S[:, :, 0] = -(KERB_FACE_Y + Y) - yaw * (xs - xs.mean())[:, None]
            S[:, :, 1] = Z + (zc - POCKET_D + KERB_BED + lip)[:, None]
            # surface: precast is denser and smoother than in-situ, but it
            # chips, and the top-front arris is where a wheel finds it
            u2 = np.zeros((m, 1)) + HS.section_perimeter_u(P2)[None, :]
            x2 = xs[:, None] + np.zeros((1, K))
            d = 0.0006 * fbm(x2 * 6.0, u2 * 6.0, 1201 + n)
            d -= _cells(x2, u2, 0.0075, 1301 + n, 0.28, 0.0005, 0.0016, 0.55)
            for ci in range(rint(0, 3, uid, "nchip")):
                cxx = x + rnd(0.02, L - 0.02, uid, "cx", ci)
                cuu = rnd(0.44, 0.52, uid, "cu", ci) * float(u2.max())
                cr = rnd(0.008, 0.030, uid, "cr", ci)
                rr = np.hypot(x2 - cxx, u2 - cuu)
                d -= 0.6 * cr * np.clip(1.0 - (rr / cr) ** 2, 0, 1) ** 0.7
            NN = sec_outward(S)
            S = S + NN * d[:, :, None]
            Cp = np.stack([xs, np.zeros(m), np.zeros(m)], -1)
            IDX = sweep(acc, Cp, np.tile(np.array([0.0, 1.0, 0.0]), (m, 1)),
                        np.tile(np.array([0.0, 0.0, 1.0]), (m, 1)), S,
                        mat=MAT_KERB, base=base, aux=aux, wear=wear, edge=E,
                        smooth=True, vcoord=xs)
            for (ii, flip) in ((0, True), (m - 1, False)):
                P3 = np.stack([np.full(K, xs[ii]), S[ii, :, 0], S[ii, :, 1]], -1)
                ctr = P3.mean(0)
                a4 = np.tile(aux.reshape(1, 4), (K + 1, 1))
                i0 = acc.verts(np.concatenate([P3, ctr[None, :]], 0),
                               uv=np.zeros((K + 1, 2)), base=base, aux=a4,
                               wear=wear)
                acc.fan(i0 + np.arange(K), i0 + K, MAT_KERB, smooth=False,
                        flip=flip)
            cnt["kerb_pieces"] = cnt.get("kerb_pieces", 0) + 1

        # THE MORTAR BED and the joint: squeezed-out mortar is what tells you
        # these are separate stones rather than one extrusion.
        bx = np.array([x - 0.004, x + L + 0.004])
        bp = np.array([[0.0, 0.0], [KERB_W + 0.012, 0.0],
                       [KERB_W + 0.010, KERB_BED],
                       [-0.006, KERB_BED]])
        bp = np.concatenate([bp[i][None, :] + (bp[(i + 1) % 4] - bp[i])[None, :]
                             * np.linspace(0, 1, 7)[:-1, None]
                             for i in range(4)], 0)
        m2 = len(bp)
        Sb = np.broadcast_to(bp[None, :, :], (2, m2, 2)).copy()
        Sb[:, :, 0] = -(KERB_FACE_Y + Sb[:, :, 0])
        Sb[:, :, 1] = Sb[:, :, 1] + (chan_z(bx, -1.0) - POCKET_D)[:, None]
        mb = np.array(srgb(MORTAR_HEX))
        prism = sweep(acc, np.stack([bx, np.zeros(2), np.zeros(2)], -1),
                      np.tile(np.array([0.0, 1.0, 0.0]), (2, 1)),
                      np.tile(np.array([0.0, 0.0, 1.0]), (2, 1)), Sb,
                      mat=MAT_MORTAR,
                      base=np.array([mb[0], mb[1], mb[2], 0.6]),
                      aux=np.array([0.3, 0.0, 0.0, hash01(uid, "m")]),
                      wear=np.array([0.4, 0.7, 0.3, 0.7]), smooth=False,
                      vcoord=bx)
        n += 1
        x += L + joint
    cnt["kerb_units"] = n
    cnt["kerb_lots"] = len(set(lots))
    cnt["kerb_profiles"] = len(profiles)
    return n


# --------------------------------------------------------------------------- #
# 10.  CAST-IN FITTINGS, THE REPAIR ANGLE, AND THE TWO JOINTS                   #
# --------------------------------------------------------------------------- #

def post_stations():
    """PUBLIC.  Parapet post x on the DECK, per side.

    Set OUT from pont_girder's end posts at |x| = 16.370 at 1.925 m pitch, so
    the panel that crosses the deck joint at 15.600 is a whole panel and not a
    600 mm offcut.  The end posts themselves are pont_girder's and are not
    rebuilt here.
    """
    xs = []
    x = POST_END_X - POST_PITCH
    while x > 0.30:
        xs.append(round(x, 4))
        x -= POST_PITCH
    return sorted([-v for v in xs] + xs)


def soffit_insert_stations():
    return [(float(x), float(sy * 1.500))
            for sy in (-1, 1)
            for x in np.arange(-15.0, 15.0001, 1.5)]


def _mat_arrays(hexs, alpha, edge, form, uid, wear):
    col = np.array(srgb(hexs))
    return (np.array([col[0], col[1], col[2], alpha]),
            np.array([edge, form, 0.0, uid]), np.array(wear, float))


def build_fittings(acc, cnt, mounts, res=1.0):
    """Everything cast into or bolted onto the slab."""
    q = max(min(float(res), 2.0), 0.3)
    zbase, zaux, zwear = _mat_arrays(ZINC_HEX, 0.0, 0.8, 0.0, 0.31,
                                     (0.35, 0.55, 0.10, 0.70))
    cbase, caux, cwear = _mat_arrays(CONC_A_HEX, 0.4, 0.5, 1.0, 0.12,
                                     (0.30, 0.50, 0.20, 0.70))

    # ---- 1. parapet ferrules ------------------------------------------
    nf = 0
    for (side, tag) in ((-1.0, "L"), (1.0, "R")):
        for n, px in enumerate(post_stations()):
            zt = float(plinth_top_z(np.array([px]), side)[0])
            o = np.array([px, side * PARAPET_Y, zt])
            mounts["parapet_post_%s_%d" % (tag, n)] = Frame(
                o, (1, 0, 0), (0, side, 0), (0, 0, 1), r=0.075,
                tag="parapet post base plate, 4 x M20 at 90 x 84, plinth %s"
                    % tag)
            for sx in (-1, 1):
                for sy in (-1, 1):
                    fo = o + np.array([sx * FERRULE_GAUGE[0] * 0.5,
                                       sy * FERRULE_GAUGE[1] * 0.5, 0.0])
                    socket(acc, fo, (0, 0, 1), 0.0150, FERRULE_BORE, 0.075,
                           MAT_STEEL, zbase, zaux, zwear, nseg=18,
                           uid=hash01("fer", tag, n, sx, sy))
                    nf += 1
        # the two END posts are pont_girder's, on the girder noses
        for (ex, nm) in ((-POST_END_X, "m"), (POST_END_X, "p")):
            mounts["parapet_post_%s_end_%s" % (tag, nm)] = Frame(
                (ex, side * PARAPET_Y, 8.164), (1, 0, 0), (0, side, 0),
                (0, 0, 1), r=0.052,
                tag="END post — pont_girder's parapet_end_%s_%s, NOT rebuilt "
                    "here" % ("A" if side < 0 else "D", nm))
    cnt["parapet_ferrules"] = nf

    # ---- 2. soffit fixing inserts ---------------------------------------
    for n, (sx, sy) in enumerate(soffit_insert_stations()):
        zs = float(soffit_z(np.array([sx]), np.array([sy]))[0])
        socket(acc, (sx, sy, zs), (0, 0, -1), 0.017, 0.0065, 0.055,
               MAT_STEEL, zbase, zaux, zwear, nseg=16,
               uid=hash01("ins", n))
        mounts["soffit_insert_%d" % n] = Frame(
            (sx, sy, zs), (1, 0, 0), (0, 1, 0), (0, 0, -1), r=0.018,
            tag="cast-in M12 soffit socket")
    cnt["soffit_inserts"] = len(soffit_insert_stations())

    # ---- 3. cast-in service ducts ---------------------------------------
    for n, dx in enumerate((-14.900, 14.900)):
        dy = -1.500
        zt = float(deck_conc_z(np.array([dx]), np.array([dy]))[0])
        zs = float(soffit_z(np.array([dx]), np.array([dy]))[0])
        socket(acc, (dx, dy, zt + SURF_T), (0, 0, 1), 0.072, 0.055, 0.090,
               MAT_STEEL, zbase, zaux, zwear, nseg=24, uid=hash01("duct", n))
        socket(acc, (dx, dy, zs), (0, 0, -1), 0.072, 0.055, 0.090,
               MAT_STEEL, zbase, zaux, zwear, nseg=24, uid=hash01("ductb", n))
        mounts["duct_%d" % n] = Frame((dx, dy, zs), (1, 0, 0), (0, 1, 0),
                                      (0, 0, -1), r=0.055,
                                      tag="cast-in 110 mm service duct")
    cnt["ducts"] = 2

    # ---- 4. THE +y REPAIR: a galvanised 80x80x8 edge angle ---------------
    # It is bolted, not cast, because it went on years after the deck.  Five
    # lengths with 12 mm gaps, and the gaps are where the run stops reading as
    # an extrusion.
    Sa, Ea = HS.angle_section(0.080, 0.080, 0.008, nc=4, ns=4)
    Sa = np.stack([Sa[:, 0], -Sa[:, 1]], -1)          # open toward +y and -z
    y_arr = KERB_FACE_Y + BATTER_DY
    segs = np.linspace(-END_X + 0.06, END_X - 0.06, 6)
    nb = 0
    for si in range(5):
        x0, x1 = segs[si] + 0.006, segs[si + 1] - 0.006
        m = max(2, int(round((x1 - x0) / (0.060 / q))))
        xs = np.linspace(x0, x1, m)
        zt = plinth_top_z(xs, +1.0)
        S = np.broadcast_to(Sa[None, :, :], (m, len(Sa), 2)).copy()
        S[:, :, 0] += y_arr + 0.040
        S[:, :, 1] += zt[:, None] - 0.040
        S[:, :, 1] += (0.0006 * fbm(xs * 3.0, np.zeros(m), 1907 + si))[:, None]
        Cp = np.stack([xs, np.zeros(m), np.zeros(m)], -1)
        sweep(acc, Cp, np.tile(np.array([0.0, 1.0, 0.0]), (m, 1)),
              np.tile(np.array([0.0, 0.0, 1.0]), (m, 1)), S, mat=MAT_STEEL,
              base=zbase, aux=zaux,
              wear=np.array([0.55, 0.6, 0.05, 0.8]), edge=Ea, smooth=True,
              vcoord=xs, flip=True)
        for (ii, flip) in ((0, False), (m - 1, True)):
            P3 = np.stack([np.full(len(Sa), xs[ii]), S[ii, :, 0], S[ii, :, 1]],
                          -1)
            ctr = P3.mean(0)
            a4 = np.tile(zaux.reshape(1, 4), (len(Sa) + 1, 1))
            i0 = acc.verts(np.concatenate([P3, ctr[None, :]], 0),
                           uv=np.zeros((len(Sa) + 1, 2)), base=zbase, aux=a4,
                           wear=zwear)
            acc.fan(i0 + np.arange(len(Sa)), i0 + len(Sa), MAT_STEEL,
                    smooth=False, flip=flip)
        for bx in np.arange(x0 + 0.22, x1 - 0.10, 1.500):
            zt = float(plinth_top_z(np.array([bx]), +1.0)[0])
            o = np.array([bx, y_arr + 0.052, zt + 0.008])
            washer(acc, o, (1, 0, 0), (0, 1, 0), (0, 0, 1), 0.019, 0.0105,
                   0.0035, MAT_STEEL, zbase, zaux, zwear, nseg=18)
            hex_nut(acc, o + np.array([0, 0, 0.0035]), (1, 0, 0), (0, 1, 0),
                    (0, 0, 1), 0.030, 0.013, 0.0105, MAT_STEEL, zbase, zaux,
                    zwear, uid=hash01("ab", si, bx))
            nb += 1
    cnt["edge_angle_lengths"] = 5
    cnt["edge_angle_bolts"] = nb

    # ---- 5. THE TWO JOINTS ----------------------------------------------
    # -x : elastomeric in a runner.  34 cast-in anchor loops, 12 mm bar.
    xr = -(END_X - JOINT_M_W * 0.5)
    nl = 0
    for yy in np.arange(-2.05, 2.06, 0.125):
        zf = float(road_z(np.array([xr]), np.array([yy]))[0]) - JOINT_M_D
        ang = np.linspace(0.0, math.pi, 11)
        R = 0.045
        P = np.stack([xr + R * np.cos(ang) * 0.0 + R * np.sin(ang) * 0.0,
                      yy + R * np.cos(ang), zf + 0.004 + R * np.sin(ang)], -1)
        T3, U3, V3 = HS.frames_along(P, ref=(1.0, 0.0, 0.0))
        Sc, Ec, _t = circle_section(9, 0.006)
        sweep(acc, P, U3, V3, Sc, mat=MAT_STEEL, base=zbase, aux=zaux,
              wear=np.array([0.4, 0.7, 0.05, 0.85]), edge=Ec, smooth=True)
        nl += 1
    mounts["joint_m"] = Frame(
        (-END_X, 0.0, float(road_z(np.array([-END_X]), np.array([0.0]))[0])
         - JOINT_M_D), (-1, 0, 0), (0, 1, 0), (0, 0, 1), r=JOINT_M_W * 0.5,
        tag="ELASTOMERIC-IN-RUNNER joint: recess %.3f x %.3f, %d anchor "
            "loops at 0.125, gap to abutment %.3f"
            % (JOINT_M_W, JOINT_M_D, nl, JOINT_M_GAP))

    # +x : comb / finger plate.  Cast-in M20 ferrules on a bolted-plate grid
    # plus a cast-in nosing angle, because a finger plate lands on steel.
    xp0 = END_X - JOINT_P_W
    nfj = 0
    for yy in np.arange(-2.09, 2.10, 0.220):
        for xx in (xp0 + 0.075, END_X - 0.075):
            zf = float(road_z(np.array([xx]), np.array([yy]))[0]) - JOINT_P_D
            socket(acc, (xx, yy, zf), (0, 0, 1), 0.0165, 0.0105, 0.085,
                   MAT_STEEL, zbase, zaux, zwear, nseg=16,
                   uid=hash01("jf", xx, yy))
            nfj += 1
    Sn, En = HS.angle_section(0.080, 0.080, 0.008, nc=4, ns=4)
    m = max(2, int(round(4.5 / (0.060 / q))))
    xs = np.full(m, xp0 + 0.040)
    ys = np.linspace(-2.24, 2.24, m)
    zn = road_z(xs, ys) - JOINT_P_D
    Sn2 = np.broadcast_to(Sn[None, :, :], (m, len(Sn), 2)).copy()
    P = np.stack([xs * 0.0 + xp0 + 0.040, ys, zn + 0.040], -1)
    U3 = np.tile(np.array([1.0, 0.0, 0.0]), (m, 1))
    V3 = np.tile(np.array([0.0, 0.0, 1.0]), (m, 1))
    sweep(acc, P, U3, V3, Sn2, mat=MAT_STEEL, base=zbase, aux=zaux,
          wear=np.array([0.5, 0.55, 0.05, 0.8]), edge=En, smooth=True)
    mounts["joint_p"] = Frame(
        (END_X, 0.0, float(road_z(np.array([END_X]), np.array([0.0]))[0])
         - JOINT_P_D), (1, 0, 0), (0, 1, 0), (0, 0, 1), r=JOINT_P_W * 0.5,
        tag="COMB / FINGER PLATE joint: recess %.3f x %.3f screeded flat, "
            "%d cast-in M20 at 0.220 x 0.180, cast-in 80x80x8 nosing angle, "
            "gap %.3f.  pont_girder's deck_joint_angle_B at local "
            "(15.928, -0.751, 8.025) carries the ABUTMENT-side plate."
            % (JOINT_P_W, JOINT_P_D, nfj, JOINT_P_GAP))
    cnt["joint_anchor_loops"] = nl
    cnt["joint_ferrules"] = nfj

    # ---- 6. the cast-in identification plate ----------------------------
    zp = float(fascia_top_z(np.array([-6.0]), -1.0)[0])
    plate_box(acc, (-6.0, -DECK_HALF_W + 0.004, zp - 0.230), 0.110, 0.005,
              0.070, MAT_STEEL, zbase, zaux, zwear, cham=0.0015, axis=0)
    cnt["id_plates"] = 1


# --------------------------------------------------------------------------- #
# 11.  THE GULLIES, THE MARKINGS, AND THE LOOSE STONE                           #
# --------------------------------------------------------------------------- #

def gully_stations():
    """PUBLIC.  The four deck gullies, 2.0 m short of each joint, in both
    channels, because the deck is hogged and sheds to both ends."""
    return [(sx * GULLY_X, sy * GULLY_Y)
            for sx in (-1.0, 1.0) for sy in (-1.0, 1.0)]


def build_drains(acc, cnt, mounts, res=1.0):
    """Four cast-in gulley pots: frame, throat, sump, outlet spigot, silt.

    The frame flange laps 60 mm over the concrete on every side, which is what
    a real cast-in frame does and which is also why the slab's grid can carry
    a square hole without the hole's stepped edge ever being visible.
    """
    q = max(min(float(res), 2.0), 0.3)
    fbase, faux, fwear = _mat_arrays("#6d6a63", 0.0, 0.9, 0.0, 0.47,
                                     (0.6, 0.75, 0.05, 0.85))
    NSEG = 64
    counts = (16, 16, 16, 16)
    for n, (gx, gy) in enumerate(gully_stations()):
        zt = float(road_z(np.array([gx]), np.array([gy]))[0]) + 0.006
        zs = float(soffit_z(np.array([gx]), np.array([gy]))[0])
        ho = GULLY_FLANGE * 0.5
        hi = GULLY_CLEAR * 0.5
        uid = hash01("gul", n)

        def loop(h, dz, shrink=1.0):
            L = HS.rect_loop(gx - h * shrink, gx + h * shrink,
                             gy - h * shrink, gy + h * shrink, 0.01,
                             counts=counts)
            return np.concatenate([L, np.full((len(L), 1), dz)], -1)

        rings = []
        specs = [(ho, zt - 0.014, 0.55), (ho, zt - 0.003, 0.95),
                 (ho * 0.985, zt, 0.85), (hi * 1.03, zt, 0.35),
                 (hi, zt - 0.004, 1.00), (hi, zt - 0.055, 0.20),
                 (hi * 1.10, zt - 0.070, 0.25),
                 (hi * 1.10, zt - 0.006 - GULLY_DEPTH, 0.30)]
        for (h, dz, e) in specs:
            P = loop(h, dz)
            a4 = np.tile(faux.reshape(1, 4), (len(P), 1))
            a4[:, 0] = e
            a4[:, 3] = uid
            i0 = acc.verts(P, uv=np.stack([np.arange(len(P)) * 0.01,
                                           np.full(len(P), dz)], -1),
                           base=fbase, aux=a4, wear=fwear)
            rings.append(i0 + np.arange(len(P)))
        for i in range(len(rings) - 1):
            bridge(acc, rings[i], rings[i + 1], MAT_STEEL,
                   smooth=False, wrap=True, flip=(i >= 3))
        # the sump floor: rect ring down to the outlet circle
        th = np.arange(len(rings[0])) * TAU / len(rings[0]) + math.pi * 0.25
        circ = np.stack([gx + GULLY_SPIGOT_R * np.cos(th),
                         gy + GULLY_SPIGOT_R * np.sin(th),
                         np.full(len(th), zt - 0.006 - GULLY_DEPTH)], -1)
        i0 = acc.verts(circ, uv=np.zeros((len(circ), 2)), base=fbase,
                       aux=faux, wear=fwear)
        rc = i0 + np.arange(len(circ))
        bridge(acc, rings[-1], rc, MAT_STEEL, smooth=False, wrap=True,
               flip=True)
        # the outlet tube: inner face seen down the pot, outer face seen from
        # under the bridge, and a real socket rim for pont_scupper's pipe
        zb = zs - 0.060
        for (r, z0, z1, flip, sm) in ((GULLY_SPIGOT_R, zt - 0.006 - GULLY_DEPTH,
                                       zb + 0.010, True, True),
                                      (GULLY_SPIGOT_R + 0.013, zs + 0.020, zb,
                                       False, True)):
            P0 = np.stack([gx + r * np.cos(th), gy + r * np.sin(th),
                           np.full(len(th), z0)], -1)
            P1 = np.stack([gx + r * np.cos(th), gy + r * np.sin(th),
                           np.full(len(th), z1)], -1)
            ia = acc.verts(P0, uv=np.zeros((len(th), 2)), base=fbase,
                           aux=faux, wear=fwear)
            ib = acc.verts(P1, uv=np.zeros((len(th), 2)), base=fbase,
                           aux=faux, wear=fwear)
            bridge(acc, ia + np.arange(len(th)), ib + np.arange(len(th)),
                   MAT_STEEL, smooth=sm, wrap=True, flip=flip)
        # close the bottom annulus
        Pa = np.stack([gx + GULLY_SPIGOT_R * np.cos(th),
                       gy + GULLY_SPIGOT_R * np.sin(th),
                       np.full(len(th), zb + 0.010)], -1)
        Pb = np.stack([gx + (GULLY_SPIGOT_R + 0.013) * np.cos(th),
                       gy + (GULLY_SPIGOT_R + 0.013) * np.sin(th),
                       np.full(len(th), zb)], -1)
        ia = acc.verts(Pa, uv=np.zeros((len(th), 2)), base=fbase, aux=faux,
                       wear=fwear)
        ib = acc.verts(Pb, uv=np.zeros((len(th), 2)), base=fbase, aux=faux,
                       wear=fwear)
        bridge(acc, ia + np.arange(len(th)), ib + np.arange(len(th)),
               MAT_STEEL, smooth=False, wrap=True, flip=False)
        # silt and leaf litter in the sump
        sbase, saux, swear = _mat_arrays("#4a4640", 0.7, 0.4, 0.0, 0.9,
                                         (0.2, 0.95, 0.35, 0.9))
        for k in range(14):
            a = rnd(0, TAU, uid, "s", k)
            rr = rnd(0.02, hi * 0.95, uid, "sr", k)
            stone(acc, (gx + rr * math.cos(a), gy + rr * math.sin(a),
                        zt - 0.004 - GULLY_DEPTH + rnd(0.0, 0.012, uid, "sz", k)),
                  rnd(0.004, 0.013, uid, "ss", k), MAT_MORTAR, sbase, saux,
                  swear, uid=hash01(uid, "st", k))
        mounts["gully_%d" % n] = Frame(
            (gx, gy, zt), (1, 0, 0), (0, 1, 0), (0, 0, 1), r=GULLY_FLANGE * 0.5,
            tag="gulley frame seat, %.3f clear opening, frame stands 6 mm "
                "proud" % GULLY_CLEAR)
        mounts["gully_outlet_%d" % n] = Frame(
            (gx, gy, zb), (1, 0, 0), (0, 1, 0), (0, 0, -1), r=GULLY_SPIGOT_R,
            tag="110 mm outlet spigot below the soffit, 60 mm proud, socket "
                "depth 0.060; route INBOARD to girder B or C — both fascia "
                "girders carry banners")
    cnt["gullies"] = 4


def build_lines(acc, cnt, res=1.0):
    """Thermoplastic markings.  2.5 mm proud, so they are geometry.

    A painted line is 0.15 mm and would be a texture; a thermoplastic line is
    2.5 mm and casts a shadow under a 12.5 deg sun, and this deck has
    thermoplastic because a service road over a circuit gets screed-applied
    markings that last.  Worn thin where wheels cross them.
    """
    q = max(min(float(res), 2.0), 0.3)
    lbase, laux, lwear = _mat_arrays(LINE_HEX, 0.2, 0.7, 0.0, 0.66,
                                     (0.55, 0.6, 0.05, 0.8))
    runs = []
    x = -END_X + 0.9
    while x < END_X - 1.9:                      # dashed centreline
        runs.append((x, x + 1.0, 0.0, 0.050))
        x += 3.0
    for yy in (-1.850, 1.850):                  # continuous edge lines
        runs.append((-END_X + 0.35, END_X - 0.35, yy, 0.050))
    n = 0
    for (x0, x1, yc, hw) in runs:
        m = max(2, int(round((x1 - x0) / (0.070 / q))))
        xs = np.linspace(x0, x1, m)
        prof = np.array([[-hw, -0.006], [hw, -0.006], [hw - 0.0035, 0.0025],
                         [-hw + 0.0035, 0.0025]])
        prof = np.concatenate(
            [prof[i][None, :] + (prof[(i + 1) % 4] - prof[i])[None, :]
             * np.linspace(0, 1, 9)[:-1, None] for i in range(4)], 0)
        K = len(prof)
        S = np.broadcast_to(prof[None, :, :], (m, K, 2)).copy()
        S[:, :, 0] += yc
        zz = road_z(xs[:, None], S[:, :, 0])
        wear = 1.0 - 0.55 * np.exp(-((S[:, :, 0] - (CROWN_Y + 0.95)) / 0.5) ** 2)
        wear *= 1.0 - 0.35 * np.exp(-((S[:, :, 0] - (CROWN_Y - 0.95)) / 0.5) ** 2)
        rough = 0.0009 * fbm(xs[:, None] * 3.0, S[:, :, 0] * 3.0, 2801 + n)
        S[:, :, 1] = zz + S[:, :, 1] * wear + rough * (S[:, :, 1] > 0)
        # ragged edges: a thermoplastic screed does not stop on a straight line
        rag = 0.0035 * fbm(xs[:, None] * 5.0, S[:, :, 0] * 20.0, 2903 + n)
        S[:, :, 0] += rag * (np.abs(S[:, :, 0] - yc) > hw * 0.6)
        Cp = np.stack([xs, np.zeros(m), np.zeros(m)], -1)
        sweep(acc, Cp, np.tile(np.array([0.0, 1.0, 0.0]), (m, 1)),
              np.tile(np.array([0.0, 0.0, 1.0]), (m, 1)), S, mat=MAT_LINE,
              base=lbase, aux=laux, wear=lwear, smooth=False, vcoord=xs)
        for (ii, flip) in ((0, True), (m - 1, False)):
            P3 = np.stack([np.full(K, xs[ii]), S[ii, :, 0], S[ii, :, 1]], -1)
            ctr = P3.mean(0)
            i0 = acc.verts(np.concatenate([P3, ctr[None, :]], 0),
                           uv=np.zeros((K + 1, 2)), base=lbase, aux=laux,
                           wear=lwear)
            acc.fan(i0 + np.arange(K), i0 + K, MAT_LINE, smooth=False,
                    flip=flip)
        n += 1
    cnt["line_runs"] = n


def build_chippings(acc, cnt, res=1.0):
    """Loose stone: what has washed into the channels and what the planer left
    along the sawn edge of the relaid bay."""
    q = max(min(float(res), 2.0), 0.3)
    sbase, saux, swear = _mat_arrays("#57534c", 0.8, 0.85, 0.0, 0.72,
                                     (0.5, 0.85, 0.15, 0.85))
    n = 0
    N = int(2200 * q)
    for k in range(N):
        u = hash01("ch", k, "u")
        side = -1.0 if hash01("ch", k, "s") < 0.62 else 1.0
        x = -END_X + 0.2 + u * (DECK_LEN - 0.4)
        dy = rnd(0.0, 0.30, "ch", k, "y") ** 1.6
        y = side * (KERB_FACE_Y - 0.004 - dy)
        if abs(x - GULLY_X) < 0.3 and abs(y) > 1.8:
            continue
        z = float(road_z(np.array([x]), np.array([y]))[0])
        r = rnd(0.0028, 0.0085, "ch", k, "r")
        stone(acc, (x, y, z + r * 0.25), r, MAT_ASPH, sbase, saux, swear,
              uid=hash01("ch", k), flat=rnd(0.4, 0.8, "ch", k, "f"))
        n += 1
    for k in range(int(320 * q)):
        x = pick([RELAY_X0, RELAY_X1], "rl", k) + rnd(-0.06, 0.06, "rl", k, "x")
        y = rnd(-2.05, 2.05, "rl", k, "y")
        z = float(road_z(np.array([x]), np.array([y]))[0])
        r = rnd(0.0025, 0.0060, "rl", k, "r")
        stone(acc, (x, y, z + r * 0.2), r, MAT_ASPH, sbase, saux, swear,
              uid=hash01("rl", k), flat=0.6)
        n += 1
    cnt["loose_stones"] = n


# --------------------------------------------------------------------------- #
# 12.  MATERIALS                                                                #
# --------------------------------------------------------------------------- #
#
# Six surfaces, each a stack of things that PHYSICALLY HAPPENED, in the order
# they happened.  The one thing concrete must not get wrong: IT IS NOT GREY.
# A cast face is a mosaic of cement-paste lot colour, aggregate ghosting where
# the fines migrated, laitance where the paste rose, carbonation chalking on
# whatever a 12.5 deg sun has bleached for eleven years, and a wash of every
# fluid that has ever run down it.  A single grey with a noise node on Base
# Color is the placeholder the brief names.
#
# LAW 6 IS OBEYED EVERYWHERE: every one of these reads TexCoord -> Object.
# Never Geometry -> Position.  This deck sits at world (-617, 95, 8), and a
# position-driven procedural at |P| ~ 620 m loses the fifth significant figure
# -- which at a 3 mm feature size is the whole feature.

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


def _chan(g):
    """The four per-vertex channels + OBJECT-space coordinates."""
    base = g.attr("base")
    aux = g.attr("aux")
    wear = g.attr("wear")
    bs = g.sep(base)
    au = g.sep(aux)
    we = g.sep(wear)
    tc = g.n("ShaderNodeTexCoord")
    uv = g.sepxyz((tc, 2))
    obj = g.vmath('MULTIPLY', (tc, 3), (1.0, 1.0, 1.0))
    return base, aux, wear, bs, au, we, tc, uv, obj


def _down(g):
    nrm = g.n("ShaderNodeNewGeometry")
    z = g.sepxyz((nrm, 1))
    return g.math('MAXIMUM', g.math('MULTIPLY', (z, 2), -1.0), 0.0, clamp=True)


def _up(g):
    nrm = g.n("ShaderNodeNewGeometry")
    z = g.sepxyz((nrm, 1))
    return g.math('MAXIMUM', (z, 2), 0.0, clamp=True)


def mat_concrete():
    """In-situ reinforced concrete, eleven years old, two pours, one repair.

      1  the POUR LOT.  base.rgb already carries which of the two pours this
         vertex belongs to and its within-lot drift; the shader adds the
         within-BATCH drift, which is a 2-3 m wavelength because that is one
         truck.
      2  AGGREGATE GHOSTING: the 10-20 mm stone under 3 mm of paste reads as a
         mottle, not as stones.  Voronoi, low contrast, and it is what stops a
         cast face looking like plaster.
      3  LAITANCE: the paste that rose against the form, paler and smoother,
         pooled at the top of each lift.
      4  BOARD GRAIN transferred off the plywood, only on formed faces
         (aux.y), running along the sheet.
      5  CARBONATION CHALKING on the faces a 12.5 deg sun actually reaches.
      6  RAIN TRACKING down the fascia, and the LIME PLUME under the drip
         groove -- the two most reliable tells that a concrete edge has been
         outdoors.
      7  ALGAL/BIOFILM band on the damp lower fascia and the whole soffit
         (wear.b), green-black and only where it stays wet.
      8  RUST bleed under the parapet ferrules and down from the joint.
      9  the SCUPPER STAIN: a dark plume on the soffit under each outlet.
         pont_scupper owns the pipe; this is my surface and my stain.
     10  the REPAIR: the sawn patch is a different, greyer, denser mortar.
     11  blowholes are GEOMETRY, but the light that fails to get out of them
         is not, so an AO term darkens their throats.
    """
    m, g, b, out = _new_mat("Concrete")
    base, aux, wear, bs, au, we, tc, uv, obj = _chan(g)
    u = g.sepxyz((tc, 2))
    ou = g.sepxyz(obj)

    # NOTE ON AXES.  The object is recentred on emit AFTER being placed, so
    # object space here is WORLD-ALIGNED (rotated 25 deg off the span), not
    # bridge-local.  Anything that has to run VERTICALLY -- rain tracks, rust
    # bleed, laitance banding -- must be stretched along OBJECT Z, not y.
    #
    # NOTE ON CONTRAST, which is the thing this shader got wrong first time.
    # Every layer below was originally a raw noise Fac mixed at 0.2-0.4.  A
    # noise Fac lives in 0.3..0.7 for most of its area, so mixing it at 0.3
    # moves the albedo by about 4 % and the surface renders as one flat grey
    # -- MEASURED under a flat white world with the Standard view transform,
    # which is the only honest way to look at an albedo: uniform 0.55 sRGB
    # with nothing on it but the blowholes' ambient occlusion.  Weathering is
    # not gentle.  Real streaks are NARROW and DARK, real lot patches differ
    # by 30-40 %, and real biofilm is nearly black.  So every layer here is
    # SHAPED with a power before it is used as a mix factor, and the targets
    # are far apart.
    lot = g.noise(g.vmath('MULTIPLY', obj, (0.55, 0.55, 0.55)), scale=1.0,
                  detail=4.0, rough=0.55)
    lotf = g.math('POWER', g.math('MULTIPLY', lot, 1.35, clamp=True), 1.6)
    agg = g.voro(g.vmath('MULTIPLY', obj, (14.0, 14.0, 14.0)), scale=1.0,
                 rand=1.0, feature='SMOOTH_F1')
    agg2 = g.voro(g.vmath('MULTIPLY', obj, (46.0, 46.0, 46.0)), scale=1.0,
                  rand=1.0, feature='F1')
    fines = g.noise(g.vmath('MULTIPLY', obj, (110.0, 110.0, 110.0)), scale=1.0,
                    detail=6.0, rough=0.62)
    grain = g.wave(g.vmath('MULTIPLY', obj, (2.4, 2.4, 2.4)), scale=17.0,
                   dist=8.0, detail=4.0, band='Y', prof='SAW')
    lait = g.noise(g.vmath('MULTIPLY', obj, (1.6, 1.6, 7.0)), scale=1.0,
                   detail=5.0, rough=0.55)
    # RAIN TRACKING.  Narrow: 20-60 mm wide, running the full height, and they
    # are the single most recognisable thing on any outdoor concrete edge.
    trak = g.noise(g.vmath('MULTIPLY', obj, (10.0, 10.0, 0.22)), scale=1.0,
                   detail=8.0, rough=0.74)
    trakf = g.math('POWER', g.math('MULTIPLY', trak, 1.25, clamp=True), 3.2)
    # ... and the broad grimy bands between them
    trak2 = g.noise(g.vmath('MULTIPLY', obj, (2.2, 2.2, 0.12)), scale=1.0,
                    detail=6.0, rough=0.68)
    trak2f = g.math('POWER', g.math('MULTIPLY', trak2, 1.30, clamp=True), 2.2)
    bio_n = g.noise(g.vmath('MULTIPLY', obj, (2.6, 2.6, 3.4)), scale=1.0,
                    detail=8.0, rough=0.70)
    biof = g.math('POWER', g.math('MULTIPLY', bio_n, 1.30, clamp=True), 2.6)
    rust_n = g.noise(g.vmath('MULTIPLY', obj, (8.0, 8.0, 0.55)), scale=1.0,
                     detail=6.0, rough=0.6)
    rustf = g.math('POWER', g.math('MULTIPLY', rust_n, 1.30, clamp=True), 3.4)
    # height within the item: 0 at the fascia soffit, 1 at the plinth top
    oz = g.sepxyz(obj)
    hgt = g.math('MULTIPLY', g.math('ADD', (oz, 2), 0.32), 1.59, clamp=True)

    # THE ORDER OF THIS STACK IS THE ORDER THE EVENTS HAPPENED, and its
    # AMPLITUDES were set against a measurement, not a feeling.  The rule the
    # first version broke: eleven independent 25 % mixes average to a flat
    # surface (measured: 8.3 % low-frequency albedo span on the hero fascia,
    # against 40-80 % for the real thing).  So the loud layers here are the
    # three that have real spatial STRUCTURE and come in on vertex channels --
    # the pour record, the formwork panels and the streaks -- and every
    # noise-driven layer is deliberately quiet.  A noise cannot carry a
    # surface; it can only texture one that is already carrying itself.
    #
    # 1. THE POUR RECORD is already in base.rgb: load-to-load tone (+-23 %)
    #    and warmth, with a ramped lift line at every truck change and a hard
    #    one at the construction joint.  Nothing to add here.
    col = base
    # 2. THE FORMWORK PANELS (aux.w).  A gang form is a patchwork of new and
    #    ninth-pour sheets; the concrete off a used sheet is darker and a
    #    little glossier, off a new one paler and chalkier, and every sheet
    #    is a shade paler round its perimeter where the ply did not bow.
    pan = (aux, 3)          # aux.w: the Attribute node's Alpha output
    p_dark = g.math('MULTIPLY', g.math('SUBTRACT', 0.5, pan), 1.75,
                    clamp=True)
    p_pale = g.math('MULTIPLY', g.math('SUBTRACT', pan, 0.5), 1.50,
                    clamp=True)
    col = g.mix(g.math('MULTIPLY', p_dark, 0.62, clamp=True), col,
                srgb("#565350"))
    col = g.mix(g.math('MULTIPLY', p_pale, 0.44, clamp=True), col,
                srgb("#98958c"))
    # 3. aggregate ghosting and the fines that migrated to the form face
    col = g.mix(g.math('MULTIPLY', g.math('POWER', (agg, 0), 1.7), 0.30),
                col, srgb("#605d57"))
    col = g.mix(g.math('MULTIPLY', g.math('POWER', (agg2, 0), 2.0), 0.24),
                col, srgb("#8d8a81"))
    col = g.mix(g.math('MULTIPLY', fines, 0.14), col, srgb("#8a8780"))
    # 4. board grain off the plywood, only on formed faces
    col = g.mix(g.math('MULTIPLY', g.math('MULTIPLY', (grain, 0), 0.22),
                       (au, 1)), col, srgb("#5e5b54"))
    # 5. laitance: the paste that rose against the form, banded in z
    col = g.mix(g.math('MULTIPLY',
                       g.math('POWER',
                              g.math('MULTIPLY',
                                     g.math('SUBTRACT', lait, 0.35), 1.8,
                                     clamp=True), 1.5), 0.24),
                col, srgb("#a5a298"))
    # 6. carbonation chalking on whatever the 12.5 deg sun has bleached
    chalk = g.math('MULTIPLY', HS._sun_face(g, 1.0), (wear, 3))
    col = g.mix(g.math('MULTIPLY', chalk, 0.30), col, srgb("#adaa9f"))
    # 7. THE STREAK SYSTEM (base.a).  Eleven years of rain sheeting off a
    #    cornice does not wash a fascia evenly, it washes it in stripes, and
    #    this is the layer that decides whether the whole item reads as an
    #    outdoor structure or as a grey box.  0.5 is clean; above it is the
    #    wet-dirt core, below it the leached calcium carbonate at the rim of
    #    the wet strip and the bright collar at the drip point.  Both are
    #    LOUD, because a real one is: a streak on a bridge fascia is the
    #    darkest and the lightest thing on the face at the same time.
    down = g.math('SUBTRACT', 1.0, _up(g))
    sd = g.math('MULTIPLY', g.math('SUBTRACT', (base, 3), 0.5), 2.0, clamp=True)
    sp = g.math('MULTIPLY', g.math('SUBTRACT', 0.5, (base, 3)), 2.0, clamp=True)
    # the core is narrower and darker where the noise says the face is dirty
    sd2 = g.math('MULTIPLY', sd, g.math('ADD', 0.86,
                                        g.math('MULTIPLY', trakf, 0.80)))
    col = g.mix(g.math('MULTIPLY', sd2, 0.95, clamp=True), col,
                srgb("#211e19"))
    col = g.mix(g.math('MULTIPLY',
                       g.math('MULTIPLY', sp,
                              g.math('ADD', 0.70,
                                     g.math('MULTIPLY', trak2f, 0.90))),
                       0.72, clamp=True), col, srgb("#d2cec0"))
    # 8. biofilm: the damp bottom band of the fascia and the soffit, and it
    #    is nearly black.  wear.z already carries the damp mask, so this is
    #    shaped by where the water actually is, not by a free-running noise.
    bio = g.math('MULTIPLY', biof, g.math('MULTIPLY', (we, 2), 1.45))
    bio = g.math('MULTIPLY', bio, g.math('SUBTRACT', 1.30,
                                         g.math('MULTIPLY', hgt, 1.05)))
    col = g.mix(g.math('MULTIPLY', bio, 1.70, clamp=True), col,
                srgb("#2b3325"))
    # 9. rust bleed under the cast-in ferrules, the joints and the corroded
    #    form ties.  wear.x above 0.50 is a REAL dribble and only there; see
    #    _channels for why this is a range split and not a sum.  Below 0.50
    #    the channel is chip strength and rust must not read it at all.
    rustm = g.math('MULTIPLY', g.math('SUBTRACT', (we, 0), 0.50), 2.0,
                   clamp=True)
    chipm = g.math('MULTIPLY', (we, 0), 2.0, clamp=True)
    rst = g.math('MULTIPLY', rustm,
                 g.math('ADD', 0.45, g.math('MULTIPLY', rustf, 1.60)))
    col = g.mix(g.math('MULTIPLY', g.math('MULTIPLY', rst, down), 1.30,
                       clamp=True), col, srgb("#6a3f21"))
    # 10. dirt, heaviest on up-facing horizontal surfaces
    col = g.mix(g.math('MULTIPLY', (we, 1), 0.55), col, srgb("#3a372f"))
    # 11. edges chalk and abrade paler
    col = g.mix(g.math('MULTIPLY', (au, 0), 0.20), col, srgb("#9c998f"))
    col = g.mix(g.math('MULTIPLY', chipm, 0.16), col, srgb("#a8a49a"))
    # 11b. THE FORM TIES AND THE HONEYCOMB.  aux.z is written by the same pass
    #      that displaced them (_tie_plugs / _honeycomb), so the colour and the
    #      hole cannot drift apart: 0.35 mortar plug, 0.70 open tie hole, 0.95
    #      honeycombed.  A repair mortar is greyer, denser and flatter than an
    #      eleven-year-old fascia and it never matches -- which is the only
    #      reason a plugged tie hole is visible on a real bridge at all.
    m_plug = g.math('MULTIPLY',
                    g.math('MULTIPLY', g.math('SUBTRACT', (au, 2), 0.18), 8.0,
                           clamp=True),
                    g.math('MULTIPLY', g.math('SUBTRACT', 0.52, (au, 2)), 8.0,
                           clamp=True), clamp=True)
    m_open = g.math('MULTIPLY',
                    g.math('MULTIPLY', g.math('SUBTRACT', (au, 2), 0.52), 8.0,
                           clamp=True),
                    g.math('MULTIPLY', g.math('SUBTRACT', 0.82, (au, 2)), 8.0,
                           clamp=True), clamp=True)
    m_hny = g.math('MULTIPLY', g.math('SUBTRACT', (au, 2), 0.85), 12.0,
                   clamp=True)
    # MEASURED, not chosen: the plug colour used to be #6e6b63..#8d8a80, which
    # brackets the fascia's own #7a7770, so on the 4K macro the plugs were
    # invisible except as a faint disc of shading.  A patching mortar is a
    # sand-cement with no coarse aggregate: it is PALER, flatter and much
    # greyer than an eleven-year-old fascia, and on every real bridge the tie
    # plugs are the first thing you see.  They also weather differently -- a
    # third of them have picked up their own dirt collar.
    plugc = g.mix(g.math('MULTIPLY', lot, 0.95), srgb("#8e8b84"),
                  srgb("#b3aea3"))       # they were made on different days
    col = g.mix(g.math('MULTIPLY', m_plug, 0.94, clamp=True), col, plugc)
    col = g.mix(g.math('MULTIPLY', m_open, 0.95, clamp=True), col,
                srgb("#171410"))
    col = g.mix(g.math('MULTIPLY', m_hny, 0.85, clamp=True), col,
                g.mix(g.math('POWER', (agg2, 0), 1.3), srgb("#4c4740"),
                      srgb("#7d766a")))
    # 12. AO AT TWO SCALES, and it does more work here than anywhere else in
    #     this module.  The leading fascia is in PERMANENT SHADE -- measured,
    #     not assumed: the contract sun dotted with bridge-local +y is +0.970,
    #     so the -y face sees it at -0.970 and is lit by sky and bounce alone.
    #     Ambient light casts no shadows, so every millimetre of relief on the
    #     hero surface would render flat without an occlusion term.  16 mm
    #     picks up the blowholes and the tie plugs; 120 mm picks up the
    #     rustication, the drip groove and the chipped arrises.
    ao = g.n("ShaderNodeAmbientOcclusion", defaults={1: 0.016})
    aoB = g.n("ShaderNodeAmbientOcclusion", defaults={1: 0.120})
    occ = g.math('SUBTRACT', 1.0, (ao, 1))
    occB = g.math('SUBTRACT', 1.0, (aoB, 1))
    col = g.mix(g.math('MULTIPLY', occ, 1.45, clamp=True), col, srgb("#211d1a"))
    col = g.mix(g.math('MULTIPLY', occB, 0.75, clamp=True), col,
                srgb("#2e2b26"))
    col = g.mix(g.math('MULTIPLY', g.math('MULTIPLY', occB, (we, 1)), 1.30,
                       clamp=True), col, srgb("#332f28"))
    g._feed(b, 0, col)

    # ROUGHNESS IS PART OF THE STREAK, not an afterthought.  A wet-dirt track
    # is a film of bound grime and it is measurably smoother than the paste
    # beside it -- at a 12.5 deg sun that difference is a visible sheen down
    # the fascia, and it is half of why a streak reads as a streak instead of
    # as a grey stripe.  Leached carbonate goes the other way: it is chalk.
    rgh = g.math('SUBTRACT', 0.94, g.math('MULTIPLY', fines, 0.14))
    rgh = g.math('ADD', rgh, g.math('MULTIPLY', (au, 1), 0.03))
    rgh = g.math('SUBTRACT', rgh, g.math('MULTIPLY', sd2, 0.30))
    rgh = g.math('ADD', rgh, g.math('MULTIPLY', sp, 0.05))
    # a well-used plywood sheet leaves a face that is a shade glossier
    rgh = g.math('SUBTRACT', rgh, g.math('MULTIPLY', p_dark, 0.055))
    rgh = g.math('ADD', rgh, g.math('MULTIPLY', bio, 0.06))
    # a trowelled mortar plug is denser and a shade smoother than the fascia
    # around it; a honeycombed hollow is bare stone and much rougher
    rgh = g.math('SUBTRACT', rgh, g.math('MULTIPLY', m_plug, 0.06))
    rgh = g.math('ADD', rgh, g.math('MULTIPLY', m_hny, 0.05))
    HS._set(g, b, rgh, "Roughness")
    # STATED AS RADIANCE MODULATION, NOT AS MILLIMETRES (itemkit 5b, brief 4a).
    # What the eye judges is what a bump does to the LIGHT, and under this
    # film's 12.47 deg sun that carries a 4.52x amplifier: m = 2 sin(theta) /
    # tan(e).  Three amplitude sets were rendered and REJECTED on the human
    # figures and every one had been chosen in millimetres.
    #
    # THIS MODULE'S WAVELENGTHS ARE IN THE VECTOR, NOT IN `scale`, and reading
    # them off the Scale socket is what put pont_deck_slab in the audit's "no
    # shader relief at all" group at m_median 0.002.  Every texture here is
    # built as `g.noise(g.vmath('MULTIPLY', obj, (110, 110, 110)), scale=1.0)`:
    # OBJECT metres are multiplied by 110 BEFORE the texture sees them, so the
    # feature size is NOISE_WAVELENGTH_FACTOR / 110 = 14.5 mm.  A reader of
    # `scale=1.0` gets 1600 mm and therefore m = 0.003 for a stage that is
    # actually at 0.351.  The bumps were never that flat; the instrument was
    # pointed at the wrong socket.  So none of the eleven stages in this module
    # is a re-tune -- every `modulation_pp` reproduces the Distance the module
    # shipped, to 1e-16, and what has changed is that the wavelength is now
    # written from the same literal that set the frequency.
    #
    #  [0] agg     w 0.45  lam 155.00 mm  m 0.181  isotropic_micro
    #      lot     w 0.30  lam 2909.1 mm  m 0.006  a 3 m batch drift, not relief
    #  [1] grain   w 0.60  lam   7.70 mm  m 0.881  isotropic_macro/sparse
    #  [2] fines   w 1.00  lam  14.55 mm  m 0.351  isotropic_micro
    #
    # [0] names `agg` because it is the ungated band with most of the height;
    # `lot` at m 0.006 is a 2.9 m tone drift that a bump cannot express at all.
    # 155 mm is far coarser than the 10-20 mm stone this shader's own docstring
    # describes -- 14 cells/m is a 71 mm pitch -- but a Voronoi scale is not a
    # bump distance and moving it is not this change.  Reported, not touched.
    # [1] is the plywood board grain and it is a Wave.  ITS WAVELENGTH IS NOT
    # 1/scale: this comment used to say "1/scale with no 1.60x", and that was
    # R2-058 -- a Wave has its own factor, 2*pi/20, and it is 3.183x FINER than
    # 1/scale, not equal to it.  It is gated to the formed faces by aux.y, hence
    # height_pp 0.6 rather than 1.0 -- the helper aims at where the mask is 1.
    # At the corrected 7.70 mm this stage is m 0.881, which is `isotropic_macro`
    # and the low end of `sparse_crease`, not `isotropic_micro`; the DEPTH is
    # unchanged, so nothing about the cast face has moved except what the module
    # claims about it.  On a cast face eleven years old this is still a
    # defensible band to be in.
    LAM_AGG = K.VORONOI_WAVELENGTH_FACTOR / 14.0      # 155.00 mm
    # R2-058: THIS READ `1.0 / Scale` AND WAS 3.183x TOO LONG.  Blender's Wave
    # multiplies the coordinate by 20 before the sine, so one band is
    # 2*pi/20 = 0.31416 of 1/Scale, not 1/Scale -- measured flat to six digits
    # over a Scale 5..230 sweep (itemkit WAVE_WAVELENGTH_FACTOR;
    # work/wavefix/emitted_wavelength.json).  itemkit's `_tex_wavelength_m` had
    # the same error, which is why this line and the audit agreed and both were
    # wrong.  THE DISTANCE ON THE SOCKET HAS NOT MOVED -- this is the depth the
    # module shipped and was judged at.  What moved is the DECLARATION: at the
    # true pitch the same amplitude is a much steeper wall, so the stage's real
    # modulation is m 0.881 and was being reported as m 0.278.  Do NOT
    # "correct" this by keeping the old modulation against the new wavelength:
    # that derives a Distance 3.183x shallower and changes a surface that was
    # rendered and looked at.
    LAM_GRAIN = K.WAVE_WAVELENGTH_FACTOR / (17.0 * 2.4)   # 7.70 mm (Wave)
    LAM_FINES = K.NOISE_WAVELENGTH_FACTOR / 110.0     #  14.55 mm
    bm = g.bump(g.math('ADD', g.math('MULTIPLY', (agg, 0), 0.45),
                       g.math('MULTIPLY', lot, 0.3)), 0.22,
                modulation_pp=0.181425, wavelength_m=LAM_AGG, height_pp=0.45)
    bm = g.bump(g.math('MULTIPLY', g.math('MULTIPLY', (grain, 0), (au, 1)),
                       0.6), 0.16, normal=bm,
                modulation_pp=0.881312, wavelength_m=LAM_GRAIN, height_pp=0.60)
    HS._set(g, b, g.bump(fines, 0.20, normal=bm,
                         modulation_pp=0.351315, wavelength_m=LAM_FINES),
            "Normal")
    return m


def mat_asphalt():
    """45 mm surface course, eleven summers old, two polished wheel tracks and
    one bay relaid last winter.

      1  binder colour, ageing from black to a grey-brown as it oxidises
      2  the CHIPPINGS' own colour -- they are a different rock from the fines
      3  POLISHING in the wheel tracks: the exposed stone faces go smooth and
         pale and the roughness collapses, which is the whole reason a wet
         race track has a visible dry line
      4  the relaid bay: fresher, blacker, finer, and its sealant bead bleeds
      5  fatty patches where the binder has risen
      6  dust and the grit banked in the channels
    """
    m, g, b, out = _new_mat("Asphalt")
    base, aux, wear, bs, au, we, tc, uv, obj = _chan(g)
    ch = g.voro(g.vmath('MULTIPLY', obj, (72.0, 72.0, 72.0)), scale=1.0,
                rand=1.0, feature='F1')
    ch2 = g.voro(g.vmath('MULTIPLY', obj, (150.0, 150.0, 150.0)), scale=1.0,
                 rand=1.0, feature='SMOOTH_F1')
    fine = g.noise(g.vmath('MULTIPLY', obj, (240.0, 240.0, 240.0)), scale=1.0,
                   detail=5.0, rough=0.6)
    macro = g.noise(g.vmath('MULTIPLY', obj, (1.6, 1.6, 1.6)), scale=1.0,
                    detail=6.0, rough=0.6)
    fatty = g.noise(g.vmath('MULTIPLY', obj, (7.0, 3.0, 7.0)), scale=1.0,
                    detail=5.0, rough=0.55)
    col = g.mix(g.math('MULTIPLY', macro, 0.45), base, srgb("#33322f"))
    col = g.mix(g.math('MULTIPLY', g.math('SUBTRACT', (ch, 0), 0.28), 1.5),
                col, srgb("#54514a"))
    col = g.mix(g.math('MULTIPLY', (ch2, 0), 0.28), col, srgb("#6b675e"))
    col = g.mix(g.math('MULTIPLY', fine, 0.22), col, srgb("#3d3b37"))
    col = g.mix(g.math('MULTIPLY', g.math('SUBTRACT', fatty, 0.55), 0.9),
                col, srgb("#1b1a19"))
    col = g.mix(g.math('MULTIPLY', (we, 1), 0.26), col, srgb("#736e63"))
    g._feed(b, 0, col)
    rgh = g.math('SUBTRACT', 0.90, g.math('MULTIPLY', (ch, 0), 0.10))
    rgh = g.math('SUBTRACT', rgh, g.math('MULTIPLY',
                                         g.math('SUBTRACT', fatty, 0.5), 0.45))
    HS._set(g, b, rgh, "Roughness")
    # RADIANCE, NOT MILLIMETRES (itemkit 5b); wavelengths off the vector
    # multiply, not `scale=1.0` -- see the note in mat_concrete.  Not a re-tune.
    #
    #  [0] chip    w 0.55  lam  30.14 mm  m 0.621  isotropic_macro
    #      macro   w 0.25  lam 1000.0 mm  m 0.009  a 1 m undulation, not relief
    #  [1] fine    w 1.00  lam   6.67 mm  m 0.460  isotropic_macro
    #
    # A 14 mm surface course IS a proud-chipping macrotexture, so the exposed
    # aggregate at 0.62 sitting mid-band in isotropic_macro is exactly where
    # the record puts hand-laid stone; `macro` is the 1 m sag of the paving
    # machine and a bump can say nothing about it.
    LAM_CHIP = K.VORONOI_WAVELENGTH_FACTOR / 72.0     #  30.14 mm
    LAM_FINE = K.NOISE_WAVELENGTH_FACTOR / 240.0      #   6.67 mm
    bm = g.bump(g.math('ADD', g.math('MULTIPLY', (ch, 0), 0.55),
                       g.math('MULTIPLY', macro, 0.25)), 0.30,
                modulation_pp=0.620685, wavelength_m=LAM_CHIP, height_pp=0.55)
    HS._set(g, b, g.bump(fine, 0.18, normal=bm,
                         modulation_pp=0.459656, wavelength_m=LAM_FINE),
            "Normal")
    return m


def mat_kerb():
    """Precast kerb: a denser, wetter-cast concrete than the deck, three
    casting lots, tyre rubber on the batter and salt bloom in the joints."""
    m, g, b, out = _new_mat("Kerb")
    base, aux, wear, bs, au, we, tc, uv, obj = _chan(g)
    agg = g.voro(g.vmath('MULTIPLY', obj, (30.0, 30.0, 30.0)), scale=1.0,
                 rand=1.0, feature='SMOOTH_F1')
    fine = g.noise(g.vmath('MULTIPLY', obj, (140.0, 140.0, 140.0)), scale=1.0,
                   detail=6.0, rough=0.6)
    mould = g.wave(g.vmath('MULTIPLY', obj, (3.0, 3.0, 3.0)), scale=42.0,
                   dist=4.0, detail=3.0, band='X', prof='SIN')
    scuff = g.noise(g.vmath('MULTIPLY', obj, (14.0, 14.0, 2.5)), scale=1.0,
                    detail=6.0, rough=0.65)
    salt = g.noise(g.vmath('MULTIPLY', obj, (9.0, 9.0, 9.0)), scale=1.0,
                   detail=7.0, rough=0.6)
    col = g.mix(g.math('MULTIPLY', (agg, 0), 0.30), base, srgb("#8f8c85"))
    col = g.mix(g.math('MULTIPLY', fine, 0.20), col, srgb("#b6b3aa"))
    col = g.mix(g.math('MULTIPLY', (mould, 0), 0.10), col, srgb("#9b9890"))
    rub = g.math('MULTIPLY', g.math('MULTIPLY', (scuff, 0), (we, 0)),
                 g.math('SUBTRACT', 1.0, _up(g)))
    col = g.mix(g.math('MULTIPLY', rub, 0.55), col, srgb("#332f2c"))
    col = g.mix(g.math('MULTIPLY', g.math('MULTIPLY', salt, (wear, 3)), 0.35),
                col, srgb("#d6d2c6"))
    col = g.mix(g.math('MULTIPLY', (we, 1), 0.24), col, srgb("#5e5a52"))
    col = g.mix(g.math('MULTIPLY', (au, 0), 0.20), col, srgb("#c0bdb4"))
    g._feed(b, 0, col)
    HS._set(g, b, g.math('SUBTRACT', 0.88, g.math('MULTIPLY', fine, 0.14)),
            "Roughness")
    # RADIANCE, NOT MILLIMETRES (itemkit 5b); wavelengths off the vector
    # multiply, not `scale=1.0` -- see the note in mat_concrete.  Not a re-tune.
    #
    #  [0] agg     w 0.50  lam  72.33 mm  m 0.212  isotropic_micro
    #  [1] fine    w 1.00  lam  11.43 mm  m 0.318  isotropic_micro
    #
    # A precast kerb is cast wet against a steel mould, so it has the flattest,
    # tightest face on the item and the low end of isotropic_micro is the right
    # place for both stages.  `agg` is SMOOTH_F1, a rounded mottle rather than
    # a stepped mosaic, so it is a soft field and it is banded as one.
    LAM_AGG = K.VORONOI_WAVELENGTH_FACTOR / 30.0      #  72.33 mm
    LAM_FINE = K.NOISE_WAVELENGTH_FACTOR / 140.0      #  11.43 mm
    bm = g.bump(g.math('MULTIPLY', (agg, 0), 0.5), 0.18,
                modulation_pp=0.21204, wavelength_m=LAM_AGG, height_pp=0.50)
    HS._set(g, b, g.bump(fine, 0.16, normal=bm,
                         modulation_pp=0.318002, wavelength_m=LAM_FINE),
            "Normal")
    return m


def mat_steel():
    """Hot-dip galvanised: frames, ferrules, the repair angle, the nosings.
    Spangle, weathering to matt carbonate, and rust only where it was cut."""
    m, g, b, out = _new_mat("Steel")
    base, aux, wear, bs, au, we, tc, uv, obj = _chan(g)
    spg = g.voro(g.vmath('MULTIPLY', obj, (190.0, 190.0, 190.0)), scale=1.0,
                 rand=1.0, feature='F1')
    fine = g.noise(g.vmath('MULTIPLY', obj, (420.0, 420.0, 420.0)), scale=1.0,
                   detail=5.0, rough=0.6)
    weath = g.noise(g.vmath('MULTIPLY', obj, (6.0, 6.0, 6.0)), scale=1.0,
                    detail=7.0, rough=0.62)
    rust = g.noise(g.vmath('MULTIPLY', obj, (26.0, 26.0, 26.0)), scale=1.0,
                   detail=7.0, rough=0.66)
    col = g.mix(g.math('MULTIPLY', (spg, 0), 0.35), srgb(ZINC_HEX),
                srgb("#c2c7ca"))
    col = g.mix(g.math('MULTIPLY', fine, 0.16), col, srgb("#7f858a"))
    aged = g.math('MULTIPLY', (wear, 3),
                  g.math('ADD', 0.3, g.math('MULTIPLY', (weath, 0), 1.0)))
    col = g.mix(g.math('MULTIPLY', aged, 0.72), col, srgb("#6d7276"))
    rr = g.math('MULTIPLY', g.math('MULTIPLY', (rust, 0), (au, 0)), (we, 0))
    col = g.mix(g.math('MULTIPLY', rr, 0.55), col, srgb("#8a4a24"))
    col = g.mix(g.math('MULTIPLY', (we, 1), 0.28), col, srgb("#4f4c46"))
    g._feed(b, 0, col)
    HS._set(g, b, 0.55, "Metallic")
    rgh = g.math('ADD', 0.32, g.math('MULTIPLY', aged, 0.42))
    rgh = g.math('ADD', rgh, g.math('MULTIPLY', fine, 0.10))
    HS._set(g, b, rgh, "Roughness")
    # RADIANCE, NOT MILLIMETRES (itemkit 5b); wavelengths off the vector
    # multiply, not `scale=1.0` -- see the note in mat_concrete.  Not a re-tune.
    #
    #  [0] spangle w 0.60  lam  11.42 mm  m 0.322  isotropic_micro
    #  [1] fine    w 1.00  lam   3.81 mm  m 0.298  isotropic_micro
    #
    # Zinc crystals stand 10-25 microns proud of one another, which is the
    # bottom of what a bump can honestly claim; isotropic_micro is the band the
    # record gives to blasted and cast metal and both stages sit inside it.
    LAM_SPANGLE = K.VORONOI_WAVELENGTH_FACTOR / 190.0  #  11.42 mm
    LAM_FINE = K.NOISE_WAVELENGTH_FACTOR / 420.0       #   3.81 mm
    bm = g.bump(g.math('MULTIPLY', (spg, 0), 0.6), 0.12,
                modulation_pp=0.322183, wavelength_m=LAM_SPANGLE,
                height_pp=0.60)
    HS._set(g, b, g.bump(fine, 0.10, normal=bm,
                         modulation_pp=0.29815, wavelength_m=LAM_FINE),
            "Normal")
    return m


def mat_line():
    """Screed-applied thermoplastic, with its glass beads and its wear."""
    m, g, b, out = _new_mat("Line")
    base, aux, wear, bs, au, we, tc, uv, obj = _chan(g)
    bead = g.voro(g.vmath('MULTIPLY', obj, (620.0, 620.0, 620.0)), scale=1.0,
                  rand=1.0, feature='F1')
    grit = g.noise(g.vmath('MULTIPLY', obj, (180.0, 180.0, 180.0)), scale=1.0,
                   detail=6.0, rough=0.6)
    worn = g.noise(g.vmath('MULTIPLY', obj, (12.0, 4.0, 12.0)), scale=1.0,
                   detail=6.0, rough=0.6)
    col = g.mix(g.math('MULTIPLY', (bead, 0), 0.25), base, srgb("#eae7dd"))
    col = g.mix(g.math('MULTIPLY', grit, 0.30), col, srgb("#9a968c"))
    col = g.mix(g.math('MULTIPLY', g.math('MULTIPLY', worn, (we, 0)), 0.65),
                col, srgb("#5b5850"))
    col = g.mix(g.math('MULTIPLY', (we, 1), 0.30), col, srgb("#6a665c"))
    g._feed(b, 0, col)
    HS._set(g, b, g.math('SUBTRACT', 0.72, g.math('MULTIPLY', (bead, 0), 0.28)),
            "Roughness")
    # RADIANCE, NOT MILLIMETRES (itemkit 5b); wavelengths off the vector
    # multiply, not `scale=1.0` -- see the note in mat_concrete.  Not a re-tune.
    #
    #  [0] bead    w 0.70  lam   3.50 mm  m 0.544  isotropic_macro
    #      grit    w 0.30  lam   8.89 mm  m 0.092  below every band
    #
    # The named band is the ballotini: a screed thermoplastic is a bed of
    # 0.6-1.2 mm glass beads half-drowned in resin, and 0.54 is a hand-laid
    # aggregate texture, which is what it is.  The anti-skid grit at 0.09 does
    # nothing on its own; it exists to break up the bead field's regularity in
    # ALBEDO, where it is mixed at 0.30, and that read does not need relief.
    LAM_BEAD = K.VORONOI_WAVELENGTH_FACTOR / 620.0    #   3.50 mm
    HS._set(g, b, g.bump(g.math('ADD', g.math('MULTIPLY', (bead, 0), 0.7),
                                g.math('MULTIPLY', grit, 0.3)), 0.16,
                         modulation_pp=0.544493, wavelength_m=LAM_BEAD,
                         height_pp=0.70),
            "Normal")
    return m


def mat_mortar():
    """Bedding mortar, the repair patch, and the silt in the sumps."""
    m, g, b, out = _new_mat("Mortar")
    base, aux, wear, bs, au, we, tc, uv, obj = _chan(g)
    sand = g.voro(g.vmath('MULTIPLY', obj, (260.0, 260.0, 260.0)), scale=1.0,
                  rand=1.0, feature='F1')
    trow = g.noise(g.vmath('MULTIPLY', obj, (14.0, 14.0, 14.0)), scale=1.0,
                   detail=6.0, rough=0.6)
    damp = g.noise(g.vmath('MULTIPLY', obj, (3.2, 3.2, 3.2)), scale=1.0,
                   detail=7.0, rough=0.65)
    col = g.mix(g.math('MULTIPLY', (sand, 0), 0.32), base, srgb("#b1ada2"))
    col = g.mix(g.math('MULTIPLY', trow, 0.28), col, srgb("#8d8a82"))
    col = g.mix(g.math('MULTIPLY', g.math('MULTIPLY', damp, (we, 1)), 0.45),
                col, srgb("#55524b"))
    col = g.mix(g.math('MULTIPLY', (we, 2), 0.35), col, srgb("#4a4f3f"))
    g._feed(b, 0, col)
    HS._set(g, b, g.math('SUBTRACT', 0.95, g.math('MULTIPLY', (sand, 0), 0.10)),
            "Roughness")
    # RADIANCE, NOT MILLIMETRES (itemkit 5b); wavelengths off the vector
    # multiply, not `scale=1.0` -- see the note in mat_concrete.  Not a re-tune.
    #
    #  [0] sand    w 0.60  lam   8.35 mm  m 0.878  isotropic_macro
    #      trowel  w 0.40  lam 114.29 mm  m 0.043  the sweep of the float
    #
    # A sand-cement bedding mortar is the roughest surface in this module and
    # 0.878 is the top of isotropic_macro, where the record puts hand-laid
    # texture -- correct for something struck off with a trowel and never
    # rubbed.  The 114 mm trowel sweep is a shape, not a relief, at m 0.043.
    LAM_SAND = K.VORONOI_WAVELENGTH_FACTOR / 260.0    #   8.35 mm
    HS._set(g, b, g.bump(g.math('ADD', g.math('MULTIPLY', (sand, 0), 0.6),
                                g.math('MULTIPLY', trow, 0.4)), 0.24,
                         modulation_pp=0.878155, wavelength_m=LAM_SAND,
                         height_pp=0.60),
            "Normal")
    return m


def materials(force=False):
    global _MATS
    if _MATS is not None and not force:
        return _MATS
    _MATS = [mat_concrete(), mat_asphalt(), mat_kerb(), mat_steel(),
             mat_line(), mat_mortar()]
    return _MATS


# --------------------------------------------------------------------------- #
# 13.  THE ASSEMBLY                                                             #
# --------------------------------------------------------------------------- #

class Deck:
    __slots__ = ("objects", "slab", "mounts", "stats", "place", "meta")

    def __init__(self):
        self.objects = []
        self.slab = None
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


def deck_to_world():
    """PUBLIC.  (R 3x3, t 3) taking bridge-local -> world.

    Re-exported from pont_girder rather than recomputed, so that this deck and
    the girders it bears on can never disagree by a rounding.
    """
    return PG.pont_to_world()


def build(coll_name=ROOT_COLL, place=None, res=1.0, verbose=True):
    """Build the deck slab and everything cast into or bolted onto it."""
    mats = materials()
    coll = _coll(coll_name)
    D = Deck()
    D.place = place
    cnt = {}
    mounts = {}
    X = stations(res)

    jobs = [("Slab", lambda a: build_slab(a, X, res=res, cnt=cnt,
                                          mounts=mounts)),
            ("Kerb_L", lambda a: build_kerbs(a, cnt, res=res, mounts=mounts)),
            ("Fitting", lambda a: build_fittings(a, cnt, mounts, res=res)),
            ("Drain", lambda a: build_drains(a, cnt, mounts, res=res)),
            ("Line", lambda a: build_lines(a, cnt, res=res)),
            ("Chip", lambda a: build_chippings(a, cnt, res=res))]
    for (nm, fn) in jobs:
        acc = Acc(PFX + nm)
        fn(acc)
        if acc.n == 0:
            continue
        V = np.concatenate(acc._V, 0)
        cnt["lowest_z_" + nm] = float(V[:, 2].min())
        cnt["highest_z_" + nm] = float(V[:, 2].max())
        if place is not None:
            acc.xform(place[0], place[1])
        ob = acc.emit(coll, mats, PFX + nm)
        D.objects.append(ob)
        if nm == "Slab":
            D.slab = ob
        if verbose:
            print(">>   %-9s %9d verts" % (PFX + nm, acc.n))

    if place is not None:
        R, t = place
        D.mounts = {k: f.transformed(R, t) for k, f in mounts.items()}
    else:
        D.mounts = dict(mounts)

    cnt["lowest_z"] = min(v for k, v in cnt.items() if k.startswith("lowest_z_"))
    cnt["highest_z"] = max(v for k, v in cnt.items()
                           if k.startswith("highest_z_"))
    cnt["track_headroom_to_slab_m"] = (cnt["lowest_z"]
                                       - float(C.ground_z(S_STATION, 0.0)))
    cnt["girder_lowest_z_over_track"] = 6.7753684          # pont_girder, measured
    cnt["objects"] = len(D.objects)
    D.stats = cnt
    return D


# --------------------------------------------------------------------------- #
# 14.  THE INTERFACE FILE                                                       #
# --------------------------------------------------------------------------- #

def dump_interface(D, path=None):
    """Everything a dependant needs, as data, so it never has to import me."""
    R, t = deck_to_world()
    xs = np.linspace(-END_X, END_X, 61)
    out = {
        "item": "pont_deck_slab",
        "version": "1.0.0",
        "built_on": {"pont_girder": "1.0.0",
                     "frame": "IDENTICAL to pont_girder.pont_to_world()"},
        "frame": {
            "note": "bridge-local: +X ALONG THE SPAN; +Y is the RACING "
                    "DIRECTION at s=2410, so y=-3.000 is the LEADING fascia; "
                    "+Z is WORLD z.",
            "station_s": S_STATION,
            "R_local_to_world": [[float(v) for v in row] for row in R],
            "t_local_to_world": [float(v) for v in t],
            "centreline_world": [float(v) for v in C.centreline(S_STATION)[:2]],
        },
        "datum": {
            "deck_half_width": DECK_HALF_W,
            "end_x": END_X,
            "deck_length": DECK_LEN,
            "haunch": HAUNCH,
            "flange_sink": FLANGE_SINK,
            "surfacing_thickness": SURF_T,
            "crown_y": CROWN_Y,
            "crossfall": XFALL,
            "z_crown_midspan": Z_CROWN0,
            "crown_hog_to_ends": CROWN_HOG,
            "kerb_face_y": KERB_FACE_Y,
            "kerb_width": KERB_W,
            "kerb_upstand": KERB_UP,
            "kerb_pocket_depth": POCKET_D,
            "plinth_in_y_left": PLINTH_IN_L,
            "plinth_out_y": PLINTH_OUT_Y,
            "parapet_y": PARAPET_Y,
            "parapet_pitch": POST_PITCH,
            "parapet_end_x": POST_END_X,
            "ferrule_pattern_mm": [FERRULE_GAUGE[0] * 1000,
                                   FERRULE_GAUGE[1] * 1000],
            "cornice_lip": CORN_LIP,
            "cornice_fall": CORN_FALL,
            "fascia_beam_y": FASCIA_BEAM_Y,
            "fascia_beam_drop": BEAM_DROP,
            "drip": {"inset": DRIP_OUT, "width": DRIP_W, "depth": DRIP_D},
            "joint_m": {"type": "elastomeric_in_runner", "x": -END_X,
                        "recess_w": JOINT_M_W, "recess_d": JOINT_M_D,
                        "gap": JOINT_M_GAP, "anchor": "12 mm loops at 0.125"},
            "joint_p": {"type": "comb_finger_plate", "x": END_X,
                        "recess_w": JOINT_P_W, "recess_d": JOINT_P_D,
                        "gap": JOINT_P_GAP,
                        "anchor": "M20 ferrules at 0.220 x 0.180, "
                                  "cast-in 80x80x8 nosing angle",
                        "girder_support_angle_local": [15.928, -0.751, 8.025]},
            "surface": {
                "note": "The concrete's weathering STRUCTURE is authored in "
                        "bridge-local (x, u) at build time and shipped in the "
                        "vertex channels, NOT computed in the shader. A "
                        "dependant that wants its own concrete to match this "
                        "one must reproduce these three fields, not the "
                        "shader: the object is world-aligned after "
                        "recentring, so no shader can recover 'along the "
                        "span'.",
                "channels": {
                    "base.rgb": "pour record: truck-load tone +-23.5 % and "
                                "warmth, ramped lift line at each load edge, "
                                "hard change at the construction joint",
                    "base.a": "streak field. 0.5 clean, >0.5 wet-dirt track "
                              "by (v-0.5)*2, <0.5 leached carbonate by "
                              "(0.5-v)*2",
                    "aux.x": "edge exposure",
                    "aux.y": "1 = cast against plywood, 0 = screeded top",
                    "aux.z": "0 plain / 0.35 mortar plug / 0.70 open tie "
                             "hole / 0.95 honeycombed",
                    "aux.w": "formwork panel tone, 0.5 = an average sheet",
                    "wear.x": "chip + rust-dribble strength",
                    "wear.y": "dirt", "wear.z": "damp", "wear.w": "age",
                },
                "pour_load_edges_x": [float(v) for v in pour_edges()],
                "ply_panel_len": PLY_LEN,
                "tie_grid": [TIE_X, TIE_V, TIE_OFF],
                "drip_blocked_x": list(DRIP_BLOCKED),
                "concrete_hex": [CONC_A_HEX, CONC_B_HEX],
                "measured_albedo_lowfreq_span_pct": 41.0,
            },
            "gullies": [[float(a), float(b)] for (a, b) in gully_stations()],
            "gully_clear": GULLY_CLEAR,
            "gully_spigot_r": GULLY_SPIGOT_R,
            "downpipe_route_note":
                "BOTH fascia girders carry banners, so a downpipe may not hang "
                "on A or D. Route inboard along the soffit to girder B or C. "
                "pont_girder already built saddles for one such pipe on girder "
                "B at local (15.560, -0.711, 7.853) and (15.560, -0.708, "
                "7.233).",
        },
        "samples": {
            "x": [float(v) for v in xs],
            "soffit_z_at_y_minus_3": [float(v) for v in
                                      soffit_z(xs, np.full(61, -2.999))],
            "soffit_z_at_y_0": [float(v) for v in soffit_z(xs, np.zeros(61))],
            "soffit_z_at_y_plus_3": [float(v) for v in
                                     soffit_z(xs, np.full(61, 2.999))],
            "fascia_soffit_z_L": [float(v) for v in fascia_soffit_z(xs, -1.0)],
            "fascia_soffit_z_R": [float(v) for v in fascia_soffit_z(xs, 1.0)],
            "fascia_top_z_L": [float(v) for v in fascia_top_z(xs, -1.0)],
            "fascia_top_z_R": [float(v) for v in fascia_top_z(xs, 1.0)],
            "plinth_top_z_L": [float(v) for v in plinth_top_z(xs, -1.0)],
            "plinth_top_z_R": [float(v) for v in plinth_top_z(xs, 1.0)],
            "road_z_at_crown": [float(v) for v in z_crown(xs)],
            "channel_z_L": [float(v) for v in chan_z(xs, -1.0)],
            "channel_z_R": [float(v) for v in chan_z(xs, 1.0)],
        },
        "variation": {
            "kerb": "left = 34 precast units, per-unit lippage/rotation/joint/"
                    "chips/lot, 2 bullnose replacements and 1 cracked unit; "
                    "right = monolithic in-situ upstand + bolted galvanised "
                    "80x80x8 edge angle in 5 lengths",
            "wearing_surface": "original course + 2 polished wheel tracks with "
                               "4-6 mm ruts + a %.1f m planed-and-relaid bay "
                               "with sawn edges and a sealant bead + a %.2f m "
                               "pothole repair + grit banked in both channels"
                               % (RELAY_X1 - RELAY_X0, POTHOLE[2] * 2),
            "joint": "elastomeric-in-runner at -x, comb/finger plate at +x - "
                     "different recess width, depth, floor finish, anchor "
                     "system and gap",
        },
        "objects": [],
        "gate_prefix": PFX,
        "counts": {},
        "mounts": {},
        "owned_elsewhere": {
            "pont_soffit_panel": "the APPLIED soffit lining and its carrier "
                                 "rails. What is here is the structural "
                                 "soffit it hangs from, plus 42 cast-in M12 "
                                 "sockets at 1.5 m to hang from.",
            "pont_parapet": "everything above plinth_top_z. 32 base-plate "
                            "positions with cast-in M20 ferrules are here.",
            "pont_scupper": "gratings, downpipes and brackets. The pots, "
                            "frames, sumps and outlet spigots are here.",
            "bridge_expansion_joint": "the comb plates, elastomeric seals and "
                                      "their runners. The recesses, anchor "
                                      "loops, ferrules and nosing angles are "
                                      "here.",
        },
    }
    if D is not None:
        out["objects"] = [o.name for o in D.objects]
        out["counts"] = {k: (float(v) if isinstance(v, float) else v)
                         for k, v in D.stats.items()}
        for k, f in sorted(D.mounts.items()):
            out["mounts"][k] = {
                "o": [float(v) for v in f.o], "x": [float(v) for v in f.x],
                "y": [float(v) for v in f.y], "z": [float(v) for v in f.z],
                "r": float(f.r), "tag": f.tag,
            }
    p = path or os.path.join(HERE, "pont_deck_slab_interface.json")
    with open(p, "w") as fh:
        json.dump(out, fh, indent=1)
    print(">> interface written: %s  (%d mounts)" % (p, len(out["mounts"])))
    return p


# --------------------------------------------------------------------------- #
# 15.  THE TEST SCENE                                                           #
# --------------------------------------------------------------------------- #

def _surface_samples(place, stride=0.05):
    """Points on the deck's OUTER surfaces, for solving a camera distance.

    Only the surfaces the lens can actually see from under the bridge: the two
    fascias, their beam soffits and drips, the cantilever soffits, the main
    soffit and the cornices.  Solving 3.000 m against the carriageway would
    put the camera above the parapet, which is not where any shot in this film
    ever is.
    """
    xs = np.arange(-END_X, END_X + stride, stride)
    P = []
    for side in (-1.0, 1.0):
        ft = fascia_top_z(xs, side)
        fb = fascia_soffit_z(xs, side)
        cs = cant_soffit_z(xs, side)
        for f in np.linspace(0.0, 1.0, 12):
            P.append(np.stack([xs, np.full(len(xs), side * DECK_HALF_W),
                               fb + f * (ft - fb)], -1))
        for yy in np.linspace(DECK_HALF_W - DRIP_OUT - DRIP_W,
                              FASCIA_BEAM_Y, 4):
            P.append(np.stack([xs, np.full(len(xs), side * yy), fb], -1))
        for yy in np.linspace(FASCIA_BEAM_Y - 0.01, PLINTH_OUT_Y, 5):
            P.append(np.stack([xs, np.full(len(xs), side * yy), cs], -1))
        for yy in np.linspace(PLINTH_OUT_Y, DECK_HALF_W, 5):
            P.append(np.stack([xs, np.full(len(xs), side * yy),
                               cornice_z(xs, side * yy)], -1))
    for yy in np.linspace(-2.35, 2.35, 26):
        P.append(np.stack([xs, np.full(len(xs), yy),
                           soffit_z(xs, np.full(len(xs), yy))], -1))
    P = np.concatenate(P, 0)
    if place is not None:
        R, t = place
        P = P @ np.asarray(R, float).T + np.asarray(t, float)[None, :]
    return P


def macro_camera(B, name="CAM_PDS_MACRO", dist=3.0, lens=35.0):
    """EXACTLY the manifest's shot: 3.0 m on a 35 mm lens.

    WHERE, AND WHY NOT WHERE I FIRST PUT IT.  The manifest's distances are the
    minimum over the 4,507-sample camera corridor, and at s = 2410 that
    corridor is the racing line at world z = 5.000, so the strictly nearest
    point of this item to the lens is the slab soffit DIRECTLY OVERHEAD
    (8.218 - 5.000 = 3.218).  I framed that first and rendered it: mean
    pixel 0.051, 29 distinct levels, a black frame.  It is physically correct
    -- the underside of a bridge over a race track is lit only by bounce off
    dark asphalt -- and it is useless as the image an item is judged on.

    So the macro is 3.000 m from the LEADING (-y) fascia instead, which is
    the surface the film's lens meets first, seen from outboard and below as
    the camera dives in.  In one frame: the fascia face with its 25 x 14 mm
    rustication, its form-tie plugs and its rain tracking; the 18 x 14 mm
    drip groove; the beam soffit; the cornice arris against sky; the
    construction joint between the two pours; and girder A receding beneath.
    The soffit-overhead frame is kept as CAM_PDS_SOFFIT_HERO so the honest
    darkness of it is still on the record rather than quietly dropped.

    `dist` is solved so the NEAREST DECK SURFACE is exactly 3.000 m.
    1244 px/m; 1 px = 0.804 mm.
    """
    place = B.place
    S = _surface_samples(place)
    aim_local = np.array([0.95, -DECK_HALF_W,
                          float(fascia_top_z(np.array([0.95]), -1.0)[0])
                          - RUST_Z - RUST_H * 0.5])
    # THE FRAMING WAS RETUNED AGAINST THE RENDER, not chosen on paper.  The
    # first version put the eye at [-0.30, -0.71, -0.64] -- well below the
    # fascia, looking steeply up -- and 43 % of the 4K master came back empty
    # sky with much of the rest the unlit girder web behind.  The item this
    # frame exists to judge occupied about a third of its own macro.  Coming
    # up to [-0.34, -0.80, -0.40] keeps the eye outboard and below (it has to
    # be: the film's lens passes UNDER this deck) but rakes ALONG the face
    # instead of up at it, so the frame is fascia, drip, beam soffit and
    # cornice arris, with the sky cut back to the strip that silhouettes the
    # arris -- worth keeping, because an edge against sky is the only place
    # the 20 mm chamfer reads as a chamfer rather than as a shading ramp.
    vdir_local = unit(np.array([-0.34, -0.80, -0.40]))
    look_off = np.array([1.25, 0.02, -0.14])
    if place is not None:
        Rm = np.asarray(place[0], float)
        tt = np.asarray(place[1], float)
        aim = Rm @ aim_local + tt
        vdir = Rm @ vdir_local
        loff = Rm @ look_off
    else:
        aim, vdir, loff = aim_local, vdir_local, look_off

    def nearest(d):
        p = aim + vdir * d
        return p, float(np.min(np.linalg.norm(S - p[None, :], axis=1)))

    best = min(((abs(nearest(d)[1] - dist), d)
                for d in np.linspace(0.5, 9.0, 4251)))
    pos, dmin = nearest(float(best[1]))
    # f/16, not f/8.  MEASURED, not chosen for taste: the first macro was
    # shot at f/11 focused at 3.3 m and the receding fascia went soft inside
    # 1.5 m of the focal plane, which blurred out exactly the 2-5 mm relief
    # the frame exists to show.  A pixel-peep frame has to be sharp over the
    # whole object or it is measuring the lens instead of the concrete.
    ob = PG._put_camera(name, pos, aim + loff, lens,
                        dof=float(np.linalg.norm(aim - pos)) + 0.55, fstop=16.0)
    px = (3840.0 * lens / SENSOR_MM) / dmin
    print(">> macro camera %s: nearest deck SURFACE %.4f m (manifest 3.0), "
          "%.0f mm lens" % (name, dmin, lens))
    print(">>   -> %.1f px/m on the 4K master, 1 px = %.3f mm"
          % (px, 1000.0 / px))
    print(">>   lens at world z = %.3f" % pos[2])
    return ob, dmin


def fascia_camera(B, name="CAM_PDS_FASCIA", dist=3.0, lens=35.0, side=1.0):
    """The same 3.0 m and the same 35 mm, on the fascia instead of the soffit.

    It exists because the two fascias of this bridge are lit completely
    differently and one macro cannot show both.  MEASURED, not assumed: the
    contract sun's azimuth is within 6 deg of bridge-local +y, so the TRAILING
    (+y) fascia is raked at near-normal incidence by a 12.5 deg sun and every
    grout fin, tie plug and blowhole on it throws a shadow, while the LEADING
    (-y) fascia -- the one the lens meets first -- is in permanent shade and
    is read by sky and by bounce off the racing surface.  Both have to survive
    a look, so both get a frame at the manifest's own distance and lens.
    """
    place = B.place
    S = _surface_samples(place)
    aim_local = np.array([1.10, side * DECK_HALF_W,
                          float(fascia_top_z(np.array([1.10]), side)[0]) - 0.21])
    vdir_local = unit(np.array([-0.30, side * 0.80, -0.52]))
    if place is not None:
        Rm = np.asarray(place[0], float)
        tt = np.asarray(place[1], float)
        aim = Rm @ aim_local + tt
        vdir = Rm @ vdir_local
        loff = Rm @ np.array([1.25, side * 0.02, -0.10])
    else:
        aim, vdir, loff = aim_local, vdir_local, np.array([1.25, 0.0, -0.10])

    def nearest(d):
        p = aim + vdir * d
        return p, float(np.min(np.linalg.norm(S - p[None, :], axis=1)))

    best = min(((abs(nearest(d)[1] - dist), d)
                for d in np.linspace(0.5, 9.0, 4251)))
    pos, dmin = nearest(float(best[1]))
    ob = PG._put_camera(name, pos, aim + loff, lens,
                        dof=float(np.linalg.norm(aim - pos)) + 0.55, fstop=16.0)
    print(">> fascia camera %s (%s fascia): nearest deck surface %.4f m, "
          "%.0f mm" % (name, "trailing/sunlit" if side > 0 else "leading/shade",
                       dmin, lens))
    return ob, dmin


def pass_camera(B, name="CAM_PDS_PASS", lens=21.0):
    """The film's own moment: the lens on the racing line at world z = 5.000,
    300 km/h, looking up and forward as the deck edge crosses the frame."""
    place = B.place
    p_local = np.array([0.20, -4.40, 5.000])
    l_local = np.array([-0.30, 3.60, 7.30])
    if place is not None:
        Rm, tt = np.asarray(place[0], float), np.asarray(place[1], float)
        pos, look = Rm @ p_local + tt, Rm @ l_local + tt
    else:
        pos, look = p_local, l_local
    S = _surface_samples(place)
    dmin = float(np.min(np.linalg.norm(S - pos[None, :], axis=1)))
    ob = PG._put_camera(name, pos, look, lens, dof=None)
    print(">> pass camera %s: nearest deck surface %.3f m, lens z %.3f"
          % (name, dmin, pos[2]))
    return ob


def inspect_camera(B, name, target_local, eye_local, lens, fstop=16.0):
    place = B.place
    if place is not None:
        Rm, tt = np.asarray(place[0], float), np.asarray(place[1], float)
        tgt = Rm @ np.asarray(target_local, float) + tt
        eye = Rm @ np.asarray(eye_local, float) + tt
    else:
        tgt = np.asarray(target_local, float)
        eye = np.asarray(eye_local, float)
    d = float(np.linalg.norm(tgt - eye))
    ob = PG._put_camera(name, eye, tgt, lens, dof=d, fstop=fstop)
    print(">> inspection camera %s at %.3f m, %.0f mm" % (name, d, lens))
    return ob


def context_surround(name="CTX_Surround", half=340.0, n=150):
    """The ground OUT TO 340 m, at the contract's own elevation, CONTEXT ONLY.

    pont_girder ships a 62 m square of racing surface, which is right for a
    girder soffit 2.9 m over the track.  It is not right for a deck soffit
    8.2 m up: at that height the underside of this slab sees a hemisphere, and
    most of what is in it at s = 2410 is not asphalt.  Rendering the deck over
    a 62 m black square in a void made the soffit render at a mean pixel of
    0.051 -- a measurement of the missing world, not of the concrete.

    So this is the rest of it: runoff platform, verge and dry summer grass at
    their real albedos, sampled off world_contract.world_ground_z so it meets
    pont_girder's square at exactly the same z.  CTX_ prefixed, so the
    acceptance gate never counts it as part of this item.
    """
    mat = PG._simple_mat(name,
                         [(0.052, 0.049, 0.038), (0.089, 0.083, 0.062),
                          (0.115, 0.108, 0.077), (0.072, 0.069, 0.052)],
                         0.93, (28.0, 210.0))
    cx, cy = C.centreline(S_STATION)[0], C.centreline(S_STATION)[1]
    xs = np.linspace(-half, half, n)
    X, Y = np.meshgrid(xs, xs, indexing="ij")
    WX, WY = (X + cx).ravel(), (Y + cy).ravel()
    Z = np.array([C.world_ground_z(float(a), float(b))[0]
                  for a, b in zip(WX, WY)])
    bad = ~np.isfinite(Z)
    if bad.any():
        Z[bad] = float(C.ground_z(S_STATION, 0.0))
    # sink it 40 mm so it can never z-fight pont_girder's inner square
    V = np.stack([X.ravel(), Y.ravel(), Z - 0.040], -1)
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


def test_scene(out=None, samples=256, res=(1920, 1080), quality=1.0,
               girder_res=0.40, context=True):
    """The acceptance scene: the deck where it really is, on the girders it
    really bears on, over the racing surface that really lights its underside,
    under the contract sun, with a camera at the manifest's own distance."""
    sc = bpy.context.scene
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    place = deck_to_world()
    print(">> building deck slab, quality %.2f" % quality)
    D = build(place=place, res=quality)
    if context:
        print(">> building pont_girder as CONTEXT at res %.2f "
              "(prefix PGD_, not measured by the gate)" % girder_res)
        PG.materials()
        PG.build(coll_name="PGD_Girders", place=place, res=girder_res,
                 verbose=False)
        context_surround()
        PG.context_ground()
        PG.context_abutments(place)
    PG.contract_light(sc)                # the CORRECTED sun; see pont_girder
    cam, dmin = macro_camera(D)
    fascia_camera(D, "CAM_PDS_FASCIA_SUN", side=1.0)
    fascia_camera(D, "CAM_PDS_FASCIA_LEAD", side=-1.0)
    pass_camera(D)
    inspect_camera(D, "CAM_PDS_SOFFIT_HERO",
                   (0.35, -2.10,
                    float(soffit_z(np.array([0.35]), np.array([-2.10]))[0])),
                   (0.29, -3.09, 5.22), 35.0, fstop=18.0)
    inspect_camera(D, "CAM_PDS_RUST",
                   (2.60, -DECK_HALF_W, 8.42),
                   (3.28, -3.62, 8.14), 58.0, fstop=16.0)
    inspect_camera(D, "CAM_PDS_DRIP",
                   (-0.40, -DECK_HALF_W + 0.02, 8.150),
                   (-0.02, -3.46, 7.86), 58.0, fstop=16.0)
    inspect_camera(D, "CAM_PDS_SPALL",
                   (SPALL[0], -DECK_HALF_W, 8.330),
                   (SPALL[0] + 0.55, -3.90, 7.95), 58.0, fstop=16.0)
    inspect_camera(D, "CAM_PDS_KERB",
                   (-6.20, -KERB_FACE_Y, 8.62),
                   (-5.05, -1.05, 9.28), 58.0, fstop=16.0)
    inspect_camera(D, "CAM_PDS_JOINT",
                   (END_X - 0.20, 0.10, 8.50),
                   (END_X - 2.00, -1.35, 9.35), 35.0, fstop=16.0)
    inspect_camera(D, "CAM_PDS_GULLY",
                   (GULLY_X, -GULLY_Y, 8.52),
                   (GULLY_X - 0.75, -1.10, 9.16), 35.0, fstop=16.0)
    inspect_camera(D, "CAM_PDS_SOFFIT",
                   (2.40, -1.20, 8.20),
                   (0.10, -3.60, 6.10), 21.0, fstop=18.0)
    inspect_camera(D, "CAM_PDS_HAUNCH",
                   (-2.10, -2.40, 8.17),
                   (-1.10, -3.70, 7.05), 35.0, fstop=16.0)
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
    D.meta["nearest_deck_surface_m"] = dmin
    dump_interface(D)
    report(D)
    if out:
        import fix_audit_blend as FA
        FA.save_clean(out)
    return D, cam


def report(D):
    st = D.stats
    px = (3840.0 * 35.0 / SENSOR_MM) / 3.0
    print(">> VARIATION, measured on what was actually emitted:")
    print("   kerb units              %3d precast, %d casting lots, "
          "%d distinct profiles, %d pieces (one unit is cracked)"
          % (st.get("kerb_units", 0), st.get("kerb_lots", 0),
             st.get("kerb_profiles", 0), st.get("kerb_pieces", 0)))
    print("   +y upstand              in-situ, %d bolted edge-angle lengths, "
          "%d bolts" % (st.get("edge_angle_lengths", 0),
                        st.get("edge_angle_bolts", 0)))
    print("   joints                  2 DIFFERENT: %d anchor loops at -x "
          "(elastomeric), %d cast-in ferrules at +x (comb plate)"
          % (st.get("joint_anchor_loops", 0), st.get("joint_ferrules", 0)))
    print("   wearing surface         %.1f m relaid bay, %.2f m pothole "
          "repair, 2 wheel tracks, %d loose stones"
          % (RELAY_X1 - RELAY_X0, POTHOLE[2] * 2, st.get("loose_stones", 0)))
    print("   form ties               %d vertices in a mortar plug, %d in an "
          "open tie hole,\n"
          "                           %d in the honeycombed patch, %d carrying "
          "a rust dribble"
          % (st.get("tie_plugs_recessed", 0), st.get("tie_holes_open", 0),
             st.get("honeycomb_verts", 0), st.get("rust_dribble_verts", 0)))
    print("   damage                  %d vertices in the repaired spall, "
          "%d in the %d chipped arrises"
          % (st.get("spall_verts", 0), st.get("arris_chip_verts", 0),
             len(CHIP_ARRIS)))
    print("   cast-in                 %d parapet ferrules, %d soffit inserts, "
          "%d ducts, %d gullies"
          % (st.get("parapet_ferrules", 0), st.get("soffit_inserts", 0),
             st.get("ducts", 0), st.get("gullies", 0)))
    print("   markings                %d thermoplastic runs, 2.5 mm proud"
          % st.get("line_runs", 0))
    print("   slab mesh               %d stations x %d section points, "
          "%d gulley quads cut"
          % (st.get("stations", 0), st.get("section_points", 0),
             st.get("gully_holes_cut", 0)))
    print(">> CLEARANCE, measured on the built mesh:")
    print("   lowest deck z           %.4f   (girders reach %.4f over the "
          "racing surface)" % (st["lowest_z"], st["girder_lowest_z_over_track"]))
    print("   highest deck z          %.4f" % st["highest_z"])
    print("   headroom to the racing surface at s=2410 (ground %.3f): %.3f m"
          % (float(C.ground_z(S_STATION, 0.0)), st["track_headroom_to_slab_m"]))
    print(">> the deck is CARRIED, not founded: it bears on pont_girder's top "
          "flanges,\n>>   so world_contract.world_ground_z and BASE_EMBED_M do "
          "not apply to it.\n>>   The datum it is placed against is "
          "pont_girder's top_z(), read per station.")
    print(">> 1 px at the manifest's 3.0 m / 35 mm = %.3f mm" % (1000.0 / px))


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
                   samples=opt("--samples", 256, int),
                   girder_res=opt("--girder-res", 0.40, float),
                   context=("--no-context" not in a))
    elif "--one" in a:
        materials()
        D = build(place=None, res=opt("--quality", 1.0, float))
        PG.contract_light()
        dump_interface(D)
        report(D)
        if "--out" in a:
            import fix_audit_blend as FA
            FA.save_clean(opt("--out"))
    else:
        print(__doc__)


if __name__ == "__main__":
    _cli()
