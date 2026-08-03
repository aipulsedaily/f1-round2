"""THE FILM SCENE — the world, the car in it, and the camera that shoots them.

    /opt/blender-5.2.0-linux-x64/blender -b \
        render/world/assembly/r2/assembly6.blend --factory-startup \
        -P tools/build_film_scene.py -- --out work/film6.blend

WHY THIS EXISTS
---------------
Until now the world and the car have never been in the same file. The world
assemblies render with the ONER camera and NO CAR — that is what
`render/world/assembly/r2/v121/*.png` are — and `world/car_anim.blend` has the
car and the showroom and no circuit. Every statement about how the car looks on
the road has therefore been a statement about a number.

This appends the `CAR` collection — 616 meshes, `CAR_ROOT` and the eight
`CARRIG_*` hub empties, with all their animation — into a world blend, and builds
the camera rig on top with the film's own grade.

APPENDED, NOT LINKED, AND THAT IS NOT A STYLE CHOICE
-----------------------------------------------------
A linked library is a second file, and `~/vast-render` ships exactly one blend to
the GPU. A linked car would render as an empty hole on the farm and as a car
here, which is the worst possible failure: it looks right on the machine where
nobody is watching the render.

WHICH WORLD
-----------
Whatever blend this is run against — but `render/world/assembly/r2/SHIPPING.md`
is unambiguous that `assembly5.blend` MUST NOT BE RENDERED FROM (its
`BR_Transit_NorthWall` stands up to 3.333 m outboard of the declared corridor,
in the shot the camera flies at 200 km/h), so this refuses to run on it by name.
"""

import argparse
import importlib.util
import json
import os
import sys
import time

import bpy

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(R2, "anim"))
sys.path.insert(0, os.path.join(R2, "world"))


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--car", default=os.path.join(R2, "world/car_anim.blend"))
    p.add_argument("--sheet", default=os.path.join(R2, "docs/beat_sheet.json"))
    p.add_argument("--telemetry",
                   default=os.path.join(R2, "telemetry/telemetry.csv"))
    p.add_argument("--spec", default=os.path.join(R2, "docs/circuit_spec.json"))
    p.add_argument("--out", required=True)
    p.add_argument("--no-rig", action="store_true",
                   help="append the car only; leave the world's own camera")
    return p.parse_args(argv)


def main():
    a = parse_args()
    src = bpy.data.filepath
    if os.path.basename(src) == "assembly5.blend":
        raise SystemExit(
            "REFUSING: assembly5.blend is superseded and must not be rendered "
            "from — see render/world/assembly/r2/SHIPPING.md. Use assembly6.")

    scene = bpy.context.scene
    sheet = json.load(open(a.sheet))
    total = int(sheet["total_frames"])
    scene.frame_start = 1
    scene.frame_end = total
    scene.render.fps = 24

    before_objs = set(o.name for o in bpy.data.objects)

    # ---- the car ---------------------------------------------------------
    t0 = time.time()
    loaded = []
    with bpy.data.libraries.load(a.car, link=False) as (src_data, dst_data):
        if "CAR" not in src_data.collections:
            raise SystemExit("%s has no CAR collection" % a.car)
        dst_data.collections = ["CAR"]
        loaded = dst_data.collections
    # `dst_data.collections` is rewritten in place with the real datablocks on
    # exit from the context manager, so this is the collection that was just
    # appended and not a name lookup that could find the world's own.
    car = [c for c in loaded if c is not None][0]
    scene.collection.children.link(car)
    print(">> appended CAR (%d objects) from %s in %.1f s"
          % (len(car.objects), a.car, time.time() - t0))

    root = None
    for o in car.objects:
        if o.name.startswith("CAR_ROOT"):
            root = o
    if root is None:
        raise SystemExit("the appended CAR collection has no CAR_ROOT")
    hubs = [o.name for o in car.objects if o.name.startswith("CARRIG_")]
    if len(hubs) != 8:
        raise SystemExit("the appended CAR collection carries %d CARRIG_* hub "
                         "empties, expected 8: %s" % (len(hubs), hubs))
    orphans = [o.name for o in car.objects
               if o.parent is not None and o.parent.name not in
               set(x.name for x in car.objects)]
    if orphans:
        raise SystemExit("%d appended parts have a parent outside the CAR "
                         "collection: %s" % (len(orphans), orphans[:6]))
    if not (root.animation_data and root.animation_data.action):
        raise SystemExit("the appended CAR_ROOT carries NO animation — the car "
                         "would sit on the dais for the whole film. Build "
                         "world/car_anim.blend with anim/build_car_anim.py.")
    print(">> CAR_ROOT %r animated, %d children, %d hub empties"
          % (root.name, len(root.children), len(hubs)))

    # ---- the grade, BEFORE the rig (the rig keys a delta from it) ---------
    import film_exposure as FX
    got = FX.apply(scene)
    print(">> GRADE from world/film_exposure.py: exposure %+.3f, view_transform "
          "%s, look %s" % (got["exposure"], got["view_transform"], got["look"]))

    # ---- the camera ------------------------------------------------------
    #
    # `build_camera_rig.main()` finishes through `fix_audit_blend.save_clean`,
    # which installs `R2_ProceduralSky` as the scene world. That is right for the
    # showroom blend it was written for and WRONG here: this world's light was
    # built by `world/build_sky.py`, and `world/film_exposure.py`'s -3.628 was
    # MEASURED under it — 39.0106 W/m2 including the atmosphere slab. Swapping
    # the world would relight the film and leave the exposure calibrated to a
    # sky that is no longer in the scene.
    #
    # So the world datablock is captured and restored, and the swap is asserted
    # rather than hoped about.
    #
    # ...EXCEPT THAT `assembly6.blend` HAS NO WORLD AT ALL, AND THE PARAGRAPH
    # ABOVE WAS WRONG ABOUT THAT.  MEASURED on the shipping assembly, 2026-08-03:
    # `bpy.context.scene.world is None`.  `render/world/assembly/r2/assemble.py`
    # builds `surface,barriers,architecture,terrain,dressing` and NOT `sky` — the
    # light is added later, by `render_setup3.py`, which calls
    # `build_sky.build(scn, scn.camera)`.  The first run of this file therefore
    # (a) crashed on `bpy.data.worlds.get(None)` AFTER saving, and (b) shipped a
    # 4.5 GB film scene lit by `save_clean`'s bare `R2_ProceduralSky` — which is
    # NOT the light `film_exposure.FILM_EXPOSURE` = -3.628 was measured under.
    # That measurement was made under build_sky INCLUDING its `SKY_AirColumn` /
    # `SKY_AirBoundary` atmosphere slab, worth 28.3005 -> 39.0106 W/m2, i.e.
    # 0.463 stops of light that R2_ProceduralSky does not have.  A film scene
    # without build_sky is a film graded for a sky it is not lit by.
    #
    # So: if the incoming scene has no world, this builds the film's own sky
    # after the rig (the rig needs to exist first — build_sky drives the world
    # off `scene.camera`), and re-saves.
    world_before = scene.world.name if scene.world else None
    if world_before is None:
        print(">> the incoming scene has NO world — build_sky will be run after "
              "the camera rig (see the note above; assembly*.blend carry no sky)")
    imgs_before = sorted(i.name for i in bpy.data.images if i.source == "FILE")
    if not a.no_rig:
        spec_mod = importlib.util.spec_from_file_location(
            "build_camera_rig", os.path.join(R2, "anim/build_camera_rig.py"))
        mod = importlib.util.module_from_spec(spec_mod)
        argv_save = sys.argv
        sys.argv = ["blender", "--", "--sheet", a.sheet, "--telemetry",
                    a.telemetry, "--spec", a.spec, "--out", a.out]
        spec_mod.loader.exec_module(mod)
        mod.main()
        sys.argv = argv_save

        world_after = scene.world.name if scene.world else None
        imgs_after = sorted(i.name for i in bpy.data.images if i.source == "FILE")
        dropped = [i for i in imgs_before if i not in imgs_after]
        if world_before is None:
            # THE FILM'S OWN LIGHT. Same call render_setup3.py makes, so the
            # film scene is lit by the sky every world render ever looked at was
            # lit by, and the sky FILM_EXPOSURE was measured under.
            import build_sky as SKY
            if scene.camera is None:
                raise SystemExit("no scene camera after the rig build — "
                                 "build_sky drives the world off it")
            sky_stats = SKY.build(scene, scene.camera)
            if scene.world is None:
                raise SystemExit("build_sky did not install a world")
            suns = [o for o in bpy.data.objects if o.type == "LIGHT"
                    and o.name.startswith("SKY_")]
            slab = [o for o in bpy.data.objects
                    if o.name in ("SKY_AirColumn", "SKY_AirBoundary")]
            if not suns or len(slab) != 2:
                raise SystemExit(
                    "build_sky left %d SKY_ lamp(s) and %d of the 2 atmosphere "
                    "slab objects. FILM_EXPOSURE was measured with both present."
                    % (len(suns), len(slab)))
            print(">> LIT by world/build_sky.py: world %r, %d SKY_ lamp(s), "
                  "atmosphere slab %s"
                  % (scene.world.name, len(suns), [o.name for o in slab]))
            print(">> build_sky stats: %s"
                  % {k: v for k, v in (sky_stats or {}).items()
                     if isinstance(v, (int, float, str, bool))})
            # the exposure/grade was applied before the rig and the rig keys a
            # DELTA from it; re-assert rather than assume nothing touched it
            got2 = FX.apply(scene)
            print(">> GRADE re-asserted after build_sky: exposure %+.3f %s %s"
                  % (got2["exposure"], got2["view_transform"], got2["look"]))
            bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.out),
                                        compress=False)
        elif world_after != world_before:
            w = bpy.data.worlds.get(world_before)
            if w is None:
                raise SystemExit(
                    "REFUSING: the rig build replaced the world %r with %r and "
                    "the original datablock is gone. This scene would render "
                    "under a light the film's exposure was not measured in."
                    % (world_before, world_after))
            scene.world = w
            print(">> RESTORED the world: the rig build swapped %r for %r; the "
                  "assembly's own sky is back" % (world_before, world_after))
            bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.out),
                                        compress=False)
        if dropped:
            raise SystemExit(
                "REFUSING: save_clean dropped %d image datablock(s) this world "
                "was using: %s. Either the world depends on an external asset "
                "(which the brief forbids and the farm cannot resolve) or the "
                "strip is too wide." % (len(dropped), dropped))
        print(">> world %r kept; %d FILE images before, %d after"
              % (scene.world.name if scene.world else None,
                 len(imgs_before), len(imgs_after)))
    else:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.out),
                                    compress=False)

    added = len(set(o.name for o in bpy.data.objects) - before_objs)
    print(">> film scene: %s -> %s  (+%d objects, %d total)"
          % (os.path.basename(src), a.out, added, len(bpy.data.objects)))
    print(">> STAGE RESULT: FILM_SCENE_BUILT")



# Imported by path, not by package: this runs inside Blender's interpreter
# with whatever cwd the caller happened to have.
import os as _os_ge, sys as _sys_ge
if _os_ge.path.dirname(_os_ge.path.abspath(__file__)) not in _sys_ge.path:
    _sys_ge.path.insert(0, _os_ge.path.dirname(_os_ge.path.abspath(__file__)))
import gate_exit                                                 # noqa: E402


if __name__ == "__main__":
    # Blender 5.2 returns 0 for a script that raised: `blender -b -P x.py`
    # prints the traceback and exits 0, MEASURED on this box. A gate that
    # crashed was indistinguishable from one that passed. guard() makes an
    # uncaught exception a status 2 and passes any real verdict through
    # unchanged. One shared helper, not N copies -- see tools/gate_exit.py.
    gate_exit.guard(main, tool="build_film_scene")
