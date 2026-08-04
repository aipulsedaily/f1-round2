"""ITEM PLACEMENT GATE — is the item actually in the blend you are rendering?

    /opt/blender-5.2.0-linux-x64/blender -b <scene.blend> --factory-startup \
        -P tools/item_placement_gate.py -- --out docs/item_placement.json

    # both controls, live, no scene needed:
    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P tools/item_placement_gate.py -- --selftest

WHY THIS EXISTS
===============
R2-182 named the trap and paid a full render cycle for it:

    "`timing_stand` has never been placed into the shipping world ... Rendering
     f1126 from the film before and after the fix would have produced two
     identical images -- and been read as 'the fix is invisible, close it'."

An item that is not in the world produces a perfect null, and a perfect null is
indistinguishable from "the change had no effect".  `ITEM-PRESENCE-CENSUS.md`
then found that this is not one item but **all 41**: 0 of 41 modules contribute
a single datablock to `assembly9.blend` or `film14.blend`.

**So no A/B on this project is admissible until this gate has been run on the
blend that is about to be rendered.**  It answers one question -- is the thing
you are about to measure in the file? -- and it answers it about a named,
declared population rather than a grep.

THE CHECK THAT DID NOT EXIST, AND ITS TWO CONTROLS
==================================================
The brief's rule is that a placement check must be shown FAILING an item that
is not placed before it is trusted PASSING one that is.  Both controls run on
every invocation of `--selftest`, live, built in-process:

  MUST FAIL  `absent`   a scene with no item collection at all -> ABSENT.
             `shortfall` the declared population minus one unit -> COUNT.
             `shared`   N objects wearing ONE mesh datablock -> the no-repeats
                        arm.  This is the control `instance_variety.py` never
                        had at the item level, and it is the exact shape of
                        "one tree spammed a hundred times".
             `unstamped` a placed population with the provenance stamp stripped
                        -> so the stamp cannot rot into decoration.
  MUST PASS  `clean`    N objects, N meshes, all stamped -> PLACEMENT_ITEMS_OK.

And the strongest control on this project costs nothing, because it is already
on disk: **run this gate against `assembly9.blend` or `film14.blend` and every
PLACE row must come back ABSENT.**  A gate that cannot tell the shipping world
from a placed one is not measuring placement.  `--expect absent` asserts that
direction explicitly, so the must-fail case is a command anybody can re-run.

WHAT IT DOES NOT DO
===================
It does not judge the item.  `tools/item_gate.py` does that and its verdict is
read here, never recomputed.  It does not test keep-out; `tools/placement_gate.py`
does, and R2-110 records that the batteries ran it twice against the world and
never once against a control, so run it with its controls, not with this.

EXIT CODES: tools/gate_exit.py's scheme.  0 clean, 1 fail, 2 crash, 3 vacuous.
Judge on the printed `STAGE RESULT` line; Blender 5.2 exits 0 on an uncaught
script exception.
"""

import json
import os
import sys

import bpy

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "world"))

import gate_exit                                            # noqa: E402
import build_items as BI                                    # noqa: E402


# --------------------------------------------------------------------------- #
#  the measurement                                                              #
# --------------------------------------------------------------------------- #

def measure_item(row, scene=None):
    """What this blend actually holds for one registry row.

    Never falls through. If the declared collection is absent the verdict is
    ABSENT and the row names what the blend does have, so an unrecognised
    convention reads as a convention problem rather than as an empty item.
    """
    scene = scene or bpy.context.scene
    key = row.get("key") or row["item"]
    coll = bpy.data.collections.get(row["collection"])
    rep = {"key": key, "item": row["item"], "collection": row["collection"],
           "prefix": row["prefix"], "state": row.get("state"),
           "expect_objects": row.get("expect_objects")}

    if coll is None:
        rep.update(verdict="ABSENT", objects=0, why=(
            "no collection named %r in this blend. Object prefixes present: %s"
            % (row["collection"],
               sorted({o.name.split("_")[0] + "_" for o in bpy.data.objects})[:12])))
        return rep

    in_scene = {o.name for o in scene.objects}
    objs = [o for o in coll.all_objects
            if o.type == "MESH" and o.name in in_scene]
    rep["objects"] = len(objs)
    if not objs:
        rep.update(verdict="EMPTY", why=(
            "the collection %r exists but contributes no mesh object to the "
            "scene. A collection that is present but unlinked renders exactly "
            "like an absent one." % row["collection"]))
        return rep

    fails = []
    want = row.get("expect_objects")
    if want is not None and len(objs) != want:
        fails.append("COUNT: %d objects, registry declares %d" % (len(objs), want))

    off = [o.name for o in objs if not o.name.startswith(row["prefix"])]
    if off:
        fails.append("PREFIX: %d objects do not carry %r: %s"
                     % (len(off), row["prefix"], sorted(off)[:6]))

    inst = [o.name for o in objs if o.instance_type != "NONE"]
    if inst:
        fails.append("INSTANCER: %d objects instance a collection (%s)"
                     % (len(inst), sorted(inst)[:4]))

    from collections import Counter
    names = [o.data.name for o in objs]
    cnt = Counter(names)
    top_mesh, top_n = cnt.most_common(1)[0]
    top_share = top_n / float(len(objs))
    distinct = len(cnt)
    shared = sorted({o.data.name for o in objs if o.data.users > 1})
    rep.update(distinct_meshes=distinct, top_source_mesh=top_mesh,
               top_source_copies=top_n, top_share=round(top_share, 6),
               shared_meshes=len(shared),
               triangles=sum(sum(max(0, len(p.vertices) - 2)
                                 for p in o.data.polygons) for o in objs))
    if distinct != len(objs):
        fails.append("NO_REPEATS: %d objects share %d distinct source meshes; "
                     "the rule is one source mesh per placed unit"
                     % (len(objs), distinct))
    if shared:
        fails.append("NO_REPEATS: %d mesh datablocks have more than one user "
                     "(%s)" % (len(shared), shared[:4]))
    gated = len(objs) >= BI.MIN_UNITS_FOR_SHARE
    rep["top_share_gated"] = gated
    if gated and top_share > BI.FAMILY_TOP_SHARE_MAX:
        fails.append("NO_REPEATS: commonest source mesh is %.2f %% of the "
                     "family, over the PER-FAMILY bound of %.0f %% "
                     "(WAVE2-SCOPE §4.3). The global 40 %% check cannot fire "
                     "at this scale." % (100 * top_share,
                                         100 * BI.FAMILY_TOP_SHARE_MAX))

    unstamped = [o.name for o in objs if o.get("r2_item") is None]
    rep["unstamped"] = len(unstamped)
    if unstamped:
        fails.append("PROVENANCE: %d of %d placed objects carry no `r2_item` "
                     "stamp (%s). An unstamped object is an UNDET row in the "
                     "next census." % (len(unstamped), len(objs),
                                       sorted(unstamped)[:4]))
    wrong = sorted({o["r2_item"] for o in objs
                    if o.get("r2_item") not in (None, key)})
    if wrong:
        fails.append("PROVENANCE: objects in %r are stamped for another item: "
                     "%s" % (row["collection"], wrong))

    rep["fails"] = fails
    rep["verdict"] = "PLACED" if not fails else "PLACED_BUT_WRONG"
    return rep


def run(registry=None, expect=None, out=None, rows_wanted=None):
    reg, rows = BI.load_registry(registry or BI.REGISTRY)
    scene = bpy.context.scene
    if rows_wanted:
        # An explicit row list verifies a TEST BUILD, where `--place` overrode
        # the registry's state. It never widens a shipping run: a row named
        # here still has to be in the registry, so this is not a way round the
        # no-auto-detection rule.
        missing = [k for k in rows_wanted if k not in rows]
        if missing:
            raise SystemExit("REFUSING: %s not in the registry" % missing)
        want = [rows[k] for k in rows_wanted]
    else:
        want = [r for r in reg["items"] if r.get("state") == "PLACE"]
    report = {"blend": bpy.data.filepath or "(no file)",
              "registry": os.path.relpath(registry or BI.REGISTRY, ROOT),
              "rows_checked": len(want),
              "rows_named_explicitly": rows_wanted or None,
              "expect": expect, "items": []}

    if not want:
        print("no registry row is in state PLACE; there is nothing to verify.")
        report["result"] = "PLACEMENT_ITEMS_NOTHING_TO_TEST_VACUOUS"
        _write(out, report)
        return gate_exit.verdict("PLACEMENT_ITEMS_NOTHING_TO_TEST_VACUOUS")

    for row in want:
        rep = measure_item(row, scene)
        report["items"].append(rep)
        print("  %-24s %-16s objects %5s   %s"
              % (rep["key"], rep["verdict"], rep.get("objects"),
                 rep.get("why", "") or
                 ("meshes %d, top %.3f %%, %d unstamped"
                  % (rep.get("distinct_meshes", 0), 100 * rep.get("top_share", 0),
                     rep.get("unstamped", 0)))))
        for f in rep.get("fails", []):
            print("      FAIL %s" % f)

    placed = [r for r in report["items"] if r["verdict"] == "PLACED"]
    absent = [r for r in report["items"] if r["verdict"] in ("ABSENT", "EMPTY")]
    broken = [r for r in report["items"] if r["verdict"] == "PLACED_BUT_WRONG"]
    report.update(n_placed=len(placed), n_absent=len(absent), n_broken=len(broken))

    # `--expect absent` is the must-fail direction, stated as a command.
    if expect == "absent":
        ok = len(absent) == len(report["items"])
        print("\nEXPECT ABSENT: %d of %d rows absent from this blend"
              % (len(absent), len(report["items"])))
        report["result"] = ("PLACEMENT_ITEMS_ABSENT_AS_EXPECTED_OK" if ok
                            else "PLACEMENT_ITEMS_FAIL")
        _write(out, report)
        return gate_exit.verdict(report["result"] if ok
                                 else "PLACEMENT_ITEMS_FAIL")

    if absent or broken:
        print("\n%d PLACE row(s) absent, %d present but wrong"
              % (len(absent), len(broken)))
        report["result"] = "PLACEMENT_ITEMS_FAIL"
    else:
        print("\nall %d PLACE row(s) present, complete, one mesh per unit, "
              "stamped" % len(placed))
        report["result"] = "PLACEMENT_ITEMS_OK"
    _write(out, report)
    return gate_exit.verdict(report["result"])


def _write(out, report):
    if not out:
        return
    try:
        import provenance as P
        report["provenance"] = P.stamp(
            tool_file=__file__, tool_version="item_placement_gate 1.0.0",
            inputs=[("blend", bpy.data.filepath or ""),
                    ("registry", BI.REGISTRY)])
    except Exception as e:                                  # pragma: no cover
        report["provenance_error"] = repr(e)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w") as f:
        json.dump(report, f, indent=1, default=str)
    print("report -> %s" % out)


# --------------------------------------------------------------------------- #
#  SELFTEST — both directions, built live, in this process                      #
# --------------------------------------------------------------------------- #

def _scene_with(n_objects, n_meshes, stamp=True, coll="W_Item_SelftestFamily",
                pfx="SLF_"):
    """Build a synthetic item family and return its registry row.

    `n_meshes < n_objects` shares datablocks -- that is the spam control, and
    it is built rather than described so the gate has to look at it.
    """
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    c = bpy.data.collections.new(coll)
    sc.collection.children.link(c)
    meshes = []
    for i in range(n_meshes):
        me = bpy.data.meshes.new("%sSrc_%03d" % (pfx, i))
        # a distinct tetrahedron per source, so the meshes are really different
        k = 1.0 + 0.01 * i
        me.from_pydata([(0, 0, 0), (k, 0, 0), (0, k, 0), (0, 0, k)], [],
                       [(0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3)])
        me.update()
        meshes.append(me)
    for i in range(n_objects):
        ob = bpy.data.objects.new("%sUnit_%04d" % (pfx, i), meshes[i % n_meshes])
        ob.location = (100.0 + i * 2.0, 50.0, 0.0)
        c.objects.link(ob)
        if stamp:
            ob["r2_item"] = "selftest_family"
    bpy.context.view_layer.update()
    return {"key": "selftest_family", "item": "selftest_family",
            "collection": coll, "prefix": pfx, "state": "PLACE",
            "expect_objects": n_objects}


def selftest():
    cases = [
        # (name, row-builder, expected verdict, expected failing arm)
        ("clean      N objects / N meshes / stamped",
         lambda: _scene_with(40, 40), "PLACED", None),
        ("absent     no collection at all",
         lambda: (bpy.ops.wm.read_factory_settings(use_empty=True),
                  {"key": "selftest_family", "item": "selftest_family",
                   "collection": "W_Item_SelftestFamily", "prefix": "SLF_",
                   "state": "PLACE", "expect_objects": 40})[1],
         "ABSENT", None),
        ("shortfall  39 of a declared 40",
         lambda: dict(_scene_with(39, 39), expect_objects=40),
         "PLACED_BUT_WRONG", "COUNT"),
        ("shared     40 objects wearing ONE mesh",
         lambda: _scene_with(40, 1), "PLACED_BUT_WRONG", "NO_REPEATS"),
        ("concentrated 40 objects, 8 meshes (top 12.5 % > 10 %)",
         lambda: _scene_with(40, 8), "PLACED_BUT_WRONG", "NO_REPEATS"),
        ("unstamped  40 objects, no provenance",
         lambda: _scene_with(40, 40, stamp=False),
         "PLACED_BUT_WRONG", "PROVENANCE"),
        ("small      4 objects, 1 mesh -- share NOT gated below %d units, but "
         "the datablock arm still fires" % BI.MIN_UNITS_FOR_SHARE,
         lambda: _scene_with(4, 1), "PLACED_BUT_WRONG", "NO_REPEATS"),
    ]
    bad = []
    print("SELFTEST -- every case built live in this process\n")
    for name, mk, want_verdict, want_arm in cases:
        row = mk()
        rep = measure_item(row)
        got = rep["verdict"]
        arms = " | ".join(f.split(":")[0] for f in rep.get("fails", []))
        ok = got == want_verdict and (want_arm is None or
                                      any(f.startswith(want_arm)
                                          for f in rep.get("fails", [])))
        print("  %-4s %-62s -> %-18s %s"
              % ("ok" if ok else "FAIL", name, got, arms or "-"))
        for f in rep.get("fails", []):
            print("           %s" % f)
        if not ok:
            bad.append("%s: wanted %s/%s, got %s/%s"
                       % (name, want_verdict, want_arm, got, arms))

    print("\n  the four MUST-FAIL cases are the point: a placement check that "
          "has only ever been run\n  on something correct is a check nobody "
          "has any reason to believe. R2-182 is what\n  a clean zero for the "
          "wrong reason costs.")
    for b in bad:
        print("\n  FAIL %s" % b)
    print("\n>> STAGE RESULT: %s"
          % ("PLACEMENT_ITEMS_SELFTEST_OK" if not bad
             else "PLACEMENT_ITEMS_SELFTEST_FAIL"))
    return 0 if not bad else 1


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

    def opt(n, d=None):
        return argv[argv.index(n) + 1] if n in argv else d

    if "--selftest" in argv:
        return selftest()
    rw = opt("--rows")
    return run(registry=opt("--registry"), expect=opt("--expect"),
               out=opt("--out"),
               rows_wanted=[x for x in rw.split(",") if x] if rw else None)


if __name__ == "__main__":
    gate_exit.guard(main)
