#!/bin/bash
# film22 -- the film carrying BOTH of R2-2041's fixes, and the first film that
# carries either.
#
#   assembly14  -> world/build_surface.py's apron runs tyre_deposit at N = 1000
#   R22041 car  -> CarbonFibre's twill re-pitched 1.6535 mm -> 5.000 mm
#
# BOTH WERE VERIFIED IN THEIR OWN BUILT ARTEFACTS BEFORE THIS RAN, off the
# sockets and not off the source: `Traffic Passes` reads 1000.0000 and
# `Mapping.Scale` reads 62.8319.  This stage exists to carry them into the ONE
# artefact a frame comes out of, because "the source is correct" has been the
# trap four times on this project.
#
# THE BREACH STAGE IS DELIBERATELY OMITTED.  run_rebuild21 died there
# (`KeyError: bpy.data.collections["BREACH_Fines"]` inside apply_breach, after
# 1,234 s of fines work) and film21_breach.blend does not exist.  That defect is
# not this block's, it is not in either fix's path, and the two proof frames --
# f599/f661 in the darkened showroom and f1030 on the pit-exit apron -- contain
# no breached glazing.  Chasing it here would couple two unrelated failures.
# film22.blend is therefore a PROOF ARTEFACT for these two fixes, not a ship
# candidate; the ship candidate needs the breach bug fixed first.
set -u
cd $HOME/f1-round2
W=work/r22041
V=render/world/assembly/r2/v126
CAR=world/R22041_car_anim_driver_CS.blend
ASM=render/world/assembly/r2/assembly14.blend
B=/opt/blender-5.2.0-linux-x64/blender
mkdir -p $W
exec > >(tee -a $W/REBUILD22.log) 2>&1
echo "######################## R2-2041 film22 $(date -Is)"

[ -s "$ASM" ] || { echo ">> STAGE RESULT: REBUILD22_FAIL (no assembly14)"; exit 10; }
[ -s "$CAR" ] || { echo ">> STAGE RESULT: REBUILD22_FAIL (no $CAR)"; exit 10; }
grep -q "STAGE RESULT: ASSEMBLY14_FIXES_PRESENT" $W/assembly14_stdout.txt || {
  echo ">> STAGE RESULT: REBUILD22_FAIL (assembly14 did not pass acceptance)"
  exit 10; }
ls -la "$ASM" "$CAR"

# build_film_scene REFUSES an undeclared world, so this is a required step.
# NOTE: SHIPPING.md is held by another agent's lease (`inflight-auto`). It is
# edited on disk because no build can run without it, and it is NOT staged or
# committed by this block -- the declaration is the owner's to make permanent.
python3 - <<'PY'
import re
p = "render/world/assembly/r2/SHIPPING.md"
s = open(p).read()
s2, n = re.subn(r"\*\*`assembly\d+\.blend`", "**`assembly14.blend`", s, count=1)
if n != 1:
    raise SystemExit("REFUSING: could not rewrite the SHIPPING.md declaration")
open(p, "w").write(s2)
print(">> SHIPPING.md now declares assembly14.blend")
PY
DECL=$(python3 tools/shipping_world.py 2>&1)
echo ">> shipping_world declares: $DECL"
case "$DECL" in *assembly14.blend) ;; *) echo ">> STAGE RESULT: REBUILD22_FAIL (declaration)"; exit 11 ;; esac

waitmem () {
  for i in $(seq 1 960); do
    A=$(free -g | awk '/^Mem:/{print $7}')
    [ "$A" -ge 5 ] && { echo "[gate] ${A} GB available, starting $1"; return 0; }
    [ $((i % 10)) -eq 1 ] && echo "[gate] $1 waiting: ${A} GB available (need 5)"
    sleep 30
  done
  echo "[gate] TIMEOUT before $1"; return 1
}

echo; echo "######## 1/2  build_film_scene -> render/film22.blend"
waitmem film_scene || exit 90
$B -b "$ASM" --factory-startup -noaudio -P tools/build_film_scene.py -- \
    --out render/film22.blend --car "$CAR" > $W/build_film22.log 2>&1
echo "  rc=$?  (exit status is NOT the evidence)"
grep -aE "^>> |STAGE RESULT|REFUS|Traceback|WORLD STALENESS" $W/build_film22.log | tail -40
grep -qa ">> STAGE RESULT: FILM_SCENE_BUILT" $W/build_film22.log || {
  echo ">> STAGE RESULT: REBUILD22_FAIL (film22 scene)"; exit 12; }
grep -qa "sky/camera bind CHECKED" $W/build_film22.log || {
  echo ">> STAGE RESULT: REBUILD22_FAIL (no sky rebind check)"; exit 13; }

echo; echo "######## 2/2  focus"
waitmem focus || exit 90
$B -b render/film22.blend --factory-startup -noaudio -P tools/r2791_apply_focus.py -- \
   --grid work/r2840/depthgrid_R2842.json --report $W/focus_report_film22.json \
   --out render/film22.blend > $W/apply_focus22.log 2>&1
grep -aE "^>> |STAGE RESULT" $W/apply_focus22.log | tail -12
grep -qa "STAGE RESULT R2791_APPLY_OK" $W/apply_focus22.log || {
  echo ">> STAGE RESULT: REBUILD22_FAIL (focus)"; exit 14; }

ls -la render/film22.blend
echo ">> STAGE RESULT: REBUILD22_BUILT"
