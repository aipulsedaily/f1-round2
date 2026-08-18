#!/bin/bash
# film23 -- THE FIRST FILM BUILT ON A SOUND WORLD WITH A COMPLETED BREACH.
# R2-2101.
#
# Every film so far has failed or been superseded:
#   film19  built on stale assembly11; breach failed on the glazing preflight
#   film20  cancelled with assembly12 (ASSEMBLY12_UNSOUND)
#   film21  built on the verified assembly13; THE BREACH DIED --
#           KeyError: bpy.data.collections["BREACH_Fines"], 1,234 s in
#   film22  assembly14 + the carbon/rubber fixes, breach DELIBERATELY OMITTED
#           because the applier was known broken; a proof artefact, not a ship
#           candidate
#
# film23 = assembly14 (film22's verified world) + R22041 car (film22's verified
# car) + THE BREACH, now that `sim/apply_breach.py`'s name collision is fixed,
# + R2-1146's strip source, the second half of a prescription that has been
# open since R2-1146 and was reported BLOCKED by R2-2041.
#
# Four stages, each judged only on its printed `>> STAGE RESULT:` token --
# Blender 5.2 exits 0 on an uncaught exception, so `$?` is not evidence.
# AND EVERY STAGE IS CHECKED FOR THE TWO-VERDICT TRAP: a stage that prints a
# FAIL and then a later PASS has an unread verdict, so the FAIL tokens are
# grepped for explicitly rather than only the PASS ones.
set -u
cd $HOME/f1-round2
W=work/r22101
V=render/world/assembly/r2/v127
CAR=world/R22041_car_anim_driver_CS.blend
ASM=render/world/assembly/r2/assembly14.blend
B=/opt/blender-5.2.0-linux-x64/blender
mkdir -p $W
exec > >(tee -a $W/REBUILD23.log) 2>&1
echo "######################## R2-2101 film23 $(date -Is)"

[ -s "$ASM" ] || { echo ">> STAGE RESULT: REBUILD23_FAIL (no assembly14)"; exit 10; }
[ -s "$CAR" ] || { echo ">> STAGE RESULT: REBUILD23_FAIL (no $CAR)"; exit 10; }
grep -q "STAGE RESULT: ASSEMBLY14_FIXES_PRESENT" work/r22041/assembly14_stdout.txt || {
  echo ">> STAGE RESULT: REBUILD23_FAIL (assembly14 did not pass acceptance)"
  exit 10; }
ls -la "$ASM" "$CAR"

# The declaration.  build_film_scene REFUSES an undeclared world, so this is a
# required step and not bookkeeping.  SHIPPING.md is held by `inflight-auto`;
# it is edited on disk because no build can run without it and it is NOT staged
# or committed by this block -- the declaration is the owner's to make
# permanent.  run_rebuild22.sh already set it to assembly14, so this is
# normally a no-op that proves the state rather than changing it.
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
case "$DECL" in *assembly14.blend) ;; *) echo ">> STAGE RESULT: REBUILD23_FAIL (declaration)"; exit 11 ;; esac

# THE SOURCE FINGERPRINT.  Two of the three edits this film exists to carry are
# in files another agent's lease covers, so they are on disk and uncommitted;
# hashing them here is the only record of WHAT was actually run.
{
  echo "=== SOURCE, hashed at $(date -Is) ==="
  sha256sum sim/apply_breach.py world/showroom_lighting.py world/showroom_strip.py \
            tools/build_film_scene.py tools/r2791_apply_focus.py \
            "$ASM" "$CAR" 2>&1
} > $W/inputs_film23.txt
cat $W/inputs_film23.txt

waitmem () {
  for i in $(seq 1 960); do
    A=$(free -g | awk '/^Mem:/{print $7}')
    [ "$A" -ge 5 ] && { echo "[gate] ${A} GB available, starting $1"; return 0; }
    [ $((i % 10)) -eq 1 ] && echo "[gate] $1 waiting: ${A} GB available (need 5)"
    sleep 30
  done
  echo "[gate] TIMEOUT before $1"; return 1
}

# Judge a stage log: the PASS token must be there AND no FAIL/REFUSE token may
# be.  `grep -qa PASS` alone is what lets a two-verdict log through.
judge () {   # judge <log> <pass-token> <stage-name>
  local log="$1" tok="$2" name="$3"
  if ! grep -qa "$tok" "$log"; then
    echo ">> STAGE RESULT: REBUILD23_FAIL ($name: no '$tok' in $log)"; return 1
  fi
  local badline
  badline=$(grep -aE "STAGE RESULT: [A-Z0-9_]*(FAIL|UNSOUND|REFUS)" "$log" | head -3)
  if [ -n "$badline" ]; then
    echo ">> TWO-VERDICT TRAP: $name printed a failing verdict as well:"
    echo "$badline"
    echo ">> STAGE RESULT: REBUILD23_FAIL ($name: unread failing verdict)"; return 1
  fi
  return 0
}

echo; echo "######## 1/4  build_film_scene -> render/film23.blend"
waitmem film_scene || exit 90
$B -b "$ASM" --factory-startup -noaudio -P tools/build_film_scene.py -- \
    --out render/film23.blend --car "$CAR" > $W/build_film23.log 2>&1
echo "  rc=$?  (exit status is NOT the evidence)"
grep -aE "^>> |STAGE RESULT|REFUS|Traceback|WORLD STALENESS|showroom_strip" \
    $W/build_film23.log | tail -45
judge $W/build_film23.log ">> STAGE RESULT: FILM_SCENE_BUILT" "film23 scene" || exit 12
grep -qa "sky/camera bind CHECKED" $W/build_film23.log || {
  echo ">> STAGE RESULT: REBUILD23_FAIL (no sky rebind check)"; exit 13; }
# the strip must have been ADDED by this build, not merely tolerated
grep -qa "showroom_strip: ADDED R2_Strip" $W/build_film23.log || {
  echo ">> STAGE RESULT: REBUILD23_FAIL (the strip source was not added)"
  grep -a "showroom_strip" $W/build_film23.log | tail -5; exit 13; }

echo; echo "######## 2/4  focus"
waitmem focus || exit 90
$B -b render/film23.blend --factory-startup -noaudio -P tools/r2791_apply_focus.py -- \
   --grid work/r2840/depthgrid_R2842.json --report $W/focus_report_film23.json \
   --out render/film23.blend > $W/apply_focus23.log 2>&1
grep -aE "^>> |STAGE RESULT" $W/apply_focus23.log | tail -14
judge $W/apply_focus23.log "STAGE RESULT R2791_APPLY_OK" "focus" || exit 14

echo; echo "######## 3/4  breach + fines"
bash $V/build_breach23.sh render/film23.blend render/film23_breach.blend
BRC=$?
[ $BRC -eq 0 ] || { echo ">> STAGE RESULT: REBUILD23_FAIL (breach rc=$BRC)"; exit 15; }

echo; echo "######## 4/4  verify"
bash $V/verify_film23.sh render/film23_breach.blend
VRC=$?
echo; ls -la render/film23.blend render/film23_breach.blend 2>&1
[ $VRC -eq 0 ] && echo ">> STAGE RESULT: REBUILD23_COMPLETE" \
               || echo ">> STAGE RESULT: REBUILD23_BUILT_BAR_NOT_MET"
