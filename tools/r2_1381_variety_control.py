#!/usr/bin/env python3
"""R2-1381 -- THE CONTROLS FOR THE VARIETY GUARD'S PLAIN-OBJECT PATH.

    blender -b -noaudio --python tools/r2_1381_variety_control.py -- [--n 4500]
    blender -b -noaudio --python tools/r2_1381_variety_control.py -- \
            --gate git:0bbfdaf            # the guard AS SHIPPED, before the fix

WHAT THIS IS FOR.  `item_gate.per_instance_variation` is the guard whose entire
purpose is the user's named failure -- "one tree spammed 100 times".  It had
two laws, not one:

  * geometry-nodes realized instances were held to 8-40 distinct SOURCES, the
    same number of distinct SHAPES, and no shape over 25 % of the population;
  * anything emitting PLAIN OBJECTS was asked for `cv_size >= 0.03` and
    `distinct_topologies >= 2`.

The second is satisfiable by 4,500 copies of two meshes at slightly different
scales, which is the named failure verbatim.  So the first thing this file does
is BUILD that item and watch the shipped rule accept it.  A fix with no
demonstrated failure is the vacuous control this project logs constantly: over
a dozen instruments here have passed without ever having been seen to fail.

THE FOUR CONTROLS, AND WHICH DIRECTION EACH ONE PROVES

  C1  false accept  vs OLD rule   MUST PASS   (the defect exists)
  C2  false accept  vs NEW rule   MUST FAIL   (the defect is closed)
  C3  40 real shapes over N       MUST PASS   (the fix is not "reject all")
  C4  7 unique objects (n < 8)    MUST PASS   (small honest populations live)

C3 and C4 matter as much as C2.  A guard that rejects everything is not strict,
it is broken in the mirror direction, and it costs a rebuild of every item in
the film to discover.

D1 is a PROBE, not a control: TWO bodies at hundreds of sizes, with the size
baked into the vertex data rather than the object matrix.  The new rule passes
it -- correctly by the letter, since those really are different meshes, and
arguably not by the spirit -- and the run prints the scale-invariant shape
count (2) that exposes it.  Recorded so the residual is a number in the log
rather than a sentence in a report.

`--gate git:<rev>` loads `item_gate.py` out of a git revision instead of the
working tree, so the "before" run is not a story about a file that no longer
exists: anybody can re-run the shipped guard against the false accept and watch
it say True, today or in a year.

NO RENDER, NO GPU, NO SCENE ON DISK.  Everything here is built with
`from_pydata` in a headless Blender and thrown away.
"""
import os
import sys
import math
import random
import argparse
import subprocess
import importlib.util

import bpy

TOOLS = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(TOOLS)
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)


def load_gate(spec_str):
    """`item_gate` from the working tree, a path, or `git:<rev>`.

    The sibling modules it imports (`provenance`, `gate_exit`,
    `socket_blend_scan`) come from `tools/` in every case -- only the gate
    itself is versioned here, because it is the only file under test.
    """
    if not spec_str:
        import item_gate
        return item_gate, os.path.join(TOOLS, "item_gate.py")
    if spec_str.startswith("git:"):
        rev = spec_str[4:]
        sha = subprocess.check_output(
            ["git", "-C", REPO, "rev-parse", "--short", rev]).decode().strip()
        src = subprocess.check_output(
            ["git", "-C", REPO, "show", f"{rev}:tools/item_gate.py"])
        out = os.path.join(REPO, "tmp", f"item_gate_at_{sha}.py")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "wb") as fh:
            fh.write(src)
        origin = f"git {sha} ({len(src)} bytes)"
    else:
        out, origin = spec_str, spec_str
    spec = importlib.util.spec_from_file_location("item_gate_under_test", out)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["item_gate_under_test"] = mod
    spec.loader.exec_module(mod)
    return mod, origin


G = None            # set in main() once the gate under test is chosen


# THE RULE AS SHIPPED BEFORE R2-1381, FROZEN VERBATIM FROM item_gate.py:2987.
# It lives here so the "before" half of every control can still be run after
# the fix has landed, and so the diff between the two laws is readable in one
# place.  Nothing in the gate imports this; it is evidence, not code.
def old_plain_object_rule(var):
    return (var["cv_size"] is not None and var["cv_size"] >= 0.03
            and var["distinct_topologies"] >= 2)


# --------------------------------------------------------------------------
# synthetic geometry
# --------------------------------------------------------------------------
def prism(name, radius, height, segs, twist=0.0):
    """A closed n-gon prism.  `segs` sets the triangle count, so two prisms
    with different `segs` are two distinct topologies; two with the same `segs`
    and different radius/height are one topology and two shapes."""
    verts, faces = [], []
    for k in range(segs):
        a = 2.0 * math.pi * k / segs
        verts.append((radius * math.cos(a), radius * math.sin(a), 0.0))
    for k in range(segs):
        a = 2.0 * math.pi * k / segs + twist
        verts.append((radius * math.cos(a), radius * math.sin(a), height))
    for k in range(segs):
        j = (k + 1) % segs
        faces.append((k, j, segs + j, segs + k))
    faces.append(tuple(range(segs)))
    faces.append(tuple(range(2 * segs - 1, segs - 1, -1)))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    return me


def scaled_copy(me, name, k):
    """A copy of one mesh with a uniform scale BAKED INTO THE VERTICES.

    This is the probe case D1: to any measurement taken on the mesh datablock
    these are different meshes, and to the eye they are one tree at N sizes.
    """
    verts = [(v.co.x * k, v.co.y * k, v.co.z * k) for v in me.vertices]
    faces = [tuple(p.vertices) for p in me.polygons]
    out = bpy.data.meshes.new(name)
    out.from_pydata(verts, [], faces)
    out.update()
    return out


def fresh_scene():
    for coll in (bpy.data.objects, bpy.data.meshes):
        for d in list(coll):
            coll.remove(d, do_unlink=True)
    return bpy.context.scene


def place(scene, meshes, n, rng, scale_lo=0.85, scale_hi=1.15, bake=None):
    """Emit `n` PLAIN OBJECTS drawn round-robin from `meshes`."""
    objs = []
    for i in range(n):
        src = meshes[i % len(meshes)]
        k = rng.uniform(scale_lo, scale_hi)
        me = scaled_copy(src, f"{bake}_{i}", k) if bake else src
        ob = bpy.data.objects.new(f"obj_{i:05d}", me)
        if bake:
            ob.scale = (1.0, 1.0, 1.0)
        else:
            ob.scale = (k, k, k)
        ob.location = (rng.uniform(-60, 60), rng.uniform(-60, 60), 0.0)
        ob.rotation_euler = (0.0, 0.0, rng.uniform(0, 2 * math.pi))
        scene.collection.objects.link(ob)
        objs.append(ob)
    return objs


# --------------------------------------------------------------------------
# one case
# --------------------------------------------------------------------------
def measure(label, objs, declared):
    """Exactly the gate's own path: tri_count -> instance_variation -> verdict."""
    bpy.context.view_layer.update()      # the objects were linked a moment ago
    deps = bpy.context.evaluated_depsgraph_get()
    _, per_tris = G.tri_count(objs, deps)
    var, _boxes = G.instance_variation(objs, deps, per_tris)
    gn_instanced = declared > 1 and var["n"] < declared * 0.5
    real = None                     # plain objects: nothing to walk

    old = old_plain_object_rule(var)
    if hasattr(G, "variation_verdict"):
        new = G.variation_verdict(declared, var, real, gn_instanced)
    else:
        new = None

    print(f">> --- {label} ---")
    print(f">>   declared {declared}, objects measured {var['n']}, "
          f"gn_instanced={gn_instanced}")
    print(f">>   cv_size {var['cv_size']}  distinct_topologies "
          f"{var['distinct_topologies']}")
    print(f">>   distinct_shapes {var.get('distinct_shapes')}  "
          f"top_shape_share {var.get('top_shape_share')}  "
          f"(required {var.get('distinct_shapes_required')}, "
          f"limit {var.get('top_shape_share_limit')})")
    print(f">>   distinct_source_meshes {var.get('distinct_source_meshes')}  "
          f"distinct_shapes_scale_invariant "
          f"{var.get('distinct_shapes_scale_invariant')}  (recorded, not gated)")
    print(f">>   OLD rule -> {old}      NEW rule -> {new}")
    return var, old, new


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=4500,
                    help="population for the big cases")
    ap.add_argument("--sources", type=int, default=40,
                    help="distinct sources for the positive control C3")
    ap.add_argument("--seed", type=int, default=1381)
    ap.add_argument("--gate", default="",
                    help="path, or git:<rev>, of the item_gate.py under test "
                         "(default: the working tree)")
    a = ap.parse_args(argv)

    global G
    G, origin = load_gate(a.gate)
    print(f">> gate under test: {origin}")
    print(f">> variation_verdict present: {hasattr(G, 'variation_verdict')}")

    rng = random.Random(a.seed)
    results = {}

    # ---- C1/C2  THE FALSE ACCEPT ----------------------------------------
    # N plain "trees" drawn from TWO meshes with a small random uniform scale.
    # This is the item the ranking document says the guard would grade as a
    # pass: 4,500 trees, two variants.
    scene = fresh_scene()
    two = [prism("src_A", 0.35, 6.0, 8), prism("src_B", 0.40, 7.0, 10)]
    objs = place(scene, two, a.n, rng)
    var, old, new = measure(f"C1/C2  FALSE ACCEPT: {a.n} plain objects, "
                            "2 source meshes, random uniform scale",
                            objs, declared=a.n)
    results["C1_false_accept_passes_OLD"] = (old is True)
    results["C2_false_accept_fails_NEW"] = (new is False)

    # ---- C3  THE POSITIVE CONTROL ---------------------------------------
    # The same population built HONESTLY: `--sources` genuinely different
    # bodies, evenly drawn.  This is what the strong path demands at this
    # count, and the new rule must not reject it.
    scene = fresh_scene()
    # `6 + i` segments, not `6 + i % 17`: the count requirement at 4,500 is
    # exactly 40, so a single accidental signature collision between two
    # sources would fail the positive control for a reason that has nothing to
    # do with the rule under test. Distinctness here is arithmetic, not luck.
    many = [prism(f"src_{i:02d}", 0.20 + 0.02 * (i % 11),
                  4.0 + 0.35 * (i % 13), 6 + i)
            for i in range(a.sources)]
    objs = place(scene, many, a.n, rng)
    var, old, new = measure(f"C3  POSITIVE CONTROL: {a.n} plain objects from "
                            f"{a.sources} genuinely different bodies",
                            objs, declared=a.n)
    results["C3_varied_passes_NEW"] = (new is True)

    # ---- C4  THE SMALL HONEST POPULATION --------------------------------
    # `pont_girder` is 7 objects, all 7 different, and is ACCEPTED.  A floor of
    # "8 distinct shapes" is arithmetically unsatisfiable by 7 objects, so the
    # new rule caps the requirement at the population.  Watch that it does.
    scene = fresh_scene()
    seven = [prism(f"girder_{i}", 0.30 + 0.05 * i, 3.0 + 0.4 * i, 5 + i)
             for i in range(7)]
    objs = place(scene, seven, 7, rng, scale_lo=0.95, scale_hi=1.05)
    var, old, new = measure("C4  SMALL POSITIVE CONTROL: 7 objects, 7 distinct "
                            "bodies (the pont_girder shape)", objs, declared=4)
    results["C4_small_varied_passes_NEW"] = (new is True)

    # ---- D1  THE RESIDUAL PROBE -----------------------------------------
    small = max(200, a.n // 10)
    scene = fresh_scene()
    two_baked = [prism("baked_A", 0.35, 6.0, 8), prism("baked_B", 0.40, 7.0, 10)]
    objs = place(scene, two_baked, small, rng, bake="baked")
    var, old, new = measure(f"D1  PROBE (not a control): {small} objects, TWO "
                            "bodies, scale baked into vertex data instead of "
                            "the object matrix", objs, declared=small)
    results["D1_probe_new_rule"] = new

    print("")
    for k, v in results.items():
        print(f">> CONTROL {k}: {v}")
    must = ["C1_false_accept_passes_OLD", "C2_false_accept_fails_NEW",
            "C3_varied_passes_NEW", "C4_small_varied_passes_NEW"]
    if not hasattr(G, "variation_verdict"):
        print(">> STAGE RESULT: R2-1381 PRE-FIX RUN -- item_gate has no "
              "variation_verdict(), so only C1 is decidable here. "
              f"C1 (false accept passes the shipped rule) = "
              f"{results['C1_false_accept_passes_OLD']}")
        return 0
    ok = all(results[k] for k in must)
    print(">> STAGE RESULT: R2-1381 CONTROLS "
          + ("ALL PASS" if ok else "FAILED")
          + " (" + ", ".join(f"{k}={results[k]}" for k in must) + ")")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
