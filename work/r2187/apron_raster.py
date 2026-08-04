"""WHERE IS THE APRON ON SCREEN AT THIS FRAME?

    blender -b render/film14_breach.blend -P work/r2187/apron_raster.py -- \
        --frame 890 --res 1920 1080

The A/B between film13_breach and film14_breach turns up ~100 pixels that
differ by more than the render's own noise floor.  Claiming those are
`ARCH_Paving_ApronPlatform` -- the one object assembly9 changed -- is a claim,
and it is testable: project the object's own vertices through the scene's own
camera at the same frame and see whether the pixels land inside it.

CONTROL: the same projection is run for an object that certainly did NOT change
(the showroom floor), so a bbox that swallows the whole frame is visible as
such rather than being read as a hit.
"""
import argparse
import json
import sys

import numpy as np

import bpy
from bpy_extras.object_utils import world_to_camera_view


def parse():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--frame", type=int, default=890)
    p.add_argument("--res", nargs=2, type=int, default=[1920, 1080])
    p.add_argument("--objects", default="ARCH_Paving_ApronPlatform")
    p.add_argument("--out", default="")
    return p.parse_args(argv)


def raster_bbox(sc, cam, ob, W, H, stride):
    n = len(ob.data.vertices)
    flat = np.empty(3 * n, dtype=np.float32)
    ob.data.vertices.foreach_get("co", flat)
    V = flat.reshape(n, 3)[::stride].astype(np.float64)
    m = np.array(ob.matrix_world)
    Vw = V @ m[:3, :3].T + m[:3, 3]
    xs, ys, front = [], [], 0
    from mathutils import Vector
    for p in Vw:
        c = world_to_camera_view(sc, cam, Vector(p))
        if c.z <= 0:
            continue
        front += 1
        if not (0.0 <= c.x <= 1.0 and 0.0 <= c.y <= 1.0):
            continue
        xs.append(c.x * W)
        ys.append((1.0 - c.y) * H)
    if not xs:
        return dict(in_frustum=0, sampled=len(Vw), in_front=front)
    return dict(in_frustum=len(xs), sampled=len(Vw), in_front=front,
                x=[round(min(xs), 1), round(max(xs), 1)],
                y=[round(min(ys), 1), round(max(ys), 1)])


def main():
    a = parse()
    sc = bpy.context.scene
    # warm-up: the first frame_set after load does not flush transforms for
    # objects the depsgraph skipped
    sc.frame_set(a.frame)
    bpy.context.view_layer.update()
    sc.frame_set(a.frame)
    bpy.context.view_layer.update()
    cam = sc.camera
    W, H = a.res
    out = {"frame": a.frame, "camera": cam.name, "res": [W, H],
           "cam_loc": [round(v, 4) for v in cam.matrix_world.translation],
           "lens_mm": round(cam.data.lens, 4), "objects": {}}
    for nm in a.objects.split(",") + ["SR_Floor", "ARCH_Showroom_Floor"]:
        ob = sc.objects.get(nm)
        if ob is None or ob.type != "MESH":
            out["objects"][nm] = "absent"
            continue
        stride = max(1, len(ob.data.vertices) // 20000)
        out["objects"][nm] = raster_bbox(sc, cam, ob, W, H, stride)
    print(json.dumps(out, indent=1))
    if a.out:
        with open(a.out, "w") as fh:
            json.dump(out, fh, indent=1)
    print("STAGE RESULT: apron_raster done")


if __name__ == "__main__":
    main()
