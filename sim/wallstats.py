"""WHAT THE EAST WALL DOES IN A DELIVERED FRAME, BY REGION, AND BEFORE vs AFTER.

    .venv/bin/python sim/wallstats.py --frame 2978 \
        --before render/r6_before/full_f2978.png \
        --after  render/r6_after/full_f2978.png \
        --out sim/out/wallstats_f2978.json

Regions are projected from `sim/out/oner_camera_track_film14_breach.json`, not
picked by eye, so the same rectangle is measured in both images and in every
frame.  `sim/wallproj.py` is the projector and it was validated against an
independent agent's report of the wound as 28.5 x 77.6 px at f2978.

THE CONTROLS, AND WHY EACH IS NOT DECORATION
============================================
CTL_UNTOUCHED   bays 7, 8 and 9 of the same wall.  The R6 fix cuts up mullions
                4/5/6 and the transoms between y +-4.3625 and does not touch a
                single vertex outside that band, so these bays are the same
                geometry in both builds.  They MUST be pixel-identical.  This
                is R2-150's free negative control, obtained here not by an
                occluder but by the fix's own blast radius -- same region, same
                two builds, no change, so it must not move.  A repair that
                "showed up" here as well would be light leaking from somewhere
                else, and no external control could tell that apart.
CTL_SKY         nothing in the scene can reach it.  Catches an exposure or
                tone-map difference that would make every other number move.
WOUND / NB_*    the claim and its two neighbours, which is the comparison the
                finding was written in: at f2978 the wound was +0.066 against
                the left neighbour and -0.124 against the right, i.e. NOT
                darker, because a transmissive wall is not darker than a hole.

AND THE MEASURE THAT MATTERS IS NOT THE MEAN.  `mean` reads the same for
"hole" and "glass" and that is the whole difficulty.  What separates a curtain
wall from an opening in one is the LATTICE: 1 px lines at known heights.  So
`grid_contrast` measures exactly that -- the amplitude of the frame's own
horizontal lines against the bay between them, at the three transom heights
the projector puts them at.  A wall whose transoms have gone reads LOW there
and a wall whose transoms are still standing reads high, whatever the mean does.
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(R2, "sim"))
import wallproj as PJ                                             # noqa: E402

# x = 15.0 rectangles on the east wall, in metres
REGIONS = [
    ("WOUND_bridged", (-2.185, 2.165), (0.0875, 6.0875)),
    ("WOUND_connected", (-2.185, -0.035), (0.0875, 6.0875)),
    ("NB_left_bay3", (-4.3625, -2.2375), (0.11, 6.09)),
    ("NB_right_bay6", (2.2375, 4.3625), (0.11, 6.09)),
    ("CTL_UNTOUCHED_bays789", (4.4375, 10.9625), (0.11, 6.09)),
    ("CTL_UNTOUCHED_bays012", (-10.9625, -4.4375), (0.11, 6.09)),
    # R2-296.  THE NEGATIVE CONTROL'S PREMISE EXPIRED WHEN THE FIX GOT BIGGER.
    #
    # `CTL_UNTOUCHED_bays012` is R2-150's free negative control and its premise
    # is stated in this file's own docstring: "the R6 fix cuts up mullions
    # 4/5/6 and the transoms between y +-4.3625 and does not touch a single
    # vertex outside that band".  That was TRUE of the R6 bake.  It is FALSE of
    # the R2-281 re-bake: at the derived transom threshold the solver also
    # releases mullion 7 and the transom over bays 2 and 7, so
    # `eastframe.plan()` deletes GW_Right_Mull_07 as well and partitions the
    # transom across bay 2 -- and bay 2 (y -6.6 .. -4.4) is INSIDE this
    # rectangle.
    #
    # So a 1.48 % reading here against a 0.00 % floor is the control working:
    # it is reporting that geometry inside it changed, and geometry inside it
    # did.  The repair is to state the premise that still holds rather than to
    # widen the limit.  Bays 0 and 1 are untouched by BOTH bakes.
    #
    # The old rectangle is KEPT, not replaced, so every number already
    # published through it stays reproducible.
    ("CTL_UNTOUCHED_bays01", (-10.9625, -6.6375), (0.11, 6.09)),
]
TRANSOM_Z = (1.350, 2.850, 4.350)


def lum(a):
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]


def load(p):
    im = Image.open(p).convert("RGB")
    return np.asarray(im, np.float64) / 255.0


def px_rect(frame, y, z, track):
    r = PJ.rect_px(frame, y[0], y[1], z[0], z[1], track=track)
    return (int(np.floor(r["u"][0])), int(np.ceil(r["u"][1])),
            int(np.floor(r["v"][0])), int(np.ceil(r["v"][1])))


def grid_contrast(L, frame, y, track):
    """HOW LOUD IS THE LATTICE, over this region's y span, at the three
    transom heights the projector puts the transoms on.

    Measured against a LOCAL baseline three to five pixels above and below,
    because the wall has a strong vertical brightness gradient in the closing
    shot (the lit floor and the plinth are behind the lower half of it) and a
    baseline taken half a metre away would be measuring that gradient instead.

    AND IT IS AN ABSOLUTE VALUE.  Measured on the delivered f2978: round 1's
    transoms are ~0.2 DARKER than the interior seen through the wound and
    LIGHTER than the crazed glass in some retained bays.  A signed contrast
    would cancel across the wall and report a lattice that is plainly there as
    nearly zero -- the same class of error as R2-181, where a welded slab's
    mean normal cancelled and the detector reported nothing.
    """
    out = {}
    for lvl, zc in enumerate(TRANSOM_Z):
        uv, _zc, _m = PJ.project(frame, np.array(
            [[15.0, y[0], zc], [15.0, y[1], zc]]), track)
        u0 = int(round(min(uv[0, 0], uv[1, 0])))
        u1 = int(round(max(uv[0, 0], uv[1, 0])))
        v = int(round(0.5 * (uv[0, 1] + uv[1, 1])))
        if u1 - u0 < 2 or not (6 < v < L.shape[0] - 6):
            continue
        line = float(L[v - 1:v + 2, u0:u1].mean())
        base = float(np.concatenate([L[v - 5:v - 2, u0:u1].ravel(),
                                     L[v + 3:v + 6, u0:u1].ravel()]).mean())
        out["transom_%d" % lvl] = dict(v=v, u=[u0, u1],
                                       line=round(line, 5),
                                       baseline=round(base, 5),
                                       signed=round(line - base, 5),
                                       contrast=round(abs(line - base), 5))
    vals = [d["contrast"] for d in out.values()]
    out["mean_contrast"] = round(float(np.mean(vals)), 5) if vals else None
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frame", type=int, required=True)
    ap.add_argument("--before", required=True)
    ap.add_argument("--after", default="")
    ap.add_argument("--repeat", default="", help="same build rendered twice; "
                                                 "the noise floor")
    ap.add_argument("--track", default=PJ.TRACK)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    track = PJ.load(a.track)
    A = load(a.before)
    B = load(a.after) if a.after else None
    Rp = load(a.repeat) if a.repeat else None
    if B is not None and B.shape != A.shape:
        raise SystemExit("STAGE RESULT: FAIL -- %s is %s, %s is %s"
                         % (a.before, A.shape, a.after, B.shape))
    LA, LB = lum(A), (lum(B) if B is not None else None)

    rep = dict(frame=a.frame, before=a.before, after=a.after,
               repeat=a.repeat, regions={}, sky={}, PASS=True, fails=[])

    for name, y, z in REGIONS:
        u0, u1, v0, v1 = px_rect(a.frame, y, z, track)
        sa = LA[v0:v1, u0:u1]
        d = dict(px=[u0, u1, v0, v1], n=int(sa.size),
                 before=dict(mean=round(float(sa.mean()), 5),
                             sd=round(float(sa.std()), 5)),
                 grid_before=grid_contrast(LA, a.frame, y, track))
        if LB is not None:
            sb = LB[v0:v1, u0:u1]
            diff = np.abs(A[v0:v1, u0:u1] - B[v0:v1, u0:u1]).max(axis=2)
            d["after"] = dict(mean=round(float(sb.mean()), 5),
                              sd=round(float(sb.std()), 5))
            d["grid_after"] = grid_contrast(LB, a.frame, y, track)
            d["changed_pct_gt_8_255"] = round(
                float(100.0 * (diff > 8 / 255.0).mean()), 4)
            d["changed_pct_gt_1_255"] = round(
                float(100.0 * (diff > 1 / 255.0).mean()), 4)
            d["mean_abs_diff_255"] = round(float(diff.mean() * 255), 4)
            d["max_abs_diff_255"] = round(float(diff.max() * 255), 4)
        if Rp is not None:
            # THE FLOOR IS NOT ZERO AND IT IS NOT SMALL.  Two renders of the
            # SAME build at f2978 differ on 2-14 % of the pixels of these
            # regions at a 1/255 threshold -- the wall is transmissive and
            # specular, adaptive sampling and the denoiser do not repeat, and
            # R2-150's 0.00 % repeat floor was measured on asphalt.  So the
            # verdict below is taken at 8/255 against the MEASURED floor at
            # 8/255, never against zero.
            dr = np.abs(A[v0:v1, u0:u1] - Rp[v0:v1, u0:u1]).max(axis=2)
            d["repeat_floor_pct_gt_1_255"] = round(
                float(100.0 * (dr > 1 / 255.0).mean()), 4)
            d["repeat_floor_pct_gt_8_255"] = round(
                float(100.0 * (dr > 8 / 255.0).mean()), 4)
            d["repeat_floor_mean_abs_255"] = round(float(dr.mean() * 255), 4)
        rep["regions"][name] = d

    # a patch of sky, well above the wall
    u0, u1, v0, v1 = 200, 900, 60, 400
    d = dict(px=[u0, u1, v0, v1],
             before_mean=round(float(LA[v0:v1, u0:u1].mean()), 5))
    if LB is not None:
        diff = np.abs(A[v0:v1, u0:u1] - B[v0:v1, u0:u1]).max(axis=2)
        d["changed_pct_gt_1_255"] = round(
            float(100.0 * (diff > 1 / 255.0).mean()), 4)
        d["changed_pct_gt_8_255"] = round(
            float(100.0 * (diff > 8 / 255.0).mean()), 4)
        d["max_abs_diff_255"] = round(float(diff.max() * 255), 4)
    rep["sky"] = d

    # ---- verdicts ----------------------------------------------------------
    if LB is not None:
        for ctl in ("CTL_UNTOUCHED_bays789", "CTL_UNTOUCHED_bays012",
                    "CTL_UNTOUCHED_bays01"):
            r = rep["regions"][ctl]
            v = r["changed_pct_gt_8_255"]
            fl = r.get("repeat_floor_pct_gt_8_255")
            # against the measured floor where there is one, and against a
            # flat 1 % otherwise.  Charging a control with a change the
            # renderer makes against ITSELF is how a good fix gets rejected.
            lim = max(3.0 * fl, 0.5) if fl is not None else 1.0
            r["control_limit_pct"] = round(lim, 4)
            if v > lim:
                rep["PASS"] = False
                rep["fails"].append(
                    "%s changed %.3f%% of pixels at 8/255 against a limit of "
                    "%.3f%% (repeat floor %s); the fix does not touch a vertex "
                    "in it, so it must not move" % (ctl, v, lim, fl))
        if rep["sky"].get("changed_pct_gt_8_255", 0) > 0.01:
            rep["PASS"] = False
            rep["fails"].append("the sky moved: this is a tone-map or "
                                "exposure difference, not a geometry one")

    with open(a.out, "w") as fh:
        json.dump(rep, fh, indent=1)
    print("STAGE RESULT: wallstats %s (%d fails) -> %s"
          % ("PASS" if rep["PASS"] else "FAIL", len(rep["fails"]), a.out))
    for f in rep["fails"]:
        print("   ", f)
    for k, v in rep["regions"].items():
        print("  %-24s mean %.4f sd %.4f  gridC %s%s"
              % (k, v["before"]["mean"], v["before"]["sd"],
                 v["grid_before"].get("mean_contrast"),
                 ("   -> after mean %.4f sd %.4f gridC %s  changed>1/255 %.3f%%"
                  % (v["after"]["mean"], v["after"]["sd"],
                     v["grid_after"].get("mean_contrast"),
                     v["changed_pct_gt_1_255"])) if "after" in v else ""))


main()
