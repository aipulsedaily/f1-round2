"""EMIT THE CEILING AS AN APPENDABLE LIBRARY COLLECTION.

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P tools/r2621_ceiling_library.py -- --out world/showroom_ceiling.blend

WHY THIS EXISTS, AND WHY IT IS THE RIGHT SHAPE RATHER THAN THE CONVENIENT ONE
=============================================================================
`tools/r2621_ceiling_build.py` opens a built film blend, builds the ceiling
into it and saves it. That works and it is verified. Its problem is not the
ceiling — the ceiling is 74k polygons and takes 10 seconds — it is that
`film16_breach.blend` is **7,969 MB** and this box has **11 GB of RAM and six
agents on it**. Opening and re-saving it costs a full paging round trip of the
whole file, twice, and MEASURED it does not complete: two attempts, 9.94 GB
read on the first, driven to 39 of 43 GB of swap, killed by its own guard.

MOVING THAT TO THE FARM DOES NOT WORK EITHER, AND THE REASON IS WORTH WRITING
DOWN because it is not obvious and it looks like it should:

  * `rq exec` takes a BUNDLE from a local root and pushes it. There is no
    supported way to hand an exec job a scene that already sits in the render
    worker's cache — `execservice.ensure_ready` deliberately reuses whatever
    scene the render worker holds and says in its own comment that "an exec job
    must never restart the render worker". So the film would have to travel as
    an `--include` in the bundle.
  * `execremote.push_bundle` compresses bundles with a HARDCODED `zstd -19 -T4`
    and has no level selection. The scene path HAS one, and it exists because
    `-19` was measured feeding a 4-5 MB/s wire at **1.3 MB/s** on a 4.22 GB
    push while the receiving ssh sat at 0.0 % CPU. Bundles never got that fix
    because a bundle is meant to be 7.9 MB of code.
  * `docs/agents.md` says it in one line: **"Ship code, not blends"**, and
    "the `.blend` is born where the render happens".

So the farm route means compressing 7.9 GB at `-19` on a box already at load
20+, to send a file the farm already has, to get back a file we already know
how to make. The write-back was never the problem — broker 2's own measured
fetch rate is 8.3 MB/s, so 7,969 MB comes home in about 16 minutes. THE INPUT
IS THE PROBLEM.

THE ACTUAL ANSWER IS TO STOP PAYING THE ROUND TRIP AT ALL
---------------------------------------------------------
The showroom itself is already solved this way. `tools/build_film_scene.py`
appends `SHOWROOM`, `PROPS` and `LIGHTS` from `world/car_anim.blend` at
identity, while the film blend is open and about to be saved anyway. A ceiling
that ships as a library collection joins that list and costs the pipeline
NOTHING — the open and the save are already being paid for by the film build.

    SET_COLLECTIONS = ("SHOWROOM", "PROPS", "LIGHTS")

becomes, next to it:

    with bpy.data.libraries.load(CEILING_BLEND, link=False) as (src, dst):
        dst.collections = ["R2_SHOWROOM_CEILING"]
    scene.collection.children.link(dst.collections[0])

That is the shape `build_film_scene.py` already uses, at identity, with no
fitting — the ceiling is authored in world coordinates against the round-1
showroom's own measured datums, exactly like the set it hangs under.

WHAT THIS FILE GUARANTEES ABOUT THE LIBRARY IT WRITES
-----------------------------------------------------
The whole point of a library is that the consumer does not have to re-verify
it, so this verifies it here and REFUSES to write a blend that fails:

  * NO LIGHT DATABLOCKS AT ALL. The ceiling creates no light, which is what
    keeps `showroom_lighting.measure()` reading 46,203.313 W across 23 lamps
    before and after. A library that smuggled in one lamp would move the film's
    exposure and nothing downstream would look for it.
  * NO EMISSIVE MATERIALS, for the same reason — `interior_emission_strength_sum`
    must not move either.
  * NO IMAGE TEXTURES. The brief forbids external assets and the farm cannot
    resolve them; a packed image would also make this file enormous.
  * Every material carries a real relief chain into Principled's `Normal`
    socket, resolved BY NAME.
  * Nothing above z 6.200, the round-1 slab soffit.
"""

import argparse
import json
import os
import sys
import time

import bpy

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(R2, "tools"), os.path.join(R2, "world"),
           os.path.join(R2, "world/items")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import gate_exit                                                 # noqa: E402


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--out", default=os.path.join(R2, "world/showroom_ceiling.blend"))
    p.add_argument("--report", default=None)
    return p.parse_args(argv)


def main():
    t0 = time.time()
    a = parse_args()
    import showroom_ceiling as SC

    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    summary = SC.build()
    rep = {"build": summary, "out": a.out}

    coll = bpy.data.collections.get(SC.COLL)
    if coll is None:
        print(">> the build produced no %s collection" % SC.COLL)
        return gate_exit.verdict("CEILING_LIB_VACUOUS")

    # ---- the guarantees, checked rather than asserted in prose -----------
    bad = []
    lights = [l.name for l in bpy.data.lights]
    if lights:
        bad.append("carries %d light datablock(s): %s" % (len(lights), lights[:4]))
    imgs = [i.name for i in bpy.data.images if i.source == "FILE"]
    if imgs:
        bad.append("carries %d FILE image(s): %s" % (len(imgs), imgs[:4]))

    emissive, flat, zmax, zworst = [], [], -1e9, None
    for m in bpy.data.materials:
        if not m.node_tree:
            continue
        for nd in m.node_tree.nodes:
            if nd.bl_idname in ("ShaderNodeEmission", "ShaderNodeBackground"):
                emissive.append(m.name)
            if nd.bl_idname == "ShaderNodeBsdfPrincipled":
                s = nd.inputs.get("Emission Strength")
                if s is not None and not s.is_linked and float(s.default_value) > 0:
                    emissive.append(m.name)
        tex = sum(1 for nd in m.node_tree.nodes
                  if nd.bl_idname.startswith("ShaderNodeTex")
                  and nd.bl_idname != "ShaderNodeTexImage")
        wired = any(nd.bl_idname == "ShaderNodeBsdfPrincipled"
                    and nd.inputs.get("Normal") is not None
                    and nd.inputs["Normal"].is_linked
                    for nd in m.node_tree.nodes)
        if tex < 3 or not wired:
            flat.append("%s (tex %d, Normal wired %s)" % (m.name, tex, wired))
    if emissive:
        bad.append("carries emissive material(s): %s" % sorted(set(emissive)))
    if flat:
        bad.append("material(s) below the depth floor: %s" % flat)

    import numpy as np
    for ob in bpy.data.objects:
        if ob.type != "MESH":
            continue
        co = np.empty(len(ob.data.vertices) * 3)
        ob.data.vertices.foreach_get("co", co)
        M = np.array(ob.matrix_basis)          # fresh objects: basis, not world
        z = (co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3])[:, 2]
        if float(z.max()) > zmax:
            zmax, zworst = float(z.max()), ob.name
    if zmax > SC.Z_SLAB + 1e-4:
        bad.append("%s reaches z %.4f, inside the round-1 slab at %.3f"
                   % (zworst, zmax, SC.Z_SLAB))

    rep["lights"] = lights
    rep["file_images"] = imgs
    rep["emissive_materials"] = sorted(set(emissive))
    rep["highest_surface"] = [zworst, round(zmax, 4)]
    rep["n_materials"] = len([m for m in bpy.data.materials
                              if m.name.startswith(SC.PFX)])
    rep["n_objects"] = len(coll.objects)

    print(">> LIBRARY %s: %d objects, %d polys, %d material(s)"
          % (SC.COLL, len(coll.objects), summary["polys"], rep["n_materials"]))
    print(">> lights %d, FILE images %d, emissive materials %d"
          % (len(lights), len(imgs), len(set(emissive))))
    print(">> highest surface %s at z %.4f (slab soffit %.3f)"
          % (zworst, zmax, SC.Z_SLAB))
    if bad:
        for b in bad:
            print(">>   REFUSING: %s" % b)
        if a.report:
            json.dump(rep, open(a.report, "w"), indent=1)
        return gate_exit.verdict("CEILING_LIB_FAIL")

    outp = os.path.abspath(a.out)
    os.makedirs(os.path.dirname(outp), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=outp, compress=False)
    if not os.path.exists(outp) or os.path.getmtime(outp) < t0:
        return gate_exit.verdict("CEILING_LIB_NOT_SAVED_FAIL")
    rep["saved_mb"] = round(os.path.getsize(outp) / 1048576.0, 2)
    print(">> saved %s  %.2f MB  in %.1f s"
          % (outp, rep["saved_mb"], time.time() - t0))
    print(">> APPEND IT WITH:")
    print("     with bpy.data.libraries.load(%r, link=False) as (src, dst):"
          % os.path.relpath(outp, R2))
    print("         dst.collections = [%r]" % SC.COLL)
    print("     scene.collection.children.link(dst.collections[0])")
    if a.report:
        os.makedirs(os.path.dirname(os.path.abspath(a.report)), exist_ok=True)
        json.dump(rep, open(a.report, "w"), indent=1)
    return gate_exit.verdict("CEILING_LIB_BUILT")


if __name__ == "__main__":
    gate_exit.guard(main, tool="r2621_ceiling_library")
