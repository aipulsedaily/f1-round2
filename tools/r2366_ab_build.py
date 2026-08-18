#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
r2366_ab_build.py — the A/B scene for the paving relief ladder.

Builds `build_architecture` under `world_contract`'s own sky and sun and puts
the film's ONER camera at a chosen frame with that frame's own pose and lens,
read out of `world/camera_rig_path.json` rather than invented.

    --before   set `R2366_LEGACY_PAVING`, which makes `build_architecture`
               rebuild the three paving materials exactly as they shipped — one
               bump on the fine aggregate, uncompressed per-cell ramp — FROM THE
               SAME WORKING COPY.

               IT USED TO IMPORT `git show HEAD:world/build_architecture.py`
               INSTEAD, AND THAT WAS WRONG. The geometry fingerprint came back
               with `ARCH_PitWall` moved by 7,268 vertices, which is not a thing
               a material change can do — and it was not this change. Another
               live agent had uncommitted R2-331/R2-334 work in the same file,
               so "HEAD" and "the working copy minus my change" were different
               artefacts and the A/B was carrying someone else's edit as a
               confound. With four agents live, the committed tree is not a safe
               baseline for a working-copy change. The control now differs from
               the subject in this change and in nothing else, and
               `tools/r2366_geometry_unchanged.py` proves it by fingerprinting
               every world-space vertex rather than by comparing counts.
    --frame N  which frame. 2978 is the closing wide (611 m, 339 mm/px along
               the view). 945 is the beat-3 breach (5.9 m, 5.3 mm/px) — the
               finest view of the same paving anywhere in the take, chosen by
               `tools/r2366_surface_visibility.py` rather than by eye.
    --out P    where to save the .blend.

WHY ARCHITECTURE ONLY, AND WHAT THAT COSTS. The change is confined to three
material factories in `build_architecture`; terrain, barriers, dressing and the
round-1 showroom are byte-identical between the arms, so leaving them out
changes what is BEHIND the paving but not the paving itself, and it makes the
comparison exact and the build 117 s instead of 1,400 s. The delivered frame is
still the arbiter: the closing wide is re-rendered from the film scene once the
world is rebuilt.

Blender 5.2 exits 0 on an uncaught script exception; judge on `STAGE RESULT`.
"""
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

import bpy                                                   # noqa: E402
from mathutils import Quaternion, Vector                     # noqa: E402


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    before = "--before" in argv
    frame = int(argv[argv.index("--frame") + 1]) if "--frame" in argv else 2978
    out = argv[argv.index("--out") + 1] if "--out" in argv else \
        os.path.join(ROOT, "work", "r2366",
                     "ab_%s_f%d.blend" % ("before" if before else "after", frame))

    # ONE MODULE, ONE FLAG. Both arms import the same working copy, so every
    # other uncommitted change in the file is common to them and cancels.
    if before:
        os.environ["R2366_LEGACY_PAVING"] = "1"
    else:
        os.environ.pop("R2366_LEGACY_PAVING", None)
    sys.path.insert(0, os.path.join(ROOT, "world"))

    t0 = time.time()
    import build_architecture as BA
    src = os.path.abspath(BA.__file__)
    print("[AB] arm=%s  build_architecture from %s  legacy=%s"
          % ("BEFORE" if before else "AFTER", src, BA.PAVING_RELIEF_LEGACY))
    # AN ARM THAT DID NOT TAKE IS NOT AN ARM. The flag is read at import time,
    # so a stale `.pyc` or an import that happened earlier in the process would
    # silently give two identical arms and a flawless, entirely convincing
    # 0.00 % result — which this project has already believed once.
    if bool(BA.PAVING_RELIEF_LEGACY) != before:
        print("STAGE RESULT: r2366_ab_build FAIL (arm=%s but "
              "PAVING_RELIEF_LEGACY=%s — the flag did not take)"
              % ("BEFORE" if before else "AFTER", BA.PAVING_RELIEF_LEGACY))
        sys.exit(1)

    BA.build(verify=False)
    print("[AB] architecture %.1f s" % (time.time() - t0))

    sc = bpy.context.scene
    import build_dressing as BD
    BD._test_env(sc)                       # world_contract's sky + sun, verbatim

    # EXPOSURE FROM `film_exposure`, NOT FROM THE CONTRACT. R2-256's harness used
    # `C.REFERENCE_EXPOSURE_EXTERIOR`; that value is DERIVED and REFUTED — it
    # over-exposes by 0.586 stops against the film's own measured -3.628.
    import film_exposure as FE
    sc.view_settings.view_transform = 'AgX'
    FE.apply(sc)
    print("[AB] exposure %+.4f stops (film_exposure.FILM_EXPOSURE)"
          % sc.view_settings.exposure)

    path = json.load(open(os.path.join(ROOT, "world",
                                       "camera_rig_path.json")))["path"]
    e = path[frame - 1]
    assert e["f"] == frame, "camera path is not 1-indexed by frame"
    cd = bpy.data.cameras.new("ONER")
    cd.sensor_width, cd.sensor_fit = 36.0, 'AUTO'
    cd.clip_start, cd.clip_end = 0.05, 200000.0       # R2-061
    cd.lens = float(e["lens"])
    cam = bpy.data.objects.new("ONER", cd)
    sc.collection.objects.link(cam)
    cam.rotation_mode = 'QUATERNION'
    cam.location = Vector(e["p"])
    cam.rotation_quaternion = Quaternion(e["q"])
    sc.camera = cam
    sc.frame_start = sc.frame_end = sc.frame_current = frame
    print("[AB] camera f%d p=%s lens=%.4f"
          % (frame, [round(x, 2) for x in e["p"]], e["lens"]))

    sc.render.engine = 'CYCLES'
    sc.render.resolution_x, sc.render.resolution_y = 3840, 2160
    sc.render.resolution_percentage = 100
    # NO MOTION BLUR. The camera is not keyed here, so a shutter would smear
    # against a static rig and differ between arms for no reason. The defect is
    # a static surface property; the delivered frame carries its own blur.
    sc.render.use_motion_blur = False
    sc.render.film_transparent = False
    sc.cycles.use_denoising = True
    sc.cycles.samples = 400
    sc.cycles.adaptive_threshold = 0.01
    sc.render.image_settings.file_format = 'PNG'

    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out)
    print("STAGE RESULT: r2366_ab_build PASS (%s, arm=%s, frame=%d, %d objects)"
          % (os.path.basename(out), "before" if before else "after", frame,
             len(bpy.data.objects)))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
        print("STAGE RESULT: r2366_ab_build FAIL (uncaught exception)")
        sys.exit(1)
