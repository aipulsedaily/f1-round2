#!/usr/bin/env bash
# R2-116 -- re-gate the stale item test blends.
#
# WHAT THIS DOES AND WHY IT IS SHAPED THIS WAY
# -------------------------------------------
# `item_build_cmd.py --stale-census` reports 16 of 32 item test blends older
# than the source that built them.  That is SUSPECT, not a defect: an mtime says
# the source moved, not that the geometry did.  This script converts the
# suspicion into a measurement, per module:
#
#   1  FINGERPRINT the blend on disk NOW  (v120/vertex_fingerprint.py)
#   2  SOCKET AUDIT it                    (tools/socket_index_audit.py --blend)
#   3  REBUILD it through `item_build_cmd.py --item X --build`, which derives
#      the command from the MODULE'S OWN PARSER and then REQUIRES the target
#      file's sha256 to change.  Not `--test --save`: that assumption is R2-108.
#   4  FINGERPRINT the rebuilt blend
#   5  SOCKET AUDIT the rebuilt blend
#   6  fp_diff old new --expect-moved 0
#   7  DETERMINISM ARM -- build the module a SECOND time to a scratch path and
#      fp_diff the two REBUILDS against each other, --expect-moved 0.
#
# STEP 7 IS THE CONTROL WITHOUT WHICH STEP 6 MEANS NOTHING.  These modules are
# procedural.  If a module reseeds per run, a rebuild differs from ANY previous
# build and "the geometry moved" is not evidence that the SOURCE moved it -- it
# is evidence of an RNG.  Step 7 measures that directly on the same instrument:
#
#   step 7 PASS (build == build)  -> the instrument is measuring source change,
#                                    so step 6's verdict is a MEASUREMENT.
#   step 7 FAIL (build != build)  -> the module is nondeterministic, and step 6
#                                    is NOT MEASURED for that module, in either
#                                    direction.  It is not a pass and it is not
#                                    a fail.
#
# AND IT IS SKIPPED WHEN STEP 6 REPORTED EVERY OBJECT BIT-IDENTICAL, because in
# that case it is already answered: a module that reseeds per run cannot
# reproduce a build made days earlier bit for bit on every object.  Determinism
# is ENTAILED by that result, not assumed away, and the row records
# DETERMINISM_ENTAILED_BY_BIT_IDENTITY so no reader has to reconstruct the
# argument.  When ANY object moved the arm RUNS -- that is precisely the case
# where the entailment does not hold.
#
# The shortcut was validated before it was used, on `spectator_seated`, which
# was run BOTH ways: 803 of 803 objects identical to the 07-29 build AND the
# determinism arm run anyway -- 803 of 803 identical again, rc 0.  The arm
# agreed with the entailment it replaces on the one module where both were
# measured.
#
# Step 6's declared expectation IS the null hypothesis under test: "the source
# moved but the geometry did not".  fp_diff FAILing is the finding.  A bare
# fp_diff run asserts nothing and exits 3 (R2-111), so an expectation is always
# declared on both arms.
#
# Blender 5.2 exits 0 on an uncaught script exception (R2-108), so nothing here
# is judged on $? alone: every stage's STAGE RESULT / verdict line is stored and
# read back from the artefact it claims to have produced.
set -u
ROOT=/home/zany/f1-round2
W=$ROOT/work/r2116
SCRATCH=$W/scratch
BL=/opt/blender-5.2.0-linux-x64/blender
VF=$ROOT/render/world/assembly/r2/v120/vertex_fingerprint.py
FPD=$ROOT/render/world/assembly/r2/v120/fp_diff.py
mkdir -p "$W/fp" "$W/logs" "$SCRATCH"

for m in "$@"; do
  B=$ROOT/world/items/${m}_test.blend
  echo "=========================== $m ==========================="
  # -- 1  fingerprint the blend as it stands (do NOT recompute if we have it) --
  if [ ! -s "$W/fp/${m}_before.json" ]; then
    "$BL" -b "$B" --factory-startup -P "$VF" -- "$W/fp/${m}_before.json" \
      > "$W/logs/${m}_fp_before.log" 2>&1
  fi
  sha_before=$(sha256sum "$B" | cut -c1-16)

  # -- 3  rebuild in place; command derived from the module's own parser -------
  ( cd "$ROOT" && timeout 10800 /usr/bin/python3 tools/item_build_cmd.py \
      --item "$m" --build ) > "$W/logs/${m}_build.log" 2>&1
  rc=$?
  sha_after=$(sha256sum "$B" | cut -c1-16)
  echo "$m BUILD rc=$rc  sha $sha_before -> $sha_after"
  /usr/bin/grep -E "^>> STAGE RESULT" "$W/logs/${m}_build.log" | tail -2
  if [ $rc -ne 0 ]; then
    echo "$m BUILD DID NOT LAND"
    continue
  fi

  # -- 4  fingerprint the rebuild ---------------------------------------------
  "$BL" -b "$B" --factory-startup -P "$VF" -- "$W/fp/${m}_after.json" \
    > "$W/logs/${m}_fp_after.log" 2>&1
  # -- 5  socket audit the rebuild --------------------------------------------
  ( cd "$ROOT" && /usr/bin/python3 tools/socket_index_audit.py --blend "$B" ) \
    > "$W/after_${m}.txt" 2>&1
  echo "$m SOCKET_AFTER rc=$?"
  # -- 6  did the geometry move between the stale blend and the rebuild? -------
  ( cd "$ROOT" && /usr/bin/python3 "$FPD" \
      "$W/fp/${m}_before.json" "$W/fp/${m}_after.json" --expect-moved 0 ) \
    > "$W/logs/${m}_fpdiff.log" 2>&1
  echo "$m FPDIFF_BEFORE_AFTER rc=$?"
  /usr/bin/grep -E "MOVED:|BIT-IDENT|STAGE RESULT" "$W/logs/${m}_fpdiff.log"

  # -- 7  DETERMINISM CONTROL, only where step 6 does not already answer it ---
  if /usr/bin/grep -qE "vertex set MOVED: 0 of " "$W/logs/${m}_fpdiff.log"; then
    echo "$m DETERMINISM_ENTAILED_BY_BIT_IDENTITY -- every object is identical"
    echo "   to a build made before the source moved; an RNG could not do that."
    continue
  fi
  S=$SCRATCH/${m}_ctl.blend
  rm -f "$S"
  ( cd "$ROOT" && timeout 10800 /usr/bin/python3 tools/item_build_cmd.py \
      --item "$m" --build --out "$S" ) > "$W/logs/${m}_build2.log" 2>&1
  rc2=$?
  echo "$m BUILD2 rc=$rc2"
  if [ $rc2 -ne 0 ] || [ ! -s "$S" ]; then
    echo "$m DETERMINISM ARM DID NOT RUN -- step 6 is NOT MEASURED"
    continue
  fi
  "$BL" -b "$S" --factory-startup -P "$VF" -- "$W/fp/${m}_ctl.json" \
    > "$W/logs/${m}_fp_ctl.log" 2>&1
  ( cd "$ROOT" && /usr/bin/python3 "$FPD" \
      "$W/fp/${m}_after.json" "$W/fp/${m}_ctl.json" --expect-moved 0 ) \
    > "$W/logs/${m}_determinism.log" 2>&1
  echo "$m DETERMINISM rc=$?"
  /usr/bin/grep -E "MOVED:|BIT-IDENT|STAGE RESULT" "$W/logs/${m}_determinism.log"
  rm -f "$S"
done
