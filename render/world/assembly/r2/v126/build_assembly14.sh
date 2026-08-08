#!/bin/bash
# assembly14 -- the world carrying R2-2041's TYRE DEPOSIT on the pit-exit apron.
#
# WHY A WORLD REBUILD FOR A MATERIAL CHANGE: `_mat_concrete` is built by
# `world/build_surface.py`, which runs inside `assemble.py`.  There is no
# cheaper artefact -- editing the material into an existing assembly would make
# a derivative blend, and NEXT-REBUILD's standing rule is that a derivative
# blend is evidence, not an artefact.  The build runs the source, once.
#
# WHAT CHANGED, AND NOTHING ELSE DID:
#   world/build_surface.py  `_mat_concrete` loses round 1's five-line painted
#                           launch streak and gains `world/items/tyre_deposit.py`'s
#                           derived field at `Traffic Passes = 1000`, signed off
#                           at R2-1226.  No geometry moves: the same 35,904
#                           quads carry the same material name.
# assembly13's own two acceptance numbers are re-asserted below UNCHANGED, so
# this build has to prove it carried the new fix AND did not regress the last
# one.  That is the check assembly11 did not have (R2-1826).
set -u
cd /home/zany/f1-round2
D=work/r22041
mkdir -p $D
OUT=/home/zany/f1-round2/render/world/assembly/r2/assembly14.blend
SRC="world/world_contract.py world/build_surface.py world/build_barriers.py
     world/build_architecture.py world/build_terrain.py world/build_dressing.py
     world/build_items.py world/itemkit.py world/items/PLACEMENT.json
     world/items/tyre_deposit.py
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

sha256sum $SRC > $D/inputs_assembly14_BEFORE.txt 2>&1
{ echo "=== INPUTS, hashed at $(date -Is) ==="; cat $D/inputs_assembly14_BEFORE.txt
  git -C /home/zany/f1-round2 rev-parse HEAD
  git -C /home/zany/f1-round2 status --short; } > $D/inputs_assembly14.txt 2>&1

waitmem assemble || exit 90
START=$(date +%s)
/opt/blender-5.2.0-linux-x64/blender -b -noaudio --factory-startup \
    -P render/world/assembly/r2/assemble.py -- --out=$OUT \
    > $D/build_assembly14.log 2>&1
RC=$?
END=$(date +%s)
echo "exit=$RC seconds=$((END-START))" | tee -a $D/inputs_assembly14.txt
ls -la $OUT >> $D/inputs_assembly14.txt 2>&1

sha256sum $SRC > $D/inputs_assembly14_AFTER.txt 2>&1

# `$?` IS WORTHLESS -- Blender 5.2 exits 0 on an uncaught script exception.
TOKEN=$(grep -o '>> STAGE RESULT: [A-Z_]*' $D/build_assembly14.log | tail -1)
echo "seconds=$((END-START)) rc=$RC  $TOKEN"
grep -E '^\[ASM\] [a-z]+: ok=' $D/build_assembly14.log || true
grep -E '^>> tyre deposit:' $D/build_assembly14.log || true

# THE MID-BUILD SOURCE GUARD (R2-1822).
if ! diff -q $D/inputs_assembly14_BEFORE.txt $D/inputs_assembly14_AFTER.txt >/dev/null; then
  echo ">> SOURCE MOVED DURING THE BUILD:"
  diff $D/inputs_assembly14_BEFORE.txt $D/inputs_assembly14_AFTER.txt | grep '^[<>]'
  echo ">> STAGE RESULT: ASSEMBLY14_UNSOUND (its own inputs changed under it;"
  echo "   the artefact may carry a mixture of two source states -- rebuild)"
  exit 7
fi
echo ">> inputs identical before and after: the build read one source state"

if [ "$TOKEN" != ">> STAGE RESULT: ASSEMBLE_OK" ]; then
  echo ">> STAGE RESULT: ASSEMBLY14_FAIL"
  exit 8
fi

# ---------------------------------------------------------------------------
# ACCEPTANCE, ASKED OF THE OUTPUT RATHER THAN THE INPUT (R2-1826).
python3 - <<'PY'
import json
p = "render/world/assembly/r2/assembly14_build.json"
try:
    mods = json.load(open(p))["mods"]
    t = mods["terrain"]["summary"]
    s = mods["surface"]["summary"]
except Exception as e:
    print(">> STAGE RESULT: ASSEMBLY14_UNVERIFIED (%s)" % e); raise SystemExit(1)
ok = True
def chk(d, k, want, note=""):
    global ok
    got = d.get(k)
    good = (got == want)
    ok = ok and good
    print("  %-32s want %-12s got %-12s %s %s"
          % (k, want, got, "OK" if good else "FAIL", note))

# --- the NEW fix must be present
chk(s, "tyre_deposit_traffic_passes", 1000.0, "(R2-1226, signed off)")
chk(s, "tyre_deposit_front_x_keys", 248, "(the wipe; <2 = laid on frame 1)")
chk(s, "tyre_deposit_material", "M_Surf_Concrete", "(the apron)")
# --- and the geometry must NOT have moved with it
chk(s, "access_quads", 35904, "(the apron; a material fix moves no quads)")
chk(s, "triangles", 2721433, "(bit-identity of the surface build)")
# --- and assembly13's acceptance must still hold
chk(t, "sward_C", 56063, "(assembly13's number; MUST NOT regress)")
chk(t, "grass_in_corridor", 1386383, "(1,370,543 = R2-1821's holes are back)")
print(">> STAGE RESULT: %s"
      % ("ASSEMBLY14_FIXES_PRESENT" if ok else "ASSEMBLY14_FIXES_ABSENT"))
raise SystemExit(0 if ok else 1)
PY
