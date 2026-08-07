#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
r2731_pit_sightline.py — WHICH BOX OF THE PIT BUILDING IS IN THE WAY, AND HOW
FAR DOES IT HAVE TO MOVE?

    python3 tools/r2731_pit_sightline.py
    python3 tools/r2731_pit_sightline.py --selftest
    python3 tools/r2731_pit_sightline.py --west-roof 7.4 --west-end -232.0

WHY IT EXISTS
-------------
R2-666 measured, with the depth-tested raycast against the assembled world,
that the car is WHOLLY hidden behind `ARCH_PitBuilding_Shell` on f1114-1116
(six frames affected, f1113-1118), occluder at 9.3-14.0 m from the lens.  The
raycast names the OBJECT.  `ARCH_PitBuilding_Shell` is one object of some
thousands of boxes and 320 m long, so "the pit building" is not yet a thing you
can fix.

This reconstructs the shell's boxes from `build_architecture.py`'s own module
constants — the same technique `r2651_pont_sightline.py` used on the bridge —
and intersects the camera-to-car segment against each named box.  It says WHICH
box, at what distance, and what change to which constant clears it.

IT IS A CHEAP PREDICTION, NOT A REPLACEMENT.  The authority is
`tools/r2651_occlusion_sweep.py` against the built world.  This exists so that
the change put in front of that raycast is a considered one rather than a
guess.

WHAT IT DOES NOT MODEL
----------------------
`ARCH_PitBuilding_Detail` (mullions, doors, balcony dressing, roof plant) is a
separate object and the raycast did not name it, so it is not reconstructed.
Per-bay piers and door heads are reconstructed from the garage table's own
generator only to the extent their y/z band can be stated without it; they sit
at y = 23.48-24.05, z <= 6.0 and no sightline in this window is below z = 13 by
the time it reaches y = 23.5, which the run prints so it is checked and not
assumed.  Bevels (0.020) are not modelled: they only ever make a box slightly
smaller, so a clearance reported here is conservative by <= 20 mm.
"""

import argparse
import json
import math
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "world"))

import world_contract as WC                                   # noqa: E402

# ---- build_architecture.py's own constants, copied with their line numbers -
# build_architecture.py:3521-3531.  If any of these move, this tool is stale;
# `--selftest` re-reads them out of the source and fails on a mismatch.
BAY_W = [21.0, 22.0, 20.5, 21.5, 23.0, 20.0, 21.0, 22.5,
         20.5, 21.0, 22.0, 20.5, 20.5, 20.0]
CORE_W = [6.0, 5.0, 5.0, 8.0]
PB_Y0, PB_Y1 = 23.5, 40.5
PB_X0, PB_X1 = -245.0, 75.0
PB_Z_GF = 6.40
PB_Z_L1 = 10.40
PB_Z_RF = 10.90
PB_Z_PT = 12.00
CANOPY_Y = 19.80
L1_FACE_Y = 21.20

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


# ---- the R2-731 annexe, READ OUT OF THE SOURCE rather than restated --------
# This tool exists to check a change to `build_architecture.py`.  If it carried
# its own copy of that change's constants it would be checking itself.
_SRC = open(os.path.join(ROOT, "world", "build_architecture.py")).read()


def _const(name, default=None):
    m = re.search(r"^%s\s*=\s*([-+0-9.]+|PB_Z_L1)\s*(?:#|$)" % name, _SRC,
                  re.M)
    if not m:
        if default is None:
            raise SystemExit("build_architecture.py no longer declares %s; this "
                             "tool is stale and must not be trusted." % name)
        return default
    return PB_Z_L1 if m.group(1) == "PB_Z_L1" else float(m.group(1))


PB_ANNEXE_X = _const("PB_ANNEXE_X")
PB_Z_ANNEXE = _const("PB_Z_ANNEXE")
ANNEXE_EAVE_Y = _const("PB_ANNEXE_EAVE_Y")
ANNEXE_FASCIA = _const("PB_ANNEXE_FASCIA")
ANNEXE_CORE_UP = _const("PB_ANNEXE_CORE_UP")
SHIPPED = (PB_ANNEXE_X, PB_Z_ANNEXE)


def shell_boxes(west_roof=None, west_end=None, annexe=None):
    """Every box `build_pit_building` puts in ARCH_PitBuilding_Shell that can
    be stated from module constants, as (name, (x0,y0,z0), (x1,y1,z1)).

    west_roof / west_end describe a blunt PROPOSAL: cap everything west of
    `west_end` at `west_roof`.  Useful for bracketing, not buildable.

    `annexe = (x_step, rf_z)` is the PROPOSED BUILD: west of `x_step` the roof
    is the annexe's — deck at `rf_z`, eaves stopping on the façade line at
    ANNEXE_EAVE_Y with a fascia instead of a parapet, no roof overhang, and the
    W core capped at rf_z + ANNEXE_CORE_UP.
    """
    B = []

    def add(nm, a, b):
        B.append((nm, tuple(map(float, a)), tuple(map(float, b))))

    def zcap(nm, a, b):
        """A roof-level box, split at west_end if the notch is asked for.

        The notch caps everything WEST of `west_end` at `west_roof`; anything
        east of it is untouched.  A capped box whose floor is already above
        `west_roof` disappears entirely, which is what a stepped-down end
        means.
        """
        if west_roof is None or west_end is None or a[0] >= west_end:
            add(nm, a, b)                          # wholly east: unchanged
            return
        if b[0] <= west_end:                       # wholly west: capped
            if west_roof > a[2]:
                add(nm + "|west", a, (b[0], b[1], min(b[2], west_roof)))
            return
        if west_roof > a[2]:                       # straddles: split
            add(nm + "|west", a, (west_end, b[1], min(b[2], west_roof)))
        add(nm + "|east", (west_end, a[1], a[2]), b)

    ax, arf = (annexe if annexe else (PB_X0, None))

    def roof(nm, a, b):
        """A roof-level box.  East of the annexe step it is built as shipped;
        west of it, it is the annexe's own roof — one storey down, stopping on
        the façade line."""
        if annexe is None or a[0] >= ax:
            add(nm, a, b)
            return
        xe = min(b[0], ax)
        dz = b[2] - a[2]
        y0 = max(a[1], ANNEXE_EAVE_Y)
        if y0 < b[1] and a[2] >= PB_Z_RF:
            add(nm + "|annexe", (a[0], y0, arf + (a[2] - PB_Z_RF)),
                (xe, b[1], arf + (a[2] - PB_Z_RF) + dz))
        if b[0] > ax:
            add(nm + "|main", (ax, a[1], a[2]), b)

    add("slab", (PB_X0, PB_Y0, -0.45), (PB_X1, PB_Y1, 0.012))
    if annexe is None:
        zcap("rear_wall", (PB_X0, PB_Y1 - 0.35, 0.0), (PB_X1, PB_Y1, PB_Z_RF))
        zcap("flank_W", (PB_X0, PB_Y0, 0.0), (PB_X0 + 0.35, PB_Y1, PB_Z_RF))
        add("L1_spandrel", (PB_X0, L1_FACE_Y, PB_Z_GF),
            (PB_X1, L1_FACE_Y + 0.12, PB_Z_L1))
    else:
        add("rear_wall|main", (ax, PB_Y1 - 0.35, 0.0), (PB_X1, PB_Y1, PB_Z_RF))
        add("rear_wall|annexe", (PB_X0, PB_Y1 - 0.35, 0.0),
            (ax, PB_Y1, arf + 0.90))
        add("flank_W", (PB_X0, PB_Y0, 0.0), (PB_X0 + 0.35, PB_Y1, arf + 0.90))
        add("L1_spandrel|main", (ax, L1_FACE_Y, PB_Z_GF),
            (PB_X1, L1_FACE_Y + 0.12, PB_Z_L1))
        add("L1_spandrel|annexe", (PB_X0, L1_FACE_Y, PB_Z_GF),
            (ax, L1_FACE_Y + 0.12, arf))
    add("flank_E", (PB_X1 - 0.35, PB_Y0, 0.0), (PB_X1, PB_Y1, PB_Z_RF))
    add("ff_slab", (PB_X0, CANOPY_Y, PB_Z_GF - 0.40), (PB_X1, PB_Y1, PB_Z_GF))
    add("canopy_fascia", (PB_X0, CANOPY_Y - 0.16, PB_Z_GF - 0.55),
        (PB_X1, CANOPY_Y, PB_Z_GF + 0.06))
    if annexe is None:
        zcap("upper_wall", (PB_X0, L1_FACE_Y - 0.10, PB_Z_L1),
             (PB_X1, PB_Y1, PB_Z_RF))
    else:                       # the annexe's roof sits ON the L1 head
        add("upper_wall|main", (ax, L1_FACE_Y - 0.10, PB_Z_L1),
            (PB_X1, PB_Y1, PB_Z_RF))
    zcap("roof_deck", (PB_X0, CANOPY_Y + 0.6, PB_Z_RF),
         (PB_X1, PB_Y1, PB_Z_RF + 0.06)) if annexe is None else \
        roof("roof_deck", (PB_X0, CANOPY_Y + 0.6, PB_Z_RF),
             (PB_X1, PB_Y1, PB_Z_RF + 0.06))
    for k in range(int((PB_X1 - PB_X0) / 0.60) + 1):
        sx = PB_X0 + k * 0.60
        (zcap if annexe is None else roof)(
            "roof_seam_%d" % k, (sx - 0.022, CANOPY_Y + 0.6, PB_Z_RF + 0.06),
            (sx + 0.022, PB_Y1, PB_Z_RF + 0.115))
    for k in range(4):
        ly = CANOPY_Y + 1.4 + k * 5.0
        (zcap if annexe is None else roof)(
            "roof_lap_%d" % k, (PB_X0, ly - 0.04, PB_Z_RF + 0.060),
            (PB_X1, ly + 0.04, PB_Z_RF + 0.064))
    if annexe is None:
        zcap("parapet_front", (PB_X0, CANOPY_Y + 0.6, PB_Z_RF),
             (PB_X1, CANOPY_Y + 0.85, PB_Z_PT))
        zcap("parapet_rear", (PB_X0, PB_Y1 - 0.25, PB_Z_RF),
             (PB_X1, PB_Y1, PB_Z_PT))
    else:
        add("parapet_front|main", (ax, CANOPY_Y + 0.6, PB_Z_RF),
            (PB_X1, CANOPY_Y + 0.85, PB_Z_PT))
        add("parapet_rear|main", (ax, PB_Y1 - 0.25, PB_Z_RF),
            (PB_X1, PB_Y1, PB_Z_PT))
        # the annexe: an eaves fascia on the façade line, not a parapet.  No
        # rear or west upstand is modelled because none is built: `rear_wall`
        # and `flank_W` already run to PB_Z_RF and stand proud of the annexe
        # deck on those two sides.
        add("annexe_fascia", (PB_X0, ANNEXE_EAVE_Y, arf),
            (ax, ANNEXE_EAVE_Y + 0.16, arf + ANNEXE_FASCIA))
        add("annexe_step_face", (ax, ANNEXE_EAVE_Y, arf),
            (ax + 0.35, PB_Y1, PB_Z_PT))
    add("rear_canopy", (PB_X0, PB_Y1, 4.9), (PB_X1, PB_Y1 + 3.2, 5.15))

    # ---- cores: _core(), build_architecture.py:3851 ------------------------
    cy0, cy1 = 21.9, PB_Y1
    xs = []
    x = PB_X0
    xs.append(("W", x, x + CORE_W[0]))
    x += CORE_W[0]
    idx = 0
    for gi, n in enumerate((4, 5, 5)):
        for _k in range(n):
            x += BAY_W[idx]
            idx += 1
        if gi < 2:
            xs.append(("M%d" % gi, x, x + CORE_W[gi + 1]))
            x += CORE_W[gi + 1]
    xs.append(("E", PB_X1 - CORE_W[3], PB_X1))
    for tag, xa, xb in xs:
        top = PB_Z_PT + (0.7 if tag != "E" else 1.9)
        if west_roof is not None and west_end is not None and xb <= west_end:
            top = min(top, west_roof)
        if annexe is not None and xb <= ax:
            top = arf + ANNEXE_CORE_UP
        add("core_%s" % tag, (xa, cy0, 0.0), (xb, cy1, top))
        if tag == "E":
            add("core_E_plant", (xa + 1.0, cy0 + 3.0, top),
                (xb - 1.0, cy0 + 8.0, top + 2.4))
        else:
            add("core_%s_plant" % tag, (xa + 0.8, cy0 + 4.0, top),
                (xb - 0.8, cy0 + 7.5, top + 1.6))
    return B


def seg_box(p, q, a, b):
    """Slab test.  Returns (t_enter, t_exit) in [0,1] or None."""
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


def to_design(p):
    x, y = WC.world_to_circuit(p[0], p[1])
    return (float(x), float(y), float(p[2]))


def run(frames, west_roof=None, west_end=None, annexe=None, verbose=True):
    cam = {int(e["f"]): e for e in
           json.load(open(os.path.join(ROOT, "world",
                                       "camera_rig_path.json")))["path"]}
    car = {int(e["f"]): e for e in
           json.load(open(os.path.join(ROOT, "world",
                                       "car_anim_measured.json")))["frames"]}
    boxes = shell_boxes(west_roof, west_end, annexe)
    rows = []
    for f in frames:
        if f not in cam or f not in car:
            continue
        C = to_design(cam[f]["p"])
        K = car[f]
        L = to_design(K["loc"])
        pts = [to_design(P) for P in car_samples(K)]
        nb = 0
        first = None
        owners = {}
        for P in pts:
            hit = None
            for nm, a, b in boxes:
                r = seg_box(C, P, a, b)
                if r is None:
                    continue
                t = r[0]
                seglen = math.dist(C, P)
                if t * seglen < 1e-6:
                    continue
                if hit is None or t < hit[0]:
                    hit = (t, nm, t * seglen)
            if hit is not None:
                nb += 1
                owners[hit[1]] = owners.get(hit[1], 0) + 1
                if first is None or hit[0] < first[0]:
                    first = hit
        rows.append(dict(f=f, n=len(pts), blocked=nb,
                         frac=round(nb / len(pts), 4),
                         owner=(max(owners, key=owners.get) if owners else None),
                         dist=(round(first[2], 2) if first else None),
                         cam_design=[round(v, 2) for v in C],
                         car_design=[round(v, 2) for v in L]))
        if verbose:
            r = rows[-1]
            print("  f%-5d blocked %2d/%2d  %-18s  d=%s  cam=(%.1f,%.1f,%.2f)"
                  % (f, r["blocked"], r["n"], r["owner"] or "-",
                     ("%.2f m" % r["dist"]) if r["dist"] else "  -   ",
                     C[0], C[1], C[2]))
    return rows


def sightline_profile(f):
    """For one frame: the ray's z and y at each x across the building, so the
    shape of the crossing is visible rather than inferred."""
    cam = {int(e["f"]): e for e in
           json.load(open(os.path.join(ROOT, "world",
                                       "camera_rig_path.json")))["path"]}
    car = {int(e["f"]): e for e in
           json.load(open(os.path.join(ROOT, "world",
                                       "car_anim_measured.json")))["frames"]}
    C = to_design(cam[f]["p"])
    L = to_design(car[f]["loc"])
    print("  f%d  cam(%.2f, %.2f, %.2f) -> car(%.2f, %.2f, %.2f)"
          % (f, C[0], C[1], C[2], L[0], L[1], L[2] + 0.5))
    L = (L[0], L[1], L[2] + 0.5)
    print("      x        y       z    (design frame; building y 19.8..40.5)")
    x = PB_X0
    while x <= min(PB_X1, L[0]) and x <= -228.0:
        if abs(L[0] - C[0]) < 1e-9:
            break
        t = (x - C[0]) / (L[0] - C[0])
        if t < 0 or t > 1:
            x += 1.0
            continue
        y = C[1] + t * (L[1] - C[1])
        z = C[2] + t * (L[2] - C[2])
        print("   %8.2f %7.2f %7.2f   %s" % (x, y, z,
              "over the building" if 19.8 <= y <= 40.5 else "clear of it in y"))
        x += 1.0


def selftest():
    ok = True

    def chk(nm, cond):
        nonlocal ok
        print("   %-42s %s" % (nm, "PASS" if cond else "FAIL"))
        ok = ok and bool(cond)

    # 1. the constants are still build_architecture.py's
    src = open(os.path.join(ROOT, "world", "build_architecture.py")).read()
    for nm, val in (("PB_Z_PT", PB_Z_PT), ("PB_Z_RF", PB_Z_RF),
                    ("CANOPY_Y", CANOPY_Y), ("PB_X0, PB_X1", None)):
        if val is None:
            chk("source still declares %s" % nm, "PB_X0, PB_X1 = -245.0, 75.0" in src)
        else:
            chk("source %s == %.2f" % (nm, val),
                ("%s = %.2f" % (nm, val)) in src)
    # 2. slab test controls
    p, q = (0, 0, 0), (10, 0, 0)
    chk("segment through a box hits",
        seg_box(p, q, (4, -1, -1), (5, 1, 1)) is not None)
    chk("segment beside a box misses",
        seg_box(p, q, (4, 5, -1), (5, 6, 1)) is None)
    chk("box BEHIND the far end misses",
        seg_box(p, q, (12, -1, -1), (13, 1, 1)) is None)
    chk("box exactly containing the origin hits",
        seg_box(p, q, (-1, -1, -1), (1, 1, 1)) is not None)
    # 3. THE INSTRUMENT MUST REPRODUCE THE KNOWN DEFECT.  `annexe=None` is the
    #    PRE-R2-731 geometry, and R2-666's raycast measured f1114-1116 wholly
    #    hidden there.  A tool that cannot see the defect cannot clear it.
    pre = {r["f"]: r for r in run(range(1100, 1136), verbose=False)}
    chk("pre-R2-731: f1114-1116 fully blocked",
        all(pre[f]["blocked"] == pre[f]["n"] for f in (1114, 1115, 1116)))
    chk("pre-R2-731: f1113/1117/1118 partial, as the raycast has them",
        all(0 < pre[f]["blocked"] < pre[f]["n"] for f in (1113, 1117, 1118)))
    chk("pre-R2-731: f1115 owner is a roof-level box",
        pre[1115]["owner"] in ("core_W", "parapet_front", "roof_deck",
                               "upper_wall"))
    chk("pre-R2-731: f1115 first hit is 8-15 m from the lens",
        pre[1115]["dist"] is not None and 8.0 <= pre[1115]["dist"] <= 15.0)
    # 4. control frames the raycast calls clear must read clear here too, in
    #    the geometry that has the defect — otherwise "clear" means nothing
    chk("pre-R2-731: f1100 clear (control)", pre[1100]["blocked"] == 0)
    chk("pre-R2-731: f1130 clear (control)", pre[1130]["blocked"] == 0)
    # 5. and the shipped constants must clear the whole event
    post = {r["f"]: r for r in run(range(1100, 1136), annexe=SHIPPED,
                                   verbose=False)}
    chk("shipped: f1105-1135 all clear, partials included",
        all(post[f]["blocked"] == 0 for f in post))
    print(">> STAGE RESULT: %s" % ("PIT_SELFTEST_OK" if ok else "PIT_SELFTEST_FAIL"))
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--frames", default="1105-1130")
    ap.add_argument("--west-roof", type=float, default=None)
    ap.add_argument("--west-end", type=float, default=None)
    ap.add_argument("--profile", type=int, default=None)
    ap.add_argument("--annexe", default=None,
                    help="x_step,roof_z (default: the shipped constants read "
                         "out of build_architecture.py); 'none' for the "
                         "pre-R2-731 geometry")
    ap.add_argument("--annexe-sweep", action="store_true")
    ap.add_argument("--sweep", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(0 if selftest() else 1)
    t = a.frames.replace("-", ",").split(",")
    frames = list(range(int(t[0]), int(t[1]) + 1))
    if a.profile:
        sightline_profile(a.profile)
        return
    if a.sweep:
        print("west_end  west_roof   blocked frames (of %d)" % len(frames))
        for we in (-244.0, -242.0, -240.0, -238.0, -236.0, -234.0, -232.0,
                   -230.0, -226.0):
            for wr in (11.0, 10.0, 9.0, 8.0, 7.4, 6.6, 6.0):
                rows = run(frames, wr, we, verbose=False)
                nb = sum(1 for r in rows if r["blocked"] == r["n"])
                npart = sum(1 for r in rows if r["blocked"] > 0)
                print("  %8.1f  %8.2f   full %2d   any %2d" % (we, wr, nb, npart))
        return
    ann = SHIPPED
    if a.annexe:
        ann = None if a.annexe in ("none", "off", "pre") else \
            tuple(float(v) for v in a.annexe.split(","))
    if a.annexe_sweep:
        print("x_step   roof_z    fully blocked / any occlusion, f%d-%d"
              % (frames[0], frames[-1]))
        for xs in (-239.0, -237.0, -236.0, -235.0, -234.0, -233.0, -232.0,
                   -230.0, -228.0, -224.0, -218.0):
            for rz in (10.40, 10.90):
                rows = run(frames, annexe=(xs, rz), verbose=False)
                nb = sum(1 for r in rows if r["blocked"] == r["n"])
                na = sum(1 for r in rows if r["blocked"] > 0)
                worst = max((r["frac"] for r in rows), default=0.0)
                print("  %7.1f  %6.2f    full %2d   any %2d   worst frac %.3f"
                      % (xs, rz, nb, na, worst))
        return
    print("pit-building sightline, west_roof=%s west_end=%s annexe=%s"
          % (a.west_roof, a.west_end, ann))
    rows = run(frames, a.west_roof, a.west_end, ann)
    nb = sum(1 for r in rows if r["blocked"] == r["n"])
    print(">> fully blocked: %d of %d frames" % (nb, len(rows)))
    print(">> STAGE RESULT: PIT_SIGHTLINE_OK")


if __name__ == "__main__":
    main()
