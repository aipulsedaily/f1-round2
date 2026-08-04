#!/usr/bin/env python3
"""Which film14 frame best sees a set of world points? Pure numpy, no Blender.

Camera model: 3840x2160, sensor 36 mm, lens per key. Blender camera looks -Z,
up +Y, in the camera's own frame; the path stores a quaternion (w,x,y,z).
"""
import json, sys, math
import numpy as np

ROOT = "/home/zany/f1-round2"
RES_X, RES_Y, SENSOR = 3840, 2160, 36.0

def quat_to_mat(q):
    w, x, y, z = q
    return np.array([
        [1-2*(y*y+z*z), 2*(x*y-z*w),   2*(x*z+y*w)],
        [2*(x*y+z*w),   1-2*(x*x+z*z), 2*(y*z-x*w)],
        [2*(x*z-y*w),   2*(y*z+x*w),   1-2*(x*x+y*y)]])

def load_path(p):
    d = json.load(open(p))
    return d["path"]

def score(pts, keys, margin=0.90):
    """-> list of (frame, n_in_frustum, nearest_m, mean_px_height_for_2m_object)"""
    out = []
    for k in keys:
        c = np.array(k["p"], float)
        R = quat_to_mat(k["q"])            # camera-to-world
        lens = float(k["lens"])
        d = pts - c
        cam = d @ R                        # world->camera (R orthonormal)
        z = -cam[:, 2]                     # depth in front of camera
        ok = z > 0.1
        if not ok.any():
            out.append((k["f"], 0, 1e9, 0.0)); continue
        fx = lens * RES_X / SENSOR         # px per (m/m)
        u = cam[ok, 0] / z[ok] * fx + RES_X / 2.0
        v = cam[ok, 1] / z[ok] * fx + RES_Y / 2.0
        inside = (u > 0) & (u < RES_X) & (v > 0) & (v < RES_Y)
        n = int(inside.sum())
        near = float(z[ok][inside].min()) if n else 1e9
        px2m = 2.0 * lens * RES_X / (SENSOR * near) if n else 0.0
        out.append((k["f"], n, near, px2m))
    return out

if __name__ == "__main__":
    ptsfile, pathfile = sys.argv[1], sys.argv[2]
    pts = np.array(json.load(open(ptsfile)), float)
    keys = load_path(pathfile)
    rows = score(pts, keys)
    rows.sort(key=lambda r: (-r[1], r[2]))
    print("%-8s %6s %10s %10s" % ("frame", "n_in", "nearest_m", "px_for_2m"))
    for r in rows[:25]:
        print("%-8d %6d %10.2f %10.1f" % r)
