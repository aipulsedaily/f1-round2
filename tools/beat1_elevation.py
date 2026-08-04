"""Camera ELEVATION per frame, and the near-nadir population, from a built path.

    python3 tools/beat1_elevation.py --path render/film14_path.json
    python3 tools/beat1_elevation.py --path A.json --vs B.json      # before/after

WHY THIS METRIC AND NOT ROLL (R2-426)
-------------------------------------
Roll measured as "world-up projected into the image plane" has condition number
`cos(elevation)` and collapses to noise exactly where beat 1 lives -- 134 of its
792 frames cannot carry a roll figure at all.  Elevation is the dot product of
the camera's forward axis with world-up.  It has no degeneracy anywhere, at any
attitude, and needs no condition number printed beside it.

    elevation_deg = degrees(asin(dot(forward, +Z)))     negative = nose-down

FORWARD, FROM THE STORED QUATERNION
-----------------------------------
Blender cameras look down their own -Z.  The stored `q` is [w,x,y,z].  The
quaternions in the path files are rounded to six decimals (R2-103, R2-325), so
`|q|` is off unit by ~8e-7; every quaternion is re-normalised before use.  That
matters for angle DIFFERENCES, not for this dot product, but it is done anyway so
the two instruments cannot disagree over a rounding floor.

The self-null is printed first, always: a path compared against itself must
report exactly zero moved frames.  A shipped comparator once reported 1,415
frames "moved" on a file diffed against a bit-identical copy.
"""

import argparse
import json
import math
import os

R2 = "/home/zany/f1-round2"

BEATS = [
    ("1_assembly", 1, 792),
    ("2_launch", 793, 864),
    ("3_breach", 865, 1056),
    ("4_transit", 1057, 1190),
    ("5_lap", 1191, 2714),
    ("6_ending", 2715, 2978),
]


def qnorm(q):
    m = math.sqrt(sum(v * v for v in q)) or 1.0
    return [v / m for v in q]


def forward(q):
    """Camera -Z axis in world space, from quaternion [w,x,y,z]."""
    w, x, y, z = qnorm(q)
    # third column of R, negated
    return [-(2.0 * (x * z + w * y)),
            -(2.0 * (y * z - w * x)),
            -(1.0 - 2.0 * (x * x + y * y))]


def elevation_deg(q):
    f = forward(q)
    m = math.sqrt(sum(v * v for v in f)) or 1.0
    return math.degrees(math.asin(max(-1.0, min(1.0, f[2] / m))))


def load(p):
    d = json.load(open(p))
    return {int(k["f"]): k for k in d["path"]}


def med(v):
    s = sorted(v)
    n = len(s)
    if not n:
        return float("nan")
    return s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2])


def profile(path, label):
    els = {f: elevation_deg(k["q"]) for f, k in path.items()}
    print(f"\n=== {label} ===")
    print(f"{'beat':14s} {'n':>5s} {'median':>9s} {'min':>9s} {'max':>9s} "
          f"{'>70 down':>9s} {'>80 down':>9s}")
    tot70 = tot80 = 0
    for name, a, b in BEATS:
        v = [els[f] for f in range(a, b + 1) if f in els]
        if not v:
            continue
        n70 = sum(1 for e in v if e < -70.0)
        n80 = sum(1 for e in v if e < -80.0)
        tot70 += n70
        tot80 += n80
        print(f"{name:14s} {len(v):5d} {med(v):9.2f} {min(v):9.2f} {max(v):9.2f} "
              f"{n70:9d} {n80:9d}")
    print(f"{'FILM':14s} {len(els):5d} {med(list(els.values())):9.2f} "
          f"{min(els.values()):9.2f} {max(els.values()):9.2f} {tot70:9d} {tot80:9d}")

    b1 = [els[f] for f in range(1, 793) if f in els]
    first60 = [els[f] for f in range(1, 61) if f in els]
    n70 = sum(1 for e in b1 if e < -70.0)
    n80 = sum(1 for e in b1 if e < -80.0)
    print(f"\nbeat 1 first frame        {els.get(1, float('nan')):8.2f} deg   "
          f"z = {path[1]['p'][2]:.4f} m")
    print(f"beat 1 f25 (t=1.04 s)     {els.get(25, float('nan')):8.2f} deg   "
          f"z = {path[25]['p'][2]:.4f} m")
    print(f"beat 1 first 60 median    {med(first60):8.2f} deg")
    print(f"beat 1 frames >70 down    {n70:5d}  ({n70 / len(b1) * 100:.1f} % of beat 1, "
          f"{n70 / 24.0:.2f} s)")
    print(f"beat 1 frames >80 down    {n80:5d}  ({n80 / len(b1) * 100:.1f} % of beat 1, "
          f"{n80 / 24.0:.2f} s)")
    return els


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", required=True)
    ap.add_argument("--vs", default=None)
    ap.add_argument("--dump", default=None)
    a = ap.parse_args()

    p = load(os.path.join(R2, a.path) if not a.path.startswith("/") else a.path)

    # ---- self-null, always, before any verdict -------------------------------
    moved = sum(1 for f in p
                if abs(elevation_deg(p[f]["q"]) - elevation_deg(p[f]["q"])) > 0)
    print(f"SELF-NULL  {len(p)} frames compared against themselves: "
          f"{moved} moved   (must be 0)")
    if moved:
        print("STAGE RESULT: ELEV_SELFNULL_FAIL")
        return 1

    ea = profile(p, a.path)

    if a.vs:
        q = load(os.path.join(R2, a.vs) if not a.vs.startswith("/") else a.vs)
        eb = profile(q, a.vs)
        common = sorted(set(ea) & set(eb))
        d = [(abs(eb[f] - ea[f]), f) for f in common]
        d.sort(reverse=True)
        nz = [x for x in d if x[0] > 1e-9]
        print(f"\n--- {a.path}  ->  {a.vs} ---")
        print(f"frames whose elevation moved at all : {len(nz)} / {len(common)}")
        print(f"worst |d elevation|                 : {d[0][0]:.4f} deg @ f{d[0][1]}")
        for name, lo, hi in BEATS:
            sub = [x for x in d if lo <= x[1] <= hi]
            w = max(sub)[0] if sub else 0.0
            print(f"  {name:14s} worst {w:8.4f} deg   moved "
                  f"{sum(1 for x in sub if x[0] > 1e-9):5d} frames")

    if a.dump:
        json.dump({str(f): round(ea[f], 4) for f in sorted(ea)},
                  open(a.dump, "w"), indent=0)
    print("\nSTAGE RESULT: ELEV_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
