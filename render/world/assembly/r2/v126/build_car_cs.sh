#!/bin/bash
# STEP A of the R2-1701 rebuild -- compose the cockpit-surface pass onto the
# correctly-paced car.
#
# WHY NOT JUST PROMOTE `work/r2881/car_anim_driver_R2881_BOTH.blend`, as
# docs/NEXT-REBUILD.md line 11 says?  Because that manifest line is STALE, and
# measuring the candidates says so:
#
#   world/R2829_car_anim_driver.blend        BOTH.blend
#   ---------------------------------------  ------------------------------
#   paint v5 + imperfections (in order)  YES  YES
#   helmet crown fix                     YES  YES
#   cockpit surface (`r2cs`)             NO   YES      <- the only thing missing
#   beat-1 re-pace / driver appear f400  YES  NO (f580, the OLD schedule)
#
# BOTH.blend was built off `world/car_anim.blend` (Aug 4), whose beat-1 assembly
# predates the re-pace: all 15 clusters seat 60-180 frames later, and its own
# sidecar records `appear_frame: 580`.  Promoting it would silently revert the
# beat-1 re-pace and violate "Order matters" items 3 and 4 -- the driver would
# pop in dead centre of a clean 6.7 m wide.  R2829 is the only correct parent.
#
# The staging doc that produced BOTH anticipated exactly this
# (docs/STAGING-R2-881-to-R2-910.md:433): "Whoever promotes should build from
# this one, OR re-run cockpit_surface.py on whatever driver-fixed car is
# current -- not promote either half alone."  This is that second path.
#
# Safe by construction: cockpit_surface.py is a material/shading-attribute pass
# with a static-geometry guarantee, its FAIL_ALREADY_APPLIED guard keys on
# `r2cs` (which R2829 does not carry), and --out refuses to overwrite its input.
set -u
cd /home/zany/f1-round2
W=work/r21701
mkdir -p $W
B=/opt/blender-5.2.0-linux-x64/blender
IN=world/R2829_car_anim_driver.blend
OUT=world/R2829_car_anim_driver_CS.blend

{
  echo "=== INPUTS, hashed at $(date -Is) ==="
  sha256sum $IN tools/cockpit_surface.py world/car_paint.py tools/imperfections.py
} > $W/inputs_car_cs.txt 2>&1
cat $W/inputs_car_cs.txt

START=$(date +%s)
$B -b "$IN" --factory-startup -noaudio -P tools/cockpit_surface.py -- \
    --out "$OUT" --strength 1.0 --json docs/r21701_cockpit_surface.json \
    > $W/car_cs.log 2>&1
RC=$?
echo "exit=$RC seconds=$(( $(date +%s) - START ))   (exit status is NOT the evidence)"
grep -E "^>> |STAGE RESULT|FAIL|REFUS|Traceback|strip|inject" $W/car_cs.log | tail -30
ls -la "$OUT" 2>&1

# Blender 5.2 exits 0 on an uncaught exception.  Judge on the token only.
TOKEN=$(grep -o '>> STAGE RESULT: [A-Z0-9_]*' $W/car_cs.log | tail -1)
echo "TOKEN=$TOKEN"
case "$TOKEN" in
  *COCKPIT_SURFACE_OK) echo ">> STAGE RESULT: CAR_CS_BUILT" ;;
  *)                   echo ">> STAGE RESULT: CAR_CS_FAIL ($TOKEN)" ;;
esac
