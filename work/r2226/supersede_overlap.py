"""How much does a hero item overlap the class-level geometry it supersedes?

    blender -b work/r2226/items_only.blend --factory-startup -P supersede_overlap.py -- \
        --host ARCH_PitWall --from render/world/assembly/r2/assembly9.blend \
        --item timing_stand --collection W_Item_TimingStand --out ov.json

The supersede debt is stated in build_items as a REBUILD_OWED line derived from
assembly9_build.json's counter (`pit_wall_stands = 5`). A counter is a claim
about what was built, not about where it is. This measures WHERE: it links ONE
object out of the 4.21 GB ship -- not the scene -- and counts how many of that
object's vertices fall inside each placed unit's world bounding box.

Zero overlap would mean the two populations coexist and the debt is cosmetic.
Non-zero means the hero geometry is standing inside the class geometry and the
old version really does have to come out first.
"""
import bpy, sys, json
from mathutils import Vector

argv = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
def opt(n, d=None): return argv[argv.index(n)+1] if n in argv else d
HOST, SRC = opt("--host"), opt("--from")
COLL, OUT = opt("--collection"), opt("--out")

# link ONE object out of the ship. Not a scene open: the census's own reader.
with bpy.data.libraries.load(SRC, link=True) as (df, dt):
    if HOST not in df.objects:
        print("REFUSING: %s has no object %r" % (SRC, HOST))
        print(">> STAGE RESULT: SUPERSEDE_NO_HOST"); sys.exit(0)
    dt.objects = [HOST]
host = bpy.data.objects[HOST]
bpy.context.scene.collection.objects.link(host)
bpy.context.view_layer.update()
me = host.data
mw = host.matrix_world
V = [mw @ v.co for v in me.vertices]
print("host %s: %d vertices linked from %s" % (HOST, len(V), SRC))

c = bpy.data.collections.get(COLL)
rows = []
for ob in sorted(c.all_objects, key=lambda o: o.name):
    if ob.type != "MESH":
        continue
    cs = [ob.matrix_world @ Vector(v) for v in ob.bound_box]
    lo = Vector((min(v.x for v in cs), min(v.y for v in cs), min(v.z for v in cs)))
    hi = Vector((max(v.x for v in cs), max(v.y for v in cs), max(v.z for v in cs)))
    n = sum(1 for v in V if lo.x <= v.x <= hi.x and lo.y <= v.y <= hi.y
            and lo.z <= v.z <= hi.z)
    rows.append({"unit": ob.name, "host_verts_inside_box": n,
                 "box": [round(x, 2) for x in (lo.x, lo.y, lo.z, hi.x, hi.y, hi.z)]})
    print("  %-28s %6d host vertices inside its box" % (ob.name, n))

hit = [r for r in rows if r["host_verts_inside_box"] > 0]
rep = {"host": HOST, "host_verts": len(V), "source": SRC, "collection": COLL,
       "units": len(rows), "units_overlapping_host": len(hit),
       "total_host_verts_inside_units": sum(r["host_verts_inside_box"] for r in rows),
       "rows": rows}
print("\n%d of %d placed units contain host geometry; %d host vertices total"
      % (len(hit), len(rows), rep["total_host_verts_inside_units"]))
if OUT:
    json.dump(rep, open(OUT, "w"), indent=1)
print(">> STAGE RESULT: %s" % ("SUPERSEDE_OVERLAP_MEASURED_NONZERO" if hit
                               else "SUPERSEDE_OVERLAP_MEASURED_ZERO"))
