"""R2-1881: PROVE `tools/instance_variety.py` CAN FAIL — and find where it cannot.

    blender -b --factory-startup -noaudio -P tools/r2_1881_variety_control.py -- \
        --arm spam --save /var/tmp/vc_spam.blend

    then, on the saved arm, the REAL guard, unmodified:

    blender -b /var/tmp/vc_spam.blend --factory-startup -P tools/instance_variety.py \
        -- --out /var/tmp/vc_spam.json

WHY
---
The client's named red line is *"one tree spammed a hundred times"*, and
`docs/instance_variety.json` is the only instrument that answers it:
4,688,475 VEG instances, 310 sources, top share 1.99 %, gini 0.7216.

**A guard that has only ever been run on a good world has not been tested.**  This
project has caught ten broken instruments in a day, and R2-1882 states the rule:
a refutation is worth nothing unless the instrument COULD have returned the other
answer.  So this file manufactures populations whose true answer is known and
requires the shipping guard to say so — including one it is known to get wrong.

THE ARMS.  Each builds a `VEG_`-prefixed emitter so the guard's family key
(`parent.name.split("_")[0]`) resolves to `VEG`, the family that carries the film's
vegetation, and the numbers are directly comparable to the shipping reading.

  spam       4,000 instances, ONE source mesh.            expect SPAM  top 100.0 %
  varied     4,000 instances over 50 sources, uniform.    expect CLEAN top ~2.5 %
  boundary_hi 4,000 instances, top source 45 %.            expect SPAM  (> 40 %)
  boundary_lo 4,000 instances, top source 35 %.            expect CLEAN (< 40 %)
  empty      no realized instances at all.                expect VACUOUS
  plainspam  2,000 PLAIN OBJECT COPIES of one mesh, no    expect VACUOUS  <-- THE HOLE
             instancing anywhere.

`plainspam` is the arm that matters.  `instance_variety.py` iterates
`depsgraph.object_instances` and `continue`s on `not inst.is_instance`, so a module
that emits plain objects contributes ZERO to every number it reports.  One tree
copied two thousand times is then not "spam" to this guard — it is not a
population at all, and the run comes back `INSTANCE_VARIETY_VACUOUS`, which reads
as an instrument problem rather than as the client's red line being crossed.

That is the same hole `tools/item_gate.py:~2986` has one level up: when a module
emits plain objects instead of geometry-nodes instances, `realized_instances()`
returns nothing, `gn_instanced` is False, and the variation test degrades to
`cv_size >= 0.03 and distinct_topologies >= 2` — TWO distinct shapes.  The guard is
weakest exactly where the client's complaint lives, and a near-band scrub tier that
emits plain objects would sail through both.

`boundary_hi` / `boundary_lo` exist so the SPAM verdict is shown to be a live
function of the distribution rather than a constant: the two arms differ only in
the share of one mesh, by ten points either side of the tool's own
`SPAM_TOP_SHARE = 0.40`.
"""
import argparse
import os
import sys

import bpy
import numpy as np

ARMS = ("spam", "varied", "boundary_hi", "boundary_lo", "empty", "plainspam")
N_INST = 4000
N_PLAIN = 2000


def parse():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--arm", required=True, choices=ARMS)
    p.add_argument("--save", required=True)
    p.add_argument("--n", type=int, default=N_INST)
    return p.parse_args(argv)


def wipe():
    for c in (bpy.data.objects, bpy.data.meshes, bpy.data.collections,
              bpy.data.node_groups):
        for d in list(c):
            try:
                c.remove(d)
            except Exception:                                      # noqa: BLE001
                pass


def leaf(name, seed, nseg=6):
    """A distinct little mesh. `seed` changes the SHAPE, so distinct names are
    distinct geometry and not 50 aliases of one datablock."""
    rng = np.random.default_rng(seed)
    t = np.linspace(0, 2 * np.pi, nseg, endpoint=False)
    r = 0.5 + 0.5 * rng.random(nseg)
    v = [(float(r[i] * np.cos(t[i])), float(r[i] * np.sin(t[i])), 0.0)
         for i in range(nseg)]
    v.append((0.0, 0.0, float(1.0 + 2.0 * rng.random())))
    f = [(i, (i + 1) % nseg, nseg) for i in range(nseg)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(v, [], f)
    me.update()
    return me


def source_collection(nsrc, seed0=100):
    """`nsrc` source objects, each with its own uniquely-named mesh datablock."""
    col = bpy.data.collections.new("VEGSRC")
    for i in range(nsrc):
        me = leaf("VEGSRC_mesh_%03d" % i, seed0 + i)
        ob = bpy.data.objects.new("VEGSRC_obj_%03d" % i, me)
        col.objects.link(ob)
    return col


def index_stream(n, nsrc, top_share):
    """n instance indices over `nsrc` sources with the commonest at `top_share`."""
    if nsrc == 1:
        return np.zeros(n, np.int32)
    ntop = int(round(top_share * n))
    rest = n - ntop
    idx = np.zeros(n, np.int32)
    if rest:
        idx[ntop:] = 1 + (np.arange(rest) % (nsrc - 1))
    rng = np.random.default_rng(3)
    rng.shuffle(idx)
    return idx


def emitter(name, n, idx, col):
    """A GN instancer: n points, each carrying an explicit source index.

    Explicit indices rather than a random pick, because the arm's whole value is
    that its true top share is KNOWN to the instance and not merely expected.
    """
    rng = np.random.default_rng(11)
    P = rng.random((n, 3)) * np.array([200.0, 200.0, 0.0])
    me = bpy.data.meshes.new(name + "_pts")
    me.from_pydata([tuple(p) for p in P], [], [])
    me.update()
    at = me.attributes.new("inst_idx", "INT", "POINT")
    at.data.foreach_set("value", idx.astype(np.int32))
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)

    ng = bpy.data.node_groups.new(name + "_gn", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    gi = ng.nodes.new("NodeGroupInput")
    go = ng.nodes.new("NodeGroupOutput")
    iop = ng.nodes.new("GeometryNodeInstanceOnPoints")
    ci = ng.nodes.new("GeometryNodeCollectionInfo")
    ci.inputs["Collection"].default_value = col
    ci.inputs["Separate Children"].default_value = True
    na = ng.nodes.new("GeometryNodeInputNamedAttribute")
    na.data_type = "INT"
    na.inputs["Name"].default_value = "inst_idx"
    iop.inputs["Pick Instance"].default_value = True
    ng.links.new(gi.outputs[0], iop.inputs["Points"])
    ng.links.new(ci.outputs["Instances"], iop.inputs["Instance"])
    ng.links.new(na.outputs[0], iop.inputs["Instance Index"])
    ng.links.new(iop.outputs["Instances"], go.inputs[0])
    md = ob.modifiers.new(name + "_mod", "NODES")
    md.node_group = ng
    return ob


def build(arm, n):
    wipe()
    sc = bpy.context.scene
    if arm == "empty":
        # A world with nothing realized. Not "clean" — unmeasured.
        me = leaf("VEG_lonely_mesh", 1)
        sc.collection.objects.link(bpy.data.objects.new("VEG_lonely", me))
        return dict(arm=arm, truth="no realized instances at all",
                    expect="INSTANCE_VARIETY_VACUOUS")

    if arm == "plainspam":
        # THE HOLE. One mesh, N plain object copies, zero instancing.
        me = leaf("VEG_scrub_L0_mesh", 42)
        rng = np.random.default_rng(5)
        for i in range(N_PLAIN):
            ob = bpy.data.objects.new("VEG_scrub_L0_%06d" % i, me)
            ob.location = tuple(rng.random(3) * np.array([200.0, 200.0, 0.0]))
            sc.collection.objects.link(ob)
        return dict(arm=arm,
                    truth="ONE source mesh copied %d times as PLAIN OBJECTS — "
                          "the client's red line, crossed" % N_PLAIN,
                    expect="INSTANCE_VARIETY_VACUOUS",
                    expect_is_a_defect=True,
                    true_top_share=1.0, true_sources=1)

    spec = {"spam": (1, 1.0), "varied": (50, 1.0 / 50),
            "boundary_hi": (50, 0.45), "boundary_lo": (50, 0.35)}[arm]
    nsrc, top = spec
    col = source_collection(nsrc)
    # the collection must exist in the file but NOT be rendered directly
    bpy.data.scenes[0].collection.children.link(col)
    col.hide_render = True
    idx = index_stream(n, nsrc, top)
    emitter("VEG_nearband_emitter", n, idx, col)
    got_top = float(np.bincount(idx).max()) / n
    return dict(arm=arm, truth="%d instances over %d sources, true top share %.4f"
                               % (n, nsrc, got_top),
                expect=("INSTANCE_VARIETY_SPAM" if got_top > 0.40
                        else "INSTANCE_VARIETY_CLEAN"),
                true_top_share=round(got_top, 4), true_sources=nsrc)


def main():
    a = parse()
    info = build(a.arm, a.n)
    # count what the depsgraph will actually hand the guard, so a build that
    # silently realized nothing is visible HERE and not misread as a guard result
    deps = bpy.context.evaluated_depsgraph_get()
    realized = sum(1 for i in deps.object_instances
                   if i.is_instance and i.object and i.object.type == "MESH")
    plain = sum(1 for o in bpy.data.objects if o.type == "MESH")
    os.makedirs(os.path.dirname(a.save), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=a.save)
    info.update(realized_instances=realized, plain_mesh_objects=plain,
                saved=a.save)
    print(">> ARM %s: %s" % (a.arm, info["truth"]))
    print(">> realized instances the guard will see: %d   plain mesh objects: %d"
          % (realized, plain))
    print(">> STAGE RESULT: R2_1881_VARIETY_ARM_BUILT %s" % (info,))


main()
