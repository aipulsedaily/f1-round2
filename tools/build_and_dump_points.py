"""Build the world from its own modules and dump WORLD POSITIONS, in one job.

    blender -b --factory-startup -P tools/build_and_dump_points.py -- \
        --mods surface,barriers,architecture,terrain,dressing \
        --out out/world_points.npz --cell 1.0 --cap 250000 --budget 3200

WHY NOT JUST OPEN assembly2.blend
---------------------------------
Because it cannot be got onto the rented box.  `rq exec` stages a bundle with
`zstd -19` through one ssh pipe and gives up at 1,800 s
(`broker/execremote.py:232`).  `assembly2.blend` is 4.19 GB of largely
incompressible float data; the push was measured at a mean 1.6 MB/s of input
and reached 57 % at the 1,800 s mark.  It does not fit in the window.  Shipping
the MODULES instead is 8 MB and the same geometry comes out the other end,
because the world is procedural and the modules are the source of truth.

WHAT THIS CHANGES ABOUT THE ANSWER, STATED PLAINLY
--------------------------------------------------
`assembly2.blend` was built on 2026-07-29 against **world contract 1.0.1**.
This builds against whatever `world/world_contract.py` says TODAY, which is
**1.1.0**, in which `barrier_offset` moved by up to 51.99 m in places.  So the
positions here are the world AS THE MODULES NOW DESCRIBE IT, which is what the
next rebuild will produce and what the item campaign will be built against --
but they are NOT byte-identical to the assembly that currently sits on disk.
The contract version actually used is recorded in the output.  Barriers, catch
fencing and runoff are the parts this can move; the track, kerbs, buildings and
terrain are not on that constant.

Everything else -- the voxelisation, the per-object cap, the kept fraction, the
vegetation-instance handling -- is exactly `tools/dump_world_points.py`, and
the docstring there is the authority on what the point cloud is and is not.

WALL CLOCK
----------
`rq exec` hard-kills the child at `--timeout`, max 3,600 s.  The full assembly
took 995 s locally on 6 cores; the rented box is slower per core.  So this
extracts points after EVERY module rather than at the end, checks the clock
before starting the next one, and writes the npz as soon as the budget is
reached.  A run that only gets through three modules returns three modules'
positions and says so, which is a partial answer.  A run that is killed returns
nothing at all, which is not.
"""
import sys, os, json, time, gc, argparse

import bpy
import numpy as np
import mathutils

T0 = time.time()
WORLD = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "world"))
if WORLD not in sys.path:
    sys.path.insert(0, WORLD)

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument("--mods", default="surface,barriers,architecture,terrain,dressing")
ap.add_argument("--out", default="out/world_points.npz")
ap.add_argument("--cell", type=float, default=1.0)
ap.add_argument("--cap", type=int, default=250000)
ap.add_argument("--seed", type=int, default=20260802)
ap.add_argument("--budget", type=float, default=3200.0)
a = ap.parse_args(argv)

bpy.ops.wm.read_factory_settings(use_empty=True)
import world_contract as C                                          # noqa: E402
print(f"[BDP] world_contract v{C.__version__}", flush=True)

rng = np.random.default_rng(a.seed)
names, pts_all, obj_all, meta = [], [], [], []
veg_origin, veg_name, veg_bbox = [], [], []
scatter, scatter_pts, scatter_name = [], [], []

# A VEG object bigger than this ACROSS is a SCATTER HOST carrying merged ground
# cover, not a discrete plant.
#
# I ORIGINALLY WROTE 40.0 HERE AND CLAIMED IT WAS THE "same value and same
# reasoning as tools/dump_world_points.py". IT WAS NOT. The sibling's value is
# 200.0, and I asserted the two agreed without reading it. Measured on
# assembly6: the largest tree diagonal is 92.0 m and the smallest scatter host
# is 1485.5 m. 40 m sits BELOW THE TREE END of that gap, so the run classed
# 7,307 objects as scatter, of which 7,273 WERE TREES -- and because trees then
# went to `scatter_pts` instead of `veg_origin`, any tiering built on the output
# would have been short 2,012,911 points (66.5 %) and 7,273 vegetation instances
# (26.0 %), silently.
#
# The gap between 92 m and 1485.5 m is enormous, so the exact value is not
# delicate -- but it must not be guessed, and it must not drift from the
# sibling. So it is READ FROM THE SIBLING and cross-checked against the measured
# gap at runtime, rather than copied and hoped over.
def _sibling_scatter_diag(default=200.0):
    """Read SCATTER_DIAG_M's default out of tools/dump_world_points.py.

    Two tools that disagree about what counts as a scatter host disagree about
    what the world contains. Reading beats copying: a copy is a claim, and the
    claim was wrong once already.
    """
    import re as _re
    sib = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "dump_world_points.py")
    try:
        src = open(sib).read()
    except OSError:
        return default
    m = _re.search(r'--scatter-diag"\s*,\s*"([0-9.]+)"', src)
    return float(m.group(1)) if m else default


SCATTER_DIAG_M = _sibling_scatter_diag()

# This world has ~34 real scatter hosts. Anything above this is the threshold
# sweeping trees in, which is exactly what 40 m did (7,307 classified, 7,273 of
# them trees). Generous so a genuinely richer world does not trip it.
SCATTER_MAX_HOSTS = 200
seen = set()
mods_done, mods_failed, mods_skipped = [], {}, []


def bbox_world(ob):
    m = ob.matrix_world
    cs = np.array([list(m @ mathutils.Vector(c)) for c in ob.bound_box], dtype=np.float64)
    return cs.min(axis=0), cs.max(axis=0)


def harvest(tag):
    """Voxelise every mesh object that has appeared since the last call."""
    dg = bpy.context.evaluated_depsgraph_get()
    n_new = 0
    for ob in list(bpy.context.scene.objects):
        if ob.name in seen or ob.type != "MESH":
            continue
        seen.add(ob.name)
        n_new += 1
        nm = ob.name
        if nm.startswith("VEG"):
            # TWO VERY DIFFERENT THINGS ARE CALLED VEG, and telling them apart by
            # NAME is how this measurement went quietly wrong. Until 2026-08-02
            # this branch recorded `ob.matrix_world.translation` for every VEG
            # object. That is right for a tree and catastrophic for a scatter
            # host:
            #
            #   * TREE / HEDGE instances -- linked duplicates of shared meshes,
            #     each a discrete plant a few metres across. One origin + bbox is
            #     exactly what a tree is.
            #   * 34 SCATTER HOSTS -- VEG_grass_fescue_F, VEG_shrub_bramble_L1,
            #     VEG_weed_nettle and friends. Their object ORIGIN IS (0,0,0)
            #     while their mesh spans +-1,250 m and carries the ground cover
            #     as merged geometry. Recording those as a point at the origin
            #     throws away the ENTIRE ground cover AND plants a phantom
            #     bramble inside the showroom, 5.7 m from the beat-1 lens.
            #
            # So the test is the world-space SIZE of the thing, never its name.
            # Ported from tools/dump_world_points.py, which had this right and
            # is the reason the shipped tiering was not affected.
            lo, hi = bbox_world(ob)
            if float(np.linalg.norm(np.asarray(hi) - np.asarray(lo))) <= SCATTER_DIAG_M:
                veg_origin.append(list(ob.matrix_world.translation))
                veg_bbox.append(list(lo) + list(hi))
                veg_name.append(nm)
                continue
            # A SCATTER HOST. Read its BASE mesh, never its evaluated one: the
            # base mesh IS the scatter point set (one vertex per clump), while
            # the evaluated mesh is those points with a clump instanced onto
            # every one -- which is where the census's billion triangles live and
            # which needed 7 GB for a single object before it was killed.
            base = ob.data
            n_pts = len(base.vertices)
            co = np.empty(n_pts * 3, dtype=np.float64)
            base.vertices.foreach_get("co", co)
            co = co.reshape(-1, 3)
            M = np.array(ob.matrix_world, dtype=np.float64)
            co = co @ M[:3, :3].T + M[:3, 3]
            scatter.append({"name": nm, "verts": n_pts,
                            "bbox_min": [round(float(x), 2) for x in lo],
                            "bbox_max": [round(float(x), 2) for x in hi],
                            "diag_m": round(float(np.linalg.norm(
                                np.asarray(hi) - np.asarray(lo))), 2)})
            scatter_pts.append(co.astype(np.float32))
            scatter_name.append(nm)
            continue
        oe = ob.evaluated_get(dg)
        try:
            me = oe.to_mesh()
        except Exception as exc:                                    # noqa: BLE001
            print(f"[BDP] {nm}: to_mesh failed {exc!r}", flush=True)
            continue
        nv = len(me.vertices)
        if nv == 0:
            oe.to_mesh_clear()
            continue
        buf = np.empty(nv * 3, dtype=np.float32)
        me.vertices.foreach_get("co", buf)
        v = buf.reshape(nv, 3)
        M = np.array(ob.matrix_world, dtype=np.float32)
        w = v @ M[:3, :3].T + M[:3, 3]
        ntri = len(me.polygons)
        oe.to_mesh_clear()
        del buf, v

        q = np.floor(w / a.cell).astype(np.int64)
        key = (q[:, 0] + 40000) * 10_000_000_000 + (q[:, 1] + 40000) * 100000 + (q[:, 2] + 40000)
        _, first = np.unique(key, return_index=True)
        cells = q[first]
        n_found = cells.shape[0]
        keep = 1.0
        if n_found > a.cap:
            sel = rng.choice(n_found, a.cap, replace=False)
            cells = cells[sel]
            keep = a.cap / float(n_found)
        centres = (cells.astype(np.float32) + 0.5) * a.cell
        lo, hi = w.min(axis=0), w.max(axis=0)
        del w, q, key

        idx = len(names)
        names.append(nm)
        pts_all.append(centres)
        obj_all.append(np.full(centres.shape[0], idx, dtype=np.int32))
        meta.append({"name": nm, "module": tag, "verts": int(nv), "tris": int(ntri),
                     "cells_found": int(n_found), "cells_kept": int(centres.shape[0]),
                     "keep_fraction": round(float(keep), 6),
                     "bbox_min": [round(float(x), 3) for x in lo],
                     "bbox_max": [round(float(x), 3) for x in hi]})
        if nv > 3_000_000:
            print(f"[BDP] {nm}: {nv/1e6:.1f} M verts -> {n_found} cells "
                  f"(kept {centres.shape[0]})", flush=True)
    return n_new


MODS = [m for m in a.mods.split(",") if m]
for m in MODS:
    if time.time() - T0 > a.budget:
        mods_skipped.append(m)
        print(f"[BDP] SKIPPING {m}: {time.time()-T0:.0f}s of {a.budget}s budget used",
              flush=True)
        continue
    t = time.time()
    print(f"\n[BDP] building {m} at t+{time.time()-T0:.0f}s", flush=True)
    try:
        if m == "surface":
            import build_surface as B; s = B.build()
        elif m == "barriers":
            import build_barriers as B; s = B.build()
        elif m == "terrain":
            import build_terrain as B; s = B.build()
        elif m == "architecture":
            import build_architecture as B; s = B.build(verify=False)
        elif m == "dressing":
            import build_dressing as B; s = B.build()
        else:
            raise RuntimeError("unknown module " + m)
        bpy.context.view_layer.update()
        n_new = harvest(m)
        mods_done.append(m)
        print(f"[BDP] {m}: built in {time.time()-t:.0f}s, {n_new} new objects, "
              f"{len(names)} objects / {len(veg_origin)} veg so far", flush=True)
    except Exception as exc:                                        # noqa: BLE001
        import traceback
        traceback.print_exc()
        mods_failed[m] = repr(exc)
        print(f"[BDP] {m}: FAILED {exc!r}", flush=True)
    gc.collect()

pts = np.concatenate(pts_all).astype(np.float32) if pts_all else np.zeros((0, 3), np.float32)
obj = np.concatenate(obj_all) if obj_all else np.zeros((0,), np.int32)
vo = np.array(veg_origin, dtype=np.float32) if veg_origin else np.zeros((0, 3), np.float32)
vb = np.array(veg_bbox, dtype=np.float32) if veg_bbox else np.zeros((0, 6), np.float32)
sp = np.concatenate(scatter_pts).astype(np.float32) if scatter_pts else np.zeros((0, 3), np.float32)

# THE GUARD THAT WOULD HAVE CAUGHT THE ORIGINAL DEFECT.
# The bug this replaces recorded every scatter host as a point at (0,0,0) --
# 5.7 m from the beat-1 lens, inside the showroom. Any consumer reading that
# concluded the showroom was full of brambles at macro distance. So: refuse to
# write a file in which VEG origins cluster on the world origin.
_near_origin = int(np.sum(np.linalg.norm(vo, axis=1) < 1.0)) if vo.shape[0] else 0
if _near_origin > 2:
    raise SystemExit(
        f"[BDP] REFUSING TO WRITE: {_near_origin} VEG objects sit within 1 m of the "
        f"world origin. That is the scatter-host defect this tool was repaired for -- "
        f"a host's origin is (0,0,0) while its geometry spans the circuit. Recording "
        f"them as points puts phantom vegetation 5.7 m from the beat-1 lens. "
        f"SCATTER_DIAG_M ({SCATTER_DIAG_M} m) is TOO HIGH -- hosts are being kept as "
        f"points. Compare against the measured object sizes below.")

# THE GUARD ABOVE ONLY CATCHES A THRESHOLD SET TOO HIGH, AND THE ERROR THAT
# ACTUALLY HAPPENED WAS THE OTHER DIRECTION. With SCATTER_DIAG_M at 40 m the
# tool wrote a clean file -- 0 VEG origins near the origin, guard silent -- while
# misclassifying 7,273 TREES as scatter hosts. One-sided bounds are a defect
# class this project has hit repeatedly (paving asserted never PROUD of the
# datum but never that it was not far BELOW it, and 100 mm of sunken forecourt
# went unseen). So bound BOTH sides.
_scatter_n = len(scatter)
_diags = [s["diag_m"] for s in scatter]
if _scatter_n > SCATTER_MAX_HOSTS:
    _small = sorted(_diags)[:5]
    raise SystemExit(
        f"[BDP] REFUSING TO WRITE: {_scatter_n} objects classified as SCATTER HOSTS, "
        f"against a plausible ceiling of {SCATTER_MAX_HOSTS}. This world has ~34 real "
        f"hosts and tens of thousands of trees. SCATTER_DIAG_M ({SCATTER_DIAG_M} m) is "
        f"TOO LOW and is sweeping trees into scatter -- smallest 5 diagonals classed as "
        f"scatter: {['%.1f' % d for d in _small]} m. A tiering built on this file would "
        f"silently lose those instances, because `scatter_pts` is not read by "
        f"screen_presence.py; only veg_origin/veg_name are.")
if _scatter_n and _diags:
    print(f"[BDP] scatter hosts {_scatter_n}, diagonals "
          f"{min(_diags):.1f}..{max(_diags):.1f} m; "
          f"veg kept as points {vo.shape[0]}", flush=True)

summary = {
    "source": "REBUILT FROM MODULES, not opened from assembly2.blend",
    "world_contract": C.__version__,
    "assembly2_contract": "1.0.1",
    "mods_requested": MODS, "mods_built": mods_done,
    "mods_failed": mods_failed, "mods_skipped": mods_skipped,
    "cell_m": a.cell, "cap_per_object": a.cap, "seed": a.seed,
    "evaluated_objects": len(names), "points": int(pts.shape[0]),
    "veg_objects": int(vo.shape[0]),
    "scatter_hosts": len(scatter), "scatter_points": int(sp.shape[0]),
    "scatter_detail": scatter,
    "total_verts": int(sum(m["verts"] for m in meta)),
    "total_tris": int(sum(m["tris"] for m in meta)),
    "seconds": round(time.time() - T0, 1),
    "objects": meta,
}
os.makedirs(os.path.dirname(os.path.abspath(a.out)) or ".", exist_ok=True)
np.savez_compressed(a.out, pts=pts, obj=obj,
                    names=np.array(names, dtype=object),
                    veg_origin=vo, veg_bbox=vb,
                    veg_name=np.array(veg_name, dtype=object),
                    scatter_pts=sp,
                    scatter_name=np.array(scatter_name, dtype=object),
                    meta=json.dumps(summary))
print("[BDP] " + json.dumps({k: v for k, v in summary.items() if k != "objects"}, indent=1),
      flush=True)
print(f"[BDP] wrote {a.out} ({os.path.getsize(a.out)/1e6:.1f} MB) in "
      f"{time.time()-T0:.0f}s", flush=True)
