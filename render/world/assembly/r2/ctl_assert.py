#!/usr/bin/env python3
"""ASSERT THAT A CONTROL MEASURED SOMETHING. Pure python3, no Blender.

    python3 ctl_assert.py --json FILE --require <check> [<check> ...]

WHY THIS EXISTS
===============
`expect pass` in lib_battery.sh checks one thing: the gate exited 0. That is
enough for a control whose only job is "do not invent a violation". It is NOT
enough for a control whose job is to catch OVER-rejection, because the two
ways of exiting 0 are not the same news:

    tested 1 objects; 0 rejected on bounding box; 1 measured per-vertex   PASS
    tested 1 objects; 1 rejected on bounding box; 0 measured per-vertex   PASS

The first is a gate that looked at the geometry and found it clean. The second
is a gate that never looked. `ctl_place_neg.blend` -- the obstacle 3 km off the
circuit -- is the second kind, and if `ctl_place_nearmiss_neg.blend` ever drifts
out to where it is bbox-rejected too, it becomes the second kind as well, and
the battery would go on printing a cheerful pass for a control that had stopped
being one. That is R2-072's failure exactly: the control expires silently, into
a pass, and the stronger the surrounding fix the deader it is.

So the near-miss control declares the QUANTITY it must have produced, not just
its exit code.

CHECKS
------
    measured-per-vertex      >=1 subject mesh reached the per-vertex path, i.e.
                             at least one keep-out volume reports a real
                             `closest_approach_m[*].clearance_m` rather than the
                             "nothing came near it" note.
    clean                    `total` violations == 0.
    clearance-between LO HI  the SMALLEST measured clearance over all volumes
                             lies in [LO, HI] metres. A near-miss control that
                             wanders far from the edge stops testing the edge.

EXIT CODES, matching tools/gate_exit.py so `expect` can read them:
    0 every check held   1 a check failed   2 the file could not be read
"""
import argparse
import json
import os
import sys


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--json", required=True)
    p.add_argument("--label", default=None)
    p.add_argument("--require", nargs="+", required=True)
    a = p.parse_args()

    label = a.label or os.path.basename(a.json)
    try:
        with open(a.json) as f:
            doc = json.load(f)
    except Exception as exc:                                     # noqa: BLE001
        print("!! ctl_assert: cannot read %s: %s" % (a.json, exc))
        print(">> STAGE RESULT: CTL_ASSERT_CRASH")
        return 2

    ca = doc.get("closest_approach_m") or {}
    measured = {k: v.get("clearance_m") for k, v in ca.items()
                if isinstance(v, dict) and v.get("clearance_m") is not None}
    bad = []

    print(">> ctl_assert %s" % label)
    print("   volumes in report        %d" % len(ca))
    print("   volumes actually MEASURED %d  %s"
          % (len(measured), ", ".join("%s %+.3f m" % (k, v)
                                      for k, v in sorted(measured.items()))
             or "(none -- every volume says 'nothing came near it')"))
    print("   violations               %s" % doc.get("total"))

    i = 0
    req = list(a.require)
    while i < len(req):
        chk = req[i]
        if chk == "measured-per-vertex":
            if not measured:
                bad.append("NOTHING was measured per-vertex: every keep-out "
                           "volume reports 'nothing came near it'. This "
                           "control passed WITHOUT the gate looking at its "
                           "geometry, so it cannot detect over-rejection and "
                           "is not the control it claims to be.")
        elif chk == "clean":
            if doc.get("total"):
                bad.append("%s violation(s) reported; this control must be "
                           "clean." % doc.get("total"))
        elif chk == "clearance-between":
            lo, hi = float(req[i + 1]), float(req[i + 2])
            i += 2
            if not measured:
                bad.append("no clearance was measured at all, so it cannot be "
                           "in [%.3f, %.3f] m." % (lo, hi))
            else:
                worst = min(measured.values())
                where = min(measured, key=lambda k: measured[k])
                print("   tightest clearance       %+.4f m on %s "
                      "(must be in [%.3f, %.3f])" % (worst, where, lo, hi))
                if not (lo <= worst <= hi):
                    bad.append(
                        "the tightest measured clearance is %+.4f m on %s, "
                        "outside [%.3f, %.3f]. A near-miss control that is no "
                        "longer near the edge is not testing the edge: too far "
                        "out and the gate stops measuring it per-vertex, too "
                        "far in and it is a positive control wearing a "
                        "negative control's name." % (worst, where, lo, hi))
        else:
            bad.append("unknown check %r" % chk)
        i += 1

    for b in bad:
        print("   FAIL " + b)
    print(">> STAGE RESULT: %s" % ("CTL_ASSERT_OK" if not bad
                                   else "CTL_ASSERT_FAIL"))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
