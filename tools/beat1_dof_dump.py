"""Dump beat 1's ACTUAL per-frame camera DOF and cluster geometry from film14.blend.

    /opt/blender-5.2.0-linux-x64/blender -b render/film14.blend \
        -P tools/beat1_dof_dump.py -- --out work/b1dof/dump.json

`docs/beat_sheet.json` holds the KEYS. Blender holds what the rig actually
interpolated between them, and beat 1's focus pull spends most of its 792 frames
BETWEEN keys — so the keys cannot answer "what is in focus at f400". Neither can
`render/film14_path.json`, which stores position, quaternion and lens and no DOF
at all.

For every frame this writes: camera matrix, lens, focus_distance, aperture_fstop,
sensor width/fit, and the evaluated WORLD bounding box of each of the 15 assembly
clusters (which move — a cluster that has flown to its seat is no longer where the
explode plan put it).

Blender 5.2 exits 0 on an uncaught exception, so judge this on the STAGE RESULT
line and on nothing else.
"""

import json
import os
import sys
import traceback

import bpy
from mathutils import Vector

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
R2 = "/home/zany/f1-round2"


def arg(name, default=None):
    if name in ARGS:
        return ARGS[ARGS.index(name) + 1]
    return default


def main():
    out_path = arg("--out", os.path.join(R2, "work/b1dof/dump.json"))
    lo = int(arg("--first", "1"))
    hi = int(arg("--last", "792"))
    step = int(arg("--step", "1"))
    geom_step = int(arg("--geom-step", "4"))
    cam_name = arg("--cam", "ONER")

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    scene = bpy.context.scene
    cam = bpy.data.objects.get(cam_name)
    if cam is None:
        print("STAGE RESULT FAIL no camera named %r" % cam_name)
        return 1
    cd = cam.data

    plan = json.load(open(os.path.join(R2, "docs/explode_plan.json")))["clusters"]

    # Resolve each cluster's parts to real objects ONCE. A part name in the plan
    # may be a prefix of several objects in the film (the film is assembly9 plus
    # 945 round-1 objects, ITEM-PRESENCE-CENSUS 1.4), so match exact first and
    # fall back to prefix, and REPORT the miss rate rather than absorbing it.
    by_name = {o.name: o for o in bpy.data.objects}
    resolved, misses = {}, {}
    for cl, spec in plan.items():
        objs, miss = [], []
        for p in spec["parts"]:
            o = by_name.get(p)
            if o is not None:
                objs.append(o)
                continue
            hits = [x for n, x in by_name.items() if n == p or n.startswith(p + ".")]
            if hits:
                objs.extend(hits)
            else:
                miss.append(p)
        resolved[cl] = objs
        misses[cl] = miss
    print(">> cluster resolution:")
    for cl in sorted(plan):
        print("   %-14s plan %3d parts -> %4d objects, %d unresolved"
              % (cl, len(plan[cl]["parts"]), len(resolved[cl]), len(misses[cl])))
    total_miss = sum(len(m) for m in misses.values())

    frames, geom = [], {}
    dg = bpy.context.evaluated_depsgraph_get()
    for f in range(lo, hi + 1, step):
        scene.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        ce = cam.evaluated_get(dg)
        m = ce.matrix_world
        frames.append({
            "f": f,
            "p": [round(v, 6) for v in m.translation],
            "q": [round(v, 6) for v in m.to_quaternion()],
            "lens": round(ce.data.lens, 5),
            "focus_m": round(ce.data.dof.focus_distance, 5),
            "fstop": round(ce.data.dof.aperture_fstop, 5),
            "use_dof": bool(ce.data.dof.use_dof),
            "focus_object": (ce.data.dof.focus_object.name
                             if ce.data.dof.focus_object else None),
        })
        if (f - lo) % geom_step == 0 or f in (lo, hi):
            g = {}
            for cl, objs in resolved.items():
                lo3 = [1e18] * 3
                hi3 = [-1e18] * 3
                for o in objs:
                    oe = o.evaluated_get(dg)
                    mw = oe.matrix_world
                    for c in oe.bound_box:
                        w = mw @ Vector(c)
                        for i in range(3):
                            lo3[i] = min(lo3[i], w[i])
                            hi3[i] = max(hi3[i], w[i])
                if lo3[0] < 1e17:
                    g[cl] = [[round(v, 5) for v in lo3], [round(v, 5) for v in hi3]]
            geom[str(f)] = g

    doc = {
        "blend": bpy.data.filepath,
        "camera": cam_name,
        "sensor_width": cd.sensor_width,
        "sensor_height": cd.sensor_height,
        "sensor_fit": cd.sensor_fit,
        "res": [scene.render.resolution_x, scene.render.resolution_y],
        "res_pct": scene.render.resolution_percentage,
        "exposure": scene.view_settings.exposure,
        "view_transform": scene.view_settings.view_transform,
        "frames": frames,
        "cluster_bbox": geom,
        "unresolved_parts": {k: v for k, v in misses.items() if v},
    }
    json.dump(doc, open(out_path, "w"))
    print("STAGE RESULT OK frames=%d geom_frames=%d unresolved_parts=%d "
          "exposure=%.4f -> %s"
          % (len(frames), len(geom), total_miss, scene.view_settings.exposure,
             out_path))
    return 0


try:
    rc = main()
except Exception:
    traceback.print_exc()
    print("STAGE RESULT FAIL uncaught exception")
    rc = 1
sys.stdout.flush()
