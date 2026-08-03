"""Per-object totals via shared mesh datablocks — cheap, no to_mesh()."""
import bpy
from collections import Counter
cache = {}
for me in bpy.data.meshes:
    me.calc_loop_triangles()
    cache[me.name] = len(me.loop_triangles)
tot = 0
per_prefix = Counter()
tops = []
for o in bpy.context.scene.objects:
    if o.type != "MESH" or o.data is None:
        continue
    c = cache.get(o.data.name, 0)
    tot += c
    per_prefix[o.name.split("_")[0]] += c
    tops.append((c, o.name))
print(f"SCENE_TRIS {tot:>15,}   (sum over objects, shared meshes counted per user)")
print(f"UNIQUE_TRIS {sum(cache.values()):>14,}   (sum over mesh datablocks)")
print(f"REUSE_FACTOR {tot/max(sum(cache.values()),1):>13.1f}x")
print("\nBY MODULE:")
for k, v in per_prefix.most_common(12):
    print(f"  {k:<16}{v:>15,}")
tops.sort(reverse=True)
print("\nHEAVIEST OBJECTS:")
for c, n in tops[:10]:
    print(f"  {c:>13,}  {n}")
