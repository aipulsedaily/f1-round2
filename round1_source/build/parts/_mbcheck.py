"""Deviation + sanity check for monocoque_b."""
import os
import sys, math, time
sys.path.insert(0, os.path.expanduser('~/opus5-car-render/build'))
sys.path.insert(0, os.path.expanduser('~/opus5-car-render/build/parts'))
import bpy, bmesh, importlib
from mathutils.bvhtree import BVHTree
from mathutils import Vector
import spec as S
import monocoque_b as M
importlib.reload(M)

for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
coll = bpy.data.collections.new("PART")
bpy.context.scene.collection.children.link(coll)
t0 = time.time()
objs = M.build(coll)
dt = time.time() - t0

tris = 0
for ob in objs:
    if ob.type == 'MESH':
        tris += len(ob.data.polygons)
print(">> built %d objects, %d polys in %.1f s" % (len(objs), tris, dt))
for ob in objs:
    if ob.type == 'MESH':
        print("     %-28s %7d" % (ob.name, len(ob.data.polygons)))

bm = bmesh.new()
for ob in objs:
    if ob.type == 'MESH':
        bm.from_mesh(ob.data)
tree = BVHTree.FromBMesh(bm)

APERTURE = set()
for x in (0.6, 0.3, 0.0):
    APERTURE.add((x, 0.92))

worst = 0.0
worst_ap = 0.0
rows = []
for x in [2.8,2.4,2.0,1.6,1.2,0.9,0.6,0.3,0.0,-0.4,-0.8,-1.2,-1.6,-2.0,-2.3]:
    for frac in [0.08,0.22,0.36,0.5,0.64,0.78,0.92]:
        y,z = S.body_surface_point(x, frac)
        for sy in (y,-y):
            loc,_,_,d = tree.find_nearest(Vector((x,sy,z)))
            if d is None: continue
            rows.append((d, x, frac))
            if (x,frac) in APERTURE:
                worst_ap = max(worst_ap, d)
            else:
                worst = max(worst, d)
rows.sort(reverse=True)
print(">> max deviation from spec surface (excluding cockpit aperture): %.4f m" % worst)
print(">> max deviation at cockpit-aperture sample points:              %.4f m" % worst_ap)
print(">> worst 12 samples:")
for (d,x,f) in rows[:12]:
    print("     x=%6.2f frac=%.2f  %6.2f mm" % (x,f,d*1000))
