#!/bin/bash
# READ assembly8 BACK. Not its build log -- the file it produced.
#
# The comparison is the one SHIPPING.md used for assembly6 -> assembly7, run
# again unchanged, because the point of a fingerprint diff is that it is the
# SAME instrument on both sides:
#
#   1  per-object vertex fingerprint (verts, coord sums, sumsq, bbox, 0.1 um
#      order-independent hash)  ->  v120/vertex_fingerprint.py, v120/fp_diff.py
#   2  per-material graph fingerprint over EVERY material, not just the bump
#      census -- build_architecture and build_terrain both moved since
#      assembly7, so "only the dressing changed" has to be measured
#   3  the module build reports, field by field
#   4  the socket audit's ARTEFACT arm, with assembly6 as the positive control
#      that must FAIL (a pass on assembly8 means nothing unless the same
#      instrument fails a blend known to be broken)
set -u
cd $HOME/f1-round2
B=/opt/blender-5.2.0-linux-x64/blender
D=render/world/assembly/r2
V0=$D/v120
W=work/r2100
A7=$D/assembly7.blend
A8=$D/assembly8.blend
A6=$D/assembly6.blend

echo "########## VERIFY assembly8 START $(date +%T)"
ls -l $A7 $A8

echo; echo "=== 1a vertex fingerprint: assembly8 ==="
$B -b -noaudio $A8 --factory-startup -P $V0/vertex_fingerprint.py -- \
    $HOME/f1-round2/$W/fp_assembly8.json 2>&1 | grep -Ev "^(Blender|\[ALSOFT])" | tail -5

echo; echo "=== 1b fp_diff assembly7 -> assembly8   (EXPECT: 0 objects moved) ==="
python3 $V0/fp_diff.py $D/v122/fp_assembly7.json $W/fp_assembly8.json

# A fingerprint diff that reports "0 moved" is worthless unless the same
# script reports a real move when there is one. v121's assembly5 -> assembly6
# pair is the known-positive: exactly ONE object, BR_Transit_NorthWall, 3.19 m.
echo; echo "=== 1c POSITIVE CONTROL: a5 -> a6, where exactly 1 object is known to have moved ==="
python3 $V0/fp_diff.py $D/v121/fp_assembly5.json $D/v121/fp_assembly6.json | head -6

echo; echo "=== 2a material graph census: assembly8 ==="
$B -b --factory-startup -P $W/material_graph_census.py -- $A8 $W/matcensus_assembly8.json 2>&1 | grep -E ">>|STAGE"

echo; echo "=== 2b material graph diff assembly7 -> assembly8 ==="
python3 $W/material_graph_diff.py $W/matcensus_assembly7.json $W/matcensus_assembly8.json

echo; echo "=== 2c CONTROL: assembly6 -> assembly7, where SHIPPING.md says exactly 9 DR_* moved ==="
python3 $W/material_graph_diff.py $W/matcensus_assembly6.json $W/matcensus_assembly7.json | head -8

echo; echo "=== 3 module build reports, assembly7 -> assembly8 ==="
python3 $W/build_json_diff.py $D/assembly7_build.json $D/assembly8_build.json

echo; echo "=== 4a socket audit ARTEFACT arm on assembly8  (MUST PASS) ==="
python3 tools/socket_index_audit.py --blend $A8 2>&1 | tail -12

echo; echo "=== 4b POSITIVE CONTROL: the same arm on assembly6  (MUST FAIL) ==="
python3 tools/socket_index_audit.py --blend $A6 2>&1 | tail -6

echo; echo "=== 4c second negative: assembly7  (MUST PASS) ==="
python3 tools/socket_index_audit.py --blend $A7 2>&1 | tail -6

echo "########## VERIFY assembly8 DONE $(date +%T)"
