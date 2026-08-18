#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r21061_exposure_counterfactual.py — WHAT A MASTER EXPOSURE MOVE WOULD COST.

The four candidate homes for a "fix" each look like they worked on the frame you
tested.  This one can be tested on EVERY frame at once, for free, because the
delivered PNGs plus the film's own measured transfer are enough to re-grade them.

METHOD.  Invert the display value through `render/r2651/agx.json` to
scene-linear, apply `--stops`, push it back through the same curve.  That is
exactly what `scene.view_settings.exposure` does, one step earlier in the same
pipeline.

WHAT THIS APPROXIMATION IS WORTH, STATED UP FRONT.  `agx.json` is a NEUTRAL
ramp, so this re-grades each channel through the grey transfer.  AgX is not
channel-separable -- it has a chromaticity inset -- so a saturated pixel will be
off.  It is exact for neutrals and good for luma statistics, which is all it is
used for.  `--validate` checks it against a real rendered pair at two exposures
and prints the residual; a simulation with no ground truth is a guess.

    .venv/bin/python tools/r21061_exposure_counterfactual.py --stops -2.07
    .venv/bin/python tools/r21061_exposure_counterfactual.py \
        --validate A.png B.png --stops -2.072
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys

import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "tools"))

from r21061_knee_sweep import Curve, _luma, _load, _horizon_row   # noqa: E402

TOKEN_OK = "R21061_COUNTERFACTUAL_OK"
TOKEN_FAIL = "R21061_COUNTERFACTUAL_FAIL"

BEATS = [(1, 792, "1_assembly"), (793, 864, "2_launch"), (865, 1056, "3_breach"),
         (1057, 1190, "4_transit"), (1191, 2714, "5_lap"), (2715, 2978, "6_ending")]


def regrade(rgb, curve, stops):
    """Display RGB -> scene-linear -> x 2**stops -> display RGB."""
    lin = np.interp(rgb, curve.disp, curve.lin) * (2.0 ** stops)
    return np.interp(lin, curve.lin, curve.disp)


def beat(f):
    for a, b, n in BEATS:
        if a <= f <= b:
            return n
    return "?"


def validate(a_png, b_png, stops, curve):
    """A real rendered pair is the only thing that can check the simulation."""
    A = _load(a_png)
    B = _load(b_png)
    if A.shape != B.shape:
        print("   FAIL the two frames are different sizes")
        return ["shape mismatch"]
    S = regrade(A, curve, stops)
    la, lb, ls = _luma(A), _luma(B), _luma(S)
    err = ls - lb
    print("   real A  luma mean %.4f   real B  luma mean %.4f   simulated B %.4f"
          % (la.mean(), lb.mean(), ls.mean()))
    print("   simulated B - real B:  mean %+.4f  p50 %+.4f  p99 |err| %.4f  max |err| %.4f"
          % (err.mean(), np.percentile(err, 50), np.percentile(np.abs(err), 99),
             np.abs(err).max()))
    bad = []
    if abs(err.mean()) > 0.02:
        bad.append("the simulation is biased by %+.4f in mean luma" % err.mean())
    if np.percentile(np.abs(err), 99) > 0.06:
        bad.append("99th-percentile error is %.4f display, too large to argue from"
                   % np.percentile(np.abs(err), 99))
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stops", type=float, default=-2.07)
    ap.add_argument("--seq", action="append",
                    default=[os.path.expanduser("~/vast-render/out2/seq/r2full"),
                             os.path.expanduser("~/vast-render/out2/seq/r2beat1_v2")])
    ap.add_argument("--step", type=int, default=5)
    ap.add_argument("--validate", nargs=2, default=None)
    a = ap.parse_args(sys.argv[1:])
    c = Curve()
    bad = []
    if a.validate:
        print(">> VALIDATION against a real rendered pair, %+.3f stops" % a.stops)
        bad += validate(a.validate[0], a.validate[1], a.stops, c)

    t75 = c.display_at_slope_fraction(0.75)
    t60 = c.display_at_slope_fraction(0.60)
    print(">> COUNTERFACTUAL: master exposure %+.3f stops (i.e. %.3f -> %.3f)"
          % (a.stops, -3.628, -3.628 + a.stops))
    print("%-12s %5s | %-24s | %-24s | %s"
          % ("beat", "n", "sh75 below-horizon %", "pure black %", "lum p50"))
    import collections
    agg = collections.defaultdict(lambda: [[], [], [], [], []])
    for d in a.seq:
        for i, p in enumerate(sorted(glob.glob(os.path.join(d, "*.png")))[::a.step]):
            f = int(os.path.basename(p).split("_")[-1].split(".")[0])
            rgb = _load(p)
            L0 = _luma(rgb)
            L1 = _luma(regrade(rgb, c, a.stops))
            hr = _horizon_row(L0)
            b0 = L0[hr:] if hr < L0.shape[0] else L0
            b1 = L1[hr:] if hr < L1.shape[0] else L1
            g = agg[beat(f)]
            g[0].append(float((b0 > t75).mean()) * 100)
            g[1].append(float((b1 > t75).mean()) * 100)
            # "pure black" is R2-082's gate: a pixel at literal 0 after grading
            g[2].append(float((L0 <= 0.5 / 255.0).mean()) * 100)
            g[3].append(float((L1 <= 0.5 / 255.0).mean()) * 100)
            g[4].append((float(np.percentile(L0, 50)), float(np.percentile(L1, 50))))
    for _, _, n in BEATS:
        if n not in agg:
            continue
        g = agg[n]
        print("%-12s %5d | now %6.2f -> %6.2f     | now %6.4f -> %6.4f    | %.3f -> %.3f"
              % (n, len(g[0]), np.median(g[0]), np.median(g[1]),
                 np.max(g[2]), np.max(g[3]),
                 np.median([x[0] for x in g[4]]), np.median([x[1] for x in g[4]])))
    for b in bad:
        print("   FAIL " + b)
    print(">> STAGE RESULT: " + (TOKEN_OK if not bad else TOKEN_FAIL))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
