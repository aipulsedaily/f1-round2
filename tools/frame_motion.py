"""HOW FAR THE PICTURE MOVES, per frame, measured in PIXELS. R2-064's picture.

    .venv/bin/python tools/frame_motion.py --dir <seq dir> --prefix <name> \
        [--lo 748 --hi 832] [--ab <other dir> --ab-prefix <name>]

Every other instrument in this fix measures the camera path in metres. This one
opens the frames. It exists because "the camera path is smooth" and "the
picture moves smoothly" are different claims, and only the second is what a
viewer sees — the same distinction that made a 34 mm camera shift worth
arguing about and a 0.069 deg quaternion metric worth throwing away.

WHAT IS MEASURED

  shift_px   the whole-frame translation between consecutive frames, by
             phase correlation on the luminance (FFT cross-power spectrum,
             parabolic sub-pixel peak fit). This is a real displacement in
             pixels, not a difference score: a frame that gets brighter does
             not move, and mean |diff| cannot tell those apart.

  resid      the mean |diff| left after shifting the previous frame by the
             measured amount, over the mean |diff| before shifting. Below 1.0
             means the shift explains the change; near 1.0 means the frames
             differ for some reason a translation cannot account for, and the
             shift number should not be trusted on that frame. Reported so a
             bad estimate is visible rather than silently averaged in.

The seam defect predicts a specific, checkable thing: the pre-fix path runs
11.34 m/s at frame 795 where the fixed one runs 4.69, so at the same camera
distance the pre-fix picture must move roughly 2.4x further between 794 and
795. That is a prediction about pixels, made from geometry, and this is what
tests it.
"""

import argparse
import glob
import math
import os
import sys

import numpy as np
from PIL import Image


# Above this, the measured shift did not reduce the frame-to-frame difference
# and the translation model has failed. A number produced by a model that does
# not fit is worse than no number.
VALID_RESID = 0.95


def lum(p):
    a = np.asarray(Image.open(p).convert("L"), dtype=np.float64) / 255.0
    return a


def hann2(shape):
    return np.outer(np.hanning(shape[0]), np.hanning(shape[1]))


def phase_shift(a, b):
    """Translation from a to b, in pixels (dy, dx), sub-pixel."""
    w = hann2(a.shape)
    A = np.fft.rfft2(a * w)
    B = np.fft.rfft2(b * w)
    R = A.conj() * B
    m = np.abs(R)
    R = np.where(m > 1e-12, R / m, 0.0)
    c = np.fft.irfft2(R, s=a.shape)
    idx = np.unravel_index(np.argmax(c), c.shape)

    def sub(axis, i):
        n = c.shape[axis]
        im, ip = (i - 1) % n, (i + 1) % n
        s = [idx[0], idx[1]]
        s[axis] = im
        vm = c[tuple(s)]
        s[axis] = ip
        vp = c[tuple(s)]
        v0 = c[idx]
        d = 2.0 * (2.0 * v0 - vm - vp)
        return i + ((vp - vm) / d if abs(d) > 1e-12 else 0.0)

    dy, dx = sub(0, idx[0]), sub(1, idx[1])
    if dy > a.shape[0] / 2:
        dy -= a.shape[0]
    if dx > a.shape[1] / 2:
        dx -= a.shape[1]
    return dy, dx


def residual(a, b, dy, dx):
    base = np.mean(np.abs(b - a))
    sh = np.roll(np.roll(a, int(round(dy)), axis=0), int(round(dx)), axis=1)
    h = int(abs(round(dy))) + 1
    w = int(abs(round(dx))) + 1
    core = (slice(h, -h or None), slice(w, -w or None))
    after = np.mean(np.abs(b[core] - sh[core]))
    return after / base if base > 1e-9 else 0.0


# The three regions. A tracking shot has no single image motion: the camera
# holds the subject while the background sweeps behind it, so a whole-frame
# estimate averages two opposed motions and lands near zero. Measured on
# frame 805 of the fixed seam: background strip -24 px, subject box +36 px,
# whole frame +13 px. `tools/continuity_gate.py`'s D5 and D7 and its pacing
# "translation" figure are all computed from the whole-frame number, which is
# why they misread this beat — see R2-068.
REGIONS = {
    "background": (0.00, 0.21, 0.00, 1.00),      # above the car: the far wall
    "subject": (0.37, 0.71, 0.31, 0.73),         # the car
    "floor": (0.78, 1.00, 0.00, 1.00),           # the dais and its reflection
}


def region_series(d, prefix, lo, hi):
    """Per-region shift, per frame, with a residual for each region."""
    out, prev = {}, None
    for f in range(lo, hi + 1):
        hits = glob.glob(os.path.join(d, f"{prefix}*{f:06d}.png"))
        if not hits:
            prev = None
            continue
        cur = lum(hits[0])
        H, W = cur.shape
        if prev is not None:
            row = {}
            for name, (y0, y1, x0, x1) in REGIONS.items():
                sl = (slice(int(y0 * H), int(y1 * H)),
                      slice(int(x0 * W), int(x1 * W)))
                dy, dx = phase_shift(prev[sl], cur[sl])
                row[name] = (math.hypot(dy, dx), dx, dy,
                             residual(prev[sl], cur[sl], dy, dx))
            out[f] = row
        prev = cur
    return out


def series(d, prefix, lo, hi):
    out = {}
    prev = None
    for f in range(lo, hi + 1):
        hits = glob.glob(os.path.join(d, f"{prefix}*{f:06d}.png"))
        if not hits:
            prev = None
            continue
        cur = lum(hits[0])
        if prev is not None:
            dy, dx = phase_shift(prev, cur)
            out[f] = (math.hypot(dy, dx), dy, dx,
                      residual(prev, cur, dy, dx))
        prev = cur
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--prefix", default="")
    ap.add_argument("--ab")
    ap.add_argument("--ab-prefix", default="")
    ap.add_argument("--lo", type=int, default=748)
    ap.add_argument("--hi", type=int, default=832)
    ap.add_argument("--regions", action="store_true",
                    help="measure the background, the subject and the floor "
                         "separately, which is the only thing that works on a "
                         "tracking shot")
    a = ap.parse_args()

    if a.regions:
        R = region_series(a.dir, a.prefix, a.lo, a.hi)
        RB = region_series(a.ab, a.ab_prefix, a.lo, a.hi) if a.ab else {}
        names = list(REGIONS)
        print(f"=== REGION MOTION, dx in pixels, frames {a.lo}-{a.hi}  "
              f"({os.path.basename(a.dir.rstrip('/'))}"
              + (f" vs {os.path.basename(a.ab.rstrip('/'))}" if RB else "")
              + ")")
        print("     f " + "".join(f"{n:>13}" for n in names)
              + "     shear" + ("   |  A/B shear" if RB else ""))
        worst = (0.0, None)
        worstb = (0.0, None)
        for f in sorted(R):
            vals = [R[f][n][1] for n in names]
            sh = max(vals) - min(vals)
            if sh > worst[0]:
                worst = (sh, f)
            line = f"  {f:5d} " + "".join(f"{v:13.1f}" for v in vals) \
                + f"{sh:10.1f}"
            if f in RB:
                vb = [RB[f][n][1] for n in names]
                shb = max(vb) - min(vb)
                if shb > worstb[0]:
                    worstb = (shb, f)
                line += f"   |  {shb:10.1f}"
            print(line)
        bad = [(f, n) for f in R for n in names if R[f][n][3] > VALID_RESID]
        print(f"  worst shear {worst[0]:.1f} px at f{worst[1]}"
              + (f"   |  A/B worst shear {worstb[0]:.1f} px at f{worstb[1]}"
                 if RB else ""))
        print(f"  region estimates a translation does NOT explain "
              f"(resid > {VALID_RESID}): {len(bad)} of {len(R)*len(names)}")
        print(">> STAGE RESULT: REGION_MOTION_OK")
        return

    A = series(a.dir, a.prefix, a.lo, a.hi)
    if not A:
        raise SystemExit(f">> FAIL: no frames matched in {a.dir}")
    B = series(a.ab, a.ab_prefix, a.lo, a.hi) if a.ab else {}

    print(f"=== FRAME MOTION, phase correlation, frames {a.lo}-{a.hi}")
    hdr = "     f   shift_px   dy      dx    resid"
    if B:
        hdr += "  |  A/B shift_px   ratio"
    print(hdr)
    for f in sorted(A):
        r = A[f]
        line = (f"  {f:5d} {r[0]:9.3f} {r[1]:7.2f} {r[2]:7.2f} {r[3]:7.3f}")
        if f in B:
            line += f"  |  {B[f][0]:11.3f} {B[f][0]/max(r[0],1e-6):7.2f}"
        print(line)
    mx = max(A.items(), key=lambda kv: kv[1][0])
    print(f"  worst shift {mx[1][0]:.3f} px at f{mx[0]}")
    if B:
        mb = max(B.items(), key=lambda kv: kv[1][0])
        print(f"  A/B worst   {mb[1][0]:.3f} px at f{mb[0]}")
    res = sorted(r[3] for r in A.values())
    med = res[len(res) // 2]
    bad = [f for f, r in A.items() if r[3] > VALID_RESID]
    print(f"  median residual {med:.3f}; frames a translation does NOT "
          f"explain (resid > {VALID_RESID}): {len(bad)} of {len(A)}")
    if med > VALID_RESID:
        print("   REFUSED: a whole-frame translation does not describe what "
              "these frames do. The camera dollies past a subject 5-7 m away "
              "while rotating, so the picture changes by parallax and scale as "
              "much as by shift, and the number this would print is the peak "
              "of a correlation that never fitted. WHAT WOULD MAKE IT "
              "MEASURABLE: a long-lens passage where the subject is far "
              "compared with the camera's own travel, or a tracked feature "
              "rather than a global model. It is NOT valid here and the shifts "
              "above are printed for inspection only.")
        print(">> STAGE RESULT: FRAME_MOTION_NOT_APPLICABLE")
        sys.exit(2)
    print(">> STAGE RESULT: FRAME_MOTION_OK")


if __name__ == "__main__":
    main()
