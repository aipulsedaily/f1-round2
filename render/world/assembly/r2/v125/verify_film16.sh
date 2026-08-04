#!/bin/bash
# READ film16 BACK, from the saved blend, and put film14 through the SAME
# instruments on the way past.  Same harness as v124/verify_film14.sh.
#
# THE BAR film16 MUST MEET OR BEAT (film14's read-back figures):
#     interior lamp load   46,203.313 W   -- from showroom_lighting.measure(),
#                                            NOT a hand-rolled probe.  A
#                                            hand-rolled one gave 46,319 W by
#                                            counting a non-interior lamp.
#     _sl_base stamps      23
#     scene_mark           3.628          -- scene key `showroom_lighting_stops`
#     assert_levelled      PASS
#     camera ONER clip     0.05 / 200000
#     socket_index_audit   PASS, against film10's standing 27-finding FAIL
set -u
cd /home/zany/f1-round2
B=/opt/blender-5.2.0-linux-x64/blender
W=work/r2500

echo "########## VERIFY film16 START $(date +%T)"
ls -l render/film14.blend render/film16.blend

for f in film16 film14; do
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

echo; echo "=== readback diff film14 -> film16, field by field ==="
python3 work/r2127/readback_diff.py $W/measured_film14.json $W/measured_film16.json

echo; echo "=== the levelling identity, recomputed from film16's OWN _sl_base props ==="
python3 -c "
import json
d=json.load(open('$W/extra_film16.json'))
for k in ('scene_mark','lift_multiplier','n_lamp_stamps','base_watts_from_stamps',
          'levelled_watts_from_stamps','identity_base_x_lift',
          'interior_lamp_watts_measured','identity_residual_w',
          'worst_per_lamp_ratio','assert_levelled'):
    print('  %-32s %s' % (k, json.dumps(d.get(k))))
"

echo; echo "=== THE BAR, judged.  film16 must MEET OR BEAT film14. ==="
python3 -c "
import json, sys
a=json.load(open('$W/extra_film14.json')); b=json.load(open('$W/extra_film16.json'))
ok=True
def chk(name, got, want, tol=0.0):
    global ok
    good = (abs(float(got)-float(want)) <= tol) if isinstance(want,(int,float)) else (got==want)
    ok = ok and good
    print('  %-34s want %-14s got %-14s %s' % (name, want, got, 'OK' if good else 'FAIL'))
chk('interior_lamp_watts', b.get('interior_lamp_watts_measured'), 46203.313, 1e-3)
chk('n_lamp_stamps',       b.get('n_lamp_stamps'), 23)
chk('scene_mark',          b.get('scene_mark'), 3.628, 1e-3)
chk('assert_levelled',     b.get('assert_levelled'), 'PASS')
print('  (film14 read on the same instrument: %s W, %s stamps, mark %s)'
      % (a.get('interior_lamp_watts_measured'), a.get('n_lamp_stamps'), a.get('scene_mark')))
print('>> STAGE RESULT: %s' % ('FILM16_BAR_MET' if ok else 'FILM16_BAR_MISSED'))
"

echo; echo "=== the ONER: one camera, clip 0.05/200000, 2978 frames, 24 fps, 3840x2160 ==="
$B -b render/film16.blend --factory-startup --python-expr "
import bpy
s = bpy.context.scene
cams = [o for o in bpy.data.objects if o.type == 'CAMERA']
r = s.render
ok = True
def chk(n, got, want):
    global ok
    g = (got == want); ok = ok and g
    print('   %-22s want %-12s got %-12s %s' % (n, want, got, 'OK' if g else 'FAIL'))
chk('camera objects', len(cams), 1)
c = cams[0].data if cams else None
chk('clip_start', round(c.clip_start, 6) if c else None, 0.05)
chk('clip_end',   round(c.clip_end, 1) if c else None, 200000.0)
chk('resolution', (r.resolution_x, r.resolution_y), (3840, 2160))
chk('res_percent', r.resolution_percentage, 100)
chk('fps', s.render.fps, 24)
chk('frame_start', s.frame_start, 1)
chk('frame_end', s.frame_end, 2978)
vs = s.view_settings
chk('view_transform', vs.view_transform, 'AgX')
chk('look', vs.look, 'None')
chk('exposure', round(vs.exposure, 3), -3.628)
print('>> STAGE RESULT: %s' % ('ONER_OK' if ok else 'ONER_FAIL'))
" 2>&1 | grep -E "^   |STAGE RESULT"

echo; echo "=== THE DRIVER AND THE ITEMS ARE IN THE FILM ==="
$B -b render/film16.blend --factory-startup --python-expr "
import bpy
pref = {'DRV_': 0, 'CFP_': 0, 'CRF_': 0, 'TS_': 0, 'SPECX_': 0}
for o in bpy.data.objects:
    for p in pref:
        if o.name.startswith(p):
            pref[p] += 1
for p, n in sorted(pref.items()):
    print('   %-8s %6d  %s' % (p, n, 'PRESENT' if n else 'ABSENT'))
drv = [o.name for o in bpy.data.objects if o.name.startswith('DRV_')][:6]
print('   driver objects: %s' % drv)
ok = all(pref[p] for p in ('CFP_','CRF_','TS_','SPECX_')) and pref['DRV_'] > 0
print('>> STAGE RESULT: %s' % ('FILM16_POPULATED' if ok else 'FILM16_MISSING_POPULATION'))
" 2>&1 | grep -E "^   |STAGE RESULT"

echo; echo "=== socket audit ARTEFACT arm on film16  (MUST PASS) ==="
python3 tools/socket_index_audit.py --blend render/film16.blend 2>&1 | tail -10

echo; echo "=== POSITIVE CONTROL: the same arm on film10  (MUST FAIL, 27) ==="
python3 tools/socket_index_audit.py --blend render/film10.blend 2>&1 | tail -5

echo; echo "=== SECOND NEGATIVE: the same arm on film14  (MUST PASS) ==="
python3 tools/socket_index_audit.py --blend render/film14.blend 2>&1 | tail -5

echo "########## VERIFY film16 DONE $(date +%T)"
