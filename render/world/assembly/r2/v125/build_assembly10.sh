#!/bin/bash
# Build assembly10 from source -- THE BATCHED REBUILD.
# Same script shape as v124/build_assembly9.sh so the two builds are comparable.
#
# Source delta against assembly9 (all of it uncommitted working-copy work by
# other agents, landed and waiting for a rebuild to reach a frame):
#   world/build_architecture.py  R2-366 paving relief ladder, R2-331 pit-wall
#                                stand ownership, apron/roof/deck surfaces
#   world/build_barriers.py      R2-331 fence-post ownership switch
#   world/build_items.py         the class-feature ownership arm + the stage
#   world/items/PLACEMENT.json   4 rows HOLD -> PLACE (this is task #121)
set -u
cd /home/zany/f1-round2
D=work/r2500
mkdir -p $D
OUT=/home/zany/f1-round2/render/world/assembly/r2/assembly10.blend

{
  echo "=== INPUTS, hashed at $(date -Is) ==="
  sha256sum world/world_contract.py world/build_surface.py world/build_barriers.py \
            world/build_architecture.py world/build_terrain.py world/build_dressing.py \
            world/build_items.py world/items/PLACEMENT.json \
            render/world/assembly/r2/assemble.py telemetry/telemetry.csv
  git -C /home/zany/f1-round2 rev-parse HEAD
  git -C /home/zany/f1-round2 status --short
} > $D/inputs_assembly10.txt 2>&1

START=$(date +%s)
/opt/blender-5.2.0-linux-x64/blender -b -noaudio --factory-startup \
    -P render/world/assembly/r2/assemble.py -- --out=$OUT \
    > $D/build_assembly10.log 2>&1
RC=$?
END=$(date +%s)
echo "exit=$RC seconds=$((END-START))" | tee -a $D/inputs_assembly10.txt
ls -la $OUT >> $D/inputs_assembly10.txt 2>&1

# `$?` IS WORTHLESS HERE -- Blender 5.2 exits 0 on an uncaught script exception.
# Judge on the token assemble.py prints, and on nothing else.
TOKEN=$(grep -o '>> STAGE RESULT: [A-Z_]*' $D/build_assembly10.log | tail -1)
echo "seconds=$((END-START)) rc=$RC  $TOKEN"
grep -E '^>> ASM MODULES' $D/build_assembly10.log || true
if [ "$TOKEN" = ">> STAGE RESULT: ASSEMBLE_OK" ]; then
  echo ">> STAGE RESULT: ASSEMBLY10_BUILT"
else
  echo ">> STAGE RESULT: ASSEMBLY10_FAIL"
fi
