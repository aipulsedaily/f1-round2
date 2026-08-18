#!/usr/bin/env bash
set -u
B=/opt/blender-5.2.0-linux-x64/blender
D=$HOME/f1-round2/render/world/assembly/r2
S=$D/assembly2.blend
while pgrep -f "[c]hain3.sh" >/dev/null 2>&1; do sleep 20; done
echo "########## probeG $(date +%T)"
$B -b -noaudio "$S" --factory-startup -P $D/probeG.py -- --out $D/probeG.json \
   > $D/probeG.log 2>&1
echo "########## probeG exit=$? $(date +%T)"
