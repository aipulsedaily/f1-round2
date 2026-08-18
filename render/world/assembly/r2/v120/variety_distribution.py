"""PER-FAMILY SOURCE DISTRIBUTION of every realized instance in the world (#28-3).

    blender -b <assembly>.blend --factory-startup -P v120/variety_distribution.py -- OUT.json

`tools/instance_variety.py` answers the question at the coarsest possible
grouping -- the FIRST token of the emitter's name, which on this world is four
buckets (VEG / BR / DR / TER).  "VEG draws on 310 sources" cannot distinguish

    40 grass species x 8 growth stages          (ample)
    a handful of trees carrying 4.7 M instances (the red line)

because both live inside the same bucket.  This splits the emitters two tokens
deep, and for every group reports the full source histogram, not a summary:

    sources          distinct evaluated source MESH datablocks
    n_eff_simpson    1 / sum(p^2) -- the number of EQUALLY-COMMON sources that
                     would give the same concentration.  This is the honest
                     count: 310 nominal sources with n_eff = 3 is three sources
                     with 307 decorations.
    n_eff_shannon    exp(H), the same idea, less punishing of a long tail
    top_share        share of the single commonest source
    gini             0 = perfectly even, 1 = one mesh is everything

Both effective counts are reported because they disagree in exactly the case
that matters -- a few dominant sources plus a long rare tail -- and a reader
who sees both cannot be misled by either.
"""
import sys, os, re, json, math, time
from collections import Counter, defaultdict
import bpy

# WHERE THIS WRITES.  Was the copy-pasted `sys.argv[-1] if ... else
# "variety_distribution.json"` idiom (fixed 2026-08-02): it took the LAST
# argument whatever it was, and given nothing usable it silently invented a
# relative filename resolved against the caller's CWD.  See the note in
# lib_probe.py.  This script has no other reason to load lib_probe -- doing so
# would drag in world_contract -- so it execs ONLY the marked resolver block,
# keeping one source of truth for output paths.
_LIB = os.path.expanduser("~/f1-round2/render/world/assembly/r2/lib_probe.py")
_BLK = re.search(r"^# --- BEGIN resolve_out.*?^# --- END resolve_out.*?$",
                 open(_LIB).read(), re.S | re.M)
if not _BLK:
    raise SystemExit("[VD] no resolve_out block in %s" % _LIB)
exec(compile(_BLK.group(0), _LIB, "exec"))
OUT = resolve_out(sys.argv, blend_path=(bpy.data.filepath or None),
                  tool="variety_distribution")
print("[VD] output ->", OUT)
T0 = time.time()


def key2(name):
    p = name.split("_")
    return "_".join(p[:2]) if len(p) >= 2 else name


deps = bpy.context.evaluated_depsgraph_get()
fam1 = defaultdict(Counter)      # first token  (what instance_variety reports)
fam2 = defaultdict(Counter)      # two tokens deep
src_global = Counter()
emitters = Counter()
total = 0
for inst in deps.object_instances:
    if not inst.is_instance:
        continue
    ob = inst.object
    if ob is None or ob.type != "MESH":
        continue
    parent = inst.parent
    ename = parent.name if parent else ob.name
    src = ob.data.name if ob.data else ob.name
    fam1[ename.split("_")[0] if "_" in ename else ename][src] += 1
    fam2[key2(ename)][src] += 1
    src_global[src] += 1
    emitters[ename] += 1
    total += 1

print("[VD] %d realized instances, %d distinct source meshes, %d emitters"
      % (total, len(src_global), len(emitters)))


def gini(counts):
    xs = sorted(counts); n = len(xs); s = sum(xs)
    if not n or not s:
        return 0.0
    return (2.0 * sum((i + 1) * x for i, x in enumerate(xs))) / (n * s) - (n + 1.0) / n


def describe(c, topn=10):
    n = sum(c.values())
    ps = [v / n for v in c.values()]
    simpson = 1.0 / sum(p * p for p in ps)
    H = -sum(p * math.log(p) for p in ps if p > 0)
    top = c.most_common(topn)
    return {"instances": n, "sources": len(c),
            "n_eff_simpson": round(simpson, 2),
            "n_eff_shannon": round(math.exp(H), 2),
            "top_share": round(top[0][1] / n, 4),
            "top10_share": round(sum(v for _, v in top) / n, 4),
            "gini": round(gini(list(c.values())), 4),
            "instances_per_source": round(n / len(c), 1),
            "top": [[k, v, round(v / n, 5)] for k, v in top]}


R = {"total_realized_instances": total,
     "distinct_source_meshes": len(src_global),
     "distinct_emitters": len(emitters),
     "global": describe(src_global, 25),
     "by_first_token": {k: describe(v) for k, v in
                        sorted(fam1.items(), key=lambda kv: -sum(kv[1].values()))},
     "by_two_tokens": {k: describe(v) for k, v in
                       sorted(fam2.items(), key=lambda kv: -sum(kv[1].values()))}}

# instances-per-source histogram, so "310 sources" can be read as a shape
hist = Counter()
for v in src_global.values():
    hist[int(math.floor(math.log10(max(v, 1))))] += 1
R["sources_by_instance_decade"] = {("1e%d" % k): v for k, v in sorted(hist.items())}

# non-instanced objects, the other half of the repetition question
obj_fam = defaultdict(Counter)
for o in bpy.context.scene.objects:
    if o.type == "MESH" and o.data is not None:
        obj_fam[key2(o.name)][o.data.name] += 1
R["objects_by_two_tokens"] = {
    k: {"objects": sum(v.values()), "meshes": len(v),
        "top_share": round(v.most_common(1)[0][1] / sum(v.values()), 4),
        "top_mesh": v.most_common(1)[0][0]}
    for k, v in sorted(obj_fam.items(), key=lambda kv: -sum(kv[1].values()))}

hdr = ("%-26s %13s %8s %10s %10s %10s %7s" %
       ("group", "instances", "sources", "n_eff_smp", "n_eff_shn", "top share", "gini"))
print(hdr); print("-" * len(hdr))
for k, d in R["by_two_tokens"].items():
    v = ("*** SPAM" if d["top_share"] > 0.40 else
         "concentrated" if d["top_share"] > 0.20 or d["gini"] > 0.60 else "varied")
    print("%-26s %13d %8d %10.2f %10.2f %9.2f%% %7.3f   %s"
          % (k, d["instances"], d["sources"], d["n_eff_simpson"],
             d["n_eff_shannon"], 100 * d["top_share"], d["gini"], v))

R["secs"] = round(time.time() - T0, 1)
# Which assembly was this distribution measured on? `variety_distribution_v120.json`
# and `..._v121.json` are compared to each other; a comparison between two files
# that cannot name their input is a comparison of two anecdotes.
sys.path.insert(0, os.path.expanduser("~/f1-round2/tools"))
import provenance as _prov                                       # noqa: E402
R = dict([(_prov.STAMP_KEY, _prov.stamp(
    tool_file=__file__, tool_version="variety_distribution",
    inputs=[("blend", bpy.data.filepath or None)]))] + list(R.items()))
json.dump(R, open(OUT, "w"), indent=1)
print("[VD] wrote", OUT, "in %.1fs" % R["secs"])
