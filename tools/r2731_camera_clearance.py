#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
r2731_camera_clearance.py — HOW CLOSE DOES THE R2-738 CANDIDATE CAMERA PASS TO
THE BUILT WORLD, AGAINST THE PATH THAT SHIPS?

    blender -b --factory-startup -P tools/r2731_camera_clearance.py -- --selftest
    blender -b --factory-startup -P tools/r2731_camera_clearance.py -- \
        --mods barriers,architecture --lo 2130 --hi 2240 \
        --out render/r2731/cam_clearance.json

WHY
---
R2-738's candidate drops the camera 7.5 m and swings it 20 m inboard so it
threads the bridge's clear opening.  An analytic check against
`ARCH_PontPlongee`'s own boxes says it clears that by 2.716 m against
`placement_gate`'s 1.20 m camera sphere.  **That is a statement about ONE
object.**  The camera is also lower and further inboard than authored for
~60 frames, and the question "does it hit anything else" has not been asked.

This asks it: triangle-level nearest-distance from the camera origin to every
evaluated mesh in the built world, per frame, for BOTH paths, so the answer is a
COMPARISON and not an absolute nobody can calibrate.  A candidate that passes
3 m from something the shipped path passes 3.2 m from is not a new hazard.

THE CONTROL, because a clearance gate that cannot fail is not a gate
--------------------------------------------------------------------
`--selftest` plants a known plane at a known distance from a known camera
position and requires the measured distance back, and plants one BEHIND the
camera to show the metric is a distance and not a projection.

Blender 5.2 exits 0 on an uncaught exception.  Judge on STAGE RESULT.
"""

import json
import os
import sys
import time

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

T0 = time.time()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(ROOT, "world"), os.path.join(ROOT, "tools")):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def log(m):
    print("[clr %6.1fs] %s" % (time.time() - T0, m))


def build(mods):
    for m in mods:
        log("building %s ..." % m)
        if m == "surface":
            import build_surface as B
        elif m == "barriers":
            import build_barriers as B
        elif m == "architecture":
            import build_architecture as B
        elif m == "terrain":
            import build_terrain as B
        elif m == "dressing":
            import build_dressing as B
        elif m == "items":
            import build_items as B
        else:
            raise SystemExit("unknown module %s" % m)
        B.build()
    bpy.context.view_layer.update()


def world_bvh(owner_out=None):
    """Build the world BVH.

    ADDITIVE (R2-971): if `owner_out` is a list it is filled with one owner
    object NAME per emitted triangle, parallel to the triangle list, so a
    nearest hit can be attributed to the object it came from.  Passing nothing
    keeps the original two-value return and the original behaviour.
    """
    dg = bpy.context.evaluated_depsgraph_get()
    verts, tris = [], []
    n = 0
    for ob in bpy.data.objects:
        if ob.type != 'MESH' or ob.hide_render:
            continue
        ev = ob.evaluated_get(dg)
        try:
            me = ev.to_mesh()
        except Exception:                                      # noqa: BLE001
            continue
        M = ev.matrix_world
        base = len(verts)
        verts.extend([M @ v.co for v in me.vertices])
        for poly in me.polygons:
            L = list(poly.vertices)
            for k in range(1, len(L) - 1):
                tris.append((base + L[0], base + L[k], base + L[k + 1]))
                if owner_out is not None:
                    owner_out.append(ob.name)
        ev.to_mesh_clear()
        n += 1
    log("bvh over %d objects, %d verts, %d tris" % (n, len(verts), len(tris)))
    return BVHTree.FromPolygons(verts, tris, all_triangles=True), n


def nearest(bvh, p):
    loc, _nrm, _i, d = bvh.find_nearest(Vector(p))
    return (float(d) if loc is not None else float("inf"))


def nearest_named(bvh, p, owners):
    """ADDITIVE (R2-971): nearest distance AND the name of the object the
    winning triangle came from.  `owners[i]` is the owner of triangle i."""
    loc, _nrm, i, d = bvh.find_nearest(Vector(p))
    if loc is None:
        return float("inf"), "?"
    nm = owners[i] if (owners and i is not None and 0 <= i < len(owners)) else "?"
    return float(d), nm


def load_path_json(fn):
    """ADDITIVE (R2-971): read a `{"path":[{f,p,q,lens}, ...]}` file (or a bare
    list of the same entries) into {frame: entry}."""
    with open(fn) as fh:
        doc = json.load(fh)
    rows = doc["path"] if isinstance(doc, dict) else doc
    return {int(e["f"]): e for e in rows}


def selftest():
    ok = True

    def chk(nm, cond, detail=""):
        nonlocal ok
        print("   %-44s %s  %s" % (nm, "PASS" if cond else "FAIL", detail))
        ok = ok and bool(cond)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    me = bpy.data.meshes.new("CTRL_Plane")
    me.from_pydata([(5, -9, -9), (5, 9, -9), (5, 9, 9), (5, -9, 9)], [],
                   [(0, 1, 2, 3)])
    bpy.context.scene.collection.objects.link(
        bpy.data.objects.new("CTRL_Plane", me))
    me2 = bpy.data.meshes.new("CTRL_Behind")
    me2.from_pydata([(-3, -9, -9), (-3, 9, -9), (-3, 9, 9), (-3, -9, 9)], [],
                    [(0, 1, 2, 3)])
    bpy.context.scene.collection.objects.link(
        bpy.data.objects.new("CTRL_Behind", me2))
    bpy.context.view_layer.update()
    bvh, _ = world_bvh()
    d = nearest(bvh, (0, 0, 0))
    chk("a plane 3 m BEHIND reads 3 m", abs(d - 3.0) < 1e-3, "%.6f" % d)
    d2 = nearest(bvh, (9, 0, 0))
    chk("a plane 4 m in front reads 4 m", abs(d2 - 4.0) < 1e-3, "%.6f" % d2)
    d3 = nearest(bvh, (5, 0, 0))
    chk("a point ON the plane reads 0", d3 < 1e-6, "%.6f" % d3)
    print(">> STAGE RESULT: %s"
          % ("CAM_CLEAR_SELFTEST_OK" if ok else "CAM_CLEAR_SELFTEST_FAIL"))
    return ok


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

    def opt(name, default=None):
        return argv[argv.index(name) + 1] if name in argv else default

    if "--selftest" in argv:
        sys.exit(0 if selftest() else 1)
    if not selftest():
        print(">> STAGE RESULT: CAM_CLEAR_SELFTEST_FAIL")
        return
    lo, hi = int(opt("--lo", 2130)), int(opt("--hi", 2240))
    mods = opt("--mods", "barriers,architecture").split(",")
    out = opt("--out", "render/r2731/cam_clearance.json")

    # ADDITIVE (R2-971): --cand / --base point the two curves at explicit path
    # JSON files.  Omitting them reproduces the original defaults exactly:
    # candidate = r2731_pont_camera_apply.candidate_path(),
    # base      = world/camera_rig_path.json.
    cand_fn = opt("--cand", opt("--path", None))
    base_fn = opt("--base", None)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    build(mods)
    owners = []
    bvh, nobj = world_bvh(owners)

    if cand_fn:
        cand = load_path_json(os.path.join(ROOT, cand_fn)
                              if not os.path.isabs(cand_fn) else cand_fn)
        log("candidate curve <- %s (%d frames)" % (cand_fn, len(cand)))
    else:
        import r2731_pont_camera_apply as CA
        cand = {int(e["f"]): e for e in CA.candidate_path()}
        log("candidate curve <- r2731_pont_camera_apply.candidate_path()")
    base_fn = base_fn or os.path.join("world", "camera_rig_path.json")
    base = load_path_json(os.path.join(ROOT, base_fn)
                          if not os.path.isabs(base_fn) else base_fn)
    log("shipped curve   <- %s (%d frames)" % (base_fn, len(base)))

    rows = []
    for f in range(lo, hi + 1):
        ds, ns = nearest_named(bvh, base[f]["p"], owners)
        dc, nc = nearest_named(bvh, cand[f]["p"], owners)
        rows.append(dict(f=f, shipped=round(ds, 4), candidate=round(dc, 4),
                         shipped_obj=ns, candidate_obj=nc))
    ws = min(rows, key=lambda r: r["shipped"])
    wc = min(rows, key=lambda r: r["candidate"])
    tight = [r for r in rows if r["candidate"] < 1.20]
    log("shipped   min %.3f m at f%d  (%s)"
        % (ws["shipped"], ws["f"], ws.get("shipped_obj", "?")))
    log("candidate min %.3f m at f%d  (%s)"
        % (wc["candidate"], wc["f"], wc.get("candidate_obj", "?")))
    log("frames where the candidate is inside the 1.20 m sphere: %d" % len(tight))
    for k, r in enumerate(sorted(rows, key=lambda x: x["candidate"])[:10]):
        log("  worst%3d: f%d  cand %.3f m (%s)   shipped %.3f m (%s)"
            % (k + 1, r["f"], r["candidate"], r.get("candidate_obj", "?"),
               r["shipped"], r.get("shipped_obj", "?")))
    os.makedirs(os.path.dirname(os.path.join(ROOT, out)), exist_ok=True)
    with open(os.path.join(ROOT, out), "w") as fh:
        json.dump(dict(meta=dict(tool="tools/r2731_camera_clearance.py",
                                 modules=mods, objects=nobj, lo=lo, hi=hi,
                                 sphere_m=1.20,
                                 note="nearest distance from the camera ORIGIN "
                                      "to any evaluated render-visible triangle; "
                                      "hide_render excluded because it cannot be "
                                      "hit by a lens that cannot see it"),
                       shipped_min=ws, candidate_min=wc,
                       frames_inside_sphere=[r["f"] for r in tight],
                       rows=rows), fh)
    print(">> STAGE RESULT: %s"
          % ("CAM_CLEAR_TIGHT" if tight else "CAM_CLEAR_OK"))


main()
