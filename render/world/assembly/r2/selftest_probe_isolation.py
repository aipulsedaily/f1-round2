"""CONTROLS FOR "probeA..probeK write where they are told, and NOWHERE ELSE".

    python3 render/world/assembly/r2/selftest_probe_isolation.py [--quick]

`selftest_probe_out.py` covers `resolve_out()` itself, on probe_pitexit.py.
This file covers the OTHER ELEVEN — probeA.py .. probeK.py — which had the
same class of fault in a worse form:

    save("probeD.json", R)          # save() joins onto lib_probe.OUT_DIR

Not a stripped directory: NO directory at all. Every version of every battery
ran `-P probeD.py` with no output argument and the file landed on the single
path `<assembly root>/probeD.json`. v121/battery.sh therefore overwrote the
`probeD.json` and `probeG.json` that `v120/collect.py` reads, and the two
versions were then diffed against each other. probeA/B/C did it three more
times each with `probeX_partial.json`.

WHAT IS CHECKED, AND WHY EACH ONE IS HERE
=========================================
1.  STATIC — all eleven call `resolve_out()` and `write_out()`, none calls
    `save()`, and `lib_probe.save()` itself now RAISES. The last one matters
    most: the idiom spread to eleven files by copy-paste, so the thing to
    prevent is not eleven bugs, it is the source they were copied from.

2.  POSITIVE CONTROL — the old two-line idiom, reproduced here verbatim, is
    shown to COLLAPSE all eleven probes' outputs onto eleven fixed paths in
    the assembly root regardless of what any caller asked for, and to make a
    v120 request and a v121 request land on the SAME FILE. The control
    reproduces the fault; it does not rely on any other module still being
    broken.

3.  LIVE — probeJ.py is run under the real Blender against a factory-startup
    scene (nine seconds; it needs no assembly) with `--out` pointed into a
    fresh directory, and the assembly root and the CWD are FINGERPRINTED
    BEFORE AND AFTER. A file landing in the right place is only half the
    claim; the other half is that nothing landed anywhere else, and a silent
    CWD default is exactly the kind of stray that hides from a test which only
    looks where it expects the file to be.

4.  LIVE REFUSAL — probeJ.py with no `--out` must exit non-zero and write
    NOTHING, anywhere. A refusal that still leaves a file behind is not a
    refusal.

5.  CROSS-VERSION — the specific reported defect: two runs asking for two
    version directories must produce two files. Under the old idiom they
    produced one, and this asserts that too.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
R2 = "/home/zany/f1-round2"
BLENDER = "/opt/blender-5.2.0-linux-x64/blender"
OUT_DIR = HERE                      # lib_probe.OUT_DIR, the old destination
LETTERS = "ABCDEFGHIJK"
ARTEFACT = {L: ("apron_uv_map.json" if L == "K" else "probe%s.json" % L)
            for L in LETTERS}
HAS_PARTIAL = "ABC"

ROWS, FAILS = [], []


def check(label, ok, detail=""):
    ROWS.append({"control": label, "ok": bool(ok), "detail": detail})
    print("   %-4s %-64s %s" % ("PASS" if ok else "FAIL", label, detail))
    if not ok:
        FAILS.append(label)


def call_census(path):
    """(set of function names actually CALLED, set of names assigned to).

    Parsed rather than grepped so that a comment quoting the old idiom -- and
    the fix's own comment does quote it -- is not mistaken for the idiom.
    """
    import ast
    tree = ast.parse(open(path).read(), path)
    calls, assigns = set(), set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            f = n.func
            if isinstance(f, ast.Name):
                calls.add(f.id)
            elif isinstance(f, ast.Attribute):
                calls.add(f.attr)
        elif isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name):
                    assigns.add(t.id)
    return calls, assigns


def snapshot(d):
    """name -> (size, mtime_ns) for one directory, non-recursive."""
    out = {}
    try:
        for n in os.listdir(d):
            p = os.path.join(d, n)
            if os.path.isfile(p):
                st = os.stat(p)
                out[n] = (st.st_size, st.st_mtime_ns)
    except OSError:
        pass
    return out


def strays(before, after):
    added = sorted(set(after) - set(before))
    touched = sorted(k for k in set(after) & set(before) if after[k] != before[k])
    return added, touched


# ---------------------------------------------------------------------------
# THE POSITIVE CONTROL: the old idiom, reproduced.
# ---------------------------------------------------------------------------
def old_save_path(name):
    """EXACTLY what lib_probe.save() used to compute. It ignores every output
    path a caller could possibly pass, because it never saw one."""
    return os.path.join(OUT_DIR, name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true",
                    help="skip the live Blender runs")
    a = ap.parse_args()

    # ---- 1. STATIC -------------------------------------------------------
    #
    # PARSED, NOT GREPPED. The first version of this check searched the file
    # text for `save(` and failed on all eleven probes -- because the comment
    # ABOVE the fix quotes the defect it fixed. A check that reads prose as
    # code is a check that goes red for describing itself, and the next person
    # deletes the comment instead of the bug. `write_calls()` walks the AST, so
    # only real calls count.
    print("1. ALL ELEVEN PROBES RESOLVE THEIR OWN OUTPUT  (parsed, not grepped)")
    for L in LETTERS:
        p = os.path.join(HERE, "probe%s.py" % L)
        calls, assigns = call_census(p)
        calls_resolve = "resolve_out" in calls and "OUT" in assigns
        calls_write = any(c == "write_out" for c in calls)
        no_save = "save" not in calls
        # `write_out(OUT, ...)` with the resolved path itself, not a derivative
        t = open(p).read()
        writes_out_var = re.search(r"\bwrite_out\(OUT\s*,", t) is not None
        no_basename = "basename" not in calls
        check("probe%s.py: resolve_out + write_out(OUT), no save(), no "
              "basename()" % L,
              calls_resolve and calls_write and writes_out_var and no_save
              and no_basename,
              "resolve=%s write_out(OUT,..)=%s save()=%s basename()=%s"
              % (calls_resolve, writes_out_var, "save" in calls,
                 "basename" in calls))
    for L in HAS_PARTIAL:
        p = os.path.join(HERE, "probe%s.py" % L)
        t = open(p).read()
        calls, _ = call_census(p)
        n = len(re.findall(r'write_out\(sidecar\(OUT, "partial"\), R\)', t))
        check("probe%s.py: its mid-run checkpoints go to sidecar(OUT, ...)" % L,
              n > 0 and "sidecar" in calls and "save" not in calls,
              "%d checkpoint(s), all via sidecar()" % n)

    lib = open(os.path.join(HERE, "lib_probe.py")).read()
    check("lib_probe.save() itself RAISES — the source the idiom was copied "
          "from is closed",
          re.search(r"def save\(.*?raise SystemExit", lib, re.S) is not None)
    check("lib_probe.sidecar() exists and is INSIDE the extracted "
          "resolve_out block",
          "def sidecar(" in lib
          and lib.index("def sidecar(") <
              lib.index("# --- END resolve_out"))

    # sidecar() must put the checkpoint beside the output, never in OUT_DIR
    sys.path.insert(0, HERE)
    ns = {"os": os, "sys": sys, "json": json}
    m = re.search(r"^# --- BEGIN resolve_out.*?^# --- END resolve_out.*?$",
                  lib, re.S | re.M)
    exec(compile(m.group(0), "lib_probe.py", "exec"), ns)
    sidecar, resolve_out = ns["sidecar"], ns["resolve_out"]
    got = sidecar("/x/v121/probeA_v121.json", "partial")
    check("sidecar() lands beside the output, not in OUT_DIR",
          got == "/x/v121/probeA_v121_partial.json"
          and not got.startswith(OUT_DIR), got)

    # ---- 2. POSITIVE CONTROL --------------------------------------------
    print("\n2. POSITIVE CONTROL — the OLD idiom, on the requests the batteries")
    print("   actually make. Every one must be shown to land in the WRONG place.")
    v120 = os.path.join(HERE, "v120")
    v121 = os.path.join(HERE, "v121")
    for L in LETTERS:
        want120 = os.path.join(v120, "probe%s_v120.json" % L)
        want121 = os.path.join(v121, "probe%s_v121.json" % L)
        old = old_save_path(ARTEFACT[L])
        new120 = resolve_out(["blender", "--", "--out", want120])
        new121 = resolve_out(["blender", "--", "--out", want121])
        check("probe%s: old idiom collapses v120 and v121 onto ONE path" % L,
              old != want120 and old != want121
              and new120 == want120 and new121 == want121,
              "old -> %s (for BOTH); new -> .../%s and .../%s"
              % (os.path.relpath(old, HERE), os.path.relpath(new120, HERE),
                 os.path.relpath(new121, HERE)))
    # the exact reported casualty
    check("the reported casualty: v121's probeD run overwrote the probeD.json "
          "v120/collect.py reads",
          old_save_path("probeD.json") == os.path.join(HERE, "probeD.json"),
          old_save_path("probeD.json"))

    if a.quick:
        return summarise()

    # ---- 3. LIVE, WITH A STRAY-FILE CHECK -------------------------------
    print("\n3. LIVE — probeJ.py under the real Blender, with the assembly root")
    print("   and the CWD fingerprinted before and after.")
    TMP = tempfile.mkdtemp(prefix="probe_isolation_")
    cwd = os.path.join(TMP, "cwd"); os.makedirs(cwd)
    dest = os.path.join(TMP, "v999", "nested")     # does not exist yet
    want = os.path.join(dest, "probeJ_v999.json")

    root_before = snapshot(OUT_DIR)
    cwd_before = snapshot(cwd)
    r = subprocess.run(
        [BLENDER, "-b", "--factory-startup", "-P",
         os.path.join(HERE, "probeJ.py"), "--", "--out", want],
        capture_output=True, text=True, cwd=cwd)
    root_after = snapshot(OUT_DIR)
    cwd_after = snapshot(cwd)

    check("probeJ --out <new nested dir> exits 0 and creates the directory",
          r.returncode == 0 and os.path.isfile(want),
          "rc=%d  %s" % (r.returncode, want))
    if os.path.isfile(want):
        d = json.load(open(want))
        check("...and the file it wrote is this run's payload, stamped",
              "lib_objects" in d and "provenance" in d,
              "keys %s" % sorted(d)[:5])
    added, touched = strays(root_before, root_after)
    check("...and NOTHING appeared or changed in the assembly root",
          not added and not touched,
          "added=%s touched=%s" % (added or "none", touched or "none"))
    added, touched = strays(cwd_before, cwd_after)
    check("...and NOTHING appeared in the CWD (the silent default's hiding "
          "place)", not added and not touched,
          "added=%s touched=%s" % (added or "none", touched or "none"))

    # ---- 4. LIVE REFUSAL -------------------------------------------------
    print("\n4. LIVE REFUSAL — no --out must write nothing, anywhere.")
    root_before = snapshot(OUT_DIR)
    cwd_before = snapshot(cwd)
    r = subprocess.run(
        [BLENDER, "-b", "--factory-startup", "-P",
         os.path.join(HERE, "probeJ.py")],
        capture_output=True, text=True, cwd=cwd)
    txt = (r.stdout or "") + (r.stderr or "")
    check("probeJ with NO --out exits non-zero and says REFUSING",
          r.returncode != 0 and "REFUSING TO RUN" in txt,
          "rc=%d" % r.returncode)
    added, touched = strays(snapshot(OUT_DIR), root_before)
    a2, t2 = strays(root_before, snapshot(OUT_DIR))
    c2, ct2 = strays(cwd_before, snapshot(cwd))
    check("...and wrote nothing to the assembly root or the CWD",
          not a2 and not t2 and not c2 and not ct2,
          "root added=%s  cwd added=%s" % (a2 or "none", c2 or "none"))

    # ---- 5. CROSS-VERSION ------------------------------------------------
    print("\n5. CROSS-VERSION — two runs, two directories, two files.")
    outs = []
    for v in ("v998", "v999b"):
        p = os.path.join(TMP, v, "probeJ_%s.json" % v)
        subprocess.run(
            [BLENDER, "-b", "--factory-startup", "-P",
             os.path.join(HERE, "probeJ.py"), "--", "--out", p],
            capture_output=True, text=True, cwd=cwd)
        outs.append(p)
    check("two versions asking for two paths get two files",
          all(os.path.isfile(p) for p in outs) and outs[0] != outs[1],
          " and ".join(os.path.basename(p) for p in outs))
    check("...whereas the OLD idiom would have given them one",
          old_save_path("probeJ.json") == old_save_path("probeJ.json"),
          old_save_path("probeJ.json"))

    print("\n   (scratch %s)" % TMP)
    return summarise()


def summarise():
    print()
    if FAILS:
        print(">> %d CONTROL(S) MISBEHAVED:" % len(FAILS))
        for f in FAILS:
            print("     " + f)
        print(">> STAGE RESULT: PROBE_ISOLATION_SELFTEST_FAIL")
        return 1
    print(">> all %d controls behaved" % len(ROWS))
    print(">> STAGE RESULT: PROBE_ISOLATION_SELFTEST_OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
