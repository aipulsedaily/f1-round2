#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
r2581_nearfield_sweep.py — WHERE ALONG THE WHOLE LAP DOES TRACKSIDE GEOMETRY
FILL THE NEAR FIELD WHILE THE SUBJECT IS A CHIP?

    .venv/bin/python tools/r2581_nearfield_sweep.py --selftest
    .venv/bin/python tools/r2581_nearfield_sweep.py --json render/r2581/nearfield.json
    .venv/bin/python tools/r2581_nearfield_sweep.py --frames 2180,2200 --verbose

WHY IT EXISTS
-------------
R2-584 read two frames with a ruler: at f2180 something fills the bottom right
while the car is a 52-px silhouette, and at f2200 two concrete pylons occupy the
left and right thirds while the car sits between them.  Two frames is two
frames.  This sweeps all 2,978 and asks the same question of every one of them,
so that a run of frames can be attributed to a NAMED structure at a NAMED
station instead of to "architecture".

It also settles the attribution, which the eye got wrong: R2-584 called f2180's
foreground "a motion-smeared grandstand structure".  It is not a grandstand.  It
is `ARCH_PontPlongee`, the bridge at lap station 2410 m, and it is the SAME
structure as f2200's pylons, 20 frames earlier in its own pass.

WHAT IT REPORTS, per film frame
-------------------------------
    subj_px / subj_frac_w
        the car's oriented bounding box (5.698 x 2.005 x 0.992 m, world_contract
        CAR_BODY_*) projected through that frame's own pose and focal, as
        delivered pixels of WIDTH and as a fraction of the 3840 px frame.  This
        is `tools/lap_shotscale.py`'s metric, IMPORTED not re-implemented, so it
        carries that tool's five-frame ruler calibration with it.
    near_frac
        the fraction of the delivered frame covered by built trackside
        structures that are CLOSER TO THE CAMERA THAN THE CAR.  Measured as the
        UNION (never the sum) of the projected 1 m occupancy voxels of those
        structures, rasterised into a 192 x 108 coverage grid.
    near_frac_ub
        the same thing from whole-cluster BOUNDING BOXES rather than voxels.  A
        bounding box is a coarse over-estimate — it fills in the sky between a
        grandstand's roof and its stanchions — so this is an UPPER BOUND and is
        reported as one.  `near_frac` is the honest number; `near_frac_ub` is
        the bracket above it.  Nothing in the report below rests on _ub alone.
    veg_frac
        the same union for trees, hedges and shrubs, kept in a SEPARATE channel:
        a tree whipping past is not the same defect as a grandstand, and mixing
        them would let vegetation manufacture a structural finding.
    worst_owner / worst_frac
        which single named object contributes the most of `near_frac`, so a run
        of frames gets attributed to `ARCH_Grandstand_01_T15`, not to a genus.
    ring_frac / clear_px / on_subject
        near_frac cannot tell FRAMING from CROWDING.  At f1191 the start/finish
        gantry covers 0.227 of the frame across the top and both sides with the
        car clear in the middle of it; at f2180 the bridge covers 0.432 and is
        touching the car.  Those are not the same event and a single coverage
        number calls them one.  So: `ring_frac` is the coverage inside a box
        0.3 frame-widths across centred on the car, `clear_px` the gap in
        delivered pixels from the car's projected box to the nearest covered
        cell, and `on_subject` whether the near field overlaps the car at all.
    near_frac_ref40
        the same measurement at a FIXED 40 mm reference focal.  A lens fix is
        landing on f2012-f2256; near_frac moves with it, this does not.  Where
        the near field is crowded is a property of the path and the placements.

WHERE THE GEOMETRY COMES FROM, AND WHAT THAT COSTS
--------------------------------------------------
`docs/screen_presence_points.npz` — the headless 1 m voxelisation of the built
world (`render/world/assembly/r2/assembly9.blend`, 560 named objects, 3.05 M
points, each the centre of an occupied 1 m cell).  Building the world again
would produce the same placements; this is that build, already done, and it
costs no memory on a box that is already swapping.  Four consequences, stated
rather than buried:

  * It is assembly9 (2026-08-04 02:01).  `render/film16.blend` has since added
    ~1,707 placed objects from `world/items/`.  Those are small items, but they
    are ADDITIONAL near-field geometry, so every near_frac here is a floor with
    respect to the shipping build, not a ceiling.
  * The voxels follow the source meshes' VERTICES, so a coarsely tessellated
    face is sampled round its rim and left hollow in the middle.  The f2200
    overlay shows exactly that on the bridge pylons.  `close1()` fills holes one
    cell wide, which recovers most of it; what remains is an UNDER-read, and it
    is the reason `near_frac` is treated below as a lower bound.
  * A catch fence 40 mm thick reads as a 1 m slab, so lattice OVER-reads.  This
    is not a rendered alpha and it does not know a fence is see-through.
  * It is geometry at the shutter's centre instant.  The delivered frames carry
    a 180-degree shutter and a camera doing up to 97 m/s, so a structure 20 m
    away smears across hundreds of pixels; `near_frac` measures where it IS,
    not how far its smear reaches.

WHAT THIS IS NOT
----------------
Not occlusion-aware between structures — but it does not need to be: coverage is
a UNION over things nearer than the car, and a near thing hiding a slightly less
near thing changes no covered cell.  It IS blind to the car being hidden BEHIND
a structure (`subj_px` is the projected size whether or not you can see it), and
blind to motion blur, which at these focal lengths smears a passing structure
WIDER than its geometry — so on the smeared frames `near_frac` under-reads.

THE CONTROLS, and the sweep is worth nothing without them
---------------------------------------------------------
This project has had about a third of its findings turn out to be broken
instruments.  Two detectors written for R2-422 returned 0.90 and 1.00 for a car
occupying 0.47 by latching onto a turntable and a back wall.  So `--selftest`
runs controls that this instrument must FAIL if it is one of those:

    empty sky        camera 5 km above the geometry     -> near_frac == 0
    absent subject   zero-volume car                    -> subj_px  == 0
    depth gate       a wall BEHIND the car              -> near_frac == 0
    positive         the same wall in front of the car  -> near_frac == 1
    union not sum    two coincident walls               -> same as one wall
    hand-computed    car at 100 m, 50 mm lens           -> 5.698*fpx/98.9975 px
    displaced        car moved 500 m sideways           -> subj_px collapses
    quantisation     one voxel of known angular size    -> within one grid cell
    closing/empty    hole-filling an empty grid         -> adds nothing
    closing/isolated hole-filling one lone cell         -> stays one cell
    closing/bridge   two cells 35 apart                 -> stays two cells
    ub >= union      cluster bound vs voxel union       -> never below it
    attribution      big far wall vs small near post    -> owner is the wall

Confirmed against DELIVERED PIXELS at four frames with `--overlay`: f1191
(gantry), f2180 and f2200 (bridge) and f2714 (main grandstand), plus f2270 as a
negative (near_frac 0.000 on a frame with nothing in the foreground).  The f2200
overlay is also where the under-read was quantified: a ruler on the delivered
frame puts the bridge at 0.42 of it against this tool's 0.267.

Blender is not involved.  Judge on the printed `>> STAGE RESULT:` line.
"""
import argparse
import collections
import json
import math
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "world"))

# The beat table, `quat_to_mat` and the frame geometry come from R2-651's tool.
# tools/r2366_surface_visibility.py has a DIFFERENT beat table (beat4 1057-2100)
# which is wrong by 910 frames against the shipped rig; it is not used here.
from r2651_track_scale import W, H, SENSOR, BEATS, beat_of, quat_to_mat  # noqa: E402
import lap_shotscale as LS                                              # noqa: E402

POINTS_NPZ = os.path.join(ROOT, "docs/screen_presence_points.npz")
POINTS_META = os.path.join(ROOT, "docs/screen_presence_objects.json")
PATH_JSON = os.path.join(ROOT, "world/camera_rig_path.json")
DOF_JSON = os.path.join(ROOT, "render/r2651/dof.json")
VOXEL_M = 1.0                     # the point cloud's own cell size
GRID = (192, 108)                 # coverage grid: 20 x 20 delivered px per cell
REF_LENS = 40.0                   # the lens-independent reference focal

# ---------------------------------------------------------------------------
# CLASSIFICATION.  Printed in full by --classify so it can be audited, because
# "which objects count as a trackside structure" is the one judgement call in
# this instrument and it must not be hidden inside a regex.
# ---------------------------------------------------------------------------
GROUND_TOKENS = ("Paving", "Markings", "RetainEdge", "Terrace", "ServiceRoad",
                 "Ground_Planting", "Verge", "Subbase", "Runoff", "Trap_",
                 "Stones_", "Kerb", "Paint", "GridNum", "AccessRoad",
                 "ApronJoint")
TALL_VEG = ("tree_", "hedge_", "shrub_", "sapling", "avenue")


def classify(name):
    """-> 'structure' | 'veg' | 'ground' | 'lowveg'."""
    if name.startswith(("SURF_", "TER_")):
        return "ground"
    if name.startswith("VEG_"):
        return "veg" if any(t in name for t in TALL_VEG) else "lowveg"
    if any(t in name for t in GROUND_TOKENS):
        return "ground"
    if name.startswith(("ARCH_", "BR_", "DR_")):
        return "structure"
    return "ground"


# ---------------------------------------------------------------------------
# The world, as occupancy voxels.
# ---------------------------------------------------------------------------
class World(object):
    """Structure and vegetation voxels, plus a terrain height field.

    `min_height_m` drops voxels sitting on the deck: painted ground ads
    (DR_Ad_000, z -0.5..0.5) are dressing, not structures, and counting them
    would put the whole apron in the near field on every paddock frame.
    """

    def __init__(self, npz=POINTS_NPZ, min_height_m=0.6, cell_m=32.0,
                 cluster_m=3.0, quiet=False):
        z = np.load(npz, allow_pickle=True)
        names = [str(s) for s in z["names"]]
        pts = np.asarray(z["pts"], dtype=np.float64)
        obj = np.asarray(z["obj"], dtype=np.int32)
        self.names = names
        kind = np.array([classify(n) for n in names])

        # --- terrain height field, from the ground classes, 20 m cells -------
        gmask = np.isin(obj, np.flatnonzero(kind == "ground"))
        gp = pts[gmask]
        self.h_cell = 20.0
        self.h_org = np.floor(pts.min(0)[:2] / self.h_cell) * self.h_cell
        nx = int(np.ceil((pts[:, 0].max() - self.h_org[0]) / self.h_cell)) + 2
        ny = int(np.ceil((pts[:, 1].max() - self.h_org[1]) / self.h_cell)) + 2
        ix = np.clip(((gp[:, 0] - self.h_org[0]) / self.h_cell).astype(int), 0, nx - 1)
        iy = np.clip(((gp[:, 1] - self.h_org[1]) / self.h_cell).astype(int), 0, ny - 1)
        acc = np.full((nx, ny), np.nan)
        # lowest ground sample in each cell: the deck, not the top of a kerb
        np.minimum.at(acc, (ix, iy), gp[:, 2])
        # fill holes with the global median so a cell with no ground sample
        # does not delete the structures standing in it
        med = float(np.nanmedian(gp[:, 2]))
        acc[np.isnan(acc)] = med
        self.hgrid = acc
        self.hshape = (nx, ny)

        def height_above_ground(P):
            jx = np.clip(((P[:, 0] - self.h_org[0]) / self.h_cell).astype(int), 0, nx - 1)
            jy = np.clip(((P[:, 1] - self.h_org[1]) / self.h_cell).astype(int), 0, ny - 1)
            return P[:, 2] - self.hgrid[jx, jy]

        self.channels = {}
        for chan, want in (("structure", "structure"), ("veg", "veg")):
            m = np.isin(obj, np.flatnonzero(kind == want))
            P = pts[m]
            O = obj[m]
            hh = height_above_ground(P)
            keep = hh >= min_height_m
            self.channels[chan] = dict(P=P[keep], O=O[keep],
                                       n_raw=int(m.sum()), n_low=int((~keep).sum()))
        self.cell_m = cell_m
        for chan, d in self.channels.items():
            d["index"] = self._build_index(d["P"], cell_m)
            d["clusters"] = self._cluster(d["P"], d["O"], cluster_m)
        if not quiet:
            self.describe()

    # -- coarse XY bucket index so a frame touches only nearby voxels --------
    @staticmethod
    def _build_index(P, cell_m):
        if len(P) == 0:
            return dict(keys=np.zeros((0, 2)), order=np.zeros(0, dtype=int),
                        start=np.zeros(1, dtype=int), ctr=np.zeros((0, 3)),
                        rad=np.zeros(0))
        c = np.floor(P[:, :2] / cell_m).astype(np.int64)
        key = c[:, 0] * 1000003 + c[:, 1]
        order = np.argsort(key, kind="stable")
        ks = key[order]
        first = np.flatnonzero(np.r_[True, ks[1:] != ks[:-1]])
        start = np.r_[first, len(ks)]
        Ps = P[order]
        ctr = np.array([Ps[start[i]:start[i + 1]].mean(0) for i in range(len(first))])
        rad = np.array([np.linalg.norm(Ps[start[i]:start[i + 1]] - ctr[i], axis=1).max()
                        for i in range(len(first))])
        return dict(P=Ps, order=order, start=start, ctr=ctr, rad=rad + 0.87)

    # -- connected components at `cl_m`, per object, for the bbox upper bound
    @staticmethod
    def _cluster(P, O, cl_m):
        out_lo, out_hi, out_o = [], [], []
        for oid in np.unique(O):
            sel = O == oid
            Q = P[sel]
            cells = np.floor(Q / cl_m).astype(np.int64)
            uniq, inv = np.unique(cells, axis=0, return_inverse=True)
            lut = {tuple(c): i for i, c in enumerate(map(tuple, uniq))}
            seen = np.zeros(len(uniq), dtype=bool)
            for i in range(len(uniq)):
                if seen[i]:
                    continue
                stack = [i]
                seen[i] = True
                comp = []
                while stack:
                    k = stack.pop()
                    comp.append(k)
                    cx, cy, cz = uniq[k]
                    for dx in (-1, 0, 1):
                        for dy in (-1, 0, 1):
                            for dz in (-1, 0, 1):
                                j = lut.get((cx + dx, cy + dy, cz + dz))
                                if j is not None and not seen[j]:
                                    seen[j] = True
                                    stack.append(j)
                mm = np.isin(inv, comp)
                out_lo.append(Q[mm].min(0) - 0.5 * VOXEL_M)
                out_hi.append(Q[mm].max(0) + 0.5 * VOXEL_M)
                out_o.append(oid)
        if not out_lo:
            return dict(lo=np.zeros((0, 3)), hi=np.zeros((0, 3)),
                        o=np.zeros(0, dtype=int), ctr=np.zeros((0, 3)),
                        rad=np.zeros(0))
        lo = np.array(out_lo)
        hi = np.array(out_hi)
        ctr = 0.5 * (lo + hi)
        return dict(lo=lo, hi=hi, o=np.array(out_o),
                    ctr=ctr, rad=np.linalg.norm(hi - ctr, axis=1))

    def describe(self):
        print(">> world: %s" % os.path.relpath(POINTS_NPZ, ROOT))
        cnt = collections.Counter(classify(n) for n in self.names)
        print("   objects by class: " + "  ".join("%s=%d" % kv for kv in
                                                  sorted(cnt.items())))
        for chan, d in self.channels.items():
            print("   %-10s %7d voxels kept (%d dropped as ground-hugging), "
                  "%d clusters" % (chan, len(d["P"]), d["n_low"],
                                   len(d["clusters"]["o"])))

    def top_objects(self, chan, n=12):
        d = self.channels[chan]
        c = collections.Counter(d["O"].tolist())
        return [(self.names[i], k) for i, k in c.most_common(n)]


# ---------------------------------------------------------------------------
# Rasterisation.  Union of axis-aligned screen rectangles, by the 2-D
# difference-array trick: O(rects + grid), and it is a UNION because the test
# is count > 0, never a sum of areas.
# ---------------------------------------------------------------------------
def close1(cov):
    """Fill single-cell holes in a coverage grid.

    WHY THIS IS HERE, AND WHY IT IS NOT CHEATING.  The point cloud is a
    voxelisation of MESH VERTICES, so a coarsely tessellated face is sampled at
    its corners and edges and left hollow in the middle.  The f2200 overlay
    shows it plainly: the outline of each bridge pylon is covered and its
    interior is not, on a pylon that is manifestly solid in the delivered
    render.  A binary closing with a 3x3 element fills holes ONE CELL wide and
    nothing larger: it cannot join two structures 35 cells apart, it cannot
    grow an isolated cell, and it can only ever add coverage that was already
    surrounded by coverage.  All three of those are asserted in --selftest.

    The padding is not cosmetic.  `ndimage.binary_closing` erodes against a
    False border, so a coverage grid that is genuinely FULL comes back at 0.971
    with its outermost ring eaten — which is how a hole-filler quietly becomes a
    frame-edge shaver.  Dilating into a False ring and eroding against a True
    one leaves a full grid full; the positive control asserts it.
    """
    from scipy import ndimage
    st = np.ones((3, 3), dtype=bool)
    pad = np.pad(cov, 1, constant_values=False)
    d = ndimage.binary_dilation(pad, structure=st)
    e = ndimage.binary_erosion(d, structure=st, border_value=1)
    return e[1:-1, 1:-1]


def rect_union(x0, x1, y0, y1, grid=GRID):
    gx, gy = grid
    sx, sy = W / gx, H / gy
    if len(x0) == 0:
        return np.zeros((gx, gy), dtype=bool)
    c0 = np.clip(np.floor(x0 / sx).astype(np.int64), 0, gx - 1)
    c1 = np.clip(np.ceil(x1 / sx).astype(np.int64) - 1, 0, gx - 1)
    r0 = np.clip(np.floor(y0 / sy).astype(np.int64), 0, gy - 1)
    r1 = np.clip(np.ceil(y1 / sy).astype(np.int64) - 1, 0, gy - 1)
    good = (x1 > 0) & (x0 < W) & (y1 > 0) & (y0 < H) & (c1 >= c0) & (r1 >= r0)
    c0, c1, r0, r1 = c0[good], c1[good], r0[good], r1[good]
    d = np.zeros((gx + 1, gy + 1), dtype=np.int32)
    np.add.at(d, (c0, r0), 1)
    np.add.at(d, (c1 + 1, r0), -1)
    np.add.at(d, (c0, r1 + 1), -1)
    np.add.at(d, (c1 + 1, r1 + 1), 1)
    cov = np.cumsum(np.cumsum(d, axis=0), axis=1)[:gx, :gy]
    return cov > 0


class Frame(object):
    """One camera pose, ready to project world points."""

    def __init__(self, p, q, lens):
        self.p = np.asarray(p, dtype=np.float64)
        self.R = quat_to_mat(q)
        self.fpx = (float(lens) / SENSOR) * W
        self.fwd = -self.R[:, 2]

    def project(self, P):
        V = P - self.p
        Cm = V @ self.R
        depth = -Cm[:, 2]
        d = np.linalg.norm(V, axis=1)
        return Cm, depth, d

    def voxel_rects(self, P, depth, Cm, half_m=0.5 * VOXEL_M):
        """Screen AABB of a `half_m`-radius camera-facing square at each point."""
        s = self.fpx / depth
        x = Cm[:, 0] * s + W * 0.5
        y = -Cm[:, 1] * s + H * 0.5
        h = half_m * s
        return x - h, x + h, y - h, y + h

    def box_rects(self, lo, hi):
        """Screen AABB of each world AABB.  Boxes straddling the camera plane
        are dropped, not clamped: a perspective divide near zero manufactures a
        full-frame rectangle, which is exactly how a coverage metric comes to
        return 1.00 for nothing."""
        n = len(lo)
        if n == 0:
            z = np.zeros(0)
            return z, z, z, z
        corners = np.empty((n, 8, 3))
        for i in range(8):
            corners[:, i, 0] = np.where(i & 1, hi[:, 0], lo[:, 0])
            corners[:, i, 1] = np.where(i & 2, hi[:, 1], lo[:, 1])
            corners[:, i, 2] = np.where(i & 4, hi[:, 2], lo[:, 2])
        V = corners - self.p
        Cm = V @ self.R
        dep = -Cm[..., 2]
        ok = dep.min(axis=1) > 0.05
        safe = np.maximum(dep, 1e-6)
        x = Cm[..., 0] * self.fpx / safe + W * 0.5
        y = -Cm[..., 1] * self.fpx / safe + H * 0.5
        x0 = np.where(ok, x.min(axis=1), 1e9)
        x1 = np.where(ok, x.max(axis=1), -1e9)
        y0 = np.where(ok, y.min(axis=1), 1e9)
        y1 = np.where(ok, y.max(axis=1), -1e9)
        return x0, x1, y0, y1


def coverage_mask(world, chan, fr, d_limit, grid=GRID, max_range=None,
                  only_obj=None):
    """The boolean coverage grid itself, for drawing over a delivered frame."""
    d = world.channels[chan]
    idx = d["index"]
    rng = d_limit if max_range is None else min(d_limit, max_range)
    vc = idx["ctr"] - fr.p
    keep = np.flatnonzero(np.linalg.norm(vc, axis=1) - idx["rad"] < rng)
    if len(keep) == 0:
        return np.zeros(grid, dtype=bool)
    sl = np.concatenate([np.arange(idx["start"][k], idx["start"][k + 1])
                         for k in keep])
    P = idx["P"][sl]
    O = d["O"][idx["order"][sl]]
    Cm, depth, dist = fr.project(P)
    m = (depth > 0.05) & (dist < rng)
    if only_obj is not None:
        m &= (O == only_obj)
    if not m.any():
        return np.zeros(grid, dtype=bool)
    x0, x1, y0, y1 = fr.voxel_rects(P[m], depth[m], Cm[m])
    return close1(rect_union(x0, x1, y0, y1, grid))


def near_measure(world, chan, fr, d_limit, grid=GRID, want_owner=True,
                 max_range=None):
    """Coverage of `chan` voxels nearer than `d_limit`.  Returns a dict."""
    d = world.channels[chan]
    idx = d["index"]
    ncell = len(idx["ctr"])
    out = dict(frac=0.0, frac_open=0.0, frac_ub=0.0, owner=None,
               owner_frac=0.0, n=0)
    if ncell == 0 or not np.isfinite(d_limit) or d_limit <= 0:
        return out
    rng = d_limit if max_range is None else min(d_limit, max_range)

    # 1. bucket cull: keep XY buckets whose bounding sphere reaches inside rng
    vc = idx["ctr"] - fr.p
    dc = np.linalg.norm(vc, axis=1)
    keep = np.flatnonzero(dc - idx["rad"] < rng)
    if len(keep) == 0:
        return out
    sl = np.concatenate([np.arange(idx["start"][k], idx["start"][k + 1])
                         for k in keep])
    P = idx["P"][sl]
    O = d["O"][idx["order"][sl]]

    Cm, depth, dist = fr.project(P)
    m = (depth > 0.05) & (dist < rng)
    if not m.any():
        return out
    Cm, depth, O = Cm[m], depth[m], O[m]
    x0, x1, y0, y1 = fr.voxel_rects(P[m], depth, Cm)
    cov = rect_union(x0, x1, y0, y1, grid)
    out["frac_open"] = float(cov.mean())
    cov = close1(cov)
    out["frac"] = float(cov.mean())
    out["n"] = int(m.sum())

    if want_owner and out["frac"] > 0:
        # rank candidates by clipped screen area (cheap), then measure the real
        # union coverage of the top few (honest, but only a few times)
        area = ((np.minimum(x1, W) - np.maximum(x0, 0)).clip(0)
                * (np.minimum(y1, H) - np.maximum(y0, 0)).clip(0))
        tot = np.bincount(O, weights=area, minlength=len(world.names))
        cand = np.argsort(tot)[::-1][:5]
        best, bestf = None, 0.0
        for oid in cand:
            if tot[oid] <= 0:
                continue
            s = O == oid
            c = close1(rect_union(x0[s], x1[s], y0[s], y1[s], grid))
            f = float(c.mean())
            if f > bestf:
                best, bestf = int(oid), f
        out["owner"] = world.names[best] if best is not None else None
        out["owner_frac"] = bestf

    # 2. the bounding-box upper bound, from the clusters
    cl = d["clusters"]
    vcc = cl["ctr"] - fr.p
    dcc = np.linalg.norm(vcc, axis=1)
    k = np.flatnonzero(dcc - cl["rad"] < rng)
    if len(k):
        bx0, bx1, by0, by1 = fr.box_rects(cl["lo"][k], cl["hi"][k])
        out["frac_ub"] = float(rect_union(bx0, bx1, by0, by1, grid).mean())
    return out


# ---------------------------------------------------------------------------
# Stations along the lap, for naming where a run happens.
# ---------------------------------------------------------------------------
def subject_screen_box(k, car, world_t, f):
    """The car's projected screen AABB in delivered pixels, or None."""
    pos, yaw, pit, rol, _v, _s = car.at(world_t[f])
    rt, up, fwd = LS.basis(k["q"])
    xs, ys = [], []
    for p in LS.obb_corners(pos, yaw, pit, rol):
        v = [p[j] - k["p"][j] for j in range(3)]
        z = LS.dot(v, fwd)
        if z <= 1e-6:
            return None
        xs.append((LS.dot(v, rt) / z * k["lens"] / SENSOR + 0.5) * W)
        ys.append((0.5 - LS.dot(v, up) / z * k["lens"] / SENSOR * W / H) * H)
    return min(xs), max(xs), min(ys), max(ys)


def crowding(cov, box, grid=GRID):
    """How close the near field comes to the SUBJECT, not merely to the frame.

    near_frac cannot tell a gantry that brackets the car (f1191: structure top,
    left and right, centre clear) from a bridge sweeping through it (f2180).
    So: the gap in delivered pixels from the car's projected box to the nearest
    covered cell, and the coverage inside a box 0.3 frame-widths across centred
    on the car.  Zero gap means the near field is touching the subject.
    """
    from scipy import ndimage
    out = dict(clear_px=None, ring_frac=None, on_subject=None)
    if box is None or not cov.any():
        return out
    gx, gy = cov.shape
    sx, sy = W / gx, H / gy
    x0, x1, y0, y1 = box
    c0 = int(np.clip(math.floor(x0 / sx), 0, gx - 1))
    c1 = int(np.clip(math.ceil(x1 / sx) - 1, 0, gx - 1))
    r0 = int(np.clip(math.floor(y0 / sy), 0, gy - 1))
    r1 = int(np.clip(math.ceil(y1 / sy) - 1, 0, gy - 1))
    dt = ndimage.distance_transform_edt(~cov, sampling=(sx, sy))
    out["clear_px"] = float(dt[c0:c1 + 1, r0:r1 + 1].min())
    out["on_subject"] = bool(cov[c0:c1 + 1, r0:r1 + 1].any())
    hw = 0.15 * W
    a0 = int(np.clip(math.floor((0.5 * (x0 + x1) - hw) / sx), 0, gx - 1))
    a1 = int(np.clip(math.ceil((0.5 * (x0 + x1) + hw) / sx), 0, gx))
    b0 = int(np.clip(math.floor((0.5 * (y0 + y1) - hw) / sy), 0, gy - 1))
    b1 = int(np.clip(math.ceil((0.5 * (y0 + y1) + hw) / sy), 0, gy))
    sub = cov[a0:a1, b0:b1]
    out["ring_frac"] = float(sub.mean()) if sub.size else 0.0
    return out


def station_table():
    import world_contract as C
    els = C.SPEC["elements"]
    tab, s = [], 0.0
    for e in els:
        L = float(e.get("length_m") or e.get("arc_m") or 0.0)
        tab.append((s, s + L, e.get("name", "?")))
        s += L
    return tab


def station_of(tab, s_m, lap=3675.0):
    s = s_m % lap
    for a, b, n in tab:
        if a <= s < b:
            return n
    return tab[-1][2]


# ---------------------------------------------------------------------------
def build_subject(path_json):
    """Per-frame (subj_frac_w, d_car, lens, s_m) from telemetry through
    anim/filmtime, exactly as tools/lap_shotscale.py does it."""
    sheet = json.load(open(os.path.join(ROOT, "docs/beat_sheet.json")))
    total = sheet["total_frames"]
    world_t = LS.build_world_time(sheet, total)
    car = LS.Car(os.path.join(ROOT, "telemetry/telemetry.csv"))
    path = LS.load_path(path_json)
    ser = LS.series(path, car, world_t, lo=1, hi=total)
    smd = {}
    for f in range(1, total + 1):
        _pos, _y, _p, _r, _v, s_m = car.at(world_t[f])
        smd[f] = s_m
    return path, ser, smd, world_t, car, total


def run(a):
    world = World(min_height_m=a.min_height)
    path, ser, smd, world_t, car, total = build_subject(a.path)
    tab = station_table()
    dof = {r["f"]: r for r in json.load(open(DOF_JSON))["frames"]}

    frames = range(1, total + 1)
    if a.frames:
        frames = []
        for tok in a.frames.split(","):
            if "-" in tok:
                b, e = tok.split("-")
                frames += list(range(int(b), int(e) + 1))
            else:
                frames.append(int(tok))

    rows = []
    for f in frames:
        k = path.get(f)
        if k is None:
            continue
        fr = Frame(k["p"], k["q"], k["lens"])
        fw, dcar, lens = ser[f]
        subj_px = fw * W if fw == fw else float("nan")
        dlim = dcar if dcar == dcar else 0.0
        st = near_measure(world, "structure", fr, dlim, max_range=a.max_range)
        vg = near_measure(world, "veg", fr, dlim, want_owner=False,
                          max_range=a.max_range)
        # LENS-INDEPENDENT COMPANION.  A lens fix is landing on f2012-f2256, so
        # "how crowded is the near field here" must be answerable as a property
        # of the PATH and the PLACEMENTS alone.  Same pose, same depth gate, a
        # fixed 40 mm reference focal — the beat's own median is 45 mm.
        ref = near_measure(world, "structure", Frame(k["p"], k["q"], REF_LENS),
                           dlim, want_owner=False, max_range=a.max_range)
        cov = coverage_mask(world, "structure", fr, dlim, max_range=a.max_range)
        cr = crowding(cov, subject_screen_box(k, car, world_t, f))
        r = dict(f=f, beat=beat_of(f), lens=round(lens, 3),
                 subj_px=None if subj_px != subj_px else round(subj_px, 1),
                 subj_frac_w=None if fw != fw else round(fw, 5),
                 d_car=None if dcar != dcar else round(dcar, 2),
                 near_frac=round(st["frac"], 4),
                 near_frac_open=round(st["frac_open"], 4),
                 near_frac_ub=round(st["frac_ub"], 4),
                 near_frac_ref40=round(ref["frac"], 4),
                 clear_px=None if cr["clear_px"] is None else round(cr["clear_px"], 1),
                 ring_frac=None if cr["ring_frac"] is None else round(cr["ring_frac"], 4),
                 on_subject=cr["on_subject"],
                 veg_frac=round(vg["frac"], 4),
                 worst_owner=st["owner"], worst_frac=round(st["owner_frac"], 4),
                 s_m=round(smd[f], 1), station=station_of(tab, smd[f]),
                 fstop=dof.get(f, {}).get("fstop"),
                 focus=dof.get(f, {}).get("focus"))
        rows.append(r)
        if a.verbose or (a.frames and len(frames) <= 40):
            print("  f%-5d %-9s lens %6.1f  subj %6.1f px (%5.2f %%)  d_car %6.1f  "
                  "near %5.3f (ub %5.3f)  veg %5.3f  %-28s %5.3f  %s"
                  % (f, r["beat"], lens, subj_px if subj_px == subj_px else -1,
                     100 * fw if fw == fw else -1, dcar if dcar == dcar else -1,
                     r["near_frac"], r["near_frac_ub"], r["veg_frac"],
                     str(r["worst_owner"])[:28], r["worst_frac"], r["station"]))
        elif f % 200 == 0:
            print("   ... f%d %s near %.3f subj %.2f %%"
                  % (f, r["beat"], r["near_frac"],
                     100 * fw if fw == fw else -1))

    if a.json:
        out = os.path.join(ROOT, a.json)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        json.dump(dict(meta=dict(
            W=W, H=H, grid=list(GRID), voxel_m=VOXEL_M,
            points=os.path.relpath(POINTS_NPZ, ROOT),
            path=os.path.relpath(a.path, ROOT),
            min_height_m=a.min_height, max_range_m=a.max_range,
            note=("near_frac is a UNION of projected 1 m occupancy voxels of "
                  "built structures nearer than the car; near_frac_ub is the "
                  "same from cluster BOUNDING BOXES and is an UPPER BOUND. "
                  "Neither is occlusion-aware w.r.t. the subject, and neither "
                  "knows that a catch fence is see-through.")),
            frames=rows), open(out, "w"))
        print(">> wrote %s (%d frames)" % (out, len(rows)))
    print(">> STAGE RESULT: R2581_NEARFIELD_SWEEP_OK")
    return rows


# ---------------------------------------------------------------------------
# CONTROLS
# ---------------------------------------------------------------------------
def _synthetic_world(P, O, names):
    """A World with hand-placed voxels and no terrain filtering."""
    w = World.__new__(World)
    w.names = names
    w.channels = {
        "structure": dict(P=P, O=O, n_raw=len(P), n_low=0,
                          index=World._build_index(P, 32.0),
                          clusters=World._cluster(P, O, 3.0)),
        "veg": dict(P=np.zeros((0, 3)), O=np.zeros(0, dtype=int), n_raw=0,
                    n_low=0, index=World._build_index(np.zeros((0, 3)), 32.0),
                    clusters=World._cluster(np.zeros((0, 3)),
                                            np.zeros(0, dtype=int), 3.0)),
    }
    return w


def _wall(x0, x1, z0, z1, y, step=1.0):
    xs = np.arange(x0, x1 + 1e-9, step)
    zs = np.arange(z0, z1 + 1e-9, step)
    X, Z = np.meshgrid(xs, zs)
    return np.c_[X.ravel(), np.full(X.size, y), Z.ravel()]


def selftest():
    ok = True

    def check(good, label, detail):
        nonlocal ok
        ok &= bool(good)
        print("  %s  %-26s %s" % ("PASS" if good else "FAIL", label, detail))

    # a camera at the origin looking along +y, +z up: q = 90 deg about x
    q_y = (math.cos(math.pi / 4), math.sin(math.pi / 4), 0.0, 0.0)
    q_up = (1.0, 0.0, 0.0, 0.0)              # Blender default: looks down -z
    LENS = 50.0
    fpx = LENS / SENSOR * W
    fr = Frame((0.0, 0.0, 0.0), q_y, LENS)

    # ---- 1. EMPTY SKY: nothing in the near field, camera pointed at nothing
    #        The wall is centred on the optical axis (z -15..15) so that the
    #        positive control below is a genuine full-frame case: at 50 m a
    #        50 mm lens sees +-10.1 m vertically, so a wall standing on the
    #        axis would fill only the top half and 0.5 would look like a bug.
    P = _wall(-40, 40, -15, 15, 50.0)
    w = _synthetic_world(P, np.zeros(len(P), dtype=int), ["WALL"])
    up = Frame((0.0, 0.0, 5000.0), q_up, LENS)   # 5 km up, looking DOWN -z...
    # ...and the wall is 5 km below and behind the near limit, so nothing.
    sky = near_measure(w, "structure", up, 100.0)
    check(sky["frac"] == 0.0 and sky["frac_ub"] == 0.0, "empty sky",
          "camera 5 km above the wall with a 100 m near limit: near_frac "
          "%.4f, ub %.4f; both must be exactly 0" % (sky["frac"], sky["frac_ub"]))

    # ---- 2. POSITIVE: the same wall filling the frame 50 m in front
    front = near_measure(w, "structure", fr, 200.0)
    check(front["frac"] > 0.98, "positive/full frame",
          "an 80x30 m wall at 50 m through a %.0f mm lens subtends more than "
          "the frame: near_frac %.4f, must be > 0.98" % (LENS, front["frac"]))

    # ---- 3. DEPTH GATE: the same wall, but the car is nearer than it.
    #        This is the control that decides whether "near field" means
    #        anything at all.  A detector that ignored the limit would still
    #        return ~1.0 here.
    behind = near_measure(w, "structure", fr, 40.0)
    check(behind["frac"] == 0.0, "depth gate/behind car",
          "wall at 50 m with the car at 40 m: near_frac %.4f, must be exactly 0"
          % behind["frac"])

    # ---- 4. UNION NOT SUM: two coincident walls must read as one
    P2 = np.vstack([P, P + np.array([0.0, 0.01, 0.0])])
    O2 = np.r_[np.zeros(len(P), dtype=int), np.ones(len(P), dtype=int)]
    w2 = _synthetic_world(P2, O2, ["WALL", "WALL_TWIN"])
    dbl = near_measure(w2, "structure", fr, 200.0)
    check(abs(dbl["frac"] - front["frac"]) < 1e-9, "union not sum",
          "doubling the wall changes near_frac by %.2e (%.4f vs %.4f); a sum "
          "would have returned ~2" % (abs(dbl["frac"] - front["frac"]),
                                      dbl["frac"], front["frac"]))

    # ---- 5. QUANTISATION: one voxel of known angular size
    one = np.array([[0.0, 200.0, 0.0]])
    w1 = _synthetic_world(one, np.zeros(1, dtype=int), ["VOX"])
    r1 = near_measure(w1, "structure", fr, 300.0)
    side_px = VOXEL_M * fpx / 200.0                    # 26.7 px
    cellf = (W / GRID[0]) * (H / GRID[1]) / float(W * H)
    exact = side_px * side_px / float(W * H)
    check(0 < r1["frac"] <= 4 * cellf + 1e-12, "quantisation",
          "a 1 m voxel at 200 m is %.1f px a side (%.2e of frame); the 20 px "
          "grid reports %.2e, i.e. %d cell(s). Must be >0 and <= 4 cells"
          % (side_px, exact, r1["frac"], round(r1["frac"] / cellf)))

    # ---- 6. HAND-COMPUTED SUBJECT SIZE.  Car at y=100 heading +x: its length
    #        lies across the view, its nearest face is at 100 - 1.0025 m.
    D = 100.0
    corners = LS.obb_corners([0.0, D, 0.0], 0.0, 0.0, 0.0)
    fw, _fh, _b = LS.project(corners, (0.0, 0.0, 0.0), q_y, LENS)
    want = LS.CAR_LEN * fpx / (D - LS.CAR_W / 2.0) / W
    check(abs(fw - want) < 1e-9, "hand-computed subj_px",
          "car 100 m away, %.0f mm: projected %.2f px, closed form "
          "5.698 * %.1f / %.4f = %.2f px" % (LENS, fw * W, fpx,
                                             D - LS.CAR_W / 2.0, want * W))

    # ---- 7. DISPLACED SUBJECT.  The R2-422 failure mode: a detector that reads
    #        the same whether the car is there or not.
    far = LS.obb_corners([0.0, D + 500.0, 0.0], 0.0, 0.0, 0.0)
    fw2, _, _ = LS.project(far, (0.0, 0.0, 0.0), q_y, LENS)
    check(fw2 < 0.2 * fw, "displaced subject",
          "car pushed 500 m further: %.2f px vs %.2f px (%.0f %% of it)"
          % (fw2 * W, fw * W, 100 * fw2 / fw))

    # ---- 8. ZERO-VOLUME SUBJECT
    z = LS.obb_corners([0.0, D, 0.0], 0.0, 0.0, 0.0, scale=0.0)
    fw3, _, _ = LS.project(z, (0.0, 0.0, 0.0), q_y, LENS)
    check(fw3 == 0.0, "absent subject",
          "a zero-volume car reads %.6f px; must be exactly 0" % (fw3 * W))

    # ---- 8b. THE HOLE-FILLING MUST NOT INVENT ANYTHING.  close1() is the one
    #      step that ADDS coverage, so it gets three controls of its own.
    empty = np.zeros(GRID, dtype=bool)
    check(not close1(empty).any(), "closing/empty stays empty",
          "closing an empty grid adds %d cells; must add 0" % close1(empty).sum())
    iso = np.zeros(GRID, dtype=bool)
    iso[50, 50] = True
    check(int(close1(iso).sum()) == 1, "closing/isolated cell",
          "one isolated covered cell closes to %d cells; must stay 1"
          % close1(iso).sum())
    two = np.zeros(GRID, dtype=bool)
    two[40, 50] = True
    two[75, 50] = True                      # 35 cells apart, like the f2200 pylons
    check(int(close1(two).sum()) == 2, "closing/does not bridge",
          "two cells 35 apart close to %d cells; must stay 2" % close1(two).sum())

    # ---- 9. BOX UPPER BOUND >= VOXEL UNION, on the real world.  If the coarse
    #        bound ever came out BELOW the honest one, one of them is wrong.
    world = World(quiet=True)
    path = LS.load_path(PATH_JSON)
    bad = []
    for f in (1200, 1500, 1900, 2000, 2090, 2180, 2200, 2400, 2600, 2700):
        k = path[f]
        ff = Frame(k["p"], k["q"], k["lens"])
        m = near_measure(world, "structure", ff, 300.0)
        if m["frac_ub"] < m["frac"] - 1e-9:
            bad.append((f, m["frac"], m["frac_ub"]))
    check(not bad, "ub >= voxel union",
          "over 10 real beat-5 poses at a 300 m limit; violations: %s" % (bad or "none"))

    # ---- 10. OWNER ATTRIBUTION.  With two walls at different depths, the owner
    #         must be the one that actually covers more of the frame.
    Pa = _wall(-40, 40, -15, 15, 50.0)
    Pb = _wall(-2, 2, -1.5, 1.5, 30.0)
    Pm = np.vstack([Pa, Pb])
    Om = np.r_[np.zeros(len(Pa), dtype=int), np.ones(len(Pb), dtype=int)]
    wm = _synthetic_world(Pm, Om, ["BIG_WALL", "SMALL_POST"])
    om = near_measure(wm, "structure", fr, 200.0)
    check(om["owner"] == "BIG_WALL", "owner attribution",
          "big wall vs small near post: owner %s at %.3f (must be BIG_WALL)"
          % (om["owner"], om["owner_frac"]))

    print(">> STAGE RESULT: %s"
          % ("R2581_NEARFIELD_SELFTEST_OK" if ok else "R2581_NEARFIELD_SELFTEST_FAIL"))
    return ok


def overlay(a):
    """Draw the coverage grid over a DELIVERED frame, so the mask can be judged
    against pixels rather than against itself.  This is the confirmation step:
    a mask that lands on empty asphalt is a broken instrument no matter how
    well its selftest behaves."""
    from PIL import Image
    world = World(min_height_m=a.min_height)
    path, ser, smd, world_t, car, total = build_subject(a.path)
    os.makedirs(os.path.join(ROOT, a.outdir), exist_ok=True)
    for tok in a.overlay.split(","):
        f, src = tok.split("=", 1)
        f = int(f)
        im = Image.open(src).convert("RGB")
        iw, ih = im.size
        k = path[f]
        fr = Frame(k["p"], k["q"], k["lens"])
        fw, dcar, lens = ser[f]
        cov = coverage_mask(world, "structure", fr, dcar, max_range=a.max_range)
        px = np.array(im, dtype=np.float64)
        gx, gy = cov.shape
        # cov is [x, y]; expand to image resolution and tint the covered cells
        cx = np.clip((np.arange(iw) * gx // iw), 0, gx - 1)
        cy = np.clip((np.arange(ih) * gy // ih), 0, gy - 1)
        m = cov[np.ix_(cx, cy)].T                       # -> (ih, iw)
        px[m] = 0.55 * px[m] + 0.45 * np.array([255.0, 0.0, 0.0])
        # the car's projected box, in green
        pos, yaw, pit, rol, _v, _s = car.at(world_t[f])
        cor = LS.obb_corners(pos, yaw, pit, rol)
        rt, up, fwd = LS.basis(k["q"])
        xs, ys = [], []
        for p in cor:
            v = [p[j] - k["p"][j] for j in range(3)]
            z = LS.dot(v, fwd)
            if z <= 1e-6:
                continue
            xs.append((LS.dot(v, rt) / z * lens / SENSOR + 0.5) * iw)
            ys.append((0.5 - LS.dot(v, up) / z * lens / (SENSOR * H / W)) * ih)
        if xs:
            x0, x1 = int(min(xs)), int(max(xs))
            y0, y1 = int(min(ys)), int(max(ys))
            pad = 6
            for (xa, xb, ya, yb) in ((x0 - pad, x1 + pad, y0 - pad, y0 - pad + 2),
                                     (x0 - pad, x1 + pad, y1 + pad - 2, y1 + pad),
                                     (x0 - pad, x0 - pad + 2, y0 - pad, y1 + pad),
                                     (x1 + pad - 2, x1 + pad, y0 - pad, y1 + pad)):
                xa, xb = max(0, xa), min(iw, xb)
                ya, yb = max(0, ya), min(ih, yb)
                if xb > xa and yb > ya:
                    px[ya:yb, xa:xb] = np.array([0.0, 255.0, 0.0])
        out = os.path.join(ROOT, a.outdir, "nf_overlay_%04d.png" % f)
        Image.fromarray(px.astype(np.uint8)).save(out)
        print("   f%-5d near_frac %.3f  subj %.1f px  -> %s"
              % (f, cov.mean(), fw * W, out))
    print(">> STAGE RESULT: R2581_NEARFIELD_OVERLAY_OK")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--overlay", default="",
                    help="f=path.png[,f=path.png...] draw the coverage grid "
                         "over delivered frames")
    ap.add_argument("--outdir", default="docs/peep/r2581")
    ap.add_argument("--path", default=PATH_JSON)
    ap.add_argument("--json", default="")
    ap.add_argument("--frames", default="")
    ap.add_argument("--min-height", type=float, default=0.6)
    ap.add_argument("--max-range", type=float, default=400.0,
                    help="ignore structures further than this even if the car "
                         "is further still; beyond it a structure is scenery, "
                         "not near field")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--classify", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    A = ap.parse_args()
    try:
        if A.selftest:
            sys.exit(0 if selftest() else 1)
        if A.overlay:
            overlay(A)
            sys.exit(0)
        if A.classify:
            wd = World(min_height_m=A.min_height)
            for cl in ("structure", "veg"):
                print("\n== %s: biggest contributors by voxel count" % cl)
                for n, c in wd.top_objects(cl, 25):
                    print("   %-34s %8d" % (n, c))
            sys.exit(0)
        run(A)
    except Exception:
        import traceback
        traceback.print_exc()
        print(">> STAGE RESULT: R2581_NEARFIELD_SWEEP_FAIL (uncaught exception)")
        sys.exit(1)
