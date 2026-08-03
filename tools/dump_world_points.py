"""Dump WORLD POSITIONS out of an assembled .blend as a voxelised surface sample.

    blender -b --factory-startup -P tools/dump_world_points.py -- \
        --blend render/world/assembly/r2/assembly2.blend \
        --out out/world_points.npz --cell 1.0 --cap 250000

WHY THIS EXISTS
---------------
`docs/item_manifest.json` carries 435 records x 19 fields and NOT ONE
COORDINATE.  Nothing else in the repository does either.  Every question of the
form "is this item ever in frame" has therefore been unanswerable, by anyone,
since the campaign was scoped -- which is exactly how a distance field with a
threshold on it came to be called `hero` for 343 items.

This produces the missing artefact: a point sample of every surface in the
assembled world, in world coordinates, labelled by the object that owns it.

WHAT IT IS AND IS NOT
---------------------
* It is a SURFACE sample, taken from evaluated mesh vertices after modifiers,
  transformed by `matrix_world`, then voxelised on a `--cell` metre grid so the
  density is bounded by area rather than by tessellation.  A 30 M-triangle road
  and a 300-triangle sign both come back at one point per cell.
* Objects over `--cap` cells are randomly subsampled and the KEPT FRACTION is
  recorded per object, so a downstream consumer can correct areas and can widen
  a splat radius to match the real spacing.  A cap that is silently applied is
  a measurement that silently lies about density.
* Instanced geometry (the 12 B-triangle vegetation layer) is NOT expanded.  The
  28,313 VEG objects are linked duplicates sharing 310 meshes, so each one is
  recorded as its own origin plus its world-space bounding box, which is what a
  tree is.  Particle/geometry-node children INSIDE those objects are not
  enumerated: that is stated here rather than discovered later.
* Vertices are not area-weighted.  A dense corner and a sparse span contribute
  one point per occupied cell either way -- which is the point of voxelising --
  but a cell containing only a single stray vertex is as present as a cell
  containing a face.  For frustum, distance and occlusion this is what we want.

OUTPUT (npz)
    pts     (M,3) float32  voxel centres, world metres
    obj     (M,)  int32    index into `names`
    names   (N,)  str      object names
    meta    json blob: per-object vert/tri counts, bbox, cells found, cells
            kept, keep fraction, collection, and the global totals
"""
import sys, os, json, time

import bpy
import numpy as np

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def opt(name, default=None):
    if name in argv:
        return argv[argv.index(name) + 1]
    return default


BLEND = opt("--blend")
OUT = opt("--out", "out/world_points.npz")
CELL = float(opt("--cell", "1.0"))
CAP = int(opt("--cap", "250000"))
SEED = int(opt("--seed", "20260802"))
# --base-mesh reads ob.data instead of the depsgraph-evaluated mesh. It misses
# anything a modifier adds (displacement, subdivision), and it is the only way
# this file opens at all on an 11 GB machine, so a run that uses it says so in
# its own output rather than passing for the evaluated sweep.
BASE_MESH = "--base-mesh" in argv
# A VEG object bigger than this ACROSS is a SCATTER HOST carrying merged
# ground cover, not one plant. MEASURED separation, not guessed: the
# largest single tree in this world has a bbox diagonal of 41 m (a mature
# oak, 33 m across and 22 m tall) and the smallest scatter host spans
# 2,020 m. 200 m sits in the middle of a 50x gap. A first pass used 20 m
# and swept 21,124 TREES into the scatter class, which is what a threshold
# picked from the wrong end of the gap does.
SCATTER_DIAG_M = float(opt("--scatter-diag", "200.0"))
# Vertices per voxelisation chunk. Bounds peak memory independently of
# mesh size; 4 M costs about 150 MB of working arrays.
CHUNK = int(opt("--chunk", "4000000"))

t0 = time.time()
print(f"[DWP] opening {BLEND}", flush=True)
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(BLEND))
print(f"[DWP] opened in {time.time() - t0:.1f}s  "
      f"objects={len(bpy.data.objects)} meshes={len(bpy.data.meshes)}", flush=True)

rng = np.random.default_rng(SEED)
dg = bpy.context.evaluated_depsgraph_get()

names, pts_all, obj_all, meta = [], [], [], []
veg_origin, veg_name, veg_bbox = [], [], []
scatter = []

scene_objs = list(bpy.context.scene.objects)
print(f"[DWP] scene objects {len(scene_objs)}", flush=True)


def bbox_world(ob):
    m = ob.matrix_world
    cs = np.array([list(m @ __import__("mathutils").Vector(c)) for c in ob.bound_box],
                  dtype=np.float64)
    return cs.min(axis=0), cs.max(axis=0)


t1 = time.time()
n_heavy = 0
n_scatter = 0
for oi, ob in enumerate(scene_objs):
    if ob.type != "MESH":
        continue
    nm = ob.name
    force_base = False
    if nm.startswith("VEG"):
        # Two very different things are called VEG in this world and telling
        # them apart by name alone is how a measurement goes quietly wrong:
        #
        #   * 27,968 TREE/HEDGE instances -- linked duplicates of 310 shared
        #     meshes, each a discrete plant a few metres across. Recorded as
        #     one origin + bbox, which is what a tree is.
        #   * 34 SCATTER HOSTS -- VEG_grass_fescue_F, VEG_shrub_bramble_L1,
        #     VEG_weed_nettle and friends. Their object ORIGIN is (0,0,0) but
        #     their mesh spans +-1,250 m and carries the 1.4 M grass clumps and
        #     38 k shrubs as merged geometry. Recording those as a point at the
        #     origin throws away the entire ground cover AND puts a phantom
        #     bramble inside the showroom, 2.4 m from the beat-1 lens.
        #
        # So the test is the world-space SIZE of the thing, not its name.
        lo, hi = bbox_world(ob)
        if float(np.linalg.norm(hi - lo)) <= SCATTER_DIAG_M:
            veg_origin.append(list(ob.matrix_world.translation))
            veg_bbox.append(list(lo) + list(hi))
            veg_name.append(nm)
            continue
        # A SCATTER HOST. Its geometry is NOT read: these 34 objects carry the
        # 1.21 BILLION triangles the census calls the evaluated layer, and the
        # float32 vertex buffer for one of them is 7 GB. What is recorded is its
        # extent and its size, and ground-cover items are mapped onto TER_Ground
        # and the verge/runoff surfaces instead -- which is where the grass
        # physically is. The cost is that the exact outline of each scatter type
        # is not measured; the benefit is that its screen presence is, because
        # the ground under it is sampled at 1 m everywhere.
        # Read its BASE mesh, never its evaluated one. The base mesh IS the
        # scatter point set -- 1,021,718 vertices for VEG_grass_fescue_H is
        # 1.02 M grass clump positions, and all 34 hosts together are 4.7 M
        # vertices, seconds of work. The EVALUATED mesh is those points with a
        # clump instanced onto every one of them, which is where the census's
        # 1.21 billion triangles live and which needed 7 GB for a single object
        # before it was killed. The positions are what this measurement wants;
        # the instanced blades are not.
        scatter.append({"name": nm, "verts": len(ob.data.vertices),
                        "bbox_min": [round(float(x), 2) for x in lo],
                        "bbox_max": [round(float(x), 2) for x in hi]})
        n_scatter += 1
        force_base = True
    else:
        force_base = False

    if BASE_MESH or (nm.startswith('VEG') and force_base):
        oe, me = None, ob.data
    else:
        oe = ob.evaluated_get(dg)
        try:
            me = oe.to_mesh()
        except Exception as exc:                   # noqa: BLE001
            print(f"[DWP] {nm}: to_mesh failed {exc!r}", flush=True)
            continue
    nv = len(me.vertices)
    ntri = len(me.polygons)
    if nv == 0:
        if oe is not None:
            oe.to_mesh_clear()
        continue
    # CHUNKED. The vegetation scatter hosts carry tens of millions of vertices
    # in one mesh, and doing this in one shot needs the float32 buffer, the
    # transformed copy, an int64 cell index and an int64 hash key all live at
    # once -- about 40 bytes a vertex, which took 10 of this machine's 11 GB on
    # a single object and got the process killed. Chunking bounds the peak at
    # CHUNK * 40 bytes regardless of how big the mesh is, and the unique-cell
    # set is merged across chunks so the answer is identical.
    M = np.array(ob.matrix_world, dtype=np.float32)      # 4x4 row-major
    R3, T3 = M[:3, :3].T, M[:3, 3]
    buf = np.empty(nv * 3, dtype=np.float32)             # 12 bytes a vertex
    me.vertices.foreach_get("co", buf)
    if oe is not None:
        oe.to_mesh_clear()
    v = buf.reshape(nv, 3)
    lo = hi = None

    def cellkey(q):
        return ((q[:, 0].astype(np.int64) + 40000) * 100000
                + (q[:, 1].astype(np.int64) + 40000)) * 100000 \
            + (q[:, 2].astype(np.int64) + 40000)

    parts = []
    for c0 in range(0, nv, CHUNK):
        w = v[c0:c0 + CHUNK] @ R3 + T3
        if lo is None:
            lo, hi = w.min(axis=0), w.max(axis=0)
        else:
            lo = np.minimum(lo, w.min(axis=0)); hi = np.maximum(hi, w.max(axis=0))
        q = np.floor(w / CELL).astype(np.int32)          # int32: +-2 G cells
        del w
        _, first = np.unique(cellkey(q), return_index=True)
        parts.append(q[first])
        del q
    del buf, v
    cells = parts[0] if len(parts) == 1 else np.vstack(parts)
    del parts
    _, f2 = np.unique(cellkey(cells), return_index=True)
    cells = cells[f2]
    n_found = cells.shape[0]
    keep = 1.0
    if n_found > CAP:
        sel = rng.choice(n_found, CAP, replace=False)
        cells = cells[sel]
        keep = CAP / float(n_found)
    centres = (cells.astype(np.float32) + 0.5) * CELL

    idx = len(names)
    names.append(nm)
    pts_all.append(centres)
    obj_all.append(np.full(centres.shape[0], idx, dtype=np.int32))
    meta.append({"name": nm, "verts": int(nv), "tris": int(ntri),
                 "cells_found": int(n_found), "cells_kept": int(centres.shape[0]),
                 "keep_fraction": round(float(keep), 6),
                 "bbox_min": [round(float(x), 3) for x in lo],
                 "bbox_max": [round(float(x), 3) for x in hi],
                 "colls": [c.name for c in ob.users_collection]})
    if nv > 2_000_000:
        n_heavy += 1
        print(f"[DWP] {nm}: {nv/1e6:.1f} M verts -> {n_found} cells "
              f"(kept {centres.shape[0]}, {time.time()-t1:.0f}s in)", flush=True)

print(f"[DWP] evaluated-layer sweep done in {time.time()-t1:.1f}s, "
      f"{len(names)} objects, {n_heavy} over 5 M verts", flush=True)

pts = np.concatenate(pts_all).astype(np.float32) if pts_all else np.zeros((0, 3), np.float32)
obj = np.concatenate(obj_all) if obj_all else np.zeros((0,), np.int32)

veg_origin = np.array(veg_origin, dtype=np.float32) if veg_origin else np.zeros((0, 3), np.float32)
veg_bbox = np.array(veg_bbox, dtype=np.float32) if veg_bbox else np.zeros((0, 6), np.float32)

summary = {
    "blend": os.path.abspath(BLEND),
    "cell_m": CELL, "cap_per_object": CAP, "seed": SEED,
    "base_mesh_only": BASE_MESH,
    "scatter_diag_m": SCATTER_DIAG_M,
    "veg_scatter_hosts_skipped": n_scatter,
    "scatter_hosts": scatter,
    "scene_objects": len(scene_objs),
    "evaluated_objects": len(names),
    "points": int(pts.shape[0]),
    "veg_objects": int(veg_origin.shape[0]),
    "total_verts": int(sum(m["verts"] for m in meta)),
    "total_tris": int(sum(m["tris"] for m in meta)),
    "seconds": round(time.time() - t0, 1),
    "objects": meta,
}

os.makedirs(os.path.dirname(os.path.abspath(OUT)) or ".", exist_ok=True)
np.savez_compressed(OUT, pts=pts, obj=obj,
                    names=np.array(names, dtype=object),
                    veg_origin=veg_origin, veg_bbox=veg_bbox,
                    veg_name=np.array(veg_name, dtype=object),
                    meta=json.dumps(summary))
print("[DWP] " + json.dumps({k: v for k, v in summary.items() if k != "objects"},
                            indent=1), flush=True)
print(f"[DWP] wrote {OUT} ({os.path.getsize(OUT)/1e6:.1f} MB)", flush=True)
