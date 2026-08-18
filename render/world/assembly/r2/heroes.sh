#!/usr/bin/env bash
# The frames that have to answer for the five defects, on the rented 5090.
set -u
cd $HOME/vast-render
D=$HOME/f1-round2/render/world/assembly/r2
SCENE=$D/render2.blend
try () {  # cam W H samples outfile [extra rq flags...]
  local cam="$1" w="$2" h="$3" sm="$4" of="$5"; shift 5
  for i in 1 2 3; do
    echo "=== $cam try $i $(date +%T)"
    ./rq render --scene "$SCENE" --cam "$cam" --res "$w" "$h" --samples "$sm" \
        --dof off "$@" --wait -o "$D/$of" 2>&1 | tail -3
    if [ -s "$D/$of" ]; then return 0; fi
    sleep 45
  done
  echo "!! $cam FAILED after 3 tries"
}
try CAM_T4_INTRUSION  3840 2160 512 CAM_T4_INTRUSION.png
try CAM_T4_KERB       3840 2160 512 CAM_T4_KERB.png
try CAM_GLASS_GAP     3840 2160 512 CAM_GLASS_GAP.png
try CAM_APRON_EDGE    3840 2160 640 CAM_APRON_EDGE.png
try CAM_TRANSIT_BLOCK 3840 2160 512 CAM_TRANSIT_BLOCK.png
try CAM_DOPPLER       3840 2160 512 CAM_DOPPLER.png
try CAM_WIDE          3840 2160 512 CAM_WIDE.png
# CAM_CAL IS SUPPOSED TO BE UNIFORM. It looks at an 18 % lambertian card 12 m
# across from 4.36 m on a 50 mm lens, so the card fills the frame by construction
# — a frustum raycast measured 441 of 441 rays landing on it. The middleware's
# blank detector then correctly flagged UNIFORM (mean 0.273757, sd 0.003243,
# identical across three attempts) and failed the job three times running.
#
# The detector was right; the caller asked the wrong question. --allow-blank is
# passed HERE ONLY, per camera, and deliberately not in `try`'s defaults: a blanket
# allow would silence the detector on the seven frames where a black or flat
# result IS the defect we are looking for. (R2-... / task #49.)
try CAM_CAL           1024  512 256 CAM_CAL.png --allow-blank
echo "HEROES DONE $(date +%T)"
