"""Is the world's vocabulary genuine variety, or one asset spammed?

    # census + sweep, in one Blender run, against the DELIVERED camera
    /opt/blender-5.2.0-linux-x64/blender -b <assembly.blend> --factory-startup \
        -noaudio -P tools/instance_variety.py -- \
        --path render/film24_path.json \
        --census work/r23721/census15.npz \
        --out docs/instance_variety.json

    # the sweep again, from the saved census, with no Blender at all
    python3 tools/instance_variety.py --census work/r23721/census15.npz \
        --path render/film24_path.json --out docs/instance_variety.json

WHY
---
    "i dont want repeat stuff aka one tree spammed 100 times everything has to
     be thought out no matter what"

===========================================================================
R2-3721 -- THIS GATE COUNTED ZERO TREES, AND ALWAYS HAD.  (defect #162)
===========================================================================
Until this rewrite the counting loop was::

    for inst in deps.object_instances:
        if not inst.is_instance:
            continue

and `world/build_terrain.py:instance_plants()` -- which places every tree,
every hedgerow tree, the paddock avenue, the near-band short trees and the
amenity trees -- makes LINKED DUPLICATE OBJECTS: real scene objects sharing a
mesh datablock.  A real object has `is_instance == False`.  So the one line
above discarded every single one of them.

Not argued from the source -- BUILT AND WATCHED, on a six-object control
(`tools/r2_3421_instance_variety_control.py`, and the four-arm successor
`tools/r2_3721_variety_gate_control.py` which drives THIS file rather than a
copy of it).  The gate watched 40 trees spammed from ONE source mesh and
reported nothing, while printing a confident SPAM verdict about the grass.

It reconciles on the shipping world too.  Summing `assembly15_build.json`'s
own geometry-nodes populations gives 4,945,517; the old gate measured
4,955,784 -- within 0.2 % -- with all 28,389 discrete plants absent
(woodland 24,646 + hedgerow 3,299 + avenue 24 + near-band short 356 +
amenity 64).

**Every variety record this project has ever quoted -- the 311 sources /
1.99 % that closed task #28, and the 1,569 / 2.03 % measured on assembly14 --
is a census of ground cover with every tree in the world left out.**

===========================================================================
AND `top_share` IS NOT RECALIBRATED HERE.  IT IS RETIRED.  (R2-3441/R2-3721)
===========================================================================
The old verdict was `top_share` -- the fraction of all realized instances
taken by the commonest source mesh -- against a 40 % line.  Three faults, all
structural rather than matters of where the threshold sits:

1.  IT HAS NO PERCEPTUAL CONTENT AT ANY VALUE.  Measured, through the real
    pipeline: collapsing eleven hero grass meshes to ONE moved the picture by
    1.4 % (whole-frame NCC 0.986, motion blur off, which is harsher than
    delivery).  Removing per-instance rotation was instantly obvious by eye.
    What defeats repetition in this world is per-instance randomisation --
    yaw, mirror, height, breadth, lean -- and `top_share` cannot see any of it.

2.  A WHOLE-WORLD RATIO CANNOT EXPRESS A SCREEN EVENT.  "One tree spammed 100
    times" is a hundred copies YOU CAN SEE AT ONCE.  A mesh used a million
    times and never twice within sight of itself is not that; a mesh used
    twelve times, all twelve filling one frame, is.  A ratio over the whole
    world cannot tell them apart.

3.  ITS DENOMINATOR WAS ALWAYS GRASS.  The family key was the leading token of
    the emitter name, and every vegetation emitter here is `VEG_*`, so ~4.9 M
    ground-cover instances were ONE family and every tree pool was diluted
    ~180x before it was looked at.

`top_share` is still COMPUTED and still written to the report, because the
historical records are quoted in `top_share` and a reader must be able to line
them up.  It decides nothing.  The key is spelled `top_share_retired_R2_3441`
so that nobody requotes it as a verdict by accident.

===========================================================================
WHAT DECIDES NOW: CO-VISIBLE SHARP INSTANCES PER SOURCE MESH
===========================================================================
For every SOURCE MESH used by two or more instances, and every frame of the
delivered camera path, the gate counts the instances of THAT ONE MESH which
are simultaneously:

    in frustum      depth > 0 and the projection inside 3840 x 2160
    recognisable    projected height >= RECOG_PX of the 4K delivery, i.e.
                    big enough that a silhouette could be read at all
    sharp           shutter smear <= SMEAR_SHARP_PX (`screen_presence.py`'s
                    own number), at the flat 180 deg shutter that ships

and keeps the peak over the film.  **That number is the client's sentence,
measured: "one tree spammed 100 times" is 100.**

It is MEASURED per mesh, not estimated.  The R2-3421 predecessor
(`tools/r2_3421_covisible_repeats.py`) divided a pool's co-visible count by an
assumed library size to get the EXPECTED per-mesh figure, because it worked
from a voxelised point dump that had lost which library slot each instance
drew.  This gate walks the depsgraph, so it knows the actual source mesh of
every single instance and needs no library table, no binomial approximation
and no voxel scale factor.

TWO MAXIMA, NOT ONE.  The frame with the most co-visible copies is a FAST
frame -- that is WHY so many are in it -- so reading the sharp count off it
reports ~0 for every pool in the world and proves nothing.  The gate tracks
the busiest frame and, separately, the busiest frame among those the shutter
leaves resolvable, and the verdict is read off the second.

EVERY FIGURE IS AN UPPER BOUND ON WHAT IS VISIBLE, deliberately:

  * OCCLUSION IS NOT SUBTRACTED.  A tree behind a hill, a grandstand or the
    showroom wall still counts.
  * TILT IS IGNORED IN THE HEIGHT.  Height is the source mesh's local z extent
    times the length of the instance matrix's z axis, so a leaning tree is
    counted at its unleant height.
  * PER-INSTANCE VARIATION IS IGNORED.  Two instances of one mesh differ by
    yaw, mirror, height, breadth and lean and do not present the same
    silhouette; this counts them as if they did.

A bound in that direction is the safe one for a red line: it can only
OVER-report repetition.  It is NOT evidence that repetition is visible -- for
that the frames are the evidence (`tools/r2_3421_frame_repetition.py` and the
control strips in `work/r23421/`).

===========================================================================
EXEMPTIONS ARE WRITTEN DOWN, NOT HIDDEN IN A NAME FILTER
===========================================================================
Removing the `is_instance` filter reveals every linked duplicate in the world,
not only the trees -- and some of what it could reveal is hardware that is
IDENTICAL BY MANUFACTURE AND BY REGULATION, which a circuit would be wrong to
vary.  A gate that fails on 4,675 identical guardrail bolts has mistaken
engineering for laziness.

The predecessor avoided that by only ever looking at `VEG_*` names, which is a
scope restriction disguised as a family key -- the R2-3425 fault.  So here the
verdict is computed over EVERY source mesh first and printed, and the
exemptions are an explicit table with a reason per entry, applied afterwards
and reported separately.  An exemption you can read is honest; a filter you
cannot see is what this file is being repaired for.

AND ON `assembly15` THE TABLE MATCHES NOTHING, WHICH IS ALSO WORTH SAYING.
Measured, not assumed: the barrier hardware in this world is MERGED GEOMETRY,
not linked duplicates -- all 131 `BR_*` source meshes have exactly ONE user
each, so the armco, the bolts and the tyre walls never enter the repeat metric
at all.  Only two families in the world are actually built from repeated
meshes: `VEG_*` (1,092 repeated meshes) and the crowd, `SPECX_*` (746).  The
exemption table is kept because the failure mode it guards is real for a world
that DOES place hardware as duplicates, and the run prints how many source
meshes it matched so that a table which has quietly stopped applying cannot go
on looking like it is doing something.

===========================================================================
NO CAMERA, NO VERDICT
===========================================================================
Co-visibility is a screen event, so it needs a screen.  With no `--path` and
no camera in the scene the gate REFUSES (VACUOUS, exit 3) rather than passing.
Zero instances is VACUOUS for the same reason it was before: "0 families, none
of them spam" is the emptiest possible pass.

THE CAMERA MUST BE THE DELIVERED ONE.  `world/camera_rig_path.json` is the
R2-1007 orphan and was never rendered; it differs from `render/film24_path.json`
on 1,142 of 2,978 frames in position (max 21.4 m).  The gate records the path
file and its sha in the report so a stale sweep is visible in the artefact.
"""
import argparse
import hashlib
import json
import math
import os
import sys
import time
from array import array
from collections import Counter, defaultdict

import numpy as np

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_HERE = os.path.join(R2, "tools")
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
import gate_exit                                                    # noqa: E402
from screen_presence import (camera_track, RES_X, RES_Y,            # noqa: E402
                             SMEAR_SHARP_PX)

# ---------------------------------------------------------------------------
# THE NUMBERS.
# ---------------------------------------------------------------------------
# The named failure, as a number.  "one tree spammed 100 times".
SPAM_CVR = 100.0

# Projected height, in pixels of the 3840x2160 delivery, at which a silhouette
# is taken to be readable at all.  The ladder is printed in full so that no
# conclusion rests on one row; the verdict is read off RECOG_PX.
RECOG_PX_LADDER = (32.0, 64.0, 128.0, 256.0)
RECOG_PX = 64.0

SHUTTER = 0.5                 # flat 180 deg, the shipping mode since R2-037

# A mesh used once cannot be a repeat.  This is the whole of the "which meshes
# are candidates" rule -- there is deliberately no name test in it.
MIN_USERS = 2

# ---------------------------------------------------------------------------
# OCCLUSION.  R2-3741.
# ---------------------------------------------------------------------------
# CO-VISIBLE MEANS VISIBLE TOGETHER, and until R2-3741 this gate counted every
# instance in the frustum whether or not the audience could see it.  On
# `assembly15` that was not a theoretical looseness: the five reed meshes that
# tripped the 100-copy line are 182-387 m away BEHIND THE PIT WALL.  An
# instance nobody can see is not a repeat of anything, so counting it is a
# defect in the measure and not a strictness setting.
#
# WHICH DIRECTION THE ERRORS GO, because subtracting occlusion can only ever
# LOWER a count and must therefore be shown not to be a quiet weakening:
#
#   * The occluder set is the WORLD SHELL ONLY -- terrain, track, barriers,
#     walls, buildings, structures; every real object whose mesh has one user.
#     Repeated instances DO NOT OCCLUDE EACH OTHER here: a tree behind a tree
#     still counts.  That is the conservative direction and it is the case the
#     red line is actually about.
#   * The shell is a SURFACE SAMPLE and the depth buffer is quarter
#     resolution, so it has holes, and a hole lets a hidden instance through as
#     visible.  Also conservative.
#   * `OCC_TOL_M` lets an instance within 0.75 m of the front surface count as
#     the front, so a plant standing ON the ground is not occluded by the
#     ground it stands on.
#
# So the subtracted count remains an UPPER BOUND on what is visible.  It is
# just a tighter one.  `tools/r2_3721_variety_gate_control.py` arms G and H
# hold that to account: the 40-trees-from-one-mesh case must still be caught
# with occlusion on, and a wall built between the camera and those same 40
# trees must be what makes them fall.
OCC_RES = 4                   # depth buffer is 1/4 linear -> 960 x 540
OCC_TOL_M = 0.75              # screen_presence.py's own tolerance
OCC_CELL_M = 1.5              # shell sample spacing, metres
SAMPLE_BATCH = 400000         # max face-samples held live at once
SAMPLE_OVERSAMPLE = 6         # draws per cell before voxel dedupe
OCC_LEVELS = 9                # mip levels: footprints 1..256 quarter-res px

# `tools/dump_world_points.py`'s own threshold, and the reason it exists: a
# scatter HOST is a real object whose base mesh spans +-1,250 m and carries the
# ground cover as merged geometry.  It is one object, so MIN_USERS already
# drops it from the sweep; this only keeps it out of the height buckets, where
# a 2.5 km "instance" would widen every cull radius in the world.
HOST_DIAG_M = 200.0

# ---------------------------------------------------------------------------
# EXEMPTIONS.  Printed, reasoned, and applied only AFTER the unexempt verdict.
#
# Matched against the SOURCE OBJECT NAME (the library object or the linked
# duplicate), not the mesh name, because that is the name a reader recognises.
# ---------------------------------------------------------------------------
EXEMPT = (
    ("BR_Armco",   "FIA-spec guardrail: every panel is the same pressing, and "
                   "a circuit whose armco varied would be wrong."),
    ("BR_Post",    "guardrail posts, same."),
    ("BR_Bolt",    "guardrail splice bolts, same."),
    ("BR_Tecpro",  "TecPro barrier modules are a manufactured product."),
    ("BR_Tyre",    "tyre wall: identical road tyres, stacked."),
    ("BR_Fence",   "debris fence posts and mesh panels."),
    ("SR_Seat",    "grandstand seating is moulded in one shape by design."),
    ("SR_Step",    "grandstand steps, same."),
    ("SR_Truss",   "temporary grandstand truss is a hire-stock section."),
)


def exempt_reason(obj_name):
    for pfx, why in EXEMPT:
        if obj_name.startswith(pfx):
            return "%s: %s" % (pfx, why)
    return None


# ---------------------------------------------------------------------------
# THE CENSUS.  Inside Blender.  BOTH ARMS.
# ---------------------------------------------------------------------------
def census():
    """Every realized mesh in the scene, keyed by its SOURCE MESH datablock.

    The two arms are the whole point of this rewrite:

      A. `is_instance == False` -- REAL OBJECTS.  Linked duplicates live here,
         which is every tree in the world.  The old gate skipped this arm
         entirely.
      B. `is_instance == True`  -- geometry-nodes instances.  The ground cover.

    Both are walked in ONE pass over `depsgraph.object_instances`, which is the
    same walk the old gate did with one `continue` in it.

    Height is the source mesh's LOCAL z extent times the length of the instance
    matrix's z axis.  That is exact for an upright instance and an over-estimate
    for a leaning one, which is the safe direction.  It matters more than it
    sounds: `build_terrain.gn_kind()` normalises every library mesh to UNIT
    HEIGHT and puts the real size in the instance scale, so a gate that read
    the mesh alone would score every grass clump as 1 m tall.
    """
    import bpy

    t0 = time.time()
    deps = bpy.context.evaluated_depsgraph_get()

    names = []                       # mesh id -> source mesh datablock name
    obj_of = []                      # mesh id -> an example source object name
    zext = []                        # mesh id -> local z extent, metres
    diag = []                        # mesh id -> local bbox diagonal, metres
    n_obj = []                       # mesh id -> count with is_instance False
    n_ins = []                       # mesh id -> count with is_instance True
    mid = {}

    X, Y, Z, H = array("f"), array("f"), array("f"), array("f")
    MI = array("i")
    n_total = 0
    n_nonmesh = 0

    for inst in deps.object_instances:
        ob = inst.object
        if ob is None or ob.type != "MESH":
            n_nonmesh += 1
            continue
        d = ob.data
        nm = d.name if d else ob.name
        i = mid.get(nm)
        if i is None:
            i = mid[nm] = len(names)
            names.append(nm)
            obj_of.append(ob.name)
            bb = ob.bound_box
            zs = [bb[k][2] for k in range(8)]
            xs = [bb[k][0] for k in range(8)]
            ys = [bb[k][1] for k in range(8)]
            zext.append(max(zs) - min(zs))
            diag.append(math.sqrt((max(xs) - min(xs)) ** 2
                                  + (max(ys) - min(ys)) ** 2
                                  + (max(zs) - min(zs)) ** 2))
            n_obj.append(0)
            n_ins.append(0)
        mw = inst.matrix_world
        t = mw.translation
        X.append(t[0])
        Y.append(t[1])
        Z.append(t[2])
        c = mw.col[2]
        H.append(zext[i] * math.sqrt(c[0] * c[0] + c[1] * c[1] + c[2] * c[2]))
        MI.append(i)
        if inst.is_instance:
            n_ins[i] += 1
        else:
            n_obj[i] += 1
        n_total += 1
        if n_total % 1000000 == 0:
            print("[census] %d realized ... %.0f s"
                  % (n_total, time.time() - t0), flush=True)

    P = np.empty((n_total, 3), np.float32)
    P[:, 0] = np.frombuffer(X, np.float32)
    P[:, 1] = np.frombuffer(Y, np.float32)
    P[:, 2] = np.frombuffer(Z, np.float32)
    out = dict(
        P=P,
        H=np.frombuffer(H, np.float32).copy(),
        MID=np.frombuffer(MI, np.int32).copy(),
        names=np.array(names, dtype=object),
        obj_of=np.array(obj_of, dtype=object),
        zext=np.array(zext, np.float32),
        diag=np.array(diag, np.float32),
        n_obj=np.array(n_obj, np.int64),
        n_ins=np.array(n_ins, np.int64),
        meta=json.dumps({
            "blend": bpy.data.filepath,
            "n_total": n_total,
            "n_objects": int(sum(n_obj)),
            "n_gn_instances": int(sum(n_ins)),
            "n_source_meshes": len(names),
            "n_nonmesh_entries": n_nonmesh,
            "census_s": round(time.time() - t0, 1),
            "blender": bpy.app.version_string,
            "numpy": np.__version__,
        }),
    )
    print("[census] %d realized meshes over %d source meshes "
          "(%d real objects + %d GN instances) in %.0f s"
          % (n_total, len(names), sum(n_obj), sum(n_ins), time.time() - t0),
          flush=True)
    return out


def shell_points(cell_m=OCC_CELL_M, progress_every=200):
    """A SURFACE sample of the world shell, for the occlusion depth buffer.

    Every real object whose mesh has ONE user -- terrain, track, kerbs,
    barriers, walls, grandstands, buildings, bridges.  A mesh with two or more
    users is a repeated instance and is deliberately NOT an occluder (see the
    OCCLUSION block at the top of this file).

    IT SAMPLES FACES, NOT VERTICES, and that is the whole reason this function
    exists rather than a call to `tools/dump_world_points.py`.  That tool
    voxelises `me.vertices`, which for a large flat quad records FOUR POINTS
    AND NO WALL -- and a hollow pit wall occludes nothing, which would have
    made this change look like it had measured something when it had not.
    Here each triangle gets `ceil(area / cell^2)` stratified barycentric
    samples, so a 40 m x 1.2 m concrete panel with two triangles becomes ~21
    points at 1.5 m spacing instead of 4 at its corners.

    Scatter hosts are skipped: `to_mesh()` on one is the 7 GB / 13-billion
    triangle evaluated layer, and grass is not an occluder worth that.  Skipping
    it can only leave an instance counted that a blade of grass hid, which is
    the safe direction.
    """
    import bpy

    t0 = time.time()
    deps = bpy.context.evaluated_depsgraph_get()
    users = Counter()
    for ob in bpy.context.scene.objects:
        if ob.type == "MESH" and ob.data is not None:
            users[ob.data.name] += 1

    rng = np.random.default_rng(20260809)
    chunks = []
    n_obj = n_skip_rep = n_skip_host = n_fail = 0
    objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    for k, ob in enumerate(objs):
        if ob.data is not None and users[ob.data.name] >= MIN_USERS:
            n_skip_rep += 1
            continue
        bb = np.array([list(v) for v in ob.bound_box], dtype=np.float64)
        M = np.array(ob.matrix_world, dtype=np.float64)
        w = bb @ M[:3, :3].T + M[:3, 3]
        # SIZE ALONE IS NOT THE HOST TEST HERE, and the first version of this
        # function used it and measured almost nothing. `HOST_DIAG_M` exists to
        # spot a 2.5 km VEGETATION scatter host whose evaluated mesh is the
        # 13-billion-triangle layer. Applied to every object it also threw out
        # SURF_Track (1,688 m), the terrain and all 131 BR_* armco runs (up to
        # 259 m) -- which is to say it threw out THE PIT WALL, the one occluder
        # this change is about. 2,089 objects survived and produced 55,979
        # points for a 2.5 km world; the corrected pass produces two orders of
        # magnitude more. The test is size AND being vegetation, exactly as
        # `dump_world_points.py` has it.
        if (ob.name.startswith("VEG")
                and float(np.linalg.norm(w.max(0) - w.min(0))) > HOST_DIAG_M):
            n_skip_host += 1
            continue
        oe = ob.evaluated_get(deps)
        try:
            me = oe.to_mesh()
        except Exception as exc:                                # noqa: BLE001
            print("[shell] %s: to_mesh failed %r" % (ob.name, exc), flush=True)
            n_fail += 1
            continue
        try:
            me.calc_loop_triangles()
            nt = len(me.loop_triangles)
            nv = len(me.vertices)
            if nt == 0 or nv == 0:
                continue
            V = np.empty(nv * 3, np.float64)
            me.vertices.foreach_get("co", V)
            V = V.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3]
            T = np.empty(nt * 3, np.int32)
            me.loop_triangles.foreach_get("vertices", T)
            T = T.reshape(-1, 3)
        finally:
            oe.to_mesh_clear()
        A, B, Cv = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
        area = 0.5 * np.linalg.norm(np.cross(B - A, Cv - A), axis=1)
        # OVERSAMPLED, BECAUSE RANDOM SAMPLES DO NOT COVER A GRID. Drawing
        # exactly `area / cell^2` uniform points and then voxel-deduping leaves
        # 1/e -- 37 % -- of the cells empty by the coupon-collector argument,
        # and an occluder with 37 % holes is an occluder things walk through:
        # the control measured 5 of 40 trees visible through a solid wall for
        # exactly this reason. At x6 the expected coverage is 99.75 %. The
        # dedupe means the OUTPUT size is unchanged; only the sampling costs
        # more.
        k_per = np.clip(np.ceil(SAMPLE_OVERSAMPLE * area / (cell_m * cell_m)),
                        1, 20000).astype(np.int64)
        # BATCHED, AND THE FIRST VERSION WAS NOT. Materialising one object's
        # whole sample set before deduping is fine for a bolt and fatal for the
        # terrain: a few thousand 50 m triangles are 1,100 samples each, and the
        # run reached 38 GB of swap and had to be stopped before it took the
        # box down with somebody else's build on it. Sample and dedupe in
        # bounded slabs instead -- the deduped result is identical, the peak is
        # not.
        cum = np.cumsum(k_per)
        tot = int(cum[-1])
        edges = [0]
        while edges[-1] < len(T):
            base = int(cum[edges[-1] - 1]) if edges[-1] > 0 else 0
            nxt = int(np.searchsorted(cum, base + SAMPLE_BATCH, side="right"))
            edges.append(min(len(T), max(nxt, edges[-1] + 1)))
        got = []
        for e0, e1 in zip(edges[:-1], edges[1:]):
            kk = k_per[e0:e1]
            idx = np.repeat(np.arange(e0, e1), kk)
            u = rng.random(len(idx))
            v = rng.random(len(idx))
            fold = u + v > 1.0
            u[fold] = 1.0 - u[fold]
            v[fold] = 1.0 - v[fold]
            Pb = (A[idx] + (B[idx] - A[idx]) * u[:, None]
                  + (Cv[idx] - A[idx]) * v[:, None])
            q = np.floor(Pb / cell_m).astype(np.int64)
            _, keep = np.unique(
                q[:, 0] * 40000000000 + q[:, 1] * 200000 + q[:, 2],
                return_index=True)
            got.append(Pb[keep].astype(np.float32))
            del idx, u, v, Pb, q
        P = np.concatenate(got) if got else np.zeros((0, 3), np.float32)
        if tot > SAMPLE_BATCH:
            print("[shell] %-28s %8d tris -> %9d samples -> %7d points"
                  % (ob.name[:28], len(T), tot, len(P)), flush=True)
        chunks.append(P)
        n_obj += 1
        if progress_every and n_obj % progress_every == 0:
            print("[shell] %d objects, %d points, %.0f s"
                  % (n_obj, sum(len(c) for c in chunks), time.time() - t0),
                  flush=True)

    P = (np.concatenate(chunks) if chunks
         else np.zeros((0, 3), np.float32))
    # one global voxel dedupe, so overlapping objects do not pay twice
    q = np.floor(P.astype(np.float64) / cell_m).astype(np.int64)
    _, keep = np.unique(q[:, 0] * 40000000000 + q[:, 1] * 200000 + q[:, 2],
                        return_index=True)
    P = P[keep]
    print("[shell] %d shell objects sampled -> %d points at %.2f m "
          "(%d repeated meshes and %d hosts skipped, %d to_mesh failures) "
          "in %.0f s" % (n_obj, len(P), cell_m, n_skip_rep, n_skip_host,
                         n_fail, time.time() - t0), flush=True)
    return P, dict(shell_objects=n_obj, points=int(len(P)), cell_m=cell_m,
                   skipped_repeated=n_skip_rep, skipped_hosts=n_skip_host,
                   to_mesh_failures=n_fail)


def save_census(c, path):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    np.savez_compressed(path, **c)
    print("[census] wrote %s (%.1f MB)"
          % (path, os.path.getsize(path) / 1e6), flush=True)


def load_census(path):
    z = np.load(path, allow_pickle=True)
    return {k: z[k] for k in z.files}


# ---------------------------------------------------------------------------
# THE SWEEP.  numpy only -- no Blender needed once the census exists.
# ---------------------------------------------------------------------------
class _Grid:
    """A uniform XY grid whose cells are CONTIGUOUS ROWS after sorting.

    `cell = ci * NY + cj`, so a box query [i0..i1] x [j0..j1] is exactly
    (i1 - i0 + 1) contiguous slices, not (i1-i0+1)*(j1-j0+1) of them.  At 2,978
    frames that difference is the difference between minutes and hours.
    """

    def __init__(self, P, cell_m, max_cells=400000):
        lo = P[:, :2].min(axis=0)
        hi = P[:, :2].max(axis=0)
        span = np.maximum(hi - lo, 1.0)
        while (int(span[0] / cell_m) + 1) * (int(span[1] / cell_m) + 1) > max_cells:
            cell_m *= 2.0
        self.cell = cell_m
        self.lo = lo
        self.NX = int(span[0] / cell_m) + 1
        self.NY = int(span[1] / cell_m) + 1
        ci = np.clip(((P[:, 0] - lo[0]) / cell_m).astype(np.int64), 0, self.NX - 1)
        cj = np.clip(((P[:, 1] - lo[1]) / cell_m).astype(np.int64), 0, self.NY - 1)
        key = ci * self.NY + cj
        self.order = np.argsort(key, kind="stable")
        self.bounds = np.searchsorted(key[self.order],
                                      np.arange(self.NX * self.NY + 1))

    def box(self, cx, cy, r):
        """Index slices covering every point within the square of half-side r."""
        i0 = max(0, int((cx - r - self.lo[0]) / self.cell))
        i1 = min(self.NX - 1, int((cx + r - self.lo[0]) / self.cell))
        j0 = max(0, int((cy - r - self.lo[1]) / self.cell))
        j1 = min(self.NY - 1, int((cy + r - self.lo[1]) / self.cell))
        if i0 > i1 or j0 > j1:
            return None
        if i0 == 0 and i1 == self.NX - 1 and j0 == 0 and j1 == self.NY - 1:
            return "ALL"
        return [(int(self.bounds[i * self.NY + j0]),
                 int(self.bounds[i * self.NY + j1 + 1]))
                for i in range(i0, i1 + 1)]


def sweep(P, H, MID, nmesh, path_json, stride=1, ladder=RECOG_PX_LADDER,
          shutter=SHUTTER, smear_px=SMEAR_SHARP_PX, progress=True,
          sharp_tracker="max", shell=None):
    """Peak co-visible count per source mesh, over the film.

    Returns two dicts of arrays keyed by ladder threshold:
        peak[thr]  -> (nmesh,) busiest frame's count, and the frame
        sharp[thr] -> (nmesh,) busiest SHARP frame's sharp count, and the frame

    `sharp_tracker` is "max" -- keep the largest sharp count seen -- and there
    is exactly one other value, "r2_3421", which is NOT a mode anybody should
    measure with.  It reproduces `tools/r2_3421_covisible_repeats.py`'s
    busiest-sharp-frame tracker, which reads

        bsharp = {p: dict(n=0.0, f=0, sharp=0.0) ...}
        ...
        if ns > bsharp[thr]["n"]:            # ns is a SHARP count
            bsharp[thr] = dict(n=n, f=f + 1, sharp=ns)   # n is the TOTAL

    i.e. it compares this frame's SHARP count against the stored frame's TOTAL.
    Since total >= sharp always, the stored value can only be replaced by a
    frame whose sharp count beats an earlier frame's total, and the tracker
    therefore reports a LOWER BOUND on the peak sharp count rather than the
    peak.  This switch exists so that the claim can be demonstrated rather than
    asserted: `tools/r2_3721_sweep_crosscheck.py` runs the same loop both ways
    and shows the emulation reproducing that tool's published numbers exactly.
    """
    C, Rm, s, _lens, nf = camera_track(path_json)
    frames = list(range(0, nf - 1, stride))
    smin = float(np.min(ladder))

    # Height octaves.  Each gets its own grid and its own cull radius, so the
    # 5 mm grit is not dragged through a 2 km search because a tree is tall.
    Hc = np.maximum(H, 1e-4)
    oct_id = np.floor(np.log2(Hc)).astype(np.int64)
    buckets = []
    for o in np.unique(oct_id):
        m = np.nonzero(oct_id == o)[0]
        Pb = np.ascontiguousarray(P[m])
        g = _Grid(Pb, 32.0)
        buckets.append(dict(idx=m[g.order], P=Pb[g.order],
                            H=np.ascontiguousarray(Hc[m][g.order]),
                            MID=np.ascontiguousarray(MID[m][g.order]),
                            grid=g, hmax=float(Hc[m].max())))

    # THE OCCLUDER SET. See the OCCLUSION block at the top of this file for
    # which way every error in it points.
    Sg = None
    if shell is not None and len(shell):
        Sg = _Grid(np.ascontiguousarray(shell), 32.0)
        Sp = np.ascontiguousarray(shell)[Sg.order]
    ow, oh = RES_X // OCC_RES, RES_Y // OCC_RES

    peak = {t: np.zeros(nmesh) for t in ladder}
    peak_f = {t: np.zeros(nmesh, np.int64) for t in ladder}
    sharp = {t: np.zeros(nmesh) for t in ladder}
    sharp_f = {t: np.zeros(nmesh, np.int64) for t in ladder}
    peak_sharp_at_peak = {t: np.zeros(nmesh) for t in ladder}
    # the SAME sweep without occlusion subtracted, carried the whole way so the
    # change can be read as a diff rather than taken on trust
    sharp_no = {t: np.zeros(nmesh) for t in ladder}
    sharp_no_f = {t: np.zeros(nmesh, np.int64) for t in ladder}
    # only read by the "r2_3421" emulation: the TOTAL count of the frame
    # currently held as the busiest-sharp one.
    sharp_total = {t: np.zeros(nmesh) for t in ladder}

    t0 = time.time()
    for n_done, f in enumerate(frames):
        cx, cy, cz = C[f]
        Rf, sf = Rm[f], s[f]
        # RANGE IS NOT DEPTH, AND THE FIRST VERSION OF THIS CULL ASSUMED IT WAS.
        #
        # Recognisable means `h * s / depth >= px_min`, i.e. depth <= h*s/px_min.
        # Culling on `range <= h*s/px_min` looks equivalent because depth <=
        # range -- but the implication runs the wrong way: an in-frustum point
        # at depth 100 m can be at RANGE 152 m if it is at the edge of an 18 mm
        # frame, and the cull threw it away. Measured, not reasoned about:
        # `tools/r2_3721_sweep_crosscheck.py` put this loop against the
        # independently written R2-3421 loop on the same 27,969 trees and 102 of
        # 120 comparisons disagreed, ALL of them low -- birch_L2 at >= 32 px read
        # 572 against 866. A cull one factor too tight silently deletes the far
        # half of a treeline and the answer still looks plausible.
        #
        # For a point inside the frame, range^2 <= depth^2 * (1 + (X/2s)^2 +
        # (Y/2s)^2), so this factor is exact and lens-dependent, and at the 18 mm
        # end of this film it is 1.52.
        kf = math.sqrt(1.0 + (RES_X / (2.0 * sf)) ** 2
                       + (RES_Y / (2.0 * sf)) ** 2)
        Rg, sg = Rm[f + 1], s[f + 1]
        Cg = C[f + 1]
        # THE FRAME'S SURVIVORS, POOLED ACROSS EVERY HEIGHT BUCKET BEFORE
        # ANYTHING IS COUNTED.
        #
        # The first version updated the running maxima inside the bucket loop,
        # and that is wrong for exactly the population this gate exists to
        # measure: `instance_plants()` randomises every tree's target height, so
        # ONE source mesh has instances in TWO OR THREE height octaves, and
        # per-bucket updates take the MAX of the partial counts where the truth
        # is their SUM. `tools/r2_3721_sweep_crosscheck.py` caught it -- 92 of
        # 120 comparisons against the R2-3421 loop disagreed, every one of them
        # low, `tree:plane_L0` reading 17 against 26.
        frame_ids, frame_px, frame_sharp = [], [], []
        frame_x, frame_y, frame_dep = [], [], []
        for b in buckets:
            r = b["hmax"] * sf / smin * kf
            sl = b["grid"].box(cx, cy, r)
            if sl is None:
                continue
            if sl == "ALL":
                Q, Hq, Mq = b["P"], b["H"], b["MID"]
            else:
                keep = [x for x in sl if x[1] > x[0]]
                if not keep:
                    continue
                if len(keep) == 1:
                    a0, a1 = keep[0]
                    Q, Hq, Mq = b["P"][a0:a1], b["H"][a0:a1], b["MID"][a0:a1]
                else:
                    Q = np.concatenate([b["P"][a:z] for a, z in keep])
                    Hq = np.concatenate([b["H"][a:z] for a, z in keep])
                    Mq = np.concatenate([b["MID"][a:z] for a, z in keep])
            if len(Q) == 0:
                continue
            # exact per-point pre-cull: recognisable needs depth <= h*s/px_min,
            # and depth <= range, so range > h*s/px_min can never qualify.
            d = Q.astype(np.float64)
            d[:, 0] -= cx
            d[:, 1] -= cy
            d[:, 2] -= cz
            rng2 = np.einsum("ij,ij->i", d, d)
            lim = Hq * (sf / smin) * kf
            m0 = rng2 <= lim * lim
            if not m0.any():
                continue
            d = d[m0]
            Hq = Hq[m0]
            Mq = Mq[m0]
            cam = d @ Rf
            dep = -cam[:, 2]
            ok = dep > 0.05
            if not ok.any():
                continue
            cam, dep, Hq, Mq = cam[ok], dep[ok], Hq[ok], Mq[ok]
            inv = 1.0 / dep
            x = cam[:, 0] * inv * sf + RES_X / 2
            y = -cam[:, 1] * inv * sf + RES_Y / 2
            infr = (x >= 0) & (x < RES_X) & (y >= 0) & (y < RES_Y)
            if not infr.any():
                continue
            x, y, Hq, Mq = x[infr], y[infr], Hq[infr], Mq[infr]
            px = Hq * sf * inv[infr]
            big = px >= smin
            if not big.any():
                continue
            W0 = d[ok][infr]                       # camera-relative positions
            x, y, px, Mq = x[big], y[big], px[big], Mq[big]
            Hq = Hq[big]
            # smear: the SAME world point through the NEXT frame's camera
            W = W0[big] + np.array([cx, cy, cz]) - Cg
            c1 = W @ Rg
            dp1 = -c1[:, 2]
            good = dp1 > 0.05
            i1 = 1.0 / np.where(good, dp1, 1.0)
            x1 = c1[:, 0] * i1 * sg + RES_X / 2
            y1 = -c1[:, 1] * i1 * sg + RES_Y / 2
            sm = np.where(good, np.hypot(x1 - x, y1 - y) * shutter, 1e9)
            is_sharp = sm <= smear_px
            frame_ids.append(Mq)
            frame_px.append(px)
            frame_sharp.append(is_sharp)
            # THE OCCLUSION PROBE IS THE SUBJECT'S MID-HEIGHT, NOT ITS ORIGIN.
            # `instance_plants()` and `gn_kind()` both put a plant's origin ON
            # THE GROUND, and the ground a few metres in front of a plant
            # projects to the same pixel as the plant's base at almost every
            # camera height in this film. Probing the origin therefore reports
            # every plant in the world as occluded by the earth it is standing
            # on -- measured, on the control: 40 trees in an empty field with
            # one ground plane came back 33.
            #
            # The mid-height point is on the subject, is what a silhouette is
            # read from, and clears the ground plane by half the plant.
            Wm = W0[big].copy()
            Wm[:, 2] += 0.5 * Hq
            cm = Wm @ Rf
            dm = -cm[:, 2]
            gm = dm > 0.05
            im = 1.0 / np.where(gm, dm, 1.0)
            frame_x.append(np.where(gm, cm[:, 0] * im * sf + RES_X / 2, x))
            frame_y.append(np.where(gm, -cm[:, 1] * im * sf + RES_Y / 2, y))
            frame_dep.append(np.where(gm, dm, dep[infr][big]))

        if not frame_ids:
            continue
        cat = (lambda L: L[0] if len(L) == 1 else np.concatenate(L))
        Mf, pxf, shf = cat(frame_ids), cat(frame_px), cat(frame_sharp)
        xf, yf, depf = cat(frame_x), cat(frame_y), cat(frame_dep)

        # ---- OCCLUSION ---------------------------------------------------
        # A quarter-resolution depth buffer of the world shell, rasterised for
        # THIS frame only, and only out to the furthest subject that could
        # matter. Nothing beyond the subjects can occlude them, so the query
        # radius is the subjects' own reach -- which is what keeps this
        # affordable at 2,977 frames.
        front = np.ones(len(Mf), bool)
        if Sg is not None and len(Mf):
            rq = float(depf.max()) * kf
            sl = Sg.box(cx, cy, rq)
            if sl is not None:
                if sl == "ALL":
                    O = Sp
                else:
                    kp = [t for t in sl if t[1] > t[0]]
                    O = (Sp[kp[0][0]:kp[0][1]] if len(kp) == 1
                         else (np.concatenate([Sp[i:j] for i, j in kp])
                               if kp else Sp[:0]))
                if len(O):
                    od = O.astype(np.float64)
                    od[:, 0] -= cx
                    od[:, 1] -= cy
                    od[:, 2] -= cz
                    oc = od @ Rf
                    odep = -oc[:, 2]
                    om = odep > 0.05
                    if om.any():
                        oi = 1.0 / odep[om]
                        oxp = oc[om, 0] * oi * sf + RES_X / 2
                        oyp = -oc[om, 1] * oi * sf + RES_Y / 2
                        inb = ((oxp >= 0) & (oxp < RES_X)
                               & (oyp >= 0) & (oyp < RES_Y))
                        if inb.any():
                            # A SPLATTED POINT IS NOT A SURFACE, and two
                            # earlier versions of this test believed variants of
                            # that. The shell is sampled every 1.5 m of WORLD,
                            # and 1.5 m at 30 m through a 50 mm lens is 67
                            # quarter-res pixels -- so 203 wall samples filled
                            # 55 pixels of the ~387,000 they cover and the
                            # buffer was 99.98 % holes. The control caught it
                            # twice: 40 trees behind a solid wall came back 40,
                            # and then 35, when the footprint was taken from the
                            # SUBJECT's depth instead of the occluder's.
                            #
                            # A SAMPLE'S FOOTPRINT IS SET BY ITS OWN DEPTH, so
                            # each shell sample is splatted into the level of a
                            # mip pyramid whose cells are about its footprint.
                            # Cost is one pass per level rather than one per
                            # pixel of footprint, and it is bounded by the
                            # buffer, not by how close the geometry comes.
                            #
                            # THE BIAS THIS CARRIES, stated rather than hoped
                            # away: a level-L cell is a 2^L block aligned to the
                            # grid, not a disc centred on the sample, so an
                            # occluding surface is dilated by up to two sample
                            # spacings at its SILHOUETTE EDGE. A subject within
                            # ~3 m of the edge of a wall may be called occluded
                            # when a sliver of it is visible. Everywhere that is
                            # not an edge -- which is all of a pit wall except
                            # its ends -- the reconstruction is exact.
                            od_in = odep[om][inb]
                            fp = OCC_CELL_M * sf / od_in / OCC_RES
                            lv = np.clip(np.ceil(np.log2(np.maximum(fp, 1.0))),
                                         0, OCC_LEVELS - 1).astype(np.int32)
                            qy = (oyp[inb] / OCC_RES).astype(np.int32)
                            qx = (oxp[inb] / OCC_RES).astype(np.int32)
                            sy = np.clip((yf / OCC_RES).astype(np.int32), 0,
                                         oh - 1)
                            sx = np.clip((xf / OCC_RES).astype(np.int32), 0,
                                         ow - 1)
                            near = np.full(len(depf), np.inf)
                            for L in range(OCC_LEVELS):
                                g = lv == L
                                if not g.any():
                                    continue
                                hL, wL = max(1, oh >> L), max(1, ow >> L)
                                b = np.full((hL, wL), np.inf, np.float64)
                                np.minimum.at(
                                    b, (np.clip(qy[g] >> L, 0, hL - 1),
                                        np.clip(qx[g] >> L, 0, wL - 1)),
                                    od_in[g])
                                near = np.minimum(
                                    near, b[np.clip(sy >> L, 0, hL - 1),
                                            np.clip(sx >> L, 0, wL - 1)])
                            front = depf <= near + OCC_TOL_M

        for thr in ladder:
            sel = pxf >= thr
            if not sel.any():
                continue
            # over the SURVIVORS, not over all nmesh source meshes: at 2,978
            # frames x 4 ladder rows a full-width bincount is a billion
            # pointless comparisons.
            u, back = np.unique(Mf[sel], return_inverse=True)
            cnt = np.bincount(back, minlength=len(u)).astype(np.float64)
            csn = np.bincount(back, weights=shf[sel].astype(np.float64),
                              minlength=len(u))
            cs = np.bincount(back,
                             weights=(shf[sel] & front[sel]).astype(np.float64),
                             minlength=len(u))
            un = csn > sharp_no[thr][u]
            if un.any():
                iu = u[un]
                sharp_no[thr][iu] = csn[un]
                sharp_no_f[thr][iu] = f + 1
            up = cnt > peak[thr][u]
            if up.any():
                iu = u[up]
                peak[thr][iu] = cnt[up]
                peak_f[thr][iu] = f + 1
                peak_sharp_at_peak[thr][iu] = cs[up]
            us = (cs > (sharp_total[thr][u] if sharp_tracker == "r2_3421"
                        else sharp[thr][u]))
            if us.any():
                iu = u[us]
                sharp[thr][iu] = cs[us]
                sharp_total[thr][iu] = cnt[us]
                sharp_f[thr][iu] = f + 1
        if progress and n_done % 250 == 0:
            print("[sweep] frame %d/%d  %.0f s" % (n_done, len(frames),
                                                   time.time() - t0), flush=True)
    print("[sweep] %d frames (stride %d) in %.0f s"
          % (len(frames), stride, time.time() - t0), flush=True)
    return dict(peak=peak, peak_f=peak_f, sharp=sharp, sharp_f=sharp_f,
                sharp_at_peak=peak_sharp_at_peak,
                sharp_no_occ=sharp_no, sharp_no_occ_f=sharp_no_f,
                occlusion=Sg is not None, nframes=nf,
                frames_swept=len(frames))


# ---------------------------------------------------------------------------
# The retired measure, kept as description so the historical records line up.
# ---------------------------------------------------------------------------
def gini(counts):
    xs = sorted(counts)
    n = len(xs)
    if n == 0 or sum(xs) == 0:
        return 0.0
    cum = sum((i + 1) * x for i, x in enumerate(xs))
    return (2.0 * cum) / (n * sum(xs)) - (n + 1.0) / n


def legacy_families(names, obj_of, n_obj, n_ins):
    """The old `family` table, over BOTH arms now.  Descriptive only."""
    fam = defaultdict(Counter)
    for i, nm in enumerate(names):
        key = obj_of[i]
        f = key.split("_")[0] if "_" in key else key
        fam[f][nm] += int(n_obj[i]) + int(n_ins[i])
    rows = []
    for f, c in fam.items():
        n = sum(c.values())
        if n == 0:
            continue
        top = c.most_common(1)[0]
        rows.append({"family": f, "instances": n, "sources": len(c),
                     "top_source": top[0],
                     "top_share_retired_R2_3441": round(top[1] / n, 4),
                     "gini": round(gini(list(c.values())), 4),
                     "instances_per_source": round(n / len(c), 1)})
    rows.sort(key=lambda r: -r["instances"])
    return rows


def sha16(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


# ---------------------------------------------------------------------------
def main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--path", default=None,
                    help="delivered camera path json (render/film24_path.json)")
    ap.add_argument("--census", default=None,
                    help="write the census here (in Blender) or read it "
                         "(outside Blender)")
    ap.add_argument("--stride", type=int, default=1)
    ap.add_argument("--recog-px", type=float, default=RECOG_PX)
    ap.add_argument("--spam-cvr", type=float, default=SPAM_CVR)
    ap.add_argument("--top", type=int, default=25)
    ap.add_argument("--census-only", action="store_true")
    ap.add_argument("--shell", default=None,
                    help="write (in Blender) or read (outside) the world-shell "
                         "occluder point sample")
    ap.add_argument("--no-occlusion", action="store_true",
                    help="report the UNSUBTRACTED counts as the verdict. The "
                         "subtracted ones are reported either way; this only "
                         "changes which decides.")
    a = ap.parse_args(argv)

    in_blender = "bpy" in sys.modules or os.environ.get("R2_FORCE_BPY")
    if not in_blender:
        try:
            import bpy                                              # noqa: F401
            in_blender = True
        except ImportError:
            in_blender = False

    if in_blender:
        c = census()
        if a.census:
            save_census(c, a.census)
        if a.shell:
            SP, smeta = shell_points()
            os.makedirs(os.path.dirname(a.shell) or ".", exist_ok=True)
            np.savez_compressed(a.shell, P=SP, meta=json.dumps(smeta))
            print("[shell] wrote %s (%.1f MB)"
                  % (a.shell, os.path.getsize(a.shell) / 1e6), flush=True)
    else:
        if not a.census or not os.path.exists(a.census):
            raise SystemExit("REFUSING: not running inside Blender and no "
                             "--census file to read. Nothing was measured.")
        c = load_census(a.census)

    names = list(c["names"])
    obj_of = list(c["obj_of"])
    n_obj = np.asarray(c["n_obj"])
    n_ins = np.asarray(c["n_ins"])
    n_use = n_obj + n_ins
    total = int(n_use.sum())
    meta = json.loads(str(c["meta"])) if "meta" in c else {}

    families = legacy_families(names, obj_of, n_obj, n_ins)
    report = {
        "total_instances": total,
        "realized_objects": int(n_obj.sum()),
        "realized_gn_instances": int(n_ins.sum()),
        "source_meshes": len(names),
        "families": families,
        "top_share_is_retired": (
            "R2-3441/R2-3721: top_share has no perceptual content at any value "
            "(11 grass meshes -> 1 moved the picture 1.4 %, whole-frame NCC "
            "0.986). It is reported for continuity with the 1.99 % and 2.03 % "
            "records and decides nothing. The verdict is covisible_sharp."),
        "spam_cvr": a.spam_cvr,
        "recog_px": a.recog_px,
        "recog_px_ladder": list(RECOG_PX_LADDER),
        "smear_sharp_px": SMEAR_SHARP_PX,
        "shutter": SHUTTER,
        "res": [RES_X, RES_Y],
        "min_users": MIN_USERS,
        "exemptions": [{"prefix": p, "why": w} for p, w in EXEMPT],
        "census_meta": meta,
        "vacuous": total == 0,
    }

    print("TOTAL %d realized meshes -- %d REAL OBJECTS + %d GN instances -- "
          "over %d source meshes\n"
          % (total, int(n_obj.sum()), int(n_ins.sum()), len(names)))
    print("The first of those two arms is the one this gate could not see "
          "before R2-3721.\n")

    if total == 0:
        json.dump(report, open(a.out, "w"), indent=1)
        print(">> REFUSING TO REPORT: this scene realized ZERO meshes, so "
              "nothing about its variety was measured.")
        print(">> That is NOT a pass -- an empty distribution cannot be spammed.")
        return gate_exit.verdict("INSTANCE_VARIETY_VACUOUS")

    if a.census_only:
        json.dump(report, open(a.out, "w"), indent=1)
        print("wrote %s (census only, no verdict asked for)" % a.out)
        return gate_exit.verdict("INSTANCE_VARIETY_CENSUS_ONLY_VACUOUS")

    # ---- the camera ------------------------------------------------------
    path = a.path
    if path is None:
        json.dump(report, open(a.out, "w"), indent=1)
        print(">> REFUSING TO REPORT: co-visibility is a SCREEN event and no "
              "camera path was given (--path).")
        print(">> A census on its own cannot say whether a mesh is repeated "
              "WHERE IT CAN BE SEEN, which is the whole rule.")
        return gate_exit.verdict("INSTANCE_VARIETY_NO_CAMERA_VACUOUS")
    report["camera_path"] = os.path.relpath(os.path.abspath(path), R2)
    report["camera_path_sha16"] = sha16(path)

    # ---- who is even a candidate ----------------------------------------
    rep = n_use >= MIN_USERS
    small = np.asarray(c["diag"]) <= HOST_DIAG_M
    cand = np.nonzero(rep & small)[0]
    report["candidate_source_meshes"] = int(len(cand))
    # A SILENT DROP IS A DEFECT EVEN WHEN IT DROPS NOTHING. `HOST_DIAG_M` is
    # there to keep 2.5 km scatter hosts out of the height buckets, and a host
    # has one user so `MIN_USERS` already excludes it -- but if a genuinely
    # REPEATED mesh were ever that large it would leave the metric without a
    # word. So the count is computed, reported and named. On assembly15 it is
    # zero: 102 meshes exceed the diagonal and every one of them is used once.
    dropped = np.nonzero(rep & ~small)[0]
    report["repeated_but_larger_than_host_diag"] = [
        {"source_mesh": names[i], "example_object": obj_of[i],
         "instances": int(n_use[i]),
         "diag_m": round(float(np.asarray(c["diag"])[i]), 1)} for i in dropped]
    if len(dropped):
        print(">> NOTE: %d REPEATED source mesh(es) are larger than "
              "HOST_DIAG_M (%.0f m) and are NOT swept. They are listed in the "
              "report; this is a hole, not a pass." % (len(dropped), HOST_DIAG_M))
        for i in dropped[:10]:
            print("     %-34s %d instances, %.0f m across"
                  % (names[i], int(n_use[i]), float(np.asarray(c["diag"])[i])))
    else:
        print("host-diagonal filter: %d source mesh(es) exceed %.0f m and "
              "NONE of them is repeated, so nothing was dropped by it."
              % (int((~small).sum()), HOST_DIAG_M))
    if len(cand) == 0:
        report["sources"] = []
        json.dump(report, open(a.out, "w"), indent=1)
        # NOT vacuous. Every source mesh used exactly once is the STRONGEST
        # possible answer to "no repeated assets", not an unmeasurable one:
        # the maximum co-visible count of any mesh is 1, by construction, and
        # that is a measurement. Vacuous is reserved for a scene that realized
        # nothing at all, which is handled above.
        print(">> every one of the %d source meshes in this scene is used "
              "EXACTLY ONCE (%d realized meshes)." % (len(names), total))
        print(">> The most co-visible copies any mesh can have is therefore 1, "
              "against the named failure of %.0f." % a.spam_cvr)
        return gate_exit.verdict("INSTANCE_VARIETY_CLEAN",
                                 "  [no mesh used twice]")

    keep = np.isin(np.asarray(c["MID"]), cand)
    P = np.asarray(c["P"])[keep]
    H = np.asarray(c["H"])[keep]
    MID = np.asarray(c["MID"])[keep]
    print("sweeping %d instances of %d repeated source meshes against %s\n"
          % (len(P), len(cand), report["camera_path"]))

    SHELL = None
    if a.shell and os.path.exists(a.shell):
        z = np.load(a.shell, allow_pickle=True)
        SHELL = z["P"]
        smeta = json.loads(str(z["meta"])) if "meta" in z.files else {}
        report["shell"] = dict(path=os.path.relpath(os.path.abspath(a.shell), R2),
                               **smeta)
        print("occluders: %d world-shell surface points at %.2f m from %d "
              "objects\n" % (len(SHELL), smeta.get("cell_m", OCC_CELL_M),
                             smeta.get("shell_objects", -1)))
    else:
        print(">> NO SHELL GIVEN (--shell): occlusion will NOT be subtracted, "
              "so every count below is the loose bound.\n")
    report["occlusion_subtracted"] = bool(SHELL is not None and not a.no_occlusion)

    sw = sweep(P, H, MID, len(names), path, stride=a.stride, shell=SHELL)
    if a.no_occlusion or SHELL is None:
        sw["sharp"], sw["sharp_f"] = sw["sharp_no_occ"], sw["sharp_no_occ_f"]
    report["frames"] = sw["nframes"]
    report["frames_swept"] = sw["frames_swept"]
    report["stride"] = a.stride

    # MEASURED per-instance height, per source mesh. The source mesh's own z
    # extent is NOT the height of anything: `build_terrain.gn_kind()` normalises
    # every library mesh to UNIT HEIGHT and puts the real size in the instance
    # scale, so `VEG_grass_reed_F03_u` has a 0.99 m mesh and 1.74 m plants.
    # Reporting only the mesh extent invites exactly that misreading.
    hmed = np.zeros(len(names))
    hmax_i = np.zeros(len(names))
    Hall = np.asarray(c["H"])
    MIDall = np.asarray(c["MID"])
    order = np.argsort(MIDall, kind="stable")
    Ms, Hs = MIDall[order], Hall[order]
    bnd = np.searchsorted(Ms, np.arange(len(names) + 1))
    for i in cand:
        seg = Hs[bnd[i]:bnd[i + 1]]
        if len(seg):
            hmed[i] = float(np.median(seg))
            hmax_i[i] = float(seg.max())

    key = a.recog_px
    rows = []
    for i in cand:
        row = {"source_mesh": names[i], "example_object": obj_of[i],
               "instances": int(n_use[i]),
               "as_objects": int(n_obj[i]), "as_gn_instances": int(n_ins[i]),
               "source_mesh_z_extent_m": round(float(np.asarray(c["zext"])[i]), 3),
               "instance_height_median_m": round(float(hmed[i]), 3),
               "instance_height_max_m": round(float(hmax_i[i]), 3),
               "exempt": exempt_reason(obj_of[i])}
        for thr in RECOG_PX_LADDER:
            row["px%d" % int(thr)] = {
                "peak_covisible": int(sw["peak"][thr][i]),
                "frame": int(sw["peak_f"][thr][i]),
                "sharp_at_that_frame": int(sw["sharp_at_peak"][thr][i]),
                "peak_covisible_sharp": int(sw["sharp"][thr][i]),
                "sharp_frame": int(sw["sharp_f"][thr][i]),
                "peak_covisible_sharp_no_occlusion":
                    int(sw["sharp_no_occ"][thr][i]),
                "sharp_frame_no_occlusion": int(sw["sharp_no_occ_f"][thr][i])}
        rows.append(row)
    rows.sort(key=lambda r: -r["px%d" % int(key)]["peak_covisible_sharp"])
    report["sources"] = rows

    # ---- the table -------------------------------------------------------
    print("CO-VISIBLE SHARP INSTANCES PER SOURCE MESH -- peak over %d frames, "
          "at >= %.0f px of a %dx%d frame" % (sw["frames_swept"], key,
                                              RES_X, RES_Y))
    print("(sharp = shutter smear <= %.0f px at the flat %.0f deg shutter; "
          "occlusion NOT subtracted)\n" % (SMEAR_SHARP_PX, SHUTTER * 360))
    hdr = ("%-34s%9s%9s%9s%9s%9s%8s   %s"
           % ("source mesh", "used", "inst h m", "covis", "SHARP", "no-occ",
              "frame", "note"))
    print(hdr)
    print("-" * len(hdr))
    for r in rows[:a.top]:
        b = r["px%d" % int(key)]
        note = "EXEMPT " + r["exempt"].split(":")[0] if r["exempt"] else ""
        print("%-34s%9d%9.2f%9d%9d%9d%8d   %s"
              % (r["source_mesh"][:34], r["instances"],
                 r["instance_height_median_m"],
                 b["peak_covisible"], b["peak_covisible_sharp"],
                 b["peak_covisible_sharp_no_occlusion"],
                 b["sharp_frame"], note))
    print("\n('inst h m' is the MEASURED median height of that mesh's "
          "instances, not the mesh's own extent -- the library meshes are "
          "normalised to unit height and the size lives in the instance scale.)")

    print("\nthe ladder, worst source mesh at each size (sharp):")
    print("%-12s%-34s%9s%9s" % ("recog px", "source mesh", "SHARP", "frame"))
    ladder_worst = {}
    for thr in RECOG_PX_LADDER:
        vals = [(int(sw["sharp"][thr][i]), i) for i in cand]
        v, i = max(vals) if vals else (0, cand[0])
        vn, jn = max([(int(sw["sharp_no_occ"][thr][j]), j) for j in cand]) \
            if len(cand) else (0, cand[0])
        ladder_worst["px%d" % int(thr)] = {
            "source_mesh": names[i], "peak_covisible_sharp": v,
            "frame": int(sw["sharp_f"][thr][i]),
            "worst_no_occlusion": names[jn],
            "peak_covisible_sharp_no_occlusion": vn,
            "exempt": exempt_reason(obj_of[i])}
        print("%-12s%-34s%9d%9d   (no-occ: %s %d)"
              % (">= %d" % int(thr), names[i][:34], v,
                 int(sw["sharp_f"][thr][i]), names[jn][:26], vn))
    report["ladder_worst"] = ladder_worst

    # ---- the verdict: unexempt first, then exempt -----------------------
    n_exempt = sum(1 for r in rows if r["exempt"])
    report["exemptions_matched"] = n_exempt
    print("\nexemptions: the table has %d entr%s and matched %d of the %d "
          "repeated source meshes in this scene."
          % (len(EXEMPT), "y" if len(EXEMPT) == 1 else "ies", n_exempt,
             len(rows)))

    worst_all = rows[0] if rows else None
    unex = [r for r in rows if not r["exempt"]]
    worst_unex = unex[0] if unex else None
    over_all = [r for r in rows
                if r["px%d" % int(key)]["peak_covisible_sharp"] >= a.spam_cvr]
    over_unex = [r for r in over_all if not r["exempt"]]
    report["worst_source_mesh"] = worst_all
    report["worst_unexempt_source_mesh"] = worst_unex
    report["over_spam_cvr"] = [r["source_mesh"] for r in over_all]
    report["over_spam_cvr_unexempt"] = [r["source_mesh"] for r in over_unex]

    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    json.dump(report, open(a.out, "w"), indent=1)
    print("\nwrote %s" % a.out)

    if worst_all:
        b = worst_all["px%d" % int(key)]
        print("\nworst source mesh in the film, BEFORE any exemption: %s at "
              "%d co-visible sharp copies (f%d), against the named failure of "
              "%.0f" % (worst_all["source_mesh"], b["peak_covisible_sharp"],
                        b["sharp_frame"], a.spam_cvr))
    if over_all and not over_unex:
        print(">> %d source mesh/meshes reach %.0f, and EVERY ONE OF THEM IS "
              "EXEMPT hardware. Listed so the exemption cannot hide them:"
              % (len(over_all), a.spam_cvr))
        for r in over_all:
            print("     %-30s %d copies -- %s"
                  % (r["source_mesh"],
                     r["px%d" % int(key)]["peak_covisible_sharp"], r["exempt"]))
    if over_unex:
        print(">> %d SOURCE MESH/MESHES REACH THE NAMED FAILURE: %.0f "
              "co-visible SHARP copies of one mesh." % (len(over_unex),
                                                        a.spam_cvr))
        for r in over_unex:
            b = r["px%d" % int(key)]
            print("     %-30s %d copies at f%d (%d instances in the world)"
                  % (r["source_mesh"], b["peak_covisible_sharp"],
                     b["sharp_frame"], r["instances"]))
        return gate_exit.verdict("INSTANCE_VARIETY_SPAM",
                                 "  [%s]" % ",".join(r["source_mesh"]
                                                     for r in over_unex[:6]))
    print(">> no unexempt source mesh reaches %.0f co-visible sharp copies "
          "anywhere in the film." % a.spam_cvr)
    return gate_exit.verdict("INSTANCE_VARIETY_CLEAN")


if __name__ == "__main__":
    gate_exit.guard(main, tool="instance_variety")
