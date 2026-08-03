#!/usr/bin/env bash
set -u
B=/opt/blender-5.2.0-linux-x64/blender
D=/home/zany/f1-round2/render/world/assembly/r2
S=$D/assembly2.blend
while pgrep -f "chain.sh" >/dev/null 2>&1; do sleep 20; done
echo "########## probeE $(date +%T)"
$B -b -noaudio "$S" --factory-startup -P $D/probeE.py -- --out $D/probeE.json \
   > $D/probeE.log 2>&1
echo "########## probeE exit=$? $(date +%T)"
