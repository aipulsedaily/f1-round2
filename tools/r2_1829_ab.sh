#!/usr/bin/env bash
# R2-1829 + R2-1824: the two remaining hard edges, A/B'd together.
#
#   arm B  R2-1821 as landed -- `render/r2_1821/ground_B_5cam.blend`, rebaked to carry
#          `CAM_sward_rim`.  No rebuild: it is the geometry already rendered and
#          measured, with one camera added.
#   arm C  the same build with the verge band's rim crossfaded and the sward layer's
#          last tier given its outward fade.
#
# The two fixes are independent of each other and neither touches R2-1821's district
# predicate, so one pair of frames settles both:
#   b6_2760    the client's frame -- carries the verge rim at f = 42 m (R2-1829)
#   sward_rim  a DIAGNOSTIC view, the only place the 1050 m radius is visible at all
#   t5_verge   beats 1-5's ground -- the verge taper's regression risk lives here
#   b6_2811    the frame R2-1661 was signed off on
set -u
R2=$HOME/f1-round2
OUT=$R2/render/r2_1829
BL=/opt/blender-5.2.0-linux-x64/blender
CAMS=b6_2760,b6_2811,t5_verge,sward_rim
mkdir -p "$OUT"

step_rebake_B() {
  [ -s "$OUT/ground_B_rim.blend" ] && { echo "have arm B blend"; return; }
  echo "=== arm B: re-bake $CAMS into R2-1821's measured geometry ==="
  $BL -b --factory-startup -noaudio -P "$R2/tools/r2_1661_rebake.py" -- \
      --module "$R2/world/build_terrain.py" \
      --load "$R2/render/r2_1821/ground_B_5cam.blend" \
      --save "$OUT/ground_B_rim.blend" --cams "$CAMS" 2>&1 | tail -5
}

step_build_C() {
  [ -s "$OUT/ground_C.blend" ] && { echo "have arm C blend"; return; }
  echo "=== arm C: full terrain build with R2-1829 + R2-1824 ==="
  $BL -b --factory-startup -noaudio -P "$R2/world/build_terrain.py" -- \
      --selftest --cams "$CAMS" --save "$OUT/ground_C.blend" 2>&1 \
      | tee "$OUT/build_C.log" \
      | grep -E "STAGE RESULT|sward|verge clumps|meadow clumps|grass:|plants_|Saved"
}

step_render() {
  cd $HOME/vast-render || exit 1
  run() {   # arm blend cam w h samples
    local dst="$OUT/${1}_${3}.png"
    [ -s "$dst" ] && { echo "have  $dst"; return; }
    echo "=== render $1 $3 ${4}x${5} @${6} ==="
    ./rq render --scene "$OUT/$2" --cam "CAM_$3" --res "$4" "$5" --samples "$6" \
        --wait -o "$dst" 2>&1 | tail -3
  }
  # grouped by ARM: the worker holds one scene resident, so this is two swaps not eight
  run B ground_B_rim.blend sward_rim 1920 1080 256
  run C ground_C.blend     b6_2760   3840 2160 512
  run C ground_C.blend     b6_2811   3840 2160 512
  run C ground_C.blend     t5_verge  1920 1080 256
  run C ground_C.blend     sward_rim 1920 1080 256
  # arm B's b6_2760 / b6_2811 / t5_verge already exist as render/r2_1821/B_*.png
  for c in b6_2760 b6_2811 t5_verge; do
    [ -s "$OUT/B_$c.png" ] || cp "$R2/render/r2_1821/B_$c.png" "$OUT/B_$c.png"
  done
}

case "${1:-all}" in
  rebake) step_rebake_B ;;
  build)  step_build_C ;;
  render) step_render ;;
  *)      step_rebake_B; step_build_C; step_render ;;
esac
echo "=== done ==="
ls -la "$OUT"/*.png 2>/dev/null || true
