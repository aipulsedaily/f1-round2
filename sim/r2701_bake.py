"""R2-701 — bake one breach cell on the farm and bring back the FILM table.

    ~/vast-render/rq exec --root ~/f1-round2 --closure \
        --include 'sim/out/fracture_wall.npz' \
        --include 'sim/out/car_identity.json' \
        --include 'world/car_anim_measured.json' \
        --include 'docs/beat_sheet.json' \
        --include 'world/items/mullion_intact_interface.json' \
        --entry sim/r2701_bake.py --arg=--rear-wing --arg=aerofoil \
        --arg=--frames --arg=520 \
        --output breach_film.npz --output breach_film.json \
        --output breach_sim.json --output breach_bake.npz \
        --timeout 3400 --slots 1

WHY THIS EXISTS AND `sim/remote_bake.py` WAS NOT ENOUGH
======================================================
Two things, both learned by having them happen.

1.  **The broker caps an exec job at 3,600 s.**  `timeout_s must be 1..3600`,
    because the in-container watchdog retires the instance at 12 h regardless.
    The 1,657-frame production bake takes 2 h 25 m and CANNOT be submitted as one
    job.  A rigid-body bake cannot be split across jobs either — frame N+1 needs
    frame N's contact state — so the window is truncated instead, and the entry
    prints the timing that lets the next cell be sized.

2.  **`remote_bake.py` runs `verify_breach` LAST, and on a truncated window that
    verifier asks about frames the table does not contain** (`persist_from=1150`,
    overlap frames to 1120).  A raise there fails the job, and a failed job
    fetches NO outputs — so a 40-minute bake that finished perfectly would come
    back as nothing.  Everything after the export is wrapped: the table is
    written and flushed before anything that can throw is allowed to run.

WHAT COMES BACK.  The decimated FILM table (~20 MB), its report, the sim report,
and the raw world-time bake.  Judge the job on the printed `>> STAGE RESULT:`
lines: Blender 5.2 exits 0 on an uncaught script exception.

WHERE THE OUTPUTS GO, AND THE HOUR IT COST (R2-701, 2026-08-04)
===============================================================
Job `9275cfd7f75d` baked all 60 frames, ran every stage, printed
`>> STAGE RESULT: R2701_BAKE PASS`, and was still reported by the broker as
"declared output(s) not produced — the child exited 0 without writing them".
Both statements were true.  The exec server stages the bundle at
`<job>/bundle/`, runs the child with cwd `<job>`, and resolves every declared
`--output` under `<job>/out/`.  `__file__` is inside `bundle/`, so deriving the
output directory from it — as this entry did — writes the table to
`<job>/bundle/out/`, which is deleted with the rest of the bundle at release and
is never looked at by the fetch.  **An entry CANNOT locate its outputs from
`__file__` on this farm.**  It must write to `out/` relative to the cwd, which
is what every other entry on this farm does via a relative `--out out/x.json`.

WHY THE LOG LOOKED LIKE A CRASH.  The tail the broker surfaces ended at
`bake: frame 60 :: 60 | Blender quit` with none of this script's markers, which
reads exactly like a death inside the bake.  It is an artefact of buffering:
this script's `print` goes through Python's `sys.stdout`, which is flushed on
every line, while Blender's own C-level `printf` (the version banner and the
`bake: frame N` progress line) sits in libc's block buffer until exit.  Both
land on the same fd, so the whole C stream is appended AFTER the whole Python
stream and the last 12 lines of the file are ALWAYS the C tail, whatever the
script did.  `_unbuffer_c_stdout()` below turns libc's buffer off so the two
streams interleave honestly.  The full log lives on the instance at
`/workspace/exec/<job_id>/job.log` and outlives a failed job — read it there
before theorising.
"""

import json
import os
import sys
import time

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The exec server's layout: bundle at <job>/bundle, outputs collected from
# <job>/out, cwd <job>.  Anywhere else, fall back to the tree's own out/.
_PARENT = os.path.dirname(R2)
if os.path.basename(R2) == "bundle" and os.path.isdir(os.path.join(_PARENT, "out")):
    OUT = os.path.join(_PARENT, "out")
else:
    OUT = os.path.join(R2, "out")

for _p in (os.path.join(R2, "sim"), os.path.join(R2, "anim"),
           os.path.join(R2, "world")):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def _unbuffer_c_stdout():
    """Stop libc holding Blender's own prints back until exit.

    Best effort and never fatal: a diagnostic aid must not be able to fail a
    40-minute bake.
    """
    try:
        import ctypes
        libc = ctypes.CDLL(None)
        stdout = ctypes.c_void_p.in_dll(libc, "stdout")
        libc.setvbuf(stdout, None, 2, 0)          # _IONBF
    except Exception:                                          # noqa: BLE001
        pass


_unbuffer_c_stdout()

T0 = time.time()
_MARKS = []


def log(m):
    print("[r2701 %7.1fs] %s" % (time.time() - T0, m))
    sys.stdout.flush()


def mark(what):
    _MARKS.append((what, time.time() - T0))
    log("--- %s at %.1fs" % (what, time.time() - T0))


def main():
    os.makedirs(OUT, exist_ok=True)
    log("cwd %s" % os.getcwd())
    log("OUT %s  (bundle root %s)" % (OUT, R2))
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

    import numpy as np
    import build_breach_sim as BS
    import breachlib as BL

    sys.argv = ["blender", "--"] + argv + [
        "--out", os.path.join(OUT, "breach_sim.blend"),
        "--report", os.path.join(OUT, "breach_sim.json"),
        "--export", os.path.join(OUT, "breach_bake.npz"),
        "--bake"]
    a = BS.parse_args()
    log("args: %s" % vars(a))

    ok, why = BL.Car().identity_ok()
    log("car identity: %s -- %s" % (ok, why))
    if not ok:
        print(">> STAGE RESULT: R2701_BAKE FAIL (car identity: %s)" % why)
        raise SystemExit(1)

    info, objs = BS.build(a)
    mark("build")
    car = BL.Car()
    wts = BL.sim_frame_world_t(info["world_t0"], info["sim_frames"])
    info["linearity"] = BS.prove_linear(objs["action"], info["sim_frames"],
                                        car, wts)
    if not info["linearity"]["all_flags_linear"] or \
            info["linearity"]["max_eval_err_m"] > 1e-5 or \
            not info["linearity"]["control_fires"]:
        print(">> STAGE RESULT: R2701_BAKE FAIL (car proxy curve not linear)")
        raise SystemExit(1)

    BS.bake(info["sim_frames"])
    mark("bake")
    loc, quat = BS.export(objs["shards"] + objs["frame"], info, a.export)
    mark("export")
    names = [o.name for o in objs["shards"] + objs["frame"]]

    # ---- the FILM table, written and flushed BEFORE anything that can throw --
    import resample as RS
    z = np.load(a.export, allow_pickle=False)
    bake = {k: z[k] for k in z.files}
    clock = BL.Clock()
    frames, L, Q = RS.to_film(bake, clock)
    log("film frames %d..%d, %d bodies" % (frames[0], frames[-1], L.shape[1]))
    keys = RS.decimate(frames, L, Q)
    rep = RS.decimation_report(frames, L, Q, keys, sample=400)
    rel, ref = RS.release_for_film(frames, L, car)
    rep["release_reference_frame"] = ref
    kf = np.concatenate([frames[np.array(k)] for k in keys]).astype(np.int32)
    kl = np.concatenate([L[np.array(k), j] for j, k in enumerate(keys)])
    kq = np.concatenate([Q[np.array(k), j] for j, k in enumerate(keys)])
    film = os.path.join(OUT, "breach_film.npz")
    np.savez_compressed(
        film,
        key_count=np.array([len(k) for k in keys], np.int32),
        key_frame=kf, key_loc=kl.astype(np.float32),
        key_quat=kq.astype(np.float32),
        release=rel.astype(np.int32),
        span=np.array([frames[0], frames[-1]], np.int32),
        names=bake["names"])
    rep["bytes"] = os.path.getsize(film)
    rep["release_min"] = int(rel[rel > 0].min()) if (rel > 0).any() else -1
    rep["release_max"] = int(rel[rel > 0].max()) if (rel > 0).any() else -1
    rep["never_released"] = int((rel < 0).sum())
    rep["film_span"] = [int(frames[0]), int(frames[-1])]
    with open(os.path.join(OUT, "breach_film.json"), "w") as fh:
        json.dump(rep, fh, indent=1, default=float)
    mark("resample")
    log("decimation: %s" % json.dumps(rep, default=float))
    print(">> STAGE RESULT: R2701_TABLE PASS (%s, %.1f MB, film f%d-f%d)"
          % (os.path.basename(film), rep["bytes"] / 1e6,
             frames[0], frames[-1]))

    # ---- everything below here is a BONUS and may not throw ---------------- #
    try:
        info["motion"] = BS.motion_report(loc, quat, names, info)
        info["aperture"] = BS.aperture_report(loc[:, :len(objs["shards"])],
                                              info["shard_meta"], info)
        log("motion: %s" % json.dumps(info["motion"], default=float))
        log("aperture: %s" % json.dumps(info["aperture"], default=float))
    except Exception as e:                                     # noqa: BLE001
        info["report_error"] = repr(e)
        log("motion/aperture FAILED (not fatal): %r" % e)
    try:
        tail = loc[-int(0.5 * BL.SIM_FPS):]
        info["settle"] = dict(
            last_half_second_max_move_m=float(
                np.linalg.norm(tail - tail[0][None], axis=2).max()),
            bodies_still_moving=int(
                (np.linalg.norm(tail[-1] - tail[0], axis=1) > 0.002).sum()),
            NOTE=("meaningless on a truncated window: the wound is still in "
                  "motion by construction" if a.frames else "full window"))
        log("settle: %s" % json.dumps(info["settle"], default=float))
    except Exception as e:                                     # noqa: BLE001
        info["settle_error"] = repr(e)
    info["timing_s"] = dict(_MARKS)
    info["truncated_to_frames"] = int(a.frames or 0)
    with open(os.path.join(OUT, "breach_sim.json"), "w") as fh:
        json.dump(info, fh, indent=1, default=float)
    log("timing: %s" % json.dumps(info["timing_s"]))
    print(">> STAGE RESULT: R2701_BAKE PASS (%d sim frames, %.0fs total, "
          "%.2f s/frame in the solver)"
          % (info["sim_frames"], time.time() - T0,
             (dict(_MARKS)["bake"] - dict(_MARKS)["build"])
             / max(info["sim_frames"], 1)))


if __name__ == "__main__":
    # Blender 5.2 exits 0 on an uncaught script exception and puts the traceback
    # on stderr.  Reprinting it on stdout, flushed, next to a FAIL token is what
    # makes the difference between a diagnosis and a guess.
    try:
        main()
    except SystemExit:
        raise
    except BaseException:                                      # noqa: BLE001
        import traceback
        print(">> STAGE RESULT: R2701_BAKE FAIL (uncaught)")
        print(traceback.format_exc())
        sys.stdout.flush()
        raise
