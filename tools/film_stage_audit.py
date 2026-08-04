"""R2-513.  WHICH POST-BUILD STAGES REACHED THIS FILM, AND WHICH DID NOT.

    python3 tools/film_stage_audit.py --ship render/film14_breach_r6.blend \
        --subject render/film16_breach.blend [--pre render/film16.blend] \
        [--json work/r2500/stage_audit.json]

WHY A SET DIFFERENCE AND NOT A CHECKLIST
----------------------------------------
`film16` reached the ladder with no breach in it (R2-512) because the chain that
calls itself complete -- `v124/build_film14.sh`, "THE FULL CHAIN, IN ORDER, and
none of it skipped" -- is three steps and does not name `sim/land_breach.sh`.

The obvious response is to write down the appliers. That fixes THIS miss and
goes stale the next time somebody adds one, which is the same failure one
generation later. A checklist of stages is a second copy of a fact, and this
project has a rule about those.

So this asks the question the checklist was standing in for: **is there any
family of objects in the SHIP that is missing from the SUBJECT?** A missed
applier necessarily shows up that way, whether or not anyone remembered it
exists, and so does a half-run one. Nothing has to be enumerated in advance.

Objects are grouped by NAME PREFIX up to the first underscore, because that is
how every generator on this project names its output (`BF_`, `GS_`, `GP_`,
`SPECX_`, `CFP_`, `DRV_`, `ARCH_`, `BR_`, `TER_`, `DR_`). A whole prefix
appearing or vanishing is a stage; a handful of objects moving within one is
not.

THE ASYMMETRY IS DELIBERATE
---------------------------
Families in SHIP-but-not-SUBJECT are reported as **MISSING** and fail the audit:
the ship had them, so a scene that means to replace it should too.

Families in SUBJECT-but-not-SHIP are reported as **NEW** and do NOT fail: this
rebuild deliberately adds four item families and a driver, and an audit that
called those regressions would be useless on exactly the build it was written
for. They are printed, because an unexpected new family is worth a human's
attention even when it is not an error.

CONTROLS.  `--pre` takes the same film BEFORE the applier ran. It must show the
breach families MISSING; if it does not, this instrument cannot see the defect
it was written for and its verdict on the subject is worthless.
"""
import argparse
import json
import os
import subprocess
import sys

BL = "/opt/blender-5.2.0-linux-x64/blender"
#: families that exist for reasons other than a build stage, or that legitimately
#: differ between two scenes without a stage having been skipped
IGNORE = {"Viewer", "Render"}


def census(path):
    code = ("import bpy, json;"
            "print('FSA' + json.dumps({"
            "'objects': sorted(o.name for o in bpy.data.objects),"
            "'collections': sorted(c.name for c in bpy.data.collections)}))")
    r = subprocess.run([BL, "-b", path, "--factory-startup", "--python-expr",
                        code], capture_output=True, text=True, timeout=10800)
    for ln in r.stdout.splitlines():
        if ln.startswith("FSA"):
            return json.loads(ln[3:])
    raise SystemExit("REFUSING: no census from %s\n%s" % (path, r.stdout[-800:]))


def families(names):
    out = {}
    for n in names["objects"]:
        p = n.split("_")[0]
        if p in IGNORE:
            continue
        out[p] = out.get(p, 0) + 1
    return out


def compare(ship, subj, label):
    s, u = families(ship), families(subj)
    missing = {k: s[k] for k in sorted(s) if k not in u}
    shrunk = {k: (s[k], u[k]) for k in sorted(s)
              if k in u and u[k] < s[k] * 0.5}
    new = {k: u[k] for k in sorted(u) if k not in s}
    print("   %-26s ship %d families / %d objects   subject %d / %d"
          % (label, len(s), sum(s.values()), len(u), sum(u.values())))
    for k, v in missing.items():
        print("     MISSING  %-22s ship has %-6d subject has 0" % (k, v))
    for k, (a, b) in shrunk.items():
        print("     SHRUNK   %-22s ship has %-6d subject has %d" % (k, a, b))
    for k, v in new.items():
        print("     NEW      %-22s subject has %-6d (not a failure)" % (k, v))
    if not missing and not shrunk:
        print("     no family in the ship is missing or halved in the subject")
    return {"missing": missing, "shrunk": shrunk, "new": new}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ship", required=True)
    ap.add_argument("--subject", required=True)
    ap.add_argument("--pre", default=None)
    ap.add_argument("--json", default=None)
    a = ap.parse_args()

    print(">> SHIP    %s" % a.ship)
    print(">> SUBJECT %s" % a.subject)
    ship = census(a.ship)
    subj = census(a.subject)
    print(">> SUBJECT vs SHIP")
    res = compare(ship, subj, "subject")

    ctl = None
    if a.pre:
        print(">> CONTROL: the same film BEFORE the applier (%s)"
              % os.path.basename(a.pre))
        pre = census(a.pre)
        ctl = compare(ship, pre, "pre-applier")
        if not ctl["missing"] and not ctl["shrunk"]:
            print(">> STAGE RESULT: STAGE_AUDIT_INVALID -- the pre-applier "
                  "control shows nothing missing, so this instrument cannot "
                  "see a skipped stage and its verdict above means nothing")
            return 2

    if a.json:
        os.makedirs(os.path.dirname(a.json), exist_ok=True)
        with open(a.json, "w") as fh:
            json.dump({"ship": a.ship, "subject": a.subject,
                       "result": res, "control": ctl}, fh, indent=1)
    ok = not res["missing"] and not res["shrunk"]
    print(">> STAGE RESULT: %s"
          % ("ALL_SHIP_STAGES_PRESENT" if ok else "STAGE_MISSING_FROM_SUBJECT"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
