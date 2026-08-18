#!/bin/bash
# film16 = the film scene on assembly10 -- the BATCHED REBUILD's film.
# Same harness as v124/build_film14.sh, one generation on, so the two are
# comparable line for line.
#
# TWO THINGS ARE DIFFERENT FROM film14 AND BOTH ARE THE POINT:
#   * the world is assembly10 (six landed source fixes + four item rows PLACE)
#   * `--car world/car_anim_driver.blend` instead of the default
#     `world/car_anim.blend`, so there is a DRIVER IN THE CAR.  `--car` is a
#     PATH, not a flag; passing the flag name alone would silently build the
#     empty-cockpit car, which is the shipped default.
#
# THE FULL CHAIN, IN ORDER, and none of it skipped:
#   1  tools/build_beatsheet.py     -> docs/beat_sheet.json   (beat 1)
#   2  tools/author_beats2_5.py     -> docs/beat_sheet.json   (beats 2-5)
#   3  anim/build_camera_rig.py     -> world/camera_rig.blend + camera_rig_path.json
#   4  tools/build_film_scene.py    -> render/film16.blend
#
# Steps 1 and 2 are run by the promotion and are NOT repeated here; the sheet
# they produced is hashed below so this build records which one it used.
#
# NO --world-override is passed.  SHIPPING.md must declare assembly10 before
# this runs, or the build must fail -- and that failure would be the guard
# working.
set -u
cd $HOME/f1-round2
W=work/r2500
D=render/world/assembly/r2
ASM=$D/assembly10.blend
OUT=render/film16.blend
CAR=world/car_anim_driver.blend
B=/opt/blender-5.2.0-linux-x64/blender

{
  echo "=== INPUTS, hashed at $(date -Is) ==="
  echo "--- declared ship (the ONE declaration) ---"
  python3 tools/shipping_world.py
  echo "--- source identity ---"
  sha256sum tools/build_film_scene.py anim/build_camera_rig.py \
            tools/author_beats2_5.py tools/build_beatsheet.py \
            docs/beat_sheet.json docs/presentation_normals.json \
            world/showroom_lighting.py world/film_exposure.py world/build_sky.py \
            world/world_contract.py telemetry/telemetry.csv $CAR
  echo "--- git ---"
  git rev-parse HEAD
  git status --short
} > $W/inputs_film16_pre.txt 2>&1
cat $W/inputs_film16_pre.txt

echo
echo "######## 3  anim/build_camera_rig.py"
START=$(date +%s)
$B -b world/beat1_anim.blend --factory-startup -P anim/build_camera_rig.py -- \
    --sheet docs/beat_sheet.json --telemetry telemetry/telemetry.csv \
    --out world/camera_rig.blend > $W/build_camera_rig.log 2>&1
echo "  rc=$?  in $(( $(date +%s) - START )) s   (exit status is NOT the evidence)"
grep -E "^>> |STAGE RESULT|Traceback" $W/build_camera_rig.log | tail -25

echo
echo "######## 4  tools/build_film_scene.py  on $(basename $ASM)  WITH THE DRIVER"
START=$(date +%s)
$B -b "$ASM" --factory-startup -P tools/build_film_scene.py -- \
    --out "$OUT" --car "$CAR" > $W/build_film16.log 2>&1
RC=$?
END=$(date +%s)
echo "exit=$RC seconds=$((END-START))   (exit status is NOT the evidence)"
grep -E "^>> |STAGE RESULT|REFUS|Traceback|WORLD" $W/build_film16.log | tail -60
ls -la "$OUT" 2>&1

TOKEN=$(grep -o '>> STAGE RESULT: [A-Z_]*' $W/build_film16.log | tail -1)
if [ "$TOKEN" = ">> STAGE RESULT: FILM_SCENE_BUILT" ]; then
  echo ">> STAGE RESULT: FILM16_BUILT"
else
  echo ">> STAGE RESULT: FILM16_FAIL ($TOKEN)"
fi
