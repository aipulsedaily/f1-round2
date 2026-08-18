#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
r2731_pont_camera_candidate.py — PUT THE CAMERA UNDER THE BRIDGE, WHERE THE
CIRCUIT SPEC ALREADY SAYS IT GOES.

    python3 tools/r2731_pont_camera_candidate.py --selftest
    python3 tools/r2731_pont_camera_candidate.py \
        --out docs/beat_sheet_R2731_PONT_CAMERA_CANDIDATE.json

*** SUPERSEDED.  DO NOT RUN THIS AGAINST THE CURRENT SHEET.  R2-1701. ***
`docs/beat_sheet.json` already carries this displacement: `tools/author_beats2_5.py`
applies it as `pont_offset()` inside `emit_keys`' sampler, so it is regenerated
from source rather than patched in afterwards.  Running this on today's sheet
DOUBLE-APPLIES it — 40 m inboard and 15 m down, through the parapet — and the
selftest below cannot see that, because it only checks that a bounded number of
keys moved by no more than one offset length.  It also used the WRONG RAMPS: the
22-frame lateral out-ramp below costs 91.2 m/s^2 (9.29 g), and R2-1004 widened
it to 32 frames for 47.7.  Kept as the record of where the displacement came
from, not as a tool to run.

WHAT IT DOES
------------
Rewrites the `world` position of beat 5's camera keys inside the bridge window
by a windowed offset in the bridge's own (lateral, vertical) frame.  It touches
`world` only: **no `look_at` is changed**, so `anim/build_camera_rig.py` re-aims
on the same targets and the car stays where it was in frame.

WHY
---
R2-738.  `docs/circuit_spec.md` §10 says the camera "threads under it at ~5 m
altitude".  As built it crosses the bridge plane at f2174 at u = -29.27 m and
11.89 m over the road — 5.1 m ABOVE the soffit and 29 m outboard of the
centreline, neither under the bridge nor over the track.  That is why the car is
wholly hidden for f2180-2191.

`tools/r2731_pont_full_sightline.py` — validated against two independent
raycasts — says a rigid translation of the camera cannot clear the pass (floor
3 frames, because the abutment's top IS the soffit and a descending ray cannot
be above it outboard and below it inboard).  Sending the camera through the
clear opening does, on a 6 m x 5 m plateau of exactly zero blocked frames.

THE OFFSET
----------
Two independent smootherstep windows, one per axis, so the camera comes back
outboard before it is at its lowest rather than flying low over the racing
surface.  Smootherstep has zero first AND second derivative at both ends, so the
correction is C2 in frame and cannot introduce a step or a kink.

    lateral   +20.0 m inboard,  window f2145 -> 2165 .. 2178 -> 2200
    vertical   -7.5 m,          window f2145 -> 2166 .. 2190 -> 2222

Both are interior to the plateau (du 18-24, dz -6..-11).

WHAT THIS IS NOT
----------------
It is not a commit.  It writes a CANDIDATE sheet beside the real one.  21 m of
deviation over ~60 frames changes what the shot looks like and not only what it
can see, and that wants eyes on rendered frames.  The authoritative continuity
check is a rig rebuild plus `world/camera_rig_continuity.json`, which this does
not run.
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
FPS = 24.0
DU, U_WIN = 20.0, (2145.0, 2165.0, 2178.0, 2200.0)
DZ, Z_WIN = -7.5, (2145.0, 2166.0, 2190.0, 2222.0)


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


def basis():
    _x, _y, _z, hdg, _k = WC.centreline(PONT_S)
    lat = (-math.sin(hdg), math.cos(hdg), 0.0)
    return lat, (0.0, 0.0, 1.0)


def offset_at(f):
    lat, up = basis()
    wu, wz = DU * win(f, U_WIN), DZ * win(f, Z_WIN)
    return tuple(wu * lat[i] + wz * up[i] for i in range(3))


def apply(sheet):
    n = 0
    touched = []
    for k in sheet["beat5"]["camera_keys"]:
        f = k["t"] * FPS
        d = offset_at(f)
        if max(abs(v) for v in d) < 1e-9:
            continue
        k["world"] = [round(k["world"][i] + d[i], 4) for i in range(3)]
        n += 1
        touched.append(round(f, 1))
    return n, touched


def selftest():
    ok = True

    def chk(nm, cond, detail=""):
        nonlocal ok
        print("   %-46s %s  %s" % (nm, "PASS" if cond else "FAIL", detail))
        ok = ok and bool(cond)

    chk("window is 0 outside and 1 on the plateau",
        win(2100, U_WIN) == 0.0 and win(2170, U_WIN) == 1.0
        and win(2300, U_WIN) == 0.0)
    # C1/C2 at the ends: finite differences of the window must vanish
    for w, nm in ((U_WIN, "u"), (Z_WIN, "z")):
        h = 1e-3
        d1a = (win(w[0] + h, w) - win(w[0], w)) / h
        d1b = (win(w[3], w) - win(w[3] - h, w)) / h
        chk("%s window has zero slope at both ends" % nm,
            abs(d1a) < 1e-4 and abs(d1b) < 1e-4,
            "%.2e / %.2e" % (d1a, d1b))
    sheet = json.load(open(os.path.join(ROOT, "docs", "beat_sheet.json")))
    before = [list(k["world"]) for k in sheet["beat5"]["camera_keys"]]
    look_before = [list(k["look_at"]) for k in sheet["beat5"]["camera_keys"]]
    n, touched = apply(sheet)
    look_after = [list(k["look_at"]) for k in sheet["beat5"]["camera_keys"]]
    chk("look_at is never touched", look_before == look_after)
    chk("a bounded number of keys move", 4 <= n <= 20, "%d keys: %s" % (n, touched))
    moved = max(math.dist(before[i], sheet["beat5"]["camera_keys"][i]["world"])
                for i in range(len(before)))
    chk("no key moves more than the offset's own length",
        moved <= math.hypot(DU, DZ) + 1e-6, "worst %.3f m" % moved)
    chk("keys outside the window are bit-identical",
        all(before[i] == sheet["beat5"]["camera_keys"][i]["world"]
            for i, k in enumerate(sheet["beat5"]["camera_keys"])
            if k["t"] * FPS <= U_WIN[0] or k["t"] * FPS >= Z_WIN[3]))
    print(">> STAGE RESULT: %s"
          % ("PONT_CAM_SELFTEST_OK" if ok else "PONT_CAM_SELFTEST_FAIL"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--out", default="docs/beat_sheet_R2731_PONT_CAMERA_CANDIDATE.json")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(0 if selftest() else 1)
    path = os.path.join(ROOT, "docs", "beat_sheet.json")
    sheet = json.load(open(path))
    n, touched = apply(sheet)
    sheet.setdefault("r2731_pont_camera", {}).update(dict(
        why="R2-738. circuit_spec.md 10 says the camera 'threads under it at "
            "~5 m altitude'; as built it crosses the bridge plane at f2174 at "
            "u=-29.27 m and 11.89 m over the road, 5.1 m ABOVE the soffit and "
            "29 m outboard. That is why the car is wholly hidden f2180-2191. "
            "This candidate sends it through the clear opening instead: "
            "u=-9.27 m, 4.39 m over the road, 2.4 m under the soffit.",
        offset_lateral_m=DU, lateral_window=list(U_WIN),
        offset_vertical_m=DZ, vertical_window=list(Z_WIN),
        keys_moved=n, frames_moved=touched,
        look_at_touched=False,
        blocked_frames_before=11, blocked_frames_after=0,
        plateau="du 18..24 m x dz -6..-11 m, all zero",
        status="CANDIDATE. Not a commit. Needs rendered frames and a rig "
               "rebuild + camera_rig_continuity gate."))
    out = os.path.join(ROOT, a.out)
    with open(out, "w") as fh:
        json.dump(sheet, fh, indent=1)
    print(">> moved %d beat-5 camera keys at frames %s" % (n, touched))
    print(">> wrote %s" % a.out)
    print(">> STAGE RESULT: PONT_CAM_CANDIDATE_WRITTEN")


if __name__ == "__main__":
    main()
