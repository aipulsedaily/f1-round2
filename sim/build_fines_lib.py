"""THE FINES AS AN APPENDABLE LIBRARY, and the round trip that proves it survives.

    blender -b --factory-startup -P sim/build_fines_lib.py -- \
        --debris sim/out/breach_debris.npz \
        --out out/breach_fines_lib.blend --report out/fines_lib.json

WHY A LIBRARY AND NOT A DRESSED FILM
====================================
The first architecture opened `film16_breach.blend` (7.97 GB) on the farm, added
the fines, and saved an 8 GB result to be fetched and re-uploaded.  It never got
to run.  The broker refused it, correctly and with the clearest message this
system produces:

    ExecMemoryShort: opening film16_breach.blend (7.97 GB) needs about 43.8 GB
    free and the box has 11.7 GB -- the render worker is holding a scene of its
    own.  Waiting rather than being OOM-killed at `Read blend` ... [attempt
    refunded]

**That is the ceiling's wall, and the ceiling already went round it.** A
post-append tool that opened the 7.9 GB film, edited it and saved it was killed
three times locally for swap exhaustion and could not be moved to the farm
either; the answer was not a bigger box, it was `world/showroom_ceiling.blend` --
a 6.99 MB appendable library that three lines in `tools/build_film_scene.py`
bring in beside the existing SHOWROOM / PROPS / LIGHTS appends.  The round trip
was wrong UPSTREAM of the farm defect it would have hit.

This module is that answer for the fines.  **It opens no scene.**  It builds into
factory startup, so its peak memory is the fines alone -- about 2 GB against the
43.8 GB the round trip wanted -- and `ExecMemoryShort` cannot apply to it by
construction.  No 8 GB output, no fetch, no re-upload, no waiting for the render
worker to go idle.  The only thing that ever opens a film-sized blend is the
render itself.

WHAT IS **NOT** IN HERE, ON PURPOSE
===================================
The frosting.  `--fracture-faces` is a MATERIAL edit to `BREACH_Glass`, a
datablock the film already owns; it creates no geometry and there is nothing to
append.  It stays in `apply_breach.py` where it is.  They were always two
changes and this keeps them two.

THE ROUND TRIP IS THE POINT, AND IT IS NOT THE CEILING'S ROUND TRIP
===================================================================
`showroom_ceiling.blend` is 21 STATIC objects.  This is 11,246 ANIMATED ones
carrying ~2.84 M keyframes on slotted actions, and their transforms are the
breach sim's own timing -- a puff that appends half a frame late is a puff that
appears before the crack that freed it.

Appending is documented to bring actions with it.  Documented is not measured,
so `--verify` does the whole trip in one process: build, save, wipe to factory
settings, append the collection back out of the file just written, and then

  * count objects and F-curve keys against the source,
  * evaluate a sample of puffs' WORLD positions at sample frames and diff them
    against `sim/debris.load()`'s own table -- the same reconstruction
    `apply_breach` keys and the render will show,
  * check the visibility keys survived, because a puff that appends visible
    from frame 1 is 260,000 chips hanging in an intact wall through beat 1.

If any of that fails, this file says so and the round trip goes back on the
table.  A library that loses its animation silently is worse than an 8 GB blend.
"""

import argparse
import json
import os
import sys
import time

import bpy                                                        # noqa: E402
import numpy as np                                                # noqa: E402

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(R2, "sim"), os.path.join(R2, "anim")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import apply_breach as AB                                         # noqa: E402
import debris as DB                                               # noqa: E402

T0 = time.time()
COLL = "BREACH_Fines"


def log(m):
    print("[lib %7.1fs] %s" % (time.time() - T0, m))
    sys.stdout.flush()


def _in_bundle(path):
    """Resolve a data path against the BUNDLE ROOT, not the process CWD.

    `rq exec` runs the child with its CWD at the JOB directory and unpacks the
    bundle into `<job>/bundle/`, so `out/x` resolves and `sim/out/x` does not --
    the latter lives under `bundle/`.  Passing `--debris sim/out/breach_debris.npz`
    therefore raised FileNotFoundError on the farm while working perfectly
    locally, where CWD is the repo root.

    AND BLENDER EXITED 0 ON THAT EXCEPTION, exactly as this project's
    `land_breach.sh` warns.  What turned it into a failure instead of a silent
    success was `--output`: the broker declared the two files, did not find
    them, and refused the job with the child's traceback attached.  A job that
    had declared no outputs would have reported PASS.
    """
    if not path or os.path.isabs(path):
        return path
    if os.path.exists(path):
        return path
    cand = os.path.join(R2, path)
    return cand if os.path.exists(cand) else path


def parse():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--debris",
                   default=os.path.join(R2, "sim/out/breach_debris.npz"))
    p.add_argument("--out", required=True)
    p.add_argument("--report", default="")
    p.add_argument("--fines-material", default="BREACH_Fines")
    p.add_argument("--no-verify", action="store_true")
    p.add_argument("--verify-frames", default="866,880,900,930,1200,2978")
    p.add_argument("--verify-puffs", type=int, default=64)
    a = p.parse_args(argv)
    # INPUTS resolve against the bundle; OUTPUTS stay relative to the CWD,
    # because `out/` is the only directory the broker fetches from and
    # everything else is deleted when the child exits.
    a.debris = _in_bundle(a.debris)
    if not os.path.exists(a.debris):
        raise SystemExit("STAGE RESULT: fines_lib FAIL -- no debris table at "
                         "%r (cwd %s, bundle root %s)"
                         % (a.debris, os.getcwd(), R2))
    return a


def build_library(a):
    sc = bpy.context.scene
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    # The film's range, because CONSTANT extrapolation past the last key is what
    # keeps the wound's fallen glass on the floor for beats 4, 5 and 6, and an
    # action evaluated outside a scene range it never had is a different curve.
    sc.frame_start, sc.frame_end = 1, 2978
    sc.unit_settings.scale_length = 1.0

    C = bpy.data.collections.new(COLL)
    sc.collection.children.link(C)
    ns = type("NS", (), dict(debris=a.debris,
                             fines_material=a.fines_material))()
    st = AB.build_debris(ns, C)
    log("built: %s" % json.dumps({k: v for k, v in st.items()
                                  if k != "report"}))

    proof = AB.prove_curves(C)
    log("curve proof: %s" % json.dumps(proof))
    if proof["flags"]["other"] or proof["max_linear_eval_err"] > 1e-4:
        raise SystemExit("STAGE RESULT: fines_lib FAIL -- curves are not "
                         "LINEAR by evaluation: %s" % proof)

    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=a.out)
    sz = os.path.getsize(a.out)
    log("saved %s (%.1f MB)" % (a.out, sz / 1e6))
    return st, proof, sz


def sample_truth(a, frames, pids):
    """Where the TABLE says each sampled puff is, at each sampled frame.

    The same linear reconstruction `apply_breach` writes and the render
    evaluates -- not the raw keys, because a key is only the truth ON a key
    frame and most of these are not.
    """
    tab = DB.load(a.debris)
    out = {}
    for j in pids:
        kf, kl, _kq = tab["keys_of"](j)
        pos = {}
        for f in frames:
            if len(kf) == 1:
                pos[f] = kl[0].copy()
                continue
            i = int(np.searchsorted(kf, f))
            if i <= 0:
                pos[f] = kl[0].copy()
            elif i >= len(kf):
                pos[f] = kl[-1].copy()          # CONSTANT extrapolation
            else:
                t = (f - kf[i - 1]) / max(kf[i] - kf[i - 1], 1e-9)
                t = min(max(t, 0.0), 1.0)
                pos[f] = kl[i - 1] * (1 - t) + kl[i] * t
        out[j] = pos
    births = {j: int(tab["puff_meta"][j][0]) for j in pids}
    return out, births, tab


def verify(a, built):
    """Wipe to factory settings, append the collection back, and measure."""
    frames = [int(x) for x in a.verify_frames.split(",")]
    log("ROUND TRIP: wiping to factory settings")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if bpy.data.objects:
        raise SystemExit("STAGE RESULT: fines_lib FAIL -- factory wipe left "
                         "%d objects; the verify would be measuring the build"
                         % len(bpy.data.objects))

    # THE THREE LINES THE FILM BUILD WILL USE, run here against the file just
    # written.  If this is not what tools/build_film_scene.py does, the verify
    # is measuring something else.
    with bpy.data.libraries.load(a.out, link=False) as (src, dst):
        if COLL not in src.collections:
            raise SystemExit("STAGE RESULT: fines_lib FAIL -- no %r collection "
                             "in the library" % COLL)
        dst.collections = [COLL]
    C = bpy.data.collections[COLL]
    bpy.context.scene.collection.children.link(C)
    sc = bpy.context.scene
    sc.frame_start, sc.frame_end = 1, 2978

    n_obj = len(C.all_objects)
    n_key = 0
    n_anim = 0
    n_hide = 0
    for ob in C.all_objects:
        ad = ob.animation_data
        if not (ad and ad.action):
            continue
        n_anim += 1
        for lay in ad.action.layers:
            for st in lay.strips:
                cb = st.channelbag(ad.action_slot)
                if not cb:
                    continue
                for fc in cb.fcurves:
                    n_key += len(fc.keyframe_points)
                    if fc.data_path.startswith("hide"):
                        n_hide += 1

    res = dict(objects=n_obj, objects_expected=built["puffs"],
               animated=n_anim, keys=n_key, keys_expected=built["keys"],
               hide_curves=n_hide, tris_expected=built["tris"])

    # ---- the load-bearing check: WORLD POSITION at sample frames ------------ #
    idx = {ob.name: ob for ob in C.all_objects}
    pids = sorted(range(built["puffs"]))[::max(1, built["puffs"]
                                               // a.verify_puffs)][:a.verify_puffs]
    truth, births, _tab = sample_truth(a, frames, pids)
    dep = bpy.context.evaluated_depsgraph_get()
    worst = 0.0
    worst_where = None
    vis_bad = []
    for f in frames:
        sc.frame_set(f)
        dep.update()
        for j in pids:
            ob = idx.get("DB_p%05d" % j)
            if ob is None:
                raise SystemExit("STAGE RESULT: fines_lib FAIL -- DB_p%05d did "
                                 "not survive the append" % j)
            got = np.array(ob.evaluated_get(dep).matrix_world.translation)
            d = float(np.linalg.norm(got - truth[j][f]))
            if d > worst:
                worst, worst_where = d, ("DB_p%05d" % j, f)
            # visibility: hidden strictly before birth, shown at and after
            want_hidden = f < births[j]
            if bool(ob.hide_render) != want_hidden:
                vis_bad.append(("DB_p%05d" % j, f, bool(ob.hide_render),
                                want_hidden))
    res["worst_pos_err_m"] = worst
    res["worst_pos_at"] = worst_where
    res["frames_checked"] = frames
    res["puffs_checked"] = len(pids)
    res["visibility_mismatches"] = vis_bad[:12]
    res["n_visibility_mismatches"] = len(vis_bad)

    res["PASS"] = bool(
        n_obj == built["puffs"]
        and n_anim == built["puffs"]
        and n_key == built["keys"]
        and worst < 1e-5
        and not vis_bad)
    return res


def main():
    a = parse()
    built, proof, sz = build_library(a)
    rep = dict(built={k: v for k, v in built.items() if k != "report"},
               curve_proof=proof, bytes=sz, out=a.out,
               debris=a.debris)
    if not a.no_verify:
        v = verify(a, built)
        rep["round_trip"] = v
        log("round trip: %s" % json.dumps(
            {k: val for k, val in v.items() if k != "visibility_mismatches"},
            default=float))
        if not v["PASS"]:
            if a.report:
                with open(a.report, "w") as fh:
                    json.dump(rep, fh, indent=1, default=float)
            raise SystemExit(
                "STAGE RESULT: fines_lib FAIL -- the append did not round "
                "trip: objects %d/%d, animated %d, keys %d/%d, worst position "
                "error %.3e m at %s, %d visibility mismatches"
                % (v["objects"], v["objects_expected"], v["animated"],
                   v["keys"], v["keys_expected"], v["worst_pos_err_m"],
                   v["worst_pos_at"], v["n_visibility_mismatches"]))
    if a.report:
        with open(a.report, "w") as fh:
            json.dump(rep, fh, indent=1, default=float)
        log("wrote %s" % a.report)
    print("STAGE RESULT: fines_lib PASS")


if __name__ == "__main__":
    main()
