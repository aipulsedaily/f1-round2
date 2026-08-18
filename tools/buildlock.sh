#!/bin/bash
# ONE HEAVY BLENDER BUILD AT A TIME -- FAIRLY, AND WITH A LANE FOR SMALL ONES.
#
#   bash tools/buildlock.sh [--small] <name> <command...>
#
# WHY THIS EXISTS.  This box has 11 GB of RAM and a 43 GB swap, and the film
# scenes are ~10 GB.  Measured at 07:0x on 2026-08-08, with seven agents live:
#
#     Mem:   11 total, 4 available          Swap: 43 total, 32 USED, 11 free
#     /proc/pressure/memory  full avg300=12.06
#
# "full avg300=12" means every runnable process was stalled on memory 12% of
# the last five minutes.  Two concurrent builds do not run at half speed; one
# gets shot by the OOM killer, and the OOM killer picks the biggest, which is
# somebody else's nearly-finished build.  After this lock went in, pressure
# fell to full avg300=0.09.  It works.
#
# ---------------------------------------------------------------------------
# R2-3066: TWO DEFECTS IN THE FIRST VERSION, BOTH FOUND BY BEING QUEUED ON IT.
#
# By 17:30 NINE agents were waiting on one global lock, and an agent reported
# both problems from inside the queue:
#
#   1. `flock` IS NOT FIFO.  Every release is a fresh race among all waiters,
#      so wait time is unbounded and unrelated to arrival order.  One agent
#      accumulated 34 minutes of waiting and then lost the handover anyway.
#
#   2. ONE LANE STARVES THE SHORT JOBS.  A 58 MB surface build waited exactly
#      as long as a 10 GB film append, behind contenders each holding 20-40
#      minutes.  Serialising a 58 MB build against a 10 GB one protects
#      nothing -- their peak footprints are not remotely comparable.
#
# The lesson is the one this project keeps relearning in new costume: a
# mechanism that fixes the failure it was aimed at can create a different one,
# and the only reason this was caught is that the agents it starved reported
# it instead of routing around it.  Both fixes below are theirs in substance.
#
# FAIRNESS.  A waiter registers in a queue directory before contending, and on
# acquiring the lock it yields unless it is the OLDEST live waiter.  That is
# approximate FIFO built out of flock, which has no ordering of its own.  Dead
# waiters are reaped on every pass, so a killed agent cannot block the queue.
#
# LANES.  --small takes a separate lock permitting up to SMALL_SLOTS builds
# concurrently, and only while there is real memory for them.  Anything that
# opens or writes a film-sized .blend is NOT small.  If in doubt, omit it: the
# cost of being wrong in the big lane is waiting, and in the small lane it is
# somebody's 40-minute build dying.
#
# The second caller always WAITS rather than failing, so wrapping a build can
# never lose you the build.
set -u

SMALL=0
if [ "${1:-}" = "--small" ]; then SMALL=1; shift; fi
NAME="${1:-unnamed}"; shift || true
[ $# -gt 0 ] || { echo "usage: bash tools/buildlock.sh [--small] <name> <command...>"; exit 2; }

# --------------------------------------------------------------------------
# R2-3602: THIS BOX HAS TWO Blender 5.2.0 BINARIES AND THEY ARE NOT THE SAME.
#
#     /opt/blender-5.2.0-linux-x64/blender   built 2026-07-14  python 3.13  numpy 2.3.4
#     /usr/bin/blender                       built 2026-07-15  python 3.14  numpy 2.5.1
#
# BOTH report themselves as `Blender 5.2.0 LTS (hash fbe6228777e7)`, and
# /usr/bin is what a bare `blender` resolves to on PATH.  The only visible
# difference in a log header is the build DATE, which nobody reads.
#
# The difference that matters is numpy.  `float()` on an array with ndim > 0
# has been deprecated since numpy 1.25; under 2.3.4 it is a warning, under
# 2.5.1 it is a TypeError.  assembly15 was built with the bare-`blender` one
# and `build_dressing` died on its first marshal post 1.1 s in -- and because
# assemble.py catches every module exception and saves the blend anyway, the
# result was a 9 GB world missing all 247 dressing objects (the ad boards, the
# tyre stacks, the flagpoles, the marshal posts, the TV cameras) whose only
# symptom was one line in a 4,000-line log.  It was then bisected against the
# ground cover and the near band, which are innocent: the arms that "passed"
# were simply the ones run with the /opt binary.  Two days of a real defect
# hunt went into a variable nobody knew was moving.
#
# So the binary is pinned HERE, at the one choke point every heavy build in
# this project already goes through.  A build with the wrong Blender is
# refused, loudly, instead of producing an artefact that is wrong quietly.
# Deliberately testing the other binary is legitimate; say so out loud with
# R2_ALLOW_ANY_BLENDER=1 and the refusal downgrades to a warning.
REF_BLENDER=/opt/blender-5.2.0-linux-x64/blender
_ref_real="$(readlink -f -- "$REF_BLENDER" 2>/dev/null || echo "$REF_BLENDER")"
for _a in "$@"; do
    [ "$(basename -- "$_a")" = "blender" ] || continue
    _got="$(command -v -- "$_a" 2>/dev/null || echo "$_a")"
    _got_real="$(readlink -f -- "$_got" 2>/dev/null || echo "$_got")"
    [ "$_got_real" != "$_ref_real" ] || continue
    if [ "${R2_ALLOW_ANY_BLENDER:-0}" = 1 ]; then
        echo "  buildlock: WARNING -- '$_a' resolves to $_got_real, NOT the"
        echo "  reference $_ref_real.  Allowed because R2_ALLOW_ANY_BLENDER=1."
        continue
    fi
    echo ">> STAGE RESULT: BUILDLOCK REFUSED  ($NAME: wrong Blender)"
    echo "   '$_a' resolves to"
    echo "       $_got_real"
    echo "   and the reference binary for this project is"
    echo "       $_ref_real"
    echo "   These two report the SAME version string and the SAME build hash"
    echo "   and ship DIFFERENT numpy versions (2.5.1 vs 2.3.4).  The wrong one"
    echo "   does not fail the build; it silently drops build_dressing's 247"
    echo "   objects and saves the blend anyway (R2-3602)."
    echo "   Use the absolute path, or set R2_ALLOW_ANY_BLENDER=1 if you mean it."
    exit 4
done

ROOT=$HOME/f1-round2
LOCK="$ROOT/.buildlock"
SMALL_LOCK="$ROOT/.buildlock.small"
QDIR="$ROOT/.buildlock.q"
SMALL_SLOTS=2
# R2-3066b: this was 1500 and the small lane was DEAD ON THIS BOX.  MemAvailable
# here sits around 1650 MB, so the moment a big build took its share the floor
# was breached, smalls fell back to the big lane, and the starvation this lane
# exists to fix came straight back.  Measured, not guessed: a concurrency test
# put two smalls behind a 6 s big build instead of alongside it, and the small
# lane ran correctly the instant it was tested on its own.
#
# 1000 MB clears two ~400 MB surface builds with headroom, and the big lane's
# own refusal at 700 MB still backstops it.  Getting this wrong in the generous
# direction OOM-kills somebody's 40-minute build, so it is deliberately not
# lower.
SMALL_MIN_MB=1000

mkdir -p "$QDIR"
avail_mb() { awk '/MemAvailable/{print int($2/1024)}' /proc/meminfo; }
swap_free_mb() { awk '/SwapFree/{print int($2/1024)}' /proc/meminfo; }

# Reap queue entries whose process is gone.  Without this one killed agent
# would hold the head of the line forever.
# R2-3066d: ALSO DROP TICKETS THAT DO NOT MATCH THE CURRENT SCHEMA.
#
# This file was rewritten twice in three minutes (5256293 17:37:13, fe87ec6
# 17:40:20) and an agent registered in the window between them.  v1 wrote
# `<stamp>-<pid>.q`; v2 prefixed a priority, `<prio>-<stamp>-<pid>.q`.  The
# queue is ordered by `ls | sort`, and '-' (0x2D) sorts BEFORE '7' (0x37) --
# so every new ticket sorted ahead of the old-format one PERMANENTLY.  That
# agent was the oldest live waiter and would have stayed at the back of the
# queue forever, while its own status line truthfully reported "0 waiters
# ahead of me" -- true when printed, false the moment the format changed
# under it.
#
# So schema drift in a sort key is not cosmetic: it silently inverts the
# ordering it is supposed to define.  A malformed ticket is dropped here, and
# the wait loop below re-registers its own ticket if it finds it gone, so a
# waiter caught by drift heals instead of starving.
#
# (The related hazard has no fix here: bash reads a script incrementally, so a
# process running the old file while it is rewritten underneath executes a
# mixture.  Do not rewrite this file while builds are queued on it.)
reap_q() {
    local f pid base
    for f in "$QDIR"/*.q; do
        [ -e "$f" ] || continue
        base="$(basename "$f" .q)"
        case "$base" in
            [01]-*-*) ;;                       # current schema
            *) echo "  buildlock: dropping malformed ticket '$base' (schema drift)"
               rm -f "$f"; continue ;;
        esac
        pid="${base##*-}"
        [ -d "/proc/$pid" ] || rm -f "$f"
    done
}

# ---------------------------------------------------------------- small lane
if [ "$SMALL" = 1 ]; then
    A=$(avail_mb)
    if [ "$A" -lt "$SMALL_MIN_MB" ]; then
        echo "small lane has ${A} MB available (< ${SMALL_MIN_MB}); taking the BIG lane WITH PRIORITY"
        SMALL=0; WAS_SMALL=1
    else
        got=0
        for slot in $(seq 1 $SMALL_SLOTS); do
            exec 8>"$SMALL_LOCK.$slot"
            if flock -n 8; then got=$slot; break; fi
        done
        if [ "$got" != 0 ]; then
            echo "=== buildlock[small $got/$SMALL_SLOTS]: $NAME ===  available ${A} MB"
            "$@"; rc=$?
            echo ">> STAGE RESULT: BUILDLOCK RELEASED  $NAME rc=$rc  (small lane, available $(avail_mb) MB)"
            exit $rc
        fi
        echo "both small slots busy -- big lane queue, WITH PRIORITY"
        SMALL=0; WAS_SMALL=1
    fi
fi

# ------------------------------------------------------------------ big lane
#
# R2-3066c: SHORT JOBS GET QUEUE PRIORITY, WHICH IS THE REAL FIX.
#
# Lowering SMALL_MIN_MB was the wrong lever and I moved it twice before seeing
# that.  Measured under nine live agents, MemAvailable OSCILLATES between 844
# and 1487 MB, so no fixed floor is both safe and useful: above ~1000 the lane
# is dead whenever a big build is resident, and below it we start a second
# build into 844 MB -- where the OOM killer takes THE BIGGEST PROCESS, i.e.
# somebody's 10 GB film append, not the 400 MB job that caused it.  The lane
# would kill the thing it was protecting.
#
# So a small job that cannot get the small lane does NOT go to the back of the
# big queue.  It goes to the FRONT, by sorting its ticket under a "0-" prefix.
# It adds no memory pressure -- it still runs alone -- and it clears in a
# fraction of the time a film append takes, so the big jobs it passes lose
# very little.  That inverts the starvation without adding a single byte of
# concurrent footprint.
PRIO=1
[ "${WAS_SMALL:-0}" = 1 ] && PRIO=0
TICKET="$QDIR/$PRIO-$(date -u +%s%N)-$$.q"
echo "$NAME pid=$$" > "$TICKET"
trap 'rm -f "$TICKET"' EXIT

exec 9>"$LOCK"
announced=0
while :; do
    reap_q
    # Self-heal: if reap_q dropped my ticket for schema drift, or anything else
    # removed it, re-register under the CURRENT schema rather than spinning
    # forever against a head I can never equal.
    if [ ! -e "$TICKET" ]; then
        TICKET="$QDIR/$PRIO-$(date -u +%s%N)-$$.q"
        echo "$NAME pid=$$" > "$TICKET"
    fi
    # Oldest live waiter wins.  Names sort lexically by the nanosecond stamp.
    head="$(ls "$QDIR"/*.q 2>/dev/null | sort | head -1)"
    if flock -n 9; then
        if [ "$head" = "$TICKET" ] || [ -z "$head" ]; then break; fi
        flock -u 9                       # not my turn -- yield to the older waiter
    fi
    if [ "$announced" = 0 ]; then
        holder="$(cat "$LOCK.who" 2>/dev/null || echo unknown)"
        ahead=$(( $(ls "$QDIR"/*.q 2>/dev/null | wc -l) - 1 ))
        echo "BUILD LOCK HELD by '$holder'; $ahead waiter(s) ahead of me -- queuing, not racing."
        announced=1
    fi
    sleep 3
done

echo "$NAME pid=$$ since=$(date -u '+%H:%M:%S')" > "$LOCK.who"
rm -f "$TICKET"; trap - EXIT

A=$(avail_mb); S=$(swap_free_mb)
echo "=== buildlock: $NAME ===  available ${A} MB, swap free ${S} MB"
if [ "$A" -lt 700 ] && [ "$S" -lt 4000 ]; then
    echo ">> STAGE RESULT: BUILDLOCK REFUSED  (available ${A} MB, swap free ${S} MB)"
    echo "   Not starting a heavy build into this.  Nothing else holds the lock,"
    echo "   so the pressure is from processes that do not use it -- find them"
    echo "   (ps -eo rss,etime,comm --sort=-rss | head) before retrying."
    rm -f "$LOCK.who"; exit 3
fi

"$@"; rc=$?
echo ">> STAGE RESULT: BUILDLOCK RELEASED  $NAME rc=$rc  (available $(avail_mb) MB)"
rm -f "$LOCK.who"
exit $rc
