#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
r2366_geometry_unchanged.py — prove the paving repair moved NO VERTEX.

R2-366 is a material change. It should therefore be provable that the two arms'
GEOMETRY is bit-identical, and that claim is worth making because this project
has been bitten twice by the converse: `assembly6` had every module summary
bit-identical to `assembly5` and one object had still moved 3.19 m.

**A summary that does not change is not evidence that geometry did not move.**
So this does not compare counts. It compares a sha256 over every vertex
coordinate of every mesh object, in name order, at full float precision — the
per-object fingerprint that found `BR_Transit_NorthWall` when the summaries could
not. Counts are printed too, but they are not the evidence.

It also asserts the MATERIALS did change, in the same run. A geometry null is
only interesting alongside a material non-null; on its own it is equally
consistent with nothing having happened at all, which is this log's most
frequently mis-diagnosed result.

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P tools/r2366_geometry_unchanged.py -- --a A.blend --b B.blend

Blender 5.2 exits 0 on an uncaught script exception; judge on `STAGE RESULT`.
"""
import argparse
import hashlib
import json
import os
import sys

import bpy
import numpy as np


def fingerprint(path):
    bpy.ops.wm.open_mainfile(filepath=path)
    per = {}
    tot = hashlib.sha256()
    nv = 0
    for ob in sorted(bpy.data.objects, key=lambda o: o.name):
        if ob.type != 'MESH' or ob.data is None:
            continue
        n = len(ob.data.vertices)
        co = np.empty(n * 3, dtype=np.float64)
        ob.data.vertices.foreach_get("co", co)
        # the WORLD position, so an object that only moved is still caught
        m = np.array(ob.matrix_world, dtype=np.float64)
        p = co.reshape(-1, 3)
        w = p @ m[:3, :3].T + m[:3, 3]
        h = hashlib.sha256(np.ascontiguousarray(w).tobytes()).hexdigest()
        per[ob.name] = dict(verts=n, polys=len(ob.data.polygons), sha=h)
        tot.update(ob.name.encode())
        tot.update(h.encode())
        nv += n
    mats = {}
    for m in sorted(bpy.data.materials, key=lambda x: x.name):
        if not m.node_tree:
            mats[m.name] = "no-nodes"
            continue
        # a stable digest of the graph: node types, and every unlinked default
        parts = []
        for nd in sorted(m.node_tree.nodes, key=lambda n: n.name):
            parts.append(nd.bl_idname + "|" + nd.name)
            for sk in nd.inputs:
                if sk.links:
                    parts.append(sk.name + "=<linked>")
                    continue
                try:
                    v = sk.default_value
                    v = tuple(v) if hasattr(v, "__len__") else v
                except Exception:                            # noqa: BLE001
                    v = "?"
                parts.append("%s=%r" % (sk.name, v))
        for lk in m.node_tree.links:
            parts.append("%s.%s->%s.%s" % (lk.from_node.name,
                                           lk.from_socket.name,
                                           lk.to_node.name, lk.to_socket.name))
        mats[m.name] = hashlib.sha256("\n".join(parts).encode()).hexdigest()
    return dict(total=tot.hexdigest(), verts=nv, objects=per, materials=mats)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True)
    ap.add_argument("--b", required=True)
    ap.add_argument("--json", default=None)
    a = ap.parse_args(argv)

    A = fingerprint(a.a)
    B = fingerprint(a.b)

    print("A %s  %d mesh objects, %d verts" % (os.path.basename(a.a),
                                               len(A["objects"]), A["verts"]))
    print("B %s  %d mesh objects, %d verts" % (os.path.basename(a.b),
                                               len(B["objects"]), B["verts"]))
    print("\nGEOMETRY sha256 over every world-space vertex, in name order")
    print("  A %s" % A["total"])
    print("  B %s" % B["total"])
    geo_same = A["total"] == B["total"]
    print("  -> %s" % ("IDENTICAL" if geo_same else "DIFFERENT"))

    moved = [n for n in set(A["objects"]) | set(B["objects"])
             if A["objects"].get(n, {}).get("sha")
             != B["objects"].get(n, {}).get("sha")]
    if moved:
        print("\n  objects whose vertices differ (%d):" % len(moved))
        for n in sorted(moved)[:20]:
            print("    %s" % n)

    changed = sorted(n for n in set(A["materials"]) | set(B["materials"])
                     if A["materials"].get(n) != B["materials"].get(n))
    print("\nMATERIALS whose node graph differs: %d of %d"
          % (len(changed), len(set(A["materials"]) | set(B["materials"]))))
    for n in changed:
        print("    %s" % n)

    want = {"A_ConcSlab", "A_ConcApron", "A_ForecourtSlab"}
    got = set(changed)
    ok = geo_same and want <= got
    if a.json:
        os.makedirs(os.path.dirname(a.json) or ".", exist_ok=True)
        json.dump(dict(geometry_identical=geo_same, moved=moved,
                       materials_changed=changed,
                       a_total=A["total"], b_total=B["total"]),
                  open(a.json, "w"), indent=1)
    print("\nSTAGE RESULT: r2366_geometry_unchanged %s "
          "(geometry %s, %d materials changed, all three paving %s)"
          % ("PASS" if ok else "FAIL",
             "identical" if geo_same else "MOVED", len(changed),
             "present" if want <= got else "MISSING %s" % sorted(want - got)))
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        import traceback
        traceback.print_exc()
        print("STAGE RESULT: r2366_geometry_unchanged FAIL (uncaught exception)")
        sys.exit(1)
