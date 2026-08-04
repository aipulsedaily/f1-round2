"""R2-258 control: what mat_print's colour field ACTUALLY looks like at the
CADENCE fascia banner's own dimensions, UV layout, base colour and aux.

The Base Color chain is rewired to an Emission and viewed under Standard, so
this measures the texture and nothing else - no light, no normal, no exposure.
The plate is 44.0 x 1.60 m with uv = (u/44, v/1.6), which is exactly what
`emit_art` writes on the banner, so the uv-driven terms (ground-dirt gradient,
rain streaks, edge grime) are keyed the same way they are on the real object.
"""
import os
import sys

sys.path.insert(0, "/home/zany/f1-round2/world")
import numpy as np
import bpy
import build_dressing as BD

W_M, H_M = 44.0, 1.60
MPP = 0.005
OUT = "/home/zany/f1-round2/work/r2256"
AUX = (0.2783, 0.3578, 0.5, 0.6985)          # the real unit's age/dirt/variant/uid

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
BD.build_materials()
m = BD.MATS["Print"]
BR = BD.Brand(BD.BRAND_BY_NAME["CADENCE"])

nt = m.node_tree
bsdf = next(n for n in nt.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled")
out = next(n for n in nt.nodes if n.bl_idname == "ShaderNodeOutputMaterial")
src = bsdf.inputs["Base Color"].links[0].from_socket
em = nt.nodes.new("ShaderNodeEmission")
nt.links.new(src, em.inputs["Color"])
em.inputs["Strength"].default_value = 1.0
nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
print("rewired Base Color ->", src.node.bl_idname, "-> Emission")

me = bpy.data.meshes.new("plate")
me.from_pydata([(-W_M / 2, -H_M / 2, 0), (W_M / 2, -H_M / 2, 0),
                (W_M / 2, H_M / 2, 0), (-W_M / 2, H_M / 2, 0)], [], [(0, 1, 2, 3)])
me.validate()
uvl = me.uv_layers.new(name="UVMap")
for li, l in enumerate(me.loops):
    v = me.vertices[l.vertex_index].co
    uvl.data[li].uv = ((v[0] + W_M / 2) / W_M, (v[1] + H_M / 2) / H_M)
for nm, col in (("base", (BR.bg[0], BR.bg[1], BR.bg[2], 1.0)), ("aux", AUX)):
    ca = me.color_attributes.new(name=nm, type='FLOAT_COLOR', domain='CORNER')
    for d in ca.data:
        d.color = col
me.materials.append(m)
ob = bpy.data.objects.new("plate", me)
sc.collection.objects.link(ob)

cd = bpy.data.cameras.new("c")
cd.type = 'ORTHO'
cd.ortho_scale = W_M
cam = bpy.data.objects.new("c", cd)
cam.location = (0, 0, 10)
sc.collection.objects.link(cam)
sc.camera = cam

sc.render.engine = 'CYCLES'
sc.cycles.device = 'CPU'
sc.cycles.samples = 4
sc.cycles.use_denoising = False
sc.render.resolution_x = int(W_M / MPP)
sc.render.resolution_y = int(H_M / MPP)
sc.render.film_transparent = False
sc.render.use_motion_blur = False
sc.view_settings.view_transform = 'Standard'
sc.view_settings.look = 'None'
sc.render.image_settings.file_format = 'PNG'
sc.render.image_settings.color_depth = '16'
SCALE_MUL = float(os.environ.get("MOTTLE_MUL", "1.0"))
if SCALE_MUL != 1.0:
    # find the LARGE-SCALE MOTTLE noise: Object coords * 0.9 into a Noise at 2.0
    hits = []
    for nd in nt.nodes:
        if nd.bl_idname != "ShaderNodeTexNoise":
            continue
        if abs(nd.inputs["Scale"].default_value - 2.0) > 1e-6:
            continue
        lk = nd.inputs["Vector"].links
        if not lk:
            continue
        vm = lk[0].from_node
        if vm.bl_idname != "ShaderNodeVectorMath":
            continue
        v = vm.inputs[1].default_value
        if abs(v[0] - 0.9) < 1e-6:
            hits.append((vm, nd))
    assert len(hits) == 1, "expected exactly one mottle node, got %d" % len(hits)
    vm, nd = hits[0]
    vm.inputs[1].default_value = (0.9 * SCALE_MUL,) * 3
    print("MOTTLE rescaled x%.3f -> %.3f cyc/m" % (SCALE_MUL, 0.9 * SCALE_MUL * 2.0))
sc.render.filepath = os.path.join(OUT, os.environ.get("MOTTLE_OUT", "print_field.png"))
bpy.ops.render.render(write_still=True)
print("RENDERED %dx%d at %.4f m/px -> %s"
      % (sc.render.resolution_x, sc.render.resolution_y, MPP, sc.render.filepath))
print("CONTROL DONE")
