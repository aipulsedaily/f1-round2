#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
terrain_ground.py — ITEM `terrain_ground`.  THE GROUND ITSELF, AT 2.5 mm.

    manifest:  nearest_camera_m 2.4   lens_at_closest_mm 35   instances 1
               hero: yes              dependents: 14
               px_per_m at that distance = 3840*35/36 / 2.4 = 1555.6
               => one 4K pixel is 0.643 mm of ground.

WHY THIS MODULE EXISTS
----------------------
`build_terrain.TER_Ground` is a 2.5 METRE grid.  Under the doppler hover the lens
is 2.4 m off that surface, where one of its cells is 3 889 screen pixels across.
Everything the eye reads as "ground" at that range — crumb, grit, worm cast,
crack, tread bar, thatch — lived in a bump map, and a bump map at a 12.5 deg sun
has no silhouette, no self-shadow and no parallax.  That is the whole of "the
grass is blurry" and "not a grass gray line done".

So this module keeps build_terrain's LANDFORM (it is the world's agreed datum and
it welds to `world_contract.corridor_rim`) and replaces the SURFACE with a
geometry clipmap that reaches 2.5 mm cells under the lens: 3.9 screen pixels at
the filmed distance.  Below 2.5 mm the shader takes over, which is the right
place for the hand-off and not one millimetre earlier.

-------------------------------------------------------------------------------
THE INTERFACE THE OTHER 14 ITEMS BUILD ON  —  this is a FOUNDATION item
-------------------------------------------------------------------------------
grass_clump_fescue / _dry / _meadow / _tussock, fern_clump, shrub_bramble /
_gorse / _broom / _hazel / _juniper, rock_scree_stone, rock_boulder, puddle and
ga_viewing_bank all scatter onto this surface.  None of their agents can ask me
anything, so everything they need is a call:

    ctx = terrain_ground.context()              # cached; builds once per session

    z      = terrain_ground.surface_z(X, Y)             # (N,) metres, world
    n      = terrain_ground.surface_normal(X, Y)        # (N,3) unit, world
    a      = terrain_ground.surface_attributes(X, Y)    # dict of the masks below
    s      = terrain_ground.sample(X, Y)                # z + normal + slope + a
    ok     = terrain_ground.is_terrain(X, Y)            # False where the ROAD
                                                        # programme owns the ground

  * `surface_z` INCLUDES this module's micro-relief.  `world_contract.ground_z`
    and `build_terrain.Ground.height` do not.  A clump placed on the contract
    datum instead of on this floats or sinks by up to
    MICRO_RELIEF_MAX_M = 0.160 m (measured max 0.1185 m, see `selftest`) — which
    at 2.4 m is 185-249 pixels of floating grass.  USE THIS FUNCTION.
  * `surface_z` is only defined where terrain owns the ground.  Test with
    `is_terrain` first; inside the road corridor use `world_contract.world_ground_z`.
  * `surface_normal` is the analytic normal of the same field, so a clump can be
    tilted onto the ground it actually stands on instead of straight up.
  * Sit on the ground with  z - BASE_EMBED_M  (world_contract, 0.020 m), never
    with an assumed z.

THE MASKS (baked as POINT attributes on every emitted mesh, and returned by
`surface_attributes`).  The first eight are the manifest's declared
`variation_axes`; they keep build_terrain's names and values EXACTLY, so anything
already reading them keeps working.  The last six are new and are the ones a
scatter actually wants:

    ter_wet      0..1  soil moisture. 1 in the swale invert and the low ground.
    ter_wear     0..1  trodden / driven / run-wide. 1 on the service strip.
    ter_cover    0..1  how much sward the ground carries.  SCATTER DENSITY.
    ter_mown     0..1  1 on the cut verge, 0 in the outfield.  BLADE LENGTH.
    ter_hedge    0..1  hedgerow root strip.
    ter_dry      0..1  per-field dryness of the crop.
    ter_field    RGB   per-field crop colour (FLOAT_COLOR attribute).
    ter_dist     0..1  distance from the circuit / 400 m.
    ter_bare     0..1  bare soil showing through.  1 - here, plant NOTHING.
    ter_grit     0..1  surface stone and grit cover.
    ter_thatch   0..1  dead litter mat lying on the soil.
    ter_rut      0..1  inside a service-vehicle wheel rut (compacted, gritty).
    ter_silt     0..1  fine washed silt: swale invert, rill mouths, puddle pans.
    ter_organic  0..1  humus richness -> how dark the topsoil reads.
    (also kept from build_terrain: ter_plateau, ter_rock, ter_moss, ter_scuff,
     ter_slope)

`ter_slope` is the slope of the GROUND, measured over SLOPE_SCALE_M = 0.60 m on
every ring, so a scatter gets the same answer at any LOD.  It is deliberately NOT
the 2.5 mm gradient: the first build fed the crumb-scale gradient into
build_terrain's stone mask and the macro render came back with grit laid out in
stripes along every crack.  `surface_normal` still answers at the 2.5 mm scale,
which is what an object needs to be seated; `ter_slope` is what a habitat rule
needs to be decided.

-------------------------------------------------------------------------------
WHAT IS ACTUALLY BUILT
-------------------------------------------------------------------------------
1. A GEOMETRY CLIPMAP.  Concentric square rings around a named centre, each a
   regular grid, each nested exactly inside the next:

     ring  cell        half-extent   quads     px at its own inner radius
     L0    2.5 mm        1.50 m      1.44 M    3.9   <- the filmed surface
     L1    5.0 mm        3.00 m      1.08 M    4.7
     L2    20  mm        8.00 m      0.55 M    7.4
     L3    100 mm       32.0  m      0.38 M    9.7
     L4    500 mm      130.0  m      0.25 M    9.5
     (L5-L7, 2.5 m / 12.5 m / 62.5 m, carry it to 21.75 km; off by default
      because the 2.4 m lens cannot see past 5 m of ground and they cost RAM)

   Rings are WELDED, not overlapped.  Two mechanisms, both necessary:
     * the height field is BAND-LIMITED to each ring's own cell, and over the
       outermost 10 cells of a ring it morphs to the NEXT ring's band limit, so
       there is no relief discontinuity at the join and no aliasing anywhere;
     * the fine ring's outer boundary vertices are then SNAPPED ONTO THE CHORD
       between the coarse ring's own boundary vertices, so the two surfaces
       share one curve exactly and there is no crack.  T-junctions are fine; a
       gap is not.

2. THE MICRO-RELIEF, which is the actual work.  Seventeen layers, each with a
   wavelength and an amplitude, each band-limited so it simply is not there on a
   ring that could not represent it:

     hummock  2.2 m/62 mm   ridge-and-furrow the verge inherited from the field
     swell    950 mm/26 mm  the slower roll under it
     tussock  620 mm/32 mm  the mounding at the base of old grass
     crown    24 mm/3.8 mm  TILLER CROWNS -- turf is a packing of little domes
     sward    48 mm/2.6 mm  the mower's own wash across them
     moss     40-90 mm      real cushion domes, 5-13 mm proud, in the damp
     wormwork 190 mm/8 mm   what a century of worms does to undisturbed turf
     clod     70 mm/6 mm    dried lumps where the sward is broken
     crumb    14 mm/2.8 mm  soil aggregate structure (voronoi, not noise)
     grain    7.5 mm/0.9 mm the sand fraction
     crack    110 mm cells  desiccation polygons, 6 mm wide and 14 mm deep
     rut      2 x 220 mm    the marshals' service track, 46 mm deep, at Dp 2.2
                            and 4.0 m, wandering +-0.35 m over 40 m of station
     tread    85 mm pitch   the tyre's own chevron bars printed in the rut floor
     pan      shallow flat-bottomed hollows where water stands in the rut
     boot     280x96 mm     footprints along the walkway, with a raised rim
     mole     230-500 mm    mounds of fine tilth
     rill     erosion runnels draining into the swale
     mat      THE TURF LIP -- living turf stands 17 mm proud of the soil beside
              it and TEARS at the edge; this is what makes a scrape read as a
              scrape in turf rather than as a brown patch

3. DISCRETE GEOMETRY that a height field cannot carry, every piece generated
   individually — there is no library of N shapes being reused, nothing is
   instanced, and every mesh in every class is its own random draw:
     TG_Grit     1 204 stones, each a UNIQUE random convex polytope (flint chip,
                 water-worn pebble or platy flake), 1-26 mm, part buried,
                 FLAT-SHADED so the arrises survive
     TG_Clod       378 dried soil lumps turned out of the rut
     TG_Cast       645 worm casts: real extruded coils, 16-34 mm across
     TG_Thatch   4 454 dead stems lying on the mat, 0.8-1.7 mm ribbons
     TG_Stubble 59 446 sheared stem butts, 8-26 mm, a third of them laid over
   The scatter covers the SECOND ring's extent (+-3.0 m), not the hero ring's,
   with a radial density taper -- scattering only inside the hero ring put a
   hard line across the top third of the macro frame where all of it stopped at
   once.

4. ONE LAYERED MATERIAL per class, all procedural, all reading
   TexCoord -> Object.  37 procedural texture nodes across the six.

-------------------------------------------------------------------------------
LIGHT, AND THE "PINK AND GREEN BLOTCHES"
-------------------------------------------------------------------------------
The manifest says it outright: terrain's materials were tuned for a 3.00:1
direct:diffuse ratio and the measured sky is 2.072:1, so shadow is 45 % brighter
relative to key than the albedos assume, and the fill is strongly blue
(SKY_TINT = 0.3115, 0.5582, 1.0000).  A soil albedo whose blue channel is near
zero therefore turns magenta in the sun and green in the shade.  That is the
mechanism, and the fix is in the numbers, not in a grade:

    every soil colour in PALETTE below has  b/r >= 0.45  and  g/r in 0.66..0.85,
    which is what a real 10YR Munsell soil measures.

`contract_light()` builds the sun and sky from `world_contract` §13 — NOT from
`tools/fix_audit_blend.py:procedural_world()`, which predates the contract and
uses aerosol 2.2 / ozone 1.0 / sun_intensity 0.85 and so would light this item
under a different sky than the film ships with.  `--calibrate` renders two
albedo-0.18 probes and prints the measured direct:diffuse against
world_contract's 2.072, so the claim is a measurement.

-------------------------------------------------------------------------------
RUN
-------------------------------------------------------------------------------
    B=/opt/blender-5.2.0-linux-x64/blender
    $B -b --factory-startup -noaudio -P world/items/terrain_ground.py -- \
        --test --save world/items/terrain_ground_test.blend
    $B -b --factory-startup -noaudio -P world/items/terrain_ground.py -- --selftest
    $B -b --factory-startup -noaudio -P world/items/terrain_ground.py -- \
        --test --quick --save /tmp/tg_quick.blend         (4x thinner, for debug)

Idempotent: every rebuild purges the TG_ collection and every TG_ datablock.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time

import numpy as np

# --------------------------------------------------------------------------------
#  paths / imports
# --------------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
WORLD = os.path.dirname(HERE)
ROOT = os.path.dirname(WORLD)
for _p in (WORLD, ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import world_contract as C          # THE datum, the corridor, the light   # noqa: E402

try:
    import bpy                       # noqa: E402
    import bmesh                     # noqa: E402
    HAVE_BPY = True
except Exception:                    # importable outside Blender for the maths
    HAVE_BPY = False

COLL = "ITEM_TERRAIN_GROUND"
PFX = "TG_"

SPEC_JSON = os.path.join(ROOT, "docs", "circuit_spec.json")

_T0 = time.time()


def log(msg):
    print("[terrain_ground %7.1fs] %s" % (time.time() - _T0, msg), flush=True)


# ================================================================================
#  0.  THE NUMBERS
# ================================================================================

# The filmed geometry, straight out of docs/item_manifest.json.  Nothing here is
# a guess and nothing here may be softened to make a gate pass.
FILMED_AT_M = 2.4
LENS_MM = 35.0
PX_PER_M = (3840.0 * LENS_MM / 36.0) / FILMED_AT_M          # 1555.6 px/m
HERO_CELL_M = 0.0025                                        # 3.89 px.  The point.

# The doppler hover: beat_sheet.json station 2555, 26.0 m off the centreline on
# the RIGHT of S11, the camera 2.4 m over the grade.  The manifest names this as
# the shot terrain_ground has to survive.
DOPPLER_S = 2555.0
DOPPLER_SIDE = -1
DOPPLER_CAM_WORLD = (-578.82, -47.47, 4.802)

# ...  and the honest correction.  At s = 2555 the barrier is pinned 30.0 m out
# (world_contract's doppler pin) so `platform_edge` is 37.904 m and the ground
# UNDER the hovering lens, at u = -26.0, is the runoff platform: owner
# "build_barriers:runoff platform", not terrain.  Terrain's own ground starts at
# the corridor rim, 11.90 m further out.  This module does not build inside the
# corridor — that is contract law and it is what stopped TER_Ground standing
# 0.381 m proud of the tarmac.  So the hero tile is centred on the nearest
# terrain-owned ground to that lens, 6.0 m outboard of the rim, and the macro
# camera is placed at EXACTLY the manifest's 2.4 m / 35 mm from it.
PLATFORM_EDGE = float(C.platform_edge(DOPPLER_S, DOPPLER_SIDE))   # 37.904 m
HERO_RIM_OFFSET_M = 2.9

# Service track: a marshals' quad runs the strip behind the barrier.  Gauge and
# tyre width are a Yamaha-class utility ATV, which is what a circuit actually
# uses, and the two ruts straddle the tile centre.
RUT_DP_M = (2.2, 4.0)          # metres outboard of the corridor rim.  This is
                               # where build_terrain's own `wear` profile puts
                               # the service strip (peak at Dp <= 3 m, gone by
                               # 9 m), so the ruts land where the rest of the
                               # world already says people walk and drive.
RUT_HALF_W_M = 0.110
RUT_DEPTH_M = 0.046
TREAD_PITCH_M = 0.085

BASE_EMBED_M = C.BASE_EMBED_M  # 0.020, re-exported so dependants need one import

# HOW FAR THIS MODULE'S SURFACE CAN BE FROM build_terrain's.  MEASURED, not
# asserted: over 25 000 random points spread across a 45 m x 800 m band of verge
# the largest |micro relief| is 0.1185 m (a molehill), p99 is 0.0357 m and the
# rms is 0.0140 m.  The analytic worst case if every layer's mask peaked at one
# point would be 0.33 m, but `bare` and `cover` are complementary so most of them
# cannot coincide.  The constant sits above every sample with headroom and
# `selftest` re-measures and PRINTS it, which is the part that matters.  14 other
# agents need this number and cannot run the selftest: it is the error a clump
# takes if it is placed on the CONTRACT datum instead of on `surface_z`, and at
# 2.4 m that is 249 screen pixels of float.
MICRO_RELIEF_MAX_M = 0.160

ATTR_SCALAR = (
    # the manifest's eight declared variation axes (ter_field is the RGB one)
    "ter_wet", "ter_wear", "ter_cover", "ter_mown", "ter_hedge", "ter_dry",
    "ter_dist",
    # build_terrain's extras, kept so nothing that reads them breaks
    "ter_plateau", "ter_rock", "ter_moss", "ter_scuff", "ter_slope",
    # this module's own
    "ter_bare", "ter_grit", "ter_thatch", "ter_rut", "ter_silt", "ter_organic",
)
ATTR_COLOR = ("ter_field",)
ATTR_NAMES = ATTR_SCALAR + ATTR_COLOR

# --------------------------------------------------------------------------------
#  THE CLIPMAP
# --------------------------------------------------------------------------------
# (cell_m, n_cells)  ->  half extent = cell*n/2.  Two invariants, asserted in
# `_check_rings`: cell[k] / cell[k-1] must be an integer (so the boundaries share
# vertices), and E[k-1] / cell[k] must be an integer (so the hole lands on grid
# lines).  Break either and the rings crack.
RINGS = [
    (0.0025, 1200),    # E =   1.50 m
    (0.0050, 1200),    # E =   3.00 m
    (0.0200,  800),    # E =   8.00 m
    (0.1000,  640),    # E =  32.00 m
    (0.5000,  520),    # E = 130.00 m
    (2.5000,  520),    # E = 650.00 m
    (12.500,  520),    # E =   3.25 km
    (62.500,  348),    # E =  10.875 km  (the manifest's 21.7 km square)
]
RINGS_DEFAULT = 5      # L0..L4 for the item blend; 8 for world assembly
BLEND_CELLS = 10       # how many of a ring's own cells the morph-to-coarser takes

# --------------------------------------------------------------------------------
#  PALETTE — linear reflectances, chosen so shadow does not go green
# --------------------------------------------------------------------------------
# b/r >= 0.45 on every soil.  See the header.  Means are the lambertian albedo
# the surface actually returns; `calibrate()` checks the render against
# world_contract.lambert_radiance for these.
PALETTE = dict(
    soil_wet=(0.0345, 0.0262, 0.0196),      # mean 0.027  saturated swale mud
    soil_damp=(0.0585, 0.0442, 0.0318),     # mean 0.045  moist loam
    soil_moist=(0.0840, 0.0630, 0.0448),    # mean 0.064
    topsoil=(0.1090, 0.0850, 0.0602),       # mean 0.085  humic A horizon
    soil_dry=(0.1690, 0.1360, 0.0995),      # mean 0.135
    crust=(0.2180, 0.1830, 0.1400),         # mean 0.180  dried silt crust
    clay_pale=(0.2450, 0.2020, 0.1560),     # mean 0.201  subsoil turned out
    thatch=(0.2050, 0.1690, 0.0905),        # mean 0.155  last year's dead grass
    thatch_old=(0.1230, 0.1010, 0.0625),    # mean 0.096  the rotted-down layer
    turf=(0.0420, 0.0820, 0.0280),          # = build_terrain GA_GRN, kept
    turf_pale=(0.0640, 0.0980, 0.0380),
    moss=(0.0270, 0.0510, 0.0215),
    algae=(0.0300, 0.0400, 0.0245),         # the film on damp silt
    flint_dark=(0.0640, 0.0605, 0.0545),    # fresh flint really is near-black
    flint_cortex=(0.1960, 0.1900, 0.1770),  # its chalk cortex
    limestone=(0.2480, 0.2410, 0.2185),
    sandstone=(0.2050, 0.1660, 0.1170),
    rubber=(0.0460, 0.0410, 0.0380),        # = build_terrain GA_RUBBER, kept
    dust=(0.2210, 0.1930, 0.1560),          # the pale film on a dry rut crown
)

SEED = 20260729


# ================================================================================
#  1.  NUMPY NOISE KIT
# ================================================================================
# Deterministic, seedable, and identical on every machine: the world is rebuilt
# by different agents on different boxes and two of them disagreeing about where
# a stone is would be a seam.

def _h2(ix, iy, seed):
    ix = ix.astype(np.int64)
    iy = iy.astype(np.int64)
    h = (ix * np.int64(1597334677)) ^ (iy * np.int64(3812015801))
    h = (h ^ np.int64(int(seed) * 2654435761)) & np.int64(0x7FFFFFFF)
    h = (h ^ (h >> 15)) * np.int64(2246822519)
    h = (h ^ (h >> 13)) * np.int64(3266489917)
    return (h ^ (h >> 16)) & np.int64(0x7FFFFFFF)


def hash01(ix, iy, seed=0):
    return _h2(np.asarray(ix), np.asarray(iy), seed).astype(np.float64) / float(0x7FFFFFFF)


def sstep(t):
    return t * t * (3.0 - 2.0 * t)


def smoothstep(a, b, x):
    return sstep(np.clip((np.asarray(x, float) - a) / (b - a + 1e-12), 0.0, 1.0))


def gnoise2(x, y, seed=0):
    """Perlin gradient noise, quintic, ~[-1, 1]."""
    ix = np.floor(x).astype(np.int64)
    iy = np.floor(y).astype(np.int64)
    fx = x - ix
    fy = y - iy

    def dot(cx, cy, dx, dy):
        a = hash01(cx, cy, seed) * (2.0 * math.pi)
        return np.cos(a) * dx + np.sin(a) * dy

    u = fx * fx * fx * (fx * (fx * 6 - 15) + 10)
    v = fy * fy * fy * (fy * (fy * 6 - 15) + 10)
    n00 = dot(ix, iy, fx, fy)
    n10 = dot(ix + 1, iy, fx - 1.0, fy)
    n01 = dot(ix, iy + 1, fx, fy - 1.0)
    n11 = dot(ix + 1, iy + 1, fx - 1.0, fy - 1.0)
    return (n00 * (1 - u) + n10 * u) * (1 - v) + (n01 * (1 - u) + n11 * u) * v


def fbm(x, y, octaves=3, lac=2.03, gain=0.5, seed=0):
    amp, f, tot, norm = 1.0, 1.0, 0.0, 0.0
    for o in range(octaves):
        tot = tot + amp * gnoise2(x * f, y * f, seed + o * 977)
        norm += amp
        amp *= gain
        f *= lac
    return tot / norm


def vor2(x, y, cs, seed=0, jitter=1.0):
    """2-D Worley cells of size `cs`.

    -> (f1, f2, cid, cx, cy):  distance to the nearest and second-nearest seed in
    METRES, a [0,1) id for the nearest cell, and the nearest seed's position.
    `f2 - f1` is the distance-to-edge field the crack network is cut from, and
    `f1` is what soil aggregate structure actually looks like — crumb is packed
    cells, not noise, and that is why this is here and not a TexNoise.
    """
    gx = np.floor(x / cs).astype(np.int64)
    gy = np.floor(y / cs).astype(np.int64)
    f1 = np.full(x.shape, 1e18)
    f2 = np.full(x.shape, 1e18)
    cid = np.zeros(x.shape)
    sx = np.zeros(x.shape)
    sy = np.zeros(x.shape)
    for ox in (-1, 0, 1):
        for oy in (-1, 0, 1):
            cxi = gx + ox
            cyi = gy + oy
            jx = (cxi + 0.5 + (hash01(cxi, cyi, seed + 11) - 0.5) * jitter) * cs
            jy = (cyi + 0.5 + (hash01(cxi, cyi, seed + 29) - 0.5) * jitter) * cs
            d = np.hypot(x - jx, y - jy)
            take = d < f1
            f2 = np.where(take, f1, np.minimum(f2, d))
            cid = np.where(take, hash01(cxi, cyi, seed + 47), cid)
            sx = np.where(take, jx, sx)
            sy = np.where(take, jy, sy)
            f1 = np.where(take, d, f1)
    return f1, f2, cid, sx, sy


def scatter_lattice(x, y, cs, seed, jitter=0.82):
    """Nearest jittered lattice point of spacing `cs`, plus its hashes.

    The workhorse for "one boot print / one molehill / one puddle pan per cell":
    a Poisson-ish point set that can be evaluated at a point instead of stored.
    -> (dx, dy, hid, h2) where (dx, dy) is the offset FROM the feature.
    """
    gx = np.floor(x / cs).astype(np.int64)
    gy = np.floor(y / cs).astype(np.int64)
    bd = np.full(x.shape, 1e18)
    bdx = np.zeros(x.shape)
    bdy = np.zeros(x.shape)
    bh = np.zeros(x.shape)
    bh2 = np.zeros(x.shape)
    for ox in (-1, 0, 1):
        for oy in (-1, 0, 1):
            cxi = gx + ox
            cyi = gy + oy
            jx = (cxi + 0.5 + (hash01(cxi, cyi, seed + 3) - 0.5) * jitter) * cs
            jy = (cyi + 0.5 + (hash01(cxi, cyi, seed + 5) - 0.5) * jitter) * cs
            ddx = x - jx
            ddy = y - jy
            d = ddx * ddx + ddy * ddy
            t = d < bd
            bd = np.where(t, d, bd)
            bdx = np.where(t, ddx, bdx)
            bdy = np.where(t, ddy, bdy)
            bh = np.where(t, hash01(cxi, cyi, seed + 7), bh)
            bh2 = np.where(t, hash01(cxi, cyi, seed + 13), bh2)
    return bdx, bdy, bh, bh2


# ================================================================================
#  2.  THE MACRO FIELD  —  build_terrain's landform, not a second opinion
# ================================================================================

_CTX = None


class Context(object):
    """Circuit + Ground + the cached spec.  Built once, shared by everything."""

    def __init__(self):
        import build_terrain as BT           # heavy; import only when needed
        self.BT = BT
        self.spec = json.load(open(SPEC_JSON))
        self.cir = BT.Circuit(self.spec)
        self.gr = BT.Ground(self.cir)


def context():
    """The cached build context.  Safe to call from any dependent item."""
    global _CTX
    if _CTX is None:
        t = time.time()
        _CTX = Context()
        log("context: build_terrain landform ready (%.1f s)" % (time.time() - t))
    return _CTX


_MACRO_KEYS = ("z", "f", "Dp", "s", "u", "D", "plateau", "built", "zrim")


def macro_at(X, Y, lattice_step=None):
    """build_terrain.Ground.height + its aux fields at arbitrary world points.

    `lattice_step` > 0 evaluates on a regular lattice and bilinearly reads it
    back.  That is not a shortcut: `Ground.height`'s shortest wavelength is
    7.4 m and its expensive part is a nearest-point search against a 14 700-point
    centreline, so sampling it at 0.20 m reproduces it to under 0.2 mm (checked
    in `selftest`) for 1/6 400 of the cost at a 2.5 mm cell.
    """
    ctx = context()
    X = np.asarray(X, float).ravel()
    Y = np.asarray(Y, float).ravel()
    if lattice_step is None or lattice_step <= 0.0:
        z, at = ctx.gr.height(X, Y, want_attr=True)
        out = {k: np.asarray(at[k], float) for k in _MACRO_KEYS if k != "z"}
        out["z"] = np.asarray(z, float)
        return out

    st = float(lattice_step)
    x0 = math.floor(X.min() / st) * st - st
    x1 = math.ceil(X.max() / st) * st + st
    y0 = math.floor(Y.min() / st) * st - st
    y1 = math.ceil(Y.max() / st) * st + st
    nx = int(round((x1 - x0) / st)) + 1
    ny = int(round((y1 - y0) / st)) + 1
    gx = x0 + np.arange(nx) * st
    gy = y0 + np.arange(ny) * st
    GX, GY = np.meshgrid(gx, gy, indexing="ij")
    z, at = ctx.gr.height(GX.ravel(), GY.ravel(), want_attr=True)

    grids = {"z": z.reshape(nx, ny)}
    for k in _MACRO_KEYS:
        if k == "z":
            continue
        v = np.asarray(at[k], float)
        if k == "s":
            # station is cyclic; unwrap about the tile's own median or the
            # interpolation runs backwards through s = 0 and prints a cliff.
            s0 = float(np.median(v))
            v = s0 + ((v - s0 + C.LAP * 0.5) % C.LAP) - C.LAP * 0.5
        grids[k] = v.reshape(nx, ny)

    fx = np.clip((X - x0) / st, 0, nx - 1.000001)
    fy = np.clip((Y - y0) / st, 0, ny - 1.000001)
    i0 = fx.astype(np.int64)
    j0 = fy.astype(np.int64)
    tx = fx - i0
    ty = fy - j0
    i1 = np.minimum(i0 + 1, nx - 1)
    j1 = np.minimum(j0 + 1, ny - 1)
    out = {}
    for k, g in grids.items():
        a = g[i0, j0] * (1 - tx) * (1 - ty) + g[i1, j0] * tx * (1 - ty)
        a = a + g[i0, j1] * (1 - tx) * ty + g[i1, j1] * tx * ty
        out[k] = a
    return out


# ================================================================================
#  3.  THE MICRO-RELIEF  —  everything below build_terrain's 7.4 m floor
# ================================================================================
#
# Every layer declares its characteristic WAVELENGTH.  `_bl` turns that into a
# weight against the ring's cell size: a feature needs about three cells to exist
# at all, so it fades in between 2.2 and 4.0 cells and is simply absent below
# that.  This is what makes the clipmap seamless — the coarse ring is not a
# decimation of the fine one, it is the same field asked a coarser question — and
# it is what stops a 7 mm layer aliasing into fireflies on a 0.5 m ring.

def bare_hint(wear):
    """Cheap stand-in for `bare` before the full mask exists (moss layer only)."""
    return np.clip(wear * 1.35, 0.0, 1.0)


def _bl(lam, cell):
    """Band-limit weight for a feature of wavelength `lam` on cells of `cell`."""
    return float(smoothstep(2.2 * cell, 4.0 * cell, lam))


def micro_relief(X, Y, cell, M, want_extra=False):
    """The layer this module adds on top of build_terrain's landform.

    X, Y  world metres.   `cell`  the ring's cell size.   `M`  macro_at() output.
    -> dz  (and, if asked, the masks the layers imply, which the attributes and
       the discrete scatters both need so that a stone and its shader agree).
    """
    Dp = M["Dp"]
    s = M["s"]
    plateau = M["plateau"]
    built = M["built"]

    # -- the three drivers, computed here so relief and attributes cannot drift --
    # marshals' walkway / service strip: build_terrain's own wear profile.
    wear = smoothstep(9.0, 1.5, Dp) * 0.52
    wear = np.maximum(wear, built * 0.6)
    wear = np.clip(wear, 0.0, 1.0)
    # sward cover, before this module's own bare patches
    cover = np.clip(1.0 - wear * 0.9, 0.0, 1.0)
    cover *= 0.55 + 0.45 * (0.5 + 0.5 * fbm(X / 46.0, Y / 46.0, 3, seed=307))
    mown = np.maximum(smoothstep(34.0, 3.0, Dp), built)
    wet = np.clip(smoothstep(1.5, -4.0, M["z"]) * 0.7
                  + 0.3 * smoothstep(0.35, 0.0, np.abs(fbm(X / 340.0, Y / 340.0, 2, seed=131))),
                  0.0, 1.0)
    wet = np.maximum(wet, 0.85 * np.exp(-(((Dp - 9.0) / 2.72) ** 2))
                     * smoothstep(1.2, 5.0, Dp))
    wet = np.clip(wet, 0.0, 1.0)

    dz = np.zeros(X.shape)

    # -- 1. HUMMOCK -------------------------------------------------------------
    # The verge was a field before it was a verge.  Ridge and furrow survives
    # mowing by decades; it is the reason a "flat" verge is never flat.
    w = _bl(2.2, cell)
    if w > 0:
        h = fbm(X / 2.20, Y / 2.20, 3, seed=1201)
        dz += w * 0.062 * h * (0.35 + 0.65 * cover) * (1.0 - 0.35 * mown) * (1.0 - plateau)
    w = _bl(0.95, cell)
    if w > 0:
        dz += w * 0.026 * fbm(X / 0.95, Y / 0.95, 3, seed=1237) * (1.0 - 0.30 * mown)

    # -- 2. TUSSOCK -------------------------------------------------------------
    w = _bl(0.62, cell)
    if w > 0:
        f1, f2, cid, _, _ = vor2(X, Y, 0.62, seed=1301, jitter=1.0)
        mound = np.clip(1.0 - f1 / 0.30, 0.0, 1.0) ** 1.5
        dz += w * 0.032 * mound * (0.25 + 0.75 * cid) * cover * (1.0 - 0.75 * wear)

    # -- 2b. THE SWARD MAT ------------------------------------------------------
    # The first macro render came back with the turf as flat green paint, because
    # every fine layer below was gated on `bare` and turf is not bare.  Mown turf
    # is NOT smooth: it is a packing of tiller crowns 15-30 mm across, each a
    # little dome of leaf bases, with the mower's own wash between them.  These
    # three layers are the turf's own micro-relief and they exist only where
    # there IS turf.
    w = _bl(0.024, cell)
    if w > 0:
        f1, f2, cid, _, _ = vor2(X, Y, 0.024, seed=1341, jitter=1.0)
        crown = np.clip(1.0 - f1 / 0.0145, 0.0, 1.0) ** 1.25
        dz += w * 0.0038 * (crown - 0.40) * (0.35 + 0.65 * cid) * cover
    w = _bl(0.048, cell)
    if w > 0:
        dz += w * 0.0026 * fbm(X / 0.048, Y / 0.048, 2, seed=1353) * cover
    # moss cushions: real domes, 40-90 mm across, in the damp and the shade
    w = _bl(0.13, cell)
    if w > 0:
        dx, dy, hid, h2 = scatter_lattice(X, Y, 0.34, seed=1367, jitter=1.0)
        rad = 0.020 + 0.026 * h2
        cush = np.clip(1.0 - (np.hypot(dx, dy) / rad) ** 2.1, 0.0, 1.0)
        dz += w * (0.0055 + 0.0075 * h2) * cush * (hid > 0.58) \
            * (1.0 - bare_hint(wear)) * (0.35 + 0.65 * wet)

    # -- 3. WORMWORK ------------------------------------------------------------
    # A century of casts, trodden flat and grown over: the fine lumpiness of old
    # undisturbed turf.  Damp ground has more of it because worms do.
    w = _bl(0.19, cell)
    if w > 0:
        h = fbm(X / 0.19, Y / 0.19, 3, seed=1409)
        dz += w * 0.0080 * h * (1.0 - 0.85 * wear) * (0.40 + 0.60 * wet)

    # -- the bare-ground mask, which the next four layers all key off ------------
    # THE TRANSECT.  The first version saturated: wear*1.25 + (1-cover)*0.85 took
    # the whole service strip to bare = 1 and the macro frame came back looking
    # like a dry lake bed.  A walked verge does not do that -- it keeps 50-70 %
    # sward and goes truly bare only in the wheel tracks and on the single most
    # trodden line.  So the strip is a GRADIENT from turf through thin sward to
    # bare rut, which is the whole of "not a grass gray line".
    patchy = 0.5 + 0.5 * fbm(X / 0.85, Y / 0.85, 3, seed=1511)
    patchy2 = 0.5 + 0.5 * fbm(X / 0.24 + 4.0, Y / 0.24, 3, seed=1523)
    bare = np.clip(wear * 1.05 + (1.0 - cover) * 0.40 - 0.42, 0.0, 1.0)
    bare = np.clip(bare * (0.30 + 0.95 * patchy) * (0.55 + 0.60 * patchy2), 0.0, 1.0)

    # THE SERVICE TRACK, laid out before the bare mask because a tyre strips
    # turf: the ruts ARE the bare ground, and computing `bare` without them left
    # the two most-used strips of the whole verge grassed over.
    track = smoothstep(0.12, 0.30, wear) * (1.0 - plateau)
    wander = 0.35 * fbm(s / 42.0, np.zeros_like(s), 2, seed=2003)
    rut_prof = [np.exp(-(((Dp - (dpc + wander)) / RUT_HALF_W_M) ** 2) * 1.15)
                for dpc in RUT_DP_M]
    rut_tot = np.clip(np.maximum.reduce(rut_prof) * track, 0.0, 1.0)
    bare = np.clip(np.maximum(bare, rut_tot * (0.62 + 0.42 * patchy2)), 0.0, 1.0)

    # -- 4. CLOD ----------------------------------------------------------------
    w = _bl(0.070, cell)
    if w > 0:
        f1, f2, cid, _, _ = vor2(X, Y, 0.070, seed=1601, jitter=1.0)
        lump = np.clip(1.0 - f1 / 0.040, 0.0, 1.0) ** 1.35
        dz += w * 0.0060 * lump * (0.30 + 0.70 * cid) * bare

    # -- 5. CRUMB ---------------------------------------------------------------
    # Soil aggregate structure.  Cells, not noise: crumb is a packing.
    w = _bl(0.014, cell)
    if w > 0:
        f1, f2, cid, _, _ = vor2(X, Y, 0.014, seed=1709, jitter=1.0)
        agg = np.clip(1.0 - f1 / 0.0082, 0.0, 1.0) ** 1.2
        dz += w * 0.0028 * (agg - 0.42) * (0.4 + 0.6 * cid) * bare

    # -- 6. GRAIN ---------------------------------------------------------------
    w = _bl(0.0075, cell)
    if w > 0:
        dz += w * 0.00090 * fbm(X / 0.0075, Y / 0.0075, 2, seed=1811) * bare

    # -- 7. DESICCATION CRACKS --------------------------------------------------
    # Only in dry, bare, fine-textured ground.  6 mm wide, 14 mm deep, on a
    # 110 mm polygon — which is a shrinkage crack in a silty clay loam, measured
    # off the ground and not off a shader preset.
    crackm = np.zeros(X.shape)
    w = _bl(0.110, cell)
    if w > 0:
        f1, f2, cid, _, _ = vor2(X, Y, 0.110, seed=1907, jitter=0.95)
        edge = f2 - f1
        # cracks are a PATCH phenomenon: they need bare, dry, undisturbed fines,
        # which is a small fraction of a verge and not the whole of it
        dry_clay = bare * np.clip(1.0 - wet * 2.2, 0.0, 1.0) \
            * smoothstep(0.52, 0.82, 0.5 + 0.5 * fbm(X / 1.35, Y / 1.35, 2, seed=1913))
        crackm = np.clip(1.0 - edge / 0.006, 0.0, 1.0) ** 0.65 * dry_clay
        dz -= w * 0.014 * crackm
        # the polygon between cracks curls up at its rim as it dries
        dz += w * 0.0022 * smoothstep(0.010, 0.030, edge) * dry_clay

    # ---------------------------------------------------------------------------
    #  THE SERVICE TRACK.  A marshals' quad runs the strip behind the barrier all
    #  season; by the last race it has printed two ruts into the turf.  This is
    #  the single most legible thing in the macro frame and it is all geometry.
    # ---------------------------------------------------------------------------
    for ri, dpc in enumerate(RUT_DP_M):
        dv = Dp - (dpc + wander)
        prof = rut_prof[ri]
        # depth varies along the track: soft where it is wet, barely there where
        # the ground is hard
        depth = RUT_DEPTH_M * (0.45 + 0.55 * (0.5 + 0.5 * fbm(s / 7.5, np.full_like(s, ri * 3.7),
                                                              3, seed=2101)))
        # a rut is cut when the ground is wet and it SURVIVES the ground drying
        # out, so the moisture term biases the depth, it does not gate it
        depth = depth * (0.78 + 0.44 * wet)
        w = _bl(2.0 * RUT_HALF_W_M, cell)
        dz -= w * depth * prof * track
        # the berm: soil pushed out to each shoulder
        berm = np.exp(-(((np.abs(dv) - RUT_HALF_W_M * 1.9) / (RUT_HALF_W_M * 0.9)) ** 2))
        dz += w * depth * 0.30 * berm * track

        # -- 9. TREAD.  The tyre's own bars, printed in the rut floor.  85 mm
        #    pitch, chevron, 6 mm deep.  At 2.5 mm cells this is 34 cells per
        #    bar: it is real geometry, it self-shadows at a 12.5 deg sun, and it
        #    is the reason the rut reads as a rut and not as a dark stripe.
        w = _bl(TREAD_PITCH_M * 0.5, cell)
        if w > 0:
            chev = s + np.abs(dv) * 1.35
            bar = np.cos(2.0 * math.pi * chev / TREAD_PITCH_M)
            bar = np.clip((bar - 0.05) / 0.55, 0.0, 1.0)
            fresh = smoothstep(0.30, 0.70, 0.5 + 0.5 * fbm(s / 3.1, np.full_like(s, ri),
                                                           2, seed=2203))
            dz -= w * 0.0082 * bar * prof * track * fresh * (0.62 + 0.38 * wet)

    # -- 10. PANS.  Flat-bottomed hollows in the rut where water stands and the
    #     fines settle out.  Their floor is deliberately FLATTENED, not dished:
    #     that is what a silted puddle bottom is, and it is where `ter_silt`
    #     comes from.
    pan = np.zeros(X.shape)
    w = _bl(0.55, cell)
    if w > 0:
        dx, dy, hid, h2 = scatter_lattice(X, Y, 1.9, seed=2311, jitter=0.9)
        r = np.hypot(dx, dy)
        rad = 0.16 + 0.34 * h2
        pan = np.clip(1.0 - (r / rad) ** 2.6, 0.0, 1.0) * (hid > 0.42) * rut_tot
        dz -= w * 0.016 * pan * (0.4 + 0.6 * wet)

    # -- 11. BOOT PRINTS along the walkway --------------------------------------
    w = _bl(0.19, cell)
    if w > 0:
        walk = smoothstep(3.2, 1.1, Dp) * smoothstep(0.15, 0.40, wear)
        dx, dy, hid, h2 = scatter_lattice(X, Y, 0.62, seed=2417, jitter=1.0)
        th = (h2 * 0.9 - 0.45) + math.radians(20.0)
        ex = dx * np.cos(th) + dy * np.sin(th)
        ey = -dx * np.sin(th) + dy * np.cos(th)
        rr = np.hypot(ex / 0.140, ey / 0.048)          # 280 x 96 mm boot
        prof = np.clip(1.0 - rr, 0.0, 1.0)
        rim = np.clip(1.0 - np.abs(rr - 1.12) / 0.30, 0.0, 1.0)
        hit = (hid > 0.55).astype(float)
        dz -= w * 0.019 * sstep(prof) * hit * walk * (0.4 + 0.9 * wet)
        dz += w * 0.0055 * rim * hit * walk

    # -- 12. MOLEHILLS ----------------------------------------------------------
    mole = np.zeros(X.shape)
    w = _bl(0.36, cell)
    if w > 0:
        dx, dy, hid, h2 = scatter_lattice(X, Y, 7.5, seed=2521, jitter=1.0)
        r = np.hypot(dx, dy)
        rad = 0.115 + 0.135 * h2
        hit = (hid > 0.62) & (wear < 0.30) & (Dp > 2.0)
        mole = np.clip(1.0 - (r / rad) ** 1.7, 0.0, 1.0) * hit
        dz += w * (0.055 + 0.075 * h2) * mole ** 1.35

    # -- 13. RILLS.  Water leaves the service strip for the swale and cuts
    #     runnels doing it.  They deepen with Dp up to the invert at 9 m.
    w = _bl(0.16, cell)
    if w > 0:
        flow = smoothstep(2.0, 7.5, Dp) * (1.0 - smoothstep(8.4, 10.2, Dp))
        ch = np.abs(fbm(X / 3.4 + 11.0, Y / 3.4, 3, seed=2617))
        rill = np.clip(1.0 - ch / 0.085, 0.0, 1.0) ** 1.4
        dz -= w * 0.030 * rill * flow

    # -- 14. THE TURF MAT.  The single most legible thing on a worn verge and the
    #     one a height field usually misses: living turf sits 10-20 mm PROUD of
    #     the soil beside it, because the mat is roots, thatch and years of cast.
    #     Where a boot or a tyre has stripped it, the edge is a small cliff with
    #     an undercut lip, not a fade.  Building that as geometry is what turns
    #     "a bare patch" into "a scrape in turf".
    w = _bl(0.13, cell)
    if w > 0:
        mat = 1.0 - np.clip(bare * 1.35, 0.0, 1.0)
        mat = mat * mat * (3.0 - 2.0 * mat)
        dz += w * 0.017 * mat * (0.45 + 0.55 * cover)
        # the lip: a narrow band of extra height right at the mat's broken edge
        lip = np.clip(1.0 - np.abs(bare - 0.62) / 0.13, 0.0, 1.0)
        dz += w * 0.0075 * lip * cover

    # ---------------------------------------------------------------------------
    #  THE WELD.  world_contract.corridor_rim is not a tolerance, it is a datum:
    #  build_barriers' runoff platform ends exactly there and terrain's first
    #  vertex sits exactly on it.  build_terrain.Ground.height already satisfies
    #  that (its batter weight is 0 at Dp = 0); this module's relief would then
    #  add up to 22 mm of its own and break it -- measured, and it is why
    #  `selftest` checks the weld instead of assuming it.  So the whole micro
    #  layer is held to zero at the rim and released over 0.45 m.  That is also
    #  what the ground does: the strip at the barrier foot is mown, trodden and
    #  smooth, not lumpy.
    hold = smoothstep(0.0, 0.45, Dp)
    dz = dz * hold

    if not want_extra:
        return dz

    silt = np.clip(pan * 1.2 + smoothstep(6.5, 9.0, Dp) * wet * 0.8, 0.0, 1.0)
    extra = dict(wear=wear, cover=cover, mown=mown, wet=wet, bare=bare,
                 crack=crackm, rut=np.clip(rut_tot, 0.0, 1.0), pan=pan,
                 mole=mole, silt=silt, track=track)
    return dz, extra


def _height(X, Y, cell, M):
    """The finished ground: build_terrain's landform + this module's relief."""
    return M["z"] + micro_relief(X, Y, cell, M)


# ================================================================================
#  4.  THE PUBLIC SAMPLING API  (what the 14 dependants call)
# ================================================================================

def is_terrain(X, Y):
    """True where THIS module owns the ground.

    False inside `world_contract.road_corridor_mask` — the racing surface, the
    runoff platform, the access ribbon and the declared apron.  A dependant that
    scatters there must use `world_contract.world_ground_z` instead; a dependant
    that scatters there using MY z will float or bury by up to 0.4 m, which is
    exactly the assembly finding the corridor hole was created to stop.
    """
    return ~C.road_corridor_mask(np.asarray(X, float), np.asarray(Y, float))


def surface_z(X, Y, cell=HERO_CELL_M, lattice_step=0.20):
    """z of the finished terrain ground at world (X, Y).  Vectorised.

    Includes this module's micro-relief, so a clump placed with it stands ON the
    ground rather than up to 0.160 m above or below it.
    """
    X = np.atleast_1d(np.asarray(X, float))
    Y = np.atleast_1d(np.asarray(Y, float))
    M = macro_at(X, Y, lattice_step)
    return _height(X, Y, cell, M)


def surface_normal(X, Y, eps=0.006, cell=HERO_CELL_M, lattice_step=0.20):
    """Unit world normal of the finished surface.  Central difference at `eps`.

    `eps` = 6 mm by default, i.e. the 2.5 mm relief is differentiated at its own
    scale.  Pass eps = 0.25 for a scatter that wants the SLOPE of the ground
    rather than the tilt of one crumb.
    """
    X = np.atleast_1d(np.asarray(X, float))
    Y = np.atleast_1d(np.asarray(Y, float))
    P = np.concatenate([X - eps, X + eps, X, X])
    Q = np.concatenate([Y, Y, Y - eps, Y + eps])
    M = macro_at(P, Q, lattice_step)
    z = _height(P, Q, cell, M)
    n = len(X)
    dzdx = (z[n:2 * n] - z[0:n]) / (2 * eps)
    dzdy = (z[3 * n:4 * n] - z[2 * n:3 * n]) / (2 * eps)
    N = np.stack([-dzdx, -dzdy, np.ones(n)], axis=1)
    return N / np.linalg.norm(N, axis=1)[:, None]


def surface_attributes(X, Y, cell=HERO_CELL_M, lattice_step=0.20):
    """The full mask set at world (X, Y).  -> dict, keys are ATTR_NAMES."""
    X = np.atleast_1d(np.asarray(X, float))
    Y = np.atleast_1d(np.asarray(Y, float))
    M = macro_at(X, Y, lattice_step)
    dz, ex = micro_relief(X, Y, cell, M, want_extra=True)
    Z = M["z"] + dz
    # slope at the 0.25 m scale, which is the one a scatter wants
    slope = _slope_by_difference(X, Y, SLOPE_SCALE_M, cell, lattice_step)
    return _attributes(X, Y, Z, M, ex, slope)


def sample(X, Y, cell=HERO_CELL_M, lattice_step=0.20):
    """Everything at once: z, normal, slope and every mask.  One pass."""
    X = np.atleast_1d(np.asarray(X, float))
    Y = np.atleast_1d(np.asarray(Y, float))
    M = macro_at(X, Y, lattice_step)
    dz, ex = micro_relief(X, Y, cell, M, want_extra=True)
    Z = M["z"] + dz
    slope = _slope_by_difference(X, Y, SLOPE_SCALE_M, cell, lattice_step)
    out = _attributes(X, Y, Z, M, ex, slope)
    out["z"] = Z
    out["normal"] = surface_normal(X, Y, cell=cell, lattice_step=lattice_step)
    out["slope"] = slope
    out["is_terrain"] = is_terrain(X, Y)
    return out


def _slope_by_difference(X, Y, h, cell, lattice_step):
    """Central-difference |grad z| over a baseline of `h` metres."""
    P = np.concatenate([X - h, X + h, X, X])
    Q = np.concatenate([Y, Y, Y - h, Y + h])
    M = macro_at(P, Q, lattice_step)
    z = _height(P, Q, cell, M)
    n = len(X)
    return np.hypot((z[n:2 * n] - z[0:n]) / (2 * h), (z[3 * n:4 * n] - z[2 * n:3 * n]) / (2 * h))


def hero_tiles():
    """Where 2.5 mm ground exists.  -> [(cx, cy, half_m, cell_m), ...]."""
    cx, cy = hero_centre()
    return [(cx, cy, RINGS[0][0] * RINGS[0][1] * 0.5, RINGS[0][0])]


def hero_centre():
    """World XY of the hero tile: 6.0 m outboard of the corridor rim at s=2555."""
    lat = PLATFORM_EDGE + HERO_RIM_OFFSET_M
    x, y, _ = C.su_to_world(DOPPLER_S, lat * DOPPLER_SIDE)
    return float(x), float(y)


# ================================================================================
#  5.  ATTRIBUTES
# ================================================================================

def _attributes(X, Y, Z, M, ex, slope):
    """Per-vertex surface description.  Nineteen masks, not one grey line.

    The first eight are build_terrain's, computed by build_terrain itself so they
    cannot drift from the rest of the world; the rest are this module's, and they
    are computed from the SAME intermediate fields the micro-relief was cut from,
    so the shader's crack mask is the crack that is actually in the mesh.
    """
    ctx = context()
    at = dict(Dp=M["Dp"], plateau=M["plateau"], built=M["built"], D=M["D"],
              s=M["s"], u=M["u"], slope=slope)
    a = ctx.BT.ground_attributes(X, Y, Z, at)          # the canonical eight + 5

    # DELIBERATE, STATED CHANGE TO build_terrain's ter_cover.  Its formula is
    #     cover = (1 - wear*0.9) * (0.55 + 0.45*noise) * (1 - 0.75*rock)
    # and the middle factor multiplies unconditionally, so even untouched mown
    # verge came out 0.44 covered.  A mown verge is 70-90 % covered; at 44 % the
    # macro render is a litter field with grass in it rather than the other way
    # round.  The floor is applied ONLY inside the mown band, so the outfield,
    # the scuffed ground and the runoff keep build_terrain's numbers exactly.
    a["ter_cover"] = np.maximum(
        a["ter_cover"], a["ter_mown"] * np.clip(0.88 - 1.05 * ex["wear"], 0.0, 1.0))
    bare = np.clip(ex["bare"] * (1.0 - 0.55 * a["ter_moss"]), 0.0, 1.0)
    a["ter_bare"] = bare
    a["ter_cover"] = np.clip(np.minimum(a["ter_cover"], 1.0 - bare * 0.9), 0.0, 1.0)
    a["ter_rut"] = ex["rut"]
    a["ter_silt"] = ex["silt"]

    # grit: the 4-70 mm fraction lying on the surface.  Concentrated in the rut
    # (dragged up by the tyre), on the walkway, and wherever the sward is gone.
    grit = np.clip(0.65 * bare + 0.55 * ex["rut"] + 0.85 * a["ter_rock"], 0.0, 1.0)
    grit *= 0.40 + 0.60 * (0.5 + 0.5 * fbm(X / 1.15, Y / 1.15, 3, seed=3301))
    a["ter_grit"] = np.clip(grit, 0.0, 1.0)

    # thatch: last year's dead grass, thickest where the sward is dense and the
    # mower has left it, thinnest where anything walks
    th = np.clip(a["ter_cover"] * (0.55 + 0.45 * a["ter_mown"]) - ex["wear"] * 0.55, 0.0, 1.0)
    th *= 0.35 + 0.65 * (0.5 + 0.5 * fbm(X / 0.62, Y / 0.62, 3, seed=3407))
    a["ter_thatch"] = np.clip(th * (1.0 - 0.7 * a["ter_wet"]), 0.0, 1.0)

    # humus: dark where undisturbed and damp, thin on the scraped strip
    org = np.clip(0.35 + 0.55 * a["ter_cover"] + 0.35 * a["ter_wet"]
                  - 0.55 * ex["wear"], 0.0, 1.0)
    org *= 0.70 + 0.30 * (0.5 + 0.5 * fbm(X / 3.4, Y / 3.4, 3, seed=3511))
    a["ter_organic"] = np.clip(org, 0.0, 1.0)

    # the crack network is a real notch in the mesh; hand the shader the same mask
    a["ter_rock"] = np.clip(a["ter_rock"] + 0.35 * ex["crack"], 0.0, 1.0)
    a["ter_slope"] = np.clip(slope, 0.0, 1.2)
    return a


# ================================================================================
#  6.  MESH PLUMBING
# ================================================================================

def _new_mesh(name, verts, quads=None, tris=None):
    me = bpy.data.meshes.new(name)
    verts = np.ascontiguousarray(verts, dtype=np.float32)
    me.vertices.add(len(verts))
    me.vertices.foreach_set("co", verts.ravel())
    polys, counts = [], []
    if quads is not None and len(quads):
        polys.append(np.asarray(quads, np.int32).ravel())
        counts.append(np.full(len(quads), 4, np.int32))
    if tris is not None and len(tris):
        polys.append(np.asarray(tris, np.int32).ravel())
        counts.append(np.full(len(tris), 3, np.int32))
    if polys:
        loops = np.concatenate(polys)
        counts = np.concatenate(counts)
        starts = np.concatenate([[0], np.cumsum(counts)[:-1]]).astype(np.int32)
        me.loops.add(len(loops))
        me.loops.foreach_set("vertex_index", loops)
        me.polygons.add(len(counts))
        me.polygons.foreach_set("loop_start", starts)
    me.update(calc_edges=True)
    me.validate(verbose=False)
    return me


def _bake_attrs(me, attrs):
    for name in ATTR_SCALAR:
        if name not in attrs:
            continue
        a = me.attributes.new(name, "FLOAT", "POINT")
        a.data.foreach_set("value", np.ascontiguousarray(attrs[name], np.float32))
    for name in ATTR_COLOR:
        if name not in attrs:
            continue
        d = np.asarray(attrs[name], np.float32)
        a = me.attributes.new(name, "FLOAT_COLOR", "POINT")
        rgba = np.concatenate([d, np.ones((len(d), 1), np.float32)], axis=1)
        a.data.foreach_set("color", np.ascontiguousarray(rgba).ravel())


def _link(ob, coll):
    coll.objects.link(ob)
    return ob


def _coll(name, parent=None):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(c)
    return c


def purge():
    """Delete everything this module has ever made, and nothing else."""
    root = bpy.data.collections.get(COLL)
    if root:
        stack, seen = [root], []
        while stack:
            c = stack.pop()
            seen.append(c)
            stack.extend(list(c.children))
        for c in seen:
            for o in list(c.objects):
                bpy.data.objects.remove(o, do_unlink=True)
        for c in seen:
            bpy.data.collections.remove(c)
    for lib in (bpy.data.objects, bpy.data.meshes, bpy.data.materials,
                bpy.data.lights, bpy.data.cameras, bpy.data.worlds,
                bpy.data.node_groups):
        for d in list(lib):
            if d.name.startswith(PFX):
                try:
                    lib.remove(d)
                except Exception:
                    pass


# ================================================================================
#  7.  THE CLIPMAP RINGS
# ================================================================================

SLOPE_SCALE_M = 0.60      # the baseline `ter_slope` and every mask that reads it
                          # are measured over this much ground, on every ring


def _box_slope(Zg, cell, scale=SLOPE_SCALE_M):
    """|grad z| of `Zg` after a separable box filter of width `scale`.

    A summed-area pass, so it costs the same on a 1.44 M-vertex ring as on a
    0.15 M one.  Edges use a shrinking window rather than wrapping, because a
    ring's edge is a real boundary and wrapping it would print a false ridge.
    """
    k = max(1, int(round(scale / cell)) // 2)
    if k < 1:
        return np.hypot(*np.gradient(Zg, cell, cell))
    A = Zg
    for axis in (0, 1):
        n = A.shape[axis]
        cs = np.cumsum(A, axis=axis)
        cs = np.concatenate([np.zeros_like(np.take(cs, [0], axis=axis)), cs], axis=axis)
        lo = np.clip(np.arange(n) - k, 0, n)
        hi = np.clip(np.arange(n) + k + 1, 0, n)
        A = (np.take(cs, hi, axis=axis) - np.take(cs, lo, axis=axis)) \
            / (hi - lo).reshape((-1, 1) if axis == 0 else (1, -1))
    gx, gy = np.gradient(A, cell, cell)
    return np.hypot(gx, gy)


def _check_rings(rings):
    for k in range(1, len(rings)):
        c0, n0 = rings[k - 1]
        c1, n1 = rings[k]
        r = c1 / c0
        assert abs(r - round(r)) < 1e-9, "ring %d: cell ratio %.6f is not integral" % (k, r)
        e0 = c0 * n0 * 0.5
        q = e0 / c1
        assert abs(q - round(q)) < 1e-9, "ring %d: hole %.4f is not a whole cell" % (k, q)
        assert n1 % 2 == 0 and n0 % 2 == 0
        assert c1 * n1 * 0.5 > e0 + c1, "ring %d does not enclose ring %d" % (k, k - 1)


def _boundary_loop(n, half):
    """Ordered (i, j) index pairs once around the square |i-n/2| = |j-n/2| = half.

    Counter-clockwise from the (-half, -half) corner, corner counted once.  Both
    a ring's own outer boundary and its neighbour's hole boundary are generated
    by this, so the two loops correspond term for term.
    """
    c = n // 2
    lo, hi = c - half, c + half
    I, J = [], []
    for j in range(lo, hi):            # +x edge going +y ... (bottom, x=lo)
        I.append(lo)
        J.append(j)
    for i in range(lo, hi):
        I.append(i)
        J.append(hi)
    for j in range(hi, lo, -1):
        I.append(hi)
        J.append(j)
    for i in range(hi, lo, -1):
        I.append(i)
        J.append(lo)
    return np.array(I), np.array(J)


def build_ring(k, rings, centre, coll, lattice_step, mat, cut_corridor=True,
               stats=None):
    """One clipmap ring, welded to its neighbours and cut clear of the corridor."""
    cell, n = rings[k]
    E = cell * n * 0.5
    cx, cy = centre
    hole = int(round((rings[k - 1][0] * rings[k - 1][1] * 0.5) / cell)) if k > 0 else 0
    cnext = rings[k + 1][0] if k + 1 < len(rings) else None

    idx = np.arange(n + 1) - n // 2
    xs = cx + idx * cell
    ys = cy + idx * cell
    GX, GY = np.meshgrid(xs, ys, indexing="ij")
    X = GX.ravel()
    Y = GY.ravel()

    t0 = time.time()
    M = macro_at(X, Y, lattice_step if cell < 0.30 else 0.0)
    dz, ex = micro_relief(X, Y, cell, M, want_extra=True)
    Z = M["z"] + dz

    # ---- morph to the next ring's band limit over the outer BLEND_CELLS -------
    if cnext is not None:
        r = np.maximum(np.abs(X - cx), np.abs(Y - cy))
        w = smoothstep(E - BLEND_CELLS * cell, E, r)
        act = w > 1e-6
        if act.any():
            dzc = micro_relief(X[act], Y[act], cnext, {kk: v[act] for kk, v in M.items()})
            Z[act] = Z[act] * (1.0 - w[act]) + (M["z"][act] + dzc) * w[act]
        # and pin the boundary EXACTLY on the coarse ring's chord, so the two
        # surfaces share one curve and there is no crack to see sky through
        rr = int(round(cnext / cell))
        bi, bj = _boundary_loop(n, n // 2)
        lin = bi * (n + 1) + bj
        zb = Z[lin]
        m = len(zb)
        assert m % rr == 0
        a0 = (np.arange(m) // rr) * rr
        a1 = (a0 + rr) % m
        t = (np.arange(m) % rr) / float(rr)
        Z[lin] = zb[a0] * (1.0 - t) + zb[a1] * t

    # ---- slope ---------------------------------------------------------------
    # AT THE LANDSCAPE SCALE, NOT THE RING'S.  The first version differentiated
    # the 2.5 mm field, so `slope` was the tilt of one soil crumb -- and
    # build_terrain's `rock` mask, which reads slope, therefore printed grit
    # along every crumb ridge and every crack.  The macro render showed it as
    # stones in stripes.  Slope is a question about the ground, so it is asked
    # at SLOPE_SCALE_M and the answer is the same on every ring.
    Zg = Z.reshape(n + 1, n + 1)
    slope = _box_slope(Zg, cell).ravel()
    attrs = _attributes(X, Y, Z, M, ex, slope)

    # ---- faces ---------------------------------------------------------------
    I = np.arange(n)[:, None] * (n + 1) + np.arange(n)[None, :]
    Q = np.stack([I, I + (n + 1), I + (n + 1) + 1, I + 1], axis=-1).reshape(-1, 4)
    keepq = np.ones(n * n, bool)
    if hole:
        c = n // 2
        gi = np.arange(n)[:, None]
        gj = np.arange(n)[None, :]
        inside = ((gi >= c - hole) & (gi < c + hole) &
                  (gj >= c - hole) & (gj < c + hole))
        keepq &= ~inside.ravel()

    # ---- the corridor hole: the road programme owns everything inside it ------
    ncut = 0
    if cut_corridor:
        F = M["f"]
        if F.min() < 0.0:
            bad = F < 0.0
            qb = bad[Q].any(axis=1)
            keepq &= ~qb
            ncut = int(qb.sum())
            # snap the surviving rim vertices onto f = 0 so the cut edge is the
            # rim and not a sawtooth of whole cells
            Fg = F.reshape(n + 1, n + 1)
            gfx, gfy = np.gradient(Fg, cell, cell)
            g2 = (gfx * gfx + gfy * gfy).ravel() + 1e-9
            touch = np.zeros((n + 1) * (n + 1), bool)
            touch[Q[qb].ravel()] = True
            mv = touch & ~bad & (F < 2.5 * cell)
            if mv.any():
                X[mv] = X[mv] - F[mv] * gfx.ravel()[mv] / g2[mv]
                Y[mv] = Y[mv] - F[mv] * gfy.ravel()[mv] / g2[mv]
                Mm = macro_at(X[mv], Y[mv], 0.0)
                Z[mv] = Mm["z"] + micro_relief(X[mv], Y[mv], cell, Mm)

    Q = Q[keepq]
    used = np.zeros((n + 1) * (n + 1), bool)
    used[Q.ravel()] = True
    remap = np.full((n + 1) * (n + 1), -1, np.int64)
    remap[used] = np.arange(int(used.sum()))
    Q = remap[Q]

    z0 = float(np.median(Z[used]))
    V = np.stack([X[used] - cx, Y[used] - cy, Z[used] - z0], axis=1)
    name = "%sGround_L%d" % (PFX, k)
    me = _new_mesh(name, V, quads=Q)
    _bake_attrs(me, {kk: (v[used] if v.ndim == 1 else v[used, :]) for kk, v in attrs.items()})
    me.materials.append(mat)
    me.shade_smooth()
    ob = bpy.data.objects.new(name, me)
    ob.location = (cx, cy, z0)          # RECENTRED ON EMIT.  Object coords stay
    _link(ob, coll)                     # inside +-E, never |P| ~ 1000 m.
    log("  %s: cell %6.4f m  E %8.2f m  %7d quads  %6d cut  (%.1f s)"
        % (name, cell, E, len(Q), ncut, time.time() - t0))
    if stats is not None:
        stats["quads"] += len(Q)
        stats["verts"] += int(used.sum())
    return ob


# ================================================================================
#  8.  DISCRETE GEOMETRY — every piece generated individually
# ================================================================================
#
# "i dont want repeat stuff aka one tree spammed 100 times".  Nothing below is
# instanced.  Each stone gets its own random half-space set, each cast its own
# helix, each stem its own spline: the meshes are unique, not one mesh rotated.

def _icosphere(sub=2):
    """Unit icosphere directions + triangles, built here so nothing is loaded."""
    t = (1.0 + 5.0 ** 0.5) / 2.0
    V = np.array([[-1, t, 0], [1, t, 0], [-1, -t, 0], [1, -t, 0],
                  [0, -1, t], [0, 1, t], [0, -1, -t], [0, 1, -t],
                  [t, 0, -1], [t, 0, 1], [-t, 0, -1], [-t, 0, 1]], float)
    V /= np.linalg.norm(V, axis=1)[:, None]
    F = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11),
         (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
         (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9),
         (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)]
    for _ in range(sub):
        mid = {}
        NF = []
        Vl = list(V)

        def m(a, b):
            k = (min(a, b), max(a, b))
            if k not in mid:
                p = Vl[a] + Vl[b]
                p = p / np.linalg.norm(p)
                Vl.append(p)
                mid[k] = len(Vl) - 1
            return mid[k]

        for (a, b, c) in F:
            ab, bc, ca = m(a, b), m(b, c), m(c, a)
            NF += [(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)]
        V = np.array(Vl)
        F = NF
    return V, np.array(F, np.int64)


_ICO = None


def _ico(sub=2):
    global _ICO
    if _ICO is None or _ICO[0] != sub:
        _ICO = (sub,) + _icosphere(sub)
    return _ICO[1], _ICO[2]


class Acc(object):
    """Vertex / triangle accumulator with per-vertex shader attributes."""

    def __init__(self):
        self.V = []
        self.T = []
        self.A = {"pid": [], "pgrad": [], "pburied": []}
        self.n = 0

    def add(self, V, T, pid, pgrad, pburied):
        self.V.append(np.asarray(V, np.float64))
        self.T.append(np.asarray(T, np.int64) + self.n)
        k = len(V)
        self.A["pid"].append(np.full(k, pid))
        self.A["pgrad"].append(np.asarray(pgrad, np.float64))
        self.A["pburied"].append(np.asarray(pburied, np.float64) if np.ndim(pburied)
                                 else np.full(k, pburied))
        self.n += k

    def emit(self, name, mat, coll, centre, smooth=True):
        if not self.V:
            return None
        V = np.concatenate(self.V)
        T = np.concatenate(self.T)
        cx, cy, cz = centre
        V = V - np.array([cx, cy, cz])
        me = _new_mesh(name, V, tris=T)
        for key, arr in self.A.items():
            d = np.concatenate(arr).astype(np.float32)
            a = me.attributes.new(key, "FLOAT", "POINT")
            a.data.foreach_set("value", np.ascontiguousarray(d))
        me.materials.append(mat)
        # A FLINT CHIP IS FACETED.  Smooth-shading a random convex polytope
        # averages its arrises away and every stone renders as a potato -- which
        # is exactly what the third macro render showed.  Solids stay flat; only
        # the extruded things (casts, stems) are smooth.
        if smooth:
            me.shade_smooth()
        else:
            me.shade_flat()
        ob = bpy.data.objects.new(name, me)
        ob.location = (cx, cy, cz)
        _link(ob, coll)
        return ob


def gen_stones(rng, P, N, radii, kinds):
    """N UNIQUE stones.  Each is its own random convex polytope, then roughened.

    r(d) = min_j h_j / (d . n_j)  over 7-15 random half-spaces gives a genuinely
    angular chip with flat faces and sharp arrises — which is what flint breaks
    into, and what a displaced sphere never looks like.  The rounded fraction
    gets many more, weaker planes so it comes out water-worn instead.
    """
    D, F = _ico(2)
    nv = len(D)
    out = Acc()
    for i in range(N):
        kind = kinds[i]
        if kind == 0:        # flint / chert chip: few planes, sharp
            npl, hlo, hhi, rough = rng.integers(6, 10), 0.58, 1.0, 0.030
        elif kind == 1:      # water-worn pebble: many weak planes
            npl, hlo, hhi, rough = rng.integers(16, 24), 0.86, 1.0, 0.030
        else:                # platy flake
            npl, hlo, hhi, rough = rng.integers(5, 8), 0.50, 1.0, 0.028
        nrm = rng.normal(size=(npl, 3))
        nrm /= np.linalg.norm(nrm, axis=1)[:, None]
        h = rng.uniform(hlo, hhi, npl)
        # A RANDOM HALF-SPACE SET DOES NOT BOUND A SOLID.  With 7-11 random
        # planes there are always directions no plane supports, and r = h/(d~0)
        # then runs to 1000x -- which is exactly what happened: a 30 mm grit
        # chip came out 12 m across, swallowed the macro camera and rendered a
        # black frame that every check upstream of the picture had passed.
        # Six jittered axis planes make the intersection provably bounded, and
        # the clip is a second belt for the degenerate case.
        cap = np.array([[1., 0, 0], [-1., 0, 0], [0, 1., 0],
                        [0, -1., 0], [0, 0, 1.], [0, 0, -1.]])
        nrm = np.concatenate([nrm, cap])
        h = np.concatenate([h, rng.uniform(0.92, 1.30, 6)])
        d = np.maximum(D @ nrm.T, 1e-3)
        r = np.clip(np.min(h[None, :] / d, axis=1), 0.10, 2.40)
        # surface roughness: three random cosine lobes, so no two stones share a face
        for _ in range(3):
            k = rng.normal(size=3)
            k /= np.linalg.norm(k)
            r *= 1.0 + rough * np.cos((D @ k) * rng.uniform(6.0, 18.0) + rng.uniform(0, 6.3))
        # normalise to a MEAN radius of 1 so `radii[i]` is the size the stone
        # actually comes out, whatever plane set it happened to draw.  Without
        # this the size distribution is a property of the random planes rather
        # than of the sieve fraction being modelled.
        r = r / float(r.mean())
        S = np.array([1.0, rng.uniform(0.62, 1.0), rng.uniform(0.42, 0.92)])
        if kind == 2:
            S[2] *= rng.uniform(0.30, 0.55)
        V = D * r[:, None] * S[None, :] * radii[i]
        # a stone lies on its flattest face: spin it so the short axis is up
        ang = rng.uniform(0, 2 * math.pi)
        ca, sa = math.cos(ang), math.sin(ang)
        R = np.array([[ca, -sa, 0.0], [sa, ca, 0.0], [0.0, 0.0, 1.0]])
        tilt = rng.uniform(-0.35, 0.35, 2)
        Rt = np.array([[1, 0, tilt[0]], [0, 1, tilt[1]], [-tilt[0], -tilt[1], 1.0]])
        V = V @ R.T @ Rt.T
        V += P[i]
        grad = np.clip((V[:, 2] - V[:, 2].min()) / max(1e-6, float(np.ptp(V[:, 2]))), 0, 1)
        out.add(V, F, float(rng.random()), grad, 0.0)
    return out


def gen_casts(rng, P, N, sizes):
    """Worm casts: real extruded coils.  Not a bump, not a decal."""
    out = Acc()
    sides = 9
    ring = np.arange(sides) * (2 * math.pi / sides)
    for i in range(N):
        # TIGHT, not stacked.  The first version used 1.6-3.4 turns rising to
        # 1.15x its own width, which renders as a little cairn of separate rings;
        # a real cast is 1-2 turns of a soft extrusion that slumps into itself,
        # so the tube is fat relative to the coil and the rise is shallow.
        turns = rng.uniform(1.05, 2.05)
        nseg = int(16 + turns * 9)
        t = np.linspace(0.0, turns * 2 * math.pi, nseg)
        R0 = sizes[i] * rng.uniform(0.34, 0.46)
        rad = R0 * (1.0 - 0.30 * t / t[-1]) * (1.0 + 0.16 * np.sin(t * 2.7))
        h = sizes[i] * rng.uniform(0.30, 0.62) * (t / t[-1]) ** 0.80
        cxs = rad * np.cos(t + rng.uniform(0, 6.3))
        cys = rad * np.sin(t + rng.uniform(0, 6.3))
        tube = sizes[i] * rng.uniform(0.19, 0.27) * (1.0 - 0.28 * (t / t[-1]))
        Cn = np.stack([cxs, cys, h], axis=1)
        d = np.gradient(Cn, axis=0)
        d /= np.linalg.norm(d, axis=1)[:, None] + 1e-9
        up = np.array([0.0, 0.0, 1.0])
        s1 = np.cross(d, up)
        s1 /= np.linalg.norm(s1, axis=1)[:, None] + 1e-9
        s2 = np.cross(d, s1)
        V = (Cn[:, None, :]
             + tube[:, None, None] * (np.cos(ring)[None, :, None] * s1[:, None, :]
                                      + np.sin(ring)[None, :, None] * s2[:, None, :]))
        V = V.reshape(-1, 3) + P[i]
        T = []
        for a in range(nseg - 1):
            for b in range(sides):
                b2 = (b + 1) % sides
                i0 = a * sides + b
                i1 = a * sides + b2
                i2 = (a + 1) * sides + b
                i3 = (a + 1) * sides + b2
                T += [(i0, i2, i3), (i0, i3, i1)]
        grad = np.repeat(t / t[-1], sides)
        out.add(V, np.array(T, np.int64), float(rng.random()), grad, 0.0)
    return out


def gen_thatch(rng, P, N, Nrm, lengths):
    """Dead grass stems lying on the mat.  Ribbons, 1.8 mm wide, 8 segments.

    Thatch is why a mown verge is not a green plane: the litter layer under the
    sward is straw-coloured, it catches a 12.5 deg sun edge-on and it throws the
    tiny shadows that make soil read as soil.  It is also the finest geometry in
    this item at 1.4 mm cross-edges.
    """
    out = Acc()
    seg = 8
    for i in range(N):
        L = lengths[i]
        th = rng.uniform(0, 2 * math.pi)
        curve = rng.uniform(-1.7, 1.7)
        t = np.linspace(0.0, 1.0, seg + 1)
        ang = th + curve * t
        dx = np.concatenate([[0.0], np.cumsum(np.cos(ang[:-1]) * (L / seg))])
        dy = np.concatenate([[0.0], np.cumsum(np.sin(ang[:-1]) * (L / seg))])
        arch = rng.uniform(0.0, 0.11) * L * np.sin(math.pi * t) ** 1.4
        # a dead fescue stem is under 2 mm.  The first pass drew them at 3.6 mm
        # and 165 mm long and the macro came back covered in pale noodles.
        w = rng.uniform(0.00075, 0.00170) * (1.0 - 0.35 * t)
        nx = -np.sin(ang)
        ny = np.cos(ang)
        V = np.empty(((seg + 1) * 2, 3))
        V[0::2, 0] = dx + nx * w
        V[0::2, 1] = dy + ny * w
        V[1::2, 0] = dx - nx * w
        V[1::2, 1] = dy - ny * w
        V[0::2, 2] = arch
        V[1::2, 2] = arch
        # lay it on the local surface plane
        n = Nrm[i]
        V[:, 2] += -(n[0] * V[:, 0] + n[1] * V[:, 1]) / max(n[2], 0.35)
        V += P[i]
        T = []
        for a in range(seg):
            i0 = a * 2
            T += [(i0, i0 + 1, i0 + 3), (i0, i0 + 3, i0 + 2)]
        grad = np.repeat(t, 2)
        out.add(V, np.array(T, np.int64), float(rng.random()), grad, 0.0)
    return out


def gen_stubble(rng, P, N, Nrm, heights):
    """The mown mat: sheared stem butts, 15-40 mm, standing.

    WHERE THIS ITEM STOPS AND grass_clump_* STARTS, stated so the four grass
    agents do not build it twice: terrain_ground owns the CUT STUBBLE -- the
    15-40 mm sheared butts the mower leaves, which are part of the ground and
    are why mown turf reads as mown.  grass_clump_fescue / _dry / _meadow /
    _tussock own the TUFTS: 60-180 mm living blades scattered ON this surface
    with `terrain_ground.surface_z` / `surface_normal`.  Do not re-create the
    stubble; do not expect this module to supply blades.

    Each butt is a 3-segment tapered ribbon with a square chopped tip, because
    that is what a rotary mower leaves and the bleached cut end is the single
    most recognisable thing about mown grass at 1 555 px/m.
    """
    out = Acc()
    seg = 4
    for i in range(N):
        H = heights[i]
        az = rng.uniform(0, 2 * math.pi)
        # a third of the sward has gone over: senesced butts lie almost flat
        lean = (rng.uniform(0.95, 1.45) if rng.random() < 0.33
                else rng.uniform(0.0, 0.95))
        bend = rng.uniform(-0.4, 1.5)
        t = np.linspace(0.0, 1.0, seg + 1)
        ang = lean + bend * t * t
        dx = np.cumsum(np.concatenate([[0.0], np.sin(ang[:-1]) * (H / seg)])) * math.cos(az)
        dy = np.cumsum(np.concatenate([[0.0], np.sin(ang[:-1]) * (H / seg)])) * math.sin(az)
        dzv = np.cumsum(np.concatenate([[0.0], np.cos(ang[:-1]) * (H / seg)]))
        # taper hard to the tip: a rectangular silhouette reads as a plank, and
        # at 1 555 px/m a 2 mm plank is 3 px of obviously-wrong
        w = rng.uniform(0.0011, 0.0022) * (1.0 - 0.72 * t ** 1.5)
        nx, ny = -math.sin(az), math.cos(az)
        V = np.empty(((seg + 1) * 2, 3))
        V[0::2, 0] = dx + nx * w
        V[0::2, 1] = dy + ny * w
        V[1::2, 0] = dx - nx * w
        V[1::2, 1] = dy - ny * w
        V[0::2, 2] = dzv
        V[1::2, 2] = dzv
        n = Nrm[i]
        V[:, 2] += -(n[0] * V[:, 0] + n[1] * V[:, 1]) / max(n[2], 0.35)
        V += P[i]
        T = []
        for a in range(seg):
            i0 = a * 2
            T += [(i0, i0 + 1, i0 + 3), (i0, i0 + 3, i0 + 2)]
        out.add(V, np.array(T, np.int64), float(rng.random()), np.repeat(t, 2), 0.0)
    return out


def build_detail(centre, coll, rng, mats, quality=1.0, stats=None):
    """Grit, clods, casts and thatch across the hero tile."""
    cell, n = RINGS[0]
    # THE DETAIL TILE IS THE FRAMED AREA, NOT THE HERO RING.  The 2.5 mm ring is
    # +-1.50 m, but a 35 mm lens 2.400 m out on a 31 deg downtilt frames ground
    # to 4.85 m of its own nadir -- so scattering only inside the hero ring put
    # a hard line across the top third of the macro where every stone, stem and
    # cast stopped at once.  The scatter runs to the SECOND ring's extent and
    # its density falls with distance instead, which is a taper rather than an
    # edge.
    E = RINGS[1][0] * RINGS[1][1] * 0.5 if len(RINGS) > 1 else cell * n * 0.5
    E0 = cell * n * 0.5
    cx, cy = centre
    t0 = time.time()

    # sample the surface on a dense jittered lattice and keep points by mask
    step = 0.015
    m = int(2 * E / step)
    gx = cx - E + (np.arange(m) + 0.5) * step
    gy = cy - E + (np.arange(m) + 0.5) * step
    GX, GY = np.meshgrid(gx, gy, indexing="ij")
    PX = (GX + (rng.random(GX.shape) - 0.5) * step).ravel()
    PY = (GY + (rng.random(GY.shape) - 0.5) * step).ravel()
    M = macro_at(PX, PY, 0.20)
    dz, ex = micro_relief(PX, PY, cell, M, want_extra=True)
    PZ = M["z"] + dz
    slope = _slope_by_difference(PX, PY, SLOPE_SCALE_M, cell, 0.20)
    A = _attributes(PX, PY, PZ, M, ex, slope)
    R = rng.random(len(PX))
    # radial taper: full density inside the hero ring, 32 % at the outer edge
    rad = np.maximum(np.abs(PX - cx), np.abs(PY - cy))
    taper = 1.0 - 0.68 * smoothstep(E0 * 0.85, E, rad)

    def pick(prob, cap):
        take = np.where(R < np.clip(np.asarray(prob) * taper, 0, 1))[0]
        if len(take) > cap:
            take = rng.choice(take, cap, replace=False)
        return take

    made = {}

    # -- GRIT ------------------------------------------------------------------
    p = (0.055 * A["ter_grit"] + 0.030 * A["ter_rut"] + 0.010 * A["ter_bare"]) * quality
    idx = pick(p, int(4200 * quality))
    if len(idx):
        radii = np.exp(rng.uniform(math.log(0.0018), math.log(0.026), len(idx)) ** 1.0)
        radii = radii * rng.choice([1.0, 1.0, 1.0, 0.55], len(idx))
        kinds = rng.choice([0, 1, 2], len(idx), p=[0.56, 0.31, 0.13])
        bury = rng.uniform(0.22, 0.78, len(idx))
        P = np.stack([PX[idx], PY[idx], PZ[idx] + radii * (0.5 - bury)], axis=1)
        acc = gen_stones(rng, P, len(idx), radii, kinds)
        made["grit"] = acc.emit(PFX + "Grit", mats["stone"], coll,
                                (cx, cy, float(np.median(PZ))), smooth=False)
        log("  grit: %d unique stones, %.1f-%.1f mm" % (len(idx), radii.min() * 1e3, radii.max() * 1e3))

    # -- CLODS -----------------------------------------------------------------
    p = (0.017 * A["ter_bare"] * (1.0 - A["ter_wet"]) + 0.014 * A["ter_rut"]) * quality
    idx = pick(p, int(1500 * quality))
    if len(idx):
        radii = np.exp(rng.uniform(math.log(0.006), math.log(0.028), len(idx)))
        kinds = np.zeros(len(idx), int)
        P = np.stack([PX[idx], PY[idx], PZ[idx] + radii * rng.uniform(-0.35, 0.10, len(idx))], axis=1)
        acc = gen_stones(rng, P, len(idx), radii, kinds)
        made["clod"] = acc.emit(PFX + "Clod", mats["clod"], coll,
                                (cx, cy, float(np.median(PZ))), smooth=False)
        log("  clods: %d" % len(idx))

    # -- WORM CASTS ------------------------------------------------------------
    p = (0.014 * (1.0 - A["ter_bare"]) * (1.0 - A["ter_rut"])
         * (0.40 + 0.60 * A["ter_wet"])) * quality
    idx = pick(p, int(1100 * quality))
    if len(idx):
        sizes = rng.uniform(0.016, 0.034, len(idx))
        P = np.stack([PX[idx], PY[idx], PZ[idx] - 0.004], axis=1)
        acc = gen_casts(rng, P, len(idx), sizes)
        made["cast"] = acc.emit(PFX + "Cast", mats["cast"], coll, (cx, cy, float(np.median(PZ))))
        log("  worm casts: %d" % len(idx))

    # -- THATCH ----------------------------------------------------------------
    # the litter mat is DENSE.  Keying it to ter_thatch alone left the turf bare
    # of it and the sward rendered as paint; it is keyed to cover as well now.
    p = (0.26 * A["ter_thatch"] + 0.012) * quality
    idx = pick(p, int(14000 * quality))
    if len(idx):
        lengths = rng.uniform(0.018, 0.068, len(idx))
        P = np.stack([PX[idx], PY[idx], PZ[idx] + 0.0016], axis=1)
        Nrm = surface_normal(PX[idx], PY[idx], eps=0.010)
        acc = gen_thatch(rng, P, len(idx), Nrm, lengths)
        made["thatch"] = acc.emit(PFX + "Thatch", mats["thatch"], coll,
                                  (cx, cy, float(np.median(PZ))))
        log("  thatch: %d stems" % len(idx))

    # -- STUBBLE ---------------------------------------------------------------
    clump = 0.30 + 1.45 * (0.5 + 0.5 * fbm(PX / 0.21, PY / 0.21, 3, seed=4409))
    p = (1.45 * A["ter_cover"] * (1.0 - A["ter_bare"]) * (0.35 + 0.65 * A["ter_mown"])
         * clump) * quality
    idx = pick(p, int(60000 * quality))
    if len(idx):
        heights = rng.uniform(0.008, 0.026, len(idx))
        Pp = np.stack([PX[idx], PY[idx], PZ[idx] - 0.003], axis=1)
        Nrm = surface_normal(PX[idx], PY[idx], eps=0.010)
        acc = gen_stubble(rng, Pp, len(idx), Nrm, heights)
        made["stubble"] = acc.emit(PFX + "Stubble", mats["stubble"], coll,
                                   (cx, cy, float(np.median(PZ))))
        log("  stubble: %d cut butts, %.0f-%.0f mm"
            % (len(idx), heights.min() * 1e3, heights.max() * 1e3))

    # MEASURE that the detail sits ON the ground instead of asserting it.  A
    # floating stone is invisible in a build log and fatal in a frame.
    for key, ob in made.items():
        if ob is None:
            continue
        co = np.empty(len(ob.data.vertices) * 3)
        ob.data.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3) + np.array(ob.location)
        gz = surface_z(co[:, 0], co[:, 1])
        dz = co[:, 2] - gz
        if dz.max() > 0.20 or dz.min() < -0.20:
            raise SystemExit(
                "REFUSING: %s has geometry %.3f..%.3f m off the ground surface. "
                "Detail that does not sit on the ground is a defect, not a "
                "tolerance." % (ob.name, dz.min(), dz.max()))
        log("  %-7s stands %+.4f .. %+.4f m off the surface (%d verts)"
            % (key, dz.min(), dz.max(), len(co)))
        if stats is not None:
            stats["verts"] += len(co)
    log("  detail built (%.1f s)" % (time.time() - t0))
    return made


# ================================================================================
#  9.  MATERIALS  —  procedural, TexCoord -> Object, calibrated
# ================================================================================

class NT(object):
    """Small node-graph DSL, same shape as build_terrain's so the two read alike."""

    def __init__(self, name):
        m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
        m.use_nodes = True
        self.m = m
        self.t = m.node_tree
        self.t.nodes.clear()
        self.x = 0
        self.row = 0

    def n(self, typ, **kw):
        nd = self.t.nodes.new(typ)
        self.x += 190
        nd.location = (self.x, self.row * -260)
        for k, v in kw.items():
            if hasattr(nd, k):
                setattr(nd, k, v)
        return nd

    def link(self, a, ai, b, bi):
        self.t.links.new(a.outputs[ai], b.inputs[bi])

    def set(self, nd, key, val):
        nd.inputs[key].default_value = val

    def pin(self, nd, idx, src):
        """Feed a node input from a (node, socket) pair, a bare node, or a value.

        Every helper below routes through this.  Half of a shader graph this size
        is plumbing, and a DSL that only accepts one of the three forms turns
        every nested expression into a temporary variable.
        """
        if src is None:
            return
        if isinstance(src, tuple) and hasattr(src[0], "outputs"):
            self.link(src[0], src[1], nd, idx)
        elif hasattr(src, "outputs"):
            self.link(src, 0, nd, idx)
        elif isinstance(src, (tuple, list)):
            nd.inputs[idx].default_value = (*src, 1.0) if len(src) == 3 else tuple(src)
        else:
            nd.inputs[idx].default_value = float(src)

    def mix(self, fac, a, b, blend="MIX"):
        nd = self.n("ShaderNodeMix", data_type="RGBA", blend_type=blend)
        self.pin(nd, 0, fac)
        self.pin(nd, 6, a)
        self.pin(nd, 7, b)
        return nd

    def fmix(self, fac, a, b):
        nd = self.n("ShaderNodeMix", data_type="FLOAT")
        self.pin(nd, 0, fac)
        self.pin(nd, 2, a)
        self.pin(nd, 3, b)
        return nd

    def noise(self, scale, detail=10.0, rough=0.58, vec=None, dist=0.0, lac=2.0):
        nd = self.n("ShaderNodeTexNoise")
        self.set(nd, "Scale", scale)
        self.set(nd, "Detail", detail)
        self.set(nd, "Roughness", rough)
        self.set(nd, "Distortion", dist)
        if "Lacunarity" in nd.inputs:
            self.set(nd, "Lacunarity", lac)
        if vec is not None:
            self.link(vec[0], vec[1], nd, 0)
        return nd

    def vor(self, scale, feature="F1", vec=None, rand=1.0):
        nd = self.n("ShaderNodeTexVoronoi", feature=feature)
        self.set(nd, "Scale", scale)
        self.set(nd, "Randomness", rand)
        if vec is not None:
            self.link(vec[0], vec[1], nd, 0)
        return nd

    def ramp(self, src, stops):
        nd = self.n("ShaderNodeValToRGB")
        self.link(src[0], src[1], nd, 0)
        el = nd.color_ramp.elements
        while len(el) > 1:
            el.remove(el[-1])
        el[0].position = stops[0][0]
        el[0].color = (*stops[0][1], 1.0)
        for p, c in stops[1:]:
            e = el.new(p)
            e.color = (*c, 1.0)
        return nd

    def math(self, op, a=None, b=None, clamp=False):
        nd = self.n("ShaderNodeMath", operation=op, use_clamp=clamp)
        self.pin(nd, 0, a)
        self.pin(nd, 1, b)
        return nd

    def attr(self, name):
        nd = self.n("ShaderNodeAttribute", attribute_type="GEOMETRY")
        nd.attribute_name = name
        return nd

    def bump(self, height, strength, distance, normal=None):
        nd = self.n("ShaderNodeBump")
        self.set(nd, "Distance", distance)
        self.pin(nd, "Strength", strength)
        self.pin(nd, "Height", height)
        if normal is not None:
            self.pin(nd, "Normal", normal)
        return nd

    def out(self, shader, si=0, disp=None):
        o = self.n("ShaderNodeOutputMaterial")
        self.link(shader, si, o, "Surface")
        if disp is not None:
            self.link(disp[0], disp[1], o, "Displacement")
        return o


P = PALETTE


def mat_ground():
    """The ground.  Eleven colour layers and four bump scales, all from masks
    that the MESH was actually cut from — the crack the shader darkens is the
    crack that is in the geometry, because both read `ter_rock`/`ter_bare`.

    Nothing here is a flat colour and nothing here is an image.
    """
    t = NT(PFX + "Ground")
    co = t.n("ShaderNodeTexCoord")
    geo = t.n("ShaderNodeNewGeometry")

    a_wet = t.attr("ter_wet")
    a_wear = t.attr("ter_wear")
    a_cov = t.attr("ter_cover")
    a_mown = t.attr("ter_mown")
    a_dry = t.attr("ter_dry")
    a_fld = t.attr("ter_field")
    a_moss = t.attr("ter_moss")
    a_scuff = t.attr("ter_scuff")
    a_bare = t.attr("ter_bare")
    a_grit = t.attr("ter_grit")
    a_thatch = t.attr("ter_thatch")
    a_rut = t.attr("ter_rut")
    a_silt = t.attr("ter_silt")
    a_org = t.attr("ter_organic")
    a_rock = t.attr("ter_rock")

    # slope from the true shading normal (the manifest's KNOWN LIMIT: slope is
    # read at render time, not baked, because the baked one is per-ring)
    sep = t.n("ShaderNodeSeparateXYZ")
    t.link(geo, "Normal", sep, 0)
    # STEEP MEANS STEEP GROUND, NOT A BUMPED NORMAL.  At a 2.5 mm mesh plus four
    # bump layers the shading normal leaves vertical constantly, so the first
    # ramp (0.55 -> 0.93) fired almost everywhere and mixed 60 % pale subsoil
    # over the entire frame.  That, plus an organic term that read clay_pale at
    # 70 %, is why the first macro render came back looking like a dry lake bed.
    steep = t.ramp((sep, 2), [(0.62, (1, 1, 1)), (0.84, (0, 0, 0))])

    # --- six object-space scales.  0.9 mm to 2.2 m. -------------------------
    n_micro = t.noise(1100.0, 12.0, 0.62, vec=(co, "Object"), dist=0.30)   # 0.9 mm
    n_grain = t.noise(330.0, 12.0, 0.60, vec=(co, "Object"), dist=0.55)    # 3 mm
    n_fine = t.noise(90.0, 12.0, 0.58, vec=(co, "Object"), dist=0.45)      # 11 mm
    n_clod = t.noise(18.0, 11.0, 0.60, vec=(co, "Object"), dist=0.60)      # 5.5 cm
    n_patch = t.noise(4.4, 9.0, 0.56, vec=(co, "Object"))                  # 23 cm
    n_broad = t.noise(0.85, 7.0, 0.55, vec=(co, "Object"))                 # 1.2 m

    # crumb: soil aggregate as CELLS, and its edges, which is where the dark is
    v_crumb = t.vor(72.0, "F1", vec=(co, "Object"))
    v_edge = t.vor(72.0, "DISTANCE_TO_EDGE", vec=(co, "Object"))
    v_grit = t.vor(24.0, "F1", vec=(co, "Object"))
    v_gritid = t.vor(24.0, "SMOOTH_F1", vec=(co, "Object"))

    # --- soil column: subsoil -> topsoil -> dry crust ------------------------
    wetness = t.math("MULTIPLY", (a_wet, 2), 1.0, clamp=True)
    soil_a = t.mix((n_clod, 0), P["topsoil"], P["soil_dry"])
    soil_b = t.mix((n_fine, 0), (soil_a, 2), P["soil_moist"])
    # humus darkens; only genuinely SCRAPED ground shows pale subsoil, and that
    # is a small part of a verge
    pale_m = t.ramp((a_org, 2), [(0.0, (1, 1, 1)), (0.30, (0, 0, 0))])
    soil_c = t.mix((t.math("MULTIPLY", (pale_m, 0), 0.70), 0), (soil_b, 2), P["clay_pale"])
    soil_d = t.mix((wetness, 0), (soil_c, 2), P["soil_damp"])
    # the crust: the top 2 mm dries pale and it is the thing a raking sun sees
    crust_m = t.math("MULTIPLY", (t.math("SUBTRACT", 1.0, (a_wet, 2)), 0),
                     (t.ramp((n_grain, 0), [(0.42, (0, 0, 0)), (0.78, (1, 1, 1))]), 0))
    soil = t.mix((t.math("MULTIPLY", (crust_m, 0), 0.30), 0), (soil_d, 2), P["crust"])

    # --- the crumb edges: every aggregate has a dark rim ----------------------
    crumb_dark = t.ramp((v_edge, 0), [(0.0, (0.30, 0.30, 0.30)), (0.10, (1, 1, 1))])
    soil2 = t.mix((t.math("MULTIPLY", (a_bare, 2), 0.85), 0), (soil, 2),
                  (t.mix((crumb_dark, 0), P["soil_damp"], (soil, 2)), 2))

    # --- sward, thatch, moss --------------------------------------------------
    # THE SWARD IS NOT ONE GREEN.  The first render's turf read as billiard
    # cloth because it was: two greens crossfaded by a 1.2 m noise, so a 3 m
    # frame saw one flat colour.  Real mown turf at 1 555 px/m is a mosaic at
    # tiller scale -- green crowns, straw between them, moss in the damp, and
    # last year's litter showing through wherever the mower scalped it.
    v_till = t.vor(38.0, "F1", vec=(co, "Object"))          # 26 mm tillers
    v_tillid = t.vor(38.0, "SMOOTH_F1", vec=(co, "Object"))
    past = t.mix((n_broad, 0), P["turf"], P["turf_pale"])
    past_t = t.mix((v_tillid, 1), (past, 2), P["turf_pale"])   # per-tiller value
    past_m = t.mix((t.math("MULTIPLY", (n_fine, 0), 0.42), 0), (past_t, 2), P["moss"])
    past2 = t.mix((a_dry, 2), (past_m, 2), P["thatch"])
    fld = t.mix(0.45, (past2, 2), (a_fld, 0))
    turf = t.mix((a_mown, 2), (fld, 2), (past_m, 2))
    # straw in the gaps between the crowns -- the mat you see looking straight
    # down into a sward, and the thing that stops it being a colour
    gap = t.ramp((v_till, 0), [(0.010, (0, 0, 0)), (0.026, (1, 1, 1))])
    thatch_c = t.mix((n_patch, 0), P["thatch"], P["thatch_old"])
    turf1 = t.mix((t.math("MULTIPLY", (gap, 0), 0.34), 0), (turf, 2), (thatch_c, 2))
    turf2 = t.mix((t.math("MULTIPLY", (a_thatch, 2), 0.46), 0), (turf1, 2), (thatch_c, 2))
    # scalped crowns: where the mower caught a hummock it took the green off
    scalp = t.ramp((n_clod, 0), [(0.62, (0, 0, 0)), (0.80, (1, 1, 1))])
    turf2 = t.mix((t.math("MULTIPLY", (scalp, 0), 0.24), 0), (turf2, 2), P["thatch_old"])

    # The turf/soil boundary is a broken EDGE, not a fade -- the mat tears.  The
    # ramp sharpens it and the 11 mm noise breaks it up so it is not a contour.
    bare_e = t.math("ADD", (a_bare, 2), t.math("MULTIPLY", (n_fine, 0), 0.28))
    bare_s = t.ramp((bare_e, 0), [(0.30, (0, 0, 0)), (0.66, (1, 1, 1))])
    ground = t.mix((bare_s, 0), (turf2, 2), (soil2, 2))
    # a root-mat rim of dead straw right where the sward is broken
    rim_m = t.ramp((bare_e, 0), [(0.30, (0, 0, 0)), (0.48, (1, 1, 1)), (0.66, (0, 0, 0))])
    ground = t.mix((t.math("MULTIPLY", (rim_m, 0), 0.55), 0), (ground, 2), P["thatch_old"])
    ground = t.mix((t.math("MULTIPLY", (a_moss, 2), 1.0), 0), (ground, 2), P["moss"])

    # --- grit lying on it, as cells so it is stones and not a tint ------------
    grit_col = t.mix((v_gritid, 1), P["flint_dark"], P["limestone"])
    grit_col2 = t.mix((n_fine, 0), (grit_col, 2), P["sandstone"])
    grit_m = t.math("MULTIPLY", (a_grit, 2),
                    (t.ramp((v_grit, 0), [(0.055, (1, 1, 1)), (0.130, (0, 0, 0))]), 0))
    ground = t.mix((t.math("MULTIPLY", (grit_m, 0), 0.80), 0), (ground, 2), (grit_col2, 2))

    # --- the rut: compacted, polished by a tyre, dusty on the crown ----------
    rut_col = t.mix((n_grain, 0), P["soil_wet"], P["soil_damp"])
    ground = t.mix((t.math("MULTIPLY", (a_rut, 2), 0.82), 0), (ground, 2), (rut_col, 2))
    dust_m = t.math("MULTIPLY", (t.math("SUBTRACT", 1.0, (a_wet, 2)), 0),
                    (t.math("MULTIPLY", (a_rut, 2), 0.30), 0))
    ground = t.mix((dust_m, 0), (ground, 2), P["dust"])

    # --- silt film and its algae, where water stands -------------------------
    silt_col = t.mix((n_patch, 0), P["soil_wet"], P["algae"])
    ground = t.mix((t.math("MULTIPLY", (a_silt, 2), 0.85), 0), (ground, 2), (silt_col, 2))

    # --- run-wide rubber, exposed subsoil on steep ground --------------------
    ground = t.mix((t.math("MULTIPLY", (a_scuff, 2), 0.75), 0), (ground, 2), P["rubber"])
    ground = t.mix((t.math("MULTIPLY", (steep, 0), 0.28), 0), (ground, 2), P["clay_pale"])
    # cracks read as a dark line: they are 14 mm deep, so they are in shadow
    crk = t.math("MULTIPLY", (a_rock, 2), (t.ramp((v_edge, 0),
                                                  [(0.0, (1, 1, 1)), (0.055, (0, 0, 0))]), 0))
    ground = t.mix((t.math("MULTIPLY", (crk, 0), 0.55), 0), (ground, 2), P["soil_wet"])

    # --- four bump scales, all BELOW the 2.5 mm mesh --------------------------
    b1 = t.bump((n_micro, 0), 0.85, 0.0016)
    b2 = t.bump((v_edge, 0), t.math("ADD", t.math("MULTIPLY", (a_bare, 2), 0.85), 0.35),
                0.0030, normal=(b1, 0))
    b3 = t.bump((n_grain, 0), 1.00, 0.0075, normal=(b2, 0))
    b4 = t.bump((n_fine, 0), t.math("MULTIPLY", (a_bare, 2), 0.60), 0.006, normal=(b3, 0))
    # ... and the turf gets its own, or the sward is smooth wherever it is green
    b5 = t.bump((v_till, 0),
                t.math("MULTIPLY", (a_cov, 2), t.math("SUBTRACT", 1.0, (a_bare, 2))),
                0.0030, normal=(b4, 0))
    b6 = t.bump((gap, 0), t.math("MULTIPLY", (a_thatch, 2), 0.75), 0.0018, normal=(b5, 0))

    # --- roughness: soil is matte, wet soil is not, stone is smoother ---------
    rgh = t.n("ShaderNodeMapRange")
    t.link(a_wet, 2, rgh, 0)
    t.set(rgh, "To Min", 0.965)
    t.set(rgh, "To Max", 0.520)
    rgh2 = t.fmix((grit_m, 0), (rgh, 0), 0.44)
    rgh3 = t.fmix((t.math("MULTIPLY", (a_thatch, 2), 0.7), 0), (rgh2, 0), 0.78)
    rgh3 = t.fmix((t.math("MULTIPLY", (a_cov, 2),
                          t.math("SUBTRACT", 1.0, (a_bare, 2))), 0), (rgh3, 0), 0.68)
    rgh4 = t.math("SUBTRACT", (rgh3, 0),
                  t.math("MULTIPLY", (n_micro, 0), 0.06), clamp=True)

    p = t.n("ShaderNodeBsdfPrincipled")
    t.link(ground, 2, p, "Base Color")
    t.link(b6, 0, p, "Normal")
    t.link(rgh4, 0, p, "Roughness")
    t.set(p, "Specular IOR Level", 0.24)
    # standing water in the pans gets a real coat, not a roughness cheat
    t.link(t.math("MULTIPLY", (a_silt, 2), (a_wet, 2)), 0, p, "Coat Weight")
    t.set(p, "Coat Roughness", 0.09)
    t.out(p)
    return t.m


def mat_stone():
    t = NT(PFX + "Stone")
    co = t.n("ShaderNodeTexCoord")
    pid = t.attr("pid")
    pg = t.attr("pgrad")
    n_f = t.noise(260.0, 12.0, 0.60, vec=(co, "Object"), dist=0.4)
    n_m = t.noise(46.0, 10.0, 0.58, vec=(co, "Object"))
    v_l = t.vor(90.0, "F1", vec=(co, "Object"))
    # flint / limestone / sandstone by per-stone id, then a chalk cortex on the
    # buried half and lichen on the exposed one
    # SKEWED DARK ON PURPOSE.  A uniform pid mix made half the grit limestone and
    # the macro render came back with a field of chalk pebbles; the sieve
    # fraction on this ground is mostly flint, which is near-black until its
    # cortex shows.
    base = t.mix((t.ramp((pid, 2), [(0.00, (0, 0, 0)), (0.58, (0, 0, 0)),
                                    (0.64, (1, 1, 1)), (1.0, (1, 1, 1))]), 0),
                 P["flint_dark"], P["limestone"])
    base2 = t.mix((t.ramp((pid, 2), [(0.62, (0, 0, 0)), (0.80, (1, 1, 1))]), 0),
                  (base, 2), P["sandstone"])
    cortex = t.mix((n_m, 0), P["flint_cortex"], P["crust"])
    stone = t.mix((t.math("MULTIPLY", (t.math("SUBTRACT", 1.0, (pg, 2)), 0), 0.55), 0),
                  (base2, 2), (cortex, 2))
    lich = t.ramp((v_l, 0), [(0.0, (1, 1, 1)), (0.35, (0, 0, 0))])
    stone2 = t.mix((t.math("MULTIPLY", (lich, 0),
                           t.math("MULTIPLY", (pg, 2), 0.55)), 0), (stone, 2), P["moss"])
    stone3 = t.mix((t.math("MULTIPLY", (t.math("SUBTRACT", 1.0, (pg, 2)), 0), 0.45), 0),
                   (stone2, 2), P["soil_damp"])
    b1 = t.bump((n_f, 0), 0.45, 0.0004)
    b2 = t.bump((v_l, 0), 0.35, 0.0012, normal=(b1, 0))
    p = t.n("ShaderNodeBsdfPrincipled")
    t.link(stone3, 2, p, "Base Color")
    t.link(b2, 0, p, "Normal")
    t.link(t.fmix((lich, 0), 0.55, 0.86), 0, p, "Roughness")
    t.set(p, "Specular IOR Level", 0.28)
    t.out(p)
    return t.m


def mat_clod():
    t = NT(PFX + "Clod")
    co = t.n("ShaderNodeTexCoord")
    pid = t.attr("pid")
    pg = t.attr("pgrad")
    n_f = t.noise(420.0, 12.0, 0.62, vec=(co, "Object"), dist=0.5)
    n_m = t.noise(60.0, 11.0, 0.58, vec=(co, "Object"))
    v = t.vor(150.0, "F1", vec=(co, "Object"))
    base = t.mix((pid, 2), P["soil_dry"], P["topsoil"])
    base2 = t.mix((n_m, 0), (base, 2), P["crust"])
    # damp underside, dry crust on top: a clod dries from the sun down
    body = t.mix((t.math("MULTIPLY", (t.math("SUBTRACT", 1.0, (pg, 2)), 0), 0.75), 0),
                 (base2, 2), P["soil_damp"])
    grit = t.ramp((v, 0), [(0.0, (1, 1, 1)), (0.30, (0, 0, 0))])
    body2 = t.mix((t.math("MULTIPLY", (grit, 0), 0.35), 0), (body, 2), P["sandstone"])
    b1 = t.bump((n_f, 0), 0.60, 0.0004)
    b2 = t.bump((v, 0), 0.55, 0.0009, normal=(b1, 0))
    p = t.n("ShaderNodeBsdfPrincipled")
    t.link(body2, 2, p, "Base Color")
    t.link(b2, 0, p, "Normal")
    t.set(p, "Roughness", 0.94)
    t.set(p, "Specular IOR Level", 0.16)
    t.out(p)
    return t.m


def mat_cast():
    t = NT(PFX + "Cast")
    co = t.n("ShaderNodeTexCoord")
    pid = t.attr("pid")
    pg = t.attr("pgrad")
    n_f = t.noise(700.0, 12.0, 0.62, vec=(co, "Object"), dist=0.6)
    n_m = t.noise(120.0, 10.0, 0.58, vec=(co, "Object"))
    base = t.mix((pid, 2), P["soil_wet"], P["soil_damp"])
    # the tip is the freshest and wettest; the base has dried and greyed
    body = t.mix((pg, 2), P["soil_moist"], (base, 2))
    body2 = t.mix((n_m, 0), (body, 2), P["topsoil"])
    b1 = t.bump((n_f, 0), 0.70, 0.0004)
    p = t.n("ShaderNodeBsdfPrincipled")
    t.link(body2, 2, p, "Base Color")
    t.link(b1, 0, p, "Normal")
    t.link(t.fmix((pg, 2), 0.62, 0.88), 0, p, "Roughness")
    t.set(p, "Specular IOR Level", 0.30)
    t.out(p)
    return t.m


def mat_thatch():
    t = NT(PFX + "Thatch")
    co = t.n("ShaderNodeTexCoord")
    pid = t.attr("pid")
    pg = t.attr("pgrad")
    n_f = t.noise(900.0, 12.0, 0.60, vec=(co, "Object"), dist=0.4)
    n_l = t.noise(30.0, 9.0, 0.55, vec=(co, "Object"))
    v = t.vor(400.0, "F1", vec=(co, "Object"))
    base = t.mix((t.ramp((pid, 2), [(0.0, (0, 0, 0)), (0.34, (1, 1, 1))]), 0),
                 P["thatch_old"], P["thatch"])
    # bleached at the tip, rotted at the butt: a dead stem is never one colour
    stem = t.mix((pg, 2), (base, 2), P["crust"])
    stem2 = t.mix((t.math("MULTIPLY", (n_l, 0), 0.30), 0), (stem, 2), P["soil_damp"])
    stem3 = t.mix((t.math("MULTIPLY", (v, 0), 0.25), 0), (stem2, 2), P["moss"])
    b1 = t.bump((n_f, 0), 0.45, 0.00025)
    p = t.n("ShaderNodeBsdfPrincipled")
    t.link(stem3, 2, p, "Base Color")
    t.link(b1, 0, p, "Normal")
    t.link(t.fmix((pg, 2), 0.80, 0.62), 0, p, "Roughness")
    t.set(p, "Specular IOR Level", 0.35)
    # a dead stem is thin and the low sun comes through it
    t.set(p, "Transmission Weight", 0.0)
    t.link(t.math("MULTIPLY", (pg, 2), 0.30), 0, p, "Subsurface Weight")
    t.set(p, "Subsurface Radius", (0.004, 0.003, 0.0015))
    t.out(p)
    return t.m


def mat_stubble():
    """Cut grass butts: green at the base, bleached at the sheared tip."""
    t = NT(PFX + "Stubble")
    co = t.n("ShaderNodeTexCoord")
    pid = t.attr("pid")
    pg = t.attr("pgrad")
    n_f = t.noise(1400.0, 12.0, 0.60, vec=(co, "Object"), dist=0.35)
    n_v = t.noise(6.0, 6.0, 0.52, vec=(co, "Object"))
    live = t.mix((n_v, 0), P["turf"], P["turf_pale"])
    # per-butt condition: some are still green, some cut weeks ago and straw
    cond = t.ramp((pid, 2), [(0.70, (0, 0, 0)), (0.98, (1, 1, 1))])
    body = t.mix((cond, 0), (live, 2), P["thatch"])
    # the sheared tip browns off within a day of the mower
    tip = t.ramp((pg, 2), [(0.84, (0, 0, 0)), (1.00, (1, 1, 1))])
    body2 = t.mix((t.math("MULTIPLY", (tip, 0), 0.38), 0), (body, 2), P["thatch_old"])
    b1 = t.bump((n_f, 0), 0.35, 0.00018)
    p = t.n("ShaderNodeBsdfPrincipled")
    t.link(body2, 2, p, "Base Color")
    t.link(b1, 0, p, "Normal")
    t.set(p, "Roughness", 0.62)
    t.set(p, "Specular IOR Level", 0.38)
    # a 12.5 deg sun goes straight through a 0.15 mm leaf; without this the
    # sward turns to black wire the moment it is backlit
    t.link(t.math("MULTIPLY", (pg, 2), 0.22), 0, p, "Subsurface Weight")
    t.set(p, "Subsurface Radius", (0.0025, 0.0035, 0.0012))
    t.out(p)
    return t.m


def build_materials():
    return dict(ground=mat_ground(), stone=mat_stone(), clod=mat_clod(),
                cast=mat_cast(), thatch=mat_thatch(), stubble=mat_stubble())


# ================================================================================
# 10.  LIGHT  —  world_contract §13, not a rounded copy of it
# ================================================================================

def contract_light(scene=None, coll=None):
    """The film's sun and sky, exactly as `world_contract` measured them.

    NOT `tools/fix_audit_blend.py:procedural_world()`.  That helper predates the
    contract and sets aerosol 2.2 / ozone 1.0 / sun_intensity 0.85, which is a
    different sky: its diffuse is far higher and far less blue, so a material
    calibrated under it is wrong under the one the film ships with.  The manifest
    names that mismatch as the direct cause of the pink/green blotching, so this
    item is lit by the contract and `--calibrate` proves it.
    """
    scene = scene or bpy.context.scene
    from mathutils import Vector

    w = bpy.data.worlds.new(PFX + "World")
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    out.location = (600, 0)
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.location = (380, 0)
    sky = nt.nodes.new("ShaderNodeTexSky")
    sky.location = (120, 0)
    avail = {e.identifier for e in sky.bl_rna.properties["sky_type"].enum_items}
    for want in ("MULTIPLE_SCATTERING", "SINGLE_SCATTERING", "HOSEK_WILKIE"):
        if want in avail:
            sky.sky_type = want
            break
    for attr, val in (("sun_disc", False),
                      ("sun_size", math.radians(C.SUN_ANGULAR_DIAM_DEG)),
                      ("sun_intensity", 1.0),
                      ("sun_elevation", math.radians(C.SUN_ELEV_DEG)),
                      ("sun_rotation", math.radians(C.SKY_SUN_ROTATION_DEG)),
                      ("altitude", C.SKY_ALTITUDE),
                      ("air_density", C.SKY_AIR),
                      ("aerosol_density", C.SKY_AEROSOL),
                      ("ozone_density", C.SKY_OZONE)):
        if hasattr(sky, attr):
            setattr(sky, attr, val)
    bg.inputs["Strength"].default_value = 1.0
    nt.links.new(sky.outputs["Color"], bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    scene.world = w

    lt = bpy.data.lights.new(PFX + "Sun", "SUN")
    lt.energy = C.SUN_ENERGY
    lt.color = C.SUN_COLOR
    lt.angle = math.radians(C.SUN_ANGULAR_DIAM_DEG)
    lt.use_shadow = True
    ob = bpy.data.objects.new(PFX + "Sun", lt)
    d = Vector(C.SUN_DIR)
    ob.rotation_mode = "QUATERNION"
    ob.rotation_quaternion = d.to_track_quat("Z", "Y")
    ob.location = (d.x * 2000.0, d.y * 2000.0, d.z * 2000.0)
    ob.visible_camera = False
    (coll or scene.collection).objects.link(ob)

    scene.view_settings.view_transform = C.VIEW_TRANSFORM
    try:
        scene.view_settings.look = C.VIEW_LOOK
    except Exception:
        pass
    scene.view_settings.exposure = C.REFERENCE_EXPOSURE_EXTERIOR
    log("light: sun %.3f W/m2 %s, elev %.3f deg, bearing %.3f deg; sky MS "
        "air %.2f aerosol %.2f ozone %.2f; AgX %.3f EV"
        % (C.SUN_ENERGY, C.SUN_COLOR, C.SUN_ELEV_DEG, C.SUN_BEARING_DEG,
           C.SKY_AIR, C.SKY_AEROSOL, C.SKY_OZONE, C.REFERENCE_EXPOSURE_EXTERIOR))
    return ob


# ================================================================================
# 11.  BUILD
# ================================================================================

def build(centre=None, nrings=RINGS_DEFAULT, detail=True, quality=1.0,
          quick=False, scene=None):
    """Emit the item into the `ITEM_TERRAIN_GROUND` collection.

    centre   world (x, y) the clipmap is centred on.  Default: the hero centre,
             6.0 m outboard of the corridor rim at the doppler station.
    nrings   how many clipmap rings.  5 reaches 130 m; 8 reaches the manifest's
             21.7 km square and is what world assembly should ask for.
    quick    4x thinner rings (cells doubled), for debugging the pipeline only.
    """
    scene = scene or bpy.context.scene
    # quick mode doubles every cell and halves every count: the extents and the
    # nesting invariants survive (a factor of 4 does not -- 150 is not divisible
    # by 4 and ring 2's hole stops landing on a grid line), so this is 2, not 4.
    rings = [(c * 2.0, n // 2) for (c, n) in RINGS] if quick else list(RINGS)
    rings = rings[:nrings]
    _check_rings(rings)

    purge()
    root = _coll(COLL)
    centre = tuple(centre) if centre else hero_centre()
    rng = np.random.default_rng(SEED)
    stats = dict(quads=0, verts=0)

    log("centre %.3f %.3f   rings %d   hero cell %.4f m -> %.2f px at %.1f m/%.0f mm"
        % (centre[0], centre[1], len(rings), rings[0][0],
           rings[0][0] * PX_PER_M, FILMED_AT_M, LENS_MM))
    mats = build_materials()
    for k in range(len(rings)):
        build_ring(k, rings, centre, root, 0.20, mats["ground"],
                   cut_corridor=True, stats=stats)
    if detail:
        build_detail(centre, root, rng, mats, quality=quality * (0.35 if quick else 1.0),
                     stats=stats)

    C.stamp(root)          # which contract this was built against
    root["item"] = "terrain_ground"
    root["hero_cell_m"] = rings[0][0]
    log("built: %d objects, %d verts, %d quads"
        % (len(root.objects), stats["verts"], stats["quads"]))
    return root


# ================================================================================
# 12.  THE ACCEPTANCE SCENE
# ================================================================================

def add_camera(name, loc, look, lens, coll, dof_target=None):
    from mathutils import Vector
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = 36.0
    cd.clip_start = 0.01
    cd.clip_end = 30000.0
    ob = bpy.data.objects.new(name, cd)
    ob.location = loc
    d = Vector(look) - Vector(loc)
    ob.rotation_mode = "QUATERNION"
    ob.rotation_quaternion = d.to_track_quat("-Z", "Y")
    coll.objects.link(ob)
    if dof_target is not None:
        cd.dof.use_dof = True
        cd.dof.focus_distance = float(d.length)
        cd.dof.aperture_fstop = float(dof_target)
    return ob


def test_scene(nrings=RINGS_DEFAULT, detail=True, quick=False, samples=256):
    """Build the item, light it with the contract sun, and put the manifest's
    own camera on it: 2.4 m away, 35 mm, which is the shot it has to survive."""
    scene = bpy.context.scene
    # Blender's startup file ships a Cube, a Camera and a 1000 W point Light.
    # Leaving them in means the item is judged under a light the film does not
    # have, and the render farm prewarms a camera that looks at nothing.
    for ob in list(bpy.data.objects):
        if not ob.name.startswith(PFX):
            bpy.data.objects.remove(ob, do_unlink=True)
    for lib in (bpy.data.materials, bpy.data.meshes, bpy.data.lights,
                bpy.data.cameras, bpy.data.worlds):
        for d in list(lib):
            if not d.name.startswith(PFX) and d.users == 0:
                lib.remove(d)          # the startup Cube's orphan "Material"
    root = build(nrings=nrings, detail=detail, quick=quick, scene=scene)
    cams = _coll(COLL + "/Cameras", root)
    contract_light(scene, coll=root)

    cx, cy = hero_centre()
    # Aim at the tile centre, which sits between the two ruts, and look across
    # them at 42 deg to the sun.  Worked out rather than eyeballed: a 35 mm lens
    # 2.400 m out at 33 deg above the surface frames ground from 1.13 m to 4.30 m
    # of the camera's nadir, which on this bearing is Dp 3.56 down to Dp 1.18 --
    # so BOTH wheel ruts, the walkway between them and the mown turf beyond are
    # in the frame, and 78 % of the frame is the 2.5 mm ring.
    ax, ay = cx, cy
    az = float(surface_z(np.array([ax]), np.array([ay]))[0])

    # The view bearing is derived, not chosen by eye.  Looking INBOARD sends the
    # top of the frame over the local crest and into the road corridor, which
    # this module deliberately builds no ground in -- the first macro render had
    # a black wedge in the corner for exactly that reason.  So the camera looks
    # OUTBOARD, where the ground runs on for 130 m, offset 26 deg so the ruts
    # cross the frame diagonally instead of running straight up it.
    p0 = np.asarray(C.su_to_world(DOPPLER_S, PLATFORM_EDGE * DOPPLER_SIDE), float)
    p1 = np.asarray(C.su_to_world(DOPPLER_S, (PLATFORM_EDGE + 1.0) * DOPPLER_SIDE), float)
    outb = (p1 - p0)[:2]
    outb /= np.linalg.norm(outb)
    view_az = math.atan2(outb[1], outb[0]) + math.radians(26.0)
    sun_az = math.atan2(C.SUN_DIR[1], C.SUN_DIR[0])
    off = math.degrees(abs((view_az - sun_az + math.pi) % (2 * math.pi) - math.pi))
    elev = math.radians(31.0)
    cam_p = (ax - math.cos(view_az) * FILMED_AT_M * math.cos(elev),
             ay - math.sin(view_az) * FILMED_AT_M * math.cos(elev),
             az + FILMED_AT_M * math.sin(elev))
    macro = add_camera(PFX + "CAM_MACRO", cam_p, (ax, ay, az), LENS_MM, cams)
    d = math.dist(cam_p, (ax, ay, az))
    log("macro camera: %.4f m from the surface on a %.0f mm lens (manifest: %.1f m / %.0f mm)"
        % (d, LENS_MM, FILMED_AT_M, LENS_MM))
    log("  view bearing %.1f deg, sun %.1f deg off axis (raking cross light), "
        "camera %.3f m over the surface" % (math.degrees(view_az), off,
                                            cam_p[2] - az))

    # a second look, further back, so the tile can be judged in its setting
    wz = float(surface_z(np.array([cx]), np.array([cy]))[0])
    wide_p = (cx - math.cos(view_az) * 9.0, cy - math.sin(view_az) * 9.0, wz + 2.9)
    add_camera(PFX + "CAM_WIDE", wide_p, (cx, cy, wz), 35.0, cams)

    scene.camera = macro
    scene.render.engine = "CYCLES"
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.film_transparent = False
    scene.cycles.samples = samples
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.01
    scene.cycles.max_bounces = 8
    scene.cycles.diffuse_bounces = 4
    scene.cycles.use_denoising = True
    return root


# ================================================================================
# 13.  MEASUREMENT
# ================================================================================

def selftest(n=150000, seed=7):
    """Measure the claims in the docstring instead of asserting them."""
    ok = [True]

    def chk(label, cond, detail=""):
        ok[0] &= bool(cond)
        print("  [%s] %-58s %s" % ("PASS" if cond else "FAIL", label, detail))

    _check_rings(RINGS)
    print("  [PASS] clipmap nesting: %d rings, cell ratios integral" % len(RINGS))

    rng = np.random.default_rng(seed)
    cx, cy = hero_centre()
    E = RINGS[0][0] * RINGS[0][1] * 0.5
    X = cx + (rng.random(n) - 0.5) * 2 * E
    Y = cy + (rng.random(n) - 0.5) * 2 * E

    M = macro_at(X, Y, 0.20)
    Mx = macro_at(X, Y, 0.0)
    chk("0.20 m lattice reproduces build_terrain's landform",
        np.abs(M["z"] - Mx["z"]).max() < 0.0005,
        "max %.4f mm" % (np.abs(M["z"] - Mx["z"]).max() * 1e3))

    dz = micro_relief(X, Y, HERO_CELL_M, Mx)
    chk("micro-relief stays inside MICRO_RELIEF_MAX_M (hero tile)",
        np.abs(dz).max() <= MICRO_RELIEF_MAX_M,
        "max %.4f m (constant %.3f), p99 %.4f m"
        % (np.abs(dz).max(), MICRO_RELIEF_MAX_M, np.percentile(np.abs(dz), 99)))

    # ... and over a WIDE band, which is where the molehills and the rills live.
    # This is the number the 14 dependants need: how far this module's surface
    # can be from build_terrain's, i.e. how wrong a clump placed on the old
    # datum would be.
    rs = np.random.default_rng(seed + 1)
    S2 = 2200.0 + rs.random(25000) * 800.0
    U2 = -(PLATFORM_EDGE + rs.random(25000) * 45.0)
    W2 = C.su_to_world(S2, U2)
    # direct, not on a lattice: the sample spans 800 m of lap, and a 0.20 m
    # lattice over that bounding box is 900 000 points to answer 25 000 questions
    Mw = macro_at(W2[:, 0], W2[:, 1], 0.0)
    dzw = micro_relief(W2[:, 0], W2[:, 1], HERO_CELL_M, Mw)
    chk("micro-relief stays inside MICRO_RELIEF_MAX_M (45 m band, 800 m of lap)",
        np.abs(dzw).max() <= MICRO_RELIEF_MAX_M,
        "max %.4f m (constant %.3f), p99 %.4f m, rms %.4f m"
        % (np.abs(dzw).max(), MICRO_RELIEF_MAX_M, np.percentile(np.abs(dzw), 99),
           float(np.sqrt((dzw ** 2).mean()))))

    # band limiting: a coarse ring must not carry fine relief
    for cell in (0.0025, 0.02, 0.5):
        d = micro_relief(X[:20000], Y[:20000], cell, {k: v[:20000] for k, v in Mx.items()})
        print("     cell %6.4f m -> relief rms %7.4f m  p99 %7.4f m"
              % (cell, float(np.sqrt((d ** 2).mean())), float(np.percentile(np.abs(d), 99))))

    # the corridor weld: on the rim my ground must be world_contract.ground_z
    S = np.linspace(2400.0, 2700.0, 400)
    for side in (+1, -1):
        R = np.asarray(C.corridor_rim(S, side), float)
        rx, ry, rz = R[:, 0], R[:, 1], R[:, 2]
        got = surface_z(rx, ry, cell=0.02, lattice_step=0.0)
        chk("weld to corridor_rim, side %+d" % side,
            np.abs(got - rz).max() < C.TOL_SEAM_M,
            "max %.4f mm (TOL_SEAM_M %.0f mm)"
            % (np.abs(got - rz).max() * 1e3, C.TOL_SEAM_M * 1e3))

    # the hero tile must be terrain's ground, not the road programme's
    it = is_terrain(X[:50000], Y[:50000])
    chk("hero tile is entirely outside the road corridor", it.all(),
        "%.2f %% terrain-owned" % (100.0 * it.mean()))

    # attributes
    A = surface_attributes(X[:40000], Y[:40000])
    miss = [k for k in ATTR_NAMES if k not in A]
    chk("every declared attribute exists", not miss, str(miss))
    bad = [k for k in ATTR_SCALAR
           if k in A and (not np.isfinite(A[k]).all()
                          or A[k].min() < -1e-6 or A[k].max() > 1.3)]
    chk("attributes are finite and in range", not bad, str(bad))
    print("     cover %.3f  bare %.3f  wear %.3f  rut %.3f  thatch %.3f  grit %.3f"
          % (A["ter_cover"].mean(), A["ter_bare"].mean(), A["ter_wear"].mean(),
             A["ter_rut"].mean(), A["ter_thatch"].mean(), A["ter_grit"].mean()))

    # normals
    N = surface_normal(X[:20000], Y[:20000])
    chk("normals are unit and up", np.abs(np.linalg.norm(N, axis=1) - 1).max() < 1e-9
        and N[:, 2].min() > 0.05, "min nz %.4f" % N[:, 2].min())

    # the palette: the anti-blotch rule
    bad = [k for k, v in PALETTE.items() if v[2] / max(v[0], 1e-6) < 0.42]
    chk("every palette colour keeps b/r >= 0.42 (blue fill will not go green)",
        not bad, str(bad))
    for k in ("topsoil", "soil_dry", "turf", "thatch"):
        v = PALETTE[k]
        r = C.lambert_radiance(v)
        print("     %-10s albedo %.3f -> lambert %.4f %.4f %.4f"
              % (k, sum(v) / 3.0, r[0], r[1], r[2]))

    print(">> STAGE RESULT: %s" % ("SELFTEST_PASS" if ok[0] else "SELFTEST_FAIL"))
    return ok[0]


def calibrate(res=(320, 240), samples=160):
    """Render two albedo-0.18 probes and report the measured direct:diffuse.

    THE MANIFEST'S OWN CONCERN, turned into a number.  It says terrain assumed a
    3.00:1 direct:diffuse and the shipped sky measures 2.072:1, and names that
    mismatch as the direct cause of the "pink and green blotches".  A claim that
    this item is lit by the second number is worth nothing unless something
    measures it, so this renders it.

    ORTHOGRAPHIC ON PURPOSE.  The first version used a 24 mm perspective camera
    26 m up and both probes fell outside the frame, so it dutifully measured the
    black sky below the horizon and reported 0.052:1 -- a broken instrument
    reporting a broken world.  With an ortho camera the world-to-pixel map is
    one multiplication and the crop windows are exact.
    """
    import tempfile
    sc = bpy.context.scene
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    contract_light(sc)

    # A PURE LAMBERT PROBE, not a Principled one.  `lambert_radiance` is defined
    # as albedo*E/pi, and Principled is a layered model whose diffuse lobe loses
    # a few percent to its specular layer even at Specular IOR Level 0 -- so a
    # Principled probe measures the BSDF as much as it measures the light and
    # came back 12 % low.  Diffuse BSDF at roughness 0 is exactly Lambert.
    m = bpy.data.materials.new(PFX + "probe")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out_n = nt.nodes.new("ShaderNodeOutputMaterial")
    dif = nt.nodes.new("ShaderNodeBsdfDiffuse")
    dif.inputs["Color"].default_value = (0.18, 0.18, 0.18, 1.0)
    dif.inputs["Roughness"].default_value = 0.0
    nt.links.new(dif.outputs[0], out_n.inputs["Surface"])

    def plane(name, loc, size, mat=m):
        bm = bmesh.new()
        bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=size * 0.5)
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        if mat is not None:
            me.materials.append(mat)
        ob = bpy.data.objects.new(name, me)
        ob.location = loc
        sc.collection.objects.link(ob)
        return ob

    AX, BX = 0.0, 9.0
    plane(PFX + "probe_sun", (AX, 0.0, 0.0), 5.0)
    plane(PFX + "probe_sky", (BX, 0.0, 0.0), 5.0)
    # A blocker put straight overhead does not shadow anything at a 12.5 deg sun.
    # It has to sit on the SUN RAY through the probe: offset by H*cot(elev) along
    # the sun's horizontal bearing.  cot(12.4706 deg) = 4.5222 = SUN_SHADOW_RATIO,
    # which the contract already publishes, so this is its number and not a
    # second opinion.
    H = 3.0
    hx, hy = C.SUN_DIR[0], C.SUN_DIR[1]
    hn = math.hypot(hx, hy)
    blk = plane(PFX + "blocker",
                (BX + hx / hn * H * C.SUN_SHADOW_RATIO,
                 hy / hn * H * C.SUN_SHADOW_RATIO, H), 16.0, mat=None)
    blk.visible_camera = False

    cd = bpy.data.cameras.new(PFX + "CAM_CAL")
    cd.type = "ORTHO"
    cd.ortho_scale = 20.0
    cam = bpy.data.objects.new(PFX + "CAM_CAL", cd)
    cam.location = ((AX + BX) * 0.5, 0.0, 40.0)
    cam.rotation_euler = (0.0, 0.0, 0.0)          # looks down -Z
    sc.collection.objects.link(cam)
    sc.camera = cam

    sc.render.engine = "CYCLES"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = False
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.view_settings.view_transform = "Standard"       # read LINEAR values
    sc.view_settings.exposure = 0.0
    sc.render.image_settings.file_format = "OPEN_EXR"
    sc.render.image_settings.color_depth = "32"
    out = os.path.join(tempfile.mkdtemp(), "cal.exr")
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(out)
    px = np.array(img.pixels[:]).reshape(res[1], res[0], 4)

    # exact world -> pixel for an ortho camera
    W, Hh = res
    cx = cam.location[0]
    mpp = cd.ortho_scale / W
    def patch(wx, half=1.4):
        i0 = int((wx - half - cx) / mpp + W * 0.5)
        i1 = int((wx + half - cx) / mpp + W * 0.5)
        j0 = int(Hh * 0.5 - half / mpp)
        j1 = int(Hh * 0.5 + half / mpp)
        return px[j0:j1, i0:i1, :3].reshape(-1, 3).mean(axis=0)

    sun = patch(AX)
    sky = patch(BX)
    want = np.array(C.lambert_radiance(0.18))
    want_sky = 0.18 * np.array(C.SKY_IRRADIANCE) / math.pi
    print(">> lambert_radiance(0.18)   contract  %.4f %.4f %.4f" % tuple(want))
    print(">> measured full-sun probe            %.4f %.4f %.4f" % tuple(sun))
    print(">> sky-only prediction      contract  %.4f %.4f %.4f" % tuple(want_sky))
    print(">> measured shadow probe              %.4f %.4f %.4f" % tuple(sky))
    d2d = (sun.sum() - sky.sum()) / max(sky.sum(), 1e-9)
    # back out the irradiances the render actually delivered, so a disagreement
    # can be attributed instead of argued about
    e_sky = math.pi * sky / 0.18
    e_dir = math.pi * (sun - sky) / 0.18
    print(">> implied SKY irradiance             %.3f %.3f %.3f  "
          "(contract %.3f %.3f %.3f)" % (*e_sky, *C.SKY_IRRADIANCE))
    print(">> implied DIRECT horizontal          %.3f %.3f %.3f  "
          "(contract %.3f %.3f %.3f)" % (*e_dir, *C.E_DIRECT_HORIZONTAL))
    print(">> measured direct:diffuse  %.3f : 1   (contract %.3f : 1, "
          "build_terrain assumed 3.000 : 1)" % (d2d, C.DIRECT_TO_DIFFUSE))
    err = float(np.abs(sun - want).max() / max(want.mean(), 1e-9))
    print(">> worst channel error vs the contract: %.2f %%" % (err * 100.0))
    # THE TOLERANCE, AND WHY IT IS NOT TIGHTER.  world_contract's SKY_IRRADIANCE
    # was measured against build_sky's FULL world -- Sky Texture plus three
    # composited cloud decks plus an aerosol mottle.  This item's test scene
    # lights itself from the bare Sky Texture at the contract's parameters, which
    # delivers about 85 % of that diffuse.  So a few percent of level is expected
    # and is attributed above rather than tuned away in the albedos.  What the
    # manifest actually warned about is the KEY:FILL RATIO, and the check is that
    # this scene is on the contract's 2.072 side of the argument and nowhere near
    # build_terrain's assumed 3.000.
    ok = (err < 0.16 and abs(d2d - C.DIRECT_TO_DIFFUSE) < 0.35
          and abs(d2d - 3.0) > 0.5)
    print(">> STAGE RESULT: %s" % ("CALIBRATION_PASS" if ok else "CALIBRATION_FAIL"))
    return sun, sky


# ================================================================================
# 14.  CLI
# ================================================================================

def main():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", action="store_true", help="build the acceptance scene")
    ap.add_argument("--build", action="store_true", help="build the item only")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--calibrate", action="store_true")
    ap.add_argument("--quick", action="store_true", help="4x thinner, debug only")
    ap.add_argument("--rings", type=int, default=RINGS_DEFAULT)
    ap.add_argument("--nodetail", action="store_true")
    ap.add_argument("--samples", type=int, default=256)
    ap.add_argument("--save", default=None)
    ap.add_argument("--render", default=None)
    ap.add_argument("--cam", default=PFX + "CAM_MACRO")
    ap.add_argument("--res", type=int, nargs=2, default=[1920, 1080])
    a = ap.parse_args(argv)

    if a.calibrate:
        calibrate()
        return
    if a.selftest:
        sys.exit(0 if selftest() else 1)
    if a.test or a.build or a.save or a.render:
        if a.test or a.save or a.render:
            test_scene(nrings=a.rings, detail=not a.nodetail, quick=a.quick,
                       samples=a.samples)
        else:
            build(nrings=a.rings, detail=not a.nodetail, quick=a.quick)
    if a.save:
        p = os.path.abspath(a.save)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        ext = [i.filepath for i in bpy.data.images if i.source == "FILE"]
        if ext:
            raise SystemExit("REFUSING TO SAVE: external images %s" % ext)
        bpy.ops.wm.save_as_mainfile(filepath=p, compress=True, relative_remap=False)
        log("saved %s (%.1f MB)" % (p, os.path.getsize(p) / 1048576.0))
    if a.render:
        sc = bpy.context.scene
        sc.camera = bpy.data.objects[a.cam]
        sc.render.resolution_x, sc.render.resolution_y = a.res
        sc.cycles.samples = a.samples
        sc.render.filepath = os.path.abspath(a.render)
        os.makedirs(os.path.dirname(sc.render.filepath), exist_ok=True)
        bpy.ops.render.render(write_still=True)
        log("rendered %s" % sc.render.filepath)


if __name__ == "__main__" and HAVE_BPY:
    main()
