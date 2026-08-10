"""Run `car_staleness.check_appended_car_keys()` ON A BUILT FILM BLEND.

    /opt/blender-5.2.0-linux-x64/blender -b render/film25.blend \
        --factory-startup -noaudio -P .../film_car_keys.py

WHY THIS FILE EXISTS.  R2-3661.

`check_appended_car_keys()` has, until now, only ever been run against CAR
blends -- `world/R2_3361_car_anim_driver_CS.blend`,
`world/R22041_car_anim_driver_CS.blend`, `world/car_anim.blend`.  It has NEVER
been run against a built film.  The wiring into `tools/build_film_scene.py`
was written up at R2-3301 and never made, because the file was leased.

That gap matters here specifically.  The car gate in the build runner asks
"is the SOURCE car's CAR_ROOT where `anim/carrig` puts it" -- and that is a
question about the file on disk BEFORE the append.  The question this film
actually needs answered is "is the CAR_ROOT that ended up INSIDE THE FILM
where `anim/carrig` puts it", i.e. did the append carry the keys through.
Those are different questions and only the second one is about the artefact
being shipped.

It reads KEYS, not dates, and that is the whole point: R2-3308 showed a date
check firing on a car whose blend is 19.4 h NEWER than the file whose motion
it does not contain.  The instrument is known to separate the two cars --
`R22041` reads worst 678.031 m at f2978, the rebuild reads 0.0000 m on all six
probes -- so a PASS here is a real discrimination, not a tautology.
"""
import os
import sys

import bpy

R2 = "/home/zany/f1-round2"
sys.path.insert(0, os.path.join(R2, "tools"))
sys.path.insert(0, os.path.join(R2, "anim"))

import car_staleness as CS          # noqa: E402

scene = bpy.context.scene
root = bpy.data.objects.get("CAR_ROOT")

print(">> film   %s (%d bytes)"
      % (bpy.data.filepath, os.path.getsize(bpy.data.filepath)))
print(">> probe frames %s   tolerance %.3f m"
      % (CS.KEY_PROBE_FRAMES, CS.KEY_TOL_M))

if root is None:
    print(">> STAGE RESULT: FILM_CAR_KEYS_FAIL (no CAR_ROOT in the film -- the "
          "append did not land)")
    raise SystemExit(1)

print(">> CAR_ROOT found: %r, animation_data=%s"
      % (root.name, root.animation_data is not None))

reasons = CS.check_appended_car_keys(root, scene)
if reasons:
    for r in reasons:
        print(">> CAR KEYS: %s" % r)
    print(">> STAGE RESULT: FILM_CAR_KEYS_STALE")
    raise SystemExit(1)

print(">> CAR KEYS: none - the CAR_ROOT INSIDE THE FILM matches anim/carrig "
      "over %d probe frames" % len(CS.KEY_PROBE_FRAMES))
print(">> STAGE RESULT: FILM_CAR_KEYS_MATCH_SOURCE")
