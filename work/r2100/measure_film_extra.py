"""THE LEVELLING IDENTITY, RECOMPUTED FROM THE ARTEFACT'S OWN STAMPS.

    /opt/blender-5.2.0-linux-x64/blender -b <film.blend> --factory-startup \
        -P work/r2100/measure_film_extra.py -- <out.json>

`work/lighting/measure_film_scene.py` reads back the levelled load (46,203 W)
and counts the `_sl_base` stamps (23). It does not read the stamps' VALUES, so
the identity everything rests on --

    3,737.113 W  x  2 ** 3.628  =  46,203.4 W

-- is checked against a number remembered from the build log rather than
against the file. That is exactly the substitution R2-071 is about. Every term
here comes out of the saved blend: the base watts from the `_sl_base` custom
properties, the lift from the scene's own mark, and the levelled watts from the
lamps themselves.

It NEVER writes to the blend.
"""
import json
import os
import sys

import bpy

R2 = "/home/zany/f1-round2"
sys.path.insert(0, os.path.join(R2, "world"))

argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else []
out = argv[0] if argv else None

import showroom_lighting as SL                                   # noqa: E402
import film_exposure as FX                                       # noqa: E402

scene = bpy.context.scene
m = SL.measure(scene)

base_key = SL.MARK + "energy"
stamped = {}
for ld in bpy.data.lights:
    if base_key in ld.keys():
        stamped[ld.name] = {"base_w": round(float(ld[base_key]), 6),
                            "now_w": round(float(ld.energy), 6)}
base_sum = round(sum(v["base_w"] for v in stamped.values()), 3)
now_sum = round(sum(v["now_w"] for v in stamped.values()), 3)
mark = scene.get(SL.SCENE_MARK)
lift = None if mark is None else 2.0 ** float(mark)
predicted = None if lift is None else round(base_sum * lift, 3)

# per-lamp, so a single lamp that missed the lift cannot hide in a total
worst = None
for n, v in stamped.items():
    if v["base_w"] == 0:
        continue
    r = v["now_w"] / v["base_w"]
    if lift and (worst is None or abs(r - lift) > abs(worst[1] - lift)):
        worst = (n, r)

cam = scene.camera
res = (scene.render.resolution_x, scene.render.resolution_y,
       scene.render.resolution_percentage)

rep = {
    "file": bpy.data.filepath,
    "bytes": os.path.getsize(bpy.data.filepath) if bpy.data.filepath else None,
    "scene_mark": None if mark is None else round(float(mark), 6),
    "lift_multiplier": None if lift is None else round(lift, 6),
    "n_lamp_stamps": len(stamped),
    "base_watts_from_stamps": base_sum,
    "levelled_watts_from_stamps": now_sum,
    "identity_base_x_lift": predicted,
    "interior_lamp_watts_measured": m["interior_lamp_watts"],
    "identity_residual_w": (None if predicted is None
                            else round(now_sum - predicted, 6)),
    "worst_per_lamp_ratio": (None if worst is None
                             else {"lamp": worst[0],
                                   "ratio": round(worst[1], 9),
                                   "want": round(lift, 9)}),
    "film_exposure_declared": FX.FILM_EXPOSURE,
    "scene_exposure": round(scene.view_settings.exposure, 6),
    "lift_plus_exposure": round(float(mark) + FX.FILM_EXPOSURE, 9)
    if mark is not None else None,
    "camera": None if cam is None else {
        "name": cam.name, "clip_start": round(cam.data.clip_start, 6),
        "clip_end": round(cam.data.clip_end, 3),
        "data_fcurves": None, "object_fcurves": None,
    },
    "n_cameras_in_scene": len([o for o in scene.objects if o.type == "CAMERA"]),
    "resolution": res,
    "frames": [scene.frame_start, scene.frame_end, scene.render.fps],
    "scale_length": scene.unit_settings.scale_length,
    "n_Vitrine": len([o for o in bpy.data.objects
                      if o.name.startswith("Vitrine_")]),
    "n_GW_Right_Glass": len([o for o in bpy.data.objects
                             if o.name.startswith("GW_Right_Glass")]),
    "ACCESS_GLASS_X_from_contract": None,
    "GW_Front_min_x": None,
}

def _fcurves(id_data):
    """F-curve count, across the 4.4+ slotted-action API AND the old flat one.

    Blender 5.2's `Action` has no `.fcurves`: the curves live in
    layers -> strips -> channelbags. Reading zero because the attribute moved
    would look exactly like a camera with no animation, which is the defect
    R2-064/R2-071 keep producing, so both shapes are tried and a failure to
    read is reported as None rather than as 0.
    """
    ad = getattr(id_data, "animation_data", None)
    act = getattr(ad, "action", None) if ad else None
    if act is None:
        return 0
    n = getattr(act, "fcurves", None)
    if n is not None:
        return len(n)
    tot = 0
    try:
        for lay in act.layers:
            for st in lay.strips:
                for cb in getattr(st, "channelbags", []):
                    tot += len(cb.fcurves)
    except Exception:                                            # noqa: BLE001
        return None
    return tot


if cam is not None:
    rep["camera"]["data_fcurves"] = _fcurves(cam.data)
    rep["camera"]["object_fcurves"] = _fcurves(cam)

try:
    import world_contract as WC
    rep["ACCESS_GLASS_X_from_contract"] = float(WC.ACCESS_GLASS_X)
except Exception as exc:                                         # noqa: BLE001
    rep["ACCESS_GLASS_X_from_contract"] = "unreadable: %r" % (exc,)

# The round-1 east panes are DELETED by build_film_scene (R3), so the breach
# plane cannot be read off them in the finished file -- `GW_Right_Glass_00_x`
# is null in the film11 readback for the same reason. What CAN be read back is
# the laminate the breach sim replaces them with, if it is in yet, and the fact
# that no round-1 pane survived.
xs = []
for o in bpy.data.objects:
    if o.type == "MESH" and o.name.startswith("GW_") and "Glass" in o.name:
        xs += [(o.matrix_world @ v.co).x for v in o.data.vertices]
rep["all_GW_glass_x_range"] = ([round(min(xs), 5), round(max(xs), 5)]
                               if xs else None)

for nm, key in (("Turntable_Deck", "Turntable_Deck_top_z"),
                ("Floor", "Floor_top_z")):
    ob = bpy.data.objects.get(nm)
    rep[key] = (None if ob is None or ob.type != "MESH"
                else round(max((ob.matrix_world @ v.co).z
                               for v in ob.data.vertices), 6))

rep["n_Vitrine_parented_to_CAR_ROOT"] = len(
    [o for o in bpy.data.objects if o.name.startswith("Vitrine_")
     and o.parent is not None and o.parent.name == "CAR_ROOT"])

try:
    SL.assert_levelled(scene)
    rep["assert_levelled"] = "PASS"
except SystemExit as exc:
    rep["assert_levelled"] = "REFUSED: %s" % exc

print(json.dumps(rep, indent=1, default=str))
if out:
    json.dump(rep, open(out, "w"), indent=1, default=str)
print("STAGE RESULT: FILM_EXTRA_MEASURED")
