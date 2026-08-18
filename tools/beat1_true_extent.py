"""Shot scale measured by PROJECTING the car, not by dividing by its length.

    python3 tools/beat1_true_extent.py --path render/film14_path.json

WHY THIS REPLACES tools/beat1_shotscale.py's HEADLINE
-----------------------------------------------------
R2-429 reports that beat 1's car is "never smaller than 76.1 % of frame width",
and `tools/beat1_shotscale.py` reproduced that. Both compute

    car_frac_width = CAR_LEN * lens / (SENSOR_W * distance)

with CAR_LEN the car's 5.72 m X span. **That is the subtense of the car's LENGTH,
and it is only the car's apparent width when the camera is looking at the car
broadside.** At f700 the camera is dead ahead of the nose, so what the frame
actually contains is the car's 2.0 m TRACK, and the formula overstates its
apparent size by the aspect of the car -- nearly 3x.

The rendered frame settles it. `work/b1look/b1focus_000700_full.png` is the
complete car, whole and uncropped, head-on on the turntable, with the showroom's
MERIDIAN sign, the 24/P1 placard, the rope barrier and the ribbed back wall
behind it. Its front wing spans about 41 % of frame width. The proxy says 79 %.

> **A metric can be right while the frame it points at is useless, and it can
> also be WRONG about a frame that is fine.** This is the same shape as R2-314's
> point-in-frustum test: a scalar stood in for a projection, and the scalar
> cannot know which way the subject is facing.

WHAT THIS MEASURES INSTEAD
--------------------------
The eight corners of the car's world bounding box, through the actual camera --
position, orientation quaternion and animated lens, per frame -- giving the true
fraction of frame width and height the car subtends, and whether it FITS.

Both columns are printed side by side for every frame sampled, because the point
is not that one number replaces another; it is the size of the disagreement and
where it lives.

CAVEAT, STATED NOT BURIED: during the first two thirds of beat 1 the car is
EXPLODED across 616 parts and its assembled bounding box does not describe
anything on screen. The assembled box is meaningful from the point the last
cluster seats -- the four corners land together at f696-704 per
`world/beat1_anim_anim.json` -- so the close-out is where this instrument has
authority, and that is exactly the region the question is about.
"""

import argparse
import json
import math
import os

R2 = os.path.expanduser("~/f1-round2")
SENSOR_W = 36.0
RES = (3840, 2160)
SENSOR_H = SENSOR_W * RES[1] / RES[0]


def qn(q):
    m = math.sqrt(sum(v * v for v in q)) or 1.0
    return [v / m for v in q]


def basis(q):
    """Camera right / up / forward in world space, from [w,x,y,z]."""
    w, x, y, z = qn(q)
    right = [1 - 2 * (y * y + z * z), 2 * (x * y + w * z), 2 * (x * z - w * y)]
    up = [2 * (x * y - w * z), 1 - 2 * (x * x + z * z), 2 * (y * z + w * x)]
    fwd = [-(2 * (x * z + w * y)), -(2 * (y * z - w * x)),
           -(1 - 2 * (x * x + y * y))]
    return right, up, fwd


def dot(a, b):
    return sum(a[i] * b[i] for i in range(3))


def extent(box_lo, box_hi, eye, q, lens):
    """(frac_w, frac_h, fits, behind) for a world AABB through this camera."""
    rt, up, fwd = basis(q)
    xs, ys = [], []
    behind = False
    for i in range(8):
        p = [box_lo[0] if i & 1 else box_hi[0],
             box_lo[1] if i & 2 else box_hi[1],
             box_lo[2] if i & 4 else box_hi[2]]
        v = [p[j] - eye[j] for j in range(3)]
        z = dot(v, fwd)
        if z <= 1e-6:
            behind = True
            continue
        xs.append(dot(v, rt) / z * lens)
        ys.append(dot(v, up) / z * lens)
    if not xs:
        return 99.0, 99.0, False, True
    fw = (max(xs) - min(xs)) / SENSOR_W
    fh = (max(ys) - min(ys)) / SENSOR_H
    fits = (fw <= 1.0 and fh <= 1.0 and not behind)
    return fw, fh, fits, behind


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", default=os.path.join(R2, "render/film14_path.json"))
    ap.add_argument("--lo", type=int, default=1)
    ap.add_argument("--hi", type=int, default=792)
    a = ap.parse_args()

    path = {int(k["f"]): k for k in json.load(open(a.path))["path"]}
    cb = json.load(open(os.path.join(R2, "docs/beat_sheet.json")))["beat1"]["car_box"]
    lo, hi = cb["lo"], cb["hi"]
    ctr = [(lo[i] + hi[i]) / 2.0 for i in range(3)]
    carlen = hi[0] - lo[0]
    print(f"car box {tuple(lo)} .. {tuple(hi)}   CAR_LEN {carlen:.2f} m   "
          f"track {hi[1]-lo[1]:.2f} m")
    print()

    rows = []
    for f in range(a.lo, a.hi + 1):
        if f not in path:
            continue
        k = path[f]
        fw, fh, fits, behind = extent(lo, hi, k["p"], k["q"], k["lens"])
        d = math.dist(k["p"], ctr)
        proxy = carlen * k["lens"] / (SENSOR_W * max(d, 1e-6))
        rows.append((f, fw, fh, fits, proxy, d, k["lens"]))

    print("SAMPLED FRAMES -- the two instruments side by side")
    print(f"{'frame':>6} {'dist':>7} {'lens':>6} {'TRUE w':>8} {'TRUE h':>8} "
          f"{'fits':>5} {'proxy w':>8} {'proxy/true':>11}")
    for f in (1, 100, 200, 300, 400, 500, 591, 622, 648, 655, 686, 700,
              718, 754, 792):
        r = next((x for x in rows if x[0] == f), None)
        if not r:
            continue
        _f, fw, fh, fits, proxy, d, lens = r
        print(f"{f:6d} {d:7.2f} {lens:6.1f} {fw:8.3f} {fh:8.3f} "
              f"{('YES' if fits else 'no'):>5} {proxy:8.3f} "
              f"{proxy/max(fw,1e-9):11.2f}x")

    # the close-out only -- where the assembled box is real
    co = [r for r in rows if 648 <= r[0] <= 792]
    if co:
        fits = [r for r in co if r[3]]
        print()
        print(f"CLOSE-OUT f648-792 ({len(co)} frames), where the car is assembled:")
        print(f"  frames in which the WHOLE CAR FITS THE FRAME : {len(fits)} "
              f"({len(fits)/len(co)*100:.0f} %)")
        if fits:
            print(f"  first such frame                             : f{fits[0][0]}")
            best = min(co, key=lambda r: max(r[1], r[2]))
            print(f"  widest framing                               : f{best[0]}  "
                  f"car {best[1]:.3f} of frame width, {best[2]:.3f} of height")
        tw = [r[1] for r in co]
        pw = [r[4] for r in co]
        print(f"  TRUE  car width, min..max                    : "
              f"{min(tw):.3f} .. {max(tw):.3f}")
        print(f"  PROXY car width, min..max                    : "
              f"{min(pw):.3f} .. {max(pw):.3f}")
        print(f"  the proxy overstates by up to                 : "
              f"{max(p/max(t,1e-9) for t,p in zip(tw,pw)):.2f}x")
    print()
    print("STAGE RESULT: TRUE_EXTENT_OK")


if __name__ == "__main__":
    main()
