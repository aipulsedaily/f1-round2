"""THE DETERMINISM ASSERTION, WATCHED TO FAIL.                    (R2-2341, #97)

    /opt/blender-5.2.0-linux-x64/blender -b <any small scene.blend> \
        --factory-startup -noaudio -P tools/placement_determinism_control.py -- \
        --out work/.../determinism_control.json [--spec ... --telemetry ...]

WHY THIS FILE EXISTS SEPARATELY FROM `--selftest`
=================================================
`placement_gate.py --repeat N` now measures the same unchanged scene N times
and REFUSES to issue a verdict unless every pass agrees. That assertion is
worth exactly as much as the evidence that it can fail.

    A CONTROL THAT HAS NEVER FAILED IS NOT A CONTROL.

Every real scene is (now) deterministic, so no real scene can test it. This
file makes one that is not: it wraps `placement_gate.measure` so that the
SECOND pass returns a deliberately different closest approach -- one object
name, changed, nothing else -- and then runs the gate's own `main()` end to
end and requires it to refuse.

Then it removes the perturbation and requires the very same `main()`, on the
very same scene, to produce a verdict again. Both halves are needed: an
assertion that fires on everything is not a control either, it is a brick.

WHAT IS PERTURBED, AND WHY THAT AND NOT SOMETHING ELSE
-----------------------------------------------------
The injected difference is a `closest_approach` OBJECT NAME on an otherwise
identical pass. That is the smallest possible version of the exact defect #97
is named for -- the figure that moved between two runs of an unchanged world.
A perturbation of `violations` would be caught by any diff; this one has to be
caught by the part that reads `closest`, which is the part that was missing.

THE TWO-VERDICT TRAP
--------------------
`main()` prints its own `>> STAGE RESULT:` line, twice, once per half. Both are
captured and NOT allowed to reach the caller's log, because a run that prints a
refusal and then a pass has an unread verdict and this project has been burned
by that. Exactly one `>> STAGE RESULT:` line is printed by this file, at the
end, and it is this control's own.
"""
import argparse
import contextlib
import io
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
import placement_gate as PG                                       # noqa: E402
import gate_exit                                                  # noqa: E402

R2 = "/home/zany/f1-round2"


def _run_gate(argv_tail):
    """Run `placement_gate.main()` with these `--` arguments; return
    (verdict_token, exit_code, captured_stdout)."""
    saved = sys.argv
    sys.argv = ["blender", "--"] + argv_tail
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            code = PG.main()
    finally:
        sys.argv = saved
    out = buf.getvalue()
    tok = None
    for line in out.splitlines():
        if ">> STAGE RESULT:" in line:
            tok = line.split(">> STAGE RESULT:", 1)[1].strip()
    return tok, code, out


def main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True, help="report path the gate writes")
    p.add_argument("--spec", default=os.path.join(R2, "docs/circuit_spec.json"))
    p.add_argument("--telemetry",
                   default=os.path.join(R2, "telemetry/telemetry.csv"))
    p.add_argument("--sheet", default=os.path.join(R2, "docs/beat_sheet.json"))
    p.add_argument("--campath",
                   default=os.path.join(R2, "world/camera_rig_path.json"))
    a = p.parse_args(argv)

    tail = ["--out", a.out, "--spec", a.spec, "--telemetry", a.telemetry,
            "--sheet", a.sheet, "--campath", a.campath, "--repeat", "2"]

    real_measure = PG.measure
    state = {"n": 0}

    def flaky_measure(*args, **kw):
        """`measure()`, made non-deterministic ON PURPOSE. Pass 0 is the truth;
        pass 1 renames whoever won `closest_approach` on the road corridor.
        Nothing about the scene changes -- only the answer does, which is the
        whole shape of the defect."""
        res = real_measure(*args, **kw)
        state["n"] += 1
        if state["n"] % 2 == 0:
            violations, ctxf, marg, closest, tested, coarse, diag = res
            closest = dict(closest)
            for k in sorted(closest):
                d, name, at = closest[k]
                closest[k] = (d, name + "_INJECTED", at)
                break
            res = (violations, ctxf, marg, closest, tested, coarse, diag)
        return res

    rows = []
    fails = []

    def check(name, got, want, detail=""):
        ok = (got == want)
        rows.append((name, got, want, detail, ok))
        print("   %s  %-58s got=%-34s expected=%s  %s"
              % ("PASS" if ok else "FAIL", name, got, want, detail))
        if not ok:
            fails.append(name)

    print(">> DETERMINISM CONTROL: the assertion is fed a non-deterministic "
          "input FIRST, and must refuse.")
    PG.measure = flaky_measure
    try:
        tok_bad, code_bad, out_bad = _run_gate(tail)
    finally:
        PG.measure = real_measure
    for line in out_bad.splitlines():
        if "MEASURED DIFFERENTLY" in line or "REFUSING TO REPORT" in line \
                or "determinism:" in line:
            print("      [gate said] %s" % line.strip())
    check("a deliberately non-deterministic measure() is REFUSED",
          tok_bad, "PLACEMENT_NONDETERMINISTIC_REFUSED",
          "exit code %s" % code_bad)
    check("...and the refusal is NOT spelled as a pass",
          code_bad != gate_exit.PASS, True, "code %s" % code_bad)

    print("\n>> DETERMINISM CONTROL: perturbation removed, same scene, same "
          "arguments -- the gate must now produce a verdict.")
    state["n"] = 0
    tok_ok, code_ok, out_ok = _run_gate(tail)
    for line in out_ok.splitlines():
        if "determinism:" in line or "closest approach" in line:
            print("      [gate said] %s" % line.strip())
    check("the unperturbed run is NOT refused as non-deterministic",
          tok_ok != "PLACEMENT_NONDETERMINISTIC_REFUSED", True,
          "verdict %s (exit %s)" % (tok_ok, code_ok))
    check("the unperturbed run reaches a real placement verdict",
          bool(tok_ok) and tok_ok.split()[0] in
          ("PLACEMENT_CLEAN", "PLACEMENT_FAIL", "PLACEMENT_VACUOUS"), True,
          "verdict %s" % tok_ok)

    print("")
    if fails:
        print(">> %d DETERMINISM CONTROL(S) MISBEHAVED: %s" % (len(fails), fails))
        return gate_exit.verdict("PLACEMENT_DETERMINISM_CONTROL_FAIL")
    print(">> the determinism assertion has been observed to FAIL on a "
          "non-deterministic input and to PASS on the same scene without it")
    return gate_exit.verdict("PLACEMENT_DETERMINISM_CONTROL_OK")


if __name__ == "__main__":
    gate_exit.guard(main, tool="placement_determinism_control")
