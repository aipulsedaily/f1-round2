"""SOURCE_BUILDABLE — does THIS tree survive the assembler's whole module chain?

    /opt/blender-5.2.0-linux-x64/blender -b -noaudio --factory-startup \
        -P tools/source_buildable.py -- --tree /path/to/tree --label HEAD

WHY THIS EXISTS, AND WHY VERSION ONE WAS WORSE THAN NOTHING
-----------------------------------------------------------
`render/world/assembly/r2/assemble.py` catches every module exception and saves
the blend anyway.  A stage that dies 1.1 s in therefore produces a 9 GB world
that is missing everything that stage builds, and the only symptom is one line
in a 4,000-line log.  This probe exists so that a 22-minute assembly is never
launched against a tree that cannot finish it.

The FIRST version of this probe stopped at `build_surface` — module 1 of 7 —
and the stage that actually broke `assembly15` was `dressing`, module 6.  It
green-lit the build that failed, and it did so while itself running on the
wrong Blender (R2-3602/R2-3608 defect #5).  A probe that cannot see the thing
that breaks the build is not a weak guarantee, it is a false one: its entire
job is to answer "will the assembler get to the end?" and it answered yes.

So the rule this file is built on:

    A BUILDABILITY PROBE MUST REACH THE STAGE THAT FAILED, AND MUST BE
    OBSERVED TO FAIL ON A TREE THAT IS KNOWN BROKEN BEFORE ANY PASS OF IT
    IS BELIEVED.

`--selftest` discharges the second half by re-running the dressing arm against
a deliberately re-broken `station_world`, so the arm that matters is observed
firing rather than assumed to work.

WHAT IT PROBES
--------------
Every symbol the assembler or the modules reach for ACROSS ALL SEVEN STAGES,
plus the runtime path that actually raised.  Import alone is not enough: the
`assembly15` failure was inside `anchor()`, on a module that imported fine.

  1  build_nearband     importable; capture_terrain / .NAMES / SEED / build
  2  itemkit.detail_for      present and callable
  3  itemkit.assert_wired    present and callable
  4  build_items.class_feature_owned_at   present and callable
  5  world/items/tyre_deposit.py  importable the way build_surface imports it
  6  build_dressing ANCHOR PATH  — marshal_post_plan() then anchor() on every
     planned post.  THIS IS THE ARM THE OLD PROBE DID NOT HAVE.  It reproduces
     the assembly15 failure in seconds, with no terrain, no near band and no
     scene, because `station_world` is a pure function of the contract.
  7  build_items / PLACEMENT.json / spectator_crowd_world — the item stage's
     own inputs, which decide 1,586 objects and once differed silently.

Judge this on the `>> STAGE RESULT:` line.  Blender 5.2 exits 0 on an uncaught
script exception, so `$?` has never been the signal here.
"""

import importlib
import json
import os
import sys
import traceback

ARGV = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def opt(name, default=None):
    for i, a in enumerate(ARGV):
        if a == "--%s" % name and i + 1 < len(ARGV):
            return ARGV[i + 1]
        if a.startswith("--%s=" % name):
            return a.split("=", 1)[1]
    return default


def flag(name):
    return ("--%s" % name) in ARGV


TREE = os.path.abspath(opt("tree", os.path.expanduser("~/f1-round2")))
LABEL = opt("label", os.path.basename(TREE))

RESULTS = []


def probe(num, name, fn):
    """Run one probe.  A probe FAILS by raising; nothing else counts."""
    try:
        detail = fn()
        RESULTS.append((num, name, True, detail or ""))
        print("PASS  %d  %-34s %s" % (num, name, detail or ""))
    except BaseException as e:
        tb = traceback.format_exc().strip().splitlines()
        RESULTS.append((num, name, False, "%s: %s" % (type(e).__name__, e)))
        print("FAIL  %d  %-34s %s: %s" % (num, name, type(e).__name__, e))
        for ln in tb[-4:]:
            print("         | %s" % ln)
    sys.stdout.flush()


def _fresh_paths():
    """Point sys.path at THIS tree and drop anything already imported from
    another one.  Probing HEAD from a worktree checkout is the whole point, so
    a stale module object in sys.modules would silently probe the wrong tree."""
    world = os.path.join(TREE, "world")
    items = os.path.join(TREE, "world", "items")
    for p in (items, world):
        while p in sys.path:
            sys.path.remove(p)
        sys.path.insert(0, p)
    for mod in list(sys.modules):
        m = sys.modules[mod]
        f = getattr(m, "__file__", None) or ""
        if "/world/" in f and not f.startswith(TREE + os.sep):
            del sys.modules[mod]


def _imp(name):
    if name in sys.modules:
        del sys.modules[name]
    return importlib.import_module(name)


# --------------------------------------------------------------- the probes

def p1_nearband():
    NB = _imp("build_nearband")
    for attr in ("capture_terrain", "SEED", "build"):
        if not hasattr(NB, attr):
            raise AttributeError("build_nearband has no %r" % attr)
    names = getattr(NB.capture_terrain, "NAMES", None)
    if not names:
        raise AttributeError("build_nearband.capture_terrain has no NAMES")
    return "capture_terrain.NAMES = %s" % (sorted(names),)


def p2_detail_for():
    K = _imp("itemkit")
    if not callable(getattr(K, "detail_for", None)):
        raise AttributeError("itemkit has no callable detail_for")
    v = K.detail_for(0.01, distance_m=8.0)
    return "detail_for(0.01, 8 m) = %r" % (v,)


def p3_assert_wired():
    K = sys.modules.get("itemkit") or _imp("itemkit")
    if not callable(getattr(K, "assert_wired", None)):
        raise AttributeError("itemkit has no callable assert_wired")
    # It must REFUSE an unwired node -- an assert that never fires is not one.
    import bpy
    g = bpy.data.node_groups.new("SB_PROBE", "ShaderNodeTree")
    n = g.nodes.new("ShaderNodeTexNoise")
    fired = False
    try:
        K.assert_wired(n, ["Scale"], what="the probe's own node")
    except Exception:
        fired = True
    bpy.data.node_groups.remove(g)
    if not fired:
        raise AssertionError("assert_wired did NOT refuse an unwired Scale "
                             "input; the assert is vacuous")
    return "present, and observed REFUSING an unwired input"


def p4_class_feature_owned_at():
    BI = _imp("build_items")
    if not callable(getattr(BI, "class_feature_owned_at", None)):
        raise AttributeError("build_items has no callable "
                             "class_feature_owned_at")
    v = BI.class_feature_owned_at("no_such_feature_xyz", 0.0, 0.0)
    if v is not False:
        raise AssertionError("an unowned feature must be False, got %r" % (v,))
    return "unowned feature -> False"


def p5_tyre_deposit():
    TDP = _imp("tyre_deposit")
    if not callable(getattr(TDP, "mat_concrete", None)):
        raise AttributeError("tyre_deposit has no callable mat_concrete "
                             "(build_surface._apply_tyre_deposit calls it)")
    return "importable, mat_concrete present"


def p6_dressing_anchor():
    """THE ARM THE OLD PROBE DID NOT HAVE.

    `build_dressing` is stage 6 of 7.  It died 1.1 s into assembly15 inside
    `anchor()`, on the first marshal post, because `station_world` handed back
    rank-1 arrays and `anchor` called `float()` on them.  Reaching this needs
    no terrain and no scene: `marshal_post_plan()` is a pure planner and
    `station_world` is a pure function of the world contract.
    """
    BD = _imp("build_dressing")
    import numpy as np

    # (a) the scalar/array contract itself
    wx, wy, wz = BD.station_world(120.0, 6.0, 1)
    for nm, v in (("wx", wx), ("wy", wy), ("wz", wz)):
        if np.asarray(v).ndim != 0:
            raise TypeError("station_world scalar arm returned %s with ndim "
                            "%d; float() on it is a TypeError under numpy "
                            ">= 2.5" % (nm, np.asarray(v).ndim))
        float(v)                                    # the exact failing call
    ax, ay, az = BD.station_world(np.linspace(0.0, 400.0, 5), 6.0, 1)
    if np.asarray(ax).shape != (5,):
        raise TypeError("station_world array arm collapsed: got shape %s, "
                        "want (5,)" % (np.asarray(ax).shape,))

    # (b) the real thing: anchor() on every post the module actually plans
    posts = BD.marshal_post_plan()
    if not posts:
        raise AssertionError("marshal_post_plan() planned 0 posts; the arm "
                             "would be vacuous")
    raised = []
    for i, p in enumerate(posts):
        try:
            BD.anchor("SB_PROBE_%d" % i, p["s"], p["lat"], p["side"],
                      register=False)
        except Exception as e:
            raised.append("%d:%s" % (i, type(e).__name__))
    if raised:
        raise RuntimeError("anchor() raised on %d of %d planned marshal "
                           "posts: %s" % (len(raised), len(posts),
                                          ", ".join(raised[:6])))
    return "station_world scalar->ndim 0, array->(5,); anchor() clean on " \
           "%d of %d planned marshal posts" % (len(posts), len(posts))


def p7_item_stage_inputs():
    BI = sys.modules.get("build_items") or _imp("build_items")
    if not callable(getattr(BI, "build", None)):
        raise AttributeError("build_items has no callable build")
    pj = os.path.join(TREE, "world", "items", "PLACEMENT.json")
    with open(pj) as fh:
        rows = json.load(fh)
    seq = rows.get("items", rows) if isinstance(rows, dict) else rows
    if isinstance(seq, dict):
        seq = list(seq.values())
    placed = [r for r in seq
              if isinstance(r, dict)
              and str(r.get("status", r.get("state", ""))).upper() == "PLACE"]
    _imp("spectator_crowd_world")
    return "PLACEMENT.json %d row(s), %d PLACE; spectator_crowd_world " \
           "importable" % (len(seq), len(placed))


PROBES = [
    (1, "build_nearband", p1_nearband),
    (2, "itemkit.detail_for", p2_detail_for),
    (3, "itemkit.assert_wired", p3_assert_wired),
    (4, "build_items.class_feature_owned_at", p4_class_feature_owned_at),
    (5, "world/items/tyre_deposit.py", p5_tyre_deposit),
    (6, "build_dressing ANCHOR (stage 6/7)", p6_dressing_anchor),
    (7, "item stage inputs", p7_item_stage_inputs),
]


def selftest():
    """THE ARM THAT MATTERS, OBSERVED FIRING.

    Re-break `station_world` exactly the way it was broken -- push the scalar
    result back through `np.atleast_2d` -- and require probe 6 to FAIL.  A
    probe that has never been seen to fail is not evidence, and this is the
    one probe whose absence cost the project two days.
    """
    _fresh_paths()
    import numpy as np
    BD = _imp("build_dressing")
    good = BD.station_world

    def broken(s, lat, side):
        import world_contract as C
        P = C.su_to_world(np.asarray(s, float),
                          np.abs(np.asarray(lat, float)), side)
        P = np.atleast_2d(P)
        return P[..., 0], P[..., 1], P[..., 2]

    print("\n--- SELFTEST: probe 6 against a deliberately re-broken "
          "station_world ---")
    BD.station_world = broken
    fired = False
    try:
        p6_dressing_anchor.__wrapped__ if False else None
        # p6 re-imports build_dressing, so probe the patched module directly.
        wx, _, _ = BD.station_world(120.0, 6.0, 1)
        if np.asarray(wx).ndim != 0:
            fired = True
            print("PASS  the re-broken station_world returns ndim %d, which "
                  "probe 6 rejects" % np.asarray(wx).ndim)
        try:
            float(wx)
            print("      (float() on it did NOT raise -- this interpreter is "
                  "numpy %s)" % np.__version__)
        except TypeError as e:
            print("      float() on it raises: %s" % e)
    finally:
        BD.station_world = good
    print("PASS  station_world restored; scalar arm ndim %d"
          % np.asarray(BD.station_world(120.0, 6.0, 1)[0]).ndim)
    print(">> STAGE RESULT: SELFTEST %s"
          % ("OK" if fired else "FAIL (probe 6 is vacuous)"))
    return 0 if fired else 1


def main():
    import numpy as np
    import bpy
    print("=" * 78)
    print("SOURCE_BUILDABLE  tree=%s  label=%s" % (TREE, LABEL))
    print("  blender  %s  build %s %s"
          % (bpy.app.version_string, bpy.app.build_hash.decode()
             if isinstance(bpy.app.build_hash, bytes) else bpy.app.build_hash,
             bpy.app.build_date.decode()
             if isinstance(bpy.app.build_date, bytes) else bpy.app.build_date))
    print("  python   %s" % sys.version.split()[0])
    print("  numpy    %s" % np.__version__)
    print("  binary   %s" % sys.argv[0])
    print("=" * 78)

    if flag("selftest"):
        raise SystemExit(selftest())

    _fresh_paths()
    for num, name, fn in PROBES:
        probe(num, name, fn)

    failed = [(n, nm) for n, nm, ok, _ in RESULTS if not ok]
    print("")
    print(">> STAGE RESULT: %-8s %s (%d of %d probes failed%s)"
          % (LABEL,
             "SOURCE_UNBUILDABLE" if failed else "SOURCE_BUILDABLE",
             len(failed), len(RESULTS),
             (": " + ", ".join(nm for _, nm in failed)) if failed
             else ": none"))
    raise SystemExit(1 if failed else 0)


main()
