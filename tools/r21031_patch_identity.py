import bpy, sys, json
from mathutils import Vector
import bpy_extras.object_utils as ou

RECTS = {
 "f2225": [("ROAD?", (1300, 950, 2300, 1450)), ("KERB ctrl", (2450, 1500, 2850, 1700)),
           ("RUNOFF?", (300, 1400, 1300, 1900)), ("ABcrop", (1300, 950, 1900, 1350))],
 "f1547": [("ROAD near", (1400, 1600, 2400, 2100)), ("ROAD mid", (2700, 1250, 3300, 1500))],
 "f2000": [("ROAD", (1400, 900, 2600, 1700))],
 "f1226": [("ROAD", (1200, 1100, 2400, 1800)), ("ABcrop", (1400, 1200, 2000, 1600))],
}
W, H = 3840, 2160
dg = bpy.context.evaluated_depsgraph_get()
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y = W, H
for f, rects in RECTS.items():
    cam = bpy.data.objects["CAM_filmpose_" + f]
    sc.camera = cam
    org = cam.matrix_world.translation
    for lab, (x0, y0, x1, y1) in rects:
        tally = {}
        N = 24
        for i in range(N):
            for j in range(N):
                px = x0 + (x1 - x0) * (i + 0.5) / N
                py = y0 + (y1 - y0) * (j + 0.5) / N
                # NDC with origin bottom-left
                ndc = Vector((px / W, 1.0 - py / H, 0.0))
                v = ou.world_to_camera_view  # noqa: F841  (kept for symmetry)
                fr = cam.data.view_frame(scene=sc)   # 4 corners at z=-1 in cam space
                tr, br, bl, tl = fr
                p = (bl + (br - bl) * ndc.x + (tl - bl) * ndc.y)
                d = (cam.matrix_world.to_3x3() @ p).normalized()
                hit, loc, nor, idx, ob, mw = sc.ray_cast(dg, org, d, distance=100000.0)
                if not hit:
                    key = "(sky)"
                else:
                    mat = None
                    try:
                        mat = ob.material_slots[ob.data.polygons[idx].material_index].name
                    except Exception:
                        pass
                    key = "%s / %s" % (ob.name, mat)
                tally[key] = tally.get(key, 0) + 1
        tot = sum(tally.values())
        top = sorted(tally.items(), key=lambda kv: -kv[1])[:4]
        print(">> %s %-10s  %s" % (f, lab,
              "  ".join("%s %.0f%%" % (k, 100.0 * v / tot) for k, v in top)))
print(">> STAGE RESULT: raycast_done")
