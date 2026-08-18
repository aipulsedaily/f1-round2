#!/usr/bin/env bash
# ATTRIBUTION: run TODAY'S probeA/B/D/G against the PREVIOUS world (assembly5).
# probeB.py (15:05), probeD.py (14:52) and probeG.py (15:18) were all rewritten
# today by other agents, so a difference between v120's baselines and the v121
# run confounds "the world changed" with "the instrument changed".  Running the
# current instruments on the previous world separates them: whatever differs
# between THIS output and the v121 output is the rebuild, and whatever differs
# between THIS output and the v120 baseline is the instrument.
set -u
B=/opt/blender-5.2.0-linux-x64/blender
D=$HOME/f1-round2/render/world/assembly/r2
V=$D/v121
OLD=$D/assembly5.blend
for p in A B D E G; do
  echo "##### probe$p on assembly5, CURRENT instrument $(date +%T)"
  # --out, not `cp` afterwards. This loop USED to let each probe write its
  # hardcoded name into the assembly root and then copy the file here --
  # which means for the seconds between the two, the assembly root held
  # THIS run's numbers under the filename the v120 collector reads. The
  # copy also silently did nothing (`2>/dev/null`) if the probe had died.
  $B -b -noaudio $OLD --factory-startup -P $D/probe$p.py -- \
     --out $V/probe${p}_a5_current.json > $V/attr_probe$p.log 2>&1
  echo "  exit=$? ($V/probe${p}_a5_current.json)"
done
echo "##### ATTRIBUTION DONE $(date +%T)"
