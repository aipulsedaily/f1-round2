#!/usr/bin/env bash
# R2-1821: the f2760 ground A/B.
#
#   arm A  R2-1661 EXACTLY AS IT LANDED -- the existing `ground_after_4cam.blend`,
#          with `CAM_b6_2760` re-baked into it.  No rebuild: the geometry is the
#          geometry that was verified at f2811, which is the whole point.  The rebake
#          runs the CURRENT module, which is legitimate because `bake_cameras` and
#          `test_scene` build the camera, the road proxy and build_sky's light and
#          NOTHING ELSE -- R2-1821 touches `habitat`, three density lines and one
#          constant, none of which those two functions call.
#   arm B  the same build with R2-1821's `paved` predicate.
#
# `b6_2760` was already in `_VIEWS_WORLD` -- R2-1129 lifted all four beat-6 poses out
# of the R2943 path -- it had simply never been baked into a blend.  So the A/B is at
# the client's own camera, lens and exposure, not at an approximation of it.
#
# t5_verge and b6_2811 ride along as the regression pair: t5_verge is beats 1-5's
# ground and must not move, b6_2811 is the frame R2-1661 was verified on and must not
# get worse.
set -u
R2=$HOME/f1-round2
OUT=$R2/render/r2_1821
BL=/opt/blender-5.2.0-linux-x64/blender
mkdir -p "$OUT"

step_rebake_A() {
  [ -s "$OUT/ground_A_5cam.blend" ] && { echo "have arm A blend"; return; }
  echo "=== arm A: re-bake CAM_b6_2760 into R2-1661's verified geometry ==="
  $BL -b --factory-startup -noaudio -P "$R2/tools/r2_1661_rebake.py" -- \
      --module "$R2/world/build_terrain.py" \
      --load "$R2/render/r2_1661/ground_after_4cam.blend" \
      --save "$OUT/ground_A_5cam.blend" \
      --cams b6_2760,b6_2811,t5_verge,esses 2>&1 | tail -6
}

step_build_B() {
  [ -s "$OUT/ground_B_5cam.blend" ] && { echo "have arm B blend"; return; }
  echo "=== arm B: full terrain build with R2-1821 ==="
  $BL -b --factory-startup -noaudio -P "$R2/world/build_terrain.py" -- \
      --selftest --cams b6_2760,b6_2811,t5_verge,esses \
      --save "$OUT/ground_B_5cam.blend" 2>&1 | tee "$OUT/build_B.log" \
      | grep -E "STAGE RESULT|sward|verge clumps|meadow clumps|grass:|plants_|Saved"
}

step_render() {
  cd $HOME/vast-render || exit 1
  run() {   # arm cam w h samples
    local dst="$OUT/${1}_${2}.png"
    [ -s "$dst" ] && { echo "have  $dst"; return; }
    echo "=== render $1 $2 ${3}x${4} @${5} ==="
    ./rq render --scene "$OUT/ground_${1}_5cam.blend" --cam "CAM_${2}" \
        --res "$3" "$4" --samples "$5" --wait -o "$dst" 2>&1 | tail -3
  }
  # GROUPED BY ARM, not by camera.  The worker holds ONE scene resident; alternating
  # A/B/A/B makes it swap the 1.1 GB scene six times instead of twice.
  for arm in A B; do
    run "$arm" b6_2760  3840 2160 512     # the client's frame -- the judgement
    run "$arm" b6_2811  3840 2160 512     # the frame R2-1661 was verified on
    run "$arm" t5_verge 1920 1080 256     # beats 1-5's ground -- must not move
  done
}

case "${1:-all}" in
  rebake) step_rebake_A ;;
  build)  step_build_B ;;
  render) step_render ;;
  *)      step_rebake_A; step_build_B; step_render ;;
esac
echo "=== done ==="; ls -la "$OUT"/*.png 2>/dev/null
