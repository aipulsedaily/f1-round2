"""R2-518.  DID ANYTHING IN `world/items/` REACH A FRAME?  One frame, cheaply.

    /opt/blender-5.2.0-linux-x64/blender -b render/film16_breach.blend \
        --factory-startup -P render/world/assembly/r2/v125/prove_items_cheap.py -- \
        --frame 2978 --res 3840 --samples 4 --out work/r2500/items_cheap.json

WHY THIS REPLACES `prove_items_in_frame.py`
-------------------------------------------
That version rendered 3 frames x 6 holdouts = 18 full renders with no
`persistent_data`, so it paid for a BVH over 42 M triangles every time. It ran
11 minutes on this box without finishing a single frame. The claim was also
stronger than the task: **task #121 asks whether anything built in
`world/items/` has EVER reached a frame, and one frame with one item in it
settles that.**

So: ONE frame, `persistent_data` on, and the per-render seconds are printed so
the cost driver is MEASURED rather than assumed -- if the load dominates and the
renders are cheap, that is worth knowing before anyone designs the next one.

f2978 is chosen because it is the closing wide, where the placed families are
plainly in shot. Picking the frame where the answer is easiest is not cheating:
the question is whether items EVER reach a frame, so any single frame that
carries them answers it, and a frame where they are large makes the measurement
robust rather than marginal.

THE MEASUREMENT
---------------
`film_transparent` makes alpha mean "some geometry covers this pixel".

    A_all       everything visible
    A_minus_F   family F set as a HOLDOUT -- it punches alpha to 0 wherever it
                is the FRONTMOST surface, and contributes no shading of its own
    F_visible = A_all - A_minus_F

A holdout cannot subtract pixels F does not own, so this cannot over-report, and
anything hidden behind the world never enters the difference -- which is exactly
the distinction between "in the scene" and "in the picture" that #121 turns on.

DOF and motion blur are left exactly as the film has them. This is a statement
about the delivered image, not about a cleaned-up version of it.

THE NEGATIVE CONTROL IS NOT OPTIONAL AND IS NOT WEAKENED. `ZZZ_NOTHING_` matches
no object; holding it out must change nothing, so its count must be 0. Without
it, "F_visible = 0" and "the difference operation is broken" are the same
reading. It costs one render.

Blender 5.2 exits 0 on an uncaught script exception. Judge on STAGE RESULT.
"""
import argparse
import json
import os
import sys
import time

import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--frame", type=int, default=2978)
ap.add_argument("--res", type=int, default=3840)
ap.add_argument("--samples", type=int, default=4)
ap.add_argument("--out", default="/home/zany/f1-round2/work/r2500/items_cheap.json")
a = ap.parse_args(argv)

FAMILIES = [("CFP_", "catch_fence_post"), ("CRF_", "crew_figure"),
            ("TS_", "timing_stand"), ("SPECX_", "spectator_crowd_world"),
            ("DRV_", "driver"), ("ZZZ_NOTHING_", "NEGATIVE CONTROL")]

sc = bpy.context.scene
t_load = time.time()
sc.render.engine = "CYCLES"
sc.cycles.samples = a.samples
sc.cycles.use_denoising = False
sc.cycles.use_adaptive_sampling = False
try:
    sc.cycles.device = "CPU"
except Exception:
    pass
# THE ONE-LINE CHANGE the last version was missing. With this off, every render
# rebuilds acceleration structures over the whole 42 M-triangle scene.
sc.render.use_persistent_data = True
sc.render.resolution_x = a.res
sc.render.resolution_y = int(round(a.res * 2160.0 / 3840.0))
sc.render.resolution_percentage = 100
sc.render.film_transparent = True
sc.render.image_settings.file_format = "PNG"
sc.render.image_settings.color_mode = "RGBA"
sc.frame_set(a.frame)

TMP = ("/tmp/claude-0/-home-zany-opus5-car-render/"
       "262f2abe-1dfb-4a32-9544-52393037f67a/scratchpad/itemscheap.png")
os.makedirs(os.path.dirname(TMP), exist_ok=True)

BY = {p: [o for o in bpy.data.objects if o.name.startswith(p)]
      for p, _ in FAMILIES}
print(">> frame %d  %dx%d  %d samples  persistent_data=%s"
      % (a.frame, sc.render.resolution_x, sc.render.resolution_y, a.samples,
         sc.render.use_persistent_data))
print(">> objects per family: %s" % {p: len(v) for p, v in BY.items()})

_total = [0]


def alpha():
    t0 = time.time()
    sc.render.filepath = TMP
    bpy.ops.render.render(write_still=True)
    for im in list(bpy.data.images):
        if im.filepath and os.path.basename(im.filepath) == "itemscheap.png":
            bpy.data.images.remove(im)
    im = bpy.data.images.load(TMP)
    px = list(im.pixels)
    n = len(px) // 4
    c = sum(1 for i in range(n) if px[i * 4 + 3] > 0.5)
    _total[0] = n                       # MEASURED off the written image (R2-517)
    bpy.data.images.remove(im)
    return c, time.time() - t0


for o in bpy.data.objects:
    o.is_holdout = False
a_all, dt0 = alpha()
print(">> A_all %d px of %d  (%.1f s -- this render paid the BVH build)"
      % (a_all, _total[0], dt0))

rows, secs, ok_any, ctl_clean = {}, {"A_all": round(dt0, 1)}, False, True
for pref, label in FAMILIES:
    objs = BY[pref]
    for o in objs:
        o.is_holdout = True
    a_less, dt = alpha()
    for o in objs:
        o.is_holdout = False
    c = a_all - a_less
    rows[label] = c
    secs[label] = round(dt, 1)
    frac = 100.0 * c / max(_total[0], 1)
    print(">>   %-24s %-6d objects -> %8d px visible (%.4f %% of frame)  %.1f s"
          % (label, len(objs), c, frac, dt))
    if label == "NEGATIVE CONTROL":
        ctl_clean = (c == 0)
    elif c > 0:
        ok_any = True

rep = {"frame": a.frame, "blend": bpy.data.filepath, "counts": rows,
       "a_all": a_all, "total_px_measured": _total[0],
       "seconds_per_render": secs, "samples": a.samples,
       "res": [sc.render.resolution_x, sc.render.resolution_y],
       "persistent_data": bool(sc.render.use_persistent_data),
       "negative_control_clean": ctl_clean, "any_item_on_screen": ok_any,
       "objects_per_family": {p: len(v) for p, v in BY.items()}}
os.makedirs(os.path.dirname(a.out), exist_ok=True)
with open(a.out, "w") as fh:
    json.dump(rep, fh, indent=1)

print(">> per-render seconds: %s" % secs)
if not ctl_clean:
    print(">> STAGE RESULT: ITEMS_INSTRUMENT_BROKEN -- holding out a family "
          "with no objects changed %d pixels" % rows["NEGATIVE CONTROL"])
elif ok_any:
    print(">> STAGE RESULT: ITEMS_REACHED_A_FRAME")
else:
    print(">> STAGE RESULT: ITEMS_NEVER_ON_SCREEN")
