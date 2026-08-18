#!/bin/bash
# Build assembly9 from source -- R2-148.  Same script shape as
# work/r2100/build_assembly8.sh, so the two builds are comparable.
# The ONLY source difference from assembly8 is 10442cd (build_architecture,
# the pit-exit apron cut) and 29105eb (world_contract selftest text only).
set -u
cd $HOME/f1-round2
D=work/r2148
mkdir -p $D
OUT=$HOME/f1-round2/render/world/assembly/r2/assembly9.blend

others () {
  ps -eo rss,args --no-headers \
    | grep '/opt/blender-5.2.0-linux-x64/blender -b' \
    | grep -v assemble.py | grep -v '[g]rep' \
    | awk '{s+=$1} END {print int(s/1024)}'
}

for i in $(seq 1 30); do
  M=$(others)
  echo "$(date +%T) other blender RSS = ${M} MB (wait ${i}/30)" >> $D/wait.log
  [ "${M:-0}" -lt 3000 ] && break
  sleep 20
done
echo "$(date +%T) STARTING BUILD, other blender RSS = $(others) MB" >> $D/wait.log

{
  echo "=== INPUTS, hashed at $(date -Is) ==="
  sha256sum world/world_contract.py world/build_surface.py world/build_barriers.py \
            world/build_architecture.py world/build_terrain.py world/build_dressing.py \
            render/world/assembly/r2/assemble.py telemetry/telemetry.csv
  ls -la --time-style=+%F_%T world/build_*.py world/world_contract.py
  git -C $HOME/f1-round2 rev-parse HEAD
  git -C $HOME/f1-round2 status --short
} > $D/inputs_assembly9.txt 2>&1

START=$(date +%s)
/opt/blender-5.2.0-linux-x64/blender -b -noaudio --factory-startup \
    -P render/world/assembly/r2/assemble.py -- --out=$OUT \
    > $D/build_assembly9.log 2>&1
RC=$?
END=$(date +%s)
echo "exit=$RC seconds=$((END-START))" | tee -a $D/inputs_assembly9.txt
ls -la $OUT >> $D/inputs_assembly9.txt 2>&1
echo "BUILD DONE rc=$RC in $((END-START)) s"
