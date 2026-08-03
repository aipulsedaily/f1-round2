#!/usr/bin/env python3
"""R2-116 -- DOES `tools/relief_audit.py` STILL DISCRIMINATE?  Both directions.

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P tools/relief_audit_control.py -- --selftest

WHY THIS EXISTS
===============
28 of 30 `render/items/_relief/*.json` predate the witness blend they describe;
every witness under `render/gate_witness/` was rebuilt on 2026-08-03.  Two have
been re-run and the numbers did not merely drift, they inverted:

    pont_girder   m_max 0.00272 -> 8.273   Height-unlinked stages 5 -> 0
    gantry_truss  m_max 0.00586 -> 8.073

Before re-running the other 28 and republishing 28 numbers, the instrument has
to be shown to still separate "there is relief here" from "there is not".  A
sweep that re-emits 28 confident figures from an instrument nobody watched fail
is how this project got the figures it is now withdrawing.

R2-072 IS THE REASON THIS CONTROL IS MANUFACTURED AND NOT NAMED.  The obvious
control -- "point it at a blend known to have no relief" -- expires into a
cheerful pass the moment that blend is repaired, which is exactly what happened
to `socket_index_audit`'s "REAL SHIPPED ARTEFACT" section when the two blends it
named were rebuilt.  So both arms are BUILT HERE, from the same node types the
item modules use, every run.  Nothing on disk can retire them.

NO EXTERNAL ASSETS.  Both control scenes are procedural: a subdivided grid, a
`ShaderNodeTexNoise`, a `ShaderNodeBump`.  Nothing is loaded, downloaded or
sampled from anywhere.

THE PAIR
========
  POSITIVE   `ShaderNodeBump.Height` driven by a procedural noise, and a mesh
             displaced by that same noise.  relief_audit MUST report bump
             stages with a non-zero `m`, and MUST NOT report the height as
             unlinked.  Without this arm, an audit that reports "no relief" on
             everything is indistinguishable from a correct one.
  NEGATIVE   bit-for-bit the same scene with the ONE `Height` link removed and
             the mesh left flat -- the R2-038 signature the two re-run reports
             say they used to carry.  relief_audit MUST report the height as
             unlinked and MUST NOT report relief.

A third statement is made about the pair rather than about either arm: the
positive's `m_max` must exceed the negative's.  Two arms that both "pass" while
returning the same number are not an instrument.

EXIT CODES (tools/gate_exit.py's scheme)
    0 the instrument discriminates   1 it does not   2 could not run
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BLENDER = "/opt/blender-5.2.0-linux-x64/blender"

# The item collection name `winding_audit.collect` looks for.
COLL = "W_Item_relief_control"
ITEM = "relief_control"


def _build(out_path, linked):
    """Write a control blend. `linked` selects the positive/negative arm."""
    import bpy
    from mathutils import Vector  # noqa: F401

    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for c in list(bpy.data.collections):
        bpy.data.collections.remove(c)

    coll = bpy.data.collections.new(COLL)
    bpy.context.scene.collection.children.link(coll)

    bpy.ops.mesh.primitive_grid_add(x_subdivisions=180, y_subdivisions=180,
                                    size=1.0)
    ob = bpy.context.active_object
    ob.name = "RELIEFCTL_Plate"
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    coll.objects.link(ob)

    # GEOMETRY ARM. The positive is displaced by a procedural function; the
    # negative is left flat. relief_audit's second layer reads mesh dihedral
    # angles, and a shader-only control could never exercise it.
    if linked:
        import math
        me = ob.data
        for v in me.vertices:
            x, y = v.co.x, v.co.y
            v.co.z = (0.0040 * math.sin(x * 220.0) * math.cos(y * 190.0)
                      + 0.0015 * math.sin(x * 610.0 + y * 550.0))
        me.update()

    mat = bpy.data.materials.new("RELIEFCTL_Mat")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]

    tex = nt.nodes.new("ShaderNodeTexNoise")
    tex.location = (-800, -200)
    tex.inputs["Scale"].default_value = 240.0
    tex.inputs["Detail"].default_value = 6.0
    tex.inputs["Roughness"].default_value = 0.55

    bump = nt.nodes.new("ShaderNodeBump")
    bump.location = (-400, -200)
    bump.inputs["Strength"].default_value = 0.85
    bump.inputs["Distance"].default_value = 0.004

    if linked:
        nt.links.new(tex.outputs["Fac"], bump.inputs["Height"])
    # THE NEGATIVE ARM'S WHOLE CONTENT IS THIS ONE MISSING LINK. `Height` keeps
    # its default constant, which is a legal value and leaves no other trace --
    # the shape R2-072's commit message calls out as having no artefact
    # signature at all.
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    ob.data.materials.append(mat)

    bpy.ops.wm.save_as_mainfile(filepath=out_path)
    print("[relief_ctl] wrote %s (linked=%s)" % (out_path, linked))


def _audit(blend, out_json):
    r = subprocess.run(
        [BLENDER, "-b", blend, "--factory-startup", "-P",
         os.path.join(HERE, "relief_audit.py"), "--",
         "--item", ITEM, "--collection", COLL, "--out", out_json],
        capture_output=True, text=True, timeout=900)
    if not os.path.exists(out_json):
        return None, (r.stdout + r.stderr)[-2000:]
    return json.load(open(out_json)), r.stdout[-800:]


def selftest():
    ok = True
    d = tempfile.mkdtemp(prefix="reliefctl_")
    print("=" * 78)
    print("RELIEF AUDIT CONTROL -- both arms built from live node types, here")
    print("=" * 78)
    arms = {}
    for name, linked in (("POSITIVE", True), ("NEGATIVE", False)):
        b = os.path.join(d, "%s.blend" % name.lower())
        r = subprocess.run(
            [BLENDER, "-b", "--factory-startup", "-P", __file__, "--",
             "--build", b, "--linked" if linked else "--unlinked"],
            capture_output=True, text=True, timeout=900)
        if not os.path.exists(b):
            print("[%s] BUILD FAILED\n%s" % (name, (r.stdout + r.stderr)[-1500:]))
            return 2
        j, tail = _audit(b, os.path.join(d, "%s.json" % name.lower()))
        if j is None:
            print("[%s] relief_audit produced no JSON\n%s" % (name, tail))
            return 2
        arms[name] = j
        print("\n[%s CONTROL]  bump stages %s   height unlinked %s   "
              "m_max %s   m_sum %s"
              % (name, j.get("bump_stages"), j.get("bump_height_unlinked"),
                 j.get("m_max"), j.get("m_sum")))

    p, n = arms["POSITIVE"], arms["NEGATIVE"]
    if (p.get("bump_stages") or 0) >= 1 and not p.get("bump_height_unlinked") \
            and (p.get("m_max") or 0) > 0:
        print("  => POSITIVE PASSES: a procedural texture on Height is FOUND, "
              "and it is reported with a non-zero m.")
    else:
        print("  => POSITIVE FAILS: the audit cannot see relief that is there. "
              "Nothing else it reports means anything.")
        ok = False

    if (n.get("bump_height_unlinked") or 0) >= 1 and (n.get("m_max") or 0) == 0:
        print("  => NEGATIVE PASSES: the one missing Height link is named as "
              "unlinked, and no relief is invented.")
    else:
        print("  => NEGATIVE FAILS: a Bump with a constant Height was not "
              "reported as unlinked (m_max %s)." % n.get("m_max"))
        ok = False

    print("\n[DISCRIMINATION] positive m_max %s  vs  negative m_max %s"
          % (p.get("m_max"), n.get("m_max")))
    if (p.get("m_max") or 0) > (n.get("m_max") or 0):
        print("  => the two arms SEPARATE. This is an instrument.")
    else:
        print("  => the two arms did not separate. Re-running the sweep would "
              "republish 28 numbers from something that is not measuring.")
        ok = False

    print("=" * 78)
    print(">> STAGE RESULT: %s" % ("RELIEF_AUDIT_DISCRIMINATES" if ok
                                   else "RELIEF_AUDIT_CONTROL_FAIL"))
    return 0 if ok else 1


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if "--build" in argv:
        _build(argv[argv.index("--build") + 1], "--linked" in argv)
        return 0
    if "--selftest" in argv or not argv:
        return selftest()
    print("usage: --selftest   (or --build PATH --linked|--unlinked)")
    return 2


if __name__ == "__main__":
    sys.exit(main())
