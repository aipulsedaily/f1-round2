#!/bin/bash
# READ film25_breach BACK from the saved blend and judge it against the bar.
# R2-3661: v128/verify_film24.sh with W -> work/r23661, the default film ->
# film25_breach, and `--want film25`.
#
# film23's evidence in work/r22101 and film24's in work/r23361 are the ONLY
# proof that those two ship candidates passed 40/40, and neither is
# reproducible from any later state of these files.  Nothing here writes into
# either directory.
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
# WHY THE PREDICTION IS FILM25'S OWN.  `film_bar.py`'s `FILM23` and `FILM24`
# dicts are those films' predictions; judging film25 by either would be moving
# the goalposts, even though all three agree to the last digit.  The value of
# the number is that it was computed from arithmetic BEFORE the artefact
# existed, and film24's was computed before a DIFFERENT artefact existed.
# film25's own was printed at 2026-08-09T01:29:14Z into
# `work/r23661/PREDICTION_film25_20260809T012914Z.log`, which predates
# `render/film25_breach.blend`, and it is `FILM25` in `tools/film_bar.py`,
# selected here by `--want film25`.
#
# They agree because THE PREDICTION IS A FUNCTION OF THE SHOWROOM, not of the
# world or the car.  film25 differs from film24 ONLY in the world underneath
# it -- assembly15 rather than assembly14 -- and assembly15 adds ground cover,
# which is TER/VEG geometry carrying no lamp.  If the artefact disagrees, the
# artefact is what is wrong.
#
# WHY film10 IS STILL IN THIS SCRIPT.  It is the NEGATIVE CONTROL.  An audit
# that has never failed is not evidence that anything passed, and film10 is the
# file on which this one is known to report 27 findings.  Keep it.  IF FILM10
# EVER COMES BACK PASS THE INSTRUMENT IS BROKEN AND EVERY PASS ABOVE IT IS
# VACUOUS -- stop and say so, do not report the bar.
set -u
set -o pipefail
cd /home/zany/f1-round2
FILM=${1:-render/film25_breach.blend}
NAME=$(basename "$FILM" .blend)
B=/opt/blender-5.2.0-linux-x64/blender
W=work/r23661
mkdir -p $W

[ -s "$FILM" ] || { echo ">> STAGE RESULT: VERIFY25_FAIL (no $FILM)"; exit 2; }

# R2-4020: THE MEASUREMENT PASSES TAKE THE BUILD LOCK.  A POLL CANNOT SEE INTENT.
#
# What was here was `waitmem`: poll `free -g`, start the pass the moment 5 GB
# looked available, time out after 8 h.  It gated the four heavy passes below
# while the bar at the bottom of this file -- the FIFTH heavy step, no bigger
# than the other four -- already went through `tools/buildlock.sh`.  The four
# were the ones outside the lock.
#
# MEASURED, 2026-08-10, on this box (11 GB RAM), pass 1 of this very script:
#
#     measure_film_scene.py on render/film25_breach.blend (10.9 GB)
#         peak RSS          7,847 MB  (7.66 GB)   VmHWM, 0.5 s polling
#         ru_maxrss         agrees to the megabyte
#         MemAvailable      7,382 MB at start  ->  264 MB at the trough
#
# ONE pass takes this box down to 264 MB.  And for the FIRST 16.5 SECONDS of
# that pass -- while it was already committed to 7.66 GB but had touched only
# ~5.7 GB of it -- `free -g` still read >= 5 GB and `waitmem` returned "start".
# So the gate was GREEN for exactly the window in which a second pass could be
# admitted, and a second pass admitted there lands in a box with 264 MB to
# spare.  The OOM killer then takes the BIGGEST process, which is whichever
# 7.66 GB pass is nearest to finishing, or somebody else's 10 GB film append.
#
# That is not a weak threshold to be tuned; a poll samples what is ALLOCATED
# NOW and the thing that matters is what is INTENDED.  Only a lock carries
# intent, because the holder registers before it allocates.  The evidence is
# `docs/r2_4020_waitmem_timeline.tsv` (0.5 s samples, the ramp and the trough).
#
# LANE: BIG, for all four.  7.66 GB is not remotely a `--small` job -- that
# lane is two slots gated at SMALL_MIN_MB=1000, sized for ~400 MB surface
# builds, and putting 7.66 GB in it would let two of them run at once and kill
# the thing the lane exists to protect.
#
# Note the deliberate behaviour change: `waitmem` gave up after 8 h and
# returned failure; buildlock QUEUES INSTEAD OF FAILING, by design, so a
# contended pass is late rather than lost.
#
# runlocked <lockname> <final-log> <cmd...>
#
#   * The blender binary stays a DIRECT argv element of buildlock.sh.  Its
#     wrong-Blender refusal (R2-3602) inspects `basename` of each argument, so
#     wrapping the command in `bash -c` would silently disarm the one check
#     that stands between this script and a quietly-corrupt world.  Do not.
#
#   * buildlock prints its OWN `>> STAGE RESULT: BUILDLOCK RELEASED` line.
#     `film_bar.py`'s VERDICT_RE is `>{0,2} *STAGE RESULT:` and it FAILs any
#     log carrying TWO verdicts (R2-2108) -- and the four logs written below
#     are exactly the four `film_bar.py` reads.  So the raw stream is captured
#     beside the log and the BUILDLOCK verdict lines are stripped on the way
#     in.  Same capture-and-replay the bar wrapper at the bottom of this file
#     has always used, for the same reason, four steps earlier.
#
#   * A refusal is NOT turned into an exit.  It leaves the log with no verdict,
#     which `film_bar.py` scores UNMEASURABLE -- this file's standing rule that
#     the printed evidence decides, never `$?`.
runlocked () {
  local lname="$1" flog="$2"; shift 2
  local raw="${flog%.log}.lock.log"
  bash tools/buildlock.sh "$lname" "$@" > "$raw" 2>&1
  local rc=$?
  grep -av "STAGE RESULT: BUILDLOCK" "$raw" > "$flog"
  [ $rc -eq 0 ] || echo "  [lock] $lname rc=$rc -- refused, or the pass failed; raw log: $raw"
  return $rc
}

echo "########## VERIFY $NAME  $(date -Is)"
ls -l "$FILM"

runlocked "verify25_measure_${NAME}" "$W/measure_${NAME}.log" \
    $B -b "$FILM" --factory-startup -noaudio \
    -P work/lighting/measure_film_scene.py -- --json $W/measured_${NAME}.json
echo "  measure_film_scene rc=$?  (exit status is NOT the evidence)"

runlocked "verify25_extra_${NAME}" "$W/extra_${NAME}.log" \
    $B -b "$FILM" --factory-startup -noaudio \
    -P work/r2100/measure_film_extra.py -- $W/extra_${NAME}.json
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
runlocked "verify25_strip_${NAME}" "$W/strip_${NAME}.log" \
    $B -b "$FILM" --factory-startup -noaudio \
    -P render/world/assembly/r2/v127/measure_strip.py -- \
    --json $W/strip_${NAME}.json
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
# R2-4020: `runlocked` preserves that.  It captures buildlock's stream to
# `materials_${NAME}.lock.log` and strips buildlock's OWN `STAGE RESULT:
# BUILDLOCK ...` line before writing this log, precisely so the lock cannot
# become the second verdict that fails a passing stage.
runlocked "verify25_materials_${NAME}" "$W/materials_${NAME}.log" \
    $B -b "$FILM" --factory-startup -noaudio \
    -P render/world/assembly/r2/v127/verify_film_materials.py -- \
    --json $W/materials_${NAME}.json
grep -aE "^\[|^   |^>> STAGE RESULT" $W/materials_${NAME}.log | tail -40

echo
echo "=== THE BAR, judged -- every assertion this header makes, counted ==="
# `--socket` opens film25_breach (10.9 GB) and film10 (4.5 GB).  It is NOT
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
bash tools/buildlock.sh "verify25_bar_${NAME}" \
  python3 tools/film_bar.py --work $W --name "$NAME" --want film25 \
      --rig world/surface_test_filmpose.blend \
      --socket --film "$FILM" > $W/bar_${NAME}.log 2>&1
BARRC=$?
grep -av "STAGE RESULT: BUILDLOCK" $W/bar_${NAME}.log

exit $BARRC
