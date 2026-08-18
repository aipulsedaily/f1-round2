#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r21061_sun_correlation.py — DOES THE SHOULDER TRACK THE SUN ACROSS THE WHOLE FILM?

Five frames agreeing with a specular prediction is five frames.  This asks the
same question of every delivered frame in the sweep at once: is the fraction of
the below-horizon frame that lands on AgX's shoulder a function of the angle
between the camera's view axis and the sun?

If it is, the bright road is the sun's specular sheen and the tone curve is a
bystander.  If shoulder area is uncorrelated with where the sun is, that
explanation is refuted and something else is lifting the road.

Reads `docs/r21061/knee_sweep.json` (levels) and the film's camera path
(geometry).  No render.

    .venv/bin/python tools/r21061_sun_correlation.py
"""
from __future__ import annotations

import json
import math
import os
import sys

import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUN_DIR = np.array([0.5178540, -0.8277670, 0.2159390])
TOKEN_OK = "R21061_SUN_CORRELATION_OK"
TOKEN_FAIL = "R21061_SUN_CORRELATION_FAIL"

BEATS = [(1, 792, "1_assembly"), (793, 864, "2_launch"), (865, 1056, "3_breach"),
         (1057, 1190, "4_transit"), (1191, 2714, "5_lap"), (2715, 2978, "6_ending")]


def quat_to_mat(q):
    w, x, y, z = q
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def beat(f):
    for a, b, n in BEATS:
        if a <= f <= b:
            return n
    return "?"


def main():
    rows = json.load(open(os.path.join(_ROOT, "docs/r21061/knee_sweep.json")))
    path = json.load(open(os.path.join(_ROOT, "render/film16_path.json")))["path"]
    P = {r["f"]: r for r in path}
    keep = {}
    for r in rows:
        if r["seq"] == "r2full" and r["frame"] in P:
            keep[r["frame"]] = r
    fs = sorted(keep)
    ang, sh75, sh60, clip, camz = [], [], [], [], []
    for f in fs:
        p = P[f]
        R = quat_to_mat(p["q"])
        fwd = R @ np.array([0.0, 0.0, -1.0])
        ang.append(math.degrees(math.acos(max(-1, min(1, float(np.dot(fwd, SUN_DIR)))))))
        sh75.append(keep[f]["sh75_below"] * 100)
        sh60.append(keep[f]["sh60_below"] * 100)
        clip.append(keep[f]["clip"] * 100)
        camz.append(p["p"][2])
    ang = np.array(ang); sh75 = np.array(sh75); sh60 = np.array(sh60)
    clip = np.array(clip); fs = np.array(fs); camz = np.array(camz)
    lap = (fs >= 1191) & (fs <= 2714)

    print(">> %d delivered frames with a pose; %d of them in beat 5" % (len(fs), lap.sum()))
    print(">> view-axis-to-sun angle vs shoulder area, BEAT 5 ONLY")
    print("%-16s %5s | %-28s | %-28s | %s"
          % ("view-to-sun", "n", "sh75 below-horizon %", "sh60 below-horizon %", "clip %"))
    bins = [(0, 30), (30, 60), (60, 90), (90, 120), (120, 150), (150, 181)]
    for lo, hi in bins:
        m = lap & (ang >= lo) & (ang < hi)
        if not m.sum():
            continue
        def st(x):
            return "p50 %6.2f p90 %6.2f max %6.2f" % (
                np.percentile(x[m], 50), np.percentile(x[m], 90), x[m].max())
        print("%3d-%3d deg      %5d | %s | %s | max %6.2f"
              % (lo, hi, m.sum(), st(sh75), st(sh60), clip[m].max()))

    # Spearman rank correlation, no scipy needed.
    def spearman(a, b):
        ra = np.argsort(np.argsort(a)).astype(float)
        rb = np.argsort(np.argsort(b)).astype(float)
        ra -= ra.mean(); rb -= rb.mean()
        return float((ra * rb).sum() / math.sqrt((ra * ra).sum() * (rb * rb).sum()))

    rho = spearman(ang[lap], sh75[lap])
    print(">> Spearman rho(view-to-sun angle, sh75) over beat 5 = %+.3f "
          "(negative = closer to the sun means more shoulder)" % rho)

    # NEGATIVE CONTROL: a quantity that must NOT explain it. Camera height has
    # no business predicting glare; if it correlates as strongly as the sun
    # angle does, the sun angle is not doing the work either.
    rho_z = spearman(camz[lap], sh75[lap])
    print(">> NEGATIVE CONTROL rho(camera height, sh75) = %+.3f" % rho_z)

    bad = []
    if rho > -0.30:
        bad.append("shoulder area does not track the sun (rho %+.3f); the "
                   "specular explanation is refuted" % rho)
    if abs(rho_z) >= abs(rho):
        bad.append("camera height predicts the shoulder as well as the sun does "
                   "(%+.3f vs %+.3f); neither is an explanation" % (rho_z, rho))

    # The arcs, as contiguous runs of frames over a threshold.
    print(">> THE ARCS: contiguous runs with sh75_below > 10 %, beat 5")
    THR = 10.0
    runs, cur = [], None
    for i, f in enumerate(fs):
        if not lap[i]:
            continue
        if sh75[i] > THR:
            if cur is None:
                cur = [f, f, sh75[i], clip[i], ang[i]]
            else:
                cur[1] = f
                cur[2] = max(cur[2], sh75[i])
                cur[3] = max(cur[3], clip[i])
                cur[4] = min(cur[4], ang[i])
        else:
            if cur is not None and cur[1] - cur[0] >= 5:
                runs.append(cur)
            cur = None
    if cur is not None:
        runs.append(cur)
    tot = 0
    for a, b, s, c, an in runs:
        tot += (b - a + 1)
        print("   f%-5d - f%-5d  %5.2f s   peak sh75 %5.1f %%  peak clip %5.2f %%  "
              "closest view-to-sun %5.1f deg" % (a, b, (b - a + 1) / 24.0, s, c, an))
    print("   TOTAL %d frames = %.2f s of the film's %.1f s"
          % (tot, tot / 24.0, 2978 / 24.0))
    for b_ in bad:
        print("   FAIL " + b_)
    print(">> STAGE RESULT: " + (TOKEN_OK if not bad else TOKEN_FAIL))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
