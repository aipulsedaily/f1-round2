#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
r2366_surface_visibility.py — WHICH FRAMES SEE THESE TWO SURFACES, AND AT WHAT
SCALE. Pure geometry off `world/camera_rig_path.json`; no Blender, no world.

THE POINT. A texture tuned only for the 595 m closing wide will fail the near
shots and vice versa, so the near frame has to be CHOSEN ON EVIDENCE rather than
picked because it is in beat 1. This walks all 2,978 frames and reports, per
frame, for each surface:

    cover_px    projected area in delivered 4K pixels (clipped to frame)
    d_med       median distance to the visible part, metres
    mm_px       millimetres of surface per delivered pixel, at d_med and at the
                surface's real incidence — the number that decides which relief
                wavelengths can be seen AT ALL

`mm_px` is the whole reason this exists. Relief finer than about 2 px is not
resolved; relief coarser than the surface's own extent is not texture, it is
form. Between those two the material has to work, and the band moves by 50x
along this take.

IT REPORTS OCCLUSION-BLIND COVERAGE and says so. Nothing here knows the roof is
behind a fence or the apron behind a barrier; `cover_px` is an UPPER BOUND, used
to rank candidate frames, not to claim a frame is good. The chosen frames are
then confirmed by rendering them.

    python3 tools/r2366_surface_visibility.py [--json OUT] [--top N]
"""
import argparse
import json
import math
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 3840, 2160
SENSOR = 36.0                      # mm, sensor_fit AUTO -> applies to the long axis

# The two subjects, as the rectangles their builders actually emit.
#   Ceiling: ~/opus5-car-render/build/s02_showroom.py build_shell(),
#            C.box(-ROOM_X-WALL_T .. +ROOM_X+WALL_T, ...), ROOM_X 15.0,
#            ROOM_Y 11.0, WALL_T 0.25, CEIL_Z 6.2, slab 0.30 thick.
#            Appended at IDENTITY by tools/build_film_scene.py, which asserts
#            the datum rather than trusting it.
#   Forecourt: world/build_architecture.py build_paving(), FORECOURT_WORLD
#            cx -0.5 cy 0.0 hx 26.5 hy 22.0 -> x -27..26, y -22..22 at Z_BAY.
#
# `exclude` REMOVES THE ONE OCCLUDER THAT DOMINATES. The forecourt rectangle
# runs UNDER the showroom, and beat 1's camera stands inside the building 2.4 m
# from paving it cannot see through the floor. Left uncorrected that single
# artefact ranks f496 first at 25.9 M px on an 8.3 M px frame — an occlusion-
# blind number believed as a measurement, which is this project's most repeated
# failure. Excluding the building footprint corrects for the floor and the
# shell. IT CORRECTS FOR NOTHING ELSE: barriers, fences and dressing still
# occlude, so the result stays an upper bound.
SURFACES = {
    "roof_top":   dict(x=(-15.25, 15.25), y=(-11.25, 11.25), z=6.500, up=+1),
    "roof_soffit": dict(x=(-15.25, 15.25), y=(-11.25, 11.25), z=6.200, up=-1),
    "forecourt":  dict(x=(-27.0, 26.0), y=(-22.0, 22.0), z=0.000, up=+1,
                       exclude=(-15.25, 15.25, -11.25, 11.25)),
}

# Beat boundaries, for reporting only. From docs/beat_sheet.json's own frames.
BEATS = [("beat1", 1, 754), ("seam", 755, 792), ("beat2", 793, 924),
         ("beat3", 925, 1056), ("beat4", 1057, 2100), ("beat5", 2101, 2714),
         ("beat6", 2715, 2978)]


def beat_of(f):
    for n, a, b in BEATS:
        if a <= f <= b:
            return n
    return "?"


def quat_to_mat(q):
    """Blender stores (w, x, y, z). Returns the camera-to-world rotation."""
    w, x, y, z = q
    n = math.sqrt(w * w + x * x + y * y + z * z)
    w, x, y, z = w / n, x / n, y / n, z / n
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def sample_grid(s, n=64):
    """A regular n x n of surface points, with the per-sample cell area.

    `n` is deliberately fine: the cell area is credited to the sample point, so
    a coarse grid at close range credits a whole 2 m cell to one in-frame point
    and over-counts wildly. 64 x 64 puts the forecourt cell at 0.84 x 0.70 m.
    """
    xs = np.linspace(s["x"][0], s["x"][1], n)
    ys = np.linspace(s["y"][0], s["y"][1], n)
    X, Y = np.meshgrid(xs, ys, indexing="ij")
    P = np.stack([X.ravel(), Y.ravel(), np.full(X.size, s["z"])], axis=1)
    cell = ((s["x"][1] - s["x"][0]) / (n - 1)) * ((s["y"][1] - s["y"][0]) / (n - 1))
    ex = s.get("exclude")
    if ex:
        keep = ~((P[:, 0] > ex[0]) & (P[:, 0] < ex[1])
                 & (P[:, 1] > ex[2]) & (P[:, 1] < ex[3]))
        P = P[keep]
    return P, cell


def frame_report(p, q, lens, surf):
    """Projected coverage and scale for one surface at one camera pose."""
    R = quat_to_mat(q)
    Rt = R.T
    fpx = (lens / SENSOR) * W                    # AUTO fit -> long axis is W
    P, cell = sample_grid(surf)
    V = P - np.asarray(p)                        # world vectors camera -> surface
    C = V @ Rt.T                                 # into camera space
    # Blender's camera looks down -Z, +Y up, +X right.
    depth = -C[:, 2]
    ok = depth > 1e-3
    if not ok.any():
        return None
    u = fpx * (C[:, 0] / np.where(ok, depth, 1.0)) + W * 0.5
    v = -fpx * (C[:, 1] / np.where(ok, depth, 1.0)) + H * 0.5
    inframe = ok & (u >= 0) & (u < W) & (v >= 0) & (v < H)
    if not inframe.any():
        return None
    d = np.linalg.norm(V, axis=1)
    # incidence: angle between the surface normal and the view ray
    nrm = np.array([0.0, 0.0, float(surf["up"])])
    ray = V / np.maximum(d, 1e-9)[:, None]
    cosi = np.abs(ray @ nrm)
    # facing check: the visible side is the one whose normal opposes the ray
    facing = (ray @ nrm) < 0.0
    vis = inframe & facing
    if not vis.any():
        return None
    dv = d[vis]
    ci = np.maximum(cosi[vis], 1e-6)
    # projected pixel area of each cell, and mm of surface per pixel ACROSS the
    # steepest direction (the foreshortened one), which is what limits detail
    px_cell = cell * ci * (fpx / dv) ** 2
    cover = float(px_cell.sum())
    dmed = float(np.median(dv))
    cimed = float(np.median(ci))
    # metres per pixel along the view-aligned (foreshortened) axis
    mm_px = 1000.0 * (dmed / fpx) / max(cimed, 1e-6)
    return dict(cover_px=cover, d_med=dmed, d_min=float(dv.min()),
                cos_inc=cimed, mm_px=mm_px, lens=float(lens))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=None)
    ap.add_argument("--top", type=int, default=6)
    ap.add_argument("--step", type=int, default=1)
    a = ap.parse_args()

    path = json.load(open(os.path.join(ROOT, "world",
                                       "camera_rig_path.json")))["path"]
    per = {k: [] for k in SURFACES}
    for e in path[::a.step]:
        for k, s in SURFACES.items():
            r = frame_report(e["p"], e["q"], e["lens"], s)
            if r:
                r["f"] = e["f"]
                r["beat"] = beat_of(e["f"])
                per[k].append(r)

    out = {}
    for k, rows in per.items():
        rows.sort(key=lambda r: -r["cover_px"])
        out[k] = rows
        print("=" * 78)
        print("%s — visible (occlusion-blind) on %d of %d sampled frames"
              % (k, len(rows), len(path[::a.step])))
        if not rows:
            continue
        print("  %-7s %-6s %10s %9s %9s %8s %8s"
              % ("frame", "beat", "cover_px", "d_med_m", "d_min_m", "mm/px", "lens"))
        for r in rows[:a.top]:
            print("  %-7d %-6s %10.0f %9.1f %9.1f %8.1f %8.1f"
                  % (r["f"], r["beat"], r["cover_px"], r["d_med"], r["d_min"],
                     r["mm_px"], r["lens"]))
        # and the closing frame, always, because it is the brief's "before"
        c = [r for r in rows if r["f"] == 2978]
        if c:
            r = c[0]
            print("  %-7d %-6s %10.0f %9.1f %9.1f %8.1f %8.1f   <- CLOSING"
                  % (r["f"], r["beat"], r["cover_px"], r["d_med"], r["d_min"],
                     r["mm_px"], r["lens"]))
        # per-beat best, so a near frame can be chosen per beat
        print("  per-beat best:")
        for bn, _, _ in BEATS:
            br = [r for r in rows if r["beat"] == bn]
            if br:
                r = max(br, key=lambda r: r["cover_px"])
                print("    %-6s f%-6d cover %9.0f  d_med %8.1f m  mm/px %7.1f"
                      % (bn, r["f"], r["cover_px"], r["d_med"], r["mm_px"]))

    if a.json:
        os.makedirs(os.path.dirname(a.json) or ".", exist_ok=True)
        json.dump({"note": "cover_px is occlusion-blind: an UPPER BOUND",
                   "surfaces": {k: v[:400] for k, v in out.items()}},
                  open(a.json, "w"), indent=1)
        print("\nwrote %s" % a.json)
    print("\nSTAGE RESULT: r2366_surface_visibility PASS")


if __name__ == "__main__":
    main()
