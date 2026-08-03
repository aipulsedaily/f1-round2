"""
build_barriers.py — Circuit Vitrine safety furniture AND the runoff platform.

Owns, for the whole 3675 m lap and the showroom->circuit transit corridor:

    * steel W-beam (Armco) barrier runs      * three-layer TecPro impact barriers
    * precast concrete barrier / pit wall    * 3.6 m debris (catch) fencing
    * gravel traps                           * tarmac runoff aprons
    * tyre walls (T4 infield + apron gate)   * marshal openings and terminals
    * THE RUNOFF PLATFORM — every square metre of ground from `verge_edge(s)`
      out to `platform_edge(s, side)`, both sides, the whole lap.  build_terrain
      cuts a hole here and welds to `corridor_rim`; nothing else builds ground
      inside it.

CONTRACT
--------
This module is subordinate to `world_contract.py`.  It imports the datum, the
widths, the runoff programme and the Beat-4 corridor extents from there and
re-derives NONE of them.  In particular:

    ground_z(s, u)      is world_contract.ground_z.  u is SIGNED, + = LEFT of
                        travel.  The module's old ground_z had neither crown nor
                        banking and was up to 0.691 m out at the verge edge,
                        which sank 90.1 % of the barrier line and buried the
                        entire runoff programme.  Every call site here now passes
                        `side`, which is what makes banking reach the runoff.
    half_width          world_contract.half_width  (spec S9, linear over 60 m,
                        transition OUTSIDE the named section)
    verge_edge          world_contract.verge_edge
    barrier_offset      world_contract.barrier_offset
    platform_edge       world_contract.platform_edge
    SEAM_DROP           RETIRED.  It claimed to absorb 15 mm of datum
                        disagreement against a measured 0.69 m.  There is no
                        datum disagreement any more: there is one function.

Read `build_barriers.md` beside this file for the variation strategy, and
`WORLD_CONTRACT.md` for why each shared number went the way it did.

Run headless:
    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup -P build_barriers.py
    ... -P build_barriers.py -- --render doppler       # build + test render
    ... -P build_barriers.py -- --list-renders

`build()` is idempotent: it wipes and rebuilds everything under the
`R2_Barriers` collection and every datablock whose name starts with `BR_`.

NOTHING here is instanced from a shared master mesh.  Every rail panel, post,
TecPro block, concrete block, fence span, tyre and pebble is generated with its
own vertex data from a deterministic per-unit parameter draw.  See
`HISTORY MODEL` below.
"""

import bpy
import bmesh  # noqa: F401  (kept: used by optional debug paths)
import json
import math
import os
import sys
import time

import numpy as np
from mathutils import Vector, Matrix  # noqa: F401

# ----------------------------------------------------------------------------
# 0.  paths + spec
# ----------------------------------------------------------------------------

HERE = os.path.dirname(os.path.abspath(__file__ if "__file__" in dir() else "."))
ROOT = os.path.dirname(HERE)
DOCS = os.path.join(ROOT, "docs")
SPEC_JSON = os.path.join(DOCS, "circuit_spec.json")
RENDER_DIR = os.path.join(ROOT, "render", "world", "barriers")

# THE CONTRACT.  Imported, never reimplemented.  `WC` and not `C` because this
# module already uses `C` as a local name for swept polylines.
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import world_contract as WC        # noqa: E402

ROOT_COLL = "R2_Barriers"
PFX = "BR_"                      # every datablock we own starts with this

with open(SPEC_JSON, "r") as _f:
    SPEC = json.load(_f)

DATUM = SPEC["datum"]["circuit_design_frame"]
ROT_DEG = float(DATUM["rotation_deg_about_z"])
PIVOT_D = np.array(DATUM["pivot_design"], dtype=np.float64)
PIVOT_W = np.array(DATUM["pivot_world"], dtype=np.float64)
LAP_LEN = float(SPEC["headline"]["length_m"])

SUN_DIR = np.array(SPEC["sun"]["direction_to_sun"], dtype=np.float64)

# ----------------------------------------------------------------------------
# 1.  deterministic hashing / noise  (no global RNG state anywhere)
# ----------------------------------------------------------------------------

_U32 = np.uint32


def hash01(*keys):
    """FNV-1a over integer key arrays -> float64 in [0,1). Broadcasts."""
    h = np.zeros(np.broadcast(*[np.asarray(k) for k in keys]).shape
                 if len(keys) > 1 else np.shape(keys[0]), dtype=np.uint32)
    h[...] = _U32(2166136261)
    with np.errstate(over="ignore"):
        for k in keys:
            kk = np.asarray(k)
            kk = np.rint(kk).astype(np.int64) if kk.dtype.kind == "f" else kk.astype(np.int64)
            kk = (kk & 0xFFFFFFFF).astype(np.uint32)
            h = (h ^ kk) * _U32(16777619)
            h = h ^ (h >> _U32(13))
            h = h * _U32(2654435761)
            h = h ^ (h >> _U32(16))
    return (h & _U32(0xFFFFFF)).astype(np.float64) / 16777215.0


def h01(*keys):
    """scalar convenience"""
    return float(hash01(*[np.array([k]) for k in keys])[0])


def _smooth(t):
    return t * t * (3.0 - 2.0 * t)


def vnoise1(x, seed=0):
    x = np.asarray(x, dtype=np.float64)
    i = np.floor(x).astype(np.int64)
    f = x - i
    a = hash01(i, np.full_like(i, seed))
    b = hash01(i + 1, np.full_like(i, seed))
    u = _smooth(f)
    return a * (1.0 - u) + b * u


def fbm1(x, seed=0, oct=4, lac=2.03, gain=0.5):
    x = np.asarray(x, dtype=np.float64)
    tot = np.zeros_like(x)
    amp, frq, nrm = 1.0, 1.0, 0.0
    for o in range(oct):
        tot += amp * vnoise1(x * frq, seed * 131 + o * 17)
        nrm += amp
        amp *= gain
        frq *= lac
    return tot / nrm


def vnoise2(x, y, seed=0):
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    ix = np.floor(x).astype(np.int64)
    iy = np.floor(y).astype(np.int64)
    fx, fy = _smooth(x - ix), _smooth(y - iy)
    s = np.full(np.broadcast(ix, iy).shape, seed, dtype=np.int64)
    c00 = hash01(ix, iy, s)
    c10 = hash01(ix + 1, iy, s)
    c01 = hash01(ix, iy + 1, s)
    c11 = hash01(ix + 1, iy + 1, s)
    return (c00 * (1 - fx) + c10 * fx) * (1 - fy) + (c01 * (1 - fx) + c11 * fx) * fy


def fbm2(x, y, seed=0, oct=4, lac=2.07, gain=0.5):
    tot = np.zeros(np.broadcast(np.asarray(x), np.asarray(y)).shape, dtype=np.float64)
    amp, frq, nrm = 1.0, 1.0, 0.0
    for o in range(oct):
        tot += amp * vnoise2(np.asarray(x) * frq, np.asarray(y) * frq, seed * 977 + o * 31)
        nrm += amp
        amp *= gain
        frq *= lac
    return tot / nrm


def worley2(x, y, seed=0, jitter=0.85):
    """Return (F1 distance, feature-cell hash) on a unit lattice."""
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    ix = np.floor(x).astype(np.int64)
    iy = np.floor(y).astype(np.int64)
    best = np.full(x.shape, 1e9)
    bid = np.zeros(x.shape)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            cx, cy = ix + dx, iy + dy
            s = np.full(cx.shape, seed, dtype=np.int64)
            hx = hash01(cx, cy, s)
            hy = hash01(cx, cy, s + 7717)
            hid = hash01(cx, cy, s + 3313)
            px = cx + 0.5 + (hx - 0.5) * jitter
            py = cy + 0.5 + (hy - 0.5) * jitter
            d = np.hypot(x - px, y - py)
            m = d < best
            best = np.where(m, d, best)
            bid = np.where(m, hid, bid)
    return best, bid


def packed_spheres(x, y, seed=0, radius=0.62, jitter=0.95):
    """Dome field: height of overlapping spheres.  Reads as packed gravel."""
    d, cid = worley2(x, y, seed, jitter)
    r = radius * (0.55 + 0.75 * cid)
    hgt = np.sqrt(np.maximum(0.0, r * r - d * d))
    return hgt, cid


def clamp01(a):
    return np.clip(a, 0.0, 1.0)


def _trapz(y, x):
    """Trapezoidal integral.  np.trapz was renamed in numpy 2 and Blender's
    bundled numpy version is not something this module gets to pick."""
    y = np.asarray(y, float)
    x = np.asarray(x, float)
    return float(np.sum(0.5 * (y[1:] + y[:-1]) * np.diff(x)))


def smoothstep(e0, e1, x):
    t = clamp01((np.asarray(x, dtype=np.float64) - e0) / max(1e-9, (e1 - e0)))
    return t * t * (3.0 - 2.0 * t)


def lerp(a, b, t):
    return a + (b - a) * t


# ----------------------------------------------------------------------------
# 2.  centreline  —  a DESIGN-FRAME view of the contract centreline
# ----------------------------------------------------------------------------
#
# The module's geometry is authored in the circuit ("design") frame and pushed to
# world by `W3` at emit time, so this class stays; but every number in it now
# comes from `world_contract`, evaluated ANALYTICALLY rather than off a 0.25 m
# lookup table.  The old sampled version quantised every station to 0.25 m, which
# put up to 125 mm of longitudinal jitter into anything not on a 0.25 m station.

class Centre:

    def __init__(self):
        a = math.radians(ROT_DEG)
        self._c, self._s2 = math.cos(a), math.sin(a)
        self.L = LAP_LEN
        self._hrot = a

    # -- sampling ----------------------------------------------------------
    def at(self, s):
        """design-frame x, y, heading, curvature, z, cross-slope at station(s).

        The last element is always 0: the old class carried a per-corner banking
        angle here and `point()` applied it by hand, which is precisely the
        duplicated cross-slope the contract abolished.  `ground_z(s, u, side)`
        carries banking now, and carries it out into the runoff.  The slot is
        kept so the tuple shape (and every unpacking of it) is unchanged.
        """
        S = np.asarray(s, dtype=np.float64) % LAP_LEN
        X, Y, H, K = WC.centreline_arrays(S)
        dx, dy = WC.world_to_circuit(X, Y)
        return dx, dy, H - self._hrot, K, WC.elevation_c(S), np.zeros_like(S)

    def normal(self, s, side):
        """unit lateral in design frame. side=+1 -> left of travel, -1 -> right."""
        _, _, h, _, _, _ = self.at(s)
        return side * -np.sin(h), side * np.cos(h)

    def point(self, s, lat, side=+1, dz=0.0, bank=False):
        """design-frame 3-D point `lat` metres to `side` of the centreline.

        The z it returns is the CENTRELINE elevation, not the ground: every
        caller in this module discards it and takes z from `ground_z(s, lat,
        side)` instead, which is the only datum there is.
        """
        x, y, h, k, z, _ = self.at(s)
        nx, ny = side * -np.sin(h), side * np.cos(h)
        zz = z + dz
        if bank:
            zz = WC.ground_z(s, lat, side) + dz
        return x + nx * lat, y + ny * lat, zz

    def to_world(self, x, y, z=None):
        dx = np.asarray(x) - PIVOT_D[0]
        dy = np.asarray(y) - PIVOT_D[1]
        wx = self._c * dx - self._s2 * dy + PIVOT_W[0]
        wy = self._s2 * dx + self._c * dy + PIVOT_W[1]
        return (wx, wy) if z is None else (wx, wy, np.asarray(z))

    def to_design(self, wx, wy):
        dx = np.asarray(wx) - PIVOT_W[0]
        dy = np.asarray(wy) - PIVOT_W[1]
        return (self._c * dx + self._s2 * dy + PIVOT_D[0],
                -self._s2 * dx + self._c * dy + PIVOT_D[1])


CL = Centre()

# ----------------------------------------------------------------------------
# 3.  track section, kerb, verge  —  ALL FROM THE CONTRACT (spec §9)
# ----------------------------------------------------------------------------
#
# `build_barriers` had the only correct `half_width` of the five builders, which
# is exactly why it must not keep its own copy: the contract is now where the
# right answer lives, and this module has to move when it moves.
#
# SEAM_DROP and EDGE_PAD are RETIRED.  They existed to hide a datum
# disagreement that has been eliminated.  What replaces them is a hidden
# vertical-then-inward flange under `build_surface`'s painted verge, which
# closes tessellation-chord slivers WITHOUT putting two surfaces coplanar:
# see PLATFORM_TUCK / PLATFORM_TUCK_Z in §11.

KERB_W = WC.KERB_W               # 1.50
VERGE_W = WC.VERGE_W             # 1.00
half_width = WC.half_width
verge_edge = WC.verge_edge

# ----------------------------------------------------------------------------
# 4.  runoff programme  —  ALSO FROM THE CONTRACT
# ----------------------------------------------------------------------------
#
# side convention:  +1 = LEFT of travel,  -1 = RIGHT of travel.
# a corner with turn_deg > 0 turns left, so its OUTSIDE is the right side.
#
# The contract's `_Corridor` is a verbatim port of the class that used to live
# here, plus the two smoothed indicator fields (`wallw`, `apronw`) that
# `platform_edge` and the apron tie need.  `barrier_offset` is therefore
# numerically identical to the barrier line this module already built — the fix
# is that it is now DERIVED from the contract's `half_width`, so a width change
# moves the runoff, the verge, the boards, the barrier line, the terrain hole and
# the dressing standoff together.

PS, NS, SGRID = WC.PS, WC.NS, WC.SGRID
B_ARMCO, B_TECPRO3, B_CONCRETE, B_NONE = (WC.B_ARMCO, WC.B_TECPRO3,
                                          WC.B_CONCRETE, WC.B_NONE)
RUNOFF_ZONES = WC.RUNOFF_ZONES
APEX_BEDS = WC.APEX_BEDS


class _CorridorView:
    """The contract's corridor programme, wearing this module's old interface.

    `build_dressing` reads `BR.COR.get("btype"|"fence"|"zone_cap", s, side)` and
    `BR.COR.barrier_offset(s, side)`.  Deleting the `Corridor` class outright
    would have broken it silently at import — which is precisely the class of
    failure this whole migration exists to stop — so the old two methods are
    kept, delegating to `world_contract._Corridor.sample`.

    `barrier_offset` deliberately routes through §4b's ownership clamp, so every
    consumer of the barrier line gets the corrected one without having to know
    the clamp exists.  Everything else (`.asph`, `.grav`, `.apex`, `.btype`,
    `.fence`, `.zone_cap`, `.sample`) passes straight through.
    """

    def __init__(self, cor):
        self._c = cor

    def __getattr__(self, k):
        return getattr(self._c, k)

    def get(self, name, s, side):
        return self.sample(name, s, side)

    def sample(self, name, s, side):
        v = self._c.sample(name, s, side)
        # THE VETO (S4c-veto, S4b-steps).  Where the barrier line runs through
        # the Beat-4 access ribbon there is no barrier and no fence, because
        # there is a ROAD there; and where the contract's line steps, no barrier
        # is laid across the jump.  Applied HERE rather than at each of the four
        # call sites, so build_armco / build_tecpro / build_concrete /
        # build_fence cannot each forget it independently.
        #
        # NOTE, and it is handed back: `build_dressing` reads
        # `world_contract.COR.sample(...)`, NOT this view, so it does NOT get
        # the veto.  It must call `build_barriers.barrier_blocked(s, side)` (or
        # read `BR.COR`) before it stands anything on the barrier line, or it
        # will put marshal posts and tyre stacks in the pit-exit road.
        if name == "btype":
            return np.where(barrier_blocked(s, side), B_NONE, v)
        if name == "fence":
            return v & ~barrier_blocked(s, side)
        return v

    def barrier_offset(self, s, side):
        return barrier_offset(s, side)


COR = _CorridorView(WC.COR)      # .asph / .grav / .apex / .btype / .fence / ...


def cor_get(name, s, side):
    """Station-sample one of the corridor programme fields."""
    return COR.sample(name, s, side)


def platform_edge(s, side):
    """Centreline -> outboard limit of the ground THIS MODULE builds (m)."""
    return WC.platform_edge(s, side)


# ============================================================================
#  4b.  CORRIDOR SELF-INTERSECTION  —  a contract defect, measured and clamped
# ============================================================================
#
# THE CIRCUIT CROSSES ITS OWN CORRIDOR.  `world_contract.barrier_offset` is
# `verge_edge + max(runoff, 4) + margin`, clamped only by the inside-of-a-corner
# radius rule.  Nothing in it knows another LEG OF THE TRACK might be in the
# way, and on this layout one is:
#
#   spec §9 gives T3 (turn_deg -28, a right-hander, so its OUTSIDE is side +1) a
#   40 m asphalt + 15 m gravel runoff.  T3 is a 140 m-radius kink, so the
#   inside-corner clamp never bites, and `barrier_offset(s, +1)` comes out at
#   66.9 m for the whole of T3 and S3.  But S4 (the hairpin exit ramp) and T5
#   run back past that side 51-67 m away and 5-7 m higher.  MEASURED, with the
#   contract's own `project` and `world_ground_z`:
#
#     s      barrier_offset    nearest station there    world ground - barrier
#     700.0      66.88            700.0 (itself)                 0.000 m
#     753.0      66.83           1225.4  u +15.34               +6.740 m
#     800.0      66.94           1166.9  u  -1.13               +5.203 m  <- it
#                                       (owner SURF_Track)         is UNDER the
#     900.0      66.97           1067.2  u  -8.14               +1.579 m  racing
#                                                                        surface
#
#   So the declared barrier line for s ~700..1100 on the left runs under the
#   S4/T5 racing surface, and the runoff platform that goes with it would be a
#   second ground plane 5-7 m below a piece of circuit that already has one.
#   14.1 % of the left corridor's stations, 4.5 % of the whole corridor's area
#   (10 752 m2).
#
# `road_corridor_mask` already resolves this correctly — it asks `project`,
# which returns the NEAREST centreline, so the mask is the union of the two
# branches and terrain cuts exactly that.  `barrier_offset` does not.  So this
# module resolves it BY THE CONTRACT'S OWN RULE and publishes the result:
#
#     owned_edge(s, side)      how far out this station's corridor reaches
#                              before another branch is nearer
#     barrier_offset(s, side)  the contract's line, capped at owned_edge - margin
#                              and slope-limited so the cap cannot put a kink in
#                              a barrier line
#
# ANY MODULE THAT NEEDS THE BARRIER LINE THROUGH THIS STRETCH MUST READ
# `build_barriers.barrier_offset`, NOT `world_contract.barrier_offset`, until
# the contract adopts the clamp — build_dressing above all.  This is a
# divergence from the contract, it is deliberate, and it is named rather than
# silent: `barrier_clamp_report()` prints exactly how much and where.
#
# ---------------------------------------------------------------------------
# THE ASSEMBLY REVIEW'S DEFECT #1, AND WHY THE FIRST VERSION OF THIS SECTION
# WAS WORSE THAN THE PROBLEM IT SOLVED
# ---------------------------------------------------------------------------
#
# The first version smoothed the DEFICIT `max(0, bo - avail)` over +-13 m of
# dilation and +-24 m of box filter and then subtracted it from `bo`:
#
#       line = min(bo - box(dilate(deficit)), avail)
#
# That is only meaningful while `bo` is continuous.  It is not.  MEASURED, on
# the contract's own 1 m grid, side +1:
#
#       s = 900   barrier_offset =  66.970      (verge_edge + 40 m asphalt +
#       s = 904   barrier_offset =  65.988       15 m gravel + margin)
#       s = 905   barrier_offset =  14.000      <- 51.99 m IN ONE METRE
#
# because `_Corridor.maxoff` box-filters an inside-corner cap that is 1e6
# outside the corner and 14.0 (= 0.50 R, R = 28 m at the T4 hairpin) inside it,
# so the filtered cap falls off a cliff at the station where the last 1e6
# leaves the 41-sample window.  The deficit at s <= 904 is ~43 m; the +-37 m
# influence window carried it forward onto stations where `bo` had already
# dropped to 14.0, and 14.0 - 32.8 = -18.8.  NEGATIVE.  A barrier face at
# u = -18.80 on side +1 is 18.8 m PAST THE CENTRELINE, and what got built was
# BR_Armco_L03 / L04 and BR_FenceStruct_L03 / L04 lying across the T4 braking
# zone: 982 of 4 147 sampled vertices inside `verge_edge`, s 904.4-937.2,
# u -9.79..+9.93, mean 1.41 m and max 4.60 m above the tarmac.
#
# THE REPLACEMENT, and the three properties it is built to have:
#
#   target(s) = min(bo, avail)              the hard answer: the contract's line
#                                           where we own the ground, the ground
#                                           we own where we do not.
#   soft(s)   = verge_edge + cone_erode(target - verge_edge, BARRIER_TAPER_MAX)
#                                           the same line, slope-limited IN
#                                           CLEARANCE-ABOVE-THE-VERGE, which is
#                                           the quantity that must never go to
#                                           zero.
#   line(s)   = lerp(target, soft, w)       blended in ONLY where the ownership
#                                           cap actually bites (`w`), so every
#                                           station the cap never touched keeps
#                                           the contract's number bit for bit.
#
#   1.  IT CANNOT REACH THE TRACK, AND THAT IS A PROOF, NOT A CLAMP.
#       `cone_erode(c, R)(s) = min_j (c(j) + R|s-j|) >= min_j c(j)`, and
#       `min_j c(j) = min_j (target - verge_edge) >= 1.000 m` — the pit wall
#       (spec S10.7, circuit y = +11.5 against a verge edge at 10.5) is the
#       tightest clearance the CONTRACT declares anywhere on the lap, and
#       `avail >= verge_edge + 4.0` by construction.  A convex combination of
#       two fields that are both >= verge_edge + 1.0 is >= verge_edge + 1.0.
#       So `barrier_offset(s, side) - verge_edge(s) >= 1.000` for every station
#       on both sides, whatever the contract does upstream.  Verified over the
#       whole 3675 m grid in `barrier_clamp_report()`.
#
#   2.  IT IS BUILDABLE.  `|d(offset)/ds| <= BARRIER_TAPER_MAX` inside the
#       blended stretch: a 1 : 3.3 barrier taper, which is what a circuit
#       actually builds where a runoff collapses into a hairpin apron.  The T4
#       entry now runs 25.0 m out at s = 860 to 14.0 m at s = 905 instead of
#       falling off a 52 m cliff.
#
#   3.  IT IS A NO-OP EVERYWHERE THE CAP DOES NOT BITE.  `deficit == 0` for
#       every station on side -1 and for 86 % of side +1, so `w == 0` there and
#       `line == target == bo`.  Global smoothing was measured and rejected:
#       eroding the whole lap at 0.25 m/m moves the RIGHT-hand barrier line in
#       by a mean of 4.49 m, because the contract's runoff ramps legitimately
#       shed 45 m of lateral over 55 m of station and a global slope limit
#       cannot tell those from the cliffs.

# ---------------------------------------------------------------------------
# PROMOTED INTO THE CONTRACT, world_contract 1.2.0, R2-035.
#
# Everything below this line was written HERE because the contract did not have a
# notion of which leg owns a patch of ground.  It does now (`world_contract` S9b),
# and it runs THIS SOLVE, unchanged — same 2.0 m station step, same 65 laterals,
# same 2.0 m / 0.25 m self tolerances, same 0.75 m medial-axis bias, same taper,
# same blend.  So `owned_edge` here is the contract's, by delegation and not by
# coincidence (RULE 1: that distinction is exactly what DEFECT 4 was).
#
# THE CLAMP IN `_build_barrier_line` BELOW IS KEPT, AND IT IS NOW A NO-OP.
# MEASURED after the promotion: `barrier_clamp_report()` reports 0.0000 of the lap
# clamped on BOTH sides and `exact_vs_contract_frac` 1.0000 — the contract's line
# already satisfies `line <= avail` by construction, so `hit` is empty and
# `line == target == bo` at every station.  It stays because it is also the
# ASSERTION that no barrier this module builds can be inside build_surface's own
# mesh, and an assertion that has become cheap is not a reason to delete it: if a
# future contract revision reopens the defect, this raises at import instead of
# building an Armco wall across the T4 braking zone again.  `barrier_clamp_report`
# is the thing to read to know which of the two it is doing.
_CAP_DS = WC.OWNED_SOLVE_DS_M       # 2.0   station step for the ownership solve
_CAP_NT = WC.OWNED_SOLVE_NT         # 65    lateral samples per station
CORRIDOR_BIAS = WC.CORRIDOR_BIAS_M  # 0.75  over-reach at the medial axis
RUNOFF_STANDOFF = 1.5               # clear ground between runoff and barrier
BARRIER_TAPER_MAX = WC.BARRIER_TAPER_MAX_RATE   # 0.30 m/m, 1 : 3.3
CLAMP_BLEND_M = WC.OWNERSHIP_BLEND_M            # 60.0
BARRIER_MIN_CLEAR_M = WC.BARRIER_MIN_CLEAR_M    # 1.00, asserted, never clamped


def owned_edge(s, side):
    """Outboard limit of the ground this station's corridor owns, in metres.

    `world_contract.owned_edge`.  Kept as a name because eleven call sites in this
    module and its S4c coverage solve read it.
    """
    return WC.owned_edge(s, side)


def _box(a, half):
    """Cyclic box smooth over +-`half` samples of the 1 m station grid."""
    k = np.ones(2 * half + 1) / (2 * half + 1)
    pad = np.concatenate([a[-half:], a, a[:half]])
    return np.convolve(pad, k, mode="same")[half:-half]


def _cone_erode(c, rate, ds=PS, laps=2):
    """Cyclic erosion by a cone:  out(s) = min_j ( c(j) + rate*|s - j| ).

    The result is <= c everywhere, is `rate`-Lipschitz, and — the property this
    whole section turns on — is never less than `min(c)`.  Two forward and two
    backward sweeps are enough to close the cycle for any `rate > 0`.
    """
    step = float(rate) * float(ds)
    e = np.asarray(c, float).copy()
    n = e.size
    for _ in range(laps):
        for i in range(n):
            v = e[i - 1] + step
            if v < e[i]:
                e[i] = v
    for _ in range(laps):
        for i in range(n - 1, -1, -1):
            v = e[(i + 1) % n] + step
            if v < e[i]:
                e[i] = v
    return e


def _build_barrier_line():
    out, diag = {}, {}
    for side in (+1, -1):
        e = verge_edge(SGRID)
        oe = owned_edge(SGRID, side)
        wall = COR.sample("wallw", SGRID, side)
        marg = (WC.PLATFORM_MARGIN_M
                + (WC.PLATFORM_MARGIN_WALL_M - WC.PLATFORM_MARGIN_M) * wall)
        # what this station's own corridor can actually carry a barrier on.
        # never tighter than verge_edge + 4.0, so `avail` can never be the thing
        # that pushes a barrier towards the track.
        avail = np.maximum(e + 4.0, oe - marg)
        bo = WC.barrier_offset(SGRID, side)

        target = np.minimum(bo, avail)                 # the hard answer
        soft = e + _cone_erode(target - e, BARRIER_TAPER_MAX)   # slope-limited

        # WHERE the cap bites, dilated by CLAMP_BLEND_M so the taper has room to
        # run into and out of the capped stretch.  Zero everywhere else, which
        # is what keeps the rest of the lap bit-identical to the contract.
        hit = (bo - avail) > 1e-9
        k = int(round(CLAMP_BLEND_M / PS))
        w = hit.astype(np.float64)
        for sh in range(1, k + 1):
            w = np.maximum(w, np.maximum(np.roll(hit, sh), np.roll(hit, -sh)))
        w = _box(w, max(1, k // 3))
        w = np.clip(w * 1.25, 0.0, 1.0)
        w = w * w * (3.0 - 2.0 * w)

        line = target * (1.0 - w) + soft * w
        line = np.minimum(line, avail)                 # ownership always wins
        out[side] = line
        diag[side] = dict(bo=bo, avail=avail, target=target, w=w, e=e)

        # THE INVARIANT, asserted at import: nothing this module builds can be
        # inside build_surface's own mesh.
        clr = line - e
        if float(clr.min()) < BARRIER_MIN_CLEAR_M - 1e-6:
            raise AssertionError(
                "barrier line inside verge_edge + %.3f on side %+d: "
                "min clearance %.4f m at s = %.1f"
                % (BARRIER_MIN_CLEAR_M, side, float(clr.min()),
                   float(SGRID[int(clr.argmin())])))
    return out, diag


_BLINE, _BDIAG = _build_barrier_line()


def barrier_offset(s, side):
    """Centreline -> barrier FACE (m).  The contract's, capped to `owned_edge`.

    Guaranteed `>= verge_edge(s) + BARRIER_MIN_CLEAR_M` for every station on
    both sides — see S4b, and `barrier_clamp_report()['invariant']`.
    """
    return np.interp(np.asarray(s, float) % LAP_LEN, SGRID, _BLINE[side],
                     period=LAP_LEN)


def barrier_clamp_report():
    """How far this module's barrier line departs from the contract's, and where."""
    r = {}
    for side in (+1, -1):
        d = WC.barrier_offset(SGRID, side) - _BLINE[side]
        m = d > 0.05
        clr = _BLINE[side] - _BDIAG[side]["e"]
        slope = np.abs(np.diff(np.concatenate([_BLINE[side], _BLINE[side][:1]])))
        r["L" if side > 0 else "R"] = dict(
            frac_of_lap=round(float(m.mean()), 4),
            max_clamp_m=round(float(d.max()), 3),
            mean_where_clamped=round(float(d[m].mean()) if m.any() else 0.0, 3),
            min_clearance_m=round(float(clr.min()), 4),
            min_clearance_s=round(float(SGRID[int(clr.argmin())]), 1),
            stations_inside_verge=int((clr < 0.0).sum()),
            max_lateral_rate=round(float(slope.max()), 4),
            exact_vs_contract_frac=round(float((d <= 1e-9).mean()), 4),
            ranges=[(round(a), round(b)) for (a, b) in _contig(m, minlen=8.0)])
    r["invariant"] = ("offset - verge_edge >= %.3f m, both sides, all %d stations"
                      % (BARRIER_MIN_CLEAR_M, NS))
    return r


# ============================================================================
#  4c.  THE GROUND THE PLATFORM ACTUALLY LAYS  —  assembly defect #4
# ============================================================================
#
# THE VOID.  `build_terrain` cuts the union of every station's quad out to
# `C.platform_edge` — deliberately a SUPERSET of `road_corridor_mask`, so that
# terrain "can never build ground the road programme also builds".  S4b clamped
# this module's platform to `owned_edge` — deliberately a SUBSET, so that a
# runoff platform is never laid 5-7 m under another leg of the same circuit.
# Two conservative decisions in opposite directions, and between them
#
#       658 m2 OF THE ROAD CORRIDOR HAD NO GROUND AT ALL.
#
# (assembly probe `void`, 2 m x 1 m grid, verge_edge -> platform_edge, both
# sides; worst at T3 s 702-746 at up to 38 m2 per 2 m station.)
#
# The resolution is NOT "build to platform_edge everywhere".  MEASURED over the
# whole clamped stretch (s 700-1212, side +1, 20 247 samples at 1 m x 0.5 m):
#
#     68.6 % of the annulus (owned_edge, platform_edge] is already covered by
#            ANOTHER station of this same module's platform;
#     of those, the covering ground is a MEDIAN 1.75 m ABOVE ours for s <= 914
#            — buried, invisible — but up to 5.44 m BELOW ours for s >= 1050,
#            where an extension would be a shelf hanging over open ground;
#     31.4 % is covered by nobody, and every one of those samples lies in
#            s 701-922.
#
# So the reach is extended to `platform_edge` exactly where the annulus is
# void AND the extension is provably buried:
#
#     platform_reach(s, side) = platform_edge   where `_fill`
#                             = owned_edge      elsewhere
#
#     _fill = (this station's annulus contains ground no other station lays)
#           AND (every covered sample in it is >= PLATFORM_FILL_CLEAR below the
#                station that covers it)
#
# ramped over PLATFORM_FILL_RAMP_M so the rim never steps.  The test is the
# exact swept-segment one — a point is covered iff it lies inside some station's
# quad {|along| <= ds/2 (1 + |u| kappa), verge_edge <= |u| <= owned_edge} — the
# same formulation `build_terrain.union_field` cuts with, so the two answers are
# about the same region and not about two different approximations of it.
#
# THE INNER EDGE, and a coplanar overlap the review did not reach.  The access
# ribbon's outboard gore runs INSIDE the pit-straight platform band for 119 m:
# at s = 3440 the ribbon covers u 10.52-12.32 of a 10.50-13.54 band (61 % of
# it), tapering to nothing by s = 3549.  MEASURED: 314 m2 of the declared band,
# ~60 m2 of it inside the stations this module actually paves, coplanar with
# `SURF_AccessRoad` on the same `ground_z` — a stroboscopic z-fight in the
# merge that Beat 4 is built around.  `world_ground_z` puts the ribbon above the
# runoff platform in its priority order, so the platform is the one that moves:
# `platform_inner` cuts the band's inboard edge to the ribbon's outboard edge,
# and the hidden verge flange is not laid where there is no painted verge to hide
# under.  CUT, DO NOT OFFSET.
#
# ...AND CUTTING IS NOT THE SAME AS STANDING BACK.  DEFECT #47, v1.1.1.  Until
# v1.1.0 this cut used `ACCESS_RIBBON_SAW_M` = 0.30 m, found the ribbon's edge by
# sweeping u in 0.10 m steps, and took the last sample INSIDE — so the band's
# inboard edge landed 0.30-0.40 m outboard of a road that stops dead.  MEASURED on
# the assembled world at 0.50 x 0.10 m, 26 901 samples over the pit exit:
#
#     SURF_AccessRoad | BR_Verge_L    22.95 m2   170 runs   lips 8-22 mm apart in z
#                                     0.20-0.30 m wide, u 11.0-11.2, s 3455-3560
#
# — the single largest piece of the 42.00 m2 of unbuilt ground the fine map found,
# and it is this stand-off, exactly.  `ACCESS_RIBBON_SAW_M` IS PAVING'S JOINT: its
# contract docstring says it exists so build_architecture's PRECAST SLAB and
# build_surface's sawn edge meet at a joint instead of interpenetrating.  This
# module lays hot asphalt on the same `ground_z`; there is nothing to saw, so it
# BUTTS, and a butt joint on a shared datum is exact and not toleranced.
#
# The edge comes from `C.ribbon_edge_u(s, "out")` now — published once, to 1 mm,
# by the same module that publishes the ribbon — instead of from a 0.10 m sweep
# each consumer runs for itself.  RULE 1.

PLATFORM_FILL_CLEAR = 0.10     # how far below the covering station's ground an
                               # extension must sit before it may be laid
PLATFORM_FILL_RAMP_M = 12.0    # station ramp from owned_edge out to platform_edge
RIBBON_SAW_M = WC.ACCESS_RIBBON_SAW_M    # 0.30 — the contract's paving joint
_FILL_DU = 0.5                 # lateral probe step for the coverage solve
FILL_SKIN_M = 2.0              # ignore the first 2 m outboard of owned_edge in
                               # the clearance test — that is the medial axis,
                               # where the two branches meet by construction
# THE BREAK TEST, AND IT WAS DEAD.  This was a private 2.0 against the contract's
# `BARRIER_MAX_LATERAL_RATE` = 1.95, and it is used as a STRICT `>` — so on a line
# the contract guarantees is 1.95-Lipschitz BY CONSTRUCTION (`_cone_erode` at
# exactly that rate) the test could never fire, whatever the corridor did.  A
# detector that cannot fire is not a detector; it is R2-012 wearing a threshold.
# RULE 1: it is the contract's number, and the contract's own [12] gate asserts
# the line against the same one, so the bound and the construction stay welded.
BARRIER_BREAK_RATE = WC.BARRIER_BREAK_RATE   # 1.95 + 1e-6 m of lateral per m of
                               # station beyond which the declared line is a
                               # JUMP, not a barrier line.  The epsilon is NOT
                               # slack: at a flat 1.95 this strict `>` fires on
                               # float round-off (measured 1.9500000000000028 on
                               # side -1) and blanks 17 m of Armco.


def _runs(mask):
    """Contiguous True index ranges [(i0, i1), ...] of a station-indexed mask."""
    out, i, n = [], 0, len(mask)
    while i < n:
        if not mask[i]:
            i += 1
            continue
        j = i
        while j < n and mask[j]:
            j += 1
        out.append((i, j))
        i = j
    return out


def _seg_cover(px, py, reach, exclude_s=None, ds=PS, chunk=96):
    """For each (px, py): is it inside some station's swept platform segment?

    -> (covered, s_owner, u_owner) where the owner is the covering station with
    the SMALLEST |u| — the one whose ground is naturally on top.  `reach` is the
    per-station, per-side outboard limit dict used for the segments.
    """
    G = SGRID
    X, Y, H, K = WC.centreline_arrays(G)
    CH, SH, KA = np.cos(H), np.sin(H), np.abs(K)
    E = verge_edge(G)
    n = px.size
    best = np.full(n, np.inf)
    so = np.zeros(n)
    uo = np.zeros(n)
    for a in range(0, G.size, chunk):
        b = min(G.size, a + chunk)
        dx = px[:, None] - X[None, a:b]
        dy = py[:, None] - Y[None, a:b]
        al = dx * CH[None, a:b] + dy * SH[None, a:b]
        u = -dx * SH[None, a:b] + dy * CH[None, a:b]
        au = np.abs(u)
        lim = np.where(u >= 0.0, reach[+1][None, a:b], reach[-1][None, a:b])
        ok = ((np.abs(al) <= 0.5 * ds * (1.0 + au * KA[None, a:b]))
              & (au >= E[None, a:b] - 1e-3) & (au <= lim))
        if exclude_s is not None:
            ok &= (np.abs(((G[None, a:b] - exclude_s[:, None] + LAP_LEN * 0.5)
                           % LAP_LEN) - LAP_LEN * 0.5) > 3.0)
        cand = np.where(ok, au, np.inf)
        j = np.argmin(cand, axis=1)
        v = cand[np.arange(n), j]
        take = v < best
        best[take] = v[take]
        so[take] = G[a:b][j[take]]
        uo[take] = u[np.arange(n), j][take]
    return np.isfinite(best), so, uo


def _build_reach():
    """Per-station outboard limit of the ground THIS MODULE lays."""
    base = {s: owned_edge(SGRID, s) for s in (+1, -1)}
    pe = {s: platform_edge(SGRID, s) for s in (+1, -1)}
    out, rep = {}, {}
    for side in (+1, -1):
        oe, pf = base[side], pe[side]
        gap = pf - oe
        idx = np.where(gap > 0.10)[0]
        fill = np.zeros(NS, bool)
        ok = np.ones(NS, bool)
        if idx.size:
            SS, UU = [], []
            for i in idx:
                U = np.arange(oe[i] + 0.25, pf[i] + 1e-9, _FILL_DU)
                if U.size == 0:
                    continue
                SS.append(np.full(U.shape, SGRID[i]))
                UU.append(U)
            SS = np.concatenate(SS)
            UU = np.concatenate(UU)
            X, Y, H, _ = WC.centreline_arrays(SS)
            PX = X - np.sin(H) * UU * side
            PY = Y + np.cos(H) * UU * side
            cov, so, uo = _seg_cover(PX, PY, base, exclude_s=SS)
            zmine = WC.ground_z(SS, UU * side)
            zoth = np.where(cov, WC.ground_z(so, uo), np.inf)
            bi = np.rint(SS / PS).astype(np.int64) % NS
            void = np.zeros(NS, bool)
            np.logical_or.at(void, bi, ~cov)
            # The clearance test SKIPS the first FILL_SKIN_M of the annulus.  At
            # u = owned_edge the two branches meet AT THE MEDIAL AXIS: the same
            # world point reached through two different (s, u), so they differ
            # by millimetres there by construction and always will.  That is the
            # rim this module already builds, not a hazard.  Including it
            # rejected s 916-922 on a 6 mm "clearance" and left 32 m2 of the
            # void open.
            skin = (UU - oe[bi]) >= FILL_SKIN_M
            clr = np.full(NS, np.inf)
            sel = cov & skin
            np.minimum.at(clr, bi[sel], (zoth - zmine)[sel])
            ok = clr >= PLATFORM_FILL_CLEAR
            fill = void & ok
            # close 1-2 station pinholes so the rim does not chatter
            for sh in (1, 2):
                fill |= (np.roll(fill, sh) & np.roll(fill, -sh) & ok)
        k = int(round(PLATFORM_FILL_RAMP_M / PS))
        w = fill.astype(np.float64)
        for sh in range(1, k + 1):
            w = np.maximum(w, np.maximum(np.roll(fill, sh), np.roll(fill, -sh)))
        w = _box(w * ok, max(1, k // 2))
        w = np.clip(w * 1.6, 0.0, 1.0)
        w = w * w * (3.0 - 2.0 * w)
        out[side] = oe + (pf - oe) * w
        rep["L" if side > 0 else "R"] = dict(
            stations_filled=int(fill.sum()),
            stations_capped=int((gap > 0.10).sum()),
            extra_area_m2=round(float(_trapz(out[side] - oe, SGRID)), 1),
            ranges=[(round(float(SGRID[a])), round(float(SGRID[b - 1])))
                    for (a, b) in _runs(fill)])
    return out, rep


_REACH, _REACH_REPORT = _build_reach()


def platform_reach(s, side):
    """Outboard limit of the ground this module lays, in metres.  See S4c."""
    return np.interp(np.asarray(s, float) % LAP_LEN, SGRID, _REACH[side],
                     period=LAP_LEN)


def _build_ribbon_fields():
    """Per-station: how far out the Beat-4 access ribbon reaches into the
    platform band, and whether a barrier may stand on the barrier line."""
    inner, block, steps = {}, {}, {}
    for side in (+1, -1):
        e = verge_edge(SGRID)
        pf = platform_edge(SGRID, side)
        X, Y, H, _ = WC.centreline_arrays(SGRID)
        # cheap pre-filter: only stations whose band can reach the route at all
        near = np.zeros(NS, bool)
        for frac in (0.0, 0.5, 1.0):
            U = (e + (pf - e) * frac) * side
            t, v = WC.access_project(X - np.sin(H) * U, Y + np.cos(H) * U)
            near |= ((t > -20.0) & (t < WC.ACCESS_TOTAL + 20.0)
                     & (np.abs(v) < WC.ACCESS_HALF_W + 30.0))
        ri = e.copy()
        # v1.1.1: the contract's own published edge, at 1 mm, on the LEFT of travel
        # where the ribbon runs.  BUTT, do not stand off — see the block above.
        # The ribbon runs on the LEFT of travel only, so on side -1 the answer is
        # `verge_edge` and there is nothing to sweep.  The 0.10 m sweep below is
        # kept ONLY as a fallback for a builder pinned to a pre-1.1.1 contract; do
        # not tighten its step, it is O(stations x laterals x 981) and at 0.01 m it
        # took the barriers build from 60 s to over 8 minutes.
        if hasattr(WC, "ribbon_edge_u"):
            if side > 0:
                ru = np.asarray(WC.ribbon_edge_u(SGRID, "out"), float)
                has = np.isfinite(ru)
                ri[has] = np.maximum(ru[has], e[has])
        else:
            for i in np.where(near)[0]:
                U = np.arange(e[i], pf[i] + 1e-9, 0.10)
                if U.size == 0:
                    continue
                px = X[i] - math.sin(H[i]) * U * side
                py = Y[i] + math.cos(H[i]) * U * side
                m = WC.in_access_ribbon(px, py)
                if m.any():
                    ri[i] = max(float(U[m].max()), e[i])
        inner[side] = np.minimum(ri, pf)

        # THE BARRIER VETO.  A concrete block straddles the declared face by
        # 0.265 m inboard (CB_T/2 + batter), so the test covers the body, not
        # just the line.
        bo = _BLINE[side]
        blk = np.zeros(NS, bool)
        for du in (-0.32, 0.0, 0.45):
            U = (bo + du) * side
            blk |= WC.in_access_ribbon(X - np.sin(H) * U, Y + np.cos(H) * U,
                                       margin=0.15)
        for sh in (1, 2, 3):          # 3 m of clearance either end of the veto
            blk |= np.roll(blk, sh) | np.roll(blk, -sh)

        # THE STEP BREAKS.  `_Corridor._build` applies the pit-straight
        # overrides, the runoff table and the inside-corner cap as HARD boolean
        # masks on a 1 m station grid, so the declared line has genuine
        # discontinuities: MEASURED, side -1, s = 250 -> 251 is 21.19 -> 67.50,
        # 46.31 m OF LATERAL IN ONE METRE OF STATION.  `barrier_nodes` walks
        # that as arclength, its straightening pass finds eleven consecutive
        # nodes on one heading, and what gets built is 46 m of three-beam Armco
        # and 3.6 m debris fence running ACROSS the T1 runoff at 89 degrees —
        # in front of CAM_T1_RUNOFF.
        #
        # It is NOT smoothed.  Slope-limiting a 46 m outward step at 0.30 m/m
        # holds the barrier 20-45 m inboard of the declared line for 150 m, and
        # `_build_programme` scales the runoff to fit inside the barrier, so it
        # would halve T1's declared 45 m asphalt + 12 m gravel to fix a barrier.
        # A step is not a barrier line, it is TWO barrier lines: the run ends
        # and another begins further out, which is what a circuit builds where a
        # runoff opens.  So no barrier is laid across the jump.  Five places,
        # 24 m of lap in total.
        drate = np.abs(np.diff(np.concatenate([bo, bo[:1]]))) / PS
        stepm = np.zeros(NS, bool)
        stepm[:-1] |= drate[:-1] > BARRIER_BREAK_RATE
        stepm[1:] |= drate[:-1] > BARRIER_BREAK_RATE
        stepm[0] |= drate[-1] > BARRIER_BREAK_RATE
        stepm[-1] |= drate[-1] > BARRIER_BREAK_RATE
        for sh in (1,):
            stepm |= np.roll(stepm, sh) | np.roll(stepm, -sh)
        block[side] = blk | stepm
        steps[side] = stepm
    return inner, block, steps


_RIB_INNER, _RIB_BLOCK, _STEP_BREAK = _build_ribbon_fields()


def platform_inner(s, side):
    """Inboard edge of the ground this module lays.

    `verge_edge(s)` everywhere except where the Beat-4 access ribbon runs over
    the platform band, where it is the ribbon's outboard edge plus the
    contract's paving joint.  build_surface owns the ribbon; we cut to it.
    """
    return np.interp(np.asarray(s, float) % LAP_LEN, SGRID, _RIB_INNER[side],
                     period=LAP_LEN)


def barrier_blocked(s, side):
    """True where no barrier of any kind may stand: the barrier line runs
    through the Beat-4 access ribbon, i.e. through the road the car drives.

    MEASURED on the shipped build: `BR_Concrete_L13` — the pit wall, spec S10.7
    at circuit y = +11.5 — stood 0.36-1.01 m above the pit-exit road over route
    t = 126-140 (world x 135.9-146.4, y 22.3-31.1).  The wall is not wrong; it
    simply cannot start before the pit exit has merged.  A real pit wall starts
    at the merge point, which is what this makes it do.
    """
    x = np.asarray(s, float) % LAP_LEN
    i = np.rint(x / PS).astype(np.int64) % NS
    return _RIB_BLOCK[side][i]


def _built_mask(side):
    """1.0 on the stations `build_platform` actually lays ground on."""
    m = np.zeros(NS)
    for (a, b) in _platform_runs(side):
        m[(SGRID >= a) & (SGRID < b)] = 1.0
    return m


def ribbon_report():
    r = {}
    for side in (+1, -1):
        tag = "L" if side > 0 else "R"
        blk = _RIB_BLOCK[side]
        cut = _RIB_INNER[side] - verge_edge(SGRID)
        r[tag] = dict(
            barrier_veto_ranges=[(round(float(SGRID[a])), round(float(SGRID[b - 1])))
                                 for (a, b) in _runs(blk)],
            barrier_veto_m=int(blk.sum()),
            step_break_ranges=[(round(float(SGRID[a])), round(float(SGRID[b - 1])),
                                round(float(np.abs(np.diff(_BLINE[side]))[
                                    max(a - 1, 0):b].max()), 1))
                               for (a, b) in _runs(_STEP_BREAK[side])],
            step_break_m=int(_STEP_BREAK[side].sum()),
            platform_cut_stations=int((cut > 1e-6).sum()),
            platform_cut_max_m=round(float(cut.max()), 3),
            platform_cut_area_m2=round(float(_trapz(cut, SGRID)), 1),
            # ...and how much of that is inside the stations this module
            # actually paves (the rest is the pit-exit apron, which is
            # build_architecture's ground and is skipped anyway).
            platform_cut_area_built_m2=round(float(_trapz(
                cut * _built_mask(side), SGRID)), 1))
    return r


# ----------------------------------------------------------------------------
# 5.  HISTORY MODEL — where the variation actually comes from
# ----------------------------------------------------------------------------
#
# Three independent fields, all functions of station, all deterministic:
#
#   AGE       piecewise-constant per maintenance RUN (25..220 m).  Drives
#             galvanise brightness, rust coverage, TecPro UV fade, bolt
#             corrosion, concrete staining.  Sharp resets at run boundaries
#             put a bright new section against a twenty-year-old one, which is
#             the single most legible anti-repetition cue on a barrier line.
#   ALIGN     smooth lateral wander + per-run step, and vertical settlement.
#   INCIDENTS discrete crash sites, sampled from a crash-probability field
#             built from the corner table, each with a kind, an extent, an
#             epoch (how long ago) and a fictional livery colour.

CRASH_W = {1: 1.00, 2: 0.25, 3: 0.75, 4: 0.95, 5: 0.40, 6: 0.30, 7: 0.30, 8: 0.85,
           9: 0.30, 10: 0.55, 11: 0.60, 12: 1.00, 13: 0.25, 14: 0.30, 15: 0.60}

# fictional test-car liveries — no real teams.  index 0 approximates our own car.
LIVERY = [
    (0.055, 0.135, 0.150), (0.640, 0.090, 0.070), (0.070, 0.180, 0.520),
    (0.880, 0.560, 0.040), (0.780, 0.780, 0.800), (0.100, 0.330, 0.170),
    (0.560, 0.110, 0.360), (0.930, 0.900, 0.250), (0.180, 0.180, 0.200),
]


def crash_field():
    s = SGRID
    w = np.full(NS, 0.045)
    for c in SPEC["corners"]:
        if not c["is_numbered_corner"]:
            continue
        i = c["index"]
        sa = c["s_apex"]
        cw = CRASH_W.get(i, 0.3)
        # braking approach (long, upstream) and exit (short, downstream)
        du = ((s - sa + LAP_LEN * 0.5) % LAP_LEN) - LAP_LEN * 0.5
        w += cw * 1.05 * np.exp(-0.5 * ((du + 55.0) / 62.0) ** 2)
        w += cw * 0.85 * np.exp(-0.5 * ((du - 45.0) / 48.0) ** 2)
    return w


class History:
    def __init__(self):
        self.runs = {}
        self.age = {}
        self.rid = {}
        for side in (+1, -1):
            self.runs[side], self.age[side] = self._runs(side)
            arr = np.zeros(NS)
            for i, (a, b, _ag) in enumerate(self.runs[side]):
                arr[(SGRID >= a) & (SGRID < b)] = i + 1 + (0 if side > 0 else 500)
            self.rid[side] = arr
        self.inc = self._incidents()

    def run_id_field(self, side):
        return self.rid[side]

    def _runs(self, side):
        """maintenance runs: (s_start, s_end, age) covering the lap."""
        seed = 5100 + (side > 0) * 37
        runs, s = [], 0.0
        sector_age = fbm1(np.arange(0, LAP_LEN, 50.0) / 640.0, seed=seed + 3)
        k = 0
        while s < LAP_LEN:
            u = h01(seed, k, 11)
            L = 25.0 + 195.0 * (u ** 1.7)
            e = min(LAP_LEN, s + L)
            sa = float(np.interp(s, np.arange(0, LAP_LEN, 50.0), sector_age))
            v = h01(seed, k, 29)
            if v < 0.085:
                age = 0.02 + 0.10 * h01(seed, k, 31)          # replaced very recently
            elif v < 0.20:
                age = 0.18 + 0.22 * h01(seed, k, 37)
            else:
                age = clamp01(0.35 + 0.62 * sa + 0.22 * (h01(seed, k, 41) - 0.5))
            runs.append((s, e, float(age)))
            s = e
            k += 1
        arr = np.zeros(NS)
        for (a, b, ag) in runs:
            arr[(SGRID >= a) & (SGRID < b)] = ag
        return runs, arr

    def _incidents(self):
        w = crash_field()
        cdf = np.cumsum(w)
        cdf /= cdf[-1]
        out = []
        N = 38
        for i in range(N):
            u = h01(7717, i, 3)
            sa = float(np.interp(u, cdf, SGRID))
            side = -1 if h01(7717, i, 5) < 0.72 else +1     # mostly the outside
            sev = h01(7717, i, 9)
            if sev < 0.44:
                kind, ext, depth = "brush", 5.0 + 9.0 * h01(7717, i, 13), 0.010
            elif sev < 0.78:
                kind, ext, depth = "hit", 8.0 + 14.0 * h01(7717, i, 13), 0.055
            elif sev < 0.93:
                kind, ext, depth = "repaired", 12.0 + 12.0 * h01(7717, i, 13), 0.012
            else:
                kind, ext, depth = "heavy", 16.0 + 14.0 * h01(7717, i, 13), 0.190
            out.append(dict(s=sa, side=side, kind=kind, extent=ext, depth=depth,
                            epoch=h01(7717, i, 17),
                            livery=LIVERY[int(h01(7717, i, 19) * (len(LIVERY) - 1e-6))],
                            idx=i))
        return out

    # --- queries ---------------------------------------------------------
    def run_id(self, s, side):
        i = (np.rint(np.asarray(s) % LAP_LEN / PS).astype(np.int64)) % NS
        return self.rid[side][i]

    def age_at(self, s, side):
        i = (np.rint(np.asarray(s) % LAP_LEN / PS).astype(np.int64)) % NS
        return self.age[side][i]

    def scars(self, s, side):
        """(dent_depth, scuff, paint_mix, paint_rgb, fresh) at station(s)."""
        s = np.atleast_1d(np.asarray(s, dtype=np.float64))
        dent = np.zeros_like(s)
        scuff = np.zeros_like(s)
        pmix = np.zeros_like(s)
        fresh = np.zeros_like(s)
        prgb = np.zeros(s.shape + (3,))
        for inc in self.inc:
            if inc["side"] != side:
                continue
            du = ((s - inc["s"] + LAP_LEN * 0.5) % LAP_LEN) - LAP_LEN * 0.5
            r = inc["extent"] * 0.5
            g = np.exp(-0.5 * (du / max(1.0, r * 0.55)) ** 2)
            g *= (np.abs(du) < r * 1.6)
            lobe = g * (0.55 + 0.9 * vnoise1(du * 0.35 + inc["idx"] * 13.0, 771))
            if inc["kind"] == "repaired":
                fresh = np.maximum(fresh, (np.abs(du) < r).astype(float))
                dent = np.maximum(dent, lobe * inc["depth"] * 0.4)
            else:
                dent = np.maximum(dent, lobe * inc["depth"])
            sc = g * (1.0 - 0.55 * inc["epoch"])
            scuff = np.maximum(scuff, sc)
            # paint transfer is a SMEAR a couple of metres long, not a wash the
            # length of the damage: tighten the lobe hard.
            gp = np.exp(-0.5 * (du / max(0.8, r * 0.24)) ** 2) * (np.abs(du) < r * 0.8)
            pm = gp * (0.85 - 0.6 * inc["epoch"])
            upd = pm > pmix
            pmix = np.where(upd, pm, pmix)
            prgb[upd] = inc["livery"]
        return dent, clamp01(scuff), clamp01(pmix), prgb, fresh

    def align(self, s, side):
        """(lateral wander m, vertical settle m) — small, smooth, plus run steps."""
        s = np.asarray(s, dtype=np.float64)
        seed = 8800 + (side > 0) * 13
        lat = (fbm1(s / 47.0, seed=seed, oct=3) - 0.5) * 0.075
        lat += (fbm1(s / 7.3, seed=seed + 5, oct=2) - 0.5) * 0.020
        vert = -(fbm1(s / 33.0, seed=seed + 9, oct=3)) * 0.045
        vert += -(fbm1(s / 5.1, seed=seed + 11, oct=2)) * 0.012
        return lat, vert


HIST = History()

# ----------------------------------------------------------------------------
# 6.  hero windows — where the camera dwells, drives tessellation only
# ----------------------------------------------------------------------------
# (label, s0, s1, side or 0=both, tier)   tier 2 = macro, 1 = near, 0 = normal
HERO = [
    ("t1_brake",     150.0,  420.0, 0, 1),
    ("hairpin",      880.0, 1100.0, 0, 2),
    ("summit",      1700.0, 1900.0, 0, 1),
    ("bridge",      2360.0, 2470.0, 0, 1),
    ("doppler",     2470.0, 2650.0, -1, 2),
    ("plunge",      2650.0, 2800.0, 0, 1),
    ("gantry",      3560.0, 3675.0, 0, 1),
    ("sf_line",        0.0,  120.0, 0, 1),
]
# real 3-D woven wire (not a card) only here — the two places the camera is
# closer to the fence than ~12 m.
WIRE_WINDOWS = [(2495.0, 2615.0, -1)]


def hero_tier(s, side):
    t = np.zeros(np.shape(np.atleast_1d(s)), dtype=int)
    for (_lbl, a, b, sd, tier) in HERO:
        if sd != 0 and sd != side:
            continue
        m = ((np.atleast_1d(s) % LAP_LEN) >= a) & ((np.atleast_1d(s) % LAP_LEN) <= b)
        t = np.where(m, np.maximum(t, tier), t)
    return t


def in_wire_window(s, side):
    for (a, b, sd) in WIRE_WINDOWS:
        if sd == side and a <= (s % LAP_LEN) <= b:
            return True
    return False

# ----------------------------------------------------------------------------
# 7.  mesh accumulation
# ----------------------------------------------------------------------------

class MB:
    """Numpy mesh accumulator -> one Blender object.  Mixed tri/quad faces."""

    __slots__ = ("name", "_V", "_F", "_K", "_UV", "_W", "_P", "_U", "_M", "_S", "_n")

    def __init__(self, name):
        self.name = name
        self._V, self._F, self._K = [], [], []
        self._UV, self._W, self._P, self._U = [], [], [], []
        self._M, self._S = [], []
        self._n = 0

    @property
    def nverts(self):
        return self._n

    def add(self, verts, faces, mat=0, uv=None, wear=None, paint=None, uid=None,
            smooth=True):
        """verts (n,3); faces (m,k) int, local indices."""
        verts = np.asarray(verts, dtype=np.float64).reshape(-1, 3)
        faces = np.asarray(faces, dtype=np.int64)
        if faces.size == 0:
            return
        n, m, k = len(verts), faces.shape[0], faces.shape[1]
        self._V.append(verts)
        self._F.append(faces + self._n)
        self._K.append(k)
        self._UV.append(np.zeros((n, 2)) if uv is None else np.asarray(uv, float).reshape(n, 2))
        self._W.append(np.tile([0.5, 0.0, 0.0, 1.0], (n, 1)) if wear is None
                       else np.asarray(wear, float).reshape(n, 4))
        self._P.append(np.tile([0.0, 0.0, 0.0, 1.0], (n, 1)) if paint is None
                       else np.asarray(paint, float).reshape(n, 4))
        self._U.append(np.tile([0.5, 0.0, 0.0, 1.0], (n, 1)) if uid is None
                       else np.asarray(uid, float).reshape(n, 4))
        self._M.append(np.full(m, int(mat), dtype=np.int32))
        self._S.append(np.full(m, bool(smooth), dtype=bool))
        self._n += n

    def add_grid(self, P, **kw):
        """P: (ni,nj,3) -> quad grid.  kw arrays may be (ni,nj,c)."""
        P = np.asarray(P, dtype=np.float64)
        ni, nj = P.shape[0], P.shape[1]
        i = (np.arange(ni - 1)[:, None] * nj + np.arange(nj - 1)[None, :])
        q = np.stack([i, i + nj, i + nj + 1, i + 1], axis=-1).reshape(-1, 4)
        kk = {}
        for key in ("uv", "wear", "paint", "uid"):
            if key in kw and kw[key] is not None:
                kk[key] = np.asarray(kw[key], float).reshape(ni * nj, -1)
        for key in ("mat", "smooth"):
            if key in kw:
                kk[key] = kw[key]
        self.add(P.reshape(-1, 3), q, **kk)

    # ------------------------------------------------------------------
    def emit(self, coll, materials):
        if not self._V or self._n == 0:
            return None
        V = np.concatenate(self._V, axis=0)
        UV = np.concatenate(self._UV, axis=0)
        W = np.concatenate(self._W, axis=0)
        P = np.concatenate(self._P, axis=0)
        U = np.concatenate(self._U, axis=0)
        M = np.concatenate(self._M, axis=0)
        S = np.concatenate(self._S, axis=0)
        loops = np.concatenate([f.ravel() for f in self._F])
        ltot = np.concatenate([np.full(f.shape[0], k, dtype=np.int32)
                               for f, k in zip(self._F, self._K)])
        lstart = np.zeros(len(ltot), dtype=np.int32)
        np.cumsum(ltot[:-1], out=lstart[1:])

        # Recentre: world coordinates out at |P| ~ 1000 m destroy float32
        # precision in any procedural texture driven by position (a x90 gravel
        # voronoi lands at 1e5 and turns to mush).  Store local coordinates and
        # carry the offset on the object, so Object/Generated texture space is
        # always small.  Materials must use TexCoord>Object, never Geometry>Position.
        ctr = 0.5 * (V.min(axis=0) + V.max(axis=0))
        V = V - ctr
        me = bpy.data.meshes.new(self.name)
        me.vertices.add(len(V))
        me.loops.add(len(loops))
        me.polygons.add(len(ltot))
        me.vertices.foreach_set("co", V.ravel())
        me.loops.foreach_set("vertex_index", loops.astype(np.int32))
        me.polygons.foreach_set("loop_start", lstart)
        me.polygons.foreach_set("loop_total", ltot)
        me.update(calc_edges=True)
        me.polygons.foreach_set("use_smooth", S)
        me.polygons.foreach_set("material_index", M)

        uvl = me.uv_layers.new(name="UVMap")
        uvl.data.foreach_set("uv", UV[loops].ravel())
        for nm, arr in (("wear", W), ("paint", P), ("uid", U)):
            ca = me.color_attributes.new(name=nm, type='FLOAT_COLOR', domain='POINT')
            ca.data.foreach_set("color", arr.ravel())
        me.validate(verbose=False)

        for mat in materials:
            me.materials.append(mat)
        ob = bpy.data.objects.new(self.name, me)
        ob.location = tuple(float(c) for c in ctr)
        coll.objects.link(ob)
        return ob


# ----------------------------------------------------------------------------
# 8.  frames + sweeping
# ----------------------------------------------------------------------------

def frames_from_polyline(P):
    """P (n,3) -> (tangent, right, up) per point, up kept near +Z."""
    P = np.asarray(P, dtype=np.float64)
    d = np.zeros_like(P)
    d[1:-1] = P[2:] - P[:-2]
    d[0] = P[1] - P[0]
    d[-1] = P[-1] - P[-2]
    L = np.linalg.norm(d, axis=1, keepdims=True)
    T = d / np.maximum(L, 1e-9)
    up0 = np.array([0.0, 0.0, 1.0])
    R = np.cross(T, up0)
    Rl = np.linalg.norm(R, axis=1, keepdims=True)
    R = R / np.maximum(Rl, 1e-9)
    U = np.cross(R, T)
    return T, R, U


def sweep(P, profile, twist=None, scale=None, close=False):
    """Sweep a 2-D profile (k,2)=(lateral,vertical) along polyline P (n,3).

    Returns (n,k,3).  `twist` (n,) radians rolls the profile about the tangent;
    `scale` (n,2) scales it per station.
    """
    P = np.asarray(P, dtype=np.float64)
    pr = np.asarray(profile, dtype=np.float64)
    T, R, U = frames_from_polyline(P)
    n, k = len(P), len(pr)
    a = np.tile(pr[None, :, 0], (n, 1))
    b = np.tile(pr[None, :, 1], (n, 1))
    if scale is not None:
        sc = np.asarray(scale, float).reshape(n, 2)
        a = a * sc[:, 0:1]
        b = b * sc[:, 1:2]
    if twist is not None:
        c, s = np.cos(twist)[:, None], np.sin(twist)[:, None]
        a, b = a * c - b * s, a * s + b * c
    return P[:, None, :] + a[..., None] * R[:, None, :] + b[..., None] * U[:, None, :]


def tube(P, radius, seg=6, phase=0.0):
    """Round tube along P.  radius may be scalar or (n,)."""
    P = np.asarray(P, dtype=np.float64)
    th = np.linspace(0, 2 * math.pi, seg, endpoint=False) + phase
    pr = np.stack([np.cos(th), np.sin(th)], axis=1)
    r = np.broadcast_to(np.asarray(radius, float).reshape(-1, 1), (len(P), 1))
    return sweep(P, pr, scale=np.concatenate([r, r], axis=1))


def ring_faces(n, k, closed=True):
    """quads between consecutive rings of a (n,k) grid."""
    i = np.arange(n - 1)[:, None]
    j = np.arange(k if closed else k - 1)[None, :]
    j2 = (j + 1) % k
    a = i * k + j
    b = (i + 1) * k + j
    c = (i + 1) * k + j2
    d = i * k + j2
    return np.stack([a, b, c, d], axis=-1).reshape(-1, 4)


def cap_fan(idx0, k, reverse=False):
    """triangle fan closing a ring of k verts starting at idx0 (uses a centre
    vertex that the caller appends at idx0+k)."""
    j = np.arange(k)
    j2 = (j + 1) % k
    c = np.full(k, idx0 + k)
    tri = np.stack([c, idx0 + j, idx0 + j2], axis=-1)
    return tri[:, ::-1] if reverse else tri


def box(cx, cy, cz, sx, sy, sz, rot=0.0):
    """Axis box with Z rotation -> (8,3) verts, (6,4) faces."""
    hx, hy, hz = sx * 0.5, sy * 0.5, sz * 0.5
    v = np.array([[-hx, -hy, -hz], [hx, -hy, -hz], [hx, hy, -hz], [-hx, hy, -hz],
                  [-hx, -hy, hz], [hx, -hy, hz], [hx, hy, hz], [-hx, hy, hz]])
    c, s = math.cos(rot), math.sin(rot)
    R = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
    v = v @ R.T + np.array([cx, cy, cz])
    f = np.array([[0, 1, 2, 3], [7, 6, 5, 4], [0, 4, 5, 1],
                  [1, 5, 6, 2], [2, 6, 7, 3], [3, 7, 4, 0]])
    return v, f


def icosphere_pts(subdiv=1):
    """Unit icosphere vertices + faces (tris)."""
    t = (1.0 + 5 ** 0.5) / 2.0
    V = np.array([[-1, t, 0], [1, t, 0], [-1, -t, 0], [1, -t, 0],
                  [0, -1, t], [0, 1, t], [0, -1, -t], [0, 1, -t],
                  [t, 0, -1], [t, 0, 1], [-t, 0, -1], [-t, 0, 1]], dtype=np.float64)
    F = np.array([[0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11],
                  [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8],
                  [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9],
                  [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1]])
    V /= np.linalg.norm(V, axis=1, keepdims=True)
    for _ in range(subdiv):
        mid = {}
        nv = list(V)
        nf = []
        def m(a, b):
            key = (min(a, b), max(a, b))
            if key not in mid:
                p = (nv[a] + nv[b])
                p = p / np.linalg.norm(p)
                nv.append(p)
                mid[key] = len(nv) - 1
            return mid[key]
        for (a, b, c) in F:
            ab, bc, ca = m(a, b), m(b, c), m(c, a)
            nf += [[a, ab, ca], [b, bc, ab], [c, ca, bc], [ab, bc, ca]]
        V = np.array(nv)
        F = np.array(nf)
    return V, F


_ICO1 = icosphere_pts(1)          # 42 v / 80 f
_ICO0 = icosphere_pts(0)          # 12 v / 20 f


# ----------------------------------------------------------------------------
# 9.  scene / collection plumbing
# ----------------------------------------------------------------------------

SUBCOLLS = ["Armco", "TecPro", "Concrete", "Fence", "FenceWire", "Gravel",
            "Runoff", "Platform", "TyreWall", "Transit"]


def purge():
    """Remove everything this module owns.  Makes build() idempotent.

    ...and the LOSER OF FINDING #3, by name.  Contract §6.2 gives the Beat-4
    walled corridor to this module (`C.CORRIDOR_OWNER`) and names the object the
    other build must not leave behind (`C.CORRIDOR_DELETE_NAMES`).  Doing that
    HERE rather than trusting the assembly order is the whole point of the
    finding: the corridor got built twice, 0.5 m apart, precisely because each
    module was correct on its own and nobody owned the overlap.
    """
    for ob in list(bpy.data.objects):
        if ob.name.startswith(PFX):
            bpy.data.objects.remove(ob, do_unlink=True)
    for nm in WC.CORRIDOR_DELETE_NAMES:
        for ob in list(bpy.data.objects):
            if ob.name == nm or ob.name.startswith(nm + "."):
                print("[BR] deleting %s — contract §6.2, this module owns the "
                      "Beat-4 corridor" % ob.name)
                bpy.data.objects.remove(ob, do_unlink=True)
        c = bpy.data.collections.get(nm)
        if c is not None:
            for ob in list(c.objects):
                bpy.data.objects.remove(ob, do_unlink=True)
            bpy.data.collections.remove(c)
            print("[BR] deleting collection %s — contract §6.2" % nm)
    root = bpy.data.collections.get(ROOT_COLL)
    if root:
        for ch in list(root.children):
            bpy.data.collections.remove(ch)
        for ob in list(root.objects):
            bpy.data.objects.remove(ob, do_unlink=True)
        bpy.data.collections.remove(root)
    for coll in list(bpy.data.collections):
        if coll.name.startswith(PFX):
            bpy.data.collections.remove(coll)
    for me in list(bpy.data.meshes):
        if me.name.startswith(PFX) or me.users == 0:
            try:
                bpy.data.meshes.remove(me)
            except Exception:
                pass
    for mat in list(bpy.data.materials):
        if mat.name.startswith(PFX):
            bpy.data.materials.remove(mat)
    for ng in list(bpy.data.node_groups):
        if ng.name.startswith(PFX):
            bpy.data.node_groups.remove(ng)
    for im in list(bpy.data.images):
        if im.name.startswith(PFX):
            bpy.data.images.remove(im)
    for coll_ in (bpy.data.lights, bpy.data.cameras, bpy.data.worlds):
        for db in list(coll_):
            if db.name.startswith(PFX):
                try:
                    coll_.remove(db)
                except Exception:
                    pass


def make_collections(scene):
    root = bpy.data.collections.new(ROOT_COLL)
    scene.collection.children.link(root)
    out = {}
    for nm in SUBCOLLS:
        c = bpy.data.collections.new(PFX + nm)
        root.children.link(c)
        out[nm] = c
    return root, out

# ----------------------------------------------------------------------------
# 10.  materials — everything procedural, driven by the per-unit attributes
# ----------------------------------------------------------------------------
#
# Attribute contract (written by MB.emit for every object this module makes):
#   UVMap    u = metres along the unit run, v = metres up the face
#   "wear"   R = age 0..1   G = rust 0..1   B = scuff 0..1   A = paint mix
#   "paint"  RGB = transferred livery colour (fictional liveries only)
#   "uid"    R = per-unit random 0..1   G = sub-type flag   B = damage   A = free

class NG:
    """Tiny shader-graph DSL.  Every value argument accepts:
         node                -> node.outputs[0]
         (node, i)           -> node.outputs[i]
         float               -> constant
         (r, g, b)           -> constant colour  (colour sockets only)
    """

    def __init__(self, mat):
        mat.use_nodes = True
        self.nt = mat.node_tree
        self.nt.nodes.clear()
        self._x = 0

    def n(self, t, defaults=None, **kw):
        nd = self.nt.nodes.new(t)
        self._x += 190
        nd.location = (self._x, (self._x // 190 % 7) * 240)
        for k, v in kw.items():
            setattr(nd, k, v)
        if defaults:
            for i, v in defaults.items():
                nd.inputs[i].default_value = v
        return nd

    # -- socket plumbing ------------------------------------------------
    def _feed(self, node, idx, v):
        if v is None:
            return
        if isinstance(v, bpy.types.Node):
            self.nt.links.new(v.outputs[0], node.inputs[idx])
        elif isinstance(v, tuple) and len(v) == 2 and isinstance(v[0], bpy.types.Node):
            self.nt.links.new(v[0].outputs[v[1]], node.inputs[idx])
        elif isinstance(v, (tuple, list)):
            node.inputs[idx].default_value = (*v, 1.0) if len(v) == 3 else tuple(v)
        else:
            node.inputs[idx].default_value = float(v)

    def lk(self, a, ao, b, bi):
        self.nt.links.new(a.outputs[ao], b.inputs[bi])

    # -- sugar ----------------------------------------------------------
    def attr(self, name):
        return self.n("ShaderNodeAttribute", attribute_name=name)

    def sep(self, v):
        s = self.n("ShaderNodeSeparateColor")
        self._feed(s, 0, v)
        return s

    def math(self, op, a=None, b=None, c=None, clamp=False):
        m = self.n("ShaderNodeMath", operation=op, use_clamp=clamp)
        self._feed(m, 0, a)
        self._feed(m, 1, b)
        self._feed(m, 2, c)
        return m

    def vmath(self, op, a=None, b=None, scale=None):
        m = self.n("ShaderNodeVectorMath", operation=op)
        self._feed(m, 0, a)
        if b is not None:
            if isinstance(b, (tuple, list)) and len(b) == 3 and not isinstance(b[0], bpy.types.Node):
                m.inputs[1].default_value = tuple(b)
            else:
                self._feed(m, 1, b)
        if scale is not None:
            self._feed(m, 3, scale)
        return m

    def mix(self, fac, a, b, blend="MIX"):
        m = self.n("ShaderNodeMixRGB", blend_type=blend)
        self._feed(m, 0, fac)
        self._feed(m, 1, a)
        self._feed(m, 2, b)
        return m

    def noise(self, vec=None, scale=5.0, detail=8.0, rough=0.55, dist=0.0):
        nd = self.n("ShaderNodeTexNoise", noise_dimensions='3D',
                    defaults={2: scale, 3: detail, 4: rough, 8: dist})
        self._feed(nd, 0, vec)
        return nd

    def voro(self, vec=None, scale=10.0, rand=1.0):
        nd = self.n("ShaderNodeTexVoronoi", feature='F1', voronoi_dimensions='3D',
                    defaults={2: scale, 8: rand})
        self._feed(nd, 0, vec)
        return nd

    def uvscale(self, uvnode, sx, sy, sz=1.0):
        return self.vmath('MULTIPLY', (uvnode, 2), (sx, sy, sz))

    def poscale(self, tcnode, s):
        """object-space position x s.  NEVER world position: see MB.emit."""
        return self.vmath('MULTIPLY', (tcnode, 3), (s, s, s))

    def spec(self, bsdf, level=0.5, tint=None):
        """Principled specular level, BY NAME.

        A natural ground surface is not a 0.5-specular dielectric.  At the 12.47
        deg sun this film uses, every ground plane is seen at a grazing angle for
        most of every frame, and at grazing incidence a 0.5 specular level throws
        the whole sky back at the camera: the verge rendered as a saturated cyan
        band behind the T1 gravel trap, which is not a colour grass has.  Set by
        name because the Principled input indices move between Blender versions
        and Specular IOR Level is at 14 in 5.2.
        """
        bsdf.inputs["Specular IOR Level"].default_value = float(level)
        if tint is not None:
            bsdf.inputs["Specular Tint"].default_value = (*tint, 1.0)

    def ramp(self, fac, stops):
        r = self.n("ShaderNodeValToRGB")
        self._feed(r, 0, fac)
        el = r.color_ramp.elements
        while len(el) > 1:
            el.remove(el[-1])
        el[0].position = stops[0][0]
        el[0].color = (*stops[0][1], 1.0)
        for (p, c) in stops[1:]:
            e = el.new(p)
            e.color = (*c, 1.0)
        return r


def _new_mat(name):
    m = bpy.data.materials.new(PFX + name)
    g = NG(m)
    out = g.n("ShaderNodeOutputMaterial")
    bsdf = g.n("ShaderNodeBsdfPrincipled")
    g.lk(bsdf, 0, out, 0)
    return m, g, bsdf, out


# --- 10.1 galvanised / weathered steel --------------------------------------

def mat_steel():
    m, g, b, _ = _new_mat("Steel_Galv")
    tc = g.n("ShaderNodeTexCoord")
    wear = g.attr("wear")
    ws = g.sep(wear)                     # 0 age, 1 rust, 2 scuff  (+ wear.A = paint)
    paint = g.attr("paint")
    age = (ws, 0)

    spg = g.voro(g.uvscale(tc, 40.0, 40.0), scale=1.0, rand=1.0)      # galv spangle ~25 mm
    fine = g.noise(g.uvscale(tc, 90.0, 90.0), scale=1.0, detail=6.0, rough=0.6)

    us = g.sep(g.attr("uid"))            # G = painted run, B = which paint
    galv = g.mix(age, (0.372, 0.386, 0.398), (0.156, 0.160, 0.158))
    galv = g.mix(0.16, galv, (spg, 1), "OVERLAY")
    galv = g.mix(0.10, galv, (fine, 1), "SOFT_LIGHT")
    patina = g.noise(g.uvscale(tc, 1.4, 0.9), scale=1.0, detail=7.0, rough=0.62)
    galv = g.mix(g.math("MULTIPLY", (ws, 0), 0.55), galv,
                 g.mix(patina, (0.198, 0.206, 0.204), (0.318, 0.322, 0.310)))
    # fictional maintenance paints — no team or sponsor colours
    pcol = g.ramp((us, 2), [(0.00, (0.520, 0.522, 0.508)),   # dirty white
                            (0.28, (0.212, 0.238, 0.216)),   # dark green
                            (0.55, (0.318, 0.330, 0.352)),   # blue grey
                            (0.80, (0.446, 0.432, 0.402)),   # stone
                            (1.00, (0.128, 0.132, 0.140))])  # near black
    chip = g.noise(g.uvscale(tc, 9.0, 9.0), scale=1.0, detail=8.0, rough=0.66)
    chipm = g.math("SUBTRACT", chip, 0.60, clamp=True)
    chipm = g.math("MULTIPLY", chipm, g.math("MULTIPLY", (ws, 0), 4.2), clamp=True)
    pcol = g.mix(chipm, pcol, galv)
    base = g.mix((us, 1), galv, pcol)

    # rust: age x downward streak x pitting
    streak = g.noise(g.uvscale(tc, 3.2, 0.42), scale=1.0, detail=9.0, rough=0.72)
    pit = g.noise(g.uvscale(tc, 26.0, 26.0), scale=1.0, detail=7.0, rough=0.62)
    rmask = g.math("MULTIPLY", (ws, 1), g.math("POWER", streak, 1.6))
    rmask = g.math("MULTIPLY", rmask, 1.95)
    rmask = g.math("SUBTRACT", rmask, 0.42, clamp=True)
    rmask = g.math("MULTIPLY", rmask, g.math("ADD", 0.30, pit))
    rmask = g.math("MULTIPLY", rmask, 1.7, clamp=True)
    rmask = g.math("MULTIPLY", rmask, 0.86)
    rmask = g.math("ADD", rmask, g.math("MULTIPLY", chipm,
                                        g.math("MULTIPLY", (us, 1), 0.55)),
                   clamp=True)
    rust_c = g.ramp(streak, [(0.00, (0.203, 0.075, 0.028)), (0.45, (0.372, 0.148, 0.051)),
                             (0.78, (0.470, 0.235, 0.093)), (1.00, (0.300, 0.190, 0.135))])
    base = g.mix(rmask, base, rust_c)

    # rubber scuff and livery transfer only reach car-contact height: UV.v is
    # metres above the barrier foot, so a fence post 4 m up never gets painted.
    hgate = g.n("ShaderNodeMapRange", clamp=True,
                defaults={1: 1.05, 2: 1.65, 3: 1.0, 4: 0.0})
    uvsep = g.n("ShaderNodeSeparateXYZ")
    g.lk(tc, 2, uvsep, 0)
    g.lk(uvsep, 1, hgate, 0)
    sstreak = g.noise(g.uvscale(tc, 1.1, 9.0), scale=1.0, detail=7.0)
    smask = g.math("MULTIPLY", (ws, 2), sstreak)
    smask = g.math("MULTIPLY", smask, 1.9, clamp=True)
    smask = g.math("MULTIPLY", smask, hgate)
    base = g.mix(smask, base, (0.038, 0.036, 0.035))

    # livery paint transfer
    pstreak = g.noise(g.uvscale(tc, 2.4, 14.0), scale=1.0, detail=6.0)
    pmask = g.math("MULTIPLY", (wear, 3), pstreak)
    pmask = g.math("MULTIPLY", pmask, 2.2, clamp=True)
    pmask = g.math("MULTIPLY", pmask, hgate)
    base = g.mix(pmask, base, (paint, 0))

    g.lk(base, 0, b, 0)
    met = g.math("SUBTRACT", 0.88, rmask)
    met = g.math("SUBTRACT", met, pmask)
    met = g.math("MULTIPLY", met, g.math("SUBTRACT", 1.0,
                                         g.math("MULTIPLY", (us, 1), 0.92)),
                 clamp=True)
    g.lk(met, 0, b, 1)
    rgh = g.math("MULTIPLY", age, 0.20)
    rgh = g.math("ADD", rgh, 0.545)
    rgh = g.math("ADD", rgh, g.math("MULTIPLY", rmask, 0.18))
    rgh = g.math("SUBTRACT", rgh, g.math("MULTIPLY", (us, 1), 0.13))
    rgh = g.math("ADD", rgh, g.math("MULTIPLY", fine, 0.09), clamp=True)
    g.lk(rgh, 0, b, 2)

    mill = g.noise(g.uvscale(tc, 340.0, 340.0), scale=1.0, detail=5.0, rough=0.55)
    hb = g.math("MULTIPLY", spg, 0.30)
    hb = g.math("ADD", hb, g.math("MULTIPLY", mill, 0.22))
    hb = g.math("ADD", hb, g.math("MULTIPLY", pit, g.math("MULTIPLY", rmask, 1.6)))
    bump = g.n("ShaderNodeBump", defaults={0: 0.55, 1: 0.0022})
    g.lk(hb, 0, bump, 3)
    g.lk(bump, 0, b, 6)
    return m


# --- 10.2 TecPro polyethylene -----------------------------------------------

def mat_tecpro():
    m, g, b, _ = _new_mat("TecPro")
    tc = g.n("ShaderNodeTexCoord")
    wear = g.attr("wear")
    ws = g.sep(wear)
    uid = g.attr("uid")
    us = g.sep(uid)
    sxyz = g.n("ShaderNodeSeparateXYZ")
    g.lk(tc, 2, sxyz, 0)          # UV.y = height above THIS block's base

    bl = g.mix((ws, 0), (0.013, 0.036, 0.212), (0.038, 0.078, 0.176))
    rd = g.mix((ws, 0), (0.290, 0.017, 0.014), (0.212, 0.070, 0.058))
    base = g.mix((us, 1), bl, rd)               # uid.G = 1 for the red cap row

    peel = g.noise(g.uvscale(tc, 55.0, 55.0), scale=1.0, detail=7.0, rough=0.55)
    lump = g.noise(g.uvscale(tc, 3.4, 3.4), scale=1.0, detail=4.0, rough=0.5)
    chalk = g.math("MULTIPLY", (ws, 0), peel)
    chalk = g.math("MULTIPLY", chalk, 0.20, clamp=True)
    base = g.mix(chalk, base, (0.560, 0.585, 0.622), "SCREEN")

    dirt = g.math("SUBTRACT", 0.30, (sxyz, 1))
    dirt = g.math("MULTIPLY", dirt, 2.6, clamp=True)
    dirt = g.math("MULTIPLY", dirt, g.noise(g.uvscale(tc, 6.0, 3.0), scale=1.0))
    dirt = g.math("MULTIPLY", dirt, 2.0, clamp=True)
    base = g.mix(dirt, base, (0.086, 0.077, 0.062))

    sstreak = g.noise(g.uvscale(tc, 1.4, 11.0), scale=1.0, detail=7.0)
    smask = g.math("MULTIPLY", (ws, 2), sstreak)
    smask = g.math("MULTIPLY", smask, 2.1, clamp=True)
    base = g.mix(smask, base, (0.030, 0.029, 0.028))
    pmask = g.math("MULTIPLY", (wear, 3), sstreak)
    pmask = g.math("MULTIPLY", pmask, 1.25, clamp=True)
    base = g.mix(pmask, base, (g.attr("paint"), 0))

    g.lk(base, 0, b, 0)
    b.inputs[1].default_value = 0.0
    rgh = g.math("MULTIPLY", (ws, 0), 0.20)
    rgh = g.math("ADD", rgh, 0.545)
    rgh = g.math("ADD", rgh, g.math("MULTIPLY", peel, 0.10), clamp=True)
    g.lk(rgh, 0, b, 2)
    b.inputs[9].default_value = 0.06
    b.inputs[11].default_value = 0.012
    hb = g.math("MULTIPLY", peel, 0.55)
    hb = g.math("ADD", hb, g.math("MULTIPLY", lump, 0.45))
    bump = g.n("ShaderNodeBump", defaults={0: 0.30, 1: 0.004})
    g.lk(hb, 0, bump, 3)
    g.lk(bump, 0, b, 6)
    return m


# --- 10.3 precast concrete ---------------------------------------------------

def mat_concrete():
    m, g, b, _ = _new_mat("Concrete")
    tc = g.n("ShaderNodeTexCoord")
    wear = g.attr("wear")
    ws = g.sep(wear)
    us = g.sep(g.attr("uid"))
    sxyz = g.n("ShaderNodeSeparateXYZ")
    g.lk(tc, 2, sxyz, 0)          # UV.y = height above THIS block's base

    pour = g.ramp((us, 0), [(0.00, (0.415, 0.408, 0.392)), (0.35, (0.472, 0.468, 0.455)),
                            (0.70, (0.386, 0.390, 0.395)), (1.00, (0.502, 0.492, 0.470))])
    agg = g.voro(g.uvscale(tc, 160.0, 160.0), scale=1.0, rand=1.0)
    agg2 = g.noise(g.uvscale(tc, 420.0, 420.0), scale=1.0, detail=8.0, rough=0.62)
    base = g.mix(0.13, pour, (agg, 1), "OVERLAY")
    base = g.mix(0.09, base, (agg2, 1), "SOFT_LIGHT")

    streak = g.noise(g.uvscale(tc, 5.5, 0.35), scale=1.0, detail=9.0, rough=0.7)
    smask = g.math("MULTIPLY", (ws, 0), streak)
    smask = g.math("MULTIPLY", smask, 1.5, clamp=True)
    base = g.mix(smask, base, (0.196, 0.190, 0.176))

    low = g.math("SUBTRACT", 0.26, (sxyz, 1))
    low = g.math("MULTIPLY", low, 3.2, clamp=True)
    low = g.math("MULTIPLY", low, g.noise(g.uvscale(tc, 9.0, 5.0), scale=1.0))
    low = g.math("MULTIPLY", low, g.math("ADD", 0.6, g.math("MULTIPLY", (ws, 0), 2.0)),
                 clamp=True)
    base = g.mix(low, base, (0.152, 0.170, 0.118))

    sc = g.math("MULTIPLY", (ws, 2), g.noise(g.uvscale(tc, 1.6, 10.0), scale=1.0))
    sc = g.math("MULTIPLY", sc, 2.0, clamp=True)
    base = g.mix(sc, base, (0.045, 0.043, 0.042))
    pm = g.math("MULTIPLY", (wear, 3), 1.6, clamp=True)
    base = g.mix(pm, base, (g.attr("paint"), 0))

    g.lk(base, 0, b, 0)
    rgh = g.math("ADD", 0.62, g.math("MULTIPLY", agg2, 0.22))
    rgh = g.math("ADD", rgh, g.math("MULTIPLY", (ws, 0), 0.12), clamp=True)
    g.lk(rgh, 0, b, 2)
    hb = g.math("MULTIPLY", agg, 0.45)
    hb = g.math("ADD", hb, g.math("MULTIPLY", agg2, 0.55))
    bump = g.n("ShaderNodeBump", defaults={0: 0.30, 1: 0.0022})
    g.lk(hb, 0, bump, 3)
    g.lk(bump, 0, b, 6)
    return m


# --- 10.4 debris-fence weave cards ------------------------------------------
FENCE_PITCH = 0.050
FENCE_WIRE_D = 0.0052
# Distance (m) over which the periodic weave mask collapses to its exact mean
# coverage.  Tuned for a 3840-wide frame; `set_fence_fade()` rescales it for
# any other render width so preview and final agree.
FENCE_FADE_NEAR = 45.0
FENCE_FADE_FAR = 190.0


def mat_fence(axis, pitch=FENCE_PITCH, wire_d=FENCE_WIRE_D):
    """axis 'V': wires run vertically, so the mask repeats along u.
       axis 'H': wires run horizontally, mask repeats along v."""
    m, g, b, out = _new_mat("FenceMesh_" + axis)
    tc = g.n("ShaderNodeTexCoord")
    sxyz = g.n("ShaderNodeSeparateXYZ")
    g.lk(tc, 2, sxyz, 0)
    us = g.sep(g.attr("uid"))
    ws = g.sep(g.attr("wear"))

    coord = 0 if axis == "V" else 1
    ph = g.math("MULTIPLY", (us, 0), pitch)
    pos = g.math("ADD", (sxyz, coord), ph)
    tri = g.math("PINGPONG", pos, pitch * 0.5)
    t = g.math("DIVIDE", tri, wire_d * 0.5)
    cov = g.math("SUBTRACT", 1.0, t)
    cov = g.math("MULTIPLY", cov, 7.0, clamp=True)

    # broken / missing wires — per-span severity from uid.B
    dmg = g.noise(g.uvscale(tc, 1.0 / pitch, 0.55), scale=1.0, detail=2.0, rough=0.5)
    dmg = g.math("SUBTRACT", dmg, 0.62, clamp=True)
    dmg = g.math("MULTIPLY", dmg, g.math("MULTIPLY", (us, 2), 9.0), clamp=True)
    cov = g.math("MULTIPLY", cov, g.math("SUBTRACT", 1.0, dmg, clamp=True))

    # analytic distance filtering: the periodic mask collapses to its exact
    # mean coverage once the aperture is under a pixel.  No geometry LOD seam.
    cam = g.n("ShaderNodeCameraData")
    fade = g.n("ShaderNodeMapRange", clamp=True,
               defaults={1: FENCE_FADE_NEAR, 2: FENCE_FADE_FAR, 3: 0.0, 4: 1.0})
    fade.name = fade.label = "BR_FENCE_FADE"
    g.lk(cam, 2, fade, 0)
    inv = g.math("SUBTRACT", 1.0, fade)
    a1 = g.math("MULTIPLY", cov, inv)
    a2 = g.math("MULTIPLY", fade, wire_d / pitch)
    alpha = g.math("ADD", a1, a2, clamp=True)

    wcol = g.mix((ws, 0), (0.585, 0.600, 0.612), (0.318, 0.286, 0.252))
    rust = g.math("MULTIPLY", (ws, 1), g.noise(g.uvscale(tc, 4.0, 4.0), scale=1.0))
    rust = g.math("MULTIPLY", rust, 2.0, clamp=True)
    wcol = g.mix(rust, wcol, (0.352, 0.150, 0.058))
    g.lk(wcol, 0, b, 0)
    b.inputs[1].default_value = 0.85
    rgh = g.math("ADD", 0.30, g.math("MULTIPLY", (ws, 0), 0.30))
    rgh = g.math("ADD", rgh, g.math("MULTIPLY", rust, 0.25), clamp=True)
    g.lk(rgh, 0, b, 2)
    hh = g.math("MULTIPLY", t, t)
    hh = g.math("SUBTRACT", 1.0, hh, clamp=True)
    hh = g.math("SQRT", hh)
    bump = g.n("ShaderNodeBump", defaults={0: 1.0, 1: wire_d * 0.5})
    g.lk(hh, 0, bump, 3)
    g.lk(bump, 0, b, 6)

    tr = g.n("ShaderNodeBsdfTransparent")
    mixs = g.n("ShaderNodeMixShader")
    g.lk(alpha, 0, mixs, 0)
    g.lk(tr, 0, mixs, 1)
    g.lk(b, 0, mixs, 2)
    g.lk(mixs, 0, out, 0)
    return m


def mat_wire():
    m, g, b, _ = _new_mat("FenceWire")
    tc = g.n("ShaderNodeTexCoord")
    ws = g.sep(g.attr("wear"))
    col = g.mix((ws, 0), (0.585, 0.600, 0.612), (0.318, 0.286, 0.252))
    rust = g.math("MULTIPLY", (ws, 1),
                  g.noise(g.uvscale(tc, 30.0, 30.0), scale=1.0, detail=7.0))
    rust = g.math("MULTIPLY", rust, 2.1, clamp=True)
    col = g.mix(rust, col, (0.352, 0.150, 0.058))
    g.lk(col, 0, b, 0)
    b.inputs[1].default_value = 0.9
    rgh = g.math("ADD", 0.28, g.math("MULTIPLY", (ws, 0), 0.30))
    rgh = g.math("ADD", rgh, g.math("MULTIPLY", rust, 0.28), clamp=True)
    g.lk(rgh, 0, b, 2)
    return m


# --- 10.5 gravel, stones, runoff asphalt, rubber, belting -------------------

def mat_gravel():
    m, g, b, _ = _new_mat("Gravel")
    tc = g.n("ShaderNodeTexCoord")
    geo = tc
    sxyz = g.n("ShaderNodeSeparateXYZ")
    g.lk(tc, 2, sxyz, 0)                       # UV.x = 0 at the track-side lip
    ws = g.sep(g.attr("wear"))

    p1 = g.poscale(geo, 90.0)                  # ~11 mm stones
    p2 = g.poscale(geo, 26.0)                  # ~38 mm clumps
    p3 = g.poscale(geo, 2.6)                   # ~0.4 m patches: the scale that
    v1 = g.voro(p1, scale=1.0, rand=1.0)       # still resolves at 30 m and is
    v2 = g.voro(p2, scale=1.0, rand=0.95)      # what stops a trap reading as clay
    v3 = g.voro(p3, scale=1.0, rand=1.0)
    grit = g.noise(p1, scale=3.5, detail=9.0, rough=0.62)

    stone = g.ramp((v1, 1), [(0.00, (0.196, 0.166, 0.126)), (0.22, (0.300, 0.258, 0.196)),
                             (0.45, (0.232, 0.216, 0.192)), (0.68, (0.352, 0.300, 0.222)),
                             (0.86, (0.152, 0.134, 0.112)), (1.00, (0.392, 0.356, 0.302))])
    base = g.mix(0.30, stone, (v2, 1), "OVERLAY")
    base = g.mix(0.16, base, (grit, 1), "SOFT_LIGHT")
    # 0.4 m patchiness — clumping, sun-bleached vs turned-over gravel
    patch = g.ramp((v3, 1), [(0.00, (0.148, 0.130, 0.104)), (0.35, (0.286, 0.256, 0.204)),
                             (0.70, (0.212, 0.196, 0.170)), (1.00, (0.372, 0.340, 0.284))])
    base = g.mix(0.42, base, patch)
    base = g.mix(0.18, base, (v3, 0), "OVERLAY")
    base = g.mix(0.13, base, (0.462, 0.428, 0.366))            # dust film
    # macro life: damp patches, dragged/darkened lanes, rake albedo
    damp = g.noise(g.uvscale(tc, 0.16, 0.055), scale=1.0, detail=6.0, rough=0.6)
    damp = g.math("SUBTRACT", damp, 0.44, clamp=True)
    damp = g.math("MULTIPLY", damp, 2.2, clamp=True)
    base = g.mix(damp, base, (0.128, 0.112, 0.092))
    rake = g.math("PINGPONG", (sxyz, 0), 0.15)
    rake = g.math("DIVIDE", rake, 0.15)
    base = g.mix(g.math("MULTIPLY", rake, 0.13), base, (0.560, 0.522, 0.452))

    drag = g.n("ShaderNodeMapRange", clamp=True,
               defaults={1: 0.0, 2: 2.6, 3: 1.0, 4: 0.0})
    g.lk(sxyz, 0, drag, 0)
    drag = g.math("MULTIPLY", drag, 1.4, clamp=True)
    drag = g.math("MULTIPLY", drag, (ws, 2))
    drag = g.math("MULTIPLY", drag, 2.0, clamp=True)
    base = g.mix(drag, base, (0.118, 0.106, 0.092))
    g.lk(base, 0, b, 0)
    rgh = g.math("ADD", 0.72, g.math("MULTIPLY", grit, 0.20), clamp=True)
    g.lk(rgh, 0, b, 2)
    hb = g.math("MULTIPLY", v1, 0.62)
    hb = g.math("ADD", hb, g.math("MULTIPLY", v2, 0.30))
    hb = g.math("ADD", hb, g.math("MULTIPLY", grit, 0.10))
    bump = g.n("ShaderNodeBump", defaults={0: 0.85, 1: 0.010})
    g.lk(hb, 0, bump, 3)
    g.lk(bump, 0, b, 6)
    g.spec(b, 0.16)                 # dry limestone gravel
    return m


def mat_stone():
    m, g, b, _ = _new_mat("Stone")
    geo = g.n("ShaderNodeTexCoord")
    us = g.sep(g.attr("uid"))
    col = g.ramp((us, 0), [(0.00, (0.238, 0.214, 0.180)), (0.25, (0.372, 0.334, 0.276)),
                           (0.50, (0.286, 0.278, 0.266)), (0.75, (0.446, 0.400, 0.322)),
                           (1.00, (0.176, 0.164, 0.150))])
    n2 = g.noise(g.poscale(geo, 1.0), scale=260.0, detail=8.0, rough=0.6)
    base = g.mix(0.20, col, (n2, 1), "OVERLAY")
    g.lk(base, 0, b, 0)
    rgh = g.math("ADD", 0.70, g.math("MULTIPLY", n2, 0.22), clamp=True)
    g.lk(rgh, 0, b, 2)
    bump = g.n("ShaderNodeBump", defaults={0: 0.45, 1: 0.0025})
    g.lk(n2, 0, bump, 3)
    g.lk(bump, 0, b, 6)
    g.spec(b, 0.16)
    return m


def mat_runoff():
    m, g, b, _ = _new_mat("RunoffAsphalt")
    geo = g.n("ShaderNodeTexCoord")
    ws = g.sep(g.attr("wear"))
    p1 = g.poscale(geo, 70.0)
    p2 = g.poscale(geo, 7.0)
    agg = g.voro(p1, scale=1.0, rand=1.0)
    blotch = g.noise(p2, scale=1.0, detail=9.0, rough=0.6)
    big = g.noise(g.poscale(geo, 1.0), scale=0.09, detail=6.0, rough=0.55)
    base = g.ramp((agg, 1), [(0.00, (0.080, 0.077, 0.074)), (0.40, (0.112, 0.109, 0.103)),
                             (0.72, (0.091, 0.089, 0.088)), (1.00, (0.141, 0.136, 0.128))])
    base = g.mix(0.28, base, (blotch, 1), "OVERLAY")
    base = g.mix(0.22, base, (big, 1), "SOFT_LIGHT")
    sc = g.math("MULTIPLY", (ws, 2), blotch)
    sc = g.math("MULTIPLY", sc, 1.8, clamp=True)
    base = g.mix(sc, base, (0.058, 0.055, 0.053))
    g.lk(base, 0, b, 0)
    rgh = g.math("ADD", 0.66, g.math("MULTIPLY", agg, 0.26), clamp=True)
    g.lk(rgh, 0, b, 2)
    hb = g.math("MULTIPLY", agg, 0.7)
    hb = g.math("ADD", hb, g.math("MULTIPLY", blotch, 0.3))
    bump = g.n("ShaderNodeBump", defaults={0: 0.30, 1: 0.0035})
    g.lk(hb, 0, bump, 3)
    g.lk(bump, 0, b, 6)
    g.spec(b, 0.22)                 # dry unrubbered runoff asphalt
    return m


def mat_verge():
    """The trackside verge — the ground from the runoff programme out to
    `platform_edge`, i.e. 237 960 m2 of what the user called "a grass gray line".

    It is 68 % of every wide frame of the flying lap, so it is built to be looked
    at.  Three things stop it reading as a flat ribbon:

      1. DRYNESS IS A FIELD ALONG THE LAP.  UV.y is the station in metres, so a
         30 m and a 95 m noise put whole stretches into drought and whole
         stretches into shade.  Nothing here is a per-square-metre average.
      2. THE CROSS-SECTION IS A REAL ONE.  UV.x is metres outboard of the painted
         verge: the first 2.5 m is scalped and rubber-flecked because cars run
         over it, the middle is mown turf, and the last few metres before the
         barrier are a compacted aggregate service strip with a mown edge —
         `wear.B` carries the distance to the barrier line.
      3. TUSSOCKS, NOT NOISE.  A voronoi at clump scale drives BOTH colour and
         bump, so the relief and the colour belong to the same clumps; at a 12.47
         deg sun that is what makes turf read as turf rather than as a green
         plane.

    Albedo check (contract §8): the mown-turf base sits at ~0.115 linear mean and
    the aggregate strip at ~0.205, so a patch of each renders at
    lambert_radiance(0.115) and lambert_radiance(0.205) respectively.
    """
    m, g, b, _ = _new_mat("Verge")
    tc = g.n("ShaderNodeTexCoord")
    uvs = g.n("ShaderNodeSeparateXYZ")
    g.lk(tc, 2, uvs, 0)                          # UV.x = m out, UV.y = station
    ws = g.sep(g.attr("wear"))                   # .B = nearness to the barrier

    # --- where along the lap: drought / shade, on two long wavelengths -------
    # Centred, NOT gained: an earlier version multiplied this by 1.55 and
    # clamped, which pinned 60 % of the lap to full drought and made the whole
    # verge one straw palette.  Measured at 0.542/0.484/0.397 display, R > G,
    # for something that is supposed to be grass.
    dry_a = g.noise(g.uvscale(tc, 0.0, 1.0 / 95.0), scale=1.0, detail=5.0, rough=0.55)
    dry_b = g.noise(g.uvscale(tc, 0.010, 1.0 / 29.0), scale=1.0, detail=6.0, rough=0.6)
    dry = g.n("ShaderNodeMapRange", clamp=True,
              defaults={1: 0.30, 2: 0.72, 3: 0.06, 4: 0.94})
    g.lk(g.mix(0.45, (dry_a, 0), (dry_b, 0)), 0, dry, 0)

    # --- clumps.  NOTE the outputs: a Voronoi's socket 1 is COLOUR, a random
    # RGB per cell.  Mixing that in as a colour is what put 3 m pink and mauve
    # blotches all over the first build of this material.  Cell randomness is
    # only ever taken as a SCALAR here (socket 0 = distance, or the colour run
    # through a ramp), so the palette stays the one written below.
    pc = g.poscale(tc, 3.4)                      # ~0.3 m tussocks
    pm = g.poscale(tc, 0.30)                     # ~3.3 m patches
    pf = g.poscale(tc, 26.0)                     # ~4 cm blade grain
    vcd = g.voro(pc, scale=1.0, rand=1.0)        # distance -> clump shape
    vcid = g.ramp((g.voro(pc, scale=1.0, rand=1.0), 1),
                  [(0.0, (0.0, 0.0, 0.0)), (1.0, (1.0, 1.0, 1.0))])   # cell id
    fine = g.noise(pf, scale=2.4, detail=9.0, rough=0.62)
    med = g.noise(pm, scale=2.0, detail=8.0, rough=0.58)
    fld = g.mix(0.55, (med, 0), vcid)            # per-clump + patch, as a scalar

    green = g.ramp(fld, [(0.00, (0.0425, 0.0645, 0.0270)),
                         (0.30, (0.0735, 0.1075, 0.0395)),
                         (0.62, (0.0580, 0.0880, 0.0330)),
                         (1.00, (0.1045, 0.1385, 0.0535))])
    straw = g.ramp(fld, [(0.00, (0.1665, 0.1425, 0.0805)),
                         (0.30, (0.2290, 0.1975, 0.1115)),
                         (0.62, (0.1880, 0.1620, 0.0915)),
                         (1.00, (0.2740, 0.2370, 0.1400))])
    turf = g.mix(dry, green, straw)
    turf = g.mix(0.14, turf, (fine, 0), "SOFT_LIGHT")
    # bare scrapes worn through to subsoil, on the patch scale
    bare = g.n("ShaderNodeMapRange", clamp=True,
               defaults={1: 0.62, 2: 0.86, 3: 0.0, 4: 1.0})
    g.lk(med, 0, bare, 0)
    bare = g.math("MULTIPLY", bare, g.math("ADD", 0.30,
                                           g.math("MULTIPLY", dry, 0.70)), clamp=True)
    turf = g.mix(bare, turf, (0.1355, 0.1115, 0.0820))

    # --- the scalped strip against the painted verge ------------------------
    # cars run over the first couple of metres; it is short, dusty and flecked
    # with rubber, and it is the band the onboard camera actually sees.
    sc = g.n("ShaderNodeMapRange", clamp=True,
             defaults={1: 0.0, 2: 2.6, 3: 1.0, 4: 0.0})
    g.lk(uvs, 0, sc, 0)
    turf = g.mix(g.math("MULTIPLY", sc, 0.70, clamp=True), turf, (0.1075, 0.0975, 0.0765))
    rub = g.math("MULTIPLY", sc, g.math("SUBTRACT", (fine, 0), 0.42, clamp=True))
    turf = g.mix(g.math("MULTIPLY", rub, 1.7, clamp=True), turf, (0.0300, 0.0288, 0.0280))

    # --- the compacted service strip along the barrier ----------------------
    strip = g.math("SUBTRACT", (ws, 2), 0.30, clamp=True)
    strip = g.math("MULTIPLY", strip, 1.45, clamp=True)
    aggid = g.ramp((g.voro(g.poscale(tc, 44.0), scale=1.0, rand=1.0), 1),
                   [(0.0, (0.0, 0.0, 0.0)), (1.0, (1.0, 1.0, 1.0))])
    agg = g.ramp(aggid, [(0.00, (0.1525, 0.1405, 0.1230)),
                         (0.35, (0.2275, 0.2090, 0.1795)),
                         (0.70, (0.1835, 0.1710, 0.1510)),
                         (1.00, (0.2640, 0.2445, 0.2090))])
    agg = g.mix(0.20, agg, (fine, 0), "SOFT_LIGHT")
    base = g.mix(strip, turf, agg)
    # a mown/compacted edge line so the strip has a boundary, not a gradient
    edge = g.math("MULTIPLY", strip, g.math("SUBTRACT", 1.0, strip))
    base = g.mix(g.math("MULTIPLY", edge, 1.1, clamp=True), base, (0.0960, 0.0920, 0.0680))
    g.lk(base, 0, b, 0)

    rgh = g.math("SUBTRACT", 0.94, g.math("MULTIPLY", strip, 0.10))
    rgh = g.math("SUBTRACT", rgh, g.math("MULTIPLY", (fine, 0), 0.10), clamp=True)
    g.lk(rgh, 0, b, 2)

    # Bump: mostly the 4 cm blade grain, only a third the clump shape.  The
    # first build drove it 55 % from a raw voronoi distance, whose hard cell
    # borders read as a polygonal patchwork at 20 m.
    hb = g.math("MULTIPLY", (fine, 0), 0.52)
    hb = g.math("ADD", hb, g.math("MULTIPLY", g.math("POWER", vcd, 0.55), 0.30))
    hb = g.math("ADD", hb, g.math("MULTIPLY", (med, 0), 0.18))
    bump = g.n("ShaderNodeBump", defaults={0: 0.55, 1: 0.014})
    g.lk(hb, 0, bump, 3)
    g.lk(bump, 0, b, 6)
    g.spec(b, 0.10)                 # turf, not a wet dielectric
    return m


def mat_rubber():
    m, g, b, _ = _new_mat("Tyre")
    geo = g.n("ShaderNodeTexCoord")
    ws = g.sep(g.attr("wear"))
    n1 = g.noise(g.poscale(geo, 1.0), scale=180.0, detail=8.0, rough=0.6)
    n2 = g.noise(g.poscale(geo, 1.0), scale=14.0, detail=6.0, rough=0.55)
    base = g.mix(0.35, (0.0165, 0.0162, 0.0160), (0.0295, 0.0288, 0.0282))
    tint = g.math("MULTIPLY", (ws, 0), 0.65, clamp=True)
    base = g.mix(tint, base, (0.128, 0.120, 0.108))
    base = g.mix(0.18, base, (n2, 1), "OVERLAY")
    g.lk(base, 0, b, 0)
    rgh = g.math("ADD", 0.52, g.math("MULTIPLY", n1, 0.22))
    rgh = g.math("ADD", rgh, g.math("MULTIPLY", (ws, 0), 0.16), clamp=True)
    g.lk(rgh, 0, b, 2)
    bump = g.n("ShaderNodeBump", defaults={0: 0.35, 1: 0.0018})
    g.lk(n1, 0, bump, 3)
    g.lk(bump, 0, b, 6)
    return m


def mat_belt():
    m, g, b, _ = _new_mat("Belt")
    tc = g.n("ShaderNodeTexCoord")
    ws = g.sep(g.attr("wear"))
    weave = g.noise(g.uvscale(tc, 60.0, 8.0), scale=1.0, detail=7.0, rough=0.6)
    grime = g.noise(g.uvscale(tc, 2.2, 2.2), scale=1.0, detail=8.0)
    base = g.mix(0.25, (0.0180, 0.0178, 0.0175), (0.0402, 0.0392, 0.0380))
    base = g.mix(0.2, base, (weave, 1), "OVERLAY")
    base = g.mix(g.math("MULTIPLY", (ws, 0), 0.45, clamp=True), base, (0.098, 0.092, 0.082))
    g.lk(base, 0, b, 0)
    rgh = g.math("ADD", 0.62, g.math("MULTIPLY", grime, 0.2), clamp=True)
    g.lk(rgh, 0, b, 2)
    bump = g.n("ShaderNodeBump", defaults={0: 0.22, 1: 0.0016})
    g.lk(weave, 0, bump, 3)
    g.lk(bump, 0, b, 6)
    return m


def build_materials():
    return {
        "steel": mat_steel(), "tecpro": mat_tecpro(), "concrete": mat_concrete(),
        "fenceV": mat_fence("V"), "fenceH": mat_fence("H"), "wire": mat_wire(),
        "gravel": mat_gravel(), "stone": mat_stone(), "runoff": mat_runoff(),
        "rubber": mat_rubber(), "belt": mat_belt(), "verge": mat_verge(),
    }

# ----------------------------------------------------------------------------
# 11.  THE DATUM  —  imported, not invented
# ----------------------------------------------------------------------------
#
# What used to be here:
#
#     z = elevation_c(s) + (-0.016) * max(0, lat - verge_edge(s))
#
# — no crown, no banking, and unsigned in `lat`, so it could not have carried
# banking even if someone had added it: banking is antisymmetric in u and this
# signature threw the sign away.  Measured against the truth at the verge edge,
# every 5 m round the lap: min -0.680 m, max +0.691 m, p95 |0.49| m.  That sank
# 90.1 % of the barrier line (mean 0.72 m, against an ARMCO_TOP of 1.012 m) and
# put 50 555 m2 of runoff asphalt and 42 419 m2 of gravel under dirt.
#
# What is here now is one line, and `side` is not optional in practice: leave it
# out and a lateral is read as SIGNED, so an unsigned distance silently becomes
# "left of travel".  Every call site in this module passes it.

PLATFORM_FALL = WC.PLATFORM_FALL          # -0.016, for reference only
BASE_EMBED = WC.BASE_EMBED_M              # 0.020 — everything standing embeds


def ground_z(s, lat, side=None):
    """THE ground datum.  `world_contract.ground_z`.

    ground_z(s, lat, side) == ground_z(s, side * lat).  Carries crown, banking,
    undulation, the negative kerbs, the verge drain and the -1.6 % runoff fall
    measured FROM THE BANKED ROAD EDGE.
    """
    return WC.ground_z(s, lat, side)


def W3(P):
    """design (...,3) -> world (...,3)"""
    P = np.asarray(P, dtype=np.float64)
    sh = P.shape
    F = P.reshape(-1, 3)
    wx, wy = CL.to_world(F[:, 0], F[:, 1])
    return np.stack([wx, wy, F[:, 2]], axis=1).reshape(sh)


# ----------------------------------------------------------------------------
# 12.  the barrier line: envelope -> panel nodes -> straightened runs
# ----------------------------------------------------------------------------

PANEL_L = 4.00           # nominal W-beam panel
POST_PITCH = 2.00        # Armco post centres
FENCE_SPAN = 8.00        # catch-fence post centres (spec §9)
FENCE_POST_H = 6.00      # total post length (spec §9)
FENCE_EMBED = 1.20
RAIL_HZ3 = [0.080, 0.390, 0.700]      # three W-beams -> 1.012 m, FIA-legal height
RAIL_HZ2 = [0.150, 0.560]
ARMCO_TOP = 1.012
MESH_Z0, MESH_Z1 = 1.05, 4.65         # 3.60 m of mesh (spec §9)


def rail_count(s, side):
    """3-beam is standard; quieter infield stretches carry 2.  Piecewise
    constant on ~70 m blocks so it never changes inside a panel."""
    blk = np.floor(np.asarray(s) / 70.0).astype(np.int64)
    r = hash01(blk, np.full(blk.shape, 6100 + (side > 0)))
    return np.where((r < 0.30) & (side > 0), 2, 3)


def barrier_nodes(side):
    """Panel-node polyline for one side of the circuit."""
    ds = 0.5
    s = np.arange(0.0, LAP_LEN, ds)
    lat_j, ver_j = HIST.align(s, side)
    # contract: build_barriers MAY add bounded lateral history jitter to the
    # barrier line so it is not a drawing-board curve; nobody else may, and it
    # is capped at BARRIER_JITTER_MAX_M.
    lat_j = np.clip(lat_j, -WC.BARRIER_JITTER_MAX_M, WC.BARRIER_JITTER_MAX_M)
    off = barrier_offset(s, side) + lat_j
    x, y, _ = CL.point(s, off, side, bank=False)
    z = ground_z(s, off, side) + ver_j
    P = np.stack([x, y, z], axis=1)
    Pc = np.vstack([P, P[:1]])
    seg = np.linalg.norm(np.diff(Pc, axis=0)[:, :2], axis=1)
    L = np.concatenate([[0.0], np.cumsum(seg)])
    total = float(L[-1])
    sc = np.concatenate([s, [LAP_LEN]])

    nodes_L, k = [0.0], 0
    while nodes_L[-1] < total - 1.6:
        p = PANEL_L * (0.965 + 0.070 * h01(4400 + (side > 0), k, 3))
        nodes_L.append(nodes_L[-1] + p)
        k += 1
    nodes_L = np.array(nodes_L)
    nodes_L[-1] = total
    N = np.stack([np.interp(nodes_L, L, Pc[:, i]) for i in range(3)], axis=1)
    NS = np.interp(nodes_L, L, sc)

    # --- straighten low-curvature stretches into genuine straight runs -----
    d = np.diff(N[:, :2], axis=0)
    hd = np.unwrap(np.arctan2(d[:, 1], d[:, 0]))
    m = len(hd)
    runs, i = [], 0
    while i < m:
        j = i + 1
        while (j < m and abs(hd[j] - hd[i]) < math.radians(0.85)
               and (nodes_L[j + 1] - nodes_L[i]) < 130.0):
            j += 1
        runs.append((i, j))
        i = j
    for (a, b) in runs:
        if b - a >= 3:
            t = (nodes_L[a:b + 1] - nodes_L[a]) / max(1e-9, nodes_L[b] - nodes_L[a])
            for c in range(2):
                N[a:b + 1, c] = N[a, c] + (N[b, c] - N[a, c]) * t
    # a small alignment step at every run joint — barriers never line up exactly
    for ri, (a, b) in enumerate(runs):
        j = (h01(4700 + (side > 0), ri, 9) - 0.5) * 0.055
        nx, ny = CL.normal(NS[a], side)
        N[a:b + 1, 0] += float(nx) * j
        N[a:b + 1, 1] += float(ny) * j

    return dict(P=N, s=NS, L=nodes_L, runs=runs, side=side, total=total,
                npanel=len(nodes_L) - 1)


def node_attrs(s, side):
    """(wear RGBA, paint RGBA, dent m, fresh flag) for stations `s`."""
    s = np.atleast_1d(np.asarray(s, dtype=np.float64))
    age = HIST.age_at(s, side)
    dent, scuff, pmix, prgb, fresh = HIST.scars(s, side)
    age = np.where(fresh > 0.5, 0.04 + 0.06 * vnoise1(s * 0.7, 61), age)
    rust = clamp01((age - 0.40) * 1.75 + 0.25 * scuff
                   + 0.34 * (fbm1(s / 11.0, seed=1201, oct=3) - 0.5))
    wear = np.stack([age, rust, scuff, pmix], axis=-1)
    paint = np.concatenate([prgb, np.ones(prgb.shape[:-1] + (1,))], axis=-1)
    return wear, paint, dent, fresh


def run_paint(rid):
    """Is this maintenance run PAINTED, and which fictional colour?
    One definition, used by rails and posts alike so they always agree."""
    rid = np.atleast_1d(np.asarray(rid)).astype(np.int64)
    flag = (hash01(rid, np.full(rid.shape, 4441)) < 0.30).astype(np.float64)
    hue = hash01(rid, np.full(rid.shape, 4457))
    return flag, hue


# ----------------------------------------------------------------------------
# 13.  W-beam rails, posts and bolts
# ----------------------------------------------------------------------------
#  profile coords: (t = away from the track, v = up from the rail bottom)

WBEAM_F = np.array([
    (0.0760, 0.0000), (0.0300, 0.0215), (0.0050, 0.0545), (0.0000, 0.0900),
    (0.0050, 0.1255), (0.0520, 0.1560), (0.0050, 0.1865), (0.0000, 0.2220),
    (0.0050, 0.2575), (0.0300, 0.2905), (0.0760, 0.3120)])
WBEAM_T = 0.0032


def wbeam_segments():
    F = WBEAM_F
    B = F + np.array([WBEAM_T, 0.0])
    return [(F, True), (B[::-1], True),
            (np.array([F[-1], B[-1]]), False), (np.array([B[0], F[0]]), False)]


def _sweep_strip(mb, P, prof, sgn, mat, smooth, uv_u, uv_v0, wear, paint, uid,
                 vscale=None):
    pr = prof.copy()
    pr[:, 0] *= sgn
    sc = None
    if vscale is not None:
        sc = np.stack([np.ones(len(P)), vscale], axis=1)
    G = sweep(P, pr, scale=sc)
    n, k = G.shape[0], G.shape[1]
    f = ring_faces(n, k, closed=False)
    uv = np.stack([np.repeat(uv_u, k), np.tile(uv_v0 + prof[:, 1], n)], axis=1)
    mb.add(W3(G).reshape(-1, 3), f, mat=mat, uv=uv,
           wear=np.repeat(wear, k, axis=0), paint=np.repeat(paint, k, axis=0),
           uid=np.repeat(uid, k, axis=0), smooth=smooth)
    return G


def build_armco(mb, nd, i0, i1, tier):
    """Armco panels i0..i1 for one chunk.  Returns unit count."""
    P, S, L, side = nd["P"], nd["s"], nd["L"], nd["side"]
    sgn = -float(side)                     # +1 * sgn * R  ==  away from the track
    if i1 - i0 < 1:
        return 0
    pan_s = 0.5 * (S[i0:i1] + S[i0 + 1:i1 + 1])
    _, _, pan_dent, _ = node_attrs(pan_s, side)
    pan_hero = hero_tier(pan_s, side)
    rc = rail_count(pan_s, side)

    units = 0
    g0 = 0
    groups = []
    for gi in range(1, len(rc) + 1):
        if gi == len(rc) or rc[gi] != rc[g0]:
            groups.append((g0, gi))
            g0 = gi
    for (a, b) in groups:
        heights = RAIL_HZ3 if rc[a] == 3 else RAIL_HZ2
        ja, jb = i0 + a, i0 + b
        ts, ss_, frac = [], [], []
        for j in range(ja, jb):
            sub = 10 if (pan_dent[j - i0] > 0.02 or pan_hero[j - i0] >= 1) else 4
            for q in range(sub):
                f = q / sub
                ts.append(L[j] + (L[j + 1] - L[j]) * f)
                ss_.append(S[j] + (S[j + 1] - S[j]) * f)
                frac.append(f)
        ts.append(L[jb]); ss_.append(S[jb]); frac.append(1.0)
        ts = np.array(ts); ss_ = np.array(ss_); frac = np.array(frac)
        C = np.stack([np.interp(ts, L, P[:, c]) for c in range(3)], axis=1)
        wear, paint, dent, fresh = node_attrs(ss_, side)
        tin = (ts % POST_PITCH) / POST_PITCH
        hold = np.sin(np.pi * np.clip(tin, 0, 1)) ** 0.6
        lat = dent * (0.55 + 0.45 * hold) * (0.60 + 0.80 * vnoise1(ts * 0.9, 331))
        lat += 0.004 * smoothstep(0.93, 1.0, frac)      # panel lap, at real joints
        vert = -0.006 * hold * (0.4 + 0.9 * vnoise1(ts * 0.31 + 17.0, 337))
        T, R, U = frames_from_polyline(C)
        Cd = C + R * (sgn * lat)[:, None] + U * vert[:, None]
        crush = 1.0 - np.clip(dent * 1.4, 0.0, 0.28)
        # uid.G selects a PAINTED run (many circuits paint their Armco);
        # uid.B picks which fictional paint.  Constant per maintenance run, so
        # the change always lands on a run joint, never mid-panel.
        painted, phue = run_paint(HIST.run_id(ss_, side))
        uid = np.stack([hash01(np.rint(ss_ / 4.0).astype(np.int64),
                               np.full(len(ss_), 21)),
                        painted, phue, np.ones(len(ss_))], axis=1)
        for hz in heights:
            base = Cd + U * hz
            ends = {}
            for si, (prof, sm) in enumerate(wbeam_segments()):
                Gs = _sweep_strip(mb, base, prof, sgn, 0, sm, ts, hz, wear, paint,
                                  uid, vscale=crush)
                if si < 2:
                    ends[si] = Gs
            # close the open ends of the rail run, otherwise the sweep leaves a
            # sawtooth silhouette wherever a run terminates
            if 0 in ends and 1 in ends:
                Gf, Gb = ends[0], ends[1]
                kk = Gf.shape[1]
                for e, wq in ((0, 0), (-1, len(ts) - 1)):
                    Vc = np.vstack([Gf[e], Gb[e][::-1]])
                    i = np.arange(kk - 1)
                    fq = np.stack([i, i + 1, kk + i + 1, kk + i], axis=-1)
                    if e == 0:
                        fq = fq[:, ::-1]
                    mb.add(W3(Vc), fq, mat=0, smooth=False,
                           uv=np.tile([[0.0, hz]], (2 * kk, 1)),
                           wear=np.tile(wear[wq], (2 * kk, 1)),
                           paint=np.tile(paint[wq], (2 * kk, 1)),
                           uid=np.tile(uid[wq], (2 * kk, 1)))
        units += (jb - ja)
        units += build_bolts(mb, C, ts, ss_, L, ja, jb, side, heights, T, R, U,
                             sgn, tier)
    units += build_armco_posts(mb, P, S, L, side, sgn, i0, i1)
    return units


def _post_profile(kind, w=0.150, d=0.078, t=0.006):
    hw, hd = w * 0.5, d * 0.5
    if kind == 0:      # C channel
        p = [(-hd, -hw), (hd, -hw), (hd, -hw + t), (-hd + t, -hw + t),
             (-hd + t, hw - t), (hd, hw - t), (hd, hw), (-hd, hw)]
    elif kind == 1:    # I section
        p = [(-hd, -hw), (hd, -hw), (hd, -hw + t), (t * 0.6, -hw + t),
             (t * 0.6, hw - t), (hd, hw - t), (hd, hw), (-hd, hw),
             (-hd, hw - t), (-t * 0.6, hw - t), (-t * 0.6, -hw + t), (-hd, -hw + t)]
    else:              # RHS
        p = [(-hd, -hw), (hd, -hw), (hd, hw), (-hd, hw)]
    return np.array(p, dtype=np.float64)


def _local_frame(P, L, u, side):
    c = np.array([np.interp(u, L, P[:, k]) for k in range(3)])
    du = (np.array([np.interp(u + 1.0, L, P[:, k]) for k in range(3)]) -
          np.array([np.interp(u - 1.0, L, P[:, k]) for k in range(3)]))
    T = du / max(1e-9, np.linalg.norm(du))
    R = np.array([T[1], -T[0], 0.0])
    R /= max(1e-9, np.linalg.norm(R))
    return c, T, R


def build_armco_posts(mb, P, S, L, side, sgn, i0, i1):
    a, bnd = L[i0], L[i1]
    cnt = 0
    for pi in range(math.ceil(a / POST_PITCH), int(bnd / POST_PITCH) + 1):
        u = pi * POST_PITCH
        if u < a or u > bnd:
            continue
        c, T, R = _local_frame(P, L, u, side)
        A = sgn * R                                  # away from the track
        sj = float(np.interp(u, L, S))
        seed = 5300 + (side > 0)
        r = h01(seed, pi, 3)
        kind = 0 if r < 0.55 else (1 if r < 0.85 else 2)
        w = 0.150 * (0.92 + 0.16 * h01(seed, pi, 7))
        prof = _post_profile(kind, w=w)
        top = 1.012 + 0.030 + 0.05 * h01(seed, pi, 11)
        bot = -0.95
        wear, paint, dent, fresh = node_attrs(np.array([sj]), side)
        lean_a = (h01(seed, pi, 13) - 0.5) * math.radians(3.4)
        lean_b = (h01(seed, pi, 17) - 0.5) * math.radians(2.2)
        if dent[0] > 0.06:
            lean_a += math.radians(9.0 + 34.0 * float(dent[0]))
        yaw = (h01(seed, pi, 19) - 0.5) * math.radians(6.0)
        ca, sa = math.cos(yaw), math.sin(yaw)
        Ta, Aa = T * ca + A * sa, A * ca - T * sa
        axis = np.array([0.0, 0.0, 1.0]) + Aa * math.tan(lean_a) + Ta * math.tan(lean_b)
        axis /= np.linalg.norm(axis)
        base = c + A * 0.094   # post face on the W-beam valley, no z-fight
        G = np.zeros((2, len(prof), 3))
        for si, hgt in enumerate((bot, top)):
            G[si] = (base + axis * hgt) + prof[:, 0][:, None] * Ta + prof[:, 1][:, None] * Aa
        f = ring_faces(2, len(prof), closed=True)
        n = 2 * len(prof)
        uv = np.stack([np.tile(prof[:, 0] * 6.0, 2),
                       np.repeat([bot, top], len(prof))], axis=1)
        pf, ph_ = run_paint(HIST.run_id(np.array([sj]), side))
        pflag, phue = float(pf[0]), float(ph_[0])
        mb.add(W3(G).reshape(-1, 3), f, mat=0, uv=uv,
               wear=np.repeat(wear, n, axis=0), paint=np.repeat(paint, n, axis=0),
               uid=np.tile([r, pflag, phue, 1.0], (n, 1)), smooth=False)
        if h01(seed, pi, 29) < 0.45:
            v, fq = box(0, 0, 0, w * 1.12, 0.098, 0.008)
            M = np.stack([Ta, Aa, axis], axis=1)
            v = (v @ M.T) + (base + axis * (top + 0.004))
            mb.add(W3(v), fq, mat=0, wear=np.repeat(wear, 8, axis=0),
                   paint=np.repeat(paint, 8, axis=0), smooth=False,
                   uv=np.zeros((8, 2)), uid=np.tile([r, 0, 0, 1], (8, 1)))
        cnt += 1
    return cnt


_HEX = np.linspace(0, 2 * math.pi, 6, endpoint=False) + math.pi / 6
_HEXCAP = np.array([[6, 7, 8, 9], [9, 10, 11, 6]])


def build_bolts(mb, C, ts, ss_, L, ja, jb, side, heights, T, R, U, sgn, tier):
    if tier < 1:
        return 0
    cnt = 0
    for li, j in enumerate(range(ja, jb + 1)):
        u = L[j]
        k = int(np.clip(np.searchsorted(ts, u), 1, len(ts) - 1))
        c, Tv, Rv, Uv = C[k], T[k], sgn * R[k], U[k]
        wear, paint, _, _ = node_attrs(np.array([float(ss_[k])]), side)
        for hi, hz in enumerate(heights):
            for dv in (0.156,):            # the W-beam bolt line is the valley
                for du in (-0.30, -0.11, 0.11, 0.30):
                    r = h01(6600 + (side > 0), li * 97 + hi * 7, int(dv * 1000) + int(du * 100))
                    if r < 0.035:
                        continue
                    rad = 0.0092 * (0.9 + 0.2 * r)
                    o = c + Uv * (hz + dv) + Tv * du - Rv * 0.0055
                    ring0 = o + (np.cos(_HEX)[:, None] * Uv + np.sin(_HEX)[:, None] * Tv) * rad
                    ring1 = ring0 - Rv * 0.011
                    V = np.vstack([ring0, ring1])
                    f = np.vstack([ring_faces(2, 6, closed=True), _HEXCAP])
                    mb.add(W3(V), f, mat=0, smooth=False,
                           wear=np.repeat(wear, 12, axis=0),
                           paint=np.repeat(paint, 12, axis=0),
                           uv=np.zeros((12, 2)), uid=np.tile([r, 0, 0, 1], (12, 1)))
                    cnt += 1
    return cnt


# ----------------------------------------------------------------------------
# 14.  debris (catch) fencing
# ----------------------------------------------------------------------------
#  posts + rakers + top rail + tension cables are real geometry.
#  The weave itself is a two-layer surface (vertical wire sheet 4.5 mm in front
#  of the horizontal wire sheet, which is what a woven mesh physically is), each
#  layer carrying the analytic weave shader.  In the declared wire windows the
#  weave is real 3-D wire geometry instead.

I_SECTION = np.array([
    (-0.076, -0.076), (0.076, -0.076), (0.076, -0.066), (0.006, -0.066),
    (0.006, 0.066), (0.076, 0.066), (0.076, 0.076), (-0.076, 0.076),
    (-0.076, 0.066), (-0.006, 0.066), (-0.006, -0.066), (-0.076, -0.066)])


def _span_shape(u01, v01, sag, bow, droop, dent_c, dent_a):
    """out-of-plane bow (m) and vertical droop for the mesh sheet."""
    b = bow * np.sin(np.pi * u01) * (0.35 + 0.65 * np.sin(np.pi * v01) ** 0.7)
    b += sag * np.sin(np.pi * u01) ** 1.6 * v01
    b += dent_a * np.exp(-0.5 * (((u01 - dent_c) / 0.16) ** 2 +
                                 ((v01 - 0.45) / 0.30) ** 2))
    dz = -droop * np.sin(np.pi * u01) * v01 ** 1.4
    return b, dz


def build_fence(mb_struct, mb_mesh, nd, i0, i1, tier, stats):
    """Catch fence over the same node polyline; spans on FENCE_SPAN centres."""
    P, S, L, side = nd["P"], nd["s"], nd["L"], nd["side"]
    sgn = -float(side)
    a, bnd = L[i0], L[i1]
    seed = 7200 + (side > 0)
    first = math.ceil(a / FENCE_SPAN)
    last = int(bnd / FENCE_SPAN)
    total = float(L[-1])
    posts = []
    ghost = set()
    # one GHOST post past the chunk end so the boundary span is built exactly
    # once (by this chunk) rather than dropped by both.
    rng = list(range(first, last + 1))
    if (last + 1) * FENCE_SPAN <= total:
        rng.append(last + 1)
        ghost.add(last + 1)
    for pi in rng:
        u = pi * FENCE_SPAN
        sj = float(np.interp(u, L, S))
        if not bool(cor_get("fence", np.array([sj]), side)[0]):
            posts.append(None)
            continue
        c, T, R = _local_frame(P, L, u, side)
        A = sgn * R
        lean = (h01(seed, pi, 3) - 0.5) * math.radians(2.6)
        yaw = (h01(seed, pi, 5) - 0.5) * math.radians(4.0)
        hgt = (FENCE_POST_H - FENCE_EMBED) * (0.985 + 0.03 * h01(seed, pi, 7))
        ca, sa = math.cos(yaw), math.sin(yaw)
        Ta, Aa = T * ca + A * sa, A * ca - T * sa
        axis = np.array([0.0, 0.0, 1.0]) + Aa * math.tan(lean)
        axis /= np.linalg.norm(axis)
        base = c + A * 0.310   # clear of the Armco post line
        posts.append(dict(u=u, s=sj, base=base, axis=axis, T=Ta, A=Aa, h=hgt, pi=pi,
                          ghost=(pi in ghost)))

    for p in posts:
        if p is None or p["ghost"]:
            continue
        seedp = seed * 3 + p["pi"]
        wear, paint, _, _ = node_attrs(np.array([p["s"]]), side)
        sw = 0.152 * (0.95 + 0.12 * h01(seedp, 11))
        prof = I_SECTION * (sw / 0.152)
        G = np.zeros((2, len(prof), 3))
        for si, hgt in enumerate((-FENCE_EMBED * 0.35, p["h"])):
            G[si] = (p["base"] + p["axis"] * hgt) + \
                prof[:, 0][:, None] * p["T"] + prof[:, 1][:, None] * p["A"]
        f = ring_faces(2, len(prof), closed=True)
        n = 2 * len(prof)
        uv = np.stack([np.tile(prof[:, 0] * 5.0, 2),
                       np.repeat([0.0, p["h"]], len(prof))], axis=1)
        mb_struct.add(W3(G).reshape(-1, 3), f, mat=0, uv=uv,
                      wear=np.repeat(wear, n, axis=0),
                      paint=np.repeat(paint, n, axis=0),
                      uid=np.tile([h01(seedp, 13), 0, 0, 1], (n, 1)), smooth=False)
        stats["fence_posts"] += 1
        # concrete pad + base plate on roughly half of them.  The pad is 90 mm
        # thick and seated 65 mm INTO the platform rather than 2 mm above the
        # barrier line: the post stands 0.31 m outboard of that line, where the
        # platform is ~20 mm lower (the -1.6 % fall plus the graded maintenance
        # strip), and a 12.5 deg sun turns a 20 mm float into a 90 mm lit gap.
        if h01(seedp, 17) < 0.5:
            v, fq = box(0, 0, 0, 0.42, 0.42, 0.090)
            M = np.stack([p["T"], p["A"], p["axis"]], axis=1)
            mb_struct.add(W3((v @ M.T) + p["base"] - p["axis"] * 0.020), fq, mat=0,
                          wear=np.repeat(wear, 8, axis=0),
                          paint=np.repeat(paint, 8, axis=0), smooth=False,
                          uv=np.zeros((8, 2)), uid=np.tile([0.4, 0, 0, 1], (8, 1)))
        # back stay on every 4th-7th post
        if p["pi"] % (4 + int(3 * h01(seedp, 19))) == 0:
            foot = p["base"] + p["A"] * 2.1
            foot[2] = p["base"][2] - 0.15
            head = p["base"] + p["axis"] * (p["h"] * 0.62)
            TT = tube(np.linspace(foot, head, 4), 0.030, seg=6)
            mb_struct.add(W3(TT).reshape(-1, 3), ring_faces(4, 6, closed=True), mat=0,
                          wear=np.repeat(wear, 24, axis=0),
                          paint=np.repeat(paint, 24, axis=0), smooth=True,
                          uv=np.zeros((24, 2)),
                          uid=np.tile([h01(seedp, 23), 0, 0, 1], (24, 1)))

    # ---- spans -----------------------------------------------------------
    for k in range(len(posts) - 1):
        p0, p1 = posts[k], posts[k + 1]
        if p0 is None or p1 is None:
            continue
        if is_gate_span(0.5 * (p0["s"] + p1["s"]), side):
            build_gate(mb_struct, mb_mesh, p0, p1, side, sgn, stats)
            continue
        build_fence_span(mb_struct, mb_mesh, p0, p1, side, sgn, tier, stats)


def build_fence_span(mb_struct, mb_mesh, p0, p1, side, sgn, tier, stats):
    sp = 0.5 * (p0["s"] + p1["s"])
    seed = 9100 + (side > 0) * 5 + p0["pi"] * 31
    wear, paint, _, _ = node_attrs(np.array([sp]), side)
    age = float(wear[0, 0])
    # tension state of THIS span: nothing about it is shared with its neighbours
    slack = 0.25 + 0.75 * h01(seed, 3)
    bow = (h01(seed, 5) - 0.42) * (0.075 + 0.115 * slack) * (0.6 + 0.9 * age)
    sag = (h01(seed, 7) - 0.5) * 0.055 * slack
    droop = (0.008 + 0.052 * slack) * (0.5 + 0.8 * age)
    dent_a = 0.0
    if h01(seed, 11) < 0.13:
        dent_a = (0.06 + 0.22 * h01(seed, 13)) * (1 if h01(seed, 17) < 0.5 else -1)
    dent_c = 0.25 + 0.5 * h01(seed, 19)
    damage = 0.0 if h01(seed, 23) > 0.14 else (0.15 + 0.65 * h01(seed, 29))

    nu = 20 if tier >= 1 else 8
    nv = 12 if tier >= 1 else 5
    U01 = np.linspace(0, 1, nu)
    V01 = np.linspace(0, 1, nv)
    UU, VV = np.meshgrid(U01, V01, indexing='ij')
    A0 = p0["base"] + p0["axis"] * 0.0
    A1 = p1["base"] + p1["axis"] * 0.0
    span_len = float(np.linalg.norm(A1 - A0))
    zr = MESH_Z1 - MESH_Z0
    base = A0[None, None, :] + (A1 - A0)[None, None, :] * UU[..., None]
    axis = p0["axis"][None, None, :] * (1 - UU[..., None]) + p1["axis"][None, None, :] * UU[..., None]
    Avec = p0["A"][None, None, :] * (1 - UU[..., None]) + p1["A"][None, None, :] * UU[..., None]
    b, dz = _span_shape(UU, VV, sag, bow, droop, dent_c, dent_a)
    Z = MESH_Z0 + zr * VV + dz
    S0 = base + axis * Z[..., None] + Avec * b[..., None]

    uvu = UU * span_len
    uvv = MESH_Z0 + zr * VV
    ph = h01(seed, 31)
    layers = ((1, 0.0045),) if in_wire_window(sp, side) else ((0, 0.0), (1, 0.0045))
    for layer, off in layers:
        Pl = S0 + Avec * off
        uid = np.stack([np.full(UU.size, ph if layer == 0 else h01(seed, 37)),
                        np.zeros(UU.size), np.full(UU.size, damage),
                        np.ones(UU.size)], axis=1)
        mb_mesh.add_grid(W3(Pl),
                         uv=np.stack([uvu.ravel(), uvv.ravel()], axis=1),
                         wear=np.repeat(wear, UU.size, axis=0),
                         paint=np.repeat(paint, UU.size, axis=0),
                         uid=uid, mat=layer, smooth=True)
    stats["fence_spans"] += 1

    # tension cables + top rail — real tubes, following the same sag
    for (vv, rad) in ((0.0, 0.0055), (0.5, 0.0045), (1.0, 0.0075)):
        bb, dzz = _span_shape(U01, np.full(nu, vv), sag, bow, droop, dent_c, dent_a)
        Zc = MESH_Z0 + zr * vv + dzz + (0.035 if vv == 1.0 else 0.0)
        Pc = (A0[None, :] + (A1 - A0)[None, :] * U01[:, None] +
              (p0["axis"][None, :] * (1 - U01[:, None]) + p1["axis"][None, :] * U01[:, None]) * Zc[:, None] +
              (p0["A"][None, :] * (1 - U01[:, None]) + p1["A"][None, :] * U01[:, None]) * bb[:, None])
        TT = tube(Pc, rad, seg=6)
        mb_struct.add(W3(TT).reshape(-1, 3), ring_faces(nu, 6, closed=True), mat=0,
                      wear=np.repeat(wear, nu * 6, axis=0),
                      paint=np.repeat(paint, nu * 6, axis=0), smooth=True,
                      uv=np.zeros((nu * 6, 2)),
                      uid=np.tile([ph, 0, 0, 1], (nu * 6, 1)))

# ----------------------------------------------------------------------------
# 15.  TecPro — three-layer polyethylene impact barrier
# ----------------------------------------------------------------------------
#  Real TecPro is a rigid backing (our Armco) faced with rows of rotomoulded
#  blocks.  "Three-layer" = three rows in depth, spec §9 at T1, T4 and T12.

TP_LEN, TP_DEP, TP_H, TP_CAP = 1.00, 0.55, 1.06, 0.34
TP_ROWS = 3
TP_STANDOFF = 0.10       # rear face of the back row to the barrier node line


def _tp_block(length, depth, height, sq=0.34, nst=7, npr=18):
    """Rounded rotomoulded block -> (verts (nst,npr,3), grid indices)."""
    th = np.linspace(0, 2 * math.pi, npr, endpoint=False)
    cy = np.cos(th)
    cz = np.sin(th)
    r = 1.0 / (np.abs(cy) ** (2.0 / sq) + np.abs(cz) ** (2.0 / sq)) ** (sq / 2.0)
    py = cy * r * depth * 0.5
    pz = cz * r * height * 0.5
    t = np.linspace(0.0, 1.0, nst)
    sx = np.sqrt(np.maximum(1e-6, 1.0 - (2.0 * t - 1.0) ** 6)) * 0.5 + 0.5
    sx = sx / sx.max()
    P = np.zeros((nst, npr, 3))
    P[..., 0] = ((t - 0.5) * length)[:, None]
    P[..., 1] = py[None, :] * sx[:, None]
    P[..., 2] = pz[None, :] * sx[:, None]
    return P


def build_tecpro(mb, nd, i0, i1, stats):
    P, S, L, side = nd["P"], nd["s"], nd["L"], nd["side"]
    sgn = -float(side)
    a, bnd = L[i0], L[i1]
    seed = 3300 + (side > 0)
    u = math.ceil(a / TP_LEN) * TP_LEN
    while u < bnd - TP_LEN * 0.5:
        sj = float(np.interp(u, L, S))
        if int(cor_get("btype", np.array([sj]), side)[0]) != B_TECPRO3:
            u += TP_LEN
            continue
        c, T, R = _local_frame(P, L, u + TP_LEN * 0.5, side)
        A = sgn * R
        wear, paint, dent, fresh = node_attrs(np.array([sj]), side)
        bi = int(round(u / TP_LEN))
        for row in range(TP_ROWS):
            for course in range(2):
                seedb = seed * 101 + bi * 17 + row * 5 + course
                rnd = h01(seedb, 3)
                cap = (course == 1)
                hgt = TP_CAP if cap else TP_H
                zc = (TP_H + hgt * 0.5) if cap else (TP_H * 0.5)
                dep = TP_DEP * (0.97 + 0.06 * h01(seedb, 5))
                # a whole TecPro wall settles and creeps; the line is never
                # a ruler-straight extrusion even where nothing has hit it
                settle = float(fbm1(np.array([u / 7.3]), seed=3411 + row)[0]) - 0.5
                if cap and h01(seedb, 41) < 0.07:
                    continue                       # cap block lifted out / missing
                # impact compression: blocks crush and bulge, front row worst
                comp = float(dent[0]) * (1.0 - 0.28 * row) * (2.2 + 2.0 * rnd)
                comp = min(0.42, comp + max(0.0, settle) * 0.16)
                B = _tp_block(TP_LEN * (0.965 + 0.03 * rnd), dep * (1.0 - comp),
                              hgt * (0.98 + 0.05 * comp + 0.03 * h01(seedb, 7)))
                yaw = (h01(seedb, 11) - 0.5) * math.radians(3.2 + 14.0 * comp)
                rol = (h01(seedb, 13) - 0.5) * math.radians(2.4)
                ca, sa = math.cos(yaw), math.sin(yaw)
                Ta = T * ca + A * sa
                Aa = A * ca - T * sa
                Uv = np.array([0.0, 0.0, 1.0])
                Aa = Aa * math.cos(rol) + Uv * math.sin(rol)
                Uv = Uv * math.cos(rol) - (A * ca - T * sa) * math.sin(rol)
                # The back row sits AGAINST the Armco, not INSIDE it.  At the
                # old 0.02 m standoff the block's rear face landed at -0.020
                # while the W-beam's track-side face is at -0.079, so every
                # back-row block passed 59 mm through the rail it is bolted to:
                # 3763 triangle intersections on the BVH gate.  0.10 m leaves
                # 21 mm of clearance, which is what a real TecPro spacer gives.
                off = -(row + 0.5) * TP_DEP - TP_STANDOFF + settle * 0.085
                org = (c + A * off + Uv * (zc + 0.02 * h01(seedb, 17) + settle * 0.045)
                       + Ta * ((h01(seedb, 19) - 0.5) * 0.055))
                V = (org[None, None, :] + B[..., 0][..., None] * Ta
                     + B[..., 1][..., None] * Aa + B[..., 2][..., None] * Uv)
                nst, npr = V.shape[0], V.shape[1]
                f = ring_faces(nst, npr, closed=True)
                uvg = np.stack([np.repeat(np.linspace(0, TP_LEN, nst), npr),
                                (B[..., 2] + hgt * 0.5).ravel()], axis=1)
                fade = clamp01(float(wear[0, 0]) * (0.55 + 0.6 * rnd))
                wv = wear.copy()
                wv[0, 0] = fade
                if float(fresh[0]) > 0.5 and h01(seedb, 23) < 0.7:
                    wv[0, 0] = 0.03          # replaced block, still vivid
                    wv[0, 2] *= 0.2
                nvv = nst * npr
                mb.add(W3(V).reshape(-1, 3), f, mat=0, uv=uvg,
                       wear=np.repeat(wv, nvv, axis=0),
                       paint=np.repeat(paint, nvv, axis=0),
                       uid=np.tile([rnd, 1.0 if cap else 0.0, 0.0, 1.0], (nvv, 1)),
                       smooth=True)
                stats["tecpro_blocks"] += 1
            # steel connecting strap between courses, every 3rd block
            if bi % 3 == 0:
                c2, T2, R2 = _local_frame(P, L, min(bnd, u + TP_LEN * 3.0), side)
                A2 = sgn * R2
                p0 = c + A * (-(row + 0.5) * TP_DEP - TP_STANDOFF - TP_DEP * 0.5) + np.array([0, 0, TP_H * 0.66])
                p1 = c2 + A2 * (-(row + 0.5) * TP_DEP - TP_STANDOFF - TP_DEP * 0.5) + np.array([0, 0, TP_H * 0.66])
                TT = tube(np.linspace(p0, p1, 3), 0.010, seg=4)
                mb.add(W3(TT).reshape(-1, 3), ring_faces(3, 4, closed=True), mat=1,
                       wear=np.repeat(wear, 12, axis=0),
                       paint=np.repeat(paint, 12, axis=0), smooth=True,
                       uv=np.zeros((12, 2)), uid=np.tile([0.5, 0, 0, 1], (12, 1)))
        u += TP_LEN
    return


# ----------------------------------------------------------------------------
# 16.  precast concrete barrier / pit wall
# ----------------------------------------------------------------------------

CB_LEN, CB_H, CB_T = 3.00, 1.20, 0.42


def _cb_block(length, height, thick, batter=0.055, chip=None):
    """Vertical-face precast block with a batter and chipped top corners."""
    hl, ht = length * 0.5, thick * 0.5
    prof = np.array([
        (-ht - batter, 0.0), (ht + batter, 0.0),
        (ht + batter * 0.55, height * 0.22), (ht * 0.92, height * 0.80),
        (ht * 0.86, height), (-ht * 0.86, height),
        (-ht * 0.92, height * 0.80), (-ht - batter * 0.55, height * 0.22)])
    nst = 4
    t = np.linspace(-hl, hl, nst)
    P = np.zeros((nst, len(prof), 3))
    P[..., 0] = t[:, None]
    P[..., 1] = prof[None, :, 0]
    P[..., 2] = prof[None, :, 1]
    if chip is not None:
        for (ci, cj, ca) in chip:
            P[ci, cj, 1] *= (1.0 - ca)
            P[ci, cj, 2] -= ca * height * 0.05
    return P


def build_concrete(mb, nd, i0, i1, stats, mat_idx=0):
    P, S, L, side = nd["P"], nd["s"], nd["L"], nd["side"]
    sgn = -float(side)
    a, bnd = L[i0], L[i1]
    seed = 2200 + (side > 0)
    u = math.ceil(a / CB_LEN) * CB_LEN
    while u < bnd - CB_LEN * 0.5:
        sj = float(np.interp(u, L, S))
        if int(cor_get("btype", np.array([sj]), side)[0]) != B_CONCRETE:
            u += CB_LEN
            continue
        c, T, R = _local_frame(P, L, u + CB_LEN * 0.5, side)
        A = sgn * R
        bi = int(round(u / CB_LEN))
        seedb = seed * 71 + bi
        rnd = h01(seedb, 3)
        wear, paint, dent, fresh = node_attrs(np.array([sj]), side)
        chip = []
        for q in range(int(3 * h01(seedb, 5))):
            chip.append((int(4 * h01(seedb, 7 + q)) % 4,
                         4 + int(2 * h01(seedb, 11 + q)),
                         0.05 + 0.16 * h01(seedb, 13 + q)))
        B = _cb_block(CB_LEN - 0.018 - 0.010 * rnd, CB_H * (0.99 + 0.02 * rnd),
                      CB_T, chip=chip)
        yaw = (h01(seedb, 17) - 0.5) * math.radians(1.3)
        rol = (h01(seedb, 19) - 0.5) * math.radians(1.1)
        ca, sa = math.cos(yaw), math.sin(yaw)
        Ta, Aa = T * ca + A * sa, A * ca - T * sa
        Uv = np.array([0.0, 0.0, 1.0])
        Aa2 = Aa * math.cos(rol) + Uv * math.sin(rol)
        Uv = Uv * math.cos(rol) - Aa * math.sin(rol)
        org = c + Uv * (-0.02 - 0.03 * h01(seedb, 23))
        V = (org[None, None, :] + B[..., 0][..., None] * Ta
             + B[..., 1][..., None] * Aa2 + B[..., 2][..., None] * Uv)
        nst, npr = V.shape[0], V.shape[1]
        f = ring_faces(nst, npr, closed=True)
        uvg = np.stack([np.repeat(np.linspace(0, CB_LEN, nst), npr),
                        np.tile(B[0, :, 2], nst)], axis=1)
        nvv = nst * npr
        wv = wear.copy()
        wv[0, 0] = clamp01(wv[0, 0] * (0.6 + 0.7 * rnd))
        mb.add(W3(V).reshape(-1, 3), f, mat=mat_idx, uv=uvg,
               wear=np.repeat(wv, nvv, axis=0),
               paint=np.repeat(paint, nvv, axis=0),
               uid=np.tile([rnd, 0.0, 0.0, 1.0], (nvv, 1)), smooth=False)
        stats["concrete_blocks"] += 1
        u += CB_LEN
    return


# ----------------------------------------------------------------------------
# 17.  tyre wall — hairpin infield and the apron corridor
# ----------------------------------------------------------------------------

def _tyre_mesh(rad=0.335, wid=0.305, bead=0.215, nring=20, seed=0, squash=0.0,
               wear_t=0.5):
    """Revolved tyre with a real tread band and sidewall curvature."""
    prof = np.array([
        (bead, -wid * 0.36), (bead + 0.030, -wid * 0.46), (rad * 0.72, -wid * 0.50),
        (rad * 0.93, -wid * 0.47), (rad * 0.995, -wid * 0.40),
        (rad, -wid * 0.22), (rad, 0.0), (rad, wid * 0.22),
        (rad * 0.995, wid * 0.40), (rad * 0.93, wid * 0.47),
        (rad * 0.72, wid * 0.50), (bead + 0.030, wid * 0.46), (bead, wid * 0.36)])
    th = np.linspace(0, 2 * math.pi, nring, endpoint=False)
    # tread grooves + flat-spotting from years of stacking
    grv = 1.0 - 0.010 * (1.0 - wear_t) * (np.abs(np.sin(th * 9.0)) > 0.72)
    flat = 1.0 - squash * np.maximum(0.0, -np.cos(th - 0.6)) ** 2
    P = np.zeros((nring, len(prof), 3))
    rr = prof[:, 0][None, :] * (grv * flat)[:, None]
    P[..., 0] = np.cos(th)[:, None] * rr
    P[..., 2] = np.sin(th)[:, None] * rr
    P[..., 1] = prof[:, 1][None, :]
    wob = 1.0 + 0.012 * (vnoise1(th * 3.0 + seed, 41)[:, None] - 0.5)
    P[..., 0] *= wob[:, 0][:, None]
    P[..., 2] *= wob[:, 0][:, None]
    return P


def build_tyre_wall(mb, path, rows, courses, side_sign, seed0, stats, belt=True):
    """path: (n,3) design polyline along the FACE of the wall."""
    path = np.asarray(path, dtype=np.float64)
    seg = np.linalg.norm(np.diff(path, axis=0)[:, :2], axis=1)
    L = np.concatenate([[0.0], np.cumsum(seg)])
    total = float(L[-1])
    pitch = 0.62
    nt = max(1, int(total / pitch))
    for i in range(nt):
        u = (i + 0.5) * total / nt
        c = np.array([np.interp(u, L, path[:, k]) for k in range(3)])
        du = (np.array([np.interp(min(total, u + 0.6), L, path[:, k]) for k in range(3)]) -
              np.array([np.interp(max(0.0, u - 0.6), L, path[:, k]) for k in range(3)]))
        T = du / max(1e-9, np.linalg.norm(du))
        R = np.array([T[1], -T[0], 0.0])
        R /= max(1e-9, np.linalg.norm(R))
        A = side_sign * R
        for row in range(rows):
            for cz in range(courses):
                sd = seed0 * 313 + i * 29 + row * 7 + cz
                rnd = h01(sd, 3)
                stag = 0.31 if (cz % 2) else 0.0
                rad = 0.335 * (0.955 + 0.075 * h01(sd, 5))
                wid = 0.305 * (0.94 + 0.13 * h01(sd, 7))
                age = clamp01(0.25 + 0.7 * h01(sd, 11))
                sq = 0.02 + 0.09 * age * (courses - cz) / max(1, courses)
                Tm = _tyre_mesh(rad=rad, wid=wid, seed=sd % 97, squash=sq,
                                wear_t=h01(sd, 13))
                spin = h01(sd, 17) * 2 * math.pi
                tiltx = (h01(sd, 19) - 0.5) * math.radians(6.0)
                cs, sn = math.cos(spin), math.sin(spin)
                # tyre local: x/z in the wheel plane (vertical), y = axle (lateral)
                ex = T * cs + np.array([0.0, 0.0, 1.0]) * sn
                ez = -T * sn + np.array([0.0, 0.0, 1.0]) * cs
                ey = A
                ct, st = math.cos(tiltx), math.sin(tiltx)
                ey2 = ey * ct + ez * st
                ez2 = ez * ct - ey * st
                org = (c + T * stag + A * (-(row + 0.5) * 0.30)
                       + np.array([0.0, 0.0, rad * 0.94 + cz * rad * 1.80]))
                V = (org[None, None, :] + Tm[..., 0][..., None] * ex
                     + Tm[..., 1][..., None] * ey2 + Tm[..., 2][..., None] * ez2)
                nr, npf = V.shape[0], V.shape[1]
                f = ring_faces(nr, npf, closed=False)
                # close the bead hole with a ring band
                inner = np.stack([V[:, 0, :], V[:, -1, :]], axis=1)
                fi = ring_faces(nr, 2, closed=False)
                uvg = np.stack([np.repeat(np.linspace(0, 2.1, nr), npf),
                                np.tile(np.linspace(0, 1, npf), nr)], axis=1)
                nvv = nr * npf
                wv = np.array([[age, 0.0, 0.35 + 0.5 * h01(sd, 23), 0.0]])
                mb.add(V.reshape(-1, 3), f, mat=0, uv=uvg,
                       wear=np.repeat(wv, nvv, axis=0),
                       paint=np.tile([0, 0, 0, 1], (nvv, 1)),
                       uid=np.tile([rnd, 0, 0, 1], (nvv, 1)), smooth=True)
                mb.add(inner.reshape(-1, 3), fi, mat=0,
                       uv=np.zeros((nr * 2, 2)),
                       wear=np.repeat(wv, nr * 2, axis=0),
                       paint=np.tile([0, 0, 0, 1], (nr * 2, 1)),
                       uid=np.tile([rnd, 0, 0, 1], (nr * 2, 1)), smooth=True)
                stats["tyres"] += 1
    if belt:
        # Conveyor belting facing.  Real belt-faced tyre walls are strips of
        # 2.6-4.5 m bolted through the tyres with a gap at every joint; the
        # belt hugs the tyre bulges rather than hanging as a smooth curtain.
        top = courses * 0.335 * 1.80 - 0.16
        vv = np.linspace(0.06, top, 7)
        pos = 0.0
        strip = 0
        while pos < total - 0.6:
            sl = min(total - pos, 2.6 + 1.9 * h01(seed0 * 7 + strip, 3))
            nu = max(3, int(sl / 0.30))
            uu = np.linspace(pos, pos + sl - 0.05, nu)
            G = np.zeros((nu, len(vv), 3))
            slack = 0.35 + 0.9 * h01(seed0 * 7 + strip, 5)
            for a_ in range(nu):
                c = np.array([np.interp(uu[a_], L, path[:, k]) for k in range(3)])
                du = (np.array([np.interp(min(total, uu[a_] + 0.5), L, path[:, k])
                                for k in range(3)]) -
                      np.array([np.interp(max(0.0, uu[a_] - 0.5), L, path[:, k])
                                for k in range(3)]))
                T = du / max(1e-9, np.linalg.norm(du))
                R = np.array([T[1], -T[0], 0.0])
                R /= max(1e-9, np.linalg.norm(R))
                A = side_sign * R
                # the tyres behind bulge on a 0.62 m pitch; the belt drapes over
                bulge = 0.026 * slack * np.cos(2 * np.pi * uu[a_] / 0.62)
                bulge += 0.030 * slack * np.sin(np.pi * ((uu[a_] - pos) / sl))
                bulge += 0.012 * (vnoise1(uu[a_] * 1.7 + seed0, 53) - 0.5)
                vsag = 0.020 * slack * np.sin(np.pi * np.clip(
                    (vv - vv[0]) / max(1e-6, vv[-1] - vv[0]), 0, 1))
                G[a_] = (c[None, :] + A[None, :] * (0.045 + bulge + vsag)[:, None]
                         + np.array([0.0, 0.0, 1.0])[None, :] * vv[:, None])
            age = 0.30 + 0.6 * h01(seed0 * 7 + strip, 7)
            wv = np.array([[age, 0.0, 0.25 + 0.5 * h01(seed0 * 7 + strip, 11), 0.0]])
            nn = nu * len(vv)
            mb.add_grid(G, mat=1,
                        uv=np.stack([np.repeat(uu, len(vv)), np.tile(vv, nu)], axis=1),
                        wear=np.repeat(wv, nn, axis=0),
                        paint=np.tile([0, 0, 0, 1], (nn, 1)),
                        uid=np.tile([h01(seed0 * 7 + strip, 13), 0, 0, 1], (nn, 1)),
                        smooth=True)
            # bolt washers along the top and bottom edge of the strip
            for uw in np.arange(pos + 0.35, pos + sl - 0.2, 0.62):
                c = np.array([np.interp(uw, L, path[:, k]) for k in range(3)])
                du = (np.array([np.interp(min(total, uw + 0.5), L, path[:, k]) for k in range(3)]) -
                      np.array([np.interp(max(0.0, uw - 0.5), L, path[:, k]) for k in range(3)]))
                T = du / max(1e-9, np.linalg.norm(du))
                R = np.array([T[1], -T[0], 0.0]); R /= max(1e-9, np.linalg.norm(R))
                A = side_sign * R
                for zw in (vv[1], vv[-2]):
                    o = c + A * 0.085 + np.array([0.0, 0.0, zw])
                    th = np.linspace(0, 2 * math.pi, 6, endpoint=False)
                    ring0 = o + (np.cos(th)[:, None] * T + np.sin(th)[:, None] *
                                 np.array([0.0, 0.0, 1.0])) * 0.026
                    ring1 = ring0 + A * 0.012
                    V = np.vstack([ring0, ring1])
                    f = np.vstack([ring_faces(2, 6, closed=True),
                                   np.array([[6, 7, 8, 9], [9, 10, 11, 6]])])
                    mb.add(V, f, mat=1, uv=np.zeros((12, 2)),
                           wear=np.tile([0.5, 0, 0.2, 0], (12, 1)),
                           paint=np.tile([0, 0, 0, 1], (12, 1)),
                           uid=np.tile([0.5, 0, 0, 1], (12, 1)), smooth=False)
            pos += sl + 0.05 + 0.06 * h01(seed0 * 7 + strip, 17)
            strip += 1

# ----------------------------------------------------------------------------
# 18.  gravel traps
# ----------------------------------------------------------------------------

TRAP_DEPTH = 0.24
STONE_BUDGET = 240000


def _contig(mask, s=SGRID, minlen=12.0):
    out, i = [], 0
    n = len(mask)
    while i < n:
        if not mask[i]:
            i += 1
            continue
        j = i
        while j < n and mask[j]:
            j += 1
        if (s[j - 1] - s[i]) >= minlen:
            out.append((float(s[i]), float(s[j - 1])))
        i = j
    return out


# ---------------------------------------------------------------------------
#  THE BUILT PROGRAMME — one definition of what is actually laid, so the
#  platform mesh and the surfaces on it can never disagree about a width.
# ---------------------------------------------------------------------------
#  The contract's runoff table gives ideal widths that ramp in and out over
#  40-60 m.  What gets BUILT is thresholded (nobody lays a 0.2 m gravel bed) and
#  then tapered back to zero over the last few metres of every run, so no
#  surface in this module ends with a blunt transverse face and so
#  `platform_widths` is continuous.  Every consumer reads these arrays; nothing
#  re-derives them.
#
#  Where a braking-zone asphalt runoff and an apex gravel bed both claim the
#  strip immediately outboard of the painted verge (this happens on the right at
#  T7i/T8, T9i/T8 and T14i/T15 — 138 m of the lap), THE ASPHALT WINS and the
#  apex bed is faded out under it.  A braking zone is paved; that is the point of
#  paving it.

_PROG_MINW = dict(asph=0.30, grav=0.90, apex=0.90)
_PROG_TAPER = dict(asph=14.0, grav=11.0, apex=9.0)


def _taper_runs(a, ramp):
    """Zero outside contiguous runs; taper each run's last `ramp` metres to 0."""
    out = np.zeros(NS)
    for (s0, s1) in _contig(a > 0.0, minlen=10.0):
        m = (SGRID >= s0) & (SGRID <= s1)
        r = min(ramp, 0.40 * (s1 - s0))
        out[m] = a[m] * (smoothstep(s0, s0 + r, SGRID[m]) *
                         (1.0 - smoothstep(s1 - r, s1, SGRID[m])))
    return out


def _build_programme():
    out = {}
    for side in (+1, -1):
        asph = COR.asph[side].copy()
        grav = COR.grav[side].copy()
        apex = COR.apex[side].copy()
        # THE RUNOFF MUST FIT INSIDE THE BARRIER.  Where §4b's ownership clamp
        # has pulled the barrier in — the T3/S3 stretch, where the spec's 40+15 m
        # would otherwise be laid on top of the S4/T5 leg — the programme is
        # scaled to the width that is actually there, keeping the declared
        # asphalt:gravel ratio.  It is the only thing that fits, and it is what a
        # real circuit does when two legs run 51 m apart.
        room = np.maximum(0.0, barrier_offset(SGRID, side) - verge_edge(SGRID)
                          - RUNOFF_STANDOFF)
        tot = asph + grav
        k = np.where(tot > room, room / np.maximum(tot, 1e-9), 1.0)
        asph = asph * k
        grav = grav * k
        apex = np.minimum(apex, room)
        asph = np.where(asph < _PROG_MINW["asph"], 0.0, asph)
        grav = np.where(grav < _PROG_MINW["grav"], 0.0, grav)
        apex = np.where(apex < _PROG_MINW["apex"], 0.0, apex)
        # ONE claim per station on the strip against the painted verge.  An apex
        # bed is the "everywhere else" default (spec §9), so wherever a braking
        # zone has a declared runoff programme, the programme wins outright.
        apex = np.where((asph > 0.0) | (grav > 0.0), 0.0, apex)
        out[side] = dict(asph=_taper_runs(asph, _PROG_TAPER["asph"]),
                         grav=_taper_runs(grav, _PROG_TAPER["grav"]),
                         apex=_taper_runs(apex, _PROG_TAPER["apex"]))
    return out


PROG = _build_programme()


def prog(name, s, side):
    """Built width of `asph` | `grav` | `apex` at station(s), metres."""
    return np.interp(np.asarray(s, float) % LAP_LEN, SGRID, PROG[side][name],
                     period=LAP_LEN)


def trap_zones():
    """(s0, s1, side, kind) for every gravel bed on the circuit."""
    z = []
    for side in (+1, -1):
        for (a, b) in _contig(PROG[side]["grav"] > 0.0):
            z.append((a, b, side, "outer"))
        for (a, b) in _contig(PROG[side]["apex"] > 0.0):
            z.append((a, b, side, "apex"))
    return z


def _trap_radii(s, side, kind):
    """(inner lateral, width) of a gravel bed, measured from the CENTRELINE."""
    if kind == "outer":
        return verge_edge(s) + prog("asph", s, side), prog("grav", s, side)
    return verge_edge(s), prog("apex", s, side)


def trap_depth_profile(DD, WW):
    """Depth of the SMOOTH gravel-bed basin below `ground_z`, in metres.

    Exactly 0 at both lateral edges (DD = 0 and DD = WW) for ANY width, so the
    bed welds flush into the platform on both sides instead of leaving a rim
    step, and `platform_z`'s sub-base can be guaranteed to stay under it.

    THE AMPLITUDE SCALES WITH THE WIDTH TOO, not just the ramps.  Shortening the
    ramps alone still let a bed reach the full 0.24 m in the middle however
    narrow it was: measured at the verge weld at s = 2128.7, a 48 mm-wide bed
    tip was a 48 mm-wide, 0.24 m-deep slot right against the painted verge.  A
    bed narrower than 2.6 m is a scrape, which is what a tapering bed edge is.
    """
    WW = np.asarray(WW, float)
    a = np.maximum(1e-6, np.minimum(1.35, 0.42 * WW))
    b = np.maximum(1e-6, np.minimum(1.10, 0.42 * WW))
    ta = clamp01(np.asarray(DD, float) / a)
    tb = clamp01((WW - DD) / b)
    return TRAP_DEPTH * clamp01(WW / 2.6) * _smooth(ta) * _smooth(tb)


def _gouges(s0, s1, side, seed):
    """Braking-zone ruts: pairs of wheel tracks ploughed into the bed."""
    out = []
    n = 3 + int(7 * h01(seed, 3))
    for k in range(n):
        u = h01(seed, 11 + k)
        sg = s0 + (s1 - s0) * (0.10 + 0.55 * u ** 0.6)     # bunched near the entry
        ang = (0.28 + 0.55 * h01(seed, 31 + k))            # radians, into the bed
        dep = 0.075 + 0.115 * h01(seed, 51 + k)
        reach = 4.0 + 14.0 * h01(seed, 71 + k)
        out.append((sg, ang, dep, reach, h01(seed, 91 + k)))
    return out


def build_gravel_trap(mb, mbs, s0, s1, side, kind, stats, stone_left):
    span = s1 - s0
    tier = int(hero_tier(np.array([0.5 * (s0 + s1)]), side)[0])
    ds = 0.09 if tier >= 2 else (0.22 if tier >= 1 else 0.36)
    # 2 m of station padding at each end.  The platform's sub-base basin is
    # keyed off the same `prog` field, and the platform samples it at up to
    # 1.9 m spacing, so a trap that stopped exactly at its contiguous run left
    # up to one platform station of basin uncovered — measured at s = 3134.6 and
    # s = 705.6 as 0.57 m of exposed sub-base at the lip.  `prog` is 0 out here,
    # so the padded rows collapse to zero width and cost nothing.
    S = np.arange(max(0.0, s0 - 2.0), min(LAP_LEN, s1 + 2.0) + ds, ds)
    r0, w = _trap_radii(S, side, kind)
    if len(S) < 4 or float(np.max(w)) < 0.5:
        return stone_left
    gouges = _gouges(s0, s1, side, 2900 + int(s0) + (side > 0))

    def bed(SS, DD, WW):
        """Bed height at station SS, `DD` metres out from the lip.  ONE
        definition, used by the surface grid and by the scattered stones, so a
        stone can never float above or sink under its own bed.

        EVERY disturbance is windowed to zero at both lateral edges by `lip`, so
        the bed meets the platform exactly on the datum and the platform's
        sub-base is guaranteed to stay beneath it (see `platform_z`).  Without
        that window a 190 mm braking rut could reach the lip and the sub-base
        would show through it.
        """
        # The lip window also has to close where the BED is narrow, not just
        # where the sample is near an edge.  In the 2 m of station padding at
        # each end of a run the width is ~0, and `lw` shrinks with it, so
        # DD/lw still reached 1 and a 190 mm braking gouge landed on a bed with
        # no width — measured as a 0.229 m step at the verge weld at s = 2128.7.
        lw = np.maximum(1e-6, np.minimum(0.90, 0.30 * WW))
        lip = (_smooth(clamp01(DD / lw)) * _smooth(clamp01((WW - DD) / lw))
               * _smooth(clamp01(WW / 1.2)))
        z = ground_z(SS, np.interp(SS, S, r0) + DD, side)
        z -= trap_depth_profile(DD, WW)
        z += lip * (fbm2(SS / 5.2, DD / 4.4, seed=1717, oct=4) - 0.5) * 0.075
        fp = 0.30 + 0.10 * fbm1(SS / 40.0, seed=1811)
        z += lip * 0.011 * np.sin(2 * np.pi * (DD / fp +
                                               0.7 * fbm1(SS / 9.0, seed=1822)))
        z += lip * (fbm2(SS / 0.55, DD / 0.55, seed=1833, oct=3) - 0.5) * \
            (0.020 if tier >= 2 else 0.010)
        dist = np.zeros_like(z)
        for (sg, ang, dep, reach, rr) in gouges:
            for tr in (-0.85, 0.85):
                ds_ = (SS - sg) - (DD * math.tan(ang)) * (1 if rr > 0.5 else -1) - tr
                mm = np.exp(-0.5 * (ds_ / 0.17) ** 2) * lip
                fd = np.exp(-DD / max(2.0, reach))
                z -= dep * mm * fd
                berm = np.exp(-0.5 * ((np.abs(ds_) - 0.34) / 0.13) ** 2) * lip
                z += dep * 0.42 * berm * fd
                dist = np.maximum(dist, mm * fd)
        return z, dist

    du = 0.045 if tier >= 2 else (0.12 if tier >= 1 else 0.30)
    W = float(np.max(w))
    D = np.unique(np.concatenate([np.arange(0.0, min(W, 3.2), du),
                                  np.arange(min(W, 3.2), W + 0.42, 0.42), [W]]))
    ni, nj = len(S), len(D)
    SS = np.repeat(S[:, None], nj, 1)
    WW = np.repeat(w[:, None], nj, 1)
    DD = D[None, :] * (w[:, None] / max(1e-6, W))
    Z, dist = bed(SS, DD, WW)
    lat = np.repeat(r0[:, None], nj, 1) + DD
    x, y, _ = CL.point(SS, lat, side, bank=False)
    P = np.stack([x, y, Z], axis=-1)
    drag = clamp01(1.2 * np.exp(-DD / 1.6) + 0.8 * dist)
    wv = np.stack([np.full(ni * nj, 0.5), np.zeros(ni * nj), drag.ravel(),
                   np.zeros(ni * nj)], axis=1)
    uv = np.stack([DD.ravel(), SS.ravel()], axis=1)          # metres
    mb.add_grid(W3(P), uv=uv, wear=wv,
                paint=np.tile([0, 0, 0, 1], (ni * nj, 1)),
                uid=np.tile([0.5, 0, 0, 1], (ni * nj, 1)), mat=0, smooth=True)
    stats["trap_area_m2"] += float(np.sum(w) * ds)

    # --- proud stones over the near band, seated on the same bed function ---
    if tier >= 1 and stone_left > 0:
        band = 8.0 if tier >= 2 else 2.4
        dens = 130.0 if tier >= 2 else 55.0
        n = int(min(stone_left, span * band * dens))
        if n > 40:
            k = np.arange(n)
            sd = 6100 + int(s0) + (side > 0)
            ss_ = S[0] + (S[-1] - S[0]) * hash01(k, np.full(n, sd))
            wq = np.interp(ss_, S, w)
            dd = np.minimum(band * hash01(k, np.full(n, sd + 7)) ** 0.7, wq * 0.98)
            zq, _ = bed(ss_, dd, wq)
            latq = np.interp(ss_, S, r0) + dd
            xq, yq, _ = CL.point(ss_, latq, side, bank=False)
            _scatter_stones(mbs, np.stack([xq, yq, zq], axis=1), sd, stats)
            stone_left -= n
    return stone_left


def _scatter_stones(mb, Pd, seed, stats, smin=0.018, smax=0.072):
    """Pd: (n,3) design-frame centres.  Every stone is unique geometry."""
    n = len(Pd)
    if n == 0:
        return
    BV, BF = _ICO0
    k = np.arange(n)
    r = smin + (smax - smin) * hash01(k, np.full(n, seed + 1)) ** 1.8
    sx = 1.0 + 0.55 * (hash01(k, np.full(n, seed + 2)) - 0.5)
    sy = 1.0 + 0.55 * (hash01(k, np.full(n, seed + 3)) - 0.5)
    sz = 0.55 + 0.45 * hash01(k, np.full(n, seed + 4))
    a = hash01(k, np.full(n, seed + 5)) * 2 * math.pi
    b = hash01(k, np.full(n, seed + 6)) * 2 * math.pi
    V = np.tile(BV[None, :, :], (n, 1, 1))
    j = np.arange(BV.shape[0])[None, :]
    jit = 0.72 + 0.56 * hash01(np.repeat(k[:, None], BV.shape[0], 1),
                               np.tile(j, (n, 1)) + seed * 13)
    V = V * jit[..., None]
    V = V * np.stack([sx, sy, sz], axis=1)[:, None, :] * r[:, None, None]
    ca, sa = np.cos(a)[:, None], np.sin(a)[:, None]
    cb, sb = np.cos(b)[:, None], np.sin(b)[:, None]
    X = V[..., 0] * ca - V[..., 1] * sa
    Y = V[..., 0] * sa + V[..., 1] * ca
    Z2 = V[..., 2]
    V = np.stack([X, Y * cb - Z2 * sb, Y * sb + Z2 * cb], axis=-1)
    V = V + Pd[:, None, :]
    V[..., 2] -= (r * 0.20)[:, None]     # seated, never floating
    nv = BV.shape[0]
    F = np.tile(BF[None, :, :], (n, 1, 1)) + (np.arange(n) * nv)[:, None, None]
    uid = np.repeat(np.stack([hash01(k, np.full(n, seed + 8)), np.zeros(n),
                              np.zeros(n), np.ones(n)], axis=1), nv, axis=0)
    mb.add(W3(V).reshape(-1, 3), F.reshape(-1, 3), mat=0,
           uv=np.zeros((n * nv, 2)),
           wear=np.tile([0.5, 0, 0, 0], (n * nv, 1)),
           paint=np.tile([0, 0, 0, 1], (n * nv, 1)), uid=uid, smooth=True)
    stats["stones"] += n


# ----------------------------------------------------------------------------
# 19.  THE RUNOFF PLATFORM  —  every square metre from verge_edge to
#      platform_edge, both sides, the whole lap
# ----------------------------------------------------------------------------
#
# THIS IS THE PART THE ASSEMBLY REVIEW WAS ABOUT.  Before the contract this
# module built three disconnected ribbons — a tarmac runoff strip, a gravel bed
# and a 4.5 m shoulder under the barrier — and left the ground between them to
# build_terrain, which covered the lot in dirt on a 2.5 m grid.  The contract
# reverses that: terrain cuts a 309 180 m2 hole and welds its first ring of
# vertices to `corridor_rim(s, side)` at `platform_edge`, and everything inside
# is ours.  227 208 m2 of it, once §4b's ownership clamp has taken out the
# 10 752 m2 where the corridor overlapped its own other branch.
#
# So the platform is ONE CONTINUOUS SURFACE per side, from `verge_edge(s)` to
# `platform_edge(s, side)`, laid on `ground_z`, carrying:
#
#     band A   runoff asphalt          verge_edge .. +prog("asph")
#     band X   apex gravel basin       verge_edge .. +prog("apex")
#     band G   outer gravel basin      +asph .. +asph+grav
#     band V   the verge itself        outboard of all of them .. platform_edge
#
# as four `add_grid` calls that share their boundary rows EXACTLY (same station
# array, same lateral formula, same z function), so there is no internal seam to
# find.  The gravel bands are a SUB-BASE: they dip well below the bed the trap
# builder lays on top, so nothing of the platform can ever poke through a rut.
#
# THE TWO WELDS, and what "agrees" means at each:
#
#   INNER, u = verge_edge(s):   z is EXACTLY ground_z, no offset, no drop.  This
#       is build_surface's outer edge.  Because two independently tessellated
#       meshes cannot follow a 3675 m curve with the same chord error, the
#       platform additionally carries a hidden flange: straight DOWN by
#       PLATFORM_TUCK_Z at u = verge_edge, then inward by PLATFORM_TUCK.  It has
#       zero horizontal footprint at the shared line and is 50 mm below the
#       datum by the time it has any, so it is NOT a coplanar surface — it
#       closes chord slivers without z-fighting.  This is what replaces
#       SEAM_DROP, which claimed to absorb 15 mm of DATUM disagreement; there is
#       none left to absorb.
#
#   OUTER, u = owned_edge(s, side):  z is EXACTLY ground_z.  This is
#       `corridor_rim`, except over the 13.6 % of the left side where §4b's
#       ownership clamp bites and it is the medial axis instead.  Station
#       spacing is chosen from the local rim radius AND from how fast the rim is
#       moving, so the chord sagitta stays under 4 mm both round the inside of
#       the hairpin (rim radius ~8 m) and along a runoff taper (1.55 m of
#       lateral per metre of station).

SHOULDER_DROP = 0.045     # pavement edge -> shoulder, at the outboard edge of
                          # the runoff asphalt.  A real runoff pad has one.
SWALE_W = 4.0             # ...recovering over this, which is the drainage swale
BERM_H = 0.075            # earth retaining bank outboard of a gravel bed
BERM_W = 3.0
PLATFORM_TUCK = 0.14      # hidden flange inboard of verge_edge
PLATFORM_TUCK_Z = 0.050
BASIN_MAX = 0.62          # deepest the gravel sub-base ever goes (measured
                          # against the worst possible bed: 0.24 profile +
                          # 0.19 rut + 0.037 noise + 0.031 ripple = 0.498 m)
BASIN_GAIN = 3.2
PLATFORM_RELIEF = 0.075   # mown-ground relief amplitude, windowed to 0 at both
                          # welds so neither weld can be anything but exact


def platform_z(S, U, side):
    """Finished ground of the runoff platform at (station, unsigned lateral).

    Departs from `ground_z` only INSIDE the platform, never at either weld:
    a pavement-edge drop and drainage swale outboard of the asphalt, an earth
    retaining berm outboard of a gravel bed, a deep sub-base under the gravel
    beds, a graded flat strip under the barrier line, and low mown-ground
    relief.  Every one of those terms is multiplied by a window that is zero at
    u = verge_edge and at u = platform_edge.
    """
    S = np.asarray(S, float)
    U = np.asarray(U, float)
    ve = verge_edge(S)               # the painted verge: where the PROGRAMME starts
    e = platform_inner(S, side)      # where this module's MESH starts (S4c)
    pe = platform_reach(S, side)     # ... and where it stops (S4b/S4c)
    b = barrier_offset(S, side)
    z = ground_z(S, U, side)

    d = U - ve                                  # metres outboard of the verge
    span = np.maximum(pe - e, 0.25)
    t = np.clip(d / span, 0.0, 1.0)
    win = np.sin(np.pi * t) ** 0.8              # 0 at BOTH welds, by construction

    wA = prog("asph", S, side)
    wG = prog("grav", S, side)
    wX = prog("apex", S, side)

    # --- gravel sub-base: strictly below whatever the trap builder lays -----
    for (a0, ww) in ((wA, wG), (0.0, wX)):
        dd = d - a0
        basin = np.minimum(BASIN_MAX, BASIN_GAIN * trap_depth_profile(
            np.clip(dd, 0.0, None), np.maximum(ww, 1e-6)))
        z -= np.where((ww > 1e-6) & (dd >= 0.0) & (dd <= ww), basin, 0.0)

    # --- pavement edge, swale and berm at the outboard edge of the programme -
    cov = np.maximum(wA + wG, wX)
    q = d - cov
    paved = (wA > 0.05) & (wG < 0.05) & (wX < 0.05)
    gravelly = (wG > 0.05) | (wX > 0.05)
    lobe_s = smoothstep(0.0, 0.55, q) * (1.0 - smoothstep(0.55, SWALE_W, q))
    lobe_b = smoothstep(0.0, 0.70, q) * (1.0 - smoothstep(0.70, BERM_W, q))
    z -= np.where(paved & (cov > 0.05), SHOULDER_DROP * lobe_s, 0.0)
    z += np.where(gravelly, BERM_H * lobe_b, 0.0)

    # --- the barrier's own maintenance strip: graded flat, 2.4 m either side --
    # It SETTLES WITH THE BARRIER.  `HIST.align`'s vertical term is what sinks a
    # barrier run up to 57 mm; if the ground under it did not sink too, the
    # barrier would stand in a 57 mm trench in some runs and be 57 mm proud in
    # others.  Reading the same field here makes the barrier stand exactly
    # 14 mm above its own shoulder everywhere, by construction.
    strip = 1.0 - np.clip(np.abs(U - b) / 2.4, 0.0, 1.0)
    strip = strip * strip * (3.0 - 2.0 * strip)
    # ...and it dies within 0.45 m of either weld.  On the pit straight the
    # platform is only 1.6 m wide (the pit wall's margin is 0.6 m), so the 4.8 m
    # maintenance strip covers all of it and carried up to 49 mm of barrier
    # settlement out onto the corridor rim.  Measured at s 30-39: -0.046 m.
    strip *= (np.clip((U - e) / 0.45, 0, 1) * np.clip((pe - U) / 0.45, 0, 1))
    z += HIST.align(S, side)[1] * strip
    z -= 0.014 * strip

    # --- mown-ground relief, dying at both welds and under the barrier -------
    rel = ((fbm2(S / 26.0, U / 17.0, seed=2411, oct=3) - 0.5) * PLATFORM_RELIEF +
           (fbm2(S / 7.5, U / 5.2, seed=2417, oct=2) - 0.5) * (PLATFORM_RELIEF * 0.34))
    z += rel * win * (1.0 - 0.85 * strip)
    return z


def _platform_ds(side, s_mid, tier):
    """Station spacing: fine enough that the corridor rim's chord sagitta stays
    under 4 mm.  On the INSIDE of the hairpin the rim radius falls to ~8 m, and
    a 2 m step there would leave a 6 cm scallop for terrain to weld to."""
    _, _, _, k, _, _ = CL.at(np.array([s_mid]))
    kk = float(np.abs(k[0]))
    pe = float(platform_reach(np.array([s_mid]), side)[0])
    R = 1e6 if kk < 1e-9 else 1.0 / kk
    # rim radius: the platform edge is inboard of the arc centre on the inside
    Rrim = max(4.0, R - pe if (np.sign(k[0]) == side) else R + pe)
    base = 0.9 if tier >= 1 else 1.9
    # ...and the rim also moves fast along a runoff taper: at the end of the T1
    # ramp `platform_edge` sheds 1.55 m of lateral per metre of station, and a
    # 1.9 m chord across that curve left a 40 mm sliver (0.087 m2, measured by
    # dense probe at s = 456.4) between the mesh edge and `corridor_rim`.
    g = abs(float(platform_reach(np.array([s_mid + 3.0]), side)[0])
            - float(platform_reach(np.array([s_mid - 3.0]), side)[0])) / 6.0
    if g > 0.40:
        base = min(base, 0.65)
    return float(np.clip(math.sqrt(8.0 * 0.004 * Rrim), 0.40, base))


def _platform_runs(side):
    """Station ranges this module paves.

    Two exclusions, both because someone else's mesh is already there:
      * the declared pit-exit apron (spec §10.7 / contract §7), whose surface is
        build_architecture's unrubbered concrete, not our runoff;
      * the handful of stations where the Beat-4 access ribbon has eaten the
        whole band, so `platform_inner` has met `platform_reach` (§4c).
    """
    skip = (WC.apron_zone(SGRID, side) > 0.5)
    skip |= (_RIB_INNER[side] >= _REACH[side] - 0.25)
    if not skip.any():
        return [(0.0, LAP_LEN)]
    runs = [(float(SGRID[i]), float(SGRID[j - 1] + PS))
            for (i, j) in _runs(~skip)]
    return [(a, b) for (a, b) in runs if b - a > 4.0]


def _lat_rows(S, side):
    """Per-station lateral row positions for each of the four bands.

    Returns a dict of (ni, nj) lateral arrays.  Every band's first/last row is
    computed from the SAME expression as its neighbour's, so the shared rows are
    bit-identical and the four grids weld without a gap.
    """
    ve = verge_edge(S)                                      # the PROGRAMME datum
    e = np.minimum(platform_inner(S, side), ve + 60.0)      # the MESH's inner edge
    pe = platform_reach(S, side)
    wA = prog("asph", S, side)
    wG = prog("grav", S, side)
    wX = prog("apex", S, side)
    # The runoff programme is measured from the painted verge and the ribbon cut
    # only ever bites on the pit straight, where the programme is 0 wide; clamp
    # anyway so a band can never start inboard of the mesh's own inner edge.
    inner = np.maximum(e, ve + np.maximum(wA + wG, wX))     # band V starts here
    b = np.clip(barrier_offset(S, side),
                np.minimum(inner + 0.5, pe - 0.40), pe - 0.20)
    out = {}
    # band A — runoff asphalt: dense against the track, coarse far out
    tA = np.linspace(0.0, 1.0, 13) ** 1.35
    out["A"] = (ve[:, None] + wA[:, None] * tA[None, :], wA)
    # band X — apex gravel sub-base
    tX = np.linspace(0.0, 1.0, 9)
    out["X"] = (ve[:, None] + wX[:, None] * tX[None, :], wX)
    # band G — outer gravel sub-base
    tG = np.linspace(0.0, 1.0, 11)
    out["G"] = ((ve + wA)[:, None] + wG[:, None] * tG[None, :], wG)
    # band V — the verge.  Three segments: inner->barrier-2.4, the 4.8 m
    # maintenance strip round the barrier, barrier+2.4->platform_edge.
    half = np.minimum(2.4, 0.40 * np.maximum(b - inner, 0.05))
    half = np.minimum(half, 0.80 * np.maximum(pe - b, 0.05))
    a0, a1 = b - half, b + half
    t1 = np.linspace(0.0, 1.0, 24)[None, 1:] ** 1.55
    t2 = np.linspace(0.0, 1.0, 8)[None, 1:]
    t3 = np.linspace(0.0, 1.0, 7)[None, 1:]
    V = np.concatenate([
        inner[:, None],
        inner[:, None] + (a0 - inner)[:, None] * t1,
        a0[:, None] + (a1 - a0)[:, None] * t2,
        a1[:, None] + (pe - a1)[:, None] * t3], axis=1)
    out["V"] = (V, pe - inner)
    return out


def build_platform(mb_a, mb_g, mb_v, side, stats):
    """The whole platform for one side, in four material bands."""
    for (r0, r1) in _platform_runs(side):
        s = r0
        while s < r1 - 1e-6:
            tier = int(hero_tier(np.array([min(r1 - 1e-6, s + 6.0)]), side)[0])
            ds = _platform_ds(side, min(r1 - 1e-6, s + 6.0), tier)
            e = min(r1, s + max(24.0, 40.0 * ds))
            n = max(3, int(round((e - s) / ds)) + 1)
            S = np.linspace(s, e, n)
            _platform_chunk(mb_a, mb_g, mb_v, S, side, stats)
            s = e


def _band_spans(wid, n):
    """Index ranges of a chunk over which a band exists, padded by one station
    on each side so the band tapers to a point instead of ending in a wedge the
    verge band would then have to cover twice."""
    m = wid > 1e-6
    out, i = [], 0
    while i < n:
        if not m[i]:
            i += 1
            continue
        j = i
        while j < n and m[j]:
            j += 1
        a, b = max(0, i - 1), min(n, j + 1)
        if b - a >= 3:
            out.append((a, b))
        i = j
    return out


def _platform_chunk(mb_a, mb_g, mb_v, S, side, stats):
    rows = _lat_rows(S, side)
    n = len(S)
    ve = verge_edge(S)
    for key, mb in (("A", mb_a), ("X", mb_g), ("G", mb_g), ("V", mb_v)):
        lat_all, wid = rows[key]
        spans = [(0, n)] if key == "V" else _band_spans(wid, n)
        for (a, b) in spans:
            Ss = S[a:b]
            lat = lat_all[a:b]
            ni, nj = len(Ss), lat.shape[1]
            SS = np.repeat(Ss[:, None], nj, 1)
            Z = platform_z(SS, lat, side)
            x, y, _ = CL.point(SS, lat, side, bank=False)
            P = np.stack([x, y, Z], axis=-1)
            d = lat - ve[a:b][:, None]
            if key == "A":
                rub = clamp01(1.35 * np.exp(-d / 2.4))
                wv = np.stack([np.full(ni * nj, 0.5), np.zeros(ni * nj),
                               rub.ravel(), np.zeros(ni * nj)], axis=1)
                stats["runoff_area_m2"] += _trapz(wid[a:b], Ss)
            elif key == "V":
                bo = barrier_offset(SS, side)
                near = clamp01(1.0 - np.abs(lat - bo) / 3.2)
                wv = np.stack([np.full(ni * nj, 0.5), np.zeros(ni * nj),
                               near.ravel(), np.zeros(ni * nj)], axis=1)
                stats["platform_area_m2"] += _trapz(wid[a:b], Ss)
            else:
                wv = np.tile([0.5, 0.0, 0.0, 0.0], (ni * nj, 1))
            mb.add_grid(W3(P),
                        uv=np.stack([d.ravel(), SS.ravel()], axis=1),
                        wear=wv, paint=np.tile([0, 0, 0, 1], (ni * nj, 1)),
                        uid=np.tile([0.5, 0, 0, 1], (ni * nj, 1)),
                        mat=0, smooth=True)
    # --- the hidden flange under build_surface's painted verge --------------
    # ONLY where there IS a painted verge to hide under.  Where the Beat-4
    # ribbon has taken the inboard part of the band, build_surface's road is the
    # neighbour, not its verge, and the joint is the contract's 0.30 m sawn one.
    ni = n
    e = ve
    # (No outward lip: band A's first row is already at exactly u = ve on exactly
    # ground_z, so the two share that edge bit for bit.  A lip would be a
    # coplanar pair between BR_Verge and BR_Runoff, which is the defect class
    # this round is closing, to save 7 ray-ties out of 104 probe stations.)
    if float(np.max(platform_inner(S, side) - ve)) <= 1e-6:
        zg = ground_z(S, e, side)
        F = np.zeros((ni, 3, 3))
        for j, (du, dz) in enumerate(((0.0, 0.0), (0.0, -PLATFORM_TUCK_Z),
                                      (-PLATFORM_TUCK, -PLATFORM_TUCK_Z))):
            x, y, _ = CL.point(S, e + du, side, bank=False)
            F[:, j, 0] = x
            F[:, j, 1] = y
            F[:, j, 2] = zg + dz
        mb_v.add_grid(W3(F), uv=np.zeros((ni * 3, 2)),
                      wear=np.tile([0.6, 0, 0.9, 0], (ni * 3, 1)),
                      paint=np.tile([0, 0, 0, 1], (ni * 3, 1)),
                      uid=np.tile([0.5, 0, 0, 1], (ni * 3, 1)), mat=0,
                      smooth=False)

    # --- the retaining bank where the corridor meets its own other branch ---
    # Where §4b's ownership clamp bites AND §4c has not filled the annulus, the
    # platform's outer edge is not the corridor rim: it is the medial axis, and
    # on the far side of it the ground belongs to the S4/T5 leg and is up to
    # 6.7 m higher.  Left as a free edge that is a hole in the world seen from
    # below, so it gets a battered retaining face down to whatever is over there.
    oe = platform_reach(S, side)
    pe_full = platform_edge(S, side)
    if float(np.min(pe_full - oe)) <= 0.05:
        return
    zt = platform_z(S, oe, side)
    xo, yo, _ = CL.point(S, oe + 1.6, side, bank=False)
    wxo, wyo = CL.to_world(xo, yo)
    zo, _own = WC.world_ground_z(np.asarray(wxo), np.asarray(wyo))
    zo = np.where(np.isfinite(zo), zo, zt - 1.2)
    depth = np.clip(zt - zo + 0.9, 0.9, 14.0)
    nvv = 4
    G = np.zeros((ni, nvv, 3))
    for j in range(nvv):
        f = j / (nvv - 1.0)
        lat = oe + 0.55 * f * f                     # 1 : 2.6 batter
        x, y, _ = CL.point(S, lat, side, bank=False)
        G[:, j, 0] = x
        G[:, j, 1] = y
        G[:, j, 2] = zt - depth * f
    mb_v.add_grid(W3(G),
                  uv=np.stack([np.repeat(oe - ve, nvv),
                               np.repeat(S, nvv)], axis=1),
                  wear=np.tile([0.7, 0, 0.4, 0], (ni * nvv, 1)),
                  paint=np.tile([0, 0, 0, 1], (ni * nvv, 1)),
                  uid=np.tile([0.5, 0, 0, 1], (ni * nvv, 1)), mat=0, smooth=True)


# ----------------------------------------------------------------------------
# 20.  real woven verticals in the declared hero window
# ----------------------------------------------------------------------------

def build_wire_window(mb, nd, stats):
    """Real 3-D vertical wires, replacing the vertical card, inside the declared
    hero windows.  Uses the SAME per-span sag parameters as `build_fence_span`
    so the real verticals and the analytic horizontals lie on one surface."""
    P, S, L, side = nd["P"], nd["s"], nd["L"], nd["side"]
    sgn = -float(side)
    zr = MESH_Z1 - MESH_Z0
    nv = 13
    vv = np.linspace(MESH_Z0, MESH_Z1, nv)
    v01 = (vv - MESH_Z0) / zr
    th = np.linspace(0, 2 * math.pi, 4, endpoint=False) + math.pi / 4
    CH = np.stack([np.cos(th), np.sin(th)], axis=1) * (FENCE_WIRE_D * 0.5)
    for (a, b, sd) in WIRE_WINDOWS:
        if sd != side:
            continue
        ua = float(np.interp(a, S, L))
        ub = float(np.interp(b, S, L))
        VS, FS, base_n = [], [], 0
        for pi in range(math.ceil(ua / FENCE_SPAN), int(ub / FENCE_SPAN)):
            u0 = pi * FENCE_SPAN
            sj = float(np.interp(u0 + FENCE_SPAN * 0.5, L, S))
            if not bool(cor_get("fence", np.array([sj]), side)[0]):
                continue
            if is_gate_span(sj, side):
                continue
            seed = 9100 + (side > 0) * 5 + pi * 31       # identical to the card
            slack = 0.25 + 0.75 * h01(seed, 3)
            bow = (h01(seed, 5) - 0.42) * (0.075 + 0.115 * slack)
            sag = (h01(seed, 7) - 0.5) * 0.055 * slack
            droop = (0.008 + 0.052 * slack)
            dent_a = 0.0
            if h01(seed, 11) < 0.13:
                dent_a = (0.06 + 0.22 * h01(seed, 13)) * (1 if h01(seed, 17) < 0.5 else -1)
            dent_c = 0.25 + 0.5 * h01(seed, 19)
            wear, paint, _, _ = node_attrs(np.array([sj]), side)
            phase = h01(seed, 31) * FENCE_PITCH
            nw = int(FENCE_SPAN / FENCE_PITCH)
            for wi in range(nw):
                uu = u0 + phase + wi * FENCE_PITCH
                if uu >= u0 + FENCE_SPAN or uu > ub:
                    break
                t01 = (uu - u0) / FENCE_SPAN
                c, T2, R2 = _local_frame(P, L, uu, side)
                A2 = sgn * R2
                bb, dzz = _span_shape(np.full(nv, t01), v01, sag, bow, droop,
                                      dent_c, dent_a)
                pts = (c[None, :]
                       + np.array([0.0, 0.0, 1.0])[None, :] * (vv + dzz)[:, None]
                       + A2[None, :] * bb[:, None])
                G = pts[:, None, :] + CH[None, :, 0][..., None] * T2 \
                    + CH[None, :, 1][..., None] * A2
                VS.append(G.reshape(-1, 3))
                FS.append(ring_faces(nv, 4, closed=True) + base_n)
                base_n += nv * 4
                stats["hero_wires"] += 1
        if not VS:
            continue
        V = np.concatenate(VS, axis=0)
        F = np.concatenate(FS, axis=0)
        nvv = len(V)
        mb.add(W3(V), F, mat=0, uv=np.zeros((nvv, 2)),
               wear=np.tile([0.45, 0.25, 0.0, 0.0], (nvv, 1)),
               paint=np.tile([0, 0, 0, 1], (nvv, 1)),
               uid=np.tile([0.5, 0, 0, 1], (nvv, 1)), smooth=True)


# ----------------------------------------------------------------------------
# 21.  the transit corridor (spec §10.5) — walled apron run + pit-exit portal
# ----------------------------------------------------------------------------

def transit_route(t):
    """world-frame points on the breach-exit route at route stations `t`."""
    X, Y, H = WC.access_route_arrays(np.asarray(t, float))
    return np.stack([X, Y, np.full_like(X, WC.APRON_Z)], axis=1), H


# --------------------------------------------------------------------------
#  THE WALLS STAND ON THE CONTRACT.  (§21 correction table, RETIRED.)
# --------------------------------------------------------------------------
#  There used to be a correction table here.  It read `telemetry/telemetry.csv`,
#  projected every transit frame onto `WC.access_route_arrays`, padded the result
#  by the swept car box and pushed the corridor walls OUTBOARD wherever the car
#  appeared to be driving through them.  It existed for exactly one reason: the
#  telemetry's transit merge and `WC.access_route_point` were not the same curve.
#  `tools/build_telemetry.py` interpolated the merge as a CHORD across the leg
#  endpoints while the contract declares it as an R150 / 40 deg arc, and the
#  sagitta between them put the car up to +8.95 m left of its own road.
#
#  R2-042 fixed the telemetry: the merge is now evaluated as the declared arc and
#  the two curves agree.  The table is not merely redundant now, it is HARMFUL —
#  MEASURED, this module's own `transit_wall_offset` over t 6 -> 96, both sides:
#
#      telemetry           north max push   pushed over   south max push
#      pre-R2-042 (chord)      +3.347 m        32.4 m         0.000 m
#      post-R2-042 (arc)        0.000 m         0.0 m         0.000 m
#      table deleted            0.000 m         0.0 m         0.000 m
#
#  and `assembly5.blend`, built against the chord telemetry, carries it: the
#  `BR_Transit_NorthWall` inner face runs 7.840 m out to route t 63 and then
#  climbs to 11.173 m at t 96 — 3.333 m outboard of the contract, in the shot the
#  camera flies at 200 km/h.  The walls stand on `TRANSIT_NORTH_OFFSET_M` /
#  `TRANSIT_SOUTH_OFFSET_M` exactly, everywhere, and `placement_gate` says so.
#
#  Do not reintroduce this.  If a future telemetry disagrees with the contract
#  again, the disagreement belongs to whichever file moved, not to the barriers.


def transit_wall_offset(t, side):
    """The wall face offset built, in metres, signed (+ = left of travel).

    `WC.TRANSIT_NORTH_OFFSET_M` / `_SOUTH_` exactly.  No correction, no
    telemetry read, no dependence on anything outside the contract.
    """
    base = (WC.TRANSIT_NORTH_OFFSET_M if side > 0 else WC.TRANSIT_SOUTH_OFFSET_M)
    return np.full(np.shape(t), float(base)) if np.ndim(t) else float(base)


def transit_wall_report():
    """Standing assertion that the corridor walls are ON the contract.

    Every `max_push_m` here must be 0.000.  It was 3.347 on the north wall
    while the retired correction table above was live; the number is kept
    measurable so a reintroduction cannot be silent.
    """
    r = {}
    for side in (+1, -1):
        t0, t1 = WC.transit_wall_span(side)
        tt = np.linspace(t0, t1, 400)
        base = (WC.TRANSIT_NORTH_OFFSET_M if side > 0
                else WC.TRANSIT_SOUTH_OFFSET_M)
        off = np.asarray(transit_wall_offset(tt, side), float)
        d = np.abs(off - base)
        r["north" if side > 0 else "south"] = dict(
            contract_offset_m=base,
            max_push_m=round(float(d.max()), 3),
            pushed_over_m=round(float((d > 0.005).mean() * (t1 - t0)), 1),
            span=[t0, t1],
            on_contract=bool(d.max() <= 1e-9))
    return r


def _transit_wall_path(side, n):
    """(route stations, wall base points, tangents, right-of-travel unit).

    Contract §6.2.  The corridor is ASYMMETRIC and that is a decision, not a
    compromise: the north retaining wall runs the spec-literal 90 m (t 6->96),
    the south tyre wall stops at t = 90 because the R150 merge arc converges and
    at t = 95 its face is 0.36 m INSIDE the painted verge.  `build_architecture`
    solved the same collision by cutting the whole corridor to 70 m, throwing
    away 20 m of the camera's walled run to fix a problem only one wall has;
    `ARCH_ApronCorridor` is deleted by name instead (CORRIDOR_DELETE_NAMES).

    The face offset is `transit_wall_offset`, which is the contract's number
    except where the DRIVEN CAR BOX is on the wrong side of it — see above.
    """
    t0, t1 = WC.transit_wall_span(side)
    tt = np.linspace(t0, t1, n)
    off = np.asarray(transit_wall_offset(tt, side), float)
    X, Y, H = WC.access_route_arrays(tt)
    P = np.stack([X - np.sin(H) * off, Y + np.cos(H) * off,
                  np.full(len(tt), WC.APRON_Z)], axis=1)
    T = np.stack([np.cos(H), np.sin(H), np.zeros(len(H))], axis=1)
    Rt = np.stack([np.sin(H), -np.cos(H), np.zeros(len(H))], axis=1)   # right of travel
    return tt, P, T, Rt


def build_terminal_nose(mb, base, T, Rt, seed=0, half_w=0.62, height=1.35,
                        reach=1.60):
    """A wrapped steel deflector nose closing the exposed end of a tyre wall.

    Half a swept ellipse in plan, tapering in height, with a rolled top edge —
    the standard treatment for a barrier terminal that faces oncoming traffic.
    Embedded by BASE_EMBED so a 12.5 deg sun cannot open a lit gap beneath it.
    """
    base = np.asarray(base, float).copy()
    base[2] -= BASE_EMBED
    na, nv = 11, 5
    th = np.linspace(-math.pi * 0.5, math.pi * 0.5, na)
    G = np.zeros((na, nv, 3))
    for i, a in enumerate(th):
        lat = math.cos(a) * half_w
        lon = math.sin(a) * reach * 0.5 + reach * 0.5
        for j in range(nv):
            f = j / (nv - 1.0)
            h = height * (1.0 - 0.30 * f * f) * (0.55 + 0.45 * math.cos(a) ** 0.4)
            wob = 0.014 * (h01(seed, i, j) - 0.5)
            G[i, j] = (base + T * lon + Rt * (lat * (1.0 - 0.18 * f) + wob)
                       + np.array([0.0, 0.0, h * f]))
    n = na * nv
    mb.add_grid(G, uv=np.stack([np.repeat(th, nv), np.tile(np.arange(nv) / 4.0, na)],
                               axis=1),
                wear=np.tile([0.30, 0.10, 0.0, 0.0], (n, 1)),
                paint=np.tile([0, 0, 0, 1], (n, 1)),
                uid=np.tile([h01(seed, 5), 0, 0, 1], (n, 1)), mat=0, smooth=True)


def build_transit(colls, mats, stats):
    # --- north side: 2.4 m cut-faced concrete retaining wall at +8.0 m -----
    uu, Pn, T, Rt = _transit_wall_path(+1, 121)
    mb = MB(PFX + "Transit_NorthWall")
    nv = 9
    vv = np.linspace(-BASE_EMBED, WC.TRANSIT_NORTH_TOP_Z, nv)
    G = np.zeros((len(uu), nv, 3))
    face = 0.14 * (fbm2(uu[:, None] / 2.2, vv[None, :] / 1.4, seed=3111, oct=4) - 0.5)
    face += 0.05 * (fbm2(uu[:, None] / 0.4, vv[None, :] / 0.3, seed=3122, oct=3) - 0.5)
    for j in range(nv):
        G[:, j, :] = Pn + np.array([0, 0, 1.0]) * vv[j] + Rt * face[:, j][:, None]
    nn = len(uu) * nv
    mb.add_grid(G, uv=np.stack([np.repeat(uu, nv), np.tile(vv, len(uu))], axis=1),
                wear=np.tile([0.55, 0, 0.1, 0], (nn, 1)),
                paint=np.tile([0, 0, 0, 1], (nn, 1)),
                uid=np.stack([np.repeat(hash01(np.rint(uu / 3.0).astype(np.int64),
                                               np.full(len(uu), 77)), nv),
                              np.zeros(nn), np.zeros(nn), np.ones(nn)], axis=1),
                mat=0, smooth=False)
    # coping
    Gc = np.zeros((len(uu), 4, 3))
    zt = WC.TRANSIT_NORTH_TOP_Z
    cp = np.array([(-0.10, zt), (0.16, zt + 0.02), (0.16, zt + 0.16), (-0.10, zt + 0.14)])
    for j in range(4):
        Gc[:, j, :] = Pn + np.array([0, 0, 1.0]) * cp[j, 1] + Rt * cp[j, 0]
    mb.add_grid(Gc, uv=np.stack([np.repeat(uu, 4), np.tile(cp[:, 1], len(uu))], axis=1),
                wear=np.tile([0.45, 0, 0.05, 0], (len(uu) * 4, 1)),
                paint=np.tile([0, 0, 0, 1], (len(uu) * 4, 1)),
                uid=np.tile([0.6, 0, 0, 1], (len(uu) * 4, 1)), mat=0, smooth=False)
    mb.emit(colls["Transit"], [mats["concrete"]])

    # --- south side: 2.0 m tyre stack + debris fence, gate portal at x=+58 --
    uu, Ps, T, Rt = _transit_wall_path(-1, 113)
    mbt = MB(PFX + "Transit_TyreWall")
    tp = WC.TRANSIT_PORTAL_X - WC.ACCESS_GLASS_X          # route station of the gate
    gate = np.abs(uu - tp) < WC.TRANSIT_PORTAL_CLEAR_M
    idx = np.where(~gate)[0]
    runs = []
    if len(idx):
        st = idx[0]
        for q in range(1, len(idx)):
            if idx[q] != idx[q - 1] + 1:
                runs.append((st, idx[q - 1]))
                st = idx[q]
        runs.append((st, idx[-1]))
    # the last 4.5 m of the run is the TERMINAL: the stack steps down and the
    # exposed end gets a wrapped steel deflector nose.  A tyre wall that simply
    # stops in front of a merging pit exit is the one thing worse than no wall.
    term_t = WC.TRANSIT_SOUTH_S1 - 4.5
    for ri, (a, b) in enumerate(runs):
        if b - a < 3:
            continue
        cut = int(np.searchsorted(uu, term_t))
        if a < cut < b:
            build_tyre_wall(mbt, Ps[a:cut + 1], rows=2, courses=3, side_sign=-1.0,
                            seed0=880 + ri, stats=stats, belt=True)
            build_tyre_wall(mbt, Ps[cut:b + 1], rows=1, courses=2, side_sign=-1.0,
                            seed0=980 + ri, stats=stats, belt=True)
        else:
            rows, crs = (1, 2) if uu[a] >= term_t else (2, 3)
            build_tyre_wall(mbt, Ps[a:b + 1], rows=rows, courses=crs, side_sign=-1.0,
                            seed0=880 + ri, stats=stats, belt=True)
    mbt.emit(colls["Transit"], [mats["rubber"], mats["belt"]])

    # portal frame at the gate + the terminal nose
    mbp = MB(PFX + "Transit_Portal")
    gi = np.where(gate)[0]
    if len(gi) > 3:
        # INSIDE the opening, not on its edges, and set back.  A post standing
        # on the last sample of the gap sat inside the terminal tyre of each run
        # — 34 triangle intersections on the BVH gate.  0.75 m in and 0.32 m
        # back buys the clearance and still leaves a 3.7 m gate, which a
        # recovery truck fits through.
        for q in (gi[0] + 1, gi[-1] - 1):
            base = Ps[q] + Rt[q] * 0.32
            TT = tube(np.linspace(base, base + np.array([0, 0, 4.6]), 3), 0.085, seg=8)
            mbp.add(TT.reshape(-1, 3), ring_faces(3, 8, closed=True), mat=0,
                    uv=np.zeros((24, 2)), wear=np.tile([0.4, 0.2, 0, 0], (24, 1)),
                    paint=np.tile([0, 0, 0, 1], (24, 1)),
                    uid=np.tile([0.5, 0, 0, 1], (24, 1)), smooth=True)
        hd = np.linspace(Ps[gi[0] + 1] + Rt[gi[0] + 1] * 0.32 + np.array([0, 0, 4.55]),
                         Ps[gi[-1] - 1] + Rt[gi[-1] - 1] * 0.32 + np.array([0, 0, 4.55]), 6)
        TT = tube(hd, 0.075, seg=8)
        mbp.add(TT.reshape(-1, 3), ring_faces(6, 8, closed=True), mat=0,
                uv=np.zeros((48, 2)), wear=np.tile([0.4, 0.2, 0, 0], (48, 1)),
                paint=np.tile([0, 0, 0, 1], (48, 1)),
                uid=np.tile([0.5, 0, 0, 1], (48, 1)), smooth=True)
    # ahead of the last tyre, not through it: the stack's terminal tyre has its
    # front face at the path end + 0.02 m, and a nose starting at the path end
    # put 34 triangles inside it.
    build_terminal_nose(mbp, Ps[-1] + T[-1] * 0.36, T[-1], Rt[-1], seed=917)
    mbp.emit(colls["Transit"], [mats["steel"]])

    # --- debris fence above the tyre wall -----------------------------------
    mbf = MB(PFX + "Transit_Fence")
    mbm = MB(PFX + "Transit_FenceMesh")
    posts = []
    for q in range(0, len(uu), 8):
        base = Ps[q] + Rt[q] * 0.30
        posts.append(dict(u=uu[q], s=0.0, base=base,
                          axis=np.array([0.0, 0.0, 1.0]), T=T[q], A=Rt[q],
                          h=4.4, pi=q))
    for k in range(len(posts) - 1):
        p0, p1 = posts[k], posts[k + 1]
        sp = 9100 + p0["pi"] * 31
        wear = np.array([[0.42, 0.18, 0.05, 0.0]])
        paint = np.array([[0, 0, 0, 1.0]])
        nu, nv2 = 14, 8
        U01 = np.linspace(0, 1, nu)
        V01 = np.linspace(0, 1, nv2)
        UU, VV = np.meshgrid(U01, V01, indexing='ij')
        A0, A1 = p0["base"], p1["base"]
        slen = float(np.linalg.norm(A1 - A0))
        z0, z1 = 2.15, 4.30
        bow = (h01(sp, 5) - 0.45) * 0.09
        b_, dz = _span_shape(UU, VV, 0.02, bow, 0.02, 0.5, 0.0)
        Av = p0["A"][None, None, :] * (1 - UU[..., None]) + p1["A"][None, None, :] * UU[..., None]
        base = A0[None, None, :] + (A1 - A0)[None, None, :] * UU[..., None]
        Zz = z0 + (z1 - z0) * VV + dz
        S0 = base + np.array([0, 0, 1.0])[None, None, :] * Zz[..., None] + Av * b_[..., None]
        for layer, off in ((0, 0.0), (1, 0.0045)):
            mbm.add_grid(S0 + Av * off,
                         uv=np.stack([(UU * slen).ravel(), (z0 + (z1 - z0) * VV).ravel()], axis=1),
                         wear=np.repeat(wear, UU.size, axis=0),
                         paint=np.repeat(paint, UU.size, axis=0),
                         uid=np.tile([h01(sp, 31 + layer), 0, 0, 1], (UU.size, 1)),
                         mat=layer, smooth=True)
            stats["fence_spans"] += 0.5
        for pp in (p0, p1):
            prof = I_SECTION
            G2 = np.zeros((2, len(prof), 3))
            for si, hgt in enumerate((0.0, 4.5)):
                G2[si] = (pp["base"] + np.array([0, 0, 1.0]) * hgt) + \
                    prof[:, 0][:, None] * pp["T"] + prof[:, 1][:, None] * pp["A"]
            nn2 = 2 * len(prof)
            mbf.add(G2.reshape(-1, 3), ring_faces(2, len(prof), closed=True), mat=0,
                    uv=np.stack([np.tile(prof[:, 0] * 5.0, 2),
                                 np.repeat([0.0, 4.5], len(prof))], axis=1),
                    wear=np.repeat(wear, nn2, axis=0),
                    paint=np.repeat(paint, nn2, axis=0),
                    uid=np.tile([0.5, 0, 0, 1], (nn2, 1)), smooth=False)
    mbf.emit(colls["Transit"], [mats["steel"]])
    mbm.emit(colls["Transit"], [mats["fenceV"], mats["fenceH"]])

# ----------------------------------------------------------------------------
# 22.  hairpin infield tyre wall  (spec §11 Beat 5: "4 m from the tyre wall")
# ----------------------------------------------------------------------------

T4_WALL_LAT = 13.10          # camera sits on the inside kerb at lat 9.0, z 0.85
T4_WALL_S = (912.0, 1058.0)


def build_t4_tyre_wall(mb, stats):
    s = np.arange(T4_WALL_S[0], T4_WALL_S[1], 0.5)
    lat = np.full_like(s, T4_WALL_LAT)
    x, y, _ = CL.point(s, lat, +1, bank=False)
    # on `platform_z`, not on `ground_z`: the wall stands on the graded
    # maintenance strip beside the barrier, which is 12-60 mm below the datum.
    # Seating it on the datum would float the bottom course by up to 40 mm, and
    # the beat sheet puts a 21 mm lens 4.0 m from this wall.
    z = platform_z(s, lat, +1) - BASE_EMBED
    P = W3(np.stack([x, y, z], axis=1))
    build_tyre_wall(mb, P, rows=3, courses=3, side_sign=+1.0, seed0=404,
                    stats=stats, belt=True)


# ----------------------------------------------------------------------------
# 23.  marshal gates in the debris fence
# ----------------------------------------------------------------------------

GATE_STATIONS = [305.0, 742.0, 968.0, 1032.0, 1288.0, 1590.0, 1782.0, 1930.0,
                 2196.0, 2372.0, 2560.0, 2726.0, 2905.0, 3092.0, 3300.0, 3612.0]


def is_gate_span(s, side):
    for gs in GATE_STATIONS:
        if abs(((s - gs + LAP_LEN * 0.5) % LAP_LEN) - LAP_LEN * 0.5) < FENCE_SPAN * 0.5:
            return True
    return False


def build_gate(mb_struct, mb_mesh, p0, p1, side, sgn, stats):
    """Marshal access gate: welded tube frame + a leaf standing part-open.

    EVERY EMIT HERE GOES THROUGH `W3`.  It did not, and that was the second half
    of the assembly review's defect #1: `p0["base"]` and `p0["A"]` come from
    `_local_frame` on the DESIGN-frame node polyline, like every other primitive
    in this module, but this one function pushed them into the mesh unrotated.
    All 16 marshal gates were therefore built at their design coordinates read as
    world ones — 40 degrees and a 350 m pivot away from the barrier they belong
    to.  Fifteen of them landed in open country where nothing noticed;
    `BR_FenceStruct_R07`'s (GATE_STATIONS 1590.0, right side) landed ON THE T6
    ESSES, 168 struct + 96 mesh verts inside `verge_edge` at s 1546.1-1558.1,
    u -8.86..-5.24, up to 3.756 m inside the track edge and 2.772 m above the
    tarmac.  A single missing coordinate transform, invisible in isolation
    because a gate 26 m from its own barrier still renders as a gate.
    """
    seed = 9500 + int(p0["s"]) + (side > 0)
    wear = np.array([[0.30 + 0.4 * h01(seed, 3), 0.15, 0.05, 0.0]])
    paint = np.array([[0.0, 0.0, 0.0, 1.0]])
    A0, A1 = p0["base"], p1["base"]
    up = np.array([0.0, 0.0, 1.0])
    z0, z1 = 1.05, 3.05
    frame = [(A0, A1, z0), (A0, A1, z1)]
    for (a, b, z) in frame:
        pts = np.linspace(a + up * z, b + up * z, 4)
        TT = tube(pts, 0.032, seg=6)
        n = 4 * 6
        mb_struct.add(W3(TT).reshape(-1, 3), ring_faces(4, 6, closed=True), mat=0,
                      uv=np.zeros((n, 2)), wear=np.repeat(wear, n, axis=0),
                      paint=np.repeat(paint, n, axis=0),
                      uid=np.tile([0.5, 0, 0, 1], (n, 1)), smooth=True)
    for a in (A0, A1):
        pts = np.linspace(a + up * z0, a + up * z1, 3)
        TT = tube(pts, 0.032, seg=6)
        n = 3 * 6
        mb_struct.add(W3(TT).reshape(-1, 3), ring_faces(3, 6, closed=True), mat=0,
                      uv=np.zeros((n, 2)), wear=np.repeat(wear, n, axis=0),
                      paint=np.repeat(paint, n, axis=0),
                      uid=np.tile([0.5, 0, 0, 1], (n, 1)), smooth=True)
    # the leaf, hinged on A0, standing open by 8-38 degrees
    ang = math.radians(8.0 + 30.0 * h01(seed, 7))
    ax = (A1 - A0)
    span = float(np.linalg.norm(ax))
    ax /= max(1e-9, span)
    nrm = p0["A"]
    nu, nv2 = 8, 6
    U01 = np.linspace(0, 1, nu)
    V01 = np.linspace(0, 1, nv2)
    UU, VV = np.meshgrid(U01, V01, indexing='ij')
    dirv = ax * math.cos(ang) + nrm * math.sin(ang)
    S0 = (A0[None, None, :] + dirv[None, None, :] * (UU * span * 0.96)[..., None]
          + up[None, None, :] * (z0 + 0.06 + (z1 - z0 - 0.12) * VV)[..., None])
    for layer, off in ((0, 0.0), (1, 0.0045)):
        nn = UU.size
        mb_mesh.add_grid(W3(S0 + (nrm * off)[None, None, :]),
                         uv=np.stack([(UU * span).ravel(),
                                      (z0 + (z1 - z0) * VV).ravel()], axis=1),
                         wear=np.repeat(wear, nn, axis=0),
                         paint=np.repeat(paint, nn, axis=0),
                         uid=np.tile([h01(seed, 11 + layer), 0, 0, 1], (nn, 1)),
                         mat=layer, smooth=True)
    # leaf frame tubes
    for (a, b) in ((S0[0, 0], S0[-1, 0]), (S0[0, -1], S0[-1, -1]),
                   (S0[-1, 0], S0[-1, -1])):
        TT = tube(np.linspace(a, b, 3), 0.024, seg=5)
        n = 3 * 5
        mb_struct.add(W3(TT).reshape(-1, 3), ring_faces(3, 5, closed=True), mat=0,
                      uv=np.zeros((n, 2)), wear=np.repeat(wear, n, axis=0),
                      paint=np.repeat(paint, n, axis=0),
                      uid=np.tile([0.5, 0, 0, 1], (n, 1)), smooth=True)
    stats["gates"] += 1


# ----------------------------------------------------------------------------
# 24.  build()
# ----------------------------------------------------------------------------

def build(scene=None, chunk_m=260.0, verbose=True):
    t0 = time.time()
    scene = scene or bpy.context.scene
    purge()
    root, colls = make_collections(scene)
    mats = build_materials()
    stats = dict(armco_panels=0, armco_posts=0, bolts=0, tecpro_blocks=0,
                 concrete_blocks=0, fence_posts=0, fence_spans=0, tyres=0,
                 stones=0, hero_wires=0, trap_area_m2=0.0, runoff_area_m2=0.0,
                 platform_area_m2=0.0, gates=0)
    objects = []
    WC.stamp(root)                     # which contract this build was made to

    for side in (+1, -1):
        nd = barrier_nodes(side)
        npan = nd["npanel"]
        per = max(20, int(chunk_m / PANEL_L))
        tag = "L" if side > 0 else "R"
        for ci, i0 in enumerate(range(0, npan, per)):
            i1 = min(npan, i0 + per)
            s_mid = float(nd["s"][(i0 + i1) // 2])
            tier = int(hero_tier(np.array([s_mid]), side)[0])
            bt = cor_get("btype", nd["s"][i0:i1], side)

            steelmask = (bt == B_ARMCO) | (bt == B_TECPRO3)
            if np.any(steelmask):
                mb = MB("%sArmco_%s%02d" % (PFX, tag, ci))
                g0 = None
                for q in range(len(steelmask) + 1):
                    on = q < len(steelmask) and steelmask[q]
                    if on and g0 is None:
                        g0 = q
                    elif not on and g0 is not None:
                        a, b = i0 + g0, i0 + q
                        n = build_armco(mb, nd, a, b, tier)
                        stats["armco_panels"] += (b - a)
                        stats["armco_posts"] += int(round(
                            (nd["L"][b] - nd["L"][a]) / POST_PITCH))
                        stats["bolts"] += max(0, n - (b - a) - int(
                            (nd["L"][b] - nd["L"][a]) / POST_PITCH))
                        g0 = None
                ob = mb.emit(colls["Armco"], [mats["steel"]])
                if ob:
                    objects.append(ob)
            if np.any(bt == B_TECPRO3):
                mb = MB("%sTecPro_%s%02d" % (PFX, tag, ci))
                build_tecpro(mb, nd, i0, i1, stats)
                ob = mb.emit(colls["TecPro"], [mats["tecpro"], mats["steel"]])
                if ob:
                    objects.append(ob)
            if np.any(bt == B_CONCRETE):
                mb = MB("%sConcrete_%s%02d" % (PFX, tag, ci))
                build_concrete(mb, nd, i0, i1, stats)
                ob = mb.emit(colls["Concrete"], [mats["concrete"]])
                if ob:
                    objects.append(ob)
            if np.any(cor_get("fence", nd["s"][i0:i1], side)):
                mbs = MB("%sFenceStruct_%s%02d" % (PFX, tag, ci))
                mbm = MB("%sFenceMesh_%s%02d" % (PFX, tag, ci))
                build_fence(mbs, mbm, nd, i0, i1, tier, stats)
                for (m_, c_, mm_) in ((mbs, "Fence", [mats["steel"]]),
                                      (mbm, "Fence", [mats["fenceV"], mats["fenceH"]])):
                    ob = m_.emit(colls[c_], mm_)
                    if ob:
                        objects.append(ob)
        # real woven verticals in the declared hero windows
        mbw = MB("%sFenceWire_%s" % (PFX, tag))
        build_wire_window(mbw, nd, stats)
        ob = mbw.emit(colls["FenceWire"], [mats["wire"]])
        if ob:
            objects.append(ob)
        # THE RUNOFF PLATFORM: verge_edge -> platform_edge, one continuous
        # surface in three material bands.  build_terrain builds no ground here.
        mb_a = MB("%sRunoff_%s" % (PFX, tag))
        mb_g = MB("%sSubbase_%s" % (PFX, tag))
        mb_v = MB("%sVerge_%s" % (PFX, tag))
        build_platform(mb_a, mb_g, mb_v, side, stats)
        for (m_, c_, mm_) in ((mb_a, "Runoff", [mats["runoff"]]),
                              (mb_g, "Gravel", [mats["gravel"]]),
                              (mb_v, "Platform", [mats["verge"]])):
            ob = m_.emit(colls[c_], mm_)
            if ob:
                objects.append(ob)

    # --- gravel traps ------------------------------------------------------
    left = STONE_BUDGET
    for (a, b, side, kind) in trap_zones():
        tag = "%s_%s_%d" % (kind, "L" if side > 0 else "R", int(a))
        mb = MB("%sTrap_%s" % (PFX, tag))
        mbs = MB("%sStones_%s" % (PFX, tag))
        left = build_gravel_trap(mb, mbs, a, b, side, kind, stats, left)
        for (m_, mm_) in ((mb, [mats["gravel"]]), (mbs, [mats["stone"]])):
            ob = m_.emit(colls["Gravel"], mm_)
            if ob:
                objects.append(ob)

    # --- hairpin tyre wall + transit corridor -------------------------------
    mbt = MB(PFX + "TyreWall_T4")
    build_t4_tyre_wall(mbt, stats)
    ob = mbt.emit(colls["TyreWall"], [mats["rubber"], mats["belt"]])
    if ob:
        objects.append(ob)
    build_transit(colls, mats, stats)
    objects += [o for o in colls["Transit"].objects]

    tri = 0
    vts = 0
    for ob in objects:
        if ob and ob.type == 'MESH':
            vts += len(ob.data.vertices)
            for p in ob.data.polygons:
                tri += max(1, p.loop_total - 2)
    stats["objects"] = len(objects)
    stats["verts"] = vts
    stats["tris"] = tri
    stats["build_s"] = round(time.time() - t0, 1)
    if verbose:
        print("[BR] " + json.dumps(stats, indent=1))
    return stats


# ----------------------------------------------------------------------------
# 25.  test-render harness  (NOT part of build(); lighting is another module)
# ----------------------------------------------------------------------------

def _look(loc, aim, lens=35.0, name="cam"):
    f = np.array(aim, dtype=np.float64) - np.array(loc, dtype=np.float64)
    f /= np.linalg.norm(f)
    up = np.array([0.0, 0.0, 1.0])
    if abs(f[2]) > 0.995:
        up = np.array([0.0, 1.0, 0.0])
    r = np.cross(f, up)
    r /= np.linalg.norm(r)
    u = np.cross(r, f)
    M = Matrix(((r[0], u[0], -f[0]), (r[1], u[1], -f[1]), (r[2], u[2], -f[2])))
    rot = M.to_euler()
    cd = bpy.data.cameras.new(PFX + "TESTCAM_" + name)
    cd.lens = lens
    cd.sensor_width = 36.0
    ob = bpy.data.objects.new(PFX + "TESTCAM_" + name, cd)
    ob.location = tuple(float(v) for v in loc)
    ob.rotation_euler = rot
    bpy.context.scene.collection.objects.link(ob)
    return ob


def _cl_world(s, lat, side):
    x, y, _ = CL.point(np.array([s]), np.array([lat]), side, bank=False)
    z = ground_z(np.array([s]), np.array([lat]), side)
    wx, wy = CL.to_world(x, y)
    return np.array([float(wx[0]), float(wy[0]), float(z[0])])


def test_cameras():
    cams = {}
    # 1. the doppler hover station, the real Beat-5 framing
    dop = np.array([-578.82, -47.47, 4.802])
    cams["doppler"] = (dop, _cl_world(2455.0, 0.0, -1) + np.array([0, 0, 1.0]), 35.0)
    # 2. straight at the fence from the hover station — 4 m of standoff
    cams["doppler_fence"] = (dop, _cl_world(2557.0, 30.0, -1) + np.array([0, 0, 2.2]), 24.0)
    # 3. down the fence line — analytic-LOD seam check, 6 m to 300 m in one frame
    cams["fence_lod"] = (_cl_world(2470.0, 25.5, -1) + np.array([0, 0, 2.0]),
                         _cl_world(2660.0, 29.0, -1) + np.array([0, 0, 2.6]), 50.0)
    # 4. the kerb-height hairpin camera (spec: inside kerb, z 0.85, 21 mm)
    hp = _cl_world(982.0, 9.0, +1) + np.array([0, 0, 0.85])
    cams["hairpin"] = (hp, _cl_world(1006.0, 8.5, -1) + np.array([0, 0, 0.9]), 21.0)
    # 5. the tyre wall at 4 m
    cams["hairpin_tyre"] = (hp, _cl_world(950.0, 13.2, +1) + np.array([0, 0, 1.1]), 35.0)
    # 6. gravel at close range
    gtrap = _cl_world(985.0, 13.0, -1)
    cams["gravel_macro"] = (gtrap + np.array([0, 0, 0.80]),
                            _cl_world(991.0, 17.5, -1) + np.array([0, 0, -0.15]), 50.0)
    # 7. Armco macro at the worst incident inside a hero window
    best = None
    for inc in HIST.inc:
        if inc["kind"] in ("hit", "heavy") and hero_tier(np.array([inc["s"]]), inc["side"])[0] >= 1:
            if best is None or inc["depth"] > best["depth"]:
                best = inc
    if best is None:
        best = HIST.inc[0]
    off = float(barrier_offset(np.array([best["s"]]), best["side"])[0])
    bp = _cl_world(best["s"], off, best["side"])
    cp = _cl_world(best["s"] - 7.5, off - 3.4, best["side"])
    cams["armco_macro"] = (cp + np.array([0, 0, 1.30]), bp + np.array([0, 0, 0.55]), 50.0)
    # 8. T1 braking zone from the air: runoff + gravel + TecPro + fence together
    t1 = _cl_world(300.0, -30.0, -1)
    cams["t1_wide"] = (t1 + np.array([0, 0, 62.0]), _cl_world(300.0, 40.0, -1), 35.0)
    # 9. 400 m of pit-straight barrier — the repeat hunt
    ps = _cl_world(3300.0, 34.0, -1)
    cams["repeat_hunt"] = (ps + np.array([0, 0, 12.0]), _cl_world(3560.0, 19.0, -1), 50.0)
    # 10. the transit corridor at rooftop height
    cams["transit"] = (np.array([26.0, -1.0, 6.2]), np.array([120.0, 16.0, 2.0]), 28.0)
    # 11. into the T4 gravel trap: rake, ruts, berms, lip and the TecPro behind
    cams["hairpin_trap"] = (_cl_world(958.0, 11.0, -1) + np.array([0, 0, 3.4]),
                            _cl_world(985.0, 26.0, -1) + np.array([0, 0, 0.0]), 35.0)
    # 12. TecPro at working distance — colour, fade, compression, missing caps
    tp = _cl_world(2712.0, float(barrier_offset(np.array([2712.0]), -1)[0]) - 4.2, -1)
    cams["tecpro_macro"] = (tp + np.array([0, 0, 1.9]),
                            _cl_world(2726.0, float(barrier_offset(
                                np.array([2726.0]), -1)[0]) - 1.4, -1) + np.array([0, 0, 0.7]),
                            50.0)

    # ---- THE CONTRACT CAMERAS.  These exist to show the five findings gone. --
    # Every one is placed in (station, lateral, side) and NOT by adding world-axis
    # offsets to a station point: the first version of these did the latter and
    # put `banked_runoff` 21 m above the runoff looking straight down at it from
    # 30 m, which rendered as a featureless grey field.  The camera-vs-geometry
    # probe in verify_vs_contract's sibling `camchk` found it; the render is what
    # made me go and look.
    #
    # 13. T10/T11 — the 294 km/h helicopter dive, and the exact place TER_Ground
    #     stood 0.387 m PROUD OF THE TARMAC.  Standing off the OUTSIDE of the
    #     complex at 34 m, looking back across the full banked section, so the
    #     cross-fall is read against the horizon and the banking is visibly
    #     carried out past the verge instead of stopping at it.
    cams["banked_runoff"] = (_cl_world(2120.0, 78.0, -1) + np.array([0, 0, 34.0]),
                             _cl_world(2240.0, 4.0, +1) + np.array([0, 0, 0.0]),
                             50.0)
    # 14. the whole cross-section of the T1 braking zone, from above the
    #     centreline: painted verge -> 45 m asphalt -> 12 m gravel -> verge ->
    #     TecPro -> fence.  If any of it is under dirt this frame says so.
    cams["platform_section"] = (_cl_world(352.0, 0.0, -1) + np.array([0, 0, 15.5]),
                                _cl_world(300.0, 46.0, -1) + np.array([0, 0, 1.0]),
                                35.0)
    # 15. the verge itself at working distance — the surface the user called
    #     "a grass gray line".  1.35 m lens height, looking along it.
    cams["verge_macro"] = (_cl_world(1420.0, 22.0, +1) + np.array([0, 0, 1.35]),
                           _cl_world(1478.0, 13.0, +1) + np.array([0, 0, 0.30]),
                           50.0)
    # 16. THE INNER WELD, grazing.  Lens 0.35 m above the painted verge on the
    #     pit straight, 30 m of joint in frame between build_surface's mesh (the
    #     test proxy) and this module's platform, into a 12.47 deg sun.  A gap,
    #     a ledge or a z-fight at verge_edge is a lit line here and nowhere else.
    cams["weld_grazing"] = (_cl_world(3300.0, 10.9, -1) + np.array([0, 0, 0.35]),
                            _cl_world(3332.0, 10.5, -1) + np.array([0, 0, 0.06]),
                            85.0)
    return cams


def set_fence_fade(scene=None, ref_width=3840.0):
    """Rescale the analytic weave-fade distances to the render width.

    The fade must begin where one mesh aperture drops under ~2 px.  That
    threshold is resolution-dependent, so preview renders and the 4K master
    would otherwise disagree.  Call this once after setting the render size.
    """
    scene = scene or bpy.context.scene
    w = scene.render.resolution_x * scene.render.resolution_percentage / 100.0
    k = max(0.08, w / ref_width)
    n = 0
    for mat in bpy.data.materials:
        if not mat.name.startswith(PFX) or not mat.node_tree:
            continue
        for nd in mat.node_tree.nodes:
            if nd.name == "BR_FENCE_FADE":
                nd.inputs[1].default_value = FENCE_FADE_NEAR * k
                nd.inputs[2].default_value = FENCE_FADE_FAR * k
                n += 1
    return n


def setup_test_proxy(scene):
    """TEST ONLY.  A stand-in racing surface so the barrier frames read as a
    circuit.  The real surface belongs to build_surface; nothing here is emitted
    by build().

    It is now built from `C.ground_z` out to EXACTLY `C.verge_edge(s)` — i.e. it
    is what `build_surface` is contractually obliged to hand me, minus its kerbs
    and its racing-line micro layer.  That makes it a TEST OF THE SEAM and not
    just set dressing: if the platform's inner weld is wrong, these frames show
    a lit gap or a ledge at the verge edge, which is precisely the defect class
    the assembly review found and nobody's isolated render could see.

    There is no verge/grass proxy any more.  There does not need to be: the
    ground from `verge_edge` to `platform_edge` is this module's own geometry,
    and if it is missing the frame should say so.
    """
    coll = bpy.data.collections.new(PFX + "TESTPROXY")
    scene.collection.children.link(coll)
    ma = bpy.data.materials.new(PFX + "TESTPROXY_asphalt")
    ma.use_nodes = True
    ma.node_tree.nodes["Principled BSDF"].inputs[0].default_value = (0.030, 0.030, 0.032, 1)
    ma.node_tree.nodes["Principled BSDF"].inputs[2].default_value = 0.55
    S = np.arange(0.0, LAP_LEN + 0.5, 0.5) % LAP_LEN
    S[-1] = LAP_LEN - 1e-6
    e = verge_edge(S)
    # full cross-section, centreline out to the painted verge edge on BOTH sides
    nD = 21
    D = np.linspace(-1.0, 1.0, nD)
    SS = S[:, None].repeat(nD, 1)
    U = D[None, :] * e[:, None]                       # SIGNED lateral
    Z = WC.ground_z(SS, U)
    X, Y, H, _ = WC.centreline_arrays(SS)
    Xw = X - np.sin(H) * U
    Yw = Y + np.cos(H) * U
    mb = MB(PFX + "TESTPROXY_track")
    mb.add_grid(np.stack([Xw, Yw, Z], axis=-1), mat=0, smooth=True)
    mb.emit(coll, [ma])


def setup_test_light(scene, sun=None, bg_strength=None):
    """TEST ONLY — and it is the CONTRACT'S light, not a stand-in.

    Every number is `world_contract` §13, which is `build_sky`'s shipped,
    measured value.  That matters here for one reason: the verge material covers
    237 960 m2 of this film and it was calibrated against `lambert_radiance`, so
    a test frame lit by anything else would tell me nothing about whether the
    calibration is right.  The old rig here (sun 1.45 W, dust_density 2.2, an
    assumed 12.5 deg) was exactly the class of private lighting that put
    build_terrain's turf 45 % out on key:fill.
    """
    ld = bpy.data.lights.new(PFX + "TESTSUN", 'SUN')
    ld.energy = WC.SUN_ENERGY
    ld.angle = math.radians(WC.SUN_ANGULAR_DIAM_DEG)
    ld.color = WC.SUN_COLOR
    ob = bpy.data.objects.new(PFX + "TESTSUN", ld)
    d = np.array(WC.SUN_DIR, dtype=np.float64)
    ob.rotation_euler = Vector((0.0, 0.0, 1.0)).rotation_difference(
        Vector(d.tolist())).to_euler()
    scene.collection.objects.link(ob)
    w = bpy.data.worlds.new(PFX + "TESTWORLD")
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    sky = nt.nodes.new("ShaderNodeTexSky")
    sky.sky_type = WC.SKY_MODEL                 # MULTIPLE_SCATTERING (no NISHITA)
    for k, v in (("sun_elevation", math.radians(WC.SUN_ELEV_DEG)),
                 ("sun_rotation", math.radians(WC.SKY_SUN_ROTATION_DEG)),
                 ("sun_disc", WC.SKY_SUN_DISC),
                 ("altitude", WC.SKY_ALTITUDE),
                 ("air_density", WC.SKY_AIR),
                 ("dust_density", WC.SKY_AEROSOL),
                 ("ozone_density", WC.SKY_OZONE)):
        try:
            setattr(sky, k, v)
        except Exception:
            pass
    bg.inputs[1].default_value = WC.SKY_STRENGTH
    nt.links.new(sky.outputs[0], bg.inputs[0])
    nt.links.new(bg.outputs[0], out.inputs[0])
    scene.world = w


def render_tests(names=None, res=(1280, 720), samples=96, sun=None, bg=None):
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    try:
        prefs = bpy.context.preferences.addons['cycles'].preferences
        prefs.compute_device_type = 'CUDA'
        prefs.get_devices()
        for d in prefs.devices:
            d.use = (d.type in ('CUDA', 'OPTIX'))
        scene.cycles.device = 'GPU'
    except Exception as e:
        print("[BR] GPU unavailable, CPU:", e)
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 6
    scene.cycles.transparent_max_bounces = 24
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.view_settings.view_transform = WC.VIEW_TRANSFORM
    scene.view_settings.look = WC.VIEW_LOOK
    scene.view_settings.exposure = WC.REFERENCE_EXPOSURE_EXTERIOR
    setup_test_light(scene)
    setup_test_proxy(scene)
    print("[BR] fence fade nodes retuned:", set_fence_fade(scene))
    os.makedirs(RENDER_DIR, exist_ok=True)
    cams = test_cameras()
    out = []
    for nm, (loc, aim, lens) in cams.items():
        if names and nm not in names:
            continue
        ob = _look(loc, aim, lens, nm)
        scene.camera = ob
        scene.render.filepath = os.path.join(RENDER_DIR, nm + ".png")
        t = time.time()
        bpy.ops.render.render(write_still=True)
        print("[BR] rendered %-16s %5.1f s -> %s" % (nm, time.time() - t,
                                                     scene.render.filepath))
        out.append(scene.render.filepath)
    return out


# ----------------------------------------------------------------------------

def _argv():
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


if __name__ == "__main__":
    args = _argv()
    if "--list-renders" in args:
        print("\n".join(test_cameras().keys()))
        sys.exit(0)
    st = build()
    if "--render" in args:
        i = args.index("--render")
        names = [a for a in args[i + 1:] if not a.startswith("--")] or None
        res = (1280, 720)
        sm = 96
        if "--res" in args:
            r = args[args.index("--res") + 1].split("x")
            res = (int(r[0]), int(r[1]))
        if "--samples" in args:
            sm = int(args[args.index("--samples") + 1])
        sun = float(args[args.index("--sun") + 1]) if "--sun" in args else 1.45
        bgv = float(args[args.index("--bg") + 1]) if "--bg" in args else 0.085
        render_tests(names, res=res, samples=sm, sun=sun, bg=bgv)
    if "--save" in args:
        p = args[args.index("--save") + 1]
        bpy.ops.wm.save_as_mainfile(filepath=p)
        print("[BR] saved", p)
