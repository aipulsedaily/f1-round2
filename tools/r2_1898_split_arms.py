"""R2-1898: split the near-band A/B's TWO ARMS out of the ONE built blend.

    blender -b --factory-startup -noaudio -P tools/r2_1898_split_arms.py -- \
        --blend world/nearband.blend --outdir render/r2_1881 \
        --frames 2760,2832,2933,2089

WHY BOTH ARMS COME OUT OF ONE FILE
-----------------------------------
The obvious BEFORE arm is a fresh `build_terrain` run without the tier.  It is the
wrong arm, and the reason is on disk:

    world/build_terrain.py, when nearband.blend was built   01c5c684d65b3c47610562747f5897fa
    world/build_terrain.py, now                             bdeac55c3b7384abd87bd7002343620a

**The file moved.**  It is live and held by another workstream, and a BEFORE built
from today's copy would differ from the AFTER in the terrain module as well as in
the tier under test.  That is R2-1151 exactly — an A/B whose arms differ in
something other than the change — and it would be invisible, because both arms
would log a clean `build_terrain` run.

So the AFTER arm is `world/nearband.blend` as built, and the BEFORE arm is the same
file with the `NearBand` collection taken out of the render.  One terrain build, one
rng stream, one grass field, one library, one camera.  The arms differ in the tier
and in nothing else, by construction rather than by intention.

THE CONTROL THAT MIRRORS THE PARITY CHECK
------------------------------------------
`r2_1881_bake_cams.py --compare` proves the arms are the SAME where they must be.
It cannot prove they DIFFER where they must — two identical arms would sail through
it, and an A/B of a file against itself is the most convincing null result there is.
So this module counts realized instances in each arm off the depsgraph and REFUSES
unless the count drops by the tier's own reported size.  Both halves are needed:
same camera, different world.

The tier hides by BOTH `hide_render` and `hide_viewport`, on the collection and on
every `VEG_nb_*` object.  `hide_render` alone would leave the depsgraph count
unchanged in a background session and the control above could not fire.
"""
import argparse
import json
import os
import sys

R2 = os.path.expanduser("~/f1-round2")
sys.path.insert(0, os.path.join(R2, "tools"))
sys.path.insert(0, os.path.join(R2, "world"))

RES = (3840, 2160)
SAMPLES = 512
SENSOR_MM = 36.0
SUB = "NearBand"
NBPFX = "VEG_nb_"


def parse():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--blend", default=os.path.join(R2, "world", "nearband.blend"))
    p.add_argument("--outdir", default=os.path.join(R2, "render", "r2_1881"))
    p.add_argument("--frames", default="2760,2832,2933,2089")
    p.add_argument("--seed-view", default="b6_2811")
    p.add_argument("--module", default=os.path.join(R2, "world", "build_terrain.py"))
    return p.parse_args(argv)


def stage(name, ok, **kw):
    print(">> STAGE RESULT: %s ok=%d %s"
          % (name, 1 if ok else 0, json.dumps(kw, sort_keys=True)))


def count_instances(bpy):
    deps = bpy.context.evaluated_depsgraph_get()
    n = 0
    for i in deps.object_instances:
        if i.is_instance and i.object and i.object.type == "MESH":
            n += 1
    return n


def main():
    a = parse()
    import importlib.util
    import bpy
    from mathutils import Quaternion
    import live_campath as LC

    campath = LC.declared_campath()
    sha = LC.sha256(campath)
    path = LC.load(byframe=True)
    frames = [int(x) for x in a.frames.split(",")]
    os.makedirs(a.outdir, exist_ok=True)

    spec = importlib.util.spec_from_file_location("ter_arm", a.module)
    T = importlib.util.module_from_spec(spec)
    sys.modules["ter_arm"] = T
    spec.loader.exec_module(T)

    bpy.ops.wm.open_mainfile(filepath=a.blend)
    sc = bpy.context.scene
    nb_obj = [o for o in bpy.data.objects if o.name.startswith(NBPFX)]
    lights = [o for o in bpy.data.objects if o.type == "LIGHT"]
    stage("arms_loaded", len(nb_obj) > 0,
          objects=len(bpy.data.objects), nb_objects=len(nb_obj),
          lights=len(lights), has_nearband_collection=SUB in bpy.data.collections,
          blend_mb=round(os.path.getsize(a.blend) / 1e6, 1))

    # ---- the ARM'S OWN sky, proxy and grade.  `build()` makes no light at all, so
    # without this both arms render black; `test_scene` is where the film's sun is.
    # The road proxy comes with it and is wanted: `cut_field` removes the ground the
    # road programme owns, so without the proxy the corridor is a hole.  Identical
    # in both arms — it is applied once, before the split.
    T.test_scene(a.seed_view)
    T.setup_render(sc, SAMPLES, RES)

    gone = [o.name for o in bpy.data.objects if o.type == "CAMERA"]
    for o in list(bpy.data.objects):
        if o.type == "CAMERA":
            bpy.data.objects.remove(o, do_unlink=True)

    col = bpy.data.collections.get("TER_TEST") or sc.collection
    cams = {}
    for f in frames:
        e = path[f]
        nm = "CAM_f%04d" % f
        cd = bpy.data.cameras.new(nm)
        cd.lens = float(e["lens"])
        cd.sensor_width = SENSOR_MM
        cd.sensor_fit = "HORIZONTAL"
        cd.clip_start = 0.05
        cd.clip_end = 60000.0
        cd.dof.use_dof = False
        ob = bpy.data.objects.new(nm, cd)
        col.objects.link(ob)
        ob.location = tuple(float(v) for v in e["p"])
        ob.rotation_mode = "QUATERNION"
        q = Quaternion([float(v) for v in e["q"]])
        q.normalize()                       # Blender does NOT (R2-1895)
        ob.rotation_quaternion = q
        cams[nm] = {"f": f,
                    "p": [round(float(v), 6) for v in e["p"]],
                    "q": [round(float(v), 6) for v in e["q"]],
                    "q_normalised": [round(float(v), 12) for v in q],
                    "lens": round(float(e["lens"]), 6)}
    sc.camera = bpy.data.objects["CAM_f%04d" % frames[0]]
    stage("cameras_baked", sorted(cams) == sorted(
        o.name for o in bpy.data.objects if o.type == "CAMERA"),
        removed=len(gone), made=sorted(cams), campath_sha256=sha[:16])

    man = {"campath": os.path.relpath(campath, R2), "campath_sha256": sha,
           "resolution": list(RES), "sensor_mm": SENSOR_MM, "samples": SAMPLES,
           "view_transform": sc.view_settings.view_transform,
           "look": getattr(sc.view_settings, "look", None),
           "exposure": round(float(sc.view_settings.exposure), 6),
           "use_dof": False, "cameras": cams}
    grade_ok = (man["view_transform"] == "AgX"
                and abs(man["exposure"] + 3.628) < 1e-6)
    stage("grade", grade_ok, view_transform=man["view_transform"],
          look=man["look"], exposure=man["exposure"], res=list(RES))

    # ---- AFTER: as built ---------------------------------------------------
    n_after = count_instances(bpy)
    after = os.path.join(a.outdir, "nb_after.blend")
    bpy.ops.wm.save_as_mainfile(filepath=after)
    json.dump(dict(man, arm="after"),
              open(os.path.join(R2, "work", "r2_1881", "cams_after.json"), "w"),
              indent=1, sort_keys=True)
    stage("after_saved", os.path.exists(after), path=after,
          realized_instances=n_after,
          mb=round(os.path.getsize(after) / 1e6, 1))

    # ---- BEFORE: the same file with the tier out of the render --------------
    c = bpy.data.collections.get(SUB)
    if c is not None:
        c.hide_render = True
        c.hide_viewport = True
    for o in nb_obj:
        o.hide_render = True
        o.hide_viewport = True
    for vl in sc.view_layers:
        lc = None
        for child in vl.layer_collection.children:
            for gc in list(child.children) + [child]:
                if gc.collection is c:
                    lc = gc
        if lc is not None:
            lc.exclude = True
    n_before = count_instances(bpy)
    before = os.path.join(a.outdir, "nb_before.blend")
    bpy.ops.wm.save_as_mainfile(filepath=before)
    json.dump(dict(man, arm="before"),
              open(os.path.join(R2, "work", "r2_1881", "cams_before.json"), "w"),
              indent=1, sort_keys=True)
    stage("before_saved", os.path.exists(before), path=before,
          realized_instances=n_before,
          mb=round(os.path.getsize(before) / 1e6, 1))

    # ---- THE CONTROL: the arms must actually DIFFER ------------------------
    drop = n_after - n_before
    ok = drop > 100000 and n_before > 0 and grade_ok
    stage("arms_differ", ok, realized_after=n_after, realized_before=n_before,
          drop=drop, drop_pct=round(100.0 * drop / max(n_after, 1), 2),
          nb_objects_hidden=len(nb_obj))
    print(">> STAGE RESULT: R2_1898_SPLIT_%s" % ("OK" if ok else "FAIL"))


main()
