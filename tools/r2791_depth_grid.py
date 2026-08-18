"""What the beat-1 lens ACTUALLY SEES, per frame, as a depth grid.

    ./rq exec --root ~/f1-round2 --closure \
        --include 'docs/explode_plan.json' \
        --scene render/film16_breach.blend \
        --entry tools/r2791_depth_grid.py \
        --arg=--scene --arg=scene.blend --arg=--out --arg=out/depthgrid.json \
        --output depthgrid.json --timeout 3600

WHY NOT THE BOUNDING BOX
------------------------
`docs/beat_sheet.json`'s `presentation_framing` and `tools/beat1_true_extent.py`
both project the eight corners of a cluster's world bbox. Both SILENTLY DROP the
corners that fall behind the camera plane, and on this beat the camera is close
enough that that happens on about a quarter of the frames. The damage is not
subtle: `fstop_required` reads f/37.95 for CORNER_RL and f/99.67 for CORNER_RR,
two stations with near-identical geometry, because the second one has a bbox
corner 0.15 m off the lens driving a division. A design that targets those
numbers is targeting an artefact.

A ray only travels forwards, so a raycast grid cannot have that failure mode. It
also measures the thing the audience is actually shown -- the visible surface
inside the frame -- rather than an axis-aligned box drawn round an exploded
cluster, most of which is empty air.

WHAT IS RECORDED, per sampled frame
-----------------------------------
  z[]    depth along the camera's own forward axis, metres, for a GX x GY grid
         of rays over the WHOLE frame (not just the centre). -1 for a miss.
  cls[]  index into `names`: which cluster owns the surface that ray hit, or
         ROOM for anything that is not an assembly part, or MISS.
  plus the camera's lens / focus_distance / aperture_fstop at that frame.

Everything else -- circle of confusion, what fraction of the subject is sharp,
where the focal plane SHOULD be -- is computed offline from this, so the
expensive scene is opened once and the analysis can be redone without it.

Blender 5.2 exits 0 on an uncaught exception. Judge on STAGE RESULT only.
"""

import json
import os
import sys
import time
import traceback

import bpy
from mathutils import Vector

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def arg(name, default=None):
    return ARGS[ARGS.index(name) + 1] if name in ARGS else default


def find(rel):
    for base in (ROOT, HERE, os.getcwd()):
        p = os.path.join(base, rel)
        if os.path.exists(p):
            return p
    raise IOError("cannot find %s" % rel)


def main():
    scene_path = arg("--scene")
    out_path = arg("--out", "out/depthgrid.json")
    lo = int(arg("--first", "1"))
    hi = int(arg("--last", "800"))
    step = int(arg("--step", "2"))
    gx = int(arg("--gx", "64"))
    gy = int(arg("--gy", "36"))
    cam_name = arg("--cam", "ONER")

    if scene_path:
        bpy.ops.wm.open_mainfile(filepath=os.path.abspath(scene_path))

    scene = bpy.context.scene
    cam = bpy.data.objects.get(cam_name)
    if cam is None:
        print("STAGE RESULT R2791_GRID_FAIL no camera %r" % cam_name)
        return 1

    plan = json.load(open(find("docs/explode_plan.json")))["clusters"]
    by_name = {o.name: o for o in bpy.data.objects}
    part_cluster = {}
    for cl, spec in plan.items():
        for p in spec["parts"]:
            if p in by_name:
                part_cluster[p] = cl
            else:
                for n in by_name:
                    if n.startswith(p + "."):
                        part_cluster[n] = cl

    # class table: 0 MISS, 1 ROOM, 2.. clusters (sorted, so the index is stable)
    clusters = sorted(plan)
    names = ["MISS", "ROOM"] + clusters
    cls_of = {c: i + 2 for i, c in enumerate(clusters)}

    sw = cam.data.sensor_width
    rx, ry = scene.render.resolution_x, scene.render.resolution_y
    sh = sw * ry / rx

    out, t0 = [], time.time()
    for f in range(lo, hi + 1, step):
        scene.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        ce = cam.evaluated_get(dg)
        m = ce.matrix_world
        eye = m.translation.copy()
        q = m.to_quaternion()
        fwd = (q @ Vector((0.0, 0.0, -1.0))).normalized()
        right = (q @ Vector((1.0, 0.0, 0.0))).normalized()
        up = (q @ Vector((0.0, 1.0, 0.0))).normalized()
        lens = ce.data.lens

        zs, cs = [], []
        for jy in range(gy):
            # pixel centres, frame spans the full sensor
            dv = ((jy + 0.5) / gy - 0.5) * sh
            for jx in range(gx):
                du = ((jx + 0.5) / gx - 0.5) * sw
                d = (fwd * lens + right * du + up * dv).normalized()
                ok, loc, _n, _i, obj, _mw = scene.ray_cast(dg, eye, d)
                if not ok:
                    zs.append(-1.0)
                    cs.append(0)
                    continue
                zs.append(round((loc - eye).dot(fwd), 4))
                nm = obj.name if obj else ""
                cs.append(cls_of.get(part_cluster.get(nm, ""), 1))

        out.append({
            "f": f,
            "p": [round(v, 6) for v in eye],
            "q": [round(v, 6) for v in q],
            "lens": round(lens, 5),
            "focus_m": round(ce.data.dof.focus_distance, 5),
            "fstop": round(ce.data.dof.aperture_fstop, 5),
            "use_dof": bool(ce.data.dof.use_dof),
            "z": zs, "cls": cs,
        })
        if len(out) % 25 == 0:
            print(">> %d frames, %.1f s elapsed, %.2f s/frame"
                  % (len(out), time.time() - t0, (time.time() - t0) / len(out)))
            sys.stdout.flush()

    doc = {
        "blend": bpy.data.filepath, "camera": cam_name,
        "grid": [gx, gy], "names": names,
        "sensor_width": sw, "sensor_height": sh, "res": [rx, ry],
        "first": lo, "last": hi, "step": step,
        "frames": out,
    }
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    json.dump(doc, open(out_path, "w"))
    print("STAGE RESULT R2791_GRID_OK frames=%d grid=%dx%d rays=%d %.1fs -> %s"
          % (len(out), gx, gy, len(out) * gx * gy, time.time() - t0, out_path))
    return 0


try:
    rc = main()
except Exception:
    traceback.print_exc()
    print("STAGE RESULT R2791_GRID_FAIL uncaught exception")
    rc = 1
sys.stdout.flush()
