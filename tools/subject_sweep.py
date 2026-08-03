"""HOW FAST DOES THE SUBJECT CROSS THE FRAME, AND DOES IT FIT IN IT.

    .venv/bin/python tools/subject_sweep.py --path render/film11_path.json
    .venv/bin/python tools/subject_sweep.py --anchors --lo 1400 --hi 1520
    .venv/bin/python tools/subject_sweep.py --selftest --path <a built path>

WHY THIS EXISTS
---------------
R2-062 ends with the finding this file is built on:

    "The rig's aim gate scored it 7.24 deg, a pass. A camera can be pointed
     exactly at its subject and still be moving far too fast to photograph it.
     Aim error and photographability are independent, and only one of them was
     being measured."

`continuity_gate --campath` DOES measure the smear — but it measures it on the
QUATERNION TRACK, which means it can only be run after the sheet has been
authored, the rig rebuilt and a path dumped, and when it fires it names a
frame rather than a cause. This file measures the same quantity from the
GEOMETRY that forces it:

    a camera that keeps a subject centred must turn at  omega = v_perp / r

where `r` is the range to the subject and `v_perp` is the component of their
relative velocity across the line of sight. Nothing about the camera's keys,
handles or rotation channels enters into it. So it can be run on the AUTHOR'S
OWN ANCHOR SPLINE, before a single key exists, which is what makes it useful
for authoring rather than only for post-mortem.

The two are checks on each other, not duplicates: if the path's measured
rotation and this file's required rotation disagree, one of the aim solve or
this model is wrong, and `--selftest` case N4 asserts they agree.

WHAT IS MEASURED, both in the frame's own units
------------------------------------------------
  1. SWEEP — omega as a percentage of the frame's own horizontal field of view
     per frame. The BOUNDS ARE QUOTED, NOT CHOSEN: they are imported from
     `tools/continuity_gate.py`'s campath gate (WHIP = 25 %, FAST = 12 %) so
     the two instruments cannot drift apart. Above 25 % of frame width in one
     frame a viewer cannot read the image at 24 fps.

  2. EXTENT — the subject's own angular size as a percentage of the frame
     width, from the angular diameter of the car's eight box corners rather
     than of a point. **DIAGNOSTIC. IT DOES NOT GATE, AND THE FIRST DRAFT OF
     THIS FILE HAD IT GATING AT 100 %, WHICH WAS WRONG.**

     The reasoning that looked right: 100 % is the frame edge, so a subject
     over 100 % is not in shot, it is across the lens. The measurement that
     refutes it, taken before this file was published:

         f807   extent 131 %   sweep 7.4 %   beat 2's ignition station, whose
                                             own note is "camera static, lens
                                             5.5 m off the rear tyre"
         f2636  extent 203 %   sweep 5.0 %   beat 5's declared "directly over
                                             the car at 83 m/s"
         f1461  extent 175 %   sweep 56.6 %  the T3 pass

     Gating extent at 100 % failed 107 frames, 100 of which are shots somebody
     authored on purpose and two of which carry their own note saying so. A
     subject larger than the frame is a CLOSE SHOT. A subject larger than the
     frame that also crosses it in two frames is the defect, and SWEEP already
     says that on its own — it fires on f1460-1463 and on nothing else in
     2,978 frames.

     So extent is printed, never judged. Collision is somebody else's
     measurement and already exists: `tools/author_beats2_5.py`'s
     camera-to-car BOX floor of 1.40 m.

     The general form of the mistake is the one `build_camera_rig.Subject`
     already records about beat 1's nominated cluster: a gate that fires on
     accepted material is measuring the model, not the rig, and shipping it
     would send someone to fix a camera that is working.

WHAT THE EXTENT DIAGNOSTIC SAYS ABOUT THE CLOSING WIDE, R2-090
---------------------------------------------------------------
Reported here rather than gated, because it is a composition question with no
right answer and not a defect. The brief names three things in beat 6:

    "the circuit, the car streaking on, the breached showroom visible in the
     distance with its wound - and holds a final composed frame for ~3 s"

Measured on the built path at the last frame, f2978: the camera is at 140 m
altitude, 595.4 m from the declared fixed point, on an **18.75 mm lens** -- the
widest in the film -- and aimed at 0.08 deg, the best aim of any beat.

    the breached opening, 9.6 m wide   1.05 % of frame width   20 px of 1920
    the car, 5.698 m long              0.63 %                  12 px of 1920

The circuit reads, and it reads well. The wound is a bright notch about 20 px
across -- present, centred, and genuinely visible at a 6x zoom, but 20 px. The
car cannot be found in the frame at all; an agent looking for it picked out a
pale paddock structure instead.

The two are not independently fixable, and the arithmetic says why. To put the
car at 2 % of frame width you either need a **73.8 mm lens** at this range,
which is a telephoto and not a closing wide, or you need to close to **188 m**,
which is a third of the circuit rather than all of it. A 595 m whole-circuit
wide cannot contain a legible car. The brief asks for both, so somebody has to
choose, and it is not this file's choice to make.

Two things that are NOT wrong and were checked before writing this down:
  * the 3 s hold is exact. Camera travel over f2906-2978 is **0.00 m in 72
    frames = 3.000 s**, which is the brief's "~3 s" to the frame.
  * the car being invisible is not an aiming failure. Beat 6's declared subject
    after t+6.0 IS the facade, not the car, and the rig is pointed at it to
    0.08 deg.

WHAT IT DOES NOT MEASURE
------------------------
It never opens a rendered frame. It cannot tell you a shot LOOKS right; only
that the picture it asks for is one a lens can hold. Motion blur, occlusion,
depth of field and whether the subject is behind a barrier are all somebody
else's measurement.

It also does not judge beat 1, whose subject is a FIELD of exploded parts and
not a point — `Subject.nearest_field` exists for exactly that reason and this
file refuses beat 1 rather than reporting a number about the wrong subject.

CONTROLS — `--selftest`, seven cases whose verdicts are known in advance
-----------------------------------------------------------------------
  P1  a SYNTHETIC case with a closed form: a subject held at exactly 10.000 m
      moving at exactly 100.000 m/s across the line of sight, on a 36 mm
      lens. The finite difference of a point on that circle is a CHORD, so
      the exact expectation is 2R sin(w/2) cos(w/2) / R rad per frame and NOT
      the continuous-time V/R; the gate must reproduce it to 1e-6.
      A gate whose arithmetic is not checked against a case with a closed
      form is an opinion.
  P2  frames 1440-1490 of the FROZEN PRE-R2085 PATH, kept at
      `docs/subject_sweep_pre_R2085_path.json`                    must FAIL
      Not the live path: the live path is the fixed one now, and a positive
      control that is allowed to be fixed is not a control. It is kept beside
      the file for the same reason tools/seam_gate.py keeps its own.
  N1  the live `--path` over frames 1100-1180. Real beat-5 material at
      73 m/s — the same window `tools/seam_gate.py` uses as its N2 control,
      deliberately, so the two gates share a negative control      must PASS
  N2  the live `--path` over frames 2200-2300, beat 5's helicopter
      arc: 60+ m/s and hundreds of metres of range                 must PASS
  N3  frames 795-860, beat 2's ignition and wheelspin              must PASS
      **THIS ARM EXISTS BECAUSE IT CAUGHT THIS FILE OUT.** Extent runs to
      131 % of frame width across 65 of these frames and every one of them is
      material with a note on it. Any future detector added here has to walk
      past a shot that fills the lens and stay quiet.
  N5  the LIVE path over P2's OWN window                          must PASS
      P2 and N5 are the same 51 frames of the same shot before and after one
      anchor moved, which is the only pair that shows this gate measures the
      pass and not merely beat 5.
  N4  agreement: over N1's window the omega this file DERIVES from geometry
      and the omega `continuity_gate` MEASURES from the quaternion track
      must agree to better than 15 % of frame width. They are computed from
      disjoint inputs -- positions and telemetry here, the rotation channel
      there -- so agreement is evidence about both.
"""

import argparse
import json
import math
import os
import re
import sys

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(R2, "anim"))
sys.path.insert(0, os.path.join(R2, "tools"))

import filmtime as FT                                            # noqa: E402
from carpath import Car, CAR_HALF_LEN, CAR_HALF_W, CAR_TOP_Z     # noqa: E402

FPS = 24.0
SENSOR_W_MM = 36.0

# QUOTED FROM tools/continuity_gate.py's campath gate, not chosen here, so the
# two instruments cannot drift apart. R2-034 is the reason this is read rather
# than copied: two shared constants living in two places agree by coincidence.
#
# `WHIP, FAST` are LOCALS inside `campath_gate()`, not module attributes, so
# importing the module does not expose them and `getattr(CG, "WHIP", 0.25)`
# would silently return a default while this file's report claimed it had read
# continuity_gate. It is parsed out of the source text instead, and this file
# REFUSES TO LOAD if the line is not there — a citation that cannot fail is not
# a citation.
def _campath_bounds():
    src = os.path.join(R2, "tools/continuity_gate.py")
    with open(src) as fh:
        for line in fh:
            m = re.match(r"\s*WHIP,\s*FAST\s*=\s*([0-9.]+)\s*,\s*([0-9.]+)", line)
            if m:
                return float(m.group(1)) * 100.0, float(m.group(2)) * 100.0, src
    raise SystemExit(
        ">> FAIL: could not find `WHIP, FAST = ...` in tools/continuity_gate.py. "
        "This file's bounds are that file's bounds; it will not invent them.")


SWEEP_FAIL_PCT, SWEEP_WARN_PCT, _BOUND_SRC = _campath_bounds()

EXTENT_NOTE_PCT = 100.0       # the frame edge — REPORTED, never judged

# THE FROZEN POSITIVE CONTROL. The pre-R2085 path, the one whose T3 pass is
# 3.26 m and 56.6 % of frame width. It is kept in docs/ rather than pointed at
# render/, for the reason tools/seam_gate.py keeps its own: a control that
# lives in a regenerable directory stops being a control the moment somebody
# regenerates it, and the first sign is a gate that quietly passes everything.
PRE_R2085 = os.path.join(R2, "docs/subject_sweep_pre_R2085_path.json")

# Beats this file will judge. Beat 1's subject is a field, not a point.
JUDGED = ("2_launch", "3_breach", "4_transit", "5_lap", "6_ending")


# ------------------------------------------------------------------ context --
def context(sheet_path=None, tele=None, spec_path=None):
    sheet = json.load(open(sheet_path or os.path.join(R2, "docs/beat_sheet.json")))
    spec = json.load(open(spec_path or os.path.join(R2, "docs/circuit_spec.json")))
    car = Car(tele or os.path.join(R2, "telemetry/telemetry.csv"), spec)
    total = int(sheet["total_frames"])
    scales, _ = FT.build_time_map(sheet, total)
    W = FT.world_time_table(scales, total)
    return sheet, spec, car, W, total


def beat_of(sheet, f):
    t = f / FPS
    last = sheet["beats"][0]["name"]
    for b in sheet["beats"]:
        if t >= b["start_s"]:
            last = b["name"]
    return last


def subject_point(sheet, car, W, f, beat):
    """The declared subject, the same way `build_camera_rig.Subject.at` does."""
    spec = sheet.get("aim", {}).get(beat, {})
    zo = float(spec.get("z_off", 0.80))
    p = car.pos(W[f])
    carpt = (p[0], p[1], p[2] + zo)
    if beat != "6_ending":
        return carpt
    b6_start = next(b["start_s"] for b in sheet["beats"] if b["name"] == "6_ending")
    t = f / FPS - b6_start
    t0 = float(spec.get("car_until_t", 4.0))
    t1 = float(spec.get("point_from_t", 6.0))
    if t <= t0:
        return carpt
    pt = tuple(float(v) for v in spec["fixed_point"])
    if t >= t1:
        return pt
    u = (t - t0) / max(t1 - t0, 1e-9)
    u = u * u * (3.0 - 2.0 * u)
    return tuple(carpt[i] + (pt[i] - carpt[i]) * u for i in range(3))


def car_box(car, wt):
    """The car's eight box corners in world space, from its own dimensions."""
    p, h, _v = car.state(wt)
    c, s = math.cos(h), math.sin(h)
    out = []
    for dx in (-CAR_HALF_LEN, CAR_HALF_LEN):
        for dy in (-CAR_HALF_W, CAR_HALF_W):
            for dz in (0.0, CAR_TOP_Z):
                out.append((p[0] + c * dx - s * dy, p[1] + s * dx + c * dy,
                            p[2] + dz))
    return out


def hfov_deg(lens_mm):
    return math.degrees(2.0 * math.atan(SENSOR_W_MM / (2.0 * max(lens_mm, 1e-6))))


def angular_extent_deg(eye, pts):
    """Angular diameter of a point set seen from `eye`: 2x the half-angle of
    the smallest cone about the set's mean direction that contains all of it."""
    dirs = []
    for q in pts:
        d = [q[i] - eye[i] for i in range(3)]
        n = math.sqrt(sum(x * x for x in d)) or 1e-9
        dirs.append([x / n for x in d])
    m = [sum(d[i] for d in dirs) / len(dirs) for i in range(3)]
    n = math.sqrt(sum(x * x for x in m)) or 1e-9
    m = [x / n for x in m]
    worst = 0.0
    for d in dirs:
        dot = max(-1.0, min(1.0, sum(m[i] * d[i] for i in range(3))))
        worst = max(worst, math.acos(dot))
    return math.degrees(2.0 * worst)


# ---------------------------------------------------------------- the model --
def sweep_series(cam_of_frame, lens_of_frame, sheet, car, W, lo, hi,
                 subject_of_frame=None, extent_pts=None):
    """Per frame: range, v_perp, required omega, subject extent.

    `cam_of_frame(f) -> (x, y, z)` is the only thing that differs between a
    built path and the author's anchor spline, which is why this takes a
    callable and not a file.
    """
    rows = []
    prev = None
    for f in range(lo, hi + 1):
        beat = beat_of(sheet, f)
        cam = cam_of_frame(f)
        if cam is None:
            prev = None
            continue
        sub = (subject_of_frame or (lambda g: subject_point(sheet, car, W, g, beat)))(f)
        d = [sub[i] - cam[i] for i in range(3)]
        r = math.sqrt(sum(x * x for x in d)) or 1e-9
        L = lens_of_frame(f)
        hf = hfov_deg(L)
        pts = (extent_pts or (lambda g: car_box(car, W[g])))(f)
        ext = angular_extent_deg(cam, pts) if pts else float("nan")
        row = {"f": f, "beat": beat, "range_m": r, "lens_mm": L, "hfov_deg": hf,
               "extent_deg": ext, "extent_pct": 100.0 * ext / hf}
        if prev is not None:
            rel = [((sub[i] - cam[i]) - prev[i]) * FPS for i in range(3)]
            u = [x / r for x in d]
            closing = sum(rel[i] * u[i] for i in range(3))
            perp = math.sqrt(max(0.0, sum(x * x for x in rel) - closing * closing))
            om_deg_frame = math.degrees(perp / r) / FPS
            row.update({"v_perp_ms": perp, "closing_ms": closing,
                        "omega_deg_frame": om_deg_frame,
                        "sweep_pct": 100.0 * om_deg_frame / hf})
        rows.append(row)
        prev = d
    return rows


def judge(rows):
    """SWEEP gates. EXTENT does not — see the docstring, and the 107 frames."""
    sw = [r for r in rows if "sweep_pct" in r]
    fails = [r for r in sw if r["sweep_pct"] >= SWEEP_FAIL_PCT]
    warns = [r for r in sw if SWEEP_WARN_PCT <= r["sweep_pct"] < SWEEP_FAIL_PCT]
    return fails, warns


def summarise(rows, label):
    sw = [r for r in rows if "sweep_pct" in r]
    if not sw:
        return {"label": label, "frames": 0}
    ws = max(sw, key=lambda r: r["sweep_pct"])
    we = max(rows, key=lambda r: r["extent_pct"])
    n_over = sum(1 for r in rows if r["extent_pct"] >= EXTENT_NOTE_PCT)
    wr = min(rows, key=lambda r: r["range_m"])
    fails, warns = judge(rows)
    ff = sorted({r["f"] for r in fails})
    return {"label": label, "frames": len(rows),
            "span": [rows[0]["f"], rows[-1]["f"]],
            "worst_sweep_pct": ws["sweep_pct"], "worst_sweep_frame": ws["f"],
            "worst_sweep_deg_frame": ws["omega_deg_frame"],
            "worst_sweep_range_m": ws["range_m"],
            "worst_sweep_vperp_ms": ws["v_perp_ms"],
            "worst_extent_pct": we["extent_pct"], "worst_extent_frame": we["f"],
            "extent_over_frame_width_frames": n_over,
            "min_range_m": wr["range_m"], "min_range_frame": wr["f"],
            "fail_frames": ff, "n_fail": len(ff),
            "n_warn": len({r["f"] for r in warns}),
            "verdict": "FAIL" if ff else "PASS"}


def report(s):
    print(f"  {s['label']}: frames {s['span'][0]}-{s['span'][1]}")
    print(f"    worst SWEEP  {s['worst_sweep_pct']:6.2f} % of frame width/frame "
          f"at f{s['worst_sweep_frame']}  "
          f"({s['worst_sweep_deg_frame']:.2f} deg/frame; the subject is "
          f"{s['worst_sweep_range_m']:.2f} m away crossing at "
          f"{s['worst_sweep_vperp_ms']:.1f} m/s)")
    print(f"    worst EXTENT {s['worst_extent_pct']:6.2f} % of frame width "
          f"at f{s['worst_extent_frame']}  ({s['extent_over_frame_width_frames']} "
          f"frames over 100 % — DIAGNOSTIC, does not gate)")
    print(f"    min range    {s['min_range_m']:6.3f} m at f{s['min_range_frame']}")
    print(f"    {s['n_fail']} FAIL frames, {s['n_warn']} WARN frames -> "
          f"{s['verdict']}")
    if s["fail_frames"]:
        ff = s["fail_frames"]
        print(f"    FAIL frames: {ff[0]}-{ff[-1]} ({len(ff)})")


# ------------------------------------------------------------- path sources --
def from_path(path_json):
    P = {e["f"]: e for e in json.load(open(path_json))["path"]}
    return (lambda f: tuple(P[f]["p"]) if f in P else None,
            lambda f: float(P[f].get("lens", 35.0)) if f in P else 35.0,
            sorted(P))


def from_anchors(sheet, car, W):
    """The AUTHOR'S OWN Catmull-Rom chain, before any key is emitted."""
    import author_beats2_5 as AB
    anchors = AB.build_anchors(car, W)
    chain = []
    for name in ("2_launch", "3_breach", "4_transit", "5_lap"):
        for a in anchors[name]:
            if not chain or abs(a["t"] - chain[-1]["t"]) > 1e-9:
                chain.append(a)
    t0, t1 = chain[0]["t"], chain[-1]["t"]

    def cam(f):
        t = f / FPS
        if t < t0 or t > t1:
            return None
        return tuple(AB.catmull_rom(chain, t))

    def lens(f):
        return float(AB.scalar_at(chain, f / FPS, "lens"))

    return cam, lens, list(range(int(math.ceil(t0 * FPS)), int(t1 * FPS) + 1))


# ---------------------------------------------------------------- selftest --
def _synthetic():
    """P1: a closed-form case. Subject at exactly 10 m, crossing at 100 m/s."""
    R, V, LENS = 10.0, 100.0, 36.0
    def cam(f):
        return (0.0, 0.0, 0.0)
    def lens(f):
        return LENS
    def sub(f):
        # a point on a circle of radius R, angular speed V/R rad/s
        w = V / R / FPS
        a = w * f
        return (R * math.cos(a), R * math.sin(a), 0.0)
    rows = sweep_series(cam, lens, {"beats": [{"name": "5_lap", "start_s": 0.0}]},
                        None, None, 1, 6, subject_of_frame=sub,
                        extent_pts=lambda f: [sub(f)])
    got = rows[-1]
    want_deg = math.degrees(V / R) / FPS
    want_pct = 100.0 * want_deg / hfov_deg(LENS)
    # a chord, not an arc: the finite-difference velocity of a point on a
    # circle is the chord, so the exact expectation is 2*R*sin(w/2)*FPS
    w = V / R / FPS
    chord_v = 2.0 * R * math.sin(w / 2.0) * FPS
    want_deg_chord = math.degrees(chord_v * math.cos(w / 2.0) / R) / FPS
    ok = abs(got["omega_deg_frame"] - want_deg_chord) < 1e-6
    return ok, got, want_deg, want_pct, want_deg_chord


def selftest(path_json):
    sheet, spec, car, W, total = context()
    cam, lens, fs = from_path(path_json)
    bad = []

    ok, got, want_deg, want_pct, want_chord = _synthetic()
    print(f"  {'PASS' if ok else 'FAIL'}  P1 synthetic: subject at 10.000 m "
          f"crossing at 100.000 m/s on a 36 mm lens -> "
          f"{got['omega_deg_frame']:.6f} deg/frame "
          f"({got['sweep_pct']:.4f} % of a {got['hfov_deg']:.2f} deg frame). "
          f"Closed form for the finite difference is {want_chord:.6f}; the "
          f"continuous-time value is {want_deg:.6f} deg/frame.")
    if not ok:
        bad.append("P1")

    pre_cam, pre_lens, _ = from_path(PRE_R2085)
    cases = [("P2", 1440, 1490, "FAIL", "the PRE-R2085 T3 pass, frozen control",
              pre_cam, pre_lens),
             ("N1", 1100, 1180, "PASS", "beat 5 at 73 m/s, seam_gate's N2 window",
              cam, lens),
             ("N2", 2200, 2300, "PASS", "beat 5's helicopter arc", cam, lens),
             ("N3", 795, 860, "PASS",
              "beat 2's ignition and wheelspin, extent 131 % on purpose",
              cam, lens),
             ("N5", 1440, 1490, "PASS", "the LIVE path at P2's own window",
              cam, lens)]
    for tag, lo, hi, want, note, c, l in cases:
        rows = sweep_series(c, l, sheet, car, W, lo, hi)
        s = summarise(rows, f"{tag} {note}")
        ok = s["verdict"] == want
        print(f"  {'PASS' if ok else 'FAIL'}  {tag} f{lo}-{hi} ({note}): "
              f"{s['verdict']}, expected {want}. worst sweep "
              f"{s['worst_sweep_pct']:.1f} % at f{s['worst_sweep_frame']}, "
              f"worst extent {s['worst_extent_pct']:.1f} % "
              f"({s['extent_over_frame_width_frames']} frames over 100 %), "
              f"min range {s['min_range_m']:.2f} m")
        if not ok:
            bad.append(tag)

    # N4: agreement with the quaternion track over N1's window.
    P = {e["f"]: e for e in json.load(open(path_json))["path"]}
    rows = sweep_series(cam, lens, sheet, car, W, 1100, 1180)
    worst = 0.0
    for r in rows:
        if "sweep_pct" not in r:
            continue
        f = r["f"]
        if f - 1 not in P:
            continue
        q0, q1 = P[f - 1]["q"], P[f]["q"]
        dot = min(1.0, abs(sum(a * b for a, b in zip(q0, q1))))
        meas = math.degrees(2 * math.acos(dot)) / r["hfov_deg"] * 100.0
        worst = max(worst, abs(meas - r["sweep_pct"]))
    ok = worst < 15.0
    print(f"  {'PASS' if ok else 'FAIL'}  N4 agreement over f1100-1180: the "
          f"omega DERIVED from range and relative velocity and the omega "
          f"MEASURED off the rotation channel differ by at most "
          f"{worst:.2f} % of frame width (bound 15.0). Disjoint inputs.")
    if not ok:
        bad.append("N4")
    return bad


# --------------------------------------------------------------------- main --
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", default=os.path.join(R2, "render/film11_path.json"))
    ap.add_argument("--anchors", action="store_true",
                    help="measure the AUTHOR'S spline instead of a built path")
    ap.add_argument("--sheet")
    ap.add_argument("--lo", type=int)
    ap.add_argument("--hi", type=int)
    ap.add_argument("--dump", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--json-out")
    a = ap.parse_args()

    if a.selftest:
        bad = selftest(a.path)
        print(">> STAGE RESULT: " + ("SUBJECT_SWEEP_SELFTEST_OK" if not bad
                                     else "SUBJECT_SWEEP_SELFTEST_BROKEN"))
        sys.exit(1 if bad else 0)

    sheet, spec, car, W, total = context(a.sheet)
    if a.anchors:
        cam, lens, fs = from_anchors(sheet, car, W)
        src = "the author's anchor spline (tools/author_beats2_5.build_anchors)"
    else:
        cam, lens, fs = from_path(a.path)
        src = a.path
    lo = a.lo if a.lo is not None else fs[0]
    hi = a.hi if a.hi is not None else fs[-1]
    lo, hi = max(lo, fs[0]), min(hi, fs[-1])

    # Beat 1 is refused rather than measured against the wrong subject.
    if beat_of(sheet, lo) == "1_assembly":
        lo = max(lo, int(round(next(b["start_s"] for b in sheet["beats"]
                                    if b["name"] == "2_launch") * FPS)) + 1)

    rows = sweep_series(cam, lens, sheet, car, W, lo, hi)
    print(f"  source: {src}")
    print(f"  bounds: SWEEP {SWEEP_WARN_PCT:.0f} % WARN / {SWEEP_FAIL_PCT:.0f} % "
          f"FAIL of frame width per frame, quoted from {_BOUND_SRC}; "
          f"EXTENT is a DIAGNOSTIC and does not gate")
    per_beat = {}
    for name in JUDGED:
        sub = [r for r in rows if r["beat"] == name]
        if len(sub) < 3:
            continue
        per_beat[name] = summarise(sub, name)
        report(per_beat[name])
    whole = summarise(rows, "WHOLE RANGE")
    print()
    report(whole)
    if a.dump:
        print("    f      range      v_perp   omega d/f   sweep %   extent %  lens")
        for r in rows:
            if "sweep_pct" not in r:
                continue
            print(f"  {r['f']:5d} {r['range_m']:10.3f} {r['v_perp_ms']:11.2f} "
                  f"{r['omega_deg_frame']:11.3f} {r['sweep_pct']:9.2f} "
                  f"{r['extent_pct']:10.2f} {r['lens_mm']:6.1f}")
    if a.json_out:
        json.dump({"source": src, "per_beat": per_beat, "whole": whole,
                   "rows": rows}, open(a.json_out, "w"), indent=1)
    print(">> STAGE RESULT: " + ("SUBJECT_SWEEP_OK" if whole["verdict"] == "PASS"
                                 else "SUBJECT_SWEEP_UNPHOTOGRAPHABLE"))
    sys.exit(1 if whole["verdict"] != "PASS" else 0)


if __name__ == "__main__":
    main()
