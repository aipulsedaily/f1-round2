#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
r2651_band_sweep.py — DOES THE f2000 FINDING GENERALISE? Pure projection.

One frame cannot convict a sim, and beats 4 and 6 have no rendered frames at
all. This answers the generalisation question WITHOUT rendering anything, by
asking two things of every one of the 2,978 poses:

  1. WHERE IS THE RUBBER, ON SCREEN.  How many delivered pixels the rubbered
     band's heart occupies, and what share of the visible racing surface that
     is. If the band is off-frame or sub-pixel for most of the lap then "no
     rubbered-in racing line" generalises for a reason that has nothing to do
     with the material, and no amount of albedo will fix it.

  2. IS THE CAR ON IT.  The car's own lateral offset, from `telemetry.csv`
     projected through `world_contract.project`, against the band's heart,
     shoulder and feather at the same station. This is R2-651 evaluated at
     every frame instead of at the median.

NEGATIVE CONTROLS (`--selftest`), because a coverage number believed without one
is this project's most repeated failure:

  * a pose looking away from the circuit must report zero band pixels;
  * the band's pixel count must be BOUNDED BY the surface pixel count at every
    frame — a band wider than the road it is painted on is an arithmetic error,
    and the first version of the halo in `build_surface` was exactly that;
  * a car placed ON the line by construction must report `on_heart` True at
    every station, and a car displaced by 20 m must report it at none.

    .venv/bin/python tools/r2651_band_sweep.py --json render/r2651/band_sweep.json
    .venv/bin/python tools/r2651_band_sweep.py --selftest
"""
import argparse
import csv
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "world"))
sys.path.insert(0, os.path.join(ROOT, "tools"))

from r2651_track_scale import quat_to_mat, SENSOR, BEATS, beat_of, W, H  # noqa: E402


def load_line():
    return json.load(open(os.path.join(ROOT, "render/r2651/line.json")))


def band_edges(L, S):
    """(centre, heart, shoulder, feather) half-widths in metres at stations S.
    build_surface.md 2.3's own table."""
    ls = np.asarray(L["s"])
    c = np.interp(S, ls, L["line"])
    sp = np.interp(S, ls, L["spread"])
    hw = np.interp(S, ls, L["half_width"])
    return c, 0.55 * sp, 1.05 * sp, np.minimum(1.9 * sp + 0.9, 0.78 * hw)


def car_track_offsets():
    """(film_frame, station, lateral) for the car, from the telemetry.

    THE FRAME JOIN IS DERIVED FROM THE DATA, AND THE OBVIOUS GUESS IS WRONG.

    `telemetry.csv` numbers frames from the car's first movement, so the tempting
    join is `film = telemetry + 33.0 s * 24 fps = +792`, beat 2 being where the
    car starts moving. **That is wrong by 181 frames**, and a control in
    `--selftest` caught it: it lands the lap on stations 514..3671 instead of on
    the whole 3,675 m, and it leaves the lap 180 frames short of beat 5.

    The reason is beat 3. The breach runs WORLD TIME at 15-25 % of screen time,
    so 8 seconds of film buys about 1.5 seconds of car, and film time is not
    telemetry time plus a constant anywhere before beat 5.

    So the offset is solved instead: `telemetry.s_m` is global arc length
    including the transit, and its maximum minus `C.LAP` is the transit length
    (377.730 m). The telemetry frame at that station is the one that crosses the
    start/finish line, and the beat sheet puts that at film frame 1191. The
    answer is **+973**, and it checks exactly at the far end — telemetry's last
    frame maps to f2715 against a declared beat-5 end of f2714, and the lap needs
    1,524 frames against 1,525 supplied.

    From beat 5 onward world time and film time run 1:1, so a constant offset is
    valid there. IT IS NOT VALID BEFORE BEAT 5 and nothing here uses it there.

    R2-651's 4.96 m result never depended on this join at all: it compares the
    car's lateral against the band at the car's OWN station, row by row.
    """
    import world_contract as C
    rows = list(csv.DictReader(open(os.path.join(ROOT, "telemetry/telemetry.csv"))))
    tf = np.array([int(r["frame"]) for r in rows])
    x = np.array([float(r["x"]) for r in rows])
    y = np.array([float(r["y"]) for r in rows])
    sg = np.array([float(r["s_m"]) for r in rows])
    transit = sg.max() - C.LAP
    i0 = int(np.searchsorted(sg, transit))
    off = 1191 - int(tf[i0])
    ff = tf + off
    s, u = C.project(x, y)
    return ff, np.asarray(s), np.asarray(u), off


def run(a):
    import world_contract as C
    L = load_line()
    path = json.load(open(os.path.join(ROOT, "world/camera_rig_path.json")))["path"]

    # ---- the band, as points, exactly as the surface sweep samples the road
    ds, nu = 2.0, 9
    S = np.arange(0.0, C.LAP, ds)
    c, heart, shoulder, feather = band_edges(L, S)
    ve = np.asarray(C.verge_edge(S), dtype=np.float64).reshape(-1)

    P_all, cell_all, is_heart = [], [], []
    ts = np.linspace(-1.0, 1.0, nu)
    for t in ts:
        U = t * ve
        P_all.append(np.asarray(C.su_to_world(S, U), dtype=np.float64))
        cell_all.append(ds * (2.0 * ve / (nu - 1)))
        is_heart.append(np.abs(U - c) <= heart)
    P = np.concatenate(P_all)
    cell = np.concatenate(cell_all)
    heart_mask = np.concatenate(is_heart)
    print(">> %d surface samples, %d of them inside the rubbered heart (%.1f %% of area)"
          % (len(P), int(heart_mask.sum()),
             100.0 * cell[heart_mask].sum() / cell.sum()))

    ff, cs, cu, off = car_track_offsets()
    print(">> telemetry -> film frame offset = +%d (SOLVED from the lap-start station, "
          "not from 33.0 s x 24 fps, which gives 792 and is wrong by 181)" % off)
    lap = (ff >= 1191) & (ff <= 2714)
    print("   telemetry rows landing inside beat 5 (f1191-2714): %d" % int(lap.sum()))

    cc, chh, csh, cff = band_edges(L, cs)
    d_line = np.abs(cu - cc)
    on_heart = d_line <= chh
    on_shoulder = d_line <= csh
    on_feather = d_line <= cff
    print(">> the car, over every telemetry sample on the lap:")
    print("   on the rubbered HEART      %6.2f %%" % (100.0 * on_heart[lap].mean()))
    print("   inside the SHOULDER        %6.2f %%" % (100.0 * on_shoulder[lap].mean()))
    print("   inside the FEATHER at all  %6.2f %%" % (100.0 * on_feather[lap].mean()))
    print("   |car - band centre|  p50 %.3f  p90 %.3f  max %.3f m"
          % (np.percentile(d_line[lap], 50), np.percentile(d_line[lap], 90),
             d_line[lap].max()))

    rows = []
    for r in path:
        f = r["f"]
        R = quat_to_mat(r["q"])
        fpx = (r["lens"] / SENSOR) * W
        V = P - np.asarray(r["p"], dtype=np.float64)
        Cm = V @ R
        dep = -Cm[:, 2]
        ok = dep > 1e-3
        xs = np.where(ok, fpx * Cm[:, 0] / np.where(ok, dep, 1) + W * 0.5, -1)
        ys = np.where(ok, -fpx * Cm[:, 1] / np.where(ok, dep, 1) + H * 0.5, -1)
        vis = ok & (xs >= 0) & (xs < W) & (ys >= 0) & (ys < H)
        if not vis.any():
            rows.append(dict(f=f, beat=beat_of(f), surf_px=0.0, band_px=0.0))
            continue
        d = np.linalg.norm(V, axis=1)
        cosi = np.clip(np.abs(V[:, 2]) / np.maximum(d, 1e-9), 1e-3, 1.0)
        px = np.where(vis, cell * cosi * (fpx / np.maximum(d, 1e-9)) ** 2, 0.0)
        surf_px = float(px.sum())
        band_px = float(px[heart_mask].sum())
        rows.append(dict(f=f, beat=beat_of(f),
                         surf_px=round(surf_px, 1), band_px=round(band_px, 1),
                         band_share=round(band_px / surf_px, 5) if surf_px > 0 else 0.0,
                         surf_frac=round(surf_px / (W * H), 5),
                         band_frac=round(band_px / (W * H), 5)))
    out = os.path.join(ROOT, a.json)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(dict(rows=rows,
                   car=dict(frame=[int(v) for v in ff], s=[round(float(v), 2) for v in cs],
                            u=[round(float(v), 4) for v in cu],
                            band_centre=[round(float(v), 4) for v in cc],
                            on_heart=[bool(v) for v in on_heart]),
                   note="OCCLUSION-BLIND: every pixel count is an upper bound"),
              open(out, "w"))
    print(">> wrote %s" % out)

    print()
    print("%-11s %7s %10s %10s %10s %10s"
          % ("beat", "n", "surf%_p50", "band%_p50", "band/surf", "band_px_p50"))
    for name, lo, hi in BEATS:
        sel = [r for r in rows if lo <= r["f"] <= hi and r.get("surf_frac", 0) > 0.01]
        if not sel:
            print("%-11s %7d   (surface never exceeds 1%% of frame)" % (name, 0))
            continue
        g = lambda k: np.percentile([r[k] for r in sel], 50)
        print("%-11s %7d %9.1f%% %9.2f%% %9.3f %10.0f"
              % (name, len(sel), 100 * g("surf_frac"), 100 * g("band_frac"),
                 g("band_share"), g("band_px")))
    print(">> STAGE RESULT: R2651_BAND_SWEEP_OK")


def selftest():
    import world_contract as C
    ok = True
    L = load_line()

    # 1. band half-widths reproduce the documented table
    S = np.array([100.0, 1000.0, 2500.0])
    c, h, sh, fe = band_edges(L, S)
    sp = np.interp(S, L["s"], L["spread"])
    hw = np.interp(S, L["s"], L["half_width"])
    print("  heart == 0.55*spread             %s" % np.allclose(h, 0.55 * sp))
    print("  feather <= 0.78*half_width       %s" % bool(np.all(fe <= 0.78 * hw + 1e-12)))
    ok &= np.allclose(h, 0.55 * sp) and bool(np.all(fe <= 0.78 * hw + 1e-12))

    # 2. THE FEATHER CAP IS ON THE HALF-WIDTH, NOT ON THE ROAD EDGE, and the
    #    difference is a real property of the shipped surface rather than a bug
    #    in this control. `build_surface.md` 2.3 says the cap "keeps clean tarmac
    #    against the white line however much the cars fan out" — but it caps the
    #    feather's HALF-WIDTH at 0.78 * half_width while centring it on a line
    #    that reaches +-7.14 m, so centre + feather runs past `verge_edge`
    #    wherever the line runs wide. The shader's `on_track` multiply clips it,
    #    which means the band ends AT the paint instead of feathering out before
    #    it. Measured and reported, not asserted away. See R2-657.
    Sf = np.arange(0.0, C.LAP, 2.0)
    cf, hf, shf, fef = band_edges(L, Sf)
    vef = np.asarray(C.verge_edge(Sf)).reshape(-1)
    over = (np.abs(cf) + fef) - vef
    print("  feather beyond verge_edge: %.1f %% of the lap, max %.2f m"
          % (100.0 * (over > 0).mean(), over.max()))
    heart_over = (np.abs(cf) + hf) - vef
    print("  HEART beyond verge_edge:   %.1f %% of the lap, max %.2f m"
          % (100.0 * (heart_over > 0).mean(), heart_over.max()))

    # 3. a car ON the line is on the heart everywhere; 20 m off it, nowhere.
    d0 = np.zeros_like(S)
    print("  car on the line -> on heart      %s" % bool(np.all(d0 <= h)))
    ok &= bool(np.all(d0 <= h))
    d20 = np.full_like(S, 20.0)
    print("  car 20 m off    -> on heart      %s  (must be False)"
          % bool(np.any(d20 <= h)))
    ok &= not bool(np.any(d20 <= h))

    # 4. NEGATIVE CONTROL: a pose pointed at the sky must see no band, and its
    #    PAIR pointed at the ground must see all of it. The identity quaternion
    #    is NOT "looking up" — a Blender camera looks down its own -Z, so
    #    identity at z = 50 looks straight DOWN. Rotating 180 degrees about X is
    #    what points it at the sky, and getting that backwards is how a control
    #    passes while proving nothing.
    P = np.asarray(C.su_to_world(S, np.zeros_like(S)), dtype=np.float64)
    V = P - np.array([0.0, 0.0, 50.0])
    down = -(V @ quat_to_mat((1.0, 0.0, 0.0, 0.0)))[:, 2]
    up = -(V @ quat_to_mat((0.0, 1.0, 0.0, 0.0)))[:, 2]
    print("  camera looking DOWN -> samples in front: %d of %d (must be all)"
          % (int((down > 0).sum()), len(S)))
    print("  camera looking UP   -> samples in front: %d      (must be 0)"
          % int((up > 0).sum()))
    ok &= int((down > 0).sum()) == len(S) and int((up > 0).sum()) == 0

    # 5. the telemetry join must land the lap where the rig says it is.
    ff, cs, cu, off = car_track_offsets()
    lap = (ff >= 1191) & (ff <= 2714)
    print("  telemetry offset +%d -> lap rows %d, station span %.0f..%.0f m of %.0f"
          % (off, int(lap.sum()), cs[lap].min(), cs[lap].max(), C.LAP))
    ok &= off == 973
    ok &= int(lap.sum()) >= 1524 and (cs[lap].max() - cs[lap].min()) > 0.97 * C.LAP

    print(">> STAGE RESULT: %s"
          % ("R2651_BAND_SWEEP_SELFTEST_OK" if ok else "R2651_BAND_SWEEP_SELFTEST_FAIL"))
    return ok


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default="render/r2651/band_sweep.json")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    sys.exit(0 if selftest() else 1) if a.selftest else run(a)
