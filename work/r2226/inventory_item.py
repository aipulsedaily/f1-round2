"""Per-object inventory of a DECLARED collection in an item test blend.

    blender -b <blend> --factory-startup -P inventory_item.py -- \
        --collection W_Item_X --prefix X_ --out inv.json

Refuses if the collection is absent. Prints STAGE RESULT.
"""
import bpy, sys, json, re
from mathutils import Vector

argv = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
def opt(n, d=None):
    return argv[argv.index(n)+1] if n in argv else d

COLL = opt("--collection"); PFX = opt("--prefix"); OUT = opt("--out")
RIG = re.compile(r"(standin|context|camera|ctx|proxy|helper|backdrop|ref)s?$", re.I)

c = bpy.data.collections.get(COLL)
if c is None:
    print("REFUSING: no collection %r. present: %s" % (COLL, sorted(x.name for x in bpy.data.collections)))
    print(">> STAGE RESULT: INVENTORY_NO_SUCH_COLLECTION")
    sys.exit(0)

rig = [ch.name for ch in c.children if RIG.search(ch.name)]
keep = []
stack = [c]; seen = set()
while stack:
    cc = stack.pop()
    if cc.name in seen: continue
    seen.add(cc.name)
    keep.extend(o for o in cc.objects if o.type == "MESH")
    for ch in cc.children:
        if not RIG.search(ch.name): stack.append(ch)

rows = []
for o in keep:
    mw = o.matrix_world
    cs = [mw @ Vector(v) for v in o.bound_box]
    xs = [v.x for v in cs]; ys = [v.y for v in cs]; zs = [v.z for v in cs]
    rows.append({"n": o.name, "mesh": o.data.name, "users": o.data.users,
                 "tris": sum(max(0, len(p.vertices)-2) for p in o.data.polygons),
                 "c": [round((min(xs)+max(xs))/2, 4), round((min(ys)+max(ys))/2, 4),
                       round((min(zs)+max(zs))/2, 4)],
                 "bb": [round(min(xs),3), round(min(ys),3), round(min(zs),3),
                        round(max(xs),3), round(max(ys),3), round(max(zs),3)],
                 "loc": [round(v,4) for v in o.location],
                 "inst": o.instance_type})
bad = [r["n"] for r in rows if PFX and not r["n"].startswith(PFX)]
shared = [r["n"] for r in rows if r["users"] > 1]
rep = {"blend": bpy.data.filepath, "collection": COLL, "prefix": PFX,
       "rig_subcollections": sorted(rig), "n_objects": len(rows),
       "n_distinct_meshes": len({r["mesh"] for r in rows}),
       "objects_not_matching_prefix": bad,
       "meshes_with_multiple_users": shared,
       "instancing_objects": [r["n"] for r in rows if r["inst"] != "NONE"],
       "total_tris": sum(r["tris"] for r in rows),
       "objects": rows}
if OUT:
    json.dump(rep, open(OUT, "w"), indent=1)
print("collection %s: %d objects, %d distinct meshes, %d tris, rig %s"
      % (COLL, rep["n_objects"], rep["n_distinct_meshes"], rep["total_tris"], rig))
print("  off-prefix %d   shared-mesh %d   instancers %d"
      % (len(bad), len(shared), len(rep["instancing_objects"])))
print(">> STAGE RESULT: INVENTORY_OK")
