#!/usr/bin/env bash
# Relief sweep over every built item witness blend.  See tools/relief_audit.py.
#
# TWO DEFECTS FIXED HERE ON 2026-08-03 (R2-116).  Both are the same shape as
# R2-072: a check that quietly stops checking.
#
# 1  IT COULD NEVER REFRESH A STALE REPORT.  The loop said
#
#        [ -f "$OUT/$it.json" ] && { echo "HAVE $it"; continue; }
#
#    so the ONLY thing that made it re-run an item was the report not existing.
#    Every witness blend under render/gate_witness/ was rebuilt on 2026-08-03
#    between 12:19 and 18:46, and 28 of the 30 reports predate their own
#    witness.  Running this file over that corpus printed `HAVE` thirty times
#    and exited 0 -- a full sweep, no work done, no way to tell from the
#    output.  And the numbers are not close: on the two items that HAVE been
#    re-run, `pont_girder` went m_max 0.00272 -> 8.273 with Height-unlinked
#    stages 5 -> 0, and `gantry_truss` 0.00586 -> 8.073.
#
#    A report is skipped now only when it is NEWER than the witness it
#    describes.  A stale one is SUPERSEDED (renamed
#    `<item>_SUPERSEDED_pre_R2038witness.json`, the convention already in use
#    in that directory) and re-run.  `--force` re-runs regardless.
#
# 2  IT CALLED BARE `blender`.  That resolves to /usr/bin/blender, which this
#    project's standing rules exclude -- it has no CUDA kernels.  relief_audit
#    does not render, so this did not corrupt a result, but the next tool
#    copied off this line would.
#
# BEFORE YOU BELIEVE A SWEEP, WATCH THE INSTRUMENT FAIL:
#     blender -b --factory-startup -P tools/relief_audit_control.py -- --selftest
# builds a Bump driven by a procedural texture and the same graph with that one
# Height link removed, and requires relief_audit to separate them.  Measured
# 2026-08-03: positive m_max 7.67173, height-unlinked 0; negative m_max none,
# height-unlinked 1.
#
# Exit codes (tools/gate_exit.py's scheme): 0 all rows current, 1 a row failed,
# 2 could not run.
set -u
cd $HOME/f1-round2
BL=/opt/blender-5.2.0-linux-x64/blender
OUT="render/items/_relief"
mkdir -p "$OUT"

FORCE=0
ONLY=""
while [ $# -gt 0 ]; do
  case "$1" in
    --force) FORCE=1 ;;
    --only)  shift; ONLY="$1" ;;
    *) echo "usage: relief_sweep.sh [--force] [--only 'a b c']"; exit 2 ;;
  esac
  shift
done

if [ -n "$ONLY" ]; then
  LIST="$ONLY"
else
  LIST=$(ls -d render/gate_witness/*/ | sed 's#render/gate_witness/##; s#/##')
fi

ran=0; skipped=0; superseded=0; failed=0
for it in $LIST; do
  B="render/gate_witness/$it/witness.blend"
  J="$OUT/$it.json"
  [ -f "$B" ] || { echo "SKIP $it -- no witness blend"; continue; }
  if [ -f "$J" ] && [ "$FORCE" -eq 0 ] && [ "$J" -nt "$B" ]; then
    echo "CURRENT $it -- report is newer than its witness"
    skipped=$((skipped + 1))
    continue
  fi
  if [ -f "$J" ]; then
    S="$OUT/${it}_SUPERSEDED_pre_R2038witness.json"
    if [ ! -f "$S" ]; then
      cp -p "$J" "$S"
      superseded=$((superseded + 1))
      echo "SUPERSEDED $it -> $(basename "$S")"
    fi
  fi
  echo "=== $it"
  timeout 2400 "$BL" -b "$B" --factory-startup -P tools/relief_audit.py -- \
      --item "$it" --out "$J" > "$OUT/$it.log" 2>&1
  # Blender 5.2 exits 0 on an uncaught script exception (R2-108), so $? is not
  # evidence.  The artefact is: relief_audit writes the JSON or it does not.
  if [ -f "$J" ] && [ "$J" -nt "$B" ]; then
    ran=$((ran + 1))
  else
    echo "FAILED $it -- no fresh JSON was written"
    failed=$((failed + 1))
  fi
done

echo
echo "re-run $ran   already current $skipped   superseded $superseded   failed $failed"
if [ "$failed" -gt 0 ]; then
  echo ">> STAGE RESULT: RELIEF_SWEEP_FAIL"
  exit 1
fi
if [ "$ran" -eq 0 ] && [ "$skipped" -eq 0 ]; then
  echo ">> STAGE RESULT: RELIEF_SWEEP_VACUOUS"
  exit 1
fi
echo ">> STAGE RESULT: RELIEF_SWEEP_OK"
