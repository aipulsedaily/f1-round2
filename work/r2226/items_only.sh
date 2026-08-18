#!/bin/bash
cd $HOME/f1-round2
B=/opt/blender-5.2.0-linux-x64/blender
# 1. items alone, into an empty scene
$B -b --factory-startup -noaudio -P world/build_items.py -- \
   --place crew_figure,timing_stand --out work/r2226/items_only.blend \
   --report work/r2226/items_only_build.json > work/r2226/items_only_build.log 2>&1
echo "build: $(grep 'STAGE RESULT' work/r2226/items_only_build.log)"
# 2. keep-out gate on the items alone
$B -b work/r2226/items_only.blend --factory-startup -noaudio -P tools/placement_gate.py -- \
   --out work/r2226/keepout_items.json > work/r2226/keepout_items.log 2>&1
echo "keepout(items): $(grep 'STAGE RESULT' work/r2226/keepout_items.log)"
# 3. THE CONTROLS -- R2-110: the batteries ran this gate twice against the world
#    and never once against a case that must fail or must pass.
for c in ctl_place_pos ctl_place_neg ctl_place_nearmiss_neg; do
  $B -b render/world/assembly/r2/v120/$c.blend --factory-startup -noaudio -P tools/placement_gate.py -- \
     --out work/r2226/keepout_$c.json > work/r2226/keepout_$c.log 2>&1
  echo "control $c: $(grep 'STAGE RESULT' work/r2226/keepout_$c.log)"
done
echo KEEPOUTDONE
