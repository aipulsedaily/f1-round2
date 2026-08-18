#!/usr/bin/env bash
# PHASE 2 — runs when the battery is done.
#
# Two things the battery turned up that CANNOT be attributed to contract 1.2.0
# without a middle measurement, because the last time either probe ran was on
# assembly2 (contract 1.0.1) and contract 1.1.1 landed in between:
#
#   probeD  ARCH_ApronPlatform x SURF_Track+Joint    0 -> 4,624 triangle pairs
#   probeB  D2 step at the glass plane x=15       0.1 mm -> 100.0 mm p50
#
# assembly4.blend (contract 1.1.1) is still on disk, so the middle point is
# measurable rather than arguable. Run the SAME probes on it.
#
# Then the #76 re-gate.
set -u
B=/opt/blender-5.2.0-linux-x64/blender
D=$HOME/f1-round2/render/world/assembly/r2
V=$D/v120

while ! grep -q "BATTERY DONE" $V/battery.log 2>/dev/null; do sleep 30; done
echo "########## PHASE 2 START $(date +%T)"

# This block used to say "preserve the v1.2.0 probe outputs before anything
# re-runs and overwrites them", and copied six files out of the assembly
# root -- a manual workaround for probes that could only write to one fixed
# path. The probes now take --out and the battery gives them one under
# $V, so there is nothing to rescue and nothing to race against.
for f in probeA probeB probeC probeD probeE probeG; do
  if [ -f $D/$f.json ] && [ ! -f $V/${f}_v120.json ]; then
    echo "NOTE: legacy $D/$f.json exists from a pre---out run; copying it"
    cp -f $D/$f.json $V/${f}_v120.json
  fi
done

echo; echo "##### probeG2 on assembly5 (1.2.0) — characterise the apron pair $(date +%T)"
$B -b -noaudio $D/assembly5.blend --factory-startup -P $V/probeG2.py -- $V/probeG2_v120.json 2>&1 | grep -E "^\[G2\]|Error"

echo; echo "##### probeD on assembly4 (1.1.1) $(date +%T)"
$B -b -noaudio $D/assembly4.blend --factory-startup -P $D/probeD.py -- \
   --out $V/probeD_a4_v111.json 2>&1 | grep -E "^\[D\]|Error"

echo; echo "##### probeG2 on assembly4 (1.1.1) $(date +%T)"
$B -b -noaudio $D/assembly4.blend --factory-startup -P $V/probeG2.py -- $V/probeG2_a4_v111.json 2>&1 | grep -E "^\[G2\]|Error"

echo; echo "##### probeG2 on assembly2 (1.0.1) — re-run the baseline today $(date +%T)"
$B -b -noaudio $D/assembly2.blend --factory-startup -P $V/probeG2.py -- $V/probeG2_a2_v101.json 2>&1 | grep -E "^\[G2\]|Error"

echo; echo "##### probeB on assembly4 (1.1.1) — when did the x=15 step appear? $(date +%T)"
$B -b -noaudio $D/assembly4.blend --factory-startup -P $D/probeB.py -- \
   --out $V/probeB_a4_v111.json 2>&1 | grep -E "^\[B\]|Error"

echo; echo "########## PHASE 2 PROBES DONE $(date +%T)"
bash $V/item76_regate.sh
echo "########## PHASE 2 DONE $(date +%T)"
