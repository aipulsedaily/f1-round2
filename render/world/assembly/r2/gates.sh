#!/usr/bin/env bash
# The three shipped gates, run on the reassembled world.
set -u
B=/opt/blender-5.2.0-linux-x64/blender
R2=$HOME/f1-round2
D=$R2/render/world/assembly/r2
SCENE=${1:-$D/assembly2.blend}

echo "############ placement_gate.py  (shipped --allow default)"
$B -b "$SCENE" --factory-startup -P $R2/tools/placement_gate.py -- \
   --out $D/placement_default.json 2>&1 | grep -v "^Fra:" | tail -60

echo
echo "############ placement_gate.py  (+ the barrier GROUND objects that the"
echo "############ shipped default list misses: BR_Subbase, BR_Trap, BR_Stones)"
$B -b "$SCENE" --factory-startup -P $R2/tools/placement_gate.py -- \
   --out $D/placement_ground.json \
   --allow "SURF_,TER_Ground,BR_Runoff,BR_Gravel,BR_Subbase,BR_Trap,BR_Stone,BR_Verge,ARCH_Paving,ARCH_Markings,Floor,Turntable_,Platform_" \
   2>&1 | grep -v "^Fra:" | tail -60

echo
echo "############ collision_gate.py"
$B -b "$SCENE" --factory-startup -P $R2/tools/collision_gate.py -- \
   --out $D/collision.json 2>&1 | grep -v "^Fra:" | tail -40

echo
echo "############ depth_probe.py"
$B -b "$SCENE" --factory-startup -P $R2/tools/depth_probe.py -- \
   --frames 1 --out $D/depth.json 2>&1 | grep -v "^Fra:" | tail -20

echo "GATES DONE"
