#!/usr/bin/env bash
# The frames that have to answer for #46, #47 and #48, on the rented 5090.
set -u
cd $HOME/vast-render
D=$HOME/f1-round2/render/world/assembly/r2
SCENE=$D/render3.blend
try () {  # cam W H samples outfile
  local cam="$1" w="$2" h="$3" sm="$4" of="$5"
  for i in 1 2 3; do
    echo "=== $cam try $i $(date +%T)"
    ./rq render --scene "$SCENE" --cam "$cam" --res "$w" "$h" --samples "$sm" \
        --dof off --agent pitexit --wait -o "$D/$of" 2>&1 | tail -3
    if [ -s "$D/$of" ]; then return 0; fi
    sleep 45
  done
  echo "!! $cam FAILED after 3 tries"
}
try CAM_APRON_EDGE     3840 2160 640 v111_CAM_APRON_EDGE.png
try CAM_PITEXIT_SEAM   3840 2160 640 v111_CAM_PITEXIT_SEAM.png
try CAM_PIT_NOSE       3840 2160 512 v111_CAM_PIT_NOSE.png
try CAM_TRANSIT_BLOCK  3840 2160 512 v111_CAM_TRANSIT_BLOCK.png
echo "HEROES v111 DONE $(date +%T)"
