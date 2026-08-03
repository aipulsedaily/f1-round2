"""The scene's EVALUATED view exposure, per frame. R2-064/R2-067's evidence.

    /opt/blender-5.2.0-linux-x64/blender -b <scene.blend> --factory-startup \
        -P tools/dump_exposure.py -- --out <exposure.json> --frames 1 2978

`world/film_exposure.py` carries INTERIOR_STOPS = 0.0 and the rig therefore
keys its interior->daylight ramp with both ends equal. That is a statement
about a CONSTANT; this reads the value the scene actually evaluates on every
frame, because "the constant is 0.0" and "the picture does not change exposure"
are different claims and only one of them is what the brief forbids.
"""
import argparse, json, sys
import bpy

argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True)
ap.add_argument("--frames", type=int, nargs=2, default=[1, 2978])
a = ap.parse_args(argv)

sc = bpy.context.scene
out = {}
for f in range(a.frames[0], a.frames[1] + 1):
    sc.frame_set(f)
    out[str(f)] = float(sc.view_settings.exposure)
json.dump(out, open(a.out, "w"))
vals = list(out.values())
print(f">> exposure over frames {a.frames[0]}-{a.frames[1]}: "
      f"{min(vals):+.6f} .. {max(vals):+.6f}  span {max(vals)-min(vals):.3e} stops")
print(f">> view transform {sc.view_settings.view_transform}, look "
      f"{sc.view_settings.look}")
print(">> STAGE RESULT: EXPOSURE_DUMP_OK")
