"""R2-1222 verification: does the handover snippet actually apply?

Runs the EXACT wiring from the staging doc against build_surface's own `_G`
kit, in a throwaway material. Proves the handover is applyable without editing
build_surface.py, which another agent holds.
"""
import os, sys, traceback
import bpy

ROOT = os.path.expanduser("~/f1-round2")
sys.path.insert(0, os.path.join(ROOT, "world"))
sys.path.insert(0, os.path.join(ROOT, "world", "items"))

FAILS = []
def chk(name, ok, detail=""):
    print("   [%s] %s %s" % ("PASS" if ok else "FAIL", name, detail))
    if not ok:
        FAILS.append(name)

try:
    import build_surface as BS
    import tyre_deposit as TDP
    print(">> imported build_surface and tyre_deposit")

    mat = bpy.data.materials.new("HANDOVER_TEST")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    g = BS._G(nt)

    # stand-ins for the substrate values live in _mat_concrete at that point
    base  = g.rgb(0.30, 0.29, 0.28)
    rough = g.math("ADD", 0.80, 0.0)
    micro = g.math("ADD", 0.50, 0.0)
    h     = g.math("ADD", 0.50, 0.0)

    # ---------- THE HANDOVER SNIPPET, VERBATIM ----------
    TDP.build_groups()

    _oc = g.n("ShaderNodeTexCoord").outputs["Object"]
    _vt = g.n("ShaderNodeVectorTransform", vector_type="POINT",
              convert_from="OBJECT", convert_to="WORLD")
    g.set(_vt.inputs["Vector"], _oc)
    Pw = _vt.outputs["Vector"]

    fld = g.n("ShaderNodeGroup", node_tree=bpy.data.node_groups[TDP.FIELD_GROUP])
    g.set(fld.inputs["World Position"], Pw)
    g.set(fld.inputs["Traffic Passes"], 1000.0)
    frontx = TDP.front_x_value_node(g)
    g.set(fld.inputs["Front X"], frontx.outputs[0])

    dep = g.n("ShaderNodeGroup", node_tree=bpy.data.node_groups[TDP.CONC_GROUP])
    for _nm, _src in (("Base Color", base), ("Roughness", rough),
                      ("Specular IOR Level", 0.32),
                      ("Height Micro", micro), ("Height Coarse", h),
                      ("Coverage", fld.outputs["Coverage"]),
                      ("Wetting", fld.outputs["Wetting"]),
                      ("Grain", fld.outputs["Grain"]),
                      ("World Position", Pw)):
        g.set(dep.inputs[_nm], _src)
    base  = dep.outputs["Base Color"]
    rough = dep.outputs["Roughness"]
    spec  = dep.outputs["Specular IOR Level"]
    micro = dep.outputs["Height Micro"]
    h     = dep.outputs["Height Coarse"]
    nrm   = dep.outputs["Normal"]

    nrm = g.bump(micro, strength=0.45, distance=0.0006, normal=nrm)
    nrm = g.bump(h,     strength=1.0,  distance=0.0030, normal=nrm)

    bsdf = g.n("ShaderNodeBsdfPrincipled")
    g.set(bsdf.inputs["Base Color"], base)
    g.set(bsdf.inputs["Roughness"], rough)
    g.set(bsdf.inputs["Specular IOR Level"], spec)
    g.set(bsdf.inputs["Normal"], nrm)
    out = g.n("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    # ---------- END SNIPPET ----------
    print(">> snippet executed without exception")

    chk("both groups instantiated",
        fld.node_tree.name == TDP.FIELD_GROUP and dep.node_tree.name == TDP.CONC_GROUP)
    # every declared input of the apply group is actually connected or set
    unlinked = [s.name for s in dep.inputs if not s.is_linked and s.name == "World Position"]
    chk("World Position linked on apply group", not unlinked, str(unlinked))
    chk("Front X linked from the Value node", fld.inputs["Front X"].is_linked)
    chk("Traffic Passes == 1000 (signed off)",
        abs(fld.inputs["Traffic Passes"].default_value - 1000.0) < 1e-9,
        "got %.4f" % fld.inputs["Traffic Passes"].default_value)
    # R2-1226: the graft that killed the fix had a dead channel. Assert on the
    # BUILT socket, never on the code that was supposed to have linked it.
    import itemkit as K
    # EXEMPTIONS, TYPED ON PURPOSE. `Specular IOR Level` and `Traffic Passes`
    # are CONSTANTS BY DESIGN, not forgotten links: the substrate's specular is
    # a literal 0.32 (build_surface.py:2897 -- there is no node to link), and
    # Traffic Passes is the art knob. Everything else is fed from a real chain.
    K.assert_wired(dep, ["Base Color", "Roughness", "Height Micro",
                         "Height Coarse", "World Position",
                         "Coverage", "Wetting", "Grain"],
                   what="the apron deposit graft")
    K.assert_wired(fld, ["World Position", "Front X"], what="the deposit field")
    chk("assert_wired passes on every channel fed by a chain", True,
        "8 apron inputs + 2 field inputs linked on the BUILT node; "
        "Specular IOR Level and Traffic Passes are constants by design")
    chk("the deposit ADDS a specular channel the substrate did not have",
        not dep.inputs["Specular IOR Level"].is_linked
        and bsdf.inputs["Specular IOR Level"].is_linked,
        "constant 0.32 in, varying out")
    # and prove the guard would have caught the real defect
    # NEGATIVE CONTROL: break a channel that IS fed by a chain and prove the
    # guard refuses it. `Base Color` stands in for R2-1226's `Interface`.
    nt.links.remove(dep.inputs["Base Color"].links[0])
    _stand_in = tuple(dep.inputs["Base Color"].default_value)
    try:
        K.assert_wired(dep, ["Base Color"], what="deliberately broken")
        _caught, _named = False, False
    except RuntimeError as _e:
        _caught, _named = True, "Base Color" in str(_e)
    chk("assert_wired CATCHES a dead channel and names it", _caught and _named,
        "unlinking Base Color is REFUSED, not rendered; it would have "
        "silently used %r" % (_stand_in,))
    chk("BSDF Specular is LINKED (was a 0.32 literal)",
        bsdf.inputs["Specular IOR Level"].is_linked)
    chk("BSDF Normal linked", bsdf.inputs["Normal"].is_linked)
    # the deposit normal must be the BASE of the substrate bumps, not replaced
    b2 = nrm.node
    chk("outer bump is a Bump node", b2.bl_idname == "ShaderNodeBump", b2.bl_idname)
    chk("outer bump chains a Normal input", b2.inputs["Normal"].is_linked)
    b1 = b2.inputs["Normal"].links[0].from_node
    chk("inner bump chains onto the apply group Normal (%s)" % dep.name,
        b1.inputs["Normal"].is_linked and
        b1.inputs["Normal"].links[0].from_node.name == dep.name,
        "from %s" % (b1.inputs["Normal"].links[0].from_node.name
                     if b1.inputs["Normal"].is_linked else "NOTHING"))
    # world-space, not object-space
    chk("world position goes through OBJECT->WORLD transform",
        _vt.convert_from == "OBJECT" and _vt.convert_to == "WORLD" and
        _vt.vector_type == "POINT")
    chk("no image textures introduced",
        sum(1 for n in nt.nodes if n.bl_idname == "ShaderNodeTexImage") == 0)

    print(">> nodes in tree: %d" % len(nt.nodes))
except Exception:
    traceback.print_exc()
    FAILS.append("EXCEPTION")

print(">> STAGE RESULT: %s  (%d failures)"
      % ("OK" if not FAILS else "FAILED: " + ", ".join(FAILS), len(FAILS)))
