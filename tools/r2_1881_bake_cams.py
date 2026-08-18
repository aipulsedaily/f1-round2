"""R2-1881: bake FILM-FRAME cameras into an A/B arm, from the DECLARED live camera.

    blender -b --factory-startup -noaudio -P tools/r2_1881_bake_cams.py -- \
        --module world/build_terrain.py --load ARM.blend --save ARM_cams.blend \
        --frames 2760,2832,2933,2089 --manifest work/r2_1881/cams_ARM.json

WHY THIS EXISTS RATHER THAN `tools/r2_1661_rebake.py`
-----------------------------------------------------
`r2_1661_rebake.py` bakes the cameras named in `build_terrain._VIEWS_WORLD`.  Those
entries were lifted from `work/r2941/film17_R2943_path.json` — the path that
rendered the R2943 4K stills — and that file is **not** the camera
`docs/LIVE-CAMERA.md` declares.  Measured, live against R2943, position identical
and aim not:

    f2760   aim  9.51 deg apart   lens  0.000 mm apart
    f2811   aim 15.88 deg apart   lens  2.504 mm apart
    f2937   aim 70.79 deg apart   lens 30.922 mm apart
    f2978   aim 70.79 deg apart   lens 55.996 mm apart   (74.00 live vs 129.99)

At f2760's 81.1 deg horizontal field, 9.51 deg is **450 px of a 3840 px frame**.
So a near-band fix judged on `CAM_b6_2760` is judged on a frame the delivered film
does not contain.  This module therefore takes the camera from `live_campath.load()`,
which takes no path argument and cannot be pointed at the wrong file.

THE ARM-PARITY GUARANTEE, AND IT IS MECHANICAL                            (R2-1151)
-----------------------------------------------------------------------------------
R2-1151: an A/B was reported to the client as "the fix does not work" when arm B had
rendered with a socket unlinked.  An A/B whose arms differ in anything but the change
under test is worthless, and prose does not enforce that.

So this module writes a MANIFEST: for every camera it bakes, the position, the
quaternion, the lens, the sensor, the DOF state, the render resolution and the grade,
plus the sha256 of the camera declaration it read.  Run it on both arms and
`--compare A.json B.json` requires them **byte-identical apart from the arm's own
name**.  If they are not, the A/B is void and it says so before any GPU is bought.

WHAT COMES FROM THE ARM AND WHAT COMES FROM THE DECLARATION
------------------------------------------------------------
  from the ARM'S OWN module   the light, the sky, the road proxy, `setup_render` —
        r2_1661's rule, and it is right: the before arm must be lit by the before
        arm's own sky or the comparison is not a comparison.
  from the DECLARATION        the camera, identically in both arms.

DOF IS FORCED OFF, IN BOTH ARMS, DELIBERATELY.  The r2_1661 arms rendered with
`dof=True` (broker `effective` line, jobs ada0865a2ec0 / 835bb0106384).  The near
band is the FOREGROUND of these frames, and a defocused foreground is the one thing
that would make a scrub tier and an empty field look alike.  Both arms are affected
equally so it does not bias the A/B — but it does destroy the evidence, so it is off,
and it is recorded in the manifest so the choice is visible rather than assumed.
"""
import argparse
import hashlib
import importlib.util
import json
import os
import sys

R2 = os.path.expanduser("~/f1-round2")
sys.path.insert(0, os.path.join(R2, "tools"))
sys.path.insert(0, os.path.join(R2, "world"))

RES = (3840, 2160)
SAMPLES = 512
SENSOR_MM = 36.0


def parse():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--module", help="the ARM's own terrain module, for the sky")
    p.add_argument("--load")
    p.add_argument("--save")
    p.add_argument("--frames", default="2760,2832,2933,2089")
    p.add_argument("--manifest")
    p.add_argument("--seed-view", default="b6_2811",
                   help="any view name, used ONLY to build the light/proxy")
    p.add_argument("--compare", nargs=2, default=None)
    return p.parse_args(argv)


def compare(a, b):
    """Are two arms' camera manifests the same in every way that matters?"""
    A = json.load(open(a))
    B = json.load(open(b))
    keys = ("campath", "campath_sha256", "resolution", "sensor_mm", "samples",
            "view_transform", "look", "exposure", "use_dof", "cameras")
    bad = [k for k in keys if A.get(k) != B.get(k)]
    for k in keys:
        same = A.get(k) == B.get(k)
        if k == "cameras":
            print("  %-16s %s" % (k, "IDENTICAL" if same else "*** DIFFER ***"))
            if not same:
                for nm in sorted(set(A["cameras"]) | set(B["cameras"])):
                    if A["cameras"].get(nm) != B["cameras"].get(nm):
                        print("      %s\n        A %s\n        B %s"
                              % (nm, A["cameras"].get(nm), B["cameras"].get(nm)))
        else:
            print("  %-16s %s   %r" % (k, "same" if same else "*** DIFFER ***",
                                       A.get(k)))
    print(">> STAGE RESULT: %s"
          % ("R2_1881_ARMS_MATCHED" if not bad
             else "R2_1881_ARMS_DIFFER  [%s]" % ",".join(bad)))
    return 0 if not bad else 1


def main():
    a = parse()
    if a.compare:
        sys.exit(compare(*a.compare))

    import bpy
    from mathutils import Quaternion, Vector                       # noqa: F401
    import live_campath as LC

    campath = LC.declared_campath()
    sha = LC.sha256(campath)
    path = LC.load(byframe=True)
    frames = [int(x) for x in a.frames.split(",")]
    missing = [f for f in frames if f not in path]
    if missing:
        raise SystemExit("REFUSING: the live camera has no frames %s" % missing)

    spec = importlib.util.spec_from_file_location("ter_arm", a.module)
    T = importlib.util.module_from_spec(spec)
    sys.modules["ter_arm"] = T
    spec.loader.exec_module(T)

    if a.load:
        bpy.ops.wm.open_mainfile(filepath=a.load)
    sc = bpy.context.scene

    # the ARM's own light, sky and proxy — and its own `setup_render` grade
    T.test_scene(a.seed_view)
    T.setup_render(sc, SAMPLES, RES)

    gone = [o.name for o in list(bpy.data.objects) if o.type == "CAMERA"]
    for o in list(bpy.data.objects):
        if o.type == "CAMERA":
            bpy.data.objects.remove(o, do_unlink=True)
    print("[bake] removed %d cameras from the arm: %s" % (len(gone), gone))

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
        cd.dof.use_dof = False                 # see the docstring
        ob = bpy.data.objects.new(nm, cd)
        col.objects.link(ob)
        ob.location = tuple(float(v) for v in e["p"])
        ob.rotation_mode = "QUATERNION"
        # RE-NORMALISE.  The path file rounds quaternions to six decimals (R2-103,
        # R2-325) so |q| is off unit by ~4e-7, and Blender does NOT normalise what it
        # is handed — it folds the residual into the object matrix as scale.  The bake
        # verifier caught this as 9.9e-3 deg of aim and 0.067 px of reprojection at
        # f2089; small, and exactly the kind of small that an A/B cannot afford.
        qn = Quaternion([float(v) for v in e["q"]])
        qn.normalize()
        ob.rotation_quaternion = qn
        cams[nm] = {"f": f,
                    "p": [round(float(v), 6) for v in e["p"]],
                    "q": [round(float(v), 6) for v in e["q"]],
                    "q_normalised": [round(float(v), 12) for v in qn],
                    "lens": round(float(e["lens"]), 6)}
    sc.camera = bpy.data.objects["CAM_f%04d" % frames[0]]

    man = {
        "arm_blend": a.save,
        "module": a.module,
        "campath": os.path.relpath(campath, R2),
        "campath_sha256": sha,
        "resolution": list(RES),
        "sensor_mm": SENSOR_MM,
        "samples": SAMPLES,
        "view_transform": sc.view_settings.view_transform,
        "look": getattr(sc.view_settings, "look", None),
        "exposure": round(float(sc.view_settings.exposure), 6),
        "use_dof": False,
        "cameras": cams,
    }

    bpy.ops.wm.save_as_mainfile(filepath=a.save)
    if a.manifest:
        os.makedirs(os.path.dirname(a.manifest), exist_ok=True)
        json.dump(man, open(a.manifest, "w"), indent=1, sort_keys=True)

    have = sorted(o.name for o in bpy.data.objects if o.type == "CAMERA")
    ok = (have == sorted(cams)
          and man["view_transform"] == "AgX"
          and abs(man["exposure"] + 3.628) < 1e-6
          and (man["look"] in (None, "None", "AgX - None")))
    print(">> grade: %s look=%r exposure %.4f  res %dx%d  dof off"
          % (man["view_transform"], man["look"], man["exposure"], *RES))
    print(">> cameras in file: %s" % have)
    print(">> STAGE RESULT: %s %s"
          % ("R2_1881_BAKE_CAMS_OK" if ok else "R2_1881_BAKE_CAMS_FAIL",
             json.dumps({"save": a.save, "frames": frames,
                         "campath_sha256": sha[:16],
                         "manifest": a.manifest})))


main()
