#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Band-limited contrast of a DELIVERED frame, per octave, in PIXELS.

WHY THIS EXISTS.  "The circuit surface reads as untextured" is a claim about
pixels, and this project has twice had a metric say one thing while the frame
said another (R2-433, R2-605).  R2-653 already showed that a *scale* table can
prove a layer is sub-pixel, but a scale table cannot tell you whether the
layers that ARE resolved carry any contrast, and it cannot separate a material
that is smooth from an atmosphere that has washed a good material flat.  That
separation is the whole question here: R2-652 found the last asphalt complaint
belonged to the camera department, and the same trap is live again — the road
in `before_f2225.png` is cream and featureless, and so is the terrain beside it.

THE INSTRUMENT.  A Laplacian pyramid on the display luma of a rectangle, giving
RMS contrast (band RMS / patch mean) per octave, band centre quoted in pixels of
the DELIVERED 3840x2160 frame.  Pixels, not millimetres, because "does it read"
is a question about the delivered image; the mm conversion is applied afterwards
from `track_scale.json`'s per-frame mm/px and is reported separately so a wrong
scale cannot corrupt the contrast number.

THE CONTROL THAT MAKES IT AN INSTRUMENT.  The atmosphere hypothesis is refuted
or confirmed by measuring a NON-ASPHALT patch at the same depth in the same
frame.  If the kerb's 100 mm stripes carry contrast where the asphalt carries
none, the haze is not the cause and the material is.  If both are flat, it is
the atmosphere and this is not the asphalt's defect — the R2-652 verdict, and
it must be available to fire again.

`--selftest` carries five controls, two of which the metric MUST fail.
"""
from __future__ import annotations
import argparse
import json
import os
import sys

import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# --------------------------------------------------------------------------- core
def _luma(rgb):
    """Rec.709 luma of a float [0,1] DISPLAY-referred image."""
    return (0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2])


def _blur5(a):
    """Separable 5-tap binomial blur — the classic Burt-Adelson pyramid kernel."""
    k = np.array([1.0, 4.0, 6.0, 4.0, 1.0])
    k /= k.sum()
    p = np.pad(a, 2, mode="edge")
    out = np.zeros_like(a)
    for i, w in enumerate(k):
        out += w * p[2:-2, i:i + a.shape[1]]
    p2 = np.pad(out, 2, mode="edge")
    out2 = np.zeros_like(a)
    for i, w in enumerate(k):
        out2 += w * p2[i:i + a.shape[0], 2:-2]
    return out2


_MARGIN = 6          # px of each band discarded before the RMS is taken


def octaves(patch, n=7):
    """[(centre_px, rms_contrast)] for `n` octaves, finest first.

    Band k is the Laplacian level after k decimations and therefore carries
    full-resolution wavelengths around **2^(k+2) px** — the calibration is not
    asserted, it is what `--selftest`'s single-sinusoid control measures, and
    the first version of this function was an octave out until that control
    said so.

    Contrast is band RMS divided by the patch MEAN, so it is a relative
    contrast and is comparable between a dark road and a bright kerb.

    `_MARGIN` px are cropped off every band before the RMS.  A binomial blur
    reproduces a linear ramp EXACTLY in the interior and not at the edge, where
    `mode="edge"` padding folds the ramp back on itself; without the crop the
    flat-ramp control returns 1.6e-3 of pure boundary artefact and the metric
    would report texture on a crowned road under a low sun — R2-654's false
    positive, in a different instrument.
    """
    a = patch.astype(np.float64)
    mean = float(a.mean())
    if mean <= 1e-9:
        return []
    cur = a
    rows = []
    for k in range(n):
        if min(cur.shape) < 4 * _MARGIN:
            break
        lo = _blur5(cur)
        band = (cur - lo)[_MARGIN:-_MARGIN, _MARGIN:-_MARGIN]
        rows.append((2.0 ** (k + 2), float(band.std()) / mean))
        # decimate for the next octave
        cur = lo[::2, ::2]
    return rows


def measure(img, rect, n=7):
    x0, y0, x1, y1 = rect
    patch = _luma(img[y0:y1, x0:x1])
    return octaves(patch, n), float(patch.mean()), float(patch.std())


# --------------------------------------------------------------------------- io
def load_png(path):
    from PIL import Image
    a = np.asarray(Image.open(path).convert("RGB")).astype(np.float64) / 255.0
    return a


def mmpx_of(frame):
    p = os.path.join(_ROOT, "render", "r2651", "track_scale.json")
    if not os.path.exists(p):
        return None
    with open(p) as fh:
        for r in json.load(fh)["frames"]:
            if r["f"] == frame:
                return r.get("mmpx")
    return None


# --------------------------------------------------------------------------- report
def report(name, rows, mean, mmpx=None):
    print("  %-26s mean %.4f" % (name, mean))
    print("      %-10s %-12s %s" % ("band px", "rms contrast",
                                    "band mm" if mmpx else ""))
    for c, v in rows:
        mm = ("%10.1f" % (c * mmpx)) if mmpx else ""
        print("      %-10.0f %-12.5f %s" % (c, v, mm))


# --------------------------------------------------------------------------- selftest
def selftest():
    print(">> SELFTEST r21031_octave_contrast")
    ok = True
    rng = np.random.default_rng(20260807)
    H = W = 256

    def chk(name, cond, msg):
        nonlocal ok
        print("   %-42s %s   %s" % (name, "PASS" if cond else "FAIL", msg))
        ok = ok and bool(cond)

    # 1. a pure linear ramp has NO band-limited contrast.  A metric that finds
    #    texture on a gradient would find texture on a crowned road under a low
    #    sun, which is exactly the false positive R2-654's band probe had.
    yy, xx = np.mgrid[0:H, 0:W]
    ramp = 0.30 + 0.25 * xx / W
    r = octaves(ramp)
    worst = max(v for _, v in r[:4])
    chk("MUST FAIL: linear ramp reads as flat", worst < 1e-4,
        "worst fine-band contrast %.2e (bar 1e-4)" % worst)

    # 2. a single sinusoid must appear in ITS OWN octave and nowhere else.
    lam = 16.0
    sine = 0.30 * (1.0 + 0.20 * np.sin(2 * np.pi * xx / lam))
    r = dict(octaves(sine))
    peak = max(r, key=lambda c: r[c])
    chk("a 16 px sinusoid peaks in the 16 px band", abs(peak - 16.0) < 1e-6,
        "peak band %.0f px, contrast %.4f" % (peak, r[peak]))
    # amplitude: a 0.20 relative sine has rms 0.20/sqrt(2) = 0.1414 spread over
    # the band; the pyramid splits it, so require it to be recovered to +-40 %.
    chk("...and recovers its amplitude", 0.06 <= r[peak] <= 0.15,
        "recovered %.4f against a 0.1414 rms sine" % r[peak])

    # 3. two sinusoids two octaves apart must both appear.  A metric that only
    #    reports total variance cannot tell a surface with one scale from a
    #    surface with three, which is the failure this whole task is about.
    Y2, X2 = np.mgrid[0:512, 0:512]
    two = 0.30 * (1.0 + 0.12 * np.sin(2 * np.pi * X2 / 8.0)
                  + 0.12 * np.sin(2 * np.pi * Y2 / 64.0))
    r = dict(octaves(two))
    chk("two scales are resolved as two", r[8.0] > 0.03 and r[64.0] > 0.03,
        "8 px %.4f, 64 px %.4f, 32 px %.4f (the empty octave between)"
        % (r[8.0], r[64.0], r[32.0]))

    # 4. MUST FAIL: a smooth field that has been BLURRED is not the same as a
    #    field that never had detail, and the metric must not confuse them —
    #    it must report the blurred one as low, so an atmosphere-washed frame
    #    is distinguishable from nothing only by the control patch, not by
    #    wishful reading of this number.
    noise = 0.30 * (1.0 + 0.25 * rng.standard_normal((H, W)))
    blurred = noise.copy()
    for _ in range(6):
        blurred = _blur5(blurred)
    rn = dict(octaves(noise))
    rb = dict(octaves(blurred))
    chk("MUST FAIL: heavy blur kills the fine octaves",
        rb[4.0] < 0.05 * rn[4.0],
        "fine band %.5f blurred vs %.5f sharp" % (rb[4.0], rn[4.0]))

    print(">> STAGE RESULT: selftest %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


# --------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--png")
    ap.add_argument("--frame", type=int)
    ap.add_argument("--rect", nargs=4, type=int, action="append",
                    metavar=("X0", "Y0", "X1", "Y1"))
    ap.add_argument("--label", action="append", default=None)
    ap.add_argument("--json")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.png:
        ap.error("--png required")
    img = load_png(a.png)
    mmpx = mmpx_of(a.frame) if a.frame else None
    print("== %s  %dx%d  mm/px %s" % (os.path.basename(a.png), img.shape[1],
                                      img.shape[0],
                                      "%.2f" % mmpx if mmpx else "unknown"))
    out = {"png": a.png, "frame": a.frame, "mmpx": mmpx, "patches": []}
    labels = a.label or []
    for i, rect in enumerate(a.rect or []):
        lab = labels[i] if i < len(labels) else "rect%d" % i
        rows, mean, sd = measure(img, rect)
        report(lab, rows, mean, mmpx)
        out["patches"].append({"label": lab, "rect": rect, "mean": mean,
                               "sd": sd,
                               "octaves": [{"px": c, "rms": v} for c, v in rows]})
    if a.json:
        with open(a.json, "w") as fh:
            json.dump(out, fh, indent=1)
        print("   wrote %s" % a.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
