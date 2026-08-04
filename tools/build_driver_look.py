"""R2-244 -- a small scene for LOOKING at the driver, at the film's own camera.

    blender -b world/car_anim_driver.blend --factory-startup -noaudio \
        -P tools/build_driver_look.py -- --frames 2632 828 700 --out render/driver_look.blend

WHY NOT THE FILM BLEND
----------------------
`render/film14.blend` is 4.53 GB and the broker is already shipping it for four
other agents; hard constraint 6 says do not disturb the queue.  This ships the
CAR plus the driver plus the sky and sun, which is everything that lights a
helmet in a cockpit, at 1/10 the payload.

WHAT IT IS NOT: the track surface, the grandstands and the showroom are absent,
so the ground bounce and the built environment do not appear in the visor.  The
visor is a mirror and it WILL therefore show a cleaner sky here than in the
film.  Stated, not hidden -- and it is the reason `--film-world` exists, which
appends assembly9's own world and sun instead of the contract's.

THE GRADE IS THE FILM'S, ASSERTED
---------------------------------
AgX / look None / exposure `world/film_exposure.FILM_EXPOSURE` = -3.628.
Every item frame judged on this project before 2026-08-03 was 0.580 stops over
because it was rendered at `itemkit.contract_sun`'s -3.048 (see
`world/humankit.py:film_exposure`), and 0.58 stops is most of the shading range
a helmet's curvature has to work in.  This file sets the film's grade and then
reads it back and raises if it did not take.
"""

import argparse
import json
import math
import os
import sys

import bpy
from mathutils import Quaternion, Vector

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(R2, "world"), os.path.join(R2, "world", "items")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

ASSEMBLY = os.path.join(R2, "render/world/assembly/r2/assembly9.blend")


def log(m):
    sys.stdout.write("[driver_look] %s\n" % m)
    sys.stdout.flush()


def append_film_world(path=ASSEMBLY):
    """The shipping world's own World datablock and every light OBJECT.

    Object names are matched against the LIGHT datablock names read out of the
    library without loading it, so this never pulls the 4.2 GB of terrain in
    just to find a sun.
    """
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        lights = set(src.lights)
        worlds = list(src.worlds)
        cand = [n for n in src.objects if n in lights or n.split(".")[0] in lights]
        log("library %s: %d worlds, %d light datablocks, %d matching objects"
            % (os.path.basename(path), len(worlds), len(lights), len(cand)))
        dst.worlds = worlds[:1]
        dst.objects = cand
    got = [o for o in bpy.data.objects if o.name in set(cand) and o.type == 'LIGHT']
    for o in got:
        if o.name not in bpy.context.scene.collection.objects:
            bpy.context.scene.collection.objects.link(o)
    w = bpy.data.worlds.get(worlds[0]) if worlds else None
    if w is not None:
        bpy.context.scene.world = w
    log("appended world %r and %d light objects: %s"
        % (getattr(w, "name", None), len(got),
           [(o.name, o.data.type) for o in got][:8]))
    return w, got


def contract_world():
    import itemkit as K
    import humankit as HK
    sc = bpy.context.scene
    K.contract_sun(sc)
    HK.film_exposure(sc)
    return sc.world, [o for o in bpy.data.objects if o.type == 'LIGHT']


def add_camera(name, path_json, frame):
    d = json.load(open(path_json))["path"][frame - 1]
    assert d["f"] == frame
    cam = bpy.data.cameras.new(name)
    cam.sensor_fit = 'AUTO'
    cam.sensor_width = 36.0
    cam.lens = float(d["lens"])
    cam.clip_start = 0.02
    cam.clip_end = 8000.0
    ob = bpy.data.objects.new(name, cam)
    bpy.context.scene.collection.objects.link(ob)
    ob.rotation_mode = 'QUATERNION'
    ob.location = Vector(d["p"])
    ob.rotation_quaternion = Quaternion(d["q"])
    return ob, d


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", type=int, nargs="+", default=[2632, 828, 700])
    ap.add_argument("--path", default=os.path.join(R2, "render/film14_path.json"))
    ap.add_argument("--out", default=os.path.join(R2, "render/driver_look.blend"))
    ap.add_argument("--film-world", action="store_true",
                    help="append assembly9's own world and lights instead of "
                         "itemkit.contract_sun's")
    a = ap.parse_args(argv)

    drv = [o for o in bpy.data.objects if o.name.startswith("DRV_")]
    if not drv:
        raise SystemExit("this blend has no DRV_* -- open car_anim_driver.blend")
    log("%d DRV_* objects present" % len(drv))

    if a.film_world:
        append_film_world()
        import film_exposure as FX
        sc = bpy.context.scene
        sc.view_settings.view_transform = 'AgX'
        sc.view_settings.look = 'None'
        sc.view_settings.exposure = float(FX.FILM_EXPOSURE)
    else:
        contract_world()

    import film_exposure as FX
    sc = bpy.context.scene
    got = (sc.view_settings.view_transform, sc.view_settings.look,
           round(float(sc.view_settings.exposure), 4))
    want = ('AgX', 'None', round(float(FX.FILM_EXPOSURE), 4))
    log("GRADE read back: %s (want %s)" % (str(got), str(want)))
    if got != want:
        print("STAGE RESULT: FAIL -- the grade did not take: %s != %s"
              % (got, want))
        return 1

    sc.render.engine = 'CYCLES'
    sc.render.resolution_x = 3840
    sc.render.resolution_y = 2160
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    sc.cycles.samples = 256
    sc.cycles.use_denoising = True
    sc.render.use_persistent_data = True

    cams = []
    for f in a.frames:
        ob, d = add_camera("CAM_DRV_F%04d" % f, a.path, f)
        cams.append(ob.name)
        log("camera %s at frame %d: p %s lens %.1f mm"
            % (ob.name, f, [round(v, 3) for v in d["p"]], d["lens"]))
    sc.camera = bpy.data.objects[cams[0]]
    sc.frame_set(a.frames[0])

    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.out),
                                compress=False, copy=False)
    log("wrote %s (%.1f MB); cameras %s"
        % (a.out, os.path.getsize(a.out) / 1e6, cams))
    print("STAGE RESULT: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
