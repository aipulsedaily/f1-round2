"""PROBE PITEXIT — the three surface defects at the pit exit, measured on the
ASSEMBLED world at fine resolution.

    #47  unwelded seam            0.50 m (s) x 0.10 m (u) over s 3380-3600, u 10-16
    #48  the self-shadowed groove 1 mm in u across the apron platform's outer edge
    #50  coplanar owners          full ray stack, every column, pair-by-pair

Run:  blender -b <assembly>.blend --factory-startup -P probe_pitexit.py -- --out OUT.json
      (a bare positional OUT.json after `--` is still accepted, see below)

WHERE IT WRITES                                        (defect fixed 2026-08-02)
-----------------------------------------------------------------------------
This tool used to ignore where it was told to write.  Three faults stacked:

    OUT = sys.argv[-1] if sys.argv[-1].endswith(".json") else "probe_pitexit.json"
    ...
    save(os.path.basename(OUT), R)

  1. `os.path.basename(OUT)` THREW THE DIRECTORY AWAY, and `save()` in
     lib_probe.py joins what it is given onto the hardcoded
     OUT_DIR = .../render/world/assembly/r2.  So every run landed in the
     assembly root no matter what path was on the command line.  v120/battery.sh
     asked for `v120/pitexit_v120.json`; the file is in the assembly root, and
     v120/ has never held one.  That is the bug, observed in the artefacts.
  2. The `else` branch defaulted SILENTLY to a bare relative name resolved
     against whatever the CWD happened to be — a different place for every
     caller, and the same name every time, so successive runs clobbered each
     other.
  3. `sys.argv[-1]` is positional-by-accident: it reads the LAST argument
     whatever it is, so `-- --out X.json --frames 3` misses X.json entirely and
     a bare `--` with no path would have silently taken the default.

Now: `--out` is parsed properly out of the args after `--`, resolved to an
ABSOLUTE path, its parent directory is created and checked writable, and the
result is written there and nowhere else.  A bare positional `*.json` is still
honoured for the existing callers (chain_v111.sh, v120/battery.sh,
v121/battery.sh) and is resolved against the CWD, which is printed.  Given
nothing usable the tool EXITS NON-ZERO IMMEDIATELY, before any of the expensive
work — it never invents a destination.  The resolver is `resolve_out()` in
lib_probe.py (shared with the other probes that take an output path); its
controls are in selftest_probe_out.py, which runs in a second without Blender.

WHY FINE.  Barriers reported 26.0 m2 of hole from its own isolated build; the
assembled world measured twice that on a 2.0 x 1.0 m grid; and a 0.5 x 0.1 m map
found a further 32 m2 the coarse grid could not see.  A 0.26 m mean gap width is
INVISIBLE to a 1.0 m sample.  Every number here is a physical area or a depth in
metres, and every hole is reported with the two objects that bound it.
"""
exec(open("/home/zany/f1-round2/render/world/assembly/r2/lib_probe.py").read())

# Resolved BEFORE the expensive work: a run that cannot write must die in the
# first second, not after twenty minutes of ray casting.
OUT = resolve_out(sys.argv, blend_path=(bpy.data.filepath or None),
                  tool="probe_pitexit")   # lib_probe.py
print("[pitexit] output ->", OUT)
R = {"contract": C.__version__}
T0 = time.time()

hide(lambda o: o.type == "MESH" and role(o.name) in ("vegetation", "dressing"))
D = dg()

GROUND = GROUND_ROLES


def ground_stack(x, y, z0, span=1.5):
    """Every GROUND surface within `span` of z0 at (x, y), top first."""
    out = []
    for (z, nm) in stack(x, y, z0=z0 + span, zmin=z0 - span, D=D, maxhits=30):
        if role(nm) in GROUND:
            out.append((z, nm))
    return out


# =========================================================================== #
#  1.  THE SEAM MAP  (#47)                                                    #
# =========================================================================== #
S0, S1, DS = 3380.0, 3600.0, 0.50
U0, U1, DU = 10.00, 16.00, 0.10
CELL = DS * DU                                   # 0.05 m2 per sample
HOLE_M = 0.050                                   # a sample is a HOLE if no ground
                                                 # surface lies within this of the
                                                 # contract datum.  50 mm is 5x
                                                 # TOL_SEAM_M and 1.7x
                                                 # TOL_COPLANAR_M, so a laid-but-
                                                 # low surface is not a hole and a
                                                 # 0.30 m bedding shaft is.

def seam_map(u0):
    """One seam map on a u grid starting at `u0`.  -> (result dict, printout).

    RUN TWICE, ON TWO OFFSET GRIDS.  Two abutting meshes share an edge
    geometrically, not topologically, and a ray aimed exactly at that edge can
    miss both — which reads as a hole one sample wide.  Every `SURF_Track |
    BR_Verge_L` run in the first map was exactly one 0.10 m sample at exactly
    u = 10.500, which is `verge_edge` to the millimetre and the first line of the
    round grid.  A map whose samples land on no boundary at all settles whether
    those are ground that is missing or rays that are unlucky.
    """
    SS = np.arange(S0, S1 + 1e-9, DS)
    UU = np.arange(u0, U1 + 1e-9, DU)
    grid_s, grid_u = np.meshgrid(SS, UU, indexing="ij")
    P = C.su_to_world(grid_s.ravel(), grid_u.ravel())
    GX, GY, GZ = P[:, 0], P[:, 1], P[:, 2]
    holes = []
    topname = np.empty(GX.size, dtype=object)
    topz = np.full(GX.size, np.nan)
    print("[seam u0=%.3f] %d x %d = %d samples at %.2f x %.2f m"
          % (u0, len(SS), len(UU), GX.size, DS, DU))
    sys.stdout.flush()
    for k in range(GX.size):
        st = ground_stack(float(GX[k]), float(GY[k]), float(GZ[k]))
        if st:
            topz[k] = st[0][0]
            topname[k] = st[0][1]
        if (not st) or (float(GZ[k]) - st[0][0] > HOLE_M):
            holes.append(k)
    hole = np.zeros(GX.size, bool)
    hole[holes] = True
    H = hole.reshape(grid_s.shape)
    TN = topname.reshape(grid_s.shape)
    TZ = topz.reshape(grid_s.shape)
    runs_out = []
    for i in range(len(SS)):
        j = 0
        while j < len(UU):
            if not H[i, j]:
                j += 1
                continue
            k = j
            while k < len(UU) and H[i, k]:
                k += 1
            lo = TN[i, j - 1] if j > 0 else None
            hi = TN[i, k] if k < len(UU) else None
            zlo = float(TZ[i, j - 1]) if j > 0 and np.isfinite(TZ[i, j - 1]) else None
            zhi = float(TZ[i, k]) if k < len(UU) and np.isfinite(TZ[i, k]) else None
            runs_out.append({"s": float(SS[i]),
                             "u0": float(UU[j]), "u1": float(UU[k - 1]),
                             "width_m": round((k - j) * DU, 3),
                             "samples": int(k - j),
                             "lip_lo": lo, "lip_hi": hi,
                             "z_lo": zlo, "z_hi": zhi,
                             "dz_mm": (round(abs(zhi - zlo) * 1000.0, 2)
                                       if (zlo is not None and zhi is not None)
                                       else None)})
            j = k
    pairs = {}
    for r in runs_out:
        key = "%s | %s" % (r["lip_lo"], r["lip_hi"])
        d = pairs.setdefault(key, {"runs": 0, "area_m2": 0.0, "dz_mm": [],
                                   "one_sample_runs": 0})
        d["runs"] += 1
        d["area_m2"] += r["width_m"] * DS
        d["one_sample_runs"] += int(r["samples"] == 1)
        if r["dz_mm"] is not None:
            d["dz_mm"].append(r["dz_mm"])
    for k, v in pairs.items():
        v["area_m2"] = round(v["area_m2"], 3)
        v["dz_mm"] = (stats(v["dz_mm"], 3) if v["dz_mm"] else None)
    multi = [r for r in runs_out if r["samples"] > 1]
    res = {
        "grid": {"s": [S0, S1, DS], "u": [u0, U1, DU], "cell_m2": CELL,
                 "hole_threshold_m": HOLE_M},
        "samples": int(GX.size),
        "hole_samples": int(hole.sum()),
        "hole_area_m2": round(float(hole.sum()) * CELL, 3),
        "one_sample_runs": int(sum(1 for r in runs_out if r["samples"] == 1)),
        "hole_area_m2_runs_wider_than_one_sample":
            round(sum(r["width_m"] * DS for r in multi), 3),
        "stations_with_a_hole": int((H.any(axis=1)).sum()),
        "s_range": ([float(SS[H.any(axis=1)].min()),
                     float(SS[H.any(axis=1)].max())] if H.any() else None),
        "u_range": ([float(UU[H.any(axis=0)].min()),
                     float(UU[H.any(axis=0)].max())] if H.any() else None),
        "widest_m": max([r["width_m"] for r in runs_out], default=0.0),
        "mean_width_m": (round(float(np.mean([r["width_m"] for r in runs_out])), 3)
                         if runs_out else 0.0),
        "by_lip_pair": pairs,
        "runs": runs_out[:400]}
    print("[seam u0=%.3f] %d hole samples = %.2f m2 over %d stations "
          "(%.2f m2 in runs wider than one sample; %d one-sample runs)"
          % (u0, hole.sum(), hole.sum() * CELL, (H.any(axis=1)).sum(),
             res["hole_area_m2_runs_wider_than_one_sample"],
             res["one_sample_runs"]))
    for k, v in sorted(pairs.items(), key=lambda kv: -kv[1]["area_m2"])[:10]:
        print("    %-58s %7.2f m2  %4d runs (%d one-sample)"
              % (k, v["area_m2"], v["runs"], v["one_sample_runs"]))
    sys.stdout.flush()
    return res


R["seam"] = seam_map(U0)
R["seam_offset_grid"] = seam_map(U0 + 0.037)
sys.stdout.flush()

# =========================================================================== #
#  2.  THE GROOVE AT THE APRON PLATFORM'S OUTER EDGE  (#48)                   #
# =========================================================================== #
# 1 mm in u, so a 5 mm groove is 5 samples wide and not an aliasing artefact.
SUN = np.array(C.SUN_DIR, float)
SUN_ELEV = C.SUN_ELEV_DEG
grooves = []
for s in (3220.0, 3260.0, 3300.0, 3340.0, 3380.0, 3410.0, 3440.0, 3470.0):
    pe = float(C.platform_edge(s, +1))
    us = np.arange(pe - 0.60, pe + 0.60, 0.001)
    prof = []
    pts = C.su_to_world(np.full(us.shape, s), us)
    for k in range(len(us)):
        st = ground_stack(float(pts[k, 0]), float(pts[k, 1]), float(pts[k, 2]))
        prof.append((float(us[k]), (float(st[0][0]) if st else None),
                     (st[0][1] if st else None),
                     round(float(pts[k, 2]) - st[0][0], 5) if st else None))
    # a "recess" is a contiguous run whose top is >= 5 mm below the datum
    rec = []
    j = 0
    while j < len(prof):
        if prof[j][3] is None or prof[j][3] < 0.005:
            j += 1
            continue
        k = j
        while k < len(prof) and prof[k][3] is not None and prof[k][3] >= 0.005:
            k += 1
        depths = [prof[q][3] for q in range(j, k)]
        rec.append({"u0": prof[j][0], "u1": prof[k - 1][0],
                    "width_m": round((k - j) * 0.001, 4),
                    "max_depth_mm": round(max(depths) * 1000.0, 2),
                    "objects": sorted({prof[q][2] for q in range(j, k)
                                       if prof[q][2]}),
                    "left_of": prof[j - 1][2] if j else None,
                    "right_of": prof[k][2] if k < len(prof) else None})
        j = k
    grooves.append({"s": s, "platform_edge": round(pe, 4), "recesses": rec})
    print("[groove] s=%.0f  platform_edge=%.3f  %d recess(es): %s"
          % (s, pe, len(rec),
             "; ".join("u %.3f-%.3f w %.3f m d %.1f mm [%s]"
                       % (r["u0"], r["u1"], r["width_m"], r["max_depth_mm"],
                          ",".join(r["objects"])[:60]) for r in rec[:4])))
    sys.stdout.flush()
R["grooves"] = {"sun_elev_deg": SUN_ELEV, "sun_dir": list(map(float, SUN)),
                "scans": grooves}

# =========================================================================== #
#  3.  COPLANAR OWNERS  (#50)                                                 #
# =========================================================================== #
CO_TOL = 0.030                              # C.TOL_COPLANAR_M
CO_TIGHT = 0.002
cols = 0
co = {}
tight = 0
for s in np.arange(3150.0, 3560.0, 2.0):
    for u in np.arange(9.0, 46.0, 1.0):
        p = C.su_to_world(np.array([s]), np.array([u]))[0]
        st = ground_stack(float(p[0]), float(p[1]), float(p[2]), span=2.0)
        cols += 1
        seen = False
        for a in range(len(st)):
            for b in range(a + 1, len(st)):
                if owner(st[a][1]) == owner(st[b][1]):
                    continue
                dz = abs(st[a][0] - st[b][0])
                if dz > CO_TOL:
                    continue
                key = " x ".join(sorted((st[a][1], st[b][1])))
                d = co.setdefault(key, {"columns": 0, "dz_mm": [],
                                        "s": [1e9, -1e9], "u": [1e9, -1e9]})
                d["columns"] += 1
                d["dz_mm"].append(round(dz * 1000.0, 3))
                d["s"] = [min(d["s"][0], float(s)), max(d["s"][1], float(s))]
                d["u"] = [min(d["u"][0], float(u)), max(d["u"][1], float(u))]
                if dz <= CO_TIGHT:
                    seen = True
        if seen:
            tight += 1
for k, v in co.items():
    v["dz_mm"] = stats(v["dz_mm"], 3)
R["coplanar"] = {"columns_tested": cols, "columns_coplanar_within_2mm": tight,
                 "pct": round(100.0 * tight / max(cols, 1), 3),
                 "tol_m": CO_TOL, "pairs": co}
print("[coplanar] %d of %d columns coplanar within 2 mm (%.2f %%)"
      % (tight, cols, 100.0 * tight / max(cols, 1)))
for k, v in sorted(co.items(), key=lambda kv: -kv[1]["columns"])[:12]:
    print("    %-62s %5d cols  dz p50 %.2f mm  s %.0f-%.0f u %.1f-%.1f"
          % (k, v["columns"], v["dz_mm"]["p50"], v["s"][0], v["s"][1],
             v["u"][0], v["u"][1]))

R["total_secs"] = round(time.time() - T0, 1)
write_out(OUT, R)
print("[pitexit] DONE %.1fs" % R["total_secs"])
