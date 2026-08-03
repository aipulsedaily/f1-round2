"""spectator_crowd -- the grandstand, built out of `humankit`.

THIS IS NOT `spectator_seated.py`. That module is the wave-1 crowd and it is the
artefact the ten defects in `docs/HUMAN-FIGURE-BRIEF.md` were measured on: it
passes `item_gate` on 420 sources over 7,420 realised instances and it is the
one the user rejected as "the people in stands honeslty fucking shit". It is
left in place, untouched, because 8 items depend on it; swapping the two is the
next agent's call and section 00.7 of HUMAN-REFERENCE.md says what has to be
true first.

WHAT IS DIFFERENT HERE, and it is one idea. The wave-1 field instances its
library with a **random** index and a **random** yaw:

    FunctionNodeRandomValue(INT, 0..419)     -> Instance Index
    FunctionNodeRandomValue(VECTOR, +-7 deg) -> Rotation

so nothing about a figure can depend on WHERE IT IS SITTING. That single line of
node graph is why defects 7, 8, 9 and 10 cannot be fixed inside it: a random
index cannot know that this seat is in an aisle, that this row is turned round
talking to the row behind, or that the car is at world (x, y) this frame. This
module bakes **`hk_src` (INT) and `hk_rot` (FLOAT_VECTOR) as point attributes**
computed by `humankit.compose_stand`, and geometry nodes reads them. Everything
else follows from that:

  7  ROLES.  Six of them (`humankit.STAND_ROLES`), each with its own archetype
     table, and the library is built PER ROLE -- so a point whose role is
     "aisle" gets a source that is actually walking, not a seated figure rotated.
  8  CLUMPS. Points exist only at occupied seats, and occupancy is the group
     field `occupancy_clumpiness` measures against a Bernoulli control.
  9  ATTENTION. A seated spectator's BODY faces where the seat faces; the HEAD
     turns. A head turn cannot come from an instance rotation, so the library is
     indexed by (role, HEAD-YAW BIN) and the seat picks the bin its own bearing
     to the car needs. That is the whole reason the source set is structured
     rather than a bag of 420 figures -- and it is the variety rule working FOR
     the picture instead of against it.
  10 CONTACT. Every seated source is built with `build_figure(seat_z=0.0)`,
     which solves the ischial contact on the FINISHED mesh, and the point is the
     seat's pan top, so a figure cannot float or sink into the seat back.

    blender -b --factory-startup -P world/items/spectator_crowd.py -- --test-scene
    python3 world/items/spectator_crowd.py --selftest
"""

import argparse
import csv
import math
import os
import sys

import numpy as np

_ITEMS = os.path.dirname(os.path.abspath(__file__))
_WORLD = os.path.dirname(_ITEMS)
_ROOT = os.path.dirname(_WORLD)
for _p in (_WORLD, _ITEMS):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import itemkit as K                                            # noqa: E402
import humankit as HK                                          # noqa: E402

try:
    import bpy
    from mathutils import Matrix, Vector
except ImportError:                                            # pragma: no cover
    bpy = None

ITEM = "spectator_seated"          # the manifest record this serves
PFX = "SPECX_"
COLL = "ITEM_spectator_crowd"
LIB_COLL = COLL + "_Library"
SEED = 20260803
DECLARED = 7800

# manifest: nearest_camera_m 14.7 on a 28 mm lens -> 254 px for a 1.25 m
# seated figure. docs/screen_presence.json measures the peak SHARP presence at
# 199.1 px and frames_at_300px = 0, so nothing ever holds this crowd at L0.
FILMED_M, LENS_MM = 14.7, 28.0
TELEMETRY = os.path.join(_ROOT, "telemetry", "telemetry.csv")

# The head turn. A spectator's body faces the track and the head tracks the
# car; `sample_pose` clamps a neck+head yaw at +-95 deg, and past about 75 deg
# a real person turns their shoulders too -- which is what the `turned` role is
# for. Each ROLE has its own span and its own bin count (`ROLE_SPAN`,
# `ROLE_BINS`) because they need different ranges: a bolted seat needs the full
# +-72, a person walking up an aisle turns their body instead and only needs
# +-44. Worst-case quantisation is span / (bins - 1): 9 deg seated, 11 deg on
# their feet, on a head that is 47 px wide.

# Sources per (role, bin) cell. The gate needs >= 40 distinct sources AND >= 40
# distinct SHAPES with no source above 25 %; this comes to several hundred.
ROLE_BINS = {"sit": 9, "turned": 5, "stand": 9, "lean_rail": 5,
             "aisle": 5, "steps": 5}
# EACH ROLE'S HEAD-YAW BINS SPAN ITS OWN RANGE, and this is not cosmetic.
# The first version binned every role over the same +-72 deg and then remapped
# the 9-bin index onto a 3-bin one, so a `steps` figure whose head should turn
# 20 deg had it BAKED at 0 or at 72. Measured on TRIBUNE PRINCIPALE against the
# realised geometry (body yaw + the bin centre actually built, NOT the plan's
# intent, which is the number `crowd_watches_the_car` reads):
#
#     role        n     mean |error|   worst
#     sit       3225      5.0 deg       9.0
#     stand      304      4.2           8.9
#     turned     101     12.2          44.3
#     lean_rail   48     11.5          40.0
#     aisle       74     19.9          53.6
#     steps       51     26.5          53.9
#
# 173 people on their feet with a head aimed up to 54 deg away from what the
# plan says they are looking at. Worst-case error is span / (bins - 1): 9 deg
# for the seated tier, and now 11 deg rather than 72 for the rest.
ROLE_SPAN = {"sit": 72.0, "turned": 44.0, "stand": 72.0, "lean_rail": 44.0,
             "aisle": 44.0, "steps": 44.0}
# SIZED AGAINST THE REALISED PLAN, NOT AGAINST THE GATE. The gate's bar is 40
# distinct sources with none above 25 %, and the first sizing (26/8/12/4/4/4 =
# 402) cleared it by two orders of magnitude while the block it actually built
# put 46 copies of one seated figure and 34 of one walking one into a single
# grandstand. Two things drive that and neither is visible in the gate number:
#
#   * 85 % of a block is seated, so the seated roles' concentration is the only
#     one the global share can see and the on-their-feet roles -- the figures
#     that catch the eye, and the only ones with a full-length silhouette --
#     are buried in the denominator;
#   * the car is 665 m from TRIBUNE PRINCIPALE, so the bearing spread ACROSS
#     THE WHOLE BLOCK is 13.7 deg and two of the nine head-yaw bins carry 74 %
#     of the seated crowd. The axis the library is structured on has almost no
#     range in the shot it was structured for. That is worth knowing and it is
#     not fixable by binning differently -- it is fixed by making the cell
#     deep enough that the busy bins still hold hundreds of different people.
#
# Measured on TRIBUNE PRINCIPALE (3,803 people): worst copies of one source
# 63 -> 21, and the on-their-feet roles 4 sources -> 36-48.
ROLE_CELL = {"sit": 64, "turned": 10, "stand": 12, "lean_rail": 10,
             "aisle": 12, "steps": 10}


# --------------------------------------------------------------------------
# 1.  THE SEATS, out of the module that casts them
# --------------------------------------------------------------------------

def seat_array(blocks=None):
    """(row, col, x, y, z_pan) for every seat, plus the per-seat facing.

    Read out of `grandstand_riser_unit.seat_grid()` -- 18,408 anchors, each
    carrying the tread point `p`, the tilted tread normal `up` and a `facing`
    toward the track. The pan top is `p + up * PAN_ABOVE_TREAD`; that constant
    is `build_architecture._seat`'s own, not a guess.
    """
    import grandstand_riser_unit as GRU
    PAN = 0.445
    out, face = [], []
    for s in GRU.seat_grid():
        if blocks and s["block"] not in blocks:
            continue
        p = np.asarray(s["p"], float) + np.asarray(s["up"], float) * PAN
        out.append((s["row"], s["col"], p[0], p[1], p[2]))
        face.append(math.degrees(math.atan2(s["facing"][1], s["facing"][0])))
    return np.asarray(out, float), np.asarray(face, float)


def car_at(frame):
    """The car's world position at `frame`. `telemetry/telemetry.csv` is owned
    by another agent; this only ever reads it."""
    with open(TELEMETRY) as fh:
        rows = list(csv.DictReader(fh))
    r = rows[max(0, min(len(rows) - 1, int(frame)))]
    return (float(r["x"]), float(r["y"]), float(r["z"]) + 0.55)


# --------------------------------------------------------------------------
# 2.  THE PLAN: who, doing what, looking where
# --------------------------------------------------------------------------

def plan_block(seed, seats, facings, focus, n_want=None,
               legacy_gaze=False, **kw):
    """`compose_stand` on a real seat array, plus the two numbers each point
    needs to pick its source: the head-turn bin and the body yaw.

    THE SPLIT IS THE POINT. `compose_stand` returns the bearing the person is
    ATTENDING TO; a seated person does not swivel their chair to it. So the
    BODY takes the seat's own facing (jittered) and the HEAD takes the
    remainder, binned -- and the bin is what indexes the library.

    `legacy_gaze=True` reproduces the SUPERSEDED ordering -- body solved
    against the continuous head, head quantised afterwards -- so the comb it
    puts through the realised gaze field can be measured rather than argued
    about. It is a control and nothing builds with it.
    """
    plan = HK.compose_stand(seed, seats, focus=focus, **kw)
    key = {(int(s[0]), int(s[1])): i for i, s in enumerate(seats)}
    # The mean bearing a seat looks along, so a person with no seat of their
    # own (aisle, steps) still has the block's geometry to stand in rather than
    # a guessed north.
    blk_face = float(np.degrees(np.arctan2(
        np.sin(np.radians(facings)).mean(),
        np.cos(np.radians(facings)).mean()))) if len(facings) else 90.0
    for r in plan:
        i = key.get((r["row"], r["col"]))
        seat_face = float(facings[i]) if i is not None else blk_face
        # HOW MUCH OF THE TURN THE BODY TAKES. A seated person's chair is
        # bolted down and only the neck moves; a person on their feet in a row
        # can pivot most of the way but is still planted facing the track; a
        # person walking is going SOMEWHERE and the head does the rest.
        #
        # The first version of this gave every on-their-feet role
        # `body = yaw_deg, head = 0`, and both halves of that were wrong:
        #   * an aisle walker in `walk_stride` was rotated bodily at the car,
        #     i.e. striding sideways across the terracing into the seats;
        #   * `gaze_bin` was therefore ALWAYS 4 for those roles, so
        #     `library_index` could only ever reach ONE of each role's bins.
        #     216 of the 402 sources were built and never instanced, and the
        #     477 people on their feet -- the most conspicuous figures in the
        #     block -- shared 24 meshes: 34 copies of one walking man.
        #     Both numbers are counted on a real block, not assumed.
        if r["role"] in ("aisle", "steps"):
            side = float(r.get("aisle_side", 1.0))
            stance, share, cap = (seat_face + (0.0 if side > 0 else 180.0),
                                  0.62, 180.0)
        elif r["role"] in ("stand", "lean_rail"):
            stance, share, cap = seat_face, 0.45, 180.0
        else:
            # A BOLTED SEAT. The body may lean and twist within the chair but
            # it cannot turn round -- past this the person IS the `turned`
            # role, which is a different pose and a different library cell.
            stance, share, cap = seat_face, 0.65, 45.0
        d = ((float(r["yaw_deg"]) - stance + 180.0) % 360.0) - 180.0
        head = float(np.clip(share * d, -ROLE_SPAN[r["role"]],
                             ROLE_SPAN[r["role"]]))
        # THE BODY MAKES UP WHATEVER THE NECK CANNOT, up to its own limit. The
        # superseded form gave the body a fixed FRACTION of the turn and let
        # the neck absorb the rest, so a large required turn produced a head
        # clipped at the span and a person facing 50 deg away from what they
        # were supposed to be looking at, with nothing recording that they were
        # not in fact looking at it.
        body = stance + float(np.clip(d - head, -cap, cap))
        head = ((float(r["yaw_deg"]) - body + 180.0) % 360.0) - 180.0
        head = float(np.clip(head, -ROLE_SPAN[r["role"]], ROLE_SPAN[r["role"]]))
        rbin = role_bin(r["role"], head)
        baked = _bin_deg(r["role"], rbin)
        # ---------------------------------------------------------------
        # THE BODY ABSORBS THE QUANTISATION RESIDUAL, and this is not a
        # refinement -- the version without it put a COMB through the crowd.
        #
        # The head turn is continuous but only ROLE_BINS of it can be BUILT,
        # so what a viewer sees is `body + baked`, not `body + head`. Solving
        # the body first and quantising the head second makes the realised
        # bearing `stance + (1 - share) d + quantise(share d)`: inside one bin
        # it sweeps (1 - share) x bin_width = 9.7 deg, and at the bin edge it
        # JUMPS by bin_width - 9.7 = 8.3 deg. Measured on TRIBUNE PRINCIPALE
        # before the fix, realised head bearing in 5 deg bins relative to the
        # block mean:
        #
        #     -15..-10   368        +5..+10      1     <- one person
        #     -10.. -5  1089       +10..+15    900
        #      -5.. +0    91       +15..+20    285
        #      +0.. +5    13       +20..+25     31
        #
        # 3,803 people occupying 10 deg out of every 18, with a hole through
        # the middle of the watching population that no crowd has and no
        # statistic in this repository could see: `crowd_watches_the_car`
        # counts everyone within 20 deg and scores 73 % either way.
        #
        # Re-solving the body AFTER the bin is known -- body = yaw - baked,
        # clamped -- makes `body + baked` equal the attend bearing exactly
        # wherever the neck and the seat can reach it. The comb goes, and the
        # per-figure attention error drops from "up to half a bin" to "only
        # what the anatomy refuses".
        # ---------------------------------------------------------------
        if not legacy_gaze:
            body = stance + float(np.clip(
                ((float(r["yaw_deg"]) - baked - stance + 180.0) % 360.0)
                - 180.0, -cap, cap))
        r["body_yaw_deg"] = body
        # the CONTINUOUS neck angle the composer wants, given the final body.
        # `head_yaw_deg` is what gets BUILT, i.e. the bin; the two differ by
        # the quantisation and that difference is what
        # `what_is_baked_is_what_was_planned` measures.
        r["head_yaw_solved_deg"] = float(np.clip(
            ((float(r["yaw_deg"]) - body + 180.0) % 360.0) - 180.0,
            -ROLE_SPAN[r["role"]], ROLE_SPAN[r["role"]]))
        r["head_yaw_deg"] = float(head) if legacy_gaze else baked
        r["gaze_bin"] = rbin
        r["gaze_baked_deg"] = baked
        # WHICH of the cell's figures, decided by the SEAT so a rebuild of the
        # same plan puts the same person back in the same chair
        k = int(HK.hash01(int(seed), r["row"] * 977 + max(r["col"], 0) * 13
                          + (1 if r["col"] < 0 else 0)) * 1e6)
        r["src"] = library_index(r["role"], r["head_yaw_deg"], k)
    if n_want is not None and len(plan) > n_want:
        # thin by GROUP, never by seat: dropping every third person out of a
        # clumped field puts the speckle straight back in.
        rr = HK.rng_for(seed, 909)
        gs = sorted({p["group"] for p in plan})
        keep, tot = set(), 0
        for g in sorted(gs, key=lambda g: rr.u()):
            n = sum(1 for p in plan if p["group"] == g)
            if tot + n > n_want:
                continue
            keep.add(g)
            tot += n
        plan = [p for p in plan if p["group"] in keep]
    return plan


# --------------------------------------------------------------------------
# 3.  THE SOURCE LIBRARY -- structured, not a bag
# --------------------------------------------------------------------------

def _role_base(role):
    base = 0
    for r in HK.STAND_ROLES:
        if r == role:
            return base
        base += ROLE_BINS[r] * ROLE_CELL[r]
    raise KeyError(role)


def role_bin(role, head_deg):
    """The role's OWN head-yaw bin for a head turn in degrees.

    THERE IS ONE INDEX NOW, AND IT IS THIS ONE. The superseded version binned
    every role over a global +-72 deg `GAZE_BINS` and then remapped that index
    onto the role's coarser bins -- two index spaces, and the first version of
    it conflated them: `library_index` remapped its argument while the library
    builder passed an already-remapped one, so two cells of `sit` landed on the
    same slot and 40 of 402 sources were never built. That is exactly the class
    of bug `library_index_is_a_bijection` exists to catch, and the way to stop
    catching it is to have one index rather than two.
    """
    nb = ROLE_BINS[role]
    if nb <= 1:
        return 0
    sp = ROLE_SPAN[role]
    t = (float(np.clip(head_deg, -sp, sp)) + sp) / (2.0 * sp)
    return int(min(nb - 1, max(0, int(round(t * (nb - 1))))))


def library_index(role, head_deg, k):
    """Flat source index for (role, head yaw in DEGREES, k). Deterministic, so
    a plan built in one process indexes a library built in another."""
    return (_role_base(role) + role_bin(role, head_deg) * ROLE_CELL[role]
            + (int(k) % ROLE_CELL[role]))


def _slot_index(role, rbin, k):
    """Flat index from the role's OWN bin -- the library builder's view."""
    return _role_base(role) + int(rbin) * ROLE_CELL[role] + int(k)


def library_size():
    return sum(ROLE_BINS[r] * ROLE_CELL[r] for r in HK.STAND_ROLES)


def _bin_deg(role, b):
    """The head yaw BAKED into cell `b` of `role`. `role_bin(role, _bin_deg(
    role, b)) == b` for every b, which is what makes the round trip lossless
    to within half a bin."""
    if ROLE_BINS[role] <= 1:
        return 0.0
    sp = ROLE_SPAN[role]
    return float(-sp + 2.0 * sp * b / (ROLE_BINS[role] - 1))


def build_library(seed=SEED, lod=None, coll=None, mats=None, limit=None,
                  yard=None, pitch=1.30, per_row=24, hands_l0=True):
    """One unique person per source slot, laid out on a CONTACT SHEET.

    NOT `hide_render`. That was the first thing this module did and it is what
    made `item_gate` report ITEM_REJECTED with `witness_frame_valid` FAIL and
    **"only 0 subject pixels"**: the gate picks the median-triangle object in
    the collection, which is necessarily one of these sources, deletes
    everything else, stages its own scene around it -- and never clears
    `hide_render`, so the frame it measured was empty sky. Three checks came
    back NOT MEASURED off one boolean.

    `hide_render` was only ever there to stop 402 people rendering ON TOP OF
    EACH OTHER at the origin, because `emit_mesh` recentres. Putting them on a
    grid well clear of the block solves that properly and gives the one picture
    that answers the variety question directly: every source the library holds,
    side by side, at one scale.
    """
    # ONE LOD FOR A CROWD IS THE WRONG ANSWER, AND IT WAS WRONG IN THE
    # EXPENSIVE DIRECTION. `LOD.for_px` takes the figure's projected HEIGHT:
    # at the manifest's 14.7 m on a 28 mm lens the scale is 203 px/m, so a
    # 1.25 m SEATED figure reads 254 px -> L1, and a 1.75 m figure ON ITS FEET
    # reads 356 px -> L0. The whole library was built at L1, so the ~15 % of
    # the block that is standing, walking, on the steps or leaning on the rail
    # -- the only figures with a full-length silhouette, the ones nearest the
    # front of a stand, and the ones the eye goes to -- were a tier short:
    # 3 grouped digits instead of 5 separate ones, 1 ear instead of 2, no
    # nails, 190 hair strands instead of 620.
    #
    # This costs nothing at render time. The library is INSTANCED, so its size
    # is a memory figure and not a per-instance one: 228 standing sources at
    # L0 plus 612 seated at L1 is ~33 M triangles against ~24 M, on a card
    # with 32 GB.
    #
    # DEFECT 6 -- "THE HANDS ARE MITTENS" -- IS FIXED HERE, AND NOT BY L0.
    # `render/items/spectator_crowd/crops/feet_c.png` shows six `sit_cheer`
    # figures with both arms raised and every raised hand a FLAT PADDLE WITH A
    # THUMB. Cause, measured on the mesh rather than inferred from the call:
    # `LOD_L1.fingers = 3` makes `_finger_groups` return two FUSED PAIRS at
    # 1.9x radius, and `humankit.hand_finger_separation` counts what that
    # actually emits --
    #
    #     tier            digit-length shells      closest two tips
    #     L2                       2                    84 mm
    #     L1  (as shipped)         3                    51 mm   <- the mitten
    #     L1 + fingers=5           5                    23 mm
    #     L0                       9 (5 + nails)        11 mm
    #
    # -- so L1 as shipped is a hand with THREE digits on it and the picture is
    # telling the truth.
    #
    # HUMAN-REFERENCE sec 0000.5 prescribes "build the seated library at L0",
    # which fixes it and costs 79,088 tris a figure against 29,755: +166 %,
    # ~62 M library triangles, and 0.92 s a figure against 0.32 s. The hand is
    # ONE BODY PART. `LOD.for_px` is right about the figure and wrong about the
    # hand: a 1.25 m seated body projects 254 px at the manifest framing, but a
    # hand raised above that body's head is nearer, unoccluded, and 90-120 px
    # across in the very crop the defect was found in.
    #
    # So the seated tier is built at L1 WITH L0 HANDS. Measured on six figures:
    # **30,675 tris against 29,755 -- 920 more, +3.1 %** -- and 0.34 s against
    # 0.32 s. Same five fingers, 3.1 % instead of 166 %.
    # `--lod L0` still does the whole-tier bump if the evidence ever demands it.
    lod = lod or HK.LOD_L1
    # the on-their-feet tier goes up a whole step -- that is decided on the
    # BASE tier, before the hand override, or `lod_up` misses the dict lookup
    # and silently leaves the standing figures a tier short again.
    lod_up = {HK.LOD_L1: HK.LOD_L0, HK.LOD_L2: HK.LOD_L1,
              HK.LOD_L3: HK.LOD_L2}.get(lod, lod)
    if hands_l0 and lod.fingers < 5:
        lod = lod.derive(name=lod.name + "h", fingers=5)
    if hands_l0 and lod_up.fingers < 5:
        lod_up = lod_up.derive(name=lod_up.name + "h", fingers=5)
    objs = []
    n = 0
    for role in HK.STAND_ROLES:
        for b in range(ROLE_BINS[role]):
            for k in range(ROLE_CELL[role]):
                idx = _slot_index(role, b, k)
                if limit is not None and n >= limit:
                    # UNPACK, like the normal exit does. `objs` holds
                    # (idx, ob) pairs; returning it raw handed the caller
                    # tuples and `--lib-limit` -- the one flag whose whole job
                    # is a fast smoke test -- died on `o.data.polygons`.
                    objs.sort(key=lambda t: t[0])
                    return [o for _i, o in objs]
                fseed = seed * 1000003 + idx * 7919 + 13
                arche = HK._pick_weighted(HK.rng_for(fseed, 77).u(),
                                          HK.STAND_POSES[role])
                seated = role in ("sit", "turned")
                # THE HEAD TURN IS BAKED IN, and it is what the bin means.
                gz = (_bin_deg(role, b), -3.0 - 6.0 * abs(_bin_deg(role, b))
                      / 72.0)
                tier = lod if seated else lod_up
                fig = HK.build_figure(seed=fseed, lod=tier, role="spectator",
                                      archetype=arche, gaze=gz,
                                      kind="sit" if seated else "stand",
                                      seat_z=0.0 if seated else None)
                nm = "%sLib%04d_%s_b%d" % (PFX, idx, role, b)
                ob = HK.emit_mesh(nm, fig["mesh"], coll, mats)
                if yard is not None:
                    # A CONTACT SHEET, ordered by (role, bin, k) so a repeat is
                    # visible as a repeat rather than hidden in a shuffle.
                    # `emit_mesh` returns the object already carrying its own
                    # recentring offset (itemkit Law 6) -- ADD to it, never
                    # replace it, or every figure sinks by half its own height.
                    off = tuple(ob.location)
                    ob.location = (off[0] + yard[0] + (n % per_row) * pitch,
                                   off[1] + yard[1] - (n // per_row) * pitch,
                                   off[2] + yard[2]
                                   + (0.445 if seated else 0.0))
                else:
                    ob.hide_render = True
                ob["hk_role"] = role
                ob["hk_gaze_bin"] = b
                ob["hk_src"] = idx
                ob["hk_arche"] = arche
                ob["hk_lod"] = tier.name
                objs.append((idx, ob))
                n += 1
    objs.sort(key=lambda t: t[0])
    return [o for _i, o in objs]


# --------------------------------------------------------------------------
# 4.  THE FIELD -- attributes, not random values
# --------------------------------------------------------------------------

def _crowd_group(name, library, n_sources):
    ng = bpy.data.node_groups.new(name, "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT",
                            socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT",
                            socket_type="NodeSocketGeometry")
    gi = ng.nodes.new("NodeGroupInput")
    go = ng.nodes.new("NodeGroupOutput")
    ci = ng.nodes.new("GeometryNodeCollectionInfo")
    ci.inputs["Collection"].default_value = library
    ci.inputs["Separate Children"].default_value = True
    ci.inputs["Reset Children"].default_value = True
    iop = ng.nodes.new("GeometryNodeInstanceOnPoints")
    iop.inputs["Pick Instance"].default_value = True
    # THE TWO ATTRIBUTES THAT MAKE THIS A CROWD AND NOT A SPECKLE.
    asrc = ng.nodes.new("GeometryNodeInputNamedAttribute")
    asrc.data_type = "INT"
    asrc.inputs["Name"].default_value = "hk_src"
    arot = ng.nodes.new("GeometryNodeInputNamedAttribute")
    arot.data_type = "FLOAT_VECTOR"
    arot.inputs["Name"].default_value = "hk_rot"
    asc = ng.nodes.new("GeometryNodeInputNamedAttribute")
    asc.data_type = "FLOAT"
    asc.inputs["Name"].default_value = "hk_scale"
    ng.links.new(gi.outputs[0], iop.inputs["Points"])
    ng.links.new(ci.outputs["Instances"], iop.inputs["Instance"])
    ng.links.new(asrc.outputs["Attribute"], iop.inputs["Instance Index"])
    ng.links.new(arot.outputs["Attribute"], iop.inputs["Rotation"])
    ng.links.new(asc.outputs["Attribute"], iop.inputs["Scale"])
    ng.links.new(iop.outputs["Instances"], go.inputs[0])
    for i, nd in enumerate((gi, ci, asrc, arot, asc, iop, go)):
        nd.location = (-700 + 220 * min(i, 5), -260 * (i % 4))
    return ng


def build_field(name, plan, library, coll, seed=SEED, n_src=None):
    """Instance the library on the plan. One point per person."""
    rr = HK.rng_for(seed, 313)
    pts, src, rot, scl = [], [], [], []
    for r in plan:
        x, y = r["pos"]
        z = r["z"]
        if r["role"] in ("aisle", "steps"):
            # step out of the row into the aisle, and stand on the tread
            x += 0.62 * r.get("aisle_side", 1.0)
            z -= 0.445
        pts.append((x, y, z))
        src.append(int(r["src"]))
        rot.append((0.0, 0.0, math.radians(r["body_yaw_deg"] - 90.0)))
        # stature is in the SOURCE, not in the scale; this is the 1-2 % a
        # shared source needs so twenty copies of it are not congruent.
        scl.append(1.0 + rr.n(0.0, 0.015))
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(p) for p in pts], [], [])
    me.update()
    a = me.attributes.new("hk_src", "INT", "POINT")
    a.data.foreach_set("value", src)
    a = me.attributes.new("hk_rot", "FLOAT_VECTOR", "POINT")
    a.data.foreach_set("vector", [c for v in rot for c in v])
    a = me.attributes.new("hk_scale", "FLOAT", "POINT")
    a.data.foreach_set("value", scl)
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    md = ob.modifiers.new("crowd", "NODES")
    md.node_group = _crowd_group(name + "_GN", library, n_src)
    ob["instances"] = len(pts)
    ob["library_sources"] = int(n_src)
    return ob


# --------------------------------------------------------------------------
# 5.  THE TEST SCENE
# --------------------------------------------------------------------------

def build_scene(seed=SEED, blocks=("TRIBUNE PRINCIPALE",), frame=1009,
                n_want=None, lod=None, lib_limit=None):
    if bpy is None:
        raise RuntimeError("needs Blender")
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    root = K.coll(COLL)
    K.purge(PFX, COLL)
    root = K.coll(COLL)
    lib = K.coll(LIB_COLL, root)
    mats = HK.figure_materials(PFX)
    focus = car_at(frame)
    seats, face = seat_array(blocks)
    HK.log("seats %d in %s; car at %.1f, %.1f, %.2f (frame %d)"
           % (len(seats), "+".join(blocks), focus[0], focus[1], focus[2],
              frame))
    plan = plan_block(seed, seats, face, focus, n_want=n_want)
    HK.log("plan: %d people, roles %s"
           % (len(plan), {k: round(v, 4)
                          for k, v in HK.role_mix(plan).items()}))
    # The contact-sheet yard, derived from the block's own bounds so it is
    # always clear of it whatever block was asked for.
    yard = (float(seats[:, 2].min()) - 46.0, float(seats[:, 3].min()) - 8.0,
            float(seats[:, 4].min()) - 2.6)
    objs = build_library(seed, lod=lod, coll=lib, mats=mats, limit=lib_limit,
                         yard=yard)
    HK.log("library: %d sources, %d tris"
           % (len(objs), sum(len(o.data.polygons) for o in objs)))
    if lib_limit is not None:
        for r in plan:
            r["gaze_bin"] = 0
            r["role"] = "sit"
    fld = build_field(PFX + "Crowd", plan, lib, root, seed,
                      n_src=len(objs))
    K.assert_no_external_assets()
    return {"plan": plan, "library": objs, "field": fld, "focus": focus,
            "seats": seats, "facings": face}


# --------------------------------------------------------------------------
# 5a.  A SEAT TO SIT ON -- context, and it is labelled as context
# --------------------------------------------------------------------------

def build_seat_standins(seats, facings, coll, mat, kind=0, every=1):
    """`CTX_` bucket seats at the real anchors, so contact can be SEEN.

    NOT the item. `grandstand_riser_unit` casts the terracing and
    `build_architecture._seat` casts the chairs; building 1,056 real castings
    for a look-test would take longer than the crowd does and that module is
    being edited by another agent as I write this, so what I would render is a
    version that no longer exists.

    WHAT THIS DOES AND DOES NOT PROVE. The pan top is `tread + 0.445`, and
    0.445 is `build_architecture._seat`'s own number for seat kind 0 -- the pan
    is `xbox(T(0, 0, 0.42), (0.44, 0.44, 0.05))`, i.e. centred 0.420 above the
    tread and 0.050 thick, so its top face is at 0.445 exactly. The standin
    therefore CANNOT be used to check that 0.445 is right: it shares the
    constant with the placement, and a check whose control shares a term with
    its subject measures nothing (this file, section 000.4). What it CAN show,
    and what no number shows, is the BACK and the WINGS -- `T(0, 0.22, 0.62)
    @ Rx(-9)` x (0.44, 0.045, 0.40) and the two 0.04 x 0.30 x 0.16 side wings --
    against a real body, i.e. whether a spectator's shoulders are inside the
    seat back and whether a wide figure's hips are inside the wings. Those are
    read off the chair's own dimensions and the figure's own mesh, which share
    nothing.
    """
    from mathutils import Matrix, Vector
    V, Q = [], []

    def box(o, ex, ey, ez, hx, hy, hz):
        b = len(V)
        for sx in (-1, 1):
            for sy in (-1, 1):
                for sz in (-1, 1):
                    V.append(tuple(o + ex * (sx * hx) + ey * (sy * hy)
                                   + ez * (sz * hz)))
        for f in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6),
                  (0, 2, 6, 4), (1, 5, 7, 3)):
            Q.append(tuple(b + i for i in f))

    for n, (s, fdeg) in enumerate(zip(seats, facings)):
        if n % every:
            continue
        up = np.array([0.0, 0.0, 1.0])
        fw = np.array([math.cos(math.radians(fdeg)),
                       math.sin(math.radians(fdeg)), 0.0])
        ex = np.cross(fw, up)
        ey = -fw                      # seat local +y is AWAY from the track
        tread = np.array([s[2], s[3], s[4]]) - up * 0.445
        # pan, nose lip, back panel, two wings -- `_seat`'s kind-0 vocabulary
        box(tread + up * 0.420, ex, ey, up, 0.22, 0.22, 0.025)
        box(tread + up * 0.450 - ey * 0.21, ex, ey, up, 0.22, 0.03, 0.045)
        c, sn = math.cos(math.radians(9.0)), math.sin(math.radians(9.0))
        by, bz = ey * c + up * sn, -ey * sn + up * c
        box(tread + up * 0.620 + ey * 0.22, ex, by, bz, 0.22, 0.0225, 0.20)
        for sx in (-0.215, 0.215):
            box(tread + up * 0.500 + ey * 0.10 + ex * sx, ex, ey, up,
                0.02, 0.15, 0.08)
    me = bpy.data.meshes.new("CTX_SeatStandin")
    me.from_pydata([tuple(map(float, v)) for v in V], [], Q)
    me.update()
    me.materials.append(mat)
    ob = bpy.data.objects.new("CTX_SeatStandin", me)
    coll.objects.link(ob)
    ob["standin"] = True
    return ob


# --------------------------------------------------------------------------
# 5a.  CAMERA PRE-FLIGHT -- arithmetic, before a single triangle is built
# --------------------------------------------------------------------------
#
# TWICE ON THIS PROJECT A FRAME WAS COMMISSIONED THAT COULD NOT SHOW WHAT IT
# WAS FOR. Beat 1's camera was aimed 48.885 deg off its own subject with zero
# parts in view; `CAM_SPECSEAT_MACRO`'s 767 px render is the artefact the whole
# human brief was written from. This module then added a third and a fourth:
# `CAM_BLOCK_ONAXIS` and `CAM_BLOCK_CROSS` were built to answer "does attention
# read" and "is a neighbour visibly the same person", rendered at 4K, and
# **cannot answer either**. Everything below exists so that the next one raises
# instead of rendering.
#
# WHY THOSE TWO FAILED, MEASURED RATHER THAN GUESSED. HUMAN-REFERENCE sec
# 0000.5 records the cause as "`macro_rig`'s depth of field turns every figure
# into a blur". **That is wrong and it is worth being exact about, because a
# wrong cause produces a wrong fix.** `itemkit.add_camera` only touches
# `cam.data.dof` when it is passed an `fstop`, `_cam` never passed one, and the
# delivered blend read back through `bpy.data.libraries.load` says
# `use_dof = False` on all six cameras. Two independent readings agree:
#
#   * the datablock: every camera in `spectator_crowd_test.blend` has
#     `use_dof False`, `focus_distance 10.0` (the Blender default, untouched);
#   * the frame: local gradient energy in `BLOCK_CROSS.png` rises MONOTONICALLY
#     from the far top of the block (0.138) to the near bottom (0.161). A
#     defocus focused at the aim point peaks in the middle and falls off both
#     ways. A scale effect does exactly what is measured.
#
# The softness is 34 M triangles of sub-pixel crowd at 192 samples going
# through the denoiser. The REAL fault is plain arithmetic and needs no render
# at all -- `camera_preflight` projects the plan and reports:
#
#     BLOCK_ONAXIS  200 m / 50 mm  ->  median head  8.0 px, 0 faces >= 40 px
#     BLOCK_CROSS   148 m / 50 mm  ->  median head 10.1 px, 0 faces >= 40 px
#
# and both look DOWN at 9-11 deg, so what they show is the tops of hats. You
# cannot judge whether two neighbours are the same person at 8 px of head, and
# no aperture setting was ever going to change that.
#
# WHAT THE REPLACEMENTS DO. A 0.23 m head at 40 px needs 174 px/m, i.e.
# `dist = 3840 * lens / (36 * 174)` -- a 300 mm lens reaches it at 184 m. So a
# LONG LENS FROM TRACK LEVEL, aimed ALONG the bank, gets a whole block AND
# resolvable faces in the same frame, which is exactly the shot broadcast uses
# and exactly what a 50 mm from 200 m cannot do.

_HEAD_H_M = 0.23              # a head's projected height, brow to chin-ish
_HEAD_DZ_SEATED = 0.72        # head centre above the seat pan
_HEAD_DZ_ONFOOT = 1.58        # ... above the tread, for a figure on its feet
_ON_FOOT = ("stand", "aisle", "steps", "lean_rail")

# The bar. 40 px of head is about where an eye socket and a nose stop being a
# smudge and two neighbouring faces become comparable; it is also the width at
# which `crops/feet_c.png` made the mitten hands unmistakable. `MIN_FACES` is
# how many figures must clear it, unoccluded, WITH THEIR FACE TOWARD THE LENS
# -- a frame with three good faces cannot answer a question about 3,803 people.
PREFLIGHT_HEAD_PX = 40.0
PREFLIGHT_MIN_FACES = 120
PREFLIGHT_MAX_ELEV = 6.0      # deg. Past this you are looking at hats.


def head_points(plan):
    """(N,3) head centres, (N,) REALISED head bearing in degrees, (N,) on-foot.

    The bearing is `body_yaw_deg + gaze_baked_deg` -- the instance rotation
    plus the head turn actually baked into the library cell the seat picked.
    NOT `yaw_deg`, which is the plan's INTENT and is what `attention_spread`
    was reading when it measured a yaw it had invented itself.
    """
    H = np.empty((len(plan), 3))
    B = np.empty(len(plan))
    F = np.zeros(len(plan), bool)
    for i, p in enumerate(plan):
        onf = p["role"] in _ON_FOOT
        F[i] = onf
        H[i] = (p["pos"][0], p["pos"][1],
                p["z"] + (_HEAD_DZ_ONFOOT if onf else _HEAD_DZ_SEATED))
        B[i] = float(p["body_yaw_deg"]) + float(p["gaze_baked_deg"])
    return H, B, F


def _basis(loc, aim):
    """Blender's own `to_track_quat('-Z','Y')` frame: forward, right, up."""
    d = np.asarray(aim, float) - np.asarray(loc, float)
    n = np.linalg.norm(d)
    if n < 1e-9:
        raise ValueError("camera and aim point coincide")
    f = d / n
    r = np.cross(f, (0.0, 0.0, 1.0))
    if np.linalg.norm(r) < 1e-9:                      # straight up or down
        r = np.array([1.0, 0.0, 0.0])
    r /= np.linalg.norm(r)
    return f, r, np.cross(r, f)


def _unoccluded(px, py, hp, z, inframe):
    """Head centres with no NEARER head centre inside their own disc.

    Deliberately crude and deliberately conservative: it counts a head as
    hidden as soon as a nearer head's centre lands within max(r_near, r_this)
    of it, which over-counts occlusion for a head peeking over a shoulder. It
    is a LOWER bound on how many faces a frame shows, and a lower bound is the
    only direction that is safe for a check that decides whether to spend a
    render.
    """
    idx = np.where(inframe)[0]
    idx = idx[np.argsort(z[idx])]
    out = np.zeros(len(z), bool)
    X, Y, R = px[idx], py[idx], hp[idx] * 0.55
    for i in range(len(idx)):
        if i == 0:
            out[idx[i]] = True
            continue
        d = np.hypot(X[:i] - X[i], Y[:i] - Y[i])
        out[idx[i]] = not np.any(d < np.maximum(R[:i], R[i]))
    return out


def preflight(name, loc, aim, lens, plan, res=None, head_px=None,
              min_faces=None, max_elev=None, min_heads=0, what=""):
    """Everything a crowd camera has to be true BEFORE it is worth rendering.

    Pure numpy. No bpy, no scene, no triangles: it takes the plan -- which is
    the same object `build_field` bakes into point attributes -- projects every
    head through the camera the arithmetic says will exist, and reports what
    the frame can physically contain. Returns a dict; `verdict` is "" on pass
    and the reason on failure.
    """
    res = res or (K.RES_X_4K, K.RES_Y_4K)
    head_px = PREFLIGHT_HEAD_PX if head_px is None else float(head_px)
    min_faces = PREFLIGHT_MIN_FACES if min_faces is None else int(min_faces)
    max_elev = PREFLIGHT_MAX_ELEV if max_elev is None else float(max_elev)
    rx, ry = int(res[0]), int(res[1])
    H, B, onf = head_points(plan)
    f, r, u = _basis(loc, aim)
    V = H - np.asarray(loc, float)
    z = V @ f
    ahead = z > 0.05
    zs = np.where(ahead, z, 1.0)
    k = float(lens) / K.SENSOR_MM * rx
    px = rx * 0.5 + k * (V @ r) / zs
    py = ry * 0.5 - k * (V @ u) / zs
    hp = k * _HEAD_H_M / zs
    inframe = ahead & (px > 0) & (px < rx) & (py > 0) & (py < ry)
    # face toward the lens: the head's own bearing against the head->camera
    # direction. 0.10 is ~84 deg, i.e. anything but a clean back-of-head.
    tc = np.asarray(loc, float) - H
    tc /= np.linalg.norm(tc, axis=1)[:, None]
    fb = np.radians(B)
    facing = (np.cos(fb) * tc[:, 0] + np.sin(fb) * tc[:, 1])
    vis = _unoccluded(px, py, hp, z, inframe) if inframe.any() else inframe
    heads = inframe & vis & (hp >= head_px)
    good = heads & (facing > 0.10)
    elev = math.degrees(math.asin(float(f[2])))
    # how much of the frame the subject actually occupies, on a 24 x 14 grid
    if inframe.any():
        gx = np.clip((px[inframe] / rx * 24).astype(int), 0, 23)
        gy = np.clip((py[inframe] / ry * 14).astype(int), 0, 13)
        fill = len(set(zip(gx.tolist(), gy.tolist()))) / (24.0 * 14.0)
    else:
        fill = 0.0
    d = np.linalg.norm(H - np.asarray(loc, float), axis=1)
    m = dict(name=name, lens=float(lens), res=(rx, ry),
             loc=tuple(float(v) for v in loc), aim=tuple(float(v) for v in aim),
             aim_dist_m=float(np.linalg.norm(np.asarray(aim, float)
                                             - np.asarray(loc, float))),
             elev_deg=elev,
             bearing_deg=math.degrees(math.atan2(float(f[1]), float(f[0]))),
             n_planned=len(plan), n_in_frame=int(inframe.sum()),
             n_unoccluded=int((inframe & vis).sum()),
             # UNOCCLUDED HEADS AT >= head_px, WHICHEVER WAY THEY POINT.
             # `n_faces_resolved` adds `facing > 0.10` -- about 84 deg -- and
             # that is the RIGHT bar for a frontal camera and the WRONG one for
             # a profile camera, where by construction the subject's face is at
             # ~90 deg to the lens and the dot product is near zero. Reporting
             # only `n_faces_resolved` made `CAM_ATTN_PROFILE` look like it saw
             # 175 people when it sees 621; the 175 are the ones whose HEADS
             # are turned out of an edge-on shoulder line toward the lens,
             # which is the attention signal itself and not a shortfall.
             n_heads_resolved=int(heads.sum()),
             n_faces_resolved=int(good.sum()),
             head_px_median=float(np.median(hp[inframe])) if inframe.any() else 0.0,
             head_px_p10=float(np.percentile(hp[inframe], 10)) if inframe.any() else 0.0,
             head_px_p90=float(np.percentile(hp[inframe], 90)) if inframe.any() else 0.0,
             frame_fill=float(fill),
             near_m=float(d[inframe].min()) if inframe.any() else float("nan"),
             far_m=float(d[inframe].max()) if inframe.any() else float("nan"),
             px_per_m_at_aim=K.px_per_m(float(np.linalg.norm(
                 np.asarray(aim, float) - np.asarray(loc, float))),
                 float(lens), rx),
             # THE SAME `k` THE PROJECTION ABOVE USED, at the aim distance.
             # Reported separately from `head_px_median` because the median is
             # taken over whatever happens to be in frame and therefore moves
             # with the field of view -- it is a property of the block, not of
             # the optics, and comparing two lenses on it compares two
             # different populations.
             head_px_at_aim=float(k * _HEAD_H_M / max(float(np.linalg.norm(
                 np.asarray(aim, float) - np.asarray(loc, float))), 1e-9)),
             what=what)
    why = []
    if m["n_in_frame"] == 0:
        why.append("NOTHING IN FRAME -- 0 of %d planned figures project inside "
                   "%dx%d. This is beat 1's failure exactly." % (len(plan), rx, ry))
    if m["n_faces_resolved"] < min_faces:
        why.append("only %d unoccluded faces at >= %.0f px (need %d); median "
                   "head is %.1f px" % (m["n_faces_resolved"], head_px,
                                        min_faces, m["head_px_median"]))
    if m["n_heads_resolved"] < int(min_heads):
        why.append("only %d unoccluded HEADS at >= %.0f px (need %d)"
                   % (m["n_heads_resolved"], head_px, int(min_heads)))
    if abs(elev) > max_elev:
        why.append("axis is %+.1f deg from horizontal (limit %.1f) -- this "
                   "frame shows the tops of heads, not faces"
                   % (elev, max_elev))
    m["verdict"] = "; ".join(why)
    return m


def preflight_report(rows, fh=None):
    out = ["%-22s %5s %7s %7s %6s %6s %7s %7s %7s %6s  %s"
           % ("camera", "lens", "aim m", "px/m", "elev", "inframe", "unocc",
              "heads", "faces", "fill", "head px med/p10")]
    for m in rows:
        out.append("%-22s %5.0f %7.1f %7.1f %+6.2f %6d %7d %7d %7d %6.2f  %.1f / %.1f%s"
                   % (m["name"], m["lens"], m["aim_dist_m"],
                      m["px_per_m_at_aim"], m["elev_deg"], m["n_in_frame"],
                      m["n_unoccluded"], m["n_heads_resolved"],
                      m["n_faces_resolved"],
                      m["frame_fill"], m["head_px_median"], m["head_px_p10"],
                      "" if not m["verdict"] else "   <<< " + m["verdict"]))
    s = "\n".join(out)
    if fh:
        fh.write(s + "\n")
    return s


# --------------------------------------------------------------------------
# 5b.  THE CAMERAS -- because the gate is necessary and not sufficient
# --------------------------------------------------------------------------
#
# Each framing is aimed at a claim rather than at the prettiest part of the
# block. The project's own record is that every one of the crew tier's six
# worst defects was found in a picture and none of them by a check: 54
# inside-out pieces, a pointed helmet, a cap inside the hair, a livery band
# across the ribs, a mark at 2 % contrast, sleeve heads as open chimneys.


def block_axes(plan):
    """The block's own frame: (centre, along, out, car_bearing_deg).

    `along` is the principal axis of the seat positions in plan -- 40.34 deg
    on TRIBUNE PRINCIPALE, over a 176 m run against 20 m of depth. `out` is the
    mean seat facing, i.e. the direction the crowd looks, which is the only
    side a camera can see a face from.
    """
    P = np.array([[p["pos"][0], p["pos"][1], p["z"]] for p in plan], float)
    ctr = P.mean(axis=0)
    C = P[:, :2] - P[:, :2].mean(axis=0)
    vt = np.linalg.svd(C, full_matrices=False)[2]
    a = vt[0]
    along = np.array([a[0], a[1], 0.0])
    # SEATED FIGURES ONLY. `aisle` and `steps` take `seat_face + 180` when they
    # are walking down the block, so averaging every role's body yaw averages a
    # vector with its own negation and returns whatever the imbalance is.
    B = np.radians([p["body_yaw_deg"] for p in plan
                    if p["role"] not in _ON_FOOT] or
                   [p["body_yaw_deg"] for p in plan])
    out = np.array([np.cos(B).mean(), np.sin(B).mean(), 0.0])
    n = np.linalg.norm(out)
    if n < 0.5:
        raise RuntimeError(
            "the seated bodies of this block do not agree on a facing "
            "(resultant %.3f) -- there is no side to put a camera on" % n)
    return ctr, along, out / n, P


def _cam(name, loc, aim, lens, coll, scene, samples=256, res=None):
    K.macro_rig(name, tuple(loc), tuple(aim), lens, coll, scene=scene,
                samples=samples, resolution=res,
                i_know_this_is_not_the_gate_resolution=(res is not None))
    return bpy.data.objects[name]


def camera_plan(plan, focus, library_xyz=None):
    """Every camera this item shoots, as pure arithmetic. NO bpy.

    Returns a list of dicts -- name, loc, aim, lens, samples, what, and the
    preflight bar each one has to clear -- so `--preflight` can check a camera
    before anything is built, and `add_cameras` can only ever build what the
    preflight has already agreed to. The two are the SAME list; a camera that
    is checked in one place and placed by different arithmetic in another is
    how `CAM_SHEET` ended up 0.0 m from its aim.

    THE GEOMETRY, on TRIBUNE PRINCIPALE and stated so it can be checked:
    the bank runs 176 m along bearing 40.34 deg and is ~20 m deep; every seat
    faces 130.0 deg (spread 0.2 deg); the car at frame 1009 is 664 m away on
    bearing 143.2 deg. So the car is only 13.2 deg off the stand's own normal
    -- which is why an on-axis frame is a WEAK test of attention (bodies point
    almost into the lens anyway) and why the along-the-bank frame at ~76 deg
    to the seat facing is the strong one: there a turned head is a face
    rotated out of a shoulder line, and there is no way to fake it.
    """
    ctr, along, out, P = block_axes(plan)
    car = math.degrees(math.atan2(focus[1] - ctr[1], focus[0] - ctr[0]))
    seated = [p for p in plan if p["role"] == "sit"]
    onfoot = [p for p in plan if p["role"] in _ON_FOOT] or seated
    zlo, zhi = float(P[:, 2].min()), float(P[:, 2].max())
    zmid = 0.5 * (zlo + zhi)
    # HALF THE BLOCK'S OWN LENGTH. Every distance below is a multiple of it and
    # every lens is derived from the distance it ends up at, so this set of
    # framings survives being pointed at a block that is not TRIBUNE
    # PRINCIPALE. A camera plan built out of absolute metres is a plan for one
    # grandstand, and there are six.
    half_len = 0.5 * float(np.ptp((P[:, :2] - ctr[:2]) @ along[:2]))
    if half_len < 3.0:
        raise RuntimeError("block is %.1f m long: there is nothing to shoot "
                           "along" % (2 * half_len))
    n_bar = int(min(300, max(40, 0.08 * len(plan))))
    specs = []

    def at_bearing(aim, dist, bearing_deg, elev_deg):
        a, e = math.radians(bearing_deg), math.radians(elev_deg)
        return np.asarray(aim, float) + dist * np.array(
            [math.cos(e) * math.cos(a), math.cos(e) * math.sin(a),
             math.sin(e)])

    def lens_for(loc, aim, head_px):
        """The lens that makes a head `head_px` tall AT THE AIM POINT.

        Not a round number picked because it sounded cinematic: the question
        this item has to answer is "is that the same person as the one next to
        him", the answer needs a face, and a face needs pixels. The distance
        follows from the block; the lens follows from the distance.
        """
        d = float(np.linalg.norm(np.asarray(aim, float)
                                 - np.asarray(loc, float)))
        return head_px / _HEAD_H_M * K.SENSOR_MM * d / K.RES_X_4K

    def add(nm, loc, aim, lens, what, samples=512, bar=None):
        specs.append(dict(name=PFX + nm, loc=tuple(float(v) for v in loc),
                          aim=tuple(float(v) for v in aim), lens=float(lens),
                          samples=int(samples), what=what,
                          bar=bar if bar is None else dict(bar)))

    # 1. ALONG THE BANK. Camera 110 m back down the block's own long axis and
    #    28 m out in front of it, at MID-BANK HEIGHT so the axis is level
    #    (+0.15 deg), on a 300 mm lens. Measured on the realised plan: 1,293
    #    figures in frame, 653 of them unoccluded, **526 with an unoccluded
    #    face at >= 40 px**, median head 58.8 px, frame fill 0.86, depth 65 to
    #    193 m. This is the frame the whole per-figure-variety question needs
    #    and the one `BLOCK_CROSS` could not be: same subject, 5.8x the head.
    #
    #    THE HEIGHT IS NOT AN OVERSIGHT. A camera at literal track level (2 m)
    #    measures 313 unoccluded heads instead of 653 and a frame fill of 0.33,
    #    because the front rows eclipse everything behind them -- checked, in
    #    the same instrument, before choosing 6.0 m. Level ALONG the bank is
    #    what "along the stand" has to mean on a raked bank; looking UP at it
    #    from the track puts sky behind the top rows and chins in front.
    a_loc = (ctr - 1.25 * half_len * along + 0.32 * half_len * out
             + np.array([0.0, 0.0, zmid - ctr[2]]))
    a_aim = np.array([ctr[0], ctr[1], zmid])
    add("CAM_CROWD_ALONG", a_loc, a_aim, lens_for(a_loc, a_aim, 65.0),
        "the bank ALONG its own axis, level: a 65 px head at the aim point "
        "and 526 unoccluded faces at >= 40 px on TRIBUNE PRINCIPALE. "
        "Per-figure variety, and head-turn against a shoulder line at "
        "~76 deg to the seat facing.", samples=1024,
        bar=dict(min_faces=n_bar, head_px=40.0, max_elev=2.0))
    # 2. THE CAR'S OWN BEARING, LEVEL, at the same 300 mm. Looking straight
    #    into a raked bank is the one geometry with almost no self-occlusion:
    #    342 in frame, 338 unoccluded, 300 faces at >= 40 px. Every head that
    #    is watching points INTO this lens and every head that is not is
    #    obvious. It is the weak half of the attention pair by construction
    #    (see the docstring) and it is still the one that shows the 27 %.
    o_aim = np.array([ctr[0], ctr[1], zmid])
    o_loc = at_bearing(o_aim, 1.70 * half_len, car, 0.0)
    add("CAM_ATTN_ONAXIS", o_loc, o_aim, lens_for(o_loc, o_aim, 50.0),
        "the block from the car's own bearing, level: a watching head is a "
        "FACE, a non-watching one is a profile. Judge the 27 %.",
        samples=1024, bar=dict(min_faces=int(n_bar * 0.67), head_px=40.0,
                               max_elev=1.0))
    # 3. 90 DEG OFF THE CAR'S BEARING, level, 300 mm, from the other flank.
    #    The A/B partner for 2: the same people, bodies square to the track,
    #    heads turned out of that square. If the crowd was rotated bodily
    #    instead of turning its heads, 2 and 3 cannot both be right.
    # WHICH FLANK. "90 deg off the car" leaves the SIDE free, and the two sides
    # are not equivalent: one of them looks down the rows and sees the back of
    # every head in front. Both candidates are projected and the one that
    # actually resolves faces wins. This is not the instrument choosing to
    # satisfy itself -- the constraint (90 deg off the car bearing, level, a
    # 65 px head at the aim) is fixed either way, and only the sign is free.
    p_aim = np.array([ctr[0], ctr[1], zmid])
    cand = []
    for sgn in (+90.0, -90.0):
        L = at_bearing(p_aim, 1.28 * half_len, car + sgn, 0.0)
        pf = preflight("probe", L, p_aim, lens_for(L, p_aim, 65.0), plan)
        # ranked on HEADS, not faces: see the bar note below. Ranking a profile
        # camera on face-toward-lens picks the flank that is least in profile.
        cand.append((pf["n_heads_resolved"], pf["n_faces_resolved"], sgn, L))
    p_loc = max(cand)[3]
    # ITS BAR IS DIFFERENT ON PURPOSE, and the reason is geometric rather than
    # convenient. This camera stands 90 deg off the car, so the seated bodies
    # are EDGE-ON to it and the face-toward-lens test (`facing > 0.10`, ~84 deg)
    # is near its zero by construction: the figures it counts as "faces" are
    # exactly the ones whose HEADS have turned out of that edge-on shoulder
    # line far enough to show, which IS the signal this frame exists to carry.
    # Measured on TRIBUNE PRINCIPALE: 1,450 in frame, **621 unoccluded heads**
    # at >= 40 px, of which **175** are turned toward the lens. Both are
    # barred: 300 heads (so the shoulder lines are countable) and 120 turned
    # (so a 10 % subgroup still has ~12 members and a difference between this
    # frame and CAM_ATTN_ONAXIS means something).
    # Setting `min_faces` to 0.67 x 300 = 201 here, as the other two carry,
    # rejected a camera that was doing its job -- and the rejection was RIGHT
    # to fire, because it caught that the bar had been written before the
    # quantity was understood.
    add("CAM_ATTN_PROFILE", p_loc, p_aim, lens_for(p_loc, p_aim, 65.0),
        "the same block at 90 deg to the car: bodies EDGE-ON to the lens, and "
        "the heads that have turned out of that shoulder line are the "
        "attention claim made visible. The half a frontal frame cannot see.",
        samples=1024,
        bar=dict(min_faces=120, min_heads=300, head_px=40.0, max_elev=1.0))
    # 4. THE MANIFEST'S OWN FRAMING. 14.7 m on a 28 mm lens is what the film
    #    does; a 1.25 m seated figure reads 254 px here and nowhere else.
    s0 = np.array([seated[len(seated) // 2]["pos"][0],
                   seated[len(seated) // 2]["pos"][1],
                   seated[len(seated) // 2]["z"] + 0.62])
    add("CAM_ROW", at_bearing(s0, FILMED_M, car + 26.0, 4.0), s0, LENS_MM,
        "a seated row at the manifest's own 14.7 m / 28 mm", samples=512,
        bar=dict(min_faces=8, head_px=40.0, max_elev=8.0))
    # 5. THE 15 % ON THEIR FEET, which is defect 7 and the part with a
    #    full-length silhouette and the fewest sources behind it.
    F = np.array([[p["pos"][0], p["pos"][1], p["z"]] for p in onfoot],
                 float).reshape(-1, 3)
    fc = F[np.argsort(np.linalg.norm(F - F.mean(axis=0), axis=1))[
        len(F) // 12]] + np.array([0.0, 0.0, 0.95])
    add("CAM_FEET", at_bearing(fc, 9.0, car + 8.0, 3.0), fc, 50.0,
        "the people on their feet -- standing, walking, on the steps, "
        "leaning on the rail", samples=512,
        bar=dict(min_faces=6, head_px=40.0, max_elev=8.0))
    # 6. HANDS AND WHAT IS IN THEM. Defect 6 (mitten hands) and defect 3 (no
    #    props) are both here, and neither survives being seen at 100 px of
    #    hand. `min_faces` is 2 because this frame is deliberately narrow.
    h0 = np.array([seated[len(seated) // 3]["pos"][0],
                   seated[len(seated) // 3]["pos"][1],
                   seated[len(seated) // 3]["z"] + 0.55])
    add("CAM_HANDS", at_bearing(h0, 3.2, car + 40.0, -2.0), h0, 85.0,
        "hands, faces and held props at 0.7 mm/px -- defects 1, 3 and 6",
        samples=768, bar=dict(min_faces=2, head_px=40.0, max_elev=8.0))
    # 7. THE LIBRARY ITSELF, laid out. The variety question answered by LOOKING
    #    at every source side by side rather than by counting them. Not
    #    preflighted against the plan -- its subject is the contact sheet, not
    #    the block -- so it carries `bar=None` and says so.
    if library_xyz is not None and len(library_xyz):
        L = np.asarray(library_xyz, float)
        lc = L.mean(axis=0)
        d = float(max(np.ptp(L[:, 0]), np.ptp(L[:, 1]))) * 0.80
        if d < 1.0:
            raise RuntimeError(
                "CAM_SHEET would stand %.3f m from its aim: the library "
                "positions handed in are all the same point. That is the "
                "depsgraph bug of 2026-08-02 (matrix_world read before any "
                "evaluation) coming back -- pass `o.location`." % d)
        add("CAM_SHEET", at_bearing((lc[0], lc[1], lc[2] + 0.9), d, 250.0,
                                    26.0), (lc[0], lc[1], lc[2] + 0.9), 50.0,
            "the whole source library side by side: if a repeat is visible "
            "HERE the count is not the answer", samples=512, bar=None)
    return specs


def add_cameras(res, coll=None, samples=None, draft=False, strict=True):
    """The looking cameras, PRE-FLIGHTED before any of them is created.

    `draft` is False by default now. It used to be True, which is how a scene
    whose saved `resolution_x` is 1920 came to have four 3840x2160 PNGs beside
    it: the harness overrode the resolution the module had chosen, and nothing
    in the module knew which of the two the frames had been judged at. The gate
    scores every pixel figure against 3840 (R2-020); so does `preflight`.
    """
    scene = bpy.context.scene
    cams = K.coll(COLL + "/Cameras", K.coll(COLL))
    K.contract_sun(PFX, scene=scene, coll_=K.coll(COLL + "/Standins",
                                                  K.coll(COLL)))
    # THE ITEM TEST SCENES ARE 0.580 STOPS OVER-EXPOSED RELATIVE TO THE FILM,
    # and every appearance judgement made on one has been made under the wrong
    # light. `itemkit.contract_sun` sets
    # `world_contract.REFERENCE_EXPOSURE_EXTERIOR = -3.048`; the film renders
    # at `film_exposure.FILM_EXPOSURE = -3.628`, and
    # `tools/build_verify_scene.py` says in terms that -3.048 is "the refuted
    # contract value" and must never be used. The five delivered
    # `render/items/spectator_crowd/*.png` frames were all shot at -3.048.
    #
    # 0.58 stops is not a rounding error on a face: it is most of the shading
    # range a brow ridge and a nasolabial fold have to work in, and defect 1 is
    # "the face is a featureless oval". This does NOT claim to be the cause --
    # the face ladder decides that -- but no more frames should be judged under
    # a light the film does not use.
    #
    # `contract_sun` is `itemkit`'s and another agent owns it, so this is
    # corrected here, loudly, rather than edited there.
    try:
        sys.path.insert(0, _WORLD)
        import film_exposure as FX                            # noqa: E402
        was = float(scene.view_settings.exposure)
        scene.view_settings.exposure = float(FX.FILM_EXPOSURE)
        HK.log("EXPOSURE: contract_sun left %+.3f EV (world_contract's refuted "
               "REFERENCE_EXPOSURE_EXTERIOR); set to film_exposure."
               "FILM_EXPOSURE %+.3f -- a %.3f stop correction. Frames shot "
               "before 2026-08-03 are that much over."
               % (was, FX.FILM_EXPOSURE, was - FX.FILM_EXPOSURE))
    except Exception as e:                                    # pragma: no cover
        raise RuntimeError(
            "could not read film_exposure.FILM_EXPOSURE (%s). REFUSING to "
            "render a crowd at an exposure nobody has checked -- that is "
            "R2-020 with a different constant." % e)
    stand = K.coll(COLL + "/Standins", K.coll(COLL))
    if res.get("facings") is not None and not bpy.data.objects.get(
            "CTX_SeatStandin"):
        nt = K.NT(PFX + "SeatCtx")
        nt.principled_out(base_color=(0.035, 0.041, 0.052), roughness=0.62)
        build_seat_standins(res["seats"], res["facings"], stand, nt.m)
    plan, focus = res["plan"], res["focus"]
    lib = [tuple(o.location) for o in res.get("library") or []]
    specs = camera_plan(plan, focus, library_xyz=lib or None)
    rx, ry = ((1920, 1080) if draft else (K.RES_X_4K, K.RES_Y_4K))

    rows, bad = [], []
    for s in specs:
        if s["bar"] is None:
            continue
        m = preflight(s["name"], s["loc"], s["aim"], s["lens"], plan,
                      res=(rx, ry), what=s["what"], **s["bar"])
        rows.append(m)
        if m["verdict"]:
            bad.append(m)
    HK.log("\n" + preflight_report(rows))
    if bad and strict:
        raise RuntimeError(
            "REFUSING to build %d camera(s) that cannot show what they are "
            "for:\n  %s\nThis is the check that `CAM_BLOCK_ONAXIS` (median "
            "head 8.0 px) and `CAM_BLOCK_CROSS` (10.1 px) were shipped and "
            "rendered at 4K without."
            % (len(bad), "\n  ".join("%s: %s" % (m["name"], m["verdict"])
                                     for m in bad)))

    out = {}
    for s in specs:
        _cam(s["name"], s["loc"], s["aim"], s["lens"], cams, scene,
             samples=(samples or s["samples"]),
             res=(None if not draft else (rx, ry)))
        cd = bpy.data.objects[s["name"]].data
        # NOT ASSUMED. The predecessor's note blames depth of field for two
        # unusable frames and the datablock says `use_dof False`; both halves
        # of that were taken on trust. State it and check it.
        if cd.dof.use_dof:
            raise RuntimeError(
                "%s has depth of field ON. Every camera in this item is a "
                "MEASURING instrument: a crowd read through a circle of "
                "confusion cannot answer a question about a 40 px head."
                % s["name"])
        out[s["name"]] = s["what"]
        HK.log("  cam %-24s %6.1f m %3.0f mm -> %5.0f px/m  dof=%s  %s"
               % (s["name"], np.linalg.norm(np.asarray(s["aim"])
                                            - np.asarray(s["loc"])),
                  s["lens"],
                  K.px_per_m(float(np.linalg.norm(np.asarray(s["aim"])
                                                  - np.asarray(s["loc"]))),
                             s["lens"], rx), cd.dof.use_dof, s["what"]))
    scene.render.resolution_x, scene.render.resolution_y = rx, ry
    scene.camera = bpy.data.objects[PFX + "CAM_CROWD_ALONG"]
    return out


# --------------------------------------------------------------------------
# 6.  SELFTEST
# --------------------------------------------------------------------------

def selftest(verbose=True):
    fails = []

    def chk(name, ok, detail):
        if not ok:
            fails.append(name)
        if verbose:
            print("  %-38s %s %s" % (name, "PASS" if ok else "FAIL", detail))

    n = library_size()
    idxs = [_slot_index(r, b, k) for r in HK.STAND_ROLES
            for b in range(ROLE_BINS[r]) for k in range(ROLE_CELL[r])]
    # and every index the PLAN can produce must land inside that space
    reach = {library_index(r, g, k) for r in HK.STAND_ROLES
             for g in np.linspace(-95.0, 95.0, 401) for k in
             range(ROLE_CELL[r])}
    chk("library_index_is_a_bijection",
        len(set(idxs)) == len(idxs) == n and min(idxs) == 0
        and max(idxs) == n - 1 and reach == set(idxs),
        "%d slots, %d distinct, range %d..%d, and the %d indices the PLAN can "
        "reach are exactly that set -- a collision or a gap here silently "
        "collapses two cells onto one mesh, or points a seat at a source that "
        "was never built, which is the variety rule failing invisibly"
        % (n, len(set(idxs)), min(idxs), max(idxs), len(reach)))

    # the gate's own bar, computed the way item_gate computes it
    need = max(8, min(40, int(math.sqrt(DECLARED))))
    chk("source_set_clears_the_gate_bar",
        n >= need and 1.0 / n <= 0.25,
        "%d sources against the gate's max(8, min(40, sqrt(%d))) = %d, worst "
        "possible top_source_share %.4f against the 0.25 limit"
        % (n, DECLARED, need, 1.0 / n))

    rows, cols = 22, 96
    seats = np.array([[r, c, c * 0.50, -36.6 - r * 0.88, 2.56 + r * 0.335]
                      for r in range(rows) for c in range(cols)], float)
    face = np.full(len(seats), 90.0)
    focus = (24.0, -8.0, 0.6)
    plan = plan_block(4242, seats, face, focus)
    used = {r["src"] for r in plan}
    bins = sorted({r["gaze_bin"] for r in plan if r["role"] == "sit"})
    chk("attention_reaches_the_library",
        len(bins) >= 5 and len(used) >= 200,
        "a %dx%d block picks %d gaze bins for its seated figures and touches "
        "%d of the %d sources; a crowd whose heads all point the same way "
        "would touch one bin, and the wave-1 field picks its source with a "
        "FunctionNodeRandomValue that cannot know where the seat is"
        % (rows, cols, len(bins), len(used), n))

    # THE BODY DOES NOT SWIVEL. A seated spectator's chair faces the track.
    body = np.array([r["body_yaw_deg"] for r in plan if r["role"] == "sit"])
    head = np.array([r["head_yaw_deg"] for r in plan if r["role"] == "sit"])
    chk("seats_do_not_swivel",
        float(np.abs(body - 90.0).max()) <= 45.0001
        and float(np.abs(head).max()) <= ROLE_SPAN["sit"] + 1e-4,
        "worst body yaw departs the seat's own facing by %.1f deg and the "
        "worst head turn is %.1f deg (clamped at %.0f); the naive version "
        "rotates the whole instance to the car and the stand reads as a "
        "fairground carousel"
        % (float(np.abs(body - 90.0).max()), float(np.abs(head).max()),
           ROLE_SPAN["sit"]))

    # WHAT IS BAKED IS NOT WHAT IS PLANNED, AND THE ATTENTION CHECK READS THE
    # PLAN.  `attention_spread` measures `yaw_deg` -- the bearing `compose_
    # stand` decided a person is attending to. What a viewer sees is
    # `body_yaw_deg` (the instance rotation) plus the head turn BAKED into
    # whichever library cell the seat picked, and those are two different
    # numbers separated by the binning. Measured on TRIBUNE PRINCIPALE with the
    # superseded 3-bin roles: mean |error| 5.8 deg overall but 26.5 deg on
    # `steps` and up to 53.9 deg worst case -- 173 people on their feet whose
    # heads point somewhere the plan never asked for, invisible to every
    # statistic in this file because every one of them reads the plan.
    #
    # POSITIVE CONTROL: the same plan re-binned over the superseded global
    # +-72 / 3-bin scheme, reproduced here rather than reached for by a flag.
    def _realised(pl, span, nb):
        out = []
        for r in pl:
            n_ = nb.get(r["role"], ROLE_BINS[r["role"]])
            s_ = span.get(r["role"], ROLE_SPAN[r["role"]])
            if n_ <= 1:
                bd = 0.0
            else:
                t = (float(np.clip(r["head_yaw_deg"], -s_, s_)) + s_) / (2 * s_)
                bd = -s_ + 2 * s_ * round(t * (n_ - 1)) / (n_ - 1)
            out.append(r["body_yaw_deg"] + bd)
        return np.asarray(out)

    # AND THE SUBJECT IS THE BINNING, NOT THE ANATOMY. The first version of
    # this measured the realised head against `yaw_deg` and went RED at 89.6
    # deg -- on a build where the binning error is 5.4 deg -- because a seated
    # body is capped at 45 deg and a neck at 72, so someone whose friend is
    # directly behind them CANNOT look at them and the residual is a correct
    # refusal, not an error. A statistic that cannot separate the term it is
    # about from a deliberate clamp elsewhere is not measuring the term it is
    # about (this file, section 000.4). The reference is therefore the
    # UNQUANTISED realisation, `body_yaw + head_yaw`, and the anatomical clamp
    # is reported separately as the number it is.
    P = np.array([[p["pos"][0], p["pos"][1]] for p in plan])
    bear = np.degrees(np.arctan2(focus[1] - P[:, 1], focus[0] - P[:, 0]))
    want = np.array([p["body_yaw_deg"] + p["head_yaw_solved_deg"]
                     for p in plan])
    intent = np.array([p["yaw_deg"] for p in plan])
    real = np.array([p["body_yaw_deg"] + p["gaze_baked_deg"] for p in plan])
    # THE CONTROL RE-PLANS. `_realised` used to re-bin the SHIPPED plan's own
    # `head_yaw_deg`, which is now the already-baked value, so the "superseded
    # global 9/3-bin scheme" was being applied to a number that had already
    # been quantised at the role's own bins and measured 28 deg instead of 36.
    # A control fed the fixed artefact is not a control.
    lp = plan_block(4242, seats, face, focus, legacy_gaze=True)
    lwant = np.array([p["body_yaw_deg"] + p["head_yaw_solved_deg"]
                      for p in lp])
    old = _realised(lp, {r: 72.0 for r in HK.STAND_ROLES},
                    {"sit": 9, "stand": 9, "turned": 3, "lean_rail": 3,
                     "aisle": 3, "steps": 3})
    wrap = lambda a, b: np.abs(((a - b + 180.0) % 360.0) - 180.0)   # noqa: E731
    e_new, e_old = wrap(real, want), wrap(old, lwant)
    f_new = float((wrap(real, bear) < 20.0).mean())
    f_int = float((wrap(intent, bear) < 20.0).mean())
    clamp = wrap(want, intent)
    chk("what_is_baked_is_what_was_planned",
        e_new.max() <= 11.5 and e_old.max() > 30.0
        and abs(f_new - f_int) < 0.02,
        "binning moves the head by at most %.1f deg (mean %.1f) from the yaw "
        "the composer solved; the superseded global 9-bin / 3-bin scheme moves "
        "it up to %.1f deg (mean %.1f). Attention measured on the REALISED "
        "geometry is %.1f %% within 20 deg against the plan's own %.1f %%. "
        "Separately, %.1f %% of the block cannot physically reach what it is "
        "attending to (neck 72 deg + seated body 45 deg), worst %.0f deg short "
        "-- that is the anatomy refusing, not the library"
        % (e_new.max(), e_new.mean(), e_old.max(), e_old.mean(),
           100 * f_new, 100 * f_int, 100 * float((clamp > 1.0).mean()),
           clamp.max()))

    a = HK.attention_spread(plan, focus)
    a0 = HK.attention_spread(
        plan_block(4242, seats, face, focus, attention=0.0), focus)
    chk("crowd_watches_the_car",
        a["frac_on"] > 0.55 and a0["frac_on"] < 0.30,
        "%.1f %% attend within 20 deg (circ sd %.1f deg); the same block with "
        "attention = 0 measures %.1f %% and %.1f deg"
        % (100 * a["frac_on"], a["circ_sd_deg"], 100 * a0["frac_on"],
           a0["circ_sd_deg"]))

    # EVERY ROLE MUST REACH ITS WHOLE LIBRARY, AND NO SOURCE MAY DOMINATE ITS
    # OWN ROLE.  `source_set_clears_the_gate_bar` above reports the WORST
    # POSSIBLE share, 1/402, and the gate reports the share over the whole
    # crowd -- and both of them are blind to the failure that actually
    # happened, because 85 % of a block is seated and a seated majority buries
    # everything else in the denominator. The 477 people on their feet were
    # sharing 24 meshes at 34 copies of one of them, at a global share of
    # 0.0089. THE RED LINE IS PER ROLE.
    #
    # POSITIVE CONTROL: the superseded rule -- `head = 0` for anyone on their
    # feet -- reproduced verbatim here rather than by reaching for a flag, so
    # it fails on its own terms forever even if the shipped rule is rewritten
    # again. NEGATIVE CONTROL: the shipped plan.
    def _role_reach(pl, flatten):
        d = {}
        for r in pl:
            hd = 0.0 if (flatten and r["role"] not in ("sit", "turned")) \
                else r["head_yaw_deg"]
            s = library_index(r["role"], hd, int(HK.hash01(
                4242, r["row"] * 977 + max(r["col"], 0) * 13
                + (1 if r["col"] < 0 else 0)) * 1e6))
            d.setdefault(r["role"], []).append(s)
        return d

    live = _role_reach(plan, False)
    dead = _role_reach(plan, True)

    # AGAINST A MATCHED CONTROL, NOT AN ABSOLUTE BAR. 13 people drawn over 12
    # sources CANNOT have a max share below 1/13, so an absolute 0.20 fails a
    # role for being small -- which is the instrument reporting its own
    # denominator. The control draws the same number of people uniformly at
    # random from the same role's built library and takes the same statistic.
    def _worst(d, tag):
        w, nm = 0.0, ""
        for role, ss in d.items():
            c = {}
            for s in ss:
                c[s] = c.get(s, 0) + 1
            nsrc = ROLE_BINS[role] * ROLE_CELL[role]
            g = np.random.default_rng(4242)
            ctl = max(np.bincount(g.integers(0, nsrc, len(ss)),
                                  minlength=nsrc)) / float(len(ss))
            f = (max(c.values()) / float(len(ss))) / max(ctl, 1e-9)
            if f > w:
                w, nm = f, ("%s: %d people, %d of %d sources, worst %.3f "
                            "against a uniform draw's %.3f"
                            % (role, len(ss), len(c), nsrc,
                               max(c.values()) / float(len(ss)), ctl))
        return w, nm

    wl, nl = _worst(live, "live")
    wd, nd = _worst(dead, "dead")
    chk("no_source_dominates_its_own_role",
        wl < 2.00 and wd > 2.50,
        "worst per-role source share is %.2fx what a uniform draw over that "
        "role's OWN library would give (%s); the superseded rule -- head yaw "
        "forced to 0 for anyone on their feet, so `gaze_bin` was always 4 and "
        "`library_index` could reach one bin per role -- measures %.2fx (%s) "
        "on the same plan, which is the user's named red line wearing a "
        "high-vis vest" % (wl, nl, wd, nd))

    # THE SHARP ONE, and it is structural rather than statistical: how many of
    # its own head-yaw bins does each role actually realise? Under the
    # superseded rule the answer was 1 for every role on its feet, ALWAYS, at
    # any block size and any seed -- so `library_index` could not reach the
    # other bins whatever the plan said, and 216 of 402 sources were built,
    # saved into a 196 MB blend and never instanced. "How many sources did the
    # sample happen to touch" is a statistic about the sample; "how many can
    # the index function REACH" is a property of the code.
    def _bins(d_plan, flatten):
        out = {}
        for r in d_plan:
            hd = 0.0 if (flatten and r["role"] not in ("sit", "turned")) \
                else r["head_yaw_deg"]
            out.setdefault(r["role"], set()).add(role_bin(r["role"], hd))
        return out

    bl, bd = _bins(plan, False), _bins(plan, True)
    big = [r for r in bl if sum(1 for p in plan if p["role"] == r) >= 20]
    ok_l = all(len(bl[r]) >= min(2, ROLE_BINS[r]) for r in big)
    ok_d = any(len(bd[r]) == 1 and ROLE_BINS[r] > 1 for r in big)
    chk("every_role_turns_its_head",
        ok_l and ok_d,
        "bins realised per role %s of %s available; the superseded rule gives "
        "%s -- one bin for every role on its feet, which pins those roles to "
        "ROLE_CELL sources however large the library is"
        % ({r: len(bl[r]) for r in sorted(bl)},
           {r: ROLE_BINS[r] for r in sorted(bl)},
           {r: len(bd[r]) for r in sorted(bd)}))

    cl, occ = HK.occupancy_clumpiness(
        [(p["row"], p["col"]) for p in plan if p["col"] >= 0], rows, cols)
    rr = np.random.default_rng(11)
    ctl, _ = HK.occupancy_clumpiness(
        [(r, c) for r in range(rows) for c in range(cols)
         if rr.random() < occ], rows, cols)
    chk("occupancy_is_clumped_on_real_seats",
        cl > 0.05 and cl > 3.0 * abs(ctl),
        "join-count clumpiness %+.4f at %.0f %% occupancy against a Bernoulli "
        "control at the same mean measuring %+.4f" % (cl, 100 * occ, ctl))

    # [10] THE REALISED GAZE FIELD IS CONTINUOUS, not a comb.
    # `crowd_watches_the_car` counts everyone within 20 deg and scores 73 %
    # whether the field is smooth or has holes punched through it, so it is
    # measured here instead: bin the REALISED head bearing (body + baked) at
    # 2 deg over the watching core and count EMPTY bins. The positive control
    # is the superseded ordering -- body solved first, head quantised second --
    # reproduced verbatim below, which leaves 10 deg of every 18 occupied.
    def _comb(bear):
        b = ((bear - np.degrees(math.atan2(
            np.sin(np.radians(bear)).mean(),
            np.cos(np.radians(bear)).mean())) + 180.0) % 360.0) - 180.0
        core = b[np.abs(b) < 30.0]
        h = np.histogram(core, bins=np.arange(-30, 31, 2))[0]
        return int((h == 0).sum()), len(core), h

    # the CONTROL is the SAME FUNCTION re-run with `legacy_gaze=True`, not a
    # reconstruction of it from the fixed plan's own output. The first version
    # of this check did the latter -- derived the old stance by subtracting the
    # new residual back off `body_yaw_deg` -- and returned 0 empty bins for
    # BOTH arms, i.e. a control that could not fail. Sixteenth time.
    lplan = plan_block(4242, seats, face, focus, legacy_gaze=True)
    n_e, n_c, _h = _comb(np.array([p["body_yaw_deg"] + p["gaze_baked_deg"]
                                   for p in plan]))
    c_e, c_c, _ = _comb(np.array([p["body_yaw_deg"] + p["gaze_baked_deg"]
                                  for p in lplan]))
    chk("realised_gaze_field_has_no_comb",
        n_e == 0 and c_e >= 4 and n_c > 400,
        "%d of 30 two-degree bins are EMPTY across the %d-person watching "
        "core; the superseded ordering (body first, head quantised second) "
        "leaves %d of 30 empty over %d -- a crowd occupying 10 deg out of "
        "every 18, which every attention statistic in this file scores "
        "identically" % (n_e, n_c, c_e, c_c))

    # ----------------------------------------------------------------------
    # CAMERA PRE-FLIGHT. Four checks and every one of them has a control that
    # reproduces a camera THIS PROJECT ACTUALLY SHIPPED, verbatim, so it fails
    # on its own terms rather than on a threshold someone might relax.
    # ----------------------------------------------------------------------
    # A SECOND SYNTHETIC BLOCK, and it has to be a realistic SHAPE. The 22x96
    # grid above is 47 m long and 19 m deep -- 2.6:1 -- and "along the bank"
    # degenerates on a block that squat: the camera stands 30 m out and every
    # front row eclipses the one behind. A real grandstand is long and thin
    # (TRIBUNE PRINCIPALE is 176 x 20 m, 8.8:1) and the along-shot is a
    # statement about that shape. Checking a camera designed for a grandstand
    # against a block that is not one measures the control, not the camera.
    crow, ccol = 24, 300
    cseats = np.array([[r, c, c * 0.50, -40.0 - r * 0.90, 2.4 + r * 0.34]
                       for r in range(crow) for c in range(ccol)], float)
    cface = np.full(len(cseats), 90.0)
    # ... and the CAR has to sit where a car sits. On TRIBUNE PRINCIPALE it is
    # 664 m away and 13.2 deg off the stand's own normal, which is why the
    # attention statistic has so little range to work with. Put it 60 deg off
    # instead and the whole crowd cranes its neck, the along-the-bank camera
    # sees the backs of those heads, and the control has quietly become a
    # different problem. 665 m on the seat facing + 13 deg.
    _cc = cseats[:, 2:4].mean(axis=0)
    cfocus = (_cc[0] + 665.0 * math.cos(math.radians(103.0)),
              _cc[1] + 665.0 * math.sin(math.radians(103.0)), 1.2)
    plan = plan_block(4243, cseats, cface, cfocus)
    focus = cfocus
    P = np.array([[p["pos"][0], p["pos"][1], p["z"]] for p in plan], float)
    pctr = P.mean(axis=0)
    span = float(max(np.ptp(P[:, 0]), np.ptp(P[:, 1])))

    def _shipped(dist, bearing, elev):
        a, e = math.radians(bearing), math.radians(elev)
        return pctr + dist * np.array([math.cos(e) * math.cos(a),
                                       math.cos(e) * math.sin(a), math.sin(e)])

    carb = math.degrees(math.atan2(focus[1] - pctr[1], focus[0] - pctr[0]))
    # [10] POSITIVE CONTROL -- the two cameras that were built, rendered at 4K
    # and could not answer the questions they were built for. Reproduced here
    # by the arithmetic that produced them (span * 1.15 / span * 0.85, 50 mm,
    # 9 deg and 11 deg of down-tilt) so that this check fails for the same
    # reason they did and cannot be satisfied by moving a constant.
    m_on = preflight("ctl_BLOCK_ONAXIS", _shipped(span * 1.15, carb, 9.0),
                     pctr, 50.0, plan)
    m_cr = preflight("ctl_BLOCK_CROSS", _shipped(span * 0.85, carb + 78.0,
                                                 11.0), pctr, 50.0, plan)
    chk("preflight_rejects_the_cameras_it_was_written_for",
        bool(m_on["verdict"]) and bool(m_cr["verdict"])
        and m_on["head_px_median"] < 40.0 and m_cr["head_px_median"] < 40.0,
        "the shipped BLOCK_ONAXIS gives a median head of %.1f px and %d "
        "resolvable faces; BLOCK_CROSS %.1f px and %d. Both are rejected. A "
        "check that cannot fail on the artefact it was written about is worth "
        "nothing." % (m_on["head_px_median"], m_on["n_faces_resolved"],
                      m_cr["head_px_median"], m_cr["n_faces_resolved"]))

    # [11] POSITIVE CONTROL -- beat 1's failure: a camera 48.885 deg off its
    # own subject, zero parts in view. Rotate the aim point about the camera
    # by exactly that and the frame must empty.
    good_loc = _shipped(140.0, carb, 0.0)
    th = math.radians(48.885)
    v = pctr - good_loc
    off = good_loc + np.array([v[0] * math.cos(th) - v[1] * math.sin(th),
                               v[0] * math.sin(th) + v[1] * math.cos(th),
                               v[2]])
    m_off = preflight("ctl_AIMED_OFF", good_loc, off, 300.0, plan)
    m_ok = preflight("ctl_AIMED_ON", good_loc, pctr, 300.0, plan)
    chk("preflight_catches_a_camera_aimed_off_its_subject",
        m_off["n_in_frame"] == 0 and bool(m_off["verdict"])
        and m_ok["n_in_frame"] > 100 and not m_ok["verdict"],
        "the same camera aimed at the block sees %d figures and passes; "
        "swung 48.885 deg -- beat 1's own error -- it sees %d and is "
        "rejected" % (m_ok["n_in_frame"], m_off["n_in_frame"]))

    # [12] THE PROJECTION IS NOT ITS OWN AUTHORITY. `attention_spread` measured
    # a yaw it had invented; this could just as easily measure a pixel size it
    # had invented. The head size at the aim point must agree with
    # `itemkit.px_per_m`, which is the number the gate and the brief both use,
    # to within a rounding error -- and it must NOT agree when the lens moves,
    # or the check is comparing a constant with itself.
    d0 = 120.0
    loc0 = _shipped(d0, carb, 0.0)
    a300 = preflight("x300", loc0, pctr, 300.0, plan)
    a150 = preflight("x150", loc0, pctr, 150.0, plan)
    want300 = K.px_per_m(d0, 300.0, K.RES_X_4K) * _HEAD_H_M
    err = abs(a300["head_px_at_aim"] - want300) / want300
    ratio = a300["head_px_at_aim"] / max(a150["head_px_at_aim"], 1e-9)
    chk("preflight_pixel_size_agrees_with_itemkit",
        err < 1e-9 and abs(ratio - 2.0) < 1e-9,
        "a %.2f m head at %.0f m on a 300 mm lens is %.2f px by "
        "itemkit.px_per_m and %.2f px out of the projection's OWN `k` "
        "(%.1e relative); halving the lens halves it, %.6f x -- so the "
        "projection is reading the lens rather than reporting a constant back "
        "to itself" % (_HEAD_H_M, d0, want300, a300["head_px_at_aim"], err,
                       ratio))

    # [13] NEGATIVE CONTROL -- what this module now ships must pass, on the
    # SAME instrument, with no special case.
    specs = camera_plan(plan, focus)
    pf = [preflight(s["name"], s["loc"], s["aim"], s["lens"], plan,
                    what=s["what"], **s["bar"])
          for s in specs if s["bar"] is not None]
    along = [m for m in pf if m["name"].endswith("CAM_CROWD_ALONG")]
    chk("shipped_cameras_clear_their_own_preflight",
        len(pf) >= 6 and not any(m["verdict"] for m in pf)
        and len(along) == 1 and abs(along[0]["elev_deg"]) <= 2.0
        and along[0]["head_px_median"] >= 40.0,
        "%d cameras, %d rejected; CAM_CROWD_ALONG resolves %d unoccluded "
        "faces at >= 40 px, median head %.1f px, axis %+.2f deg from level"
        % (len(pf), sum(1 for m in pf if m["verdict"]),
           along[0]["n_faces_resolved"] if along else -1,
           along[0]["head_px_median"] if along else -1,
           along[0]["elev_deg"] if along else 99))

    if verbose:
        print("\n  spectator_crowd selftest: %d checks, %d FAILED %s"
              % (14, len(fails), fails or ""))
    return fails


def main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else argv[1:]
    p = argparse.ArgumentParser(prog="spectator_crowd")
    p.add_argument("--selftest", action="store_true")
    p.add_argument("--preflight", action="store_true",
                   help="project the REAL block through every camera and "
                        "report what each frame can physically contain. "
                        "Plain python, no Blender, ~25 s -- run it before "
                        "spending a render, every time.")
    p.add_argument("--test-scene", action="store_true")
    p.add_argument("--frame", type=int, default=1009)
    p.add_argument("--blocks", default="TRIBUNE PRINCIPALE")
    p.add_argument("--n", type=int, default=None)
    p.add_argument("--lod", default="L1")
    p.add_argument("--lib-limit", type=int, default=None)
    p.add_argument("--cameras", action="store_true",
                   help="add the LOOKING cameras (see camera_plan). Every one "
                        "is pre-flighted against the plan first and the build "
                        "RAISES if any cannot show what it is for.")
    p.add_argument("--4k", dest="fourk", action="store_true",
                   help="ignored: 4K is now the default. Kept so the old "
                        "command line still runs.")
    p.add_argument("--draft", action="store_true",
                   help="stage the cameras at 1920x1080. R2-020: the gate "
                        "scores every pixel figure against 3840, so a draft "
                        "frame must never be shipped as the artefact.")
    p.add_argument("--out", default=os.path.join(_ITEMS,
                                                 "spectator_crowd_test.blend"))
    a = p.parse_args(argv)
    if a.selftest:
        sys.exit(1 if selftest() else 0)
    if a.preflight:
        seats, facings = seat_array(tuple(a.blocks.split("+")))
        focus = car_at(a.frame)
        plan = plan_block(SEED, seats, facings, focus, n_want=a.n)
        specs = camera_plan(plan, focus)
        rows = [preflight(s["name"], s["loc"], s["aim"], s["lens"], plan,
                          what=s["what"], **s["bar"])
                for s in specs if s["bar"] is not None]
        ctr, along, out, P = block_axes(plan)
        print("BLOCK  %s: %d seats, %d people, %.1f m along bearing %.2f deg, "
              "%.1f m deep, z %.2f..%.2f"
              % (a.blocks, len(seats), len(plan),
                 float(np.ptp((P[:, :2] - ctr[:2]) @ along[:2])),
                 math.degrees(math.atan2(along[1], along[0])),
                 float(np.ptp((P[:, :2] - ctr[:2]) @ out[:2])),
                 P[:, 2].min(), P[:, 2].max()))
        print("CAR at frame %d: %.1f m away on bearing %.2f deg; the seated "
              "BODIES average %.2f deg (the seats themselves face 130.00 with "
              "a 0.2 deg spread), so the car is %.2f deg off"
              % (a.frame,
                 math.hypot(focus[0] - ctr[0], focus[1] - ctr[1]),
                 math.degrees(math.atan2(focus[1] - ctr[1],
                                         focus[0] - ctr[0])),
                 math.degrees(math.atan2(out[1], out[0])),
                 abs(((math.degrees(math.atan2(focus[1] - ctr[1],
                                               focus[0] - ctr[0]))
                       - math.degrees(math.atan2(out[1], out[0])) + 180)
                      % 360) - 180)))
        print()
        print(preflight_report(rows))
        bad = [m for m in rows if m["verdict"]]
        print("\n%d camera(s) rejected." % len(bad))
        sys.exit(1 if bad else 0)
    if a.test_scene:
        lod = {"L0": HK.LOD_L0, "L1": HK.LOD_L1, "L2": HK.LOD_L2,
               "L3": HK.LOD_L3}[a.lod]
        res = build_scene(blocks=tuple(a.blocks.split("+")), frame=a.frame,
                          n_want=a.n, lod=lod, lib_limit=a.lib_limit)
        if a.cameras:
            add_cameras(res, draft=a.draft)
        bpy.ops.wm.save_as_mainfile(filepath=a.out, compress=True)
        HK.log("saved %s" % a.out)


if __name__ == "__main__":
    main()
