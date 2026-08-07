#!/usr/bin/env python3
"""TWO RUNS THAT DISAGREE, MECHANICALLY ATTRIBUTED.  Defect #97.

    python3 tools/report_repro.py A.json B.json
    python3 tools/report_repro.py --selftest
    python3 tools/report_repro.py --require docs/placement_report.json

WHAT WAS ALREADY DONE, AND WHAT WAS NOT
=======================================
`tools/provenance.py` closed half of #97 and closed it well: every report it
stamps records each input's path, mtime and full sha256, plus the tool's own
hash and -- by default, without anyone having to remember -- `itemkit.py` and
`world_contract.py`, which change an answer without ever appearing in argv.
Its `verify()` then re-measures those inputs and says what has moved.

But `verify()` compares a report to **disk as it is now**.  #97's actual
question is a different one:

    the closest approach moved between run A and run B.  Which of them moved
    it -- the world, an input, the tool, or nothing at all?

`verify()` cannot answer that, because by the time anyone asks, disk is at
some third state and neither A's nor B's inputs are on it any more.  The
question is A-against-B, and nothing in the repository could ask it.

THE FOUR VERDICTS
=================
Given two stamped reports, every declared input, the tool file, the contract
and itemkit are compared BY HASH, and the report bodies are compared with the
stamps stripped out:

    inputs same, results same        REPRODUCED
    inputs moved, results moved      ATTRIBUTED      -- and it names which
    inputs same, results moved       NON_REPRODUCIBLE
    inputs moved, results same       INSENSITIVE

`NON_REPRODUCIBLE` is the alarm this file exists for.  It means either the
tool is not deterministic, or it read something it never declared -- and both
of those make every number downstream of it uncitable.  Nothing else in the
repository can currently distinguish that case from an ordinary regression.

`INSENSITIVE` is the quieter one and is worth as much.  A report whose numbers
do not move when a declared input moves is a report that may not be reading
that input at all: **a metric that reads the same present or absent.**  That is
the single commonest defect shape in this project's log -- a bay list hardcoded
so a bay was never measured, a min clamped at zero reading 791 frames as 0.00,
a control that passed only because it discarded 70 % of its work.  A differ
that could only report ATTRIBUTED would launder exactly that failure as a
success.

UNSTAMPED IS NOT A MISSING FIELD, IT IS AN UNCITEABLE REPORT
============================================================
Every one of the six placement reports on disk today predates stamping:

    docs/placement_report.json          docs/placement_depth.json
    docs/placement_report_r2.json       docs/placement_after_46.json
    docs/placement_report_cam34.json    docs/placement_before_46.json

R2-735 had to settle an argument between three of them by mtime and by
byte-comparing rows, and concluded that the NEWEST file was the STALE one.
That work was only necessary because none of them says what it measured.
`--require` is the consumer-side half: a tool that reads one of these should
refuse rather than quietly compute on it, because an unstamped report cannot be
told apart from a fresh one and the difference has already been wrong once.
"""
import os
import sys
import json
import argparse

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import provenance as P                                            # noqa: E402


# --------------------------------------------------------------------------
def _load(path):
    with open(path, "r", errors="replace") as fh:
        return json.load(fh)


def _input_hashes(stamp):
    """{role: sorted tuple of sha256} over inputs, also_hash and the tool.

    A ROLE IS NOT UNIQUE, and assuming it was cost this file its own P5
    control.  `provenance.stamp()` appends `world_contract` and `itemkit` by
    default and does NOT deduplicate by role -- so a caller that passes
    `also_hash=[("world_contract", <some other copy>)]` produces a stamp with
    TWO entries under that role.  Keying a dict on the role silently kept the
    last one and dropped the other, and the differ then reported
    NON_REPRODUCIBLE for a contract change it had thrown away: an attribution
    tool laundering the very thing it exists to attribute.

    So the value is the multiset of hashes under a role.  Two runs agree on a
    role when they read the same set of bytes under it, however many files
    that was.
    """
    out = {}
    for group, prefix in (("inputs", ""), ("also_hash", "code:")):
        for f in stamp.get(group) or []:
            role = prefix + str(f.get("role"))
            sha = f.get("sha256") if f.get("status") == "OK" else \
                "<%s>" % f.get("status")
            out.setdefault(role, []).append(sha)
    tool = stamp.get("tool") or {}
    out.setdefault("code:tool", []).append(
        tool.get("sha256") or "<%s>" % tool.get("status"))
    return {k: tuple(sorted(v)) for k, v in out.items()}


def _show(shas):
    return ",".join(s[:16] if s else "?" for s in shas)


def _body(report):
    """The report with its stamp removed, canonicalised for comparison.

    Sorted keys and a fixed separator so that two dicts differing only in
    insertion order compare equal: a re-run that emits the same numbers in a
    different order is REPRODUCED, and calling it a regression would train
    everybody to ignore this tool.
    """
    d = {k: v for k, v in report.items() if k != P.STAMP_KEY}
    return json.dumps(d, sort_keys=True, separators=(",", ":"))


def _closest(report):
    """The `closest_approach_m` block, which is the number #97 is named for."""
    c = report.get("closest_approach_m")
    return c if isinstance(c, dict) else None


def compare(path_a, path_b):
    a, b = _load(path_a), _load(path_b)
    res = {"a": os.path.abspath(path_a), "b": os.path.abspath(path_b),
           "moved_inputs": [], "role_mismatch": [], "results_differ": None,
           "closest_approach_delta": [], "verdict": None, "why": None}

    sa, sb = a.get(P.STAMP_KEY), b.get(P.STAMP_KEY)
    unstamped = [p for p, s in ((path_a, sa), (path_b, sb)) if not s]
    if unstamped:
        res["verdict"] = "UNCITEABLE"
        res["why"] = ("no provenance stamp in: %s -- these reports cannot say "
                      "what they measured, so a difference between them cannot "
                      "be attributed to anything. Re-run the tool that writes "
                      "them; it stamps now." % ", ".join(unstamped))
        res["unstamped"] = unstamped
        return res

    ha, hb = _input_hashes(sa), _input_hashes(sb)
    for role in sorted(set(ha) | set(hb)):
        if role not in ha or role not in hb:
            res["role_mismatch"].append(
                {"role": role, "in_a": role in ha, "in_b": role in hb})
        elif ha[role] != hb[role]:
            res["moved_inputs"].append(
                {"role": role, "a": ha[role], "b": hb[role]})

    res["results_differ"] = (_body(a) != _body(b))

    ca, cb = _closest(a), _closest(b)
    if ca and cb:
        for vol in sorted(set(ca) | set(cb)):
            ra, rb = ca.get(vol) or {}, cb.get(vol) or {}
            if ra.get("clearance_m") != rb.get("clearance_m") or \
                    ra.get("object") != rb.get("object"):
                res["closest_approach_delta"].append({
                    "volume": vol,
                    "a": {"object": ra.get("object"),
                          "clearance_m": ra.get("clearance_m")},
                    "b": {"object": rb.get("object"),
                          "clearance_m": rb.get("clearance_m")}})

    moved = bool(res["moved_inputs"] or res["role_mismatch"])
    differ = res["results_differ"]
    if not moved and not differ:
        res["verdict"] = "REPRODUCED"
        res["why"] = "every declared input, the tool, the contract and itemkit " \
                     "hash identically, and the report bodies are identical."
    elif moved and differ:
        res["verdict"] = "ATTRIBUTED"
        res["why"] = "the results moved and so did: %s" % ", ".join(
            [x["role"] for x in res["moved_inputs"]] +
            ["%s (declared in only one run)" % x["role"]
             for x in res["role_mismatch"]])
    elif not moved and differ:
        res["verdict"] = "NON_REPRODUCIBLE"
        res["why"] = ("the results moved and NOTHING declared moved. Either the "
                      "tool is not deterministic, or it read an input it does "
                      "not declare. Every number in both reports is unciteable "
                      "until this is resolved.")
    else:
        res["verdict"] = "INSENSITIVE"
        res["why"] = ("a declared input moved (%s) and not one number in the "
                      "report changed. Confirm the report actually reads it -- "
                      "a metric that reads the same present or absent has been "
                      "the commonest defect on this project."
                      % ", ".join(x["role"] for x in res["moved_inputs"]))
    return res


def require(path, allow_unstamped_reason=None):
    """Consumer-side gate: refuse to compute on a report that cannot say what
    it measured.  Returns the loaded report, or raises SystemExit.

    This is the half `provenance.stamp()` cannot do for itself.  A stamp only
    helps if something REFUSES when it is absent; a stamp nobody checks is a
    header, and the project has already shipped a fix into a file the pipeline
    does not read (R2-1099).
    """
    rep = _load(path)
    if rep.get(P.STAMP_KEY):
        v = P.verify(path)
        print(">> provenance: %s  %s" % (v["status"], path))
        for d in v.get("drift", []):
            print("   DRIFT %-14s measured %s -> now %s"
                  % (d["role"], d["measured_sha256"], d["current_sha256"]))
        return rep
    if allow_unstamped_reason:
        print(">> provenance: UNSTAMPED, ALLOWED -- %s" % allow_unstamped_reason)
        print(">> %s predates provenance stamping. Its numbers are NOT "
              "attributable to any world." % path)
        return rep
    print("REFUSING: %s carries no provenance stamp." % path)
    print("  It cannot say which world, telemetry, camera path or contract it")
    print("  measured, so its numbers cannot be told apart from a stale run.")
    print("  R2-735 spent an entire entry on exactly this, and concluded the")
    print("  NEWEST of three such files was the stale one.")
    print("  Re-run the tool that writes it (it stamps now), or pass")
    print("  --allow-unstamped '<why this is acceptable here>'.")
    print(">> STAGE RESULT: FAIL (1 violations)")
    raise SystemExit(1)


# --------------------------------------------------------------------------
def _print(res, verbose=True):
    if verbose:
        print("A  %s" % res["a"])
        print("B  %s" % res["b"])
        for m in res["moved_inputs"]:
            print("   MOVED   %-22s %s -> %s"
                  % (m["role"], _show(m["a"]), _show(m["b"])))
        for m in res["role_mismatch"]:
            print("   ROLE    %-22s in A=%s in B=%s"
                  % (m["role"], m["in_a"], m["in_b"]))
        for c in res["closest_approach_delta"]:
            print("   CLOSEST %-22s %s %s  ->  %s %s"
                  % (c["volume"], c["a"]["object"], c["a"]["clearance_m"],
                     c["b"]["object"], c["b"]["clearance_m"]))
        print("   %s" % res["verdict"])
        print("   %s" % res["why"])
    return res


EXIT = {"REPRODUCED": 0, "ATTRIBUTED": 0, "INSENSITIVE": 2,
        "NON_REPRODUCIBLE": 3, "UNCITEABLE": 4}


def _main(argv):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("reports", nargs="*", metavar="REPORT.json")
    p.add_argument("--selftest", action="store_true")
    p.add_argument("--require", metavar="REPORT.json", default=None)
    p.add_argument("--allow-unstamped", default=None, metavar="REASON")
    p.add_argument("--json", default=None)
    a = p.parse_args(argv)

    if a.selftest:
        from report_repro_selftest import run                     # noqa: PLC0415
        return run()
    if a.require:
        require(a.require, a.allow_unstamped)
        print(">> STAGE RESULT: OK (0 violations)")
        return 0
    if len(a.reports) != 2:
        p.print_help()
        return 2
    res = _print(compare(a.reports[0], a.reports[1]))
    if a.json:
        with open(a.json, "w") as fh:
            json.dump(res, fh, indent=1)
    print(">> STAGE RESULT: %s (%s)"
          % ("OK" if res["verdict"] in ("REPRODUCED", "ATTRIBUTED") else "FAIL",
             res["verdict"]))
    return EXIT[res["verdict"]]


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
