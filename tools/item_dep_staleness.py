#!/usr/bin/env python3
"""R2-116 -- STALENESS AGAINST THE WHOLE SOURCE CLOSURE, NOT JUST THE MODULE FILE.

    blender -b --factory-startup -P tools/item_dep_staleness.py -- --census
    blender -b --factory-startup -P tools/item_dep_staleness.py -- --selftest

WHAT `--stale-census` MEASURES, AND WHAT IT DOES NOT
====================================================
`tools/item_build_cmd.py --stale-census` compares each `*_test.blend` against
`world/items/<module>.py` and reports 15-16 of 32 SUSPECT. That comparison is
correct and it is deliberately narrow -- it is exactly what its own output
claims. But an item module is not the only source that built its blend. Every
one of them builds through `world/itemkit.py`, most through
`world/world_contract.py`, and the figure modules through `world/humankit.py`.

R2-070 IS THIS SHAPE ALREADY: "fix a shared helper, miss its importers. The
helper's author can see every call site INSIDE the helper's file. The call sites
that matter are the ones in files that merely `import` it." A staleness census
keyed on the importer's own mtime has the same blind spot in the other
direction: `itemkit.py` moving is invisible to it, in all 32 rows at once.

So this file asks the same question of the CLOSURE: is the blend older than ANY
project source the module actually loads?

TWO ARMS, R2-073 -- because a census that reads code and never runs it
manufactures defects at the rate it finds them
=======================================================================
STATIC   read `import` / `from ... import` statements out of the module's AST
         and resolve them against `world/`, `world/items/`, and the repo root.
         Cheap, and it cannot see a deferred import inside a function.
RUNTIME  IMPORT the module in this Blender and read `sys.modules` afterwards
         for every loaded module whose `__file__` is inside the repo. That is
         the interpreter answering, not a reading of the source. Import-time
         only: no geometry is built, so it costs milliseconds. It cannot see an
         import that happens inside `build()` and never at import time -- which
         is why both arms are reported and neither is dropped.

Where the two disagree the row prints BOTH, and the closure used for the
verdict is the UNION: a dependency either arm can see is a dependency.

CONTROLS, BOTH DIRECTIONS (R2-072) -- generated, never named
============================================================
`--selftest` writes a throwaway module and a throwaway "blend" into a temp dir
and drives the comparison over them:

  POSITIVE  a blend older than a helper it imports, whose OWN module file is
            NEWER than the blend. `--stale-census`'s rule scores this CLEAN.
            This one must report STALE, and must name the helper. Without this
            arm, "31 of 32" is indistinguishable from a checker that says
            everything is stale.
  NEGATIVE  the same layout with the blend newer than everything. Must report
            CLEAN -- otherwise the positive proves nothing.

Nothing here names a real module or a real blend, so no repair can silently
retire the control.

EXIT CODES (tools/gate_exit.py's scheme)
    0 clean   1 stale rows found   2 could not run   3 nothing measured
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ITEMS = os.path.join(ROOT, "world", "items")


def _argv():
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]


def _resolve(name, search):
    for d in search:
        for cand in (os.path.join(d, name + ".py"),
                     os.path.join(d, name, "__init__.py")):
            if os.path.exists(cand):
                return os.path.abspath(cand)
    return None


def static_closure(path, root=ROOT):
    """Project source files this module names in an import statement."""
    search = [os.path.dirname(path), os.path.join(root, "world"), root]
    try:
        tree = ast.parse(open(path).read(), path)
    except Exception as e:
        return None, "unparseable: %s" % e
    out = set()
    for n in ast.walk(tree):
        names = []
        if isinstance(n, ast.Import):
            names = [a.name.split(".")[0] for a in n.names]
        elif isinstance(n, ast.ImportFrom) and n.module and not n.level:
            names = [n.module.split(".")[0]]
        for nm in names:
            r = _resolve(nm, search)
            if r and r.startswith(root + os.sep) and r != os.path.abspath(path):
                out.add(r)
    return out, "ok"


def _purge_project_modules(root=ROOT):
    """Drop every already-imported PROJECT module from `sys.modules`.

    THE FIRST VERSION OF THIS FILE GOT THIS WRONG AND THE CENSUS SAID SO.
    All 32 items are imported in one interpreter. `itemkit` is loaded by
    whichever item comes first alphabetically, so every later item's
    `set(sys.modules) - before` diff is EMPTY for it -- the runtime arm reported
    0 dependencies for 31 of 32 rows and "disagreed" with the static arm
    everywhere. An import that a previous row already performed is still this
    row's dependency; it is just invisible to a diff. Only project files are
    purged: dropping `bpy` or `numpy` would re-run C extension init.
    """
    for nm, m in list(sys.modules.items()):
        f = getattr(m, "__file__", None)
        if f and os.path.abspath(f).startswith(root + os.sep):
            del sys.modules[nm]


def runtime_closure(module_name, root=ROOT):
    """Project source files actually loaded when the module is IMPORTED."""
    for p in (os.path.join(root, "world"), ITEMS, root):
        if p not in sys.path:
            sys.path.insert(0, p)
    _purge_project_modules(root)
    before = set(sys.modules)
    try:
        __import__(module_name)
    except BaseException as e:
        return None, "import raised %s: %s" % (type(e).__name__, e)
    out = set()
    for nm in set(sys.modules) - before:
        m = sys.modules.get(nm)
        f = getattr(m, "__file__", None) or ""
        f = os.path.abspath(f) if f else ""
        if f.startswith(root + os.sep) and not f.endswith(
                os.path.join("items", module_name + ".py")):
            out.add(f)
    return out, "ok"


def census(runtime=True):
    import glob
    rows = []
    for b in sorted(glob.glob(os.path.join(ITEMS, "*_test.blend"))):
        stem = os.path.basename(b)[: -len("_test.blend")]
        src = os.path.join(ITEMS, stem + ".py")
        if not os.path.exists(src):
            rows.append({"item": stem, "status": "NOT_MEASURED",
                         "why": "no world/items/%s.py" % stem})
            continue
        bm = os.path.getmtime(b)
        st, st_why = static_closure(src)
        rt, rt_why = (runtime_closure(stem) if runtime else (None, "skipped"))
        closure = set(st or ()) | set(rt or ())
        closure.add(os.path.abspath(src))
        newer = sorted((os.path.relpath(p, ROOT), os.path.getmtime(p))
                       for p in closure if os.path.getmtime(p) > bm)
        rows.append({
            "item": stem, "blend_mtime": bm,
            "own_module_newer": os.path.getmtime(src) > bm,
            "static_deps": len(st or ()), "static_why": st_why,
            "runtime_deps": (len(rt) if rt is not None else None),
            "runtime_why": rt_why,
            "arms_disagree": (st is not None and rt is not None
                              and set(st) != set(rt)),
            "newer_than_blend": [n for n, _m in newer],
            "worst_hours": (round((max(m for _n, m in newer) - bm) / 3600.0, 1)
                            if newer else 0.0),
            "status": "STALE_CLOSURE" if newer else "CLEAN",
        })
    return rows


# ---------------------------------------------------------------------------
def selftest():
    import shutil
    import tempfile
    ok = True
    d = tempfile.mkdtemp(prefix="depstale_")
    try:
        w = os.path.join(d, "world")
        it = os.path.join(w, "items")
        os.makedirs(it)
        open(os.path.join(w, "fakekit.py"), "w").write("VALUE = 1\n")
        mod = os.path.join(it, "fakeitem.py")
        open(mod, "w").write("import fakekit\n")

        print("=" * 78)
        print("DEP-STALENESS SELFTEST -- a synthetic module and helper, built here")
        print("=" * 78)

        def run(blend_t, helper_t, mod_t):
            blend = os.path.join(it, "fakeitem_test.blend")
            open(blend, "w").write("x")
            os.utime(os.path.join(w, "fakekit.py"), (helper_t, helper_t))
            os.utime(mod, (mod_t, mod_t))
            os.utime(blend, (blend_t, blend_t))
            st, _ = static_closure(mod, root=d)
            closure = set(st or ()) | {os.path.abspath(mod)}
            newer = sorted(os.path.relpath(p, d) for p in closure
                           if os.path.getmtime(p) > blend_t)
            own_newer = os.path.getmtime(mod) > blend_t
            return newer, own_newer

        now = time.time()
        # POSITIVE: helper newer than the blend, module file OLDER than it --
        # precisely the row `--stale-census` scores CLEAN.
        newer, own_newer = run(blend_t=now - 3600, helper_t=now,
                               mod_t=now - 7200)
        print("\n[POSITIVE CONTROL] blend 1 h old, helper touched NOW, "
              "module file 2 h old")
        print("  own-module rule (what --stale-census uses) says stale: %s"
              % own_newer)
        print("  closure rule says newer-than-blend: %s" % newer)
        if not own_newer and newer == ["world/fakekit.py"]:
            print("  => POSITIVE CONTROL PASSES: the closure arm catches a row "
                  "the own-module rule scores CLEAN, and names the helper.")
        else:
            print("  => POSITIVE CONTROL FAILED. This checker cannot see the "
                  "case it exists for.")
            ok = False

        # NEGATIVE: blend newer than everything.
        newer, own_newer = run(blend_t=now, helper_t=now - 7200,
                               mod_t=now - 7200)
        print("\n[NEGATIVE CONTROL] blend newest of the three")
        print("  closure rule says newer-than-blend: %s" % newer)
        if not newer:
            print("  => NEGATIVE CONTROL PASSES: and it is a verdict, not a "
                  "no-op -- the same code path returned a hit above.")
        else:
            print("  => NEGATIVE CONTROL FAILED: it flags a fresh blend.")
            ok = False

        # RUNTIME ARM, on the real corpus rather than the fixture: it has to
        # actually load something, or "runtime agrees" means nothing.
        rt, why = runtime_closure("spectator_seated")
        n = len(rt) if rt is not None else -1
        print("\n[RUNTIME ARM LIVE] importing world/items/spectator_seated.py "
              "loaded %d project module(s) (%s)" % (n, why))
        if rt:
            for p in sorted(rt):
                print("      %s" % os.path.relpath(p, ROOT))
        if not rt:
            print("  => the runtime arm loaded NOTHING. It is not an arm; the "
                  "census would be static-only and must say so.")
            ok = False
        else:
            print("  => RUNTIME ARM IS LIVE.")

        # SECOND-IMPORT CONTROL. The census imports 32 modules into ONE
        # interpreter. A `set(sys.modules)` diff reports a shared helper only
        # for whichever module loaded it first, and silently reports NOTHING
        # for every module after that -- which is how the first version of this
        # file produced "runtime 0" on 31 of 32 rows. So: import two different
        # real items that share a helper, in order, and require the SECOND to
        # still name it.
        print("\n[SECOND-IMPORT CONTROL] two items that share a helper, "
              "imported in sequence")
        a_rt, _ = runtime_closure("armco_w_beam")
        b_rt, _ = runtime_closure("kerb_precast_unit")
        shared = (set(a_rt or ()) & set(b_rt or ()))
        print("  armco_w_beam        -> %d project module(s)" % len(a_rt or ()))
        print("  kerb_precast_unit   -> %d project module(s)" % len(b_rt or ()))
        print("  shared: %s" % sorted(os.path.relpath(p, ROOT) for p in shared))
        if shared:
            print("  => PASSES: the second import still sees the helper the "
                  "first one loaded. The arm is not blinded by ordering.")
        else:
            print("  => FAILS: the second import saw none of the first's "
                  "modules. Every row after the first is under-reported and "
                  "the census's 'arms disagree' column is an artefact of this "
                  "file, not a fact about the corpus.")
            ok = False
    finally:
        shutil.rmtree(d, ignore_errors=True)

    print("=" * 78)
    print(">> STAGE RESULT: %s" % ("DEP_STALENESS_SELFTEST_OK" if ok
                                   else "DEP_STALENESS_SELFTEST_FAIL"))
    return 0 if ok else 1


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--census", action="store_true")
    p.add_argument("--selftest", action="store_true")
    p.add_argument("--no-runtime", action="store_true")
    p.add_argument("--json", default=None)
    a = p.parse_args(_argv())
    if a.selftest:
        return selftest()
    if not a.census:
        print("nothing asked for: pass --census or --selftest.")
        print(">> STAGE RESULT: DEP_STALENESS_VACUOUS")
        return 3

    rows = census(runtime=not a.no_runtime)
    if not rows:
        print(">> STAGE RESULT: DEP_STALENESS_VACUOUS")
        return 3
    stale = [r for r in rows if r["status"] == "STALE_CLOSURE"]
    own = [r for r in rows if r.get("own_module_newer")]
    nm = [r for r in rows if r["status"] == "NOT_MEASURED"]
    print("item test blends on disk                        %d" % len(rows))
    print("stale by the module's OWN mtime (--stale-census) %d" % len(own))
    print("stale against the whole SOURCE CLOSURE           %d" % len(stale))
    print("not measured                                    %d" % len(nm))
    print()
    for r in sorted(stale, key=lambda r: -r["worst_hours"]):
        flag = " " if r["own_module_newer"] else "*"
        print(" %s %-28s %6.1f h   %s" % (flag, r["item"], r["worst_hours"],
                                          ", ".join(r["newer_than_blend"][:5])))
    print("\n * = the module's own file is OLDER than the blend, so "
          "`--stale-census` scores this row CLEAN.")
    dis = [r for r in rows if r.get("arms_disagree")]
    if dis:
        print("\nARMS DISAGREE on %d row(s) -- the union was used:" % len(dis))
        for r in dis[:10]:
            print("   %-28s static %s  runtime %s" % (r["item"],
                                                      r["static_deps"],
                                                      r["runtime_deps"]))
    bad_rt = [r for r in rows if r.get("runtime_deps") is None
              and r["status"] != "NOT_MEASURED"]
    if bad_rt:
        print("\nSTATIC ONLY -- the runtime arm could not import these, so "
              "their closure is a reading of the source and not a measurement:")
        for r in bad_rt:
            print("   %-28s %s" % (r["item"], r["runtime_why"]))
    if a.json:
        json.dump(rows, open(a.json, "w"), indent=1)
        print("\nwrote %s" % a.json)
    print(">> STAGE RESULT: %s" % ("ITEM_DEPS_STALE" if stale
                                   else "ITEM_DEPS_CLEAN"))
    return 1 if stale else 0


if __name__ == "__main__":
    sys.exit(main())
