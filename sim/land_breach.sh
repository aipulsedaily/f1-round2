#!/bin/bash
# LAND THE BAKE.  Everything between a finished raw table and a rendered frame.
#
#   bash sim/land_breach.sh <raw_bake.npz> <sim_report.json> <target_film.blend>
#
# Every stage prints a STAGE RESULT line and this script STOPS on the first
# one that is not PASS.  Blender 5.2 exits 0 on an uncaught exception, so `$?`
# is not evidence and is not used as any stage's verdict here: each stage is
# judged on text it printed, or on a file it was supposed to write.
#
# WHY THIS IS A SCRIPT AND NOT A MEMORY.  The order matters and two of the
# steps have already been got wrong on this project: the release rule differs
# between entry points (fixed, resample.release_for_film), and the applier must
# be pointed at the CURRENT film scene, which has moved three times in a day.
set -u
cd /home/zany/f1-round2
B="${1:-sim/tmp/breach_full_m1.npz}"
J="${2:-sim/tmp/breach_full_m1.json}"
FILM="${3:-}"
BL=/opt/blender-5.2.0-linux-x64/blender
PY=.venv/bin/python

say() { echo; echo "=== $* ==="; }
die() { echo "STAGE RESULT: FAIL -- $*"; exit 1; }

[ -f "$B" ] || die "no raw bake at $B"
[ -f "$J" ] || die "no sim report at $J"

say "0.  what was baked"
$PY -c "
import json,sys
d=json.load(open('$J'))
print('thresholds', json.dumps(d['thresholds']))
print('sim_frames', d['sim_frames'], 'bodies', d['n_bodies'],
      'constraints', d['n_constraints'])
t=d['thresholds']
ok = (t['bond_per_m']==100.0 and t['mullion_joint']==40.0
      and t['mullion_base']==120.0 and t['glass_edge']==2.5
      and t['pvb']==0.9 and t['transom']==260.0)
print('STAGE RESULT: thresholds', 'PASS' if ok else 'FAIL',
      '(want bond 100, mullion 40/120, everything else unchanged)')
sys.exit(0 if ok else 1)
" || die "the bake is not at the configuration that was decided"

say "1.  resample to film frames  (release_for_film, ONE rule)"
$PY sim/resample.py --bake "$B" \
    --out sim/out/breach_film.npz --report sim/out/breach_film.json \
    2>&1 | tail -30
$PY -c "
import json,sys
r=json.load(open('sim/out/breach_film.json'))
print('release_min', r.get('release_frame_min'), 'ref',
      r.get('release_reference_frame'), 'never', r.get('never_released'),
      'max_pos_err_m', r.get('max_pos_err_m'))
ok = r.get('release_frame_min',0) >= 860 and r.get('max_pos_err_m',9) <= 0.0016
print('STAGE RESULT: resample', 'PASS' if ok else 'FAIL')
sys.exit(0 if ok else 1)
" || die "resample"

say "2.  the swap: one frame per bay, nothing uncovered  (R2-098)"
$PY sim/verify_breach.py --swap 2>&1 | tail -6 | grep "STAGE RESULT" \
  || die "swap check printed no verdict"

say "3.  does the wall un-break?  (the f0866 prediction)"
$PY sim/slabcheck.py --film sim/out/breach_film.npz \
    --out sim/out/slab_NEW.json 2>&1 | tail -3

say "4.  the aperture, on the honest connected measure"
$PY sim/breach_metrics.py "$B" "$J" > sim/out/metrics_NEW.json 2>&1
$PY -c "
import json
d=json.load(open('sim/out/metrics_NEW.json'))
print('CONTROLS', json.dumps(d['CONTROLS']))
a=d['aperture']
print('connected %.2f x %.2f m, vacated %.1f%%'
      % (a['hole_w_m'], a['hole_h_m'], a['vacated_pct']))
print('per bay', json.dumps(a['per_bay']))
print('frame bodies', json.dumps(d['frame_bodies']))
print('STAGE RESULT: metrics', 'PASS' if d['CONTROLS']['PASS'] else 'FAIL')
"

say "5.  the full verifier"
$PY sim/verify_breach.py --film sim/out/breach_film.npz \
    --out sim/out/verify.json 2>&1 | tail -5

if [ -z "$FILM" ]; then
  echo
  echo "STOPPING BEFORE THE APPLY: no target film scene given."
  echo "Pass the CURRENT one as argument 3.  It has moved three times today"
  echo "(film9 -> film10 -> film11 -> film11_r2085cam, and film12 is being"
  echo "built on assembly8).  Applying onto a superseded scene is the whole"
  echo "reason film9_breach had to be redone."
  exit 0
fi

say "5b. the camera track, from the CURRENT scene"
echo "sim/out/oner_camera_track.json was made by hand from film9 at 15:13 and"
echo "the camera has moved twice since.  Every pixel figure goes through it."
$BL -b "$FILM" -P sim/dump_camera_track.py -- \
    --out sim/out/oner_camera_track.json 2>&1 | tail -30 | grep -E "STAGE RESULT|blend|camera|sensor" \
  || die "camera track"

say "6.  apply onto $FILM"
echo "NOTE: R5 still refuses, and what it refuses on has CHANGED (R2-266)."
echo "It used to name GW_Right_Transom_0/1/2 -- three unbroken 21.9 m bars"
echo "across the aperture -- and this script said the geometry 'was not ours'."
echo "It is: R6 is implemented now, sim/eastframe.py cuts round 1's east frame"
echo "into the pieces the bake moves, and the applier reports R5 AGAIN after"
echo "the build with the intruders classified by whether they cross the WOUND."
echo "Over the wound that count is 0.  What is left is the SOUTH wall's frame"
echo "(GW_Front_*), two light fins, and this module's own transom remainder"
echo "over the six bays that keep their glass -- all deliberate, none ours to"
echo "move.  --force is still right; read R5_intruders_over_the_wound_after in"
echo "the apply report, not the preflight's headline count."
OUT="render/$(basename "$FILM" .blend)_breach.blend"
$BL -b "$FILM" -P sim/apply_breach.py -- \
    --out "$OUT" --report sim/out/apply_NEW.json --force 2>&1 | tail -25
$PY -c "
import json,sys,os
r=json.load(open('sim/out/apply_NEW.json'))
e=r.get('east_wall',{})
print('east wall PASS' , e.get('PASS'), 'panes', len(e.get('panes_built',[])),
      'missing', e.get('panes_missing'), 'hidden', e.get('panes_hidden_at_frame'))
print('objects', r['stats']['objects'], 'keys', r['stats']['keys'])
ok = bool(e.get('PASS')) and r['stats']['objects'] > 3800
print('STAGE RESULT: apply', 'PASS' if ok else 'FAIL')
sys.exit(0 if ok else 1)
" || die "apply"
say "7.  the swap, asked of the SCENE that renders  (R2-098)"
$BL -b "$OUT" -P sim/verify_breach.py -- --swap-scene 2>&1 \
    | grep -E "STAGE RESULT|problems" | tail -4

echo
echo "STAGE RESULT: landed.  Scene written to $OUT"
echo "Next: render f0855-f0890 on the farm and LOOK at them."
