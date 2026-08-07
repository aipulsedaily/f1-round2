"""HOW FAR into the driving surface does a flagged object actually reach?

    /opt/blender-5.2.0-linux-x64/blender -b <scene.blend> --factory-startup \
        -P tools/placement_depth.py -- --report docs/placement_report.json \
                                       --out docs/placement_depth.json

WHY tri_pairs IS NOT AN ANSWER
------------------------------
placement_gate.py reports how many triangle pairs of an object intersect the
keep-out volume. That number answers "do these two meshes touch?" and nothing
else. It cannot tell apart:

    a pit wall correctly sitting AT the track edge, its inner face flush with
    the white line, clipped only by the gate's 0.50 m courtesy margin

    a catch fence standing 9 m INTO the racing line, which a car hits at
    280 km/h

Both report thousands of tri pairs. ARCH_PitWall reported 15,165 — the largest
number in the run — and a pit wall belongs exactly where a pit wall is. Ranking
by tri_pairs therefore puts the most-correct object at the top of the defect
list, which is worse than useless: it is actively misleading.

THE NUMBER THAT DECIDES
-----------------------
For every vertex inside the corridor's height band, find the nearest centreline
station s, take the lateral offset u from the centreline, and compute

    intrusion = half_width(s) - |u|

    intrusion > 0   the object is INSIDE the driving surface -> real defect
    intrusion ~ 0   flush with the track edge -> correct for walls, kerbs, verges
    intrusion < 0   outside the surface entirely -> gate margin false positive

That is a physical distance in metres. It is directly actionable ("move this
1.4 m outboard"), it ranks defects by how badly they matter, and it cannot be
gamed by an object simply having a dense mesh.

PERFORMANCE
-----------
The first version of this scan was `min(points, key=...)` over ~1800 centreline
stations for every vertex — 180 million Python-level operations for the pit wall
alone. That is the same nested-loop mistake that made the first placement gate
unable to run at all. Nearest-station lookup goes through mathutils.kdtree,
which is a C-side O(log n) query.
"""

import argparse
import json
import math
import os
import sys

import bpy
from mathutils import Vector
from mathutils.kdtree import KDTree

# Imported by path, not by package: this runs inside Blender's interpreter with
# whatever cwd the caller happened to have.
if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gate_exit                                                 # noqa: E402
import report_repro as _repro                                   # noqa: E402

R2 = "/home/zany/f1-round2"

# Objects whose job is to define the track edge. These are EXPECTED to measure
# an intrusion near zero; that is them being correctly placed, not a defect.
# Anything here still fails if it reaches meaningfully INTO the surface.
EDGE_FAMILIES = ("DR_Kerb", "BR_Subbase", "BR_Verge", "ARCH_PitWall",
                 "ARCH_RetainEdge", "SURF_Kerb")

# How far in something may reach before it is called a defect. 50 mm is the
# width of a paint line — below that, an object is flush with the edge within
# the tolerance the geometry itself was built to.
INTRUSION_TOL = 0.05


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--report", default=os.path.join(R2, "docs/placement_report.json"))
    p.add_argument("--out", required=True)
    p.add_argument("--spec", default=os.path.join(R2, "docs/circuit_spec.json"))
    p.add_argument("--zhi", type=float, default=4.50)
    p.add_argument("--zlo", type=float, default=-0.60)
    # DEFECT #97, THE CONSUMER SIDE.  `placement_gate.py` stamps its reports
    # now, but this tool read `rep["violations"]` without ever asking what the
    # report measured -- so a four-day-old file computed exactly as smoothly
    # as a fresh one, and the numbers came out looking identical.  R2-735
    # settled an argument between three such reports by mtime and by
    # byte-comparing rows, and found the NEWEST of them was the stale one.
    # A stamp nobody checks is a header; this is the check.
    p.add_argument("--allow-unstamped", default=None, metavar="WHY",
                   help="proceed on a report with no provenance stamp, "
                        "recording the reason in the output. Every placement "
                        "report written before 2026-08-04 needs this.")
    return p.parse_args(argv)


def centreline(spec, step=1.0):
    """Dense centreline stations, straight off the spec's elements."""
    out = []
    for el in spec["elements"]:
        x0, y0 = el["start_world"][0], el["start_world"][1]
        h0 = math.radians(el["heading_world_deg"])
        L, s0 = el["length_m"], el["s_start"]
        R, turn = el.get("radius_m"), el.get("turn_deg")
        n = max(int(L / step), 1)
        for i in range(n):
            t = i * L / n
            if el["type"] == "S" or not R:
                x, y = x0 + math.cos(h0) * t, y0 + math.sin(h0) * t
            else:
                sg = 1.0 if (turn or 0) >= 0 else -1.0
                h = h0 + sg * t / R
                cx = x0 - sg * R * math.sin(h0)
                cy = y0 + sg * R * math.cos(h0)
                x = cx + sg * R * math.sin(h)
                y = cy - sg * R * math.cos(h)
            out.append((s0 + t, x, y))
    return out


def half_width_fn(spec):
    sys.path.insert(0, os.path.join(R2, "world"))
    try:
        import world_contract as WC
        if hasattr(WC, "half_width"):
            return WC.half_width
    except Exception:
        pass
    return lambda s: spec.get("track_section", {}).get("width_m", 14.0) * 0.5


def main():
    a = parse_args()
    spec = json.load(open(a.spec))
    hw = half_width_fn(spec)

    stations = centreline(spec, step=1.0)
    kd = KDTree(len(stations))
    for i, (_s, x, y) in enumerate(stations):
        kd.insert((x, y, 0.0), i)
    kd.balance()
    print(f">> centreline: {len(stations)} stations in a KD-tree")

    # Refuses an unstamped report unless the caller says out loud why that is
    # acceptable here.  See tools/report_repro.py.
    rep = _repro.require(a.report, a.allow_unstamped)
    names = []
    for v in rep["violations"]:
        if v["object"] not in names:
            names.append(v["object"])
    print(f">> measuring {len(names)} flagged objects")

    deps = bpy.context.evaluated_depsgraph_get()
    rows = []
    for nm in names:
        ob = bpy.data.objects.get(nm)
        if ob is None or ob.type != "MESH":
            print(f"   (skip {nm}: not a mesh in this scene)")
            continue
        oe = ob.evaluated_get(deps)
        try:
            me = oe.to_mesh()
        except Exception:
            continue
        if me is None:
            continue
        mw = ob.matrix_world
        worst, worst_s, worst_p, nverts = -1e9, None, None, 0
        for v in me.vertices:
            p = mw @ v.co
            if p.z > a.zhi or p.z < a.zlo:
                continue                       # above/below the corridor band
            nverts += 1
            _co, idx, _d = kd.find((p.x, p.y, 0.0))
            s, cx, cy = stations[idx]
            u = math.hypot(p.x - cx, p.y - cy)
            intr = hw(s) - u
            if intr > worst:
                worst, worst_s, worst_p = intr, s, (p.x, p.y, p.z)
        oe.to_mesh_clear()
        if worst_s is None:
            print(f"   (skip {nm}: no vertices in the corridor height band)")
            continue
        edge = nm.startswith(EDGE_FAMILIES)
        rows.append({"object": nm, "max_intrusion_m": round(worst, 4),
                     "at_s": round(worst_s, 1),
                     "at_world": [round(c, 3) for c in worst_p],
                     "half_width_m": round(hw(worst_s), 3),
                     "verts_in_band": nverts,
                     "edge_family": edge,
                     "defect": bool(worst > INTRUSION_TOL and not edge)})

    rows.sort(key=lambda r: -r["max_intrusion_m"])
    defects = [r for r in rows if r["defect"]]
    edge_ok = [r for r in rows if r["edge_family"]]
    fp = [r for r in rows if not r["defect"] and not r["edge_family"]]

    json.dump({"rows": rows, "n_defects": len(defects),
               "n_edge_family": len(edge_ok), "n_false_positive": len(fp),
               "intrusion_tol_m": INTRUSION_TOL},
              open(a.out, "w"), indent=1)

    print(f"\n{'object':<34}{'intrusion':>12}{'half_w':>9}{'at s':>8}   class")
    for r in rows:
        if r["defect"]:
            cls = "*** IN THE DRIVING SURFACE"
        elif r["edge_family"]:
            cls = ("edge family, flush (correct)" if r["max_intrusion_m"] <= INTRUSION_TOL
                   else f"EDGE FAMILY BUT {r['max_intrusion_m']:.2f} m IN -- check")
        else:
            cls = "outside surface (gate margin only)"
        print(f"  {r['object']:<32}{r['max_intrusion_m']:>+11.3f} m"
              f"{r['half_width_m']:>8.2f}{r['at_s']:>8.0f}   {cls}")

    print(f"\n>> {len(defects)} REAL defects, {len(edge_ok)} edge-family, "
          f"{len(fp)} margin-only false positives, of {len(rows)} flagged")
    if not rows:
        # Nothing was flagged by the upstream gate, so this tool re-measured
        # nothing. Reporting DEPTH_CLEAN off an empty input set is a pass
        # nobody earned.
        print(">> REFUSING TO REPORT: the input report flagged no objects, so "
              "this tool re-measured nothing. That is NOT a pass.")
        return gate_exit.verdict("DEPTH_VACUOUS")
    if not defects:
        return gate_exit.verdict("DEPTH_CLEAN")
    return gate_exit.verdict("DEPTH_FAIL", " (%d)" % len(defects))


if __name__ == "__main__":
    # Blender 5.2 returns 0 for a script that raised; guard() makes the verdict
    # main() returns the process status, and an exception a status 2.
    gate_exit.guard(main, tool="placement_depth")
