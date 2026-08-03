"""Object-level mesh reuse per family — the repetition test for what ISN'T instanced."""
import bpy
from collections import Counter, defaultdict
fam_objs = defaultdict(Counter)      # family -> mesh name -> how many objects use it
for o in bpy.context.scene.objects:
    if o.type != "MESH" or o.data is None:
        continue
    f = o.name.split("_")[0] if "_" in o.name else o.name
    fam_objs[f][o.data.name] += 1
def gini(xs):
    xs = sorted(xs); n = len(xs); s = sum(xs)
    if not n or not s: return 0.0
    return (2.0*sum((i+1)*x for i,x in enumerate(xs)))/(n*s) - (n+1.0)/n
print(f"{'family':<10}{'objects':>9}{'meshes':>8}{'obj/mesh':>10}{'top share':>11}{'gini':>8}   commonest mesh")
rows=[]
for f,c in fam_objs.items():
    n=sum(c.values()); top=c.most_common(1)[0]
    rows.append((n,f,len(c),top,gini(list(c.values()))))
rows.sort(reverse=True)
for n,f,nm,top,g in rows:
    print(f"{f:<10}{n:>9,}{nm:>8,}{n/nm:>10.1f}{top[1]/n*100:>10.1f}%{g:>8.3f}   {top[0]} x{top[1]}")
