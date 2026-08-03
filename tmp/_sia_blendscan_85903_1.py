
import bpy, json, sys

NORMAL_SINKS = ['Coat Normal', 'Displacement', 'Height', 'Normal', 'Tangent']
RELIEF_NODES = ['ShaderNodeBump', 'ShaderNodeNormalMap', 'ShaderNodeBevel']
SHADER_SINK_TYPES = ['ShaderNodeAddShader', 'ShaderNodeAmbientOcclusion', 'ShaderNodeBackground', 'ShaderNodeDisplacement', 'ShaderNodeEmission', 'ShaderNodeHoldout', 'ShaderNodeMixShader', 'ShaderNodeOutputLight', 'ShaderNodeOutputMaterial', 'ShaderNodeOutputWorld', 'ShaderNodeSubsurfaceScattering', 'ShaderNodeVectorDisplacement', 'ShaderNodeVolumeAbsorption', 'ShaderNodeVolumePrincipled', 'ShaderNodeVolumeScatter']
SHADER_SINK_PREFIX = 'ShaderNodeBsdf'


def _is_shader_sink(nd):
    return (nd.bl_idname in SHADER_SINK_TYPES
            or nd.bl_idname.startswith(SHADER_SINK_PREFIX))


def _f(sock):
    try:
        return float(sock.default_value)
    except Exception:
        return None


def _shell(nt):
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
                "shell": _shell(nt)})
        for l in links:
            if l.to_socket.name in NORMAL_SINKS:
                continue
            if _is_shader_sink(l.to_node):
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
                    "shell": _shell(nt)})
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
                    "shell": _shell(nt)})
        if nd.bl_idname == "ShaderNodeBump":
            if "Height" in nd.inputs and not nd.inputs["Height"].is_linked:
                findings.append({
                    "rule": "BUMP_HEIGHT_UNLINKED", "kind": kind,
                    "owner": owner, "node": nd.name, "node_type": nd.bl_idname,
                    "detail": "Height is a constant (%r): no gradient, so no "
                              "relief whatever Strength says"
                              % _f(nd.inputs["Height"]),
                    "shell": _shell(nt)})
            if ("Filter Width" in nd.inputs
                    and nd.inputs["Filter Width"].is_linked):
                findings.append({
                    "rule": "BUMP_FILTER_WIDTH_DRIVEN", "kind": kind,
                    "owner": owner, "node": nd.name, "node_type": nd.bl_idname,
                    "detail": "Filter Width is driven by %s -- that is where a "
                              "height lands when Bump is addressed by index"
                              % nd.inputs["Filter Width"].links[0].from_node.bl_idname,
                    "shell": _shell(nt)})


def run():
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




open(sys.argv[-1], "w").write(json.dumps(run(), indent=1))
