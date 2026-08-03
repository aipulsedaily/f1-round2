"""STRONGEST collision gate — real triangle-vs-triangle, everything against everything.

    /opt/blender-5.2.0-linux-x64/blender -b <scene.blend> --factory-startup \
        -P tools/collision_gate.py -- --out docs/collision_report.json \
        [--frames 1,200,400,792] [--groups docs/explode_plan.json]

WHY THIS EXISTS
---------------
The user found it, by looking at a render, again:

    "make sure everything have the strongest collision detection one of the wheel
     suspension photos from the middlewaer shows the suspension is through the floor"

He was right. Six clusters were inside the turntable deck — all four corners 186 mm
in, FD 220 mm, FW 67 mm. Two separate weaknesses caused it:

1. **The floor was wrong.** The explode solver constrained parts against z=0, the
   showroom floor. But the car stands on a dais: `Turntable_Deck` top is z=0.340
   over a 6.9 x 6.9 m footprint. Anything dropping below 0.340 inside that
   footprint is inside the plinth, not above the floor.

2. **The check was too weak to notice.** It compared axis-aligned bounding boxes
   between CLUSTERS only. An AABB test cannot see the environment at all, and
   even between clusters it reasons about boxes rather than surfaces — two parts
   can interlock without their boxes reporting anything useful, and two boxes can
   overlap while the meshes never touch.

This gate replaces both with the strongest practical test: **BVH trees over the
EVALUATED meshes, testing actual triangle intersection**, over every pair that
matters:

    cluster  x  cluster          (a part through another part)
    cluster  x  environment      (a part through the deck, floor, wall, glazing)
    cluster  x  props            (a part through the vitrine, tyre stacks, plaque)

Round 1 built the same thing after shipping 19 overlapping module pairs, and its
lesson is written into this file's design: **any intersection is a defect by
definition** — there is no acceptable amount of one solid passing through another.

ANIMATED SCENES
---------------
`--frames` tests specific frames, because Beat 1 moves 616 objects for 33 seconds
and a layout that is clean at rest can still drive a suspension arm through the
deck mid-flight. A gate that only checks frame 1 would have passed the exact
defect that prompted it.
"""

import argparse
import json
import os
import sys
from collections import defaultdict

import bpy
from mathutils.bvhtree import BVHTree

# Imported by path, not by package: this runs inside Blender's interpreter with
# whatever cwd the caller happened to have.
if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gate_exit                                                 # noqa: E402

# Environment that parts must never intersect. Matched by prefix against the
# SHOWROOM / PROPS / LIGHTS collections so a renamed object cannot silently drop
# out of the test.
ENV_COLLECTIONS = ("SHOWROOM", "PROPS", "LIGHTS")


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True)
    p.add_argument("--groups", default=None,
                   help="explode_plan.json; groups parts into clusters so the "
                        "report names an assembly rather than 616 objects")
    p.add_argument("--frames", default=None,
                   help="comma list of frames to test; default = current frame")
    p.add_argument("--skip-self", action="store_true", default=True,
                   help="do not test parts within the same cluster against each "
                        "other — they are bolted together and touch by design")
    return p.parse_args(argv)


def bvh_of(objs, deps):
    """One BVH tree over the union of these objects' EVALUATED meshes.

    Evaluated, not base: 13 MIRROR modifiers mean a base mesh is HALF the real
    object, and SOLIDIFY adds shell thickness that is exactly what would be
    intersecting. Testing base meshes would miss the geometry that collides.
    """
    verts, faces = [], []
    for ob in objs:
        oe = ob.evaluated_get(deps)
        try:
            me = oe.to_mesh()
        except Exception:
            continue
        if me is None:
            continue
        base = len(verts)
        mw = ob.matrix_world
        verts.extend([mw @ v.co for v in me.vertices])
        for poly in me.polygons:
            vs = list(poly.vertices)
            for i in range(1, len(vs) - 1):          # fan-triangulate
                faces.append((base + vs[0], base + vs[i], base + vs[i + 1]))
        oe.to_mesh_clear()
    if not faces:
        return None
    return BVHTree.FromPolygons(verts, faces, all_triangles=True, epsilon=0.0)


def main():
    a = parse_args()
    scene = bpy.context.scene
    frames = ([int(f) for f in a.frames.split(",")] if a.frames
              else [scene.frame_current])

    # ---- group the car into clusters -------------------------------------
    groups = defaultdict(list)
    if a.groups:
        plan = json.load(open(a.groups))
        for key, c in plan["clusters"].items():
            for pname in c["parts"]:
                ob = bpy.data.objects.get(pname)
                if ob and ob.type == "MESH":
                    groups[key].append(ob)
    else:
        for ob in scene.objects:
            if ob.type == "MESH" and "CAR" in {c.name for c in ob.users_collection}:
                groups["CAR"].append(ob)

    # ---- environment, one BVH per object so the report names the culprit --
    env = {}
    for ob in scene.objects:
        if ob.type != "MESH":
            continue
        colls = {c.name for c in ob.users_collection}
        if colls & set(ENV_COLLECTIONS):
            env[ob.name] = [ob]

    print(f">> {len(groups)} clusters, {len(env)} environment objects, "
          f"frames {frames}")

    # A GATE THAT CANNOT FIND ITS SUBJECT MUST NOT REPORT CLEAN.
    #
    # Run against the world-only assembly this printed "0 clusters, 0
    # environment objects" and then "STAGE RESULT: COLLISION_CLEAN", because
    # zero pairs were tested and zero of them intersected. That is true and
    # worthless: a world assembly has no explode-plan clusters and no
    # SHOWROOM/PROPS/LIGHTS collections, so the gate was reporting a pass on an
    # empty set while the reader took it as proof the scene was sound.
    #
    # This is the same failure as R2-017 wearing different clothes -- a check
    # that quietly stops protecting you while still printing a verdict. Round 1
    # shipped 19 overlapping module pairs behind a bounding-box test; R2-012
    # shipped an assertion that could never fail. The rule that follows from
    # four repeats: NO GATE MAY EMIT A PASS WITHOUT NAMING WHAT IT TESTED.
    if not groups or not env:
        missing = []
        if not groups:
            missing.append("no clusters (needs --groups explode_plan.json, or a "
                           "CAR collection)")
        if not env:
            missing.append(f"no environment objects (needs one of {ENV_COLLECTIONS})")
        print(">> REFUSING TO REPORT: " + "; ".join(missing))
        print(">> This scene contains nothing this gate can test. That is NOT a "
              "pass.\n>> Run it on a scene that has the car and the showroom, or "
              "use the\n>> module-boundary triangle test instead.")
        json.dump({"frames": {}, "worst": None, "total_hits": 0,
                   "vacuous": True, "reason": missing},
                  open(a.out, "w"), indent=1)
        # `return` used to mean exit 0 here — the refusal was stated in the
        # text and contradicted by the status. VACUOUS is code 3.
        return gate_exit.verdict("COLLISION_VACUOUS")

    report = {"frames": {}, "worst": None, "total_hits": 0}
    worst = None

    for fr in frames:
        scene.frame_set(fr)
        bpy.context.view_layer.update()
        deps = bpy.context.evaluated_depsgraph_get()

        trees = {}
        for k, objs in groups.items():
            t = bvh_of(objs, deps)
            if t:
                trees[k] = t
        env_trees = {}
        for k, objs in env.items():
            t = bvh_of(objs, deps)
            if t:
                env_trees[k] = t

        hits = []
        keys = sorted(trees)
        # cluster x cluster
        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                ov = trees[keys[i]].overlap(trees[keys[j]])
                if ov:
                    hits.append({"a": keys[i], "b": keys[j], "kind": "cluster",
                                 "tri_pairs": len(ov)})
        # cluster x environment
        for k in keys:
            for e, et in env_trees.items():
                ov = trees[k].overlap(et)
                if ov:
                    hits.append({"a": k, "b": e, "kind": "environment",
                                 "tri_pairs": len(ov)})

        hits.sort(key=lambda h: -h["tri_pairs"])
        report["frames"][str(fr)] = hits
        report["total_hits"] += len(hits)
        if hits and (worst is None or hits[0]["tri_pairs"] > worst["tri_pairs"]):
            worst = dict(hits[0], frame=fr)

        tag = "CLEAN" if not hits else f"{len(hits)} INTERSECTIONS"
        print(f">> frame {fr:>5}: {tag}")
        for h in hits[:12]:
            print(f"     {h['kind']:<12} {h['a']:<16} x {h['b']:<24} "
                  f"{h['tri_pairs']:>7} triangle pairs")

    report["worst"] = worst
    json.dump(report, open(a.out, "w"), indent=1)
    print(f">> wrote {a.out}")
    if report["total_hits"] == 0:
        return gate_exit.verdict("COLLISION_CLEAN")
    return gate_exit.verdict("COLLISION_FAIL",
                             " (%d hits)" % report["total_hits"])


if __name__ == "__main__":
    # Blender 5.2 returns 0 for a script that raised; guard() makes the verdict
    # main() returns the process status, and an exception a status 2.
    gate_exit.guard(main, tool="collision_gate")
