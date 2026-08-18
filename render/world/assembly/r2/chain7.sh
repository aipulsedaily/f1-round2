#!/usr/bin/env bash
set -u
B=/opt/blender-5.2.0-linux-x64/blender
D=$HOME/f1-round2/render/world/assembly/r2
while pgrep -f "[c]hain6.sh" >/dev/null 2>&1; do sleep 20; done
echo "########## probeI $(date +%T)"
$B -b -noaudio $D/render2.blend --factory-startup -P $D/probeI.py -- --out $D/probeI.json \
   > $D/probeI.log 2>&1
echo "########## probeI exit=$? $(date +%T)"
