"""READ THE ARTEFACT BACK. What a saved film scene actually contains.

    /opt/blender-5.2.0-linux-x64/blender -b <scene.blend> --factory-startup \
        -P work/lighting/measure_film_scene.py -- --json <out.json>

WHY THIS EXISTS
---------------
`render/film9.blend` shipped un-relit and the build log said it was fine. The
build log is not the artefact. This opens the saved blend and reports the two
numbers that settle it -- the interior lamp load in watts and the count of
`_sl_base` stamps -- plus every datum `build_film_scene.py` asserts, so a
rebuild can be checked against the file rather than against its own stdout.

It NEVER writes. It is an instrument, and an instrument that can modify its
subject is not one.
"""
import json
import os
import sys

import bpy

R2 = "/home/zany/f1-round2"
sys.path.insert(0, os.path.join(R2, "world"))


def main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    out = argv[argv.index("--json") + 1] if "--json" in argv else None

    scene = bpy.context.scene
    import showroom_lighting as SL
    import film_exposure as FX

    m = SL.measure(scene)

    # the stamps, counted on the datablocks themselves
    lamp_stamped = [l.name for l in bpy.data.lights if SL.MARK + "energy" in l.keys()]
    mat_stamped = sorted(set(
        mat.name for mat in bpy.data.materials
        for k in mat.keys() if k.startswith(SL.MARK + "emit:")))

    # every lamp in the scene, not just the ones classified interior
    all_lamps = [o for o in scene.objects if o.type == "LIGHT"]
    sky_lamps = [o.name for o in all_lamps if o.name.startswith("SKY_")]
    lamp_watts_all = round(sum(float(o.data.energy) for o in all_lamps), 3)

    cams = []
    for o in scene.objects:
        if o.type == "CAMERA":
            cams.append({"name": o.name, "clip_start": round(o.data.clip_start, 4),
                         "clip_end": round(o.data.clip_end, 1),
                         "is_scene_camera": scene.camera is not None
                         and o.name == scene.camera.name})

    def _top(name):
        ob = bpy.data.objects.get(name)
        if ob is None or ob.type != "MESH":
            return None
        return round(max((ob.matrix_world @ v.co).z for v in ob.data.vertices), 4)

    glass = bpy.data.objects.get("GW_Right_Glass_00")
    glass_x = None
    if glass is not None and glass.type == "MESH":
        xs = [(glass.matrix_world @ v.co).x for v in glass.data.vertices]
        glass_x = [round(min(xs), 5), round(max(xs), 5)]

    vit = [o.name for o in bpy.data.objects if o.name.startswith("Vitrine_")]
    car_root = bpy.data.objects.get("CAR_ROOT")

    rep = {
        "file": bpy.data.filepath,
        "bytes": os.path.getsize(bpy.data.filepath) if bpy.data.filepath else None,
        # THE TWO NUMBERS
        "interior_lamp_watts": m["interior_lamp_watts"],
        "n_interior_lamps": m["n_interior_lamps"],
        "n_lamp_stamps__sl_base": len(lamp_stamped),
        "n_material_stamps__sl_base": len(mat_stamped),
        "scene_mark_showroom_lighting_stops": m["scene_mark"],
        "expected_lift_stops": SL.LIFT_STOPS,
        "n_interior_emissive_materials": m["n_interior_emissive_materials"],
        "interior_emission_strength_sum": m["interior_emission_strength_sum"],
        # everything else
        "lamp_watts_all_objects": lamp_watts_all,
        "n_lamps_all": len(all_lamps),
        "sky_lamps": sky_lamps,
        "world": scene.world.name if scene.world else None,
        "engine": scene.render.engine,
        "view_transform": scene.view_settings.view_transform,
        "look": scene.view_settings.look,
        "exposure": round(scene.view_settings.exposure, 4),
        "film_exposure_declared": FX.FILM_EXPOSURE,
        "frame_start": scene.frame_start, "frame_end": scene.frame_end,
        "fps": scene.render.fps,
        "scale_length": scene.unit_settings.scale_length,
        "collections": sorted(c.name for c in scene.collection.children),
        "n_objects": len(scene.objects),
        "n_objects_data": len(bpy.data.objects),
        "cameras": cams,
        "scene_camera": scene.camera.name if scene.camera else None,
        # R2-2821.  THE BAR ASKED THIS FILE FOR FIVE KEYS IT NEVER EMITTED.
        # v124, v125 and v126 all did `if k in m: chk(...) else: print NOT
        # REPORTED` over 'resolution_x', 'resolution_y', 'clip_start',
        # 'clip_end' and 'camera'.  None of the five was here -- there was
        # 'cameras' (a list) and 'scene_camera' (a name), and no resolution and
        # no clip at all -- so the delivery format, the oner and the clip range
        # printed 'NOT REPORTED' on every film this project has ever verified
        # and were counted as NEITHER pass nor fail.  A check that reads a key
        # nobody emits is indistinguishable from a check that passed.
        #
        # These are the SAME numbers under the names the bar asks for.  They
        # are flat scalars on purpose: 'cameras' is a list, and a bar line that
        # has to index a list to find the scene camera is one refactor away
        # from silently reading the wrong camera.
        "resolution_x": scene.render.resolution_x,
        "resolution_y": scene.render.resolution_y,
        "resolution_percentage": scene.render.resolution_percentage,
        "camera": scene.camera.name if scene.camera else None,
        "clip_start": (None if scene.camera is None
                       else round(scene.camera.data.clip_start, 6)),
        "clip_end": (None if scene.camera is None
                     else round(scene.camera.data.clip_end, 3)),
        "n_cameras_in_scene": len(cams),
        "GW_Right_Glass_00_x": glass_x,
        "n_GW_Right_Glass": len([o for o in bpy.data.objects
                                 if o.name.startswith("GW_Right_Glass")]),
        "n_GW_Front": len([o for o in bpy.data.objects
                           if o.name.startswith("GW_Front_")]),
        "Turntable_Deck_top_z": _top("Turntable_Deck"),
        "Floor_top_z": _top("Floor"),
        "n_Vitrine": len(vit),
        "n_Vitrine_parented_to_CAR_ROOT": len(
            [o for o in bpy.data.objects if o.name.startswith("Vitrine_")
             and car_root is not None and o.parent is car_root]),
        "CAR_ROOT_animated": bool(car_root and car_root.animation_data
                                  and car_root.animation_data.action),
        "n_CARRIG": len([o for o in bpy.data.objects
                         if o.name.startswith("CARRIG_")]),
        "lamp_stamped_examples": sorted(lamp_stamped)[:8],
    }

    # THE VERDICT, computed here rather than left to a reader
    try:
        SL.assert_levelled(scene)
        rep["assert_levelled"] = "PASS"
    except SystemExit as e:
        rep["assert_levelled"] = "REFUSED: %s" % e

    print(json.dumps(rep, indent=1, sort_keys=True))
    if out:
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        json.dump(rep, open(out, "w"), indent=1, sort_keys=True)
        print(">> wrote %s" % out)
    print(">> STAGE RESULT: MEASURE_FILM_SCENE_DONE")


main()
