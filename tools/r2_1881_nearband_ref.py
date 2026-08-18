"""R2-1881: THE f2760 REFERENCE, and the frames that best EXHIBIT the near-band void.

    .venv/bin/python tools/r2_1881_nearband_ref.py --selftest
    .venv/bin/python tools/r2_1881_nearband_ref.py --frame 2760
    .venv/bin/python tools/r2_1881_nearband_ref.py --scan --out work/r2_1881/scan.json

WHAT IT MEASURES, AND WHY THIS STATISTIC
----------------------------------------
The defect (R2-1884) is a PLACEMENT hole: `build_terrain.habitat()` computes

    wood *= smoothstep(52.0, 150.0, D)          D = |u|, distance to the centreline

so woodland probability is exactly zero inside 52 m of the track, and `wood` gates
woodland, hedgerows, shrubs, saplings and ferns.  The client sees it as "anything 5
feet away from the main road and buildings have blank grass no detail nothing".

A frame exhibits that defect in proportion to HOW MUCH OF THE FRAME is evacuated
near band.  So:

    DEFECT EXPOSURE  E(f) = (screen area in px^2 of ground with D <= 52 m
                             AND no woody instance within 10 m plan distance)
                          / (3840 * 2160)

Screen area is computed per ground sample as (ppm_f)^2 * a_sample, where
ppm_f = (3840 * lens_f / 36) / depth_f is pixels per metre at that sample's depth.
This is the same projection R2-1881/R2-1884 used, and it is a per-FRAME quantity —
R2-1882 records that a control which minimised over all 2,978 frames tested nothing,
because the camera flies.

E(f) is a FRAME statistic, not a film statistic.  It is what a reviewer looking at
one still would see, which is exactly how the client judged it.

WHY 52 m AND 10 m ARE NOT FREE PARAMETERS
-----------------------------------------
52.0 is read out of the failing line in `build_terrain.py:3724`, not chosen.
10 m is R2-1884's published headline threshold, reused so this instrument's numbers
are comparable to the ones already in the log rather than a second scale.
Both are `--band` / `--gap` overridable and both are printed on every run.

THE CONTROLS, AND THEY ARE THE POINT                                      (R2-072)
----------------------------------------------------------------------------------
This project's commonest defect is a broken instrument, so `--selftest` refuses to
report unless a metric that must read BLANK reads blank and one that must read
PLANTED reads planted.  Every control is manufactured at run time from the shipping
world, so none of them expires when the defect is fixed:

  PLANTED (must read 0 % blank)   ground samples placed AT woody instance origins.
        Nearest-woody distance must be 0.000 m and E must be 0.
  BARE (must read ~100 % blank)   ground samples on a ring at D = 10 m from the
        centreline, i.e. inside the 52 m evacuation where `wood` is identically 0 by
        construction.  If this does not read blank the instrument cannot see absence.
  PROJECTION      a point placed on the camera's own forward axis must land on the
        principal point (1920, 1080) to a pixel, and a point 20 m BEHIND the lens and
        a point outside the FOV must both contribute zero area.
  VACUITY         a nearest-neighbour query with the tree set EMPTIED must report
        every sample blank; one with a tree at every sample must report none.  A
        metric that reads the same either way is not a measurement.

WHAT IT DELIBERATELY DOES NOT DO
--------------------------------
No occlusion.  A ground sample behind a grandstand still counts.  `lap_shotscale.py`
is blind to occlusion by declaration (R2-132) and so is this; the number is an upper
bound on exposed void, and it is stated rather than implied.

The point cloud is `work/w2_0/retier_a10/world_points.npz`, dumped from
`render/world/assembly/r2/assembly10.blend`.  A rebuild is in flight; `--points`
re-points this at a newer dump without editing the tool.
"""
import argparse
import json
import math
import os
import sys

import numpy as np

R2 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(R2, "tools"))
sys.path.insert(0, os.path.join(R2, "world"))

import live_campath as LC                                          # noqa: E402

RES_X, RES_Y = 3840, 2160
SENSOR_MM = 36.0
BAND_M = 52.0          # build_terrain.py:3724  smoothstep(52.0, 150.0, D)
GAP_M = 10.0           # R2-1884's published threshold
POINTS = os.path.join(R2, "work", "w2_0", "retier_a10", "world_points.npz")

# Woody = everything `wood` gates.  Trees, hedgerow trees and the avenue carry an
# explicit origin in the dump; shrubs and saplings are picked out of the mesh-point
# cloud by object name, because the dump's `veg_origin` table holds only the first
# three classes and a partial definition of "woody" would understate the void.
WOODY_PREFIX = ("VEG_tree_", "VEG_hedge_", "VEG_avenue",
                "VEG_shrub", "VEG_sapling")


# --------------------------------------------------------------- camera geometry
def qmat(q):
    """Rotation matrix from a [w,x,y,z] quaternion, re-normalised (R2-103)."""
    w, x, y, z = q
    n = math.sqrt(w * w + x * x + y * y + z * z) or 1.0
    w, x, y, z = w / n, x / n, y / n, z / n
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ])


def cam_axes(q):
    """(forward, right, up) in world space.  Blender: forward = -Z, up = +Y."""
    R = qmat(q)
    return -R[:, 2], R[:, 0], R[:, 1]


def project(P, p, q, lens, res=(RES_X, RES_Y)):
    """-> (u_px, v_px, depth, inside).  Pinhole, 36 mm horizontal sensor."""
    fwd, right, up = cam_axes(q)
    d = P - np.asarray(p, float)[None, :]
    depth = d @ fwd
    s = res[0] * lens / SENSOR_MM                 # px per (metre / metre of depth)
    with np.errstate(divide="ignore", invalid="ignore"):
        u = res[0] * 0.5 + s * (d @ right) / depth
        v = res[1] * 0.5 - s * (d @ up) / depth
    inside = (depth > 0.05) & (u >= 0) & (u < res[0]) & (v >= 0) & (v < res[1])
    return u, v, depth, inside


def ppm(depth, lens, res_x=RES_X):
    """Pixels per world metre at `depth`."""
    return (res_x * lens / SENSOR_MM) / depth


# --------------------------------------------------------------------- the world
class World:
    def __init__(self, points=POINTS, nground=60000, seed=1881):
        z = np.load(points, allow_pickle=True)
        names = [str(n) for n in z["names"]]
        obj = z["obj"]
        pts = z["pts"]

        gi = [i for i, n in enumerate(names) if n.startswith("TER_Ground")]
        m = np.isin(obj, gi)
        g = pts[m]
        rng = np.random.default_rng(seed)
        if len(g) > nground:
            g = g[rng.choice(len(g), nground, replace=False)]
        self.ground = g.astype(np.float64)

        wo = [z["veg_origin"].astype(np.float64)]
        wi = [i for i, n in enumerate(names)
              if any(n.startswith(p) for p in WOODY_PREFIX)]
        if wi:
            mm = np.isin(obj, wi)
            if mm.any():
                # one representative point per woody object, not every vertex
                oi = obj[mm]
                pp = pts[mm].astype(np.float64)
                order = np.argsort(oi, kind="stable")
                oi, pp = oi[order], pp[order]
                cut = np.flatnonzero(np.diff(oi)) + 1
                wo.append(np.array([c.mean(axis=0)
                                    for c in np.split(pp, cut)]))
        self.woody = np.vstack(wo)
        self.n_woody_origin = len(z["veg_origin"])
        self.points_file = points

        import world_contract as C                                 # noqa: E402
        self.C = C
        s, u = C.project(self.ground[:, 0], self.ground[:, 1])
        self.D = np.abs(np.asarray(u, float))
        self.a_sample = None            # world m^2 each sample stands for, set below
        self._set_sample_area()
        self.gap = self._nearest_woody(self.ground[:, :2], self.woody[:, :2])

    def _set_sample_area(self):
        """Each ground sample stands for total_ground_area / n_samples.

        The dump is a uniform vertex sample of one mesh, so the samples are equal
        weight by construction; the absolute area only scales E and is reported so
        the scaling is visible rather than hidden.
        """
        x, y = self.ground[:, 0], self.ground[:, 1]
        hull = (x.max() - x.min()) * (y.max() - y.min())
        self.extent_m2 = float(hull)
        self.a_sample = float(hull) / len(self.ground)

    @staticmethod
    def _nearest_woody(g2, w2):
        """Plan distance from each ground sample to the nearest woody instance.

        `scipy.spatial.cKDTree`, which is EXACT.  A fixed-radius grid lookup is the
        cheap alternative and it can return a NEAR MISS when the true nearest sits
        one cell over — R2-1884 named that as the failure mode a 3x3 lookup has —
        so the tree is used and `_brute` below is kept solely as its control.

        Brute force over the real population is 60k x 100k, which is 6.5 GB of
        pairwise distances on an 11 GB box; it is run on a SAMPLE, in the selftest.
        """
        if len(w2) == 0:
            return np.full(len(g2), np.inf)
        from scipy.spatial import cKDTree
        d, _ = cKDTree(np.ascontiguousarray(w2)).query(
            np.ascontiguousarray(g2), k=1, workers=-1)
        return np.asarray(d, float)

    @staticmethod
    def _brute(g2, w2):
        """The O(nm) answer. Small inputs only — the KD-tree's control."""
        if len(w2) == 0:
            return np.full(len(g2), np.inf)
        return np.sqrt(((g2[:, None, :] - w2[None, :, :]) ** 2).sum(-1)).min(1)


# ------------------------------------------------------------------ per-frame E
TILE = 40      # px. 96 x 54 tiles on a 3840 x 2160 frame.


def frame_stats(W, e, band=BAND_M, gap=GAP_M, res=(RES_X, RES_Y), tile=TILE):
    """DEFECT EXPOSURE by screen TILE, with the nearest sample winning each tile.

    NOT by summing (ppm^2 * a_sample) over samples.  The dump is a vertex sample of
    the terrain mesh and the mesh is NOT uniformly tessellated — it is denser near
    the corridor, which is exactly the band being measured — so an area-weighted sum
    over samples multiplies the defect by the tessellation.  My first version did
    that and returned E = 46.2 for a quantity bounded by 1; the bound is what caught
    it.  A tile grid with the nearest sample winning is a depth buffer at 40 px, and
    it is bounded by construction.
    """
    tx, ty = res[0] // tile, res[1] // tile
    ntile = tx * ty
    u, v, depth, inside = project(W.ground, e["p"], e["q"], e["lens"], res)
    out = dict(f=int(e["f"]), lens=float(e["lens"]), n_inside=int(inside.sum()),
               ground_tiles=0, frame_frac=0.0, near_tiles=0, void_tiles=0,
               E=0.0, E_allband=0.0, near_frac_of_ground=0.0,
               void_frac_of_near=0.0, tile_px=tile, n_tiles=ntile)
    if not inside.any():
        return out
    k = inside
    ti = (v[k].astype(np.int64) // tile) * tx + (u[k].astype(np.int64) // tile)
    d = depth[k]
    # nearest sample per tile == what the camera would actually see there
    order = np.lexsort((d, ti))
    ti_s, idx_s = ti[order], np.flatnonzero(k)[order]
    first = np.concatenate(([True], ti_s[1:] != ti_s[:-1]))
    rep = idx_s[first]                                  # one sample per tile
    D, gp = W.D[rep], W.gap[rep]
    nt = len(rep)
    near = int((D <= band).sum())
    void = int(((D <= band) & (gp > gap)).sum())
    allv = int((gp > gap).sum())
    out.update(ground_tiles=nt, frame_frac=nt / ntile,
               near_tiles=near, void_tiles=void,
               E=void / ntile, E_allband=allv / ntile,
               near_frac_of_ground=near / nt,
               void_frac_of_near=(void / near) if near else 0.0)
    return out


# -------------------------------------------------------------- crop selection
def crop_boxes(W, e, band=BAND_M, gap=GAP_M, res=(RES_X, RES_Y), tile=TILE,
               n=3, size=(1280, 800)):
    """1:1 crop boxes over the near-band VOID, chosen by the measurement.

    `tools/ab_crops.py` fixes its crops per cluster so "it looks better now" is
    falsifiable.  Same rule here, one step earlier: the boxes are the densest
    windows of evacuated near-band tiles in the frame, so they are reproducible
    from the geometry and nobody has chosen them by eye.  Non-maximum suppression
    keeps the boxes from being three views of one patch.
    """
    tx, ty = res[0] // tile, res[1] // tile
    u, v, depth, inside = project(W.ground, e["p"], e["q"], e["lens"], res)
    if not inside.any():
        return []
    k = inside
    ti = (v[k].astype(np.int64) // tile) * tx + (u[k].astype(np.int64) // tile)
    order = np.lexsort((depth[k], ti))
    ti_s, idx_s = ti[order], np.flatnonzero(k)[order]
    first = np.concatenate(([True], ti_s[1:] != ti_s[:-1]))
    rep, tid = idx_s[first], ti_s[first]
    hot = tid[(W.D[rep] <= band) & (W.gap[rep] > gap)]
    if len(hot) == 0:
        return []
    M = np.zeros((ty, tx))
    M[hot // tx, hot % tx] = 1.0
    cw, ch = size[0] // tile, size[1] // tile
    # integral image -> density of every cw x ch window, in one pass
    I = np.pad(M, ((1, 0), (1, 0))).cumsum(0).cumsum(1)
    S = (I[ch:, cw:] - I[:-ch, cw:] - I[ch:, :-cw] + I[:-ch, :-cw])
    out = []
    for _ in range(n):
        if S.max() <= 0:
            break
        j, i = np.unravel_index(int(np.argmax(S)), S.shape)
        x, y = i * tile, j * tile
        out.append(dict(x=int(x), y=int(y), w=int(size[0]), h=int(size[1]),
                        void_tiles=int(S[j, i]),
                        void_frac=float(S[j, i]) / (cw * ch)))
        S[max(0, j - ch):j + ch, max(0, i - cw):i + cw] = 0.0   # suppress
    return out


# ---------------------------------------------------------------------- selftest
def selftest(W, band=BAND_M, gap=GAP_M):
    ok = True

    def chk(name, cond, msg=""):
        nonlocal ok
        print("  %-58s %s  %s" % (name, "ok  " if cond else "FAIL", msg))
        ok = ok and bool(cond)

    print(">> SELFTEST r2_1881_nearband_ref")
    bf = LC.load(byframe=True)
    e = bf[2760]

    # ---- PROJECTION -------------------------------------------------------
    fwd, right, up = cam_axes(e["q"])
    p = np.asarray(e["p"], float)
    ahead = (p + 100.0 * fwd)[None, :]
    u, v, d, ins = project(ahead, e["p"], e["q"], e["lens"])
    chk("P: a point on the forward axis lands on the principal point",
        abs(u[0] - RES_X / 2) < 1e-6 and abs(v[0] - RES_Y / 2) < 1e-6 and ins[0],
        "u=%.6f v=%.6f depth=%.3f" % (u[0], v[0], d[0]))
    chk("P: px-per-metre at 100 m on this lens",
        abs(ppm(100.0, e["lens"]) - (RES_X * e["lens"] / SENSOR_MM) / 100.0) < 1e-9,
        "%.4f px/m" % ppm(100.0, e["lens"]))

    behind = (p - 20.0 * fwd)[None, :]
    _, _, _, insb = project(behind, e["p"], e["q"], e["lens"])
    chk("N: a point 20 m BEHIND the lens is outside", not insb[0])
    side = (p + 100.0 * right - 1.0 * fwd)[None, :]
    _, _, _, inss = project(side, e["p"], e["q"], e["lens"])
    chk("N: a point beside and behind the lens is outside", not inss[0])

    # ---- PLANTED: samples ON woody origins must read 0 m and 0 void --------
    n = min(4000, len(W.woody))
    idx = np.random.default_rng(7).choice(len(W.woody), n, replace=False)
    planted = W.woody[idx][:, :2]
    dp = World._nearest_woody(planted, W.woody[:, :2])
    chk("PLANTED: ground planted AT a woody origin reads 0.000 m",
        float(dp.max()) < 1e-6, "max %.9f m over %d samples" % (dp.max(), n))
    chk("PLANTED: and therefore 0 %% of it is blank",
        float((dp > gap).mean()) == 0.0,
        "%.4f %% blank" % (100 * (dp > gap).mean()))

    # ---- BARE: a ring at D = 10 m is inside the evacuation by construction --
    s = np.linspace(0.0, float(W.C.LAP), 4000, endpoint=False)
    bx, by = [], []
    for sign in (+1.0, -1.0):
        P = np.asarray(W.C.su_to_world(s, np.full_like(s, sign * 10.0)), float)
        bx.append(P[:, 0]); by.append(P[:, 1])
    bare = np.column_stack([np.concatenate(bx), np.concatenate(by)])
    sb, ub = W.C.project(bare[:, 0], bare[:, 1])
    chk("BARE: the manufactured ring really is at D = 10 m",
        abs(float(np.abs(ub).mean()) - 10.0) < 0.5,
        "mean D %.4f m, max %.4f" % (np.abs(ub).mean(), np.abs(ub).max()))
    db = World._nearest_woody(bare, W.woody[:, :2])
    frac = float((db > gap).mean())
    chk("BARE: ground 10 m from the centreline reads BLANK",
        frac > 0.90, "%.2f %% of it has no woody instance within %.0f m"
                     % (100 * frac, gap))

    # ---- VACUITY: the metric must move when the population moves ----------
    dv = World._nearest_woody(W.ground[:2000, :2], np.zeros((0, 2)))
    chk("V: with NO woody instances at all, everything reads blank",
        bool(np.isinf(dv).all()), "100.00 %% blank")
    dv2 = World._nearest_woody(W.ground[:2000, :2], W.ground[:2000, :2])
    chk("V: with a woody instance ON every sample, nothing reads blank",
        float(dv2.max()) < 1e-6, "max %.9f m" % dv2.max())

    # ---- the KD-tree against brute force, on a sample ---------------------
    gs = W.ground[:1500, :2]
    ws = W.woody[np.random.default_rng(2).choice(len(W.woody), 6000,
                                                 replace=False)][:, :2]
    dk = World._nearest_woody(gs, ws)
    db2 = World._brute(gs, ws)
    chk("V: cKDTree agrees with brute force to 1e-9",
        float(np.abs(dk - db2).max()) < 1e-9,
        "max |diff| %.3e m over %d x %d" % (np.abs(dk - db2).max(), len(gs),
                                            len(ws)))

    # ---- END TO END on the real frame statistic ---------------------------
    # The two arms differ ONLY in the woody population, so anything E does here it
    # does because of the planting and not because of the projection or the tiling.
    st = frame_stats(W, e, band, gap)
    chk("f2760 returns a bounded, non-trivial E",
        0.0 < st["E"] < 1.0 and st["n_inside"] > 100,
        "E=%.4f over %d framed samples, %d ground tiles"
        % (st["E"], st["n_inside"], st["ground_tiles"]))

    keep = W.gap
    try:
        W.gap = np.full(len(W.ground), np.inf)          # NOTHING is planted
        bare_st = frame_stats(W, e, band, gap)
        chk("E2E: with the woody population EMPTIED, every near tile is void",
            abs(bare_st["E"] - bare_st["near_frac_of_ground"]
                * bare_st["frame_frac"]) < 1e-9
            and bare_st["void_frac_of_near"] == 1.0,
            "E %.4f -> %.4f, void/near %.1f %%"
            % (st["E"], bare_st["E"], 100 * bare_st["void_frac_of_near"]))
        W.gap = np.zeros(len(W.ground))                 # a tree ON every sample
        full_st = frame_stats(W, e, band, gap)
        chk("E2E: with a woody instance on EVERY sample, E is exactly 0",
            full_st["E"] == 0.0 and full_st["ground_tiles"] == st["ground_tiles"],
            "E %.4f -> %.4f on the same %d tiles"
            % (st["E"], full_st["E"], full_st["ground_tiles"]))
        chk("E2E: and the three arms share one framing (the camera did not move)",
            bare_st["ground_tiles"] == st["ground_tiles"] == full_st["ground_tiles"],
            "%d tiles in all three" % st["ground_tiles"])
    finally:
        W.gap = keep

    # ---- the statistic is bounded on every frame it will be scanned over ---
    bs = [frame_stats(W, bf[f], band, gap) for f in range(1, 2979, 97)]
    chk("E is bounded in [0,1] on a 31-frame sweep of the whole film",
        all(0.0 <= r["E"] <= 1.0 and 0.0 <= r["frame_frac"] <= 1.0 for r in bs),
        "max E %.4f, max ground coverage %.1f %%"
        % (max(r["E"] for r in bs), 100 * max(r["frame_frac"] for r in bs)))

    print("\n>> STAGE RESULT: %s"
          % ("R2_1881_NEARBAND_REF_OK" if ok else "R2_1881_NEARBAND_REF_FAIL"))
    return 0 if ok else 1


# -------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--points", default=POINTS)
    ap.add_argument("--nground", type=int, default=60000)
    ap.add_argument("--band", type=float, default=BAND_M)
    ap.add_argument("--gap", type=float, default=GAP_M)
    ap.add_argument("--frame", type=int, default=None)
    ap.add_argument("--scan", action="store_true")
    ap.add_argument("--crops", default=None,
                    help="comma-separated frames -> a regions json usable by "
                         "tools/r2_1821_ground_detail.py --regions and "
                         "tools/peep.py ab --box")
    ap.add_argument("--ncrop", type=int, default=3)
    ap.add_argument("--stride", type=int, default=1)
    ap.add_argument("--out", default=None)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    W = World(a.points, a.nground)
    print(">> world: %d ground samples (%.1f m2 each), %d woody instances "
          "(%d from veg_origin), band %.1f m, gap %.1f m"
          % (len(W.ground), W.a_sample, len(W.woody), W.n_woody_origin,
             a.band, a.gap))

    if a.selftest:
        sys.exit(selftest(W, a.band, a.gap))

    bf = LC.load(byframe=True)
    if a.frame:
        e = bf[a.frame]
        st = frame_stats(W, e, a.band, a.gap)
        print(json.dumps(st, indent=1))
        return

    if a.crops:
        reg, per = {}, {}
        for f in [int(x) for x in a.crops.split(",")]:
            bs = crop_boxes(W, bf[f], a.band, a.gap, n=a.ncrop)
            per[f] = bs
            for i, b in enumerate(bs):
                nm = "f%04d_nearband_%d" % (f, i)
                reg[nm] = [b["x"], b["y"], b["w"], b["h"]]
                print("  %-22s [%4d,%4d %dx%d]  %d void tiles, %.0f %% of the box"
                      % (nm, b["x"], b["y"], b["w"], b["h"],
                         b["void_tiles"], 100 * b["void_frac"]))
        if a.out:
            os.makedirs(os.path.dirname(a.out), exist_ok=True)
            json.dump(reg, open(a.out, "w"), indent=1)
            print("\nwrote %s  (%d regions)" % (a.out, len(reg)))
        return

    if a.scan:
        rows = [frame_stats(W, bf[f], a.band, a.gap)
                for f in sorted(bf)[::a.stride]]
        rows.sort(key=lambda r: -r["E"])
        print("%6s %8s %9s %9s %9s %9s"
              % ("frame", "lens", "E", "E_all", "ground%", "void/near"))
        for r in rows[:30]:
            print("%6d %8.2f %9.4f %9.4f %8.1f%% %8.1f%%"
                  % (r["f"], r["lens"], r["E"], r["E_allband"],
                     100 * r["frame_frac"], 100 * r["void_frac_of_near"]))
        if a.out:
            os.makedirs(os.path.dirname(a.out), exist_ok=True)
            json.dump({"band_m": a.band, "gap_m": a.gap,
                       "points": a.points, "nground": len(W.ground),
                       "a_sample_m2": W.a_sample,
                       "n_woody": len(W.woody),
                       "camera": LC.declared_campath(),
                       "rows": rows}, open(a.out, "w"), indent=1)
            print("\nwrote %s" % a.out)


if __name__ == "__main__":
    main()
