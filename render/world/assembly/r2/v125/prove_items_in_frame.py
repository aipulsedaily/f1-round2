"""RENDER A FRAME AND COUNT ITEM PIXELS.  Task #121's actual claim.

    /opt/blender-5.2.0-linux-x64/blender -b render/film16.blend --factory-startup \
        -P render/world/assembly/r2/v125/prove_items_in_frame.py -- \
        --frames 2000,2635,2900 --res 480 --samples 24 --out work/r2500/items_in_frame.json

WHY THIS EXISTS AND WHY THE PLACEMENT REPORT IS NOT IT
------------------------------------------------------
`build_items` reporting `ITEMS_PLACED_OK` says the stage ran and linked objects
into the scene.  Task #121 is not that claim -- it is *"nothing built in
`world/items/` has ever reached a FRAME"*.  An object can be in a scene and be
behind a wall, outside the frustum, or one pixel wide for the whole take.  Those
are different statements and this project has been burned by the gap.

So this measures PIXELS, through the film's own ONER camera, at the film's own
frames.

HOW, AND WHY IT CANNOT REPORT A FALSE POSITIVE
----------------------------------------------
Every object gets `pass_index` from its name prefix -- 1 CFP_, 2 CRF_, 3 TS_,
4 SPECX_, 5 DRV_ -- and everything else keeps 0.  The IndexOB pass is then a
per-pixel integer saying which family the camera actually saw, resolved through
real occlusion and real depth.  A count > 0 for a family means the camera hit
that family's geometry in that frame.  There is no way to score a pixel for an
item that is not on screen.

THE NEGATIVE CONTROL IS IN THE SAME RUN.  Index 6 is assigned to a family that
does not exist (`ZZZ_NOTHING_`), and its count MUST be 0.  If a nonexistent
family scores pixels, the mapping is wrong and every positive count in the same
table is worthless.  A gate that has only ever been run on a scene where the
answer is yes has not been tested.

Blender 5.2 exits 0 on an uncaught script exception.  Judge on STAGE RESULT.
"""
import argparse
import json
import os
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--frames", default="2000,2635,2900")
ap.add_argument("--res", type=int, default=480)
ap.add_argument("--samples", type=int, default=24)
ap.add_argument("--out", default="/home/zany/f1-round2/work/r2500/items_in_frame.json")
a = ap.parse_args(argv)

FAMILIES = [("CFP_", 1, "catch_fence_post"), ("CRF_", 2, "crew_figure"),
            ("TS_", 3, "timing_stand"), ("SPECX_", 4, "spectator_crowd_world"),
            ("DRV_", 5, "driver"), ("ZZZ_NOTHING_", 6, "NEGATIVE CONTROL")]

sc = bpy.context.scene
print(">> scene %r camera %r  %dx%d  frames %d-%d"
      % (sc.name, sc.camera.name if sc.camera else None,
         sc.render.resolution_x, sc.render.resolution_y,
         sc.frame_start, sc.frame_end))

counts_scene = {p: 0 for p, _, _ in FAMILIES}
for ob in bpy.data.objects:
    for pref, idx, _ in FAMILIES:
        if ob.name.startswith(pref):
            ob.pass_index = idx
            counts_scene[pref] += 1
            break
print(">> objects tagged per family: %s" % counts_scene)

sc.render.engine = "CYCLES"
sc.cycles.samples = a.samples
sc.cycles.use_denoising = False
try:
    sc.cycles.device = "CPU"
except Exception:
    pass
sc.render.resolution_x = a.res
sc.render.resolution_y = int(round(a.res * 2160.0 / 3840.0))
sc.render.resolution_percentage = 100
sc.render.film_transparent = False
vl = sc.view_layers[0]
vl.use_pass_object_index = True

sc.use_nodes = True
nt = sc.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
rl = nt.nodes.new("CompositorNodeRLayers")
vw = nt.nodes.new("CompositorNodeViewer")
nt.links.new(rl.outputs["IndexOB"], vw.inputs["Image"])

report = {"frames": {}, "objects_tagged": counts_scene,
          "res": [sc.render.resolution_x, sc.render.resolution_y],
          "samples": a.samples}
ok_any = False
control_clean = True

for f in [int(x) for x in a.frames.split(",") if x.strip()]:
    sc.frame_set(f)
    bpy.ops.render.render(write_still=False)
    img = bpy.data.images.get("Viewer Node")
    px = list(img.pixels)
    n = len(px) // 4
    hist = {}
    for i in range(n):
        v = int(round(px[i * 4]))
        if v:
            hist[v] = hist.get(v, 0) + 1
    row = {}
    for pref, idx, label in FAMILIES:
        c = hist.get(idx, 0)
        row[label] = c
        if label == "NEGATIVE CONTROL":
            if c:
                control_clean = False
        elif c:
            ok_any = True
    total_px = n
    report["frames"][f] = {"counts": row, "total_px": total_px}
    print(">> f%-5d of %d px: %s" % (f, total_px, row))

report["negative_control_clean"] = control_clean
report["any_item_on_screen"] = ok_any
os.makedirs(os.path.dirname(a.out), exist_ok=True)
with open(a.out, "w") as fh:
    json.dump(report, fh, indent=1)

if not control_clean:
    print(">> STAGE RESULT: ITEM_PIXELS_INSTRUMENT_BROKEN "
          "-- a family with no objects scored pixels")
elif ok_any:
    print(">> STAGE RESULT: ITEMS_REACHED_A_FRAME")
else:
    print(">> STAGE RESULT: ITEMS_NEVER_ON_SCREEN")
