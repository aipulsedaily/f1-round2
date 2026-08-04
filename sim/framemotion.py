#!/usr/bin/env python3
"""DID THE FRAME BREAK?  Asked of a bake table, and asked the same way twice.

    .venv/bin/python sim/framemotion.py sim/tmp/breach_full_r2281.npz \\
        --ref sim/tmp/breach_full_m1.npz --out sim/out/framemotion_r2281.json

`motion_report` in the builder answers "did anything move", over 3,948 bodies
dominated by 3,796 shards, and R2-267 is what happens when the frame's answer
is read out of a statistic that is 96 % glass: "mullion 5 travelling 4.43 m"
was true and was a statement about two segments out of eight.

So this reports the frame ONLY, per body, and it reports the thing the shipped
bake got wrong, which is not travel at all but SEPARATION.  A transom that has
lost its screws does not have to go anywhere: it can hang off its other end,
or sit on the shard pile.  What tells you the joint let go is that the two
bodies it joined are no longer where they were relative to each other.

    joint separation = || (a(t) - b(t)) - (a(0) - b(0)) ||

which is zero for a rigid pair however far the pair travels together, and
which is therefore the measurement that does not care whether the wall fell
over or was pushed.  Each transom end is matched to the mullion segment
`build_breach_sim._seg_at` bolted it to, by the same nearest-centre rule, so
this asks about the joints that exist rather than the ones that look likely.
"""

import argparse
import json
import os
import re
import sys

import numpy as np

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(R2, "sim"))

# WHERE "BROKEN" SITS, AND WHY IT IS NOT 20 mm.
#
# My first value was 0.020 m, reasoned as "four times the collision margin plus
# the kerf".  Run against the SHIPPED table it reported 18 broken joints of 95
# and all six of mullion 5's transom ends broken -- in a bake whose transom
# constraints are at 499 kN and cannot possibly have broken.  A Bullet FIXED
# constraint is a soft constraint: at 24 sequential-impulse iterations it holds
# to tens of millimetres under load, not to zero, and 20 mm is inside that.
#
# The shipped table brackets this for me and the bracket is wide open:
#
#     largest separation on a joint that DID NOT break     0.0725 m
#     smallest separation on a joint that DID break        1.3605 m
#                                                          (MUL05_S00->S01)
#
# a factor of nineteen with nothing in it.  0.25 m sits 3.4x above the
# compliance and 5.4x below the real break, and `separation_histogram` in the
# output prints the whole distribution every run so that if a future bake ever
# fills that gap in, it is visible rather than silently classified.
BROKEN_M = 0.25


def load(p):
    d = np.load(p, allow_pickle=True)
    return d["loc"], d["quat"], [str(x) for x in d["names"]], d["world_t"]


def frame_index(names):
    idx = {}
    for i, nm in enumerate(names):
        if nm.startswith("MUL") or nm.startswith("TRN"):
            idx[nm] = i
    return idx


def seg_centres(iface, uid, nseg=8):
    st = {r["uid"]: r for r in iface["stations"]}[uid]
    z0, z1 = st["foot_z"], st["head_z"]
    return [(z0 + (z1 - z0) * (k + 0.5) / nseg) for k in range(nseg)]


def seg_at(centres, z):
    return int(np.argmin([abs(c - z) for c in centres]))


def travel(loc, i):
    d = loc[:, i, :] - loc[0, i, :]
    return float(np.linalg.norm(d, axis=1).max())


def separation(loc, ia, ib):
    r = (loc[:, ia, :] - loc[:, ib, :]) - (loc[0, ia, :] - loc[0, ib, :])
    return float(np.linalg.norm(r, axis=1).max())


def analyse(path, iface, label):
    loc, quat, names, wt = load(path)
    idx = frame_index(names)
    out = {"table": os.path.basename(path), "label": label,
           "frames": int(loc.shape[0]), "frame_bodies": len(idx)}

    # ---- travel, by member ------------------------------------------------ #
    mul, trn = {}, {}
    for nm, i in idx.items():
        t = travel(loc, i)
        (mul if nm.startswith("MUL") else trn)[nm] = round(t, 4)
    out["max_travel_any_mullion_body_m"] = round(max(mul.values()), 4) if mul else 0.0
    out["max_travel_any_transom_body_m"] = round(max(trn.values()), 4) if trn else 0.0
    out["mullion_bodies_over_0p5m"] = sorted(
        [k for k, v in mul.items() if v > 0.5])
    out["transom_bodies_over_0p5m"] = sorted(
        [k for k, v in trn.items() if v > 0.5])
    out["worst_travel"] = dict(sorted(
        list(mul.items()) + list(trn.items()),
        key=lambda kv: -kv[1])[:14])

    # ---- the joints, by separation ---------------------------------------- #
    st = iface["stations"]
    ys = [r["y"] for r in st]
    zs = [ln["z"] for ln in iface["transom_landings"]["lines"]]
    joints = {}
    for zi, z in enumerate(zs):
        for b in range(len(st) - 1):
            tn = "TRN_z%d_b%02d" % (zi, b)
            if tn not in idx:
                continue
            for side, uid in (("a", st[b]["uid"]), ("b", st[b + 1]["uid"])):
                cen = seg_centres(iface, uid)
                k = seg_at(cen, z)
                mn = "MUL%02d_S%02d" % (uid, k)
                if mn not in idx:
                    # an intact mullion is one body, S00
                    mn = "MUL%02d_S00" % uid
                    if mn not in idx:
                        continue
                joints["%s->%s" % (tn, mn)] = round(
                    separation(loc, idx[tn], idx[mn]), 5)
    # mullion segment-to-segment and the head
    for uid in sorted({r["uid"] for r in st}):
        segs = [n for n in idx if n.startswith("MUL%02d_S" % uid)
                and not n.endswith("_P")]
        segs.sort()
        for a, b in zip(segs, segs[1:]):
            joints["%s->%s" % (a, b)] = round(
                separation(loc, idx[a], idx[b]), 5)

    out["joints"] = joints
    out["joints_broken"] = {k: v for k, v in joints.items() if v > BROKEN_M}
    out["n_joints"] = len(joints)
    out["n_joints_broken"] = len(out["joints_broken"])
    # the gap BROKEN_M lives in, printed every run rather than assumed
    vals = sorted(joints.values())
    below = [v for v in vals if v <= BROKEN_M]
    above = [v for v in vals if v > BROKEN_M]
    out["separation_histogram"] = dict(
        n=len(vals),
        largest_below_threshold_m=round(below[-1], 5) if below else None,
        smallest_above_threshold_m=round(above[0], 5) if above else None,
        threshold_m=BROKEN_M,
        gap_factor=round(above[0] / below[-1], 1)
        if below and above and below[-1] > 0 else None,
        deciles=[round(v, 5) for v in np.percentile(vals, range(0, 101, 10))])

    # ---- the question the closing frame asks ------------------------------ #
    # mullion 5's column above the car: segments S02..S07 and the six transom
    # ends that hold them up.
    col = ["MUL05_S%02d" % k for k in range(2, 8)]
    out["mullion5_column"] = {c: mul.get(c, None) for c in col}
    out["mullion5_column_max_travel_m"] = round(
        max([mul.get(c, 0.0) for c in col]), 4)
    ends = {k: v for k, v in joints.items() if "MUL05_S" in k
            and k.startswith("TRN")}
    out["mullion5_transom_ends"] = ends
    out["mullion5_transom_ends_broken"] = sum(
        1 for v in ends.values() if v > BROKEN_M)
    out["mullion5_transom_ends_total"] = len(ends)

    # ---- the three lattice lines the closing frame renders ----------------- #
    for zi in range(len(zs)):
        bodies = {k: v for k, v in trn.items()
                  if k.startswith("TRN_z%d_" % zi)}
        out["line_z%d_max_travel_m" % zi] = round(max(bodies.values()), 4) \
            if bodies else 0.0
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("npz")
    ap.add_argument("--ref", default="")
    ap.add_argument("--out", default="")
    ap.add_argument("--iface", default=os.path.join(
        R2, "world", "items", "mullion_intact_interface.json"))
    a = ap.parse_args()
    with open(a.iface) as fh:
        iface = json.load(fh)

    now = analyse(a.npz, iface, "after")
    doc = {"after": now}
    if a.ref and os.path.exists(a.ref):
        before = analyse(a.ref, iface, "before")
        n = min(before["frames"], now["frames"])
        doc["before"] = before
        doc["comparable_frames"] = n
        doc["delta"] = dict(
            max_transom_travel_m=[before["max_travel_any_transom_body_m"],
                                  now["max_travel_any_transom_body_m"]],
            mullion5_column_max_travel_m=[
                before["mullion5_column_max_travel_m"],
                now["mullion5_column_max_travel_m"]],
            joints_broken=[before["n_joints_broken"], now["n_joints_broken"]],
            mullion5_transom_ends_broken=[
                before["mullion5_transom_ends_broken"],
                now["mullion5_transom_ends_broken"]])
        if before["frames"] != now["frames"]:
            doc["WARNING"] = (
                "the two tables are %d and %d frames long; travel is a "
                "running maximum so the shorter one is a LOWER BOUND on the "
                "longer one's number and they are not directly comparable"
                % (before["frames"], now["frames"]))

    print(json.dumps(doc, indent=1, default=float))
    if a.out:
        os.makedirs(os.path.dirname(a.out), exist_ok=True)
        with open(a.out, "w") as fh:
            json.dump(doc, fh, indent=1, default=float)
        print("wrote %s" % a.out)
    print("STAGE RESULT: framemotion  frame_joints_broken=%d of %d  "
          "mullion5_transom_ends_broken=%d of %d  "
          "mullion5_column_max_travel=%.3f m"
          % (now["n_joints_broken"], now["n_joints"],
             now["mullion5_transom_ends_broken"],
             now["mullion5_transom_ends_total"],
             now["mullion5_column_max_travel_m"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
