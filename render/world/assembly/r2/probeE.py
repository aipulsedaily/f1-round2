"""PROBE E — the barrier-foot baseline, done properly.

Probe A's first attempt took the TOPMOST hit at each barrier node, which at a
barrier node is the barrier itself (p50 came out at +0.998 m, i.e. the 1.012 m
Armco).  The question is the GROUND under the foot, so structural barriers,
dressing and vegetation are excluded from the search.

  P4  ground_z - node_z at every barrier node   (baseline p50 -10.8 mm,
      within 40 mm 94.94 %, n 1896)
  and the same nodes' Armco top vs the ground it stands on (baseline: 1.020 /
  1.014 m of a 1.012 m Armco showing).
"""
import os
exec(open(os.path.expanduser("~/f1-round2/render/world/assembly/r2/lib_probe.py")).read())

# ------------------------------------------------- WHERE THIS PROBE WRITES --
# Was `save("probeE.json", ...)`. `save()` joins its argument onto
# lib_probe's hardcoded OUT_DIR, so this probe could only ever write to
# probeE.json in the assembly root, whatever it was asked for.
# v120/battery.sh and v121/battery.sh BOTH run this probe with no
# output argument at all, so the v121 run overwrote the probeE.json that
# v120/collect.py reads, and the two versions were then compared
# against each other. Cross-version contamination by design.
#
# It now takes `--out PATH` (a bare positional *.json still works for the
# older chain scripts) and REFUSES to run without one. resolve_out() never
# invents a destination and never strips the directory off the one it was
# given -- the three faults probe_pitexit.py had at once.
OUT = resolve_out(sys.argv, blend_path=(bpy.data.filepath or None),
                  tool="probeE")
print("[E] output ->", OUT)

# Blender 5.2 returns 0 for a script that raised, so a probe that died halfway
# was indistinguishable from one that finished.  install() arms sys.excepthook
# and an atexit sentinel; done() on the last line disarms it.
sys.path.insert(0, os.path.expanduser("~/f1-round2/tools"))
import gate_exit                                                 # noqa: E402
gate_exit.install(tool="probeE")


R = {}
T0 = time.time()

hide(lambda o: o.type == "MESH" and role(o.name) in
     ("vegetation", "dressing", "barrier_struct"))
D = dg()

import build_barriers as BB

recs = []
skips = {"bnone": 0, "blocked": 0, "noground": 0}
for side in (+1, -1):
    nodes = BB.barrier_nodes(side)
    P = np.asarray(BB.W3(nodes["P"]), float)   # design frame -> world
    SS = np.asarray(nodes["s"], float)
    btyp = np.asarray(C.barrier_type(SS, side))
    try:
        blocked = np.asarray(BB.barrier_blocked(SS, side))
    except Exception:
        blocked = np.zeros(len(SS), bool)
    step = max(1, len(P) // 1000)
    for i in range(0, len(P), step):
        if btyp[i] == C.B_NONE:
            skips["bnone"] += 1; continue
        if bool(np.atleast_1d(blocked)[i]):
            skips["blocked"] += 1; continue
        px, py, pz = float(P[i][0]), float(P[i][1]), float(P[i][2])
        z, nm = top_hit(px, py, D=D)
        if z is None:
            skips["noground"] += 1; continue
        recs.append({"s": round(float(SS[i]), 1), "side": side,
                     "node_z": round(pz, 4), "ground": round(float(z), 4),
                     "ground_obj": nm,
                     "ground_minus_node": round(float(z) - pz, 4)})

g = [r["ground_minus_node"] for r in recs]
R["P4_barrier_feet"] = {
    "method": "topmost GROUND surface under each barrier node "
              "(structural barriers, dressing and vegetation hidden)",
    "nodes_measured": len(recs),
    "skips": skips,
    "ground_minus_node_z": stats(g, 4),
    "ground_minus_node_z_mm": {k: (round(v * 1000, 2) if isinstance(v, float) else v)
                               for k, v in stats(g, 4).items()},
    "within_40mm_pct": round(100.0 * sum(1 for v in g if abs(v) <= 0.040)
                             / max(1, len(g)), 2),
    "within_150mm_pct": round(100.0 * sum(1 for v in g if abs(v) <= 0.150)
                              / max(1, len(g)), 2),
    "ground_obj_histogram": {},
    "worst": sorted(recs, key=lambda r: -abs(r["ground_minus_node"]))[:15],
    "was": "p50 -0.0108 m (-10.8 mm), within 40 mm 94.94 %, n 1896",
    "secs": round(time.time() - T0, 1)}
h = {}
for r in recs:
    h[r["ground_obj"]] = h.get(r["ground_obj"], 0) + 1
R["P4_barrier_feet"]["ground_obj_histogram"] = dict(
    sorted(h.items(), key=lambda kv: -kv[1])[:12])
print("[E] P4 feet: n=%d  p50 %.1f mm  p05 %.1f  p95 %.1f  within40 %.2f%%"
      % (len(recs), 1000 * np.percentile(g, 50), 1000 * np.percentile(g, 5),
         1000 * np.percentile(g, 95), R["P4_barrier_feet"]["within_40mm_pct"]))
sys.stdout.flush()

# ---- how much Armco is showing above the ground it stands on ---------------
show_all()
hide(lambda o: o.type == "MESH" and role(o.name) in ("vegetation", "dressing"))
D2 = dg()
showing = []
for side in (+1, -1):
    nodes = BB.barrier_nodes(side)
    P = np.asarray(BB.W3(nodes["P"]), float)   # design frame -> world
    SS = np.asarray(nodes["s"], float)
    btyp = np.asarray(C.barrier_type(SS, side))
    try:
        blocked = np.asarray(BB.barrier_blocked(SS, side))
    except Exception:
        blocked = np.zeros(len(SS), bool)
    step = max(1, len(P) // 800)
    for i in range(0, len(P), step):
        if btyp[i] != C.B_ARMCO:
            continue
        if bool(np.atleast_1d(blocked)[i]):
            continue
        px, py = float(P[i][0]), float(P[i][1])
        st = stack(px, py, D=D2, maxhits=10)
        top = None; gnd = None
        for z, nm in st:
            if role(nm) == "barrier_struct" and top is None:
                top = z
            if role(nm) in GROUND_ROLES and gnd is None:
                gnd = z
        if top is not None and gnd is not None:
            showing.append({"s": round(float(SS[i]), 1), "side": side,
                            "showing": round(float(top - gnd), 4)})
sv = [x["showing"] for x in showing]
R["P4_armco_showing"] = {
    "nodes": len(showing), "design_top_m": 1.012, "showing_m": stats(sv, 4),
    "within_100mm_of_design_pct": round(100.0 * sum(
        1 for v in sv if abs(v - 1.012) <= 0.100) / max(1, len(sv)), 2),
    "worst_low": sorted(showing, key=lambda x: x["showing"])[:10],
    "was": "p50 1.055 m, 85.9 % within 100 mm of 1.012 m; worst_low 0.795 m at "
           "s=904.8 which was BR_Armco_L03 standing on the racing surface"}
print("[E] armco showing: n=%d p50 %.3f m within100mm %.2f%%"
      % (len(showing), np.percentile(sv, 50) if sv else -1,
         R["P4_armco_showing"]["within_100mm_of_design_pct"]))

R["total_secs"] = round(time.time() - T0, 1)
write_out(OUT, R)
print("[E] DONE %.1fs" % R["total_secs"])
gate_exit.done()
