"""Diff two vertex fingerprints. -> did every built vertex actually move?

    python3 fp_diff.py OLD.json NEW.json [--expect-moved N | --expect-any-move]
    python3 fp_diff.py --selftest

THIS FILE PRINTED ITS ANSWER AND THREW ITS VERDICT AWAY   (fixed 2026-08-03)
===========================================================================
`v122/battery.sh` states, in capitals, the prediction its whole run rests on:

    "fp_diff must find ZERO moved objects. A moved object would mean a module
     other than mine changed under me ... and would have to be chased before
     anything else in this report is believed."

`moved` was computed on line 10, printed on line 18, and **never consulted**.
There was no `sys.exit`, no `STAGE RESULT`, no `gate_exit` -- the script fell
off the end, returned 0, and `lib_battery.sh :: run()` recorded `ok`. The
battery's FIRST and most load-bearing assertion could print "100.00 %" and the
run would still end `>> STAGE RESULT: BATTERY_OK`.

The vacuous branch was worse: two fingerprints with no object names in common
printed their own refusal -- "the two scenes cannot be compared" -- and also
exited 0. That is a comparison that did not happen, scored as a comparison that
passed.

So: the expectation is now DECLARED on the command line and CHECKED, and the
no-common-names case is a refusal with a status (3), not a pass.

    --expect-moved N     exactly N common objects may have moved. This is what
                         v121/v122 want, with N = 0 and N = 1 respectively.
    --expect-any-move    at least one must have moved. For the other direction:
                         a rebuild that was supposed to change something and did
                         not is the same defect wearing the other sign, and it
                         is how a harness measured a four-day-old blend and
                         called it a null.
    (neither)            a printout, not a check. It exits 3 (VACUOUS) and says
                         so, because a bare run scored as a pass is the defect
                         this file was repaired for.

EXIT CODES, matching tools/gate_exit.py: 0 PASS  1 FAIL  2 CRASH  3 VACUOUS
"""
import json
import sys


def load(path):
    d = json.load(open(path))
    return d


def diff(a, b):
    A, B = a["rows"], b["rows"]
    ka, kb = set(A), set(B)
    common = ka & kb
    return {
        "A": A, "B": B, "common": common, "only_old": ka - kb,
        "only_new": kb - ka,
        "moved": [k for k in common if A[k]["hash"] != B[k]["hash"]],
        "same": [k for k in common if A[k]["hash"] == B[k]["hash"]],
        "vcount_changed": [k for k in common if A[k]["verts"] != B[k]["verts"]],
    }


def report(a, b, d):
    A, B, common = d["A"], d["B"], d["common"]
    print("objects  old %d  new %d  common %d  only-old %d  only-new %d"
          % (len(A), len(B), len(common), len(d["only_old"]),
             len(d["only_new"])))
    print("total verts  old %d  new %d" % (a["total_verts"], b["total_verts"]))
    if not common:
        return
    moved, same = d["moved"], d["same"]
    print("common objects whose vertex set MOVED: %d of %d (%.2f %%)"
          % (len(moved), len(common), 100.0 * len(moved) / len(common)))
    print("common objects BIT-IDENTICAL:          %d" % len(same))
    print("common objects with a different vertex COUNT: %d"
          % len(d["vcount_changed"]))
    if same[:10]:
        print("  identical, first 10:", same[:10])
    if moved[:10]:
        print("  MOVED, first 10:", sorted(moved)[:10])
    dd = []
    for k in moved:
        for i in range(3):
            dd.append(abs(A[k]["bbox_min"][i] - B[k]["bbox_min"][i]))
            dd.append(abs(A[k]["bbox_max"][i] - B[k]["bbox_max"][i]))
    if dd:
        dd.sort()
        print("bbox corner shift over moved objects: max %.4f m  p50 %.6f m  "
              "p95 %.4f m  (0 means the shape changed inside a fixed envelope)"
              % (dd[-1], dd[len(dd) // 2], dd[int(0.95 * len(dd))]))


def judge(d, expect_moved, expect_any_move):
    """Return (exit_code, verdict_string, [reasons])."""
    if not d["common"]:
        return (3, "FP_DIFF_VACUOUS",
                ["NO OBJECT NAMES IN COMMON -- the two scenes cannot be "
                 "compared object-by-object, so this run measured nothing "
                 "about whether geometry moved. That is a REFUSAL, not a pass."])
    n = len(d["moved"])
    if expect_moved is not None:
        if n != expect_moved:
            return (1, "FP_DIFF_FAIL_UNEXPECTED",
                    ["%d common object(s) moved; %d were declared. %s"
                     % (n, expect_moved,
                        "A module other than the one under test changed "
                        "underneath this comparison, and it has to be chased "
                        "before anything else in this report is believed."
                        if n > expect_moved else
                        "The change under test did not reach the geometry it "
                        "was supposed to reach -- which is the same defect as "
                        "a null produced by code that never ran.")])
        return (0, "FP_DIFF_OK_AS_DECLARED", [])
    if expect_any_move:
        if n == 0:
            return (1, "FP_DIFF_FAIL_NOTHING_MOVED",
                    ["not one of %d common objects moved. A rebuild that was "
                     "meant to change geometry and changed none is "
                     "indistinguishable from a rebuild that never ran."
                     % len(d["common"])])
        return (0, "FP_DIFF_OK_AS_DECLARED", [])
    return (3, "FP_DIFF_VACUOUS_NOTHING_TESTED",
            ["no expectation was declared, so this run ASSERTS NOTHING -- it is a printout, not a check. Pass --expect-moved N or --expect-any-move. Exiting 3 (VACUOUS) rather than 0, because a bare run being scored as a pass is the defect this file was repaired for."])


def selftest():
    """Both directions, on synthetic fingerprints. A check nobody has watched
    fail has not been shown to work."""
    def fp(rows):
        return {"rows": rows,
                "total_verts": sum(r["verts"] for r in rows.values())}

    base = {"OB_a": {"hash": "h1", "verts": 8,
                     "bbox_min": [0, 0, 0], "bbox_max": [1, 1, 1]},
            "OB_b": {"hash": "h2", "verts": 8,
                     "bbox_min": [0, 0, 0], "bbox_max": [1, 1, 1]}}
    moved1 = {"OB_a": dict(base["OB_a"], hash="hX", bbox_max=[4, 1, 1]),
              "OB_b": base["OB_b"]}
    disjoint = {"OB_z": base["OB_a"]}

    cases = [
        # label,              A,       B,         expect_moved, any, want_rc
        ("identical, expect 0 moved   (must PASS)", base, base, 0, False, 0),
        ("one moved,  expect 0 moved   (must FAIL)", base, moved1, 0, False, 1),
        ("one moved,  expect 1 moved   (must PASS)", base, moved1, 1, False, 0),
        ("identical, expect ANY move   (must FAIL)", base, base, None, True, 1),
        ("one moved,  expect ANY move   (must PASS)", base, moved1, None, True, 0),
        ("no names in common           (must REFUSE=3)", base, disjoint,
         0, False, 3),
        ("no expectation declared      (must REFUSE=3, asserts nothing)",
         base, base, None, False, 3),
    ]
    bad = []
    for label, A, B, em, any_, want in cases:
        d = diff(fp(A), fp(B))
        rc, verdict, _why = judge(d, em, any_)
        ok = rc == want
        print("  %-58s want rc=%d got rc=%d %-22s %s"
              % (label, want, rc, verdict, "ok" if ok else "*** WRONG ***"))
        if not ok:
            bad.append(label)
    print(">> STAGE RESULT: %s" % ("FP_DIFF_SELFTEST_OK" if not bad
                                   else "FP_DIFF_SELFTEST_FAIL"))
    return 0 if not bad else 1


def main(argv):
    if "--selftest" in argv:
        return selftest()
    expect_moved = None
    if "--expect-moved" in argv:
        expect_moved = int(argv[argv.index("--expect-moved") + 1])
    expect_any = "--expect-any-move" in argv
    pos = [x for x in argv if not x.startswith("--")
           and not (expect_moved is not None
                    and x == argv[argv.index("--expect-moved") + 1])]
    if len(pos) < 2:
        print("usage: fp_diff.py OLD.json NEW.json "
              "[--expect-moved N | --expect-any-move]")
        print(">> STAGE RESULT: FP_DIFF_CRASH")
        return 2
    a, b = load(pos[0]), load(pos[1])
    d = diff(a, b)
    report(a, b, d)
    rc, verdict, why = judge(d, expect_moved, expect_any)
    for w in why:
        print("   %s %s" % ("FAIL" if rc == 1 else "NOTE", w))
    print(">> STAGE RESULT: %s" % verdict)
    return rc


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except SystemExit:
        raise
    except Exception:                                            # noqa: BLE001
        import traceback
        traceback.print_exc()
        print(">> STAGE RESULT: FP_DIFF_CRASH")
        sys.exit(2)
