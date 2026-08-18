#!/bin/bash
# READ film19_breach BACK from the saved blend and judge it against the bar in
# docs/NEXT-REBUILD.md.  Same instruments as v125/verify_film16.sh so the two
# generations are comparable line for line.  R2-1701.
#
#   usage: verify_film19.sh [blend]     default render/film19_breach.blend
#
# THE BAR:
#     interior lamp load   46,203.313 W   from showroom_lighting.measure(), NOT
#                                         a hand-rolled probe -- a hand-rolled
#                                         one read 46,319 W by counting a lamp
#                                         that is not interior
#     _sl_base stamps      23             scene key showroom_lighting_stops
#     scene_mark           3.628          assert_levelled PASS, UNCONDITIONALLY
#     ONER clip            0.05 / 200000  3840x2160, 24 fps, 1..2978,
#                                         AgX, look None, exposure -3.628
#     socket audit         PASS, against film10's standing 27-finding FAIL
#
# WHY film10 IS STILL IN THIS SCRIPT.  It is the NEGATIVE CONTROL.  An audit that
# has never failed is not evidence that anything passed, and film10 is the file
# on which this one is known to report 27 findings.  Keep it.  If film10 ever
# comes back PASS the instrument is broken, and every PASS above it is vacuous.
set -u
cd $HOME/f1-round2
FILM=${1:-render/film19_breach.blend}
NAME=$(basename "$FILM" .blend)
B=/opt/blender-5.2.0-linux-x64/blender
W=work/r21701
mkdir -p $W

[ -s "$FILM" ] || { echo ">> STAGE RESULT: VERIFY19_FAIL (no $FILM)"; exit 2; }

waitmem () {
  for i in $(seq 1 960); do
    A=$(free -g | awk '/^Mem:/{print $7}')
    [ "$A" -ge 5 ] && { echo "[gate] ${A} GB available, starting $1"; return 0; }
    [ $((i % 10)) -eq 1 ] && echo "[gate] $1 waiting: ${A} GB available (need 5)"
    sleep 30
  done
  echo "[gate] TIMEOUT before $1"; return 1
}

echo "########## VERIFY $NAME  $(date -Is)"
ls -l "$FILM"

waitmem measure_film_scene || exit 90
$B -b "$FILM" --factory-startup -noaudio \
    -P work/lighting/measure_film_scene.py -- --json $W/measured_${NAME}.json \
    > $W/measure_${NAME}.log 2>&1
echo "  measure_film_scene rc=$?  (exit status is NOT the evidence)"

waitmem measure_film_extra || exit 90
$B -b "$FILM" --factory-startup -noaudio \
    -P work/r2100/measure_film_extra.py -- $W/extra_${NAME}.json \
    > $W/extra_${NAME}.log 2>&1
echo "  measure_film_extra rc=$?"

echo
echo "=== the levelling identity, recomputed from ${NAME}'s OWN _sl_base props ==="
python3 -c "
import json
d=json.load(open('$W/extra_${NAME}.json'))
for k in ('scene_mark','lift_multiplier','n_lamp_stamps','base_watts_from_stamps',
          'levelled_watts_from_stamps','identity_base_x_lift',
          'interior_lamp_watts_measured','identity_residual_w',
          'worst_per_lamp_ratio','assert_levelled'):
    print('  %-32s %s' % (k, json.dumps(d.get(k))))
"

echo
echo "=== THE BAR, judged ==="
python3 -c "
import json, sys
b=json.load(open('$W/extra_${NAME}.json'))
try:
    m=json.load(open('$W/measured_${NAME}.json'))
except Exception:
    m={}
ok=True
def chk(name, got, want, tol=0.0):
    global ok
    if isinstance(want,(int,float)) and isinstance(got,(int,float)):
        good = abs(float(got)-float(want)) <= tol
    else:
        good = (got==want)
    ok = ok and good
    print('  %-34s want %-16s got %-16s %s' % (name, want, got, 'OK' if good else 'FAIL'))
chk('interior_lamp_watts', b.get('interior_lamp_watts_measured'), 46203.313, 1e-3)
chk('n_lamp_stamps',       b.get('n_lamp_stamps'), 23)
chk('scene_mark',          b.get('scene_mark'), 3.628, 1e-9)
chk('assert_levelled',     b.get('assert_levelled'), 'PASS')
for k,want in (('resolution_x',3840),('resolution_y',2160),('fps',24),
               ('frame_start',1),('frame_end',2978),
               ('view_transform','AgX'),('look','None'),('exposure',-3.628),
               ('clip_start',0.05),('clip_end',200000.0),('camera','ONER')):
    if k in m: chk(k, m.get(k), want, 1e-6 if isinstance(want,float) else 0)
    else:      print('  %-34s NOT REPORTED by measure_film_scene' % k)
print()
print('>> STAGE RESULT: %s' % ('VERIFY19_BAR_PASS' if ok else 'VERIFY19_BAR_FAIL'))
sys.exit(0 if ok else 1)
"
BARRC=$?

echo
echo "=== socket_index_audit: $NAME must PASS, film10 must still FAIL 27 ==="
for f in "$FILM" render/film10.blend; do
  waitmem "socket_audit $(basename $f)" || exit 90
  echo "--- $(basename $f) ---"
  python3 tools/socket_index_audit.py --blend "$f" 2>&1 | tail -12
done

echo
echo "=== rig_preflight ==="
python3 tools/rig_preflight.py 2>&1 | tail -12
echo "  rig_preflight exit=$?"

echo
echo "=== slabcheck (MUST exit 0) ==="
.venv/bin/python sim/slabcheck.py 2>&1 | tail -3
echo "  slabcheck exit=$?"

exit $BARRC
