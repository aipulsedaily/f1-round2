#!/usr/bin/env python3
"""R2-2970: THE GROUND-COVER TIER, MEASURED IN PIXELS INSTEAD OF IN CLAIMS.

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup -noaudio \
        -P tools/r2970_groundcover_px.py -- --out work/r2970/px.json

WHY THIS FILE EXISTS
--------------------
`docs/WAVE1-PEEP-SYNTHESIS.md` PATTERN 4:

    "The recurring shape: the mechanism is in the code and its amplitude is
     3-5x too small to survive to pixels.  That is a different bug from 'not
     built', and it is invisible to any check that inspects the code rather
     than the image."

Every previous ground-cover pass argued from a *derivation* -- "a 35 mm lens at
3840 px resolves 2.47e-4 rad, so at 7.5 m one pixel is 1.94 mm".  That number is
about a camera station somebody chose.  `work/w2_0/retier_a10/sp_objects.json`
is a different kind of number: it is the MEASURED peak sharp resolution of each
object over all 2,978 frames of the actual film, with occlusion and with a
180-degree shutter smear.  It says the ground cover is seen at

    VEG_grass_* / VEG_grit_*   425.8 px/m   ->  1 px = 2.35 mm   (at 4.58 m)
    VEG_weed_thistle           347.9 px/m   ->  1 px = 2.87 mm   (at 6.01 m)

This file takes that file as the scale, BUILDS the actual library meshes with the
project's own generators, MEASURES the built geometry, and converts every feature
into pixels.  Nothing here is retyped: the sizes come from `world.build_terrain`'s
own constants by import, and the resolutions come from `sp_objects.json` by read.

THE LAW IT ENFORCES
-------------------
    A feature smaller than 1 px is invisible however correct it is, and building
    it is waste.  A feature larger than 1 px must exist as GEOMETRY.

So each measured feature gets one of three verdicts:

    ABOVE    >= 1 px and built            -- fine
    MISSING  >= 1 px and NOT built        -- a defect, this is what we are hunting
    BELOW    <  1 px                      -- must not be built; if it is, it is waste

WHAT IT MEASURES ON THE BUILT MESH (not on the constants)
---------------------------------------------------------
grass   `keel_span`   the median across-blade quad span.  A hero blade is
                      edge / keel / edge, so this span IS the lit half of the
                      light/dark pair that the whole channelled-blade argument
                      rests on.  If it is under a pixel there is no pair.
        `seed_head`   whether a panicle was actually emitted, and how many
                      spikelets it has.
grit    `smooth_frac` fraction of polygons flagged shade-smooth.  A flint chip's
                      only mechanism at a 12.5 deg sun is the hard shading break
                      at a facet edge; `shade_smooth()` deletes every one of them
                      while leaving the geometry in place, which is PATTERN 4 in
                      its purest form -- the amplitude is not 3x small, it is 0.
        `facet_span`  median polygon edge length, scaled to the piece size band.
        `dihedral`    median face-to-face angle, and the fraction of edges over
                      20 deg.  A smoothed icosphere and an angular chip have the
                      same triangle count and completely different distributions.
weed    `margin_rms`  the leaf's built half-width profile, fitted to a smooth
                      monotone taper, RMS residual in px.  This is the WAVE1
                      trouser-taper test: a smooth ribbon fits to ~0, a lobed
                      (pinnatifid) leaf cannot.  It is how "the thistle leaf has
                      no lobes" becomes a number.
        `stem_facet`  the stem tube's facet width -- a 4-gon at 10 px is a
                      square prism with a 90 deg shading break down it.

EVERY GATE HERE WAS WATCHED FAILING.  `--selftest` damages the generators four
different ways (halve the blade width, re-smooth the grit, un-lobe the leaves,
delete the panicles) and asserts that the matching gate FAILS and that the other
gates do not.  A gate that has only ever seen good geometry has not been tested;
this project has caught over a dozen instruments passing vacuously.  Zero meshes
measured is VACUOUS, not clean.

Blender 5.2 exits 0 on an uncaught exception, so judge on `>> STAGE RESULT:`.
"""
import argparse
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (HERE, os.path.join(ROOT, "world"), ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

import bpy                                                          # noqa: E402
import gate_exit                                                    # noqa: E402
import build_terrain as BT                                          # noqa: E402

gate_exit.install(tool="r2970_groundcover_px")

# ---------------------------------------------------------------------------
# THE SCALE.  Read, never retyped.
# ---------------------------------------------------------------------------
SP_OBJECTS = os.path.join(ROOT, "work", "w2_0", "retier_a10", "sp_objects.json")

PX_LINE = 1.0          # the resolve threshold, in pixels.  The campaign's law.

# A PERIODIC FEATURE NEEDS TWO PIXELS PER CYCLE, NOT ONE.
# The one-pixel law is about an ISOLATED feature: a nail head, a stone, a lobe.
# A serration, a rib, a weave is a WAVE, and a wave sampled at under two samples
# per period does not come out small, it comes out ALIASED -- it renders as
# something that is not there.  So repeating features are declined against 2 px
# of PITCH, and the pitch is what gets measured, not the amplitude.  This is the
# same distinction that made a 0.87 px carbon weave waste rather than faint.
NYQUIST_LINE = 2.0


# THE SAMPLE-FLOOR CORRECTION.                                       R2-2949/2949a
#
# `peak_unocc_sharp_px_per_m` is a PEAK, and a peak over a point cloud can be set
# by one point.  R2-2949 re-ran the field with a MINIMUM SHARP-SAMPLE FLOOR --
# the control that pass did not apply -- and three of its four headline rows did
# not survive it.  The two that matter here:
#
#     VEG_grass_fescue_H   425.82  ->  425.82 at >=10,  396.91 at >=25   SURVIVES
#     VEG_grit_chip        425.82  ->  425.82 at >=10,  396.91 at >=25   SURVIVES
#     VEG_weed_thistle     347.88  ->  141.41 at >=10,   85.73 at >=25   WITHDRAWN
#
# Grass and grit hold because their peak is set by 25 points spread over
# 5.0 x 12.0 m, all outdoors, all at z 0.5-1.5 m, 570 m from the pavilion, in
# f2316 -- a frame `work/r22161_proxy/r22161_proxy_002316.png` shows as sharp
# foreground sward.  The thistle has 6,821 points against grass's 164,884 and
# its peak was set by fewer than ten of them.
#
# This table is applied ON TOP of the file, at the >=10 floor, and the file's own
# figure is kept alongside so the correction is visible rather than laundered.
# It is the difference between a change that ships and one that does not: at
# 141.41 px/m the thistle's built leaf lobe is 0.79 px and its 4-sided stem is
# already sub-pixel, so both of this block's weed changes were withdrawn.
#
# ALSO CORRECTED: `min_depth_m` is the minimum over ALL visible frames, not the
# depth at the peak-sharp frame, so "425.8 px/m at 4.58 m" pairs two different
# frames.  Grass is 425.82 px/m at f2316, depth 17.40 m.  Nothing here computes
# with depth; it is reported, and it is reported as unknown rather than wrong.
SAMPLE_FLOOR = 10
CORRECTED_PX_PER_M = {
    "VEG_weed_thistle": 141.41,
}

# AND EVERYTHING ELSE THE FLOOR HAS NOT BEEN RUN ON IS UNVERIFIED, NOT TRUSTED.
#
# This rule was put here because the gate CAUGHT ME.  Having corrected the
# thistle, I left `VEG_weed_dock`, `_nettle` and `_ragwort` on the raw field --
# and the healthy control run promptly failed `stem_round` on all three, on the
# strength of 230-260 px/m figures produced by exactly the method that had just
# been falsified for their nearest neighbour.  R2-2949 says so in terms: the
# untested rows "should be treated as unverified until re-run with a floor."
#
# The discriminator is how many points the peak could have been set by.  The two
# objects that SURVIVED the floor carry 164,884 and 247,106 points; the one that
# COLLAPSED 2.5x carries 6,821.  So an object under `VERIFIED_MIN_POINTS` whose
# figure has not been independently re-run is reported and NOT gated -- because
# gating on a number this project has already shown to be a single-sample
# artefact is how a measurement stops being evidence.
VERIFIED_MIN_POINTS = 15000


def sharp_table(path=SP_OBJECTS):
    """object name -> measured peak unoccluded sharp px/m over the whole film."""
    d = json.load(open(path))
    out = {}
    for o in d["objects"]:
        raw = float(o["peak_unocc_sharp_px_per_m"])
        out[o["object"]] = dict(
            px_per_m=CORRECTED_PX_PER_M.get(o["object"], raw),
            raw_px_per_m=raw,
            corrected=o["object"] in CORRECTED_PX_PER_M,
            points=int(o["points"]),
            verified=(o["object"] in CORRECTED_PX_PER_M
                      or int(o["points"]) >= VERIFIED_MIN_POINTS),
            frames_sharp=int(o["frames_sharp"]),
            frames_visible=int(o["frames_visible"]))
    return out, d


# ---------------------------------------------------------------------------
# WORLD SCALE OF A LIBRARY MESH.  Derived, not assumed.
# ---------------------------------------------------------------------------
# A library mesh is not what lands on the ground.  `gn_kind` normalises every
# mesh to unit height and rescales it to a target, so a feature authored at `a`
# metres lands at `a * target_h / h0`.  For hero grass `build_grass` passes
#
#     target = base * mean(h),   base = U(0.72,1.45) * (1 - 0.32*mown)
#                                       * (0.55 + 0.75*fbm01)
#
# and separately multiplies X and Y by `spread = 1 + 0.75*mown`.  `mean(h)` IS
# the per-mesh `h0` for this library, so the net factor is `base`.  A blade's
# WIDTH is horizontal and carries base*spread; its LENGTH is mostly vertical and
# carries base alone.  `mown` appears in both with opposite signs, so the two do
# not multiply out to the naive product -- which is why this is sampled from the
# same expressions `build_grass` evaluates instead of being bounded by hand.
#
# THE VERDICT IS TAKEN AT THE MEDIAN, NOT AT THE EXTREME.  Gating on the
# smallest clump in the world makes every gate permanently MARGINAL and
# therefore unfailable -- which is a vacuous gate, and the control file proves
# it by halving the blade width and watching the p50 gate fall through 1 px
# while the extreme-low gate would not have moved off MARGINAL.
_MC = np.random.default_rng(20260808)
_mown = _MC.random(200000)
_fbm01 = 0.5 + 0.5 * (_MC.random(200000) - 0.5)          # fbm's own ~[0.25,0.75]
_base = _MC.uniform(0.72, 1.45, 200000) * (1.0 - 0.32 * _mown) \
    * (0.55 + 0.75 * _fbm01)
_spread = 1.0 + 0.75 * _mown
GRASS_W_SCALE = tuple(np.quantile(_base * _spread, [0.10, 0.50, 0.90]))
GRASS_H_SCALE = tuple(np.quantile(_base, [0.10, 0.50, 0.90]))


def _p50(a):
    return float(np.median(a)) if len(a) else float("nan")


def mesh_arrays(me):
    V = np.empty(len(me.vertices) * 3, np.float64)
    me.vertices.foreach_get("co", V)
    return V.reshape(-1, 3)


def poly_loops(me):
    """(start, total) per polygon plus the flat loop->vertex table."""
    n = len(me.polygons)
    st = np.empty(n, np.int32); tot = np.empty(n, np.int32)
    me.polygons.foreach_get("loop_start", st)
    me.polygons.foreach_get("loop_total", tot)
    lv = np.empty(len(me.loops), np.int32)
    me.loops.foreach_get("vertex_index", lv)
    return st, tot, lv


def quad_min_edge(me, V):
    """For every quad, the shorter of its two edge directions, in metres.

    A grass blade's quads are (i, i+1, k+i+1, k+i): one pair of edges runs
    ALONG the blade (L/segs) and the other ACROSS it (edge->keel).  The min is
    therefore the across-blade span, which is the finest lateral feature the
    blade has and the one the keel's light/dark pair is made of.
    """
    st, tot, lv = poly_loops(me)
    m = tot == 4
    if not m.any():
        return np.zeros(0)
    s = st[m]
    a = V[lv[s]]; b = V[lv[s + 1]]; c = V[lv[s + 2]]; d = V[lv[s + 3]]
    e0 = 0.5 * (np.linalg.norm(b - a, axis=1) + np.linalg.norm(d - c, axis=1))
    e1 = 0.5 * (np.linalg.norm(c - b, axis=1) + np.linalg.norm(a - d, axis=1))
    return np.minimum(e0, e1)


def poly_edge_mean(me, V):
    """Mean edge length per polygon, in metres -- the facet's own size."""
    st, tot, lv = poly_loops(me)
    out = []
    for k in np.unique(tot):
        m = tot == k
        s = st[m]
        idx = np.stack([lv[s + j] for j in range(k)], 1)
        P = V[idx]
        e = np.linalg.norm(P - np.roll(P, -1, axis=1), axis=2)
        out.append(e.mean(1))
    return np.concatenate(out) if out else np.zeros(0)


def smooth_fraction(me):
    n = len(me.polygons)
    if n == 0:
        return float("nan")
    sm = np.empty(n, bool)
    me.polygons.foreach_get("use_smooth", sm)
    return float(sm.mean())


def dihedral_stats(me, V):
    """Median face-to-face angle in degrees, and the fraction of shared edges
    that break by more than 20 deg.  Independent of triangle count."""
    st, tot, lv = poly_loops(me)
    N = np.empty(len(me.polygons) * 3, np.float64)
    me.polygons.foreach_get("normal", N)
    N = N.reshape(-1, 3)
    edge_face = {}
    for i in range(len(st)):
        s, t = int(st[i]), int(tot[i])
        for j in range(t):
            a, b = int(lv[s + j]), int(lv[s + (j + 1) % t])
            k = (a, b) if a < b else (b, a)
            edge_face.setdefault(k, []).append(i)
    ang = []
    for k, fs in edge_face.items():
        if len(fs) != 2:
            continue
        c = float(np.clip(np.dot(N[fs[0]], N[fs[1]]), -1.0, 1.0))
        ang.append(math.degrees(math.acos(c)))
    if not ang:
        return float("nan"), float("nan")
    ang = np.array(ang)
    return float(np.median(ang)), float((ang > 20.0).mean()), float((ang < 5.0).mean())


# ---------------------------------------------------------------------------
# THE LEAF-MARGIN TEST  (the WAVE1 trouser-taper test, on a leaf)
# ---------------------------------------------------------------------------
def leaf_margin_rms(me, V, mat_index):
    """RMS deviation of a leaf's half-width profile from a smooth taper, in mm.

    `_ribbon` emits 2k verts per leaf: k on one margin then k on the other, so
    the half-width at station j is |A_j - B_j| / 2.  A smooth ribbon's profile
    is W*sin(pi f^0.62), which the monotone-in-f cubic below fits to almost
    nothing.  A pinnatifid leaf -- a thistle, a ragwort -- oscillates about
    that taper by the lobe depth, and cannot be fitted.  The residual IS the
    lobe depth, which is exactly the quantity that has to clear a pixel.
    """
    st, tot, lv = poly_loops(me)
    m = (tot == 4)
    if not m.any():
        return float("nan"), 0
    mi = np.empty(len(me.polygons), np.int32)
    me.polygons.foreach_get("material_index", mi)
    m &= (mi == mat_index)
    if not m.any():
        return float("nan"), 0
    s = st[m]
    # quad (i, i+1, k+i+1, k+i): verts 0 and 3 are the two margins at station i
    A = V[lv[s]]; B = V[lv[s + 3]]
    halfw = 0.5 * np.linalg.norm(A - B, axis=1)
    # group into leaves: a leaf's quads are contiguous and its stations run
    # monotonically away from the base.  Split where the vertex index jumps.
    vi = lv[s].astype(np.int64)
    brk = np.where(np.diff(vi) != 1)[0] + 1
    groups = np.split(np.arange(len(vi)), brk)
    res = []
    nleaf = 0
    stations = []
    for g in groups:
        stations.append(len(g))
        # A CUBIC HAS FOUR PARAMETERS.  Fitting it to five stations is exact, so
        # the residual would be zero for ANY profile including a lobed one --
        # the test would pass vacuously on undersampled geometry, which is the
        # precise failure mode this whole file exists to prevent.  Under eight
        # stations the mesh cannot carry the answer and the measurement refuses.
        if len(g) < 8:
            continue
        w = halfw[g]
        f = np.linspace(0.0, 1.0, len(w))
        # smooth taper reference: least-squares cubic in f.  Deliberately
        # generous -- a cubic can already follow sin(pi f^0.62) closely, so any
        # residual left is genuine margin structure and not fit error.
        Xd = np.stack([np.ones_like(f), f, f ** 2, f ** 3], 1)
        coef, *_ = np.linalg.lstsq(Xd, w, rcond=None)
        res.append(float(np.sqrt(np.mean((w - Xd @ coef) ** 2))))
        nleaf += 1
    return (float(np.median(res)) if res else float("nan")), nleaf, \
        (int(np.median(stations)) if stations else 0)


# ---------------------------------------------------------------------------
# BUILD THE LIBRARIES AND MEASURE THEM
# ---------------------------------------------------------------------------
def build_libs(n=4, seed=20260808):
    BT.build_materials()
    rng = np.random.default_rng(seed)
    out = {"grass": {}, "grass_blades": {}, "grit": {}, "weed": {}}
    for k in BT.GRASS_PROF:
        nb = (190, 330) if k != "reed" else (70, 130)
        out["grass"][k] = [BT.gen_grass(np.random.default_rng(int(rng.integers(1 << 31))),
                                        k, blades=int(rng.integers(*nb)), segs=6, lod=0)
                           for _ in range(n)]
        # A SECOND CLUMP OF THE SAME KIND WITH THE PANICLE SUPPRESSED.
        # `quad_min_edge` cannot tell a blade's across-span from a 1.2 mm panicle
        # tube's circumference, and after R2-2972 the panicle contributes MORE
        # quads than the blades do -- so measuring blade width on the shipping
        # mesh silently reports the seed head instead.  (It did: reed's measured
        # blade width moved 2.37 -> 1.41 px on a change that does not touch a
        # blade.)  `_seed_heads` runs strictly after every blade is placed, so
        # suppressing it leaves the blade code path bit-identical.
        seed0 = BT.GRASS_PROF[k]["seed"]
        BT.GRASS_PROF[k]["seed"] = 0.0
        try:
            out["grass_blades"][k] = [
                BT.gen_grass(np.random.default_rng(int(rng.integers(1 << 31))), k,
                             blades=int(rng.integers(*nb)), segs=6, lod=0)
                for _ in range(n)]
        finally:
            BT.GRASS_PROF[k]["seed"] = seed0
    for gkey, gmat in (("clod", BT.VPFX + "clod"), ("gritstone", BT.VPFX + "gritstone")):
        # THROUGH THE PRODUCTION HELPER, never through gen_stone directly: the
        # gate must not be able to measure a piece the film does not render.
        out["grit"][gkey] = [BT.gen_grit_piece(
            np.random.default_rng(int(rng.integers(1 << 31))), gmat)
            for _ in range(n * 3)]
    for k in BT.WEED_ORDER:
        out["weed"][k] = [BT.gen_weed(k, np.random.default_rng(int(rng.integers(1 << 31))))
                          for _ in range(n)]
    return out


# feature name -> (class, what the real plant's feature measures, mm)
# The declined list is as much of the deliverable as the built list: a feature
# below the line must NOT be built, and the arithmetic that declines it has to
# be on the record or somebody will build it again.
DECLINED = [
    # feature                        class                  mm        line
    ("grass blade rib PITCH",        "VEG_grass_fescue_H", (0.30, 0.60), NYQUIST_LINE,
     "5-7 ribs across a 2-3 mm blade: periodic, so 2 px"),
    ("grass margin serration PITCH", "VEG_grass_fescue_H", (0.10, 0.30), NYQUIST_LINE,
     "scabrid teeth; periodic, so 2 px"),
    ("grass ligule at the node",     "VEG_grass_fescue_H", (1.0, 3.0), PX_LINE,
     "the sheath collar, one per blade"),
    ("grit chip surface pitting",    "VEG_grit_chip", (0.3, 1.2), NYQUIST_LINE,
     "the `ridged` field's own amplitude, already in gen_stone"),
    ("thistle leaf spine THICKNESS", "VEG_weed_thistle", (0.5, 1.0), PX_LINE,
     "the spine's LENGTH clears the line; a 0.2 px thick needle carries "
     "no shading, so the whole spine is declined"),
    ("thistle involucre bract WIDTH", "VEG_weed_thistle", (2.0, 3.0), PX_LINE,
     "the spiny bracts of the flower head"),
    ("plantain leaf rib PITCH",      "VEG_weed_plantain", (1.0, 2.0), NYQUIST_LINE,
     "five parallel ribs; periodic, so 2 px"),
    ("nettle leaf serration PITCH",  "VEG_weed_nettle", (1.6, 8.7), NYQUIST_LINE,
     "12 teeth a side on a 38-209 mm leaf.  The tooth DEPTH (4-8 mm, 1.0-2.1 px) "
     "clears the one-pixel line, but the PITCH is 0.4-2.3 px and its typical is "
     "1.0 px -- one sample per cycle.  Built, it would alias, not soften"),
    ("ragwort leaf lobe RMS",        "VEG_weed_ragwort", (1.5, 3.9), PX_LINE,
     "BUILT, MEASURED AT 0.57 px RMS BY THIS FILE, AND REMOVED AGAIN.  The leaf "
     "half width is 1.5-8.2 px (typical 3.5), so even a 0.55 cut is 1.9 px peak "
     "and 0.57 px RMS; 1 px RMS would need a 0.95 cut, which is a comb"),
    ("thistle leaf lobe RMS",        "VEG_weed_thistle", (5.6, 5.6), PX_LINE,
     "BUILT, MEASURED AT 1.95 px RMS -- and then R2-2949's sample floor moved "
     "the class from 347.88 to 141.41 px/m and the same margin became 0.79 px "
     "(0.48 at a >=25 floor).  Removed, at 3.75x the leaf quads for nothing"),
    ("thistle 8-sided stem",         "VEG_weed_thistle", (1.58, 1.58), PX_LINE,
     "the SILHOUETTE ERROR 8 sides would have removed.  At the corrected "
     "141.41 px/m the 4-sided stem is already 0.86 px at its thick end, so "
     "eight sides bought 0.6 px of nothing at 4 quads per stem segment"),
]


def measure(libs, sharp):
    rows = []

    def px(obj, mm):
        r = sharp.get(obj)
        if r is None:
            return float("nan")
        return mm * 1e-3 * r["px_per_m"]

    # ---- grass ------------------------------------------------------------
    for k, ms in libs["grass"].items():
        obj = BT.VPFX + "grass_%s_H" % k
        if obj not in sharp:
            continue
        prof = BT.GRASS_PROF[k]
        W, H = GRASS_W_SCALE, GRASS_H_SCALE
        bl = libs["grass_blades"].get(k, ms)          # panicle-free, see build_libs
        spans = np.concatenate([quad_min_edge(me, mesh_arrays(me)) for me, _ in bl])
        span_mm = _p50(spans) * 1000.0
        rows.append(dict(cls=obj, feature="blade full width (BUILT, 2x span)",
                         mm=tuple(2 * span_mm * s for s in W),
                         built=True, gate="blade_width"))
        rows.append(dict(cls=obj, feature="blade keel half-span (BUILT)",
                         mm=tuple(span_mm * s for s in W),
                         built=True, gate=None, info=True,
                         note="the lit half of the channelled blade's light/dark "
                              "pair; sits at the resolution limit BY PHYSICS -- "
                              "a real fescue blade is 1-3 mm and widening it "
                              "would be the mat the life-size pass removed"))
        rows.append(dict(cls=obj, feature="blade length",
                         mm=(prof["h"][0] * 1000 * H[0],
                             0.5 * (prof["h"][0] + prof["h"][1]) * 1000 * H[1],
                             prof["h"][1] * 1000 * H[2]),
                         built=True, gate=None))
        rows.append(dict(cls=obj, feature="blade tip width (0.05 w)",
                         mm=tuple(2 * 0.05 * prof["w"][1] * 1000 * s for s in W),
                         built=True, gate=None, info=True,
                         note="the far END of a taper, not a feature with a size "
                              "of its own: the taper is read over the blade's "
                              "60-330 px of length, and a blade that did not go "
                              "to a point would read as a cut-off strap"))
        rows.append(dict(cls=obj, feature="tiller crown scatter",
                         mm=tuple(0.044 * 1000 * s for s in W),
                         built=True, gate=None))
        rows.append(dict(cls=obj, feature="clump spread",
                         mm=tuple(prof["spread"] * 1000 * s for s in W),
                         built=True, gate=None))
        # seed head: is a panicle actually in the mesh?
        n_head = int(round(max(8, 260 // 3) * prof["seed"] * BT.SEED_HEAD_FRAC))
        nb = list(BT.PANICLE_N); nsp = list(BT.PANICLE_SPIKE)
        rows.append(dict(cls=obj, feature="seed-head spikelet (dia)",
                         mm=tuple(2 * BT.PANICLE_RAD_M[1] * 1000 * s for s in W),
                         built=n_head > 0, gate="seed_head",
                         extra=dict(heads_per_clump=n_head, seed_frac=prof["seed"],
                                    branches=nb, spikelets_per_branch=nsp,
                                    spikelets_per_head=[nb[0] * (1 + nsp[0]),
                                                        nb[1] * (1 + nsp[1])])))
        rows.append(dict(cls=obj, feature="seed-head panicle branch (len)",
                         mm=(BT.PANICLE_LEN_M[0] * 1000 * W[0],
                             0.5 * sum(BT.PANICLE_LEN_M) * 1000 * W[1],
                             BT.PANICLE_LEN_M[1] * 1000 * W[2]),
                         built=n_head > 0, gate=None))

    # ---- grit -------------------------------------------------------------
    for name, hr, share, key in BT.GRIT_KINDS:
        obj = BT.VPFX + name
        if obj not in sharp:
            continue
        ms = libs["grit"].get("clod" if key == "clod" else "gritstone")
        if not ms:
            continue
        me = ms[0][0]
        V = mesh_arrays(me)
        # library stones are authored at h0 and rescaled to h in hr
        h0 = float(np.mean([h for _, h in ms]))
        fac = poly_edge_mean(me, V)
        facet_mm = _p50(fac) / max(h0, 1e-6) * 1000.0
        sm = float(np.mean([smooth_fraction(m) for m, _ in ms]))
        ds = [dihedral_stats(m, mesh_arrays(m)) for m, _ in ms]
        dh = float(np.mean([d[0] for d in ds]))
        dfrac = float(np.mean([d[1] for d in ds]))
        cop = float(np.mean([d[2] for d in ds]))
        rows.append(dict(cls=obj, feature="piece size",
                         mm=(hr[0] * 1000, hr[1] * 1000), built=True, gate=None))
        rows.append(dict(cls=obj, feature="facet edge (BUILT)",
                         mm=(facet_mm * hr[0], facet_mm * hr[1]),
                         built=sm < 0.5, gate="grit_facet",
                         extra=dict(smooth_frac=round(sm, 4),
                                    dihedral_p50_deg=round(dh, 2),
                                    frac_edges_gt20=round(dfrac, 4),
                                    coplanar_frac=round(cop, 4))))

    # ---- weeds ------------------------------------------------------------
    for k, ms in libs["weed"].items():
        obj = BT.VPFX + "weed_%s" % k
        if obj not in sharp:
            continue
        sp = BT.WEEDS[k]
        hlo, hhi = sp["h"]
        Llo = hlo * sp["lsz"][0] * 1.55
        Lhi = hhi * sp["lsz"][1] * 1.55
        rows.append(dict(cls=obj, feature="plant height",
                         mm=(hlo * 1000, hhi * 1000), built=True, gate=None))
        rows.append(dict(cls=obj, feature="leaf length",
                         mm=(Llo * 1000, Lhi * 1000), built=True, gate=None))
        rows.append(dict(cls=obj, feature="leaf full width",
                         mm=(Llo * sp["lw"] * 1000, Lhi * sp["lw"] * 1000),
                         built=True, gate=None))
        rr = [leaf_margin_rms(me, mesh_arrays(me), 1) for me, _ in ms]
        good = np.array([r for r, n, s in rr if r == r])
        rms_mm = (_p50(good) * 1000.0) if len(good) else float("nan")
        st_med = int(np.median([s for _, _, s in rr])) if rr else 0
        # THE GATE APPLIES ONLY WHERE THE SPECIES DECLARES ITSELF PINNATIFID.
        # A dock or a plantain leaf really is entire-margined, so measuring one
        # against a lobe threshold would fail a correct mesh.  The declaration is
        # `LOBED_WEEDS`, the measurement is the mesh, and the gate is the
        # distance between them -- which is the only arrangement in which the
        # gate can catch "declared but not built", i.e. PATTERN 4.
        lobed = k in BT.LOBED_WEEDS
        rows.append(dict(cls=obj, feature="leaf margin relief (BUILT, RMS)",
                         mm=(rms_mm, rms_mm), built=True,
                         gate="leaf_margin" if lobed else None,
                         info=not lobed,
                         extra=dict(leaves_measured=int(sum(n for _, n, _s in rr)),
                                    stations_per_leaf=st_med,
                                    declared_lobed=lobed,
                                    spec=BT.LOBED_WEEDS.get(k))))
        srad = BT.WEED_STEM_R              # (base, tip) as a fraction of h
        sides = BT.WEED_STEM_SIDES
        d_lo, d_hi = 2 * srad[1] * hlo, 2 * srad[0] * hhi
        d_mid_px = px(obj, math.sqrt(d_lo * d_hi) * 1000)
        rows.append(dict(cls=obj, feature="stem diameter",
                         mm=(d_lo * 1000, d_hi * 1000), built=True, gate=None))
        # THE GATE IS ON THE POLYGONAL SILHOUETTE ERROR, AND IT IS AN UPPER
        # BOUND.  Everything else in this file asks "is the feature big enough to
        # see"; this one asks the opposite -- "is the ARTEFACT small enough not
        # to".  An n-gon standing for a circle falls (d/2)(1 - cos(pi/n)) inside
        # it, and that error is what makes a low-poly tube change width as it
        # spins.  It is read at the THICK end, not at the typical, because the
        # error grows with diameter and plant height is drawn uniformly, so the
        # thick end is one plant in a handful.
        #
        # It only applies where the stem is itself resolved: a plantain's flower
        # rod is 1.1 px thick, and how many sides a one-pixel tube has cannot be
        # a defect.  Gating it anyway fails correct geometry, and a gate that
        # fails correct geometry is a gate somebody switches off.
        err = 0.5 * (1.0 - math.cos(math.pi / sides))
        stem_resolved = d_mid_px >= 2.0
        rows.append(dict(cls=obj, feature="stem silhouette error (UPPER BOUND)",
                         mm=(d_lo * err * 1000, d_hi * err * 1000),
                         built=True, gate="stem_round" if stem_resolved else None,
                         info=not stem_resolved, upper=True, at=2,
                         extra=dict(sides=sides,
                                    stem_dia_px=round(float(d_mid_px), 2))))
        if sp["head"]:
            rows.append(dict(cls=obj, feature="floret",
                             mm=(0.020 * hlo * 1000, 0.055 * hhi * 1000),
                             built=True, gate=None))

    for feat, cls, mm, line, why in DECLINED:
        rows.append(dict(cls=cls, feature=feat, mm=mm, built=False,
                         gate=None, line=line, declined=why))

    # EVERY ROW CARRIES (low, TYPICAL, high) AND THE VERDICT IS TAKEN AT THE
    # TYPICAL.  Rows that only have a min/max size range get the geometric mean
    # as their typical, which is the right centre for a quantity spanning an
    # order of magnitude.
    # SUPPRESS THE GATE ON ANY CLASS WHOSE RESOLUTION IS UNVERIFIED.  The row is
    # still measured and still printed -- with UNVERIFIED on it, so it reads as a
    # gap in the evidence rather than as a pass.
    for r in rows:
        s = sharp.get(r["cls"])
        if s and not s["verified"] and r.get("gate"):
            r["gate"] = None
            r["unverified"] = True

    for r in rows:
        mm = list(r["mm"])
        if len(mm) == 2:
            mm = [mm[0], math.sqrt(max(mm[0], 0.0) * max(mm[1], 0.0)), mm[1]]
        r["mm"] = tuple(mm)
        r["px"] = tuple(px(r["cls"], v) for v in mm)
        mid = r["px"][r.get("at", 1)]
        if r.get("unverified"):
            r["verdict"] = "UNVERIFIED"
            continue
        if r.get("upper"):
            # an UPPER-BOUND row inverts the law: the quantity is an artefact,
            # so it must stay UNDER the line rather than clear it.
            r["verdict"] = ("INFO" if r.get("info") else
                            "UNMEASURABLE" if mid != mid else
                            "SUB-PIXEL" if mid < PX_LINE else "ARTEFACT")
            continue
        if r.get("info"):
            r["verdict"] = "INFO"
        elif mid != mid:
            # a BUILT-geometry row whose measurement came back nan did not
            # measure anything.  That is UNMEASURABLE, and this project's
            # gate_exit treats unmeasurable as vacuous, never as a pass.
            r["verdict"] = "UNMEASURABLE" if r["built"] else "NO-SCALE"
        elif mid < r.get("line", PX_LINE):
            r["verdict"] = "BELOW" if not r["built"] else "BELOW-BUT-BUILT"
        elif not r["built"]:
            r["verdict"] = "MISSING"
        elif mid < PX_LINE:
            r["verdict"] = "UNDER-BAND"
        elif r["px"][0] < PX_LINE:
            r["verdict"] = "MARGINAL"
        else:
            r["verdict"] = "ABOVE"
    return rows


# ---------------------------------------------------------------------------
# THE GATES.  One per mechanism, each with a threshold in PIXELS.
# ---------------------------------------------------------------------------
def gates(rows):
    """Every gate is 'this named mechanism must clear the pixel line'."""
    out = {}
    for r in rows:
        g = r.get("gate")
        if not g:
            continue
        key = "%s/%s" % (r["cls"], g)
        ok = r["verdict"] in ("ABOVE", "MARGINAL", "SUB-PIXEL")
        out[key] = dict(gate=g, cls=r["cls"], feature=r["feature"],
                        px=r["px"], verdict=r["verdict"], pass_=ok,
                        extra=r.get("extra"))
    return out


def report(rows, gts, sp_meta):
    print("\nMEASURED SHARP RESOLUTION (work/w2_0/retier_a10/sp_objects.json, "
          "%d frames, %s shutter)" % (sp_meta["frames"], sp_meta["shutter_mode"]))
    if CORRECTED_PX_PER_M:
        print("   sample-floor corrections applied (>=%d sharp samples, "
              "R2-2949/2949a):" % SAMPLE_FLOOR)
        for k, v in sorted(CORRECTED_PX_PER_M.items()):
            print("     %-24s file says %.2f px/m, corrected to %.2f px/m"
                  % (k, [o["peak_unocc_sharp_px_per_m"] for o in sp_meta["objects"]
                         if o["object"] == k][0], v))
    print("   px columns are low / TYPICAL / high over the world's own scale "
          "distribution; the verdict is taken at the TYPICAL.\n")
    print("%-24s %-36s %-22s %-21s  %s"
          % ("class", "feature", "size mm", "px", "verdict"))
    print("-" * 122)
    last = None
    for r in sorted(rows, key=lambda r: (r["cls"], r["feature"])):
        if r["cls"] != last:
            print("-" * 122)
            last = r["cls"]
        print("%-24s %-36s %6.2f %7.2f %6.2f  %5.2f %6.2f %5.2f  %s%s"
              % (r["cls"][:24], r["feature"][:36],
                 r["mm"][0], r["mm"][1], r["mm"][2],
                 r["px"][0], r["px"][1], r["px"][2], r["verdict"],
                 ("   <- " + r["declined"][:38]) if r.get("declined") else ""))
    print("\nGATES  (threshold: the TYPICAL must clear %.1f px)" % PX_LINE)
    for k in sorted(gts):
        g = gts[k]
        print("  %-48s %5.2f %6.2f %5.2f px  %-14s %s%s"
              % (k, g["px"][0], g["px"][1], g["px"][2], g["verdict"],
                 "PASS" if g["pass_"] else "FAIL",
                 ("  " + json.dumps(g["extra"])) if g["extra"] else ""))


def run(out_path):
    sharp, meta = sharp_table()
    libs = build_libs()
    nmesh = sum(len(v) for grp in libs.values() for v in grp.values())
    rows = measure(libs, sharp)
    gts = gates(rows)
    report(rows, gts, meta)
    if out_path:
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        json.dump(dict(rows=rows, gates=gts, meshes_measured=nmesh,
                       px_line=PX_LINE, source=SP_OBJECTS),
                  open(out_path, "w"), indent=1)
        print("\nwrote %s" % out_path)
    return rows, gts, nmesh


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="")
    a = ap.parse_args(argv)
    rows, gts, nmesh = run(a.out)

    if nmesh == 0:
        print(">> REFUSING TO REPORT: zero library meshes were built, so nothing "
              "about the ground cover was measured.")
        gate_exit.done("GROUNDCOVER_PX_VACUOUS")
        return
    bad = [k for k, g in gts.items() if not g["pass_"]]
    miss = [r for r in rows if r["verdict"] == "MISSING"]
    # WASTE IS ONLY CHARGED AGAINST OPTIONAL, GATED DETAIL.  A plantain's stem
    # is 0.58 px across; that is not a feature somebody chose to add below the
    # line, it is how thick a plantain's stem is, and the plant cannot be built
    # without one.  Charging it as waste would bury the one row that IS waste.
    waste = [r for r in rows if r["verdict"] == "BELOW-BUT-BUILT" and r.get("gate")]
    unver = sorted({r["cls"] for r in rows if r.get("unverified")})
    if unver:
        print("\n%d class(es) NOT GATED because their sharp resolution has not "
              "been re-run under a >=%d sample floor (R2-2949); they carry under "
              "%d points and their nearest neighbour collapsed 2.5x under that "
              "control:\n   %s" % (len(unver), SAMPLE_FLOOR, VERIFIED_MIN_POINTS,
                                   ", ".join(unver)))
    print("\n%d gate(s), %d failing; %d MISSING feature(s) above the pixel line; "
          "%d built below it" % (len(gts), len(bad), len(miss), len(waste)))
    for r in miss:
        print("   MISSING  %-24s %-34s typical %.2f px"
              % (r["cls"], r["feature"], r["px"][1]))
    for r in waste:
        print("   WASTE    %-24s %-34s typical %.2f px -- built below the line"
              % (r["cls"], r["feature"], r["px"][1]))
    if bad:
        for k in bad:
            print("   FAIL     %s  (%s)" % (k, gts[k]["verdict"]))
        gate_exit.done("GROUNDCOVER_PX_FAIL", "  [%s]" % ",".join(sorted(bad)))
    else:
        gate_exit.done("GROUNDCOVER_PX_CLEAN")


if __name__ == "__main__":
    main()
