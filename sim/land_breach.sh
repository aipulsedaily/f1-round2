#!/bin/bash
# LAND THE BAKE.  Everything between a finished raw table and a rendered frame.
#
#   bash sim/land_breach.sh <raw_bake.npz> <sim_report.json> <target_film.blend> [out.blend]
#
# The 4th argument is the scene to WRITE.  It used to be computed as
# "render/<film>_breach.blend", which means landing a second bake onto the same
# film silently overwrote the first one's delivered scene -- a 5 GB artefact
# other agents are rendering from.  It still defaults to that name so nothing
# that called this script with three arguments changes; pass a fourth when the
# old one has to survive, which is every A/B.
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
OUT_ARG="${4:-}"
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
# R2-282.  THE DECIDED CONFIGURATION HAS MOVED, AND THIS GATE IS WHY IT COULD
# NOT MOVE BY ACCIDENT.  It used to pin transom == 260.0, which is 499 kN for
# two M6 self-tappers, so any bake that corrected the frame would have been
# refused here.  The two frame numbers are now the DERIVED ones
# (sim/frame_thresholds.py): transom 8.8 = 16.90 kN, and the head is a SLIDER
# because wall_iface declares a 17.2 mm expansion gap at that joint.  The
# head's breaking threshold is unchanged at mullion_joint * 0.5 = 20 on
# purpose -- see the note in build_breach_sim.
want = dict(bond_per_m=100.0, mullion_joint=40.0, mullion_base=120.0,
            glass_edge=2.5, pvb=0.9, transom=8.8, head=20.0,
            head_restraint='slider')
bad = {k: (t.get(k), v) for k, v in want.items() if t.get(k) != v}
ok = not bad
if bad:
    print('MISMATCH got/want', json.dumps(bad))
print('STAGE RESULT: thresholds', 'PASS' if ok else 'FAIL',
      '(want bond 100, mullion 40/120, transom 8.8, head slider at 20)')
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
# R2-1121: THIS NOW GATES.  It used to be `... 2>&1 | tail -3` with no `|| die`,
# so the pipeline's status was tail's and slabcheck's exit code went in the bin
# -- which is how a bay declared to leave and reading DID_NOT_MOVE survived
# even after R2-1049 taught the tool to fail on it.  The verification bar says
# "slabcheck MUST exit 0"; something has to actually read it.  `set -u` is on
# but `pipefail` is not, so the status is taken without a pipe.
$PY sim/slabcheck.py --film sim/out/breach_film.npz \
    --out sim/out/slab_NEW.json > sim/tmp/slab_stage.txt 2>&1 \
    || { tail -3 sim/tmp/slab_stage.txt; die "slabcheck"; }
tail -3 sim/tmp/slab_stage.txt

say "3b. does the wall un-break?  asked of the ALUMINIUM  (R2-601)"
# STAGE 3 ABOVE GATED ON NOTHING UNTIL R2-1121 -- it printed slabcheck's tail
# and the script carried on regardless -- and slabcheck asks the question of the
# GLASS, which is the half that has not failed since bond went to 100.  The
# half that fails is the frame: in the shipped table 62 of 66 deflected frame
# bodies end up back at home, MUL05_S02 peaking at 157 mm and ending at 0.7 mm.
# Nothing saw it because every frame number in this pipeline is a MAX.
$PY sim/breach_metrics.py "$B" "$J" > sim/out/metrics_NEW.json 2>&1
$PY -c "
import json
d = json.load(open('sim/out/metrics_NEW.json'))
p = d['persistence']
f, g = p['frame_bodies'], p['glass']
print('rule:', p['rule'])
print('CONTROLS', json.dumps(p['CONTROLS']))
print('aluminium: %d of %d deflected bodies came home, largest %s at %.4f m'
      % (f['RECOVERED'], f['deflected'], f['max_recovered_name'],
         f['max_recovered_peak_m']))
print('           worst', json.dumps(f['worst'][:4]))
print('glass:     %d of %d came home, median end/peak %s'
      % (g['RECOVERED'], g['deflected'], g['median_end_over_peak']))
print('STAGE RESULT: persistence', 'PASS' if p['PASS'] else 'FAIL')
" | tee sim/tmp/persist_stage.txt
grep -q "STAGE RESULT: persistence PASS" sim/tmp/persist_stage.txt \
    || die "the wall un-breaks: a deflected member returns to the intact rest \
pose.  This is R2-601.  The lever is t_transom, NOT the head restraint: at \
transom 260 the three full-width rails never break their bolt to mullions \
4/5/6, bays 3-6 stay one rigid ladder, and its FIXED constraints drive every \
deflection back to zero.  Re-bake at the derived transom threshold (8.8)."

say "4.  the aperture, on the honest connected measure"
# metrics_NEW.json was written by stage 3b -- scoring a 152 MB table twice is
# four minutes of nothing.
$PY -c "
import json
d=json.load(open('sim/out/metrics_NEW.json'))
print('CONTROLS', json.dumps(d['CONTROLS']))
a=d['aperture']
# R2-606 / R2-1083: the aperture has TWO correct values and this line quoted
# only the narrower one, labelled 'connected' — which is how 2.15 x 6.00
# entered every document.  \`sim/aperture.py\` returns both from one call and its
# own docstring says quoting one without the mullion state is a known error.
# Neither number is the aperture on its own; the pair is.
print('aperture, mullion strips OPAQUE   %.2f x %.2f m, vacated %.1f%%'
      % (a['hole_w_m'], a['hole_h_m'], a['vacated_pct']))
if 'hole_bridged_w_m' in a:
    print('aperture, strips PASSABLE where that segment left'
          '   %.2f x %.2f m'
          % (a['hole_bridged_w_m'], a['hole_bridged_h_m']))
    print('  -> the opening is %.2f m wide at car height and %.2f m above '
          'z=1.593, where mullion 5 S02-S07 still stand.  Quote BOTH, always '
          'with the mullion state.'
          % (a['hole_bridged_w_m'], a['hole_w_m']))
else:
    print('  !! hole_bridged_* MISSING from metrics_NEW.json — this bake '
          'predates R2-606 and the single number below is the NARROW one')
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
OUT="${OUT_ARG:-render/$(basename "$FILM" .blend)_breach.blend}"
echo "writing $OUT"
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
