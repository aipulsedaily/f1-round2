#!/usr/bin/env python3
"""DOES THE SHIPPED BEAT SHEET COME BACK OUT OF THE TREE THAT CLAIMS TO MAKE IT?

    .venv/bin/python tools/sheet_reproduces.py [--sheet docs/beat_sheet.json]

WHY THIS EXISTS
------------------------------------------------------------------------
`docs/beat_sheet.json` is 100 % derived output.  This project has now shipped
the same failure three times -- R2-1007, R2-1091, and the film18 world-staleness
incident -- where a derived artefact and the generator that is supposed to
produce it drifted apart and nobody noticed for days.

**AND NO EXISTING GATE CAN CATCH IT.**  The aim gate, the framing gate and the
continuity gate all ask "is this camera legal".  Two completely different
cameras can both be legal.  When beat 5's framing feature lived only in an
uncommitted working-tree file, a checkout would have silently reverted the
camera and *every gate would still have passed*, because the old camera passed
them too.  A green gate is not protection against this class of defect; only
reproduction is.

THERE ARE TWO DISTINCT FAILURES AND THEY NEED DIFFERENT ANSWERS
------------------------------------------------------------------------
  DIVERGED     the sheet does not come back out of the WORKING TREE.
               Somebody hand-edited the sheet, or an input moved under it.
               The sheet is lying about its own provenance.

  UNCOMMITTED  the sheet DOES come back out of the working tree, but the
               working tree is dirty in the generator chain -- so a fresh
               clone, a git worktree, or any `git checkout tools/` produces a
               DIFFERENT sheet with no error at all.  The artefact is correct
               and unreproducible-by-anyone-else, which is the exact shape of
               the three incidents above.

The second is the quiet one, and it is the one that keeps happening.  It is
reported as a FAILURE here, not as a note, because "correct on one machine" is
how a camera gets reverted by somebody else's routine checkout.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Everything the sheet is derived FROM.  If any of these is dirty, the sheet on
# disk is a function of uncommitted state.
CHAIN = [
    "tools/build_beatsheet.py",
    "tools/author_beats2_5.py",
    "anim/filmtime.py",
    "anim/carpath.py",
    "docs/circuit_spec.json",
    "docs/explode_plan.json",
    "docs/presentation_normals.json",
    "world/beat1_anim_anim.json",
    "telemetry/telemetry.csv",
]


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def git(*args):
    return subprocess.run(["git"] + list(args), cwd=R2,
                          capture_output=True, text=True).stdout.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sheet", default=os.path.join(R2, "docs/beat_sheet.json"))
    ap.add_argument("--python", default=os.path.join(R2, ".venv/bin/python"))
    a = ap.parse_args()

    shipped = os.path.abspath(a.sheet)
    print(f">> sheet under test  {os.path.relpath(shipped, R2)}")
    print(f">> sha256            {sha(shipped)}")

    # ---- 1. is the generator chain committed? ---------------------------
    dirty = []
    for p in CHAIN:
        full = os.path.join(R2, p)
        if not os.path.exists(full):
            continue
        if git("status", "--porcelain", "--", p):
            dirty.append(p)

    print(">> GENERATOR CHAIN")
    for p in CHAIN:
        if not os.path.exists(os.path.join(R2, p)):
            print(f"     {'MISSING':<11} {p}")
            continue
        print(f"     {'DIRTY' if p in dirty else 'committed':<11} {p}")

    # ---- 2. does the sheet come back out of the working tree? -----------
    with tempfile.TemporaryDirectory() as td:
        cand = os.path.join(td, "regen.json")
        env = dict(os.environ, B1_SHEET_OUT=cand)
        r1 = subprocess.run([a.python, os.path.join(R2, "tools/build_beatsheet.py")],
                            cwd=R2, env=env, capture_output=True, text=True)
        if not os.path.exists(cand):
            print(">> build_beatsheet.py did not write a sheet:")
            print("\n".join(r1.stdout.splitlines()[-8:]))
            print(">> STAGE RESULT: SHEET_REPRODUCTION_FAILED")
            return 1
        r2 = subprocess.run([a.python, os.path.join(R2, "tools/author_beats2_5.py"),
                             "--sheet", cand],
                            cwd=R2, capture_output=True, text=True)
        if r2.returncode != 0:
            print(">> author_beats2_5.py failed:")
            print("\n".join(r2.stdout.splitlines()[-8:]))
            print(">> STAGE RESULT: SHEET_REPRODUCTION_FAILED")
            return 1

        want = json.load(open(shipped))
        got = json.load(open(cand))

    same = want == got
    print(f">> REPRODUCTION FROM THE WORKING TREE: "
          f"{'IDENTICAL' if same else 'DIFFERENT'}")
    if not same:
        keys = sorted(set(want) | set(got))
        for k in keys:
            if want.get(k) != got.get(k):
                print(f"     block differs: {k}")

    # ---- 3. verdict ------------------------------------------------------
    if not same:
        print(">> The sheet on disk is NOT what this tree produces. Either it was "
              "edited by hand or an input moved under it. Find out which before "
              "trusting any gate that has been run against it -- a gate proves "
              "the camera is legal, never that it is the intended one.")
        print(">> STAGE RESULT: SHEET_DIVERGED")
        return 1

    if dirty:
        print(">> The sheet reproduces HERE and only here. These files are dirty, "
              "so a fresh clone, a git worktree, or any `git checkout` of them "
              "regenerates a DIFFERENT sheet WITH NO ERROR:")
        for p in dirty:
            print(f"     {p}")
        print(">> Every gate would still pass on that different sheet, because "
              "the gates cannot tell two legal cameras apart. Commit the chain "
              "and the sheet together, or the artefact is correct on exactly one "
              "machine.")
        print(">> STAGE RESULT: SHEET_UNCOMMITTED_GENERATOR")
        return 1

    print(">> The sheet reproduces from a clean tree: anyone who checks this "
          "commit out gets this camera.")
    print(">> STAGE RESULT: SHEET_REPRODUCES")
    return 0


if __name__ == "__main__":
    sys.exit(main())
