#!/bin/bash
# READ film14 BACK, from the saved blend, and put film13 through the SAME
# instruments on the way past.  Same harness as work/r2127/verify_film13.sh.
set -u
cd /home/zany/f1-round2
B=/opt/blender-5.2.0-linux-x64/blender
W=work/r2148

echo "########## VERIFY film14 START $(date +%T)"
ls -l render/film13.blend render/film14.blend

for f in film14 film13; do
  echo; echo "=== measure_film_scene.py on $f ==="
  $B -b render/$f.blend --factory-startup \
      -P work/lighting/measure_film_scene.py -- --json $W/measured_${f}.json \
      > $W/measure_${f}.log 2>&1
  echo "  rc=$?  ->  $W/measured_${f}.json"
  echo "=== measure_film_extra.py on $f  (the identity, RECOMPUTED from the stamps) ==="
  $B -b render/$f.blend --factory-startup \
      -P work/r2100/measure_film_extra.py -- $W/extra_${f}.json \
      > $W/extra_${f}.log 2>&1
  echo "  rc=$?"
done

echo; echo "=== readback diff film13 -> film14, field by field ==="
python3 work/r2127/readback_diff.py $W/measured_film13.json $W/measured_film14.json

echo; echo "=== the levelling identity, recomputed from film14's OWN _sl_base props ==="
python3 -c "
import json,sys
d=json.load(open('$W/extra_film14.json'))
for k in ('scene_mark','lift_multiplier','n_lamp_stamps','base_watts_from_stamps',
          'levelled_watts_from_stamps','identity_base_x_lift',
          'interior_lamp_watts_measured','identity_residual_w',
          'worst_per_lamp_ratio','assert_levelled'):
    print('  %-32s %s' % (k, json.dumps(d.get(k))))
"

echo; echo "=== socket audit ARTEFACT arm on film14  (MUST PASS) ==="
python3 tools/socket_index_audit.py --blend render/film14.blend 2>&1 | tail -10

echo; echo "=== POSITIVE CONTROL: the same arm on film10  (MUST FAIL, 27) ==="
python3 tools/socket_index_audit.py --blend render/film10.blend 2>&1 | tail -5

echo; echo "=== SECOND NEGATIVE: the same arm on film13  (MUST PASS) ==="
python3 tools/socket_index_audit.py --blend render/film13.blend 2>&1 | tail -5

echo "########## VERIFY film14 DONE $(date +%T)"
