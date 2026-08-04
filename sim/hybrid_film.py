#!/usr/bin/env python3
"""A DIAGNOSTIC film table: one bake's FRAME on another bake's GLASS.

    .venv/bin/python sim/hybrid_film.py \\
        --frame-from sim/out/breach_film.npz \\
        --glass-from sim/out/breach_film_R6_SHIPPED.npz \\
        --out sim/out/breach_film_FRAMEONLY.npz

WHAT THIS IS FOR, AND WHY IT IS NOT A DELIVERY
==============================================
The re-bake at the derived thresholds does two things at once.  It takes the
east frame apart -- which is what it was for, and which R2-289 shows happens
across the whole defensible threshold band.  And it lets the kinematic car
proxy plough the unrestrained glass field 88 m down the forecourt (R2-290),
which is a second defect the first correction UNMASKED rather than caused.

Those two land on top of each other in the closing frame, and the second one
sits BETWEEN the camera and the wall, so the wound cannot be measured through
it.  This table answers the question the job was actually asked -- *if the
frame comes apart the way the corrected solver says it does, does the aperture
read at 595 m?* -- by putting the corrected frame on the shipped glass.

**IT IS NOT SHIPPABLE AND CANNOT BECOME SO.**  Its glass and its frame come
from two different solves, so the shards are not where that frame would have
put them, and no single physical run produces it.  It is the same kind of
object as `film14_breach_r6_DEMO.blend` and it is marked the same way: any
scene built from it carries `DIAGNOSTIC_DO_NOT_SHIP` in its filename, and this
module refuses to write to a path that does not say so.

WHAT IT PRESERVES
=================
Both tables come from the same build -- same 3,948 bodies in the same order,
same names, same fracture plan, same seed -- so the merge is per-body and
exact.  It is checked, not assumed: the name arrays must be identical or this
refuses.  `release` is taken per body from whichever table that body's motion
came from, because `eastframe.plan()` reads `release` to decide which members
to replace, and a frame body carrying the glass table's release frame would be
partitioned as if it had never moved.
"""

import argparse
import os
import sys

import numpy as np


def is_frame_body(nm):
    return nm.startswith("MUL") or nm.startswith("TRN")


def load(path):
    z = np.load(path, allow_pickle=False)
    cnt = z["key_count"].astype(int)
    off = np.concatenate([[0], np.cumsum(cnt)])
    return dict(cnt=cnt, off=off, kf=z["key_frame"].astype(int),
                kl=z["key_loc"], kq=z["key_quat"],
                rel=z["release"].astype(int), span=z["span"].astype(int),
                names=[str(x) for x in z["names"]])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frame-from", required=True)
    ap.add_argument("--glass-from", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    if "DO_NOT_SHIP" not in os.path.basename(a.out).upper() and \
            "FRAMEONLY" not in os.path.basename(a.out).upper():
        raise SystemExit(
            "REFUSING: %r does not name itself as a diagnostic.  This table "
            "mixes two solves and must not be mistaken for a bake."
            % os.path.basename(a.out))

    F, G = load(a.frame_from), load(a.glass_from)
    if F["names"] != G["names"]:
        raise SystemExit(
            "REFUSING: the two tables do not have identical body lists (%d vs "
            "%d names, first difference at %s).  A per-body merge across "
            "different builds would silently pair the wrong bodies."
            % (len(F["names"]), len(G["names"]),
               next((i for i, (x, y) in enumerate(zip(F["names"], G["names"]))
                     if x != y), None)))
    if not np.array_equal(F["span"], G["span"]):
        raise SystemExit("REFUSING: the two tables cover different film spans "
                         "%s vs %s" % (F["span"], G["span"]))

    names = F["names"]
    take_frame = np.array([is_frame_body(n) for n in names])
    cnt, kf, kl, kq, rel = [], [], [], [], []
    n_frame = n_glass = 0
    for j, nm in enumerate(names):
        S = F if take_frame[j] else G
        s, e = S["off"][j], S["off"][j + 1]
        cnt.append(int(S["cnt"][j]))
        kf.append(S["kf"][s:e])
        kl.append(S["kl"][s:e])
        kq.append(S["kq"][s:e])
        rel.append(int(S["rel"][j]))
        if take_frame[j]:
            n_frame += 1
        else:
            n_glass += 1

    np.savez_compressed(
        a.out,
        key_count=np.asarray(cnt, np.int32),
        key_frame=np.concatenate(kf).astype(np.int32),
        key_loc=np.concatenate(kl).astype(np.float32),
        key_quat=np.concatenate(kq).astype(np.float32),
        release=np.asarray(rel, np.int32),
        span=F["span"].astype(np.int32),
        names=np.asarray(names))

    print("frame bodies from %s: %d" % (os.path.basename(a.frame_from),
                                        n_frame))
    print("glass bodies from %s: %d" % (os.path.basename(a.glass_from),
                                        n_glass))
    print("wrote %s (%.1f MB)" % (a.out, os.path.getsize(a.out) / 1e6))

    # read it back and prove the merge did what it says
    H = load(a.out)
    bad = []
    for j, nm in enumerate(names):
        S = F if is_frame_body(nm) else G
        s, e = S["off"][j], S["off"][j + 1]
        hs, he = H["off"][j], H["off"][j + 1]
        if not (np.array_equal(H["kf"][hs:he], S["kf"][s:e])
                and np.allclose(H["kl"][hs:he], S["kl"][s:e])
                and H["rel"][j] == S["rel"][j]):
            bad.append(nm)
    print("STAGE RESULT: hybrid %s  (%d frame + %d glass bodies, %d "
          "mismatches on readback)"
          % ("OK" if not bad else "FAIL", n_frame, n_glass, len(bad)))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
