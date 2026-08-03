"""REMOTE BAKE — build, bake, export, resample and verify, in one exec job.

    ~/vast-render/rq exec --root /home/zany/f1-round2 \
        --include 'sim/*.py' --include 'sim/out/fracture_wall.npz' \
        --include 'sim/out/car_identity.json' --include 'anim/filmtime.py' \
        --include 'docs/beat_sheet.json' \
        --include 'world/car_anim_measured.json' \
        --include 'world/items/mullion_intact_interface.json' \
        --entry sim/remote_bake.py \
        --output breach_film.npz --output breach_sim.json \
        --output breach_film.json --output verify.json \
        --timeout 7200

WHY THIS RUNS OFF THIS BOX
==========================
3,090 rigid bodies and 9,612 constraints over 1,561 world-time frames.  This
machine has 11 GB of RAM, of which about 2 GB is free while other agents hold
7 GB, and the first attempt at the bonded bake died silently mid-bake with no
output — the failure mode the project has already been bitten by, since Blender
5.2 exits 0 on an uncaught exception and a killed process leaves nothing behind
at all.  The rented box has the memory.

WHAT COMES BACK, AND WHAT DOES NOT
----------------------------------
The raw world-time bake is ~3,000 bodies x 1,561 frames x 7 floats.  It stays on
the remote box; what is FETCHED is the resampled, decimated FILM table, its
measurement reports, and the verifier's verdict.  `push_scene` is not resumable
(#80) and the same caution applies to anything crossing that link in either
direction: move the small artefact, not the big one.

The raw bake is also written to out/ under `--output breach_bake.npz` if it is
asked for, so a re-decimation at a different tolerance does not need a re-bake.
"""

import json
import os
import sys
import time

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(R2, "out")
for _p in (os.path.join(R2, "sim"), os.path.join(R2, "anim"),
           os.path.join(R2, "world")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

T0 = time.time()


def log(m):
    print("[remote %7.1fs] %s" % (time.time() - T0, m))
    sys.stdout.flush()


def main():
    os.makedirs(OUT, exist_ok=True)
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

    import build_breach_sim as BS
    import breachlib as BL
    import numpy as np

    # the args the sim builder wants, with our own out/ paths spliced in
    sys.argv = ["blender", "--"] + argv + [
        "--out", os.path.join(OUT, "breach_sim.blend"),
        "--report", os.path.join(OUT, "breach_sim.json"),
        "--export", os.path.join(OUT, "breach_bake.npz"),
        "--bake"]
    a = BS.parse_args()
    log("args: %s" % vars(a))

    info, objs = BS.build(a)
    car = BL.Car()
    wts = BL.sim_frame_world_t(info["world_t0"], info["sim_frames"])
    info["linearity"] = BS.prove_linear(objs["action"], info["sim_frames"],
                                        car, wts)
    if not info["linearity"]["all_flags_linear"] or \
            info["linearity"]["max_eval_err_m"] > 1e-5 or \
            not info["linearity"]["control_fires"]:
        raise SystemExit("REFUSING: car proxy curve is not LINEAR: %s"
                         % info["linearity"])
    BS.bake(info["sim_frames"])
    loc, quat = BS.export(objs["shards"] + objs["frame"], info, a.export)
    names = [o.name for o in objs["shards"] + objs["frame"]]
    info["motion"] = BS.motion_report(loc, quat, names, info)
    info["aperture"] = BS.aperture_report(loc[:, :len(objs["shards"])],
                                          info["shard_meta"], info)
    log("motion: %s" % json.dumps(info["motion"]))
    log("aperture: %s" % json.dumps(info["aperture"]))

    # ---- the settle test: is the wound STILL at the end of the window? ----- #
    # If it is not, the window is too short and the wound would still be moving
    # when beat 4 turns away from it.  Reported, not assumed.
    tail = loc[-int(0.5 * BL.SIM_FPS):]
    info["settle"] = dict(
        last_half_second_max_move_m=float(
            np.linalg.norm(tail - tail[0][None], axis=2).max()),
        bodies_still_moving=int(
            (np.linalg.norm(tail[-1] - tail[0], axis=1) > 0.002).sum()))
    log("settle: %s" % json.dumps(info["settle"]))

    with open(os.path.join(OUT, "breach_sim.json"), "w") as fh:
        json.dump(info, fh, indent=1, default=float)

    # ---- resample to film frames and decimate ----------------------------- #
    import resample as RS
    z = np.load(a.export, allow_pickle=False)
    bake = {k: z[k] for k in z.files}
    clock = BL.Clock()
    frames, L, Q = RS.to_film(bake, clock)
    log("film frames %d..%d, %d bodies" % (frames[0], frames[-1], L.shape[1]))
    keys = RS.decimate(frames, L, Q,
                       progress=lambda j, n: log("  decimate %d/%d" % (j, n)))
    rep = RS.decimation_report(frames, L, Q, keys, sample=400)
    # RELEASE is measured from the state at IMPACT, not at frame 1: the bonded
    # wall settles a fraction of a millimetre under its own weight before the
    # car arrives, and a 0.2 mm trigger would fire the intact-pane swap on every
    # shard at frame 855 — the wall would shatter five frames before the car
    # touched it and nothing in the transform table would look wrong.
    i0 = int(np.argmin(np.abs(frames - int(round(car.impact_frame())))))
    rel = RS.release_frames(frames[i0:], L[i0:], eps=0.002)
    rep["release_reference_frame"] = int(frames[i0])
    kf = np.concatenate([frames[np.array(k)] for k in keys]).astype(np.int32)
    kl = np.concatenate([L[np.array(k), j] for j, k in enumerate(keys)])
    kq = np.concatenate([Q[np.array(k), j] for j, k in enumerate(keys)])
    np.savez_compressed(
        os.path.join(OUT, "breach_film.npz"),
        key_count=np.array([len(k) for k in keys], np.int32),
        key_frame=kf, key_loc=kl.astype(np.float32),
        key_quat=kq.astype(np.float32),
        release=rel.astype(np.int32),
        span=np.array([frames[0], frames[-1]], np.int32),
        names=bake["names"])
    rep["bytes"] = os.path.getsize(os.path.join(OUT, "breach_film.npz"))
    rep["release_min"] = int(rel[rel > 0].min()) if (rel > 0).any() else -1
    rep["release_max"] = int(rel[rel > 0].max()) if (rel > 0).any() else -1
    rep["never_released"] = int((rel < 0).sum())
    with open(os.path.join(OUT, "breach_film.json"), "w") as fh:
        json.dump(rep, fh, indent=1, default=float)
    log("decimation: %s" % json.dumps(rep, default=float))

    # ---- verify ----------------------------------------------------------- #
    import verify_breach as VB

    class A(object):
        film = os.path.join(OUT, "breach_film.npz")
        shards = os.path.join(R2, "sim", "out", "fracture_wall.npz")
        overlap_frames = [861, 866, 880, 920, 1000, 1056, 1120]
        overlap_sample = 300
        persist_from = 1150
    ver = VB.run(A)
    try:
        f2 = np.load(A.film, allow_pickle=False)
        Lr, Qr = RS.read_film(A.film)["expand"](
            np.arange(int(f2["span"][0]), int(f2["span"][1]) + 1))
        VB.plan_png(Lr, os.path.join(OUT, "breach_plan.png"))
        ver["plan_png"] = "breach_plan.png"
    except Exception as e:                                     # noqa: BLE001
        ver["plan_png_error"] = str(e)
    with open(os.path.join(OUT, "verify.json"), "w") as fh:
        json.dump(ver, fh, indent=1, default=float)
    log("verify: %s" % json.dumps({k: v for k, v in ver.items()
                                   if k != "overlap"}, default=float))
    log("DONE")


if __name__ == "__main__":
    main()
