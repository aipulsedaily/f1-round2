"""PROBE A — the barrier defects.

  D1  structural barrier/fence geometry inside verge_edge(s), WHOLE LAP
      (vertex-exhaustive + a ray sweep over the racing surface)
  D4  ground coverage across the road corridor, verge_edge -> platform_edge,
      both sides, on the review's own 2 m x 1 m grid
  D5  BR_Concrete_L13 (and anything else) standing in the Beat-4 pit-exit road
  P4  barrier feet vs the ground they stand on  (baseline p50 -10.8 mm)
"""
exec(open("/home/zany/f1-round2/render/world/assembly/r2/lib_probe.py").read())

# ------------------------------------------------- WHERE THIS PROBE WRITES --
# Was `save("probeA.json", ...)`. `save()` joins its argument onto
# lib_probe's hardcoded OUT_DIR, so this probe could only ever write to
# probeA.json in the assembly root, whatever it was asked for.
# v120/battery.sh and v121/battery.sh BOTH run this probe with no
# output argument at all, so the v121 run overwrote the probeA.json that
# v120/collect.py reads, and the two versions were then compared
# against each other. Cross-version contamination by design.
#
# Its mid-run checkpoints had the same fault twice over: `probeA_partial.json`
# was also a fixed name in the assembly root, shared by every version.
# They now go to `sidecar(OUT, "partial")`, i.e. beside this run's own output.
#
# It now takes `--out PATH` (a bare positional *.json still works for the
# older chain scripts) and REFUSES to run without one. resolve_out() never
# invents a destination and never strips the directory off the one it was
# given -- the three faults probe_pitexit.py had at once.
OUT = resolve_out(sys.argv, blend_path=(bpy.data.filepath or None),
                  tool="probeA")
print("[A] output ->", OUT)

# Blender 5.2 returns 0 for a script that raised, so a probe that died halfway
# was indistinguishable from one that finished.  install() arms sys.excepthook
# and an atexit sentinel; done() on the last line disarms it.
sys.path.insert(0, "/home/zany/f1-round2/tools")
import gate_exit                                                 # noqa: E402
gate_exit.install(tool="probeA")


R = {}
T0 = time.time()

# --------------------------------------------------------------- census ---
by_role, by_owner = {}, {}
for ob in bpy.data.objects:
    if ob.type != "MESH":
        continue
    r = role(ob.name); o = owner(ob.name)
    by_role[r] = by_role.get(r, 0) + 1
    by_owner[o] = by_owner.get(o, 0) + 1
R["census"] = {"by_role": by_role, "by_owner": by_owner,
               "objects_total": len(bpy.data.objects),
               "contract": C.__version__}
print("[A] census", json.dumps(R["census"]))

STRUCT = [ob for ob in bpy.data.objects
          if ob.type == "MESH" and role(ob.name) == "barrier_struct"]
print("[A] %d structural barrier objects" % len(STRUCT))

# ============================================================ D1 vertex ====
t = time.time()
tot = 0; inside = 0; worst = []; per_obj = {}
for ob in STRUCT:
    P = world_verts(ob)
    if P is None:
        continue
    s, u = su_of(P)
    e = C.verge_edge(s)
    d = e - np.abs(u)                     # >0 == inside the racing surface
    m = d > 1e-4
    tot += len(P); n = int(m.sum())
    if n:
        inside += n
        per_obj[ob.name] = {"n": n, "of": len(P),
                            "s_range": [round(float(s[m].min()), 1),
                                        round(float(s[m].max()), 1)],
                            "u_range": [round(float(u[m].min()), 2),
                                        round(float(u[m].max()), 2)],
                            "max_intrusion_m": round(float(d[m].max()), 3)}
    del P, s, u, e, d, m
R["D1_vertex"] = {"struct_objects": len(STRUCT),
                  "struct_verts": tot,
                  "verts_inside_verge_edge": inside,
                  "per_object": per_obj,
                  "was": "982 of 4147 sampled on BR_Armco_L03 alone; "
                         "BR_Armco_L03/L04, BR_FenceStruct_L03/L04, "
                         "BR_FenceStruct_R07",
                  "secs": round(time.time() - t, 1)}
print("[A] D1 vertex: %d of %d structural verts inside verge_edge  (%.1fs)"
      % (inside, tot, time.time() - t))
print("    ", json.dumps(per_obj)[:1500])
sys.stdout.flush()

# =========================================================== D1 ray sweep ==
# 2.0 m station x 0.5 m lateral over the whole racing surface, exactly as the
# assembly review swept it.  Everything except the surface + barriers is hidden
# so a ray that stops on a barrier is unambiguous.
t = time.time()
hide(lambda o: o.type == "MESH" and role(o.name) in
     ("vegetation", "dressing"))
D = dg()
hits = []; nsamp = 0
S = np.arange(0.0, LAP, 2.0)
for s0 in S:
    e = float(C.verge_edge(np.array([s0]))[0])
    U = np.arange(-e, e + 1e-9, 0.5)
    for u0 in U:
        x, y, _z = C.su_to_world(s0, u0)
        st = stack(float(x), float(y), D=D, maxhits=8)
        nsamp += 1
        if not st:
            continue
        # tarmac = the first track/kerb/surface hit in the stack
        tz = None
        for z, nm in st:
            if role(nm) in ("track", "kerb", "surface_other", "access"):
                tz = z; break
        for z, nm in st:
            if role(nm) == "barrier_struct":
                hits.append({"s": round(float(s0), 1), "u": round(float(u0), 2),
                             "obj": nm, "z": round(float(z), 3),
                             "above_tarmac_m": (round(float(z - tz), 3)
                                                if tz is not None else None)})
                break
h = [x["above_tarmac_m"] for x in hits if x["above_tarmac_m"] is not None]
R["D1_raysweep"] = {"samples": nsamp, "grid": "2.0 m station x 0.5 m lateral, |u| <= verge_edge",
                    "structural_hits": len(hits),
                    "area_m2": round(len(hits) * 2.0 * 0.5, 2),
                    "objects": sorted({x["obj"] for x in hits}),
                    "s_range": ([min(x["s"] for x in hits),
                                 max(x["s"] for x in hits)] if hits else None),
                    "height_above_tarmac": stats(h, 3) if h else None,
                    "examples": hits[:20],
                    "was": "51 samples / 6.4 m2 over s 904.5-1059.5, "
                           "mean 1.410 m, max 4.601 m above the tarmac",
                    "secs": round(time.time() - t, 1)}
print("[A] D1 ray sweep: %d structural hits of %d samples (%.1fs)"
      % (len(hits), nsamp, time.time() - t))
sys.stdout.flush()
write_out(sidecar(OUT, "partial"), R)

# ================================================================== D4 =====
# ground coverage across the corridor annulus, 2 m station x 1 m lateral
t = time.time()
show_all()
hide(lambda o: o.type == "MESH" and role(o.name) == "vegetation")
D = dg()
void = []; nsamp = 0; per_station = {}
for s0 in np.arange(0.0, LAP, 2.0):
    e = float(C.verge_edge(np.array([s0]))[0])
    for side in (+1, -1):
        pe = float(C.platform_edge(np.array([s0]), side)[0])
        if pe <= e:
            continue
        for uu in np.arange(e + 0.5, pe, 1.0):
            u0 = uu * side
            x, y, _z = C.su_to_world(s0, u0)
            z, nm = top_hit(float(x), float(y), D=D)
            nsamp += 1
            if z is None:
                void.append([round(float(s0), 1), side, round(float(uu), 2),
                             round(pe, 2)])
                k = round(float(s0), 1)
                per_station[k] = per_station.get(k, 0) + 1
R["D4_corridor_void"] = {
    "grid": "2.0 m station x 1.0 m lateral, verge_edge -> platform_edge, both sides",
    "samples": nsamp,
    "void_samples": len(void),
    "void_area_m2": round(len(void) * 2.0 * 1.0, 1),
    "stations_affected": len(per_station),
    "station_runs": runs(list(per_station.keys())),
    "worst_stations": sorted(((v * 2.0, k) for k, v in per_station.items()),
                             reverse=True)[:12],
    "examples": void[:40],
    "was": "658.0 m2 over 104 stations, worst T3 s 702-746 (38 m2 / station)",
    "secs": round(time.time() - t, 1)}
print("[A] D4: void %.1f m2 over %d stations of %d samples (%.1fs)"
      % (len(void) * 2.0, len(per_station), nsamp, time.time() - t))
sys.stdout.flush()
write_out(sidecar(OUT, "partial"), R)

# ================================================================== D5 =====
# anything standing above the road on the Beat-4 transit route
t = time.time()
import csv as _csv
TEL = "/home/zany/f1-round2/telemetry/telemetry.csv"
rows = []
if os.path.exists(TEL):
    with open(TEL) as f:
        for r in _csv.DictReader(f):
            rows.append(r)
print("[A] telemetry rows", len(rows), (list(rows[0].keys()) if rows else []))

blocked = []; ntest = 0
# route-parametric sweep is authoritative: the contract's own access route,
# full 12 m driving width, every 0.5 m of route
for tt in np.arange(0.0, C.ACCESS_TOTAL + 1e-9, 0.5):
    x0, y0, h0 = C.access_route_point(float(tt))
    for v in np.arange(-6.0, 6.0 + 1e-9, 0.5):
        px = x0 - math.sin(h0) * v; py = y0 + math.cos(h0) * v
        st = stack(float(px), float(py), D=D, maxhits=10)
        ntest += 1
        if not st:
            continue
        gz = None
        for z, nm in st:
            r = role(nm)
            if r in ("access", "track", "kerb", "arch", "surface_other",
                     "verge_platform", "TER_Ground", "runoff_asphalt"):
                gz = z; gn = nm; break
        for z, nm in st:
            if (role(nm) in ("barrier_struct", "dressing")
                    and gz is not None and z > gz + 0.05):
                blocked.append({"t": round(float(tt), 1), "v": round(float(v), 2),
                                "xy": [round(float(px), 2), round(float(py), 2)],
                                "obj": nm, "owner": owner(nm),
                                "above_road_m": round(float(z - gz), 3),
                                "ground": gn})
                break
byo = {}
for b in blocked:
    byo[b["obj"]] = byo.get(b["obj"], 0) + 1
R["D5_transit_road"] = {
    "grid": "0.5 m of route x 0.5 m lateral, |v| <= 6.0 m (the full 12 m road)",
    "samples": ntest,
    "blocked": len(blocked),
    "objects": dict(sorted(byo.items(), key=lambda kv: -kv[1])),
    "barriers_blocked": sum(1 for b in blocked if b["owner"] == "barriers"),
    "dressing_blocked": sum(1 for b in blocked if b["owner"] == "dressing"),
    "height_above_road": stats([b["above_road_m"] for b in blocked], 3) if blocked else None,
    "examples": blocked[:40],
    "was": "BR_Concrete_L13, 15 points blocked over route t 126-140, "
           "0.36-1.01 m above the road",
    "secs": round(time.time() - t, 1)}
print("[A] D5: %d blocked of %d  objs=%s  (%.1fs)"
      % (len(blocked), ntest, json.dumps(byo)[:300], time.time() - t))
sys.stdout.flush()
write_out(sidecar(OUT, "partial"), R)

# ============================================== P4 barrier feet baseline ===
t = time.time()
feet = None
try:
    import build_barriers as BB
    recs = []
    for side in (+1, -1):
        nodes = BB.barrier_nodes(side)
        P = np.asarray(nodes["P"], float)
        SS = np.asarray(nodes["s"], float)
        btyp = BB.WC.barrier_type(SS, side) if hasattr(BB, "WC") else None
        blocked = None
        if hasattr(BB, "barrier_blocked"):
            try:
                blocked = np.asarray(BB.barrier_blocked(SS, side))
            except Exception:
                blocked = None
        step = max(1, len(P) // 1000)
        for i in range(0, len(P), step):
            if btyp is not None and btyp[i] == C.B_NONE:
                continue
            if blocked is not None and bool(np.atleast_1d(blocked)[i]):
                continue
            px, py, pz = float(P[i][0]), float(P[i][1]), float(P[i][2])
            z, nm = top_hit(px, py, D=D)
            if z is None:
                continue
            recs.append({"s": round(float(SS[i]), 1), "side": side,
                         "node_z": round(pz, 4), "ground": round(float(z), 4),
                         "ground_obj": nm,
                         "ground_minus_node": round(float(z) - pz, 4)})
    feet = {"nodes_measured": len(recs),
            "ground_minus_node_z": stats([r["ground_minus_node"] for r in recs], 4),
            "within_40mm_pct": (round(100.0 * sum(
                1 for r in recs if abs(r["ground_minus_node"]) <= 0.040)
                / max(1, len(recs)), 2)),
            "worst": sorted(recs, key=lambda r: -abs(r["ground_minus_node"]))[:12]}
except Exception as e:
    import traceback; traceback.print_exc()
    feet = {"error": repr(e)}
feet["was"] = "p50 -0.0108 m (-10.8 mm), within 40 mm 94.94 %, n 1896"
feet["secs"] = round(time.time() - t, 1)
R["P4_barrier_feet"] = feet
print("[A] P4 feet:", json.dumps({k: v for k, v in feet.items() if k != "worst"})[:600])

R["total_secs"] = round(time.time() - T0, 1)
write_out(OUT, R)
print("[A] DONE %.1fs" % R["total_secs"])
gate_exit.done()
