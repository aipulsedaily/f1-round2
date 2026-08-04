"""R2-701 — every breach table judged side by side, on the three measurements
that separate a breach from a defect.

    .venv/bin/python sim/r2701_verdict.py \
        R6=sim/out/breach_film_R6_SHIPPED.npz \
        R2281=sim/out/breach_film_R2281_REBAKE.npz \
        R2387=sim/out/breach_film_R2387.npz \
        AERO=sim/out/breach_film_R2701A.npz \
        SOLID=sim/out/breach_film_R2701S.npz

Three measurements, and they are deliberately not one number:

  1. **POSE** (`sim/ridepose.py`) — the acceptance criterion of R2-700, as the
     own-motion ratio: the share of a member's on-screen movement that is its
     own rather than the car's.  Under 0.25 while aboard = being carried.
     This is the verdict.  It is quoted with `aboard`, because a bake with
     nothing aboard is VACUOUS rather than passing (R6 is the worked example:
     nothing comes to rest on a car that nothing comes off).

  2. **TRAY RESIDENCE** — film frames spent within ±0.5 m of car-local
     x = -2.200, the rear wing's leading face, while above the deck.  This is
     the mechanism `--rear-wing aerofoil` exists to change, so it is the number
     that says whether the CORRECTION worked, as distinct from whether the
     PICTURE is fixed.  The two can differ and the whole point of separating
     them is that they can.

  3. **THE Z GAP AT THE PEAK** — how far the worst member sits above the proxy's
     highest surface (`CAR_TOP_Z` = 0.992) during f0967-f0977, and how far below
     it the nearest other body is.  In R2387 that gap is +0.55 m with 0.30 m of
     air underneath: at the frames the eye judges, the member is NOT touching
     the car at all.  A fix aimed at a contact cannot be assumed to reach a
     phase that has no contact in it, and this column is what keeps that
     honest.

Judge on the printed `>> STAGE RESULT:` line.
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
import resample as RS                                             # noqa: E402
import sagpx as SG                                                # noqa: E402
import ridepose as RP                                             # noqa: E402

WING_X = -2.200
PEAK = (967, 977)


def carlocal(table, f0, f1):
    T = RS.read_film(table)
    names = T["names"]
    fr = np.arange(f0, f1 + 1, dtype=float)
    L, _Q = T["expand"](fr)
    car = BL.Car()
    clock = BL.Clock()
    wt = np.array([clock.world_t(f) for f in fr])
    cl, ce = car.at_world_t(wt)
    Rc = RP._rotmats(ce)
    q = np.einsum("fij,fbi->fbj", Rc, L - cl[:, None, :])
    return names, fr, q


def tray_residence(names, fr, q):
    """longest run in the wing's catch band, per structural body."""
    out = []
    for b, n in enumerate(names):
        if n.startswith("GS_"):
            continue
        m = ((np.abs(q[:, b, 0] - WING_X) < 0.5) & (q[:, b, 2] > 0.55)
             & (np.abs(q[:, b, 1]) < 1.2))
        r, s = RP.longest_run(m)
        if r:
            out.append((r, n, float(fr[s]), float(fr[s + r - 1]),
                        float(q[s:s + r, b, 2].mean())))
    out.sort(reverse=True)
    return out


def peak_gap(names, fr, q, body):
    """how far the body floats above the proxy, and what is under it."""
    b = names.index(body)
    k0 = int(np.searchsorted(fr, PEAK[0]))
    k1 = int(np.searchsorted(fr, PEAK[1]))
    gl = np.array([n.startswith("GS_") for n in names])
    zs, unders, ngs = [], [], []
    for k in range(k0, k1 + 1):
        p = q[k, b]
        d2 = np.hypot(q[k, :, 0] - p[0], q[k, :, 1] - p[1])
        below = (d2 < 0.6) & (q[k, :, 2] < p[2] - 0.02) & (q[k, :, 2] > p[2] - 1.2)
        below[b] = False
        zs.append(p[2])
        ngs.append(int((below & gl).sum()))
        unders.append(float(p[2] - q[k, below, 2].max()) if below.any()
                      else float("nan"))
    return (float(np.mean(zs)), float(np.mean(zs)) - BL.CAR_TOP_Z,
            float(np.nanmean(unders)) if not np.all(np.isnan(unders)) else
            float("nan"), float(np.mean(ngs)))


def main():
    specs = [s for s in sys.argv[1:] if "=" in s]
    if not specs:
        raise SystemExit(__doc__)
    track = SG.load_track()
    rows = []
    for spec in specs:
        tag, _, table = spec.partition("=")
        table = table if os.path.isabs(table) else os.path.join(R2, table)
        if not os.path.exists(table):
            print("   %-6s MISSING %s" % (tag, table))
            continue
        pose = RP.analyse(table, np.arange(940, 1061), track)
        names, fr, q = carlocal(table, 860, 1060)
        tray = tray_residence(names, fr, q)
        worst = (pose["carried"][0]["name"] if pose["carried"]
                 else (tray[0][1] if tray else None))
        gap = peak_gap(names, fr, q, worst) if worst else (
            float("nan"),) * 4
        rows.append(dict(tag=tag, table=os.path.basename(table),
                         aboard=pose["n_aboard"], carried=pose["n_carried"],
                         rated=pose["n_rated"], min_ratio=pose["min_ratio"],
                         verdict=pose["VERDICT"], worst=worst,
                         tray_top=tray[0][:2] if tray else None,
                         tray_frames=tray[0][0] if tray else 0,
                         peak_z=gap[0], peak_above_car=gap[1],
                         peak_air_below=gap[2], peak_glass_below=gap[3]))

    print()
    print("%-7s %7s %8s %9s %8s %26s %7s %8s %8s"
          % ("bake", "aboard", "carried", "min own", "verdict", "tray band, worst member",
             "peak z", "above", "air under"))
    print("%-7s %7s %8s %9s %8s %26s %7s %8s %8s"
          % ("", "", "<0.25", "ratio", "", "(frames near x=-2.200)", "(m)",
             "car (m)", "it (m)"))
    for r in rows:
        print("%-7s %7d %8s %9s %8s %26s %7.2f %+8.2f %8.2f"
              % (r["tag"], r["aboard"],
                 "%d/%d" % (r["carried"], r["rated"]),
                 "%.3f" % r["min_ratio"] if r["min_ratio"] is not None else "n/a",
                 r["verdict"],
                 ("%s %d" % (r["tray_top"][1], r["tray_top"][0]))
                 if r["tray_top"] else "-",
                 r["peak_z"], r["peak_above_car"], r["peak_air_below"]))
    print()
    for r in rows:
        print("   %-6s worst member by pose: %s" % (r["tag"], r["worst"]))
    out = os.path.join(R2, "sim", "out", "r2701_verdict.json")
    with open(out, "w") as fh:
        json.dump(rows, fh, indent=1, default=float)
    print("wrote %s" % out)
    print(">> STAGE RESULT: R2701_VERDICT %s"
          % " ".join("%s=%s" % (r["tag"], r["verdict"]) for r in rows))


if __name__ == "__main__":
    main()
