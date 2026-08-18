"""R2-401 -- WHICH PART of the driver reaches the film, in pixels.

    /opt/blender-5.2.0-linux-x64/blender -b <car_anim_driver*.blend> \
        --factory-startup -noaudio -P tools/r2401_part_mask.py -- \
        --frames 2635 2632 --tag base

R2-241 measured that the driver is on screen for 2,164 frames and peaks at
366 px.  It did not measure WHAT is on screen, and the whole question of
whether the cockpit reads occupied turns on that: a helmet alone in a hole
reads differently from a helmet with shoulders and arms under it.

The instrument is `tools/driver_containment.py`'s, unchanged in principle: every
car mesh is `is_holdout` so it punches a transparent hole while still occluding,
`film_transparent` is on, one sample, 0.01 px filter, opaque material override.
Alpha is 1 exactly where an unoccluded DRIVER surface is frontmost.  What is
added is that the pass is run once per GROUP, so the 132,155 px at frame 2632
resolve into helmet / arms / torso.

THE TRAP THIS FILE IS BUILT AGAINST (R2-249)
    `driver_containment`'s first cut forced every DRV_* object visible for its
    "driver present" pass, which switched the boots back on -- the objects
    `place_driver` had just excluded -- and it then reported the identical leak
    before and after the fix.  A gate that overrides the thing it measures is
    measuring itself.  So here the AUTHORED visibility is read first and a group
    can only ever be a SUBSET of what actually renders: a part that
    `place_driver` excluded stays excluded and is reported as such.

CONTROLS
    NEGATIVE  an 'none' group with every DRV_* hidden must return 0 px.
    POSITIVE  the group pixel counts must sum to within a few px of the 'all'
              group -- if they do not, the groups do not partition the driver
              and the split is not a split.  (They cannot sum EXACTLY: where
              one part occludes another, both are frontmost in their own pass.
              The excess is reported, not hidden.)
"""
import argparse
import json
import os
import sys

import bpy
import numpy as np
from mathutils import Quaternion, Vector

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES_X, RES_Y, SENSOR = 3840, 2160, 36.0

GROUPS = {
    "helmet": ("DRV_Helmet", "DRV_Balaclava"),
    "arms":   ("DRV_Glove_L", "DRV_Glove_R"),
    "torso":  ("DRV_Suit", "DRV_HANS", "DRV_Harness", "DRV_Extras"),
}


def log(m):
    sys.stdout.write("[r2401_mask] %s\n" % m)
    sys.stdout.flush()


def film_camera(path_json, frame):
    d = json.load(open(path_json))["path"][frame - 1]
    assert d["f"] == frame
    cam = bpy.data.cameras.new("CAM_R2401_%d" % frame)
    cam.sensor_fit = 'AUTO'
    cam.sensor_width = SENSOR
    cam.lens = float(d["lens"])
    cam.clip_start = 0.02
    cam.clip_end = 6000.0
    ob = bpy.data.objects.new("CAM_R2401_%d" % frame, cam)
    bpy.context.scene.collection.objects.link(ob)
    ob.rotation_mode = 'QUATERNION'
    ob.location = Vector(d["p"])
    ob.rotation_quaternion = Quaternion(d["q"])
    return ob, float(d["lens"])


def render_alpha(out_png):
    sc = bpy.context.scene
    sc.render.filepath = out_png
    bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(out_png)
    a = np.array(im.pixels[:], dtype=np.float32).reshape(RES_Y, RES_X, 4)
    bpy.data.images.remove(im)
    return (a[..., 3] > 0.5)[::-1]


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", type=int, nargs="+", default=[2635, 2632])
    ap.add_argument("--path", default=os.path.join(R2, "render/film14_path.json"))
    ap.add_argument("--outdir", default=os.path.join(R2, "render/r2401"))
    ap.add_argument("--tag", default="base")
    ap.add_argument("--report", default=None)
    a = ap.parse_args(argv)
    os.makedirs(a.outdir, exist_ok=True)
    rep = {"tag": a.tag, "blend": bpy.data.filepath, "frames": {}}

    drv = [o for o in bpy.data.objects
           if o.name.startswith("DRV_") and o.type == 'MESH']
    if not drv:
        raise SystemExit("no DRV_* meshes in this blend")

    # AUTHORED visibility first, then drop the animation so this file's own
    # hide_render writes are not overwritten on the next frame_set.
    authored = {}
    for o in drv:
        keyed = bool(o.animation_data and o.animation_data.action)
        authored[o.name] = (False if keyed else bool(o.hide_render))
        o.animation_data_clear()
    renders = sorted(k for k, v in authored.items() if not v)
    excluded = sorted(k for k, v in authored.items() if v)
    log("authored: %d render %s ; %d excluded %s"
        % (len(renders), renders, len(excluded), excluded))
    rep["authored_render"] = renders
    rep["authored_excluded"] = excluded

    drvset = set(o.name for o in drv)
    ncar = 0
    for o in bpy.data.objects:
        if o.type != 'MESH':
            continue
        if o.name in drvset:
            o.is_holdout = False
        else:
            o.is_holdout = True
            ncar += 1
    log("%d car meshes -> holdout" % ncar)

    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.render.resolution_x, sc.render.resolution_y = RES_X, RES_Y
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = True
    sc.render.filter_size = 0.01
    sc.cycles.samples = 1
    sc.cycles.use_denoising = False
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGBA'
    sc.render.use_persistent_data = True
    mat = bpy.data.materials.new("R2401_Opaque")
    mat.use_nodes = False
    sc.view_layers[0].material_override = mat

    plan = [("all", tuple(renders)), ("none", ())] + [
        (g, tuple(n for n in names if n in renders)) for g, names in GROUPS.items()]

    for f in a.frames:
        cam, lens = film_camera(a.path, f)
        sc.camera = cam
        sc.frame_set(f)
        row = {"lens": lens, "groups": {}}
        for gname, names in plan:
            for o in drv:
                o.hide_render = (o.name not in names)
            bpy.context.view_layer.update()
            png = os.path.join(a.outdir, "pm_%s_f%04d_%s.png" % (a.tag, f, gname))
            M = render_alpha(png)
            n = int(M.sum())
            row["groups"][gname] = {"px": n, "objects": list(names), "png": png}
            if n:
                ys, xs = np.nonzero(M)
                row["groups"][gname]["bbox"] = [int(xs.min()), int(xs.max()),
                                                int(ys.min()), int(ys.max())]
            log("  f%d %-8s %8d px  (%s)" % (f, gname, n, ",".join(names) or "-"))
        allpx = row["groups"]["all"]["px"]
        parts = sum(row["groups"][g]["px"] for g in GROUPS)
        row["sum_of_groups"] = parts
        row["overlap_excess_px"] = parts - allpx
        log("  f%d SPLIT: helmet %.1f%%  arms %.1f%%  torso %.1f%%   "
            "(groups sum %d vs all %d, excess %+d from mutual occlusion)"
            % (f, 100.0 * row["groups"]["helmet"]["px"] / max(allpx, 1),
               100.0 * row["groups"]["arms"]["px"] / max(allpx, 1),
               100.0 * row["groups"]["torso"]["px"] / max(allpx, 1),
               parts, allpx, parts - allpx))
        if row["groups"]["none"]["px"] != 0:
            print("STAGE RESULT: FAIL -- the NEGATIVE control is not zero "
                  "(%d px with every DRV_* hidden); the alpha is not the driver"
                  % row["groups"]["none"]["px"])
            return 1
        if allpx == 0:
            print("STAGE RESULT: FAIL -- 0 driver px at frame %d; nothing to "
                  "split" % f)
            return 1
        if parts < allpx:
            print("STAGE RESULT: FAIL -- the groups sum to FEWER px (%d) than "
                  "the whole (%d): they do not cover the driver" % (parts, allpx))
            return 1
        rep["frames"][str(f)] = row

    out = a.report or os.path.join(R2, "docs/r2401_part_mask_%s.json" % a.tag)
    json.dump(rep, open(out, "w"), indent=1)
    log("wrote %s" % out)
    print("STAGE RESULT: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
