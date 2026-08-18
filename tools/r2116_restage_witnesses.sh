#!/usr/bin/env bash
# R2-116 -- restage the witness blend of every item whose test blend was rebuilt.
#
# WHY.  `render/items/_relief/<item>.json` is measured from
# `render/gate_witness/<item>/witness.blend`, which `item_gate` stages from
# `world/items/<item>_test.blend`.  Rebuilding the test blend makes the witness
# the stale link in that chain, and re-running the relief audit against an old
# witness would republish a number about an artefact that no longer exists --
# the same mistake, one level down, as the one this whole task is unpicking.
#
# So the order is: rebuild the test blend, RESTAGE the witness from it, then
# re-run the relief audit.  `tools/relief_sweep.sh` picks the third step up on
# its own, because it re-runs any report older than its witness.
#
# `--stage-only` writes the witness blend + spec and stops.  Its own help says
# the result is then REJECTED, because the render-based checks did not run --
# that is correct and it is NOT a verdict about the item.  This script reads
# the witness FILE, not the exit status: Blender 5.2 exits 0 on an uncaught
# script exception (R2-108), and `--stage-only`'s rejection is not a failure.
#
# spectator_seated is deliberately NOT in the default list.  `item_gate` derives
# the witness directory from the ITEM ID rather than the module name, and the
# module `spectator_crowd` serves the same item id -- staging one destroys the
# other's witness.  R2-061 avoided that collision on purpose; pass it by name
# and back the directory up first if you really want it.
set -u
ROOT=$HOME/f1-round2
BL=/opt/blender-5.2.0-linux-x64/blender
W=$ROOT/work/r2116
mkdir -p "$W/logs"
cd "$ROOT"

ok=0; bad=0
for m in "$@"; do
  B=$ROOT/world/items/${m}_test.blend
  WB=$ROOT/render/gate_witness/$m/witness.blend
  [ -f "$B" ] || { echo "SKIP $m -- no test blend"; continue; }
  before=$( [ -f "$WB" ] && sha256sum "$WB" | cut -c1-16 || echo none )
  timeout 7200 "$BL" -b "$B" --factory-startup -P tools/item_gate.py -- \
      --item "$m" --stage-only \
      --out "$W/logs/${m}_stage.json" > "$W/logs/${m}_stage.log" 2>&1
  after=$( [ -f "$WB" ] && sha256sum "$WB" | cut -c1-16 || echo none )
  if [ "$after" != "none" ] && [ "$after" != "$before" ]; then
    echo "$m RESTAGED  witness $before -> $after"
    ok=$((ok + 1))
  else
    echo "$m WITNESS DID NOT MOVE ($before -> $after) -- relief numbers for"
    echo "   this item stay attached to the OLD witness and are NOT MEASURED"
    echo "   against the rebuild.  Last lines of its log:"
    tail -4 "$W/logs/${m}_stage.log" | sed 's/^/     /'
    bad=$((bad + 1))
  fi
done
echo
echo "restaged $ok   did not restage $bad"
if [ "$bad" -gt 0 ]; then echo ">> STAGE RESULT: RESTAGE_INCOMPLETE"; exit 1; fi
if [ "$ok" -eq 0 ]; then echo ">> STAGE RESULT: RESTAGE_VACUOUS"; exit 3; fi
echo ">> STAGE RESULT: RESTAGE_OK"
