#!/bin/bash
# Every camera gate on film14, each with BOTH controls, and the path self-null
# run FIRST so a clean diff means something (R2-103).
set -u
cd $HOME/f1-round2
W=work/r2148
P=render/film14_path.json

echo "########## CAMERA GATES ON $P  $(date +%T)"

echo; echo "=== 0 PATH SELF-NULL: film14 against ITSELF, both instruments ==="
echo "--- the SHIPPED wide reading (2*acos|dot|), which has a 0.162 deg floor:"
python3 render/world/assembly/r2/v123/path_diff.py $P $P docs/beat_sheet.json 2>&1 | head -6
echo "--- the STRICT componentwise reading (sign-normalised), which has none:"
python3 work/r2127/path_diff_strict.py $P $P docs/beat_sheet.json 2>&1 | tail -8

echo; echo "=== 1 path diff film13 -> film14, STRICT ==="
python3 work/r2127/path_diff_strict.py render/film13_path.json $P docs/beat_sheet.json

echo; echo "=== 2 horizon_gate --selftest (7/7, incl. P4 the 170-deg synthetic) ==="
python3 tools/horizon_gate.py --selftest 2>&1 | tail -10

echo; echo "=== 3 horizon_gate --census ==="
python3 tools/horizon_gate.py --census 2>&1 | tail -8

echo; echo "=== 4 horizon_gate ARTEFACT arm: film14 f2600-2714 (MUST PASS) ==="
python3 tools/horizon_gate.py --path $P --lo 2600 --hi 2714 2>&1 | tail -12

echo; echo "=== 5 horizon_gate POSITIVE CONTROL: docs/horizon_pre_R2112_path.json (MUST FAIL) ==="
python3 tools/horizon_gate.py --path docs/horizon_pre_R2112_path.json --lo 2600 --hi 2714 2>&1 | tail -10

echo; echo "=== 6 seam_gate --selftest, DEFAULT --path (world/camera_rig_path.json) ==="
python3 tools/seam_gate.py --selftest 2>&1 | tail -6

echo; echo "=== 7 seam_gate ARTEFACT arm on film14 ==="
python3 tools/seam_gate.py --path $P 2>&1 | tail -22

echo; echo "=== 8 seam_gate --census ==="
python3 tools/seam_gate.py --path $P --census 2>&1 | tail -6

echo; echo "=== 9 campath_gate on film14 ==="
python3 tools/continuity_gate.py --campath $P --report $W/campath_film14.json 2>&1 | tail -20

echo; echo "=== 10 campath_gate on the stored pre-R2112 rolled path -- AND IT PASSES ==="
# THIS IS NOT A CONTROL FOR THIS GATE, and running it is how that was found out.
# `docs/horizon_pre_R2112_path.json` is the path with 28 fully-inverted frames
# and -122.93 deg of roll in it. horizon_gate FAILS it, 32 FAIL frames.
# campath_gate PASSES it, 0 FAIL, with the SAME five advisories film14 gets --
# because campath_gate measures speed, rotation RATE and path kink, and has no
# roll or up-vector term at all. A gate whose "positive control" returns the
# same verdict as the artefact has asserted nothing about that artefact.
python3 tools/continuity_gate.py --campath docs/horizon_pre_R2112_path.json \
    --report $W/campath_ctl_rolled.json 2>&1 | tail -4

echo; echo "=== 11 campath_gate TRUE POSITIVE CONTROL A: the pre-R2064 seam path (MUST FAIL) ==="
python3 tools/continuity_gate.py --campath docs/seam_pre_R2064_path.json \
    --report $W/campath_ctl_seam.json 2>&1 | tail -3

echo; echo "=== 12 campath_gate TRUE POSITIVE CONTROL B: film9, the broken generation (MUST FAIL) ==="
python3 tools/continuity_gate.py --campath render/film9_path.json \
    --report $W/campath_ctl_film9.json 2>&1 | tail -3

echo "########## GATES DONE $(date +%T)"
