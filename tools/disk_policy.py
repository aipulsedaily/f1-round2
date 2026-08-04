"""THE WAVE-2 DISK POLICY.  Census, `.blend1` sweep, and the guarded test-blend purge.

    python3 tools/disk_policy.py census
    python3 tools/disk_policy.py selftest            # the guard's controls, both arms
    python3 tools/disk_policy.py blend1  --scope items [--apply]
    python3 tools/disk_policy.py purge   [--apply]

WHY THIS FILE EXISTS
--------------------
`docs/WAVE2-SCOPE.md` sec 5.5 measures the wave against the disk and finds it does
not fit:

    world/items/   36 GB for 32 items  =  1.125 GB per item (test blend + .blend1)
    113 proposed   x 1.125 GB          =  127 GB      free ~123 GB

and then says, in its own words, *"Wave 2 needs a disk policy before it needs an
agent"*, naming two measures and recording that **neither exists**.  This is both
of them.  The scope's own estimate is not quoted here; every number this tool
prints is `os.stat` and `os.statvfs` at the moment it ran.

THE TWO MEASURES, AND WHY THEY ARE DIFFERENT IN KIND
-----------------------------------------------------
1. `blend1`  -- delete Blender's `.blend1` overwrite backups.  A ONE-OFF reclaim.
   A `.blend1` is the previous contents of the file beside it; Blender writes one
   on every save and nothing on this project has ever read one.

2. `purge`   -- delete an item's `_test.blend` once the record that REPLACES it is
   complete and provably about it.  A STEADY-STATE mechanism: it reclaims almost
   nothing today (see the guard results) and is what keeps the wave's footprint
   flat while 113 items are built.  The distinction matters for planning: measure
   1 buys the wave its headroom, measure 2 stops it filling back up.

MEASURE 1 IS NOT THE FREE LUNCH THE SCOPE TAKES IT FOR.  MEASURED, TWICE:
--------------------------------------------------------------------------
A blanket `find -name '*.blend1' -delete` is correct for 155 of this tree's 172
backups and SILENTLY DESTRUCTIVE for 17 of them, in two unrelated ways:

  * **5 backups have no sibling `.blend` at all** -- the backup IS the file.
    `world/items/access_road_slab_draft.blend1` (0.27 GB),
    `work/r2116/scratch/gravel_bed_surface_ctl.blend1` (0.97 GB),
    `work/gru/probe0.blend1`, and two in `render/exposure_cal/`.

  * **12 `world/items/*_test.blend1` are the ONLY remaining copy of the artefact
    a PUBLISHED gate verdict describes.**  MEASURED by sha256 against the
    `provenance.inputs[role=blend]` hash in `render/items/<id>/gate.json`:
    the live `_test.blend` has moved underneath the report (sec 7.4 measures 19 of
    31 in that state) and the bytes the report was computed on survive only in
    the backup.  Six of the twelve carry an ACCEPT: `armco_post`, `crew_figure`,
    `pit_wall_unit`, `team_truck_trailer`, `terrain_ground`, `timing_stand`.
    Deleting those turns a re-checkable verdict into an unfalsifiable claim --
    R2-118's shape, arrived at by housekeeping instead of by re-analysis.

So the sweep carries its own two guards, `B1` and `B2` below, and both have
controls in `selftest`.  The safe reclaim is smaller than the naive one and is
printed as a measurement, never as the naive total.

AND THE SWEEP IS THE WRONG FIX ANYWAY -- `.blend1` IS ONE PREFERENCE
---------------------------------------------------------------------
MEASURED, both arms in one `--factory-startup` run:

    save_version = 1  (THE FACTORY DEFAULT, i.e. what every item build uses)
        save A.blend twice  ->  ['A.blend', 'A.blend1']
    save_version = 0
        save B.blend twice  ->  ['B.blend']

`bpy.context.preferences.filepaths.save_version` is **1** under
`--factory-startup`, so every re-save of a 2.3 GB test blend silently writes a
2.3 GB duplicate.  That is where `world/items/`'s 19.2 GB of backups came from and
it is the whole of the difference between the scope's per-item figure and the
measured one:

    scope sec 5.5   36 GB / 32 items          = 1.125 GB/item   (includes .blend1)
    MEASURED        test blend + witness + records, NO .blend1
                    median 472 MB   mean 688 MB   p90 1220 MB   max 4097 MB

**113 x 688 MB = 76 GB, not 127 GB.**  A wave-2 build wrapper that sets
`save_version = 0` before it saves removes the entire class at source, costs one
line, and needs no sweep, no guard and no judgement call about which backup is
load-bearing.  Sweeping is what you do to the 19.2 GB that already exist; setting
the preference is what stops the next 113 items making 76 GB more.

THE PURGE IS SAFE BY CONSTRUCTION, AND THE CONSTRUCTION IS THE POINT
---------------------------------------------------------------------
Deleting a test blend is only safe if what is left behind -- the gate report, the
printed log, the witness pair and the macro -- is a COMPLETE record OF THAT BLEND.
So the guard does not ask "does a report exist"; it asks "does this report
describe the bytes I am about to delete", and it answers with sha256, not mtime.

    G1 report_exists          render/items/<id>/gate.json exists and decodes
    G2 printed_line           render/items/<id>/gate_run.log carries a
                              `STAGE RESULT:` line.  R2-116/R2-117: the JSON
                              `result` field is TWO-VALUED and there are THREE
                              outcomes, so a verdict read from it is not a
                              verdict.  This tool NEVER reads `result` except to
                              report that it disagrees.
    G3 verdict_accepted       the PRINTED verdict is ITEM_ACCEPTED.
                              ITEM_REJECTED and ITEM_UNMEASURABLE both keep the
                              blend: one is "fix the item", the other is "fix the
                              gate", and both need the artefact.
    G4 report_is_about_this   provenance inputs[role=blend].sha256 == sha256 of
                              the blend on disk.  This is the staleness arm and
                              it is CONTENT-addressed.  R2-119 measures 31 of 32
                              blends stale by mtime while `own_module_newer`
                              scores all 32 clean -- an mtime rule is exactly the
                              rule that was already blind here.
    G5 macro_present          render/items/<id>/macro.png exists,
    G6 macro_at_4k            at 3840x2160 (campaign deliverable 3), and
    G7 witness_pair           witness.png + witness_spec.json both exist, so the
                              verdict stays reproducible after the blend is gone.
    G8 report_is_about_this_item
                              the report's own `item` field, and the log's own
                              `>> item <id>` line, agree with the DIRECTORY the
                              report is filed under.  Added after this tool's
                              first run: `render/items/spectator_crowd/gate.json`
                              carries `"item": "spectator_seated"` and its
                              `gate_run.log` opens `spectator_crowd_test.blend`,
                              prints `>> item spectator_seated`, selects
                              collection `ITEM_spectator_crowd`, scores
                              `spectator_seated`'s witness PNG via `--from-png`,
                              and prints `STAGE RESULT: ITEM_ACCEPTED`.  One run,
                              three items' identities.  Without G8 this tool would
                              have purged `spectator_crowd_test.blend` on the
                              strength of an ACCEPT about a different item as soon
                              as somebody rendered it a macro.  Meanwhile
                              `spectator_seated` -- the ONLY item of the 32 with a
                              macro on disk -- has NO `gate_run.log` at all: its
                              printed evidence lives in `spectator_crowd`'s
                              directory.  R2-121's mechanism, one layer out.

    INFO (not blocking) stale_closure -- itemkit.py / world_contract.py sha256
    recorded in the report against those files now.  A blend stale against a
    frozen input must be REBUILT (sec 7.3), so keeping it buys nothing; but the
    ACCEPT it carries is void, so it is reported next to the verdict and never
    silently.

`selftest` runs five controls in a throwaway sandbox -- four that MUST refuse and
one that MUST accept -- and exits non-zero if any arm disagrees.  A guard that has
only ever been shown accepting is not a guard.

WHAT THIS TOOL WILL NOT DELETE, EVER
-------------------------------------
`render/film*.blend` and `render/world/assembly/**/assembly*.blend` are refused by
path at the lowest level, in `_forbidden()`, whatever scope or flag is passed.
All 15 films and 8 assemblies are deliberate; `film10` is the assembly6 control
whose 27-finding audit FAIL is what makes every other film's PASS non-vacuous.
The film `.blend1` backups are a large reclaim and are NOT taken by default: the
`film-backups` scope exists so the number can be measured, and it refuses to
apply without `--i-have-been-told-films-may-lose-their-backups`.
"""
import os, sys, json, time, argparse, hashlib, shutil, tempfile, re

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ITEMS_DIR   = os.path.join(R2, "world", "items")
REPORTS_DIR = os.path.join(R2, "render", "items")
RECEIPTS    = os.path.join(R2, "work", "w2_0")

MACRO_W, MACRO_H = 3840, 2160

BLEND1_SCOPES = {
    # scope name      -> (root, recurse)
    "items":          (os.path.join(R2, "world", "items"), True),
    "witness":        (os.path.join(R2, "render", "gate_witness"), True),
    "world":          (os.path.join(R2, "world"), False),
    "work":           (os.path.join(R2, "work"), True),
    "render-misc":    (os.path.join(R2, "render"), True),   # excludes film*.blend1
    "film-backups":   (os.path.join(R2, "render"), False),  # ONLY film*.blend1
}


# ---------------------------------------------------------------- protections

def _forbidden(path):
    """Paths this tool refuses to unlink under any scope, flag or mode.

    Returns a reason string, or None.  Checked immediately before every unlink,
    not only at selection time, so a bug in scope selection cannot reach a film.
    """
    b = os.path.basename(path)
    if b.endswith(".blend"):
        return "a .blend is never deleted by this tool (only .blend1 backups)"
    if re.match(r"^film.*\.blend1$", b) and not _FILM_BACKUPS_AUTHORISED[0]:
        return "render/film*.blend1 needs --i-have-been-told-films-may-lose-their-backups"
    if re.match(r"^assembly.*\.blend1?$", b):
        return "assembly blends and their backups are never deleted"
    return None


_FILM_BACKUPS_AUTHORISED = [False]


def _statvfs_free():
    s = os.statvfs(R2)
    return s.f_bavail * s.f_frsize


def _sha256(path, chunk=1 << 22):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def _gb(n):
    return n / (1024.0 ** 3)


def _receipt(name, payload):
    os.makedirs(RECEIPTS, exist_ok=True)
    p = os.path.join(RECEIPTS, "%s_%s.json" % (name, time.strftime("%Y%m%dT%H%M%S")))
    with open(p, "w") as f:
        json.dump(payload, f, indent=1)
    return p


# ---------------------------------------------------------------- census

def cmd_census(a):
    rows = []
    for dp, dn, fn in os.walk(R2):
        if os.sep + ".git" in dp:
            continue
        for f in fn:
            if f.endswith((".blend", ".blend1")):
                p = os.path.join(dp, f)
                try:
                    rows.append((p, os.path.getsize(p)))
                except OSError:
                    pass

    def tot(pred):
        sel = [r for r in rows if pred(r[0])]
        return len(sel), sum(r[1] for r in sel)

    free = _statvfs_free()
    print("FREE ON /                                  %10.2f GB" % _gb(free))
    print()
    print("%-46s %6s %12s" % ("category", "files", "GB"))
    cats = [
        ("world/items  *_test.blend",
         lambda p: p.startswith(ITEMS_DIR) and p.endswith("_test.blend")),
        ("world/items  *.blend1",
         lambda p: p.startswith(ITEMS_DIR) and p.endswith(".blend1")),
        ("world/items  other .blend",
         lambda p: p.startswith(ITEMS_DIR) and p.endswith(".blend")
                   and not p.endswith("_test.blend")),
        ("render/film*.blend        (PROTECTED)",
         lambda p: re.match(r"^film.*\.blend$", os.path.basename(p))
                   and os.path.dirname(p) == os.path.join(R2, "render")),
        ("render/film*.blend1       (ask first)",
         lambda p: re.match(r"^film.*\.blend1$", os.path.basename(p))
                   and os.path.dirname(p) == os.path.join(R2, "render")),
        ("assembly*.blend           (PROTECTED)",
         lambda p: re.match(r"^assembly.*\.blend$", os.path.basename(p))),
        ("render/gate_witness *.blend1",
         lambda p: p.startswith(os.path.join(R2, "render", "gate_witness"))
                   and p.endswith(".blend1")),
        ("world/verify_*.blend1",
         lambda p: os.path.dirname(p) == os.path.join(R2, "world")
                   and p.endswith(".blend1")),
        ("work/**/*.blend1",
         lambda p: p.startswith(os.path.join(R2, "work")) and p.endswith(".blend1")),
    ]
    for label, pred in cats:
        n, b = tot(pred)
        print("%-46s %6d %12.3f" % (label, n, _gb(b)))
    n, b = tot(lambda p: p.endswith(".blend1"))
    print("%-46s %6d %12.3f" % ("-- ALL .blend1 anywhere", n, _gb(b)))
    n, b = tot(lambda p: True)
    print("%-46s %6d %12.3f" % ("-- ALL .blend + .blend1", n, _gb(b)))
    return 0


# ---------------------------------------------------------------- blend1 sweep

def _collect_blend1(scope):
    root, recurse = BLEND1_SCOPES[scope]
    out = []
    if recurse:
        walker = os.walk(root)
    else:
        walker = [(root, [], os.listdir(root))]
    for dp, dn, fn in walker:
        if os.sep + ".git" in dp:
            continue
        for f in fn:
            if not f.endswith(".blend1"):
                continue
            p = os.path.join(dp, f)
            if not os.path.isfile(p):
                continue
            isfilm = (re.match(r"^film.*\.blend1$", f)
                      and os.path.dirname(p) == os.path.join(R2, "render"))
            if scope == "film-backups" and not isfilm:
                continue
            if scope == "render-misc" and isfilm:
                continue
            out.append(p)
    return sorted(out)


def published_blend_hashes(reports_dir=REPORTS_DIR):
    """{bytes: {sha256: item}} for every blend a PUBLISHED gate report describes.

    Keyed on size first so `B2` hashes only the handful of backups whose length
    could possibly match; a size mismatch is already proof of a different file.
    """
    idx = {}
    if not os.path.isdir(reports_dir):
        return idx
    for item in sorted(os.listdir(reports_dir)):
        p = os.path.join(reports_dir, item, "gate.json")
        if not os.path.exists(p):
            continue
        try:
            with open(p) as f:
                rep = json.load(f)
        except Exception:
            continue
        rec = _recorded_blend(rep)
        if rec and rec.get("sha256") and rec.get("bytes") is not None:
            idx.setdefault(rec["bytes"], {})[rec["sha256"]] = item
    return idx


def blend1_guard(path, published):
    """Why this `.blend1` may NOT be deleted, or None.

    B1  no sibling `.blend` -- the backup IS the file, not a backup of one.
    B2  its bytes are the subject of a published gate verdict and the live
        `.blend` no longer is.  Deleting it makes that verdict unfalsifiable.
    """
    sibling = path[:-1]
    if not os.path.exists(sibling):
        return "B1_no_sibling_blend__this_backup_is_the_only_copy"
    sz = os.path.getsize(path)
    cand = published.get(sz)
    if cand:
        if _sha256(path) in cand:
            item = cand[_sha256(path)]
            try:
                live_is_it = (os.path.getsize(sibling) == sz
                              and _sha256(sibling) == _sha256(path))
            except OSError:
                live_is_it = False
            if not live_is_it:
                return ("B2_sole_carrier_of_the_blend_%s_verdict_describes" % item)
    return None


def cmd_blend1(a):
    if a.scope == "film-backups":
        _FILM_BACKUPS_AUTHORISED[0] = a.i_have_been_told_films_may_lose_their_backups
    files = _collect_blend1(a.scope)
    published = published_blend_hashes()
    rows, blocked = [], []
    for p in files:
        why = _forbidden(p) or blend1_guard(p, published)
        sz = os.path.getsize(p)
        row = {"path": os.path.relpath(p, R2), "bytes": sz,
               "companion_blend_exists": os.path.exists(p[:-1])}
        if why:
            row["refused"] = why
            blocked.append(row)
        else:
            rows.append(row)

    sel = sum(r["bytes"] for r in rows)
    naive = sel + sum(r["bytes"] for r in blocked)
    print("scope %-14s  files %3d  %8.3f GB naive" % (a.scope, len(files), _gb(naive)))
    print("   SAFE TO DELETE   %3d  %8.3f GB" % (len(rows), _gb(sel)))
    print("   REFUSED          %3d  %8.3f GB" % (len(blocked),
                                                 _gb(naive - sel)))
    for r in blocked:
        print("      %-58s %7.3f GB  %s" % (r["path"], _gb(r["bytes"]), r["refused"]))
    if not a.apply:
        print("   DRY RUN -- nothing deleted.  Re-run with --apply.")
        _receipt("blend1_dryrun_%s" % a.scope,
                 {"scope": a.scope, "safe": rows, "refused": blocked,
                  "naive_bytes": naive, "safe_bytes": sel})
        return 0

    free_before = _statvfs_free()
    deleted, freed = [], 0
    for r in rows:
        p = os.path.join(R2, r["path"])
        # re-checked immediately before unlink, not only at selection time, so a
        # bug in scope selection cannot reach a protected file
        why = _forbidden(p) or blend1_guard(p, published)
        if why:
            print("   REFUSED AT UNLINK %s: %s" % (r["path"], why))
            continue
        try:
            os.unlink(p)
            deleted.append(r)
            freed += r["bytes"]
        except OSError as e:
            print("   FAILED %s: %s" % (r["path"], e))
    free_after = _statvfs_free()

    print()
    print("DELETED           %d files" % len(deleted))
    print("sum of filesizes  %10.3f GB" % _gb(freed))
    print("statvfs free      %10.3f GB -> %10.3f GB   = %+.3f GB MEASURED"
          % (_gb(free_before), _gb(free_after), _gb(free_after - free_before)))
    p = _receipt("blend1_%s" % a.scope,
                 {"scope": a.scope, "deleted": deleted, "refused": blocked,
                  "sum_filesizes_bytes": freed,
                  "statvfs_free_before": free_before,
                  "statvfs_free_after": free_after,
                  "statvfs_delta_bytes": free_after - free_before})
    print("receipt           %s" % os.path.relpath(p, R2))
    return 0


# ---------------------------------------------------------------- the guard

VERDICT_RE = re.compile(r"STAGE RESULT:\s*(ITEM_[A-Z_]+)")
LOG_ITEM_RE = re.compile(r"^>>\s*item\s+(\S+)")


def printed_item(log_path):
    """The id the RUN said it was gating, off the log's own `>> item <id>` line."""
    if not os.path.exists(log_path):
        return None
    with open(log_path, "r", errors="replace") as f:
        for line in f:
            m = LOG_ITEM_RE.match(line.strip())
            if m:
                return m.group(1)
    return None


def printed_verdict(log_path):
    """The verdict OF THE RUN.  R2-116/R2-117: read the printed line, never the field.

    Returns (verdict, line_no) or (None, None).  The LAST such line wins, because a
    log is appended to and the last stage result is the run's.
    """
    if not os.path.exists(log_path):
        return None, None
    v, n = None, None
    with open(log_path, "r", errors="replace") as f:
        for i, line in enumerate(f, 1):
            m = VERDICT_RE.search(line)
            if m:
                v, n = m.group(1), i
    return v, n


def _png_size(path):
    """Width/height straight out of the PNG IHDR.  No image library."""
    try:
        with open(path, "rb") as f:
            head = f.read(24)
        if head[:8] != b"\x89PNG\r\n\x1a\n" or head[12:16] != b"IHDR":
            return None
        return (int.from_bytes(head[16:20], "big"),
                int.from_bytes(head[20:24], "big"))
    except OSError:
        return None


def _recorded_blend(report):
    for e in (report.get("provenance", {}) or {}).get("inputs", []) or []:
        if e.get("role") == "blend":
            return e
    return None


def _recorded_also(report, role):
    for e in (report.get("provenance", {}) or {}).get("also_hash", []) or []:
        if e.get("role") == role:
            return e
    return None


def evaluate(item, items_dir=ITEMS_DIR, reports_dir=REPORTS_DIR, r2=R2):
    """Decide whether `<item>_test.blend` may be deleted.  Pure; no side effects.

    Returns a dict with `purgeable` (bool), `refusals` (list of guard ids that
    failed) and every measurement the decision was taken on.
    """
    blend = os.path.join(items_dir, item + "_test.blend")
    rdir  = os.path.join(reports_dir, item)
    rep_p = os.path.join(rdir, "gate.json")
    log_p = os.path.join(rdir, "gate_run.log")

    out = {"item": item, "blend": blend,
           "blend_exists": os.path.exists(blend),
           "blend_bytes": os.path.getsize(blend) if os.path.exists(blend) else 0,
           "refusals": [], "notes": []}
    R = out["refusals"].append

    if not out["blend_exists"]:
        out["purgeable"] = False
        R("no_blend")               # nothing to purge; not an error
        return out

    # G1 -------------------------------------------------------------- report
    report = None
    if not os.path.exists(rep_p):
        R("G1_report_missing")
    else:
        try:
            with open(rep_p) as f:
                report = json.load(f)
        except Exception as e:
            R("G1_report_undecodable")
            out["notes"].append(str(e))
    out["report"] = rep_p if report is not None else None

    # G2 --------------------------------------------------------- printed line
    v, ln = printed_verdict(log_p)
    out["printed_verdict"] = v
    out["printed_verdict_line"] = ln
    out["json_result_field"] = (report or {}).get("result")
    if v is None:
        R("G2_no_printed_STAGE_RESULT")
        if out["json_result_field"]:
            out["notes"].append(
                "the JSON `result` field says %s -- R2-116/117: that field is "
                "two-valued for three outcomes and is NOT a verdict"
                % out["json_result_field"])
    else:
        if out["json_result_field"] and out["json_result_field"] != v:
            out["notes"].append(
                "JSON `result`=%s DISAGREES with the printed line %s (R2-117)"
                % (out["json_result_field"], v))
        # G3 ------------------------------------------------------- verdict
        if v != "ITEM_ACCEPTED":
            R("G3_verdict_%s" % v.replace("ITEM_", "").lower())

    # G4 ------------------------------------------- report describes THIS blend
    if report is not None:
        rec = _recorded_blend(report)
        if not rec or not rec.get("sha256"):
            R("G4_report_records_no_blend_sha")
        else:
            out["recorded_blend_bytes"] = rec.get("bytes")
            out["recorded_blend_sha256"] = rec["sha256"]
            if rec.get("bytes") is not None and rec["bytes"] != out["blend_bytes"]:
                # size alone is proof of a different file; skip the hash
                R("G4_report_is_stale_against_the_blend")
                out["notes"].append(
                    "report describes %d bytes, blend on disk is %d"
                    % (rec["bytes"], out["blend_bytes"]))
            else:
                have = _sha256(blend)
                out["blend_sha256"] = have
                if have != rec["sha256"]:
                    R("G4_report_is_stale_against_the_blend")
                    out["notes"].append("sha256 differs at equal size")

    # G5/G6 ------------------------------------------------------------ macro
    macro = os.path.join(rdir, "macro.png")
    out["macro"] = macro if os.path.exists(macro) else None
    if not os.path.exists(macro):
        R("G5_macro_missing")
    else:
        wh = _png_size(macro)
        out["macro_px"] = wh
        if wh != (MACRO_W, MACRO_H):
            R("G6_macro_not_at_gate_resolution")

    # G7 --------------------------------------------------------- witness pair
    if report is not None:
        w = report.get("witness") or {}
        png, spec = w.get("png"), w.get("spec")
        ok = bool(png and os.path.exists(png)) and bool(spec and os.path.exists(spec))
        out["witness_png"], out["witness_spec"] = png, spec
        if not ok:
            R("G7_witness_pair_incomplete")
    else:
        R("G7_witness_pair_incomplete")

    # G8 ------------------------------------- the report is about THIS item id
    said = printed_item(log_p)
    out["log_says_item"] = said
    out["report_says_item"] = (report or {}).get("item")
    for src, val in (("report", out["report_says_item"]), ("log", said)):
        if val is not None and val != item:
            R("G8_report_is_about_%s_not_%s" % (val, item))
            out["notes"].append(
                "the %s filed under render/items/%s/ says it is about %r "
                "(R2-121: a report filed under the wrong id is worse than a "
                "missing one, because every consumer keys on the directory)"
                % (src, item, val))

    # INFO ------------------------------------------------------ stale closure
    if report is not None:
        stale = []
        for role, path in (("itemkit", os.path.join(r2, "world", "itemkit.py")),
                           ("world_contract",
                            os.path.join(r2, "world", "world_contract.py"))):
            rec = _recorded_also(report, role)
            if rec and rec.get("sha256") and os.path.exists(path):
                if _sha256(path) != rec["sha256"]:
                    stale.append(role)
        out["stale_closure"] = stale
        if stale:
            out["notes"].append(
                "INFO not blocking: blend predates %s (R2-119) -- the ACCEPT it "
                "carries is void and the item must be rebuilt" % ", ".join(stale))

    out["purgeable"] = not out["refusals"]
    return out


def cmd_purge(a):
    items = sorted(f[:-len("_test.blend")] for f in os.listdir(ITEMS_DIR)
                   if f.endswith("_test.blend"))
    if a.item:
        items = [i for i in items if i in a.item]

    rows = [evaluate(i) for i in items]
    ok  = [r for r in rows if r["purgeable"]]
    no  = [r for r in rows if not r["purgeable"]]

    print("%-32s %10s  %-16s %s" % ("item", "MB", "printed", "verdict"))
    for r in rows:
        print("%-32s %10.1f  %-16s %s"
              % (r["item"], r["blend_bytes"] / 1e6,
                 (r["printed_verdict"] or "-").replace("ITEM_", ""),
                 "PURGE" if r["purgeable"] else "KEEP  " + ",".join(r["refusals"])))
    print()
    print("PURGEABLE %d of %d   %8.3f GB" % (len(ok), len(rows),
                                             _gb(sum(r["blend_bytes"] for r in ok))))
    print("HELD      %d of %d   %8.3f GB" % (len(no), len(rows),
                                             _gb(sum(r["blend_bytes"] for r in no))))
    tally = {}
    for r in no:
        for g in r["refusals"]:
            tally[g] = tally.get(g, 0) + 1
    for g, n in sorted(tally.items(), key=lambda kv: -kv[1]):
        print("   %-44s %3d" % (g, n))

    if not a.apply:
        print("   DRY RUN -- nothing deleted.  Re-run with --apply.")
        _receipt("purge_dryrun", {"rows": rows})
        return 0

    free_before = _statvfs_free()
    freed = 0
    for r in ok:
        why = _forbidden(r["blend"])
        if why:
            print("   REFUSED AT UNLINK %s: %s" % (r["item"], why))
            continue
        os.unlink(r["blend"])
        freed += r["blend_bytes"]
        r["deleted"] = True
    free_after = _statvfs_free()
    print("sum of filesizes  %10.3f GB" % _gb(freed))
    print("statvfs free      %10.3f GB -> %10.3f GB   = %+.3f GB MEASURED"
          % (_gb(free_before), _gb(free_after), _gb(free_after - free_before)))
    p = _receipt("purge", {"rows": rows, "sum_filesizes_bytes": freed,
                           "statvfs_free_before": free_before,
                           "statvfs_free_after": free_after})
    print("receipt           %s" % os.path.relpath(p, R2))
    return 0


# ---------------------------------------------------------------- selftest

_PNG_HDR = b"\x89PNG\r\n\x1a\n"


def _fake_png(path, w, h):
    import struct, zlib
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    def chunk(t, d):
        return (struct.pack(">I", len(d)) + t + d
                + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff))
    with open(path, "wb") as f:
        f.write(_PNG_HDR + chunk(b"IHDR", ihdr) + chunk(b"IEND", b""))


def _fixture(root, item, *, blend_bytes=b"BLENDER-TEST-PAYLOAD",
             report=True, log_verdict="ITEM_ACCEPTED", json_result="ITEM_ACCEPTED",
             blend_sha_matches=True, macro=True, macro_wh=(MACRO_W, MACRO_H),
             witness=True, report_item=None, log_item=None):
    idir = os.path.join(root, "world", "items")
    rdir = os.path.join(root, "render", "items", item)
    wdir = os.path.join(root, "render", "gate_witness", item)
    for d in (idir, rdir, wdir, os.path.join(root, "world")):
        os.makedirs(d, exist_ok=True)
    # the frozen inputs, so stale_closure is quiet in the controls
    for n in ("itemkit.py", "world_contract.py"):
        with open(os.path.join(root, "world", n), "w") as f:
            f.write("# %s\n" % n)

    blend = os.path.join(idir, item + "_test.blend")
    with open(blend, "wb") as f:
        f.write(blend_bytes)
    sha = _sha256(blend)
    size = len(blend_bytes)

    if witness:
        _fake_png(os.path.join(wdir, "witness.png"), 512, 512)
        with open(os.path.join(wdir, "witness_spec.json"), "w") as f:
            json.dump({"control": "ok"}, f)
    if macro:
        _fake_png(os.path.join(rdir, "macro.png"), *macro_wh)
    if log_verdict:
        with open(os.path.join(rdir, "gate_run.log"), "w") as f:
            f.write(">> item %s  hero=True\n" % (log_item or item))
            f.write("... gate ran ...\n>> STAGE RESULT: %s\n" % log_verdict)
    if report:
        rep = {
            "item": report_item or item,
            "result": json_result,
            "witness": {"blend": None,
                        "png": os.path.join(wdir, "witness.png"),
                        "spec": os.path.join(wdir, "witness_spec.json")},
            "provenance": {
                "inputs": [{"role": "blend", "path": blend,
                            "bytes": size if blend_sha_matches else size + 7,
                            "sha256": sha if blend_sha_matches else "0" * 64}],
                "also_hash": [
                    {"role": "itemkit",
                     "sha256": _sha256(os.path.join(root, "world", "itemkit.py"))},
                    {"role": "world_contract",
                     "sha256": _sha256(os.path.join(root, "world",
                                                    "world_contract.py"))}],
            },
        }
        with open(os.path.join(rdir, "gate.json"), "w") as f:
            json.dump(rep, f)
    return blend


def cmd_selftest(a):
    """Both arms.  Four controls that MUST refuse, one that MUST accept."""
    fails = 0
    cases = [
        # name,                      fixture kwargs,                        expect
        ("POSITIVE complete record", {},                                    True,  []),
        ("NEGATIVE report missing",  {"report": False},                     False, ["G1_report_missing"]),
        ("NEGATIVE report stale vs blend",
                                     {"blend_sha_matches": False},          False, ["G4_report_is_stale_against_the_blend"]),
        ("NEGATIVE verdict only in JSON field (no printed line)",
                                     {"log_verdict": None},                 False, ["G2_no_printed_STAGE_RESULT"]),
        ("NEGATIVE printed UNMEASURABLE while JSON says ACCEPTED",
                                     {"log_verdict": "ITEM_UNMEASURABLE"},  False, ["G3_verdict_unmeasurable"]),
        ("NEGATIVE macro absent",    {"macro": False},                      False, ["G5_macro_missing"]),
        ("NEGATIVE macro not 4K",    {"macro_wh": (1920, 1080)},            False, ["G6_macro_not_at_gate_resolution"]),
        ("NEGATIVE witness pair torn",
                                     {"witness": False},                    False, ["G7_witness_pair_incomplete"]),
        ("NEGATIVE report filed under the wrong item id",
                                     {"report_item": "other_item"},         False, ["G8_report_is_about_other_item_not_ctl_item"]),
        ("NEGATIVE log says it gated a DIFFERENT item",
                                     {"log_item": "other_item"},            False, ["G8_report_is_about_other_item_not_ctl_item"]),
    ]
    print("%-58s %-8s %s" % ("control", "expect", "got"))
    for name, kw, expect_purgeable, expect_refusals in cases:
        root = tempfile.mkdtemp(prefix="dp_selftest_")
        try:
            _fixture(root, "ctl_item", **kw)
            r = evaluate("ctl_item",
                         items_dir=os.path.join(root, "world", "items"),
                         reports_dir=os.path.join(root, "render", "items"),
                         r2=root)
            got = r["purgeable"]
            ok = (got == expect_purgeable)
            for g in expect_refusals:
                if g not in r["refusals"]:
                    ok = False
            print("%-58s %-8s %-8s %s   %s"
                  % (name, "PURGE" if expect_purgeable else "REFUSE",
                     "PURGE" if got else "REFUSE",
                     "ok" if ok else "*** MISMATCH ***",
                     ",".join(r["refusals"])))
            if not ok:
                fails += 1
        finally:
            shutil.rmtree(root, ignore_errors=True)

    # ---- the .blend1 arm: B1 orphan, B2 sole carrier of a published verdict ----
    print()
    b1cases = [
        ("B1 POSITIVE ordinary backup beside its .blend", "ordinary", False),
        ("B1 NEGATIVE backup with NO sibling .blend",     "orphan",   True),
        ("B2 NEGATIVE backup IS the blend a report describes", "carrier", True),
        ("B2 POSITIVE report describes the LIVE blend, backup is stale",
                                                          "live",     False),
    ]
    print("%-58s %-8s %s" % ("control", "expect", "got"))
    for name, kind, want_refuse in b1cases:
        root = tempfile.mkdtemp(prefix="dp_b1_")
        try:
            idir = os.path.join(root, "world", "items")
            rdir = os.path.join(root, "render", "items", "ctl_item")
            os.makedirs(idir); os.makedirs(rdir)
            blend  = os.path.join(idir, "ctl_item_test.blend")
            backup = blend + "1"
            with open(backup, "wb") as f:
                f.write(b"OLD-BYTES-XX")
            if kind != "orphan":
                with open(blend, "wb") as f:
                    f.write(b"NEW-BYTES-YYYY" if kind != "live" else b"OLD-BYTES-XX")
            described = backup if kind == "carrier" else (
                blend if kind == "live" else None)
            if described:
                with open(os.path.join(rdir, "gate.json"), "w") as f:
                    json.dump({"item": "ctl_item", "provenance": {"inputs": [
                        {"role": "blend", "path": blend,
                         "bytes": os.path.getsize(described),
                         "sha256": _sha256(described)}]}}, f)
            pub = published_blend_hashes(os.path.join(root, "render", "items"))
            why = blend1_guard(backup, pub)
            ok = (why is not None) == want_refuse
            print("%-58s %-8s %-8s %s   %s"
                  % (name, "REFUSE" if want_refuse else "delete",
                     "REFUSE" if why else "delete",
                     "ok" if ok else "*** MISMATCH ***", why or ""))
            if not ok:
                fails += 1
        finally:
            shutil.rmtree(root, ignore_errors=True)

    # the forbidden-path arm: it must refuse a film and an assembly by name
    print()
    for p, want in [("/x/render/film10.blend", True),
                    ("/x/render/film10.blend1", True),
                    ("/x/render/world/assembly/r2/assembly9.blend", True),
                    ("/x/render/world/assembly/r2/assembly9.blend1", True),
                    ("/x/world/items/foo_test.blend1", False)]:
        why = _forbidden(p)
        ok = (why is not None) == want
        print("%-58s %-8s %-8s %s"
              % ("path guard " + os.path.basename(p),
                 "REFUSE" if want else "allow",
                 "REFUSE" if why else "allow",
                 "ok" if ok else "*** MISMATCH ***"))
        if not ok:
            fails += 1

    print()
    print("SELFTEST %s  (%d mismatches)" % ("PASS" if fails == 0 else "FAIL", fails))
    return 1 if fails else 0


# ---------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("census").set_defaults(fn=cmd_census)
    sub.add_parser("selftest").set_defaults(fn=cmd_selftest)

    b = sub.add_parser("blend1")
    b.add_argument("--scope", required=True, choices=sorted(BLEND1_SCOPES))
    b.add_argument("--apply", action="store_true")
    b.add_argument("--include-orphans", action="store_true",
                   help="also take backups that have no companion .blend")
    b.add_argument("--i-have-been-told-films-may-lose-their-backups",
                   action="store_true")
    b.set_defaults(fn=cmd_blend1)

    p = sub.add_parser("purge")
    p.add_argument("--item", action="append")
    p.add_argument("--apply", action="store_true")
    p.set_defaults(fn=cmd_purge)

    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
