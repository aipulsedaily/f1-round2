"""THE SEAMS — the one-take law, measured on both sides of every join.

    python3 sim/seams.py --table sim/out/breach_film.npz --label AFTER

There are two kinds of seam in this film and this script measures both with the
same code, so a BEFORE and an AFTER column are comparable by construction.

THE CAR'S SEAMS (beat 2 | beat 3 | beat 4)
==========================================
`docs/beat_sheet.json` joins beat 2 to beat 3 at t = 36.0 s (film f865) and
beat 3 to beat 4 at t = 44.0 s (film f1057).  The car's transform is READ from
`world/car_anim_measured.json`; the breach sim consumes it and emits nothing
that touches it.  So this arm exists to PROVE that rather than to assert it: it
hashes the measured table, prints the car's pose and speed on both sides of
both joins, and reports the largest per-frame acceleration anywhere near them.
If a fix ever does move the car, this is the column that shows it.

THE TABLE'S SEAMS (release, and the last key)
=============================================
`apply_breach.py` keys the table and extrapolates CONSTANT on both sides.

  RELEASE SEAM   a body's first key must be where the static wall already has
                 it, or the body pops on the frame it is released.
  LAST-KEY SEAM  past f1165 every body holds its pose for 1,813 frames.  A body
                 that is still moving when the keys run out stops dead.
                 `sim/rest_gate.py` owns the visibility question; this measures
                 the discontinuity itself, and WHERE the frozen field lands in
                 the closing frame, which is the thing R2-290 priced at
                 two-thirds of the frame width.

Nothing here writes.  It reads a table and prints two blocks.
"""

import argparse
import hashlib
import json
import os
import sys

import numpy as np

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(R2, "sim"), os.path.join(R2, "anim")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import breachlib as BL                                            # noqa: E402
import sagpx                                                       # noqa: E402
from carproxy_probe import load, track                             # noqa: E402

SEAMS = ((865, "beat 2 | beat 3  (t = 36.0 s, IMPACT)"),
         (1057, "beat 3 | beat 4  (t = 44.0 s)"))
CLOSING_FRAME = 2978


def car_arm():
    car, clock = BL.Car(), BL.Clock()
    h = hashlib.sha256()
    h.update(np.ascontiguousarray(car.loc, np.float64).tobytes())
    h.update(np.ascontiguousarray(car.rot, np.float64).tobytes())
    out = dict(measured=os.path.basename(BL.CAR_JSON),
               frames=car.n, sha256=h.hexdigest()[:16], seams=[])
    # per-FILM-frame speed, in WORLD time: the ramp is a sampling operation and
    # differencing on film frames would report it as a deceleration.
    wt = np.array([clock.world_t(float(f)) for f in range(1, car.n + 1)])
    dv = np.gradient(car.loc, axis=0) / np.gradient(wt)[:, None]
    sp = np.linalg.norm(dv, axis=1)
    acc = np.gradient(sp) / np.gradient(wt)
    for f, name in SEAMS:
        i = f - 1
        out["seams"].append(dict(
            frame=f, name=name,
            loc_before=[round(float(x), 6) for x in car.loc[i - 1]],
            loc_at=[round(float(x), 6) for x in car.loc[i]],
            loc_after=[round(float(x), 6) for x in car.loc[i + 1]],
            rot_at=[round(float(x), 8) for x in car.rot[i]],
            speed_before=round(float(sp[i - 1]), 6),
            speed_at=round(float(sp[i]), 6),
            speed_after=round(float(sp[i + 1]), 6),
            worst_accel_pm5=round(float(np.abs(acc[i - 5:i + 6]).max()), 4),
            median_accel_beat=round(
                float(np.median(np.abs(acc[max(0, i - 60):i + 60]))), 4)))
    return out


def table_arm(table, report):
    T = load(table)
    with open(report) as fh:
        meta = {r["name"]: r for r in json.load(fh)["shard_meta"]}
    clock = BL.Clock()
    span = T["span"].tolist()

    pop, pop_who = 0.0, None
    last_v, names = [], []
    P_end = []
    for nm in T["names"]:
        ff, p = track(T, nm)
        m = meta.get(nm)
        if m is not None:
            d = float(np.linalg.norm(p[0] - np.asarray(m["origin"], float)))
            if d > pop:
                pop, pop_who = d, nm
        # the last-key discontinuity, in metres per FILM frame, which is the
        # unit the freeze happens in
        if len(ff) >= 2:
            last_v.append(float(np.linalg.norm(p[-1] - p[-2])
                                / max(ff[-1] - ff[-2], 1.0)))
        else:
            last_v.append(0.0)
        names.append(nm)
        P_end.append(p[-1])
    last_v = np.array(last_v)
    P_end = np.array(P_end)

    tr = sagpx.load_track()
    u, v, d, ok = sagpx.project(tr, CLOSING_FRAME - 1, P_end)
    on = ok & (u > 0) & (u < 3840) & (v > 0) & (v < 2160)

    # the FROZEN part of that: bodies that were still moving when the keys ran
    # out AND land inside the closing raster
    moving = last_v > 1.0 / 24.0                # 1 m/s in world terms at 24 fps
    fm = moving & on
    return dict(
        table=os.path.basename(table), span=span, bodies=len(names),
        release_pop_max_m=round(pop, 6), release_pop_worst=pop_who,
        last_key=int(span[1]),
        bodies_over_1mm_per_film_frame=int((last_v > 1e-3).sum()),
        bodies_over_1m_per_s=int(moving.sum()),
        median_last_speed_m_per_s=round(float(np.median(last_v) * 24.0), 4),
        max_last_speed_m_per_s=round(float(last_v.max() * 24.0), 4),
        worst_body=names[int(last_v.argmax())],
        end_x_median=round(float(np.median(P_end[:, 0])), 3),
        end_x_p95=round(float(np.percentile(P_end[:, 0], 95)), 3),
        end_x_max=round(float(P_end[:, 0].max()), 3),
        closing_frame=CLOSING_FRAME,
        in_closing_raster=int(on.sum()),
        frozen_in_closing_raster=int(fm.sum()),
        frozen_u=[round(float(u[fm].min()), 1),
                  round(float(u[fm].max()), 1)] if fm.any() else None,
        frozen_v=[round(float(v[fm].min()), 1),
                  round(float(v[fm].max()), 1)] if fm.any() else None,
        frozen_px=[round(float(u[fm].max() - u[fm].min()), 1),
                   round(float(v[fm].max() - v[fm].min()), 1)]
        if fm.any() else None,
        all_u=[round(float(u[on].min()), 1), round(float(u[on].max()), 1)]
        if on.any() else None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--table", default=os.path.join(
        R2, "sim/out/breach_film.npz"))
    ap.add_argument("--report", default=os.path.join(
        R2, "sim/out/breach_sim.json"))
    ap.add_argument("--label", default=None)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()

    car = car_arm()
    tab = table_arm(a.table, a.report)
    lab = a.label or os.path.basename(a.table)

    print("=== SEAMS [%s] ===" % lab)
    print("-- the car (input; this sim reads it and writes nothing to it)")
    print("   %s  %d frames  sha256[:16] %s"
          % (car["measured"], car["frames"], car["sha256"]))
    for s in car["seams"]:
        print("   f%-5d %s" % (s["frame"], s["name"]))
        print("      loc  %s -> %s -> %s"
              % (s["loc_before"], s["loc_at"], s["loc_after"]))
        print("      speed %.4f -> %.4f -> %.4f m/s   worst |a| within +-5 "
              "frames %.4f m/s2 (beat median %.4f)"
              % (s["speed_before"], s["speed_at"], s["speed_after"],
                 s["worst_accel_pm5"], s["median_accel_beat"]))
    print("-- the table")
    for k in ("table", "span", "bodies", "release_pop_max_m",
              "release_pop_worst", "last_key",
              "bodies_over_1mm_per_film_frame", "bodies_over_1m_per_s",
              "median_last_speed_m_per_s", "max_last_speed_m_per_s",
              "worst_body", "end_x_median", "end_x_p95", "end_x_max",
              "in_closing_raster", "frozen_in_closing_raster",
              "frozen_u", "frozen_v", "frozen_px", "all_u"):
        print("   %-32s %s" % (k, tab[k]))

    if a.json:
        with open(a.json, "w") as fh:
            json.dump(dict(label=lab, car=car, table=tab), fh, indent=1)
        print("   wrote %s" % a.json)


if __name__ == "__main__":
    main()
