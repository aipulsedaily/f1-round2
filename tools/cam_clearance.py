"""How close the camera gets to the room, in metres. R2-064's local check.

    /opt/blender-5.2.0-linux-x64/blender -b <showroom.blend> --factory-startup \
        -P tools/cam_clearance.py -- --campath <path.json> --lo 755 --hi 864 \
        --out <clearance.json>

`tools/placement_gate.py` is the real keep-out gate and it must be run against
the ASSEMBLED world; run against a showroom-only scene it reports the car's own
parts inside the road corridor, because at those frames the car is out on the
lap and there is no world for it to be on. That is a wrong-scene answer, not a
result, and this is not a substitute for it.

What this DOES answer, on the scene beat 2 actually plays in: how close the
camera passes to the showroom's geometry. Triangle-level, on the EVALUATED
meshes so modifiers count, with the car and its children excluded by name
because the camera is deliberately close to the car and that distance is the
shot. Reported per frame, minimum and where.
"""
import argparse, json, os, sys
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--campath", required=True)
ap.add_argument("--lo", type=int, default=755)
ap.add_argument("--hi", type=int, default=864)
ap.add_argument("--radius", type=float, default=0.60,
                help="the camera sphere. placement_gate uses 1.20 m for a "
                     "camera at 100 m/s outdoors; inside a showroom at 9 m/s "
                     "the lens hood is the thing that matters")
ap.add_argument("--out")
a = ap.parse_args(argv)

dg = bpy.context.evaluated_depsgraph_get()
car = set()
root = bpy.data.objects.get("CAR_ROOT")
if root is not None:
    stack = [root]
    while stack:
        o = stack.pop()
        car.add(o.name)
        stack += list(o.children)
print(f">> excluding {len(car)} car objects (CAR_ROOT and its children)")

verts, tris, owner = [], [], []
n_obj = 0
for ob in bpy.context.scene.objects:
    if ob.type != "MESH" or ob.name in car or ob.hide_render:
        continue
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    if me is None or not len(me.polygons):
        ev.to_mesh_clear()
        continue
    base = len(verts)
    m = ob.matrix_world
    verts += [m @ v.co for v in me.vertices]
    for p in me.polygons:
        vi = list(p.vertices)
        for i in range(1, len(vi) - 1):
            tris.append((base + vi[0], base + vi[i], base + vi[i + 1]))
            owner.append(ob.name)
    ev.to_mesh_clear()
    n_obj += 1
print(f">> BVH over {n_obj} room objects, {len(verts)} verts, {len(tris)} tris")
if not tris:
    print(">> FAIL: no room geometry found; this measures nothing")
    print(">> STAGE RESULT: CAM_CLEARANCE_VACUOUS")
    sys.exit(1)
bvh = BVHTree.FromPolygons(verts, tris)

P = {e["f"]: e for e in json.load(open(a.campath))["path"]}
rows = []
for f in range(a.lo, a.hi + 1):
    if f not in P:
        continue
    p = Vector(P[f]["p"])
    loc, nor, idx, dist = bvh.find_nearest(p)
    name = owner[idx] if idx is not None and idx < len(owner) else "?"
    # IN FRONT OF THE LENS OR BEHIND IT. find_nearest is a sphere; a wall
    # 0.13 m behind the camera is not in the picture, and calling that a
    # near-miss on a shot would be the wrong quantity again.
    q = P[f]["q"]
    w, x, y, z = q
    fwd = Vector((-2 * (x * z + w * y), -2 * (y * z - w * x),
                  -(1 - 2 * (x * x + y * y)))).normalized()
    ahead = (Vector(loc) - p).normalized().dot(fwd) if dist > 1e-9 else 0.0
    rows.append((f, float(dist), [round(v, 3) for v in loc], name,
                 round(float(ahead), 3)))
worst = min(rows, key=lambda r: r[1])
print(f"=== CAMERA CLEARANCE, frames {a.lo}-{a.hi}")
for r in rows:
    if r[0] % 5 == 0 or r[0] == worst[0]:
        print(f"  f{r[0]:5d}  {r[1]:8.3f} m to {r[3]} at {r[2]}  "
              f"cos(to lens axis) {r[4]:+.2f}")
print(f"  MINIMUM {worst[1]:.3f} m at f{worst[0]}, to {worst[3]} at "
      f"{worst[2]}, cos(to lens axis) {worst[4]:+.2f}  (sphere {a.radius} m)")
if a.out:
    json.dump({"rows": rows, "min_m": worst[1], "min_f": worst[0],
               "radius": a.radius, "campath": os.path.abspath(a.campath)},
              open(a.out, "w"), indent=1)
ok = worst[1] > a.radius
print(">> STAGE RESULT: " + ("CAM_CLEARANCE_OK" if ok else "CAM_CLEARANCE_TIGHT"))
sys.exit(0 if ok else 1)
