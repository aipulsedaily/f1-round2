#!/usr/bin/env python3
"""R2-116 -- HOW MANY BASE POSTURES IS THE SEATED CROWD ACTUALLY BUILT FROM?

    blender -b <spectator_seated_test.blend> --factory-startup \
        -P tools/pose_census.py -- --artefact --json OUT.json
    blender -b --factory-startup -P tools/pose_census.py -- --runtime --json OUT.json
    blender -b --factory-startup -P tools/pose_census.py -- --selftest

WHY THIS EXISTS
===============
`item_gate.py :: realized_instances` grew a `distinct_shapes` term for one
named reason, written into its own docstring:

    "The rebuilt `spectator_seated` reports 420 distinct source datablocks over
     7,420 realized instances -- comfortably over the required 40 -- and the
     peep still says '~6 poses'.  420 datablocks holding 6 shapes satisfies a
     datablock count and satisfies nothing else."

That check exists to catch ONE artefact, and the stored verdict for that
artefact -- `render/gate_witness/_results/spectator_seated/gate.json`, 30 July
-- records `distinct_shapes: 420`, `distinct_shapes_required: 40`, and
`per_instance_variation: true`.  The check designed to catch this item passes
it, with the maximum possible score.

Either the item is genuinely varied and the peep was wrong, or
`_shape_signature` -- `(len(verts), len(polys), bbox to 10 mm, log volume)` --
is separating 420 *people* while the *posture* vocabulary behind them is small.
Those two possibilities are distinguishable by measurement and this file makes
the measurement, because a signature that counts bodies and a signature that
counts poses answer different questions and only one of them is the user's.

WHAT IS MEASURED, AND WHY IT NEEDS NO CLUSTERING HEURISTIC
==========================================================
`spectator_seated.build_library` stamps every source object it emits:

    ob["posture"]    = spec["posture"]        # the BASE posture's name
    ob["spec_index"] = index0 + i

so the base posture of every source datablock is recorded IN THE ARTEFACT by
the module that built it.  No descriptor, no distance threshold, no k.  The
posture vocabulary is read, not inferred.

TWO ARMS, R2-073
================
ARTEFACT  walk `depsgraph.object_instances` of the built blend exactly as
          item_gate does, and tally the SOURCE OBJECT'S `["posture"]` stamp
          beside the same `_shape_signature` item_gate uses.  Same walk, same
          instances, two different questions asked of them.
RUNTIME   call `spectator_seated.sample_spec(index0 + i)` for the same indices
          the library is built from and tally `spec["posture"]`.  This never
          opens a blend, so it cannot be fooled by a stale one -- which is the
          entire subject of this task.

The two arms are independent and must agree.  If they do not, say so and stop:
a disagreement means the blend on disk was not built by this source, which is
itself the finding.

CONTROLS -- BOTH DIRECTIONS, GENERATED FROM LIVE SOURCE (R2-072)
================================================================
A control that names a broken artefact expires into a cheerful pass the moment
the artefact is fixed.  These name nothing.  `--selftest` builds both arms'
input from the live module every run:

  POSITIVE  420 specs drawn with `force_posture="upright"`.  This IS "420
            datablocks holding one pose".  The census MUST report 1 distinct
            posture and a top share of 1.0000, and it must FAIL its bar.
            Without this arm, a census that always answers "lots" is
            indistinguishable from a census that is right.
  NEGATIVE  420 specs drawn normally.  The census must report the module's
            real vocabulary and must PASS.

EXIT CODES (tools/gate_exit.py's scheme)
    0 pass   1 fail the declared bar   2 could not run   3 vacuous/not measured
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ITEMS = os.path.join(ROOT, "world", "items")
for _p in (os.path.join(ROOT, "world"), ITEMS):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# THE BAR IS READ FROM THE MANIFEST, NOT INVENTED HERE.
#
# item_gate uses need = max(8, min(40, sqrt(realized))) for DATABLOCK counts. A
# posture vocabulary is a different quantity and a smaller one, and this project
# already states the number: `docs/item_manifest.json`, item `spectator_seated`,
# `variation_axes[0]` == "8-12 base postures". So the floor is PARSED from that
# string each run rather than copied into this file, for R2-110's reason -- a
# threshold copied out of the contract stops tracking the contract, silently,
# and the copy is what expires. If the manifest cannot be read the census says
# NOT MEASURED rather than falling back to a number of its own invention.
TOP_POSTURE_SHARE_LIMIT = 0.25
MANIFEST = os.path.join(ROOT, "docs", "item_manifest.json")


def posture_floor_from_manifest(item="spectator_seated", manifest=MANIFEST):
    """-> (floor:int|None, provenance:str). None means NOT MEASURED."""
    import re as _re
    try:
        d = json.load(open(manifest))
    except Exception as e:
        return None, "manifest unreadable: %s" % e
    for it in d.get("items", []):
        if it.get("id") != item:
            continue
        for ax in it.get("variation_axes", []):
            m = _re.match(r"\s*(\d+)\s*-\s*(\d+)\s+base postures", str(ax))
            if m:
                return int(m.group(1)), ("item_manifest.json :: %s "
                                         ".variation_axes -> %r" % (item, ax))
        return None, ("item %r declares no '<n>-<m> base postures' variation "
                      "axis, so there is no bar to judge against" % item)
    return None, "item %r is not in the manifest" % item


POSTURE_FLOOR, POSTURE_FLOOR_WHY = posture_floor_from_manifest()

LIBRARY_INDEX0 = 1000000      # spectator_seated.build_library's default
LIBRARY_N = 420               # its --library default


def _argv():
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]


def _shape_signature(me):
    """item_gate._shape_signature, reproduced so both numbers come off ONE walk.

    Deliberately a copy and not an import: importing item_gate pulls its whole
    render harness into a census that must run in seconds. It is 8 lines and it
    is checked against item_gate's own text by `--selftest`.
    """
    import numpy as np
    if not me.vertices:
        return None
    xs = np.empty(len(me.vertices) * 3, dtype=np.float64)
    me.vertices.foreach_get("co", xs)
    xs = xs.reshape(-1, 3)
    d = xs.max(axis=0) - xs.min(axis=0)
    vol = float(max(d[0], 1e-6) * max(d[1], 1e-6) * max(d[2], 1e-6))
    return (len(me.vertices), len(me.polygons),
            int(round(d[0] * 100)), int(round(d[1] * 100)), int(round(d[2] * 100)),
            int(round(math.log(max(vol, 1e-12)) * 100)))


def _verify_signature_matches_item_gate():
    """The copy above must still be the gate's. Read the gate's source and diff
    the returned tuple's shape, so a change there cannot leave this file quietly
    measuring something else."""
    src = open(os.path.join(HERE, "item_gate.py")).read()
    i = src.find("def _shape_signature")
    if i < 0:
        return False, "item_gate.py has no _shape_signature"
    body = src[i:src.find("\ndef ", i + 10)]
    want = ["len(me.vertices), len(me.polygons)",
            "int(round(d[0] * 100))",
            "int(round(math.log(max(vol, 1e-12)) * 100))"]
    missing = [w for w in want if w not in body]
    return (not missing), ("matches" if not missing else "DIVERGED: %s" % missing)


# ---------------------------------------------------------------------------
# ARTEFACT ARM
# ---------------------------------------------------------------------------
def artefact_arm(collection=None):
    import bpy
    deps = bpy.context.evaluated_depsgraph_get()
    want = None
    if collection and collection in bpy.data.collections:
        want = {o.name for o in bpy.data.collections[collection].all_objects}

    postures = Counter()
    shapes = Counter()
    srcs = Counter()
    unstamped = Counter()
    sig_cache = {}
    n = 0
    for inst in deps.object_instances:
        if not inst.is_instance:
            continue
        parent = inst.parent
        if parent is not None and want and parent.name not in want:
            continue
        ob = inst.object
        if ob is None or ob.type != "MESH":
            continue
        n += 1
        key = ob.data.name if ob.data else ob.name
        srcs[key] += 1
        if key not in sig_cache:
            try:
                sig_cache[key] = _shape_signature(ob.data)
            except Exception:
                sig_cache[key] = ("UNREADABLE", key)
        shapes[sig_cache[key]] += 1
        # the posture stamp lives on the SOURCE OBJECT, written by build_library
        p = None
        try:
            src_ob = bpy.data.objects.get(ob.name)
            if src_ob is not None and "posture" in src_ob.keys():
                p = str(src_ob["posture"])
        except Exception:
            p = None
        if p is None:
            unstamped[key] += 1
        else:
            postures[p] += 1
    return _summarise("artefact", n, srcs, shapes, postures, unstamped)


def _summarise(arm, n, srcs, shapes, postures, unstamped):
    if not n:
        return {"arm": arm, "realized": 0, "status": "NOT_MEASURED",
                "why": "no realized geometry-nodes instances were walked"}
    stamped = sum(postures.values())
    out = {
        "arm": arm,
        "realized": n,
        "distinct_sources": len(srcs),
        "distinct_shapes": len(shapes),
        "top_source_share": round(srcs.most_common(1)[0][1] / n, 4) if srcs else None,
        "top_shape_share": round(shapes.most_common(1)[0][1] / n, 4) if shapes else None,
        "instances_with_a_posture_stamp": stamped,
        "instances_without_a_posture_stamp": int(sum(unstamped.values())),
    }
    if not stamped:
        out["status"] = "NOT_MEASURED"
        out["why"] = ("no instance's source object carries a `posture` custom "
                      "property, so the posture vocabulary was not read. This "
                      "is not a pass and it is not a fail.")
        return out
    out["distinct_postures"] = len(postures)
    out["top_posture"] = postures.most_common(1)[0][0]
    out["top_posture_share"] = round(postures.most_common(1)[0][1] / stamped, 4)
    out["posture_histogram"] = dict(postures.most_common())
    out["posture_floor"] = POSTURE_FLOOR
    out["posture_floor_from"] = POSTURE_FLOOR_WHY
    out["top_posture_share_limit"] = TOP_POSTURE_SHARE_LIMIT
    if POSTURE_FLOOR is None:
        out["status"] = "NOT_MEASURED"
        out["why"] = ("the posture vocabulary was counted (%d distinct, top "
                      "%.4f) but there is no bar to judge it against: %s"
                      % (out["distinct_postures"], out["top_posture_share"],
                         POSTURE_FLOOR_WHY))
        return out
    out["status"] = ("POSTURE_OK"
                     if (out["distinct_postures"] >= POSTURE_FLOOR
                         and out["top_posture_share"] <= TOP_POSTURE_SHARE_LIMIT)
                     else "POSTURE_FAIL")
    return out


# ---------------------------------------------------------------------------
# RUNTIME ARM -- the module's own sampler, no blend involved
# ---------------------------------------------------------------------------
def runtime_arm(n=LIBRARY_N, index0=LIBRARY_INDEX0, force_posture=None):
    import spectator_seated as SS
    postures = Counter()
    for i in range(n):
        spec = SS.sample_spec(index0 + i, SS.SEED, force_posture=force_posture)
        postures[str(spec["posture"])] += 1
    fake_src = Counter({("s%d" % i): 1 for i in range(n)})
    return _summarise("runtime", n, fake_src, Counter(postures), postures, Counter())


# ---------------------------------------------------------------------------
# CONTROLS
# ---------------------------------------------------------------------------
def selftest():
    ok = True
    print("=" * 78)
    print("POSE CENSUS SELFTEST -- both directions, generated from live source")
    print("=" * 78)

    same, why = _verify_signature_matches_item_gate()
    print("[SIGNATURE PARITY] the copied _shape_signature vs item_gate.py: %s" % why)
    ok &= same

    print("\n[THRESHOLD PROVENANCE] floor = %r from %s" % (POSTURE_FLOOR,
                                                           POSTURE_FLOOR_WHY))
    if POSTURE_FLOOR is None:
        print("  => there is no bar; the census can only report, not judge.")
        ok = False
    else:
        # and the derivation must actually READ the manifest, not coincide with
        # a hardcoded 8. Point it at a manifest that says something else.
        import tempfile
        fake = {"items": [{"id": "spectator_seated",
                           "variation_axes": ["3-4 base postures"]}]}
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(fake, f)
            fp = f.name
        got, _w = posture_floor_from_manifest(manifest=fp)
        os.unlink(fp)
        print("  a manifest saying '3-4 base postures' yields floor %r" % got)
        if got == 3:
            print("  => the floor TRACKS the contract; it is not a constant "
                  "that happens to equal it.")
        else:
            print("  => the floor did NOT track the contract. It is effectively "
                  "hardcoded and will expire silently when the contract moves.")
            ok = False

    print("\n[POSITIVE CONTROL] 420 specs, force_posture='upright'.")
    print("  This IS '420 datablocks holding one pose'. The census must SEE it.")
    pos = runtime_arm(force_posture="upright")
    print("  distinct_postures %d   top_posture_share %.4f   status %s"
          % (pos["distinct_postures"], pos["top_posture_share"], pos["status"]))
    if pos["distinct_postures"] == 1 and pos["top_posture_share"] == 1.0 \
            and pos["status"] == "POSTURE_FAIL":
        print("  => POSITIVE CONTROL PASSES: one pose is reported as one pose "
              "and it FAILS the bar.")
    else:
        print("  => POSITIVE CONTROL FAILED. The census cannot see the defect "
              "it exists for; every other number it prints is worthless.")
        ok = False

    print("\n[NEGATIVE CONTROL] the same 420 indices, drawn normally.")
    neg = runtime_arm()
    print("  distinct_postures %d   top_posture_share %.4f   status %s"
          % (neg["distinct_postures"], neg["top_posture_share"], neg["status"]))
    if neg["distinct_postures"] > 1 and neg["status"] == "POSTURE_OK":
        print("  => NEGATIVE CONTROL PASSES: and it is a verdict, not a no-op "
              "-- the positive arm above returned 1 on the same code path.")
    else:
        print("  => NEGATIVE CONTROL FAILED: %s" % neg)
        ok = False

    print("\n[DISCRIMINATION] positive %d vs negative %d distinct postures"
          % (pos["distinct_postures"], neg["distinct_postures"]))
    if neg["distinct_postures"] <= pos["distinct_postures"]:
        print("  => the two arms did not separate. NOT a usable instrument.")
        ok = False

    print("=" * 78)
    print(">> STAGE RESULT: %s" % ("POSE_CENSUS_SELFTEST_OK" if ok
                                   else "POSE_CENSUS_SELFTEST_FAIL"))
    return 0 if ok else 1


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--artefact", action="store_true")
    a.add_argument("--runtime", action="store_true")
    a.add_argument("--selftest", action="store_true")
    a.add_argument("--collection", default=None)
    a.add_argument("--json", default=None)
    ns = a.parse_args(_argv())

    if ns.selftest:
        return selftest()
    if not (ns.artefact or ns.runtime):
        print("nothing asked for: pass --artefact, --runtime or --selftest.")
        print(">> STAGE RESULT: POSE_CENSUS_VACUOUS")
        return 3

    rows = {}
    if ns.runtime:
        rows["runtime"] = runtime_arm()
    if ns.artefact:
        rows["artefact"] = artefact_arm(ns.collection)

    for k, r in rows.items():
        print("-- %s arm" % k)
        for kk in ("realized", "distinct_sources", "distinct_shapes",
                   "top_shape_share", "distinct_postures", "top_posture",
                   "top_posture_share", "instances_without_a_posture_stamp",
                   "status", "why"):
            if kk in r:
                print("   %-34s %s" % (kk, r[kk]))
        if "posture_histogram" in r:
            print("   posture_histogram:")
            for p, c in r["posture_histogram"].items():
                print("      %-26s %6d" % (p, c))

    agree = None
    if len(rows) == 2 and all("distinct_postures" in r for r in rows.values()):
        agree = (rows["runtime"]["distinct_postures"]
                 == rows["artefact"]["distinct_postures"])
        print("\nTWO ARMS: runtime %d postures, artefact %d -- %s"
              % (rows["runtime"]["distinct_postures"],
                 rows["artefact"]["distinct_postures"],
                 "AGREE" if agree else "DISAGREE"))
        if not agree:
            print("   A disagreement means the blend on disk was NOT built by "
                  "this source. That is the finding; the posture numbers below "
                  "it are not yet evidence about the module.")

    if ns.json:
        with open(ns.json, "w") as f:
            json.dump({"rows": rows, "arms_agree": agree}, f, indent=1)
        print("wrote %s" % ns.json)

    st = [r.get("status") for r in rows.values()]
    if "NOT_MEASURED" in st:
        v, rc = "POSE_CENSUS_NOT_MEASURED", 3
    elif agree is False:
        v, rc = "POSE_CENSUS_ARMS_DISAGREE", 1
    elif "POSTURE_FAIL" in st:
        v, rc = "POSE_CENSUS_FAIL", 1
    else:
        v, rc = "POSE_CENSUS_OK", 0
    print(">> STAGE RESULT: %s" % v)
    return rc


if __name__ == "__main__":
    sys.exit(main())
