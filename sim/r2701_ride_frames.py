"""R2-701 — the peak of the deck ride, rendered from TWO breach tables in ONE job.

    ~/vast-render/rq exec --root ~/f1-round2 --closure \
        --include 'sim/out/fracture_wall.npz' \
        --include 'sim/out/breach_film_R2387.npz' \
        --include 'sim/out/breach_film_R2701A.npz' \
        --include 'world/items/mullion_intact_interface.json' \
        --include 'docs/beat_sheet.json' \
        --scene render/film14.blend \
        --entry sim/r2701_ride_frames.py \
        --arg=--tables --arg=A=sim/out/breach_film_R2701A.npz \
        --arg=B=sim/out/breach_film_R2387.npz \
        --arg=--frames --arg=967,972,977 \
        --output A_f0967.png ... --timeout 3400 --slots 2

WHY BOTH TABLES ARE RENDERED HERE RATHER THAN COMPARED AGAINST WHAT IS ON DISK
=============================================================================
`render/r2387/new_ride_f0972.png` already exists and was rendered through
`rq render` from `render/film14_breach_R2387.blend`.  Comparing a frame this
script produces against that one would put the RENDER PATH in the difference
alongside the table, and R2-387's own render script says it in as many words:
"anything else is not a difference, it is a settings change".

So the base scene is opened twice, from the same staged `scene.blend`, and each
table is applied to a fresh copy of it.  The applier is DESTRUCTIVE — it deletes
round 1's east frame and refuses if that frame is already missing — so a second
apply onto an applied scene is not a supported operation and is not attempted.

The render settings are copied from `~/vast-render/worker/server.py` field for
field (CYCLES, GPU, adaptive sampling at 0.01, OpenImageDenoise on the GPU, DOF
forced on, persistent data on) so that these frames sit on the same ladder as
every other beat-3 frame this project has rendered.

Judge on the printed `>> STAGE RESULT:` lines.  Blender 5.2 exits 0 on an
uncaught script exception, and a frame that comes back black is a farm failure
that a `$?` of zero will happily hide: every frame written here is checked for
being a picture before the job claims to have made one.
"""

import json
import os
import sys
import time

import bpy

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# WHERE THE OUTPUTS GO, AND THE JOB THIS COST.  The exec server stages the
# bundle at `<job>/bundle/`, runs the child with cwd `<job>`, and collects every
# declared `--output` from `<job>/out/`.  `__file__` is inside `bundle/`, so
# deriving the output directory from it writes into `<job>/bundle/out/` — which
# is deleted with the bundle and never fetched.  The job then reports
# "declared output(s) not produced: the child exited 0 without writing them"
# while the child's own log says it wrote them, and both are true.
# AN ENTRY CANNOT LOCATE ITS OUTPUTS FROM `__file__` ON THIS FARM.
_PARENT = os.path.dirname(R2)
if os.path.basename(R2) == "bundle" and os.path.isdir(os.path.join(_PARENT,
                                                                  "out")):
    OUT = os.path.join(_PARENT, "out")
    JOB = _PARENT
else:
    OUT = os.path.join(R2, "out")
    JOB = R2

for _p in (os.path.join(R2, "sim"), os.path.join(R2, "anim"),
           os.path.join(R2, "world")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

T0 = time.time()
# `--scene` is linked into the JOB directory as `scene.blend`, not into the
# bundle: it is staged from the instance's content-addressed scene cache.
SCENE = os.path.join(JOB, "scene.blend")


def log(m):
    print("[ride %7.1fs] %s" % (time.time() - T0, m))
    sys.stdout.flush()


def use_gpu():
    prefs = bpy.context.preferences.addons["cycles"].preferences
    chosen = None
    for kind in ("OPTIX", "CUDA"):
        prefs.compute_device_type = kind
        prefs.refresh_devices()
        if any(d.type == kind for d in prefs.devices):
            chosen = kind
            break
    if chosen is None:
        raise SystemExit("REFUSING: no OptiX or CUDA device — this would "
                         "render on the CPU and never finish")
    for d in prefs.devices:
        d.use = (d.type == chosen)
    bpy.context.scene.cycles.device = "GPU"
    log("device=%s [%s]" % (chosen, ", ".join(d.name for d in prefs.devices
                                              if d.use)))


def configure(scene, cam_name, res, samples):
    cam = bpy.data.objects[cam_name]
    scene.camera = cam
    scene.render.engine = "CYCLES"
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.resolution_percentage = 100
    scene.render.use_border = False
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.cycles.samples = samples
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.01
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = "OPENIMAGEDENOISE"
    if hasattr(scene.cycles, "denoising_use_gpu"):
        scene.cycles.denoising_use_gpu = True
    scene.render.use_persistent_data = True
    if cam.data.type != "ORTHO":
        cam.data.dof.use_dof = True          # --dof on, as every ride frame was
    return cam


def is_a_picture(path):
    """A structurally perfect, correctly sized BLACK png has been delivered by
    this farm and counted as done.  Nothing here reports a render it has not
    looked at."""
    img = bpy.data.images.load(path)
    try:
        px = list(img.pixels)
        n = len(px) // 4
        lum = [0.2126 * px[4 * i] + 0.7152 * px[4 * i + 1]
               + 0.0722 * px[4 * i + 2] for i in range(0, n, 97)]
        m = sum(lum) / len(lum)
        sd = (sum((x - m) ** 2 for x in lum) / len(lum)) ** 0.5
        return dict(lum_mean=m, lum_sd=sd, ok=bool(sd > 0.01 and m > 0.005))
    finally:
        bpy.data.images.remove(img)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--tables", nargs="+", required=True,
                    help="TAG=path/to/breach_film.npz, repeatable")
    ap.add_argument("--frames", default="967,972,977")
    ap.add_argument("--cam", default="ONER")
    ap.add_argument("--res", default="1920,1080")
    ap.add_argument("--samples", type=int, default=256)
    a = ap.parse_args(argv)

    frames = [int(x) for x in a.frames.split(",")]
    res = tuple(int(x) for x in a.res.split(","))
    os.makedirs(OUT, exist_ok=True)
    if not os.path.exists(SCENE):
        raise SystemExit("REFUSING: no scene.blend in the job directory — "
                         "this entry needs `rq exec --scene <film>.blend`")

    import apply_breach as AB
    verdicts = {}
    for spec in a.tables:
        tag, _, table = spec.partition("=")
        table = os.path.join(R2, table) if not os.path.isabs(table) else table
        if not os.path.exists(table):
            raise SystemExit("REFUSING: no table at %s" % table)
        log("=== %s : %s" % (tag, table))
        bpy.ops.wm.open_mainfile(filepath=SCENE)
        log("opened scene.blend (%.1f MB on disk)"
            % (os.path.getsize(SCENE) / 1e6))

        sys.argv = ["blender", "--", "--film", table,
                    "--out", os.path.join(JOB, "applied_%s.blend" % tag),
                    "--report", os.path.join(OUT, "apply_%s.json" % tag),
                    "--force"]
        AB.main()
        log("applied %s" % tag)

        use_gpu()
        sc = bpy.context.scene
        configure(sc, a.cam, res, a.samples)
        for f in frames:
            sc.frame_set(f)
            configure(sc, a.cam, res, a.samples)      # frame_set re-evaluates
            out = os.path.join(OUT, "%s_f%04d.png" % (tag, f))
            sc.render.filepath = out
            t = time.time()
            bpy.ops.render.render(write_still=True)
            v = is_a_picture(out)
            verdicts["%s_f%04d" % (tag, f)] = v
            log("rendered %s in %.0fs  lum %.3f sd %.3f  %s"
                % (os.path.basename(out), time.time() - t, v["lum_mean"],
                   v["lum_sd"], "OK" if v["ok"] else "BLANK"))
        try:
            os.remove(os.path.join(JOB, "applied_%s.blend" % tag))
        except OSError:
            pass

    with open(os.path.join(OUT, "ride_frames.json"), "w") as fh:
        json.dump(verdicts, fh, indent=1)
    bad = [k for k, v in verdicts.items() if not v["ok"]]
    print(">> STAGE RESULT: R2701_RIDE_FRAMES %s (%d frames, blank: %s)"
          % ("PASS" if not bad else "FAIL", len(verdicts), bad or "none"))


if __name__ == "__main__":
    main()
