#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""subpixel_stability.py — how much does a frame change when the lens moves by
less than one pixel?

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P tools/subpixel_stability.py -- a.png b.png c.png \
        --regions near=0,1400,3840,760 far=0,0,3840,600 \
        --out render/items/<id>/subpixel.json

WHY THIS EXISTS
---------------
`docs/item_manifest.json` asks, for `asphalt_wearing_course`:

    "it must be re-checked for TEMPORAL flicker in motion, not just in a still."

A still cannot answer that and neither can a claim.  What a set of stills CAN
measure is the ingredient flicker is made of: sensitivity to sub-pixel lens
motion.  Detail finer than the ray footprint changes a lot between two frames a
third of a pixel apart; detail the footprint resolves changes smoothly.  So
render the same shot at 0, 1/3 and 2/3 of a pixel of lateral lens travel and
measure the RMS difference, per region, normalised by each region's own RMS
contrast.

WHAT IT DOES AND DOES NOT PROVE
-------------------------------
It DOES bound how aliased the surface is: a normalised sensitivity of 1.0 means
a third of a pixel of camera motion changes a pixel by as much as the texture
varies at all, i.e. pure noise.  Under about 0.35 the surface is resolved.

It DOES NOT prove temporal stability in the delivered shot, because the delivered
shot has motion blur, a denoiser with temporal input, and (at the hairpin) a
STATIC camera.  Reporting it as if it did would be the R2-017 failure.  Read it
as: "the geometry is/is not aliased at the delivery pixel scale."
"""

import argparse
import json
import os
import sys

import bpy
import numpy as np


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser()
    p.add_argument("images", nargs="+")
    p.add_argument("--regions", nargs="*", default=[],
                   help="name=x,y,w,h  (top-left origin, pixels)")
    p.add_argument("--out", required=True)
    return p.parse_args(argv)


def load(path):
    img = bpy.data.images.load(path)
    W, H = img.size
    buf = np.empty(W * H * 4, np.float32)
    img.pixels.foreach_get(buf)
    a = buf.reshape(H, W, 4)[::-1, :, :3]        # top-down, RGB
    bpy.data.images.remove(img)
    return a.astype(np.float64)


def main():
    a = parse_args()
    ims = [load(p) for p in a.images]
    if len({i.shape for i in ims}) != 1:
        raise SystemExit("REFUSING: the frames are not the same size, so a "
                         "per-pixel difference would be comparing different "
                         "pixels. %s" % [i.shape for i in ims])
    H, W, _ = ims[0].shape
    regions = {"whole_frame": (0, 0, W, H)}
    for spec in a.regions:
        name, rest = spec.split("=", 1)
        x, y, w, h = (int(v) for v in rest.split(","))
        regions[name] = (x, y, min(w, W - x), min(h, H - y))

    rep = {"frames": [os.path.basename(p) for p in a.images],
           "resolution": [W, H], "regions": {}}
    for name, (x, y, w, h) in regions.items():
        subs = [im[y:y + h, x:x + w] for im in ims]
        lum = [s.mean(axis=2) for s in subs]
        # the region's own spatial contrast: what "a lot" means here
        contrast = float(np.sqrt(np.mean((lum[0] - lum[0].mean()) ** 2)))
        diffs = []
        for i in range(1, len(lum)):
            d = float(np.sqrt(np.mean((lum[i] - lum[0]) ** 2)))
            diffs.append(d)
        rep["regions"][name] = {
            "box_xywh": [x, y, w, h],
            "mean": round(float(lum[0].mean()), 5),
            "spatial_rms_contrast": round(contrast, 5),
            "rms_diff_per_frame": [round(d, 6) for d in diffs],
            "normalised_sensitivity": [round(d / max(contrast, 1e-9), 4)
                                       for d in diffs],
        }
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(rep, open(a.out, "w"), indent=1)
    print(">> sub-pixel stability, %d frames at %dx%d" % (len(ims), W, H))
    for name, r in rep["regions"].items():
        print("   %-14s contrast %.4f   rms diff %s   normalised %s"
              % (name, r["spatial_rms_contrast"],
                 r["rms_diff_per_frame"], r["normalised_sensitivity"]))
    print(">> wrote", a.out)
    print(">> NOTE: this bounds ALIASING at the delivery pixel scale. It does "
          "NOT\n>>       prove temporal stability in the delivered shot -- that "
          "needs\n>>       motion blur and the real camera track.")



# Imported by path, not by package: this runs inside Blender's interpreter
# with whatever cwd the caller happened to have.
import os as _os_ge, sys as _sys_ge
if _os_ge.path.dirname(_os_ge.path.abspath(__file__)) not in _sys_ge.path:
    _sys_ge.path.insert(0, _os_ge.path.dirname(_os_ge.path.abspath(__file__)))
import gate_exit                                                 # noqa: E402


if __name__ == "__main__":
    # Blender 5.2 returns 0 for a script that raised: `blender -b -P x.py`
    # prints the traceback and exits 0, MEASURED on this box. A gate that
    # crashed was indistinguishable from one that passed. guard() makes an
    # uncaught exception a status 2 and passes any real verdict through
    # unchanged. One shared helper, not N copies -- see tools/gate_exit.py.
    gate_exit.guard(main, tool="subpixel_stability")
