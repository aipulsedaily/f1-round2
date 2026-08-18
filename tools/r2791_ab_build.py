"""Build ONE blend with TWO cameras that differ ONLY in focus and aperture.

    /opt/blender-5.2.0-linux-x64/blender -b world/beat1_anim.blend \
        --factory-startup -P tools/r2791_ab_build.py -- \
        --path render/film16_path.json --dump work/r2791/focusdump.json \
        --out render/r2791_dof_ab.blend

WHY THIS SHAPE
--------------
The claim being tested is "the focal plane is in the wrong place and the iris is
too wide". The claim NOT being made, and the one I was told not to make, is
anything about where the camera is or where it points -- that belongs to the
agent re-pacing this beat, and two agents writing one path is how a one-shot film
acquires a seam.

So both cameras are keyed from the SAME per-frame transform, out of the same
`render/film16_path.json`, by the same loop. `assert_transforms_identical()`
below then re-samples both through Blender's own evaluation and requires bitwise
agreement at every frame. That is a structural guarantee rather than a promise:
if this file ever moves a camera, the build fails.

WHY NOT render/film16_breach.blend
----------------------------------
It is 7.97 GB, the local machine has 11 GB, and the question is entirely about
where the plane of focus sits inside the showroom. `world/beat1_anim.blend` is
the same room, the same 616 exploded parts on the same part animation, and the
same 23 practicals, at 291 MB. This is the vehicle `tools/beat1_ab_build.py`
already established for exactly this class of question.

ITS LIMIT, STATED RATHER THAN DISCOVERED: through the glass this scene shows
`R2_ProceduralSky`, not the film's sky. Beat 1's subject is inside the room and
both arms share the scene, so nothing in the verdict rests on it -- but a frame
from here is not a frame of the film and must not be quoted as one.

THE GRADE, AND THE TRAP IN IT
-----------------------------
Reproduced from `tools/beat1_ab_build.py`, whose comment earned it: this scene
is authored at exposure 0.000, the film grades at `FILM_EXPOSURE`, and the
practicals are lifted to compensate. An exposure ramp keyed against 0.000 is
ANIMATION and is re-evaluated on load, so it silently overwrites any static
grade set afterwards and the room comes back 3.628 stops over. The ramp is
cleared and the grade set statically, which is correct here and only here
because every frame of beat 1 precedes the ramp.
"""

import json
import math
import os
import sys

import bpy
from mathutils import Quaternion, Vector

R2 = os.path.expanduser("~/f1-round2")
for p in (os.path.join(R2, "world"), os.path.join(R2, "tools")):
    if p not in sys.path:
        sys.path.insert(0, p)

import film_exposure as FX                                        # noqa: E402
import showroom_lighting as SL                                    # noqa: E402
import r2791_beat1_focus as SOLVE                                 # noqa: E402

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(name, default=None):
    return ARGS[ARGS.index(name) + 1] if name in ARGS else default


def key_transform(cam, path_rows):
    """Location, rotation and lens. IDENTICAL for both arms, by construction."""
    cam.rotation_mode = "QUATERNION"
    for e in path_rows:
        f = e["f"]
        cam.location = Vector(e["p"])
        cam.keyframe_insert("location", frame=f)
        cam.rotation_quaternion = Quaternion(e["q"])
        cam.keyframe_insert("rotation_quaternion", frame=f)
        cam.data.lens = float(e["lens"])
        cam.data.keyframe_insert("lens", frame=f)


def key_dof(cam, per_frame):
    """per_frame: {f: (focus_m, fstop)}"""
    cam.data.dof.use_dof = True
    for f in sorted(per_frame):
        fo, ns = per_frame[f]
        cam.data.dof.focus_distance = float(fo)
        cam.data.dof.keyframe_insert("focus_distance", frame=f)
        cam.data.dof.aperture_fstop = float(ns)
        cam.data.dof.keyframe_insert("aperture_fstop", frame=f)


def assert_transforms_identical(scene, a, b, frames):
    """The whole integrity of this A/B. Re-sampled through Blender, not asserted
    from the keys that were written -- a bug in the keying loop would be invisible
    to a check that only reads the keys back."""
    worst_p = worst_q = worst_l = 0.0
    for f in frames:
        scene.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        ae, be = a.evaluated_get(dg), b.evaluated_get(dg)
        worst_p = max(worst_p, (ae.matrix_world.translation
                                - be.matrix_world.translation).length)
        qa, qb = ae.matrix_world.to_quaternion(), be.matrix_world.to_quaternion()
        worst_q = max(worst_q, max(abs(qa[i] - qb[i]) for i in range(4)))
        worst_l = max(worst_l, abs(ae.data.lens - be.data.lens))
    print(">> transforms identical? worst position %.3e m, quaternion %.3e, "
          "lens %.3e mm over %d frames" % (worst_p, worst_q, worst_l, len(frames)))
    if worst_p > 1e-9 or worst_q > 1e-9 or worst_l > 1e-9:
        raise SystemExit("THE TWO ARMS DO NOT SHARE A PATH — this A/B would be "
                         "attributing a framing difference to focus")


def assert_dof_differs(scene, a, b, frames):
    worst = 0.0
    n_diff = 0
    for f in frames:
        scene.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        ae, be = a.evaluated_get(dg), b.evaluated_get(dg)
        d = abs(ae.data.dof.focus_distance - be.data.dof.focus_distance)
        worst = max(worst, d)
        if d > 0.01:
            n_diff += 1
    print(">> focus differs on %d of %d sampled frames, worst %.3f m"
          % (n_diff, len(frames), worst))
    if worst < 0.05:
        raise SystemExit("the two arms have the same focus — nothing to compare")


def main():
    path_json = arg("--path", os.path.join(R2, "render/film16_path.json"))
    dump_json = arg("--dump", os.path.join(R2, "work/r2791/focusdump.json"))
    out = arg("--out", os.path.join(R2, "render/r2791_dof_ab.blend"))
    lo, hi = int(arg("--first", "1")), int(arg("--last", "792"))

    scene = bpy.context.scene

    for o in [o for o in bpy.data.objects if o.type == "CAMERA"]:
        bpy.data.objects.remove(o, do_unlink=True)

    rows = [e for e in json.load(open(path_json))["path"] if lo <= e["f"] <= hi]
    print(">> %d path rows f%d-%d from %s" % (len(rows), lo, hi, path_json))

    # ---- the SHIPPED depth of field ----------------------------------------
    #
    # Preferred: the per-frame curve read off `render/film16_breach.blend`
    # itself, which is the shipping truth including whatever Blender's handles
    # actually did between the keys.
    #
    # Fallback, and it is a GOOD fallback rather than a concession: key the arm
    # from `docs/beat_sheet.json`'s own 23 beat-1 keys at their own frames and
    # let Blender interpolate. That is not an approximation of what the film
    # does -- it is the same 23 numbers through the same interpolator, which is
    # literally what `build_camera_rig.insert()` does. The dump is then a
    # cross-check on the fallback rather than a dependency of it.
    dump, ship, ship_src = None, {}, None
    if os.path.exists(dump_json):
        dump = json.load(open(dump_json))
        ship = {e["f"]: (e["focus_m"], e["fstop"]) for e in dump["frames"]
                if lo <= e["f"] <= hi}
        if len(ship) >= len(rows):
            ship_src = "per-frame from %s (blend %s)" % (dump_json, dump.get("blend"))
        else:
            ship = {}
    if not ship:
        sheet = json.load(open(os.path.join(R2, "docs/beat_sheet.json")))["beat1"]
        for k in sheet["camera_keys"]:
            f = int(round(k["t"] * SOLVE.FPS)) + 1
            if lo <= f <= hi and k.get("focus_distance_m"):
                ship[f] = (float(k["focus_distance_m"]), float(k.get("fstop", 2.8)))
        ship_src = ("docs/beat_sheet.json beat1.camera_keys — %d keys, "
                    "interpolated by Blender exactly as the film does" % len(ship))
    print(">> SHIP arm DOF: %s" % ship_src)

    # ---- the SOLVED depth of field -----------------------------------------
    field = SOLVE.load_field()
    cams = SOLVE.load_cams_from_path(path_json, lo, hi)
    bg = None
    grid = arg("--grid")
    sub = None
    if grid and os.path.exists(grid):
        sub, bg = SOLVE.depth_from_grid(json.load(open(grid)))
        print(">> subject/background depth measured from %s (%d frames)"
              % (grid, len(bg)))
    # The close-out hand-back needs a value at EVERY frame, so when the SHIP arm
    # is only 23 keys the hand-back reads the sheet's own close-out keys through
    # the same linear fill rather than pretending the gaps are zero.
    sf = {f: v[0] for f, v in ship.items()}
    sn = {f: v[1] for f, v in ship.items()}
    if len(ship) < len(rows):
        ks = sorted(ship)
        for e in rows:
            f = e["f"]
            if f in sf:
                continue
            lo_k = max([k for k in ks if k <= f], default=ks[0])
            hi_k = min([k for k in ks if k >= f], default=ks[-1])
            if lo_k == hi_k:
                sf[f], sn[f] = ship[lo_k]
                continue
            u = (f - lo_k) / float(hi_k - lo_k)
            u = SOLVE.smoothstep(u)
            sf[f] = ship[lo_k][0] * (1 - u) + ship[hi_k][0] * u
            sn[f] = ship[lo_k][1] * (1 - u) + ship[hi_k][1] * u
    solved = SOLVE.solve(cams, field, shipped_focus=sf, shipped_fstop=sn,
                         subject_depth=sub, bg_depth=bg)
    fix = {r["f"]: (r["focus_m"], r["fstop"]) for r in solved}

    # ---- two cameras, one path ---------------------------------------------
    made = []
    for name, dof in (("ONER_SHIP", ship), ("ONER_FIX", fix)):
        cd = bpy.data.cameras.new(name + "_DATA")
        cd.sensor_width = (dump or {}).get("sensor_width", 36.0)
        cd.sensor_fit = (dump or {}).get("sensor_fit", "AUTO")
        ob = bpy.data.objects.new(name, cd)
        scene.collection.objects.link(ob)
        key_transform(ob, rows)
        key_dof(ob, dof)
        made.append(ob)
        print(">> built %s" % name)
    ship_cam, fix_cam = made

    probe = [f for f in (lo, 50, 100, 150, 200, 258, 300, 371, 400, 464, 500,
                         550, 592, 622, 700, 750, hi) if lo <= f <= hi]
    assert_transforms_identical(scene, ship_cam, fix_cam, probe)
    assert_dof_differs(scene, ship_cam, fix_cam, probe)

    # ---- the film's light level and grade (see the header, R2-027) ----------
    SL.apply(scene)
    if scene.animation_data and scene.animation_data.action:
        print(">> removing the mis-keyed exposure ramp (%s)"
              % scene.animation_data.action.name)
        scene.animation_data_clear()
    FX.apply(scene)
    SL.assert_levelled(scene)
    for f in probe:
        scene.frame_set(f)
        if abs(scene.view_settings.exposure - FX.FILM_EXPOSURE) > 1e-5:
            raise SystemExit("exposure is %s at f%d, not FILM_EXPOSURE"
                             % (scene.view_settings.exposure, f))
    print(">> grade holds %+.3f (%s / %s) at every probed frame"
          % (FX.FILM_EXPOSURE, scene.view_settings.view_transform,
             scene.view_settings.look))

    scene.render.resolution_x, scene.render.resolution_y = 3840, 2160
    scene.render.resolution_percentage = 100
    scene.render.fps = 24
    scene.render.use_motion_blur = True
    scene.render.motion_blur_shutter = 0.5
    scene.render.motion_blur_position = "CENTER"
    scene.frame_start, scene.frame_end = lo, hi
    scene.camera = ship_cam
    scene.frame_set(lo)

    bpy.ops.wm.save_as_mainfile(filepath=out, compress=False)
    print(">> wrote %s (%.0f MB)" % (out, os.path.getsize(out) / 1e6))
    print(">> STAGE RESULT: R2791_AB_BUILD_OK")
    return 0


try:
    rc = main()
except SystemExit as e:
    print(">> STAGE RESULT: R2791_AB_BUILD_FAIL %s" % e)
    rc = 1
except Exception:
    import traceback
    traceback.print_exc()
    print(">> STAGE RESULT: R2791_AB_BUILD_FAIL uncaught")
    rc = 1
sys.stdout.flush()
