"""R2-3421 -- CO-VISIBLE RECOGNISABLE REPEATS: the rule's own metric.

    python3 tools/r2_3421_covisible_repeats.py \
        --points work/w2_0/retier_a10/world_points.npz \
        --path world/camera_rig_path.json --out work/r23421/covisible.json

WHY NOT TOP SHARE
=================
The red line is "no repeated assets -- one tree spammed 100 times is the named
failure".  It is policed by `tools/instance_variety.py`'s `top_share`: the
fraction of ALL realized instances taken by the commonest source mesh.  Three
things are wrong with that as a reading of the rule, and all three are
structural, not matters of where the threshold sits:

1.  `top_share` IS A WHOLE-WORLD RATIO AND THE RULE IS A SCREEN EVENT.  The
    named failure is a hundred copies you can SEE AT ONCE.  A mesh used a
    million times, never twice within sight of itself, is not it; a mesh used
    twelve times, all twelve filling one frame, is.  A ratio over the whole
    world cannot tell those apart.

2.  ITS DENOMINATOR IS DOMINATED BY GRASS.  `instance_variety.py` keys the
    family off the leading token of the emitter name, and every vegetation
    emitter in this world is named `VEG_*`, so 4.9 M grass clumps, 1.6 M grit
    pieces and every tree pool in the film are ONE family.  The commonest
    source is therefore always a grass mesh, and every tree pool is diluted by
    a factor of ~180 before it is looked at.

3.  IT CANNOT SEE A SINGLE TREE.  Trees, hedgerow trees and the avenue are
    placed by `build_terrain.instance_plants`, which makes LINKED DUPLICATE
    OBJECTS -- real scene objects sharing a mesh.  `instance_variety.py` walks
    `depsgraph.object_instances` and skips everything with `is_instance ==
    False`, which is every real object.  The 27,969 trees in this world have
    never been measured by the instrument that polices the tree rule.
    `tools/r2_3421_instance_variety_control.py` demonstrates that on a
    six-object scene.

WHAT THIS MEASURES INSTEAD
==========================
For every SOURCE POOL -- a set of instances that draw their mesh from the same
library -- and every frame:

    n_recog   instances in the frustum whose projected height is at least
              RECOG_PX pixels of the 3840x2160 delivery, i.e. big enough that
              a silhouette could be read at all
    n_sharp   those of them whose shutter smear is at most SMEAR_SHARP_PX
    cvrr      n_recog / L, the EXPECTED number of instances sharing any one of
              the pool's L library meshes that are on screen together
    cvrr_hi   the 99th-percentile busiest slot, from the binomial the uniform
              `rng.integers(0, L, n)` pick actually is

`cvrr` is what "one tree spammed 100 times" measures on this scale: the client's
own sentence is cvrr = 100.

EVERY NUMBER HERE IS AN UPPER BOUND ON WHAT IS VISIBLE, deliberately:

  * occlusion is ignored, so a tree behind a hill still counts;
  * instances differ by yaw, mirror, height, breadth and lean, so two instances
    of one mesh do not present the same silhouette -- and this counts them as
    if they did;
  * the pools merge woodland and hedgerow of the same species and LOD, because
    `build_library` hands both the SAME meshes.

A bound in that direction is safe for a red line: it can only over-report
repetition.  It is NOT safe as evidence that repetition is visible -- for that
the frames themselves are the evidence, which is why this block also renders
the ladder in `tools/r2_3421_variety_control.py` and looks at the delivery in
`tools/r2_3421_frame_repetition.py`.

THE POINT CLOUD, AND WHAT IS EXACT IN IT
========================================
`tools/build_and_dump_points.py` records trees, hedgerow trees and the avenue as
ONE ORIGIN AND ONE WORLD BBOX PER INSTANCE (`veg_origin`, `veg_bbox`, 27,969 of
them) -- exact, unsampled, with the real per-instance height.  Ground cover is a
scatter host: its BASE mesh is one vertex per clump, and the dump voxelises that
at `cell_m` = 1 m, so `VEG_grass_fescue_H` arrives as 164,884 points standing
for 1,021,524 clumps.  Grass counts here are therefore scaled by that ratio and
FLAGGED as scaled; grass heights are the emitter's own range, not a bbox.
"""
import argparse
import json
import math
import os
import sys

import numpy as np

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_HERE = os.path.join(R2, "tools")
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
import gate_exit                                                    # noqa: E402
from screen_presence import (camera_track, RES_X, RES_Y,            # noqa: E402
                             SMEAR_SHARP_PX)

SHUTTER = 0.5                 # flat 180 deg, the shipping mode since R2-037
RECOG_PX_LADDER = (32.0, 64.0, 128.0, 256.0)
RECOG_PX = 64.0               # the row the verdict is read off

# THE NAMED FAILURE, AS A NUMBER.  "one tree spammed 100 times".
SPAM_CVRR = 100.0

# ---- LIBRARY SIZES ----------------------------------------------------------
# build_terrain.build_library(rng, counts) with counts = nlod =
#   [max(2, round(v * (0.45 + 0.55 * QUAL))) for v in (8, 12, 16, 7, 7, 9)]
# and QUAL = 1.0 for a shipping build (build_terrain.py:75), so counts is
# (8, 12, 16, 7, 7, 9) exactly.  Cross-checked against
# assembly14_build.json: grass_library 55 = 5 kinds x 11.
NLOD = (8, 12, 16, 7, 7, 9)
GRASS_NLIB_H = 11
GRASS_NLIB_F = max(3, GRASS_NLIB_H // 2)

# a representative clump height per grass kind, from build_terrain.GRASS_PROF's
# `h` range.  Grass has no per-instance bbox in the dump, so the MIDPOINT is
# used and the sensitivity to it is reported.
GRASS_H = {"fescue": 0.22, "tussock": 0.46, "meadow": 0.56, "dry": 0.18,
           "reed": 0.95}
SHRUB_H = 1.3
FERN_H = 0.7
WEED_H = 0.55
STONE_H = 0.25
GRIT_H = 0.05

# VEG_grass_fescue_H arrives voxelised. verts / cells_found per emitter is read
# from the dump's own meta, never assumed.


def pool_of(name):
    """Which SOURCE POOL a family draws from, and how big that library is.

    Woodland and hedgerow of the same species and LOD share `lib[(key, lod)]`,
    and the paddock avenue is `lib[("plane", 0)]` -- the SAME eight meshes as
    every L0 plane in the world.  Merging them is the whole point: an avenue
    tree and a woodland plane that are the same mesh are a repeat whatever
    collection they live in.
    """
    if name.startswith("VEG_tree_") or name.startswith("VEG_hedge_"):
        tail = name.split("_", 2)[2]            # e.g. "oak0"
        sp, lod = tail[:-1], int(tail[-1])
        return "tree:%s_L%d" % (sp, lod), NLOD[lod], None
    if name == "VEG_avenue":
        return "tree:plane_L0", NLOD[0], None
    if name == "VEG_avenue_new":
        return "tree:sapling_L0", NLOD[0], None
    if name == "VEG_sapling":
        return "tree:sapling_L0", NLOD[0], None
    if name.startswith("VEG_shrub_"):
        lod = 1 if name.endswith("_L1") else 0
        return name, NLOD[3 + lod], SHRUB_H
    if name == "VEG_fern":
        return name, NLOD[5], FERN_H
    if name.startswith("VEG_weed_"):
        return name, max(3, NLOD[5]), WEED_H
    if name.startswith("VEG_stone_"):
        return name, max(6, NLOD[5] + 3), STONE_H
    if name.startswith("VEG_grit_"):
        return name, max(14, NLOD[5] * 2), GRIT_H
    if name.startswith("VEG_grass_"):
        kind = name.split("_")[2]
        return name, (GRASS_NLIB_H if name.endswith("_H") else GRASS_NLIB_F), \
            GRASS_H.get(kind, 0.3)
    return None, None, None


def binom_hi(n, L, q=0.99):
    """The q-quantile of the busiest of L uniform slots holding n draws.

    Normal approximation to the binomial with a Bonferroni correction over the
    L slots -- adequate at these n, and stated so nobody reads it as exact.
    """
    if n <= 0 or L <= 1:
        return float(n)
    p = 1.0 / L
    mu = n * p
    sd = math.sqrt(n * p * (1 - p))
    # z for the (1 - (1-q)/L) point of the normal
    a = 1.0 - (1.0 - q) / L
    z = 2.0 ** 0.5 * _erfinv(2.0 * a - 1.0)
    return mu + z * sd


def _erfinv(y):
    # Winitzki's approximation; good to ~2e-3 relative, which is far finer than
    # anything this quantile is used to decide.
    a = 0.147
    ln = math.log(max(1e-12, 1.0 - y * y))
    t = 2.0 / (math.pi * a) + ln / 2.0
    return math.copysign(math.sqrt(max(0.0, math.sqrt(t * t - ln / a) - t)), y)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--points", required=True)
    ap.add_argument("--path", default=os.path.join(R2, "world/camera_rig_path.json"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--stride", type=int, default=1)
    a = ap.parse_args()

    z = np.load(a.points, allow_pickle=True)
    meta = json.loads(str(z["meta"]))
    scat = {m["name"]: m for m in meta["objects"]}

    # ---- discrete plants: exact origin and exact world bbox per instance ----
    vo = z["veg_origin"].astype(np.float64)
    vb = z["veg_bbox"].astype(np.float64)
    vn = [str(s) for s in z["veg_name"]]
    # instance_plants names them "<tag>_%06d"; the family is everything before
    # the counter, exactly as screen_presence.py derives it.
    vfam = np.array(["_".join(s.split("_")[:-1]) for s in vn])
    vh = vb[:, 5] - vb[:, 2]                    # world bbox height, per instance

    # ---- ground cover: voxelised clump positions, scaled by the dump's meta --
    pts = z["pts"].astype(np.float64)
    obj = z["obj"]
    names = [str(s) for s in z["names"]]

    groups = {}       # pool -> dict(P, H, L, scale, exact, members)
    for i, nm in enumerate(names):
        if not nm.startswith("VEG_"):
            continue
        pool, L, h = pool_of(nm)
        if pool is None or h is None:
            continue
        m = obj == i
        if not m.any():
            continue
        md = scat.get(nm, {})
        sc = (md.get("verts", 0) / max(1, md.get("cells_found", 1))) \
            if md.get("cells_found") else 1.0
        g = groups.setdefault(pool, dict(P=[], H=[], L=L, scale=sc, exact=False,
                                         members=[]))
        g["P"].append(pts[m])
        g["H"].append(np.full(int(m.sum()), h))
        g["members"].append(nm)
        g["scale"] = sc
    for fam in sorted(set(vfam)):
        pool, L, _ = pool_of(fam)
        if pool is None:
            continue
        m = vfam == fam
        g = groups.setdefault(pool, dict(P=[], H=[], L=L, scale=1.0, exact=True,
                                         members=[]))
        g["P"].append(vo[m])
        g["H"].append(vh[m])
        g["members"].append(fam)
        g["exact"] = True
    for g in groups.values():
        g["P"] = np.concatenate(g["P"])
        g["H"] = np.concatenate(g["H"])

    C, Rm, s, lens, nf = camera_track(a.path)
    frames = range(0, nf - 1, a.stride)

    rows = []
    for pool in sorted(groups):
        g = groups[pool]
        P, H, L, sc = g["P"], g["H"], g["L"], g["scale"]
        # TWO maxima, not one. The frame with the most co-visible instances is
        # a FAST frame -- that is why so many are in it -- so reading the sharp
        # count off it reports 0 for every pool in the world and proves nothing.
        # `best` is the busiest frame; `bsharp` is the busiest frame among those
        # the shutter leaves resolvable, and it is the one the rule is about.
        best = {p: dict(n=0.0, f=0, sharp=0.0) for p in RECOG_PX_LADDER}
        bsharp = {p: dict(n=0.0, f=0, sharp=0.0) for p in RECOG_PX_LADDER}
        for f in frames:
            d = P - C[f]
            cam = d @ Rm[f]
            dep = -cam[:, 2]
            ok = dep > 0.05
            if not ok.any():
                continue
            inv = 1.0 / dep[ok]
            x = cam[ok, 0] * inv * s[f] + RES_X / 2
            y = -cam[ok, 1] * inv * s[f] + RES_Y / 2
            infr = (x >= 0) & (x < RES_X) & (y >= 0) & (y < RES_Y)
            if not infr.any():
                continue
            x, y = x[infr], y[infr]
            px = H[ok][infr] * s[f] * inv[infr]
            top = np.max(px)
            if top < RECOG_PX_LADDER[0]:
                continue
            # smear only for the ones that could matter
            Q = P[ok][infr]
            d1 = Q - C[f + 1]
            c1 = d1 @ Rm[f + 1]
            dp1 = -c1[:, 2]
            good = dp1 > 0.05
            sm = np.full(len(Q), 1e9)
            i1 = 1.0 / np.where(good, dp1, 1.0)
            x1 = c1[:, 0] * i1 * s[f + 1] + RES_X / 2
            y1 = -c1[:, 1] * i1 * s[f + 1] + RES_Y / 2
            sm[good] = np.hypot(x1 - x, y1 - y)[good] * SHUTTER
            for thr in RECOG_PX_LADDER:
                sel = px >= thr
                n = float(sel.sum()) * sc
                ns = float((sel & (sm <= SMEAR_SHARP_PX)).sum()) * sc
                if n > best[thr]["n"]:
                    best[thr] = dict(n=n, f=f + 1, sharp=ns)
                if ns > bsharp[thr]["n"]:
                    bsharp[thr] = dict(n=n, f=f + 1, sharp=ns)
        row = {"pool": pool, "library": L, "instances": int(round(len(P) * sc)),
               "exact_positions": bool(g["exact"]), "voxel_scale": round(sc, 3),
               "members": sorted(g["members"])}
        for thr in RECOG_PX_LADDER:
            b, bs = best[thr], bsharp[thr]
            row["px%d" % int(thr)] = {
                "peak_covisible": round(b["n"], 1), "frame": b["f"],
                "cvrr": round(b["n"] / L, 2),
                "cvrr_hi99": round(binom_hi(b["n"], L), 2),
                # the busiest SHARP frame -- a different frame, and the one the
                # rule is about, because a repeat you cannot resolve is not one
                "sharp_frame": bs["f"],
                "peak_covisible_sharp": round(bs["sharp"], 1),
                "cvrr_sharp": round(bs["sharp"] / L, 2),
                "cvrr_sharp_hi99": round(binom_hi(bs["sharp"], L), 2)}
        rows.append(row)

    key = "px%d" % int(RECOG_PX)
    rows.sort(key=lambda r: -r[key]["cvrr_sharp"])
    over = [r for r in rows if r[key]["cvrr_sharp"] >= SPAM_CVRR]

    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    json.dump({"recog_px_ladder": list(RECOG_PX_LADDER), "recog_px": RECOG_PX,
               "smear_sharp_px": SMEAR_SHARP_PX, "spam_cvrr": SPAM_CVRR,
               "res": [RES_X, RES_Y], "pools": rows,
               "over_spam_cvrr": [r["pool"] for r in over]},
              open(a.out, "w"), indent=1)

    print("CO-VISIBLE RECOGNISABLE REPEATS -- peak over %d frames, at >= %.0f px "
          "of a %dx%d frame\n" % (nf, RECOG_PX, RES_X, RES_Y))
    print("%-22s%5s%11s%9s%8s%8s%7s%9s%9s%8s" %
          ("pool", "lib", "instances", "covis", "cvrr", "cvrr99", "frame",
           "shcovis", "shcvrr", "shframe"))
    for r in rows:
        b = r[key]
        if b["peak_covisible"] <= 0:
            continue
        print("%-22s%5d%11d%9.0f%8.1f%8.1f%7d%9.0f%9.1f%8d" %
              (r["pool"], r["library"], r["instances"], b["peak_covisible"],
               b["cvrr"], b["cvrr_hi99"], b["frame"],
               b["peak_covisible_sharp"], b["cvrr_sharp"], b["sharp_frame"]))
    print("\nwrote %s" % a.out)
    if over:
        print(">> %d POOL(S) reach the named failure: %.0f co-visible SHARP "
              "instances of one source mesh" % (len(over), SPAM_CVRR))
        for r in over:
            print("     %-22s cvrr_sharp %.1f at f%d"
                  % (r["pool"], r[key]["cvrr_sharp"], r[key]["frame"]))
        return gate_exit.verdict("COVISIBLE_REPEATS_SPAM")
    return gate_exit.verdict("COVISIBLE_REPEATS_CLEAN")


if __name__ == "__main__":
    gate_exit.guard(main)
