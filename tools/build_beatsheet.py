"""THE camera beat sheet — one unbroken flight plan, first frame to last.

    .venv/bin/python tools/build_beatsheet.py

Reads the three artefacts that are already settled and writes
`docs/beat_sheet.{json,md}`:

    docs/circuit_spec.json    world, beat durations, Beat-6 trajectory, doppler
    docs/explode_plan.json    15 clusters, exploded positions, seat order
    telemetry/telemetry.csv   the car's motion, 1743 frames

BEAT 1 IS THE PART THAT DID NOT EXIST YET
-----------------------------------------
The circuit spec fixed beat DURATIONS and solved Beats 5-6 (including a Beat-6
trajectory verified at 2.03 g). It could not choreograph Beat 1 because it was
written before the inventory: it did not know there were 15 clusters, where they
hang, or how big they are.

The brief's rule for Beat 1 is absolute:

    "Every part/cluster gets a readable moment ... No part seats without having
     been seen."

So this schedules two interleaved sequences over 33 s:

  * a PRESENTATION order — the camera weaves through the field, and each cluster
    is large in frame for a window of its own;
  * a SEAT order — mechanically fixed by the inventory (core first, underbody
    before topside, aero late, wheels last, simultaneous).

These orders are NOT independent. A cluster must be presented before it seats,
or the brief is violated. They are reconciled by exploiting a property of the
seat order: it runs core -> inboard -> bodywork -> aero -> outboard corners, i.e.
roughly CENTRE-OUTWARD. A camera path that begins tight on the monocoque and
spirals outward therefore presents clusters in very nearly seat order for free,
and the schedule below only has to nudge the exceptions.

Flyability is checked, not assumed: the path length is divided by the available
time and reported as a mean camera speed. A drone that has to average 12 m/s
through a 9.84 m field is not weaving, it is fleeing.
"""

import csv
import json
import math
import os
import sys

R2_ANIM = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "anim")
sys.path.insert(0, R2_ANIM)
import filmtime as FT                                              # noqa: E402

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = os.path.join(R2, "docs")

# Beat durations fixed by the circuit spec §11 and verified to sum to the
# headline film length.
BEATS = [
    ("1_assembly", 33.0, "exploded field, 15 clusters presented then seated"),
    ("2_launch", 3.0, "idle, then 11.98 m to the glass at 53.8 km/h"),
    ("3_breach", 8.0, "screen time; world-time ramps to 15-25% and back"),
    ("4_transit", 5.6, "world time; apron, merge arc, onto the pit straight"),
    ("5_lap", 63.5, "one flying lap, vantage morphing continuously"),
    ("6_ending", 11.0, "decelerate and rise to the closing wide, hold 3 s"),
]


def load():
    spec = json.load(open(os.path.join(DOCS, "circuit_spec.json")))
    plan = json.load(open(os.path.join(DOCS, "explode_plan.json")))
    with open(os.path.join(R2, "telemetry", "telemetry.csv")) as f:
        tel = list(csv.DictReader(f))
    return spec, plan, tel


def cluster_geometry(plan):
    """Exploded world centre and radius for every cluster."""
    out = {}
    for k, c in plan["clusters"].items():
        off = c["explode_offset"]
        lo = [c["bbox_min"][i] + off[i] for i in range(3)]
        hi = [c["bbox_max"][i] + off[i] for i in range(3)]
        ctr = [(lo[i] + hi[i]) / 2 for i in range(3)]
        rad = max(0.5 * math.dist(lo, hi), 0.05)
        out[k] = {"centre": [round(v, 4) for v in ctr], "radius": round(rad, 4),
                  "n_parts": c["n_parts"], "tris": c["tris"],
                  "size": [round(hi[i] - lo[i], 3) for i in range(3)]}
    return out


def present_order(geo, seat_order):
    """Camera visiting order: seat order, but locally reordered for flyability.

    Seat order is mechanically fixed and runs roughly centre-outward, so it is
    used as the spine. Within the four corners — which seat SIMULTANEOUSLY and
    therefore impose no ordering on each other — the camera visits them in the
    order that minimises travel from wherever it arrives, rather than the
    arbitrary FL/FR/RL/RR of the inventory.
    """
    corners = [k for k in seat_order if k.startswith("CORNER_")]
    spine = [k for k in seat_order if not k.startswith("CORNER_")]
    if not corners:
        return spine
    cur = geo[spine[-1]]["centre"]
    rest, ordered = list(corners), []
    while rest:
        nxt = min(rest, key=lambda k: math.dist(cur, geo[k]["centre"]))
        ordered.append(nxt)
        cur = geo[nxt]["centre"]
        rest.remove(nxt)
    return spine + ordered


def camera_station(centre, radius, idx, n, look_dir=None):
    """Where the lens sits to make this cluster large AND legible in frame.

    Standoff scales with the cluster's own size so a 0.19 m steering wheel is
    framed as tightly as a 2.86 m monocoque — the brief wants each part large, not
    each part at the same distance.

    DIRECTION IS MEASURED, NOT GENERATED. `look_dir` comes from
    `tools/presentation_normals.py`, which samples 192 directions per cluster and
    scores each by the projected area a lens there would actually receive,
    weighted by how many distinct materials are visible from it.

    The first version of this function used an azimuth spiral instead — even
    coverage of the field, no knowledge of the parts — and the macro audit render
    duly presented the steering wheel FROM BEHIND: sharp, well lit, showing the
    column stub while the display, LED strip and buttons faced away. The measured
    direction for SW is [-0.879, 0.110, 0.464], which is the driver's viewpoint.

    The spiral survives only as a fallback for a cluster with no measurement, and
    a small spiral-derived roll is still mixed in so consecutive stations are not
    all at the same elevation — the path must still weave, not orbit on one plane.
    """
    standoff = max(radius * 1.55 + 0.42, 0.75)
    if look_dir:
        d = list(look_dir)
        # small deterministic tilt so 15 stations do not all sit at the same
        # elevation; too small to lose the measured face
        tilt = math.radians(7.0) * math.sin(idx * 1.7)
        d[2] += math.sin(tilt) * 0.35
    else:
        az = (idx / max(n, 1)) * 2.0 * math.pi * 1.35 + 0.6
        el = math.radians(9.0 + 26.0 * (0.5 + 0.5 * math.sin(idx * 1.7)))
        d = [math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el)]
    mag = max(math.sqrt(sum(v * v for v in d)), 1e-9)
    d = [v / mag for v in d]
    return [round(centre[i] + d[i] * standoff, 4) for i in range(3)], round(standoff, 4)


# --------------------------------------------------------------------------- #
#  THE CLOSE-OUT — the last 20 % of beat 1, and R2-029.                         #
# --------------------------------------------------------------------------- #
#
# WHAT WAS THERE.  Two keys, 163 frames apart: CORNER_FL's presentation station
# at t = 24.64 (frame 591) and the push toward the finished car at t = 31.40
# (frame 754).  Two keys cannot describe a move around a car, and this one did
# not: the straight line between those stations goes THROUGH the assembled car,
# and the quaternion slerp between the two orientations swings the lens onto the
# glass wall on the way.  Measured 48.88 deg off the parts field at frame 669,
# and the rendered frame at 648 is the mullion grid with not one part in it.
#
# WHAT IS ACTUALLY HAPPENING IN THOSE 163 FRAMES, from world/beat1_anim_anim.json:
#
#     NOSE   seats 597-605      FW  seats 630-638      RW  seats 663-671
#     the four CORNERS seat TOGETHER 696-704   <- the beat's climax
#
# Five landings, including the simultaneous four-wheel seat the brief calls for
# ("wheels LAST with a simultaneous seat"), and the camera was pointed at a wall
# for all of them.  So the close-out is not a transition to be smoothed over; it
# is the last act of the assembly and it has to be SHOT.
#
# THE MOVE.  The camera leaves CORNER_FL's station on the car's left flank,
# swings forward around the NOSE — outside the car, never through it — rising
# and widening from 58 mm to 36 mm so the whole 5.7 m car is held as the last
# parts arrive, then settles right into the hero three-quarter the declared final
# key already occupies.  Each key is placed against a landing:
#
#   t 25.90  f 622   the front wing arriving, corners still hanging outboard
#   t 27.30  f 655   wide enough to hold the rear wing's seat at 663
#   t 28.60  f 686   dead ahead, 10 frames before all four corners land together
#   t 29.90  f 718   the completed car, drifting right into the closing station
#
# CONSTRAINTS THE STATIONS ARE SOLVED AGAINST, all measured on beat1_anim.blend:
#   * the car body occupies x -2.70..3.02, y +-1.00, z 0.34..1.33.  Closest
#     approach of any station to that box is 2.14 m.
#   * the showroom's rope barrier ring reaches radius 6.96 m and z 0.92; every
#     station is either outside it or more than 1.2 m above it.
#   * walls |x| 15.25 / |y| 11.25, ceiling 6.20, spot rigs from z 5.11 — the
#     move never goes above 2.35 m.
#
# THE LAST KEY IS NOT TOUCHED.  t = 31.40 is the seam with beat 2, whose first
# key sits 2.09 m away 39 frames later at 40.0 -> 39.95 mm.  Moving it would put
# a discontinuity in a film whose one law is that there are none.
BEAT1_CLOSEOUT = [
    dict(t=25.90, world=[3.30, 3.10, 1.95], look_at=[2.70, 0.30, 0.62],
         lens_mm=48.0, fstop=2.6, focus_distance_m=3.16, focus_target="FW",
         note="the front wing arrives (seats 630); CORNER_FL sweeps past the "
              "lens 1.2 m out on the left"),
    dict(t=27.30, world=[5.30, 2.55, 2.20], look_at=[0.60, 0.20, 0.85],
         lens_mm=40.0, fstop=3.0, focus_distance_m=5.42, focus_target="RW",
         note="wide enough to carry the rear wing's seat at 663 — RW lands "
              "10.4 deg off axis inside a 14.2 deg half-frame"),
    dict(t=28.60, world=[6.60, 0.90, 2.35], look_at=[0.20, 0.05, 0.80],
         lens_mm=36.0, fstop=3.1, focus_distance_m=6.65, focus_target="CORNERS",
         note="ahead of the nose for the simultaneous four-wheel seat at 696; "
              "all four corners are inside 8.2 deg of a 15.7 deg half-frame"),
    dict(t=29.90, world=[7.15, -1.90, 2.20], look_at=[0.15, 0.0, 0.78],
         lens_mm=38.0, fstop=3.15, focus_distance_m=7.40, focus_target="CAR",
         note="the car is complete; the camera drifts right into the closing "
              "three-quarter"),
]


# --------------------------------------------------------------------------- #
#  BRIDGES — where two presentations are too far apart in BEARING.              #
# --------------------------------------------------------------------------- #
#
# The presentations are 42 frames apart and the camera slerps between them.  Most
# of those transitions keep something in frame the whole way, because the field is
# dense and the aim gate scores the NEAREST cluster: on the rebuilt rig, 788 of
# beat 1's 792 frames measure 0.00 deg.
#
# One does not.  RW's station looks at the rear wing hanging BEHIND the car in
# -Y; CORNER_RL's looks at the rear-left wheel in +Y.  That is a 110 degree pan,
# and halfway through it the lens is pointed almost straight DOWN at bare floor:
# MEASURED 30.05 deg off the nearest cluster edge over frames 446-449, the only
# remaining excursion in the beat and 0.05 deg past its declared 30 deg bound.
#
# The bridge is not a fudge to get under a threshold; it is the shot the pan was
# missing.  The engine cover seats at frame 440, six frames earlier, so on the way
# from the rear wing to the rear-left corner the camera has something real to look
# at, and it is the thing that just landed.
# TWO keys, not one, and the reason is measured: with a single bridge at frame
# 446 the excursion shrank from 30.05 deg to 10.85 deg but 2 frames (434-435)
# still put the rear wing's edge 1.096 of a half-frame out, i.e. just off the top
# of the picture at 58 mm.  The second key sits ON those frames.  The lens widens
# 58 -> 50 -> 54 -> 58 across the bridge, which is the camera taking in the car
# so far before tightening back onto a wheel.
BEAT1_BRIDGES = [
    dict(t=18.10, world=[-3.70, 1.11, 2.16], look_at=[-1.35, 0.05, 1.02],
         lens_mm=50.0, fstop=2.4, focus_distance_m=2.81,
         focus_target="EC_SEATING",
         note="bridge RW -> CORNER_RL, part 1: the engine cover is landing "
              "(frames 432-440) and the pan is on it"),
    dict(t=18.60, world=[-3.02, 1.06, 2.18], look_at=[-1.60, 0.10, 0.95],
         lens_mm=54.0, fstop=2.3, focus_distance_m=2.11, focus_target="EC_SEATED",
         note="bridge RW -> CORNER_RL, part 2: seated, and the lens tightens "
              "back toward the rear-left corner"),
]


def build_beat1(geo, plan, dur, normals=None):
    order = present_order(geo, plan["seat_order"])
    n = len(order)
    # Reserve the last 20% for the final settle and the push toward the car, so
    # the presentations occupy the first 80% and every part is seen before the
    # corners land together.  That reservation is NOT a gap: see BEAT1_CLOSEOUT.
    present_span = dur * 0.80
    slot = present_span / n
    keys, sched = [], []
    prev = None
    path_len = 0.0
    for i, k in enumerate(order):
        g = geo[k]
        nd = (normals or {}).get(k, {}).get("normal")
        pos, standoff = camera_station(g["centre"], g["radius"], i, n, nd)
        t = round(i * slot, 3)
        if prev is not None:
            path_len += math.dist(prev, pos)
        prev = pos
        # 35 mm lens on the wide clusters, longer on the small dense ones so the
        # steering wheel is not presented by shoving the lens 190 mm from it.
        lens = 35.0 if g["radius"] > 0.8 else 58.0
        keys.append({
            "t": t, "beat": "1_assembly", "world": pos,
            "look_at": g["centre"], "lens_mm": lens,
            "fstop": 2.2 if g["radius"] < 0.8 else 2.8,
            "focus_target": k, "focus_distance_m": standoff,
            "presentation_dir_measured": bool(nd),
            "visible_materials": (normals or {}).get(k, {}).get("distinct_materials"),
            "world_time_scale": 1.0,
            "note": f"present {k} ({g['n_parts']} parts, {g['tris']:,} tris)",
        })
        sched.append({
            "cluster": k, "n_parts": g["n_parts"], "tris": g["tris"],
            "presented_t": t, "presented_until_t": round(t + slot, 3),
            "seat_t": None, "seen_before_seat": None,
        })

    # Seating: mechanical order, staggered, with the four corners simultaneous.
    seat_start = dur * 0.42
    seat_span = dur * 0.50
    spine = [k for k in plan["seat_order"] if not k.startswith("CORNER_")]
    corners = [k for k in plan["seat_order"] if k.startswith("CORNER_")]
    per = seat_span / (len(spine) + 1)
    seat_t = {}
    for i, k in enumerate(spine):
        seat_t[k] = round(seat_start + i * per, 3)
    for k in corners:
        seat_t[k] = round(seat_start + len(spine) * per, 3)   # simultaneous

    for s in sched:
        s["seat_t"] = seat_t[s["cluster"]]
        s["seen_before_seat"] = s["presented_t"] < s["seat_t"]

    # BRIDGES and THE CLOSE-OUT — see the two blocks above.
    for k in BEAT1_BRIDGES + BEAT1_CLOSEOUT:
        e = dict(k)
        e.update(beat="1_assembly", world_time_scale=1.0)
        keys.append(e)

    # final push toward the assembled car. THE SEAM WITH BEAT 2 — do not move it.
    last = [6.8, -4.4, 1.9]
    keys.append({
        "t": round(dur - 1.6, 3), "beat": "1_assembly",
        "world": last, "look_at": [0.15, 0.0, 0.75],
        "lens_mm": 40.0, "fstop": 3.2, "focus_target": "CAR",
        "focus_distance_m": 8.3, "world_time_scale": 1.0,
        "note": "push toward the completed car; spot rigs ramp ~1 stop over 12 "
                "frames. THE SEAM: beat 2's first key is 2.09 m away 39 frames "
                "later at 39.95 mm, so this key is fixed and beats 1 and 2 join "
                "at 1.29 m/s with no step in position, aim or focal length",
    })
    # ONE PATH means one ordering: the bridges and close-out are authored out of
    # sequence, so the keys are sorted by film time and the path length is
    # measured on the sorted list rather than on the order they were appended in.
    keys.sort(key=lambda k: k["t"])
    path_len = sum(math.dist(keys[i - 1]["world"], keys[i]["world"])
                   for i in range(1, len(keys)))
    return order, keys, sched, path_len


# The assembled car's own extent, MEASURED on world/beat1_anim.blend at the last
# frame (947 objects dumped, grouped by module prefix): MB/FW/NOSE/RW/wheel/halo
# together span these bounds.  Beat 1's camera is the only camera in the film
# that flies inside the same room as the car while it is being built, so this is
# where a fly-through gets caught, and it is what R2-029 was.
CAR_BOX_LO = (-2.70, -1.00, 0.34)
CAR_BOX_HI = (3.02, 1.00, 1.33)

# DERIVED, not chosen.  The camera's near clip is 0.10 m (Blender's default; the
# rig does not override it for the film camera), so anything closer than that
# renders as a cut-open surface filling the frame.  0.30 m is three times that,
# which leaves room for the bezier to bow off the straight chord this check
# samples.  It is deliberately NOT a "keep away from the car" figure: beat 1 is a
# weave THROUGH the field and skimming 0.5 m over the monocoque between the two
# front corners is the shot, not a defect.  What is a defect is going THROUGH,
# and that is what 0.30 m catches.
#
# THIS IS A PRE-FLIGHT, NOT THE AUTHORITATIVE MEASUREMENT.  It samples the
# straight chord between keys.  The real path is the per-frame one the rig build
# emits to world/camera_rig_path.json, and R2-025 is precisely the record of
# what sweeping keys instead of the path costs.
CAR_CLEAR_M = 0.30

# This module's own docstring calls 12 m/s through a 9.84 m field "not weaving,
# fleeing".  Half of that is the working limit: 6 m/s is 21.6 km/h, brisk for a
# drone in a 30 x 22 m room and slow enough that a 58 mm lens still resolves.
SPEED_LIMIT_MS = 6.0


def _box_dist(p, lo, hi):
    """Distance from a point to the SURFACE of an axis-aligned box, 0 if inside."""
    d = [max(lo[i] - p[i], 0.0, p[i] - hi[i]) for i in range(3)]
    return math.sqrt(sum(v * v for v in d))


def beat1_flight_check(keys, fps=24):
    """Per-key speed and clearance, in metres and metres per second.

    A COUNT OF KEYS IS NOT A MEASUREMENT.  R2-029 shipped because the continuity
    gate measured position jumps and rotation steps, and a slow straight move
    through a car has neither.  So this measures the two quantities that move
    actually has wrong: how fast the camera goes, and how close it gets to the
    car -- sampled BETWEEN keys, not at them, because the defect was entirely
    between two keys.
    """
    rows, worst_clear, worst_speed = [], (1e9, None), (0.0, None)
    for i in range(1, len(keys)):
        a, b = keys[i - 1], keys[i]
        dt = max(b["t"] - a["t"], 1e-9)
        d = math.dist(a["world"], b["world"])
        v = d / dt
        # sample the straight chord between the keys; the spline bows outward
        # from it, so the chord is the pessimistic case for clearance
        clear = min(_box_dist([a["world"][c] + (b["world"][c] - a["world"][c]) * u / 40.0
                               for c in range(3)], CAR_BOX_LO, CAR_BOX_HI)
                    for u in range(41))
        rows.append({"from": a.get("focus_target"), "to": b.get("focus_target"),
                     "t": [a["t"], b["t"]],
                     "frames": [int(round(a["t"] * fps)), int(round(b["t"] * fps))],
                     "chord_m": round(d, 3), "speed_ms": round(v, 3),
                     "min_clearance_m": round(clear, 3),
                     "lens_mm": [a["lens_mm"], b["lens_mm"]]})
        if clear < worst_clear[0]:
            worst_clear = (clear, rows[-1])
        if v > worst_speed[0]:
            worst_speed = (v, rows[-1])
    return rows, worst_clear, worst_speed


def main(check=None):
    """`check` = path to an EXISTING beat sheet: gate it instead of writing one.

    A GATE THAT HAS NEVER FAILED HAS NOT BEEN SHOWN TO WORK, and this project has
    shipped six checks that could not fail.  So both gates below can be pointed
    at an arbitrary sheet, and the one they are tested against is the artefact
    already known to be bad -- the sheet whose beat 1 was authored against an
    older docs/explode_plan.json and whose close-out was two keys 163 frames
    apart.  It must come back BEATSHEET_VIOLATION naming FD, NOSE and the
    fly-through, and it does.
    """
    spec, plan, tel = load()
    geo = cluster_geometry(plan)
    total = sum(d for _, d, _ in BEATS)

    npath = os.path.join(DOCS, "presentation_normals.json")
    normals = json.load(open(npath)) if os.path.exists(npath) else {}
    print(f">> presentation normals: {len(normals)} clusters measured"
          if normals else ">> WARNING: no presentation normals; spiral fallback")
    order, b1keys, sched, path_len = build_beat1(geo, plan, BEATS[0][1], normals)
    mean_speed = path_len / BEATS[0][1]
    if check:
        print(f">> GATING AN EXISTING SHEET: {check}  (nothing will be written)")
        b1keys = json.load(open(check))["beat1"]["camera_keys"]
        path_len = sum(math.dist(b1keys[i - 1]["world"], b1keys[i]["world"])
                       for i in range(1, len(b1keys)))
        mean_speed = path_len / BEATS[0][1]

    unseen = [s["cluster"] for s in sched if not s["seen_before_seat"]]

    # ---- GATE: does beat 1's camera actually miss the car? (R2-029) ---------
    flight, worst_clear, worst_speed = beat1_flight_check(b1keys)
    flight_fail = []
    if worst_clear[0] < CAR_CLEAR_M:
        r = worst_clear[1]
        flight_fail.append(
            "the camera passes %.3f m from the assembled car body between frames "
            "%d and %d (%s -> %s); the floor is %.2f m"
            % (worst_clear[0], r["frames"][0], r["frames"][1], r["from"], r["to"],
               CAR_CLEAR_M))
    if worst_speed[0] > SPEED_LIMIT_MS:
        r = worst_speed[1]
        flight_fail.append(
            "the camera covers %.3f m in %.2f s = %.2f m/s between frames %d and "
            "%d (%s -> %s); beat 1's limit is %.1f m/s"
            % (r["chord_m"], r["t"][1] - r["t"][0], worst_speed[0], r["frames"][0],
               r["frames"][1], r["from"], r["to"], SPEED_LIMIT_MS))

    # ---- GATE: is every cluster IN FRAME at its own presentation key? -------
    #
    # The keys used to be generated from one revision of docs/explode_plan.json
    # and then survived a later one.  Nothing re-checked them, and two clusters
    # (FD and NOSE) ended up 34.5 and 43.8 degrees OUTSIDE the frame edge at
    # their own presentation -- the brief's "no part seats without having been
    # seen", violated by a stale file rather than by a bad camera move.  So the
    # geometry that the keys were solved against is re-measured here, from the
    # plan as it stands, and reported as an angle.
    #
    # AND THE FIELD MOVES.  A cluster hangs at its exploded centre only until it
    # flies; after that the honest question is where it IS at that key's time.
    # world/beat1_anim_anim.json is what the part animation was actually built
    # from, so the seat frames come from there, and a key placed against a
    # LANDING (the close-out's four) is measured against the landing position.
    anim_p = os.path.join(R2, "world/beat1_anim_anim.json")
    anim = json.load(open(anim_p)) if os.path.exists(anim_p) else {}
    flight_f = float(anim.get("flight_s", 1.55)) * 24
    land = {c: v["last_land"] for c, v in anim.get("clusters", {}).items()}
    final = {k: [(c["bbox_min"][i] + c["bbox_max"][i]) / 2 for i in range(3)]
             for k, c in plan["clusters"].items()}

    def where(name, t_s):
        """Cluster centre at film time `t_s`, exploded -> seated."""
        exp = geo[name]["centre"]
        lf = land.get(name)
        if lf is None:
            return exp
        u = max(0.0, min(1.0, (t_s * 24 - (lf - flight_f)) / max(flight_f, 1.0)))
        u = u * u * (3.0 - 2.0 * u)
        return [exp[i] + (final[name][i] - exp[i]) * u for i in range(3)]

    framing, framing_fail = [], []
    for k in b1keys:
        t = k.get("focus_target")
        if t not in geo:
            continue
        ctr, rad = where(t, k["t"]), geo[t]["radius"]
        cam, look = k["world"], k["look_at"]
        v = [look[i] - cam[i] for i in range(3)]
        nv = math.sqrt(sum(x * x for x in v)) or 1.0
        d = [ctr[i] - cam[i] for i in range(3)]
        nd = math.sqrt(sum(x * x for x in d)) or 1.0
        c = max(-1.0, min(1.0, sum(v[i] * d[i] for i in range(3)) / (nv * nd)))
        ang = math.degrees(math.acos(c))
        edge = max(0.0, ang - math.degrees(math.asin(min(1.0, rad / max(nd, rad)))))
        half_v = math.degrees(math.atan(0.5 * (36.0 * 2160 / 3840) / k["lens_mm"]))
        framing.append({"cluster": t, "t": k["t"], "range_m": round(nd, 3),
                        "edge_angle_deg": round(edge, 3),
                        "half_frame_deg": round(half_v, 3),
                        "lens_mm": k["lens_mm"]})
        if edge > half_v:
            framing_fail.append(
                "%s is %.2f deg outside a %.2f deg half-frame at its own "
                "presentation key (t = %.2f s, %.0f mm, %.2f m away)"
                % (t, edge - half_v, half_v, k["t"], k["lens_mm"], nd))

    # beat time offsets
    t0, offsets = 0.0, {}
    for name, dur, _ in BEATS:
        offsets[name] = round(t0, 3)
        t0 += dur

    out = {
        "law": "ONE CONTINUOUS SHOT — zero cuts, one camera, one path",
        "fps": 24,
        "total_s": round(total, 3),
        "total_frames": int(round(total * 24)),
        "beats": [{"name": n, "start_s": offsets[n], "duration_s": d, "note": note}
                  for n, d, note in BEATS],
        "beat1": {
            "present_order": order,
            "schedule": sched,
            "camera_keys": b1keys,
            "path_length_m": round(path_len, 3),
            "mean_camera_speed_ms": round(mean_speed, 3),
            "clusters_seating_unseen": unseen,
            "flight": flight,
            "min_clearance_to_car_m": round(worst_clear[0], 3),
            "max_key_to_key_speed_ms": round(worst_speed[0], 3),
            "car_box": {"lo": list(CAR_BOX_LO), "hi": list(CAR_BOX_HI),
                        "clearance_floor_m": CAR_CLEAR_M,
                        "speed_limit_ms": SPEED_LIMIT_MS,
                        "measured_on": "world/beat1_anim.blend"},
            "presentation_framing": framing,
        },
        "speed_ramps": [{
            "beat": "3_breach",
            "screen_s": 8.0, "world_s": 1.6,
            # SOLVED here rather than declared, so the sheet is correct on a
            # single pass.  It used to be written as 0.20 and only corrected on
            # a SECOND run of author_beats2_5.py -- a pipeline whose output
            # depended on how many times it had been run.
            "min_world_time_scale": round(
                FT.solve_floor(int(round(8.0 * 24)), 1.6,
                               FT.RAMP_EASE_IN_FRAMES, FT.RAMP_EASE_OUT_FRAMES), 6),
            "ease": "smooth (no stepped time); shutter scales with world time so "
                    "motion blur reads correctly at slowed speed",
            "audio": "all layers time-stretch AND pitch with world time",
        }],
        "doppler": spec["doppler"],
        "beat6": spec["beat6"],
        "sources": {
            "circuit": "docs/circuit_spec.json",
            "explode": "docs/explode_plan.json",
            "telemetry": "telemetry/telemetry.csv",
        },
    }
    if not check:
        # THIS FILE DOES NOT OWN THE WHOLE SHEET, AND USED TO OVERWRITE IT.
        # `tools/author_beats2_5.py` writes beat2..beat5, `aim` and `time_map`
        # into the same JSON. Running this file alone silently deleted 413 camera
        # keys and every beat's aim declaration -- four beats' worth of camera,
        # which is the exact defect #34 existed to fix, reintroduced by running a
        # tool. The blocks this file does not author are now CARRIED FORWARD and
        # named in the log, so the destruction cannot happen quietly.
        dest = os.path.join(DOCS, "beat_sheet.json")
        carried = []
        if os.path.exists(dest):
            try:
                prev = json.load(open(dest))
            except Exception:
                prev = {}
            for k, v in prev.items():
                if k not in out:
                    out[k] = v
                    carried.append(k)
        if carried:
            print(">> carried forward from the existing sheet (this file does "
                  "not author them; tools/author_beats2_5.py does): "
                  + ", ".join(sorted(carried)))
            print(">> RE-RUN tools/author_beats2_5.py if beat 1's timing or the "
                  "beat durations changed, because beats 2-5 are splined "
                  "against them.")
        json.dump(out, open(dest, "w"), indent=1)

    print(f">> film {total:.1f} s = {out['total_frames']} frames @ 24 fps")
    print(f">> beat 1: {len(order)} clusters, path {path_len:.2f} m, "
          f"mean camera speed {mean_speed:.2f} m/s")
    print(f">> every cluster seen before it seats: "
          f"{'YES' if not unseen else 'NO -> ' + ', '.join(unseen)}")
    for s in sched:
        flag = "" if s["seen_before_seat"] else "   <-- SEATS UNSEEN"
        print(f"   {s['cluster']:<16} present {s['presented_t']:6.2f}s  "
              f"seat {s['seat_t']:6.2f}s  {s['n_parts']:>3} parts{flag}")
    print(">> beat 1 FLIGHT — chord speed and clearance to the assembled car "
          "body, sampled BETWEEN keys")
    for r in flight:
        mark = ""
        if r["min_clearance_m"] < CAR_CLEAR_M:
            mark = "   <-- INSIDE THE CAR" if r["min_clearance_m"] <= 0.0 else \
                   "   <-- TOO CLOSE"
        if r["speed_ms"] > SPEED_LIMIT_MS:
            mark += "   <-- TOO FAST"
        print(f"   f{r['frames'][0]:>4}-{r['frames'][1]:<4} {str(r['from']):<14}"
              f"-> {str(r['to']):<14} {r['chord_m']:6.2f} m  "
              f"{r['speed_ms']:5.2f} m/s  clear {r['min_clearance_m']:6.3f} m  "
              f"{r['lens_mm'][0]:.0f}->{r['lens_mm'][1]:.0f} mm{mark}")
    print(f">> beat 1 worst clearance to the car {worst_clear[0]:.3f} m "
          f"(floor {CAR_CLEAR_M}), fastest key-to-key {worst_speed[0]:.2f} m/s "
          f"(limit {SPEED_LIMIT_MS})")
    print(">> beat 1 FRAMING — each cluster's angle OUTSIDE the frame edge at "
          "its own presentation key, against the plan as it stands now")
    for r in framing:
        over = r["edge_angle_deg"] - r["half_frame_deg"]
        print(f"   {r['cluster']:<16} t {r['t']:6.2f}s  {r['range_m']:5.2f} m  "
              f"{r['lens_mm']:4.0f} mm   edge {r['edge_angle_deg']:6.2f} deg vs "
              f"half-frame {r['half_frame_deg']:5.2f} deg"
              + ("   <-- OFF SCREEN by %.2f deg" % over if over > 0 else ""))

    fails = flight_fail + framing_fail + (
        ["clusters that seat unseen: " + ", ".join(unseen)] if unseen else [])
    for f in fails:
        print("   FAIL " + f)
    print(">> STAGE RESULT: BEATSHEET_OK" if not fails
          else ">> STAGE RESULT: BEATSHEET_VIOLATION")
    return 0 if not fails else 1


# Imported by path, not by package: this runs inside Blender's interpreter
# with whatever cwd the caller happened to have.
import os as _os_ge, sys as _sys_ge
if _os_ge.path.dirname(_os_ge.path.abspath(__file__)) not in _sys_ge.path:
    _sys_ge.path.insert(0, _os_ge.path.dirname(_os_ge.path.abspath(__file__)))
import gate_exit                                                 # noqa: E402


if __name__ == "__main__":
    # Blender 5.2 returns 0 for a script that raised, so a crash was
    # indistinguishable from a pass. guard() makes it a status 2 and passes
    # a real verdict through unchanged. See tools/gate_exit.py.
    gate_exit.guard(
        lambda: main(check=(sys.argv[sys.argv.index("--check") + 1]
                            if "--check" in sys.argv else None)),
        tool="build_beatsheet")
