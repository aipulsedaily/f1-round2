"""SCORE A BAKE.  One instrument, run identically on every run in the sweep and
on the null, so the numbers in the report are comparable by construction.

    python3 sim/breach_metrics.py sim/tmp/sw_b100.npz sim/tmp/sw_b100.json

WHAT IT MEASURES, AND WHY EACH ONE EXISTS
  aperture      the largest CONNECTED vacated region (sim/aperture.py), not the
                bbox of the origins of everything that twitched.  The bbox
                measure reports 13.0 x 5.8 m off TWO shards; see
                aperture.aperture_controls.
  ceiling       what the aperture COULD be given which bays the plan allows to
                go.  Bays 2 and 7 are `retained` by the plan, so the glass can
                span at most bay 3's left edge to bay 6's right edge = 8.77 m.
                The declared 9.6 m is |y| <= 4.8 between the two BENT mullions,
                which is a different measurement of a different object.
  fragments     mass-weighted speed, and LAUNCH speed (the speed at which each
                shard crosses 0.25 m from home) as distinct from peak speed.
                Peak speed over 3,948 bodies is a max over noise; launch speed
                is the thing "flung at 2.4x the impactor" is a claim about.
  frame         which mullion segments left, and how far the retained ones bent
                — R6's acceptance criterion.
  rest          how much of the field is still moving at the last frame.

CONTROLS are printed with every run:
  positive  an injected body at 40 m/s must come back at 40 m/s
  negative  bodies whose transform is BIT-IDENTICAL across the whole bake must
            come back at exactly 0 m/s and 0 m of travel.  (Selecting them by
            "net displacement < 1e-6" does NOT work: one shard in the b100 bake
            leaves at 18 m/s and lands back within 2.5e-7 m of home.)
"""
import json
import os
import re
import sys

import numpy as np

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in ("sim", "anim", "world"):
    p = os.path.join(R2, _p)
    if p not in sys.path:
        sys.path.insert(0, p)

import aperture as AP                                              # noqa: E402
import fracture as FR                                              # noqa: E402

GONE_M = 0.25
DESTROYED = (3, 4, 5, 6)
RETAINED = (2, 7)
CAR_V = 16.4
CAR_M = 798.0


def score(npz_path, json_path, plan=None, cell=0.05, verbose=True):
    d = np.load(npz_path, allow_pickle=True)
    loc, names, wt = d["loc"], d["names"], d["world_t"]
    info = json.load(open(json_path))
    meta = info["shard_meta"]
    nsh = len(meta)
    plan = plan or FR.load(os.path.join(R2, "sim/out/fracture_wall.npz"))
    m = np.array([x["mass"] for x in meta], float)
    st = np.array([x["origin"] for x in meta], float)
    en = loc[-1, :nsh]
    dt = np.diff(wt)[:, None]
    v = np.linalg.norm(np.diff(loc, axis=0), axis=2) / dt
    vsh = v[:, :nsh]

    # ---- CONTROLS ------------------------------------------------------- #
    n = len(wt)
    fake = np.zeros((n, 1, 3))
    fake[:, 0, 0] = 40.0 * (wt - wt[0])
    cpos = float((np.linalg.norm(np.diff(fake, axis=0), axis=2).ravel()
                  / np.diff(wt)).max())
    frozen = np.all(loc == loc[0], axis=(0, 2))
    cneg_v = float(v[:, frozen].max()) if frozen.any() else float("nan")
    cneg_d = float(np.linalg.norm(loc[-1][frozen] - loc[0][frozen],
                                  axis=1).max()) if frozen.any() else 0.0
    controls = dict(POS_injected_40ms=round(cpos, 4),
                    NEG_bitidentical_n=int(frozen.sum()),
                    NEG_bitidentical_max_speed_ms=cneg_v,
                    NEG_bitidentical_max_travel_m=cneg_d,
                    PASS=bool(abs(cpos - 40.0) < 1e-2 and frozen.sum() > 0
                              and cneg_v == 0.0 and cneg_d == 0.0))

    # ---- who left ------------------------------------------------------- #
    net = np.linalg.norm(en - st, axis=1)
    gone = net > GONE_M
    gone_ids = {(meta[i]["bay"], meta[i]["id"]) for i in np.where(gone)[0]}

    # ---- the frame: which mullion segments left, how far the rest bent --- #
    fr_names = [str(x) for x in names[nsh:]]
    fr_st, fr_en = loc[0, nsh:], loc[-1, nsh:]
    fr_net = np.linalg.norm(fr_en - fr_st, axis=1)
    gone_mul, mul_disp = set(), {}
    for k, nm in enumerate(fr_names):
        mm = re.match(r"MUL(\d\d)_S(\d\d)", nm)
        if not mm:
            continue
        mi, sj = int(mm.group(1)), int(mm.group(2))
        mul_disp.setdefault(mi, []).append(float(fr_net[k]))
        if fr_net[k] > GONE_M:
            # the un-segmented mullions are one body for the whole height
            for s in (range(8) if mi in (0, 1, 2, 8, 9, 10) else [sj]):
                gone_mul.add((mi, s))
    frame = dict(
        mullion_max_disp_m={str(k): round(max(vv), 4)
                            for k, vv in sorted(mul_disp.items())},
        segments_gone=sorted({mi for mi, _ in gone_mul}),
        n_segments_gone=len(gone_mul),
        bent_3_m=round(max(mul_disp.get(3, [0])), 4),
        bent_7_m=round(max(mul_disp.get(7, [0])), 4),
        transom_max_disp_m=round(float(max(
            [fr_net[k] for k, nm in enumerate(fr_names)
             if nm.startswith("TRN")] or [0])), 4))

    # ---- aperture -------------------------------------------------------- #
    bays = tuple(sorted(set(DESTROYED) | set(RETAINED)))
    grid = AP._rasterise(plan, cell, bays)
    ap = AP.hole(plan, gone_ids, cell, bays, grid, gone_mullions=gone_mul)
    ap["old_bbox_measure"] = AP.old_bbox(plan, gone_ids)
    per_bay = {}
    for b in bays:
        g1 = AP._rasterise(plan, cell, (b,))
        h = AP.hole(plan, gone_ids, cell, (b,), g1)
        per_bay[str(b)] = dict(role=plan["roles"][b],
                               vacated_pct=round(h["vacated_pct"], 1),
                               hole_w_m=round(h["hole_w_m"], 2),
                               hole_h_m=round(h["hole_h_m"], 2))
    ap["per_bay"] = per_bay
    r = plan["rects"]
    ap["CEILING"] = dict(
        glass_width_if_bays_3_to_6_all_leave_m=round(
            r[6][1] - r[3][0], 3),
        glass_height_m=round(r[4][3] - r[4][2], 3),
        declared_w_m=9.6, declared_h_m=5.6,
        note="9.6 m is |y| <= 4.8, the clear span between the two BENT "
             "mullions at y = +-4.4.  The GLASS in bays 3-6 can only reach "
             "8.77 m: reaching 9.6 m of glass needs 385 mm off the inner edge "
             "of bays 2 and 7, which the plan marks `retained`.")

    # ---- fragments ------------------------------------------------------- #
    # LAUNCH speed: each shard's speed at the frame it first passes 0.25 m.
    trav = np.linalg.norm(loc[:, :nsh] - st[None], axis=2)
    first = np.argmax(trav > GONE_M, axis=0)
    launch = np.array([vsh[max(0, first[i] - 1), i] if gone[i] else 0.0
                       for i in range(nsh)])
    lg, mg = launch[gone], m[gone]
    peak = vsh.max(axis=0)

    def mw(x, w, q):
        o = np.argsort(x)
        c = np.cumsum(w[o]) / w.sum()
        return float(x[o][min(np.searchsorted(c, q), len(x) - 1)])

    frag = dict(
        n_gone=int(gone.sum()), of=nsh,
        gone_mass_kg=round(float(m[gone].sum()), 1),
        total_mass_kg=round(float(m.sum()), 1),
        launch_ms=dict(
            p50=round(mw(lg, mg, .50), 2), p90=round(mw(lg, mg, .90), 2),
            p99=round(mw(lg, mg, .99), 2), max=round(float(lg.max()), 2))
        if gone.any() else {},
        launch_over_impactor=round(float(mw(lg, mg, .99)) / CAR_V, 2)
        if gone.any() else 0.0,
        peak_ms=dict(p50_mass=round(mw(peak, m, .50), 2),
                     p99_mass=round(mw(peak, m, .99), 2),
                     max=round(float(peak.max()), 1)),
        mass_pct_over_impactor_speed=round(
            100 * float(m[peak > CAR_V].sum()) / float(m.sum()), 2),
        mass_pct_over_2x_impactor=round(
            100 * float(m[peak > 2 * CAR_V].sum()) / float(m.sum()), 3),
        field_KE_max_J=round(float((0.5 * m[None] * vsh ** 2).sum(1).max())),
        car_KE_J=round(0.5 * CAR_M * CAR_V ** 2),
        floor=dict(landed_below_z0p5=int((en[:, 2] < 0.5).sum()),
                   max_down_dz_m=round(float((en[:, 2] - st[:, 2]).min()), 3),
                   east_of_x15p5=int((en[:, 0] > 15.5).sum())))

    # ---- at rest? -------------------------------------------------------- #
    last = v[-1]
    rest = dict(bodies_over_1mm_per_film_frame=int(
        (last / 24.0 > 0.001).sum()), of=int(len(last)),
        max_speed_last_frame_ms=round(float(last.max()), 3),
        median_speed_last_frame_ms=round(float(np.median(last)), 4))

    out = dict(run=os.path.basename(npz_path),
               bond_per_m=info["thresholds"]["bond_per_m"],
               no_car=("car proxy: 0" in "" or info.get("n_bodies", 0) < 4040),
               frames=int(len(wt)),
               window_s=round(float(wt[-1] - wt[0]), 4),
               CONTROLS=controls, aperture=ap, fragments=frag,
               frame_bodies=frame, at_rest=rest)
    if verbose:
        print(json.dumps(out, indent=1, default=float))
    return out


if __name__ == "__main__":
    score(sys.argv[1], sys.argv[2])
