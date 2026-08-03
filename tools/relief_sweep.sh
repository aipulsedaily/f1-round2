#!/usr/bin/env bash
# Relief sweep over every built item blend. See tools/relief_audit.py.
set -u
cd /home/zany/f1-round2
OUT="render/items/_relief"
mkdir -p "$OUT"
for it in $(ls -d render/gate_witness/*/ | sed 's#render/gate_witness/##; s#/##'); do
  B="render/gate_witness/$it/witness.blend"
  [ -f "$B" ] || { echo "SKIP $it"; continue; }
  [ -f "$OUT/$it.json" ] && { echo "HAVE $it"; continue; }
  echo "=== $it"
  timeout 2400 blender -b "$B" --factory-startup -P tools/relief_audit.py -- \
      --item "$it" --out "$OUT/$it.json" > "$OUT/$it.log" 2>&1 \
      || echo "FAILED $it"
done
echo DONE
