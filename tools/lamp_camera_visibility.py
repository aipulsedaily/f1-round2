"""IS ANY LAMP RENDERING AS A NAKED SOURCE IN THIS FRAME?

    blender -b <blend> --factory-startup -P tools/lamp_camera_visibility.py

In Cycles an area lamp with `visible_camera` set renders as a glowing
rectangle.  This showroom has three area lamps of 4.6 x 3.4 m, 5.0 x 3.4 m and
4.8 x 0.62 m hanging in mid-air at z 2.80 .. 4.60 with no fixture of any kind,
and two of them fall inside frame 1 of the film.  This checks the FLAG and the
FRUSTUM together, because either alone answers the wrong question: a lamp
outside the frame does not matter however visible it is, and a lamp in the
frame does not matter if it is invisible to camera rays.

Measured on the round-1 showroom: `visible_camera` is False on all 23
practicals and on SKY_Sun, so the answer is clean.  Kept because that is a
negative worth being able to re-take -- see R2-623.
"""
import os
import math, sys, json
import bpy
from mathutils import Vector

sc = bpy.context.scene
sc.frame_set(1)
cam = sc.camera
cd = cam.data
rx, ry = sc.render.resolution_x, sc.render.resolution_y
ar = rx / float(ry)
sw = cd.sensor_width
sw_eff, sh_eff = (sw, sw / ar) if ar >= 1 else (sw * ar, sw)
M = cam.matrix_world
R = M.to_3x3().inverted()
o = M.translation
hx = math.degrees(math.atan((sw_eff / 2.0) / cd.lens))
hy = math.degrees(math.atan((sh_eff / 2.0) / cd.lens))
print(">> frame 1: lens %.1f mm, half-angles %.2f deg h / %.2f deg v, cam %s"
      % (cd.lens, hx, hy, [round(v, 4) for v in o]))
rows = []
for ob in sc.objects:
    if ob.type != "LIGHT":
        continue
    ld = ob.data
    p = ob.matrix_world.translation
    v = R @ (p - o)                       # camera space, -Z forward
    if v.z >= 0:
        inside, ax, ay = False, None, None
    else:
        ax = math.degrees(math.atan2(v.x, -v.z))
        ay = math.degrees(math.atan2(v.y, -v.z))
        inside = abs(ax) <= hx and abs(ay) <= hy
    rows.append({"name": ob.name, "type": ld.type,
                 "visible_camera": bool(ob.visible_camera),
                 "size": [round(getattr(ld, "size", 0.0), 3),
                          round(getattr(ld, "size_y", 0.0), 3)],
                 "in_frame_1": bool(inside),
                 "az_deg": None if ax is None else round(ax, 2),
                 "el_deg": None if ay is None else round(ay, 2),
                 "dist_m": round((p - o).length, 2)})
bad = [r for r in rows if r["in_frame_1"] and r["visible_camera"]
       and r["type"] == "AREA" and max(r["size"]) > 1.0]
for r in sorted(rows, key=lambda d: (not d["in_frame_1"], d["name"])):
    print("   %-18s %-5s vis_cam=%-5s size %6.2f x %-5.2f  in_frame=%-5s "
          "az %+7s el %+7s  %5.1f m"
          % (r["name"], r["type"], r["visible_camera"], r["size"][0],
             r["size"][1], r["in_frame_1"], r["az_deg"], r["el_deg"],
             r["dist_m"]))
json.dump(rows, open(os.path.expanduser("~/f1-round2/work/ceiling/lampvis.json"), "w"), indent=1)
print(">> %d large AREA lamp(s) both camera-visible AND inside frame 1: %s"
      % (len(bad), [r["name"] for r in bad]))
print(">> STAGE RESULT: %s" % ("LAMPVIS_NAKED_SOURCE_IN_FRAME" if bad
                               else "LAMPVIS_CLEAN"))
