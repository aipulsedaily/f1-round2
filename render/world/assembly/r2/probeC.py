"""PROBE C — the nine original probes that must not regress.

  P1  terrain over the racing surface       (was 0 of 47 775 rays)
  P2  kerb + verge band buried              (was 0 buried by terrain)
  P3  runoff / gravel visible               (was terrain covers 0.00 %)
  P9  vegetation on track / runoff / gravel (was 0)
"""
import os
exec(open(os.path.expanduser("~/f1-round2/render/world/assembly/r2/lib_probe.py")).read())

# ------------------------------------------------- WHERE THIS PROBE WRITES --
# Was `save("probeC.json", ...)`. `save()` joins its argument onto
# lib_probe's hardcoded OUT_DIR, so this probe could only ever write to
# probeC.json in the assembly root, whatever it was asked for.
# v120/battery.sh and v121/battery.sh BOTH run this probe with no
# output argument at all, so the v121 run overwrote the probeC.json that
# v120/collect.py reads, and the two versions were then compared
# against each other. Cross-version contamination by design.
#
# Its mid-run checkpoints had the same fault twice over: `probeC_partial.json`
# was also a fixed name in the assembly root, shared by every version.
# They now go to `sidecar(OUT, "partial")`, i.e. beside this run's own output.
#
# It now takes `--out PATH` (a bare positional *.json still works for the
# older chain scripts) and REFUSES to run without one. resolve_out() never
# invents a destination and never strips the directory off the one it was
# given -- the three faults probe_pitexit.py had at once.
OUT = resolve_out(sys.argv, blend_path=(bpy.data.filepath or None),
                  tool="probeC")
print("[C] output ->", OUT)

# Blender 5.2 returns 0 for a script that raised, so a probe that died halfway
# was indistinguishable from one that finished.  install() arms sys.excepthook
# and an atexit sentinel; done() on the last line disarms it.
sys.path.insert(0, os.path.expanduser("~/f1-round2/tools"))
import gate_exit                                                 # noqa: E402
gate_exit.install(tool="probeC")


R = {}
T0 = time.time()

# ================================================= P1 racing surface =======
hide(lambda o: o.type == "MESH" and role(o.name) == "vegetation")
D = dg()

t = time.time()
hist = {}; notrack = []; nsamp = 0
NL = 25
for s0 in np.arange(0.0, LAP, 1.0):
    hw = float(C.half_width(np.array([s0]))[0])
    for u0 in np.linspace(-hw, hw, NL):
        x, y, _z = C.su_to_world(s0, u0)
        z, nm = top_hit(float(x), float(y), D=D)
        nsamp += 1
        r = role(nm) if nm else "NOTHING"
        hist[r] = hist.get(r, 0) + 1
        if r != "track":
            dat = float(C.ground_z(np.array([s0]), np.array([u0]))[0])
            notrack.append({"s": round(float(s0), 1), "u": round(float(u0), 2),
                            "obj": nm, "role": r,
                            "proud_m": (round(float(z) - dat, 4) if z is not None else None)})
ter = hist.get("TER_Ground", 0) + hist.get("vegetation", 0)
R["P1_racing_surface"] = {
    "grid": "1.0 m station x 25 laterals across |u| <= half_width(s)",
    "samples": nsamp,
    "topmost_role_histogram": dict(sorted(hist.items(), key=lambda kv: -kv[1])),
    "terrain_topmost": ter,
    "terrain_pct": round(100.0 * ter / max(1, nsamp), 4),
    "not_track_topmost": len(notrack),
    "not_track_pct": round(100.0 * len(notrack) / max(1, nsamp), 4),
    "barrier_struct_topmost": hist.get("barrier_struct", 0),
    "worst": sorted([n for n in notrack if n["proud_m"] is not None],
                    key=lambda n: -n["proud_m"])[:14],
    "was": "0 of 47 775 rays terrain-topmost (review baseline 5.3 %, 407/7728, "
           "max +0.381 m); 5 barrier_struct topmost = defect 1",
    "secs": round(time.time() - t, 1)}
print("[C] P1: %d samples, terrain %d (%.4f%%), barrier_struct %d, not-track %d"
      % (nsamp, ter, R["P1_racing_surface"]["terrain_pct"],
         hist.get("barrier_struct", 0), len(notrack)))
sys.stdout.flush()
write_out(sidecar(OUT, "partial"), R)

# ================================================= P2 kerb + verge =========
t = time.time()
hist2 = {}; bad = []; n2 = 0
for s0 in np.arange(0.0, LAP, 2.0):
    hw = float(C.half_width(np.array([s0]))[0])
    e = float(C.verge_edge(np.array([s0]))[0])
    for side in (+1, -1):
        for uu in np.linspace(hw + 0.05, e - 0.05, 9):
            u0 = uu * side
            x, y, _z = C.su_to_world(s0, u0)
            z, nm = top_hit(float(x), float(y), D=D)
            n2 += 1
            r = role(nm) if nm else "NOTHING"
            hist2[r] = hist2.get(r, 0) + 1
            if r not in ("track", "kerb"):
                dat = float(C.ground_z(np.array([s0]), np.array([u0]))[0])
                bad.append({"s": round(float(s0), 1), "side": side,
                            "u": round(float(uu), 2), "obj": nm, "role": r,
                            "depth_m": (round(float(z) - dat, 4) if z is not None else None)})
ter2 = hist2.get("TER_Ground", 0) + hist2.get("vegetation", 0)
R["P2_kerb_verge_band"] = {
    "grid": "2.0 m station x 9 laterals, half_width -> verge_edge, both sides",
    "samples": n2,
    "topmost_role_histogram": dict(sorted(hist2.items(), key=lambda kv: -kv[1])),
    "terrain_topmost": ter2,
    "buried_by_terrain_pct": round(100.0 * ter2 / max(1, n2), 4),
    "not_surface": len(bad),
    "not_surface_pct": round(100.0 * len(bad) / max(1, n2), 4),
    "barrier_struct_topmost": hist2.get("barrier_struct", 0),
    "examples": bad[:20],
    "was": "0 buried by terrain (review baseline 42.3 %, 1776/4198); "
           "3 barrier_struct topmost = defect 1",
    "secs": round(time.time() - t, 1)}
print("[C] P2: %d samples, terrain %d, barrier_struct %d, not-surface %d"
      % (n2, ter2, hist2.get("barrier_struct", 0), len(bad)))
sys.stdout.flush()
write_out(sidecar(OUT, "partial"), R)

# ================================================= P3 runoff / gravel ======
t = time.time()
res = {}
for band in ("asphalt", "gravel", "apex"):
    hist3 = {}; n3 = 0; covered = []
    for s0 in np.arange(0.0, LAP, 3.0):
        e = float(C.verge_edge(np.array([s0]))[0])
        for side in (+1, -1):
            w = C.runoff_widths(np.array([s0]), side)
            if band == "asphalt":
                a, b = 0.0, float(np.atleast_1d(w["asphalt"])[0])
            elif band == "gravel":
                a = float(np.atleast_1d(w["asphalt"])[0])
                b = a + float(np.atleast_1d(w["gravel"])[0])
            else:
                a, b = 0.0, float(np.atleast_1d(w["apex"])[0])
            if b - a < 0.6:
                continue
            for uu in np.linspace(a + 0.3, b - 0.3, 4):
                u0 = (e + uu) * side
                x, y, _z = C.su_to_world(s0, u0)
                z, nm = top_hit(float(x), float(y), D=D)
                n3 += 1
                r = role(nm) if nm else "NOTHING"
                hist3[r] = hist3.get(r, 0) + 1
                if r in ("TER_Ground", "vegetation"):
                    covered.append({"s": round(float(s0), 1), "side": side,
                                    "u": round(float(u0), 2), "obj": nm})
    terr = hist3.get("TER_Ground", 0) + hist3.get("vegetation", 0)
    res[band] = {"samples": n3,
                 "topmost_role_histogram": dict(sorted(hist3.items(), key=lambda kv: -kv[1])),
                 "terrain_covering": terr,
                 "terrain_pct": round(100.0 * terr / max(1, n3), 4),
                 "examples": covered[:10]}
    print("[C] P3 %s: %d samples, terrain %d (%.4f%%)"
          % (band, n3, terr, res[band]["terrain_pct"]))
R["P3_runoff_gravel"] = {"bands": res,
                         "was": "terrain covers 0.00 % of runoff/gravel/apex "
                                "(asphalt 856/856, outer gravel 924/924, apex 704/704 visible)",
                         "secs": round(time.time() - t, 1)}
sys.stdout.flush()
write_out(sidecar(OUT, "partial"), R)

# ================================================= P9 vegetation ===========
t = time.time()
show_all()
D = dg()
n_inst = 0; on_track = 0; on_runoff = 0; on_gravel = 0; offend = []
pts_x = []; pts_y = []
for inst in D.object_instances:
    ob = inst.object
    nm = ob.name if ob else ""
    if not (nm.startswith("VEG_") or nm.startswith("TER_Veg")):
        continue
    m = inst.matrix_world
    pts_x.append(m[0][3]); pts_y.append(m[1][3])
    n_inst += 1
print("[C] P9 collected %d vegetation instance points (%.1fs)"
      % (n_inst, time.time() - t))
sys.stdout.flush()
PX = np.asarray(pts_x); PY = np.asarray(pts_y)
del pts_x, pts_y
inside_cor = 0
if n_inst:
    CH = 200000
    for i in range(0, n_inst, CH):
        j = min(i + CH, n_inst)
        s, u = C.project(PX[i:j], PY[i:j])
        au = np.abs(u)
        hw = C.half_width(s); e = C.verge_edge(s)
        sd = np.where(u >= 0, 1, -1)
        wa = np.where(u >= 0, C.COR.sample("asph", s, +1), C.COR.sample("asph", s, -1))
        wg = np.where(u >= 0, C.COR.sample("grav", s, +1), C.COR.sample("grav", s, -1))
        wx = np.where(u >= 0, C.COR.sample("apex", s, +1), C.COR.sample("apex", s, -1))
        pe = np.where(u >= 0, C.platform_edge(s, +1), C.platform_edge(s, -1))
        inside_cor += int((au <= pe).sum())
        mt = au <= e                                    # track + kerb + verge
        mr = (au > e) & (au <= e + wa)                  # runoff asphalt
        mgv = (au > e + wa) & (au <= e + wa + wg)       # gravel
        mapex = (au > e) & (au <= e + wx)               # apex beds
        on_track += int(mt.sum()); on_runoff += int(mr.sum())
        on_gravel += int((mgv | mapex).sum())
        bad = mt | mr | mgv | mapex
        if bad.any():
            idx = np.nonzero(bad)[0][:10]
            for k in idx:
                offend.append({"x": round(float(PX[i + k]), 2),
                               "y": round(float(PY[i + k]), 2),
                               "s": round(float(s[k]), 1),
                               "u": round(float(u[k]), 2)})
R["P9_vegetation"] = {
    "instance_points": n_inst,
    "inside_corridor": inside_cor,
    "on_racing_surface": on_track,
    "on_runoff_asphalt": on_runoff,
    "on_gravel": on_gravel,
    "bad_total": on_track + on_runoff + on_gravel,
    "offenders": offend[:30],
    "was": "3 073 526 scatter points, 1 413 059 inside the corridor, "
           "0 on the racing surface / runoff / gravel",
    "secs": round(time.time() - t, 1)}
print("[C] P9: %d pts, corridor %d, bad %d"
      % (n_inst, inside_cor, R["P9_vegetation"]["bad_total"]))

R["total_secs"] = round(time.time() - T0, 1)
write_out(OUT, R)
print("[C] DONE %.1fs" % R["total_secs"])
gate_exit.done()
