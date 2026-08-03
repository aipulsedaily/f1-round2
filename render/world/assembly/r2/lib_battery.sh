# shellcheck shell=bash
# THE BATTERY RUNNER — one copy, sourced by v120, v121 and v122/battery.sh.
#
# WHY THIS FILE EXISTS
# ====================
# Both batteries had their own `run ()`:
#
#     run () { echo; echo "##### $1"; shift; "$@"; echo "##### exit=$? $(date)"; }
#
# It printed the exit code and threw it away. That was harmless while every gate
# exited 0 whatever it found; now that a gate's status means something, throwing
# it away would be the same defect one level up. And a private copy of shared
# behaviour in three files is exactly what defeated the socket guard (R2-057), so
# there is one copy and both batteries source it.
#
# THE TWO KINDS OF STEP, WHICH ARE NOT THE SAME KIND
# ==================================================
# A battery run mixes two things that need opposite handling:
#
#   MEASUREMENTS  `placement_gate` on the world. A FAIL here is the battery
#                 DOING ITS JOB — it found the defect it was run to find. A
#                 survey that stops at the first one tells you about one defect
#                 and hides the other nineteen, and these run for hours over
#                 4 GB scenes. So a failed measurement is RECORDED and the run
#                 CONTINUES, and the battery's own exit status is non-zero at
#                 the end.
#
#   CONTROLS      `collision_gate POSITIVE control`, which must FAIL, and
#                 `... NEGATIVE control`, which must PASS. A control that does
#                 not do what it was built to do means the instrument is not
#                 measuring, and every measurement after it is worthless. That
#                 HALTS, immediately, by default.
#
# Yesterday's battery had two positive depth controls and none that must pass —
# `ctl_depth_neg.blend` put the wheel 200 mm in the air, so the "negative"
# control was a second positive one. Nothing noticed, because nothing was
# ASSERTING what each control had to do. `expect` states it per step, in the
# battery, next to the command, so a control that changes meaning breaks the
# run instead of quietly agreeing with its neighbour.
#
# USAGE
# =====
#     source "$D/lib_battery.sh"
#
#     regenerate_controls "$B" "$V0/make_controls.py" "$V0"
#                                                # rebuild the control scenes
#                                                # from live source; halts if
#                                                # they were not rewritten
#     run    "label"                 cmd...      # measurement; records, continues
#     expect pass    "label"         cmd...      # must exit 0
#     expect fail    "label"         cmd...      # must exit 1
#     expect vacuous "label"         cmd...      # must exit 3   (refused)
#     expect any     "label"         cmd...      # must not CRASH (2) or be
#                                                # killed; anything else is fine
#     battery_summary                            # prints the table, sets the
#                                                # script's exit status
#
# `--keep-going` on the battery's command line (or KEEP_GOING=1 in the
# environment) downgrades a misbehaving CONTROL from "halt" to "record and
# carry on" — for the case where you genuinely want the whole survey out of one
# overnight run and will read the table yourself. It is explicit, it is printed
# in the header, and it never turns a failure into a pass: `battery_summary`
# still exits non-zero.
#
# EXIT CODES, from tools/gate_exit.py:
#     0 PASS   1 FAIL   2 CRASH (or bad arguments)   3 VACUOUS (refused)

KEEP_GOING="${KEEP_GOING:-0}"
for _arg in "$@"; do
  case "$_arg" in
    --keep-going) KEEP_GOING=1 ;;
  esac
done

_BATTERY_ROWS=()
_BATTERY_BAD=0          # the INSTRUMENT misbehaved: a control, or a crash
_BATTERY_DEFECTS=0      # the SUBJECT failed a measurement: a real finding
_BATTERY_HALTED=""

# ---------------------------------------------------------------------------
# REBUILD THE CONTROL SCENES FROM LIVE SOURCE, EVERY RUN.
#
# The controls are .blend files on disk. Until 2026-08-03 nothing regenerated
# them: three batteries opened whatever a human had last left in v120/, and
# `ctl_place_pos.blend` is POSITIONED FROM THE LIVE CONTRACT -- half_width,
# su_to_world, ground_z. A stale copy is an obstacle aimed at a corridor that
# has since moved, and it fails, and the failure looks like proof the gate
# works. That is R2-072's shape: a control whose broken input is FOUND on disk
# rather than MANUFACTURED from source expires silently.
#
# So: regenerate first, and treat a regeneration that did not happen as an
# instrument failure rather than a warning. A battery that could not rebuild
# its controls has no controls.
# ---------------------------------------------------------------------------
regenerate_controls () {   # <blender> <make_controls.py> <outdir>
  local bl="$1" mk="$2" dir="$3"
  echo
  echo "##### regenerate the control scenes from live source  $(date +%T)"
  local before after n=0
  before=$(ls -l "$dir"/ctl_*.blend 2>/dev/null | md5sum)
  "$bl" -b --factory-startup -P "$mk" -- --outdir "$dir" 2>&1 \
    | grep -E '^\[CTL\]' | sed 's/^/   /'
  local rc=${PIPESTATUS[0]}
  n=$(ls "$dir"/ctl_*.blend 2>/dev/null | wc -l)
  after=$(ls -l "$dir"/ctl_*.blend 2>/dev/null | md5sum)
  echo "   rc=$rc, $n control blend(s) present"
  # Blender 5.2 exits 0 on an uncaught script exception, so rc is not evidence.
  # The evidence is the artefacts: they must EXIST and they must have been
  # REWRITTEN by this call.
  if [ "$n" -lt 10 ]; then
    echo "!!!!! only $n control blend(s) in $dir; make_controls.py writes 10."
    _battery_record control "regenerate control scenes" "10 blends" "$n" "bad"
    _battery_halt "the control scenes could not be regenerated ($n of 10)"
    return 0
  fi
  if [ "$before" = "$after" ]; then
    echo "!!!!! the control blends were NOT rewritten (identical listing)."
    echo "!!!!! Every control below would be measuring a file this run did not"
    echo "!!!!! produce -- which is the exact defect this step exists to stop."
    _battery_record control "regenerate control scenes" "rewritten" "unchanged" "bad"
    _battery_halt "the control scenes were not rewritten"
    return 0
  fi
  _battery_record control "regenerate control scenes" "10 blends" "$n rebuilt" "ok"
  return 0
}

_battery_name_of () {
  case "$1" in
    0) echo "PASS" ;;
    1) echo "FAIL" ;;
    2) echo "CRASH" ;;
    3) echo "VACUOUS" ;;
    124) echo "TIMEOUT" ;;
    *) echo "rc=$1" ;;
  esac
}

_battery_record () {   # kind label want got verdict
  _BATTERY_ROWS+=("$1|$2|$3|$4|$5")
  case "$5" in
    ok|finding) ;;                                  # counted by the caller
    *) _BATTERY_BAD=$((_BATTERY_BAD + 1)) ;;        # bad, skipped
  esac
}

# ---------------------------------------------------------------------------
# A MEASUREMENT. Never halts. Its result lands in the summary.
# ---------------------------------------------------------------------------
run () {
  local label="$1"; shift
  echo
  echo "##### $label  $(date +%T)"
  if [ -n "$_BATTERY_HALTED" ]; then
    echo "##### SKIPPED — the battery halted at: $_BATTERY_HALTED"
    _battery_record measure "$label" "-" "skipped" "skipped"
    return 0
  fi
  "$@"
  local rc=$?
  echo "##### exit=$rc ($(_battery_name_of $rc))  $(date +%T)"
  # A measurement that CRASHED did not measure anything, so it is never "the
  # gate doing its job" -- it is the instrument failing, same as a control.
  if [ "$rc" = 2 ] || [ "$rc" -ge 124 ]; then
    _battery_record measure "$label" "a verdict" "$(_battery_name_of $rc)" "bad"
    _battery_halt "$label produced no verdict ($(_battery_name_of $rc))"
  elif [ "$rc" != 0 ]; then
    # A finding, not a malfunction: the gate looked and did not like what it
    # saw. Recorded, counted, and the run carries on -- but the battery does
    # NOT get to call itself OK at the end.
    _BATTERY_DEFECTS=$((_BATTERY_DEFECTS + 1))
    _battery_record measure "$label" "-" "$(_battery_name_of $rc)" "finding"
  else
    _battery_record measure "$label" "-" "$(_battery_name_of $rc)" "ok"
  fi
  return 0
}

# ---------------------------------------------------------------------------
# A CONTROL. Says what it must do. Halts the battery if it does not.
# ---------------------------------------------------------------------------
expect () {
  local want="$1"; local label="$2"; shift 2
  local wantrc
  case "$want" in
    pass)    wantrc=0 ;;
    fail)    wantrc=1 ;;
    vacuous) wantrc=3 ;;
    any)     wantrc=-1 ;;
    *) echo "!!!!! battery: 'expect $want' is not a thing. Use pass|fail|vacuous|any." >&2
       _BATTERY_BAD=$((_BATTERY_BAD + 1)); return 0 ;;
  esac
  echo
  echo "##### $label  $(date +%T)   [CONTROL: must $want]"
  if [ -n "$_BATTERY_HALTED" ]; then
    echo "##### SKIPPED — the battery halted at: $_BATTERY_HALTED"
    _battery_record control "$label" "$want" "skipped" "skipped"
    return 0
  fi
  "$@"
  local rc=$?
  echo "##### exit=$rc ($(_battery_name_of $rc))  $(date +%T)"
  local ok=0
  if [ "$wantrc" = -1 ]; then
    { [ "$rc" != 2 ] && [ "$rc" -lt 124 ]; } && ok=1
  elif [ "$rc" = "$wantrc" ]; then
    ok=1
  fi
  if [ "$ok" = 1 ]; then
    _battery_record control "$label" "$want" "$(_battery_name_of $rc)" "ok"
  else
    echo "!!!!! CONTROL MISBEHAVED: '$label' had to $want and returned $(_battery_name_of $rc)."
    echo "!!!!! The instrument is not measuring what it claims;"
    echo "!!!!! every measurement after this one is unusable."
    _battery_record control "$label" "$want" "$(_battery_name_of $rc)" "bad"
    _battery_halt "control '$label' had to $want and returned $(_battery_name_of $rc)"
  fi
  return 0
}

_battery_halt () {
  if [ "$KEEP_GOING" = 1 ]; then
    echo "!!!!! --keep-going: carrying on anyway. The battery will still exit non-zero."
  else
    _BATTERY_HALTED="$1"
    echo "!!!!! HALTING. Re-run with --keep-going to survey the rest anyway."
  fi
}

battery_summary () {
  echo
  echo "############################################################ SUMMARY"
  printf "%-8s %-58s %-9s %-9s %s\n" KIND STEP MUST GOT ""
  local r kind label want got verdict
  for r in "${_BATTERY_ROWS[@]}"; do
    IFS='|' read -r kind label want got verdict <<< "$r"
    printf "%-8s %-58s %-9s %-9s %s\n" "$kind" "$label" "$want" "$got" \
      "$([ "$verdict" = ok ] && echo "" || echo "  <<< $verdict")"
  done
  echo
  if [ -n "$_BATTERY_HALTED" ]; then
    echo ">> BATTERY HALTED: $_BATTERY_HALTED"
  fi

  # A BATTERY THAT RAN NOTHING HAS NOT PASSED.
  #
  # This is not hypothetical and it is not pedantry: the first version of this
  # function returned 0 and printed "BATTERY_OK (0 steps: every control behaved
  # and every measurement came back clean)" for an empty run -- the exact
  # vacuous pass this whole task exists to remove, reintroduced in the tool
  # written to remove it. A battery whose `run`/`expect` lines were all
  # commented out, or that was sourced and never used, must refuse.
  if [ "${#_BATTERY_ROWS[@]}" = 0 ]; then
    echo ">> REFUSING TO REPORT: this battery ran ZERO steps. Nothing was"
    echo ">> measured and no control was exercised. That is NOT a pass."
    echo ">> STAGE RESULT: BATTERY_VACUOUS"
    return 3
  fi

  # ORDER MATTERS BELOW, AND IT IS DELIBERATE.
  #
  # A KNOWN malfunction outranks "you had no controls": if a gate crashed or a
  # control misbehaved, that is a specific diagnosis and it should be the one
  # reported. "No controls at all" is the fallback for a run where nothing went
  # visibly wrong and there is still no reason to believe it.
  if [ "$_BATTERY_BAD" != 0 ]; then
    echo ">> $_BATTERY_BAD of ${#_BATTERY_ROWS[@]} steps did not do what they had to (a control misbehaved, or a gate produced no verdict)."
    echo ">> The measurements in this run are NOT evidence of anything."
    echo ">> STAGE RESULT: BATTERY_INSTRUMENT_FAIL"
    return 2
  fi

  # A BATTERY WITH NO CONTROLS IS A BATTERY WITH NO EVIDENCE.
  #
  # Every measurement rests on the instruments having been shown to work ON
  # THIS RUN. `run` lines alone give numbers nobody has any reason to believe
  # -- which is how a harness measured a four-day-old blend and returned a
  # flawless null against a noise floor, when the real answer was 57.50 %.
  local _nctl=0 _r
  for _r in "${_BATTERY_ROWS[@]}"; do
    case "$_r" in control\|*) _nctl=$((_nctl + 1)) ;; esac
  done
  if [ "$_nctl" = 0 ]; then
    echo ">> REFUSING TO REPORT: ${#_BATTERY_ROWS[@]} measurement(s) and NOT ONE"
    echo ">> control. Nothing on this run showed the instruments were measuring."
    echo ">> STAGE RESULT: BATTERY_VACUOUS"
    return 3
  fi

  # THE SUBJECT FAILED, THE INSTRUMENT DID NOT. Distinct news, distinct code:
  # a caller needs to tell "your world is broken" from "my gate is broken", and
  # collapsing those two into one status is the whole subject of this fix.
  if [ "$_BATTERY_DEFECTS" != 0 ]; then
    echo ">> every control behaved, so the instruments were measuring."
    echo ">> $_BATTERY_DEFECTS of ${#_BATTERY_ROWS[@]} measurements came back non-clean. These are FINDINGS about the world, not malfunctions."
    echo ">> STAGE RESULT: BATTERY_FINDINGS"
    return 1
  fi
  echo ">> STAGE RESULT: BATTERY_OK  (${#_BATTERY_ROWS[@]} steps: every control behaved and every measurement came back clean)"
  return 0
}
