#!/usr/bin/env python3
"""DOES EVERY BEAT-1 CLUSTER STILL READ ON SCREEN AFTER THE CAMERA CHANGED?

    .venv/bin/python tools/beat1_part_framing.py --path <rig>_path.json \
        [--vs <other>_path.json] [--anim world/R2829_beat1_anim_anim.json] \
        [--json out.json] [--selftest]

WHY THIS EXISTS (R2-2761, #29)
------------------------------------------------------------------------------
Beat 1's assembly animation was authored against a camera that has since moved,
and the standing instruction is the right one: *a part that read well under the
old camera may be off-screen or edge-clipped under the new one -- MEASURE that
rather than assuming it.*  Every instrument already on the project answers a
neighbouring question and not this one:

    tools/beat1_present_gate.py   the 15 PRESENTATION keys only, and only at
                                  each cluster's EXPLODED position -- it cannot
                                  see a cluster in flight or after it seats
    tools/beat1_true_extent.py    the assembled CAR box, one subject, and its
                                  own docstring says it is only authoritative
                                  after the corners seat
    tools/screen_presence.py      needs a Blender-produced point cloud and
                                  ASSUMES STATIC GEOMETRY, which is the one
                                  thing 616 flying parts are not
    tools/r2401_part_mask.py      true per-part pixels, but it renders

So this one takes the moving cluster boxes and the per-frame camera, and reports
where each cluster sits in the FRAME, every frame it is alive, in half-frames --
the unit `sheet.aim.frame_margin` fails at (0.92) and the unit R2-2161 chose for
beat 5, so an author reads back the number the gate reads.

WHAT IT IS A MODEL OF, STATED PLAINLY
------------------------------------------------------------------------------
The flight is Blender F-curve keys: `exploded` at `start_f`, a small overshoot at
`land_f`, `seated` at `land_f + settle` (anim/build_beat1_anim.py:135-165).  This
file does not open the blend, so the curve BETWEEN those keys is a model of
Blender's AUTO_CLAMPED bezier, not the bezier.  Two models are therefore
evaluated -- `smooth` (smoothstep, what AUTO_CLAMPED approximates) and `linear`
-- and any verdict that differs between them is reported as UNRESOLVED rather
than settled, because the two bracket the real curve.  A conclusion that
survives both does not depend on the model.

The cluster AABB is translated, not re-fitted: the flight also spins each part
+-4.5 deg about the offset direction, which can push a corner a few centimetres
outside a translated box.  That is a bias TOWARD calling something on-screen, so
it is bounded by `--rot-pad`, which inflates the box by the arc a point at the
box's own radius sweeps through 4.5 deg.  Default on.

WHAT A VERDICT MEANS
------------------------------------------------------------------------------
    inside      the whole cluster box is within +-0.92 half-frames
    edge        the box crosses 0.92 but its CENTRE is still in frame -- the
                cluster is clipped by the frame edge
    off         the box centre is outside the frame, or behind the lens

`--vs` runs a second path and reports only the frames whose verdict CHANGED,
which is the actual question: not "is this shot well framed" but "did my change
take something away that was there before".
"""
import argparse
import json
import math
import os
import sys

FPS = 24.0
SENSOR_W_MM = 36.0
RENDER_ASPECT = 2160.0 / 3840.0
R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The gate's own failure point, in half-frames (docs/beat_sheet.json aim.frame_margin).
FRAME_MARGIN = 0.92
# anim/build_beat1_anim.py defaults.
FLIGHT_S = 1.55
SETTLE_FRAMES = 3
STAGGER_FRAMES = 8.0
SPIN_DEG = 4.5


def cam_basis(q):
    """right/up/forward in world from a Blender quaternion [w, x, y, z]."""
    w, x, y, z = q
    xx, yy, zz = x * x, y * y, z * z
    right = (1 - 2 * (yy + zz), 2 * (x * y + w * z), 2 * (x * z - w * y))
    up = (2 * (x * y - w * z), 1 - 2 * (xx + zz), 2 * (y * z + w * x))
    fwd = (-(2 * (x * z + w * y)), -(2 * (y * z - w * x)), -(1 - 2 * (xx + yy)))
    return right, up, fwd


def smoothstep(u):
    u = max(0.0, min(1.0, u))
    return u * u * (3.0 - 2.0 * u)


def cluster_offset_scale(f, start_f, land_f, mode):
    """How much of `explode_offset` is still applied at frame `f`.

    1.0 = fully exploded, 0.0 = seated.  Before `start_f` the part is not yet
    keyed and sits at its exploded position; after `land_f` it is home (the
    overshoot is <= 45 mm and is ignored, which is 0.6 % of the smallest cluster
    offset and cannot move a framing verdict).
    """
    if f <= start_f:
        return 1.0
    if f >= land_f:
        return 0.0
    u = (f - start_f) / float(max(land_f - start_f, 1))
    return 1.0 - (smoothstep(u) if mode == "smooth" else u)


def project_box(cam, q, lens_mm, lo, hi):
    """The box's extent in the picture, in HALF-FRAMES: (max|u|, max|v|, centre).

    Returns None if any corner is at or behind the lens plane -- a box straddling
    the camera has no finite screen extent and must not be silently clamped.
    """
    right, up, fwd = cam_basis(q)
    lens = max(lens_mm, 1e-6)
    half_w = 0.5 * SENSOR_W_MM / lens
    half_h = 0.5 * SENSOR_W_MM * RENDER_ASPECT / lens
    us, vs = [], []
    for cx in (lo[0], hi[0]):
        for cy in (lo[1], hi[1]):
            for cz in (lo[2], hi[2]):
                w = (cx - cam[0], cy - cam[1], cz - cam[2])
                fz = sum(w[i] * fwd[i] for i in range(3))
                if fz <= 1e-6:
                    return None
                fx = sum(w[i] * right[i] for i in range(3))
                fy = sum(w[i] * up[i] for i in range(3))
                us.append((fx / fz) / half_w)
                vs.append((fy / fz) / half_h)
    cu, cv = 0.5 * (min(us) + max(us)), 0.5 * (min(vs) + max(vs))
    return max(abs(min(us)), abs(max(us))), max(abs(min(vs)), abs(max(vs))), (cu, cv)


def verdict(proj):
    if proj is None:
        return "off"
    hu, hv, (cu, cv) = proj
    if hu <= FRAME_MARGIN and hv <= FRAME_MARGIN:
        return "inside"
    if abs(cu) <= 1.0 and abs(cv) <= 1.0:
        return "edge"
    return "off"


def load_clusters(plan_path, anim_path, rot_pad=True):
    plan = json.load(open(plan_path))
    anim = json.load(open(anim_path))
    by_name = {c["name"]: c for c in plan["clusters"]} if \
        isinstance(plan["clusters"], list) and "name" in plan["clusters"][0] else None
    if by_name is None:
        # the plan stores clusters as a list of dicts keyed elsewhere, or a dict
        cl = plan["clusters"]
        by_name = cl if isinstance(cl, dict) else {c.get("name", str(i)): c
                                                   for i, c in enumerate(cl)}
    out = []
    for name, meta in anim["clusters"].items():
        c = by_name.get(name)
        if c is None:
            continue
        lo, hi = list(c["bbox_min"]), list(c["bbox_max"])
        if rot_pad:
            # a point at the box's own radius sweeps this far through SPIN_DEG
            rad = 0.5 * math.dist(lo, hi)
            pad = rad * math.radians(SPIN_DEG)
            lo = [v - pad for v in lo]
            hi = [v + pad for v in hi]
        land_f = int(meta["last_land"])           # the LAST part of the cluster
        start_f = max(int(meta["first_land"]) - int(round(FLIGHT_S * FPS)), 1)
        out.append({"name": name, "lo": lo, "hi": hi,
                    "off": list(c["explode_offset"]),
                    "start_f": start_f, "land_f": land_f,
                    "parts": meta.get("parts", c.get("n_parts"))})
    return sorted(out, key=lambda c: c["start_f"])


def run(path_json, clusters, mode, f_lo, f_hi):
    P = {int(e["f"]): e for e in path_json["path"]}
    res = {}
    for c in clusters:
        lo_f = max(f_lo, c["start_f"])
        hi_f = min(f_hi, c["land_f"] + SETTLE_FRAMES)
        rows = {}
        for f in range(lo_f, hi_f + 1):
            e = P.get(f)
            if e is None:
                continue
            s = cluster_offset_scale(f, c["start_f"], c["land_f"], mode)
            lo = [c["lo"][i] + c["off"][i] * s for i in range(3)]
            hi = [c["hi"][i] + c["off"][i] * s for i in range(3)]
            pr = project_box(e["p"], e["q"], e["lens"], lo, hi)
            rows[f] = {"v": verdict(pr),
                       "hu": None if pr is None else round(pr[0], 4),
                       "hv": None if pr is None else round(pr[1], 4)}
        res[c["name"]] = rows
    return res


def summarise(res, label):
    print(">> %s — every beat-1 cluster, every frame it is alive" % label)
    print("   %-14s %6s %6s-%-6s %7s %7s %7s   %8s %8s"
          % ("cluster", "parts", "f0", "f1", "inside", "edge", "off",
             "max hu", "max hv"))
    tot = {"inside": 0, "edge": 0, "off": 0}
    for name, rows in res.items():
        if not rows:
            continue
        cnt = {"inside": 0, "edge": 0, "off": 0}
        for r in rows.values():
            cnt[r["v"]] += 1
            tot[r["v"]] += 1
        hus = [r["hu"] for r in rows.values() if r["hu"] is not None]
        hvs = [r["hv"] for r in rows.values() if r["hv"] is not None]
        fs = sorted(rows)
        print("   %-14s %6s %6d-%-6d %7d %7d %7d   %8.3f %8.3f"
              % (name, "-", fs[0], fs[-1], cnt["inside"], cnt["edge"], cnt["off"],
                 max(hus) if hus else float("nan"),
                 max(hvs) if hvs else float("nan")))
    print("   %-14s %6s %13s %7d %7d %7d"
          % ("TOTAL", "", "", tot["inside"], tot["edge"], tot["off"]))
    return tot


def compare(a, b, label_a, label_b):
    """Only the frames whose verdict CHANGED. That is the question #29 asks."""
    print(">> CHANGED FRAMES — %s -> %s" % (label_a, label_b))
    worse = better = 0
    rank = {"inside": 0, "edge": 1, "off": 2}
    for name in a:
        rows_a, rows_b = a[name], b.get(name, {})
        runs = []
        for f in sorted(set(rows_a) & set(rows_b)):
            va, vb = rows_a[f]["v"], rows_b[f]["v"]
            if va != vb:
                runs.append((f, va, vb))
                if rank[vb] > rank[va]:
                    worse += 1
                else:
                    better += 1
        if runs:
            f0, f1 = runs[0][0], runs[-1][0]
            kinds = sorted({"%s->%s" % (r[1], r[2]) for r in runs})
            print("   %-14s %4d frames  f%d-%d  %s"
                  % (name, len(runs), f0, f1, ", ".join(kinds)))
    if not worse and not better:
        print("   none — every cluster holds the same verdict on every frame")
    else:
        print("   %d frame(s) WORSE, %d frame(s) better" % (worse, better))
    return worse, better


def selftest():
    """A gate that has never failed has not been shown to work."""
    ok = True
    # negative control: a path compared with itself must report zero changes
    path = {"frames": 2, "path": [
        {"f": 1, "p": [0, -10, 2], "q": [0.7071, 0.7071, 0, 0], "lens": 35.0},
        {"f": 2, "p": [0, -10, 2], "q": [0.7071, 0.7071, 0, 0], "lens": 35.0}]}
    cl = [{"name": "T", "lo": [-1, -1, 0], "hi": [1, 1, 1], "off": [0, 0, 0],
           "start_f": 1, "land_f": 2, "parts": 1}]
    a = run(path, cl, "smooth", 1, 2)
    w, b = compare(a, a, "self", "self")
    if (w, b) != (0, 0):
        print("!! negative control FAILED: %d/%d changes against itself" % (w, b))
        ok = False
    # positive control: turn the camera 180 deg and everything must go off
    back = {"frames": 2, "path": [
        {"f": 1, "p": [0, -10, 2], "q": [0.0, 0.0, 0.7071, 0.7071], "lens": 35.0},
        {"f": 2, "p": [0, -10, 2], "q": [0.0, 0.0, 0.7071, 0.7071], "lens": 35.0}]}
    c = run(back, cl, "smooth", 1, 2)
    if any(r["v"] != "off" for r in c["T"].values()):
        print("!! positive control FAILED: a camera pointed away still reads %s"
              % sorted({r["v"] for r in c["T"].values()}))
        ok = False
    w2, _ = compare(a, c, "facing", "turned away")
    if w2 != 2:
        print("!! positive control FAILED: expected 2 worse frames, got %d" % w2)
        ok = False
    # a box that fills the frame must read `edge`, not `inside`
    near = [{"name": "T", "lo": [-8, -1, 0], "hi": [8, 1, 1], "off": [0, 0, 0],
             "start_f": 1, "land_f": 2, "parts": 1}]
    d = run(path, near, "smooth", 1, 2)
    if any(r["v"] == "inside" for r in d["T"].values()):
        print("!! edge control FAILED: a 16 m box at 10 m read `inside`")
        ok = False
    print(">> STAGE RESULT: %s" % ("PART_FRAMING_SELFTEST_OK" if ok
                                   else "PART_FRAMING_SELFTEST_FAIL"))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", help="a *_path.json from anim/build_camera_rig.py")
    ap.add_argument("--vs", default=None, help="a second path; report only changes")
    ap.add_argument("--plan", default=os.path.join(R2, "docs/explode_plan.json"))
    ap.add_argument("--anim", default=os.path.join(R2, "world/R2829_beat1_anim_anim.json"),
                    help="the seat schedule to judge against. NOT "
                         "world/beat1_anim_anim.json by default: that file is "
                         "the pre-R2-831 pacing and disagrees with the sheet by "
                         "60-180 frames on all 15 clusters.")
    ap.add_argument("--lo", type=int, default=1)
    ap.add_argument("--hi", type=int, default=792)
    ap.add_argument("--no-rot-pad", action="store_true")
    ap.add_argument("--json", default=None)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.path:
        ap.error("--path is required")

    clusters = load_clusters(a.plan, a.anim, rot_pad=not a.no_rot_pad)
    print(">> %d clusters from %s (seat schedule) x %s (geometry)"
          % (len(clusters), os.path.relpath(a.anim, R2),
             os.path.relpath(a.plan, R2)))
    A = json.load(open(a.path))
    out = {"path": a.path, "vs": a.vs, "models": {}}
    unresolved = []
    for mode in ("smooth", "linear"):
        ra = run(A, clusters, mode, a.lo, a.hi)
        print()
        tot = summarise(ra, "%s flight model, %s" % (mode, os.path.basename(a.path)))
        out["models"].setdefault(mode, {})["a_totals"] = tot
        if a.vs:
            B = json.load(open(a.vs))
            rb = run(B, clusters, mode, a.lo, a.hi)
            print()
            totb = summarise(rb, "%s flight model, %s" % (mode, os.path.basename(a.vs)))
            print()
            w, b = compare(ra, rb, os.path.basename(a.path), os.path.basename(a.vs))
            out["models"][mode].update({"b_totals": totb, "worse": w, "better": b})
            if w:
                unresolved.append(mode)
    if a.json:
        json.dump(out, open(a.json, "w"), indent=1)
        print(">> wrote %s" % a.json)
    if a.vs:
        ws = {m: out["models"][m].get("worse", 0) for m in out["models"]}
        if not any(ws.values()):
            print(">> STAGE RESULT: PART_FRAMING_NO_REGRESSION  (both flight "
                  "models agree: 0 frames worse)")
        elif all(ws.values()):
            print(">> STAGE RESULT: PART_FRAMING_REGRESSION  %s" % ws)
        else:
            print(">> STAGE RESULT: PART_FRAMING_UNRESOLVED  the two flight "
                  "models disagree (%s); the real bezier is between them" % ws)
    else:
        print(">> STAGE RESULT: PART_FRAMING_MEASURED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
