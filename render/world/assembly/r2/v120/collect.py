"""Collect every result of the #53 battery into one printout."""
import json, os, glob, sys

V = "/home/zany/f1-round2/render/world/assembly/r2/v120"
D = "/home/zany/f1-round2/render/world/assembly/r2"


def j(p):
    try:
        return json.load(open(p))
    except Exception as e:
        return {"__error__": repr(e)}


def hdr(t):
    print("\n" + "=" * 78 + "\n" + t + "\n" + "=" * 78)


hdr("BUILD")
for tag, p in (("assembly2 (1.0.1)", D + "/assembly2_build.json"),
               ("assembly3 (1.1.0)", D + "/assembly3_build.json"),
               ("assembly4 (1.1.1)", D + "/assembly4_build.json"),
               ("assembly5 (1.2.0)", D + "/assembly5_build.json")):
    b = j(p)
    if "__error__" in b:
        print(tag, b["__error__"]); continue
    tri = {}
    for m, r in b["mods"].items():
        s = r.get("summary", {})
        tri[m] = s.get("triangles") or s.get("tris") or s.get("base_tris") or \
            s.get("evaluated_tris")
    print("%-18s objects %6d  meshes %5d  mats %4d  %6.1fs  %7.1f MB  %s"
          % (tag, b["total_objects"], b["total_meshes"], b["total_materials"],
             b["build_s"], b["blend_mb"], b["object_prefixes"]))
    for m, r in b["mods"].items():
        s = r.get("summary", {})
        print("      %-14s %7.1fs  tris %s" % (m, r["s"], tri[m]))

hdr("PLACEMENT GATE")
for tag, p in (("v1.1.1 assembly4 (baseline)", "/home/zany/f1-round2/docs/placement_after_46.json"),
               ("v1.2.0 assembly5 default", V + "/placement_v120.json"),
               ("v1.2.0 assembly5 +ground", V + "/placement_v120_ground.json"),
               ("CONTROL positive", V + "/ctl_place_pos.json"),
               ("CONTROL negative", V + "/ctl_place_neg.json")):
    r = j(p)
    if "__error__" in r:
        print("%-30s %s" % (tag, r["__error__"])); continue
    print("%-30s violations %2s   closest %s"
          % (tag, r.get("total"),
             {k: (v["object"], v["clearance_m"])
              for k, v in (r.get("closest_approach_m") or {}).items()}))
    for v in r.get("violations", []):
        print("      %-24s %-14s %.3f m in at %s"
              % (v["object"], v["volume"], v["intrusion_m"], v["at_world"]))

hdr("ROAD CORRIDOR, GROUND-REFERENCED (probe_roadclear)")
r = j(V + "/roadclear_v120.json")
if "__error__" not in r:
    print(json.dumps({k: v for k, v in r.items() if k != "violations"}, indent=1))
    for v in r.get("violations", [])[:20]:
        print("   ", v)
else:
    print(r)

hdr("COLLISION GATE / DEPTH PROBE (+ controls)")
for tag, p in (("collision world", V + "/collision_v120.json"),
               ("collision CONTROL pos", V + "/ctl_collide_pos.json"),
               ("collision CONTROL neg", V + "/ctl_collide_neg.json"),
               ("depth world", V + "/depth_v120.json"),
               ("depth CONTROL pos", V + "/ctl_depth_pos.json"),
               ("depth CONTROL neg", V + "/ctl_depth_neg.json")):
    print("%-24s %s" % (tag, json.dumps(j(p))[:400]))

hdr("MODULE BOUNDARY (probeD / probeG) — v1.0.1 baseline vs v1.2.0")
# THIS LINE READ THE ASSEMBLY ROOT, AND THAT IS THE BUG.
#
# `probeD.py` used to write `probeD.json` into the assembly root whatever
# version ran it, so v121/battery.sh's run overwrote the file this collector
# reads and the "v1.0.1 baseline vs v1.2.0" table below silently compared the
# baseline against v121's numbers. The probes now take --out and the v120
# battery writes `v120/probeD_v120.json`, so this reads THIS version's own
# artefact.
#
# The legacy path is still tried, and SAID SO when it is used, because a file
# in the assembly root now has no version attached to it and reading it
# silently would be the same defect wearing the fix's clothes.
_new_p = V + "/probeD_v120.json"
if not os.path.exists(_new_p):
    _legacy = D + "/probeD.json"
    print("!! %s does not exist; falling back to the LEGACY shared path %s,\n"
          "!! which any version's battery may have written. Re-run\n"
          "!! v120/battery.sh to get a version-attributed file."
          % (_new_p, _legacy))
    _new_p = _legacy
old = j(V + "/baseline_assembly2/probeD.json").get("bvh", {})
new = j(_new_p).get("bvh", {})
print("(probeD read from %s)" % _new_p)
for k in sorted(set(old) | set(new)):
    print("%-46s  was %6s -> now %6s tri-pairs"
          % (k, old.get(k, {}).get("triangle_pairs", "-"),
             new.get(k, {}).get("triangle_pairs", "-")))
    for pr in new.get(k, {}).get("pairs", []):
        print("        %s x %s  %d" % (pr["a"], pr["b"], pr["tri_pairs"]))
print("BVH machinery control:", json.dumps(j(V + "/ctl_bvh.json")))

hdr("VARIETY")
print("shipped instance_variety:", json.dumps(j(V + "/instance_variety_v120.json"))[:800])
print("CONTROL spam :", json.dumps(j(V + "/ctl_variety_pos.json"))[:400])
print("CONTROL varied:", json.dumps(j(V + "/ctl_variety_neg.json"))[:400])
vd = j(V + "/variety_distribution_v120.json")
if "__error__" not in vd:
    print("\ntotal %d instances over %d distinct source meshes, %d emitters"
          % (vd["total_realized_instances"], vd["distinct_source_meshes"],
             vd["distinct_emitters"]))
    print("global:", json.dumps({k: v for k, v in vd["global"].items() if k != "top"}))
    print("sources by instance decade:", vd["sources_by_instance_decade"])
    print("\n%-28s %12s %8s %10s %10s %9s %7s" %
          ("group", "instances", "sources", "n_eff_smp", "n_eff_shn", "top%", "gini"))
    for k, d in vd["by_two_tokens"].items():
        print("%-28s %12d %8d %10.2f %10.2f %8.2f%% %7.3f"
              % (k, d["instances"], d["sources"], d["n_eff_simpson"],
                 d["n_eff_shannon"], 100 * d["top_share"], d["gini"]))
    print("\ntop 15 sources world-wide:")
    for k, v, s in vd["global"]["top"][:15]:
        print("   %-44s %9d  %6.3f %%" % (k, v, 100 * s))

hdr("PIT EXIT #47 / #48 / #50")
for tag, p in (("assembly3 1.1.0", D + "/probe_pitexit_before2.json"),
               ("assembly4 1.1.1", D + "/probe_pitexit_after.json"),
               ("assembly5 1.2.0", V + "/pitexit_v120.json")):
    r = j(p)
    if "__error__" in r:
        print(tag, r["__error__"]); continue
    keys = [k for k in r if k not in ("seam_maps", "recess", "columns")]
    print("\n---", tag, "keys:", list(r.keys()))
    print(json.dumps({k: r[k] for k in r if not isinstance(r[k], (list,))
                      or len(str(r[k])) < 600}, indent=1)[:3000])
