#!/usr/bin/env python3
"""THE ARTEFACT SCAN, as one importable rule set.  R2-070 / R2-072.

`tools/socket_index_audit.py --blend` carried these rules as a SOURCE STRING
that it wrote to a temp file and handed to a fresh Blender.  That worked, and
it had exactly one consumer: a human typing the command.  R2-071's rule --
*a source fix is not landed until the artefact downstream of it has been
rebuilt and re-read* -- needs the read to happen inside something that runs on
its own, and the only thing that opens an item's built blend as a matter of
course is `tools/item_gate.py`.

A guard whose rules live in a string can only be run by spawning Blender.
`item_gate` is ALREADY inside Blender with the blend open, so spawning a
second one to reopen a 2.4 GB file would be absurd.  Hence this module: the
rules, once, importable both ways.

  * `socket_index_audit.py --blend x.blend` bootstraps this module inside the
    Blender it spawns.
  * `item_gate.py` imports it directly and calls `scan_open_blend()` on the
    scene it is already holding.

NOTHING HERE IMPORTS bpy AT MODULE LEVEL, so the constants can be read (and
the module linted) by a plain interpreter.  `scan_open_blend()` needs bpy and
imports it when called.

WHAT IT DETECTS
---------------
  RELIEF_INTO_NON_NORMAL   FAIL  a Bump / Normal Map / Bevel output landing on
                                 a SHADING node's non-normal input.  On 5.2
                                 the `Normal` off-by-one puts it on `Thin
                                 Wall`.  This is R2-057 / R2-070 seen from the
                                 far end.
  RELIEF_ORPHANED          FAIL  a relief node whose output goes nowhere -- the
                                 same defect when the stray index runs off the
                                 end of the socket list and the link is
                                 silently dropped.
  BUMP_HEIGHT_UNLINKED     FAIL  R2-038: `Height` on a constant.  No gradient,
                                 so no relief whatever Strength says.
  BUMP_FILTER_WIDTH_DRIVEN FAIL  R2-038's other half: a texture in `Filter
                                 Width`, which is where the height lands when
                                 the Bump node is addressed one socket short.
  RELIEF_INTO_COMPUTATION  NOTE  a relief output reaching a Vector/Math/Mix
                                 node.  This is the edge-wear idiom and it is
                                 CORRECT -- see below.

THE IDIOM THAT MUST NOT FAIL
----------------------------
The first version of this rule failed `armco_w_beam.mat_wbeam`:

    bev    = t.bevel(0.0035, 10)
    facing = t.vmath("DOT_PRODUCT", bev, (NewGeometry, 1))   # 1 = Normal

a bevelled normal dotted with the true geometry normal -- the standard way to
build an edge-wear mask, and entirely correct.  A rule that fails a shipped,
deliberate idiom gets switched off within a day, and a guard that is switched
off catches nothing.  So THE SINK DECIDES THE SEVERITY: a relief output on a
non-normal input of a SHADING node cannot be anything but a miswire, because
those sockets do not take a normal; a relief output on a Vector/Math/Mix node
is somebody computing with it.  The first FAILS, the second is a NOTE.
Nothing is dropped -- the distinction is reported, not hidden.
"""

from __future__ import annotations

# Sockets a normal-producing node is ALLOWED to drive.  Deliberately short.
NORMAL_SINKS = {
    "Normal",            # every BSDF
    "Coat Normal",       # Principled's coat layer
    "Height",            # Bump -> Bump chaining (the previous stage's normal)
    "Tangent",           # anisotropy chains
    "Displacement",
}

RELIEF_NODES = ("ShaderNodeBump", "ShaderNodeNormalMap", "ShaderNodeBevel")

SHADER_SINK_TYPES = {
    "ShaderNodeOutputMaterial", "ShaderNodeOutputWorld", "ShaderNodeOutputLight",
    "ShaderNodeEmission", "ShaderNodeBackground", "ShaderNodeHoldout",
    "ShaderNodeSubsurfaceScattering", "ShaderNodeVolumeScatter",
    "ShaderNodeVolumeAbsorption", "ShaderNodeVolumePrincipled",
    "ShaderNodeMixShader", "ShaderNodeAddShader",
    "ShaderNodeDisplacement", "ShaderNodeVectorDisplacement",
    "ShaderNodeAmbientOcclusion",
}
SHADER_SINK_PREFIX = "ShaderNodeBsdf"

# The rules that FAIL.  Anything else this module emits is a NOTE.
FAILING_RULES = ("RELIEF_INTO_NON_NORMAL", "RELIEF_ORPHANED",
                 "BUMP_HEIGHT_UNLINKED", "BUMP_FILTER_WIDTH_DRIVEN")


def is_shader_sink(nd):
    return (nd.bl_idname in SHADER_SINK_TYPES
            or nd.bl_idname.startswith(SHADER_SINK_PREFIX))


def _f(sock):
    try:
        return float(sock.default_value)
    except Exception:                                        # noqa: BLE001
        return None


def shell_state(nt):
    """Transmission / subsurface / alpha / coat state of every Principled in
    this tree.  This is what decides whether a stray relief link is 'flat' or
    'a per-pixel shell flip', so it is measured, never assumed."""
    out = []
    for nd in nt.nodes:
        if nd.bl_idname != "ShaderNodeBsdfPrincipled":
            continue
        d = {"node": nd.name}
        for nm in ("Transmission Weight", "Subsurface Weight", "Alpha",
                   "Coat Weight", "Normal", "Thin Wall"):
            if nm in nd.inputs:
                s = nd.inputs[nm]
                d[nm] = {"linked": s.is_linked, "value": _f(s)}
        out.append(d)
    return out


def scan_tree(kind, owner, nt, findings):
    """Append every finding in one node tree to `findings`."""
    for nd in nt.nodes:
        if nd.bl_idname not in RELIEF_NODES:
            continue
        links = list(nd.outputs[0].links)
        if not links:
            findings.append({
                "rule": "RELIEF_ORPHANED", "severity": "FAIL", "kind": kind,
                "owner": owner,
                "node": nd.name, "node_type": nd.bl_idname,
                "detail": "%s output is not connected to anything" % nd.bl_idname,
                "shell": shell_state(nt)})
        for l in links:
            if l.to_socket.name in NORMAL_SINKS:
                continue
            if is_shader_sink(l.to_node):
                findings.append({
                    "rule": "RELIEF_INTO_NON_NORMAL", "severity": "FAIL",
                    "kind": kind,
                    "owner": owner, "node": nd.name, "node_type": nd.bl_idname,
                    "to_node": l.to_node.bl_idname,
                    "to_socket": l.to_socket.name,
                    "detail": "%s -> %s.%r. That is a shading node and %r "
                              "does not take a normal, so this is a miswire."
                              % (nd.bl_idname, l.to_node.bl_idname,
                                 l.to_socket.name, l.to_socket.name),
                    "shell": shell_state(nt)})
            else:
                findings.append({
                    "rule": "RELIEF_INTO_COMPUTATION", "severity": "NOTE",
                    "kind": kind,
                    "owner": owner, "node": nd.name, "node_type": nd.bl_idname,
                    "to_node": l.to_node.bl_idname,
                    "to_socket": l.to_socket.name,
                    "detail": "%s -> %s.%r -- computed with, not shaded "
                              "with. The edge-wear idiom (Bevel dotted with "
                              "the geometry normal) looks exactly like this."
                              % (nd.bl_idname, l.to_node.bl_idname,
                                 l.to_socket.name),
                    "shell": shell_state(nt)})
        if nd.bl_idname == "ShaderNodeBump":
            if "Height" in nd.inputs and not nd.inputs["Height"].is_linked:
                findings.append({
                    "rule": "BUMP_HEIGHT_UNLINKED", "kind": kind,
                    "owner": owner, "node": nd.name, "node_type": nd.bl_idname,
                    "detail": "Height is a constant (%r): no gradient, so no "
                              "relief whatever Strength says"
                              % _f(nd.inputs["Height"]),
                    "shell": shell_state(nt)})
            if ("Filter Width" in nd.inputs
                    and nd.inputs["Filter Width"].is_linked):
                findings.append({
                    "rule": "BUMP_FILTER_WIDTH_DRIVEN", "kind": kind,
                    "owner": owner, "node": nd.name, "node_type": nd.bl_idname,
                    "detail": "Filter Width is driven by %s -- that is where a "
                              "height lands when Bump is addressed by index"
                              % nd.inputs["Filter Width"].links[0].from_node.bl_idname,
                    "shell": shell_state(nt)})


def scan_open_blend():
    """Scan every material, world and node group in the OPEN blend.

    Requires bpy.  Returns the same dict shape the `--blend` arm has always
    produced, so `socket_index_audit.report_blend` reads either one."""
    import bpy                                               # noqa: PLC0415

    findings = []
    scanned = 0
    for m in bpy.data.materials:
        if m.use_nodes and m.node_tree:
            scanned += 1
            scan_tree("material", m.name, m.node_tree, findings)
    for w in bpy.data.worlds:
        if w.use_nodes and w.node_tree:
            scanned += 1
            scan_tree("world", w.name, w.node_tree, findings)
    for g in bpy.data.node_groups:
        scanned += 1
        scan_tree("node_group", g.name, g, findings)
    return {"blend": bpy.data.filepath, "scanned_trees": scanned,
            "blender": bpy.app.version_string, "findings": findings}


def failing(findings):
    """The findings that are a verdict rather than a note."""
    return [f for f in findings if f.get("severity") != "NOTE"]
