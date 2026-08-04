"""R2-179 A/B: the timing-stand deck seen from the film's own frame-1126 lens.

    blender -b <ts_test.blend> --factory-startup -P tools/r2179_ab_build.py -- \
            --out render/r2179/<tag>.blend [--frame 1126]

WHY THIS AND NOT `render/film14.blend`.
--------------------------------------
The brief asked for frame 1126 rendered before and after. It cannot be, from
the shipping film, and the reason is the finding:

    **`timing_stand` has never been placed into the assembled world.** `TS_`
    appears **0 times** in `work/r2148/fp_assembly9.json`, the per-object
    fingerprint of all 28,781 objects in the shipping world, and the strings
    `TS_Stand`, `W_Item_TimingStand` and `MPD_Deck` appear **0 times** in the
    4.53 GB `render/film14.blend` -- against `ARCH_PitWall`, which appears,
    as the positive control for that test. `docs/screen_presence.json` scores
    this item against `hosts: ["ARCH_PitWall"]`, i.e. against the pit wall
    standing in for geometry that was never built into the scene.

So rendering f1126 from `film14` before and after this fix would produce two
IDENTICAL images, and their identity would say nothing whatever about the
fix -- it is exactly the manufactured null R2-108 records.

What IS true is that the camera and the frame are right. Frame 1126 of
`render/film14_path.json` sits at (140.717, 38.878, 16.735) on a 35 mm lens,
and `TS_Stand00_BOREAL` -- whose world position comes from the module's own
`stand_records()`, not from the scene -- lands **27.88 m away, at pixel
(1607, 2016) of 3840x2160, its 2.903 m deck spanning 402 px**, looked down on
from 16.05 m above the deck. That is the presentation the defect is about.

So this puts the FILM'S OWN CAMERA, read from the film's own path file, into
the item's test blend, and renders the two builds through it. Same camera,
same lens, same pose, same seed, one variable.

Determinism is pinned the way `tools/glass_winding_ab_build.py` pins it, and
for its reason: adaptive sampling and denoising both make a pixel diff a
measurement of the sampler.
"""
import argparse
import json
import math
import os
import sys

import bpy
from mathutils import Quaternion, Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "world"))

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True)
ap.add_argument("--frame", type=int, default=1126)
ap.add_argument("--path", default=os.path.join(ROOT, "render",
                                               "film14_path.json"))
ap.add_argument("--samples", type=int, default=256)
ap.add_argument("--res", type=int, nargs=2, default=[3840, 2160])
a = ap.parse_args(argv)

key = {int(k["f"]): k for k in json.load(open(a.path))["path"]}[a.frame]

cd = bpy.data.cameras.new("CAM_F%d" % a.frame)
cd.lens = float(key["lens"])
cd.sensor_width = 36.0
cd.dof.use_dof = False
cam = bpy.data.objects.new("CAM_F%d" % a.frame, cd)
bpy.context.scene.collection.objects.link(cam)
cam.rotation_mode = "QUATERNION"
cam.location = Vector(tuple(key["p"]))
cam.rotation_quaternion = Quaternion(tuple(key["q"]))

sc = bpy.context.scene
sc.camera = cam
sc.render.engine = "CYCLES"
sc.render.resolution_x, sc.render.resolution_y = a.res
sc.render.resolution_percentage = 100
sc.cycles.samples = a.samples
sc.cycles.use_adaptive_sampling = False
sc.cycles.use_denoising = False
sc.cycles.seed = 0
sc.cycles.use_animated_seed = False
sc.cycles.max_bounces = 12
sc.render.film_transparent = False

try:
    import film_exposure as FX
    FX.apply(sc)
    print(">> film grade applied, exposure %.3f" % FX.FILM_EXPOSURE)
except Exception as e:                                            # noqa: BLE001
    print(">> WARNING: film grade NOT applied (%s); both arms share this, so "
          "the A/B is still valid, but the absolute look is not the film's"
          % e)

# THE SUBJECT MUST BE IN THE PICTURE, AND SAYING SO IS NOT OPTIONAL. R2-172's
# EMPTY_SCENE assert exists because a flawless render of nothing is a flawless
# render. Project the stand's own deck corner and require it on screen.
stands = [o for o in sc.objects if o.name.startswith("TS_Stand")]
if not stands:
    raise SystemExit("EMPTY SCENE: no TS_Stand* object in %s"
                     % bpy.data.filepath)
R = cam.rotation_quaternion.to_matrix()
W, H = a.res
onscreen = []
for ob in stands:
    c = ob.matrix_world.translation
    v = R.transposed() @ (c - cam.location)
    if v.z >= 0:
        continue
    px = W * 0.5 + (v.x / -v.z) * (cd.lens / cd.sensor_width) * W
    py = H * 0.5 - (v.y / -v.z) * (cd.lens / cd.sensor_width) * W
    if 0 <= px < W and 0 <= py < H:
        onscreen.append((ob.name, round(px), round(py), round(-v.z, 2)))
print(">> %d of %d stands on screen: %s" % (len(onscreen), len(stands),
                                            onscreen))
if not onscreen:
    raise SystemExit("SUBJECT NOT IN FRAME: nothing to A/B. Refusing to write "
                     "a blend that would render a convincing null.")

p = os.path.abspath(a.out)
os.makedirs(os.path.dirname(p), exist_ok=True)
ext = [i.filepath for i in bpy.data.images if i.source == "FILE"]
if ext:
    raise SystemExit("REFUSING TO SAVE: external images %s" % ext)
bpy.ops.wm.save_as_mainfile(filepath=p, compress=True, relative_remap=False)
print(">> wrote %s (%.1f MB)" % (p, os.path.getsize(p) / 1048576.0))
