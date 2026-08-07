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
                  "size": [round(hi[i] - lo[i], 3) for i in range(3)],
                  # R2-829: the placer needs the BOX, not a sphere around it.
                  # A sphere of the half-diagonal is up to sqrt(3) too big in the
                  # narrow axis, and every cluster here is long and thin.
                  "box_lo": [round(v, 4) for v in lo],
                  "box_hi": [round(v, 4) for v in hi]}
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

# R2-829.  THE FRACTION OF THE FRAME A PRESENTATION IS ALLOWED TO OCCUPY.
#
# This constant already existed -- as a local inside the FRAMING gate in main().
# The gate used it to print "it would fit at X m" for fifteen clusters that did
# not fit, fifteen times, in every run, for weeks. Nothing consumed the number,
# because the thing that CHOSE the distance could not see the lens. It is hoisted
# here so the placer and the gate are held to one number rather than two.
FILL_TARGET = 0.85

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

# ---- the closing lens push.  R2-113. ---------------------------------------
#
# The brief names three things in the last frame -- "the circuit, the car
# streaking on, the breached showroom visible in the distance with its wound".
# R2-090 closed the third of those as geometrically unavailable: at f2978 the
# wound and the car are 966 m apart, and requiring both in frame pushes the
# camera back at exactly the rate a longer lens gains, so the car is pinned at
# about 11.3 px = 1920 * 5.698 / 966 from ANY position at ANY focal length. The
# focal length falls out of the expression entirely. The car's beat is real and
# it lives at f2756-2832, where the car is still 20 to 40 px; it is not the last
# frame, and the last frame is about the wound.
#
# THE REMAINING TWO STILL FIGHT, AND THEY ARE RESOLVED IN SEQUENCE RATHER THAN
# IN ONE FRAME. Measured at the hold, 595.4 m out and 140 m up:
#
#   lens     mullion pitch   sky in frame   the wound        the circuit
#   18.75    3.7 px          29.3 %         20 px, a blob    1143 m, reads
#   40       7.9 px           5.7 %         37 px            536 m, reads best
#   74      14.6 px           0.0 %         65 px, reads     290 m, gone
#
# At 18.75 mm the mullion grid is not resolvable, so the bright opening has no
# grid to be a hole IN and reads as a specular hit. At 74 mm the grid is crisp
# either side of the opening and absent across it, and the empty dais ring is
# legible through the gap -- but the circuit has left the frame and so has the
# sky. So the hold OPENS at 40 mm, where the circuit reads, and PUSHES to 74 mm,
# where the wound reads.
#
# AND THE HOLD WAS A FREEZE. The camera is stationary for the last 3 s -- 0.00 m
# over 72 frames, measured -- so at a fixed lens f2906 and f2978 are the same
# picture: mean |difference| 0.8/255, 56 pixels of 2.07 M differing by more than
# 16. The push is the only motion in the last three seconds, and it leaves the
# camera path untouched: every seam, the aim gate and the 0.00 m hold stay
# exactly as measured.
CLOSING_LENS_HOLD_START_MM = 40.0
CLOSING_LENS_HOLD_END_MM = 74.0


def closing_lens_push(beat6):
    """Retarget beat 6's last two declared lens values. R2-113.

    Nothing else about beat 6 is touched: no key moves, no time changes, and the
    hold's two keys keep their identical positions, so the 3 s hold is still a
    hold. `hold_lens_mm` is updated alongside the key so the summary field and
    the key it summarises cannot disagree -- R2-100 is a fact with two copies
    going stale, and this block would otherwise create one.
    """
    b6 = json.loads(json.dumps(beat6))            # never mutate the spec's dict
    ks = sorted(b6["keys"], key=lambda k: k["t"])
    t0, t1 = b6["hold_start_t"], b6["hold_end_t"]
    hit = 0
    for k in ks:
        if k["t"] == t0:
            k["lens_mm"] = CLOSING_LENS_HOLD_START_MM
            hit += 1
        elif k["t"] == t1:
            k["lens_mm"] = CLOSING_LENS_HOLD_END_MM
            hit += 1
    if hit != 2:
        # A silent no-op here would ship the freeze back. Refuse instead.
        raise SystemExit(
            "R2-113: beat 6's hold keys t=%s and t=%s are not both in "
            "spec['beat6']['keys'] (matched %d) — the closing lens push has "
            "nothing to attach to" % (t0, t1, hit))
    b6["hold_lens_mm"] = CLOSING_LENS_HOLD_END_MM
    b6["closing_lens_push"] = {
        "from_mm": CLOSING_LENS_HOLD_START_MM,
        "to_mm": CLOSING_LENS_HOLD_END_MM,
        "over_t": [t0, t1],
        "why": "R2-113. The circuit reads at 40 mm and the wound does not; the "
               "wound reads at 74 mm and the circuit is gone. The hold was a "
               "freeze, so the push is the only motion in the last 3 s.",
    }
    return b6


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


# --------------------------------------------------------------------------- #
#  THE CORNER GROUP — R2-830.                                                   #
# --------------------------------------------------------------------------- #
#
# THE FOUR CORNERS ARE ONE SUBJECT AND THE FILM SHOT THEM AS FOUR.
#
# `docs/explode_plan.json` declares them a simultaneous group: they seat at the
# same instant and impose no order on each other. They are also, pairwise, the
# same object — CORNER_RL and CORNER_RR are both 745,562 tris, CORNER_FR and
# CORNER_FL both 690,930 — and the project's brief has a no-repeated-assets red
# line. Presenting them one after another cost 9.20 s, 28 % of beat 1, to show
# the audience the same wheel four times at 2.0-2.3x frame overflow, none of them
# legible. That is the single largest recoverable block of time in the beat.
#
# SO THEY GET ONE STATION, and it is a REAL station rather than a bookkeeping
# convenience: the union of the four exploded boxes is a genuine 5.25 x 4.42 x
# 0.72 m subject, it goes through the same R2-829 standoff solve as everything
# else, and the FRAMING gate measures it exactly as it measures the other eleven.
# Nothing here is exempted from a check; a new subject is declared and then
# checked.
#
# THE DIRECTION IS STILL MEASURED. It is the normalised mean of the four measured
# presentation normals, so the group is seen from the direction that the four
# individual measurements agree on. It is not generated, and it is not chosen.
#
# AND IT PAYS TWICE. The four corners' seated positions are the four corners of
# the car, so a station that contains the exploded group contains the assembled
# car — the group's presentation frame IS a whole-car frame. The beat's climax
# and its establishing payoff become the same shot instead of two shots 9 s apart.
CORNER_GROUP = "CORNER_GROUP"


def build_corner_group(geo, plan, normals):
    """Declare the four corners as one subject, in memory only.

    NOT written to docs/explode_plan.json, and deliberately: that file is read by
    `anim/build_beat1_anim.py`, which iterates `clusters` and dereferences
    `parts`. A synthetic cluster there would be animated as a 166-part duplicate
    of four clusters that are already animated. The group is a CAMERA subject and
    it lives only where the camera lives.
    """
    corners = [k for k in plan["seat_order"] if k.startswith("CORNER_")]
    if not corners:
        return None, []
    lo = [min(geo[k]["box_lo"][i] for k in corners) for i in range(3)]
    hi = [max(geo[k]["box_hi"][i] for k in corners) for i in range(3)]
    plan["clusters"][CORNER_GROUP] = {
        "bbox_min": [round(v, 4) for v in lo],
        "bbox_max": [round(v, 4) for v in hi],
        "explode_offset": [0.0, 0.0, 0.0],       # the box is ALREADY exploded
        "n_parts": sum(geo[k]["n_parts"] for k in corners),
        "tris": sum(geo[k]["tris"] for k in corners),
        "parts": [],
        "r2830_members": list(corners),
    }
    geo[CORNER_GROUP] = {
        "centre": [round((lo[i] + hi[i]) / 2, 4) for i in range(3)],
        "radius": round(max(0.5 * math.dist(lo, hi), 0.05), 4),
        "n_parts": sum(geo[k]["n_parts"] for k in corners),
        "tris": sum(geo[k]["tris"] for k in corners),
        "size": [round(hi[i] - lo[i], 3) for i in range(3)],
        "box_lo": [round(v, 4) for v in lo],
        "box_hi": [round(v, 4) for v in hi],
    }
    nsum = [0.0, 0.0, 0.0]
    for k in corners:
        nv = (normals or {}).get(k, {}).get("normal")
        if nv:
            for i in range(3):
                nsum[i] += nv[i]
    m = math.sqrt(sum(v * v for v in nsum))
    if m > 1e-6:
        normals[CORNER_GROUP] = {
            "normal": [round(v / m, 5) for v in nsum],
            "distinct_materials": max(
                (normals.get(k, {}).get("distinct_materials") or 0)
                for k in corners),
            # The mean of four legal directions can leave the legal band, so the
            # group opts INTO the R2-451 clamp rather than inheriting whatever
            # its members happened to carry.
            "r2451_reaimed": True,
            "r2830_mean_of": list(corners),
        }
    return CORNER_GROUP, corners


def lens_for(g):
    """35 mm on the wide clusters, longer on the small dense ones so the
    steering wheel is not presented by shoving the lens 190 mm from it."""
    return 35.0 if g["radius"] > 0.8 else 58.0


_KEY_GEOM_CACHE = {}


def key_geom(geo, normals, k, idx, n):
    """(station, standoff, lens, unit view direction) for a presentation.

    MEMOISED — R2-829. The station is now a fixed-point solve rather than one
    multiplication, and the Held-Karp tour solver evaluates it O(m^2 * 2^m) times
    over the same few hundred (cluster, index) pairs. It is a pure function of
    (cluster, tour index, tour length) given the plan and the normals, both of
    which are loaded once per process, so the cache is keyed on exactly that.
    """
    ck = (k, idx, n, id(geo), id(normals))
    hit = _KEY_GEOM_CACHE.get(ck)
    if hit is not None:
        return hit
    g = geo[k]
    nv = (normals or {}).get(k, {})
    # R2-451.  The clamp engages ONLY for a cluster whose normals entry says it
    # was chosen under the R2-451 law, and the default is OFF.  Two reasons, and
    # the second one is a hazard this file created for five other live agents:
    #
    #  * `r2451_reaimed: false` records a cluster that WAS examined against the
    #    depression cap and could not be moved -- every legal direction it has
    #    breaks beat 1's schedule or its clearance gate. Clamping it anyway does
    #    not produce a legal station, it produces an unschedulable beat.
    #  * A PRE-R2-451 normals file has no markers at all, and clamping all
    #    fifteen of its near-nadir directions to 25 deg makes `present_order()`
    #    raise SystemExit. Defaulting the clamp ON would therefore have broken
    #    `build_beatsheet.py` for anyone running it against the shipped
    #    `docs/presentation_normals.json` -- in a shared working tree, from the
    #    moment the edit was saved and before anything was committed.
    #
    # So the backstop protects data that opted into the law and never retrofits
    # itself onto data that did not.
    legalise = nv.get("r2451_reaimed", False)
    # R2-829: the lens is chosen BEFORE the distance, because the distance now
    # depends on it. It always did depend on it; the code just could not say so.
    lens = float(nv.get("r2429_lens_mm") or lens_for(g))
    box = ((g["box_lo"], g["box_hi"]) if "box_lo" in g else None)
    pos, standoff = camera_station(g["centre"], g["radius"], idx, n,
                                   nv.get("normal"), legalise=legalise,
                                   standoff_override=nv.get("r2429_standoff_m"),
                                   box=box, lens_mm=lens)
    d = [g["centre"][i] - pos[i] for i in range(3)]
    m = math.sqrt(sum(x * x for x in d)) or 1.0
    out = (pos, standoff, lens, [x / m for x in d])
    _KEY_GEOM_CACHE[ck] = out
    return out


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


# --------------------------------------------------------------------------- #
#  THE SEAT SCHEDULE — R2-831, and the two constants that caused "way too slow". #
# --------------------------------------------------------------------------- #
#
#     seat_start = dur * 0.42
#     seat_span  = dur * 0.50
#
# 0.42 + 0.50 = 0.92. Assembly completed at 92 % of beat 1 BY CONSTRUCTION, for
# any value of `dur`, leaving the remaining 8 % as the payoff — 4.0 s of a 33 s
# beat, 12 %. The client's note was "way too slow I feel", and the mechanism is
# not that the camera moves slowly. It is that the beat spends its energy where
# there is nothing to see and goes still the moment there is: measured frame-to-
# frame image change is 20.27 across the unreadable tour and 4.89 across the
# readable payoff, a 4.14x collapse exactly where the subject finally appears.
#
# THE INTUITIVE FIX IS BACKWARDS. Shortening beat 1 to 24 s — the obvious answer
# to "too slow" — completes assembly at 22.08 s and leaves a 1.92 s payoff. It
# MORE THAN HALVES the thing the client is waiting for, because everything here
# is expressed as a fraction of `dur`, and it costs an audio-master rebuild for a
# strictly worse result. Beat 1 stays 33.0 s and the film stays 124.0833 s.
#
# 0.30 / 0.36 WAS THE PLAN. IT IS NOT FLYABLE, AND THE SOLVER SAYS SO.
#
# The plan predicted 0.30 / 0.36 -> corners at t = 20.79 s, on a cost model that
# expected the pulled-back stations (R2-829) to make the tour CHEAPER: from
# farther out the bearing between adjacent clusters shrinks, so the pan term
# falls. That half is true. The other half was not modelled: `move_seconds` is
# `max(dwell, transit, pan)`, and pulling the stations back from 1.5-4.9 m to
# 2.3-7.6 m moves them APART, so the TRANSIT term rises and becomes the binding
# one. MEASURED, as minimum flyable tour time:
#
#     shipped 15-node tour, lens-blind stations     18.91 s
#     the SAME tour with lens-aware stations        21.19 s   framing costs 2.28 s
#     the 12-node grouped tour, lens-aware          17.29 s   grouping saves 3.90 s
#
# So the framing fix really does cost time and the corner group really does pay
# for it, and the net is 1.62 s FASTER than what shipped. What the plan got wrong
# was the size: it expected ~6.7 s of recovery and there is 3.90 s.
#
# AND THE TARGET WAS NEVER REACHABLE, WITH OR WITHOUT THE FRAMING FIX. A tour
# that takes 17.29 s to fly, starting at 2.00 s after the establishing lead-in,
# cannot present the corners before 19.29 s, and they may not seat until 2.05 s
# after that (1.55 s of flight plus a 0.5 s margin). The floor is 21.34 s. Even
# the shipped lens-blind geometry could not have seated them before 22.96 s.
# 20.79 s was not a schedule that the framing fix took away; it was never on the
# table.
#
# MEASURED, not asserted — a 21 x 20 grid over (start, span), each cell a full
# Held-Karp solve against that cell's own deadlines:
#
#     0.30 / 0.36    NO visiting order exists, at any speed the beat allows
#     0.28 / 0.40    corners t 21.340 s   the earliest feasible point on the grid
#     0.30 / 0.38    corners t 21.395 s   <- SHIPPED
#     0.42 / 0.50    corners t 28.985 s   what shipped before
#
# The frontier is flat: every feasible pair has `start + 11*span/12` ~ 0.647, so
# trading start against span moves the answer by hundredths of a second and the
# choice between them is free. 0.30 is therefore kept exactly as briefed and the
# span alone absorbs the difference, which makes the deviation from the plan one
# number instead of two.
#
# 0.30 / 0.38 puts the four corners down at t = 21.395 s (frame 513), last part
# settled at frame 521, and the payoff becomes 11.29 s instead of 4.01 s — 2.81x,
# against the 3.05x the plan hoped for. The missing 0.6 s is the price of the
# framing fix, and it is the right trade: there is no schedule in which the car
# assembles earlier AND every part is legible when it is shown.
BEAT1_SEAT_START_FRAC = 0.30
BEAT1_SEAT_SPAN_FRAC = 0.38


def seat_schedule(plan, dur):
    """{cluster: seat time}. Mechanical order, staggered, corners simultaneous.

    THE ONE PLACE THIS IS COMPUTED. It used to live inside `build_beat1`, which
    meant the presentation DEADLINES — which are derived from it — were read from
    `world/beat1_anim_anim.json` instead, i.e. from the last build of a 291 MB
    blend. The two could disagree and nothing compared them; see the desync check
    in `main()`, which now does.
    """
    spine = [k for k in plan["seat_order"] if not k.startswith("CORNER_")]
    corners = [k for k in plan["seat_order"] if k.startswith("CORNER_")]
    start = dur * BEAT1_SEAT_START_FRAC
    span = dur * BEAT1_SEAT_SPAN_FRAC
    per = span / (len(spine) + 1)
    seat_t = {k: round(start + i * per, 3) for i, k in enumerate(spine)}
    for k in corners:
        seat_t[k] = round(start + len(spine) * per, 3)   # simultaneous
    return seat_t


def solve_visit_order(geo, normals, start, rest, n, span_s, deadlines,
                      exit_to=None, idx0=0, pin_last=None, t0=0.0):
    """Cheapest visiting order from `start` through `rest`, exactly.

    Held-Karp over the free nodes. The move cost depends on each cluster's
    INDEX in the tour (`camera_station` tilts the station by it), and that is
    not a problem for the DP because the index is |S| - 1, i.e. it is already
    part of the state.

    `deadlines` is {cluster: latest film time it may be presented}, in FILM time;
    `t0` is when the tour starts, and leaving it out is how the shipped sheet
    presented FD at 14.54 s against a 13.20 s deadline while the solver believed
    it was inside it. The old code compared a cost measured from the tour's start
    against a deadline measured from the beat's start, and the establishing
    lead-in is 2.0 s of difference between those two origins.
    R2-832.

    THE FEASIBILITY TEST IS NOW THE MINIMUM-TIME SCHEDULE, not a guessed scale.
    A move cannot be flown faster than `move_seconds`, so if the cumulative
    `move_seconds` to reach a cluster already exceeds its deadline, no allocation
    of any span can rescue it — the tour is infeasible, full stop, and no
    iteration on a scale factor is needed to know that. The old loop guessed a
    scale, filtered against it, then re-derived the scale from the filtered
    answer; it converged on self-consistency rather than on feasibility.

    Returns (sequence, order_cost, move_cost_to_each) — the third is what the
    caller needs to choose the largest span that still meets every deadline.
    """
    free = [k for k in rest if k != pin_last]
    m = len(free)
    INF = float("inf")

    def mhop(a, ia, b, ib):
        return _hop_cost(geo, normals, a, ia, b, ib, n, cost=move_seconds)

    def ohop(a, ia, b, ib):
        return _hop_cost(geo, normals, a, ia, b, ib, n, cost=order_seconds)

    # dp[(mask, last)] = (min order cost, move cost along that same path)
    dp, par = {}, {}
    for j, b in enumerate(free):
        mc = mhop(start, idx0, b, idx0 + 1)
        if t0 + mc <= deadlines.get(b, 1e9) + 1e-9:
            dp[(1 << j, j)] = (ohop(start, idx0, b, idx0 + 1), mc)
            par[(1 << j, j)] = None
    for mask in range(1, 1 << m):
        for last in range(m):
            if not mask & (1 << last):
                continue
            cur = dp.get((mask, last))
            if cur is None:
                continue
            oc, mc = cur
            depth = bin(mask).count("1")               # == index of `last`
            for nxt in range(m):
                if mask & (1 << nxt):
                    continue
                mc2 = mc + mhop(free[last], idx0 + depth,
                                free[nxt], idx0 + depth + 1)
                if t0 + mc2 > deadlines.get(free[nxt], 1e9) + 1e-9:
                    continue
                oc2 = oc + ohop(free[last], idx0 + depth,
                                free[nxt], idx0 + depth + 1)
                key = (mask | (1 << nxt), nxt)
                if oc2 < (dp.get(key) or (INF, 0.0))[0]:
                    dp[key] = (oc2, mc2)
                    par[key] = last
    full = (1 << m) - 1
    best, blast, best_tail = INF, None, None
    for last in range(m):
        v = dp.get((full, last))
        if v is None:
            continue
        oc, mc = v
        o_tail, m_tail = 0.0, 0.0
        if pin_last is not None:
            o_tail = ohop(free[last], idx0 + m, pin_last, idx0 + m + 1)
            m_tail = mhop(free[last], idx0 + m, pin_last, idx0 + m + 1)
            if t0 + mc + m_tail > deadlines.get(pin_last, 1e9) + 1e-9:
                continue
        if exit_to is not None:
            j = idx0 + m + (1 if pin_last else 0)
            o_tail += _exit_cost(geo, normals,
                                 pin_last if pin_last else free[last],
                                 j, n, *exit_to, cost=order_seconds)
        if oc + o_tail < best:
            best, blast, best_tail = oc + o_tail, last, None
    if blast is None:
        raise SystemExit(
            ">> beat 1: NO visiting order meets the flight deadlines even at the "
            "minimum time every move needs. The tour cannot be flown before the "
            "parts it is a tour of have left their stations. Widen the seat "
            "schedule (BEAT1_SEAT_SPAN_FRAC) or pull the stations back further.")
    seq, mask, last = [], full, blast
    while last is not None:
        seq.append(free[last])
        nl = par[(mask, last)]
        mask ^= (1 << last)
        last = nl
    seq.reverse()
    seq = [start] + seq + ([pin_last] if pin_last else [])
    return seq, best


def present_order(geo, seat_order, normals=None, deadlines=None, t0=0.0):
    """Camera visiting order: solved against the MOVE, not against the inventory.

    Seat order is not a visiting order. It is centre-outward in ASSEMBLY, not in
    space, and following it sends the camera NOSE -> FW -> RW, +3.75 m to +4.38 m
    to -4.59 m, a 9.14 m traverse in one slot. That is the dash the campath gate
    found, and this is solved instead.

    ONE TOUR, TWELVE NODES — R2-830. It used to be two solves: a spine of eleven,
    then the four corners as their own little problem entered from a bridge. The
    four corners are now ONE node (`CORNER_GROUP`), so there is one tour: from MB,
    which is the film's first frame and stays there, through the other ten, ending
    on the corner group, which is pinned last because it is the beat's climax and
    the close-out is authored out of its station.

    The corners used to be ordered by centre-to-centre DISTANCE, which is not the
    cost the camera pays: two stations 1.02 m apart can be 87 degrees apart in
    bearing. That ordering problem no longer exists, because there is nothing left
    to order — they seat simultaneously and they are now shot simultaneously.
    """
    corners = [k for k in seat_order if k.startswith("CORNER_")]
    spine = [k for k in seat_order if not k.startswith("CORNER_")]
    if normals is None or deadlines is None:
        return spine + corners          # geometry-free fallback; gated below
    nodes = spine + ([CORNER_GROUP] if CORNER_GROUP in geo else corners)
    n = len(nodes)
    seq, cost = solve_visit_order(
        geo, normals, spine[0], nodes[1:], n, None, deadlines,
        idx0=0, pin_last=(CORNER_GROUP if CORNER_GROUP in geo else None), t0=t0)
    return seq


# --------------------------------------------------------------------------- #
#  THE STANDOFF LAW — R2-829.  A distance that cannot see the lens is a guess.   #
# --------------------------------------------------------------------------- #
#
# WHAT WAS THERE, for the whole of round 2:
#
#     standoff = max(radius * 1.55 + 0.42, 0.75)
#
# It is a function of the SUBJECT alone. It fixes the subtended angle at ~80 deg
# and then the picture is taken with whatever lens `lens_for()` hands back — 35 mm
# on the big clusters, 58 mm on the small dense ones. An 80 deg subject through a
# 58 mm lens (a 31.6 deg horizontal field) is a subject two and a half times wider
# than the picture, and that is not a marginal miss, it is the arithmetic working
# exactly as written. Every one of the fifteen presentations overflowed its own
# frame, 1.11x to 2.32x, and the gate said so on every run.
#
# THE REPLACEMENT MEASURES THE PICTURE, not a proxy for it. The subject is not a
# sphere of the bbox half-diagonal — it is eight bounding-box corners, projected
# through the real lens from the real direction, and what matters is the extent of
# that projection on the sensor. So the law is stated as the thing we actually
# want and then solved for:
#
#     max(extent_h / SENSOR_H, extent_w / SENSOR_W) == FILL_TARGET
#
# SOLVED, NOT APPROXIMATED. Projected extent falls as ~1/distance but not exactly,
# because a box near the lens is not a small object: the near face is magnified
# relative to the far one and the perspective term does not scale. So this is a
# fixed point, `s <- s * fill / FILL_TARGET`, iterated on the true projection until
# it stops moving. It converges in three or four passes and the caller asserts
# that it converged rather than assuming it.
#
# WHY THIS IS COUPLED TO THE DIRECTION AND SOLVED JOINTLY WITH IT. The elevation
# clamp (`_legalise_station_dir`, R2-451) depends on the standoff — it is the
# standoff that decides whether a given depression puts the lens through the
# ceiling or under the rope barrier. And the standoff depends on the direction,
# because a box is not the same width from every side. Solving either one first
# and then the other gives a station that satisfies whichever was solved second.
# They are therefore iterated together.
def _cam_basis(fwd):
    """Right/up for a forward direction, matching the FRAMING gate's `_basis`."""
    wu = [0.0, 0.0, 1.0]
    if abs(sum(fwd[i] * wu[i] for i in range(3))) > 0.999:
        wu = [0.0, 1.0, 0.0]
    rt = [fwd[1] * wu[2] - fwd[2] * wu[1],
          fwd[2] * wu[0] - fwd[0] * wu[2],
          fwd[0] * wu[1] - fwd[1] * wu[0]]
    m = math.sqrt(sum(x * x for x in rt)) or 1.0
    rt = [x / m for x in rt]
    up = [rt[1] * fwd[2] - rt[2] * fwd[1],
          rt[2] * fwd[0] - rt[0] * fwd[2],
          rt[0] * fwd[1] - rt[1] * fwd[0]]
    return rt, up


def frame_fill(cam, centre, box_lo, box_hi, lens_mm):
    """Fraction of the frame the box's projection occupies, worst of h and w.

    This is the FRAMING gate's own measurement, lifted so the placer is scored by
    the instrument that judges it. >1.0 means the audience gets a fragment.
    """
    fwd = [centre[i] - cam[i] for i in range(3)]
    m = math.sqrt(sum(x * x for x in fwd)) or 1.0
    fwd = [x / m for x in fwd]
    rt, up = _cam_basis(fwd)
    us, vs = [], []
    for ix in (0, 1):
        for iy in (0, 1):
            for iz in (0, 1):
                p = [box_lo[0] if ix == 0 else box_hi[0],
                     box_lo[1] if iy == 0 else box_hi[1],
                     box_lo[2] if iz == 0 else box_hi[2]]
                dd = [p[i] - cam[i] for i in range(3)]
                z = sum(dd[i] * fwd[i] for i in range(3))
                if z <= 1e-6:
                    return float("inf")        # a corner behind the lens
                us.append(sum(dd[i] * rt[i] for i in range(3)) / z * lens_mm)
                vs.append(sum(dd[i] * up[i] for i in range(3)) / z * lens_mm)
    return max((max(vs) - min(vs)) / SENSOR_H_MM,
               (max(us) - min(us)) / SENSOR_W_MM)


def standoff_for_fill(centre, box_lo, box_hi, d, lens_mm, s0,
                      fill=None, iters=24, tol=1e-4):
    """Distance along `d` at which the box's projection fills `fill` of frame.

    Returns (standoff, converged). `d` points FROM the cluster centre TOWARD the
    camera, which is the convention `camera_station` returns its position in.

    `fill` defaults to the module's FILL_TARGET *at call time*, not at definition
    time. Writing `fill=FILL_TARGET` in the signature binds the value once when
    the module loads, so every sweep over FILL_TARGET silently measures the same
    number — which is exactly what happened on the first attempt at this sweep,
    and it produced four identical rows that looked like a real (null) result.
    """
    fill = FILL_TARGET if fill is None else fill
    s = max(float(s0), 0.05)
    for _ in range(iters):
        cam = [centre[i] + d[i] * s for i in range(3)]
        f = frame_fill(cam, centre, box_lo, box_hi, lens_mm)
        if f == float("inf"):
            s *= 2.0                      # inside the box; walk out and retry
            continue
        s_new = s * f / fill
        if abs(s_new - s) <= tol * max(s, 1.0):
            return s_new, True
        s = s_new
    return s, False


def camera_station(centre, radius, idx, n, look_dir=None, legalise=True,
                   standoff_override=None, box=None, lens_mm=None):
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

    R2-451 — THE STATION MUST BE A CAMERA POSITION, AND THAT IS ENFORCED HERE.
    ------------------------------------------------------------------------
    This function turns a direction into a lens position, so it is the last place
    that can guarantee the result is somewhere a camera could be.  It never did,
    and the film opens 84.15 deg nose-down from z = 5.6607 — above every light in
    the showroom — because whatever `presentation_normals.py` handed it went
    straight through unchecked.

    `presentation_normals.py` now selects inside the same band, so in the normal
    case this clamp is a no-op and the selftest asserts that.  It is here for the
    two ways an illegal station can still arrive:

      * THE WEAVE TILT ITSELF.  `tilt` adds up to 0.0427 to d[2].  A direction
        selected at exactly the 25 deg cap comes out of the tilt at 26.4 deg, so
        the placer can violate a bound the selector respected.
      * A STALE OR HAND-EDITED NORMALS FILE.  The pre-R2-451 file is still on
        disk and reachable by one `--out` flag.

    A clamp preserves AZIMUTH and moves only elevation, because azimuth is the
    measured quantity — it is which face of the part the audience sees, which is
    the whole point of `presentation_normals` — and elevation is the quantity
    that had no constraint on it.
    """
    # THE OLD LAW, kept as the seed for the fixed point and as the fallback for a
    # caller with no box. It is a decent starting distance and a bad final one.
    standoff = max(radius * 1.55 + 0.42, 0.75)
    # R2-464.  An override lets one station be an ESTABLISHING station without
    # repealing the law for the others, and it is data in the normals file rather
    # than a branch here, so the exception is visible in the artefact that
    # records it.  It also wins over the R2-829 solve, deliberately: an override
    # is a hand-placed station and the whole point of it is that it is not solved.
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

    if standoff_override:
        standoff = float(standoff_override)
        if legalise:
            d = _legalise_station_dir(d, centre, standoff)
    elif box is not None and lens_mm and STANDOFF_LENS_AWARE:
        # R2-829.  Direction and distance are solved TOGETHER — see the block
        # above this function for why neither can be solved first.
        conv = False
        for _ in range(8):
            if legalise:
                d = _legalise_station_dir(d, centre, standoff)
            s_new, conv = standoff_for_fill(centre, box[0], box[1], d,
                                            float(lens_mm), standoff)
            if abs(s_new - standoff) <= 1e-4 * max(standoff, 1.0):
                standoff = s_new
                break
            standoff = s_new
        if not conv:
            raise SystemExit(
                ">> R2-829: the standoff fixed point did not converge for a "
                "cluster at %s on a %.0f mm lens (last %.4f m). A station that "
                "is not solved must not be shipped as one." % (centre, lens_mm,
                                                               standoff))
        if legalise:
            d = _legalise_station_dir(d, centre, standoff)
    elif legalise:
        d = _legalise_station_dir(d, centre, standoff)
    return [round(centre[i] + d[i] * standoff, 4) for i in range(3)], round(standoff, 4)


# R2-829.  The lens-aware standoff is ON by default and `B1_LENS_STANDOFF=0`
# reproduces the pre-R2-829 sheet exactly. Same discipline as B1_ESTABLISH: this
# project keeps the arm it must fail, so the arm it must pass is not a vacuous
# pass, and the null for every R2-829 measurement is taken with this off.
STANDOFF_LENS_AWARE = os.environ.get("B1_LENS_STANDOFF", "1").strip() \
    not in ("0", "off", "")

# R2-451.  All four MEASURED, none asserted -- see tools/beat1_nadir_cause.py
# and tools/beat1_reaim.py.
STATION_MAX_DEPRESSION_DEG = float(
    os.environ.get("B1_MAX_DEPRESSION", "25.0"))   # deepest hand-authored key
# B1_MAX_DEPRESSION=90 disables the clamp entirely and is how the pre-R2-451
# sheet is reproduced bit-for-bit from this file. That reproduction is the null
# every measurement in R2-451 is taken against, and it is run first.
STATION_MIN_ELEV_DEG = -8.0         # presentation_normals' own floor
STATION_SPOT_RIG_Z = 5.590          # 6 x SPOT, world/beat1_anim.blend
STATION_LENS_CLEARANCE = 0.30
STATION_MIN_CAM_Z = 1.20            # the close-out's rope-barrier rule


def _set_elev(d, elev_deg):
    """Same azimuth, new elevation. Azimuth is the measured quantity."""
    h = math.hypot(d[0], d[1])
    if h < 1e-9:
        return [math.cos(math.radians(elev_deg)), 0.0,
                math.sin(math.radians(elev_deg))]
    e = math.radians(elev_deg)
    s = math.cos(e) / h
    return [d[0] * s, d[1] * s, math.sin(e)]


def _legalise_station_dir(d, centre, standoff):
    """Clamp a station direction into the band a camera can actually occupy."""
    if STATION_MAX_DEPRESSION_DEG >= 90.0:
        return d                       # the null: pre-R2-451 behaviour, exactly
    zmax = STATION_SPOT_RIG_Z - STATION_LENS_CLEARANCE
    e = math.degrees(math.asin(max(-1.0, min(1.0, d[2]))))
    e = min(STATION_MAX_DEPRESSION_DEG, max(STATION_MIN_ELEV_DEG, e))
    # then the room: cam_z = centre_z + standoff * sin(e)
    for _ in range(4):
        z = centre[2] + standoff * math.sin(math.radians(e))
        if z > zmax:
            s = (zmax - centre[2]) / standoff
            e = math.degrees(math.asin(max(-1.0, min(1.0, s))))
        elif z < STATION_MIN_CAM_Z:
            s = (STATION_MIN_CAM_Z - centre[2]) / standoff
            e = math.degrees(math.asin(max(-1.0, min(1.0, s))))
        else:
            break
        e = min(STATION_MAX_DEPRESSION_DEG, max(STATION_MIN_ELEV_DEG, e))
    return _set_elev(d, e)


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
# WHAT R2-833 CHANGES, AND WHY THE FOUR HAND-PLACED KEYS COULD NOT SURVIVE.
#
# Every one of those four times is an anchor against a LANDING FRAME — 630, 663,
# 696 — and R2-831 moves all three. Keeping the keys where they are would point
# the camera at four events that now happen 8 seconds earlier, which is the same
# defect R2-029 was, reintroduced by arithmetic instead of by omission. So the
# close-out is no longer four constants; it is DERIVED from the corner group's
# solved station and the pinned seam key, and it moves whenever they move.
#
# AND IT IS NOW THE PAYOFF, WHICH IS A DIFFERENT JOB. The old close-out was a
# 5.3 s transition that had to chase five landings scattered over 163 frames.
# After R2-830/831 the camera is ALREADY at a station that holds the whole car
# (the corner group's own presentation frame contains the assembled car at 0.83
# of frame width — measured, not arranged), and the last part settles at frame
# 507. That leaves ~11.9 s in which the subject is a finished Formula 1 car and
# the camera has nothing left to explain.
#
# THE MEASUREMENT THAT DECIDES WHAT TO DO WITH IT. Frame-to-frame image change on
# the delivered 720p beat: 20.27 across the unreadable tour, 4.89 across the
# readable payoff — a 4.14x collapse exactly where the subject finally appears.
# The beat did not read as slow because the camera was slow. It read as slow
# because it went STILL at the moment there was finally something to look at.
# Making the payoff three times longer without moving the camera would have made
# that worse, not better, and it is the obvious way to get this wrong.
#
# THE MOVE. One continuous orbit, azimuth 177 deg -> 327 deg (150 deg the short
# way, passing behind the car and down its right flank to the front-right
# three-quarter), radius opening 6.9 -> 8.1 m, descending 4.27 -> 1.90 m from the
# high group station to eye level, lens 35 -> 40 mm so the car holds a constant
# size in frame while the vantage changes completely. It is a single gesture, it
# never stops, and it arrives exactly on the pinned seam key.
#
# CONSTRAINTS IT IS SOLVED AGAINST, all measured on beat1_anim.blend:
#   * the car body occupies x -2.70..3.02, y +-1.00, z 0.34..1.33. The orbit
#     never comes inside 5.9 m of the box, against a 0.30 m floor.
#   * the showroom's rope barrier ring reaches radius 6.96 m and z 0.92; the
#     orbit is either outside it or more than 1.2 m above it, everywhere.
#   * walls |x| 15.25 / |y| 11.25, ceiling 6.20, spot rigs from z 5.11.
#
# THE LAST KEY IS NOT TOUCHED.  t = 31.40 is the seam with beat 2, whose first
# key sits 2.09 m away 39 frames later at 40.0 -> 39.95 mm.  Moving it would put
# a discontinuity in a film whose one law is that there are none.  The orbit is
# built to LAND on it: its final authored key is the seam key's own station.
BEAT1_CLOSEOUT_KEYS = 6          # ~2 s apart; enough for the bezier to be an arc
BEAT1_CLOSEOUT_LENS_END_MM = 40.0     # == the seam key, so the lens is C1 there
# R2-838/839. The orbit's angular rate at each end, as a multiple of its own mean.
#
# START at 1.0: the camera reaches the corner group's station already moving at
# ~1.96 m/s, so easing IN to a standstill and back out would be a deceleration
# the shot does not want and the energy curve cannot afford. It carries straight
# on into the orbit.
#
# END at 0.57: the beat 1/2 seam bridge's own keys run at ~1.2 m/s and they are
# CARRIED FORWARD, i.e. fixed. Arriving faster than that puts a step at frame 754
# no matter which way the orbit turns. 0.57 x the orbit's mean is ~1.2 m/s.
#
# TUNED AGAINST THE PER-FRAME CAMPATH GATE, not derived: arc length per unit
# parameter is not constant, so the ratio of rates is not the ratio of speeds.
BEAT1_ORBIT_START_RATE = 1.00
BEAT1_ORBIT_END_RATE = 0.57

# R2-839. The long way round is 210 deg instead of 150, and at a mean radius of
# 7.5 m that is 27.5 m of arc in 12.08 s -- which the pre-flight rejected at
# 4.04-4.52 m/s against beat 1's 4.00 m/s peak limit. The orbit therefore CUTS
# THE CORNER: the radius dips below the straight interpolation at mid-arc and
# returns to it at both ends, which shortens the path without moving either
# endpoint. 1.0 m of dip removes ~2.4 m of arc.
#
# BOUNDED BY THE PICTURE, not by the gate. At mid-arc the radius is 6.5 m and the
# lens is ~37.5 mm, so the 5.72 m car spans 0.92 of the frame width -- still
# whole, which is the entire point of the payoff.
BEAT1_ORBIT_RADIUS_DIP_M = 1.00


# --------------------------------------------------------------------------- #
#  THE APPROACH KEY — R2-837, and it is a LENS defect, not an aim defect.       #
# --------------------------------------------------------------------------- #
#
# The hop into the corner group is structurally the largest reorientation in the
# beat: it leaves the last close presentation (RW, 58 mm at 3.80 m) for the beat's
# widest shot (the group, 35 mm at 7.58 m), and it turns 107 deg doing it. With
# only its two endpoints keyed, the rig ramps the lens LINEARLY across all 65
# frames — so at the midpoint the camera has finished most of its turn while still
# carrying most of a 58 mm lens.
#
# MEASURED on the built per-frame path, every frame of beat 1 against the nearest
# cluster's bounding-sphere EDGE (the aim gate's own metric, `ang / half_v`):
#
#     f420-433   14 frames over the 0.92 margin, peaking at 1.155 at f431
#     everywhere else in the 792 frames:  inside the margin
#
# ONE excursion in the beat, and reading the row is what identifies the cause:
#
#     f431   lens 46.8 mm   half-frame 12.22 deg   nearest edge 14.12 deg
#
# The camera is not pointed at nothing. RW's edge is 14.12 deg off axis and the
# frame is only 12.22 deg tall, so the subject is 1.9 deg outside a picture that a
# 37 mm lens would have contained. THE AIM IS FINE AND THE LENS IS TOO LONG —
# which is why the answer is not the old bridge (a key that points the camera at
# something else); it is a key that finishes the widening BEFORE the turn needs
# it, and that is also what the shot wants. You widen as you pull back, so the car
# grows into the frame instead of snapping wide at the end.
#
# `_U` is where along the hop the key sits; the lens is at the destination's value
# by then, so the entire excursion window is shot at ~36 mm rather than ~47-52.
BEAT1_APPROACH_U = 0.28
BEAT1_APPROACH_LENS_MM = 36.5


def beat1_approach_key(t0, cam0, look0, lens0, t1, cam1, look1):
    """The widening key on the hop into the corner group. Derived, not placed."""
    u = BEAT1_APPROACH_U
    w = [round(cam0[i] + (cam1[i] - cam0[i]) * u, 4) for i in range(3)]
    la = [round(look0[i] + (look1[i] - look0[i]) * u, 4) for i in range(3)]
    return dict(
        t=round(round((t0 + (t1 - t0) * u) * 24.0) / 24.0, 6),
        world=w, look_at=la, lens_mm=BEAT1_APPROACH_LENS_MM,
        focus_target="CORNER_GROUP_APPROACH",
        fstop=2.8, focus_distance_m=round(math.dist(w, la), 3),
        note="R2-837 approach: the lens reaches its wide end BEFORE the turn "
             "into the corner group needs it. Without it the rig ramps 58->35 mm "
             "linearly over 65 frames and 14 frames (f420-433) carry a subject "
             "outside a frame a 37 mm lens would have held.")


def beat1_closeout(t0, cam0, look0, lens0, seam, onward=None):
    """The payoff orbit: from the corner group's station to the beat 1/2 seam.

    DERIVED FROM ITS TWO ENDPOINTS. `cam0/look0/lens0` are the corner group's
    SOLVED presentation station and `seam` is the pinned seam key, so this move
    cannot drift away from either of them when the schedule changes — which is
    exactly what the four hand-placed constants it replaces could not promise.

    Interpolated in CYLINDRICAL coordinates about the turntable, not in Cartesian
    ones, and that is the whole trick: a straight line between two stations on
    opposite sides of a car goes through the car (R2-029), while an arc in
    azimuth cannot. The azimuth is unwrapped to the SHORT way round so the camera
    never takes the 210 deg route to save 150 deg of the same move.
    """
    ax0 = math.atan2(cam0[1], cam0[0])
    ax1 = math.atan2(seam["world"][1], seam["world"][0])
    dax = (ax1 - ax0 + math.pi) % (2.0 * math.pi) - math.pi     # the short way
    # R2-839.  THE ORBIT GOES THE WAY THE FILM CONTINUES, NOT THE SHORT WAY.
    #
    # Taking the short way round put the camera into the seam travelling +x +y
    # while the film's very next key leaves it travelling -x -y. That is not a
    # kink, it is a REVERSAL: the camera stops dead at frame 754 and goes back
    # the way it came. Blender's AUTO_CLAMPED handles then flatten the key,
    # because a local extremum is exactly what a reversal is, and the per-frame
    # speed collapsed to 0.010 m/frame against 0.049 on either side.
    #
    # MEASURED, and this is what identified it — per-frame chord either side of
    # the seam, candidate against the shipped path:
    #
    #     f744   cand 0.045   ship 0.064
    #     f750   cand 0.023   ship 0.056
    #     f754   cand 0.010   ship 0.051      <- the seam
    #     f756   cand 0.049   ship 0.049      <- the seam bridge takes over
    #
    # The shipped path does not have this problem because its close-out arrived
    # at the seam ALREADY travelling -x -y, monotone through the key, so nothing
    # flattened. Matching that is a constraint on the orbit's direction, and it
    # is the one-shot law: a velocity reversal is a cut.
    #
    # So the sign is chosen by where the film goes NEXT. `onward` is the first
    # camera position after the seam (the beat 1/2 seam bridge's own first key);
    # the orbit turns whichever way leaves its azimuth rate matching that.
    if onward is not None:
        ax_next = math.atan2(onward[1], onward[0])
        d_next = (ax_next - ax1 + math.pi) % (2.0 * math.pi) - math.pi
        if d_next != 0.0 and (d_next > 0.0) != (dax > 0.0):
            # go the long way instead, so the azimuth rate does not change sign
            dax -= math.copysign(2.0 * math.pi, dax)
    if abs(dax) < math.radians(30.0):        # degenerate: nothing to orbit
        dax = math.copysign(math.radians(30.0), dax or 1.0)
    r0 = math.hypot(cam0[0], cam0[1])
    r1 = math.hypot(seam["world"][0], seam["world"][1])
    t1 = seam["t"]
    keys = []
    for i in range(1, BEAT1_CLOSEOUT_KEYS + 1):
        u = i / float(BEAT1_CLOSEOUT_KEYS)
        # R2-838.  THE ORBIT MUST NOT EASE OUT, BECAUSE BEAT 2 IS STILL MOVING.
        #
        # This was a smoothstep, `u*u*(3-2u)`, whose derivative is ZERO at both
        # ends. That is the right curve for a move that stops. This move does not
        # stop — it hands over to beat 2, whose first key is 2.09 m away 39 frames
        # later, i.e. 1.29 m/s. Easing out parked the camera on the seam and beat
        # 2 tore away from it, and the per-frame campath gate caught it exactly
        # there: "frame 754: camera speed changes 0.0439 m/frame in one frame,
        # z=56.4 against a local median of 0.00086 (0.2 -> 1.2 m/s). An eased
        # curve does not do this; a keyframe with a linear handle does."
        #
        # A C0-continuous seam is not enough for this film. The one law is that
        # there are no cuts, and a velocity step IS a cut — it just does not look
        # like one in a still.
        #
        # So the easing is a cubic with the boundary conditions the shot actually
        # has: e(0)=0, e(1)=1, e'(0)=0 (leave the group station gently, the camera
        # has been nearly still there while the car assembled) and e'(1)=r, the
        # rate that matches beat 2's departure instead of fighting it.
        s0, r = BEAT1_ORBIT_START_RATE, BEAT1_ORBIT_END_RATE
        a = r + s0 - 2.0
        b = 3.0 - r - 2.0 * s0
        e = a * u ** 3 + b * u ** 2 + s0 * u
        a = ax0 + dax * e
        r = r0 + (r1 - r0) * e - BEAT1_ORBIT_RADIUS_DIP_M * math.sin(math.pi * e)
        z = cam0[2] + (seam["world"][2] - cam0[2]) * e
        la = [look0[j] + (seam["look_at"][j] - look0[j]) * e for j in range(3)]
        w = [round(r * math.cos(a), 4), round(r * math.sin(a), 4), round(z, 4)]
        lens = lens0 + (BEAT1_CLOSEOUT_LENS_END_MM - lens0) * e
        if i == BEAT1_CLOSEOUT_KEYS:
            # LAND ON THE SEAM EXACTLY — by emitting the seam key ITSELF, not a
            # copy of its numbers. A copy is a second place the seam is written
            # down, and a second place is where the two drift apart.
            keys.append(dict(seam))
            break
        # FOCUS IS NOT OWNED HERE — R2-834. `focus_distance_m` is set to the
        # geometric range to the aim point and `fstop` is ramped onto the seam
        # key's own 3.2, purely so the key is WELL-FORMED and the rig can build
        # it. Both are the focus agent's to solve; they are not a focus decision,
        # they are the absence of one, and the staging note says so.
        keys.append(dict(
            t=round(t0 + (t1 - t0) * u, 4), world=w, look_at=[round(v, 4) for v in la],
            lens_mm=round(lens, 3), focus_target="CAR",
            fstop=round(3.0 + 0.2 * e, 3),
            focus_distance_m=round(math.dist(w, la), 3),
            note="R2-833 payoff orbit %d/%d: the assembled car, %.0f deg of "
                 "azimuth at %.2f m" % (i, BEAT1_CLOSEOUT_KEYS,
                                        math.degrees(abs(dax)) * e, r)))
    return keys


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
# R2-830 — RETIRED, AND KEPT SO THE REASON IS NOT LOST.
#
# The bridge existed because RW's station looked at the rear wing hanging behind
# the car in -Y and CORNER_RL's looked at the rear-left wheel in +Y: a 110 deg pan
# between two stations 1.53 m from their subjects, halfway through which the lens
# pointed at bare floor. BOTH of those facts are gone.
#
#   * R2-829 pulls RW's station to 3.80 m and the corner group's to 7.58 m, and
#     from that far out every station is looking INWARD at the same car. The
#     bearing between adjacent stations collapses; it is the close-in standoff
#     that made the pan enormous, not the tour.
#   * R2-830 removes CORNER_RL's individual presentation, so the pan the bridge
#     was built to cover no longer occurs at all.
#
# It is not deleted because the measurement in the comment above is real and a
# future close-in tour would need it again. It is simply no longer emitted, and
# `build_beat1` no longer references it. What replaces it as the guarantee is the
# measured pan rate in the FLIGHT block — which is the instrument that found the
# problem in the first place.
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


# --------------------------------------------------------------------------- #
#  THE ESTABLISHING FRAME — R2-429 / R2-464.                                    #
# --------------------------------------------------------------------------- #
#
# WHAT R2-429 ACTUALLY FOUND, once the metric was corrected.  Its headline —
# "the car is never smaller than 76.1 % of frame width" — is the subtense of the
# car's 5.72 m LENGTH, which is its apparent width only when the camera is
# broadside.  Projecting the eight bbox corners through the real camera instead
# (`tools/beat1_true_extent.py`) says something different:
#
#     close-out f648-792, frames containing the WHOLE car     136 / 145  (94 %)
#     first frame that contains the whole car                 f657, t = 27.4 s
#     f700 car fraction of frame width      proxy 0.832   TRUE 0.497
#
# and `work/b1look/b1focus_000700_full.png` settles it: the complete car,
# uncropped, head-on on the turntable, with the showroom's sign, placard, rope
# barrier and back wall behind it.  **Beat 1 has an establishing shot. It arrives
# 27.4 seconds into a 33-second beat.**
#
# AND IT CANNOT SIMPLY BE MOVED EARLIER, because its subject does not exist
# earlier: it is a shot of the ASSEMBLED car, and the four corners do not land
# until f696-704.  The payoff of an assembly cannot precede the assembly.
#
# So the opening gets its own establishing frame with its own subject — the
# EXPLODED FIELD in the darkened room, which is what the brief actually asks the
# first image to show: "the camera drifts through the darkened showroom as parts
# hang exploded in space around the empty turntable".
#
# WHY IT IS AN AUTHORED KEY AND NOT A WIDER STANDOFF.  Pushing MB's station back
# along its own presentation normal was tried first and fails geometrically, not
# marginally: MB's direction was chosen to show MB's best face, and walking
# backwards down it carries the lens INTO the field and out the far end.  At a
# 7.5 m standoff the camera stands at x = -6.50, inside the field's own
# -6.40..4.72 x-span, with field corners at negative depth behind the lens.
# A direction chosen to see one cluster is not a direction that sees the room.
#
# WHAT THE BEAT CAN AFFORD.  MEASURED, with the offset modelled — a lead-in both
# delays every presentation AND compresses the tour, and modelling only the
# compression says 4.0 s where the truth is 2.0:
#
#     max affordable lead-in, shipped normals   2.0 s   (binding: BB, 0.45 s slack)
#     max affordable lead-in, R2-451 normals    2.0 s   (binding: SW, 2.52 s slack)
#
# 2.0 s at 24 fps is 48 frames, and beat 6 already holds a composed frame for 3 s.
#
# THE STATION IS SOLVED JOINTLY WITH MB'S DIRECTION, and it has to be.  The
# first attempt put the establishing key on the ray through MB's own station and
# pushed back: MB's re-aimed direction points along the field's LONG axis, so
# that view looks down an 11 m corridor, needs 10-11 m to contain it, and lands
# 6.5-7.5 m from MB's station -- 8.29 m in 2.0 s, which fails the weave-speed
# gate at 5.64-6.30 m/s against 4.00.  A direction chosen to show one cluster is
# not a direction that shows the room, and the establishing station cannot be
# derived from it.
#
# Solved instead over MB's whole legal band x (azimuth, elevation, distance,
# lens), subject to: the field fits, the lens is in the room and under the rigs,
# and the chord to MB's station is flyable in the lead-in.  The winner puts the
# camera BROADSIDE to the field's long axis, which is the obvious answer that the
# push-back parameterisation could not reach.  MB's direction moves with it and
# gets BETTER, not worse: 77.3 % of its unconstrained score against the 48.2 %
# the R2-451 search had to settle for.
#
# THE STATION, solved rather than placed.  The field is 11.12 x 4.42 x 3.84 m
# centred at (-0.841, 0, 2.194).  Containing 11.12 m at 0.85 fill needs
# `d >= 13.08 * lens / 36`; the lens is 18 mm, which is inside the film's own
# range (beat 3 runs 21-32 mm, beat 6 reaches 18.8) and not a new look.  At
# d = 9.00 m and 10.00 deg of depression — the film's house angle, R2-454 — the
# lens sits at z 3.757, 1.83 m under the spot rigs at 5.590, and at y = -8.863,
# radius 8.90 m, outside the rope ring at 6.96 and 2.4 m inside the wall at
# |y| 11.25.  The far wall is then ~9 m behind the subject, which is the
# background throw the brief's rim lighting and DOF both need and which the
# nadir stations did not have.
#
# R2-501.  THE FIVE NUMBERS IN THE PARAGRAPH ABOVE WERE WRONG UNTIL THE
# PROMOTION READ THEM.  It said 24 mm, d = 8.70 m, 12 deg, z 4.00, y -8.51 —
# an EARLIER solve — while `BEAT1_ESTABLISH` below said 18 mm, 9.000 m,
# 9.9985 deg, z 3.7566, y -8.8633.  The constant was right and shipped; the
# prose beside it described a station that does not exist.  Nothing read the
# prose, so nothing caught it, and every summary of this work quoted the prose.
# Derive these from `BEAT1_ESTABLISH` if you change it — see the assertion under
# it, which now makes the disagreement a build failure rather than a comment.
def _establish_on():
    """R2-464 IS ON BY DEFAULT AS OF R2-501. The candidate is promoted.

    It was held off by default while a ladder pass was in flight against the
    camera it replaces (R2-463): the flag existed so a candidate could be
    measured end to end without changing the film under five other agents. That
    pass has completed and the hold is lifted, so the DEFAULT is now the fixed
    opening and `B1_ESTABLISH=0` reproduces the shipped nadir behaviour exactly.

    The flag is deliberately kept rather than deleted. `B1_ESTABLISH=0` is the
    only way to rebuild the pre-promotion sheet, and this project keeps the
    arm it must fail so the arm it must pass is not a vacuous pass.
    """
    return os.environ.get("B1_ESTABLISH", "1").strip() not in ("0", "off", "")


BEAT1_ESTABLISH_LEAD_S = 2.0
BEAT1_ESTABLISH = dict(
    t=0.0, world=[-0.8409, -8.8633, 3.7566], look_at=[-0.841, 0.0, 2.194],
    lens_mm=18.0, fstop=4.0, focus_distance_m=9.0, focus_target="FIELD",
    note="ESTABLISHING. The whole exploded field in the darkened showroom, "
         "with the empty turntable under it — the brief's own first image. "
         "R2-429/R2-464.")


def establish_station_geometry(est=BEAT1_ESTABLISH):
    """-> (standoff_m, depression_deg, lens_z, radius_m). MEASURED, not quoted.

    R2-501 exists because the paragraph above `_establish_on` quoted five
    numbers for this station and every one of them was from a superseded solve.
    A comment cannot be wrong if the number is computed, so the three claims the
    promotion turns on — 18 mm, 9.0 m, 10.00 deg — are asserted here against the
    constant itself and this module refuses to load if they drift apart.
    """
    w, la = est["world"], est["look_at"]
    d = [w[i] - la[i] for i in range(3)]
    horiz = math.hypot(d[0], d[1])
    return (math.sqrt(horiz * horiz + d[2] * d[2]),
            math.degrees(math.atan2(d[2], horiz)), w[2], math.hypot(w[0], w[1]))


_ES_D, _ES_DEP, _ES_Z, _ES_R = establish_station_geometry()
assert abs(_ES_D - 9.0) < 5e-4, _ES_D
assert abs(_ES_DEP - 10.0) < 5e-3, _ES_DEP          # 9.99850, "exactly 10.00"
assert abs(BEAT1_ESTABLISH["lens_mm"] - 18.0) < 1e-9
assert abs(BEAT1_ESTABLISH["focus_distance_m"] - _ES_D) < 5e-4, (
    "focus_distance_m must be the solved standoff, not a rounded copy of it")
assert _ES_Z <= 5.29, "R2-454: the lens must stay under the spot rig plane"
assert _ES_Z >= 1.20, "R2-454: the lens must clear the rope barrier"
assert _ES_R > 6.96, "the station is inside the rope ring"


def seam_onward_point(sheet_path):
    """The first camera position AFTER beat 1's seam key. R2-839.

    Read from the shipped sheet rather than hard-coded, because it belongs to
    `beat1_2_seam` / `beat2`, which this file does not author. Returns None if it
    cannot be found, and the caller then keeps the short-way orbit — a missing
    onward point must not silently become a claim about one.
    """
    try:
        sh = json.load(open(sheet_path))
    except Exception:
        return None
    ks = list((sh.get("beat1_2_seam") or {}).get("camera_keys") or [])
    ks += list((sh.get("beat2") or {}).get("camera_keys") or [])
    ks = sorted((k for k in ks if "world" in k and "t" in k),
                key=lambda k: float(k["t"]))
    for k in ks:
        if float(k["t"]) > 31.4 + 1e-9:
            return list(k["world"])
    return None


def build_beat1(geo, plan, dur, normals=None, deadlines=None, onward=None):
    # R2-830/831/832. ONE TOUR, ONE SPAN, AND THE SPAN IS SOLVED.
    #
    # What was here: a 1.76 s uniform slot used to derive `corner_last_t`, two
    # bridge times pinned to the engine cover's landing frame, and two separately
    # allocated spans. All four of those anchors are downstream of a seat schedule
    # that R2-831 moves, so none of them survives as a constant. The structure is
    # now: the tour starts after the establishing lead-in and ends on the corner
    # group, and everything else is derived.
    seat_t = seat_schedule(plan, dur)
    n_spine = len([k for k in plan["seat_order"] if not k.startswith("CORNER_")])
    grouped = CORNER_GROUP in geo
    n = n_spine + (1 if grouped else 4)

    # R2-464: the establishing frame eats the front of the tour's span, so the
    # tour is BOTH delayed and compressed. Both effects are in the solve.
    lead = float(os.environ.get("B1_ESTABLISH_LEAD_S",
                                BEAT1_ESTABLISH_LEAD_S if _establish_on() else 0.0))
    order = present_order(geo, plan["seat_order"], normals, deadlines, t0=lead)

    # ---- THE SPAN IS CHOSEN, NOT ASSUMED -----------------------------------
    #
    # `_allocate` spreads a span over the moves in proportion to what they cost,
    # so the time at which the k-th cluster is presented is
    #
    #     t_k = lead + span * (cum_cost_k / total_cost)
    #
    # and requiring t_k <= deadline_k inverts to a bound on the span, one per
    # cluster. The beat should be as UNHURRIED as its deadlines allow — a tour
    # flown faster than it needs to be is the "dash" R2-062 caught — so the span
    # is the largest one that every cluster still tolerates, and the cluster that
    # sets it is named in the log rather than left to be guessed at.
    costs = [_hop_cost(geo, normals, order[i], i, order[i + 1], i + 1, n)
             for i in range(len(order) - 1)]
    total = sum(costs)
    cum, acc = {}, 0.0
    for i, k in enumerate(order[1:]):
        acc += costs[i]
        cum[k] = acc
    span_cap, binder = float("inf"), None
    for k, c in cum.items():
        d = deadlines.get(k)
        if d is None or c <= 0:
            continue
        lim = (d - lead) * total / c
        if lim < span_cap:
            span_cap, binder = lim, k
    if span_cap <= 0:
        raise SystemExit(">> beat 1: the presentation span solves to zero or "
                         "less; the seat schedule leaves no room for the tour")
    dt, ratio = _allocate(costs, span_cap)
    budget = {"tour": ratio, "span_s": round(span_cap, 4), "binding": binder}
    print(f">> beat 1 SPAN SOLVED: {span_cap:.3f} s for {len(order)} "
          f"presentations, bound by {binder} (ratio {ratio:.3f}; 1.000 = every "
          f"move sits exactly on its own limit, above 1.000 = squeezed)")

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
    t = lead
    for i, k in enumerate(order):
        times[k] = on_frame(t)
        if i < len(dt):
            t += dt[i]
    seq_f = [int(round(times[k] * 24)) for k in order]
    assert all(b > a for a, b in zip(seq_f, seq_f[1:])), (
        f"two presentations quantised onto the same frame: {seq_f}")
    # R2-835.  THE `CORNER_FL LANDS ON FRAME 591` ASSERTION IS GONE, DELIBERATELY.
    #
    # It read:
    #     assert int(round(times[corners[-1]] * 24)) == int(round(corner_last_t*24))
    # where `corner_last_t = dur * 0.80 - dur * 0.80 / 15`, i.e. the 15th of
    # fifteen equal 1.76 s slots. THAT SLOT SCHEME NO LONGER EXISTS. R2-062
    # replaced the uniform slot with a cost-proportional allocation, and the
    # constant survived only because it happened to still be reproducible; R2-830
    # removes CORNER_FL's individual presentation entirely, so there is nothing
    # left for it to be an assertion ABOUT.
    #
    # RECORDED HERE SO IT IS NOT RESTORED AS A SAFETY CHECK. It looks like one —
    # "the best material in the film must come out unchanged" — but it is not a
    # property of the picture, it is the arithmetic of a dead uniform slot. Any
    # future change to the seat schedule, the tour, or the standoff law moves that
    # frame legitimately, and an assertion that forbids it would forbid the fix
    # rather than protect the shot. What protects the shot is the FRAMING gate and
    # the campath gate, both of which measure the picture.

    keys, sched = [], []
    if lead > 0.0:
        est = dict(BEAT1_ESTABLISH)
        est["beat"] = "1_assembly"
        est["world_time_scale"] = 1.0
        est["presentation_dir_measured"] = False
        keys.append(est)
    group_geom = None
    prev_geom = None
    for i, k in enumerate(order):
        g = geo[k]
        nd = (normals or {}).get(k, {}).get("normal")
        pos, standoff, lens, _v = key_geom(geo, normals, k, i, n)
        t = times[k]
        members = plan["clusters"].get(k, {}).get("r2830_members") or [k]
        key = {
            "t": t, "beat": "1_assembly", "world": pos,
            "look_at": g["centre"], "lens_mm": lens,
            "fstop": 2.2 if g["radius"] < 0.8 else 2.8,
            "focus_target": k, "focus_distance_m": standoff,
            "presentation_dir_measured": bool(nd),
            "visible_materials": (normals or {}).get(k, {}).get("distinct_materials"),
            "world_time_scale": 1.0,
            "note": f"present {k} ({g['n_parts']} parts, {g['tris']:,} tris)",
        }
        if k == CORNER_GROUP:
            key["r2830_members"] = list(members)
            key["note"] = (
                "present the four corners AS ONE GROUP (%d parts, %s tris) — "
                "they seat simultaneously, they are pairwise the same asset, and "
                "four separate presentations cost 9.20 s to show the audience the "
                "same wheel four times at 2.0-2.3x frame overflow"
                % (g["n_parts"], f"{g['tris']:,}"))
            group_geom = (pos, list(g["centre"]), lens)
            # R2-837: the widening key on the way in. Emitted here because this
            # is the only place that has BOTH endpoints of the hop.
            if prev_geom is not None:
                keys.append(beat1_approach_key(prev_geom[3], prev_geom[0],
                                               prev_geom[1], prev_geom[2],
                                               t, pos, list(g["centre"])))
        keys.append(key)
        prev_geom = (pos, list(g["centre"]), lens, t)
        nxt = times[order[i + 1]] if i + 1 < len(order) else None
        for mname in members:
            sched.append({
                "cluster": mname, "n_parts": geo[mname]["n_parts"],
                "tris": geo[mname]["tris"],
                "presented_t": t,
                "presented_until_t": (round(nxt, 4) if nxt is not None else None),
                "presented_as": (k if k != mname else None),
                "seat_t": None, "seen_before_seat": None,
            })

    # R2-831. THE SEAT SCHEDULE IS NOW COMPUTED IN ONE PLACE (`seat_schedule`)
    # and read here, because the presentation DEADLINES are derived from the same
    # function. It used to be computed here and the deadlines read out of
    # `world/beat1_anim_anim.json` — a build artefact of a 291 MB blend — so the
    # two could disagree silently. `main()` now compares them and says so.
    #
    # THE BLEND MUST BE REBUILT WHENEVER THIS MOVES. `world/beat1_anim.blend` was
    # BUILT from these times and is not rebuilt here, so a change to
    # BEAT1_SEAT_START_FRAC, BEAT1_SEAT_SPAN_FRAC or the seat order desynchronises
    # the parts from the camera. That is not a warning about a hypothetical: the
    # desync is silent in every gate in this file, because every gate here reads
    # the sheet.
    for s in sched:
        s["seat_t"] = seat_t[s["cluster"]]
        s["seen_before_seat"] = s["presented_t"] < s["seat_t"]

    # THE SEAM WITH BEAT 2 — do not move it. Built first, because the close-out
    # orbit is solved to LAND on it.
    seam = {
        "t": round(dur - 1.6, 3), "beat": "1_assembly",
        "world": [6.8, -4.4, 1.9], "look_at": [0.15, 0.0, 0.75],
        "lens_mm": 40.0, "fstop": 3.2, "focus_target": "CAR",
        "focus_distance_m": 8.3, "world_time_scale": 1.0,
        "note": "push toward the completed car; spot rigs ramp ~1 stop over 12 "
                "frames. THE SEAM: beat 2's first key is 2.09 m away 39 frames "
                "later at 39.95 mm, so this key is fixed and beats 1 and 2 join "
                "at 1.29 m/s with no step in position, aim or focal length",
    }

    # THE CLOSE-OUT — R2-833, derived from the corner group's station and the
    # seam, not from four constants anchored to landing frames that have moved.
    closeout = []
    if group_geom is not None:
        closeout = beat1_closeout(times[order[-1]], group_geom[0],
                                  group_geom[1], group_geom[2], seam,
                                  onward=onward)
    for k in closeout:
        e = dict(k)
        e.update(beat="1_assembly", world_time_scale=1.0)
        keys.append(e)
    if not closeout:
        keys.append(seam)
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

    # R2-451: overridable so a candidate normals file can be built and MEASURED
    # end to end before docs/ is touched -- six agents are live against docs/.
    npath = os.environ.get("B1_NORMALS",
                           os.path.join(DOCS, "presentation_normals.json"))
    if npath != os.path.join(DOCS, "presentation_normals.json"):
        print(f">> B1_NORMALS override in force: {npath}")
    normals = json.load(open(npath)) if os.path.exists(npath) else {}
    print(f">> presentation normals: {len(normals)} clusters measured"
          if normals else ">> WARNING: no presentation normals; spiral fallback")

    # R2-830.  Declare the four corners as one camera subject, in memory only.
    if normals and os.environ.get("B1_CORNER_GROUP", "1").strip() \
            not in ("0", "off", ""):
        gk, gmem = build_corner_group(geo, plan, normals)
        if gk:
            g = geo[gk]
            print(">> corner group: %s = %s — one subject, %.2f x %.2f x %.2f m, "
                  "%d parts, %s tris" % (gk, "+".join(gmem), g["size"][0],
                                         g["size"][1], g["size"][2],
                                         g["n_parts"], f"{g['tris']:,}"))

    # ---- WHEN EACH CLUSTER STOPS BEING WHERE ITS STATION SAYS IT IS ---------
    #
    # A presentation station is `explode_offset + bbox_centre` plus a standoff,
    # i.e. it is solved against the cluster's EXPLODED position. The cluster is
    # only there until it starts FLYING, which is `flight_s` before it lands --
    # not until it lands. Presenting after that aims a solved station at empty
    # air. So the visiting order is constrained by the flight START, with a
    # margin, and world/beat1_anim_anim.json is the file the part animation was
    # actually built from, so it is the one that gets to say when.
    # Overridable for the same reason B1_NORMALS and B1_SHEET_OUT are: a
    # candidate must be measurable end to end before world/ is touched, and the
    # part animation is half of what "end to end" means here.
    anim_p = os.environ.get("B1_ANIM_JSON",
                            os.path.join(R2, "world/beat1_anim_anim.json"))
    if anim_p != os.path.join(R2, "world/beat1_anim_anim.json"):
        print(f">> B1_ANIM_JSON override in force: {anim_p}")
    anim = json.load(open(anim_p)) if os.path.exists(anim_p) else {}
    flight_f = float(anim.get("flight_s", 1.55)) * 24
    PRESENT_MARGIN_S = 0.5

    # R2-831.  THE DEADLINES COME FROM THE SCHEDULE, NOT FROM THE LAST BUILD.
    #
    # They used to be read out of `world/beat1_anim_anim.json` — the sidecar of a
    # 291 MB blend — while the seat times they are derived FROM were computed
    # inside `build_beat1`. Two sources for one fact, and the sheet trusted the
    # stale one: any change to the seat constants produced a sheet solved against
    # the PREVIOUS assembly timing, which is precisely the silent desync the
    # comment at the seat schedule warns about and which no gate here could see,
    # because every gate here reads the sheet.
    b1_seat = seat_schedule(plan, BEATS[0][1])
    deadlines = {c: t - flight_f / 24.0 - PRESENT_MARGIN_S
                 for c, t in b1_seat.items()}
    if CORNER_GROUP in geo:
        deadlines[CORNER_GROUP] = min(
            deadlines[c] for c in plan["seat_order"] if c.startswith("CORNER_"))
    tight = sorted(((c, t) for c, t in deadlines.items()
                    if c != CORNER_GROUP), key=lambda kv: kv[1])[:3]
    print(">> presentation deadlines (flight start less a %.1f s margin), "
          "tightest three: " % PRESENT_MARGIN_S
          + ", ".join(f"{c} {t:.2f} s" for c, t in tight))

    # ---- AND THE BLEND IS CHECKED AGAINST THEM, LOUDLY ---------------------
    anim_seat = {c: v["seat_frame"] / 24.0
                 for c, v in anim.get("clusters", {}).items()}
    desync = sorted((c, anim_seat[c], b1_seat[c]) for c in anim_seat
                    if c in b1_seat
                    and abs(anim_seat[c] - b1_seat[c]) > 1.0 / 24.0)
    if not anim_seat:
        print(">> WARNING: no world/beat1_anim_anim.json; nothing can confirm "
              "that the parts assemble on the schedule this sheet declares")
    elif desync:
        print(">> !! PART/CAMERA DESYNC: world/%s was built from a DIFFERENT "
              "seat schedule than this sheet declares — %d of %d clusters "
              "disagree by more than one frame."
              % (os.path.basename(anim.get("blend", "beat1_anim.blend")),
                 len(desync), len(anim_seat)))
        for c, a_t, b_t in desync[:6]:
            print("   %-16s blend f%-4d (%.2f s)   sheet f%-4d (%.2f s)   "
                  "%+.2f s" % (c, round(a_t * 24), a_t, round(b_t * 24), b_t,
                               b_t - a_t))
        print("   REBUILD REQUIRED: anim/build_beat1_anim.py reads seat_t from "
              "this sheet. Until it is re-run, the camera is solved against one "
              "assembly and the pictures show another.")
    else:
        print(">> part/camera sync: world/%s agrees with this sheet's seat "
              "schedule on all %d clusters"
              % (os.path.basename(anim.get("blend", "beat1_anim.blend")),
                 len(anim_seat)))

    onward = seam_onward_point(os.path.join(DOCS, "beat_sheet.json"))
    print(">> beat 1/2 seam onward point: %s"
          % ("%s (the orbit's direction is matched to it)"
             % [round(v, 3) for v in onward] if onward else
             "NOT FOUND — the orbit keeps the short way round and the seam's "
             "velocity continuity is NOT established"))
    order, b1keys, sched, path_len, budget = build_beat1(
        geo, plan, BEATS[0][1], normals, deadlines, onward=onward)
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

    # ----------------------------------------------------------------- R2-316
    #
    # THIS BLOCK USED TO REPORT `edge_angle_deg = 0.000` FOR ALL FIFTEEN
    # PRESENTATIONS AND CALL IT A PASS.  It could not have reported anything
    # else.  It computed
    #
    #     edge = max(0, ang - asin(rad / nd))
    #
    # where `ang` is the angle from the optical axis to the cluster's CENTRE --
    # and `camera_station()` puts the lens on the ray through that centre, so
    # `ang` is identically zero at every presentation.  Subtracting the cluster's
    # own angular radius from zero and clamping at zero measures the angle to the
    # NEAR edge of a body the axis passes through, which is always inside the
    # frame.  The thing that overflows is the FAR edge, and the sign in front of
    # `asin` is what decides which one you get.  Same class as R2-062: the aim
    # was measured, the photographability was not.
    #
    # Measured with the sign corrected, on the shipped stations: every one of the
    # fifteen overflows, from 1.06x the frame (SW) to 2.59x (NOSE).
    #
    # It now measures the projected extent of the eight bounding-box corners
    # rather than a sphere of the bbox half-diagonal, because that is what the
    # audience sees, and it reports the two numbers the fix needs:
    #
    #   * `extent_frac_frame_h/w` -- >1.0 means the audience gets a fragment.
    #   * `fstop_required` -- the f-number that would hold the WHOLE cluster
    #     inside `SHARP_BUDGET_PX` at 4K, from the exact thin-lens blur
    #         C = (f/N) f |s - s_f| / ((s_f - f) s)
    #     evaluated at the cluster's own near and far depth.  This is the number
    #     that says the two defects are one: at the shipped standoff the corner
    #     clusters need about f/52, which is not a photographable aperture; at a
    #     standoff that makes them FIT they need about f/6.5, which is.  Framing
    #     is therefore a precondition of focus, not a parallel defect.
    #
    # `tools/beat1_present_gate.py` is the standalone form with the selftest.
    SENSOR_W_MM = 36.0
    RES_XY = (3840, 2160)
    SENSOR_H_MM = SENSOR_W_MM * RES_XY[1] / RES_XY[0]
    SHARP_BUDGET_PX = 2.0
    COC_MM = SHARP_BUDGET_PX / (RES_XY[0] / SENSOR_W_MM)
    FILL_TARGET = 0.85

    def _basis(cam, look):
        v = [look[i] - cam[i] for i in range(3)]
        n = math.sqrt(sum(x * x for x in v)) or 1.0
        fwd = [x / n for x in v]
        wu = [0.0, 0.0, 1.0]
        if abs(sum(fwd[i] * wu[i] for i in range(3))) > 0.999:
            wu = [0.0, 1.0, 0.0]
        rt = [fwd[1] * wu[2] - fwd[2] * wu[1],
              fwd[2] * wu[0] - fwd[0] * wu[2],
              fwd[0] * wu[1] - fwd[1] * wu[0]]
        n = math.sqrt(sum(x * x for x in rt)) or 1.0
        rt = [x / n for x in rt]
        up = [rt[1] * fwd[2] - rt[2] * fwd[1],
              rt[2] * fwd[0] - rt[0] * fwd[2],
              rt[0] * fwd[1] - rt[1] * fwd[0]]
        return fwd, rt, up

    framing, framing_fail = [], []
    for k in b1keys:
        t = k.get("focus_target")
        if t not in geo:
            continue
        ctr, rad = where(t, k["t"]), geo[t]["radius"]
        cam, look = k["world"], k["look_at"]
        lens = float(k["lens_mm"])
        d = [ctr[i] - cam[i] for i in range(3)]
        nd = math.sqrt(sum(x * x for x in d)) or 1.0
        fwd, rt, up = _basis(cam, look)
        c = max(-1.0, min(1.0, sum(fwd[i] * d[i] for i in range(3)) / nd))
        ang = math.degrees(math.acos(c))
        half_r = math.degrees(math.asin(min(1.0, rad / max(nd, rad))))
        near_edge = max(0.0, ang - half_r)
        far_edge = ang + half_r                       # <-- the one that overflows
        half_v = math.degrees(math.atan(0.5 * SENSOR_H_MM / lens))

        # the cluster's own box, translated to where it is at this film time
        cp = plan["clusters"][t]
        off = cp["explode_offset"]
        exp_ctr = geo[t]["centre"]
        sh = [ctr[i] - exp_ctr[i] for i in range(3)]
        blo = [cp["bbox_min"][i] + off[i] + sh[i] for i in range(3)]
        bhi = [cp["bbox_max"][i] + off[i] + sh[i] for i in range(3)]
        us, vs, zs = [], [], []
        for ix in (0, 1):
            for iy in (0, 1):
                for iz in (0, 1):
                    p = [blo[0] if ix == 0 else bhi[0],
                         blo[1] if iy == 0 else bhi[1],
                         blo[2] if iz == 0 else bhi[2]]
                    dd = [p[i] - cam[i] for i in range(3)]
                    z = sum(dd[i] * fwd[i] for i in range(3))
                    zs.append(z)
                    if z > 1e-6:
                        us.append(sum(dd[i] * rt[i] for i in range(3)) / z * lens)
                        vs.append(sum(dd[i] * up[i] for i in range(3)) / z * lens)
        if us:
            ext_h = (max(vs) - min(vs)) / SENSOR_H_MM
            ext_w = (max(us) - min(us)) / SENSOR_W_MM
        else:
            ext_h = ext_w = float("inf")

        # the f-number that would hold the whole box inside the pixel budget
        sfoc = float(k.get("focus_distance_m", nd)) * 1000.0
        z_lo, z_hi = min(zs) * 1000.0, max(zs) * 1000.0
        z_worst = z_lo if abs(z_lo - sfoc) > abs(z_hi - sfoc) else z_hi
        if z_worst > lens and sfoc > lens:
            n_req = (lens * lens * abs(z_worst - sfoc)
                     / (COC_MM * (sfoc - lens) * z_worst))
        else:
            n_req = float("inf")
        # and the standoff at which FILL_TARGET would be met on this lens
        s_fit = nd * max(ext_h, ext_w) / FILL_TARGET if max(ext_h, ext_w) else nd

        is_presentation = bool(k.get("presentation_dir_measured"))
        framing.append({"cluster": t, "t": k["t"], "range_m": round(nd, 3),
                        "edge_angle_deg": round(near_edge, 3),
                        "far_edge_angle_deg": round(far_edge, 3),
                        "half_frame_deg": round(half_v, 3),
                        "lens_mm": lens,
                        "extent_frac_frame_h": round(ext_h, 3),
                        "extent_frac_frame_w": round(ext_w, 3),
                        "depth_span_m": round((z_hi - z_lo) / 1000.0, 4),
                        "fstop_shipped": k.get("fstop"),
                        "fstop_required": (round(n_req, 2)
                                           if n_req != float("inf") else None),
                        "standoff_for_fill_m": round(s_fit, 3),
                        "fill_target": FILL_TARGET,
                        "sharp_budget_px": SHARP_BUDGET_PX,
                        "presentation": is_presentation})
        if is_presentation and max(ext_h, ext_w) > 1.0:
            framing_fail.append(
                "%s does not FIT its own presentation frame: %.2fx frame height, "
                "%.2fx frame width at t = %.2f s (%.0f mm, %.2f m). It would fit "
                "at %.2f m on this lens, and holding its %.2f m of depth inside "
                "%.1f px then needs f/%.1f against the shipped f/%.2f"
                % (t, ext_h, ext_w, k["t"], lens, nd, s_fit,
                   (z_hi - z_lo) / 1000.0, SHARP_BUDGET_PX,
                   n_req, k.get("fstop", 0.0)))
        elif not is_presentation and near_edge > half_v:
            # THE BRIDGES AND THE CLOSE-OUT KEEP THE OLD TEST, DELIBERATELY.
            # Those keys are hand-placed and reviewed, and they are SUPPOSED to
            # let a wing run off the edge of frame -- the front wing at t=25.90
            # reads 30.46 deg on the far edge against an 11.91 deg half-frame
            # and that is the shot, not a defect. The fit test is a claim about
            # a PRESENTATION: a station built to make one cluster large enough
            # to read has failed if the cluster does not fit. Applying it to a
            # composed wide would have failed two frames a review already
            # accepted, which is how a corrected metric loses its credibility.
            framing_fail.append(
                "%s is %.2f deg outside a %.2f deg half-frame at t = %.2f s "
                "(%.0f mm, %.2f m away)"
                % (t, near_edge - half_v, half_v, k["t"], lens, nd))

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
                "budget_ratio": {k: (round(v, 4) if isinstance(v, (int, float))
                                     else v) for k, v in budget.items()},
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
        "beat6": closing_lens_push(spec["beat6"]),
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
        # R2-451: overridable for the same reason B1_NORMALS is -- a candidate
        # sheet must be measurable end to end before docs/ is touched. The
        # carry-forward below still reads the SHIPPED sheet, so a candidate
        # inherits beats 2-5 exactly and the seam cannot drift by construction.
        dest = os.environ.get("B1_SHEET_OUT", os.path.join(DOCS, "beat_sheet.json"))
        if dest != os.path.join(DOCS, "beat_sheet.json"):
            print(f">> B1_SHEET_OUT override in force: {dest}")
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

        # R2-451: the carry-forward SOURCE is always the shipped sheet, never
        # `dest`. Reading `dest` was correct while dest was always the shipped
        # sheet; the moment B1_SHEET_OUT points somewhere new, `dest` does not
        # exist, `prev` is {}, and beats 2-5 and every aim declaration are
        # silently dropped -- the exact defect this whole block exists to
        # prevent, reintroduced by the flag that was added to make the block
        # safe to test. Named here because it is a one-character mistake with a
        # four-beat blast radius.
        carry_src = os.path.join(DOCS, "beat_sheet.json")
        if os.path.exists(carry_src):
            try:
                prev = json.load(open(carry_src))
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
    print(f">> beat 1: {len(order)} presentations covering {len(sched)} "
          f"clusters, path {path_len:.2f} m, mean camera speed "
          f"{mean_speed:.2f} m/s")
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
        big = max(r["extent_frac_frame_h"], r["extent_frac_frame_w"])
        print(f"   {r['cluster']:<16} t {r['t']:6.2f}s  {r['range_m']:5.2f} m  "
              f"{r['lens_mm']:4.0f} mm   fills {r['extent_frac_frame_h']:5.2f} x "
              f"{r['extent_frac_frame_w']:5.2f} of frame   far edge "
              f"{r['far_edge_angle_deg']:6.2f} vs half-frame "
              f"{r['half_frame_deg']:5.2f} deg   f/{str(r['fstop_shipped']):>4} "
              f"needs f/{r['fstop_required']}"
              + ("   <-- OVERFLOWS by %.2fx" % big if big > 1.0 else ""))

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
