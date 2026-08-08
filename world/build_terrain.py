#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_terrain.py — landform, treeline, undergrowth and grass for CIRCUIT VITRINE.

ONE CONTINUOUS SHOT.  The camera flies out of the showroom, across the paddock and
around a 3675 m lap, so every square metre of ground here is potentially on screen.
There are no cheap far-side zones; there is only budget-by-distance.

WHAT THIS MODULE OWNS
  * the landform OUTSIDE the road corridor: a single continuous height field carrying
    the circuit's 11.63 m of relief, welded vertex-for-vertex to world_contract's
    corridor rim, plus the five named landforms from circuit_spec.md §5.
  * everything growing on it — inside the corridor as well as outside: 9 tree species
    + dead snags + saplings, shrubs, ferns, reeds, weeds, wildflowers, stones and six
    kinds of grass, all generated procedurally, all placed by habitat.
  * everything LYING on it.  Bare ground is made of the 10-95 mm fraction -- grit,
    flint chips and dried clods -- and that fraction is geometry, not a bump map, or it
    does not exist at a 12.47 deg sun.  See `build_grit` and build_terrain.md 6.3b.

VEGETATION IS A GEOMETRY PROBLEM, NOT A MATERIAL PROBLEM.  A grass shader on a plane
  cannot look like grass 2.4 m from the lens, and beat_sheet.json's doppler hover puts
  the camera exactly there.  Hero blades are channelled about a midrib, in tillers, at
  life size (3.4-6.6 mm), 6 segments, with a short understorey -- 2 914 polygons per
  clump against the previous 211, spent only inside GRASS_HERO_D of the camera path
  because instancing makes base geometry free and traversal is what costs.  See
  `gen_grass` and build_terrain.md 5.5.

WHAT IT DOES NOT OWN
  * the racing surface, kerbs, runoff, gravel traps, barriers, buildings, sky or sun.
  * ANY GROUND GEOMETRY INSIDE THE ROAD CORRIDOR.  world_contract.road_corridor_mask
    is a hole in this height field, not a blend: 0.31 km^2 of it.  See section 2 of
    build_terrain.md and WORLD_CONTRACT.md section 5.

THE CONTRACT IS AUTHORITATIVE.  Every number this module shares with another builder
  — the datum z, the track width, the corridor rim, the runoff cross-section, the sun
  and the exposure — is imported from world_contract, never re-derived here.

Run headless:
    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup -noaudio -P build_terrain.py
    ...  -P build_terrain.py -- --selftest --cams doppler --save ter.blend    (910 s)
    ...  -P build_terrain.py -- --macro doppler --cams doppler --save m.blend  (40 s)
Idempotent: re-running deletes and rebuilds the WORLD_TERRAIN collection only.

`--macro` is the pixel-work loop: ONE 300 m window of verge at full production density,
built from the SAME functions the full build calls (they take a station window), so a
1:1 crop of it is evidence about the build and not about the probe.
"""

import bpy, bmesh, math, json, os, sys, time, colorsys
import numpy as np
from mathutils import Vector, Matrix, Euler

# ----------------------------------------------------------------------------------
# 0.  CONFIGURATION
# ----------------------------------------------------------------------------------

HERE      = os.path.dirname(os.path.abspath(__file__))
ROOT      = os.path.dirname(HERE)
SPEC_JSON = os.path.join(ROOT, "docs", "circuit_spec.json")
BEAT_JSON = os.path.join(ROOT, "docs", "beat_sheet.json")

if HERE not in sys.path:
    sys.path.insert(0, HERE)
import world_contract as C          # THE datum, the widths, the corridor, the light
import itemkit as K                 # relief_amplitude_for / detail_for -- the laws

COLL      = "WORLD_TERRAIN"
PFX       = "TER_"          # every datablock we own starts with this
VPFX      = "VEG_"

# Quality dial.  TERRAIN_FAST=1 in the environment thins the scatter for local
# GTX-1070 test renders; it never changes geometry *design*, only counts.
FAST      = os.environ.get("TERRAIN_FAST", "0") == "1"
QUAL      = float(os.environ.get("TERRAIN_QUALITY", "0.28" if FAST else "1.0"))

# --- ground grid -------------------------------------------------------------------
CORE_MIN  = (-980.0, -560.0)      # world metres; circuit bbox is x -635..557 y -215..941
CORE_MAX  = ( 900.0, 1290.0)
CELL      = 2.5 if not FAST else 5.0
FAR_STEPS = 26                    # geometrically-growing rings out to the horizon
FAR_GROW  = 1.30

# --- THE HORIZON --------------------------------------------------------------------
# A FLAT PLATE CANNOT MAKE A HORIZON FOR AN ELEVATED CAMERA, AND THAT IS GEOMETRY,
# NOT AN OPINION.  Beat 6 holds for its last 11 seconds from z = 140 m.  Ground at
# z = 0 always subtends a NEGATIVE elevation from up there, so however far the plate
# is pushed, a wedge of sky-direction-but-not-sky is left between the plate's edge and
# the true horizon — and Blender's Nishita sky returns BLACK for every direction below
# the horizon, so that wedge renders as a void.  Measured on the plate as it stands
# (`work/ramp/skyline.json`, `Ground.height` walked outward on 48 bearings from the
# beat-6 hold):
#
#     plate edge          10 233 .. 15 840 m   ->  -0.51 .. -0.78 deg
#     skyline of the      even sampled to 60 km the height field never
#     height field        exceeds +11 m, so 48 of 48 bearings are BELOW the horizon
#
# Pushing FAR_STEPS to 32 buys 48 km and -0.16 deg, still 6 black rows at 4K, and it
# takes the outermost cell from 2.3 km to 49 km.  The honest fix is the one real
# landscapes use: THE FAR GROUND RISES.  A range whose crest stands above the
# camera's eye level puts sky on land instead of sky on nothing, and it costs no new
# source mesh and no new instance — it is the ground's own height field.
#
# The wavelengths are set by the GRID, not by taste.  The outermost rings are 1.0-2.3
# km wide, so anything shorter than about 12 km out there is below Nyquist and will
# alias into a saw edge on the skyline; the second octave is therefore faded out
# before the cells get coarse rather than left to sparkle.  (The existing +-34 m a3
# term already runs a 2.1 km wavelength through 1.4-2.3 km cells between 5.2 and
# 11 km, which is marginal; it is left alone here, and noted.)
# WHAT THIS IS AND IS NOT RESPONSIBLE FOR — MEASURED, 2026-08-03, AND IT REFUTES
# THE BRIEF THIS TERM WAS WRITTEN FOR. The 56 black rows were NOT the plate's
# edge. `ONER`'s camera datablock ships with clip_end = 1000.0 m — Blender's
# factory default, never set by `anim/build_camera_rig.py:575` — against
# `build_sky`'s own documented hand-off of >= 50 km. Everything past 1 km was
# simply not drawn. Three renders of the SAME ground under the SAME sky settle
# it (`work/ramp/b6/`, counted by `tools/black_row_count.py`):
#
#     terrain WITH this term,    clip   1 000 m   ->  71 black rows
#     terrain WITH this term,    clip 200 000 m   ->   0 black rows
#     terrain WITHOUT this term, clip 200 000 m   ->   0 black rows
#
# So THIS TERM IS NOT WHAT FIXES THE DEFECT and it must not be credited with it.
# The 80 km aerosol slab in-scatters enough over 10 km (18 % transmittance) that
# a ray missing the plate comes back as haze rather than as void.
#
# It is kept for what it DOES do, which the A/B shows plainly: without it the far
# field dissolves into a featureless haze band with no horizon LINE in it; with
# it the sky sits on a defined edge. It costs nothing — 599 872 verts and 600 209
# polys either way, bit-identical, because it changes z on vertices that already
# exist — and it is one constant to switch off: SET `HORIZON_Z_M = 0.0` AND THE
# TERM VANISHES ENTIRELY, which is exactly how the control above was rendered.
HORIZON_RISE_M   = 3600.0     # Dc where the far field begins to climb
HORIZON_CREST_M  = 9500.0     # Dc where it has fully climbed
HORIZON_Z_M      = 300.0      # mean crest height above the datum
HORIZON_LAM_M    = 15500.0    # along-range wavelength of the crest line
HORIZON_RELIEF_M = 118.0      # p-p modulation of the crest at HORIZON_LAM_M
HORIZON_LAM2_M   = 6400.0     # second octave: foothills and spurs
HORIZON_REL2_M   = 46.0
HORIZON_LAM3_M   = 2400.0     # third octave, alive only where the cells are fine
HORIZON_REL3_M   = 14.0

# --- corridor ----------------------------------------------------------------------
# THE HOLE.  world_contract.road_corridor_mask is the region the road programme owns;
# this module builds no ground inside it at all.  PLATFORM_DROP (0.12 m) and the old
# `Circuit._platform` runoff table are GONE — the platform is world_contract.ground_z,
# which already falls at -1.6 % from the banked road edge, and terrain welds its first
# ring of vertices to world_contract.corridor_rim.
BATTER        = C.CORRIDOR_BATTER_M   # 34.0 m: rim -> natural ground
DITCH_DEPTH   = 0.34      # drainage swale, OUTSIDE the rim (contract section 5)
DITCH_AT      = 9.0       # metres outboard of the rim to the swale invert
DITCH_SIG     = 3.4       # swale half-width shape
DITCH_HOLD    = (1.2, 5.0)  # the swale is forced to zero over this band at the rim,
                            # so the weld cannot be a 34 mm notch (TOL_SEAM_M = 10 mm)
CUT_REFINE    = 26        # bisection halvings that put each cut vertex ON the rim
                          # rather than on the linear interpolation of the field.
                          # 26 halvings of a 2.5 m cell edge is 3.7e-8 m.
TRACK_DS      = 1.0       # centreline sampling

SEED          = 20260728

# --- vegetation budget (production values; scaled by QUAL) --------------------------
BUDGET = dict(
    trees_near      = 1500,   # <  90 m of the camera path: hero LOD, unique meshes
    trees_mid       = 4200,   # 90-350 m
    trees_far       = 6200,   # > 350 m, incl. the skyline mass
    hedge_trees     = 1100,
    shrubs          = 9000,
    ferns           = 5200,
    reeds           = 2600,
    grass_near      = 420000, # clumps within the verge band
    grass_mid       = 190000,
    meadow          = 120000,
    weeds           = 26000,  # docks, thistles, plantain, yarrow, ragwort
    stones          = 34000,  # scree, field stone, and gravel dragged out of the traps
)

# --- wind (shared by grass lean, tree lean bias and canopy flagging) ----------------
WIND_BEARING = 65.0                      # degrees, world; direction the wind blows TO
WIND_DIR     = (math.cos(math.radians(WIND_BEARING)), math.sin(math.radians(WIND_BEARING)))
WIND_LEAN    = math.radians(15.0)        # mean grass lean from vertical

SUN_DIR      = np.array(C.SUN_DIR)       # direction TO the sun, world.  CONTRACT.

# Foliage is budgeted by leaf-area index, and the per-species leafn figures below are
# set for LAI ~= 2.5-4.  This multiplier takes the broadleaf species up to LAI ~4-5.5,
# which is where a mature closed crown actually sits, once the virtual shoots in
# _dress_leaves spread the leaves through the crown volume instead of along the twigs.
LEAF_DENSITY = (1.55, 2.35, 1.0)   # per LOD

# L1 gets the bigger boost on purpose.  L1 covers 95-380 m from the camera path, and at
# 4K that is a tree 100-400 px tall -- big enough that a see-through crown reads as a
# defect, but the tier was budgeted at a third of L0 as if it were background.  A
# 1280x720 check on the esses ridge showed exactly that: near trees dense, the 150 m
# treeline behind them skeletal.  The number that matters is leaf area over crown area in
# PIXELS, and at L1 it was ~1.1 (transparent); 2.35x puts it at ~1.8.

LOG_T0 = time.time()
def log(msg):
    print("[terrain %7.1fs] %s" % (time.time() - LOG_T0, msg), flush=True)


# ----------------------------------------------------------------------------------
# 1.  NUMPY NOISE  (everything procedural — no textures are loaded from disk)
# ----------------------------------------------------------------------------------

def _hash2(ix, iy, seed):
    h = (ix.astype(np.int64) * np.int64(1597334677)) ^ (iy.astype(np.int64) * np.int64(3812015801))
    h = (h ^ np.int64(seed * 2654435761)) & np.int64(0x7FFFFFFF)
    h = (h ^ (h >> 15)) * np.int64(2246822519)
    h = (h ^ (h >> 13)) * np.int64(3266489917)
    return (h ^ (h >> 16)) & np.int64(0x7FFFFFFF)


def hash01(ix, iy, seed=0):
    """Deterministic [0,1) hash of an integer lattice point."""
    return _hash2(ix, iy, seed).astype(np.float64) / float(0x7FFFFFFF)


def gnoise2(x, y, seed=0):
    """Perlin-style gradient noise, quintic interpolation, output ~[-1,1]."""
    ix = np.floor(x).astype(np.int64); iy = np.floor(y).astype(np.int64)
    fx = x - ix; fy = y - iy
    def dot(cx, cy, dx, dy):
        a = hash01(cx, cy, seed) * (2.0 * math.pi)
        return np.cos(a) * dx + np.sin(a) * dy
    u = fx * fx * fx * (fx * (fx * 6 - 15) + 10)
    v = fy * fy * fy * (fy * (fy * 6 - 15) + 10)
    n00 = dot(ix,     iy,     fx,       fy)
    n10 = dot(ix + 1, iy,     fx - 1.0, fy)
    n01 = dot(ix,     iy + 1, fx,       fy - 1.0)
    n11 = dot(ix + 1, iy + 1, fx - 1.0, fy - 1.0)
    return (n00 * (1 - u) + n10 * u) * (1 - v) + (n01 * (1 - u) + n11 * u) * v


def fbm(x, y, octaves=4, lac=2.03, gain=0.5, seed=0):
    amp, f, tot, norm = 1.0, 1.0, 0.0, 0.0
    for o in range(octaves):
        tot = tot + amp * gnoise2(x * f, y * f, seed + o * 977)
        norm += amp
        amp *= gain; f *= lac
    return tot / norm


def ridged(x, y, octaves=4, seed=0):
    amp, f, tot, norm = 1.0, 1.0, 0.0, 0.0
    for o in range(octaves):
        n = 1.0 - np.abs(gnoise2(x * f, y * f, seed + o * 613))
        tot = tot + amp * (n * n)
        norm += amp
        amp *= 0.5; f *= 2.07
    return tot / norm


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a + 1e-12), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def window(x, lo, hi, feather):
    """1 inside [lo,hi], falling to 0 over `feather` on each side."""
    return smoothstep(lo - feather, lo, x) * (1.0 - smoothstep(hi, hi + feather, x))


# ----------------------------------------------------------------------------------
# 2.  THE CIRCUIT — centreline, elevation, corridor widths
# ----------------------------------------------------------------------------------

class Circuit:
    """A thin, cached view of world_contract's centreline and corridor.

    NOTHING here is re-derived.  The old class integrated its own centreline, its own
    half-width table (`_half_width`, which box-filtered a [3115, 3675] span over 60 m
    and so CENTRED the width transition on the element boundary instead of starting
    there — 15.00 m at s = 3115 against the spec's 16.00, 0.502 m out over 14.4 % of
    the lap) and its own runoff table (`_platform`).  All three are deleted.  The
    contract owns them, `build_barriers` builds to them, and this module now asks.
    """

    def __init__(self, spec):
        self.spec = spec
        self.L = C.LAP
        self.S = np.arange(0.0, C.LAP, TRACK_DS)
        self.N = len(self.S)
        self.X, self.Y, self.H, self.K = C.centreline_arrays(self.S)
        self.Z = C.elevation_c(self.S)                 # centreline datum
        self.HW = C.half_width(self.S)                 # spec S9, fixed
        self.VE = C.verge_edge(self.S)                 # outer edge of build_surface
        # the corridor rim, per side, and the datum z ON it
        self.PLAT = {+1: C.platform_edge(self.S, +1), -1: C.platform_edge(self.S, -1)}
        self.RIMZ = {s: C.ground_z(self.S, self.PLAT[s] * s) for s in (+1, -1)}
        self.MAXPLAT = float(max(self.PLAT[+1].max(), self.PLAT[-1].max()))

    # -- nearest-point query --------------------------------------------------------
    def query(self, px, py):
        """-> (s, u_signed, lim, z_rim) for arbitrary world points.

        u is SIGNED, + to the LEFT of travel — the convention finding #1 was about.
        `lim` is world_contract.platform_edge on that side (the corridor rim) and
        `z_rim` is world_contract.ground_z AT the rim, i.e. exactly the z terrain's
        first ring of vertices must weld to.
        """
        f, zr, s, u, lim, Dc = corridor_fz(px, py)
        return s, u, lim, zr


# world <-> circuit frame -- the contract's, so the frames cannot drift ---------------
world_to_circuit = C.world_to_circuit
circuit_to_world = C.circuit_to_world


# ----------------------------------------------------------------------------------
# 2b.  THE ROAD CORRIDOR AS A SIGNED FIELD
# ----------------------------------------------------------------------------------
#
# `C.road_corridor_mask` answers yes/no.  Cutting a hole with a straight edge needs
# a SIGNED field so a cell that straddles the rim can be clipped instead of dropped:
# at CELL = 2.5 m, dropping whole cells puts a 2.5 m sawtooth down both sides of a
# 3675 m circuit, which is the failure the contract's section 5 is written about.
#
#     corridor_field(x, y)  <= 0  the road programme owns this ground; build nothing
#                            > 0  metres outboard of the rim, measured laterally
#
# It is the same region as `road_corridor_mask` — checked, both ways, in `selftest`.

_RIB_T = np.linspace(0.0, C.ACCESS_TOTAL, 981)
_RIB_IN, _RIB_OUT = C.access_edges(_RIB_T)
_RIB_M = C.ACCESS_CORRIDOR_MARGIN_M
_CIR_BB = None          # filled by _corridor_bbox() on first use


def _corridor_bbox():
    global _CIR_BB
    if _CIR_BB is None:
        s = np.arange(0.0, C.LAP, 1.0)
        X, Y, _, _ = C.centreline_arrays(s)
        pad = float(max(C.platform_edge(s, +1).max(), C.platform_edge(s, -1).max())) + 2.0
        _CIR_BB = (X.min() - pad, X.max() + pad, Y.min() - pad, Y.max() + pad)
    return _CIR_BB


# --- the medial axis, and why the nearest branch is not enough -----------------------
#
# `C.project` returns the NEAREST point on the centreline, and `C.road_corridor_mask`
# compares |u| against THAT branch's `platform_edge`.  On a closed loop that is not
# quite the corridor: at the medial axis between two branches a point is very nearly
# equidistant from both and `project` picks one.  If the branch it picks has a 12.1 m
# platform and the branch it does not has an 87.9 m one, the mask says "terrain builds
# here" about ground `build_barriers` will pave from the other branch.  MEASURED on
# this grid: the nearest-branch field is discontinuous by up to 33.4 m at the medial
# axis, and 1.4 % of the cut vertices landed on the discontinuity instead of on a rim.
#
# So this module projects onto the two nearest DISTINCT branches and takes the smaller
# field.  That is continuous across the medial axis, and it is deliberately
# CONSERVATIVE: terrain's hole becomes a superset of `road_corridor_mask`, never a
# subset, so terrain can never build ground the road programme also builds.  The extra
# area is reported by `selftest` as `union_extra_m2`.

_UDS = 1.0                                       # union sampling step along the lap
_US = np.arange(0.0, C.LAP, _UDS)
_UX, _UY, _UH, _UK = C.centreline_arrays(_US)
_UCH = np.cos(_UH); _USH = np.sin(_UH)
_UPP = C.platform_edge(_US, +1)                  # rim offset, left of travel
_UPM = C.platform_edge(_US, -1)                  # rim offset, right of travel
# The rim, on a 5 cm station grid, for the along-corrected lookup below.  The runoff
# ramps are steep -- 45 m of asphalt eased over 55 m of station is 0.8 m of rim per
# metre travelled, and PE'' is large where a ramp starts -- so a quad that uses its own
# station's rim, or even a first-order extrapolation of it, dilates the union laterally
# and opens a gap between terrain and the platform build_barriers actually lays.
# MEASURED: own-station 1.4 m, first-order 0.55 m, this 0.01 m.
_FDS = 0.05
_FS_ = np.arange(0.0, C.LAP, _FDS)
_FPP = C.platform_edge(_FS_, +1)
_FPM = C.platform_edge(_FS_, -1)
_NF = len(_FS_)
_UKA = np.abs(_UK)
_NU = len(_US)
UNION_BAND = 130.0        # |u| beyond which no station can possibly claim a point:
                          # max platform_edge is 87.95 m, so 130 is a 42 m guard, and
                          # both fields exceed BATTER there so the height field cannot
                          # notice the switch


def union_field(x, y, pchunk=20000, schunk=256):
    """The EXACT corridor field: min over every station of the distance to its quad.

    The corridor is the swept region  {|along| <= ds/2,  -platform_edge(-1) <= u <=
    platform_edge(+1)}  over all stations.  For station i the signed distance to that
    quad is

        max( u - PE_left(s_i + along),  -PE_right(s_i + along) - u,
             |along| - (ds/2)(1 + |u| |kappa|) )

    with the rim linearly interpolated off a 5 cm station grid,

    and the field is the minimum over i.  Two corrections that are not decoration:
    the `(1 + |u| |kappa|)` factor lengthens each quad by exactly the arc a laterally
    offset point covers on the outside of a curve, which closes the fan gap between
    consecutive quads (at 88 m of runoff and kappa = 0.04 the gap is 3.5 m); and the
    rim is evaluated at `s_i + along` to first order, without which that same
    lengthening drags the widening runoff ramps outward and opens a 1.4 m gap between
    terrain and the platform.  A minimum of finitely many continuous functions is continuous, which is the
    whole point: `C.project`-based fields jump by up to 33 m at the medial axis of the
    loop and the cell clipper cannot bisect a discontinuity.

    -> (f, s_owner, u_owner) for the station whose quad is nearest.
    """
    n = len(x)
    best = np.full(n, np.inf)
    bs = np.zeros(n); bu = np.zeros(n)
    for a in range(0, n, pchunk):
        b = min(n, a + pchunk)
        xa = x[a:b, None]; ya = y[a:b, None]
        m = b - a
        cb = np.full(m, np.inf); cs = np.zeros(m); cu = np.zeros(m)
        for p in range(0, _NU, schunk):
            q = min(_NU, p + schunk)
            ex = xa - _UX[None, p:q]
            ey = ya - _UY[None, p:q]
            along = ex * _UCH[None, p:q] + ey * _USH[None, p:q]
            lat = -ex * _USH[None, p:q] + ey * _UCH[None, p:q]
            # ARC, NOT TANGENT.  A point at lateral u whose perpendicular foot is
            # `d` metres of STATION away sits at along = d * (1 - u*kappa) in the
            # frame of this station.  So the foot -- the station whose rim actually
            # governs it -- is s_i + along / (1 - u*kappa), and the along window that
            # corresponds to +-ds/2 of station is (ds/2) * (1 - u*kappa).  Using
            # `along` as if it were station puts the rim lookup up to 0.55 m out at
            # 57 m of offset in an 82 m-radius corner, which is a 0.55 m slot between
            # terrain and the platform.
            wf = np.maximum(1.0 - lat * _UK[None, p:q], 0.15)
            sq = (_US[None, p:q] + along / wf) * (1.0 / _FDS)
            k0 = np.floor(sq); wq = sq - k0
            k0 = k0.astype(np.int64) % _NF
            k1 = (k0 + 1) % _NF
            pep = _FPP[k0] * (1.0 - wq) + _FPP[k1] * wq
            pem = _FPM[k0] * (1.0 - wq) + _FPM[k1] * wq
            du = np.maximum(lat - pep, -pem - lat)
            da = np.abs(along) - 0.5 * _UDS * wf
            fi = np.maximum(du, da)
            j = np.argmin(fi, axis=1)
            r = np.arange(m)
            v = fi[r, j]
            upd = v < cb
            cb = np.where(upd, v, cb)
            cs = np.where(upd, (_US[p + j] + along[r, j] / wf[r, j]) % C.LAP, cs)
            cu = np.where(upd, lat[r, j], cu)
        best[a:b] = cb; bs[a:b] = cs; bu[a:b] = cu
    return best, bs, bu


def corridor_fz(x, y):
    """-> (f, z_rim, s, u, lim, Dc).

    `f`      metres outboard of the road corridor; <= 0 where the road programme owns
             the ground and this module must build none.  EXACT and CONTINUOUS: the
             union field above inside a 130 m band, the cheap nearest-branch value
             outside it, and the two are numerically interchangeable there because
             both exceed the 34 m batter.
    `z_rim`  world_contract's datum ON the rim that owns the boundary here — the z
             terrain welds to.  On the lap that is `ground_z(s, +-platform_edge)`,
             i.e. exactly `C.corridor_rim`.  Around the Beat-4 access ribbon it is the
             ribbon's own plane (`access_z`), which is flat z = 0.000 for the first
             49.6 m per spec 10.3(b) and identically `ground_z` past the merge.
    `Dc`     distance to the nearest centreline.  CONTINUOUS everywhere, unlike `f`'s
             cheap approximation, so every long-range rule (relief amplitude, woodland
             density, hedgerows) is keyed on this and not on the corridor field.

    ONE implementation, used by both the cutter and the height field, so the cut and
    the batter cannot disagree about where the rim is.
    """
    x = np.atleast_1d(np.asarray(x, float))
    y = np.atleast_1d(np.asarray(y, float))
    s, u = C.project(x, y)
    Dc = np.abs(u)
    lim = np.where(u >= 0.0, C.platform_edge(s, +1), C.platform_edge(s, -1))
    f = Dc - lim
    band = Dc < UNION_BAND
    if band.any():
        fu, su, uu = union_field(x[band], y[band])
        i = np.where(band)[0]
        f[i] = fu; s[i] = su; u[i] = uu
        lim[i] = np.where(uu >= 0.0, C.platform_edge(su, +1), C.platform_edge(su, -1))
    z = C.ground_z(s, np.where(u >= 0.0, lim, -lim))
    rb = (x > C.ACCESS_GLASS_X - 40.0) & (x < 320.0) & (y > -80.0) & (y < 220.0)
    if rb.any():
        t, v = C.access_project(x[rb], y[rb])
        lo = np.interp(t, _RIB_T, _RIB_IN) - _RIB_M
        hi = np.interp(t, _RIB_T, _RIB_OUT) + _RIB_M
        # THE START CAP IS THE GLASS PLANE, NOT `-margin`.  Assembly finding #2: the
        # 3.0 m keep-out is a LATERAL allowance for the Beat-4 corridor wall footings,
        # and treating it as longitudinal too walked terrain's cut 3.0 m BACK THROUGH
        # THE GLASS WALL to world x = 12.000, while architecture cut to 14.70 and
        # build_surface's ribbon starts at 15.000 -- 64 m2 of the Beat-3 -> Beat-4
        # hinge with no ground at all, a black slot in CAM_GLASS_GAP.png at the exact
        # metre the car breaches the glass.  `C.ACCESS_RIBBON_T_MIN` is now the pinned
        # start of the ribbon for every consumer and every margin.
        fr = np.maximum(np.maximum(lo - v, v - hi),
                        np.maximum(C.ACCESS_RIBBON_T_MIN - t,
                                   t - (C.ACCESS_TOTAL + _RIB_M)))
        take = fr < f[rb]
        if take.any():
            idx = np.where(rb)[0][take]
            f[idx] = fr[take]
            z[idx] = C.access_z(np.clip(t[take], 0.0, C.ACCESS_TOTAL),
                                np.clip(v[take], lo[take], hi[take]))
    return f, z, s, u, lim, Dc


def corridor_field(x, y):
    """Metres outboard of the road corridor.  <= 0 inside it.  Vectorised."""
    return corridor_fz(x, y)[0]


def cut_field(x, y):
    """THE FIELD THE GROUND MESH IS CUT WITH.  <= 0 where terrain builds nothing.

    `min(corridor_field, C.platform_field)` — the road corridor UNION the declared
    z = 0.000 platform.

    DEFECT #50, v1.1.1.  This module cut a hole for the corridor and nothing else.
    For the paddock, the pit lane, the garages and the pit-exit apron it only
    FLATTENED its height field (`built`, in `landform`), so `TER_Ground` was still
    THERE, underneath build_architecture's concrete, at whatever height the
    flattening left it.  MEASURED on the assembled world by casting the full ray
    stack in 7 585 columns over the pit-exit apron:

        ARCH_Paving_Paddock x TER_Ground   859 columns  |dz| p50 15.59 mm
                                           s 3196-3406, u 41.0-45.0
        ARCH_Paving_PitLane x TER_Ground    60 columns  |dz| p50 16.59 mm
        49 of 7 585 columns (0.65 %) carried two DIFFERENTLY-OWNED surfaces
        within 2 mm of each other.

    Two owners on one square metre flickers under a moving camera, and this is a
    ONE-SHOT film with no cut to hide it.  `C.world_ground_z` already hands every
    one of those columns to `build_architecture:paving`; the contract's rule for
    this is "cut, do not offset" (TOL_COPLANAR_M); there simply was no signed field
    to cut the platform with.  `C.platform_field` is that field.

    The declared platform is 63 725 m2 of which 76 % lies outside the corridor —
    48 400 m2 — against build_architecture's own reported `paving_m2` of 48 239.
    The two agree to 0.3 %, which is the check that this is the same region and not
    a second opinion about it.

    ONLY THE CUT USES THIS.  `corridor_field` still drives the batter, the relief
    ramp and the plant-clearance tests, because those are statements about distance
    from the ROAD and the platform is not a road.
    """
    return np.minimum(corridor_field(x, y),
                      np.asarray(C.platform_field(x, y), float))


# ----------------------------------------------------------------------------------
# 3.  THE HEIGHT FIELD
# ----------------------------------------------------------------------------------

def far_horizon(x, y, Dc):
    """The distant range that gives the closing wide a skyline.

    See the HORIZON_* block at the top of this file for why a flat plate cannot
    produce a horizon for a camera at 140 m and why the answer is elevation
    rather than extent.

    THREE THINGS THIS IS DELIBERATELY NOT
    --------------------------------------
    * It is not a backdrop, a skirt or a horizon ring.  It is a term in the
      ground's own height field, so it is the same mesh, the same material and
      the same weld; there is no LOD boundary to crack and no second surface to
      keep in step.
    * It is not new geometry.  `build_ground` already emits a vertex at every
      station of the graded axes out to 10.8 km; this changes their z.  Zero
      extra vertices, zero extra source meshes, zero extra instances — which is
      what the red line on asset reuse is actually about.
    * It is not visible from the circuit.  `Dc` is distance to the CENTRELINE,
      and this is identically zero inside HORIZON_RISE_M = 3.6 km.  The lap, the
      paddock, the showroom, every declared empty-zone camera volume and the
      whole 1 150 m vegetation field are further inside that than the term ever
      reaches, so nothing the car drives past or the lens gets near moves by a
      millimetre.  `selftest` measures exactly that.

    The third octave is windowed OFF beyond 6 km because the cells there pass
    2.4 km wavelengths at under two samples each.  A skyline that sparkles
    between frames is worse than a skyline that is smooth, and this shot holds
    for three seconds without a cut.
    """
    w = smoothstep(HORIZON_RISE_M, HORIZON_CREST_M, Dc)
    if not np.any(w):
        return np.zeros_like(np.asarray(x, float))
    crest = (0.5 + 0.5 * ridged(x / HORIZON_LAM_M, y / HORIZON_LAM_M,
                                2, seed=71))
    z = HORIZON_Z_M + HORIZON_RELIEF_M * (crest - 0.5)
    z = z + HORIZON_REL2_M * fbm(x / HORIZON_LAM2_M, y / HORIZON_LAM2_M,
                                 2, seed=73)
    z = z + (HORIZON_REL3_M * fbm(x / HORIZON_LAM3_M, y / HORIZON_LAM3_M,
                                  2, seed=79)
             * (1.0 - smoothstep(4200.0, 6400.0, Dc)))
    return w * z


class Ground:
    """h(x,y) for the world OUTSIDE the road corridor, plus the shader's attributes.

    Structure
      base      Shepard interpolation of the road's own z over the whole plane, so the
                ground everywhere is anchored to the elevation the circuit actually has
      landform  the five named features of circuit_spec §5, each anchored to the track
                feature it is named after
      relief    fBm whose amplitude ramps in with distance OUTBOARD OF THE RIM
      batter    over the first 34 m outboard of the rim the natural ground is blended
                into world_contract.ground_z AT THE RIM, so the weld is exact at the
                rim (weight 0) and nothing is imposed on the road programme

    Inside the corridor this function is still defined and still smooth — the cut
    interpolates across it — but no vertex ends up there.  See `build_ground`.
    """

    def __init__(self, cir):
        self.cir = cir
        # Shepard control points: the centreline every 10 m
        st = 10
        self.px = cir.X[::st].copy(); self.py = cir.Y[::st].copy(); self.pz = cir.Z[::st].copy()
        # named anchors
        cs = {c["name"].split()[0]: c for c in cir.spec["corners"] if c.get("is_numbered_corner")}
        self.T4 = np.array(cs["T4"]["apex_world"][:2])
        # outward normal of the hairpin (apex - arc centre)
        self.T4_out = np.array([-0.208, 0.978])
        self.T8 = np.array(cs["T8"]["apex_world"][:2])

    # -- Shepard base ---------------------------------------------------------------
    def base(self, x, y, chunk=20000):
        out = np.empty(len(x))
        a2 = 42.0 ** 2
        for a in range(0, len(x), chunk):
            b = min(len(x), a + chunk)
            dx = x[a:b, None] - self.px[None, :]
            dy = y[a:b, None] - self.py[None, :]
            w = 1.0 / (dx * dx + dy * dy + a2)
            w *= w                       # 1/d^4 -> tight anchoring near the track
            out[a:b] = (w @ self.pz) / w.sum(axis=1)
        return out

    # -- the named landforms --------------------------------------------------------
    # Every feature is a SMOOTH WORLD-SPACE primitive.  An earlier version masked them
    # with the nearest-station arc length s and the signed lateral offset d; both flip
    # discontinuously across the medial axis of the loop and printed 15 m cliffs
    # straight across the outfield.  Nothing here may depend on (s, d).
    def landform(self, x, y):
        z = np.zeros(len(x))

        def dome(cx, cy, ax, ay, rot, amp):
            c, s_ = math.cos(rot), math.sin(rot)
            ux = ((x - cx) * c + (y - cy) * s_) / ax
            uy = (-(x - cx) * s_ + (y - cy) * c) / ay
            t = np.clip(1.0 - (ux * ux + uy * uy), 0.0, 1.0)
            return amp * t * t * (3 - 2 * t)

        # (1) NE ESCARPMENT beyond T4.  Falls at -8 % from the edge of the hairpin's
        #     gravel to -10.5 m, then levels into a valley floor that rolls back up
        #     into the far field: a camera on T4's inside kerb sees the car against
        #     falling ground and sky (spec §5, §11).
        r = np.hypot(x - self.T4[0], y - self.T4[1])
        u = np.stack([(x - self.T4[0]) / (r + 1e-6), (y - self.T4[1]) / (r + 1e-6)], 1)
        fan = smoothstep(-0.10, 0.80, u @ self.T4_out)
        z += fan * (-10.5) * smoothstep(44.0, 175.0, r) * (1.0 - 0.80 * smoothstep(430.0, 1150.0, r))

        # (2) THE RIDGE carrying the esses; crest +3.5 m over the summit shelf, plus a
        #     knoll on the infield flank so 8 m of road relief reads as 19 m of
        #     landscape.  Both clear the infield-bowl camera volume.
        z += dome(-238.0, 665.0, 430.0, 235.0, math.radians(158.0), 3.55)
        z += dome(-140.0, 428.0, 210.0, 148.0, math.radians(150.0), 2.75)

        # (3) THE WEST HILLSIDE.  A ramp hinged on the line through the sweeper and the
        #     doppler straight, falling away on the outboard (west) side to -12 m.
        ox, oy = -556.0, 45.0
        along  = (x - ox) * 0.212 + (y - oy) * (-0.977)
        out    = (x - ox) * (-0.977) + (y - oy) * (-0.212)
        z += (-12.0) * smoothstep(78.0, 340.0, out) * window(along, -430.0, 430.0, 330.0)

        # (4) THE RETURN HOLLOW at T12/T13 — deepen the bowl the road already sits in.
        z += dome(-452.0, -192.0, 235.0, 118.0, math.radians(12.0), -1.15)

        # (5) THE PLATEAU: dead flat z=0 for the pit straight, paddock and showroom.
        cx, cy = world_to_circuit(x, y)
        plat = window(cx, -620.0, 300.0, 110.0) * window(cy, -120.0, 140.0, 85.0)

        # (6) The three named empty zones (spec §10.7) are camera volumes.  Terrain
        #     inside them is held near the local datum so nothing grows into the
        #     helicopter arc, the doppler sight line or the Beat-6 crane-out.
        z_ez = (window(cx, -340.0, 160.0, 90.0) * window(cy, 180.0, 420.0, 90.0))
        z_ez = np.maximum(z_ez, window(cx, -1010.0, -860.0, 80.0) * window(cy, 150.0, 560.0, 80.0))
        z_ez = np.maximum(z_ez, window(cx, -120.0, 260.0, 90.0) * window(cy, -340.0, -62.0, 90.0))
        return z, plat, z_ez

    # -- rolling far field ----------------------------------------------------------
    def relief(self, x, y, Dp, Dc, calm):
        """`Dp` is metres OUTBOARD OF THE CORRIDOR RIM, not from the centreline.

        The old version keyed on distance from the centreline, which meant the relief
        amplitude at a given point depended on how wide the runoff happened to be
        there — 30 m of amplitude ramp had already been spent by the time the ground
        emerged from under a 70 m runoff.  `calm` (0..1) suppresses relief inside the
        plateau and the declared empty-zone camera volumes.
        """
        k = 1.0 - calm
        a1 = smoothstep(30.0, 260.0, Dc)
        a2 = smoothstep(200.0, 900.0, Dc)
        a3 = smoothstep(700.0, 2600.0, Dc)
        z  = a1 * 2.2 * fbm(x / 195.0, y / 195.0, 3, seed=11) * k
        z += a2 * 7.5 * fbm(x / 620.0, y / 620.0, 3, seed=23) * k
        z += (a3 * (1.0 - smoothstep(5200.0, 11000.0, Dc)) * 34.0
              * (0.5 + 0.5 * ridged(x / 2100.0, y / 2100.0, 3, seed=37)))
        # micro relief for the verges: long wavelengths only, the grid cell is 2.5 m.
        # It starts at the rim now instead of 2 m from the centreline, so the ground
        # immediately behind the barrier is not glassy.
        z += smoothstep(0.5, 26.0, Dp) * 0.42 * fbm(x / 26.0, y / 26.0, 2, seed=53) \
            * (0.35 + 0.65 * k)
        z += smoothstep(1.0, 12.0, Dp) * 0.11 * fbm(x / 7.4, y / 7.4, 2, seed=59) * k
        z += far_horizon(x, y, Dc)
        return z


    # -- the whole thing ------------------------------------------------------------
    def height(self, x, y, want_attr=False):
        """Natural ground, welded to the corridor rim.

        Returns z everywhere it is asked, including inside the corridor, where the
        value is a smooth continuation used only by the cell-clipper's interpolation.
        `build_ground` removes every vertex and every face that lands there.
        """
        x = np.asarray(x, float); y = np.asarray(y, float)
        f, zrim, s, u, lim, Dc = corridor_fz(x, y)
        Dp = np.maximum(f, 0.0)                   # 0 ON the rim

        zb = self.base(x, y)
        zl, plateau, empty = self.landform(x, y)
        calm = np.clip(np.maximum(0.90 * plateau, 0.82 * empty), 0.0, 1.0)
        z_nat = zb + zl * (1.0 - 0.85 * empty)
        z_nat = z_nat * (1.0 - 0.94 * plateau)             # plateau flattening
        z_nat = z_nat + self.relief(x, y, Dp, Dc, calm)

        # --- built platforms: paddock / pit / showroom pad and the round-1 ground ----
        cx, cy = world_to_circuit(x, y)
        pad = window(cx, -490.0, 140.0, 26.0) * window(cy, -70.0, 120.0, 26.0)
        r1  = window(x, -172.0, 172.0, 26.0) * window(y, -172.0, 172.0, 26.0)
        built = np.maximum(pad, r1)
        z_nat = z_nat * (1.0 - built) + (0.0 - 0.20) * built

        # --- THE BATTER -------------------------------------------------------------
        # At the rim (Dp = 0) the weight is exactly 0, so terrain's first ring of
        # vertices lands on world_contract.ground_z to the last bit.  It is a weld,
        # not a tolerance: TOL_SEAM_M never has to absorb anything.
        t = smoothstep(0.0, 1.0, Dp / BATTER)
        z = (1.0 - t) * zrim + t * z_nat

        # --- the drainage swale, OUTSIDE the rim -------------------------------------
        # The old one was centred 7 m beyond the platform edge with sigma 4.6, which
        # left a 34 mm notch AT the weld.  It is now held to zero over the first
        # DITCH_HOLD metres and its invert is 9 m out.
        ditch = DITCH_DEPTH * np.exp(-(((Dp - DITCH_AT) / DITCH_SIG) ** 2))
        ditch *= smoothstep(DITCH_HOLD[0], DITCH_HOLD[1], Dp)
        ditch *= (1.0 - smoothstep(0.55, 0.95, plateau)) * 0.75 + 0.25
        z -= ditch

        if not want_attr:
            return z
        return z, dict(s=s, u=u, D=Dc, Dp=Dp, f=f, zrim=zrim, lim=lim,
                       plateau=plateau, built=built, corridor=t, cx=cx, cy=cy)


# ----------------------------------------------------------------------------------
# 4.  MESH PLUMBING
# ----------------------------------------------------------------------------------

def new_mesh(name, verts, faces, uvs=None):
    me = bpy.data.meshes.new(name)
    verts = np.asarray(verts, dtype=np.float32)
    me.vertices.add(len(verts))
    me.vertices.foreach_set("co", verts.ravel())
    if len(faces):
        counts = np.array([len(f) for f in faces], dtype=np.int32)
        loops = np.concatenate([np.asarray(f, dtype=np.int32) for f in faces])
        starts = np.concatenate([[0], np.cumsum(counts)[:-1]]).astype(np.int32)
        me.loops.add(len(loops))
        me.loops.foreach_set("vertex_index", loops)
        me.polygons.add(len(counts))
        me.polygons.foreach_set("loop_start", starts)
    me.update(calc_edges=True)
    me.validate(verbose=False)
    return me


def new_mesh_arrays(name, verts, tris, quads=None):
    """Fast path when faces are homogeneous numpy arrays."""
    me = bpy.data.meshes.new(name)
    verts = np.asarray(verts, dtype=np.float32)
    me.vertices.add(len(verts))
    me.vertices.foreach_set("co", verts.ravel())
    polys = []
    counts = []
    if quads is not None and len(quads):
        polys.append(np.asarray(quads, np.int32).ravel()); counts.append(np.full(len(quads), 4, np.int32))
    if tris is not None and len(tris):
        polys.append(np.asarray(tris, np.int32).ravel()); counts.append(np.full(len(tris), 3, np.int32))
    if polys:
        loops = np.concatenate(polys); counts = np.concatenate(counts)
        starts = np.concatenate([[0], np.cumsum(counts)[:-1]]).astype(np.int32)
        me.loops.add(len(loops)); me.loops.foreach_set("vertex_index", loops)
        me.polygons.add(len(counts)); me.polygons.foreach_set("loop_start", starts)
    me.update(calc_edges=True)
    me.validate(verbose=False)
    return me


def link(obj, coll):
    coll.objects.link(obj)
    return obj


def get_coll(name, parent=None):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        (parent or bpy.context.scene.collection).children.link(c)
    return c


def purge():
    """Idempotency: delete everything this module has ever made, and nothing else."""
    root = bpy.data.collections.get(COLL)
    if root:
        stack = [root]; seen = []
        while stack:
            c = stack.pop()
            seen.append(c)
            stack.extend(list(c.children))
        for c in seen:
            for o in list(c.objects):
                bpy.data.objects.remove(o, do_unlink=True)
        for c in seen:
            bpy.data.collections.remove(c)
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.node_groups, bpy.data.objects):
        for d in list(coll):
            if d.name.startswith(PFX) or d.name.startswith(VPFX):
                try:
                    coll.remove(d)
                except Exception:
                    pass


# ----------------------------------------------------------------------------------
# 5.  GROUND MESH
# ----------------------------------------------------------------------------------

def graded_axis(lo, hi, cell, steps, grow):
    """Uniform `cell` across [lo,hi], then geometrically growing rings outward."""
    n = int(round((hi - lo) / cell))
    core = lo + np.arange(n + 1) * cell
    outs = []
    d = cell
    p = hi
    for _ in range(steps):
        d *= grow
        p += d
        outs.append(p)
    up = np.array(outs)
    dn = lo - (up - hi)
    return np.concatenate([dn[::-1], core, up])


def _cut_cells(F, nx, ny):
    """Marching-squares clip of the grid against the corridor field.

    Every cell is split into two triangles FIRST, then each triangle is clipped by
    Sutherland-Hodgman against f >= 0.  Splitting first is not a detail: clipping a
    quad against an implicit boundary is ambiguous when the two inside corners are
    diagonally opposite, and the ambiguous case resolves to a bow-tie that covers the
    hole.  A triangle carrying a linear field has no ambiguous case.

    Returns (polys, edge_keys): `polys` is a list of vertex-key rings over 'grid vertex
    flat index' (>= 0) and 'cut vertex' (encoded -(k+1)); `edge_keys` is the ordered
    list of (ia, ib) grid-edge endpoints that produced each cut vertex.  The rings are
    returned unsplit so `build_ground` can subdivide the one edge of each that lies on
    the rim before triangulating.
    """
    Fr = F.ravel()
    ins = (Fr < 0.0)
    ins2 = ins.reshape(nx, ny)
    cnt = (ins2[:-1, :-1].astype(np.int8) + ins2[1:, :-1] +
           ins2[1:, 1:] + ins2[:-1, 1:])
    mi, mj = np.where((cnt > 0) & (cnt < 4))

    cut = {}
    keys = []
    polys = []

    def crossing(a, b):
        k = (a, b) if a < b else (b, a)
        v = cut.get(k)
        if v is None:
            v = -(len(keys) + 1)
            cut[k] = v
            keys.append(k)
        return v

    def clip(tri):
        out = []
        n = len(tri)
        for q in range(n):
            a = tri[q]; b = tri[(q + 1) % n]
            fa = Fr[a] >= 0.0
            if fa:
                out.append(a)
            if fa != (Fr[b] >= 0.0):
                out.append(crossing(a, b))
        return out

    for i, j in zip(mi.tolist(), mj.tolist()):
        p0 = i * ny + j
        p1 = p0 + ny
        p2 = p1 + 1
        p3 = p0 + 1
        for tri in ((p0, p1, p2), (p0, p2, p3)):
            poly = clip(tri)
            if len(poly) >= 3:
                polys.append(poly)
    return polys, keys


def _rim_infill(polys, VX, VY, nk, target=0.40, maxsub=10):
    """Subdivide each clipped ring's rim edge and put the new vertices ON the rim.

    A clipped cell contributes ONE straight segment of the terrain boundary, so at
    CELL = 2.5 m the hole's edge is a 2.5 m polyline chasing a curve whose radius is
    as low as 25 m.  The chord sagitta is d^2/8R = 31 mm, and because the rim's z also
    curves, the ray-cast weld error was MEASURED at 121 mm max on the 5 m test grid —
    twelve times TOL_SEAM_M.  Splitting each rim edge to <= 0.60 m and projecting the
    new vertices back onto the rim by bisection takes that down by (0.6/2.5)^2.

    -> (polys, EX, EY) with the rings rewritten to include the new vertices, which
    continue the cut-vertex numbering (`nk` is how many of those there are).
    """
    seg = []                      # (poly index, position in ring, key_a, key_b, n)
    for pi, ring in enumerate(polys):
        m = len(ring)
        for q in range(m):
            a, b = ring[q], ring[(q + 1) % m]
            if a < 0 and b < 0:
                ia, ib = -a - 1, -b - 1
                d = math.hypot(VX[ia] - VX[ib], VY[ia] - VY[ib])
                n = int(min(maxsub, max(1, round(d / target))))
                if n > 1:
                    seg.append((pi, q, ia, ib, n))
    if not seg:
        return polys, np.zeros(0), np.zeros(0)

    A = []; B = []
    for (_, _, ia, ib, n) in seg:
        for k in range(1, n):
            A.append((ia, ib, k / n))
    ia = np.array([a[0] for a in A]); ib = np.array([a[1] for a in A])
    tt = np.array([a[2] for a in A])
    ax, ay = VX[ia], VY[ia]
    bx, by = VX[ib], VY[ib]
    mx = ax + tt * (bx - ax); my = ay + tt * (by - ay)
    dx = bx - ax; dy = by - ay
    L = np.maximum(np.hypot(dx, dy), 1e-9)
    nx_, ny_ = -dy / L, dx / L                  # unit normal to the chord
    R = 3.0                                     # the chord can cut 1.5 m into a tight
    fp = cut_field(mx + R * nx_, my + R * ny_)         # rim; +-0.8 m did not bracket
    fm = cut_field(mx - R * nx_, my - R * ny_)         # it and left 12 vertices in
    ok = (fp >= 0.0) != (fm >= 0.0)                     # the corridor
    lo = np.where(fp >= 0.0, -R, R)             # the inside end
    hi = -lo                                    # the outside end
    for _ in range(18):
        mid = 0.5 * (lo + hi)
        pos = cut_field(mx + mid * nx_, my + mid * ny_) >= 0.0
        hi = np.where(pos, mid, hi)
        lo = np.where(pos, lo, mid)
    EX = mx + hi * nx_
    EY = my + hi * ny_
    # A vertex whose perpendicular does not bracket the rim is DROPPED, not fudged: an
    # unprojected midpoint sits inside the corridor by the chord's sagitta, which is
    # exactly the defect this function exists to remove.
    keepv = ok & (cut_field(EX, EY) >= -1e-6)

    # infill vertices continue the CUT numbering, so both decode the same way:
    # ring id v < 0  ->  cut array index (-v - 1)
    idmap = np.full(len(EX), -1, np.int64)
    good = np.where(keepv)[0]
    idmap[good] = np.arange(len(good))
    EX = EX[good]; EY = EY[good]

    out = [list(r) for r in polys]
    pos = 0
    for (pi, q, _ia, _ib, n) in seg:
        ids = [idmap[pos + k] for k in range(n - 1)]
        pos += n - 1
        ids = [-(nk + int(v) + 1) for v in ids if v >= 0]
        if not ids:
            continue
        ring = out[pi]
        j = ring.index(polys[pi][q])            # at most one rim edge per clipped cell
        ring[j + 1:j + 1] = ids
    return out, EX, EY


def _refine_cuts(keys, fx, fy, Fr):
    """Put every cut vertex ON the rim, not on the linear interpolation of the field.

    BISECTION, not false position, and the answer is the OUTSIDE end of the final
    bracket.  Two reasons, both measured:

      * `corridor_field` is |u| - platform_edge(s), and near the medial axis of the
        loop, near a corner where platform_edge swings 40 m in 60 m of station, and
        wherever the access ribbon's field takes over from the lap's, it is strongly
        non-linear along a 2.5 m cell edge.  Five regula-falsi steps left 1.4 % of the
        cut vertices more than a millimetre out and the worst 33 m out — a spike
        straight through the runoff.
      * bisection's bracket shrinks unconditionally: 26 halvings of a 2.5 m edge is
        3.7e-8 m, and taking `ta` guarantees f >= 0, so a cut vertex can never be
        inside the corridor no matter how badly behaved the field is.

    `selftest` measures both: max |corridor_field| over the cut vertices, and the
    count of ground vertices inside the corridor (which must be 0).
    """
    if not keys:
        return np.zeros((0,)), np.zeros((0,))
    K = np.asarray(keys, np.int64)
    ia, ib = K[:, 0].copy(), K[:, 1].copy()
    swap = Fr[ia] < 0.0                       # make `a` the OUTSIDE end
    ia[swap], ib[swap] = K[swap, 1], K[swap, 0]
    xa, ya = fx[ia], fy[ia]
    xb, yb = fx[ib], fy[ib]
    ta = np.zeros(len(ia)); tb = np.ones(len(ia))
    for _ in range(CUT_REFINE):
        t = 0.5 * (ta + tb)
        px = xa + t * (xb - xa); py = ya + t * (yb - ya)
        pos = cut_field(px, py) >= 0.0
        ta = np.where(pos, t, ta)
        tb = np.where(pos, tb, t)
    return xa + ta * (xb - xa), ya + ta * (yb - ya)


def build_ground(gr, root):
    xs = graded_axis(CORE_MIN[0], CORE_MAX[0], CELL, FAR_STEPS, FAR_GROW)
    ys = graded_axis(CORE_MIN[1], CORE_MAX[1], CELL, FAR_STEPS, FAR_GROW)
    nx, ny = len(xs), len(ys)
    log("ground grid %d x %d = %d verts, extent %.0f x %.0f m"
        % (nx, ny, nx * ny, xs[-1] - xs[0], ys[-1] - ys[0]))
    GX, GY = np.meshgrid(xs, ys, indexing="ij")
    fx = GX.ravel(); fy = GY.ravel()
    z, at = gr.height(fx, fy, want_attr=True)
    # DEFECT #50: the cut is `cut_field`, not `at["f"]`.  `at["f"]` is distance from
    # the ROAD corridor and drives the batter and the relief ramp; the HOLE is the
    # road corridor UNION the declared z = 0.000 platform.  See `cut_field`.
    Fr = np.minimum(at["f"], np.asarray(C.platform_field(fx, fy), float))

    # ---- THE HOLE ---------------------------------------------------------------
    # world_contract.road_corridor_mask is the region build_surface, build_barriers
    # and build_architecture own.  Terrain builds NO ground there.  It does not
    # blend into it, drop to a platform under it or lay a shoulder inside it — the
    # 2.5 m grid cannot represent a track edge, and every one of the assembly
    # review's finding-1 numbers is what happens when it tries.
    t_cut = time.time()
    polys, keys = _cut_cells(Fr.reshape(nx, ny), nx, ny)
    cxr, cyr = _refine_cuts(keys, fx, fy, Fr)
    keep = Fr >= 0.0
    nk = int(keep.sum())
    vid = np.full(nx * ny, -1, np.int64)
    vid[keep] = np.arange(nk)
    polys, exr, eyr = _rim_infill(polys, cxr, cyr, len(cxr))
    cxr = np.concatenate([cxr, exr]); cyr = np.concatenate([cyr, eyr])

    # cut vertices: their z comes from the SAME height function, which at f = 0 is
    # exactly (1 - 0) * z_rim = world_contract.ground_z on the rim.  The weld is by
    # construction, not by tolerance.
    if len(cxr):
        zc, atc = gr.height(cxr, cyr, want_attr=True)
    else:
        zc = np.zeros(0); atc = {k: np.zeros(0) for k in at}

    VX = np.concatenate([fx[keep], cxr])
    VY = np.concatenate([fy[keep], cyr])
    VZ = np.concatenate([z[keep], zc])
    atv = {k: np.concatenate([at[k][keep], atc[k]]) for k in at}

    # true slope, from the built height field itself rather than guessed from the
    # landform structure (the old `ground_attributes` shipped an all-zero `slope`
    # and every rule that read it was therefore dead)
    gzx, gzy = np.gradient(z.reshape(nx, ny), xs, ys)
    sl = np.hypot(gzx, gzy)
    slz = GridZ(xs, ys, sl)
    atv["slope"] = np.concatenate([sl.ravel()[keep],
                                   slz(cxr, cyr) if len(cxr) else np.zeros(0)])

    # full quads: cells with no corner inside the corridor
    ins2 = (Fr < 0.0).reshape(nx, ny)
    cnt = (ins2[:-1, :-1].astype(np.int8) + ins2[1:, :-1] +
           ins2[1:, 1:] + ins2[:-1, 1:])
    I = np.arange(nx - 1)[:, None] * ny + np.arange(ny - 1)[None, :]
    full = (cnt == 0)
    Q = np.stack([I, I + ny, I + ny + 1, I + 1], axis=-1)[full]
    quads = vid[Q]

    # clipped cells: remap grid indices through `vid`, cut indices to nk + k, and fan
    # triangulate the (now subdivided) rings
    faces = []
    for ring in polys:
        r = [vid[v] if v >= 0 else nk + (-v - 1) for v in ring]
        for k in range(1, len(r) - 1):
            faces.append((r[0], r[k], r[k + 1]))
    tris = np.asarray(faces, np.int64) if faces else np.zeros((0, 3), np.int64)

    verts = np.stack([VX, VY, VZ], axis=1)
    me = new_mesh_arrays(PFX + "Ground", verts, tris, quads)
    log("  corridor cut: %d cells clipped, %d rim vertices (+%d infill), %d grid verts"
        " dropped, %.0f m2 removed  (%.1f s)"
        % (int(((cnt > 0) & (cnt < 4)).sum()), len(keys), len(exr), nx * ny - nk,
           float((~keep).sum()) * CELL * CELL, time.time() - t_cut))

    # the height grid the plant scatter samples still needs a value everywhere,
    # including inside the hole, so plants can be placed on the CONTRACT datum there
    grid = (xs, ys, z.reshape(nx, ny))

    # ---- surface attributes the material reads --------------------------------
    attrs = ground_attributes(VX, VY, VZ, atv)
    for name, data in attrs.items():
        if data.ndim == 1:
            a = me.attributes.new(name, "FLOAT", "POINT")
            a.data.foreach_set("value", data.astype(np.float32))
        else:
            a = me.attributes.new(name, "FLOAT_COLOR", "POINT")
            rgba = np.concatenate([data, np.ones((len(data), 1))], axis=1)
            a.data.foreach_set("color", rgba.astype(np.float32).ravel())

    ob = bpy.data.objects.new(PFX + "Ground", me)
    me.materials.append(bpy.data.materials[PFX + "Ground"])
    link(ob, root)
    me.shade_smooth()
    return ob, attrs, grid


def field_pattern(x, y):
    """Voronoi partition of the outfield into hedged fields.

    Returns (cell_id_hash, distance-to-boundary).  The same partition drives the
    ground shader's crop colour AND the hedgerow scatter, so hedges land exactly on
    the field boundaries instead of near them.
    """
    warpx = x + 46.0 * fbm(x / 260.0, y / 260.0, 2, seed=71)
    warpy = y + 46.0 * fbm(x / 260.0 + 19.0, y / 260.0 - 7.0, 2, seed=83)
    cs = 155.0
    gx = np.floor(warpx / cs).astype(np.int64); gy = np.floor(warpy / cs).astype(np.int64)
    best = np.full(len(x), 1e9); second = np.full(len(x), 1e9)
    bid = np.zeros(len(x))
    for ox in (-1, 0, 1):
        for oy in (-1, 0, 1):
            cx = gx + ox; cy = gy + oy
            jx = (cx + hash01(cx, cy, 101)) * cs
            jy = (cy + hash01(cx, cy, 202)) * cs
            dd = np.hypot(warpx - jx, warpy - jy)
            take = dd < best
            second = np.where(take, best, np.minimum(second, dd))
            bid = np.where(take, hash01(cx, cy, 303), bid)
            best = np.where(take, dd, best)
    return bid, (second - best)


# --- where cars run wide -------------------------------------------------------------
# A station field, per side, of how hard this piece of ground gets used when a car
# misses the apex.  It peaks on the OUTSIDE of a corner and about 45 m PAST the geometric
# apex, because that is where a car that has run out of road actually arrives.  It drives
# three things: the ground's rubber/soil staining, the grass scatter's density and its
# dryness, and where gravel dragged out of the traps ends up.

def _build_scuff():
    S = np.arange(0.0, C.LAP, 1.0)
    _, _, _, k = C.centreline_arrays(S)
    a = np.abs(k)
    hard = np.clip((a - 0.0035) / (0.0160 - 0.0035), 0.0, 1.0)   # R 286 m -> R 62 m
    hard = hard * hard * (3.0 - 2.0 * hard)
    # push the peak downstream of the apex and give it a long tail
    off = np.arange(-60, 161)
    ker = np.exp(-0.5 * ((off - 45.0) / 42.0) ** 2); ker /= ker.sum()
    pad = np.concatenate([hard[-200:], hard, hard[:200]])
    hs = np.convolve(pad, ker, mode="same")[200:-200]
    out = {}
    ker2 = np.exp(-0.5 * (np.arange(-90, 91) / 28.0) ** 2); ker2 /= ker2.sum()
    for side in (+1, -1):
        v = hs * (np.sign(k) == -side)          # outside of the turn
        pad = np.concatenate([v[-200:], v, v[:200]])
        out[side] = np.convolve(pad, ker2, mode="same")[200:-200]
    return S, out


_SCUFF_S, _SCUFF = _build_scuff()


def scuff(s, side):
    """0..1 how hard cars use the ground on `side` at station `s`."""
    return np.interp(np.asarray(s, float) % C.LAP, _SCUFF_S, _SCUFF[side],
                     period=C.LAP)


def scuff_u(s, u):
    """`scuff` for a SIGNED lateral offset."""
    return np.where(u >= 0.0, scuff(s, +1), scuff(s, -1))


def ground_attributes(x, y, z, at):
    """Per-vertex surface description.  Not one grey line: thirteen masks."""
    Dp = at["Dp"]; plateau = at["plateau"]; built = at["built"]
    slope = at.get("slope", np.zeros(len(x)))
    D = at["D"]
    scf = scuff_u(at["s"], at["u"]) * smoothstep(70.0, 8.0, Dp)

    fid, fdist = field_pattern(x, y)

    # moisture: low ground and the hollow are damp, ridges and the escarpment are dry,
    # and the drainage swale itself runs wet along its invert
    wet = smoothstep(1.5, -4.0, z) * 0.7 + 0.3 * smoothstep(
        0.35, 0.0, np.abs(fbm(x / 340.0, y / 340.0, 2, seed=131)))
    wet = np.maximum(wet, 0.85 * np.exp(-(((Dp - DITCH_AT) / (DITCH_SIG * 0.8)) ** 2))
                     * smoothstep(DITCH_HOLD[0], DITCH_HOLD[1], Dp))
    wet = np.clip(wet, 0, 1)

    # wear: the marshals' walkway and the service strip run immediately behind the
    # barrier line, which is 0-10 m outboard of the rim, NOT 26 m from a platform edge
    # that no longer exists
    # the marshals' walkway and the service strip run immediately behind the barrier.
    # 0.80 over 11 m read as bare tan soil for the whole shoulder in `before/
    # t10_rim_bare.png`; a real service strip is a mown, thin, trodden band, not a
    # scrape.
    wear = smoothstep(9.0, 1.5, Dp) * 0.52
    wear = np.maximum(wear, built * 0.6)
    wear = np.maximum(wear, scf * 0.62)                       # run-wide scuffing
    trackway = smoothstep(0.6, 0.0, np.abs(fbm(x / 90.0, y / 90.0, 2, seed=211) - 0.16))
    wear = np.clip(wear + 0.45 * trackway * smoothstep(60.0, 200.0, D)
                   * (1 - plateau * 0.5), 0, 1)

    # stone: field stone and scree, on steep ground, on the escarpment shoulder and in
    # patches out in the fields where the plough turns them up
    rock = smoothstep(0.16, 0.42, slope)
    rock = np.maximum(rock, 0.55 * smoothstep(0.10, 0.30, slope)
                      * smoothstep(0.30, 0.62, fbm(x / 74.0, y / 74.0, 3, seed=419)))
    rock = np.maximum(rock, 0.42 * smoothstep(0.42, 0.74, fbm(x / 128.0, y / 128.0,
                                                              3, seed=421))
                      * smoothstep(70.0, 230.0, D))
    rock = np.clip(rock * (1.0 - 0.85 * plateau) * (1.0 - built), 0, 1)

    # grass cover: thin where worn, on steep ground, on stone and where cars run wide
    cover = np.clip(1.0 - wear * 0.9, 0, 1)
    cover *= 0.55 + 0.45 * (0.5 + 0.5 * fbm(x / 46.0, y / 46.0, 3, seed=307))
    cover *= (1.0 - 0.75 * rock)
    cover = np.clip(cover, 0, 1)

    # moss and low herbage in the damp shade of the hedge lines and the swale
    moss = np.clip(wet * smoothstep(0.25, 0.75, fbm(x / 19.0, y / 19.0, 3, seed=523))
                   * (1.0 - 0.6 * wear), 0, 1)

    # mown: the verges behind the barrier are cut, the outfield is not
    mown = smoothstep(34.0, 3.0, Dp)
    mown = np.maximum(mown, built)

    # crop / pasture colour per field, hedgerow darkening at the boundary
    hedge = smoothstep(9.0, 1.5, fdist) * smoothstep(150.0, 340.0, D)

    # ---- THE FIELD COLOUR ------------------------------------------------  R2-1661
    #
    # WHAT WAS WRONG WITH IT.  Three things compounded, and all three were
    # quantisation:
    #
    #   1. `fam = floor(fid * 3)` picked ONE OF THREE colours per field.  A field is
    #      155 m across (see `field_pattern`); at beat 6's 99 m and 22 mm that is a
    #      third of the frame in one flat value, and there were only three values in
    #      the world.
    #   2. Those three were 0.150 / 0.230 / 0.222 in luminance -- a 53 % step between
    #      neighbours, measured at 20-25 CV p5-p95 over half the frame.
    #   3. `dry` was ALSO 0.15 + 0.85 * fid, so one random number drove both the
    #      family and the hay/straw mix and the two reinforced each other.  One
    #      number, one boundary, two coincident steps.
    #
    # WHAT IT IS NOW.  The palette is a CLOSED LOOP walked continuously by `fid`, so
    # every field takes its own colour off a 1-D manifold and there is no
    # quantisation left to make a blotch.  The loop is compressed to 0.168 / 0.211 /
    # 0.206 in luminance -- a 26 % step, half what it was -- with the family
    # difference carried in HUE, because fields genuinely do differ and hue is how a
    # boundary reads as a boundary instead of as a brightness patch.  `dry` comes off
    # an independent hash.  And two unquantised tints at 190 m and 64 m multiply the
    # whole thing and DO NOT respect the field partition, which is what stops the eye
    # locking onto it.
    #
    # NOT A GRADE FIX, AND IT COULD NOT HAVE BEEN ONE.  Under the closing haze
    # asphalt and field measure 0.367/0.333/0.246 against 0.380/0.354/0.263; anything
    # applied downstream to separate those takes the car's 0.14 blue-minus-red break
    # with it, and that colour break is the whole reason the car is legible at 63 px.
    # This is upstream of the grade, on the ground's own albedo, and touches nothing
    # else in the frame.
    fdry = hash_field(fid, 3119)                      # INDEPENDENT of the family
    dry = np.clip(0.12 + 0.80 * fdry, 0, 1)

    pal = np.array([[0.108, 0.196, 0.062],     # deep pasture     lum 0.168
                    [0.216, 0.222, 0.088],     # hay meadow       lum 0.211
                    [0.268, 0.198, 0.100]])    # cut / stubble    lum 0.206
    fc = fid * 3.0
    i0 = np.floor(fc).astype(int) % 3
    w = (fc - np.floor(fc))[:, None]
    col = pal[i0] * (1.0 - w) + pal[(i0 + 1) % 3] * w
    # per-field value and warmth jitter, so two fields that land near each other on
    # the loop are still not the same colour
    col = col * (1.0 + (hash_field(fid, 971) - 0.5) * 0.19)[:, None]
    warm = (hash_field(fid, 4441) - 0.5) * 0.13
    col = col * np.stack([1.0 + warm, 1.0 + 0.15 * warm, 1.0 - 0.9 * warm], 1)
    # drainage and subsoil at 190 m and 64 m, CROSSING the hedges.  Farmland's
    # strongest large-scale tone variation is the soil under it, and soil does not
    # stop at a field boundary.  This is the term that turns a partition back into a
    # landscape.
    soilv = (0.5 + 0.5 * fbm(x / 190.0, y / 190.0, 3, seed=1661)) * 0.30 \
        + (0.5 + 0.5 * fbm(x / 64.0, y / 64.0, 3, seed=1662)) * 0.16
    col = np.clip(col * (0.79 + soilv)[:, None], 0.0, 1.0)

    # ---- the crop's own grain -------------------------------------------------
    # A per-field row direction and a headland band, handed to `mat_ground` so that
    # the swathes, the tramlines and the worked margin are drawn per shading point
    # rather than per vertex: the ground grid is 2.5 m and a tramline is 1.7 m wide,
    # so this pattern cannot live in a vertex attribute.  Interpolating (cos, sin)
    # across a boundary shortens the vector, which fades the grain out exactly where
    # the hedge is, which is where it should fade.
    # THE VECTOR CARRIES THE SPACING AS WELL AS THE DIRECTION, and it is free.
    # Storing k * (cos, sin) instead of the unit vector scales the rotated coordinate
    # by k, so ONE per-field number moves the swathe period off 5.2 m and the tramline
    # period off 21 m together and in proportion -- exactly as a different machine on
    # a different farm would.  Without it every field in the world is worked at the
    # same spacing and only the angle changes, which is a pattern and not a landscape.
    # Packed at 0.35 rather than 0.5 because |k| reaches 1.35 and the channel is 0..1.
    fang = hash_field(fid, 7717) * 2.0 * np.pi
    krow = 0.75 + 0.60 * hash_field(fid, 5231)      # swathes 3.9-6.9 m, trams 16-28 m
    head = smoothstep(34.0, 6.0, fdist)
    crop = np.stack([np.cos(fang) * krow * 0.35 + 0.5,
                     np.sin(fang) * krow * 0.35 + 0.5, head], 1)

    return dict(ter_wet=wet.astype(np.float64), ter_wear=wear, ter_cover=cover,
                ter_mown=mown, ter_hedge=hedge, ter_dry=dry, ter_field=col,
                ter_crop=crop,
                ter_dist=np.clip(D / 400.0, 0, 1), ter_plateau=plateau,
                ter_rock=rock, ter_moss=moss, ter_scuff=np.clip(scf, 0, 1),
                ter_slope=np.clip(slope, 0, 1.2))


def hash_field(fid, k=0):
    v = np.sin(fid * 127.1 + k * 0.0173) * (43758.5453 + k)
    return v - np.floor(v)


# ==================================================================================
# 6.  PLANT GEOMETRY — every species is generated, none is duplicated
# ==================================================================================

UP = np.array([0.0, 0.0, 1.0])


class Accum:
    """Vertex/face accumulator with per-face material index and per-vertex attrs."""

    def __init__(self):
        self.V = []; self.T = []; self.Q = []
        self.TM = []; self.QM = []
        self.A = []          # per-vertex float attribute (blade/leaf id)
        self.G = []          # per-vertex float attribute (height along plant, 0..1)
        self.n = 0

    def add(self, v, tris=None, quads=None, mat=0, attr=None, grad=None):
        o = self.n
        v = np.asarray(v, float)
        self.V.append(v)
        if tris is not None and len(tris):
            self.T.append(np.asarray(tris, np.int64) + o)
            self.TM.append(np.full(len(tris), mat, np.int32))
        if quads is not None and len(quads):
            self.Q.append(np.asarray(quads, np.int64) + o)
            self.QM.append(np.full(len(quads), mat, np.int32))
        self.A.append(np.zeros(len(v)) if attr is None else np.asarray(attr, float))
        self.G.append(np.zeros(len(v)) if grad is None else np.asarray(grad, float))
        self.n += len(v)

    def finish(self, name, mat_names):
        V = np.concatenate(self.V) if self.V else np.zeros((0, 3))
        Q = np.concatenate(self.Q) if self.Q else np.zeros((0, 4), np.int64)
        T = np.concatenate(self.T) if self.T else np.zeros((0, 3), np.int64)
        QM = np.concatenate(self.QM) if self.QM else np.zeros(0, np.int32)
        TM = np.concatenate(self.TM) if self.TM else np.zeros(0, np.int32)
        me = new_mesh_arrays(name, V, T, Q)
        if len(QM) + len(TM):
            me.polygons.foreach_set("material_index", np.concatenate([QM, TM]))
        A = np.concatenate(self.A) if self.A else np.zeros(0)
        G = np.concatenate(self.G) if self.G else np.zeros(0)
        a = me.attributes.new("pid", "FLOAT", "POINT"); a.data.foreach_set("value", A.astype(np.float32))
        g = me.attributes.new("pgrad", "FLOAT", "POINT"); g.data.foreach_set("value", G.astype(np.float32))
        for mn in mat_names:
            me.materials.append(bpy.data.materials[mn])
        me.update()
        return me


def _norm(v):
    n = np.linalg.norm(v, axis=-1, keepdims=True)
    return v / np.maximum(n, 1e-9)


def _frames(pts):
    """Parallel-transported orthonormal frames along a polyline (k,3)."""
    k = len(pts)
    t = np.zeros((k, 3))
    t[:-1] = pts[1:] - pts[:-1]
    t[-1] = t[-2]
    t = _norm(t)
    u = np.zeros((k, 3)); v = np.zeros((k, 3))
    ref = np.array([0.0, 1.0, 0.0])
    if abs(np.dot(t[0], ref)) > 0.9:
        ref = np.array([1.0, 0.0, 0.0])
    u[0] = _norm(np.cross(t[0], ref)); v[0] = np.cross(t[0], u[0])
    for i in range(1, k):
        pu = u[i - 1] - t[i] * np.dot(u[i - 1], t[i])
        n = np.linalg.norm(pu)
        u[i] = pu / n if n > 1e-6 else _norm(np.cross(t[i], ref))
        v[i] = np.cross(t[i], u[i])
    return t, u, v


def tube(acc, pts, rads, sides, mat, gmin=0.0, gmax=1.0, close_tip=True):
    pts = np.asarray(pts, float); rads = np.asarray(rads, float)
    k = len(pts)
    t, u, v = _frames(pts)
    th = np.linspace(0, 2 * math.pi, sides, endpoint=False)
    ct, st = np.cos(th), np.sin(th)
    V = (pts[:, None, :]
         + rads[:, None, None] * (ct[None, :, None] * u[:, None, :]
                                  + st[None, :, None] * v[:, None, :])).reshape(-1, 3)
    i = np.arange(k - 1)[:, None] * sides + np.arange(sides)[None, :]
    j = (np.arange(sides) + 1) % sides
    q = np.stack([i, i + sides, np.arange(k - 1)[:, None] * sides + sides + j[None, :],
                  np.arange(k - 1)[:, None] * sides + j[None, :]], -1).reshape(-1, 4)
    g = np.repeat(np.linspace(gmin, gmax, k), sides)
    tris = None
    if close_tip:
        V = np.concatenate([V, pts[-1:]], 0)
        tip = len(V) - 1
        base = (k - 1) * sides
        tris = np.stack([np.full(sides, tip), base + np.arange(sides), base + j], -1)
        g = np.concatenate([g, [gmax]])
    acc.add(V, tris=tris, quads=q, mat=mat, grad=g)


# --- leaf templates -----------------------------------------------------------------
def _leaf_broad(width=0.62, lobes=0.0):
    """Six verts, four triangles, folded along the midrib and curled at the tip.

    A canopy needs many thousands of these, so a blade is as cheap as a blade can be
    while still holding a real outline and a real normal.  (A ten-triangle version
    cost 2.5x for detail invisible past 25 m; trees never come closer than ~40 m to
    the camera path.)
    """
    w = width
    V = np.array([
        [0.00,  0.000,      0.000],
        [0.30,  0.42 * w,  -0.016], [0.68,  0.50 * w, -0.040],
        [1.00,  0.000,     -0.062],
        [0.68, -0.50 * w,  -0.040], [0.30, -0.42 * w, -0.016],
    ])
    if lobes > 0:
        V[1, 1] *= 1.0 + 0.22 * lobes; V[5, 1] *= 1.0 + 0.22 * lobes
        V[2, 0] += 0.06 * lobes; V[4, 0] += 0.06 * lobes
    T = np.array([[0, 1, 2], [0, 2, 3], [0, 3, 4], [0, 4, 5]])
    G = np.array([0.0, 0.30, 0.68, 1.0, 0.68, 0.30])
    return V, T, G


def _leaf_needle(n=3, spread=0.28, w=0.030):
    V = []; T = []; G = []
    for i in range(n):
        a = (i - (n - 1) / 2.0) * spread
        c, s = math.cos(a), math.sin(a)
        base = len(V)
        V += [[0.0, -w * 0.55, 0.0], [0.0, w * 0.55, 0.0],
              [c * 1.0, s * 1.0 - w * 0.30, -0.10 * abs(a)], [c * 1.0, s * 1.0 + w * 0.30, -0.10 * abs(a)]]
        T += [[base, base + 1, base + 3], [base, base + 3, base + 2]]
        G += [0.0, 0.0, 1.0, 1.0]
    return np.array(V), np.array(T), np.array(G)


def _leaf_brush(n=12, w=0.030, cone=0.80, taper=0.55):
    """A conifer SHOOT, not a flat spray: needles radiate around the axis in 3-D so
    the sprite reads as foliage from any angle.  A planar fan disappeared edge-on and
    made the pines look like bare wire."""
    V = []; T = []; G = []
    for i in range(n):
        th = i * 2.399963  # golden angle, so no two needles overlap
        f = 0.55 + 0.45 * ((i * 7 % n) / float(n))
        ax = np.array([1.0, math.cos(th) * cone, math.sin(th) * cone])
        ax = ax / np.linalg.norm(ax)
        sd = np.cross(ax, [0.0, 0.0, 1.0])
        nn = np.linalg.norm(sd)
        sd = sd / nn if nn > 1e-6 else np.array([0.0, 1.0, 0.0])
        b = len(V)
        st = np.array([0.10 * f, 0.0, 0.0])
        en = st + ax * f
        V += list(st - sd * w * 0.5) and [list(st - sd * w * 0.5), list(st + sd * w * 0.5),
                                          list(en + sd * w * taper * 0.5), list(en - sd * w * taper * 0.5)]
        T += [[b, b + 1, b + 2], [b, b + 2, b + 3]]
        G += [0.0, 0.0, 1.0, 1.0]
    return np.array(V), np.array(T), np.array(G)


def _leaf_scale():
    V = np.array([[0.0, -0.05, 0.0], [0.0, 0.05, 0.0], [0.6, 0.07, 0.03],
                  [0.6, -0.07, 0.03], [1.0, 0.0, 0.0]])
    T = np.array([[0, 1, 2], [0, 2, 3], [3, 2, 4]])
    G = np.array([0.0, 0.0, 0.6, 0.6, 1.0])
    return V, T, G


def _leaf_pinnate(pairs=4, leaflet=0.30):
    """Compound leaf (ash / rowan): a rachis carrying paired leaflets."""
    lv, lt, lg = _leaf_broad(0.42)
    V = [np.array([[0, 0, 0], [1.0, 0, -0.05]])]
    T = []; G = [np.array([0.0, 1.0])]
    n = 2
    for i in range(pairs):
        f = 0.22 + 0.76 * i / max(1, pairs - 1)
        for sgn in (-1, 1):
            a = math.radians(58.0) * sgn
            R = np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])
            vv = (lv * leaflet) @ R.T + np.array([f, 0, -0.02 - 0.03 * f])
            V.append(vv); T.append(lt + n); G.append(lg)
            n += len(vv)
    return np.concatenate(V), np.concatenate(T), np.concatenate(G)


LEAF_TEMPLATES = {
    "broad":   _leaf_broad(0.62),
    "broadw":  _leaf_broad(0.92, lobes=1.0),
    "conif":   _leaf_broad(0.55),
    "conifs":  _leaf_broad(0.52),     # oak / plane: wide, lobed
    "narrow":  _leaf_broad(0.40),                # willow
    "small":   _leaf_broad(0.60),
    "needle":  _leaf_needle(3, 0.34, 0.026),
    "needle5": _leaf_brush(14, 0.030, 0.85, 0.5),
    "brushfine": _leaf_brush(10, 0.024, 0.95, 0.5),
    "scale":   _leaf_brush(11, 0.038, 1.05, 0.7),
    "pinnate": _leaf_pinnate(3, 0.34),
}


def place_leaves(acc, pos, fwd, side, up, size, mat, rng):
    """Instance a leaf template on (m) frames, vectorised."""
    tpl, tri, grad = LEAF_TEMPLATES[mat[1]]
    m = len(pos)
    if m == 0:
        return
    sz = size[:, None]
    V = (pos[:, None, :]
         + (tpl[None, :, 0:1] * fwd[:, None, :]
            + tpl[None, :, 1:2] * side[:, None, :]
            + tpl[None, :, 2:3] * up[:, None, :]) * sz[:, None, :]).reshape(-1, 3)
    T = (tri[None, :, :] + (np.arange(m) * len(tpl))[:, None, None]).reshape(-1, 3)
    pid = np.repeat(rng.random(m), len(tpl))
    G = np.tile(grad, m)
    acc.add(V, tris=T, mat=mat[0], attr=pid, grad=G)


# ----------------------------------------------------------------------------------
# 6.1  SPECIES
# ----------------------------------------------------------------------------------
# Each entry is a genuinely different growth habit, not a re-parameterised clone:
# branching topology (spiral / whorled / opposite / multi-stem), gravitropism sign,
# taper law, crown envelope and leaf morphology all differ.

SPECIES = {
    "oak": dict(
        label="pedunculate oak", h=(12.0, 21.0), dbh=0.0152, trunk=0.22, depth=6,
        children=(4, 4, 4, 4, 5), angle=(36, 62), roll="spiral",
        grav=(0.12, 0.16, 0.20, 0.24, 0.26),
        taper=0.58, seg=(7, 5, 4, 3, 3, 2), sides=(11, 7, 5, 4, 4, 3),
        clear=0.24, curl=0.30, lenr=(0.92, 0.70, 0.64, 0.60, 0.58),
        crown=1.35, leaf="broadw", leafsz=(0.101, 0.168),
        leafn=(29000, 9425, 0), bark="oak", canopy=(0.62, 0.30), wind=0.5),
    "poplar": dict(
        label="lombardy poplar", h=(16.0, 27.0), dbh=0.0105, trunk=0.62, depth=5,
        children=(10, 4, 4, 5), angle=(13, 26), roll="spiral",
        grav=(0.88, 0.82, 0.74, 0.62),
        taper=0.70, seg=(11, 5, 4, 3, 2), sides=(9, 6, 4, 4, 3),
        clear=0.12, curl=0.10, lenr=(0.46, 0.58, 0.60, 0.60),
        crown=0.34, leaf="broad", leafsz=(0.074, 0.120),
        leafn=(33000, 10500, 0), bark="poplar", canopy=(0.30, 0.85), wind=0.8),
    "pine": dict(
        label="scots pine", h=(13.0, 23.0), dbh=0.0122, trunk=0.50, depth=5,
        children=(8, 5, 5, 6), angle=(56, 84), roll="whorl",
        grav=(-0.05, 0.08, 0.14, 0.16),
        taper=0.62, seg=(10, 4, 3, 3, 2), sides=(10, 6, 4, 4, 3),
        clear=0.46, curl=0.16, lenr=(0.54, 0.68, 0.66, 0.62),
        crown=1.28, leaf="conif", leafsz=(0.130, 0.210),
        leafn=(26000, 8600, 0), bark="pine", canopy=(0.85, 0.42), wind=0.35),
    "birch": dict(
        label="silver birch", h=(8.0, 16.5), dbh=0.0092, trunk=0.32, depth=6,
        children=(4, 4, 4, 4, 5), angle=(26, 46), roll="spiral",
        grav=(0.28, -0.18, -0.40, -0.62, -0.80),
        taper=0.60, seg=(9, 5, 4, 3, 3, 2), sides=(9, 6, 4, 4, 3, 3),
        clear=0.26, curl=0.42, lenr=(0.72, 0.64, 0.64, 0.64, 0.66),
        crown=0.85, leaf="small", leafsz=(0.062, 0.102),
        leafn=(38000, 12500, 0), bark="birch", canopy=(0.55, 0.45), wind=1.0),
    "plane": dict(
        label="london plane", h=(12.0, 20.0), dbh=0.0156, trunk=0.34, depth=6,
        children=(3, 4, 4, 4, 5), angle=(28, 52), roll="opposite",
        grav=(0.32, 0.26, 0.20, 0.18, 0.16),
        taper=0.56, seg=(7, 5, 4, 3, 3, 2), sides=(12, 7, 5, 4, 4, 3),
        clear=0.44, curl=0.22, lenr=(0.86, 0.70, 0.64, 0.60, 0.58),
        crown=1.20, leaf="broadw", leafsz=(0.127, 0.208),
        leafn=(26100, 8700, 0), bark="plane", canopy=(0.70, 0.28), wind=0.5),
    "cypress": dict(
        label="italian cypress", h=(7.0, 14.5), dbh=0.0090, trunk=0.74, depth=4,
        children=(15, 6, 6), angle=(8, 19), roll="spiral", grav=(0.94, 0.88, 0.80),
        taper=0.74, seg=(12, 5, 3, 2), sides=(8, 5, 3, 3),
        clear=0.06, curl=0.06, lenr=(0.34, 0.56, 0.60),
        crown=0.22, leaf="conifs", leafsz=(0.090, 0.140),
        leafn=(24000, 8000, 0), bark="cypress", canopy=(0.22, 0.92), wind=0.25),
    "willow": dict(
        label="crack willow", h=(8.0, 15.0), dbh=0.0142, trunk=0.22, depth=6,
        children=(4, 4, 4, 5, 5), angle=(32, 58), roll="spiral",
        grav=(0.30, -0.25, -0.52, -0.80, -1.05),
        taper=0.58, seg=(6, 5, 4, 3, 3, 2), sides=(11, 7, 5, 4, 3, 3),
        clear=0.20, curl=0.55, lenr=(0.86, 0.72, 0.70, 0.74, 0.80),
        crown=1.05, leaf="narrow", leafsz=(0.100, 0.170),
        leafn=(34000, 11000, 0), bark="willow", canopy=(0.75, 0.36), wind=1.3),
    "hawthorn": dict(
        label="hawthorn", h=(2.8, 6.2), dbh=0.020, trunk=0.20, depth=5,
        children=(4, 4, 4, 5), angle=(40, 76), roll="spiral",
        grav=(0.18, 0.12, 0.08, 0.05, 0.02),
        taper=0.56, seg=(5, 4, 3, 3, 2), sides=(8, 5, 4, 3, 3),
        clear=0.12, curl=0.58, lenr=(0.80, 0.64, 0.60, 0.58, 0.56),
        crown=1.45, leaf="small", leafsz=(0.046, 0.076),
        leafn=(24000, 8000, 0), bark="hawthorn", canopy=(0.85, 0.30), wind=0.7,
        multi=(2, 4)),
    "rowan": dict(
        label="rowan", h=(7.0, 13.0), dbh=0.0110, trunk=0.30, depth=5,
        children=(4, 4, 4, 4), angle=(28, 52), roll="opposite",
        grav=(0.36, 0.26, 0.20, 0.16),
        taper=0.60, seg=(7, 5, 4, 3, 2), sides=(9, 6, 4, 3, 3),
        clear=0.34, curl=0.24, lenr=(0.78, 0.66, 0.62, 0.58),
        crown=0.92, leaf="pinnate", leafsz=(0.150, 0.235),
        leafn=(4600, 1550, 0), bark="rowan", canopy=(0.60, 0.42), wind=0.6),
    "snag": dict(
        label="dead standing timber", h=(5.5, 14.0), dbh=0.0165, trunk=0.72, depth=4,
        children=(5, 3, 2), angle=(32, 78), roll="spiral", grav=(0.05, -0.12, -0.25),
        taper=0.50, seg=(11, 6, 4, 3), sides=(10, 6, 4, 3),
        clear=0.26, curl=0.36, lenr=(0.46, 0.42, 0.40),
        crown=0.85, leaf=None, leafsz=(0, 0),
        leafn=(0, 0, 0), bark="snag", canopy=(0.5, 0.5), wind=0.4, broken=True),
    "sapling": dict(
        label="sapling", h=(1.4, 4.2), dbh=0.0125, trunk=0.42, depth=4,
        children=(4, 4, 3), angle=(28, 58), roll="spiral", grav=(0.44, 0.34, 0.26),
        taper=0.62, seg=(6, 4, 3, 2), sides=(7, 5, 3, 3),
        clear=0.18, curl=0.35, lenr=(0.66, 0.58, 0.54),
        crown=0.95, leaf="broad", leafsz=(0.057, 0.094),
        leafn=(1950, 728, 0), bark="birch", canopy=(0.6, 0.5), wind=1.2),
}

SHRUBS = {
    "bramble": dict(h=(0.7, 1.7), depth=3, children=(6, 4), angle=(48, 88),
                    grav=(-0.30, -0.60), lenr=(0.62, 0.66), sides=(5, 4, 3),
                    seg=(5, 4, 3), leaf="small", leafsz=(0.035, 0.060), leafn=(520, 240),
                    bark="hawthorn", stems=(3, 7), taper=0.72),
    "gorse":   dict(h=(0.6, 1.9), depth=3, children=(7, 4), angle=(24, 52),
                    grav=(0.35, 0.20), lenr=(0.52, 0.52), sides=(5, 4, 3),
                    seg=(5, 3, 3), leaf="brushfine", leafsz=(0.048, 0.075), leafn=(420, 190),
                    bark="hawthorn", stems=(4, 9), taper=0.70),
    "hazel":   dict(h=(1.6, 3.6), depth=3, children=(4, 4), angle=(28, 56),
                    grav=(0.55, 0.28), lenr=(0.58, 0.58), sides=(6, 4, 3),
                    seg=(6, 4, 3), leaf="broad", leafsz=(0.060, 0.100), leafn=(760, 320),
                    bark="hawthorn", stems=(3, 8), taper=0.74),
    "broom":   dict(h=(0.5, 1.4), depth=2, children=(9,), angle=(12, 34),
                    grav=(0.70,), lenr=(0.58,), sides=(4, 3), seg=(5, 3),
                    leaf="scale", leafsz=(0.030, 0.045), leafn=(520, 220),
                    bark="hawthorn", stems=(5, 12), taper=0.76),
    "juniper": dict(h=(0.6, 1.6), depth=2, children=(8,), angle=(46, 82),
                    grav=(0.10,), lenr=(0.62,), sides=(5, 3), seg=(4, 3),
                    leaf="brushfine", leafsz=(0.055, 0.085), leafn=(420, 190),
                    bark="pine", stems=(2, 5), taper=0.68),
}


def _branch(acc, sp, rng, p, dirv, length, radius, depth, lod, leafbank, wind, roll0=0.0):
    """Recursive branch.  Appends geometry into `acc`; records terminal twigs."""
    dmax = sp["depth"] - 1
    nseg = max(2, sp["seg"][min(depth, len(sp["seg"]) - 1)] - (1 if lod else 0))
    sides = max(3, sp["sides"][min(depth, len(sp["sides"]) - 1)] - (2 if lod == 1 else 0))
    grav = sp["grav"][min(depth, len(sp["grav"]) - 1)]
    curl = sp["curl"] * (1.0 + 0.5 * depth / max(1, dmax))
    pts = [p.copy()]; rr = [radius]
    d = dirv.copy()
    step = length / nseg
    for i in range(nseg):
        # Scale-invariant shaping: each term accumulates to a fixed amount over the
        # branch regardless of its length, so a 9 m limb and a 0.3 m twig share the
        # species' curvature signature instead of the twig coming out dead straight.
        d = d + UP * (grav / nseg)
        d = d + wind * (sp["wind"] * 0.06 * (0.3 + 0.7 * (depth / max(1, dmax))) / nseg)
        d = d + (rng.random(3) - 0.5) * (curl * 1.6 / nseg)
        d = _norm(d)
        p = pts[-1] + d * step
        pts.append(p.copy())
        rr.append(radius * (sp["taper"] ** ((i + 1) / nseg * 1.15)))
    pts = np.array(pts); rr = np.array(rr)
    if depth == 0:
        rr[0] *= 1.24; rr[1] *= 1.08          # root flare
    g0 = depth / max(1.0, dmax)
    tube(acc, pts, rr, sides, 0, gmin=g0, gmax=min(1.0, g0 + 1.0 / max(1, dmax)))

    if depth >= dmax - 1:
        leafbank.append((pts, rr, depth))
    if depth >= dmax:
        return

    nch = sp["children"][min(depth, len(sp["children"]) - 1)]
    if lod == 1 and depth >= dmax - 1:
        nch = max(2, nch - 1)
    a0, a1 = sp["angle"]
    clear = sp["clear"] if depth == 0 else 0.16
    roll = roll0
    for c in range(nch):
        f = clear + (1.0 - clear) * ((c + 0.5 + 0.6 * (rng.random() - 0.5)) / nch)
        f = min(0.99, max(0.05, f))
        idx = f * (len(pts) - 1)
        i0 = int(idx); tfr = idx - i0
        i1 = min(i0 + 1, len(pts) - 1)
        base = pts[i0] * (1 - tfr) + pts[i1] * tfr
        pdir = _norm(pts[min(i0 + 1, len(pts) - 1)] - pts[i0]) if i0 + 1 < len(pts) else d
        # roll about the parent axis
        if sp["roll"] == "spiral":
            roll += math.radians(137.5) + rng.normal(0, 0.30)
        elif sp["roll"] == "opposite":
            roll += math.pi + (math.radians(90.0) if c % 2 == 1 else 0.0) + rng.normal(0, 0.16)
        else:                                   # whorl
            roll = roll0 + c * 2 * math.pi / nch + rng.normal(0, 0.13)
        ref = np.array([0.0, 0.0, 1.0])
        if abs(pdir[2]) > 0.94:
            ref = np.array([1.0, 0.0, 0.0])
        e1 = _norm(np.cross(pdir, ref)); e2 = np.cross(pdir, e1)
        lat = math.cos(roll) * e1 + math.sin(roll) * e2
        # the leader keeps going: on excurrent species the first child continues the axis
        ang = math.radians(rng.uniform(a0, a1))
        if depth == 0 and sp["crown"] < 0.5 and c == nch - 1:
            ang *= 0.25
        cdir = _norm(pdir * math.cos(ang) + lat * math.sin(ang))
        clen = length * sp["lenr"][min(depth, len(sp["lenr"]) - 1)] * rng.uniform(0.74, 1.16)
        # A child is a fraction of the parent's radius WHERE IT ATTACHES, never of the
        # parent's base radius -- otherwise a twig springing from the thin end of a
        # limb comes out thicker than the limb, which is what made the first pass look
        # like a coral instead of a tree.
        r_at = radius * (sp["taper"] ** (f * 1.15))
        crad = r_at * (0.52 + 0.20 * (1.0 - f)) * rng.uniform(0.86, 1.08)
        clen *= (1.0 - 0.34 * f) * sp["crown"] ** 0.22
        _branch(acc, sp, rng, base, cdir, clen, crad, depth + 1, lod, leafbank, wind, roll)


def gen_tree(key, rng, lod, height=None):
    """One unique tree.  lod 0 = hero, 1 = mid, 2 = distant canopy shells."""
    sp = SPECIES[key]
    acc = Accum()
    h = height if height is not None else rng.uniform(*sp["h"])
    rad = h * sp["dbh"] * rng.uniform(0.84, 1.18)
    # wind flagging: exposed specimens lean and their crowns stream downwind
    wind = np.array([WIND_DIR[0], WIND_DIR[1], 0.0]) * rng.uniform(0.35, 1.5)
    lean = np.array([WIND_DIR[0], WIND_DIR[1], 0.0]) * rng.uniform(0.01, 0.09) \
        + np.array([rng.normal(0, 0.045), rng.normal(0, 0.045), 0.0])
    d0 = _norm(UP + lean)
    leafbank = []

    stems = 1
    if sp.get("multi"):
        stems = int(rng.integers(sp["multi"][0], sp["multi"][1] + 1))
    for st in range(stems):
        a = rng.uniform(0, 2 * math.pi)
        off = np.array([math.cos(a), math.sin(a), 0.0]) * (0.0 if stems == 1 else rng.uniform(0.05, 0.32))
        sd = _norm(d0 + off * 1.4)
        off = off - np.array([0.0, 0.0, rad * 1.6 + 0.10])   # bole starts below grade
        hh = h * (1.0 if stems == 1 else rng.uniform(0.62, 1.0))
        _branch(acc, sp, rng, off, sd, hh * sp["trunk"], rad / max(1.0, stems ** 0.55),
                0, lod, leafbank, wind)

    # normalise: the recursion's reach is emergent, so rescale to the drawn height
    V = np.concatenate(acc.V)
    zmax = V[:, 2].max()
    if zmax > 0.2:
        k = h / zmax
        for i in range(len(acc.V)):
            acc.V[i] = acc.V[i] * k
        for i in range(len(leafbank)):
            leafbank[i] = (leafbank[i][0] * k, leafbank[i][1] * k, leafbank[i][2])

    if sp.get("broken"):
        pass
    elif lod == 2:
        _canopy_shells(acc, sp, rng, h, leafbank)
    elif sp["leaf"]:
        target = int(sp["leafn"][lod] * LEAF_DENSITY[lod] * rng.uniform(0.74, 1.20))
        _dress_leaves(acc, sp, rng, leafbank, target, wind)

    mats = [VPFX + "bark_" + sp["bark"]]
    mats.append(VPFX + "leaf_" + key if sp["leaf"] else VPFX + "bark_" + sp["bark"])
    # slot 2 is the L2 canopy shell.  It is NOT the leaf material: a shell shaded with
    # the leaf shader is an opaque blob, and an opaque blob throws an opaque shadow --
    # which is the whole of "tree shadows are mushy blobs".  See mat_canopy.
    mats.append(VPFX + "canopy_" + key if sp["leaf"] else VPFX + "bark_" + sp["bark"])
    me = acc.finish(VPFX + "tree_%s_L%d_%04d" % (key, lod, rng.integers(0, 1 << 30) % 9999), mats)
    return me, h


def _dress_leaves(acc, sp, rng, leafbank, target, wind):
    if not leafbank or target <= 0:
        return
    tot = sum(max(1, len(p) - 1) for p, r, d in leafbank)
    per = max(1, int(round(target / tot)))
    P = []; F = []; S = []; U = []; SZ = []
    # THE VIRTUAL SHOOT.  The recursion stops at 4-6 orders, so every leaf used to be
    # pinned within a couple of millimetres of one of ~1500 terminal twigs: 29 000 leaves
    # on 460 m of twig, which is a correct leaf-area index arranged as ropes.  The tree
    # read as a bare skeleton with green string on it.  A real tree has one more order --
    # the season's unlignified shoots -- carrying the leaves out into the crown volume.
    # Modelling those as geometry costs another 5x of branches for something 40 m from
    # the lens; instead each terminal segment sprouts a few virtual shoots and the leaves
    # ride along them.  Zero extra branch geometry, and the crown fills.
    shoot_r = 0.55 + 0.85 * sp.get("crown", 1.0)      # spreading crowns fill wider
    for pts, rr, depth in leafbank:
        k = len(pts)
        seg = pts[1:] - pts[:-1]
        for i in range(k - 1):
            n = per + (1 if rng.random() < (target / tot - per) else 0)
            if n <= 0:
                continue
            t = rng.random(n)[:, None]
            base = pts[i] + seg[i] * t
            pdir = _norm(seg[i])
            slen = float(np.linalg.norm(seg[i]))
            ref = np.array([0.0, 0.0, 1.0])
            if abs(pdir[2]) > 0.94:
                ref = np.array([1.0, 0.0, 0.0])
            e1 = _norm(np.cross(pdir, ref)); e2 = np.cross(pdir, e1)
            roll = rng.random(n) * 2 * math.pi
            lat = np.cos(roll)[:, None] * e1 + np.sin(roll)[:, None] * e2
            ang = rng.uniform(0.55, 1.32, n)[:, None]
            f = _norm(pdir * np.cos(ang) + lat * np.sin(ang))
            # droop and wind stream
            f = _norm(f + np.array([0, 0, -1.0]) * rng.uniform(0.05, 0.55, n)[:, None]
                      + wind * 0.10)
            s = _norm(np.cross(f, UP + np.array([0.01, 0.01, 0.0])))
            u = np.cross(f, s)
            # leaves are tufted, not evenly spread: a handful of shoot directions per
            # segment, several leaves strung along each, which is how a shoot grows and
            # is also what stops the fill from looking like a spherical fog of leaves
            ns = max(2, n // 4)
            grp = rng.integers(0, ns, n)
            sr = rng.random((ns, 3)) - 0.5
            sd = _norm(pdir[None, :] * 0.55 + sr + np.array([0.0, 0.0, -0.22]))[grp]
            along = (rng.random(n) ** 0.62)[:, None] * (slen * shoot_r)
            P.append(base + lat * (rr[i] * 1.05) + sd * along)
            F.append(f); S.append(s); U.append(u)
            SZ.append(rng.uniform(sp["leafsz"][0], sp["leafsz"][1], n))
    if not P:
        return
    place_leaves(acc, np.concatenate(P), np.concatenate(F), np.concatenate(S),
                 np.concatenate(U), np.concatenate(SZ), (1, sp["leaf"]), rng)


def _canopy_shells(acc, sp, rng, h, leafbank):
    """Distant LOD: the canopy becomes 5-11 noise-deformed shells hung on real tips.

    The first version of this used 3-7 lightly-displaced icospheres and it showed: at
    the Beat-6 hold a 15 m tree a kilometre out still covers ~37 px at 4K, and smooth
    spheres at that size read as a row of green balls floating over white sticks.  Three
    things fix it and all three matter:

      * TWO displacement scales.  A smooth lobe (the crown's big masses) times a
        per-vertex hash spike (the twig tips that make a canopy's edge ragged).  A
        silhouette with only the smooth term is a ball however hard it is deformed.
      * The shells overlap and skirt DOWN past their centres, so the canopy is one
        connected mass with light coming through the bottom, not beads on a stick.
      * They are darker than the hero LOD, not lighter.  A real canopy at a kilometre is
        mostly self-shadowed; the earlier shells took pgrad 0.85 (the sunlit-tip colour)
        and pid ~U(0,1) (mid value), so distant woods came out PALER than near ones,
        which is backwards and was most of why the treeline looked like polystyrene.

    Silhouette still differs per species (crown ratio, count, columnar vs spreading) and
    every shell carries its own noise seed, so no two distant trees share an outline.
    """
    if not leafbank:
        return
    tips = np.array([p[-1] for p, r, d in leafbank])
    if len(tips) == 0:
        return
    zt = tips[:, 2]
    # columnar species stack their masses vertically, spreading species fan them out
    col = 1.0 / (0.35 + sp["crown"])          # cypress/poplar ~2.4, oak/hawthorn ~0.6
    n = int(rng.integers(5, 12))
    # pick tips spread through the crown rather than uniformly at random, so the shells
    # cover the whole envelope instead of clumping wherever the recursion made most tips
    order = np.argsort(zt + rng.normal(0, 0.12 * h, len(zt)))
    pick = order[np.clip((np.linspace(0.06, 0.99, n)
                          + rng.normal(0, 0.06, n)) * (len(order) - 1), 0,
                         len(order) - 1).astype(int)]
    cen = tips[pick].astype(float)
    rad = h * (0.11 + 0.155 * sp["crown"]) * rng.uniform(0.72, 1.34, n)
    for i in range(n):
        v, f = _ico(2)
        sd = int(rng.integers(0, 99999))
        # smooth lobe: the big masses of the crown
        lobe = 1.0 + 0.42 * fbm(v[:, 0] * 2.2 + i * 7.0, v[:, 1] * 2.2 - i * 3.0, 2, seed=sd)
        # per-vertex spike: the ragged twiggy edge.  Hash on the quantised direction so
        # it is deterministic per mesh but uncorrelated between neighbouring vertices.
        q = (v * 97.0).astype(np.int64)
        spike = 0.74 + 0.52 * hash01(q[:, 0] * 31 + q[:, 2], q[:, 1] * 17 - q[:, 2], sd + 5)
        v = v * (lobe * spike)[:, None] * rad[i]
        v[:, 0] /= (0.62 + 0.55 * col)
        v[:, 1] /= (0.62 + 0.55 * col)
        v[:, 2] *= 0.66 + 0.62 * sp["canopy"][1]
        # skirt: hang the underside down so shells merge into one mass and the crown has
        # a lit top edge and a shadowed belly rather than a hard sphere terminator
        under = np.clip(-v[:, 2] / max(rad[i], 1e-4), 0.0, 1.0)
        v[:, 2] -= under * rad[i] * rng.uniform(0.18, 0.62)
        # darker than the hero LOD: pid drives value 0.72..1.30, so hold it low
        acc.add(v + cen[i], tris=f, mat=2,
                attr=np.full(len(v), rng.uniform(0.02, 0.46)),
                grad=np.full(len(v), rng.uniform(0.30, 0.62)))


_ICO_CACHE = {}


def _ico(sub=1):
    if sub in _ICO_CACHE:
        return [a.copy() for a in _ICO_CACHE[sub]]
    t = (1 + 5 ** 0.5) / 2
    V = np.array([[-1, t, 0], [1, t, 0], [-1, -t, 0], [1, -t, 0],
                  [0, -1, t], [0, 1, t], [0, -1, -t], [0, 1, -t],
                  [t, 0, -1], [t, 0, 1], [-t, 0, -1], [-t, 0, 1]], float)
    F = np.array([[0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11],
                  [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8],
                  [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9],
                  [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1]])
    for _ in range(sub):
        mid = {}
        nf = []
        V = list(V)
        for a, b, c in F:
            ids = []
            for u, v in ((a, b), (b, c), (c, a)):
                k = (min(u, v), max(u, v))
                if k not in mid:
                    mid[k] = len(V)
                    V.append((np.array(V[u]) + np.array(V[v])) / 2)
                ids.append(mid[k])
            x, y, z = ids
            nf += [[a, x, z], [b, y, x], [c, z, y], [x, y, z]]
        V = np.array(V); F = np.array(nf)
    V = V / np.linalg.norm(V, axis=1, keepdims=True)
    _ICO_CACHE[sub] = (V, F)
    return V.copy(), F.copy()


def gen_shrub(key, rng, lod=0):
    sp = dict(SHRUBS[key])
    sp.setdefault("roll", "spiral"); sp.setdefault("clear", 0.10); sp.setdefault("curl", 0.5)
    sp.setdefault("crown", 1.0); sp.setdefault("wind", 1.0); sp.setdefault("multi", None)
    sp["leafn"] = (sp["leafn"][0], sp["leafn"][1], 0)
    acc = Accum()
    h = rng.uniform(*sp["h"])
    wind = np.array([WIND_DIR[0], WIND_DIR[1], 0.0]) * rng.uniform(0.4, 1.4)
    leafbank = []
    ns = int(rng.integers(sp["stems"][0], sp["stems"][1] + 1))
    for i in range(ns):
        a = rng.uniform(0, 2 * math.pi)
        off = np.array([math.cos(a), math.sin(a), 0.0]) * rng.uniform(0.0, 0.22 * h)
        d = _norm(UP * rng.uniform(0.8, 2.2) + np.array([math.cos(a), math.sin(a), 0]) * rng.uniform(0.2, 1.0))
        _branch(acc, sp, rng, off, d, h * rng.uniform(0.45, 0.75), h * 0.020, 0, lod, leafbank, wind)
    # x2.6: at 420-760 leaves a 1.5 m bramble is a handful of white twigs, and in a
    # trackside wide the shrub layer read as a scatter of dead sticks rather than as
    # scrub.  A shrub is a dense thing; that is what makes it a shrub.
    _dress_leaves(acc, sp, rng, leafbank,
                  int(sp["leafn"][lod] * 2.6 * rng.uniform(0.7, 1.25)), wind)
    return acc.finish(VPFX + "shrub_%s_L%d_%03d" % (key, lod, rng.integers(0, 999999) % 9999),
                      [VPFX + "bark_" + sp["bark"], VPFX + "leaf_shrub_" + key]), h


def gen_fern(rng, kind="fern"):
    """Bracken / fern clump: 5-11 arching pinnate fronds."""
    acc = Accum()
    h = rng.uniform(0.35, 1.05)
    n = int(rng.integers(5, 12))
    P = []; F = []; S = []; U = []; SZ = []
    for i in range(n):
        a = rng.uniform(0, 2 * math.pi)
        tilt = rng.uniform(0.35, 1.15)
        d = _norm(np.array([math.cos(a) * tilt, math.sin(a) * tilt, 1.0]))
        L = h * rng.uniform(0.7, 1.2)
        k = 5
        pts = [np.zeros(3)]
        dd = d.copy()
        for j in range(k):
            dd = _norm(dd + np.array([0, 0, -0.36]) * (j / k) + np.array([WIND_DIR[0], WIND_DIR[1], 0]) * 0.06)
            pts.append(pts[-1] + dd * (L / k))
        pts = np.array(pts)
        tube(acc, pts, np.linspace(0.006, 0.002, k + 1), 3, 0)
        seg = pts[1:] - pts[:-1]
        for j in range(k):
            m = 3
            t = rng.random(m)[:, None]
            base = pts[j] + seg[j] * t
            pdir = _norm(seg[j])
            e1 = _norm(np.cross(pdir, UP + np.array([0.01, 0, 0])))
            e2 = np.cross(pdir, e1)
            roll = (rng.integers(0, 2, m) * math.pi + rng.normal(0, 0.2, m))
            lat = np.cos(roll)[:, None] * e1 + np.sin(roll)[:, None] * e2
            f = _norm(pdir * 0.35 + lat * 0.94)
            s = _norm(np.cross(f, UP + np.array([0.01, 0.01, 0])))
            P.append(base); F.append(f); S.append(s); U.append(np.cross(f, s))
            SZ.append(rng.uniform(0.10, 0.20, m) * (1.0 - 0.5 * j / k))
    place_leaves(acc, np.concatenate(P), np.concatenate(F), np.concatenate(S),
                 np.concatenate(U), np.concatenate(SZ), (1, "pinnate"), rng)
    return acc.finish(VPFX + "fern_%03d" % (rng.integers(0, 999999) % 9999),
                      [VPFX + "bark_hawthorn", VPFX + "leaf_fern"]), h


# ----------------------------------------------------------------------------------
# 6.2  WEEDS AND STONES
# ----------------------------------------------------------------------------------
# The user's red line is "not a grass gray line".  A verge is not grass: it is grass,
# and dock, and thistle, and ragwort going over, and plantain flattened by feet, and
# yarrow, and nettle where the ground is rich — and it has stones in it.  Six weeds and
# three stone classes, all generated, none re-tinted from another.

WEEDS = {
    # basal habit                                          flowering head
    "dock":     dict(h=(0.40, 1.15), leaves=(7, 14), lsz=(0.16, 0.34), lw=0.30,
                     tilt=(0.20, 1.05), droop=0.55, stems=(1, 3), stemf=0.95,
                     head="spike", hcol=(0.140, 0.042, 0.020), hn=(70, 150)),
    "thistle":  dict(h=(0.45, 1.30), leaves=(6, 12), lsz=(0.14, 0.30), lw=0.19,
                     tilt=(0.35, 1.25), droop=0.35, stems=(1, 2), stemf=1.0,
                     head="brush", hcol=(0.115, 0.048, 0.150), hn=(38, 70)),
    "ragwort":  dict(h=(0.35, 0.95), leaves=(6, 11), lsz=(0.10, 0.20), lw=0.24,
                     tilt=(0.30, 1.10), droop=0.45, stems=(1, 3), stemf=0.85,
                     head="corymb", hcol=(0.470, 0.330, 0.030), hn=(16, 34)),
    "plantain": dict(h=(0.12, 0.34), leaves=(5, 10), lsz=(0.09, 0.19), lw=0.38,
                     tilt=(1.05, 1.50), droop=0.12, stems=(2, 5), stemf=1.15,
                     head="rod", hcol=(0.075, 0.062, 0.032), hn=(28, 60)),
    "yarrow":   dict(h=(0.22, 0.60), leaves=(8, 16), lsz=(0.07, 0.15), lw=0.10,
                     tilt=(0.45, 1.20), droop=0.30, stems=(1, 4), stemf=1.0,
                     head="umbel", hcol=(0.420, 0.400, 0.360), hn=(22, 44)),
    "nettle":   dict(h=(0.35, 0.90), leaves=(10, 22), lsz=(0.07, 0.15), lw=0.42,
                     tilt=(0.60, 1.25), droop=0.30, stems=(2, 5), stemf=1.0,
                     head=None, hcol=(0.070, 0.090, 0.036), hn=(0, 0)),
}

WEED_ORDER = list(WEEDS.keys())

# ====================================================================================
# THE GROUND-COVER TIER'S A/B HARNESS                                        R2-2970
# ====================================================================================
# `TERRAIN_R2970_BEFORE=1` reverts the three amplitude changes this pass SHIPPED to
# the ground-cover tier -- no seed head on fescue or tussock, a 9-spoke panicle,
# smooth-shaded grit -- so the before/after measurement in
# `tools/r2970_groundcover_px.py` is the same code, the same seed and the same
# generators differing in exactly one thing.
#
# It deliberately does NOT cover the two changes this pass built and then WITHDREW
# (the thistle leaf lobe and the 8-sided weed stem, R2-2973/R2-2974): those are
# gone from both arms, because a switch that can restore geometry the measurement
# rejected is a quality dial, and this is a measurement switch.
#
# It is the same device as `TERRAIN_LEGACY_GRASS` above and it is a MEASUREMENT
# SWITCH, NEVER A QUALITY DIAL.  Nothing in the production path reads it.
R2970_BEFORE = os.environ.get("TERRAIN_R2970_BEFORE", "0") == "1"

# --- constants the pixel gate imports instead of retyping ---------------------------
# `tools/r2970_groundcover_px.py` converts every one of these into pixels at the
# MEASURED sharp resolution of the object that carries it.  They live here, at
# module scope, for the reason the project states in one line: constants are
# imported, never retyped.  Seven copies of the car's bounding box already exist.
WEED_STEM_R     = (0.016, 0.006)   # stem radius at base / tip, as a fraction of h

# SIDES ON THE STEM TUBE.  RAISED TO 8, THEN WITHDRAWN.            R2-2973, vetoed
#
# The quantity that decides this is the POLYGONAL SILHOUETTE ERROR -- how far an
# n-gon's edge falls inside the circle it stands for, (d/2)(1 - cos(pi/n)) -- not
# the facet width, because what gives a low-poly tube away first is that its
# outline changes width as it spins.  Against R2-2945's `VEG_weed_thistle` at
# 347.9 px/m, four sides came out at 0.76 px typical and 2.12 px at the base of
# the tallest plant, i.e. a visible artefact, and it was raised to eight.
#
# R2-2949 THEN WITHDREW THAT RESOLUTION.  With a minimum sharp-sample floor --
# the control that pass did not apply -- `VEG_weed_thistle` falls from 347.88 to
# **141.41 px/m at >=10 samples** and 85.73 at >=25, because its peak was set by
# fewer than ten of its 6,821 points.  (Grass and grit hold at 425.82 to a >=10
# floor with 25 spatially-spread setters and zero shell contamination, which is
# why the grass and grit work in this block stands and this does not.)
#
# At the corrected 141.41 px/m, 1 px is 7.07 mm and the four-sided stem is:
#
#     n = 4    0.31 px typical   0.86 px at the thick end   -- ALREADY SUB-PIXEL
#     n = 8    0.08 px           0.22 px
#
# So four sides was never an artefact and eight bought 0.6 px of nothing, at
# four quads per stem segment.  Reverted.  The mechanism and its gate stay --
# `stem_round` is what produced this number and is the only UPPER-BOUND gate in
# `tools/r2970_groundcover_px.py`.
#
# It is also NOT thinned to life size (a real 0.9 m spear thistle stem is
# 8-12 mm, so this is ~2.5x thick).  That is an accuracy call with no reference
# in hand and it is declined rather than guessed at.
WEED_STEM_SIDES = 4

# WHICH WEEDS ARE PINNATIFID, AND HOW DEEPLY                              R2-2974
#
# A spear thistle and a ragwort do not have smooth-edged leaves: they are cut
# most of the way to the midrib in a repeating lobe.  `_ribbon` drew a smooth
# sine taper for every weed in the world, so the single most characteristic
# feature of the two commonest verge weeds was absent from the mesh.
#
# IT IS HERE BECAUSE IT CLEARS THE LINE, AND ONLY BECAUSE OF THAT.  Measured at
# VEG_weed_thistle's 347.9 px/m (1 px = 2.87 mm):
#
#     leaf length        h * lsz * 1.55 = 0.10-0.60 m       35-210 px
#     leaf half width    0.5 * lw * L   = 9.5-57 mm        3.3-20  px
#     lobe DEPTH         `depth` of that half width        1.5-14  px
#     lobe PITCH         L / (2 * lobes)                    3-26   px
#
# The shallow end of that is marginal and the middle of it is not.  Contrast
# `DECLINED` in the gate: a 0.3 mm blade serration is 0.13 px and a thistle
# SPINE is 0.2 px thick, and neither is built, because a feature under a pixel
# is waste however botanically correct it is.
#
# `segs` has to rise with the lobe count or the lobe cannot be drawn: a ribbon
# needs at least two stations per lobe to have a waist and a shoulder, so
# `_ribbon` raises its own segment count to 3 per lobe when lobes are asked for.
#
# THIS TABLE IS EMPTY, AND IT HELD TWO SPECIES.                   R2-2974, vetoed
#
# Both were built with the mechanism below, both were MEASURED on the built mesh
# by `tools/r2970_groundcover_px.py`, and both came back under the pixel line.
#
#   ragwort   built, measured 0.57 px RMS, removed.  VEG_weed_ragwort is seen at
#             233.3 px/m (1 px = 4.29 mm) and its leaf half width is 1.5-8.2 px
#             (typical 3.5), so a 0.55 cut is 1.9 px peak and 0.57 px RMS.
#             Reaching 1 px RMS needs depth ~0.95 -- a leaf cut 95 % to the
#             midrib, which is not a ragwort, it is a comb.
#   thistle   built, measured 1.95 px RMS at R2-2945's 347.9 px/m -- and then
#             R2-2949 withdrew that resolution.  With a minimum sharp-sample
#             floor `VEG_weed_thistle` is 141.41 px/m at >=10 samples and 85.73
#             at >=25, so the same built margin is **0.79 px** and **0.48 px**.
#             Removed, at 3.75x the leaf quads (segs 4 -> 15) for nothing.
#
# Both are botanically correct, both are cheap, and both are declined, because
# the rule is not "build what is real", it is "build what survives to a pixel".
# The mechanism stays: `_ribbon`'s `lobe` and the `leaf_margin` gate are what
# produced these two numbers, and they are what will decide the next candidate.
LOBED_WEEDS = {}

# THE PANICLE.  One grass seed head: `PANICLE_N` branches off the culm tip, each
# `PANICLE_LEN_M` long and `PANICLE_RAD_M` thick, carrying `PANICLE_SPIKE`
# spikelets along its length.
#
# IT WAS NINE STRAIGHT SPOKES.                                             R2-2972
# Nine tubes radiating from one point is a spider, not a head, and the shape
# PATTERN 4 names -- "the mechanism is in the code and its amplitude is 3-5x too
# small to survive to pixels" -- is exactly this: a real Festuca or Dactylis
# panicle carries 25-150 spikelets on whorled branches.  Every part of it clears
# the line at the grass tier's measured 425.8 px/m (1 px = 2.35 mm):
#
#     branch length   20-60 mm    8.5-25.5 px
#     branch/spikelet 2.4-3.2 mm  1.0-1.4  px
#     whole head      40-120 mm    17-51   px
#
# so it is built.
#
# AND IT IS BUILT OUT OF FLAT STRIPS, WHICH IS WHY IT IS AFFORDABLE.  The old
# nine spokes were 3-sided TUBES: 15 triangles each to model the roundness of
# something 1.0-1.4 px thick.  Three facets on a 1.2 px cylinder are 0.4 px
# apiece -- the cross-section is entirely below the line, so every one of those
# triangles was spent on a shape nobody can sample.  A tapered flat strip is 4
# triangles and is indistinguishable at 1.2 px.  Measured per head:
#
#     old   1 culm tube +  9 tube branches                     150 tris
#     new   1 culm tube + 24 strip branches + 48 strip spikelets ~207 tris
#
# -- 2.7x the branches and 5x the spikelets for 1.4x the triangles.  That ratio
# is the whole reason this change is affordable: `work/r2500/build_assembly10.log`
# puts 1,821,790 HERO clumps in the world at 3,171 polys each, which is roughly
# 10.9 G of the world's 15.1 G instanced triangles.  Hero grass is the single
# largest triangle consumer in the film, so a 6x panicle built out of tubes would
# have taken the world to ~39 G and would have been a render-time decision
# disguised as a detail decision.
PANICLE_N      = (9, 9) if R2970_BEFORE else (18, 30)
PANICLE_SPIKE  = (0, 0) if R2970_BEFORE else (1, 3)
PANICLE_LEN_M  = (0.020, 0.060)
# half width at base / mid / tip.  Full width 2.4 / 3.2 / 1.2 mm = 1.0 / 1.4 /
# 0.5 px at the grass tier's measured 425.8 px/m.
PANICLE_RAD_M  = (0.0012, 0.0016, 0.0006)
SEED_HEAD_FRAC = 0.35


def _hair(acc, pts, ws, mat, grad=1.0):
    """A tapered FLAT strip along `pts`, half-widths `ws`.  2 tris per segment.

    The panicle's branches and spikelets are 1.0-1.4 px thick, so their
    cross-section is below the pixel line and a tube's extra triangles buy
    nothing.  Cf. `_sward_leaf`, which makes the same argument for a drift leaf
    at 40 m, and `_blade`, which makes the OPPOSITE argument at 4.6 m where the
    keel is the read.  The three of them are the same law at three distances.
    """
    pts = np.asarray(pts, float); ws = np.asarray(ws, float)
    k = len(pts)
    t, _, _ = _frames(pts)
    side = _norm(np.cross(t, np.array([WIND_DIR[0], WIND_DIR[1], 0.0])
                          + np.array([0.03, 0.02, 0.9])))
    V = np.concatenate([pts + side * ws[:, None], pts - side * ws[:, None]], 0)
    i = np.arange(k - 1)
    Q = np.stack([i, i + 1, k + i + 1, k + i], -1)
    acc.add(V, quads=Q, mat=mat, grad=np.full(2 * k, grad))


def _ribbon(acc, base, d0, L, W, segs, mat, rng, droop=0.5, curve=0.35, pid=None,
            lobe=None):
    """One arching, tapering leaf blade, built as a real ribbon.

    A flat quad on a frame is what `place_leaves` does and it is right for a tree at
    30 m; a dock leaf 1.2 m from the lens has to actually curve.

    `lobe` is an entry of `LOBED_WEEDS`.  It modulates the half-width profile so
    the margin is cut back toward the midrib `lobes` times a side, which is what
    makes a thistle leaf a thistle leaf.  It is a change to the SILHOUETTE, i.e.
    geometry, and not to a normal map: at 3-14 px of lobe depth a shader cannot
    put the notch there because the notch is where the leaf stops being.
    """
    if lobe:
        segs = max(segs, 3 * int(lobe["lobes"]))
    d = _norm(np.asarray(d0, float))
    wd = np.array([WIND_DIR[0], WIND_DIR[1], 0.0])
    pts = [np.asarray(base, float)]
    for j in range(segs):
        f = (j + 1.0) / segs
        d = _norm(d + np.array([0.0, 0.0, -droop * f * 2.2 / segs]) + wd * (curve * 0.05))
        pts.append(pts[-1] + d * (L / segs))
    pts = np.array(pts)
    t, u, v = _frames(pts)
    side = _norm(np.cross(t[0], wd + np.array([0.04, 0.03, 0.92])))
    f = np.linspace(0.0, 1.0, len(pts))
    w = W * np.sin(np.pi * np.clip(f, 0.02, 0.99) ** 0.62) + W * 0.06
    if lobe:
        # cut the margin back toward the midrib `lobes` times.  The sinus never
        # closes completely (0.10 floor) because a leaf that reaches zero width
        # is two leaves, and the lobes get shallower toward the tip, which is
        # what pinnatifid actually means.
        ph = rng.uniform(0, 2 * math.pi)
        cut = 0.5 - 0.5 * np.cos(2 * math.pi * lobe["lobes"] * f + ph)
        w = w * np.maximum(0.10, 1.0 - lobe["depth"] * cut * (1.0 - 0.45 * f))
    V = np.concatenate([pts + side * w[:, None], pts - side * w[:, None]], 0)
    k = len(pts)
    i = np.arange(k - 1)
    Q = np.stack([i, i + 1, k + i + 1, k + i], -1)
    G = np.tile(f, 2)
    acc.add(V, quads=Q, mat=mat,
            attr=np.full(2 * k, rng.random() if pid is None else pid), grad=G)


def _weed_head(acc, rng, sp, top, up, size):
    """The flowering head: four genuinely different constructions, one per habit."""
    kind = sp["head"]
    n = int(rng.integers(sp["hn"][0], sp["hn"][1] + 1))
    if kind is None or n <= 0:
        return
    wd = np.array([WIND_DIR[0], WIND_DIR[1], 0.0])
    P = []; F = []; S = []; U = []; SZ = []
    if kind == "spike" or kind == "rod":
        # a dense vertical spike of tiny bracts (dock seed, plantain flower rod)
        L = size * (0.34 if kind == "spike" else 0.42)
        for i in range(n):
            f = rng.random() ** (0.7 if kind == "spike" else 1.0)
            a = rng.uniform(0, 2 * math.pi)
            r = size * (0.030 if kind == "rod" else 0.055) * (1.0 - 0.55 * f)
            p = top + up * (L * f) + np.array([math.cos(a) * r, math.sin(a) * r, 0.0])
            fw = _norm(np.array([math.cos(a), math.sin(a), rng.uniform(-0.5, 0.4)]))
            sd = _norm(np.cross(fw, up + np.array([0.02, 0.01, 0.0])))
            P.append(p); F.append(fw); S.append(sd); U.append(np.cross(fw, sd))
            SZ.append(size * rng.uniform(0.020, 0.042))
    elif kind == "brush":
        # thistle: a hemispherical brush of florets on a short involucre
        for i in range(n):
            a = rng.uniform(0, 2 * math.pi)
            el = rng.uniform(0.15, 1.0)
            d = _norm(np.array([math.cos(a) * (1 - el * 0.7), math.sin(a) * (1 - el * 0.7), el]))
            p = top + d * size * 0.035
            sd = _norm(np.cross(d, up + np.array([0.03, 0.01, 0.0])))
            P.append(p); F.append(d); S.append(sd); U.append(np.cross(d, sd))
            SZ.append(size * rng.uniform(0.030, 0.055))
    else:                                   # corymb / umbel: a flat-topped plate
        spread = size * (0.20 if kind == "corymb" else 0.14)
        for i in range(n):
            a = rng.uniform(0, 2 * math.pi)
            r = spread * math.sqrt(rng.random())
            p = top + np.array([math.cos(a) * r, math.sin(a) * r,
                                rng.uniform(-0.05, 0.03) * size])
            fw = _norm(np.array([math.cos(a) * 0.35, math.sin(a) * 0.35, 1.0]))
            sd = _norm(np.cross(fw, wd + np.array([0.05, 0.02, 0.9])))
            P.append(p); F.append(fw); S.append(sd); U.append(np.cross(fw, sd))
            SZ.append(size * rng.uniform(0.028, 0.052))
    place_leaves(acc, np.array(P), np.array(F), np.array(S), np.array(U),
                 np.array(SZ), (2, "small"), rng)


def gen_weed(key, rng):
    """One unique weed.  Material slots: 0 stem, 1 leaf, 2 flower."""
    sp = WEEDS[key]
    acc = Accum()
    h = rng.uniform(*sp["h"])
    nl = int(rng.integers(sp["leaves"][0], sp["leaves"][1] + 1))
    a0 = rng.uniform(0, 2 * math.pi)
    for i in range(nl):
        a = a0 + i * math.radians(137.5) + rng.normal(0, 0.25)
        tilt = rng.uniform(*sp["tilt"])
        d = _norm(np.array([math.cos(a) * math.sin(tilt), math.sin(a) * math.sin(tilt),
                            math.cos(tilt)]))
        L = h * rng.uniform(sp["lsz"][0], sp["lsz"][1]) * 1.55
        base = np.array([0.0, 0.0, 0.0]) + np.array(
            [math.cos(a), math.sin(a), 0.0]) * h * rng.uniform(0.0, 0.05)
        _ribbon(acc, base, d, L, L * sp["lw"] * 0.5, 4, 1, rng,
                droop=sp["droop"] * rng.uniform(0.7, 1.4),
                lobe=LOBED_WEEDS.get(key))
    ns = int(rng.integers(sp["stems"][0], sp["stems"][1] + 1))
    for i in range(ns):
        a = rng.uniform(0, 2 * math.pi)
        lean = rng.uniform(0.02, 0.20)
        d = _norm(np.array([math.cos(a) * lean, math.sin(a) * lean, 1.0])
                  + np.array([WIND_DIR[0], WIND_DIR[1], 0.0]) * 0.10)
        L = h * sp["stemf"] * rng.uniform(0.80, 1.05)
        k = 4
        pts = [np.array([math.cos(a), math.sin(a), 0.0]) * h * rng.uniform(0.0, 0.04)]
        dd = d.copy()
        for j in range(k):
            dd = _norm(dd + np.array([WIND_DIR[0], WIND_DIR[1], 0.0]) * 0.05
                       + np.array([0, 0, -0.05 * (j / k)]))
            pts.append(pts[-1] + dd * (L / k))
        pts = np.array(pts)
        tube(acc, pts, np.linspace(h * WEED_STEM_R[0], h * WEED_STEM_R[1], k + 1),
             WEED_STEM_SIDES, 0)
        # a few cauline leaves up the stem
        if key in ("nettle", "ragwort", "thistle"):
            for j in range(1, k):
                for sgn in (1, -1):
                    e = _norm(np.cross(dd, UP + np.array([0.02, 0.01, 0.0]))) * sgn
                    _ribbon(acc, pts[j], _norm(e * 1.3 + UP * 0.5),
                            L * rng.uniform(0.14, 0.26), L * 0.045, 3, 1, rng, droop=0.5,
                            lobe=LOBED_WEEDS.get(key))
        _weed_head(acc, rng, sp, pts[-1], _norm(dd), h)
    mats = [VPFX + "weedstem_" + key, VPFX + "leaf_weed_" + key,
            VPFX + "flower_" + key]
    return acc.finish(VPFX + "weed_%s_%03d" % (key, rng.integers(0, 999999) % 9999),
                      mats), h


STONES = {                     # size range, flatness, angularity, subdivisions
    "pebble": dict(h=(0.030, 0.085), flat=(0.55, 0.85), ang=0.30, sub=1),
    "cobble": dict(h=(0.10, 0.34), flat=(0.42, 0.80), ang=0.45, sub=2),
    "boulder": dict(h=(0.45, 1.70), flat=(0.50, 0.90), ang=0.55, sub=2),
}


# CLEAVAGE PLANES ON A GRIT CHIP.                                          R2-2975
#
# The grit fraction is the highest-resolution class in the whole world outside the
# forecourt paving: `sp_objects.json` measures VEG_grit_chip / _stone / _clod at
# 425.8 px/m over 999-1012 SHARP FRAMES -- more than any other object in the film.
# 1 px is 2.35 mm there, so a 12-38 mm chip is 5.1-16.2 px, a 35-95 mm stone is
# 14.9-40.4 px, and the 80-face icosphere they are built from has facets of
# 1.4-10.9 px.  Every one of those facets is above the pixel line.
#
# AND `shade_smooth()` DELETED ALL OF THEM.  Not scaled them down by 3-5x: set the
# amplitude to exactly zero while leaving the geometry in the file, so a code
# review, a triangle count and the material_depth check all pass and the pixels
# show a smooth pebble.  That is `docs/WAVE1-PEEP-SYNTHESIS.md` PATTERN 4 in its
# limiting case, and it is why `facet` exists.
#
# Two changes, both geometry, neither a material:
#   * `facet=True` shades the piece FLAT, so a facet edge is a hard shading break.
#     At a 12.47 deg sun a hard break is the entire read of a stone; a smooth
#     normal makes a 16 px flint chip a 16 px ball bearing.
#   * cleavage planes.  A flint chip is not a lumpy sphere, it is a conchoidal
#     fracture: a few genuinely flat faces meeting at sharp arrises.  Each plane
#     clamps the vertices outside it back onto it.
#
# THE SECOND ONE IS THE SMALLER OF THE TWO AND ITS SIZE WAS MEASURED, NOT
# ASSUMED.  Over 30 pieces, the fraction of shared edges that are coplanar to
# within 5 deg -- i.e. that lie inside one genuinely flat face:
#
#     no cleavage                              0.139
#     off 0.55-0.92, 2-5 planes                0.156   (volume kept 0.93)
#     off 0.45-0.78, 3-6 planes                0.203   (volume kept 0.82)
#     off 0.38-0.70, 4-7 planes                0.244   (volume kept 0.68)
#
# so the honest statement is that cleavage buys ~45 % more truly flat facet at a
# fifth of the volume, and it cannot buy more than that on a 42-vertex icosphere
# because a cap that holds only three or four vertices cannot contain a whole
# triangle.  `shade_flat` is the mechanism; this is shaping.  The middle row is
# taken.  (Volume is not size: `gn_kind` normalises by height and rescales to
# GRIT_KINDS' range, so a leaner piece is a leaner piece, not a smaller one.)
#
# The `ridged` field that was supposed to be doing all of this never could: it is
# sampled at 42 vertices 0.55 units apart at a base frequency of 5.3 over 3
# octaves, so it is aliased by 3-12x, and its amplitude of +-0.033 R is +-0.27 px
# on a 38 mm chip -- under the line even if it had been sampled properly.  It is
# left alone; it was never the mechanism.
GRIT_CLEAVE_N   = (3, 6)         # flat fracture faces per piece
GRIT_CLEAVE_OFF = (0.45, 0.78)   # plane offset as a fraction of the piece radius


def gen_stone(key, rng, matname=None, facet=False):
    """One unique stone: an icosphere pushed around by fBm and bedding planes.

    `facet` -- the grit fraction.  Cleaves the piece on 2-5 flat planes and shades
    it FLAT.  See GRIT_CLEAVE_N.  Field stone (cobble, boulder) keeps the smooth
    rounded form it ships with, because a river-worn cobble genuinely is rounded.
    """
    sp = STONES[key]
    V, F = _ico(sp["sub"])
    n = len(V)
    seed = int(rng.integers(0, 1 << 20))
    # anisotropy: stones are not spheres, they are flattened along a bedding plane
    ax = np.array([1.0, rng.uniform(0.62, 1.0), rng.uniform(*sp["flat"])])
    R = Euler((rng.uniform(0, 3.14), rng.uniform(0, 3.14), rng.uniform(0, 6.28))).to_matrix()
    P = V * ax[None, :]
    # lumpy fBm + angular facets from a second, higher-frequency ridged field
    amp = 0.22 + 0.30 * sp["ang"]
    d = fbm(P[:, 0] * 2.1 + seed, P[:, 1] * 2.1 - seed, 4, seed=seed % 9973)
    d2 = ridged(P[:, 0] * 5.3, P[:, 1] * 5.3 + 3.0, 3, seed=(seed + 17) % 9973)
    P *= (1.0 + amp * d + sp["ang"] * 0.22 * (d2 - 0.5))[:, None]
    if facet and not R2970_BEFORE:
        rad = float(np.linalg.norm(P, axis=1).max())
        for _ in range(int(rng.integers(GRIT_CLEAVE_N[0], GRIT_CLEAVE_N[1] + 1))):
            nrm = rng.normal(0, 1, 3)
            nrm /= max(float(np.linalg.norm(nrm)), 1e-9)
            off = rad * rng.uniform(*GRIT_CLEAVE_OFF)
            s = P @ nrm
            out = s > off
            if out.any():
                P[out] -= np.outer(s[out] - off, nrm)
    P = P @ np.asarray(R, float).T
    P[:, 2] -= P[:, 2].min()
    h = float(P[:, 2].max())
    if h < 1e-4:
        h = 1e-4
    me = new_mesh_arrays(VPFX + "stone_%s_%04d" % (key, rng.integers(0, 1 << 20) % 9999),
                         P, F, None)
    me.materials.append(bpy.data.materials[matname or (VPFX + "stone")])
    if facet and not R2970_BEFORE:
        me.shade_flat()
    else:
        me.shade_smooth()
    return me, h


def gen_grit_piece(rng, matname):
    """ONE grit piece, built the one way the whole project builds them.

    `build_library`, `macro_probe` and `tools/r2970_groundcover_px.py` all come
    through here, so the gate cannot measure a piece that differs from the one
    the film renders -- which is how a measurement quietly stops being evidence.
    """
    return gen_stone("pebble", rng, matname=matname, facet=True)


# --- grass ---------------------------------------------------------------------------
#
# VEGETATION IS A GEOMETRY PROBLEM, NOT A MATERIAL PROBLEM.  The user's note on the 4K
# frame -- "the grass is blurry ... we need max detail max models detail on everything"
# -- is a statement about what a blade IS at 2.4 m from the lens, which is where the
# doppler hover puts the camera (beat_sheet.json: station 2555, 26.0 m off the
# centreline, 2.4 m above grade).  A 35 mm lens at 3840 px resolves 2.47e-4 rad per
# pixel, so at the nearest ground actually inside that frame (7.5 m, from the -1.68 deg
# pitch and the 16.13 deg half-angle) ONE PIXEL IS 1.94 mm.  Everything below follows
# from that number.
#
# THREE THINGS MAKE A BLADE READ, and the old generator had one of them:
#
#  1. WIDTH near 2-4 px.  The old blades were 6.0-11.0 mm across (w is a HALF-width and
#     the ribbon is +-w), which is 3-6 px -- but a fescue blade is 1-3 mm and a rye
#     blade 3-6 mm, so they were 2-3x life size.  Oversized blades OVERLAP, and overlap
#     is exactly what turns blades into a mat.  Now 3.4-6.6 mm for fescue, i.e. 1.8-3.4
#     px at 7.5 m and 6-12 px at 2.4 m, with three times as many of them.
#  2. A FOLD.  A flat two-vertex ribbon has ONE normal across its width, so under a
#     12.47 deg sun a whole blade is one flat tone and neighbouring blades differ only
#     by their lean.  A real blade is CHANNELLED about its midrib.  Every hero blade now
#     carries three vertices per station -- edge, keel, edge -- so the two halves shade
#     differently and the keel throws a specular line down the blade.  That is where the
#     "edges and tips" in the brief actually come from: it is a light/dark PAIR even
#     when the blade is 2 px wide, which no shader on a flat strip can produce.
#  3. DARK GAPS.  Most of the read of turf is the shadowed thatch BETWEEN the blades.
#     The old clump was a uniform disc of full-length blades, so it closed into a
#     canopy with nothing under it.  Blades now come in TILLERS (a real sward is
#     tillers, not a scatter), each tiller a fan from one base, and 34 % of every clump
#     is a short understorey at 0.30-0.62 of full height that fills the floor without
#     closing the top.
#
# Plus: 6 segments instead of 3 (a 0.25 m blade is 125 px tall at 2.4 m, and a
# three-segment polyline reads as a kinked stick), a real point at the tip (0.05 w
# rather than 0.15 w) and a progressive twist about the blade axis.
#
# THE COST IS ALMOST NOTHING, and that is why this is the right axis to spend on.
# Cycles keeps ONE copy of a mesh however many objects instance it, so the library is
# 55 meshes and the 3 M placements are instances.  A hero clump is ~6 k triangles
# against the old ~460, and the whole library still fits in a few hundred thousand
# resident triangles.  What DOES scale is per-instance BVH traversal, so the hero
# blade is spent only where it can be seen: `GRASS_HERO_D` metres of the camera path.

# A/B HARNESS.  TERRAIN_LEGACY_GRASS=1 reverts the whole grass layer to the previous
# pass -- flat two-vertex ribbons, 3 segments, 54-98 scattered blades, no tillers, no
# understorey, blades at 6.0-11.0 mm -- so the before/after crops in build_terrain.md
# section 9.3 are the same camera, the same light and the same placement, differing in
# exactly one thing.  It is a measurement switch, never a quality dial.
LEGACY_GRASS = os.environ.get("TERRAIN_LEGACY_GRASS", "0") == "1"

VERGE_TAIL_T = 0.28        # R2-1829: the outer fraction of the verge band's own draw
                           # over which it crossfades to zero instead of ending. 0.28
                           # of a 50 m band on the pit straight is f = 28..42 m, and
                           # the sward drifts are at full weight from f = 34, so the
                           # handoff happens where the receiving layer is already
                           # carrying the ground. Sized against the sward's own ramp,
                           # not chosen.  See `verge_band`'s `tdraw`.

BUILT_STANDOFF_M = 3.0     # metres of clear ground outside architecture's declared
                           # paving before ground cover reaches full weight.  Sized by
                           # the widest placeable unit's half-extent (a tier-A sward
                           # drift, 1.67 m), not chosen.  See `habitat`.

GRASS_HERO_D = 48.0        # hero clumps within this of the LENS (CameraPath.dist3,
                           # true 3-D); far clumps beyond it.  At 60 m a 4 mm blade is
                           # 0.24 px and no geometry can help; what matters there is
                           # the clump silhouette, which the far mesh has -- and
                           # beyond that again it is the sward drifts (section 6b),
                           # because a silhouette on 4 % ground cover is still 96 %
                           # flat colour.

# THE TWO KINDS THAT CARRY THE MOST SHARP FRAMES CARRIED NO SEED HEAD.     R2-2971
#
# `work/w2_0/retier_a10/sp_objects.json` measures VEG_grass_tussock_H at 407.3 px/m
# over 845 sharp frames and VEG_grass_fescue_H at 425.8 px/m over 845 -- more sharp
# frames than any other vegetation in the film -- and both shipped `seed=0.0`.  In
# the rough (the frame this tier was re-derived from, f2316, where the sward fills
# the bottom 35 % of the plate) `build_grass`'s own habitat weights make TUSSOCK the
# dominant kind at w = 0.65, so the commonest grass in the sharpest ground cover in
# the film had no panicle at all in a shot whose thistles are in flower.
#
# A panicle is 17-51 px tall with 1.0-1.4 px branches at this resolution (see
# PANICLE_N).  It is the single largest piece of grass structure above the pixel
# line that was not being built.  Fescue gets a small share because the fescue
# weight peaks on the MOWN verge where most culms really are cut; tussock, which
# is the unmanaged rough, gets a real one.
GRASS_PROF = dict(
    # h        blade length              w  HALF-width at the base (m)
    # lean     multiplier on WIND_LEAN   seed  fraction that gets a panicle
    # spread   clump radius (m)          keel  fold depth as a multiple of w
    # tiller   (min, max) blades per tiller
    fescue=dict(h=(0.14, 0.30), w=(0.0017, 0.0033), lean=(0.75, 1.15),
                seed=0.0 if R2970_BEFORE else 0.15,
                spread=0.21, keel=0.85, tiller=(3, 6), under=0.34, twist=1.10),
    tussock=dict(h=(0.30, 0.62), w=(0.0024, 0.0046), lean=(0.60, 1.05),
                 seed=0.0 if R2970_BEFORE else 0.45,
                 spread=0.27, keel=0.95, tiller=(4, 8), under=0.30, twist=1.40),
    meadow=dict(h=(0.35, 0.78), w=(0.0015, 0.0029), lean=(0.85, 1.25), seed=0.55,
                spread=0.33, keel=0.75, tiller=(2, 5), under=0.26, twist=1.60),
    dry=dict(h=(0.10, 0.26), w=(0.0019, 0.0035), lean=(1.15, 1.55), seed=0.10,
             spread=0.25, keel=0.60, tiller=(3, 7), under=0.38, twist=0.90),
    reed=dict(h=(0.9, 1.9), w=(0.0038, 0.0072), lean=(0.55, 0.95), seed=0.75,
              spread=0.30, keel=1.05, tiller=(1, 3), under=0.14, twist=0.70),
)


def _blade(acc, rng, prof, base, L, w, lean, segs, keel, wdir, pid):
    """One blade: a tapered, twisted, CHANNELLED ribbon on a cantilever path."""
    az = wdir * math.sin(lean) + np.array([rng.normal(0, 0.22), rng.normal(0, 0.22), 0])
    d = _norm(UP * math.cos(lean) + az)
    pts = [base]
    ws = [w]
    for j in range(segs):
        f = (j + 1) / segs
        d = _norm(d + wdir * (0.55 * lean * f) + np.array([0, 0, -0.30 * f * f]))
        pts.append(pts[-1] + d * (L / segs))
        # taper: nearly parallel-sided for the first third, then to a real point
        ws.append(w * max(0.05, 1.0 - 0.95 * f ** 1.6))
    pts = np.array(pts)
    ws = np.array(ws)
    k = len(pts)
    t, _, _ = _frames(pts)
    side0 = _norm(np.cross(t[0], wdir + np.array([0.03, 0.02, 0.9])))
    G = np.linspace(0.0, 1.0, k)
    if keel <= 0.0:
        # far LOD: the old flat two-vertex ribbon, which is all a sub-pixel clump needs
        side = _norm(np.cross(t, wdir + np.array([0.03, 0.02, 0.9])))
        V = np.concatenate([pts + side * ws[:, None], pts - side * ws[:, None]], 0)
        i = np.arange(k - 1)
        Q = np.stack([i, i + 1, k + i + 1, k + i], -1)
        acc.add(V, quads=Q, mat=0, attr=np.full(2 * k, pid), grad=np.tile(G, 2))
        return
    # hero LOD: edge / keel / edge, twisted progressively about the blade axis
    tw = prof["twist"] * rng.uniform(-1.0, 1.0)
    S = np.empty((k, 3)); N = np.empty((k, 3))
    cur = side0
    for i in range(k):
        cur = cur - t[i] * float(np.dot(cur, t[i]))
        n = np.linalg.norm(cur)
        cur = cur / n if n > 1e-9 else _norm(np.cross(t[i], UP + 0.1))
        a = tw * G[i]
        nrm = _norm(np.cross(t[i], cur))
        S[i] = cur * math.cos(a) + nrm * math.sin(a)
        N[i] = _norm(np.cross(t[i], S[i]))
    A = pts + S * ws[:, None]
    B = pts - S * ws[:, None]
    M = pts + N * (keel * ws)[:, None]
    V = np.concatenate([A, M, B], 0)
    i = np.arange(k - 1)
    Q = np.concatenate([np.stack([i, i + 1, k + i + 1, k + i], -1),
                        np.stack([k + i, k + i + 1, 2 * k + i + 1, 2 * k + i], -1)], 0)
    acc.add(V, quads=Q, mat=0, attr=np.full(3 * k, pid), grad=np.tile(G, 3))


LEGACY_W = dict(fescue=(0.0030, 0.0055), tussock=(0.0045, 0.0085),
                meadow=(0.0025, 0.0048), dry=(0.0035, 0.0060), reed=(0.0060, 0.0110))


def gen_grass(rng, kind="fescue", blades=26, segs=3, lod=0):
    """One grass clump.  Wind lean is world-consistent; the clump only varies about it.

    `lod` 0 = hero (channelled blades, tillers, understorey), 1 = far (flat ribbons).
    See the block comment above for why each of those exists and what it costs.
    """
    prof = GRASS_PROF[kind]
    if LEGACY_GRASS:
        prof = dict(prof, w=LEGACY_W[kind], under=0.0, tiller=(1, 1))
    elif lod != 0:
        # THE FAR TIER KEEPS THE WIDE BLADE, ON PURPOSE.  Narrowing the hero blade to
        # life size is what makes it resolve at 7.5 m; beyond GRASS_HERO_D a blade is
        # under a third of a pixel and its width is not a shape any more, it is a
        # COVERAGE fraction.  A 3.4 mm blade there is simply 2x less sward than a
        # 6.6 mm one for the same instance cost, so the far library keeps the previous
        # pass's widths and the far field does not thin out behind the hero band.
        prof = dict(prof, w=LEGACY_W[kind])
    keel = prof["keel"] if lod == 0 else 0.0
    acc = Accum()
    hmax = 0.0
    wdir = np.array([WIND_DIR[0], WIND_DIR[1], 0.0])
    placed = 0
    while placed < blades:
        # A TILLER, not a blade.  Grass grows as fans of blades off one crown, and a
        # scatter of independent blades is the single clearest tell that a clump was
        # generated rather than grown -- it has no structure at any scale between the
        # blade and the clump, so at 2.4 m it reads as felt.
        nt = int(rng.integers(prof["tiller"][0], prof["tiller"][1] + 1)) if lod == 0 else 1
        nt = min(nt, blades - placed)
        a = rng.uniform(0, 2 * math.pi)
        r = prof["spread"] * math.sqrt(rng.random())
        crown = np.array([math.cos(a) * r, math.sin(a) * r, 0.0])
        fan = rng.uniform(0, 2 * math.pi)
        under = rng.random() < prof["under"]
        tid = rng.random()
        for j in range(nt):
            # blades of one tiller share a crown and fan out around it
            th = fan + 2 * math.pi * j / max(nt, 1) + rng.normal(0, 0.35)
            rr = rng.uniform(0.0, 0.022) * (1.0 + 2.0 * r / max(prof["spread"], 1e-6))
            base = crown + np.array([math.cos(th) * rr, math.sin(th) * rr, 0.0])
            L = rng.uniform(*prof["h"])
            if under:
                L *= rng.uniform(0.30, 0.62)
            hmax = max(hmax, L)
            w = rng.uniform(*prof["w"]) * (0.80 if under else 1.0)
            lean = WIND_LEAN * rng.uniform(*prof["lean"]) * (0.65 if under else 1.0)
            _blade(acc, rng, prof, base, L, w, lean, segs, keel, wdir,
                   tid * 0.55 + rng.random() * 0.45)
            placed += 1
    if prof["seed"] > 0:
        _seed_heads(acc, rng, max(8, blades // 3), prof, hmax)
    return acc.finish(VPFX + "grass_%s_%03d" % (kind, rng.integers(0, 999999) % 9999),
                      [VPFX + "grass_" + kind]), hmax


def _seed_heads(acc, rng, blades, prof, hmax):
    n = max(1, int(blades * prof["seed"] * SEED_HEAD_FRAC))
    for i in range(n):
        a = rng.uniform(0, 2 * math.pi)
        r = prof["spread"] * 0.7 * math.sqrt(rng.random())
        L = hmax * rng.uniform(1.0, 1.35)
        lean = WIND_LEAN * rng.uniform(1.1, 1.6)
        wdir = np.array([WIND_DIR[0], WIND_DIR[1], 0.0])
        d = _norm(UP * math.cos(lean) + wdir * math.sin(lean))
        pts = [np.array([math.cos(a) * r, math.sin(a) * r, 0.0])]
        for j in range(3):
            d = _norm(d + wdir * 0.22 + np.array([0, 0, -0.16]))
            pts.append(pts[-1] + d * (L / 3))
        pts = np.array(pts)
        tube(acc, pts, np.array([0.0022, 0.0018, 0.0014, 0.0010]), 3, 0)
        # THE PANICLE.  Branches off the culm tip, spikelets along each branch.
        # See PANICLE_N: nine straight spokes off a single point was the whole
        # head, and it is 3-5x under the amplitude the measured 425.8 px/m can
        # resolve.  Every branch and every spikelet here clears the pixel line.
        top = pts[-1]
        m = int(rng.integers(PANICLE_N[0], PANICLE_N[1] + 1))
        ang = rng.random(m) * 2 * math.pi
        pl = rng.uniform(PANICLE_LEN_M[0], PANICLE_LEN_M[1], m)
        # branches leave the culm in whorls up the top ~35 % of it, not all from
        # one node: a panicle is a raceme of racemes and the vertical spread is
        # what stops it reading as a starburst.
        wh = np.zeros(m) if R2970_BEFORE else rng.random(m) ** 0.7 * (0.35 * L)
        base = top - _norm(pts[-1] - pts[-2])[None, :] * wh[:, None]
        tip = base + np.stack([np.cos(ang) * pl * 0.5, np.sin(ang) * pl * 0.5,
                               -pl * rng.uniform(0.3, 1.0, m)], 1)
        R = np.asarray(PANICLE_RAD_M, float)
        for j in range(m):
            b, e = base[j], tip[j]
            if R2970_BEFORE:
                tube(acc, np.array([b, (b + e) / 2, e]), R, 3, 0, gmin=1.0, gmax=1.0)
            else:
                # the branch droops: the mid station sags below the chord, which
                # is 1-2 px of sag over an 8.5-25.5 px branch and is what stops a
                # panicle reading as a starburst
                mid = (b + e) / 2 + np.array([0, 0, -0.18 * pl[j]])
                _hair(acc, np.array([b, mid, e]), R, 0)
            ns = int(rng.integers(PANICLE_SPIKE[0], PANICLE_SPIKE[1] + 1))
            for s in range(ns):
                f = (s + 1.0) / (ns + 1.0)
                p0 = b + (e - b) * f
                sl = pl[j] * rng.uniform(0.28, 0.55)
                p1 = p0 + np.array([math.cos(ang[j] + rng.normal(0, 0.9)) * sl * 0.5,
                                    math.sin(ang[j] + rng.normal(0, 0.9)) * sl * 0.5,
                                    -sl * rng.uniform(0.2, 0.8)])
                _hair(acc, np.array([p0, p1]), R[:2] * 0.85, 0)


# ==================================================================================
# 6b.  THE MID-SCALE GROUND COVER — "sward drifts"           R2-1661
# ==================================================================================
#
# WHY THIS TIER EXISTS.  Until now the ground had exactly two states and nothing in
# between them:
#
#   hero clumps   190-330 channelled blades in tillers, ~4 600 triangles, placed at
#                 ~19 per square metre — but ONLY in the verge band, and the verge
#                 band is drawn along the track.
#   flat colour   everything else.  The infield carries `meadow` clumps on a 1.35 m
#                 jittered grid at ~50 % acceptance, which is 0.28 clumps per square
#                 metre.  At a clump radius of 0.2-0.3 m that is FOUR PER CENT ground
#                 cover.  The other ninety-six per cent is the ground shader, and the
#                 ground shader out there is a per-field flat colour.
#
# Nobody noticed for five beats because the lens never looks at the infield: beats
# 1-5 keep the camera 2-6 m off the deck, where the verge band fills the bottom of
# the frame and the trees fill the top.  Beat 6 climbs to 99-140 m and points a 22 mm
# lens across it, and four per cent cover over a flat colour map is exactly what "we
# just zoom out so you see all the patches in the land" describes.
#
# WHAT COVERAGE ACTUALLY COSTS, AND WHY THE UNIT IS A DRIFT AND NOT A CLUMP.
# Getting the infield to verge density would be 19 clumps/m^2 over 8.4 km^2 — 160
# million instances.  That is not a budget, it is a hang, and it is the same shape of
# argument that made a hero tree tier unbuildable elsewhere in this project.  The
# way out is to make the PLACEABLE UNIT bigger: one drift carries the tufts that
# would otherwise have been twenty separate clumps, so the instance count falls by
# the square of the pitch while the covered area does not move.  Measured against the
# real camera path: 261 k drifts and 117 M instanced triangles, against terrain's
# existing 13.88 G — 0.85 %.
#
# AND THE UNIT IS SIZED BY WHAT THE LENS CAN RESOLVE, NOT BY WHAT GRASS IS.
# The four 4K frames of this ending that exist put the ground at 2.5 cm per pixel
# (f2978, 130 mm, 345 m) and 9.2 cm per pixel (f2811, 22 mm, 259 m), falling to ~36
# cm at a kilometre.  A 4 mm fescue blade is a quarter of a pixel at the BEST of
# those, so a blade out here is not a shape, it is a coverage fraction — the same
# argument the far grass tier already makes for keeping its wide blade.  A drift's
# leaves are therefore 1-6 cm across depending on tier, which is a coarse rough
# sward (cocksfoot, Yorkshire fog, soft rush, dock) and not a mown lawn, because
# a coarse rough sward is what unmanaged infield actually is.
#
# THE MECHANISM IS SHADOW, NOT SILHOUETTE.  The sun ships at 12.47 deg elevation, so
# everything vertical throws a shadow 4.5 times its own height.  A 0.4 m tuft lays
# down 1.8 m of shadow; a 1.0 m rush spike lays down 4.5 m.  Screen cover from an
# oblique view is
#
#     1 - exp( -lambda * (4 r^2 + 2 r h cot(elevation)) )
#
# and at f2811's 22.6 deg axis, lambda = 1.6/m^2 of r = 0.22 m, h = 0.38 m tufts is
# 61 % — from 35 % PLAN cover, because an oblique view of vertical things is mostly
# their sides.  That is why this works at 400 triangles per drift and would not work
# as a flat texture.
#
# WHAT IT IS NOT.  It is not a fix for the field colour, which is R2-1661 part 3
# below, and it is not a substitute for the hero band: inside `GRASS_HERO_D` the real
# clumps still own the ground and the drift density ramps to zero under them.

SWARD_Q = float(os.environ.get("TERRAIN_SWARD", "1.0"))   # density dial, never design

# R2-1824: how far inboard of the LAST tier's d1 its uncompensated outward fade starts.
# An internal crossfade can be short because the next tier fills in behind it; this one
# fades into nothing, so it is deliberately much longer than the 24 m used at the joins.
# 190 m puts the fade over dcam3 860..1076 m, which at f2760's ~36 cm per pixel out
# there is ~600 px of screen rather than the 15 px a 50 m fade would have given.
SWARD_TAIL_M = 190.0

# tag  d0     d1     pitch  tuft/m2 blades segs  r(m)          h(m)        w half (m)
#                                                                          tall/m2 tall h
#
# `lam` AND `tall` ARE GROUND DENSITIES, PER SQUARE METRE OF WORLD, and the drift is
# populated off `pitch ** 2` and not off its own drawn area.  This is not the same
# number and getting it wrong is a 2.1x error in the direction that is hardest to
# see.  A drift is drawn over 1.45 x its pitch (the anti-tiling rule above), so 2.1
# drift centres lie within reach of any ground point, and each contributes
# n_tuft / (1.45 pitch)^2 tufts per square metre:
#
#     ground density = 2.1 * n_tuft / (2.1 * pitch^2) = n_tuft / pitch^2
#
# -- the overlap cancels exactly.  Populating off the drawn area instead would put
# 2.1 * lam on the ground, and tier B would have come out at 88 % screen cover: a
# solid dark mat, which is the flat wash again in the other direction.  So `lam` is
# solved from the screen-cover law in the block comment, backwards, for a MEAN of
# ~72 % after the ~0.72 mean thinning the density masks apply:
#
#     lam = 1.27 / (0.72 * (4 r^2 + 2 r h cot e))      e = the tier's view elevation
#
# tier A is seen at ~30 deg (it is the bottom of the frame), C at ~8 deg (it is out
# near the horizon, where an oblique view does most of the covering for free -- which
# is why the cheapest tier needs the fewest tufts and not the most).
SWARD_TIERS = (
    dict(tag="A", d0=30.0,   d1=200.0,  pitch=2.30, lam=5.65, blades=(4, 7), segs=3,
         r=(0.13, 0.24), h=(0.10, 0.45), w=(0.0050, 0.0120),
         tall=0.100, th=(0.50, 0.95)),
    dict(tag="B", d0=200.0,  d1=520.0,  pitch=3.60, lam=2.80, blades=(3, 6), segs=2,
         r=(0.17, 0.31), h=(0.14, 0.55), w=(0.0080, 0.0180),
         tall=0.075, th=(0.60, 1.10)),
    dict(tag="C", d0=520.0,  d1=1050.0, pitch=6.00, lam=0.65, blades=(3, 5), segs=2,
         r=(0.24, 0.46), h=(0.20, 0.70), w=(0.0140, 0.0300),
         tall=0.055, th=(0.80, 1.40)),
)


def _sward_leaf(acc, rng, base, L, w, lean, segs, wdir, pid, tilt=0.0):
    """One coarse leaf: a tapered FLAT ribbon.  2 * segs triangles, no keel.

    The keel exists on a hero blade because at 2.4 m the two halves of a channelled
    blade shade differently and that light/dark pair is most of the read.  At 40 m
    and beyond the whole blade is under a pixel wide, so the keel doubles the
    triangle count to modulate something nobody can sample.  Flat, here, on purpose.
    """
    az = wdir * math.sin(lean) + np.array([rng.normal(0, 0.30), rng.normal(0, 0.30),
                                           0.0])
    d = _norm(UP * math.cos(lean + tilt) + az * (1.0 + 2.2 * tilt))
    pts = [base]
    ws = [w]
    for j in range(segs):
        fj = (j + 1) / segs
        d = _norm(d + wdir * (0.60 * lean * fj) + np.array([0, 0, -0.34 * fj * fj]))
        pts.append(pts[-1] + d * (L / segs))
        ws.append(w * max(0.06, 1.0 - 0.92 * fj ** 1.5))
    pts = np.array(pts); ws = np.array(ws)
    k = len(pts)
    t, _, _ = _frames(pts)
    side = _norm(np.cross(t, wdir + np.array([0.03, 0.02, 0.9])))
    V = np.concatenate([pts + side * ws[:, None], pts - side * ws[:, None]], 0)
    i = np.arange(k - 1)
    Q = np.stack([i, i + 1, k + i + 1, k + i], -1)
    G = np.linspace(0.0, 1.0, k)
    acc.add(V, quads=Q, mat=0, attr=np.full(2 * k, pid), grad=np.tile(G, 2))


def gen_sward(rng, tier, kind="meadow", pitch=None):
    """One sward drift: a square metre-scale patch of rough ground cover.

    Authored at TRUE WORLD SIZE over `pitch` metres square and returned with its own
    height, so `gn_kind` normalises and rescales it back to (almost) the size it was
    drawn at.  Every drift in the library is generated independently — there is no
    template being rotated, which is the named failure on this project.
    """
    T = tier
    pitch = T["pitch"] if pitch is None else pitch
    # DRAWN OVER 1.45 x THE PITCH IT IS PLACED AT.  A patch drawn at exactly the
    # placement pitch tiles, and a tiling ground cover seen from 100 m up is a grid,
    # which is a worse artefact than the wash it replaces.  Drawing wide and placing
    # close makes neighbours overlap by ~2.1x in area, so no seam survives.
    half = pitch * 1.45 * 0.5
    # THE GROUND EACH DRIFT OWNS, not the area it is drawn over.  See SWARD_TIERS.
    own = pitch * pitch
    acc = Accum()
    wdir = np.array([WIND_DIR[0], WIND_DIR[1], 0.0])
    hmax = 1e-3

    n_tuft = max(3, int(round(T["lam"] * own * rng.uniform(0.82, 1.20))))
    # crowns on a relaxed jitter, not a pure uniform: real tufts sit in drifts with
    # bare ground between them, and a uniform scatter reads as a texture
    dx = rng.random(n_tuft) * 2 - 1
    dy = rng.random(n_tuft) * 2 - 1
    cl = 0.5 + 0.5 * np.sin(dx * 3.1 + rng.random() * 6.3) * np.sin(dy * 2.7
                                                                   + rng.random() * 6.3)
    keepc = rng.random(n_tuft) < (0.45 + 0.75 * cl)
    dx, dy = dx[keepc], dy[keepc]
    for i in range(len(dx)):
        crown = np.array([dx[i] * half, dy[i] * half, 0.0])
        rr = rng.uniform(*T["r"])
        L = rng.uniform(*T["h"])
        nb = int(rng.integers(T["blades"][0], T["blades"][1] + 1))
        fan = rng.uniform(0, 2 * math.pi)
        tid = rng.random()
        hmax = max(hmax, L)
        for j in range(nb):
            th = fan + 2 * math.pi * j / nb + rng.normal(0, 0.42)
            r0 = rng.uniform(0.0, 0.16) * rr
            b = crown + np.array([math.cos(th) * r0, math.sin(th) * r0, 0.0])
            # lean is set so the leaf tip lands near the tuft radius: that is what
            # makes the footprint the `r` the coverage arithmetic was done with
            lean = math.atan2(rr * rng.uniform(0.55, 1.25), max(L, 1e-3))
            lean = min(lean, 1.30) * WIND_LEAN * 0.55 + 0.55 * lean
            _sward_leaf(acc, rng, b, L, rng.uniform(*T["w"]), lean, T["segs"], wdir,
                        tid * 0.55 + rng.random() * 0.45)

    # PROSTRATE LITTER.  A few near-flat leaves lying in the sward.  2 triangles each
    # and they buy plan cover the erect tufts cannot, but they are kept to a minority
    # because a horizontal ribbon under a 12.47 deg sun is a painted patch: it holds
    # no shadow and no silhouette, and a field of them would be the flat wash again
    # in a different colour.
    n_lit = max(1, int(round(T["lam"] * own * 0.34)))
    for i in range(n_lit):
        b = np.array([rng.uniform(-half, half), rng.uniform(-half, half), 0.006])
        _sward_leaf(acc, rng, b, rng.uniform(*T["h"]) * rng.uniform(0.55, 1.05),
                    rng.uniform(*T["w"]) * 1.5, rng.uniform(1.02, 1.36), T["segs"],
                    wdir, rng.random(), tilt=rng.uniform(0.10, 0.34))

    # SPIKES.  Rush, dock and seeding grass standing clear of the sward.  Sparse and
    # cheap, and worth their triangles entirely for their shadows: at 12.47 deg a
    # 1.0 m spike lays 4.5 m of shadow across the ground, and 0.07 spikes per square
    # metre is the fine dark stipple that reads as farmland from the air.
    n_tall = max(0, int(round(T["tall"] * own * rng.uniform(0.6, 1.5))))
    for i in range(n_tall):
        b = np.array([rng.uniform(-half, half), rng.uniform(-half, half), 0.0])
        L = rng.uniform(*T["th"])
        hmax = max(hmax, L)
        pid = rng.random()
        for j in range(2):
            _sward_leaf(acc, rng, b, L * rng.uniform(0.82, 1.0),
                        rng.uniform(*T["w"]) * 0.75,
                        WIND_LEAN * rng.uniform(0.55, 1.05) + 0.12 * j,
                        max(2, T["segs"]), wdir, pid)

    me = acc.finish(VPFX + "sward_%s_%s_%03d" % (kind, T["tag"],
                                                 rng.integers(0, 999999) % 9999),
                    [VPFX + "grass_" + kind])
    # THE SECOND RETURN IS THE PLAN HALF-EXTENT, NOT THE PLANT HEIGHT, and that is not
    # cosmetic.  `gn_kind` normalises every library mesh by this number and then
    # rescales the lot by one target, so whatever is returned here becomes the thing
    # every drift is made equal in.  Returning the tallest plant would have done
    # exactly that to the tallest plant: a drift that happened to draw no rush spike
    # tops out at 0.70 m against a library mean of 1.30 and would have been scaled up
    # 1.86x -- a 9 m drift on a 6 m pitch, its leaves 1.86x the width the resolvable-
    # floor arithmetic chose, and the variation driven by a dice roll about spikes.
    # `half` is a per-tier constant, so the normalise-and-rescale is exactly 1.0 and
    # the drift lands at the size it was drawn at.
    return me, half


def build_sward(gr, gz, cam, coll, rng, q, ras):
    """The mid-scale ground cover, tiered by TRUE DISTANCE TO THE LENS.

    `habitat`'s `dcam3` and not `dcam`: see `CameraPath`.  On a horizontal metric the
    ground under beat 6's 140 m crane scores zero and buys the densest tier for
    itself, while the several hundred metres of infield the wide lens is pointed at
    score 200-600 and buy the cheapest.  That is the wrong way round, and it is the
    only place in the film where the two metrics disagree, because beats 1-5 keep the
    lens 2-6 m above the ground it is looking at.
    """
    stats = {}
    tot = 0
    itris = 0
    nlib = max(4, int(round(13 * (0.4 + 0.6 * q))))
    kinds = list(GRASS.keys())
    X0, X1, Y0, Y1 = -1520.0, 1440.0, -1120.0, 1840.0

    for T in SWARD_TIERS:
        lib = {}
        for kd in kinds:
            lib[kd] = [gen_sward(np.random.default_rng(int(rng.integers(1 << 31))),
                                 T, kd) for _ in range(nlib)]
        mt = int(np.mean([_mesh_tris(m) for m, _ in lib[kinds[0]]]))
        log("  sward %s library: %d x %d drifts, %d tris each (mean)"
            % (T["tag"], len(kinds), nlib, mt))

        # THE TIERS CROSSFADE, THEY DO NOT BUTT.  A hard cut at 200 m and 520 m would
        # lay two concentric density rings across the exact frame this is being built
        # for -- a new artefact in place of the old one.  Each tier fades out over
        # [d1 - 24, d1 + 26] and the next fades in over the same interval, and a
        # smoothstep plus its own complement sums to one, so the cover is continuous
        # across the join even though the drift that carries it changes.
        lo, hi = T["d0"] - 24.0, T["d1"] + 26.0
        sx, sy, sr = jitter_grid(X0, X1, Y0, Y1, T["pitch"], 8100 + ord(T["tag"]))
        r0 = ras.sample(sx, sy)
        band = (r0["dcam3"] >= lo) & (r0["dcam3"] < hi)
        band &= r0["f"] > 12.0
        sx, sy, sr = sx[band], sy[band], sr[band]
        if not len(sx):
            continue
        h = habitat(gr, gz, cam, sx, sy, ras)

        # DENSITY.  Everything here thins the cover; nothing raises it above 1, so a
        # drift is never asked to be denser than it was drawn.
        dens = np.ones(len(sx))
        dens *= smoothstep(lo, T["d0"] + 26.0, h["dcam3"])   # under the hero band the
        #                                            real clumps own the ground
        if T is not SWARD_TIERS[-1]:
            dens *= smoothstep(hi, T["d1"] - 24.0, h["dcam3"])   # ... and the next
        #                                            tier owns it beyond d1
        else:
            # THE LAST TIER HAS NOBODY TO HAND TO, AND THAT IS WHY IT WAS CUT  R2-1824
            #
            # The line above is a crossfade: tier N fades out over [d1-24, d1+26] while
            # tier N+1 fades in over the same interval, and a smoothstep plus its own
            # complement sums to one, so the cover never dips. The guard exists because
            # the last tier has no successor -- but the consequence was that tier C kept
            # FULL density right up to `band`'s `dcam3 < d1 + 26` and then stopped dead.
            # MEASURED at f2760: 0.586 cover to 0.000 across zero metres at 1076 m.
            #
            # That is precisely the artefact this whole section was written to avoid,
            # sitting at the one radius the crossfade could not reach. Beyond it there
            # is no layer at all, so the fade here is UNCOMPENSATED and has to be longer
            # than a handoff: `SWARD_TAIL_M` dissolves the layer into the far field
            # instead of ending it.
            #
            # STRICTLY A SOFTENING. It only ever multiplies density DOWN, so it cannot
            # add a drift, cannot cost a triangle, and cannot move any tier boundary
            # inboard of it -- tiers A and B are untouched by construction.
            dens *= smoothstep(hi, T["d1"] - SWARD_TAIL_M, h["dcam3"])
        dens *= smoothstep(12.0, 34.0, h["f"])          # the verge band owns the rim
        dens *= (1.0 - h["paved"])          # R2-1821: architecture's DECLARED concrete,
        #                        not the drawn paddock district.  1.0 and not 0.90 --
        #                        on concrete the answer is none, and outside the 3 m
        #                        standoff the answer is all of it.
        dens *= (1.0 - 0.72 * h["wood"])                # a wood floor is ferns, not sward
        dens *= (1.0 - 0.55 * smoothstep(0.18, 0.46, h["slope"]))
        # patchiness at 38 m and 9 m, so the infield has bare ground in it and does
        # not become a second flat wash
        dens *= np.clip(0.50 + 0.62 * (0.5 + 0.5 * fbm(sx / 38.0, sy / 38.0, 3,
                                                       seed=811)), 0, 1)
        dens *= np.clip(0.62 + 0.50 * (0.5 + 0.5 * fbm(sx / 9.0, sy / 9.0, 2,
                                                       seed=813)), 0, 1)
        take = np.where(sr < np.clip(dens, 0, 1) * SWARD_Q * (0.55 + 0.45 * q))[0]
        take = take[outside_corridor(sx[take], sy[take], 2.0)]
        if not len(take):
            continue
        hs = {k: v[take] for k, v in h.items()}
        P = np.stack([sx[take], sy[take], gz(sx[take], sy[take]) - 0.045], 1)

        # kind by habitat, on the same weights `build_grass` uses, so the drifts and
        # the clumps they sit between are the same vegetation
        mown = smoothstep(34.0, 2.0, hs["f"])
        dry = smoothstep(3.5, 9.0, hs["z"]) + smoothstep(0.12, 0.34, hs["slope"]) * 0.5
        wet = smoothstep(-1.0, -3.4, hs["z"])
        W = np.stack([0.10 + 0.55 * mown,
                      0.40 + 0.40 * (1 - mown),
                      0.22 + 0.62 * (1 - mown) * (1 - wet),
                      0.06 + 0.72 * np.clip(dry, 0, 1),
                      0.02 + 0.80 * wet * (1 - mown)], 1)
        W = np.clip(W, 1e-4, None); W /= W.sum(1, keepdims=True)
        ki = (rng.random(len(take))[:, None] > np.cumsum(W, 1)).sum(1) \
            .clip(0, len(kinds) - 1)

        for j, kd in enumerate(kinds):
            m = ki == j
            if not m.any():
                continue
            # every drift in a tier was authored to the same plan half-extent, so
            # `gn_kind`'s normalise-and-rescale is the identity and the +-9 % is the
            # only size variation there is
            th = lib[kd][0][1] * (1.0 + rng.normal(0, 0.09, int(m.sum())))
            got = gn_kind("sward_%s_%s" % (kd, T["tag"]), lib[kd], P[m], th, rng,
                          coll, lean=0.55, wide=0.07)
            tot += got
            itris += int(m.sum()) * mt
        log("  sward %s: %d drifts placed (pitch %.2f m, d %.0f-%.0f m)"
            % (T["tag"], len(take), T["pitch"], T["d0"], T["d1"]))
        stats["sward_" + T["tag"]] = int(len(take))

    log("  sward: %d drifts, %d instanced tris" % (tot, itris))
    stats["sward_drifts"] = int(tot)
    stats["sward_library"] = len(SWARD_TIERS) * len(kinds) * nlib
    stats["instanced_tris"] = itris
    return stats


# ==================================================================================
# 7.  MATERIALS — every one procedural, nothing loaded from disk
# ==================================================================================

class NT:
    """Tiny node-graph DSL so the shaders below read like recipes."""

    def __init__(self, name):
        m = bpy.data.materials.get(name)
        if m is None:
            m = bpy.data.materials.new(name)
        m.use_nodes = True
        self.m = m
        self.t = m.node_tree
        self.t.nodes.clear()
        self.x = 0

    def n(self, typ, **kw):
        nd = self.t.nodes.new(typ)
        self.x += 190
        nd.location = (self.x, 0)
        for k, v in kw.items():
            if hasattr(nd, k):
                setattr(nd, k, v)
        return nd

    def link(self, a, ai, b, bi):
        so = a.outputs[ai] if isinstance(ai, int) else a.outputs[ai]
        si = b.inputs[bi] if isinstance(bi, int) else b.inputs[bi]
        self.t.links.new(so, si)

    def set(self, nd, key, val):
        nd.inputs[key].default_value = val

    def mix(self, fac, a, b, blend="MIX"):
        n = self.n("ShaderNodeMix", data_type="RGBA", blend_type=blend)
        if isinstance(fac, tuple) and hasattr(fac[0], "outputs"):
            self.link(fac[0], fac[1], n, 0)
        else:
            n.inputs[0].default_value = float(fac)
        for i, s in ((6, a), (7, b)):
            if isinstance(s, tuple) and hasattr(s[0], "outputs"):
                self.link(s[0], s[1], n, i)
            else:
                n.inputs[i].default_value = (*s, 1.0) if len(s) == 3 else s
        return n

    def noise(self, scale, detail=8.0, rough=0.55, vec=None, dist=0.0):
        n = self.n("ShaderNodeTexNoise")
        self.set(n, "Scale", scale); self.set(n, "Detail", detail)
        self.set(n, "Roughness", rough); self.set(n, "Distortion", dist)
        if vec is not None:
            self.link(vec[0], vec[1], n, 0)
        return n

    def ramp(self, src, stops):
        n = self.n("ShaderNodeValToRGB")
        self.link(src[0], src[1], n, 0)
        el = n.color_ramp.elements
        while len(el) > 1:
            el.remove(el[-1])
        el[0].position = stops[0][0]; el[0].color = (*stops[0][1], 1.0)
        for p, c in stops[1:]:
            e = el.new(p); e.color = (*c, 1.0)
        return n

    def math(self, op, a=None, b=None, clamp=False):
        n = self.n("ShaderNodeMath", operation=op, use_clamp=clamp)
        for i, s in ((0, a), (1, b)):
            if s is None:
                continue
            if isinstance(s, tuple):
                self.link(s[0], s[1], n, i)
            else:
                n.inputs[i].default_value = s
        return n

    def attr(self, name, kind="GEOMETRY"):
        n = self.n("ShaderNodeAttribute", attribute_type=kind)
        n.attribute_name = name
        return n

    def out(self, shader, si=0):
        o = self.n("ShaderNodeOutputMaterial")
        self.link(shader, si, o, "Surface")
        return o


def _mix2(t, fac, a, b):
    return t.mix(fac, a, b)


# --- bark ---------------------------------------------------------------------------
BARK = {
    # base colour, ridge colour, ridge scale, ridge strength, style
    #
    # These were measured-ish reflectances taken straight from "what colour is that bark",
    # and every trunk in the world came out a white stick.  Two reasons, both real:
    # a trunk is a near-vertical cylinder lit by a 12.5 deg sun, so it takes the light
    # almost face-on where the ground takes it at a graze; and real bark is dirty,
    # lichened and self-shadowed in its fissures in a way a base colour does not capture.
    # Everything pale is pulled down about a third.  Birch stays the palest thing in the
    # world because birch is, but 0.34 not 0.52.
    "oak":      ((0.078, 0.058, 0.042), (0.024, 0.018, 0.014), 26.0, 0.55, "ridge"),
    "poplar":   ((0.098, 0.090, 0.070), (0.036, 0.033, 0.026), 34.0, 0.42, "ridge"),
    "pine":     ((0.155, 0.072, 0.034), (0.052, 0.028, 0.017), 15.0, 0.62, "plate"),
    "birch":    ((0.340, 0.322, 0.296), (0.038, 0.034, 0.032), 22.0, 0.28, "birch"),
    "plane":    ((0.196, 0.188, 0.156), (0.078, 0.084, 0.056), 9.0, 0.34, "mottle"),
    "cypress":  ((0.086, 0.068, 0.050), (0.031, 0.024, 0.019), 40.0, 0.40, "ridge"),
    "willow":   ((0.086, 0.072, 0.054), (0.023, 0.019, 0.015), 20.0, 0.65, "ridge"),
    "hawthorn": ((0.098, 0.080, 0.062), (0.030, 0.024, 0.018), 30.0, 0.50, "ridge"),
    "rowan":    ((0.122, 0.112, 0.094), (0.045, 0.040, 0.034), 32.0, 0.30, "ridge"),
    "snag":     ((0.188, 0.176, 0.158), (0.062, 0.056, 0.049), 18.0, 0.70, "ridge"),
}


def mat_bark(key):
    base, ridge, scale, strength, style = BARK[key]
    t = NT(VPFX + "bark_" + key)
    co = t.n("ShaderNodeTexCoord")
    mp = t.n("ShaderNodeMapping")
    t.link(co, "Object", mp, 0)
    t.set(mp, "Scale", (1.0, 1.0, 0.16 if style != "plate" else 0.34))
    oi = t.n("ShaderNodeObjectInfo")

    n1 = t.noise(scale, 9.0, 0.62, vec=(mp, 0), dist=0.9)
    if style == "birch":
        # lenticels: horizontal dashes, plus dark base plates low on the trunk
        wv = t.n("ShaderNodeTexWave", wave_type="BANDS", bands_direction="Z")
        t.link(mp, 0, wv, 0)
        t.set(wv, "Scale", 26.0); t.set(wv, "Distortion", 22.0); t.set(wv, "Detail", 3.0)
        m = t.math("MULTIPLY", (wv, 1), (n1, 0))
        rmp = t.ramp((m, 0), [(0.35, (1, 1, 1)), (0.62, (0, 0, 0))])
    elif style == "mottle":
        vo = t.n("ShaderNodeTexVoronoi", feature="F1")
        t.link(mp, 0, vo, 0); t.set(vo, "Scale", scale); t.set(vo, "Randomness", 1.0)
        rmp = t.ramp((vo, 0), [(0.0, (0, 0, 0)), (0.30, (1, 1, 1)), (0.55, (0.35, 0.35, 0.35))])
    elif style == "plate":
        vo = t.n("ShaderNodeTexVoronoi", feature="DISTANCE_TO_EDGE")
        t.link(mp, 0, vo, 0); t.set(vo, "Scale", scale); t.set(vo, "Randomness", 0.9)
        rmp = t.ramp((vo, 0), [(0.0, (0, 0, 0)), (0.13, (1, 1, 1))])
    else:
        rmp = t.ramp((n1, 0), [(0.34, (0, 0, 0)), (0.66, (1, 1, 1))])

    col = t.mix((rmp, 0), ridge, base)
    # young wood at the twig ends is smoother and lighter; pgrad is 0 at the base
    pg = t.attr("pgrad")
    young = t.mix((pg, 2), (col, 2), tuple(min(1.0, c * 2.1 + 0.05) for c in base))
    # per-instance variation: whole trees differ in tone and value
    hs = t.n("ShaderNodeHueSaturation")
    t.link(young, 2, hs, "Color")
    hshift = t.n("ShaderNodeMapRange")
    t.link(oi, "Random", hshift, 0)
    t.set(hshift, "To Min", 0.455); t.set(hshift, "To Max", 0.545)
    t.link(hshift, 0, hs, "Hue")
    vshift = t.n("ShaderNodeMapRange")
    t.link(oi, "Random", vshift, 0)
    t.set(vshift, "To Min", 0.62); t.set(vshift, "To Max", 1.42)
    t.link(vshift, 0, hs, "Value")

    fine = t.noise(scale * 9.0, 6.0, 0.6, vec=(mp, 0))
    bump = t.n("ShaderNodeBump")
    t.set(bump, "Strength", strength); t.set(bump, "Distance", 0.012)
    t.link(fine, 0, bump, "Height")
    bump2 = t.n("ShaderNodeBump")
    t.set(bump2, "Strength", strength * 1.1); t.set(bump2, "Distance", 0.05)
    t.link(rmp, 0, bump2, "Height"); t.link(bump, 0, bump2, "Normal")

    p = t.n("ShaderNodeBsdfPrincipled")
    t.link(hs, 0, p, "Base Color")
    t.link(bump2, 0, p, "Normal")
    t.set(p, "Roughness", 0.86); t.set(p, "Specular IOR Level", 0.22)
    t.out(p)
    return t.m


# --- foliage ------------------------------------------------------------------------
LEAF = {   # summer colour, autumn colour, translucency, roughness
    "oak":      ((0.055, 0.098, 0.028), (0.230, 0.120, 0.030), 0.30, 0.42),
    "poplar":   ((0.075, 0.135, 0.040), (0.280, 0.215, 0.045), 0.36, 0.36),
    "pine":     ((0.031, 0.058, 0.030), (0.052, 0.062, 0.030), 0.18, 0.50),
    "birch":    ((0.078, 0.128, 0.038), (0.300, 0.230, 0.048), 0.40, 0.34),
    "plane":    ((0.062, 0.105, 0.032), (0.220, 0.140, 0.038), 0.30, 0.40),
    "cypress":  ((0.026, 0.046, 0.028), (0.032, 0.048, 0.028), 0.14, 0.52),
    "willow":   ((0.068, 0.112, 0.046), (0.215, 0.185, 0.055), 0.38, 0.38),
    "hawthorn": ((0.042, 0.082, 0.026), (0.170, 0.098, 0.030), 0.26, 0.44),
    "rowan":    ((0.058, 0.100, 0.032), (0.290, 0.105, 0.030), 0.32, 0.40),
    "sapling":  ((0.086, 0.140, 0.042), (0.260, 0.190, 0.048), 0.42, 0.34),
    "shrub_bramble": ((0.048, 0.076, 0.028), (0.180, 0.075, 0.045), 0.28, 0.44),
    "shrub_gorse":   ((0.036, 0.062, 0.024), (0.120, 0.098, 0.030), 0.20, 0.50),
    "shrub_hazel":   ((0.062, 0.108, 0.034), (0.240, 0.170, 0.042), 0.34, 0.40),
    "shrub_broom":   ((0.044, 0.078, 0.026), (0.150, 0.130, 0.034), 0.24, 0.46),
    "shrub_juniper": ((0.030, 0.050, 0.032), (0.036, 0.054, 0.032), 0.16, 0.52),
    "fern":     ((0.048, 0.090, 0.030), (0.200, 0.150, 0.040), 0.44, 0.36),
}


def mat_leaf(key):
    summer, autumn, trans, rough = LEAF[key]
    t = NT(VPFX + "leaf_" + key)
    oi = t.n("ShaderNodeObjectInfo")
    pid = t.attr("pid")        # per-leaf random inside one tree
    pg = t.attr("pgrad")       # 0 at petiole, 1 at tip

    # Per-instance season: most trees green, a minority turning.  The first cut opened at
    # Random 0.68 and ran to 0.85 mix, which turns a third of the wood and reads as late
    # October -- in a wide it looked like half the treeline was dead.  0.82/0.62 turns
    # about a fifth, which is early autumn: colour in the mass, not a bonfire.
    season = t.n("ShaderNodeMapRange")
    t.link(oi, "Random", season, 0)
    t.set(season, "From Min", 0.82); t.set(season, "From Max", 1.0)
    t.set(season, "To Min", 0.0); t.set(season, "To Max", 0.62)
    season.clamp = True
    # per-leaf jitter on top, so a turning tree turns leaf by leaf
    sj = t.math("ADD", (season, 0), None)
    jit = t.math("MULTIPLY", (pid, 2), 0.16)
    t.link(jit, 0, sj, 1)
    sjc = t.math("MULTIPLY", (sj, 0), 1.0, clamp=True)
    col = t.mix((sjc, 0), summer, autumn)

    # tip / vein value gradient
    tipmix = t.math("MULTIPLY", (pg, 2), 0.45)
    col2 = t.mix((tipmix, 0), (col, 2), tuple(c * 1.55 + 0.012 for c in summer))

    hs = t.n("ShaderNodeHueSaturation")
    t.link(col2, 2, hs, "Color")
    hv = t.n("ShaderNodeMapRange")
    t.link(oi, "Random", hv, 0)
    t.set(hv, "To Min", 0.470); t.set(hv, "To Max", 0.532)
    t.link(hv, 0, hs, "Hue")
    vv = t.n("ShaderNodeMapRange")
    t.link(pid, 2, vv, 0)
    t.set(vv, "To Min", 0.72); t.set(vv, "To Max", 1.30)
    t.link(vv, 0, hs, "Value")

    p = t.n("ShaderNodeBsdfPrincipled")
    t.link(hs, 0, p, "Base Color")
    t.set(p, "Roughness", rough)
    t.set(p, "Specular IOR Level", 0.34)
    tr = t.n("ShaderNodeBsdfTranslucent")
    t.link(hs, 0, tr, "Color")
    sh = t.n("ShaderNodeMixShader")
    sh.inputs[0].default_value = trans
    t.link(p, 0, sh, 1); t.link(tr, 0, sh, 2)

    # PER-INSTANCE DEFOLIATION.  Each instance drops a different random subset of its
    # own leaves, so two instances of the same base mesh do not share a silhouette.
    thr = t.n("ShaderNodeMapRange")
    t.link(oi, "Random", thr, 0)
    t.set(thr, "To Min", 0.74); t.set(thr, "To Max", 1.01)
    keep = t.math("LESS_THAN", (pid, 2), (thr, 0))
    tp = t.n("ShaderNodeBsdfTransparent")
    fin = t.n("ShaderNodeMixShader")
    t.link(keep, 0, fin, 0)
    t.link(tp, 0, fin, 1); t.link(sh, 0, fin, 2)
    t.out(fin)
    t.m.use_backface_culling = False
    return t.m


def mat_canopy(key):
    """The L2 canopy shell: a PERFORATED leaf mass, not a solid one.

    A distant canopy is 55-75 % gaps by projected area, and those gaps are what makes a
    tree shadow a pool of dapple instead of a hole.  The shells were shaded with the
    leaf material, whose only transparency is the per-INSTANCE defoliation test, so
    every L2 shell was fully opaque: seen from a helicopter the woodland cast flat grey
    slabs, which is exactly what "tree shadows are mushy blobs because the canopies
    have no leaf geometry" describes.

    Cutting real leaves at L2 is not the answer -- an L2 tree is 37 px at a kilometre
    and 24 646 of them at hero leaf density is not a budget, it is a hang.  What IS the
    answer is that the SHADOW does not care how the gaps are made.  So the shell is cut
    by two noise fields in OBJECT space, at leaf scale (60 mm) and at twig-cluster
    scale (0.34 m), to a coverage of about 0.55 -- and because Cycles evaluates the
    same shader on shadow rays, the dapple is in the shadow as well as in the tree.

    The colour is the species' own summer leaf, darkened: a canopy at a kilometre is
    mostly self-shadowed, and shell value already rides low on `pid` for that reason.
    """
    summer, autumn, trans, rough = LEAF[key]
    t = NT(VPFX + "canopy_" + key)
    oi = t.n("ShaderNodeObjectInfo")
    pid = t.attr("pid")
    co = t.n("ShaderNodeTexCoord")
    season = t.n("ShaderNodeMapRange")
    t.link(oi, "Random", season, 0)
    t.set(season, "From Min", 0.82); t.set(season, "From Max", 1.0)
    t.set(season, "To Min", 0.0); t.set(season, "To Max", 0.55)
    season.clamp = True
    col = t.mix((season, 0), summer, autumn)
    hs = t.n("ShaderNodeHueSaturation")
    t.link(col, 2, hs, "Color")
    vv = t.n("ShaderNodeMapRange")
    t.link(pid, 2, vv, 0)
    t.set(vv, "To Min", 0.58); t.set(vv, "To Max", 1.08)
    t.link(vv, 0, hs, "Value")
    p = t.n("ShaderNodeBsdfPrincipled")
    t.link(hs, 0, p, "Base Color")
    t.set(p, "Roughness", min(0.92, rough + 0.22))
    t.set(p, "Specular IOR Level", 0.12)
    tr = t.n("ShaderNodeBsdfTranslucent")
    t.link(hs, 0, tr, "Color")
    sh = t.n("ShaderNodeMixShader")
    sh.inputs[0].default_value = trans * 0.8
    t.link(p, 0, sh, 1); t.link(tr, 0, sh, 2)
    # THE PERFORATION.  A leaf-scale cut whose DENSITY varies at twig-cluster scale.
    #
    # Thresholding the PRODUCT of two noises was the first attempt and it is a trap:
    # a Noise Texture is ~N(0.5, 0.13), so the product is ~N(0.25, 0.094) and any fixed
    # threshold picked by eye lands in the wrong tail -- 0.055..0.165 would have kept
    # ~85 % of the shell, i.e. done almost nothing.  Driving the THRESHOLD of a
    # single-noise cut with the cluster noise keeps the statistics knowable: `nl` is
    # ~N(0.5, 0.13) and the cut sits at 0.40 + 0.18*nc, mean 0.49, so coverage is
    # ~0.55 by construction and the clusters modulate where the holes gather rather
    # than how many there are.
    nl = t.noise(17.0, 2.0, 0.55, vec=(co, "Object"))
    nc = t.noise(3.1, 3.0, 0.62, vec=(co, "Object"))
    fm0 = t.math("ADD", 0.40, (t.math("MULTIPLY", (nc, 0), 0.18), 0))
    fm1 = t.math("ADD", (fm0, 0), 0.10)
    keep = t.n("ShaderNodeMapRange")
    t.link(nl, 0, keep, 0)
    t.link(fm0, 0, keep, "From Min")
    t.link(fm1, 0, keep, "From Max")
    t.set(keep, "To Min", 0.0); t.set(keep, "To Max", 1.0)
    keep.clamp = True
    tp = t.n("ShaderNodeBsdfTransparent")
    fin = t.n("ShaderNodeMixShader")
    t.link(keep, 0, fin, 0)
    t.link(tp, 0, fin, 1); t.link(sh, 0, fin, 2)
    t.out(fin)
    t.m.use_backface_culling = False
    return t.m


GRASS = {   # base colour, tip colour, dry colour, translucency
    # The dry tones were 0.17-0.25 mean and up to 80 % of every clump mixed to them from
    # mid-blade up, which under a sun at (1.000, 0.716, 0.387) turned the whole verge to
    # straw -- see `before/*_straw.png`.  Standing dead grass IS that colour, but a mown
    # early-autumn verge is mostly green with dead thatch UNDER it, not bleached tips.
    # The mix is now 0-45 % over the top 45 % of clumps (see mat_grass).
    "fescue":  ((0.032, 0.066, 0.019), (0.086, 0.130, 0.036), (0.128, 0.115, 0.050), 0.42),
    "tussock": ((0.030, 0.056, 0.017), (0.105, 0.128, 0.040), (0.150, 0.128, 0.054), 0.40),
    "meadow":  ((0.036, 0.074, 0.021), (0.135, 0.150, 0.048), (0.186, 0.156, 0.062), 0.48),
    "dry":     ((0.062, 0.060, 0.027), (0.190, 0.160, 0.062), (0.235, 0.192, 0.080), 0.50),
    "reed":    ((0.042, 0.072, 0.027), (0.128, 0.140, 0.052), (0.176, 0.150, 0.062), 0.44),
}


def mat_grass(key):
    base, tip, dry, trans = GRASS[key]
    t = NT(VPFX + "grass_" + key)
    oi = t.n("ShaderNodeObjectInfo")
    pid = t.attr("pid"); pg = t.attr("pgrad")
    g = t.math("POWER", (pg, 2), 0.75)
    col = t.mix((g, 0), base, tip)
    # per-clump dryness, and per-blade jitter within the clump
    dr = t.n("ShaderNodeMapRange")
    t.link(oi, "Random", dr, 0)
    t.set(dr, "From Min", 0.55); t.set(dr, "From Max", 1.0)
    t.set(dr, "To Min", 0.0); t.set(dr, "To Max", 0.45); dr.clamp = True
    dj = t.math("ADD", (dr, 0), None)
    t.link(t.math("MULTIPLY", (pid, 2), 0.30), 0, dj, 1)
    djc = t.math("MULTIPLY", (dj, 0), 1.0, clamp=True)
    # dry only from mid-blade upward: bases stay green
    dmask = t.math("MULTIPLY", (djc, 0), (pg, 2))
    col2 = t.mix((dmask, 0), (col, 2), dry)
    hs = t.n("ShaderNodeHueSaturation")
    t.link(col2, 2, hs, "Color")
    vv = t.n("ShaderNodeMapRange")
    t.link(pid, 2, vv, 0)
    t.set(vv, "To Min", 0.68); t.set(vv, "To Max", 1.34)
    t.link(vv, 0, hs, "Value")
    p = t.n("ShaderNodeBsdfPrincipled")
    t.link(hs, 0, p, "Base Color")
    t.set(p, "Roughness", 0.44); t.set(p, "Specular IOR Level", 0.40)
    tr = t.n("ShaderNodeBsdfTranslucent")
    t.link(hs, 0, tr, "Color")
    sh = t.n("ShaderNodeMixShader")
    sh.inputs[0].default_value = trans
    t.link(p, 0, sh, 1); t.link(tr, 0, sh, 2)
    t.out(sh)
    return t.m


# --- the ground ---------------------------------------------------------------------
#
# CALIBRATED AGAINST world_contract.lambert_radiance, NOT against build_terrain.md 2.1.
# Section 2.1 of that note published an assumed rig (sun 120 W/m2 at (1, .735, .470),
# aerosol 1.45, ozone 1.8, direct:diffuse 3.0:1, AgX -2.70) and told the sky owner to
# adopt it verbatim.  build_sky measured its sun against its own sky instead and shipped
# 115.754 at (1, .71632, .38712), aerosol 0.45, ozone 1.30, direct:diffuse 2.072, AgX
# -3.048.  The level is close by luck; the COLOUR and the KEY:FILL RATIO are not —
# shadows are 45 % brighter relative to key than these albedos were tuned against, and
# markedly bluer (sky tint (0.3115, 0.5582, 1.0000)).
#
# So every base colour below is now a real visible-band reflectance, and the check is
# arithmetic rather than taste:
#
#   C.lambert_radiance(a) = a/pi * (E_DIRECT_HORIZONTAL + SKY_IRRADIANCE)
#                         = a/pi * (29.224, 25.482, 23.249)
#   C.lambert_radiance(0.18) = (1.674, 1.460, 1.332), mean 1.4888 = AgX mid grey
#
# GRASS mean albedo 0.051 therefore renders 1.55 stops under mid grey, which is where
# a dense green sward belongs; DRY_GRASS 0.127 lands 0.5 stops under; SCREE 0.216 lands
# just above.  `probe_albedo()` measures the built material and prints the ratio.

GA_GRN   = (0.042, 0.082, 0.028)   # dense green pasture, mean 0.051
GA_GRN2  = (0.062, 0.098, 0.036)   # lighter/greyer sward
GA_DRYG  = (0.170, 0.150, 0.062)   # hay, standing dead grass, mean 0.127
GA_SOIL  = (0.058, 0.043, 0.030)   # damp turned soil
GA_DUST  = (0.122, 0.100, 0.071)   # dry dust and clay, mean 0.098
GA_STONE = (0.228, 0.222, 0.202)   # limestone / flint scree, mean 0.217
GA_STONE2 = (0.128, 0.118, 0.104)  # the dirtier, lichened half of the same scree
GA_MOSS  = (0.026, 0.050, 0.020)
GA_RUBBER = (0.046, 0.041, 0.038)  # ground a car has run over: rubber and soil
GA_HEDGEROOT = (0.026, 0.030, 0.016)
GA_WETSOIL = (0.030, 0.024, 0.020)


def mat_ground():
    t = NT(PFX + "Ground")
    geo = t.n("ShaderNodeNewGeometry")
    co = t.n("ShaderNodeTexCoord")

    a_wet = t.attr("ter_wet"); a_wear = t.attr("ter_wear"); a_cov = t.attr("ter_cover")
    a_mown = t.attr("ter_mown"); a_hedge = t.attr("ter_hedge"); a_dry = t.attr("ter_dry")
    a_fld = t.attr("ter_field"); a_dist = t.attr("ter_dist")
    a_rock = t.attr("ter_rock"); a_moss = t.attr("ter_moss"); a_scuff = t.attr("ter_scuff")
    a_crop = t.attr("ter_crop")

    # slope from the true shading normal: steep ground shows soil and scree
    sep = t.n("ShaderNodeSeparateXYZ")
    t.link(geo, "Normal", sep, 0)
    slope = t.ramp((sep, 2), [(0.62, (1, 1, 1)), (0.94, (0, 0, 0))])

    # ---- THE OCTAVE LADDER ------------------------------------------------ R2-1661
    #
    # It used to be five noises at 3 cm, 13 cm, 38 cm, 7.7 m and 62 m, and the last of
    # those only tinted GA_GRN against GA_GRN2 -- a +-20 % swing on a term that then
    # had 55 % of a flat per-field colour mixed OVER it.  So between 40 cm and 8 m
    # there was nothing, between 8 m and 62 m there was nothing, and the only strong
    # signal anywhere in the 10-200 m band was the field partition itself.  That is
    # the arithmetic behind "patches": at 99 m up on a 22 mm lens the 10-200 m band IS
    # the picture, and the only thing in it was a three-value colour map.  Two octaves
    # are added to fill it, and neither of them knows where a field boundary is.
    #
    # AND THE DETAIL IS SIZED, NOT TYPED.  `n_grain` at 3 cm carried `detail = 10`,
    # which emits down to 0.029 mm against a 1.32 mm floor at the closest the lens
    # ever gets to this surface (2.4 m, 34 mm, 4K) -- six octaves nobody can sample,
    # on the shader that covers every square metre of ground in the film.  `detail_for`
    # states the floor instead of assuming it.  The two new mid-scale noises are
    # floored deliberately COARSE: their job is the 10-200 m band and everything below
    # a third of a metre is already carried by the three fine noises above them, so
    # buying octaves down to a centimetre out there would be paying twice.
    d_fine = dict(distance_m=2.4, lens_mm=34.0)          # the verge fly-by, 4K
    n_grain = t.noise(34.0, K.detail_for(0.030, **d_fine), 0.68,
                      vec=(co, "Object"), dist=0.25)
    n_clod = t.noise(7.5, K.detail_for(0.133, **d_fine), 0.62,
                     vec=(co, "Object"), dist=0.55)
    n_fine = t.noise(2.6, K.detail_for(0.385, **d_fine), 0.62,
                     vec=(co, "Object"), dist=0.4)
    n_mid = t.noise(0.13, K.detail_for(7.7, floor_mm=120.0), 0.58, vec=(co, "Object"))
    n_m2 = t.noise(0.045, K.detail_for(22.0, floor_mm=340.0), 0.55,
                   vec=(co, "Object"), dist=0.30)
    n_big = t.noise(0.016, K.detail_for(62.0, floor_mm=1400.0), 0.55, vec=(co, "Object"))
    n_m4 = t.noise(0.0072, K.detail_for(139.0, floor_mm=4000.0), 0.50, vec=(co, "Object"))

    # stones: a voronoi cell field, so a scree slope is made of individual stones
    # rather than of brown noise
    vor = t.n("ShaderNodeTexVoronoi", feature="F1")
    t.link(co, "Object", vor, 0)
    t.set(vor, "Scale", 5.5); t.set(vor, "Randomness", 1.0)
    vore = t.n("ShaderNodeTexVoronoi", feature="DISTANCE_TO_EDGE")
    t.link(co, "Object", vore, 0)
    t.set(vore, "Scale", 5.5); t.set(vore, "Randomness", 1.0)
    stone_id = t.ramp((vor, 1), [(0.0, (0, 0, 0)), (1.0, (1, 1, 1))])
    stone_col = t.mix((stone_id, 0), GA_STONE2, GA_STONE)
    # only the bigger cells read as stones; the rest is the grit between them
    stone_mask = t.ramp((vore, 0), [(0.02, (0, 0, 0)), (0.09, (1, 1, 1))])

    # ---- THE CROP GRAIN --------------------------------------------------- R2-1661
    #
    # `ter_crop` carries, per vertex, the field's own row direction packed as
    # (cos/2 + 1/2, sin/2 + 1/2) and its headland band in z.  Rotating the object
    # coordinates into that frame here -- rather than baking the pattern into a vertex
    # attribute -- is not a preference: the ground grid is 2.5 m and a sprayer
    # wheeling is 1.7 m wide, so the pattern is finer than the mesh that would have to
    # carry it.
    #
    # WHAT THIS IS FOR.  Reducing the step between fields (in `ground_attributes`)
    # stops the boundaries reading as blotches, but on its own it leaves 155 m of
    # smooth colour on either side of every hedge, and smooth is the other half of the
    # complaint.  Real farmland from 100 m up is not smooth: it carries the marks of
    # being WORKED -- cutting swathes at ~5 m, tramlines every 21 m, and a headland
    # round the margin driven across the rows.  Those are the features that say
    # "agriculture" at exactly the 2-20 m scale this beat resolves at (9.2 cm per
    # pixel at f2811's axis, 2.5 cm at f2978's), and they cost shader maths and no
    # geometry at all.
    cxy = t.n("ShaderNodeSeparateXYZ")
    t.link(co, "Object", cxy, 0)
    crop = t.n("ShaderNodeSeparateXYZ")
    t.link(a_crop, 1, crop, 0)
    # unpack k * (cos, sin) from the 0..1 channels: (v - 0.5) / 0.35
    ccos = t.math("MULTIPLY_ADD", (crop, 0), 2.857143)
    t.set(ccos, 2, -1.428571)
    csin = t.math("MULTIPLY_ADD", (crop, 1), 2.857143)
    t.set(csin, 2, -1.428571)
    rowu = t.math("ADD", (t.math("MULTIPLY", (cxy, 0), (ccos, 0)), 0),
                  (t.math("MULTIPLY", (cxy, 1), (csin, 0)), 0))
    rowv = t.math("SUBTRACT", (t.math("MULTIPLY", (cxy, 1), (ccos, 0)), 0),
                  (t.math("MULTIPLY", (cxy, 0), (csin, 0)), 0))
    # the headland is worked ACROSS the rows, so the two axes swap in that band
    dvu = t.math("SUBTRACT", (rowv, 0), (rowu, 0))
    swu = t.math("MULTIPLY_ADD", (dvu, 0), (crop, 2))      # rowu + head * (rowv - rowu)
    t.link(rowu, 0, swu, 2)
    # CUTTING SWATHES, 5.2 m.  A mown or cut field carries the lay of the last pass.
    sw = t.math("SINE", (t.math("MULTIPLY", (swu, 0), 1.2083), 0))     # 2pi / 5.2
    # AMPLITUDE BY HOW ARABLE THE FIELD IS.  Permanent pasture does not carry cutting
    # swathes; hay and stubble do, and they are the `ter_dry` end of the palette.  A
    # uniform amplitude over every field in the world reads as corduroy laid on the
    # landscape rather than as a crop that was cut.
    swamp = t.math("MULTIPLY_ADD", (a_dry, 2), 0.054)
    t.set(swamp, 2, 0.018)                                 # 1.8 % pasture, 7.2 % hay
    swt = t.math("MULTIPLY_ADD", (sw, 0), (swamp, 0))
    t.set(swt, 2, 1.0)
    # TRAMLINES, 21 m apart and 1.7 m wide, and only on the arable end of the palette
    # (`ter_dry`) and only outside the headland, because that is where a sprayer
    # actually leaves them.
    trq = t.math("FRACT", (t.math("MULTIPLY", (rowv, 0), 0.047619), 0))    # 1 / 21
    trd = t.math("ABSOLUTE", (t.math("SUBTRACT", (trq, 0), 0.5), 0))
    tram = t.ramp((trd, 0), [(0.0405, (1, 1, 1)), (0.0570, (0, 0, 0))])
    trm = t.math("MULTIPLY", (tram, 0), (a_dry, 2))
    trm = t.math("MULTIPLY", (trm, 0),
                 (t.math("SUBTRACT", 1.0, (crop, 2)), 0))

    # pasture colour: field crop tint, modulated by the big noise
    past = t.mix((n_big, 0), GA_GRN, GA_GRN2)
    past2 = t.mix((a_dry, 2), (past, 2), GA_DRYG)
    # 0.42, not 0.55.  The flat per-field colour is still the dominant term out in the
    # fields -- it should be, a field IS a colour -- but it no longer overwhelms the
    # procedural pasture underneath it, which is the only part of this that varies
    # continuously.
    fld = t.mix(0.42, (past2, 2), (a_fld, 0))
    # THE MISSING BAND: 22 m and 139 m, multiplicative, crossing every hedge.
    tone2 = t.n("ShaderNodeMapRange")
    t.link(n_m2, 0, tone2, 0)
    t.set(tone2, "To Min", 0.855); t.set(tone2, "To Max", 1.145)
    tone4 = t.n("ShaderNodeMapRange")
    t.link(n_m4, 0, tone4, 0)
    t.set(tone4, "To Min", 0.830); t.set(tone4, "To Max", 1.170)
    fld2 = t.mix(1.0, (fld, 2), (tone2, 0), blend="MULTIPLY")
    fld3 = t.mix(1.0, (fld2, 2), (tone4, 0), blend="MULTIPLY")
    fld4 = t.mix(1.0, (fld3, 2), (swt, 0), blend="MULTIPLY")
    # far fields take their crop colour, near verges stay mown green
    turf = t.mix((a_mown, 2), (fld4, 2), (past, 2))
    # the wheelings themselves: bruised crop over bared soil
    turf = t.mix((t.math("MULTIPLY", (trm, 0), 0.62), 0), (turf, 2), GA_DUST)
    # a fine green/straw mottle at blade scale, so mown turf is not flat
    turf2 = t.mix((t.math("MULTIPLY", (n_grain, 0), 0.22), 0), (turf, 2), GA_DRYG)

    # soil / wear
    wearn = t.math("MULTIPLY", (a_wear, 2), None)
    t.link(t.ramp((n_mid, 0), [(0.25, (0.35, 0.35, 0.35)), (0.75, (1, 1, 1))]), 0, wearn, 1)
    soil0 = t.mix((n_fine, 0), GA_SOIL, GA_DUST)
    soil = t.mix((t.math("MULTIPLY", (n_clod, 0), 0.55), 0), (soil0, 2), GA_DUST)
    ground = t.mix((wearn, 0), (turf2, 2), (soil, 2))
    # thin cover shows soil through the sward
    thin = t.math("SUBTRACT", 1.0, (a_cov, 2))
    thin2 = t.math("MULTIPLY", (thin, 0), 0.65)
    ground2 = t.mix((thin2, 0), (ground, 2), (soil, 2))
    # STONE: scree and field stone, masked by the voronoi so it is stones, not tint
    rockm = t.math("MULTIPLY", (a_rock, 2), (stone_mask, 0))
    ground3 = t.mix((rockm, 0), (ground2, 2), (stone_col, 2))
    # steep ground: exposed subsoil under the stones
    ground3b = t.mix((t.math("MULTIPLY", (slope, 0), 0.7), 0), (ground3, 2),
                     (0.152, 0.132, 0.108))
    # WHERE CARS RUN WIDE: rubber and dragged soil, dark and desaturated
    ground3c = t.mix((t.math("MULTIPLY", (a_scuff, 2), 0.80), 0), (ground3b, 2), GA_RUBBER)
    # moss in the damp shade
    ground3d = t.mix((a_moss, 2), (ground3c, 2), GA_MOSS)
    # hedge line darkening so the geometry hedges sit on a shadowed root strip
    ground4 = t.mix((a_hedge, 2), (ground3d, 2), GA_HEDGEROOT)
    # damp ground is darker and glossier
    ground5 = t.mix((a_wet, 2), (ground4, 2), GA_WETSOIL)

    bump0 = t.n("ShaderNodeBump")
    t.set(bump0, "Strength", 0.42); t.set(bump0, "Distance", 0.012)
    t.link(n_grain, 0, bump0, "Height")
    bumpS = t.n("ShaderNodeBump")          # the stones stand proud of the grit
    t.set(bumpS, "Distance", 0.055)
    t.link(t.math("MULTIPLY", (rockm, 0), 1.15), 0, bumpS, "Strength")
    t.link(vore, 0, bumpS, "Height"); t.link(bump0, 0, bumpS, "Normal")
    bump1 = t.n("ShaderNodeBump")
    t.set(bump1, "Strength", 0.55); t.set(bump1, "Distance", 0.06)
    t.link(n_fine, 0, bump1, "Height"); t.link(bumpS, 0, bump1, "Normal")
    bump2 = t.n("ShaderNodeBump")
    t.set(bump2, "Strength", 0.40); t.set(bump2, "Distance", 0.5)
    t.link(n_mid, 0, bump2, "Height"); t.link(bump1, 0, bump2, "Normal")

    rgh = t.n("ShaderNodeMapRange")
    t.link(a_wet, 2, rgh, 0)
    t.set(rgh, "To Min", 0.94); t.set(rgh, "To Max", 0.62)
    # stone is smoother than soil and takes a low-sun sheen
    rgh2 = t.mix((rockm, 0), (rgh, 0), (0.46, 0.46, 0.46))

    p = t.n("ShaderNodeBsdfPrincipled")
    t.link(ground5, 2, p, "Base Color")
    t.link(bump2, 0, p, "Normal")
    t.link(rgh2, 2, p, "Roughness")
    t.set(p, "Specular IOR Level", 0.20)
    t.out(p)
    return t.m


# --- weeds and stones -----------------------------------------------------------------
WEED_MAT = {   # leaf colour, stem colour, flower colour, leaf translucency
    "dock":     ((0.048, 0.078, 0.026), (0.062, 0.048, 0.024), (0.140, 0.042, 0.020), 0.36),
    "thistle":  ((0.055, 0.072, 0.038), (0.058, 0.062, 0.036), (0.115, 0.048, 0.150), 0.30),
    "ragwort":  ((0.040, 0.070, 0.024), (0.052, 0.060, 0.028), (0.470, 0.330, 0.030), 0.34),
    "plantain": ((0.046, 0.082, 0.028), (0.056, 0.064, 0.030), (0.075, 0.062, 0.032), 0.38),
    "yarrow":   ((0.036, 0.062, 0.026), (0.048, 0.056, 0.028), (0.420, 0.400, 0.360), 0.32),
    "nettle":   ((0.034, 0.066, 0.022), (0.044, 0.058, 0.026), (0.070, 0.090, 0.036), 0.40),
}


def _leafy(name, col, trans, rough=0.40, spec=0.35):
    """A leaf-like Principled + translucent mix with per-instance value jitter."""
    t = NT(name)
    oi = t.n("ShaderNodeObjectInfo")
    pg = t.attr("pgrad"); pid = t.attr("pid")
    tip = tuple(min(1.0, c * 1.55 + 0.006) for c in col)
    base = t.mix((pg, 2), col, tip)
    hs = t.n("ShaderNodeHueSaturation")
    t.link(base, 2, hs, "Color")
    vv = t.n("ShaderNodeMapRange")
    t.link(oi, "Random", vv, 0)
    t.set(vv, "To Min", 0.66); t.set(vv, "To Max", 1.38)
    t.link(vv, 0, hs, "Value")
    hh = t.n("ShaderNodeMapRange")
    t.link(pid, 2, hh, 0)
    t.set(hh, "To Min", 0.470); t.set(hh, "To Max", 0.532)
    t.link(hh, 0, hs, "Hue")
    p = t.n("ShaderNodeBsdfPrincipled")
    t.link(hs, 0, p, "Base Color")
    t.set(p, "Roughness", rough); t.set(p, "Specular IOR Level", spec)
    tr = t.n("ShaderNodeBsdfTranslucent")
    t.link(hs, 0, tr, "Color")
    sh = t.n("ShaderNodeMixShader")
    sh.inputs[0].default_value = trans
    t.link(p, 0, sh, 1); t.link(tr, 0, sh, 2)
    t.out(sh)
    return t.m


def mat_weeds():
    for k, (leaf, stem, flow, tr) in WEED_MAT.items():
        _leafy(VPFX + "leaf_weed_" + k, leaf, tr, 0.42, 0.36)
        _leafy(VPFX + "weedstem_" + k, stem, 0.12, 0.52, 0.30)
        _leafy(VPFX + "flower_" + k, flow, 0.30, 0.34, 0.42)


def mat_stone():
    """Field stone / flint scree.  Albedo 0.13-0.24 against C.lambert_radiance."""
    t = NT(VPFX + "stone")
    oi = t.n("ShaderNodeObjectInfo")
    co = t.n("ShaderNodeTexCoord")
    n1 = t.noise(9.0, 10.0, 0.62, vec=(co, "Object"), dist=0.4)
    n2 = t.noise(46.0, 8.0, 0.70, vec=(co, "Object"))
    # two lithologies, chosen per stone, plus lichen in the shade of the grain
    base = t.mix((oi, "Random"), (0.235, 0.226, 0.204), (0.118, 0.106, 0.092))
    band = t.mix((n1, 0), (base, 2), (0.178, 0.166, 0.148))
    lich = t.mix((t.math("MULTIPLY", (n2, 0), 0.42), 0), (band, 2), (0.150, 0.160, 0.086))
    bump = t.n("ShaderNodeBump")
    t.set(bump, "Strength", 0.45); t.set(bump, "Distance", 0.012)
    t.link(n2, 0, bump, "Height")
    p = t.n("ShaderNodeBsdfPrincipled")
    t.link(lich, 2, p, "Base Color")
    t.link(bump, 0, p, "Normal")
    t.set(p, "Roughness", 0.62); t.set(p, "Specular IOR Level", 0.42)
    t.out(p)
    return t.m


def mat_grit_stone():
    """The grit fraction's stone: a DIRTY one.

    `mat_stone` is right for scree and field stone -- a freshly broken flint really is
    0.22 and it belongs on a scree slope.  Dropped into the sward 5 m from the lens at
    2.1 stops above turf, the same material reads as golf balls: measured on the first
    doppler crop, the 35-95 mm pieces came back at (196, 190, 176) against grass at
    (74, 78, 46).  A stone that has been lying in a verge is not a fresh fracture: it
    is the dark lithology with soil washed into its crevices, which is 1.0-1.3 stops
    above the ground rather than 2.1, and it still reads because what makes it read is
    the shadow it throws, not its value.
    """
    t = NT(VPFX + "gritstone")
    oi = t.n("ShaderNodeObjectInfo")
    co = t.n("ShaderNodeTexCoord")
    n1 = t.noise(14.0, 8.0, 0.60, vec=(co, "Object"), dist=0.35)
    n2 = t.noise(64.0, 6.0, 0.68, vec=(co, "Object"))
    base = t.mix((oi, "Random"), (0.128, 0.118, 0.104), (0.086, 0.078, 0.066))
    band = t.mix((n1, 0), (base, 2), (0.104, 0.094, 0.080))
    # soil washed into the crevices: the ground's own dust colour, driven by the fine
    # field so it lands in the hollows the bump is already making
    soil = t.mix((t.math("MULTIPLY", (n2, 0), 0.55), 0), (band, 2), GA_SOIL)
    bump = t.n("ShaderNodeBump")
    t.set(bump, "Strength", 0.52); t.set(bump, "Distance", 0.008)
    t.link(n2, 0, bump, "Height")
    p = t.n("ShaderNodeBsdfPrincipled")
    t.link(soil, 2, p, "Base Color")
    t.link(bump, 0, p, "Normal")
    t.set(p, "Roughness", 0.74); t.set(p, "Specular IOR Level", 0.26)
    t.out(p)
    return t.m


def mat_clod():
    """A dried clod of the ground itself: the soil, not a rock.

    Its albedo is deliberately the SAME pair the ground shader uses for dust and damp
    turned soil (GA_DUST 0.098 / GA_SOIL 0.044), because a clod that reads as a
    different material from the ground it broke off is worse than no clod at all.  What
    makes it visible is not colour, it is that it has a silhouette and throws a shadow
    across its neighbour at a 12.47 deg sun.
    """
    t = NT(VPFX + "clod")
    oi = t.n("ShaderNodeObjectInfo")
    co = t.n("ShaderNodeTexCoord")
    n1 = t.noise(22.0, 6.0, 0.58, vec=(co, "Object"))
    n2 = t.noise(120.0, 4.0, 0.66, vec=(co, "Object"))
    base = t.mix((oi, "Random"), GA_DUST, GA_SOIL)
    col = t.mix((t.math("MULTIPLY", (n1, 0), 0.55), 0), (base, 2),
                tuple(c * 1.35 for c in GA_DUST))
    bump = t.n("ShaderNodeBump")
    t.set(bump, "Strength", 0.62); t.set(bump, "Distance", 0.006)
    t.link(n2, 0, bump, "Height")
    p = t.n("ShaderNodeBsdfPrincipled")
    t.link(col, 2, p, "Base Color")
    t.link(bump, 0, p, "Normal")
    t.set(p, "Roughness", 0.88); t.set(p, "Specular IOR Level", 0.16)
    t.out(p)
    return t.m


def build_materials():
    for k in BARK:
        mat_bark(k)
    for k in LEAF:
        mat_leaf(k)
        mat_canopy(k)
    for k in GRASS:
        mat_grass(k)
    mat_weeds()
    mat_stone()
    mat_grit_stone()
    mat_clod()
    mat_ground()


# ==================================================================================
# 8.  WHERE THINGS GROW
# ==================================================================================

class GridZ:
    """Bilinear lookup of the built ground surface, so plants sit ON the mesh."""

    def __init__(self, xs, ys, Z):
        self.xs = xs; self.ys = ys; self.Z = Z

    def __call__(self, x, y, want_slope=False):
        i = np.clip(np.searchsorted(self.xs, x) - 1, 0, len(self.xs) - 2)
        j = np.clip(np.searchsorted(self.ys, y) - 1, 0, len(self.ys) - 2)
        x0 = self.xs[i]; x1 = self.xs[i + 1]; y0 = self.ys[j]; y1 = self.ys[j + 1]
        tx = np.clip((x - x0) / (x1 - x0), 0, 1); ty = np.clip((y - y0) / (y1 - y0), 0, 1)
        z00 = self.Z[i, j]; z10 = self.Z[i + 1, j]; z01 = self.Z[i, j + 1]; z11 = self.Z[i + 1, j + 1]
        z = (z00 * (1 - tx) + z10 * tx) * (1 - ty) + (z01 * (1 - tx) + z11 * tx) * ty
        if not want_slope:
            return z
        dzdx = ((z10 - z00) * (1 - ty) + (z11 - z01) * ty) / (x1 - x0)
        dzdy = ((z01 - z00) * (1 - tx) + (z11 - z10) * tx) / (y1 - y0)
        return z, np.hypot(dzdx, dzdy)


class CameraPath:
    """Everywhere the lens goes, for budgeting detail by distance-to-path.

    Beats 1-3 are inside the showroom, beat 4 crosses the apron, beat 5 is the lap
    (the camera is never more than ~30 m off the centreline), beat 6 is the crane-out.

    TWO METRICS, AND THE DIFFERENCE BETWEEN THEM IS THE WHOLE OF R2-1661.
    ----------------------------------------------------------------------
    `dist` is the HORIZONTAL distance to the nearest camera station.  It throws the
    z away, which costs nothing for beats 1-5 because the lens is 2-6 m above the
    ground it is looking at: a clump 47 m out horizontally is 47.4 m out in three
    dimensions and lands on the same side of every threshold.

    Beat 6 is the one place in the film where the camera LEAVES the ground.  It
    climbs to 140 m, and at that point a horizontal metric says the ground directly
    beneath the crane is zero metres from the lens.  So `dist` opens a phantom hero
    disc under the aerial -- 48 m of hero grass spent on ground 140 m away and mostly
    out of frame -- while the several hundred metres of infield the wide lens is
    actually pointed at score 200-600 m and fall to the far tier, which is a sparse
    scatter over flat colour.  That is what "we just zoom out so you see all the
    patches in the land" is: not a colour bug, a COVERING bug, and the covering rule
    was reading the wrong distance.

    `dist3` is the true three-dimensional distance to the nearest camera station and
    is the metric every ground-cover tier is now budgeted against.  `dist` is kept
    because the tree, shrub, weed and grit tiers are calibrated against it and are
    not in scope here -- changing one predicate is the fix; changing five is a
    different experiment.
    """

    def __init__(self, cir, beats):
        P = [np.stack([cir.X[::6], cir.Y[::6], cir.Z[::6] + 6.0], 1)]
        P.append(np.array([k["world"] for k in beats["beat6"]["keys"]]))
        P.append(np.array([[0, 0, 2.0], [15, 0, 2.5], [60, 0, 4.0],
                           [120, 8, 8.0], [200, 60, 14.0], [329.4, 169.8, 12.0]]))
        P.append(np.array(beats["doppler"]["camera_world"])[None, :])
        self.P = np.concatenate(P, 0)

    def dist(self, x, y, chunk=8000):
        out = np.empty(len(x))
        for a in range(0, len(x), chunk):
            b = min(len(x), a + chunk)
            dx = x[a:b, None] - self.P[None, :, 0]
            dy = y[a:b, None] - self.P[None, :, 1]
            out[a:b] = np.sqrt((dx * dx + dy * dy).min(axis=1))
        return out

    def dist3(self, x, y, z, chunk=8000):
        """True 3-D distance to the nearest camera station.  >= `dist`, always."""
        z = np.broadcast_to(np.asarray(z, float), np.shape(x))
        out = np.empty(len(x))
        for a in range(0, len(x), chunk):
            b = min(len(x), a + chunk)
            dx = x[a:b, None] - self.P[None, :, 0]
            dy = y[a:b, None] - self.P[None, :, 1]
            dz = z[a:b, None] - self.P[None, :, 2]
            out[a:b] = np.sqrt((dx * dx + dy * dy + dz * dz).min(axis=1))
        return out


class Raster:
    """A field evaluated once on a coarse lattice and sampled bilinearly thereafter.

    corridor_fz() and CameraPath.dist() are both O(candidates x samples); run directly
    on the million-candidate grass grid they cost minutes.  Both fields are smooth at
    14 m away from the medial axis, and the coarse decisions they feed are all several
    metres wide -- but the ONE decision that has to be exact, "is this point inside the
    road corridor", is re-tested exactly on the survivors (see `outside_corridor`)."""

    FIELDS = ("D", "f", "dcam", "dcam3")

    def __init__(self, gr, cam, x0, x1, y0, y1, step=14.0, gz=None):
        self.xs = np.arange(x0, x1 + step, step)
        self.ys = np.arange(y0, y1 + step, step)
        GX, GY = np.meshgrid(self.xs, self.ys, indexing="ij")
        fx, fy = GX.ravel(), GY.ravel()
        f, zrim, s, u, lim, Dc = corridor_fz(fx, fy)
        sh = (len(self.xs), len(self.ys))
        self.D = Dc.reshape(sh)
        self.f = np.minimum(f, 1e4).reshape(sh)     # metres OUTBOARD OF THE RIM
        self.dcam = cam.dist(fx, fy).reshape(sh)
        # `dcam3` needs a ground height, and the lattice is 46 k points, so it takes
        # the GridZ the build already made off the BUILT mesh when there is one and
        # falls back to Ground.height (another corridor_fz sweep) only for callers
        # that have no grid yet.
        gzv = gz(fx, fy) if gz is not None else gr.height(fx, fy)
        self.dcam3 = cam.dist3(fx, fy, gzv).reshape(sh)

    def sample(self, x, y):
        i = np.clip(((x - self.xs[0]) / (self.xs[1] - self.xs[0])).astype(int), 0, len(self.xs) - 2)
        j = np.clip(((y - self.ys[0]) / (self.ys[1] - self.ys[0])).astype(int), 0, len(self.ys) - 2)
        tx = np.clip((x - self.xs[i]) / (self.xs[1] - self.xs[0]), 0, 1)
        ty = np.clip((y - self.ys[j]) / (self.ys[1] - self.ys[0]), 0, 1)
        out = {}
        for k in self.FIELDS:
            A = getattr(self, k)
            out[k] = ((A[i, j] * (1 - tx) + A[i + 1, j] * tx) * (1 - ty)
                      + (A[i, j + 1] * (1 - tx) + A[i + 1, j + 1] * tx) * ty)
        return out


def outside_corridor(x, y, clear=0.0):
    """EXACT test: True where a plant of standoff `clear` may stand.

    The raster is a 14 m lattice and interpolating `f` across it is worth a metre near
    a tight rim.  Anything that must not end up inside the road programme's ground —
    every tree, every shrub, every stone — gets this test on its final position.
    """
    return corridor_field(np.asarray(x, float), np.asarray(y, float)) > clear


def habitat(gr, gz, cam, x, y, ras=None):
    """Everything the placement rules need, evaluated once per candidate.

    `f` is metres OUTBOARD OF THE CORRIDOR RIM; negative means the road programme owns
    that ground.  Every standoff rule is written against it rather than against
    distance-from-the-centreline, because "48 m from the centreline" is inside the
    pit lane at s = 0 (rim 12.1 m) and 40 m short of the barrier at T10 (rim 87.9 m),
    and the old rules used the same number at both.
    """
    if ras is None:
        f, zrim, s, u, lim, D = corridor_fz(x, y)
        dcam = cam.dist(x, y)
        dcam3 = cam.dist3(x, y, gz(x, y))
    else:
        r = ras.sample(x, y)
        D, f, dcam, dcam3 = r["D"], r["f"], r["dcam"], r["dcam3"]
        s = np.zeros_like(D); u = D
    z, slope = gz(x, y, want_slope=True)
    cx, cy = world_to_circuit(x, y)
    plateau = window(cx, -620.0, 300.0, 110.0) * window(cy, -120.0, 140.0, 85.0)
    built = np.maximum(window(cx, -490.0, 140.0, 26.0) * window(cy, -70.0, 120.0, 26.0),
                       window(x, -172.0, 172.0, 26.0) * window(y, -172.0, 172.0, 26.0))
    # ---- `paved`: WHERE THE ARCHITECTURE ACTUALLY IS ------------------  R2-1821
    #
    # `built` above is a DISTRICT drawn by hand: circuit x -490..140, y -70..120,
    # feathered 26 m, plus a 344 m box round the showroom.  16.50 ha.  The contract
    # declares the paving itself -- 6.66 ha -- and §11 says in terms that the two are
    # meant to be the same region "stated once so the extents cannot drift".
    #
    # THEY HAD DRIFTED, AND THE MEASUREMENT IS NOT CLOSE.  Sampled over the drawn box:
    # 31.9 % of it is actually paved, 20.7 % is inside the road corridor, and 47.7 %
    # -- 7.98 ha -- is OPEN GROUND THIS MODULE OWNS.  Worse, the whole SOUTHERN half,
    # circuit y -70..0, 4.83 ha, is 0.0 % paved: there is not one square metre of
    # architecture in it.  It is the field beside the pit building, and it is the
    # region the client described as "blank grass no detail nothing".
    #
    # WHAT THAT COSTS, MEASURED ON f2760's OWN FRUSTUM.  46.7 % of the ground in that
    # frame is inside the drawn box.  Ground-cover density inside it is 0.049 against
    # 0.472 outside -- a 9.7x step -- and because the box is a rectangle in circuit
    # space its feathered edge lays that step across open farmland as a STRAIGHT LINE
    # answering to nothing in the picture.  R2-1661 caught tiers that would have laid
    # density rings at 200 m and 520 m; this is the same artefact drawn by the mask
    # instead of by the tiers, and R2-1661's new sward layer inherited it verbatim.
    #
    # AND THIS MODULE ALREADY TREATS THE CONTRACT AS AUTHORITATIVE FOR THE SAME
    # QUESTION.  `cut_field` cuts the ground MESH against `C.platform_field` -- whose
    # outside-corridor area agrees with build_architecture's own reported `paving_m2`
    # to 0.3 % -- so terrain builds no ground on the declared platform at all.  It was
    # cutting its ground to the footprint and then refusing to PLANT on the district.
    # A plant standing where `platform_field > 0` therefore always has ground under it,
    # which is the property the old box could not offer and the reason this is the
    # right field rather than merely a smaller one.
    #
    # THE STANDOFF IS SIZED BY THE PLACEABLE UNIT, NOT CHOSEN.  A tier-A sward drift is
    # drawn over 1.45 x its 2.30 m pitch, so its half-extent is 1.67 m; 3.0 m of
    # standoff keeps every leaf of a full-weight drift off architecture's concrete
    # while leaving the grass meeting the pavement, which is where grass meets pavement
    # on a real circuit.  A hard edge AT a kerb is correct; the defect was a soft edge
    # 300 m away from one.
    #
    # SCOPE, and it is deliberately the same scope R2-1149 used for `dist3`: `paved`
    # drives the THREE GROUND-COVER TIERS -- the verge band, the meadow and the sward
    # drifts.  Trees, shrubs, ferns, weeds, grit and the park species mix still read
    # `built`, because a tree keep-out around a paddock genuinely IS a district and
    # those tiers are calibrated against this box.  Changing one predicate is a fix.
    paved = smoothstep(BUILT_STANDOFF_M, 0.0,
                       np.asarray(C.platform_field(x, y), float))
    ez = (window(cx, -340.0, 160.0, 90.0) * window(cy, 180.0, 420.0, 90.0))
    ez = np.maximum(ez, window(cx, -1010.0, -860.0, 80.0) * window(cy, 150.0, 560.0, 80.0))
    ez = np.maximum(ez, window(cx, -120.0, 260.0, 90.0) * window(cy, -340.0, -62.0, 90.0))
    fid, fdist = field_pattern(x, y)
    # woodland: patchy, correlated at ~165 m, denser on slopes and away from the road
    wood = smoothstep(-0.22, 0.34, fbm(x / 165.0, y / 165.0, 4, seed=401))
    wood *= smoothstep(52.0, 150.0, D)
    wood *= (1.0 - 0.88 * plateau) * (1.0 - 0.94 * built) * (1.0 - 0.80 * ez)
    wood = np.clip(wood * (0.70 + 0.90 * smoothstep(0.03, 0.22, slope)), 0, 1)
    return dict(s=s, u=u, D=D, f=f, z=z, slope=slope, plateau=plateau,
                built=built, paved=paved, ez=ez, dcam=dcam, dcam3=dcam3, wood=wood,
                fid=fid, fdist=fdist, cx=cx, cy=cy)


def jitter_grid(x0, x1, y0, y1, step, seed):
    nx = int((x1 - x0) / step); ny = int((y1 - y0) / step)
    ix, iy = np.meshgrid(np.arange(nx), np.arange(ny), indexing="ij")
    ix = ix.ravel(); iy = iy.ravel()
    return (x0 + (ix + hash01(ix, iy, seed)) * step,
            y0 + (iy + hash01(ix, iy, seed + 7717)) * step,
            hash01(ix, iy, seed + 31337))


# --- species mixes by habitat -------------------------------------------------------
TREE_ORDER = ["oak", "poplar", "pine", "birch", "plane", "cypress",
              "willow", "hawthorn", "rowan", "snag"]

MIX_BASE    = np.array([0.23, 0.03, 0.15, 0.20, 0.02, 0.005, 0.04, 0.15, 0.09, 0.075])
MIX_EXPOSED = np.array([0.08, 0.01, 0.40, 0.10, 0.00, 0.00, 0.00, 0.22, 0.10, 0.09])
MIX_DAMP    = np.array([0.10, 0.16, 0.02, 0.24, 0.02, 0.00, 0.28, 0.08, 0.06, 0.04])
MIX_STEEP   = np.array([0.20, 0.01, 0.30, 0.18, 0.00, 0.00, 0.01, 0.16, 0.07, 0.07])
MIX_PARK    = np.array([0.16, 0.22, 0.04, 0.10, 0.26, 0.14, 0.02, 0.02, 0.04, 0.00])
MIX_HEDGE   = np.array([0.14, 0.05, 0.02, 0.12, 0.02, 0.00, 0.05, 0.45, 0.12, 0.03])


def species_pick(h, rng, hedge=False):
    n = len(h["z"])
    expo = smoothstep(4.0, 9.5, h["z"]) * smoothstep(0.05, 0.25, h["slope"] + 0.05)
    damp = smoothstep(0.5, -3.4, h["z"])
    steep = smoothstep(0.10, 0.34, h["slope"])
    park = np.clip(h["plateau"] * 0.9 + h["built"] * 0.7, 0, 1)
    W = (MIX_BASE[None, :]
         + expo[:, None] * (MIX_EXPOSED - MIX_BASE)[None, :]
         + damp[:, None] * (MIX_DAMP - MIX_BASE)[None, :]
         + steep[:, None] * (MIX_STEEP - MIX_BASE)[None, :]
         + park[:, None] * (MIX_PARK - MIX_BASE)[None, :])
    if hedge:
        W = 0.25 * W + 0.75 * MIX_HEDGE[None, :]
    W = np.clip(W, 1e-4, None)
    W /= W.sum(1, keepdims=True)
    r = rng.random(n)[:, None]
    return (r > np.cumsum(W, 1)).sum(1).clip(0, len(TREE_ORDER) - 1)


# ==================================================================================
# 9.  LIBRARY AND INSTANCING
# ==================================================================================

def build_library(rng, counts):
    """Unique base meshes.  Instances then differ from one another by height, breadth,
    mirroring, lean, spin, colour, season and canopy density (build_terrain.md §4)."""
    lib = {}
    for key in TREE_ORDER + ["sapling"]:
        for lod in (0, 1, 2):
            ms = []
            for i in range(counts[lod]):
                me, h = gen_tree(key, np.random.default_rng(int(rng.integers(1 << 31))), lod)
                me.name = VPFX + "tree_%s_L%d_%02d" % (key, lod, i)
                ms.append((me, h))
            lib[(key, lod)] = ms
        log("  lib %-9s hero %6d polys x%d" % (key, len(lib[(key, 0)][0][0].polygons), counts[0]))
    for key in SHRUBS:
        for lod in (0, 1):
            ms = []
            for i in range(counts[3 + lod]):
                me, h = gen_shrub(key, np.random.default_rng(int(rng.integers(1 << 31))), lod)
                me.name = VPFX + "shrub_%s_L%d_%02d" % (key, lod, i)
                ms.append((me, h))
            lib[("shrub_" + key, lod)] = ms
    ferns = []
    for i in range(counts[5]):
        me, h = gen_fern(np.random.default_rng(int(rng.integers(1 << 31))))
        me.name = VPFX + "fern_%02d" % i
        ferns.append((me, h))
    lib[("fern", 0)] = ferns
    nw = max(3, counts[5])
    for key in WEED_ORDER:
        ws = []
        for i in range(nw):
            me, h = gen_weed(key, np.random.default_rng(int(rng.integers(1 << 31))))
            me.name = VPFX + "weed_%s_%02d" % (key, i)
            ws.append((me, h))
        lib[("weed_" + key, 0)] = ws
    for key in STONES:
        ss = []
        for i in range(max(6, counts[5] + 3)):
            me, h = gen_stone(key, np.random.default_rng(int(rng.integers(1 << 31))))
            me.name = VPFX + "stone_%s_%02d" % (key, i)
            ss.append((me, h))
        lib[("stone_" + key, 0)] = ss
    # the grit pass: the same generator, the ground's own materials, and a fatter
    # library because grit is the densest thing in the world and a repeated pebble at
    # 2 m is the exact failure the brief prohibits.
    for gkey, gmat in (("clod", VPFX + "clod"), ("gritstone", VPFX + "gritstone")):
        cs = []
        for i in range(max(14, counts[5] * 2)):
            me, h = gen_grit_piece(np.random.default_rng(int(rng.integers(1 << 31))),
                                   gmat)
            me.name = VPFX + "%s_%02d" % (gkey, i)
            cs.append((me, h))
        lib[(gkey, 0)] = cs
    return lib


def instance_plants(coll, lib, key, lod, P, rng, hrange=None, lean=1.0,
                    tag="T", mirror=True):
    """Linked-duplicate objects: one mesh, many genuinely different individuals."""
    ms = lib[(key, lod)]
    n = len(P)
    if n == 0:
        return 0
    pick = rng.integers(0, len(ms), n)
    hr = hrange or (SPECIES[key]["h"] if key in SPECIES else (1.0, 2.0))
    target = rng.uniform(hr[0], hr[1], n)
    wide = 1.0 + rng.normal(0, 0.085, n)
    spin = rng.random(n) * 2 * math.pi
    lx = rng.normal(0.0, 0.030, n) * lean + WIND_DIR[1] * 0.032 * lean
    ly = rng.normal(0.0, 0.030, n) * lean - WIND_DIR[0] * 0.032 * lean
    flip = rng.random(n) < 0.5
    for i in range(n):
        me, h0 = ms[pick[i]]
        ob = bpy.data.objects.new("%s%s_%06d" % (VPFX, tag, i), me)
        sc = float(target[i] / max(h0, 0.05))
        sxy = sc * float(wide[i])
        ob.location = (float(P[i, 0]), float(P[i, 1]), float(P[i, 2]))
        ob.scale = (-sxy if (mirror and flip[i]) else sxy, sxy, sc)
        ob.rotation_euler = (float(lx[i]), float(ly[i]), float(spin[i]))
        coll.objects.link(ob)
    return n


def _mesh_tris(me):
    c = np.empty(len(me.polygons), np.int32)
    me.polygons.foreach_get("loop_total", c)
    return int((c - 2).sum())


def gn_kind(name, meshes, P, target_h, rng, parent, lean=1.0, mirror=True,
            wide=0.14, xy=None):
    """Instance ONE kind of plant on a point cloud through Geometry Nodes.

    One collection per kind, and every library mesh in it normalised to unit height,
    so (a) which slot `Pick Instance` lands on is irrelevant to the scale maths and
    (b) the mapping cannot silently break if Collection Info's child order ever
    changes.  Kind selection is carried by having separate point clouds, not by
    trusting an index into a mixed collection.
    """
    n = len(P)
    if n == 0 or not meshes:
        return 0
    lib_coll = bpy.data.collections.new(VPFX + name + "_lib")   # not linked to scene
    for me, h0 in meshes:
        # normalise a COPY: the same library group may also be used by object-based
        # placement (the avenue's replacement saplings), and rescaling the shared mesh
        # in place would silently resize everything already placed from it.
        m2 = me.copy()
        m2.name = me.name + "_u"
        if h0 > 1e-4:
            V = np.empty(len(m2.vertices) * 3, np.float32)
            m2.vertices.foreach_get("co", V)
            m2.vertices.foreach_set("co", (V.reshape(-1, 3) / h0).ravel())
            m2.update()
        lib_coll.objects.link(bpy.data.objects.new(m2.name, m2))

    sc = np.asarray(target_h, float)
    if sc.ndim == 0:
        sc = np.full(n, float(sc))
    # `xy` widens the footprint INDEPENDENTLY of height.  Mown verge turf is short and
    # broad; scaling a unit-height clump uniformly makes it short and NARROW, and 15
    # tufts per m2 of 0.12 m-wide clump is 11 % ground cover -- bare soil with sprigs
    # on it, which is exactly the thing the brief prohibits.
    ex = np.ones(n) if xy is None else np.broadcast_to(np.asarray(xy, float), (n,))
    w = 1.0 + rng.normal(0, wide, n)
    sx = sc * w * ex
    if mirror:
        sx = np.where(rng.random(n) < 0.5, -sx, sx)
    scl = np.stack([sx, sc * (1.0 + rng.normal(0, wide, n)) * ex, sc], 1)
    rot = np.stack([rng.normal(0, 0.030, n) * lean + WIND_DIR[1] * 0.030 * lean,
                    rng.normal(0, 0.030, n) * lean - WIND_DIR[0] * 0.030 * lean,
                    rng.random(n) * 2 * math.pi], 1)
    idx = rng.integers(0, len(meshes), n)

    me = new_mesh_arrays(VPFX + name, P, None, None)
    for nm, data in (("inst_rot", rot), ("inst_scl", scl)):
        a = me.attributes.new(nm, "FLOAT_VECTOR", "POINT")
        a.data.foreach_set("vector", np.asarray(data, np.float32).ravel())
    a = me.attributes.new("inst_idx", "INT", "POINT")
    a.data.foreach_set("value", np.asarray(idx, np.int32))
    ob = bpy.data.objects.new(VPFX + name, me)
    parent.objects.link(ob)

    ng = bpy.data.node_groups.new(VPFX + "gn_" + name, "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N = ng.nodes
    gi = N.new("NodeGroupInput"); gi.location = (-700, 0)
    go = N.new("NodeGroupOutput"); go.location = (400, 0)
    iop = N.new("GeometryNodeInstanceOnPoints"); iop.location = (100, 0)
    ci = N.new("GeometryNodeCollectionInfo"); ci.location = (-300, -260)
    ci.inputs[0].default_value = lib_coll
    ci.inputs[1].default_value = True      # separate children
    ci.inputs[2].default_value = True      # reset children
    L = ng.links
    L.new(gi.outputs[0], iop.inputs["Points"])
    L.new(ci.outputs[0], iop.inputs["Instance"])
    iop.inputs["Pick Instance"].default_value = True
    for k, (sock, nm, dt) in enumerate((("Instance Index", "inst_idx", "INT"),
                                        ("Rotation", "inst_rot", "FLOAT_VECTOR"),
                                        ("Scale", "inst_scl", "FLOAT_VECTOR"))):
        na = N.new("GeometryNodeInputNamedAttribute")
        na.data_type = dt
        na.inputs[0].default_value = nm
        na.location = (-460, 220 - 150 * k)
        L.new(na.outputs[0], iop.inputs[sock])
    L.new(iop.outputs[0], go.inputs[0])
    m = ob.modifiers.new(VPFX + "gn", "NODES")
    m.node_group = ng
    return n


# ==================================================================================
# 10.  BUILD
# ==================================================================================

def _sub(root, name):
    c = bpy.data.collections.new(COLL + "/" + name)
    root.children.link(c)
    return c


def build(quality=None):
    q = QUAL if quality is None else quality
    t0 = time.time()
    purge()
    spec = json.load(open(SPEC_JSON))
    beats = json.load(open(BEAT_JSON))
    cir = Circuit(spec)
    gr = Ground(cir)
    rng = np.random.default_rng(SEED)

    root = bpy.data.collections.new(COLL)
    bpy.context.scene.collection.children.link(root)
    c_ground = _sub(root, "Ground")
    c_trees = _sub(root, "Trees")
    c_shrub = _sub(root, "Undergrowth")
    c_grass = _sub(root, "Grass")
    c_weeds = _sub(root, "WeedsStones")

    log("materials")
    build_materials()

    log("ground")
    gob, attrs, (gxs, gys, gZ) = build_ground(gr, c_ground)
    gz = GridZ(gxs, gys, gZ)
    cam = CameraPath(cir, beats)

    # ---- library ----------------------------------------------------------------
    # (treeL0, treeL1, treeL2, shrubL0, shrubL1, fern) unique base meshes PER SPECIES.
    # These are the numbers the red line is really about: 1500 hero trees drawn from 5
    # oaks is 27 uses of each mesh, and mirroring only halves that.  8 per species x 11
    # species = 88 hero trees, so no L0 mesh is used more than ~17 times anywhere in the
    # world and never twice within sight of each other (placement is habitat-driven, and
    # the picks are independent).  The cost is base geometry, which is shared: 8 x 11 x
    # ~207 k = 18 M triangles resident once, not per instance.
    nlod = [max(2, int(round(v * (0.45 + 0.55 * q)))) for v in (8, 12, 16, 7, 7, 9)]
    log("library (unique base meshes per species: L0 x%d, L1 x%d, L2 x%d)"
        % (nlod[0], nlod[1], nlod[2]))
    lib = build_library(rng, nlod)

    # ---- candidate field ---------------------------------------------------------
    log("scatter: rasterising track and camera-path fields")
    X0, X1, Y0, Y1 = -1520.0, 1440.0, -1120.0, 1840.0
    ras = Raster(gr, cam, X0 - 40, X1 + 40, Y0 - 40, Y1 + 40, 14.0, gz=gz)
    cx_, cy_, cr_ = jitter_grid(X0, X1, Y0, Y1, 5.6, 991)
    keepc = ras.sample(cx_, cy_)["D"] < 1150.0
    cx_, cy_, cr_ = cx_[keepc], cy_[keepc], cr_[keepc]
    h = habitat(gr, gz, cam, cx_, cy_, ras)
    log("  %d candidates" % len(cx_))

    stats = {}

    # -- WOODLAND ------------------------------------------------------------------
    # Standoff is measured OUTBOARD OF THE CORRIDOR RIM, which is where the ground
    # this module owns actually starts.  12 m of it puts the nearest trunk ~18 m
    # behind the barrier face and clear of the debris fence.
    can = (h["f"] > 12.0) & (h["D"] > 26.0) & (h["built"] < 0.30) & (h["ez"] < 0.42)
    pw = h["wood"] * 0.44 * q
    take = can & (cr_ < pw)
    idx = np.where(take)[0]
    idx = idx[outside_corridor(cx_[idx], cy_[idx], 8.0)]
    log("  woodland trees: %d" % len(idx))
    hh = {k: v[idx] for k, v in h.items()}
    sp = species_pick(hh, rng)
    lod = np.where(hh["dcam"] < 95.0, 0, np.where(hh["dcam"] < 380.0, 1, 2))
    Z = gz(cx_[idx], cy_[idx]) - 0.05
    P = np.stack([cx_[idx], cy_[idx], Z], 1)
    n_tree = 0
    for si, key in enumerate(TREE_ORDER):
        for l in (0, 1, 2):
            m = (sp == si) & (lod == l)
            if not m.any():
                continue
            # exposed ground -> shorter, more strongly wind-flagged specimens
            ex = smoothstep(4.0, 9.5, hh["z"][m]).mean()
            n_tree += instance_plants(
                c_trees, lib, key, l, P[m], rng,
                hrange=(SPECIES[key]["h"][0] * (1.0 - 0.22 * ex),
                        SPECIES[key]["h"][1] * (1.0 - 0.26 * ex)),
                lean=1.0 + 1.6 * ex, tag="tree_%s%d" % (key, l))
    stats["woodland_trees"] = n_tree

    # -- HEDGEROWS on the field boundaries ------------------------------------------
    # The ground shader's crop colour and these hedges come from the SAME Voronoi
    # partition, so the hedge always sits exactly on the boundary it is shading.
    hedge_ok = (h["fdist"] < 4.2) & (h["f"] > 26.0) & (h["wood"] < 0.42) & \
               (h["built"] < 0.25) & (h["ez"] < 0.5)
    hi = np.where(hedge_ok & (cr_ < 0.30 * q))[0]
    hi = hi[outside_corridor(cx_[hi], cy_[hi], 18.0)]
    hh2 = {k: v[hi] for k, v in h.items()}
    spH = species_pick(hh2, rng, hedge=True)
    lodH = np.where(hh2["dcam"] < 95.0, 0, np.where(hh2["dcam"] < 380.0, 1, 2))
    PH = np.stack([cx_[hi], cy_[hi], gz(cx_[hi], cy_[hi]) - 0.05], 1)
    n_h = 0
    for si, key in enumerate(TREE_ORDER):
        for l in (0, 1, 2):
            m = (spH == si) & (lodH == l)
            if m.any():
                n_h += instance_plants(c_trees, lib, key, l, PH[m], rng,
                                       hrange=(SPECIES[key]["h"][0] * 0.55,
                                               SPECIES[key]["h"][1] * 0.85),
                                       lean=1.5, tag="hedge_%s%d" % (key, l))
    stats["hedgerow_trees"] = n_h

    # -- PADDOCK AVENUE: a planted row, maintained, with two gaps and a replacement --
    av = []
    for t in np.arange(0.0, 1.0001, 1.0 / 26):
        ax, ay = circuit_to_world(-470.0 + t * 560.0, 118.0)
        av.append((ax, ay))
    av = np.array(av)
    keep = np.ones(len(av), bool)
    keep[[7, 8, 19]] = False                      # two lost trees, never replanted
    avP = np.stack([av[keep, 0], av[keep, 1], gz(av[keep, 0], av[keep, 1]) - 0.05], 1)
    jit = rng.normal(0, 0.9, (len(avP), 2))
    avP[:, :2] += jit
    # L0, and a wide height range: a planted avenue IS uniform, but 20 identical
    # lollipops in a line is the exact thing the brief prohibits, and a real avenue is
    # uniform in SPACING and species, not in size -- trees planted the same year still
    # differ by 30 % in height depending on what is under them.
    stats["avenue"] = instance_plants(c_trees, lib, "plane", 0, avP[:-2], rng,
                                      hrange=(11.8, 19.6), lean=0.4, tag="avenue")
    stats["avenue"] += instance_plants(c_trees, lib, "sapling", 0, avP[-2:], rng,
                                       hrange=(3.4, 4.1), lean=0.5, tag="avenue_new")

    # -- UNDERGROWTH: shrub layer, thickest at the woodland edge --------------------
    ux, uy, ur = jitter_grid(X0, X1, Y0, Y1, 3.4, 613)
    ku = ras.sample(ux, uy)["D"] < 620.0
    ux, uy, ur = ux[ku], uy[ku], ur[ku]
    hu = habitat(gr, gz, cam, ux, uy, ras)
    edge = np.exp(-((hu["wood"] - 0.34) / 0.22) ** 2)          # the boundary band
    inner = smoothstep(0.45, 0.85, hu["wood"]) * 0.45
    ps = (0.26 * edge + 0.42 * inner) * q
    ok = (hu["f"] > 5.0) & (hu["built"] < 0.3) & (hu["ez"] < 0.6)
    si = np.where(ok & (ur < ps))[0]
    si = si[outside_corridor(ux[si], uy[si], 3.0)]
    log("  shrubs: %d" % len(si))
    SH = list(SHRUBS.keys())
    # shrub species by habitat: gorse and juniper on the dry exposed ground, hazel and
    # bramble in the damp shade, broom on the disturbed margins
    zz = hu["z"][si]; sl = hu["slope"][si]
    wS = np.stack([
        0.30 + 0.25 * smoothstep(1.0, -3.0, zz),                       # bramble
        0.12 + 0.42 * smoothstep(3.0, 9.0, zz),                        # gorse
        0.22 + 0.28 * smoothstep(2.0, -3.0, zz),                       # hazel
        0.16 + 0.20 * smoothstep(0.05, 0.25, sl),                      # broom
        0.10 + 0.34 * smoothstep(0.10, 0.34, sl) * smoothstep(2.0, 8.0, zz)], 1)
    wS /= wS.sum(1, keepdims=True)
    kS = (rng.random(len(si))[:, None] > np.cumsum(wS, 1)).sum(1).clip(0, len(SH) - 1)
    PS = np.stack([ux[si], uy[si], gz(ux[si], uy[si]) - 0.04], 1)
    lodS = (hu["dcam"][si] > 130.0).astype(int)
    n_s = 0
    inst_tris = 0
    for j, key in enumerate(SH):
        for l in (0, 1):
            m = (kS == j) & (lodS == l)
            if not m.any():
                continue
            hr = SHRUBS[key]["h"]
            th = rng.uniform(hr[0], hr[1], int(m.sum()))
            n_s += gn_kind("shrub_%s_L%d" % (key, l), lib[("shrub_" + key, l)],
                           PS[m], th, rng, c_shrub, lean=1.3)
            inst_tris += int(m.sum()) * _mesh_tris(lib[("shrub_" + key, l)][0][0])
    stats["shrubs"] = n_s

    # young trees coming up through the shrub layer
    sap = np.where(ok & (ur > 0.90) & (ur < 0.90 + 0.055 * q) & (hu["wood"] > 0.30))[0]
    sap = sap[outside_corridor(ux[sap], uy[sap], 3.0)]
    PY = np.stack([ux[sap], uy[sap], gz(ux[sap], uy[sap]) - 0.04], 1)
    stats["saplings"] = gn_kind("sapling", lib[("sapling", 0)], PY,
                                rng.uniform(1.3, 4.0, len(PY)), rng, c_shrub, lean=1.8)
    inst_tris += len(PY) * _mesh_tris(lib[("sapling", 0)][0][0])

    # -- FERNS on the shaded woodland floor -----------------------------------------
    fi = np.where((hu["wood"] > 0.55) & (ur > 0.55) & (ur < 0.55 + 0.30 * q) &
                  (hu["f"] > 10.0) & (hu["built"] < 0.3))[0]
    fi = fi[outside_corridor(ux[fi], uy[fi], 5.0)]
    PF = np.stack([ux[fi], uy[fi], gz(ux[fi], uy[fi]) - 0.03], 1)
    stats["ferns"] = gn_kind("fern", lib[("fern", 0)], PF,
                             rng.uniform(0.35, 1.05, len(PF)), rng, c_shrub, lean=1.0)
    inst_tris += len(PF) * _mesh_tris(lib[("fern", 0)][0][0])
    stats["instanced_tris"] = inst_tris

    # -- GRASS ----------------------------------------------------------------------
    log("grass")
    gstats = build_grass(cir, gr, gz, cam, c_grass, rng, q, ras)
    gstats["instanced_tris"] = gstats.get("instanced_tris", 0) + stats.get("instanced_tris", 0)
    stats.update(gstats)

    # -- SWARD DRIFTS: the mid-scale cover between the hero band and flat colour ----
    log("sward drifts (the tier between a hero clump and a painted field)")
    sstats = build_sward(gr, gz, cam, c_grass, rng, q, ras)
    stats["instanced_tris"] = stats.get("instanced_tris", 0) + sstats.pop("instanced_tris", 0)
    stats.update(sstats)

    # -- WEEDS AND STONES -------------------------------------------------------------
    log("weeds and stones")
    wstats = build_weeds_and_stones(cir, gr, gz, cam, c_weeds, lib, rng, q, ras)
    stats["instanced_tris"] = stats.get("instanced_tris", 0) + wstats.pop("instanced_tris", 0)
    stats.update(wstats)

    # -- GRIT -------------------------------------------------------------------------
    log("grit (bare ground is made of stones, not of a bump map)")
    kstats = build_grit(cir, gr, gz, cam, c_weeds, lib, rng, q, ras)
    stats["instanced_tris"] = stats.get("instanced_tris", 0) + kstats.pop("grit_tris", 0)
    stats.update(kstats)

    # ---- summary ------------------------------------------------------------------
    # Count triangles per UNIQUE mesh once, then multiply by users.  Walking polygons
    # per object is O(objects x polygons) -- 30 k objects x 130 k polys never returns.
    tri_of = {}
    base_tris = 0
    for me in bpy.data.meshes:
        if not (me.name.startswith(PFX) or me.name.startswith(VPFX)):
            continue
        c = np.empty(len(me.polygons), np.int32)
        me.polygons.foreach_get("loop_total", c)
        tri_of[me.name] = int((c - 2).sum())
        base_tris += tri_of[me.name]
    tris = 0
    n_obj = 0
    uniq = set()
    for c in (c_ground, c_trees, c_shrub, c_grass, c_weeds):
        for o in c.objects:
            n_obj += 1
            if o.type == 'MESH':
                uniq.add(o.data.name)
                tris += tri_of.get(o.data.name, 0)
    tris += stats.get("instanced_tris", 0)
    stats["objects"] = n_obj
    stats["unique_meshes"] = len(tri_of)
    stats["base_library_tris"] = base_tris
    stats["evaluated_tris"] = tris
    stats["build_s"] = round(time.time() - t0, 1)
    log("done in %.1f s: %s" % (time.time() - t0, stats))
    return stats


def verge_band(cir, rng, side, per_m, out_extra=42.0, swin=None, bias=True):
    """Sample the ground cover band on one side of the circuit, IN (s, u).

    THIS IS WHERE "not a grass gray line" is actually decided.  The band now starts at
    `C.verge_edge` — INSIDE the road corridor — and runs to `C.platform_edge` + 42 m,
    so it crosses the runoff programme instead of starting outside it.  Terrain builds
    no GROUND in there (the contract's hole), but it still plants: the verge wants
    grass and the user asked for it.  What it must not do is plant on the runoff
    asphalt or in a gravel trap, so both are cut out by `C.runoff_widths`, and the
    pit wall footing and the declared pit-exit apron are cut out too because those are
    build_architecture's concrete.

    `swin` = (s0, s1) restricts the draw to a station window.  It exists so
    `macro_probe` can build the SAME band, from the SAME function, over 200 m of lap
    instead of 3675 — a probe that reimplemented the placement would be evidence about
    the probe and not about the build.

    -> dict of arrays for the surviving samples.
    """
    n_st = cir.N
    sts = np.arange(n_st)
    if swin is not None:
        keepw = (cir.S >= swin[0]) & (cir.S <= swin[1])
        sts = sts[keepw]
    st = np.repeat(sts, per_m)
    n = len(st)
    ds = rng.random(n) * TRACK_DS
    s = (cir.S[st] + ds) % C.LAP
    e = C.verge_edge(s)
    lim = C.platform_edge(s, side)
    # THE FOLD.  (s, u) -> world is only injective while |u| < the radius of curvature
    # on the inside of a bend.  T4 is an R25 hairpin, so a band running to
    # platform_edge + 42 m on its inside crosses the centre of curvature 30 m out and
    # comes back down the other side: MEASURED, 26 % of the band's samples landed at a
    # lateral offset up to 112 m away from the one they were drawn at, and 7 275 of
    # them ended up ON THE RACING SURFACE.  Cap the band at 0.75 R on the inside.
    kk = cir.K[st]
    onin = (side * kk) > 0.0
    cap = np.where(onin & (np.abs(kk) > 1e-9),
                   0.75 / np.maximum(np.abs(kk), 1e-9), 1e9)
    outer = np.minimum(lim + out_extra, cap)
    # THE BIAS, AND ITS SIGN.  For t uniform, u = e + t**k * W has CDF (a/W)**(1/k), so
    # the areal density goes as a**(1/k - 1): k > 1 concentrates samples AT THE VERGE,
    # k < 1 pushes them away from it.  The old k = 0.62 (and the pass before it, 0.55)
    # was the wrong side of 1 and thinned the grass exactly where the camera flies --
    # visible in `before/t5_verge_k062.png` as bare ground with weeds standing in it.
    # k = 1.8 gives density ~ a**-0.44: ~4x the mean at the verge, ~0.6x at 70 m out.
    # ... but a pure power law starves the far half of the band: at the corridor rim
    # 82 m out it left 2.6 clumps/m2 (`before/t10_rim_thinshoulder.png`).  So the draw
    # is a MIXTURE -- 62 % verge-biased, 38 % uniform across the whole band -- which
    # keeps the verge dense and puts a real mown shoulder behind the barrier line.
    r = rng.random(n)
    t = np.where(rng.random(n) < 0.62, r ** 1.8, r) if bias else r
    # FRACTION OF THE WAY TO THIS SAMPLE'S OWN OUTER EDGE -- but only where that edge
    # is the DESIGNED rim.  Returned so a caller can crossfade the band out instead of
    # cutting it (R2-1829).
    #
    # It is `t` and NOT `f`, because `outer` is capped to 0.75 R on the inside of a
    # bend: the designed rim sits at f = 42 m on a straight and at much less through
    # T4, so a taper written against `f` would fade the wrong ground at every hairpin.
    #
    # AND IT IS ZEROED WHERE THE FOLD CAP BINDS, which the first version was not, and
    # that was a real hole rather than a nicety.  MEASURED over the whole lap: 26.6 %
    # of the band lands in the taper zone, and 3.8 % of THOSE are inside the road
    # corridor at a median f of **-14.3 m** -- fourteen metres INBOARD of the rim,
    # clustered at s 919-1225 and s 2603-2756, which is T4 and its neighbours.  There
    # the cap truncates the band deep inside the corridor, and the sward drifts cannot
    # take the handoff because their own gate is `f > 12`.  Fading there removes grass
    # and hands to nothing: a bare strip on the inside of the hairpin, which is the
    # exact defect this whole workstream exists to remove.
    #
    # A crossfade is only legitimate where there is a layer on the other side to
    # receive it.  Where the band was cut short by a numerical guard rather than
    # reaching its rim, there is no other side, so it keeps its hard edge -- and that
    # edge is inside the corridor where the road programme owns the ground anyway.
    capped = outer < (lim + out_extra) - 1e-6
    tdraw = np.where(capped, 0.0, t)
    # ALL the randomness lives in (station, lateral), so the band tests below see the
    # FINAL lateral offset.  The old version drew u, tested the bands and then added
    # gaussian jitter in x and y, which walked clumps back into the gravel.
    u = e + t * np.maximum(outer - e, 0.0) + rng.normal(0, 0.09, n)
    lat = u - e                                  # outboard of the painted verge

    w = C.runoff_widths(s, side)
    bare = ((lat < (w["asphalt"] + w["gravel"])) | (lat < w["apex"]) |
            (lat < 0.05) | (outer <= e + 0.30) | (u > outer))
    keep = ~bare
    idx = np.where(keep)[0]
    st = st[idx]; s = s[idx]; u = u[idx]
    ds = ds[idx]
    hd = cir.H[st]
    us = u * side
    # A point `ds` further along the lap at lateral offset u is NOT at
    # (tangent*ds + normal*u) from the station: it is at tangent*ds*(1 - u*kappa).
    # Dropping the (1 - u*kappa) factor is a lateral error of ds*u*kappa, which at 40 m
    # of offset in a 50 m-radius corner is 0.8 m -- straight into the gravel trap.
    along = ds * (1.0 - us * cir.K[st])
    x = cir.X[st] + np.cos(hd) * along - np.sin(hd) * us
    y = cir.Y[st] + np.sin(hd) * along + np.cos(hd) * us

    # --- and now the test that actually matters --------------------------------------
    # Drawing in (s, u) on ONE side says nothing about which branch of the loop the
    # resulting world point is nearest to.  In the infield a clump drawn 50 m off the
    # esses can be 20 m off the doppler straight, and land in ITS gravel trap.  So
    # everything is re-projected with C.project -- the same call `C.world_ground_z`
    # makes -- and the cross-section test is redone against the branch that is really
    # there.  MEASURED before this pass: 15 753 of 60 000 in-corridor samples were on
    # runoff asphalt or in a gravel bed, and 5 782 were on the racing surface itself.
    s2, u2 = C.project(x, y)
    sd = np.where(u2 >= 0.0, 1.0, -1.0)
    lim2 = np.where(u2 >= 0.0, C.platform_edge(s2, +1), C.platform_edge(s2, -1))
    e2 = C.verge_edge(s2)
    lat2 = np.abs(u2) - e2
    wp = C.runoff_widths(s2, +1)
    wm = C.runoff_widths(s2, -1)
    wa = np.where(u2 >= 0.0, wp["asphalt"], wm["asphalt"])
    wg = np.where(u2 >= 0.0, wp["gravel"], wm["gravel"])
    wx = np.where(u2 >= 0.0, wp["apex"], wm["apex"])
    inside = np.abs(u2) <= lim2
    bad = (lat2 < 0.05) | (lat2 < wa + wg) | (lat2 < wx)
    bt = np.where(u2 >= 0.0, C.barrier_type(s2, +1), C.barrier_type(s2, -1))
    az = np.where(u2 >= 0.0, C.apron_zone(s2, +1), C.apron_zone(s2, -1))
    bad |= inside & ((bt == C.B_CONCRETE) | (az > 0.4))
    j = np.where(~bad)[0]
    return dict(s=s2[j], u=u2[j], lat=lat2[j], x=x[j], y=y[j], inside=inside[j],
                f=np.abs(u2[j]) - lim2[j],
                # ... and zeroed once more, on the REPROJECTED result.  `capped` catches
                # the fold cap at a hairpin; it does not catch a sample drawn near its
                # own rim on one branch that `C.project` lands inside ANOTHER branch's
                # corridor -- "a clump drawn 50 m off the esses can be 20 m off the
                # doppler straight", as the test below already says about gravel.
                # MEASURED: 23,354 of 2,130,639 in-corridor samples, median f -11.0 m,
                # still being tapered after the cap fix.  `inside` is exactly `f <= 0`,
                # and the sward's own gate is `f > 12`, so tapering any of them hands to
                # nothing.  THE TAPER APPLIES ONLY OUTBOARD OF THE RIM.
                tdraw=np.where(inside[j], 0.0, tdraw[idx][j]),
                side=sd[j],
                scuff=np.where(u2[j] >= 0.0, scuff(s2[j], +1), scuff(s2[j], -1)),
                gravel_edge=(wa + wg)[j],
                has_gravel=((wg > 1.0) | (wx > 1.0))[j])


def band_z(b, gz):
    """z for a band sample: the CONTRACT datum inside the corridor, terrain outside.

    Inside the corridor `gz` is a smooth continuation of the natural ground and is
    completely wrong — up to 0.39 m proud of the tarmac at T10/T11, which is the
    review's finding #1 in one number.  Nothing inside the corridor may be placed
    with it.  At the rim the two agree exactly, so the join is invisible.
    """
    z = np.where(b["inside"], C.ground_z(b["s"], b["u"]), gz(b["x"], b["y"]))
    return z


def build_grass(cir, gr, gz, cam, coll, rng, q, ras, swin=None, meadow=True,
                nlib=None):
    """Grass, weeds and stones.  The verge band is generated ALONG the track in (s, u)
    so every clump lands exactly where the eye will be, and it now crosses the road
    corridor because the contract says terrain plants there even though it meshes
    nothing there."""
    kinds = list(GRASS.keys())                       # fescue tussock meadow dry reed
    nlib = max(4, int(round(11 * (0.4 + 0.6 * q)))) if nlib is None else int(nlib)
    # TWO LIBRARIES, ONE PER LOD.  Hero clumps carry channelled blades in tillers at
    # 6 segments and 190-330 blades; far clumps are the old flat 3-segment ribbon at
    # 54-98.  The split is `GRASS_HERO_D` metres of the LENS -- `CameraPath.dist3`,
    # the true 3-D distance to the nearest camera station, not the centreline and not
    # the horizontal projection of the path -- because that is the only distance that
    # decides whether a blade is ever more than a quarter of a pixel.  Blades per clump cost nothing at render
    # time (one resident mesh, millions of instances); what costs is BVH traversal per
    # instance, so it is spent where the lens is.
    libs = {}
    libs_far = {}
    for k in kinds:
        hero, far = [], []
        nb = (190, 330) if k != "reed" else (70, 130)
        if LEGACY_GRASS:
            nb, hsegs, hlod = (54, 98), 3, 1
        else:
            hsegs, hlod = 6, 0
        for i in range(nlib):
            me, hgt = gen_grass(np.random.default_rng(int(rng.integers(1 << 31))), k,
                                blades=int(rng.integers(*nb)), segs=hsegs, lod=hlod)
            me.name = VPFX + "grass_%s_H%02d" % (k, i)
            hero.append((me, hgt))
        for i in range(max(3, nlib // 2)):
            me, hgt = gen_grass(np.random.default_rng(int(rng.integers(1 << 31))), k,
                                blades=int(rng.integers(54, 98)), segs=3, lod=1)
            me.name = VPFX + "grass_%s_F%02d" % (k, i)
            far.append((me, hgt))
        libs[k] = hero
        libs_far[k] = far
    log("  grass library: %d hero clumps (%d polys each, mean) + %d far"
        % (len(kinds) * nlib,
           int(np.mean([len(m.polygons) for m, _ in libs[kinds[0]]])),
           len(kinds) * len(libs_far[kinds[0]])))

    # --- the verge band, from the painted verge outward -----------------------------
    # 900 per station-metre per side is ~19 clumps/m^2 at the verge falling to ~11 at
    # the doppler station's 26 m offset (the mixture bias below); with 190-330 blade
    # hero clumps that is 2 300-4 000 blades/m^2 where the camera flies, against the
    # 400-700 of the previous pass and the ~35 of the pass before that, which rendered
    # as bare soil with sprigs on it.
    per_m = max(6, int(900.0 * q))
    bands = [verge_band(cir, rng, side, per_m, swin=swin) for side in (+1, -1)]
    B = {k: np.concatenate([b[k] for b in bands]) for k in bands[0]}
    Pxy = np.stack([B["x"], B["y"]], 1)
    hg = habitat(gr, gz, cam, B["x"], B["y"], ras)
    # patchy, thin where it is walked on and where cars run wide, lush in the hollows
    patch = 0.5 + 0.5 * fbm(B["x"] / 11.0, B["y"] / 11.0, 3, seed=77)
    dens = np.clip(0.35 + 0.65 * patch, 0, 1) * (1.0 - 0.55 * B["scuff"])
    # scuffed right at the kerb -- but only where cars actually go, and never by half
    dens *= 1.0 - (0.15 + 0.40 * B["scuff"]) * smoothstep(2.2, 0.0, B["lat"])
    # ---- THE BAND'S OUTER RIM IS A CROSSFADE, NOT A CUT --------------  R2-1829
    #
    # `out_extra = 42` put a hard edge at 42 m outboard of the corridor rim: verge
    # clumps at full density on the inside of it, none at all on the outside, and the
    # sward drifts alone beyond. MEASURED on the R2-1821 render at f2760, fine-detail
    # sd across that line: 4.5 -> 2.6 in one 32 px tile.
    #
    # IT IS AN OLD EDGE THAT R2-1821 MADE VISIBLE. Before the district fix both sides
    # of it were bare (1.0 against 1.4) and there was nothing to see; restoring the
    # verge on the near side is what turned it into a band. It was found by looking at
    # a 1:1 crop, not by any metric in that pass.
    #
    # THE FIX IS THE ONE R2-1661 ALREADY USED ON THE TIER JOINS: crossfade instead of
    # butt. The sward drifts are at FULL weight from f = 34 (`smoothstep(12, 34, f)`),
    # which is inboard of the rim at 42, so the band can hand off to a layer that is
    # already carrying the ground. Nothing is left uncovered by this -- the assertion
    # in `tools/r2_1829_edges.py` is that no bin across the handoff falls below what
    # the ground BEYOND the rim already reads, and that is what "no blank spots" means
    # here: the bulge is removed, not a hole opened.
    dens *= smoothstep(1.0, 1.0 - VERGE_TAIL_T, B["tdraw"])
    # THE BUILT PAD MUST NOT STERILISE THE VERGE.  This test used `built`, the paddock
    # DISTRICT — circuit x -490..+140, y -70..+120 — which contains the WHOLE pit
    # straight, both its verges included.  Testing it here removed every clump from the
    # s = 3115..250 south verge, where `C.runoff_widths` says there are 8.5 m of grass
    # between the painted verge and the barrier at circuit y = -19; the frame came back
    # as bare olive ground (`before/pit_verge_nograss.png`).
    #
    # THAT WAS PATCHED WITH `| B["inside"]` AND THE PATCH WAS THE WRONG SHAPE.  It saved
    # the strip INSIDE the corridor and left everything outboard of the rim deleted, so
    # the band from the rim out to `platform_edge + 42` — the whole grass shoulder of
    # the pit straight, on BOTH sides — still had not one clump in it.  Measured on
    # f2760: 9.5 % of the ground in frame lies at f = 0..12 m, 77 % of that is inside
    # the district, and it carries NO verge clump (this test), NO sward drift (the tier
    # starts at f = 12) and NO meadow (it starts at f = 18).  Three tiers, three
    # different reasons, one strip of ground, and it is the strip the client called
    # "5 feet away from the main road and buildings".
    #
    # `paved` is the contract's declared concrete instead of the drawn district, so the
    # garages and the paddock still get no verge band — correctly, they are buildings —
    # and the grass shoulder gets one.  R2-1821.
    keep = (rng.random(len(Pxy)) < dens) & (hg["wood"] < 0.62) \
        & ((hg["paved"] < 0.35) | B["inside"])
    Pv = Pxy[keep]
    hv = {k: v[keep] for k, v in hg.items()}
    Bv = {k: v[keep] for k, v in B.items()}
    hv["f"] = Bv["f"]                       # exact, overriding the 14 m raster read
    zv = band_z(Bv, gz) - 0.055
    log("  verge clumps: %d  (%d inside the road corridor, on C.ground_z)"
        % (len(Pv), int(Bv["inside"].sum())))

    # --- meadow / infield / hillside -------------------------------------------------
    if meadow:
        mx, my, mr = jitter_grid(-1300.0, 1250.0, -950.0, 1650.0, 1.35, 4242)
        km = ras.sample(mx, my)["D"] < 430.0
        mx, my, mr = mx[km], my[km], mr[km]
        hm = habitat(gr, gz, cam, mx, my, ras)
        dens = (0.34 + 0.5 * fbm(mx / 26.0, my / 26.0, 3, seed=91))
        dens *= (1.0 - 0.55 * hm["wood"]) * (1.0 - hm["paved"])      # R2-1821
        dens *= smoothstep(18.0, 55.0, hm["f"])   # the band above owns everything nearer
        dens *= smoothstep(700.0, 260.0, hm["dcam"])
        mi = np.where(mr < dens * 0.85 * q)[0]
        Pm = np.stack([mx[mi], my[mi]], 1)
        hmi = {k: v[mi] for k, v in hm.items()}
        zm = gz(Pm[:, 0], Pm[:, 1]) - 0.055
    else:
        Pm = np.zeros((0, 2)); zm = np.zeros(0)
        hmi = {k: v[:0] for k, v in hv.items()}
    log("  meadow clumps: %d" % len(Pm))

    P = np.concatenate([Pv, Pm], 0)
    z = np.concatenate([zv, zm])
    H = {k: np.concatenate([hv[k], hmi[k]]) for k in hv}
    scf = np.concatenate([Bv["scuff"], np.zeros(len(Pm))])
    n = len(P)
    # kind by habitat: mown fescue on the verge, tussock in the rough, seeding meadow
    # grass out in the fields, dry burnt grass on the escarpment, the exposed ridge and
    # wherever cars run wide, reeds in the wet bottom of the hollow
    mown = smoothstep(34.0, 2.0, H["f"])
    dry = smoothstep(3.5, 9.0, H["z"]) + smoothstep(0.12, 0.34, H["slope"]) * 0.5 \
        + scf * 1.10
    wet = smoothstep(-1.0, -3.4, H["z"])
    W = np.stack([0.15 + 0.85 * mown,
                  0.30 + 0.35 * (1 - mown),
                  0.10 + 0.60 * (1 - mown) * (1 - wet),
                  0.05 + 0.75 * np.clip(dry, 0, 1),
                  0.02 + 0.85 * wet * (1 - mown)], 1)
    W = np.clip(W, 1e-4, None); W /= W.sum(1, keepdims=True)
    ki = (rng.random(n)[:, None] > np.cumsum(W, 1)).sum(1).clip(0, len(kinds) - 1)

    # clump size: shorter where mown, and correlated at 7 m so tufts come in drifts
    base = rng.uniform(0.72, 1.45, n) * (1.0 - 0.32 * mown)
    base *= 0.55 + 0.75 * (0.5 + 0.5 * fbm(P[:, 0] / 7.0, P[:, 1] / 7.0, 2, seed=131))
    # ... and BROADER where mown, independently of height (see gn_kind)
    spread = 1.0 + 0.75 * mown
    # THE PREDICATE, R2-1661.  `dcam3`, not `dcam`: the horizontal metric says the
    # ground under beat 6's 140 m crane is zero metres from the lens and buys it hero
    # clumps, and measured over the real path that phantom disc is HALF the hero
    # ground outside the verge band (0.0493 km2 on the horizontal metric against
    # 0.0252 km2 on the true one).  Beats 1-5 keep the lens 2-6 m up, so a clump 47 m
    # out horizontally is 47.4 m out in three dimensions and does not change tier.
    hero = H["dcam3"] < GRASS_HERO_D
    tot = 0
    nhero = 0
    itris = 0
    for j, k in enumerate(kinds):
        for tier, lb, tag in ((hero, libs, "H"), (~hero, libs_far, "F")):
            m = (ki == j) & tier
            if not m.any():
                continue
            hgt = np.array([h for _, h in lb[k]]).mean()
            got = gn_kind("grass_%s_%s" % (k, tag), lb[k],
                          np.stack([P[m, 0], P[m, 1], z[m]], 1),
                          base[m] * hgt, rng, coll, lean=0.9, wide=0.11,
                          xy=spread[m])
            tot += got
            if tag == "H":
                nhero += got
            itris += int(m.sum()) * _mesh_tris(lb[k][0][0])
    log("  grass: %d clumps, %d of them hero (< %.0f m of the lens, 3-D)"
        % (tot, nhero, GRASS_HERO_D))
    return dict(grass_clumps=int(tot), grass_hero_clumps=int(nhero),
                grass_library=len(kinds) * nlib,
                grass_in_corridor=int(Bv["inside"].sum()),
                instanced_tris=itris)


def build_weeds_and_stones(cir, gr, gz, cam, coll, lib, rng, q, ras, swin=None,
                           field=True):
    """Weeds on the verge and the field margins; stones on scree, in the swale, and
    dragged out of the gravel traps.

    A verge is not grass.  Six weed habits and three stone classes, placed by the same
    (s, u) band as the grass so they land where the lens is, and cut out of the runoff
    asphalt and the traps by `C.runoff_widths` exactly as the grass is.
    """
    stats = {}
    itris = 0
    per_m = max(1, int(15.0 * q))
    bands = [verge_band(cir, rng, side, per_m, out_extra=26.0, swin=swin)
             for side in (+1, -1)]
    B = {k: np.concatenate([b[k] for b in bands]) for k in bands[0]}
    hb = habitat(gr, gz, cam, B["x"], B["y"], ras)

    # WEEDS.  Rank ground (nettle), disturbed margins (dock, thistle, ragwort),
    # trodden strips (plantain) and dry banks (yarrow).
    rich = smoothstep(0.0, 1.0, 0.5 + 0.5 * fbm(B["x"] / 34.0, B["y"] / 34.0, 3, seed=613))
    dens = (0.30 + 0.55 * rich) * (1.0 - 0.55 * B["scuff"])
    dens *= smoothstep(0.0, 3.5, B["lat"])            # not on the painted verge
    dens *= (1.0 - 0.55 * hb["wood"])
    dens *= np.where(B["inside"], 1.0, 1.0 - 0.85 * hb["built"])
    sel = np.where((rng.random(len(B["x"])) < np.clip(dens, 0, 1))
                   & ((hb["built"] < 0.4) | B["inside"]))[0]
    if len(sel):
        Bw = {k: v[sel] for k, v in B.items()}
        zw = band_z(Bw, gz) - 0.02
        rr = rich[sel]
        walkish = smoothstep(4.0, 0.5, Bw["lat"])
        # THE WHITE SPECKLES.  Measured on CAM_T10_HELI.png: 1 745 isolated pixels in a
        # 1200 x 500 crop sit 28-112/255 above their own 9x9 local median, the brightest
        # at (220, 208, 193).  They are yarrow umbels and ragwort corymbs -- physically
        # correct flowers (a white umbel really is that bright against 0.05 turf) that
        # are SUB-PIXEL at 200-400 m, and a sub-pixel object three stops above its
        # background does not average down, it aliases into a dot.  At 4K that reads as
        # dirt on the lens, which is what the user called it.
        # A flowering weed is therefore a NEAR-FIELD object: full weight inside 45 m of
        # the camera path, gone by 110 m, with the non-flowering habits taking up the
        # weight so the far verge does not thin out.  The flowers that survive are the
        # ones with enough pixels to read AS flowers.
        near = smoothstep(110.0, 45.0, hb["dcam"][sel])
        W = np.stack([0.22 + 0.30 * rr + 0.10 * (1 - near),        # dock
                      0.16 + 0.34 * (1 - rr) + 0.10 * (1 - near),  # thistle
                      (0.14 + 0.30 * (1 - rr)) * near,             # ragwort (yellow)
                      0.10 + 0.55 * walkish + 0.14 * (1 - near),   # plantain
                      (0.12 + 0.28 * (1 - rr)) * near,             # yarrow  (white)
                      0.08 + 0.50 * rr + 0.10 * (1 - near)], 1)    # nettle
        W = np.clip(W, 1e-4, None); W /= W.sum(1, keepdims=True)
        kw = (rng.random(len(sel))[:, None] > np.cumsum(W, 1)).sum(1).clip(0, len(WEED_ORDER) - 1)
        nwd = 0
        for j, key in enumerate(WEED_ORDER):
            m = kw == j
            if not m.any():
                continue
            hr = WEEDS[key]["h"]
            nwd += gn_kind("weed_" + key, lib[("weed_" + key, 0)],
                           np.stack([Bw["x"][m], Bw["y"][m], zw[m]], 1),
                           rng.uniform(hr[0], hr[1], int(m.sum())), rng, coll,
                           lean=1.2, wide=0.13)
            itris += int(m.sum()) * _mesh_tris(lib[("weed_" + key, 0)][0][0])
        stats["weeds"] = nwd
        log("  weeds: %d  (%d inside the road corridor)" % (nwd, int(Bw["inside"].sum())))

    # GRAVEL SPRAY: pebbles dragged out of a trap and thrown across the grass behind
    # it.  Only where there IS a trap, only downstream of it, and only where cars
    # actually go off — which is `scuff`.
    spray = (B["has_gravel"] & (B["lat"] > B["gravel_edge"]) &
             (B["lat"] < B["gravel_edge"] + 9.0))
    pd = np.clip(0.85 * B["scuff"] * smoothstep(9.0, 0.0, B["lat"] - B["gravel_edge"]), 0, 1)
    ps = np.where(spray & (rng.random(len(B["x"])) < pd))[0]
    if len(ps):
        Bp = {k: v[ps] for k, v in B.items()}
        zp = band_z(Bp, gz) - 0.012
        stats["gravel_spray"] = gn_kind(
            "stone_spray", lib[("stone_pebble", 0)],
            np.stack([Bp["x"], Bp["y"], zp], 1),
            rng.uniform(0.030, 0.085, len(ps)), rng, coll, lean=0.0, wide=0.22)
        itris += len(ps) * _mesh_tris(lib[("stone_pebble", 0)][0][0])
        log("  gravel spray: %d pebbles" % len(ps))

    # FIELD STONE AND SCREE, outside the corridor only
    if not field:
        stats["instanced_tris"] = itris
        return stats
    sx, sy, sr = jitter_grid(-1300.0, 1250.0, -950.0, 1650.0, 2.6, 8123)
    ks = ras.sample(sx, sy)["D"] < 900.0
    sx, sy, sr = sx[ks], sy[ks], sr[ks]
    hs = habitat(gr, gz, cam, sx, sy, ras)
    stony = smoothstep(0.12, 0.40, hs["slope"])
    stony = np.maximum(stony, 0.45 * smoothstep(0.40, 0.72,
                                                fbm(sx / 128.0, sy / 128.0, 3, seed=421)))
    pd = stony * (1.0 - 0.9 * hs["built"]) * (1.0 - 0.5 * hs["plateau"]) * q
    take = np.where((hs["f"] > 3.0) & (sr < pd * 0.55))[0]
    take = take[outside_corridor(sx[take], sy[take], 0.6)]
    if len(take):
        zs = gz(sx[take], sy[take]) - 0.04
        big = rng.random(len(take))
        for key, m, hr in (("cobble", big < 0.86, (0.10, 0.34)),
                           ("boulder", big >= 0.86, (0.45, 1.70))):
            if not m.any():
                continue
            stats["stones_" + key] = gn_kind(
                "stone_" + key, lib[("stone_" + key, 0)],
                np.stack([sx[take][m], sy[take][m], zs[m]], 1),
                rng.uniform(hr[0], hr[1], int(m.sum())), rng, coll, lean=0.0, wide=0.20)
            itris += int(m.sum()) * _mesh_tris(lib[("stone_" + key, 0)][0][0])
        log("  field stone: %d" % len(take))
    stats["instanced_tris"] = itris
    return stats


# --- GRIT: what makes bare ground bare ground ------------------------------------------
#
# "bare ground is a flat sandy plane with no stones or clods."  It was, and no shader
# could have fixed it.  MEASURED on CAM_T10_HELI.png over an 840 x 460 crop of the
# escarpment: local (9x9) sigma of luminance 6.25/255 at a mean of 108.4, i.e. 5.8 %
# RELATIVE contrast -- and 5.1 % on the pale runoff beside it.  The surface is flat to
# within a few pixel values over a metre of ground, because everything the ground
# shader carries below ~0.4 m is a BUMP, and a bump has no silhouette, casts no shadow
# on its neighbour and disappears entirely at a 12.47 deg grazing sun where the only
# thing that reads is the shadow one clod throws across the next.
#
# Field stone was already scattered, but at 0.10-1.70 m and only on slopes > 7 deg and
# in the ploughed patches -- 244 cobbles and 30 boulders in the whole world.  What bare
# ground is actually made of is the 10-70 mm fraction: grit, flint chips, dried clods
# of the soil itself.  That fraction is now geometry.
#
# BUDGET.  It only has to exist where it can be resolved.  At 4K on a 35 mm lens one
# pixel is 1.94 mm at 7.5 m, 24 mm at 95 m; a 40 mm clod is 20 px near and 1.6 px at
# GRIT_D, so GRIT_D is where it stops mattering and the pass stops.  Inside that,
# density is driven by BARENESS -- the inverse of the very same 11 m patch field that
# thins the grass, plus `scuff`, slope and dryness -- so grit appears exactly where the
# sward does not, and the two never fight for the same square metre.

GRIT_D = 95.0        # metres of camera path beyond which grit is sub-pixel and skipped
GRIT_NEAR = 15.0     # pieces per m2 on fully bare ground at the lens
GRIT_FAR = 2.2       # ... at GRIT_D
GRIT_KINDS = (
    #  name        size range (m)  share  library key
    ("grit_chip",  (0.012, 0.038), 0.46, "gritstone"),
    ("grit_stone", (0.035, 0.095), 0.24, "gritstone"),
    ("grit_clod",  (0.020, 0.070), 0.30, "clod"),
)


def build_grit(cir, gr, gz, cam, coll, lib, rng, q, ras, swin=None):
    """Stones, chips and soil clods on bare ground, within GRIT_D of the camera path."""
    per_m = max(4, int(700.0 * q))
    bands = [verge_band(cir, rng, side, per_m, out_extra=22.0, swin=swin, bias=False)
             for side in (+1, -1)]
    B = {k: np.concatenate([b[k] for b in bands]) for k in bands[0]}
    if not len(B["x"]):
        return {}
    hb = habitat(gr, gz, cam, B["x"], B["y"], ras)
    # width of the band this sample was drawn from, so the ACCEPTANCE gives a constant
    # areal density instead of a constant count per station-metre: (lat - f) is
    # platform_edge - verge_edge exactly, whatever the runoff does.
    Wb = np.maximum((B["lat"] - B["f"]) + 22.0, 1.0)
    patch = 0.5 + 0.5 * fbm(B["x"] / 11.0, B["y"] / 11.0, 3, seed=77)
    bare = np.clip(1.0 - np.clip(0.35 + 0.65 * patch, 0, 1), 0, 1)
    bare = np.clip(bare * 1.35 + 0.60 * B["scuff"]
                   + 0.50 * smoothstep(0.12, 0.34, hb["slope"])
                   + 0.40 * smoothstep(3.5, 9.5, hb["z"])
                   + 0.30 * smoothstep(0.42, 0.78, fbm(B["x"] / 23.0, B["y"] / 23.0,
                                                       3, seed=5501)), 0.0, 1.0)
    tgt = (GRIT_FAR + (GRIT_NEAR - GRIT_FAR)
           * smoothstep(GRIT_D, 6.0, hb["dcam"])) * bare * q
    p = np.clip(tgt * Wb / float(per_m), 0.0, 1.0)
    sel = np.where((rng.random(len(p)) < p) & (hb["dcam"] < GRIT_D * 1.05)
                   & (hb["wood"] < 0.80))[0]
    if not len(sel):
        return {}
    Bs = {k: v[sel] for k, v in B.items()}
    z = band_z(Bs, gz)
    r = rng.random(len(sel))
    cum = 0.0
    stats = {}
    itris = 0
    tot = 0
    for (name, hr, share, key) in GRIT_KINDS:
        m = (r >= cum) & (r < cum + share)
        cum += share
        if not m.any() or (key, 0) not in lib:
            continue
        # HALF BURIED.  A stone lying ON a plane is a stone lying on a plane; a stone
        # bedded 30-60 % into it is a stone in the ground, and at a grazing sun the
        # difference is the shape of the shadow it throws.
        h = rng.uniform(hr[0], hr[1], int(m.sum()))
        got = gn_kind(name, lib[(key, 0)],
                      np.stack([Bs["x"][m], Bs["y"][m],
                                z[m] - h * rng.uniform(0.30, 0.60, int(m.sum()))], 1),
                      h, rng, coll, lean=0.0, wide=0.30)
        tot += got
        itris += got * _mesh_tris(lib[(key, 0)][0][0])
    log("  grit: %d pieces (%.1f-%.1f per m2 of bare ground within %.0f m of the path)"
        % (tot, GRIT_FAR, GRIT_NEAR, GRIT_D))
    stats["grit_pieces"] = int(tot)
    stats["grit_tris"] = int(itris)
    return stats


# ==================================================================================
# 11.  TEST RENDER HARNESS  (its own camera/sun/world; build() creates none of these)
# ==================================================================================

_VIEWS_WORLD = {
    # name:        (position,                   look-at,                 lens)
    "wide":        ((594.19, 16.05, 140.0),     (15.0, 0.0, 6.0),        18.75),
    "hairpin":     ((233.0, 917.0, 0.85),       (250.0, 985.0, 1.0),     21.0),
    "doppler":     ((-578.82, -47.47, 4.80),    (-540.0, 40.0, 2.0),     35.0),
    "esses":       ((-90.0, 300.0, 78.0),       (-250.0, 540.0, 8.0),    28.0),
    "verge":       ((300.0, 205.0, 1.35),       (430.0, 260.0, 2.0),     35.0),
    "ridge":       ((-330.0, 250.0, 26.0),      (-300.0, 640.0, 12.0),   40.0),
    "plunge":      ((-430.0, 30.0, 30.0),       (-620.0, 180.0, 4.0),    35.0),
    # repeat-hunting frames: long lenses straight down a treeline, which is where a
    # duplicated asset would betray itself.  See build_terrain.md section 7.
    "repeat_n":    ((120.0, 470.0, 12.0),       (-330.0, 700.0, 16.0),   85.0),
    "repeat_s":    ((-160.0, -120.0, 9.0),      (330.0, 60.0, 14.0),     85.0),
    # grass at knee height OUTSIDE the graded platform -- (262,168) was inside it, i.e.
    # on the bare worn corridor another module paves over, and showed no grass at all.
    # The trailing True means both z values are ABOVE LOCAL GROUND, resolved by ray-cast
    # in test_scene: this spot is on the esses ridge at ~+12 m, and an absolute z of 0.45
    # buried the camera ten metres underground (the frame came back black with the sky
    # upside down at the bottom -- that is what a camera inside the terrain looks like).
    "grass":       ((-318.0, 268.0, 0.45),      (-286.0, 330.0, 1.1),    50.0, True),
    # ---- BEAT 6, THE ENDING, AT THE POSE THAT ACTUALLY RENDERED THE 4K STILLS -----
    # R2-1129: two beat-6 cameras exist.  `world/camera_rig_path.json` is sha256-clean
    # and selftest-green and is NOT the camera that made
    # `~/vast-render/out/seq/r2943_4k/*.png`; those came from
    # `work/r2941/film17_R2943_path.json` via the blend's own baked camera, and they
    # are the only 4K frames of the ending that exist.  A ground A/B judged against
    # them has to be shot from the same place with the same lens, so these four are
    # lifted straight out of the R2943 path (position, forward vector x 300 m, lens).
    #
    #                    cm per delivered pixel at the frame's ground axis
    # b6_2760  60 m up, 21 mm   6.5   the climb
    # b6_2811  99 m up, 22 mm   9.2   THE WORST CASE.  Widest ground coverage of the
    #                                 beat (420 m of world across the frame), and the
    #                                 frame the client is describing.
    # b6_2937 140 m up, 84 mm   3.8
    # b6_2978 140 m up, 130 mm  2.5   THE CONTROL.  Ground 294-417 m out at 2-3 cm per
    #                                 pixel, hero grass on the near bank, and it looks
    #                                 right.  If this frame gets worse, the fix is wrong.
    # ---- DIAGNOSTIC, NOT A FILM FRAME -------------------------------------  R2-1824
    # The sward layer's outer radius is at `dcam3` ~ 1050 m, and `dcam3` is distance to
    # the nearest CAMERA PATH station -- the path wraps the whole 3675 m lap, so that
    # radius is the far farmland OUTSIDE the circuit, behind the treeline, in every
    # delivered view. MEASURED over ten of them: the best (`esses`) puts 0.84 % of its
    # frame inside the fade band and `b6_2978` puts 0.00 %. **No frame in this film can
    # show this fix.** That is a reason to state it, not a reason to skip the check, so
    # this view is sited on the one patch of open, unwooded, near-level ground inside
    # the band -- world (-1260, 1020), found by histogramming the band itself -- and
    # looks along it from 1418 m out, which is beyond the band's own outer edge so the
    # camera does not drag the radius with it. Adding a VIEW cannot perturb placement:
    # `CameraPath` is built from the circuit and the beat keys, never from `VIEWS`.
    "sward_rim":   ((-1440.51, 1426.72, 63.13),  (-1260.00, 1020.00, 4.60), 50.0),
    "b6_2760":     ((420.07, 88.51, 60.28),     (431.43, 370.11, -42.53), 21.02),
    "b6_2811":     ((514.49, 61.05, 99.23),     (472.92, 334.95, -15.86), 22.00),
    "b6_2937":     ((594.19, 16.05, 140.00),    (514.26, 278.25, 18.09),  84.13),
    "b6_2978":     ((594.19, 16.05, 140.00),    (514.26, 278.25, 18.09),  129.99),
}

# ---- LIGHTING FOR TEST RENDERS ONLY -------------------------------------------------
#
# THIS IS NO LONGER A RIG OF ITS OWN.  build_terrain.md 2.1 used to publish an assumed
# sun (120 W/m2 at (1, .735, .470), aerosol 1.45, ozone 1.80, direct:diffuse 3.0:1,
# AgX -2.70) and invite the sky owner to adopt it.  build_sky measured instead of
# assuming and shipped different numbers, so every material calibrated against 2.1 was
# calibrated against a light that does not exist.
#
# The harness therefore IMPORTS build_sky and lights with the film's actual sun, sky,
# cloud decks and atmosphere.  That is the whole point of the exercise: a terrain render
# is only evidence if it is lit by the light the terrain will actually be lit by.  If
# build_sky cannot be imported the harness falls back to world_contract's published
# constants, which are build_sky's own measured values, and says so in the log.

# EXPOSURE.  The contract hands off REFERENCE_EXPOSURE_EXTERIOR = -3.048, solved so that
# `lambert_radiance(0.18)` (mean 1.4888) lands on AgX mid grey.  MEASURED against the rig
# build_sky actually ships, with `probe_albedo` -- four known-albedo lambertian patches at
# z = 0.60 m, rendered LINEAR into an EXR under build_sky.build():
#
#     albedo        measured (R,G,B)              measured / lambert_radiance
#     0.180 grey    2.6938  2.2354  1.7471        1.609  1.531  1.312
#     turf  0.051   0.6464  1.0430  0.2859        1.654  1.568  1.380
#     dry   0.127   2.6059  1.9164  0.6295        1.648  1.575  1.372
#     scree 0.217   3.3969  2.7499  1.9567        1.602  1.527  1.309
#
# The ratio is constant to +-1.6 % across a 4.3x range of albedo, so THE MATERIALS ARE
# RIGHT and the constant is not: `C.SKY_IRRADIANCE` was measured from the sky texture
# alone and does not include SKY_Atmosphere's in-scattering, which adds ~38 W/m2 of
# warm airlight to a horizontal surface.  An 0.18 surface therefore renders at 2.2254,
# i.e. log2(1.4888/2.2254) = -0.580 stops away from where the contract intends it.
#
# Re-measured with the built terrain in the scene (which occludes the lower hemisphere
# and bounces a little back) the grey patch reads 2.1539 mean, i.e. -0.533 stops; the
# two bracket the constant to within 0.05 stops.
#
# So this harness exposes at the measured value and says so.  The film's exposure is the
# camera rig's (task #34) and the constant is build_sky's; this is a finding for both,
# not a unilateral regrade -- both numbers are printed on every render.
# THIS WAS THE THIRD INDEPENDENT COPY of the film's exposure.  The -0.580 here
# was this module's own albedo-probe measurement and it was right; it is now
# imported rather than restated, so it cannot drift from render_setup2/3.
# world/film_exposure.py splits the same correction into its two MEASURED parts
# (SKY_Atmosphere's airlight -0.463, C.SKY_IRRADIANCE's shortfall -0.117) and
# gates the total against a rendered 18 % card: -3.6343 measured, -3.628 shipped.
import film_exposure as FX                                        # noqa: E402
EXPOSURE_CONTRACT = FX.CONTRACT_EXPOSURE               # -3.048
EXPOSURE_AIRLIGHT_STOPS = FX.ATMOSPHERE_STOPS + FX.SKY_SHORTFALL_STOPS   # -0.580
EXPOSURE = FX.FILM_EXPOSURE                            # -3.628
_SKY = None


def _sky_module():
    global _SKY
    if _SKY is None:
        try:
            import build_sky
            _SKY = build_sky
        except Exception as e:                                  # pragma: no cover
            log("build_sky unavailable (%s); falling back to contract constants" % e)
            _SKY = False
    return _SKY or None


def _fallback_light(coll):
    """world_contract's published sun + sky, for when build_sky cannot be imported."""
    sc = bpy.context.scene
    sun = bpy.data.lights.new("TER_TEST_sun", 'SUN')
    sun.energy = C.SUN_ENERGY
    sun.angle = math.radians(C.SUN_ANGULAR_DIAM_DEG)
    sun.color = C.SUN_COLOR
    so = bpy.data.objects.new("TER_TEST_sun", sun)
    coll.objects.link(so)
    so.rotation_mode = 'QUATERNION'
    so.rotation_quaternion = Vector(tuple(C.SUN_DIR)).to_track_quat('Z', 'Y')

    w = bpy.data.worlds.get("TER_TEST_world") or bpy.data.worlds.new("TER_TEST_world")
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    sky = nt.nodes.new("ShaderNodeTexSky")
    types = [i.identifier for i in sky.bl_rna.properties['sky_type'].enum_items]
    sky.sky_type = C.SKY_MODEL if C.SKY_MODEL in types else types[0]
    for attr, val in (("sun_elevation", math.radians(C.SUN_ELEV_DEG)),
                      ("sun_rotation", math.radians(C.SKY_SUN_ROTATION_DEG)),
                      ("sun_disc", C.SKY_SUN_DISC), ("sun_intensity", 1.0),
                      ("altitude", C.SKY_ALTITUDE), ("air_density", C.SKY_AIR),
                      ("aerosol_density", C.SKY_AEROSOL),
                      ("ozone_density", C.SKY_OZONE)):
        if hasattr(sky, attr):
            setattr(sky, attr, val)
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs[1].default_value = C.SKY_STRENGTH
    out = nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(sky.outputs[0], bg.inputs[0])
    nt.links.new(bg.outputs[0], out.inputs[0])

    # aerial perspective, at the CONTRACT's extinction.  The old harness ran 2.2e-5 /m
    # and called it "26 km visibility"; Koschmieder says 3.912 / 2.2e-5 = 178 km, so it
    # was 7.7x too thin and the 3.7 km lap had almost no depth cue.
    me = bpy.data.meshes.new("TER_TEST_haze")
    e = 26000.0
    vs = [(-e, -e, -400.0), (e, -e, -400.0), (e, e, -400.0), (-e, e, -400.0),
          (-e, -e, 4200.0), (e, -e, 4200.0), (e, e, 4200.0), (-e, e, 4200.0)]
    fs = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
          (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    me.from_pydata(vs, [], fs)
    me.update()
    hm = bpy.data.materials.get("TER_TEST_haze") or bpy.data.materials.new("TER_TEST_haze")
    hm.use_nodes = True
    ht = hm.node_tree
    ht.nodes.clear()
    vol = ht.nodes.new("ShaderNodeVolumeScatter")
    vol.inputs["Color"].default_value = (*C.SKY_TINT, 1.0)
    vol.inputs["Density"].default_value = C.SIGMA_EXT_550
    vol.inputs["Anisotropy"].default_value = 0.62
    hout = ht.nodes.new("ShaderNodeOutputMaterial")
    ht.links.new(vol.outputs[0], hout.inputs["Volume"])
    me.materials.append(hm)
    hob = bpy.data.objects.new("TER_TEST_haze", me)
    coll.objects.link(hob)
    hob.visible_shadow = False


# ---- THE ROAD PROGRAMME, AS A CONTRACT PROXY ---------------------------------------
#
# build_terrain must not build ground inside the corridor, so a terrain-only render of
# the verge shows grass floating over a hole.  This builds what world_contract SAYS is
# there -- the racing surface out to verge_edge and the runoff programme out to
# platform_edge, straight off C.ground_z and C.runoff_widths -- so that a test frame
# shows the weld, the banking and the runoff for what they are.
#
# IT IS TEST GEOMETRY.  It lives in TER_TEST, `build()` never creates it, and the real
# thing is build_surface's and build_barriers'.  Its value is that it is generated from
# the contract alone: if terrain and the proxy disagree anywhere, terrain is wrong.

PROXY_BANDS = [   # name, albedo, roughness
    ("track",   (0.062, 0.060, 0.058), 0.62),
    ("kerb",    (0.300, 0.075, 0.062), 0.42),
    ("verge",   (0.072, 0.070, 0.068), 0.60),
    ("runoff",  (0.098, 0.094, 0.090), 0.66),
    ("gravel",  (0.230, 0.205, 0.168), 0.78),
    ("plat",    (0.088, 0.082, 0.062), 0.80),
]


def _proxy_mat(name, rgb, rough):
    m = bpy.data.materials.get(name)
    if m is None:
        m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    co = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 18.0
    nz.inputs["Detail"].default_value = 8.0
    nt.links.new(co.outputs["Object"], nz.inputs[0])
    mx = nt.nodes.new("ShaderNodeMix")
    mx.data_type = 'RGBA'
    nt.links.new(nz.outputs[0], mx.inputs[0])
    mx.inputs[6].default_value = (*rgb, 1.0)
    mx.inputs[7].default_value = (*[min(1.0, v * 1.35) for v in rgb], 1.0)
    p = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(mx.outputs[2], p.inputs["Base Color"])
    p.inputs["Roughness"].default_value = rough
    p.inputs["Specular IOR Level"].default_value = 0.30
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(p.outputs[0], o.inputs["Surface"])
    return m


def build_road_proxy(coll, ds=1.0, nlat=30):
    """The contract's own road surface, meshed.  Test evidence only."""
    for i, (nm, rgb, rough) in enumerate(PROXY_BANDS):
        _proxy_mat("TER_PROXY_" + nm, rgb, rough)
    S = np.arange(0.0, C.LAP, ds)
    ns = len(S)
    X, Y, H, _ = C.centreline_arrays(S)
    e = C.verge_edge(S)
    hw = C.half_width(S)
    cols = []          # (u_signed array, band index array)
    # racing surface + kerb + verge, both sides, in one sweep
    ts = np.linspace(-1.0, 1.0, 2 * nlat + 1)
    for t in ts:
        u = t * e
        a = np.abs(u)
        band = np.where(a <= hw, 0, np.where(a <= hw + C.KERB_W, 1, 2))
        cols.append((u, band))
    # the runoff programme, per side
    for side in (+1, -1):
        lim = C.platform_edge(S, side)
        w = C.runoff_widths(S, side)
        for t in np.linspace(0.0, 1.0, nlat + 1)[1:]:
            u = e + (t ** 0.8) * (lim - e)
            lat = u - e
            band = np.where(lat < w["asphalt"], 3,
                            np.where((lat < w["asphalt"] + w["gravel"]) | (lat < w["apex"]),
                                     4, 5))
            cols.append((u * side, band))
    cols.sort(key=lambda c: np.mean(c[0]))
    nc = len(cols)
    U = np.stack([c[0] for c in cols], 1)                  # (ns, nc)
    BD = np.stack([c[1] for c in cols], 1)
    Z = C.ground_z(np.repeat(S[:, None], nc, 1).ravel(), U.ravel()).reshape(ns, nc)
    PX = (X[:, None] - np.sin(H)[:, None] * U).ravel()
    PY = (Y[:, None] + np.cos(H)[:, None] * U).ravel()
    V = np.stack([PX, PY, Z.ravel()], 1)
    i = np.arange(ns)[:, None] * nc + np.arange(nc - 1)[None, :]
    inext = ((np.arange(ns) + 1) % ns)[:, None] * nc + np.arange(nc - 1)[None, :]
    quads = np.stack([i, inext, inext + 1, i + 1], -1).reshape(-1, 4)
    mats = np.maximum(BD[:, :-1], BD[:, 1:]).reshape(-1)
    me = new_mesh_arrays("TER_PROXY_Road", V, None, quads)
    for nm, _, _ in PROXY_BANDS:
        me.materials.append(bpy.data.materials["TER_PROXY_" + nm])
    me.polygons.foreach_set("material_index", mats.astype(np.int32))
    me.update()
    ob = bpy.data.objects.new("TER_PROXY_Road", me)
    coll.objects.link(ob)
    return ob


# ---- VIEWS --------------------------------------------------------------------------
# (position, look-at, lens[, ground_relative])
VIEWS = dict(_VIEWS_WORLD)

# station-based views: resolved against the CONTRACT, so they land on the datum
# whatever the widths do.  (s, u, height, look_s, look_u, look_height, lens)
# Every one is chosen against the CONTRACT's cross-section, not by eye: each lateral
# offset below is inside `C.runoff_widths`' grass band at that station, or just
# outboard of `C.platform_edge`.
SVIEWS = {
    # T5: grass runs from verge_edge 9.50 out to platform_edge 39.09 with no asphalt
    # and no gravel, so this is the verge the camera really flies down.  Knee height.
    "t5_verge":   (1250.0, +12.5, 1.35, 1362.0, +4.0, 0.85, 34.0),
    # the pit straight, south side: grass 10.50 -> 25.00, barrier pinned at y = -19.
    # This is the strip that was 0.63 m of UNBUILT GROUND before the width fix.
    "pit_verge":  (3300.0, -13.5, 1.30, 3480.0, -9.5, 0.85, 40.0),
    # T10/T11, the 294 km/h banked sweeper, from just OUTSIDE the rim looking back
    # across the whole runoff programme: 55 m of asphalt, 15 m of gravel and the grass
    # shoulder -- 0.387 m of which used to be under TER_Ground.
    "t10_rim":    (2150.0, -92.0, 2.30, 2290.0, -26.0, 0.60, 28.0),
    # T8: the outboard gravel bed ends at 54.0 and grass runs to 62.29.  Gravel edge,
    # the spray dragged out of it, the grass, the rim and the swale in one frame.
    "t8_gravel":  (1792.0, -57.5, 1.25, 1868.0, -46.0, 0.50, 50.0),
    # the T4 hairpin's paved apron at kerb height, looking across the corridor at the
    # NE escarpment falling away
    "t4_apex":    (1000.0, +11.6, 0.85, 1062.0, -22.0, 1.40, 24.0),
    # the doppler station: grass to the verge on both sides, barrier pinned 30 m out
    "doppler_v":  (2560.0, -14.0, 1.50, 2690.0, -6.0, 0.90, 35.0),
    # the esses, from the ridge shoulder, down the corridor
    "esses_rim":  (1700.0, +44.0, 5.0, 1560.0, +12.0, 2.0, 32.0),
}


def _sview(spec):
    s, u, dh, ls, lu, ldh, lens = spec
    p = C.su_to_world(s, u)
    q = C.su_to_world(ls, lu)
    return ((p[0], p[1], p[2] + dh), (q[0], q[1], q[2] + ldh), lens)


def test_scene(view="wide", haze=True, proxy=True):
    sc = bpy.context.scene
    for n in ("TER_TEST",):
        c = bpy.data.collections.get(n)
        if c:
            for o in list(c.objects):
                bpy.data.objects.remove(o, do_unlink=True)
            bpy.data.collections.remove(c)
    c = bpy.data.collections.new("TER_TEST")
    sc.collection.children.link(c)

    if proxy and bpy.data.objects.get("TER_PROXY_Road") is None:
        t0 = time.time()
        build_road_proxy(c)
        log("road proxy from the contract: %.1f s" % (time.time() - t0))
    elif proxy:
        ob = bpy.data.objects["TER_PROXY_Road"]
        if ob.name not in c.objects:
            c.objects.link(ob)

    if view in SVIEWS:
        pos, look, lens = _sview(SVIEWS[view])
        ground_rel = False
    else:
        spec = VIEWS[view]
        pos, look, lens = spec[0], spec[1], spec[2]
        ground_rel = len(spec) > 3 and spec[3]

    cam = bpy.data.cameras.new("TER_TEST_cam")
    cam.lens = lens
    cam.sensor_width = 36.0
    # a new camera clips at 1000 m; Cycles honours that, and build_sky's hand-off asks
    # for >= 50 km because its cloud decks and atmosphere slab are that far out.
    cam.clip_start = 0.05
    cam.clip_end = 60000.0
    co = bpy.data.objects.new("TER_TEST_cam", cam)
    c.objects.link(co)

    sky = _sky_module() if haze else None
    if sky is not None:
        sky.build(sc, camera=co)
        try:
            sky.bind_camera(co)
        except Exception as e:
            log("bind_camera skipped (%s)" % e)
        log("lit by build_sky: sun %.3f W/m2 %s, AgX %.3f"
            % (C.SUN_ENERGY, tuple(round(v, 5) for v in C.SUN_COLOR), EXPOSURE))
    else:
        _fallback_light(c)

    if ground_rel:
        dg = bpy.context.evaluated_depsgraph_get()

        def _ground(p):
            hit, loc, *_ = sc.ray_cast(dg, (p[0], p[1], 900.0), (0.0, 0.0, -1.0))
            return (p[0], p[1], (loc.z if hit else 0.0) + p[2])
        pos, look = _ground(pos), _ground(look)

    co.location = pos
    d = Vector(look) - Vector(pos)
    co.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    sc.camera = co
    return co


def setup_render(sc, samples, res):
    """Cycles settings.  The two volume settings build_sky insists on are set BEFORE
    it runs (it raises them, never lowers them) so its atmosphere is not starved."""
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'GPU'
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 8
    sc.cycles.transmission_bounces = 4
    sc.cycles.transparent_max_bounces = 32     # foliage alpha needs depth
    sc.cycles.volume_step_rate = 4.0
    sc.cycles.volume_max_steps = 1024
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.film_transparent = False
    # THE CONTRACT'S GRADE.  One lens, one grade: AgX, Look = None, exposure
    # C.REFERENCE_EXPOSURE_EXTERIOR.  The old harness ran -2.70 with a Medium Contrast
    # look, which is 0.348 stops and a tone curve away from what the film will use.
    sc.view_settings.view_transform = C.VIEW_TRANSFORM
    sc.view_settings.exposure = EXPOSURE
    try:
        sc.view_settings.look = C.VIEW_LOOK
    except TypeError:
        pass
    log("grade: %s look=%s exposure %.3f  (contract %.3f %+0.3f measured airlight)"
        % (C.VIEW_TRANSFORM, C.VIEW_LOOK, EXPOSURE, EXPOSURE_CONTRACT,
           EXPOSURE_AIRLIGHT_STOPS))


def render(path, view="wide", res=(1920, 1080), samples=48, haze=True, proxy=True):
    sc = bpy.context.scene
    setup_render(sc, samples, res)
    test_scene(view, haze=haze, proxy=proxy)
    setup_render(sc, samples, res)             # build_sky may raise volume settings
    try:
        prefs = bpy.context.preferences.addons['cycles'].preferences
        prefs.compute_device_type = 'CUDA'
        prefs.get_devices()
        for d in prefs.devices:
            d.use = (d.type == 'CUDA')
    except Exception as e:
        log("GPU setup failed (%s), falling back to CPU" % e)
        sc.cycles.device = 'CPU'
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    log("wrote %s" % path)


# ---- THE MACRO PROBE ----------------------------------------------------------------
#
# A full build is ~10 minutes and a 1 GB blend, which is the wrong iteration loop for a
# question that is decided in a 400 x 300 pixel crop: "is an individual blade of grass
# resolvable at the distance the doppler hover actually puts the lens?"
#
# So this builds ONE 280 m window of the lap -- the real `verge_band`, the real
# `gen_grass`, the real materials, the real `build_sky`, the contract's own road proxy
# -- and nothing else.  It is a 40 MB blend that renders in a couple of minutes.  It
# is deliberately built out of the SAME functions the full build calls, with a station
# window passed down, because a probe that reimplements the placement is evidence
# about the probe.

def _probe_gz(gr, x0, x1, y0, y1, step=5.0):
    """A GridZ over the probe window, sampled ONCE off Ground.height.

    It has to be a grid and not a direct call.  `Ground.height` includes the corridor
    batter, so it calls `corridor_fz`, which is the O(points x 3675 stations) exact
    union field: fine for the 640 k vertices of one build, ruinous for the ~540 k band
    samples x 3 (the slope finite difference) x 3 passes the probe asks for.  The real
    build has exactly the same property and solves it the same way -- `build()` hands
    the scatter a `GridZ` off the BUILT mesh, never `Ground.height`.  Measured: direct
    calls did not finish the first band in 4 minutes; the grid takes 12 s.
    """
    xs = np.arange(x0, x1 + step, step)
    ys = np.arange(y0, y1 + step, step)
    GX, GY = np.meshgrid(xs, ys, indexing="ij")
    Z = gr.height(GX.ravel(), GY.ravel()).reshape(GX.shape)
    return GridZ(xs, ys, Z)


def macro_probe(view="doppler", half=140.0, q=1.0, grit=True):
    """Build the vegetation macro test: one window of verge, at full production density."""
    t0 = time.time()
    purge()
    spec = json.load(open(SPEC_JSON))
    beats = json.load(open(BEAT_JSON))
    cir = Circuit(spec)
    gr = Ground(cir)
    cam = CameraPath(cir, beats)
    rng = np.random.default_rng(SEED)
    root = bpy.data.collections.new(COLL)
    bpy.context.scene.collection.children.link(root)
    c_grass = _sub(root, "Grass")
    c_weeds = _sub(root, "WeedsStones")
    build_materials()

    # where the camera is, in stations
    if view in SVIEWS:
        pos, look, lens = _sview(SVIEWS[view])
    else:
        sp = VIEWS[view]
        pos, look, lens = sp[0], sp[1], sp[2]
    s0, _ = C.project(np.array([pos[0]]), np.array([pos[1]]))
    s0 = float(s0[0])
    swin = (max(0.0, s0 - half), min(C.LAP - 1.0, s0 + half))
    log("macro probe: view %s, station %.1f, window %.0f..%.0f"
        % (view, s0, swin[0], swin[1]))

    X0 = min(pos[0], look[0]) - 260.0; X1 = max(pos[0], look[0]) + 260.0
    Y0 = min(pos[1], look[1]) - 260.0; Y1 = max(pos[1], look[1]) + 260.0
    gz = _probe_gz(gr, X0, X1, Y0, Y1, 5.0)
    ras = Raster(gr, cam, X0, X1, Y0, Y1, 14.0, gz=gz)
    log("  raster + height grid %.1f s" % (time.time() - t0))

    nlib = max(3, int(round(9 * q)))
    stats = {}
    stats.update(build_grass(cir, gr, gz, cam, c_grass, rng, q, ras, swin=swin,
                             meadow=False, nlib=nlib))
    lib = {}
    for key in WEED_ORDER:
        lib[("weed_" + key, 0)] = [
            gen_weed(key, np.random.default_rng(int(rng.integers(1 << 31))))
            for _ in range(max(3, nlib // 2))]
    for key in STONES:
        lib[("stone_" + key, 0)] = [
            gen_stone(key, np.random.default_rng(int(rng.integers(1 << 31))))
            for _ in range(max(4, nlib // 2))]
    for gkey, gmat in (("clod", VPFX + "clod"), ("gritstone", VPFX + "gritstone")):
        lib[(gkey, 0)] = [
            gen_grit_piece(np.random.default_rng(int(rng.integers(1 << 31))), gmat)
            for _ in range(max(10, nlib))]
    stats.update(build_weeds_and_stones(cir, gr, gz, cam, c_weeds, lib, rng, q, ras,
                                        swin=swin, field=False))
    if grit:
        stats.update(build_grit(cir, gr, gz, cam, c_weeds, lib, rng, q, ras, swin=swin))
    log("macro probe built in %.1f s: %s" % (time.time() - t0, json.dumps(stats)))
    return stats


# ==================================================================================
# 12.  VERIFICATION AGAINST THE CONTRACT
# ==================================================================================
#
# The single lesson of the assembly review is that six agents each verified their own
# work in isolation.  So every check below is against world_contract, not against this
# module's own assumptions, and every one of them is a number.

def selftest(nsamp=200000, seed=7):
    """Measure the built terrain against the contract.  -> dict of numbers."""
    rng = np.random.default_rng(seed)
    out = {}
    ob = bpy.data.objects.get(PFX + "Ground")
    if ob is None:
        return {"error": "TER_Ground not built"}
    me = ob.data
    V = np.empty(len(me.vertices) * 3, np.float32)
    me.vertices.foreach_get("co", V)
    V = V.reshape(-1, 3).astype(np.float64)
    out["ground_verts"] = int(len(V))
    out["ground_polys"] = int(len(me.polygons))

    # 1.  NO VERTEX INSIDE THE ROAD CORRIDOR.  This is finding #1, as a single number.
    f = corridor_field(V[:, 0], V[:, 1])
    out["min_corridor_field_mm"] = round(float(f.min()) * 1000.0, 4)
    out["verts_inside_corridor_1mm"] = int((f < -1e-3).sum())
    out["verts_in_contract_mask"] = int(
        (C.road_corridor_mask(V[:, 0], V[:, 1]) & (f > 1e-6)).sum())

    # 2.  THE WELD, measured against the CONTRACT'S OWN RIM rather than against this
    #     module's idea of it: take C.corridor_rim_polyline every 4 m, drop a ray on
    #     TER_Ground, and compare the hit with the rim's published z.
    dgw = bpy.context.evaluated_depsgraph_get()
    obw = ob.evaluated_get(dgw)
    mww = ob.matrix_world.inverted()
    dz = []
    miss = 0
    other = 0
    OFF = 0.10                                 # sample just OUTBOARD of the rim so the
    for side in (+1, -1):                      # ray is unambiguously in terrain's
        Sr = np.arange(0.0, C.LAP, 4.0)        # half-space, not on the boundary edge
        E = C.platform_edge(Sr, side) + OFF
        P = C.su_to_world(Sr, E * side)
        ok = ~C.in_access_ribbon(P[:, 0], P[:, 1], margin=12.0)
        ff = corridor_field(P[:, 0], P[:, 1])
        # a rim point can legitimately fall inside ANOTHER branch's corridor where two
        # parts of the loop pass close; the road programme paves it from there, and
        # terrain leaving a hole is correct, not a gap
        other += int((ff[ok] < 0.0).sum())
        ok &= ff >= 0.0
        # ... and from v1.1.1 a rim point can also fall inside the DECLARED z = 0
        # platform, which `cut_field` now cuts out of TER_Ground (defect #50).
        # build_architecture paves it; terrain leaving a hole there is the fix, not
        # a gap, so those samples are counted separately rather than as misses.
        pf = np.asarray(C.platform_field(P[:, 0], P[:, 1]), float)
        other += int((pf[ok] < 0.0).sum())
        ok &= pf >= 0.0
        for k in np.where(ok)[0]:
            px, py, pz = float(P[k, 0]), float(P[k, 1]), float(P[k, 2])
            hit, loc, *_ = obw.ray_cast(mww @ Vector((px, py, pz + 40.0)),
                                        Vector((0.0, 0.0, -1.0)), distance=120.0)
            if hit:
                dz.append(float((ob.matrix_world @ loc).z) - pz)
            else:
                miss += 1
    dz = np.array(dz)
    out["rim_samples"] = int(len(dz))
    out["rim_no_terrain"] = int(miss)
    out["rim_owned_by_other_branch"] = other
    if len(dz):
        out["weld_max_mm"] = round(float(np.abs(dz).max() * 1000.0), 3)
        out["weld_p99_mm"] = round(float(np.percentile(np.abs(dz), 99) * 1000.0), 3)
        out["weld_rms_mm"] = round(float(np.sqrt((dz ** 2).mean()) * 1000.0), 3)
        out["weld_within_TOL_SEAM"] = bool(np.abs(dz).max() <= C.TOL_SEAM_M)

    # 3.  NOTHING PROUD OF THE ROAD.  Sample the racing surface and the runoff and ask
    #     the built mesh what is above it, by ray-cast against TER_Ground only.
    S = rng.random(nsamp) * C.LAP
    side = np.where(rng.random(nsamp) < 0.5, 1.0, -1.0)
    t = rng.random(nsamp)
    lim = np.where(side > 0, C.platform_edge(S, +1), C.platform_edge(S, -1))
    U = side * t * lim
    P = C.su_to_world(S, U)
    dg = bpy.context.evaluated_depsgraph_get()
    obe = ob.evaluated_get(dg)
    mw = ob.matrix_world.inverted()
    above = 0
    worst = 0.0
    worst_at = None
    step = max(1, nsamp // 4000)               # ray-casting is the expensive part
    n_ray = 0
    for k in range(0, nsamp, step):
        o = mw @ Vector((float(P[k, 0]), float(P[k, 1]), float(P[k, 2]) + 60.0))
        hit, loc, *_ = obe.ray_cast(o, Vector((0.0, 0.0, -1.0)), distance=200.0)
        n_ray += 1
        if hit:
            dz = float((ob.matrix_world @ loc).z) - float(P[k, 2])
            if dz > 0.0:
                above += 1
                if dz > worst:
                    worst = dz
                    worst_at = (float(S[k]), float(U[k]))
    out["road_rays"] = n_ray
    out["terrain_above_road_pct"] = round(100.0 * above / max(n_ray, 1), 4)
    out["terrain_above_road_worst_m"] = round(worst, 4)
    out["terrain_above_road_worst_at_su"] = worst_at

    # 4.  WIDTHS.  This module no longer has its own; assert that.
    out["half_width_3115"] = float(C.half_width(3115.0))
    out["half_width_250"] = float(C.half_width(250.0))

    # 4b. THE HORIZON.  Two numbers, and the second is the one that matters.
    #
    #     `horizon_min_elev_deg` walks the BUILT MESH outward from beat 6's own
    #     hold — docs/beat_sheet.json beat 6, world (594.19, 16.05, 140.0) — on 48
    #     bearings and takes the largest elevation angle the ground reaches on
    #     each. If the smallest of those is not POSITIVE, some bearing has sky
    #     where it should have land, and Blender's Nishita sky returns black below
    #     the horizon, so that bearing renders as a void. Measured before this
    #     module grew a far field: -0.13 deg on 48 of 48 bearings.
    #
    #     `horizon_intrusion_m` is the negative control, and it is the reason the
    #     first number is allowed to be large: the SAME far-field term, sampled
    #     everywhere within HORIZON_RISE_M of the centreline, must be identically
    #     zero. A range that lifts the horizon by lifting the circuit would score
    #     just as well on the first number and would be a catastrophe.
    cam6 = np.array([594.19, 16.05, 140.0])
    D2 = np.hypot(V[:, 0] - cam6[0], V[:, 1] - cam6[1])
    B2 = np.degrees(np.arctan2(V[:, 1] - cam6[1], V[:, 0] - cam6[0])) % 360.0
    EL = np.degrees(np.arctan2(V[:, 2] - cam6[2], np.maximum(D2, 1.0)))
    far = D2 > 2000.0                          # the skyline is a far-field fact
    nb = 48
    sect = np.floor(B2 / (360.0 / nb)).astype(int)
    best = np.full(nb, -90.0)
    for k in range(nb):
        m = far & (sect == k)
        if m.any():
            best[k] = float(EL[m].max())
    out["horizon_min_elev_deg"] = round(float(best.min()), 4)
    out["horizon_max_elev_deg"] = round(float(best.max()), 4)
    out["horizon_bearings_below_zero"] = int((best <= 0.0).sum())
    _f, _zr, _s, _u, _lim, Dc_v = corridor_fz(V[:, 0], V[:, 1])
    near = Dc_v < HORIZON_RISE_M
    hz_near = far_horizon(V[near][:, 0], V[near][:, 1], Dc_v[near])
    out["horizon_intrusion_m"] = round(float(np.abs(hz_near).max()), 9)
    out["horizon_verts_within_rise"] = int(near.sum())

    # 5.  VEGETATION.  How much of it is inside the corridor, and is any of it in a
    #     gravel trap or on runoff asphalt?
    bad = 0
    tot = 0
    ins = 0
    root = bpy.data.collections.get(COLL)
    plants = []
    if root is not None:
        for ch in root.children:               # ONLY what is linked into the scene:
            plants.extend(ch.objects)          # the *_lib groups are not, and they sit
    for o in plants:                           # at the origin, which is in the ribbon
        if not o.name.startswith(VPFX):        # TER_Ground is not a plant
            continue
        if o.type != 'MESH' or not len(o.data.vertices):
            continue
        if o.modifiers:                        # a gn_kind point cloud
            Pv = np.empty(len(o.data.vertices) * 3, np.float32)
            o.data.vertices.foreach_get("co", Pv)
            Pv = Pv.reshape(-1, 3).astype(np.float64)
        else:
            Pv = np.array([[o.location.x, o.location.y, o.location.z]])
        tot += len(Pv)
        # the NEAREST branch, as C.world_ground_z uses, not the union's deepest quad:
        # "which cross-section am I standing in" is a question about the branch that
        # is actually there
        sp, up = C.project(Pv[:, 0], Pv[:, 1])
        limp = np.where(up >= 0.0, C.platform_edge(sp, +1), C.platform_edge(sp, -1))
        inside = np.abs(up) <= limp
        ins += int(inside.sum())
        if inside.any():
            s2, u2 = sp[inside], up[inside]
            e2 = C.verge_edge(s2)
            lat = np.abs(u2) - e2
            wA = np.where(u2 >= 0, C.runoff_widths(s2, +1)["asphalt"],
                          C.runoff_widths(s2, -1)["asphalt"])
            wG = np.where(u2 >= 0, C.runoff_widths(s2, +1)["gravel"],
                          C.runoff_widths(s2, -1)["gravel"])
            wX = np.where(u2 >= 0, C.runoff_widths(s2, +1)["apex"],
                          C.runoff_widths(s2, -1)["apex"])
            bad += int(((lat < 0.0) | (lat < wA + wG) | (lat < wX)).sum())
    out["plants_total"] = tot
    out["plants_in_corridor"] = ins
    out["plants_on_runoff_or_gravel"] = bad

    out["contract_version"] = C.__version__
    log("selftest: %s" % json.dumps(out, default=str))
    return out


def probe_albedo(res=(320, 240), samples=64):
    """Render four known patches and compare to C.lambert_radiance.

    The check that says whether the ground material is calibrated to the light that
    actually ships.  Renders LINEAR (view transform Standard, exposure 0) into an EXR
    and reads the pixels back, so nothing is guessed from a tone-mapped PNG.

    The patches sit at z = 0.60 m and the camera 40 m above them, i.e. IN the boundary
    layer where the film's surfaces actually are.  A first version put them at 400 m
    with a 60 m stand-off and read 1.44x lambert_radiance, most of which was the
    atmosphere between the patch and the lens.
    """
    sc = bpy.context.scene
    for n in ("TER_PROBE",):
        c = bpy.data.collections.get(n)
        if c:
            for o in list(c.objects):
                bpy.data.objects.remove(o, do_unlink=True)
            bpy.data.collections.remove(c)
    c = bpy.data.collections.new("TER_PROBE")
    sc.collection.children.link(c)
    patches = [("grey018", (0.18, 0.18, 0.18)), ("turf", GA_GRN),
               ("dryg", GA_DRYG), ("scree", GA_STONE)]
    for i, (nm, rgb) in enumerate(patches):
        me = bpy.data.meshes.new("TER_PROBE_" + nm)
        e = 6.0
        x0 = -30.0 + i * 20.0
        me.from_pydata([(x0 - e, -e, 0.60), (x0 + e, -e, 0.60),
                        (x0 + e, e, 0.60), (x0 - e, e, 0.60)], [], [(0, 1, 2, 3)])
        me.update()
        m = bpy.data.materials.new("TER_PROBE_" + nm)
        m.use_nodes = True
        nt = m.node_tree
        nt.nodes.clear()
        p = nt.nodes.new("ShaderNodeBsdfDiffuse")
        p.inputs["Color"].default_value = (*rgb, 1.0)
        o = nt.nodes.new("ShaderNodeOutputMaterial")
        nt.links.new(p.outputs[0], o.inputs["Surface"])
        me.materials.append(m)
        ob = bpy.data.objects.new("TER_PROBE_" + nm, me)
        c.objects.link(ob)
    cam = bpy.data.cameras.new("TER_PROBE_cam")
    cam.type = 'ORTHO'; cam.ortho_scale = 90.0
    cam.clip_start = 1.0; cam.clip_end = 60000.0
    co = bpy.data.objects.new("TER_PROBE_cam", cam)
    c.objects.link(co)
    co.location = (5.0, 0.0, 40.6)
    co.rotation_euler = (0.0, 0.0, 0.0)
    sc.camera = co
    sky = _sky_module()
    if sky is not None:
        sky.build(sc, camera=co)
    else:
        _fallback_light(c)
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'GPU'
    sc.cycles.samples = samples
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.view_settings.view_transform = 'Standard'
    sc.view_settings.exposure = 0.0
    sc.render.image_settings.file_format = 'OPEN_EXR'
    sc.render.image_settings.color_depth = '32'
    path = os.path.join(_tmpdir(), "ter_probe.exr")
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(path)
    W, H = img.size
    px = np.array(img.pixels[:]).reshape(H, W, 4)
    out = {}
    for i, (nm, rgb) in enumerate(patches):
        # patch i is centred at world x = -30 + 20 i, camera at x = 5, ortho 90 wide
        cx = int(round((( -30.0 + i * 20.0) - 5.0) / 90.0 * W + W * 0.5))
        band = px[H // 2 - 12:H // 2 + 12, max(0, cx - 12):cx + 12, :3]
        meas = band.reshape(-1, 3).mean(0)
        want = np.array(C.lambert_radiance(rgb))
        out[nm] = dict(measured=[round(float(v), 4) for v in meas],
                       lambert=[round(float(v), 4) for v in want],
                       ratio=[round(float(a / b), 4) for a, b in zip(meas, want)])
    bpy.data.images.remove(img)
    sc.render.image_settings.file_format = 'PNG'
    log("albedo probe: %s" % json.dumps(out))
    return out


def _tmpdir():
    d = os.environ.get("TER_TMP", "/var/tmp/terrain_work")
    os.makedirs(d, exist_ok=True)
    return d


def bake_cameras(names):
    """Leave a FEW named cameras in the scene, lit by build_sky, for tools/r5090."""
    sc = bpy.context.scene
    test_scene(names[0])                      # builds the light, the proxy and cam 0
    made = []
    for o in list(bpy.data.objects):           # KEEP IT FEW: the worker prewarms every
        if o.type == 'CAMERA' and not o.name.startswith("CAM_"):
            bpy.data.objects.remove(o, do_unlink=True)   # camera at load
    for nm in names:
        if nm in SVIEWS:
            pos, look, lens = _sview(SVIEWS[nm])
        else:
            spec = VIEWS[nm]
            pos, look, lens = spec[0], spec[1], spec[2]
            if len(spec) > 3 and spec[3]:
                dg = bpy.context.evaluated_depsgraph_get()

                def _g(p):
                    hit, loc, *_ = sc.ray_cast(dg, (p[0], p[1], 900.0), (0, 0, -1.0))
                    return (p[0], p[1], (loc.z if hit else 0.0) + p[2])
                pos, look = _g(pos), _g(look)
        cd = bpy.data.cameras.new("CAM_" + nm)
        cd.lens = lens; cd.sensor_width = 36.0
        cd.clip_start = 0.05; cd.clip_end = 60000.0
        ob = bpy.data.objects.new("CAM_" + nm, cd)
        bpy.data.collections["TER_TEST"].objects.link(ob)
        ob.location = pos
        d = Vector(look) - Vector(pos)
        ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        made.append("CAM_" + nm)
    setup_render(sc, 512, (3840, 2160))
    sc.camera = bpy.data.objects[made[0]]
    log("baked cameras: %s" % made)
    return made


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if "--load" in argv:
        # test-render an already-built .blend instead of rebuilding.
        bpy.ops.wm.open_mainfile(filepath=argv[argv.index("--load") + 1])
        stats = {"loaded": argv[argv.index("--load") + 1]}
    elif "--macro" in argv:
        # the vegetation macro probe: ONE window of verge at production density, so a
        # blade-level question gets a two-minute loop instead of a ten-minute one.
        v = argv[argv.index("--macro") + 1] if len(argv) > argv.index("--macro") + 1 \
            and not argv[argv.index("--macro") + 1].startswith("--") else "doppler"
        hw = float(argv[argv.index("--half") + 1]) if "--half" in argv else 140.0
        stats = macro_probe(view=v, half=hw, grit="--nogrit" not in argv)
    else:
        stats = build()
    if "--probe" in argv:
        stats["albedo_probe"] = probe_albedo()
    if "--render" in argv:
        out = argv[argv.index("--render") + 1]
        views = argv[argv.index("--views") + 1].split(",") if "--views" in argv else ["wide"]
        res = (1920, 1080)
        if "--res" in argv:
            res = tuple(int(v) for v in argv[argv.index("--res") + 1].split("x"))
        smp = int(argv[argv.index("--samples") + 1]) if "--samples" in argv else 48
        haze = "--nohaze" not in argv
        proxy = "--noproxy" not in argv
        for v in views:
            render(os.path.join(out, "terrain_%s.png" % v), v, res, smp,
                   haze=haze, proxy=proxy)
    if "--selftest" in argv:
        stats["selftest"] = selftest()
    if "--cams" in argv:
        # bake a few named cameras into the saved blend for tools/r5090.  KEEP IT FEW:
        # the worker prewarms every camera at load and 19 of them blew the readiness
        # probe.  Lighting comes from build_sky, exactly as in `render`.
        names = argv[argv.index("--cams") + 1].split(",")
        stats["cams"] = bake_cameras(names)
    if "--save" in argv:
        bpy.ops.wm.save_as_mainfile(filepath=argv[argv.index("--save") + 1])
    print(json.dumps(stats, indent=1))


if __name__ == "__main__":
    main()


