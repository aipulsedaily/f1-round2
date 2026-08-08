#!/bin/bash
# ONE HEAVY BLENDER BUILD AT A TIME.  Wrap any film/world build in this.
#
#   bash tools/buildlock.sh <name> <command...>
#
# WHY THIS EXISTS.  This box has 11 GB of RAM and a 43 GB swap, and the film
# scenes are ~10 GB.  Measured at 07:0x on 2026-08-08, with seven agents live:
#
#     Mem:   11 total, 4 available          Swap: 43 total, 32 USED, 11 free
#     /proc/pressure/memory  full avg300=12.06
#
# "full avg300=12" means every runnable process was stalled on memory 12% of
# the last five minutes.  That is why a film build takes 27 minutes here and
# not 17.  Two concurrent builds do not run at half speed; one of them gets
# shot by the OOM killer, and the OOM killer does not pick the newest -- it
# picks the biggest, which is somebody else's nearly-finished 3.9 GB build.
#
# This was found by an agent that KILLED ITS OWN BUILD at 6m57s rather than
# risk another agent's 27-minute film build, with 528 MB available and swap at
# 35/45 GB.  It was right, and the correct response to being right is a
# mechanism, not a note.  A warning is not a mechanism -- that lesson has been
# learned three separate times tonight (gitguard's docstring, test_broker's
# docstring, and the "queue politely" honour system that an exec ignored,
# taking a GPU another job held and killing it terminally).
#
# The lock is ADVISORY in the sense that a build not wrapped in it is not
# stopped.  It is a real flock otherwise: the second caller WAITS, it does not
# fail, so wrapping a build can never lose you the build.
set -u
NAME="${1:-unnamed}"; shift || true
[ $# -gt 0 ] || { echo "usage: bash tools/buildlock.sh <name> <command...>"; exit 2; }

LOCK=/home/zany/f1-round2/.buildlock
exec 9>"$LOCK"

avail_mb() { awk '/MemAvailable/{print int($2/1024)}' /proc/meminfo; }
swap_free_mb() { awk '/SwapFree/{print int($2/1024)}' /proc/meminfo; }

if ! flock -n 9; then
    holder="$(cat "$LOCK.who" 2>/dev/null || echo unknown)"
    echo "BUILD LOCK HELD by '$holder' -- waiting rather than racing it."
    echo "  (a second ~10 GB build here does not halve the speed, it feeds the OOM killer)"
    flock 9
fi
echo "$NAME pid=$$ since=$(date -u '+%H:%M:%S')" > "$LOCK.who"

A=$(avail_mb); S=$(swap_free_mb)
echo "=== buildlock: $NAME ===  available ${A} MB, swap free ${S} MB"
if [ "$A" -lt 700 ] && [ "$S" -lt 4000 ]; then
    echo ">> STAGE RESULT: BUILDLOCK REFUSED  (available ${A} MB, swap free ${S} MB)"
    echo "   Not starting a heavy build into this.  Nothing else is holding the"
    echo "   lock, so the pressure is from processes that do not use it -- find"
    echo "   them (ps -eo rss,etime,comm --sort=-rss | head) before retrying."
    rm -f "$LOCK.who"; exit 3
fi

"$@"; rc=$?
echo ">> STAGE RESULT: BUILDLOCK RELEASED  $NAME rc=$rc  (available $(avail_mb) MB)"
rm -f "$LOCK.who"
exit $rc
