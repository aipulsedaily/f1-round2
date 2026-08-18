#!/usr/bin/env bash
# #76 — the three modules whose collapsed hash was repaired on 2026-08-02
# (avalanche 0.2718 -> 0.4993, re-measured today as 0.4993 against the audit
# tool's own known-bad 0.2721 / murmur3 0.5005 controls).
#
# The hash drives per-instance variation, so every built vertex in these three
# moved and their existing gate.json describes geometry that no longer exists.
#
# THE CONTROL THAT MAKES THIS READABLE.  The gate ITSELF was rewritten since
# those reports were written (#59/#63: 5 checks -> 8, and it renders now;
# 28/28 accepted became 7/28).  So a bare "re-gate" would confound the hash
# repair with the gate rewrite and could not attribute either.  Both scenes are
# therefore gated with TODAY's gate:
#
#     OLD scene = the *_test.blend on disk from 2026-07-29, PRE-repair
#     NEW scene = rebuilt now from the module,             POST-repair
#
# Same gate, same harness, same staging: the difference between the two IS the
# hash repair.
set -u
B=/opt/blender-5.2.0-linux-x64/blender
R2=$HOME/f1-round2
V=$R2/render/world/assembly/r2/v120
I=$R2/world/items

items=("grandstand_riser_unit W_Item_GrandstandRiserUnit"
       "kerb_precast_unit     W_Item_KerbPrecastUnit"
       "team_truck_trailer    W_Item_TeamTruckTrailer")

for row in "${items[@]}"; do
  set -- $row; name=$1; coll=$2
  echo "############################################################ $name $(date +%T)"

  echo "### fingerprint OLD (pre-repair) $(date +%T)"
  $B -b $I/${name}_test.blend --factory-startup -P $V/vertex_fingerprint.py -- \
     $V/fp_${name}_old.json 2>&1 | grep -E "^\[VF\]|Error"

  echo "### rebuild test scene from the repaired module $(date +%T)"
  $B -b --factory-startup -P $I/${name}.py -- --test \
     --save $V/${name}_test_v76.blend 2>&1 | tail -6

  echo "### fingerprint NEW (post-repair) $(date +%T)"
  $B -b $V/${name}_test_v76.blend --factory-startup -P $V/vertex_fingerprint.py -- \
     $V/fp_${name}_new.json 2>&1 | grep -E "^\[VF\]|Error"

  echo "### vertex diff $(date +%T)"
  python3 $V/fp_diff.py $V/fp_${name}_old.json $V/fp_${name}_new.json \
          > $V/fp_${name}_diff.txt 2>&1
  cat $V/fp_${name}_diff.txt

  # The brief's named risk: variation INCREASES after the repair, so watch for a
  # module that now scatters past its own placement gate -- and for
  # kerb_precast (KPU_, an EDGE_FAMILY) breaching half-width at the track edge.
  echo "### placement_gate on the OLD scene $(date +%T)"
  $B -b $I/${name}_test.blend --factory-startup -P $R2/tools/placement_gate.py -- \
     --out $V/place_${name}_oldhash.json 2>&1 | grep -E "^>>|^  " | tail -20
  echo "### placement_gate on the NEW scene $(date +%T)"
  $B -b $V/${name}_test_v76.blend --factory-startup -P $R2/tools/placement_gate.py -- \
     --out $V/place_${name}_newhash.json 2>&1 | grep -E "^>>|^  " | tail -20

  echo "### item_gate on the OLD scene, TODAY's gate $(date +%T)"
  $B -b $I/${name}_test.blend --factory-startup -P $R2/tools/item_gate.py -- \
     --item $name --collection $coll \
     --out $V/gate_${name}_oldhash.json \
     --witness-dir $V/witness_${name}_oldhash 2>&1 | tail -45

  echo "### item_gate on the NEW scene, TODAY's gate $(date +%T)"
  $B -b $V/${name}_test_v76.blend --factory-startup -P $R2/tools/item_gate.py -- \
     --item $name --collection $coll \
     --out $V/gate_${name}_newhash.json \
     --witness-dir $V/witness_${name}_newhash 2>&1 | tail -45
done
echo "############ #76 RE-GATE DONE $(date +%T)"
