#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
r2731_pont_camera_apply.py — BAKE THE R2-738 CANDIDATE CAMERA, AND PROVE THE
RE-AIM BEFORE USING IT.

    python3 tools/r2731_pont_camera_apply.py --selftest
    python3 tools/r2731_pont_camera_apply.py --out work/r2731/cam_candidate_path.json
    blender -b film16_breach.blend -P tools/r2731_pont_camera_apply.py -- --apply \
        --render-frames 2174,2180,2186,2190,2195,2200 --out-dir out/

WHAT IT DOES
------------
Moves the camera through the bridge's clear opening over f2145-2222 (R2-738) and
RE-AIMS it so the car stays where it was in frame.

THE RE-AIM IS THE PART THAT NEEDS PROVING.  Moving the camera 21 m without
turning it would throw the car out of frame, and the numbers in R2-738 are
occlusion numbers, which do not depend on rotation at all.  So the aim is
reconstructed here — look at the car's box centre, image-up pulled toward world
+Z — and `--selftest` checks that reconstruction against the SHIPPED path first:
re-aim the UNMOVED camera the same way and the car must project to the same
screen position the shipped quaternion puts it at.  If that fails, the aim model
is wrong and the moved camera cannot be trusted either.

That control is the whole reason this is a separate tool from
`r2731_pont_camera_candidate.py`, which only writes beat-sheet keys and lets the
rig do the aiming.  This one has to do the aiming itself, so it has to earn it.
"""

import argparse
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "world"))
import world_contract as WC                                     # noqa: E402

PONT_S = 2410.0
DU, U_WIN = 20.0, (2145.0, 2165.0, 2178.0, 2200.0)
DZ, Z_WIN = -7.5, (2145.0, 2166.0, 2190.0, 2222.0)
W, H, SENSOR = 3840, 2160, 36.0
CAR_LEN, CAR_W, CAR_BOT_Z, CAR_TOP_Z = 5.698, 2.005, 0.020, 0.992


def smoother(t):
    t = max(0.0, min(1.0, t))
    return t * t * t * (t * (t * 6 - 15) + 10)


def win(f, w):
    f0, f1, f2, f3 = w
    if f <= f0 or f >= f3:
        return 0.0
    if f < f1:
        return smoother((f - f0) / (f1 - f0))
    if f <= f2:
        return 1.0
    return smoother((f3 - f) / (f3 - f2))


def offset_at(f):
    _x, _y, _z, hdg, _k = WC.centreline(PONT_S)
    lat = (-math.sin(hdg), math.cos(hdg), 0.0)
    wu, wz = DU * win(f, U_WIN), DZ * win(f, Z_WIN)
    return (wu * lat[0], wu * lat[1], wz)


# ---- minimal vector / quaternion helpers, so this runs with or without bpy ---
def sub(a, b):
    return [a[i] - b[i] for i in range(3)]


def norm(a):
    n = math.sqrt(sum(v * v for v in a))
    return [v / n for v in a] if n > 1e-12 else [0.0, 0.0, 0.0]


def cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0]]


def dot(a, b):
    return sum(a[i] * b[i] for i in range(3))


def mat_to_quat(x, y, z):
    """Columns of the rotation matrix -> (w, x, y, z), Blender's order."""
    m = [[x[0], y[0], z[0]], [x[1], y[1], z[1]], [x[2], y[2], z[2]]]
    tr = m[0][0] + m[1][1] + m[2][2]
    if tr > 0:
        s = math.sqrt(tr + 1.0) * 2
        return [0.25 * s, (m[2][1] - m[1][2]) / s,
                (m[0][2] - m[2][0]) / s, (m[1][0] - m[0][1]) / s]
    if m[0][0] > m[1][1] and m[0][0] > m[2][2]:
        s = math.sqrt(1.0 + m[0][0] - m[1][1] - m[2][2]) * 2
        return [(m[2][1] - m[1][2]) / s, 0.25 * s,
                (m[0][1] + m[1][0]) / s, (m[0][2] + m[2][0]) / s]
    if m[1][1] > m[2][2]:
        s = math.sqrt(1.0 + m[1][1] - m[0][0] - m[2][2]) * 2
        return [(m[0][2] - m[2][0]) / s, (m[0][1] + m[1][0]) / s,
                0.25 * s, (m[1][2] + m[2][1]) / s]
    s = math.sqrt(1.0 + m[2][2] - m[0][0] - m[1][1]) * 2
    return [(m[1][0] - m[0][1]) / s, (m[0][2] + m[2][0]) / s,
            (m[1][2] + m[2][1]) / s, 0.25 * s]


def look_quat(eye, target, up_ref=(0.0, 0.0, 1.0)):
    """Blender camera looking at `target`: -Z forward, +Y image up."""
    zc = norm(sub(eye, target))                 # +Z is BACK along the view
    xc = norm(cross(up_ref, zc))
    if max(abs(v) for v in xc) < 1e-9:          # looking straight up/down
        xc = norm(cross((0.0, 1.0, 0.0), zc))
    yc = cross(zc, xc)
    return mat_to_quat(xc, yc, zc)


def qrot(q, v):
    w, x, y, z = q
    t = [2 * (y * v[2] - z * v[1]), 2 * (z * v[0] - x * v[2]),
         2 * (x * v[1] - y * v[0])]
    return [v[0] + w * t[0] + (y * t[2] - z * t[1]),
            v[1] + w * t[1] + (z * t[0] - x * t[2]),
            v[2] + w * t[2] + (x * t[1] - y * t[0])]


def project(p, q, lens, pt):
    fwd, up, right = qrot(q, [0, 0, -1]), qrot(q, [0, 1, 0]), qrot(q, [1, 0, 0])
    d = sub(pt, p)
    zc = dot(d, fwd)
    if zc <= 1e-6:
        return None, None
    fpx = (lens / SENSOR) * W
    return (dot(d, right) / zc * fpx + W * 0.5,
            -dot(d, up) / zc * fpx + H * 0.5)


def car_axes(rot):
    rx, ry, rz = rot
    cy, sy = math.cos(rz), math.sin(rz)
    cp, sp = math.cos(ry), math.sin(ry)
    cr, sr = math.cos(rx), math.sin(rx)
    return ((cy * cp, sy * cp, -sp),
            (cy * sp * sr - sy * cr, sy * sp * sr + cy * cr, cp * sr),
            (cy * sp * cr + sy * sr, sy * sp * cr - cy * sr, cp * cr))


def car_centre(rec):
    ax, ay, az = car_axes(rec["rot"])
    o = rec["loc"]
    lz = 0.5 * (CAR_BOT_Z + CAR_TOP_Z)
    return [o[i] + az[i] * lz for i in range(3)]


def poses():
    cam = {int(e["f"]): e for e in json.load(open(
        os.path.join(ROOT, "world", "camera_rig_path.json")))["path"]}
    car = {int(e["f"]): e for e in json.load(open(
        os.path.join(ROOT, "world", "car_anim_measured.json")))["frames"]}
    return cam, car


def candidate_path():
    cam, car = poses()
    out = []
    for f in sorted(cam):
        e = cam[f]
        d = offset_at(f)
        p = [e["p"][i] + d[i] for i in range(3)]
        q = e["q"]
        if max(abs(v) for v in d) > 1e-9 and f in car:
            q = look_quat(p, car_centre(car[f]))
        out.append(dict(f=f, p=[round(v, 5) for v in p],
                        q=[round(v, 7) for v in q], lens=e["lens"]))
    return out


def selftest():
    ok = True

    def chk(nm, cond, detail=""):
        nonlocal ok
        print("   %-52s %s  %s" % (nm, "PASS" if cond else "FAIL", detail))
        ok = ok and bool(cond)

    cam, car = poses()
    # CONTROL 1: the aim model must reproduce the SHIPPED framing on the
    # UNMOVED camera.  If it cannot, it may not be used on the moved one.
    worst, wf = 0.0, None
    for f in range(2140, 2231):
        if f not in car:
            continue
        c = car_centre(car[f])
        qa = look_quat(cam[f]["p"], c)
        xa, ya = project(cam[f]["p"], qa, cam[f]["lens"], c)
        xb, yb = project(cam[f]["p"], cam[f]["q"], cam[f]["lens"], c)
        d = math.hypot(xa - xb, ya - yb)
        if d > worst:
            worst, wf = d, f
    chk("re-aim reproduces the shipped framing (unmoved)",
        worst < 60.0, "worst %.1f px of 3840 at f%s" % (worst, wf))

    # CONTROL 2: the candidate must put the car at the SAME screen place
    path = {int(e["f"]): e for e in candidate_path()}
    worst2, wf2 = 0.0, None
    for f in range(2140, 2231):
        if f not in car:
            continue
        c = car_centre(car[f])
        xa, ya = project(path[f]["p"], path[f]["q"], path[f]["lens"], c)
        xb, yb = project(cam[f]["p"], cam[f]["q"], cam[f]["lens"], c)
        d = math.hypot(xa - xb, ya - yb)
        if d > worst2:
            worst2, wf2 = d, f
    chk("candidate holds the car in the same screen place",
        worst2 < 60.0, "worst %.1f px at f%s" % (worst2, wf2))

    # CONTROL 3: outside the window nothing moves at all
    chk("frames outside the window are bit-identical",
        all(path[f]["p"] == [round(v, 5) for v in cam[f]["p"]]
            and path[f]["q"] == [round(v, 7) for v in cam[f]["q"]]
            for f in cam if f <= U_WIN[0] or f >= Z_WIN[3]))
    chk("the lens is never touched",
        all(path[f]["lens"] == cam[f]["lens"] for f in cam))
    # CONTROL 4: quaternions stay unit and step smoothly
    step = max(max(abs(path[f + 1]["q"][i] - path[f]["q"][i]) for i in range(4))
               for f in range(2100, 2260))
    base = max(max(abs(cam[f + 1]["q"][i] - cam[f]["q"][i]) for i in range(4))
               for f in range(2100, 2260))
    chk("rotation step stays in the shipped envelope", step < 4 * base + 0.02,
        "candidate %.5f/frame against shipped %.5f" % (step, base))
    print(">> STAGE RESULT: %s"
          % ("PONT_CAM_APPLY_SELFTEST_OK" if ok else "PONT_CAM_APPLY_SELFTEST_FAIL"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--apply", action="store_true",
                    help="inside Blender: key the candidate onto the ONER camera")
    ap.add_argument("--camera", default="ONER")
    ap.add_argument("--out", default="work/r2731/cam_candidate_path.json")
    a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:]
                      if "--" in sys.argv else None)
    if a.selftest:
        sys.exit(0 if selftest() else 1)
    path = candidate_path()
    if a.apply:
        import bpy
        ob = bpy.data.objects.get(a.camera)
        if ob is None:
            print(">> STAGE RESULT: PONT_CAM_APPLY_NO_CAMERA")
            return
        ob.rotation_mode = 'QUATERNION'
        lo, hi = int(U_WIN[0]) - 2, int(Z_WIN[3]) + 2
        n = 0
        for e in path:
            f = int(e["f"])
            if not (lo <= f <= hi):
                continue
            ob.location = e["p"]
            ob.rotation_quaternion = e["q"]
            ob.keyframe_insert("location", frame=f)
            ob.keyframe_insert("rotation_quaternion", frame=f)
            n += 1
        print(">> keyed %d frames on %s (f%d-%d)" % (n, a.camera, lo, hi))
        print(">> STAGE RESULT: PONT_CAM_APPLIED")
        return
    out = os.path.join(ROOT, a.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as fh:
        json.dump(dict(frames=len(path), path=path,
                       note="R2-738 candidate: camera through the bridge's clear "
                            "opening, f2145-2222, re-aimed on the car."), fh)
    print(">> wrote %s (%d frames)" % (a.out, len(path)))
    print(">> STAGE RESULT: PONT_CAM_PATH_WRITTEN")


if __name__ == "__main__":
    main()
