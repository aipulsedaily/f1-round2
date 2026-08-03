"""WHEEL ROTATION GATE — is `wheel_rot_rad` monotonic, and does it match the road?

    .venv/bin/python tools/wheel_rotation_gate.py [--telemetry ...] [--sheet ...]

WHY THIS FILE EXISTS
--------------------
R2-041.  `wheel_rot_rad` stepped **backwards 9.0821 rad (1.4454 revolutions) at
frame 10**, in the middle of the launch, and every artefact in the project read
that column without ever differencing it.  A wheel that un-spins one and a half
turns in 1/24 s is not a subtle defect; it is simply that nothing looked.

WHAT IT MEASURES, IN REAL UNITS
-------------------------------
TWO INDEPENDENT MEASUREMENTS OF THE SAME QUANTITY, required to agree:

  A. THE COLUMN.  `diff(wheel_rot_rad)` over the raw 1,743 telemetry rows and,
     separately, over the FILM's 2,978 frames walked through `anim/filmtime.py`
     (which is what the render actually samples: beat 3's ramp means film frame
     and telemetry row are not the same thing).  Reports the most negative step
     in radians.  It must be >= 0.

  B. THE ROAD.  Rolling contact says rotation = distance / radius, so
     `wheel_rot_rad` minus `s_m / r` must be a NON-DECREASING step function whose
     total rise is exactly the sanctioned launch slip and which is FLAT
     everywhere the `wheelspin` column is 0.  That derives the same series from a
     different column and catches an error that happens to be monotonic.

  Plus the headline reconciliation the brief asks for: total revolutions against
  distance / circumference.

CONTROLS — A CHECK THAT HAS NEVER FAILED HAS NOT BEEN SHOWN TO WORK
-------------------------------------------------------------------
`--selftest` runs the gate against:

  * POSITIVE, the real defect.  The pre-fix formula (`extra` written into the
    first 10 frames and left at zero afterwards) rebuilt from the shipped column.
    The gate MUST fail it, and must name frame 10.
  * POSITIVE, a monotonic-but-wrong series.  Rotation from `s_m` with the launch
    slip omitted entirely: strictly increasing, so measurement A passes it.
    Measurement B MUST fail it, which is the whole reason B exists.
  * NEGATIVE, the shipped column.  Must pass both.

The selftest exits non-zero unless every one of those three verdicts is the
expected one, so a gate that has been broken into always-pass cannot pretend.
"""

import argparse
import csv
import json
import math
import os
import sys

import numpy as np

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(R2, "anim"))
import filmtime as FT                                              # noqa: E402

WHEEL_RADIUS_M = 0.36          # tools/build_telemetry.py --wheel-radius default
CIRC_M = 2.0 * math.pi * WHEEL_RADIUS_M
TOL_REV = 1.0e-4               # revolutions; 1e-4 rev = 0.036 deg = 0.23 mm of road

# Measurement B subtracts two columns that the CSV writes at DIFFERENT precisions
# -- `s_m` at 4 dp and `wheel_rot_rad` at 5 dp -- so the difference carries a
# quantisation artefact that is not a defect.  Worst case per frame-to-frame
# step: 1e-4 m of road (two half-ULP roundings) over the radius, plus 1e-5 rad.
# DERIVED, not chosen: at r = 0.36 m that is 2.88e-4 rad, and the measured worst
# on a clean series is 2.80e-4.  Measurement A needs no such allowance, because
# rounding a non-decreasing sequence leaves it non-decreasing.
QUANT_RAD = 1.0e-4 / WHEEL_RADIUS_M + 1.0e-5

# The brief sanctions ONE departure from rolling contact: ~10 frames of launch
# wheelspin.  If the `wheelspin` column flags those frames, the rotation column
# has to actually show slip there -- otherwise the two columns contradict each
# other and the sanctioned violation has silently gone missing.
MIN_SANCTIONED_SLIP_REV = 0.25


def load(path):
    rows = list(csv.DictReader(open(path)))
    col = lambda n: np.array([float(r[n]) for r in rows])          # noqa: E731
    return {"t": col("t_s"), "s": col("s_m"), "w": col("wheel_rot_rad"),
            "v": col("speed_ms"), "spin": col("wheelspin")}


def film_series(tel, sheet_path):
    """`wheel_rot_rad` sampled on every one of the film's frames.

    The film is 2,978 frames of FILM time; the telemetry is 1,743 rows of WORLD
    time, and beat 3's ramp offsets the two clocks permanently.  Anything that
    samples the telemetry per frame has to walk that map, so this gate does too
    -- checking only the raw rows would pass a rig that samples them backwards.
    """
    sheet = json.load(open(sheet_path))
    n = int(sheet["total_frames"])
    scales, _ = FT.build_time_map(sheet, n)
    W = FT.world_time_table(scales, n)
    wt = np.clip(np.array([W[f] for f in range(1, n + 1)]), 0.0, tel["t"][-1])
    return wt, np.interp(wt, tel["t"], tel["w"])


def measure(tel, sheet_path=None):
    """Both measurements, as a dict of numbers in real units."""
    out = {}

    # ---- A. the column, raw rows -----------------------------------------
    d = np.diff(tel["w"])
    i = int(np.argmin(d)) if d.size else -1
    out["A_raw_min_step_rad"] = float(d.min()) if d.size else 0.0
    out["A_raw_min_step_rev"] = out["A_raw_min_step_rad"] / (2.0 * math.pi)
    out["A_raw_min_step_frame"] = i + 1
    out["A_raw_backwards_frames"] = int((d < -1e-9).sum())

    # ---- A. the column, walked onto the film's frames --------------------
    if sheet_path:
        wt, wf = film_series(tel, sheet_path)
        df = np.diff(wf)
        j = int(np.argmin(df)) if df.size else -1
        out["A_film_frames"] = int(wf.size)
        out["A_film_min_step_rad"] = float(df.min()) if df.size else 0.0
        out["A_film_min_step_rev"] = out["A_film_min_step_rad"] / (2.0 * math.pi)
        out["A_film_min_step_frame"] = j + 2          # film frames are 1-based
        out["A_film_backwards_frames"] = int((df < -1e-9).sum())

    # ---- B. the road ------------------------------------------------------
    slip = tel["w"] - tel["s"] / WHEEL_RADIUS_M        # rad of non-rolling rotation
    dslip = np.diff(slip)
    spinning = tel["spin"][1:] > 0                     # the step ENDS in a spin frame
    rolling = (tel["spin"][1:] == 0) & (tel["spin"][:-1] == 0)
    out["B_slip_total_rev"] = float(slip[-1]) / (2.0 * math.pi)
    out["B_slip_min_step_rad"] = float(dslip.min()) if dslip.size else 0.0
    out["B_spin_frames"] = int((tel["spin"] > 0).sum())
    out["B_slip_rise_on_spin_rev"] = (
        float(dslip[spinning].sum()) / (2.0 * math.pi) if spinning.any() else 0.0)
    out["B_slip_drift_off_spin_rev"] = (
        float(np.abs(dslip[rolling]).max()) / (2.0 * math.pi) if rolling.any() else 0.0)

    # ---- the headline reconciliation -------------------------------------
    out["total_rev"] = float(tel["w"][-1]) / (2.0 * math.pi)
    out["distance_m"] = float(tel["s"][-1])
    out["circumference_m"] = CIRC_M
    out["rolling_rev"] = out["distance_m"] / CIRC_M
    out["residual_rev"] = out["total_rev"] - out["rolling_rev"]
    out["residual_minus_slip_rev"] = out["residual_rev"] - out["B_slip_total_rev"]
    return out


def verdict(m):
    """FAILs in plain language, in real units. Unproven is a FAIL."""
    bad = []
    if m["A_raw_min_step_rad"] < -1e-9:
        bad.append("A: wheel_rot_rad steps BACKWARDS %.5f rad (%.4f rev) at "
                   "telemetry frame %d, on %d frame(s) in total"
                   % (-m["A_raw_min_step_rad"], -m["A_raw_min_step_rev"],
                      m["A_raw_min_step_frame"], m["A_raw_backwards_frames"]))
    if m.get("A_film_min_step_rad", 0.0) < -1e-9:
        bad.append("A: on the FILM's frames wheel_rot_rad steps BACKWARDS %.5f "
                   "rad at film frame %d, on %d frame(s)"
                   % (-m["A_film_min_step_rad"], m["A_film_min_step_frame"],
                      m["A_film_backwards_frames"]))
    elif "A_film_min_step_rad" not in m:
        bad.append("A: the film series was NOT measured (no beat sheet given), "
                   "so monotonicity over the take's 2,978 frames is UNPROVEN")
    if m["B_slip_min_step_rad"] < -QUANT_RAD:
        bad.append("B: the slip (rotation minus distance/radius) DECREASES by "
                   "%.5f rad, past the %.5f rad the CSV's own quantisation can "
                   "explain; a wheel cannot un-slip"
                   % (-m["B_slip_min_step_rad"], QUANT_RAD))
    if (m["B_spin_frames"] > 0
            and m["B_slip_rise_on_spin_rev"] < MIN_SANCTIONED_SLIP_REV):
        bad.append("B: the wheelspin column flags %d launch frames but the "
                   "rotation column shows only %.4f rev of slip across them "
                   "(expected at least %.2f) -- the two columns disagree about "
                   "whether the sanctioned wheelspin happened at all"
                   % (m["B_spin_frames"], m["B_slip_rise_on_spin_rev"],
                      MIN_SANCTIONED_SLIP_REV))
    if m["B_slip_drift_off_spin_rev"] > TOL_REV:
        bad.append("B: rolling contact is broken OUTSIDE the sanctioned "
                   "wheelspin -- the slip moves %.6f rev in one frame with "
                   "wheelspin=0 (tolerance %.6f)"
                   % (m["B_slip_drift_off_spin_rev"], TOL_REV))
    if abs(m["residual_minus_slip_rev"]) > TOL_REV:
        bad.append("total revolutions do not reconcile: %.4f total - %.4f "
                   "rolling = %.4f rev, but the declared launch slip is %.4f "
                   "rev (mismatch %.6f, tolerance %.6f)"
                   % (m["total_rev"], m["rolling_rev"], m["residual_rev"],
                      m["B_slip_total_rev"], m["residual_minus_slip_rev"], TOL_REV))
    return bad


def report(name, m, bad):
    print("--- %s" % name)
    print("    A raw   min step %+.6f rad (%+.5f rev) at frame %d; %d backwards"
          % (m["A_raw_min_step_rad"], m["A_raw_min_step_rev"],
             m["A_raw_min_step_frame"], m["A_raw_backwards_frames"]))
    if "A_film_min_step_rad" in m:
        print("    A film  min step %+.6f rad over %d film frames; %d backwards"
              % (m["A_film_min_step_rad"], m["A_film_frames"],
                 m["A_film_backwards_frames"]))
    print("    B slip   total %.4f rev, min step %+.6f rad (quantisation "
          "allowance %.6f), %.4f rev gained over %d flagged spin frames, worst "
          "off-spin drift %.7f rev"
          % (m["B_slip_total_rev"], m["B_slip_min_step_rad"], QUANT_RAD,
             m["B_slip_rise_on_spin_rev"], m["B_spin_frames"],
             m["B_slip_drift_off_spin_rev"]))
    print("    reconcile %.4f rev total = %.4f rev rolling (%.2f m / %.4f m) "
          "+ %.4f rev slip   (mismatch %.2e rev, tol %.0e)"
          % (m["total_rev"], m["rolling_rev"], m["distance_m"],
             m["circumference_m"], m["B_slip_total_rev"],
             abs(m["residual_minus_slip_rev"]), TOL_REV))
    for b in bad:
        print("    FAIL " + b)
    print("    %s" % ("PASS" if not bad else "FAIL"))
    return not bad


def _rebreak_windowed(tel):
    """POSITIVE CONTROL: the pre-fix artefact, rebuilt from the shipped column.

    The old code wrote the cumulative slip into the first 10 frames and left the
    rest at zero.  Subtracting the held slip from every frame past the window
    reproduces exactly that series -- the defect itself, not an imitation of it.
    """
    t = dict((k, v.copy()) for k, v in tel.items())
    slip = t["w"] - t["s"] / WHEEL_RADIUS_M
    hold = slip[9]
    t["w"][10:] -= hold
    return t


def _rebreak_noslip(tel):
    """POSITIVE CONTROL 2: monotonic, and still wrong.

    Pure rolling contact with the sanctioned launch wheelspin deleted.  Strictly
    increasing, so measurement A is happy; measurement B has to be the one that
    catches it, which is why there are two.
    """
    t = dict((k, v.copy()) for k, v in tel.items())
    t["w"] = t["s"] / WHEEL_RADIUS_M
    return t


def _synthetic_ok(tel):
    """NEGATIVE CONTROL: a clean series built from scratch, must pass."""
    t = dict((k, v.copy()) for k, v in tel.items())
    slip = np.zeros_like(t["s"])
    n = int((tel["spin"] > 0).sum())
    slip[:n] = np.linspace(0.0, 9.1398, n)
    slip[n:] = 9.1398
    t["w"] = t["s"] / WHEEL_RADIUS_M + slip
    return t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--telemetry", default=os.path.join(R2, "telemetry/telemetry.csv"))
    ap.add_argument("--sheet", default=os.path.join(R2, "docs/beat_sheet.json"))
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    tel = load(a.telemetry)
    if not a.selftest:
        m = measure(tel, a.sheet)
        ok = report(os.path.relpath(a.telemetry, R2), m, verdict(m))
        print(">> STAGE RESULT: " + ("WHEEL_ROTATION_MONOTONIC" if ok
                                     else "WHEEL_ROTATION_FAIL"))
        sys.exit(0 if ok else 1)

    cases = [
        ("NEGATIVE  the shipped column", tel, True),
        ("NEGATIVE  a synthetic clean series", _synthetic_ok(tel), True),
        ("POSITIVE  the pre-fix windowed slip (R2-041)", _rebreak_windowed(tel), False),
        ("POSITIVE  monotonic but no launch slip", _rebreak_noslip(tel), False),
    ]
    allok = True
    for name, t, want_pass in cases:
        m = measure(t, a.sheet)
        bad = verdict(m)
        got_pass = not bad
        good = got_pass == want_pass
        allok &= good
        report("%s  [expect %s]" % (name, "PASS" if want_pass else "FAIL"), m, bad)
        print("    SELFTEST %s" % ("ok" if good else "BROKEN -- the gate did not "
                                   "do what it claims"))
    print(">> STAGE RESULT: " + ("WHEEL_GATE_SELFTEST_OK" if allok
                                 else "WHEEL_GATE_SELFTEST_BROKEN"))
    sys.exit(0 if allok else 1)



# Imported by path, not by package: this runs inside Blender's interpreter
# with whatever cwd the caller happened to have.
import os as _os_ge, sys as _sys_ge
if _os_ge.path.dirname(_os_ge.path.abspath(__file__)) not in _sys_ge.path:
    _sys_ge.path.insert(0, _os_ge.path.dirname(_os_ge.path.abspath(__file__)))
import gate_exit                                                 # noqa: E402


if __name__ == "__main__":
    # Blender 5.2 returns 0 for a script that raised: `blender -b -P x.py`
    # prints the traceback and exits 0, MEASURED on this box. A gate that
    # crashed was indistinguishable from one that passed. guard() makes an
    # uncaught exception a status 2 and passes any real verdict through
    # unchanged. One shared helper, not N copies -- see tools/gate_exit.py.
    gate_exit.guard(main, tool="wheel_rotation_gate")
