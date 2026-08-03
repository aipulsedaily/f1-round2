"""human_peep -- crops for looking at a figure render at the pixel level.

The gate is necessary and not sufficient, and the last instruction in the brief
is "then render at 767 px and ask whether it is a person". A 3840 x 2160 frame
displayed whole is a thumbnail; the question is answered on the head, the hand
and the hem, at 1:1 and at 4:1. This cuts them.

It finds the subject by PROJECTING THE MESH, not by thresholding the image: the
camera and the object are both in the blend, so where the head lands is a
computed fact rather than a guess, and a crop that misses is a crop that wasted
a render.

    blender -b <item>_test.blend --factory-startup -P world/items/human_peep.py \
        -- --png render/items/<id>/peep_767px.png --cam PPF_CAM_PEEP_767 \
           --subject PPF_Fig_009 --out render/items/<id>/peep
"""

import argparse
import json
import os
import sys

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
import human_png as HP                                          # noqa: E402

try:
    import bpy
    from mathutils import Vector
    from bpy_extras.object_utils import world_to_camera_view
except ImportError:                                             # noqa: BLE001
    bpy = None

# (name, what fraction of the subject's height the band spans, from the top)
BANDS = (("head", 0.00, 0.16),
         ("torso", 0.16, 0.55),
         ("hands", 0.38, 0.62),
         ("feet", 0.86, 1.02),
         ("whole", -0.03, 1.03))


def subject_screen_box(scene, cam, ob, step=5):
    me = ob.data
    co = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    P = co.reshape(-1, 3)[::step]
    M = np.array(ob.matrix_world.to_4x4())
    W = P @ M[:3, :3].T + M[:3, 3]
    uv = np.array([[*world_to_camera_view(scene, cam, Vector(p))] for p in W])
    rx = scene.render.resolution_x
    ry = scene.render.resolution_y
    px = uv[:, 0] * rx
    py = (1.0 - uv[:, 1]) * ry
    return px, py, W


def main():
    p = argparse.ArgumentParser(prog="human_peep")
    p.add_argument("--png", required=True)
    p.add_argument("--cam", required=True)
    p.add_argument("--subject", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--scale", type=int, default=2)
    argv = sys.argv
    a = p.parse_args(argv[argv.index("--") + 1:] if "--" in argv else argv[1:])

    scene = bpy.context.scene
    cam = bpy.data.objects[a.cam]
    ob = bpy.data.objects[a.subject]
    scene.camera = cam
    bpy.context.view_layer.update()
    px, py, W = subject_screen_box(scene, cam, ob)
    img = HP.read(a.png)
    if img.dtype == np.uint16:
        img = (img >> 8).astype(np.uint8)
    H, Wd = img.shape[:2]
    if (Wd, H) != (scene.render.resolution_x, scene.render.resolution_y):
        print("!! the PNG is %dx%d but the scene renders %dx%d -- the projection "
              "below is in SCENE pixels and will not line up. R2-020."
              % (Wd, H, scene.render.resolution_x, scene.render.resolution_y))
    top, bot = float(py.min()), float(py.max())
    hgt = bot - top
    left, right = float(px.min()), float(px.max())
    rep = {"png": a.png, "resolution": [Wd, H], "subject": a.subject,
           "subject_px_height": round(hgt, 1),
           "subject_px_width": round(right - left, 1),
           "subject_box_px": [round(left, 1), round(top, 1),
                              round(right, 1), round(bot, 1)],
           "crops": {}}
    os.makedirs(a.out, exist_ok=True)
    for name, f0, f1 in BANDS:
        y0 = top + f0 * hgt
        y1 = top + f1 * hgt
        cx = 0.5 * (left + right)
        half = max(0.62 * (y1 - y0), 0.62 * (right - left))
        x0, x1 = cx - half, cx + half
        x0 = int(max(0, min(Wd - 8, x0)))
        x1 = int(max(x0 + 8, min(Wd, x1)))
        y0 = int(max(0, min(H - 8, y0)))
        y1 = int(max(y0 + 8, min(H, y1)))
        sc = a.scale if (x1 - x0) * a.scale < 1600 else 1
        dst = os.path.join(a.out, "%s.png" % name)
        shp = HP.crop(a.png, dst, x0, y0, x1, y1, scale=sc)
        rep["crops"][name] = {"box_px": [x0, y0, x1, y1],
                              "magnification": sc, "out_shape": list(shp)}
        print("  %-6s %4d,%4d .. %4d,%4d  (%d x %d px, x%d) -> %s"
              % (name, x0, y0, x1, y1, x1 - x0, y1 - y0, sc, dst))
    json.dump(rep, open(os.path.join(a.out, "peep.json"), "w"), indent=1)
    print("  subject %s reads %.0f x %.0f px in this frame"
          % (a.subject, right - left, hgt))


if __name__ == "__main__":
    main()
