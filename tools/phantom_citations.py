#!/usr/bin/env python3
"""GREP FOR THE GUARD BEFORE YOU CITE IT. A docstring that names a safeguard
which does not exist is worse than no docstring: it stops the next person
looking.

    python3 tools/phantom_citations.py
    python3 tools/phantom_citations.py --selftest

THE DEFECT THIS ANSWERS
=======================
`itemkit.socket_audit()` was named by two live docstrings and one RuntimeError
message -- the message an engineer reads at the exact moment a socket index has
moved under them -- and **there is no such function**. The audit is inline in
`itemkit.selftest()`. It survived because nobody ever tried to call it: a
citation is not executed, so it never fails, so it never gets fixed. Four more
of the same shape were found in the same sweep on 2026-08-03:

    world/itemkit.py                    itemkit.socket_audit()   phantom
    world/items/crew_fireproof_overall  itemkit socket_audit()   phantom
    tools/item_presence.py              --shutter-mode           phantom flag
    tools/beat2_probe.py                --dump-exposure          phantom flag
    tools/black_row_count.py            --control                phantom flag
                                        (the guard is real; the FLAG NAME is
                                         wrong, so the documented invocation
                                         is an argparse error)

WHAT IT CHECKS, AND WHAT IT CANNOT
==================================
Two citation shapes, both mechanical enough to be checked without guessing:

  MODULE.FUNCTION()   `foo.bar()` in a docstring or comment, where `foo` is the
                      basename of a real project .py file -> `def bar` must
                      exist in it.
  PATH                `tools/x.py`, `world/x.py`, `anim/x.py`, `sim/x.py` in a
                      docstring or comment -> the file must exist.

FLAG citations are deliberately NOT swept automatically. A `--flag` in prose
may belong to any of forty tools, and a checker that guesses which one would
manufacture defects at the same rate it finds them -- R2-073's exact lesson. So
flags are held in an explicit, hand-verified list below, and the sweep's job is
to keep them honest: each entry names the tool it belongs to and the check
asserts that tool really registers it.

EXIT: 0 no phantoms   1 a phantom   2 could not run
"""

import argparse
import ast
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCAN_DIRS = ("tools", "world", "anim", "sim", "audio")
SKIP_DIRS = {"__pycache__", ".git", "items"}   # items/ is swept separately

#: A prose line containing this token is exempt: it is DOCUMENTING a phantom
#: rather than relying on one. Deliberately ugly so it cannot be typed by
#: accident, and it must appear on the same line as the citation.
EXEMPT = "PHANTOM-OK"

#: Cited-but-absent, confirmed real, in files this repair was not allowed to
#: touch (four other agents own them right now). Listed rather than allowlisted
#: silently: they PRINT on every run, as NOTE, so they cannot rot into
#: invisibility. Clear a row by fixing the citation, not by deleting the row.
KNOWN_UNFIXED = {
    ("tools/build_film_scene.py", "world/assembly/r2/assemble.py"):
        "the real path is render/world/assembly/r2/assemble.py; "
        "build_film_scene.py is owned by another agent",
    ("tools/socket_index_audit.py", "world/items/foo.py"):
        "a placeholder in a usage example, not a claim; socket_index_audit.py "
        "is owned by another agent",
}

#: Flag citations that have been read by a human, with the tool that owns them.
#: Add a row when you cite a flag in prose; the checker holds the row to the
#: tool's real argparse.
FLAG_CITATIONS = [
    ("tools/screen_presence.py", "--uniform-shutter"),
    ("tools/black_row_count.py", "--no-control"),
    ("tools/dump_exposure.py", "--out"),
    ("tools/build_verify_scene.py", "--control-break-exposure"),
    ("tools/build_verify_scene.py", "--control-break-view-transform"),
    ("tools/build_beat1_audit.py", "--control-plant-missing-image"),
    ("tools/item_build_cmd.py", "--stale-census"),
]

_CALL = re.compile(r'\b([a-z_][a-z0-9_]*)\.([a-z_][a-z0-9_]*)\(\)')
_PATH = re.compile(r'\b((?:tools|world|anim|sim|audio)/[A-Za-z0-9_./-]+\.py)\b')


def project_modules():
    mods = {}
    for base in SCAN_DIRS:
        for dp, dn, fn in os.walk(os.path.join(ROOT, base)):
            dn[:] = [d for d in dn if d not in SKIP_DIRS]
            for f in fn:
                if f.endswith(".py"):
                    mods.setdefault(f[:-3], os.path.join(dp, f))
    return mods


def defs_in(path):
    try:
        tree = ast.parse(open(path, encoding="utf-8", errors="replace").read())
    except (SyntaxError, OSError):
        return set()
    return {n.name for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef,
                              ast.ClassDef))}


def prose_of(path):
    """Every docstring and every `#` comment, with a line number."""
    out = []
    src = open(path, encoding="utf-8", errors="replace").read()
    for i, line in enumerate(src.splitlines(), 1):
        h = line.find("#")
        if h >= 0 and line[:h].count('"') % 2 == 0 \
                and line[:h].count("'") % 2 == 0:
            out.append((i, line[h:]))
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return out
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef,
                          ast.ClassDef)):
            d = ast.get_docstring(n, clean=False)
            if d:
                base = getattr(n, "lineno", 1)
                for j, line in enumerate(d.splitlines()):
                    out.append((base + j, line))
    return out


def check_source(path, mods, defcache):
    """Phantoms cited by one file. Returns a list of (line, kind, detail)."""
    bad = []
    for ln, text in prose_of(path):
        if EXEMPT in text:
            continue
        for mod, fn in _CALL.findall(text):
            if mod not in mods:
                continue                      # not a project module; not ours
            if mod not in defcache:
                defcache[mod] = defs_in(mods[mod])
            if fn not in defcache[mod]:
                bad.append((ln, "function",
                            "%s.%s() -- `%s` has no `def %s`"
                            % (mod, fn, os.path.relpath(mods[mod], ROOT), fn)))
        for rel in _PATH.findall(text):
            if not os.path.exists(os.path.join(ROOT, rel)):
                bad.append((ln, "path", "%s -- no such file" % rel))
    return bad


def check_flags():
    bad = []
    for rel, flag in FLAG_CITATIONS:
        p = os.path.join(ROOT, rel)
        if not os.path.exists(p):
            bad.append("%s: the file itself does not exist" % rel)
            continue
        src = open(p, encoding="utf-8", errors="replace").read()
        if ('"%s"' % flag) not in src and ("'%s'" % flag) not in src:
            bad.append("%s does not register %s" % (rel, flag))
    return bad


def sweep():
    mods = project_modules()
    defcache = {}
    files = []
    for base in SCAN_DIRS:
        for dp, dn, fn in os.walk(os.path.join(ROOT, base)):
            dn[:] = [d for d in dn if d in ("items",) or d not in SKIP_DIRS]
            dn[:] = [d for d in dn if d != "__pycache__"]
            files += [os.path.join(dp, f) for f in fn if f.endswith(".py")]
    hits, known = [], []
    for p in sorted(files):
        rel = os.path.relpath(p, ROOT)
        if rel == os.path.join("tools", "phantom_citations.py"):
            continue                       # its own examples are the controls
        for ln, kind, detail in check_source(p, mods, defcache):
            cited = detail.split(" -- ")[0]
            if (rel, cited) in KNOWN_UNFIXED:
                known.append((rel, ln, cited, KNOWN_UNFIXED[(rel, cited)]))
            else:
                hits.append((rel, ln, kind, detail))
    print("files swept                 %d" % len(files))
    print("project modules known       %d" % len(mods))
    print("phantom citations found     %d" % len(hits))
    for rel, ln, kind, detail in hits:
        print("   FAIL %s:%d  %s" % (rel, ln, detail))
    print("known, cited-but-absent, owned elsewhere  %d" % len(known))
    for rel, ln, cited, why in known:
        print("   NOTE %s:%d  %s -- %s" % (rel, ln, cited, why))
    fb = check_flags()
    print("flag citations on the list  %d, of which broken %d"
          % (len(FLAG_CITATIONS), len(fb)))
    for b in fb:
        print("   FAIL " + b)
    ok = not hits and not fb
    print(">> STAGE RESULT: %s" % ("PHANTOM_CITATIONS_CLEAN" if ok
                                   else "PHANTOM_CITATIONS_FAIL"))
    return 0 if ok else 1


def selftest():
    """BOTH DIRECTIONS. A checker that has never rejected anything has not been
    shown to work -- and this one has to be shown NOT to reject correct prose,
    because a citation checker that over-fires is how R2-073 nearly condemned
    ten correct calls."""
    import tempfile
    mods = project_modules()
    bad = []

    good = '''"""Doc.

    See itemkit.selftest() and tools/gate_exit.py.
    """
# and gate_exit.verdict() too
'''
    phantom = '''"""Doc.

    See itemkit.socket_audit() and tools/no_such_tool.py.
    """
# and gate_exit.no_such_function() too
'''
    d = tempfile.mkdtemp(prefix="phantom_ctl_")
    for label, src, want in (("NEGATIVE CONTROL: three REAL citations", good, 0),
                             ("POSITIVE CONTROL: three PHANTOM citations",
                              phantom, 3)):
        p = os.path.join(d, "ctl.py")
        open(p, "w").write(src)
        got = check_source(p, mods, {})
        okk = len(got) == want
        print("  %-46s want %d, found %d  %s"
              % (label, want, len(got), "ok" if okk else "*** WRONG ***"))
        for ln, kind, detail in got:
            print("       %s: %s" % (kind, detail))
        if not okk:
            bad.append(label)
    print(">> STAGE RESULT: %s" % ("PHANTOM_SELFTEST_OK" if not bad
                                   else "PHANTOM_SELFTEST_FAIL"))
    return 0 if not bad else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    sys.exit(selftest() if a.selftest else sweep())
