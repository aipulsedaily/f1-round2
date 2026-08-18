"""PROBE G2 — the ARCH_Paving_ApronPlatform x SURF_* interpenetration probeD found
on the v1.2.0 rebuild, measured, plus the same pair on any other assembly.

probeD reported 4,624 triangle pairs for `ARCH_ApronPlatform x SURF_Track+Joint`
where assembly2 (contract 1.0.1) reported 0. probeG's hard-coded pair list does
not cover it, so a count is all we have and a count cannot tell a 1 mm graze at
a welded joint from a metre of one slab inside another.

Run on any assembly:

    blender -b <assembly>.blend --factory-startup -P v120/probeG2.py -- --out OUT.json

Output path handling was the copy-pasted `sys.argv[-1] ... else "probeG2.json"`
idiom (fixed 2026-08-02): it read the LAST argument whatever it was, and given
nothing usable it silently invented a relative filename resolved against the
caller's CWD.  It now goes through lib_probe.resolve_out(), which resolves to an
absolute path and refuses rather than guessing.  A bare positional OUT.json is
still accepted for v120/battery.sh and v121/battery.sh.
"""
import os
exec(open(os.path.expanduser("~/f1-round2/render/world/assembly/r2/lib_probe.py")).read())
from mathutils.bvhtree import BVHTree

OUT = resolve_out(sys.argv, blend_path=(bpy.data.filepath or None), tool="probeG2")
print("[G2] output ->", OUT)
R = {"contract": C.__version__, "scene": bpy.data.filepath}
T0 = time.time()
D = dg()


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
        R[label] = {"error": "missing object: %s" % (na if A is None else nb)}
        print("[G2] %-44s MISSING" % label)
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
    R[label] = {"a": na, "b": nb, "triangle_pairs": len(ov),
                "a_triangles": len(fa), "b_triangles": len(fb),
                "abs_dz_mm": stats(dz, 2) if dz else None,
                "coplanar_under_1mm": sum(1 for d in dz if d < 1.0),
                "coplanar_under_TOL_COPLANAR":
                    sum(1 for d in dz if d < C.TOL_COPLANAR_M * 1000),
                "s_range": S, "u_range": U,
                "world_x_range": ([round(min(xs), 2), round(max(xs), 2)] if xs else None),
                "world_y_range": ([round(min(ys), 2), round(max(ys), 2)] if ys else None),
                "examples": sorted(recs, key=lambda r: -abs(r["dz_mm"]))[:12]}
    print("[G2] %-44s %6d pairs  |dz| p50 %.2f mm max %.2f mm  s %s u %s"
          % (label, len(ov), (R[label]["abs_dz_mm"] or {}).get("p50", -1),
             (R[label]["abs_dz_mm"] or {}).get("max", -1), S, U))
    sys.stdout.flush()


analyse("ARCH_Paving_ApronPlatform", "SURF_Track", "APRON_x_TRACK")
analyse("ARCH_Paving_ApronPlatform", "SURF_ApronJoint", "APRON_x_APRONJOINT")
analyse("ARCH_Paving_ApronPlatform", "SURF_AccessRoad", "APRON_x_ACCESSROAD")

# POSITIVE CONTROL on the same BVH path, in this same scene: two cubes that are
# known to interpenetrate, and two that are known not to.
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 500.0))
ca = bpy.context.object; ca.name = "G2_CTL_A"
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.5, 0, 500.0))
cb = bpy.context.object; cb.name = "G2_CTL_B_INSIDE"
bpy.ops.mesh.primitive_cube_add(size=1.0, location=(9.0, 0, 500.0))
cc = bpy.context.object; cc.name = "G2_CTL_C_APART"
bpy.context.view_layer.update()
D = dg()
analyse("G2_CTL_A", "G2_CTL_B_INSIDE", "CONTROL_POSITIVE")
analyse("G2_CTL_A", "G2_CTL_C_APART", "CONTROL_NEGATIVE")

R["secs"] = round(time.time() - T0, 1)
write_out(OUT, R)
print("[G2] wrote", OUT, "in %.1fs" % R["secs"])
