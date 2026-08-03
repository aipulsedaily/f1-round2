"""REPORT PROVENANCE — what a report measured, recorded in the report.

WHY THIS EXISTS
===============
Twenty-four times on this project the INSTRUMENT has been the broken thing
rather than the work. The specific failure this module closes is narrower and
more banal than a broken instrument, and it has cost more:

    A report on disk does not say what it was computed from.

Three landed consequences, all real, all from this project:

1.  Fourteen item modules were rebuilt on 2026-08-02 and their gate verdicts
    written to `work/r2038/gate/<module>/gate.json`. The CANONICAL path
    `render/items/<module>/gate.json` still held 29-30 July files.
    `crew_fireproof_overall` read ITEM_ACCEPTED canonically and was in fact
    ITEM_REJECTED. A reviewer opened the canonical file, saw a four-day-old
    verdict, and was one sentence away from reporting that a correct result
    contradicted the disk.

2.  A placement report changed on an UNCHANGED blend, because telemetry and the
    camera path had been rebuilt underneath it. `ARCH_RetainEdge +0.359 m`
    became `BR_Concrete_L12 +4.608 m` with no world change and nothing recorded
    why. Two runs that disagree cannot be told apart from a regression.

3.  A harness measured a four-day-old blend and returned mean |diff| 7.69e-06
    against a 7.70e-06 noise floor -- flawless, entirely convincing, and wrong:
    the real answer was 57.50 %. Nothing in the output said which blend it had
    opened.

None of these is an analysis failure. Every one of them is a MISSING HEADER.
So this is a header block, deliberately not an analysis. It records, for every
report: the INPUT PATH, its MTIME, its CONTENT HASH, the TOOL VERSION and the
CONTRACT VERSION -- and then `verify()` can say, later and mechanically,
whether the thing on disk is still the thing that was measured.

WHAT IT DELIBERATELY DOES NOT DO
================================
It does not judge. A stamp never fails a gate. It answers "what did this
measure?", never "was it good?". Mixing those would make the header something
an author is tempted to argue with.

It does not truncate hashes. A hash of the first N bytes of a .blend is a hash
that agrees across two different .blend files, which is worse than no hash at
all -- it is a hash that LIES, and lying artefacts are the entire subject of
this module. Large files are hashed in full; a 235 MB test blend costs well
under a second and the report is written once.

It does not silently omit a missing input. A stamp with an input quietly left
out is indistinguishable from a stamp of a run that did not use it. A missing,
unreadable or directory input is recorded AS SUCH, with the reason.

THE `describes` FIELD -- read this one
======================================
The trap that follows fixing (1) is subtler than (1): a FRESH `gate.json`
sitting beside a STALE `macro.png` is a new version of the same lie, and it is
harder to catch because the verdict is now correct. So a stamp records not only
what went IN but which sibling artefacts the report CLAIMS TO DESCRIBE, with
their hashes. `verify()` then catches a report whose own illustration has been
replaced, or never was replaced when it should have been.

USAGE
=====
    import provenance as P

    report["provenance"] = P.stamp(
        tool_file=__file__,
        tool_version="rig_version %d" % RIG_VERSION,
        inputs=[("blend", a.blend), ("manifest", manifest_path)],
        describes=[("witness_png", wpng), ("witness_blend", wblend)],
    )

and later, from anywhere:

    python3 tools/provenance.py --verify render/items/*/gate.json

Self-test (proves the check can FAIL, which is the only reason to trust it
when it passes):

    python3 tools/provenance.py --selftest
"""
import hashlib
import json
import os
import platform
import re
import socket
import sys
import time

# Bumped when the SHAPE of the stamp changes, so a reader can tell a stamp it
# does not understand from a stamp that is merely old.
STAMP_VERSION = 1

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The key the stamp is stored under, in every report that carries one.
STAMP_KEY = "provenance"

_HASH_CHUNK = 1 << 20


# --------------------------------------------------------------------------
# 1.  ONE FILE
# --------------------------------------------------------------------------
def file_facts(path, role=None):
    """Path, mtime, size and full sha256 of one file.

    A file that is missing, unreadable, or a directory is recorded as such --
    never omitted. `{"role": "telemetry", "status": "MISSING"}` is a fact about
    the run; a silently absent key is not.
    """
    d = {"role": role, "path": None, "status": "OK",
         "mtime": None, "mtime_iso": None, "bytes": None, "sha256": None}
    if path is None:
        d["status"] = "NOT_GIVEN"
        return d
    p = str(path)
    d["path"] = os.path.abspath(p)
    try:
        st = os.stat(d["path"])
    except OSError as e:
        d["status"] = "MISSING"
        d["error"] = "%s: %s" % (type(e).__name__, e)
        return d
    d["mtime"] = round(st.st_mtime, 3)
    d["mtime_iso"] = time.strftime("%Y-%m-%dT%H:%M:%S",
                                   time.localtime(st.st_mtime))
    d["bytes"] = st.st_size
    if os.path.isdir(d["path"]):
        d["status"] = "DIRECTORY"
        return d
    t0 = time.time()
    h = hashlib.sha256()
    try:
        with open(d["path"], "rb") as fh:
            for chunk in iter(lambda: fh.read(_HASH_CHUNK), b""):
                h.update(chunk)
    except OSError as e:
        d["status"] = "UNREADABLE"
        d["error"] = "%s: %s" % (type(e).__name__, e)
        return d
    d["sha256"] = h.hexdigest()
    dt = time.time() - t0
    if dt > 0.25:                      # only worth saying when it cost anything
        d["hash_seconds"] = round(dt, 2)
    return d


# --------------------------------------------------------------------------
# 2.  VERSIONS
# --------------------------------------------------------------------------
def contract_version(path=None):
    """`world_contract.__version__` WITHOUT importing it.

    Read from source text on purpose: importing the contract drags in bpy and
    a multi-thousand-line module, and a stamp must be cheap enough that nobody
    is ever tempted to skip it. If the module happens to be imported already,
    that value is preferred -- it is the one actually in play.
    """
    mod = sys.modules.get("world_contract")
    if mod is not None and getattr(mod, "__version__", None):
        return str(mod.__version__)
    p = path or os.path.join(R2, "world", "world_contract.py")
    try:
        with open(p, "r", errors="replace") as fh:
            for line in fh:
                m = re.match(r'''^__version__\s*=\s*["'](.+?)["']''', line)
                if m:
                    return m.group(1)
    except OSError:
        pass
    return None


def blender_version():
    """The running Blender, or None outside Blender. Not guessed."""
    try:
        import bpy                                             # noqa: F401
    except Exception:
        return None
    try:
        return {"version": bpy.app.version_string,
                "hash": bpy.app.build_hash.decode()
                if isinstance(bpy.app.build_hash, bytes)
                else str(bpy.app.build_hash)}
    except Exception:
        return {"version": None, "hash": None}


# --------------------------------------------------------------------------
# 3.  THE STAMP
# --------------------------------------------------------------------------
def stamp(tool_file, inputs=(), describes=(), tool_version=None,
          also_hash=(), extra=None):
    """The header block. Cheap, mechanical, and never a verdict.

    tool_file     __file__ of the tool writing the report.
    inputs        [(role, path), ...] -- everything the numbers were computed
                  FROM. Under-declaring here is the whole defect: the placement
                  report that moved 4.2 m on an unchanged blend had moved
                  because of `--telemetry` and `--campath`, neither of which
                  the report mentioned.
    describes     [(role, path), ...] -- sibling artefacts this report CLAIMS
                  TO DEPICT (the witness png, the macro render). A fresh
                  verdict beside a stale illustration is the same lie wearing
                  a clean shirt.
    tool_version  the tool's own declared version, if it has one
                  (item_gate's RIG_VERSION, placement_gate's spec revision).
                  The file hash covers the code regardless; this is for humans.
    also_hash     [(role, path), ...] -- shared code whose content changes the
                  answer without appearing in argv: itemkit, the contract.
    """
    ins = [file_facts(p, role=r) for r, p in inputs]
    des = [file_facts(p, role=r) for r, p in describes]
    aux = [file_facts(p, role=r) for r, p in also_hash]
    # itemkit and the contract change results without ever appearing on a
    # command line, so they are stamped by default rather than by remembering.
    have = {a["path"] for a in aux if a.get("path")}
    for role, p in (("itemkit", os.path.join(R2, "world", "itemkit.py")),
                    ("world_contract",
                     os.path.join(R2, "world", "world_contract.py"))):
        ap = os.path.abspath(p)
        if os.path.exists(ap) and ap not in have:
            aux.append(file_facts(ap, role=role))

    d = {
        "stamp_version": STAMP_VERSION,
        "written_at_iso": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "written_at": round(time.time(), 3),
        "tool": file_facts(tool_file, role="tool"),
        "tool_version": tool_version,
        "contract_version": contract_version(),
        "blender": blender_version(),
        "inputs": ins,
        "describes": des,
        "also_hash": aux,
        "argv": list(sys.argv),
        "cwd": os.getcwd(),
        "host": socket.gethostname(),
        "python": platform.python_version(),
    }
    if extra:
        d["extra"] = extra
    return d


def attach(report, **kw):
    """`report[STAMP_KEY] = stamp(**kw)`, returning the report. Convenience so
    a call site is one line and nobody is tempted to skip it."""
    report[STAMP_KEY] = stamp(**kw)
    return report


# --------------------------------------------------------------------------
# 4.  VERIFY — the half that makes the stamp worth writing
# --------------------------------------------------------------------------
def verify(report_path, check_describes=True):
    """Re-measure a stamped report's inputs and say what has moved since.

    Returns a dict with `status` in:
        OK              every input and described artefact still matches
        DRIFTED         at least one input's content differs from the stamp
        GONE            at least one input no longer exists
        UNSTAMPED       the report carries no stamp (i.e. predates this module)
        UNREADABLE      the report itself could not be read

    DRIFTED is not automatically wrong. It is the thing that could not be
    SEEN before: a report and a world that have parted company. Whether that
    means "re-run" or "this is a historical record" is a judgement, and this
    function deliberately does not make it.
    """
    out = {"report": os.path.abspath(str(report_path)), "status": "OK",
           "drift": [], "missing": [], "note": None}
    try:
        with open(report_path) as fh:
            rep = json.load(fh)
    except Exception as e:
        out["status"] = "UNREADABLE"
        out["note"] = "%s: %s" % (type(e).__name__, e)
        return out
    st = rep.get(STAMP_KEY)
    if not isinstance(st, dict):
        out["status"] = "UNSTAMPED"
        out["note"] = ("no %r block: this report predates provenance stamping "
                       "and cannot say what it measured" % STAMP_KEY)
        return out
    out["stamp_version"] = st.get("stamp_version")
    out["written_at_iso"] = st.get("written_at_iso")
    groups = [("inputs", st.get("inputs") or []),
              ("also_hash", st.get("also_hash") or []),
              ("tool", [st.get("tool")] if st.get("tool") else [])]
    if check_describes:
        groups.append(("describes", st.get("describes") or []))
    for group, items in groups:
        for was in items:
            if not isinstance(was, dict) or not was.get("path"):
                continue
            if was.get("status") not in ("OK", None):
                continue                      # already recorded as absent then
            now = file_facts(was["path"], role=was.get("role"))
            if now["status"] != "OK":
                out["missing"].append({"group": group, "role": was.get("role"),
                                       "path": was["path"],
                                       "now": now["status"]})
                continue
            if was.get("sha256") and now["sha256"] != was["sha256"]:
                out["drift"].append({
                    "group": group, "role": was.get("role"),
                    "path": was["path"],
                    "measured_sha256": was["sha256"][:16],
                    "current_sha256": now["sha256"][:16],
                    "measured_mtime": was.get("mtime_iso"),
                    "current_mtime": now["mtime_iso"]})
    if out["missing"]:
        out["status"] = "GONE"
    elif out["drift"]:
        out["status"] = "DRIFTED"
    return out


# --------------------------------------------------------------------------
# 5.  SELFTEST — a positive control that FAILS and a negative that PASSES
# --------------------------------------------------------------------------
def selftest(verbose=True):
    """Prove `verify` can see drift before trusting it when it reports none.

    A check that has never been observed to fire has not been shown to work.
    That sentence is the reason this project has a defect log with 57 entries
    in it, so it is enforced here rather than recommended.
    """
    import tempfile
    ok, fails = [], []

    def chk(name, cond, detail):
        ok.append((name, bool(cond), detail))
        if not cond:
            fails.append(name)
        if verbose:
            print("  %-38s %-4s %s" % (name, "PASS" if cond else "FAIL", detail))

    tmp = tempfile.mkdtemp(prefix="prov_selftest_")
    src = os.path.join(tmp, "input.blend")
    art = os.path.join(tmp, "witness.png")
    rep = os.path.join(tmp, "gate.json")
    with open(src, "wb") as fh:
        fh.write(b"ORIGINAL INPUT")
    with open(art, "wb") as fh:
        fh.write(b"ORIGINAL ARTEFACT")

    report = {"result": "ITEM_ACCEPTED"}
    attach(report, tool_file=__file__, tool_version="selftest",
           inputs=[("blend", src)], describes=[("witness_png", art)])
    with open(rep, "w") as fh:
        json.dump(report, fh, indent=1)

    # --- the stamp records what it claims to record -----------------------
    st = report[STAMP_KEY]
    chk("stamp_has_input_path", st["inputs"][0]["path"] == src,
        st["inputs"][0]["path"])
    chk("stamp_has_input_hash", bool(st["inputs"][0]["sha256"]),
        (st["inputs"][0]["sha256"] or "")[:16])
    chk("stamp_has_input_mtime", st["inputs"][0]["mtime"] is not None,
        str(st["inputs"][0]["mtime_iso"]))
    chk("stamp_has_tool_hash", bool(st["tool"]["sha256"]),
        (st["tool"]["sha256"] or "")[:16])
    chk("stamp_has_contract_version", st["contract_version"] is not None,
        str(st["contract_version"]))

    # --- NEGATIVE CONTROL: nothing changed, verify must PASS --------------
    v = verify(rep)
    chk("negative_control_unchanged_is_OK", v["status"] == "OK",
        "status=%s drift=%d missing=%d"
        % (v["status"], len(v["drift"]), len(v["missing"])))

    # --- POSITIVE CONTROL 1: the INPUT is rewritten, verify must FAIL ------
    #     Same byte length, so a size-only check would miss it. Mtime is left
    #     alone deliberately: this reproduces the real fault, where a rebuilt
    #     input had DIFFERENT CONTENT and the report never noticed.
    time.sleep(0.01)
    with open(src, "wb") as fh:
        fh.write(b"REBUILT_ INPUT")           # 14 bytes, same as ORIGINAL INPUT
    v = verify(rep)
    chk("positive_control_input_drift_FIRES", v["status"] == "DRIFTED",
        "status=%s, drifted=%s"
        % (v["status"], [d["role"] for d in v["drift"]]))
    chk("positive_control_same_size_still_caught",
        os.path.getsize(src) == 14 and v["status"] == "DRIFTED",
        "%d bytes, still caught" % os.path.getsize(src))

    # --- POSITIVE CONTROL 2: THE ACTUAL TRAP ------------------------------
    #     Restore the input, then change only the DESCRIBED artefact. This is
    #     "a fresh gate.json beside a stale macro.png" in miniature: the
    #     verdict's inputs are pristine and the picture it ships with is not.
    with open(src, "wb") as fh:
        fh.write(b"ORIGINAL INPUT")
    v = verify(rep)
    chk("input_restored_is_OK_again", v["status"] == "OK", "status=%s" % v["status"])
    with open(art, "wb") as fh:
        fh.write(b"A DIFFERENT ARTEFACT ENTIRELY")
    v = verify(rep)
    chk("positive_control_stale_sibling_FIRES",
        v["status"] == "DRIFTED"
        and any(d["group"] == "describes" for d in v["drift"]),
        "status=%s, drifted=%s"
        % (v["status"], [(d["group"], d["role"]) for d in v["drift"]]))

    # --- POSITIVE CONTROL 3: input deleted --------------------------------
    with open(art, "wb") as fh:
        fh.write(b"ORIGINAL ARTEFACT")
    os.remove(src)
    v = verify(rep)
    chk("positive_control_missing_input_FIRES", v["status"] == "GONE",
        "status=%s, missing=%s"
        % (v["status"], [m["role"] for m in v["missing"]]))

    # --- an UNSTAMPED report is called out, not silently passed -----------
    bare = os.path.join(tmp, "bare.json")
    with open(bare, "w") as fh:
        json.dump({"result": "ITEM_ACCEPTED"}, fh)
    v = verify(bare)
    chk("unstamped_report_is_flagged", v["status"] == "UNSTAMPED", v["note"])

    # --- a missing input is RECORDED, never omitted -----------------------
    f = file_facts(os.path.join(tmp, "does_not_exist"), role="ghost")
    chk("missing_input_is_recorded_not_omitted",
        f["status"] == "MISSING" and f["role"] == "ghost",
        "%s / role=%s" % (f["status"], f["role"]))

    for p in (art, rep, bare):
        try:
            os.remove(p)
        except OSError:
            pass
    try:
        os.rmdir(tmp)
    except OSError:
        pass

    if verbose:
        print("\n  %d/%d checks pass%s"
              % (len(ok) - len(fails), len(ok),
                 "" if not fails else "   FAILED: " + ", ".join(fails)))
    return not fails


# --------------------------------------------------------------------------
def _main(argv):
    import argparse
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--selftest", action="store_true")
    p.add_argument("--verify", nargs="*", default=None,
                   metavar="REPORT.json")
    p.add_argument("--json", default=None, help="write verify results here")
    p.add_argument("--quiet", action="store_true")
    a = p.parse_args(argv)

    if a.selftest:
        return 0 if selftest(verbose=not a.quiet) else 1

    if a.verify is not None:
        rows = [verify(x) for x in a.verify]
        worst = 0
        for r in rows:
            if not a.quiet:
                print("%-10s %s" % (r["status"], r["report"]))
                for d in r["drift"]:
                    print("    DRIFT   %-14s %s" % (d["role"], d["path"]))
                    print("            measured %s @ %s -> now %s @ %s"
                          % (d["measured_sha256"], d["measured_mtime"],
                             d["current_sha256"], d["current_mtime"]))
                for m in r["missing"]:
                    print("    %-7s %-14s %s" % (m["now"], m["role"], m["path"]))
            worst = max(worst, {"OK": 0, "UNSTAMPED": 1, "DRIFTED": 2,
                                "GONE": 2, "UNREADABLE": 2}[r["status"]])
        if a.json:
            os.makedirs(os.path.dirname(os.path.abspath(a.json)), exist_ok=True)
            with open(a.json, "w") as fh:
                json.dump(rows, fh, indent=1)
        return worst

    p.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
