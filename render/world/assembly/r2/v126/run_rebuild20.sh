#!/bin/bash
# film20 -- the film on assembly12, which is the first world carrying R2-1821's
# habitat/paving-extent fix (the client's "blank grass" note).  R2-1823.
#
# Waits for assembly12, promotes it in SHIPPING.md, then runs the same four
# stages film19 proved: scene -> focus -> breach(+fines) -> verify.  Every stage
# is judged only on its printed token; Blender 5.2 exits 0 on exceptions.
set -u
cd /home/zany/f1-round2
W=work/r21701
V=render/world/assembly/r2/v126
CAR=world/R21701_car_anim_driver_CS.blend
ASM=render/world/assembly/r2/assembly12.blend
B=/opt/blender-5.2.0-linux-x64/blender
mkdir -p $W
exec > >(tee -a $W/REBUILD20.log) 2>&1
echo "######################## R2-1823 film20 $(date -Is)"

for i in $(seq 1 240); do
  grep -q "STAGE RESULT: ASSEMBLY12_BUILT" $W/assembly12_stdout.txt 2>/dev/null && break
  if grep -qE "ASSEMBLY12_(FAIL|UNSOUND)" $W/assembly12_stdout.txt 2>/dev/null; then
    echo ">> STAGE RESULT: REBUILD20_FAIL (assembly12 did not build cleanly)"; exit 10
  fi
  [ $((i % 10)) -eq 1 ] && echo "[wait] $(date -Is) assembly12 not ready"
  sleep 30
done
[ -s "$ASM" ] || { echo ">> STAGE RESULT: REBUILD20_FAIL (no assembly12)"; exit 10; }
echo "[wait] assembly12 ready: $(ls -la $ASM)"

# Promote assembly12.  build_film_scene REFUSES an undeclared world, so this is
# a required step and not bookkeeping.
python3 - <<'PY'
import re
p = "render/world/assembly/r2/SHIPPING.md"
s = open(p).read()
s2, n = re.subn(r"\*\*`assembly\d+\.blend`", "**`assembly12.blend`", s, count=1)
if n != 1:
    raise SystemExit("REFUSING: could not rewrite the SHIPPING.md declaration")
open(p, "w").write(s2)
print(">> SHIPPING.md now declares assembly12.blend")
PY
DECL=$(python3 tools/shipping_world.py 2>&1)
echo ">> shipping_world declares: $DECL"
case "$DECL" in *assembly12.blend) ;; *) echo ">> STAGE RESULT: REBUILD20_FAIL (declaration)"; exit 11 ;; esac

echo; echo "######## 1/4  build_film_scene -> render/film20.blend"
A=$(free -g | awk '/^Mem:/{print $7}'); while [ "$A" -lt 5 ]; do sleep 30; A=$(free -g | awk '/^Mem:/{print $7}'); done
$B -b "$ASM" --factory-startup -noaudio -P tools/build_film_scene.py -- \
    --out render/film20.blend --car "$CAR" > $W/build_film20.log 2>&1
echo "  rc=$?  (exit status is NOT the evidence)"
grep -aE "^>> |STAGE RESULT|REFUS|Traceback|WORLD STALENESS" $W/build_film20.log | tail -40
grep -qa ">> STAGE RESULT: FILM_SCENE_BUILT" $W/build_film20.log || {
  echo ">> STAGE RESULT: REBUILD20_FAIL (film20 scene)"; exit 12; }
grep -qa "sky/camera bind CHECKED" $W/build_film20.log || {
  echo ">> STAGE RESULT: REBUILD20_FAIL (no sky rebind check)"; exit 13; }

echo; echo "######## 2/4  focus"
A=$(free -g | awk '/^Mem:/{print $7}'); while [ "$A" -lt 5 ]; do sleep 30; A=$(free -g | awk '/^Mem:/{print $7}'); done
$B -b render/film20.blend --factory-startup -noaudio -P tools/r2791_apply_focus.py -- \
   --grid work/r2840/depthgrid_R2842.json --report $W/focus_report_film20.json \
   --out render/film20.blend > $W/apply_focus20.log 2>&1
grep -aE "^>> |STAGE RESULT" $W/apply_focus20.log | tail -12
grep -qa "STAGE RESULT R2791_APPLY_OK" $W/apply_focus20.log || {
  echo ">> STAGE RESULT: REBUILD20_FAIL (focus)"; exit 14; }

echo; echo "######## 3/4  breach + fines"
sed -e 's#render/film19#render/film20#g' -e 's#apply_film19#apply_film20#g' \
    -e 's#breach19#breach20#g' -e 's#BREACH19#BREACH20#g' \
    $V/build_breach19.sh > $W/build_breach20.sh
bash $W/build_breach20.sh || { echo ">> STAGE RESULT: REBUILD20_FAIL (breach)"; exit 15; }

echo; echo "######## 4/4  verify"
bash $V/verify_film19.sh render/film20_breach.blend
VRC=$?
echo; ls -la render/film20.blend render/film20_breach.blend 2>&1
[ $VRC -eq 0 ] && echo ">> STAGE RESULT: REBUILD20_COMPLETE" \
               || echo ">> STAGE RESULT: REBUILD20_BUILT_BAR_NOT_MET"
