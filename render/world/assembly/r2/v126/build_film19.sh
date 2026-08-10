#!/bin/bash
# film19 = THE REBUILD.  The film scene on assembly11, with the car rebuilt so
# it carries the lap-down, and every manifest change that lands at scene-build
# time.  R2-1701.
#
#   usage: build_film19.sh <car-blend>
#
# WHAT THIS CARRIES THAT film18 DID NOT
#   * assembly11 -- film18 was built on assembly10 (Aug 4), which predates FOUR
#     of its own generators, so the beat-4 pit annexe (build_architecture.py)
#     and the asphalt relief re-budget (build_surface.py) were in source and in
#     no film.  The R2-1661 ground pass rides along.
#   * a car with the beat-6 LAP-DOWN.  carpath.py is 08:40 and the R2829 car is
#     04:24, so film18 shipped without it.  Rebuilding the car anim picks it up
#     for free -- pose_series reads carpath.Car._extrap.
#   * the beat-6 ending re-key, folded into the GENERATORS (not the generated
#     sheet) so it survives regeneration: closing lens 40/74 -> 55/130 mm and
#     the aim tracks the car for the whole beat instead of whipping 82 deg to
#     the facade at t=+4.0.
#
# THE ORDER IS NOT NEGOTIABLE and each item fails SILENTLY if violated -- see
# docs/NEXT-REBUILD.md "Order matters".  Of them, this script owns:
#   (1) re-bind the sky after the camera rig is rebuilt.  build_camera_rig
#       DELETES every camera; build_sky's two SCRIPTED drivers then point at a
#       dead ID and the decks "behave as a skybox".  build_film_scene does the
#       rebind itself and PRINTS the check -- the grep below fails the build if
#       that line is missing, because a silent skybox is the whole defect.
#   (6) the rig is rebuilt from the CURRENT sheet, which build_film_scene does
#       by calling build_camera_rig.main() with its own --out, so the path file
#       is named after THIS film and no stale world/camera_rig_path.json is
#       consulted.
set -u
CAR=${1:?usage: build_film19.sh <car-blend>}
cd /home/zany/f1-round2
W=work/r21701
D=render/world/assembly/r2
ASM=$D/assembly11.blend
OUT=render/film19.blend
B=/opt/blender-5.2.0-linux-x64/blender
mkdir -p $W

[ -s "$ASM" ] || { echo ">> STAGE RESULT: FILM19_FAIL (no $ASM)"; exit 2; }
[ -s "$CAR" ] || { echo ">> STAGE RESULT: FILM19_FAIL (no car $CAR)"; exit 2; }

# The shipping declaration is a GUARD, not a formality: build_film_scene refuses
# to build on a world SHIPPING.md does not declare, and passing
# --world-override to silence that would be building on a world nobody promoted.
DECLARED=$(python3 tools/shipping_world.py 2>&1)
echo ">> shipping_world declares: $DECLARED"
case "$DECLARED" in
  *assembly11.blend) ;;
  *) echo ">> STAGE RESULT: FILM19_FAIL (SHIPPING.md declares $DECLARED, not assembly11)"; exit 3 ;;
esac

{
  echo "=== INPUTS, hashed at $(date -Is) ==="
  echo "--- declared ship ---"; python3 tools/shipping_world.py
  echo "--- source identity ---"
  sha256sum tools/build_film_scene.py anim/build_camera_rig.py \
            tools/author_beats2_5.py tools/build_beatsheet.py \
            docs/beat_sheet.json docs/circuit_spec.json \
            world/showroom_lighting.py world/film_exposure.py world/build_sky.py \
            world/world_contract.py world/showroom_ceiling.blend \
            telemetry/telemetry.csv "$CAR" "$ASM"
  echo "--- git ---"; git rev-parse HEAD; git status --short
} > $W/inputs_film19.txt 2>&1

waitmem () {
  for i in $(seq 1 960); do
    A=$(free -g | awk '/^Mem:/{print $7}')
    [ "$A" -ge 5 ] && { echo "[gate] ${A} GB available, starting $1"; return 0; }
    [ $((i % 10)) -eq 1 ] && echo "[gate] $1 waiting: ${A} GB available (need 5)"
    sleep 30
  done
  echo "[gate] TIMEOUT before $1"; return 1
}

echo
echo "######## build_film_scene.py  ->  $OUT   car=$(basename $CAR)"
waitmem build_film_scene || exit 90
START=$(date +%s)
$B -b "$ASM" --factory-startup -noaudio -P tools/build_film_scene.py -- \
    --out "$OUT" --car "$CAR" > $W/build_film19.log 2>&1
echo "exit=$?  seconds=$(( $(date +%s) - START ))   (exit status is NOT the evidence)"
grep -aE "^>> |STAGE RESULT|REFUS|Traceback|WORLD STALENESS" $W/build_film19.log | tail -70
ls -la "$OUT" 2>&1

TOKEN=$(grep -ao '>> STAGE RESULT: [A-Z_]*' $W/build_film19.log | tail -1)
if [ "$TOKEN" != ">> STAGE RESULT: FILM_SCENE_BUILT" ]; then
  echo ">> STAGE RESULT: FILM19_FAIL ($TOKEN)"; exit 4
fi

# Ordering constraint 1, asserted rather than assumed.  build_sky binds two
# cloud-parallax drivers to the camera by ID; the rig rebuild deletes cameras.
if ! grep -aq "sky/camera bind CHECKED" $W/build_film19.log; then
  echo ">> STAGE RESULT: FILM19_FAIL (no sky/camera bind check line -- the decks"
  echo "   may be silently behaving as a skybox; build_sky's own docstring)"
  exit 5
fi
grep -a "sky/camera bind CHECKED" $W/build_film19.log

echo ">> STAGE RESULT: FILM19_BUILT"
