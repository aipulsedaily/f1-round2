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
    p.add_argument("--keep-r1-glass", action="store_true",
                   help="keep round 1's ten GW_Right_Glass_* placeholder panes. "
                        "sim/out/apply_requirements.json R3 requires them GONE; "
                        "this exists only for an A/B of the 33.5 mm move.")
    p.add_argument("--no-showroom", action="store_true",
                   help="append the CAR collection only. Beats 1, 2 and 3 — "
                        "1,056 frames, 35 %% of the film — then have no set.")
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

    # ---- the showroom ----------------------------------------------------
    # THE SET FOR 1,056 OF THE FILM'S 2,978 FRAMES, AND IT WAS BEING LEFT OUT.
    #
    # Beats 1 (assembly), 2 (launch) and 3 (breach) all happen INSIDE the
    # showroom, and the shipping world does not contain one: assembly6.blend's
    # object prefixes are VEG/DR/BR/SURF/ARCH/TER and the only showroom-ish
    # object in it is `ARCH_ShowroomSurrounds`. No floor, no dais, no glass.
    # MEASURED, first run of this file, 2026-08-03: with only `CAR` appended the
    # car's tyres sit +0.4400 m above `ARCH_Paving_Forecourt` for every one of
    # beat 1's frames -- the dais deck top (0.340) over the exterior paving
    # (-0.100) -- with nothing between them.
    #
    # It does not need a third file. `world/car_anim.blend` ALREADY carries the
    # set, in its own collections, because build_car_anim.py was run on the
    # showroom blend:
    #
    #     CAR       625   the car, CAR_ROOT, the 8 CARRIG_* hubs
    #     SHOWROOM   76   Floor, GW_* curtain wall, Turntable_Deck, Platform_Dais
    #     PROPS     189   including all 28 Vitrine_*, ALREADY UNPARENTED
    #     LIGHTS     61   the showroom's interior rig
    #     CAMERAS     4   dropped by the rig anyway, so not appended
    #
    # Appending from THIS file rather than from `world/verify_showroom.blend` is
    # the point: car_anim.blend is the post-unparent artefact. Its Vitrines are
    # in PROPS with parent None (MEASURED: 0 of 28 parented to CAR_ROOT), so the
    # display case full of brake discs stays bolted to the showroom floor instead
    # of flying round the circuit at 330 km/h. Appending the set from a second
    # file would also give the scene two copies of every vitrine.
    #
    # The transform is identity and the datum is exact, so this is a plain
    # append with no fitting: MEASURED on car_anim.blend, GW_Right_Glass_00 lies
    # in the plane x = 15.0000 == `world_contract.ACCESS_GLASS_X`, the breach
    # plane build_architecture calls a butt joint with no allowance, and
    # Turntable_Deck's top is z = 0.3400 == the spec's deck_top_z. Both are
    # re-asserted below rather than trusted.
    SET_COLLECTIONS = ("SHOWROOM", "PROPS", "LIGHTS")
    if a.no_showroom:
        print(">> --no-showroom: beats 1-3 (frames 1-1056) will have NO SET")
    else:
        t1 = time.time()
        with bpy.data.libraries.load(a.car, link=False) as (src_data, dst_data):
            missing = [c for c in SET_COLLECTIONS if c not in src_data.collections]
            if missing:
                raise SystemExit(
                    "%s has no %s collection(s). The showroom is the set for "
                    "beats 1-3; rebuild it with anim/build_car_anim.py."
                    % (a.car, missing))
            dst_data.collections = list(SET_COLLECTIONS)
            got_set = dst_data.collections
        for col in got_set:
            scene.collection.children.link(col)
            print(">> appended %s (%d objects)" % (col.name, len(col.objects)))

        # THE VITRINES. 28 of them, and 16 were parented to CAR_ROOT before
        # build_car_anim.py unparented them. If that ever regresses, this build
        # is where it must stop.
        vit = [o for o in bpy.data.objects if o.name.startswith("Vitrine_")]
        flying = [o.name for o in vit if o.parent is root]
        if flying:
            raise SystemExit(
                "REFUSING: %d Vitrine_* display cases are parented to CAR_ROOT "
                "and would be flown round the circuit at 330 km/h: %s"
                % (len(flying), flying[:6]))
        print(">> %d Vitrine_* appended, 0 parented to CAR_ROOT" % len(vit))

        # THE BREACH PLANE. world_contract.ACCESS_GLASS_X, asserted in the
        # scene's own coordinates after the append.
        import world_contract as WC
        bpy.context.view_layer.update()
        glass = bpy.data.objects.get("GW_Right_Glass_00")
        if glass is None or glass.type != "MESH":
            raise SystemExit("no GW_Right_Glass_00 mesh after appending SHOWROOM")
        xs = [(glass.matrix_world @ v.co).x for v in glass.data.vertices]
        want_x = float(getattr(WC, "ACCESS_GLASS_X", 15.0))
        if max(abs(x - want_x) for x in xs) > 1e-3:
            raise SystemExit(
                "REFUSING: GW_Right_Glass_00 spans x %.4f..%.4f, not the "
                "declared breach plane ACCESS_GLASS_X = %.4f. The car breaches "
                "the glass at a station the whole film is timed against."
                % (min(xs), max(xs), want_x))
        deck = bpy.data.objects.get("Turntable_Deck")
        top = max((deck.matrix_world @ v.co).z for v in deck.data.vertices)
        if abs(top - 0.340) > 1e-3:
            raise SystemExit(
                "REFUSING: Turntable_Deck top is z = %.4f, not the 0.340 the "
                "car's contact solve stands it on." % top)
        floor = bpy.data.objects.get("Floor")
        ftop = max((floor.matrix_world @ v.co).z for v in floor.data.vertices)
        if abs(ftop) > 1e-3:                       # sim/out R4
            raise SystemExit(
                "REFUSING: showroom Floor top is z = %.4f, not 0.000. The "
                "breach sim baked 3,796 shard resting transforms against that "
                "plane; a floor 20 mm low leaves every one of them hovering."
                % ftop)
        if abs(scene.unit_settings.scale_length - 1.0) > 1e-9:   # sim/out R2
            raise SystemExit("REFUSING: scene unit scale_length is %r, not 1.0"
                             % scene.unit_settings.scale_length)
        print(">> SET DATUMS: breach plane x = %.4f (ACCESS_GLASS_X %.4f), "
              "Turntable_Deck top z = %.4f, Floor top z = %.4f, "
              "appended in %.1f s"
              % (xs[0], want_x, top, ftop, time.time() - t1))

        # ---- R3: ROUND 1'S EAST GLASS COMES OUT -------------------------
        # `sim/out/apply_requirements.json` R3, measured by the breach agent and
        # not negotiable: the ten `GW_Right_Glass_00..09` are round 1's
        # placeholder east wall -- four verts each, zero-thickness planes lying
        # exactly on x = 15.000 -- and `sim/apply_breach.py` replaces them with
        # real 11.5 mm laminate at x 14.95500..14.96650. Leaving them in puts two
        # east walls 33.5 mm apart: they z-fight through the 33 s of beat 1 that
        # is spent on this glass's reflections, and after the breach the deleted
        # wall's ghost pane is still standing in the aperture.
        #
        # They are deleted AFTER the datum assertion above and not before, so the
        # incoming x = 15.000 is still proved on the way past. The contract's
        # `ACCESS_GLASS_X` is unchanged by this: what moves 33.5 mm inboard is
        # the laminate's outer FACE, not the declared plane.
        if not a.keep_r1_glass:
            req = os.path.join(R2, "sim/out/apply_requirements.json")
            names = ["GW_Right_Glass_%02d" % i for i in range(10)]
            if os.path.exists(req):
                names = json.load(open(req)).get("delete_from_target", names)
            gone = []
            for n in names:
                ob = bpy.data.objects.get(n)
                if ob is not None:
                    bpy.data.objects.remove(ob, do_unlink=True)
                    gone.append(n)
            left = [n for n in names if bpy.data.objects.get(n) is not None]
            if left:
                raise SystemExit("failed to delete round 1 east glass: %s" % left)
            stray = [o.name for o in bpy.data.objects
                     if o.name.startswith("GW_Right_Glass")]
            if stray:
                raise SystemExit(
                    "GW_Right_Glass objects survive the R3 deletion: %s. The "
                    "breach sim would leave a ghost pane in the aperture."
                    % stray)
            front = len([o for o in bpy.data.objects
                         if o.name.startswith("GW_Front_")])
            print(">> R3: deleted %d round-1 east panes %s; %d GW_Front_* (the "
                  "SOUTH wall, y = -11.000) kept, as the contract requires"
                  % (len(gone), gone[:3] + ["..."] if len(gone) > 3 else gone,
                     front))
        else:
            print(">> --keep-r1-glass: the round-1 east wall STAYS. "
                  "sim/apply_breach.py will z-fight against it.")

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
