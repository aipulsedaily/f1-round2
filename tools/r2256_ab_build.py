#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
r2256_ab_build.py — the A/B scene for the La Passerelle fascia.

Builds `build_architecture` + `build_dressing` under `world_contract`'s own sky
and sun, and puts the film's ONER camera at frame 2575 with the pose, lens, DOF
and shutter the delivered frame `2972abcb3fa1.png` was rendered with (read out of
`world/camera_rig_path.json` and `world/camera_rig.blend`, not invented):

    p       (-68.37986, -164.94598, 4.72238)
    q       (0.672424, 0.613148, -0.279232, -0.306471)
    lens    40.7321 mm on a 36.0 mm sensor, fit AUTO
    dof     f/5.6 focused at 43.176 m   (CoC at the banner's 67.21 m = 0.26 px,
                                         so DOF is NOT what softens this sign)
    blur    motion blur on, shutter 0.5 — the camera runs 4.074 m/frame here,
            which smears the banner 16.8 px, 8 along it and 15 across

The camera is keyed at 2574 / 2575 / 2576 so the motion blur is the real one and
not a still.

    --defect   re-author the deleted `PASSERELLE  2` run into ARCH_LaPasserelle,
               exactly as `build_bridges` used to, giving the BEFORE arm.
    --out P    where to save the .blend.

Blender 5.2 exits 0 on an uncaught script exception; judge on `STAGE RESULT`.
"""

import json
import math
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "world"))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import bpy                                                  # noqa: E402
from mathutils import Quaternion, Vector                    # noqa: E402

FRAME = 2575
CAM_LENS = 40.7321
CAM_FSTOP = 5.6
CAM_FOCUS = 43.176
SHUTTER = 0.5


def author_defect(BA):
    """Put `PASSERELLE  2` back on the truss face, from the deleted literals."""
    orig = BA.MB.build
    done = []

    def build(self, coll, matrix=None, *a, **kw):
        if self.name == "ARCH_LaPasserelle" and not done:
            X, D, soffit, dep = -450.0, 4.0, 7.50, 3.05
            orig_text = BA.MB.text
            orig_text(self, "PASSERELLE  2",
                      BA.T(X - D / 2 - 0.1, 2.0, soffit + dep - 0.9)
                      @ BA.Rz(-90) @ BA.Rx(90), 0.85, "A_Sign",
                      BA.srgb('#e8ebee'), extrude=0.02)
            done.append(1)
            print("[AB] DEFECT RE-AUTHORED: PASSERELLE  2 on ARCH_LaPasserelle")
        return orig(self, coll, matrix=matrix, *a, **kw)

    BA.MB.build = build
    return done


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    want_defect = "--defect" in argv
    out = argv[argv.index("--out") + 1] if "--out" in argv else \
        os.path.join(ROOT, "work", "r2256",
                     "ab_%s.blend" % ("before" if want_defect else "after"))

    t0 = time.time()
    import build_architecture as BA
    done = author_defect(BA) if want_defect else None
    BA.build(verify=False)
    print("[AB] architecture %.1f s" % (time.time() - t0))
    if want_defect and not done:
        print("STAGE RESULT: r2256_ab_build FAIL (the defect was never authored)")
        sys.exit(1)

    t0 = time.time()
    import build_dressing as BD
    BD.build()
    print("[AB] dressing %.1f s" % (time.time() - t0))

    sc = bpy.context.scene
    BD._test_env(sc)                       # world_contract's sky + sun, verbatim
    C = BD.C
    sc.view_settings.view_transform = 'AgX'
    sc.view_settings.look = C.VIEW_LOOK
    sc.view_settings.exposure = C.REFERENCE_EXPOSURE_EXTERIOR
    print("[AB] light = world_contract %s, sun %.3f W/m2, AgX %+.3f stops"
          % (C.__version__, C.SUN_ENERGY, sc.view_settings.exposure))

    # ---- the ONER camera, keyed so the motion blur is the delivered one -----
    path = json.load(open(os.path.join(ROOT, "world",
                                       "camera_rig_path.json")))["path"]
    cd = bpy.data.cameras.new("ONER")
    cd.sensor_width, cd.sensor_fit = 36.0, 'AUTO'
    cd.clip_start, cd.clip_end = 0.05, 200000.0
    cd.dof.use_dof = True
    cd.dof.aperture_fstop = CAM_FSTOP
    cd.dof.focus_distance = CAM_FOCUS
    cam = bpy.data.objects.new("ONER", cd)
    sc.collection.objects.link(cam)
    cam.rotation_mode = 'QUATERNION'
    for f in (FRAME - 1, FRAME, FRAME + 1):
        e = path[f - 1]
        assert e["f"] == f, "camera path is not 1-indexed by frame"
        cam.location = Vector(e["p"])
        cam.rotation_quaternion = Quaternion(e["q"])
        cam.keyframe_insert("location", frame=f)
        cam.keyframe_insert("rotation_quaternion", frame=f)
        cd.lens = float(e["lens"])
        cd.keyframe_insert("lens", frame=f)
    sc.camera = cam
    sc.frame_start, sc.frame_end, sc.frame_current = FRAME, FRAME, FRAME
    e = path[FRAME - 1]
    print("[AB] camera frame %d  p=%s lens=%.4f" % (FRAME, e["p"], e["lens"]))

    sc.render.engine = 'CYCLES'
    sc.render.resolution_x, sc.render.resolution_y = 3840, 2160
    sc.render.resolution_percentage = 100
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = SHUTTER
    sc.render.film_transparent = False
    sc.cycles.use_denoising = True
    sc.cycles.samples = 400
    sc.cycles.adaptive_threshold = 0.01
    sc.render.image_settings.file_format = 'PNG'

    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out)
    n_obj = len(bpy.data.objects)
    print("[AB] saved %s  (%d objects)" % (out, n_obj))
    print("STAGE RESULT: r2256_ab_build PASS  (%s, defect=%s, %d objects)"
          % (os.path.basename(out), bool(want_defect), n_obj))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
        print("STAGE RESULT: r2256_ab_build FAIL (uncaught exception)")
        sys.exit(1)
