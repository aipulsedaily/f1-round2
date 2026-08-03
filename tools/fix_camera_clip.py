"""THE FILM CAMERA'S FAR CLIP PLANE — 1000 m, against a documented 50 km.

    /opt/blender-5.2.0-linux-x64/blender -b render/film8.blend --factory-startup \
        -P tools/fix_camera_clip.py -- --out render/film8c.blend

WHAT WAS MEASURED, AND WHAT IT REFUTES
=======================================
The closing wide of beat 6 carries **56 full-width rows of pure black**, 220-275
of 720, 7.8 % of the frame, and the film's last 11 seconds hold on that shot.
It was read as "the camera looks past the terrain plate". **It is not.**

    ONER camera data, measured on world/camera_rig.blend:
        lens 18.750   clip_start 0.1000   clip_end 1000.0
    A camera datablock made by bpy.data.cameras.new() and never touched:
        clip_end 1000.0

`anim/build_camera_rig.py:575` creates `ONER` with `bpy.data.cameras.new("ONER")`
and sets `sensor_width`, `sensor_fit`, `dof.use_dof` and `rotation_mode`. It
never sets `clip_end`. So the film is shot through **Blender's factory default
1 km far plane** — while `world/build_sky.py`'s own hand-off block declares

    handoff=dict(camera_clip_end_min=50000.0, ...)
    log("HAND-OFF: camera clip_end >= 50 km; ...")

and `build_sky`'s own cameras use `cd.clip_end = 200000.0` with the comment "the
haze slab is 80 km across; clipping it truncates". The requirement is written
down in the module that owns the light, and nothing enforces it.

THE MEASUREMENT THAT SETTLES IT — AN INTERNAL CONTROL IN ONE FRAME
-------------------------------------------------------------------
Frame 2860 rendered from `render/film8.blend` at 1280x720 with
`--film-transparent`, so that anything drawn is opaque and anything not drawn is
alpha 0 (`work/ramp/b6/alpha_2860.png`):

    rows 136-275   alpha 0.000 everywhere      NOTHING IS DRAWN
    row  276       first alpha > 0             the tops of the nearest trees
    rows 304+      alpha 1.000 everywhere      solid geometry

Predicted from a 1000 m clip alone: the camera is at z = 128.799, so a ray at
depression `t` meets z = 0 at 128.799 / sin t, which passes 1000 m at
t = 7.402 deg. At 0.07880 deg per row with the horizon on row 210.0, that is
**row 303.9**. Measured 304. The prediction is a consequence of the clip
distance and the camera's own height and lens, and it lands within one row.

The positive and negative controls are inside that single frame: rows 304+ are
geometry INSIDE 1 km and come back opaque; rows 136-275 are the same world
BEYOND 1 km and come back empty. One render, one exposure, one denoiser.

WHY IT ONLY APPEARS UNDER THE CORRECT SKY, WHICH IS WHY IT SURVIVED
-------------------------------------------------------------------
Blender's Nishita / multiple-scattering Sky Texture returns **black for every
direction below the horizon**. So a downward ray that hits nothing renders 0.
Under the wrong sky the same rays returned a soft grey-blue gradient and the
band read as haze -- which is exactly what the earlier beat-6 frames show
(`work/film6/evidence/beat56/`, zero black rows) and why every one of them
understated it.

WHAT THIS TOOL IS AND IS NOT
-----------------------------
It is a REPAIR OF AN ARTEFACT, not a fix of the cause. The one-line cause lives
in `anim/build_camera_rig.py`, which is owned by another agent this session and
is deliberately not touched here:

    cam_data.clip_start = 0.05
    cam_data.clip_end   = 200000.0     # build_sky hand-off: >= 50 km

Until that lands, every rebuild of the rig reintroduces the 1 km plane. This
tool exists so the defect can be measured, fixed in the shipped blend, and
rendered against, and so the repair is checkable rather than believed.
"""

import argparse
import json
import math
import os
import sys
import time

import bpy

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(R2, "tools"), os.path.join(R2, "world")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import gate_exit                                             # noqa: E402

# `world/build_sky.py` line 1407, its own comment: "the haze slab is 80 km
# across; clipping it truncates". Its declared floor is `camera_clip_end_min`
# = 50 000 m. This takes the module's own working value, not the floor, so a
# camera at one end of the 80 km slab can still see the other.
WANT_CLIP_END = 200000.0
DECLARED_MIN = 50000.0
WANT_CLIP_START = 0.05


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--out", default=None,
                   help="save here; omit to report only")
    p.add_argument("--cam", default=None,
                   help="camera object name; default is the scene camera")
    p.add_argument("--all", action="store_true",
                   help="fix every camera datablock, not just the scene's")
    p.add_argument("--report", default=None)
    p.add_argument("--frame", type=int, default=2860)
    return p.parse_args(argv)


def horizon_row(cam, frame, W=1280, H=720):
    """Which image row the mathematical horizon lands on, and deg per row.

    Reported because it is what turns a clip distance into a row count, and
    because the whole diagnosis stands or falls on the two agreeing.
    """
    import numpy as np
    sc = bpy.context.scene
    sc.frame_set(frame)
    bpy.context.view_layer.update()
    R = np.array(cam.matrix_world.to_3x3())
    sw = cam.data.sensor_width
    sh = sw * H / float(W)
    L = cam.data.lens
    lo, hi = 0.0, float(H)
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        ndy = 1.0 - (mid + 0.5) / H * 2.0
        v = R @ np.array([0.0, ndy * sh * 0.5 / L, -1.0])
        v /= np.linalg.norm(v)
        if math.degrees(math.asin(v[2])) > 0.0:
            lo = mid
        else:
            hi = mid
    vfov = 2.0 * math.degrees(math.atan(sh * 0.5 / L))
    z = float(cam.matrix_world.translation.z)
    return {"horizon_row": 0.5 * (lo + hi), "deg_per_row": vfov / H,
            "vfov_deg": vfov, "lens_mm": L, "cam_z": z}


def predicted_last_drawn_row(geom, clip_end):
    """The row below which a FLAT ground at z = 0 is still inside `clip_end`.

    This is the arithmetic the alpha render was checked against; it is kept in
    the tool so the claim can be re-derived on any frame rather than quoted.
    """
    z = geom["cam_z"]
    if clip_end <= z:
        return None
    t = math.degrees(math.asin(min(1.0, z / clip_end)))
    return geom["horizon_row"] + t / geom["deg_per_row"], t


def main():
    a = parse_args()
    t0 = time.time()
    sc = bpy.context.scene
    src = bpy.data.filepath
    print(">> source %s" % src)

    cam = (bpy.data.objects.get(a.cam) if a.cam else sc.camera)
    if cam is None or cam.type != "CAMERA":
        why = ("REFUSING: no camera %r in this scene (scene.camera is %r)"
               % (a.cam, sc.camera.name if sc.camera else None))
        print(why)
        return gate_exit.verdict("CLIP_NO_CAMERA_REFUSED", why)

    before = [{"data": cd.name, "users": cd.users,
               "clip_start": cd.clip_start, "clip_end": cd.clip_end,
               "lens": cd.lens} for cd in bpy.data.cameras]
    for r in before:
        print(">> BEFORE  camera data %-16r  lens %8.3f  clip %.4f .. %.1f m"
              % (r["data"], r["lens"], r["clip_start"], r["clip_end"]))

    geom = horizon_row(cam, a.frame)
    pred = predicted_last_drawn_row(geom, cam.data.clip_end)
    print(">> frame %d: camera z = %.3f m, lens %.3f, vFOV %.3f deg, "
          "%.5f deg/row at 720p, horizon on row %.1f"
          % (a.frame, geom["cam_z"], geom["lens_mm"], geom["vfov_deg"],
             geom["deg_per_row"], geom["horizon_row"]))
    if pred:
        print(">> with clip_end = %.1f m, FLAT ground at z = 0 is inside the "
              "clip only below %.2f deg of depression == row %.1f; every row "
              "above that draws NOTHING and the Nishita sky returns BLACK "
              "below the horizon" % (cam.data.clip_end, pred[1], pred[0]))

    if cam.data.clip_end >= DECLARED_MIN:
        why = ("clip_end is already %.1f m, at or beyond build_sky's declared "
               "minimum of %.0f m -- nothing to repair."
               % (cam.data.clip_end, DECLARED_MIN))
        print(">> " + why)
        return gate_exit.verdict("CLIP_ALREADY_OK", " " + why)

    targets = list(bpy.data.cameras) if a.all else [cam.data]
    for cd in targets:
        cd.clip_start = WANT_CLIP_START
        cd.clip_end = WANT_CLIP_END
    pred2 = predicted_last_drawn_row(geom, WANT_CLIP_END)
    print(">> AFTER   %d camera datablock(s) set to clip %.4f .. %.1f m "
          "(build_sky hand-off floor %.0f m)"
          % (len(targets), WANT_CLIP_START, WANT_CLIP_END, DECLARED_MIN))
    if pred2:
        print(">> flat ground at z = 0 is now inside the clip below %.4f deg "
              "== row %.2f, i.e. %.1f rows of 720 below the horizon instead of "
              "%.1f" % (pred2[1], pred2[0], pred2[0] - geom["horizon_row"],
                        pred[0] - geom["horizon_row"] if pred else float("nan")))

    # A far plane is not free: Cycles' ray epsilon and the depth buffer both
    # scale with the ratio. Report it rather than leave it to be discovered.
    print(">> clip ratio %.3e (start %.4f / end %.1f); Cycles is a ray tracer "
          "and has no depth buffer, so this costs precision only in the "
          "viewport, not in the render"
          % (WANT_CLIP_END / WANT_CLIP_START, WANT_CLIP_START, WANT_CLIP_END))

    rep = {"source": src, "frame": a.frame, "geometry": geom,
           "before": before, "want_clip_end": WANT_CLIP_END,
           "declared_min": DECLARED_MIN,
           "predicted_last_drawn_row_before": pred[0] if pred else None,
           "predicted_last_drawn_row_after": pred2[0] if pred2 else None,
           "cameras_fixed": [cd.name for cd in targets]}

    if a.out:
        out = os.path.abspath(a.out)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=out, compress=False)
        rep["out"] = out
        print(">> saved %s (%.2f GB) in %.0f s"
              % (out, os.path.getsize(out) / 2 ** 30, time.time() - t0))
    if a.report:
        p = os.path.abspath(a.report)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        json.dump(rep, open(p, "w"), indent=1)
        print(">> report -> %s" % p)

    return gate_exit.verdict(
        "CLIP_END_REPAIRED_OK",
        " %d camera(s) 1000.0 -> %.1f m" % (len(targets), WANT_CLIP_END))


if __name__ == "__main__":
    gate_exit.guard(main, tool="fix_camera_clip")
