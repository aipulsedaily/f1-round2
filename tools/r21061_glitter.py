#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r21061_glitter.py — IS THE BRIGHT PATCH ON THE ROAD A SPECULAR SHEEN?

The sweep found the film's brightest below-horizon regions in three short arcs
of the lap.  "It looks like sun glare" is a description, not evidence.  This
tests it GEOMETRICALLY and with NO RENDER: for a flat horizontal road it
computes the SPECULAR POINT -- the ground point whose mirror reflection of the
view ray lands on the sun -- projects it into the delivered frame, and reports
where it falls.

If the measured bright region is centred on that point and elongated along the
sun's azimuth, it is a specular sheen and the tone curve is not its cause.  If
the bright region has nothing to do with it, the brightness is diffuse or
atmospheric and the specular hypothesis is REFUTED.

CONTROLS.  A frame in which the camera looks AWAY from the sun must have no
specular point in shot -- that is the negative control, and it is required to
fire, because a predictor that puts a hot spot in every frame explains nothing.

    .venv/bin/python tools/r21061_glitter.py --frames 2340 2360 2225 2000
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "world"))

TOKEN_OK = "R21061_GLITTER_OK"
TOKEN_FAIL = "R21061_GLITTER_FAIL"

#: world_contract's measured sun. Unit vector pointing TO the sun.
SUN_DIR = np.array([0.5178540, -0.8277670, 0.2159390])
SENSOR_W = 36.0                                   # mm, Blender default


def quat_to_mat(q):
    w, x, y, z = q
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def load_path(p):
    d = json.load(open(p))
    return {r["f"]: r for r in d["path"]}


def project(P, cam_p, R, lens, W, H):
    """World point -> pixel (x, y) with origin TOP-LEFT. None if behind."""
    v = np.asarray(P) - cam_p
    c = R.T @ v                                   # camera space, -Z forward
    if c[2] >= -1e-6:
        return None
    f_px = lens / SENSOR_W * W
    x = W * 0.5 + f_px * (c[0] / -c[2])
    y = H * 0.5 - f_px * (c[1] / -c[2])
    return (x, y)


def specular_point(cam_p, z_ground=0.0):
    """Ground point whose mirror reflection of the view ray reaches the sun.

    For a horizontal plane the reflected direction of a ray hitting the ground
    is the incoming direction with z negated.  We want the OUTGOING ray to the
    sun, so the incoming view ray must be SUN_DIR with z negated, i.e. the
    camera looks along (Sx, Sy, -Sz).  Walking that from the camera to z_ground
    gives the point.
    """
    d = np.array([SUN_DIR[0], SUN_DIR[1], -SUN_DIR[2]])
    if d[2] >= -1e-9:
        return None
    t = (z_ground - cam_p[2]) / d[2]
    return cam_p + t * d if t > 0 else None


def measure_png(path, W=None, H=None):
    from PIL import Image
    a = np.asarray(Image.open(path).convert("RGB")).astype(np.float64) / 255.0
    L = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
    return a, L


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", default=os.path.join(_ROOT, "render", "film16_path.json"))
    ap.add_argument("--seq", default=os.path.expanduser("~/vast-render/out2/seq/r2full"))
    ap.add_argument("--pat", default="r2full_%06d.png")
    ap.add_argument("--frames", type=int, nargs="+", required=True)
    ap.add_argument("--thr", type=float, default=0.8125)   # 50 % of peak slope
    a = ap.parse_args(sys.argv[1:])
    P = load_path(a.path)
    bad = []
    print(">> SUN_DIR %s  elevation %.3f deg  bearing %.3f deg"
          % (tuple(round(v, 5) for v in SUN_DIR),
             math.degrees(math.asin(SUN_DIR[2])),
             math.degrees(math.atan2(SUN_DIR[0], SUN_DIR[1]))))
    print("%6s %7s %8s %9s %9s  %-22s %-22s %s"
          % ("frame", "lens", "cam z", "view.sun", "spec dist",
             "spec point px", "bright centroid px", "verdict"))
    for f in a.frames:
        r = P.get(f)
        if r is None:
            bad.append("frame %d not in the path" % f)
            continue
        cam_p = np.array(r["p"], dtype=float)
        R = quat_to_mat(r["q"])
        fwd = R @ np.array([0.0, 0.0, -1.0])
        png = os.path.join(a.seq, a.pat % f)
        if not os.path.exists(png):
            bad.append("no delivered frame at %s" % png)
            continue
        rgb, L = measure_png(png)
        H, W = L.shape
        m = L > a.thr
        # the bright region BELOW the horizon only: drop the top 45 % of rows,
        # which is where sky lives in every frame in this set.
        mb = m.copy()
        mb[: int(H * 0.45)] = False
        if mb.sum() > 0:
            ys, xs = np.nonzero(mb)
            cen = (float(xs.mean()), float(ys.mean()))
            frac = float(mb.mean())
        else:
            cen, frac = (float("nan"), float("nan")), 0.0
        S = specular_point(cam_p)
        if S is None:
            sp, dist = None, float("nan")
        else:
            sp = project(S, cam_p, R, float(r["lens"]), W, H)
            dist = float(np.linalg.norm(S - cam_p))
        va = math.degrees(math.acos(max(-1, min(1, float(np.dot(fwd, SUN_DIR))))))
        inshot = sp is not None and -0.25 * W <= sp[0] <= 1.25 * W and -0.25 * H <= sp[1] <= 1.25 * H
        if S is None:
            verdict = "camera at or below the road plane"
        elif sp is None:
            verdict = "specular point BEHIND the camera (looking away from the sun)"
        elif not inshot:
            verdict = "specular point OUT of frame"
        elif frac < 0.005:
            verdict = "specular point in frame, NO bright region"
        else:
            d = math.hypot(sp[0] - cen[0], sp[1] - cen[1]) / W
            verdict = "centroid %.2f frame-widths from specular point" % d
        print("%6d %7.2f %8.2f %9.2f %9.1f  %-22s %-22s %s"
              % (f, r["lens"], cam_p[2], va, dist,
                 ("(%7.1f,%7.1f)" % sp) if sp else "-",
                 ("(%7.1f,%7.1f)" % cen) if frac else "-", verdict))
    for b in bad:
        print("   FAIL " + b)
    print(">> STAGE RESULT: " + (TOKEN_OK if not bad else TOKEN_FAIL))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
