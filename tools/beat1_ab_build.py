"""Build ONE blend carrying BOTH beat-1 cameras, for the R2-451 A/B.

    /opt/blender-5.2.0-linux-x64/blender -b work/b1nadir/cam_before.blend \
        --factory-startup -P tools/beat1_ab_build.py -- \
        --after work/b1nadir/cam_after.blend --out render/r2451_b1ab.blend

WHY ONE BLEND WITH TWO CAMERAS
------------------------------
The two arms then differ by the camera and by NOTHING else -- same geometry, same
lights, same grade, same sim state, same upload -- so a difference in the picture
cannot be a difference in the scene.  It also costs one scene transfer to the
render box instead of two, which matters on a shared $45 cap.

WHY NOT render/film14.blend
---------------------------
It is 4.53 GB and rebuilding it with a new camera is a 4.5 GB read, a 4.5 GB
write and a 4.5 GB upload, for a question that is entirely about where the lens
points inside the showroom.  This scene is `world/beat1_anim.blend` -- the same
showroom, the same 616 exploded parts, the same 23 practicals, the same part
animation -- at 291 MB.

THE LIMIT, STATED RATHER THAN DISCOVERED: through the glass wall this scene shows
`R2_ProceduralSky`, not `world/build_sky.py`'s sky with its atmosphere slab, so
the exterior seen through the mullions is not the film's exterior.  Beat 1's
subject is inside the room and the comparison is between two cameras in the SAME
scene, so nothing in the verdict rests on it -- but a frame from here is not a
frame of the film and must not be quoted as one.

THE GRADE IS THE FILM'S
-----------------------
`world/beat1_anim.blend` was authored at view exposure 0.000 with round-1
practicals.  The film grades at `film_exposure.FILM_EXPOSURE` and the practicals
are lifted by exactly `-FILM_EXPOSURE` to compensate (see world/showroom_lighting.py).
Both are applied here, imported and never hardcoded, so the A/B is lit and graded
the way beat 1 actually is.  Rendering this scene as-loaded would put the room
3.628 stops under and answer a question about the encoder instead of the camera.
"""

import argparse
import os
import sys

import bpy

R2 = "/home/zany/f1-round2"
for p in (os.path.join(R2, "world"), os.path.join(R2, "tools")):
    if p not in sys.path:
        sys.path.insert(0, p)

import film_exposure as FX                                        # noqa: E402
import showroom_lighting as SL                                    # noqa: E402


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--after", required=True)
    p.add_argument("--out", required=True)
    return p.parse_args(argv)


def main():
    a = parse_args()
    scene = bpy.context.scene

    cams = [o for o in bpy.data.objects if o.type == "CAMERA"]
    if len(cams) != 1:
        raise SystemExit(f"expected exactly one camera in the BEFORE blend, "
                         f"found {[c.name for c in cams]}")
    before = cams[0]
    before.name = "CAM_R2451_BEFORE"
    before.data.name = "CAMDATA_R2451_BEFORE"
    print(f">> BEFORE camera: {before.name}")

    # ---- append the AFTER camera, with its object AND data animation --------
    with bpy.data.libraries.load(a.after) as (src, dst):
        pick = [n for n in src.objects if n == "ONER"] or list(src.objects)[:1]
        dst.objects = pick
    got = [o for o in dst.objects if o is not None]
    if len(got) != 1 or got[0].type != "CAMERA":
        raise SystemExit(f"append from {a.after} did not yield one camera: {got}")
    after = got[0]
    after.name = "CAM_R2451_AFTER"
    after.data.name = "CAMDATA_R2451_AFTER"
    scene.collection.objects.link(after)
    print(f">> AFTER camera appended: {after.name}")

    for c in (before, after):
        ok_o = bool(c.animation_data and c.animation_data.action)
        ok_d = bool(c.data.animation_data and c.data.animation_data.action)
        print(f"   {c.name:22s} obj-anim {ok_o}  data-anim {ok_d}  "
              f"dof {c.data.dof.use_dof}")
        if not (ok_o and ok_d):
            raise SystemExit(f"{c.name} lost its animation on append -- an "
                             f"un-animated camera would render one static "
                             f"station for every frame and look like a fix")

    # ---- the two cameras must actually DIFFER, and at f1 -------------------
    scene.frame_set(1)
    bpy.context.view_layer.update()
    p0 = before.matrix_world.translation.copy()
    p1 = after.matrix_world.translation.copy()
    print(f">> f1  BEFORE {tuple(round(v, 4) for v in p0)}   "
          f"AFTER {tuple(round(v, 4) for v in p1)}   d = {(p1 - p0).length:.4f} m")
    if (p1 - p0).length < 1e-6:
        raise SystemExit("the two cameras are at the same place at f1 -- the "
                         "A/B would compare a frame against itself")

    # ---- the film's own light level and grade, imported, never hardcoded ----
    SL.apply(scene)
    FX.apply(scene)
    SL.assert_levelled(scene)
    print(f">> grade: exposure {scene.view_settings.exposure:+.3f}  "
          f"({scene.view_settings.view_transform} / {scene.view_settings.look})")
    # 1e-9 is TIGHTER THAN THE PROPERTY. `view_settings.exposure` is a float32
    # RNA property, so -3.628 stores as -3.62800002098..., and a 1e-9 assertion
    # on it fails on a scene that is graded exactly right. The tolerance is the
    # storage precision, not a fudge.
    if abs(scene.view_settings.exposure - FX.FILM_EXPOSURE) > 1e-5:
        raise SystemExit(f"view exposure {scene.view_settings.exposure} is not "
                         f"FILM_EXPOSURE {FX.FILM_EXPOSURE}")
    if scene.view_settings.view_transform != FX.VIEW_TRANSFORM or \
            scene.view_settings.look != FX.VIEW_LOOK:
        raise SystemExit("view transform / look are not the film's")

    scene.render.resolution_x, scene.render.resolution_y = 3840, 2160
    scene.render.resolution_percentage = 100
    scene.render.use_motion_blur = True
    scene.render.motion_blur_shutter = 0.5
    scene.render.motion_blur_position = "CENTER"
    scene.camera = before

    bpy.ops.wm.save_as_mainfile(filepath=a.out, compress=False)
    print(f">> wrote {a.out} "
          f"({os.path.getsize(a.out) / 1e6:.0f} MB)")
    print(">> STAGE RESULT: B1AB_BUILD_OK")
    return 0


import gate_exit                                                  # noqa: E402

if __name__ == "__main__":
    gate_exit.guard(main, tool="beat1_ab_build")
