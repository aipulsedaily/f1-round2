"""R2-512.  IS THE BREACH ACTUALLY IN THIS FILM SCENE?

    python3 tools/breach_gate.py --blend render/film16_breach.blend \
        [--control render/film14_breach_r6.blend] [--json out.json]

WHY THIS EXISTS
---------------
`film16.blend` reached the ladder queue with **no breach in it at all**.  Not
degraded -- absent.  `sim/apply_breach.py` had simply never been run on it,
because `tools/build_film_scene.py` and `sim/land_breach.sh` are separate stages
and NOTHING asserted the second one had happened.  The car would have driven
through an unbroken glass wall, with round 1's undeformed aluminium grid still
standing across it, for 22 chunks of a 21-hour pass.

That is the same family as R2-502 one level up: a stage that can be skipped
without anything saying so.  R2-502 was a build that printed success having
written no file; this is a PIPELINE that produced a plausible film with a whole
stage missing.

THE TEST IS COMPLEMENTARY, AND THAT IS THE POINT
------------------------------------------------
Checking for one created object is weak: a name can be absent because the
applier did not run, because it was renamed, or because a grep over a compressed
blend missed it.  So this asserts BOTH directions of the same event:

    CREATED   objects `apply_breach` brings into being      MUST BE PRESENT
    DELETED   round-1 members `apply_breach` removes        MUST BE ABSENT
    CONTROL   an object neither touches (the ONER camera)   MUST BE PRESENT

A blend that never saw the applier fails on BOTH arms at once -- its created
objects are missing AND its deleted objects are still there -- which no naming
change or read error can imitate.  The control being non-zero on the same file
is what makes a zero on the other arms mean something: without it, "0 shards"
and "the reader is broken" are indistinguishable, which is the failure mode this
project keeps rediscovering.

    GW_Right_Mull_04 / GW_Right_Transom_0 are round 1's mullion and transom.
    `apply_breach` DELETES them and rebuilds them as BF_* pieces the bake moves.
    Their presence is positive evidence the wall is still intact.

Read from the SAVED BLEND, never from a build log.
"""
import argparse
import json
import os
import sys

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: objects `sim/apply_breach.py` CREATES.  (kind, name-or-prefix, is_prefix)
CREATED = [("collection", "BREACH_Shards", False),
           ("object", "GP_b04", False),
           ("object", "GS_b04_", True),
           ("object", "BF_MUL05_S02", False)]

#: round-1 members `sim/apply_breach.py` DELETES when it rebuilds the east frame
DELETED = [("object", "GW_Right_Mull_04", False),
           ("object", "GW_Right_Transom_0", False)]

#: touched by neither arm -- proves the reader works on THIS file
CONTROL = [("object", "ONER", False)]


def census(path):
    """-> {(kind, name): count} read out of the blend with Blender.

    Uses `bpy` rather than `strings` because a compressed blend does not carry
    its names in the clear and a string scan would silently under-count.
    """
    import subprocess
    code = (
        "import bpy, json;"
        "print('BREACHGATE' + json.dumps({"
        "'objects': sorted(o.name for o in bpy.data.objects),"
        "'collections': sorted(c.name for c in bpy.data.collections)}))")
    out = subprocess.run(
        ["/opt/blender-5.2.0-linux-x64/blender", "-b", path,
         "--factory-startup", "--python-expr", code],
        capture_output=True, text=True, timeout=7200).stdout
    for ln in out.splitlines():
        if ln.startswith("BREACHGATE"):
            return json.loads(ln[len("BREACHGATE"):])
    raise SystemExit("REFUSING: no census came back from %s" % path)


def count(names, spec):
    kind, nm, is_pref = spec
    pool = names["collections"] if kind == "collection" else names["objects"]
    return sum(1 for n in pool if (n.startswith(nm) if is_pref else n == nm))


def judge(path, names):
    rows, ok = [], True
    for spec in CONTROL:
        c = count(names, spec)
        rows.append(("CONTROL", spec[1], c, "present", c > 0))
        if c == 0:
            ok = False
    if not rows[-1][4]:
        print("   >> the CONTROL is zero: this file could not be read "
              "properly and NO other row here means anything.")
        return rows, False, True
    for spec in CREATED:
        c = count(names, spec)
        good = c > 0
        rows.append(("CREATED", spec[1], c, "present", good))
        ok = ok and good
    for spec in DELETED:
        c = count(names, spec)
        good = c == 0
        rows.append(("DELETED", spec[1], c, "absent", good))
        ok = ok and good
    return rows, ok, False


def report(path, names):
    print(">> %s" % path)
    rows, ok, dead = judge(path, names)
    for arm, nm, c, want, good in rows:
        print("   %-8s %-22s count %-4d want %-8s %s"
              % (arm, nm, c, want, "OK" if good else "FAIL"))
    return ok, dead


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--blend", required=True)
    ap.add_argument("--control", default=None,
                    help="a blend KNOWN to carry the breach; it must PASS, or "
                         "this gate has not been shown to work")
    ap.add_argument("--json", default=None)
    a = ap.parse_args()

    ok, dead = report(a.blend, census(a.blend))
    ctl_ok = None
    if a.control:
        print()
        ctl_ok, _ = report(a.control, census(a.control))
        if not ctl_ok:
            print(">> STAGE RESULT: BREACH_GATE_INVALID -- the positive control "
                  "%s FAILED, so a FAIL on the subject proves nothing"
                  % a.control)
            return 2
    if a.json:
        with open(a.json, "w") as fh:
            json.dump({"blend": a.blend, "pass": ok, "control": a.control,
                       "control_pass": ctl_ok}, fh, indent=1)
    if dead:
        print(">> STAGE RESULT: BREACH_GATE_UNREADABLE")
        return 2
    print(">> STAGE RESULT: %s" % ("BREACH_PRESENT" if ok else "BREACH_ABSENT"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
