#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
r2366_crop_owner.py — WHICH OBJECT AND WHICH MATERIAL IS ACTUALLY IN THE CROP.

The brief names a crop of the delivered frame and calls it "the paddock apron".
There are FIVE paving objects in three material families with three different
hash-cell sizes, and picking the wrong one means fixing a surface the crop does
not contain. `screen_presence.json` cannot answer it — it is stamped against
assembly6 and the old camera.

So this RAYCASTS the delivered frame's own pixels. It builds `build_architecture`
(117 s), puts the ONER camera at the frame the brief cites with that frame's own
pose and lens out of `world/camera_rig_path.json`, and fires one ray per sampled
pixel of the crop, reporting the object and material each ray lands on with the
hit distance and the surface scale in mm per pixel.

IT SEES ONLY ARCHITECTURE. Terrain, barriers, dressing and the round-1 showroom
are not built here, so a ray that would really have hit a barrier is reported as
whatever architecture lies behind it. That makes this an attribution of the
PAVING, which is what it is for, and the ranking is confirmed by the render.

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P tools/r2366_crop_owner.py -- --frame 2978 --crop 900 780 900 420

Blender 5.2 exits 0 on an uncaught script exception; judge on `STAGE RESULT`.
"""
import argparse
import collections
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "world"))

import bpy                                                   # noqa: E402
from mathutils import Quaternion, Vector                     # noqa: E402

W, H = 3840, 2160
SENSOR = 36.0


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--frame", type=int, default=2978)
    ap.add_argument("--crop", type=int, nargs=4, default=[900, 780, 900, 420],
                    metavar=("X", "Y", "W", "H"))
    ap.add_argument("--step", type=int, default=6)
    ap.add_argument("--json", default=None)
    ap.add_argument("--load", default=None,
                    help="a previously built architecture .blend, to skip the "
                         "117 s rebuild while iterating on the probe")
    a = ap.parse_args(argv)

    if a.load:
        bpy.ops.wm.open_mainfile(filepath=a.load)
        print("[owner] loaded %s" % a.load)
    else:
        import build_architecture as BA
        BA.build(verify=False)
    sc = bpy.context.scene
    print("[owner] architecture built: %d objects" % len(bpy.data.objects))

    path = json.load(open(os.path.join(ROOT, "world",
                                       "camera_rig_path.json")))["path"]
    e = path[a.frame - 1]
    assert e["f"] == a.frame, "camera path is not 1-indexed by frame"
    p = Vector(e["p"])
    q = Quaternion(e["q"])
    R = q.to_matrix()
    fpx = (float(e["lens"]) / SENSOR) * W
    print("[owner] frame %d  p=%s  lens=%.4f  f=%.1f px"
          % (a.frame, [round(x, 2) for x in e["p"]], e["lens"], fpx))

    dg = bpy.context.evaluated_depsgraph_get()
    x0, y0, cw, ch = a.crop
    hits = collections.Counter()
    objxy = collections.defaultdict(list)
    mats = collections.Counter()
    dist = collections.defaultdict(list)
    n_ray = n_hit = 0
    for py in range(y0, y0 + ch, a.step):
        for px in range(x0, x0 + cw, a.step):
            # pixel -> camera-space ray (Blender: -Z forward, +Y up)
            cx = (px + 0.5 - W * 0.5) / fpx
            cy = -(py + 0.5 - H * 0.5) / fpx
            d = R @ Vector((cx, cy, -1.0))
            d.normalize()
            n_ray += 1
            ok, loc, nor, idx, ob, mw = sc.ray_cast(dg, p, d, distance=5000.0)
            if not ok:
                continue
            n_hit += 1
            hits[ob.name] += 1
            dist[ob.name].append((loc - p).length)
            # the face index belongs to the EVALUATED object, so resolve the
            # material against that; -1 means the original data is gone, and an
            # unresolvable slot is reported as "?" rather than guessed at.
            mn = "?"
            try:
                obe = ob.evaluated_get(dg)
                if obe.type == 'MESH' and idx >= 0:
                    mi = obe.data.polygons[idx].material_index
                    if 0 <= mi < len(obe.material_slots):
                        mn = obe.material_slots[mi].material.name
            except Exception:                                # noqa: BLE001
                mn = "?"
            mats[(ob.name, mn)] += 1
            # WHERE, IN THE MATERIAL'S OWN COORDINATES, THE FRAME ACTUALLY
            # SAMPLES IT. These materials are driven from Object coordinates and
            # several of their features are position-dependent — A_ConcSlab's
            # rubber pick-up is a clamped MapRange on object Y that is FULLY ON
            # below y = 11. Probing such a material at its origin measures a
            # region the film never shows. These medians are what
            # `r2366_paint_vs_geometry.py` samples instead.
            try:
                lo = ob.matrix_world.inverted() @ loc
                objxy[mn].append((lo.x, lo.y))
            except Exception:                            # noqa: BLE001
                pass

    print("\n[owner] crop %dx%d+%d+%d, step %d -> %d rays, %d hits (%.1f %%)"
          % (cw, ch, x0, y0, a.step, n_ray, n_hit, 100.0 * n_hit / max(n_ray, 1)))
    print("\n  %-34s %7s %7s %10s %9s" % ("object", "rays", "share", "d_med_m",
                                          "mm/px"))
    res = []
    for name, n in hits.most_common(12):
        ds = sorted(dist[name])
        dm = ds[len(ds) // 2]
        # mm of surface per delivered pixel, at normal incidence; the real
        # incidence makes it larger, so this is a LOWER bound on coarseness
        mmpx = 1000.0 * dm / fpx
        share = 100.0 * n / max(n_hit, 1)
        print("  %-34s %7d %6.1f%% %10.1f %9.1f" % (name, n, share, dm, mmpx))
        res.append(dict(object=name, rays=n, share_pct=share, d_med_m=dm,
                        mm_px_min=mmpx))
    print("\n  %-34s %-20s %7s %7s" % ("object", "material", "rays", "share"))
    for (on, mn), n in mats.most_common(12):
        print("  %-34s %-20s %7d %6.1f%%"
              % (on, mn, n, 100.0 * n / max(n_hit, 1)))

    print("\n  median OBJECT-space sample point per material (the probe point)")
    print("  %-22s %9s %10s %10s" % ("material", "rays", "obj_x", "obj_y"))
    probes = {}
    for mn, pts in sorted(objxy.items(), key=lambda kv: -len(kv[1])):
        if len(pts) < 50:
            continue
        xs = sorted(p[0] for p in pts)
        ys = sorted(p[1] for p in pts)
        mx, my = xs[len(xs) // 2], ys[len(ys) // 2]
        probes[mn] = [mx, my]
        print("  %-22s %9d %10.2f %10.2f" % (mn, len(pts), mx, my))

    if a.json:
        os.makedirs(os.path.dirname(a.json) or ".", exist_ok=True)
        json.dump(dict(frame=a.frame, crop=a.crop, rays=n_ray, hits=n_hit,
                       probe_object_xy=probes,
                       focal_px=fpx, objects=res,
                       materials=[dict(object=k[0], material=k[1], rays=v)
                                  for k, v in mats.most_common(20)]),
                  open(a.json, "w"), indent=1)
        print("\n[owner] wrote %s" % a.json)
    print("STAGE RESULT: r2366_crop_owner PASS (%d hits of %d rays)"
          % (n_hit, n_ray))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
        print("STAGE RESULT: r2366_crop_owner FAIL (uncaught exception)")
        sys.exit(1)
