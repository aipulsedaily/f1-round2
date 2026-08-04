"""Project the east wall's bays into the ONER frame, from the dumped track.

Pure numpy, no bpy.  Blender camera convention: -Z forward, +Y up, +X right,
sensor 36 mm AUTO fit on 3840x2160 (so the horizontal axis is the fit axis).
"""
import json
import sys

import numpy as np

TRACK = "/home/zany/f1-round2/sim/out/oner_camera_track_film14_breach.json"
SENSOR = 36.0
RES = (3840, 2160)


def quat_to_mat(q):
    w, x, y, z = q
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def load(track=TRACK):
    rows = json.load(open(track))
    return {int(r[0]): r for r in rows}


def project(frame, P, track=None, res=RES, sensor=SENSOR):
    """P: (n,3) world points -> (n,2) pixel coords, origin TOP-LEFT, and z_cam."""
    tr = track or load()
    r = tr[frame]
    C = np.array(r[1:4], float)
    R = quat_to_mat(r[4:8])
    lens = float(r[8])
    D = (np.asarray(P, float) - C) @ R          # world -> camera
    # camera looks down -Z
    zc = -D[:, 2]
    fpx = lens / sensor * res[0]                # AUTO fit: width is the fit axis
    u = res[0] * 0.5 + D[:, 0] / zc * fpx
    v = res[1] * 0.5 - D[:, 1] / zc * fpx
    return np.stack([u, v], 1), zc, dict(C=C, lens=lens, fpx=fpx)


def rect_px(frame, y0, y1, z0, z1, x=15.0, track=None):
    P = np.array([[x, y, z] for y in (y0, y1) for z in (z0, z1)])
    uv, zc, meta = project(frame, P, track)
    return dict(u=[float(uv[:, 0].min()), float(uv[:, 0].max())],
                v=[float(uv[:, 1].min()), float(uv[:, 1].max())],
                w_px=float(uv[:, 0].max() - uv[:, 0].min()),
                h_px=float(uv[:, 1].max() - uv[:, 1].min()),
                range_m=float(zc.mean()), lens=meta["lens"])


# The wall, as the fracture plan cuts it.  Bay i spans mullion i .. i+1.
BAY_Y = [(-11.0 + 2.2 * i + 0.0375, -11.0 + 2.2 * (i + 1) - 0.0375)
         for i in range(10)]
HOLE = dict(name="HOLE_connected", y=(-2.185, -0.035), z=(0.0875, 6.0875))
HOLE_BR = dict(name="HOLE_bridged", y=(-2.185, 2.165), z=(0.0875, 6.0875))
NB_L = dict(name="NB_left_bay3", y=(-4.3625, -2.2375), z=(0.11, 6.09))
NB_R = dict(name="NB_right_bay6", y=(2.2375, 4.3625), z=(0.11, 6.09))


def border_for(frame, y, z, pad=1.6, track=None):
    """Normalised --border (MINX MAXX MINY MAXY, origin BOTTOM-left) around a
    wall rectangle, padded, square-ish."""
    r = rect_px(frame, y[0], y[1], z[0], z[1], track=track)
    cu = 0.5 * (r["u"][0] + r["u"][1])
    cv = 0.5 * (r["v"][0] + r["v"][1])
    half = 0.5 * max(r["w_px"], r["h_px"]) * pad
    halfu, halfv = half, half
    u0, u1 = cu - halfu, cu + halfu
    v0, v1 = cv - halfv, cv + halfv
    return (max(0.0, u0 / RES[0]), min(1.0, u1 / RES[0]),
            max(0.0, 1.0 - v1 / RES[1]), min(1.0, 1.0 - v0 / RES[1])), r


if __name__ == "__main__":
    tr = load()
    for f in (2901, 2940, 2978):
        print("=== frame %d ===" % f)
        for reg in (HOLE, HOLE_BR, NB_L, NB_R):
            r = rect_px(f, reg["y"][0], reg["y"][1], reg["z"][0], reg["z"][1],
                        track=tr)
            print("  %-16s u %8.1f..%8.1f  v %8.1f..%8.1f  %6.1f x %6.1f px  "
                  "range %6.1f m  lens %.1f"
                  % (reg["name"], r["u"][0], r["u"][1], r["v"][0], r["v"][1],
                     r["w_px"], r["h_px"], r["range_m"], r["lens"]))
        b, r = border_for(f, HOLE_BR["y"], HOLE_BR["z"], track=tr)
        print("  border(bridged, pad1.6) = %.5f %.5f %.5f %.5f"
              % b)
        # px per metre, vertical
        print("  px/m vertical = %.3f   px/m horizontal = %.3f"
              % (r["h_px"] / 6.0, r["w_px"] / 4.35))
