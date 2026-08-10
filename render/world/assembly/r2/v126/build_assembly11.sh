#!/bin/bash
# Build assembly11 from source -- the world rebuild the film rebuild is blocked on.
#
# WHY THIS EXISTS (R2-1701):
#   assembly10.blend is 2026-08-04 15:46 and predates FOUR of its own generator
#   modules.  film18 was built on it, so two landed manifest changes are in no
#   film:
#     world/build_architecture.py  2026-08-07 04:11  beat-4 pit annexe loses a
#                                  storey west of PB_ANNEXE_X (6 occluded frames -> 0)
#     world/build_surface.py       2026-08-07 09:42  asphalt relief re-budget,
#                                  7 stages 3.7 mm..1.03 m, octave contrast 2.70x
#   and two more changes want to land with them:
#     world/build_terrain.py       2026-08-07 18:35  R2-1661 ground/sward pass;
#                                  its author explicitly asks for this re-run
#     world/build_dressing.py      2026-08-07 03:31
#
# `world/itemkit.py` is hashed below even though it is not a top-level mod: it is
# the shared law module that surface, terrain and dressing all import, so a stale
# reading of it is exactly the kind of silent drop this rebuild exists to stop.
# It was edited 21:20 today (K.assert_wired, R2-1154) -- that addition is
# selftest-only and not on the build path, which is why this build may proceed.
set -u
cd /home/zany/f1-round2
D=work/r21701
mkdir -p $D
OUT=/home/zany/f1-round2/render/world/assembly/r2/assembly11.blend

{
  echo "=== INPUTS, hashed at $(date -Is) ==="
  sha256sum world/world_contract.py world/build_surface.py world/build_barriers.py \
            world/build_architecture.py world/build_terrain.py world/build_dressing.py \
            world/build_items.py world/itemkit.py world/items/PLACEMENT.json \
            render/world/assembly/r2/assemble.py telemetry/telemetry.csv
  git -C /home/zany/f1-round2 rev-parse HEAD
  git -C /home/zany/f1-round2 status --short
} > $D/inputs_assembly11.txt 2>&1

START=$(date +%s)
/opt/blender-5.2.0-linux-x64/blender -b -noaudio --factory-startup \
    -P render/world/assembly/r2/assemble.py -- --out=$OUT \
    > $D/build_assembly11.log 2>&1
RC=$?
END=$(date +%s)
echo "exit=$RC seconds=$((END-START))" | tee -a $D/inputs_assembly11.txt
ls -la $OUT >> $D/inputs_assembly11.txt 2>&1

# `$?` IS WORTHLESS HERE -- Blender 5.2 exits 0 on an uncaught script exception.
# Judge on the token assemble.py prints, and on nothing else.
TOKEN=$(grep -o '>> STAGE RESULT: [A-Z_]*' $D/build_assembly11.log | tail -1)
echo "seconds=$((END-START)) rc=$RC  $TOKEN"
grep -E '^\[ASM\] [a-z]+: ok=' $D/build_assembly11.log || true
if [ "$TOKEN" = ">> STAGE RESULT: ASSEMBLE_OK" ]; then
  echo ">> STAGE RESULT: ASSEMBLY11_BUILT"
else
  echo ">> STAGE RESULT: ASSEMBLY11_FAIL"
fi
