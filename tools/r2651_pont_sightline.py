#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
r2651_pont_sightline.py — DOES LE PONT DE LA PLONGEE STAND BETWEEN THE LENS AND
THE CAR, AND FOR HOW LONG?  Pure geometry. No Blender, no world blend.

WHY THIS EXISTS SEPARATELY FROM THE FULL RAYCAST.  A raycast against the
assembled world is the authority, but it needs a 7.5 GB scene and a rented box.
This does not: `build_architecture.py` builds this bridge from eleven numbers in
a local frame on the centreline at s = 2410, and every one of them is readable
from source. So the bridge can be reconstructed exactly as an oriented box and
the camera-to-car segment intersected against it analytically, in a second, on a
machine that is swapping.

It is therefore a CHEAP PREDICTION that the raycast must agree with. If the two
disagree, one of them is wrong and that is worth knowing.

THE BRIDGE, out of `build_architecture.py` (search `PONT_S`):

    PONT_S = 2410.0                     station, on the centreline
    zr     = C.elevation_c(2410)        road level at that station
    soff   = zr + 6.80                  soffit -- underside of the girders
    half   = 15.0                       spans u = -15 .. +15 (lateral)
    dw     = 6.0                        deck width ALONG the track

    girders     soff        .. soff + 1.35
    deck slab   soff + 1.35 .. soff + 1.62
    parapet     soff + 1.62 .. soff + 2.72   (A_ConcPrecast -- SOLID)
    mesh screen soff + 2.72 .. soff + 3.70   (A_MeshDark -- SEE-THROUGH in
                                              reality, opaque to a raycast)

    along-track extent  -dw/2 - 0.35 .. +dw/2 + 0.35  = -3.35 .. +3.35 m

THE SOLID BAND AND THE SEE-THROUGH BAND ARE REPORTED SEPARATELY, because a
raycast cannot tell a concrete parapet from a wire fence and this project has
already been bitten by exactly that.

    .venv/bin/python tools/r2651_pont_sightline.py
    .venv/bin/python tools/r2651_pont_sightline.py --selftest
"""
import argparse
import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "world"))

PONT_S = 2410.0
HALF = 15.0           # lateral half-span, m
DW = 6.0              # deck width along the track, m
ALONG = DW / 2 + 0.35     # 3.35 m either side of the station
SOFFIT_OVER_ROAD = 6.80

BANDS = {                                   # (z_lo, z_hi) above the soffit
    "girders":     (0.00, 1.35),
    "deck_slab":   (1.35, 1.62),
    "parapet":     (1.62, 2.72),            # SOLID concrete
    "mesh_screen": (2.72, 3.70),            # see-through in reality
}
SOLID = ("girders", "deck_slab", "parapet")
SEE_THROUGH = ("mesh_screen",)


def bridge_frame():
    """(origin, along, lateral, up, z_road) — the bridge's own orthonormal frame."""
    import world_contract as C
    x, y, _z, hdg, _k = C.centreline(PONT_S)
    along = np.array([np.cos(hdg), np.sin(hdg), 0.0])
    lat = np.array([-np.sin(hdg), np.cos(hdg), 0.0])
    up = np.array([0.0, 0.0, 1.0])
    zr = float(C.elevation_c(PONT_S))
    return np.array([x, y, 0.0]), along, lat, up, zr


def segment_hits_slab(P0, P1, org, along, lat, zr, band):
    """Does the segment P0->P1 pass through the bridge's band?  Slab method.

    Returns (hit, t_enter, t_exit) with t in [0, 1] along the segment.
    """
    lo = zr + SOFFIT_OVER_ROAD + band[0]
    hi = zr + SOFFIT_OVER_ROAD + band[1]
    d = P1 - P0
    t0, t1 = 0.0, 1.0
    for axis, a, b in ((along, -ALONG, ALONG),
                       (lat, -HALF, HALF),
                       (np.array([0.0, 0.0, 1.0]), lo, hi)):
        # coordinate of P0 and direction along this axis, in the bridge frame
        if axis[2] == 1.0:
            p = P0[2]
            dd = d[2]
        else:
            p = float((P0 - org) @ axis)
            dd = float(d @ axis)
        if abs(dd) < 1e-12:
            if p < a or p > b:
                return False, 0.0, 0.0
            continue
        ta, tb = (a - p) / dd, (b - p) / dd
        if ta > tb:
            ta, tb = tb, ta
        t0 = max(t0, ta)
        t1 = min(t1, tb)
        if t0 > t1:
            return False, 0.0, 0.0
    return True, t0, t1


def run(a):
    path = {r["f"]: r for r in json.load(
        open(os.path.join(ROOT, "world/camera_rig_path.json")))["path"]}
    car = {r["f"]: r for r in json.load(
        open(os.path.join(ROOT, "world/car_anim_measured.json")))["frames"]}
    org, along, lat, up, zr = bridge_frame()
    print(">> Le Pont de la Plongee: station %.0f, road z %.3f, soffit z %.3f, "
          "deck top z %.3f, parapet top z %.3f"
          % (PONT_S, zr, zr + SOFFIT_OVER_ROAD, zr + SOFFIT_OVER_ROAD + 1.62,
             zr + SOFFIT_OVER_ROAD + 2.72))
    print("   spans lateral +-%.1f m, along-track +-%.2f m" % (HALF, ALONG))

    rows = []
    for f in range(1191, 2715):
        if f not in path or f not in car:
            continue
        P0 = np.array(path[f]["p"], dtype=np.float64)
        c = np.array(car[f]["loc"], dtype=np.float64)
        # aim at the car's roll hoop rather than its origin: the origin is at the
        # contact plane and a bridge that clears the origin can still cut the car.
        targets = [c + np.array([0, 0, dz]) for dz in (0.10, 0.55, 1.00)]
        hits = {}
        for nm, band in BANDS.items():
            n = 0
            for T in targets:
                h, t0, t1 = segment_hits_slab(P0, T, org, along, lat, zr, band)
                if h:
                    n += 1
            if n:
                hits[nm] = n
        solid = sum(hits.get(k, 0) for k in SOLID)
        mesh = sum(hits.get(k, 0) for k in SEE_THROUGH)
        d_car = float(np.linalg.norm(c - P0))
        rows.append(dict(f=f, solid=solid, mesh=mesh, d=round(d_car, 1),
                         which=",".join(sorted(hits)) or ""))

    hit = [r for r in rows if r["solid"] > 0]
    mhit = [r for r in rows if r["solid"] == 0 and r["mesh"] > 0]
    print()
    print(">> frames of beat 5 whose camera-to-car line passes through SOLID "
          "bridge structure: %d" % len(hit))
    print(">> ... through the SEE-THROUGH mesh screen only:                  %d"
          % len(mhit))
    if hit:
        fs = [r["f"] for r in hit]
        runs = []
        s = fs[0]
        for i in range(1, len(fs) + 1):
            if i == len(fs) or fs[i] != fs[i - 1] + 1:
                runs.append((s, fs[i - 1]))
                if i < len(fs):
                    s = fs[i]
        for lo, hi in runs:
            sub = [r for r in hit if lo <= r["f"] <= hi]
            full = [r for r in sub if r["solid"] >= 3]
            print("   f%d-%d  %d frames, %.2f s   fully blocked on %d of them   "
                  "car %.0f-%.0f m   parts: %s"
                  % (lo, hi, hi - lo + 1, (hi - lo + 1) / 24.0, len(full),
                     min(r["d"] for r in sub), max(r["d"] for r in sub),
                     sorted({p for r in sub for p in r["which"].split(",") if p})))
    out = os.path.join(ROOT, "render/r2651/pont_sightline.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(rows, open(out, "w"))
    print(">> wrote %s" % out)
    for f in (2180, 2185, 2190, 2195, 2200):
        r = next((x for x in rows if x["f"] == f), None)
        if r:
            print("   f%-5d solid %d/3  mesh %d/3  car %.0f m  %s"
                  % (f, r["solid"], r["mesh"], r["d"], r["which"]))
    print(">> STAGE RESULT: R2651_PONT_SIGHTLINE_OK")


def selftest():
    ok = True
    org, along, lat, up, zr = bridge_frame()
    lo = zr + SOFFIT_OVER_ROAD

    # 1. a segment straight down the middle of the deck slab must hit it.
    P0 = org + along * 60.0 + np.array([0, 0, lo + 1.5])
    P1 = org - along * 60.0 + np.array([0, 0, lo + 1.5])
    h, _, _ = segment_hits_slab(P0, P1, org, along, lat, zr, BANDS["deck_slab"])
    print("  through the deck slab            %s  (must be True)" % h)
    ok &= h

    # 2. THE CONTROL THAT MATTERS: a segment UNDER the soffit must miss
    #    everything. A car passes under this bridge every lap and if the
    #    instrument cannot see that, every number it produces is noise.
    P0 = org + along * 60.0 + np.array([0, 0, lo - 3.0])
    P1 = org - along * 60.0 + np.array([0, 0, lo - 3.0])
    any_hit = any(segment_hits_slab(P0, P1, org, along, lat, zr, b)[0]
                  for b in BANDS.values())
    print("  under the soffit                 %s  (must be False)" % any_hit)
    ok &= not any_hit

    # 3. a segment OUTSIDE the lateral span must miss.
    P0 = org + along * 60.0 + lat * 40.0 + np.array([0, 0, lo + 1.5])
    P1 = org - along * 60.0 + lat * 40.0 + np.array([0, 0, lo + 1.5])
    any_hit = any(segment_hits_slab(P0, P1, org, along, lat, zr, b)[0]
                  for b in BANDS.values())
    print("  40 m off to the side             %s  (must be False)" % any_hit)
    ok &= not any_hit

    # 4. a segment that STOPS SHORT of the bridge must miss, however well aimed.
    #    This is the depth test, and without it "aimed at" is mistaken for
    #    "blocked by".
    P0 = org + along * 60.0 + np.array([0, 0, lo + 1.5])
    P1 = org + along * 30.0 + np.array([0, 0, lo + 1.5])
    h, _, _ = segment_hits_slab(P0, P1, org, along, lat, zr, BANDS["deck_slab"])
    print("  stopping 30 m short              %s  (must be False)" % h)
    ok &= not h

    # 5. and one that starts beyond it going away must miss too.
    P0 = org - along * 30.0 + np.array([0, 0, lo + 1.5])
    P1 = org - along * 90.0 + np.array([0, 0, lo + 1.5])
    h, _, _ = segment_hits_slab(P0, P1, org, along, lat, zr, BANDS["deck_slab"])
    print("  starting past it, going away     %s  (must be False)" % h)
    ok &= not h

    print(">> STAGE RESULT: %s"
          % ("R2651_PONT_SELFTEST_OK" if ok else "R2651_PONT_SELFTEST_FAIL"))
    return ok


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    sys.exit(0 if selftest() else 1) if a.selftest else run(a)
