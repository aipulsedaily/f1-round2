"""THE BEAT-1 -> BEAT-2 SEAM, measured. R2-064.

    .venv/bin/python tools/seam_gate.py --path render/film9_path.json
    .venv/bin/python tools/seam_gate.py --selftest --path <a built path>
    .venv/bin/python tools/seam_gate.py --census --path <a built path>

WHAT THIS IS FOR
----------------
Beat 1's last camera key is at film t = 31.4 (frame 754) and beat 2's first is
at t = 33.041667 (frame 793). Between them the sheet declared NOTHING, so for
39 frames the path was whatever Blender's AUTO_CLAMPED handles decided, and the
handle at frame 793 was computed from a 39-frame neighbour on its left and a
2-frame neighbour on its right. The measured consequence is in `--selftest`'s
positive control: the curve runs 2.61x the chord speed of the key pair it lies
between, and 98.5 m/s^2 arrives in one frame.

`work/campath/beat1_probe.py` already prints four seam numbers, and it takes
them from `sorted(beat1.camera_keys)[-1]` and `sorted(beat2.camera_keys)[0]` —
by LIST POSITION. That is fine while nothing is inserted between them and
useless the moment something is, because it would silently start measuring a
different pair of keys and report four different numbers as though the seam had
moved. This gate pins the two keys BY THEIR DECLARED FILM TIME, so inserting
keys between them cannot change what it measures.

WHAT IS MEASURED, and every number is in real units

  1. THE FOUR INVARIANTS, at t = 31.4 and t = 33.041667, from the sheet:
     chord (m), mean speed over the gap (m/s), the angle between the two look
     directions (deg), and the focal-length step (mm). These are beat 1's
     hand-off contract and they are held to 1e-4.

  2. THE SAME TWO KEYS IN THE BUILT ARTEFACT. The declared positions are also
     checked against the per-frame path at frames 754 and 793, because a sheet
     that declares a seam and a rig that builds a different one is exactly the
     failure this project keeps paying for. Intent is not artefact.

  3. BULGE — the one that catches the handle artefact, and it is SCALE-FREE.
     For every consecutive pair of camera keys inside the window, the fastest
     per-frame step between them against the CHORD speed of that same pair.
     A curve may not run more than `TOL_BULGE` times faster than the two keys
     it is interpolating between.

     Why per-pair and not "peak speed in the window against the fastest key
     pair in the window": the second compares a frame in one interval to a
     different interval's chord, so it reads +14 % on a curve that is 161 %
     over the pair it actually sits between. Both are printed; only the
     per-pair one gates.

     ONLY PAIRS `MAX_BULGE_GAP` FRAMES APART OR LESS ARE GATED. Across half a
     second the curve should be close to the straight line between its two
     keys; across 47 frames a camera legitimately accelerates and decelerates,
     and this one does — beat 1's f339-386 runs 2.061x its own chord and is
     accepted material. Long pairs are printed by `--census` and not judged.

     WHERE 1.80 COMES FROM — a census, not a preference. `--census` walks every
     key interval of the whole 2,978-frame film and prints the distribution. On
     the pre-fix build the worst GATED interval outside this window is 1.570x
     (f2313-2321, beat 5) and the worst inside it is 2.247x (f812-820). 1.80
     sits 15 % above everything the film already does and 21 % below the
     defect. `--selftest` RE-RUNS that census and refuses to certify the bound
     if it has stopped separating the two, so the number cannot quietly go
     stale.

     A pair whose chord is under `HOLD_CHORD_MS` is a HOLD and a ratio against
     it is a division by the measurement's own floor. Those are judged against
     an absolute peak instead of being skipped, because silently skipping them
     would leave a hole exactly where a camera is meant to be still — the one
     place a wandering bezier is most visible.

  4. LOCAL ACCELERATION RATIO, not a global limit. |a| at a frame against the
     MEDIAN |a| of its +-8 frame neighbourhood, which is the idiom
     `tools/car_anim_gate.py` D already uses and the one MASTER-PLAN section 6
     item 26 exists to recommend: a global threshold either passes a spike
     sitting on a fast passage or fails a whole fast passage. A spike is a
     LOCAL event and has to be measured locally.

     Film-wide on the pre-fix build the p99 is 2.88x and the p99.9 is 6.61x.
     The bound is 6.0x. TWO FRAMES OUTSIDE THIS WINDOW EXCEED IT and are
     reported by `--census` rather than absorbed: f463 (8.82x, beat 1) and
     f2680 (13.76x, one frame past R2-063's beat-5/6 blend). Neither is this
     gate's window and neither is claimed to be fixed here.

  5. SMEAR. Rotation per frame as a percentage of the frame's own horizontal
     field of view, which is the quantity `work/campath/beat1_probe.py` reports
     and R2-062 was judged on, so the two are comparable. WARN only: the smear
     bound belongs to whoever is looking at frames.

WHAT THIS GATE DOES NOT MEASURE, stated so nobody assumes it does
-----------------------------------------------------------------
It never opens a rendered frame. Everything here is geometry off the camera
path. It cannot tell you the seam LOOKS right; it can only tell you the camera
is not doing something the authoring never asked for. A picture is still
required and this is not a substitute for one.

CONTROLS — `--selftest` runs six cases whose verdicts are known in advance,
three that must FAIL and three that must PASS, plus the census assertion above,
and exits non-zero unless every one of them behaves:

  P1  the shipped pre-fix path at the seam, kept at
      `work/campath/seam_pre_R2064.json`                          must FAIL
      It fails on BULGE and on SPIKE independently.
  P2  beat 3 frames 900-1000 — which passes clean — with a +25 %
      overshoot injected inside one key interval                  must FAIL
  P3  the current build against a sheet in which one beat-2 key
      pair has been collapsed onto a single position, i.e. a
      declared hold that the path does not hold                   must FAIL
      This one exists because the HOLD branch is the only test a
      BULGE ratio cannot express, and an untested branch in a gate
      is not a test.
  N1  beat 3 frames 900-1000, untouched. REAL material at the same
      3-10 m/s the seam runs at, and nothing to do with any fix
      applied here                                                must PASS

      Beat 1 is NOT a control window and cannot be: its keys are 33
      frames apart there, so no pair is inside MAX_BULGE_GAP and the
      gate refuses it rather than reporting a ratio it did not
      measure. That refusal is the correct behaviour and it is why
      the control moved to a beat whose keys this can judge.
  N2  beat 5 frames 1100-1180, untouched. 73 m/s. Proves the tests
      are measuring overshoot and spikes and not merely speed      must PASS
  N3  the live `--path` at the seam window                        must PASS

P2 and N1 are one artefact and its perturbation, which is the only way to show
BULGE measures overshoot rather than smoothness. N2 exists because a gate that
only ever saw a 3 m/s showroom drift would not have earned the right to judge a
camera that also flies at 100 m/s.
"""

import argparse
import copy
import json
import math
import os
import statistics
import sys

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FPS = 24.0
SENSOR_W_MM = 36.0

# The two keys that ARE the seam, by declared film time. Not by list position.
B1_LAST_T = 31.4
B2_FIRST_T = 33.041667
T_EPS = 1e-5

# Beat 1's declared hand-off contract, as measured before any of this work and
# quoted in beat 1's own last-key note. These are held, not re-derived.
DECLARED = {
    "chord_m": 2.0893,
    "speed_ms": 1.2727,
    "look_angle_deg": 13.2504,
    "lens_delta_mm": -0.051,
}
TOL_INVARIANT = 1e-4
TOL_ARTEFACT_M = 1e-3

# The window. It opens 16 frames before beat 1's last key so the approach is in
# it, and closes at frame 832, three frames past the end of the sanctioned
# wheelspin, so the whole descend-settle-hold move is inside one measurement.
W_LO, W_HI = 738, 832

TOL_BULGE = 1.80
MAX_BULGE_GAP = 12     # frames; see below
TOL_ACCEL_RATIO = 6.0
TOL_ROT_PCT = 12.0
# A key pair whose two keys are less than this far apart is a HOLD, and a bulge
# RATIO against it is a division by the measurement's own floor. Held to an
# absolute peak instead. 0.15 m/s is 6 mm per frame; 0.30 m/s is 12 mm.
HOLD_CHORD_MS = 0.15
HOLD_PEAK_MS = 0.30
NBHD = 8


# ------------------------------------------------------------------ helpers --
def load_path(p):
    doc = json.load(open(p))
    return {e["f"]: e for e in doc["path"]}


def key_at(keys, t):
    """The key at a declared film time. Refuses to guess."""
    hits = [k for k in keys if abs(float(k["t"]) - t) < T_EPS]
    if len(hits) != 1:
        raise SystemExit(f">> FAIL: expected exactly one key at t={t}, "
                         f"found {len(hits)}")
    return hits[0]


def look_dir(k):
    d = [k["look_at"][i] - k["world"][i] for i in range(3)]
    n = math.hypot(*d) or 1.0
    return [x / n for x in d]


def all_sheet_keys(sheet):
    """Every camera key the rig will build, from every block that holds one.

    Driven by what is in the file, so a block added later cannot be missed by a
    hardcoded list of two names — which is the defect that left beats 2-5 with
    no camera at all. Beat 6 is deliberately absent: its keys are stored
    RELATIVE to its own start and are resampled by `beat6_path()`, so they are
    not comparable and this gate refuses windows that contain only those.
    """
    out = []
    for name, block in sheet.items():
        if not isinstance(block, dict):
            continue
        for k in block.get("camera_keys") or []:
            if "world" in k and "t" in k:
                out.append(dict(k, _block=name))
    return sorted(out, key=lambda k: float(k["t"]))


def key_pairs(ks, lo, hi, max_gap=None):
    """Consecutive key pairs wholly inside [lo, hi], as (fa, fb, chord_speed).

    `max_gap` drops pairs further apart than that. BULGE is only meaningful
    over a SHORT interval: across 47 frames a camera legitimately accelerates
    and decelerates, and the film does — beat 1's f339-386 runs 2.061x its own
    chord and is accepted material. Across half a second it should be close to
    the straight line between its two keys. Long pairs are still reported by
    `--census`; they are not gated, and this is the reason.
    """
    out = []
    for i in range(len(ks) - 1):
        fa = int(round(float(ks[i]["t"]) * FPS))
        fb = int(round(float(ks[i + 1]["t"]) * FPS))
        dts = float(ks[i + 1]["t"]) - float(ks[i]["t"])
        if fb <= fa or dts <= 0 or fa < lo or fb > hi:
            continue
        if max_gap is not None and fb - fa > max_gap:
            continue
        out.append((fa, fb, math.dist(ks[i]["world"], ks[i + 1]["world"]) / dts))
    return out


def series(path, lo, hi):
    fs = [f for f in range(lo, hi + 1) if f in path and (f - 1) in path]
    spd = {f: math.dist(path[f - 1]["p"], path[f]["p"]) * FPS for f in fs}
    acc = {f: (spd[f] - spd[f - 1]) * FPS for f in fs if (f - 1) in spd}
    rot = {}
    for f in fs:
        q0, q1 = path[f - 1]["q"], path[f]["q"]
        n0 = math.sqrt(sum(x * x for x in q0)) or 1.0
        n1 = math.sqrt(sum(x * x for x in q1)) or 1.0
        dot = min(1.0, abs(sum((a / n0) * (b / n1) for a, b in zip(q0, q1))))
        dth = math.degrees(2 * math.acos(dot))
        hfov = math.degrees(2 * math.atan(SENSOR_W_MM / (2 * path[f - 1]["lens"])))
        rot[f] = 100.0 * dth / hfov
    return spd, acc, rot


def local_ratio(acc):
    worst = (0.0, None, None, None)
    for f in sorted(acc):
        nb = [abs(acc[g]) for g in range(f - NBHD, f + NBHD + 1)
              if g in acc and g != f]
        if len(nb) < NBHD:
            continue
        med = statistics.median(nb)
        r = abs(acc[f]) / med if med > 1e-6 else (
            float("inf") if abs(acc[f]) > 1.0 else 0.0)
        if r > worst[0]:
            worst = (r, f, acc[f], med)
    return worst


def measure(path, sheet, lo=W_LO, hi=W_HI, seam_checks=True):
    o = {"window": [lo, hi], "seam_checks": seam_checks}

    if seam_checks:
        b1 = key_at(sheet["beat1"]["camera_keys"], B1_LAST_T)
        b2 = key_at(sheet["beat2"]["camera_keys"], B2_FIRST_T)
        chord = math.dist(b1["world"], b2["world"])
        dt = float(b2["t"]) - float(b1["t"])
        d0, d1 = look_dir(b1), look_dir(b2)
        ang = math.degrees(math.acos(
            max(-1.0, min(1.0, sum(x * y for x, y in zip(d0, d1))))))
        o["inv"] = {"chord_m": round(chord, 4), "dt_s": round(dt, 5),
                    "speed_ms": round(chord / dt, 4),
                    "look_angle_deg": round(ang, 4),
                    "lens_delta_mm": round(b2["lens_mm"] - b1["lens_mm"], 4)}
        o["inv_moved"] = {k: (o["inv"][k], v) for k, v in DECLARED.items()
                          if abs(o["inv"][k] - v) > TOL_INVARIANT}
        f1 = int(round(B1_LAST_T * FPS))
        f2 = int(round(B2_FIRST_T * FPS))
        o["seam_frames"] = [f1, f2]
        o["artefact_err_m"] = {
            str(f1): round(math.dist(path[f1]["p"], b1["world"]), 6),
            str(f2): round(math.dist(path[f2]["p"], b2["world"]), 6)}
        o["artefact_lens_err_mm"] = {
            str(f1): round(path[f1]["lens"] - b1["lens_mm"], 6),
            str(f2): round(path[f2]["lens"] - b2["lens_mm"], 6)}
    else:
        o["inv"], o["inv_moved"], o["artefact_err_m"] = {}, {}, {}

    spd, acc, rot = series(path, lo, hi)
    o["v_max_ms"], o["v_max_f"] = max((v, f) for f, v in spd.items())

    pairs = key_pairs(all_sheet_keys(sheet), lo, hi, MAX_BULGE_GAP)
    if not pairs:
        o["refuse"] = (f"no consecutive camera-key pair closer than "
                       f"{MAX_BULGE_GAP} frames lies wholly inside frames "
                       f"{lo}-{hi}, so there is nothing to compare the "
                       f"interpolation against. Widen the window, or emit keys "
                       f"at a spacing this can judge.")
        return o
    o["refuse"] = None
    bulges = []
    for fa, fb, cv in pairs:
        mv = max(spd[f] for f in range(fa + 1, fb + 1) if f in spd)
        if cv < HOLD_CHORD_MS:
            # A HOLD. `mv / cv` is not a ratio here, it is a division by the
            # measurement's own floor, and silently skipping these pairs would
            # leave a hole exactly where a camera is supposed to be still — the
            # one place a bezier wandering is most visible. Judged absolutely
            # instead, and if a hold ever needs to be judged it will be by this
            # branch and not by an omission.
            if mv > HOLD_PEAK_MS:
                o.setdefault("hold_fail", []).append(
                    (fa, fb, round(cv, 4), round(mv, 4)))
            continue
        bulges.append((mv / cv, fa, fb, cv, mv))
    if not bulges:
        o["refuse"] = (f"every key pair inside frames {lo}-{hi} is a hold "
                       f"(chord under {HOLD_CHORD_MS} m/s). BULGE cannot be "
                       f"computed and this gate will not report a ratio it did "
                       f"not measure.")
        return o
    bulges.sort(reverse=True)
    o["bulge"], o["bulge_f0"], o["bulge_f1"], o["bulge_chord_ms"], \
        o["bulge_peak_ms"] = bulges[0]
    o["bulge_top"] = [[round(b[0], 3), b[1], b[2]] for b in bulges[:5]]
    o["authored_max_ms"] = max(cv for _fa, _fb, cv in pairs)
    o["peak_vs_fastest_pair_pct"] = 100.0 * (
        o["v_max_ms"] / o["authored_max_ms"] - 1.0)

    r, f, a, med = local_ratio(acc)
    o["accel_ratio"], o["accel_ratio_f"] = r, f
    o["accel_at_ratio"], o["accel_nbhd_median"] = a, med
    o["accel_abs_max"], o["accel_abs_max_f"] = max(
        (abs(v), k) for k, v in acc.items())
    o["rot_max_pct"], o["rot_max_f"] = max((v, f) for f, v in rot.items())
    o["series"] = {str(f): [round(spd[f], 4), round(acc.get(f, 0.0), 2),
                            round(rot[f], 2)] for f in sorted(spd)}
    return o


def verdict(o):
    fails, warns = [], []
    if o.get("refuse"):
        return ["REFUSED: " + o["refuse"]], []
    for k, (got, want) in o["inv_moved"].items():
        fails.append(f"SEAM INVARIANT {k} moved: {got} against the declared "
                     f"{want}")
    for f, e in o["artefact_err_m"].items():
        if e > TOL_ARTEFACT_M:
            fails.append(f"the built path at frame {f} is {e:.4f} m from the "
                         f"key the sheet declares there")
    for fa, fb, cv, mv in o.get("hold_fail", []):
        fails.append(
            f"HOLD: the keys at f{fa} and f{fb} are {cv:.4f} m/s apart — a "
            f"hold — but the curve between them reaches {mv:.4f} m/s "
            f"(bound {HOLD_PEAK_MS} m/s)")
    if o["bulge"] > TOL_BULGE:
        fails.append(
            f"BULGE: between the keys at f{o['bulge_f0']} and f{o['bulge_f1']} "
            f"the curve reaches {o['bulge_peak_ms']:.4f} m/s where those two "
            f"keys are {o['bulge_chord_ms']:.4f} m/s apart — "
            f"{o['bulge']:.3f}x, bound {TOL_BULGE:.2f}x")
    if o["accel_ratio"] > TOL_ACCEL_RATIO:
        fails.append(
            f"SPIKE: |accel| {abs(o['accel_at_ratio']):.1f} m/s^2 at frame "
            f"{o['accel_ratio_f']} is {o['accel_ratio']:.1f}x the median "
            f"{o['accel_nbhd_median']:.2f} of its +-{NBHD} frame neighbourhood "
            f"(bound {TOL_ACCEL_RATIO:.0f}x)")
    if o["rot_max_pct"] > TOL_ROT_PCT:
        warns.append(
            f"SMEAR: {o['rot_max_pct']:.2f} % of the frame width at frame "
            f"{o['rot_max_f']} (WARN over {TOL_ROT_PCT:.0f} %)")
    return fails, warns


def report(o, label=""):
    print(f"=== SEAM GATE  frames {o['window'][0]}-{o['window'][1]}  {label}")
    if o.get("refuse"):
        print("   REFUSED " + o["refuse"])
        return
    if o["seam_checks"]:
        print("  the four invariants, pinned at t=31.4 and t=33.041667:")
        for k in ("chord_m", "speed_ms", "look_angle_deg", "lens_delta_mm"):
            mark = "   MOVED" if k in o["inv_moved"] else ""
            print(f"    {k:16s} {o['inv'][k]:>12}   declared "
                  f"{DECLARED[k]}{mark}")
        print("  built path vs the keys the sheet declares there: "
              + ", ".join(f"f{f} {e*1000:.4f} mm"
                          for f, e in o["artefact_err_m"].items()))
    print(f"  peak speed             {o['v_max_ms']:9.4f} m/s @f{o['v_max_f']}")
    print(f"  fastest authored pair  {o['authored_max_ms']:9.4f} m/s   "
          f"(peak is {o['peak_vs_fastest_pair_pct']:+.1f} % of it — REPORTED, "
          f"not gated)")
    print(f"  worst BULGE            {o['bulge']:9.3f} x  f{o['bulge_f0']}-"
          f"{o['bulge_f1']}: {o['bulge_peak_ms']:.3f} m/s inside a "
          f"{o['bulge_chord_ms']:.3f} m/s chord   (bound {TOL_BULGE:.2f}x)")
    print("    next: " + ", ".join(f"{b[0]:.2f}x f{b[1]}-{b[2]}"
                                   for b in o["bulge_top"][1:]))
    print(f"  worst |accel|          {o['accel_abs_max']:9.2f} m/s^2 "
          f"@f{o['accel_abs_max_f']}")
    print(f"  worst LOCAL accel      {o['accel_ratio']:9.2f} x  @f"
          f"{o['accel_ratio_f']}  ({o['accel_at_ratio']:+.1f} against a "
          f"neighbourhood median of {o['accel_nbhd_median']:.2f})   "
          f"(bound {TOL_ACCEL_RATIO:.0f}x)")
    print(f"  worst rotation         {o['rot_max_pct']:9.2f} %width/frame "
          f"@f{o['rot_max_f']}   (WARN over {TOL_ROT_PCT:.0f} %)")


# ----------------------------------------------------------------- census --
def census(path, sheet):
    """Every key interval, and every frame's local accel ratio, film-wide.

    This is what TOL_BULGE and TOL_ACCEL_RATIO are set from, recomputed rather
    than quoted. `--selftest` asserts the separation still holds.
    """
    ks = all_sheet_keys(sheet)
    lo = min(int(round(float(k["t"]) * FPS)) for k in ks)
    hi = max(int(round(float(k["t"]) * FPS)) for k in ks)
    spd, acc, _rot = series(path, max(lo, 2), hi)
    rows = []
    for fa, fb, cv in key_pairs(ks, lo, hi, MAX_BULGE_GAP):
        if cv < HOLD_CHORD_MS:
            continue
        mv = max(spd[f] for f in range(fa + 1, fb + 1) if f in spd)
        rows.append((mv / cv, fa, fb))
    long_rows = []
    for fa, fb, cv in key_pairs(ks, lo, hi):
        if cv < HOLD_CHORD_MS or fb - fa <= MAX_BULGE_GAP:
            continue
        mv = max(spd[f] for f in range(fa + 1, fb + 1) if f in spd)
        long_rows.append((mv / cv, fa, fb))
    long_rows.sort(reverse=True)
    rows.sort(reverse=True)
    inside = [r for r in rows if r[1] >= W_LO and r[2] <= W_HI]
    outside = [r for r in rows if not (r[1] >= W_LO and r[2] <= W_HI)]

    ar = []
    for f in sorted(acc):
        nb = [abs(acc[g]) for g in range(f - NBHD, f + NBHD + 1)
              if g in acc and g != f]
        if len(nb) < 2 * NBHD:
            continue
        med = statistics.median(nb)
        if med > 1e-6:
            ar.append((abs(acc[f]) / med, f, acc[f]))
    ar.sort(reverse=True)
    return {"bulge_rows": rows, "bulge_long": long_rows, "bulge_inside": inside,
            "bulge_outside": outside, "accel_rows": ar,
            "n_pairs": len(rows), "frames": [lo, hi]}


def print_census(c):
    print(f"=== CENSUS over frames {c['frames'][0]}-{c['frames'][1]}, "
          f"{c['n_pairs']} key intervals of {MAX_BULGE_GAP} frames or less")
    print("  worst BULGE, top 8 anywhere:")
    for r, fa, fb in c["bulge_rows"][:8]:
        tag = "  <- inside the seam window" if (fa >= W_LO and fb <= W_HI) else ""
        print(f"     {r:7.3f} x   f{fa}-{fb}{tag}")
    ob = c["bulge_outside"][0] if c["bulge_outside"] else (0, 0, 0)
    ib = c["bulge_inside"][0] if c["bulge_inside"] else (0, 0, 0)
    print(f"  worst OUTSIDE the seam window {ob[0]:.3f} x (f{ob[1]}-{ob[2]})")
    print(f"  worst INSIDE  the seam window {ib[0]:.3f} x (f{ib[1]}-{ib[2]})")
    print(f"  the shipped bound is {TOL_BULGE:.2f} x")
    print(f"  intervals LONGER than {MAX_BULGE_GAP} frames are reported, not "
          f"gated — worst 5:")
    for r, fa, fb in c["bulge_long"][:5]:
        print(f"     {r:7.3f} x   f{fa}-{fb}  ({fb - fa} frames)")
    print("  worst LOCAL accel ratio, top 8 anywhere:")
    for r, f, a in c["accel_rows"][:8]:
        tag = "  <- inside the seam window" if W_LO <= f <= W_HI else ""
        print(f"     {r:7.2f} x   f{f}   a = {a:+8.2f} m/s^2{tag}")
    over = [x for x in c["accel_rows"]
            if x[0] > TOL_ACCEL_RATIO and not (W_LO <= x[1] <= W_HI)]
    print(f"  frames over the {TOL_ACCEL_RATIO:.0f}x bound OUTSIDE this "
          f"gate's window: {len(over)}"
          + ("" if not over else "  -> "
             + ", ".join(f"f{f} ({r:.1f}x)" for r, f, _a in over[:6])))
    print("     (reported, not fixed here: they belong to other beats)")


# ---------------------------------------------------------------- controls --
def inject_overshoot(src, lo, hi, sheet, frac):
    """Push one frame further along its own direction, inside a key interval.

    A perturbation of a REAL, passing artefact. It changes nothing about
    smoothness elsewhere, so a gate that fails it is failing the overshoot and
    not the neighbourhood.
    """
    pairs = key_pairs(all_sheet_keys(sheet), lo, hi)
    fa, fb, _cv = max(pairs, key=lambda p: p[1] - p[0])
    fx = (fa + fb) // 2
    out = {f: dict(e) for f, e in src.items()}
    d = [out[fx]["p"][i] - out[fx - 1]["p"][i] for i in range(3)]
    n = math.hypot(*d) or 1.0
    for f in range(fx, fb):                  # displace, then return to the key
        w = 1.0 - (f - fx) / max(fb - fx, 1)
        out[f] = dict(src[f])
        out[f]["p"] = [src[f]["p"][i] + d[i] / n * frac * n * w * 6.0
                       for i in range(3)]
    return out


def collapse_pair(sheet, lo, hi):
    """A sheet in which one key pair inside the window is a declared HOLD.

    The two keys are moved onto the same world position and nothing else is
    touched, so the PATH still moves between them exactly as it did. That is
    what a hold that does not hold looks like, and it is the only case the
    BULGE ratio cannot express — which is why the HOLD branch exists and why it
    needs a control of its own rather than riding on the others.
    """
    sh = copy.deepcopy(sheet)
    ks = sorted(sh["beat2"]["camera_keys"], key=lambda k: float(k["t"]))
    for i in range(len(ks) - 1):
        fa = int(round(float(ks[i]["t"]) * FPS))
        fb = int(round(float(ks[i + 1]["t"]) * FPS))
        if lo <= fa and fb <= hi and 2 <= fb - fa <= MAX_BULGE_GAP:
            ks[i + 1]["world"] = list(ks[i]["world"])
            return sh, fa, fb
    raise SystemExit(">> FAIL: no beat-2 key pair available to collapse")


def selftest(sheet, live_path, pre_path, pre_sheet_path):
    for f in (pre_path, pre_sheet_path):
        if not os.path.exists(f):
            print(f"   FAIL positive control missing: {f}")
            return 1
    pre = load_path(pre_path)
    pre_sheet = json.load(open(pre_sheet_path))
    live = load_path(live_path)

    cases = [
        ("P1 shipped pre-fix path against ITS OWN sheet, seam window",
         pre, W_LO, W_HI, True, "FAIL", pre_sheet),
        ("P2 beat 3 f900-1000 with a +25 % overshoot injected inside one "
         "key interval",
         inject_overshoot(live, 900, 1000, sheet, 0.25), 900, 1000, False,
         "FAIL", None),
        ("N1 beat 3 f900-1000, untouched (3-10 m/s, keys ~4 frames apart)",
         live, 900, 1000, False, "PASS", None),
        ("N2 beat 5 f1100-1180, untouched (73 m/s)", live, 1100, 1180, False,
         "PASS", None),
        ("N3 the current build, seam window", live, W_LO, W_HI, True, "PASS",
         None),
    ]
    hold_sheet, ha, hb = collapse_pair(sheet, W_LO, W_HI)
    cases.insert(2, (f"P3 the current build against a sheet whose f{ha}-{hb} "
                     f"pair is collapsed into a declared hold",
                     live, W_LO, W_HI, True, "FAIL", hold_sheet))
    bad = 0
    for name, p, lo, hi, sc, want, sh in cases:
        o = measure(p, sh or sheet, lo, hi, seam_checks=sc)
        fails, _w = verdict(o)
        got = "FAIL" if fails else "PASS"
        print(f"  {got}  (want {want})  {name}")
        if not o.get("refuse"):
            print(f"        bulge {o['bulge']:.3f}x (f{o['bulge_f0']}-"
                  f"{o['bulge_f1']}), local accel {o['accel_ratio']:.2f}x, "
                  f"peak {o['v_max_ms']:.3f} m/s")
        for f in fails:
            print(f"          - {f}")
        if got != want:
            bad += 1

    # ---- the bound must still SEPARATE the film from the defect ----------
    c = census(pre, pre_sheet)
    ob = c["bulge_outside"][0][0] if c["bulge_outside"] else 0.0
    ib = c["bulge_inside"][0][0] if c["bulge_inside"] else 0.0
    ok = ob < TOL_BULGE < ib
    print(f"  {'PASS' if ok else 'FAIL'}  census: on the positive control the "
          f"worst interval outside the window is {ob:.3f}x and inside it is "
          f"{ib:.3f}x; the bound {TOL_BULGE:.2f}x must lie strictly between "
          f"them")
    if not ok:
        bad += 1
    print(f">> selftest: {len(cases) + 1 - bad}/{len(cases) + 1} controls "
          f"behaved")
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", default=os.path.join(R2, "render/film9_path.json"))
    ap.add_argument("--sheet", default=os.path.join(R2, "docs/beat_sheet.json"))
    ap.add_argument("--pre", default=os.path.join(
        R2, "docs/seam_pre_R2064_path.json"),
        help="the shipped pre-fix path, kept as the positive control. In "
             "docs/ and not in work/ because work/ is gitignored and a "
             "control that can be deleted by a tidy-up is not a control")
    ap.add_argument("--pre-sheet", default=os.path.join(
        R2, "docs/seam_pre_R2064_sheet.json"),
        help="THE SHEET THAT PATH WAS BUILT FROM. Measuring the pre-fix path "
             "against the CURRENT sheet's keys compares a curve to keys it was "
             "never built from: it still fails, but the ratio it prints is "
             "meaningless. A control judged against the wrong reference is the "
             "failure this project keeps logging, so the pair is kept together")
    ap.add_argument("--window", type=int, nargs=2, default=[W_LO, W_HI])
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--census", action="store_true")
    ap.add_argument("--json-out")
    ap.add_argument("--dump", action="store_true",
                    help="print the per-frame series")
    a = ap.parse_args()

    sheet = json.load(open(a.sheet))
    if a.selftest:
        bad = selftest(sheet, a.path, a.pre, a.pre_sheet)
        print(">> STAGE RESULT: " + ("SEAM_GATE_SELFTEST_OK" if not bad
                                     else "SEAM_GATE_SELFTEST_BROKEN"))
        sys.exit(1 if bad else 0)

    path = load_path(a.path)
    if a.census:
        print_census(census(path, sheet))
        print(">> STAGE RESULT: SEAM_CENSUS_OK")
        return

    lo, hi = a.window
    o = measure(path, sheet, lo, hi, seam_checks=(lo, hi) == (W_LO, W_HI))
    report(o, os.path.basename(a.path))
    if a.dump and not o.get("refuse"):
        print("    f     v m/s    a m/s2   rot %")
        for f in sorted(int(k) for k in o["series"]):
            v, ac, r = o["series"][str(f)]
            print(f"  {f:5d} {v:9.4f} {ac:9.2f} {r:7.2f}")
    fails, warns = verdict(o)
    for w in warns:
        print("   WARN " + w)
    for f in fails:
        print("   FAIL " + f)
    if a.json_out:
        json.dump(o, open(a.json_out, "w"), indent=1)
    print(">> STAGE RESULT: " + ("SEAM_OK" if not fails else "SEAM_DEFECT"))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
