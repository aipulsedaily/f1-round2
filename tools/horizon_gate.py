"""IS THE HORIZON LEVEL. The one thing about this camera nobody measures.

    .venv/bin/python tools/horizon_gate.py --path world/camera_rig_path.json
    .venv/bin/python tools/horizon_gate.py --selftest --path <a built path>
    .venv/bin/python tools/horizon_gate.py --path <p> --dump --lo 2630 --hi 2700

WHY THIS EXISTS, AND WHY THE GAP WAS INVISIBLE
----------------------------------------------
Three instruments look at this camera's orientation and not one of them can
see a roll:

  * the RIG'S AIM GATE measures the angle from the camera's -Z to the declared
    subject. Roll is rotation ABOUT -Z, so it does not move the subject one
    pixel off the optical axis. **The aim gate is blind to roll by
    construction**, and R2-024 already logged the consequence once: "a
    top-down camera barrel-rolling at 36.9 deg/frame while the aim read 0.00".
  * `continuity_gate --campath`'s C1 measures TOTAL rotation per frame as a
    fraction of frame width. A roll shows up in it, but only as a rate: a
    camera that unwinds 60 deg of roll over 42 frames is doing 1.4 deg/frame,
    which on a 24 mm lens is 1.9 % of frame width against a 12 % WARN. **A
    slow roll is invisible to a rate detector precisely because it is slow.**
  * `tools/subject_sweep.py` measures how fast the subject crosses the frame.
    Roll does not move the subject.

So the quantity that is actually wrong — how far from level the picture IS —
was never a number. This file makes it one.

WHAT IS MEASURED
----------------
  TILT: the image rotation, `atan2(right.z, up.z)`, per frame, in degrees.
  Zero is a level horizon; +-180 is upside down. Computed from the path's
  quaternion and nothing else.

  **THE FIRST VERSION OF THIS FILE USED `asin(right.z)` AND IT WAS WRONG.**
  That is the angle of the right axis above the horizontal plane, and it
  SATURATES: it cannot tell a camera rolled theta from one rolled 180-theta,
  and it returns to zero as the camera passes through fully inverted. On this
  film's own beat 6 the consequence was not subtle -- the camera is inverted
  (`up.z < 0`) for **28 consecutive frames, f2636-f2663**, reaching **176.65 deg
  at f2651, 3.3 deg from perfectly upside-down, where the old metric reported
  +1.99 deg**. It called the worst frame in the film level.

      frame   asin(right.z)   atan2(right.z, up.z)   up.z
      f2651        + 1.99            +176.65        -0.594   inverted
      f2661        -52.92            -101.23        -0.158   inverted
      f2666        -59.88            - 81.71        +0.126
      f2680        -33.83            - 36.97        +0.740

  Found by a render agent who looked at f2666, measured the dominant
  straight-edge direction in the PIXELS at +83 deg from horizontal, and did
  not accept a geometry number that disagreed with the picture. The
  measurement that settles it is the sign of `up.z`, which the old metric
  discards entirely. Selftest P4 is now a camera rolled 170 deg, which the old
  metric scored as 10 deg.

  PITCH is measured alongside it and is the reason this gate does not simply
  threshold tilt. **A top-down shot has no horizon in it**, and "tilt" on a
  camera looking at the ground is not a defect, it is a choice of which way is
  up in a frame that has no up. Beat 5's declared last move is "directly over
  the car at 83 m/s" and it reads 79 deg of pitch; judging its roll would be
  judging the model.

  So the gate judges tilt ONLY where a horizon can be in shot: where the view
  direction is within `HORIZON_PITCH_DEG` of horizontal. The bound is stated
  rather than tuned — 45 deg is the pitch at which the horizon leaves a 3:2
  frame on the widest lens the film uses (18.8 mm, 86.6 deg horizontal, 62.4
  deg vertical: the frame's top edge reaches 31.2 deg above the axis, so at
  45 deg of pitch the horizon is already out of frame with 14 deg to spare).
  The measurement is therefore conservative in the direction of not firing.

  TILT RATE is reported and does not gate: `continuity_gate` already owns
  rotation rate and two gates owning one quantity is how they drift apart.

BEAT 6'S ROLL: THE WAIVER I WROTE DOES NOT HOLD, AND THE NUMBER IT WAS WRITTEN
ON WAS WRONG. R2-091, corrected.

I waived this roll as "a banked peel-off, not a defect" on the strength of
f2680 (reads as a banked aerial) and f2694 (levelled, clean). Both bracket the
peak. The peak was then rendered and it does not read:

  f2666   the frame is on its SIDE. The track runs top-to-bottom, the pit
          garages are a vertical stripe against the left edge, and there is no
          sky and no horizon anywhere in it. Measured from the pixels, the
          dominant straight-edge direction is **+83 deg from horizontal**,
          against -44 deg at f2680 and -29 deg at f2694 -- and -29 deg is the
          LEVEL reference, because the pit straight recedes diagonally even
          with the camera level. Quadrant luma agrees: the bright pit-building
          band is across the TOP at f2694, on a diagonal at f2680, and a
          VERTICAL band down the LEFT at f2666.

  f2680   reads as a bank, and the reason is visible: it has sky in its
          top-left corner, so the viewer can see which way up is. f2666 has no
          sky at all.

So the waiver is supported from about **f2673** onward, where the true tilt has
come back inside -59 deg, and is NOT supported across roughly **f2658-f2670**.

TWO THINGS THE OLD METRIC HID, both found by rendering the peak rather than
trusting the geometry:

  * The camera goes **fully inverted** -- `up.z < 0` -- for **28 consecutive
    frames, f2636-f2663**, peaking at **176.65 deg at f2651**, 3.3 deg from
    perfectly upside-down. The old `asin(right.z)` reported **+1.99 deg** there.
  * f2666 is not the peak. It is -81.71 deg, not the -59.88 deg first reported.

MOST OF THE INVERSION IS HARMLESS, AND THAT WAS CHECKED RATHER THAN ASSUMED.
f2646 and f2651 were rendered: they are near-nadir shots in which the car fills
the frame and there is no world reference at all, so being upside down is
invisible and they look good. The `|pitch| <= 45 deg` scope is doing exactly
its job there. The damage is confined to the frames where the world re-enters
shot while the roll is still past vertical -- **f2661 (-101 deg) and f2666
(-82 deg)**.

WHAT STANDS AND WHAT DOES NOT:
  * the gate FAILing beat 6 is correct and is not waived;
  * the peel-off reads from ~f2673 on, so the shape of the move is sound;
  * f2658-f2670 is a real defect, ~13 frames, and needs a fix that R2-089's
    two rejected candidates do not provide;
  * the film-wide waiver I proposed is withdrawn.

**A waiver written from bracketing frames is an assumption. This one was, and
the peak refuted it.**

TWO FIXES WERE COSTED AND BOTH WERE REJECTED, R2-089. The numbers are here so
the next agent does not pay for them again.

**1. Blend look_quat's roll REFERENCE instead of switching it.** The mechanism
behind beat 6's roll is that the reference flips from "direction of travel" to
"world +Z" as the camera pitches up out of the top-down, and the 3-deg-per-
frame correction limit turns that step into a 42-frame unroll. The obvious fix
is to blend. Blending the raw reference vectors is what produced 175 deg and
90 deg in the two attempts `look_quat`'s own docstring records, so this
candidate blended the two DESIRED UP VECTORS instead, by rotating one onto the
other about the view axis -- well conditioned everywhere, no cross product
whose sign can flip. Built and measured, worst tilt per beat, FAIL frames in
brackets:

    beat        1_assembly   4_transit   5_lap      6_ending
    shipped     20.83 ( 9)    2.08 (0)   0.90 (0)   59.88 (32)
    candidate   38.59 (49)    2.08 (0)   2.98 (0)   41.47 (14)

It halves beat 6 and nearly doubles beat 1. A fix that moves the defect to
another beat is not a fix.

**2. Raise the 3-deg-per-frame correction limit.** This is the cleanest-looking
knob on the file and it is the wrong one, because it converts a STATIC error --
a tilted horizon -- into a DYNAMIC one, a smearing roll, and this camera has no
headroom for the dynamic one. The full sweep, horizon on the left and
`continuity_gate --campath`'s rotation smear on the right:

  lim   b1 tilt(F)   b4         b5         b6          b1 rot   b5 rot   campath
  3.0   20.83 ( 9)   2.08 (0)   0.90 (0)   59.88 (32)   16.41 %  16.18 %  PASS
  6.0    7.95 ( 0)   0.02 (0)   0.21 (0)   63.31 (26)   22.09 %  18.16 %  PASS
 10.0    7.95 ( 0)   0.02 (0)   0.26 (0)   42.16 ( 8)   27.81 %  30.87 %  FAIL x2
 15.0    7.95 ( 0)   0.02 (0)   0.28 (0)    0.01 ( 0)   27.81 %  47.83 %  FAIL x3
 20.0    7.95 ( 0)   0.02 (0)   0.28 (0)    0.01 ( 0)   27.81 %  56.61 %  FAIL x3
 30.0    7.95 ( 0)   0.02 (0)   0.28 (0)    0.01 ( 0)   27.81 %  98.92 %  FAIL x3

At 15 deg the horizon problem vanishes ENTIRELY -- beat 6 goes to 0.01 deg --
and beat 5's rotation smear goes to 47.8 % of frame width, which is the exact
class of defect R2-085 was spent killing at f1461 (56.6 %). **The 3 deg limit is
not arbitrary; it is buying rotation legibility with horizon level, and one
number cannot satisfy both.**

So the fix has to be UPSTREAM: stop the roll error reaching 60 deg rather than
bleed it off faster. The two directions, neither taken here, are to give beat 6
a DECLARED roll -- its subject after t+6.0 is a fixed point, and a locked wide
on a fixed point wants world up, not a transported frame -- or to change the
authoring so the near-vertical view is never entered, which is what forces the
exit to cost 60 deg and is the same class of fix as R2-085. The second lives in
`tools/author_beats2_5.py`, at the t=109.60 anchor, "directly over the car at
83 m/s".

**None of this should be decided before a frame of it has been seen.** That is
the whole reason it is written down instead of committed.

SCOPE — BEAT 1 IS REFUSED, AND THE FIRST DRAFT OF THIS FILE DID NOT REFUSE IT
-----------------------------------------------------------------------------
Beat 1 is the weave through the exploded parts field, inside a darkened
showroom, on 35-58 mm lenses at steep down-angles. It has four short episodes
over 4 deg -- f135-148 running 20.8 -> 4.1, f165-169, f266-270, f525-534 --
and every one of them is a monotone unroll, `look_quat` doing exactly what it
exists to do as the camera comes back level over a part.

Judging them fired this gate on 34 frames of material somebody authored, which
is the same mistake `tools/subject_sweep.py` records catching in its own EXTENT
detector, and the same one `build_camera_rig.Subject` records about beat 1's
nominated cluster. Beat 1 is refused for the same reason those two refuse it:
its frame has no world horizon in it and its subject is a field, so a number
about either measures the model rather than the rig.

WHAT THE OTHER FIVE BEATS DO, which is what makes the bounds defensible:

    2_launch     72 judged frames    worst 0.01 deg
    3_breach    192                  worst 0.04 deg
    4_transit   134                  worst 2.08 deg
    5_lap     1,384                  worst 0.90 deg
    6_ending    322                  worst 59.88 deg   <- 34 frames over 4 deg

Four of the five hold the horizon inside 2.08 deg across 1,782 frames. The
fifth is what this gate was written to find.

THE BOUNDS
----------
  FAIL at 10 deg, WARN at 4 deg, and the film's own material is what sets
  them. Across beats 2 to 5 -- 1,782 judged frames, every lens the film uses,
  from a 7.5 m/s launch to a 101.9 m/s helicopter arc -- the tilt never
  exceeds **2.08 deg**. So 4 deg is 1.9x and 10 deg is 4.8x everything the
  film already does, and neither can fire on accepted material. `--census`
  re-derives that separation every run and refuses to certify the bounds if
  the film's own maximum has crept up to meet them, which is the idiom
  `tools/seam_gate.py --census` already uses so a threshold cannot go stale.

WHAT IT DOES NOT MEASURE
------------------------
It never opens a rendered frame, so it cannot tell you whether the horizon is
occluded, whether the shot reads, or whether a deliberate dutch angle is
deliberate. It reports geometry. A gate that says "10.4 deg at f2660" is a
reason to look at frame 2660, not a verdict about it.

CONTROLS — `--selftest`, seven cases
-----------------------------------
  P1  SYNTHETIC, closed form: a camera at the origin looking along +X with a
      known roll of exactly 30.000 deg applied about its own view axis. The
      gate must report 30.000000 deg of tilt and 0.000000 deg of pitch.
      A gate whose arithmetic is unchecked against a case with a closed form
      is an opinion.
  P2  SYNTHETIC: the same camera pitched 80 deg down and rolled 30 deg. The
      gate must report the tilt and must NOT judge it, because there is no
      horizon in the frame. This is the arm that stops the gate firing on
      beat 5's declared top-down.
  P4  SYNTHETIC: a camera rolled exactly 170 deg. The gate must read 170 deg
      and `up.z` must be negative. The metric this file shipped with read it
      as 10 deg. This arm exists because that metric survived a six-control
      selftest, a census and a published finding.
  P3  the live `--path` over frames 2640-2700                   must FAIL
  N1  the live `--path` over frames 793-2600, beats 2 to 5    must PASS
      1,808 frames, every lens the film uses, from a 7.5 m/s launch to a
      101.9 m/s helicopter arc.
  N3  the live `--path` over beat 1, frames 1-792         must be VACUOUS
      **THIS ARM EXISTS BECAUSE IT CAUGHT THIS FILE OUT.** Beat 1 reaches
      20.83 deg at f135 and the first draft failed it on 34 frames. Beat 1 is
      refused wholesale, so nothing in it is judged and the verdict is a
      REFUSAL, not a pass -- the distinction another agent added to this file
      on 2026-08-03, and the right one: a gate that judged nothing has proven
      nothing. Any future change to the scope has to walk past the weave and
      still refuse rather than quietly approve.
  N2  the live `--path` over frames 2700-2978, the closing hold must PASS
"""

import argparse
import json
import math
import re
import os
import sys

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FPS = 24.0
# THE DEFAULT PATH GOES STALE, AND IT DID.  R2-114.
#
# This gate shipped defaulting to `render/film11_path.json`. film12 was built
# twenty minutes later with R2-085's fix in it, the default was never moved, and
# the consequence was not a stale number in a report: the N1 arm of this file's
# own SELFTEST -- "beats 2 to 5 must PASS" -- ran against film11, found the
# 155.65 deg roll at f1464 that film12 had already fixed, and reported
# HORIZON_GATE_SELFTEST_BROKEN. **A negative control failing because its INPUT is
# a generation old is indistinguishable, on the printed line, from the gate being
# broken**, and this file had just been used to publish a finding.
#
# The default is now the CAMERA RIG'S OWN OUTPUT rather than a numbered film
# scene. `anim/build_camera_rig.py` writes it, `tools/build_film_scene.py`
# consumes it, and it is the authority on where the camera points; a numbered
# copy in render/ is a snapshot of it and there is a new one every time anybody
# assembles a scene. Deliberately NOT "the newest film*_path.json": picking up
# whatever a passing agent happened to drop in render/ is how a gate ends up
# judging something nobody chose.
DEFAULT_PATH = os.path.join(R2, "world/camera_rig_path.json")


def _stale_default_warning(chosen):
    """The rig's path is the default; say so if a film scene disagrees with it.

    A film*_path.json that differs from the rig means the assembled scene holds a
    DIFFERENT camera from the one this gate just judged -- which is the R2-114
    failure seen from the other end, and the frames come from the scene.
    """
    if os.path.abspath(chosen) != os.path.abspath(DEFAULT_PATH):
        return None
    d = os.path.join(R2, "render")
    if not os.path.isdir(d):
        return None
    try:
        mine = open(DEFAULT_PATH, "rb").read()
    except OSError:
        return None
    best, gen = None, -1
    for fn in os.listdir(d):
        m = re.fullmatch(r"film(\d+)([a-z]*)_path\.json", fn)
        if m and int(m.group(1)) > gen:
            best, gen = fn, int(m.group(1))
    if best is None:
        return None
    try:
        theirs = open(os.path.join(d, best), "rb").read()
    except OSError:
        return None
    if theirs == mine:
        return None
    return ("render/%s -- the newest assembled film scene -- holds a DIFFERENT "
            "camera from world/camera_rig_path.json, which is what was just "
            "judged. Rendered frames come from the scene. Re-assemble it, or "
            "pass --path render/%s to judge what will actually be rendered."
            % (best, best))


TILT_FAIL_DEG = 10.0
TILT_WARN_DEG = 4.0
HORIZON_PITCH_DEG = 45.0
GATE_VERSION = "horizon_gate/1.0.0"

# Beat 1 ends at film t = 33.0 s. Refused -- see SCOPE in the docstring. Taken
# from the sheet when one is available so a beat boundary that moves moves this
# too, and falling back to the declared frame only if the sheet cannot be read.
BEAT1_LAST_FRAME = 792


def _beat1_last_frame(sheet_path=None):
    try:
        sheet = json.load(open(sheet_path
                               or os.path.join(R2, "docs/beat_sheet.json")))
        t = next(b["start_s"] for b in sheet["beats"] if b["name"] == "2_launch")
        return int(round(t * FPS))
    except Exception:
        return BEAT1_LAST_FRAME


BEAT1_LAST_FRAME = _beat1_last_frame()


def axes(q):
    """(right, up, forward) from a quaternion (w, x, y, z), Blender's order.

    NORMALISED FIRST, and that is not decoration. The path file stores
    quaternions at six decimals, so |q| is not 1, and R2-068 records an
    instrument that reported 0.069 deg of rotation off components that were
    bit-identical because it skipped exactly this step. The same trap was
    walked into again while measuring the blast radius of R2-085.
    """
    n = math.sqrt(sum(c * c for c in q)) or 1.0
    w, x, y, z = [c / n for c in q]
    right = (1 - 2 * (y * y + z * z), 2 * (x * y + w * z), 2 * (x * z - w * y))
    up = (2 * (x * y - w * z), 1 - 2 * (x * x + z * z), 2 * (y * z + w * x))
    fwd = (-2 * (x * z + w * y), -2 * (y * z - w * x), -(1 - 2 * (x * x + y * y)))
    return right, up, fwd


def _asin_deg(v):
    return math.degrees(math.asin(max(-1.0, min(1.0, v))))


def tilt_deg(right, up):
    """Image rotation about the view axis. 0 level, +-180 upside down.

    NOT `asin(right.z)`. See the docstring: that saturates at +-90 and reported
    a camera 3.3 deg from inverted as 1.99 deg from level.
    """
    return math.degrees(math.atan2(right[2], up[2]))


def measure(P, lo, hi):
    rows = []
    prev = None
    for f in range(lo, hi + 1):
        if f not in P:
            continue
        r, u, fw = axes(P[f]["q"])
        tilt = tilt_deg(r, u)
        pitch = abs(_asin_deg(-fw[2]))
        row = {"f": f, "tilt_deg": tilt, "pitch_deg": pitch,
               "inverted": bool(u[2] < 0.0),
               "horizon_in_shot": pitch < HORIZON_PITCH_DEG,
               "lens_mm": float(P[f].get("lens", 35.0))}
        if prev is None:
            row["tilt_rate_deg"] = 0.0
        else:                              # wrap: 179 -> -179 is 2 deg, not 358
            d = (tilt - prev + 180.0) % 360.0 - 180.0
            row["tilt_rate_deg"] = d
        rows.append(row)
        prev = tilt
    return rows


def judge(rows, beat1_last=None):
    b1 = BEAT1_LAST_FRAME if beat1_last is None else beat1_last
    judged = [r for r in rows if r["horizon_in_shot"] and r["f"] > b1]
    fails = [r for r in judged if abs(r["tilt_deg"]) >= TILT_FAIL_DEG]
    warns = [r for r in judged
             if TILT_WARN_DEG <= abs(r["tilt_deg"]) < TILT_FAIL_DEG]
    return judged, fails, warns


def _runs(fs):
    out, cur = [], []
    for f in fs:
        if cur and f == cur[-1] + 1:
            cur.append(f)
        else:
            if cur:
                out.append((cur[0], cur[-1]))
            cur = [f]
    if cur:
        out.append((cur[0], cur[-1]))
    return out


def summarise(rows, label, beat1_last=None):
    """VERDICT IS ONE OF PASS / FAIL / VACUOUS, AND VACUOUS IS NOT A PASS.

    Both empty cases used to return "PASS" and the gate printed HORIZON_LEVEL
    and exited 0 (fixed 2026-08-03):

      * `rows` empty -- `--lo/--hi` outside the path's frame range. The gate
        reported a level horizon for a window it had not looked at.
      * `judged` empty -- every frame pitched further than HORIZON_PITCH_DEG
        from horizontal, so no frame was eligible. A camera rolled 80 deg while
        pointed at the floor passed, because nothing was measured.

    A horizon gate that measured no frames has not shown the horizon is level.
    It is a REFUSAL (exit 3), and the message says what would make it
    measurable, per the project's "unproven is a FAIL" rule.
    """
    judged, fails, warns = judge(rows, beat1_last)
    if not rows:
        return {"label": label, "frames": 0, "frames_with_horizon": 0,
                "verdict": "VACUOUS",
                "why": "no frames in range. Nothing was measured, so nothing "
                       "is proven about the horizon. Check --lo/--hi against "
                       "the frame range in the path file."}
    worst = max(judged, key=lambda r: abs(r["tilt_deg"])) if judged else None
    worst_any = max(rows, key=lambda r: abs(r["tilt_deg"]))
    return {"label": label, "span": [rows[0]["f"], rows[-1]["f"]],
            "frames": len(rows), "frames_with_horizon": len(judged),
            "worst_judged_tilt_deg": worst["tilt_deg"] if worst else 0.0,
            "worst_judged_frame": worst["f"] if worst else 0,
            "worst_judged_pitch_deg": worst["pitch_deg"] if worst else 0.0,
            "worst_tilt_anywhere_deg": worst_any["tilt_deg"],
            "worst_tilt_anywhere_frame": worst_any["f"],
            "worst_tilt_anywhere_pitch_deg": worst_any["pitch_deg"],
            "inverted_frames": sum(1 for r in rows if r.get("inverted")),
            "inverted_runs": _runs([r["f"] for r in rows if r.get("inverted")]),
            "fail_frames": _runs([r["f"] for r in fails]),
            "warn_frames": _runs([r["f"] for r in warns]),
            "n_fail": len(fails), "n_warn": len(warns),
            "verdict": ("FAIL" if fails else
                        ("PASS" if judged else "VACUOUS")),
            "why": (None if judged else
                    "%d frame(s) in range and NOT ONE of them was judged: "
                    "every one is pitched more than %.0f deg from horizontal, "
                    "so the horizon is not in shot anywhere here. A gate that "
                    "judged nothing has proven nothing."
                    % (len(rows), HORIZON_PITCH_DEG))}


def report(s):
    if not s.get("frames"):
        print(f"  {s['label']}: no frames")
        return
    print(f"  {s['label']}: frames {s['span'][0]}-{s['span'][1]}, "
          f"{s['frames_with_horizon']} of {s['frames']} judged "
          f"(a horizon in shot, and not beat 1)")
    print(f"    worst tilt WITH a horizon   {s['worst_judged_tilt_deg']:7.2f} deg "
          f"at f{s['worst_judged_frame']} (pitch "
          f"{s['worst_judged_pitch_deg']:.1f} deg)")
    print(f"    worst tilt anywhere         {s['worst_tilt_anywhere_deg']:7.2f} deg "
          f"at f{s['worst_tilt_anywhere_frame']} (pitch "
          f"{s['worst_tilt_anywhere_pitch_deg']:.1f} deg — not judged if over "
          f"{HORIZON_PITCH_DEG:.0f})")
    if s.get("inverted_frames"):
        print(f"    CAMERA INVERTED (up.z < 0) on {s['inverted_frames']} frames "
              f"{s['inverted_runs']} — the old asin(right.z) metric read these "
              f"as approaching LEVEL")
    print(f"    {s['n_fail']} FAIL frames {s['fail_frames'] or ''}")
    print(f"    {s['n_warn']} WARN frames {s['warn_frames'] or ''}")
    print(f"    -> {s['verdict']}")


# ---------------------------------------------------------------- selftest --
def _synth(pitch_deg, roll_deg):
    """A camera looking along +X, pitched down, then rolled about its own axis.

    Built from axis-angle products rather than from the formula this file
    inverts, so the test and the thing tested do not share their arithmetic.
    """
    def qmul(a, b):
        w1, x1, y1, z1 = a
        w2, x2, y2, z2 = b
        return (w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
                w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
                w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
                w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2)

    def aa(axis, deg):
        h = math.radians(deg) / 2.0
        n = math.sqrt(sum(c * c for c in axis))
        s = math.sin(h) / n
        return (math.cos(h), axis[0] * s, axis[1] * s, axis[2] * s)

    # Blender camera: -Z is the view axis, +Y is up, +X is right.
    # Start from a camera looking along world +X with world +Z up:
    #   -Z -> +X,  +Y -> +Z,  +X -> +Y
    base = qmul(aa((0, 0, 1), 90.0), aa((1, 0, 0), 90.0))
    # pitch DOWN about the camera's own right axis, then roll about its view
    q = qmul(base, aa((1, 0, 0), -pitch_deg))
    q = qmul(q, aa((0, 0, 1), -roll_deg))
    return q


def selftest(path_json):
    bad = []

    q = _synth(0.0, 30.0)
    r, u, fw = axes(q)
    tilt, pitch = _asin_deg(r[2]), abs(_asin_deg(-fw[2]))
    ok = abs(abs(tilt) - 30.0) < 1e-6 and pitch < 1e-6
    print(f"  {'PASS' if ok else 'FAIL'}  P1 synthetic: a camera on the "
          f"horizontal rolled exactly 30.000 deg reads tilt {tilt:.6f} deg, "
          f"pitch {pitch:.6f} deg")
    if not ok:
        bad.append("P1")

    q = _synth(80.0, 30.0)
    r, u, fw = axes(q)
    tilt, pitch = tilt_deg(r, u), abs(_asin_deg(-fw[2]))
    rows = [{"f": 10 ** 6, "tilt_deg": tilt, "pitch_deg": pitch,
             "inverted": bool(u[2] < 0.0),
             "horizon_in_shot": pitch < HORIZON_PITCH_DEG, "lens_mm": 24.0,
             "tilt_rate_deg": 0.0}]
    s = summarise(rows, "P2")
    ok = (pitch > HORIZON_PITCH_DEG and s["verdict"] == "VACUOUS")
    print(f"  {'PASS' if ok else 'FAIL'}  P2 synthetic: the same 30 deg roll "
          f"pitched 80 deg down reads pitch {pitch:.3f} deg, so it is REPORTED "
          f"({tilt:.3f} deg) and NOT judged -- verdict {s['verdict']}, which is "
          f"a REFUSAL and not a pass. This is the arm that stops the gate "
          f"firing on beat 5's declared top-down.")
    if not ok:
        bad.append("P2")

    q = _synth(0.0, 170.0)
    r, u, fw = axes(q)
    true, old = tilt_deg(r, u), _asin_deg(r[2])
    ok = abs(abs(true) - 170.0) < 1e-6 and abs(abs(old) - 10.0) < 1e-6 and u[2] < 0
    print(f"  {'PASS' if ok else 'FAIL'}  P4 synthetic, THE ARM THAT WOULD HAVE "
          f"CAUGHT THIS FILE: a camera rolled exactly 170.000 deg -- 10 deg from "
          f"upside down -- reads {abs(true):.6f} deg on atan2(right.z, up.z) and "
          f"{abs(old):.6f} deg on the asin(right.z) this file used to use. up.z "
          f"= {u[2]:+.4f}, so the sign alone settles it.")
    if not ok:
        bad.append("P4")

    P = {e["f"]: e for e in json.load(open(path_json))["path"]}
    for tag, lo, hi, want, note in (
            ("P3", 2640, 2700, "FAIL", "the beat-5 -> beat-6 peel-off"),
            ("N1", 793, 2600, "PASS", "beats 2-5, every lens the film uses"),
            ("N2", 2700, 2978, "PASS", "the closing hold"),
            ("N3", 1, 792, "VACUOUS",
             "beat 1, the weave: refused wholesale, so NOTHING is judged and "
             "the verdict is a refusal rather than a pass")):
        s = summarise(measure(P, lo, hi), tag)
        ok = s["verdict"] == want
        print(f"  {'PASS' if ok else 'FAIL'}  {tag} f{lo}-{hi} ({note}): "
              f"{s['verdict']}, expected {want}. worst tilt with a horizon "
              f"{s['worst_judged_tilt_deg']:.2f} deg at f{s['worst_judged_frame']}, "
              f"{s['n_fail']} FAIL / {s['n_warn']} WARN frames")
        if not ok:
            bad.append(tag)
    return bad


def census(P):
    """The film's own tilt distribution, so the bounds can be re-derived.

    Refuses to certify if the maximum OUTSIDE the known region has crept up to
    meet the WARN bound — the same idiom `tools/seam_gate.py --census` uses so
    a threshold cannot quietly go stale.
    """
    rows = measure(P, min(P), max(P))
    judged, _f, _w = judge(rows)
    known = [r for r in judged if 2640 <= r["f"] <= 2700]
    other = [r for r in judged if not (2640 <= r["f"] <= 2700)]
    m_other = max((abs(r["tilt_deg"]) for r in other), default=0.0)
    m_known = max((abs(r["tilt_deg"]) for r in known), default=0.0)
    print(f"=== CENSUS over {len(rows)} frames, {len(judged)} judged "
          f"(pitch < {HORIZON_PITCH_DEG:.0f} deg, beat 1 refused)")
    print(f"  worst tilt OUTSIDE f2640-2700   {m_other:6.2f} deg")
    print(f"  worst tilt INSIDE  f2640-2700   {m_known:6.2f} deg")
    print(f"  the shipped bounds are {TILT_WARN_DEG:.0f} deg WARN / "
          f"{TILT_FAIL_DEG:.0f} deg FAIL")
    ok = m_other < TILT_WARN_DEG < TILT_FAIL_DEG < m_known
    print(f"  {'PASS' if ok else 'FAIL'}  the bounds still lie strictly between "
          f"what the film does and what it is being judged for")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", default=DEFAULT_PATH)
    ap.add_argument("--lo", type=int)
    ap.add_argument("--hi", type=int)
    ap.add_argument("--dump", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--census", action="store_true")
    ap.add_argument("--json-out")
    a = ap.parse_args()

    if a.selftest:
        bad = selftest(a.path)
        print(">> STAGE RESULT: " + ("HORIZON_GATE_SELFTEST_OK" if not bad
                                     else "HORIZON_GATE_SELFTEST_BROKEN"))
        sys.exit(1 if bad else 0)

    P = {e["f"]: e for e in json.load(open(a.path))["path"]}
    if a.census:
        ok = census(P)
        print(">> STAGE RESULT: " + ("HORIZON_CENSUS_OK" if ok
                                     else "HORIZON_CENSUS_STALE"))
        sys.exit(0 if ok else 1)

    lo = a.lo if a.lo is not None else min(P)
    hi = a.hi if a.hi is not None else max(P)
    rows = measure(P, lo, hi)
    print(f"  source: {a.path}")
    _w = _stale_default_warning(a.path)
    if _w:
        print("  STALE DEFAULT: " + _w)
    print(f"  bounds: {TILT_WARN_DEG:.0f} deg WARN / {TILT_FAIL_DEG:.0f} deg "
          f"FAIL, judged only where the view is within "
          f"{HORIZON_PITCH_DEG:.0f} deg of horizontal")
    s = summarise(rows, "WHOLE RANGE")
    report(s)
    if a.dump:
        print("    f    tilt deg  rate deg/f   pitch deg  horizon?  lens")
        for r in rows:
            print(f"  {r['f']:5d} {r['tilt_deg']:10.3f} {r['tilt_rate_deg']:11.3f} "
                  f"{r['pitch_deg']:11.2f}  {'yes' if r['horizon_in_shot'] else ' no'}"
                  f"    {r['lens_mm']:6.1f}")
    if a.json_out:
        json.dump({"gate": GATE_VERSION, "path": os.path.abspath(a.path),
                   "summary": s, "rows": rows}, open(a.json_out, "w"), indent=1)
    if s.get("why"):
        print("  REFUSING: " + s["why"])
    print(">> STAGE RESULT: " + {"PASS": "HORIZON_LEVEL",
                                 "FAIL": "HORIZON_ROLLED",
                                 "VACUOUS": "HORIZON_VACUOUS"}[s["verdict"]])
    # 0 PASS / 1 FAIL / 3 VACUOUS, matching tools/gate_exit.py so a battery's
    # `expect vacuous` can tell "it refused" from "it passed".
    sys.exit({"PASS": 0, "FAIL": 1, "VACUOUS": 3}[s["verdict"]])


if __name__ == "__main__":
    main()
