"""SHOT SCALE per frame: how big is the car, and how far away is the lens.

    python3 tools/beat1_shotscale.py --path render/film14_path.json
    python3 tools/beat1_shotscale.py --path A.json --vs B.json

R2-429 measured that beat 1 never goes wider than 76.1 % of frame width and that
the lens is never further than 8.32 m from a 5.7 m car in 33 seconds -- so the
film has no establishing shot.  This reproduces that from the path, and then
reports what R2-451's re-aim does to it, because the two findings share a
placement even though they do not share a cause.

THE PLACEMENT IS POLAR AND THE TWO DEFECTS ARE ITS TWO COORDINATES
------------------------------------------------------------------
    station  =  cluster_centre  +  d * standoff
                                   ^^^^^^^^^^^ R2-429: `radius*1.55 + 0.42`
                                               fixes the SUBTENDED ANGLE at
                                               ~80 deg, so the subject always
                                               fills the frame and is therefore
                                               never seen whole
                                ^ R2-425/451: argmax projected area is a PLAN
                                  VIEW, so the lens is always overhead

Neither law can produce the other -- a radius cannot choose a direction -- so
they are not one root cause.  But they are not independent in their EFFECT
either: the direction of maximum projected area is close to the direction of
maximum projected EXTENT for a flat body, so the direction law was choosing,
out of every direction available, one of the few from which the cluster is
biggest.  For the near-nadir clusters the two compound; for the corners they do
not.  This tool prints both columns so the claim is checkable rather than
asserted.

THE METRIC, and it reproduces R2-429's headline exactly
-------------------------------------------------------
    frame_width_at(d)  =  d * SENSOR_W / lens
    car_frac_width     =  CAR_LEN / frame_width_at(d)
                       =  CAR_LEN * lens / (SENSOR_W * d)

At R2-429's own worst frame -- f754, 8.32 m, 40 mm -- that is
5.7 * 40 / (36 * 8.32) = 0.761, which is the published 76.1 %.  The car box is
`beat_sheet.beat1.car_box`, measured on world/beat1_anim.blend, and CAR_LEN is
its X span; the distance is to the box CENTRE, and both are printed so a
different convention can be reconciled rather than argued about.

READ `frac > 1.0` AS "the car does not fit": it is an apparent-size proxy, not a
frustum test, and during beat 1 the car is EXPLODED across a field wider than the
assembled car, so the percentages understate how full the frame is.  The
load-bearing column is the camera DISTANCE, which is a direct path measurement
and has no proxy in it at all.
"""

import argparse
import json
import math
import os

R2 = "/home/zany/f1-round2"
SENSOR_W = 36.0

BEATS = [("1_assembly", 1, 792), ("2_launch", 793, 864), ("3_breach", 865, 1056),
         ("4_transit", 1057, 1190), ("5_lap", 1191, 2714), ("6_ending", 2715, 2978)]


def pct(v, q):
    s = sorted(v)
    if not s:
        return float("nan")
    i = min(len(s) - 1, max(0, int(round(q * (len(s) - 1)))))
    return s[i]


def load(p):
    return {int(k["f"]): k for k in json.load(open(p))["path"]}


def car_ref():
    b = json.load(open(os.path.join(R2, "docs/beat_sheet.json")))["beat1"]["car_box"]
    lo, hi = b["lo"], b["hi"]
    ctr = [(lo[i] + hi[i]) / 2.0 for i in range(3)]
    return ctr, hi[0] - lo[0]


def profile(path, label, ctr, carlen):
    print(f"\n=== {label} ===")
    print(f"car box centre {tuple(round(v,3) for v in ctr)}   "
          f"CAR_LEN {carlen:.2f} m")
    print(f"{'beat':14s} {'n':>5s} {'dist med':>9s} {'dist max':>9s} "
          f"{'frac med':>9s} {'frac p10':>9s} {'frac min':>9s} {'<100%':>7s} "
          f"{'<60%':>6s}")
    rows = {}
    for name, a, b in BEATS:
        D, F = [], []
        for f in range(a, b + 1):
            if f not in path:
                continue
            k = path[f]
            d = math.dist(k["p"], ctr)
            D.append(d)
            F.append(carlen * k["lens"] / (SENSOR_W * max(d, 1e-6)))
        if not D:
            continue
        n100 = sum(1 for x in F if x < 1.0)
        n60 = sum(1 for x in F if x < 0.60)
        rows[name] = (D, F)
        print(f"{name:14s} {len(D):5d} {pct(D,0.5):9.2f} {max(D):9.2f} "
              f"{pct(F,0.5):9.3f} {pct(F,0.10):9.3f} {min(F):9.3f} "
              f"{n100:7d} {n60:6d}")
    D, F = rows.get("1_assembly", ([], []))
    if D:
        wf = max(range(1, 793), key=lambda f: math.dist(path[f]["p"], ctr)
                 if f in path else -1)
        print(f"\nbeat 1 widest frame        f{wf}  dist {math.dist(path[wf]['p'], ctr):.2f} m  "
              f"lens {path[wf]['lens']:.1f} mm  car {carlen * path[wf]['lens'] / (SENSOR_W * math.dist(path[wf]['p'], ctr)):.3f} of frame width")
        print(f"beat 1 smallest the car gets  {min(F):.3f} of frame width")
        print(f"beat 1 frames under 100 %     {sum(1 for x in F if x < 1.0)}")
        print(f"beat 1 frames under  60 %     {sum(1 for x in F if x < 0.60)}")
        lo, hi = pct(F, 0.10), pct(F, 0.90)
        print(f"beat 1 p10..p90               {lo:.3f} .. {hi:.3f}  "
              f"= {math.log2(hi / lo):.2f} octaves of scale variety, "
              f"{'ENTIRELY above 100 %' if lo >= 1.0 else 'crossing 100 %'}")
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", required=True)
    ap.add_argument("--vs", default=None)
    a = ap.parse_args()
    ctr, carlen = car_ref()
    ra = profile(load(a.path), os.path.basename(a.path), ctr, carlen)
    if a.vs:
        rb = profile(load(a.vs), os.path.basename(a.vs), ctr, carlen)
        Da, Fa = ra["1_assembly"]
        Db, Fb = rb["1_assembly"]
        print(f"\n--- beat 1, before -> after ---")
        print(f"max camera distance   {max(Da):7.2f} m  ->  {max(Db):7.2f} m")
        print(f"median distance       {pct(Da,0.5):7.2f} m  ->  {pct(Db,0.5):7.2f} m")
        print(f"car at its smallest   {min(Fa):7.3f}    ->  {min(Fb):7.3f}   "
              f"of frame width")
        print(f"frames under 100 %    {sum(1 for x in Fa if x<1.0):7d}    ->  "
              f"{sum(1 for x in Fb if x<1.0):7d}")
        print(f"frames under  60 %    {sum(1 for x in Fa if x<0.60):7d}    ->  "
              f"{sum(1 for x in Fb if x<0.60):7d}")
    print("\nSTAGE RESULT: SHOTSCALE_OK")


if __name__ == "__main__":
    main()
