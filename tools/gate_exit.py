"""EXIT STATUS FOR GATES — the verdict the shell can read.

WHY THIS EXISTS
===============
A gate reported a failure in its text and told the shell it had succeeded.

    $ blender -b world.blend -P tools/placement_gate.py -- --out p.json
    >> 3 PLACEMENT VIOLATIONS (ranked by intrusion depth)
    >> STAGE RESULT: PLACEMENT_FAIL
    $ echo $?
    0

That was true of `placement_gate.py`, `collision_gate.py`,
`instance_variety.py`, `placement_depth.py`, `relief_control_measure.py` and
`v120/probe_roadclear.py` simultaneously. Their `--selftest` paths exited 1
correctly; a REAL violation did not. Any batch, chain or CI step that branched
on `$?` saw success while the report on disk said FAIL.

Two further holes made it worse, and both are closed here:

  * BLENDER 5.2 EXITS 0 ON AN UNCAUGHT SCRIPT EXCEPTION. Measured on this box:
    `blender -b --factory-startup -P raise.py` prints the traceback and returns
    0. A gate that CRASHES was indistinguishable from a gate that PASSED, for
    every `-P` entry point in the project. (`sys.exit(N)` from inside the script
    IS honoured — also measured — which is what makes the wrapper below work.)

  * "COULD NOT MEASURE" WAS SPELLED 0. `collision_gate` and `depth_probe`
    already say VACUOUS in their text and already refuse to report — and then
    returned 0, which is the one thing a refusal must not do. This project
    treats vacuous as NOT A PASS, so it gets its own code.

THE CODES
=========
    0  PASS      the gate measured something and it was clean
    1  FAIL      the gate measured something and it was not clean
    2  CRASH     the gate did not produce a verdict: uncaught exception, bad
                 arguments, missing input file. argparse already uses 2 for a
                 usage error, so this agrees with it rather than fighting it.
    3  VACUOUS   the gate ran, refused, and said why: nothing in the scene for
                 it to test, no overlap to measure, subject not found. NOT a
                 pass, and deliberately distinguishable from FAIL so a caller
                 can tell "your world is broken" from "you pointed me at the
                 wrong file".

Anything non-zero is not a pass. A caller that only knows `if rc:` is still
correct; a caller that wants to tell the three apart now can.

HOW TO USE IT
=============
A tool with a `main()` (everything in `tools/`)::

    import gate_exit
    ...
    if __name__ == "__main__":
        gate_exit.guard(main)                 # main returns a code, or raises

and inside `main`, end with::

        return gate_exit.verdict("PLACEMENT_FAIL" if worst else "PLACEMENT_CLEAN")

`verdict()` prints the `>> STAGE RESULT: ...` line AND returns the matching
code, from the same string, so the text and the status cannot disagree —
which is exactly how they came to disagree in the first place.

A top-level script with no `main()` (`probeA.py` .. `probeK.py`, which are
executed straight down by `-P`)::

    gate_exit.install(tool="probeA")          # first thing after the imports
    ...
    gate_exit.done()                          # last line of the file

`install()` sets `sys.excepthook`, so an exception exits 2 instead of 0, and
arms an `atexit` sentinel so a script that stops early WITHOUT raising — a
bare `return`-shaped bail, an `os.exit` somewhere in a library — also fails
rather than passing silently. `done()` disarms the sentinel.

WHAT THIS MODULE DOES NOT DO
============================
It does not decide anything. It maps a verdict string that the gate already
prints onto a number, and it makes an exception loud. A gate that classifies
wrongly will still classify wrongly, at a non-zero exit status.

It is deliberately ONE file, imported, not copied. A private copy of shared
behaviour is what defeated the socket guard (R2-057): three docstrings cited
`itemkit.socket_audit()`, which does not exist.  PHANTOM-OK  If you find yourself pasting
`try: main() except: sys.exit(1)` into a gate, import this instead.

CONTROLS
========
`tools/gate_exit_selftest.py` — every code, the excepthook under real Blender,
the atexit sentinel, and a positive control that reproduces the ORIGINAL fault
(a gate that prints FAIL and exits 0) and shows this module rejecting it.
"""

import os
import sys
import traceback

PASS = 0
FAIL = 1
CRASH = 2
VACUOUS = 3

NAMES = {PASS: "PASS", FAIL: "FAIL", CRASH: "CRASH", VACUOUS: "VACUOUS"}

# ---------------------------------------------------------------------------
# Verdict string -> code.
#
# Matched on SUBSTRINGS of the verdict token because the project's verdicts are
# composed, not enumerated: "PLACEMENT_FAIL  [+3 context findings]",
# "COLLISION_FAIL (17 hits)", "ROADCLEAR_FAIL (4)". Order matters — VACUOUS and
# the refusal words are tested before FAIL so that a token containing both
# lands on the more specific one.
# ---------------------------------------------------------------------------
_VACUOUS_MARKERS = ("VACUOUS", "REFUS", "UNMEASURABLE", "NOT_MEASURED",
                    "NOTHING_TESTED", "UNDECLARED", "SKIPPED",
                    # R2-3181: a CONTROL that could not perturb the thing it
                    # tests. `placement_determinism_control.py` reported FAIL
                    # for that, which reads as "the gate under test is broken"
                    # and sends the next reader to debug an innocent gate. "I
                    # could not test this" is exactly the VACUOUS case this
                    # module already defines, so it gets that code and not FAIL.
                    "INAPPLICABLE")
_FAIL_MARKERS = ("FAIL", "VIOLAT", "REJECT", "SUSPECT", "MISBEHAV", "SPAM",
                 "STRAGGLER", "STILL_MISSING", "OUT_OF_RANGE", "BROKEN",
                 "INTRUSION", "COLLIDE", "NOT_CLEAN", "STALE",
                 # R2-1084: the camera rig's own refusal, which used to be
                 # printed and then walked past. Listed before the PASS markers
                 # get a look, as every FAIL marker is.
                 "SEAM_BRIDGE_MOVED")
_PASS_MARKERS = ("CLEAN", "_OK", "OK_", "PASS", "ACCEPT", "VALIDATED",
                 "MONOTONIC", "BUILT", "NO_BEAT_CLIPS", "AIRBORNE_OK",
                 # R2-1084: anim/build_camera_rig.py and the re-key stage.
                 # Both were UNRECOGNISED, i.e. CRASH, which is why neither
                 # could adopt this module without saying so first. Spelled in
                 # full rather than as "AIMED"/"REKEY" so a future
                 # CAMERA_RIG_AIM_FAIL cannot be swallowed by a loose prefix.
                 "CONTINUOUS_AND_AIMED", "REKEYED")


def code_for(verdict):
    """The exit code implied by a `STAGE RESULT` verdict string.

    Unrecognised is CRASH, not PASS. A verdict this module has never seen is a
    verdict nobody has decided the meaning of, and defaulting an unknown to
    success is the whole family of bug this file exists to close.
    """
    v = str(verdict).upper()
    for m in _VACUOUS_MARKERS:
        if m in v:
            return VACUOUS
    for m in _FAIL_MARKERS:
        if m in v:
            return FAIL
    for m in _PASS_MARKERS:
        if m in v:
            return PASS
    return CRASH


def verdict(token, detail="", stream=None):
    """Print `>> STAGE RESULT: <token><detail>` and return its exit code.

    ONE call site produces both the human-readable verdict and the machine
    -readable one, from the same string. That is the point: the defect was two
    independent statements of the same fact, one of which was wrong.
    """
    out = stream or sys.stdout
    rc = code_for(token)
    if rc == CRASH:
        print(">> gate_exit: verdict %r is not one this project has a code for; "
              "treating it as CRASH rather than guessing it is a pass." % token,
              file=out)
    print(">> STAGE RESULT: %s%s" % (token, detail), file=out)
    out.flush()
    return rc


# ---------------------------------------------------------------------------
# EVERY verdict in a log, not the last one. R2-1084.
#
# A stage that CHAINS another stage prints two verdicts. `build_verify_scene.py`
# loads `anim/build_camera_rig.py` and calls its `main()` in-process; the rig
# printed `>> STAGE RESULT: CAMERA_RIG_FAIL` and *returned*, so the caller ran on
# to its own work and printed its own passing verdict underneath. The log then
# ends in a pass and the build is judged on it.
#
# Every reader in this project took the LAST line -- including
# gate_exit_selftest.py, which is the control that is supposed to catch this
# family. The last line is the verdict of the OUTERMOST stage, which is not the
# same claim as "the build is clean", and the difference is invisible in exactly
# the case that matters.
#
# So: a log has ONE status, and it is the worst thing anybody printed in it.
# ---------------------------------------------------------------------------
import re                                                          # noqa: E402

_VERDICT_RE = re.compile(r">>\s*STAGE RESULT:\s*(\S+)")

# Severity order for reducing many verdicts to one status. NOT numeric order:
# VACUOUS is 3 and CRASH is 2, and "the gate blew up" outranks "the gate
# refused". PASS is last precisely so that one pass among failures never wins.
_SEVERITY = (CRASH, FAIL, VACUOUS, PASS)


def scan(text):
    """Every `STAGE RESULT` verdict in `text`, worst-first status.

    Returns `(rc, found)` where `found` is a list of `(token, code)` in the
    order printed and `rc` is the worst code among them.

    A text with NO verdict line at all is CRASH, not PASS: a stage that
    produced no verdict did not pass, and Blender exits 0 on an uncaught
    exception, so silence is the shape a crash actually has here.
    """
    found = [(t, code_for(t)) for t in _VERDICT_RE.findall(text or "")]
    if not found:
        return CRASH, found
    codes = {c for _, c in found}
    for sev in _SEVERITY:
        if sev in codes:
            return sev, found
    return CRASH, found


def scan_report(text, source="<text>", stream=None):
    """`scan()`, printed. Returns the same code."""
    out = stream or sys.stdout
    rc, found = scan(text)
    if not found:
        print(">> gate_exit.scan %s: NO STAGE RESULT LINE — a stage that "
              "printed no verdict did not pass." % source, file=out)
        return rc
    print(">> gate_exit.scan %s: %d verdict(s)" % (source, len(found)), file=out)
    for i, (tok, c) in enumerate(found, 1):
        mark = "  " if c == PASS else "<<"
        print("   %s %d/%d  %-34s %s" % (mark, i, len(found), tok, NAMES[c]),
              file=out)
    if rc != PASS:
        bad = [t for t, c in found if c != PASS]
        last = found[-1]
        print(">> gate_exit.scan %s: STATUS %s — %d non-pass verdict(s): %s"
              % (source, NAMES[rc], len(bad), ", ".join(bad)), file=out)
        if last[1] == PASS:
            print("   THE LAST LINE IS A PASS (%s) AND THE BUILD IS NOT. "
                  "This is R2-1084: judging on the last verdict reports "
                  "success here." % last[0], file=out)
    else:
        print(">> gate_exit.scan %s: STATUS PASS — all %d verdict(s) clean"
              % (source, len(found)), file=out)
    out.flush()
    return rc


# ---------------------------------------------------------------------------
# The Blender wrapper.
# ---------------------------------------------------------------------------
def _emit_traceback(tool):
    # stdout is block-buffered when a battery redirects it into a log file and
    # stderr is not. Without these flushes the traceback lands at the TOP of the
    # log, above the evidence that produced it — measured, and it cost a reader
    # twenty minutes. Same reasoning as build_verify_scene.py, which is where
    # this behaviour was first written by hand.
    sys.stdout.flush()
    sys.stderr.flush()
    traceback.print_exc()
    print(">> STAGE RESULT: %s_CRASH" % (tool or "GATE"), file=sys.stderr)
    sys.stdout.flush()
    sys.stderr.flush()


def guard(main, tool=None):
    """Run `main()` and exit with a status that reflects what happened.

    `main` may return an int (used as-is), None (treated as PASS — the many
    tools that simply print and stop), or raise.

    A `SystemExit` carrying a STRING is Python's "die with a message" idiom and
    the project uses it heavily for refusals (`raise SystemExit("REFUSING: no
    collection named ...")`). Python maps that to status 1, i.e. to FAIL, which
    would file "you pointed me at the wrong blend" under "your world is broken".
    A message that announces a refusal is mapped to VACUOUS instead.
    """
    tool = tool or os.path.basename(getattr(main, "__module__", "") or "gate")
    try:
        rc = main()
    except SystemExit as e:                                     # noqa: PERF203
        c = e.code
        if c is None:
            sys.exit(PASS)
        if isinstance(c, int):
            sys.exit(c)
        # a message: print it where a message belongs, then classify it
        print(str(c), file=sys.stderr)
        sys.stderr.flush()
        up = str(c).upper()
        sys.exit(VACUOUS if any(m in up for m in _VACUOUS_MARKERS) else FAIL)
    except KeyboardInterrupt:
        _emit_traceback(tool)
        sys.exit(CRASH)
    except BaseException:                                       # noqa: BLE001
        # BaseException, not Exception: Blender scripts hit MemoryError and
        # RecursionError on 4 GB scenes, and those must not exit 0 either.
        _emit_traceback(tool)
        sys.exit(CRASH)
    if rc is None or rc is True:
        sys.exit(PASS)
    if isinstance(rc, int):
        sys.exit(rc)
    # Many tools here `return` a report dict or a list from main(). That is not
    # a status, and coercing it would be inventing one -- so it is PASS (the
    # tool ran to completion) and it SAYS the status came from completion
    # rather than from a verdict, which is the distinction this module exists
    # to keep.
    print(">> gate_exit: %s.main() returned a %s, not an exit code; the status "
          "below means 'ran to completion', not 'passed a check'."
          % (tool, type(rc).__name__), file=sys.stderr)
    sys.exit(PASS)


# ---------------------------------------------------------------------------
# The top-level-script wrapper, for the probes that have no main().
# ---------------------------------------------------------------------------
_STATE = {"armed": False, "tool": "probe", "finished": False}


def _excepthook(etype, evalue, etb):
    sys.stdout.flush()
    sys.stderr.flush()
    traceback.print_exception(etype, evalue, etb)
    print(">> STAGE RESULT: %s_CRASH" % _STATE["tool"].upper(), file=sys.stderr)
    sys.stdout.flush()
    sys.stderr.flush()
    # os._exit, not sys.exit: we are already inside the interpreter's
    # unwinding, and Blender will otherwise carry on to its own quit path and
    # return 0 — which is the entire defect.
    os._exit(CRASH)


def _sentinel():
    if _STATE["armed"] and not _STATE["finished"]:
        print(">> gate_exit: %s stopped before calling done(). It did not "
              "finish, so it did not pass." % _STATE["tool"], file=sys.stderr)
        print(">> STAGE RESULT: %s_INCOMPLETE" % _STATE["tool"].upper(),
              file=sys.stderr)
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(CRASH)


def install(tool="probe", sentinel=True):
    """Arm crash detection for a straight-line `-P` script.

    Call it once, immediately after the imports, and call `done()` on the last
    line. Between those two points an uncaught exception exits CRASH instead of
    Blender's 0, and stopping early without raising exits CRASH too.
    """
    import atexit
    _STATE["tool"] = tool
    _STATE["finished"] = False
    sys.excepthook = _excepthook
    if sentinel and not _STATE["armed"]:
        atexit.register(_sentinel)
    _STATE["armed"] = bool(sentinel)


def done(token=None, detail=""):
    """Disarm the sentinel. With a verdict token, exit on it as well."""
    _STATE["finished"] = True
    if token is not None:
        sys.exit(verdict(token, detail))


def selftest_summary():
    """What the codes mean, for a report that wants to quote them."""
    return dict(PASS=PASS, FAIL=FAIL, CRASH=CRASH, VACUOUS=VACUOUS)


if __name__ == "__main__":
    # With log files: scan them and EXIT ON THE WORST VERDICT IN THEM.
    #     python tools/gate_exit.py build.log        # $? is the real status
    #     blender ... | tee build.log; python tools/gate_exit.py build.log
    args = [a for a in sys.argv[1:] if a != "-"]
    if sys.argv[1:]:
        worst = PASS
        srcs = args or ["<stdin>"]
        for src in srcs:
            txt = sys.stdin.read() if src == "<stdin>" else open(src).read()
            rc = scan_report(txt, source=src)
            if rc != PASS and (worst == PASS or
                               _SEVERITY.index(rc) < _SEVERITY.index(worst)):
                worst = rc
        sys.exit(worst)

    print(__doc__)
    for tok in ("PLACEMENT_CLEAN", "PLACEMENT_FAIL", "COLLISION_VACUOUS",
                "DEPTH_PROBE_OK", "ITEM_REJECTED", "WHAT_IS_THIS",
                "CAMERA_RIG_FAIL", "CAMERA_RIG_CONTINUOUS_AND_AIMED"):
        print("  %-32s -> %d (%s)" % (tok, code_for(tok), NAMES[code_for(tok)]))
