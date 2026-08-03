#!/usr/bin/env python3
"""THE BUILD COMMAND FOR AN ITEM MODULE, DERIVED FROM THAT MODULE'S OWN CLI.

    python3 tools/item_build_cmd.py --item pont_deck_slab
    python3 tools/item_build_cmd.py --census
    python3 tools/item_build_cmd.py --stale-census
    python3 tools/item_build_cmd.py --selftest          # both directions, live

WHY THIS EXISTS — A HARNESS FLAG MISMATCH THAT MANUFACTURED A NULL RESULT
========================================================================
The item modules do not share a CLI. MEASURED over all 41 `world/items/*.py` by
this file's own `--census` on 2026-08-03:

    save flag   --out 21    --save 18    neither 2
    build verb  --test 22   --test-scene 5   --test-blend 4   none 10
    parser      argparse 35   hand-rolled 5   none 1

There is no shared `cli()` — `itemkit.cli()` exists and NOT ONE module calls it.

Handed the wrong save flag, a module built on a hand-rolled `opt()` parser does
not complain. It builds the whole test scene, prints its full report, THROWS THE
RESULT AWAY and exits 0. `work/r2038/run_module.sh` passed `--save` to all
fourteen modules in its campaign; five of them -- crew_fireproof_overall,
gantry_truss, marshal_post_column, pont_deck_slab, pont_girder -- take `--out`.
On pont_deck_slab the gate then measured the blend built on 29 July, rendered it
against itself, and returned:

    mean |diff| 7.69e-06 against a 7.70e-06 noise floor
    0.00 % of pixels moved, high-pass correlation 0.99994

A flawless, entirely convincing null. The real answer was **57.50 %**.

A null that means "the code never ran" is indistinguishable from a null that
means "the change had no effect", and this project has been fooled by that shape
at least twice. `work/r2038/run_module3.sh` fixed it inside one campaign script.
This file is that fix taken out of the campaign, because the mismatch is not
r2038's: **`world/items/REFERENCE.md` documented `--test --save <path>` as THE
build command every item agent follows, and it is the wrong SAVE FLAG on 23 of
41 modules and the wrong VERB on 3 more.** Fixed there too, on 2026-08-03.

REPRODUCED ON LIVE SOURCE, 2026-08-03 — both directions, same module, same box:

    crew_fireproof_overall --test --n 1 --save A.blend   exit 0, 188,062 tris
                                                         built and reported,
                                                         A.blend NOT WRITTEN
    crew_fireproof_overall --test --n 1 --out  B.blend   exit 0, same build,
                                                         B.blend = 18,367,428 B

The two runs differ by one line of stdout. Nothing else in either log says which
one wrote a file.

WHAT THIS TOOL GUARANTEES, AND WHAT IT DOES NOT
===============================================
`--item X` prints the command. `--build X --out P` RUNS it and then REQUIRES the
artefact to have moved: a build that leaves the target file's sha256 unchanged
exits non-zero and says so, because reading the flag correctly is still only a
belief until the file on disk has changed.

The flag detection has two arms, for the reason R2-073 gives -- a census that
reads source and never runs it manufactures defects at the same rate it finds
them:

  STATIC   parse the module's source for the option strings it registers, both
           `argparse.add_argument("--x")` and the hand-rolled `"--x" in a` /
           `a.index("--x")` idiom.
  RUNTIME  for every module whose parser is argparse, run it with an unknown
           flag and read the OPTION TABLE argparse prints in its own usage
           line. That is the live parser answering, not a reading of it, and it
           costs nothing because argparse refuses before any geometry is built.

Modules with a hand-rolled parser cannot be probed that cheaply -- their argv
handling only runs after a full build -- so their answer is STATIC ONLY and this
tool says so per module rather than pretending otherwise. `--selftest` closes
that gap on a sample by building for real, in both directions, and comparing the
artefact.

EXIT CODES (tools/gate_exit.py's scheme, so a battery can read them)
    0 fine   1 a mismatch / a build that did not land   2 could not run
"""

import argparse
import ast
import hashlib
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ITEMS = os.path.join(ROOT, "world", "items")
BLENDER = "/opt/blender-5.2.0-linux-x64/blender"

#: The build verbs seen in the corpus, most specific first — `--test` is a
#: prefix of nothing but it is the fallback, so it is tried last.
VERBS = ("--test-scene", "--test-blend", "--test")
SAVE_FLAGS = ("--save", "--out")


# ---------------------------------------------------------------------------
#  STATIC ARM
# ---------------------------------------------------------------------------
def _argparse_options(tree):
    """Option strings registered through `add_argument`."""
    out = set()
    for n in ast.walk(tree):
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr == "add_argument"):
            for arg in n.args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str) \
                        and arg.value.startswith("-"):
                    out.add(arg.value)
    return out


def _handrolled_options(src):
    """The `"--x" in a` / `a.index("--x")` idiom, which argparse never sees."""
    out = set()
    for m in re.finditer(r'["\'](--[a-zA-Z0-9][a-zA-Z0-9-]*)["\']\s*(?:in\s+a\b'
                         r'|in\s+argv\b)', src):
        out.add(m.group(1))
    for m in re.finditer(r'\.index\(\s*["\'](--[a-zA-Z0-9][a-zA-Z0-9-]*)["\']',
                         src):
        out.add(m.group(1))
    return out


def scan(path):
    src = open(path, encoding="utf-8", errors="replace").read()
    try:
        tree = ast.parse(src)
        ap = _argparse_options(tree)
    except SyntaxError:
        ap = set()
    hand = _handrolled_options(src)
    opts = ap | hand
    return {"module": os.path.splitext(os.path.basename(path))[0],
            "path": path,
            "parser": "argparse" if ap else ("hand-rolled" if hand else "none"),
            "options": opts,
            "verb": next((v for v in VERBS if v in opts), None),
            "save": next((f for f in SAVE_FLAGS if f in opts), None)}


# ---------------------------------------------------------------------------
#  RUNTIME ARM — ask the live parser, for free, for the argparse modules
# ---------------------------------------------------------------------------
_USAGE_OPT = re.compile(r'(--[a-zA-Z0-9][a-zA-Z0-9-]*)')


def probe_runtime(rec, timeout=180):
    """Run the module with an unknown flag and read argparse's own usage line.

    argparse refuses before the module builds anything, so this is seconds, not
    hours. It is the LIVE option table: no reading of the source is involved.
    """
    if rec["parser"] != "argparse":
        return None            # its argv handling only runs after a full build
    cmd = [BLENDER, "-b", "--factory-startup", "-noaudio", "-P", rec["path"],
           "--", "--itemBuildCmdProbe"]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except (subprocess.TimeoutExpired, OSError):
        return None
    blob = (p.stdout or "") + (p.stderr or "")
    m = re.search(r'usage:.*?(?=\n\S|\Z)', blob, re.S)
    if not m:
        return None
    return set(_USAGE_OPT.findall(m.group(0)))


# ---------------------------------------------------------------------------
def build_command(rec, out_path):
    if rec["save"] is None:
        return None
    cmd = [BLENDER, "-b", "--factory-startup", "-P", rec["path"], "--"]
    if rec["verb"]:
        cmd.append(rec["verb"])
    cmd += [rec["save"], out_path]
    return cmd


def _sha(path):
    if not os.path.exists(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run_build(rec, out_path, extra=(), timeout=10800):
    """Run the build and REQUIRE the artefact to have moved."""
    cmd = build_command(rec, out_path)
    if cmd is None:
        print("   FAIL %s registers neither --save nor --out; there is no way "
              "to ask it for a blend." % rec["module"])
        return 1, None
    cmd += list(extra)
    before = _sha(out_path)
    print("   $ " + " ".join(cmd))
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    after = _sha(out_path)
    print("   blender exit=%d (NOT evidence: Blender 5.2 exits 0 on an "
          "uncaught script exception)" % p.returncode)
    print("   artefact sha256  before %s  after %s"
          % ((before or "ABSENT")[:16], (after or "ABSENT")[:16]))
    if after is None:
        print("   FAIL the build wrote no file at %s. The module accepted the "
              "run, built, reported and exited 0 -- and threw the result away. "
              "This is the manufactured null." % out_path)
        return 1, p
    if before == after:
        print("   FAIL %s is byte-identical to what was there before this "
              "build. Everything downstream would be measuring a file this "
              "run did not produce." % out_path)
        return 1, p
    print("   OK   %s rewritten, %d bytes" % (out_path, os.path.getsize(out_path)))
    return 0, p


# ---------------------------------------------------------------------------
def census(runtime=True):
    recs = [scan(os.path.join(ITEMS, f)) for f in sorted(os.listdir(ITEMS))
            if f.endswith(".py")]
    bad = []
    print("%-32s %-12s %-13s %-8s %s"
          % ("MODULE", "PARSER", "VERB", "SAVE", "RUNTIME AGREES?"))
    n_probed = n_agree = 0
    for r in recs:
        agree = "-- static only (hand-rolled parser)"
        if runtime and r["parser"] == "argparse":
            live = probe_runtime(r)
            if live is None:
                agree = "?? no usage line"
            else:
                n_probed += 1
                ok = ((r["save"] is None or r["save"] in live)
                      and (r["verb"] is None or r["verb"] in live))
                n_agree += 1 if ok else 0
                agree = "yes" if ok else "NO -- live table %s" % sorted(live)
                if not ok:
                    bad.append("%s: static says %s/%s, the live parser says %s"
                               % (r["module"], r["verb"], r["save"],
                                  sorted(live)))
        print("%-32s %-12s %-13s %-8s %s"
              % (r["module"], r["parser"], r["verb"] or "-", r["save"] or "-",
                 agree))
    n_save = sum(1 for r in recs if r["save"] == "--save")
    n_out = sum(1 for r in recs if r["save"] == "--out")
    n_none = sum(1 for r in recs if r["save"] is None)
    print("\n  %d modules: %d take --save, %d take --out, %d take neither"
          % (len(recs), n_save, n_out, n_none))
    print("  world/items/REFERENCE.md documents `--test --save <path>`. That is "
          "the WRONG SAVE FLAG on %d of %d modules" % (n_out, len(recs)))
    print("  and the wrong VERB on %d more."
          % sum(1 for r in recs if r["save"] == "--save"
                and r["verb"] not in (None, "--test")))
    print("  runtime arm: %d of %d argparse modules probed, %d agreed with the "
          "static reading" % (n_probed, sum(1 for r in recs
                                            if r["parser"] == "argparse"),
                              n_agree))
    return recs, bad


# ---------------------------------------------------------------------------
def stale_census():
    """Which `*_test.blend` files are OLDER than the module that built them.

    The wrong build flag is one way to end up measuring a file the run did not
    produce. Simply never rebuilding is the other, and it leaves exactly the
    same signature: a gate that reports confidently on geometry that predates
    the change under test.

    HONEST ABOUT WHAT THIS PROVES. An mtime says the SOURCE moved, not that the
    GEOMETRY did -- a docstring edit trips it. So this reports SUSPECT, and the
    only thing that clears a row is a rebuild (`--build`, which requires the
    artefact's sha256 to change). It is a list of things nobody has any reason
    to believe, not a list of known defects.
    """
    import time
    rows = []
    for f in sorted(os.listdir(ITEMS)):
        if not f.endswith(".py"):
            continue
        mod = f[:-3]
        blend = os.path.join(ITEMS, mod + "_test.blend")
        if not os.path.exists(blend):
            continue
        ps = os.path.getmtime(os.path.join(ITEMS, f))
        bs = os.path.getmtime(blend)
        rows.append((mod, ps, bs))
    stale = [r for r in rows if r[1] > r[2]]
    print("item test blends on disk           %d" % len(rows))
    print("SUSPECT (source newer than blend)  %d" % len(stale))
    for mod, ps, bs in sorted(stale, key=lambda r: r[2] - r[1]):
        print("   %-30s source %s   blend %s   blend is %6.1f h older"
              % (mod, time.strftime("%m-%d %H:%M", time.localtime(ps)),
                 time.strftime("%m-%d %H:%M", time.localtime(bs)),
                 (ps - bs) / 3600.0))
    print(">> STAGE RESULT: %s"
          % ("ITEM_BLENDS_OK_CURRENT" if not stale else "ITEM_BLENDS_SUSPECT"))
    return 0 if not stale else 1


def selftest(module="crew_fireproof_overall", extra=("--n", "1")):
    """BOTH DIRECTIONS, on live source, measured on the artefact.

    The positive control is the documented command. It MUST leave no file --
    if it ever starts writing one, this whole tool is unnecessary and should be
    deleted, and that is a result worth having too.
    """
    import shutil
    import tempfile
    rec = scan(os.path.join(ITEMS, module + ".py"))
    bad = []
    tmp = tempfile.mkdtemp(prefix="item_build_cmd_")
    try:
        print("SELFTEST on %s (parser %s, verb %s, save %s)"
              % (module, rec["parser"], rec["verb"], rec["save"]))

        wrong = "--save" if rec["save"] == "--out" else "--out"
        print("\n[POSITIVE CONTROL] the flag REFERENCE.md documents, %r, which "
              "this module does not take" % wrong)
        pth = os.path.join(tmp, "pos.blend")
        cmd = [BLENDER, "-b", "--factory-startup", "-P", rec["path"], "--"]
        if rec["verb"]:
            cmd.append(rec["verb"])
        cmd += list(extra) + [wrong, pth]
        print("   $ " + " ".join(cmd))
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=10800)
        built = [l for l in (p.stdout or "").splitlines()
                 if "triangles" in l or "tris" in l]
        print("   blender exit=%d, wrote a file: %s"
              % (p.returncode, os.path.exists(pth)))
        for l in built[-1:]:
            print("   it DID build: %s" % l.strip())
        if os.path.exists(pth):
            bad.append("the wrong flag WROTE a file; the mismatch this tool "
                       "exists for does not reproduce and the tool should be "
                       "re-examined")
        elif p.returncode != 0:
            print("   (it also exited non-zero, so this module's mismatch is "
                  "at least loud)")

        print("\n[NEGATIVE CONTROL] the flag derived from the module itself, %r"
              % rec["save"])
        pth2 = os.path.join(tmp, "neg.blend")
        rc, _ = run_build(rec, pth2, extra=extra)
        if rc != 0:
            bad.append("the DERIVED flag did not produce an artefact either; "
                       "the detection is wrong, not just the documentation")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    for b in bad:
        print("\n   FAIL " + b)
    print("\n>> STAGE RESULT: %s" % ("ITEM_BUILD_CMD_OK" if not bad
                                     else "ITEM_BUILD_CMD_FAIL"))
    return 0 if not bad else 1


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--item")
    p.add_argument("--out")
    p.add_argument("--build", action="store_true",
                   help="run the build and require the artefact to move")
    p.add_argument("--census", action="store_true")
    p.add_argument("--stale-census", action="store_true",
                   help="which *_test.blend files predate their own source")
    p.add_argument("--no-runtime", action="store_true",
                   help="census: skip the live-parser arm (faster, weaker)")
    p.add_argument("--selftest", action="store_true")
    p.add_argument("--selftest-item", default="crew_fireproof_overall")
    a = p.parse_args()

    if a.selftest:
        return selftest(a.selftest_item)
    if a.stale_census:
        return stale_census()
    if a.census:
        _recs, bad = census(runtime=not a.no_runtime)
        for b in bad:
            print("   FAIL " + b)
        print(">> STAGE RESULT: %s" % ("ITEM_BUILD_CMD_OK" if not bad
                                       else "ITEM_BUILD_CMD_FAIL"))
        return 0 if not bad else 1
    if not a.item:
        p.error("give --item, --census or --selftest")
    path = os.path.join(ITEMS, a.item + ".py")
    if not os.path.exists(path):
        print("no such module: %s" % path)
        return 2
    rec = scan(path)
    out = a.out or os.path.join(ITEMS, a.item + "_test.blend")
    cmd = build_command(rec, out)
    if cmd is None:
        print("%s registers neither --save nor --out." % a.item)
        return 1
    if a.build:
        rc, _ = run_build(rec, out)
        print(">> STAGE RESULT: %s" % ("ITEM_BUILD_OK_LANDED" if rc == 0
                                       else "ITEM_BUILD_FAIL_DID_NOT_LAND"))
        return rc
    print(" ".join(cmd))
    return 0


if __name__ == "__main__":
    sys.exit(main())
