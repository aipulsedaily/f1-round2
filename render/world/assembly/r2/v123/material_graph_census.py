"""PER-MATERIAL GRAPH FINGERPRINT — the material-side analogue of
v120/vertex_fingerprint.py.

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup \
        -P work/r2100/material_graph_census.py -- <blend> <out.json>

WHY NOT THE EXISTING CENSUS.  `work/lighting/dressing_bump_census.py` counts
BUMP nodes, which is what the assembly6 -> assembly7 promotion turned on.  It
would be silent about a material whose roughness moved, whose texture scale
changed, or that gained a node somewhere else in its graph -- and this rebuild
runs `build_architecture` and `build_terrain` too, both of which have moved
since assembly7 was built.  "Only the nine DR_* materials differ" has to be a
MEASUREMENT over every material, not an inference from the one census that was
pointed at the one module that was expected to change.

This is the same discipline SHIPPING.md applies to geometry: a summary that
does not change is not evidence that nothing moved.  So: every material, every
node, every input default, every link, hashed.

Only MATERIAL datablocks are loaded (`bpy.data.libraries.load` pulls the
datablocks asked for plus their dependencies), so this costs seconds on a
4.2 GB assembly instead of the minutes a full open costs.

IT NEVER WRITES TO THE SUBJECT.  It is an instrument.
"""
import hashlib
import json
import os
import sys

import bpy

argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else []
blend, out = argv[0], argv[1]


def _val(v):
    """A socket default, canonicalised so float noise cannot masquerade as a
    change and a real move cannot hide in the rounding."""
    try:
        return [round(float(x), 9) for x in v]
    except TypeError:
        pass
    if isinstance(v, float):
        return round(v, 9)
    if isinstance(v, (int, bool, str)):
        return v
    return repr(v)


def graph_rows(nt):
    """Nodes and links, in a canonical order, with every addressable value."""
    nodes = []
    for n in sorted(nt.nodes, key=lambda x: (x.bl_idname, x.name)):
        ins = []
        for i, s in enumerate(n.inputs):
            d = None
            if hasattr(s, "default_value"):
                d = _val(s.default_value)
            ins.append([i, s.name, s.type, bool(s.links), d])
        props = {}
        for p in n.bl_rna.properties:
            if p.is_readonly or p.identifier in ("name", "label", "location",
                                                 "width", "height", "color",
                                                 "select", "parent"):
                continue
            try:
                props[p.identifier] = _val(getattr(n, p.identifier))
            except Exception:                                    # noqa: BLE001
                pass
        nodes.append({"name": n.name, "idname": n.bl_idname,
                      "inputs": ins, "props": props})
    links = sorted(
        "%s.%s -> %s.%s" % (l.from_node.name, l.from_socket.name,
                            l.to_node.name, l.to_socket.name)
        for l in nt.links)
    return nodes, links


with bpy.data.libraries.load(blend, link=False) as (src, dst):
    dst.materials = list(src.materials)

rows = {}
for mat in bpy.data.materials:
    nt = mat.node_tree
    if nt is None:
        rows[mat.name] = {"nodes": 0, "links": 0, "hash": "NO_NODE_TREE"}
        continue
    nodes, links = graph_rows(nt)
    blob = json.dumps({"n": nodes, "l": links}, sort_keys=True,
                      separators=(",", ":")).encode()
    rows[mat.name] = {
        "nodes": len(nodes),
        "links": len(links),
        "node_types": sorted(set(n["idname"] for n in nodes)),
        "hash": hashlib.sha1(blob).hexdigest()[:16],
        "graph": blob.decode(),            # kept, so a diff can say WHAT moved
    }

payload = {
    "blend": os.path.abspath(blend),
    "blend_bytes": os.path.getsize(blend),
    "materials": len(rows),
    "rows": rows,
}
with open(out, "w") as fh:
    json.dump(payload, fh, indent=1)
print(">> %s: %d materials, census -> %s"
      % (os.path.basename(blend), len(rows), out))
print("STAGE RESULT: MATERIAL_GRAPH_CENSUS_WRITTEN")
