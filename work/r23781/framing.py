#!/usr/bin/env python3
"""R2-3781 -- WHAT THE FILM ACTUALLY GIVES THE FOUR LAST ITEMS.

    python3 work/r23781/framing.py --out work/r23781/framing.json
    python3 work/r23781/framing.py --control

WHY THIS EXISTS
===============
`docs/item_manifest.json` and `work/r23721_item2/a9_film24_item_presence.json`
rank these four items by

    peak_unocc_sharp_px_4k  =  declared height_m  x  a HOST object's px/m

with `measured_as_self: false`.  That is a ranking signal.  It is NOT a detail
budget, and R2-634 / R2-3721 both say so in capitals.  This file measures the
px/m of the object that IS the item, at the frame the film actually shows it,
so that a feature's millimetres can be turned into pixels before anybody builds
it.

The projection is `tools/screen_presence.py`'s, imported rather than retyped
(R2-2990's rule: the constants and the quaternion convention come from the
instrument that produced the published numbers, or the two answers are not
comparable).

THE CONTROL
===========
`--control` damages the measurement in four ways that must each move the
answer, and refuses to certify an arm that does not move.  An arm that cannot
fail is not evidence.  Damages:

    no_frustum   drop the on-sensor test  -- geometry behind the camera scores
    no_depth     drop depth > 0.05        -- points at the lens score infinity
    no_smear     drop the shutter test    -- smeared frames score
    frozen_lens  pin lens to 35 mm        -- the "35 mm equivalent" fallacy

plus a NULL arm (no damage) which must reproduce the undamaged answer exactly.
"""
import os
import sys
import json
import argparse

import numpy as np

R2 = "/home/zany/f1-round2"
sys.path.insert(0, os.path.join(R2, "tools"))
import screen_presence as SP                                    # noqa: E402

PATH = os.path.join(R2, "render", "film25_path.json")
NPZ = os.path.join(R2, "work", "w2_0", "retier_a9", "world_points.npz")

# The objects that ARE the four items, and the hosts they are currently
# measured through.  Kept apart on purpose: the whole finding is the gap.
SUBJECTS = {
    "exterior_ground_apron":    ["ARCH_Paving_ApronPlatform"],
    "grandstand_debris_fence":  ["ARCH_Grandstand_00_OUEST", "ARCH_Grandstand_01_T15",
                                 "ARCH_Grandstand_02_OUEST", "ARCH_Grandstand_03_PRINCIPALE",
                                 "ARCH_Grandstand_04_EST", "ARCH_Grandstand_05_TEMPORAIRE",
                                 "ARCH_Grandstand_Towers", "ARCH_Grandstand_Terrace"],
    "podium_backdrop":          ["ARCH_Grandstand_Towers", "ARCH_Grandstand_Terrace"],
    "podium_structure":         ["ARCH_Grandstand_Towers", "ARCH_Grandstand_Terrace"],
}
RANKED_THROUGH = {
    "exterior_ground_apron":    ["ARCH_Paving_Forecourt", "ARCH_Paving_ApronPlatform"],
    "grandstand_debris_fence":  SUBJECTS["grandstand_debris_fence"],
    "podium_backdrop":          SUBJECTS["podium_backdrop"],
    "podium_structure":         SUBJECTS["podium_structure"],
}
DECLARED_H = {"exterior_ground_apron": 1.0, "grandstand_debris_fence": 3.6,
              "podium_backdrop": 4.0, "podium_structure": 3.5}


def load():
    C, Rm, s, lens, n = SP.camera_track(PATH)
    z = np.load(NPZ, allow_pickle=True)
    pts = z["pts"].astype(np.float64)
    obj = z["obj"]
    names = [str(x) for x in z["names"]]
    return C, Rm, s, lens, n, pts, obj, names


def sweep(C, Rm, s, lens, nframes, P, damage=""):
    """Per-frame px/m and depth for one point set.  Returns arrays over frames.

    R2-3781a: `dep` is the depth of the point that SET the px/m, not the median
    of everything in frame.  The first draft reported the median beside a
    minimum-depth px/m and the pair was unreadable -- 155.63 px/m 'at 178.02 m'
    on a 40 mm lens is arithmetically impossible, which is how the defect was
    caught.
    """
    ppm = np.zeros(nframes)
    dep = np.full(nframes, np.nan)
    cnt = np.zeros(nframes, dtype=int)
    if len(P) == 0:
        return ppm, dep, cnt
    for fi in range(nframes):
        Cf, Rf = C[fi], Rm[fi]
        sf = SP.RES_X * (35.0 if damage == "frozen_lens" else lens[fi]) / SP.SENSOR_MM
        D = P - Cf
        xc = D @ Rf[:, 0]
        yc = D @ Rf[:, 1]
        zc = D @ Rf[:, 2]
        depth = -zc
        ok = np.ones(len(P), dtype=bool) if damage == "no_depth" else depth > 0.05
        if not ok.any():
            continue
        d = np.where(ok, depth, np.nan)
        px = SP.RES_X / 2.0 + sf * xc / d
        py = SP.RES_Y / 2.0 + sf * yc / d
        if damage == "no_frustum":
            inf = ok
        else:
            inf = ok & (px >= 0) & (px < SP.RES_X) & (py >= 0) & (py < SP.RES_Y)
        if not inf.any():
            continue
        dd = depth[inf]
        cnt[fi] = int(inf.sum())
        # px/m at the CLOSEST in-frame point of this object on this frame,
        # and the depth OF THAT POINT.
        dmin = float(np.maximum(dd.min(), 1e-6))
        dep[fi] = dmin
        ppm[fi] = float(sf / dmin)
    return ppm, dep, cnt


SHEET = os.path.join(R2, "docs", "beat_sheet.json")


def smear_mask(C, Rm, lens, nframes, damage=""):
    """Frames where the camera's own angular rate keeps a static point sharp.

    The shutter is NOT retyped here.  `screen_presence.shutter_track` reads the
    beat sheet's own time map, and the whole point of importing the instrument
    is that this arm and the published table use the same one (R2-2990).
    """
    if damage == "no_smear":
        return np.ones(nframes, dtype=bool)
    shut, _ = SP.shutter_track(SHEET, nframes)
    fwd = -Rm[:, :, 2]
    d = np.zeros(nframes)
    for fi in range(nframes - 1):
        c = float(np.clip((fwd[fi] * fwd[fi + 1]).sum(), -1, 1))
        d[fi] = np.arccos(c)
    d[-1] = d[-2]
    s = SP.RES_X * lens / SP.SENSOR_MM
    smear_px = d * s * np.asarray(shut)
    return smear_px <= SP.SMEAR_SHARP_PX


def measure(damage=""):
    C, Rm, s, lens, n, pts, obj, names = load()
    sharp = smear_mask(C, Rm, lens, n, damage)
    idx = {nm: i for i, nm in enumerate(names)}
    out = {}
    for item, subs in SUBJECTS.items():
        rows = {}
        for group, objs in (("self", subs), ("ranked_through", RANKED_THROUGH[item])):
            sel = np.zeros(len(pts), dtype=bool)
            for o in objs:
                if o in idx:
                    sel |= (obj == idx[o])
            P = pts[sel]
            ppm, dep, cnt = sweep(C, Rm, s, lens, n, P, damage)
            live = (cnt > 0) & sharp
            if live.any():
                bf = int(np.argmax(np.where(live, ppm, -1)))
                rows[group] = dict(objects=objs, points=int(len(P)),
                                   frames_in_frustum=int((cnt > 0).sum()),
                                   frames_sharp_in_frustum=int(live.sum()),
                                   peak_px_per_m=round(float(ppm[bf]), 3),
                                   peak_frame=bf + 1,
                                   depth_at_peak_m=round(float(dep[bf]), 3),
                                   lens_at_peak_mm=round(float(lens[bf]), 3),
                                   mm_per_px=round(1000.0 / ppm[bf], 4))
            else:
                rows[group] = dict(objects=objs, points=int(len(P)),
                                   frames_in_frustum=int((cnt > 0).sum()),
                                   frames_sharp_in_frustum=0, peak_px_per_m=0.0)
        rows["declared_height_m"] = DECLARED_H[item]
        out[item] = rows
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="")
    ap.add_argument("--control", action="store_true")
    a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else None)

    base = measure()
    print("R2-3781  FRAMING -- the film's own resolution on the four last items")
    print("camera %s   points %s" % (os.path.relpath(PATH, R2), os.path.relpath(NPZ, R2)))
    print("")
    print("%-26s %-14s %9s %7s %9s %8s %9s" %
          ("item", "measured on", "px/m", "frame", "depth m", "lens mm", "mm/px"))
    for item, r in base.items():
        for group in ("self", "ranked_through"):
            g = r[group]
            if g["peak_px_per_m"] > 0:
                print("%-26s %-14s %9.2f %7d %9.2f %8.2f %9.4f" %
                      (item if group == "self" else "", group, g["peak_px_per_m"],
                       g["peak_frame"], g["depth_at_peak_m"], g["lens_at_peak_mm"],
                       g["mm_per_px"]))
            else:
                print("%-26s %-14s %9s  (never in frustum and sharp)" %
                      (item if group == "self" else "", group, "-"))
        s, h = r["self"], r["declared_height_m"]
        rk = r["ranked_through"]
        if s["peak_px_per_m"] > 0 and rk["peak_px_per_m"] > 0:
            print("%-26s %-14s ranked at %.1f px (h %.1f x %.2f); own geometry gives %.1f px  "
                  "-- overstated %.2fx" %
                  ("", "", h * rk["peak_px_per_m"], h, rk["peak_px_per_m"],
                   h * s["peak_px_per_m"], rk["peak_px_per_m"] / s["peak_px_per_m"]))
        print("")

    if a.out:
        json.dump(dict(camera=PATH, points=NPZ, items=base),
                  open(a.out, "w"), indent=1)
        print("wrote %s" % a.out)

    if not a.control:
        print(">> STAGE RESULT: R2_3781_FRAMING_OK")
        return 0

    print("")
    print("CONTROL -- each damage must MOVE the answer; an arm that cannot fail is not evidence")
    dead = []
    for dmg in ("", "no_frustum", "no_depth", "no_smear", "frozen_lens"):
        got = measure(dmg)
        moved, tot = 0, 0
        for item in base:
            for group in ("self", "ranked_through"):
                tot += 1
                if abs(got[item][group]["peak_px_per_m"] - base[item][group]["peak_px_per_m"]) > 1e-6:
                    moved += 1
        if dmg == "":
            ok = (moved == 0)
            print("  %-12s NULL, must NOT move   %2d/%2d moved   %s" %
                  ("(none)", moved, tot, "ok" if ok else "BROKEN"))
            if not ok:
                dead.append("null")
        else:
            ok = (moved > 0)
            print("  %-12s must move             %2d/%2d moved   %s" %
                  (dmg, moved, tot, "ok" if ok else "VACUOUS"))
            if not ok:
                dead.append(dmg)
    if dead:
        print(">> STAGE RESULT: R2_3781_FRAMING_CONTROL_BROKEN  [%s]" % ",".join(dead))
        return 1
    print(">> STAGE RESULT: R2_3781_FRAMING_CONTROL_OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
