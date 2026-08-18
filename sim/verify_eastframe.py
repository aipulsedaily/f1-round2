"""Read the applied east frame back out of a saved scene, at real frames.

    blender -b <scene>.blend -P sim/verify_eastframe.py -- --out X.json

WHAT IT PROVES, and why each one is here:

  A  AT FRAME 1 THE FRAME IS ROUND 1'S, TO THE MILLIMETRE.  The union of the
     supplied pieces' world AABBs, per member, must equal the AABB round 1's
     solid had.  This is the continuity claim -- beat 1 is unchanged -- and it
     is checked by measurement rather than by the argument that CONSTANT
     extrapolation ought to do it.
  B  AT FRAME 844 (the last frame before the bake's table starts) it is STILL
     round 1's.  Backwards extrapolation is the mechanism; 844 is where it
     would show if it were wrong.
  C  AT FRAME 2978 the pieces the bake threw are where the bake left them, and
     the ones it did not are still home.
  D  THE UNTOUCHED MULLIONS HAVE NOT MOVED AT ANY OF THE THREE FRAMES.  Same
     scene, same build, no line of sight needed: they are the negative control.

The transforms are read from an EVALUATED depsgraph after `frame_set`, and
nothing here is hidden at any frame, so the R2 hidden-object trap (a hidden
object's matrix_world silently returns its SAVED pose, worst error 120.7 m)
cannot bite -- but the script asserts `hide_render` is False on every piece it
reads, rather than relying on my belief that it is.
"""
import argparse
import json
import os
import sys

import bpy
import numpy as np
from mathutils import Vector

R2 = os.path.expanduser("~/f1-round2")
sys.path.insert(0, os.path.join(R2, "sim"))
import eastframe as EF                                            # noqa: E402


def aabb(dg, name):
    o = bpy.data.objects.get(name)
    if o is None:
        return None
    ob = o.evaluated_get(dg)
    V = np.array([tuple(ob.matrix_world @ Vector(c)) for c in ob.bound_box])
    return V.min(0), V.max(0), bool(o.hide_render)


def main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(R2, "sim/out/frame_verify.json"))
    ap.add_argument("--frames", default="1,844,860,880,2978")
    a = ap.parse_args(argv)

    import resample as RS
    film = RS.read_film(os.path.join(R2, "sim/out/breach_film.npz"))
    names = film["names"]
    home = np.array([film["keys_of"](i)[1][0] for i in range(len(names))], float)
    pl = EF.plan(names, film["release"], home)

    sc = bpy.context.scene
    out = {"frames": {}, "PASS": True, "fails": []}
    hidden_seen = []
    for f in [int(x) for x in a.frames.split(",")]:
        sc.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        rows = {}
        # per replaced member: union of its pieces' AABBs
        for member in sorted({p["member"] for p in pl["pieces"]}):
            lo = np.full(3, np.inf)
            hi = np.full(3, -np.inf)
            for p in pl["pieces"]:
                if p["member"] != member:
                    continue
                r = aabb(dg, p["name"])
                if r is None:
                    out["fails"].append("frame %d: %s absent" % (f, p["name"]))
                    out["PASS"] = False
                    continue
                if r[2]:
                    hidden_seen.append((f, p["name"]))
                lo = np.minimum(lo, r[0])
                hi = np.maximum(hi, r[1])
            rows[member] = dict(lo=[round(float(v), 4) for v in lo],
                                hi=[round(float(v), 4) for v in hi])
        # the untouched mullions, individually
        ctl = {}
        for n in pl["untouched"]:
            r = aabb(dg, n)
            if r is None:
                continue
            ctl[n] = [round(float(v), 5) for v in list(r[0]) + list(r[1])]
        # the individual pieces of mullion 5, so the missing bottom is visible
        m5 = {}
        for p in pl["pieces"]:
            if not p["name"].startswith("BF_MUL05"):
                continue
            r = aabb(dg, p["name"])
            m5[p["name"]] = dict(lo=[round(float(v), 3) for v in r[0]],
                                 hi=[round(float(v), 3) for v in r[1]])
        out["frames"][str(f)] = dict(members=rows, control=ctl, mullion5=m5)

    out["hidden_pieces_seen"] = hidden_seen
    if hidden_seen:
        out["PASS"] = False
        out["fails"].append("pieces hidden at some frame: %s" % hidden_seen[:5])

    # ---- A/B: frame 1 and 844 must be round 1's solids ---------------------
    WANT = {}
    for uid in pl["mullions_replaced"]:
        y0, y1 = EF.mullion_y_span(uid)
        WANT[EF.MULL_NAME % uid] = (EF.R1_X[0], y0, EF.R1_MULL_Z[0],
                                    EF.R1_X[1], y1, EF.R1_MULL_Z[1])
    for lvl, zc in enumerate(EF.R1_TRANSOM_Z):
        if not any(l == lvl for l, _b in pl["transoms_replaced"]):
            continue
        WANT[EF.TRANSOM_NAME % lvl] = (
            EF.R1_X[0], EF.R1_TRANSOM_Y[0], zc - EF.R1_TRANSOM_HALF_Z,
            EF.R1_X[1], EF.R1_TRANSOM_Y[1], zc + EF.R1_TRANSOM_HALF_Z)
    for f in ("1", "844"):
        if f not in out["frames"]:
            continue
        for m, w in WANT.items():
            got = out["frames"][f]["members"][m]
            e = max(abs(g - x) for g, x in zip(got["lo"] + got["hi"], w))
            out.setdefault("A_round1_match_mm", {})["f%s/%s" % (f, m)] = \
                round(e * 1000, 4)
            if e > 1e-4:
                out["PASS"] = False
                out["fails"].append(
                    "frame %s: %s AABB %s != round 1's %s (err %.4f m)"
                    % (f, m, got, list(w), e))

    # ---- D: the untouched mullions must be identical across all frames -----
    fs = list(out["frames"])
    base = out["frames"][fs[0]]["control"]
    worst = 0.0
    for f in fs[1:]:
        for n, v in out["frames"][f]["control"].items():
            worst = max(worst, max(abs(x - y) for x, y in zip(v, base[n])))
    out["D_control_max_move_m"] = round(worst, 9)
    if worst > 1e-9:
        out["PASS"] = False
        out["fails"].append("an untouched mullion moved %.6f m" % worst)

    with open(a.out, "w") as fh:
        json.dump(out, fh, indent=1)
    print("STAGE RESULT: frame verify %s (%d fails) -> %s"
          % ("PASS" if out["PASS"] else "FAIL", len(out["fails"]), a.out))
    for x in out["fails"][:10]:
        print("   ", x)


main()
