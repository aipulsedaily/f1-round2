"""R2-3721 -- DO THE TWO CO-VISIBILITY LOOPS AGREE ON THE SAME 27,969 TREES?

    python3 tools/r2_3721_sweep_crosscheck.py \
        --points work/w2_0/retier_a10/world_points.npz \
        --path render/film24_path.json \
        --covis work/r23721/covis_film24.json \
        --out work/r23721/sweep_crosscheck.json

WHY
---
`tools/instance_variety.py` grew its own co-visibility sweep at R2-3721, with a
height-octave spatial index and a per-point cull that `tools/r2_3421_
covisible_repeats.py` does not have -- it walks every point every frame.  Two
loops, written independently, six weeks apart, over the same projection.

The optimisation is exactly the kind of thing that produces a confident wrong
number: a cull radius one metre too small silently drops the far half of a
treeline and the answer still looks plausible.  So the two are made to agree on
input they can share.

WHAT IS SHARED, AND WHAT IS NOT
-------------------------------
The dump records the 27,969 discrete plants of `assembly10` as ONE ORIGIN AND
ONE WORLD BBOX EACH -- exact, unsampled.  Both loops are given those origins
and those bbox heights, and both are given the same camera path.  The only
thing that differs is the loop.

The R2-3421 tool reports per POOL (a set of instances sharing a library), not
per source mesh, because the dump does not record which library slot each tree
drew.  So this cross-check assigns every instance of a pool to ONE synthetic
source mesh, which makes `instance_variety.sweep()`'s per-mesh peak the same
quantity as the pool's peak.  That is the whole trick, and it is why this file
proves nothing about the LIBRARY arithmetic -- only about the projection, the
frustum test, the size test, the smear and the frame bookkeeping.

GROUND COVER IS DELIBERATELY EXCLUDED.  The dump voxelises it, so the two tools
would be comparing different point sets and any disagreement would be
unattributable.  The trees are exact in both.

PASS CONDITION -- THREE CLAIMS, AND THE THIRD IS A FINDING ABOUT THE REFERENCE
------------------------------------------------------------------------------
1.  `peak_covisible` agrees EXACTLY, every pool, every rung.  Not "close" --
    the same points through the same camera give the same integers, and a
    tolerance here would hide precisely the off-by-a-cell bug this exists to
    catch.  It did catch two, both in the new loop and both silent
    under-counts, and both are written up at their fix sites:

      * the cull tested RANGE against a limit derived from DEPTH, and threw
        away in-frustum trees at the edge of a wide frame (102 of 120
        comparisons wrong);
      * the running maxima were updated inside the height-bucket loop, so a
        source mesh whose instances straddle two height octaves -- which is
        every tree pool, because `instance_plants()` randomises target height
        -- had the MAX of its partial counts taken where the SUM was right
        (92 of 120 wrong, `tree:plane_L0` reading 17 against 26).

2.  `peak_covisible_sharp` is NEVER LOWER in `instance_variety.sweep()` than in
    the reference.  If it were, the new loop would be the broken one.

3.  It IS HIGHER on some pools, and that is a defect in the REFERENCE, not a
    disagreement to be split.  `r2_3421_covisible_repeats.py` tracks the
    busiest sharp frame with

        if ns > bsharp[thr]["n"]:                       # ns is a SHARP count
            bsharp[thr] = dict(n=n, f=f + 1, sharp=ns)  # n is the TOTAL

    -- comparing a sharp count against the stored frame's TOTAL.  Because total
    >= sharp always, a later frame can only displace an earlier one by beating
    its TOTAL, so the tracker reports a LOWER BOUND on the peak sharp count.
    Asserting that is not enough, so this file PROVES it: it runs the same loop
    a second time with `sharp_tracker="r2_3421"`, and requires the emulation to
    reproduce the reference's published numbers EXACTLY.  If it does, the
    mechanism is established and the gap is the reference's.

`tools/r2_3421_covisible_repeats.py` IS NOT EDITED HERE.  It is held by
another agent's lease (`r2-3421-variety`), and a lease you do not own is not
yours to release.  The defect is reported and the file is left alone.
"""
import argparse
import json
import os
import sys

import numpy as np

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_HERE = os.path.join(R2, "tools")
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
import gate_exit                                                    # noqa: E402
import instance_variety as IV                                       # noqa: E402
from r2_3421_covisible_repeats import pool_of                       # noqa: E402


def check(label, ok, detail=""):
    print("  %-4s %s%s" % ("ok" if ok else "FAIL", label,
                           ("   [%s]" % detail) if detail else ""))
    return bool(ok)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--points", required=True)
    ap.add_argument("--path", required=True)
    ap.add_argument("--covis", required=True,
                    help="r2_3421_covisible_repeats.py output for the SAME path")
    ap.add_argument("--out", required=True)
    ap.add_argument("--stride", type=int, default=1)
    a = ap.parse_args()

    z = np.load(a.points, allow_pickle=True)
    vo = z["veg_origin"].astype(np.float32)
    vb = z["veg_bbox"].astype(np.float64)
    vn = [str(s) for s in z["veg_name"]]
    vfam = np.array(["_".join(s.split("_")[:-1]) for s in vn])
    vh = (vb[:, 5] - vb[:, 2]).astype(np.float32)

    pools, pid = [], {}
    MID = np.full(len(vo), -1, np.int32)
    for fam in sorted(set(vfam)):
        pool, L, _h = pool_of(fam)
        if pool is None:
            continue
        i = pid.get(pool)
        if i is None:
            i = pid[pool] = len(pools)
            pools.append(pool)
        MID[vfam == fam] = i
    keep = MID >= 0
    P, H, MID = vo[keep], vh[keep], MID[keep]
    print("cross-checking %d discrete plants over %d pools, %s\n"
          % (len(P), len(pools), os.path.relpath(a.path, R2)))

    sw = IV.sweep(P, H, MID, len(pools), a.path, stride=a.stride,
                  progress=False)
    print("\nsecond pass, emulating the reference's busiest-sharp-frame "
          "tracker ...")
    em = IV.sweep(P, H, MID, len(pools), a.path, stride=a.stride,
                  progress=False, sharp_tracker="r2_3421")

    ref = {r["pool"]: r for r in json.load(open(a.covis))["pools"]}
    rows = []
    missing = [p for p in pools if p not in ref]
    n_pk_bad = n_sh_low = n_sh_high = n_em_bad = 0
    for i, pool in enumerate(pools):
        r = ref.get(pool)
        if r is None:
            continue
        for thr in IV.RECOG_PX_LADDER:
            k = "px%d" % int(thr)
            mine_pk = int(sw["peak"][thr][i])
            mine_sh = int(sw["sharp"][thr][i])
            emu_sh = int(em["sharp"][thr][i])
            # the reference stores voxel-scaled floats; trees are scale 1.0
            ref_pk = int(round(r[k]["peak_covisible"]))
            ref_sh = int(round(r[k]["peak_covisible_sharp"]))
            n_pk_bad += mine_pk != ref_pk
            n_sh_low += mine_sh < ref_sh
            n_sh_high += mine_sh > ref_sh
            n_em_bad += emu_sh != ref_sh
            rows.append({"pool": pool, "px": int(thr),
                         "iv_peak": mine_pk, "ref_peak": ref_pk,
                         "iv_sharp": mine_sh, "ref_sharp": ref_sh,
                         "emulated_ref_sharp": emu_sh,
                         "iv_sharp_frame": int(sw["sharp_f"][thr][i]),
                         "ref_sharp_frame": r[k]["sharp_frame"]})

    print("\n%-22s%5s%9s%9s%9s%9s%9s" % ("pool", "px", "iv covis", "ref covis",
                                         "iv sharp", "ref sh", "emul sh"))
    for r in sorted(rows, key=lambda r: -(r["iv_sharp"] - r["ref_sharp"]))[:16]:
        print("%-22s%5d%9d%9d%9d%9d%9d   %s"
              % (r["pool"], r["px"], r["iv_peak"], r["ref_peak"],
                 r["iv_sharp"], r["ref_sharp"], r["emulated_ref_sharp"],
                 "" if r["iv_sharp"] == r["ref_sharp"] else "<< ref low"))

    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    json.dump({"points": os.path.relpath(a.points, R2),
               "path": os.path.relpath(a.path, R2),
               "instances": int(len(P)), "pools": len(pools),
               "pools_missing_from_reference": missing,
               "comparisons": len(rows),
               "peak_disagreements": n_pk_bad,
               "sharp_lower_than_reference": n_sh_low,
               "sharp_higher_than_reference": n_sh_high,
               "emulation_disagreements": n_em_bad,
               "rows": rows}, open(a.out, "w"), indent=1)
    print("\nwrote %s\n" % a.out)

    ok = True
    ok &= check("CLAIM 1  peak_covisible agrees EXACTLY on all %d comparisons"
                % len(rows), n_pk_bad == 0, "%d disagree" % n_pk_bad)
    ok &= check("CLAIM 2  instance_variety's sharp count is NEVER lower than "
                "the reference's", n_sh_low == 0, "%d lower" % n_sh_low)
    ok &= check("CLAIM 3  emulating the reference's tracker reproduces its "
                "published numbers EXACTLY, so the gap is its tracker",
                n_em_bad == 0, "%d differ" % n_em_bad)
    print("\n  and the gap is real: the reference under-reports peak sharp on "
          "%d of %d comparisons." % (n_sh_high, len(rows)))
    if missing:
        print("  NOTE %d pool(s) are not in the reference report: %s"
              % (len(missing), ", ".join(missing)))

    if not ok:
        return gate_exit.verdict("SWEEP_CROSSCHECK_FAIL")
    return gate_exit.verdict("SWEEP_CROSSCHECK_OK")


if __name__ == "__main__":
    gate_exit.guard(main, tool="sweep_crosscheck")
