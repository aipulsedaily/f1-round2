"""KEEP-OUT GATE — nothing may occupy the road, the car's path, or the camera's path.

    /opt/blender-5.2.0-linux-x64/blender -b <scene.blend> --factory-startup \
        -P tools/placement_gate.py -- --out docs/placement_report.json \
        [--allow SURF_,TER_Ground] [--frames 1,400,792]

WHY
---
    "you need to make sure theres no building no fences etc ont he road every
     thing to be perfectionasistly placed onto the map"

The world is about to be populated by one agent per object — trash cans, truck
wheels, cable ramps, fence posts, hundreds of them, placed in parallel by agents
who cannot see each other's work. Without an automatic gate, "is anything on the
road?" becomes a question nobody can answer until a frame is rendered, and by
then it is a defect in a delivered shot.

The adversarial review already proved this is not hypothetical: 59% of dressing
objects were buried, the Beat-4 corridor was built twice 0.5 m apart, and the
terrain sat on top of the racing surface over 5.3% of its area.

THREE VOLUMES, NOT ONE
----------------------
1. THE ROAD CORRIDOR. Centreline +/- half_width(s), from the surface up to
   ROAD_CLEAR_H. Only the driving surface, its markings and its kerbs belong in
   here. A fence post, a building corner or a tyre stack inside this volume is a
   hard failure — a car would hit it.

2. THE CAR'S DRIVEN PATH. The actual swept volume from telemetry.csv, using the
   measured car box (5.698 x 2.005 x 0.992 m) plus margin, along every frame of
   the transit and the lap. This is stricter than the corridor in the places that
   matter — the racing line runs wide over kerbs, and the transit route leaves
   the circuit entirely to cross the paddock.

3. THE CAMERA'S FLIGHT PATH. The camera flies THROUGH this world for 124 seconds
   without a cut. If it clips a grandstand roof or a catch fence, the shot is
   dead and there is no cutting around it. A sphere of CAM_CLEAR_R is swept along
   every camera key.

Each volume is tested against the EVALUATED geometry of every object, because a
BEVEL or SOLIDIFY modifier is exactly what turns "just clear" into "just
touching".

WHAT COUNTS AS ALLOWED
----------------------
Only things whose job is to be there: the surface itself, its markings, kerbs,
and the ground the wheels roll on. `--allow` takes name prefixes. Everything else
found inside a keep-out volume is reported with its name, the volume it violated,
and how far in it reaches, so the fix is unambiguous.

THE ROAD CORRIDOR IS REFERENCED TO THE ROAD                        (R2, 2026-08-02)
-----------------------------------------------------------------------------
Until today the corridor was an ABSOLUTE world-z band, -0.5 .. +4.5 m, with the
centreline stations pinned at z = 0.0:

    volumes["road_corridor"] = {..., "zlo": -0.5, "zhi": ROAD_CLEAR_H,
                                "pts": [(x, y, 0.0) for ...]}

This circuit climbs and falls: centreline elevation runs -3.666 .. +7.964 m.
Measured over a 14 700-station 0.25 m grid:

    road surface inside the absolute band            49.48 % of stations
    road surface entirely ABOVE the band             28.08 %   <- NO HEADROOM TESTED
    road surface below the band (band floating)      22.44 %

Over 28 % of the lap the gate tested a slab of air the road was not in. A 2 m
cube standing on the racing line at s = 1798.75 (elevation +7.964 m) put ZERO of
its 8 vertices in the band: the gate did not fire, and reported PLACEMENT_CLEAN.
`car_path` and `camera_path` were never affected -- both already reference their
own sample z. Only the corridor was pinned to zero.

The band is now per-station, `elevation(s) - ROAD_ZLO .. elevation(s) + 4.5`,
using the SAME `zband` mechanism `car_path` has always used.

INDEPENDENCE, KEPT DELIBERATELY (R2-044)
----------------------------------------
This gate is semi-independent of `world/world_contract.py` ON PURPOSE: a gate
that imports the thing it checks can agree with a wrong number. That is why
CAR_MARGIN and the literal `0.5 * 2.005` car half-width live here rather than
being read from the contract.

So the elevation is NOT imported from the contract either. It is re-derived here
from `docs/circuit_spec.json` -- the design document, i.e. the REQUIREMENT --
by implementing spec section "elevation" (`station_z_pvi`: tangent grades joined
by parabolic vertical curves) a second time, in `elevation_fn()`. If the built
world ever stops matching the design, this gate is on the design's side.

`--selftest` cross-checks that second implementation against
`world_contract.elevation_c` over the whole lap and FAILS on disagreement,
which is the point: two methods, required to agree, neither one trusted.

(Known and deliberately left alone: `half_width_fn()` still PREFERS the
contract's `half_width`, because the spec states the width transition rule in
prose that four of five modules already read differently once -- re-deriving it
here would encode a sixth reading. It is noted, not silently accepted.)

SUBJECT vs CONTEXT                                                 (R2, 2026-08-02)
-----------------------------------------------------------------------------
An item author's test scene deliberately lays a slab of context ground ON the
road so the item has something to stand on -- `KPUX_Ground` reaches 7.09 m into
the corridor, `XTT_Ground` 8.46 m. Those are the test rig, not the item, and the
campaign brief FORBIDS silencing the gate with an allow-list of their names.

So they are separated STRUCTURALLY, not by name-list: an item test scene puts its
item in `W_Item_<Name>` and its furniture in the `.../Standins` child collection,
which is exactly the convention `tools/item_gate.py` already selects on. Context
objects are still MEASURED and still REPORTED, under `context_findings` -- they
are just not counted as the item's violations. Nothing is silenced; it is
attributed. `--subject <collection>` states it explicitly when a scene does not
follow the convention.
"""

import argparse
import csv
import hashlib
import json
import math
import os
import re
import sys

import bpy
from mathutils import Vector
from mathutils.kdtree import KDTree

R2 = "/home/zany/f1-round2"
# Imported by path, not by package: this runs inside Blender's interpreter with
# whatever cwd the caller happened to have.
if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import provenance as _prov                                       # noqa: E402
import gate_exit                                                 # noqa: E402

# Clearances. Generous on purpose: a gate that only catches actual contact will
# pass a fence post 50 mm from the racing line, which is not "perfectionistly
# placed" by any reading.
ROAD_MARGIN = 0.50        # m beyond half_width that must also stay clear
ROAD_CLEAR_H = 4.50       # m of headroom above the surface
ROAD_ZLO = 0.50           # m below the road surface the band still tests
CAR_MARGIN = 0.60         # m around the measured car box
CAM_CLEAR_R = 1.20        # m sphere swept along the camera path

# THE CAR BOX, AND THE 0.340 m THIS FILE USED TO LOSE            (R2-071, item 78)
#
# These four numbers are the SECOND copy of the box `world_contract` publishes as
# `CAR_BODY_W_M / CAR_RIDE_HEIGHT_M / CAR_BODY_H_M / CAR_CLEARANCE_M`, and the copy
# is DELIBERATE -- see "INDEPENDENCE, KEPT DELIBERATELY" in the header. What was not
# deliberate is that it had drifted, in the one direction a second copy always drifts:
# the number nobody diffed.
#
# The car path's z band was `(-0.3, 0.992 + CAR_MARGIN)`. `0.992` is the box's
# THICKNESS (`CAR_BODY_H_M`), and it was used as though it were the box's TOP. The
# measured box (round2_inventory S2, and the contract's own head comment) is
# z 0.340 .. 1.332 above the road: it sits on 0.340 m of RIDE HEIGHT. So the top of
# the car is 1.332 m, not 0.992 m, and the band stopped
#
#       0.992 + 0.60 = 1.592 m   where the contract's swept box reaches
#       1.332 + 0.60 = 1.932 m
#
# -- 0.340 m short, over all 1743 telemetry stations. `intrusion()` returns -1e9 for
# a point outside the band, so anything hanging in that 340 mm slice directly over
# the driven line was not merely un-flagged, it never reached the distance test and
# could not appear in `closest_approach` either. That is the same failure mode as the
# road corridor's floating band (see the header), one volume along.
#
# The FLOOR stays at -0.30 m and is NOT re-derived: the contract's box would give
# 0.340 - 0.60 = -0.26 m, and -0.30 m is 40 mm deeper, i.e. it tests strictly more.
# Deeper is the safe direction here and it is stated rather than left to arithmetic.
#
# `--selftest` now diffs all four against the contract and FAILS on disagreement,
# exactly as it already does for `elevation`. R2-044 asked for the two to "be diffed
# by hand if either moves"; a hand diff that nobody schedules is not an instrument.
CAR_BODY_W_M = 2.005      # m, measured (round2_inventory S2): y -1.003 .. +1.003
CAR_RIDE_HEIGHT_M = 0.340 # m, underbody above the road
CAR_BODY_TOP_M = 1.332    # m, top of the box above the road (= ride + 0.992 thick)
CAR_ZLO = -0.30           # m below the road the band still tests (see above)

# THE FLOOR IS BOUNDED ON BOTH SIDES, AND THE RESIDUAL IS MEASURED.
#
# The band's z reference is the CENTRELINE elevation, but the road is crowned and
# the spec banks T10/T11 at 4 deg, so at the outboard edge the surface sits a
# little BELOW the centreline and a floor at exactly -0.50 m is fractionally
# above it there. Both directions are wrong in their own way:
#
#   floor too HIGH  -> the bottom slice of the road is not tested, and a low
#                      obstacle sitting on it is invisible.
#   floor too LOW   -> the corridor starts testing structure that is SUPPOSED to
#                      be buried. Measured, not hypothetical: a floor of -1.393 m
#                      (0.50 + the spec's worst-case 4 deg bank + 2 deg crown
#                      over 8.50 m) reported BR_Verge_L 7.312 m "into the road",
#                      when those 12 vertices are 0.94-6.76 m UNDER the racing
#                      surface where the verge platform passes beneath the climb
#                      out of T4. A false alarm at 7.3 m depth is exactly the
#                      kind of finding that teaches a reader to skim.
#
# Measured over a 14 700-station grid at 21 lateral offsets across the corridor,
# a floor of `elevation(s) - 0.50` lies above the true surface on 1.59 % of
# stations, by at most 0.0384 m. So the residual is: at the most banked point on
# the circuit an obstacle must be at least 38 mm tall to be seen. It is stated
# here rather than papered over, and `--selftest` FAILS if it ever exceeds
# FLOOR_SHORTFALL_MAX -- so a future circuit that banks harder forces a decision
# instead of quietly losing the bottom of its corridor.
FLOOR_SHORTFALL_MAX = 0.10
CROWN_DEG = 2.0           # crown allowance used only in the reported diagnostic

# WHAT THIS INSTRUMENT CAN ACTUALLY RESOLVE.
#
# The corridor is reconstructed here from `spec.elements` -- straights and
# circular arcs -- and tested by nearest-station lookup. That reconstruction is
# NOT bit-identical to the contract's centreline: measured over all 3,666
# stations, the gate's centreline sits up to 5.34 mm (median 2.37 mm) away from
# the contract's. That disagreement is the price of the independence, and it is
# the floor on the gate's lateral precision. It is not removable by finer
# sampling -- measured at 1.000 / 0.500 / 0.250 / 0.125 m station spacing, the
# figure does not move.
#
# Reporting a 0.4 mm intrusion from a 5.3 mm-uncertain centreline is false
# precision, and it is not hypothetical: with the corridor's z fixed, five
# `kerb_precast_unit` elements came out at 0.5001-0.5004 m against a 0.5000 m
# limit -- kerbs whose inner lip is SUPPOSED to sit on the white line, landing a
# few tenths of a millimetre on the wrong side of it.
#
# So the decision carries a stated tolerance. Anything between the limit and the
# limit + REPORT_TOL_M is NOT called a violation and IS listed, in full, under
# `within_instrument_tolerance` -- visible, attributable, and not quietly
# dropped. `--selftest` measures the centreline disagreement against the
# contract and FAILS if it ever grows past this tolerance, so the number cannot
# rot into a magic constant.
#
# For scale: this gate exists to catch a fence spanning the racing line at
# 7.106 m and a corridor built twice 0.5 m apart. 10 mm is three orders of
# magnitude below anything it is for.
REPORT_TOL_M = 0.010

DEFAULT_ALLOW = ("SURF_", "TER_Ground", "BR_Runoff", "BR_Gravel",
                 "ARCH_Paving", "ARCH_Markings", "Floor", "Turntable_", "Platform_")

# Objects whose JOB is to define the track edge. A kerb's inner lip sits on the
# white line by design, so judging it against half_width + ROAD_MARGIN would
# report all 13 of them as intrusions — which the first analytic run did.
#
# They are NOT blanket-allowed, because a kerb 3 m into the racing line is a
# real defect and blanket-allowing it is how a gate stops protecting you. They
# are held to the TRUE half-width instead of the courtesy margin: an edge object
# may sit at or outside the surface boundary, never inside it.
#
# `KPU_` is the per-item campaign's `kerb_precast_unit`: the same serrated kerb
# as `SURF_Kerb`, rebuilt as individual precast elements under the item prefix.
# It is listed HERE and deliberately NOT in DEFAULT_ALLOW — it gets the TIGHTER
# test (the true half-width, no courtesy margin), not an exemption, so an
# element that ever reaches into the racing line is still a hard failure.
EDGE_FAMILIES = ("DR_Kerb", "SURF_Kerb", "KPU_", "BR_Subbase", "BR_Verge",
                 "ARCH_PitWall", "ARCH_RetainEdge")

# GROUND. The car's swept volume is a test for OBSTACLES, not for the surface
# the car is driving on — and a racing car spends the lap running over verges,
# kerbs, runoff and the odd bit of gravel. Reporting the ground under the wheels
# as "in the car's path" is a category error: it flagged BR_Verge_L at 1.023 m
# and the honest answer is that the car is supposed to be there.
#
# Exempt from the CAR PATH only. A verge is still held to its edge threshold in
# the road corridor, and none of this exempts anything from the camera volume —
# the camera flies, so ground in its path is a genuine collision.
GROUND_FAMILIES = ("SURF_", "TER_Ground", "BR_Verge", "BR_Runoff", "BR_Gravel",
                   "BR_Trap", "BR_Stones", "BR_Subbase", "DR_Kerb", "KPU_",
                   "ARCH_Paving", "ARCH_Markings", "Floor")


# SUBJECT vs CONTEXT, structurally. Same two patterns `tools/item_gate.py`
# selects on, so one convention governs both gates: an item test scene puts the
# item in `W_Item_<Name>` and its stand-ins/furniture/cameras in a child
# collection whose name ends in Standins / Context / Cameras / Proxies / ...
#
# These are NOT an allow-list. An allow-list names objects and excuses them; this
# names a PLACE IN THE SCENE GRAPH and attributes what it finds there. Context
# objects are measured exactly as everything else is, and every metre they reach
# into a keep-out volume is printed and written to the report -- under
# `context_findings` instead of `violations`, because a slab the test rig laid on
# the road is not a defect in the item standing on it.
CONTEXT_COLL_PAT = re.compile(
    r"(standin|context|camera|ctx|proxy|helper|backdrop|ref)s?$", re.I)
CONTEXT_PAT = re.compile(
    r"(?:^|_)(?:ctx|standin|stand_in|context|proxy|placeholder|helper|"
    r"backdrop|dummy)(?:_|\d|$)", re.I)


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=False)
    p.add_argument("--selftest", action="store_true",
                   help="run the gate's own controls and exit non-zero if any "
                        "of them does not behave; touches no world file")
    p.add_argument("--subject", default=None,
                   help="collection that IS the thing under test. Everything "
                        "outside it is measured and reported as context rather "
                        "than as the subject's violations.")
    p.add_argument("--allow", default=",".join(DEFAULT_ALLOW))
    p.add_argument("--spec", default=os.path.join(R2, "docs/circuit_spec.json"))
    p.add_argument("--telemetry", default=os.path.join(R2, "telemetry/telemetry.csv"))
    p.add_argument("--sheet", default=os.path.join(R2, "docs/beat_sheet.json"))
    p.add_argument("--campath",
                   default=os.path.join(R2, "world/camera_rig_path.json"),
                   help="per-frame camera path emitted by anim/build_camera_rig.py")
    p.add_argument("--step", type=float, default=4.0,
                   help="metres between road-corridor samples")
    p.add_argument("--repeat", type=int, default=2,
                   help="measure the unchanged scene this many times and "
                        "REFUSE the verdict unless every pass agrees. A "
                        "placement number that cannot be obtained twice is "
                        "not a verdict. 1 disables the assertion, and the "
                        "report says so.")
    return p.parse_args(argv)


def road_samples(spec, step):
    """Centreline points with half-width, straight off the spec's elements."""
    out = []
    for el in spec["elements"]:
        x0, y0 = el["start_world"][0], el["start_world"][1]
        h0 = math.radians(el["heading_world_deg"])
        L, s0 = el["length_m"], el["s_start"]
        n = max(int(L / step), 1)
        R = el.get("radius_m")
        turn = el.get("turn_deg")
        for i in range(n):
            t = i * L / n
            if el["type"] == "S" or not R:
                x, y = x0 + math.cos(h0) * t, y0 + math.sin(h0) * t
            else:
                sign = 1.0 if (turn or 0) >= 0 else -1.0
                dth = sign * t / R
                h = h0 + dth
                cx = x0 - sign * R * math.sin(h0)
                cy = y0 + sign * R * math.cos(h0)
                x = cx + sign * R * math.sin(h)
                y = cy - sign * R * math.cos(h)
            out.append((s0 + t, x, y))
    return out


def half_width_fn(spec):
    """(half_width(s), where_it_came_from).

    THE FALLBACK USED TO BE SILENT, AND IT CHANGES EVERY NUMBER  (R2-2341)
    ---------------------------------------------------------------------
    This was `except Exception: pass` followed by a CONSTANT half-width off the
    spec. The two branches do not measure the same corridor: the contract's
    `half_width` runs 7.00-8.50 m per station, the fallback is a flat
    `width_m / 2`. A run that took the fallback and a run that did not produce
    different `closest_approach` figures on an unchanged world, and the report
    said nothing about which one it had been -- which is exactly the shape of
    defect #97, one function up from where anybody was looking.

    `world_contract.py` is a live file six agents share. A transient
    half-written state, a stale `__pycache__`, a `numpy` that failed to import
    -- any of them flipped this branch for one run and back for the next.

    So: the source is RETURNED, recorded in the report and printed. And a
    contract that EXISTS but will not import is a REFUSAL, not a fallback: the
    quiet substitution of a different corridor is the thing being fixed.
    """
    wc_path = os.path.join(R2, "world", "world_contract.py")
    sys.path.insert(0, os.path.join(R2, "world"))
    try:
        import world_contract as WC          # noqa
        if hasattr(WC, "half_width"):
            return WC.half_width, "world_contract.half_width"
        why = "world_contract imported but has no half_width"
    except Exception as e:                                        # noqa: BLE001
        why = "world_contract import failed: %r" % (repr(e)[:200],)
    if os.path.exists(wc_path):
        raise SystemExit(
            "REFUSING: %s exists but could not supply half_width (%s). The "
            "silent fallback to a constant spec width measures a DIFFERENT "
            "corridor and would report a different closest approach on an "
            "unchanged world -- see R2-2341. Fix the import; do not measure "
            "through it." % (wc_path, why))
    sec = spec.get("track_section", {})
    w = sec.get("width_m", 14.0)
    return (lambda s: w * 0.5,
            "spec track_section.width_m/2 = %.4f m (CONSTANT; no %s on disk)"
            % (w * 0.5, wc_path))


def elevation_fn(spec):
    """z(s) on the centreline, re-derived from the SPEC. No contract import.

    spec section "elevation" declares the vertical alignment as PVIs --
    (station, elevation, vertical-curve length) -- with the stated method
    "tangent grades joined by parabolic vertical curves". This implements that
    sentence:

        outside a curve   z = z_pvi[i] + g[i] * (s - s_pvi[i])          (tangent)
        inside curve j    z = z_j + g[j-1]*(x - L/2) + (g[j]-g[j-1])*x^2/(2L)

    where x is measured from the curve's BVC at s_j - L/2. Equal-tangent
    parabolic curve, the standard highway form.

    This is deliberately a SECOND implementation of a number `world_contract`
    also computes. `--selftest` requires the two to agree to 1e-6 m over the
    whole lap; if they ever diverge the gate says so instead of picking one.
    """
    pv = spec["elevation"]["station_z_pvi"]
    S = [float(p["s"]) for p in pv]
    Z = [float(p["z"]) for p in pv]
    L = [float(p.get("vertical_curve_len_m", 0.0)) for p in pv]
    if len(S) < 2:
        raise SystemExit("REFUSING: spec elevation has fewer than two PVIs; "
                         "the road corridor has nothing to reference.")
    G = [(Z[i + 1] - Z[i]) / (S[i + 1] - S[i]) for i in range(len(S) - 1)]
    G.append(G[-1])
    lap = float(spec["headline"]["length_m"])

    def elev(s):
        x = float(s) % lap
        seg = 0
        for i in range(len(S) - 1):
            if x >= S[i]:
                seg = i
        z = Z[seg] + G[seg] * (x - S[seg])
        for j in range(1, len(S) - 1):
            Lv = L[j]
            if Lv <= 0.0:
                continue
            a0 = S[j] - Lv * 0.5
            if a0 <= x <= S[j] + Lv * 0.5:
                xx = x - a0
                z = (Z[j] + G[j - 1] * (xx - Lv * 0.5)
                     + (G[j] - G[j - 1]) * xx * xx / (2.0 * Lv))
        return z

    return elev


def crossfall_allowance(spec, half_width_max):
    """Worst-case cross-fall from the spec: tan(max banking + crown) * half-width.

    REPORTED, NOT APPLIED. It is the upper bound on how far below the centreline
    the road surface can get, and it is printed so a reader can see how the 0.50 m
    floor compares. Using it AS the floor was tried and measured: it buys nothing
    the 38 mm residual does not already cover, and it costs a 7.3 m false alarm on
    buried verge structure. See the FLOOR comment at the top of this file.
    """
    banks = [abs(float(c.get("banking_deg") or 0.0))
             for c in spec.get("corners", [])]
    bank = max(banks) if banks else 0.0
    return math.tan(math.radians(bank + CROWN_DEG)) * half_width_max, bank


# ---------------------------------------------------------------------------
#  SUBJECT SELECTION
# ---------------------------------------------------------------------------

def _collection_meshes(coll):
    """Meshes of a collection, descending into children but NOT into one named
    like a stand-in / context / camera group."""
    out, skipped, seen, stack = [], [], set(), [coll]
    while stack:
        c = stack.pop()
        if c.name in seen:
            continue
        seen.add(c.name)
        out.extend(o for o in c.objects if o.type == "MESH")
        for ch in c.children:
            if CONTEXT_COLL_PAT.search(ch.name):
                skipped.append(ch.name)
            else:
                stack.append(ch)
    return out, skipped


def split_subject_context(scene, subject_name):
    """(subject_names, context_names, why) -- which meshes ARE the thing tested.

    THE PROBLEM THIS SOLVES. On the assembled world every mesh is the subject and
    this is a no-op. On an item test scene it is not: the scene deliberately lays
    a context ground slab across the road so the item has something to stand on,
    and the shipped gate reported that slab as a 7-8 m intrusion in every single
    item author's run. The brief forbids allow-listing it away, correctly -- an
    allow-list would also excuse a real slab dumped on the racing line.

    So the split is structural. In priority order:

      1. `--subject <collection>` -- stated by the caller, taken as given except
         that child collections named like stand-in groups are still skipped.
      2. a collection matching `W_Item_*` or `ITEM_*` -- the campaign convention.
      3. every mesh, minus anything living ONLY inside a collection named like a
         stand-in group, minus anything NAMED like a stand-in.

    Whatever is chosen is reported verbatim in the JSON and printed, so a reader
    can see the selection the numbers were produced under. A gate that quietly
    narrows its subject is R2-019 wearing a different hat.
    """
    meshes = [o for o in scene.objects if o.type == "MESH"]
    names = {o.name for o in meshes}

    if subject_name:
        c = bpy.data.collections.get(subject_name)
        if c is None:
            raise SystemExit(f"REFUSING: no collection named '{subject_name}'. "
                             f"Scene has: {sorted(x.name for x in bpy.data.collections)[:20]}")
        objs, skipped = _collection_meshes(c)
        sub = {o.name for o in objs} & names
        why = f"--subject {subject_name}"
        if skipped:
            why += f" (skipped stand-in sub-collections {skipped})"
        return sub, names - sub, why

    # THE ITEM CONVENTION IS FOR ITEM TEST SCENES, AND IT FIRED ON THE
    # ASSEMBLED WORLD.                                              (R2-2341)
    #
    # Rule 2 says "a collection matching W_Item_*/ITEM_* is the thing under
    # test, everything else is the test rig's furniture". That is true of a
    # scene an item author built. It is catastrophically false of
    # `assembly14.blend`, where the item campaign's collections have been
    # MERGED IN alongside the whole circuit. Measured, on the shipping world:
    #
    #     >> subject: 900 meshes via collection 'ITEM_spectator_crowd'
    #        (item-campaign convention); 5 item collections present, took the
    #        largest -- pass --subject to be explicit
    #
    # 900 meshes subject, **29,304 meshes context**. Everything the gate exists
    # to guard — every barrier, fence, gantry and building — was reclassified
    # as somebody's test furniture. Two consequences, both fatal:
    #
    #   * `closest_approach_m` EXCLUDES context, so on the full circuit it
    #     reported `road_corridor: "measured, nothing close"`.
    #   * findings from context go to `context_findings`, and the verdict is
    #     `PLACEMENT_CLEAN` when `violations` is empty. A fence spanning the
    #     racing line would have been a context finding and a CLEAN verdict.
    #
    # The file already knows this is the danger — "A gate that quietly narrows
    # its subject is R2-019 wearing a different hat" — and then narrowed
    # quietly, printing a hint about `--subject` and carrying on.
    #
    # The distinguishing fact is COVERAGE. In an item test scene the item is
    # most of the scene. In the assembled world it is 3 % of it. So the
    # convention applies only when the item collection is the dominant content,
    # and otherwise this falls through to rule 3 — every mesh, minus anything
    # in a stand-in/context collection — which is the correct reading of an
    # assembled world and still attributes a real item scene's furniture.
    ITEM_SCENE_MIN_COVERAGE = 0.50
    cands = [c for c in bpy.data.collections
             if re.match(r"(w_item_|item_)", c.name, re.I)
             and not CONTEXT_COLL_PAT.search(c.name)]
    if cands:
        cands.sort(key=lambda c: (-len(c.all_objects), c.name))
        c = cands[0]
        objs, skipped = _collection_meshes(c)
        sub = {o.name for o in objs} & names
        # Coverage is measured over the item collection's WHOLE TREE -- item
        # plus the stand-in children this function deliberately skips -- since
        # that tree is what an item test scene consists of. A well-formed item
        # scene scores ~100 %; the assembled world scores 3 %.
        tree = {o.name for o in c.all_objects if o.type == "MESH"} & names
        cover = (len(tree) / len(names)) if names else 0.0
        if sub and cover >= ITEM_SCENE_MIN_COVERAGE:
            why = (f"collection '{c.name}' (item-campaign convention; "
                   f"{100 * cover:.1f} % of the scene's meshes)")
            if skipped:
                why += f", skipping stand-in sub-collections {skipped}"
            if len(cands) > 1:
                why += (f"; {len(cands)} item collections present, took the "
                        f"largest -- pass --subject to be explicit")
            return sub, names - sub, why
        if sub:
            print(f">> NOT an item test scene: the largest item collection "
                  f"'{c.name}' and its children hold {len(tree)} of "
                  f"{len(names)} meshes ({100 * cover:.1f} %). The item "
                  f"convention would have made {len(names) - len(sub)} meshes "
                  f"'context' and excused them from the verdict. Measuring the "
                  f"WHOLE scene instead; pass --subject if you really meant to "
                  f"narrow it.")

    ctx = set()
    for c in bpy.data.collections:
        if CONTEXT_COLL_PAT.search(c.name):
            ctx |= {o.name for o in c.all_objects if o.type == "MESH"}
    # An object that ALSO lives in a non-context collection is not context.
    for o in meshes:
        if o.name in ctx and any(not CONTEXT_COLL_PAT.search(uc.name)
                                 for uc in o.users_collection):
            ctx.discard(o.name)
    ctx |= {o.name for o in meshes if CONTEXT_PAT.search(o.name)}
    ctx &= names
    if ctx:
        return (names - ctx, ctx,
                f"every mesh MINUS {len(ctx)} in a stand-in/context collection "
                f"or named like one (no W_Item_* collection in this scene)")
    return names, set(), "every mesh in the scene (nothing looks like context)"


def station_tree(points):
    kd = KDTree(len(points))
    for i, p in enumerate(points):
        kd.insert((p[0], p[1], 0.0), i)
    kd.balance()
    return kd


def bbox_world(oe):
    """Evaluated world-space AABB, without converting to a mesh."""
    mw = oe.matrix_world
    cs = [mw @ Vector(c) for c in oe.bound_box]
    return (Vector((min(c.x for c in cs), min(c.y for c in cs),
                    min(c.z for c in cs))),
            Vector((max(c.x for c in cs), max(c.y for c in cs),
                    max(c.z for c in cs))))


def intrusion(vol, p):
    """How far INSIDE this keep-out volume is world point p, in metres.

    Negative means outside. This is the whole gate: an exact signed distance,
    not a triangle count.
    """
    _co, idx, _d = vol["kd"].find((p.x, p.y, 0.0))
    sx, sy, sz = vol["pts"][idx]
    if vol.get("sphere"):
        return vol["radius"][idx] - (p - Vector((sx, sy, sz))).length
    if vol.get("zband"):
        lo, hi = vol["zband"]
        if p.z < sz + lo or p.z > sz + hi:
            return -1e9
    else:
        if p.z < vol["zlo"] or p.z > vol["zhi"]:
            return -1e9
    return vol["radius"][idx] - math.hypot(p.x - sx, p.y - sy)


def build_volumes(a, spec, verbose=True):
    """The three keep-out volumes. Shared by the gate and by --selftest, so the
    controls exercise the volume the gate actually uses rather than a copy."""
    #
    # Two rewrites got here. The first was nested Python loops over
    # samples x objects x vertices; on the real assembled world -- 28,686
    # objects, 3.97 GB -- it read the blend and then never emitted a result.
    #
    # The second built each keep-out region as a mesh of per-station boxes and
    # used BVHTree.overlap(). That ran, but the boxes were AXIS-ALIGNED while
    # the track curves, so on any corner a box whose half-width is 8.0 m reaches
    # 8.0 * sqrt(2) = 11.3 m corner-to-corner. Everything sitting in that
    # 3.3 m diagonal skirt -- the pit wall, every gravel trap, the barrier
    # sub-base, 13 kerbs -- was reported as being ON THE ROAD.
    #
    # It was measurably wrong in the way that matters most: ranking by triangle
    # count put ARCH_PitWall first at 15,165 pairs (it measures 3.279 m OUTSIDE
    # the surface, i.e. perfectly placed) and buried BR_FenceStruct_L03 at
    # seventh (it reaches 7.106 m INTO a 7.39 m half-width -- it spans the
    # racing line). A gate that ranks the most-correct object above a fence
    # across the track is worse than no gate; it trains the reader to skim.
    #
    # There is no reason to approximate a corridor with polygons at all. The
    # corridor IS an analytic shape: nearest centreline station, lateral offset,
    # height band. Testing it directly is exact, has no diagonal skirt, cannot
    # miss an object floating in the interior (which a hollow swept prism would),
    # and reports a PHYSICAL DEPTH IN METRES instead of a triangle count --
    # so a finding says "move this 1.4 m outboard" rather than "these meshes
    # touch, good luck".
    #
    # Cost is controlled by rejecting on the evaluated bounding box first, which
    # needs no mesh conversion, so only the handful of objects actually near a
    # keep-out volume pay for a per-vertex scan.

    hw, hw_src = half_width_fn(spec)
    elev = elevation_fn(spec)
    volumes = {}

    # ROAD CORRIDOR. Sampled every metre: the lookup is a KD-tree query, so a
    # dense centreline costs nothing at test time and removes the discretisation
    # error a 4 m spacing would leave on a tight hairpin.
    #
    # THE Z BAND IS PER STATION. Each sample carries its own road elevation and
    # the band is `zband`-relative to it, exactly as `car_path` has always been
    # relative to the telemetry's own z. Pinning the stations at z = 0.0 and
    # using an absolute -0.5 .. +4.5 m band tested empty air over 28 % of a lap
    # that climbs 11.6 m; see the header.
    road = road_samples(spec, 1.0)
    hw_max = max(hw(s) for (s, _x, _y) in road) + ROAD_MARGIN
    xfall, bank_deg = crossfall_allowance(spec, hw_max)
    zlo = -ROAD_ZLO
    zs = [elev(s) for (s, _x, _y) in road]
    volumes["road_corridor"] = {
        "kd": station_tree([(x, y) for (_s, x, y) in road],),
        "radius": [hw(s) + ROAD_MARGIN for (s, _x, _y) in road],
        "zlo": None, "zhi": None,
        "zband": (zlo, ROAD_CLEAR_H),
        "s": [s for (s, _x, _y) in road],
        "pts": [(x, y, z) for (_s, x, y), z in zip(road, zs)]}
    _r = volumes["road_corridor"]["radius"]
    if verbose:
        print(f">> road corridor: {len(road)} stations, "
              f"half-width {min(_r):.2f}-{max(_r):.2f} m (per-station, analytic)")
        print(f">> road corridor z band: GROUND-REFERENCED, "
              f"elevation(s) {min(zs):+.3f}..{max(zs):+.3f} m, "
              f"band {zlo:+.3f} .. {ROAD_CLEAR_H:+.3f} m about it")
        print(f">> road corridor half-width came from: {hw_src}")
        print(f">> spec worst-case cross-fall {xfall:.3f} m "
              f"(banking {bank_deg:.0f} deg + {CROWN_DEG:.0f} deg crown over "
              f"{hw_max:.2f} m) -- reported, NOT added to the floor; measured "
              f"residual is 38 mm on 1.6 % of stations, see --selftest")
    volumes["road_corridor"]["_meta"] = {
        "elevation_min_m": round(min(zs), 4), "elevation_max_m": round(max(zs), 4),
        "zband": [round(zlo, 4), ROAD_CLEAR_H],
        "spec_worst_crossfall_m": round(xfall, 4),
        "spec_max_banking_deg": bank_deg,
        # WHICH half_width DID THIS RUN ACTUALLY USE? Two runs on either side
        # of the (formerly silent) contract-import fallback measured corridors
        # 7.00-8.50 m and a flat constant wide, and nothing in the report said
        # so. It is a number the answer depends on, so it is in the body.
        "half_width_source": hw_src,
        "half_width_min_m": round(min(hw(s) for (s, _x, _y) in road), 6),
        "half_width_max_m": round(max(hw(s) for (s, _x, _y) in road), 6),
        "reference": "per-station centreline elevation re-derived from "
                     "circuit_spec.json elevation.station_z_pvi"}

    if os.path.exists(a.telemetry):
        with open(a.telemetry) as f:
            tel = list(csv.DictReader(f))
        pts = [(float(r["x"]), float(r["y"]), float(r["z"])) for r in tel]
        r = 0.5 * CAR_BODY_W_M + CAR_MARGIN
        czhi = CAR_BODY_TOP_M + CAR_MARGIN
        volumes["car_path"] = {
            "kd": station_tree([(p[0], p[1]) for p in pts]),
            "radius": [r] * len(pts), "s": list(range(len(pts))),
            "pts": pts, "zlo": None, "zhi": None,
            "zband": (CAR_ZLO, czhi)}
        if verbose:
            print(f">> car path: {len(pts)} stations, half-width {r:.2f} m, "
                  f"band {CAR_ZLO:+.3f} .. {czhi:+.3f} m about the telemetry z "
                  f"(car box 0.340..{CAR_BODY_TOP_M:.3f} + {CAR_MARGIN:.2f} m)")

    # THE CAMERA VOLUME. Preference order, and the reason for it:
    #
    #   1. the PER-FRAME path the rig build emits (`camera_rig_path.json`). The
    #      camera flies BETWEEN its keys, and a key-only sweep tests 0.2 % of
    #      the frames it is airborne for. This is the artefact, sampled where it
    #      actually is.
    #   2. every beat's keys from the sheet. Note "every": this file used to
    #      read beat1 + beat6 by name, which is the same bug that lost four
    #      beats' worth of camera in the first place.
    #
    # Falling back is announced loudly. A gate that quietly measures a weaker
    # thing than it claims is R2-019, and it happened here once already.
    keys = []
    src = None
    if a.campath and os.path.exists(a.campath):
        pj = json.load(open(a.campath))
        keys = [e["p"] for e in pj["path"]]
        src = f"per-frame path, {len(keys)} frames, from {a.campath}"
    if os.path.exists(a.sheet):
        sheet = json.load(open(a.sheet))
        skeys = []
        for b in sheet.get("beats", []):
            blk = sheet.get("beat" + b["name"].split("_")[0], {})
            for k in (blk.get("camera_keys") or blk.get("keys") or []):
                skeys.append(k["world"])
        dp = sheet.get("doppler", {}).get("camera_world")
        if dp:
            skeys.append(dp)
        if not keys:
            keys = skeys
            src = (f"KEYS ONLY, {len(keys)} of them -- NO per-frame path at "
                   f"{a.campath}. The camera is airborne for 2,978 frames and "
                   f"this sweeps the handful it is keyed on; run "
                   f"anim/build_camera_rig.py first to emit the path.")
        else:
            keys += skeys
        if keys:
            volumes["camera_path"] = {
                "kd": station_tree([(k[0], k[1]) for k in keys]),
                "radius": [CAM_CLEAR_R] * len(keys), "s": list(range(len(keys))),
                "pts": [tuple(k) for k in keys], "zlo": None, "zhi": None,
                "sphere": True}
            if verbose:
                print(f">> camera path: {src}; sphere r={CAM_CLEAR_R} m over "
                      f"{len(keys)} sample points")

    return volumes


# ---------------------------------------------------------------------------
#  THE REPORT MUST NOT DEPEND ON THE ORDER THE SCENE HAPPENS TO BE WALKED IN
# ---------------------------------------------------------------------------
#
# `closest_approach` was decided by a strict `>` over `scene.objects`:
#
#     if d > closest.get(vname, (-1e9,))[0]:
#         closest[vname] = (d, ob.name, at)
#
# On an EXACT TIE -- and this world is built from repeated modules laid on a
# regular station grid, so exact ties are the normal case, not a curiosity --
# the winner is whichever object the scene walk reached first. Scene order is
# not part of the world: it moves when an object is added, removed, renamed,
# relinked, or the file is re-saved by a different tool. So the number that
# `placement_gate` adjudicates on could change identity with no world change,
# and no reader could tell that from a regression.
#
# Depth first, then NAME. Nothing else. Two runs of the same world now have to
# agree, and if they do not, something real moved.                  (R2-2341)

def _better(d, tag, cur):
    """Is (d, tag) a stronger claim than `cur = (d, tag, ...)`? Total order."""
    if cur is None:
        return True
    if d != cur[0]:
        return d > cur[0]
    return tag < cur[1]


def measure(scene, volumes, allow, context_names=frozenset(), verbose=True):
    """Every mesh against every volume. Returns (violations, context_findings,
    marginal, closest, tested, coarse_rejected, diag).

    `context_names` are measured identically; their findings are routed to a
    separate list so the report can attribute them without excusing them.

    `diag` carries everything that used to be thrown away silently -- the
    objects that could not be measured, the runner-up behind every closest
    approach, and the order the scene was walked in. All three change the
    answer, and all three used to be invisible.
    """
    # THE DEPSGRAPH IS EVALUATED BEFORE IT IS READ.
    # `ob.evaluated_get(deps)` on a depsgraph that has not been evaluated hands
    # back geometry and matrices from whatever state the file was saved in.
    # This costs one call and removes a whole family of "it read differently
    # that time" from the list of things this report can be accused of.
    bpy.context.view_layer.update()
    deps = bpy.context.evaluated_depsgraph_get()
    violations = []
    ctx_findings = []
    marginal = []
    closest = {}
    runner_up = {}
    tested = coarse_rejected = 0
    diag = {"skipped_bbox": [], "skipped_to_mesh": [], "skipped_empty_mesh": [],
            "scene_walk_order_sha256": None}
    max_r = max(max(v["radius"]) for v in volumes.values())

    walk = [ob for ob in scene.objects]
    diag["scene_walk_order_sha256"] = hashlib.sha256(
        "\n".join(o.name for o in walk).encode()).hexdigest()

    for ob in walk:
        if ob.type != "MESH" or ob.name.startswith(allow):
            continue
        oe = ob.evaluated_get(deps)
        try:
            lo, hi = bbox_world(oe)
        except Exception as e:                                    # noqa: BLE001
            # A SKIP IS NOT A PASS. This was a bare `continue`: an object that
            # could not be bounded silently left the survey, and on a box under
            # memory pressure that is a run-to-run difference with no record.
            diag["skipped_bbox"].append({"object": ob.name,
                                         "why": repr(e)[:200]})
            continue
        tested += 1

        # COARSE REJECT on the evaluated bounding box. No mesh conversion, so
        # the ~28,000 objects nowhere near a keep-out volume cost one KD query
        # each instead of a full per-vertex scan.
        centre = (lo + hi) * 0.5
        reach = (hi - lo).length * 0.5 + max_r
        near = {}
        for vname, vol in volumes.items():
            if vol["kd"].find_range((centre.x, centre.y, 0.0), reach):
                near[vname] = vol
        if not near:
            coarse_rejected += 1
            continue

        try:
            me = oe.to_mesh()
        except Exception as e:                                    # noqa: BLE001
            diag["skipped_to_mesh"].append({"object": ob.name,
                                            "why": repr(e)[:200]})
            continue
        if me is None or not me.polygons:
            diag["skipped_empty_mesh"].append(ob.name)
            continue
        # THE EVALUATED MATRIX, not the original's.
        # The coarse reject above bounds `oe` -- the EVALUATED object -- and
        # then the per-vertex loop used to transform by `ob.matrix_world`, the
        # ORIGINAL's cached matrix. For anything parented, constrained or
        # driven the two differ, so the gate selected an object by where the
        # depsgraph says it is and then measured it where the file was saved.
        # One object, two positions, and which one you got depended on whether
        # the depsgraph had been evaluated.                        (R2-2341)
        mw = oe.matrix_world
        worst = {}
        for v in me.vertices:
            p = mw @ v.co
            at = (round(p.x, 3), round(p.y, 3), round(p.z, 3))
            for vname, vol in near.items():
                d = intrusion(vol, p)
                # Ties between two VERTICES of one object move `at_world`, and
                # a reader chases a coordinate. Broken on the point itself.
                if _better(d, at, worst.get(vname)):
                    worst[vname] = (d, at)
        oe.to_mesh_clear()

        # An edge-defining object is measured against the true surface boundary;
        # everything else must also respect the courtesy margin.
        #
        # THE COURTESY BELONGS TO THE ROAD CORRIDOR AND NOWHERE ELSE. (R2-2341)
        # `limit` was per-OBJECT, so an EDGE_FAMILIES name bought 0.50 m of
        # exemption in ALL THREE volumes. The justification for it is entirely
        # about the corridor's radius: the corridor is inflated by ROAD_MARGIN,
        # and a kerb whose inner lip sits on the white line is 0.50 m inside
        # THAT inflated shape while being exactly on the true boundary. Neither
        # of the other two volumes is inflated by ROAD_MARGIN -- `car_path` is
        # half the car plus CAR_MARGIN, `camera_path` is a CAM_CLEAR_R sphere --
        # so the same 0.50 m there is not a courtesy, it is 0.50 m of the car's
        # swept volume and of the camera's clearance, given away by a name.
        #
        # It was not hypothetical. `docs/placement_after_46.json` reports
        #
        #     total: 0        (i.e. PLACEMENT_CLEAN)
        #     closest_approach_m.car_path: ARCH_RetainEdge, clearance -0.1553 m
        #
        # -- a clean verdict whose own headline number says something is 155 mm
        # INSIDE the driven path. The two halves of that report contradict each
        # other and the contradiction is this line.
        is_edge = ob.name.startswith(EDGE_FAMILIES)
        is_ground = ob.name.startswith(GROUND_FAMILIES)
        is_ctx = ob.name in context_names
        for vname, (d, at) in worst.items():
            limit = ROAD_MARGIN if (is_edge and vname == "road_corridor") else 0.0
            if vname == "car_path" and is_ground:
                continue                      # the car drives ON the ground
            # CLEAREST APPROACH, even when nothing is violated. "CLEAN" with
            # 0.02 m to spare and "CLEAN" with 8 m to spare are different
            # answers, and only one of them survives somebody nudging an object.
            #
            # Context furniture is EXCLUDED from closest-approach: a test rig's
            # slab lying across the road would otherwise own this figure and
            # hide how close the item itself gets, which is the number the
            # author has to act on. It is reported in full under
            # `context_findings`, not dropped.
            #
            # THE RUNNER-UP IS KEPT. "ARCH_Gantry, 1.1491 m" and "ARCH_Gantry
            # 1.1491 m with BR_Concrete_L12 tied to the last decimal behind it"
            # are different answers: the second one says the name in this field
            # is a coin toss. A report that cannot show its own margin cannot
            # be told apart from one that is flipping.
            if not is_ctx:
                if _better(d, ob.name, closest.get(vname)):
                    if vname in closest:
                        runner_up[vname] = closest[vname]
                    closest[vname] = (d, ob.name, at)
                elif _better(d, ob.name, runner_up.get(vname)):
                    runner_up[vname] = (d, ob.name, at)
            if d > limit:
                rec = {"object": ob.name, "volume": vname,
                       "intrusion_m": round(d, 4), "at_world": at,
                       "edge_family": limit > 0.0}
                if d <= limit + REPORT_TOL_M:
                    # Past the limit, but by less than this instrument can
                    # tell apart from zero. Listed, never silently dropped.
                    rec["past_limit_mm"] = round((d - limit) * 1000.0, 3)
                    marginal.append(rec)
                else:
                    (ctx_findings if is_ctx else violations).append(rec)

    diag["runner_up"] = runner_up
    n_skip = (len(diag["skipped_bbox"]) + len(diag["skipped_to_mesh"])
              + len(diag["skipped_empty_mesh"]))
    if verbose:
        print(f">> tested {tested} objects; {coarse_rejected} rejected on "
              f"bounding box; {tested - coarse_rejected} measured per-vertex")
        if n_skip:
            print(f">> {n_skip} object(s) COULD NOT BE MEASURED and were left "
                  f"out of every number above -- listed in the report under "
                  f"determinism.skipped: "
                  f"bbox={len(diag['skipped_bbox'])} "
                  f"to_mesh={len(diag['skipped_to_mesh'])} "
                  f"empty={len(diag['skipped_empty_mesh'])}")
    return (violations, ctx_findings, marginal, closest, tested,
            coarse_rejected, diag)


def main():
    a = parse_args()
    if a.selftest:
        return selftest(a)
    if not a.out:
        raise SystemExit("REFUSING: --out is required (or pass --selftest).")
    allow = tuple(x.strip() for x in a.allow.split(",") if x.strip())
    spec = json.load(open(a.spec))
    volumes = build_volumes(a, spec)

    scene = bpy.context.scene
    subject, context, why = split_subject_context(scene, a.subject)
    print(f">> subject: {len(subject)} meshes via {why}")
    if context:
        print(f">> context: {len(context)} meshes are the scene's own furniture, "
              f"not the thing under test: {sorted(context)[:12]}"
              f"{' ...' if len(context) > 12 else ''}")
        print(">> they are still measured; anything they reach is reported "
              "under context_findings, NOT excused")

    # ---- THE REPORT ASSERTS ITS OWN REPRODUCIBILITY --------------------
    #
    # `--repeat N` measures the same unchanged scene N times in this process
    # and requires the N results to be IDENTICAL. It is deliberately not a
    # human's promise in a staging note: a placement verdict that cannot be
    # obtained twice is not a verdict, and this is the one place that can say
    # so at the moment the number is produced.
    #
    # It does not cover everything a second PROCESS would (the scene walk
    # order, the blend load) -- so the walk order is hashed into the report as
    # well, and two reports of the same world can be diffed on it by
    # tools/report_repro.py. What it does cover is every lazily-evaluated
    # thing: the depsgraph, modifier evaluation, and any state the first pass
    # leaves behind for the second.
    passes = []
    for _i in range(max(1, a.repeat)):
        passes.append(measure(scene, volumes, allow, context,
                              verbose=(_i == 0)))
    violations, ctx_findings, marginal, closest, tested, coarse, diag = passes[0]

    def _fingerprint(p):
        v, c, m, cl, t, cr, dg = p
        return json.dumps(
            {"violations": sorted(v, key=lambda r: (r["volume"], r["object"],
                                                    r["intrusion_m"])),
             "context": sorted(c, key=lambda r: (r["volume"], r["object"],
                                                 r["intrusion_m"])),
             "marginal": sorted(m, key=lambda r: (r["volume"], r["object"],
                                                  r["intrusion_m"])),
             "closest": {k: [cl[k][0], cl[k][1], cl[k][2]] for k in sorted(cl)},
             "tested": t, "coarse": cr,
             "walk": dg["scene_walk_order_sha256"],
             "skipped": [len(dg["skipped_bbox"]), len(dg["skipped_to_mesh"]),
                         len(dg["skipped_empty_mesh"])]},
            sort_keys=True, separators=(",", ":"))

    fps = [_fingerprint(p) for p in passes]
    repeat_ok = len(set(fps)) == 1
    # ONE PASS IS NOT AGREEMENT. `len({x}) == 1` is trivially true, and calling
    # that "IDENTICAL" would be a metric that reads the same whether it was
    # tested or not -- the commonest defect shape in this log. `--repeat 1`
    # says NOT_ASSERTED, in the body, where a diff can see it.
    determinism = {
        "repeats": len(passes),
        "repeat_measure": ("NOT_ASSERTED (--repeat 1: this report makes no "
                           "claim about its own reproducibility)"
                           if len(passes) < 2 else
                           "IDENTICAL" if repeat_ok else "DIFFERED"),
        "repeat_fingerprint_sha256": [
            hashlib.sha256(f.encode()).hexdigest()[:16] for f in fps],
        "scene_walk_order_sha256": diag["scene_walk_order_sha256"],
        "skipped": {"bbox": diag["skipped_bbox"][:50],
                    "to_mesh": diag["skipped_to_mesh"][:50],
                    "empty_mesh": diag["skipped_empty_mesh"][:50],
                    "total": (len(diag["skipped_bbox"])
                              + len(diag["skipped_to_mesh"])
                              + len(diag["skipped_empty_mesh"]))},
        # THE MARGIN BEHIND EVERY REPORTED WINNER. Zero means the name in
        # `closest_approach_m` is decided by the tie-break, not by the world.
        "closest_approach_margin": {},
    }
    for k in sorted(volumes):
        c, r = closest.get(k), diag["runner_up"].get(k)
        if not c:
            continue
        row = {"winner": c[1], "intrusion_m": round(c[0], 6),
               "runner_up": r[1] if r else None,
               "runner_up_intrusion_m": round(r[0], 6) if r else None,
               "margin_m": round(c[0] - r[0], 9) if r else None}
        if r and c[0] == r[0]:
            row["note"] = ("EXACT TIE -- the object named here is chosen by "
                           "the deterministic tie-break (lowest name), not by "
                           "the geometry. Both are equally the closest.")
        determinism["closest_approach_margin"][k] = row
    if not repeat_ok:
        print(">> THE SAME UNCHANGED SCENE MEASURED DIFFERENTLY ON REPEAT:")
        for i, f in enumerate(fps):
            print("     pass %d  %s" % (i, hashlib.sha256(
                f.encode()).hexdigest()[:16]))

    # ---- report ----------------------------------------------------------
    # Ranked by DEPTH, so the worst physical error is the first line read.
    worst = sorted(violations, key=lambda v: -v["intrusion_m"])
    ctx_worst = sorted(ctx_findings, key=lambda v: -v["intrusion_m"])
    marg = sorted(marginal, key=lambda v: -v["intrusion_m"])

    # ---- WHAT THIS REPORT MEASURED -------------------------------------
    # A placement report once changed on an UNCHANGED blend: `ARCH_RetainEdge
    # +0.359 m` became `BR_Concrete_L12 +4.608 m` with no world change at all.
    # Telemetry and the camera path had been rebuilt underneath it, and nothing
    # in the report recorded either. Two runs that disagree could not be told
    # apart from a regression.
    #
    # THE KEEP-OUT VOLUMES ARE BUILT FROM `--spec`, `--telemetry`, `--sheet`
    # AND `--campath`, NOT FROM THE BLEND. So all four are inputs in exactly
    # the sense that matters, and under-declaring them here is the entire
    # defect. See tools/provenance.py.
    _stamp = _prov.stamp(
        tool_file=__file__,
        tool_version="placement_gate; spec %s" % (spec.get("version")
                                                  or spec.get("revision")
                                                  or "unversioned"),
        inputs=[("blend", bpy.data.filepath or None),
                ("spec", a.spec),
                ("telemetry", a.telemetry),
                ("beat_sheet", a.sheet),
                ("camera_path", a.campath)],
    )

    json.dump({_prov.STAMP_KEY: _stamp,
               "violations": worst, "total": len(worst),
               "context_findings": ctx_worst,
               "context_total": len(ctx_worst),
               "within_instrument_tolerance": marg,
               "within_instrument_tolerance_total": len(marg),
               "instrument_tolerance_m": REPORT_TOL_M,
               "subject_selection": {"why": why, "subject_meshes": len(subject),
                                     "context_meshes": len(context),
                                     "context_objects": sorted(context)[:200]},
               # EVERY volume gets a row, including the ones nothing came near.
               # An absent key and "measured, nothing close" look identical to a
               # reader and to a diff, and that equivalence is exactly what let
               # probeG's z-fight scan switch itself off unnoticed.
               "closest_approach_m": {
                   k: ({"object": closest[k][1],
                        "clearance_m": round(-closest[k][0], 4),
                        "at_world": closest[k][2]} if k in closest else
                       {"object": None, "clearance_m": None, "at_world": None,
                        "note": "no subject mesh came within bounding-box reach "
                                "of this volume -- measured, nothing close"})
                   for k in volumes},
               "method": "analytic signed distance to keep-out volume",
               "determinism": determinism,
               "road_corridor": volumes["road_corridor"]["_meta"],
               # EVERY CONSTANT THE ANSWER DEPENDS ON, IN THE BODY.
               # `car_zlo` and `car_top` were not here, and they are two of the
               # three numbers that define the car volume: the 340 mm band
               # error of #78 moved `closest_approach` and left no trace in any
               # report it moved. A diff of two report bodies now sees it.
               "clearances": {"road_margin": ROAD_MARGIN, "road_h": ROAD_CLEAR_H,
                              "road_zlo": volumes["road_corridor"]["zband"][0],
                              "car_margin": CAR_MARGIN, "cam_r": CAM_CLEAR_R,
                              "car_zlo": CAR_ZLO, "car_body_top": CAR_BODY_TOP_M,
                              "car_body_w": CAR_BODY_W_M,
                              "car_swept_half_w": 0.5 * CAR_BODY_W_M + CAR_MARGIN,
                              "car_band_top": CAR_BODY_TOP_M + CAR_MARGIN}},
              open(a.out, "w"), indent=1)

    for vname in sorted(volumes):
        c = closest.get(vname)
        if c:
            mg = determinism["closest_approach_margin"].get(vname) or {}
            tail = ""
            if mg.get("margin_m") == 0.0:
                tail = ("   EXACT TIE with %s -- the name is the tie-break, "
                        "not the geometry" % mg.get("runner_up"))
            elif mg.get("margin_m") is not None:
                tail = "   (%s %.4f m behind)" % (mg.get("runner_up"),
                                                  mg["margin_m"])
            print(f">> closest approach, {vname:<14} {c[1]:<26} "
                  f"{-c[0]:+8.3f} m of clearance   at {c[2]}{tail}")
        else:
            print(f">> closest approach, {vname:<14} "
                  f"{'(nothing came near it)':<26}   measured, nothing close")
    sk = determinism["skipped"]["total"]
    print(f">> determinism: {determinism['repeats']} pass(es), "
          f"{determinism['repeat_measure']}; scene walk "
          f"{determinism['scene_walk_order_sha256'][:16]}; "
          f"{sk} object(s) unmeasurable")
    if determinism["repeats"] < 2:
        print(">> NOTE: --repeat 1 -- this report makes NO claim about its own "
              "reproducibility. It is a number, not a verdict.")
    if ctx_worst:
        print(f">> {len(ctx_worst)} CONTEXT findings -- the scene's own test rig, "
              f"attributed rather than excused:")
        for v in ctx_worst[:12]:
            print(f"     [context] {v['volume']:<15} {v['object']:<28} "
                  f"{v['intrusion_m']:>8.3f} m in")
    if marg:
        print(f">> {len(marg)} past the limit by less than the "
              f"{REPORT_TOL_M * 1000:.0f} mm this method can resolve "
              f"(centreline reconstruction differs from the contract's by up "
              f"to 5.3 mm) -- listed, not counted:")
        for v in marg[:12]:
            print(f"     [within tol] {v['volume']:<15} {v['object']:<28} "
                  f"{v['past_limit_mm']:>8.3f} mm past the limit")
    ctx_tag = (f"  [+{len(ctx_worst)} context findings]" if ctx_worst else "")

    # A GATE THAT MEASURED NOTHING HAS NOT PASSED.
    #
    # `tested` is the count of subject meshes actually put through `measure()`.
    # On an empty scene, or one whose every mesh matched `--allow`, the loops
    # above run zero times, `worst` is empty, and the gate printed
    # PLACEMENT_CLEAN — the same shape of hole collision_gate and depth_probe
    # were fixed for. It is VACUOUS, not clean.
    if not tested:
        print(">> REFUSING TO REPORT: no subject mesh was measured against any "
              "keep-out volume (empty scene, or everything matched --allow "
              f"{allow!r}).")
        print(">> Nothing here for this gate to test. That is NOT a pass.")
        return gate_exit.verdict("PLACEMENT_VACUOUS")

    # AN IRREPRODUCIBLE MEASUREMENT IS NOT A VERDICT.               (R2-2341)
    #
    # This comes BEFORE clean/fail on purpose. If the same unchanged scene
    # measured two different ways in one process, then neither the CLEAN nor
    # the FAIL below is attributable to the world, and printing either of them
    # is worse than printing nothing -- a CLEAN would be quoted, and a FAIL
    # would send somebody to move an object that was never in the way. It is
    # its own verdict so a caller can tell it apart from a dirty world.
    if not repeat_ok:
        print(">> REFUSING TO REPORT: the same unchanged scene measured "
              "differently on repeat, in one process, with nothing touched "
              "between passes. Every number above is unciteable.")
        # The token carries "REFUSED" so `gate_exit` maps it to VACUOUS (3) --
        # "the gate ran, refused, and said why" -- rather than to CRASH. It is
        # deliberately NOT spelled as a FAIL: the world may be perfectly clean,
        # and sending somebody to move an object on the strength of a number
        # the tool cannot obtain twice is the second-worst outcome here.
        return gate_exit.verdict("PLACEMENT_NONDETERMINISTIC_REFUSED")

    if not worst:
        print(">> NOTHING is on the road, in the car's path, or in the camera's path")
        return gate_exit.verdict("PLACEMENT_CLEAN", ctx_tag)
    print(f">> {len(worst)} PLACEMENT VIOLATIONS (ranked by intrusion depth)")
    for v in worst[:30]:
        print(f"     {v['volume']:<15} {v['object']:<34} "
              f"{v['intrusion_m']:>8.3f} m in   at {v['at_world']}")
    return gate_exit.verdict("PLACEMENT_FAIL", ctx_tag)


# ===========================================================================
#  SELFTEST -- the controls that would have caught the corridor defect
# ===========================================================================
#
# The absolute-z corridor survived because NOTHING EVER MADE IT FIRE. There was
# a negative control (a cube 3 km off the circuit, correctly silent) and a
# positive control that only ever exercised `car_path`. `ctl_place_pos.json`
# shows it: one violation, volume `car_path`, and the road corridor silent on a
# cube standing on the racing line.
#
# So the controls below are per-VOLUME and per-FAILURE-MODE, and they are bounded
# on BOTH sides -- an object above the headroom and an object buried under the
# road must both stay silent, or the fix has merely traded a false negative for
# a false positive. None of them depends on any other module being broken: the
# faulty absolute band is reconstructed here, inline, from its own constants.

def _cube_verts(cx, cy, cz, half=1.0):
    return [Vector((cx + sx * half, cy + sy * half, cz + sz * half))
            for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]


def selftest(a):
    spec = json.load(open(a.spec))
    vols = build_volumes(a, spec, verbose=True)
    road = vols["road_corridor"]
    elev = elevation_fn(spec)
    zlo, zhi = road["zband"]
    fails = []
    rows = []

    def check(name, got, want, detail=""):
        ok = (got == want)
        rows.append({"control": name, "fires": got, "must_fire": want,
                     "detail": detail, "ok": ok})
        print(f"   {'PASS' if ok else 'FAIL'}  {name:<52} "
              f"fires={got!s:<5} expected={want!s:<5} {detail}")
        if not ok:
            fails.append(name)

    def corridor_hit(cx, cy, cz, half=1.0):
        """Max intrusion of a cube's 8 vertices -- the gate's own decision."""
        return max(intrusion(road, p) for p in _cube_verts(cx, cy, cz, half))

    def old_absolute_hit(cx, cy, cz, half=1.0):
        """The SHIPPED band, reconstructed inline: stations pinned at z = 0.0,
        absolute -0.5 .. +4.5 m. Present so the controls demonstrate the fault
        rather than assume it -- and so this file keeps a record of what the
        old gate did on each case even after nothing else remembers."""
        best = -1e9
        for p in _cube_verts(cx, cy, cz, half):
            if p.z < -0.5 or p.z > ROAD_CLEAR_H:
                continue
            _co, idx, _d = road["kd"].find((p.x, p.y, 0.0))
            sx, sy, _sz = road["pts"][idx]
            best = max(best, road["radius"][idx] - math.hypot(p.x - sx, p.y - sy))
        return best

    # station lookup: (s -> x, y) from the gate's own centreline samples
    S = road["s"]
    P = road["pts"]

    def at_station(s_target):
        i = min(range(len(S)), key=lambda i: abs(S[i] - s_target))
        return P[i][0], P[i][1], P[i][2], S[i]

    print("\n>> SELFTEST: road corridor")

    # ---- 1. THE DEMONSTRATED CASE -------------------------------------
    # s = 1798.75, the highest point on the lap (elevation +7.96 m). A 2 m cube
    # standing on the racing line here put 0 of its 8 vertices in the shipped
    # absolute band. This is the control whose ABSENCE let the defect ship.
    hx, hy, hz, hs = at_station(1798.75)
    d_new = corridor_hit(hx, hy, hz + 1.0)
    d_old = old_absolute_hit(hx, hy, hz + 1.0)
    check("HIGH POINT s=1798.75 (elev %+.3f m): 2 m cube on the racing line"
          % hz, d_new > 0, True, "intrusion %+.3f m" % d_new)
    rows[-1]["shipped_absolute_band_would_fire"] = bool(d_old > 0)
    print(f"         the shipped absolute band on this same cube: "
          f"{'FIRES' if d_old > 0 else 'DEAD (this is the defect)'}")
    if d_old > 0:
        fails.append("the reconstructed absolute band fires -- the control no "
                     "longer reproduces the fault it was written for")

    # ---- 2. THE OTHER SIDE --------------------------------------------
    # The band did not only float above the road, it also sank below it over
    # 22.44 % of the lap. Bounding one side is how 100 mm of sunken forecourt
    # went unseen for a week.
    zs = [p[2] for p in P]
    lo_i = min(range(len(zs)), key=lambda i: zs[i])
    lx, ly, lz, ls = P[lo_i][0], P[lo_i][1], P[lo_i][2], S[lo_i]
    d_new = corridor_hit(lx, ly, lz + 1.0)
    d_old = old_absolute_hit(lx, ly, lz + 1.0)
    check("LOW POINT s=%.2f (elev %+.3f m): 2 m cube on the racing line"
          % (ls, lz), d_new > 0, True, "intrusion %+.3f m" % d_new)
    rows[-1]["shipped_absolute_band_would_fire"] = bool(d_old > 0)

    # ---- 3. NO REGRESSION WHERE THE OLD BAND HAPPENED TO WORK ---------
    mx, my, mz, ms = at_station(100.0)
    d_new = corridor_hit(mx, my, mz + 1.0)
    d_old = old_absolute_hit(mx, my, mz + 1.0)
    check("FLAT s=100 (elev %+.3f m): cube the old band DID catch" % mz,
          d_new > 0, True, "intrusion %+.3f m (old band: %s)"
          % (d_new, "fired" if d_old > 0 else "dead"))
    if d_old <= 0:
        fails.append("the old band should have caught the s=100 case; the "
                     "no-regression control is not testing what it claims")

    # ---- 4/5. THE BAND IS BOUNDED, AND THE BOUNDS ARE WHERE THEY SAY --
    # A ground-referenced band must not become an infinite column: a gantry
    # soffit at 9 m is 4.5 m clear and legal, and a gate that flags it is a
    # gate nobody will keep running. Nor may the floor sink into the sub-base:
    # a floor of -1.393 m reported BR_Verge_L 7.312 m "into the road" when
    # those vertices are metres UNDER it.
    #
    # So both edges are straddled at +/- 50 mm, on the same single point, which
    # is the actual decision the per-vertex loop makes.
    for tag, dz, want in (
            ("CEILING - 50 mm (elev %+.3f)" % (ROAD_CLEAR_H - 0.05),
             ROAD_CLEAR_H - 0.05, True),
            ("CEILING + 50 mm (elev %+.3f)" % (ROAD_CLEAR_H + 0.05),
             ROAD_CLEAR_H + 0.05, False),
            ("FLOOR   + 50 mm (elev %+.3f)" % (-ROAD_ZLO + 0.05),
             -ROAD_ZLO + 0.05, True),
            ("FLOOR   - 50 mm (elev %+.3f)" % (-ROAD_ZLO - 0.05),
             -ROAD_ZLO - 0.05, False)):
        d = intrusion(road, Vector((hx, hy, hz + dz)))
        check("%s: point on the centreline" % tag, d > 0, want,
              "intrusion %+.3f m" % d)

    d = corridor_hit(hx, hy, hz - 6.0)
    check("BURIED 6 m under the road: must stay silent", d > 0, False,
          "intrusion %+.3f m" % d)

    # ---- 6. LATERAL, both sides of the boundary ------------------------
    # The corridor is half_width + ROAD_MARGIN wide; a cube centred just
    # outside that plus its own half-diagonal must be silent, and one on the
    # centreline must fire. Uses the gate's own radius so it cannot drift.
    _co, idx, _d = road["kd"].find((hx, hy, 0.0))
    R = road["radius"][idx]
    # normal direction from the centreline at this station
    j = (idx + 1) % len(P)
    tx, ty = P[j][0] - P[idx][0], P[j][1] - P[idx][1]
    tl = math.hypot(tx, ty) or 1.0
    nx, ny = -ty / tl, tx / tl
    off = R + 3.0
    d = corridor_hit(hx + nx * off, hy + ny * off, hz + 1.0)
    check("OUTSIDE the corridor laterally (%.2f m off centre): silent" % off,
          d > 0, False, "intrusion %+.3f m" % d)

    # ---- 7. NEGATIVE: 3 km off the circuit -----------------------------
    d = corridor_hit(hx + 3000.0, hy, hz + 1.0)
    check("3 km off the circuit: silent", d > 0, False,
          "intrusion %+.3f m" % d)

    # ---- 8. THE REPORTING TOLERANCE, STRADDLED ------------------------
    # REPORT_TOL_M exists because the gate cannot resolve better than its own
    # centreline reconstruction. It must not become a place for real intrusions
    # to hide, so both sides of it are tested through `measure()` -- the same
    # routing the real run uses, not a re-derivation of the rule.
    print("\n>> SELFTEST: reporting tolerance")
    scene = bpy.context.scene
    _co, idx0, _d = road["kd"].find((hx, hy, 0.0))
    for obn in list(scene.objects):
        if obn.type == "MESH":
            bpy.data.objects.remove(obn, do_unlink=True)
    for tag, past, want_viol, want_marg in (
            ("half the tolerance past the limit", REPORT_TOL_M * 0.5,
             False, True),
            ("ten times the tolerance past the limit", REPORT_TOL_M * 10.0,
             True, False)):
        for o in list(scene.objects):
            if o.type == "MESH":
                bpy.data.objects.remove(o, do_unlink=True)
        # A point whose MEASURED intrusion is exactly `past`, found by bisecting
        # the gate's own `intrusion()` rather than by trusting an algebraic
        # offset -- the nearest-station lookup is not the perpendicular, so
        # "radius minus past" is not "past metres in". A 0.1 mm cube is then
        # built there, small enough that all 8 vertices share that intrusion.
        j = (idx0 + 1) % len(P)
        tx, ty = P[j][0] - P[idx0][0], P[j][1] - P[idx0][1]
        tl = math.hypot(tx, ty) or 1.0
        nx, ny = -ty / tl, tx / tl
        lo_o, hi_o = 0.0, road["radius"][idx0] + 5.0
        for _ in range(80):
            mid = 0.5 * (lo_o + hi_o)
            dd = intrusion(road, Vector((hx + nx * mid, hy + ny * mid, hz + 1.0)))
            if dd > past:
                lo_o = mid
            else:
                hi_o = mid
        off = 0.5 * (lo_o + hi_o)
        bpy.ops.mesh.primitive_cube_add(
            size=0.0001, location=(hx + nx * off, hy + ny * off, hz + 1.0))
        bpy.context.object.name = "SELFTEST_Marginal"
        bpy.context.view_layer.update()
        v, cf, mg, cl, _t, _c, _dg = measure(scene, vols, (), set(),
                                            verbose=False)
        got_v = any(x["volume"] == "road_corridor" for x in v)
        got_m = any(x["volume"] == "road_corridor" for x in mg)
        check("%s -> counted as a violation" % tag, got_v, want_viol,
              "%s" % ([x.get("past_limit_mm") for x in mg] or ""))
        check("%s -> listed under within_instrument_tolerance" % tag,
              got_m, want_marg)
    for o in list(scene.objects):
        if o.type == "MESH":
            bpy.data.objects.remove(o, do_unlink=True)

    # ---- 8. TWO METHODS, REQUIRED TO AGREE -----------------------------
    # The spec-derived elevation vs `world_contract.elevation_c`. They are
    # independent implementations of the same design sentence; if they ever
    # disagree the gate must say so rather than pick one.
    print("\n>> SELFTEST: elevation, two independent methods")
    agree = None
    try:
        sys.path.insert(0, os.path.join(R2, "world"))
        import world_contract as WC        # noqa
        import numpy as np
        SS = np.arange(0.0, float(spec["headline"]["length_m"]), 0.25)
        mine = np.array([elev(float(s)) for s in SS])
        theirs = np.asarray(WC.elevation_c(SS), float)
        dmax = float(abs(mine - theirs).max())
        agree = dmax
        check("spec-derived elevation == world_contract.elevation_c",
              dmax < 1e-6, True, "max |d| = %.3e m over %d stations"
              % (dmax, len(SS)))
        # THE FLOOR MUST LIE UNDER THE ROAD, EVERYWHERE ACROSS ITS WIDTH.
        # Second method again: the contract's ground_z includes crown, banking
        # and micro-relief. The band floor has to be below all of it, or the
        # corridor stops testing the outboard edge of a banked corner.
        hwv = np.asarray(WC.half_width(SS), float) + ROAD_MARGIN
        low = np.full_like(SS, 1e9)
        for k in np.linspace(-1.0, 1.0, 21):
            low = np.minimum(low, np.asarray(WC.ground_z(SS, hwv * k), float))
        shortfall = (mine + zlo) - low        # >0 = floor sits ABOVE the road
        sf_max = float(shortfall.max())
        sf_frac = float((shortfall > 0).mean())
        check("band FLOOR is no more than %.0f mm above the true road surface"
              % (FLOOR_SHORTFALL_MAX * 1000),
              sf_max <= FLOOR_SHORTFALL_MAX, True,
              "worst %+.4f m on %.2f %% of stations -> an obstacle must be "
              "%.0f mm tall there to be seen" % (sf_max, 100 * sf_frac,
                                                 max(sf_max, 0.0) * 1000))
        rows[-1]["floor_shortfall_m"] = round(sf_max, 5)
        rows[-1]["floor_shortfall_station_frac"] = round(sf_frac, 5)
        gtop = np.asarray(WC.ground_z(SS, np.zeros_like(SS)), float)
        head = float((mine + ROAD_CLEAR_H - gtop).min())
        check("band CEILING gives at least 4.0 m of real headroom everywhere",
              head > 4.0, True, "tightest headroom %+.4f m" % head)

        # THE INSTRUMENT'S OWN RESOLUTION, measured rather than asserted.
        # The gate rebuilds the centreline from `spec.elements`; the contract
        # builds its own. REPORT_TOL_M is only honest if it covers how far
        # apart those two reconstructions actually are.
        gx = np.array([p[0] for p in P])
        gy = np.array([p[1] for p in P])
        _s2, u2 = WC.project(gx, gy)
        cl_err = float(np.abs(np.asarray(u2, float)).max())
        check("REPORT_TOL_M covers the two centrelines' disagreement",
              cl_err <= REPORT_TOL_M, True,
              "gate centreline is up to %.4f m (%.2f mm) off the contract's; "
              "declared tolerance %.0f mm"
              % (cl_err, cl_err * 1000, REPORT_TOL_M * 1000))
        rows[-1]["centreline_disagreement_m"] = round(cl_err, 6)
    except Exception as e:                                    # noqa: BLE001
        print("   SKIPPED: world_contract not importable (%s). The "
              "cross-check between the two methods DID NOT RUN -- that is a "
              "hole, not a pass." % e)
        fails.append("elevation cross-check did not run")

    # ---- 8b. THE PRIVATE CAR BOX vs THE CONTRACT'S    (R2-071, item 78) -----
    # The copy above is deliberate. Its DRIFT is not, and drift is the only thing
    # a second copy of a fact ever does. R2-044 recorded this pair with the
    # instruction that "the two must be diffed by hand if either moves"; the hand
    # diff never happened, and by the time it did the band top was 0.340 m low.
    #
    # So the diff runs on every selftest, on the four numbers that define the box
    # and on the two derived quantities the gate actually measures with. Note this
    # does NOT make the gate read the contract -- `build_volumes` still uses the
    # private literals. It makes disagreement LOUD instead of silent, which is the
    # only part of "semi-independent" that was missing.
    print("\n>> SELFTEST: the gate's private car box vs world_contract's")

    def car_box_rows(w, ride, top, marg):
        """The six numbers, gate side vs contract side. -> [(name, mine, theirs)]"""
        return [
            ("body width",        w,                    WC.CAR_BODY_W_M),
            ("ride height",       ride,                 WC.CAR_RIDE_HEIGHT_M),
            ("body top above road", top,
             WC.CAR_RIDE_HEIGHT_M + WC.CAR_BODY_H_M),
            ("courtesy margin",   marg,                 WC.CAR_CLEARANCE_M),
            ("swept half-width",  0.5 * w + marg,       WC.CAR_SWEPT_HALF_W_M),
            ("band TOP above road", top + marg,
             WC.CAR_RIDE_HEIGHT_M + WC.CAR_BODY_H_M + WC.CAR_CLEARANCE_M),
        ]

    def car_box_worst(rows_):
        """Largest |gate - contract| over the six, in metres."""
        return max(abs(m - t) for _n, m, t in rows_)

    try:
        import world_contract as WC        # noqa  (re-import: 8 may have failed)
        live = car_box_rows(CAR_BODY_W_M, CAR_RIDE_HEIGHT_M,
                            CAR_BODY_TOP_M, CAR_MARGIN)
        for n, mine_, theirs_ in live:
            print("   %-22s gate %9.4f   contract %9.4f   delta %+.4f m"
                  % (n, mine_, theirs_, mine_ - theirs_))
        worst = car_box_worst(live)
        check("the gate's car box agrees with world_contract's",
              worst <= 1e-9, True, "worst |delta| = %.3e m over %d quantities"
              % (worst, len(live)))
        rows[-1]["car_box_worst_delta_m"] = worst

        # The band FLOOR is deliberately NOT equal to the contract's; assert the
        # direction instead, so "deeper on purpose" cannot quietly become
        # "shallower by accident".
        contract_floor = WC.CAR_RIDE_HEIGHT_M - WC.CAR_CLEARANCE_M
        check("the band FLOOR tests at least as deep as the contract's box",
              CAR_ZLO <= contract_floor + 1e-9, True,
              "gate %+.4f m, contract-derived %+.4f m, %.0f mm deeper"
              % (CAR_ZLO, contract_floor, (contract_floor - CAR_ZLO) * 1000))

        # NEGATIVE CONTROL. The check above is only worth running if it can fail.
        # Feed it the box this file SHIPPED until item 78 -- top = 0.992 m, the
        # thickness used as the height -- and require it to say so.
        was = car_box_rows(2.005, 0.340, 0.992, 0.60)
        was_worst = car_box_worst(was)
        check("CONTROL: the same check FAILS the box this file shipped",
              was_worst > 1e-9, True,
              "worst |delta| = %.4f m (band top 1.5920 vs 1.9320) -- the "
              "shipped band stopped %.0f mm under the car's own roof"
              % (was_worst, was_worst * 1000))
        rows[-1]["shipped_car_box_worst_delta_m"] = was_worst
        if was_worst <= 1e-9:
            fails.append("the car-box control no longer reproduces the drift "
                         "it was written for -- the check cannot fail")
    except Exception as e:                                    # noqa: BLE001
        print("   SKIPPED: world_contract not importable (%s). The car-box "
              "diff DID NOT RUN -- that is a hole, not a pass." % e)
        fails.append("car box cross-check did not run")

    # ---- 9. THE SUBJECT/CONTEXT SPLIT MUST NOT SILENCE ANYTHING --------
    # Structural, so it has to be shown to be a no-op on a scene with no
    # context, and to attribute rather than drop on one that has some.
    print("\n>> SELFTEST: subject / context split")
    sub, ctx, why = split_subject_context(bpy.context.scene, None)
    check("empty/plain scene: nothing is classified as context",
          len(ctx) > 0, False, f"{len(sub)} subject, {len(ctx)} context ({why})")

    scene = bpy.context.scene
    bpy.ops.mesh.primitive_cube_add(size=2.0, location=(hx, hy, hz + 1.0))
    item = bpy.context.object
    item.name = "SELFTEST_Item"
    bpy.ops.mesh.primitive_cube_add(size=2.0, location=(lx, ly, lz + 1.0))
    rig = bpy.context.object
    rig.name = "SELFTEST_Ground"
    ic = bpy.data.collections.new("W_Item_Selftest")
    scene.collection.children.link(ic)
    sc = bpy.data.collections.new("W_Item_Selftest/Standins")
    ic.children.link(sc)
    for ob, c in ((item, ic), (rig, sc)):
        for oc in list(ob.users_collection):
            oc.objects.unlink(ob)
        c.objects.link(ob)
    bpy.context.view_layer.update()

    sub, ctx, why = split_subject_context(scene, None)
    check("item scene: the stand-in slab is classified as context",
          rig.name in ctx and item.name in sub, True,
          f"subject={sorted(sub)} context={sorted(ctx)} ({why})")

    v, cf, mg, cl, _t, _c, _dg = measure(scene, vols, (), ctx,
                                         verbose=False)
    got_item = any(x["object"] == item.name for x in v)
    got_rig_ctx = any(x["object"] == rig.name for x in cf)
    got_rig_viol = any(x["object"] == rig.name for x in v)
    check("the ITEM on the road is still a violation", got_item, True)
    check("the stand-in slab is REPORTED, under context_findings",
          got_rig_ctx, True,
          "%.3f m in" % max([x["intrusion_m"] for x in cf] or [0.0]))
    check("the stand-in slab is NOT counted as the item's violation",
          got_rig_viol, False)

    # ---- 9b. AN ITEM COLLECTION IN A BIG SCENE MUST NOT NARROW IT ----------
    # The item convention fired on `assembly14.blend` and made 29,304 of 30,204
    # meshes "context" -- see the comment in `split_subject_context`. Straddled
    # here: the SAME item collection, in a scene where it is most of the
    # content and in a scene where it is a small minority.
    print("\n>> SELFTEST: the item convention vs an assembled world")
    for o in list(scene.objects):
        if o.type == "MESH":
            bpy.data.objects.remove(o, do_unlink=True)
    for cn in ("ITEM_Selftest_Small", "ITEM_Selftest_Small/Standins"):
        if cn in bpy.data.collections:
            bpy.data.collections.remove(bpy.data.collections[cn])
    small = bpy.data.collections.new("ITEM_Selftest_Small")
    scene.collection.children.link(small)
    item_names, world_names = [], []
    for k in range(2):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(hx, hy, hz + 1 + k))
        ob = bpy.context.object
        ob.name = "SELFTEST_TheItem%d" % k
        for oc in list(ob.users_collection):
            oc.objects.unlink(ob)
        small.objects.link(ob)
        item_names.append(ob.name)
    for k in range(18):
        bpy.ops.mesh.primitive_cube_add(size=1.0,
                                        location=(hx + 4000 + k, hy, hz))
        bpy.context.object.name = "SELFTEST_WorldPiece%02d" % k
        world_names.append(bpy.context.object.name)
    bpy.context.view_layer.update()

    sub9, ctx9, why9 = split_subject_context(scene, None)
    check("an item collection holding 10 % of the scene does NOT narrow it",
          len(ctx9), 0, "%d subject / %d context -- %s"
          % (len(sub9), len(ctx9), why9))
    check("CONTROL: and every world mesh is still in the subject",
          all(n in sub9 for n in world_names), True,
          "%d of %d present" % (sum(n in sub9 for n in world_names),
                                len(world_names)))
    # THE DELIBERATE FAILURE: the shipped rule, reconstructed, DOES narrow.
    shipped_sub = {o.name for o in small.all_objects if o.type == "MESH"}
    shipped_ctx = {o.name for o in scene.objects
                   if o.type == "MESH"} - shipped_sub
    check("CONTROL: the SHIPPED rule WOULD have excused the world as context",
          len(shipped_ctx) > 0, True,
          "%d subject / %d context under the shipped rule"
          % (len(shipped_sub), len(shipped_ctx)))
    rows[-1]["shipped_rule_context_count"] = len(shipped_ctx)
    if not shipped_ctx:
        fails.append("the item-coverage control no longer reproduces the "
                     "narrowing it was written for -- it cannot fail")
    for o in list(scene.objects):
        if o.type == "MESH":
            bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.collections.remove(small)

    # ---- 10. THE REPORT MUST NOT DEPEND ON SCENE ORDER    (R2-2341, #97) ----
    #
    # #97: a `closest_approach` figure moved between two runs of an unchanged
    # world and nothing recorded why. Provenance closed the half of that which
    # was undeclared INPUT DRIFT. This is the other half: given identical
    # inputs, is the number a property of the world, or of the walk?
    #
    # The shipped rule was a strict `>` over `scene.objects`, so on an EXACT
    # TIE the winner was whoever the walk reached first. Two objects at the
    # same place is not a hypothetical on this project -- the adversarial
    # review found the Beat-4 corridor built TWICE, 0.5 m apart -- and a world
    # assembled from repeated modules on a regular station grid ties
    # constantly.
    #
    # THE CONTROL IS BOUND TO FAIL FIRST. Below, the same two tied objects are
    # put through BOTH rules on BOTH walk orders. The shipped rule is
    # reconstructed inline (same pattern as `old_absolute_hit` above) and is
    # REQUIRED to flip; if it ever stops flipping, this control has stopped
    # reproducing the fault it was written for and says so. Then the shipped
    # tie-break is required NOT to flip. A control that has only ever seen a
    # deterministic input has not been tested.
    print("\n>> SELFTEST: determinism of closest_approach")
    for o in list(scene.objects):
        if o.type == "MESH":
            bpy.data.objects.remove(o, do_unlink=True)

    def _make_tie_pair(order):
        """Two IDENTICAL cubes on the racing line, linked in `order`. Identical
        geometry at an identical transform, so their intrusions are equal to
        the last bit by construction -- no float luck involved."""
        for o in list(scene.objects):
            if o.type == "MESH":
                bpy.data.objects.remove(o, do_unlink=True)
        made = {}
        for nm in ("SELFTEST_TieA", "SELFTEST_TieB"):
            bpy.ops.mesh.primitive_cube_add(size=2.0,
                                            location=(hx, hy, hz + 1.0))
            bpy.context.object.name = nm
            made[nm] = bpy.context.object
        # Relink in the requested order: `scene.objects` follows the collection
        # link order, so this is the knob that permutes the walk.
        for nm in order:
            ob = made[nm]
            for c in list(ob.users_collection):
                c.objects.unlink(ob)
        for nm in order:
            scene.collection.objects.link(made[nm])
        bpy.context.view_layer.update()
        return made

    def _shipped_first_wins(records):
        """THE RULE THIS FILE SHIPPED, reconstructed:

            if d > closest.get(vname, (-1e9,))[0]: closest[vname] = ...

        strict `>`, so an exact tie is kept by whoever arrived first."""
        best = None
        for d, name in records:
            if best is None or d > best[0]:
                best = (d, name)
        return best[1]

    def _fixed_rule(records):
        """`_better()`: depth, then name. Independent of arrival order."""
        best = None
        for d, name in records:
            if _better(d, name, best):
                best = (d, name)
        return best[1]

    tie_res = {}
    for order in (("SELFTEST_TieA", "SELFTEST_TieB"),
                  ("SELFTEST_TieB", "SELFTEST_TieA")):
        _make_tie_pair(order)
        v2, cf2, mg2, cl2, t2, c2, dg2 = measure(scene, vols, (), set(),
                                                 verbose=False)
        walk = [o.name for o in scene.objects if o.type == "MESH"]
        # The two objects' own intrusions, in the order the gate walked them.
        recs = [(max(intrusion(road, p)
                     for p in _cube_verts(hx, hy, hz + 1.0, 1.0)), nm)
                for nm in walk]
        tie_res[order] = {
            "walk": walk,
            "walk_sha": dg2["scene_walk_order_sha256"][:16],
            "gate_winner": cl2["road_corridor"][1] if "road_corridor" in cl2
                           else None,
            "margin": (round(cl2["road_corridor"][0]
                             - dg2["runner_up"]["road_corridor"][0], 12)
                       if "road_corridor" in cl2
                       and "road_corridor" in dg2["runner_up"] else None),
            "shipped_rule_winner": _shipped_first_wins(recs),
            "fixed_rule_winner": _fixed_rule(recs),
            "tested": t2}

    fwd = tie_res[("SELFTEST_TieA", "SELFTEST_TieB")]
    rev = tie_res[("SELFTEST_TieB", "SELFTEST_TieA")]
    print("   walk order A,B -> %s   walk order B,A -> %s"
          % (fwd["walk"], rev["walk"]))

    # (a) THE CONTROL IS REAL: the permutation actually permuted the walk.
    #     Without this, everything below would pass on a scene that never
    #     changed -- which is how a control quietly becomes a decoration.
    check("CONTROL: permuting the link order really does move the scene walk",
          fwd["walk_sha"] != rev["walk_sha"], True,
          "%s vs %s" % (fwd["walk_sha"], rev["walk_sha"]))

    # (b) THE TIE IS EXACT. If it is not, (c) proves nothing.
    check("the two objects are an EXACT tie (margin 0.0 m)",
          fwd["margin"] == 0.0, True, "margin %r m" % (fwd["margin"],))

    # (c) THE DELIBERATE FAILURE: the shipped rule flips with the walk.
    check("CONTROL: the SHIPPED first-wins rule FLIPS the reported object",
          fwd["shipped_rule_winner"] != rev["shipped_rule_winner"], True,
          "%s -> %s" % (fwd["shipped_rule_winner"],
                        rev["shipped_rule_winner"]))
    rows[-1]["shipped_rule_winners"] = [fwd["shipped_rule_winner"],
                                        rev["shipped_rule_winner"]]
    if fwd["shipped_rule_winner"] == rev["shipped_rule_winner"]:
        fails.append("the scene-order control no longer reproduces the flip it "
                     "was written for -- it cannot fail, so it is not a control")

    # (d) AND THE FIX: the gate's own answer does not.
    check("the GATE's closest_approach is the same under both walk orders",
          fwd["gate_winner"] == rev["gate_winner"], True,
          "%s vs %s" % (fwd["gate_winner"], rev["gate_winner"]))
    check("the deterministic rule agrees with the gate on both orders",
          fwd["fixed_rule_winner"] == rev["fixed_rule_winner"] ==
          fwd["gate_winner"] == rev["gate_winner"], True,
          "%s / %s / %s / %s" % (fwd["fixed_rule_winner"],
                                 rev["fixed_rule_winner"],
                                 fwd["gate_winner"], rev["gate_winner"]))

    # ---- 11. AN UNMEASURABLE OBJECT MUST NOT LEAVE SILENTLY ----------------
    # `to_mesh()` and `bbox_world()` were both `except: continue`. A mesh with
    # no polygons takes the same exit, and it is the one of the three that can
    # be built on purpose -- so it is the one the control uses. Under memory
    # pressure the other two take that exit too, and an object that leaves the
    # survey without a line in the report is a difference between two runs
    # that nothing can attribute.
    print("\n>> SELFTEST: an object that cannot be measured is REPORTED")
    for o in list(scene.objects):
        if o.type == "MESH":
            bpy.data.objects.remove(o, do_unlink=True)
    bpy.ops.mesh.primitive_cube_add(size=2.0, location=(hx, hy, hz + 1.0))
    bpy.context.object.name = "SELFTEST_Solid"
    me_empty = bpy.data.meshes.new("SELFTEST_EmptyMesh")
    me_empty.from_pydata([(hx, hy, hz + 1.0), (hx + 0.1, hy, hz + 1.0)], [], [])
    me_empty.update()
    ob_empty = bpy.data.objects.new("SELFTEST_NoPolys", me_empty)
    scene.collection.objects.link(ob_empty)
    bpy.context.view_layer.update()
    v3, cf3, mg3, cl3, t3, c3, dg3 = measure(scene, vols, (), set(),
                                             verbose=False)
    named = (dg3["skipped_empty_mesh"] + [x["object"] for x in dg3["skipped_bbox"]]
             + [x["object"] for x in dg3["skipped_to_mesh"]])
    check("an object with no polygons is NAMED as unmeasurable, not dropped",
          "SELFTEST_NoPolys" in named, True, "skipped: %s" % (named,))
    check("CONTROL: the measurable object beside it is still measured",
          "road_corridor" in cl3
          and cl3["road_corridor"][1] == "SELFTEST_Solid", True,
          "closest: %s" % (cl3.get("road_corridor"),))

    # ---- 12. THE REPEAT-MEASURE ASSERTION MUST BE ABLE TO SAY 'DIFFERED' ---
    # `--repeat` compares fingerprints of N passes. A comparison that has only
    # ever been shown two identical things has not been tested. Feed it two
    # deliberately different ones and require it to notice; the project has
    # more than a dozen instruments that read the same either way, and an
    # equality test is the easiest possible place to add another.
    print("\n>> SELFTEST: the repeat-measure assertion, fed a difference")
    same = ['{"closest":{"road_corridor":[0.5,"A"]}}',
            '{"closest":{"road_corridor":[0.5,"A"]}}']
    diff = ['{"closest":{"road_corridor":[0.5,"A"]}}',
            '{"closest":{"road_corridor":[0.5,"B"]}}']
    check("CONTROL: two DIFFERENT pass fingerprints are reported as DIFFERED",
          len(set(diff)) == 1, False, "%d distinct" % len(set(diff)))
    check("two identical pass fingerprints are reported as IDENTICAL",
          len(set(same)) == 1, True, "%d distinct" % len(set(same)))

    # ---- 13. THE EDGE COURTESY IS THE ROAD CORRIDOR'S, NOT EVERY VOLUME'S --
    # An EDGE_FAMILIES name used to buy 0.50 m of exemption in ALL THREE
    # volumes because `limit` was computed once per object. On the corridor
    # that is correct and deliberate (the corridor is inflated by ROAD_MARGIN
    # and a kerb sits on the true boundary). On the car's swept volume and the
    # camera's clearance sphere it is 0.50 m of somebody's safety margin handed
    # over on a prefix match -- and `docs/placement_after_46.json` is a
    # PLACEMENT_CLEAN report whose own car_path clearance is -0.1553 m.
    #
    # Straddled: the same object, the same depth, in the two volumes.
    print("\n>> SELFTEST: the edge-family courtesy, per volume")
    car = vols.get("car_path")
    if not car:
        check("car_path volume exists to test the courtesy against",
              False, True, "no telemetry at %s" % a.telemetry)
    else:
        for o in list(scene.objects):
            if o.type == "MESH":
                bpy.data.objects.remove(o, do_unlink=True)
        cx, cy, cz = car["pts"][len(car["pts"]) // 3]

        def _place_at_depth(vol, want, base, direction):
            """Bisect for a point whose measured intrusion into `vol` is
            `want` -- the gate's own `intrusion()`, not an algebraic offset."""
            lo_o, hi_o = 0.0, max(vol["radius"]) + 5.0
            for _ in range(80):
                mid = 0.5 * (lo_o + hi_o)
                q = Vector((base[0] + direction[0] * mid,
                            base[1] + direction[1] * mid, base[2]))
                if intrusion(vol, q) > want:
                    lo_o = mid
                else:
                    hi_o = mid
            m = 0.5 * (lo_o + hi_o)
            return (base[0] + direction[0] * m, base[1] + direction[1] * m,
                    base[2])

        # 0.20 m in: past a limit of 0.0, comfortably under a limit of 0.50.
        px, py, pz = _place_at_depth(car, 0.20, (cx, cy, cz + 0.5), (1.0, 0.0))
        for nm in ("ARCH_RetainEdge_SELFTEST", "SELFTEST_PlainObject"):
            bpy.ops.mesh.primitive_cube_add(size=0.0002, location=(px, py, pz))
            bpy.context.object.name = nm
        bpy.context.view_layer.update()
        v4, cf4, mg4, cl4, t4, c4, dg4 = measure(scene, vols, (), set(),
                                                 verbose=False)
        edge_car = [x for x in v4 if x["object"] == "ARCH_RetainEdge_SELFTEST"
                    and x["volume"] == "car_path"]
        plain_car = [x for x in v4 if x["object"] == "SELFTEST_PlainObject"
                     and x["volume"] == "car_path"]
        check("CONTROL: a PLAIN object 0.20 m into the car path is a violation",
              bool(plain_car), True,
              "%s" % ([round(x["intrusion_m"], 4) for x in plain_car],))
        check("an EDGE-FAMILY object 0.20 m into the CAR PATH is a violation "
              "too", bool(edge_car), True,
              "%s" % ([round(x["intrusion_m"], 4) for x in edge_car],))
        rows[-1]["shipped_rule_excused_it"] = True

        # And the corridor half, unchanged: the courtesy must still apply there.
        for o in list(scene.objects):
            if o.type == "MESH":
                bpy.data.objects.remove(o, do_unlink=True)
        # The corridor normal, recomputed here rather than inherited from a
        # loop variable forty lines up: a control that depends on leftover
        # state is a control that stops meaning what it says.
        _co, _i0, _dd = road["kd"].find((hx, hy, 0.0))
        _j = (_i0 + 1) % len(P)
        _tx, _ty = P[_j][0] - P[_i0][0], P[_j][1] - P[_i0][1]
        _tl = math.hypot(_tx, _ty) or 1.0
        rx, ry, rz = _place_at_depth(road, 0.20, (hx, hy, hz + 1.0),
                                     (-_ty / _tl, _tx / _tl))
        for nm in ("ARCH_RetainEdge_SELFTEST", "SELFTEST_PlainObject"):
            bpy.ops.mesh.primitive_cube_add(size=0.0002, location=(rx, ry, rz))
            bpy.context.object.name = nm
        bpy.context.view_layer.update()
        v5, cf5, mg5, cl5, t5, c5, dg5 = measure(scene, vols, (), set(),
                                                 verbose=False)
        edge_road = [x for x in v5 if x["object"] == "ARCH_RetainEdge_SELFTEST"
                     and x["volume"] == "road_corridor"]
        plain_road = [x for x in v5 if x["object"] == "SELFTEST_PlainObject"
                      and x["volume"] == "road_corridor"]
        check("CONTROL: a PLAIN object 0.20 m into the corridor IS a violation",
              bool(plain_road), True,
              "%s" % ([round(x["intrusion_m"], 4) for x in plain_road],))
        check("an EDGE-FAMILY object 0.20 m into the CORRIDOR is still "
              "excused (courtesy kept where it belongs)",
              bool(edge_road), False, "")

    for o in list(scene.objects):
        if o.type == "MESH":
            bpy.data.objects.remove(o, do_unlink=True)

    # ---- verdict -------------------------------------------------------
    out = {"controls": rows, "failures": fails,
           "elevation_agreement_max_m": agree,
           "road_corridor": road["_meta"]}
    # The selftest's verdict needs its provenance as much as the gate's does:
    # "all controls behaved" is a claim about a particular spec and a
    # particular telemetry file, not a standing property of the tool.
    out[_prov.STAMP_KEY] = _prov.stamp(
        tool_file=__file__, tool_version="placement_gate --selftest",
        inputs=[("spec", a.spec), ("telemetry", a.telemetry),
                ("beat_sheet", a.sheet), ("camera_path", a.campath)])
    if a.out:
        json.dump(out, open(a.out, "w"), indent=1)
        print(f"\n>> wrote {a.out}")
    if fails:
        print(f"\n>> {len(fails)} SELFTEST CONTROL(S) MISBEHAVED: {fails}")
        return gate_exit.verdict("PLACEMENT_SELFTEST_FAIL")
    print(f"\n>> all {len(rows)} controls behaved")
    return gate_exit.verdict("PLACEMENT_SELFTEST_OK")


if __name__ == "__main__":
    # Blender 5.2 returns 0 for a script that raised, so a gate that CRASHED
    # was indistinguishable from one that passed. gate_exit.guard turns the
    # verdict main() returns into the process status and an exception into 2.
    gate_exit.guard(main, tool="placement_gate")
