"""THE FINES, RENDERED.  A demonstrator, NOT a candidate for the film.

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P sim/debris_demo.py -- --frame 880 --out render/debris/f880_A.png

WHY THIS EXISTS AND WHY IT IS NOT THE FILM
==========================================
The deliverable for task #129 is "demonstrated in rendered frames at a
resolution where it can actually be seen", and on 2026-08-07 neither of the two
things that could produce a film frame is available: both vast.ai brokers were
torn down after the render ladder, and the local card reports
`Unable to determine the device handle for GPU0`.  The film blends are 7-8 GB
against 11 GB of host RAM.

So this builds the BREACH ALONE -- the shards, the panes and the fines, from the
same tables `apply_breach` reads, through the same `build()` -- under the film's
own sun, the film's own sky generator, the film's own exposure, and the film's
own camera transform and lens AT A NAMED FRAME, read from
`sim/out/oner_camera_track.json` (R2-706: every pixel figure goes through that
file).  Pixel scale, sun angle, shutter and grade are therefore the film's.  The
showroom, the circuit and the car are NOT here.

WHAT THAT MEANS FOR THE CONCLUSIONS
    honest    the size of a chip in pixels; whether a flake reads as a streak;
              the density of the field; the A/B of with-fines against
              without-fines on identical geometry and identical light.
    NOT honest anything about occlusion by the car or the showroom, about the
              fines against a specific background, or about the grade in
              context.  Those need the film scene and the farm.

`--no-fines` renders the CONTROL: the identical scene with the fines collection
excluded.  A demonstration with no negative is a picture, not evidence.
"""

import argparse
import json
import math
import os
import sys
import types

import bpy                                                        # noqa: E402
from mathutils import Quaternion, Vector                          # noqa: E402

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(R2, "sim"), os.path.join(R2, "world"),
           os.path.join(R2, "anim")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# world/build_sky.py owns the light; these are its constants, cited not copied
# from taste.  SUN_DIR is _RAW_SUN normalised, SUN_ENERGY is its max channel,
# and REFERENCE_EXPOSURE_EXTERIOR is what the film grades at.
SUN_DIR = Vector((0.518, -0.828, 0.216)).normalized()
SUN_ENERGY = 115.754
SUN_COLOR = (1.00000, 0.71632, 0.38712)
SUN_ANGULAR_DIAM = math.radians(0.526)
SKY_SUN_ROTATION_DEG = 147.9697
EXPOSURE = -3.048


def log(m):
    print(">> %s" % m)
    sys.stdout.flush()


def parse():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--frame", type=int, default=880)
    p.add_argument("--out", required=True)
    p.add_argument("--res", type=int, default=3840)
    p.add_argument("--crop", default="",
                   help="x0,x1,y0,y1 in 0..1 -- a BORDER render, so the pixel "
                        "scale stays the delivery format's")
    p.add_argument("--samples", type=int, default=192)
    p.add_argument("--no-fines", action="store_true",
                   help="the control: identical scene, fines excluded")
    p.add_argument("--debris", default=os.path.join(R2, "sim/out/breach_debris.npz"))
    p.add_argument("--film", default=os.path.join(R2, "sim/out/breach_film.npz"))
    p.add_argument("--shards", default=os.path.join(R2, "sim/out/fracture_wall.npz"))
    p.add_argument("--hero-m", type=float, default=6.0)
    p.add_argument("--save-blend", default="")
    p.add_argument("--frost", action="store_true",
                   help="also apply --fracture-faces to BREACH_Glass, so the "
                        "same frames answer 'do the flakes resolve' AND 'does "
                        "a frosted shard stop reading as a thin bright line'")
    p.add_argument("--build-only", action="store_true",
                   help="save the blend and skip the render; the farm renders "
                        "it separately through `rq anim`, which is the only "
                        "path with a GPU")
    a = p.parse_args(argv)
    # Inputs resolve against the BUNDLE ROOT under `rq exec`, whose CWD is the
    # job directory and whose bundle sits in `bundle/`.  R2-788.
    for f in ("debris", "film", "shards"):
        v = getattr(a, f)
        if v and not os.path.isabs(v) and not os.path.exists(v):
            c = os.path.join(R2, v)
            if os.path.exists(c):
                setattr(a, f, c)
    return a


def main():
    a = parse()
    sc = bpy.context.scene
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    sc.unit_settings.scale_length = 1.0

    import apply_breach as AB
    ns = types.SimpleNamespace(
        film=a.film, shards=a.shards, debris="" if a.no_fines else a.debris,
        glass_material="BREACH_Glass", fines_material="BREACH_Fines",
        hero_m=a.hero_m, detail_hero=2, detail_bulk=1, no_frame=True,
        fracture_faces=bool(a.frost), fines_lib="")
    stats, C_shard, C_pane, C_frame, C_fines = AB.build(ns)
    log("build: %s" % json.dumps(
        {k: v for k, v in stats.items()
         if k in ("objects", "tris", "keys", "hero")}))
    log("fines: %s" % json.dumps(
        {k: v for k, v in stats["fines"].items() if k != "report"}))

    # ---- the light ---------------------------------------------------------- #
    ld = bpy.data.lights.new("SUN", "SUN")
    ld.energy = SUN_ENERGY
    ld.color = SUN_COLOR
    ld.angle = SUN_ANGULAR_DIAM
    sun = bpy.data.objects.new("SUN", ld)
    sc.collection.objects.link(sun)
    sun.rotation_mode = "QUATERNION"
    sun.rotation_quaternion = Vector((0, 0, -1)).rotation_difference(-SUN_DIR)

    sc.world = bpy.data.worlds.new("SKY")
    sc.world.use_nodes = True
    wnt = sc.world.node_tree
    bg = wnt.nodes["Background"]
    sky = wnt.nodes.new("ShaderNodeTexSky")
    # 'MULTIPLE_SCATTERING', not 'NISHITA'.  Blender 5.2's enum is
    # ('SINGLE_SCATTERING', 'MULTIPLE_SCATTERING', 'PREETHAM', 'HOSEK_WILKIE');
    # the old name raises, and `world/build_sky.py` already uses the right one
    # at both of its call sites.  Copying the film's generator means copying its
    # spelling.
    sky.sky_type = "MULTIPLE_SCATTERING"
    sky.sun_elevation = math.asin(SUN_DIR.z)
    sky.sun_rotation = math.radians(SKY_SUN_ROTATION_DEG)
    sky.sun_disc = False              # the SUN lamp is the disc
    wnt.links.new(sky.outputs["Color"], bg.inputs["Color"])

    # ---- the ground, so the fines have something to land on and the frame is
    # not black below the wound.  Plain, deliberately: this is not a set. ----- #
    bpy.ops.mesh.primitive_plane_add(size=120.0, location=(20.0, 0.0, 0.0))
    gp = bpy.context.object
    gm = bpy.data.materials.new("DEMO_Ground")
    gm.use_nodes = True
    gb = gm.node_tree.nodes.get("Principled BSDF")
    gb.inputs["Base Color"].default_value = (0.055, 0.055, 0.058, 1.0)
    gb.inputs["Roughness"].default_value = 0.62
    gp.data.materials.append(gm)

    # ---- the camera: the FILM's, at this frame ------------------------------ #
    trk = json.load(open(os.path.join(R2, "sim/out/oner_camera_track.json")))
    row = trk[a.frame - 1]
    assert int(row[0]) == a.frame, (row[0], a.frame)
    cd = bpy.data.cameras.new("CAM")
    cd.lens = row[8]
    cd.sensor_width = 36.0
    cd.sensor_fit = "HORIZONTAL"
    cam = bpy.data.objects.new("CAM", cd)
    sc.collection.objects.link(cam)
    cam.rotation_mode = "QUATERNION"
    cam.location = (row[1], row[2], row[3])
    cam.rotation_quaternion = Quaternion((row[4], row[5], row[6], row[7]))
    sc.camera = cam
    log("camera f%d at (%.3f, %.3f, %.3f) lens %.2f mm -> %.1f px/m at 1.00 m"
        % (a.frame, row[1], row[2], row[3], row[8], a.res * row[8] / 36.0))

    # ---- render ------------------------------------------------------------- #
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = a.samples
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.01
    sc.cycles.use_denoising = True
    sc.render.resolution_x = a.res
    sc.render.resolution_y = int(round(a.res * 9 / 16))
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    # 180 deg shutter.  The F-curves are keyed in FILM frames and the world-time
    # ramp is already inside them, so 0.5 of a film frame IS the 180 deg the
    # brief requires, scaled by world time, with no second correction.
    sc.render.use_motion_blur = True
    sc.render.motion_blur_shutter = 0.5
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.exposure = EXPOSURE
    if a.crop:
        x0, x1, y0, y1 = [float(v) for v in a.crop.split(",")]
        sc.render.use_border = True
        sc.render.use_crop_to_border = True
        sc.render.border_min_x, sc.render.border_max_x = x0, x1
        sc.render.border_min_y, sc.render.border_max_y = y0, y1
        log("border crop %s -> %d x %d px at the 4K pixel scale"
            % (a.crop, int(round((x1 - x0) * sc.render.resolution_x)),
               int(round((y1 - y0) * sc.render.resolution_y))))
    sc.frame_set(a.frame)

    if a.save_blend:
        bpy.ops.wm.save_as_mainfile(filepath=a.save_blend)
        log("saved %s" % a.save_blend)

    if a.build_only:
        print("STAGE RESULT: debris_demo PASS (build-only, %s)"
              % ("fines+frost" if a.frost else
                 "control" if a.no_fines else "fines"))
        return
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    sc.render.filepath = a.out
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_depth = "16"
    bpy.ops.render.render(write_still=True)
    ok = os.path.exists(a.out) and os.path.getsize(a.out) > 4096
    log("wrote %s (%s bytes)"
        % (a.out, os.path.getsize(a.out) if os.path.exists(a.out) else "NONE"))
    print("STAGE RESULT: debris_demo %s%s"
          % ("PASS" if ok else "FAIL",
             " (control, no fines)" if a.no_fines else ""))


if __name__ == "__main__":
    main()
