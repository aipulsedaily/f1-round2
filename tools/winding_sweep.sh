#!/usr/bin/env bash
# Winding sweep over every built item blend. See tools/winding_audit.py.
#   tools/winding_sweep.sh witness   # the gate's witness subjects (fast)
#   tools/winding_sweep.sh test      # the full test scenes (slow, big)
set -u
cd /home/zany/f1-round2
MODE="${1:-witness}"
OUT="render/items/_winding/${MODE}"
mkdir -p "$OUT"
if [ "$MODE" = "witness" ]; then
  LIST=$(ls -d render/gate_witness/*/ | sed 's#render/gate_witness/##; s#/##')
else
  LIST=$(ls world/items/*_test.blend | sed 's#world/items/##; s#_test.blend##')
fi
for it in $LIST; do
  if [ "$MODE" = "witness" ]; then B="render/gate_witness/$it/witness.blend";
  else B="world/items/${it}_test.blend"; fi
  [ -f "$B" ] || { echo "SKIP $it (no blend)"; continue; }
  [ -f "$OUT/$it.json" ] && { echo "HAVE $it"; continue; }
  echo "=== $it"
  timeout 3600 blender -b "$B" --factory-startup -P tools/winding_audit.py -- \
      --item "$it" --rays "${RAYS:-400}" --out "$OUT/$it.json" \
      > "$OUT/$it.log" 2>&1 || echo "FAILED $it (see $OUT/$it.log)"
done
echo DONE
