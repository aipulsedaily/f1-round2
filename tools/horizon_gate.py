"""IS THE HORIZON LEVEL. The one thing about this camera nobody measures.

    .venv/bin/python tools/horizon_gate.py --path render/film11_path.json
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
  TILT: the angle between the camera's own right axis and the world horizontal
  plane, per frame, in degrees. Zero is a level horizon. It is computed from
  the path's quaternion and nothing else.

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

BEAT 6'S ROLL HAS NOW BEEN SEEN, AND IT SHOULD PROBABLY NOT BE FIXED. R2-091.

This gate FAILs beat 6 on 32 frames and I wrote it expecting that to be a
defect. Two frames were then rendered and they do not support the reading:

  f2680, tilt -33.8 deg   the pit wall runs diagonally across the frame, the
                          car sharp and centred, the pit lane legible. It reads
                          as a BANKED AERIAL -- the shot a helicopter makes
                          peeling away from a subject -- not as a camera
                          falling over.
  f2694, tilt  -0.07 deg  levelled, a clean legible aerial down the pit straight
                          with the pit lane, garage doors and timing gantry.

Beat 6's first declared move IS a peel-off. A camera that banks as it peels and
rolls level into the closing wide is that move, and the roll is smooth
throughout -- about 5.5 deg/frame with no discontinuity anywhere in it.

So the number is real, the instrument is right, and the verdict is a WAIVER
rather than a bug: **this is a known accepted exception pending a human
decision, not a defect to be fixed.** It is deliberately NOT tuned out of the
gate. A gate quietly re-tuned so it stops firing on something someone accepted
is worse than a gate with a waiver written next to it, because the next
regression in the same place would then be invisible too -- which is precisely
how the 79.77 deg roll at f1487 survived in the shipped film.

STILL UNSEEN: **f2666, the -59.88 deg peak.** f2680 and f2694 bracket it and
both read, but the peak itself has not been looked at. That is the frame to
queue before anyone acts on this either way.

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

CONTROLS — `--selftest`, six cases
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
  P3  the live `--path` over frames 2640-2700                   must FAIL
  N1  the live `--path` over frames 793-2600, beats 2 to 5    must PASS
      1,808 frames, every lens the film uses, from a 7.5 m/s launch to a
      101.9 m/s helicopter arc.
  N3  the live `--path` over beat 1, frames 1-792             must PASS
      **THIS ARM EXISTS BECAUSE IT CAUGHT THIS FILE OUT.** Beat 1 reaches
      20.83 deg at f135 and the first draft failed it on 34 frames. Any
      future change to the scope has to walk past the weave and stay quiet.
  N2  the live `--path` over frames 2700-2978, the closing hold must PASS
"""

import argparse
import json
import math
import os
import sys

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FPS = 24.0
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


def measure(P, lo, hi):
    rows = []
    prev = None
    for f in range(lo, hi + 1):
        if f not in P:
            continue
        r, u, fw = axes(P[f]["q"])
        tilt = _asin_deg(r[2])
        pitch = abs(_asin_deg(-fw[2]))
        row = {"f": f, "tilt_deg": tilt, "pitch_deg": pitch,
               "horizon_in_shot": pitch < HORIZON_PITCH_DEG,
               "lens_mm": float(P[f].get("lens", 35.0))}
        row["tilt_rate_deg"] = (tilt - prev) if prev is not None else 0.0
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
    judged, fails, warns = judge(rows, beat1_last)
    if not rows:
        return {"label": label, "frames": 0, "verdict": "PASS"}
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
            "fail_frames": _runs([r["f"] for r in fails]),
            "warn_frames": _runs([r["f"] for r in warns]),
            "n_fail": len(fails), "n_warn": len(warns),
            "verdict": "FAIL" if fails else "PASS"}


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
    tilt, pitch = _asin_deg(r[2]), abs(_asin_deg(-fw[2]))
    rows = [{"f": 10 ** 6, "tilt_deg": tilt, "pitch_deg": pitch,
             "horizon_in_shot": pitch < HORIZON_PITCH_DEG, "lens_mm": 24.0,
             "tilt_rate_deg": 0.0}]
    s = summarise(rows, "P2")
    ok = (pitch > HORIZON_PITCH_DEG and s["verdict"] == "PASS")
    print(f"  {'PASS' if ok else 'FAIL'}  P2 synthetic: the same 30 deg roll "
          f"pitched 80 deg down reads pitch {pitch:.3f} deg, so it is REPORTED "
          f"({tilt:.3f} deg) and NOT judged. This is the arm that stops the "
          f"gate firing on beat 5's declared top-down.")
    if not ok:
        bad.append("P2")

    P = {e["f"]: e for e in json.load(open(path_json))["path"]}
    for tag, lo, hi, want, note in (
            ("P3", 2640, 2700, "FAIL", "the beat-5 -> beat-6 peel-off"),
            ("N1", 793, 2600, "PASS", "beats 2-5, every lens the film uses"),
            ("N2", 2700, 2978, "PASS", "the closing hold"),
            ("N3", 1, 792, "PASS", "beat 1, the weave, which is refused")):
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
    ap.add_argument("--path", default=os.path.join(R2, "render/film11_path.json"))
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
    print(">> STAGE RESULT: " + ("HORIZON_LEVEL" if s["verdict"] == "PASS"
                                 else "HORIZON_ROLLED"))
    sys.exit(1 if s["verdict"] != "PASS" else 0)


if __name__ == "__main__":
    main()
