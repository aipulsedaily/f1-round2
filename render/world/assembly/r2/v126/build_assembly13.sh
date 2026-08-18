#!/bin/bash
# assembly13 -- the world AGAIN, for R2-1821's habitat/paving-extent fix.
#
# WHY A SECOND WORLD REBUILD 50 MINUTES AFTER THE FIRST:
# assembly11 read `world/build_terrain.py` at ~22:06 and the file was rewritten
# at 22:25:31 -- DURING assembly11's own terrain stage.  `world_contract.py`
# changed at 22:16:29, also mid-build.  assembly11 therefore carries R2-1661's
# ground pass and NOT R2-1821's, and its own summary proves it to the unit:
# `sward_drifts: 264890` is R2-1661's figure exactly.
#
# THE STALENESS INSTRUMENT CANNOT SEE THIS, AND THAT IS THE POINT.
# `report_world_staleness` compares the assembly's mtime against each module's
# mtime.  assembly11 was SAVED at 22:40, after build_terrain's 22:25, so the
# comparison reads FRESH while the build is stale -- because the module was READ
# at 22:06, 19 minutes before it changed.  A save-time comparison cannot detect
# a source edit that lands mid-build.  Hence the guard below: the inputs are
# hashed BEFORE and AFTER, and a build whose own sources moved under it is
# reported as UNSOUND rather than saved as if nothing happened.
set -u
cd $HOME/f1-round2
D=work/r21701
mkdir -p $D
OUT=$HOME/f1-round2/render/world/assembly/r2/assembly13.blend
SRC="world/world_contract.py world/build_surface.py world/build_barriers.py
     world/build_architecture.py world/build_terrain.py world/build_dressing.py
     world/build_items.py world/itemkit.py world/items/PLACEMENT.json
     render/world/assembly/r2/assemble.py telemetry/telemetry.csv"

waitmem () {
  for i in $(seq 1 960); do
    A=$(free -g | awk '/^Mem:/{print $7}')
    [ "$A" -ge 5 ] && { echo "[gate] ${A} GB available, starting $1"; return 0; }
    [ $((i % 10)) -eq 1 ] && echo "[gate] $1 waiting: ${A} GB available (need 5)"
    sleep 30
  done
  echo "[gate] TIMEOUT before $1"; return 1
}

sha256sum $SRC > $D/inputs_assembly13_BEFORE.txt 2>&1
{ echo "=== INPUTS, hashed at $(date -Is) ==="; cat $D/inputs_assembly13_BEFORE.txt
  git -C $HOME/f1-round2 rev-parse HEAD
  git -C $HOME/f1-round2 status --short; } > $D/inputs_assembly13.txt 2>&1

waitmem assemble || exit 90
START=$(date +%s)
/opt/blender-5.2.0-linux-x64/blender -b -noaudio --factory-startup \
    -P render/world/assembly/r2/assemble.py -- --out=$OUT \
    > $D/build_assembly13.log 2>&1
RC=$?
END=$(date +%s)
echo "exit=$RC seconds=$((END-START))" | tee -a $D/inputs_assembly13.txt
ls -la $OUT >> $D/inputs_assembly13.txt 2>&1

sha256sum $SRC > $D/inputs_assembly13_AFTER.txt 2>&1

# `$?` IS WORTHLESS -- Blender 5.2 exits 0 on an uncaught script exception.
TOKEN=$(grep -o '>> STAGE RESULT: [A-Z_]*' $D/build_assembly13.log | tail -1)
echo "seconds=$((END-START)) rc=$RC  $TOKEN"
grep -E '^\[ASM\] [a-z]+: ok=' $D/build_assembly13.log || true

# THE MID-BUILD SOURCE GUARD.  This is the check assembly11 did not have.
if ! diff -q $D/inputs_assembly13_BEFORE.txt $D/inputs_assembly13_AFTER.txt >/dev/null; then
  echo ">> SOURCE MOVED DURING THE BUILD:"
  diff $D/inputs_assembly13_BEFORE.txt $D/inputs_assembly13_AFTER.txt | grep '^[<>]'
  echo ">> STAGE RESULT: ASSEMBLY13_UNSOUND (its own inputs changed under it;"
  echo "   the artefact may carry a mixture of two source states -- rebuild)"
  exit 7
fi
echo ">> inputs identical before and after: the build read one source state"

if [ "$TOKEN" = ">> STAGE RESULT: ASSEMBLE_OK" ]; then
  echo ">> STAGE RESULT: ASSEMBLY13_BUILT"
else
  echo ">> STAGE RESULT: ASSEMBLY13_FAIL"
fi

# ---------------------------------------------------------------------------
# ACCEPTANCE, ASKED OF THE OUTPUT RATHER THAN THE INPUT (R2-1826).
# The fingerprint guard above asks "did the source move under the build".  This
# asks the complementary question: "did the fixes actually reach the geometry".
# sward C must FALL 65,100 -> 56,063 (tier C's outward fade replacing the hard
# cut at 1076 m), and grass_in_corridor must be EXACTLY 1,386,383 -- a buggy
# intermediate read 1,370,543 because the verge taper reached inside the
# corridor through two holes.  If that number moves, the holes are back.
python3 - <<'PY'
import json, sys
p = "render/world/assembly/r2/assembly13_build.json"
try:
    t = json.load(open(p))["mods"]["terrain"]["summary"]
except Exception as e:
    print(">> STAGE RESULT: ASSEMBLY13_UNVERIFIED (%s)" % e); raise SystemExit(1)
ok = True
def chk(k, want, direction=""):
    global ok
    got = t.get(k)
    good = (got == want)
    ok = ok and good
    print("  %-22s want %-12s got %-12s %s %s"
          % (k, want, got, "OK" if good else "FAIL", direction))
chk("sward_C", 56063, "(was 65,100 pre-fix; MUST fall)")
chk("grass_in_corridor", 1386383, "(MUST be identical; 1,370,543 = holes back)")
print(">> STAGE RESULT: %s"
      % ("ASSEMBLY13_FIXES_PRESENT" if ok else "ASSEMBLY13_FIXES_ABSENT"))
raise SystemExit(0 if ok else 1)
PY
