"""PROBE G — the two cross-module interpenetrations probe D found, measured.

  BR_Verge_R x SURF_AccessRoad      51 triangle pairs
  TER_Ground x ARCH_Paving_ApronPlatform  74 triangle pairs

A triangle-pair count says "they touch"; it does not say whether that is a
1 mm graze at a welded rim or a metre of one solid inside another.  This
reports WHERE, HOW DEEP, and HOW MUCH AREA, and whether the pair is coplanar
(a z-fight) or a genuine crossing.

THE Z-FIGHT SCAN USED TO SWITCH ITSELF OFF                        (R2, 2026-08-02)
-----------------------------------------------------------------------------
The scan region was taken from `world_x_range` / `world_y_range`, which this
file only fills in FROM THE BVH OVERLAP.  So:

    xr = box.get("world_x_range")
    if not xr:
        continue                      # <- no overlap, no scan, no output key

When the interpenetration cleared, the region became None and the scan skipped
itself silently.  Its "33 of 3600 columns coplanar within 2 mm" figure was never
re-measured on 1.2.0 -- the key simply stopped appearing, and an absent key reads
as "fine" to every human and every diff.

A check that stops running when the thing improves cannot tell you it improved,
and cannot tell you when it comes back.  Coplanarity is not the same question as
interpenetration anyway: two surfaces can sit at identical z over a wide area
with ZERO triangle pairs crossing, which is a z-fight that renders as flicker and
a BVH overlap of exactly nothing.  Driving the scan off the overlap made the
z-fight test conditional on the crossing test, which is the one thing it must not
be.

The scan region is now the PLAN INTERSECTION OF THE TWO OBJECTS' BOUNDING BOXES,
which exists whether or not anything overlaps, so the scan always runs and a
clear result is written down as an explicit zero.  When there IS an overlap its
extent is scanned as well, so the historical figure stays comparable.

AND THE SCAN ITSELF WAS BLIND TO THE WORST CASE
-----------------------------------------------
Giving the scan a positive control immediately failed it.  Two plates at exactly
the same z scored 0 of 144 columns.

`lib_probe.stack()` walks a column by re-casting from `hit.z - 1e-4` after every
hit, so two surfaces at IDENTICAL z collapse into a single hit -- the second cast
starts below both.  The old scan was built on `stack()`, so it could only see
pairs separated by more than 0.1 mm and less than 2 mm, and a perfect z-fight
(the case that actually flickers on screen) was the one thing it could not
report.  Its historical "33 of 3600" was therefore an undercount by construction.

The scan now casts each object's OWN BVH independently -- no epsilon, no
ordering -- so |za - zb| is measured directly and 0.000 mm is detectable.  Three
controls at the bottom: exactly coplanar and 1 mm apart must both be seen, 50 mm
apart must not.
"""
import os
exec(open(os.path.expanduser("~/f1-round2/render/world/assembly/r2/lib_probe.py")).read())

# ------------------------------------------------- WHERE THIS PROBE WRITES --
# Was `save("probeG.json", ...)`. `save()` joins its argument onto
# lib_probe's hardcoded OUT_DIR, so this probe could only ever write to
# probeG.json in the assembly root, whatever it was asked for.
# v120/battery.sh and v121/battery.sh BOTH run this probe with no
# output argument at all, so the v121 run overwrote the probeG.json that
# v120/collect.py reads, and the two versions were then compared
# against each other. Cross-version contamination by design.
#
# It now takes `--out PATH` (a bare positional *.json still works for the
# older chain scripts) and REFUSES to run without one. resolve_out() never
# invents a destination and never strips the directory off the one it was
# given -- the three faults probe_pitexit.py had at once.
OUT = resolve_out(sys.argv, blend_path=(bpy.data.filepath or None),
                  tool="probeG")
print("[G] output ->", OUT)

# Blender 5.2 returns 0 for a script that raised, so a probe that died halfway
# was indistinguishable from one that finished.  install() arms sys.excepthook
# and an atexit sentinel; done() on the last line disarms it.
sys.path.insert(0, os.path.expanduser("~/f1-round2/tools"))
import gate_exit                                                 # noqa: E402
gate_exit.install(tool="probeG")

from mathutils.bvhtree import BVHTree

R = {}
T0 = time.time()
D = dg()
ZFIGHT_TOL_M = 0.002
SCAN_N = 60


def plan_bbox(ob):
    m = ob.matrix_world
    cs = [m @ Vector(c) for c in ob.bound_box]
    return (min(c.x for c in cs), max(c.x for c in cs),
            min(c.y for c in cs), max(c.y for c in cs))


def plan_intersection(na, nb):
    """The x/y rectangle both objects occupy.  None when they are disjoint in
    plan -- which is itself a reportable answer, not a reason to skip."""
    A = bpy.data.objects.get(na)
    B = bpy.data.objects.get(nb)
    if A is None or B is None:
        return None
    ax0, ax1, ay0, ay1 = plan_bbox(A)
    bx0, bx1, by0, by1 = plan_bbox(B)
    x0, x1 = max(ax0, bx0), min(ax1, bx1)
    y0, y1 = max(ay0, by0), min(ay1, by1)
    if x1 <= x0 or y1 <= y0:
        return None
    return [round(x0, 3), round(x1, 3)], [round(y0, 3), round(y1, 3)]


def obj_bvh(ob):
    vs, fs = tri_data(ob)
    if not fs:
        return None, None
    return BVHTree.FromPolygons(vs, fs, all_triangles=True, epsilon=0.0), vs


def zfight_scan(na, nb, xr, yr, n=SCAN_N, max_vert_samples=40000):
    """Columns where object A's surface and object B's surface sit within 2 mm.

    CAST PER OBJECT, not down the scene stack.                (R2, 2026-08-02)

    `lib_probe.stack()` walks a column by re-casting from `hit.z - 1e-4` after
    every hit. Two surfaces at EXACTLY the same z therefore collapse into a
    single hit: the second cast starts below both of them. The old scan was
    built on `stack()`, so a perfect z-fight -- the worst case, the one that
    actually flickers -- was the one case it could not see. It could only see
    pairs separated by MORE than 0.1 mm and less than 2 mm.

    This was not reasoned out, it was caught: the positive control below (two
    coplanar plates 12 km from anything) returned 0 of 144 columns.

    Casting each object's own BVH independently has no epsilon and no ordering,
    so |za - zb| is measured directly and 0.000 mm is detectable. It also names
    the exact pair rather than inferring one from `owner()` of whatever the
    scene ray happened to strike -- the same lesson as probeD's split rows.

    WHERE IT SAMPLES MATTERS AS MUCH AS HOW.

    A uniform 60 x 60 grid over the shared bounding rectangle was tried first and
    measured, on this world, 253 columns hitting BR_Verge_R, 253 hitting
    SURF_AccessRoad, and ZERO hitting both. That zero is a property of the grid,
    not of the world: 3600 samples over a 211 x 104 m rectangle is 3.5 x 1.7 m
    spacing, and the place two adjacent surfaces can z-fight is a seam
    centimetres wide. A grid that coarse reports "clean" for the same reason a
    net with metre-wide holes reports no fish.

    So the sample set is the union of
      - that uniform grid (coarse, unbiased, and what the controls exercise), and
      - object A's OWN evaluated vertices inside the shared rectangle, capped and
        strided. Every one of those is guaranteed to land on A, and they cluster
        exactly where A's geometry is dense -- along its edges and seams, which
        is where the answer lives.
    """
    A = bpy.data.objects.get(na)
    B = bpy.data.objects.get(nb)
    if A is None or B is None:
        return {"samples": 0, "columns_hitting_both": 0,
                "coplanar_within_2mm": 0, "exactly_coplanar_under_0p1mm": 0,
                "error": "missing object"}
    ta, va = obj_bvh(A)
    tb, vb = obj_bvh(B)
    if ta is None or tb is None:
        return {"samples": 0, "columns_hitting_both": 0,
                "coplanar_within_2mm": 0, "exactly_coplanar_under_0p1mm": 0,
                "error": "object has no faces"}
    z0 = max(max(v.z for v in va), max(v.z for v in vb)) + 10.0

    pts = [(float(x), float(y))
           for x in np.linspace(xr[0], xr[1], n)
           for y in np.linspace(yr[0], yr[1], n)]
    n_grid = len(pts)
    inrect = [(v.x, v.y) for v in va
              if xr[0] <= v.x <= xr[1] and yr[0] <= v.y <= yr[1]]
    stride = max(1, len(inrect) // max_vert_samples)
    vpts = inrect[::stride]
    pts += vpts

    both = 0
    fights = []
    dzs = []
    for x, y in pts:
        o = Vector((x, y, z0))
        ha = ta.ray_cast(o, DOWN)
        hb = tb.ray_cast(o, DOWN)
        if ha[0] is None or hb[0] is None:
            continue
        both += 1
        dz = abs(ha[0].z - hb[0].z)
        dzs.append(dz * 1000.0)
        if dz < ZFIGHT_TOL_M:
            fights.append({"xy": [round(x, 3), round(y, 3)],
                           "a": na, "b": nb, "za": round(ha[0].z, 5),
                           "zb": round(hb[0].z, 5),
                           "dz_mm": round(dz * 1000, 4)})
    # SAY WHICH KIND OF ZERO THIS IS. "0 of 0" and "0 of 41" are both zeros and
    # they mean completely different things; leaving a reader to work out which
    # is the same courtesy the vanished output key used to extend.
    if both == 0:
        verdict = ("NO_SHARED_PLAN_AREA -- of %d sampled columns not one has "
                   "BOTH surfaces above it. These two are adjacent, not "
                   "overlapping, so there is no coplanarity to have." % len(pts))
    elif not fights:
        verdict = ("NO_COPLANARITY -- %d columns have both surfaces and none "
                   "is within %.0f mm" % (both, ZFIGHT_TOL_M * 1000))
    else:
        verdict = ("COPLANAR -- %d of %d shared columns within %.0f mm"
                   % (len(fights), both, ZFIGHT_TOL_M * 1000))
    return {"verdict": verdict,
            "samples": len(pts), "grid_samples": n_grid,
            "vertex_samples": len(vpts),
            "a_vertices_in_rect": len(inrect), "vertex_stride": stride,
            "columns_hitting_both": both,
            "coplanar_within_2mm": len(fights),
            "pct_of_columns_hitting_both":
                round(100.0 * len(fights) / max(1, both), 3),
            "abs_dz_mm": stats(dzs, 3) if dzs else None,
            "exactly_coplanar_under_0p1mm": sum(1 for d in dzs if d < 0.1),
            "x_range": [round(float(xr[0]), 3), round(float(xr[1]), 3)],
            "y_range": [round(float(yr[0]), 3), round(float(yr[1]), 3)],
            "examples": sorted(fights, key=lambda f: f["dz_mm"])[:10]}


def tri_data(ob):
    ev = ob.evaluated_get(D)
    me = ev.to_mesh()
    me.calc_loop_triangles()
    M = ob.matrix_world
    vs = [M @ v.co for v in me.vertices]
    fs = [tuple(t.vertices) for t in me.loop_triangles]
    ev.to_mesh_clear()
    return vs, fs


def analyse(na, nb, label):
    A = bpy.data.objects.get(na); B = bpy.data.objects.get(nb)
    if A is None or B is None:
        R[label] = {"error": "missing object"}
        return
    va, fa = tri_data(A)
    vb, fb = tri_data(B)
    ta = BVHTree.FromPolygons(va, fa, all_triangles=True, epsilon=0.0)
    tb = BVHTree.FromPolygons(vb, fb, all_triangles=True, epsilon=0.0)
    ov = ta.overlap(tb)
    recs = []
    for ia, ib in ov:
        ca = (va[fa[ia][0]] + va[fa[ia][1]] + va[fa[ia][2]]) / 3.0
        cb = (vb[fb[ib][0]] + vb[fb[ib][1]] + vb[fb[ib][2]]) / 3.0
        za = [va[k].z for k in fa[ia]]
        zb = [vb[k].z for k in fb[ib]]
        recs.append({"xy": [round(ca.x, 2), round(ca.y, 2)],
                     "za": round(ca.z, 4), "zb": round(cb.z, 4),
                     "dz_mm": round((ca.z - cb.z) * 1000.0, 2),
                     "a_z_span_mm": round((max(za) - min(za)) * 1000.0, 2),
                     "b_z_span_mm": round((max(zb) - min(zb)) * 1000.0, 2)})
    dz = [abs(r["dz_mm"]) for r in recs]
    xs = [r["xy"][0] for r in recs]; ys = [r["xy"][1] for r in recs]
    S = U = None
    if recs:
        s, u = C.project(np.array(xs), np.array(ys))
        S = [round(float(s.min()), 1), round(float(s.max()), 1)]
        U = [round(float(u.min()), 2), round(float(u.max()), 2)]
    R[label] = {"a": na, "b": nb,
                "triangle_pairs": len(ov),
                "a_triangles": len(fa), "b_triangles": len(fb),
                "abs_dz_mm": stats(dz, 2) if dz else None,
                "coplanar_under_1mm": sum(1 for d in dz if d < 1.0),
                "coplanar_under_TOL_COPLANAR": sum(1 for d in dz if d < C.TOL_COPLANAR_M * 1000),
                "s_range": S, "u_range": U,
                "world_x_range": ([round(min(xs), 2), round(max(xs), 2)] if xs else None),
                "world_y_range": ([round(min(ys), 2), round(max(ys), 2)] if ys else None),
                "examples": sorted(recs, key=lambda r: -abs(r["dz_mm"]))[:10]}
    print("[G] %-38s %d pairs  |dz| p50 %.2f mm max %.2f mm  s %s u %s"
          % (label, len(ov),
             (R[label]["abs_dz_mm"] or {}).get("p50", -1),
             (R[label]["abs_dz_mm"] or {}).get("max", -1), S, U))
    sys.stdout.flush()


analyse("BR_Verge_R", "SURF_AccessRoad", "BR_Verge_R_x_SURF_AccessRoad")
analyse("BR_Verge_L", "SURF_AccessRoad", "BR_Verge_L_x_SURF_AccessRoad")
analyse("TER_Ground", "ARCH_Paving_ApronPlatform", "TER_Ground_x_ARCH_Apron")

# ---- does either read as a visible z-fight from above? ---------------------
#
# ALWAYS RUNS. The region no longer comes from the overlap -- it is the plan
# intersection of the two objects' bounding boxes, which exists whether or not
# a single triangle crosses. A cleared overlap now produces an explicit
# `coplanar_within_2mm: 0` over a stated region, so "it got better" and "the
# scan didn't happen" stop looking identical in the JSON.
for label, key, na, nb in (
        ("ribbon_overlap", "BR_Verge_R_x_SURF_AccessRoad",
         "BR_Verge_R", "SURF_AccessRoad"),
        ("apron_overlap", "TER_Ground_x_ARCH_Apron",
         "TER_Ground", "ARCH_Paving_ApronPlatform")):
    box = R.get(key, {})
    out = {"pair": [na, nb], "bvh_triangle_pairs": box.get("triangle_pairs")}

    pi = plan_intersection(na, nb)
    if pi is None:
        out["bbox_region"] = {
            "samples": 0, "coplanar_within_2mm": 0, "pct": 0.0,
            "note": "the two objects do not overlap in plan at all -- an "
                    "explicit zero, not a skipped scan"}
        print("[G] %s z-fight scan: objects disjoint in plan; explicit 0" % label)
    else:
        out["bbox_region"] = zfight_scan(na, nb, pi[0], pi[1])
        out["bbox_region"]["region_source"] = "plan intersection of bounding boxes"
        b = out["bbox_region"]
        print("[G] %s z-fight scan (bbox region): %d of %d columns hitting both "
              "are coplanar within 2 mm (%d exactly, under 0.1 mm)  x %s y %s"
              % (label, b["coplanar_within_2mm"], b["columns_hitting_both"],
                 b["exactly_coplanar_under_0p1mm"], pi[0], pi[1]))
        print("[G]    " + b["verdict"])
        print("[G]    sampled %d grid + %d of %d A-vertices (stride %d)"
              % (b["grid_samples"], b["vertex_samples"],
                 b["a_vertices_in_rect"], b["vertex_stride"]))

    # The historical figure was measured over the OVERLAP extent. Keep it when
    # there is one, so the two runs stay comparable -- and label it.
    xr, yr = box.get("world_x_range"), box.get("world_y_range")
    if xr and yr:
        out["overlap_region"] = zfight_scan(na, nb, xr, yr)
        out["overlap_region"]["region_source"] = "extent of the BVH overlap"
        print("[G] %s z-fight scan (overlap region): %d of %d columns coplanar"
              % (label, out["overlap_region"]["coplanar_within_2mm"],
                 out["overlap_region"]["columns_hitting_both"]))
    else:
        out["overlap_region"] = None
        out["overlap_region_note"] = (
            "no BVH overlap in this build, so there is no overlap extent to "
            "scan. THE SCAN STILL RAN, over the bbox region above. Until "
            "2026-08-02 this case produced no output key at all.")
    R[label + "_zfight_scan"] = out
    sys.stdout.flush()

# ---------------------------------------------------------------- CONTROLS --
# The scan is the thing that broke, so the scan is what gets controlled.
#
# POSITIVE (exact)  two plates at EXACTLY the same z. Every column must read as
#                   coplanar. This is the case the old `stack()`-based scan
#                   could not see at all -- it returned 0 of 144 -- and it is
#                   the case that actually flickers in a render.
# POSITIVE (near)   1 mm apart, inside the 2 mm tolerance. Must be seen.
# NEGATIVE          50 mm apart, 25x the tolerance. Must NOT be seen.
#
# Built from scratch 12 km from anything, measured, removed. None of them
# depends on a defect surviving anywhere else in the world.
CTL = {"tol_m": ZFIGHT_TOL_M}
_cx, _cy, _cz = 12000.0, 12000.0, 50.0
_plates = []
for _nm in ("SURF_ZFightControl", "ARCH_ZFightControl"):
    bpy.ops.mesh.primitive_plane_add(size=8.0, location=(_cx, _cy, _cz))
    _p = bpy.context.object
    _p.name = _nm
    _plates.append(_p)
for tag, dz, want_hits in (("positive_exactly_coplanar", 0.0, True),
                           ("positive_1mm_apart", 0.001, True),
                           ("negative_50mm_apart", 0.050, False)):
    _plates[1].location = (_cx, _cy, _cz + dz)
    bpy.context.view_layer.update()
    r = zfight_scan(_plates[0].name, _plates[1].name,
                    [_cx - 3.0, _cx + 3.0], [_cy - 3.0, _cy + 3.0], n=12)
    ok = (r["coplanar_within_2mm"] > 0) == want_hits
    CTL[tag] = {"separation_mm": dz * 1000.0, "must_see_coplanar": want_hits,
                "coplanar_within_2mm": r["coplanar_within_2mm"],
                "columns_hitting_both": r["columns_hitting_both"],
                "samples": r["samples"], "ok": ok}
    print("[G] CONTROL %-26s sep %5.1f mm -> %d/%d coplanar columns   %s"
          % (tag, dz * 1000.0, r["coplanar_within_2mm"],
             r["columns_hitting_both"], "PASS" if ok else "FAIL"))
for _p in _plates:
    bpy.data.objects.remove(_p, do_unlink=True)
CTL["all_ok"] = all(CTL[k]["ok"] for k in ("positive_exactly_coplanar",
                                          "positive_1mm_apart",
                                          "negative_50mm_apart"))
R["zfight_scan_controls"] = CTL
if not CTL["all_ok"]:
    print("[G] !! THE Z-FIGHT SCAN'S OWN CONTROLS MISBEHAVED -- every scan "
          "number above is unsupported")

# NOT calling show_all(): nothing is saved from this process, and un-hiding
# 28,314 vegetation emitters forces a full depsgraph rebuild of 4.7 M instances
# for no measurement at all.
R["total_secs"] = round(time.time() - T0, 1)
write_out(OUT, R)
print("[G] DONE %.1fs" % R["total_secs"])
gate_exit.done()
