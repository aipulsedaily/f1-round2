"""Does beat 1's focus track the CLUSTER BEING PRESENTED? Per frame, from film14.

The confounded comparison this replaces measured `focus_distance` against the
distance to `CAR_ROOT`. In beat 1 the car is EXPLODED — 616 parts on separate
trajectories — and `CAR_ROOT` is the assembled body's origin, which is not what
the lens is presenting. Distance to it says nothing about whether the focus is
right.

The reference here is the presented cluster's own evaluated world bounding box at
that frame, which is what `tools/beat1_dof_dump.py` extracts from `film14.blend`.
The presentation windows come from `docs/beat_sheet.json`'s beat-1 schedule, so
the cluster nominated at each frame is the one the beat sheet says is on screen.

Reads:  work/b1dof/dump.json           camera + cluster bboxes, per frame
        docs/beat_sheet.json           the presentation schedule

Run:    python3 tools/beat1_focus_track.py
        python3 tools/beat1_focus_track.py --frames 120,300,400,500,591,700
        python3 tools/beat1_focus_track.py --selftest
"""

import argparse
import json
import math
import os
import sys

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FPS = 24.0


def qrot(q, v):
    """Rotate v by quaternion q = (w, x, y, z)."""
    w, x, y, z = q
    t = [2 * (y * v[2] - z * v[1]),
         2 * (z * v[0] - x * v[2]),
         2 * (x * v[1] - y * v[0])]
    return [v[i] + w * t[i] + (y * t[2] - z * t[1] if i == 0 else
                               z * t[0] - x * t[2] if i == 1 else
                               x * t[1] - y * t[0]) for i in range(3)]


def cam_axes(q):
    """Blender camera looks down -Z, up +Y, right +X in its own space."""
    right = qrot(q, [1.0, 0.0, 0.0])
    up = qrot(q, [0.0, 1.0, 0.0])
    fwd = qrot(q, [0.0, 0.0, -1.0])
    return fwd, right, up


def blur_px(f, N, focus_m, s_m, px_per_mm):
    s, sf = s_m * 1000.0, focus_m * 1000.0
    if s <= f or sf <= f:
        return float("inf")
    return (f / N) * f / (sf - f) * abs(s - sf) / s * px_per_mm


def presented_at(sched, frame):
    """The cluster the beat sheet says is being presented at this frame."""
    t = (frame - 1) / FPS
    best = None
    for e in sched:
        if e["presented_t"] <= t < e["presented_until_t"]:
            best = e["cluster"]
    if best is None:
        # before the first or after the last presentation window
        if t < sched[0]["presented_t"]:
            return sched[0]["cluster"], "pre"
        if t >= sched[-1]["presented_until_t"]:
            return sched[-1]["cluster"], "closeout"
        # the gap between SW's window ending and CORNER_RR's beginning is the
        # authored EC-seating bridge; nothing is nominated there.
        return None, "bridge"
    return best, "presented"


def analyse(dump, sched, frames=None):
    sw = dump["sensor_width"]
    rx, ry = dump["res"]
    px_per_mm = rx / sw
    sh = sw * ry / rx
    geom = dump["cluster_bbox"]
    geom_frames = sorted(int(k) for k in geom)

    out = []
    for e in dump["frames"]:
        f = e["f"]
        if frames and f not in frames:
            continue
        cl, kind = presented_at(sched, f)
        gf = min(geom_frames, key=lambda g: abs(g - f))
        box = geom.get(str(gf), {}).get(cl) if cl else None
        row = {"f": f, "cluster": cl, "window": kind,
               "lens": e["lens"], "fstop": e["fstop"], "focus_m": e["focus_m"],
               "geom_frame": gf}
        if box is None:
            out.append(row)
            continue
        lo3, hi3 = box
        eye = e["p"]
        fwd, right, up = cam_axes(e["q"])
        depths, us, vs = [], [], []
        for i in (0, 1):
            for j in (0, 1):
                for k in (0, 1):
                    c = [lo3[0] if i == 0 else hi3[0],
                         lo3[1] if j == 0 else hi3[1],
                         lo3[2] if k == 0 else hi3[2]]
                    d = [c[m] - eye[m] for m in range(3)]
                    z = sum(d[m] * fwd[m] for m in range(3))
                    depths.append(z)
                    if z > 1e-6:
                        us.append(sum(d[m] * right[m] for m in range(3)) / z * e["lens"])
                        vs.append(sum(d[m] * up[m] for m in range(3)) / z * e["lens"])
        ctr = [(lo3[m] + hi3[m]) / 2 for m in range(3)]
        dc = [ctr[m] - eye[m] for m in range(3)]
        rng = math.sqrt(sum(v * v for v in dc))
        zc = sum(dc[m] * fwd[m] for m in range(3))
        offax = math.degrees(math.acos(max(-1.0, min(1.0, zc / max(rng, 1e-9)))))

        row.update({
            "range_centre_m": round(rng, 4),
            "focus_minus_range_m": round(e["focus_m"] - rng, 4),
            "depth_near_m": round(min(depths), 4),
            "depth_far_m": round(max(depths), 4),
            "off_axis_deg": round(offax, 3),
            "blur_centre_px": round(blur_px(e["lens"], e["fstop"], e["focus_m"],
                                            max(rng, 1e-3), px_per_mm), 1),
            "blur_near_px": round(blur_px(e["lens"], e["fstop"], e["focus_m"],
                                          max(min(depths), 1e-3), px_per_mm), 1),
            "blur_far_px": round(blur_px(e["lens"], e["fstop"], e["focus_m"],
                                         max(max(depths), 1e-3), px_per_mm), 1),
            "extent_frac_frame_h": (round((max(vs) - min(vs)) / sh, 3) if vs else None),
            "extent_frac_frame_w": (round((max(us) - min(us)) / sw, 3) if us else None),
            "focus_inside_cluster": bool(min(depths) <= e["focus_m"] <= max(depths)),
        })
        out.append(row)
    return out


def selftest(dump):
    """The frame geometry, checked against the path file that no part of this
    module reads, and against the film's own declared numbers."""
    ok = True

    def chk(name, got, want, tol):
        nonlocal ok
        good = abs(got - want) <= tol
        ok = ok and good
        print("  %-52s %12.6f  want %12.6f  %s"
              % (name, got, want, "ok" if good else "FAIL"))

    # 1. cam_axes must be orthonormal and right-handed for every beat-1 frame.
    worst_orth, worst_hand = 0.0, 1.0
    for e in dump["frames"]:
        f_, r_, u_ = cam_axes(e["q"])
        for a in (f_, r_, u_):
            worst_orth = max(worst_orth, abs(math.sqrt(sum(x * x for x in a)) - 1))
        worst_orth = max(worst_orth, abs(sum(r_[i] * u_[i] for i in range(3))))
        worst_orth = max(worst_orth, abs(sum(r_[i] * f_[i] for i in range(3))))
        cx = [r_[1] * u_[2] - r_[2] * u_[1],
              r_[2] * u_[0] - r_[0] * u_[2],
              r_[0] * u_[1] - r_[1] * u_[0]]
        worst_hand = min(worst_hand, -sum(cx[i] * f_[i] for i in range(3)))
    chk("camera basis orthonormality, worst error", worst_orth, 0.0, 1e-5)
    chk("right x up == -fwd (right-handed), worst", worst_hand, 1.0, 1e-5)

    # 2. The dumped camera positions must match render/film14_path.json, which
    #    was written by a different tool on a different run.
    pth = {p["f"]: p for p in json.load(
        open(os.path.join(R2, "render/film14_path.json")))["path"]}
    wp, wl = 0.0, 0.0
    for e in dump["frames"]:
        q = pth.get(e["f"])
        if not q:
            continue
        wp = max(wp, max(abs(e["p"][i] - q["p"][i]) for i in range(3)))
        wl = max(wl, abs(e["lens"] - q["lens"]))
    chk("dumped position vs film14_path.json, worst m", wp, 0.0, 1e-4)
    chk("dumped lens vs film14_path.json, worst mm", wl, 0.0, 1e-3)

    # 3. The exposure the dump read must be the film's, not a mis-graded one.
    sys.path.insert(0, os.path.join(R2, "world"))
    import film_exposure
    chk("scene exposure == FILM_EXPOSURE",
        dump["exposure"], film_exposure.FILM_EXPOSURE, 1e-6)

    # 4. NEGATIVE CONTROL. The confounded reference reproduced: distance to the
    #    ASSEMBLED body origin must disagree with the presented cluster, or this
    #    whole module is measuring the same thing under a new name.
    sched = json.load(open(os.path.join(R2, "docs/beat_sheet.json"))
                      )["beat1"]["schedule"]
    rows = [r for r in analyse(dump, sched) if r.get("range_centre_m")]
    car = [0.0, 0.0, 0.0]
    diffs = []
    for e in dump["frames"]:
        r = next((x for x in rows if x["f"] == e["f"]), None)
        if not r:
            continue
        dcar = math.dist(e["p"], car)
        diffs.append(abs(dcar - r["range_centre_m"]))
    m = sum(diffs) / len(diffs)
    print("  %-52s %12.6f  (must be LARGE)  %s"
          % ("mean |dist to CAR origin - dist to cluster|, m", m,
             "ok" if m > 0.5 else "FAIL"))
    ok = ok and m > 0.5

    print("\nSTAGE RESULT %s selftest" % ("OK" if ok else "FAIL"))
    return 0 if ok else 1


def best_moments(dump, budget_px=2.0, fill=1.0):
    """Per cluster, the BEST frame in all of beat 1 — not the frame the schedule
    nominates.

    THE SCHEDULE'S WINDOW IS NOT "ON SCREEN". A window runs from one station's
    arrival to the NEXT station's arrival, so its last frames are spent flying
    away; at f500 the cluster the window nominates (CORNER_RR) is 95.7 deg off
    axis, i.e. beside the camera. `continuity_gate` already reports 127 beat-1
    frames with the nominated cluster over 25 deg off axis. Judging focus at
    nominated frames therefore grades the camera on frames where the part is not
    in the picture at all — the same class of confound as measuring against
    CAR_ROOT, one level up.

    So this asks the question the brief actually asks: does EVERY cluster get, at
    SOME frame, a moment where it is (a) on screen, (b) whole in frame, and (c)
    sharp? A cluster with no such frame has no readable moment.
    """
    sw = dump["sensor_width"]
    rx, ry = dump["res"]
    px_per_mm = rx / sw
    sh = sw * ry / rx
    geom = dump["cluster_bbox"]
    cams = {e["f"]: e for e in dump["frames"]}
    out = {}

    for fk in sorted(geom, key=int):
        f = int(fk)
        e = cams.get(f)
        if not e:
            continue
        eye = e["p"]
        fwd, right, up = cam_axes(e["q"])
        for cl, (lo3, hi3) in geom[fk].items():
            depths, us, vs = [], [], []
            for i in (0, 1):
                for j in (0, 1):
                    for k in (0, 1):
                        c = [lo3[0] if i == 0 else hi3[0],
                             lo3[1] if j == 0 else hi3[1],
                             lo3[2] if k == 0 else hi3[2]]
                        d = [c[m] - eye[m] for m in range(3)]
                        z = sum(d[m] * fwd[m] for m in range(3))
                        depths.append(z)
                        if z > 1e-6:
                            us.append(sum(d[m] * right[m] for m in range(3)) / z * e["lens"])
                            vs.append(sum(d[m] * up[m] for m in range(3)) / z * e["lens"])
            if not us or min(depths) <= 1e-6:
                continue                       # straddles or is behind the lens
            ctr = [(lo3[m] + hi3[m]) / 2 for m in range(3)]
            dc = [ctr[m] - eye[m] for m in range(3)]
            rng = math.sqrt(sum(v * v for v in dc))
            zc = sum(dc[m] * fwd[m] for m in range(3))
            if zc <= 0:
                continue
            uc = sum(dc[m] * right[m] for m in range(3)) / zc * e["lens"]
            vc = sum(dc[m] * up[m] for m in range(3)) / zc * e["lens"]
            if abs(uc) > sw / 2 or abs(vc) > sh / 2:
                continue                       # centre is off screen
            eh = (max(vs) - min(vs)) / sh
            ew = (max(us) - min(us)) / sw
            bl = blur_px(e["lens"], e["fstop"], e["focus_m"], rng, px_per_mm)
            bn = blur_px(e["lens"], e["fstop"], e["focus_m"], max(min(depths), 1e-3),
                         px_per_mm)
            bf = blur_px(e["lens"], e["fstop"], e["focus_m"], max(depths), px_per_mm)
            rec = {"f": f, "range_m": round(rng, 3), "lens": e["lens"],
                   "fstop": e["fstop"], "focus_m": e["focus_m"],
                   "blur_centre_px": round(bl, 2), "blur_near_px": round(bn, 1),
                   "blur_far_px": round(bf, 1),
                   "ext_h": round(eh, 3), "ext_w": round(ew, 3),
                   "fits": bool(eh <= fill and ew <= fill),
                   "sharp_centre": bool(bl <= budget_px),
                   "sharp_whole": bool(max(bn, bf) <= budget_px)}
            d = out.setdefault(cl, {"onscreen": 0, "sharpest": None,
                                    "clean": None, "largest_fitting": None})
            d["onscreen"] += 1
            if d["sharpest"] is None or bl < d["sharpest"]["blur_centre_px"]:
                d["sharpest"] = rec
            if rec["fits"] and rec["sharp_centre"]:
                if d["clean"] is None or eh > d["clean"]["ext_h"]:
                    d["clean"] = rec
            if rec["fits"]:
                if d["largest_fitting"] is None or eh > d["largest_fitting"]["ext_h"]:
                    d["largest_fitting"] = rec
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--best", action="store_true",
                    help="per-cluster best readable moment across ALL of beat 1")
    ap.add_argument("--budget-px", type=float, default=2.0)
    ap.add_argument("--dump", default=os.path.join(R2, "work/b1dof/dump.json"))
    ap.add_argument("--frames", default="")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--json")
    ap.add_argument("--every", type=int, default=0)
    a = ap.parse_args()

    dump = json.load(open(a.dump))
    if a.selftest:
        return selftest(dump)

    if a.best:
        res = best_moments(dump, a.budget_px)
        order = json.load(open(os.path.join(R2, "docs/beat_sheet.json"))
                          )["beat1"]["present_order"]
        print("PER-CLUSTER BEST MOMENT IN ALL 792 FRAMES OF BEAT 1  "
              "(sharp = centre blur <= %.1f px at 4K)\n" % a.budget_px)
        print("%-14s %6s | %-32s | %-32s" %
              ("cluster", "onscr", "SHARPEST frame (blur / size)",
               "LARGEST FRAME-FITTING (blur/size)"))
        nclean = 0
        for cl in order + [c for c in res if c not in order]:
            d = res.get(cl)
            if not d:
                print("%-14s %6s | %-32s | %-32s" % (cl, 0, "NEVER ON SCREEN", "-"))
                continue
            s, g = d["sharpest"], d["largest_fitting"]
            cln = d["clean"]
            if cln:
                nclean += 1
            print("%-14s %6d | f%-5d %6.2f px  %4.2f x %4.2f | %s"
                  % (cl, d["onscreen"], s["f"], s["blur_centre_px"],
                     s["ext_h"], s["ext_w"],
                     ("f%-5d %6.2f px  %4.2f x %4.2f" %
                      (g["f"], g["blur_centre_px"], g["ext_h"], g["ext_w"]))
                     if g else "NEVER FITS THE FRAME"))
            if cln:
                print("%-14s %6s | CLEAN MOMENT f%-5d %5.2f px  %4.2f x %4.2f"
                      % ("", "", cln["f"], cln["blur_centre_px"],
                         cln["ext_h"], cln["ext_w"]))
        print("\nclusters with a CLEAN readable moment (fits the frame AND its "
              "centre is sharp): %d of %d" % (nclean, len(order)))
        print("STAGE RESULT OK clusters=%d clean=%d" % (len(order), nclean))
        if a.json:
            json.dump(res, open(a.json, "w"), indent=1)
        return 0

    sched = json.load(open(os.path.join(R2, "docs/beat_sheet.json"))
                      )["beat1"]["schedule"]
    want = None
    if a.frames:
        want = set(int(x) for x in a.frames.split(","))
    rows = analyse(dump, sched, want)
    if a.every:
        rows = [r for r in rows if r["f"] % a.every == 0 or (want and r["f"] in want)]

    print("%5s %-14s %-10s %5s %5s %8s %8s %8s | %7s %7s %7s | %6s %6s"
          % ("f", "presented", "window", "lens", "fstop", "focus_m", "range_m",
             "delta_m", "blur_nr", "blur_ct", "blur_fr", "ext_h", "ext_w"))
    for r in rows:
        if "range_centre_m" not in r:
            print("%5d %-14s %-10s %5.1f %5.2f %8.3f %8s %8s | %7s %7s %7s | %6s %6s"
                  % (r["f"], r["cluster"] or "-", r["window"], r["lens"],
                     r["fstop"], r["focus_m"], "-", "-", "-", "-", "-", "-", "-"))
            continue
        print("%5d %-14s %-10s %5.1f %5.2f %8.3f %8.3f %+8.3f | %7.1f %7.1f %7.1f "
              "| %6.2f %6.2f"
              % (r["f"], r["cluster"], r["window"], r["lens"], r["fstop"],
                 r["focus_m"], r["range_centre_m"], r["focus_minus_range_m"],
                 r["blur_near_px"], r["blur_centre_px"], r["blur_far_px"],
                 r["extent_frac_frame_h"], r["extent_frac_frame_w"]))

    have = [r for r in rows if "range_centre_m" in r]
    if have:
        worst = max(have, key=lambda r: abs(r["focus_minus_range_m"]))
        print("\nframes measured %d;  worst |focus - range to cluster centre| "
              "%.3f m at f%d (%s)"
              % (len(have), abs(worst["focus_minus_range_m"]), worst["f"],
                 worst["cluster"]))
        soft = [r for r in have if r["blur_centre_px"] > 2.0]
        print("frames whose PRESENTED CLUSTER CENTRE is blurred over 2 px: "
              "%d of %d" % (len(soft), len(have)))
        print("STAGE RESULT OK frames=%d soft_centres=%d" % (len(have), len(soft)))
    if a.json:
        json.dump(rows, open(a.json, "w"), indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
