"""THE A/B: the same file, one collection toggled.

    blender -b render/debris/demo.blend -P sim/debris_ab.py -- \
        --frame 880 --tag f880 --crop 0.34,0.66,0.30,0.70

Renders the SAME scene twice at the same frame, same seed, same samples, same
crop, with `BREACH_Fines` excluded in the control.  Nothing else differs, and
nothing is rebuilt between the two, so a difference in the frames is the fines
and cannot be anything else -- which is more than can be said for an A/B that
re-runs a builder (R2-436's manufactured-control problem in miniature).

It also reports the CHANGED-PIXEL fraction between the pair, at three
thresholds, because "I can see it" and "it is measurable" are different claims
and this beat has burned the project on the difference before.
"""

import argparse
import json
import os
import sys

import bpy                                                        # noqa: E402
import numpy as np                                                # noqa: E402


def parse():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--frame", type=int, required=True)
    p.add_argument("--tag", required=True)
    p.add_argument("--dir", default="render/debris")
    p.add_argument("--crop", default="")
    p.add_argument("--res", type=int, default=3840)
    p.add_argument("--samples", type=int, default=192)
    p.add_argument("--collection", default="BREACH_Fines")
    return p.parse_args(argv)


def _set_crop(sc, crop):
    if not crop:
        sc.render.use_border = False
        return
    x0, x1, y0, y1 = [float(v) for v in crop.split(",")]
    sc.render.use_border = True
    sc.render.use_crop_to_border = True
    sc.render.border_min_x, sc.render.border_max_x = x0, x1
    sc.render.border_min_y, sc.render.border_max_y = y0, y1


def _lc(vl, name):
    """Find a LayerCollection by name, depth first."""
    stack = [vl.layer_collection]
    while stack:
        c = stack.pop()
        if c.collection.name == name:
            return c
        stack.extend(c.children)
    return None


def main():
    a = parse()
    sc = bpy.context.scene
    sc.cycles.samples = a.samples
    sc.cycles.device = "CPU"
    sc.render.resolution_x = a.res
    sc.render.resolution_y = int(round(a.res * 9 / 16))
    _set_crop(sc, a.crop)
    sc.frame_set(a.frame)
    os.makedirs(a.dir, exist_ok=True)

    lc = _lc(bpy.context.view_layer, a.collection)
    if lc is None:
        raise SystemExit("STAGE RESULT: debris_ab FAIL -- no collection %r"
                         % a.collection)
    n = len(lc.collection.all_objects)

    out = {}
    for label, exclude in (("A_fines", False), ("B_control", True)):
        lc.exclude = exclude
        path = os.path.join(a.dir, "%s_%s.png" % (a.tag, label))
        sc.render.filepath = path
        sc.render.image_settings.file_format = "PNG"
        sc.render.image_settings.color_depth = "16"
        bpy.ops.render.render(write_still=True)
        out[label] = path
        print(">> %s: %s objects in %s, wrote %s (%d bytes)"
              % (label, 0 if exclude else n, a.collection, path,
                 os.path.getsize(path) if os.path.exists(path) else 0))
    lc.exclude = False

    # ---- the measurement ---------------------------------------------------- #
    ia = bpy.data.images.load(out["A_fines"])
    ib = bpy.data.images.load(out["B_control"])
    A = np.array(ia.pixels[:], dtype=np.float32).reshape(-1, 4)[:, :3]
    B = np.array(ib.pixels[:], dtype=np.float32).reshape(-1, 4)[:, :3]
    npx = len(A)
    d = np.abs(A - B).max(axis=1)
    rep = dict(frame=a.frame, crop=a.crop, res=a.res, samples=a.samples,
               pixels=int(npx),
               fines_objects=int(n),
               changed_gt_1_255=float((d > 1 / 255.0).mean()),
               changed_gt_4_255=float((d > 4 / 255.0).mean()),
               changed_gt_16_255=float((d > 16 / 255.0).mean()),
               mean_abs_delta=float(d.mean()),
               max_abs_delta=float(d.max()),
               mean_A=float(A.mean()), mean_B=float(B.mean()))
    jp = os.path.join(a.dir, "%s_ab.json" % a.tag)
    with open(jp, "w") as fh:
        json.dump(rep, fh, indent=1)
    print(">> A/B %s" % json.dumps(rep, indent=1))
    ok = rep["changed_gt_1_255"] > 0.0
    print("STAGE RESULT: debris_ab %s" % ("PASS" if ok else
                                          "FAIL -- the fines changed NO pixel"))


if __name__ == "__main__":
    main()
