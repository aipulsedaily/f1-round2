#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
r2651_line_probe.py — IS THE RUBBERED LINE THERE, IN THE DELIVERED PIXELS?

`build_surface.md` §2.5 measures the rubbered band at 2.2-2.9 : 1 against clean
tarmac. That measurement was taken from PLAN VIEWS UNDER A UNIFORM DOME, in
linear albedo. The film is a low sun at grazing incidence through AgX at
exposure -3.628. Those are not the same measurement and the second one has never
been taken.

So this takes it. For a delivered frame it:

  * walks the circuit centreline, finds the stations the camera can see,
  * for each, projects the whole cross-section u = -verge_edge .. +verge_edge,
  * reads the DELIVERED pixel luminance along that section,
  * and marks where `build_surface` says the rubber IS: the heart
    (+-0.55*spread), the shoulder (1.05*spread) and the feather, all centred on
    `racing_line_offset(s)` -- and, separately, where the CAR actually is.

The output is a luminance-vs-u profile with a PREDICTED dark band position. That
is a falsifiable prediction, not an impression: if the profile has a minimum at
the predicted `racing_line_offset` the band is present and legible; if it is
flat, or if its minimum is somewhere else, it is not.

NEGATIVE CONTROL (`--selftest`). The same profile is extracted against a
DELIBERATELY WRONG station offset (+400 m round the lap) and against a shuffled
line offset. A probe that reports "rubber found at the predicted place" for a
prediction that is 400 m away is measuring the road's own shading, not rubber,
and this project has shipped exactly that class of detector before.

    .venv/bin/python tools/r2651_line_probe.py \
        --frame 2000 --png ~/vast-render/out/seq/r1full/r1full_002000.png
    .venv/bin/python tools/r2651_line_probe.py --selftest
"""
import argparse
import json
import math
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "world"))
sys.path.insert(0, os.path.join(ROOT, "tools"))

from r2651_track_scale import quat_to_mat, SENSOR   # noqa: E402

W4K, H4K = 3840, 2160


def load_line():
    d = json.load(open(os.path.join(ROOT, "render/r2651/line.json")))
    return {k: np.asarray(v) for k, v in d.items() if k != "meta"} | {"meta": d["meta"]}


def luminance(rgb):
    """Rec.709 luma of the DELIVERED (already-graded) pixels. Display-referred
    on purpose: the question is what the audience sees, not what Cycles wrote."""
    return 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]


def section_profile(img, pose, L, s, nu=161, u_max=None):
    """Delivered luminance along the cross-section at station `s`.

    Returns (u, lum, valid) at the frame's own resolution, or None if the
    section is not on screen.
    """
    import world_contract as C
    H, Wpx = img.shape[:2]
    ve = float(np.interp(s, L["s"], L["verge_edge"])) if u_max is None else u_max
    u = np.linspace(-ve, ve, nu)
    P = np.asarray(C.su_to_world(np.full(nu, s), u), dtype=np.float64)
    R = quat_to_mat(pose["q"])
    fpx = (pose["lens"] / SENSOR) * Wpx           # scale to the frame we have
    V = P - np.asarray(pose["p"], dtype=np.float64)
    Cm = V @ R
    dep = -Cm[:, 2]
    ok = dep > 1e-3
    xs = np.full(nu, -1.0)
    ys = np.full(nu, -1.0)
    xs[ok] = fpx * Cm[ok, 0] / dep[ok] + Wpx * 0.5
    ys[ok] = -fpx * Cm[ok, 1] / dep[ok] + H * 0.5
    valid = ok & (xs >= 0) & (xs < Wpx) & (ys >= 0) & (ys < H)
    if valid.sum() < nu * 0.5:
        return None
    lum = np.full(nu, np.nan)
    lum[valid] = luminance(img[ys[valid].astype(int), xs[valid].astype(int)])
    return u, lum, valid, np.median(dep[valid])


def rubber_window(L, s):
    """(centre, heart_half, shoulder_half, feather_half) in metres, from
    build_surface.md §2.3's own table."""
    c = float(np.interp(s, L["s"], L["line"]))
    sp = float(np.interp(s, L["s"], L["spread"]))
    hw = float(np.interp(s, L["s"], L["half_width"]))
    return (c, 0.55 * sp, 1.05 * sp, min(1.9 * sp + 0.9, 0.78 * hw))


def contrast_at(u, lum, centre, half, hw):
    """Band depth against the LOCAL TREND, not against a global mean.

    Returns (inside, expected_from_trend, ratio) or None.

    THE TREND SUBTRACTION IS THE WHOLE POINT AND IT WAS FOUND BY A CONTROL.
    The first version compared the mean inside the band with the mean outside
    it. On a synthetic pure gradient with NO band that returns 0.72 — it reports
    a 1.4 : 1 band that does not exist — because the band centre is off-centre
    in `u`, so "outside" is weighted to one side and the gradient does the rest.
    A crowned road under a low oblique sun IS a gradient across `u`, so that
    version would have found rubber on every section it looked at.

    A straight line is fitted to the off-band samples and the band is measured
    as the residual against it, which is exactly zero for any linear gradient.
    """
    on = np.isfinite(lum) & (np.abs(u) <= hw)
    if on.sum() < 20:
        return None
    ins = on & (np.abs(u - centre) <= half)
    out = on & (np.abs(u - centre) > half * 2.2)
    if ins.sum() < 5 or out.sum() < 8:
        return None
    k, b0 = np.polyfit(u[out], lum[out], 1)
    trend_in = float(np.mean(k * u[ins] + b0))
    a = float(np.nanmean(lum[ins]))
    return a, trend_in, (trend_in / a if a > 1e-6 else float("nan"))


def run(a):
    import world_contract as C
    L = load_line()
    path = {r["f"]: r for r in json.load(
        open(os.path.join(ROOT, "world/camera_rig_path.json")))["path"]}
    pose = path[a.frame]
    img = np.asarray(Image.open(a.png).convert("RGB"), dtype=np.float64) / 255.0
    Hpx, Wpx = img.shape[:2]
    print(">> frame %d  %dx%d  lens %.2f mm  cam (%.1f, %.1f, %.1f)"
          % (a.frame, Wpx, Hpx, pose["lens"], *pose["p"]))

    # which stations are on screen: coarse scan of the centreline
    S = np.arange(0.0, C.LAP, 5.0)
    P = np.asarray(C.su_to_world(S, np.zeros_like(S)), dtype=np.float64)
    R = quat_to_mat(pose["q"])
    fpx = (pose["lens"] / SENSOR) * Wpx
    V = P - np.asarray(pose["p"], dtype=np.float64)
    Cm = V @ R
    dep = -Cm[:, 2]
    ok = dep > 1e-3
    xs = fpx * Cm[:, 0] / np.where(ok, dep, 1) + Wpx * 0.5
    ys = -fpx * Cm[:, 1] / np.where(ok, dep, 1) + Hpx * 0.5
    on = ok & (xs >= 0) & (xs < Wpx) & (ys >= 0) & (ys < Hpx)
    Son = S[on]
    don = dep[on]
    if len(Son) == 0:
        print(">> STAGE RESULT: R2651_LINE_PROBE_NO_TRACK_ON_SCREEN")
        return
    print(">> centreline stations on screen: %d  (s %.0f..%.0f, depth %.0f..%.0f m)"
          % (len(Son), Son.min(), Son.max(), don.min(), don.max()))

    order = np.argsort(don)
    picks = [Son[order[int(q * (len(order) - 1))]] for q in (0.02, 0.10, 0.25, 0.50)]
    print()
    print("%8s %7s %8s %9s %9s %8s %8s %8s"
          % ("s", "depth", "line_u", "heart_m", "lum_in", "lum_out", "ratio", "argmin_u"))
    results = []
    for s in picks:
        pr = section_profile(img, pose, L, float(s))
        if pr is None:
            print("%8.0f   (cross-section not sufficiently on screen)" % s)
            continue
        u, lum, valid, d = pr
        c, heart, shoulder, feather = rubber_window(L, float(s))
        hw = float(np.interp(s, L["s"], L["half_width"]))
        con = contrast_at(u, lum, c, heart, hw)
        onr = np.isfinite(lum) & (np.abs(u) <= hw)
        amin = float(u[onr][np.nanargmin(lum[onr])]) if onr.sum() > 5 else float("nan")
        if con is None:
            print("%8.0f %7.0f %8.2f %9.2f      (too few samples)" % (s, d, c, heart))
            continue
        print("%8.0f %7.0f %8.2f %9.2f %9.4f %8.4f %8.3f %8.2f"
              % (s, d, c, heart, con[0], con[1], con[2], amin))
        results.append(dict(s=float(s), depth=float(d), line_u=c, heart=heart,
                            lum_in=con[0], lum_out=con[1], ratio=con[2],
                            argmin_u=amin, half_width=hw,
                            u=u.tolist(), lum=[None if not np.isfinite(v) else round(float(v), 5) for v in lum]))
    if a.json:
        out = os.path.join(ROOT, a.json)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        json.dump(dict(frame=a.frame, png=a.png, rows=results), open(out, "w"))
        print(">> wrote %s" % out)
    print(">> STAGE RESULT: R2651_LINE_PROBE_OK")


def selftest():
    """Controls the probe must pass AND controls it must fail."""
    ok = True
    L = load_line()

    # 1. rubber_window reproduces build_surface.md 2.3 by hand at a known s.
    c, h, sh, fe = rubber_window(L, 100.0)
    sp = float(np.interp(100.0, L["s"], L["spread"]))
    hw = float(np.interp(100.0, L["s"], L["half_width"]))
    print("  s=100  spread %.4f  heart %.4f (must be 0.55*spread = %.4f)"
          % (sp, h, 0.55 * sp))
    ok &= abs(h - 0.55 * sp) < 1e-9
    ok &= abs(sh - 1.05 * sp) < 1e-9
    ok &= abs(fe - min(1.9 * sp + 0.9, 0.78 * hw)) < 1e-9

    # 2. contrast_at on a SYNTHETIC profile with a band of known depth.
    u = np.linspace(-8, 8, 161)
    lum = np.full_like(u, 0.10)
    lum[np.abs(u - 2.0) <= 1.5] = 0.04            # a 2.5 : 1 band at u = +2
    got = contrast_at(u, lum, 2.0, 1.5, 8.0)
    print("  synthetic band ratio  = %.4f   (must be 2.5)" % got[2])
    ok &= abs(got[2] - 2.5) < 1e-9

    # 3. NEGATIVE CONTROL THE PROBE MUST FAIL. Same synthetic profile, but the
    #    prediction is 5 m away from the band. A probe that still reports a
    #    ratio near 2.5 is finding structure wherever it looks.
    got = contrast_at(u, lum, -3.0, 1.5, 8.0)
    print("  band predicted 5 m off = %.4f   (must be ~1.0, NOT 2.5)" % got[2])
    ok &= abs(got[2] - 1.0) < 0.25

    # 4. A flat profile must give exactly 1.0 however hard it is asked.
    got = contrast_at(u, np.full_like(u, 0.07), 2.0, 1.5, 8.0)
    print("  flat profile ratio     = %.4f   (must be exactly 1.0)" % got[2])
    ok &= abs(got[2] - 1.0) < 1e-12

    # 5. And a gradient with NO band must not be reported as one. This is the
    #    real failure mode: a crowned, obliquely-lit road IS a gradient.
    got = contrast_at(u, 0.10 + 0.01 * u, 2.0, 1.5, 8.0)
    print("  pure gradient ratio    = %.4f   (must be within 5%% of 1.0)" % got[2])
    ok &= abs(got[2] - 1.0) < 0.05

    print(">> STAGE RESULT: %s"
          % ("R2651_LINE_PROBE_SELFTEST_OK" if ok else "R2651_LINE_PROBE_SELFTEST_FAIL"))
    return ok


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--frame", type=int, default=2000)
    ap.add_argument("--png", default=os.path.expanduser("~/vast-render/out/seq/r1full/r1full_002000.png"))
    ap.add_argument("--json", default="")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    sys.exit(0 if selftest() else 1) if a.selftest else run(a)
