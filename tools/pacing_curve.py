"""THE PACING CURVE — image change, its DERIVATIVE, and one-second novelty.

    .venv/bin/python tools/pacing_curve.py --video watch/AFTER_beat1_33s.mp4
    .venv/bin/python tools/pacing_curve.py --selftest

WHY THIS EXISTS, AND WHAT IT CORRECTS.  R2-831 measured the AMOUNT of frame-to-
frame image change across beat 1, found the energy curve inverted (20.27 across
the tour, 4.89 across the payoff) and moved it.  That fix was right and the
client still went to sleep.  R2-1144 then measured the same beat again and found
the amount was never the variable:

    first 4 s of beat 1      29.35 levels of frame-to-frame change
    the rest of beat 1       26.34 levels

The opening carries 1.11x MORE movement than what follows it.  What it does not
carry is any CHANGE in that movement.  So this tool reports three curves and the
headline is the second one:

    d1[f]    mean |I(f) - I(f-1)|        how much the image moves        (levels)
    a[f]     |d1[f] - d1[f-1]|           how much that RATE changes      (levels)
    nov[f]   mean |I(f) - I(f-FPS)|      how much is new since a second ago

A steady drift is hypnotic regardless of its magnitude -- it is the visual
equivalent of a held note -- and `a` is what tells a drift from a gesture.  On
beat 1 as delivered it runs 0.898 against a 16.52 mean: 5.4 % of the movement
itself.

THE UNITS ARE 8-BIT LEVELS ON THE LUMA PLANE AT THE PROXY'S OWN RESOLUTION and
that is load-bearing, because mean |difference| is NOT scale-invariant: it falls
as a frame is downscaled and the fall depends on the spatial frequency of what
is moving.  Every number this file prints is therefore tagged with the
resolution it was measured at, and two curves may only be compared when those
agree.  The selftest holds this file to R2-1144's published figures on
`watch/AFTER_beat1_33s.mp4`, so a change that silently moves the scale fails.
"""

import argparse
import json
import os
import subprocess
import sys

import numpy as np

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPS = 24


def decode_gray(path, width=None, height=None):
    """Stream a video's luma plane as a (n, h, w) uint8 array.

    Full resolution by default.  ffmpeg's `gray` output is the Y plane after the
    decoder's own colour conversion, which is what a viewer's eye integrates and
    what R2-1144 measured.
    """
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=width,height,nb_frames", "-of", "json", path],
        capture_output=True, text=True, check=True)
    st = json.loads(probe.stdout)["streams"][0]
    w = width or int(st["width"])
    h = height or int(st["height"])
    cmd = ["ffmpeg", "-v", "error", "-i", path]
    if width or height:
        cmd += ["-vf", f"scale={w}:{h}"]
    cmd += ["-f", "rawvideo", "-pix_fmt", "gray", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    n = len(raw) // (w * h)
    return np.frombuffer(raw[:n * w * h], dtype=np.uint8).reshape(n, h, w), w, h


def curves(frames, fps=FPS):
    """(d1, accel, novelty) as float arrays indexed by frame.

    d1[0], accel[0..1] and novelty[0..fps-1] have no predecessor and are NaN
    rather than zero.  A zero there is a real measurement of no movement and
    this project has already shipped one instrument that could not tell those
    apart.
    """
    n = len(frames)
    f = frames.astype(np.int16)
    d1 = np.full(n, np.nan)
    for i in range(1, n):
        d1[i] = np.abs(f[i] - f[i - 1]).mean()
    accel = np.full(n, np.nan)
    accel[2:] = np.abs(np.diff(d1[1:]))
    nov = np.full(n, np.nan)
    for i in range(fps, n):
        nov[i] = np.abs(f[i] - f[i - fps]).mean()
    return d1, accel, nov


def _m(a):
    a = np.asarray(a, dtype=float)
    a = a[np.isfinite(a)]
    return float(a.mean()) if a.size else float("nan")


def report(d1, accel, nov, label, w, h, fps=FPS, window_s=2.0):
    n = len(d1)
    print(f">> {label}  {n} frames @ {fps} fps, measured at {w}x{h} luma")
    print(f"   mean image change   {_m(d1):8.3f} levels")
    print(f"   mean |acceleration| {_m(accel):8.3f} levels  "
          f"= {100.0 * _m(accel) / max(_m(d1), 1e-9):5.2f} % of the mean change")
    print(f"   mean novelty (1 s)  {_m(nov):8.3f} levels")
    step = int(round(window_s * fps))
    print(f"   per-{window_s:g}s: t      change   |accel|   %of      novelty")
    for a in range(0, n, step):
        b = min(a + step, n)
        print(f"            {a / fps:6.2f}  {_m(d1[a:b]):7.2f}  "
              f"{_m(accel[a:b]):7.3f}  {100.0 * _m(accel[a:b]) / max(_m(d1[a:b]), 1e-9):5.2f}%  "
              f"{_m(nov[a:b]):7.2f}")


# --------------------------------------------------------------------------- #
#  THE SELFTEST — R2-1144's numbers, or this instrument is not the instrument.  #
# --------------------------------------------------------------------------- #
#
# A measurement tool written to justify a fix is worth nothing unless it first
# reproduces the measurement the fix is a response to.  These five figures are
# quoted in the R2-1144 defect entry and in the client brief; they were taken on
# `watch/AFTER_beat1_33s.mp4`, which is 792 frames of 1280x720.
R2_1144 = {
    "video": "watch/AFTER_beat1_33s.mp4",
    "first_6s_mean_change": 16.52,
    "first_6s_mean_accel": 0.898,
    "novelty_by_second": [48.50, 48.48, 37.36, 35.66, 36.09],
    "first_4s_change": 29.35,
    "rest_of_beat1_change": 26.34,
}


def selftest():
    path = os.path.join(R2, R2_1144["video"])
    if not os.path.exists(path):
        print(f">> SELFTEST SKIPPED: {path} is not on disk")
        return 0
    frames, w, h = decode_gray(path)
    d1, accel, nov = curves(frames)
    bad = []

    def chk(name, got, want, tol):
        ok = abs(got - want) <= tol
        print(f"   {'ok  ' if ok else 'FAIL'} {name:<28} got {got:8.3f}  "
              f"R2-1144 {want:8.3f}  (tol {tol})")
        if not ok:
            bad.append(name)

    print(f">> SELFTEST against R2-1144 on {R2_1144['video']} ({w}x{h}, "
          f"{len(frames)} frames)")
    n6 = 6 * FPS
    chk("first 6 s mean change", _m(d1[:n6]), R2_1144["first_6s_mean_change"], 0.05)
    chk("first 6 s mean |accel|", _m(accel[:n6]), R2_1144["first_6s_mean_accel"], 0.02)
    for i, want in enumerate(R2_1144["novelty_by_second"]):
        a, b = i * FPS, (i + 1) * FPS
        chk(f"novelty {i}-{i+1} s", _m(nov[a + FPS:b + FPS]), want, 0.35)
    n4 = 4 * FPS
    chk("first 4 s change", _m(d1[:n4]), R2_1144["first_4s_change"], 0.35)
    chk("rest of beat 1 change", _m(d1[n4:]), R2_1144["rest_of_beat1_change"], 0.35)
    print(">> STAGE RESULT: PACING_CURVE_SELFTEST_OK" if not bad
          else ">> STAGE RESULT: PACING_CURVE_SELFTEST_FAILED (%s)" % ", ".join(bad))
    return 0 if not bad else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video")
    ap.add_argument("--label", default=None)
    ap.add_argument("--window-s", type=float, default=2.0)
    ap.add_argument("--scale", default=None, help="WxH to measure at")
    ap.add_argument("--json-out", default=None)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.video:
        ap.error("--video or --selftest")
    w = h = None
    if a.scale:
        w, h = (int(v) for v in a.scale.lower().split("x"))
    frames, w, h = decode_gray(a.video, w, h)
    d1, accel, nov = curves(frames)
    report(d1, accel, nov, a.label or os.path.basename(a.video), w, h,
           window_s=a.window_s)
    if a.json_out:
        json.dump({"video": a.video, "w": w, "h": h, "fps": FPS,
                   "d1": [None if not np.isfinite(v) else round(float(v), 4) for v in d1],
                   "accel": [None if not np.isfinite(v) else round(float(v), 4) for v in accel],
                   "novelty": [None if not np.isfinite(v) else round(float(v), 4) for v in nov]},
                  open(a.json_out, "w"))
        print(f">> wrote {a.json_out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
