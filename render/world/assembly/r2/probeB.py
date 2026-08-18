"""PROBE B — the ground-coverage / seam defects.

  D2  the corridor mouth at the glass plane: x 4-17, y +/-14, 0.10 x 0.5 m grid
  D3  the pit-exit apron edge joint at s = 3247 / 3305 / 3361 and across the bay grid
  P5  Beat-4 scan: one owner at a time, no cross-owner coplanar pairs
  P6  the corridor is built once
  P7  half width 8.000 at the pinned stations
  P8  verge seam, surface at verge_edge - 20 mm vs platform at + 20 mm
"""
import os
exec(open(os.path.expanduser("~/f1-round2/render/world/assembly/r2/lib_probe.py")).read())

# ------------------------------------------------- WHERE THIS PROBE WRITES --
# Was `save("probeB.json", ...)`. `save()` joins its argument onto
# lib_probe's hardcoded OUT_DIR, so this probe could only ever write to
# probeB.json in the assembly root, whatever it was asked for.
# v120/battery.sh and v121/battery.sh BOTH run this probe with no
# output argument at all, so the v121 run overwrote the probeB.json that
# v120/collect.py reads, and the two versions were then compared
# against each other. Cross-version contamination by design.
#
# Its mid-run checkpoints had the same fault twice over: `probeB_partial.json`
# was also a fixed name in the assembly root, shared by every version.
# They now go to `sidecar(OUT, "partial")`, i.e. beside this run's own output.
#
# It now takes `--out PATH` (a bare positional *.json still works for the
# older chain scripts) and REFUSES to run without one. resolve_out() never
# invents a destination and never strips the directory off the one it was
# given -- the three faults probe_pitexit.py had at once.
OUT = resolve_out(sys.argv, blend_path=(bpy.data.filepath or None),
                  tool="probeB")
print("[B] output ->", OUT)

# Blender 5.2 returns 0 for a script that raised, so a probe that died halfway
# was indistinguishable from one that finished.  install() arms sys.excepthook
# and an atexit sentinel; done() on the last line disarms it.
sys.path.insert(0, os.path.expanduser("~/f1-round2/tools"))
import gate_exit                                                 # noqa: E402
gate_exit.install(tool="probeB")


R = {}
T0 = time.time()

hide(lambda o: o.type == "MESH" and role(o.name) == "vegetation")
D = dg()

# ================================================================== D2 =====
# the review's own grid: x 4 -> 17 step 0.10, y -14 -> +14 step 0.5 = 7 467
t = time.time()
XS = np.arange(4.0, 17.0 + 1e-9, 0.10)
YS = np.arange(-14.0, 14.0 + 1e-9, 0.5)
print("[B] D2 grid %d x %d = %d" % (len(XS), len(YS), len(XS) * len(YS)))
nohit = 0; nsamp = 0
byx_nohit = {}; byx_deep = {}
hist = {}
worst = []
drops = []
zmap = {}
for x in XS:
    for y in YS:
        z, nm = top_hit(float(x), float(y), D=D)
        nsamp += 1
        if z is None:
            nohit += 1
            byx_nohit[round(float(x), 2)] = byx_nohit.get(round(float(x), 2), 0) + 1
            hist["NOTHING"] = hist.get("NOTHING", 0) + 1
            continue
        hist[nm] = hist.get(nm, 0) + 1
        dz, own = C.world_ground_z(float(x), float(y))
        drop = (float(dz) - float(z)) * 1000.0
        drops.append(drop)
        zmap[(round(float(x), 2), round(float(y), 2))] = (float(z), nm)
        if drop > 50.0:
            byx_deep[round(float(x), 2)] = byx_deep.get(round(float(x), 2), 0) + 1
            worst.append({"x": round(float(x), 2), "y": round(float(y), 2),
                          "z": round(float(z), 4), "datum": round(float(dz), 4),
                          "drop_mm": round(drop, 1), "obj": nm,
                          "datum_owner": own})
xopen = sorted(byx_nohit.keys())
DA = np.asarray(drops)
R["D2_glass_mouth"] = {
    "grid": "x 4.00-17.00 step 0.10 m, y -14.0-+14.0 step 0.5 m",
    "samples": nsamp,
    "no_ground_at_all": nohit,
    "no_ground_m2": round(nohit * 0.10 * 0.5, 2),
    "drop_below_datum_mm": stats(drops, 2),
    "deeper_than_5mm": int((DA > 5).sum()),
    "deeper_than_50mm": int((DA > 50).sum()),
    "deeper_than_99mm": int((DA > 99).sum()),
    "deeper_than_150mm": int((DA > 150).sum()),
    "x_columns_with_no_hit": xopen,
    "x_columns_more_than_50mm_low": sorted(byx_deep.keys()),
    "topmost_histogram": dict(sorted(hist.items(), key=lambda kv: -kv[1])),
    "worst": sorted(worst, key=lambda w: -w["drop_mm"])[:20],
    "was": "1276 of 7467 samples with NO USABLE GROUND (~64 m2); "
           "x 14.70-14.975 fully open (0.300 m x 12.75 m)",
    "secs": round(time.time() - t, 1)}
print("[B] D2: nohit %d, >50mm low %d, >150mm low %d, of %d samples (%.1fs)"
      % (nohit, int((DA > 50).sum()), int((DA > 150).sum()), nsamp, time.time() - t))

# the STEP across x = 15.000, which is where round-1's `Floor` has to land
step = []
for y in np.arange(-11.0, 11.01, 0.5):
    za, na = top_hit(14.90, float(y), D=D)
    zb, nb = top_hit(15.10, float(y), D=D)
    if za is None or zb is None:
        step.append({"y": round(float(y), 2), "step_mm": None, "a": na, "b": nb})
    else:
        step.append({"y": round(float(y), 2),
                     "step_mm": round((zb - za) * 1000.0, 2), "a": na, "b": nb})
sv = [s["step_mm"] for s in step if s["step_mm"] is not None]
R["D2_step_at_glass_plane"] = {
    "samples": len(step), "step_mm": stats(sv, 2), "rows": step[:20],
    "note": "round-1's `Floor` (top z = 0.000, x -15..15, y -11..11) is NOT in "
            "this assembly; build_architecture deliberately lays only the "
            "formation at -0.100 under it"}
print("[B] D2 step at x=15: p50 %.1f mm  min %.1f  max %.1f"
      % (R["D2_step_at_glass_plane"]["step_mm"].get("p50", 0),
         R["D2_step_at_glass_plane"]["step_mm"].get("min", 0),
         R["D2_step_at_glass_plane"]["step_mm"].get("max", 0)))

# surface's open item: x 15.0-16.5 at 6.30 < |y| <= 9.0
patch = []
for x in np.arange(15.0, 16.55, 0.10):
    for y in list(np.arange(6.30, 9.05, 0.25)) + list(np.arange(-9.0, -6.25, 0.25)):
        z, nm = top_hit(float(x), float(y), D=D)
        patch.append([round(float(x), 2), round(float(y), 2),
                      (round(float(z), 4) if z is not None else None), nm])
R["D2_pavilion_shoulder"] = {
    "samples": len(patch),
    "no_ground": sum(1 for p in patch if p[2] is None),
    "objects": sorted({p[3] for p in patch if p[3]}),
    "examples": [p for p in patch if p[2] is None][:20],
    "was": "build_surface reported x 15.0-16.5 at 6.30 < |y| <= 9.0 with no "
           "ground (architecture SKIPPED any bay overlapping the pavilion)"}
print("[B] D2 pavilion shoulder: %d of %d with no ground"
      % (R["D2_pavilion_shoulder"]["no_ground"], len(patch)))
sys.stdout.flush()

# fine 5 mm profile straight through the driving line at three y
prof = {}
for y in (0.0, 3.0, 6.0):
    row = []
    for x in np.arange(11.0, 17.0 + 1e-9, 0.005):
        z, nm = top_hit(float(x), float(y), D=D)
        row.append([round(float(x), 3), (round(float(z), 4) if z is not None else None), nm])
    prof["y=%.1f" % y] = row
R["D2_profiles_5mm"] = prof
gaps = {}
for k, row in prof.items():
    g = [r[0] for r in row if r[1] is None]
    gaps[k] = {"no_hit_samples": len(g), "x_range": ([min(g), max(g)] if g else None)}
R["D2_profile_gaps"] = gaps
print("[B] D2 profiles:", json.dumps(gaps))
write_out(sidecar(OUT, "partial"), R)

# ================================================================== D3 =====
# the pit-exit apron edge, at the review's own stations
t = time.time()
sec = {}
for s0 in (3247.0, 3305.0, 3361.0, 3210.0, 3400.0):
    e = float(C.verge_edge(np.array([s0]))[0])
    row = []
    for du in np.arange(-0.150, 0.400 + 1e-9, 0.001):
        u0 = e + du
        x, y, _z = C.su_to_world(s0, u0)
        z, nm = top_hit(float(x), float(y), D=D)
        dat = float(C.ground_z(np.array([s0]), np.array([u0]))[0])
        row.append([round(float(du), 4),
                    (round(float(z), 5) if z is not None else None), nm,
                    (round(float(dat - z) * 1000.0, 2) if z is not None else None)])
    drops = [r[3] for r in row if r[3] is not None]
    sec["s=%.0f" % s0] = {"verge_edge": round(e, 4),
                          "no_hit": sum(1 for r in row if r[1] is None),
                          "max_drop_mm": (round(max(drops), 2) if drops else None),
                          "profile": row}
R["D3_apron_edge_1mm"] = {
    "stations": sec,
    "was": "ray fell 0.300 m to the sub-base at u 10.500-10.512 "
           "(SURF_Track ends 10.500, first bay starts 10.512)",
    "secs": round(time.time() - t, 1)}
for k, v in sec.items():
    print("[B] D3 %s verge_edge %.4f  max drop %.2f mm  no_hit %d"
          % (k, v["verge_edge"], (v["max_drop_mm"] or 0), v["no_hit"]))
sys.stdout.flush()

# the whole apron: a dense off-grid sweep looking for open bay joints
t = time.time()
cols = []; nb = 0
for s0 in np.arange(3196.0, 3405.0, 0.37):
    e = float(C.verge_edge(np.array([s0]))[0])
    if float(C.apron_zone(np.array([s0]), +1)[0]) <= 0.5:
        continue
    for du in np.arange(0.02, 12.0, 0.23):
        u0 = e + du
        x, y, _z = C.su_to_world(s0, u0)
        z, nm = top_hit(float(x), float(y), D=D)
        nb += 1
        if z is None:
            cols.append({"s": round(float(s0), 2), "du": round(float(du), 3),
                         "drop_mm": None, "obj": None})
            continue
        dat = float(C.ground_z(np.array([s0]), np.array([u0]))[0])
        cols.append({"s": round(float(s0), 2), "du": round(float(du), 3),
                     "drop_mm": round((dat - float(z)) * 1000.0, 2), "obj": nm})
dr = [c["drop_mm"] for c in cols if c["drop_mm"] is not None]
R["D3_apron_sweep"] = {
    "columns": nb,
    "no_ground": sum(1 for c in cols if c["drop_mm"] is None),
    "drop_below_datum_mm": stats(dr, 2),
    "deeper_than_50mm": sum(1 for d in dr if d > 50),
    "deeper_than_100mm": sum(1 for d in dr if d > 100),
    "deeper_than_250mm": sum(1 for d in dr if d > 250),
    "worst": sorted([c for c in cols if c["drop_mm"] is not None],
                    key=lambda c: -c["drop_mm"])[:20],
    "was": "26 mm open joint on the 2.4 x 3.0 m bay grid; 12.75 % of columns "
           "low, p99 386.0 mm, max 392.5 mm",
    "secs": round(time.time() - t, 1)}
print("[B] D3 sweep: %d cols, p99 %.1f mm, max %.1f mm, >50mm %d (%.1fs)"
      % (nb, R["D3_apron_sweep"]["drop_below_datum_mm"].get("p99", 0),
         R["D3_apron_sweep"]["drop_below_datum_mm"].get("max", 0),
         R["D3_apron_sweep"]["deeper_than_50mm"], time.time() - t))
sys.stdout.flush()
write_out(sidecar(OUT, "partial"), R)

# =============================================== P5 Beat-4 scan / coplanar ==
t = time.time()
changes = []; copl = []; unowned = 0; pts = 0; stackrec = []
prev = None
for tt in np.arange(0.0, C.ACCESS_TOTAL + 1e-9, 1.0):
    x0, y0, h0 = C.access_route_point(float(tt))
    for v in (-4.0, -2.0, 0.0, 2.0, 4.0):
        px = x0 - math.sin(h0) * v; py = y0 + math.cos(h0) * v
        st = stack(float(px), float(py), D=D, maxhits=10)
        pts += 1
        if not st:
            unowned += 1
            continue
        if v == 0.0:
            top = st[0][1]
            if prev is not None and top != prev:
                changes.append({"t": round(float(tt), 1), "frm": prev, "to": top})
            prev = top
            stackrec.append([round(float(tt), 1), round(float(px), 2),
                             round(float(py), 2), top, round(float(st[0][0]), 4),
                             len(st)])
        for i in range(len(st)):
            for j in range(i + 1, len(st)):
                if abs(st[i][0] - st[j][0]) < C.TOL_COPLANAR_M:
                    if owner(st[i][1]) != owner(st[j][1]):
                        copl.append({"t": round(float(tt), 1), "v": v,
                                     "a": st[i][1], "b": st[j][1],
                                     "dz_mm": round(abs(st[i][0] - st[j][0]) * 1000, 3)})
R["P5_beat4"] = {"points": pts, "ownership_changes_on_centreline": len(changes),
                 "changes": changes,
                 "coplanar_cross_owner_pairs": len(copl),
                 "coplanar_examples": copl[:20],
                 "unowned_points": unowned,
                 "TOL_COPLANAR_M": C.TOL_COPLANAR_M,
                 "centreline_stack": stackrec,
                 "was": "0 coplanar cross-owner pairs, 4 ownership changes, 0 unowned",
                 "secs": round(time.time() - t, 1)}
print("[B] P5 beat4: %d changes, %d coplanar cross-owner, %d unowned"
      % (len(changes), len(copl), unowned))
sys.stdout.flush()

# ============================================== P6 corridor built once =====
#
# `duplicate_wall_pairs` USED TO BE A LITERAL COPY of P5's
# `coplanar_cross_owner_pairs`:
#
#     "duplicate_wall_pairs": R["P5_beat4"]["coplanar_cross_owner_pairs"],
#
# Same number, different name, and the name was the wrong one. Its "4 duplicate
# wall pairs" was never a duplicated corridor -- the corridor is built once, as
# the two lines above it already establish -- it was four coplanar cross-owner
# stack pairs on the Beat-4 route, which is P5's question, not P6's. A
# mislabelled metric that reads as a defect is worse than no metric: it costs a
# reader the time to disprove it, every time.
#
# It now MEASURES DUPLICATION. The defect it is named for is real and specific:
# "the Beat-4 corridor was built twice 0.5 m apart". Two builds of the same
# corridor produce two meshes with the SAME topology (identical vertex and
# polygon counts) and the SAME size (bbox dimensions equal to the millimetre)
# whose centroids are a short distance apart. That is what is tested.
t = time.time()
present = [n for n in C.CORRIDOR_DELETE_NAMES if n in bpy.data.objects]
cor_objs = sorted({ob.name for ob in bpy.data.objects
                   if ob.type == "MESH" and ("Transit" in ob.name or
                                             "ApronCorridor" in ob.name)})

DUP_DIM_TOL_M = 0.001      # two builds of one corridor are the same SIZE
DUP_MAX_SEP_M = 5.0        # ... parked a short distance apart (the case was 0.5)


def _sig(ob, D=None):
    """(verts, polys, rounded bbox dims, centroid) of an evaluated object."""
    P = world_verts(ob, D=D)
    if P is None:
        return None
    dims = np.round(P.max(axis=0) - P.min(axis=0), 4)
    return {"name": ob.name, "verts": int(len(P)),
            "polys": int(len(ob.data.polygons)),
            "dims": dims, "centroid": P.mean(axis=0)}


def duplicate_pairs(names, D=None):
    """Pairs of objects that look like two builds of the same thing."""
    sigs = [s for s in (_sig(bpy.data.objects[n], D=D) for n in names) if s]
    out = []
    for i in range(len(sigs)):
        for j in range(i + 1, len(sigs)):
            a, b = sigs[i], sigs[j]
            if a["verts"] != b["verts"] or a["polys"] != b["polys"]:
                continue
            if np.abs(a["dims"] - b["dims"]).max() > DUP_DIM_TOL_M:
                continue
            sep = float(np.linalg.norm(a["centroid"] - b["centroid"]))
            if sep <= DUP_MAX_SEP_M:
                out.append({"a": a["name"], "b": b["name"],
                            "verts": a["verts"], "polys": a["polys"],
                            "dims_m": [round(float(x), 4) for x in a["dims"]],
                            "centroid_separation_m": round(sep, 4)})
    return out, len(sigs)


dups, n_sig = duplicate_pairs(cor_objs, D=D)

# CONTROLS. The check has to be shown capable of firing, and of NOT firing.
# The fault it looks for is trivially reproducible: duplicate one corridor
# object and shift it 0.5 m, which is exactly the geometry of the original
# defect ("the Beat-4 corridor was built twice 0.5 m apart").
#
#   POSITIVE  twin at 0.5 m  -> must be found, and must be the ONLY pair found,
#             which is simultaneously the proof that the five genuinely
#             different corridor objects are not reported as duplicates of each
#             other.
#   NEGATIVE  twin at 500 m  -> identical geometry, far away. Must NOT be
#             reported, or DUP_MAX_SEP_M is not doing anything and the check
#             would call every reused mesh in the world a duplicated corridor.
#
# Both are built here and removed again; neither depends on any defect
# surviving anywhere else.
ctl = {"criteria": {"max_separation_m": DUP_MAX_SEP_M,
                    "dim_tol_m": DUP_DIM_TOL_M}}
if cor_objs:
    _src = bpy.data.objects[cor_objs[0]]
    _twin = _src.copy()
    _twin.data = _src.data.copy()
    _twin.name = _src.name + "_DUPCONTROL"
    bpy.context.scene.collection.objects.link(_twin)
    for _tag, _dx, _want in (("positive_twin_0m5", 0.5, 1),
                             ("negative_twin_500m", 500.0, 0)):
        _twin.location = (_src.location.x + _dx, _src.location.y,
                          _src.location.z)
        bpy.context.view_layer.update()
        _d2, _ = duplicate_pairs(cor_objs + [_twin.name], D=dg())
        hit = [p for p in _d2 if _twin.name in (p["a"], p["b"])]
        ctl[_tag] = {"offset_m": _dx, "must_find": _want, "found": len(hit),
                     "ok": len(hit) == _want,
                     "separation_m": (hit[0]["centroid_separation_m"]
                                      if hit else None)}
        print("[B] P6 CONTROL %-20s twin of %s at %+.1f m -> found %d  %s"
              % (_tag, _src.name, _dx, len(hit),
                 "PASS" if ctl[_tag]["ok"] else "FAIL"))
    bpy.data.objects.remove(_twin, do_unlink=True)
    bpy.context.view_layer.update()
    ctl["ok"] = all(ctl[k]["ok"] for k in ("positive_twin_0m5",
                                           "negative_twin_500m"))
else:
    ctl.update({"ok": False,
                "note": "NO corridor objects in this scene, so the duplicate "
                        "check had nothing to run on. That is not a pass."})
    print("[B] P6 CONTROL: no corridor objects -- the check did not run")

R["P6_corridor_once"] = {"CORRIDOR_DELETE_NAMES": list(C.CORRIDOR_DELETE_NAMES),
                         "still_present": present,
                         "contract_owner": C.CORRIDOR_OWNER,
                         "corridor_objects": cor_objs,
                         "objects_signed": n_sig,
                         "duplicate_wall_pairs": len(dups),
                         "duplicate_wall_pair_detail": dups,
                         "duplicate_criteria": {
                             "same_vertex_and_polygon_count": True,
                             "bbox_dims_equal_within_m": DUP_DIM_TOL_M,
                             "centroid_separation_at_most_m": DUP_MAX_SEP_M},
                         "control": ctl,
                         "was": "built once; CORRIDOR_DELETE_NAMES absent. "
                                "Before 2026-08-02 this field was a copy of "
                                "P5.coplanar_cross_owner_pairs and its '4' was "
                                "not a duplicated corridor.",
                         "secs": round(time.time() - t, 1)}
print("[B] P6: %d corridor objects, %d duplicate wall pairs (measured, not "
      "copied from P5)" % (len(cor_objs), len(dups)))
for _p in dups[:5]:
    print("     DUP %-30s %-30s sep %.3f m"
          % (_p["a"], _p["b"], _p["centroid_separation_m"]))

# ================================================= P7 half width ===========
t = time.time()
hw = {}
for s0 in (250.0, 280.0, 3085.0, 3100.0, 3115.0, 3300.0, 3400.0):
    e = float(C.verge_edge(np.array([s0]))[0])
    m = {"contract_half_width": round(float(C.half_width(np.array([s0]))[0]), 4),
         "contract_verge_edge": round(e, 4)}
    for side in (+1, -1):
        last_track = None; first_hole = None
        for du in np.arange(0.0, 30.0, 0.02):
            u0 = (e - 2.0 + du) * side
            x, y, _z = C.su_to_world(s0, u0)
            z, nm = top_hit(float(x), float(y), D=D)
            if nm == "SURF_Track":
                last_track = abs(u0)
            if z is None and first_hole is None:
                first_hole = abs(u0)
        m["side%+d" % side] = {"last_track_u": (round(last_track, 3) if last_track else None),
                               "implied_half_width": (round(last_track - 2.5, 3)
                                                      if last_track else None),
                               "first_hole_u": (round(first_hole, 3) if first_hole else None)}
    hw["s=%.0f" % s0] = m
R["P7_half_width"] = {"stations": hw,
                      "was": "8.000 at s=3115 and s=250, all four modules agree",
                      "secs": round(time.time() - t, 1)}
print("[B] P7:", json.dumps(hw)[:900])
sys.stdout.flush()

# ================================================= P8 verge seam ===========
t = time.time()
recs = []
for s0 in np.arange(0.0, LAP, 5.0):
    e = float(C.verge_edge(np.array([s0]))[0])
    for side in (+1, -1):
        x1, y1, _z1 = C.su_to_world(s0, (e - 0.020) * side)
        x2, y2, _z2 = C.su_to_world(s0, (e + 0.020) * side)
        z1, n1 = top_hit(float(x1), float(y1), D=D)
        z2, n2 = top_hit(float(x2), float(y2), D=D)
        if z1 is None or z2 is None:
            recs.append({"s": round(float(s0), 1), "side": side, "dz": None,
                         "surf": n1, "barr": n2})
            continue
        recs.append({"s": round(float(s0), 1), "side": side,
                     "dz": round(float(z2 - z1), 5), "surf": n1, "barr": n2})
dz = [r["dz"] for r in recs if r["dz"] is not None]
adz = [abs(d) for d in dz]
R["P8_verge_seam"] = {
    "samples": len(recs),
    "missing": sum(1 for r in recs if r["dz"] is None),
    "raw": stats(dz, 5),
    "abs": stats(adz, 5),
    "p95_abs_mm": round(float(np.percentile(adz, 95)) * 1000, 3) if adz else None,
    "p99_abs_mm": round(float(np.percentile(adz, 99)) * 1000, 3) if adz else None,
    "within_TOL_SEAM_pct": round(100.0 * sum(1 for a in adz if a <= C.TOL_SEAM_M)
                                 / max(1, len(adz)), 3),
    "TOL_SEAM_M": C.TOL_SEAM_M,
    "worst": sorted([r for r in recs if r["dz"] is not None],
                    key=lambda r: -abs(r["dz"]))[:15],
    "was": "p95 |8.9| mm, p99 |301| mm, within TOL_SEAM 97.14 %",
    "secs": round(time.time() - t, 1)}
print("[B] P8 seam: p95 %.3f mm p99 %.3f mm within %.2f%%"
      % (R["P8_verge_seam"]["p95_abs_mm"], R["P8_verge_seam"]["p99_abs_mm"],
         R["P8_verge_seam"]["within_TOL_SEAM_pct"]))

R["total_secs"] = round(time.time() - T0, 1)
write_out(OUT, R)
print("[B] DONE %.1fs" % R["total_secs"])
gate_exit.done()
