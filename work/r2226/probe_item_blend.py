"""Probe an item test blend: collections, object counts, world-space bounds.

    blender -b <blend> --factory-startup -P probe_item_blend.py -- --json out.json
"""
import bpy, sys, json, os
argv = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
out = None
for i,a in enumerate(argv):
    if a == "--json": out = argv[i+1]

rep = {"blend": bpy.data.filepath, "collections": {}, "objects": len(bpy.data.objects),
       "meshes": len(bpy.data.meshes), "materials": len(bpy.data.materials)}
for c in bpy.data.collections:
    rep["collections"][c.name] = {"objects": len(c.objects), "children": [ch.name for ch in c.children]}

# prefix census + world bounds per prefix
import collections as _c
pref = _c.Counter()
bb = {}
for ob in bpy.data.objects:
    p = ob.name.split("_")[0] + "_"
    pref[p] += 1
    if ob.type != 'MESH' or ob.data is None: continue
    mw = ob.matrix_world
    for corner in ob.bound_box:
        v = mw @ __import__("mathutils").Vector(corner)
        d = bb.setdefault(p, [1e18,1e18,1e18,-1e18,-1e18,-1e18])
        for k in range(3):
            d[k] = min(d[k], v[k]); d[k+3] = max(d[k+3], v[k])
rep["prefixes"] = dict(pref)
rep["bounds_by_prefix"] = {k: [round(x,3) for x in v] for k,v in bb.items()}
# mesh datablock reuse: users per mesh
reuse = _c.Counter()
for me in bpy.data.meshes:
    reuse[me.users] += 1
rep["mesh_users_histogram"] = dict(reuse)
rep["distinct_meshes"] = len(bpy.data.meshes)
# object locations sample
rep["sample_objects"] = [
    {"n": ob.name, "loc": [round(v,3) for v in ob.location],
     "rot": [round(v,4) for v in ob.rotation_euler],
     "coll": [c.name for c in ob.users_collection]}
    for ob in list(bpy.data.objects)[:25]]
rep["total_tris"] = sum(len(m.loop_triangles) if m.loop_triangles else sum(max(0,len(p.vertices)-2) for p in m.polygons) for m in bpy.data.meshes)
print(">> PROBE " + json.dumps(rep, indent=1))
if out:
    with open(out,"w") as f: json.dump(rep,f,indent=1)
print(">> STAGE RESULT: PROBE_OK")
