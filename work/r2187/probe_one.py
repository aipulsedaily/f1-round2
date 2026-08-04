"""One shard, read three ways, at eight frames.  Is my instrument lying?"""
import sys
import numpy as np
import bpy

sc = bpy.context.scene
name = "GS_b04_00000"
o = None
for ob in sc.objects:
    if ob.name.startswith("GS_b04_"):
        o = ob
        break
print("probe object:", o.name)
fc = {}
ad = o.animation_data
for layer in ad.action.layers:
    for strip in layer.strips:
        cb = strip.channelbag(ad.action_slot)
        for f in cb.fcurves:
            fc.setdefault(f.data_path, {})[f.array_index] = f
loc = fc["location"]
print("n keys on location[0]:", len(loc[0].keyframe_points),
      "first", loc[0].keyframe_points[0].co[:], "last",
      loc[0].keyframe_points[-1].co[:])

for f in (845, 860, 866, 880, 900, 920, 1164, 1165, 1200):
    sc.frame_set(f)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = o.evaluated_get(dg)
    curve = tuple(round(loc[i].evaluate(f), 4) for i in range(3))
    print("f%-5d  orig.location %-34s  orig.matrix_world %-34s  eval %-34s  fcurve %s"
          % (f,
             tuple(round(v, 4) for v in o.location),
             tuple(round(v, 4) for v in o.matrix_world.translation),
             tuple(round(v, 4) for v in ev.matrix_world.translation),
             curve))
