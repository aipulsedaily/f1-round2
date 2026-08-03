"""POSITIVE / NEGATIVE CONTROL for probeD's BVH interpenetration machinery.

probeD reports "0 triangle pairs" for four of its six module-boundary tests.
A zero from a working test and a zero from a test that cannot fire look
identical in the log, and this project has shipped the second kind twice
(R2-012, R2-018).  This runs probeD's OWN `bvh()` / `overlap()` path against
two cubes that are KNOWN to interpenetrate and two that are KNOWN to be apart,
in the same Blender build, and prints both answers.

    blender -b --factory-startup -P v120/ctl_bvh.py
"""
import bpy, json, os, sys
from mathutils.bvhtree import BVHTree

bpy.ops.wm.read_factory_settings(use_empty=True)
D = bpy.context.evaluated_depsgraph_get()


def mk(name, loc):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    ob = bpy.context.object
    ob.name = name
    return ob


def bvh(ob):
    """Byte-for-byte the construction probeD uses."""
    ev = ob.evaluated_get(bpy.context.evaluated_depsgraph_get())
    me = ev.to_mesh()
    me.calc_loop_triangles()
    M = ob.matrix_world
    vs = [M @ v.co for v in me.vertices]
    fs = [tuple(t.vertices) for t in me.loop_triangles]
    ev.to_mesh_clear()
    return BVHTree.FromPolygons(vs, fs, all_triangles=True, epsilon=0.0), len(fs)


a = mk("CTL_A", (0.0, 0.0, 0.0))
b_pos = mk("CTL_B_INSIDE", (0.5, 0.0, 0.0))     # 50 % overlap
b_neg = mk("CTL_B_APART", (5.0, 0.0, 0.0))      # 4 m of clear air
b_touch = mk("CTL_B_TOUCHING", (1.0, 0.0, 0.0))  # coplanar faces, no volume

bpy.context.view_layer.update()
ta, na = bvh(a)
R = {}
for nm, ob in (("POSITIVE_overlapping", b_pos),
               ("NEGATIVE_apart", b_neg),
               ("EDGE_exactly_touching", b_touch)):
    tb, nb = bvh(ob)
    ov = ta.overlap(tb)
    R[nm] = {"tri_pairs": len(ov), "tris_a": na, "tris_b": nb}
    print("[CTL-BVH] %-24s %6d triangle pairs" % (nm, len(ov)))

ok = R["POSITIVE_overlapping"]["tri_pairs"] > 0 and R["NEGATIVE_apart"]["tri_pairs"] == 0
R["verdict"] = "BVH_MACHINERY_WORKS" if ok else "BVH_MACHINERY_BROKEN"
print("[CTL-BVH] " + R["verdict"])
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ctl_bvh.json")
json.dump(R, open(out, "w"), indent=1)
print("[CTL-BVH] wrote", out)
