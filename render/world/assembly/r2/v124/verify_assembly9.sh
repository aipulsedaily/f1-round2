#!/bin/bash
# READ assembly9 BACK -- the file, not the build log.
#
# Identical in shape to v123/verify_assembly8.sh, deliberately: the point of a
# fingerprint diff is that it is the SAME instrument on both sides, and the
# a7 -> a8 comparison is the one this is being read against.
#
#   1  per-object vertex fingerprint (verts, coord sums, sumsq, bbox, 0.1 um
#      order-independent hash)   ->  v120/vertex_fingerprint.py + v120/fp_diff.py
#      DECLARED expectation: --expect-moved 1.  fp_diff was repaired under
#      R2-111 (it computed `moved`, printed it and never consulted it), so the
#      expectation now has to be stated on the command line and is checked.
#   2  per-material graph fingerprint over EVERY material, node, input default,
#      link and node property -- not the bump census, which is blind to a
#      roughness change from build_architecture.
#   3  the module build reports, field by field.
#   4  the socket audit ARTEFACT arm, with assembly6 as the positive control
#      that MUST FAIL.
#
# Every arm carries its control in the same run.  A "0 moved" from a script
# that cannot report a move is not a result.
set -u
cd $HOME/f1-round2
B=/opt/blender-5.2.0-linux-x64/blender
D=render/world/assembly/r2
V0=$D/v120
V4=$D/v124
W=work/r2148
A6=$D/assembly6.blend
A8=$D/assembly8.blend
A9=$D/assembly9.blend

mkdir -p $W

echo "########## VERIFY assembly9 START $(date +%T)"
ls -l $A8 $A9

echo; echo "=== 0 fp_diff SELFTEST  (7 arms, both directions, must be OK) ==="
python3 $V0/fp_diff.py --selftest

echo; echo "=== 1a vertex fingerprint: assembly9 ==="
$B -b -noaudio $A9 --factory-startup -P $V0/vertex_fingerprint.py -- \
    $HOME/f1-round2/$W/fp_assembly9.json 2>&1 | grep -Ev "^(Blender|\[ALSOFT])" | tail -5

echo; echo "=== 1b fp_diff assembly8 -> assembly9   (DECLARED: exactly 1 moved) ==="
python3 $V0/fp_diff.py $D/v123/fp_assembly8.json $W/fp_assembly9.json --expect-moved 1

echo; echo "=== 1c POSITIVE CONTROL: a5 -> a6, one object known to have moved 3.1885 m ==="
python3 $V0/fp_diff.py $D/v121/fp_assembly5.json $D/v121/fp_assembly6.json --expect-moved 1 | head -8

echo; echo "=== 1d NEGATIVE CONTROL: a8 -> a9 declared as 0 moved -- MUST FAIL (rc 1) ==="
python3 $V0/fp_diff.py $D/v123/fp_assembly8.json $W/fp_assembly9.json --expect-moved 0 \
    | tail -3
echo "   (rc above must be 1; a diff that cannot fail cannot pass)"

echo; echo "=== 1e the one object, field by field ==="
python3 $V4/fp_object_detail.py $D/v123/fp_assembly8.json $W/fp_assembly9.json

echo; echo "=== 2a material graph census: assembly9 ==="
$B -b --factory-startup -P work/r2100/material_graph_census.py -- $A9 \
    $W/matcensus_assembly9.json 2>&1 | grep -E ">>|STAGE"

echo; echo "=== 2b material graph diff assembly8 -> assembly9   (EXPECT 0 of 132) ==="
python3 work/r2100/material_graph_diff.py work/r2100/matcensus_assembly8.json \
    $W/matcensus_assembly9.json

echo; echo "=== 2c CONTROL: a6 -> a7, where exactly 9 DR_* are known to differ ==="
python3 work/r2100/material_graph_diff.py work/r2100/matcensus_assembly6.json \
    work/r2100/matcensus_assembly7.json | head -8

echo; echo "=== 3 module build reports, assembly8 -> assembly9 ==="
python3 work/r2100/build_json_diff.py $D/assembly8_build.json $D/assembly9_build.json

echo; echo "=== 4a socket audit ARTEFACT arm on assembly9  (MUST PASS) ==="
python3 tools/socket_index_audit.py --blend $A9 2>&1 | tail -12

echo; echo "=== 4b POSITIVE CONTROL: the same arm on assembly6  (MUST FAIL, 27) ==="
python3 tools/socket_index_audit.py --blend $A6 2>&1 | tail -6

echo; echo "=== 4c second negative: assembly8  (MUST PASS) ==="
python3 tools/socket_index_audit.py --blend $A8 2>&1 | tail -6

echo "########## VERIFY assembly9 DONE $(date +%T)"
