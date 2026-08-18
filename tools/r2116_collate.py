#!/usr/bin/env python3
"""R2-116 -- collate the re-gate run into one table.

    python3 tools/r2116_collate.py

Reads only artefacts that `tools/r2116_regate_stale_items.sh` actually wrote,
and reports a row as INCOMPLETE when a stage's output file is missing rather
than inferring the stage's verdict from the ones around it. Every column is a
line lifted out of a stored log; nothing here recomputes a verdict.
"""
import os
import re
import sys

ROOT = os.path.expanduser("~/f1-round2")
W = os.path.join(ROOT, "work", "r2116")

ORDER = ["spectator_seated", "driver_figure", "tyre_blanket",
         "crew_fireproof_overall", "armco_post", "paddock_personnel_figure",
         "crew_figure", "team_truck_trailer", "kerb_precast_unit",
         "armco_w_beam", "pit_wall_unit", "terrain_ground",
         "marshal_post_column", "showroom_facade_panel", "gravel_bed_surface",
         "marshal_post_deck"]

# The five modules `item_build_cmd --census` marks STATIC ONLY: a hand-rolled
# parser cannot be probed by handing it an unknown flag, so their save flag is
# a reading of their source and not a live parser's answer.
STATIC_ONLY = {"crew_fireproof_overall", "gantry_truss", "marshal_post_column",
               "pont_deck_slab", "pont_girder"}


def audit_verdict(path):
    if not os.path.exists(path):
        return "-"
    t = open(path).read()
    if re.search(r"^PASS", t, re.M):
        note = " (NOTE)" if "NOTE" in t else ""
        return "PASS" + note
    if re.search(r"^FAIL", t, re.M):
        return "FAIL"
    return "?"


def fpdiff(path):
    if not os.path.exists(path):
        return None
    t = open(path).read()
    m = re.search(r"MOVED: (\d+) of (\d+) \(([\d.]+) %\)", t)
    ident = re.search(r"BIT-IDENTICAL:\s+(\d+)", t)
    verdict = re.search(r"STAGE RESULT: (\S+)", t)
    return {"moved": int(m.group(1)) if m else None,
            "total": int(m.group(2)) if m else None,
            "pct": m.group(3) if m else None,
            "identical": int(ident.group(1)) if ident else None,
            "verdict": verdict.group(1) if verdict else None,
            "bbox": (re.search(r"bbox corner shift[^\n]*", t).group(0)
                     if "bbox corner shift" in t else "")}


def main():
    print("%-26s %-6s %-9s %-9s %-28s %s" %
          ("module", "static", "socket_B", "socket_A", "geometry vs stale blend",
           "determinism"))
    print("-" * 118)
    n_ident = n_moved = n_incomplete = 0
    for m in ORDER:
        b = audit_verdict(os.path.join(W, "before_%s.txt" % m))
        a = audit_verdict(os.path.join(W, "after_%s.txt" % m))
        fd = fpdiff(os.path.join(W, "logs", "%s_fpdiff.log" % m))
        det = fpdiff(os.path.join(W, "logs", "%s_determinism.log" % m))
        so = "yes" if m in STATIC_ONLY else "-"
        if fd is None:
            print("%-26s %-6s %-9s %-9s %-28s %s" %
                  (m, so, b, a, "INCOMPLETE -- not run yet", ""))
            n_incomplete += 1
            continue
        if fd["moved"] == 0:
            g = "identical: %d/%d objects" % (fd["identical"], fd["total"])
            d = "entailed by bit-identity"
            n_ident += 1
        else:
            g = "MOVED %d of %d (%s %%)" % (fd["moved"], fd["total"], fd["pct"])
            n_moved += 1
            if det is None:
                d = "NOT MEASURED -- arm did not run"
            elif det["moved"] == 0:
                d = "deterministic (%d/%d identical)" % (det["identical"],
                                                         det["total"])
            else:
                d = ("NONDETERMINISTIC -- %d/%d moved build-to-build; the "
                     "left column is NOT MEASURED"
                     % (det["moved"], det["total"]))
        print("%-26s %-6s %-9s %-9s %-28s %s" % (m, so, b, a, g, d))
    print("-" * 118)
    print("rebuilt identical %d   geometry moved %d   not yet run %d"
          % (n_ident, n_moved, n_incomplete))
    for m in ORDER:
        fd = fpdiff(os.path.join(W, "logs", "%s_fpdiff.log" % m))
        if fd and fd["moved"]:
            print("\n%s: %s" % (m, fd["bbox"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
