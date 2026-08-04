"""R2-386 ABLATION READOUT — three raw world-time bakes, one table.

    python3 sim/carproxy_ablation.py sim/tmp/r2386/A0.npz sim/tmp/r2386/A1.npz ...

Reads the RAW export written by `build_breach_sim.export()` — `loc` (frames x
bodies x 3), `quat`, `names`, `world_t` — so the cells are compared on the
solver's own grid with no resampling in between.

For each cell it reports the three things the fix has to move and the two it
must not:

    MUST MOVE     `MUL05_S02` travel and peak speed          (the ride)
                  `GS_b05_00434` travel and peak speed       (the underfloor clamp)
                  transport distance inside the car envelope (the population)
    MUST NOT      the aperture, from each cell's own report
                  the untouched mullions, 0-4 and 6-10
"""

import json
import os
import sys

import numpy as np

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(R2, "sim"), os.path.join(R2, "anim")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import breachlib as BL                                            # noqa: E402
from carproxy_probe import to_car_local                            # noqa: E402
from carproxy_census import proxy_env                              # noqa: E402

WATCH = ("MUL05_S02", "GS_b05_00434", "MUL05_S00", "MUL05_S07")
CONTROL_PREFIX = tuple("MUL%02d" % u for u in
                       (0, 1, 2, 3, 4, 6, 7, 8, 9, 10))


# --------------------------------------------------------------------------- #
#  INTERPENETRATION — the price of withdrawing the collider
# --------------------------------------------------------------------------- #
#  If the proxy stops colliding, whatever was resting on it or wedged under it
#  is inside the car for as long as it takes the car to drive out from under
#  it, and the ONER camera is locked on the car at 6 to 13 m for all of beat 3.
#  So the fix has to be PRICED, not just claimed.
#
#  A point is inside a convex hull iff no direction separates it from the hull.
#  Testing a fixed fan of directions tests the intersection of that many slabs,
#  which CONTAINS the hull, so this over-counts.  That is the safe direction
#  for a cost: a fix that looks clean here is clean.
def _dirs(n=128):
    i = np.arange(n) + 0.5
    phi = np.arccos(1 - 2 * i / n)
    th = np.pi * (1 + 5 ** 0.5) * i
    return np.c_[np.cos(th) * np.sin(phi), np.sin(th) * np.sin(phi),
                 np.cos(phi)]


def inside_parts(L):
    """(N,3) car-local points -> bool (N,), inside ANY proxy part."""
    D = _dirs()
    out = np.zeros(len(L), bool)
    for _nm, P in BL.car_proxy_parts():
        P = np.asarray(P, float)
        lo, hi = P.min(0), P.max(0)
        cand = np.all((L >= lo - 1e-9) & (L <= hi + 1e-9), axis=1) & ~out
        if not cand.any():
            continue
        sup = (P @ D.T).max(axis=0)                    # (n_dirs,)
        q = L[cand] @ D.T                              # (n_cand, n_dirs)
        out[np.where(cand)[0]] = np.all(q <= sup + 1e-9, axis=1)
    return out


def cell(path):
    z = np.load(path, allow_pickle=True)
    loc, names, wt = z["loc"], [str(x) for x in z["names"]], z["world_t"]
    idx = {n: i for i, n in enumerate(names)}
    nf = len(wt)
    car = BL.Car()
    c_loc, c_rot = car.at_world_t(wt)
    dt = np.gradient(wt)

    rep_path = path.replace(".npz", ".json")
    rep = json.load(open(rep_path)) if os.path.exists(rep_path) else {}

    out = dict(cell=os.path.basename(path), frames=nf, bodies=len(names),
               car_proxy=rep.get("car_proxy"),
               aperture=rep.get("aperture"),
               thresholds=rep.get("thresholds"), watch={}, controls={})

    # interpenetration, per frame, over every body at once
    step = max(1, nf // 200)
    sample = list(range(0, nf, step))
    pen = np.zeros(nf, int)
    for fi in sample:
        L = to_car_local(loc[fi].astype(float),
                         np.repeat(c_loc[fi][None], len(names), 0),
                         np.repeat(c_rot[fi][None], len(names), 0))
        pen[fi] = int(inside_parts(L).sum())
    post = [f for f in sample if f >= 200]     # after the car is through
    out["interpenetration"] = dict(
        sampled_every=step,
        max_bodies_inside=int(pen.max()),
        at_sim_frame=int(pen.argmax()) + 1,
        at_last_frame=int(pen[sample[-1]]),
        mean_after_the_car_is_through=round(float(pen[post].mean()), 1),
        sampled_frames_over_100=int((pen[post] > 100).sum()),
        of_samples=len(post))

    lo, hi = proxy_env()
    tot_tr = 0.0
    n_cap = 0
    for j, nm in enumerate(names):
        p = loc[:, j, :].astype(float)
        L = to_car_local(p, c_loc, c_rot)
        ins = np.all((L > lo) & (L < hi), axis=1)
        seg = np.linalg.norm(np.diff(p, axis=0), axis=1)
        held = ins[:-1] & ins[1:]
        tr = float(seg[held].sum())
        tot_tr += tr
        if tr > 1.0:
            n_cap += 1
        if nm in WATCH:
            v = np.linalg.norm(np.gradient(p, axis=0) / dt[:, None], axis=1)
            d0 = np.linalg.norm(p - p[0], axis=1)
            mv = np.where(d0 > 0.05)[0]
            out["watch"][nm] = dict(
                travel_m=round(float(d0[-1]), 3),
                peak_speed=round(float(v.max()), 3),
                end_speed=round(float(v[-1]), 3),
                first_move_sim_frame=int(mv[0]) + 1 if len(mv) else None,
                transport_m=round(tr, 3),
                frames_held=int(held.sum()))
    out["transport_m_total"] = round(tot_tr, 1)
    out["bodies_carried_over_1m"] = n_cap

    # the untouched mullions: nothing may move
    worst = 0.0
    who = None
    for j, nm in enumerate(names):
        if nm.startswith(CONTROL_PREFIX):
            d = float(np.linalg.norm(loc[-1, j] - loc[0, j]))
            if d > worst:
                worst, who = d, nm
    out["controls"] = dict(untouched_mullion_max_travel_m=round(worst, 6),
                           worst=who)

    # the field at the last frame of the cell
    v_end = np.linalg.norm((loc[-1] - loc[-2]).astype(float) / dt[-1], axis=1)
    out["field_end"] = dict(
        over_1ms=int((v_end > 1.0).sum()), of=len(names),
        median=round(float(np.median(v_end)), 4),
        max=round(float(v_end.max()), 3),
        x_median=round(float(np.median(loc[-1, :, 0])), 3),
        x_max=round(float(loc[-1, :, 0].max()), 3))
    return out


def main():
    cells = [cell(p) for p in sys.argv[1:]]
    keys = [c["cell"] for c in cells]
    print("== R2-386 ablation, %d cells, %d frames each"
          % (len(cells), cells[0]["frames"]))
    for c in cells:
        print("   %-12s proxy=%s" % (c["cell"], json.dumps(c["car_proxy"])))

    def row(label, fn):
        print("   %-42s %s" % (label,
                               "  ".join("%14s" % fn(c) for c in cells)))

    print("   %-42s %s" % ("", "  ".join("%14s" % k[:14] for k in keys)))
    for nm in WATCH:
        for f, lab in (("travel_m", "travel m"), ("peak_speed", "peak m/s"),
                       ("transport_m", "transported m"),
                       ("frames_held", "sim frames held")):
            row("%s  %s" % (nm, lab),
                lambda c, nm=nm, f=f: c["watch"].get(nm, {}).get(f))
    row("TOTAL transport, all bodies (m)", lambda c: c["transport_m_total"])
    row("bodies carried > 1 m", lambda c: c["bodies_carried_over_1m"])
    row("field at last frame: over 1 m/s",
        lambda c: c["field_end"]["over_1ms"])
    row("field at last frame: median m/s",
        lambda c: c["field_end"]["median"])
    row("field at last frame: max x", lambda c: c["field_end"]["x_max"])
    row("PRICE bodies inside the car, worst frame",
        lambda c: c["interpenetration"]["max_bodies_inside"])
    row("PRICE   ... at that sim frame",
        lambda c: c["interpenetration"]["at_sim_frame"])
    row("PRICE mean inside, car through",
        lambda c: c["interpenetration"]["mean_after_the_car_is_through"])
    row("PRICE samples over 100 inside",
        lambda c: "%d of %d" % (c["interpenetration"]["sampled_frames_over_100"],
                                c["interpenetration"]["of_samples"]))
    row("CONTROL untouched mullions max m",
        lambda c: c["controls"]["untouched_mullion_max_travel_m"])
    row("aperture width m",
        lambda c: (c["aperture"] or {}).get("width_m"))
    row("aperture height m",
        lambda c: (c["aperture"] or {}).get("height_m"))
    row("shards gone", lambda c: (c["aperture"] or {}).get("gone"))
    row("glass mass gone kg",
        lambda c: round((c["aperture"] or {}).get("gone_mass_kg", 0), 1))

    with open(os.path.join(R2, "sim/out/r2386_ablation.json"), "w") as fh:
        json.dump(cells, fh, indent=1)
    print("   wrote sim/out/r2386_ablation.json")


if __name__ == "__main__":
    main()
