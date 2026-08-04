#!/bin/bash
# READ assembly10 BACK -- the file, not the build log.
#
# Identical in shape to v124/verify_assembly9.sh, deliberately: a fingerprint
# diff is only evidence when it is the SAME instrument on both sides.
#
# UNLIKE every previous promotion, this one is NOT expected to move one object.
# It is the batched rebuild -- six landed source changes plus four item rows
# going HOLD -> PLACE -- so the declared expectation is "many", and the
# interesting arms are (a) that the items actually ARRIVED, which has never
# happened before (task #121), and (b) that the things NOT touched did not move.
set -u
cd /home/zany/f1-round2
B=/opt/blender-5.2.0-linux-x64/blender
D=render/world/assembly/r2
V0=$D/v120
V4=$D/v124
W=work/r2500
A6=$D/assembly6.blend
A9=$D/assembly9.blend
A10=$D/assembly10.blend

mkdir -p $W

echo "########## VERIFY assembly10 START $(date +%T)"
ls -l $A9 $A10

echo; echo "=== 0 fp_diff SELFTEST  (must be OK before any arm is believed) ==="
python3 $V0/fp_diff.py --selftest 2>&1 | tail -6

echo; echo "=== 1a vertex fingerprint: assembly10 ==="
$B -b -noaudio $A10 --factory-startup -P $V0/vertex_fingerprint.py -- \
    /home/zany/f1-round2/$W/fp_assembly10.json 2>&1 \
    | grep -Ev "^(Blender|\[ALSOFT])" | tail -5

echo; echo "=== 1b fp_diff assembly9 -> assembly10  (the batched rebuild) ==="
python3 $V0/fp_diff.py $W/fp_assembly9_ref.json $W/fp_assembly10.json | head -40

echo; echo "=== 1c NEGATIVE CONTROL: the same diff declared as 0 moved -- MUST FAIL ==="
python3 $V0/fp_diff.py $W/fp_assembly9_ref.json $W/fp_assembly10.json --expect-moved 0 \
    | tail -3
echo "   rc above must be 1: a diff that cannot fail cannot pass"

echo; echo "=== 1d POSITIVE CONTROL: a5 -> a6, one object known to have moved 3.1885 m ==="
python3 $V0/fp_diff.py $D/v121/fp_assembly5.json $D/v121/fp_assembly6.json \
    --expect-moved 1 | head -8

echo; echo "=== 2 module build reports, assembly9 -> assembly10 ==="
python3 work/r2100/build_json_diff.py $D/assembly9_build.json $D/assembly10_build.json

echo; echo "=== 3 THE ITEMS ARRIVED?  task #121 -- nothing in world/items/ has"
echo    "    ever reached a frame.  Counted off the SAVED BLEND, per prefix. ==="
$B -b -noaudio $A10 --factory-startup --python-expr "
import bpy, json
want = {'CFP_': 676, 'CRF_': 120, 'TS_': 10, 'SPECX_': 900}
got = {}
for o in bpy.data.objects:
    for p in want:
        if o.name.startswith(p):
            got[p] = got.get(p, 0) + 1
ok = True
for p, n in sorted(want.items()):
    g = got.get(p, 0)
    print('   %-8s expect %5d  got %5d  %s' % (p, n, g, 'OK' if g else 'ABSENT'))
    if not g:
        ok = False
colls = [c.name for c in bpy.data.collections if c.name.startswith(('W_Item_', 'ITEM_'))]
print('   item collections in the blend: %s' % colls)
print('>> STAGE RESULT: %s' % ('ITEMS_PRESENT' if ok else 'ITEMS_ABSENT'))
" 2>&1 | grep -E "^   |STAGE RESULT"

echo; echo "=== 4a socket audit ARTEFACT arm on assembly10  (MUST PASS) ==="
python3 tools/socket_index_audit.py --blend $A10 2>&1 | tail -12

echo; echo "=== 4b POSITIVE CONTROL: the same arm on assembly6  (MUST FAIL, 27) ==="
python3 tools/socket_index_audit.py --blend $A6 2>&1 | tail -6

echo; echo "=== 4c second negative: assembly9  (MUST PASS) ==="
python3 tools/socket_index_audit.py --blend $A9 2>&1 | tail -6

echo "########## VERIFY assembly10 DONE $(date +%T)"
