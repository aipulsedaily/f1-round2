#!/usr/bin/env python3
"""R2-1381 -- RE-SCORE THE 32 SHIPPED ITEM VERDICTS AGAINST THE CLOSED GUARD.

    python3 tools/r2_1381_rescore.py [--dir render/items]

Reads every `render/items/*/gate.json` and asks, WITHOUT RE-RENDERING AND
WITHOUT RE-BUILDING ANYTHING, what `per_instance_variation` would say now that
the plain-object path is held to distinct SHAPES rather than distinct triangle
counts.  It writes nothing: `gate.json` files are the record of the run that
produced them and are not edited after the fact.

WHAT CAN AND CANNOT BE DECIDED FROM THE RECORD

  * `distinct_topologies` is `len(set(triangle_count))`, and

        distinct_shapes >= distinct_topologies

    holds whenever two differing triangle counts bring a differing vertex or
    polygon count with them, which is the ordinary case.  It is a bound and not
    a theorem: `_shape_signature` is (vertices, polygons, bbox to 10 mm, volume
    to 1 %), so two meshes agreeing on ALL of those and differing only in how
    their faces are cut into n-gons would be one shape and two topologies.  The
    lower bound is used below to say what CLEARS the new count requirement; it
    is never used to fail anything, so the exception can only make this report
    optimistic, never punitive.
  * The commonest-shape share was never recorded on the plain-object path --
    the old rule had no use for it -- and it cannot be bounded from a distinct
    count.  90 topologies over 3,236 objects is equally consistent with an even
    spread and with 2,500 objects sharing one.  So for those items the SHARE
    half is UNPROVEN, and this project's standing rule is that unproven is not
    a pass (R2-019).
  * Where `distinct_topologies == instances_found`, every object has its own
    triangle count, so every object is its own shape and the share is exactly
    1/n.  Those items are decidable end to end.

The output separates those three states rather than collapsing them, because
"would fail" and "was never measured" are different findings and only one of
them is somebody's rebuild.
"""
import os
import sys
import glob
import json
import math
import argparse

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)


_NEED_SRC = None


def need_distinct_shapes_for(n):
    """Evaluate item_gate's own `need_distinct_shapes` body without importing
    bpy: the function is pure arithmetic, so its source is exec'd in isolation.
    A second hand-typed copy of the rule would be the eighth copy of a constant
    in this repository and would drift from the gate within a week."""
    global _NEED_SRC
    if _NEED_SRC is None:
        src = open(os.path.join(HERE, "item_gate.py")).read()
        i = src.index("def need_distinct_shapes(")
        j = src.index("\ndef ", i + 1)
        ns = {"math": math}
        exec(compile(src[i:j], "item_gate.need_distinct_shapes", "exec"), ns)
        _NEED_SRC = ns["need_distinct_shapes"]
    return _NEED_SRC(n)


def rescore(path):
    d = json.load(open(path))
    m = d.get("measured", {})
    c = d.get("checks", {})
    r = {
        # THE DIRECTORY, NOT THE `item` FIELD. `render/items/spectator_crowd/
        # gate.json` carries `"item": "spectator_seated"`, so keying on the
        # field silently merges two different items' verdicts into one row.
        "item": os.path.basename(os.path.dirname(path)),
        "item_field": d.get("item"),
        "result": d.get("result"),
        "declared": m.get("instances_declared"),
        "n": m.get("instances_found"),
        "cv_size": m.get("cv_size"),
        "dt": m.get("distinct_topologies"),
        "real": m.get("realized_instances"),
        "was": c.get("per_instance_variation"),
    }
    declared, n, dt = r["declared"], r["n"], r["dt"]

    if declared is None or declared <= 1:
        r["path"] = "declared<=1 (no population required)"
        r["now"] = "PASS (unchanged)"
        return r
    if r["real"]:
        # NOT ASSERTED -- RECOMPUTED.  `need_distinct_shapes` and
        # `top_share_limit` are now shared with the plain-object path, and the
        # claim that sharing them moved no shipped verdict is only worth
        # something if the shipped numbers are put back through them.
        real = r["real"]
        n = real["realized"]
        need = need_distinct_shapes_for(n)
        limit = max(0.25, 1.0 / max(n, 1))
        now = (real["distinct_sources"] >= need
               and real["distinct_shapes"] >= need
               and real["top_source_share"] <= limit
               and real["top_shape_share"] <= limit)
        r["path"] = "realized instances (strong path)"
        r["need_shapes"] = need
        r["share_limit"] = limit
        r["now"] = ("PASS" if now else "FAIL") + (
            " (unchanged)" if now == bool(r["was"]) else " ** CHANGED **")
        return r
    if n is not None and declared > 1 and n < declared * 0.5:
        r["path"] = "gn_instanced, unresolvable (already fails)"
        r["now"] = "FAIL (unchanged)"
        return r

    # ---- the weak path, which is the one that changed --------------------
    r["path"] = "PLAIN OBJECTS (the weak path)"
    need = need_distinct_shapes_for(n)
    r["need_shapes"] = need
    r["share_limit"] = round(max(0.25, 1.0 / max(n, 1)), 4)
    cv_ok = r["cv_size"] is not None and r["cv_size"] >= 0.03
    if not cv_ok:
        r["now"] = "FAIL (cv_size floor, unchanged)"
        return r
    if dt < need:
        r["now"] = f"FAIL (shapes >= {dt} < {need} required)"
        return r
    if dt == n:
        r["now"] = f"PASS (all {n} objects distinct: share = 1/{n})"
        return r
    r["now"] = (f"UNPROVEN (count clears: shapes >= {dt} >= {need}; "
                f"commonest-shape share was never recorded)")
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.path.join(REPO, "render", "items"))
    a = ap.parse_args()
    rows = [rescore(p) for p in sorted(glob.glob(os.path.join(a.dir, "*", "gate.json")))]

    weak = [r for r in rows if r["path"].startswith("PLAIN")]
    print(f">> {len(rows)} item reports read; {len(weak)} took the plain-object "
          "path with more than one declared instance")
    hdr = (f"{'item':28} {'result':18} {'decl':>6} {'n':>6} {'dt':>5} "
           f"{'need':>5}  verdict now")
    print(hdr)
    print("-" * len(hdr))
    for r in sorted(rows, key=lambda x: (x["path"], x["item"])):
        if not r["path"].startswith("PLAIN"):
            continue
        print(f"{r['item']:28} {str(r['result']):18} {r['declared']:>6} "
              f"{r['n']:>6} {r['dt']:>5} {r['need_shapes']:>5}  {r['now']}")

    mislabelled = [r for r in rows
                   if r["item_field"] and r["item_field"] != r["item"]]
    for r in mislabelled:
        print(f">> NOTE: render/items/{r['item']}/gate.json is labelled "
              f"\"item\": \"{r['item_field']}\" -- unrelated to R2-1381, but any "
              "tool keying on that field merges two items.")

    strong = [r for r in rows if r["path"].startswith("realized")]
    print("")
    print(">> strong path (realized instances), recomputed through the now-shared "
          "need_distinct_shapes/top_share_limit:")
    for r in strong:
        print(f">>   {r['item']:26} realized {r['real']['realized']:>5}  "
              f"need {r['need_shapes']:>3}  limit {r['share_limit']:.3f}  "
              f"{r['now']}")
    moved = [r for r in strong if "CHANGED" in r["now"]]

    flips = [r for r in weak
             if r["result"] == "ITEM_ACCEPTED" and not r["now"].startswith("PASS")]
    print("")
    print(">> ACCEPTED items whose per_instance_variation no longer stands:")
    if not flips:
        print(">>   (none)")
    for r in flips:
        print(f">>   {r['item']}: {r['now']}")
    print(f">> strong-path verdicts moved by the shared thresholds: {len(moved)}")
    print(">> STAGE RESULT: R2-1381 RESCORE "
          f"{len(weak)} weak-path items, "
          f"{len([r for r in weak if r['now'].startswith('FAIL')])} FAIL, "
          f"{len([r for r in weak if r['now'].startswith('UNPROVEN')])} UNPROVEN, "
          f"{len([r for r in weak if r['now'].startswith('PASS')])} PASS; "
          f"{len(flips)} ACCEPTED verdicts affected")
    return 0


if __name__ == "__main__":
    sys.exit(main())
