#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R2-2990 -- what distance, what lens and how many pixels does the film ACTUALLY
give ``forecourt_paving_bay``?

    python3 tools/r2990_forecourt_framing.py --selftest
    python3 tools/r2990_forecourt_framing.py --out work/r2990/framing.json

WHY
---
`render/items/forecourt_paving_bay/gate.json` reads ITEM_ACCEPTED at
`filmed_at_m = 1.7`, `onscreen_px_4k = 2160`, i.e. **2196.1 px/m, 0.4554 mm/px**.
That framing came from `docs/item_manifest.json`, whose `nearest_camera_m` is a
reconstructed corridor distance with no frustum test and no script
(`tools/screen_presence.py` docstring; `docs/WAVE2-RANKING.md` sec 7 step 1
measures the manifest over-framing by a MEDIAN 8.83x and a worst 336x).

`work/w2_0/retier_a10/sp_objects.json` says the host surface
``ARCH_Paving_Forecourt`` -- which IS this item's own geometry, not a shared
host, because the module's docstring says it replaces those bay faces one for
one -- peaks at **1049.4475 unoccluded sharp px/m at f282**, 0.9529 mm/px.
Those two disagree by 2.09x in linear resolution.

This file settles it against the camera, the way `lighting_mast.derive_framing()`
settled R2-1362 (host-derived 7.602 m -> measured 84.18 m).

EVERY AUTHORITY, AND NOT ONE OF THEM RETYPED
--------------------------------------------
| input | source |
|---|---|
| camera | `tools/live_campath.load()` -- takes NO path, so it cannot be given the wrong one. Resolves to film19 today. |
| projection | `RES_X`, `RES_Y`, `SENSOR_MM`, `SMEAR_SHARP_PX`, `OCC_RES`, `OCC_TOL_M` imported from `tools/screen_presence.py` |
| shutter | `anim/filmtime.py` via screen_presence's own `--uniform-shutter` mode (flat 180 deg, R2-037) |
| surface points | `work/w2_0/retier_a10/world_points.npz`, object `ARCH_Paving_Forecourt` |
| bay size | `CELL_W`, `CELL_H`, `SETOUT_X`, `SETOUT_Y` imported from `world/items/forecourt_paving_bay.py` |

THE THREE NUMBERS THIS PRODUCES, AND WHY THEY ARE THREE AND NOT ONE
--------------------------------------------------------------------
1. ``depth_m``       -- the true pinhole depth at the peak sharp frame.
2. ``lens_mm``       -- the EVALUATED focal length at that frame. It is not 35.
3. ``gate_dist_m``   -- the distance to hand `item_gate.py --filmed-distance-m`.

(3) is NOT (1), and that is R2-1367: `item_gate.py:3046` honours
`--filmed-distance-m` but line ~3053 reads `lens = rec["lens_at_closest_mm"]`
straight out of the manifest with no override. So the witness is always staged
on the manifest's lens. To reproduce the film's px/m the caller must hand the
gate the distance that yields it AT THE MANIFEST LENS:

    gate_dist_m = (RES_X * manifest_lens / SENSOR_MM) / measured_px_per_m

and say out loud that it is a 35 mm-equivalent, not a position.

OCCLUSION
---------
Replicated from screen_presence step 5: a quarter-res depth buffer rasterised
from the SAME point cloud, so a hole in the cloud can only let a hidden point
through. `unoccluded` is therefore a LOWER bound on occlusion and an UPPER bound
on visibility -- and every conclusion drawn here is a DEMOTION (the item is
filmed further away and smaller than the manifest says), which is the safe
direction against an upper bound.

Two passes, because the buffer needs all 3.04 M points but the answer needs only
the frames that could win: pass 1 sweeps the 2,448 forecourt points over all
2,978 frames with no occlusion; pass 2 rasterises the full cloud for the
`--occ-frames` best candidates only.

The shortlist is not an approximation and there is a runtime assertion that says
so. Occlusion can only REMOVE points, never raise a frame's px/m, so a frame's
occluded-and-sharp peak is bounded above by its sharp peak with occlusion
ignored. If the winner's px/m is at least the WEAKEST shortlisted frame's
no-occlusion sharp px/m, no excluded frame could have beaten it. That inequality
is checked on every run (`shortlist_sufficient`) and the tool REFUSES if it does
not hold, rather than quietly returning the best of an arbitrary 240.
"""

import argparse
import json
import math
import os
import re
import sys

import numpy as np

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(R2, "tools"), os.path.join(R2, "world"),
           os.path.join(R2, "anim")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import gate_exit                                                  # noqa: E402
import live_campath                                               # noqa: E402
import screen_presence as SP                                      # noqa: E402

# Projection constants -- IMPORTED, never retyped. Seven copies of the car's
# bounding box already exist in this tree; this makes no eighth of anything.
RES_X, RES_Y = SP.RES_X, SP.RES_Y
SENSOR_MM = SP.SENSOR_MM
SMEAR_SHARP_PX = SP.SMEAR_SHARP_PX
OCC_RES = SP.OCC_RES
OCC_TOL_M = SP.OCC_TOL_M

POINTS = os.path.join(R2, "work", "w2_0", "retier_a10", "world_points.npz")
SP_OBJECTS = os.path.join(R2, "work", "w2_0", "retier_a10", "sp_objects.json")
HOST_OBJECT = "ARCH_Paving_Forecourt"

# The camera sp_objects.json was measured against. Named ONLY so the calibration
# control can reproduce its published number; never used for a live reading.
SP_CAMERA_FOR_CONTROL = "render/film17_path.json"


# --------------------------------------------------------------------- camera
def camera_track(path_file):
    """(C[n,3], R[n,3,3], lens[n]). The quaternion-to-matrix conversion is
    `screen_presence.camera_track`'s, imported rather than re-derived -- a
    second copy of a rotation convention is exactly the class of duplication
    R2-1007 and `tools/shipping_world.py` exist to prevent."""
    C, Rm, _s, lens, _n = SP.camera_track(path_file)
    return C, Rm, lens


def flat_shutter(n):
    """The flat 180 deg shutter that ships (R2-037): 0.5 of a frame, every frame."""
    return np.full(n, 0.5)


def campath_divergence(a_file, b_file):
    """Per-frame difference between two camera paths.

    Exists because this reading rests entirely on ONE frame being the same in
    the camera `sp_objects.json` was measured against and the camera the film
    has. R2-2947 states that f282 is bit-identical; a statement is not a
    measurement, and "confined to beat 1" was inherited on exactly that basis
    from a DIFFERENT pair of cameras and was false of this one.
    """
    Ca, Ra, la = camera_track(a_file)
    Cb, Rb, lb = camera_track(b_file)

    # NORMALISE. `screen_presence.camera_track` builds R straight from the
    # stored quaternion without normalising it, and the path files round q to
    # six decimals, so |q|^2 = 0.999999 and the resulting matrix is off
    # orthonormal by ~1e-6. Feeding that to acos((tr-1)/2) -- which is
    # ill-conditioned at tr=3 -- turns a 1e-6 scale error into an apparent
    # 0.17 DEGREE rotation. R2-2947 reports exactly 0.17 deg at f282 for two
    # quaternions that are BYTE-IDENTICAL in the two files. That figure is the
    # artifact, not a drift. The identity arm in --selftest is what caught it.
    def _orthonormalise(R):
        u, _, vt = np.linalg.svd(R)
        return u @ vt
    Ra = np.stack([_orthonormalise(m) for m in Ra])
    Rb = np.stack([_orthonormalise(m) for m in Rb])

    n = min(len(Ca), len(Cb))
    per, ndiff = [], 0
    worst_p = worst_l = worst_a = 0.0
    wpf = wlf = waf = 0
    for f in range(n):
        dp = float(np.linalg.norm(Ca[f] - Cb[f]))
        dl = float(abs(la[f] - lb[f]))
        # Angle between the two rotations, via the FROBENIUS norm and not via
        # acos((tr-1)/2). For rotations ||Ra-Rb||_F = 2*sqrt(2)*|sin(theta/2)|
        # exactly, and asin is well conditioned at 0 where acos is not. The
        # acos form turned a 1e-6 quaternion-normalisation error into 0.17 deg;
        # this form returns EXACTLY 0.0 for identical inputs, which is what the
        # identity arm requires.
        fro = float(np.linalg.norm(Ra[f] - Rb[f]))
        da = math.degrees(2.0 * math.asin(min(1.0, fro / (2.0 * math.sqrt(2.0)))))
        per.append({"f": f + 1, "dpos_m": dp, "dlens_mm": dl, "dang_deg": da})
        if dp > 0 or dl > 0 or da > 0:
            ndiff += 1
        if dp > worst_p:
            worst_p, wpf = dp, f + 1
        if dl > worst_l:
            worst_l, wlf = dl, f + 1
        if da > worst_a:
            worst_a, waf = da, f + 1
    return {"n": n, "n_differ": ndiff, "per_frame": per,
            "worst_pos_m": worst_p, "worst_pos_f": wpf,
            "worst_lens_mm": worst_l, "worst_lens_f": wlf,
            "worst_ang_deg": worst_a, "worst_ang_f": waf}


# ------------------------------------------------------------------- geometry
def load_host_points(npz=POINTS, obj_name=HOST_OBJECT):
    z = np.load(npz, allow_pickle=True)
    names = list(z["names"])
    if obj_name not in names:
        raise SystemExit("REFUSING: %r is not in %s" % (obj_name, npz))
    i = names.index(obj_name)
    m = z["obj"] == i
    pts = z["pts"][m].astype(np.float64)
    if not len(pts):
        raise SystemExit("REFUSING: %r has 0 points" % obj_name)
    return pts


def cell_m(npz=POINTS):
    """The point cloud's voxel pitch, from its own metadata."""
    z = np.load(npz, allow_pickle=True)
    return float(json.loads(str(z["meta"]))["cell_m"])


def _r1_shell():
    """`R1_SHELL` lifted out of `world/build_architecture.py`'s own AST.

    That module imports `bpy` at module scope and cannot be imported from bare
    python, and it is CONTENDED by another agent right now, so it is neither
    imported nor edited nor retyped -- it is parsed. Same technique as
    `tools/r2941_veg_framing.py`.
    """
    import ast
    src = open(os.path.join(R2, "world", "build_architecture.py")).read()
    for node in ast.parse(src).body:
        if (isinstance(node, ast.Assign) and node.targets
                and getattr(node.targets[0], "id", None) == "R1_SHELL"):
            return tuple(ast.literal_eval(node.value))
    raise SystemExit("REFUSING: no R1_SHELL assignment in build_architecture.py")


def subject_mask(pts, npz=POINTS):
    """WHICH OF THE HOST OBJECT'S POINTS ARE THE ITEM'S OWN GEOMETRY.

    THE DEFECT THIS EXISTS TO CATCH. `ARCH_Paving_Forecourt` is not only the
    paving bays. `world/items/forecourt_paving_bay.py`'s own docstring, section
    "WHAT THE ASSEMBLY MUST DELETE", says the item replaces THE BAY FACES AND
    ONLY THE BAY FACES, and that the assembly must KEEP the object's sub-base
    prism (-0.30..-0.012) and "its formation slab under the pavilion
    (R1_FORMATION_Z)". Those two are the same Blender object and therefore the
    same row in `sp_objects.json`.

    Three rules, each one auditable, and each one with the count it removes
    printed by --selftest:

      1. THE BAY PLANE. Keep only the voxel layer that contains the flag top at
         `world_contract.APRON_Z`. The cloud is voxelised at `cell_m` (1.0 m)
         with cell CENTRES, so the layer is derived, not typed. This alone drops
         the sub-base prism and the buried formation slab into their own layer.
      2. OUTSIDE THE PAVILION. `R1_SHELL` is cut out of the paving; anything of
         this object inside it is slab under the showroom floor.
      3. OUTSIDE THE ACCESS RIBBON. `forecourt_paving_bay.RIBBON_KEEPOUT`.

    AND THE VOXEL Z IS REPLACED BY THE KNOWN PLANE. A cell centre is 0.5 m above
    the surface it samples, and the camera is 2.9 m above that surface, so an
    uncorrected sample is 17 % closer than the concrete. x and y keep their
    quantisation -- nothing here can fix that -- but z is known to +3.5/-9.0 mm
    from the module's own asserted bounds, so it is set exactly.
    """
    import world_contract as C
    cm = cell_m(npz)
    layer_z = math.floor(C.APRON_Z / cm) * cm + cm / 2.0
    sh = _r1_shell()
    kx0, kx1, ky0, ky1 = FCP.RIBBON_KEEPOUT
    in_layer = np.abs(pts[:, 2] - layer_z) < cm / 2.0
    in_shell = ((pts[:, 0] >= sh[0]) & (pts[:, 0] <= sh[1]) &
                (pts[:, 1] >= sh[2]) & (pts[:, 1] <= sh[3]))
    in_rib = ((pts[:, 0] >= kx0) & (pts[:, 0] <= kx1) &
              (pts[:, 1] >= ky0) & (pts[:, 1] <= ky1))
    keep = in_layer & ~in_shell & ~in_rib
    detail = {"cell_m": cm, "bay_layer_z": layer_z, "r1_shell": list(sh),
              "ribbon_keepout": list(FCP.RIBBON_KEEPOUT),
              "n_total": int(len(pts)),
              "n_off_bay_layer": int((~in_layer).sum()),
              "n_inside_pavilion": int(in_shell.sum()),
              "n_in_ribbon": int(in_rib.sum()),
              "n_kept": int(keep.sum()),
              "apron_z": float(C.APRON_Z)}
    return keep, detail


def to_bay_plane(pts, npz=POINTS):
    """Same points with z set to the flag top plane. See `subject_mask`."""
    import world_contract as C
    q = pts.copy()
    q[:, 2] = C.APRON_Z
    return q


def project(pts, Cf, Rf, lens_mm):
    """-> (depth, px, py, in_frustum). depth is PINHOLE -Z, not radial."""
    P = pts - Cf
    depth = -(P @ Rf[:, 2])
    xc = P @ Rf[:, 0]
    yc = P @ Rf[:, 1]
    s = RES_X * lens_mm / SENSOR_MM
    d = np.where(depth > 1e-6, depth, 1e-6)
    px = RES_X * 0.5 + s * xc / d
    py = RES_Y * 0.5 + s * yc / d
    inf = (depth > 0.05) & (px >= 0) & (px < RES_X) & (py >= 0) & (py < RES_Y)
    return depth, px, py, inf


def frame_metrics(pts, Cf, Rf, Cn, Rn, lens_f, lens_n, shutter_f,
                  radial=False, no_frustum=False, no_smear=False):
    """(ppm, depth, in_frustum, sharp) for ONE frame.

    ONE definition, used by BOTH passes. It is a function and not two inlined
    copies because the two copies is the bug the control harness caught: pass 2
    re-derived the winner with its own undamaged arithmetic, so `radial`,
    `no_frustum` and `no_smear` altered only the shortlist ORDER and the same
    frame won anyway. Four damage arms read 0.00 % moved -- i.e. four checks
    that changed nothing, which is this project's most-logged defect shape,
    committed by the very file written to catch it.
    """
    depth, px, py, inf = project(pts, Cf, Rf, lens_f)
    if no_frustum:
        inf = depth > 0.05
    s = RES_X * lens_f / SENSOR_MM
    if radial:
        # THE MANIFEST'S OWN ERROR: radial distance where pinhole depth
        # belongs (screen_presence docstring step 1).
        den = np.linalg.norm(pts - Cf, axis=1)
    else:
        den = depth
    ppm = s / np.maximum(den, 1e-6)
    _, px2, py2, _ = project(pts, Cn, Rn, lens_n)
    smear = shutter_f * np.hypot(px2 - px, py2 - py)
    sharp = inf if no_smear else (inf & (smear <= SMEAR_SHARP_PX))
    return ppm, depth, inf, sharp, smear


def sweep(pts, C, Rm, lens, shutter, radial=False, no_frustum=False,
          no_smear=False):
    """Pass 1. Per frame, the best px/m over the object's points.

    `radial`, `no_frustum`, `no_smear` are DAMAGE SWITCHES for the control
    harness. They are arguments and not edits so the damaged run is the same
    code path as the live one.
    """
    n = len(C)
    out = np.zeros((n, 4))          # best_ppm_sharp, depth_at, best_ppm_any, nvis
    for f in range(n):
        g = min(f + 1, n - 1)
        ppm, depth, inf, sh, _sm = frame_metrics(
            pts, C[f], Rm[f], C[g], Rm[g], lens[f], lens[g], shutter[f],
            radial=radial, no_frustum=no_frustum, no_smear=no_smear)
        if not inf.any():
            continue
        out[f, 3] = int(inf.sum())
        out[f, 2] = float(ppm[inf].max())
        if sh.any():
            k = int(np.argmax(np.where(sh, ppm, -1.0)))
            out[f, 0] = ppm[k]
            out[f, 1] = depth[k]
    return out


def occ_mask_for_frame(all_pts, subject_pts, Cf, Rf, lens_mm, no_buffer=False):
    """Replicate screen_presence step 5 for ONE frame.

    The buffer is rasterised from the WHOLE cloud; `subject_pts` are then tested
    against it. They are passed separately rather than as a mask because the
    subject's z has been snapped to the bay plane (`to_bay_plane`) and the
    buffer must still be built from the cloud as it is.

    -> boolean over `subject_pts`: True = in front of the buffer.
    """
    depth, px, py, inf = project(all_pts, Cf, Rf, lens_mm)
    ow, oh = RES_X // OCC_RES, RES_Y // OCC_RES
    qx = np.clip((px[inf] / OCC_RES).astype(np.int32), 0, ow - 1)
    qy = np.clip((py[inf] / OCC_RES).astype(np.int32), 0, oh - 1)
    buf = np.full(ow * oh, np.inf, dtype=np.float32)
    if not no_buffer:
        np.minimum.at(buf, qy * ow + qx, depth[inf].astype(np.float32))
    sd, spx, spy, sinf = project(subject_pts, Cf, Rf, lens_mm)
    # spx/spy are only meaningful where the point is in frustum; elsewhere the
    # divide by a clamped depth can produce inf/NaN and casting that to int32 is
    # undefined. Index with zeros there and let `sinf` do the rejecting.
    sqx = np.clip(np.where(sinf, spx, 0.0) / OCC_RES, 0, ow - 1).astype(np.int32)
    sqy = np.clip(np.where(sinf, spy, 0.0) / OCC_RES, 0, oh - 1).astype(np.int32)
    front = sinf & (sd <= buf[sqy * ow + sqx] + OCC_TOL_M)
    return front


# ------------------------------------------------------------- the bay on screen
def bay_screen_px(pts, Cf, Rf, lens_mm, cell_w, cell_h, setout_x, setout_y):
    """How many 4K pixels ONE 1.5 x 1.0 m flag covers at this frame.

    The manifest applies its px formula to an in-plane dimension with no regard
    for the angle it is seen at (screen_presence's FORESHORTENING note). A
    paving flag is horizontal under a camera a couple of metres up, so its
    on-screen size is NOT `1.0 m * px_per_m`. This projects the flag's four
    ACTUAL corners, on the module's own setting-out grid, and reports the
    screen-space extent of the quad.

    -> dict with the winning cell, its corner pixels, and three sizes:
       `diag_px` (the longest screen diagonal -- what the eye calls "how big"),
       `bbox_px` (max of the screen bbox sides), and `naive_px` (the manifest's
       unforeshortened `cell_h * px_per_m`, for the comparison).
    """
    depth, px, py, inf = project(pts, Cf, Rf, lens_mm)
    if not inf.any():
        return None
    s = RES_X * lens_mm / SENSOR_MM
    ppm = s / np.maximum(depth, 1e-6)
    k = int(np.argmax(np.where(inf, ppm, -1.0)))
    x, y = pts[k, 0], pts[k, 1]
    # the cell this point falls in, on the module's own grid
    i = math.floor((setout_x - x) / cell_w)
    j = math.floor((y - setout_y) / cell_h)
    x1, x0 = setout_x - i * cell_w, setout_x - (i + 1) * cell_w
    y0, y1 = setout_y + j * cell_h, setout_y + (j + 1) * cell_h
    corners = np.array([[x0, y0, pts[k, 2]], [x1, y0, pts[k, 2]],
                        [x1, y1, pts[k, 2]], [x0, y1, pts[k, 2]]])
    cd, cx, cy, _ = project(corners, Cf, Rf, lens_mm)
    diag = 0.0
    for a in range(4):
        for b in range(a + 1, 4):
            diag = max(diag, math.hypot(cx[a] - cx[b], cy[a] - cy[b]))
    return {
        "cell_ij": [i, j],
        "cell_world": [round(x0, 3), round(x1, 3), round(y0, 3), round(y1, 3)],
        "corner_px": [[round(float(cx[t]), 1), round(float(cy[t]), 1)]
                      for t in range(4)],
        "corner_depth_m": [round(float(cd[t]), 4) for t in range(4)],
        "diag_px": round(diag, 1),
        "bbox_px": round(max(float(cx.max() - cx.min()),
                             float(cy.max() - cy.min())), 1),
        "naive_px": round(float(cell_h * ppm[k]), 1),
        "nearest_point_depth_m": round(float(depth[k]), 4),
        "px_per_m_here": round(float(ppm[k]), 2),
    }


# --------------------------------------------------------------------- reading
def camera_indoors(C):
    """Frames where the lens is inside the pavilion plan `R1_SHELL`.

    THE FRAME FALSIFIED THE READING, TWICE, BEFORE THIS EXISTED. The occlusion
    model is a quarter-res depth buffer rasterised from a 1 m point cloud, and
    `screen_presence.py` says in terms that `ever_unoccluded = True` is not
    proof -- a hole in the cloud lets a hidden point through. The pavilion shell
    is a wall between a camera inside it and a forecourt outside it, and the
    cloud cannot express a wall at 1 m.

    So the winning frames were LOOKED AT. `work/r22161_proxy/*_000282.png` is a
    showroom interior; `*_000104.png` is a dark showroom floor with suspension
    parts hanging over it and a concrete wall behind. Neither contains any
    forecourt paving. This is `tools/r2941_veg_framing.py`'s reading 2 exactly:
    a peak at f147 that turned out to be a wheel macro indoors.

    A coarse proxy, adopted only after the image refuted the alternative, and
    stated as coarse: it excludes the camera being inside the shell, NOT the
    shell being between the camera and the paving from outside.
    """
    sh = _r1_shell()
    return ((C[:, 0] >= sh[0]) & (C[:, 0] <= sh[1]) &
            (C[:, 1] >= sh[2]) & (C[:, 1] <= sh[3]))


def take_reading(campath_file, label, occ_frames=240, damage=None, quiet=False,
                 min_points=1, outdoor_only=False):
    """`min_points` -- how many of the object's cloud points must be sharp AND
    unoccluded AND in frustum before a frame is allowed to set the peak.

    `sp_objects.json` uses 1, implicitly: its peak is a `np.maximum.at` over
    points with no floor at all. On this object that turns out to matter more
    than anything else in this file -- the published 1049.4475 px/m is set by
    ONE cloud point out of 2,448, in a frame where three are in frustum. A
    single sample of a surface sampled at `cell_m` spacing is not a measurement
    of how that surface is filmed, it is the extreme tail of one. So the reading
    is taken at several floors and all of them are reported.
    """
    damage = damage or {}
    pts_all = load_host_points()
    keep, mask_detail = subject_mask(pts_all)
    if damage.get("no_subject_mask"):
        keep = np.ones(len(pts_all), dtype=bool)
    pts = pts_all[keep]
    if not damage.get("no_plane_snap"):
        pts = to_bay_plane(pts)
    C, Rm, lens = camera_track(campath_file)
    shutter = flat_shutter(len(C))
    per = sweep(pts, C, Rm, lens, shutter,
                radial=damage.get("radial", False),
                no_frustum=damage.get("no_frustum", False),
                no_smear=damage.get("no_smear", False))

    # pass 2: occlusion on the shortlist
    z = np.load(POINTS, allow_pickle=True)
    all_pts = z["pts"].astype(np.float64)

    indoors = camera_indoors(C)
    if outdoor_only:
        per[indoors, 0] = 0.0
    order = np.argsort(-per[:, 0])
    cand = [int(f) for f in order[:occ_frames] if per[f, 0] > 0]
    best = None
    for f in cand:
        fr = occ_mask_for_frame(all_pts, pts, C[f], Rm[f], lens[f],
                                no_buffer=damage.get("no_occ", False))
        if not fr.any():
            continue
        g = min(f + 1, len(C) - 1)
        ppm, depth, inf, sh, smear = frame_metrics(
            pts, C[f], Rm[f], C[g], Rm[g], lens[f], lens[g], shutter[f],
            radial=damage.get("radial", False),
            no_frustum=damage.get("no_frustum", False),
            no_smear=damage.get("no_smear", False))
        good = sh & fr
        if int(good.sum()) < min_points:
            continue
        k = int(np.argmax(np.where(good, ppm, -1.0)))
        rec = {"frame": f + 1, "ppm": float(ppm[k]), "depth_m": float(depth[k]),
               "lens_mm": float(lens[f]),
               "smear_px": float(smear[k]),
               "n_sharp_unocc_pts": int(good.sum())}
        if best is None or rec["ppm"] > best["ppm"]:
            best = rec
    if best is None:
        raise SystemExit(
            "REFUSING: no frame has %d sharp unoccluded point(s) for %s"
            % (min_points, label))

    # SHORTLIST SUFFICIENCY -- see the docstring. Occlusion only removes points,
    # so no frame outside the shortlist can beat a winner that already exceeds
    # the weakest shortlisted frame's occlusion-free sharp px/m.
    cutoff = float(per[cand[-1], 0]) if cand else 0.0
    if best["ppm"] < cutoff:
        raise SystemExit(
            "REFUSING: the %d-frame occlusion shortlist may have excluded the "
            "winner -- best found %.4f px/m but the weakest shortlisted frame "
            "could reach %.4f. Re-run with a larger --occ-frames."
            % (len(cand), best["ppm"], cutoff))

    f = best["frame"] - 1
    bay = bay_screen_px(pts, C[f], Rm[f], lens[f], FCP.CELL_W, FCP.CELL_H,
                        FCP.SETOUT_X, FCP.SETOUT_Y)
    # how many frames are sharp+in-frustum at all (no occlusion) -- comparable
    # with sp_objects' `frames_sharp`
    frames_sharp = int((per[:, 0] > 0).sum())
    out = {
        "label": label,
        "host_object": HOST_OBJECT,
        "n_points": int(len(pts)),
        "subject_mask": mask_detail,
        "peak_sharp": best,
        "peak_sharp_mm_per_px": 1000.0 / best["ppm"],
        "frames_sharp_in_frustum": frames_sharp,
        "min_depth_m_in_frustum": float(
            np.min(per[per[:, 1] > 0, 1])) if (per[:, 1] > 0).any() else None,
        "peak_any_ppm": float(per[:, 2].max()),
        "peak_any_frame": int(np.argmax(per[:, 2])) + 1,
        "bay_on_screen": bay,
        "min_points": min_points,
        "outdoor_only": bool(outdoor_only),
        "frames_camera_indoors": int(indoors.sum()),
        "shortlist": {"n": len(cand), "weakest_no_occ_sharp_ppm": cutoff,
                      "sufficient": True},
        "damage": damage or None,
    }
    if not quiet:
        print(">> %-40s min_pts %-3d f%-5d %9.3f px/m  %.4f mm/px  "
              "depth %8.4f m  lens %6.3f mm  (%d pts sharp+unocc)"
              % (label, min_points, best["frame"], best["ppm"],
                 1000.0 / best["ppm"], best["depth_m"], best["lens_mm"],
                 best["n_sharp_unocc_pts"]))
    return out


# ------------------------------------------------------- the gate's framing pair
def gate_framing(ppm, manifest_lens_mm):
    """What to hand `item_gate.py`, given the trap it carries.

    R2-1367: the gate honours --filmed-distance-m and IGNORES the lens. So the
    distance that reproduces `ppm` in the witness is a 35 mm-EQUIVALENT, not a
    position, and it must be reported as one.
    """
    return (RES_X * manifest_lens_mm / SENSOR_MM) / ppm


# ------------------------------------------------------------------- selftest
def _selftest():
    ok = True

    def chk(name, cond, msg=""):
        nonlocal ok
        print("  %-58s %s  %s" % (name, "ok  " if cond else "FAIL", msg))
        ok = ok and bool(cond)

    print(">> SELFTEST r2990_forecourt_framing")

    # ---------- projection algebra, closed form -----------------------------
    # A point 10 m dead ahead on a 50 mm lens must land at frame centre and
    # report s/depth px/m exactly.
    Rf = np.eye(3)                                # identity: cam looks down -Z
    p = np.array([[0.0, 0.0, -10.0]])
    d, px, py, inf = project(p, np.zeros(3), Rf, 50.0)
    chk("closed form: depth", abs(d[0] - 10.0) < 1e-9, "%.6f" % d[0])
    chk("closed form: lands at frame centre",
        abs(px[0] - RES_X / 2) < 1e-6 and abs(py[0] - RES_Y / 2) < 1e-6)
    want = (RES_X * 50.0 / SENSOR_MM) / 10.0
    chk("closed form: px/m", abs(want - 533.3333) < 1e-3, "%.4f px/m" % want)

    # ---------- NEGATIVE: behind the camera is not in frustum ---------------
    d, px, py, inf = project(np.array([[0.0, 0.0, +10.0]]), np.zeros(3), Rf, 50.0)
    chk("MUST REJECT: a point behind the camera", not inf[0], "depth %.3f" % d[0])

    # ---------- NEGATIVE: outside the frame is not in frustum ---------------
    # half-width at 10 m on a 50 mm lens is 10*18/50 = 3.6 m
    d, px, py, inf = project(np.array([[3.7, 0.0, -10.0]]), np.zeros(3), Rf, 50.0)
    chk("MUST REJECT: 3.7 m off axis (frame half-width 3.6 m)", not inf[0],
        "px %.1f of %d" % (px[0], RES_X))
    d, px, py, inf = project(np.array([[3.5, 0.0, -10.0]]), np.zeros(3), Rf, 50.0)
    chk("  ...and 3.5 m off axis IS in frustum (the arm is not vacuous)", inf[0],
        "px %.1f" % px[0])

    # ---------- NEGATIVE: pinhole depth is not radial distance --------------
    p = np.array([[3.0, 0.0, -4.0]])
    d, _, _, _ = project(p, np.zeros(3), Rf, 35.0)
    rad = float(np.linalg.norm(p))
    chk("pinhole depth (4.0) differs from radial (5.0)",
        abs(d[0] - 4.0) < 1e-9 and abs(rad - 5.0) < 1e-9,
        "the manifest's own error is worth 25 %% here")

    # ---------- the gate framing pair, and the lens trap --------------------
    gd = gate_framing(1049.4475, 35.0)
    chk("gate 35 mm-equivalent distance for 1049.45 px/m",
        abs(gd - 3.5575) < 1e-3, "%.4f m" % gd)
    chk("  ...and it is NOT the true depth when the lens is not 35",
        abs(gate_framing(1049.4475, 38.0) - gd) > 0.1,
        "at 38 mm the same px/m needs %.4f m" % gate_framing(1049.4475, 38.0))

    # ---------- bay projection: a flag seen face-on at a known distance -----
    # camera 10 m straight up over the origin looking down: -Z world = -Z cam
    Rdown = np.array([[1.0, 0, 0], [0, 1.0, 0], [0, 0, 1.0]])
    ptsq = np.array([[0.05, 0.05, 0.0]])
    b = bay_screen_px(ptsq, np.array([0.0, 0.0, 10.0]), Rdown, 35.0,
                      1.5, 1.0, 15.0, 0.0)
    ppm = (RES_X * 35.0 / SENSOR_MM) / 10.0
    want_diag = math.hypot(1.5, 1.0) * ppm
    chk("bay: face-on diagonal == sqrt(1.5^2+1^2) * px/m",
        abs(b["diag_px"] - want_diag) < 1.0,
        "%.1f px vs %.1f" % (b["diag_px"], want_diag))
    chk("bay: the cell contains the point it was found from",
        b["cell_world"][0] <= 0.05 <= b["cell_world"][1] and
        b["cell_world"][2] <= 0.05 <= b["cell_world"][3],
        "cell %s" % b["cell_world"])

    # ---------- NEGATIVE: foreshortening must actually bite -----------------
    # the same flag from 10 m away at 10 deg above its plane
    th = math.radians(10.0)
    Cg = np.array([0.05 - 10 * math.cos(th), 0.05, 10 * math.sin(th)])
    fwd = (np.array([0.05, 0.05, 0.0]) - Cg)
    fwd /= np.linalg.norm(fwd)
    zc = -fwd
    up = np.array([0.0, 0.0, 1.0])
    xc = np.cross(up, zc); xc /= np.linalg.norm(xc)
    yc = np.cross(zc, xc)
    Rg = np.stack([xc, yc, zc], axis=1)
    bg = bay_screen_px(ptsq, Cg, Rg, 35.0, 1.5, 1.0, 15.0, 0.0)
    # closed form: the 1.5 m axis lies along the view and collapses to
    # 1.5*sin(10 deg); the 1.0 m axis is across the view and does not.
    want_g = math.hypot(1.5 * math.sin(th), 1.0) * ppm
    chk("MUST SHRINK: a grazing flag matches the closed-form foreshortening",
        abs(bg["diag_px"] - want_g) / want_g < 0.03,
        "%.1f px grazing vs closed form %.1f (face-on was %.1f, so "
        "foreshortening removes %.0f %%)"
        % (bg["diag_px"], want_g, b["diag_px"],
           100 * (1 - bg["diag_px"] / b["diag_px"])))
    chk("  ...and the naive unforeshortened figure is the one that is wrong",
        abs(bg["naive_px"] - 1.0 * ppm) < 2.0,
        "naive says %.1f px for the same flag" % bg["naive_px"])

    # ---------- the live camera resolves, and it is not a literal -----------
    p = live_campath.declared_campath()
    chk("live camera resolves through live_campath (no path named here)",
        os.path.exists(p), os.path.relpath(p, R2))
    src = open(__file__).read()
    lits = set(re.findall(r"film\d+_path\.json", src))
    chk("  ...and the ONLY path literal in this file is the control's",
        lits == {os.path.basename(SP_CAMERA_FOR_CONTROL)},
        "literals present: %s" % (sorted(lits) or "none"))

    # ---------- THE SUBJECT MASK, and the defect it was written for ---------
    ap = load_host_points()
    keep, det = subject_mask(ap)
    print("  -- subject mask: %d points in %s -> %d are the item's own"
          % (det["n_total"], HOST_OBJECT, det["n_kept"]))
    print("     %d off the bay layer (sub-base + formation), %d inside "
          "R1_SHELL %s, %d in the access ribbon"
          % (det["n_off_bay_layer"], det["n_inside_pavilion"],
             det["r1_shell"], det["n_in_ribbon"]))
    chk("the mask removes something and keeps something",
        0 < det["n_kept"] < det["n_total"],
        "%d of %d kept" % (det["n_kept"], det["n_total"]))
    chk("R1_SHELL was parsed out of build_architecture, not typed",
        _r1_shell() == (-15.250, 15.000, -11.250, 11.250), str(_r1_shell()))
    chk("the bay layer is DERIVED from cell_m and APRON_Z",
        abs(det["bay_layer_z"] - 0.5) < 1e-9 and det["cell_m"] == 1.0,
        "layer z %.3f at cell %.2f m" % (det["bay_layer_z"], det["cell_m"]))

    # THE ARM THAT MATTERS: the point that sets sp_objects' published peak must
    # be one this mask REJECTS, and the reason must be nameable.
    bad = np.array([[3.5, -3.5, -0.5]])
    kb, _ = subject_mask(bad)
    chk("MUST REJECT: (3.5,-3.5,-0.5) -- the voxel that sets the published "
        "1049.4475 px/m", not kb[0],
        "it is inside R1_SHELL and on the formation-slab layer, and the "
        "module's docstring says it does not build either")
    good = np.array([[FCP.TEST_CENTRE[0], FCP.TEST_CENTRE[1], 0.5]])
    kg, _ = subject_mask(good)
    chk("  ...and MUST KEEP a point on the east forecourt at the bay layer",
        kg[0], "the arm is not just 'reject everything'")

    # plane snap
    snapped = to_bay_plane(ap[keep])
    chk("plane snap puts every kept point on APRON_Z",
        float(np.abs(snapped[:, 2]).max()) == 0.0,
        "max |z| = %.6f" % float(np.abs(snapped[:, 2]).max()))
    chk("  ...and it MOVES them (the cloud is a voxel centre, not a surface)",
        float(np.abs(ap[keep][:, 2] - snapped[:, 2]).max()) > 0.4,
        "by %.3f m" % float(np.abs(ap[keep][:, 2] - snapped[:, 2]).max()))

    # ---------- IDENTITY ARM. A path against ITSELF must be exactly zero. ---
    # This is the arm that caught the 0.17 deg: it is not a drift, it is the
    # comparator's own numerical noise on an unnormalised quaternion, and a
    # self-comparison is the only way to see that.
    lp = live_campath.declared_campath()
    self_div = campath_divergence(lp, lp)
    worst_self = max(e["dang_deg"] for e in self_div["per_frame"])
    chk("IDENTITY: a path against itself reports 0 frames differing",
        self_div["n_differ"] == 0,
        "%d differ, worst angle %.3e deg" % (self_div["n_differ"], worst_self))

    # ---------- f282: are the two cameras the same there? -------------------
    # R2-2947 asserts they are bit-identical at the frame this whole reading
    # rests on. Taking that on trust is how "confined to beat 1" propagated.
    div = campath_divergence(lp, os.path.join(R2, SP_CAMERA_FOR_CONTROL))
    f282 = div["per_frame"][281]
    chk("f282 position identical across film17/film19",
        f282["dpos_m"] == 0.0, "%.6f m" % f282["dpos_m"])
    chk("f282 lens identical", f282["dlens_mm"] == 0.0,
        "%.6f mm" % f282["dlens_mm"])
    chk("f282 orientation identical (R2-2947's 0.17 deg was the artifact)",
        f282["dang_deg"] == 0.0, "%.3e deg" % f282["dang_deg"])
    # and prove it against the raw file, with no instrument in between
    ra = json.load(open(os.path.join(R2, SP_CAMERA_FOR_CONTROL)))["path"][281]
    rb = json.load(open(lp))["path"][281]
    chk("  ...confirmed on the RAW json: p, q and lens are byte-identical",
        ra["p"] == rb["p"] and ra["q"] == rb["q"] and ra["lens"] == rb["lens"],
        "q %s" % (ra["q"],))
    chk("  ...and the comparator is NOT vacuous: it finds the known drift",
        div["n_differ"] > 500 and div["worst_pos_m"] > 10.0,
        "%d of %d frames differ, worst %.3f m of position at f%d, "
        "%.3f mm of lens at f%d, %.3f deg at f%d"
        % (div["n_differ"], div["n"], div["worst_pos_m"], div["worst_pos_f"],
           div["worst_lens_mm"], div["worst_lens_f"],
           div["worst_ang_deg"], div["worst_ang_f"]))

    print()
    return gate_exit.verdict("R2990_FRAMING_OK" if ok else "R2990_FRAMING_FAIL",
                             " r2990_framing_selftest")


# --------------------------------------------------------------------------- main
import importlib.util as _ilu                                     # noqa: E402
_spec = _ilu.spec_from_file_location(
    "fcp_item", os.path.join(R2, "world", "items", "forecourt_paving_bay.py"))
FCP = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(FCP)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--out", default=None)
    ap.add_argument("--occ-frames", type=int, default=240)
    ap.add_argument("--min-points-ladder", type=int, nargs="*",
                    default=[2, 5, 10, 25, 50])
    ap.add_argument("--calibrate", action="store_true",
                    help="also take the reading on the camera sp_objects.json "
                         "used, and require it to reproduce its published "
                         "number. This is the instrument's calibration.")
    ap.add_argument("--damage", default=None,
                    choices=["radial", "no_frustum", "no_smear", "no_occ",
                            "no_subject_mask", "no_plane_snap"])
    a = ap.parse_args()
    if a.selftest:
        return _selftest()

    dmg = {a.damage: True} if a.damage else {}
    livecam = live_campath.declared_campath()      # sha-verified, raises if stale
    doc = {"camera": os.path.relpath(livecam, R2), "manifest_lens_mm": 35.0}

    # ---- CALIBRATION FIRST, and deliberately UNCORRECTED -------------------
    # The instrument is configured exactly as `screen_presence.py` was -- whole
    # object, voxel z as stored, no point floor -- on the camera sp_objects was
    # measured against. If it does not reproduce the published number to four
    # decimals then every correction below is a change of instrument and not a
    # finding, and there is nothing to say.
    sp = json.load(open(SP_OBJECTS))
    row = [r for r in sp["objects"] if r["object"] == HOST_OBJECT][0]
    if a.calibrate:
        live_campath.load_explicit(
            SP_CAMERA_FOR_CONTROL,
            why="R2-2990 calibration: reproduce sp_objects.json's published "
                "peak_unocc_sharp_px_per_m on the camera it was measured "
                "against, so every later difference is a change of camera or "
                "of subject and not a change of instrument")
        sp_dmg = dict(dmg); sp_dmg["no_subject_mask"] = True
        sp_dmg["no_plane_snap"] = True
        cal = take_reading(os.path.join(R2, SP_CAMERA_FOR_CONTROL),
                           "A. sp_objects reproduced", occ_frames=a.occ_frames,
                           damage=sp_dmg)
        pub, got = row["peak_unocc_sharp_px_per_m"], cal["peak_sharp"]["ppm"]
        err = abs(got - pub) / pub
        agree = err < 1e-4 and cal["peak_sharp"]["frame"] == row["sharp_frame"]
        doc["calibration"] = {
            "published_ppm": pub, "published_frame": row["sharp_frame"],
            "reproduced_ppm": got,
            "reproduced_frame": cal["peak_sharp"]["frame"],
            "rel_err": err, "agrees": bool(agree), "reading": cal}
        print(">> CALIBRATION: published %.4f px/m at f%d, reproduced %.4f at "
              "f%d -- %.4f %% apart -- %s"
              % (pub, row["sharp_frame"], got, cal["peak_sharp"]["frame"],
                 100 * err, "AGREE" if agree else "DISAGREE"))
        if not agree and not a.damage:
            return gate_exit.verdict("R2990_FRAMING_FAIL", " calibration")

    # ---- THE ABLATION. One correction at a time, each one named. -----------
    steps = [
        ("B. + the live camera",
         {"no_subject_mask": True, "no_plane_snap": True}, 1),
        ("C. + only the item's own geometry", {"no_plane_snap": True}, 1),
        ("D. + voxel centre -> the bay plane", {}, 1),
    ]
    for mp in a.min_points_ladder:
        steps.append(("E. + at least %d sharp unoccluded samples" % mp, {}, mp))

    steps = [(l, d, mp, False) for (l, d, mp) in steps]
    for mp in a.min_points_ladder:
        steps.append(("F. + camera OUTSIDE the pavilion, >= %d samples" % mp,
                      {}, mp, True))

    doc["ablation"] = []
    for label, d, mp, outdoor in steps:
        dd = dict(dmg); dd.update(d)
        try:
            r = take_reading(livecam, label, occ_frames=a.occ_frames,
                             damage=dd, min_points=mp, outdoor_only=outdoor)
        except SystemExit as exc:
            print(">> %-42s REFUSED: %s" % (label, exc))
            doc["ablation"].append({"step": label, "refused": str(exc)})
            continue
        doc["ablation"].append({
            "step": label, "min_points": mp, "damage": d or None,
            "outdoor_only": outdoor,
            "frame": r["peak_sharp"]["frame"], "ppm": r["peak_sharp"]["ppm"],
            "mm_per_px": r["peak_sharp_mm_per_px"],
            "depth_m": r["peak_sharp"]["depth_m"],
            "lens_mm": r["peak_sharp"]["lens_mm"],
            "n_pts": r["peak_sharp"]["n_sharp_unocc_pts"],
            "n_subject_points": r["n_points"],
            "frames_sharp_in_frustum": r["frames_sharp_in_frustum"],
            "gate_dist_35mm_equiv_m":
                gate_framing(r["peak_sharp"]["ppm"], 35.0),
            "bay_on_screen": r["bay_on_screen"],
            "subject_mask": r["subject_mask"]})
        doc["live"] = r        # the last step standing is the answer

    ans = doc["ablation"][-1]
    doc["answer"] = {
        "frame": ans["frame"], "px_per_m": ans["ppm"],
        "mm_per_px": ans["mm_per_px"], "depth_m": ans["depth_m"],
        "lens_mm": ans["lens_mm"],
        "gate_dist_35mm_equiv_m": ans["gate_dist_35mm_equiv_m"],
        "bay_diag_px": ans["bay_on_screen"]["diag_px"],
        "n_sharp_unocc_points": ans["n_pts"]}

    div = campath_divergence(livecam, os.path.join(R2, SP_CAMERA_FOR_CONTROL))
    for f in sorted({row["sharp_frame"], ans["frame"]}):
        pf = div["per_frame"][f - 1]
        doc.setdefault("camera_divergence_at", {})[str(f)] = pf
        print(">> camera A/B at f%d: %.6f m, %.6f mm, %.6f deg"
              % (pf["f"], pf["dpos_m"], pf["dlens_mm"], pf["dang_deg"]))
    doc["camera_divergence_overall"] = {
        k: div[k] for k in ("n", "n_differ", "worst_pos_m", "worst_pos_f",
                            "worst_lens_mm", "worst_lens_f",
                            "worst_ang_deg", "worst_ang_f")}
    print(">> overall %d of %d frames differ between the two cameras"
          % (div["n_differ"], div["n"]))

    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        json.dump(doc, open(a.out, "w"), indent=1)
        print(">> wrote %s" % a.out)
    return gate_exit.verdict("R2990_FRAMING_OK", " reading taken")


if __name__ == "__main__":
    gate_exit.guard(main)
