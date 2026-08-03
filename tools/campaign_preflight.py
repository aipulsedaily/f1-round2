#!/usr/bin/env python3
"""Filesystem resume checkpoint for the item campaign.

WHY THIS EXISTS
---------------
Wave 1 ran under the workflow runtime's `pipeline()`, whose per-agent cache
replayed unchanged prompts instantly. That cache rescued two lost sessions -- a
usage cap and a batch of API 500s. Wave 2 moves to Agent-tool orchestration for
the 4 -> 16 concurrency step (PLAN-throughput-optimisation.md sec 6), and
**that cache does not exist on the Agent-tool path**. Losing it silently means a
cap event costs a full re-run of everything in flight: up to one tranche, ~16
items x 2.4 h = 38 agent-hours (sec 6.3, failure mode 2).

This replaces it with something the orchestrator can run in under a second
before every fan-out: look on disk, and do not dispatch an agent for an item
that is already finished.

WHAT "FINISHED" MEANS, AND WHY THERE ARE TWO ANSWERS
----------------------------------------------------
Two different questions get confused into one, and conflating them is how a
checkpoint grows a hole:

  RESUME   "was this item already done?"  -- the question `pipeline()`'s cache
           answered. It knows nothing about quality; it only knows the work
           happened. This is the question a crash-resume must ask, because
           re-running accepted work is the exact cost the checkpoint exists to
           avoid.

  WAVE2    "does this item meet the wave-2 contract?" -- artefacts present AND
           the macro delivered at the resolution the gate scores (R2-020) AND
           judged by the CURRENT gate AND accepted.

`--policy resume` (default) answers the first. `--policy wave2` answers the
second, and its extra rules are exactly the three defects wave 1 shipped:
1080p macros scored as 4K, gate reports written by the superseded four-check
gate, and rejections.

Run both. The gap between them is the wave-2 rework list, and it is meant to be
visible rather than quietly skipped.

EVERY RULE OPENS THE ARTEFACT
-----------------------------
`os.path.exists` is not a check. A session killed mid-write leaves a truncated
JSON, a zero-byte PNG, a half-written module -- all of which exist. On this
project the verification has been the broken thing nine times, always in the
same shape: the instrument reported on something other than the artefact. So:
the module is parsed, the blend's magic is read, the JSON is decoded and its
fields checked, and the PNG is walked chunk-by-chunk to its IEND. A file that
cannot be opened is a REBUILD, never a skip.

Stdlib only, no bpy: it must be cheap enough to run before every fan-out.

USAGE
    python3 tools/campaign_preflight.py --all
    python3 tools/campaign_preflight.py --items kerb_hero_t4,armco_post
    python3 tools/campaign_preflight.py --wave 2 --policy wave2 --json pf.json
    python3 tools/campaign_preflight.py --all --emit build   # ids, one per line

EXIT CODES
    0  every requested item skips (nothing to do)
    1  at least one item needs building  (normal; not an error)
    2  refused -- bad arguments, or an id that is not in the manifest
"""

import argparse
import ast
import json
import os
import struct
import sys

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(R2, "docs/item_manifest.json")

# The resolution tools/item_gate.py computes every pixel figure against
# (item_gate.py:195 RES_X_4K). A macro delivered at anything else was scored
# against a frame that does not exist -- R2-020, 11 of 28 wave-1 heroes.
RES_X_4K = 3840
RES_Y_4K = 2160

# The checks the CURRENT gate reports. A gate.json missing any of these was
# written by the superseded four-check gate and says nothing about the bar the
# item is now held to.
GATE_CHECKS_NOW = (
    "no_external_assets",
    "material_depth",
    "geometry_resolves_at_distance",
    "per_instance_variation",
    "witness_frame_valid",
    "surface_microstructure",
    "relief_reads_as_lip_and_shade",
    "silhouette_departs_from_analytic",
)

BLEND_MAGICS = (
    b"BLENDER",            # uncompressed
    b"\x28\xb5\x2f\xfd",   # zstd  -- what Blender 3.0+ writes by default
    b"\x1f\x8b",           # gzip  -- older compressed blends
)


# ---------------------------------------------------------------------------
# artefact readers. Each returns (ok, detail). None of them trusts existence.
# ---------------------------------------------------------------------------

def read_python(path, entrypoint="build"):
    """Exists, PARSES, and exposes the entry point the contract names.

    "Parses" alone is NOT enough, and I found that out by testing this rule
    against an artefact I had deliberately broken. Truncating a real 1,757-line
    item module to its first third produced a file that `ast.parse` accepts
    without complaint -- Python is happy for a `for` block to run off the end of
    the file -- so the first version of this function SKIPPED a module that was
    two thirds missing. That is precisely the hole the tranche cost is measured
    in.

    What survives truncation is the tail, and the tail is where the entry point
    lives. Measured over all 28 wave-1 modules: **28 of 28 define a top-level
    `build`**, and the last top-level def is `main` (24) or `_cli` (4). A module
    that parses but has no `build` is not a built item, whatever else is in it.
    """
    if not os.path.isfile(path):
        return False, "missing"
    n = os.path.getsize(path)
    if n < 200:
        return False, f"{n} bytes -- too small to be a built item module"
    try:
        src = open(path, "r", encoding="utf-8", errors="strict").read()
    except (OSError, UnicodeDecodeError) as exc:
        return False, f"unreadable: {type(exc).__name__}"
    try:
        tree = ast.parse(src, filename=path)
    except SyntaxError as exc:
        return False, f"does not parse: line {exc.lineno}: {exc.msg}"
    fns = [n_.name for n_ in tree.body
           if isinstance(n_, (ast.FunctionDef, ast.AsyncFunctionDef))]
    if not fns:
        return False, "parses but defines no top-level function -- no build entry point"
    if entrypoint not in fns:
        return False, (f"parses ({len(src.splitlines())} lines, {len(fns)} defs) "
                       f"but defines no top-level `{entrypoint}()`. Either it is "
                       f"truncated -- a half-written module still parses -- or it "
                       f"does not follow ITEM-CAMPAIGN-BRIEF sec 7. All 28 wave-1 "
                       f"modules define `{entrypoint}`.")
    return True, f"{len(src.splitlines())} lines, {len(fns)} top-level defs, has {entrypoint}()"


def read_blend(path):
    """Exists and starts with a magic Blender actually writes."""
    if not os.path.isfile(path):
        return False, "missing"
    n = os.path.getsize(path)
    if n < 1024:
        return False, f"{n} bytes -- truncated"
    with open(path, "rb") as f:
        head = f.read(12)
    for m in BLEND_MAGICS:
        if head.startswith(m):
            return True, f"{n/1e6:.1f} MB"
    return False, f"not a blend (magic {head[:8]!r})"


def read_png(path):
    """Signature, IHDR, and a walk to IEND.

    The walk is the point. A render killed at 90 % leaves a PNG whose header is
    perfectly valid and whose pixels stop halfway; only reaching IEND proves the
    writer finished. Returns (width, height) in the detail dict.
    """
    if not os.path.isfile(path):
        return False, "missing", {}
    n = os.path.getsize(path)
    if n < 45:
        return False, f"{n} bytes -- truncated", {}
    with open(path, "rb") as f:
        if f.read(8) != b"\x89PNG\r\n\x1a\n":
            return False, "not a PNG", {}
        # first chunk must be IHDR
        raw = f.read(8)
        if len(raw) < 8:
            return False, "truncated before IHDR", {}
        ln, typ = struct.unpack(">I4s", raw)
        if typ != b"IHDR" or ln != 13:
            return False, f"first chunk is {typ!r}, not a 13-byte IHDR", {}
        ihdr = f.read(13)
        f.read(4)                                   # CRC
        w, h = struct.unpack(">II", ihdr[:8])
        depth, ctype = ihdr[8], ihdr[9]
        saw_iend = False
        while True:
            raw = f.read(8)
            if len(raw) < 8:
                break
            ln, typ = struct.unpack(">I4s", raw)
            if typ == b"IEND":
                saw_iend = True
                break
            if f.seek(ln + 4, os.SEEK_CUR) > n:
                break
        meta = {"width": w, "height": h, "bit_depth": depth,
                "colour_type": ctype, "bytes": n}
        if not saw_iend:
            return False, f"{w}x{h} but the chunk stream never reaches IEND -- " \
                          "the writer did not finish", meta
        return True, f"{w}x{h}, {depth}-bit, {n/1e6:.1f} MB", meta


def read_gate(path, item_id):
    """Decodes, is about THIS item, and carries a verdict."""
    if not os.path.isfile(path):
        return False, "missing", {}
    if os.path.getsize(path) == 0:
        return False, "zero bytes", {}
    try:
        d = json.load(open(path))
    except (json.JSONDecodeError, OSError) as exc:
        return False, f"does not decode: {exc}", {}
    if not isinstance(d, dict):
        return False, "is not a JSON object", {}
    if d.get("item") != item_id:
        return False, f"reports on '{d.get('item')}', not '{item_id}'", {}
    checks = d.get("checks")
    if not isinstance(checks, dict) or not checks:
        return False, "carries no 'checks' block", {}
    if "result" not in d:
        return False, "carries no 'result'", {}
    return True, f"{d['result']}, {len(checks)} checks", d


# ---------------------------------------------------------------------------
# the per-item verdict
# ---------------------------------------------------------------------------

def paths_for(item_id):
    return {
        "module": os.path.join(R2, "world/items", item_id + ".py"),
        "blend": os.path.join(R2, "world/items", item_id + "_test.blend"),
        "gate": os.path.join(R2, "render/items", item_id, "gate.json"),
        "macro": os.path.join(R2, "render/items", item_id, "macro.png"),
    }


def inspect(item_id, entrypoint="build"):
    """Every artefact, opened. Policy is applied afterwards, not here."""
    p = paths_for(item_id)
    ok_mod, why_mod = read_python(p["module"], entrypoint)
    ok_bl, why_bl = read_blend(p["blend"])
    ok_gate, why_gate, gate = read_gate(p["gate"], item_id)
    ok_png, why_png, png = read_png(p["macro"])

    rules = [
        ("module_parses", ok_mod, why_mod, p["module"]),
        ("test_blend_readable", ok_bl, why_bl, p["blend"]),
        ("gate_report_decodes", ok_gate, why_gate, p["gate"]),
        ("macro_png_complete", ok_png, why_png, p["macro"]),
    ]

    # --- the wave-2 conformance rules ------------------------------------
    if not ok_png:
        r_res = (False, "no readable macro to measure")
    elif (png["width"], png["height"]) != (RES_X_4K, RES_Y_4K):
        r_res = (False,
                 f"macro delivered {png['width']}x{png['height']}, but the gate "
                 f"scores every pixel figure against {RES_X_4K}x{RES_Y_4K} "
                 f"(item_gate.py RES_X_4K) -- every px judgement on this item is "
                 f"out by {RES_X_4K / max(png['width'], 1):.3g}x. R2-020.")
    else:
        r_res = (True, f"{RES_X_4K}x{RES_Y_4K}")

    if not ok_gate:
        r_sch = (False, "no readable gate report")
        r_acc = (False, "no readable gate report")
    else:
        missing = [c for c in GATE_CHECKS_NOW if c not in gate["checks"]]
        r_sch = ((not missing),
                 "current gate" if not missing else
                 f"written by a superseded gate -- missing {missing}")
        res = gate.get("result")
        r_acc = (res == "ITEM_ACCEPTED", str(res))

    wave2 = [
        ("macro_at_gate_resolution", r_res[0], r_res[1], p["macro"]),
        ("gate_report_is_current", r_sch[0], r_sch[1], p["gate"]),
        ("gate_accepted", r_acc[0], r_acc[1], p["gate"]),
    ]

    # --- ADVISORY, deliberately not blocking ------------------------------
    # If the module is newer than its gate report, the report does not describe
    # the code on disk. That is real and worth seeing -- it is exactly the shape
    # of a rework killed mid-write, leaving stale downstream artefacts. It is
    # NOT a skip criterion, because I measured it: 11 of the 28 wave-1 items
    # have a module newer than their gate.json (agents kept editing after
    # gating), so blocking on it would re-run 11 items that are genuinely done.
    # An mtime is not the artefact. Reported, never acted on.
    advisories = []
    if ok_mod and ok_gate:
        dt = os.path.getmtime(p["module"]) - os.path.getmtime(p["gate"])
        if dt > 0:
            advisories.append(
                f"module is {dt/60:.0f} min NEWER than its gate report -- the "
                f"report may not describe the code on disk")

    return {
        "item": item_id,
        "rules": {n: {"ok": ok, "detail": d} for n, ok, d, _ in rules},
        "wave2_rules": {n: {"ok": ok, "detail": d} for n, ok, d, _ in wave2},
        "advisories": advisories,
        "macro": png,
        "gate_result": (gate or {}).get("result"),
    }


def verdict(rep, policy):
    fails = [f"{n}: {v['detail']}" for n, v in rep["rules"].items() if not v["ok"]]
    if policy == "wave2":
        fails += [f"{n}: {v['detail']}"
                  for n, v in rep["wave2_rules"].items() if not v["ok"]]
    return ("SKIP" if not fails else "BUILD"), fails


# ---------------------------------------------------------------------------

def load_ids(args):
    man = json.load(open(args.manifest))
    known = [it["id"] for it in man["items"]]
    kset = set(known)
    if args.items:
        want = [s.strip() for s in args.items.replace("\n", ",").split(",") if s.strip()]
        bad = [i for i in want if i not in kset]
        if bad and not args.allow_unknown:
            sys.stderr.write(
                "REFUSING: not in docs/item_manifest.json: " + ", ".join(bad) +
                "\nThe manifest is the single source of truth for what exists. "
                "Pass --allow-unknown only to probe an id on purpose.\n")
            sys.exit(2)
        return want
    if args.wave is not None:
        sys.stderr.write(
            "REFUSING: --wave is not implemented here. Wave membership is a "
            "scoping decision (ITEM-CAMPAIGN-BRIEF sec 6) that depends on the "
            "re-measured screen presence from #61, and a checkpoint that "
            "invented its own wave boundaries would silently disagree with the "
            "orchestrator. Pass the ids with --items, or --all.\n")
        sys.exit(2)
    return known


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--items", help="comma- or newline-separated item ids")
    g.add_argument("--all", action="store_true", help="every id in the manifest")
    g.add_argument("--wave", type=int, help="(refused -- see the message)")
    p.add_argument("--policy", choices=("resume", "wave2"), default="resume")
    p.add_argument("--manifest", default=MANIFEST)
    p.add_argument("--json", help="write the full per-item report here")
    p.add_argument("--emit", choices=("build", "skip"),
                   help="print just those ids, one per line, for a fan-out")
    p.add_argument("--allow-unknown", action="store_true")
    p.add_argument("--entrypoint", default="build",
                   help="the top-level function an item module must define "
                        "(ITEM-CAMPAIGN-BRIEF sec 7). Default 'build'.")
    p.add_argument("--advisories", action="store_true",
                   help="also print the non-blocking notes")
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args()

    ids = load_ids(args)
    reports, skip, build = [], [], []
    for i in ids:
        rep = inspect(i, args.entrypoint)
        v, fails = verdict(rep, args.policy)
        rep["policy"] = args.policy
        rep["verdict"] = v
        rep["blocking"] = fails
        reports.append(rep)
        (skip if v == "SKIP" else build).append(i)

    if args.emit:
        for i in (build if args.emit == "build" else skip):
            print(i)
    elif not args.quiet:
        print(f"pre-flight  policy={args.policy}  {len(ids)} items")
        print("-" * 78)
        for r in reports:
            mark = "skip " if r["verdict"] == "SKIP" else "BUILD"
            extra = ""
            if r["macro"]:
                extra = f"  macro {r['macro']['width']}x{r['macro']['height']}"
            print(f"  {mark}  {r['item']:28s}{extra}")
            for f in r["blocking"]:
                print(f"           ! {f}")
            if args.advisories:
                for a in r["advisories"]:
                    print(f"           ~ {a}")
        print("-" * 78)
        print(f"  SKIP  {len(skip)}   BUILD {len(build)}")
        if build:
            print("  build: " + ", ".join(build))

    if args.json:
        os.makedirs(os.path.dirname(os.path.abspath(args.json)) or ".", exist_ok=True)
        json.dump({"policy": args.policy, "n": len(ids),
                   "skip": skip, "build": build, "items": reports},
                  open(args.json, "w"), indent=1)

    sys.exit(0 if not build else 1)


if __name__ == "__main__":
    main()
