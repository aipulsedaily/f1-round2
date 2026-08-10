#!/bin/bash
# THE REST OF THE R2-1701 REBUILD, unattended.
#
#   film19.blend  ->  focus post-pass  ->  film19_breach.blend  ->  verify
#
# Waits for the car chain to deliver world/R21701_car_anim_driver_CS.blend, then
# runs the three build stages in order and the read-back at the end.  Every
# stage is judged ONLY on its printed token, because Blender 5.2 exits 0 on an
# uncaught exception.  Any stage that does not print its token STOPS the chain --
# a rebuild that carries on past a failed stage is how a change gets silently
# dropped, which is the whole thing this rebuild exists to correct.
#
# Progress: work/r21701/REBUILD.log      final state: the last STAGE RESULT line
set -u
cd /home/zany/f1-round2
W=work/r21701
V=render/world/assembly/r2/v126
CAR=world/R21701_car_anim_driver_CS.blend
B=/opt/blender-5.2.0-linux-x64/blender
mkdir -p $W
exec > >(tee -a $W/REBUILD.log) 2>&1

echo "######################## R2-1701 REBUILD $(date -Is)"

# ---------------------------------------------------------------- wait for car
# The car chain is serialised behind a Blender lock several other agents share,
# so this can legitimately sit here a while.  It waits rather than racing.
for i in $(seq 1 240); do
  [ -s "$CAR" ] && break
  [ $((i % 10)) -eq 1 ] && echo "[wait] $(date -Is) car not ready yet ($CAR)"
  sleep 30
done
if [ ! -s "$CAR" ]; then
  echo ">> STAGE RESULT: REBUILD_FAIL (car never arrived: $CAR)"; exit 10
fi
echo "[wait] car ready: $(ls -la $CAR)"

# ------------------------------------------------------------------- film19
echo; echo "######## 1/4  build_film_scene"
bash $V/build_film19.sh "$CAR" || { echo ">> STAGE RESULT: REBUILD_FAIL (film19)"; exit 11; }

# --------------------------------------------------------------- focus pass
# Manifest item: beat-1 focus, keyed to the SUBJECT rather than to frame
# numbers.  It is a post-pass on the film blend and it must run BEFORE
# apply_breach, because the breach applier writes the file the focus keys live
# in.  The depth grid is the re-paced one (R2-842), not the superseded dip-1.00
# grid beside it.
echo; echo "######## 2/4  r2791_apply_focus"
GRID=work/r2840/depthgrid_R2842.json
if [ ! -s "$GRID" ]; then
  echo ">> STAGE RESULT: REBUILD_FAIL (no depth grid $GRID)"; exit 12
fi
A=$(free -g | awk '/^Mem:/{print $7}')
while [ "$A" -lt 5 ]; do sleep 30; A=$(free -g | awk '/^Mem:/{print $7}'); done
$B -b render/film19.blend --factory-startup -noaudio \
   -P tools/r2791_apply_focus.py -- \
   --grid "$GRID" --report $W/focus_report_film19.json --out render/film19.blend \
   > $W/apply_focus19.log 2>&1
echo "  rc=$?  (exit status is NOT the evidence)"
grep -aE "^>> |STAGE RESULT|Traceback" $W/apply_focus19.log | tail -20
if ! grep -qa "STAGE RESULT R2791_APPLY_OK" $W/apply_focus19.log; then
  echo ">> STAGE RESULT: REBUILD_FAIL (focus pass)"; exit 13
fi

# -------------------------------------------------------------------- breach
echo; echo "######## 3/4  apply_breach WITH THE FINES"
bash $V/build_breach19.sh || { echo ">> STAGE RESULT: REBUILD_FAIL (breach)"; exit 14; }

# -------------------------------------------------------------------- verify
echo; echo "######## 4/4  verify"
bash $V/verify_film19.sh render/film19_breach.blend
VRC=$?

echo
echo "######################## DONE $(date -Is)  verify_rc=$VRC"
ls -la render/film19.blend render/film19_breach.blend 2>&1
if [ $VRC -eq 0 ]; then
  echo ">> STAGE RESULT: REBUILD_COMPLETE"
else
  echo ">> STAGE RESULT: REBUILD_BUILT_BAR_NOT_MET (see $W/REBUILD.log)"
fi
