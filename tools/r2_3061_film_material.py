"""R2-3061: READ THE ROAD MATERIAL OUT OF THE RENDERED FILM ITSELF.

    blender -b --factory-startup -P tools/r2_3061_film_material.py -- \
        --blend render/film22.blend [--mat M_Surf_Asphalt]

THE QUESTION THIS ANSWERS, AND WHY THE RECORD CANNOT
----------------------------------------------------
`docs/NEXT-REBUILD.md` lists the asphalt relief re-budget under "Landed in
SOURCE, in no film blend". If that is true, the delivered film predates the fix,
nothing needs authoring, and the rebuild carries it. Three agents in one night
have already been sent to build something that already existed, so this is not a
question to answer from a document.

`bpy.data.libraries.load` pulls ONE datablock and its dependencies out of a
.blend without opening the scene, so the 10 GB film costs a seek and a few MB
rather than an hour and 10 GB of swap. The material that comes back is the one
Cycles shaded the delivered frames with, and its node tree can be walked for the
layers the re-budget added: `amp_field`, and the six meso structures that feed it.

It prints a wavelength census as well, because "the nodes are present" and "the
nodes are at the wavelengths the comment claims" are different questions and this
module has had a comment disagree with its own graph before.
"""
import argparse
import os
import sys

R2 = "/home/zany/f1-round2"
sys.path.insert(0, os.path.join(R2, "tools"))

import bpy                                            # noqa: E402

TEX = {"ShaderNodeTexNoise", "ShaderNodeTexVoronoi", "ShaderNodeTexWave"}

# The re-budget's own signature, as `world/build_surface.py` writes it.
#
# `_G.tag(name, sock)` sets `sock.node.LABEL = "DBG:" + name`, NOT the node's
# name. The first version of this file looked for node NAMES and reported
# "0/8 tags present, FILM_MISSING_REBUDGET" on a film that carries all eight --
# which would have sent this task off to re-author a material that was already
# there, the exact outcome the brief was written to prevent. The census below
# is what caught it: 38 textures at wavelengths identical to a fresh build is
# not what a missing re-budget looks like. Two independent readings of the same
# artefact, and the disagreement was the instrument.
REBUDGET_TAGS = ("amp_field", "chip_hi", "offline", "ravel", "screed", "craze",
                 "pluck", "h_hard")
TAG_PREFIX = "DBG:"


def coord_gain(sock, depth=0):
    if depth > 24 or sock is None or not sock.is_linked:
        return [(1.0, "unlinked")]
    n = sock.links[0].from_node
    t = n.bl_idname
    if t == "ShaderNodeTexCoord":
        return [(1.0, sock.links[0].from_socket.name)]
    if t == "ShaderNodeUVMap":
        return [(1.0, "uv:" + n.uv_map)]
    if t == "ShaderNodeVectorMath":
        if n.operation == "SCALE":
            k = abs(n.inputs["Scale"].default_value) or 1.0
            return [(g * k, lab) for g, lab in coord_gain(n.inputs[0], depth + 1)]
        return coord_gain(n.inputs[0], depth + 1)
    if t == "ShaderNodeCombineXYZ":
        out = []
        for ax, inp in zip("XYZ", n.inputs[:3]):
            if not inp.is_linked:
                continue
            m = inp.links[0].from_node
            if m.bl_idname == "ShaderNodeMath" and m.operation == "MULTIPLY":
                a, b = m.inputs[0], m.inputs[1]
                k = (b.default_value if not b.is_linked
                     else (a.default_value if not a.is_linked else 1.0))
                out.append((abs(k) or 1.0, "combine." + ax))
        return out or [(1.0, "combine")]
    for i in n.inputs:
        if i.type == "VECTOR" and i.is_linked:
            return coord_gain(i, depth + 1)
    return [(1.0, t)]


def reach_channels(nt):
    """{node: set of BSDF inputs it can reach}, by walking BACK from the BSDF.

    "There are textures at 69 mm and 48 mm" and "anything at 69 mm reaches the
    delivered pixel as a colour" are different claims, and only the second one
    is about what a luminance band-pass measures. A layer that reaches only
    `Normal` is a shading gradient that a 12.47 deg sun may or may not turn into
    contrast; a layer that reaches only an amplitude field for a sub-pixel
    stipple reaches the pixel as its local mean. Base Color is the channel a
    band-pass reads first, so it is worth knowing which octaves are in it.
    """
    bsdf = next((n for n in nt.nodes
                 if n.bl_idname == "ShaderNodeBsdfPrincipled"), None)
    if bsdf is None:
        return {}
    out = {}
    for chan in ("Base Color", "Roughness", "Normal", "Specular IOR Level",
                 "Anisotropic"):
        if chan not in bsdf.inputs or not bsdf.inputs[chan].is_linked:
            continue
        seen = set()
        stack = [bsdf.inputs[chan].links[0].from_node]
        while stack:
            n = stack.pop()
            if n in seen:
                continue
            seen.add(n)
            for i in n.inputs:
                for lk in i.links:
                    stack.append(lk.from_node)
        for n in seen:
            out.setdefault(n, set()).add(chan)
    return out


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--blend", required=True)
    ap.add_argument("--mat", default="M_Surf_Asphalt")
    a = ap.parse_args(argv)

    src = a.blend if os.path.isabs(a.blend) else os.path.join(R2, a.blend)
    with bpy.data.libraries.load(src, link=False) as (have, want):
        names = [m for m in have.materials]
        if a.mat not in names:
            cand = [m for m in names if "sphalt" in m or "Track" in m]
            raise SystemExit("no material %r in %s; candidates: %s"
                             % (a.mat, src, cand[:10]))
        want.materials = [a.mat]
    mat = bpy.data.materials[a.mat]
    nt = mat.node_tree
    print(">> pulled %r out of %s  (%d nodes, %d links)"
          % (mat.name, os.path.basename(src), len(nt.nodes), len(nt.links)))

    labels = {n.label for n in nt.nodes if n.label}
    have_tags = {t: (TAG_PREFIX + t) in labels for t in REBUDGET_TAGS}
    print("\n=== the R2-1031 re-budget's own tagged nodes, in the SHIPPED material ===")
    for t, ok in have_tags.items():
        print("   %-12s %s" % (t, "PRESENT" if ok else "ABSENT"))
    # THE CONTROL FOR THE CONTROL. A label test that finds nothing looks the same
    # whether the labels are absent or the test is looking in the wrong field.
    print("   [%d labelled nodes in the tree; a tag test that finds 0 of 8 in a "
          "tree with 0 labels is measuring itself]" % len(labels))

    chans = reach_channels(nt)
    SHORT = {"Base Color": "COLOR", "Roughness": "rough", "Normal": "normal",
             "Specular IOR Level": "spec", "Anisotropic": "aniso"}
    rows = []
    for n in nt.nodes:
        if n.bl_idname not in TEX or "Scale" not in n.inputs:
            continue
        sc = float(n.inputs["Scale"].default_value)
        ch = ",".join(sorted(SHORT[c] for c in chans.get(n, ()))) or "-- UNREACHED"
        for gain, lab in coord_gain(n.inputs.get("Vector")):
            k = sc * gain
            if k > 0:
                rows.append((1.0 / k, n.bl_idname.replace("ShaderNodeTex", ""),
                             n.name, lab, ch))
    rows.sort(reverse=True)
    print("\n=== wavelength census of the SHIPPED material (%d textures) ===" % len(rows))
    for lam, typ, nm, lab, ch in rows:
        print("   %9.1f mm  %-8s %-22s %-14s %s" % (lam * 1000, typ, nm[:22], lab, ch))

    inband = [r for r in rows if 0.040 <= r[0] <= 0.250]
    print("\n=== inside 40-250 mm (the band a 3.8 mm/px near-field frame puts in "
          "the 16-64 px @4K window): %d ===" % len(inband))
    for lam, typ, nm, lab, ch in inband:
        print("   %9.1f mm  %-8s %-22s %s" % (lam * 1000, typ, nm[:22], ch))
    col = [r for r in inband if "COLOR" in r[4]]
    print("   -> of those, %d reach Base Color: %s"
          % (len(col), ", ".join("%.0f mm" % (r[0]*1000) for r in col) or "NONE"))

    ok = all(have_tags.values())
    print("\n>> STAGE RESULT: %s  (%d/%d re-budget tags present in the RENDERED "
          "film's own material)"
          % ("FILM_CARRIES_REBUDGET" if ok else "FILM_MISSING_REBUDGET",
             sum(have_tags.values()), len(have_tags)))


main()
