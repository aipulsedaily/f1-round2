"""R2-3421 -- DOES `instance_variety.py` SEE A SPAMMED TREE?  A six-object answer.

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup -noaudio \
        -P tools/r2_3421_instance_variety_control.py -- --out work/r23421/iv_control.json

WHY
---
`tools/instance_variety.py` is the instrument that polices "no repeated assets
-- one tree spammed 100 times is the named failure".  Its counting loop is::

    for inst in deps.object_instances:
        if not inst.is_instance:
            continue

and `build_terrain.instance_plants()` -- which places every tree, every
hedgerow tree and the paddock avenue, 27,969 objects in `assembly14` -- makes
LINKED DUPLICATE OBJECTS: real scene objects that share a mesh datablock.  A
real object has `is_instance == False`.

So the claim under test is that the gate written for the tree rule cannot see a
tree.  This project has found over a dozen instruments that pass vacuously, and
every one of them was found by BUILDING THE FAILURE AND WATCHING THE GATE MISS
IT, so that is what this does rather than arguing from the source.

THE SCENE
---------
Deliberately the smallest thing that can tell the two placement styles apart:

    A. 40 linked-duplicate objects, ALL sharing ONE mesh.  This is a tree
       spammed 40 times, built exactly the way build_terrain builds trees.
    B. 1 emitter with a Geometry Nodes Instance-on-Points reading a two-mesh
       collection, 40 points.  This is how build_terrain places grass.

If the gate is sound it reports 41 sources' worth of trouble in A.  If the
blind spot is real it reports A as ZERO INSTANCES and grades the world on B
alone -- and B, with two meshes over 40 picks, is 50 % top share, so the gate
will happily print a SPAM verdict about the half of the scene that is not the
tree while the 100 %-spammed tree is invisible to it.

WHAT WOULD FALSIFY THE FINDING
------------------------------
`deps.object_instances` yielding `is_instance == True` for a linked duplicate.
The run prints the raw counts both ways -- with the filter and without -- so
the reader is not asked to take the conclusion on trust.
"""
import argparse
import json
import os
import sys
from collections import Counter

import bpy

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
import gate_exit                                                    # noqa: E402


def _spam_threshold():
    """`instance_variety.py`'s own SPAM_TOP_SHARE, read out of its source.

    It cannot be imported: that file is a straight-line `-P` script that parses
    argv and walks the depsgraph at import time.  So it is READ, not retyped --
    the same route `tools/build_and_dump_points.py` uses for its sibling's
    SCATTER_DIAG_M, and for the same reason: a copied constant is a claim, and
    the one time this project copied one instead of reading it, the two files
    disagreed by a factor of five and nobody noticed.
    """
    import re
    src = open(os.path.join(_HERE, "instance_variety.py")).read()
    m = re.search(r"^SPAM_TOP_SHARE\s*=\s*([0-9.]+)", src, re.M)
    if not m:
        raise SystemExit("no SPAM_TOP_SHARE in tools/instance_variety.py")
    return float(m.group(1))


SPAM_TOP_SHARE = _spam_threshold()

N_TREES = 40
N_POINTS = 40


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene

    # ---- A: ONE mesh, 40 linked duplicate objects (build_terrain's trees) ----
    bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=0.5, depth=2.0)
    tree = bpy.context.object
    tree.name = "VEG_tree_oak0_000000"
    tree.data.name = "VEG_tree_oak_L0_00"
    for i in range(1, N_TREES):
        ob = bpy.data.objects.new("VEG_tree_oak0_%06d" % i, tree.data)
        ob.location = (i * 2.0, 0.0, 0.0)
        sc.collection.objects.link(ob)

    # ---- B: ONE emitter, 40 GN instances over a TWO-mesh collection ---------
    lib = bpy.data.collections.new("VEG_grass_lib")
    for j in range(2):
        bpy.ops.mesh.primitive_cube_add(size=0.4, location=(0, 0, -50 - j))
        c = bpy.context.object
        c.name = c.data.name = "VEG_grass_fescue_H%02d_u" % j
        sc.collection.objects.unlink(c)
        lib.objects.link(c)

    me = bpy.data.meshes.new("VEG_grass_fescue_H")
    me.from_pydata([(i * 0.5, 5.0, 0.0) for i in range(N_POINTS)], [], [])
    me.update()
    a = me.attributes.new("inst_idx", "INT", "POINT")
    a.data.foreach_set("value", [i % 2 for i in range(N_POINTS)])
    emit = bpy.data.objects.new("VEG_grass_fescue_H", me)
    sc.collection.objects.link(emit)

    ng = bpy.data.node_groups.new("gn", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N = ng.nodes
    gi = N.new("NodeGroupInput")
    go = N.new("NodeGroupOutput")
    iop = N.new("GeometryNodeInstanceOnPoints")
    ci = N.new("GeometryNodeCollectionInfo")
    ci.inputs[0].default_value = lib
    ci.inputs[1].default_value = True
    ci.inputs[2].default_value = True
    na = N.new("GeometryNodeInputNamedAttribute")
    na.data_type = "INT"
    na.inputs[0].default_value = "inst_idx"
    L = ng.links
    L.new(gi.outputs[0], iop.inputs["Points"])
    L.new(ci.outputs[0], iop.inputs["Instance"])
    L.new(na.outputs[0], iop.inputs["Instance Index"])
    iop.inputs["Pick Instance"].default_value = True
    L.new(iop.outputs[0], go.inputs[0])
    emit.modifiers.new("gn", "NODES").node_group = ng

    bpy.context.view_layer.update()


def walk():
    """Both walks, side by side: the gate's, and the same walk without its filter."""
    deps = bpy.context.evaluated_depsgraph_get()
    gated, ungated = Counter(), Counter()
    n_is_instance = 0
    n_total = 0
    for inst in deps.object_instances:
        ob = inst.object
        if ob is None or ob.type != "MESH":
            continue
        n_total += 1
        key = ob.data.name if ob.data else ob.name
        ungated[key] += 1
        if inst.is_instance:
            n_is_instance += 1
            gated[key] += 1
    return gated, ungated, n_is_instance, n_total


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)

    build()
    gated, ungated, n_is, n_tot = walk()

    tree_mesh = "VEG_tree_oak_L0_00"
    seen_gated = gated.get(tree_mesh, 0)
    seen_ungated = ungated.get(tree_mesh, 0)

    print("scene: %d linked-duplicate trees on ONE mesh, %d GN instances on TWO"
          % (N_TREES, N_POINTS))
    print("depsgraph mesh entries: %d total, %d with is_instance == True\n" % (n_tot, n_is))
    print("%-28s%14s%14s" % ("source mesh", "gate's walk", "unfiltered"))
    for k in sorted(set(gated) | set(ungated)):
        print("%-28s%14d%14d" % (k, gated.get(k, 0), ungated.get(k, 0)))

    # what the gate would REPORT about this scene, from its own arithmetic
    n = sum(gated.values())
    verdict = None
    if n:
        top = gated.most_common(1)[0]
        share = top[1] / n
        verdict = {"total_instances": n, "sources": len(gated),
                   "top_source": top[0], "top_share": round(share, 4),
                   "spam": share > SPAM_TOP_SHARE}
        print("\ninstance_variety.py would report: %d instances, %d sources, "
              "top %s at %.1f %% -> %s"
              % (n, len(gated), top[0], share * 100,
                 "SPAM" if verdict["spam"] else "clean"))

    res = {"n_trees_built": N_TREES, "tree_mesh": tree_mesh,
           "tree_instances_seen_by_gate": seen_gated,
           "tree_instances_seen_unfiltered": seen_ungated,
           "depsgraph_mesh_entries": n_tot, "is_instance_true": n_is,
           "gate_would_report": verdict,
           "spam_top_share_threshold": SPAM_TOP_SHARE}
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    json.dump(res, open(a.out, "w"), indent=1)
    print("\nwrote %s" % a.out)

    if seen_gated == 0 and seen_ungated == N_TREES:
        print("\n>> THE GATE SAW %d OF THE %d SPAMMED TREES." % (seen_gated, N_TREES))
        print(">> The unfiltered walk saw all %d, so the trees ARE in the "
              "depsgraph; `is_instance` is what discards them." % N_TREES)
        print(">> Every tree in assembly14 is placed this way "
              "(build_terrain.instance_plants -> linked duplicate objects).")
        return gate_exit.verdict("IV_BLINDSPOT_CONFIRMED_GATE_BROKEN")
    if seen_gated == N_TREES:
        print("\n>> The gate saw all %d. The blind spot claimed by R2-3421 is "
              "REFUTED on this box." % N_TREES)
        return gate_exit.verdict("IV_BLINDSPOT_REFUTED_GATE_OK")
    print("\n>> Neither outcome: gate %d, unfiltered %d of %d. Do not conclude "
          "from this run." % (seen_gated, seen_ungated, N_TREES))
    return gate_exit.verdict("IV_BLINDSPOT_VACUOUS")


if __name__ == "__main__":
    gate_exit.guard(main)
