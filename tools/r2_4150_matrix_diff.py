#!/usr/bin/env python
"""R2-4150 -- DIFF TWO ADJUDICATIONS, GATE BY GATE AND BEAT BY BEAT.

    .venv/bin/python -m tools.r2_4150_matrix_diff OLD.json NEW.json

A pass that changes one beat has to prove it changed only that beat. This
prints every gate's outcome in both runs, every failure line that appeared or
disappeared, and the numbers inside the lines that survive -- so a regression
somewhere else in the film cannot hide behind an improvement at the breach.
"""

import json
import re
import sys


def gates(path):
    d = json.load(open(path))
    return d["adjudication"]["report"]["gates"], d


def lines(g):
    out = {}
    for name, v in g.items():
        for kind in ("failures", "inapplicable"):
            for f in v.get(kind, []):
                beat = f.split(":", 1)[0].strip()
                out.setdefault((name, kind, beat), []).append(f)
    return out


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    go, do = gates(sys.argv[1])
    gn, dn = gates(sys.argv[2])
    print("OLD %s" % do["adjudication"]["wav"])
    print("NEW %s\n" % dn["adjudication"]["wav"])

    print("%-12s %-14s %-14s" % ("gate", "OLD", "NEW"))
    for k in sorted(set(go) | set(gn)):
        a = go.get(k, {}).get("outcome", "-")
        b = gn.get(k, {}).get("outcome", "-")
        flag = "   <-- MOVED" if a != b else ""
        print("%-12s %-14s %-14s%s" % (k, a, b, flag))
    print()

    lo, ln = lines(go), lines(gn)
    print("FAILURE / INAPPLICABLE LINES THAT APPEARED OR DISAPPEARED")
    for k in sorted(set(lo) | set(ln)):
        if k in lo and k not in ln:
            for f in lo[k]:
                print("  GONE  [%s %s] %s" % (k[0], k[1], f))
        elif k in ln and k not in lo:
            for f in ln[k]:
                print("  NEW   [%s %s] %s" % (k[0], k[1], f))
    print()

    num = re.compile(r"-?\d+\.\d+")
    print("LINES PRESENT IN BOTH, WITH THEIR NUMBERS")
    for k in sorted(set(lo) & set(ln)):
        for fa, fb in zip(lo[k], ln[k]):
            na, nb = num.findall(fa), num.findall(fb)
            if na != nb:
                print("  [%s %s %s]" % k)
                print("    OLD %s" % fa)
                print("    NEW %s" % fb)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
