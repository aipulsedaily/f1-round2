"""PROMOTE a rebuilt gate report into its canonical slot -- with its evidence.

    python3 tools/promote_gate_reports.py --plan          # print, change nothing
    python3 tools/promote_gate_reports.py --apply

WHY
===
Fourteen item modules were rebuilt on 2026-08-02 (dead bump stacks repaired,
111 stages -> 0) and re-gated. The verdicts landed in
`work/r2038/gate/<module>/gate.json`. The CANONICAL path that everyone reads,
`render/items/<module>/gate.json`, still served **29-30 July** files.
`crew_fireproof_overall` read ITEM_ACCEPTED canonically and was in fact
ITEM_REJECTED. A reviewer verifying an agent's work opened the canonical file
and was one sentence away from reporting that a correct result contradicted the
disk. It did not. The disk was four days old.

THE TRAP THAT FOLLOWS FIXING THAT ONE
=====================================
A fresh `gate.json` beside a stale `macro.png` is a new version of the same lie,
and a worse one, because the verdict is now right and only the picture is wrong.
So this promotes a COMPLETE SET or it promotes nothing:

    gate.json          the verdict
    gate_run.log       the console trace that produced it
    build.log          the build that produced the blend it read
    witness.png        THE FRAME THE VERDICT WAS COMPUTED FROM, frozen here
    witness_spec.json  the control regions that frame was measured against
    PROVENANCE.json    every hash, every mtime, and every refusal below

and everything the canonical directory held from before the rebuild is MOVED,
not deleted, into `_superseded_<date>/`. Nothing is destroyed and nothing stale
is left sitting next to a fresh verdict.

WHY THE WITNESS FRAME IS COPIED AND NOT SYMLINKED
=================================================
It was going to be a symlink into `render/gate_witness/<module>/`, on the
reasoning that a link cannot go stale. That reasoning is wrong, and this
project has the counter-example: `render/gate_witness/armco_w_beam/witness.png`
was OVERWRITTEN at 19:14:51 by a later diagnostic run, 103 seconds after the
verdict at 19:13:08 was computed from the previous contents. A symlink would
have followed the overwrite silently and served a different picture under the
verdict's name. A frozen copy plus a recorded hash cannot.

WHAT IT REFUSES TO DO
=====================
1.  It will not promote a report whose build does not postdate the last edit of
    the module source. Promoting a stale report INTO the canonical slot is
    strictly worse than leaving the canonical slot stale, because it launders
    the staleness through a fresh mtime.
2.  It will not ship a witness frame that was written AFTER the verdict that
    supposedly measured it. Where that happened the frame is promoted under the
    name `witness_OVERWRITTEN_by_later_run.png` and PROVENANCE.json records that
    the verdict's own frame no longer exists on disk.
3.  `gate_pinned.json` is never promoted as a verdict. The pipeline that wrote
    it labels it "pinned run -- NOT the verdict" (`work/r2038/run_module2.sh`
    line 105): it re-gates with `--subject` forced to whatever the BEFORE
    witness framed, to check that an A/B pair looked at the same object. It
    disagrees with the verdict for two modules, by design. It is promoted into
    `diagnostic_pinned_subject/` with a README, or not at all.
"""
import argparse
import json
import os
import shutil
import sys
import time

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(R2, "tools"))
import provenance as P                                           # noqa: E402

SRC_ROOT = os.path.join(R2, "work", "r2038", "gate")
DST_ROOT = os.path.join(R2, "render", "items")
SRC_PY = os.path.join(R2, "world", "items")

# The gate rewrite that took the check count from 4 to 8. Everything canonical
# older than this was written by a gate that could not measure
# surface_microstructure, relief_reads_as_lip_and_shade, witness_frame_valid or
# silhouette_departs_from_analytic at all.
GATE_REWRITE_ISO = "2026-07-29T23:00:00"


def facts(p, role=None):
    return P.file_facts(p, role=role)


def assess(module):
    """Everything knowable about one promotion, before anything is moved."""
    src = os.path.join(SRC_ROOT, module)
    dst = os.path.join(DST_ROOT, module)
    a = {"module": module, "src": src, "dst": dst, "refusals": [],
         "warnings": []}

    gj = os.path.join(src, "gate.json")
    if not os.path.exists(gj):
        a["refusals"].append("no gate.json in %s" % src)
        return a
    rep = json.load(open(gj))
    a["result"] = rep.get("result")
    a["n_checks"] = len(rep.get("checks") or {})
    a["failing"] = [k for k, v in (rep.get("checks") or {}).items() if v is False]
    a["unmeasurable"] = rep.get("unmeasurable") or []
    a["gate_json"] = facts(gj, "gate.json")

    # ---- the blend the gate actually READ, from its own console trace ----
    blend = None
    runlog = os.path.join(src, "run.log")
    if os.path.exists(runlog):
        with open(runlog, errors="replace") as fh:
            for line in fh:
                if "Read blend:" in line:
                    blend = line.split("Read blend:")[1].strip().strip('"')
                    break
    a["blend"] = facts(blend, "blend") if blend else {"status": "NOT_GIVEN"}

    # ---- ORDERING: report must postdate the source it claims to describe --
    py = os.path.join(SRC_PY, module + ".py")
    a["source_py"] = facts(py, "source_py")
    gm = a["gate_json"].get("mtime")
    bm = a["blend"].get("mtime")
    sm = a["source_py"].get("mtime")
    if sm and bm and bm <= sm:
        a["refusals"].append(
            "the blend the gate read (%s) PREDATES the module source (%s) -- "
            "this verdict describes a build that no longer exists"
            % (a["blend"]["mtime_iso"], a["source_py"]["mtime_iso"]))
    if bm and gm and gm <= bm:
        a["refusals"].append(
            "gate.json (%s) predates the blend it read (%s)"
            % (a["gate_json"]["mtime_iso"], a["blend"]["mtime_iso"]))
    a["ordering_ok"] = not a["refusals"]

    # ---- the witness set, and whether it is still the VERDICT's -----------
    w = rep.get("witness") or {}
    a["witness"] = {}
    for key in ("png", "spec", "blend"):
        p = w.get(key)
        f = facts(p, "witness_" + key)
        if f.get("status") == "OK" and gm and f["mtime"] > gm:
            f["verdict_frame"] = False
            f["note"] = ("written %s, AFTER the verdict at %s -- a later run "
                         "overwrote it; this is NOT the frame the verdict was "
                         "computed from"
                         % (f["mtime_iso"], a["gate_json"]["mtime_iso"]))
        elif f.get("status") == "OK":
            f["verdict_frame"] = True
        a["witness"][key] = f
    if a["witness"].get("png", {}).get("verdict_frame") is False:
        a["warnings"].append(
            "the verdict's own witness frame no longer exists on disk")

    # ---- the pinned diagnostic, if any -----------------------------------
    pin = os.path.join(src, "gate_pinned.json")
    if os.path.exists(pin):
        pj = json.load(open(pin))
        a["pinned"] = {"result": pj.get("result"),
                       "failing": [k for k, v in (pj.get("checks") or {}).items()
                                   if v is False],
                       "agrees_with_verdict": pj.get("result") == a["result"]}

    # ---- what is currently in the canonical slot -------------------------
    cur = []
    if os.path.isdir(dst):
        for n in sorted(os.listdir(dst)):
            p = os.path.join(dst, n)
            if os.path.isdir(p):
                cur.append({"name": n, "kind": "dir", "action": "left alone"})
                continue
            st = os.stat(p)
            stale = gm is not None and st.st_mtime < gm
            cur.append({"name": n, "kind": "file",
                        "mtime_iso": time.strftime("%Y-%m-%dT%H:%M:%S",
                                                   time.localtime(st.st_mtime)),
                        "bytes": st.st_size,
                        "action": "supersede" if stale else "left alone"})
    a["canonical_now"] = cur
    a["canonical_gate_json"] = None
    old = os.path.join(dst, "gate.json")
    if os.path.exists(old):
        try:
            oj = json.load(open(old))
            a["canonical_gate_json"] = {
                "result": oj.get("result"),
                "n_checks": len(oj.get("checks") or {}),
                "mtime_iso": time.strftime(
                    "%Y-%m-%dT%H:%M:%S",
                    time.localtime(os.stat(old).st_mtime))}
        except Exception as e:
            a["canonical_gate_json"] = {"error": str(e)}
    return a


def refuse(a, apply=False):
    """Refusing is not the same as saying nothing.

    A refused promotion leaves the canonical slot holding an OLDER verdict while
    a newer one is known to exist and to disagree. Dropping that fact on the
    floor recreates the defect from the other direction: the reader is again
    looking at a file that does not know what it does not know. So the refusal
    is written down, in the canonical directory, naming where the newer verdict
    lives and why it was not promoted.
    """
    dst = a["dst"]
    note = {
        "STATUS": "PENDING_REGATE",
        "one_line": ("a NEWER gate verdict exists for this item and was "
                     "REFUSED promotion; the file beside this one is older"),
        "newer_verdict": {
            "result": a.get("result"),
            "checks": a.get("n_checks"),
            "failing_checks": a.get("failing"),
            "unmeasurable": a.get("unmeasurable"),
            "lives_at": os.path.join(a["src"], "gate.json"),
            "written_at": a["gate_json"].get("mtime_iso"),
        },
        "why_refused": a["refusals"],
        "what_is_owed": (
            "rebuild the module and re-gate it. Neither the file beside this "
            "one NOR the newer verdict describes the module source as it "
            "stands now."),
        "do_not": (
            "do not promote the newer verdict by hand to make this go away. "
            "It was refused because its blend predates the current source, "
            "and promoting a stale report INTO the canonical slot is strictly "
            "worse than leaving the canonical slot stale -- it launders the "
            "staleness through a fresh mtime."),
        "written_by": os.path.abspath(__file__),
        "written_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "source_py_now": a.get("source_py"),
        "blend_the_newer_verdict_read": a.get("blend"),
    }
    if apply:
        os.makedirs(dst, exist_ok=True)
        with open(os.path.join(dst, "PENDING_REGATE.json"), "w") as fh:
            json.dump(note, fh, indent=1)
    return note


def promote(a, apply=False):
    """Move the stale set aside, copy the complete fresh set in, stamp it."""
    if a["refusals"]:
        refuse(a, apply=apply)
        return {"module": a["module"], "promoted": False,
                "why": a["refusals"], "pending_regate_written": True}
    src, dst = a["src"], a["dst"]
    day = (a["gate_json"]["mtime_iso"] or "")[:10]
    sup = os.path.join(dst, "_superseded_%s" % day)

    moved, copied = [], []
    if apply:
        os.makedirs(dst, exist_ok=True)
    for row in a["canonical_now"]:
        if row["action"] != "supersede":
            continue
        moved.append(row["name"])
        if apply:
            os.makedirs(sup, exist_ok=True)
            shutil.move(os.path.join(dst, row["name"]),
                        os.path.join(sup, row["name"]))

    def cp(s, d):
        copied.append(os.path.basename(d))
        if apply:
            shutil.copy2(s, d)

    cp(os.path.join(src, "gate.json"), os.path.join(dst, "gate.json"))
    for s, d in (("run.log", "gate_run.log"), ("build.log", "build.log")):
        if os.path.exists(os.path.join(src, s)):
            cp(os.path.join(src, s), os.path.join(dst, d))

    wpng = a["witness"].get("png", {})
    if wpng.get("status") == "OK":
        name = ("witness.png" if wpng.get("verdict_frame")
                else "witness_OVERWRITTEN_by_later_run.png")
        cp(wpng["path"], os.path.join(dst, name))
    wspec = a["witness"].get("spec", {})
    if wspec.get("status") == "OK":
        name = ("witness_spec.json" if wspec.get("verdict_frame")
                else "witness_spec_OVERWRITTEN_by_later_run.json")
        cp(wspec["path"], os.path.join(dst, name))

    # the pinned run, quarantined and labelled
    if a.get("pinned"):
        pd = os.path.join(dst, "diagnostic_pinned_subject")
        if apply:
            os.makedirs(pd, exist_ok=True)
        for n in ("gate_pinned.json", "run_pinned.log"):
            if os.path.exists(os.path.join(src, n)):
                cp(os.path.join(src, n), os.path.join(pd, n))
        if apply:
            with open(os.path.join(pd, "README.txt"), "w") as fh:
                fh.write(
                    "THIS IS NOT THE VERDICT.\n\n"
                    "A pinned run re-gates the item with --subject forced to "
                    "whatever the BEFORE witness framed, so that an A/B pair "
                    "can be shown to have looked at the same object. It is a "
                    "diagnostic. The pipeline that produced it says so in "
                    "as many words -- work/r2038/run_module2.sh line 105:\n"
                    "    '(pinned run -- NOT the verdict)'\n\n"
                    "The verdict for this item is ../gate.json.\n"
                    "This run says: %s%s\n"
                    % (a["pinned"]["result"],
                       ("  (it DISAGREES with the verdict, which is %s -- "
                        "that disagreement is about WHICH INSTANCE was framed, "
                        "not about whether the item passes)" % a["result"])
                       if not a["pinned"]["agrees_with_verdict"] else ""))
            copied.append("diagnostic_pinned_subject/README.txt")

    # ---- PROVENANCE.json: what was promoted, from where, and what it is --
    prov = {
        "PROMOTION": {
            "what": "the 2026-08-02 rebuilt gate report for '%s', promoted "
                    "into its canonical slot" % a["module"],
            "promoted_at_iso": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "promoted_from": src,
            "promoted_by": os.path.abspath(__file__),
            "verdict": a["result"],
            "checks_in_this_gate": a["n_checks"],
            "failing_checks": a["failing"],
            "unmeasurable": a["unmeasurable"],
            "replaced": a["canonical_gate_json"],
            "superseded_into": os.path.basename(sup) if moved else None,
            "superseded_files": moved,
            "copied_in": copied,
        },
        "STAMP_KIND": {
            "value": "RETROFIT_AT_PROMOTION",
            "read_this": (
                "gate.json itself carries NO provenance stamp: it was written "
                "on 2026-08-02, before tools/provenance.py existed. The hashes "
                "below were taken at PROMOTION time, not at MEASUREMENT time, "
                "and are therefore evidence that the file on disk today is the "
                "file that was promoted -- NOT evidence of what the gate read "
                "four hours before that. What supports the latter is the "
                "ORDERING below, which is weaker than a hash and is stated as "
                "such. Gate reports produced from now on carry a real "
                "at-run-time stamp; run "
                "`python3 tools/provenance.py --verify <report>` on them."),
        },
        "ORDERING_EVIDENCE": {
            "claim": "this report describes the current module source",
            "module_source_py": a["source_py"],
            "blend_the_gate_read": a["blend"],
            "gate_json": a["gate_json"],
            "holds": ("source %s  <  blend %s  <  gate.json %s"
                      % (a["source_py"].get("mtime_iso"),
                         a["blend"].get("mtime_iso"),
                         a["gate_json"].get("mtime_iso"))),
            "what_it_does_not_prove": (
                "mtime ordering cannot prove the blend was BUILT from that "
                "source, only that it was written after it. A build that "
                "silently failed and left an older blend in place would "
                "satisfy this test. The build.log promoted alongside is the "
                "check on that."),
        },
        "WITNESS": a["witness"],
        "PINNED_DIAGNOSTIC": a.get("pinned"),
        "WARNINGS": a["warnings"],
    }
    if apply:
        with open(os.path.join(dst, "PROVENANCE.json"), "w") as fh:
            json.dump(prov, fh, indent=1)
    return {"module": a["module"], "promoted": True, "verdict": a["result"],
            "moved": len(moved), "copied": len(copied),
            "copied_names": copied, "superseded_names": moved,
            "warnings": a["warnings"]}


def audit(apply=False):
    """Re-measure every promoted report's inputs against the disk NOW.

    A promotion is a statement about a moment. The moment passes. During the
    2026-08-03 promotion an R2-057 socket sweep was concurrently editing
    `world/items/*.py`, and four modules' sources moved WITHIN TEN MINUTES of
    their reports being promoted. That is not a race to be engineered away --
    it is the normal condition of a project with several agents in it, and the
    only real defence is that the drift is VISIBLE.

    So this re-reads each `PROVENANCE.json`, re-hashes the module source and
    the blend the gate read, and where they have moved it writes
    `SOURCE_MOVED.json` beside the verdict. It never rolls a promotion back:
    the promoted verdict is still the best measurement anyone has, and
    replacing it with an older, weaker one to satisfy tidiness would be the
    original defect in reverse. It marks, and it says what is owed.
    """
    rows = []
    for pj in sorted(__import__("glob").glob(os.path.join(DST_ROOT,
                                                          "*/PROVENANCE.json"))):
        d = os.path.dirname(pj)
        mod = os.path.basename(d)
        P = json.load(open(pj))
        oe = P.get("ORDERING_EVIDENCE") or {}
        moved = []
        # The witness .blend is NOT copied into the canonical slot -- it is
        # 4-8 MB per module and gate.json already names it. But "named" is not
        # "safe": `render/gate_witness/armco_w_beam/witness.blend` was
        # overwritten 103 seconds after the verdict that used it. So its hash
        # at promotion time is re-checked here, and a replacement is reported
        # rather than followed silently.
        wit = P.get("WITNESS") or {}
        srcs = [("module_source_py", "module source", oe.get("module_source_py")),
                ("blend_the_gate_read", "the blend the gate read",
                 oe.get("blend_the_gate_read")),
                ("witness_blend", "the witness .blend gate.json points at",
                 wit.get("blend"))]
        for key, label, was in srcs:
            was = was or {}
            if was.get("status") != "OK":
                continue
            now = facts(was["path"], was.get("role"))
            if now["status"] != "OK":
                moved.append({"what": label, "path": was["path"],
                              "change": now["status"]})
            elif now["sha256"] != was["sha256"]:
                moved.append({"what": label, "path": was["path"],
                              "change": "CONTENT CHANGED",
                              "was_mtime": was["mtime_iso"],
                              "now_mtime": now["mtime_iso"],
                              "was_sha256": was["sha256"][:16],
                              "now_sha256": now["sha256"][:16]})
        rows.append({"module": mod, "moved": moved})
        marker = os.path.join(d, "SOURCE_MOVED.json")
        if not moved:
            if apply and os.path.exists(marker):
                os.remove(marker)
            continue
        note = {
            "STATUS": "SOURCE_MOVED_SINCE_PROMOTION",
            "one_line": ("the verdict beside this file is the best measurement "
                         "anyone has, and it no longer describes the module "
                         "source as it stands"),
            "verdict_beside_this": P["PROMOTION"].get("verdict"),
            "promoted_at": P["PROMOTION"].get("promoted_at_iso"),
            "what_moved": moved,
            "what_is_owed": ("rebuild and re-gate. Until then read the verdict "
                             "as provisional."),
            "why_it_was_not_rolled_back": (
                "the artefact it replaced was a 4-check verdict from 2026-07-29 "
                "that could not measure surface relief at all. Reverting to it "
                "to make this marker go away would be the original defect in "
                "reverse -- trading a verdict that is slightly out of date for "
                "one that is wrong."),
            "detected_by": os.path.abspath(__file__),
            "detected_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        if apply:
            with open(marker, "w") as fh:
                json.dump(note, fh, indent=1)
    n = sum(1 for r in rows if r["moved"])
    for r in rows:
        if r["moved"]:
            print("MOVED  %-28s %s" % (r["module"],
                                       "; ".join(m["what"] for m in r["moved"])))
    print("\n%s -- %d of %d promoted reports have drifted from their inputs"
          % ("APPLIED" if apply else "DRY RUN (nothing changed)", n, len(rows)))
    return rows


def selftest(verbose=True):
    """Plant each fault this tool exists to catch, and confirm it FIRES.

    The two refusals below both fired for real during the 2026-08-03 run --
    `marshal_post_column`'s source was edited by a concurrent agent 8 hours
    after its gate ran, and the witness frames of `armco_w_beam` and
    `catch_fence_post` had been overwritten by later diagnostic runs 103 and 62
    seconds after their verdicts. But a check that has only ever fired by
    accident has not been SHOWN to work, and this tool will be run again for
    every pending re-gate. So the faults are reproduced here on purpose, on
    synthetic files, and the negative control -- a clean report -- must pass.
    """
    import tempfile
    global SRC_ROOT, DST_ROOT, SRC_PY
    keep = (SRC_ROOT, DST_ROOT, SRC_PY)
    ok, fails = [], []

    def chk(name, cond, detail):
        ok.append(name)
        if not cond:
            fails.append(name)
        if verbose:
            print("  %-40s %-4s %s" % (name, "PASS" if cond else "FAIL", detail))

    def build(tmp, mod, src_dt, blend_dt, gate_dt, png_dt):
        """One synthetic module. Times are offsets in seconds from now."""
        now = time.time()
        SRC_PY_D = os.path.join(tmp, "src")
        SRC_D = os.path.join(tmp, "gate", mod)
        DST_D = os.path.join(tmp, "items", mod)
        WIT = os.path.join(tmp, "wit", mod)
        for d in (SRC_PY_D, SRC_D, DST_D, WIT):
            os.makedirs(d, exist_ok=True)
        py = os.path.join(SRC_PY_D, mod + ".py")
        bl = os.path.join(tmp, mod + "_test.blend")
        png = os.path.join(WIT, "witness.png")
        spec = os.path.join(WIT, "witness_spec.json")
        for p, dt, body in ((py, src_dt, "# module\n"), (bl, blend_dt, "BLEND"),
                            (png, png_dt, "PNG"), (spec, png_dt, "{}")):
            with open(p, "w") as fh:
                fh.write(body)
            os.utime(p, (now + dt, now + dt))
        rep = {"item": mod, "checks": {c: True for c in
                                       ("no_external_assets", "material_depth",
                                        "geometry_resolves_at_distance",
                                        "per_instance_variation",
                                        "witness_frame_valid",
                                        "surface_microstructure",
                                        "relief_reads_as_lip_and_shade",
                                        "silhouette_departs_from_analytic")},
               "witness": {"png": png, "spec": spec, "blend": None},
               "result": "ITEM_ACCEPTED"}
        gj = os.path.join(SRC_D, "gate.json")
        with open(gj, "w") as fh:
            json.dump(rep, fh)
        with open(os.path.join(SRC_D, "run.log"), "w") as fh:
            fh.write('00:00.1  blend | Read blend: "%s"\n' % bl)
        os.utime(gj, (now + gate_dt, now + gate_dt))
        return SRC_PY_D, os.path.join(tmp, "gate"), os.path.join(tmp, "items")

    tmp = tempfile.mkdtemp(prefix="promote_selftest_")
    try:
        # --- NEGATIVE CONTROL: source < blend < gate, frame before verdict ---
        SRC_PY, SRC_ROOT, DST_ROOT = build(
            os.path.join(tmp, "clean"), "m_clean",
            src_dt=-300, blend_dt=-200, gate_dt=-100, png_dt=-150)
        a = assess("m_clean")
        chk("negative_control_clean_report_promotes",
            not a["refusals"] and not a["warnings"],
            "refusals=%s warnings=%s" % (a["refusals"], a["warnings"]))

        # --- POSITIVE 1: the module source was edited AFTER the blend --------
        SRC_PY, SRC_ROOT, DST_ROOT = build(
            os.path.join(tmp, "srcmoved"), "m_srcmoved",
            src_dt=-50, blend_dt=-200, gate_dt=-100, png_dt=-150)
        a = assess("m_srcmoved")
        chk("positive_control_source_moved_REFUSES",
            any("PREDATES the module source" in r for r in a["refusals"]),
            a["refusals"] or "NO REFUSAL -- the check is blind")
        r = promote(a, apply=False)
        chk("refused_report_is_not_promoted", r["promoted"] is False,
            "promoted=%s" % r["promoted"])

        # --- POSITIVE 2: THE WITNESS FRAME WAS OVERWRITTEN AFTER THE VERDICT -
        #     This is the trap in its purest form: the verdict is perfectly
        #     valid, every ordering check passes, and the picture shipped with
        #     it is of something else.
        SRC_PY, SRC_ROOT, DST_ROOT = build(
            os.path.join(tmp, "frame"), "m_frame",
            src_dt=-300, blend_dt=-200, gate_dt=-100, png_dt=-10)
        a = assess("m_frame")
        chk("positive_control_overwritten_frame_FIRES",
            a["witness"]["png"].get("verdict_frame") is False
            and bool(a["warnings"]),
            a["warnings"] or "NO WARNING -- a stale frame would ship as fresh")
        chk("overwritten_frame_still_promotes_under_honest_name",
            not a["refusals"],
            "the verdict is sound; only its illustration is not, so it is "
            "renamed rather than withheld")
        r = promote(a, apply=False)
        chk("overwritten_frame_renamed",
            "witness_OVERWRITTEN_by_later_run.png" in r["copied_names"]
            and "witness.png" not in r["copied_names"],
            "copied set = %s" % r["copied_names"])

        # --- POSITIVE 3: gate.json older than the blend it claims to read ----
        SRC_PY, SRC_ROOT, DST_ROOT = build(
            os.path.join(tmp, "backwards"), "m_backwards",
            src_dt=-300, blend_dt=-50, gate_dt=-100, png_dt=-150)
        a = assess("m_backwards")
        chk("positive_control_gate_predates_blend_REFUSES",
            any("predates the blend" in r for r in a["refusals"]),
            a["refusals"] or "NO REFUSAL -- the check is blind")
    finally:
        SRC_ROOT, DST_ROOT, SRC_PY = keep
        shutil.rmtree(tmp, ignore_errors=True)

    if verbose:
        print("\n  %d/%d checks pass%s"
              % (len(ok) - len(fails), len(ok),
                 "" if not fails else "   FAILED: " + ", ".join(fails)))
    return not fails


def main(argv):
    p = argparse.ArgumentParser()
    p.add_argument("--selftest", action="store_true",
                   help="plant each fault this tool catches and confirm it "
                        "fires; touches nothing real")
    p.add_argument("--audit", action="store_true",
                   help="re-measure every promoted report's inputs against "
                        "disk now and mark the ones that have drifted; exits "
                        "non-zero if any has. Run this after ANY change to "
                        "world/items/.")
    p.add_argument("--apply", action="store_true",
                   help="actually move and copy. Default is a dry run.")
    p.add_argument("--only", default=None, help="comma-separated modules")
    p.add_argument("--json", default=os.path.join(
        R2, "work", "provenance", "promotion.json"))
    a = p.parse_args(argv)
    if a.selftest:
        return 0 if selftest() else 1
    if a.audit:
        rows = audit(apply=a.apply)
        return 1 if any(r["moved"] for r in rows) else 0

    mods = sorted(n for n in os.listdir(SRC_ROOT)
                  if os.path.isdir(os.path.join(SRC_ROOT, n)))
    if a.only:
        want = {x.strip() for x in a.only.split(",")}
        mods = [m for m in mods if m in want]

    rows, results = [], []
    for m in mods:
        s = assess(m)
        rows.append(s)
        results.append(promote(s, apply=a.apply))

    print("%-26s %-6s %-16s %-16s %s"
          % ("module", "chks", "canonical was", "now", "note"))
    for s, r in zip(rows, results):
        was = s.get("canonical_gate_json") or {}
        wtxt = "%s/%s" % (str(was.get("result", "-")).replace("ITEM_", ""),
                          was.get("n_checks", "-"))
        now = "%s/%d" % (str(s.get("result", "-")).replace("ITEM_", ""),
                         s.get("n_checks", 0))
        note = ""
        if not r["promoted"]:
            note = "REFUSED: " + "; ".join(r["why"])
        elif s["warnings"]:
            note = "; ".join(s["warnings"])
        flip = " <-- FLIPPED" if (was.get("result") and
                                  was.get("result") != s.get("result")) else ""
        print("%-26s %-6d %-16s %-16s %s%s"
              % (s["module"], s.get("n_checks", 0), wtxt, now, note, flip))

    os.makedirs(os.path.dirname(a.json), exist_ok=True)
    with open(a.json, "w") as fh:
        json.dump({"applied": a.apply, "assessed": rows, "results": results},
                  fh, indent=1, default=str)
    print("\n%s -- %d promoted, %d refused.  detail: %s"
          % ("APPLIED" if a.apply else "DRY RUN (nothing changed)",
             sum(1 for r in results if r["promoted"]),
             sum(1 for r in results if not r["promoted"]), a.json))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
