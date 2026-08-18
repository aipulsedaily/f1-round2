"""R2-1061: asphalt BSDF + camera/sun geometry of the test rig. Read-only."""
import bpy, math
from mathutils import Vector
sc = bpy.context.scene
sun = bpy.data.objects["TEST_Sun"]
sd = (sun.matrix_world.to_3x3() @ Vector((0, 0, -1))).normalized()
L = -sd                                      # direction TO the sun
print(">> SUN energy=%.4f color=%s dir_to_sun=(%.5f,%.5f,%.5f) elev=%.3f" %
      (sun.data.energy, tuple(round(c,4) for c in sun.data.color), L.x, L.y, L.z,
       math.degrees(math.asin(L.z))))
w = sc.world
bg = w.node_tree.nodes["Background"]
sky = w.node_tree.nodes["Sky Texture"]
print(">> SKY strength=%.4f type=%s" % (bg.inputs["Strength"].default_value, sky.sky_type))
for k in ("sun_elevation","sun_rotation","sun_intensity","sun_size","turbidity",
          "ground_albedo","altitude","air_density","dust_density","ozone_density",
          "sun_disc"):
    if hasattr(sky, k):
        v = getattr(sky, k)
        print("     sky.%-16s %s" % (k, round(v,5) if isinstance(v,float) else v))
m = bpy.data.materials["M_Surf_Asphalt"]
print(">> MATERIAL", m.name)
def walk(nt, ind="   "):
    for n in nt.nodes:
        vals = []
        for i in n.inputs:
            if not i.is_linked and hasattr(i, "default_value"):
                dv = i.default_value
                try:
                    dv = tuple(round(float(x),4) for x in dv)
                except TypeError:
                    dv = round(float(dv),4) if isinstance(dv,(int,float)) else dv
                vals.append("%s=%s" % (i.name, dv))
        links = ["%s<-%s.%s" % (i.name, i.links[0].from_node.name, i.links[0].from_socket.name)
                 for i in n.inputs if i.is_linked]
        print("%s%-30s %-28s %s | %s" % (ind, n.name, n.bl_idname, " ".join(vals)[:150], " ".join(links)[:160]))
walk(m.node_tree)
tg = bpy.data.materials.get("TEST_GroundMat")
if tg and tg.use_nodes:
    print(">> TEST_GroundMat"); walk(tg.node_tree)
for f in ("f2225","f2000","f1226","f1547"):
    cam = bpy.data.objects["CAM_filmpose_"+f]
    p = cam.matrix_world.translation
    d = (cam.matrix_world.to_3x3() @ Vector((0,0,-1))).normalized()
    # angle between view dir and sun dir (forward scatter if small)
    ang = math.degrees(math.acos(max(-1,min(1, d.dot(-L)))))
    print(">> CAM %s loc=(%.2f,%.2f,%.2f) dir=(%.4f,%.4f,%.4f) lens=%.2f pitch=%.2f  angle(view,awayfromsun)=%.2f"
          % (f,p.x,p.y,p.z,d.x,d.y,d.z,cam.data.lens, math.degrees(math.asin(-d.z)), ang))
print(">> STAGE RESULT: R21061_MAT_OK")
