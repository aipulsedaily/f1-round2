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
# R2-1824: `nearband` runs AFTER `terrain` and that order is structural, not a
# preference -- it captures five objects from terrain's own build (see the
# terrain branch below).  `items` still runs LAST, because an item may SUPERSEDE
# class-level geometry and can only take out what has already been built.
MODS = opt("mods",
           "surface,barriers,architecture,terrain,nearband,dressing,items").split(",")
if "nearband" in MODS and "terrain" in MODS \
        and MODS.index("nearband") < MODS.index("terrain"):
    raise SystemExit("REFUSING: --mods puts nearband before terrain; it reads "
                     "objects terrain has not made yet.")
NEARBAND_CTX = {}

# clean file
bpy.ops.wm.read_factory_settings(use_empty=True)

import world_contract as C
print("[ASM] world_contract v%s" % C.__version__)

report = {"contract": C.__version__, "mods": {}}
t_all = time.time()


def _source_fingerprint():
    """sha256 of every generator module, taken NOW -- at READ time.

    R2-1822.  The staleness guard downstream used to compare the assembly's
    SAVE mtime against each module's mtime, and that cannot see the failure it
    exists to catch.  `assembly11.blend` read `world/build_terrain.py` at 22:06,
    the file was rewritten at 22:25 -- during its own terrain stage -- and the
    blend was saved at 22:40.  Save-time > module-mtime, so the check reported
    FRESH while the artefact was built from a source state that no longer
    existed anywhere.  A content hash taken at read time is the only thing that
    pins what a build actually consumed, so it is recorded here and travels with
    the artefact in `<blend>_build.json` and in the scene itself.

    R2-3542: THE FINGERPRINT HAD A BLIND SPOT WIDER THAN THE THING IT COVERED.

    Until now this enumerated `world/build_*.py`, `world_contract.py` and
    `itemkit.py` and nothing else.  Three load-bearing inputs were therefore
    invisible to it:

      * `world/items/PLACEMENT.json` -- decides which item rows are PLACEd.
        Measured at R2-3482: HEAD marks 1 row PLACE where the shipped world
        marks 4.  Two assemblies built from those two states differ by 1,586
        objects (`CFP` 676, `SPECX` 900, `TS` 10) and, before this change,
        CARRIED IDENTICAL FINGERPRINTS.  Not a crash -- a silent 1,586-object
        hole reported as a clean build.
      * `world/items/*.py` -- the item generators themselves.  `build_surface`
        imports `tyre_deposit` from here, so this directory is not even
        confined to the `items` stage.
      * `assemble.py` -- THIS FILE, which chooses the module set and their
        order.  A build with `nearband` dropped from `MODS` fingerprinted
        identically to one with it in.

    A fingerprint that omits the inputs deciding 1,586 objects is not a weaker
    guarantee than one that includes them; it is a FALSE one, because its whole
    purpose is to answer "would a rebuild be this file?" and it answered yes.
    Widening it can only turn false FRESH into true STALE.

    Keys are repo-relative so `tools/build_film_scene.py` and
    `tools/car_staleness.py`, which both re-resolve each key against the repo
    root, keep working unchanged on the wider set.
    """
    import hashlib
    out = {}

    def take(relpath, abspath):
        try:
            with open(abspath, "rb") as fh:
                out[relpath] = hashlib.sha256(fh.read()).hexdigest()
        except OSError:
            out[relpath] = None

    wdir = WORLD          # the repo's world/, already resolved at module import;
                          # deriving it again from __file__ got the depth wrong
                          # and silently fingerprinted ZERO modules (R2-1826).
    names = [f for f in os.listdir(wdir)
             if f.endswith(".py") and (f.startswith("build_")
                                       or f in ("world_contract.py", "itemkit.py"))]
    for fn in sorted(names):
        take("world/" + fn, os.path.join(wdir, fn))

    # The item generators and their placement table.  `.json` matters as much as
    # `.py` here: PLACEMENT.json is the file that decides the 1,586 objects.
    idir = os.path.join(wdir, "items")
    try:
        inames = sorted(f for f in os.listdir(idir)
                        if f.endswith(".py") or f.endswith(".json"))
    except OSError:
        inames = []
    for fn in inames:
        take("world/items/" + fn, os.path.join(idir, fn))

    # The assembler itself -- it chooses MODS and their order.
    take("render/world/assembly/r2/assemble.py", os.path.abspath(__file__))

    return out


report["source_sha256"] = _source_fingerprint()
report["source_read_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
print("[ASM] source fingerprint taken over %d module(s) at %s"
      % (len(report["source_sha256"]), report["source_read_utc"]))


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
            # R2-1824.  `nearband` needs the SAME Ground/GridZ/CameraPath/Raster
            # and library that terrain built, not equivalents: a second GridZ
            # sampled on a coarser grid is a different height field, and plants
            # placed against it sit at a different z from the woodland they are
            # meant to blend into.  `capture_terrain` wraps those five
            # constructors for the duration of THIS call and records the
            # instances, restoring the module attributes afterwards --
            # build_terrain.py is not modified.  So the capture has to happen
            # here, around terrain's own build, and nearband cannot precede it.
            if "nearband" in MODS:
                import numpy as _np
                import build_nearband as NB
                with NB.capture_terrain() as cap:
                    s = B.build()
                missing = [n for n in NB.capture_terrain.NAMES if n not in cap.got]
                if missing:
                    raise RuntimeError(
                        "nearband context capture incomplete: %s. Refusing to "
                        "build the near band against objects terrain did not "
                        "make." % (missing,))
                NEARBAND_CTX.update(dict(
                    gr=cap.got["Ground"], gz=cap.got["GridZ"],
                    cam=cap.got["CameraPath"], ras=cap.got["Raster"],
                    lib=cap.got["build_library"],
                    rng=_np.random.default_rng(NB.SEED),
                    root=bpy.data.collections.get(B.COLL),
                    dom=(-1520.0, 1440.0, -1120.0, 1840.0)))
                print("[ASM] nearband context captured: %s"
                      % ", ".join(sorted(cap.got)))
            else:
                s = B.build()
        elif m == "nearband":
            import build_nearband as NB
            if not NEARBAND_CTX:
                raise RuntimeError(
                    "nearband ran without a terrain context. It CAPTURES "
                    "CameraPath/GridZ/Ground/Raster/build_library from terrain, "
                    "so it cannot precede what it reads -- put 'terrain' before "
                    "'nearband' in --mods.")
            s = NB.build(ctx=NEARBAND_CTX)
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
# R2-1822: the fingerprint travels INSIDE the artefact, not only in the sidecar.
# A sidecar can be regenerated, moved, or read for the wrong blend; a scene key
# cannot be separated from the world it describes.
bpy.context.scene["world_source_sha256"] = json.dumps(report["source_sha256"])
bpy.context.scene["world_source_read_utc"] = report["source_read_utc"]
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
