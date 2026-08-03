#!/usr/bin/env bash
# CONTROLS FOR lib_battery.sh — the runner is an instrument too.
#
#     bash render/world/assembly/r2/selftest_battery.sh
#
# The batteries used to swallow every exit code, so the runner that replaces
# that has to be shown to do the three things it exists to do:
#
#   * a CONTROL that misbehaves HALTS the run and everything after it is
#     marked skipped, not passed;
#   * a MEASUREMENT that fails is RECORDED and the survey CARRIES ON, because
#     stopping at the first finding on a four-hour run hides the rest;
#   * `--keep-going` surveys past a bad control WITHOUT turning it into a pass.
#
# It uses `true` and `false` and tiny `exit N` shells as the gates, so it costs
# nothing and it cannot pass because some real gate happens to be broken --
# every subject here is built in this file.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TMP="$(mktemp -d -t battery_ctl_XXXXXX)"
FAILS=0

say () { printf "   %-4s %-58s %s\n" "$1" "$2" "${3:-}"; [ "$1" = PASS ] || FAILS=$((FAILS+1)); }

# A gate that exits with a code we choose, and says so, like a real one.
cat > "$TMP/gate.sh" <<'EOF'
#!/usr/bin/env bash
echo ">> STAGE RESULT: FAKE_$2"
exit $1
EOF
chmod +x "$TMP/gate.sh"
G="$TMP/gate.sh"

# --------------------------------------------------------------------------
# 1. EVERY STEP BEHAVES -> BATTERY_OK, status 0
# --------------------------------------------------------------------------
cat > "$TMP/b_ok.sh" <<EOF
set -u
D="$HERE"
source "\$D/lib_battery.sh"
expect fail    "positive control" $G 1 FAIL
expect pass    "negative control" $G 0 CLEAN
expect vacuous "world, must refuse" $G 3 VACUOUS
run "a clean measurement" $G 0 CLEAN
battery_summary
exit \$?
EOF
out=$(bash "$TMP/b_ok.sh" 2>&1); rc=$?
echo "1. EVERY STEP BEHAVES"
say "$([ "$rc" = 0 ] && echo PASS || echo FAIL)" \
    "all controls behaved, all measurements clean -> exit 0" "rc=$rc"
say "$(grep -q "STAGE RESULT: BATTERY_OK" <<<"$out" && echo PASS || echo FAIL)" \
    "...and it says BATTERY_OK"

# --------------------------------------------------------------------------
# 2. A REAL FINDING: the survey must CONTINUE and still exit non-zero
# --------------------------------------------------------------------------
cat > "$TMP/b_find.sh" <<EOF
set -u
D="$HERE"
source "\$D/lib_battery.sh"
expect fail "positive control" $G 1 FAIL
run "placement_gate, finds a violation" $G 1 PLACEMENT_FAIL
run "a later measurement that MUST still run" $G 0 CLEAN
battery_summary
exit \$?
EOF
out=$(bash "$TMP/b_find.sh" 2>&1); rc=$?
echo
echo "2. A MEASUREMENT FAILS — the survey carries on, the battery does not pass"
say "$(grep -q "a later measurement that MUST still run" <<<"$out" \
        && ! grep -q "SKIPPED" <<<"$out" && echo PASS || echo FAIL)" \
    "the step AFTER the finding still ran"
say "$([ "$rc" = 1 ] && echo PASS || echo FAIL)" \
    "the battery exits 1 (findings), not 0" "rc=$rc"
say "$(grep -q "STAGE RESULT: BATTERY_FINDINGS" <<<"$out" && echo PASS || echo FAIL)" \
    "...and it says BATTERY_FINDINGS, not BATTERY_OK"

# --------------------------------------------------------------------------
# 3. A CONTROL MISBEHAVES: HALT, and mark the rest skipped
# --------------------------------------------------------------------------
cat > "$TMP/b_ctl.sh" <<EOF
set -u
D="$HERE"
source "\$D/lib_battery.sh"
expect fail "positive control THAT WRONGLY PASSES" $G 0 CLEAN
run "a measurement that must NOT be trusted after that" $G 0 CLEAN
battery_summary
exit \$?
EOF
out=$(bash "$TMP/b_ctl.sh" 2>&1); rc=$?
echo
echo "3. A CONTROL MISBEHAVES — halt, and do not report the rest as passes"
say "$(grep -q "CONTROL MISBEHAVED" <<<"$out" && echo PASS || echo FAIL)" \
    "it says the control misbehaved"
say "$(grep -q "SKIPPED — the battery halted" <<<"$out" && echo PASS || echo FAIL)" \
    "the following measurement is SKIPPED, not run and not passed"
say "$([ "$rc" = 2 ] && echo PASS || echo FAIL)" \
    "the battery exits 2 (instrument failure)" "rc=$rc"
say "$(grep -q "BATTERY_INSTRUMENT_FAIL" <<<"$out" && echo PASS || echo FAIL)" \
    "...and it says the measurements are not evidence"

# THE SAME FOR THE OTHER DIRECTION: a NEGATIVE control that fails.
cat > "$TMP/b_ctl2.sh" <<EOF
set -u
D="$HERE"
source "\$D/lib_battery.sh"
expect pass "negative control THAT WRONGLY FAILS" $G 1 FAIL
battery_summary
exit \$?
EOF
out=$(bash "$TMP/b_ctl2.sh" 2>&1); rc=$?
say "$([ "$rc" = 2 ] && echo PASS || echo FAIL)" \
    "a NEGATIVE control that fails halts it too" "rc=$rc"

# THE CASE THAT ACTUALLY HAPPENED: two positive controls, none that must pass.
# `expect` cannot prevent someone writing two `expect fail` lines, but it makes
# the omission VISIBLE in the summary, which is what was missing.
cat > "$TMP/b_ctl3.sh" <<EOF
set -u
D="$HERE"
source "\$D/lib_battery.sh"
expect fail "depth POSITIVE control" $G 1 FAIL
expect fail "depth 'NEGATIVE' control that is really a second positive" $G 1 FAIL
battery_summary
exit \$?
EOF
out=$(bash "$TMP/b_ctl3.sh" 2>&1); rc=$?
say "$(grep -cE '^control .*fail ' <<<"$(grep -A99 SUMMARY <<<"$out")" \
        | grep -q 2 && echo PASS || echo FAIL)" \
    "two 'must fail' controls and no 'must pass' one is VISIBLE in the summary" \
    "$(grep -A99 SUMMARY <<<"$out" | grep -c 'fail ') rows say must=fail"

# --------------------------------------------------------------------------
# 4. --keep-going surveys past a bad control but never calls it a pass
# --------------------------------------------------------------------------
cat > "$TMP/b_keep.sh" <<EOF
set -u
D="$HERE"
source "\$D/lib_battery.sh"
expect fail "positive control THAT WRONGLY PASSES" $G 0 CLEAN
run "the rest of the survey" $G 0 CLEAN
battery_summary
exit \$?
EOF
out=$(bash "$TMP/b_keep.sh" --keep-going 2>&1); rc=$?
echo
echo "4. --keep-going"
say "$(grep -q "the rest of the survey" <<<"$out" \
        && ! grep -q "SKIPPED" <<<"$out" && echo PASS || echo FAIL)" \
    "the rest of the survey DOES run"
say "$([ "$rc" = 2 ] && echo PASS || echo FAIL)" \
    "and the battery STILL exits non-zero" "rc=$rc"

# --------------------------------------------------------------------------
# 5. A CRASHING GATE is never 'the gate doing its job'
# --------------------------------------------------------------------------
cat > "$TMP/b_crash.sh" <<EOF
set -u
D="$HERE"
source "\$D/lib_battery.sh"
expect fail "a control, so 'no controls' is not the reason" $G 1 FAIL
run "a gate that CRASHES (rc 2)" $G 2 CRASH
battery_summary
exit \$?
EOF
out=$(bash "$TMP/b_crash.sh" 2>&1); rc=$?
echo
echo "5. A CRASHING MEASUREMENT"
say "$([ "$rc" = 2 ] && echo PASS || echo FAIL)" \
    "rc=2 from a measurement is an instrument failure, not a finding" "rc=$rc"
say "$(grep -q "produced no verdict" <<<"$out" && echo PASS || echo FAIL)" \
    "...and the CRASH is named, not reported as 'you had no controls'"

# --------------------------------------------------------------------------
# 6. POSITIVE CONTROL ON THE OLD RUNNER — it could not have caught any of this
# --------------------------------------------------------------------------
cat > "$TMP/b_old.sh" <<EOF
set -u
run () { echo; echo "##### \$1"; shift; "\$@"; echo "##### exit=\$?"; }
run "positive control THAT WRONGLY PASSES" $G 0 CLEAN
run "placement_gate, finds a violation" $G 1 PLACEMENT_FAIL
EOF
out=$(bash "$TMP/b_old.sh" 2>&1); rc=$?
echo
echo "6. POSITIVE CONTROL — the runner these batteries used to have"
say "$([ "$rc" = 0 ] && echo PASS || echo FAIL)" \
    "the OLD run() exits 0 after a dead control AND a violation" "rc=$rc"


# --------------------------------------------------------------------------
# 7. A BATTERY THAT MEASURED NOTHING, OR CONTROLLED NOTHING, MUST REFUSE
#    The first version of battery_summary() printed "BATTERY_OK (0 steps)" and
#    returned 0 -- the vacuous pass this whole task exists to remove, inside
#    the tool written to remove it. These two controls exist so it cannot come
#    back.
# --------------------------------------------------------------------------
cat > "$TMP/b_empty.sh" <<EOF
set -u
D="$HERE"
source "\$D/lib_battery.sh"
battery_summary
exit \$?
EOF
out=$(bash "$TMP/b_empty.sh" 2>&1); rc=$?
echo
echo "7. AN EMPTY OR UNCONTROLLED BATTERY"
say "$([ "$rc" = 3 ] && echo PASS || echo FAIL)" \
    "zero steps -> VACUOUS(3), not BATTERY_OK" "rc=$rc"
say "$(grep -q "BATTERY_VACUOUS" <<<"$out" && echo PASS || echo FAIL)" \
    "...and it says so"

cat > "$TMP/b_noctl.sh" <<EOF
set -u
D="$HERE"
source "\$D/lib_battery.sh"
run "a measurement with no control anywhere on the run" $G 0 CLEAN
battery_summary
exit \$?
EOF
out=$(bash "$TMP/b_noctl.sh" 2>&1); rc=$?
say "$([ "$rc" = 3 ] && echo PASS || echo FAIL)" \
    "measurements but ZERO controls -> VACUOUS(3)" "rc=$rc"
say "$(grep -q "NOT ONE" <<<"$out" && echo PASS || echo FAIL)" \
    "...and it names the reason: no control was exercised"

echo
rm -rf "$TMP"
if [ "$FAILS" != 0 ]; then
  echo ">> $FAILS CONTROL(S) MISBEHAVED"
  echo ">> STAGE RESULT: BATTERY_RUNNER_SELFTEST_FAIL"
  exit 1
fi
echo ">> every control behaved"
echo ">> STAGE RESULT: BATTERY_RUNNER_SELFTEST_OK"
