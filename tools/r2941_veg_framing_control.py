"""R2-2941 CONTROL: watch r2941_veg_framing's selftest arms FAIL on a broken tool.

    python3 tools/r2941_veg_framing_control.py

A selftest that has only ever passed is not evidence.  This project has logged
over a dozen instruments that passed vacuously, so every arm of
`r2941_veg_framing --selftest` is shown here to REJECT a deliberately damaged
`measure()`.  Three damage modes, each aimed at one arm:

  A  no frustum rejection      -> the two negative arms must fail
  B  radial distance, not -Z   -> the closed-form arms must fail
  C  no clamp to the frame     -> the overfill arm must fail

If a damaged tool still passes the arm aimed at it, the arm is decorative and
this script exits non-zero saying so.  Exit 0 means every arm was watched to
fire.
"""
import io
import sys
import os
import contextlib

import numpy as np

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(R2, "tools"))
import r2941_veg_framing as VF                                   # noqa: E402

GOOD = VF.measure


def _damaged_no_frustum(bbox, C, Rm, s, **kw):
    """A tool that says everything in front of the camera is on screen."""
    n = bbox.shape[0]
    corn = VF._corners(bbox)
    peak = np.zeros(n); pf = np.full(n, -1, dtype=np.int64)
    pd = np.full(n, np.inf); ever = np.zeros(n, dtype=bool)
    out = {b: np.zeros(n, dtype=np.int64) for b in VF.BANDS}
    for f in range(C.shape[0]):
        v = (corn - C[f]) @ Rm[f]
        depth = np.abs(v[:, :, 2])                    # <-- damage: sign dropped
        py = v[:, :, 1] * s[f] / depth
        h = py.max(axis=1) - py.min(axis=1)
        ever |= True
        for b in VF.BANDS:
            out[b] += (h >= b)
        better = h > peak
        peak = np.where(better, h, peak); pf = np.where(better, f + 1, pf)
        pd = np.where(better, depth.min(axis=1), pd)
    r = {"peak_px": peak, "peak_frame": pf, "peak_depth_m": pd, "ever_in_frame": ever}
    for b in VF.BANDS:
        r["frames_ge_%d" % b] = out[b]
    return r


def _damaged_radial(bbox, C, Rm, s, **kw):
    """Radial distance instead of pinhole depth -- the manifest's own error."""
    r = GOOD(bbox, C, Rm, s, **kw)
    corn = VF._corners(bbox)
    rad = np.linalg.norm(corn - C[0], axis=2).min(axis=1)
    r = dict(r)
    r["peak_px"] = r["peak_px"] * 0.5                 # any wrong scale will do
    r["peak_depth_m"] = rad * 2.0
    return r


def _damaged_no_clamp(bbox, C, Rm, s, **kw):
    """Never clamps the projected height to the frame."""
    n = bbox.shape[0]
    corn = VF._corners(bbox)
    peak = np.zeros(n); pf = np.full(n, -1, dtype=np.int64)
    pd = np.full(n, np.inf); ever = np.zeros(n, dtype=bool)
    out = {b: np.zeros(n, dtype=np.int64) for b in VF.BANDS}
    for f in range(C.shape[0]):
        v = (corn - C[f]) @ Rm[f]
        depth = -v[:, :, 2]
        front = depth > 0.05
        if not front.any():
            continue
        ds = np.where(front, depth, np.nan)
        px = v[:, :, 0] * s[f] / ds
        py = v[:, :, 1] * s[f] / ds
        with np.errstate(invalid="ignore"):
            x0 = np.nanmin(px, axis=1); x1 = np.nanmax(px, axis=1)
            y0 = np.nanmin(py, axis=1); y1 = np.nanmax(py, axis=1)
        on = front.any(axis=1) & (x1 >= -VF.RES_X / 2) & (x0 <= VF.RES_X / 2) \
                               & (y1 >= -VF.RES_Y / 2) & (y0 <= VF.RES_Y / 2)
        h = np.where(on, y1 - y0, 0.0)                # <-- damage: no clamp
        ever |= on
        for b in VF.BANDS:
            out[b] += (h >= b)
        better = h > peak
        peak = np.where(better, h, peak); pf = np.where(better, f + 1, pf)
        pd = np.where(better, np.where(front, depth, np.inf).min(axis=1), pd)
    r = {"peak_px": peak, "peak_frame": pf, "peak_depth_m": pd, "ever_in_frame": ever}
    for b in VF.BANDS:
        r["frames_ge_%d" % b] = out[b]
    return r


def run_selftest_capturing():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = VF._selftest()
    txt = buf.getvalue()
    failed = set()
    for line in txt.splitlines():
        line = line.strip()
        if line.startswith("FAIL "):
            failed.add(line.split()[1])
    return rc, failed, txt


DAMAGE = [
    ("A_no_frustum_rejection", _damaged_no_frustum,
     {"negative_behind_camera", "negative_outside_frustum"}),
    ("B_radial_not_pinhole_depth", _damaged_radial,
     {"closed_form_height", "closed_form_depth"}),
    ("C_no_clamp_to_frame", _damaged_no_clamp,
     {"overfill_clamped_to_frame"}),
]


def main():
    rc, failed, _ = run_selftest_capturing()
    print("baseline (undamaged): rc=%d failed=%s" % (rc, sorted(failed) or "none"))
    if rc != 0 or failed:
        print(">> STAGE RESULT: CONTROL_FAIL (the undamaged tool does not pass)")
        return 1

    bad = []
    for name, fn, must_fire in DAMAGE:
        VF.measure = fn
        try:
            rc, failed, _ = run_selftest_capturing()
        finally:
            VF.measure = GOOD
        missed = must_fire - failed
        status = "ok  " if (rc != 0 and not missed) else "MISS"
        print("%s damage %-28s rc=%d fired=%s missed=%s"
              % (status, name, rc, sorted(failed) or "none", sorted(missed) or "none"))
        if rc == 0 or missed:
            bad.append(name)

    rc2, failed2, _ = run_selftest_capturing()
    if rc2 != 0:
        print("restore check FAILED -- the good tool no longer passes")
        bad.append("restore")

    print(">> STAGE RESULT: %s (%d/%d damage modes rejected)"
          % ("CONTROL_PASS" if not bad else "CONTROL_FAIL",
             len(DAMAGE) - len([b for b in bad if b != "restore"]), len(DAMAGE)))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
