#!/usr/bin/env bash
set -u
B=/opt/blender-5.2.0-linux-x64/blender
D=/home/zany/f1-round2/render/world/assembly/r2
S=$D/assembly2.blend
while pgrep -f "probeA.py" >/dev/null 2>&1; do sleep 20; done
for p in probeB probeC probeD; do
  echo "########## $p $(date +%T)"
  $B -b -noaudio "$S" --factory-startup -P $D/$p.py -- --out $D/$p.json \
     > $D/$p.log 2>&1
  echo "########## $p exit=$? $(date +%T)"
done
echo "########## gates $(date +%T)"
bash $D/gates.sh "$S" > $D/gates.log 2>&1
echo "########## CHAIN DONE $(date +%T)"
