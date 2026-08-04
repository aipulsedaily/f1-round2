"""R2-511.  How much of the strapline does MERIDIAN actually EAT, in pixels?

    /opt/blender-5.2.0-linux-x64/blender -b world/camera_rig.blend --factory-startup \
        -P tools/r2511_sign_occlusion.py -- --frames 1,9,25 --res 3840 \
        [--fix 0.5] [--json work/r2500/sign_occlusion.json]

WHY THE AABB MEASUREMENT THAT FOUND THIS IS NOT GOOD ENOUGH
-----------------------------------------------------------
R2-509 found the collision with screen-space axis-aligned bounding boxes, and an
AABB can overlap when the glyphs do not.  A wide text run seen with its baseline
tilted on screen has an AABB much taller than the run, and two stacked runs can
then "overlap" as boxes while every glyph is clear.  The pit board's 7.2 % is
exactly the shape of that artefact -- 46.1 x 2.8 px on runs whose world gap
(41.7 mm) is seven times their depth (6 mm), where the depth mechanism cannot be
the cause.

So this measures OCCLUSION, per pixel, and does not use boxes at all:

    S      = strapline pixels with the strapline rendered ALONE
    S_seen = strapline pixels with the wordmark also present, from IndexOB
    eaten  = (S - S_seen) / S

`eaten` is the fraction of the strapline the wordmark's body covers.  It is
zero when the two do not touch however close their boxes are, and it cannot be
non-zero unless the wordmark is genuinely in front of strapline pixels.

CONTROLS, both in the same run:
  * `S` itself is reported.  If the strapline is off screen, S = 0 and the run
    says NO_SUBJECT rather than reporting a clean 0 % that means nothing.
  * a run against a frame with the wordmark HIDDEN must give eaten = 0.000 --
    printed as SELF_NULL.  A measurement that reads the same with and without
    the thing being measured is the failure mode this project keeps hitting.

THE FIX, AND WHY IT IS A LOCAL-Z SCALE AND NOT A REBUILD
--------------------------------------------------------
`WallSign_Word` is built by `/home/zany/opus5-car-render/build/s07_props.py`,
which is READ-ONLY (project law 1), so the glyph run cannot be re-extruded at
source.  Its depth is `2*extrude(0.022) + 2*bevel(0.004) = 52.0 mm` and it is
stacked 46.3 mm above the strapline: THE DEPTH EXCEEDS THE GAP, which is the
whole defect.

Blender curve extrusion runs along the curve's local Z, so the built mesh's
depth axis is its own local Z and scaling that axis alone changes the letter
DEPTH and nothing else -- glyph shapes, cap height, letter-spacing, the fitted
2.60 m width and the mounting datum at the object origin are all untouched.
`--fix k` sets that scale.  k = 0.5 gives 26.0 mm, which is 56 % of the gap.

This is the `tools/add_dais_ramp.py` shape: open the blend that exists, assert
the datum rather than trusting it, change one thing, save somewhere new.

Blender 5.2 exits 0 on an uncaught script exception.  Judge on STAGE RESULT.
"""
import argparse
import json
import os
import sys

import bpy

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--frames", default="1,9,25")
ap.add_argument("--res", type=int, default=3840)
ap.add_argument("--samples", type=int, default=4)
ap.add_argument("--fix", type=float, default=None,
                help="scale WallSign_Word's local Z (depth) by this and "
                     "re-measure. 1.0 = unchanged.")
ap.add_argument("--json", default=None)
ap.add_argument("--save", default=None)
a = ap.parse_args(argv)

WORD, STRAP = "WallSign_Word", "WallSign_Strap"
sc = bpy.context.scene
word, strap = bpy.data.objects.get(WORD), bpy.data.objects.get(STRAP)
if word is None or strap is None:
    print(">> STAGE RESULT: SIGN_OCCL_FAIL -- %s / %s not in this blend"
          % (WORD, STRAP))
    raise SystemExit(0)


def depth_m(ob):
    """Local-Z extent in metres -- the extrusion axis, in the object's frame."""
    zs = [v.co.z for v in ob.data.vertices]
    return (max(zs) - min(zs)) * abs(ob.scale.z)


def gap_m():
    """World vertical gap between the two runs' bounding boxes."""
    from mathutils import Vector

    def zr(o):
        p = [(o.matrix_world @ Vector(c)).z for c in o.bound_box]
        return min(p), max(p)
    wl, wh = zr(word)
    sl, sh = zr(strap)
    return wl - sh


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

# NO COMPOSITOR.  Blender 5.2 moved `scene.node_tree`, and an IndexOB pass read
# through a Viewer node is not reachable in background mode anyway.  Occlusion
# is measured with ALPHA and a HOLDOUT instead, which needs neither:
#
#   film_transparent  -> background alpha 0, so alpha>0 IS "this object covers
#                        this pixel"
#   only the strapline is visible          -> S       = its full silhouette
#   + the wordmark as a HOLDOUT            -> S_seen  = the part of that
#                                             silhouette the wordmark does not
#                                             punch out
#
# A holdout writes alpha 0 wherever the object is in front, which is exactly the
# occlusion question and nothing else.  `is_holdout` means the wordmark
# contributes no shading of its own, so the difference cannot be a lighting
# change masquerading as coverage.
sc.render.film_transparent = True
sc.render.image_settings.file_format = "PNG"
sc.render.image_settings.color_mode = "RGBA"
sc.render.image_settings.color_depth = "8"

_orig_hide = {o.name: o.hide_render for o in bpy.data.objects}
for o in bpy.data.objects:
    o.hide_render = True
strap.hide_render = False
word.is_holdout = True

TMP = "/tmp/claude-0/-home-zany-opus5-car-render/262f2abe-1dfb-4a32-9544-52393037f67a/scratchpad/r2511.png"
os.makedirs(os.path.dirname(TMP), exist_ok=True)


def _alpha_count():
    sc.render.filepath = TMP
    bpy.ops.render.render(write_still=True)
    for im in list(bpy.data.images):
        if im.filepath and os.path.basename(im.filepath) == "r2511.png":
            bpy.data.images.remove(im)
    im = bpy.data.images.load(TMP)
    px = list(im.pixels)
    n = len(px) // 4
    c = sum(1 for i in range(n) if px[i * 4 + 3] > 0.5)
    bpy.data.images.remove(im)
    return c


def measure(frames):
    rows = {}
    for f in frames:
        sc.frame_set(f)
        word.hide_render = True                     # strapline ALONE
        s_alone = _alpha_count()
        word.hide_render = False                    # + the wordmark as holdout
        s_seen = _alpha_count()
        eaten = ((s_alone - s_seen) / float(s_alone)) if s_alone else None
        rows[f] = {"strap_alone_px": s_alone, "strap_seen_px": s_seen,
                   "eaten_frac": eaten}
        if not s_alone:
            print("   f%-5d NO_SUBJECT -- the strapline renders 0 px; this "
                  "frame says nothing" % f)
        else:
            print("   f%-5d strapline %6d px alone -> %6d px seen   "
                  "EATEN %6.2f %%" % (f, s_alone, s_seen, eaten * 100.0))
    return rows


frames = [int(x) for x in a.frames.split(",") if x.strip()]
print(">> %s depth %.4f m (%.1f mm), gap to strapline %.4f m (%.1f mm)"
      % (WORD, depth_m(word), depth_m(word) * 1000, gap_m(), gap_m() * 1000))
print(">> BEFORE")
before = measure(frames)

print(">> SELF-NULL: wordmark hidden in BOTH arms, eaten must be 0.000")
f0 = frames[0]
sc.frame_set(f0)
word.hide_render = True
s1 = _alpha_count()
s2 = _alpha_count()
word.hide_render = False
null_ok = (s1 == s2)
print("   f%-5d %d px vs %d px  -> %s" % (f0, s1, s2, "SELF_NULL_OK"
                                          if null_ok else "SELF_NULL_FAIL"))

after = None
if a.fix is not None:
    d0 = depth_m(word)
    word.scale.z = word.scale.z * a.fix
    bpy.context.view_layer.update()
    d1 = depth_m(word)
    print(">> FIX: WallSign_Word local-Z scaled by %.3f -- depth %.1f mm -> "
          "%.1f mm, against a %.1f mm gap"
          % (a.fix, d0 * 1000, d1 * 1000, gap_m() * 1000))
    if d1 >= gap_m():
        print(">>   WARNING: the depth is STILL >= the gap; this scale does "
              "not clear the mechanism")
    print(">> AFTER")
    after = measure(frames)
    if a.save:
        for o in bpy.data.objects:
            o.hide_render = _orig_hide.get(o.name, False)
        word.is_holdout = False
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.save),
                                    compress=False)
        print(">> saved %s" % a.save)

rep = {"word_depth_m": depth_m(word), "gap_m": gap_m(), "before": before,
       "after": after, "fix": a.fix, "self_null_ok": null_ok,
       "res": [sc.render.resolution_x, sc.render.resolution_y]}
if a.json:
    os.makedirs(os.path.dirname(a.json), exist_ok=True)
    with open(a.json, "w") as fh:
        json.dump(rep, fh, indent=1)

live = [r["eaten_frac"] for r in before.values() if r["eaten_frac"] is not None]
if not null_ok:
    print(">> STAGE RESULT: SIGN_OCCL_INSTRUMENT_BROKEN")
elif not live:
    print(">> STAGE RESULT: SIGN_OCCL_NO_SUBJECT -- no frame showed the "
          "strapline; this run proves nothing either way")
elif after is not None:
    aft = [r["eaten_frac"] for r in after.values() if r["eaten_frac"] is not None]
    print(">> worst eaten  BEFORE %.2f %%   AFTER %.2f %%"
          % (max(live) * 100, max(aft) * 100))
    print(">> STAGE RESULT: %s"
          % ("SIGN_OCCL_FIXED" if max(aft) < 0.01 else "SIGN_OCCL_STILL_EATEN"))
else:
    print(">> STAGE RESULT: %s"
          % ("SIGN_OCCL_CONFIRMED" if max(live) > 0.01 else "SIGN_OCCL_ABSENT"))
