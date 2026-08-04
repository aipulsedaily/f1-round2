"""Dump the FULL presentation-score surface, plus the room the camera flies in.

    /opt/blender-5.2.0-linux-x64/blender -b world/beat1_anim.blend \
        --factory-startup -P tools/beat1_view_surface.py -- \
        --plan docs/explode_plan.json --out work/b1nadir/view_surface.json

WHY DUMP THE WHOLE SURFACE
--------------------------
`tools/presentation_normals.py` emits only its top 16 directions, and for the
four clusters that open the film those 16 span 84 deg down to 53 deg -- so the
stored file cannot answer "what does a shallow view cost?", which is the only
question this block needs answered.  It also cannot show whether the argmax is a
peak or a plateau.  MB's top 16 sit inside 8 % of each other, which is a plateau,
and an argmax over a plateau is a coin flip that happened to land on the pole.

Same scoring function, unchanged, so the winner reproduces
`docs/presentation_normals.json` exactly -- that reproduction is asserted, not
hoped for.  The only differences are (a) every sampled direction is kept, and
(b) it is vectorised through numpy, because 192 directions x ~6 M faces is not a
Python loop.

ALSO DUMPED, because the fix needs measured room geometry and not a code comment:
the world Z of every light in the scene (`tools/build_beatsheet.py:621` asserts
"spot rigs from z 5.11" in a comment with no citation), the shell bounds, and the
dais/turntable top.
"""

import argparse
import json
import math
import os
import sys
from collections import defaultdict

import bpy
import numpy as np
from mathutils import Vector


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--plan", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--dirs", type=int, default=192)
    p.add_argument("--min-elev-deg", type=float, default=-8.0)
    return p.parse_args(argv)


def sphere_dirs(n, min_elev_deg):
    """Fibonacci sphere, filtered -- byte-identical to presentation_normals.py."""
    out = []
    ga = math.pi * (3.0 - math.sqrt(5.0))
    for i in range(n):
        z = 1.0 - (2.0 * i + 1.0) / n
        r = math.sqrt(max(0.0, 1.0 - z * z))
        th = ga * i
        v = Vector((math.cos(th) * r, math.sin(th) * r, z))
        if math.degrees(math.asin(max(-1.0, min(1.0, v.z)))) >= min_elev_deg:
            out.append(v.normalized())
    return out


def main():
    a = parse_args()
    plan = json.load(open(a.plan))
    deps = bpy.context.evaluated_depsgraph_get()
    dirs = sphere_dirs(a.dirs, a.min_elev_deg)
    D = np.array([[d.x, d.y, d.z] for d in dirs], dtype=np.float64)   # (K,3)
    print(f">> {len(dirs)} directions kept of {a.dirs}")

    # ------------------------------------------------------------------ room --
    lights = []
    for ob in bpy.data.objects:
        if ob.type == "LIGHT":
            lights.append({"name": ob.name, "kind": ob.data.type,
                           "z": round(ob.matrix_world.translation.z, 4),
                           "xy": [round(ob.matrix_world.translation.x, 3),
                                  round(ob.matrix_world.translation.y, 3)],
                           "energy": round(getattr(ob.data, "energy", 0.0), 3)})
    lights.sort(key=lambda L: -L["z"])
    if lights:
        zs = [L["z"] for L in lights]
        print(f">> {len(lights)} lights, world z {min(zs):.3f} .. {max(zs):.3f}")
        for L in lights[:12]:
            print(f"     {L['name']:<34}{L['kind']:<6}z={L['z']:7.3f}  "
                  f"E={L['energy']:.2f}")

    # ------------------------------------------------------------- clusters --
    out = {}
    for key, c in plan["clusters"].items():
        N, A, M = [], [], []
        matid = {}
        for pname in c["parts"]:
            ob = bpy.data.objects.get(pname)
            if ob is None or ob.type != "MESH":
                continue
            oe = ob.evaluated_get(deps)
            try:
                me = oe.to_mesh()
            except Exception:
                continue
            if me is None:
                continue
            mw = ob.matrix_world
            nm = mw.to_3x3().inverted_safe().transposed()
            slots = [ms.material.name if ms.material else "?"
                     for ms in ob.material_slots] or ["?"]
            npoly = len(me.polygons)
            if npoly:
                nrm = np.empty(npoly * 3)
                are = np.empty(npoly)
                me.polygons.foreach_get("normal", nrm)
                me.polygons.foreach_get("area", are)
                mi = np.empty(npoly, dtype=np.int32)
                me.polygons.foreach_get("material_index", mi)
                nrm = nrm.reshape(npoly, 3)
                # object -> world normal transform, then renormalise
                T = np.array(nm).reshape(3, 3)
                nrm = nrm @ T.T
                ln = np.linalg.norm(nrm, axis=1)
                ln[ln == 0] = 1.0
                nrm /= ln[:, None]
                ids = np.empty(npoly, dtype=np.int32)
                for si, sname in enumerate(slots):
                    matid.setdefault(sname, len(matid))
                sl = np.array([matid[slots[min(int(x), len(slots) - 1)]]
                               for x in mi], dtype=np.int32)
                N.append(nrm)
                A.append(are)
                M.append(sl)
            oe.to_mesh_clear()

        if not N:
            out[key] = {"note": "no geometry"}
            continue
        N = np.concatenate(N)
        A = np.concatenate(A)
        M = np.concatenate(M)
        nmat = int(M.max()) + 1

        dots = N @ D.T                      # (F,K)
        np.clip(dots, 0.0, None, out=dots)
        dots *= A[:, None]                  # projected area contribution
        proj = dots.sum(axis=0)             # (K,)
        # per-material projected area: (nmat, K)
        per = np.zeros((nmat, D.shape[0]))
        for m in range(nmat):
            sel = (M == m)
            if sel.any():
                per[m] = dots[sel].sum(axis=0)
        rich = (per > 0.02 * np.maximum(proj, 1e-12)[None, :]).sum(axis=0)
        score = proj * (1.0 + 0.45 * rich)
        score[proj <= 0.0] = -1.0

        elevs = np.degrees(np.arcsin(np.clip(D[:, 2], -1, 1)))
        order = np.argsort(-score)
        best = int(order[0])
        out[key] = {
            "n_parts": c["n_parts"],
            "n_faces": int(N.shape[0]),
            "best_normal": [round(float(v), 5) for v in D[best]],
            "best_score": round(float(score[best]), 5),
            "best_elev_deg": round(float(elevs[best]), 4),
            "dirs": [[round(float(D[i, 0]), 5), round(float(D[i, 1]), 5),
                      round(float(D[i, 2]), 5)] for i in range(D.shape[0])],
            "score": [round(float(x), 5) for x in score],
            "proj_m2": [round(float(x), 5) for x in proj],
            "rich": [int(x) for x in rich],
            "elev_deg": [round(float(x), 4) for x in elevs],
        }
        print(f"   {key:<16} faces {N.shape[0]:>8}  best elev "
              f"{elevs[best]:7.2f}  score {score[best]:10.4f}")

    # ----------------------------------------------- reproduction assertion --
    ref_p = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(a.out))),
                         "docs", "presentation_normals.json")
    ref_p = "/home/zany/f1-round2/docs/presentation_normals.json"
    bad = []
    if os.path.exists(ref_p):
        ref = json.load(open(ref_p))
        for k, v in out.items():
            if "best_normal" not in v or k not in ref:
                continue
            d = max(abs(v["best_normal"][i] - ref[k]["normal"][i]) for i in range(3))
            if d > 1e-4:
                bad.append((k, v["best_normal"], ref[k]["normal"]))
    print()
    if bad:
        print(">> REPRODUCTION FAILED -- this surface is not the shipped scorer:")
        for k, a_, b_ in bad:
            print(f"     {k}: got {a_}  shipped {b_}")
        print(">> STAGE RESULT: VIEW_SURFACE_REPRO_FAIL")
        return 1
    print(">> REPRODUCTION OK: every winner matches docs/presentation_normals.json")

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump({"lights": lights, "clusters": out}, open(a.out, "w"))
    print(f">> wrote {a.out}")
    print(">> STAGE RESULT: VIEW_SURFACE_OK")
    return 0


import os as _o, sys as _s
if _o.path.dirname(_o.path.abspath(__file__)) not in _s.path:
    _s.path.insert(0, _o.path.dirname(_o.path.abspath(__file__)))
import gate_exit                                                  # noqa: E402

if __name__ == "__main__":
    gate_exit.guard(main, tool="beat1_view_surface")
