"""R2-1061: what IS surface_test_filmpose.blend lit by? Read-only probe."""
import bpy, math, json, sys
sc = bpy.context.scene
print(">> SCENE", sc.name, "res", sc.render.resolution_x, sc.render.resolution_y)
vs = sc.view_settings
print(">> VIEW", vs.view_transform, "look", vs.look, "exposure %.4f" % vs.exposure,
      "gamma %.3f" % vs.gamma, "display", sc.display_settings.display_device)
print(">> ENGINE", sc.render.engine, "samples",
      getattr(sc.cycles, "samples", None))
print(">> OBJECTS n=%d" % len(bpy.data.objects))
for o in sorted(bpy.data.objects, key=lambda x: x.name):
    n = o.name
    extra = ""
    if o.type == "LIGHT":
        L = o.data
        d = (o.matrix_world.to_3x3() @ __import__("mathutils").Vector((0, 0, -1))).normalized()
        el = math.degrees(math.asin(max(-1, min(1, -d.z))))
        az = math.degrees(math.atan2(-d.y, -d.x))
        extra = ("type=%s energy=%.4f angle=%.5f color=%s sun_elev=%.3f sun_az=%.3f"
                 % (L.type, L.energy, getattr(L, "angle", -1),
                    tuple(round(c, 4) for c in L.color), el, az))
    elif o.type == "MESH":
        try:
            extra = "tris~%d mats=%s hide_render=%s" % (
                len(o.data.polygons), [m.name for m in o.data.materials][:4], o.hide_render)
        except Exception:
            extra = "mesh"
    elif o.type == "CAMERA":
        p = o.matrix_world.translation
        d = (o.matrix_world.to_3x3() @ __import__("mathutils").Vector((0, 0, -1))).normalized()
        extra = ("lens=%.3f loc=(%.2f,%.2f,%.2f) dir=(%.4f,%.4f,%.4f) fstop=%s focus=%s"
                 % (o.data.lens, p.x, p.y, p.z, d.x, d.y, d.z,
                    getattr(o.data.dof, "aperture_fstop", None),
                    getattr(o.data.dof, "focus_distance", None)))
    print("   %-42s %-8s %s" % (n, o.type, extra))
w = sc.world
print(">> WORLD", w.name if w else None)
if w and w.use_nodes:
    for nd in w.node_tree.nodes:
        print("     node %-28s %s" % (nd.name, nd.bl_idname))
print(">> STAGE RESULT: R21061_PROBE_OK")
