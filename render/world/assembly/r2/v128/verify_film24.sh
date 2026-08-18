#!/bin/bash
# READ film24_breach BACK from the saved blend and judge it against the bar.
# R2-3361: v127/verify_film23.sh with W -> work/r23361, the default film ->
# film24_breach, and `--want film24`.  film23's OWN measurement artefacts in
# work/r22101 are the only evidence that the previous ship candidate passed
# 40/40 and are NOT reproducible from any earlier state of these files, so
# nothing here may write into that directory.
# v126/verify_film19.sh, with the lamp numbers moved and two sections added.
# R2-2101.
#
#   usage: verify_film24.sh [blend]     default render/film24_breach.blend
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
# prediction and the arithmetic behind it.
#
# R2-3361: FILM24 HAS ITS OWN, and re-using film23's would have been moving the
# goalposts even though the two agree to the last digit -- the value of the
# number is that it was computed from arithmetic BEFORE the artefact existed,
# and film23's was computed before a DIFFERENT artefact existed.  film24's was
# printed at 2026-08-08T18:59:12Z into
# `work/r23361/PREDICTION_film24_20260808T185912Z.log`, which predates
# `render/film24_breach.blend`, and it is `FILM24` in `tools/film_bar.py`,
# selected here by `--want film24`.  They agree because the prediction is a
# function of the SHOWROOM, not of the car: film24 differs from film23 only in
# the car's keys and the camera, and both cars carry the same 23 lamps, none of
# them inside `showroom_lighting.SHELL` (`work/r23361/lampcheck.log`).
# If the artefact disagrees, the artefact is what is wrong.
#
# WHY film10 IS STILL IN THIS SCRIPT.  It is the NEGATIVE CONTROL.  An audit
# that has never failed is not evidence that anything passed, and film10 is the
# file on which this one is known to report 27 findings.  Keep it.  If film10
# ever comes back PASS the instrument is broken and every PASS above it is
# vacuous.
#
# R2-3121 -- THE THREE EDITS R2-2821 WROTE OUT FOR WHOEVER HELD THIS FILE.
# The lease `r2-2101-breach-strip` is gone, so they are applied here:
#   1. `set -o pipefail`, below.  Of 176 shell scripts in this repo, 5 set it,
#      and every discarded verdict in this harness came from a `cmd | tail`
#      whose status the shell then reported as the tool's.
#   2. the inline `python3 -c "..."` judge is replaced by `tools/film_bar.py`,
#      which counts EVERY assertion this header makes.  The old judge made 37
#      assertions and could act on 24; the 13 silent ones included both socket
#      arms, `rig_preflight`, `slabcheck`, and every stage's printed verdict.
#      With them counted, film23's recorded `VERIFY23_BAR_PASS` became
#      `FILM_BAR_FAIL`.
#   3. the trailing `socket_index_audit` / `rig_preflight` / `slabcheck`
#      sections are deleted.  `film_bar.py` runs all four as list-argv
#      subprocesses -- no shell, therefore no pipe, therefore the status is
#      the tool's own -- and judges each one.
# The judge lives in `tools/`, ONCE, and not in this `vNNN` directory: this bar
# was copy-pasted per generation, so R2-2109's repair landed in one of four
# copies and the other three kept printing PASS.
#
# THE MATERIALS BUILD NOW RUNS BEFORE THE JUDGE, not after it.  It has to: the
# judge reads `materials_${NAME}.log`, and in the old order that log was the
# PREVIOUS run's.
set -u
set -o pipefail
cd $HOME/f1-round2
FILM=${1:-render/film24_breach.blend}
NAME=$(basename "$FILM" .blend)
B=/opt/blender-5.2.0-linux-x64/blender
W=work/r23361
mkdir -p $W

# R2-3121: `WANT_WATTS=46866.886` and `WANT_STAMPS=24` used to live here and
# were the inline judge's only copy of this film's predicted load.  They are
# now `FILM23`/`FILM24` in `tools/film_bar.py`, once each.  A second copy here
# would be a
# number nothing reconciles -- seven copies of the car's bounding box were
# found in this codebase on 2026-08-08 and this file is not adding to that.

[ -s "$FILM" ] || { echo ">> STAGE RESULT: VERIFY24_FAIL (no $FILM)"; exit 2; }

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
echo "=== carbon + rubber, read back out of the FILM (R2-2041's two fixes) ==="
# THE REDIRECT IS THE WHOLE LOG.  `film_bar.py` requires EXACTLY ONE
# `>> STAGE RESULT:` line in this file and FAILs on two -- a log carrying two
# verdicts has an unread verdict (R2-2108).  Nothing else may be appended here.
waitmem film_materials || exit 90
$B -b "$FILM" --factory-startup -noaudio \
    -P render/world/assembly/r2/v127/verify_film_materials.py -- \
    --json $W/materials_${NAME}.json > $W/materials_${NAME}.log 2>&1
grep -aE "^\[|^   |^>> STAGE RESULT" $W/materials_${NAME}.log | tail -40

echo
echo "=== THE BAR, judged -- every assertion this header makes, counted ==="
# This film's predicted load lives in film_bar.py's `FILM24`, and the bar's
# other constants are IMPORTED by it from world/film_exposure.py,
# world/showroom_lighting.py and docs/beat_sheet.json.  Nothing derivable is
# retyped here any more.
#
# `--socket` opens film24_breach (10.9 GB) and film10 (4.5 GB).  It is not
# optional: film10 is the bar's ONLY negative control, the one thing that
# proves the socket instrument still fires, and NOT running it is
# UNMEASURABLE, which film_bar.py counts as a failure to verify rather than as
# a pass.  Wrapped in the build lock because two ~10 GB opens on an 11 GB box
# do not run at half speed -- one of them gets OOM-killed.
#
# THE OUTPUT GOES TO A FILE AND IS THEN REPLAYED WITHOUT buildlock's OWN
# `>> STAGE RESULT: BUILDLOCK RELEASED` LINE.  Not cosmetics: this script's
# stdout must carry EXACTLY ONE verdict, or every reader of it inherits the
# two-verdict trap that cost this bar two of its four failures.  `BARRC` is
# buildlock's status, which is the bar's own -- buildlock ends on `exit $rc`,
# not on a pipeline.
#
# R2-3361: `--want film24` IS NOT COSMETIC.  `film_bar.py`'s `FILM23` dict is
# FILM23's prediction, and judging film24 by it would be moving the goalposts
# even though the two agree to the last digit -- the number's value is that it
# was computed from arithmetic before the artefact existed, and film23's was
# computed before a DIFFERENT artefact existed.  film24's own was printed at
# 2026-08-08T18:59:12Z into work/r23361/PREDICTION_film24_20260808T185912Z.log,
# which predates render/film24_breach.blend.  `--want` defaults to film23 so no
# existing caller changes meaning.
bash tools/buildlock.sh "verify24_bar_${NAME}" \
  python3 tools/film_bar.py --work $W --name "$NAME" --want film24 \
      --rig world/surface_test_filmpose.blend \
      --socket --film "$FILM" > $W/bar_${NAME}.log 2>&1
BARRC=$?
grep -av "STAGE RESULT: BUILDLOCK" $W/bar_${NAME}.log

exit $BARRC
