#!/usr/bin/env bash
# R2-1661: the ground A/B on the 5090, at the delivered grade (AgX / None / -3.628,
# baked in by build_terrain's own setup_render).  Both arms terrain-only; the camera
# is the one that rendered the four existing 4K stills (R2-1129).
#   beat 6 -- the judgement, at delivery res and samples
#   beat 5 -- the regression check, at 1080p: the question there is "did the new
#             mid-ground layer make an established beat worse", which does not need
#             4K to answer.
set -u
VR=$HOME/vast-render
OUT=$HOME/f1-round2/render/r2_1661
cd "$VR" || exit 1
run() {  # arm cam W H samples
  local arm=$1 cam=$2 w=$3 h=$4 s=$5
  local dst="$OUT/${arm}_${cam}.png"
  [ -s "$dst" ] && { echo "have  $dst"; return; }
  echo "=== $arm $cam ${w}x${h} @${s} ==="
  ./rq render --scene "$OUT/ground_${arm}_4cam.blend" --cam "CAM_${cam}" \
      --res "$w" "$h" --samples "$s" --wait -o "$dst" 2>&1 | tail -3
}
for arm in before after; do
  run "$arm" b6_2811 3840 2160 512
  run "$arm" b6_2978 3840 2160 512
done
for arm in before after; do
  run "$arm" t5_verge 1920 1080 256
  run "$arm" esses    1920 1080 256
done
echo "=== done ==="; ls -la "$OUT"/*.png
