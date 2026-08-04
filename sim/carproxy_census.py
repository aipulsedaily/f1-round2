"""CAR-PROXY CENSUS — how much of the debris field is the car CARRYING?

    python3 sim/carproxy_census.py --table sim/out/breach_film_R2281_REBAKE.npz

Reads a breach table, puts every body into the CAR'S OWN FRAME at every key,
and separates the distance each body travelled into

    TRANSPORT   distance covered while inside the car proxy's envelope
    FREE        distance covered outside it

and classifies the capture by WHERE on the car it is held: on the deck, under
the floor, at the nose, or alongside.  It also runs the momentum budget the
docstring of `build_breach_sim.py` argues from — Sum(m|v|) over the field
against the car's own 798 x v — so that "the field takes up to 45 % of the
car's momentum" can be checked rather than repeated.

Masses and areas come from `shard_meta` in a breach_sim report; they are
geometry, not solver output, so any report of the same fracture will do.  Frame
bodies are not in `shard_meta` and get their mass from the same rule the build
uses: 4.7 kg/m of 6063-T6, split 0.72 / 0.28 between extrusion and plate.

WHY THE ENVELOPE IS THE PROXY'S OWN POINTS AND NOT A GUESSED BOX
================================================================
`breachlib.car_proxy_parts()` is the collider.  This module takes the union of
its points, so the envelope is the thing the solver actually collides against,
inflated by one margin.  A guessed box would let the census be wrong in the
direction that flatters it.
"""

import argparse
import json
import os
import sys
from collections import defaultdict

import numpy as np

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(R2, "sim"), os.path.join(R2, "anim")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import breachlib as BL                                            # noqa: E402
from carproxy_probe import load, track, to_car_local               # noqa: E402

INFLATE = 0.12          # m.  A body is "held" if it is within 120 mm of the
                        # proxy's own convex envelope: the collision margin is
                        # 0.15 mm, so this is generous ON PURPOSE — a census
                        # that under-counts capture would understate the defect
                        # it exists to size.


def proxy_env():
    P = np.vstack([p for _n, p in BL.car_proxy_parts()])
    return P.min(axis=0) - INFLATE, P.max(axis=0) + INFLATE


def masses(report):
    with open(report) as fh:
        d = json.load(fh)
    m = {r["name"]: float(r["mass"]) for r in d["shard_meta"]}
    a = {r["name"]: float(r["area"]) for r in d["shard_meta"]}
    return m, a


def frame_mass(name, iface):
    """4.7 kg/m over the segment's own height, 0.72 body / 0.28 plate."""
    st = {r["uid"]: r for r in iface["stations"]}
    try:
        if name.startswith("MUL"):
            uid = int(name[3:5])
            r = st[uid]
            h = (r["head_z"] - r["foot_z"]) / 8.0
            return 4.7 * h * (0.28 if name.endswith("_P") else 0.72)
        if name.startswith("TRN"):
            # a transom rail across one bay; the census only needs it to order
            # of magnitude, and the bay pitch is the station spacing
            ys = sorted(r["y"] for r in iface["stations"])
            pitch = float(np.median(np.diff(ys)))
            return 4.7 * pitch * (0.28 if name.endswith("_P") else 0.72)
    except Exception:
        pass
    return 3.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--table", default=os.path.join(
        R2, "sim", "out", "breach_film_R2281_REBAKE.npz"))
    ap.add_argument("--report", default=os.path.join(
        R2, "sim", "out", "breach_sim.json"))
    ap.add_argument("--json", default=None)
    ap.add_argument("--label", default=None)
    a = ap.parse_args()

    T = load(a.table)
    clock, car = BL.Clock(), BL.Car()
    lo, hi = proxy_env()
    M, A = masses(a.report)
    iface = BL.wall_iface()

    tag = a.label or os.path.basename(a.table)
    print("== census %s   proxy envelope x %.2f..%.2f  y %.2f..%.2f  "
          "z %.2f..%.2f (+%.0f mm)"
          % (tag, lo[0], hi[0], lo[1], hi[1], lo[2], hi[2], INFLATE * 1000))

    # one shared film-frame grid: every body is keyed on a subset of it
    allf = np.arange(int(T["span"][0]), int(T["span"][1]) + 1, dtype=float)
    wt = np.array([clock.world_t(f) for f in allf])
    c_loc, c_rot = car.at_world_t(wt)
    fidx = {f: i for i, f in enumerate(allf)}

    tot = dict(bodies=0, transport_m=0.0, free_m=0.0, mass_kg=0.0,
               captured=0, transported_mass_kg=0.0)
    mode_n, mode_m = defaultdict(int), defaultdict(float)
    per_body = []
    # field momentum on the shared grid
    p_field = np.zeros(len(allf))
    m_field = np.zeros(len(allf))

    for nm in T["names"]:
        ff, p = track(T, nm)
        ii = np.array([fidx[f] for f in ff])
        L = to_car_local(p, c_loc[ii], c_rot[ii])
        inside = np.all((L > lo) & (L < hi), axis=1)
        seg = np.linalg.norm(np.diff(p, axis=0), axis=1)
        held = inside[:-1] & inside[1:]
        tr = float(seg[held].sum())
        fr = float(seg[~held].sum())
        m = M.get(nm) or frame_mass(nm, iface)

        # capture mode at the frame of greatest transport speed
        mode = "none"
        if held.any():
            k = int(np.argmax(np.where(held, seg, 0.0)))
            lx, ly, lz = L[k]
            if lz > 0.55:
                mode = "deck"
            elif lz < 0.12 and -2.2 < lx < 1.6:
                mode = "underfloor"
            elif lx > 1.5:
                mode = "nose"
            else:
                mode = "flank"

        tot["bodies"] += 1
        tot["transport_m"] += tr
        tot["free_m"] += fr
        tot["mass_kg"] += m
        if tr > 1.0:
            tot["captured"] += 1
            tot["transported_mass_kg"] += m
            mode_n[mode] += 1
            mode_m[mode] += m
        per_body.append(dict(body=nm, transport_m=tr, free_m=fr, mass_kg=m,
                             mode=mode))

        # momentum, on world time
        dt = np.gradient(wt[ii])
        v = np.linalg.norm(np.gradient(p, axis=0) / dt[:, None], axis=1)
        p_field[ii] += m * v
        m_field[ii] += m

    car_v = np.linalg.norm(np.gradient(c_loc, axis=0) / np.gradient(wt)[:, None],
                           axis=1)
    car_p = 798.0 * car_v

    print("   bodies %d, total mass %.1f kg" % (tot["bodies"], tot["mass_kg"]))
    print("   distance TRANSPORTED by the car : %10.1f m" % tot["transport_m"])
    print("   distance travelled FREE         : %10.1f m" % tot["free_m"])
    print("   transport share of all travel   : %9.1f %%"
          % (100.0 * tot["transport_m"] / max(tot["transport_m"] + tot["free_m"],
                                              1e-9)))
    print("   bodies carried >1 m: %d (%.1f kg, %.1f %% of the field's mass)"
          % (tot["captured"], tot["transported_mass_kg"],
             100.0 * tot["transported_mass_kg"] / max(tot["mass_kg"], 1e-9)))
    for k in sorted(mode_n, key=lambda x: -mode_n[x]):
        print("      %-11s %5d bodies %8.1f kg" % (k, mode_n[k], mode_m[k]))

    j = int(np.argmax(p_field))
    print("   field momentum peak %.0f kg.m/s at film f%.0f, car %.0f kg.m/s "
          "-> %.1f %% of the car"
          % (p_field[j], allf[j], car_p[j], 100.0 * p_field[j] / car_p[j]))
    for f in (860, 880, 900, 950, 1000, 1100, 1165):
        if f in fidx:
            i = fidx[f]
            print("      f%-5d field %8.0f  car %8.0f   %6.1f %%"
                  % (f, p_field[i], car_p[i], 100.0 * p_field[i] / car_p[i]))

    top = sorted(per_body, key=lambda r: -r["transport_m"])[:15]
    print("   most-transported bodies:")
    for r in top:
        print("      %8.1f m transported (%6.1f free) %-14s %s"
              % (r["transport_m"], r["free_m"], r["body"], r["mode"]))

    if a.json:
        with open(a.json, "w") as fh:
            json.dump(dict(table=a.table, totals=tot,
                           modes={k: dict(n=mode_n[k], kg=mode_m[k])
                                  for k in mode_n},
                           momentum=dict(
                               film=allf.tolist(), field=p_field.tolist(),
                               car=car_p.tolist()),
                           top=top), fh, indent=1)
        print("   wrote %s" % a.json)


if __name__ == "__main__":
    main()
