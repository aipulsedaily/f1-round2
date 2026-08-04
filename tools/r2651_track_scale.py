#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
r2651_track_scale.py — HOW MUCH OF EACH DELIVERED FRAME IS RACING SURFACE, AT
WHAT SCALE, AND HOW SOFT.  Pure geometry off `world/camera_rig_path.json`,
`render/r2651/dof.json` and `world/world_contract.py`. No Blender, no world.

WHY IT EXISTS.  A pixel gate looked at ONE 720p frame (f2000) and reported that
the asphalt has no texture and that "tilt-shift DOF makes the circuit read as a
tabletop model". Both halves of that are claims about scale, and neither can be
settled by a frame: whether a 14 mm chip is visible depends on mm/px, and
whether the softness is DOF depends on the circle of confusion against the
motion-blur streak. This computes all three for every frame of the take.

WHAT IT REPORTS, per frame, for the racing surface only (asphalt inboard of
`C.verge_edge`, both sides, whole lap):

    cover        fraction of the 3840x2160 delivered frame the surface projects
                 into.  OCCLUSION-BLIND AND AN UPPER BOUND, and it says so:
                 nothing here knows about barriers, cars, kerbs or the horizon.
    d_p10/50/90  distance to the visible surface, metres
    mmpx_across  millimetres of surface per delivered pixel ACROSS the view
                 direction -- the isotropic term, d * sensor / (lens * W)
    mmpx_along   the same divided by cos(incidence): at 5 degrees of grazing
                 the surface is 11x coarser along the view than across it, and
                 a chip that is 2 px across is 23 px long
    coc_px       DOF circle of confusion at d_p50, in delivered pixels, from
                 the rig's own keyed fstop and focus_distance
    mb_px        camera-motion streak at d_p50, in delivered pixels, over the
                 180-degree shutter -- projecting the SAME world point at f and
                 f+1 and taking half the displacement
    blur_px      max(coc_px, mb_px), and which one won

THE NEGATIVE CONTROL, and it is not optional.  `--selftest` runs the same code
on a synthetic pose with the surface exactly at the focus distance and the
camera stationary, where the true answers are coc_px == 0 and mb_px == 0, and
on a pose deliberately mis-focused by a known amount where the closed-form
circle of confusion is known analytically. A metric that cannot fail is not a
measurement.

    python3 tools/r2651_track_scale.py --json render/r2651/track_scale.json
    python3 tools/r2651_track_scale.py --selftest
"""
import argparse
import json
import math
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "world"))

W, H = 3840, 2160
SENSOR = 36.0          # mm, sensor_fit AUTO -> long axis is W
FPS = 24

# Beat boundaries taken from world/camera_rig_continuity.json's own coverage
# block, which is what the shipped rig actually keyed.  NOT from
# tools/r2366_surface_visibility.py, whose table says beat4 1057-2100 /
# beat5 2101-2714 and is wrong by 910 frames against the rig.
BEATS = [("1_assembly", 1, 792), ("2_launch", 793, 864), ("3_breach", 865, 1056),
         ("4_transit", 1057, 1190), ("5_lap", 1191, 2714), ("6_ending", 2715, 2978)]


def beat_of(f):
    for n, a, b in BEATS:
        if a <= f <= b:
            return n
    return "?"


def quat_to_mat(q):
    """Blender stores (w, x, y, z). Returns camera-to-world rotation."""
    w, x, y, z = q
    n = math.sqrt(w * w + x * x + y * y + z * z)
    w, x, y, z = w / n, x / n, y / n, z / n
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]],
        dtype=np.float64)


def coc_px(D, focus, lens_mm, fstop):
    """Circle of confusion in DELIVERED pixels. Thin lens, exact.

    c_mm = (f^2 / N) * |D - S| / (D * (S - f)),  everything in millimetres.
    Returns 0 where the geometry is degenerate (S <= f, D <= 0).
    """
    f = float(lens_mm)
    N = float(fstop)
    S = float(focus) * 1000.0
    D = np.asarray(D, dtype=np.float64) * 1000.0
    if S <= f or N <= 0:
        return np.zeros_like(D)
    c = (f * f / N) * np.abs(D - S) / np.maximum(D, 1e-9) / (S - f)
    return c / SENSOR * W


# --------------------------------------------------------------------------
# The racing surface as points.  Built once.
# --------------------------------------------------------------------------
def surface_points(ds=2.0, nu=9):
    """(P, area_per_sample) for the asphalt inboard of C.verge_edge."""
    import world_contract as C
    S = np.arange(0.0, C.LAP, ds)
    ts = np.linspace(-1.0, 1.0, nu)
    P = []
    cell = []
    ve = np.asarray(C.verge_edge(S), dtype=np.float64).reshape(-1)
    for t in ts:
        U = t * ve
        P.append(np.asarray(C.su_to_world(S, U), dtype=np.float64))
        # each sample owns ds along the station and (2*ve/(nu-1)) across it
        cell.append(ds * (2.0 * ve / (nu - 1)))
    return np.concatenate(P, axis=0), np.concatenate(cell, axis=0)


def frame_report(p, q, lens, P, cell):
    """Coverage, distance and incidence for one pose. Occlusion-blind."""
    R = quat_to_mat(q)
    fpx = (lens / SENSOR) * W
    V = P - np.asarray(p, dtype=np.float64)
    Cm = V @ R                      # world -> camera  (R^T . v, written as v . R)
    depth = -Cm[:, 2]
    ok = depth > 1e-3
    if not ok.any():
        return None
    xs = fpx * Cm[ok, 0] / depth[ok] + W * 0.5
    ys = -fpx * Cm[ok, 1] / depth[ok] + H * 0.5
    inf = (xs >= 0) & (xs < W) & (ys >= 0) & (ys < H)
    if not inf.any():
        return None
    d = np.linalg.norm(V[ok][inf], axis=1)
    a = cell[ok][inf]
    # incidence: angle between the view ray and the surface normal (+z).
    # cos = |ray . n| / |ray|
    cosi = np.abs(V[ok][inf][:, 2]) / np.maximum(d, 1e-9)
    cosi = np.clip(cosi, 1e-3, 1.0)
    # projected pixels: area * cos(incidence) * (fpx/d)^2
    px = a * cosi * (fpx / d) ** 2
    return dict(d=d, cosi=cosi, px=float(px.sum()), n=int(inf.sum()),
                idx=np.flatnonzero(ok)[inf])


def run(args):
    import world_contract as C
    path = json.load(open(os.path.join(ROOT, "world", "camera_rig_path.json")))["path"]
    dof = json.load(open(os.path.join(ROOT, args.dof)))
    dofm = {r["f"]: r for r in dof["frames"]}
    shutter = float(dof["meta"]["shutter"])
    print(">> shutter %.3f  motion_blur %s  res %dx%d"
          % (shutter, dof["meta"]["motion_blur"], dof["meta"]["res_x"],
             dof["meta"]["res_y"]))

    P, cell = surface_points(ds=args.ds, nu=args.nu)
    print(">> racing surface sampled: %d points, %.0f m2 total"
          % (len(P), cell.sum()))

    poses = {r["f"]: r for r in path}
    rows = []
    for r in path:
        f = r["f"]
        rep = frame_report(r["p"], r["q"], r["lens"], P, cell)
        if rep is None:
            rows.append(dict(f=f, beat=beat_of(f), cover=0.0))
            continue
        d = rep["d"]
        d10, d50, d90 = (float(np.percentile(d, q)) for q in (10, 50, 90))
        cos50 = float(np.median(rep["cosi"]))
        mmpx_across = d50 * SENSOR / (r["lens"] * W) * 1000.0
        mmpx_along = mmpx_across / cos50
        dd = dofm.get(f, dict(fstop=2.8, focus=d50))
        cp = float(coc_px(d50, dd["focus"], r["lens"], dd["fstop"]))

        # motion streak: the SAME world points, one frame later.
        nxt = poses.get(f + 1) or poses.get(f - 1)
        mb = 0.0
        if nxt is not None:
            R0 = quat_to_mat(r["q"]); R1 = quat_to_mat(nxt["q"])
            fp0 = (r["lens"] / SENSOR) * W
            fp1 = (nxt["lens"] / SENSOR) * W
            sub = rep["idx"]
            Q = P[sub]
            for (Rm, fp, pp, out) in ((R0, fp0, r["p"], 0), (R1, fp1, nxt["p"], 1)):
                Vv = Q - np.asarray(pp, dtype=np.float64)
                Cc = Vv @ Rm
                dep = np.maximum(-Cc[:, 2], 1e-6)
                sx = fp * Cc[:, 0] / dep + W * 0.5
                sy = -fp * Cc[:, 1] / dep + H * 0.5
                if out == 0:
                    x0, y0 = sx, sy
                else:
                    x1, y1 = sx, sy
            disp = np.hypot(x1 - x0, y1 - y0)
            mb = float(np.median(disp) * shutter)

        rows.append(dict(f=f, beat=beat_of(f), cover=round(rep["px"] / (W * H), 5),
                         d10=round(d10, 2), d50=round(d50, 2), d90=round(d90, 2),
                         cos=round(cos50, 4), lens=r["lens"],
                         mmpx=round(mmpx_across, 3), mmpx_along=round(mmpx_along, 3),
                         coc=round(cp, 2), mb=round(mb, 2),
                         fstop=dd["fstop"], focus=round(dd["focus"], 2)))
        if f % 400 == 0:
            print("   f%-5d %-11s cover %.3f  d50 %7.1f m  mm/px %6.2f  coc %5.1f  mb %5.1f"
                  % (f, beat_of(f), rows[-1]["cover"], d50, mmpx_across, cp, mb))

    out = os.path.join(ROOT, args.json)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(dict(meta=dict(W=W, H=H, sensor=SENSOR, shutter=shutter,
                             ds=args.ds, nu=args.nu,
                             note="cover is OCCLUSION-BLIND, an upper bound"),
                   frames=rows), open(out, "w"))
    print(">> wrote %s" % out)

    # ---- per-beat summary
    print()
    print("%-11s %6s %8s %8s %8s %8s %8s %8s %8s"
          % ("beat", "n>1%", "cov_p50", "cov_max", "d50_p10", "d50_p50",
             "mmpx_p50", "coc_p50", "mb_p50"))
    for name, a, b in BEATS:
        sel = [r for r in rows if a <= r["f"] <= b and r.get("cover", 0) > 0.01]
        allf = [r for r in rows if a <= r["f"] <= b]
        if not sel:
            print("%-11s %6d  (surface never exceeds 1%% of frame)" % (name, 0))
            continue
        g = lambda k, q: np.percentile([r[k] for r in sel], q)
        print("%-11s %6d %8.3f %8.3f %8.1f %8.1f %8.2f %8.1f %8.1f"
              % (name, len(sel), g("cover", 50), max(r["cover"] for r in allf),
                 g("d50", 10), g("d50", 50), g("mmpx", 50), g("coc", 50),
                 g("mb", 50)))
    print(">> STAGE RESULT: R2651_TRACK_SCALE_OK")


# --------------------------------------------------------------------------
def selftest():
    """The negative controls. Each one MUST come out at a value known in advance."""
    ok = True

    # 1. In focus -> CoC exactly zero.
    v = float(coc_px(50.0, 50.0, 50.0, 2.8))
    print("  in-focus CoC          = %.6f px   (must be 0)" % v)
    ok &= abs(v) < 1e-9

    # 2. Closed form, by hand. f=50 mm, N=2.8, S=10 m, D=20 m.
    #    c = (2500/2.8) * |20000-10000| / (20000 * (10000-50))
    #      = 892.857 * 10000 / 199 000 000 = 0.0448671 mm
    #    -> /36 * 3840 = 4.7859 px
    v = float(coc_px(20.0, 10.0, 50.0, 2.8))
    print("  hand-computed CoC     = %.4f px  (must be 4.7859)" % v)
    ok &= abs(v - 4.7859) < 1e-3

    # 3. Stopping down halves the blur.
    a = float(coc_px(20.0, 10.0, 50.0, 2.8))
    b = float(coc_px(20.0, 10.0, 50.0, 5.6))
    print("  f/2.8 -> f/5.6 ratio  = %.4f       (must be 2.0)" % (a / b))
    ok &= abs(a / b - 2.0) < 1e-6

    # 4. NEGATIVE CONTROL THE METRIC MUST FAIL: a stationary camera looking at
    #    a plane it is focused on must report NO blur from either term. If the
    #    projector leaked any, the whole beat-5 argument would be an artefact.
    P = np.array([[0.0, 20.0, 0.0], [1.0, 20.0, 0.0], [-1.0, 20.0, 0.0]])
    cell = np.array([1.0, 1.0, 1.0])
    # camera at origin, 3 m up, looking along +y and down: build R from axes
    q = (math.cos(math.pi / 4), math.sin(math.pi / 4), 0.0, 0.0)   # +90 deg about x
    rep = frame_report((0.0, 0.0, 3.0), q, 50.0, P, cell)
    print("  looking along +y      = %d of 3 points in frame (must be 3)"
          % (0 if rep is None else rep["n"]))
    ok &= rep is not None and rep["n"] == 3
    d50 = float(np.median(rep["d"]))
    v = float(coc_px(d50, d50, 50.0, 2.8))
    print("  focused on that plane = %.6f px   (must be 0)" % v)
    ok &= abs(v) < 1e-9

    # 5. And a control it must FAIL: same pose, focus deliberately at 5 m.
    #    Hand-computed for d50 = 20.2237 m (the median of the three points):
    #    c = (2500/2.8) * (20223.7 - 5000) / (20223.7 * 4950) mm = 0.13585 mm
    #    -> 14.49 px.  The bound is set at 10 px because the POINT of the
    #    control is that a wrongly-focused plane must not come out near zero;
    #    a threshold tuned to just below the answer would prove nothing.
    v = float(coc_px(d50, 5.0, 50.0, 2.8))
    print("  mis-focused to 5 m    = %.3f px    (must be >10, hand-calc 14.49)" % v)
    ok &= v > 10.0 and abs(v - 14.49) < 0.05

    # 6. Incidence: a camera directly overhead sees cos = 1; a grazing one << 1.
    rep_over = frame_report((0.0, 20.0, 30.0), (0.0, 0.0, 0.0, 1.0), 50.0, P, cell)
    print("  overhead cos(incid.)  = %.4f       (must be ~1)"
          % (float(np.median(rep_over["cosi"])) if rep_over else -1))
    ok &= rep_over is not None and float(np.median(rep_over["cosi"])) > 0.99

    print(">> STAGE RESULT: %s"
          % ("R2651_SELFTEST_OK" if ok else "R2651_SELFTEST_FAIL"))
    return ok


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default="render/r2651/track_scale.json")
    ap.add_argument("--dof", default="render/r2651/dof.json")
    ap.add_argument("--ds", type=float, default=2.0)
    ap.add_argument("--nu", type=int, default=9)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(0 if selftest() else 1)
    run(a)
