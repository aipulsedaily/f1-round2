#!/bin/bash
# film14 = the film scene on assembly9 -- the first film built on a world that
# carries R2-132's pit-exit apron.  Same harness as work/r2127/build_film13.sh,
# one generation on, so the two are comparable line for line.
#
# THE FULL CHAIN, IN ORDER, and none of it skipped:
#   1  tools/author_beats2_5.py      -> docs/beat_sheet.json
#   2  anim/build_camera_rig.py      -> world/camera_rig.blend + camera_rig_path.json
#   3  tools/build_film_scene.py     -> render/film14.blend
#
# NO --world-override is passed.  SHIPPING.md must declare assembly9 before this
# runs, or the build must fail -- and that failure would be the guard working.
set -u
cd $HOME/f1-round2
W=work/r2148
D=render/world/assembly/r2
ASM=$D/assembly9.blend
OUT=render/film14.blend
B=/opt/blender-5.2.0-linux-x64/blender

{
  echo "=== INPUTS, hashed at $(date -Is) ==="
  echo "--- declared ship (the ONE declaration) ---"
  .venv/bin/python tools/shipping_world.py
  echo "--- source identity ---"
  sha256sum tools/build_film_scene.py anim/build_camera_rig.py \
            tools/author_beats2_5.py tools/build_beatsheet.py \
            docs/beat_sheet.json world/showroom_lighting.py \
            world/film_exposure.py world/build_sky.py \
            world/world_contract.py telemetry/telemetry.csv \
            tools/horizon_gate.py world/camera_rig_path.json
  echo "--- git ---"
  git rev-parse HEAD
  git status --short
  echo "--- mtimes ---"
  ls -la --time-style=+%F_%T $ASM world/car_anim.blend docs/beat_sheet.json \
       anim/build_camera_rig.py world/build_*.py
} > $W/inputs_film14_pre.txt 2>&1
cat $W/inputs_film14_pre.txt

echo
echo "######## 1  author_beats2_5.py"
cp docs/beat_sheet.json $W/beat_sheet_BEFORE_author.json
.venv/bin/python tools/author_beats2_5.py > $W/author.log 2>&1
echo "  rc=$?  (exit status is NOT the evidence)"
tail -4 $W/author.log
echo "  sheet sha BEFORE: $(sha256sum $W/beat_sheet_BEFORE_author.json | cut -c1-8)"
echo "  sheet sha AFTER : $(sha256sum docs/beat_sheet.json | cut -c1-8)"

echo
echo "######## 2  anim/build_camera_rig.py"
cp world/camera_rig_path.json $W/camera_rig_path_BEFORE.json
START=$(date +%s)
$B -b world/beat1_anim.blend --factory-startup -P anim/build_camera_rig.py -- \
    --sheet docs/beat_sheet.json --telemetry telemetry/telemetry.csv \
    --out world/camera_rig.blend > $W/build_camera_rig.log 2>&1
echo "  rc=$?  in $(( $(date +%s) - START )) s"
grep -E "^>> |STAGE RESULT|Traceback" $W/build_camera_rig.log | tail -20
echo "  path sha BEFORE: $(sha256sum $W/camera_rig_path_BEFORE.json | cut -c1-8)"
echo "  path sha AFTER : $(sha256sum world/camera_rig_path.json | cut -c1-8)"
echo "  git says about the tracked rig path:"
git status --short world/camera_rig_path.json || true

echo
echo "######## 3  tools/build_film_scene.py  on $(basename $ASM)"
START=$(date +%s)
$B -b "$ASM" --factory-startup -P tools/build_film_scene.py -- --out "$OUT" \
    > $W/build_film14.log 2>&1
RC=$?
END=$(date +%s)
echo "exit=$RC seconds=$((END-START))   (exit status is NOT the evidence)" \
     | tee -a $W/inputs_film14_pre.txt
grep -E "^>> |STAGE RESULT|REFUS|Error|Traceback|WORLD" $W/build_film14.log | tail -60
ls -la "$OUT" 2>&1
echo "FILM14 BUILD DONE rc=$RC in $((END-START)) s"
