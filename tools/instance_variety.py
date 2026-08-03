"""Is the world's instanced vocabulary genuine variety, or one asset spammed?

    /opt/blender-5.2.0-linux-x64/blender -b <assembly.blend> --factory-startup \
        -P tools/instance_variety.py -- --out docs/instance_variety.json

WHY
---
    "i dont want repeat stuff aka one tree spammed 100 times everything has to
     be thought out no matter what"

The assembled world traces 13.18 billion triangles from 4,688,475 realized
instances -- but those resolve to only 310 distinct source meshes. That single
number cannot say whether the world is rich or repetitive: 310 sources is ample
if it is 40 grass species across 8 growth stages, and damning if 4.7 M instances
lean on a handful of trees.

The distribution is what answers it, per family:

    sources          how many distinct meshes that family draws from
    top_share        what fraction of the family is its single commonest mesh
    gini             concentration of the whole distribution, 0 = perfectly
                     even, 1 = one mesh is everything

`top_share` is the number that catches the named failure. A family of 500,000
grass clumps whose commonest mesh is 60 % of the population IS one tree spammed,
however many rare variants pad the tail.

THE VERDICT WAS PRINTED AND NEVER RETURNED                         (R2, 2026-08-03)
-----------------------------------------------------------------------------
This file printed `*** SPAM: one mesh is most of it` per family and then exited
0, with no `STAGE RESULT` line at all. So the one failure it was written to
catch was invisible to every caller that branched on `$?`, and invisible to any
log scraper looking for the project's verdict convention. Both are fixed below:
one `STAGE RESULT` token, derived from the same `top_share` threshold the table
prints, and an exit code derived from that token by `tools/gate_exit.py`.

Zero instances is now VACUOUS, not clean. A world with no realized instances
told this tool nothing about variety, and "0 families, none of them spam" is
the emptiest possible pass.
"""
import argparse, json, math, os, sys
from collections import Counter, defaultdict
import bpy

# Imported by path, not by package: this runs inside Blender's interpreter with
# whatever cwd the caller happened to have.
if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gate_exit                                                 # noqa: E402

# Blender 5.2 returns 0 for a script that raised. This is a straight-line
# script, not a main() — install() arms sys.excepthook and an atexit sentinel
# so a crash or an early stop is a status 2, not a silent pass.
gate_exit.install(tool="instance_variety")

SPAM_TOP_SHARE = 0.40     # the same number the table's verdict column uses

argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True)
a = ap.parse_args(argv)

deps = bpy.context.evaluated_depsgraph_get()
fam = defaultdict(Counter)
total = 0
for inst in deps.object_instances:
    if not inst.is_instance:
        continue
    ob = inst.object
    if ob is None or ob.type != "MESH":
        continue
    parent = inst.parent
    key = (parent.name if parent else ob.name)
    # family = leading token of the emitter's name (VEG_, BR_, DR_ ...)
    f = key.split("_")[0] if "_" in key else key
    fam[f][ob.data.name if ob.data else ob.name] += 1
    total += 1

def gini(counts):
    xs = sorted(counts)
    n = len(xs)
    if n == 0 or sum(xs) == 0:
        return 0.0
    cum = sum((i + 1) * x for i, x in enumerate(xs))
    return (2.0 * cum) / (n * sum(xs)) - (n + 1.0) / n

rows = []
for f, c in fam.items():
    n = sum(c.values())
    top = c.most_common(1)[0]
    rows.append({"family": f, "instances": n, "sources": len(c),
                 "top_source": top[0], "top_share": round(top[1] / n, 4),
                 "gini": round(gini(list(c.values())), 4),
                 "instances_per_source": round(n / len(c), 1)})
rows.sort(key=lambda r: -r["instances"])

spam = [r for r in rows if r["top_share"] > SPAM_TOP_SHARE]

json.dump({"total_instances": total, "families": rows,
           "spam_top_share_threshold": SPAM_TOP_SHARE,
           "spam_families": [r["family"] for r in spam],
           "vacuous": total == 0},
          open(a.out, "w"), indent=1)

print(f"TOTAL {total:,} realized instances\n")
print(f"{'family':<10}{'instances':>12}{'sources':>9}{'inst/src':>10}"
      f"{'top share':>11}{'gini':>8}   verdict")
for r in rows:
    v = ("*** SPAM: one mesh is most of it" if r["top_share"] > SPAM_TOP_SHARE else
         "concentrated" if r["top_share"] > 0.20 or r["gini"] > 0.60 else
         "varied")
    print(f"{r['family']:<10}{r['instances']:>12,}{r['sources']:>9}"
          f"{r['instances_per_source']:>10,.0f}{r['top_share']*100:>10.1f}%"
          f"{r['gini']:>8.3f}   {v}")
print(f"\nwrote {a.out}")

# ---- the verdict, and the exit status, from the same number ---------------
if total == 0:
    print(">> REFUSING TO REPORT: this scene realized ZERO instances, so "
          "nothing about its variety was measured.")
    print(">> That is NOT a pass — an empty distribution cannot be spammed.")
    gate_exit.done("INSTANCE_VARIETY_VACUOUS")
elif spam:
    print(">> %d SPAMMED FAMILY/FAMILIES (one source mesh is more than "
          "%.0f %% of the family):" % (len(spam), SPAM_TOP_SHARE * 100))
    for r in spam:
        print("     %-10s %s is %.1f %% of %d instances"
              % (r["family"], r["top_source"], r["top_share"] * 100,
                 r["instances"]))
    gate_exit.done("INSTANCE_VARIETY_SPAM",
                   "  [%s]" % ",".join(r["family"] for r in spam))
else:
    print(">> no family leans on one source mesh past %.0f %%"
          % (SPAM_TOP_SHARE * 100))
    gate_exit.done("INSTANCE_VARIETY_CLEAN")
