#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
r2366_paving_window.py — find a rectangle of the delivered frame that is PAVING
AND ALMOST NOTHING ELSE, by raycasting rather than by eye.

WHY. The brief's crop is 59.8 % paving; the other 40 % is barriers, fences,
containers, a service road and the pit wall, and those carry far more contrast
than a concrete apron does. Measured over the whole crop, the paving's own
statistics are swamped: the first A/B run reported a spectral `peakiness` of
39,966 in BOTH arms — that number is the diagonal barrier line, not the tiling,
and it would have read the same whether the defect was present or absent.

A METRIC THAT READS THE SAME WHETHER THE THING IS PRESENT OR ABSENT IS NOT A
MEASUREMENT. So the measurement window is derived from the picture: one ray per
sampled pixel, resolved against a real `build_architecture` build at the film's
own camera, and then the largest rectangle whose paving purity clears a
threshold.

ONE WINDOW, COMPUTED ONCE, USED BY EVERY ARM. It is computed from the BEFORE
build and reused unchanged for AFTER and NULL, so no arm can move the goalposts
by changing which pixels it is judged on — the same discipline R2-060's
five-arm experiment needed.

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P tools/r2366_paving_window.py -- --frame 2978 \
        --region 700 700 1400 700 --step 2 --load work/r2366/arch_base.blend

Blender 5.2 exits 0 on an uncaught script exception; judge on `STAGE RESULT`.
"""
import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "world"))

import bpy                                                   # noqa: E402
import numpy as np                                           # noqa: E402
from mathutils import Quaternion, Vector                     # noqa: E402

W, H = 3840, 2160
SENSOR = 36.0
PAVING = {"A_ConcSlab", "A_ConcApron", "A_ForecourtSlab"}


def largest_pure_rect(mask, purity, min_w, min_h):
    """Largest-area axis-aligned rectangle whose mean(mask) >= `purity`.

    Brute force over a summed-area table. The grid is the raycast grid, not the
    frame, so this is thousands of cells rather than millions of pixels.
    """
    S = np.zeros((mask.shape[0] + 1, mask.shape[1] + 1), dtype=np.float64)
    S[1:, 1:] = np.cumsum(np.cumsum(mask.astype(np.float64), 0), 1)

    def mean(y0, x0, y1, x1):
        n = (y1 - y0) * (x1 - x0)
        return (S[y1, x1] - S[y0, x1] - S[y1, x0] + S[y0, x0]) / n

    best = None
    hh, ww = mask.shape
    for y0 in range(hh):
        for y1 in range(y0 + min_h, hh + 1):
            for x0 in range(ww):
                # grow x1 while purity holds; once it fails it can only fail
                # further for this (y0, y1, x0), so stop.
                x1 = x0 + min_w
                if x1 > ww:
                    break
                last = None
                while x1 <= ww and mean(y0, x0, y1, x1) >= purity:
                    last = x1
                    x1 += 1
                if last is not None:
                    area = (y1 - y0) * (last - x0)
                    if best is None or area > best[0]:
                        best = (area, y0, x0, y1, last)
    return best


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--frame", type=int, default=2978)
    ap.add_argument("--region", type=int, nargs=4,
                    default=[700, 700, 1400, 700], metavar=("X", "Y", "W", "H"))
    ap.add_argument("--step", type=int, default=4)
    ap.add_argument("--purity", type=float, default=0.97)
    ap.add_argument("--invert", action="store_true",
                    help="find a window of everything EXCEPT paving — the "
                         "negative control. A region the change cannot reach, "
                         "carrying real contrast rather than empty sky: a "
                         "control that is identically black proves only that "
                         "black does not move.")
    ap.add_argument("--load", default=None)
    ap.add_argument("--json", default=None)
    a = ap.parse_args(argv)

    if a.load:
        bpy.ops.wm.open_mainfile(filepath=a.load)
    else:
        import build_architecture as BA
        BA.build(verify=False)
    sc = bpy.context.scene

    path = json.load(open(os.path.join(ROOT, "world",
                                       "camera_rig_path.json")))["path"]
    e = path[a.frame - 1]
    assert e["f"] == a.frame
    p = Vector(e["p"])
    R = Quaternion(e["q"]).to_matrix()
    fpx = (float(e["lens"]) / SENSOR) * W
    dg = bpy.context.evaluated_depsgraph_get()

    x0, y0, rw, rh = a.region
    xs = list(range(x0, x0 + rw, a.step))
    ys = list(range(y0, y0 + rh, a.step))
    mask = np.zeros((len(ys), len(xs)), dtype=bool)
    for iy, py in enumerate(ys):
        for ix, px in enumerate(xs):
            cx = (px + 0.5 - W * 0.5) / fpx
            cy = -(py + 0.5 - H * 0.5) / fpx
            d = R @ Vector((cx, cy, -1.0))
            d.normalize()
            ok, loc, nor, idx, ob, mw = sc.ray_cast(dg, p, d, distance=5000.0)
            if not ok:
                continue
            try:
                obe = ob.evaluated_get(dg)
                if obe.type == 'MESH' and idx >= 0:
                    mi = obe.data.polygons[idx].material_index
                    if 0 <= mi < len(obe.material_slots):
                        mask[iy, ix] = \
                            obe.material_slots[mi].material.name in PAVING
            except Exception:                                # noqa: BLE001
                pass

    if a.invert:
        mask = ~mask
    print("[win] region %dx%d+%d+%d, step %d -> %dx%d cells, %.1f %% wanted"
          % (rw, rh, x0, y0, a.step, mask.shape[1], mask.shape[0],
             100.0 * mask.mean()))

    best = largest_pure_rect(mask, a.purity, max(8, 120 // a.step),
                             max(8, 120 // a.step))
    if best is None:
        print("STAGE RESULT: r2366_paving_window FAIL (no rectangle reaches "
              "%.0f %% paving; the region is too mixed)" % (100 * a.purity))
        sys.exit(1)
    area, cy0, cx0, cy1, cx1 = best
    fx0 = x0 + cx0 * a.step
    fy0 = y0 + cy0 * a.step
    fw = (cx1 - cx0) * a.step
    fh = (cy1 - cy0) * a.step
    pur = mask[cy0:cy1, cx0:cx1].mean()
    print("[win] best window %dx%d+%d+%d  purity %.2f %%  (%d px)"
          % (fw, fh, fx0, fy0, 100 * pur, fw * fh))

    out = dict(frame=a.frame, region=a.region, step=a.step,
               purity_threshold=a.purity, window=[fx0, fy0, fw, fh],
               window_purity=float(pur),
               region_paving_fraction=float(mask.mean()))
    if a.json:
        os.makedirs(os.path.dirname(a.json) or ".", exist_ok=True)
        json.dump(out, open(a.json, "w"), indent=1)
        print("[win] wrote %s" % a.json)
    print("STAGE RESULT: r2366_paving_window PASS (%dx%d+%d+%d at %.1f %%)"
          % (fw, fh, fx0, fy0, 100 * pur))


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        import traceback
        traceback.print_exc()
        print("STAGE RESULT: r2366_paving_window FAIL (uncaught exception)")
        sys.exit(1)
