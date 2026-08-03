#!/usr/bin/env bash
# v1.1.1 verification chain: re-measure BEFORE with the new instruments, then AFTER.
set -u
B=/opt/blender-5.2.0-linux-x64/blender
D=/home/zany/f1-round2/render/world/assembly/r2
R2=/home/zany/f1-round2
# wait for the assembly to finish saving
while ! grep -q '"blend_mb"' $D/assemble4.log 2>/dev/null; do sleep 20; done
sleep 10
echo "########## probe BEFORE (assembly3, contract 1.1.0) $(date +%T)"
$B -b $D/assembly3.blend --factory-startup -P $D/probe_pitexit.py -- probe_pitexit_before2.json > $D/probe_before2.log 2>&1
echo "########## probe AFTER (assembly4, contract 1.1.1) $(date +%T)"
$B -b $D/assembly4.blend --factory-startup -P $D/probe_pitexit.py -- probe_pitexit_after.json > $D/probe_after.log 2>&1
echo "########## placement gate AFTER $(date +%T)"
cd $R2 && $B -b $D/assembly4.blend --factory-startup -P tools/placement_gate.py -- --out docs/placement_after_46.json > $D/placement_after_46.log 2>&1
echo "########## render setup $(date +%T)"
$B -b -noaudio $D/assembly4.blend --factory-startup -P $D/render_setup3.py -- --out=$D/render3.blend > $D/render_setup3.log 2>&1
echo "########## CHAIN DONE $(date +%T)"
