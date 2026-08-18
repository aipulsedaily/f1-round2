"""DRESS AN ALREADY-LANDED BREACH: add the fines, frost the fracture faces.

    blender -b render/film16_breach.blend -P sim/breach_dress.py -- \
        --fines sim/out/breach_debris.npz --frost \
        --out render/film16_breach_DRESSED.blend

WHY THIS EXISTS AND IS NOT `apply_breach.py`
============================================
`apply_breach` BUILDS a breach into a scene that has none.  `film16_breach.blend`
already has one -- 3,845 objects, landed, verified three ways, and it is the ship
candidate.  Re-running the applier on it would build a second wall.  What is
needed instead is two additive edits to a scene that is already correct:

    --fines   link a BREACH_Fines collection from sim/out/breach_debris.npz
    --frost   rewrite BREACH_Glass so a fracture face is not a polished one,
              and stamp each shard's own fracture data onto its object

Both call straight into `sim/apply_breach.py` -- `build_debris`,
`frost_glass_material`, `stamp_fracture_props` -- so there is exactly ONE
implementation of each and a fresh apply and a dressed blend cannot disagree.
That is the same rule `shardmesh.py` is written to: the sim and the render
import the same mesher because a second one is a second answer.

THE TWO FLAGS ARE INDEPENDENT ON PURPOSE.  They are different defects with
different evidence and different risk: the fines add 4.68 M triangles, the
frosting adds none.  Either must be revertible without the other, so each is its
own flag, its own report block, and its own commit.

IT REFUSES RATHER THAN WRITING A PLAUSIBLE WRONG SCENE.  If the target has no
BREACH collection, or no BREACH_Glass, or already has fines, it says so and
stops.  `--force` is not offered: there is no case where dressing the wrong
scene is what somebody meant.
"""

import argparse
import json
import os
import sys
import time

import bpy                                                        # noqa: E402

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(R2, "sim"), os.path.join(R2, "anim")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import apply_breach as AB                                         # noqa: E402
import fracture as FR                                             # noqa: E402

T0 = time.time()


def log(m):
    print("[dress %7.1fs] %s" % (time.time() - T0, m))
    sys.stdout.flush()


def parse():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--src", default="",
                   help="blend to OPEN first.  `rq exec` runs "
                        "`blender -b --factory-startup -P <entry>` with NO "
                        "scene loaded and stages the scene beside the script "
                        "as `scene.blend`, so under exec this is required.  "
                        "Omit it when driving Blender directly with "
                        "`blender -b <blend> -P sim/breach_dress.py`.")
    p.add_argument("--out", required=True)
    p.add_argument("--fines", default="",
                   help="path to sim/out/breach_debris.npz")
    p.add_argument("--frost", action="store_true")
    p.add_argument("--shards",
                   default=os.path.join(R2, "sim/out/fracture_wall.npz"))
    p.add_argument("--fines-material", default="BREACH_Fines")
    p.add_argument("--report",
                   default=os.path.join(R2, "sim/out/dress_report.json"),
                   help="under `rq exec` point this at out/, because "
                        "EVERYTHING OUTSIDE out/ IS DELETED when the child "
                        "exits -- a report written anywhere else is a report "
                        "nobody will ever read.")
    p.add_argument("--dry-run", action="store_true",
                   help="check the target and report, write nothing")
    return p.parse_args(argv)


def preflight(a):
    """What must be true of the target, checked and reported before any edit."""
    c = {}
    root = bpy.data.collections.get("BREACH")
    c["BREACH collection present"] = root is not None
    sh = bpy.data.collections.get("BREACH_Shards")
    c["BREACH_Shards present"] = sh is not None
    c["shard count > 3000"] = bool(sh and len(sh.objects) > 3000)
    c["BREACH_Glass material present"] = \
        bpy.data.materials.get("BREACH_Glass") is not None
    have_fines = bpy.data.collections.get("BREACH_Fines")
    c["no fines already present"] = have_fines is None or \
        len(have_fines.objects) == 0
    sc = bpy.context.scene
    c["frame_end == 2978"] = sc.frame_end == 2978
    c["unit scale == 1.0"] = abs(sc.unit_settings.scale_length - 1.0) < 1e-9
    if a.fines:
        c["fines table exists"] = os.path.exists(a.fines)
    detail = dict(
        shards=len(sh.objects) if sh else 0,
        objects=len(bpy.data.objects),
        blend=bpy.data.filepath,
        frame_range=[sc.frame_start, sc.frame_end])
    return c, detail


def main():
    a = parse()
    if a.src:
        if not os.path.exists(a.src):
            raise SystemExit("STAGE RESULT: dress FAIL -- no --src at %s"
                             % a.src)
        log("opening %s (%.2f GB)"
            % (a.src, os.path.getsize(a.src) / 1e9))
        bpy.ops.wm.open_mainfile(filepath=a.src)
        log("opened: %d objects" % len(bpy.data.objects))
    if not a.fines and not a.frost:
        raise SystemExit("STAGE RESULT: dress FAIL -- nothing asked for; "
                         "pass --fines and/or --frost")

    checks, detail = preflight(a)
    for k, v in checks.items():
        log("  preflight %-32s %s" % (k, "PASS" if v else "FAIL"))
    log("  target: %s" % json.dumps(detail))
    if not all(checks.values()):
        raise SystemExit(
            "STAGE RESULT: dress FAIL -- the target is not a landed breach "
            "scene: %s" % [k for k, v in checks.items() if not v])

    rep = dict(target=detail, preflight=checks, out=a.out,
               fines=None, frost=None)

    # ---- FROST first: it is cheap, and if it fails the fines are wasted ----- #
    if a.frost:
        plan = FR.load(a.shards)
        st = AB.stamp_fracture_props(plan)
        log("frost: stamped fx_energy/fx_size on %d shards (%d missing)"
            % (st["stamped"], st["missing"]))
        if st["stamped"] < 3000:
            raise SystemExit(
                "STAGE RESULT: dress FAIL -- only %d shards took the fracture "
                "properties; the material would read 0 for the rest and "
                "silently render them clear" % st["stamped"])
        mat = bpy.data.materials["BREACH_Glass"]
        fx = AB.frost_glass_material(mat)
        log("frost: %s" % json.dumps(fx))
        rep["frost"] = dict(stamp=st, material=fx)

    # ---- FINES -------------------------------------------------------------- #
    if a.fines:
        root = bpy.data.collections.get("BREACH")
        C = bpy.data.collections.get("BREACH_Fines")
        if C is None:
            C = bpy.data.collections.new("BREACH_Fines")
            root.children.link(C)
        ns = type("NS", (), dict(debris=a.fines,
                                 fines_material=a.fines_material))()
        st = AB.build_debris(ns, C)
        log("fines: %s" % json.dumps({k: v for k, v in st.items()
                                      if k != "report"}))
        proof = AB.prove_curves(C)
        log("fines curve proof: %s" % json.dumps(proof))
        if proof["flags"]["other"] or proof["max_linear_eval_err"] > 1e-4:
            raise SystemExit("STAGE RESULT: dress FAIL -- the fines curves are "
                             "not LINEAR by evaluation: %s" % proof)
        rep["fines"] = dict(stats={k: v for k, v in st.items()
                                   if k != "report"}, proof=proof)

    sc = bpy.context.scene
    rep["after"] = dict(objects=len(bpy.data.objects),
                        added=len(bpy.data.objects) - detail["objects"])
    if a.dry_run:
        log("--dry-run: wrote nothing")
        print("STAGE RESULT: dress DRYRUN")
        return

    bpy.ops.wm.save_as_mainfile(filepath=a.out)
    rep["bytes"] = os.path.getsize(a.out)
    with open(a.report, "w") as fh:
        json.dump(rep, fh, indent=1, default=float)
    log("wrote %s (%.1f MB)" % (a.out, rep["bytes"] / 1e6))
    print("STAGE RESULT: dress PASS")


if __name__ == "__main__":
    main()
