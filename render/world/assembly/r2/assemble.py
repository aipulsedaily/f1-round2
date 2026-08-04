"""Assemble every world module into ONE Blender scene and save it.

    blender -b -noaudio -P assemble.py -- --out X.blend [--mods surface,barriers,...]

Nothing here builds geometry of its own.  It calls each module's own build() in
an order that respects the contract's ownership rules and reports what each one
produced, so that the assembled result can be probed as a single world.
"""
import sys, os, time, json, gc

import bpy

WORLD = "/home/zany/f1-round2/world"
if WORLD not in sys.path:
    sys.path.insert(0, WORLD)

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def opt(name, default=None):
    for a in argv:
        if a.startswith("--%s=" % name):
            return a.split("=", 1)[1]
    return default


OUT = opt("out", "/home/zany/f1-round2/render/world/assembly/assembly.blend")
# `items` runs LAST and deliberately so: an item may SUPERSEDE class-level
# geometry, and it can only take out what has already been built.  Before it
# existed, 0 of 41 item modules reached the ship -- see world/build_items.py and
# docs/ITEM-PRESENCE-CENSUS.md.  It places only the rows
# `world/items/PLACEMENT.json` marks PLACE, and refuses anything with no row.
MODS = opt("mods",
           "surface,barriers,architecture,terrain,dressing,items").split(",")

# clean file
bpy.ops.wm.read_factory_settings(use_empty=True)

import world_contract as C
print("[ASM] world_contract v%s" % C.__version__)

report = {"contract": C.__version__, "mods": {}}
t_all = time.time()


def mem():
    try:
        with open("/proc/self/status") as f:
            for ln in f:
                if ln.startswith("VmRSS"):
                    return ln.split()[1:3]
    except Exception:
        pass
    return ["?"]


for m in MODS:
    t0 = time.time()
    print("\n" + "=" * 78)
    print("[ASM] building %s   (rss %s)" % (m, " ".join(mem())))
    print("=" * 78)
    sys.stdout.flush()
    try:
        if m == "surface":
            import build_surface as B
            s = B.build()
        elif m == "barriers":
            import build_barriers as B
            s = B.build()
        elif m == "terrain":
            import build_terrain as B
            s = B.build()
        elif m == "architecture":
            import build_architecture as B
            s = B.build(verify=("--noverify" not in argv))
        elif m == "dressing":
            import build_dressing as B
            s = B.build()
        elif m == "items":
            import build_items as B
            s = B.build()
        elif m == "sky":
            import build_sky as B
            s = B.build(bpy.context.scene, None)
        else:
            raise RuntimeError("unknown module " + m)
        ok = True
        err = None
    except Exception as e:
        import traceback
        traceback.print_exc()
        s, ok, err = {}, False, repr(e)
    dt = time.time() - t0
    n = len([o for o in bpy.data.objects])
    report["mods"][m] = {"ok": ok, "err": err, "s": round(dt, 1),
                         "objects_total": n,
                         "summary": {k: v for k, v in (s or {}).items()
                                     if isinstance(v, (int, float, str, bool))}}
    print("[ASM] %s: ok=%s %.1fs  scene objects now %d  rss %s"
          % (m, ok, dt, n, " ".join(mem())))
    sys.stdout.flush()
    gc.collect()

bpy.context.view_layer.update()

# census by collection prefix
pref = {}
for ob in bpy.data.objects:
    p = ob.name.split("_")[0]
    pref[p] = pref.get(p, 0) + 1
report["object_prefixes"] = pref
report["total_objects"] = len(bpy.data.objects)
report["total_meshes"] = len(bpy.data.meshes)
report["total_materials"] = len(bpy.data.materials)
report["build_s"] = round(time.time() - t_all, 1)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=False)
report["blend"] = OUT
report["blend_mb"] = round(os.path.getsize(OUT) / 1048576.0, 1)
with open(OUT.replace(".blend", "_build.json"), "w") as f:
    json.dump(report, f, indent=1, default=str)
print("\n[ASM] " + json.dumps(report, indent=1, default=str))

# THE VERDICT LINE.  The loop above catches every module exception and carries
# on, deliberately -- one broken module should still leave a probeable blend.
# But Blender 5.2 exits 0 on an uncaught script exception anyway, so `$?` was
# never the signal, and until now NOTHING printed a machine-readable verdict:
# a run in which `items` raised and built nothing looked exactly like a good one
# unless a human read 4,000 lines of log.  Judge this build on this line only.
_failed = sorted(k for k, v in report["mods"].items() if not v["ok"])
_empty = sorted(k for k, v in report["mods"].items()
                if v["ok"] and not v["summary"])
if _failed:
    print(">> ASM MODULES FAILED: %s" % ", ".join(_failed))
    for k in _failed:
        print(">>   %s: %s" % (k, report["mods"][k]["err"]))
if _empty:
    print(">> ASM MODULES RETURNED AN EMPTY SUMMARY: %s" % ", ".join(_empty))
print(">> STAGE RESULT: %s"
      % ("ASSEMBLE_FAIL" if _failed else "ASSEMBLE_OK"))
