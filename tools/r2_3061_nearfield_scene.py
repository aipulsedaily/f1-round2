"""R2-3061: THE NEAR-FIELD ASPHALT RIG — the film's own pose, with and without
the shutter, on the surface alone.

    blender -b --factory-startup -P tools/r2_3061_nearfield_scene.py -- \
        --out world/r23061_nearfield.blend

WHY THIS EXISTS
---------------
`build_surface.FILM_POSE_FRAMES` is (1547, 2225, 2000, 1226). Those were chosen
off `render/r2651/track_scale.json` as the frames where the surface is sharpest,
and their camera-motion streaks are 7.0, 10.3, 69.7 and 5.4 px at 4K.

The frames the client's complaint is actually about are not those. R2-2881 named
f1685-1688, f1784-1787 and f2622, and the SAME table says:

    f1787   3.80 mm/px   90.9 % of frame   CoC 0.24 px   streak 245.2 px
    f1350   5.18 mm/px   61.6 %            CoC 0.45      streak 214.0 px
    f2622   4.22 mm/px   98.2 %            CoC 2.11      streak 213.2 px

So the material has never been looked at, in a test frame or a gate, at the
sampling the defect frames use (3-5 mm/px, five times finer than the sharpest
test frame) or under anything like their shutter (210-245 px, THIRTY times the
median test frame's). Both of those change which octaves reach the delivered
pixel, and a 16-64 px @4K band at 3.8 mm/px is 61-243 mm of road — a different
part of the material entirely from the 0.19-0.75 m that band means at f1547.

WHAT IT BUILDS
--------------
One blend, one animated camera, six render frames:

    1350, 1787, 2622    the film's own pose, keyed from `render/film22_path.json`
                        at f-2..f+2, so Cycles' own 180-degree shutter reproduces
                        the delivered streak from the delivered path
    4350, 4787, 5622    THE SAME POSE, HELD STILL. Five identical keys, so the
                        camera's velocity is exactly zero and the same view
                        renders with no motion blur at all.

The still twin is the control the whole question turns on. If the asphalt's
16-64 px band comes back healthy with the camera stopped and empty with it
moving, the defect is the shutter and no amount of shader authoring will fix it
-- authoring into it would be this project's double correction for the third
time. If it comes back empty in BOTH, the material is genuinely blank in that
band and the fix is in `_mat_asphalt`.

The pair is rendered in ONE job because they are the same camera at different
frame numbers, so the control costs no extra cold start -- and a cold start, not
the rendering, is what a broker job actually costs.

WHAT IS AND IS NOT THE FILM
---------------------------
IS: the surface build itself, `world_contract`'s sun and sky (via
`build_surface._mk_sun`, which is built entirely from `C.SUN_*`/`C.SKY_*`), the
contract's view transform and reference exposure, the rig's own keyed lens,
f-stop, focus distance and 0.5 shutter, and the delivered resolution.

IS NOT: the car, the barriers, the architecture, the terrain, the dressing or
the items. Their shadows and occlusion are absent, so ABSOLUTE tile levels here
are not the film's and are not claimed to be. What is claimed is the BAND
STRUCTURE of the road surface at the film's own sampling, and the tile mean is
printed beside every band number so the reader can see how far the levels drift.
"""
import argparse
import json
import math
import os
import sys

R2 = "/home/zany/f1-round2"
sys.path.insert(0, os.path.join(R2, "world"))
sys.path.insert(0, R2)

import bpy                                            # noqa: E402
import world_contract as C                            # noqa: E402


def _load_surface(path=None):
    """`world/build_surface.py`, or ANOTHER COPY OF IT NAMED ON THE COMMAND LINE.

    The A/B this rig exists for is one material against another, and the only
    honest way to get the BEFORE arm is to run the committed file rather than a
    remembered description of it:

        git show HEAD:world/build_surface.py > /tmp/before_build_surface.py
        ... --surface-module /tmp/before_build_surface.py

    The module is loaded under its own name from an explicit path, so nothing in
    the worktree is stashed, checked out or moved -- six other agents are live in
    this repository and a `git stash` here would take their files with it.
    """
    if not path:
        import build_surface as B                     # noqa: PLC0415
        return B, os.path.join(R2, "world/build_surface.py")
    import importlib.util                             # noqa: PLC0415
    spec = importlib.util.spec_from_file_location("build_surface", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["build_surface"] = mod
    spec.loader.exec_module(mod)
    return mod, path

PATH_JSON = os.path.join(R2, "render/film22_path.json")
DOF_JSON = os.path.join(R2, "render/r2651/dof.json")
LIVE_FRAMES = (1350, 1787, 2622)
STILL_OFFSET = 3000          # 1350 -> 4350, 1787 -> 4787, 2622 -> 5622
PAD = 2                      # frames keyed either side, so the shutter has a path
RES = (3840, 2160)
SAMPLES = 32                 # the delivery spec (R2-2881 4K arm, spec c0b2aabd80dcee71)


def _key(ob, cam, f, rec, dof):
    ob.location = rec["p"]
    ob.rotation_mode = 'QUATERNION'
    ob.rotation_quaternion = rec["q"]
    ob.keyframe_insert("location", frame=f)
    ob.keyframe_insert("rotation_quaternion", frame=f)
    cam.lens = float(rec["lens"])
    cam.keyframe_insert("lens", frame=f)
    if dof:
        cam.dof.aperture_fstop = float(dof["fstop"])
        cam.dof.focus_distance = max(float(dof["focus"]), 0.1)
        cam.dof.keyframe_insert("aperture_fstop", frame=f)
        cam.dof.keyframe_insert("focus_distance", frame=f)


def _default_interp(mode):
    """Make every key this file inserts LINEAR, at insert time.

    `Action.fcurves` is GONE in Blender 5.2 -- actions are slotted now and the
    curves live under `action.layers[].strips[].channelbag(slot)`. The first
    version of this file walked `ad.action.fcurves`, raised AttributeError, and
    **Blender exited 0**, so the buildlock printed `rc=0` on a run that wrote no
    blend at all. Setting the preference instead needs no traversal and cannot
    go stale against another API move.

    It matters: on BEZIER keys the camera eases in and out of every key, so the
    five identical keys of the still arm would still be still, but the live arm's
    sub-frame velocity across the open shutter would be the ease curve's rather
    than the delivered path's, and the whole point is to reproduce the delivered
    streak.
    """
    try:
        bpy.context.preferences.edit.keyframe_new_interpolation_type = mode
        return True
    except Exception as exc:
        print("!! could not set default key interpolation: %s" % exc)
        return False


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(R2, "world/r23061_nearfield.blend"))
    ap.add_argument("--surface-module", default="",
                    help="path to the build_surface.py to run; default is the "
                         "worktree's. Use it to build the BEFORE arm from "
                         "`git show HEAD:world/build_surface.py`.")
    a = ap.parse_args(argv)

    path = {r["f"]: r for r in json.load(open(PATH_JSON))["path"]}
    dof = {r["f"]: r for r in json.load(open(DOF_JSON))["frames"]}

    B, bpath = _load_surface(a.surface_module)
    import hashlib
    with open(bpath, "rb") as fh:
        bsha = hashlib.sha256(fh.read()).hexdigest()
    print(">> surface module: %s\n>> sha256:         %s" % (bpath, bsha))

    _default_interp('LINEAR')
    B.build()
    scene = bpy.context.scene
    B._scene_settings(scene, RES, SAMPLES, measure=False)
    scene.cycles.device = 'GPU'
    B._mk_sun(scene)
    B._test_props(scene, None)                 # the whole-lap stand-in ground

    # THE SHUTTER IS THE RIG'S, NOT THIS FILE'S.  `anim/build_camera_rig.py` ships
    # `--shutter 0.5`, `--shutter-mode flat`, position CENTER, and `dof.json`
    # records 0.5 on every one of the 2,978 delivered frames.  Assert it rather
    # than retype it: a shutter that silently differs from the film's would make
    # every number here a measurement of this file.
    shut = {dof[f]["shutter"] for f in LIVE_FRAMES}
    if shut != {0.5}:
        raise SystemExit("dof.json says the shutter is %s at the probe frames, "
                         "not 0.5 -- the rig has changed and this rig must too" % shut)
    scene.render.use_motion_blur = True
    scene.render.motion_blur_shutter = 0.5
    scene.render.motion_blur_position = 'CENTER'

    cam = bpy.data.cameras.new("CAM_NEARFIELD")
    cam.sensor_fit = 'HORIZONTAL'
    cam.sensor_width = 36.0
    cam.dof.use_dof = True
    ob = bpy.data.objects.new("CAM_NEARFIELD", cam)
    scene.collection.objects.link(ob)
    scene.camera = ob

    # ---- the live arm: the delivered path, keyed either side of each probe ----
    for f in LIVE_FRAMES:
        for g in range(f - PAD, f + PAD + 1):
            if g in path:
                _key(ob, cam, g, path[g], dof.get(g))
    # ---- the still arm: the same pose, five identical keys, zero velocity ----
    for f in LIVE_FRAMES:
        s = f + STILL_OFFSET
        for g in range(s - PAD, s + PAD + 1):
            _key(ob, cam, g, path[f], dof.get(f))

    scene.frame_start, scene.frame_end = min(LIVE_FRAMES), max(LIVE_FRAMES) + STILL_OFFSET

    # ---- OBSERVE THE CONTROL FAILING AND PASSING, before anything is rendered --
    # A "still" camera that is not actually still would silently produce a second
    # blurred arm and the A/B would compare two of the same thing.  Measure the
    # per-frame displacement off the evaluated depsgraph, which is what Cycles
    # samples, not off the keys this file just wrote.
    dg = bpy.context.evaluated_depsgraph_get()
    worst_live, worst_still = 0.0, 0.0
    for f in LIVE_FRAMES:
        for tag, fr in (("live", f), ("still", f + STILL_OFFSET)):
            ps = []
            for sub in (-0.25, 0.25):
                scene.frame_set(fr, subframe=0.0)
                scene.frame_float = fr + sub
                dg.update()
                m = ob.evaluated_get(dg).matrix_world
                ps.append((m.translation.copy(), cam.lens))
            d = (ps[1][0] - ps[0][0]).length
            if tag == "live":
                worst_live = max(worst_live, d)
            else:
                worst_still = max(worst_still, d)
            print(">> %-5s f%-5d camera moves %.6f m across the open shutter"
                  % (tag, fr, d))
    ok = worst_live > 0.05 and worst_still < 1e-9
    print(">> STAGE RESULT: %s  (live worst %.6f m must be > 0.05, still worst "
          "%.3e m must be 0)"
          % ("SHUTTER_ARMS_OK" if ok else "SHUTTER_ARMS_FAILED",
             worst_live, worst_still))
    if not ok:
        raise SystemExit("the two arms are not different; refusing to write a "
                         "blend whose A/B compares two of the same thing")

    scene.frame_set(LIVE_FRAMES[0])
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=a.out)
    print(">> wrote %s  (%d objects, camera %s, frames %s + %s)"
          % (a.out, len(bpy.data.objects), ob.name, list(LIVE_FRAMES),
             [f + STILL_OFFSET for f in LIVE_FRAMES]))
    print(">> STAGE RESULT: NEARFIELD_SCENE_OK")


main()
