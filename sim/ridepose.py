"""RIDEPOSE — the acceptance test for the deck ride, as R2-700 states it.

    .venv/bin/python sim/ridepose.py --table sim/out/breach_film_R2387.npz \
        --tag R2387 --json sim/out/ridepose_R2387.json

WHY THIS IS NOT A COUNT AND NOT A DISTANCE
==========================================
R2-700: two corrected bakes put the SAME EIGHT frame members on the car at
f0972 and read completely differently -- one alongside the cockpit reads as an
accident, one across the roof reads as broken.  Member count cannot separate
accept from reject and never could.  Neither can travel distance: the 55 m
slide everyone argued about subtends **11 px** on screen and the ride subtends
**1,879 px**.

The criterion the eye applies, and the only one this module implements:

    debris travelling alongside, tumbling or trailing is fine and desirable;
    something lying flat across the bodywork WITH NO RELATIVE MOTION is what
    reads as broken.

So the measurement is a POSE HISTORY, in three parts, per structural member:

  1. IS IT ABOARD -- car-local position over the car's plan and above the deck.
     "Above the deck" is car-local z > 0.55, the same definition the phase
     decomposition in R2-4xx used, so this number is comparable with that one.
     NOTE it is deliberately NOT `carproxy_census`'s envelope, whose upper bound
     is car-local z = 1.112 m while the ride happens at z 0.95-1.69 -- that
     bound is why the census reported `MUL05_S02 transported 0.0 m` for a body
     that was riding (R2-4xx, the instrument lesson).

  2. IS IT STILL RELATIVE TO THE CAR -- and measured IN PIXELS, because the eye
     is judging a picture.  Per film frame, the body's actual screen position
     is compared with where it would have been had it been WELDED to the car
     since the previous frame:

         rel_px(f) = |proj_f(p(f)) - proj_f(c(f) + R(f) . q(f-1))|

     where q is the body's position in the car's own frame.  A member locked to
     the bodywork scores ~0 px however fast the car is travelling; a member
     tumbling alongside scores tens of pixels.  Absolute screen motion is
     reported beside it, because it is the contrast between the two that reads
     as "at rest in a shot where everything else is smeared".

     THE HEADLINE STATISTIC IS THAT CONTRAST AS A RATIO: `rel_px / abs_px`, the
     share of a member's on-screen movement that is ITS OWN rather than the
     car's.  0 is welded to the bodywork; ~1 is a body the car is simply driving
     away from.  The verdict is taken on this and not on a run length, for a
     measured reason -- see below.

  3. IS IT LYING ACROSS OR TRAVELLING ALONGSIDE -- the member's own long axis,
     taken from its INTACT REST POSE in the wall (mullions are vertical, so the
     long axis is whatever the rest quaternion maps world +z from), expressed in
     the car's frame.  |axis . y_car| near 1 is a bar lying transversely across
     the car; near 0 is a bar pointing the way the car is going.

VERDICT.  A member FAILS if it is aboard and its median own-motion ratio over
the window is under `--ratio` (0.25).  It is reported over a sweep, because a
gate whose verdict flips with its threshold has not measured anything.

WHY NOT THE OBVIOUS READING -- "near-static for N frames"
---------------------------------------------------------
That form is implemented too (`longest_still_run`) and it is REPORTED BUT NOT
GATED ON, because it inverts when the window moves:

  members with a still run >= 12 frames at 3 px   f900-f1060  f940-f1060  f967-f977
    R2281 RE-BAKE   (the eye ACCEPTS this one)          6           0          0
    R2387 AIR       (the eye REJECTS this one)          2           2          0

On the widest window the accepted bake fails harder than the rejected one, and
on the narrowest neither fails at all.  A run length is a bounded measure
reporting confidently about its bound -- the same shape of error as
`carproxy_census`'s z-ceiling (R2-4xx).  The ratio does not move:

  lowest own-motion ratio of any member aboard    f900-f1060  f940-f1060  f967-f977
    R2281 RE-BAKE                                    0.304       0.337      0.378
    R2387 AIR                                        0.125       0.076      0.110
    R6 SHIPPED                                    no member is ever aboard

Three windows, a factor of three in every one of them, the same ordering the eye
gave, and an empty gap from 0.19 to 0.30 for the threshold to sit in.  0.25 is
the middle of that gap and is not fitted to anything finer.

WINDOW.  Default f0940-f1060, which contains the peak f0967-f0977 where five
structural members subtend 614-1,879 px at 2.4-3.6 m from the lens.  One frame
cannot judge this beat (R2-700's structural warning) and this module refuses to
report a single frame's population as a verdict.

THE HOLE IN THIS GATE, STATED SO IT CANNOT BE FORGOTTEN.  R6 SHIPPED passes it
perfectly, and R6 is the broken one: its thresholds were 29.5x too strong, its
frame never failed, and nothing can come to rest on a car that nothing comes off.
**This test is only meaningful beside a count of what came off the wall**, which
is why `n_aboard` is printed next to every verdict and why a bake with zero
members aboard is reported as VACUOUS rather than as a pass.
"""

import argparse
import json
import os
import sys

import numpy as np

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(R2, "sim"), os.path.join(R2, "anim")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import breachlib as BL                                            # noqa: E402
import resample as RS                                             # noqa: E402
import sagpx as SG                                                # noqa: E402

# the car's plan, from the proxy's own extents plus a margin for a body whose
# ORIGIN is outboard of the bodywork while the bar itself lies over it
PLAN_X = (BL.TAIL_DX - 0.40, BL.NOSE_DX + 0.40)
PLAN_Y = 1.20
DECK_Z = (0.55, 3.00)


def _rotmats(eul):
    """(N,3) XYZ euler -> (N,3,3), the same convention as carproxy_probe."""
    cx, cy, cz = np.cos(eul).T
    sx, sy, sz = np.sin(eul).T
    n = len(eul)
    R = np.empty((n, 3, 3))
    R[:, 0, 0] = cy * cz
    R[:, 0, 1] = cz * sx * sy - cx * sz
    R[:, 0, 2] = cx * cz * sy + sx * sz
    R[:, 1, 0] = cy * sz
    R[:, 1, 1] = cx * cz + sx * sy * sz
    R[:, 1, 2] = -cz * sx + cx * sy * sz
    R[:, 2, 0] = -sy
    R[:, 2, 1] = cy * sx
    R[:, 2, 2] = cx * cy
    return R


def _quat_R(q):
    """(N,4) WXYZ -> (N,3,3)."""
    return SG._rot(np.asarray(q, float))


def longest_run(mask):
    """(length, start_index) of the longest True run."""
    best = cur = b0 = c0 = 0
    for k, f in enumerate(mask):
        if f:
            if cur == 0:
                c0 = k
            cur += 1
            if cur > best:
                best, b0 = cur, c0
        else:
            cur = 0
    return best, b0


def analyse(table, frames, track, still_px=3.0, still_frames=12, ratio=0.25,
            sweep=(0.5, 1.0, 2.0, 3.0, 5.0, 10.0)):
    T = RS.read_film(table)
    names = T["names"]
    keep = [j for j, n in enumerate(names) if not n.startswith("GS_")]
    car = BL.Car()

    # one extra frame at the front: every rate here is a backward difference
    fr = np.concatenate([[frames[0] - 1], frames]).astype(float)
    L, Q = T["expand"](fr)
    L, Q = L[:, keep], Q[:, keep]
    kn = [names[j] for j in keep]

    # the rest pose, for the member's own long axis
    f_rest = float(T["span"][0])
    _, Qr = T["expand"](np.array([f_rest]))
    Rr = _quat_R(Qr[0, keep])
    # a mullion is vertical in the wall and a transom is horizontal-and-across;
    # either way the bar's long axis is the world axis its REST orientation is
    # aligned to, so read it off the rest rotation rather than assuming.
    axis_local = np.empty((len(kn), 3))
    for i, n in enumerate(kn):
        w = np.array([0.0, 0.0, 1.0]) if n.startswith("MUL") \
            else np.array([0.0, 1.0, 0.0])
        axis_local[i] = Rr[i].T @ w

    wt = np.array([BL.Clock().world_t(f) for f in fr], float)
    c_loc, c_eul = car.at_world_t(wt)
    Rc = _rotmats(c_eul)

    nF, nB = len(fr), len(kn)
    q = np.einsum("fij,fbi->fbj", Rc, L - c_loc[:, None, :])      # car-local
    aboard = ((q[:, :, 0] > PLAN_X[0]) & (q[:, :, 0] < PLAN_X[1])
              & (np.abs(q[:, :, 1]) < PLAN_Y)
              & (q[:, :, 2] > DECK_Z[0]) & (q[:, :, 2] < DECK_Z[1]))

    # where it would be if it had been WELDED to the car since the frame before
    weld = c_loc[1:, None, :] + np.einsum("fij,fbj->fbi", Rc[1:],
                                          q[:-1])
    rel_px = np.zeros((nF - 1, nB))
    abs_px = np.zeros((nF - 1, nB))
    in_ras = np.zeros((nF - 1, nB), bool)
    depth = np.zeros((nF - 1, nB))
    for k in range(nF - 1):
        i = int(fr[k + 1]) - 1
        if i < 0 or i >= len(track["frame"]):
            continue
        ax, ay, dp, oka = SG.project(track, i, L[k + 1])
        bx, by, _, okb = SG.project(track, i, weld[k])
        cx, cy, _, okc = SG.project(track, i, L[k])
        rel_px[k] = np.hypot(ax - bx, ay - by)
        abs_px[k] = np.hypot(ax - cx, ay - cy)
        in_ras[k] = oka & okb
        depth[k] = dp

    # the member's long axis in the car's frame
    ax_w = np.einsum("fbij,bj->fbi", _quat_R(Q.reshape(-1, 4)).reshape(
        nF, nB, 3, 3), axis_local)
    ax_c = np.einsum("fij,fbi->fbj", Rc, ax_w)
    across = np.abs(ax_c[:, :, 1])                    # 1 = lying transversely

    ab = aboard[1:]
    # the own-motion ratio is only meaningful where the member is on screen AND
    # the screen is actually moving: at abs_px under a pixel the quotient is
    # noise over noise, so those frames are dropped rather than averaged in.
    usable = ab & in_ras & (abs_px > 1.0)
    out = dict(table=os.path.basename(table), n_bodies=nB,
               frames=[int(frames[0]), int(frames[-1])],
               still_px=still_px, still_frames=still_frames, ratio=ratio,
               bodies=[])
    worst = None
    for b in range(nB):
        m_still = ab[:, b] & (rel_px[:, b] < still_px) & in_ras[:, b]
        run, s0 = longest_run(m_still)
        rec = dict(
            name=kn[b],
            frames_aboard=int(ab[:, b].sum()),
            longest_still_run=int(run),
            run_films=[float(frames[s0]), float(frames[s0 + run - 1])]
            if run else None,
            sweep={("%.1f" % t): int(longest_run(
                ab[:, b] & (rel_px[:, b] < t) & in_ras[:, b])[0])
                for t in sweep})
        if run:
            sl = slice(s0, s0 + run)
            rec.update(
                run_rel_px_mean=float(rel_px[sl, b].mean()),
                run_rel_px_max=float(rel_px[sl, b].max()),
                run_abs_px_mean=float(abs_px[sl, b].mean()),
                run_depth_m=float(depth[sl, b].mean()),
                run_carlocal=[float(q[1:][sl, b, i].mean()) for i in range(3)],
                run_across=float(across[1:][sl, b].mean()))
        if ab[:, b].any():
            sl = ab[:, b]
            rec.update(
                aboard_rel_px_median=float(np.median(rel_px[sl, b])),
                aboard_abs_px_median=float(np.median(abs_px[sl, b])),
                aboard_carlocal_z=float(q[1:][sl, b, 2].mean()),
                aboard_across=float(across[1:][sl, b].mean()))
        u = usable[:, b]
        if u.sum() >= 6:
            rec["own_motion_ratio"] = float(
                np.median(rel_px[u, b] / abs_px[u, b]))
            rec["ratio_frames"] = int(u.sum())
        out["bodies"].append(rec)
        if run >= (worst["longest_still_run"] if worst else 1):
            if rec["frames_aboard"]:
                worst = rec
    out["worst"] = worst
    out["n_aboard"] = int(sum(1 for r in out["bodies"] if r["frames_aboard"]))
    rated = [r for r in out["bodies"] if r.get("own_motion_ratio") is not None]
    carried = [r for r in rated if r["own_motion_ratio"] < ratio]
    out["n_rated"] = len(rated)
    out["n_carried"] = len(carried)
    out["min_ratio"] = min([r["own_motion_ratio"] for r in rated], default=None)
    out["carried"] = sorted(carried, key=lambda r: r["own_motion_ratio"])
    # a run-length verdict is kept for the record and NOT used: see the module
    # docstring for the three windows in which it inverts.
    out["n_still_runs"] = int(sum(1 for r in out["bodies"]
                                  if r["longest_still_run"] >= still_frames))
    if out["n_aboard"] == 0:
        out["PASS"] = None
        out["VERDICT"] = "VACUOUS"      # nothing came off the wall to judge
    else:
        out["PASS"] = out["n_carried"] == 0
        out["VERDICT"] = "PASS" if out["PASS"] else "FAIL"
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--table", required=True)
    ap.add_argument("--tag", default=None)
    ap.add_argument("--f0", type=int, default=940)
    ap.add_argument("--f1", type=int, default=1060)
    ap.add_argument("--still-px", type=float, default=3.0)
    ap.add_argument("--still-frames", type=int, default=12)
    ap.add_argument("--ratio", type=float, default=0.25,
                    help="a member whose own-motion ratio is BELOW this, while "
                         "aboard, is being carried rather than travelling")
    ap.add_argument("--track", default=SG.TRACK)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()

    tag = a.tag or os.path.basename(a.table)
    frames = np.arange(a.f0, a.f1 + 1)
    r = analyse(a.table, frames, SG.load_track(a.track),
                still_px=a.still_px, still_frames=a.still_frames,
                ratio=a.ratio)
    r["tag"] = tag
    r["track"] = a.track

    print("== %s   %s   f%d-f%d" % (tag, r["table"], a.f0, a.f1))
    print("   structural bodies %d, of which ABOARD at some frame: %d"
          % (r["n_bodies"], r["n_aboard"]))
    print("   still = under %.1f px/frame relative to the car, while aboard"
          % a.still_px)
    rows = sorted([b for b in r["bodies"] if b.get("own_motion_ratio")
                   is not None], key=lambda b: b["own_motion_ratio"])[:12]
    print("   %-14s %7s %6s %6s %8s %8s %7s %6s"
          % ("body", "aboard", "OWN", "still", "rel_px", "abs_px", "z",
             "across"))
    for b in rows:
        print("   %-14s %7d %6.3f %6d %8.2f %8.0f %7.2f %6.2f"
              % (b["name"], b["frames_aboard"], b["own_motion_ratio"],
                 b["longest_still_run"],
                 b.get("aboard_rel_px_median", 0.0),
                 b.get("aboard_abs_px_median", 0.0),
                 b.get("aboard_carlocal_z", 0.0), b.get("aboard_across", 0.0)))
    if r["worst"]:
        print("   still-run sweep (px -> longest run) for %s: %s   [REPORTED, "
              "NOT GATED ON -- it inverts with the window]"
              % (r["worst"]["name"], json.dumps(r["worst"]["sweep"])))
    print("   lowest own-motion ratio %s   carried (< %.2f): %d of %d rated"
          % ("%.3f" % r["min_ratio"] if r["min_ratio"] is not None else "n/a",
             a.ratio, r["n_carried"], r["n_rated"]))
    if r["VERDICT"] == "VACUOUS":
        print("   NO MEMBER IS EVER ABOARD.  This gate cannot fail such a bake "
              "and must not be read as passing it: nothing comes to rest on a "
              "car that nothing comes off (R2-700).")
    print(">> STAGE RESULT: RIDEPOSE_%s %s (aboard %d)"
          % (tag, r["VERDICT"], r["n_aboard"]))
    if a.json:
        with open(a.json, "w") as fh:
            json.dump(r, fh, indent=1, default=float)
        print("wrote %s" % a.json)


if __name__ == "__main__":
    main()
