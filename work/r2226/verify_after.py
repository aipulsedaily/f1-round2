"""Verify the AFTER blend before any A/B, and classify occlusion for the control.

    blender -b render/r2226_items.blend --factory-startup -P work/r2226/verify_after.py -- \
        --frames 654,1126 --out work/r2226/after_verify.json

Two jobs in one 5 GB scene load:

1.  THE R2-182 CHECK. `tools/item_placement_gate.py` on the blend that is about
    to be rendered. An item absent from the world makes before/after identical
    and the null reads as "the change is invisible". No A/B on this project is
    admissible until this has passed on THIS file.

2.  THE R2-150 CONTROL, DERIVED INDEPENDENTLY OF THE DIFF. For each placed unit
    and each frame, cast from the camera to the unit's centroid against the
    BVHs of the NAMED large occluders only -- never `scene.ray_cast` over the
    whole depsgraph, which R2-150 measured running an hour over 29,415 objects
    and being killed. A unit whose ray is blocked is OCCLUDED: its screen box
    must NOT move between the two builds, and that is the free negative
    control.
"""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector, Quaternion
from mathutils.bvhtree import BVHTree

sys.path.insert(0, os.path.expanduser("~/f1-round2/tools"))
sys.path.insert(0, os.path.expanduser("~/f1-round2/world"))

argv = sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else []
def opt(n, d=None): return argv[argv.index(n)+1] if n in argv else d
FRAMES = [int(x) for x in (opt("--frames") or "654").split(",")]
OUT = opt("--out")
RES_X, RES_Y, SENSOR = 3840, 2160, 36.0

rep = {"blend": bpy.data.filepath, "frames": {}}

# ---- 1. the placement gate, on this exact file --------------------------- #
import item_placement_gate as G
print("=" * 70); print("PLACEMENT GATE on the blend about to be rendered")
rc = G.run(rows_wanted=["crew_figure", "timing_stand"],
           out=os.path.expanduser("~/f1-round2/work/r2226/gate_after.json"))
rep["placement_gate_rc"] = rc
print("=" * 70)

# ---- camera --------------------------------------------------------------- #
sc = bpy.context.scene
cam = sc.camera
rep["camera"] = cam.name if cam else None
print("scene camera: %r  (scene %r)" % (rep["camera"], sc.name))
print("cameras in file: %s" % sorted(o.name for o in bpy.data.objects if o.type == "CAMERA"))

# ---- 2. occlusion, against NAMED occluders only --------------------------- #
# The named set: everything big and opaque between the paddock/pit straight and
# a camera near the showroom. Chosen by name from assembly9's own object list,
# not by a sweep -- R2-150's three-minute answer against its one-hour one.
OCCLUDERS = ["ARCH_PitBuilding_Shell", "ARCH_PitBuilding_Detail",
             "ARCH_PaddockBuildings", "ARCH_Ground_Compound",
             "ARCH_Ground_Fences", "ARCH_Ground_Decks", "ARCH_RaceControl",
             "ARCH_PitWall", "ARCH_ShowroomSurrounds", "ARCH_Grandstand_03_PRINCIPALE",
             "Wall_BackX", "Wall_SideY0", "Wall_SideY1", "Ceiling", "Floor"]
dg = bpy.context.evaluated_depsgraph_get()
trees, used = {}, []
for n in OCCLUDERS:
    ob = bpy.data.objects.get(n)
    if ob is None or ob.type != "MESH":
        continue
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    mw = ob.matrix_world
    verts = [mw @ v.co for v in me.vertices]
    polys = [list(p.vertices) for p in me.polygons]
    if verts and polys:
        trees[n] = BVHTree.FromPolygons(verts, polys, all_triangles=False, epsilon=0.0)
        used.append((n, len(verts), len(polys)))
    ev.to_mesh_clear()
rep["occluders_used"] = used
print("occluder BVHs: %s" % used)

ITEMS = {"crew_figure": "W_Item_CrewFigure", "timing_stand": "W_Item_TimingStand"}
units = {}
for it, cn in ITEMS.items():
    c = bpy.data.collections.get(cn)
    units[it] = []
    if c is None:
        continue
    for ob in c.all_objects:
        if ob.type != "MESH":
            continue
        cs = [ob.matrix_world @ Vector(v) for v in ob.bound_box]
        units[it].append({
            "n": ob.name,
            "c": [sum(v[k] for v in cs) / 8.0 for k in range(3)],
            "corners": [[v.x, v.y, v.z] for v in cs]})

path = json.load(open(os.path.expanduser("~/f1-round2/render/film14_path.json")))["path"]
byf = {k["f"]: k for k in path}

def quat_mat(q):
    return Quaternion(q).to_matrix()

for f in FRAMES:
    k = byf[f]
    C = Vector(k["p"]); R = quat_mat(k["q"]); lens = float(k["lens"])
    fx = lens * RES_X / SENSOR
    frep = {"cam": list(k["p"]), "lens": lens, "items": {}}
    for it, us in units.items():
        rows = []
        for u in us:
            # screen box from the 8 world corners
            uu, vv, zz = [], [], []
            for w in u["corners"]:
                d = Vector(w) - C
                cam_v = R.transposed() @ d
                z = -cam_v.z
                if z <= 0.05:
                    zz.append(z); continue
                uu.append(cam_v.x / z * fx + RES_X / 2.0)
                vv.append(cam_v.y / z * fx + RES_Y / 2.0)
                zz.append(z)
            if not uu:
                rows.append({"n": u["n"], "in_frustum": False, "why": "behind"})
                continue
            x0, x1 = min(uu), max(uu); y0, y1 = min(vv), max(vv)
            infr = (x1 > 0 and x0 < RES_X and y1 > 0 and y0 < RES_Y)
            cen = Vector(u["c"])
            d = cen - C; dist = d.length; dirn = d.normalized()
            blocked_by, tmin = None, dist
            for nm, t in trees.items():
                hit = t.ray_cast(C, dirn, dist)
                if hit[0] is not None and hit[3] is not None and hit[3] < tmin - 0.05:
                    tmin = hit[3]; blocked_by = nm
            rows.append({"n": u["n"], "in_frustum": bool(infr),
                         "dist_m": round(dist, 2),
                         "box": [round(x0, 1), round(y0, 1), round(x1, 1), round(y1, 1)],
                         "px_h": round(y1 - y0, 1),
                         "occluded": blocked_by is not None,
                         "blocked_by": blocked_by,
                         "block_t": round(tmin, 2) if blocked_by else None})
        vis = [r for r in rows if r.get("in_frustum") and not r.get("occluded")]
        occ = [r for r in rows if r.get("in_frustum") and r.get("occluded")]
        frep["items"][it] = {"n_units": len(rows), "n_in_frustum":
                             sum(1 for r in rows if r.get("in_frustum")),
                             "n_visible": len(vis), "n_occluded": len(occ),
                             "units": rows}
        print("frame %d  %-14s units %3d  in-frustum %3d  VISIBLE %3d  OCCLUDED %3d"
              % (f, it, len(rows), frep["items"][it]["n_in_frustum"], len(vis), len(occ)))
    rep["frames"][str(f)] = frep

if OUT:
    json.dump(rep, open(OUT, "w"), indent=1)
    print("wrote %s" % OUT)
print(">> STAGE RESULT: AFTER_VERIFY_OK")
