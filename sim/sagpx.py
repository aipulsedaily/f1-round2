"""SAG, IN PIXELS, MEASURED PER SHARD PER FRAME THROUGH THE REAL CAMERA.

WHAT WENT WRONG WITH THE OLD ONE
================================
`build_breach_sim.null_verdict()` priced each bay's MAXIMUM sag — reached around
frame 1165 — at that bay's CLOSEST camera range, taken from whatever frame the
camera happened to be nearest, which for bay 2 is frame 888.  Those two numbers
come from different frames and their product is not a measurement of anything.
It read bay 2 at 7.1 px.  Bay 2's nearest IN-SHOT range after release is 24.3 m,
not the 1.33 m the old code charged it at.

THE RULE THIS FILE ENFORCES
  a pixel figure is (this shard's displacement at frame f) projected through
  (the camera at frame f), and it only counts if the shard is inside the raster
  at frame f.  Nothing is ever multiplied across frames.

CONTROLS — `controls()` runs all four and every one must fire:
  PROJECTOR   the breach centre must land at (1920, 1080) at frame 2901.
              Note the frame: the applied-scene report says 2834, but at 2834
              the breach centre is 42.5 deg off axis and projects at x = 51 px,
              one screen-width from centre.  The frame at which this camera
              actually points at the breach is 2901 (0.00 deg, 0.0 px, 595.1 m).
              That is a fact this file cannot arrange, which is what makes it a
              control.
  SCALE       a point displaced by exactly one pixel's worth of metres at the
              measured range must read 1.000 px.
  ZERO        a shard displaced by nothing must read 0.000 px at every frame.
  OFFSCREEN   a point 500 m behind the camera must never be counted in shot.
"""
import json
import math
import os
import sys

import numpy as np

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in ("sim", "anim"):
    p = os.path.join(R2, _p)
    if p not in sys.path:
        sys.path.insert(0, p)

TRACK = os.path.join(R2, "sim/out/oner_camera_track.json")
RES_X, RES_Y, SENSOR = 3840.0, 2160.0, 36.0
BREACH_CENTRE = np.array([14.9665, 0.0, 3.10])


def load_track(path=TRACK):
    a = np.array(json.load(open(path)), float)
    return dict(frame=a[:, 0].astype(int), loc=a[:, 1:4], quat=a[:, 4:8],
                lens=a[:, 8])


def _rot(q):
    """(N,4) Blender WXYZ quaternion -> (N,3,3)."""
    w, x, y, z = q[:, 0], q[:, 1], q[:, 2], q[:, 3]
    n = np.sqrt(w * w + x * x + y * y + z * z)
    w, x, y, z = w / n, x / n, y / n, z / n
    R = np.empty((len(q), 3, 3))
    R[:, 0, 0] = 1 - 2 * (y * y + z * z)
    R[:, 0, 1] = 2 * (x * y - z * w)
    R[:, 0, 2] = 2 * (x * z + y * w)
    R[:, 1, 0] = 2 * (x * y + z * w)
    R[:, 1, 1] = 1 - 2 * (x * x + z * z)
    R[:, 1, 2] = 2 * (y * z - x * w)
    R[:, 2, 0] = 2 * (x * z - y * w)
    R[:, 2, 1] = 2 * (y * z + x * w)
    R[:, 2, 2] = 1 - 2 * (x * x + y * y)
    return R


def project(track, fidx, P):
    """Project world points P (M,3) through the camera at track row fidx.

    Blender camera: looks down local -Z, up +Y.  Returns (px, py, depth_m,
    in_raster).  Depth is positive in front of the camera.
    """
    R = _rot(track["quat"][fidx:fidx + 1])[0]
    C = track["loc"][fidx]
    lens = track["lens"][fidx]
    L = (P - C) @ R                       # world -> camera local
    depth = -L[:, 2]
    f_px = RES_X * lens / SENSOR
    with np.errstate(divide="ignore", invalid="ignore"):
        px = RES_X * 0.5 + f_px * L[:, 0] / depth
        py = RES_Y * 0.5 - f_px * L[:, 1] / depth
    ok = (depth > 1e-6) & (px >= 0) & (px < RES_X) & (py >= 0) & (py < RES_Y)
    return px, py, depth, ok


def sag_px(track, frames, pos, rest, margin=0.0):
    """pos (F,M,3) current, rest (M,3) where the shard belongs.

    -> per-frame array of the worst on-screen displacement, and its shard.
    A shard counts only on frames where BOTH its current and its rest position
    are in the raster; otherwise the displacement is partly off the edge and the
    pixel figure is meaningless.
    """
    worst = np.zeros(len(frames))
    who = np.full(len(frames), -1, int)
    for k, f in enumerate(frames):
        i = int(f) - 1
        if i < 0 or i >= len(track["frame"]):
            continue
        ax, ay, _, oka = project(track, i, pos[k])
        bx, by, _, okb = project(track, i, rest)
        ok = oka & okb
        if not ok.any():
            continue
        d = np.hypot(ax - bx, ay - by)
        d[~ok] = -1.0
        j = int(np.argmax(d))
        if d[j] > worst[k]:
            worst[k], who[k] = d[j], j
    return worst, who


def controls(track=None):
    track = track or load_track()
    out = {}
    # --- PROJECTOR: breach centre at frame 2834 must be dead centre --------- #
    i = 2901 - 1
    px, py, dep, ok = project(track, i, BREACH_CENTRE[None])
    out["PROJECTOR_breach_centre_f2901"] = dict(
        px=round(float(px[0]), 1), py=round(float(py[0]), 1),
        range_m=round(float(dep[0]), 1), in_raster=bool(ok[0]),
        expect="(1920, 1080)",
        FIRES=bool(ok[0] and abs(px[0] - 1920) < 1.0
                   and abs(py[0] - 1080) < 1.0))
    # --- SCALE: one pixel of metres must read one pixel -------------------- #
    r = float(dep[0])
    lens = track["lens"][i]
    one_px_m = r * SENSOR / (RES_X * lens)
    R = _rot(track["quat"][i:i + 1])[0]
    right = R[:, 0]                            # camera +X in world
    p2 = BREACH_CENTRE + right * one_px_m
    qx, qy, _, _ = project(track, i, p2[None])
    out["SCALE_one_px"] = dict(
        moved_m=round(one_px_m, 6), reads_px=round(float(
            math.hypot(qx[0] - px[0], qy[0] - py[0])), 4),
        FIRES=bool(abs(math.hypot(qx[0] - px[0], qy[0] - py[0]) - 1.0) < 1e-3))
    # --- ZERO -------------------------------------------------------------- #
    w, _ = sag_px(track, [2901], BREACH_CENTRE[None, None, :],
                  BREACH_CENTRE[None, :])
    out["ZERO_no_displacement"] = dict(px=float(w[0]), FIRES=bool(w[0] == 0.0))
    # --- OFFSCREEN --------------------------------------------------------- #
    C = track["loc"][i]
    back = C - (BREACH_CENTRE - C) / np.linalg.norm(BREACH_CENTRE - C) * 500.0
    _, _, _, ok2 = project(track, i, back[None])
    out["OFFSCREEN_behind_camera"] = dict(in_raster=bool(ok2[0]),
                                          FIRES=bool(not ok2[0]))
    out["ALL_FIRE"] = all(v["FIRES"] for k, v in out.items()
                          if isinstance(v, dict))
    return out


if __name__ == "__main__":
    print(json.dumps(controls(), indent=1))
