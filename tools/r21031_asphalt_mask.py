import bpy, sys, numpy as np
from mathutils import Vector

f = sys.argv[sys.argv.index("--") + 1]
W, H, S = 3840, 2160, 16          # S px per mask cell
sc = bpy.context.scene
sc.render.resolution_x, sc.render.resolution_y = W, H
cam = bpy.data.objects["CAM_filmpose_" + f]
sc.camera = cam
dg = bpy.context.evaluated_depsgraph_get()
org = cam.matrix_world.translation
fr = cam.data.view_frame(scene=sc)
tr, br, bl, tl = fr
R = cam.matrix_world.to_3x3()
mw, mh = W // S, H // S
m = np.zeros((mh, mw), dtype=np.uint8)
for j in range(mh):
    for i in range(mw):
        u = (i + 0.5) / mw
        v = 1.0 - (j + 0.5) / mh
        p = bl + (br - bl) * u + (tl - bl) * v
        d = (R @ p).normalized()
        hit, loc, nor, idx, ob, _ = sc.ray_cast(dg, org, d, distance=100000.0)
        if hit and ob.name == "SURF_Track":
            try:
                if ob.material_slots[ob.data.polygons[idx].material_index].name \
                        == "M_Surf_Asphalt":
                    m[j, i] = 1
            except Exception:
                pass
# largest all-ones axis-aligned rectangle (histogram method)
best = (0, None)
heights = np.zeros(mw, dtype=int)
for j in range(mh):
    heights = np.where(m[j] == 1, heights + 1, 0)
    stack = []
    for i in range(mw + 1):
        h = heights[i] if i < mw else 0
        start = i
        while stack and stack[-1][1] >= h:
            si, sh = stack.pop()
            area = sh * (i - si)
            if area > best[0]:
                best = (area, (si, j - sh + 1, i, j + 1))
            start = si
        stack.append((start, h))
a, rect = best
x0, y0, x1, y1 = [c * S for c in rect]
print(">> STAGE RESULT: PURE_ASPHALT_RECT %s %d %d %d %d  (%d x %d px, cover %.1f%%)"
      % (f, x0, y0, x1, y1, x1 - x0, y1 - y0, 100.0 * m.mean()))
