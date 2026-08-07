"""CONTROLS FOR `tools/gate_exit.py` — and for the fault it closes.

    python3 tools/gate_exit_selftest.py            [--quick]

Every claim this file makes is made twice: once by showing the NEW code does
the right thing, and once by showing the OLD code did the wrong thing, ON THE
SAME INPUT. A control that only exercises the fix cannot tell "fixed" from
"never broken", and this project has shipped one of those before — a check went
green because the miswiring it detected had been repaired upstream, so it was
asserting nothing.

So the positive controls here RE-CREATE the defects, from scratch, in temporary
files, and run them under the real Blender binary:

  1. BLENDER EXITS 0 ON AN UNCAUGHT EXCEPTION.  A script that raises is written
     out and run unguarded. If it ever starts exiting non-zero on its own, this
     control FAILS — and that is correct, because the wrapper would then be
     load-bearing for a reason that no longer exists and somebody should know.

  2. A GATE THAT PRINTS FAIL AND EXITS 0.  The original shape of
     placement_gate / collision_gate / instance_variety, reproduced in six
     lines. It must exit 0, or this file is not testing the thing it claims.

  3. A SCRIPT THAT STOPS EARLY WITHOUT RAISING.  Blender exits 0 for that too.

Then the same three, wrapped, must exit 2 / 1 / 2.

And then the REAL gates are run against the REAL control blends in
`render/world/assembly/r2/v120/`, because a unit test of the mapping proves
nothing about whether `placement_gate.py` actually returns its verdict.

THE CONTROLS ARE THEMSELVES CHECKED
===================================
`ctl_depth_neg.blend` spent a day floating the wheel 200 mm in the AIR, which
made it a second POSITIVE control while the battery counted it as the negative
one — two controls that must fail and none that must pass. So this file does
not merely assert that the negative controls exit 0: it asserts they exit 0
*having measured something*, by reading the report they wrote. A gate that
passes on an empty set is the failure mode, not the test of it.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
R2 = os.path.dirname(HERE)
V120 = os.path.join(R2, "render/world/assembly/r2/v120")
BLENDER = "/opt/blender-5.2.0-linux-x64/blender"

sys.path.insert(0, HERE)
import gate_exit                                                 # noqa: E402

ROWS, FAILS = [], []


def check(label, ok, detail=""):
    ROWS.append({"control": label, "ok": bool(ok), "detail": detail})
    print("   %-4s %-62s %s" % ("PASS" if ok else "FAIL", label, detail))
    if not ok:
        FAILS.append(label)


def blend_run(script_text, argv=(), blend=None, tmp=None):
    """Write `script_text` to a temp file, run it under Blender, return
    (returncode, combined output)."""
    p = os.path.join(tmp, "s%d.py" % abs(hash(script_text)))
    with open(p, "w") as f:
        f.write(script_text)
    cmd = [BLENDER, "-b"]
    if blend:
        cmd.append(blend)
    cmd += ["--factory-startup", "-P", p, "--"] + list(argv)
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=tmp)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


# ===========================================================================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true",
                    help="skip the real-gate runs (they cost ~90 s of Blender "
                         "starts); the fault reproductions still run")
    a = ap.parse_args()

    TMP = tempfile.mkdtemp(prefix="gate_exit_ctl_")
    print("scratch dir %s\n" % TMP)

    # ---- 1. THE MAPPING ---------------------------------------------------
    print("1. VERDICT STRING -> EXIT CODE")
    TABLE = [
        ("PLACEMENT_CLEAN", gate_exit.PASS),
        ("PLACEMENT_FAIL", gate_exit.FAIL),
        ("PLACEMENT_FAIL  [+3 context findings]", gate_exit.FAIL),
        ("PLACEMENT_VACUOUS", gate_exit.VACUOUS),
        ("COLLISION_CLEAN", gate_exit.PASS),
        ("COLLISION_FAIL (17 hits)", gate_exit.FAIL),
        ("COLLISION_VACUOUS", gate_exit.VACUOUS),
        ("DEPTH_PROBE_OK", gate_exit.PASS),
        ("DEPTH_PROBE_FAIL", gate_exit.FAIL),
        ("DEPTH_PROBE_VACUOUS", gate_exit.VACUOUS),
        ("INSTANCE_VARIETY_SPAM", gate_exit.FAIL),
        ("INSTANCE_VARIETY_CLEAN", gate_exit.PASS),
        ("ROADCLEAR_FAIL (4)", gate_exit.FAIL),
        ("ROADCLEAR_CLEAN", gate_exit.PASS),
        ("ITEM_ACCEPTED", gate_exit.PASS),
        ("ITEM_REJECTED", gate_exit.FAIL),
        ("ITEM_UNMEASURABLE", gate_exit.VACUOUS),
        ("RELIEF_CHECK_SUSPECT", gate_exit.FAIL),
        ("RELIEF_CHECK_VALIDATED", gate_exit.PASS),
    ]
    for tok, want in TABLE:
        got = gate_exit.code_for(tok)
        check("%-38s -> %s" % (tok, gate_exit.NAMES[want]), got == want,
              "" if got == want else "got %s" % gate_exit.NAMES[got])
    # THE DEFAULT MATTERS MORE THAN THE TABLE. An unknown verdict must not be
    # a pass; that default is the difference between a gate that fails safe
    # and one that fails silent.
    check("an UNRECOGNISED verdict is CRASH, not PASS",
          gate_exit.code_for("SOMETHING_NOBODY_HAS_DECIDED") == gate_exit.CRASH,
          "unknown -> %s" % gate_exit.NAMES[
              gate_exit.code_for("SOMETHING_NOBODY_HAS_DECIDED")])

    # ---- 2. THE FAULT ITSELF, REPRODUCED ---------------------------------
    print("\n2. POSITIVE CONTROLS — the ORIGINAL faults, rebuilt and run under "
          "the real\n   Blender. Each MUST exit 0, or this file is testing "
          "nothing.")

    RAISER = 'print("about to raise")\nraise RuntimeError("boom")\n'
    rc, out = blend_run(RAISER, tmp=TMP)
    check("bare `-P` script that RAISES exits 0 (Blender 5.2 swallows it)",
          rc == 0 and "RuntimeError" in out, "rc=%d" % rc)

    GATE_SHAPE = (
        'print(">> 3 PLACEMENT VIOLATIONS")\n'
        'print(">> STAGE RESULT: PLACEMENT_FAIL")\n')
    rc, out = blend_run(GATE_SHAPE, tmp=TMP)
    check("a gate that PRINTS `STAGE RESULT: PLACEMENT_FAIL` exits 0",
          rc == 0 and "PLACEMENT_FAIL" in out, "rc=%d" % rc)

    EARLY = ('import sys\nprint("half way")\n'
             'if True:\n    sys.settrace(None)\n'
             '# ... and the rest of the probe never runs\n')
    rc, _ = blend_run(EARLY, tmp=TMP)
    check("a script that simply stops early exits 0", rc == 0, "rc=%d" % rc)

    # ---- 3. THE SAME THREE, WRAPPED --------------------------------------
    print("\n3. NEGATIVE/POSITIVE CONTROLS ON THE FIX — the same three inputs, "
          "wrapped.")
    PRE = ('import sys\nsys.path.insert(0, %r)\nimport gate_exit\n' % HERE)

    rc, out = blend_run(
        PRE + 'def main():\n    raise RuntimeError("boom")\n'
              'gate_exit.guard(main, tool="ctl")\n', tmp=TMP)
    check("guard(): a main() that RAISES exits CRASH(2) and prints a traceback",
          rc == gate_exit.CRASH and "RuntimeError" in out, "rc=%d" % rc)

    rc, out = blend_run(
        PRE + 'def main():\n'
              '    return gate_exit.verdict("PLACEMENT_FAIL")\n'
              'gate_exit.guard(main, tool="ctl")\n', tmp=TMP)
    check("guard(): a FAIL verdict exits FAIL(1) AND prints STAGE RESULT",
          rc == gate_exit.FAIL and "STAGE RESULT: PLACEMENT_FAIL" in out,
          "rc=%d" % rc)

    rc, out = blend_run(
        PRE + 'def main():\n'
              '    return gate_exit.verdict("PLACEMENT_CLEAN")\n'
              'gate_exit.guard(main, tool="ctl")\n', tmp=TMP)
    check("guard(): a CLEAN verdict exits PASS(0)",
          rc == gate_exit.PASS and "PLACEMENT_CLEAN" in out, "rc=%d" % rc)

    rc, out = blend_run(
        PRE + 'def main():\n'
              '    return gate_exit.verdict("COLLISION_VACUOUS")\n'
              'gate_exit.guard(main, tool="ctl")\n', tmp=TMP)
    check("guard(): a VACUOUS verdict exits VACUOUS(3), not 0 and not 1",
          rc == gate_exit.VACUOUS, "rc=%d" % rc)

    rc, out = blend_run(
        PRE + 'def main():\n'
              '    raise SystemExit("REFUSING: no collection named X")\n'
              'gate_exit.guard(main, tool="ctl")\n', tmp=TMP)
    check("guard(): `raise SystemExit(\"REFUSING: ...\")` exits VACUOUS(3), "
          "not Python's 1",
          rc == gate_exit.VACUOUS and "REFUSING" in out, "rc=%d" % rc)

    rc, out = blend_run(
        PRE + 'def main():\n    raise SystemExit("something else broke")\n'
              'gate_exit.guard(main, tool="ctl")\n', tmp=TMP)
    check("guard(): SystemExit with a NON-refusal message stays FAIL(1)",
          rc == gate_exit.FAIL, "rc=%d" % rc)

    rc, out = blend_run(
        PRE + 'gate_exit.install(tool="ctl")\nraise RuntimeError("boom")\n',
        tmp=TMP)
    check("install(): a top-level script that RAISES exits CRASH(2)",
          rc == gate_exit.CRASH and "RuntimeError" in out, "rc=%d" % rc)

    rc, out = blend_run(
        PRE + 'gate_exit.install(tool="ctl")\nprint("half way")\n', tmp=TMP)
    check("install(): stopping WITHOUT done() exits CRASH(2) (the sentinel)",
          rc == gate_exit.CRASH and "INCOMPLETE" in out, "rc=%d" % rc)

    rc, out = blend_run(
        PRE + 'gate_exit.install(tool="ctl")\nprint("all done")\n'
              'gate_exit.done()\n', tmp=TMP)
    check("install(): reaching done() exits PASS(0)", rc == gate_exit.PASS,
          "rc=%d" % rc)

    rc, out = blend_run(
        PRE + 'gate_exit.install(tool="ctl")\n'
              'gate_exit.done("ROADCLEAR_FAIL (4)")\n', tmp=TMP)
    check("install(): done(<verdict>) exits on the verdict",
          rc == gate_exit.FAIL and "ROADCLEAR_FAIL (4)" in out, "rc=%d" % rc)

    if a.quick:
        return summarise(TMP)

    # ---- 4. THE REAL GATES, THE REAL CONTROL BLENDS ----------------------
    print("\n4. THE SHIPPED GATES against the shipped control blends.")
    CASES = [
        # tool,               blend,                     args,          want
        ("placement_gate",  "ctl_place_pos.blend",    [],  gate_exit.FAIL),
        ("placement_gate",  "ctl_place_neg.blend",    [],  gate_exit.PASS),
        ("collision_gate",  "ctl_collide_pos.blend",  [],  gate_exit.FAIL),
        ("collision_gate",  "ctl_collide_neg.blend",  [],  gate_exit.PASS),
        ("depth_probe", "ctl_depth_pos.blend", ["--frames", "1"], gate_exit.FAIL),
        ("depth_probe", "ctl_depth_float_pos.blend", ["--frames", "1"],
         gate_exit.FAIL),
        ("depth_probe", "ctl_depth_neg.blend", ["--frames", "1"], gate_exit.PASS),
        ("instance_variety", "ctl_variety_pos.blend", [], gate_exit.FAIL),
        ("instance_variety", "ctl_variety_neg.blend", [], gate_exit.PASS),
    ]
    reports = {}
    for tool, blend, extra, want in CASES:
        bp = os.path.join(V120, blend)
        if not os.path.exists(bp):
            check("%s on %s" % (tool, blend), False, "MISSING CONTROL BLEND")
            continue
        out_json = os.path.join(TMP, "%s_%s.json" % (tool, blend[:-6]))
        r = subprocess.run(
            [BLENDER, "-b", bp, "--factory-startup", "-P",
             os.path.join(HERE, tool + ".py"), "--", "--out", out_json] + extra,
            capture_output=True, text=True, cwd=TMP)
        txt = (r.stdout or "") + (r.stderr or "")
        said = [l for l in txt.splitlines() if "STAGE RESULT" in l]
        reports[(tool, blend)] = out_json
        # BOTH: the status AND the text. The defect was the two disagreeing, so
        # a control that only reads one of them could not have caught it.
        code_says = r.returncode == want
        text_says = bool(said) and gate_exit.code_for(
            said[-1].split("STAGE RESULT:")[1].strip()) == want
        check("%-16s %-26s -> %s" % (tool, blend, gate_exit.NAMES[want]),
              code_says and text_says,
              "rc=%d  %s" % (r.returncode, said[-1].strip() if said else
                             "NO STAGE RESULT LINE"))

    # ---- 5. ARE THE NEGATIVE CONTROLS ACTUALLY MEASURING? ----------------
    print("\n5. THE NEGATIVE CONTROLS MUST PASS BECAUSE THEY MEASURED "
          "SOMETHING CLEAN,\n   not because they measured nothing. "
          "(ctl_depth_neg.blend was a second\n   POSITIVE control for a day, "
          "and no assertion noticed.)")
    p = reports.get(("depth_probe", "ctl_depth_neg.blend"))
    if p and os.path.exists(p):
        d = json.load(open(p))
        rows = [r for fr in d.get("frames", {}).values() for r in fr.values()]
        verdicts = sorted({r.get("verdict") for r in rows})
        nvert = sum(r.get("vertices_in_plan", 0) for r in rows)
        check("depth NEGATIVE control measured >0 vertices and none FLOATING/"
              "PENETRATION",
              bool(rows) and nvert > 0 and not d.get("vacuous")
              and not ({"FLOATING", "PENETRATION"} & set(verdicts)),
              "%d surface-frame row(s), %d vertices, verdicts %s"
              % (len(rows), nvert, verdicts))
    else:
        check("depth NEGATIVE control report is readable", False, "no report")

    p = reports.get(("collision_gate", "ctl_collide_neg.blend"))
    if p and os.path.exists(p):
        d = json.load(open(p))
        check("collision NEGATIVE control tested frames and found 0 hits "
              "(not vacuous)",
              bool(d.get("frames")) and not d.get("vacuous")
              and d.get("total_hits") == 0,
              "frames=%s hits=%s vacuous=%s"
              % (list(d.get("frames") or {}), d.get("total_hits"),
                 d.get("vacuous")))

    p = reports.get(("instance_variety", "ctl_variety_neg.blend"))
    if p and os.path.exists(p):
        d = json.load(open(p))
        check("variety NEGATIVE control realized >0 instances",
              d.get("total_instances", 0) > 0,
              "%s instances over %s families"
              % (d.get("total_instances"), len(d.get("families") or [])))

    p = reports.get(("placement_gate", "ctl_place_neg.blend"))
    if p and os.path.exists(p):
        d = json.load(open(p))
        check("placement NEGATIVE control is CLEAN, and the gate did not "
              "declare it vacuous", d.get("total") == 0, "total=%s"
              % d.get("total"))

    # ---- 6. VACUOUS AND CRASH, ON REAL GATES ------------------------------
    print("\n6. REFUSAL AND CRASH, from the shipped gates themselves.")
    r = subprocess.run(
        [BLENDER, "-b", "--factory-startup", "-P",
         os.path.join(HERE, "collision_gate.py"), "--",
         "--out", os.path.join(TMP, "vac.json")],
        capture_output=True, text=True, cwd=TMP)
    txt = (r.stdout or "") + (r.stderr or "")
    check("collision_gate on a scene with NO car and NO showroom -> VACUOUS(3)",
          r.returncode == gate_exit.VACUOUS and "COLLISION_VACUOUS" in txt,
          "rc=%d" % r.returncode)

    # placement_gate's own vacuous case: every mesh matched --allow, so nothing
    # was measured. It used to print PLACEMENT_CLEAN off zero measurements --
    # the same hole collision_gate and depth_probe were fixed for, in the gate
    # that had never been checked for it.
    r = subprocess.run(
        [BLENDER, "-b", "--factory-startup", "-P",
         os.path.join(HERE, "placement_gate.py"), "--",
         "--out", os.path.join(TMP, "vac2.json"), "--allow", "Cube"],
        capture_output=True, text=True, cwd=TMP)
    txt = (r.stdout or "") + (r.stderr or "")
    check("placement_gate with every mesh --allow'ed (0 measured) -> "
          "VACUOUS(3), not CLEAN",
          r.returncode == gate_exit.VACUOUS and "PLACEMENT_VACUOUS" in txt,
          "rc=%d" % r.returncode)

    r = subprocess.run(
        [BLENDER, "-b", "--factory-startup", "-P",
         os.path.join(HERE, "instance_variety.py"), "--",
         "--out", os.path.join(TMP, "vac3.json")],
        capture_output=True, text=True, cwd=TMP)
    txt = (r.stdout or "") + (r.stderr or "")
    check("instance_variety on a scene with ZERO realized instances -> "
          "VACUOUS(3)",
          r.returncode == gate_exit.VACUOUS
          and "INSTANCE_VARIETY_VACUOUS" in txt, "rc=%d" % r.returncode)

    r = subprocess.run(
        [BLENDER, "-b", "--factory-startup", "-P",
         os.path.join(HERE, "placement_gate.py"), "--",
         "--out", os.path.join(TMP, "x.json"),
         "--spec", os.path.join(TMP, "no_such_spec.json")],
        capture_output=True, text=True, cwd=TMP)
    check("placement_gate with a --spec that does not exist -> CRASH(2), "
          "not 0", r.returncode == gate_exit.CRASH,
          "rc=%d" % r.returncode)

    r = subprocess.run(
        [BLENDER, "-b", "--factory-startup", "-P",
         os.path.join(HERE, "placement_gate.py"), "--", "--selftest"],
        capture_output=True, text=True, cwd=TMP)
    check("placement_gate --selftest still exits 0 (the wrapper did not break "
          "it)", r.returncode == gate_exit.PASS, "rc=%d" % r.returncode)

    # ---- 7. TWO VERDICTS IN ONE LOG, AND THE LAST ONE IS A PASS. R2-1084 --
    print("\n7. A LOG WITH TWO VERDICTS. The last line is the verdict of the "
          "OUTERMOST\n   stage, not of the build. Section 4 above reads "
          "`said[-1]`, and so did every\n   other reader in this project, "
          "which is why this went unseen:\n   build_verify_scene.py chains "
          "build_camera_rig.py, the rig printed\n   CAMERA_RIG_FAIL and "
          "RETURNED, and the re-key stage finished and printed\n   its own "
          "pass underneath it.")

    TWO = (">> ONER camera: 532 keys over 2978 frames\n"
           "   FAIL 1_assembly: subject reaches 1.155 of the half-frame at "
           "frame 431 (margin 0.92)\n"
           ">> STAGE RESULT: CAMERA_RIG_FAIL\n"
           ">> re-keyed 2978 frames\n"
           ">> STAGE RESULT: FILM_SCENE_REKEYED_R2851\n")

    # The control that matters: the OLD reader must call this a pass, or this
    # case is not reproducing the fault and proves nothing about the fix.
    old_reader = gate_exit.code_for(
        [l for l in TWO.splitlines() if "STAGE RESULT" in l][-1]
        .split("STAGE RESULT:")[1].strip())
    check("the last-line reader calls the two-verdict log a PASS "
          "(the fault, reproduced)",
          old_reader == gate_exit.PASS,
          "last-line -> %s" % gate_exit.NAMES[old_reader])

    rc, found = gate_exit.scan(TWO)
    check("scan() reads BOTH verdicts and returns FAIL(1)",
          rc == gate_exit.FAIL and len(found) == 2,
          "rc=%s, %d verdict(s): %s" % (gate_exit.NAMES[rc], len(found),
                                        [t for t, _ in found]))

    # Not vacuous: it must still pass a log that is genuinely clean.
    rc, found = gate_exit.scan(">> STAGE RESULT: CAMERA_RIG_CONTINUOUS_AND_"
                               "AIMED\n>> STAGE RESULT: FILM_SCENE_REKEYED_X\n")
    check("scan() passes a log whose verdicts are ALL clean",
          rc == gate_exit.PASS and len(found) == 2,
          "rc=%s" % gate_exit.NAMES[rc])

    rc, found = gate_exit.scan("built 2978 frames\nno verdict here\n")
    check("scan() calls a log with NO verdict CRASH(2), not PASS",
          rc == gate_exit.CRASH and not found, "rc=%s" % gate_exit.NAMES[rc])

    # Severity, not numeric order: VACUOUS is 3 and CRASH is 2, and a crash
    # among refusals must still be the status.
    rc, _ = gate_exit.scan(">> STAGE RESULT: COLLISION_VACUOUS\n"
                           ">> STAGE RESULT: WHAT_IS_THIS\n"
                           ">> STAGE RESULT: PLACEMENT_CLEAN\n")
    check("scan() reduces {VACUOUS, CRASH, PASS} to CRASH(2)",
          rc == gate_exit.CRASH, "rc=%s" % gate_exit.NAMES[rc])

    rc, _ = gate_exit.scan(">> STAGE RESULT: COLLISION_VACUOUS\n"
                           ">> STAGE RESULT: PLACEMENT_FAIL\n")
    check("scan() reduces {VACUOUS, FAIL} to FAIL(1)",
          rc == gate_exit.FAIL, "rc=%s" % gate_exit.NAMES[rc])

    # The rig's own tokens had NO code before R2-1084 -- both were CRASH, which
    # is why build_camera_rig.py could not adopt this module until they did.
    for tok, want in (("CAMERA_RIG_CONTINUOUS_AND_AIMED", gate_exit.PASS),
                      ("CAMERA_RIG_FAIL", gate_exit.FAIL),
                      ("SEAM_BRIDGE_MOVED_BEAT1", gate_exit.FAIL),
                      ("FILM_SCENE_REKEYED_R2851", gate_exit.PASS)):
        got = gate_exit.code_for(tok)
        check("code_for(%s) is %s" % (tok, gate_exit.NAMES[want]), got == want,
              "-> %s" % gate_exit.NAMES[got])

    # THE CLI, which is how a batch step actually uses this.
    lp = os.path.join(TMP, "two_verdict.log")
    with open(lp, "w") as fh:
        fh.write(TWO)
    r = subprocess.run([sys.executable, os.path.join(HERE, "gate_exit.py"), lp],
                       capture_output=True, text=True, cwd=TMP)
    check("`python tools/gate_exit.py <log>` exits FAIL(1) on that log",
          r.returncode == gate_exit.FAIL
          and "THE LAST LINE IS A PASS" in (r.stdout or ""),
          "rc=%d" % r.returncode)

    return summarise(TMP)


def summarise(tmp):
    print()
    if FAILS:
        print(">> %d CONTROL(S) MISBEHAVED:" % len(FAILS))
        for f in FAILS:
            print("     " + f)
        print(">> STAGE RESULT: GATE_EXIT_SELFTEST_FAIL")
        return 1
    print(">> all %d controls behaved (scratch %s)" % (len(ROWS), tmp))
    shutil.rmtree(tmp, ignore_errors=True)
    print(">> STAGE RESULT: GATE_EXIT_SELFTEST_OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
