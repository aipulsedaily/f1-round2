"""Beat 1's presentation gate: is the presented cluster IN FOCUS, and does it FIT?

Two questions the shipped gates could not answer, for the reason R2-062 named once
already:

    `presentation_framing` in the beat sheet reports `edge_angle_deg = 0.000` for
    every one of the fifteen presentations.  That is not a pass.  It is the angular
    offset of the cluster's CENTRE from the optical axis, and the station is BUILT
    by placing the lens on the ray through that centre, so the number is
    identically zero by construction and can never be anything else.  It measures
    aim.  Nobody measured SIZE, and nobody measured DEPTH.

This module measures both, off the same axis-aligned bounding box the standoff
formula itself consumes (`docs/explode_plan.json`), so it cannot be accused of
grading against a different body than the one that set the distance.

    standoff = max(radius * 1.55 + 0.42, 0.75),  radius = half the bbox DIAGONAL

FIT.  The eight exploded bbox corners are projected through the actual camera key
(position, look-at, lens, 36 mm sensor, AUTO fit at 16:9 -> 20.25 mm of sensor
height).  Reported as a fraction of frame height and frame width.  >1.0 means the
cluster does not fit and the audience sees a fragment.

FOCUS.  The same eight corners are projected onto the view axis to get the near and
far depth of the cluster as the lens actually sees it, and Blender's own thin-lens
blur is evaluated at each:

    A = f / N                                       aperture diameter
    C = A * f / (s_focus - f) * |s - s_focus| / s   blur diameter on the sensor

converted to 4K pixels at 3840 / 36 mm = 106.67 px/mm.  A cluster is IN FOCUS when
its whole depth stays inside the chosen pixel budget; the default budget is 2.0 px,
which is the loosest number that can still be called sharp in a brief that demands
carbon weave resolve as weave at macro distance.

Run:
    python3 tools/beat1_present_gate.py                  # the fifteen stations
    python3 tools/beat1_present_gate.py --selftest       # the arithmetic, checked
    python3 tools/beat1_present_gate.py --json out.json
"""

import argparse
import json
import math
import os
import sys

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SENSOR_MM = 36.0          # anim/build_camera_rig.py:798
RES = (3840, 2160)
PX_PER_MM = RES[0] / SENSOR_MM
SHARP_PX = 2.0


def sensor_hw():
    """(half-width, half-height) of the sensor in mm, sensor_fit AUTO at 16:9."""
    w = SENSOR_MM
    h = SENSOR_MM * RES[1] / RES[0]
    return w / 2.0, h / 2.0


def sub(a, b):
    return [a[i] - b[i] for i in range(3)]


def dot(a, b):
    return sum(a[i] * b[i] for i in range(3))


def cross(a, b):
    return [a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0]]


def norm(a):
    m = math.sqrt(dot(a, a))
    return [x / m for x in a] if m > 1e-12 else [0.0, 0.0, 1.0]


def basis(eye, target):
    """Camera basis: fwd toward target, right, up. Roll is irrelevant to extent
    along the two axes only if the box is symmetric, so we report BOTH axes and
    also the roll-invariant radial extent."""
    fwd = norm(sub(target, eye))
    world_up = [0.0, 0.0, 1.0]
    if abs(dot(fwd, world_up)) > 0.999:
        world_up = [0.0, 1.0, 0.0]
    right = norm(cross(fwd, world_up))
    up = norm(cross(right, fwd))
    return fwd, right, up


def corners(bmin, bmax):
    out = []
    for i in (0, 1):
        for j in (0, 1):
            for k in (0, 1):
                out.append([bmin[0] if i == 0 else bmax[0],
                            bmin[1] if j == 0 else bmax[1],
                            bmin[2] if k == 0 else bmax[2]])
    return out


def blur_px(lens_mm, fstop, focus_m, s_m):
    """Thin-lens blur circle diameter in 4K pixels for a point at s_m."""
    f = lens_mm
    s = s_m * 1000.0
    sf = focus_m * 1000.0
    if s <= f or sf <= f:
        return float("inf")
    a = f / fstop
    c_mm = a * f / (sf - f) * abs(s - sf) / s
    return c_mm * PX_PER_MM


def dof_limits(lens_mm, fstop, focus_m, budget_px=SHARP_PX):
    """Near/far distance whose blur circle equals budget_px. Metres."""
    f = lens_mm
    sf = focus_m * 1000.0
    a = f / fstop
    c = budget_px / PX_PER_MM                 # mm on sensor
    k = a * f / (sf - f)                      # mm
    # near: k*(sf-s)/s = c  ->  s = k*sf/(k+c)
    near = k * sf / (k + c)
    den = k - c
    far = (k * sf / den) if den > 1e-9 else float("inf")
    return near / 1000.0, (far / 1000.0 if far != float("inf") else float("inf"))


def measure_station(cl, key, budget_px=SHARP_PX):
    """One presentation. `cl` is an explode_plan cluster, `key` a beat-sheet key."""
    off = cl["explode_offset"]
    bmin = [cl["bbox_min"][i] + off[i] for i in range(3)]
    bmax = [cl["bbox_max"][i] + off[i] for i in range(3)]
    ctr = [cl["centre"][i] + off[i] for i in range(3)]

    eye = key["world"]
    look = key["look_at"]
    lens = float(key["lens_mm"])
    fstop = float(key["fstop"])
    focus = float(key["focus_distance_m"])

    fwd, right, up = basis(eye, look)
    hw, hh = sensor_hw()

    depths, us, vs = [], [], []
    for c in corners(bmin, bmax):
        d = sub(c, eye)
        z = dot(d, fwd)
        depths.append(z)
        if z > 1e-6:
            # projected position on the sensor, mm
            us.append(dot(d, right) / z * lens)
            vs.append(dot(d, up) / z * lens)

    radius = 0.5 * math.sqrt(sum(v * v for v in cl["size"]))
    standoff = max(radius * 1.55 + 0.42, 0.75)
    rng = math.sqrt(dot(sub(ctr, eye), sub(ctr, eye)))

    behind = min(depths) <= 1e-6
    if us:
        ext_w = (max(us) - min(us)) / (2 * hw)
        ext_h = (max(vs) - min(vs)) / (2 * hh)
    else:
        ext_w = ext_h = float("inf")

    near_px = blur_px(lens, fstop, focus, max(min(depths), 1e-3))
    far_px = blur_px(lens, fstop, focus, max(depths))
    ctr_px = blur_px(lens, fstop, focus, rng)
    dn, df = dof_limits(lens, fstop, focus, budget_px)

    # what fraction of the cluster's DEPTH is inside the sharp budget
    lo, hi = min(depths), max(depths)
    inside = max(0.0, min(hi, df) - max(lo, dn))
    frac = inside / (hi - lo) if hi > lo else 1.0

    return {
        "cluster": key.get("focus_target"),
        "t": key["t"], "frame": int(round(key["t"] * 24)) + 1,
        "lens_mm": lens, "fstop": fstop,
        "focus_m": round(focus, 4),
        "range_to_centre_m": round(rng, 4),
        "radius_m": round(radius, 4),
        "standoff_formula_m": round(standoff, 4),
        "widest_size_m": round(max(cl["size"]), 4),
        "extent_frac_frame_h": round(ext_h, 3),
        "extent_frac_frame_w": round(ext_w, 3),
        "fits": bool(ext_h <= 1.0 and ext_w <= 1.0 and not behind),
        "depth_near_m": round(lo, 4), "depth_far_m": round(hi, 4),
        "depth_span_m": round(hi - lo, 4),
        "dof_near_m": round(dn, 4),
        "dof_far_m": (round(df, 4) if df != float("inf") else None),
        "dof_span_m": (round(df - dn, 4) if df != float("inf") else None),
        "blur_near_px": round(near_px, 1),
        "blur_far_px": round(far_px, 1),
        "blur_centre_px": round(ctr_px, 2),
        "depth_frac_sharp": round(frac, 3),
        "in_focus": bool(frac >= 0.999),
    }


def load():
    ep = json.load(open(os.path.join(R2, "docs/explode_plan.json")))
    bs = json.load(open(os.path.join(R2, "docs/beat_sheet.json")))
    return ep["clusters"], bs["beat1"]["camera_keys"]


def run(budget_px=SHARP_PX):
    clusters, keys = load()
    rows = []
    for k in keys:
        tgt = k.get("focus_target")
        # `presentation_dir_measured` is what separates a PRESENTATION from a
        # bridge or close-out key.  Without it the two close-out keys tagged
        # focus_target FW and RW get graded as presentations of clusters they are
        # merely pointing near, and RW's shipped 5.42 m reads as a 3.89 m error
        # against a standoff formula that was never applied to it.
        if tgt not in clusters or not k.get("presentation_dir_measured"):
            continue
        rows.append(measure_station(clusters[tgt], k, budget_px))
    return rows


def selftest():
    """The arithmetic, against cases whose answers are known independently."""
    ok = True

    def chk(name, got, want, tol):
        nonlocal ok
        good = abs(got - want) <= tol
        ok = ok and good
        print("  %-46s %12.5f  want %12.5f  %s"
              % (name, got, want, "ok" if good else "FAIL"))

    # 1. A point AT the focus plane has zero blur, at any aperture.
    chk("blur at focus plane", blur_px(58, 2.2, 1.5, 1.5), 0.0, 1e-9)

    # 2. dof_limits must invert blur_px exactly.
    dn, df = dof_limits(58, 2.2, 1.5, 2.0)
    chk("blur at dof_near == budget", blur_px(58, 2.2, 1.5, dn), 2.0, 1e-6)
    chk("blur at dof_far  == budget", blur_px(58, 2.2, 1.5, df), 2.0, 1e-6)

    # 3. Against the textbook hyperfocal form, which is a DIFFERENT expression:
    #        H = f^2/(N c) + f ;  near = H s/(H + s - f) ;  far = H s/(H - s + f)
    #    The two are NOT algebraically identical.  `blur_px` is the exact thin-lens
    #    result -- the cone from the lens converges at s' = sf/(s-f) and is cut by a
    #    sensor at v = s_f f/(s_f - f), giving C = (f/N) f |s - s_f| / ((s_f - f) s)
    #    -- while the H form carries the usual small-CoC approximation.  They must
    #    agree to a hair, not exactly; at 58 mm / f2.2 / 1.5 m they differ by
    #    0.018 mm in 1474, which is 1.2e-5.  A tolerance of 0.05 mm asserts that
    #    the approximation is the only difference between them.
    f, N, c, s = 58.0, 2.2, 2.0 / PX_PER_MM, 1500.0
    H = f * f / (N * c) + f
    chk("textbook near, mm (approx form)", dn * 1000.0, H * s / (H + s - f), 0.05)
    chk("textbook far,  mm (approx form)", df * 1000.0, H * s / (H - s + f), 0.05)

    # 4. Framing: a box exactly as tall as the frame must read 1.000.
    #    frame height at range d on lens L is d * sensor_h / L.
    L, d = 58.0, 1.5
    hgt = d * (SENSOR_MM * RES[1] / RES[0]) / L
    fake = {"bbox_min": [-1e-6, -1e-6, -hgt / 2], "bbox_max": [1e-6, 1e-6, hgt / 2],
            "centre": [0, 0, 0], "size": [0, 0, hgt], "explode_offset": [0, 0, 0]}
    key = {"world": [d, 0, 0], "look_at": [0, 0, 0], "lens_mm": L, "fstop": 8.0,
           "focus_distance_m": d, "t": 0.0, "focus_target": "SELFTEST"}
    r = measure_station(fake, key)
    chk("box == frame height reads 1.000", r["extent_frac_frame_h"], 1.000, 2e-3)

    # 5. NEGATIVE CONTROL: the same box at twice the standoff must halve.
    key2 = dict(key, world=[2 * d, 0, 0], focus_distance_m=2 * d)
    r2 = measure_station(fake, key2)
    chk("same box at 2x range reads 0.500", r2["extent_frac_frame_h"], 0.500, 2e-3)

    # 6. The standoff formula reproduces the shipped focus distances.
    clusters, keys = load()
    worst = 0.0
    n = 0
    for k in keys:
        t = k.get("focus_target")
        if t not in clusters or not k.get("presentation_dir_measured"):
            continue
        n += 1
        cl = clusters[t]
        rad = 0.5 * math.sqrt(sum(v * v for v in cl["size"]))
        worst = max(worst, abs(max(rad * 1.55 + 0.42, 0.75)
                               - float(k["focus_distance_m"])))
    chk("standoff formula vs shipped focus, worst m", worst, 0.0, 1e-3)
    chk("presentation stations found", float(n), 15.0, 0.0)

    print("\nSTAGE RESULT %s selftest" % ("OK" if ok else "FAIL"))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--budget-px", type=float, default=SHARP_PX)
    ap.add_argument("--json")
    a = ap.parse_args()
    if a.selftest:
        return selftest()

    rows = run(a.budget_px)

    print("BEAT 1 PRESENTATION GATE — sharp budget %.1f px at 4K\n" % a.budget_px)
    print("%-14s %5s %5s %5s %7s | %6s %6s %5s | %7s %7s %8s %8s %6s"
          % ("cluster", "f", "lens", "fstop", "focus_m",
             "ext_h", "ext_w", "fits", "depth_m", "dof_m",
             "blur_nr", "blur_far", "sharp"))
    for r in rows:
        print("%-14s %5d %5.1f %5.2f %7.3f | %6.2f %6.2f %5s | %7.3f %7.4f "
              "%8.1f %8.1f %6.1f%%"
              % (r["cluster"], r["frame"], r["lens_mm"], r["fstop"], r["focus_m"],
                 r["extent_frac_frame_h"], r["extent_frac_frame_w"],
                 "yes" if r["fits"] else "NO",
                 r["depth_span_m"], r["dof_span_m"] or -1,
                 r["blur_near_px"], r["blur_far_px"],
                 100.0 * r["depth_frac_sharp"]))

    nfit = sum(1 for r in rows if not r["fits"])
    nfoc = sum(1 for r in rows if not r["in_focus"])
    print("\n%d/%d clusters DO NOT FIT the frame; %d/%d are NOT fully in focus"
          % (nfit, len(rows), nfoc, len(rows)))
    print("STAGE RESULT OK stations=%d nofit=%d nofocus=%d"
          % (len(rows), nfit, nfoc))
    if a.json:
        json.dump(rows, open(a.json, "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
