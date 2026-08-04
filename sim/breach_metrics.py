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
  persistence   PEAK IS NOT PERSISTENCE.  `frame` above, and
                `apply_breach.build_frame`'s `max_travel_m`, are MAXIMA over
                the bake.  A member that deflects 303 mm and springs back to
                0 mm, and one that deflects 303 mm and stays there, print the
                SAME 0.303 in both.  In a take with zero cuts the first is the
                wall repairing itself on camera.  So this measures END and
                END/PEAK and it is the arm that refuses.  R2-601.

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
# R2-601.  A body has DEFLECTED if its peak travel clears 10 mm, and has
# RECOVERED if it ends below 10 % of its own peak.  10 mm is the smallest
# deflection that is worth a pixel anywhere in this shot: the beat-3 pass runs
# at 5.3 mm/px, so 10 mm is 1.9 px there.  10 % is not a tuned number -- the
# recoveries this catches sit at 0.3-0.5 % of peak and the survivors at 93-100 %,
# so anything between about 2 % and 80 % separates the two populations
# identically.
DEFLECT_M = 0.010
RETURN_FRAC = 0.10
# THE GATE IS ON THE SIZE OF THE LARGEST RECOVERY, NOT ON THE COUNT.  A count
# of zero cannot be asked for and should not be: a mullion that is still bolted
# in is SUPPOSED to flex a few millimetres under the blast and come back, and
# every bake on disk has a handful of sub-20 mm ones on the neighbouring
# members.  What is a defect is a recovery you can SEE.  25 mm is 4.7 px at the
# beat-3 pass's own measured near scale of 5.3 mm/px (f945, 5.9 m).  It
# separates the populations by 8x -- shipped bake 157 mm, corrected bake
# 19.5 mm -- and any value from 25 mm to 90 mm returns the same verdict on
# every bake in sim/tmp.  R2-601.
RECOVERY_GATE_M = 0.025
# The glass arm is a whole-field statistic, not a count, for the same reason:
# 57 of 3,789 shards landing back near home is gravel settling.  A pane that
# bulges as a sheet and springs back moves the MEDIAN -- 0.159 in the
# superseded bond-4000 bake against 0.999-1.000 in every bake in the ship path.
GLASS_MEDIAN_FLOOR = 0.90
DESTROYED = (3, 4, 5, 6)
RETAINED = (2, 7)
CAR_V = 16.4
CAR_M = 798.0


def _recovery(D):
    """D: (T, N) displacement-from-home.  -> per-body peak, end, end/peak."""
    pk = D.max(axis=0)
    en = D[-1]
    return pk, en, en / np.maximum(pk, 1e-12)


def persistence(loc, names, nsh):
    """DID ANYTHING GO OUT AND COME BACK?  R2-601.

    The defect this exists for is a wall that un-breaks: bodies that deflect
    and then return to the intact rest pose.  It is invisible to every measure
    the pipeline had, because they are all maxima -- see the module docstring.

    Reported for the ALUMINIUM and the GLASS separately, because they fail for
    different reasons and only one of them has ever actually failed:

      the glass  recovers only under the SUPERSEDED bond-4000 config
                 (`sim/tmp/breach_bake.npz`: median end/peak 0.159, 1,261 of
                 3,796 shards home again).  At bond 100 it is 0.999-1.000 in
                 every bake on disk.  R2-097's "the pane bulges as a sheet and
                 springs back" is a true statement about that file and a false
                 one about anything in the ship path.
      the frame  recovers whenever `t_transom` is left at 260.  The shipped
                 table has 62 of 66 deflected frame bodies home again.

    CONTROLS, all three must fire or the number is not evidence:
      POS  an injected body that goes 1 m out and comes back MUST be counted
           recovered.  A measure that only ever looks at the last frame, or
           only at the peak, fails this.
      NEG  an injected body that goes 1 m out and STAYS must NOT be counted.
      ZERO bodies bit-identical across the whole bake are neither deflected nor
           recovered -- they never moved, and "came home" is not the same claim
           as "never left".
    """
    T = loc.shape[0]
    fr = np.arange(nsh, loc.shape[1])
    gs = np.arange(0, nsh)
    out = {}
    for tag, ii in (("frame_bodies", fr), ("glass", gs)):
        if not len(ii):
            out[tag] = dict(n=0)
            continue
        D = np.linalg.norm(loc[:, ii] - loc[0, ii][None], axis=2)
        pk, en, r = _recovery(D)
        defl = pk > DEFLECT_M
        back = defl & (r < RETURN_FRAC)
        nm = [names[i] for i in ii]
        worst = sorted(((float(pk[k]), float(en[k]), float(r[k]), nm[k])
                        for k in np.where(defl)[0]), reverse=True)[:12]
        out[tag] = dict(
            n=int(len(ii)), deflected=int(defl.sum()),
            RECOVERED=int(back.sum()), stayed_out=int((defl & ~back).sum()),
            pct_recovered=round(100.0 * back.sum() / max(1, defl.sum()), 1),
            median_end_over_peak=(round(float(np.median(r[defl])), 4)
                                  if defl.any() else None),
            max_peak_m=round(float(pk.max()), 4),
            # the gated number: how big is the biggest thing that came home
            max_recovered_peak_m=(round(float(pk[back].max()), 4)
                                  if back.any() else 0.0),
            max_recovered_name=(nm[int(np.where(back)[0][
                int(np.argmax(pk[back]))])] if back.any() else None),
            recovered_names=sorted(nm[k] for k in np.where(back)[0])[:12],
            worst=[[w[3], round(w[0], 4), round(w[1], 4), round(w[2], 4)]
                   for w in worst])

    # ---- CONTROLS -------------------------------------------------------- #
    t = np.linspace(0.0, 1.0, T)
    synth = np.zeros((T, 3, 3))
    synth[:, 0, 0] = np.sin(np.pi * t)            # POS: out 1 m and back
    synth[:, 1, 0] = t                            # NEG: out 1 m and stays
    synth[:, 2, 0] = 0.0                          # ZERO: never moves
    Ds = np.linalg.norm(synth - synth[0][None], axis=2)
    spk, sen, sr = _recovery(Ds)
    sdefl = spk > DEFLECT_M
    sback = sdefl & (sr < RETURN_FRAC)
    ctl = dict(POS_out_and_back_flagged=bool(sback[0]),
               NEG_out_and_stays_flagged=bool(sback[1]),
               ZERO_never_moved_deflected=bool(sdefl[2]),
               POS_end_over_peak=round(float(sr[0]), 6),
               NEG_end_over_peak=round(float(sr[1]), 6))
    ctl["PASS"] = bool(sback[0] and not sback[1] and not sdefl[2])
    out["CONTROLS"] = ctl

    out["rule"] = (
        "deflected: peak travel > %.3f m.  RECOVERED: end < %.0f %% of that "
        "body's OWN peak.  REFUSED when the largest recovery in the aluminium "
        "clears %.3f m (%.1f px at the beat-3 pass's 5.3 mm/px), or when the "
        "glass field's median end/peak falls below %.2f."
        % (DEFLECT_M, 100 * RETURN_FRAC, RECOVERY_GATE_M,
           RECOVERY_GATE_M / 0.0053, GLASS_MEDIAN_FLOOR))
    fb, gl = out["frame_bodies"], out["glass"]
    out["frame_PASS"] = bool(fb["max_recovered_peak_m"] <= RECOVERY_GATE_M)
    out["glass_PASS"] = bool(gl["median_end_over_peak"] is None
                             or gl["median_end_over_peak"] >= GLASS_MEDIAN_FLOOR)
    out["PASS"] = bool(ctl["PASS"] and out["frame_PASS"] and out["glass_PASS"])
    return out


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

    # ---- persistence: did anything go out and come BACK?  R2-601. -------- #
    persist = persistence(loc, [str(x) for x in names], nsh)

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
               frame_bodies=frame, at_rest=rest, persistence=persist)
    if verbose:
        print(json.dumps(out, indent=1, default=float))
    return out


if __name__ == "__main__":
    score(sys.argv[1], sys.argv[2])
