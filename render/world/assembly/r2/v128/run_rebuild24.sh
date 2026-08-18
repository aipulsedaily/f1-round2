#!/bin/bash
# film24 -- THE FIRST FILM WHOSE ENDING HAS A CAR IN IT.  R2-3361.
#
# `render/film23_breach.blend` IS NOT TOUCHED BY THIS SCRIPT AND MUST NOT BE.
# It carries a clean bar (FILM_BAR_PASS 40/40) and a clean placement verdict,
# and those must stay measurable on the file they were measured on.  Every
# output name here is film24 and every work path is `work/r23361`, so
# `work/r22101` -- film23's only evidence -- is immutable from here.
#
# WHAT IS DIFFERENT FROM film23, AND IT IS EXACTLY TWO THINGS
# -----------------------------------------------------------
#   1. THE CAR.  film22 and film23 both append
#      `world/R22041_car_anim_driver_CS.blend`, whose CAR_ROOT keys predate the
#      R2-943 lap-down.  Measured on that artefact by `car_staleness --keys`:
#      f1200/f2000/f2714 all 0.000 m, then 43.490 / 247.075 / 678.031 m at
#      f2760 / f2850 / f2978.  91 of beat 6's 264 frames -- 34.5 %, 3.79 s,
#      including the film's LAST FRAME -- contain no car at all.
#      This appends `world/R2_3361_car_anim_driver_CS.blend`, which reads
#      CAR_KEYS_MATCH_SOURCE at 0.000 m on all six probes.
#
#   2. THE CAMERA.  `build_film_scene` rebuilds the rig IN-PROCESS from
#      `--sheet` on every build (tools/build_film_scene.py:633), so passing the
#      live `docs/beat_sheet.json` is what carries beat 5's re-pace, beat 1's
#      re-pace and beat 6's closing lens.  Measured against film23's camera:
#      beat 1 lens differs by 7.027 mm, beat 5 position by 0.264 m and lens by
#      1.407 mm, beats 2/3/4/6 by exactly 0.  `render/film23_path.json` is
#      `363e4e88...`; this build's must NOT come out at that sha or the rig did
#      not pick the sheet up.
#
# The world is assembly14, UNCHANGED -- see the override block below, which is
# the one judgement call in this file and is not buried.
#
# Four stages, each judged only on its printed `>> STAGE RESULT:` token --
# Blender 5.2 exits 0 on an uncaught exception, so `$?` is not evidence -- and
# every stage checked for the two-verdict trap.
set -u
cd $HOME/f1-round2
W=work/r23361
V7=render/world/assembly/r2/v127
V8=render/world/assembly/r2/v128
CAR=world/R2_3361_car_anim_driver_CS.blend
ASM=render/world/assembly/r2/assembly14.blend
SHEET=docs/beat_sheet.json
B=/opt/blender-5.2.0-linux-x64/blender
mkdir -p $W
exec > >(tee -a $W/REBUILD24.log) 2>&1
echo "######################## R2-3361 film24 $(date -Is)"

[ -s "$ASM" ] || { echo ">> STAGE RESULT: REBUILD24_FAIL (no assembly14)"; exit 10; }
[ -s "$CAR" ] || { echo ">> STAGE RESULT: REBUILD24_FAIL (no $CAR)"; exit 10; }
grep -q "STAGE RESULT: ASSEMBLY14_FIXES_PRESENT" work/r22041/assembly14_stdout.txt || {
  echo ">> STAGE RESULT: REBUILD24_FAIL (assembly14 did not pass acceptance)"
  exit 10; }

# THE SHIP CANDIDATE MUST NOT BE OVERWRITTEN, AND THAT IS MEASURED, NOT ASKED.
# A promise not to write a file is not evidence; the sha is taken here and
# re-taken at the end, and a difference FAILS the build.
BEFORE23=$(sha256sum render/film23_breach.blend 2>/dev/null | cut -c1-16)
echo ">> film23_breach.blend sha16 BEFORE this run: ${BEFORE23:-absent}"
[ -n "$BEFORE23" ] || { echo ">> STAGE RESULT: REBUILD24_FAIL (film23_breach.blend is absent -- refusing to run without the baseline this build promises not to touch)"; exit 10; }

# THE CAR'S PROVENANCE, ASSERTED RATHER THAN ASSUMED.  A date check cannot
# catch this defect -- R2-3308 proved it: `--check` on the shipped car fires
# and never names anim/carpath.py, because the blend is 19.4 h NEWER than the
# file whose motion it does not contain.  Read the KEYS.
echo; echo "######## 0/4  the car's keys, against anim/carrig"
$B -b "$CAR" --factory-startup -noaudio -P tools/car_staleness.py -- --keys \
   > $W/keys_film24_car.log 2>&1
grep -a "CAR KEYS\|STAGE RESULT" $W/keys_film24_car.log
grep -qa "STAGE RESULT: CAR_KEYS_MATCH_SOURCE" $W/keys_film24_car.log || {
  echo ">> STAGE RESULT: REBUILD24_FAIL (the car this film would append is STALE)"
  exit 11; }

SHA=$(python3 -c "import hashlib;print(hashlib.sha256(open('$SHEET','rb').read()).hexdigest()[:16])")
echo ">> $SHEET sha256[:16] = $SHA"
[ "$SHA" = "1abee787a8044f35" ] || {
  echo ">> STAGE RESULT: REBUILD24_FAIL (sheet is $SHA, not the live 1abee787a8044f35)"
  exit 11; }

python3 - <<'PY'
import re
p = "render/world/assembly/r2/SHIPPING.md"
s = open(p).read()
s2, n = re.subn(r"\*\*`assembly\d+\.blend`", "**`assembly14.blend`", s, count=1)
if n != 1:
    raise SystemExit("REFUSING: could not rewrite the SHIPPING.md declaration")
if s2 != s:
    open(p, "w").write(s2)
    print(">> SHIPPING.md rewritten to declare assembly14.blend")
else:
    print(">> SHIPPING.md already declares assembly14.blend (unchanged)")
PY
DECL=$(python3 tools/shipping_world.py 2>&1)
echo ">> shipping_world declares: $DECL"
case "$DECL" in *assembly14.blend) ;; *) echo ">> STAGE RESULT: REBUILD24_FAIL (declaration)"; exit 11 ;; esac

# THE SOURCE FINGERPRINT.  v127's list PLUS docs/beat_sheet.json, which was not
# in it -- and the sheet is the one input this film exists to pick up, so its
# absence from the record would have made the film's provenance unreadable.
{
  echo "=== SOURCE, hashed at $(date -Is) ==="
  sha256sum "$SHEET" telemetry/telemetry.csv docs/circuit_spec.json \
            anim/build_camera_rig.py anim/carpath.py anim/carrig.py \
            sim/apply_breach.py world/showroom_lighting.py world/showroom_strip.py \
            tools/build_film_scene.py tools/r2791_apply_focus.py \
            "$ASM" "$CAR" 2>&1
} > $W/inputs_film24.txt
cat $W/inputs_film24.txt

waitmem () {
  for i in $(seq 1 960); do
    A=$(free -g | awk '/^Mem:/{print $7}')
    [ "$A" -ge 5 ] && { echo "[gate] ${A} GB available, starting $1"; return 0; }
    [ $((i % 10)) -eq 1 ] && echo "[gate] $1 waiting: ${A} GB available (need 5)"
    sleep 30
  done
  echo "[gate] TIMEOUT before $1"; return 1
}

judge () {   # judge <log> <pass-token> <stage-name>
  local log="$1" tok="$2" name="$3"
  if ! grep -qa "$tok" "$log"; then
    echo ">> STAGE RESULT: REBUILD24_FAIL ($name: no '$tok' in $log)"; return 1
  fi
  local badline
  badline=$(grep -aE "STAGE RESULT: [A-Z0-9_]*(FAIL|UNSOUND|REFUS)" "$log" | head -3)
  if [ -n "$badline" ]; then
    echo ">> TWO-VERDICT TRAP: $name printed a failing verdict as well:"
    echo "$badline"
    echo ">> STAGE RESULT: REBUILD24_FAIL ($name: unread failing verdict)"; return 1
  fi
  return 0
}

# ---------------------------------------------------------------------------
# THE ONE JUDGEMENT CALL IN THIS FILE, STATED RATHER THAN BURIED.
#
# `build_film_scene.report_world_staleness` (R2-1822) REFUSES to build on a
# world that is not what its own source would produce.  film23 passed it clean
# at 06:10 -- "assembly14.blend matches its recorded source fingerprint over 10
# module(s)".  IT NO LONGER DOES.  Measured today, 2 of those 10 differ:
#
#     world/build_surface.py   assembly14 read 678fdb3f, source is now 9b5d6fb2
#                              (a LANDED, committed change: R2-3061..R2-3066,
#                              the asphalt re-budget and its partial revert)
#     world/build_terrain.py   assembly14 read 991b15a0, HEAD is 258048f7 and
#                              the worktree is d09ac2a8 -- i.e. assembly14 was
#                              built from a state of that file that NEVER
#                              LANDED, and there are 1,101 uncommitted lines in
#                              it right now belonging to another agent
#
# So THE WORLD IS STALE, and that is a real, newly-opened finding -- it is NOT
# an artefact of this rebuild and it was true of film23 the moment those two
# modules moved.  Two ways to clear it and only one is honest here:
#
#   REBUILD assembly14.  REJECTED, and not on cost.  `build_terrain.py` carries
#   1,101 uncommitted lines of somebody else's in-flight work; rebuilding the
#   world now would bake unlanded source into the ship candidate, which is a
#   worse instance of exactly the defect this gate exists to prevent.  It would
#   also change the world under a film whose whole purpose is to isolate the
#   car and the camera, so beat 6's before/after would stop being a comparison.
#
#   OVERRIDE, with the reason on the record.  TAKEN.  film24 is deliberately
#   built on THE SAME WORLD ARTEFACT film23 was, so the only differences between
#   the two films are the two named above.
#
# THIS IS NOT A CLEARED WARNING.  The world's staleness is unfixed, it is
# written up as its own prescription, and it must be closed by an assembly15
# BEFORE the 4K master -- not by this film.
OVERRIDE_REASON="R2-3361: film24 isolates the car and the camera and is built on the SAME assembly14 artefact as film23, deliberately, so beat 6's before/after is a comparison. assembly14 is stale against world/build_surface.py (landed R2-3061..R2-3066) and world/build_terrain.py (which assembly14 read in an UNLANDED state and which carries 1,101 uncommitted lines now). Rebuilding the world would bake another agent's unlanded work into the ship candidate. The world's staleness is a separate, open prescription for assembly15 and is NOT cleared by this override."

echo; echo "######## 1/4  build_film_scene -> render/film24.blend"
# BUILDLOCK, NOT JUST waitmem.  v127 used `waitmem` alone, which asks whether
# there is memory NOW and not whether somebody else is about to take it; on an
# 11 GB box with several agents live and a ~10 GB film append that is a race
# the OOM killer settles by shooting the biggest process, i.e. this one.  The
# big lane is FIFO.  Stage 4 is deliberately NOT wrapped: `verify_film24.sh`
# takes the same lock for the bar, and nesting it would deadlock.
waitmem film_scene || exit 90
bash tools/buildlock.sh r2-3361-film24-scene \
  $B -b "$ASM" --factory-startup -noaudio -P tools/build_film_scene.py -- \
    --out render/film24.blend --car "$CAR" --sheet "$SHEET" \
    --world-override "$OVERRIDE_REASON" > $W/build_film24.log 2>&1
echo "  rc=$?  (exit status is NOT the evidence)"
grep -aE "^>> |STAGE RESULT|REFUS|Traceback|WORLD STALENESS|showroom_strip" \
    $W/build_film24.log | tail -45
judge $W/build_film24.log ">> STAGE RESULT: FILM_SCENE_BUILT" "film24 scene" || exit 12
grep -qa "sky/camera bind CHECKED" $W/build_film24.log || {
  echo ">> STAGE RESULT: REBUILD24_FAIL (no sky rebind check)"; exit 13; }
grep -qa "showroom_strip: ADDED R2_Strip" $W/build_film24.log || {
  echo ">> STAGE RESULT: REBUILD24_FAIL (the strip source was not added)"
  grep -a "showroom_strip" $W/build_film24.log | tail -5; exit 13; }

# THE RIG MUST HAVE PICKED THE LIVE SHEET UP.  film22_path.json and
# film23_path.json are byte-identical (363e4e88b30207ad); if film24's comes out
# at that sha the in-process rig build did not read the sheet this film is for.
P24=$(sha256sum render/film24_path.json | cut -c1-16)
echo ">> render/film24_path.json sha16 = $P24"
[ "$P24" = "363e4e88b30207ad" ] && {
  echo ">> STAGE RESULT: REBUILD24_FAIL (the camera path is film22/film23's -- the rig did not read the live sheet)"
  exit 13; }
python3 - <<'PY'
import json, math, os, sys
# <<'PY' is the QUOTED heredoc form, so the shell expands nothing in here and
# $HOME would arrive at Python as four literal characters. Expand it in Python.
R2 = os.path.expanduser("~/f1-round2")
sys.path.insert(0, R2 + "/tools")
import lap_shotscale as LS
a = LS.load_path(R2 + "/render/film23_path.json")
b = LS.load_path(R2 + "/render/film24_path.json")
print(">> film24's camera vs film23's, per beat:")
moved = 0
for nm, lo, hi in LS.BEATS:
    w = max(math.dist(a[f]["p"], b[f]["p"]) for f in range(lo, hi + 1))
    l = max(abs(a[f]["lens"] - b[f]["lens"]) for f in range(lo, hi + 1))
    print("     %-12s d position %8.4f m   d lens %8.4f mm" % (nm, w, l))
    moved += (w > 0 or l > 0)
print(">> %d of 6 beats moved. Expected: beat 1 (re-paced payoff orbit) and "
      "beat 5 (re-pace); beat 6 already carried its closing lens." % moved)
PY

echo; echo "######## 2/4  focus"
waitmem focus || exit 90
bash tools/buildlock.sh r2-3361-film24-focus \
  $B -b render/film24.blend --factory-startup -noaudio -P tools/r2791_apply_focus.py -- \
   --grid work/r2840/depthgrid_R2842.json --report $W/focus_report_film24.json \
   --out render/film24.blend > $W/apply_focus24.log 2>&1
grep -aE "^>> |STAGE RESULT" $W/apply_focus24.log | tail -14
judge $W/apply_focus24.log "STAGE RESULT R2791_APPLY_OK" "focus" || exit 14

echo; echo "######## 3/4  breach + fines"
# The 10.9 GB bake is NOT redone: sim/breachlib.py reads the car only for beat 3
# (f865-1056), and the driver-car rebuild is EXACTLY 0.0 on every channel there.
bash tools/buildlock.sh r2-3361-film24-breach \
  bash $V8/build_breach24.sh render/film24.blend render/film24_breach.blend
BRC=$?
[ $BRC -eq 0 ] || { echo ">> STAGE RESULT: REBUILD24_FAIL (breach rc=$BRC)"; exit 15; }

echo; echo "######## 4/4  verify"
bash $V8/verify_film24.sh render/film24_breach.blend
VRC=$?

echo
AFTER23=$(sha256sum render/film23_breach.blend 2>/dev/null | cut -c1-16)
echo ">> film23_breach.blend sha16 AFTER this run: ${AFTER23:-absent}  (was ${BEFORE23:-absent})"
[ "$AFTER23" = "$BEFORE23" ] || { echo ">> STAGE RESULT: REBUILD24_FAIL (THIS RUN TOUCHED film23_breach.blend)"; exit 16; }
ls -la render/film24.blend render/film24_breach.blend render/film23_breach.blend 2>&1
[ $VRC -eq 0 ] && echo ">> STAGE RESULT: REBUILD24_COMPLETE" \
               || echo ">> STAGE RESULT: REBUILD24_BUILT_BAR_NOT_MET"
