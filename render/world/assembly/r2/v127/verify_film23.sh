#!/bin/bash
# READ film23_breach BACK from the saved blend and judge it against the bar.
# v126/verify_film19.sh, with the lamp numbers moved and two sections added.
# R2-2101.
#
#   usage: verify_film23.sh [blend]     default render/film23_breach.blend
#
# THE BAR:
#     interior lamp load  46,866.886 W  from showroom_lighting.measure(), NOT a
#                                       hand-rolled probe -- a hand-rolled one
#                                       read 46,319 W by counting a lamp that
#                                       is not interior
#     _sl_base stamps     24            scene key showroom_lighting_stops
#     scene_mark          3.628         assert_levelled PASS, UNCONDITIONALLY
#     ONER clip           0.05/200000   3840x2160, 24 fps, 1..2978, AgX, look
#                                       None, exposure -3.628
#     socket audit        PASS, against film10's standing 27-finding FAIL
#     carbon + rubber     Mapping.Scale 62.8319, Traffic Passes 1000, 2 TDP_*
#     slabcheck           exits 0
#
# WHY 46,866.886 AND 24, AND WHY THAT IS NOT MOVING THE GOALPOSTS.
# The number was PREDICTED BEFORE THE BUILD, not read off it.  R2-1146's strip
# source is 50.0 W nominal / luma(COLD) 0.931576 = 53.6725 W, levelled by the
# same 2**3.628 = 12.363369 as everything else, so it adds 663.573 W to
# 46,203.313.  `python3 world/showroom_strip.py --selftest` prints that
# prediction and the arithmetic behind it, and it printed it before
# `run_rebuild23.sh` was started.  If the artefact disagrees, the artefact is
# what is wrong.
#
# WHY film10 IS STILL IN THIS SCRIPT.  It is the NEGATIVE CONTROL.  An audit
# that has never failed is not evidence that anything passed, and film10 is the
# file on which this one is known to report 27 findings.  Keep it.  If film10
# ever comes back PASS the instrument is broken and every PASS above it is
# vacuous.
set -u
cd /home/zany/f1-round2
FILM=${1:-render/film23_breach.blend}
NAME=$(basename "$FILM" .blend)
B=/opt/blender-5.2.0-linux-x64/blender
W=work/r22101
mkdir -p $W

WANT_WATTS=46866.886
WANT_STAMPS=24

[ -s "$FILM" ] || { echo ">> STAGE RESULT: VERIFY23_FAIL (no $FILM)"; exit 2; }

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
echo "=== the strip source, R2-1146's second half ==="
waitmem showroom_strip || exit 90
$B -b "$FILM" --factory-startup -noaudio \
    -P render/world/assembly/r2/v127/measure_strip.py -- \
    --json $W/strip_${NAME}.json > $W/strip_${NAME}.log 2>&1
grep -aE "^>> STAGE RESULT" $W/strip_${NAME}.log || echo "  (strip probe printed no verdict)"
python3 -c "
import json,sys
try: m=json.load(open('$W/strip_${NAME}.json'))
except Exception as e: print('  strip NOT MEASURED: %s' % e); sys.exit(0)
for k in sorted(m): print('  %-24s %s' % (k, json.dumps(m[k])))
"

echo
echo "=== THE BAR, judged ==="
python3 -c "
import json, sys
b=json.load(open('$W/extra_${NAME}.json'))
try:    m=json.load(open('$W/measured_${NAME}.json'))
except Exception: m={}
try:    s=json.load(open('$W/strip_${NAME}.json'))
except Exception: s={}
ok=True
def chk(name, got, want, tol=0.0):
    global ok
    if isinstance(want,(int,float)) and isinstance(got,(int,float)) and not isinstance(want,bool):
        good = abs(float(got)-float(want)) <= tol
    else:
        good = (got==want)
    ok = ok and good
    print('  %-34s want %-16s got %-16s %s' % (name, want, got, 'OK' if good else 'FAIL'))
chk('interior_lamp_watts', b.get('interior_lamp_watts_measured'), $WANT_WATTS, 1e-2)
chk('n_lamp_stamps',       b.get('n_lamp_stamps'), $WANT_STAMPS)
chk('scene_mark',          b.get('scene_mark'), 3.628, 1e-9)
chk('assert_levelled',     b.get('assert_levelled'), 'PASS')
chk('strip present',       s.get('present'), True)
chk('strip narrow axis m', s.get('size_y'), 0.10, 1e-4)
chk('strip radiance (authored)', s.get('radiance_authored'), 47.4569, 1e-3)
chk('strip is hidden from camera', s.get('visible_camera'), False)
for k,want in (('fps',24),('frame_start',1),('frame_end',2978),
               ('view_transform','AgX'),('look','None'),('exposure',-3.628)):
    if k in m: chk(k, m.get(k), want, 1e-6 if isinstance(want,float) else 0)
    else:      print('  %-34s NOT REPORTED by measure_film_scene' % k)
# R2-2109.  THE ONER/4K/CLIP LINE OF THE BAR WAS NEVER ACTUALLY JUDGED.
# v124, v125 and v126 all asked measure_film_scene for 'resolution_x',
# 'resolution_y', 'clip_start', 'clip_end' and 'camera'.  IT EMITS NONE OF
# THOSE KEYS -- it has 'scene_camera', and no resolution and no clip at all --
# so all five fell into the else branch, printed 'NOT REPORTED', and were
# counted as neither pass nor fail.  Five of the bar's own lines have been
# decorative on every film this project has verified, including the one that
# names the delivery format.
# They ARE in measure_film_extra, off the same open blend.
res = b.get('resolution') or [None, None, None]
chk('resolution_x', res[0], 3840)
chk('resolution_y', res[1], 2160)
chk('resolution_pct', res[2], 100)
cam = b.get('camera') or {}
chk('camera',     cam.get('name'), 'ONER')
chk('clip_start', cam.get('clip_start'), 0.05, 1e-9)
chk('clip_end',   cam.get('clip_end'), 200000.0, 1e-6)
chk('n_cameras_in_scene', b.get('n_cameras_in_scene'), 1)
chk('scale_length', b.get('scale_length'), 1.0, 1e-9)
chk('camera object_fcurves', bool(cam.get('object_fcurves')), True)
print()
print('>> STAGE RESULT: %s' % ('VERIFY23_BAR_PASS' if ok else 'VERIFY23_BAR_FAIL'))
sys.exit(0 if ok else 1)
"
BARRC=$?

echo
echo "=== carbon + rubber, read back out of the FILM (R2-2041's two fixes) ==="
waitmem film_materials || exit 90
$B -b "$FILM" --factory-startup -noaudio \
    -P render/world/assembly/r2/v127/verify_film_materials.py -- \
    --json $W/materials_${NAME}.json > $W/materials_${NAME}.log 2>&1
grep -aE "^\[|^   |^>> STAGE RESULT" $W/materials_${NAME}.log | tail -40
grep -qa ">> STAGE RESULT: FILM_MATERIALS_OK" $W/materials_${NAME}.log \
  || { echo "  ^^ carbon/rubber DID NOT PASS"; BARRC=1; }

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
