"""CAR-PROXY PROBE — read a breach table and ask what the car did to a body.

    python3 sim/carproxy_probe.py --table sim/out/breach_film_R2281_REBAKE.npz \
        --body MUL05_S02

Standard library + numpy only; it never opens Blender and it never opens the
sim scene, so it can be run against any table that exists.

WHY THE SPEEDS ARE IN WORLD TIME AND NOT FILM TIME
==================================================
The table is keyed on FILM frames and beat 3 ramps world time down to 15.37 %,
so a body moving at a constant 16 m/s covers 6.5x less ground per film frame
inside the ramp than outside it.  Differencing the table on film frames would
therefore report the ramp as a deceleration and the ramp's end as an
acceleration, which is exactly the artefact this probe exists to rule out.
Every velocity here is d(position)/d(WORLD time), via `breachlib.Clock`.

WHAT "CARRIED" MEANS, MEASURED
==============================
The car's pose is known independently of the sim — it is read from
`world/car_anim_measured.json`, the same file the sim keys the proxy from.  So
for any body at any frame we can express its position in the CAR'S OWN FRAME.
A body that is struck once and thrown has a car-local x that runs monotonically
backwards (the car leaves it behind).  A body that is CARRIED has a car-local
position that stays put.  That is the whole test, and it needs no contact
manifold — which is just as well, because bpy exposes none.
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


def load(table):
    z = np.load(table, allow_pickle=True)
    names = [str(x) for x in z["names"]]
    cnt = z["key_count"]
    off = np.concatenate([[0], np.cumsum(cnt)])
    return dict(names=names, cnt=cnt, off=off, frame=z["key_frame"],
                loc=z["key_loc"], quat=z["key_quat"], release=z["release"],
                span=z["span"], index={n: i for i, n in enumerate(names)})


def track(T, name):
    i = T["index"][name]
    a, b = T["off"][i], T["off"][i + 1]
    return T["frame"][a:b].astype(float), T["loc"][a:b].astype(float)


def car_at_film(clock, car, ff):
    """(loc, euler) of CAR_ROOT at fractional film frames `ff`."""
    wt = np.array([clock.world_t(f) for f in np.atleast_1d(ff)], float)
    loc, rot = car.at_world_t(wt)
    return wt, loc, rot


def to_car_local(p_world, c_loc, c_rot):
    """World -> car-local.  The car's euler is XYZ; through beat 3 it is a
    near-pure yaw-free translation, but this does the full inverse anyway so it
    stays correct if the rig ever gains a rotation."""
    out = np.empty_like(p_world)
    for k in range(len(p_world)):
        cx, cy, cz = c_rot[k]
        Rx = np.array([[1, 0, 0], [0, np.cos(cx), -np.sin(cx)],
                       [0, np.sin(cx), np.cos(cx)]])
        Ry = np.array([[np.cos(cy), 0, np.sin(cy)], [0, 1, 0],
                       [-np.sin(cy), 0, np.cos(cy)]])
        Rz = np.array([[np.cos(cz), -np.sin(cz), 0],
                       [np.sin(cz), np.cos(cz), 0], [0, 0, 1]])
        R = Rz @ Ry @ Rx
        out[k] = R.T @ (p_world[k] - c_loc[k])
    return out


CAR_ENV = dict(x=(-4.0, 6.0), y=(-2.0, 2.0), z=(-1.0, 3.0))


def probe(T, name, clock, car, verbose=True):
    ff, p = track(T, name)
    wt, cl, cr = car_at_film(clock, car, ff)
    loc_l = to_car_local(p, cl, cr)

    d0 = np.linalg.norm(p - p[0], axis=1)
    dt = np.gradient(wt)
    v = np.gradient(p, axis=0) / dt[:, None]
    sp = np.linalg.norm(v, axis=1)

    moved = np.where(d0 > 0.05)[0]
    f_first = float(ff[moved[0]]) if len(moved) else float("nan")

    inside = ((loc_l[:, 0] > CAR_ENV["x"][0]) & (loc_l[:, 0] < CAR_ENV["x"][1])
              & (np.abs(loc_l[:, 1]) < CAR_ENV["y"][1])
              & (loc_l[:, 2] > CAR_ENV["z"][0]) & (loc_l[:, 2] < CAR_ENV["z"][1]))
    # longest consecutive run inside the envelope
    best = cur = 0
    b0 = c0 = 0
    for k, f in enumerate(inside):
        if f:
            if cur == 0:
                c0 = k
            cur += 1
            if cur > best:
                best, b0 = cur, c0
        else:
            cur = 0

    r = dict(
        body=name, n_keys=int(len(ff)),
        film_first=ff[0], film_last=ff[-1],
        first_move_film_frame=f_first,
        travel_m=float(d0[-1]), travel_max_m=float(d0.max()),
        dx=float(p[-1, 0] - p[0, 0]), dy=float(p[-1, 1] - p[0, 1]),
        dz=float(p[-1, 2] - p[0, 2]),
        p_first=p[0].tolist(), p_last=p[-1].tolist(),
        speed_max=float(sp.max()),
        speed_max_film_frame=float(ff[int(sp.argmax())]),
        speed_last=float(sp[-1]),
        carlocal_frames_inside=int(inside.sum()),
        carlocal_longest_run=int(best),
        carlocal_run_film=[float(ff[b0]), float(ff[b0 + best - 1])] if best else None,
    )
    if verbose:
        print("== %s  (%d keys, film %.0f..%.0f)" % (name, r["n_keys"],
                                                     r["film_first"],
                                                     r["film_last"]))
        print("   first move >0.05 m at film f%.1f" % r["first_move_film_frame"])
        print("   travel %.2f m   d=(%.2f, %.2f, %.2f)"
              % (r["travel_m"], r["dx"], r["dy"], r["dz"]))
        print("   speed max %.2f m/s at f%.1f, last %.2f m/s"
              % (r["speed_max"], r["speed_max_film_frame"], r["speed_last"]))
        print("   inside car envelope %d/%d keys, longest run %d (%s)"
              % (r["carlocal_frames_inside"], r["n_keys"],
                 r["carlocal_longest_run"], r["carlocal_run_film"]))
    return r, dict(ff=ff, wt=wt, p=p, loc_l=loc_l, sp=sp, d0=d0,
                   car_loc=cl)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--table", default=os.path.join(
        R2, "sim", "out", "breach_film_R2281_REBAKE.npz"))
    ap.add_argument("--body", action="append", default=[])
    ap.add_argument("--trace", default=None,
                    help="body name: print a per-key trace")
    ap.add_argument("--top", type=int, default=0,
                    help="also report the N furthest-travelled bodies")
    ap.add_argument("--json", default=None)
    a = ap.parse_args()

    T = load(a.table)
    clock = BL.Clock()
    car = BL.Car()
    print("table %s  span %s  bodies %d"
          % (os.path.basename(a.table), T["span"].tolist(), len(T["names"])))

    out = {"table": a.table, "bodies": []}
    for nm in (a.body or ["MUL05_S02"]):
        r, tr = probe(T, nm, clock, car)
        out["bodies"].append(r)

    if a.trace:
        _, tr = probe(T, a.trace, clock, car, verbose=False)
        print("\n-- trace %s : film, worldt, x, z, |v|, car_x, local_x, local_z"
              % a.trace)
        n = len(tr["ff"])
        step = max(1, n // 60)
        for k in list(range(0, n, step)) + [n - 1]:
            print("   f%7.1f  t%7.3f  x%9.2f z%7.2f  v%7.2f  carx%9.2f  "
                  "lx%8.2f lz%7.2f"
                  % (tr["ff"][k], tr["wt"][k], tr["p"][k, 0], tr["p"][k, 2],
                     tr["sp"][k], tr["car_loc"][k, 0], tr["loc_l"][k, 0],
                     tr["loc_l"][k, 2]))

    if a.top:
        tot = []
        for nm in T["names"]:
            ff, p = track(T, nm)
            tot.append((float(np.linalg.norm(p[-1] - p[0])), nm))
        tot.sort(reverse=True)
        print("\n-- %d furthest-travelled bodies" % a.top)
        for d, nm in tot[:a.top]:
            print("   %8.2f m  %s" % (d, nm))
        out["top"] = [dict(travel_m=d, body=nm) for d, nm in tot[:a.top]]

    if a.json:
        with open(a.json, "w") as fh:
            json.dump(out, fh, indent=1)
        print("wrote %s" % a.json)


if __name__ == "__main__":
    main()
