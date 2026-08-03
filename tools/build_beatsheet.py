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
or the brief is violated.

THEY USED TO BE RECONCILED BY AN ARGUMENT, AND THE ARGUMENT WAS FALSE. It ran:
the seat order goes core -> inboard -> bodywork -> aero -> outboard corners,
i.e. roughly CENTRE-OUTWARD, so a camera that begins tight on the monocoque and
spirals outward presents clusters in very nearly seat order for free. Seat
order is centre-outward in ASSEMBLY. It is not centre-outward in SPACE: its
9th, 10th and 11th entries are NOSE at x = +3.75, FW at x = +4.38 and RW at
x = -4.59, and the camera was given ONE 1.76 s slot to cross all 9 m of that.

The measured cost, on the shipped film (`render/film9_path.json`, campath gate):
**1.25 s at up to 7.82 m/s** in a beat that declares a 1.994 m/s weave, 8.5 %
of the beat above twice its own design speed, and a contact-sheet review of
three independent renders reading the middle of it as an illegible streak
field. THE AIM GATE PASSED ALL OF IT at 7.24 deg worst, because a camera can be
pointed exactly at its subject and still be moving far too fast to photograph
it.

So the visiting order is no longer inherited from the inventory: it is SOLVED,
against the cost of the move, subject to every cluster being presented before
it starts flying. See `move_seconds` and `present_order`.

Flyability is checked, not assumed, and now in the units the picture is in:
metres per second against the beat's own declared weave speed, and FRAME WIDTHS
PER FRAME against the rate at which a pan stops being readable. A drone that
has to average 12 m/s through a 9.84 m field is not weaving, it is fleeing --
and one that turns 87 degrees in 18 frames through a 58 mm lens is not
presenting anything, whatever its speed.
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


# --------------------------------------------------------------------------- #
#  THE MOVE COST — why beat 1 is timed the way it is.  R2-062.                  #
# --------------------------------------------------------------------------- #
#
# WHAT WAS WRONG.  Beat 1 used SEAT ORDER as its visiting order and gave every
# cluster the same 1.76 s slot.  Neither of those is a property of the pictures.
#
#   * seat order is centre-outward in ASSEMBLY, not in SPACE.  Its 9th, 10th and
#     11th entries are NOSE (x = +3.75), FW (x = +4.38) and RW (x = -4.59), so
#     the camera was required to cross the whole 9 m field in one slot.
#   * a fixed slot pays the same time for a 1.0 m hop and a 9.1 m one.
#
# MEASURED ON THE SHIPPED FILM (render/film9_path.json, the campath gate):
#
#     f387-416   1.25 s at up to 7.82 m/s, in a beat whose own sheet declares a
#                1.994 m/s mean and whose docstring calls a fast camera here
#                "not weaving, fleeing"
#     8.5 %      of beat 1's frames exceed twice that declared mean
#     f455       23.41 % of the frame width swept in ONE FRAME, the highest
#                rotation anywhere in beat 1
#
# and a contact-sheet review of three independent renders (film8, beat1_fix,
# showlight) reads frame 400 — the middle of that dash — as an illegible streak
# field.  The AIM gate passed all of it at 7.24 deg worst, because a camera can
# be pointed exactly at a subject and still be moving too fast to photograph it.
#
# WHAT REPLACES IT.  A move is given the time its WORST constraint needs.  Three
# things can bind, and the cost of a move is whichever needs the most seconds:
#
#     DWELL_S                        the readable moment the brief owes a cluster
#     chord x ease / peak-speed      transit without exceeding beat 1's own
#                                    declared weave speed
#     bearing x ease / pan-limit     the turn, expressed in FRAME WIDTHS rather
#                                    than degrees — 5 deg/frame at 35 mm and at
#                                    58 mm are different pictures, which is the
#                                    same argument tools/continuity_gate makes
#                                    for reporting rotation that way
#
# Every one of those costs is time-like and every constraint scales as 1/dt, so
# allocating the span in PROPORTION to the cost is not a heuristic: it is the
# exact minimax solution — it equalises how close each move is to its own limit,
# and no other split has a lower worst case.  The common ratio comes out as one
# number, BUDGET_RATIO, which says how far beat 1's tightest move is from spec.
#
# AND IT IS WHY THE ADDITIVE VERSION OF THIS WAS WRONG.  A cost of
# `dwell + chord/v + bearing/omega` ranked CORNER_RR -> CORNER_RL (1.67 m,
# 83.7 deg) below CORNER_RL -> CORNER_FR (4.40 m, 59.0 deg) because the transit
# term dominated, gave the pure pan 35 frames, and the built path came back at
# 17.3 % of frame width per frame — WORSE than the 14.5 % it replaced.  A move
# that is almost all rotation has to be paid for in rotation.
#
# The visiting order is then the order that MINIMISES the total of those costs,
# solved exactly (Held-Karp over 11 nodes), subject to every cluster being
# presented before it starts FLYING — not merely before it lands, because a
# station is solved against a cluster's EXPLODED centre and is stale the moment
# the cluster leaves it.
#
# NOTE WHAT IS *NOT* CLAIMED HERE.  This does not make the pictures good; it
# makes them photographable.  The eased peaks are estimated, not evaluated, so
# the gates below are a pre-flight and the per-frame campath gate on the built
# path remains the authority.
DWELL_S = 0.72            # s of hold per presentation
SENSOR_W_MM = 36.0
SENSOR_H_MM = 36.0 * 2160 / 3840

# The Bezier the rig lays through these keys overshoots the chord/dt mean, so a
# schedule that sets the MEAN right still has to know what the PEAK will be.
#
# MEASURED, NOT ASSUMED. Ratio of the per-frame peak speed to the key-to-key
# chord/dt mean, over all 20 non-degenerate key-to-key segments of beat 1 on the
# shipped path (render/film9_path.json):
#
#     1.522 1.507 1.506 1.502 1.475 1.421 1.402 1.389 1.375 1.365  (worst ten)
#
# so 1.52 is the observed maximum, not a guess and not a safety factor. The one
# segment excluded is NOSE -> FW (f338-380), 1.005 m in 1.76 s, where the peak
# inside the window is set by the OVERSHOOT OF ITS NEIGHBOURS rather than by the
# move itself and the ratio is a meaningless 2.65.
#
# THIS MAKES THE CHECK BELOW A PRE-FLIGHT AND NOT THE AUTHORITY. It predicts
# 7.89 m/s for the dash that measured 7.82 and 21.1 % of frame width for the pan
# that measured 23.4, which is good enough to catch a defect and NOT good enough
# to adjudicate a marginal one -- the ratio is set partly by the NEIGHBOURING
# segments' timing, which two keys cannot see.
#
# SO THE PREDICTION IS A RANGE, NOT A NUMBER, AND A GATE DOES NOT FAIL INSIDE
# ITS OWN RESOLUTION. The measured ratios span 1.365 to 1.522, so a move's peak
# is predicted as [mean x 1.36, mean x 1.52]:
#
#     range entirely above the limit   FAIL   -- it cannot be within spec
#     range straddling the limit       WARN   -- this instrument cannot say
#     range entirely below            pass
#
# That distinction is load-bearing. CORNER_FR -> CORNER_FL is 4.609 m in 42
# frames, it is PINNED GEOMETRY inside the part of beat 1 the review calls the
# best material in the film, and it predicts [3.60, 4.00] against a 4.00 limit.
# Failing the build on it would be an instrument condemning a shot it cannot
# measure -- and the per-frame path says 3.576 m/s, comfortably inside.
EASE_PEAK_LO = 1.36
EASE_PEAK_HI = 1.52
EASE_PEAK = EASE_PEAK_HI          # scheduling pays the pessimistic one

# ROTATION EASES DIFFERENTLY FROM TRANSLATION, AND BY MUCH MORE.  Same
# measurement, same 20 segments, but the ratio of peak deg/frame to
# (endpoint bearing / dt) is 1.10 to 2.54 with a median of 2.4, against 1.36 to
# 1.52 for speed.  It is larger and looser for a reason: the camera TRANSLATES
# between two keys, so the direction to what it is looking at swings along an
# arc that the straight-line bearing between the endpoints does not measure at
# all — SP -> FD has 0.4 deg of endpoint bearing and a measured 1.47 deg/frame
# peak.  Using the translation figure for rotation is what under-timed the
# rear-axle crossing by 40 %.
#
# So the pan side of this pre-flight is WEAK BY CONSTRUCTION and is stated as
# such: it is good enough to size a schedule and not good enough to certify one.
EASE_ROT_LO = 1.10
EASE_ROT_HI = 2.50

# The presentation phase's own design speed, and how far a single move may peak
# above it. THE OLD SPEED_LIMIT_MS OF 6.0 IS NOT REMOVED — it is the room's
# flyability limit and it still means something — but it is three times beat 1's
# declared mean, so it could never have caught the dash, and did not.
BEAT1_DESIGN_SPEED_MS = 2.00
BEAT1_PEAK_FACTOR = 2.00
# The campath gate calls anything above 12 % of frame width per frame "fast,
# readable, but detail will be lost" and anything above 25 % unreadable. The
# sheet is held to the lower of the two, because a presentation whose detail is
# lost is a presentation that did not happen.
BEAT1_PAN_LIMIT_WIDTHS = 0.12


def hfov_deg(lens_mm):
    return math.degrees(2.0 * math.atan(SENSOR_W_MM / (2.0 * lens_mm)))


def _transit_s(chord_m):
    return chord_m * EASE_PEAK_HI / (BEAT1_DESIGN_SPEED_MS * BEAT1_PEAK_FACTOR)


def _pan_s(bearing_deg, hfov):
    return bearing_deg * EASE_ROT_HI / max(BEAT1_PAN_LIMIT_WIDTHS * hfov * 24.0,
                                           1e-9)


def move_seconds(chord_m, bearing_deg, hfov):
    """Seconds a move needs = whichever of its three constraints needs the most.

    The return value is the dt at which this move sits EXACTLY on its limits, so
    a segment's total is the span at which the whole segment does. THIS IS THE
    TIMING COST, and only the timing cost.
    """
    return max(DWELL_S, _transit_s(chord_m), _pan_s(bearing_deg, hfov))


def order_seconds(chord_m, bearing_deg, hfov):
    """Cost of a move for choosing the TOUR, which is a different question.

    Timing asks "given a fixed span, how do I split it", and there only the
    binding constraint of each move matters -- hence the max() above. Choosing a
    route asks "which tour costs least overall", and costs ADD along a tour: a
    move that is moderately long AND moderately turny is worse than one that is
    only one of those, and max() cannot see that.

    It is not a stylistic preference. The tour that minimises the sum of the
    max() cost is MB -> CI -> NOSE -> FW -> halo -> SP -> BB -> EC -> FD -> RW
    -> SW, and the rig's own AIM GATE FAILS it: at frame 131, between the front
    wing and the halo, the nearest cluster's edge reaches 0.936 of the
    half-frame against a 0.92 margin -- the field falls out of the picture. The
    tour that minimises the sum of this additive cost is MB -> halo -> CI ->
    NOSE -> FW -> SW -> BB -> SP -> FD -> EC -> RW, which passes at 0.072 and
    ends at the rear of the car where the bridge into the corners begins. Both
    were built and measured; this is the one that survived.
    """
    return DWELL_S + _transit_s(chord_m) + _pan_s(bearing_deg, hfov)


def lens_for(g):
    """35 mm on the wide clusters, longer on the small dense ones so the
    steering wheel is not presented by shoving the lens 190 mm from it."""
    return 35.0 if g["radius"] > 0.8 else 58.0


def key_geom(geo, normals, k, idx, n):
    """(station, standoff, lens, unit view direction) for a presentation."""
    g = geo[k]
    pos, standoff = camera_station(g["centre"], g["radius"], idx, n,
                                   (normals or {}).get(k, {}).get("normal"))
    d = [g["centre"][i] - pos[i] for i in range(3)]
    m = math.sqrt(sum(x * x for x in d)) or 1.0
    return pos, standoff, lens_for(g), [x / m for x in d]


def _bearing(u, v):
    return math.degrees(math.acos(max(-1.0, min(1.0, sum(a * b for a, b in zip(u, v))))))


def _hop_cost(geo, normals, a, ia, b, ib, n, cost=move_seconds):
    pa, _sa, la, va = key_geom(geo, normals, a, ia, n)
    pb, _sb, lb, vb = key_geom(geo, normals, b, ib, n)
    return cost(math.dist(pa, pb), _bearing(va, vb),
                min(hfov_deg(la), hfov_deg(lb)))


def _exit_cost(geo, normals, a, ia, n, exit_pos, exit_view, exit_lens,
               cost=move_seconds):
    pa, _s, la, va = key_geom(geo, normals, a, ia, n)
    return cost(math.dist(pa, exit_pos), _bearing(va, exit_view),
                min(hfov_deg(la), hfov_deg(exit_lens)))


def solve_visit_order(geo, normals, start, rest, n, span_s, deadlines,
                      exit_to=None, idx0=0, pin_last=None):
    """Cheapest visiting order from `start` through `rest`, exactly.

    Held-Karp over the free nodes. The move cost depends on each cluster's
    INDEX in the tour (`camera_station` tilts the station by it), and that is
    not a problem for the DP because the index is |S| - 1, i.e. it is already
    part of the state.

    `deadlines` is {cluster: latest film time it may be presented}. Feasibility
    needs the schedule's scale factor, which needs the tour, so the solve is
    iterated on the scale — twice is enough in practice and it is asserted to
    converge rather than assumed to.
    """
    free = [k for k in rest if k != pin_last]
    m = len(free)
    exitc = None
    scale = 1.0
    best_seq = None
    for _it in range(8):
        INF = float("inf")
        # dp[(mask, last)] = min cost to have visited `mask` and be at free[last]
        dp = {}
        par = {}
        c0 = {}
        for j, b in enumerate(free):
            c = _hop_cost(geo, normals, start, idx0, b, idx0 + 1, n,
                          cost=order_seconds)
            if c * scale <= deadlines.get(b, 1e9):
                dp[(1 << j, j)] = c
                par[(1 << j, j)] = None
            c0[j] = c
        for mask in range(1, 1 << m):
            for last in range(m):
                if not mask & (1 << last):
                    continue
                cur = dp.get((mask, last))
                if cur is None:
                    continue
                depth = bin(mask).count("1")            # == index of `last`
                for nxt in range(m):
                    if mask & (1 << nxt):
                        continue
                    c = cur + _hop_cost(geo, normals, free[last], idx0 + depth,
                                        free[nxt], idx0 + depth + 1, n,
                                        cost=order_seconds)
                    if c * scale > deadlines.get(free[nxt], 1e9):
                        continue
                    key = (mask | (1 << nxt), nxt)
                    if c < dp.get(key, INF):
                        dp[key] = c
                        par[key] = last
        full = (1 << m) - 1
        best, blast = INF, None
        for last in range(m):
            v = dp.get((full, last))
            if v is None:
                continue
            tail = 0.0
            if pin_last is not None:
                tail = _hop_cost(geo, normals, free[last], idx0 + m,
                                 pin_last, idx0 + m + 1, n,
                                 cost=order_seconds)
                if (v + tail) * scale > deadlines.get(pin_last, 1e9):
                    continue
            if exit_to is not None:
                j = idx0 + m + (1 if pin_last else 0)
                tail += _exit_cost(geo, normals,
                                   pin_last if pin_last else free[last],
                                   j, n, *exit_to, cost=order_seconds)
            if v + tail < best:
                best, blast = v + tail, last
        if blast is None:
            raise SystemExit(">> beat 1: no visiting order satisfies the flight "
                             "deadlines; the presentation span is too short")
        seq, mask, last = [], full, blast
        while last is not None:
            seq.append(free[last])
            nl = par[(mask, last)]
            mask ^= (1 << last)
            last = nl
        seq.reverse()
        seq = [start] + seq + ([pin_last] if pin_last else [])
        new_scale = span_s / best
        if best_seq == seq and abs(new_scale - scale) < 1e-9:
            break
        best_seq, scale = seq, new_scale
    return best_seq, best, scale


def present_order(geo, seat_order, normals=None, deadlines=None,
                  spine_span_s=None, corner_span_s=None,
                  spine_exit=None, corner_entry=None):
    """Camera visiting order: solved against the MOVE, not against the inventory.

    The old version used seat order as the spine and only reordered the four
    corners, on the argument that assembly order is roughly centre-outward and
    therefore roughly flyable for free. It is not: seat order sends the camera
    NOSE -> FW -> RW, which is +3.75 m to +4.38 m to -4.59 m, a 9.14 m traverse
    inside one 1.76 s slot. That is the dash the campath gate found.

    Both halves are now solved the same way and by the same cost:

      * the SPINE (everything that is not a corner) — from MB, which is the
        film's first frame and stays there, through the other ten, ending
        wherever leaves the shortest run into the RW -> corner bridge.
      * the FOUR CORNERS, which seat SIMULTANEOUSLY and so impose no order on
        each other. CORNER_FL is pinned LAST because BEAT1_CLOSEOUT is authored
        out of its station — "CORNER_FL sweeps past the lens 1.2 m out on the
        left" — and the close-out is the part of beat 1 that already works.

    The corners used to be ordered by centre-to-centre DISTANCE, which is not
    the cost the camera pays: two stations 1.02 m apart can be 87 degrees apart
    in bearing, and that is exactly the pair (bridge -> CORNER_RL) that produced
    beat 1's worst rotation.
    """
    corners = [k for k in seat_order if k.startswith("CORNER_")]
    spine = [k for k in seat_order if not k.startswith("CORNER_")]
    if normals is None or deadlines is None:
        return spine + corners          # geometry-free fallback; gated below
    n = len(spine) + len(corners)
    sp_seq, _c, _s = solve_visit_order(
        geo, normals, spine[0], spine[1:], n, spine_span_s, deadlines,
        exit_to=spine_exit, idx0=0)
    # The corner tour starts from the BRIDGE, not from a cluster, so it is
    # solved as its own little problem with the bridge as the fixed entry.
    co_seq = _solve_corner_order(geo, normals, corners, n, len(spine),
                                 corner_entry)
    return sp_seq + co_seq


def _solve_corner_order(geo, normals, corners, n, idx0, entry):
    """Four corners, CORNER_FL last, entered from the bridge. 3! = 6 tours."""
    import itertools
    free = [k for k in corners if k != "CORNER_FL"]
    best, bseq = None, None
    for perm in itertools.permutations(free):
        seq = list(perm) + ["CORNER_FL"]
        tot, prev = 0.0, None
        for i, k in enumerate(seq):
            if i == 0:
                tot += _exit_cost(geo, normals, k, idx0 + i, n, *entry,
                                  cost=order_seconds)
            else:
                tot += _hop_cost(geo, normals, prev, idx0 + i - 1, k, idx0 + i,
                                 n, cost=order_seconds)
            prev = k
        if best is None or tot < best:
            best, bseq = tot, seq
    return bseq


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


def _fixed_key_geom(k):
    """(station, unit view, lens) for a hand-authored key such as a bridge."""
    d = [k["look_at"][i] - k["world"][i] for i in range(3)]
    m = math.sqrt(sum(x * x for x in d)) or 1.0
    return list(k["world"]), [x / m for x in d], k["lens_mm"]


def _allocate(costs, span_s):
    """Spread `span_s` over consecutive moves in proportion to what they cost.

    THIS IS THE WHOLE RE-TIMING.  The old schedule paid every move the same
    1.76 s; this pays each one its share of the same total, so a 1.0 m hop with
    no pan is cheap and a 9 m traverse is not affordable at all — which is why
    the visiting order no longer contains one.

    Because every constraint in `move_seconds` scales as 1/dt, proportional IS
    minimax: it leaves every move the same distance from its own worst limit.
    That distance is returned as `ratio`; 1.0 means the segment fits exactly,
    above 1.0 means it does not and by how much.
    """
    tot = sum(costs)
    if tot <= 0:
        raise SystemExit(">> beat 1: zero total move cost")
    k = span_s / tot
    return [c * k for c in costs], tot / span_s


def build_beat1(geo, plan, dur, normals=None, deadlines=None):
    n = len(plan["seat_order"])
    # Reserve the last 20% for the final settle and the push toward the car, so
    # the presentations occupy the first 80% and every part is seen before the
    # corners land together.  That reservation is NOT a gap: see BEAT1_CLOSEOUT.
    slot = dur * 0.80 / n                       # 1.76 s — the OLD uniform slot,
    #                                             kept only to derive the two
    #                                             times below, which are pinned.
    # CORNER_FL LANDS ON THE SLOT IT ALWAYS HAD.  Everything at or after this
    # time — CORNER_FL's presentation and the whole close-out — is byte-for-byte
    # what shipped, because the contact-sheet review reads frames 591-792 as the
    # best material in the film and nothing here is allowed to disturb it.
    corner_last_t = round(dur * 0.80 - slot, 3)              # 24.64 s, frame 591
    # The bridges are pinned to a SEAT time (the engine cover lands 432-440), and
    # seat times do not move, so neither do they.
    b1_t = BEAT1_BRIDGES[0]["t"]                             # 18.10 s, frame 434
    b2_t = BEAT1_BRIDGES[1]["t"]                             # 18.60 s, frame 446
    bridge1 = _fixed_key_geom(BEAT1_BRIDGES[0])
    bridge2 = _fixed_key_geom(BEAT1_BRIDGES[1])

    order = present_order(geo, plan["seat_order"], normals, deadlines,
                          spine_span_s=b1_t,
                          corner_span_s=corner_last_t - b2_t,
                          spine_exit=bridge1, corner_entry=bridge2)
    n_spine = len([k for k in plan["seat_order"] if not k.startswith("CORNER_")])
    spine, corners = order[:n_spine], order[n_spine:]

    # ---- the two solved schedules ------------------------------------------
    sp_costs = [_hop_cost(geo, normals, spine[i], i, spine[i + 1], i + 1, n)
                for i in range(len(spine) - 1)]
    sp_costs.append(_exit_cost(geo, normals, spine[-1], len(spine) - 1, n, *bridge1))
    sp_dt, sp_ratio = _allocate(sp_costs, b1_t)

    co_costs = [_exit_cost(geo, normals, corners[0], n_spine, n, *bridge2)]
    co_costs += [_hop_cost(geo, normals, corners[i], n_spine + i,
                           corners[i + 1], n_spine + i + 1, n)
                 for i in range(len(corners) - 1)]
    co_dt, co_ratio = _allocate(co_costs, corner_last_t - b2_t)
    budget = {"spine": sp_ratio, "corners": co_ratio}
    print(f">> beat 1 BUDGET RATIO: spine {sp_ratio:.3f}, corners "
          f"{co_ratio:.3f}  (1.000 = the segment fits its span exactly; above "
          f"1.000 every move in it is squeezed by that factor)")

    # ---- ON THE FRAME, BECAUSE THE RIG PUTS IT THERE ANYWAY ----------------
    #
    # anim/build_camera_rig.py inserts every key at `int(round(t * FPS))`. A
    # sheet that says 22.87 s and a sheet that says 22.875 s build the SAME
    # keyframe, so a solved time that is not on a frame is a number that claims
    # a precision the film does not have -- and, worse, it makes a diff against
    # the previous sheet look like a change where there is none. The solved
    # times are therefore quantised here, and the result is asserted to be
    # strictly increasing: two keys on one frame would silently delete one.
    def on_frame(t):
        return round(round(t * 24.0) / 24.0, 6)

    times = {}
    t = 0.0
    for i, k in enumerate(spine):
        times[k] = on_frame(t)
        t += sp_dt[i]
    t = b2_t
    for i, k in enumerate(corners):
        t += co_dt[i]
        times[k] = on_frame(t)
    seq_f = [int(round(times[k] * 24)) for k in order]
    assert all(b > a for a, b in zip(seq_f, seq_f[1:])), (
        f"two presentations quantised onto the same frame: {seq_f}")
    # The pin is arithmetic, not aspiration -- and it is a pin on the FRAME.
    # Frames 591-792 (CORNER_FL's presentation and the whole close-out) are the
    # part of beat 1 the contact-sheet review calls the best material in the
    # film, and they must come out of this rebuild unchanged.
    assert int(round(times[corners[-1]] * 24)) == int(round(corner_last_t * 24)), (
        f"CORNER_FL landed on frame {times[corners[-1]] * 24}, not its pinned "
        f"{corner_last_t * 24}")

    keys, sched = [], []
    for i, k in enumerate(order):
        g = geo[k]
        nd = (normals or {}).get(k, {}).get("normal")
        pos, standoff, lens, _v = key_geom(geo, normals, k, i, n)
        t = times[k]
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
        nxt = (times[order[i + 1]] if i + 1 < len(order)
               else BEAT1_CLOSEOUT[0]["t"])
        if i == n_spine - 1:
            nxt = b1_t
        sched.append({
            "cluster": k, "n_parts": g["n_parts"], "tris": g["tris"],
            "presented_t": t, "presented_until_t": round(nxt, 4),
            "seat_t": None, "seen_before_seat": None,
        })

    # Seating: mechanical order, staggered, with the four corners simultaneous.
    #
    # THIS IS THE ONE THING IN BEAT 1 THAT MUST NOT MOVE.  world/beat1_anim.blend
    # was BUILT from these times (MB 333, FD 366, ... corners 696) and it is not
    # rebuilt here, so a change to `seat_start`, `seat_span` or the seat order
    # would silently desynchronise the parts from the camera.  The presentation
    # schedule above is derived independently and only has to stay AHEAD of it.
    seat_start = dur * 0.42
    seat_span = dur * 0.50
    seat_spine = [k for k in plan["seat_order"] if not k.startswith("CORNER_")]
    seat_corners = [k for k in plan["seat_order"] if k.startswith("CORNER_")]
    per = seat_span / (len(seat_spine) + 1)
    seat_t = {}
    for i, k in enumerate(seat_spine):
        seat_t[k] = round(seat_start + i * per, 3)
    for k in seat_corners:
        seat_t[k] = round(seat_start + len(seat_spine) * per, 3)   # simultaneous

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
    return order, keys, sched, path_len, budget


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
    """Per-key speed, PAN RATE and clearance, in the units the picture is in.

    A COUNT OF KEYS IS NOT A MEASUREMENT.  R2-029 shipped because the continuity
    gate measured position jumps and rotation steps, and a slow straight move
    through a car has neither.  So this measures the quantities that move
    actually has wrong: how fast the camera goes, how fast it turns, and how
    close it gets to the car -- sampled BETWEEN keys, not at them, because the
    defect was entirely between two keys.

    R2-062 ADDED THE LAST TWO COLUMNS, AND THEY MATTER MORE THAN THE FIRST.  The
    only speed check here was `SPEED_LIMIT_MS = 6.0`, three times beat 1's own
    declared 1.994 m/s mean, so the 7.82 m/s dash at f387-416 passed it with
    0.8 m/s to spare while being unwatchable.  The two limits are different
    questions and both are now asked:

        SPEED_LIMIT_MS                  can a drone fly this at all
        BEAT1_DESIGN_SPEED_MS x FACTOR  is this the weave the beat sheet says
                                        it is, or is it a dash
        BEAT1_PAN_LIMIT_WIDTHS          can the frame be read while it turns

    Peaks are ESTIMATED from the chord/dt mean by EASE_PEAK, because this runs
    before any curve exists.  The authority is `tools/continuity_gate.py
    --campath` on the built per-frame path; this is the pre-flight that stops a
    sheet reaching it.
    """
    rows, worst_clear, worst_speed = [], (1e9, None), (0.0, None)
    worst_peak, worst_pan = (0.0, None), (0.0, None)
    for i in range(1, len(keys)):
        a, b = keys[i - 1], keys[i]
        dt = max(b["t"] - a["t"], 1e-9)
        d = math.dist(a["world"], b["world"])
        v = d / dt
        va, vb = _fixed_key_geom(a)[1], _fixed_key_geom(b)[1]
        bear = _bearing(va, vb)
        hf = min(hfov_deg(a["lens_mm"]), hfov_deg(b["lens_mm"]))
        peak = v * EASE_PEAK_HI
        peak_lo = v * EASE_PEAK_LO
        pan = (bear * EASE_PEAK_HI / dt) / fps / hf       # frame widths / frame
        pan_lo = (bear * EASE_PEAK_LO / dt) / fps / hf
        # sample the straight chord between the keys; the spline bows outward
        # from it, so the chord is the pessimistic case for clearance
        clear = min(_box_dist([a["world"][c] + (b["world"][c] - a["world"][c]) * u / 40.0
                               for c in range(3)], CAR_BOX_LO, CAR_BOX_HI)
                    for u in range(41))
        rows.append({"from": a.get("focus_target"), "to": b.get("focus_target"),
                     "t": [a["t"], b["t"]],
                     "frames": [int(round(a["t"] * fps)), int(round(b["t"] * fps))],
                     "chord_m": round(d, 3), "speed_ms": round(v, 3),
                     "peak_speed_ms": round(peak, 3),
                     "peak_speed_ms_lo": round(peak_lo, 3),
                     "bearing_deg": round(bear, 2),
                     "peak_pan_widths_per_frame": round(pan, 4),
                     "peak_pan_widths_per_frame_lo": round(pan_lo, 4),
                     "min_clearance_m": round(clear, 3),
                     "lens_mm": [a["lens_mm"], b["lens_mm"]]})
        if clear < worst_clear[0]:
            worst_clear = (clear, rows[-1])
        if v > worst_speed[0]:
            worst_speed = (v, rows[-1])
        if peak > worst_peak[0]:
            worst_peak = (peak, rows[-1])
        if pan > worst_pan[0]:
            worst_pan = (pan, rows[-1])
    return rows, worst_clear, worst_speed, worst_peak, worst_pan



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

    # ---- WHEN EACH CLUSTER STOPS BEING WHERE ITS STATION SAYS IT IS ---------
    #
    # A presentation station is `explode_offset + bbox_centre` plus a standoff,
    # i.e. it is solved against the cluster's EXPLODED position. The cluster is
    # only there until it starts FLYING, which is `flight_s` before it lands --
    # not until it lands. Presenting after that aims a solved station at empty
    # air. So the visiting order is constrained by the flight START, with a
    # margin, and world/beat1_anim_anim.json is the file the part animation was
    # actually built from, so it is the one that gets to say when.
    anim_p = os.path.join(R2, "world/beat1_anim_anim.json")
    anim = json.load(open(anim_p)) if os.path.exists(anim_p) else {}
    flight_f = float(anim.get("flight_s", 1.55)) * 24
    PRESENT_MARGIN_S = 0.5
    deadlines = {c: (v["seat_frame"] - flight_f) / 24.0 - PRESENT_MARGIN_S
                 for c, v in anim.get("clusters", {}).items()}
    if deadlines:
        tight = sorted(deadlines.items(), key=lambda kv: kv[1])[:3]
        print(">> presentation deadlines (flight start less a %.1f s margin), "
              "tightest three: " % PRESENT_MARGIN_S
              + ", ".join(f"{c} {t:.2f} s" for c, t in tight))
    else:
        print(">> WARNING: no world/beat1_anim_anim.json; the visiting order is "
              "unconstrained and a cluster may be presented after it has flown")

    order, b1keys, sched, path_len, budget = build_beat1(
        geo, plan, BEATS[0][1], normals, deadlines)
    mean_speed = path_len / BEATS[0][1]
    if check:
        print(f">> GATING AN EXISTING SHEET: {check}  (nothing will be written)")
        b1keys = json.load(open(check))["beat1"]["camera_keys"]
        path_len = sum(math.dist(b1keys[i - 1]["world"], b1keys[i]["world"])
                       for i in range(1, len(b1keys)))
        mean_speed = path_len / BEATS[0][1]

    unseen = [s["cluster"] for s in sched if not s["seen_before_seat"]]

    # ---- GATE: does beat 1's camera actually miss the car? (R2-029) ---------
    flight, worst_clear, worst_speed, worst_peak, worst_pan = \
        beat1_flight_check(b1keys)
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
    # ---- GATE: IS IT A WEAVE OR A DASH?  R2-062. ----------------------------
    #
    # A move FAILS only when the WHOLE predicted range is out of spec. When the
    # range straddles the limit this instrument cannot tell, says so, and leaves
    # the verdict to `tools/continuity_gate.py --campath` on the built path.
    peak_limit = BEAT1_DESIGN_SPEED_MS * BEAT1_PEAK_FACTOR
    flight_warn = []
    for r in flight:
        if r["peak_speed_ms_lo"] > peak_limit:
            flight_fail.append(
                "the camera peaks at %.2f-%.2f m/s between frames %d and %d "
                "(%s -> %s, %.3f m in %.2f s); beat 1 declares a %.2f m/s weave "
                "and a move may not peak above %.1fx that (%.2f m/s)"
                % (r["peak_speed_ms_lo"], r["peak_speed_ms"], r["frames"][0],
                   r["frames"][1], r["from"], r["to"], r["chord_m"],
                   r["t"][1] - r["t"][0], BEAT1_DESIGN_SPEED_MS,
                   BEAT1_PEAK_FACTOR, peak_limit))
        elif r["peak_speed_ms"] > peak_limit:
            flight_warn.append(
                "f%d-%d %s -> %s peaks at %.2f-%.2f m/s against a %.2f m/s "
                "limit: INSIDE THIS INSTRUMENT'S RESOLUTION. The per-frame "
                "campath gate decides."
                % (r["frames"][0], r["frames"][1], r["from"], r["to"],
                   r["peak_speed_ms_lo"], r["peak_speed_ms"], peak_limit))
        if r["peak_pan_widths_per_frame_lo"] > BEAT1_PAN_LIMIT_WIDTHS:
            flight_fail.append(
                "the camera sweeps %.1f-%.1f %% of its own frame width per frame "
                "between frames %d and %d (%s -> %s, %.1f deg of bearing in "
                "%.2f s at %.0f mm); above %.0f %% the detail in a presentation "
                "is lost"
                % (100.0 * r["peak_pan_widths_per_frame_lo"],
                   100.0 * r["peak_pan_widths_per_frame"], r["frames"][0],
                   r["frames"][1], r["from"], r["to"], r["bearing_deg"],
                   r["t"][1] - r["t"][0], max(r["lens_mm"]),
                   100.0 * BEAT1_PAN_LIMIT_WIDTHS))
        elif r["peak_pan_widths_per_frame"] > BEAT1_PAN_LIMIT_WIDTHS:
            flight_warn.append(
                "f%d-%d %s -> %s sweeps %.1f-%.1f %% of frame width per frame "
                "against a %.0f %% limit: INSIDE THIS INSTRUMENT'S RESOLUTION."
                % (r["frames"][0], r["frames"][1], r["from"], r["to"],
                   100.0 * r["peak_pan_widths_per_frame_lo"],
                   100.0 * r["peak_pan_widths_per_frame"],
                   100.0 * BEAT1_PAN_LIMIT_WIDTHS))

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
    # `anim` and `flight_f` are loaded above, where the visiting order needs them.
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
            "max_estimated_peak_speed_ms": round(worst_peak[0], 3),
            "max_estimated_pan_widths_per_frame": round(worst_pan[0], 4),
            "car_box": {"lo": list(CAR_BOX_LO), "hi": list(CAR_BOX_HI),
                        "clearance_floor_m": CAR_CLEAR_M,
                        "speed_limit_ms": SPEED_LIMIT_MS,
                        "measured_on": "world/beat1_anim.blend"},
            "weave_spec": {
                "design_speed_ms": BEAT1_DESIGN_SPEED_MS,
                "peak_factor": BEAT1_PEAK_FACTOR,
                "peak_speed_limit_ms": round(BEAT1_DESIGN_SPEED_MS
                                             * BEAT1_PEAK_FACTOR, 3),
                "pan_limit_widths_per_frame": BEAT1_PAN_LIMIT_WIDTHS,
                "ease_speak_peak_over_mean": [EASE_PEAK_LO, EASE_PEAK_HI],
                "ease_rotation_peak_over_mean": [EASE_ROT_LO, EASE_ROT_HI],
                "dwell_s": DWELL_S,
                "budget_ratio": {k: round(v, 4) for k, v in budget.items()},
                "note": "each move is given time in proportion to whichever of "
                        "its three constraints (dwell, transit at the peak "
                        "speed limit, turn at the pan limit) needs the most, "
                        "which is the exact minimax split; the visiting order "
                        "is the one that minimises the total. budget_ratio is "
                        "how far the tightest move in each segment is from its "
                        "limit -- above 1.0 the segment is over-subscribed and "
                        "every move in it is squeezed by that factor. Peaks "
                        "here are ESTIMATED and the rotation estimate is weak; "
                        "the authority is tools/continuity_gate.py --campath on "
                        "the built path.",
            },
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
        # AND THE CARRY-FORWARD WAS ONLY ONE LEVEL DEEP, WHICH IS NOT ENOUGH.
        # `speed_ramps` IS authored here, so it was rewritten whole -- and
        # author_beats2_5.py annotates the entry inside it with
        # `min_world_time_scale_note`, the paragraph recording that the 0.153719
        # floor is SOLVED and that the 0.20 it replaced integrated to 3.73 s of
        # world time instead of 1.6. Every run of this file silently deleted
        # that paragraph while leaving the number it explains. Same defect, one
        # level down, and it is the annotation that is easy to lose and hard to
        # notice. The merge is now recursive and it NEVER overwrites a value
        # this file authored: it only restores keys that would otherwise vanish.
        dest = os.path.join(DOCS, "beat_sheet.json")
        carried = []

        # A LIST IS ONLY WALKED WHEN ITS ELEMENTS CAN BE IDENTIFIED, and that
        # restriction is the whole safety of this. Zipping two lists by POSITION
        # would merge beat 1's 22nd camera key with a DIFFERENT 22nd camera key
        # the moment the schedule changes -- which is exactly what just changed
        # -- and would restore one cluster's `focus_target` onto another's. So a
        # list is walked only if every element carries one of these keys and the
        # values are unique on BOTH sides; anything else is left alone.
        ID_KEYS = ("beat", "name", "cluster")

        def _index(seq):
            for idk in ID_KEYS:
                if all(isinstance(e, dict) and idk in e for e in seq):
                    ids = [e[idk] for e in seq]
                    if len(set(ids)) == len(ids):
                        return idk, dict(zip(ids, seq))
            return None, None

        def carry(new, old, path=""):
            if isinstance(new, dict) and isinstance(old, dict):
                for k, v in old.items():
                    p = f"{path}.{k}" if path else k
                    if k not in new:
                        new[k] = v
                        carried.append(p)
                    else:
                        carry(new[k], v, p)
            elif isinstance(new, list) and isinstance(old, list) and new and old:
                ka, ia = _index(new)
                kb, ib = _index(old)
                if ka and ka == kb:
                    for ident, a in ia.items():
                        if ident in ib:
                            carry(a, ib[ident], f"{path}[{ident}]")

        if os.path.exists(dest):
            try:
                prev = json.load(open(dest))
            except Exception:
                prev = {}
            carry(out, prev)
        if carried:
            top = sorted({c.split(".")[0].split("[")[0] for c in carried})
            print(">> carried forward from the existing sheet (this file does "
                  "not author them; tools/author_beats2_5.py does): "
                  + ", ".join(top))
            nested = [c for c in carried if "." in c or "[" in c]
            if nested:
                print(">>   ... including nested annotations this file would "
                      "otherwise have deleted: " + ", ".join(sorted(nested)))
            print(">> RE-RUN tools/author_beats2_5.py if beat 1's timing or the "
                  "beat durations changed, because beats 2-5 are splined "
                  "against them.")
            if "beat1_2_seam" in out:
                print(">> IN PARTICULAR the `beat1_2_seam` block just carried "
                      "forward is the beat-1 -> beat-2 bridge (R2-064). Its "
                      "first anchor IS beat 1's last key, transcribed, so if "
                      "beat 1's last key moved, that block is now spliced to a "
                      "key that no longer exists and the seam is worse than it "
                      "was before the bridge. It is carried, not re-derived, "
                      "because this file does not author it.")
        json.dump(out, open(dest, "w"), indent=1)

    print(f">> film {total:.1f} s = {out['total_frames']} frames @ 24 fps")
    print(f">> beat 1: {len(order)} clusters, path {path_len:.2f} m, "
          f"mean camera speed {mean_speed:.2f} m/s")
    print(f">> every cluster seen before it seats: "
          f"{'YES' if not unseen else 'NO -> ' + ', '.join(unseen)}")
    print(">> beat 1 VISITING ORDER: " + " -> ".join(order))
    for s in sched:
        flag = "" if s["seen_before_seat"] else "   <-- SEATS UNSEEN"
        dl = deadlines.get(s["cluster"])
        if dl is not None and s["presented_t"] > dl:
            flag += "   <-- PRESENTED AFTER IT HAS FLOWN"
        print(f"   {s['cluster']:<16} present {s['presented_t']:6.2f}s  "
              f"(deadline {dl if dl is None else round(dl, 2)})  "
              f"seat {s['seat_t']:6.2f}s  {s['n_parts']:>3} parts{flag}")
    print(">> beat 1 FLIGHT — chord speed, pan rate and clearance to the "
          "assembled car body, sampled BETWEEN keys")
    for r in flight:
        mark = ""
        if r["min_clearance_m"] < CAR_CLEAR_M:
            mark = "   <-- INSIDE THE CAR" if r["min_clearance_m"] <= 0.0 else \
                   "   <-- TOO CLOSE"
        if r["speed_ms"] > SPEED_LIMIT_MS:
            mark += "   <-- UNFLYABLE"
        lim = BEAT1_DESIGN_SPEED_MS * BEAT1_PEAK_FACTOR
        if r["peak_speed_ms_lo"] > lim:
            mark += "   <-- A DASH, NOT A WEAVE"
        elif r["peak_speed_ms"] > lim:
            mark += "   <-- speed unresolved"
        if r["peak_pan_widths_per_frame_lo"] > BEAT1_PAN_LIMIT_WIDTHS:
            mark += "   <-- PAN SMEARS"
        elif r["peak_pan_widths_per_frame"] > BEAT1_PAN_LIMIT_WIDTHS:
            mark += "   <-- pan unresolved"
        print(f"   f{r['frames'][0]:>4}-{r['frames'][1]:<4} {str(r['from']):<14}"
              f"-> {str(r['to']):<14} {r['chord_m']:6.2f} m  "
              f"{r['speed_ms']:5.2f} m/s (peak {r['peak_speed_ms_lo']:5.2f}-"
              f"{r['peak_speed_ms']:<5.2f})  pan {r['bearing_deg']:5.1f} deg = "
              f"{100*r['peak_pan_widths_per_frame_lo']:4.1f}-"
              f"{100*r['peak_pan_widths_per_frame']:<4.1f} %w/fr  "
              f"clear {r['min_clearance_m']:6.3f} m  "
              f"{r['lens_mm'][0]:.0f}->{r['lens_mm'][1]:.0f} mm{mark}")
    print(f">> beat 1 worst clearance to the car {worst_clear[0]:.3f} m "
          f"(floor {CAR_CLEAR_M}), fastest key-to-key {worst_speed[0]:.2f} m/s "
          f"(flyability limit {SPEED_LIMIT_MS})")
    print(f">> beat 1 estimated worst PEAK speed {worst_peak[0]:.2f} m/s "
          f"(limit {BEAT1_DESIGN_SPEED_MS * BEAT1_PEAK_FACTOR:.2f} = "
          f"{BEAT1_PEAK_FACTOR:.0f}x the declared {BEAT1_DESIGN_SPEED_MS:.2f} "
          f"m/s weave), worst PAN {100*worst_pan[0]:.1f} %% of frame width per "
          f"frame (limit {100*BEAT1_PAN_LIMIT_WIDTHS:.0f} %%)")
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
    for w in flight_warn:
        print("   UNRESOLVED " + w)
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
