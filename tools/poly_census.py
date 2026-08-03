"""Total polygon count — base, evaluated, and realized-with-instances.

Three different numbers, and conflating them is how people quote a scene as
"2 million polys" when Cycles is actually building a BVH over 400 million:

  BASE       sum of bpy.data.meshes polygons. What is stored in the file.
             Ignores every modifier and every instance. Cheap.
  EVALUATED  each object's mesh after modifiers (SUBSURF, SOLIDIFY, MIRROR,
             geometry nodes that OUTPUT geometry). What one copy really costs.
  REALIZED   every instance the depsgraph emits, counted separately. This is
             what the renderer actually traces, and for a world with 500,000
             grass clumps it is the only honest figure.
"""
import bpy, sys, time

t0 = time.time()
sc = bpy.context.scene

base_tris = 0
for me in bpy.data.meshes:
    for p in me.polygons:
        base_tris += max(len(p.vertices) - 2, 1)
print(f"BASE      {base_tris:>15,} tris across {len(bpy.data.meshes):,} meshes")
sys.stdout.flush()

deps = bpy.context.evaluated_depsgraph_get()

# ---- evaluated, one copy per object -------------------------------------
ev_tris = 0
n_obj = 0
for ob in sc.objects:
    if ob.type != "MESH":
        continue
    oe = ob.evaluated_get(deps)
    try:
        me = oe.to_mesh()
    except Exception:
        continue
    if me is None:
        continue
    n_obj += 1
    for p in me.polygons:
        ev_tris += max(len(p.vertices) - 2, 1)
    oe.to_mesh_clear()
print(f"EVALUATED {ev_tris:>15,} tris across {n_obj:,} mesh objects "
      f"({time.time()-t0:.0f}s)")
sys.stdout.flush()

# ---- realized, every instance the depsgraph emits ------------------------
# Cache per source mesh so a grass clump instanced 500,000 times is converted
# once, not 500,000 times.
cache = {}
inst_tris = 0
n_inst = 0
for inst in deps.object_instances:
    if not inst.is_instance:
        continue
    ob = inst.object
    if ob is None or ob.type != "MESH":
        continue
    key = ob.data.name if ob.data else ob.name
    if key not in cache:
        try:
            me = ob.to_mesh()
        except Exception:
            cache[key] = 0
            continue
        if me is None:
            cache[key] = 0
            continue
        c = 0
        for p in me.polygons:
            c += max(len(p.vertices) - 2, 1)
        cache[key] = c
        ob.to_mesh_clear()
    inst_tris += cache[key]
    n_inst += 1

print(f"INSTANCES {inst_tris:>15,} tris across {n_inst:,} realized instances "
      f"from {len(cache):,} distinct source meshes")
print(f"RENDERED  {ev_tris + inst_tris:>15,} tris total  <- what Cycles traces")
print(f"({time.time()-t0:.0f}s)")

# ---- biggest contributors ------------------------------------------------
tops = []
for ob in sc.objects:
    if ob.type != "MESH":
        continue
    oe = ob.evaluated_get(deps)
    try:
        me = oe.to_mesh()
    except Exception:
        continue
    if me is None:
        continue
    c = sum(max(len(p.vertices) - 2, 1) for p in me.polygons)
    oe.to_mesh_clear()
    if c > 20000:
        tops.append((c, ob.name))
tops.sort(reverse=True)
print("\nheaviest single objects:")
for c, n in tops[:15]:
    print(f"  {c:>12,}  {n}")
