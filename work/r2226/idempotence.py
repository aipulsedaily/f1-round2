"""build() twice in one session must give an identical scene -- build_dressing's
rule, and the reason R2_Items is purged before a rebuild."""
import os
import bpy, sys, json
sys.path.insert(0, os.path.expanduser("~/f1-round2/world"))
import build_items as BI

def sig():
    objs = sorted(o.name for o in bpy.data.objects)
    mesh = sorted(m.name for m in bpy.data.meshes)
    return (len(objs), len(mesh), objs[:3], objs[-3:],
            sum(len(m.vertices) for m in bpy.data.meshes))

a = BI.build(place=["crew_figure"]); sa = sig()
b = BI.build(place=["crew_figure"]); sb = sig()
print("\nrun 1  objects %d meshes %d verts %d" % (sa[0], sa[1], sa[4]))
print("run 2  objects %d meshes %d verts %d" % (sb[0], sb[1], sb[4]))
same = sa == sb and a["objects"] == b["objects"] and a["triangles"] == b["triangles"]
print("first/last names identical: %s" % (sa[2] == sb[2] and sa[3] == sb[3]))
print(">> STAGE RESULT: %s" % ("ITEMS_IDEMPOTENT_OK" if same
                               else "ITEMS_NOT_IDEMPOTENT_FAIL"))
