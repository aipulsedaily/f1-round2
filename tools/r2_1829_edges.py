"""R2-1829 / R2-1824: the two remaining hard edges in the ground layer, and the
invariants that must NOT move while they are removed.

    blender -b --factory-startup -noaudio -P tools/r2_1829_edges.py

Both fixes are crossfades and both are strictly multiplicative reductions, so the way
they fail is not "the edge is still there" -- it is "the edge is gone because the
ground on both sides of it is gone". Every assertion below is therefore paired: one
that the step shrank, one that nothing that used to carry cover stopped carrying it.

  R2-1829  the verge band's outer rim.  `dens *= smoothstep(1, 1-VERGE_TAIL_T, tdraw)`
  R2-1824  the sward layer's outermost radius.  the last tier gets the outward fade

WHAT MUST NOT MOVE, and why each one is here rather than a general "looks fine":

  1  THE VERGE ITSELF.  The inner band -- tdraw < 1 - VERGE_TAIL_T, which is the ground
     beats 1-5 fly along at knee height -- must keep its clump count to within the
     Monte Carlo of the draw. This is the assertion that the taper did not simply thin
     the whole verge.
  2  NO HOLE AT THE HANDOFF. Across the rim, total ground cover must never fall below
     what the ground BEYOND the rim already carries. "No blank spots" does not mean
     "no gradient"; it means the transition may not go below the level it is heading
     for. A taper that dipped and recovered would pass a step test and fail the brief.
  3  TIERS A AND B UNTOUCHED.  R2-1824 edits the LAST tier only. Tier A and tier B
     counts must be identical to the unit, not merely close -- they are computed from
     the same grids with the same seeds and nothing in their density chain changed.
  4  THE 200 m AND 520 m JOINS STILL SUM TO ONE.  The fix adds a fade to the tier that
     had none; it must not perturb the two that already worked.
  5  NOTHING ON THE CONCRETE.  R2-1821's negative control, re-run, because these two
     changes touch the same density chains.
"""
import os
import bpy, sys, json
import numpy as np

sys.path.insert(0, os.path.expanduser("~/f1-round2/world"))
sys.path.insert(0, os.path.expanduser("~/f1-round2"))
import build_terrain as T
import world_contract as C

FAIL = []


def check(name, cond, detail):
    print("  %-56s %s   %s" % (name, "OK  " if cond else "FAIL", detail))
    if not cond:
        FAIL.append(name)


def sward_density(h, x, y, tier, tail):
    """The tier's density chain, verbatim, with the outward fade under our control."""
    lo, hi = tier["d0"] - 24.0, tier["d1"] + 26.0
    band = (h["dcam3"] >= lo) & (h["dcam3"] < hi) & (h["f"] > 12.0)
    d = T.smoothstep(lo, tier["d0"] + 26.0, h["dcam3"])
    if tier is not T.SWARD_TIERS[-1]:
        d = d * T.smoothstep(hi, tier["d1"] - 24.0, h["dcam3"])
    elif tail is not None:
        d = d * T.smoothstep(hi, tier["d1"] - tail, h["dcam3"])
    d = d * T.smoothstep(12.0, 34.0, h["f"]) * (1.0 - h["paved"])
    d = d * (1.0 - 0.72 * h["wood"])
    d = d * (1.0 - 0.55 * T.smoothstep(0.18, 0.46, h["slope"]))
    d = d * np.clip(0.50 + 0.62 * (0.5 + 0.5 * T.fbm(x / 38.0, y / 38.0, 3, seed=811)), 0, 1)
    d = d * np.clip(0.62 + 0.50 * (0.5 + 0.5 * T.fbm(x / 9.0, y / 9.0, 2, seed=813)), 0, 1)
    return np.where(band, np.clip(d, 0, 1), 0.0)


def main():
    spec = json.load(open(T.SPEC_JSON)); beats = json.load(open(T.BEAT_JSON))
    cir = T.Circuit(spec); gr = T.Ground(cir); cam = T.CameraPath(cir, beats)
    X0, X1, Y0, Y1 = -1300.0, 1300.0, -1300.0, 1300.0
    gxs = np.arange(X0, X1, 10.0); gys = np.arange(Y0, Y1, 10.0)
    GX, GY = np.meshgrid(gxs, gys, indexing="ij")
    gz = T.GridZ(gxs, gys, gr.height(GX.ravel(), GY.ravel()).reshape(GX.shape))
    ras = T.Raster(gr, cam, X0, X1, Y0, Y1, 14.0, gz=gz)
    out = {}

    # =============================== R2-1829 ====================================
    print("R2-1829  the verge band's outer rim")
    per_m = max(6, int(900.0 * T.QUAL))
    bands = [T.verge_band(cir, np.random.default_rng(7), side, per_m,
                          swin=(3115.0, C.LAP)) for side in (+1, -1)]
    B = {k: np.concatenate([b[k] for b in bands]) for k in bands[0]}
    hg = T.habitat(gr, gz, cam, B["x"], B["y"], ras)
    rng = np.random.default_rng(11)
    patch = 0.5 + 0.5 * T.fbm(B["x"] / 11.0, B["y"] / 11.0, 3, seed=77)
    base = np.clip(0.35 + 0.65 * patch, 0, 1) * (1.0 - 0.55 * B["scuff"])
    base *= 1.0 - (0.15 + 0.40 * B["scuff"]) * T.smoothstep(2.2, 0.0, B["lat"])
    gate = (hg["wood"] < 0.62) & ((hg["paved"] < 0.35) | B["inside"])
    roll = rng.random(len(B["x"]))
    taper = T.smoothstep(1.0, 1.0 - T.VERGE_TAIL_T, B["tdraw"])
    old = (roll < base) & gate
    new = (roll < base * taper) & gate

    inner = B["tdraw"] < (1.0 - T.VERGE_TAIL_T)
    out["verge_inner_old"] = int((inner & old).sum())
    out["verge_inner_new"] = int((inner & new).sum())
    check("1  THE VERGE ITSELF is untouched (tdraw < %.2f)" % (1 - T.VERGE_TAIL_T),
          (inner & old).sum() == (inner & new).sum(),
          "%d -> %d clumps  (must be identical: the taper is 1.0 there)"
          % ((inner & old).sum(), (inner & new).sum()))

    # --- 1c  NOTHING INSIDE THE CORRIDOR MAY BE TAPERED, over the WHOLE LAP --------
    # The first version of this whole tool only ever looked at the pit straight, where
    # the fold cap never binds -- so it could not see that the taper was fading ground
    # 14 m INBOARD of the rim at T4, where no sward exists to receive the handoff.
    # A one-straight sample cannot answer a question about a lap with hairpins in it,
    # and the symptom was a 1.1 % move in a count that should have been identical.
    lapb = [T.verge_band(cir, np.random.default_rng(7), side, per_m) for side in (+1, -1)]
    L = {k: np.concatenate([b[k] for b in lapb]) for k in lapb[0]}
    ltap = T.smoothstep(1.0, 1.0 - T.VERGE_TAIL_T, L["tdraw"])
    bad_in = L["inside"] & (ltap < 0.999)
    out["lap_incorridor_tapered"] = int(bad_in.sum())
    check("1c NOTHING inside the road corridor is tapered, WHOLE LAP",
          bad_in.sum() == 0,
          "%d of %d in-corridor samples touched by the taper (f median %.1f m)"
          % (bad_in.sum(), int(L["inside"].sum()),
             float(np.median(L["f"][bad_in])) if bad_in.any() else 0.0))

    outer = ~inner
    check("1b the taper actually acts on the rim",
          (outer & new).sum() < 0.75 * max(1, (outer & old).sum()),
          "outer band %d -> %d clumps  (%.0f %% of before)"
          % ((outer & old).sum(), (outer & new).sum(),
             100.0 * (outer & new).sum() / max(1, (outer & old).sum())))

    # --- 2. NO HOLE AT THE HANDOFF ------------------------------------------------
    #
    # THE FIRST VERSION OF THIS ASSERTION WAS MEASURED ON THE BAND'S OWN SAMPLES AND
    # WAS MEANINGLESS. The band stops at its rim by construction, so there are no band
    # samples beyond f = 42 at all: the "far field" it compared against was an empty
    # slice that averaged to 0.0, and the "step" it computed was between two bins BOTH
    # INSIDE the taper. It reported FAIL on a working fix, for the second time in this
    # workstream -- the same mistake as R2-1826's ratio threshold, in a new costume.
    # An instrument that cannot see the far side of an edge cannot measure that edge.
    #
    # So the profile is taken on a GROUND GRID that exists on both sides of the rim,
    # and the verge is counted per SQUARE METRE OF GROUND rather than per band sample.
    # Those are not the same number: the draw is 62 % biased by t**1.8, so an
    # acceptance FRACTION is flat at ~0.37 across the whole band while the areal
    # density it produces varies ~4x. The fraction is what the old profile printed.
    edges = np.arange(0.0, 70.0, 4.0)
    fmid = 0.5 * (edges[:-1] + edges[1:])
    # verge clumps per unit ground area: along a straight, every f-bin of equal width
    # covers equal ground, so raw counts ARE areal density up to one constant.
    outside = ~B["inside"]
    cnt_o = np.array([((B["f"] >= a) & (B["f"] < b) & outside & old).sum()
                      for a, b in zip(edges[:-1], edges[1:])], float)
    cnt_n = np.array([((B["f"] >= a) & (B["f"] < b) & outside & new).sum()
                      for a, b in zip(edges[:-1], edges[1:])], float)
    # sward, on its own grid, binned by the same f
    gx, gy, _ = T.jitter_grid(-700.0, 700.0, -700.0, 700.0, 4.0, 4242)
    hgd = T.habitat(gr, gz, cam, gx, gy, ras)
    swg = sum(sward_density(hgd, gx, gy, t, T.SWARD_TAIL_M) for t in T.SWARD_TIERS)
    ok_g = hgd["paved"] < 0.02
    prof_s = np.array([swg[(hgd["f"] >= a) & (hgd["f"] < b) & ok_g].mean()
                       if ((hgd["f"] >= a) & (hgd["f"] < b) & ok_g).sum() > 40 else np.nan
                       for a, b in zip(edges[:-1], edges[1:])])
    scale = np.nanmax(cnt_o) if np.nanmax(cnt_o) > 0 else 1.0
    vo, vn = cnt_o / scale, cnt_n / scale
    tot_o, tot_n = vo + prof_s, vn + prof_s
    print("     f (m)       " + " ".join("%5.0f" % v for v in fmid))
    print("     verge old   " + " ".join("%5.2f" % v for v in vo))
    print("     verge new   " + " ".join("%5.2f" % v for v in vn))
    print("     sward       " + " ".join("%5.2f" % v for v in prof_s))
    print("     TOTAL old   " + " ".join("%5.2f" % v for v in tot_o))
    print("     TOTAL new   " + " ".join("%5.2f" % v for v in tot_n))

    beyond = np.isfinite(prof_s) & (fmid > 46.0)
    floor = float(np.nanmean(tot_n[beyond]))
    inband = np.isfinite(tot_n) & (fmid > 20.0) & (fmid < 46.0)
    out["far_field_level"] = round(floor, 3)
    check("2  NO HOLE: cover across the handoff stays at or above the far field",
          bool((tot_n[inband] >= floor * 0.98).all()),
          "min across f 20-46 m = %.3f, the ground BEYOND the rim carries %.3f"
          % (np.nanmin(tot_n[inband]), floor))

    def step(p):
        """the jump across the rim, from the last bin inside to the first outside"""
        i = int(np.argmin(np.abs(fmid - 42.0)))
        lo_, hi_ = p[i], p[min(len(p) - 1, i + 2)]
        return 100.0 * (hi_ / lo_ - 1.0) if lo_ > 1e-6 else 0.0
    s_old, s_new = step(tot_o), step(tot_n)
    out["rim_step_pct_old"] = round(s_old, 1); out["rim_step_pct_new"] = round(s_new, 1)
    check("2b the step ACROSS the rim is smaller", abs(s_new) < 0.5 * abs(s_old),
          "%.1f %% -> %.1f %% across f = 42 m" % (s_old, s_new))

    # =============================== R2-1824 ====================================
    print("R2-1824  the sward layer's outermost radius")
    counts = {}
    for tail in (None, T.SWARD_TAIL_M):
        tot = {}
        for Tr in T.SWARD_TIERS:
            sx, sy, sr = T.jitter_grid(X0, X1, Y0, Y1, Tr["pitch"], 8100 + ord(Tr["tag"]))
            r0 = ras.sample(sx, sy)
            keepb = (r0["dcam3"] >= Tr["d0"] - 24.0) & (r0["dcam3"] < Tr["d1"] + 26.0) \
                & (r0["f"] > 12.0)
            sx, sy, sr = sx[keepb], sy[keepb], sr[keepb]
            if not len(sx):
                tot[Tr["tag"]] = 0; continue
            h = T.habitat(gr, gz, cam, sx, sy, ras)
            d = sward_density(h, sx, sy, Tr, tail)
            tk = np.where(sr < d * T.SWARD_Q * (0.55 + 0.45 * T.QUAL))[0]
            tk = tk[T.outside_corridor(sx[tk], sy[tk], 2.0)]
            tot[Tr["tag"]] = len(tk)
            if tail is not None:
                tot["_on_concrete_" + Tr["tag"]] = int(
                    C.apron_platform_mask(sx[tk], sy[tk]).sum())
        counts["cut" if tail is None else "faded"] = tot
    out["sward_counts"] = counts
    a, b = counts["cut"], counts["faded"]
    check("3  TIER A and TIER B are identical to the unit",
          a["A"] == b["A"] and a["B"] == b["B"],
          "A %d -> %d,  B %d -> %d" % (a["A"], b["A"], a["B"], b["B"]))
    check("3b tier C loses drifts to the fade and gains none",
          b["C"] < a["C"],
          "C %d -> %d  (%.1f %%, and the fade can only multiply DOWN)"
          % (a["C"], b["C"], 100.0 * b["C"] / max(1, a["C"])))

    # --- 4. the joins that already worked must still sum to one -------------------
    rng2 = np.random.default_rng(5)
    px = rng2.uniform(X0, X1, 400000); py = rng2.uniform(Y0, Y1, 400000)
    hp = T.habitat(gr, gz, cam, px, py, ras)
    dens_tot = sum(sward_density(hp, px, py, t, T.SWARD_TAIL_M) for t in T.SWARD_TIERS)
    keepo = (hp["f"] > 40.0) & (hp["paved"] < 0.02) & (hp["wood"] < 0.1)
    joins = {}
    for c, nm in ((200.0, "A->B 200 m"), (520.0, "B->C 520 m")):
        lo_ = keepo & (hp["dcam3"] > c - 40) & (hp["dcam3"] < c - 10)
        hi_ = keepo & (hp["dcam3"] > c + 10) & (hp["dcam3"] < c + 40)
        v = 100.0 * (dens_tot[hi_].mean() / dens_tot[lo_].mean() - 1.0)
        joins[nm] = round(float(v), 1)
    check("4  the 200 m and 520 m joins still sum to one",
          all(abs(v) < 15.0 for v in joins.values()),
          " ".join("%s %+.1f %%" % (k, v) for k, v in joins.items()))

    # the new outer fade, as a profile
    print("     the outer radius, mean sward cover on open ground:")
    for a_, b_ in ((700, 800), (800, 860), (860, 920), (920, 980), (980, 1030),
                   (1030, 1076), (1076, 1150), (1150, 1300)):
        m = keepo & (hp["dcam3"] >= a_) & (hp["dcam3"] < b_)
        if m.sum() > 30:
            print("       %4d-%4d m   %5.3f   (n=%d)" % (a_, b_, dens_tot[m].mean(), m.sum()))

    check("5  NOTHING on architecture's declared paving",
          sum(v for k, v in b.items() if k.startswith("_on_concrete")) == 0,
          "sward on paving: " + ", ".join("%s %d" % (k[-1], v)
                                          for k, v in b.items()
                                          if k.startswith("_on_concrete")))

    print(json.dumps(out, indent=1, default=str))
    print(">> STAGE RESULT: %s" % ("R2_1829_EDGES_OK (0 failures)" if not FAIL
                                   else "R2_1829_EDGES_FAIL " + " | ".join(FAIL)))


main()
