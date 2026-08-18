#!/usr/bin/env bash
# RENDER AND LOOK at the pit exit and the apron on the v1.2.0 rebuild.
# 1080p first, then zoom crops. Never straight to 4K.
set -u
B=/opt/blender-5.2.0-linux-x64/blender
D=$HOME/f1-round2/render/world/assembly/r2
V=$D/v120
S=$D/assembly5.blend

echo "########## render_setup -> render5.blend $(date +%T)"
$B -b -noaudio $S --factory-startup -P $D/render_setup3.py -- \
   --out=$D/render5.blend > $V/render_setup5.log 2>&1
echo "########## setup exit=$? $(date +%T)"
tail -3 $V/render_setup5.log
ls -l $D/render5.blend

cd $HOME/vast-render
SCENE=$D/render5.blend
try () {  # cam W H samples outfile [extra...]
  local cam="$1" w="$2" h="$3" sm="$4" of="$5"; shift 5
  for i in 1 2 3; do
    echo "=== $cam try $i $(date +%T)"
    ./rq render --scene "$SCENE" --cam "$cam" --res "$w" "$h" --samples "$sm" \
        --dof off --agent worldrebuild --wait -o "$V/$of" "$@" 2>&1 | tail -4
    if [ -s "$V/$of" ]; then return 0; fi
    sleep 60
  done
  echo "!! $cam FAILED after 3 tries"
}

# --- the three frames that answer for #47 / #48 / #50, at 1080p -------------
try CAM_PITEXIT_SEAM  1920 1080 256 v120_CAM_PITEXIT_SEAM_1080.png
try CAM_APRON_EDGE    1920 1080 256 v120_CAM_APRON_EDGE_1080.png
try CAM_PIT_NOSE      1920 1080 256 v120_CAM_PIT_NOSE_1080.png
try CAM_TRANSIT_BLOCK 1920 1080 256 v120_CAM_TRANSIT_BLOCK_1080.png

# --- pixel-peep: the apron's sawn joints and the pit-exit seam --------------
# --zoom multiplies pixel density BEFORE cropping, so these are real detail.
try CAM_APRON_EDGE   1920 1080 320 v120_PEEP_apron_joint.png \
    --border 0.05 0.35 0.02 0.28 --zoom 6
try CAM_PITEXIT_SEAM 1920 1080 320 v120_PEEP_pitexit_seam.png \
    --border 0.30 0.70 0.10 0.45 --zoom 6

echo "########## HEROES v120 DONE $(date +%T)"
