#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_dressing.py — trackside dressing for Circuit Vitrine (round 2)

Marshal posts, advertising boards (fictional brands only), tyre stacks,
braking-distance boards, corner signage, TV camera masts, PA horns, cable
runs, cones, bins, windsocks, flagpoles and painted runoff logos.

    /opt/blender-5.2.0-linux-x64/blender -b --factory-startup -P build_dressing.py
    ...  -P build_dressing.py -- --render doppler hairpin --res 1600x900 --samples 128
    ...  -P build_dressing.py -- --list-renders
    ...  -P build_dressing.py -- --render all --context      (barriers + surface too)

`build()` is idempotent: every datablock it owns is named `DR_*` and is purged
before the rebuild, so two consecutive calls give an identical scene.

THIS MODULE IS SUBORDINATE TO `world_contract.py`.  It owns no datum, no width
and no ground height of its own:

    ground_z(s, lat, side)   is world_contract.ground_z with a SIGNED lateral.
                             `side` is MANDATORY — the assembly review's finding
                             #1 was 150 objects placed by a datum expressed in
                             |lat|, which cannot carry banking and was 0.69 m out
                             at the verge edge before it fell a single metre.
    anchor(...)              the only way anything in this file touches the
                             ground.  It goes through world_contract.world_ground_z,
                             embeds by C.BASE_EMBED_M, records the point in
                             ANCHORS, and refuses to place outside the corridor.
    half_width / verge_edge  world_contract's (spec §9, transition OUTSIDE the
                             section).
    barrier_offset           build_barriers' clamped line, guarded (see §2).

Design notes live in build_dressing.md.  The short version:

  * NOTHING here is an instance.  No linked duplicates, no particle systems, no
    geometry-node instancing.  Every board, every post, every tyre, every cone
    is generated from its own parameter draw into its own vertex data.
  * A brand's LOGOTYPE repeats — that is what a brand is — but no two boards
    are the same board: size, layout, colour age, dirt, damage, mounting and
    the surface the print is mapped onto all differ per unit, and the module
    asserts signature uniqueness at build time.
  * Placement is derived, not sprinkled: marshal posts sit at corner exits with
    verified mutual sight lines and next to the barrier module's access gates;
    braking boards sit at real distances before real braking zones; boards go
    where a circuit can actually sell space (TV sight lines).
"""

import bpy
import bmesh  # noqa: F401  (kept for interactive debugging)
import math
import os
import sys
import json
import time
import numpy as np

# --------------------------------------------------------------------------- #
#  0.  paths, spec, the barrier-module contract                                 #
# --------------------------------------------------------------------------- #

HERE = os.path.dirname(os.path.abspath(__file__ if "__file__" in dir() else "."))
ROOT = os.path.dirname(HERE)
DOCS = os.path.join(ROOT, "docs")
SPEC_JSON = os.path.join(DOCS, "circuit_spec.json")
RENDER_DIR = os.path.join(ROOT, "render", "world", "dressing")

ROOT_COLL = "R2_Dressing"
PFX = "DR_"

if HERE not in sys.path:
    sys.path.insert(0, HERE)

with open(SPEC_JSON) as fh:
    SPEC = json.load(fh)

DATUM = SPEC["datum"]["circuit_design_frame"]
ROT_DEG = float(DATUM["rotation_deg_about_z"])
PIVOT_D = np.array(DATUM["pivot_design"], dtype=np.float64)
PIVOT_W = np.array(DATUM["pivot_world"], dtype=np.float64)
LAP = float(SPEC["headline"]["length_m"])

# THE CONTRACT.  Imported, never reimplemented, never "matched".
import world_contract as C              # noqa: E402
CONTRACT_MIN = (1, 0, 0)
if tuple(int(v) for v in C.__version__.split(".")) < CONTRACT_MIN:
    raise RuntimeError("world_contract %s < %s" % (C.__version__, CONTRACT_MIN))

# The light is build_sky's, republished by the contract.  Round 1's dressing
# read `SPEC["sun"]` and was calibrated against a sun that does not exist;
# build_terrain.md §2.1 made the same mistake (WORLD_CONTRACT.md §8).
SUN_DIR = np.array(C.SUN_DIR, dtype=np.float64)

# THE SHARED KIT.  Imported for its BY-NAME node API and its relief law, not
# copied.  `NG` below is this module's own private DSL and it carried its own
# private copy of R2-038: `bump()` pinned ShaderNodeBump by index and Blender
# 5.2 inserted `Filter Width` at index 2, so the height went into the filter
# and Height stayed on its constant 1.0 — a constant has zero gradient, so
# every relief stage in this file contributed NOTHING.  `NG.bump` now routes
# through `itemkit.NT.bump`, which wires by name and takes `modulation_pp=` /
# `wavelength_m=`.  See §4 and R2-038 / R2-057 in docs/DEFECT-LOG-R2.md.
import itemkit as K                      # noqa: E402

# The barrier module owns the barrier LINE — and only the line.  It publishes a
# deliberate, documented divergence from the contract (`build_barriers` §4b): the
# circuit crosses its own corridor near T3/T5, so it clamps `barrier_offset` to
# the ground its own station actually owns.  Its note says in capitals that any
# module needing the barrier line through that stretch must read
# `build_barriers.barrier_offset` rather than the contract's.  This module does,
# and guards it (§2).  Everything else — the datum, the widths, the verge — comes
# straight from the contract, so a missing build_barriers is a degraded barrier
# line, never a wrong ground height.
BR = None
try:
    import build_barriers as BR          # noqa: N816
except Exception as exc:                 # pragma: no cover - fallback path
    print("[DR] WARNING: build_barriers not importable (%s); falling back to "
          "world_contract.barrier_offset, which does not carry the T3/T5 "
          "corridor self-intersection clamp." % exc)

# --------------------------------------------------------------------------- #
#  1.  deterministic hashing + noise                                            #
# --------------------------------------------------------------------------- #


def hash01(*keys):
    """Deterministic float in [0,1) from any tuple of numbers/strings."""
    h = np.uint64(0xCBF29CE484222325)
    for k in keys:
        if isinstance(k, str):
            for ch in k:
                h = np.uint64((int(h) ^ ord(ch)) * 0x100000001B3 & 0xFFFFFFFFFFFFFFFF)
            continue
        v = np.uint64(int(round(float(k) * 1024.0)) & 0xFFFFFFFFFFFFFFFF)
        h = np.uint64((int(h) ^ int(v)) * 0x100000001B3 & 0xFFFFFFFFFFFFFFFF)
        h = np.uint64(int(h) ^ (int(h) >> np.uint64(29)))
    x = int(h) & 0xFFFFFFFF
    return x / 4294967296.0


def rnd(lo, hi, *keys):
    return lo + (hi - lo) * hash01(*keys)


def rint(lo, hi, *keys):
    """inclusive integer draw"""
    return int(lo + math.floor(hash01(*keys) * (hi - lo + 1 - 1e-9)))


def pick(seq, *keys):
    return seq[int(hash01(*keys) * len(seq)) % len(seq)]


def chance(p, *keys):
    return hash01(*keys) < p


def _smooth(t):
    return t * t * (3.0 - 2.0 * t)


def vnoise1(x, seed=0):
    x = np.asarray(x, dtype=np.float64)
    i = np.floor(x)
    f = x - i
    def rr(k):
        k = np.mod(k, 65536.0)
        return np.abs(np.sin((k * 127.1 + seed * 311.7) * 43758.5453) % 1.0)
    return rr(i) + (rr(i + 1.0) - rr(i)) * _smooth(f)


def fbm1(x, seed=0, oct=4, gain=0.5, lac=2.03):
    x = np.asarray(x, dtype=np.float64)
    tot = np.zeros_like(x)
    a, fq = 1.0, 1.0
    nrm = 0.0
    for o in range(oct):
        tot = tot + a * (vnoise1(x * fq, seed + o * 17) - 0.5) * 2.0
        nrm += a
        a *= gain
        fq *= lac
    return tot / max(nrm, 1e-9)


def clamp01(a):
    return np.clip(a, 0.0, 1.0)


def smoothstep(e0, e1, x):
    return clamp01((np.asarray(x, float) - e0) / max(e1 - e0, 1e-9)) ** 2 * \
        (3.0 - 2.0 * clamp01((np.asarray(x, float) - e0) / max(e1 - e0, 1e-9)))


def srgb(hexstr):
    """'#rrggbb' -> linear RGB tuple."""
    h = hexstr.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    return tuple((v / 12.92) if v <= 0.04045 else (((v + 0.055) / 1.055) ** 2.4)
                 for v in c)


def tint(col, k, *keys):
    """jitter a linear colour by +-k (multiplicative, per channel)"""
    return tuple(max(0.0, c * (1.0 + k * (hash01(*keys, i) * 2.0 - 1.0)))
                 for i, c in enumerate(col[:3]))


# --------------------------------------------------------------------------- #
#  2.  the circuit — centreline, corridor, ground                               #
# --------------------------------------------------------------------------- #

# ---------------------------------------------------------------------------
# THE DATUM.  There is exactly one, it lives in `world_contract`, and `side` is
# not optional.
#
# What was here before: `ground_z(s, lat)` with an UNSIGNED lateral, delegating
# to the old `build_barriers.ground_z`, which was `elevation_c(s) - 0.016 *
# max(0, lat - verge_edge)`.  It carried no crown, no banking and no undulation,
# and — because it could not see which side of the road it was on — it could not
# have carried banking even in principle.  Measured against the contract with
# build_barriers already migrated, that still buried 77 of this module's 260
# objects more than 150 mm, worst 1.689 m (DR_Billboard_09).  Against the
# unmigrated world the review measured 89 of 150 buried, worst 7.38 m.
#
# `side` is therefore a REQUIRED argument of `ground_z` here.  Leaving it out is
# a TypeError at build time instead of a silent 0.69 m error at 4 K.
# ---------------------------------------------------------------------------

_HROT = math.radians(ROT_DEG)


class Centre:
    """The contract's centreline, wearing this module's old interface.

    Kept because `bridge_banner_sites` and the painted logos author in the
    circuit design frame.  Every number in it is `world_contract`'s, evaluated
    analytically — the old class re-integrated the spec's element list on its
    own 0.25 m turtle and quantised every station to 0.25 m.
    """

    def at(self, s):
        """design x, y, heading, curvature, CENTRELINE z at station(s)."""
        S = np.asarray(s, dtype=np.float64) % LAP
        X, Y, H, K = C.centreline_arrays(S)
        dx, dy = C.world_to_circuit(X, Y)
        return dx, dy, H - _HROT, K, C.elevation_c(S)

    def to_world(self, x, y, z=None):
        wx, wy = C.circuit_to_world(np.asarray(x, float), np.asarray(y, float))
        return (wx, wy) if z is None else (wx, wy, np.asarray(z))

    def to_design(self, wx, wy):
        return C.world_to_circuit(np.asarray(wx, float), np.asarray(wy, float))


CL = Centre()


def cl_at(s):
    """(x, y, heading, curvature, z) in the DESIGN frame at station s"""
    return CL.at(s)


def world_head(s):
    """heading of travel in WORLD radians at station s"""
    return C.centreline_arrays(np.asarray(s, float) % LAP)[2]


def tangent_world(s):
    h = world_head(s)
    return np.cos(h), np.sin(h)


def normal_world(s, side):
    """unit world lateral, pointing AWAY from the track on `side`"""
    h = world_head(s)
    return side * -np.sin(h), side * np.cos(h)


def station_world(s, lat, side):
    """world (x, y, GROUND z) `lat` metres to `side` of the centreline.

    The third element used to be the centreline elevation and every call site
    threw it away.  It is now `ground_z`, so throwing it away is merely wasteful
    rather than wrong.
    """
    P = C.su_to_world(np.asarray(s, float), np.abs(np.asarray(lat, float)), side)
    P = np.atleast_2d(P)
    return P[..., 0], P[..., 1], P[..., 2]


# ---- widths: the contract's, all of them ----------------------------------

half_width = C.half_width          # spec §9, transition OUTSIDE the section
verge_edge = C.verge_edge          # half_width + 1.50 kerb + 1.00 painted verge


def barrier_type(s, side):
    """0 armco, 1 tecpro, 2 concrete, 3 none"""
    return C.COR.sample("btype", s, side)


def has_fence(s, side):
    return bool(C.COR.sample("fence", s, side))


def runoff_widths(s, side):
    """{asphalt, gravel, grass, apex}, measured OUTBOARD from verge_edge(s)."""
    return C.runoff_widths(s, side)


def zone_cap(s, side):
    """height cap from the spec's declared empty zones (99 = unconstrained)"""
    return float(C.COR.sample("zone_cap", s, side))


# ---- the barrier line, and the ground this module is allowed to stand on ----
#
# BARRIER_SANITY_M exists because `build_barriers.barrier_offset` is not always
# outside the road.  Measured over the whole lap at 1 m, with build_barriers at
# its current revision:
#
#     side +1   58 m of lap (1.6 %) with the barrier face inside verge_edge + 1
#               s  905..938   face -18.80 .. +10.56 against a verge edge of 9.85
#               s 1037..1060  face  +5.37 .. +10.76 against a verge edge of 9.81
#     side -1   none, min +19.00
#
# That is the T4 hairpin, where §4b's deficit smoothing over-corrects; a face at
# -18.80 is 18.8 m on the far side of the CENTRELINE.  It is build_barriers'
# number to fix.  What this module must not do is hang advertising boards off it
# and lay some of them across the racing surface, so the line is clamped to the
# outside of the painted verge and `dressing_gate()` prints how hard it bit.
#
# The clamp is 0.30 m and not a comfortable 2 m ON PURPOSE.  Where the barrier IS
# the pit wall it stands at circuit y = 11.5 against a verge edge at 10.5, and a
# 2 m standoff would have pushed every board mounted on that wall 1.2 m into the
# pit lane — trading a visible defect for an invisible one.

BARRIER_SANITY_M = 0.30        # the barrier face is never inside the verge edge
DRESS_INSET = 0.60             # nothing stands closer than this to the corridor
                               # rim: past it the ground is build_terrain's height
                               # field, welded to `corridor_rim` and battered
                               # outward over 34 m, and no contract predicts it
BARRIER_CLEAR_M = 0.60         # free-standing furniture stands at least this far
                               # BEHIND the barrier face, so nothing shares a
                               # footprint with an Armco post or a TecPro block

_CLAMP_LOG = dict(inboard_m=0.0, inboard_n=0, outboard_m=0.0, outboard_n=0,
                  pushed_out_m=0.0, pushed_out_n=0, calls=0, no_room=0,
                  untrusted=0)


def _bo_raw(s, side):
    if BR is not None:
        return np.asarray(BR.barrier_offset(np.asarray(s, float), side), float)
    return np.asarray(C.barrier_offset(np.asarray(s, float), side), float)


def barrier_offset(s, side):
    """distance from the centreline to the barrier FACE (metres), guarded."""
    b = _bo_raw(s, side)
    lo = np.asarray(verge_edge(s), float) + BARRIER_SANITY_M
    out = np.maximum(b, lo)
    d = float(np.max(out - b)) if np.size(out) else 0.0
    if d > 1e-6:
        _CLAMP_LOG["inboard_m"] = max(_CLAMP_LOG["inboard_m"], d)
        _CLAMP_LOG["inboard_n"] += int(np.count_nonzero(out - b > 1e-6))
    return out


def barrier_ok(s, side):
    """Is build_barriers' own barrier line usable at this station?

    False over the 95 m of lap where `BR.barrier_offset` comes out INSIDE the
    painted verge — s 905..938 and 1037..1060 on the left, where §4b's deficit
    smoothing over-corrects and the declared face reaches -18.80 m, which is
    18.8 m on the far side of the CENTRELINE.  `barrier_offset` above clamps the
    number so nothing lands on the racing surface, but the clamped value is a
    guess, not a barrier: the STEEL is still wherever build_barriers put it, and
    the BVH gate found 46 dressing objects and 54 502 triangle pairs inside it,
    every one of them at T4.  So this module builds no furniture there and says
    so in `dressing_gate()` rather than dressing a barrier that is not there.
    """
    if side not in _UNTRUSTED:
        g = np.arange(0.0, LAP, 1.0)
        bad = _bo_raw(g, side) < verge_edge(g) + BARRIER_SANITY_M
        # build_barriers smooths its deficit over +-24 samples plus a 13-sample
        # dilation, so the line is dragged for ~37 m either side of the stations
        # that actually break.  UNTRUSTED_PAD covers that bleed: without it,
        # boards at s 880-905 and posts at s 960-1040 were still following a
        # line the smoothing had pulled off the steel, for 6 664 and 6 617
        # triangle intersections respectively.
        w = np.zeros_like(bad)
        pad = int(UNTRUSTED_PAD_M)
        for sh in range(-pad, pad + 1):
            w |= np.roll(bad, sh)
        _UNTRUSTED[side] = w
    u = _UNTRUSTED[side]
    idx = (np.rint(np.asarray(s, float) % LAP).astype(np.int64)) % len(u)
    ok = not bool(np.any(u[idx]))
    if not ok:
        _CLAMP_LOG["untrusted"] += 1
    return ok


def corridor_edge(s, side):
    """Outboard limit of ground the ROAD PROGRAMME builds, in metres.

    `build_barriers.owned_edge` where available — `world_contract.platform_edge`
    narrowed to the ground this station actually owns where the circuit passes
    its own corridor; the two agree over 95.5 % of the lap.  Past this line the
    ground is build_terrain's, and nothing in this module stands on it.
    """
    if BR is not None:
        return np.asarray(BR.owned_edge(np.asarray(s, float), side), float)
    return np.asarray(C.platform_edge(np.asarray(s, float), side), float)


def _rim(s, side, foot):
    return float(corridor_edge(s, side)) - DRESS_INSET - float(foot)


def fit_lat(s, side, want, foot=0.0):
    """Clamp a lateral into the band this module owns.  Always returns a number.

    For things MOUNTED ON the barrier, whose lateral is the barrier's own.
    """
    s = float(s)
    lo = float(verge_edge(s)) + BARRIER_SANITY_M
    hi = max(_rim(s, side, foot), lo)
    v = float(np.clip(float(want), lo, hi))
    _CLAMP_LOG["calls"] += 1
    if float(want) - v > 1e-6:
        _CLAMP_LOG["outboard_m"] = max(_CLAMP_LOG["outboard_m"], float(want) - v)
        _CLAMP_LOG["outboard_n"] += 1
    return v


_STAYS = {}


def _stay_stations(side):
    """The stations where build_barriers rakes a back stay off a fence post.

    It puts one on every 4th-7th post on an 8 m post pitch, so they are 32-56 m
    apart — 5-7 % of the lap, not a lateral band.  Reproducing the predicate
    exactly (rather than standing everything 2.4 m clear of a stay that is
    usually not there) is the difference between 3 billboards and 13: the
    blanket lateral rule ate the whole 6 m platform.
    """
    if BR is None:
        return np.zeros(0)
    nd = BR.barrier_nodes(side)
    L, S = nd["L"], nd["s"]
    total = float(L[-1])
    seed = 7200 + (side > 0)
    out = []
    for pi in range(0, int(total / BR.FENCE_SPAN) + 1):
        u = pi * BR.FENCE_SPAN
        if u > total:
            break
        sj = float(np.interp(u, L, S))
        if not bool(C.COR.sample("fence", np.array([sj]), side)[0]):
            continue
        if pi % (4 + int(3 * BR.h01(seed * 3 + pi, 19))) == 0:
            out.append(sj)
    return np.array(sorted(out))


def _stay_near(s, side, tol):
    """Is a fence back stay within `tol` metres of station `s`?"""
    if BR is None:
        return False
    if side not in _STAYS:
        _STAYS[side] = _stay_stations(side)
    a = _STAYS[side]
    if a.size == 0:
        return False
    d = np.abs(((a - float(s) + LAP * 0.5) % LAP) - LAP * 0.5)
    return bool(d.min() <= tol)


def _stay_duck(s, side, height, halfspan):
    """Outboard distance from the barrier structure a `height` object fits under.

    A stay's foot is 2.45 m outboard of the node line at grade and its head is
    3.00 m up at the post, so an object either tucks UNDER the diagonal or
    stands clear of the foot.  Only applies where a stay actually is.
    """
    if height <= 0.0 or not has_fence(s, side):
        return 1e9
    if not _stay_near(s, side, float(halfspan) + 0.45):
        return 1e9
    t = max(0.0, 1.0 - float(height) / STAY_HEAD_Z)
    return max(0.0, (STAY_FOOT_M - STRUCT_BACK_M) * t - 0.12)


def fit_behind(s, side, want, foot=0.0, clear=BARRIER_CLEAR_M, height=0.0,
               halfspan=0.0):
    """Clamp a lateral into the ground BEHIND the barrier.  None if there is none.

    Where the barrier is the pit wall the road programme builds only
    `PLATFORM_MARGIN_WALL_M` = 0.6 m of footing behind it, because the ground
    there belongs to the pit lane (WORLD_CONTRACT.md §4).  A TV mast planted in
    it stands in the pit lane — which is exactly what `tvcam@26/+1` did, 171 mm
    proud of `world_ground_z` and owned by `build_architecture:paving`.  Free-
    standing furniture therefore asks for room first and is dropped if there is
    none, rather than being clamped to somewhere it does not belong.
    """
    s = float(s)
    _CLAMP_LOG["calls"] += 1
    if not barrier_ok(s, side):
        return None
    base = float(barrier_back(s, side))
    lo = base + float(clear)
    hi = _rim(s, side, foot)
    duck = _stay_duck(s, side, height, halfspan)
    if duck < 1e8 and (lo + foot) - base > duck:
        lo = max(lo, base + (STAY_FOOT_M - STRUCT_BACK_M) + 0.35 + foot)
    if hi < lo:
        _CLAMP_LOG["no_room"] += 1
        return None
    v = float(np.clip(float(want), lo, hi))
    if float(want) - v > 1e-6:                # pulled IN, away from the rim
        _CLAMP_LOG["outboard_m"] = max(_CLAMP_LOG["outboard_m"],
                                       float(want) - v)
        _CLAMP_LOG["outboard_n"] += 1
    elif v - float(want) > 1e-6:              # pushed OUT, clear of the barrier
        _CLAMP_LOG["pushed_out_m"] = max(_CLAMP_LOG["pushed_out_m"],
                                         v - float(want))
        _CLAMP_LOG["pushed_out_n"] += 1
    return v


def room_behind(s, side, foot=0.0, clear=BARRIER_CLEAR_M, height=0.0,
                halfspan=0.0):
    """metres of usable ground behind the barrier at (s, side); <0 means none"""
    s = float(s)
    base = float(barrier_back(s, side))
    lo = base + float(clear)
    duck = _stay_duck(s, side, height, halfspan)
    if duck < 1e8 and (lo + foot) - base > duck:
        lo = max(lo, base + (STAY_FOOT_M - STRUCT_BACK_M) + 0.35 + foot)
    return _rim(s, side, foot) - lo


# ---- the barrier's REAL track-facing surface -------------------------------
#
# `barrier_offset` is the declared face.  The mesh is not on it, and cannot be:
# build_barriers lays 4 m W-beam panels as STRAIGHT CHORDS on a jittered line,
# so through a corner the steel sits inboard of the declared face by the panel
# sagitta, and the maintenance-history wander moves it again.  Measured against
# `BR.barrier_offset` over the assembled build, per 4 m station bin:
#
#     BR_Armco   inboard of the declared face: p50 -0.004 m, p05 -0.095 m
#     BR_TecPro  inboard of the declared face: p50 -1.800 m   (3 x 0.55 m rows
#                                                              + a 0.10 standoff)
#     BR_Concrete                              p50 -0.281 m   (a 0.6 m wall,
#                                                              face = its centre)
#
# Hanging a rigid board on the DECLARED face therefore drove it through the
# steel: 77 DR_ objects and 207 583 triangle pairs on the BVH gate.  This table
# reads build_barriers' own panel-node polyline — the same construction its
# rails are swept along — and returns the most inboard lateral any panel reaches
# near a station, so a board can be stood off the real steel instead of a line.

# All five constants below are MEASURED off the assembled build, per 4 m station
# bin, against `barrier_face` itself:
#
#   BR_Armco       inboard p50 +0.027  p05 -0.015 | outboard p50 +0.227
#   BR_TecPro      inboard p50 -1.744  p05 -1.774
#   BR_FenceStruct inboard p50 +0.297  p05 +0.104 | outboard p50 +0.547
#   BR_FenceMesh   inboard p50 +0.345  p05 +0.218
#   BR_Concrete    inboard p50 -0.270  p05 -0.281  (a 0.6 m wall on its centre)
#
# so a board hung at `barrier_face - 0.045` clears the beam by 30-60 mm, and a
# banner at `barrier_face + BANNER_MOUNT_M` hangs between the tension cables and
# the mesh instead of 0.27 m in front of the whole fence.

BOARD_STANDOFF_M = 0.045       # strap + bolt head depth behind the board face
TECPRO_FRONT_M = 1.85          # TP_ROWS*TP_DEP + TP_STANDOFF + impact bulge
BANNER_MOUNT_M = 0.055         # MEASURED: the fence POST flange reaches as far
                               # inboard as +0.104 at p05 and the cloth's own
                               # backward billow is 20 mm, so 55 mm is where a
                               # banner hangs without going through a post.
                               # The mesh sits 0.12-0.29 m behind it, which is
                               # what a cable-tied banner on a raked fence
                               # actually looks like from the track.
STRUCT_BACK_M = 0.45           # Armco posts, blockouts and the fence post flange
STAY_FOOT_M = 2.45             # fence back-stay foot: post base + 2.1 m outboard
STAY_HEAD_Z = 3.00             # ... rising to 0.62 * (6.0 - 1.2) at the post
UNTRUSTED_PAD_M = 42.0         # build_barriers' deficit smoothing bleed
_FACE = {}
_UNTRUSTED = {}


def _build_face(side):
    """(inboard, outboard) lateral envelope of build_barriers' node polyline.

    Sampled off `BR.barrier_nodes` — the same 4 m panel chords its rails are
    swept along — so it carries the maintenance-history wander AND the chord
    sagitta through a corner, which is where a rigid board goes through steel.
    """
    if BR is None:
        return None, None
    nd = BR.barrier_nodes(side)
    P = np.asarray(nd["P"], float)
    t = np.linspace(0.0, 1.0, 5)[:, None]
    A, B = P[:-1, :2], P[1:, :2]
    Q = (A[None, :, :] * (1.0 - t)[:, :, None] +
         B[None, :, :] * t[:, :, None]).reshape(-1, 2)
    wx, wy = CL.to_world(Q[:, 0], Q[:, 1])
    ss, uu = C.project(wx, wy)
    au = np.abs(uu)
    n = int(LAP) + 1
    idx = np.clip(np.rint(ss).astype(int), 0, n - 1)
    lo = np.full(n, np.inf)
    hi = np.full(n, -np.inf)
    np.minimum.at(lo, idx, au)
    np.maximum.at(hi, idx, au)
    dec = np.asarray(barrier_offset(np.arange(n, dtype=float), side), float)
    lo = np.where(np.isfinite(lo), lo, dec)
    hi = np.where(np.isfinite(hi), hi, dec)
    rl, rh = lo.copy(), hi.copy()
    for sh in range(1, 4):              # +-3 m: a 4.6 m board spans two panels
        rl = np.minimum(rl, np.roll(lo, sh))
        rl = np.minimum(rl, np.roll(lo, -sh))
        rh = np.maximum(rh, np.roll(hi, sh))
        rh = np.maximum(rh, np.roll(hi, -sh))
    return rl, rh


def _face_tab(side, which):
    if side not in _FACE:
        _FACE[side] = _build_face(side)
    return _FACE[side][which]


def barrier_face(s, side):
    """The most inboard lateral build_barriers' steel reaches near station `s`."""
    if BR is None:
        return np.asarray(barrier_offset(s, side), float)
    f = _face_tab(side, 0)
    return np.interp(np.asarray(s, float) % LAP,
                     np.arange(len(f), dtype=float), f, period=LAP)


def barrier_back(s, side):
    """The most OUTBOARD lateral the barrier structure reaches near `s`."""
    if BR is None:
        return np.asarray(barrier_offset(s, side), float) + STRUCT_BACK_M
    f = _face_tab(side, 1)
    return np.interp(np.asarray(s, float) % LAP,
                     np.arange(len(f), dtype=float), f,
                     period=LAP) + STRUCT_BACK_M


def mount_lat(s, side):
    """Where a board bolted to this barrier's face actually goes.

    TecPro is 1.75 m of energy absorber in front of the node line, so a board
    strapped to the "face" is 1.75 m inside three rows of foam.  Boards are not
    mounted on TecPro at all (`ad_board_plan` sends those runs to the fence);
    this is the belt-and-braces number in case one gets here anyway.
    """
    if not barrier_ok(s, side):
        return None
    f = float(barrier_face(s, side))
    if int(barrier_type(s, side)) == 1:
        f -= TECPRO_FRONT_M
    return f - BOARD_STANDOFF_M


def ground_z(s, lat, side):
    """THE ground datum at (station, lateral, side).  `world_contract.ground_z`.

    `side` is MANDATORY: +1 = left of travel, -1 = right.  `lat` may be signed
    or unsigned; its absolute value is taken and `side` decides.  Carries crown,
    banking, undulation, the negative kerbs, the verge drain and the -1.6 %
    runoff fall measured FROM THE BANKED ROAD EDGE.
    """
    return C.ground_z(np.asarray(s, float), np.abs(np.asarray(lat, float)), side)


# ---- ANCHORS: the only way anything in this file touches the ground ---------
#
# Every ground-standing unit registers the point it stands on.  `verify_dressing.py`
# reads ANCHORS, asks `world_contract.world_ground_z` for the same point, and
# then raycasts the ASSEMBLED build_surface + build_barriers meshes at it.  That
# is the check the assembly review says was missing: not "does my module agree
# with itself" but "is my object on my neighbour's triangle".

ANCHORS = []
BASE_EMBED = C.BASE_EMBED_M        # 0.020 — see WORLD_CONTRACT.md §4


def anchor(name, s, lat, side, embed=0.0, foot=0.0, behind=False,
           clear=BARRIER_CLEAR_M, height=0.0, halfspan=0.0, register=True):
    """-> (wx, wy, wz, lat) for a unit standing at (station, lateral, side).

    The lateral is fitted into the corridor first, so the returned `lat` is the
    one actually used and callers must build against it rather than their wish.
    `embed` sinks the unit into the datum (contract §4: nothing standing on the
    ground may be able to open a lit gap under itself at a 12.5 deg sun).
    `behind=True` means free-standing furniture, which needs real ground behind
    the barrier and returns (None, None, None, None) when there is none.
    """
    if behind:
        la = fit_behind(s, side, lat, foot=foot, clear=clear, height=height,
                        halfspan=halfspan)
        if la is None:
            return None, None, None, None
    else:
        la = fit_lat(s, side, lat, foot=foot)
    wx, wy, wz = station_world(s, la, side)
    wx, wy, wz = float(wx), float(wy), float(wz)
    wz -= float(embed)
    if register:
        ANCHORS.append(dict(n=name, p=(wx, wy, wz), s=float(s), u=la * side,
                            side=int(side)))
    return wx, wy, wz, la


def dressing_gate():
    """What the guards caught this build.  Printed by build()."""
    return dict(placement_queries=_CLAMP_LOG["calls"],
                dropped_no_ground_behind_barrier=_CLAMP_LOG["no_room"],
                dropped_barrier_line_untrusted=_CLAMP_LOG["untrusted"],
                barrier_line_pulled_out_of_road_n=_CLAMP_LOG["inboard_n"],
                barrier_line_pulled_out_of_road_max_m=round(
                    _CLAMP_LOG["inboard_m"], 3),
                placements_pulled_inside_rim_n=_CLAMP_LOG["outboard_n"],
                placements_pulled_inside_rim_max_m=round(
                    _CLAMP_LOG["outboard_m"], 3),
                placements_pushed_clear_of_barrier_n=_CLAMP_LOG["pushed_out_n"],
                placements_pushed_clear_of_barrier_max_m=round(
                    _CLAMP_LOG["pushed_out_m"], 3))


GATE_STATIONS = list(BR.GATE_STATIONS) if BR is not None else \
    [305.0, 742.0, 968.0, 1032.0, 1288.0, 1590.0, 1782.0, 1930.0,
     2196.0, 2372.0, 2560.0, 2726.0, 2905.0, 3092.0, 3300.0, 3612.0]

# The W-beam top, read from the module that meshes it rather than copied.  Every
# board mounted "on the barrier" in this file sits at ground_z + ARMCO_TOP, so a
# change to the rail heights has to move the boards with it.
ARMCO_TOP = float(BR.ARMCO_TOP) if BR is not None else 1.012

# ---- corners, as placement anchors ----------------------------------------

CORNERS = []
for c in SPEC["corners"]:
    if not c.get("is_numbered_corner"):
        continue
    arc = float(c["arc_m"])
    CORNERS.append(dict(
        i=int(c["index"]), name=c["name"], kind=c["type"],
        s_apex=float(c["s_apex"]), arc=arc,
        s_in=float(c["s_apex"]) - arc * 0.5, s_out=float(c["s_apex"]) + arc * 0.5,
        left=(c["direction"] == "left"),
        outside=(-1 if c["direction"] == "left" else +1),
        inside=(+1 if c["direction"] == "left" else -1),
        apex_kph=float(c["apex_kph"]), brake_kph=float(c["entry_kph"]),
        R=float(c["radius_m"])))
CORNERS.sort(key=lambda c: c["s_apex"])

# Braking zones taken from the corner table's published braking events, plus the
# two lighter ones the layout still signs.  (from, to, distance) in the spec §4.
BRAKE_ZONES = [
    # corner index, board distances (m before turn-in), how hard (drives design)
    (1,  [300, 250, 200, 150, 100, 50], "heavy"),
    (4,  [200, 150, 100, 50], "heavy"),
    (10, [150, 100, 50], "brush"),
    (12, [250, 200, 150, 100, 50], "heavy"),
    (15, [150, 100, 50], "medium"),
    (5,  [150, 100, 50], "medium"),
]

# ---- camera-path proximity: the LOD driver --------------------------------
# The camera is on/near the racing line for the whole lap, so "distance to the
# camera path" is essentially "distance to the track", plus the named stations
# where the beat sheet parks the camera very close to trackside furniture.

HERO = [
    # (name, s0, s1, side (0=both), tier)
    ("sf_line",   0.0,  140.0, 0, 2),
    ("t1_brake", 150.0, 430.0, 0, 2),
    ("t1",       430.0, 560.0, 0, 1),
    ("t3",       700.0, 800.0, 0, 1),
    ("hairpin",  870.0, 1120.0, 0, 3),
    ("rampe",   1120.0, 1320.0, 0, 1),
    ("summit",  1650.0, 1930.0, 0, 2),
    ("sweeper", 2050.0, 2360.0, 0, 1),
    ("bridge",  2360.0, 2470.0, 0, 2),
    ("doppler", 2470.0, 2660.0, -1, 3),
    ("plunge",  2650.0, 2820.0, 0, 2),
    ("gate",    3050.0, 3200.0, 0, 1),
    ("gantry",  3540.0, 3675.0, 0, 2),
]


def hero_tier(s, side=0):
    """0 = background, 1 = seen at speed, 2 = seen close, 3 = inspected at 4 m"""
    s = float(s) % LAP
    t = 0
    for (_nm, a, b, sd, tier) in HERO:
        if sd != 0 and sd != side:
            continue
        if a <= b:
            inside = a <= s <= b
        else:
            inside = s >= a or s <= b
        if inside:
            t = max(t, tier)
    return t


# --------------------------------------------------------------------------- #
#  3.  mesh accumulator                                                         #
# --------------------------------------------------------------------------- #

class MB:
    """Numpy mesh accumulator -> one recentred Blender object.

    Channels:
      uv    : (u, v)          board layout space / generic surface parameter
      base  : RGBA            the object's own colour (print, paint, plastic)
      aux   : (age, dirt, k, uid)   weathering + a per-unit decorrelation hash
    """

    __slots__ = ("name", "_V", "_F", "_K", "_UV", "_B", "_A", "_M", "_S", "_n")

    def __init__(self, name):
        self.name = name
        self._V, self._F, self._K = [], [], []
        self._UV, self._B, self._A = [], [], []
        self._M, self._S = [], []
        self._n = 0

    @property
    def nverts(self):
        return self._n

    def add(self, verts, faces, mat=0, uv=None, base=(1, 1, 1, 1),
            aux=(0.3, 0.2, 0.5, 0.5), smooth=False):
        verts = np.asarray(verts, dtype=np.float64).reshape(-1, 3)
        faces = np.asarray(faces, dtype=np.int64)
        if faces.size == 0 or len(verts) == 0:
            return
        n, m = len(verts), faces.shape[0]
        k = faces.shape[1]
        self._V.append(verts)
        self._F.append(faces + self._n)
        self._K.append(k)
        self._UV.append(np.zeros((n, 2)) if uv is None
                        else np.asarray(uv, float).reshape(n, 2))
        b = np.asarray(base, float)
        self._B.append(np.tile(b if b.size == 4 else np.append(b, 1.0), (n, 1))
                       if b.ndim == 1 else b.reshape(n, 4))
        a = np.asarray(aux, float)
        self._A.append(np.tile(a, (n, 1)) if a.ndim == 1 else a.reshape(n, 4))
        self._M.append(np.full(m, int(mat), dtype=np.int32))
        self._S.append(np.full(m, bool(smooth), dtype=bool))
        self._n += n

    def grid(self, P, **kw):
        """P (ni,nj,3) -> quads.  uv/base/aux may be (ni,nj,c) or flat."""
        P = np.asarray(P, dtype=np.float64)
        ni, nj = P.shape[0], P.shape[1]
        i = (np.arange(ni - 1)[:, None] * nj + np.arange(nj - 1)[None, :])
        q = np.stack([i, i + nj, i + nj + 1, i + 1], axis=-1).reshape(-1, 4)
        kk = {}
        for key in ("uv", "base", "aux"):
            v = kw.get(key)
            if v is not None:
                v = np.asarray(v, float)
                kk[key] = v.reshape(ni * nj, -1) if v.ndim == 3 else v
        for key in ("mat", "smooth"):
            if key in kw:
                kk[key] = kw[key]
        self.add(P.reshape(-1, 3), q, **kk)

    # -- primitives (all in a local frame; caller transforms) ---------------

    def box(self, p0, p1, mat=0, base=(1, 1, 1, 1), aux=None, skip="",
            uvscale=1.0):
        x0, y0, z0 = p0
        x1, y1, z1 = p1
        x0, x1 = min(x0, x1), max(x0, x1)
        y0, y1 = min(y0, y1), max(y0, y1)
        z0, z1 = min(z0, z1), max(z0, z1)
        V = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
             (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        F = {"b": (0, 3, 2, 1), "t": (4, 5, 6, 7), "-y": (0, 1, 5, 4),
             "+y": (2, 3, 7, 6), "-x": (3, 0, 4, 7), "+x": (1, 2, 6, 5)}
        faces = [f for k, f in F.items() if k not in skip]
        uv = np.array([(v[0] * uvscale, v[2] * uvscale) for v in V])
        self.add(V, np.array(faces), mat, uv=uv, base=base,
                 aux=aux if aux is not None else (0.3, 0.2, 0.5, 0.5))

    def cyl(self, p0, p1, r0, mat=0, base=(1, 1, 1, 1), aux=None, n=12,
            r1=None, caps=True, smooth=True, phase=0.0):
        p0 = np.asarray(p0, float); p1 = np.asarray(p1, float)
        r1 = r0 if r1 is None else r1
        d = p1 - p0
        L = np.linalg.norm(d)
        if L < 1e-9:
            return
        w = d / L
        up = np.array([0.0, 0.0, 1.0]) if abs(w[2]) < 0.95 else np.array([1.0, 0.0, 0.0])
        u = np.cross(w, up); u /= np.linalg.norm(u)
        v = np.cross(w, u)
        th = np.linspace(0, 2 * math.pi, n, endpoint=False) + phase
        c, s = np.cos(th), np.sin(th)
        A = p0[None, :] + r0 * (c[:, None] * u[None, :] + s[:, None] * v[None, :])
        B = p1[None, :] + r1 * (c[:, None] * u[None, :] + s[:, None] * v[None, :])
        V = np.concatenate([A, B], axis=0)
        i = np.arange(n)
        j = (i + 1) % n
        F = np.stack([i, j, j + n, i + n], axis=-1)
        uv = np.concatenate([np.stack([th / (2 * math.pi), np.zeros(n)], -1),
                             np.stack([th / (2 * math.pi), np.full(n, L)], -1)])
        self.add(V, F, mat, uv=uv, base=base,
                 aux=aux if aux is not None else (0.3, 0.2, 0.5, 0.5),
                 smooth=smooth)
        if caps:
            for (ctr, rr, rev) in ((p0, r0, True), (p1, r1, False)):
                ring = ctr[None, :] + rr * (c[:, None] * u[None, :] +
                                            s[:, None] * v[None, :])
                V2 = np.concatenate([ctr[None, :], ring], axis=0)
                idx = np.arange(1, n + 1)
                nxt = np.roll(idx, -1)
                F2 = np.stack([np.zeros(n, int), nxt, idx], -1) if rev else \
                    np.stack([np.zeros(n, int), idx, nxt], -1)
                self.add(V2, F2, mat, base=base,
                         aux=aux if aux is not None else (0.3, 0.2, 0.5, 0.5))

    def tube(self, pts, r, mat=0, base=(1, 1, 1, 1), aux=None, n=8, caps=True,
             taper=None):
        """swept tube through a polyline"""
        P = np.asarray(pts, float)
        if len(P) < 2:
            return
        T = np.gradient(P, axis=0)
        T /= np.maximum(np.linalg.norm(T, axis=1)[:, None], 1e-9)
        up = np.array([0.0, 0.0, 1.0])
        U = np.cross(T, up)
        bad = np.linalg.norm(U, axis=1) < 1e-6
        U[bad] = np.cross(T[bad], np.array([1.0, 0.0, 0.0]))
        U /= np.maximum(np.linalg.norm(U, axis=1)[:, None], 1e-9)
        V = np.cross(T, U)
        th = np.linspace(0, 2 * math.pi, n, endpoint=False)
        rr = np.full(len(P), r, float) if taper is None else np.asarray(taper, float)
        pts3 = (P[:, None, :] + rr[:, None, None] *
                (np.cos(th)[None, :, None] * U[:, None, :] +
                 np.sin(th)[None, :, None] * V[:, None, :]))
        ni, nj = pts3.shape[0], pts3.shape[1]
        i = (np.arange(ni - 1)[:, None] * nj + np.arange(nj)[None, :])
        j = (np.arange(ni - 1)[:, None] * nj + (np.arange(nj)[None, :] + 1) % nj)
        F = np.stack([i, j, j + nj, i + nj], axis=-1).reshape(-1, 4)
        uv = np.stack([np.tile(th / (2 * math.pi), ni),
                       np.repeat(np.arange(ni, dtype=float), nj)], -1)
        self.add(pts3.reshape(-1, 3), F, mat, uv=uv, base=base,
                 aux=aux if aux is not None else (0.3, 0.2, 0.5, 0.5), smooth=True)
        if caps:
            for k, rev in ((0, True), (ni - 1, False)):
                ring = pts3[k]
                V2 = np.concatenate([P[k][None, :], ring], axis=0)
                idx = np.arange(1, nj + 1)
                nxt = np.roll(idx, -1)
                F2 = np.stack([np.zeros(nj, int), nxt, idx], -1) if rev else \
                    np.stack([np.zeros(nj, int), idx, nxt], -1)
                self.add(V2, F2, mat, base=base,
                         aux=aux if aux is not None else (0.3, 0.2, 0.5, 0.5))

    def prism(self, pts2, z0, z1, mat=0, base=(1, 1, 1, 1), aux=None,
              top=True, bot=True, smooth=False):
        """extrude a 2-D polygon (list of (x,y)) between two z"""
        P = np.asarray(pts2, float)
        n = len(P)
        V = np.concatenate([np.column_stack([P, np.full(n, z0)]),
                            np.column_stack([P, np.full(n, z1)])])
        i = np.arange(n)
        j = (i + 1) % n
        F = [np.stack([i, j, j + n, i + n], -1)]
        if bot:
            F.append(np.stack([np.zeros(n - 2, int), np.arange(2, n),
                               np.arange(1, n - 1)], -1))
        if top:
            F.append(np.stack([np.full(n - 2, n), np.arange(1, n - 1) + n,
                               np.arange(2, n) + n], -1))
        aux = aux if aux is not None else (0.3, 0.2, 0.5, 0.5)
        for f in F:
            self.add(V, f, mat, base=base, aux=aux, smooth=(smooth and f is F[0]))

    def poly(self, pts3, mat=0, base=(1, 1, 1, 1), aux=None, uv=None,
             two_sided=False):
        """one flat n-gon"""
        P = np.asarray(pts3, float).reshape(-1, 3)
        n = len(P)
        if n < 3:
            return
        F = np.stack([np.zeros(n - 2, int), np.arange(1, n - 1),
                      np.arange(2, n)], -1)
        aux = aux if aux is not None else (0.3, 0.2, 0.5, 0.5)
        self.add(P, F, mat, uv=uv, base=base, aux=aux)
        if two_sided:
            self.add(P, F[:, ::-1], mat, uv=uv, base=base, aux=aux)

    # -- realise -------------------------------------------------------------
    def emit(self, coll, materials, name=None):
        if not self._V or self._n == 0:
            return None
        V = np.concatenate(self._V, axis=0)
        UV = np.concatenate(self._UV, axis=0)
        B = np.concatenate(self._B, axis=0)
        A = np.concatenate(self._A, axis=0)
        M = np.concatenate(self._M, axis=0)
        S = np.concatenate(self._S, axis=0)
        loops = np.concatenate([f.ravel() for f in self._F])
        ltot = np.concatenate([np.full(f.shape[0], k, dtype=np.int32)
                               for f, k in zip(self._F, self._K)])
        lstart = np.zeros(len(ltot), dtype=np.int32)
        np.cumsum(ltot[:-1], out=lstart[1:])
        # Recentre.  World |P| ~ 1000 m destroys float32 precision inside any
        # position-driven procedural; every material here reads TexCoord>Object.
        ctr = 0.5 * (V.min(axis=0) + V.max(axis=0))
        V = V - ctr
        nm = name or self.name
        me = bpy.data.meshes.new(nm)
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
        for cname, arr in (("base", B), ("aux", A)):
            ca = me.color_attributes.new(name=cname, type='FLOAT_COLOR',
                                         domain='POINT')
            ca.data.foreach_set("color", arr.ravel())
        me.validate(verbose=False)
        for mat in materials:
            me.materials.append(mat)
        ob = bpy.data.objects.new(nm, me)
        ob.location = tuple(float(c) for c in ctr)
        coll.objects.link(ob)
        return ob


# ---- local frames ---------------------------------------------------------

def frame_from_facing(pos, facing_xy):
    """Right-handed basis with ey = facing (horizontal), ez = up, ex = ey x ez.
    Returns a 3x3 numpy matrix whose COLUMNS are ex, ey, ez."""
    ey = np.array([facing_xy[0], facing_xy[1], 0.0], float)
    n = np.linalg.norm(ey)
    ey = ey / n if n > 1e-9 else np.array([1.0, 0.0, 0.0])
    ez = np.array([0.0, 0.0, 1.0])
    ex = np.cross(ey, ez)
    return np.column_stack([ex, ey, ez]), np.asarray(pos, float)


class Local(MB):
    """An MB view that transforms every primitive from a local frame into the
    parent's frame.  Nestable: Local(Local(mb, ...), ...) composes."""

    __slots__ = ("R", "O", "parent")

    def __init__(self, parent, R, O):
        MB.__init__(self, parent.name)
        self.parent = parent
        self.R = np.asarray(R, float)
        self.O = np.asarray(O, float)

    @property
    def nverts(self):
        return self.parent.nverts

    def add(self, verts, faces, *a, **kw):
        V = np.asarray(verts, float).reshape(-1, 3)
        if V.size == 0:
            return
        self.parent.add(V @ self.R.T + self.O[None, :], faces, *a, **kw)

    def emit(self, *a, **kw):
        raise RuntimeError("emit the parent MB, not the Local view")


def yaw(deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]])


def pitchX(deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return np.array([[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]])


def rollY(deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]])


# --------------------------------------------------------------------------- #
#  4.  materials — 12 vertex-colour-driven node graphs                          #
# --------------------------------------------------------------------------- #

M_PRINT, M_FABRIC, M_STEEL, M_ALU, M_RUBBER, M_PLASTIC = 0, 1, 2, 3, 4, 5
M_CONC, M_WOOD, M_EMIT, M_GLASS, M_PAINT, M_TARP = 6, 7, 8, 9, 10, 11
MAT_ORDER = ["Print", "Fabric", "Steel", "Alu", "Rubber", "Plastic",
             "Concrete", "Wood", "Emit", "Glass", "Paint", "Tarp"]
MATS = {}

# --------------------------------------------------------------------------- #
#  4a.  WHAT A `Scale` ACTUALLY EMITS — including the one itemkit gets wrong.   #
# --------------------------------------------------------------------------- #
#
# `itemkit` publishes NOISE_WAVELENGTH_FACTOR = 1.60 and VORONOI_ = 2.17 and
# says in capitals that they are SINGLE-SOURCED and still owe an independent
# confirmation.  Four of the nine relief stages in this module are driven by
# ShaderNodeTexWave, for which itemkit publishes no factor at all — its
# `_tex_wavelength_m()` returns `1.0 / Scale`.
#
# MEASURED HERE, because two stages' wavelengths depend on it (work/dr_relief/
# wave_factor.py, output work/dr_relief/wave_factor.txt).  An 8192 px
# orthographic emission render of each node alone on a 2.000 m plane, one pixel
# row, zero-crossing count AND rfft peak, swept over Scale so that a factor that
# is really a factor has to stay constant:
#
#     Scale        10       20       40       80
#     Wave       0.3125   0.3150   0.3137   0.3143      <- constant. 0.3139 avg
#     Noise      1.667    1.702    1.650                <- 1.60 confirmed, ~5 %
#     Voronoi    1.905    2.222    2.051                <- 2.17 confirmed, ~7 %
#
# So ShaderNodeTexWave emits 2*pi/20 = 0.31416 / Scale, NOT 1.0 / Scale, and
# itemkit's own header already knows this: it used Blender's closed-form Wave
# as the CONTROL for the noise/voronoi measurement and quotes 0.3136 against
# "2*pi/20 = 0.31416".  The constant is right in the comment and wrong in the
# code, and `_tex_wavelength_m` is what `bump_relief_report` audits with.
# ITEMKIT IS NOT MINE TO EDIT; this is reported, not patched (see the note in
# the task report).  Two consequences land here:
#
#   * every Wave in this file emits 3.18x FINER than 1/Scale implies, which is
#     how `mat_fabric`'s weave — documented in its own docstring as a 1.15 mm
#     pitch, with a half-pitch phase offset of 0.00057 m hard-coded to that
#     same 1.15 mm — was actually emitting 0.361 mm.  At the film's distances
#     that is a tenth of a pixel: a weave that cannot reach the image.
#   * `pit_wall_unit_itemkit`'s LAM_PLY = 1.0 / 230.0 is 3.18x too long, so its
#     ply-veneer stage is that much shallower than the m = 1.5452 it declares.
#     Reported, not touched.
#
# Scales below are therefore written as `wave_scale_for(lambda)` and friends, so
# the code and the comment cannot drift apart again.
WAVE_WAVELENGTH_FACTOR = 2.0 * math.pi / 20.0        # 0.31416, measured above


def wave_scale_for(wavelength_m):
    """`Scale` that makes ShaderNodeTexWave emit bands of `wavelength_m`."""
    return WAVE_WAVELENGTH_FACTOR / float(wavelength_m)


# --------------------------------------------------------------------------- #
#  4b.  HOW FAR EACH HEIGHT SIGNAL ACTUALLY SWINGS — measured, not assumed.     #
# --------------------------------------------------------------------------- #
#
# `NT.bump(modulation_pp=...)` derives `Distance = amplitude / (strength *
# height_pp)`, so a `height_pp` that is 2x wrong ships a stage 2x too deep and
# the module's declared modulation becomes a lie that renders.  itemkit offers
# "1.0 for a full-range ramp, ~0.6 for a raw Noise" as a rule of thumb.
#
# THESE ARE MEASURED, in situ, on the built graph: work/dr_relief/height_pp.py
# re-points each material's output at an Emission driven by that bump's own
# Height source and renders it orthographically onto a plane carrying
# representative `base`/`aux` attributes (age 0.60, dirt 0.40, variant 0.50).
# Output work/dr_relief/height_pp.json.
#
# The probe carries its own control twice over.  It refuses unless all fourteen
# renders are DISTINCT — its first version returned one identical number for
# every stage because `--factory-startup` is not an empty scene and the default
# Cube was sitting between the camera and the plane.  And Wood and Tarp are
# undistorted Wave Colors, whose true swing is exactly 1.0; the probe returns
# 1.000 and 0.999 for them, so it reads a full-range signal as full range.
#
# Four of the fourteen were 1.4x to 3.4x away from what the rule of thumb would
# have given, all in stages built out of several nodes:
#
#     print squeegee   guessed 1.00  measured 0.286   distortion 2.0 leaves the
#                                                     Wave mostly dark (mean .02)
#     fabric weave     guessed 0.50  measured 0.904   MAXIMUM of two bands
#     steel spangle    guessed 0.50  measured 1.159   raw Voronoi F1 exceeds 1
#     steel rust mask  guessed 0.85  measured 0.510   ramp x age x 0.85
#
# A raw Noise measures 0.50-0.57, which CONFIRMS itemkit's 0.6 rule of thumb.
HEIGHT_PP = {
    "print_peel":     0.557,   # Noise, detail 6
    "print_squeegee": 0.286,   # Wave Color, distortion 2.0, detail 3
    "fabric_wr2":     0.506,   # Noise, detail 5
    "fabric_wr1":     0.501,   # Noise, detail 6
    "fabric_crease":  0.866,   # two ramped bands, MAXIMUM, x creaseh x age
    "fabric_weave":   0.904,   # MAXIMUM of warp and weft, + slub
    "steel_rust":     0.510,   # ramp x age x 0.85
    "steel_spangle":  1.159,   # raw Voronoi F1 distance
    "alu_grain":      0.565,   # Noise, detail 4
    "rubber_micro":   0.564,   # Noise, detail 6
    "plastic_mould":  0.553,   # Noise, detail 8
    "concrete_agg":   0.695,   # Voronoi/2 + Noise/2
    "wood_grain":     1.000,   # Wave Color, distortion 6
    "tarp_rib":       0.999,   # Wave Color, undistorted
}


class NG:
    """minimal shader-graph DSL (same shape as the barrier module's)"""

    def __init__(self, mat):
        mat.use_nodes = True
        self.mat = mat
        self.nt = mat.node_tree
        self.nt.nodes.clear()
        self._x = 0
        self._kit_ = None

    def n(self, t, defaults=None, **kw):
        nd = self.nt.nodes.new(t)
        self._x += 190
        nd.location = (self._x, (self._x // 190 % 6) * 260)
        for k, v in kw.items():
            setattr(nd, k, v)
        if defaults:
            for i, v in defaults.items():
                nd.inputs[i].default_value = v
        return nd

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

    def _feed_named(self, node, name, v):
        """`_feed`, addressing the socket BY NAME.  USE THIS FOR `Normal`.

        R2-057.  The live order of ShaderNodeBsdfPrincipled in Blender 5.2 is

            [0] Base Color [1] Metallic [2] Roughness [3] IOR [4] Alpha
            [5] THIN WALL  [6] Normal   [7] Weight ...

        and every `_feed(b, 5, <bump>)` in this module — all nine of them —
        was written when index 5 was `Normal`.  The whole relief chain of the
        dressing was therefore being wired into **Thin Wall**, and the Normal
        socket of all nine Principled BSDFs was left unconnected.

        The two defects stacked.  `bump()` below had no gradient to hand over
        (R2-038) and what it did hand over went to the wrong socket (R2-057),
        so 4.29 M triangles of trackside dressing were flat twice.  Either
        defect alone produces the same picture, which is why fixing one and
        measuring would have returned a perfect, convincing null.

        Indices 0, 1, 2 and 3 (Base Color, Metallic, Roughness, IOR) did NOT
        move and are left alone: a socket inserted after you is not a move.
        `_feed(b, 4, ...)` does not appear in this file.
        """
        if v is None:
            return
        for i, s in enumerate(node.inputs):
            if s.name == name:
                return self._feed(node, i, v)
        raise RuntimeError(
            "%s has no input named %r; it has %s"
            % (node.bl_idname, name, [s.name for s in node.inputs]))

    def _kit(self):
        """An `itemkit.NT` bound to THIS node tree.

        Not a second graph and not a copy of itemkit's code: the same object,
        pointed at the material `NG` is already building, so `NT.bump` — the
        by-name, relief-law-carrying implementation that was repaired once and
        should not be repaired again — builds our nodes.  `NT.__init__` would
        create a material and clear its tree, which is why it is bypassed;
        `NT.n`, `NT.pin`, `NT.pin_named` and `NT.bump` need only `.m`, `.t`
        and `.x`.
        """
        if self._kit_ is None:
            k = K.NT.__new__(K.NT)
            k.m = self.mat
            k.t = self.nt
            k.x = 0
            self._kit_ = k
        return self._kit_

    def lk(self, a, ao, b, bi):
        self.nt.links.new(a.outputs[ao], b.inputs[bi])

    def attr(self, name):
        return self.n("ShaderNodeAttribute", attribute_name=name)

    def sep(self, v):
        s = self.n("ShaderNodeSeparateColor")
        self._feed(s, 0, v)
        return s

    def sepxyz(self, v):
        s = self.n("ShaderNodeSeparateXYZ")
        self._feed(s, 0, v)
        return s

    def math(self, op, a=None, b=None, c=None, clamp=False):
        m = self.n("ShaderNodeMath", operation=op, use_clamp=clamp)
        self._feed(m, 0, a); self._feed(m, 1, b); self._feed(m, 2, c)
        return m

    def vmath(self, op, a=None, b=None, scale=None):
        m = self.n("ShaderNodeVectorMath", operation=op)
        self._feed(m, 0, a)
        if b is not None:
            if isinstance(b, (tuple, list)) and len(b) == 3 and \
                    not isinstance(b[0], bpy.types.Node):
                m.inputs[1].default_value = tuple(b)
            else:
                self._feed(m, 1, b)
        if scale is not None:
            self._feed(m, 3, scale)
        return m

    def mix(self, fac, a, b, blend="MIX"):
        m = self.n("ShaderNodeMixRGB", blend_type=blend)
        self._feed(m, 0, fac); self._feed(m, 1, a); self._feed(m, 2, b)
        return m

    def noise(self, vec=None, scale=5.0, detail=8.0, rough=0.55, dist=0.0):
        nd = self.n("ShaderNodeTexNoise", noise_dimensions='3D',
                    defaults={2: scale, 3: detail, 4: rough, 8: dist})
        self._feed(nd, 0, vec)
        return nd

    def voro(self, vec=None, scale=10.0, rand=1.0, feature='F1'):
        nd = self.n("ShaderNodeTexVoronoi", feature=feature,
                    voronoi_dimensions='3D', defaults={2: scale, 8: rand})
        self._feed(nd, 0, vec)
        return nd

    def wave(self, vec=None, scale=10.0, dist=0.0, detail=2.0, band='X'):
        nd = self.n("ShaderNodeTexWave", wave_type='BANDS', bands_direction=band,
                    defaults={1: scale, 2: dist, 3: detail})
        self._feed(nd, 0, vec)
        return nd

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

    def bump(self, height, strength=1.0, dist=None, normal=None,
             modulation_pp=None, wavelength_m=None, height_pp=1.0):
        """Height -> normal perturbation, THROUGH `itemkit.NT.bump`.

        WHAT THIS USED TO BE, and it is the whole of R2-038 in four lines:

            b = self.n("ShaderNodeBump", defaults={0: strength, 1: dist})
            self._feed(b, 2, height)

        Blender 5.2's ShaderNodeBump is

            [0] Strength  [1] Distance  [2] FILTER WIDTH  [3] Height  [4] Normal

        so `height` went into Filter Width and the Height socket kept its
        constant default of 1.0.  A constant has zero gradient.  Every relief
        stage in this module produced no relief whatsoever, and it was silent:
        the material built, the node count was right, and the graph looked
        correct in the editor.

        STATE THE RADIANCE MODULATION, NOT THE MILLIMETRES.  `modulation_pp`
        with `wavelength_m` derives the depth from the contract sun (itemkit
        section 5b): at this film's 12.47 deg the divisor `tan(e)` amplifies a
        given slope 4.52x over a 45 deg reference, so the same 0.5 mm is
        m = 0.57 on an 8 mm crumple and m = 0.045 on a 100 mm flute.  `dist`
        (raw metres) is still accepted so a stage can be pinned to a measured
        depth, but nothing in this file uses it any more.

        `height_pp` is the peak-to-peak swing of what is actually fed to
        Height — about 0.6 for a raw Noise, ~1.0 for a full-range ramp or a
        Wave Color — because the depth is divided by it.

        Returns the bump NODE (not itemkit's `(node, socket)` pair), so it
        drops straight into `NG._feed` / `NG._feed_named` like every other
        node in this DSL, and chains through `normal=`.
        """
        return self._kit().bump(height, strength, distance=dist, normal=normal,
                                modulation_pp=modulation_pp,
                                wavelength_m=wavelength_m,
                                height_pp=height_pp)[0]


def _new_mat(name):
    m = bpy.data.materials.new(PFX + name)
    g = NG(m)
    out = g.n("ShaderNodeOutputMaterial")
    bsdf = g.n("ShaderNodeBsdfPrincipled")
    g.lk(bsdf, 0, out, 0)
    return m, g, bsdf, out


def _set_named(b, val, *names):
    """Write `val` to the first of `names` this node has, or RAISE.  R2-072.

    This module carried the same silent-drop idiom three times --

        for nm_ in ("Specular IOR Level", "Specular"):
            if nm_ in b.inputs:
                b.inputs[nm_].default_value = 0.24
                break

    -- with no `else`.  Addressing by NAME is why R2-057's socket INSERTION
    could not reach these; a socket RENAME or REMOVAL was the case the missing
    `else` did not cover, and that one leaves NO artefact signature at all.
    `tools/socket_blend_scan.py` can see a bump that landed on `Thin Wall`,
    because the wrong link is in the blend.  A specular level that was never
    written is invisible: the socket keeps its default, and a default is a
    legal value.

    The alias list still does its job -- 5.2's Principled has `Specular IOR
    Level` and has no `Specular` -- and it is only when NONE of the candidates
    resolves that a value has been dropped.  See
    `tools/socket_setter_census.py` for the same fix and its controls on the
    three `_set` helpers this idiom was copied from.
    """
    for nm_ in names:
        if nm_ in b.inputs:
            b.inputs[nm_].default_value = val
            return nm_
    raise KeyError(
        "%s has no socket named %s -- its sockets are %s. This write was "
        "silently dropped before R2-072."
        % (b.bl_idname, " / ".join(repr(n) for n in names),
           [s.name for s in b.inputs]))


def _common(g):
    """the three inputs every material in this module reads"""
    base = g.attr("base")
    aux = g.attr("aux")
    a = g.sep(aux)                      # r = age, g = dirt/exposure, b = variant
    tc = g.n("ShaderNodeTexCoord")
    uv = g.sepxyz((tc, 2))              # UV
    obj = g.vmath('MULTIPLY', (tc, 3), (1.0, 1.0, 1.0))
    return base, aux, a, tc, uv, obj


def _bleach(g, base, age):
    """sunlight on printed vinyl: saturation dies, value lifts, hue drifts warm"""
    hsv = g.n("ShaderNodeHueSaturation")
    g._feed(hsv, 0, 0.5)
    g._feed(hsv, 1, g.math('SUBTRACT', 1.0, g.math('MULTIPLY', age, 0.62)))
    g._feed(hsv, 2, g.math('ADD', 1.0, g.math('MULTIPLY', age, 0.16)))
    g._feed(hsv, 3, 1.0)
    g._feed(hsv, 4, base)
    return hsv


def mat_print():
    m, g, b, _ = _new_mat("Print")
    base, aux, a, tc, uv, obj = _common(g)
    p3 = g.vmath('MULTIPLY', (tc, 3), (3.0, 3.0, 3.0))
    age, dirt = (a, 0), (a, 1)
    col = _bleach(g, base, age)
    # patchy extra fade: the sun does not bleach a 6 m board evenly.  It is a
    # further loss of saturation, NOT a mix toward grey — mixing toward a fixed
    # grey turned every black board khaki (defect 3 in the note).
    #
    # MEASURED FAILURE: at 1.5 m the macro render still came back a flat colour
    # fill.  The cause was scale, not absence — every term was keyed to a single
    # 1.5-scale noise, so a 4 m board saw about one and a half cycles of
    # everything and the variation was a slow gradient the eye reads as flat.
    # Real printed vinyl on a race weekend is uneven at THREE scales at once:
    # 0.6-2 m of uneven UV exposure and cleaning, 0.1-0.3 m of handling and
    # wash marks, and 5-20 mm of orange peel.  All three are here now.
    nz = g.noise(p3, scale=1.5, detail=4.0)
    nz2 = g.noise(g.vmath('MULTIPLY', (tc, 3), (11.0, 11.0, 11.0)), scale=2.0,
                  detail=6.0, rough=0.62)
    nz = g.math('ADD', g.math('MULTIPLY', nz, 0.62),
                g.math('MULTIPLY', nz2, 0.38))
    hsv2 = g.n("ShaderNodeHueSaturation")
    g._feed(hsv2, 0, 0.5)
    g._feed(hsv2, 1, g.math('SUBTRACT', 1.0,
                            g.math('MULTIPLY',
                                   g.math('MULTIPLY', age, 0.30), nz)))
    g._feed(hsv2, 2, g.math('ADD', 1.0,
                            g.math('MULTIPLY',
                                   g.math('MULTIPLY', age, 0.10), nz)))
    g._feed(hsv2, 3, 1.0)
    g._feed(hsv2, 4, col)
    col = hsv2
    # ground dirt: rises from the bottom edge (uv.y = height fraction)
    grad = g.ramp((uv, 1), [(0.0, (1, 1, 1)), (0.16, (0.45, 0.45, 0.45)),
                            (0.42, (0.0, 0.0, 0.0))])
    dnz = g.noise(g.vmath('MULTIPLY', (tc, 3), (7.0, 7.0, 7.0)), scale=2.5,
                  detail=8.0)
    dm = g.math('MULTIPLY', g.math('MULTIPLY', grad, dirt),
                g.math('ADD', 0.45, dnz), clamp=True)
    col = g.mix(dm, col, (0.075, 0.061, 0.048))
    # rubber flick from the track: hard specks, only low on the board
    spk = g.voro(g.vmath('MULTIPLY', (tc, 3), (26.0, 26.0, 26.0)), scale=1.0)
    spkm = g.math('MULTIPLY',
                  g.ramp(spk, [(0.0, (1, 1, 1)), (0.055, (1, 1, 1)),
                               (0.075, (0, 0, 0))]),
                  g.math('MULTIPLY', dirt,
                         g.ramp((uv, 1), [(0.0, (1, 1, 1)), (0.30, (0, 0, 0))])),
                  clamp=True)
    col = g.mix(spkm, col, (0.012, 0.010, 0.010))
    # RAIN STREAKS.  The single most recognisable thing about a real trackside
    # board: vertical wash marks running down from the top edge, keyed to a
    # 1-D noise across the board so no two columns are alike.
    strk = g.noise(g.vmath('MULTIPLY', (tc, 3), (3.6, 0.10, 0.10)), scale=3.0,
                   detail=7.0, rough=0.75)
    strk2 = g.noise(g.vmath('MULTIPLY', (tc, 3), (13.0, 0.16, 0.16)), scale=3.0,
                    detail=5.0, rough=0.7)
    top = g.ramp((uv, 1), [(0.20, (0, 0, 0)), (1.0, (1, 1, 1))])
    sm_ = g.math('MULTIPLY',
                 g.math('MULTIPLY',
                        g.ramp(g.math('ADD', g.math('MULTIPLY', strk, 0.62),
                                      g.math('MULTIPLY', strk2, 0.38)),
                               [(0.430, (0, 0, 0)), (0.615, (1, 1, 1))]), top),
                 g.math('ADD', 0.22, g.math('MULTIPLY', dirt, 0.95)), clamp=True)
    # the wash is mixed toward a DARKENED VERSION OF THE BOARD, not toward a
    # fixed grey: a rain streak on a black board is nearly invisible in life,
    # and mixing toward a constant turned every dark board tan.
    col = g.mix(sm_, col, g.mix(0.45, col, (0.135, 0.126, 0.112)))
    # laminate scuffing + a general film of dust everywhere, not only low down
    scr = g.noise(g.vmath('MULTIPLY', (tc, 3), (26.0, 1.6, 4.0)), scale=3.0,
                  detail=6.0, rough=0.8)
    film = g.noise(g.vmath('MULTIPLY', (tc, 3), (1.4, 1.4, 1.4)), scale=3.0,
                   detail=6.0)
    col = g.mix(g.math('MULTIPLY', g.math('MULTIPLY', dirt, 0.34), film),
                col, g.mix(0.5, col, (0.30, 0.285, 0.26)))
    # LARGE-SCALE MOTTLE.  A board is washed, scuffed and re-hung; its finish is
    # never uniform over a metre.  Mixing toward a lightened and a darkened
    # version of ITSELF keeps the brand colour and only breaks up the value,
    # which is the whole difference between "printed board" and "colour fill".
    mot = g.noise(g.vmath('MULTIPLY', (tc, 3), (0.9, 0.9, 0.9)), scale=2.0,
                  detail=5.0, rough=0.58)
    up = g.ramp(mot, [(0.50, (0, 0, 0)), (0.78, (1, 1, 1))])
    dn = g.ramp(mot, [(0.22, (1, 1, 1)), (0.50, (0, 0, 0))])
    col = g.mix(g.math('MULTIPLY', up, 0.30), col, g.mix(0.72, col, (1, 1, 1)))
    col = g.mix(g.math('MULTIPLY', dn, 0.26), col, g.mix(0.78, col, (0, 0, 0)))
    # EDGE GRIME.  Dirt and hand marks collect at the rim of every panel; the
    # middle of a board is always the cleanest part of it.
    ex = g.math('MINIMUM', (uv, 0), g.math('SUBTRACT', 1.0, (uv, 0)))
    ey = g.math('MINIMUM', (uv, 1), g.math('SUBTRACT', 1.0, (uv, 1)))
    edge = g.ramp(g.math('MINIMUM', g.math('MULTIPLY', ex, 2.4), ey),
                  [(0.0, (1, 1, 1)), (0.13, (0, 0, 0))])
    col = g.mix(g.math('MULTIPLY', g.math('MULTIPLY', edge, dirt), 0.42),
                col, g.mix(0.55, col, (0.055, 0.050, 0.043)))
    rough = g.math('ADD', g.math('ADD', 0.26, g.math('MULTIPLY', age, 0.30)),
                   g.math('MULTIPLY', dm, 0.30), clamp=True)
    rough = g.math('ADD', rough, g.math('MULTIPLY', scr, 0.12), clamp=True)
    rough = g.math('ADD', rough, g.math('MULTIPLY', sm_, 0.18), clamp=True)
    # the laminate is polished where it is handled and matt where it is chalky,
    # so the specular breaks up at the same scale the colour does
    rough = g.math('SUBTRACT', rough, g.math('MULTIPLY', up, 0.13), clamp=True)
    rough = g.math('ADD', rough, g.math('MULTIPLY', edge, 0.10), clamp=True)
    g._feed(b, 0, col)
    g._feed(b, 2, rough)
    # A matte laminate is not a 4 % dielectric mirror.  Left at the default,
    # the broad specular lobe of a 12.5-degree sun turned every BLACK board tan.
    _set_named(b, 0.24, "Specular IOR Level", "Specular")
    # printed vinyl on composite: orange peel ~8 mm, squeegee lines ~30 mm.
    # (The first version ran these at 480 cycles/m: pure sub-pixel noise, which
    # is why the boards rendered as flat plastic.)
    #
    # THE TWO SIZES IN THAT COMMENT ARE NOW THE TWO NUMBERS IN THE CODE.  They
    # were not before: `scale=2.0` on a x46 pre-gain emits 1.60/92 = 17.4 mm,
    # not 8, and `scale=33.0` on a Wave emits 0.31416/33 = 9.5 mm, not 30.  A
    # comment is not a specification; `noise_scale_for` and `wave_scale_for`
    # are.
    LAM_PEEL = 0.008           # orange peel in the laminate
    LAM_SQ = 0.030             # applicator/squeegee ridging, horizontal bands
    peel = g.noise(obj, scale=K.noise_scale_for(LAM_PEEL), detail=6.0)
    sq = g.wave(obj, scale=wave_scale_for(LAM_SQ), dist=2.0, detail=3.0,
                band='Z')
    # Stated as RADIANCE MODULATION (itemkit 5b), one stage per wavelength.
    # A laminated print is the smoothest thing in this module: the peel sits
    # mid-`isotropic_micro` (0.12-0.45, the band that holds the ACCEPTED 0.28
    # cloth), and the squeegee ridge below it, because it must read as a ripple
    # in the specular and not as a corrugation.  Raw Noise swings ~0.6 p-p; a
    # Wave's Color output swings the full 1.0.
    nrm = g.bump(peel, 1.0, modulation_pp=0.30, wavelength_m=LAM_PEEL,
                 height_pp=HEIGHT_PP["print_peel"])
    nrm = g.bump(sq, 1.0, normal=nrm, modulation_pp=0.18, wavelength_m=LAM_SQ,
                 height_pp=HEIGHT_PP["print_squeegee"])
    g._feed_named(b, "Normal", nrm)
    return m


def mat_fabric():
    """PVC-coated polyester banner mesh: weave, creases, grime, selective fade.

    What was here: `_bleach`, a bottom-up dirt gradient and a 1.2 mm grid bump at
    strength 0.16.  Rendered against the contract's real light that is a flat
    colour fill, which is exactly what the review saw.  A banner at 2 m reads as
    cloth because of five things, and it now has all five:

      1. a WEAVE, not a grid.  Warp and weft cross over and under, so the
         highlight runs in two interleaved directions with a half-pitch phase
         offset, and the yarns are slubby rather than perfectly regular.
      2. STORAGE CREASES.  A banner lives folded in a crate.  The fold lines are
         straight, roughly a metre apart, permanently shinier (the PVC is
         burnished) and slightly lighter (the ink has micro-cracked).
      3. SELECTIVE UV FADE.  Magenta and yellow pigments die years before cyan,
         so a faded banner does not go grey, it goes cold and light.  The fade is
         also strongest at the top, which sees the most sky.
      4. GRIME IN THE WEAVE.  Dirt collects in the interstices, not on the
         crowns, so the dirt mask is keyed to the weave's own valleys.
      5. INK vs SUBSTRATE.  Heavy solvent coverage lays flatter and glosses more
         than the bare white base, so roughness falls where the print is dark.

    Plus a real transmission: a banner backlit by a low sun glows, and this sun
    is 12.47 deg up.
    """
    m, g, b, _ = _new_mat("Fabric")
    base, aux, a, tc, uv, obj = _common(g)
    age, dirt, variant = (a, 0), (a, 1), (a, 2)
    p = g.vmath('MULTIPLY', (tc, 3), (1.0, 1.0, 1.0))

    # ---- 1. the weave -----------------------------------------------------
    # 1.15 mm pitch.  Warp and weft are half a pitch out of phase, and
    # `MAXIMUM` of the two is the over/under crossing.
    #
    # `PITCH = 870.0` DID NOT PRODUCE A 1.15 mm PITCH.  A Wave emits
    # 0.31416/Scale, not 1/Scale (§4a, measured over an 8x scale sweep), so 870
    # emitted 0.361 mm: a third of a millimetre, well under a pixel at every
    # distance this film ever sees a banner from, and only ~50x the float
    # resolution of a recentred object coordinate at the far end of a long
    # chunk.  The half-pitch phase offset on the next line gives the error
    # away — 0.00057 m is half of 1.15 mm, not half of 0.361 mm — so the intent
    # was always 1.15 and only the Scale was wrong.  The weave drives the grime
    # mask and the roughness as well as the relief, so this was a sub-pixel
    # COLOUR field too, not just a wasted bump.
    LAM_WEAVE = 0.00115
    PITCH = wave_scale_for(LAM_WEAVE)                    # 273.2
    warp = g.wave(p, scale=PITCH, dist=0.0, detail=0.0, band='X')
    weft = g.wave(g.vmath('ADD', p, (LAM_WEAVE * 0.5, 0.0, 0.0)), scale=PITCH,
                  dist=0.0, detail=0.0, band='Y')
    slub = g.noise(g.vmath('MULTIPLY', p, (7.0, 240.0, 7.0)), scale=3.0,
                   detail=3.0, rough=0.5)
    weave = g.math('MAXIMUM', g.math('MULTIPLY', warp, 0.96),
                   g.math('MULTIPLY', weft, 0.90))
    weave = g.math('ADD', g.math('MULTIPLY', weave, 0.86),
                   g.math('MULTIPLY', slub, 0.14), clamp=True)

    # ---- 2. storage creases ------------------------------------------------
    # object-space bands, so a banner creases where it was folded, not where its
    # UVs happen to run.  Two families, roughly 0.9 m and 1.15 m apart.
    # A ruler-straight grid of identical lines is a tiled texture, not a folded
    # banner: the first render of this shader read as ceramic tile.  The fold
    # coordinate is WARPED by a slow noise so the lines wander a few centimetres
    # over their length, and each line's strength is modulated by a second one
    # so some are hard, some are ghosts and some are missing entirely.
    warp = g.noise(g.vmath('MULTIPLY', p, (0.55, 0.55, 0.55)), scale=2.0,
                   detail=4.0)
    pw = g.vmath('ADD', p, g.vmath('MULTIPLY',
                                   g.vmath('SUBTRACT', warp, (0.5, 0.5, 0.5)),
                                   (0.16, 0.16, 0.16)))
    cr1 = g.wave(pw, scale=0.92, dist=0.0, detail=0.0, band='Z')
    cr2 = g.wave(pw, scale=0.74, dist=0.0, detail=0.0, band='X')
    crease = g.math('MAXIMUM',
                    g.ramp(cr1, [(0.476, (0, 0, 0)), (0.500, (1, 1, 1)),
                                 (0.524, (0, 0, 0))]),
                    g.ramp(cr2, [(0.482, (0, 0, 0)), (0.500, (1, 1, 1)),
                                 (0.518, (0, 0, 0))]))
    creaseh = g.noise(g.vmath('MULTIPLY', p, (0.42, 0.42, 0.42)), scale=2.0,
                      detail=4.0)
    crease = g.math('MULTIPLY', crease,
                    g.ramp(creaseh, [(0.30, (0, 0, 0)), (0.44, (0.35, 0.35, 0.35)),
                                     (0.66, (1, 1, 1))]),
                    clamp=True)
    # THE WRINKLES.  Near-vertical below the ties and fanning out toward the
    # bottom edge (the z pre-gain is a third of the horizontal one, so they are
    # streaks, not blobs).  These are the thing that makes a hung sheet read as
    # cloth at 2 m, and geometry cannot carry them: at the wavelengths that
    # matter the art tessellation would have to be 10 mm and the print layers
    # would stitch through each other (see `layer_step`).  In the shader they
    # cost nothing and resolve at any distance.
    #
    # The old comment here asked for "5-20 mm of relief" and that request is
    # gone, not reworded: see the relief block in section 6.  The two are kept
    # as separate signals rather than pre-summed because they are 2.6x apart in
    # wavelength and each now carries its own depth.
    wr1 = g.noise(g.vmath('MULTIPLY', p, (17.0, 17.0, 2.1)), scale=2.0,
                  detail=6.0, rough=0.60)
    wr2 = g.noise(g.vmath('MULTIPLY', p, (6.5, 6.5, 1.15)), scale=2.0,
                  detail=5.0, rough=0.55)
    crease = g.math('MULTIPLY', crease,
                    g.math('ADD', 0.30, g.math('MULTIPLY', age, 0.95)),
                    clamp=True)

    # ---- 3. selective fade -------------------------------------------------
    # top-weighted: uv.y is the height fraction of the sheet
    sun = g.math('ADD', 0.55, g.math('MULTIPLY',
                                     g.ramp((uv, 1), [(0.10, (0, 0, 0)),
                                                      (1.0, (1, 1, 1))]), 0.45))
    patch = g.noise(g.vmath('MULTIPLY', p, (1.3, 1.3, 1.3)), scale=2.0,
                    detail=5.0)
    fade = g.math('MULTIPLY',
                  g.math('MULTIPLY', age, sun),
                  g.math('ADD', 0.55, g.math('MULTIPLY', patch, 0.9)),
                  clamp=True)
    # magenta and yellow go first -> the survivor is cyan-ish and lighter
    sep = g.sep(base)
    faded = g.n("ShaderNodeCombineColor")
    g._feed(faded, 0, g.math('ADD', (sep, 0),
                             g.math('MULTIPLY', g.math('SUBTRACT', 0.62,
                                                       (sep, 0)), 0.42)))
    g._feed(faded, 1, g.math('ADD', (sep, 1),
                             g.math('MULTIPLY', g.math('SUBTRACT', 0.60,
                                                       (sep, 1)), 0.30)))
    g._feed(faded, 2, g.math('ADD', (sep, 2),
                             g.math('MULTIPLY', g.math('SUBTRACT', 0.56,
                                                       (sep, 2)), 0.16)))
    col = g.mix(fade, base, faded)
    # the crease lightens the ink where it cracked
    col = g.mix(g.math('MULTIPLY', crease, 0.34), col,
                g.mix(0.5, col, (0.62, 0.62, 0.60)))

    # ---- 4. grime ----------------------------------------------------------
    valley = g.math('SUBTRACT', 1.0, weave)
    ground = g.ramp((uv, 1), [(0.0, (1, 1, 1)), (0.13, (0.5, 0.5, 0.5)),
                              (0.46, (0, 0, 0))])
    grime = g.noise(g.vmath('MULTIPLY', p, (5.0, 5.0, 5.0)), scale=2.5,
                    detail=7.0, rough=0.62)
    dm = g.math('MULTIPLY',
                g.math('MULTIPLY', dirt,
                       g.math('ADD', g.math('MULTIPLY', ground, 0.80),
                              g.math('MULTIPLY', grime, 0.55))),
                g.math('ADD', 0.34, g.math('MULTIPLY', valley, 0.95)),
                clamp=True)
    col = g.mix(dm, col, (0.058, 0.050, 0.040))
    # vertical rain wash off the top edge, mixed toward a darkened self
    strk = g.noise(g.vmath('MULTIPLY', p, (26.0, 0.35, 0.35)), scale=3.0,
                   detail=6.0, rough=0.72)
    wash = g.math('MULTIPLY',
                  g.math('MULTIPLY',
                         g.ramp(strk, [(0.46, (0, 0, 0)), (0.60, (1, 1, 1))]),
                         g.ramp((uv, 1), [(0.22, (0, 0, 0)), (1.0, (1, 1, 1))])),
                  g.math('MULTIPLY', dirt, 0.75), clamp=True)
    col = g.mix(wash, col, g.mix(0.5, col, (0.115, 0.108, 0.096)))
    # the same three-scale unevenness the rigid boards get: without it a 3 m
    # banner is one flat value however good its relief is
    mot = g.noise(g.vmath('MULTIPLY', p, (1.1, 1.1, 1.1)), scale=2.0,
                  detail=5.0, rough=0.58)
    up = g.ramp(mot, [(0.50, (0, 0, 0)), (0.80, (1, 1, 1))])
    dn = g.ramp(mot, [(0.20, (1, 1, 1)), (0.50, (0, 0, 0))])
    col = g.mix(g.math('MULTIPLY', up, 0.24), col, g.mix(0.76, col, (1, 1, 1)))
    col = g.mix(g.math('MULTIPLY', dn, 0.22), col, g.mix(0.80, col, (0, 0, 0)))
    g._feed(b, 0, col)

    # ---- 5. roughness: ink lays flatter than the bare substrate -------------
    lum = g.n("ShaderNodeRGBToBW")
    g._feed(lum, 0, col)
    rough = g.math('SUBTRACT', 0.74,
                   g.math('MULTIPLY', g.math('SUBTRACT', 1.0, lum), 0.16))
    rough = g.math('ADD', rough, g.math('MULTIPLY', age, 0.10))
    rough = g.math('ADD', rough, g.math('MULTIPLY', dm, 0.14))
    rough = g.math('SUBTRACT', rough, g.math('MULTIPLY', crease, 0.24))
    rough = g.math('ADD', rough, g.math('MULTIPLY', up, 0.12), clamp=True)
    g._feed(b, 2, rough)
    _set_named(b, 0.38, "Specular IOR Level", "Specular")

    # ---- 6. relief: the wrinkles, the creases, the weave --------------------
    # FOUR WAVELENGTHS SPANNING 107x CANNOT SHARE ONE `Distance`.  The old line
    # summed a 1.15 mm weave, a ~10 mm crease ridge and 47/123 mm wrinkles into
    # a single bump and gave the lot one depth; even correctly wired that is a
    # single slope applied to four different feature sizes, which is the exact
    # confusion itemkit 5b exists to remove.  One stage per wavelength, chained
    # through `normal=`, each stating what it is meant to DO to the light.
    #
    #   wrinkles   `geometry_fold` (0.60-1.40).  These are real folds in a hung
    #              sheet carried in the shader because the tessellation cannot
    #              carry them (see the docstring).  They are the thing that
    #              makes cloth read as cloth at 2 m, so they are the deepest
    #              stage here — but NOT the 5-20 mm the old comment asked for:
    #              10 mm p-p at a 47 mm wavelength is a 34 deg surface, m = 5.0,
    #              which at a 12.47 deg sun is a shadow, not relief.  That is
    #              millimetre-thinking, and it is what got three amplitude sets
    #              rejected on the human figures.
    #   crease     `sparse_crease` (0.80-1.60).  A storage fold is a permanent
    #              burnished ridge and it acts on a few per cent of the area.
    #              Its wavelength is NOT the 0.34 m wave period: the ramp
    #              [0.476, 0.500, 0.524] is a 0.048-wide window on a wave whose
    #              slope at mid-crossing is pi/lambda = 9.2 /m, so the ridge is
    #              5.2 mm across and behaves as a ~10 mm feature.
    #   weave      0.28 exactly — the ACCEPTED cloth value from the record in
    #              itemkit 5b, at the pitch this material is named for.
    LAM_WR2 = K.NOISE_WAVELENGTH_FACTOR / 13.0           # 123.1 mm, slow fold
    LAM_WR1 = K.NOISE_WAVELENGTH_FACTOR / 34.0           #  47.1 mm, riding on it
    LAM_CREASE = 0.010                                   # the ramped ridge
    nrm = g.bump(wr2, 1.0, modulation_pp=0.95, wavelength_m=LAM_WR2,
                 height_pp=HEIGHT_PP["fabric_wr2"])
    nrm = g.bump(wr1, 1.0, normal=nrm, modulation_pp=0.75,
                 wavelength_m=LAM_WR1, height_pp=HEIGHT_PP["fabric_wr1"])
    nrm = g.bump(crease, 1.0, normal=nrm, modulation_pp=1.20,
                 wavelength_m=LAM_CREASE, height_pp=HEIGHT_PP["fabric_crease"])
    nrm = g.bump(weave, 1.0, normal=nrm, modulation_pp=0.28,
                 wavelength_m=LAM_WEAVE, height_pp=HEIGHT_PP["fabric_weave"])
    g._feed_named(b, "Normal", nrm)

    # ---- 7. transmission: a 12.5 deg sun behind a banner shows through ------
    tr = g.n("ShaderNodeBsdfTranslucent")
    g._feed(tr, 0, g.mix(0.55, col, (0.42, 0.40, 0.36)))
    mixs = g.n("ShaderNodeMixShader")
    # mesh banners (variant > 0.6) are perforated and pass much more light
    g._feed(mixs, 0, g.math('ADD', 0.075,
                            g.math('MULTIPLY',
                                   g.ramp(variant, [(0.58, (0, 0, 0)),
                                                    (0.70, (1, 1, 1))]), 0.20)))
    g.lk(b, 0, mixs, 1)
    g.lk(tr, 0, mixs, 2)
    out = [nd for nd in g.nt.nodes if nd.type == 'OUTPUT_MATERIAL'][0]
    g.lk(mixs, 0, out, 0)
    return m


def mat_steel():
    m, g, b, _ = _new_mat("Steel")
    base, aux, a, tc, uv, obj = _common(g)
    age, galv = (a, 0), (a, 2)
    p = g.vmath('MULTIPLY', (tc, 3), (1.0, 1.0, 1.0))
    # galvanised spangle.  A x55 pre-gain at Scale 1 emits 2.17/55 = 39.5 mm
    # cells, which is a plausible hot-dip spangle and is left exactly as it was.
    LAM_SPANGLE = K.VORONOI_WAVELENGTH_FACTOR / 55.0     # 39.5 mm
    spg = g.voro(g.vmath('MULTIPLY', p, (55.0, 55.0, 55.0)), scale=1.0)
    gcol = g.mix(g.math('MULTIPLY', spg, 0.9), (0.42, 0.44, 0.46),
                 (0.60, 0.62, 0.63))
    col = g.mix(galv, base, gcol)
    # rust: patchy, worse low down and worse with age
    rn = g.noise(g.vmath('MULTIPLY', p, (2.6, 2.6, 2.6)), scale=3.0, detail=8.0,
                 rough=0.62)
    rmask = g.math('MULTIPLY',
                   g.ramp(rn, [(0.42, (0, 0, 0)), (0.62, (1, 1, 1))]),
                   g.math('MULTIPLY', age, 0.85), clamp=True)
    rcol = g.mix(g.noise(g.vmath('MULTIPLY', p, (14.0, 14.0, 14.0)), scale=4.0),
                 (0.115, 0.042, 0.016), (0.22, 0.085, 0.030))
    col = g.mix(rmask, col, rcol)
    g._feed(b, 0, col)
    g._feed(b, 1, g.math('MULTIPLY', g.math('SUBTRACT', 1.0, rmask),
                         g.math('ADD', 0.18, g.math('MULTIPLY', galv, 0.8)),
                         clamp=True))
    g._feed(b, 2, g.math('ADD', g.math('ADD', 0.30, g.math('MULTIPLY', age, 0.26)),
                         g.math('MULTIPLY', rmask, 0.36), clamp=True))
    # Rust crust and galvanising spangle are 5x apart and are different things:
    # one is a proud scab with a torn edge, the other is a crystal facet that
    # barely displaces at all.  Two stages.
    #
    #   rust     `isotropic_macro` (0.35-0.95).  It is a real raised crust, and
    #            it is GATED — `rmask` is a ramp times `age`, so it acts on a
    #            fraction of a fraction and never becomes an ungated field.
    #            Its wavelength is not the 205 mm of the driving noise: the
    #            [0.42, 0.62] ramp is a 0.20 window on a signal that swings
    #            ~0.6 p-p, which sharpens the patch edge about 3x.
    #   spangle  `isotropic_micro` (0.12-0.45), at the bottom of it.  A spangle
    #            is a crystallographic facet: it changes the normal, it does
    #            not build a hill.
    LAM_RUST = (K.NOISE_WAVELENGTH_FACTOR / 7.8) * (0.20 / 0.6)   # 68.4 mm
    nrm = g.bump(rmask, 1.0, modulation_pp=0.70, wavelength_m=LAM_RUST,
                 height_pp=HEIGHT_PP["steel_rust"])
    nrm = g.bump(spg, 1.0, normal=nrm, modulation_pp=0.25,
                 wavelength_m=LAM_SPANGLE, height_pp=HEIGHT_PP["steel_spangle"])
    g._feed_named(b, "Normal", nrm)
    return m


def mat_alu():
    m, g, b, _ = _new_mat("Alu")
    base, aux, a, tc, uv, obj = _common(g)
    age = (a, 0)
    p = g.vmath('MULTIPLY', (tc, 3), (1.0, 1.0, 1.0))
    grain = g.noise(g.vmath('MULTIPLY', p, (300.0, 6.0, 300.0)), scale=2.0,
                    detail=4.0)
    col = g.mix(g.math('MULTIPLY', age, 0.5), base, (0.26, 0.27, 0.28))
    g._feed(b, 0, g.mix(g.math('MULTIPLY', grain, 0.25), col, (0.55, 0.56, 0.58)))
    # anodised / mill-finish aluminium is NOT a mirror: a fully metallic,
    # roughness-0.2 board rim rendered as a white streak against the sky.
    g._feed(b, 1, 0.82)
    g._feed(b, 2, g.math('ADD', 0.36, g.math('MULTIPLY', age, 0.26), clamp=True))
    # Mill/brush grain.  The pre-gain is (300, 6, 300), so the feature is 50x
    # longer along y than across it: the relief wavelength that matters is the
    # SHORT one, 1.60/600 = 2.67 mm, because that is the direction the normal
    # actually turns in.  `isotropic_micro` at the bottom of the band — a mill
    # finish is nearly smooth and reads as a satin sheen, and the module already
    # learned once (two lines up) that treating this metal as a mirror turned a
    # board rim into a white streak against the sky.
    LAM_GRAIN = K.NOISE_WAVELENGTH_FACTOR / 600.0        # 2.67 mm across
    g._feed_named(b, "Normal",
                  g.bump(grain, 1.0, modulation_pp=0.18,
                         wavelength_m=LAM_GRAIN,
                         height_pp=HEIGHT_PP["alu_grain"]))
    return m


def mat_rubber():
    m, g, b, _ = _new_mat("Rubber")
    base, aux, a, tc, uv, obj = _common(g)
    age = (a, 0)
    p = g.vmath('MULTIPLY', (tc, 3), (1.0, 1.0, 1.0))
    chalk = g.noise(g.vmath('MULTIPLY', p, (9.0, 9.0, 9.0)), scale=3.0, detail=7.0)
    col = g.mix(g.math('MULTIPLY', g.math('MULTIPLY', age, 0.55),
                       g.math('ADD', 0.35, chalk), clamp=True),
                base, (0.082, 0.078, 0.073))
    g._feed(b, 0, col)
    g._feed(b, 2, g.math('ADD', 0.62, g.math('MULTIPLY', age, 0.24), clamp=True))
    micro = g.noise(g.vmath('MULTIPLY', p, (200.0, 200.0, 200.0)), scale=2.0,
                    detail=6.0)
    # Tyre-wall mould texture and the crazing that comes with it: 1.60/400 =
    # 4.0 mm.  Top of `isotropic_micro` (0.12-0.45) — an old, chalked tyre wall
    # is the mattest, most broken-up surface in this module short of concrete,
    # and these are stacked in the open where the 12.47 deg key rakes across
    # them.
    LAM_MICRO = K.NOISE_WAVELENGTH_FACTOR / 400.0        # 4.0 mm
    g._feed_named(b, "Normal",
                  g.bump(micro, 1.0, modulation_pp=0.35,
                         wavelength_m=LAM_MICRO,
                         height_pp=HEIGHT_PP["rubber_micro"]))
    return m


def mat_plastic():
    m, g, b, _ = _new_mat("Plastic")
    base, aux, a, tc, uv, obj = _common(g)
    age, dirt = (a, 0), (a, 1)
    p = g.vmath('MULTIPLY', (tc, 3), (1.0, 1.0, 1.0))
    col = _bleach(g, base, age)
    dnz = g.noise(g.vmath('MULTIPLY', p, (12.0, 12.0, 12.0)), scale=3.0)
    dm = g.math('MULTIPLY', g.math('MULTIPLY', dirt, dnz), 1.4, clamp=True)
    col = g.mix(dm, col, (0.10, 0.088, 0.072))
    g._feed(b, 0, col)
    g._feed(b, 2, g.math('ADD', 0.28, g.math('MULTIPLY', age, 0.36), clamp=True))
    # Moulded polymer — cones, bins, ducting.  1.60/180 = 8.9 mm of tool
    # grain, low `isotropic_micro`: injection texture is shallow by design and
    # the parts are new-ish relative to everything else out here.
    LAM_MOULD = K.NOISE_WAVELENGTH_FACTOR / 180.0        # 8.9 mm
    g._feed_named(b, "Normal",
                  g.bump(g.noise(g.vmath('MULTIPLY', p, (90.0, 90.0, 90.0)),
                                 scale=2.0), 1.0, modulation_pp=0.22,
                         wavelength_m=LAM_MOULD,
                         height_pp=HEIGHT_PP["plastic_mould"]))
    return m


def mat_conc():
    m, g, b, _ = _new_mat("Concrete")
    base, aux, a, tc, uv, obj = _common(g)
    age = (a, 0)
    p = g.vmath('MULTIPLY', (tc, 3), (1.0, 1.0, 1.0))
    agg = g.voro(g.vmath('MULTIPLY', p, (34.0, 34.0, 34.0)), scale=1.0)
    fine = g.noise(g.vmath('MULTIPLY', p, (8.0, 8.0, 8.0)), scale=3.0, detail=8.0)
    col = g.mix(g.math('MULTIPLY', agg, 0.55), base, (0.30, 0.30, 0.29))
    col = g.mix(g.math('MULTIPLY', g.math('MULTIPLY', age, fine), 1.2), col,
                (0.135, 0.130, 0.120))
    g._feed(b, 0, col)
    g._feed(b, 2, 0.88)
    # THE ONE PLACE A SUMMED HEIGHT IS HONEST.  `agg` emits 2.17/34 = 63.8 mm
    # and `fine` 1.60/24 = 66.7 mm — 4 % apart, so one Distance really does fit
    # both and they stay in a single stage.
    #
    # `isotropic_macro` (0.35-0.95) at the top: exposed-aggregate concrete is
    # the coarsest surface in this module.  It stops at 0.85 and not higher
    # because it is UNGATED — it covers the whole surface, and the standing
    # rule out of the human figures is that nothing isotropic and ungated goes
    # above m = 1.  (pit_wall_unit runs its aggregate at 2.63, but that stage
    # is multiplied by a `skin_gone` mask and acts on a fraction of the face.)
    LAM_CONC = 0.5 * (K.VORONOI_WAVELENGTH_FACTOR / 34.0
                      + K.NOISE_WAVELENGTH_FACTOR / 24.0)      # 65.3 mm
    g._feed_named(b, "Normal",
                  g.bump(g.math('ADD', g.math('MULTIPLY', agg, 0.5),
                                g.math('MULTIPLY', fine, 0.5)), 1.0,
                         modulation_pp=0.85, wavelength_m=LAM_CONC,
                         height_pp=HEIGHT_PP["concrete_agg"]))
    return m


def mat_wood():
    m, g, b, _ = _new_mat("Wood")
    base, aux, a, tc, uv, obj = _common(g)
    age = (a, 0)
    p = g.vmath('MULTIPLY', (tc, 3), (1.0, 1.0, 1.0))
    grain = g.wave(g.vmath('MULTIPLY', p, (1.0, 1.0, 1.0)), scale=26.0, dist=6.0,
                   detail=4.0, band='X')
    col = g.mix(g.math('MULTIPLY', grain, 0.6), base,
                g.mix(0.55, base, (0.06, 0.035, 0.018)))
    col = g.mix(g.math('MULTIPLY', age, 0.45), col, (0.24, 0.225, 0.205))
    g._feed(b, 0, col)
    g._feed(b, 2, g.math('ADD', 0.55, g.math('MULTIPLY', age, 0.28), clamp=True))
    # Sawn timber and ply — hoardings, pallets, post packers.  0.31416/26 =
    # 12.1 mm, which is a real annual-ring spacing for the softwood this stuff
    # is made of, so the Scale is left alone; only the depth is stated.  Top of
    # `isotropic_micro` / bottom of `isotropic_macro`: weathered softwood loses
    # its summerwood and the grain stands proud, but it is still a plank and
    # not a stucco.  The Wave's Color output swings nearly the full 1.0.
    LAM_WOOD = WAVE_WAVELENGTH_FACTOR / 26.0             # 12.1 mm
    g._feed_named(b, "Normal",
                  g.bump(grain, 1.0, modulation_pp=0.40,
                         wavelength_m=LAM_WOOD,
                         height_pp=HEIGHT_PP["wood_grain"]))
    return m


def mat_emit():
    m, g, b, out = _new_mat("Emit")
    base, aux, a, tc, uv, obj = _common(g)
    sepb = g.sep(base)
    alpha = g.n("ShaderNodeSeparateColor")           # keep base.a via attribute
    em = g.n("ShaderNodeEmission")
    g._feed(em, 0, base)
    g._feed(em, 1, g.math('MULTIPLY', (aux, 2), 14.0))
    g._feed(b, 0, (0.012, 0.012, 0.013))
    g._feed(b, 2, 0.18)
    mixs = g.n("ShaderNodeMixShader")
    g._feed(mixs, 0, g.math('MULTIPLY', (aux, 2), 3.0, clamp=True))
    g.lk(b, 0, mixs, 1)
    g.lk(em, 0, mixs, 2)
    g.lk(mixs, 0, out, 0)
    return m


def mat_glass():
    m, g, b, _ = _new_mat("Glass")
    base, aux, a, tc, uv, obj = _common(g)
    g._feed(b, 0, base)
    g._feed(b, 2, 0.04)
    g._feed(b, 3, 1.45)
    _set_named(b, 1.0, "Transmission Weight", "Transmission")
    return m


def mat_paint():
    m, g, b, out = _new_mat("Paint")
    base, aux, a, tc, uv, obj = _common(g)
    age = (a, 0)
    p = g.vmath('MULTIPLY', (tc, 3), (1.0, 1.0, 1.0))
    wear = g.noise(g.vmath('MULTIPLY', p, (4.5, 4.5, 4.5)), scale=4.0, detail=9.0,
                   rough=0.7)
    mask = g.ramp(g.math('SUBTRACT', wear, g.math('MULTIPLY', age, 0.36)),
                  [(0.30, (0, 0, 0)), (0.46, (1, 1, 1))])
    col = g.mix(g.math('MULTIPLY', age, 0.5), base, (0.28, 0.28, 0.27))
    g._feed(b, 0, col)
    g._feed(b, 2, 0.80)
    tr = g.n("ShaderNodeBsdfTransparent")
    mixs = g.n("ShaderNodeMixShader")
    g._feed(mixs, 0, mask)
    g.lk(tr, 0, mixs, 1)
    g.lk(b, 0, mixs, 2)
    g.lk(mixs, 0, out, 0)
    if hasattr(m, "blend_method"):        # EEVEE only; gone in some 5.x builds
        try:
            m.blend_method = 'BLEND'
        except Exception:
            pass
    return m


def mat_tarp():
    m, g, b, _ = _new_mat("Tarp")
    base, aux, a, tc, uv, obj = _common(g)
    age, dirt = (a, 0), (a, 1)
    p = g.vmath('MULTIPLY', (tc, 3), (1.0, 1.0, 1.0))
    col = _bleach(g, base, age)
    col = g.mix(g.math('MULTIPLY', dirt, 0.8, clamp=True), col,
                (0.085, 0.078, 0.066))
    g._feed(b, 0, col)
    g._feed(b, 2, g.math('ADD', 0.55, g.math('MULTIPLY', age, 0.25), clamp=True))
    # The scrim under the PVC coating.  0.31416/180 = 1.75 mm, which is what a
    # 1000D 9x9-per-inch reinforcing weave actually measures, so the Scale
    # stands; only the depth is stated.  Mid `isotropic_micro` — a coated tarp
    # is a woven cloth seen THROUGH a skin, so it is shallower than the bare
    # banner weave next door even though the two are the same kind of feature.
    LAM_RIB = WAVE_WAVELENGTH_FACTOR / 180.0             # 1.75 mm
    rib = g.wave(g.vmath('MULTIPLY', p, (1.0, 1.0, 1.0)), scale=180.0, band='X')
    g._feed_named(b, "Normal",
                  g.bump(rib, 1.0, modulation_pp=0.24, wavelength_m=LAM_RIB,
                         height_pp=HEIGHT_PP["tarp_rib"]))
    return m


def build_materials():
    MATS.clear()
    for nm, fn in (("Print", mat_print), ("Fabric", mat_fabric),
                   ("Steel", mat_steel), ("Alu", mat_alu), ("Rubber", mat_rubber),
                   ("Plastic", mat_plastic), ("Concrete", mat_conc),
                   ("Wood", mat_wood), ("Emit", mat_emit), ("Glass", mat_glass),
                   ("Paint", mat_paint), ("Tarp", mat_tarp)):
        MATS[nm] = fn()
    return [MATS[n] for n in MAT_ORDER]


# --------------------------------------------------------------------------- #
#  5.  type — glyphs baked from Blender's bundled font, cached                  #
# --------------------------------------------------------------------------- #

_GLYPH = {}
_CAPH = [None]


def _bake_glyph(ch, res=4):
    cu = bpy.data.curves.new("_dr_glyph", 'FONT')
    cu.body = ch
    cu.size = 1.0
    cu.extrude = 0.0
    cu.align_x = 'LEFT'
    cu.align_y = 'TOP_BASELINE'
    cu.resolution_u = res
    ob = bpy.data.objects.new("_dr_glyph", cu)
    bpy.context.scene.collection.objects.link(ob)
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    V = np.zeros((0, 2)); F = np.zeros((0, 3), int)
    if me is not None and len(me.vertices):
        co = np.empty(len(me.vertices) * 3)
        me.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        me.calc_loop_triangles()
        if len(me.loop_triangles):
            tri = np.empty(len(me.loop_triangles) * 3, dtype=np.int32)
            me.loop_triangles.foreach_get("vertices", tri)
            F = tri.reshape(-1, 3).astype(np.int64)
            V = co[:, :2].copy()
    ev.to_mesh_clear()
    bpy.context.scene.collection.objects.unlink(ob)
    bpy.data.objects.remove(ob)
    bpy.data.curves.remove(cu)
    return V, F


def glyph(ch, res=4):
    """cap-height-normalised glyph: verts (N,2) with baseline y=0, x from 0,
    triangles (M,3), and an advance width in cap-heights."""
    if _CAPH[0] is None:
        V, _F = _bake_glyph("H", res)
        _CAPH[0] = float(V[:, 1].max()) if len(V) else 0.7
    key = ch
    if key in _GLYPH:
        return _GLYPH[key]
    if ch == " ":
        out = (np.zeros((0, 2)), np.zeros((0, 3), int), 0.30)
        _GLYPH[key] = out
        return out
    V, F = _bake_glyph(ch)
    k = 1.0 / max(_CAPH[0], 1e-6)
    if len(V):
        V = V * k
        x0 = V[:, 0].min()
        V[:, 0] -= x0
        adv = float(V[:, 0].max())
    else:
        adv = 0.30
    out = (V, F, adv)
    _GLYPH[key] = out
    return out


_TEXT = {}


def text_poly(body, tracking=0.10):
    """(verts (N,2) in cap-heights, tris (M,3), total width).  Cached."""
    key = (body, round(tracking, 4))
    if key in _TEXT:
        return _TEXT[key]
    VS, FS = [], []
    x = 0.0
    n0 = 0
    for ch in body:
        V, F, adv = glyph(ch)
        if len(V):
            VS.append(V + np.array([x, 0.0]))
            FS.append(F + n0)
            n0 += len(V)
        x += adv + (tracking if ch != " " else 0.0)
    x = max(0.0, x - tracking)
    out = (np.concatenate(VS) if VS else np.zeros((0, 2)),
           np.concatenate(FS) if FS else np.zeros((0, 3), int), x)
    _TEXT[key] = out
    return out


# --------------------------------------------------------------------------- #
#  6.  the brand book — every brand fictional, invented for this film           #
# --------------------------------------------------------------------------- #
#
# 12 names + colours are shared verbatim with build_architecture.py's BRANDS so
# the pit wall, the grandstand fascia and the trackside boards advertise the
# SAME companies.  The other 19 are this module's, and carry sector, mark,
# typographic tracking, strapline and a commercial tier (tier drives how much
# board space the brand buys, which is what makes the distribution read as a
# real sales sheet rather than as uniform noise).

BRANDS = [
    # name, bg, fg, mark, tier, tracking, strapline
    ("VERSANT",    '#12385e', '#e9eef2', 'chevron', 3, 0.16, "ASSURANCE"),
    ("OCTAL",      '#c8442a', '#fdf6e8', 'grid',    3, 0.13, "SYSTEMS"),
    ("CADENCE",    '#1d1f22', '#d8b03a', 'wave',    3, 0.20, "HORLOGERIE"),
    ("SEPTIME",    '#0f6b52', '#eef6f2', 'hex',     2, 0.14, "AGRO"),
    ("PALLAS",     '#5a2d6e', '#f0e9f4', 'ring',    2, 0.18, "CAPITAL"),
    ("TERRA NOVA", '#7a5a24', '#f6efdf', 'delta',   2, 0.10, "TRAVAUX"),
    ("ZEPHYR",     '#0f7fa8', '#f2fbfe', 'arcs',    3, 0.15, "AIR"),
    ("BRIAR",      '#4a5a2c', '#f0f3e6', 'shield',  1, 0.12, "OUTDOORS"),
    ("NOVEM",      '#a01d3c', '#ffeef2', 'bars',    2, 0.16, "SANTE"),
    ("ORTHO",      '#2b2f33', '#9fd6e8', 'mono',    1, 0.19, "OPTIQUE"),
    ("LUMIERE",    '#d8a417', '#241d10', 'wing',    3, 0.17, "ENERGIE"),
    ("MARQUE",     '#171a1d', '#e2e5e8', 'diamond', 2, 0.22, "MEDIA"),
    # --- this module's additions ------------------------------------------
    ("MERIDIAN",   '#111114', '#f4c518', 'chevron', 4, 0.14, "PNEUMATIQUES"),
    ("ARDENT",     '#e0561a', '#191512', 'delta',   4, 0.12, "CARBURANTS"),
    ("VOLTAIC",    '#101014', '#d9f23a', 'bolt',    3, 0.15, "CHARGE"),
    ("KESTREL",    '#33506b', '#eef2f6', 'wing',    2, 0.13, "LOGISTIQUE"),
    ("FONTAINE",   '#bfe2f2', '#14384c', 'drop',    2, 0.16, "EAU DE SOURCE"),
    ("SABLIER",    '#e8dcc0', '#1a1712', 'diamond', 2, 0.24, "GENEVE"),
    ("NORDVAL",    '#cfe4ef', '#123044', 'mount',   1, 0.14, "ACIERS"),
    ("HALCYON",    '#1d4b3c', '#e9dcbf', 'arch',    2, 0.18, "HOTELS"),
    ("PRIMEUR",    '#c4157a', '#ffffff', 'bars',    1, 0.12, "MARCHES"),
    ("OBSIDIAN",   '#0c0c0e', '#f2f2f2', 'mono',    3, 0.26, "GESTION"),
    ("CIRRUS",     '#4aa3d8', '#0b2231', 'arcs',    2, 0.15, "TELECOM"),
    ("MARENGO",    '#5c1522', '#e6cf9c', 'shield',  2, 0.17, "DOMAINE"),
    ("ATELIER 9",  '#efe7d8', '#161616', 'mono',    1, 0.11, "CARROSSERIE"),
    ("VERITAS",    '#0d2a4a', '#c9a447', 'ring',    3, 0.19, "AUDIT"),
    ("PYLON",      '#6d7278', '#e02b1f', 'grid',    1, 0.13, "RESEAUX"),
    ("LE BREUIL",  '#6b1220', '#e8c46a', 'crest',   1, 0.15, "1897"),
    ("ALTIS",      '#0b5d63', '#f0fbfa', 'delta',   2, 0.16, "AVIATION"),
    ("CALIBRE",    '#232628', '#e46a1f', 'hex',     2, 0.14, "OUTILLAGE"),
    ("CIRCUIT VITRINE", '#26292d', '#f5f5f2', 'wing', 5, 0.20, "LE CIRCUIT"),
]

BRAND_BY_NAME = {b[0]: i for i, b in enumerate(BRANDS)}
HOUSE = BRAND_BY_NAME["CIRCUIT VITRINE"]
TYRE_BRAND = BRAND_BY_NAME["MERIDIAN"]

# a brand's chance of buying any given slot, from its tier
TIER_W = {1: 0.6, 2: 1.0, 3: 1.7, 4: 2.6, 5: 1.2}
_BRAND_CDF = np.cumsum([TIER_W[b[4]] for b in BRANDS])
_BRAND_CDF = _BRAND_CDF / _BRAND_CDF[-1]


def brand_pick(*keys):
    u = hash01(*keys)
    return int(np.searchsorted(_BRAND_CDF, u))


class Brand:
    __slots__ = ("i", "name", "bg", "fg", "mark", "tier", "track", "strap")

    def __init__(self, i):
        i = i % len(BRANDS)
        nm, bg, fg, mk, tier, tr, st = BRANDS[i]
        self.i = i
        self.name = nm
        self.bg = srgb(bg)
        self.fg = srgb(fg)
        self.mark = mk
        self.tier = tier
        self.track = tr
        self.strap = st


# --------------------------------------------------------------------------- #
#  7.  the art engine — board graphics authored in board metres                 #
# --------------------------------------------------------------------------- #

class Art:
    """2-D artwork in board coordinates: u along the board from 0..W (reading
    order), v up from 0..H.  Everything is convex-safe or pre-triangulated."""

    def __init__(self, W, H):
        self.W = W
        self.H = H
        self.items = []          # (verts (N,2), tris (M,3), colour, layer)

    def _push(self, V, F, col, layer):
        if len(V) == 0 or len(F) == 0:
            return
        self.items.append((np.asarray(V, float), np.asarray(F, np.int64),
                           tuple(col), layer))

    def fan(self, pts, col, layer=1):
        P = np.asarray(pts, float)
        n = len(P)
        if n < 3:
            return
        F = np.stack([np.zeros(n - 2, int), np.arange(1, n - 1),
                      np.arange(2, n)], -1)
        self._push(P, F, col, layer)

    def rect(self, u0, v0, u1, v1, col, layer=1):
        self.fan([(u0, v0), (u1, v0), (u1, v1), (u0, v1)], col, layer)

    def disc(self, cu, cv, r, col, layer=1, n=44, a0=0.0, a1=2 * math.pi):
        th = np.linspace(a0, a1, n)
        P = np.column_stack([cu + r * np.cos(th), cv + r * np.sin(th)])
        P = np.vstack([[cu, cv], P])
        F = np.stack([np.zeros(n - 1, int), np.arange(1, n),
                      np.arange(2, n + 1)], -1)
        self._push(P, F, col, layer)

    def ring(self, cu, cv, r, w, col, layer=1, n=64, a0=0.0, a1=2 * math.pi):
        th = np.linspace(a0, a1, n)
        A = np.column_stack([cu + (r - w) * np.cos(th), cv + (r - w) * np.sin(th)])
        B = np.column_stack([cu + r * np.cos(th), cv + r * np.sin(th)])
        P = np.vstack([A, B])
        i = np.arange(n - 1)
        F = np.concatenate([np.stack([i, i + n, i + n + 1], -1),
                            np.stack([i, i + n + 1, i + 1], -1)])
        self._push(P, F, col, layer)

    def strip(self, A, B, col, layer=1):
        """quad strip between two equal-length polylines"""
        A = np.asarray(A, float); B = np.asarray(B, float)
        n = len(A)
        P = np.vstack([A, B])
        i = np.arange(n - 1)
        F = np.concatenate([np.stack([i, i + n, i + n + 1], -1),
                            np.stack([i, i + n + 1, i + 1], -1)])
        self._push(P, F, col, layer)

    def text(self, body, cu, cv, h, col, layer=2, align='C', tracking=0.12,
             slant=0.0, width=1.0, bold=0.0):
        V, F, w = text_poly(body, tracking)
        if len(V) == 0:
            return 0.0
        V = V.copy()
        V[:, 0] *= width
        w *= width
        if slant:
            V[:, 0] += V[:, 1] * math.tan(math.radians(slant))
        V *= h
        w *= h
        if align == 'C':
            V[:, 0] -= w * 0.5
        elif align == 'R':
            V[:, 0] -= w
        V[:, 0] += cu
        V[:, 1] += cv
        if bold > 0.0:
            # Emboldening by stroke dilation.  Each dilated copy is its own art
            # item on its own micro-layer: pushing them as one item made 13
            # coplanar overlapping outlines that z-fought into mush.
            nb = 14
            for a in range(nb):
                th = a * 2.0 * math.pi / nb
                self._push(V + np.array([math.cos(th), math.sin(th)]) * bold,
                           F, col, layer + 0.16 * (a + 1) / nb)
        self._push(V, F, col, layer + (0.20 if bold > 0.0 else 0.0))
        return w

    def text_width(self, body, h, tracking=0.12, width=1.0):
        return text_poly(body, tracking)[2] * h * width

    # ---- brand marks -----------------------------------------------------
    def mark(self, kind, cu, cv, size, col, layer=2, seed=0):
        s = size
        if kind == 'chevron':
            for k in range(2):
                o = k * s * 0.46
                self.fan([(cu - s * 0.55 + o, cv - s * 0.5),
                          (cu - s * 0.17 + o, cv - s * 0.5),
                          (cu + s * 0.30 + o, cv), (cu - s * 0.17 + o, cv + s * 0.5),
                          (cu - s * 0.55 + o, cv + s * 0.5),
                          (cu - s * 0.08 + o, cv)], col, layer)
        elif kind == 'ring':
            self.ring(cu, cv, s * 0.52, s * 0.13, col, layer)
            self.rect(cu - s * 0.06, cv - s * 0.62, cu + s * 0.06, cv + s * 0.62,
                      col, layer)
        elif kind == 'bars':
            for k in range(3):
                self.fan([(cu - s * 0.5 + k * s * 0.28, cv - s * 0.5),
                          (cu - s * 0.28 + k * s * 0.28, cv - s * 0.5),
                          (cu - s * 0.10 + k * s * 0.28, cv + s * 0.5),
                          (cu - s * 0.32 + k * s * 0.28, cv + s * 0.5)], col, layer)
        elif kind == 'wave':
            n = 40
            t = np.linspace(-0.6, 0.6, n)
            y = np.sin(t * 5.6) * s * 0.24
            A = np.column_stack([cu + t * s, cv + y - s * 0.10])
            B = np.column_stack([cu + t * s, cv + y + s * 0.10])
            self.strip(A, B, col, layer)
        elif kind == 'diamond':
            self.fan([(cu, cv - s * 0.62), (cu + s * 0.44, cv),
                      (cu, cv + s * 0.62), (cu - s * 0.44, cv)], col, layer)
            self.fan([(cu, cv - s * 0.30), (cu + s * 0.21, cv),
                      (cu, cv + s * 0.30), (cu - s * 0.21, cv)],
                     (0.0, 0.0, 0.0), layer + 1)
        elif kind == 'mono':
            self.ring(cu, cv, s * 0.58, s * 0.09, col, layer)
        elif kind == 'delta':
            self.fan([(cu - s * 0.55, cv - s * 0.45), (cu + s * 0.55, cv - s * 0.45),
                      (cu, cv + s * 0.55)], col, layer)
        elif kind == 'arcs':
            for k in range(3):
                self.ring(cu - s * 0.2, cv - s * 0.35, s * (0.35 + k * 0.24),
                          s * 0.085, col, layer, n=26, a0=0.10, a1=1.42)
        elif kind == 'shield':
            self.fan([(cu - s * 0.42, cv + s * 0.55), (cu + s * 0.42, cv + s * 0.55),
                      (cu + s * 0.42, cv - s * 0.10), (cu, cv - s * 0.60),
                      (cu - s * 0.42, cv - s * 0.10)], col, layer)
        elif kind == 'grid':
            for a in range(2):
                for bq in range(2):
                    self.rect(cu - s * 0.5 + a * s * 0.54,
                              cv - s * 0.5 + bq * s * 0.54,
                              cu - s * 0.08 + a * s * 0.54,
                              cv - s * 0.08 + bq * s * 0.54,
                              col if (a + bq) % 2 == 0 else col, layer)
        elif kind == 'hex':
            th = np.linspace(0, 2 * math.pi, 7)[:6] + math.pi / 6
            self.fan(np.column_stack([cu + s * 0.55 * np.cos(th),
                                      cv + s * 0.55 * np.sin(th)]), col, layer)
        elif kind == 'wing':
            for k in range(3):
                o = k * s * 0.20
                self.fan([(cu - s * 0.60, cv - s * 0.28 + o),
                          (cu + s * 0.52 - k * s * 0.20, cv - s * 0.28 + o),
                          (cu + s * 0.40 - k * s * 0.20, cv - s * 0.14 + o),
                          (cu - s * 0.60, cv - s * 0.14 + o)], col, layer)
        elif kind == 'bolt':
            self.fan([(cu + s * 0.10, cv + s * 0.60), (cu - s * 0.34, cv + s * 0.02),
                      (cu - s * 0.02, cv + s * 0.02), (cu - s * 0.14, cv - s * 0.60),
                      (cu + s * 0.34, cv - s * 0.02), (cu + s * 0.00, cv - s * 0.02)],
                     col, layer)
        elif kind == 'drop':
            self.disc(cu, cv - s * 0.10, s * 0.40, col, layer)
            self.fan([(cu - s * 0.30, cv + s * 0.05), (cu, cv + s * 0.62),
                      (cu + s * 0.30, cv + s * 0.05)], col, layer)
        elif kind == 'mount':
            self.fan([(cu - s * 0.60, cv - s * 0.40), (cu - s * 0.12, cv + s * 0.50),
                      (cu + s * 0.16, cv + s * 0.02), (cu + s * 0.60, cv - s * 0.40)],
                     col, layer)
        elif kind == 'arch':
            self.ring(cu, cv - s * 0.30, s * 0.55, s * 0.14, col, layer, n=30,
                      a0=0.0, a1=math.pi)
            self.rect(cu - s * 0.55, cv - s * 0.55, cu - s * 0.41, cv - s * 0.30,
                      col, layer)
            self.rect(cu + s * 0.41, cv - s * 0.55, cu + s * 0.55, cv - s * 0.30,
                      col, layer)
        elif kind == 'crest':
            self.fan([(cu - s * 0.40, cv + s * 0.52), (cu + s * 0.40, cv + s * 0.52),
                      (cu + s * 0.30, cv - s * 0.20), (cu, cv - s * 0.58),
                      (cu - s * 0.30, cv - s * 0.20)], col, layer)
            self.rect(cu - s * 0.22, cv - s * 0.02, cu + s * 0.22, cv + s * 0.10,
                      (0.0, 0.0, 0.0), layer + 1)


# ---- board layouts --------------------------------------------------------
# Each returns nothing; it paints `art`.  `k` is the board's own hash seed.

def _lay_fullbleed(art, br, k):
    W, H = art.W, art.H
    art.rect(0, 0, W, H, br.bg, 0)
    h = H * rnd(0.42, 0.56, k, 1)
    w = art.text_width(br.name, h, br.track)
    if w > W * 0.80:
        h *= W * 0.80 / w
        w = W * 0.80
    art.text(br.name, W * 0.5, H * 0.5 - h * 0.40, h, br.fg, 2, tracking=br.track)


def _lay_mark_left(art, br, k):
    W, H = art.W, art.H
    art.rect(0, 0, W, H, br.bg, 0)
    ms = H * 0.56
    art.mark(br.mark, W * 0.13, H * 0.52, ms, br.fg, 2)
    h = H * rnd(0.34, 0.46, k, 2)
    w = art.text_width(br.name, h, br.track)
    if w > W * 0.72:
        h *= W * 0.72 / w
    # layer 3, not 2: the wordmark and the mark can overlap on a short board,
    # and two art elements on the same layer are coplanar and z-fight (the "V"
    # of VOLTAIC was being eaten by its own bolt).
    art.text(br.name, W * 0.24, H * 0.5 - h * 0.40, h, br.fg, 3, align='L',
             tracking=br.track)


def _lay_band(art, br, k):
    W, H = art.W, art.H
    art.rect(0, 0, W, H, br.fg, 0)
    bv = H * rnd(0.52, 0.68, k, 3)
    art.rect(0, H - bv, W, H, br.bg, 1)
    h = bv * 0.58
    w = art.text_width(br.name, h, br.track)
    if w > W * 0.86:
        h *= W * 0.86 / w
    art.text(br.name, W * 0.5, H - bv * 0.5 - h * 0.40, h, br.fg, 2,
             tracking=br.track)
    art.text(br.strap, W * 0.5, (H - bv) * 0.34, (H - bv) * 0.34, br.bg, 2,
             tracking=br.track * 1.9)


def _lay_diag(art, br, k):
    W, H = art.W, art.H
    art.rect(0, 0, W, H, br.bg, 0)
    x0 = W * rnd(0.42, 0.62, k, 4)
    art.fan([(x0, 0), (W, 0), (W, H), (x0 + H * 0.55, H)], br.fg, 1)
    h = H * 0.44
    avail = x0 - W * 0.10                 # the wordmark must clear the split
    w = art.text_width(br.name, h, br.track)
    if w > avail:
        h *= avail / w
    art.text(br.name, W * 0.055, H * 0.5 - h * 0.40, h, br.fg, 3, align='L',
             tracking=br.track)
    art.mark(br.mark, W - H * 0.42, H * 0.5, H * 0.5, br.bg, 2)


def _lay_repeat(art, br, k):
    """long board: the logo repeats along it, but never at the same size"""
    W, H = art.W, art.H
    art.rect(0, 0, W, H, br.bg, 0)
    nrep = max(2, int(W / rnd(2.6, 4.4, k, 5)))
    for r in range(nrep):
        cu = W * (r + 0.5) / nrep
        h = H * rnd(0.34, 0.46, k, 6, r)
        w = art.text_width(br.name, h, br.track)
        if w > W / nrep * 0.86:
            h *= (W / nrep * 0.86) / w
        art.text(br.name, cu, H * 0.5 - h * 0.40, h, br.fg, 2, tracking=br.track)
    art.rect(0, H * 0.03, W, H * 0.06, br.fg, 1)


def _lay_strap(art, br, k):
    W, H = art.W, art.H
    art.rect(0, 0, W, H, br.bg, 0)
    h = H * 0.40
    w = art.text_width(br.name, h, br.track)
    if w > W * 0.72:
        h *= W * 0.72 / w
    art.text(br.name, W * 0.5, H * 0.52, h, br.fg, 2, tracking=br.track)
    art.rect(W * 0.5 - w * 0.5, H * 0.44, W * 0.5 + w * 0.5, H * 0.475, br.fg, 1)
    art.text(br.strap, W * 0.5, H * 0.20, H * 0.17, br.fg, 2,
             tracking=br.track * 2.4)


def _lay_chequer(art, br, k):
    W, H = art.W, art.H
    art.rect(0, 0, W, H, br.bg, 0)
    cq = H * 0.13
    ncq = int(W / cq)
    for i in range(ncq):
        for j in range(2):
            if (i + j) % 2:
                art.rect(i * cq, H - (j + 1) * cq, (i + 1) * cq, H - j * cq,
                         br.fg, 1)
    h = (H - 2 * cq) * 0.62
    w = art.text_width(br.name, h, br.track)
    if w > W * 0.80:
        h *= W * 0.80 / w
    art.text(br.name, W * 0.5, (H - 2 * cq) * 0.5 - h * 0.40, h, br.fg, 2,
             tracking=br.track)


def _lay_reverse(art, br, k):
    W, H = art.W, art.H
    art.rect(0, 0, W, H, br.fg, 0)
    art.rect(W * 0.02, H * 0.06, W * 0.98, H * 0.94, br.bg, 1)
    # a ghost mark, deliberately bled off the top and bottom and then clipped
    art.mark(br.mark, W * rnd(0.16, 0.84, k, 12), H * 0.5, H * 1.15,
             tint(br.fg, 0.0, k) if False else
             tuple(0.5 * (a + b) for a, b in zip(br.fg, br.bg)), 2)
    h = H * 0.40
    w = art.text_width(br.name, h, br.track)
    if w > W * 0.78:
        h *= W * 0.78 / w
    art.text(br.name, W * 0.5, H * 0.5 - h * 0.40, h, br.fg, 4, tracking=br.track)


def _lay_bigmark(art, br, k):
    W, H = art.W, art.H
    art.rect(0, 0, W, H, br.bg, 0)
    art.mark(br.mark, W * 0.80, H * 0.52, H * 0.86, br.fg, 2)
    h = H * 0.30
    w = art.text_width(br.name, h, br.track)
    if w > W * 0.60:
        h *= W * 0.60 / w
    art.text(br.name, W * 0.05, H * 0.30, h, br.fg, 3, align='L',
             tracking=br.track)
    hs = H * 0.13
    ws = art.text_width(br.strap, hs, br.track * 2.2)
    if ws > W * 0.58:
        hs *= W * 0.58 / ws
    art.text(br.strap, W * 0.05, H * 0.13, hs, br.fg, 3, align='L',
             tracking=br.track * 2.2)


def _lay_stripe(art, br, k):
    W, H = art.W, art.H
    art.rect(0, 0, W, H, br.fg, 0)
    nst = rint(3, 6, k, 7)
    for i in range(nst):
        v0 = H * (0.06 + 0.10 * i)
        art.fan([(0, v0), (W, v0 + H * rnd(-0.05, 0.05, k, 8, i)),
                 (W, v0 + H * 0.055), (0, v0 + H * 0.055)], br.bg, 1)
    h = H * 0.36
    art.text(br.name, W * 0.5, H * 0.62, h, br.bg, 2, tracking=br.track)


def _lay_house(art, br, k):
    """circuit house board — the circuit advertises itself"""
    W, H = art.W, art.H
    art.rect(0, 0, W, H, br.bg, 0)
    art.rect(0, H * 0.88, W, H, srgb('#b8352a'), 1)
    art.rect(0, 0, W, H * 0.06, srgb('#b8352a'), 1)
    h = H * 0.40
    w = art.text_width("CIRCUIT VITRINE", h, 0.22)
    if w > W * 0.82:
        h *= W * 0.82 / w
    art.text("CIRCUIT VITRINE", W * 0.5, H * 0.42, h, br.fg, 2, tracking=0.22)
    art.text(pick(["3 675 m  ·  15 VIRAGES", "TOUR RECORD 63.5 s",
                   "GRAND PRIX", "LE CIRCUIT"], k, 9),
             W * 0.5, H * 0.20, H * 0.15, br.fg, 2, tracking=0.30)


LAYOUTS = [_lay_fullbleed, _lay_mark_left, _lay_band, _lay_diag, _lay_repeat,
           _lay_strap, _lay_chequer, _lay_reverse, _lay_bigmark, _lay_stripe]


def paint_board(W, H, br, k, layout=None):
    art = Art(W, H)
    if br.i == HOUSE:
        _lay_house(art, br, k)
        return art
    if layout is None:
        ar = W / max(H, 1e-6)
        pool = list(range(len(LAYOUTS)))
        if ar > 5.5:                    # long thin board: repeat or band
            pool = [4, 4, 2, 0, 5, 9]
        elif ar < 2.2:                  # tall board: mark-led
            pool = [8, 1, 7, 2, 5]
        layout = pick(pool, k, 11)
    LAYOUTS[layout](art, br, k)
    return art


# --------------------------------------------------------------------------- #
#  8.  board surfaces + the physical board families                             #
# --------------------------------------------------------------------------- #

def _subdiv(V, F, maxlen):
    """4-split every triangle whose longest edge exceeds maxlen (<=4 passes)."""
    V = list(map(tuple, V))
    F = [tuple(f) for f in F]
    for _ in range(4):
        need = False
        mid = {}
        out = []

        def _m(a, b):
            key = (a, b) if a < b else (b, a)
            if key not in mid:
                mid[key] = len(V)
                V.append(((V[a][0] + V[b][0]) * 0.5, (V[a][1] + V[b][1]) * 0.5))
            return mid[key]

        for (a, b, c) in F:
            pa, pb, pc = V[a], V[b], V[c]
            e = max(math.hypot(pb[0] - pa[0], pb[1] - pa[1]),
                    math.hypot(pc[0] - pb[0], pc[1] - pb[1]),
                    math.hypot(pa[0] - pc[0], pa[1] - pc[1]))
            if e <= maxlen:
                out.append((a, b, c))
                continue
            need = True
            ab, bc, ca = _m(a, b), _m(b, c), _m(c, a)
            out.extend([(a, ab, ca), (ab, b, bc), (ca, bc, c), (ab, bc, ca)])
        F = out
        if not need:
            break
    return np.array(V, float), np.array(F, np.int64)


# THE PRINT IS INK, NOT RELIEF.
#
# `emit_art` stacks the artwork in layers so a logotype covers its background.
# The old code pushed each layer 1.6 mm along the panel's LOCAL +y and scaled
# that by `out`, which on a fence banner (out = 1.8) put every glyph 2.9 mm
# proud of the cloth.  At a 12.47 deg sun that is a 13 mm cast shadow under
# every letter: the macro render read as embossed plastic plates, not print.
#
# Two changes.  The step is now 0.40 mm for a rigid laminate and 0.16 mm for
# cloth — both smaller than the substrate's own bump — and it is applied along
# the SURFACE NORMAL rather than along local +y.  Offsetting along a fixed axis
# is what forced the wrinkles to stay at ~1 m wavelengths: on a steep fold the
# layers slid sideways relative to each other and crossed.  A normal offset
# cannot cross as long as it is small against the radius of curvature, which at
# 0.16 mm against a 0.15 m fold radius is a factor of a thousand.

# THE PRINT IS INK, NOT RELIEF — and why the layer step is DERIVED, not chosen.
#
# `emit_art` stacks the artwork: a full-bleed background, then shapes, then text.
# Each layer is tessellated INDEPENDENTLY, so each is a DIFFERENT piecewise-linear
# approximation of the same curved surface.  A chord across a triangle of edge L
# on a surface of radius R sags below it by L^2 / 8R, so unless the layer step
# exceeds that sag the background pokes through the glyphs.
#
# Measured, the hard way: the first rebuilt banner had 65 mm triangles on wrinkles
# with R = 0.15 m, which is 3.5 mm of sag against a 0.16 mm step, and every letter
# came back with bites out of it.  The ORIGINAL code hid the same problem by
# pushing the layers 2.9 mm apart — which is why the print read as embossed
# plastic plates at macro, and why the wrinkles had to stay at ~1 m wavelengths.
# One defect, two symptoms.
#
# So the step is computed from the tessellation and the surface's own worst
# curvature instead of being a constant:
#
#       step = max(LAYER_STEP_MIN, SAG_SAFETY * L^2 / (8 R_min))
#
# and the geometry is kept to curvatures a sane tessellation can carry: the
# gross cloth shape (sag, billow, scallops, folds) is >= R 1.2 m, and the fine
# 5-20 mm creases that make cloth read as cloth are carried by the SHADER's
# bump, which resolves at any distance for no vertex cost at all.
#
#   cloth, hero:   L 0.045, R 1.2  ->  sag 0.21 mm, step 0.40 mm  (1.9x)
#   rigid, hero:   L 0.120, R 5.0  ->  sag 0.36 mm, step 0.47 mm  (1.3x)
#   rigid, far:    L 0.300, R 5.0  ->  sag 2.25 mm, step 2.93 mm  (invisible at
#                                                                  the distance)

LAYER_STEP_MIN = 0.00040        # printed vinyl really is about this thick
SAG_SAFETY = 1.30
CLOTH_RMIN = 1.20               # gross cloth shape, creases live in the shader
BOARD_RMIN = 5.00               # panel bow and impact dents


def layer_step(maxlen, rmin):
    """Vertical separation the art layers need at this tessellation."""
    return max(LAYER_STEP_MIN, SAG_SAFETY * maxlen * maxlen / (8.0 * rmin))


def with_normal_offset(f, du=0.006, dv=0.006):
    """Wrap a (U, V, off) surface so `off` runs along its own normal.

    Offsetting along a fixed local axis (which is what the original did) forces
    the layers to slide sideways relative to each other wherever the surface is
    steep, so it needs a step proportional to the slope.  Along the normal the
    layers are parallel surfaces and only the chord sag above matters.
    """
    def g(U, V, off=0.0):
        P = f(U, V, 0.0)
        o = float(off)
        if abs(o) < 1e-12:
            return P
        d = f(U, V, 1.0) - P                      # the surface's own +off axis
        Pu = f(U + du, V, 0.0) - f(U - du, V, 0.0)
        Pv = f(U, V + dv, 0.0) - f(U, V - dv, 0.0)
        n = np.cross(Pu, Pv)
        L = np.linalg.norm(n, axis=-1, keepdims=True)
        n = np.where(L > 1e-12, n / np.maximum(L, 1e-12), d)
        sgn = np.sign(np.sum(n * d, axis=-1, keepdims=True))
        sgn = np.where(sgn == 0.0, 1.0, sgn)
        return P + n * sgn * o
    return g


def board_surface(W, H, k, bow=0.0, dents=(), fabric=False, sag=0.0,
                  billow=0.0, twist=0.0, ties=(), tear=None, fold=None):
    """(U in 0..W, V in 0..H, out) -> local (x, y, z), x across, y out, z up.

    `out` is along the surface normal (see `with_normal_offset`).

    FABRIC.  A hung banner is not a sagging rectangle.  It is a sheet carrying
    load into a handful of grommets, and everything the eye recognises about one
    comes from that: the top edge scallops between ties, creases fan downward
    and outward from every tie, the storage fold sits where it was folded, and
    the bottom edge is heavier than the middle.  `ties` is the list of grommet
    U positions, so the geometry and the mounting hardware cannot disagree.
    """
    dl = list(dents)
    tu = np.asarray(ties, float) if len(ties) else np.zeros(0)

    def base(U, V, off=0.0):
        U = np.asarray(U, float)
        V = np.asarray(V, float)
        u = U / max(W, 1e-9)
        v = V / max(H, 1e-9)
        x = W * 0.5 - U
        z = np.array(V, float)
        y = np.full(U.shape, float(off))
        if bow:
            y = y + bow * (1.0 - 4.0 * (u - 0.5) ** 2)
        for (du_, dv_, dd, rr) in dl:
            y = y - dd * np.exp(-(((U - du_) ** 2 + (V - dv_) ** 2) / (rr * rr)))
        if fabric:
            # 1. gross shape: the bottom sags and the belly billows
            z = z - sag * np.sin(np.pi * np.clip(u, 0, 1)) * \
                np.maximum(0.0, 1.0 - v) ** 1.3
            y = y + billow * np.sin(np.pi * np.clip(u, 0, 1)) * \
                np.sin(math.pi * 0.5 + 1.2 * np.pi * v) * 0.7
            # 2. the top edge SCALLOPS between grommets, and the scallop hangs
            #    down into the sheet, dying out about a tie-spacing below
            if tu.size >= 2:
                pitch = float(np.mean(np.diff(tu))) if tu.size > 1 else W
                t = np.clip((U[..., None] - tu[None, :]) / max(pitch, 0.15),
                            -1.0, 1.0)
                bay = np.cos(np.pi * t) * 0.5 + 0.5          # 1 at a tie
                near = np.max(bay, axis=-1)
                drop = (1.0 - near) * (0.006 + 0.012 * hash01(k, 771))
                z = z - drop * np.clip(v - 0.25, 0, 1) ** 1.6 / 0.75
            # 3. CREASES fanning down and out from every grommet.  In GEOMETRY
            #    they are kept to wavelengths the art tessellation can carry
            #    (R >= 1.2 m); the 5-20 mm creases that make cloth read as cloth
            #    are the SHADER's, where they cost nothing and resolve at any
            #    distance.
            if tu.size:
                dxs = U[..., None] - tu[None, :]
                dys = (H - V)[..., None] + 0.06
                r = np.hypot(dxs, dys)
                ang = np.arctan2(dxs, dys)
                ph = (hash01(k, 772) * 6.283 +
                      np.arange(tu.size)[None, :] * 2.399)
                amp = 0.010 + 0.014 * hash01(k, 773)
                cr = (amp * np.exp(-r / 0.85) *
                      np.sin(2.3 * ang + ph) *
                      np.clip((r - 0.10) / 0.30, 0.0, 1.0))
                y = y + np.sum(cr, axis=-1)
            # 4. the storage fold: banners live folded in a crate
            if fold is not None:
                for (fv, fa) in fold:
                    y = y + fa * np.exp(-((v - fv) / 0.075) ** 2)
            # 5. the hem-weighted bottom edge, and a slack ripple across it
            y = y + 0.010 * np.sin(u * 3.2 + k * 6.0) * np.clip(1.0 - v * 2.2,
                                                               0, 1)
            z = z - 0.004 * np.clip(1.0 - v * 3.0, 0, 1)
            # 6. a torn-out grommet: the cloth lets go and that corner droops
            if tear is not None:
                (tx, ta) = tear
                d2 = np.hypot(U - tx, (H - V) * 0.65)
                w2 = np.exp(-(d2 / 0.85) ** 2)
                z = z - ta * w2 * np.clip(v - 0.15, 0, 1)
                y = y + ta * 0.45 * w2
        if twist:
            th = twist * (u - 0.5)
            xr = x * np.cos(th) - y * np.sin(th)
            y = x * np.sin(th) + y * np.cos(th)
            x = xr
        return np.stack([x, y, z], axis=-1)

    return with_normal_offset(base)


def _clip_tris(V, F, W, H):
    """Sutherland-Hodgman every triangle against the board rectangle, so no
    artwork can ever escape the panel it is printed on."""
    planes = ((1.0, 0.0, 0.0), (-1.0, 0.0, W), (0.0, 1.0, 0.0), (0.0, -1.0, H))
    OV, OF = [], []
    for tri in F:
        poly = [tuple(V[i]) for i in tri]
        for (a, b, c) in planes:
            if not poly:
                break
            out = []
            n = len(poly)
            for i in range(n):
                p, q = poly[i], poly[(i + 1) % n]
                dp = a * p[0] + b * p[1] + c
                dq = a * q[0] + b * q[1] + c
                if dp >= 0:
                    out.append(p)
                if (dp > 0) != (dq > 0):
                    t = dp / (dp - dq)
                    out.append((p[0] + (q[0] - p[0]) * t,
                                p[1] + (q[1] - p[1]) * t))
            poly = out
        if len(poly) < 3:
            continue
        i0 = len(OV)
        OV.extend(poly)
        for i in range(1, len(poly) - 1):
            OF.append((i0, i0 + i, i0 + i + 1))
    if not OF:
        return np.zeros((0, 2)), np.zeros((0, 3), np.int64)
    return np.array(OV, float), np.array(OF, np.int64)


def emit_art(mb, art, surf, aux, mat=M_PRINT, maxlen=0.45, out=1.0, clip=True,
             rmin=BOARD_RMIN):
    for (V, F, col, layer) in art.items:
        if len(V) == 0 or len(F) == 0:
            continue
        if clip and (V[:, 0].min() < -1e-6 or V[:, 0].max() > art.W + 1e-6 or
                     V[:, 1].min() < -1e-6 or V[:, 1].max() > art.H + 1e-6):
            V, F = _clip_tris(V, F, art.W, art.H)
            if len(F) == 0:
                continue
        span = max(V[:, 0].max() - V[:, 0].min(), V[:, 1].max() - V[:, 1].min())
        if span > maxlen:
            V, F = _subdiv(V, F, maxlen)
        P = surf(V[:, 0], V[:, 1], layer * layer_step(maxlen, rmin) * out)
        uv = np.column_stack([V[:, 0] / max(art.W, 1e-6),
                              V[:, 1] / max(art.H, 1e-6)])
        mb.add(P, F, mat, uv=uv, base=(col[0], col[1], col[2], 1.0), aux=aux,
               smooth=True)


def panel_body(mb, surf, W, H, thick, aux, back=(0.10, 0.105, 0.11, 1),
               nu=None, nv=None, mat_back=M_PRINT, rim=True, u0=0.0, u1=None,
               v0=0.0, v1=None):
    """back plate + folded rim for a rigid printed board (or one panel of it)."""
    u1 = W if u1 is None else u1
    v1 = H if v1 is None else v1
    nu = nu or max(3, int((u1 - u0) / 0.55) + 1)
    nv = nv or max(3, int((v1 - v0) / 0.45) + 1)
    U = np.linspace(u0, u1, nu)
    V = np.linspace(v0, v1, nv)
    UU, VV = np.meshgrid(U, V, indexing='ij')
    Pb = surf(UU.ravel(), VV.ravel(), -thick).reshape(nu, nv, 3)
    uv = np.stack([UU / max(W, 1e-9), VV / max(H, 1e-9)], -1)
    # reverse winding so the back faces away from the track
    i = (np.arange(nu - 1)[:, None] * nv + np.arange(nv - 1)[None, :])
    q = np.stack([i, i + 1, i + nv + 1, i + nv], axis=-1).reshape(-1, 4)
    mb.add(Pb.reshape(-1, 3), q, mat_back, uv=uv.reshape(-1, 2), base=back,
           aux=aux)
    if not rim:
        return
    for (Ua, Va) in ((np.linspace(u0, u1, nu), np.full(nu, v0)),
                     (np.linspace(u0, u1, nu), np.full(nu, v1)),
                     (np.full(nv, u0), np.linspace(v0, v1, nv)),
                     (np.full(nv, u1), np.linspace(v0, v1, nv))):
        A = surf(Ua, Va, 0.0)
        B = surf(Ua, Va, -thick)
        n = len(A)
        P = np.vstack([A, B])
        ii = np.arange(n - 1)
        q = np.stack([ii, ii + n, ii + n + 1, ii + 1], -1)
        mb.add(P, q, mat_back, base=back, aux=aux)
        mb.add(P, q[:, ::-1], mat_back, base=back, aux=aux)


def chord_frame(s0, s1, side, lat0, lat1=None, dz=0.0, tilt=True, name=None):
    """local frame for a flat panel spanning stations s0..s1 at lateral `lat`.

    `tilt=True` rolls the panel's x-axis onto the line the GROUND takes between
    its two ends.  A board bolted to an Armco follows the Armco, and the Armco
    follows `ground_z`; a level board on a 3.5 % grade opens a wedge under itself
    of 0.035 * W, which is 160 mm on a 4.6 m advertising panel and was there in
    every one of the 584 of them.  Free-standing hoardings pass `tilt=False`:
    they are built level and their legs are cut to length, which is what a real
    one is.
    """
    lat1 = lat0 if lat1 is None else lat1
    x0, y0, z0 = station_world(s0, lat0, side)
    x1, y1, z1 = station_world(s1, lat1, side)
    x0, y0, z0 = float(x0), float(y0), float(z0)
    x1, y1, z1 = float(x1), float(y1), float(z1)
    d = np.array([x1 - x0, y1 - y0, (z1 - z0) if tilt else 0.0])
    W = float(np.linalg.norm(d))
    if W < 1e-6:
        return None, None, 0.0
    ex = (-side) * d / W
    ez = np.array([0.0, 0.0, 1.0]) - ex * float(ex[2])
    n = float(np.linalg.norm(ez))
    ez = ez / n if n > 1e-9 else np.array([0.0, 0.0, 1.0])
    ey = np.cross(ez, ex)
    R = np.column_stack([ex, ey, ez])
    O = np.array([(x0 + x1) * 0.5, (y0 + y1) * 0.5, (z0 + z1) * 0.5 + float(dz)])
    if name:
        # the ANCHOR is the ground under the panel's mid STATION, not the chord
        # midpoint: on a 150 m radius the chord's centre is 18 mm inboard of the
        # arc, and asking `world_ground_z` there measures the sagitta rather
        # than the module's conformance.
        sm = 0.5 * (float(s0) + float(s1))
        lm = 0.5 * (float(lat0) + float(lat1))
        ax, ay, az = station_world(sm, lm, side)
        ANCHORS.append(dict(n=name, p=(float(ax), float(ay), float(az)),
                            s=sm, u=lm * side, side=int(side)))
    return R, O, W


def board_aux(age, dirt, k, variant=0.5):
    return (float(age), float(dirt), float(variant), float(k))


# ---- family 1: barrier-face board -----------------------------------------

def build_barrier_board(mb, s0, s1, side, bi, k, tier):
    """the classic Armco-face board.  Returns a signature tuple."""
    sm = 0.5 * (s0 + s1)
    ml_ = [mount_lat(x, side) for x in (s0, s1, sm)]
    if any(v is None for v in ml_):
        return None
    lat = fit_lat(sm, side, min(ml_))
    R, O, W = chord_frame(s0, s1, side, lat,
                          name="board@%.1f/%+d" % (sm, side))
    if R is None or W < 1.0:
        return None
    br = Brand(bi)
    # Event advertising is PRINTED FOR THE WEEKEND: most boards are new, a
    # minority are the permanent local advertisers that have been up for years.
    # Uniform ageing made a race weekend look like a derelict circuit.
    age = 0.04 + 0.80 * hash01(k, 21) ** 3.0
    dirt = clamp01(rnd(0.35, 1.0, k, 22) * (0.7 + 0.5 * hash01(k, 23)))
    H = rnd(0.62, 1.00, k, 24)
    z0 = rnd(0.02, 0.09, k, 25)
    thick = rnd(0.010, 0.020, k, 26)
    bow = rnd(-0.012, 0.022, k, 27)
    lean = rnd(-1.2, 2.6, k, 28) if chance(0.22, k, 29) else 0.0
    dents = []
    nd = 0
    if chance(0.20 + 0.10 * (tier >= 2), k, 30):
        nd = rint(1, 2, k, 31)
        for d in range(nd):
            # depth/radius kept to R = r^2/2d >= 5 m so the art tessellation
            # can carry the dent without the layers stitching through it
            dr_ = rnd(0.42, 0.95, k, 35, d)
            dents.append((rnd(0.15, 0.85, k, 32, d) * W,
                          rnd(0.15, 0.75, k, 33, d) * H,
                          min(rnd(0.006, 0.020, k, 34, d), dr_ * dr_ / 10.0),
                          dr_))
    ml = 0.12 if tier >= 2 else 0.30
    surf = board_surface(W, H, k, bow=bow, dents=dents)
    art = paint_board(W, H, br, k)
    Rl = R @ pitchX(lean) if lean else R
    lo = Local(mb, Rl, O + np.array([0.0, 0.0, z0]))
    aux = board_aux(age, dirt, hash01(k, 36))
    emit_art(lo, art, surf, aux, maxlen=ml)
    panel_body(lo, surf, W, H, thick, aux,
               back=(0.085, 0.088, 0.092, 1),
               nu=max(3, int(W / (0.5 if tier >= 2 else 0.9)) + 1),
               nv=max(3, int(H / 0.4) + 1))
    # mounting: vertical straps clamped to the W-beam + bolt heads
    nstr = max(2, int(round(W / rnd(1.5, 2.4, k, 37))))
    sage = (min(1.0, age + 0.15), dirt, rnd(0.15, 0.85, k, 38), hash01(k, 39))
    for j in range(nstr):
        u = W * (j + 0.5) / nstr
        x = W * 0.5 - u
        wd = rnd(0.035, 0.055, k, 40, j)
        lo.box((x - wd, -thick - 0.012, H * 0.10),
               (x + wd, -thick - 0.002, H * 0.92), M_STEEL,
               base=(0.5, 0.5, 0.5, 0.0), aux=sage)
        for zz in (H * 0.18, H * 0.80):
            # hex head + washer, not a flat disc
            lo.cyl((x, -thick - 0.014, zz), (x, 0.0035, zz), 0.008, M_STEEL,
                   base=(0.5, 0.5, 0.5, 0.0), aux=sage, n=6)
            lo.cyl((x, 0.0035, zz), (x, 0.0085, zz), 0.0115, M_STEEL,
                   base=(0.5, 0.5, 0.5, 0.0), aux=sage, n=6,
                   phase=hash01(k, 41, j) * 1.0)
            lo.cyl((x, 0.0015, zz), (x, 0.0035, zz), 0.016, M_STEEL,
                   base=(0.5, 0.5, 0.5, 0.0), aux=sage, n=12)
    return ("bar", br.name, round(W, 2), round(H, 2), round(age, 3), nd,
            round(bow, 4), round(lean, 2))


# ---- family 2: fence banner ------------------------------------------------
#
# The review's verdict on this family was "a flat colour fill with no fabric,
# wrinkles, grommets, print texture or sun-fade".  All five were true.  What a
# hung banner actually is, from the outside in:
#
#   a printed PVC-coated polyester sheet, hemmed 35 mm all round with the hem
#   folded to the back and stitched, brass eyelets punched through the hem at
#   roughly half-metre centres, cable-tied to the debris fence at most of them
#   but not all of them, creased where it was folded in its crate, scalloping
#   between its ties and fanning fine diagonal wrinkles down from each one.
#
# Every one of those is now geometry or shader, and the grommet positions are a
# single list shared by the surface function, the eyelets and the ties, so the
# wrinkles radiate from the holes the ties actually go through.

BANNER_HEM_M = 0.035               # folded hem depth
BANNER_EYELET_R0 = 0.0038          # brass eyelet bore
BANNER_EYELET_R1 = 0.0072          # eyelet flange
BRASS = (0.42, 0.28, 0.10, 1)


def banner_ties(W, k, pitch=None):
    """grommet U positions along an edge: both corners, then even centres."""
    pitch = pitch if pitch is not None else rnd(0.42, 0.72, k, 760)
    inset = BANNER_HEM_M * 0.5 + 0.010
    span = max(W - 2.0 * inset, 0.05)
    n = max(2, int(round(span / pitch)) + 1)
    return [inset + span * j / (n - 1) for j in range(n)], n


def _cloth_ring(lo, surf, u, v, r0, r1, off, mat, base, aux, n=12):
    th = np.linspace(0.0, 2.0 * math.pi, n, endpoint=False)
    A = surf(u + r0 * np.cos(th), v + r0 * np.sin(th), off)
    B = surf(u + r1 * np.cos(th), v + r1 * np.sin(th), off)
    P = np.vstack([A, B])
    i = np.arange(n)
    j = (i + 1) % n
    q = np.stack([i, j, j + n, i + n], -1)
    lo.add(P, q, mat, base=base, aux=aux)
    lo.add(P, q[:, ::-1], mat, base=base, aux=aux)
    return A


def eyelet(lo, surf, u, v, aux, n=12, front=0.0009, back=-0.0042):
    """a brass eyelet set through the cloth: flange, flange, barrel, bore."""
    A = _cloth_ring(lo, surf, u, v, BANNER_EYELET_R0, BANNER_EYELET_R1, front,
                    M_ALU, BRASS, aux, n)
    Bk = _cloth_ring(lo, surf, u, v, BANNER_EYELET_R0, BANNER_EYELET_R1 * 0.92,
                     back, M_ALU, BRASS, aux, n)
    P = np.vstack([A, Bk])
    i = np.arange(n)
    j = (i + 1) % n
    q = np.stack([i, j, j + n, i + n], -1)
    lo.add(P, q[:, ::-1], M_ALU, base=BRASS, aux=aux)
    # the bore reads as a hole because it is in shadow behind the flange
    th = np.linspace(0.0, 2.0 * math.pi, n, endpoint=False)
    D = surf(u + BANNER_EYELET_R0 * 0.96 * np.cos(th),
             v + BANNER_EYELET_R0 * 0.96 * np.sin(th), back - 0.0006)
    ctr = surf(np.array([u]), np.array([v]), back - 0.0009)
    P2 = np.vstack([ctr, D])
    f = np.stack([np.zeros(n, int), 1 + i, 1 + j], -1)
    lo.add(P2, f, M_PLASTIC, base=(0.012, 0.011, 0.010, 1), aux=aux)


def _hem_strip(lo, surf, W, H, aux, back_col):
    """the folded-and-stitched hem, and the stitch line that shows on the face"""
    hw = BANNER_HEM_M
    edges = (
        (np.linspace(0.0, W, max(6, int(W / 0.10))), None, 0.0, hw),        # bottom
        (np.linspace(0.0, W, max(6, int(W / 0.10))), None, H, -hw),         # top
        (None, np.linspace(0.0, H, max(6, int(H / 0.10))), 0.0, hw),        # left
        (None, np.linspace(0.0, H, max(6, int(H / 0.10))), W, -hw),         # right
    )
    for (Uax, Vax, at, dep) in edges:
        if Uax is not None:
            Ua, Va0, Va1 = Uax, np.full(len(Uax), at), np.full(len(Uax), at + dep)
        else:
            Ua, Va0, Va1 = None, None, None
            Va = Vax
            Ua0, Ua1 = np.full(len(Va), at), np.full(len(Va), at + dep)
        if Uax is not None:
            A = surf(Ua, Va0, -0.0016)
            B = surf(Ua, Va1, -0.0034)
            Sa = surf(Ua, Va1, 0.0007)
            Sb = surf(Ua, Va1 + (0.0025 if dep > 0 else -0.0025), 0.0007)
        else:
            A = surf(Ua0, Va, -0.0016)
            B = surf(Ua1, Va, -0.0034)
            Sa = surf(Ua1, Va, 0.0007)
            Sb = surf(Ua1 + (0.0025 if dep > 0 else -0.0025), Va, 0.0007)
        n = len(A)
        P = np.vstack([A, B])
        i = np.arange(n - 1)
        q = np.stack([i, i + n, i + n + 1, i + 1], -1)
        lo.add(P, q, M_FABRIC, base=back_col, aux=aux)
        lo.add(P, q[:, ::-1], M_FABRIC, base=back_col, aux=aux)
        # stitching: one continuous 2.5 mm thread strip, not 800 stitches
        P2 = np.vstack([Sa, Sb])
        lo.add(P2, np.stack([i, i + 1, i + n + 1, i + n], -1), M_FABRIC,
               base=(0.055, 0.052, 0.048, 1), aux=(aux[0], 0.5, 0.2, aux[3]))


def build_fence_banner(mb, s0, s1, side, bi, k, tier):
    sm = 0.5 * (s0 + s1)
    # a banner hangs on the debris fence ABOVE the rail, so it stands off the
    # fence mesh rather than the beam
    if not (barrier_ok(s0, side) and barrier_ok(s1, side)):
        return None
    lat = fit_lat(sm, side, min(float(barrier_face(s0, side)),
                                float(barrier_face(s1, side)))
                  + BANNER_MOUNT_M)
    R, O, W = chord_frame(s0, s1, side, lat,
                          name="banner@%.1f/%+d" % (sm, side))
    if R is None or W < 1.5:
        return None
    br = Brand(bi)
    H = rnd(0.95, 2.15, k, 41)
    z0 = ARMCO_TOP + rnd(0.06, 0.30, k, 42)
    age = 0.04 + 0.58 * hash01(k, 43) ** 2.8
    dirt = clamp01(rnd(0.25, 0.85, k, 44))
    sag = rnd(0.02, 0.13, k, 45)
    # the backward billow is capped: the fence mesh is only 43 mm behind the
    # cloth at p05 and a banner that bows into it is a defect, not slack
    billow = (rnd(0.02, 0.13, k, 46) if chance(0.6, k, 47)
              else -rnd(0.006, 0.020, k, 46))
    mesh_banner = chance(0.45, k, 764)          # perforated mesh vs solid PVC
    ties, nt = banner_ties(W, k)
    bties, _nb = banner_ties(W, k + 0.31,
                             pitch=rnd(0.55, 1.05, k, 765))
    # the storage folds: where it was folded in its crate, as height fractions
    nf = rint(1, 3, k, 766)
    fold = [(rnd(0.18, 0.86, k, 767, j), rnd(-0.006, 0.006, k, 768, j))
            for j in range(nf)]
    # one banner in eight has torn out a grommet and is hanging off that corner
    tear = None
    if chance(0.13, k, 769) and nt >= 3:
        ti = rint(0, nt - 1, k, 770)
        tear = (ties[ti], rnd(0.05, 0.16, k, 771))
        ties = [t for j, t in enumerate(ties) if j != ti]
    ml = 0.045 if tier >= 2 else 0.085
    surf = board_surface(W, H, hash01(k, 48), fabric=True, sag=sag,
                         billow=billow, ties=ties, tear=tear, fold=fold)
    art = paint_board(W, H, br, k + 0.5)
    lo = Local(mb, R, O + np.array([0.0, 0.0, z0]))
    aux = board_aux(age, dirt, 0.75 if mesh_banner else 0.25)
    emit_art(lo, art, surf, aux, mat=M_FABRIC, maxlen=ml, out=1.0,
             rmin=CLOTH_RMIN)
    # back side of the cloth (banners are printed one side, grey behind)
    back_col = (0.285, 0.288, 0.282, 1)
    nu = max(4, int(W / ml) + 1)
    nv = max(4, int(H / ml) + 1)
    U = np.linspace(0, W, nu)
    V = np.linspace(0, H, nv)
    UU, VV = np.meshgrid(U, V, indexing='ij')
    P = surf(UU.ravel(), VV.ravel(), -0.0012).reshape(nu, nv, 3)
    i = (np.arange(nu - 1)[:, None] * nv + np.arange(nv - 1)[None, :])
    q = np.stack([i, i + 1, i + nv + 1, i + nv], axis=-1).reshape(-1, 4)
    lo.add(P.reshape(-1, 3), q, M_FABRIC,
           uv=np.stack([UU / W, VV / H], -1).reshape(-1, 2),
           base=back_col, aux=aux, smooth=True)
    _hem_strip(lo, surf, W, H, aux, back_col)
    # eyelets: every tie on the top, fewer along the bottom, one per side
    hin = BANNER_HEM_M * 0.5
    for u in ties:
        eyelet(lo, surf, u, H - hin, aux)
    for u in bties:
        eyelet(lo, surf, u, hin, aux)
    for v in (H * 0.5,):
        eyelet(lo, surf, hin, v, aux)
        eyelet(lo, surf, W - hin, v, aux)
    if tear is not None:
        # the torn hole itself: a ragged crescent where the brass pulled out
        tu = tear[0]
        th = np.linspace(0.4, 2.4, 9)
        rr = 0.011 + 0.004 * np.sin(th * 5.0 + k)
        A = surf(tu + rr * np.cos(th), H - hin + rr * np.sin(th), 0.0006)
        Bp = surf(np.full(9, tu), np.full(9, H - hin), 0.0006)
        lo.add(np.vstack([A, Bp]),
               np.stack([np.arange(8), np.arange(8) + 1,
                         np.arange(8) + 10, np.arange(8) + 9], -1),
               M_FABRIC, base=(0.12, 0.115, 0.108, 1), aux=aux)
    # cable ties: most grommets are tied, a couple are not.  A banner with two
    # ties undone and flapping is what a real one looks like on Sunday.
    for (j, u) in enumerate(ties):
        if chance(0.14, k, 50, j):
            continue
        pnt = surf(np.array([u]), np.array([H - hin]), 0.0)[0]
        lo.tube([[pnt[0], pnt[1] - 0.018, pnt[2] - 0.026],
                 [pnt[0], pnt[1] - 0.048, pnt[2] + 0.020],
                 [pnt[0], pnt[1] + 0.020, pnt[2] + 0.038],
                 [pnt[0], pnt[1] + 0.010, pnt[2] - 0.010]], 0.0030, M_PLASTIC,
                base=(0.02, 0.02, 0.02, 1), aux=(age, 0.3, 0.4, hash01(k, 51)),
                n=5, caps=False)
    return ("ban", br.name, round(W, 2), round(H, 2), round(age, 3),
            round(sag, 3), round(billow, 3), nt, len(fold),
            "mesh" if mesh_banner else "pvc", tear is not None)


# ---- family 3: free-standing billboard -------------------------------------

def build_billboard(mb, s, side, bi, k):
    if zone_cap(s, side) < 6.0:
        return None
    # a hoarding stands on its own footings BEHIND the barrier; 0.42 m of
    # concrete pad plus the raking brace's foot is its outboard extent
    lat = fit_behind(s, side, float(barrier_back(s, side)) +
                     rnd(1.4, 7.0, k, 60), foot=1.45, clear=1.20,
                     height=rnd(4.2, 6.4, k, 63) + 0.3,
                     halfspan=rnd(6.0, 13.5, k, 61) * 0.5)
    if lat is None:
        return None
    br = Brand(bi)
    W = rnd(6.0, 13.5, k, 61)
    H = rnd(2.4, 4.0, k, 62)
    ztop = rnd(4.2, 6.4, k, 63)
    z0 = ztop - H
    half = W * 0.5
    ds = half / max(1.0, 1.0)
    R, O, _w = chord_frame(s - half, s + half, side, lat, tilt=False,
                           name="billboard@%.1f/%+d" % (s, side))
    if R is None:
        return None
    yawd = rnd(-14.0, 14.0, k, 64)          # angled to face the braking car
    R = R @ yaw(yawd)
    age = 0.04 + 0.70 * hash01(k, 65) ** 2.8
    dirt = clamp01(rnd(0.15, 0.55, k, 66))
    npan = rint(2, 4, k, 67)
    lo = Local(mb, R, O)
    aux = board_aux(age, dirt, hash01(k, 68))
    thick = 0.028
    # ONE artwork across the whole hoarding, carried by a surface that knows
    # about the physical panel joints: each panel has its own bow and sits a
    # millimetre or two proud of its neighbour, so the joints read as joints
    # and the graphic still runs across them.
    pw = W / npan
    bows = [rnd(-0.020, 0.030, k, 69, p) for p in range(npan)]
    seat = [rnd(-0.004, 0.004, k, 77, p) for p in range(npan)]

    def _bsurf(U, V, off=0.0):
        U = np.asarray(U, float)
        V = np.asarray(V, float)
        pi_ = np.clip((U / pw).astype(int), 0, npan - 1)
        uu = (U - pi_ * pw) / pw
        bw = np.array(bows)[pi_]
        st = np.array(seat)[pi_]
        y = off + st + bw * (1.0 - 4.0 * (uu - 0.5) ** 2)
        # the 7 mm shadow gap at every joint
        gap = np.minimum(uu, 1.0 - uu) * pw
        y = y - 0.010 * np.exp(-(gap / 0.010) ** 2) * (pi_ > -1)
        return np.stack([W * 0.5 - U, y, V + z0], -1)

    bsurf = with_normal_offset(_bsurf)
    art = paint_board(W, H, br, k)
    emit_art(Local(lo, np.eye(3), np.zeros(3)), art, bsurf, aux, maxlen=0.22)
    for p in range(npan):
        panel_body(Local(lo, np.eye(3), np.zeros(3)), bsurf, W, H, thick, aux,
                   back=(0.09, 0.09, 0.09, 1), nu=max(3, int(pw / 0.6) + 1),
                   u0=p * pw + 0.005, u1=(p + 1) * pw - 0.005)
    # frame: posts, rails, braces, footings
    nleg = 2 if W < 9.0 else 3
    sage = (min(1.0, age + 0.2), 0.5, rnd(0.2, 0.9, k, 70), hash01(k, 71))
    for j in range(nleg):
        u = W * (0.16 + 0.68 * j / max(1, nleg - 1)) if nleg > 1 else W * 0.5
        x = W * 0.5 - u
        pw = rnd(0.075, 0.115, k, 72, j)
        lo.box((x - pw, -thick - 0.10 - pw, -0.35), (x + pw, -thick - 0.10 + pw,
                                                     z0 + H * 0.86), M_STEEL,
               base=(0.5, 0.5, 0.5, 0.0), aux=sage)
        lo.box((x - 0.42, -thick - 0.10 - 0.42, -0.34),
               (x + 0.42, -thick - 0.10 + 0.42, rnd(0.04, 0.14, k, 73, j)),
               M_CONC, base=(0.34, 0.335, 0.32, 1),
               aux=(min(1.0, age + 0.3), 0.6, 0.4, hash01(k, 74, j)))
        # diagonal brace to the ground
        lo.cyl((x, -thick - 0.10, z0 + H * 0.55),
               (x, -thick - 1.30, -0.15), 0.032, M_STEEL,
               base=(0.5, 0.5, 0.5, 0.0), aux=sage, n=8)
    for zr in (z0 + H * 0.12, z0 + H * 0.86):
        lo.box((-W * 0.5, -thick - 0.10, zr - 0.045),
               (W * 0.5, -thick - 0.02, zr + 0.045), M_STEEL,
               base=(0.5, 0.5, 0.5, 0.0), aux=sage)
    if chance(0.35, k, 75):                 # maintenance ladder
        x = W * 0.5 - W * rnd(0.20, 0.80, k, 76)
        for r in (-0.16, 0.16):
            lo.cyl((x + r, -thick - 0.34, -0.20), (x + r, -thick - 0.34, z0 + H * 0.5),
                   0.016, M_STEEL, base=(0.5, 0.5, 0.5, 0.0), aux=sage, n=6)
        nr = int((z0 + H * 0.5 + 0.2) / 0.30)
        for rr in range(nr):
            zz = -0.20 + 0.30 * (rr + 1)
            lo.cyl((x - 0.16, -thick - 0.34, zz), (x + 0.16, -thick - 0.34, zz),
                   0.012, M_STEEL, base=(0.5, 0.5, 0.5, 0.0), aux=sage, n=6)
    return ("big", br.name, round(W, 2), round(H, 2), npan, round(yawd, 1),
            round(age, 3))


# ---- family 4: apex / kerb-side low board ----------------------------------

def build_apex_board(mb, s, side, bi, k):
    # An apex board stands on the PLATFORM — sealed runoff or mown shoulder —
    # never in a gravel bed.  A gravel trap is a dished bed of loose stone; the
    # datum describes the platform it is cut into, not its floor, so a board
    # standing in one floated, measured at 250 mm on the assembled build.
    if not barrier_ok(s, side):
        return None
    rw = runoff_widths(s, side)
    e = float(verge_edge(s))
    apex, asph, grav = (float(rw["apex"]), float(rw["asphalt"]),
                        float(rw["gravel"]))
    lo_ = e + (apex + 0.80 if apex > 0.8 else 1.60)
    hi_ = float(barrier_offset(s, side)) - 1.20
    if grav > 0.5:                       # keep clear of the outer gravel bed
        hi_ = min(hi_, e + asph - 0.80)
    if hi_ < lo_:
        return None
    lat = lo_ + rnd(0.0, 1.0, k, 80) * min(hi_ - lo_, 7.0)
    lat = fit_lat(s, side, lat, foot=0.5)
    br = Brand(bi)
    W = rnd(2.8, 5.2, k, 81)
    H = rnd(0.55, 0.85, k, 82)
    R, O, _w = chord_frame(s - W * 0.5, s + W * 0.5, side, lat,
                           name="apexboard@%.1f/%+d" % (s, side))
    if R is None:
        return None
    R = R @ pitchX(rnd(6.0, 14.0, k, 83))
    age = rnd(0.20, 0.95, k, 84)
    dirt = clamp01(rnd(0.45, 1.0, k, 85))
    z0 = rnd(0.18, 0.34, k, 86)
    lo = Local(mb, R, O + np.array([0, 0, z0]))
    aux = board_aux(age, dirt, hash01(k, 87))
    surf = board_surface(W, H, k, bow=rnd(-0.01, 0.02, k, 88))
    emit_art(lo, paint_board(W, H, br, k + 0.25), surf, aux, maxlen=0.22)
    panel_body(lo, surf, W, H, 0.016, aux)
    sage = (min(1.0, age + 0.2), 0.7, 0.6, hash01(k, 89))
    for j in (-1, 1):
        x = j * W * rnd(0.28, 0.40, k, 90)
        lo.cyl((x, -0.05, 0.0), (x, -0.05, -z0 - 0.1), 0.030, M_STEEL,
               base=(0.5, 0.5, 0.5, 0.0), aux=sage, n=8)
        lo.cyl((x, -0.05, H * 0.4), (x, -0.42, -z0 - 0.05), 0.022, M_STEEL,
               base=(0.5, 0.5, 0.5, 0.0), aux=sage, n=6)
    return ("apx", br.name, round(W, 2), round(H, 2), round(age, 3))


# ---- family 5: bridge fascia banner ---------------------------------------
#
# Both of the circuit's overpasses are read from build_architecture.py's own
# numbers, so a banner sits ON the girder / truss face rather than floating.
#   La Passerelle    : circuit frame, x = -450, deck width 4.0, y -24..+28,
#                      soffit 7.50, truss depth 3.05
#   Le Pont de la P. : world frame, origin/heading/road level EVALUATED from
#                      `world_contract` at `build_architecture.PONT_S` (R2-731;
#                      it was three copied literals and R2-664 said what that
#                      costs), deck 6.0 wide, half-span 15.0, soffit +6.80,
#                      plate girders 1.35 m deep

def build_bridge_banner(mb, ctr, facing, W, H, bi, k, mat=M_PRINT, tilt=0.0):
    br = Brand(bi)
    R, O = frame_from_facing(ctr, facing)
    if tilt:
        R = R @ pitchX(tilt)
    lo = Local(mb, R, O)
    age = 0.05 + 0.55 * hash01(k, 600) ** 2.4
    aux = board_aux(age, rnd(0.15, 0.45, k, 601), hash01(k, 602))
    surf = board_surface(W, H, k, bow=rnd(-0.010, 0.020, k, 603))
    emit_art(lo, paint_board(W, H, br, k), surf, aux, mat=mat, maxlen=0.30)
    panel_body(lo, surf, W, H, 0.020, aux, back=(0.075, 0.078, 0.082, 1))
    sage = (min(1.0, age + 0.25), 0.6, 0.7, hash01(k, 604))
    nfx = max(3, int(W / 3.2))
    for j in range(nfx):
        x = W * 0.5 - W * (j + 0.5) / nfx
        for zz in (H * 0.14, H * 0.86):
            lo.cyl((x, -0.028, zz), (x, 0.006, zz), 0.011, M_STEEL,
                   base=(0.5, 0.5, 0.5, 0.0), aux=sage, n=6)
    return ("bridge", br.name, round(W, 2), round(H, 2), round(age, 3))


def bridge_banner_sites():
    """(world centre, facing, W, H) for every fascia a banner can hang on."""
    out = []
    # --- La Passerelle: circuit frame -------------------------------------
    X, Dw, soffit, dep = -450.0, 4.0, 7.50, 3.05
    for sx in (-1, 1):
        cx = X + sx * (Dw * 0.5 + 0.055)
        cy = 0.5 * (-20.0 + 24.0)
        wx, wy = CL.to_world(np.array([cx]), np.array([cy]))
        fx, fy = CL.to_world(np.array([cx + sx * 1.0]), np.array([cy]))
        out.append(((float(wx[0]), float(wy[0]), soffit + 0.62 + 0.80),
                    (float(fx[0] - wx[0]), float(fy[0] - wy[0])), 44.0, 1.60,
                    "passerelle"))
    # --- Le Pont de la Plongee: world frame -------------------------------
    #
    # R2-731 / R2-664.  DERIVED FROM THE BRIDGE'S OWN STATION, NOT COPIED.
    #
    # This used to read `hdg = math.radians(295.4)`, `ox, oy = -617.56, 94.75`,
    # `soff = 3.913 + 6.80` — three literals which are exactly
    # `WC.centreline(2410)` and `WC.elevation_c(2410)` + 6.80, i.e. a snapshot
    # of `build_architecture.PONT_S` taken by hand.  R2-664's occupancy proxy
    # found these banners in the beat-5 sightline corridor out to f2196, four
    # frames past the bridge's own window, and wrote down the consequence:
    # "any placement move must carry the banners with it; they are not part of
    # build_architecture's bridge and WILL NOT FOLLOW PONT_S on their own."
    # R2-660 then moved PONT_S 2410 -> 2460.  A copied literal would have left
    # four banners hanging in mid air 50 m short of the bridge, on the same
    # faces R2-256 already records a collision on.
    #
    # The import is deliberately NOT guarded.  A fallback here would mean this
    # module silently keeps building at a station the bridge no longer occupies,
    # which is the exact failure the block above describes; if
    # `build_architecture` cannot be imported, the banners must not be built at
    # all.
    import build_architecture as ARCH                            # noqa: E402
    px_, py_, _pz, phdg, _pk = C.centreline(ARCH.PONT_S)
    hdg = float(phdg)
    ox, oy = float(px_), float(py_)
    soff = float(C.elevation_c(ARCH.PONT_S)) + 6.80
    for sx in (-1, 1):
        lx = sx * (3.0 + 0.20)
        ly = 0.0
        wx = ox + lx * math.cos(hdg) - ly * math.sin(hdg)
        wy = oy + lx * math.sin(hdg) + ly * math.cos(hdg)
        fx = math.cos(hdg) * sx
        fy = math.sin(hdg) * sx
        out.append(((wx, wy, soff + 0.70), (fx, fy), 27.0, 1.15, "pont"))
    return out


# ---- family 6: flagpole ----------------------------------------------------

def build_flagpole(mb, wx, wy, wz, k, bi=None, height=None):
    h = height if height is not None else rnd(7.0, 11.0, k, 100)
    br = Brand(bi if bi is not None else brand_pick(k, 101))
    age = rnd(0.1, 0.7, k, 102)
    sage = (age, 0.3, 0.85, hash01(k, 103))
    lo = Local(mb, yaw(rnd(0, 360, k, 104)), np.array([wx, wy, wz]))
    lo.cyl((0, 0, 0), (0, 0, h), 0.075, M_ALU, base=(0.62, 0.63, 0.64, 1),
           aux=sage, n=14, r1=0.048)
    lo.cyl((0, 0, h), (0, 0, h + 0.10), 0.055, M_ALU, base=(0.7, 0.7, 0.7, 1),
           aux=sage, n=12)
    lo.box((-0.35, -0.35, -0.05), (0.35, 0.35, 0.10), M_CONC,
           base=(0.33, 0.33, 0.32, 1), aux=(0.6, 0.7, 0.4, hash01(k, 105)))
    # the flag: hangs from the halyard, curls in the 12.5-degree evening light
    fw = rnd(1.6, 2.6, k, 106)
    fh = fw * rnd(0.55, 0.70, k, 107)
    ztop = h - rnd(0.25, 0.7, k, 108)
    curl = rnd(0.25, 0.75, k, 109)
    art = paint_board(fw, fh, br, k + 0.75)
    ph = hash01(k, 110) * 6.0

    def _fsurf(A, B, off=0.0):
        a = np.clip(np.asarray(A, float) / fw, 0, 1)
        b = np.clip(np.asarray(B, float) / fh, 0, 1)
        # a flag on a halyard luffs: the fly end curls, and the curl carries a
        # travelling ripple that grows with distance from the hoist
        curlv = curl * np.sin(a * 3.4 + ph) * a ** 1.3 * 0.5
        rip = 0.035 * curl * np.sin(a * 11.0 + ph * 2.0 + b * 2.6) * a ** 1.6
        return np.stack([0.09 + a * fw,
                         curlv + rip + off,
                         ztop - fh + b * fh - 0.10 * a ** 2 -
                         0.05 * np.sin(a * 5.0 + b * fh * 2.0) -
                         0.02 * a ** 2 * np.sin(b * 7.0 + ph)], -1)

    surf = with_normal_offset(_fsurf)
    aux = board_aux(min(1.0, age + 0.25), 0.15, hash01(k, 111))
    emit_art(lo, art, surf, aux, mat=M_FABRIC, maxlen=0.038, out=1.0,
             rmin=CLOTH_RMIN)
    nu, nv = 44, 24
    U = np.linspace(0, fw, nu)
    V = np.linspace(0, fh, nv)
    UU, VV = np.meshgrid(U, V, indexing='ij')
    P = surf(UU.ravel(), VV.ravel(), -0.0010).reshape(nu, nv, 3)
    i = (np.arange(nu - 1)[:, None] * nv + np.arange(nv - 1)[None, :])
    q = np.stack([i, i + 1, i + nv + 1, i + nv], axis=-1).reshape(-1, 4)
    lo.add(P.reshape(-1, 3), q, M_FABRIC,
           uv=np.stack([UU / fw, VV / fh], -1).reshape(-1, 2),
           base=(0.32, 0.32, 0.31, 1), aux=aux, smooth=True)
    # the hoist: a sleeve and two clips onto the halyard
    for bv in (0.06, fh - 0.06):
        pnt = surf(np.array([0.012]), np.array([bv]), 0.0)[0]
        lo.cyl((pnt[0] - 0.02, pnt[1], pnt[2]), (pnt[0] + 0.01, pnt[1], pnt[2]),
               0.008, M_ALU, base=(0.55, 0.56, 0.57, 1), aux=aux, n=8)
    return ("flag", br.name, round(fw, 2), round(h, 2))


# --------------------------------------------------------------------------- #
#  9.  the equipment library — everything that dresses a marshal post           #
# --------------------------------------------------------------------------- #

GALV = (0.5, 0.5, 0.5, 0.0)          # base.a = 0 -> the steel shader goes galv
FLAGS = [("yellow", '#f0c000'), ("yellow", '#f0c000'), ("blue", '#1257a8'),
         ("green", '#0f9b46'), ("red", '#c8102e'), ("white", '#f2f2f2'),
         ("oil", '#e04a10'), ("black", '#1a1a1a')]
HIVIS = ['#e8f22a', '#f26a12', '#e8f22a', '#d8ec1e']


def eq_extinguisher(lo, k, kind=0):
    """0 = 6 kg powder, 1 = 9 kg, 2 = 50 kg trolley unit"""
    age = rnd(0.05, 0.6, k, 1)
    red = tint(srgb('#b4121b'), 0.10, k, 2)
    aux = (age, rnd(0.2, 0.7, k, 3), 0.4, hash01(k, 4))
    if kind == 2:
        r, h = 0.20, 0.98
        lo.cyl((0, 0, 0.10), (0, 0, 0.10 + h), r, M_PLASTIC,
               base=(*red, 1), aux=aux, n=20)
        lo.cyl((0, 0, 0.10 + h), (0, 0, 0.10 + h + 0.07), r * 0.55, M_PLASTIC,
               base=(*red, 1), aux=aux, n=16, r1=r * 0.30)
        lo.cyl((0, 0, 0.10 + h + 0.07), (0, 0, 0.10 + h + 0.16), 0.028, M_ALU,
               base=(0.55, 0.56, 0.55, 1), aux=aux, n=10)
        for sx in (-1, 1):
            lo.cyl((sx * (r + 0.05), 0.0, 0.10), (sx * (r + 0.05), 0.0, 1.30),
                   0.016, M_STEEL, base=GALV, aux=aux, n=8)
            lo.cyl((sx * (r + 0.05), -0.09, 0.16), (sx * (r + 0.05), 0.09, 0.16),
                   0.075, M_RUBBER, base=(0.02, 0.02, 0.02, 1), aux=aux, n=14)
        lo.cyl((-r - 0.05, 0, 1.30), (r + 0.05, 0, 1.30), 0.016, M_STEEL,
               base=GALV, aux=aux, n=8)
        pts = [[r * 0.6, -0.04, 1.05], [r + 0.16, -0.12, 0.85],
               [r + 0.10, 0.05, 0.55], [r * 0.5, 0.02, 0.35]]
        lo.tube(pts, 0.013, M_RUBBER, base=(0.03, 0.03, 0.03, 1), aux=aux, n=6)
    else:
        r = 0.078 if kind == 0 else 0.092
        h = 0.44 if kind == 0 else 0.55
        lo.cyl((0, 0, 0.0), (0, 0, h), r, M_PLASTIC, base=(*red, 1), aux=aux,
               n=18)
        lo.cyl((0, 0, h), (0, 0, h + 0.055), r * 0.6, M_PLASTIC, base=(*red, 1),
               aux=aux, n=14, r1=r * 0.34)
        lo.cyl((0, 0, h + 0.055), (0, 0, h + 0.125), 0.020, M_ALU,
               base=(0.5, 0.5, 0.48, 1), aux=aux, n=10)
        lo.box((-0.035, -0.10, h + 0.10), (0.035, 0.02, h + 0.135), M_ALU,
               base=(0.42, 0.42, 0.40, 1), aux=aux)
        lo.tube([[0.0, -0.02, h + 0.10], [r + 0.06, -0.05, h * 0.78],
                 [r + 0.02, 0.03, h * 0.42]], 0.010, M_RUBBER,
                base=(0.03, 0.03, 0.03, 1), aux=aux, n=6)
        # label band
        lo.cyl((0, 0, h * 0.32), (0, 0, h * 0.62), r + 0.001, M_PRINT,
               base=(0.85, 0.84, 0.80, 1), aux=(age, 0.3, 0.5, hash01(k, 5)),
               n=18, caps=False)


def eq_cone(lo, k, h=0.60):
    age = rnd(0.15, 0.9, k, 10)
    aux = (age, rnd(0.4, 1.0, k, 11), 0.5, hash01(k, 12))
    org = tint(srgb('#e2500f'), 0.12, k, 13)
    lo.box((-0.19, -0.19, 0.0), (0.19, 0.19, 0.035), M_PLASTIC, base=(*org, 1),
           aux=aux)
    lo.cyl((0, 0, 0.02), (0, 0, h), 0.135, M_PLASTIC, base=(*org, 1), aux=aux,
           n=16, r1=0.030, caps=False)
    for (z0, z1) in ((h * 0.42, h * 0.60), (h * 0.70, h * 0.80)):
        r0 = 0.135 + (0.030 - 0.135) * (z0 / h)
        r1 = 0.135 + (0.030 - 0.135) * (z1 / h)
        lo.cyl((0, 0, z0), (0, 0, z1), r0 + 0.002, M_PRINT,
               base=(0.72, 0.73, 0.75, 1), aux=(age, 0.5, 0.5, hash01(k, 14)),
               n=16, r1=r1 + 0.002, caps=False)


def eq_bin(lo, k, kind=0):
    age = rnd(0.2, 0.9, k, 20)
    aux = (age, rnd(0.4, 1.0, k, 21), 0.5, hash01(k, 22))
    col = srgb(pick(['#2b4d2e', '#38414a', '#4a2f22', '#1f3f5c'], k, 23))
    if kind == 0:      # wheelie bin
        w, d, h = 0.29, 0.27, 0.52
        lo.prism([(-w, -d), (w, -d * 0.9), (w, d * 0.9), (-w, d)], 0.14, h,
                 M_PLASTIC, base=(*col, 1), aux=aux)
        lo.box((-w - 0.01, -d - 0.01, h), (w + 0.01, d + 0.01, h + 0.035),
               M_PLASTIC, base=(*tint(col, 0.06, k, 24), 1), aux=aux)
        for sx in (-1, 1):
            lo.cyl((sx * (w - 0.05), -d + 0.03, 0.075),
                   (sx * (w - 0.05), -d + 0.09, 0.075), 0.075, M_RUBBER,
                   base=(0.02, 0.02, 0.02, 1), aux=aux, n=12)
        lo.box((-w * 0.5, -d - 0.02, h - 0.05), (w * 0.5, -d - 0.005, h - 0.01),
               M_PLASTIC, base=(*col, 1), aux=aux)
    else:              # open steel drum
        lo.cyl((0, 0, 0), (0, 0, 0.86), 0.29, M_STEEL, base=(*col, 1), aux=aux,
               n=22, caps=False)
        lo.cyl((0, 0, 0.0), (0, 0, 0.02), 0.29, M_STEEL, base=(*col, 1), aux=aux,
               n=22)
        for zz in (0.22, 0.58):
            lo.cyl((0, 0, zz), (0, 0, zz + 0.035), 0.303, M_STEEL, base=(*col, 1),
                   aux=aux, n=22, caps=False)


def eq_sacks(lo, k, n=None):
    """oil-dry / granulate sacks on a pallet"""
    n = n if n is not None else rint(3, 7, k, 30)
    age = rnd(0.1, 0.6, k, 31)
    # pallet
    for j in range(3):
        lo.box((-0.55, -0.36 + j * 0.33, 0.0), (0.55, -0.24 + j * 0.33, 0.055),
               M_WOOD, base=(0.24, 0.17, 0.10, 1), aux=(age, 0.6, 0.4, hash01(k, 32)))
    for j in range(5):
        lo.box((-0.55 + j * 0.245, -0.40, 0.055), (-0.45 + j * 0.245, 0.40, 0.075),
               M_WOOD, base=(0.26, 0.19, 0.11, 1), aux=(age, 0.6, 0.4, hash01(k, 33)))
    z = 0.075
    for i in range(n):
        w = rnd(0.22, 0.28, k, 34, i)
        d = rnd(0.16, 0.20, k, 35, i)
        h = rnd(0.09, 0.13, k, 36, i)
        cx = rnd(-0.22, 0.22, k, 37, i)
        cy = rnd(-0.14, 0.14, k, 38, i)
        sub = Local(lo, yaw(rnd(-16, 16, k, 39, i)), np.array([cx, cy, z]))
        col = srgb(pick(['#d8d2c0', '#c9c2ae', '#e0dccb'], k, 40, i))
        sub.box((-w, -d, 0.0), (w, d, h), M_PLASTIC, base=(*col, 1),
                aux=(age, rnd(0.3, 0.8, k, 41, i), 0.5, hash01(k, 42, i)))
        sub.box((-w * 0.62, -d - 0.001, h * 0.30),
                (w * 0.62, -d + 0.001, h * 0.72), M_PRINT,
                base=(0.06, 0.30, 0.16, 1), aux=(age, 0.3, 0.5, hash01(k, 43, i)))
        z += h * rnd(0.86, 0.98, k, 44, i)


def eq_broom(lo, k, kind=0):
    """0 broom, 1 shovel, 2 rake"""
    age = rnd(0.2, 0.9, k, 50)
    aux = (age, 0.6, 0.55, hash01(k, 51))
    L = rnd(1.35, 1.60, k, 52)
    lo.cyl((0, 0, 0), (0, 0, L), 0.017, M_WOOD, base=(0.32, 0.22, 0.12, 1),
           aux=aux, n=8)
    if kind == 0:
        lo.box((-0.22, -0.035, -0.06), (0.22, 0.035, 0.005), M_WOOD,
               base=(0.28, 0.19, 0.10, 1), aux=aux)
        nb = 26
        for i in range(nb):
            x = -0.20 + 0.40 * i / (nb - 1)
            lo.cyl((x, rnd(-0.02, 0.02, k, 53, i), -0.06),
                   (x + rnd(-0.02, 0.02, k, 54, i), rnd(-0.03, 0.03, k, 55, i),
                    -0.06 - rnd(0.10, 0.15, k, 56, i)), 0.006, M_PLASTIC,
                   base=(0.16, 0.11, 0.05, 1), aux=aux, n=4, caps=False)
    elif kind == 1:
        sub = Local(lo, pitchX(12.0), np.array([0, 0, 0]))
        sub.prism([(-0.13, -0.14), (0.13, -0.14), (0.15, 0.10), (0.0, 0.20),
                   (-0.15, 0.10)], -0.012, 0.0, M_STEEL,
                  base=(0.45, 0.45, 0.44, 1), aux=(age, 0.7, 0.7, hash01(k, 57)))
    else:
        lo.box((-0.20, -0.02, -0.03), (0.20, 0.02, 0.01), M_STEEL,
               base=(0.42, 0.42, 0.41, 1), aux=aux)
        for i in range(12):
            x = -0.18 + 0.36 * i / 11
            lo.cyl((x, 0, -0.03), (x, 0.03, -0.12), 0.005, M_STEEL,
                   base=(0.42, 0.42, 0.41, 1), aux=aux, n=4)


def eq_flagrack(lo, k, nflag=None):
    """furled flags in a rack — the single most legible 'marshal post' cue"""
    nflag = nflag if nflag is not None else rint(4, 7, k, 60)
    age = rnd(0.15, 0.75, k, 61)
    aux = (age, 0.5, 0.8, hash01(k, 62))
    w = 0.16 + 0.115 * nflag
    lo.box((-w * 0.5, -0.075, 0.72), (w * 0.5, 0.075, 0.80), M_STEEL,
           base=GALV, aux=aux, skip="t")
    lo.box((-w * 0.5, -0.075, 0.06), (w * 0.5, 0.075, 0.13), M_STEEL,
           base=GALV, aux=aux)
    for sx in (-1, 1):
        lo.cyl((sx * (w * 0.5 - 0.03), 0.0, 0.0),
               (sx * (w * 0.5 - 0.03), 0.0, 0.80), 0.020, M_STEEL, base=GALV,
               aux=aux, n=8)
    order = list(range(len(FLAGS)))
    for i in range(nflag):
        fi = order[int(hash01(k, 63, i) * len(order)) % len(order)]
        nmc, hx = FLAGS[fi]
        x = -w * 0.5 + 0.09 + i * (w - 0.18) / max(1, nflag - 1)
        lean = rnd(-6, 6, k, 64, i)
        sub = Local(lo, pitchX(lean) @ rollY(rnd(-4, 4, k, 65, i)),
                    np.array([x, 0.0, 0.06]))
        pl = rnd(0.95, 1.20, k, 66, i)
        sub.cyl((0, 0, 0), (0, 0, pl), 0.011, M_WOOD, base=(0.34, 0.24, 0.13, 1),
                aux=aux, n=6)
        col = tint(srgb(hx), 0.07, k, 67, i)
        rl = rnd(0.50, 0.68, k, 68, i)
        r0 = rnd(0.026, 0.040, k, 69, i)
        # flags get replaced every season: they are the NEWEST cloth on the post
        fage = rnd(0.05, 0.34, k, 70, i)
        sub.cyl((0, 0, pl - rl), (0, 0, pl - 0.03), r0, M_FABRIC, base=(*col, 1),
                aux=(fage, 0.25, 0.5, hash01(k, 71, i)),
                n=10, r1=r0 * rnd(0.72, 1.0, k, 72, i))
        # the tie that holds the roll
        sub.cyl((0, 0, pl - rl * 0.42), (0, 0, pl - rl * 0.42 + 0.018),
                r0 * 1.12, M_FABRIC, base=(0.06, 0.06, 0.07, 1),
                aux=(fage, 0.3, 0.5, hash01(k, 76, i)), n=10, caps=False)
        if chance(0.30, k, 73, i):      # one flag part-unfurled, hanging
            fw, fh = 0.55, 0.42
            nu, nv = 10, 8
            U = np.linspace(0, fw, nu); V = np.linspace(0, fh, nv)
            UU, VV = np.meshgrid(U, V, indexing='ij')
            P = np.stack([r0 + UU * 0.35,
                          np.sin(UU * 3.0 + hash01(k, 74, i) * 5) * 0.06 * UU,
                          pl - 0.06 - VV * 1.0 - 0.10 * (UU / fw) ** 2], -1)
            ii = (np.arange(nu - 1)[:, None] * nv + np.arange(nv - 1)[None, :])
            q = np.stack([ii, ii + 1, ii + nv + 1, ii + nv], -1).reshape(-1, 4)
            sub.add(P.reshape(-1, 3), q, M_FABRIC,
                    uv=np.stack([UU / fw, VV / fh], -1).reshape(-1, 2),
                    base=(*col, 1), aux=(fage, 0.3, 0.5, hash01(k, 75, i)),
                    smooth=True)
            sub.add(P.reshape(-1, 3), q[:, ::-1], M_FABRIC,
                    uv=np.stack([UU / fw, VV / fh], -1).reshape(-1, 2),
                    base=(*col, 1), aux=(fage, 0.3, 0.5, hash01(k, 75, i)),
                    smooth=True)


def eq_lightpanel(lo, k, state=0.0, h=2.35):
    """FIA marshal LED flag panel on its own post, facing oncoming traffic"""
    age = rnd(0.05, 0.45, k, 80)
    aux = (age, 0.3, 0.7, hash01(k, 81))
    lo.cyl((0, 0, 0), (0, 0, h), 0.055, M_STEEL, base=GALV, aux=aux, n=10)
    lo.box((-0.20, -0.20, 0.0), (0.20, 0.20, 0.06), M_CONC,
           base=(0.33, 0.33, 0.32, 1), aux=(0.6, 0.7, 0.4, hash01(k, 82)))
    W, H = 0.92, 0.70
    sub = Local(lo, pitchX(rnd(-9, -4, k, 83)), np.array([0, 0.05, h - H * 0.5]))
    sub.box((-W * 0.5, -0.055, -H * 0.5), (W * 0.5, 0.0, H * 0.5), M_PLASTIC,
            base=(0.035, 0.036, 0.038, 1), aux=aux)
    # hood
    sub.box((-W * 0.5 - 0.02, -0.06, H * 0.5), (W * 0.5 + 0.02, 0.13, H * 0.5 + 0.03),
            M_PLASTIC, base=(0.030, 0.030, 0.032, 1), aux=aux)
    for sx in (-1, 1):
        sub.box((sx * (W * 0.5) - 0.02 * sx, -0.06, -H * 0.5),
                (sx * (W * 0.5 + 0.02), 0.10, H * 0.5), M_PLASTIC,
                base=(0.030, 0.030, 0.032, 1), aux=aux)
    # LED matrix: a real panel is a dense grid of small lenses in a dark field,
    # not a coarse speaker grille
    nx, nz = 24, 18
    lit = srgb('#12d84a') if state > 0.5 else (0.02, 0.02, 0.02)
    sub.box((-W * 0.44, -0.002, -H * 0.42), (W * 0.44, 0.002, H * 0.42),
            M_PLASTIC, base=(0.016, 0.016, 0.018, 1), aux=(0.1, 0.2, 0.5, 0.5))
    for a in range(nx):
        for bq in range(nz):
            x = -W * 0.42 + 0.84 * W * a / (nx - 1)
            z = -H * 0.40 + 0.80 * H * bq / (nz - 1)
            sub.box((x - 0.0085, 0.002, z - 0.0085),
                    (x + 0.0085, 0.0055, z + 0.0085),
                    M_EMIT, base=(*lit, 1),
                    aux=(0.0, 0.0, state * rnd(0.85, 1.0, k, 84, a, bq), 0.5))


def eq_phone(lo, k, h=1.35):
    """marshal comms cabinet on a post, with its conduit"""
    age = rnd(0.2, 0.8, k, 90)
    aux = (age, 0.5, 0.6, hash01(k, 91))
    lo.cyl((0, 0, 0), (0, 0, h + 0.35), 0.038, M_STEEL, base=GALV, aux=aux, n=8)
    yel = tint(srgb('#e8b117'), 0.08, k, 92)
    lo.box((-0.14, -0.10, h - 0.24), (0.14, 0.10, h + 0.22), M_PLASTIC,
           base=(*yel, 1), aux=aux)
    lo.box((-0.145, 0.10, h - 0.245), (0.145, 0.115, h + 0.225), M_PLASTIC,
           base=(*tint(yel, 0.10, k, 93), 1), aux=aux)
    lo.box((-0.10, 0.115, h - 0.14), (0.10, 0.125, h + 0.10), M_PRINT,
           base=(0.02, 0.02, 0.02, 1), aux=(age, 0.3, 0.5, hash01(k, 94)))
    lo.tube([[0.0, -0.038, h - 0.24], [0.02, -0.06, 0.7], [0.0, -0.05, 0.10],
             [0.0, -0.02, 0.0]], 0.012, M_PLASTIC, base=(0.05, 0.05, 0.05, 1),
            aux=aux, n=6, caps=False)


def eq_jacket(lo, k):
    """a hi-vis jacket on a hook — the post is staffed, the marshal is at the
    rail.  A hanging cloth, not a person: a badly-modelled human at 4 m would
    be far worse than none."""
    col = srgb(pick(HIVIS, k, 100))
    age = rnd(0.1, 0.5, k, 101)
    nu, nv = 12, 14
    W, H = 0.46, 0.72
    U = np.linspace(-W * 0.5, W * 0.5, nu)
    V = np.linspace(0, -H, nv)
    UU, VV = np.meshgrid(U, V, indexing='ij')
    u = UU / (W * 0.5)
    v = -VV / H
    bulge = 0.055 * (1 - u ** 2) * np.sin(v * math.pi * 0.85) + \
        0.012 * np.sin(u * 9.0 + hash01(k, 102) * 6)
    P = np.stack([UU * (0.75 + 0.35 * v), bulge, VV * (1.0 - 0.05 * u ** 2)], -1)
    i = (np.arange(nu - 1)[:, None] * nv + np.arange(nv - 1)[None, :])
    q = np.stack([i, i + 1, i + nv + 1, i + nv], -1).reshape(-1, 4)
    aux = (age, 0.35, 0.5, hash01(k, 103))
    uv = np.stack([(UU / W + 0.5), 1.0 + VV / H], -1).reshape(-1, 2)
    lo.add(P.reshape(-1, 3), q, M_FABRIC, uv=uv, base=(*col, 1), aux=aux,
           smooth=True)
    lo.add(P.reshape(-1, 3), q[:, ::-1], M_FABRIC, uv=uv, base=(*col, 1),
           aux=aux, smooth=True)
    for vv in (-0.30, -0.42):
        VV2 = np.full(nu, vv)
        UU2 = U
        u2 = UU2 / (W * 0.5)
        v2 = -vv / H
        b2 = 0.055 * (1 - u2 ** 2) * np.sin(v2 * math.pi * 0.85)
        A = np.stack([UU2 * (0.75 + 0.35 * v2), b2 + 0.003, np.full(nu, vv)], -1)
        B = np.stack([UU2 * (0.75 + 0.35 * v2), b2 + 0.003,
                      np.full(nu, vv - 0.055)], -1)
        P2 = np.vstack([A, B])
        ii = np.arange(nu - 1)
        q2 = np.stack([ii, ii + nu, ii + nu + 1, ii + 1], -1)
        lo.add(P2, q2, M_FABRIC, base=(0.72, 0.73, 0.75, 1),
               aux=(age, 0.3, 0.5, hash01(k, 104)))


def eq_helmet(lo, k):
    col = srgb(pick(['#e8e8e6', '#1a1a1c', '#d0361f', '#1c4f8c'], k, 110))
    aux = (rnd(0.05, 0.4, k, 111), 0.3, 0.5, hash01(k, 112))
    n = 16
    th = np.linspace(0, math.pi * 2, n, endpoint=False)
    ph = np.linspace(0, math.pi * 0.5, 8)
    TH, PH = np.meshgrid(th, ph, indexing='ij')
    r = 0.135
    P = np.stack([r * np.cos(TH) * np.cos(PH), r * np.sin(TH) * np.cos(PH),
                  r * np.sin(PH)], -1)
    i = (np.arange(n)[:, None] * 8 + np.arange(7)[None, :])
    j = ((np.arange(n)[:, None] + 1) % n) * 8 + np.arange(7)[None, :]
    q = np.stack([i, j, j + 1, i + 1], -1).reshape(-1, 4)
    lo.add(P.reshape(-1, 3), q, M_PLASTIC, base=(*col, 1), aux=aux, smooth=True)
    lo.box((-0.10, -0.145, 0.02), (0.10, -0.10, 0.085), M_GLASS,
           base=(0.05, 0.045, 0.035, 1), aux=aux)


def eq_crate(lo, k):
    col = srgb(pick(['#1d4f7a', '#5c1d1d', '#2b2b2e', '#155c3a'], k, 120))
    aux = (rnd(0.2, 0.8, k, 121), 0.6, 0.5, hash01(k, 122))
    w, d, h = rnd(0.26, 0.34, k, 123), rnd(0.20, 0.26, k, 124), rnd(0.16, 0.26, k, 125)
    lo.box((-w, -d, 0), (w, d, h), M_PLASTIC, base=(*col, 1), aux=aux)
    lo.box((-w - 0.012, -d - 0.012, h), (w + 0.012, d + 0.012, h + 0.02),
           M_PLASTIC, base=(*tint(col, 0.10, k, 126), 1), aux=aux)


def eq_spineboard(lo, k):
    col = srgb('#e2620f')
    aux = (rnd(0.1, 0.5, k, 130), 0.4, 0.5, hash01(k, 131))
    lo.box((-0.22, -0.03, 0.0), (0.22, 0.03, 1.78), M_PLASTIC, base=(*col, 1),
           aux=aux)
    for zz in (0.30, 0.85, 1.40):
        lo.box((-0.235, -0.035, zz), (0.235, 0.035, zz + 0.055), M_FABRIC,
               base=(0.05, 0.05, 0.06, 1), aux=aux)
    for zz in (0.20, 0.60, 1.10, 1.55):
        for sx in (-1, 1):
            lo.box((sx * 0.185 - 0.03, -0.032, zz), (sx * 0.185 + 0.03, 0.032,
                                                     zz + 0.10), M_PLASTIC,
                   base=(0.02, 0.02, 0.02, 1), aux=aux)


def eq_firstaid(lo, k):
    aux = (rnd(0.1, 0.5, k, 140), 0.4, 0.5, hash01(k, 141))
    lo.box((-0.19, -0.11, 0.0), (0.19, 0.11, 0.26), M_PLASTIC,
           base=(0.78, 0.79, 0.78, 1), aux=aux)
    lo.box((-0.045, -0.115, 0.06), (0.045, -0.108, 0.20), M_PRINT,
           base=(0.02, 0.35, 0.13, 1), aux=aux)
    lo.box((-0.10, -0.115, 0.105), (0.10, -0.108, 0.155), M_PRINT,
           base=(0.02, 0.35, 0.13, 1), aux=aux)


def eq_chair(lo, k):
    col = srgb(pick(['#2d3540', '#3d2d24', '#1f3a2c'], k, 150))
    aux = (rnd(0.2, 0.8, k, 151), 0.6, 0.5, hash01(k, 152))
    for (sx, sy) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        lo.cyl((sx * 0.19, sy * 0.19, 0), (sx * 0.20, sy * 0.20, 0.42), 0.012,
               M_STEEL, base=GALV, aux=aux, n=6)
    lo.box((-0.22, -0.22, 0.42), (0.22, 0.22, 0.455), M_FABRIC, base=(*col, 1),
           aux=aux)
    sub = Local(lo, pitchX(-12), np.array([0, 0.20, 0.455]))
    sub.box((-0.20, -0.02, 0.0), (0.20, 0.015, 0.40), M_FABRIC, base=(*col, 1),
            aux=aux)


def eq_jerrycan(lo, k):
    col = srgb(pick(['#2b6b2b', '#7a1f1f', '#2f3f5c'], k, 160))
    aux = (rnd(0.2, 0.7, k, 161), 0.6, 0.5, hash01(k, 162))
    lo.box((-0.085, -0.16, 0.0), (0.085, 0.16, 0.44), M_PLASTIC, base=(*col, 1),
           aux=aux)
    lo.cyl((0.0, -0.10, 0.44), (0.0, -0.10, 0.50), 0.030, M_PLASTIC,
           base=(*col, 1), aux=aux, n=10)
    lo.box((-0.055, 0.02, 0.44), (0.055, 0.13, 0.485), M_PLASTIC,
           base=(*col, 1), aux=aux)


def eq_hosereel(lo, k):
    aux = (rnd(0.2, 0.8, k, 170), 0.6, 0.6, hash01(k, 171))
    lo.cyl((-0.09, 0, 0.55), (0.09, 0, 0.55), 0.055, M_STEEL, base=GALV,
           aux=aux, n=12)
    for j in range(9):
        r = 0.10 + j * 0.018
        lo.cyl((-0.075, 0, 0.55), (0.075, 0, 0.55), r, M_RUBBER,
               base=(0.05, 0.05, 0.05, 1), aux=aux, n=18, caps=False)
    for sx in (-1, 1):
        lo.cyl((sx * 0.11, 0, 0.55), (sx * 0.11, 0, 0.0), 0.020, M_STEEL,
               base=GALV, aux=aux, n=8)
    lo.cyl((-0.11, 0, 0.28), (0.11, 0, 0.28), 0.016, M_STEEL, base=GALV,
           aux=aux, n=6)


def eq_sign_panel(lo, k, body, W, H, bg, fg, mat=M_PRINT, tracking=0.16,
                  lines=None, thick=0.012, aux=None):
    """a generic legible sign: background + centred text (or two lines)"""
    aux = aux or (rnd(0.15, 0.8, k, 180), rnd(0.3, 0.9, k, 181), 0.5,
                  hash01(k, 182))
    art = Art(W, H)
    art.rect(0, 0, W, H, bg, 0)
    rows = lines or [(body, 0.5, 0.62)]
    for (txt, vc, hh) in rows:
        h = H * hh
        w = art.text_width(txt, h, tracking)
        if w > W * 0.88:
            h *= W * 0.88 / w
        art.text(txt, W * 0.5, H * vc - h * 0.40, h, fg, 2, tracking=tracking)
    surf = board_surface(W, H, k, bow=rnd(-0.004, 0.008, k, 183))
    lo2 = Local(lo, np.eye(3), np.array([0.0, 0.0, 0.0]))
    emit_art(lo2, art, surf, aux, mat=mat, maxlen=0.20)
    panel_body(lo2, surf, W, H, thick, aux, back=(0.14, 0.145, 0.15, 1))
    return art


# --------------------------------------------------------------------------- #
# 10.  marshal posts                                                            #
# --------------------------------------------------------------------------- #

SHELTER_COLS = ['#2f4f6d', '#5d6b57', '#7a2f2a', '#3b3f45', '#8a7a4a', '#2b5c50']


def build_shelter(lo, k, kind, W, D, Hh):
    """kind 0 open canopy, 1 box hut, 2 none (equipment stand), 3 platform"""
    age = rnd(0.15, 0.9, k, 200)
    aux = (age, rnd(0.3, 0.8, k, 201), rnd(0.1, 0.9, k, 202), hash01(k, 203))
    col = tint(srgb(pick(SHELTER_COLS, k, 204)), 0.10, k, 205)
    painted = chance(0.62, k, 206)
    steelbase = (*col, 1) if painted else GALV
    legr = rnd(0.038, 0.058, k, 207)
    plat = 0.0
    if kind == 3:
        plat = rnd(0.75, 1.15, k, 208)
        # under-deck frame: four corner posts + two bearers + cross-bracing.
        # (The first build floated the whole shelter: the deck had no legs.)
        for (sx, sy) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            lo.box((sx * W * 0.5 - 0.05, sy * D * 0.5 - 0.05,
                    -0.02), (sx * W * 0.5 + 0.05, sy * D * 0.5 + 0.05,
                             plat - 0.10), M_STEEL, base=steelbase, aux=aux)
            lo.box((sx * W * 0.5 - 0.17, sy * D * 0.5 - 0.17, -0.06),
                   (sx * W * 0.5 + 0.17, sy * D * 0.5 + 0.17, 0.05), M_CONC,
                   base=(0.33, 0.33, 0.32, 1),
                   aux=(0.65, 0.75, 0.4, hash01(k, 216, sx, sy)))
        for sy in (-1, 1):
            lo.box((-W * 0.5 - 0.04, sy * D * 0.5 - 0.045, plat - 0.16),
                   (W * 0.5 + 0.04, sy * D * 0.5 + 0.045, plat - 0.06),
                   M_STEEL, base=steelbase, aux=aux)
            lo.cyl((-W * 0.5, sy * D * 0.5, 0.06), (W * 0.5, sy * D * 0.5,
                                                    plat - 0.14), 0.018,
                   M_STEEL, base=steelbase, aux=aux, n=6)
        # deck
        lo.box((-W * 0.5, -D * 0.5, plat - 0.06), (W * 0.5, D * 0.5, plat),
               M_STEEL, base=steelbase, aux=aux)
        for j in range(int(W / 0.22)):
            x = -W * 0.5 + 0.11 + j * 0.22
            lo.box((x - 0.09, -D * 0.5, plat - 0.005), (x + 0.09, D * 0.5,
                                                        plat + 0.012), M_WOOD,
                   base=(0.30, 0.22, 0.13, 1), aux=(age, 0.7, 0.4, hash01(k, 209, j)))
        # a real stair: two stringers and treads, on the side away from the track
        nst = max(2, int(round(plat / 0.20)))
        run = 0.26
        sxs = 1 if chance(0.5, k, 217) else -1
        x0 = sxs * (W * 0.5 + 0.03)
        for j in range(nst):
            zt = plat * (j + 1) / nst
            y0 = D * 0.30 - j * run
            lo.box((x0 + sxs * 0.02, y0 - run * 0.92, zt - 0.042),
                   (x0 + sxs * 0.62, y0, zt), M_STEEL, base=steelbase, aux=aux)
        for off in (0.08, 0.56):
            lo.cyl((x0 + sxs * off, D * 0.30 + 0.06, plat + 0.02),
                   (x0 + sxs * off, D * 0.30 - nst * run - 0.04, 0.02), 0.026,
                   M_STEEL, base=steelbase, aux=aux, n=6)
        # stair handrail on the outboard stringer
        lo.cyl((x0 + sxs * 0.62, D * 0.30, plat + 0.95),
               (x0 + sxs * 0.62, D * 0.30 - nst * run, 0.92), 0.020,
               M_STEEL, base=steelbase, aux=aux, n=6)
        for yy in (D * 0.30 - 0.05, D * 0.30 - nst * run + 0.10):
            lo.cyl((x0 + sxs * 0.62, yy, 0.0), (x0 + sxs * 0.62, yy,
                                                plat * 0.95), 0.018,
                   M_STEEL, base=steelbase, aux=aux, n=6)
        # handrail along the open (track) side
        for sx in (-1, 1):
            lo.cyl((sx * W * 0.5, -D * 0.5, plat), (sx * W * 0.5, -D * 0.5,
                                                    plat + 1.05), 0.024,
                   M_STEEL, base=steelbase, aux=aux, n=8)
        lo.cyl((-W * 0.5, -D * 0.5, plat + 1.05), (W * 0.5, -D * 0.5, plat + 1.05),
               0.024, M_STEEL, base=steelbase, aux=aux, n=8)
        lo.cyl((-W * 0.5, -D * 0.5, plat + 0.55), (W * 0.5, -D * 0.5, plat + 0.55),
               0.020, M_STEEL, base=steelbase, aux=aux, n=8)
    if kind == 2:
        # equipment stand only: a rail on two posts, with hooks
        for sx in (-1, 1):
            lo.cyl((sx * W * 0.4, 0.0, 0.0), (sx * W * 0.4, 0.0, 1.35), legr,
                   M_STEEL, base=steelbase, aux=aux, n=10)
            lo.box((sx * W * 0.4 - 0.16, -0.16, 0.0), (sx * W * 0.4 + 0.16, 0.16,
                                                       0.05), M_CONC,
                   base=(0.33, 0.33, 0.32, 1), aux=(0.6, 0.7, 0.4, hash01(k, 210)))
        lo.cyl((-W * 0.4, 0.0, 1.32), (W * 0.4, 0.0, 1.32), 0.028, M_STEEL,
               base=steelbase, aux=aux, n=10)
        for j in range(4):
            x = -W * 0.28 + j * W * 0.185
            lo.tube([[x, 0.0, 1.30], [x, -0.06, 1.24], [x, -0.02, 1.19]], 0.008,
                    M_STEEL, base=steelbase, aux=aux, n=5, caps=False)
        return plat, aux, steelbase
    # legs
    rooffall = rnd(0.10, 0.22, k, 211)
    for (sx, sy) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        zt = Hh + plat + (rooffall if sy > 0 else 0.0)
        lo.cyl((sx * W * 0.5, sy * D * 0.5, 0.0 if kind != 3 else plat - 0.06),
               (sx * W * 0.5, sy * D * 0.5, zt), legr, M_STEEL, base=steelbase,
               aux=aux, n=10)
        if kind != 3:
            lo.box((sx * W * 0.5 - 0.15, sy * D * 0.5 - 0.15, -0.02),
                   (sx * W * 0.5 + 0.15, sy * D * 0.5 + 0.15, 0.055), M_CONC,
                   base=(0.33, 0.33, 0.32, 1),
                   aux=(0.6, 0.7, 0.4, hash01(k, 212, sx, sy)))
    # roof: profiled steel sheet, overhanging, falling to the back
    ovx, ovy = 0.18, 0.16
    nrib = int((W + 2 * ovx) / 0.19)
    for j in range(nrib):
        x0 = -W * 0.5 - ovx + j * (W + 2 * ovx) / nrib
        x1 = x0 + (W + 2 * ovx) / nrib * 0.94
        hgt = 0.022 if j % 2 == 0 else 0.0
        lo.add(*_ramp_sheet(x0, x1, -D * 0.5 - ovy, D * 0.5 + ovy,
                            Hh + plat, Hh + plat + rooffall, hgt),
               mat=M_STEEL, base=steelbase, aux=aux, smooth=False)
    # rear + one side skin
    skin = pick([M_STEEL, M_WOOD, M_STEEL], k, 213)
    scol = steelbase if skin == M_STEEL else (0.30, 0.22, 0.13, 1)
    if kind in (0, 1, 3):
        z0 = plat
        lo.box((-W * 0.5 - 0.01, D * 0.5 - 0.02, z0),
               (W * 0.5 + 0.01, D * 0.5 + 0.01, Hh + plat + rooffall * 0.95),
               skin, base=scol, aux=aux)
        # sheet joints, and a notice sheet on about half the posts
        nsh = max(2, int(W / rnd(0.85, 1.25, k, 218)))
        for j in range(1, nsh):
            x = -W * 0.5 + W * j / nsh
            lo.box((x - 0.012, D * 0.5 - 0.032, z0),
                   (x + 0.012, D * 0.5 - 0.018,
                    Hh + plat + rooffall * 0.92), M_STEEL,
                   base=steelbase, aux=(min(1.0, age + 0.15), 0.6, 0.5,
                                        hash01(k, 219, j)))
        if chance(0.55, k, 220):
            nw = rnd(0.30, 0.46, k, 221)
            nh = nw * rnd(1.25, 1.45, k, 222)
            nz = plat + rnd(1.05, 1.45, k, 223)
            nx_ = rnd(-0.32, 0.32, k, 224) * W
            lo.box((nx_ - nw * 0.5, D * 0.5 - 0.036, nz),
                   (nx_ + nw * 0.5, D * 0.5 - 0.030, nz + nh), M_PRINT,
                   base=(0.80, 0.79, 0.75, 1),
                   aux=(rnd(0.3, 0.8, k, 225), 0.35, 0.5, hash01(k, 226)))
            for r in range(4):
                lo.box((nx_ - nw * 0.34, D * 0.5 - 0.038,
                        nz + nh * (0.68 - r * 0.14)),
                       (nx_ + nw * (0.34 - 0.06 * r), D * 0.5 - 0.036,
                        nz + nh * (0.72 - r * 0.14)), M_PRINT,
                       base=(0.10, 0.10, 0.11, 1),
                       aux=(0.3, 0.3, 0.5, hash01(k, 227, r)))
        sx = 1 if chance(0.5, k, 214) else -1
        lo.box((sx * W * 0.5 - 0.01 * sx, -D * 0.5, z0),
               (sx * W * 0.5 + 0.01 * sx, D * 0.5, Hh + plat + rooffall * 0.5),
               skin, base=scol, aux=aux)
    if kind == 1:
        # box hut: front half-wall + a window opening
        lo.box((-W * 0.5, -D * 0.5 - 0.01, plat), (W * 0.5, -D * 0.5 + 0.01,
                                                   plat + 0.95), skin,
               base=scol, aux=aux)
        lo.box((-W * 0.5, -D * 0.5 - 0.01, plat + 1.75),
               (W * 0.5, -D * 0.5 + 0.01, Hh + plat), skin, base=scol, aux=aux)
        # bench inside
        lo.box((-W * 0.4, D * 0.5 - 0.42, plat + 0.44),
               (W * 0.4, D * 0.5 - 0.06, plat + 0.49), M_WOOD,
               base=(0.31, 0.23, 0.14, 1), aux=(age, 0.6, 0.4, hash01(k, 215)))
    return plat, aux, steelbase


def _ramp_sheet(x0, x1, y0, y1, z_front, z_back, rise):
    """one corrugation of a sloping roof sheet as a closed slab"""
    V = [(x0, y0, z_front + rise), (x1, y0, z_front + rise),
         (x1, y1, z_back + rise), (x0, y1, z_back + rise),
         (x0, y0, z_front - 0.012), (x1, y0, z_front - 0.012),
         (x1, y1, z_back - 0.012), (x0, y1, z_back - 0.012)]
    F = np.array([(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (2, 6, 7, 3),
                  (3, 7, 4, 0), (1, 5, 6, 2)])
    return V, F


def post_pad(k):
    """shelter and hardstanding dimensions for a post, drawn once.

    `_finalise_posts` needs these to stand the post off the barrier by half its
    own pad, and `build_marshal_post` needs them to build it.  Two copies of the
    same hash draw is exactly the class of divergence this rebuild exists to
    stop, so there is one.
    """
    W = rnd(2.1, 3.4, k, 301)
    D = rnd(1.5, 2.3, k, 302)
    Hh = rnd(2.15, 2.55, k, 303)
    return W, D, Hh, W * rnd(1.35, 1.9, k, 304), D * rnd(1.5, 2.1, k, 305)


def build_marshal_post(mb, post, tier):
    """post = dict(n, s, side, lat, kind, ...).  One object per post."""
    s, side, lat = post["s"], post["side"], post["lat"]
    k = post["k"]
    W, D, Hh, padw, padd = post_pad(k)
    # The hardstanding reaches padd*0.55 OUTBOARD of the post centre and
    # padd*0.45 INBOARD.  `_finalise_posts` already stood the post off the
    # barrier by padd*0.45 + clearance, so the slab cannot run into the Armco;
    # `foot` here is what the corridor rim has to hold on the far side.
    wx, wy, z, lat = anchor("post%02d" % post["n"], s, lat, side,
                            embed=BASE_EMBED, foot=padd * 0.55 + 0.2,
                            behind=True, clear=padd * 0.45 + 0.25,
                            height=Hh + 0.9, halfspan=padw * 0.5)
    if wx is None:                       # no ground behind the barrier here
        return []
    post["lat"] = lat
    nx, ny = normal_world(s, side)
    # LOCAL FRAME: +y points AWAY from the track, so the shelter's back wall is
    # at +D/2 and its open front (-D/2) looks at the circuit, which is the whole
    # point of a marshal post.  (The first build had this backwards and every
    # post presented a blank wall to the camera.)
    R, O = frame_from_facing((float(wx), float(wy), z), (float(nx), float(ny)))
    R = R @ yaw(rnd(-9, 9, k, 300))
    lo = Local(mb, R, O)
    kind = post["kind"]
    pad_age = rnd(0.25, 0.95, k, 306)
    # ground pad: concrete slab, gravel patch, or nothing
    padkind = pick([0, 0, 0, 1, 2], k, 307)
    if padkind == 0:
        nseg = max(2, int(padw / 1.4))
        for j in range(nseg):
            x0 = -padw * 0.5 + j * padw / nseg
            x1 = x0 + padw / nseg - 0.012
            lo.box((x0, -padd * 0.55, -0.10), (x1, padd * 0.45,
                                               rnd(0.005, 0.022, k, 308, j)),
                   M_CONC, base=(0.335, 0.335, 0.325, 1),
                   aux=(pad_age, rnd(0.4, 0.9, k, 309, j), 0.5, hash01(k, 310, j)))
    elif padkind == 1:
        lo.box((-padw * 0.5, -padd * 0.55, -0.08), (padw * 0.5, padd * 0.45,
                                                    0.012), M_CONC,
               base=(0.22, 0.205, 0.185, 1), aux=(0.9, 0.9, 0.5, hash01(k, 311)))
    plat, aux, steelbase = build_shelter(lo, k, kind, W, D, Hh)
    # ---- equipment: every post gets a different kit, laid out on its own pad
    slots = []
    nsl = 9
    for j in range(nsl):
        sx = -padw * 0.5 + padw * (j + 0.5) / nsl
        slots.append(sx)
    used = set()

    def slot(pref, kk):
        order = sorted(range(nsl), key=lambda j: abs(slots[j] - pref) +
                       0.9 * hash01(k, 320, kk, j))
        for j in order:
            if j not in used:
                used.add(j)
                return slots[j]
        return pref

    inv = []
    gz = 0.0                      # ground items stay on the ground...
    # flags: always at the FRONT of the post, where a marshal grabs them
    fx = max(-W * 0.36, min(W * 0.36, rnd(-0.6, 0.6, k, 321) * W))
    frack = Local(lo, yaw(rnd(-20, 20, k, 322)),
                  np.array([fx, -D * 0.5 + rnd(0.16, 0.40, k, 323), plat]))
    eq_flagrack(frack, k + 1.0, rint(4, 7, k, 324))
    inv.append("flagrack")
    # extinguishers: 1-3, mixed sizes, on the pad beside the shelter
    nex = rint(1, 3, k, 325)
    for j in range(nex):
        kind_e = pick([0, 0, 1, 2], k, 326, j)
        ex = slot(rnd(-1.0, 1.0, k, 327, j) * padw * 0.4, 2 + j)
        onduck = kind != 3 and abs(ex) < W * 0.45 and chance(0.4, k, 330, j)
        sub = Local(lo, yaw(rnd(0, 360, k, 328, j)),
                    np.array([ex, rnd(-0.3, 0.4, k, 329, j) + D * 0.35,
                              plat if onduck else gz]))
        eq_extinguisher(sub, k + 2.0 + j, kind_e)
    inv.append("extinguisher x%d" % nex)
    # light panel: on its own post, out toward the track, facing oncoming cars
    if post.get("panel", True):
        # off to one side, so it never stands in front of the post's own opening
        lp = Local(lo, yaw(180.0 + rnd(-12, 12, k, 330)),
                   np.array([(1.0 if chance(0.5, k, 331) else -1.0) *
                             padw * rnd(0.34, 0.52, k, 335),
                             -padd * rnd(0.55, 0.80, k, 332), 0.0]))
        eq_lightpanel(lp, k + 3.0, state=post.get("panel_state", 0.0),
                      h=rnd(2.15, 2.55, k, 333))
        inv.append("LED panel")
    # comms — cabinet on the back of the post, facing in
    if chance(0.72, k, 334):
        ph = Local(lo, yaw(180.0 + rnd(-25, 25, k, 335)),
                   np.array([slot(-padw * 0.42, 7), D * 0.5 + 0.16, 0.0]))
        eq_phone(ph, k + 4.0)
        inv.append("comms")
    # brooms / shovels / rakes leaning on the back wall, INSIDE the shelter
    ntool = rint(1, 3, k, 336)
    for j in range(ntool):
        tx = rnd(-0.42, 0.42, k, 337, j) * W
        sub = Local(lo, yaw(rnd(-30, 30, k, 338, j)) @
                    pitchX(-rnd(9, 17, k, 339, j)),
                    np.array([tx, D * 0.5 - 0.16, plat]))
        eq_broom(sub, k + 5.0 + j, pick([0, 0, 1, 2], k, 340, j))
    inv.append("tools x%d" % ntool)
    # bin / drum
    if chance(0.8, k, 341):
        bx = slot(rnd(-1, 1, k, 342) * padw * 0.45, 13)
        sub = Local(lo, yaw(rnd(0, 360, k, 343)),
                    np.array([bx, rnd(0.1, 0.6, k, 344) + D * 0.3, gz]))
        eq_bin(sub, k + 6.0, 0 if chance(0.6, k, 345) else 1)
        inv.append("bin")
    # absorbent sacks
    if chance(0.55, k, 346):
        sx = slot(rnd(-1, 1, k, 347) * padw * 0.42, 14)
        sub = Local(lo, yaw(rnd(0, 360, k, 348)),
                    np.array([sx, rnd(0.2, 0.7, k, 349) + D * 0.4, gz]))
        eq_sacks(sub, k + 7.0)
        inv.append("granulate")
    # cones, nested or standing
    if chance(0.75, k, 350):
        ncone = rint(2, 6, k, 351)
        cx = slot(rnd(-1, 1, k, 352) * padw * 0.45, 15)
        if chance(0.5, k, 353):        # nested stack
            for j in range(ncone):
                sub = Local(lo, yaw(rnd(0, 360, k, 354, j)),
                            np.array([cx + rnd(-0.02, 0.02, k, 355, j),
                                      D * 0.3 + rnd(-0.02, 0.02, k, 356, j),
                                      gz + j * 0.085]))
                eq_cone(sub, k + 8.0 + j, rnd(0.52, 0.66, k, 357, j))
        else:
            for j in range(min(ncone, 4)):
                sub = Local(lo, yaw(rnd(0, 360, k, 358, j)),
                            np.array([cx + rnd(-0.5, 0.5, k, 359, j),
                                      rnd(-0.9, 0.4, k, 360, j), gz]))
                eq_cone(sub, k + 8.0 + j, rnd(0.52, 0.72, k, 361, j))
        inv.append("cones x%d" % ncone)
    # first aid / spine board / hi-vis / helmets — the "staffed" cues
    if chance(0.5, k, 362):
        sub = Local(lo, yaw(rnd(-15, 15, k, 363)),
                    np.array([W * 0.5 - 0.30, D * 0.5 - 0.10, plat + 0.9]))
        eq_firstaid(sub, k + 9.0)
        inv.append("first aid")
    if chance(0.35, k, 364) and kind != 2:
        sub = Local(lo, yaw(rnd(-8, 8, k, 365)) @ rollY(rnd(-6, 6, k, 366)),
                    np.array([-W * 0.5 + 0.20, D * 0.5 - 0.09, plat + 0.02]))
        eq_spineboard(sub, k + 10.0)
        inv.append("spine board")
    njk = rint(0, 3, k, 367)
    for j in range(njk):
        sub = Local(lo, yaw(rnd(-25, 25, k, 368, j)),
                    np.array([rnd(-0.8, 0.8, k, 369, j) * W * 0.5,
                              D * 0.5 - 0.13, plat + rnd(1.55, 1.80, k, 370, j)]))
        eq_jacket(sub, k + 11.0 + j)
    if njk:
        inv.append("hi-vis x%d" % njk)
    if chance(0.4, k, 371) and kind in (0, 1, 3):
        for j in range(rint(1, 2, k, 372)):
            sub = Local(lo, yaw(rnd(0, 360, k, 373, j)),
                        np.array([rnd(-0.6, 0.6, k, 374, j) * W * 0.5,
                                  D * 0.5 - 0.35, plat + 0.50]))
            eq_helmet(sub, k + 12.0 + j)
        inv.append("helmets")
    if chance(0.45, k, 375):
        sub = Local(lo, yaw(rnd(0, 360, k, 376)),
                    np.array([rnd(-1, 1, k, 377) * W * 0.34,
                              rnd(-0.1, 0.35, k, 378) * D, plat]))
        eq_chair(sub, k + 13.0)
        inv.append("chair")
    if chance(0.5, k, 379):
        sub = Local(lo, yaw(rnd(0, 360, k, 380)),
                    np.array([slot(rnd(-1, 1, k, 381) * padw * 0.4, 16),
                              rnd(0.2, 0.6, k, 382) + D * 0.3, gz]))
        eq_crate(sub, k + 14.0)
        inv.append("crate")
    if chance(0.30, k, 383):
        sub = Local(lo, yaw(rnd(0, 360, k, 384)),
                    np.array([slot(rnd(-1, 1, k, 385) * padw * 0.4, 17),
                              rnd(0.2, 0.6, k, 386) + D * 0.3, gz]))
        eq_jerrycan(sub, k + 15.0)
        inv.append("jerrycan")
    if chance(0.25, k, 387) and kind in (0, 1):
        sub = Local(lo, yaw(180.0), np.array([W * 0.5 - 0.10, D * 0.5 - 0.10,
                                              plat + 0.55]))
        eq_hosereel(sub, k + 16.0)
        inv.append("hose reel")
    # the post identity board — every post is numbered, and the number is the
    # thing a viewer can actually read
    pn = "%d" % post["n"]
    bw, bh = rnd(0.62, 0.86, k, 388), rnd(0.42, 0.56, k, 389)
    sub = Local(lo, yaw(180.0 + rnd(-6, 6, k, 390)),
                np.array([rnd(-0.3, 0.3, k, 391) * W * 0.5, -D * 0.5 - 0.03,
                          plat + Hh * rnd(0.62, 0.74, k, 392) - bh * 0.5]))
    eq_sign_panel(sub, k + 17.0, pn, bw, bh, srgb('#f0f0ec'), srgb('#141414'),
                  tracking=0.10,
                  lines=[("POSTE", 0.74, 0.24), (pn, 0.30, 0.50)])
    for sx in (-1, 1):
        sub.cyl((sx * bw * 0.34, -0.012, bh * 0.5),
                (sx * bw * 0.34, -0.012,
                 plat + Hh - (plat + Hh * rnd(0.62, 0.74, k, 392) - bh * 0.5)),
                0.012, M_STEEL, base=GALV,
                aux=(0.5, 0.6, 0.8, hash01(k, 393)), n=6)
    inv.append("post number board")
    return inv


# --------------------------------------------------------------------------- #
# 11.  tyres and tyre stacks                                                    #
# --------------------------------------------------------------------------- #
#
# Four archetypes, each generated from its own profile: an F1 slick, an F1 wet,
# a road tyre and a truck tyre.  Tread is real geometry (grooves cut into the
# crown), the sidewall carries a raised brand band, and every tyre draws its own
# radius, width, wear, squash and chalking.

TYRE_KINDS = ("slick", "wet", "road", "truck")
COMPOUND = [('#c8102e', "TENDRE"), ('#f0c000', "MOYEN"), ('#f2f2f2', "DUR"),
            ('#1f9b46', "INTER"), ('#1257a8', "PLUIE")]


def tyre_dims(k, kind="slick", scale=1.0):
    """(R, width, rim radius, groove count) — needed before the tyre is built so
    a stack can be seated on the ground and closed at the top."""
    if kind == "slick":
        R = rnd(0.345, 0.365, k, 400) * scale
        Wd = rnd(0.300, 0.330, k, 401) * scale
        return R, Wd, R * rnd(0.60, 0.64, k, 402), 0
    if kind == "wet":
        R = rnd(0.340, 0.360, k, 400) * scale
        Wd = rnd(0.295, 0.325, k, 401) * scale
        return R, Wd, R * rnd(0.60, 0.64, k, 402), 4
    if kind == "road":
        R = rnd(0.300, 0.335, k, 400) * scale
        Wd = rnd(0.185, 0.225, k, 401) * scale
        return R, Wd, R * rnd(0.62, 0.70, k, 402), 3
    R = rnd(0.480, 0.545, k, 400) * scale
    Wd = rnd(0.255, 0.300, k, 401) * scale
    return R, Wd, R * rnd(0.58, 0.64, k, 402), 4


def build_tyre(lo, k, kind="slick", load=0.0, scale=1.0):
    """one tyre lying flat (axis = z).  load 0..1 squashes it and flattens the
    crown, which is what the tyre under a five-high stack actually does."""
    if kind == "slick":
        R = rnd(0.345, 0.365, k, 400) * scale
        Wd = rnd(0.300, 0.330, k, 401) * scale
        rim = R * rnd(0.60, 0.64, k, 402)
        ngroove = 0
    elif kind == "wet":
        R = rnd(0.340, 0.360, k, 400) * scale
        Wd = rnd(0.295, 0.325, k, 401) * scale
        rim = R * rnd(0.60, 0.64, k, 402)
        ngroove = 4
    elif kind == "road":
        R = rnd(0.300, 0.335, k, 400) * scale
        Wd = rnd(0.185, 0.225, k, 401) * scale
        rim = R * rnd(0.62, 0.70, k, 402)
        ngroove = 3
    else:
        R = rnd(0.480, 0.545, k, 400) * scale
        Wd = rnd(0.255, 0.300, k, 401) * scale
        rim = R * rnd(0.58, 0.64, k, 402)
        ngroove = 4
    age = rnd(0.15, 0.75, k, 403)
    aux = (age, rnd(0.3, 0.9, k, 404), 0.5, hash01(k, 405))
    n = 44 if scale > 0.8 else 30
    th = np.linspace(0, 2 * math.pi, n, endpoint=False)
    ct, st = np.cos(th), np.sin(th)
    # --- the section, as a real tyre section: bead -> sidewall -> shoulder ->
    # crown (with the tread grooves cut INTO it) -> shoulder -> sidewall -> bead
    crown_hw = 0.36                      # half-width of the flat crown, in Wd
    sec = [(rim / R, -0.42), (0.800, -0.505), (0.910, -0.500), (0.975, -0.445),
           (0.996, -0.400), (1.0, -crown_hw)]
    if ngroove:
        # A groove is a THIN dark line, not a canyon.  Measured against real
        # tyres: ~5 % of the crown width each and 1.5–3 % of the radius deep.
        # (The first two passes made them 30–60 % of the crown and 5 % deep,
        # which is why a stack rendered as coiled hose rather than as tyres.)
        pitch = 2.0 * crown_hw / (ngroove + 1)
        gw = crown_hw * 2.0 * 0.024             # groove half-width, in Wd units
        dep = rnd(0.014, 0.030, k, 407) * (1.0 - 0.45 * age)
        for gi in range(ngroove):
            zc = -crown_hw + pitch * (gi + 1)
            sec += [(1.0, zc - gw * 1.30), (1.0 - dep * 0.80, zc - gw),
                    (1.0 - dep, zc - gw * 0.70), (1.0 - dep, zc + gw * 0.70),
                    (1.0 - dep * 0.80, zc + gw), (1.0, zc + gw * 1.30)]
    sec += [(1.0, crown_hw), (0.996, 0.400), (0.975, 0.445), (0.910, 0.500),
            (0.800, 0.505), (rim / R, 0.42)]
    sec = sorted(set(sec), key=lambda t: (t[1], -t[0])) if False else sec
    npf = len(sec)
    wob = 1.0 + 0.010 * np.sin(th * 3.0 + hash01(k, 406) * 6.0)
    P = []
    for (rf, zf) in sec:
        # the tyre under load spreads: the crown flattens and the sidewall bulges
        bulge = 1.0 + load * 0.045 * math.exp(-((abs(zf) - 0.47) / 0.16) ** 2)
        flat = 1.0 - load * 0.020 * max(0.0, 1.0 - abs(zf) / crown_hw)
        rr = R * rf * bulge * flat
        zz = Wd * zf * (1.0 - load * 0.06)
        P.append(np.stack([rr * ct * wob, rr * st * wob, np.full(n, zz)], -1))
    P = np.stack(P, 0)
    i = (np.arange(npf - 1)[:, None] * n + np.arange(n)[None, :])
    j = (np.arange(npf - 1)[:, None] * n + (np.arange(n)[None, :] + 1) % n)
    q = np.stack([i, j, j + n, i + n], -1).reshape(-1, 4)
    uv = np.stack([np.tile(th / (2 * math.pi), npf),
                   np.repeat(np.arange(npf, dtype=float) / (npf - 1), n)], -1)
    lo.add(P.reshape(-1, 3), q, M_RUBBER, uv=uv, base=(0.042, 0.040, 0.039, 1),
           aux=aux, smooth=True)
    # the inner bore + the two bead faces close the solid
    for (sz, rev) in ((-1, True), (1, False)):
        rr = R * (rim / R)
        A = np.stack([rr * ct, rr * st, np.full(n, Wd * 0.42 * sz)], -1)
        B = np.stack([rr * 0.985 * ct, rr * 0.985 * st,
                      np.full(n, Wd * 0.30 * sz)], -1)
        PP = np.vstack([A, B])
        ii = np.arange(n)
        jj = (ii + 1) % n
        qq = np.stack([ii, jj, jj + n, ii + n], -1)
        lo.add(PP, qq[:, ::-1] if rev else qq, M_RUBBER,
               base=(0.030, 0.029, 0.028, 1), aux=aux, smooth=True)
    rr = R * (rim / R) * 0.985
    A = np.stack([rr * ct, rr * st, np.full(n, -Wd * 0.30)], -1)
    B = np.stack([rr * ct, rr * st, np.full(n, Wd * 0.30)], -1)
    PP = np.vstack([A, B])
    ii = np.arange(n)
    jj = (ii + 1) % n
    lo.add(PP, np.stack([ii, jj, jj + n, ii + n], -1)[:, ::-1], M_RUBBER,
           base=(0.022, 0.021, 0.020, 1), aux=aux, smooth=True)
    # sidewall brand band + a compound stripe (fictional tyre supplier)
    ci = int(hash01(k, 408) * len(COMPOUND)) % len(COMPOUND)
    ccol = srgb(COMPOUND[ci][0])
    for sz in (-1, 1):
        zz = Wd * 0.50 * sz
        r0, r1 = R * 0.855, R * 0.925
        A = np.stack([r0 * ct, r0 * st, np.full(n, zz + 0.0015 * sz)], -1)
        B = np.stack([r1 * ct, r1 * st, np.full(n, zz + 0.0015 * sz)], -1)
        PP = np.vstack([A, B])
        ii = np.arange(n)
        jj = (ii + 1) % n
        qq = np.stack([ii, jj, jj + n, ii + n], -1)
        if sz < 0:
            qq = qq[:, ::-1]
        lo.add(PP, qq, M_PRINT, base=(*ccol, 1),
               uv=np.stack([np.tile(th / (2 * math.pi), 2),
                            np.repeat([0.0, 1.0], n)], -1),
               aux=(age, aux[1], 0.5, hash01(k, 409)), smooth=True)
    # raised lettering on one sidewall (MERIDIAN, the circuit's tyre supplier)
    if scale > 0.75:
        br = Brand(TYRE_BRAND)
        V, F, wtxt = text_poly(br.name, 0.10)
        if len(V):
            hgt = R * 0.085
            V = V * hgt
            wtxt *= hgt
            rr = R * 0.78
            ang0 = hash01(k, 410) * 2 * math.pi
            a = ang0 + (V[:, 0] - wtxt * 0.5) / rr
            rad = rr + V[:, 1]
            P2 = np.stack([rad * np.cos(a), rad * np.sin(a),
                           np.full(len(V), Wd * 0.50 + 0.004)], -1)
            lo.add(P2, F, M_RUBBER, base=(0.16, 0.155, 0.15, 1),
                   aux=(age, aux[1], 0.5, hash01(k, 411)))
    return R, Wd


def build_tyre_stack(mb, wx, wy, wz, k, heading=0.0, n=None, kind=None,
                     capped=None, toppled=False, belt=None):
    """a bolted free-standing stack.  Not a barrier — those belong to the
    barrier module; these are the loose stacks a circuit actually leaves at
    gates, post pads and trap corners."""
    n = n if n is not None else rint(3, 6, k, 420)
    kind = kind or pick(["slick", "slick", "wet", "road", "truck"], k, 421)
    capped = chance(0.45, k, 422) if capped is None else capped
    lo = Local(mb, yaw(heading + rnd(-15, 15, k, 423)), np.array([wx, wy, wz]))
    if toppled:
        # A stack on its side is a CYLINDER LYING DOWN: its axis is horizontal
        # and it rests on its own outer radius.  The first version pitched it by
        # 74-106 deg about a fixed 0.34 m pivot, so anything past 90 drove the
        # far end of a 2 m stack up to 0.45 m into the ground (DR_Tyres_008,
        # measured).  Pitch is now 90 +- 2.5 deg and the pivot is the real
        # outer radius, so the lowest point lands within a millimetre of grade.
        Rmax = max(tyre_dims(k + 0.13 * i, kind)[0] for i in range(n))
        lo = Local(lo, pitchX(90.0 + rnd(-2.5, 2.5, k, 424)),
                   np.array([0, 0, Rmax - 0.012]))
    z = 0.0                       # running TOP of the stack
    R = 0.35
    for i in range(n):
        load = (n - i - 1) / max(1, n - 1)
        Ri, Wi, _rim, _ng = tyre_dims(k + 0.13 * i, kind)
        squeeze = rnd(0.90, 0.99, k, 430, i)
        zc = z + Wi * 0.5 * squeeze
        sub = Local(lo, yaw(rnd(0, 360, k, 425, i)) @
                    pitchX(rnd(-3.5, 3.5, k, 426, i)) @
                    rollY(rnd(-3.5, 3.5, k, 427, i)),
                    np.array([rnd(-0.035, 0.035, k, 428, i),
                              rnd(-0.035, 0.035, k, 429, i), zc]))
        R, Wd = build_tyre(sub, k + 0.13 * i, kind, load=load * 0.8)
        z = zc + Wd * 0.5 * squeeze
    if capped:
        col = srgb(pick(['#1a1a1c', '#26428c', '#8c2626', '#d8d8d4'], k, 431))
        sub = Local(lo, np.eye(3), np.array([0, 0, z]))
        sub.cyl((0, 0, -0.055), (0, 0, 0.012), R * 0.99, M_PLASTIC,
                base=(*col, 1), aux=(rnd(0.2, 0.8, k, 432), 0.6, 0.5,
                                     hash01(k, 433)), n=28)
    if belt is None:
        belt = chance(0.35, k, 434)
    if belt and not toppled:
        sub = Local(lo, np.eye(3), np.array([0, 0, 0]))
        bcol = srgb(pick(['#1b1b1e', '#2f5a2f', '#5a2f2f'], k, 435))
        for zb in (z * 0.35, z * 0.72):
            sub.cyl((0, 0, zb), (0, 0, zb + 0.045), R * 1.005, M_FABRIC,
                    base=(*bcol, 1), aux=(0.4, 0.7, 0.5, hash01(k, 436)),
                    n=30, caps=False)
    # the through-bolt a real stack is built on
    lo.cyl((0, 0, -0.05), (0, 0, z + 0.06), 0.016, M_STEEL, base=GALV,
           aux=(rnd(0.3, 0.9, k, 437), 0.7, 0.8, hash01(k, 438)), n=8)
    return n, kind


# --------------------------------------------------------------------------- #
# 12.  markers, corner signage, and the rest of the kerb-side furniture         #
# --------------------------------------------------------------------------- #

def build_distance_board(mb, s, side, dist, k, style=0, tier=1):
    """braking board.  Real ones stand just outside the track edge, angled a
    few degrees toward the oncoming driver."""
    if not barrier_ok(s, side):
        return None
    mount = pick([0, 0, 1], k, 450)          # 0 = own posts, 1 = on the barrier
    lat = float(barrier_offset(s, side))
    if mount == 1:
        lat = mount_lat(s, side) - 0.01
    else:
        lat = max(float(verge_edge(s)) + 1.20,
                  lat - rnd(0.4, 2.2, k, 451))
    W = rnd(1.15, 1.45, k, 452)
    H = rnd(0.85, 1.10, k, 453)
    z0 = (ARMCO_TOP + rnd(0.04, 0.14, k, 454)) if mount == 1 \
        else rnd(0.75, 1.15, k, 455)
    if mount == 0:
        wx, wy, zb, lat = anchor("marker%d@%.0f" % (dist, s), s, lat, side,
                                 embed=BASE_EMBED, foot=0.25)
    else:
        wx, wy, zb, lat = anchor("marker%d@%.0f" % (dist, s), s, lat, side,
                                 foot=0.25)
    nx, ny = normal_world(s, side)
    R, O = frame_from_facing((float(wx), float(wy), zb + z0),
                             (-float(nx), -float(ny)))
    # angled toward the car coming down the road
    R = R @ yaw(-side * rnd(8.0, 22.0, k, 456))
    lo = Local(mb, R, O)
    age = rnd(0.15, 0.85, k, 457)
    aux = (age, rnd(0.4, 0.95, k, 458), 0.5, hash01(k, 459))
    bg = srgb('#1c1f24') if style == 0 else srgb('#f4f4f0')
    fg = srgb('#f6f6f2') if style == 0 else srgb('#1c1f24')
    art = Art(W, H)
    art.rect(0, 0, W, H, bg, 0)
    if style == 0:
        art.rect(W * 0.04, H * 0.05, W * 0.96, H * 0.95, bg, 1)
    txt = "%d" % dist
    h = H * 0.68
    w = art.text_width(txt, h, 0.06)
    if w > W * 0.76:
        h *= W * 0.76 / w
    # a braking board's numerals are heavy: the glyphs are stretched, not
    # dilated — outline dilation produced overlapping coplanar copies
    art.text(txt, W * 0.5, H * 0.5 - h * 0.40, h, fg, 2, tracking=0.075,
             width=1.14)
    surf = board_surface(W, H, k, bow=rnd(-0.006, 0.012, k, 460),
                         dents=[(rnd(0.2, 0.8, k, 461) * W,
                                 rnd(0.2, 0.8, k, 462) * H,
                                 rnd(0.004, 0.011, k, 463), 0.34)]
                         if chance(0.25, k, 464) else [])
    sub = Local(lo, np.eye(3), np.array([0, 0, 0]))
    emit_art(sub, art, surf, aux, maxlen=0.16)
    panel_body(sub, surf, W, H, 0.014, aux, back=(0.13, 0.135, 0.14, 1))
    sage = (min(1.0, age + 0.2), 0.7, 0.7, hash01(k, 465))
    if mount == 0:
        for sx in (-1, 1):
            x = sx * W * rnd(0.28, 0.38, k, 466)
            lo.cyl((x, -0.03, 0.0), (x, -0.03, -z0 - 0.12), 0.032, M_STEEL,
                   base=GALV, aux=sage, n=8)
            lo.box((x - 0.15, -0.20, -z0 - 0.14), (x + 0.15, 0.14, -z0 + 0.02),
                   M_CONC, base=(0.33, 0.33, 0.32, 1),
                   aux=(0.7, 0.8, 0.4, hash01(k, 467, sx)))
    else:
        for sx in (-1, 1):
            x = sx * W * 0.32
            lo.box((x - 0.035, -0.03, -z0 + 0.20), (x + 0.035, -0.012, H * 0.8),
                   M_STEEL, base=GALV, aux=sage)
    return dist


def build_corner_sign(mb, corner, k):
    """corner number + name plate on the outside barrier at the entry"""
    s = corner["s_in"] - rnd(12.0, 34.0, k, 470)
    side = corner["outside"]
    ml_ = mount_lat(s, side)
    if ml_ is None:
        return None
    lat = fit_lat(s, side, ml_)
    W = rnd(1.9, 2.6, k, 471)
    H = rnd(0.52, 0.68, k, 472)
    z0 = ARMCO_TOP + rnd(0.05, 0.22, k, 473)
    R, O, Ww = chord_frame(s - W * 0.5, s + W * 0.5, side, lat, dz=z0,
                           name="cornersign%d" % corner["i"])
    if R is None:
        return None
    lo = Local(mb, R, O)
    age = rnd(0.10, 0.70, k, 474)
    aux = (age, rnd(0.3, 0.8, k, 475), 0.5, hash01(k, 476))
    bg = srgb('#1b3a63')
    fg = srgb('#f2f2ee')
    art = Art(Ww, H)
    art.rect(0, 0, Ww, H, bg, 0)
    art.rect(0, 0, Ww * 0.20, H, srgb('#c8342a'), 1)
    art.text("%d" % corner["i"], Ww * 0.10, H * 0.24, H * 0.56, fg, 2,
             tracking=0.06)
    nm = corner["name"].upper()
    h = H * 0.42
    w = art.text_width(nm, h, 0.14)
    if w > Ww * 0.74:
        h *= Ww * 0.74 / w
    art.text(nm, Ww * 0.24, H * 0.5 - h * 0.40, h, fg, 2, align='L',
             tracking=0.14)
    surf = board_surface(Ww, H, k, bow=rnd(-0.005, 0.010, k, 477))
    emit_art(lo, art, surf, aux, maxlen=0.18)
    panel_body(lo, surf, Ww, H, 0.014, aux, back=(0.13, 0.135, 0.14, 1))
    for j in (-1, 1):
        x = j * Ww * 0.36
        lo.box((x - 0.03, -0.03, -z0 + 0.25), (x + 0.03, -0.012, H * 0.85),
               M_STEEL, base=GALV, aux=(min(1.0, age + 0.2), 0.7, 0.7,
                                        hash01(k, 478)))
    return corner["i"]


def build_info_sign(mb, s, side, k, lines, W=None, H=None, bg=None, fg=None,
                    lat=None, h_post=None):
    """generic trackside information sign on two posts"""
    W = W or rnd(1.5, 2.2, k, 480)
    H = H or rnd(0.55, 0.85, k, 481)
    lat = lat if lat is not None else float(barrier_offset(s, side)) + \
        rnd(0.6, 2.6, k, 482)
    hp = h_post if h_post is not None else rnd(1.05, 1.55, k, 483)
    wx, wy, zb, lat = anchor("infosign@%.0f/%+d" % (s, side), s, lat, side,
                             embed=BASE_EMBED, foot=W * 0.5, behind=True,
                             clear=0.45, height=hp + H + 0.15)
    if wx is None:
        return False
    nx, ny = normal_world(s, side)
    R, O = frame_from_facing((float(wx), float(wy), zb + hp),
                             (-float(nx), -float(ny)))
    R = R @ yaw(rnd(-18, 18, k, 484))
    lo = Local(mb, R, O)
    age = rnd(0.2, 0.9, k, 485)
    aux = (age, rnd(0.4, 0.95, k, 486), 0.5, hash01(k, 487))
    bg = bg if bg is not None else srgb('#f0eee6')
    fg = fg if fg is not None else srgb('#1a1a1c')
    nl = len(lines)
    rows = [(t, 1.0 - (i + 0.55) / nl, 0.72 / nl) for i, t in enumerate(lines)]
    eq_sign_panel(lo, k, "", W, H, bg, fg, tracking=0.13, lines=rows, aux=aux)
    sage = (min(1.0, age + 0.2), 0.7, 0.8, hash01(k, 488))
    for sx in (-1, 1):
        x = sx * W * rnd(0.28, 0.40, k, 489)
        lo.cyl((x, -0.02, 0.0), (x, -0.02, -hp - 0.10), 0.028, M_STEEL,
               base=GALV, aux=sage, n=8)
    return True


def build_tv_camera(mb, s, side, k):
    """a trackside TV camera on a mast: the thing that makes a circuit read as
    a televised race weekend rather than a road."""
    lat = float(barrier_offset(s, side)) + rnd(1.0, 4.0, k, 500)
    cap = zone_cap(s, side)
    h = min(rnd(3.2, 5.6, k, 501), cap - 0.4 if cap < 90 else 99.0)
    if h < 2.2:
        return None
    wx, wy, zb, lat = anchor("tvcam@%.0f/%+d" % (s, side), s, lat, side,
                             embed=BASE_EMBED, foot=0.35, behind=True,
                             height=h + 0.4)
    if wx is None:
        return None
    nx, ny = normal_world(s, side)
    R, O = frame_from_facing((wx, wy, zb), (-float(nx), -float(ny)))
    lo = Local(mb, R, O)
    age = rnd(0.1, 0.6, k, 502)
    aux = (age, 0.5, 0.75, hash01(k, 503))
    # lattice mast
    lo.box((-0.30, -0.30, -0.06), (0.30, 0.30, 0.10), M_CONC,
           base=(0.33, 0.33, 0.32, 1), aux=(0.6, 0.7, 0.4, hash01(k, 504)))
    legs = [(-0.13, -0.13), (0.13, -0.13), (0.13, 0.13), (-0.13, 0.13)]
    for (lx, ly) in legs:
        lo.cyl((lx, ly, 0.05), (lx * 0.55, ly * 0.55, h), 0.026, M_STEEL,
               base=GALV, aux=aux, n=6)
    nrung = int(h / 0.45)
    for r in range(1, nrung):
        t = r / nrung
        zz = 0.05 + t * (h - 0.05)
        sc = 1.0 - 0.45 * t
        for j in range(4):
            a = legs[j]
            b = legs[(j + 1) % 4]
            lo.cyl((a[0] * sc, a[1] * sc, zz), (b[0] * sc, b[1] * sc, zz),
                   0.010, M_STEEL, base=GALV, aux=aux, n=4)
            if r % 2 == 0:
                zz2 = 0.05 + (r + 1) / nrung * (h - 0.05)
                sc2 = 1.0 - 0.45 * (r + 1) / nrung
                lo.cyl((a[0] * sc, a[1] * sc, zz), (b[0] * sc2, b[1] * sc2, zz2),
                       0.008, M_STEEL, base=GALV, aux=aux, n=4)
    # head: pan/tilt, body, lens, hood, cable drop
    pan = rnd(-45, 45, k, 505)
    tiltd = rnd(-12, 2, k, 506)
    hd = Local(lo, yaw(pan) @ pitchX(tiltd), np.array([0.0, 0.0, h + 0.06]))
    hd.cyl((0, 0, -0.06), (0, 0, 0.10), 0.075, M_PLASTIC,
           base=(0.10, 0.10, 0.11, 1), aux=aux, n=14)
    hd.box((-0.13, -0.30, 0.10), (0.13, 0.26, 0.34), M_PLASTIC,
           base=(0.055, 0.055, 0.06, 1), aux=aux)
    hd.cyl((0, -0.30, 0.22), (0, -0.62, 0.22), 0.072, M_PLASTIC,
           base=(0.05, 0.05, 0.055, 1), aux=aux, n=18, r1=0.086)
    hd.cyl((0, -0.62, 0.22), (0, -0.635, 0.22), 0.082, M_GLASS,
           base=(0.02, 0.025, 0.03, 1), aux=aux, n=20)
    hd.box((-0.16, -0.72, 0.30), (0.16, -0.24, 0.345), M_PLASTIC,
           base=(0.045, 0.045, 0.05, 1), aux=aux)
    hd.box((-0.09, 0.26, 0.14), (0.09, 0.36, 0.30), M_PLASTIC,
           base=(0.08, 0.08, 0.085, 1), aux=aux)
    hd.tube([[0.05, 0.30, 0.14], [0.10, 0.36, -0.10], [0.06, 0.20, -0.45]],
            0.012, M_PLASTIC, base=(0.03, 0.03, 0.03, 1), aux=aux, n=5,
            caps=False)
    lo.tube([[0.06, 0.14, h - 0.30], [0.10, 0.20, h * 0.55],
             [0.05, 0.14, 0.30], [0.02, 0.10, 0.05]], 0.014, M_PLASTIC,
            base=(0.03, 0.03, 0.03, 1), aux=aux, n=5, caps=False)
    return h


def build_speaker(mb, s, side, k):
    lat = float(barrier_offset(s, side)) + rnd(0.8, 3.5, k, 510)
    h = rnd(3.0, 4.2, k, 511)
    if zone_cap(s, side) < h + 0.3:
        return None
    wx, wy, zb, lat = anchor("speaker@%.0f/%+d" % (s, side), s, lat, side,
                             embed=BASE_EMBED, foot=0.25, behind=True,
                             height=h + 0.3)
    if wx is None:
        return None
    nx, ny = normal_world(s, side)
    R, O = frame_from_facing((wx, wy, zb), (-float(nx), -float(ny)))
    lo = Local(mb, R, O)
    age = rnd(0.2, 0.8, k, 512)
    aux = (age, 0.6, 0.8, hash01(k, 513))
    lo.cyl((0, 0, 0), (0, 0, h), 0.052, M_STEEL, base=GALV, aux=aux, n=10)
    lo.box((-0.20, -0.20, -0.05), (0.20, 0.20, 0.07), M_CONC,
           base=(0.33, 0.33, 0.32, 1), aux=(0.6, 0.7, 0.4, hash01(k, 514)))
    for j in range(rint(1, 3, k, 515)):
        sub = Local(lo, yaw(rnd(-60, 60, k, 516, j)) @ pitchX(rnd(-16, -4, k, 517, j)),
                    np.array([0, 0, h - 0.18 - j * 0.34]))
        col = srgb(pick(['#8a8a86', '#3a3a3c', '#c8c6bc'], k, 518, j))
        sub.cyl((0, 0.06, 0), (0, -0.34, 0), 0.055, M_PLASTIC, base=(*col, 1),
                aux=aux, n=16, r1=0.165)
        sub.cyl((0, 0.06, 0), (0, 0.16, 0), 0.055, M_PLASTIC, base=(*col, 1),
                aux=aux, n=14, r1=0.042)
    return h


def build_windsock(mb, s, side, k):
    lat = float(barrier_offset(s, side)) + rnd(1.4, 4.6, k, 520)
    h = rnd(4.5, 6.5, k, 521)
    if zone_cap(s, side) < h + 0.5:
        return None
    wx, wy, zb, lat = anchor("windsock@%.0f/%+d" % (s, side), s, lat, side,
                             embed=BASE_EMBED, foot=0.35, behind=True,
                             height=h + 0.4)
    if wx is None:
        return None
    R, O = frame_from_facing((wx, wy, zb), (1.0, 0.0))
    lo = Local(mb, R @ yaw(rnd(0, 360, k, 522)), O)
    aux = (rnd(0.2, 0.7, k, 523), 0.4, 0.8, hash01(k, 524))
    lo.cyl((0, 0, 0), (0, 0, h), 0.055, M_STEEL, base=GALV, aux=aux, n=10,
           r1=0.038)
    lo.box((-0.28, -0.28, -0.05), (0.28, 0.28, 0.08), M_CONC,
           base=(0.33, 0.33, 0.32, 1), aux=(0.6, 0.7, 0.4, hash01(k, 525)))
    lo.cyl((0, 0, h - 0.04), (0, 0.34, h - 0.04), 0.020, M_STEEL, base=GALV,
           aux=aux, n=6)
    # the sock: five alternating bands, drooping and curling
    n = 22
    nb = 5
    L = rnd(1.9, 2.6, k, 526)
    droop = rnd(0.35, 0.75, k, 527)
    th = np.linspace(0, 2 * math.pi, n, endpoint=False)
    rings = []
    for b in range(nb + 1):
        t = b / nb
        r = 0.30 * (1.0 - 0.55 * t)
        y = 0.32 + t * L                  # hung from the ring at the arm's end
        z = h - 0.04 - droop * t ** 1.7
        rings.append(np.stack([r * np.cos(th),
                               np.full(n, y),
                               r * np.sin(th) + z], -1))
    for b in range(nb):
        A, B = rings[b], rings[b + 1]
        P = np.vstack([A, B])
        i = np.arange(n)
        j = (i + 1) % n
        q = np.stack([i, j, j + n, i + n], -1)
        col = srgb('#e2500f') if b % 2 == 0 else srgb('#f2f2ee')
        lo.add(P, q, M_FABRIC, base=(*col, 1),
               uv=np.stack([np.tile(th / (2 * math.pi), 2),
                            np.repeat([b / nb, (b + 1) / nb], n)], -1),
               aux=(rnd(0.3, 0.8, k, 528), 0.4, 0.5, hash01(k, 529)),
               smooth=True)
        lo.add(P, q[:, ::-1], M_FABRIC, base=(*col, 1),
               aux=(rnd(0.3, 0.8, k, 528), 0.4, 0.5, hash01(k, 529)),
               smooth=True)
    return h


def build_cable_run(mb, s0, s1, side, k):
    """the conduit and junction boxes that run the length of every barrier"""
    def lat_fn(ss):
        return fit_behind(ss, side, float(barrier_back(ss, side)) + 0.25,
                          foot=0.1, clear=0.20)
    n = max(2, int((s1 - s0) / 2.0))
    S = np.linspace(s0, s1, n)
    P = []
    runs = [[]]
    for ss in S:
        la = lat_fn(ss)
        if la is None:                     # no barrier to run alongside
            if runs[-1]:
                runs.append([])
            continue
        wx, wy, _ = station_world(ss, la, side)
        zz = float(ground_z(ss, la, side)) + 0.07 + \
            0.012 * math.sin(ss * 0.7 + hash01(k, 530) * 6.0)
        runs[-1].append([float(wx), float(wy), zz])
    aux = (rnd(0.3, 0.9, k, 531), 0.8, 0.5, hash01(k, 532))
    rad = rnd(0.035, 0.055, k, 533)
    for seg in runs:
        if len(seg) < 2:
            continue
        mb.tube(np.array(seg), rad, M_PLASTIC, base=(0.045, 0.045, 0.05, 1),
                aux=aux, n=7)
    nb = max(1, int((s1 - s0) / rnd(28.0, 52.0, k, 534)))
    for j in range(nb):
        ss = s0 + (j + 0.5) * (s1 - s0) / nb
        wx, wy, zz, la = anchor("jbox@%.0f/%+d" % (ss, side), ss, lat_fn(ss),
                                side, embed=BASE_EMBED, foot=0.25,
                                behind=True, clear=0.30)
        if wx is None:
            continue
        nx, ny = normal_world(ss, side)
        R, O = frame_from_facing((wx, wy, zz), (-float(nx), -float(ny)))
        lo = Local(mb, R @ yaw(rnd(-12, 12, k, 535, j)), O)
        col = srgb(pick(['#5c5f52', '#4a4d52', '#6b6255'], k, 536, j))
        lo.box((-0.22, -0.16, 0.0), (0.22, 0.16, rnd(0.42, 0.62, k, 537, j)),
               M_PLASTIC, base=(*col, 1),
               aux=(rnd(0.3, 0.95, k, 538, j), 0.85, 0.5, hash01(k, 539, j)))
    return nb


def build_gully(mb, s, side, k):
    """a verge drainage gully — small, but the eye knows when they are absent"""
    # a gully sits at the verge/runoff seam, so it is the one thing in this file
    # allowed on the verge itself: it is a hole in the ground, not furniture.
    if float(runoff_widths(s, side)["apex"]) > 1.2:
        return None                     # an apex gravel bed starts at the verge
    lat = float(verge_edge(s)) + rnd(0.35, 0.9, k, 540)
    wx, wy, _ = station_world(s, lat, side)
    zz = float(ground_z(s, lat, side))
    ANCHORS.append(dict(n="gully@%.0f/%+d" % (s, side),
                        p=(float(wx), float(wy), zz), s=float(s),
                        u=lat * side, side=int(side)))
    nx, ny = normal_world(s, side)
    R, O = frame_from_facing((float(wx), float(wy), zz), (-float(nx), -float(ny)))
    lo = Local(mb, R, O)
    L = rnd(0.55, 0.95, k, 541)
    Wd = rnd(0.30, 0.42, k, 542)
    aux = (rnd(0.5, 1.0, k, 543), 0.95, 0.85, hash01(k, 544))
    lo.box((-L * 0.5 - 0.05, -Wd * 0.5 - 0.05, -0.14),
           (L * 0.5 + 0.05, Wd * 0.5 + 0.05, -0.005), M_CONC,
           base=(0.30, 0.30, 0.29, 1), aux=aux)
    nb = int(L / 0.075)
    for j in range(nb):
        x = -L * 0.5 + 0.037 + j * L / nb
        lo.box((x - 0.020, -Wd * 0.5, -0.045), (x + 0.020, Wd * 0.5, -0.005),
               M_STEEL, base=(0.22, 0.20, 0.18, 1), aux=aux)
    for sy in (-1, 1):
        lo.box((-L * 0.5, sy * Wd * 0.5 - 0.022 * sy, -0.05),
               (L * 0.5, sy * Wd * 0.5 + 0.022 * sy, -0.004), M_STEEL,
               base=(0.24, 0.22, 0.20, 1), aux=aux)


def build_painted_logo(mb, s, side, bi, k):
    """sponsor name painted on the asphalt runoff — the wide-shot dressing that
    only exists on circuits with real money behind them"""
    # Paint goes on the runoff ASPHALT, not on gravel and not on grass.  The
    # contract publishes the asphalt band's width at every station, so the logo
    # is placed inside it instead of at a guessed 6-14 m: `runoff_widths` is
    # measured OUTBOARD FROM verge_edge.
    rw = runoff_widths(s, side)
    asph = float(rw["asphalt"])
    if asph < 9.0 or float(rw["apex"]) > 1.0:
        return None                      # not enough sealed runoff to paint on
    lat0 = float(verge_edge(s)) + 2.5 + rnd(0.0, 1.0, k, 550) * (asph - 8.0)
    br = Brand(bi)
    txt = br.name
    hgt = rnd(2.6, 4.4, k, 551)
    V, F, w = text_poly(txt, br.track * 1.4)
    if len(V) == 0:
        return None
    V = V * hgt
    w *= hgt
    if w > 46.0:
        sc = 46.0 / w
        V *= sc
        w *= sc
        hgt *= sc
    # lay it along the road: glyph x -> station, glyph y -> lateral
    sc = -1.0 if side > 0 else 1.0
    ss = s - w * 0.5 + V[:, 0]
    la = lat0 + sc * V[:, 1]
    wx, wy, _ = station_world(ss, la, side)
    zz = ground_z(ss, la, side) + 0.004
    P = np.stack([np.asarray(wx, float), np.asarray(wy, float),
                  np.asarray(zz, float)], -1)
    age = rnd(0.25, 0.9, k, 552)
    mb.add(P, F, M_PAINT, base=(*br.fg, 1.0),
           uv=np.stack([V[:, 0] / max(w, 1e-6), V[:, 1] / max(hgt, 1e-6)], -1),
           aux=(age, 0.8, 0.5, hash01(k, 553)))
    return br.name


# --------------------------------------------------------------------------- #
# 13.  placement — where a circuit actually puts all of this                    #
# --------------------------------------------------------------------------- #

SG = np.arange(0.0, LAP, 1.0)


def _corner_of(s):
    best, bd = None, 1e9
    for c in CORNERS:
        d = abs(((s - c["s_apex"] + LAP * 0.5) % LAP) - LAP * 0.5)
        if d < bd:
            best, bd = c, d
    return best, bd


CORNER_TV = {1: 1.00, 2: 0.75, 3: 0.70, 4: 1.00, 5: 0.70, 6: 0.55, 7: 0.55,
             8: 0.65, 9: 0.55, 10: 0.90, 11: 0.90, 12: 1.00, 13: 0.60,
             14: 0.60, 15: 0.85}


def tv_value_field():
    """how sellable each metre of each side is.  Corners sell (the cameras
    point at apexes), the pit straight sells (it is on screen every lap), the
    infield of the esses does not."""
    V = {+1: np.full(len(SG), 0.14), -1: np.full(len(SG), 0.14)}
    for c in CORNERS:
        w = CORNER_TV.get(c["i"], 0.6)
        for side in (+1, -1):
            fac = 1.0 if side == c["outside"] else 0.62
            d = np.abs(((SG - c["s_apex"] + LAP * 0.5) % LAP) - LAP * 0.5)
            lobe = np.exp(-(d / (c["arc"] * 0.9 + 70.0)) ** 2)
            V[side] = np.maximum(V[side], 0.16 + 0.80 * w * fac * lobe)
    pit = (SG >= 3115.0) | (SG <= 250.0)
    V[-1][pit] = np.maximum(V[-1][pit], 0.88)      # south side of the straight
    V[+1][pit] = np.minimum(V[+1][pit], 0.05)      # pit wall: architecture's
    dop = (SG >= 2440.0) & (SG <= 2680.0)
    V[-1][dop] = np.maximum(V[-1][dop], 0.86)
    for side in (+1, -1):
        V[side] *= 0.55 + 0.45 * (0.5 + 0.5 * fbm1(SG / 190.0, seed=7700 + side))
    return V


def near_gate(s, tol=6.0):
    return any(abs(((s - g + LAP * 0.5) % LAP) - LAP * 0.5) < tol
               for g in GATE_STATIONS)


def marshal_post_plan():
    """corner exits first, then infill so no gap exceeds 300 m, then a sight-
    line pass.  Posts are pulled toward the barrier module's access gates,
    because that is where marshals physically get onto the circuit."""
    posts = []
    for c in CORNERS:
        s = (c["s_out"] + rnd(8.0, 42.0, c["i"], 900)) % LAP
        side = c["outside"]
        if c["i"] == 4:
            posts.append(dict(s=(c["s_in"] - 42.0) % LAP, side=c["inside"],
                              why="T4 inside flag point"))
        if c["i"] in (10, 12):
            posts.append(dict(s=(c["s_in"] - rnd(55.0, 95.0, c["i"], 901)) % LAP,
                              side=side, why="T%d braking-zone post" % c["i"]))
        posts.append(dict(s=s, side=side, why="T%d exit" % c["i"]))
    # infill on the long straights
    posts.sort(key=lambda p: p["s"])
    out = []
    for i, p in enumerate(posts):
        out.append(p)
        q = posts[(i + 1) % len(posts)]
        gap = (q["s"] - p["s"]) % LAP
        if gap > 300.0:
            npt = int(gap // 260.0)
            for j in range(npt):
                ss = (p["s"] + gap * (j + 1) / (npt + 1)) % LAP
                sd = p["side"] if hash01(ss, 902) < 0.5 else q["side"]
                if barrier_type(ss, sd) == 2 or barrier_type(ss, sd) == 3:
                    sd = -sd
                out.append(dict(s=ss, side=sd, why="straight infill"))
    # snap toward access gates
    for p in out:
        for g in GATE_STATIONS:
            d = ((g - p["s"] + LAP * 0.5) % LAP) - LAP * 0.5
            if abs(d) < 55.0:
                p["s"] = (p["s"] + d * 0.72) % LAP
                p["why"] += " + gate"
                break
    _finalise_posts(out)
    # --- sight-line repair.  A post that cannot see the next one is useless.
    # The cheap fix is the one a real circuit uses: put the post on a raised
    # platform.  Only when that is not enough is another post inserted.
    for _it in range(8):
        bad = []
        for i, p in enumerate(out):
            q = out[(i + 1) % len(out)]
            gap = (q["s"] - p["s"]) % LAP
            zA = float(ground_z(p["s"], p["lat"], p["side"])) + p["eye"]
            zB = float(ground_z(q["s"], q["lat"], q["side"])) + q["eye"]
            t = np.linspace(0.04, 0.96, 60)
            ss = (p["s"] + gap * t) % LAP
            zc = np.asarray(cl_at(ss)[4], float) + 0.35
            cl = zA + (zB - zA) * t - zc
            if float(np.min(cl)) < 0.35 and gap > 55.0:
                bad.append((i, (i + 1) % len(out),
                            float(ss[int(np.argmin(cl))])))
        if not bad:
            break
        added = 0
        for (i, j, sb) in bad:
            if out[i]["kind"] != 3:
                out[i]["kind"] = 3
                out[i]["forced_platform"] = True
            elif out[j]["kind"] != 3:
                out[j]["kind"] = 3
                out[j]["forced_platform"] = True
            else:
                side = out[i]["side"]
                if barrier_type(sb, side) in (2, 3):
                    side = -side
                out.append(dict(s=sb % LAP, side=side, why="sight-line crest"))
                added += 1
        _finalise_posts(out)
        if added == 0 and _it > 4:
            break
    return out


def _finalise_posts(out):
    # A marshal post is a building with a hardstanding.  It needs real ground
    # BEHIND the barrier, and there are stretches with none: the pit wall leaves
    # 0.6 m of footing because the ground behind it is the pit lane.  Rather than
    # clamp such a post to somewhere it does not belong (which is what put a TV
    # mast in the pit lane, measured at 171 mm proud of world_ground_z), try the
    # other side, then walk the station, then drop it.
    keep = []
    for p in out:
        k0 = hash01(p["s"], p["side"], 903) * 1000.0
        _, _, _ph, _padw, _padd = post_pad(k0)
        need = _padd * 0.55 + 0.2
        clr = _padd * 0.45 + 0.25
        hgt = _ph + 0.9
        hs = _padw * 0.5
        if room_behind(p["s"], p["side"], need, clr, hgt, hs) >= 0.0:
            keep.append(p)
            continue
        if room_behind(p["s"], -p["side"], need, clr, hgt, hs) >= 0.0:
            p["side"] = -p["side"]
            p["why"] += " (side swapped: no ground behind the barrier)"
            keep.append(p)
            continue
        moved = False
        for d in (9.0, -9.0, 16.0, -16.0, 25.0, -25.0, 38.0, -38.0, 55.0, -55.0,
                  78.0, -78.0, 110.0, -110.0, 150.0, -150.0, 200.0, -200.0):
            ss = (p["s"] + d) % LAP
            for sd in (p["side"], -p["side"]):
                if room_behind(ss, sd, need, clr, hgt, hs) >= 0.0:
                    p["s"], p["side"] = ss, sd
                    p["why"] += " (moved %+.0f m for hardstanding)" % d
                    keep.append(p)
                    moved = True
                    break
            if moved:
                break
    out[:] = keep
    out.sort(key=lambda p: p["s"])
    # numbering + per-post parameters
    for i, p in enumerate(out):
        p["n"] = i + 1
        k = hash01(p["s"], p["side"], 903) * 1000.0
        p["k"] = k
        tier = hero_tier(p["s"], p["side"])
        p["tier"] = tier
        # shelter archetype: elevated platforms where the ground is low against
        # the track, box huts on the exposed summit, canopies elsewhere
        r = hash01(k, 904)
        if p.get("forced_platform"):
            p["kind"] = 3
        elif 1650 < p["s"] < 1960:
            p["kind"] = 1 if r < 0.6 else 0
        elif r < 0.14:
            p["kind"] = 2
        elif r < 0.30:
            p["kind"] = 3
        elif r < 0.62:
            p["kind"] = 1
        else:
            p["kind"] = 0
        _pw, _pd, _ph, _padw, _padd = post_pad(k)
        p["pad"] = (_padw, _padd)
        # the slab's INBOARD edge must clear the barrier face, or the concrete
        # runs through the Armco the post is standing behind
        p["lat"] = float(barrier_offset(p["s"], p["side"])) + \
            _padd * 0.45 + rnd(0.35, 1.30, k, 905)
        cap = zone_cap(p["s"], p["side"])
        if cap < 3.6 and not p.get("forced_platform"):
            p["kind"] = 2
        p["panel"] = hash01(k, 906) < 0.86
        p["panel_state"] = 1.0 if hash01(k, 907) < 0.22 else 0.0
        # eye height for the sight-line solve: a platform post stands higher
        p["eye"] = 1.65 + (rnd(0.75, 1.15, k, 208) if p["kind"] == 3 else 0.0)
    return out


def sight_lines(posts):
    """verify each post can see the next one: chord against the road's own
    vertical profile (the crests at the summit and Le Basculement are the real
    blockers on this circuit)."""
    rep = []
    for i, p in enumerate(posts):
        q = posts[(i + 1) % len(posts)]
        sA, sB = p["s"], q["s"]
        gap = (sB - sA) % LAP
        zA = float(ground_z(sA, p["lat"], p["side"])) + p["eye"]
        zB = float(ground_z(sB, q["lat"], q["side"])) + q["eye"]
        t = np.linspace(0.05, 0.95, 40)
        ss = (sA + gap * t) % LAP
        zc = cl_at(ss)[4] + 0.35
        clear = float(np.min(zA + (zB - zA) * t - np.asarray(zc, float)))
        rep.append(dict(a=p["n"], b=q["n"], gap=round(gap, 1),
                        clear=round(clear, 2)))
    return rep


def ad_board_plan(reserved):
    """walk both sides of the circuit and sell the space."""
    TV = tv_value_field()
    plan = []
    for side in (+1, -1):
        s = hash01(side, 910) * 40.0
        guard = 0
        while s < LAP and guard < 4000:
            guard += 1
            bt = int(barrier_type(s, side))
            if bt in (2, 3):
                s += 6.0
                continue
            v = float(TV[side][int(s) % len(SG)])
            if hash01(s, side, 911) > v:
                s += rnd(6.0, 26.0, s, side, 912)
                continue
            runlen = rnd(9.0, 46.0, s, side, 913) * (0.6 + 0.9 * v)
            s1 = min(s + runlen, LAP - 0.5)
            # Several brands share a run.  A brand may take 1-3 CONSECUTIVE
            # slots (circuits do sell blocks) but never more, because a long
            # ribbon of one name is the exact thing that reads as a repeat.
            nbr = int(np.clip(2 + runlen / 12.0, 2, 5))
            brs = []
            for j in range(nbr):
                bi = brand_pick(s, side, 915, j)
                for _try in range(4):
                    if bi not in brs:
                        break
                    bi = brand_pick(s, side, 915, j, _try + 9)
                brs.append(bi)
            blk = rint(1, 2, s, side, 921)
            u = s
            j = 0
            while u < s1 - 1.4:
                pl = rnd(2.0, 4.6, u, side, 916)
                pl = min(pl, s1 - u)
                mid = u + pl * 0.5
                if near_gate(mid, 7.0) or any(a <= mid <= b and sd == side
                                              for (a, b, sd) in reserved):
                    u += pl + 0.2
                    j += 1
                    continue
                bi = brs[(j // blk) % nbr]
                tier = hero_tier(mid, side)
                r = hash01(u, side, 917)
                # A TecPro run is 1.75 m of energy absorber standing in front of
                # the node line.  Nothing is strapped to it: the advertising goes
                # on the debris fence above, or nowhere.
                if int(barrier_type(mid, side)) == 1:
                    if not has_fence(mid, side):
                        u += pl + 0.2
                        j += 1
                        continue
                    kind = "ban"
                else:
                    kind = "bar"
                    if has_fence(mid, side) and r < 0.26 and v > 0.45:
                        kind = "ban"
                plan.append(dict(kind=kind, s0=u, s1=u + pl - 0.12, side=side,
                                 brand=bi, k=hash01(u, side, 918) * 1000.0,
                                 tier=tier))
                u += pl + rnd(0.02, 0.30, u, side, 919)
                j += 1
            s = s1 + rnd(2.0, 30.0, s, side, 920)
    return plan


def billboard_plan():
    """big boards where a braking car (and the TV) look at them for seconds"""
    out = []
    spots = []
    for (ci, dists, hard) in BRAKE_ZONES:
        c = [c for c in CORNERS if c["i"] == ci][0]
        n = 3 if hard == "heavy" else 2
        for j in range(n):
            s = (c["s_in"] - rnd(70.0, 300.0, ci, j, 930)) % LAP
            spots.append((s, c["outside"], "T%d braking" % ci))
    for (s, side, why) in [(120.0, -1, "pit straight"), (3300.0, -1, "T15 exit"),
                           (2560.0, -1, "doppler"), (1780.0, +1, "summit"),
                           (2180.0, -1, "sweeper outside"),
                           (640.0, -1, "east chute")]:
        spots.append((s, side, why))
    # a hoarding standing in front of another hoarding is a modelling mistake,
    # not dressing: enforce 55 m of separation per side
    spots.sort(key=lambda t: t[0])
    keep = []
    for (s, side, why) in spots:
        if any(sd == side and abs(((s - s2 + LAP * 0.5) % LAP) - LAP * 0.5) < 55.0
               for (s2, sd, _w) in keep):
            continue
        keep.append((s, side, why))
    for i, (s, side, why) in enumerate(keep):
        k = hash01(s, side, 931) * 1000.0
        out.append(dict(s=s % LAP, side=side, brand=brand_pick(s, side, 932),
                        k=k, why=why))
    return out


def tyre_stack_plan(posts):
    """gates, post pads, trap corners and the two service laybys"""
    out = []
    for g in GATE_STATIONS:
        for side in (+1, -1):
            if barrier_type(g, side) in (2, 3):
                continue
            if hash01(g, side, 940) < 0.55:
                continue
            n = rint(2, 4, g, side, 941)
            for j in range(n):
                out.append(dict(s=(g + rnd(-5.0, 5.0, g, side, 942, j)) % LAP,
                                side=side,
                                lat_off=rnd(0.9, 2.6, g, side, 943, j),
                                k=hash01(g, side, j, 944) * 1000.0,
                                n=rint(3, 6, g, side, 945, j),
                                toppled=chance(0.10, g, side, 946, j),
                                why="gate"))
    for p in posts:
        if hash01(p["k"], 947) < 0.45:
            continue
        for j in range(rint(1, 3, p["k"], 948)):
            out.append(dict(s=(p["s"] + rnd(-4.5, 4.5, p["k"], 949, j)) % LAP,
                            side=p["side"],
                            lat_off=rnd(1.6, 4.0, p["k"], 950, j),
                            k=hash01(p["k"], j, 951) * 1000.0,
                            n=rint(2, 5, p["k"], 952, j),
                            toppled=chance(0.12, p["k"], 953, j),
                            why="post %d" % p["n"]))
    # service laybys: a real circuit keeps spares somewhere
    for (s, side, cnt) in ((1042.0, +1, 9), (2745.0, -1, 8), (455.0, -1, 6),
                           (1905.0, +1, 5)):
        for j in range(cnt):
            out.append(dict(s=(s + rnd(-11.0, 11.0, s, j, 954)) % LAP, side=side,
                            lat_off=rnd(1.2, 4.2, s, j, 955),
                            k=hash01(s, j, 956) * 1000.0,
                            n=rint(2, 7, s, j, 957),
                            toppled=chance(0.22, s, j, 958),
                            why="layby"))
    return out


# --------------------------------------------------------------------------- #
# 14.  collections, purge, build                                               #
# --------------------------------------------------------------------------- #

SUBCOLLS = ["MarshalPosts", "AdBoards", "Banners", "Billboards", "TyreStacks",
            "Markers", "Signage", "Broadcast", "KerbDetail", "Paint"]


def purge():
    for ob in [o for o in bpy.data.objects if o.name.startswith(PFX)]:
        bpy.data.objects.remove(ob, do_unlink=True)
    for me in [m for m in bpy.data.meshes if m.name.startswith(PFX)]:
        bpy.data.meshes.remove(me)
    for ma in [m for m in bpy.data.materials if m.name.startswith(PFX)]:
        bpy.data.materials.remove(ma)
    for cn in SUBCOLLS + [ROOT_COLL]:
        nm = (PFX + cn) if cn != ROOT_COLL else ROOT_COLL
        c = bpy.data.collections.get(nm)
        if c:
            bpy.data.collections.remove(c)
    for cu in [c for c in bpy.data.curves if c.name.startswith("_dr_")]:
        bpy.data.curves.remove(cu)


def make_collections(scene):
    root = bpy.data.collections.new(ROOT_COLL)
    scene.collection.children.link(root)
    cs = {}
    for nm in SUBCOLLS:
        c = bpy.data.collections.new(PFX + nm)
        root.children.link(c)
        cs[nm] = c
    return root, cs


class Batch:
    """accumulates geometry into per-chunk MBs so no object spans more than
    `chunk` metres of circuit (object-space coordinates stay small)."""

    def __init__(self, name, chunk=80.0):
        self.name = name
        self.chunk = chunk
        self.mbs = {}

    def at(self, s):
        i = int((float(s) % LAP) // self.chunk)
        mb = self.mbs.get(i)
        if mb is None:
            mb = MB("%s%s_%03d" % (PFX, self.name, i))
            self.mbs[i] = mb
        return mb

    def emit(self, coll, materials):
        n = 0
        for i in sorted(self.mbs):
            if self.mbs[i].emit(coll, materials) is not None:
                n += 1
        return n


LANDMARKS = {}


def _mark(key, pos, facing=None, extra=None):
    """record a real built position so the test cameras aim at real geometry
    instead of at a guessed station."""
    LANDMARKS.setdefault(key, []).append(
        dict(p=[float(v) for v in pos],
             f=None if facing is None else [float(v) for v in facing],
             x=extra))


def build(verbose=True):
    t0 = time.time()
    scene = bpy.context.scene
    LANDMARKS.clear()
    ANCHORS.clear()
    for _kk in _CLAMP_LOG:
        _CLAMP_LOG[_kk] = 0 if _kk.endswith("_n") or _kk == "calls" else 0.0
    purge()
    mats = build_materials()
    root, cs = make_collections(scene)
    summary = dict(module="build_dressing", collection=ROOT_COLL)
    sigs = {}

    def sig(t):
        if t is None:
            return
        sigs[t] = sigs.get(t, 0) + 1

    # ---- 1. marshal posts -------------------------------------------------
    posts = marshal_post_plan()
    inv_all = []
    for p in posts:
        mb = MB("%sPost_%02d" % (PFX, p["n"]))
        inv = build_marshal_post(mb, p, p["tier"])
        mb.emit(cs["MarshalPosts"], mats)
        inv_all.append(len(inv))
        wx, wy, wz = station_world(p["s"], p["lat"], p["side"])
        nx, ny = normal_world(p["s"], p["side"])
        _mark("post", (float(wx), float(wy), float(wz)),
              (-float(nx), -float(ny)),
              dict(s=p["s"], side=p["side"], n=p["n"], kind=p["kind"],
                   tier=p["tier"]))
    sl = sight_lines(posts)
    summary["marshal_posts"] = len(posts)
    summary["post_max_gap_m"] = max(r["gap"] for r in sl)
    summary["post_min_sight_clearance_m"] = min(r["clear"] for r in sl)
    summary["post_kinds"] = {k: sum(1 for p in posts if p["kind"] == k)
                             for k in (0, 1, 2, 3)}

    # ---- 2. reserved intervals (signage owns these metres of barrier) -----
    reserved = []
    markers = Batch("Marker", 120.0)
    nmark = 0
    for (ci, dists, hard) in BRAKE_ZONES:
        c = [cc for cc in CORNERS if cc["i"] == ci][0]
        for d in dists:
            s = (c["s_in"] - d) % LAP
            side = c["outside"]
            k = hash01(s, side, 960) * 1000.0
            build_distance_board(markers.at(s), s, side, d, k,
                                 style=0 if hash01(ci, 961) < 0.75 else 1,
                                 tier=hero_tier(s, side))
            reserved.append((s - 2.2, s + 2.2, side))
            nmark += 1
            lat = fit_lat(s, side, float(barrier_offset(s, side)))
            wx, wy, wz = station_world(s, lat, side)
            nx, ny = normal_world(s, side)
            _mark("marker", (float(wx), float(wy), float(wz)),
                  (-float(nx), -float(ny)), dict(s=s, side=side, d=d, corner=ci))
    signage = Batch("Sign", 120.0)
    ncorner = 0
    for c in CORNERS:
        k = hash01(c["i"], 962) * 1000.0
        s = c["s_in"] - rnd(12.0, 34.0, k, 470)
        if build_corner_sign(signage.at(s), c, k) is not None:
            reserved.append((s - 1.6, s + 1.6, c["outside"]))
            ncorner += 1
            lat = fit_lat(s, c["outside"], float(barrier_offset(s, c["outside"])))
            wx, wy, wz = station_world(s, lat, c["outside"])
            nx, ny = normal_world(s, c["outside"])
            _mark("cornersign",
                  (float(wx), float(wy), float(wz)),
                  (-float(nx), -float(ny)),
                  dict(s=s, side=c["outside"], corner=c["i"], name=c["name"]))
    # sector markers and access signage
    ninfo = 0
    for (s, side, lines) in [(1225.0, +1, ["SECTEUR 2"]),
                             (2450.0, -1, ["SECTEUR 3"]),
                             (3660.0, -1, ["SECTEUR 1"]),
                             (60.0, -1, ["LIGNE", "DE DEPART"]),
                             (940.0, +1, ["ACCES", "POSTE"]),
                             (2560.0, -1, ["ZONE", "TECHNIQUE"]),
                             (1290.0, -1, ["SORTIE", "SECOURS"]),
                             (3090.0, +1, ["ENTREE", "STANDS"]),
                             (2200.0, +1, ["ACCES", "INTERDIT"]),
                             (1600.0, -1, ["POSTE", "MEDICAL"])]:
        k = hash01(s, side, 963) * 1000.0
        if build_info_sign(signage.at(s), s % LAP, side, k, lines):
            ninfo += 1
    for g in GATE_STATIONS:
        if hash01(g, 964) < 0.45:
            continue
        side = +1 if hash01(g, 965) < 0.5 else -1
        if barrier_type(g, side) in (2, 3):
            side = -side
        k = hash01(g, 966) * 1000.0
        if build_info_sign(signage.at(g), g, side, k,
                           [pick(["ACCES PISTE", "PORTAIL", "SECOURS",
                                  "INTERVENTION"], k, 967)],
                           W=rnd(0.9, 1.4, k, 968), H=rnd(0.36, 0.52, k, 969),
                           h_post=rnd(1.0, 1.4, k, 970)):
            ninfo += 1
    summary["distance_boards"] = nmark
    summary["corner_signs"] = ncorner
    summary["info_signs"] = ninfo

    # ---- 3. advertising ---------------------------------------------------
    ads = Batch("Ad", 80.0)
    bans = Batch("Ban", 80.0)
    nbar = nban = 0
    plan = ad_board_plan(reserved)
    for b in plan:
        sm = 0.5 * (b["s0"] + b["s1"])
        lat = fit_lat(sm, b["side"], float(barrier_offset(sm, b["side"])))
        wx, wy, wz = station_world(sm, lat, b["side"])
        nx, ny = normal_world(sm, b["side"])
        lm = ((float(wx), float(wy), float(wz)),
              (-float(nx), -float(ny)),
              dict(s=sm, side=b["side"], tier=b["tier"],
                   brand=BRANDS[b["brand"]][0]))
        if b["kind"] == "bar":
            t = build_barrier_board(ads.at(b["s0"]), b["s0"], b["s1"], b["side"],
                                    b["brand"], b["k"], b["tier"])
            if t:
                nbar += 1
                sig(t)
                _mark("board", *lm)
        else:
            t = build_fence_banner(bans.at(b["s0"]), b["s0"], b["s1"], b["side"],
                                   b["brand"], b["k"], b["tier"])
            if t:
                nban += 1
                sig(t)
                _mark("banner", *lm)
    nbig = 0
    for b in billboard_plan():
        mb = MB("%sBillboard_%02d" % (PFX, nbig))
        t = build_billboard(mb, b["s"], b["side"], b["brand"], b["k"])
        if t:
            mb.emit(cs["Billboards"], mats)
            nbig += 1
            sig(t)
            lat = fit_lat(b["s"], b["side"],
                          float(barrier_offset(b["s"], b["side"])) + 5.0)
            wx, wy, wz = station_world(b["s"], lat, b["side"])
            nx, ny = normal_world(b["s"], b["side"])
            _mark("billboard",
                  (float(wx), float(wy), float(wz)),
                  (-float(nx), -float(ny)),
                  dict(s=b["s"], side=b["side"], why=b["why"]))
    nbrg = 0
    brg = MB(PFX + "BridgeBanners")
    for (ctr, fac, W, H, why) in bridge_banner_sites():
        k = hash01(ctr[0], ctr[1], 979) * 1000.0
        t = build_bridge_banner(brg, ctr, fac, W, H, brand_pick(ctr[0], 980), k)
        if t:
            nbrg += 1
            sig(t)
            _mark("bridge", ctr, fac, dict(why=why))
    brg.emit(cs["Billboards"], mats)
    napx = 0
    apx = Batch("Apex", 120.0)
    for c in CORNERS:
        # R2-257.  TWO BOARDS AT ONE CORNER WERE TWO DRAWS FROM ONE WINDOW.
        # `s` used to be an independent uniform over the same +-30 m window for
        # every j, so nothing stopped the second board landing on the first.  On
        # the shipping seeds it did: DR_Apex_022 carried two ATELIER 9 boards
        # 0.277 m apart with 70.9 % of the smaller panel superimposed, which
        # renders as one garbled legend -- the same defect shape as R2-256 on La
        # Passerelle, found by the same sweep.  A board is at most 5.2 m wide
        # (`build_apex_board` W = rnd(2.8, 5.2)), so when there are two they now
        # take opposite halves of the window with a 7 m guard at the shared
        # edge: centres are >= 14.0 m apart and two panels cannot meet.  The
        # SINGLE-board draw is deliberately left on the old expression and the
        # old seed, so nothing moves at the 8 corners that carry one board.
        napx_c = rint(0, 2, c["i"], 971)
        for j in range(napx_c):
            if napx_c < 2:
                s = c["s_apex"] + rnd(-30.0, 30.0, c["i"], j, 972)
            else:
                s = (c["s_apex"] + (j * 2 - 1) *
                     (7.0 + rnd(0.0, 23.0, c["i"], j, 972)))
            k = hash01(c["i"], j, 973) * 1000.0
            t = build_apex_board(apx.at(s), s % LAP, c["inside"],
                                 brand_pick(c["i"], j, 974), k)
            if t:
                napx += 1
                sig(t)
    # painted runoff logos
    paint = Batch("Paint", 160.0)
    npl = 0
    for (s, side) in [(300.0, -1), (400.0, -1), (760.0, +1), (2200.0, -1),
                      (2300.0, -1), (2760.0, -1), (3420.0, +1), (1160.0, -1)]:
        k = hash01(s, side, 975) * 1000.0
        if build_painted_logo(paint.at(s), s, side, brand_pick(s, side, 976), k):
            npl += 1
    # flagpoles: the S/F approach and the paddock margin
    poles = MB(PFX + "Flagpoles")
    nfp = 0
    for j in range(12):
        s = 3560.0 + j * 9.0
        side = -1
        lat = float(barrier_offset(s, side)) + 1.6 + (0.4 * j) % 1.6
        wx, wy, zz, lat = anchor("flagpole%02d" % j, s, lat, side,
                                 embed=BASE_EMBED, foot=0.4, behind=True,
                                 clear=0.45, height=10.6)
        if wx is None:
            continue
        build_flagpole(poles, float(wx), float(wy), zz,
                       hash01(s, j, 977) * 1000.0,
                       bi=(HOUSE if j % 4 == 0 else None),
                       height=rnd(7.5, 10.5, s, j, 978))
        nfp += 1
    poles.emit(cs["Signage"], mats)
    summary["ad_boards_barrier"] = nbar
    summary["ad_banners_fence"] = nban
    summary["billboards"] = nbig
    summary["bridge_banners"] = nbrg
    summary["apex_boards"] = napx
    summary["painted_logos"] = npl
    summary["flagpoles"] = nfp

    # ---- 4. tyre stacks ---------------------------------------------------
    tyres = Batch("Tyres", 80.0)
    ntyre_st = 0
    ntyres = 0
    for t in tyre_stack_plan(posts):
        s = t["s"]
        side = t["side"]
        lat = float(barrier_offset(s, side)) + t["lat_off"]
        # a stack is 0.36 m in radius and the Armco's posts and blockouts reach
        # 0.38 m outboard of the declared face at p95, so the CENTRE has to be
        # at least 0.36 + 0.38 + a margin behind it
        wx, wy, zz, lat = anchor("tyres%03d@%.0f" % (ntyre_st, s), s, lat, side,
                                 embed=BASE_EMBED, foot=0.85, behind=True,
                                 clear=0.55, height=0.30 + 0.25 * t["n"])
        if wx is None:
            continue
        hd = math.degrees(float(world_head(s)))
        n, kind = build_tyre_stack(tyres.at(s), float(wx), float(wy), zz,
                                   t["k"], heading=hd, n=t["n"],
                                   toppled=t["toppled"])
        ntyre_st += 1
        ntyres += n
        nx, ny = normal_world(s, side)
        _mark("tyres", (float(wx), float(wy), zz), (-float(nx), -float(ny)),
              dict(s=s, side=side, n=n, kind=kind, why=t["why"]))
    summary["tyre_stacks"] = ntyre_st
    summary["tyres"] = ntyres

    # ---- 5. broadcast + kerb-side detail ----------------------------------
    ncam = 0
    for j in range(15):
        s = (j * LAP / 15.0 + rnd(-45.0, 45.0, j, 980)) % LAP
        c, d = _corner_of(s)
        if d > 120.0 and hash01(j, 981) < 0.4:
            s = (c["s_apex"] - 60.0) % LAP
        side = c["outside"] if hash01(j, 982) < 0.7 else -c["outside"]
        if barrier_type(s, side) == 3:
            side = -side
        mb = MB("%sTVCam_%02d" % (PFX, j))
        if build_tv_camera(mb, s, side, hash01(s, j, 983) * 1000.0):
            mb.emit(cs["Broadcast"], mats)
            ncam += 1
            lat = fit_lat(s, side, float(barrier_offset(s, side)) + 2.5)
            wx, wy, wz = station_world(s, lat, side)
            nx, ny = normal_world(s, side)
            _mark("tvcam", (float(wx), float(wy), float(wz)),
                  (-float(nx), -float(ny)), dict(s=s, side=side))
    spk = Batch("Speaker", 160.0)
    nspk = 0
    for j in range(14):
        s = (j * LAP / 14.0 + rnd(-60.0, 60.0, j, 984)) % LAP
        side = +1 if hash01(j, 985) < 0.5 else -1
        if barrier_type(s, side) == 3:
            side = -side
        if build_speaker(spk.at(s), s, side, hash01(s, j, 986) * 1000.0):
            nspk += 1
    nws = 0
    for (s, side) in ((1780.0, +1), (960.0, -1), (2620.0, -1)):
        if build_windsock(spk.at(s), s, side, hash01(s, 987) * 1000.0):
            nws += 1
    kerb = Batch("Kerb", 120.0)
    ncab = 0
    for (a, b, side) in [(0.0, 250.0, -1), (250.0, 560.0, -1), (860.0, 1120.0, +1),
                         (1650.0, 1930.0, +1), (2440.0, 2700.0, -1),
                         (2700.0, 2900.0, -1), (3115.0, 3675.0, -1),
                         (560.0, 800.0, +1), (1930.0, 2150.0, -1)]:
        ncab += build_cable_run(kerb.at(a), a, b, side,
                                hash01(a, side, 988) * 1000.0)
    ngul = 0
    for j in range(46):
        s = (j * LAP / 46.0 + rnd(-30.0, 30.0, j, 989)) % LAP
        side = +1 if hash01(j, 990) < 0.5 else -1
        build_gully(kerb.at(s), s, side, hash01(s, j, 991) * 1000.0)
        ngul += 1
    summary["tv_cameras"] = ncam
    summary["pa_speakers"] = nspk
    summary["windsocks"] = nws
    summary["junction_boxes"] = ncab
    summary["gullies"] = ngul

    # ---- 6. realise the batches ------------------------------------------
    summary["objects_ads"] = ads.emit(cs["AdBoards"], mats)
    summary["objects_banners"] = bans.emit(cs["Banners"], mats)
    apx.emit(cs["AdBoards"], mats)
    markers.emit(cs["Markers"], mats)
    signage.emit(cs["Signage"], mats)
    tyres.emit(cs["TyreStacks"], mats)
    spk.emit(cs["Broadcast"], mats)
    kerb.emit(cs["KerbDetail"], mats)
    paint.emit(cs["Paint"], mats)

    # ---- 7. the anti-repetition gate --------------------------------------
    dupes = {k: v for k, v in sigs.items() if v > 1}
    summary["board_units"] = sum(sigs.values())
    summary["board_distinct_signatures"] = len(sigs)
    summary["board_duplicate_signatures"] = len(dupes)
    if dupes and verbose:
        print("[DR] WARNING: %d duplicated board signatures" % len(dupes))

    nobj = nv = nf = 0
    for c in cs.values():
        for ob in c.objects:
            nobj += 1
            nv += len(ob.data.vertices)
            nf += sum(len(p.vertices) - 2 for p in ob.data.polygons)
    summary["objects"] = nobj
    summary["vertices"] = nv
    summary["triangles"] = nf
    summary["materials"] = len(mats)
    summary["brands"] = len(BRANDS)
    summary["build_s"] = round(time.time() - t0, 1)
    summary["barriers_linked"] = BR is not None
    summary["contract"] = C.__version__
    summary["ground_anchors"] = len(ANCHORS)
    summary["placement_gate"] = dressing_gate()
    if verbose:
        print("[DR] " + json.dumps(summary, indent=1))
        print("[DR] sight lines: max gap %.1f m, min clearance %.2f m"
              % (summary["post_max_gap_m"], summary["post_min_sight_clearance_m"]))
    return summary


# --------------------------------------------------------------------------- #
# 15.  test-render harness (never reached from build())                        #
# --------------------------------------------------------------------------- #

def _look(loc, aim, lens, name):
    cam = bpy.data.cameras.new(name)
    cam.lens = lens
    cam.clip_start = 0.05
    cam.clip_end = 20000.0
    ob = bpy.data.objects.new(name, cam)
    bpy.context.scene.collection.objects.link(ob)
    d = np.array(aim, float) - np.array(loc, float)
    dxy = math.hypot(d[0], d[1])
    ob.location = loc
    # camera looks down its local -Z; euler XYZ gives
    #   forward = Rz(g) Rx(t) (0,0,-1) = (-sin g sin t, cos g sin t, -cos t)
    ob.rotation_euler = (math.pi * 0.5 + math.atan2(d[2], dxy), 0.0,
                         math.atan2(d[1], d[0]) - math.pi * 0.5)
    return ob


def _wp(s, lat, side, dz=0.0):
    wx, wy, _ = station_world(s, lat, side)
    return (float(wx), float(wy), float(ground_z(s, lat, side)) + dz)


def _lm(key, pred=None, n=0):
    """pick a real built landmark (optionally the n-th matching one)"""
    L = LANDMARKS.get(key, [])
    if pred:
        L = [d for d in L if pred(d.get("x") or {})]
    if not L:
        return None
    return L[min(n, len(L) - 1)]


def _front(lm, dist, dz, lens, aim_dz=0.0, side_off=0.0):
    """camera `dist` metres in front of a landmark's face, looking at it"""
    p = np.array(lm["p"], float)
    f = np.array(lm["f"] or [1.0, 0.0], float)
    f = np.array([f[0], f[1], 0.0]) / max(1e-9, math.hypot(f[0], f[1]))
    t = np.array([-f[1], f[0], 0.0])
    loc = p + f * dist + np.array([0, 0, dz]) + t * side_off
    aim = p + np.array([0, 0, aim_dz])
    return (tuple(loc), tuple(aim), lens)


def test_cameras():
    C = {}
    # ---- framings aimed at REAL built objects -----------------------------
    b = _lm("board", lambda x: x.get("tier", 0) >= 2)
    if b:
        C["board_macro"] = _front(b, 1.55, 0.72, 85.0, aim_dz=0.52,
                                  side_off=0.55)
        C["board_run"] = _front(b, 9.0, 2.4, 40.0, aim_dz=0.6, side_off=13.0)
    bn = _lm("banner")
    if bn:
        C["banner_macro"] = _front(bn, 2.1, 1.9, 70.0, aim_dz=1.85,
                                   side_off=0.7)
    pm = _lm("post", lambda x: x.get("tier", 0) >= 2)
    if pm:
        C["post_macro"] = _front(pm, 6.5, 1.7, 40.0, aim_dz=1.5, side_off=3.2)
        C["post_wide"] = _front(pm, 14.0, 3.0, 24.0, aim_dz=1.6, side_off=9.0)
    p2 = _lm("post", lambda x: x.get("kind") == 3)
    if p2:
        C["post_platform"] = _front(p2, 8.0, 2.2, 35.0, aim_dz=2.0,
                                    side_off=4.5)
    ty = _lm("tyres", lambda x: x.get("n", 0) >= 4)
    if ty:
        C["tyre_macro"] = _front(ty, 4.2, 1.5, 42.0, aim_dz=0.70,
                                 side_off=1.8)
    mk = _lm("marker", lambda x: x.get("d") == 100)
    if mk:
        C["marker_macro"] = _front(mk, 5.0, 1.8, 50.0, aim_dz=1.7,
                                   side_off=2.0)
    cs_ = _lm("cornersign")
    if cs_:
        C["cornersign"] = _front(cs_, 4.5, 1.8, 55.0, aim_dz=1.4, side_off=1.8)
    bb = _lm("billboard")
    if bb:
        C["billboard"] = _front(bb, 22.0, 6.0, 35.0, aim_dz=4.0, side_off=9.0)
        C["billboard_back"] = _front(bb, -9.0, 3.2, 28.0, aim_dz=3.4,
                                     side_off=5.0)
    tv = _lm("tvcam")
    if tv:
        C["tvcam"] = _front(tv, 9.0, 1.8, 45.0, aim_dz=4.2, side_off=4.0)
    bg_ = _lm("bridge", lambda x: x.get("why") == "pont")
    if bg_:
        C["bridge"] = _front(bg_, 42.0, -5.6, 50.0, aim_dz=0.0, side_off=2.0)
    C["doppler"] = (( -578.82, -47.47, 4.802), _wp(2420.0, 0.0, +1, 1.0), 50.0)
    C["doppler_wide"] = ((-578.82, -47.47, 4.802), _wp(2560.0, 26.0, -1, 1.2),
                         24.0)
    C["hairpin"] = (_wp(1005.0, 9.5, +1, 0.85), _wp(1035.0, 12.0, -1, 0.9), 21.0)
    C["hairpin_out"] = (_wp(1040.0, 6.0, -1, 1.6), _wp(1075.0, 26.0, -1, 2.2),
                        35.0)
    C["t1_brake"] = (_wp(180.0, 6.0, -1, 1.4), _wp(360.0, 12.0, -1, 1.6), 45.0)
    # the deliberate hunt for a recognisable repeat: 90 m of the pit-straight
    # board ribbon, oblique, from the height a chase camera flies at
    C["repeat_hunt"] = (_wp(3380.0, 5.0, -1, 3.4), _wp(3470.0, 18.5, -1, 0.9),
                        50.0)
    C["straight_boards"] = (_wp(3400.0, 12.0, -1, 1.3), _wp(3560.0, 17.0, -1, 1.0),
                            50.0)
    C["billboard_back"] = (_wp(2555.0, 46.0, -1, 3.4), _wp(2570.0, 34.0, -1, 3.0),
                           28.0)
    C["sweeper_air"] = (_wp(2150.0, 120.0, -1, 60.0), _wp(2250.0, 10.0, -1, 0.0),
                        35.0)
    C["gantry"] = (_wp(3620.0, 26.0, -1, 3.0), _wp(3670.0, 8.0, +1, 3.0), 24.0)
    C["flagpoles"] = (_wp(3520.0, 14.0, -1, 2.0), _wp(3600.0, 26.0, -1, 6.0),
                      35.0)
    C["painted"] = (_wp(2740.0, 12.0, -1, 6.0), _wp(2775.0, 24.0, -1, 0.0), 35.0)
    return C


def _test_env(scene):
    """THE CONTRACT'S LIGHT.  Not an approximation of it.

    Every number here is `world_contract` §13, which is build_sky's shipped,
    measured rig.  The old harness lit these renders with a 2.2 W sun at
    elevation 12.5 / rotation -58 and a 0.5 sky, then graded at -0.35 stops.
    That is roughly 50x under key with the wrong sun colour and a 3.5x wrong
    key:fill, which is why the boards read as flat colour fills: they were
    being judged under a light that does not exist.  `render_tests` prints
    `lambert_radiance(0.18)` so the exposure can be checked against the
    contract's own published check value, (1.6744, 1.4600, 1.3321).
    """
    w = bpy.data.worlds.new(PFX + "TestWorld")
    scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bgn = nt.nodes.new("ShaderNodeBackground")
    sky = nt.nodes.new("ShaderNodeTexSky")
    sky.sky_type = C.SKY_MODEL                       # MULTIPLE_SCATTERING
    sky.sun_elevation = math.radians(C.SUN_ELEV_DEG)
    sky.sun_rotation = math.radians(C.SKY_SUN_ROTATION_DEG)
    sky.sun_disc = C.SKY_SUN_DISC                    # False: the lamp IS the key
    sky.sun_size = math.radians(C.SUN_ANGULAR_DIAM_DEG)
    sky.sun_intensity = 1.0
    sky.air_density = C.SKY_AIR
    sky.aerosol_density = C.SKY_AEROSOL    # Blender 5.x: NOT `dust_density`
    sky.ozone_density = C.SKY_OZONE
    sky.altitude = C.SKY_ALTITUDE
    nt.links.new(sky.outputs[0], bgn.inputs[0])
    bgn.inputs[1].default_value = C.SKY_STRENGTH
    nt.links.new(bgn.outputs[0], out.inputs[0])
    lampd = bpy.data.lights.new(PFX + "TestSun", 'SUN')
    lampd.energy = C.SUN_ENERGY                      # 115.754 W/m2
    lampd.color = C.SUN_COLOR                        # (1, 0.71632, 0.38712)
    lampd.angle = math.radians(C.SUN_ANGULAR_DIAM_DEG)
    ob = bpy.data.objects.new(PFX + "TestSun", lampd)
    scene.collection.objects.link(ob)
    d = np.array(C.SUN_DIR, float)
    d = d / np.linalg.norm(d)
    ob.rotation_euler = (math.acos(max(-1.0, min(1.0, d[2]))),
                         0.0, math.atan2(d[1], d[0]) + math.pi * 0.5)
    return ob


def _test_proxy(scene):
    """a stand-in racing surface + platform so the frames read as a circuit.
    Never emitted by build()."""
    coll = bpy.data.collections.new(PFX + "TESTPROXY")
    scene.collection.children.link(coll)
    S = np.arange(0.0, LAP, 4.0)
    cols = np.array([-70.0, -34.0, -16.0, -8.0, 0.0, 8.0, 16.0, 34.0, 70.0])
    V = []
    for ss in S:
        row = []
        for u in cols:
            side = +1 if u >= 0 else -1
            wx, wy, _ = station_world(ss, abs(u), side)
            z = float(ground_z(ss, abs(u), side)) - 0.02
            row.append([float(wx), float(wy), z])
        V.append(row)
    V = np.array(V)
    ni, nj = V.shape[0], V.shape[1]
    i = (np.arange(ni - 1)[:, None] * nj + np.arange(nj - 1)[None, :])
    q = np.stack([i, i + nj, i + nj + 1, i + 1], -1).reshape(-1, 4)
    me = bpy.data.meshes.new(PFX + "TESTPROXY_Ground")
    me.from_pydata([tuple(p) for p in V.reshape(-1, 3)], [],
                   [tuple(f) for f in q])
    me.validate()
    m = bpy.data.materials.new(PFX + "TESTPROXY_M")
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs[0].default_value = (0.052, 0.051, 0.050, 1)   # aged asphalt, a~0.11
    b.inputs[2].default_value = 0.72
    me.materials.append(m)
    ob = bpy.data.objects.new(PFX + "TESTPROXY_Ground", me)
    coll.objects.link(ob)
    return coll


def render_tests(names=None, res=(1280, 720), samples=64, context=False,
                 exposure=None, proxy=True):
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    try:
        scene.cycles.device = 'GPU'
        prefs = bpy.context.preferences.addons['cycles'].preferences
        prefs.compute_device_type = 'CUDA'
        prefs.get_devices()
        for d in prefs.devices:
            d.use = (d.type != 'CPU')
    except Exception as exc:
        print("[DR] GPU setup skipped:", exc)
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    try:
        scene.view_settings.view_transform = 'AgX'
    except Exception:
        pass
    scene.view_settings.look = C.VIEW_LOOK
    scene.view_settings.exposure = (C.REFERENCE_EXPOSURE_EXTERIOR
                                    if exposure is None else exposure)
    _test_env(scene)
    lr = C.lambert_radiance(0.18)
    print("[DR] light = world_contract %s: sun %.3f W/m2 %s, AgX %+.3f stops; "
          "an 18 %% grey card renders at %s"
          % (C.__version__, C.SUN_ENERGY,
             tuple(round(v, 5) for v in C.SUN_COLOR),
             scene.view_settings.exposure, tuple(round(v, 4) for v in lr)))
    if proxy:
        _test_proxy(scene)
    os.makedirs(RENDER_DIR, exist_ok=True)
    cams = test_cameras()
    todo = list(cams.keys()) if not names or names == ["all"] else names
    out = []
    for nm in todo:
        if nm not in cams:
            print("[DR] no such camera:", nm)
            continue
        loc, aim, lens = cams[nm]
        ob = _look(loc, aim, lens, PFX + "cam_" + nm)
        scene.camera = ob
        scene.render.filepath = os.path.join(RENDER_DIR, nm + ".png")
        t = time.time()
        bpy.ops.render.render(write_still=True)
        print("[DR] rendered %-16s %6.1f s -> %s" % (nm, time.time() - t,
                                                     scene.render.filepath))
        out.append(scene.render.filepath)
    return out


def _argv():
    return sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


if __name__ == "__main__":
    args = _argv()
    if "--list-renders" in args:
        print("\n".join(test_cameras().keys()))
        sys.exit(0)
    st = build()
    if "--context" in args:
        for nm, fn in (("surface", lambda: __import__("build_surface").build()),
                       ("barriers", lambda: BR.build()),
                       ("architecture",
                        lambda: __import__("build_architecture").build())):
            if ("--only" in args and
                    nm not in args[args.index("--only") + 1]):
                continue
            try:
                t = time.time()
                fn()
                print("[DR] context %s built in %.1f s" % (nm, time.time() - t))
            except Exception as exc:
                print("[DR] %s context failed: %s" % (nm, exc))
    if "--render" in args:
        i = args.index("--render")
        names = []
        for a in args[i + 1:]:
            if a.startswith("--"):
                break
            names.append(a)
        names = names or None
        res = (1280, 720)
        sm = 64
        if "--res" in args:
            r = args[args.index("--res") + 1].split("x")
            res = (int(r[0]), int(r[1]))
        if "--samples" in args:
            sm = int(args[args.index("--samples") + 1])
        # --sun / --bg are GONE.  The light is world_contract's, not a knob:
        # every "these look flat" judgement made under an invented 2.2 W sun was
        # made under a light that does not exist (see build_dressing.md, defect
        # 24).  --exp survives only for deliberate over/under-exposure probes.
        exp = (float(args[args.index("--exp") + 1]) if "--exp" in args
               else None)
        render_tests(names, res=res, samples=sm, context="--context" in args,
                     exposure=exp, proxy="--noproxy" not in args)
    if "--save" in args:
        p = args[args.index("--save") + 1]
        bpy.ops.wm.save_as_mainfile(filepath=p)
        print("[DR] saved", p)
