#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
r2731_pont_full_sightline.py — THE PONT, INCLUDING ITS ABUTMENTS.

    python3 tools/r2731_pont_full_sightline.py --selftest
    python3 tools/r2731_pont_full_sightline.py --station 2460 --frames 2150-2260
    python3 tools/r2731_pont_full_sightline.py --sweep

WHY THIS EXISTS, AND IT IS NOT A NICER VERSION OF `r2651_pont_sightline.py`
--------------------------------------------------------------------------
`r2651_pont_sightline.py` reconstructs Le Pont de la Plongee as FOUR HORIZONTAL
BANDS — girders, deck slab, parapet, mesh screen — spanning lateral u = -15..+15
from the soffit up.  That is the superstructure, and its own docstring says so.

`build_architecture.py` also builds, on each side:

    an ABUTMENT      x +-4.2, |u| 12.8 .. 18.0, z (zr - 6.0) .. soffit
    a precast pad    x +-5.0, |u| 12.0 .. 19.0, z (zr - 6.0) .. (ground + 0.10)
    five WING WALL steps, out to |u| = 26.6, z (zr - 4.0) .. soffit

The abutment alone is a 12.8 m tall, 5.2 m deep block of concrete on each side.
**A sightline that passes outboard of the span and below the deck is blocked by
it, and the four-band model cannot see that at all.**

This matters because R2-660 chose `PONT_S = 2460` by sweeping the station with
the four-band model, which reported zero blocked frames from 2460 to 2610.  The
depth-tested raycast against the built world at 2460 reports **f2196 and
f2203-2230 blocked, 25 frames** — worse than the 12 the move was made to close —
and the occluder is 32-66 m from the lens, i.e. the abutment, not the deck.
Same failure shape as R2-664's own v1: a model that omits the thing that
actually blocks returns a confident zero.

VALIDATION, and it is the whole reason this tool may be trusted
---------------------------------------------------------------
`--selftest` reproduces BOTH raycast runs, at two different stations, from the
same code:

    s = 2410   ->  must block f2181-2191 and clear f2170-2179, f2194-2200
    s = 2460   ->  must block f2204-2227 and clear f2180-2193

Two independent ground truths taken from
`render/r2651/occlusion.json` (station 2410) and
`render/r2731/occ_STALE_s2460_firstannexe.json` (station 2460, kept precisely so
this control can keep running).  An instrument that reproduces
one of them could be right by luck; one that reproduces a defect it did not
predict, at a station chosen by someone else, is doing geometry.

WHAT IT STILL DOES NOT MODEL
----------------------------
The cross-bracing (r = 0.05 m), parapet posts (r = 0.04 m) and the deck's own
15-per-girder web stiffeners are cylinders and thin plates; they are inside the
solid bands' envelope in z and cannot extend a window.  `DR_BridgeBanners` is
build_dressing's and is checked separately, against the world, not here.
Bevels (0.010) only shrink a box.
"""

import argparse
import json
import math
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "world"))

import world_contract as WC                                    # noqa: E402

HALF = 15.0
DW = 6.0
SOFFIT_OVER_ROAD = 6.80
EMBED = WC.BASE_EMBED_M

# --- the car's 58 sample points, IDENTICAL to r2651_occlusion_sweep.py -------
# Copied deliberately rather than reimplemented: a cheap prediction that samples
# the subject differently from the authority it is predicting is not comparable
# to it, and the first draft of this tool (an 18-point grid lifted by a ride
# height the sweep records but does not use) missed the true window by 4 frames.
CAR_LEN, CAR_W = 5.698, 2.005
CAR_BOT_Z, CAR_TOP_Z = 0.020, 0.992
_FACE_UV = [(a, b) for a in (0.1, 0.5, 0.9) for b in (0.1, 0.5, 0.9)]


def car_axes(rot):
    """Blender 'XYZ' euler -> (+X forward, +Y left, +Z up), the sweep's own."""
    rx, ry, rz = rot
    cy, sy = math.cos(rz), math.sin(rz)
    cp, sp = math.cos(ry), math.sin(ry)
    cr, sr = math.cos(rx), math.sin(rx)
    return ((cy * cp, sy * cp, -sp),
            (cy * sp * sr - sy * cr, sy * sp * sr + cy * cr, cp * sr),
            (cy * sp * cr + sy * sr, sy * sp * cr - cy * sr, cp * cr))


def car_samples(rec):
    """54 hull points + the 4 measured wheel points = 58, in world."""
    ax, ay, az = car_axes(rec["rot"])
    o = rec["loc"]
    hx, hy = CAR_LEN * 0.5, CAR_W * 0.5
    lo, hi = CAR_BOT_Z, CAR_TOP_Z
    out = []
    for axis, sgn in ((0, +1), (0, -1), (1, +1), (1, -1), (2, +1), (2, -1)):
        for u, v in _FACE_UV:
            if axis == 0:
                lx, ly, lz = sgn * hx, -hy + 2 * hy * u, lo + (hi - lo) * v
            elif axis == 1:
                lx, ly, lz = -hx + 2 * hx * u, sgn * hy, lo + (hi - lo) * v
            else:
                lx, ly = -hx + 2 * hx * u, -hy + 2 * hy * v
                lz = hi if sgn > 0 else lo
            out.append(tuple(o[i] + ax[i] * lx + ay[i] * ly + az[i] * lz
                             for i in range(3)))
    for c in ("FL", "FR", "RL", "RR"):
        if c in rec.get("contacts", {}):
            out.append(tuple(rec["contacts"][c]))
    return out

# `A_MeshDark` / `A_MeshScreen` are see-through in the delivered frame and
# opaque to a BVH.  They are kept in their own channel and NEVER pooled with
# concrete, exactly as r2651_occlusion_sweep.py does it.
FENCE = ("mesh_screen",)


def bridge_boxes(s, soffit_over_road=None, open_parapet=False):
    """Every box `build_bridges` puts in ARCH_PontPlongee, in the bridge's own
    local frame (x along the racing direction, y = LEFT of travel, z = world z),
    as (name, channel, (x0,y0,z0), (x1,y1,z1))."""
    zr = float(WC.elevation_c(s))
    soff = zr + (SOFFIT_OVER_ROAD if soffit_over_road is None
                 else soffit_over_road)
    B = []

    def add(nm, ch, a, b):
        a2 = tuple(min(a[i], b[i]) for i in range(3))
        b2 = tuple(max(a[i], b[i]) for i in range(3))
        B.append((nm, ch, a2, b2))

    for sgn in (-1, 1):
        zab = float(WC.ground_z(s, sgn * HALF)) - EMBED
        add("abutment_%+d" % sgn, "solid",
            (-DW / 2 - 1.2, sgn * HALF - 2.2, zr - 6.0),
            (DW / 2 + 1.2, sgn * HALF + 3.0, soff))
        add("pad_%+d" % sgn, "solid",
            (-DW / 2 - 2.0, sgn * HALF - 3.0, zr - 6.0),
            (DW / 2 + 2.0, sgn * HALF + 4.0, zab + 0.10))
        for k in range(5):
            add("wing_%+d_%d" % (sgn, k), "solid",
                (-DW / 2 - 1.2 - k * 0.35, sgn * (HALF + 2.6 + k * 1.4),
                 zr - 4.0 + k * 0.9),
                (DW / 2 + 1.2 + k * 0.35, sgn * (HALF + 4.0 + k * 1.4),
                 soff - k * 1.1))
    for i, sx in enumerate((-DW / 2, DW / 2)):
        add("girder_%d" % i, "solid", (sx - 0.14, -HALF, soff),
            (sx + 0.14, HALF, soff + 1.35))
        for k in range(15):
            yy = -HALF + 0.9 + k * 2.0
            add("stiff_%d_%d" % (i, k), "solid", (sx - 0.30, yy, soff + 0.1),
                (sx + 0.30, yy + 0.10, soff + 1.25))
    add("deck_slab", "solid", (-DW / 2 - 0.35, -HALF, soff + 1.35),
        (DW / 2 + 0.35, HALF, soff + 1.62))
    for i, sx in enumerate((-DW / 2 - 0.3, DW / 2 + 0.3)):
        if open_parapet:
            # the concrete upstand replaced by a kerb + a full-height mesh
            # screen: the SOLID band stops at the deck slab
            add("kerb_%d" % i, "solid", (sx - 0.09, -HALF, soff + 1.62),
                (sx + 0.09, HALF, soff + 1.87))
            add("mesh_screen_%d" % i, "fence", (sx - 0.03, -HALF, soff + 1.87),
                (sx + 0.03, HALF, soff + 3.70))
        else:
            add("parapet_%d" % i, "solid", (sx - 0.09, -HALF, soff + 1.62),
                (sx + 0.09, HALF, soff + 2.72))
            add("mesh_screen_%d" % i, "fence", (sx - 0.03, -HALF, soff + 2.72),
                (sx + 0.03, HALF, soff + 3.70))
    add("wearing_course", "solid", (-DW / 2 + 0.2, -HALF - 6.0, soff + 1.55),
        (DW / 2 - 0.2, HALF + 6.0, soff + 1.63))
    return B


def to_local(s, P):
    """World -> the bridge's local frame at station s."""
    x, y, _z, hdg, _k = WC.centreline(s)
    c, sn = math.cos(hdg), math.sin(hdg)
    dx, dy = P[0] - float(x), P[1] - float(y)
    return (dx * c + dy * sn, -dx * sn + dy * c, P[2])


def seg_box(p, q, a, b):
    t0, t1 = 0.0, 1.0
    for i in range(3):
        d = q[i] - p[i]
        if abs(d) < 1e-12:
            if p[i] < a[i] or p[i] > b[i]:
                return None
            continue
        u = (a[i] - p[i]) / d
        v = (b[i] - p[i]) / d
        if u > v:
            u, v = v, u
        t0 = max(t0, u)
        t1 = min(t1, v)
        if t0 > t1:
            return None
    return (t0, t1)


_CAM = None
_CAR = None


def poses():
    global _CAM, _CAR
    if _CAM is None:
        _CAM = {int(e["f"]): e for e in json.load(open(
            os.path.join(ROOT, "world", "camera_rig_path.json")))["path"]}
        _CAR = {int(e["f"]): e for e in json.load(open(
            os.path.join(ROOT, "world", "car_anim_measured.json")))["frames"]}
    return _CAM, _CAR


def run(frames, s, verbose=False, solid_only=True, soffit=None,
        open_parapet=False):
    cam, car = poses()
    boxes = bridge_boxes(s, soffit, open_parapet)
    use = [b for b in boxes if not (solid_only and b[1] != "solid")]
    # one bounding box over the whole bridge, tested first.  A frame whose
    # sightline misses it cannot be occluded by any of its 50 parts, and most
    # frames of a 1,524-frame beat miss it.
    BB0 = tuple(min(b[2][i] for b in use) for i in range(3))
    BB1 = tuple(max(b[3][i] for b in use) for i in range(3))
    rows = []
    for f in frames:
        if f not in cam or f not in car:
            continue
        C = to_local(s, cam[f]["p"])
        pts = [to_local(s, P) for P in car_samples(car[f])]
        if not any(seg_box(C, P, BB0, BB1) for P in pts):
            rows.append(dict(f=f, n=len(pts), blocked=0, frac=0.0,
                             owner=None, dist=None))
            continue
        nb = 0
        first = None
        owners = {}
        for P in pts:
            hit = None
            for nm, ch, a, b in use:
                r = seg_box(C, P, a, b)
                if r is None:
                    continue
                seglen = math.dist(C, P)
                if r[0] * seglen < 1e-6:
                    continue
                if hit is None or r[0] < hit[0]:
                    hit = (r[0], nm, r[0] * seglen)
            if hit is not None:
                nb += 1
                owners[hit[1]] = owners.get(hit[1], 0) + 1
                if first is None or hit[0] < first[0]:
                    first = hit
        rows.append(dict(f=f, n=len(pts), blocked=nb,
                         frac=round(nb / len(pts), 4),
                         owner=(max(owners, key=owners.get) if owners else None),
                         dist=(round(first[2], 2) if first else None)))
        if verbose and nb:
            print("  f%-5d %2d/%2d  %-14s d=%6.1f m"
                  % (f, nb, len(pts), rows[-1]["owner"], rows[-1]["dist"]))
    return rows


def blocked_set(frames, s):
    return set(r["f"] for r in run(frames, s) if r["blocked"] == r["n"])


def selftest():
    ok = True

    def chk(nm, cond, detail=""):
        nonlocal ok
        print("   %-52s %s   %s" % (nm, "PASS" if cond else "FAIL", detail))
        ok = ok and bool(cond)

    win = list(range(2150, 2280))

    def truth(path, key):
        d = json.load(open(os.path.join(ROOT, path)))
        return set(r["f"] for r in d["frames"]
                   if r["in_frame"] and r["occ_frac_front"] >= 0.999
                   and r["owner"] == "ARCH_PontPlongee"
                   and r["owner_ch"] == "solid" and r["f"] in win), key

    t2410, _ = truth("render/r2651/occlusion.json", 2410)
    got = blocked_set(win, 2410.0)
    chk("s=2410 reproduces the raycast's solid-blocked set",
        got == t2410, "raycast %s..%s (%d), model %s..%s (%d)"
        % (min(t2410), max(t2410), len(t2410), min(got), max(got), len(got)))

    p2460 = os.path.join(ROOT, "render/r2731/occ_STALE_s2460_firstannexe.json")
    if os.path.exists(p2460):
        t2460, _ = truth("render/r2731/occ_STALE_s2460_firstannexe.json", 2460)
        got2 = blocked_set(win, 2460.0)
        chk("s=2460 reproduces the SECOND raycast's solid-blocked set",
            got2 == t2460, "raycast %s..%s (%d), model %s..%s (%d)"
            % (min(t2460), max(t2460), len(t2460), min(got2), max(got2),
               len(got2)))
    else:
        chk("s=2460 second ground truth present", False, "missing " + p2460)

    # slab-test controls
    p, q = (0, 0, 0), (10, 0, 0)
    chk("segment through a box hits",
        seg_box(p, q, (4, -1, -1), (5, 1, 1)) is not None)
    chk("segment beside a box misses",
        seg_box(p, q, (4, 5, -1), (5, 6, 1)) is None)
    chk("box beyond the far end misses",
        seg_box(p, q, (12, -1, -1), (13, 1, 1)) is None)
    # the abutment must actually be in the model
    nm = [b[0] for b in bridge_boxes(2410.0)]
    chk("the model contains abutments and wing walls",
        any(n.startswith("abutment") for n in nm)
        and sum(1 for n in nm if n.startswith("wing")) == 10)
    print(">> STAGE RESULT: %s"
          % ("PONT_FULL_SELFTEST_OK" if ok else "PONT_FULL_SELFTEST_FAIL"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--station", type=float, default=2460.0)
    ap.add_argument("--frames", default="1191-2714")
    ap.add_argument("--sweep", default=None,
                    help="s0,s1,step over the whole of beat 5")
    ap.add_argument("--soffit", type=float, default=None,
                    help="soffit height over the road; default 6.80")
    ap.add_argument("--open-parapet", action="store_true",
                    help="model the concrete upstand as kerb + full-height mesh")
    ap.add_argument("--grid", default=None,
                    help="s0,s1,ds,z0,z1,dz -- station x soffit")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(0 if selftest() else 1)
    t = a.frames.replace("-", ",").split(",")
    frames = list(range(int(t[0]), int(t[1]) + 1))
    if a.sweep:
        s0, s1, st = (float(v) for v in a.sweep.split(","))
        print("station   full-blocked   any-occluded   worst frac   window")
        s = s0
        while s <= s1 + 1e-9:
            rows = run(frames, s, open_parapet=a.open_parapet)
            full = [r["f"] for r in rows if r["blocked"] == r["n"]]
            any_ = [r["f"] for r in rows if r["blocked"] > 0]
            worst = max((r["frac"] for r in rows), default=0.0)
            print("  %7.1f      %4d          %4d        %.3f      %s"
                  % (s, len(full), len(any_), worst,
                     ("%d..%d" % (min(any_), max(any_))) if any_ else "-"))
            s += st
        return
    if a.grid:
        s0, s1, ds, z0, z1, dz = (float(v) for v in a.grid.split(","))
        zs = []
        z = z0
        while z <= z1 + 1e-9:
            zs.append(z)
            z += dz
        print("soffit\\station " + " ".join("%6.0f" % v for v in
              [s0 + i * ds for i in range(int((s1 - s0) / ds) + 1)]))
        for z in zs:
            row = []
            st = s0
            while st <= s1 + 1e-9:
                rr = run(frames, st, soffit=z, open_parapet=a.open_parapet)
                row.append(sum(1 for r in rr if r["blocked"] == r["n"]))
                st += ds
            print("  %6.2f      " % z + " ".join("%6d" % v for v in row))
        return
    rows = run(frames, a.station, verbose=True, soffit=a.soffit,
               open_parapet=a.open_parapet)
    full = [r["f"] for r in rows if r["blocked"] == r["n"]]
    print(">> s=%.1f  fully blocked %d frames%s"
          % (a.station, len(full),
             ("  (%d..%d)" % (min(full), max(full))) if full else ""))
    print(">> STAGE RESULT: PONT_FULL_OK")


if __name__ == "__main__":
    main()
