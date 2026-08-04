#!/bin/bash
cd /home/zany/f1-round2
for it in crew_figure timing_stand armco_post catch_fence_post tyre_wall_tyre gantry_truss pont_girder heras_fence_panel spectator_crowd terrain_ground forecourt_paving_bay pit_wall_unit; do
  b=world/items/${it}_test.blend
  [ -f "$b" ] || { echo "MISSING $b"; continue; }
  /opt/blender-5.2.0-linux-x64/blender -b "$b" --factory-startup -noaudio \
    -P work/r2226/probe_item_blend.py -- --json work/r2226/probe_${it}.json > work/r2226/probe_${it}.log 2>&1
  echo "done $it  $(grep -c 'STAGE RESULT: PROBE_OK' work/r2226/probe_${it}.log)"
done
echo ALLDONE
